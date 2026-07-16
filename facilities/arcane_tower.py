# facilities/arcane_tower.py
"""
Arcane Tower facility – available in Skylume, Veilholt, Isle of Glass, Stormhold, and Dunemar.

Services:
  1. Scaled Research Tiers      – Pay gold for XP (all towers)
  2. Arcane Teleportation       – Teleport to visited cities (arcane tower cities only)
  3. Skill Mastery Research     – Accelerate skill mastery (arcane tower cities only)
  4. Craft Arcane Scroll        – Sacrifice 4 same-rarity equipment for a fusion scroll
  5. Arcane Blessings           – Temporary buffs with visible [Mystic] tag
  6. Pandemonium Warding        – Reduce next curse effect (Isle of Glass only)
"""

from utils import advance_time
from city_dialogue import service_dialogue
from gui.terminal import term
from combat.skills import (
    get_all_unlocked_skills, get_skill_mastery_level,
    get_class_skill_map, format_mastery_label
)
from resources.items import build_item, ITEM_RARITY
from inventory import add_item_to_inventory, remove_item_by_reference
from resources.cities import CITIES


def _get_wonderland_max_floor(player):
    """Return the highest floor reached in Wonderland dungeon."""
    wl_prog = player.get("city_floors", {}).get("wonderland", {})
    return wl_prog.get("max_floor", 1)


def _strip_wonderland_only_from_ally(ally):
    """Remove wonderland_only flag from all equipped items on an ally.

    Called when a heroine becomes permanent or leaves Wonderland,
    since wonderland_only items acquired as quest rewards should
    persist outside Wonderland.
    """
    for slot in ("weapon", "armor", "accessory1", "accessory2"):
        item = ally.get("equipped", {}).get(slot)
        if item and item.get("wonderland_only"):
            item.pop("wonderland_only", None)


def _wizard_interaction(player):
    """Handle the Wizard of Oz encounter in Wonderland's Arcane Tower.

    Phase 1: Give Silver Slippers (requires floor 30+)
    Phase 2: Upgrade Silver Slippers → Ruby Slippers (requires Wicked Witch defeat + materials)
    """
    from resources.dialogues.wonderland import WONDERLAND_WIZARD_DIALOGUE as WD
    from combat.ally import get_heroine_in_party

    term.clear()

    if player.get("wl_wizard_slippers_upgraded"):
        for line in WD.get("upgrade_already", [WD["leave"][0]]):
            term.print(line)
        term.pause()
        return

    wizard_spoken = player.get("wl_wizard_spoken", False)
    witch_defeated = player.get("wl_boss_defeated_wicked_witch", False)

    # Phase 2: Upgrade
    if wizard_spoken and witch_defeated:
        dorothy = get_heroine_in_party(player, "dorothy")
        has_slippers_equipped = (
            dorothy and
            dorothy.get("equipped", {}).get("accessory1", {}).get("id") == "silver_slippers"
        )

        has_hat = any(item.get("id") == "witch_hat" for item in player.get("inventory", []))
        has_crystal = any(item.get("id") == "emerald_flame_crystal" for item in player.get("inventory", []))

        if not has_slippers_equipped:
            for line in WD.get("upgrade_no_dorothy", [WD["leave"][0]]):
                term.print(line)
            term.pause()
            return
        if not (has_hat and has_crystal):
            for line in WD.get("upgrade_no_materials", [WD["leave"][0]]):
                term.print(line)
            term.pause()
            return

        for line in WD.get("upgrade_intro", []):
            term.print(line)
        term.print("")
        choice = term.menu(["Yes — transform the slippers!", "Not yet."], prompt="")
        if choice != 0:
            term.print(WD.get("leave", [""])[0])
            term.pause()
            return

        for line in WD.get("upgrade_perform", []):
            term.print(line)

        for mat_id in ("witch_hat", "emerald_flame_crystal"):
            for item in list(player.get("inventory", [])):
                if item.get("id") == mat_id:
                    player["inventory"].remove(item)
                    break

        ruby = build_item("ruby_slippers", rarity="unique", enhance=5)
        dorothy["equipped"]["accessory1"] = ruby
        from combat.elemental import compute_ally_elemental
        e_res, e_dmg = compute_ally_elemental(dorothy)
        dorothy["elemental_res"] = e_res
        dorothy["elemental_dmg"] = e_dmg

        from combat.ally_skills import swap_dorothy_to_vorpal_skills, grant_dorothy_upgrade_skill
        swap_dorothy_to_vorpal_skills(dorothy)
        grant_dorothy_upgrade_skill(dorothy)

        player["wl_wizard_slippers_upgraded"] = True
        term.print("")
        term.print("👠 Ruby Slippers awakened! Dorothy gains 'Emerald City's Light'!")
        term.pause()
        return

    # Phase 1: First meeting
    if not wizard_spoken:
        for line in WD.get("enter", []):
            term.print(line)
        term.print("")
        choice = term.menu([
            '"You\'re the Wizard? The REAL Wizard of Oz?"',
            '"Why are you hiding behind a curtain?"',
            '"What do you have for me?"',
        ], prompt="")
        if choice < 0:
            term.print(WD.get("leave", [""])[0])
            term.pause()
            return

        for line in WD.get("slippers_gift", []):
            term.print(line)
        term.print("")

        slippers = build_item("silver_slippers", rarity="unique", enhance=0)
        if not add_item_to_inventory(player, slippers):
            term.print("\nYour inventory is full! Make room and return.")
            term.pause()
            return

        player["wl_wizard_spoken"] = True
        term.print("\n👠 Received: Silver Slippers (dormant — waiting for Dorothy)")
        term.pause()
        return

    for line in WD.get("slippers_already", [WD["leave"][0]]):
        term.print(line)
    term.pause()

# ── Which cities have an arcane tower ────────────────────────────────────────
ARCANE_TOWER_CITIES = {"skylume", "veilholt", "isle_of_glass", "stormhold", "dunemar"}

# ── Research tier definitions ────────────────────────────────────────────────
# (tier_name, gold_cost, xp_gain, min_level)
RESEARCH_TIERS = [
    ("Novice Study",       500,     200,   1),
    ("Arcane Study",      3000,     800,   5),
    ("Deep Research",    12000,    2500,  10),
    ("Forbidden Tomes",  40000,    7000,  20),
    ("Astral Projection",100000,  18000,  30),
]

# ── Arcane Blessing definitions ──────────────────────────────────────────────
# (name, description, gold_cost, buff_type, buff_data, min_level)
ARCANE_BLESSINGS = [
    (
        "Mystic Ward",
        "Gain +3 defense for the next 10 dungeon rooms.",
        8000, "arcane_ward",
        {"value": 3, "remaining": 10},
        5
    ),
    (
        "Arcane Clarity",
        "+4 Wisdom for stat checks in the next dungeon run (8 rooms).",
        10000, "arcane_blessing",
        {"stat": "Wisdom", "value": 4, "remaining": 8},
        8
    ),
    (
        "Elemental Attunement",
        "Your attacks deal +15% elemental damage for the next 8 rooms.",
        15000, "arcane_blessing",
        {"stat": "all", "value": 0, "remaining": 8, "elemental_boost": 0.15},
        12
    ),
    (
        "Mana Attunement",
        "All skill cooldowns are reduced by 1 for the next 8 rooms.",
        20000, "arcane_blessing",
        {"stat": "all", "value": 0, "remaining": 8, "cooldown_reduction": 1},
        15
    ),
    (
        "Greater Mystic Ward",
        "Gain +6 defense for the next 12 dungeon rooms.",
        25000, "arcane_ward",
        {"value": 6, "remaining": 12},
        18
    ),
]

# ── Scroll crafting: rarity order ────────────────────────────────────────────
RARITY_ORDER = ["common", "uncommon", "rare", "epic", "legendary", "unique"]
SCROLL_ID_MAP = {
    "common":    "common_scroll",
    "uncommon":  "uncommon_scroll",
    "rare":      "rare_scroll",
    "epic":      "epic_scroll",
    "legendary": "legendary_scroll",
}

# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def arcane_tower_service(player, city_id):
    """Arcane tower: research, teleportation, skill mastery, scroll crafting, blessings."""
    service_dialogue(city_id, "arcane_tower", "enter")

    while True:
        options = _build_menu_options(player, city_id)

        choice = term.menu(options, prompt="What will you do?", allow_cancel=True, cancel_label="Leave")
        if choice < 0:
            break

        selected = options[choice]

        if selected.startswith("Research"):
            _research(player, city_id)
        elif selected == "Arcane Teleportation":
            _arcane_teleport(player, city_id)
        elif selected == "Skill Mastery Research":
            _skill_mastery_research(player, city_id)
        elif selected.startswith("Craft Arcane Scroll"):
            _craft_scroll(player, city_id)
        elif selected == "Arcane Blessings":
            _arcane_blessings(player, city_id)
        elif selected == "Pandemonium Warding":
            _pandemonium_warding(player, city_id)
        elif selected.startswith("Return through the Looking-Glass"):
            _leave_wonderland(player)
            return  # Exit arcane tower after leaving Wonderland
        elif selected == "Speak with the Wizard":
            _wizard_interaction(player)
        elif selected == "Investigate mysterious book":
            if _investigate_mysterious_book(player, city_id):
                return  # Exit arcane tower — player is now in Wonderland
        else:
            break  # safety

    service_dialogue(city_id, "arcane_tower", "leave")
    term.pause()
    advance_time(player, 30)


def _build_menu_options(player, city_id):
    """Build the menu options list based on city and player progress."""
    options = ["Research (gain XP)"]

    if city_id in ARCANE_TOWER_CITIES:
        options.append("Arcane Teleportation")
        options.append("Skill Mastery Research")

    options.append("Craft Arcane Scroll (sacrifice 4 equipment)")
    options.append("Arcane Blessings")

    if city_id == "isle_of_glass":
        options.append("Pandemonium Warding")

    # ── Wonderland: Return portal ──────────────────────────────────────
    if city_id == "wonderland":
        options.append("Return through the Looking-Glass (Veilholt)")

    # ── Wonderland: Wizard of Oz (floor 30+) ───────────────────────────
    wizard_available = (
        city_id == "wonderland" and
        _get_wonderland_max_floor(player) >= 30
    )
    if wizard_available:
        options.append("Speak with the Wizard")

    # ── Wonderland: Entry book (Veilholt only) ─────────────────────────
    if city_id == "veilholt":
        city_floors = player.get("city_floors", {})
        cities_f20 = sum(
            1 for cid, prog in city_floors.items()
            if prog.get("max_floor", 1) >= 20
        )
        if cities_f20 >= 2 and player.get("day", 1) >= 60:
            options.append("Investigate mysterious book")

    return options


# ═══════════════════════════════════════════════════════════════════════════════
#  1. SCALED RESEARCH TIERS
# ═══════════════════════════════════════════════════════════════════════════════

def _research(player, city_id):
    """Offer tiered research options scaled to player level and gold."""
    player_level = player.get("level", 1)

    available = [(name, cost, xp, lvl) for (name, cost, xp, lvl) in RESEARCH_TIERS
                 if player_level >= lvl]

    if not available:
        term.print("The archmage has nothing to teach you yet. Return when you are stronger.")
        term.pause()
        return

    term.print("\n--- Arcane Research ---")
    term.print("The archmage gestures toward shelves of ancient tomes.\n")

    tier_options = []
    for name, cost, xp, lvl in available:
        label = f"{name} ({cost:,} gold → {xp:,} XP)"
        tier_options.append(label)

    tier_choice = term.menu(tier_options, prompt="Choose your study:", allow_cancel=True)
    if tier_choice < 0:
        return

    tier_name, cost, xp_gain, _ = available[tier_choice]

    if player.get("gold", 0) < cost:
        term.print(f"Insufficient gold. You need {cost:,} gold.")
        term.pause()
        return

    if not term.confirm(f"Spend {cost:,} gold to gain {xp_gain:,} XP via {tier_name}?"):
        return

    player["gold"] -= cost
    # Use gain_exp to properly respect level caps and Learning bonus
    from leveling import gain_exp
    gain_exp(player, xp_gain)

    term.print(f"\nYou immerse yourself in {tier_name.lower()}.")
    term.print(f"The arcane knowledge seeps into your mind. (+{xp_gain:,} XP)")
    service_dialogue(city_id, "arcane_tower", "research")
    term.pause()


# ═══════════════════════════════════════════════════════════════════════════════
#  2. ARCANE TELEPORTATION
# ═══════════════════════════════════════════════════════════════════════════════

def _arcane_teleport(player, city_id):
    """Teleport to any previously visited city for a gold fee."""
    term.print("\n--- Arcane Teleportation ---")
    term.print("The archmage traces a glowing circle on the floor.\n")

    # Only cities with an arcane tower can be teleported to/from.
    # Isle of Glass: teleport FROM is always allowed, but teleport TO is
    # forbidden unless the player possesses the Glass Anchor key item
    # (obtained by clearing Floor 10 of Pandemonium on the Isle of Glass).
    has_glass_anchor = any(
        item.get("id") == "glass_anchor" for item in player.get("inventory", [])
    )
    if has_glass_anchor:
        ALLOWED_DESTINATIONS = set(ARCANE_TOWER_CITIES)
    else:
        ALLOWED_DESTINATIONS = ARCANE_TOWER_CITIES - {"isle_of_glass"}

    # Build list of visited arcane-tower cities (excluding current and Isle of Glass as destination)
    visited = []
    for cid, cdata in CITIES.items():
        if cid == city_id:
            continue
        if cid not in ALLOWED_DESTINATIONS:
            continue
        # Consider a city "visited" if player has been there (tracked via city_floors or location)
        city_prog = player.get("city_floors", {}).get(cid, {})
        if city_prog.get("max_floor", 1) > 1 or player.get("location") == cid:
            visited.append((cid, cdata["name"]))
        # Also check if they ever visited by checking if the city appears in visited_cities
        if cid in player.get("visited_cities", []):
            if (cid, cdata["name"]) not in visited:
                visited.append((cid, cdata["name"]))

    # Always allow teleport to any arcane-tower city the player has seen (fallback: check city_floors)
    for cid, cdata in CITIES.items():
        if cid == city_id:
            continue
        if cid not in ALLOWED_DESTINATIONS:
            continue
        city_prog = player.get("city_floors", {}).get(cid, {})
        if cid not in [v[0] for v in visited]:
            if city_prog.get("max_floor", 1) > 1:
                visited.append((cid, cdata["name"]))

    if not visited:
        term.print("You haven't visited any other cities yet. There are no destinations to teleport to.")
        term.pause()
        return

    # Sort by name for consistency
    visited.sort(key=lambda x: x[1])

    # Calculate costs based on distance tier
    dest_options = []
    for cid, cname in visited:
        # Base cost scales with player level; higher level = more expensive
        base_cost = 2000 + player.get("level", 1) * 200
        dest_options.append(f"{cname} ({base_cost:,} gold)")

    choice = term.menu(dest_options, prompt="Choose destination:", allow_cancel=True)
    if choice < 0:
        return

    target_city_id, target_name = visited[choice]
    cost = 2000 + player.get("level", 1) * 200

    if player.get("gold", 0) < cost:
        term.print(f"Insufficient gold. You need {cost:,} gold.")
        term.pause()
        return

    if not term.confirm(f"Spend {cost:,} gold to teleport to {target_name}?"):
        return

    player["gold"] -= cost
    player["location"] = target_city_id
    term.print(f"\nThe circle flares with blinding light!")
    term.print(f"You step through... and arrive in {target_name}.")
    advance_time(player, 60)
    term.pause()


# ═══════════════════════════════════════════════════════════════════════════════
#  3. SKILL MASTERY RESEARCH
# ═══════════════════════════════════════════════════════════════════════════════

def _skill_mastery_research(player, city_id):
    """Pay gold to add mastery progress to a skill through arcane mentoring."""
    term.print("\n--- Skill Mastery Research ---")
    term.print("The archmage can accelerate your mastery of known skills.\n")

    unlocked = get_all_unlocked_skills(player)
    if not unlocked:
        term.print("You have no unlocked skills to research.")
        term.pause()
        return

    # Build options with current mastery display
    skill_map = get_class_skill_map(player)
    skill_options = []
    for sid, sdef in unlocked:
        mastery_lvl = get_skill_mastery_level(player, sid)
        current_uses = player.get("skill_mastery", {}).get(sid, 0)
        mastery_label = format_mastery_label(sid, player)
        next_threshold = _next_mastery_threshold(current_uses)
        if mastery_lvl >= 3:
            status = f"[MAX]"
        else:
            status = f"({current_uses}/{next_threshold})"
        label = f"{sdef['name']} {mastery_label} {status}"
        skill_options.append((sid, sdef, label))

    display_options = [s[2] for s in skill_options]
    choice = term.menu(display_options, prompt="Choose a skill to research:", allow_cancel=True)
    if choice < 0:
        return

    sid, sdef, _ = skill_options[choice]
    current_uses = player.get("skill_mastery", {}).get(sid, 0)
    mastery_lvl = get_skill_mastery_level(player, sid)

    if mastery_lvl >= 3:
        term.print("This skill is already fully mastered (★★★).")
        term.pause()
        return

    # Cost scales with current mastery level
    # Mastery 0→1: needs 10 uses, costs 5000 gold
    # Mastery 1→2: needs 15 more uses (from 10 to 25), costs 15000 gold
    # Mastery 2→3: needs 25 more uses (from 25 to 50), costs 40000 gold
    thresholds = [10, 25, 50]
    costs = [5000, 15000, 40000]
    needed = thresholds[mastery_lvl] - current_uses
    cost = costs[mastery_lvl]

    term.print(f"\n{sdef['name']} — Current Mastery: {'★' * mastery_lvl if mastery_lvl > 0 else 'None'}")
    term.print(f"Progress: {current_uses}/{thresholds[mastery_lvl]} uses ({needed} more needed)")
    term.print(f"Cost to advance: {cost:,} gold")

    if player.get("gold", 0) < cost:
        term.print("Insufficient gold.")
        term.pause()
        return

    if not term.confirm("Proceed with arcane mentoring?"):
        return

    player["gold"] -= cost
    # Add exactly enough uses to reach the next threshold
    for _ in range(needed):
        from combat.skills import add_skill_mastery_xp
        new_lvl = add_skill_mastery_xp(player, sid)
    
    new_level = get_skill_mastery_level(player, sid)
    new_label = '★' * new_level if new_level > 0 else 'None'
    term.print(f"\nThe archmage guides your practice with ancient techniques.")
    term.print(f"{sdef['name']} mastery: {new_label}!")

    if new_level >= 1:
        bonuses = ["+15% power"]
        if new_level >= 2:
            bonuses.append("-1 turn cooldown")
        if new_level >= 3:
            bonuses.append("+30% power & bonus effect")
        term.print(f"Bonuses unlocked: {', '.join(bonuses[:new_level])}")

    term.pause()


def _next_mastery_threshold(current_uses):
    """Return the next mastery threshold for display."""
    if current_uses < 10:
        return 10
    elif current_uses < 25:
        return 25
    else:
        return 50


# ═══════════════════════════════════════════════════════════════════════════════
#  4. CRAFT ARCANE SCROLL (sacrifice 4 same-rarity equipment)
# ═══════════════════════════════════════════════════════════════════════════════

def _craft_scroll(player, city_id):
    """Sacrifice 4 unequipped equipment of the same rarity to craft a fusion scroll."""
    term.print("\n--- Craft Arcane Scroll ---")
    term.print("The archmage can distill the essence of equipment into a Scroll of Fusion.")
    term.print("You must sacrifice 4 unequipped items of the same rarity.\n")

    inv = player.get("inventory", [])

    # Collect unequipped equipment, grouped by rarity
    by_rarity = {}
    for idx, item in enumerate(inv):
        if item.get("type") != "equipment":
            continue
        # Unique items cannot be sacrificed — their essence is too powerful
        if item.get("unique"):
            continue
        rarity = item.get("rarity", "common")
        by_rarity.setdefault(rarity, []).append((idx, item))

    # Show what's available
    available_rarities = []
    for rarity in RARITY_ORDER:
        items = by_rarity.get(rarity, [])
        if len(items) >= 4:
            available_rarities.append(rarity)

    if not available_rarities:
        term.print("You need at least 4 unequipped equipment of the same rarity.")
        term.print("(Equipped items cannot be sacrificed.)")
        term.pause()
        return

    term.print("Available rarities for crafting:")
    rarity_options = []
    for rarity in available_rarities:
        count = len(by_rarity[rarity])
        scroll_name = f"Scroll of Fusion ({rarity})"
        cost = _scroll_craft_cost(rarity)
        rarity_options.append(f"{rarity.title()} — {count} items available → {scroll_name} (cost: {cost:,} gold)")

    choice = term.menu(rarity_options, prompt="Choose rarity to craft:", allow_cancel=True)
    if choice < 0:
        return

    target_rarity = available_rarities[choice]
    cost = _scroll_craft_cost(target_rarity)

    if player.get("gold", 0) < cost:
        term.print(f"Insufficient gold. You need {cost:,} gold.")
        term.pause()
        return

    # ── Interactive item selection ──────────────────────────────────────
    items_of_rarity = by_rarity[target_rarity]
    selected = set()  # indices into items_of_rarity list

    while True:
        # Build options list with toggle indicators
        options = []
        for i, (inv_idx, item) in enumerate(items_of_rarity):
            mark = "[✓]" if i in selected else "[ ]"
            name = item.get("name", f"Item #{inv_idx}")
            # Show a short stat line for context
            atk = item.get("attack", 0)
            dfn = item.get("defense", 0)
            stats_str = f"ATK:{atk} DEF:{dfn}" if atk or dfn else ""
            if stats_str:
                options.append(f"{mark} {name}  ({stats_str})")
            else:
                options.append(f"{mark} {name}")

        prompt = f"Select 4 items to sacrifice ({len(selected)}/4 selected) — click to toggle:"

        # Show Craft button only when exactly 4 selected
        if len(selected) == 4:
            options.append(f"✨ Craft Scroll of Fusion ({target_rarity.title()}) — {cost:,} gold")

        choice = term.menu(options, prompt=prompt, allow_cancel=True, cancel_label="Back")
        if choice < 0:
            return

        # Craft button (last option when 4 selected)
        if len(selected) == 4 and choice == len(options) - 1:
            break

        # Toggle item selection
        if 0 <= choice < len(items_of_rarity):
            if choice in selected:
                selected.discard(choice)
            else:
                selected.add(choice)

    # ── Confirmation & crafting ─────────────────────────────────────────
    items_to_sacrifice = [items_of_rarity[i] for i in selected]

    term.print(f"\nSacrificing {cost:,} gold and these items:")
    for _, item in items_to_sacrifice:
        term.print(f"  - {item['name']}")

    if not term.confirm("Proceed with the ritual?"):
        return

    player["gold"] -= cost

    # Remove the selected items (remove from the back to avoid index shifting)
    indices = sorted([idx for idx, _ in items_to_sacrifice], reverse=True)
    for idx in indices:
        if 0 <= idx < len(player.get("inventory", [])):
            del player["inventory"][idx]

    # Create the scroll
    scroll_id = SCROLL_ID_MAP[target_rarity]
    scroll = build_item(scroll_id, rarity=target_rarity)
    scroll["name"] = f"Scroll of Fusion ({target_rarity.title()})"

    if add_item_to_inventory(player, scroll):
        term.print(f"\nThe archmage channels the essence into a {scroll['name']}!")
    else:
        term.print("\nYour inventory is full! The scroll crumbles to dust...")
        # Refund half the items as a consolation (rough approximation)
        player["gold"] += cost // 2

    term.pause()


def _scroll_craft_cost(rarity):
    """Gold cost to craft a scroll of the given rarity."""
    costs = {
        "common":    2000,
        "uncommon":  5000,
        "rare":     12000,
        "epic":     30000,
        "legendary": 80000,
    }
    return costs.get(rarity, 5000)


# ═══════════════════════════════════════════════════════════════════════════════
#  5. ARCANE BLESSINGS
# ═══════════════════════════════════════════════════════════════════════════════

def _arcane_blessings(player, city_id):
    """Purchase temporary arcane blessings that persist through dungeon rooms."""
    term.print("\n--- Arcane Blessings ---")
    term.print("The archmage can imbue you with temporary arcane power.")
    term.print("These blessings last for a set number of dungeon rooms.\n")

    bless_options = []
    for name, desc, cost, btype, bdata, min_lvl in ARCANE_BLESSINGS:
        if player.get("level", 1) >= min_lvl:
            label = f"{name} — {cost:,} gold"
            bless_options.append((name, desc, cost, btype, bdata, label))

    if not bless_options:
        term.print("No blessings are available at your level.")
        term.pause()
        return

    display = [b[5] for b in bless_options]
    choice = term.menu(display, prompt="Choose a blessing:", allow_cancel=True)
    if choice < 0:
        return

    name, desc, cost, btype, bdata, _ = bless_options[choice]

    # Check if player already has this buff type active
    for existing in player.get("active_buffs", []):
        if existing.get("source") == "arcane_tower" and existing.get("label") == name:
            term.print(f"You already have {name} active ({existing.get('remaining', 0)} rooms remaining).")
            term.pause()
            return

    if player.get("gold", 0) < cost:
        term.print(f"Insufficient gold. You need {cost:,} gold.")
        term.pause()
        return

    term.print(f"\n{name}: {desc}")
    if not term.confirm(f"Purchase for {cost:,} gold?"):
        return

    player["gold"] -= cost

    buff = dict(bdata)
    buff["source"] = "arcane_tower"
    buff["label"] = name
    buff["type"] = btype
    player.setdefault("active_buffs", []).append(buff)

    tag = "[Mystic]" if btype == "arcane_ward" else "[Arcane]"
    term.print(f"\nThe archmage weaves the spell around you. {tag} {name} is now active!")
    term.print(f"Remaining rooms: {buff['remaining']}")
    term.pause()


# ═══════════════════════════════════════════════════════════════════════════════
#  6. PANDEMONIUM WARDING (Isle of Glass only)
# ═══════════════════════════════════════════════════════════════════════════════

def _pandemonium_warding(player, city_id):
    """Purchase protection against Pandemonium curses. Only at Isle of Glass."""
    term.print("\n--- Pandemonium Warding ---")
    term.print("The crystalline tower hums with ancient power.")
    term.print("The archmage can weave a ward that weakens the next curse you face in Pandemonium.\n")

    # Check if already warded
    if player.get("arcane_warding_active"):
        reduction = int(player.get("arcane_warding_pct", 0.35) * 100)
        term.print(f"You already have a Pandemonium Ward active ({reduction}% curse reduction).")
        if term.confirm("Refresh the ward?"):
            pass  # fall through to purchase
        else:
            return

    # Tiered warding options
    ward_options = [
        ("Lesser Ward", 25000, 0.25, "Reduces next curse effect by 25%"),
        ("Greater Ward", 60000, 0.40, "Reduces next curse effect by 40%"),
        ("Absolute Ward", 120000, 0.60, "Reduces next curse effect by 60%"),
    ]

    display = [f"{name} — {cost:,} gold ({desc})" for name, cost, pct, desc in ward_options]
    choice = term.menu(display, prompt="Choose a ward:", allow_cancel=True)
    if choice < 0:
        return

    name, cost, pct, desc = ward_options[choice]

    if player.get("gold", 0) < cost:
        term.print(f"Insufficient gold. You need {cost:,} gold.")
        term.pause()
        return

    if not term.confirm(f"Purchase {name} for {cost:,} gold?"):
        return

    player["gold"] -= cost
    player["arcane_warding_active"] = True
    player["arcane_warding_pct"] = pct

    term.print(f"\nThe archmage channels crystalline energy through you.")
    term.print(f"{name} active! The next Pandemonium curse will be weakened by {int(pct * 100)}%.")
    term.pause()


# ═══════════════════════════════════════════════════════════════════════════════
#  TICKING: Consume arcane blessing rooms on dungeon floor entry
# ═══════════════════════════════════════════════════════════════════════════════

def consume_arcane_blessing_room(player):
    """Call this when entering a new dungeon room to decrement arcane blessing counters."""
    for buff in player.get("active_buffs", [])[:]:
        if buff.get("source") != "arcane_tower":
            continue
        buff["remaining"] = buff.get("remaining", 0) - 1
        if buff["remaining"] <= 0:
            player["active_buffs"].remove(buff)
            label = buff.get("label", "Arcane Blessing")
            # Will be printed by dungeon system; just clean up


def get_arcane_elemental_boost(entity):
    """Return the elemental damage multiplier from active Elemental Attunement."""
    for buff in entity.get("active_buffs", []):
        if buff.get("source") == "arcane_tower" and buff.get("elemental_boost"):
            return buff["elemental_boost"]
    return 0.0


def get_arcane_cooldown_reduction(entity):
    """Return cooldown reduction from active Mana Attunement."""
    for buff in entity.get("active_buffs", []):
        if buff.get("source") == "arcane_tower" and buff.get("cooldown_reduction"):
            return buff["cooldown_reduction"]
    return 0


# ═══════════════════════════════════════════════════════════════════════════════
#  WONDERLAND: Mysterious Book Entry & Exit
# ═══════════════════════════════════════════════════════════════════════════════

def _investigate_mysterious_book(player, city_id):
    """Entry point to Wonderland — benches all allies and teleports player.

    Available in Veilholt Arcane Tower when floor + day milestones are met.
    Shows different messages based on whether the player has the Looking Glass Shard.

    Returns True if the player entered Wonderland, False otherwise.
    """
    from utils import format_time

    has_shard = any(
        item.get("id") == "looking_glass_shard"
        for item in player.get("inventory", [])
    )

    term.print(
        "\nA leather-bound book sits on a pedestal, its pages rustling "
        "though there is no wind. The title reads: 'Wonderland.'"
    )

    if not has_shard:
        term.print(
            "\nYou run your fingers over the cover. The pages feel ordinary — "
            "just paper and ink. Whatever magic this book once held, it seems "
            "dormant. You sense you're missing something... a key, perhaps. "
            "Something to look *through*, not at."
        )
        term.print(
            "\nThe archmage shrugs. 'It's just an ordinary book to you... for now.'"
        )
        term.pause()
        return False

    # ── Player has the shard ────────────────────────────────────────────
    term.print(
        "\nThe archmage warns: 'That book... it does not merely tell a story. "
        "It pulls the reader inside. Your companions cannot follow.'"
    )

    if not term.confirm("Open the book and enter Wonderland?"):
        return False

    # ── Bench all current allies (except permanent Wonderland heroines) ──
    current_allies = player.get("allies", [])
    permanent_heroine_keys = {"alice": "wonderland_heroine_alice_permanent",
                               "red_hood": "wonderland_heroine_redhood_permanent",
                               "dorothy": "wonderland_heroine_dorothy_permanent"}
    benched = []
    keep = []
    for ally in current_allies:
        hk = ally.get("_heroine_key")
        if hk in permanent_heroine_keys and player.get(permanent_heroine_keys[hk]):
            keep.append(ally)
        else:
            benched.append(ally)

    # ── Restore saved temp heroines from previous Wonderland visit ──────
    saved_temps = player.pop("wonderland_saved_temp_heroines", [])
    for saved in saved_temps:
        hk = saved.get("_heroine_key")
        # Only restore if the heroine is still temp (not yet permanent)
        if hk in permanent_heroine_keys and not player.get(permanent_heroine_keys[hk]):
            # Check if this heroine is already in keep (shouldn't be, but be safe)
            already_present = any(a.get("_heroine_key") == hk for a in keep)
            if not already_present:
                saved["_wonderland_temp"] = True
                keep.append(saved)
                term.print(f"\n💫 {saved['name']} reappears from the story's edge — your journey together resumes.")
        elif hk in permanent_heroine_keys and player.get(permanent_heroine_keys[hk]):
            # Heroine became permanent since we saved — add to keep as permanent
            already_present = any(a.get("_heroine_key") == hk for a in keep)
            if not already_present:
                saved["_wonderland_temp"] = False
                keep.append(saved)

    if saved_temps:
        term.pause()

    player["wonderland_benched_allies"] = benched
    player["allies"] = keep
    player["party_order"] = list(range(len(keep)))

    # ── Freeze time ──────────────────────────────────────────────────────
    player["wonderland_time_frozen"] = player["time_minutes"]
    player["wonderland_day_frozen"] = player.get("day", 1)

    # ── Store return location ────────────────────────────────────────────
    player["wonderland_return_city"] = city_id

    # ── Teleport ─────────────────────────────────────────────────────────
    player["location"] = "wonderland"
    player["wonderland_active"] = True
    player["wonderland_unlocked"] = True

    term.print(
        "\nThe pages envelop you. The archmage's tower dissolves into "
        "a sky the colour of aged parchment."
    )
    term.print("You are in Wonderland.")
    term.pause()
    return True


def _leave_wonderland(player):
    """Restore benched allies, unfreeze time, and return to Veilholt.

    Called when the player selects 'Return through the Looking-Glass'
    in the Wonderland Arcane Tower (Cheshire Cat).
    """
    from utils import format_time

    # ── Separate permanent vs temporary heroines ─────────────────────────
    permanent_heroines = []
    saved_temp_heroines = []
    for ally in player.get("allies", []):
        hk = ally.get("_heroine_key")
        if hk == "alice" and player.get("wonderland_heroine_alice_permanent"):
            ally["_wonderland_temp"] = False
            _strip_wonderland_only_from_ally(ally)
            permanent_heroines.append(ally)
        elif hk == "red_hood" and player.get("wonderland_heroine_redhood_permanent"):
            ally["_wonderland_temp"] = False
            _strip_wonderland_only_from_ally(ally)
            permanent_heroines.append(ally)
        elif hk == "dorothy" and player.get("wonderland_heroine_dorothy_permanent"):
            ally["_wonderland_temp"] = False
            _strip_wonderland_only_from_ally(ally)
            permanent_heroines.append(ally)
        elif hk in ("alice", "red_hood", "dorothy") and ally.get("_wonderland_temp"):
            # Save temp heroine so they can be restored on re-entry
            # This preserves their equipment (including quest upgrades)
            saved_temp_heroines.append(ally)

    # ── Save temp heroines for re-entry restoration ─────────────────────
    player["wonderland_saved_temp_heroines"] = saved_temp_heroines

    # ── Restore benched allies ───────────────────────────────────────────
    benched = player.pop("wonderland_benched_allies", [])
    player["allies"] = benched
    player["party_order"] = list(range(len(benched)))

    # ── Append permanent heroines ───────────────────────────────────────
    for heroine in permanent_heroines:
        player["allies"].append(heroine)
        player["party_order"].append(len(player["allies"]) - 1)

    # ── Overflow check: prompt to send excess allies to the house ───────
    from combat.ally import MAX_ALLIES, _return_ally_to_house, ensure_party_order
    while len(player["allies"]) > MAX_ALLIES:
        houses = player.get("houses", {})
        if not houses:
            dropped = player["allies"].pop()
            ensure_party_order(player)
            term.print(
                f"\n⚠ Your party is overflowing and you have no house! "
                f"{dropped['name']} has left."
            )
            term.pause()
            continue

        house_city, house = next(iter(houses.items()))
        excess = len(player["allies"]) - MAX_ALLIES
        term.print(
            f"\n⚠ Your party is overflowing by {excess} ally(s). "
            f"You must send someone to the house."
        )

        ally_names = [f"{a['name']} (Lv.{a['level']})" for a in player["allies"]]
        choice = term.menu(ally_names, prompt="Send which ally to the house?")
        if choice < 0 or choice >= len(player["allies"]):
            continue

        ally_to_send = player["allies"].pop(choice)
        _return_ally_to_house(player, ally_to_send, house)
        ensure_party_order(player)
        term.print(f"{ally_to_send['name']} has been sent to the house.")

    # ── Unfreeze time ───────────────────────────────────────────────────
    player["time_minutes"] = player.pop("wonderland_time_frozen", player["time_minutes"])
    player["day"] = player.pop("wonderland_day_frozen", player.get("day", 1))

    # ── Reset temp heroine states if not permanent AND not saved ────────
    saved_hks = {a.get("_heroine_key") for a in saved_temp_heroines}
    if not player.get("wonderland_heroine_alice_permanent") and "alice" not in saved_hks:
        player["wl_alice_state"] = "intro"
    if not player.get("wonderland_heroine_redhood_permanent") and "red_hood" not in saved_hks:
        player["wl_redhood_state"] = "intro"
    if not player.get("wonderland_heroine_dorothy_permanent") and "dorothy" not in saved_hks:
        player["wl_dorothy_state"] = "intro"

    # ── Cleanup Wonderland state ────────────────────────────────────────
    player["wonderland_active"] = False
    player.pop("wl_internal_time", None)

    # ── Return to Veilholt ──────────────────────────────────────────────
    return_city = player.pop("wonderland_return_city", "veilholt")
    player["location"] = return_city

    term.print(
        "\nThe book closes with a soft thud. The archmage's tower "
        "reforms around you."
    )
    term.print(
        f"The clock on the wall reads: {format_time(player['time_minutes'])}. "
        "No time has passed."
    )
    term.pause()