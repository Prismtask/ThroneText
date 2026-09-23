# combat/ally.py
"""Ally system - companions recruited from house monster girls."""
from combat.combat_io import c_print, c_input, c_clear
import random
from combat.stats import compute_enemy_attributes
from resources.enemies import ENEMIES, ENEMY_RACES
from resources.races_classes import ATTRIBUTES
from inventory import get_total_equipment_mods, remove_item_by_reference

ALLY_STAT_MULTIPLIER = 0.85   # Allies are slightly stronger at base
ALLY_LEVEL_STAT_BONUS = 0.18 # Allies gain a bit more stat per level above level 1
ALLY_HP_MULTIPLIER = 0.75    # Allies have slightly more HP baseline

# ── Party size constants ──────────────────────────────────────────────────────
MAX_PARTY_SIZE = 8        # Total party slots (player + up to 7 allies)
ACTIVE_PARTY_SIZE = 4     # Maximum combat participants (including player, so 3 allies max in combat)
MAX_ALLIES = 7            # Maximum allies in party (player + 7 = 8 total)


# ── Party order management ───────────────────────────────────────────────────

def ensure_party_order(player):
    """Initialize or repair the party_order list for the player.
    
    party_order is a list of indices into player['allies'], where:
      - First (ACTIVE_PARTY_SIZE - 1) entries are the FRONT row (active combat)
      - Remaining entries are the BACK row (reserve)
    The player themselves is always active and not in this list.
    """
    allies = player.get("allies", [])
    n = len(allies)
    order = player.get("party_order", [])

    # Clean out stale indices
    order = [i for i in order if 0 <= i < n]

    # Add any new allies not yet in order
    existing = set(order)
    for i in range(n):
        if i not in existing:
            order.append(i)

    player["party_order"] = order


def get_active_allies(player):
    """Return allies in the FRONT row (active in combat). Max 3 allies."""
    ensure_party_order(player)
    allies = player.get("allies", [])
    order = player.get("party_order", [])
    result = []
    for idx in order[:ACTIVE_PARTY_SIZE - 1]:  # first 3 slots = active
        if idx < len(allies):
            ally = allies[idx]
            if not ally.get("defeated") and ally.get("current_hp", 0) > 0:
                result.append(ally)
    return result


def get_reserve_allies(player):
    """Return allies in the BACK row (reserve, not in combat)."""
    ensure_party_order(player)
    allies = player.get("allies", [])
    order = player.get("party_order", [])
    result = []
    for idx in order[ACTIVE_PARTY_SIZE - 1:]:  # slots 4+ = reserve
        if idx < len(allies):
            ally = allies[idx]
            if not ally.get("defeated") and ally.get("current_hp", 0) > 0:
                result.append(ally)
    return result


def get_all_active_allies_including_defeated(player):
    """Return all allies in the FRONT row (including defeated ones, for display)."""
    ensure_party_order(player)
    allies = player.get("allies", [])
    order = player.get("party_order", [])
    result = []
    for idx in order[:ACTIVE_PARTY_SIZE - 1]:
        if idx < len(allies):
            result.append(allies[idx])
    return result


def get_all_reserve_allies_including_defeated(player):
    """Return all allies in the BACK row (including defeated ones, for display)."""
    ensure_party_order(player)
    allies = player.get("allies", [])
    order = player.get("party_order", [])
    result = []
    for idx in order[ACTIVE_PARTY_SIZE - 1:]:
        if idx < len(allies):
            result.append(allies[idx])
    return result


def swap_party_member(player, ally_index):
    """Swap an ally between front and back rows by their absolute index in allies list.
    
    If the ally is in the front row, they swap with the first available back row ally.
    If the ally is in the back row, they swap with the first available front row ally.
    Returns (message, success_bool).
    """
    ensure_party_order(player)
    allies = player.get("allies", [])
    order = player.get("party_order", [])
    n = len(allies)

    if ally_index < 0 or ally_index >= n:
        return "Invalid ally selection.", False

    ally_name = allies[ally_index]["name"]
    active_limit = ACTIVE_PARTY_SIZE - 1

    if ally_index in order[:active_limit]:
        # Ally is in front — swap with first back row ally
        back_indices = order[active_limit:]
        if not back_indices:
            return f"{ally_name} is already in the front row and there are no back row allies to swap with.", False
        target_idx = back_indices[0]
        # Swap positions in order
        pos_a = order.index(ally_index)
        pos_b = order.index(target_idx)
        order[pos_a], order[pos_b] = order[pos_b], order[pos_a]
        target_name = allies[target_idx]["name"]
        return f"{ally_name} moves to the back row. {target_name} steps forward!", True
    else:
        # Ally is in back — swap with first front row ally
        front_indices = order[:active_limit]
        if not front_indices:
            return f"There are no front row allies to swap with.", False
        target_idx = front_indices[0]
        pos_a = order.index(ally_index)
        pos_b = order.index(target_idx)
        order[pos_a], order[pos_b] = order[pos_b], order[pos_a]
        target_name = allies[target_idx]["name"]
        return f"{ally_name} steps forward! {target_name} moves to the back row.", True


def do_ally_switch(player, front_ally_idx, reserve_ally_idx):
    """Swap two specific allies: a front-row ally with a reserve ally.
    
    Used when an ally uses the Switch action on their turn.
    Args:
        front_ally_idx: absolute index of the front ally (the one switching)
        reserve_ally_idx: absolute index of the reserve ally (the one coming in)
    Returns (message, success_bool).
    """
    ensure_party_order(player)
    allies = player.get("allies", [])
    order = player.get("party_order", [])
    n = len(allies)
    active_limit = ACTIVE_PARTY_SIZE - 1

    if front_ally_idx < 0 or front_ally_idx >= n:
        return "Invalid front ally selection.", False
    if reserve_ally_idx < 0 or reserve_ally_idx >= n:
        return "Invalid reserve ally selection.", False

    front_name = allies[front_ally_idx]["name"]
    reserve_name = allies[reserve_ally_idx]["name"]

    # Verify positions
    if front_ally_idx not in order[:active_limit]:
        return f"{front_name} is not in the front row.", False
    if reserve_ally_idx not in order[active_limit:]:
        return f"{reserve_name} is not in the back row.", False

    # Swap positions in order
    pos_a = order.index(front_ally_idx)
    pos_b = order.index(reserve_ally_idx)
    order[pos_a], order[pos_b] = order[pos_b], order[pos_a]

    return f"{reserve_name} steps forward! {front_name} retreats to the back row.", True


def can_switch(player):
    """Return True if the player has at least one reserve ally who could switch in."""
    reserve = get_reserve_allies(player)
    return len(reserve) > 0


def auto_fill_active_slots(player):
    """If there are fewer than ACTIVE_PARTY_SIZE-1 active allies, pull from reserve to fill slots.
    Call this at combat start to ensure the front row is fully populated.
    Returns list of messages about who moved."""
    ensure_party_order(player)
    allies = player.get("allies", [])
    order = player.get("party_order", [])
    active_limit = ACTIVE_PARTY_SIZE - 1
    msgs = []

    # Count currently alive active allies
    active_alive = sum(
        1 for idx in order[:active_limit]
        if idx < len(allies) and not allies[idx].get("defeated") and allies[idx].get("current_hp", 0) > 0
    )

    # If we already have enough, stop
    needed = active_limit - active_alive
    if needed <= 0:
        return msgs

    # Find alive reserve allies to pull forward
    reserve_alive = []
    for idx in order[active_limit:]:
        if idx < len(allies) and not allies[idx].get("defeated") and allies[idx].get("current_hp", 0) > 0:
            reserve_alive.append(idx)

    # Also find defeated/inactive front allies to swap out
    inactive_front = []
    for idx in order[:active_limit]:
        if idx >= len(allies) or allies[idx].get("defeated") or allies[idx].get("current_hp", 0) <= 0:
            inactive_front.append(idx)

    swaps = min(len(inactive_front), len(reserve_alive), needed)
    for i in range(swaps):
        front_idx = inactive_front[i]
        back_idx = reserve_alive[i]
        pos_a = order.index(front_idx)
        pos_b = order.index(back_idx)
        order[pos_a], order[pos_b] = order[pos_b], order[pos_a]
        msgs.append(f"{allies[back_idx]['name']} moves to the front row!")
        if front_idx < len(allies):
            msgs.append(f"{allies[front_idx]['name']} moves to the back row.")

    return msgs


def _fix_level_hp_bonus(girl):
    """Compute or repair an ally's level_hp_bonus.

    Handles backwards compatibility: if a girl was captured at a high level
    before this fix, her stored level_hp_bonus will be 0. We detect this and
    compute the correct bonus from her level.
    """
    level = girl.get("level", 1)
    stored = girl.get("level_hp_bonus")
    expected = max(0, (level - 1) * 4)
    # If stored value is missing or suspiciously low for a high-level girl,
    # use the expected formula instead.
    if stored is None or (stored == 0 and level > 1):
        return expected
    return stored


def ally_max_hp(ally):
    """Compute ally max HP based on Constitution and level-up bonuses (same formula as player)."""
    con = ally["attributes"]["Constitution"]
    bonus = ally.get("level_hp_bonus", 0)
    return int(15 + con * 3 + bonus)


def create_ally_from_girl(girl):
    """Convert a house monster girl dict into a combat-ready ally dict.

    girl format from house:
        {"key": "...", "name": "...", "level": N, "affection": N, "captured_on": N}
    """
    enemy_key = girl.get("key")
    template = ENEMIES.get(enemy_key)
    if not template:
        # Fallback for missing template
        from combat.elemental import neutral_profile
        level = girl.get("level", 1)
        return {
            "name": girl.get("name", "Companion"),
            "key": enemy_key or "unknown",
            "level": level,
            "attributes": {attr: 1 for attr in ATTRIBUTES},
            "current_hp": 30,
            "max_hp": 30,
            "equipped": {"weapon": None, "armor": None, "accessory1": None, "accessory2": None},
            "active_buffs": [],
            "active_debuffs": [],
            "blinded": False,
            "slowed": False,
            "stunned": False,
            "frozen": False,
            "cursed": False,
            "dreaded": False,
            "silenced": False,
            "is_ally": True,
            "affection": girl.get("affection", 20),
            "exp": girl.get("exp", 0),
            "level_hp_bonus": _fix_level_hp_bonus(girl),
            "elemental_res": neutral_profile(),
            "elemental_dmg": neutral_profile(),
        }

    attrs = compute_enemy_attributes(enemy_key)
    level = girl.get("level", 1)

    # Attributes: use stored values if available (preserves manual level-up picks),
    # otherwise compute from formula for newly captured or legacy girls.
    stored_attrs = girl.get("attributes")
    if stored_attrs and all(attr in stored_attrs for attr in ATTRIBUTES):
        scaled_attrs = dict(stored_attrs)
    else:
        # Scale down attributes for balance with level-based scaling
        scaled_attrs = {}
        for attr in ATTRIBUTES:
            base = attrs.get(attr, 0)
            level_bonus = (level - 1) * ALLY_LEVEL_STAT_BONUS
            scaled = max(1, int(base * ALLY_STAT_MULTIPLIER + level_bonus))
            scaled_attrs[attr] = scaled

    # Apply engagement ring stat bonus (from proposal)
    ring_bonus = girl.get("ring_stat_bonus")
    if ring_bonus:
        for attr, val in ring_bonus.items():
            scaled_attrs[attr] = scaled_attrs.get(attr, 0) + val

    ally = {
        "name": girl.get("name", template["name"]),
        "key": enemy_key,
        "level": girl.get("level", template["level"]),
        "attributes": scaled_attrs,
        "equipped": {"weapon": None, "armor": None, "accessory1": None, "accessory2": None},
        "active_buffs": [],
        "active_debuffs": [],
        "blinded": False,
        "slowed": False,
        "stunned": False,
        "frozen": False,
        "cursed": False,
        "dreaded": False,
        "silenced": False,
        "is_ally": True,
        "affection": girl.get("affection", 30),
        "affection_cap": girl.get("affection_cap", 100),
        "engaged": girl.get("engaged", False),
        "married": girl.get("married", False),
        "monster_girl": template.get("monster_girl", True),
        "exp": girl.get("exp", 0),
        "level_hp_bonus": _fix_level_hp_bonus(girl),
        "level_cap": girl.get("level_cap", 10),
        "defeated": False,
        # Skill system fields
        "passive_skill": girl.get("passive_skill", None),  # Race-based passive
        "innate_skills": girl.get("innate_skills", []),    # 2 innate skills unique to girl
        "learned_skills": girl.get("learned_skills", []),  # List of learned skill_ids
        "learning": girl.get("learning", None),             # Current skill being learned: {"skill_id": "...", "exp": 0, "exp_needed": 300}
        "skill_cooldowns": girl.get("skill_cooldowns", {}), # skill_id -> cooldown_remaining
        "skill_mastery": girl.get("skill_mastery", {}),     # skill_id -> exp_count (for mastery levels)
    }

    # Compute HP based on scaled Constitution + level
    ally["max_hp"] = ally_max_hp(ally)
    ally["current_hp"] = ally["max_hp"]

    # Add elemental stats from race
    from combat.elemental import compute_ally_elemental
    e_res, e_dmg = compute_ally_elemental(ally)
    ally["elemental_res"] = e_res
    ally["elemental_dmg"] = e_dmg
    
    # Initialize skill system
    from combat.ally_skills import initialize_ally_skills
    initialize_ally_skills(ally, enemy_key, template.get("race"))

    return ally


def get_ally_effective_attribute(ally, attr_name):
    """Return effective attribute after equipment and buffs."""
    base = ally["attributes"].get(attr_name, 0)
    equip_mods = get_total_equipment_mods(ally)
    total = base + equip_mods.get(attr_name, 0)

    for debuff in ally.get("active_debuffs", []):
        if debuff.get("type") == "curse":
            total -= debuff.get("penalty", 2)

    if attr_name == "Strength":
        from combat.status_effects import get_weaken_penalty
        total -= get_weaken_penalty(ally)

    for buff in ally.get("active_buffs", []):
        if buff.get("type") in ("blessing", "well_rested") or buff.get("stat") == "all":
            total += buff.get("value", 0)
        elif buff.get("stat") == attr_name:
            total += buff.get("value", 0)

    # Apply race passive stat bonuses
    from combat.ally_skills import get_race_passive
    race = ally.get("race")
    if race:
        passive = get_race_passive(race)
        if passive:
            effect = passive.get("effect", {})
            if effect.get("type") in ("damage_reduction", "life_steal", "regen"):
                pass  # Handled elsewhere, not attribute bonuses
            elif effect.get("stat") == "all":
                affected = effect.get("stats", [])
                if attr_name in affected:
                    total += effect.get("value", 0)
            elif effect.get("stat") == attr_name:
                total += effect.get("value", 0)

    # Tarnished Jade pin bonuses
    from combat.weapon.tarnished_jade import get_tarnished_jade_str_bonus, get_tarnished_jade_wis_bonus, is_tarnished_jade_weakened
    if attr_name == "Strength":
        total += get_tarnished_jade_str_bonus(ally)
    elif attr_name == "Wisdom":
        total += get_tarnished_jade_wis_bonus(ally)
    # Apply weaken debuff from Wedge Backlash
    if is_tarnished_jade_weakened(ally):
        total = total // 2

    # Author's Pen passive: +4 all stats while in Wonderland
    from combat.weapon.authors_pen import get_authors_pen_stat_bonus
    total += get_authors_pen_stat_bonus(ally, attr_name)

    return total


def compute_ally_stats(ally):
    """Return tuple of effective stats (str, con, dex, ler, wis, cha)."""
    a_str = get_ally_effective_attribute(ally, "Strength")
    a_con = get_ally_effective_attribute(ally, "Constitution")
    a_dex = get_ally_effective_attribute(ally, "Dexterity")
    a_ler = get_ally_effective_attribute(ally, "Learning")
    a_wis = get_ally_effective_attribute(ally, "Wisdom")
    a_cha = get_ally_effective_attribute(ally, "Charisma")
    return a_str, a_con, a_dex, a_ler, a_wis, a_cha


def format_ally_status_line(ally, idx=None, is_active=False):
    """Format a compact name/HP line for an ally."""
    prefix = f"[{idx}]" if idx is not None else "   "
    active_mark = " >" if is_active else ""
    mg_symbol = " ♀" if ally.get("monster_girl") else ""
    if ally.get("defeated") or ally.get("current_hp", 0) <= 0:
        return f"{prefix} {ally['name'][:12]:<12} [INCAPACITATED]{mg_symbol}{active_mark}"
    return f"{prefix} {ally['name'][:12]:<12} {ally['current_hp']:>3}/{ally['max_hp']:<3}{mg_symbol}{active_mark}"


def format_ally_buff_line(ally):
    """Format a compact buff/debuff tag line for an ally."""
    statuses = []
    if ally.get("stunned"):
        statuses.append("STN")
    if ally.get("slowed"):
        statuses.append("SLW")
    if ally.get("blinded"):
        statuses.append("BLD")
    if ally.get("frozen"):
        statuses.append("FRZ")
    if any(d["type"] == "poison" for d in ally.get("active_debuffs", [])):
        statuses.append("PSN")
    if any(d["type"] == "bleed" for d in ally.get("active_debuffs", [])):
        statuses.append("BLE")
    if any(d["type"] == "burn" for d in ally.get("active_debuffs", [])):
        statuses.append("BRN")
    return f" [{' '.join(statuses)}]" if statuses else ""


def _hp_bar(current, max_hp, width=10):
    """Return a simple ASCII HP bar."""
    if max_hp <= 0:
        return "[          ]"
    ratio = current / max_hp
    filled = int(ratio * width)
    filled = max(0, min(width, filled))
    empty = width - filled
    bar = "#" * filled + "." * empty
    return f"[{bar}]"


def get_alive_allies(player):
    """Return list of alive (non-defeated) allies from player."""
    return [a for a in player.get("allies", []) if not a.get("defeated") and a.get("current_hp", 0) > 0]


def get_all_party_members(player):
    """Return list of all alive party members: [player] + alive allies."""
    party = [player]
    party.extend(get_alive_allies(player))
    return party


def equip_ally_item(ally, item, player, target_slot=None):
    """Equip an item on an ally from the player's inventory."""
    from inventory import add_item_to_inventory

    # Block equipping temporary Wonderland heroines
    # EXCEPTION: vorpal_blade_rusted / vorpal_blade on Alice (heroine quest item)
    # EXCEPTION: woodcutters_broken_axe / grandmothers_axe on Red Hood
    # EXCEPTION: silver_slippers / ruby_slippers on Dorothy
    item_id = item.get("id", "")
    is_vorpal_on_alice = (
        item_id in ("vorpal_blade_rusted", "vorpal_blade") and
        ally.get("_heroine_key") == "alice"
    )
    is_axe_on_redhood = (
        item_id in ("woodcutters_broken_axe", "grandmothers_axe") and
        ally.get("_heroine_key") == "red_hood"
    )
    is_slippers_on_dorothy = (
        item_id in ("silver_slippers", "ruby_slippers") and
        ally.get("_heroine_key") == "dorothy"
    )
    if ally.get("_wonderland_temp") and not is_vorpal_on_alice and not is_axe_on_redhood and not is_slippers_on_dorothy:
        return f"Cannot equip gear on {ally['name']} — they are not a permanent ally yet."

    item_slot = item["slot"]
    # Resolve dual accessory slots
    if item_slot == "accessory":
        if target_slot in ("accessory1", "accessory2"):
            pass  # use caller-specified slot
        elif ally.get("equipped", {}).get("accessory1") is None:
            target_slot = "accessory1"
        elif ally.get("equipped", {}).get("accessory2") is None:
            target_slot = "accessory2"
        else:
            target_slot = "accessory1"
    else:
        target_slot = item_slot

    old = ally.get("equipped", {}).get(target_slot)
    if old:
        # Return old item to player inventory
        if not add_item_to_inventory(player, old):
            return f"Cannot equip {item['name']} on {ally['name']} — your inventory is full."
    ally["equipped"][target_slot] = item
    # Remove item from player inventory
    if item in player.get("inventory", []):
        player["inventory"].remove(item)
    # Recalculate ally elemental profile
    from combat.elemental import compute_ally_elemental
    res, dmg = compute_ally_elemental(ally)
    ally["elemental_res"] = res
    ally["elemental_dmg"] = dmg

    # Vorpal Blade on Alice: trigger skill swap
    if is_vorpal_on_alice:
        from combat.ally_skills import swap_alice_to_vorpal_skills
        swap_alice_to_vorpal_skills(ally)

    # Grandmother's Axe on Red Hood: trigger skill swap
    if is_axe_on_redhood:
        from combat.ally_skills import swap_redhood_to_vorpal_skills
        swap_redhood_to_vorpal_skills(ally)

    # Silver/Ruby Slippers on Dorothy: trigger skill swap
    if is_slippers_on_dorothy:
        from combat.ally_skills import swap_dorothy_to_vorpal_skills
        swap_dorothy_to_vorpal_skills(ally)

    return f"Equipped {item['name']} on {ally['name']}."


def unequip_ally_slot(ally, slot, player):
    """Unequip an item from an ally and return to player's inventory."""
    from inventory import add_item_to_inventory

    # Block unequipping temporary Wonderland heroines
    # EXCEPTION: vorpal blade on Alice (heroine quest item)
    # EXCEPTION: woodcutter/grandmother axe on Red Hood
    # EXCEPTION: silver/ruby slippers on Dorothy
    equipped_item = ally.get("equipped", {}).get(slot, {}) or {}
    is_vorpal_on_alice = (
        equipped_item.get("id") in ("vorpal_blade_rusted", "vorpal_blade") and
        ally.get("_heroine_key") == "alice"
    )
    is_axe_on_redhood = (
        equipped_item.get("id") in ("woodcutters_broken_axe", "grandmothers_axe") and
        ally.get("_heroine_key") == "red_hood"
    )
    is_slippers_on_dorothy = (
        equipped_item.get("id") in ("silver_slippers", "ruby_slippers") and
        ally.get("_heroine_key") == "dorothy"
    )
    if ally.get("_wonderland_temp") and not is_vorpal_on_alice and not is_axe_on_redhood and not is_slippers_on_dorothy:
        return f"Cannot unequip from {ally['name']} — they are not a permanent ally yet."

    if slot in ally.get("equipped", {}) and ally["equipped"][slot]:
        item = ally["equipped"][slot]
        if add_item_to_inventory(player, item):
            ally["equipped"][slot] = None
            # Recalculate ally elemental profile
            from combat.elemental import compute_ally_elemental
            res, dmg = compute_ally_elemental(ally)
            ally["elemental_res"] = res
            ally["elemental_dmg"] = dmg

            # Vorpal Blade removed from Alice: revert skills
            if is_vorpal_on_alice:
                from combat.ally_skills import revert_alice_to_normal_skills
                revert_alice_to_normal_skills(ally)

            # Grandmother's Axe removed from Red Hood: revert skills
            if is_axe_on_redhood:
                from combat.ally_skills import revert_redhood_to_normal_skills
                revert_redhood_to_normal_skills(ally)

            # Silver/Ruby Slippers removed from Dorothy: revert skills
            if is_slippers_on_dorothy:
                from combat.ally_skills import revert_dorothy_to_normal_skills
                revert_dorothy_to_normal_skills(ally)

            return f"Unequipped {item['name']} from {ally['name']}."
        else:
            return f"Cannot unequip {item['name']} from {ally['name']} — your inventory is full!"
    return "Nothing equipped in that slot."


def dismiss_allies_back_to_house(player):
    """Return all active allies to the house's monster_girls list.

    Unequips all gear (returns to player inventory) and restores the girls to the house.
    """
    from inventory import add_item_to_inventory
    allies = player.pop("allies", [])
    if not allies:
        return

    houses = player.get("houses", {})
    if not houses:
        return

    house_city, house = next(iter(houses.items()))
    house.setdefault("monster_girls", [])

    for ally in allies:
        # Skip returning equipped items for temp heroines (their gear is innate)
        if not ally.get("_wonderland_temp"):
            # Return equipped items to player
            for slot in ["weapon", "armor", "accessory1", "accessory2"]:
                item = ally.get("equipped", {}).get(slot)
                if item:
                    if not add_item_to_inventory(player, item):
                        c_print(f"Your inventory is full! {item['name']} from {ally['name']} was dropped.")
                    ally["equipped"][slot] = None

        # Add back to house (only if not already there)
        existing = [g for g in house["monster_girls"] if g.get("key") == ally["key"] and g.get("name") == ally["name"]]
        if not existing:
            house["monster_girls"].append({
                "key": ally["key"],
                "name": ally["name"],
                "level": ally["level"],
                "affection": ally.get("affection", 30),
                "affection_cap": ally.get("affection_cap", 100),
                "engaged": ally.get("engaged", False),
                "married": ally.get("married", False),
                "exp": ally.get("exp", 0),
                "level_hp_bonus": ally.get("level_hp_bonus", 0),
                "level_cap": ally.get("level_cap", 10),
                "attributes": dict(ally.get("attributes", {})),
            })


def _return_ally_to_house(player, ally, house):
    """Return a single ally to the house's monster_girls list."""
    from inventory import add_item_to_inventory

    # Skip returning equipped items for temp heroines (their gear is innate)
    if not ally.get("_wonderland_temp"):
        # Return equipped items to player
        for slot in ["weapon", "armor", "accessory1", "accessory2"]:
            item = ally.get("equipped", {}).get(slot)
            if item:
                if not add_item_to_inventory(player, item):
                    c_print(f"Your inventory is full! {item['name']} from {ally['name']} was dropped.")
                ally["equipped"][slot] = None

    # Add back to house (only if not already there)
    existing = [g for g in house.get("monster_girls", []) if g.get("key") == ally.get("key") and g.get("name") == ally.get("name")]
    if not existing:
        house.setdefault("monster_girls", []).append({
            "key": ally.get("key"),
            "name": ally["name"],
            "level": ally["level"],
            "affection": ally.get("affection", 30),
            "affection_cap": ally.get("affection_cap", 100),
            "engaged": ally.get("engaged", False),
            "married": ally.get("married", False),
            "exp": ally.get("exp", 0),
            "level_hp_bonus": ally.get("level_hp_bonus", 0),
            "level_cap": ally.get("level_cap", 10),
            "attributes": dict(ally.get("attributes", {})),
        })


def recruit_ally_from_house(player, girl, house):
    """Recruit a monster girl from house to active party (max 7 allies, 8 total party)."""
    allies = player.get("allies", [])
    if len(allies) >= MAX_ALLIES:
        # Party is full — ask who to replace
        ally_names = []
        for i, a in enumerate(allies):
            if a.get("defeated") or a.get("current_hp", 0) <= 0:
                status = "[INCAPACITATED]"
            else:
                status = f"HP {a['current_hp']}/{a['max_hp']}"
            ally_names.append(f"{a['name']} — {status}")
        ally_names.append("Cancel")
        from gui.terminal import term
        choice = term.menu(ally_names, prompt=f"Your party is full ({MAX_ALLIES}/{MAX_ALLIES}). Replace which ally?")
        if choice < 0 or choice >= len(allies):
            return None, "Recruitment cancelled."
        replaced = allies[choice]
        _return_ally_to_house(player, replaced, house)
        allies.pop(choice)

    ally = create_ally_from_girl(girl)
    player.setdefault("allies", []).append(ally)

    # Remove from house
    house["monster_girls"] = [g for g in house["monster_girls"]
                                if not (g.get("key") == girl.get("key") and g.get("name") == girl.get("name"))]

    return ally, f"{ally['name']} has joined your party!"


# ─────────────────────────────────────────────────────────────────────────────
# ALLY COMBAT ACTIONS
# ─────────────────────────────────────────────────────────────────────────────

def _ally_action_menu(ally, player, enemies):
    """Build action menu for an ally. Returns (menu_str, valid_keys, disabled_keys)."""
    actions = []
    disabled_keys = []

    # Check if Black Silence Gloves are equipped — replaces entire skill menu
    from combat.weapon.black_silence_gloves import _actor_has_black_silence_gloves
    has_gloves = _actor_has_black_silence_gloves(ally)
    
    if has_gloves:
        return _ally_gloves_menu(ally, player, enemies)

    # Palette's Brush — replaces class skills with the brush kit
    from combat.weapon.palette_brush import _actor_has_palette_brush, get_brush_action_menu
    if _actor_has_palette_brush(ally):
        return get_brush_action_menu(ally, player, enemies, False)

    actions.append(('a', 'Attack'))
    actions.append(('d', 'Defend'))

    # Abyss Fang – only if equipped and off cooldown
    from combat.weapon.abyss_fang import is_abyss_fang_available
    if is_abyss_fang_available(ally):
        actions.append(('w', 'Wield the Abyss'))

    # Captain's Cutlass – Crew Rally
    from combat.weapon.captain_cutlass import is_captain_cutlass_available
    if is_captain_cutlass_available(ally):
        actions.append(('r', 'Crew Rally'))

    # Author's Pen – Rewrite
    from combat.weapon.authors_pen import is_authors_pen_available
    if is_authors_pen_available(ally):
        actions.append(('e', 'Rewrite'))

    # Switch – only if there are reserve allies to swap with
    if can_switch(player):
        actions.append(('s', 'Switch'))

    # Skills – innate + learned, off cooldown
    from combat.ally_skills import get_usable_skills_in_combat
    usable_skills = get_usable_skills_in_combat(ally)
    for idx, (sid, sdef) in enumerate(usable_skills):
        actions.append((str(idx + 1), sdef['name']))

    # Use item - check if player has usable items
    combat_items = [
        item for item in player.get("inventory", [])
        if item.get("type") in ["consumable", "utility"]
    ]
    if combat_items:
        actions.append(('u', 'Use Item'))

    # Blank Canvas Shawl – free action, once per combat
    from combat.weapon.blank_canvas_shawl import _actor_has_blank_canvas_shawl
    if _actor_has_blank_canvas_shawl(ally) and not ally.get("blank_canvas_used"):
        actions.append(('b', 'Blank Canvas'))

    menu_str = '  '.join(f'[{key.upper()}]{label}' for key, label in actions)
    valid_keys = [key for key, _ in actions if key not in disabled_keys]
    return menu_str, valid_keys, disabled_keys


def _ally_gloves_menu(ally, player, enemies):
    """Build the action menu when an ally has Black Silence gloves equipped."""
    actions = []
    disabled_keys = []

    actions.append(('d', 'Defend'))

    # Switch
    if can_switch(player):
        actions.append(('s', 'Switch'))

    # Workshop attacks 1-9
    workshop_state = ally.get("gloves_workshop_used", set())
    if not isinstance(workshop_state, (set, list)):
        workshop_state = set()
    from combat.weapon.black_silence_gloves import WORKSHOPS
    for wid, ws in WORKSHOPS.items():
        key = str(wid)
        label = f'{ws["name"]} [{ws["stat"][:3].upper()}]'
        if wid in workshop_state:
            actions.append((key, f'{label} [USED]'))
            disabled_keys.append(key)
        else:
            actions.append((key, label))

    # Furioso
    if ally.get("gloves_furioso_available"):
        actions.append(('0', 'FURIOSO'))

    # Use item
    combat_items = [
        item for item in player.get("inventory", [])
        if item.get("type") in ["consumable", "utility"]
    ]
    if combat_items:
        actions.append(('u', 'Use Item'))

    # Blank Canvas Shawl – free action, once per combat
    from combat.weapon.blank_canvas_shawl import _actor_has_blank_canvas_shawl
    if _actor_has_blank_canvas_shawl(ally) and not ally.get("blank_canvas_used"):
        actions.append(('b', 'Blank Canvas'))

    menu_str = '  '.join(f'[{key.upper()}]{label}' for key, label in actions)
    valid_keys = [key for key, _ in actions if key not in disabled_keys]
    return menu_str, valid_keys, disabled_keys


def handle_ally_turn(ally, player, enemies, p_str, p_con, p_dex, p_ler, p_wis, p_cha, on_kill=None):
    """Handle an ally's turn in combat. Player chooses the ally's action.

    Returns: "continue", "victory", "dead", or "retry"
    """
    from combat.combat_ui import print_combat_hud
    from combat.status_effects import is_silenced
    from character import player_max_hp

    # Reset defending flag each turn so it only applies if they choose Defend THIS turn
    ally["defending_this_turn"] = False

    # Palette's Brush: reset the once-per-turn stance flag
    from combat.weapon.palette_brush import begin_actor_turn
    begin_actor_turn(ally)

    # Palette heroine: color cycle each turn + deferred Signature strike
    from combat.palette_ally import (
        is_palette_ally, has_pending_signature,
        fire_palette_signature, advance_palette_ally_color,
    )
    from combat.weapon.palette_brush import _actor_has_palette_brush, COLOR_NAMES as _BRUSH_COLORS
    if is_palette_ally(ally) and not _actor_has_palette_brush(ally):
        color = advance_palette_ally_color(ally)
        c_print(f"  🎨 {ally['name']}'s brush settles on {_BRUSH_COLORS[color]}.")
        if has_pending_signature(ally):
            msg = fire_palette_signature(ally, player, enemies, on_kill)
            c_print(msg)
            return "continue"

    a_str, a_con, a_dex, a_ler, a_wis, a_cha = compute_ally_stats(ally)

    # Show HUD with this ally marked as active (this already renders the menu block)
    print_combat_hud(player, enemies, active_ally=ally)

    # Fetch the actions behind the scenes to keep the tracking list valid
    _, valid_actions, _disabled = _ally_action_menu(ally, player, enemies)

    # REMOVED: Redundant text headers and duplicate action list prints
    action = c_input(f"  ({ally['name']}) Choose action: ").strip().lower()
    while action not in valid_actions:
        c_print(f"  Invalid choice. Available: {', '.join(valid_actions)}")
        action = c_input("  Choose: ").strip().lower()

    # ----- SWITCH (ally swaps with a reserve ally, costs their turn) -----
    if action == "s":
        reserve = get_reserve_allies(player)
        if not reserve:
            c_print("  No allies in reserve to switch with.")
            return "retry"

        # Signal to GUI that we're in ally switch mode
        player["_ally_switch_mode"] = True
        player["_ally_switch_front"] = ally["name"]
        try:
            c_print(f"\n  {ally['name']} prepares to swap with a reserve ally...")
            c_print("\n  --- BACKUP PARTY (Back Row) ---")
            for i, r_ally in enumerate(reserve):
                c_print(f"  [{i+1}] {r_ally['name']} — HP: {r_ally['current_hp']}/{r_ally['max_hp']}")
            c_print("  [0] Cancel")

            try:
                choice = c_input(f"  Pick an ally to swap {ally['name']} with: ").strip()
                if choice == "0":
                    return "retry"
                idx = int(choice) - 1
                if idx < 0 or idx >= len(reserve):
                    c_print("  Invalid choice.")
                    return "retry"
                target_reserve = reserve[idx]
                allies_list = player.get("allies", [])
                reserve_abs_idx = allies_list.index(target_reserve)
                front_abs_idx = allies_list.index(ally)
                msg, ok = do_ally_switch(player, front_abs_idx, reserve_abs_idx)
                if ok:
                    c_print(f"  {msg}")
                    return "continue"
                else:
                    c_print(f"  {msg}")
                    return "retry"
            except (ValueError, IndexError):
                c_print("  Invalid choice.")
                return "retry"
        finally:
            player["_ally_switch_mode"] = False
            player.pop("_ally_switch_front", None)

    # ----- WIELD THE ABYSS (Abyss Fang weapon special) -----
    if action == "w":
        from combat.weapon.abyss_fang import _wield_abyss_fang_actor
        result, _def = _wield_abyss_fang_actor(ally, is_player=False)
        return result

    # ----- CREW RALLY (Captain's Cutlass weapon special) -----
    if action == "r":
        from combat.weapon.captain_cutlass import _use_crew_rally_actor
        result, _def = _use_crew_rally_actor(ally, is_player=False, player=player)
        return result

    # ----- REWRITE (Author's Pen accessory special) -----
    if action == "e":
        from combat.weapon.authors_pen import _use_rewrite_actor
        result, _def = _use_rewrite_actor(ally, player=player, is_player=False)
        return result

    # ----- BLANK CANVAS (shawl free action, once per combat) -----
    if action == "b":
        from combat.weapon.blank_canvas_shawl import use_blank_canvas
        for m in use_blank_canvas(ally, False, player):
            c_print(f"  {m}")
        return "retry"

    # ----- BRUSH STANCE (free action, once per turn) -----
    if action == "t":
        from combat.weapon.palette_brush import set_brush_stance
        c_print(set_brush_stance(ally))
        return "retry"

    # ----- BRUSH EXHIBITS (i/k/g) -----
    if action in ("i", "k", "g"):
        from combat.weapon.palette_brush import (
            _actor_has_palette_brush, execute_impasto_exhibit,
            execute_chiaroscuro_exhibit, execute_signature_exhibit,
            get_brush_exhibits,
        )
        if not _actor_has_palette_brush(ally):
            return "retry"
        key_map = {"i": "impasto", "k": "chiaroscuro", "g": "signature"}
        exhibit_key = key_map[action]
        if exhibit_key not in [k for k, _ in get_brush_exhibits(ally)]:
            c_print("  That exhibit is not available yet.")
            return "retry"
        stats = (a_str, a_con, a_dex, a_ler, a_wis, a_cha)
        alive_before = {id(e) for e in enemies if e["hp"] > 0}
        if exhibit_key == "impasto":
            msg, victory = execute_impasto_exhibit(ally, enemies, stats, False)
        elif exhibit_key == "chiaroscuro":
            msg, victory = execute_chiaroscuro_exhibit(ally, enemies, stats, False)
        else:
            msg, victory = execute_signature_exhibit(ally, enemies, stats, False)
        c_print(msg)
        killed = [e for e in enemies if e["hp"] <= 0 and id(e) in alive_before]
        if on_kill:
            for e in killed:
                on_kill(e, enemies)
        if victory:
            return "victory"
        return "continue"

    # ----- SKILLS (numbered 1-9) or GLOVES WORKSHOPS -----
    if action.isdigit():
        # Check if Black Silence Gloves are equipped — workshop attacks replace skills
        from combat.weapon.black_silence_gloves import _actor_has_black_silence_gloves, _execute_workshop_actor, _execute_furioso_actor
        
        if _actor_has_black_silence_gloves(ally):
            if action == '0':
                # FURIOSO
                c_print("\n>>> FURIOSO: All nine workshops in sequence! <<<")
                enemies_before = [e for e in enemies if e["hp"] > 0]
                msg, victory = _execute_furioso_actor(
                    ally, enemies, a_str, a_con, a_dex, a_ler, a_wis, a_cha, is_player=False,
                )
                c_print(msg)
                # Fire on_kill for enemies actually killed by the attack (snapshot before side effects)
                if on_kill:
                    killed_by_attack = [e for e in enemies_before if e["hp"] <= 0]
                    for e in killed_by_attack:
                        on_kill(e, enemies)
                if victory:
                    return "victory"
                return "continue"
            else:
                workshop_id = int(action)
                if workshop_id < 1 or workshop_id > 9:
                    c_print("  Invalid workshop choice.")
                    return "retry"
                ws_used = ally.get("gloves_workshop_used", set())
                if not isinstance(ws_used, (set, list)):
                    ws_used = set()
                if workshop_id in ws_used:
                    c_print("  That workshop has already been used this cycle!")
                    return "retry"
                from combat.weapon.black_silence_gloves import WORKSHOPS
                ws = WORKSHOPS.get(workshop_id, {})
                ws_name = ws.get("name", f"Workshop {workshop_id}")
                ws_desc = ws.get("desc", "")
                c_print(f"\n>>> {ws_name}: {ws_desc}")
                c_input("  Press Enter to use it...")
                enemies_before = [e for e in enemies if e["hp"] > 0]
                msg, victory = _execute_workshop_actor(
                    ally, enemies, workshop_id,
                    a_str, a_con, a_dex, a_ler, a_wis, a_cha, is_player=False,
                )
                c_print(msg)
                # Fire on_kill for enemies actually killed by the attack (snapshot before side effects)
                if on_kill:
                    killed_by_attack = [e for e in enemies_before if e["hp"] <= 0]
                    for e in killed_by_attack:
                        on_kill(e, enemies)
                if victory:
                    return "victory"
                return "continue"

        # Normal skills (no gloves)
        from combat.ally_skills import get_usable_skills_in_combat, execute_ally_skill, format_ally_mastery_label
        if is_silenced(ally):
            c_print(f"  {ally['name']} is silenced and cannot use skills!")
            return "retry"

        skill_idx = int(action) - 1
        usable_skills = get_usable_skills_in_combat(ally)
        if skill_idx < 0 or skill_idx >= len(usable_skills):
            c_print("  Invalid skill choice.")
            return "retry"

        skill_id, skill_def = usable_skills[skill_idx]
        from combat.combat_ui import format_skill_elemental_tag
        elem_tag = format_skill_elemental_tag(skill_def)
        c_print(f"\n  >> {skill_def['name']}{elem_tag}: {skill_def['description']}")
        mastery_label = format_ally_mastery_label(skill_id, ally)
        if mastery_label:
            c_print(f"      Mastery: {mastery_label}")
        c_input("  Press Enter to use it...")

        all_allies = player.get("allies", [])
        # Track alive enemies before skill so on_kill can fire for newly-dead ones.
        # Snapshot which enemies were actually killed by the skill BEFORE any
        # on_kill side effects (e.g. boss death destroying linked minions).
        alive_before = {id(e) for e in enemies if e["hp"] > 0}
        msg, victory = execute_ally_skill(ally, player, skill_id, skill_def, enemies, all_allies)
        c_print(f"  {msg}")
        # Determine enemies killed by the skill (before on_kill side effects)
        killed_by_skill = [e for e in enemies if e["hp"] <= 0 and id(e) in alive_before]
        if on_kill:
            for e in killed_by_skill:
                on_kill(e, enemies)
        if victory:
            return "victory"
        return "continue"

    # ----- ATTACK -----
    if action == "a":
        if len(enemies) > 1:
            try:
                choice = int(c_input("  Select target number: ")) - 1
                if choice < 0 or choice >= len(enemies):
                    c_print("  Invalid target selection.")
                    return "retry"
                target = enemies[choice]
            except ValueError:
                c_print("  Please enter a valid number.")
                return "retry"
        else:
            target = enemies[0]

        # --- ENEMY DODGE CHECK ---
        from combat.stats import roll_dodge
        is_dodged, dodge_chance = roll_dodge(target, ally)
        if is_dodged:
            c_print(f"  The {target['name']} dodges {ally['name']}'s attack!")
            return "continue"

        # ── Wonderland Shadow: Caterpillar's Smoke — accuracy penalty ──
        from wonderland_curses import get_shadow_accuracy_penalty
        smoke_penalty = get_shadow_accuracy_penalty(player)
        if smoke_penalty > 0 and random.random() < smoke_penalty:
            c_print(f"  💨 The smoke clouds {ally['name']}'s vision — the attack goes wide!")
            return "continue"

        equipped_weapon = ally.get("equipped", {}).get("weapon")
        raw_scaling = equipped_weapon.get("scaling_stat", ["Strength"]) if equipped_weapon else ["Strength"]
        scaling_stats = raw_scaling if isinstance(raw_scaling, list) else [raw_scaling]

        scaling_val = 0
        for stat in scaling_stats:
            if stat == "Strength":
                scaling_val += a_str
            elif stat == "Dexterity":
                scaling_val += a_dex
            elif stat == "Constitution":
                scaling_val += a_con
            elif stat == "Learning":
                scaling_val += a_ler
            elif stat == "Wisdom":
                scaling_val += a_wis
            elif stat == "Charisma":
                scaling_val += a_cha
            else:
                from combat.stats import get_effective_attribute
                scaling_val += get_effective_attribute(ally, stat)

        # Apply weapon's scaling_mult (e.g. Constitution weapons use 0.5 for half scaling)
        if equipped_weapon and equipped_weapon.get("scaling_mult"):
            scaling_val = int(scaling_val * equipped_weapon["scaling_mult"])

        # ── Elemental Trait: pre-damage modifiers (Sunder, Pierce) ──
        from combat.elemental_traits import get_trait_for_weapon, apply_trait_pre_damage
        trait = get_trait_for_weapon(equipped_weapon, equipped_weapon.get("rarity", "common")) if equipped_weapon else None
        pre_dmg = apply_trait_pre_damage(trait, target) if trait else None

        from combat.stat_milestones import get_strength_bonus
        # ── Sunder (Physical trait): armor penetration ──
        effective_con_mod = target["con_mod"]
        if pre_dmg and pre_dmg.get("armor_pen", 1.0) < 1.0:
            effective_con_mod = int(target["con_mod"] * pre_dmg["armor_pen"])
            if effective_con_mod < target["con_mod"]:
                c_print(f"  ⚔️ Sunder! {target['name']}'s armor is reduced.")
        dmg = random.randint(3, 8) + scaling_val + get_strength_bonus(ally) - effective_con_mod
        dmg = max(0, dmg)

        # Hunter's Mark: increased damage taken
        if target.get("hunters_mark"):
            mark_bonus = target.get("hunters_mark_bonus", 0.15)
            dmg = int(dmg * (1 + mark_bonus))

        # Apply damage_boost buffs (multi-turn, non-consuming)
        for buff in ally.get("active_buffs", []):
            if buff.get("type") == "damage_boost":
                dmg = int(dmg * (1 + buff.get("value", 0)))

        # Critical hit check
        from combat.stats import roll_critical_hit, apply_critical_damage, format_critical_tag
        is_crit, _ = roll_critical_hit(ally, "ally", dex=a_dex, lrn=a_ler)
        dmg = apply_critical_damage(dmg, is_crit)

        # Apply elemental damage
        from combat.elemental import calculate_elemental_damage
        element = None
        if equipped_weapon and "elemental_dmg" in equipped_weapon:
            from combat.elemental import get_attack_element
            element = get_attack_element(ally, equipped_weapon)
        final_dmg = calculate_elemental_damage(dmg, ally, target, element)

        # Palette's Brush: stance damage multiplier
        from combat.weapon.palette_brush import get_brush_damage_mult
        final_dmg = int(final_dmg * get_brush_damage_mult(ally))

        # ── Pierce (Magical trait): ignore portion of enemy elemental resistance ──
        if pre_dmg and pre_dmg.get("res_ignore", 0) > 0 and element:
            target_res = target.get("elemental_res", {}).get(element, 1.0)
            if target_res < 1.0:
                attacker_dmg_mult = ally.get("elemental_dmg", {}).get(element, 1.0)
                mitigated_res = 1.0 + (target_res - 1.0) * (1.0 - pre_dmg["res_ignore"])
                final_dmg = int(dmg * attacker_dmg_mult * mitigated_res)
                final_dmg = max(0, final_dmg)
                c_print(f"  🔮 Pierce! {target['name']}'s {element} resistance is partially bypassed.")

        # Captain's Cutlass: High Tide + Rally attack bonuses
        from combat.weapon.captain_cutlass import get_high_tide_attack_bonus, get_rally_attack_bonus
        final_dmg += get_high_tide_attack_bonus(ally, final_dmg)
        final_dmg += get_rally_attack_bonus(ally, final_dmg)
        final_dmg = max(0, final_dmg)
        
        # Wonderland: Jabberwock's Bane — bonus damage vs boss enemies
        if target.get("boss"):
            from wonderland_curses import get_jabberwock_bane_multiplier
            bane_mult = get_jabberwock_bane_multiplier(player)
            if bane_mult > 0:
                bonus_dmg = int(final_dmg * bane_mult)
                final_dmg += bonus_dmg
                if bonus_dmg > 0:
                    c_print(f"  ⚔️ Vorpal blessing surges! +{bonus_dmg} bonus damage!")
        
        target["hp"] -= final_dmg
        # ── Sky Piercer: execute non-superboss enemies left at/below threshold ──
        from combat.weapon.sky_piercer import check_sky_piercer_execute
        check_sky_piercer_execute(ally, target, final_dmg)
        # Palette's Brush: strokes, Pigment Explosion, aura procs
        from combat.weapon.palette_brush import _actor_has_palette_brush, on_brush_attack_hit
        if _actor_has_palette_brush(ally):
            for m in on_brush_attack_hit(ally, target, final_dmg, enemies):
                c_print(f"  {m}")
        # ── Elemental Trait: on-hit effects (Ignite, Chain, Leech, Swift, Bulwark) ──
        if trait:
            from combat.elemental_traits import apply_trait
            apply_trait(trait, ally, target, enemies, final_dmg)

        # Vileheart Pendant: chance to poison on physical hit
        from combat.vileheart_venom import try_vileheart_venom_proc
        if try_vileheart_venom_proc(ally, target):
            c_print(f"  🧪 Vileheart Pendant: {target['name']} is poisoned!")

        # ── Grandmother's Axe / Woodcutter's Broken Axe: bleed-pop passive ──
        if equipped_weapon and target["hp"] > 0:
            weapon_special = equipped_weapon.get("special", "")
            if weapon_special in ("grandmothers_axe", "woodcutter_broken"):
                # Check if target is bleeding
                bleed_debuff = None
                for d in target.get("active_debuffs", []):
                    if d.get("type") == "bleed":
                        bleed_debuff = d
                        break
                if bleed_debuff:
                    chance = 0.40 if weapon_special == "grandmothers_axe" else 0.20
                    if random.random() < chance:
                        from combat.status_effects import detonate_bleed
                        det_dmg, det_msgs = detonate_bleed(target)
                        for det_msg in det_msgs:
                            c_print(f"  {det_msg}")
                        # No heal — pure damage pop (unlike Chrysalis)
                        if target["hp"] <= 0:
                            if on_kill:
                                on_kill(target, enemies)
                            # ── Elemental Trait: on-kill effects (Douse, Purge) ──
                            if trait:
                                from combat.elemental_traits import apply_trait_on_kill
                                apply_trait_on_kill(trait, ally, target, enemies)
                            c_print(f"  {ally['name']} defeated {target['name']}!")

        # Apply race passive life steal (Vampire)
        from combat.ally_skills import get_race_passive
        race_passive = get_race_passive(ally.get("race"))
        if race_passive:
            effect = race_passive.get("effect", {})
            if effect.get("type") == "life_steal" and final_dmg > 0:
                ls = effect.get("value", 0)
                heal = int(final_dmg * ls)
                old_hp = ally["current_hp"]
                ally["current_hp"] = min(old_hp + heal, ally["max_hp"])
                actual = ally["current_hp"] - old_hp
                if actual > 0:
                    c_print(f"  [{race_passive['name']}] {ally['name']} recovers {actual} HP!")

        verb = "strikes"
        if "Dexterity" in scaling_stats:
            verb = "shoots" if "bow" in equipped_weapon.get("id", "") else "pierces"
        elif "Learning" in scaling_stats:
            verb = "blasts"

        crit_tag = format_critical_tag(is_crit)
        is_crit_bool = bool(crit_tag)
        from combat.helpers import format_damage_msg
        c_print("  " + format_damage_msg(ally['name'], target['name'], final_dmg, element=element, crit=is_crit_bool))
        if target["hp"] <= 0:
            if on_kill:
                on_kill(target, enemies)
            # ── Elemental Trait: on-kill effects (Douse, Purge) ──
            if trait:
                from combat.elemental_traits import apply_trait_on_kill
                apply_trait_on_kill(trait, ally, target, enemies)
            c_print(f"  {ally['name']} defeated {target['name']}!")
            # Captain's Cutlass: High Tide stack on kill (player and ally wielders)
            from combat.weapon.captain_cutlass import check_high_tide_kill
            check_high_tide_kill(ally, target)
            check_high_tide_kill(player, target)
        return "continue"

    # ----- DEFEND -----
    elif action == "d":
        c_print(f"  {ally['name']} braces for impact, raising their guard.")
        ally["defending_this_turn"] = True
        return "continue"

    # ----- USE ITEM -----
    elif action == "u":
        combat_items = [
            (idx, item) for idx, item in enumerate(player.get("inventory", []))
            if item.get("type") in ["consumable", "utility"]
        ]
        if not combat_items:
            c_print("  No usable items in the shared inventory.")
            return "retry"

        c_print("\n  Shared Battle Inventory:")
        for display_idx, (_, itm) in enumerate(combat_items):
            qty = itm.get("count", 1)
            qty_str = f" x{qty}" if qty > 1 else ""
            c_print(f"  {display_idx+1}. {itm['name']}{qty_str} ({itm['type']})")

        try:
            choice = int(c_input("  Use which item? (0 to cancel): ")) - 1
            if choice < 0 or choice >= len(combat_items):
                return "retry"
            true_idx, item = combat_items[choice]
            msg = ""
            target = None

            # ── Potion Sickness: only blocks healing consumables (not buffs/utility items) ──
            is_healing_item = (
                item.get("type") == "consumable" and
                item.get("power", 0) > 0
            )
            if is_healing_item and ally.get("potion_sickness", 0) > 0:
                c_print(f"  {ally['name']} is still queasy from the last potion! ({ally['potion_sickness']} turn(s) remaining)")
                return "retry"

            # Items that need an enemy target: utility items with debuff/damage keys.
            # Consumables never need a target (they always affect the user).
            # Escape/flee/capture items handle their own target logic separately.
            affects_enemy = (
                any(k in item for k in ["status", "blind_enemy", "damage_over_time",
                                         "poison_damage", "stun_chance", "expose_armor",
                                         "burn_tier", "shock_damage"]) or
                (item.get("type") == "utility" and
                 item.get("power", item.get("base_power", 0)) > 0 and
                 "escape_bonus" not in item and
                 not item.get("fixed_flee") and
                 not item.get("capture_net"))
            )
            if affects_enemy:
                if len(enemies) > 1:
                    try:
                        t_choice = int(c_input(f"  Select target for {item['name']}: ")) - 1
                        if t_choice < 0 or t_choice >= len(enemies):
                            c_print("  Invalid target choice.")
                            return "retry"
                        target = enemies[t_choice]
                    except ValueError:
                        c_print("  Invalid input.")
                        return "retry"
                else:
                    target = enemies[0]

            # Healing items affect the ally using them
            if "power" in item and item.get("type") == "consumable":
                old_hp = ally["current_hp"]
                new_hp = min(old_hp + item["power"], ally["max_hp"])
                healed_amount = new_hp - old_hp
                ally["current_hp"] = new_hp
                msg += f"{ally['name']} recovers {healed_amount} HP. "

            if "heal_over_time" in item:
                ally.setdefault("active_buffs", []).append({
                    "type": "hot",
                    "value": item["heal_over_time"],
                    "remaining": item.get("duration", 3)
                })
                msg += f"{ally['name']} starts regenerating {item['heal_over_time']} HP each turn. "

            if "temp_stat" in item:
                stat = item["temp_stat"]
                val = item.get("base_power", 3)
                ally.setdefault("active_buffs", []).append({
                    "stat": stat,
                    "value": val,
                    "remaining": item.get("duration", 4)
                })
                msg += f"{ally['name']}'s {stat} increases by {val} for {item.get('duration',4)} turns. "

            if "defense_buff" in item:
                ally.setdefault("active_buffs", []).append({
                    "type": "defense",
                    "value": item["defense_buff"],
                    "remaining": item.get("duration", 3)
                })
                msg += f"Damage taken by {ally['name']} reduced by {item['defense_buff']} for {item.get('duration',3)} turns. "

            if item.get("cure_curse"):
                from combat.status_effects import cure_curse
                result = cure_curse(ally)
                if result == "cured":
                    msg += "The dark curse is lifted! "
                else:
                    msg += "Not cursed. "

            if item.get("cure_poison"):
                before = len([d for d in ally.get("active_debuffs", []) if d["type"] == "poison"])
                ally["active_debuffs"] = [d for d in ally.get("active_debuffs", []) if d["type"] != "poison"]
                after = len([d for d in ally.get("active_debuffs", []) if d["type"] == "poison"])
                if before > after:
                    msg += "The poison is cleansed. "
                else:
                    msg += "Not poisoned. "

            if item.get("expose_armor"):
                if target is None:
                    # Fallback: affects_enemy should have caught this; if not, pick first alive enemy
                    alive = [e for e in enemies if e["hp"] > 0]
                    if alive:
                        target = alive[0]
                    else:
                        c_print("  No valid target for armour shatter!")
                        return "retry"
                from combat.status_effects import apply_expose
                result, new_con = apply_expose(target, item["expose_armor"])
                if result == "applied":
                    msg += f"{target['name']}'s armour is shattered! Armour reduced to {new_con}. "
                else:
                    msg += f"{target['name']}'s armour is already fully exposed! "
            if item.get("burn_tier"):
                from combat.status_effects import apply_burn
                result = apply_burn(target, tier=item["burn_tier"], duration=item.get("burn_duration", 3))
                if result == "applied":
                    msg += f"{target['name']} catches fire! "
                elif result == "upgraded":
                    msg += f"The flames intensify on {target['name']}! "
                elif result == "intensified":
                    msg += f"The blaze grows stronger on {target['name']}! "
                else:
                    msg += f"The burn on {target['name']} is refreshed. "
            if item.get("shock_damage"):
                from combat.status_effects import apply_shock
                result = apply_shock(target, item["shock_damage"], item.get("shock_duration", 3))
                if result == "applied":
                    msg += f"{target['name']} is jolted with electricity! "
                else:
                    msg += f"The shock on {target['name']} is renewed! "
            if item.get("type") == "utility" and "damage_over_time" not in item and "stun_chance" not in item:
                item_power = item.get("power", item.get("base_power", 0))
                if item_power > 0:
                    from combat.stat_milestones import get_dexterity_damage_bonus_for_ally
                    dmg = item_power + get_dexterity_damage_bonus_for_ally(ally)
                    armor = target["con_mod"]
                    if "armor_pierce" in item:
                        armor = max(0, armor - item["armor_pierce"])
                        msg += f"(ignores {item['armor_pierce']} armor) "
                    final_dmg = max(1, dmg - armor)
                    target["hp"] -= final_dmg
                    # ── Sky Piercer: execute non-superboss enemies left at/below threshold ──
                    from combat.weapon.sky_piercer import check_sky_piercer_execute
                    check_sky_piercer_execute(ally, target, final_dmg)
                    from combat.helpers import format_damage_msg
                    msg += format_damage_msg(ally['name'], target['name'], final_dmg, skill_name=item.get('name', 'Item')) + " "

            if "poison_damage" in item:
                from combat.status_effects import apply_poison
                apply_poison(target, item["poison_damage"], item.get("poison_duration", 3))
                msg += f"{target['name']} is poisoned! "

            if "stun_chance" in item:
                if random.random() < item["stun_chance"]:
                    target["stunned"] = True
                    msg += f"{target['name']} is stunned! "
                else:
                    msg += "The stun attempt fails. "

            if item.get("status") == "slow":
                target["slowed"] = True
                msg += f"{target['name']} is slowed. "

            if item.get("blind_enemy"):
                target["blinded"] = True
                target.setdefault("active_debuffs", []).append({
                    "type": "blind",
                    "remaining": 3
                })
                msg += f"{target['name']} is blinded. "

            c_print(f"  {msg}")
            remove_item_by_reference(player, item)
            if is_healing_item:
                ally["potion_sickness"] = 2

            if not [e for e in enemies if e["hp"] > 0]:
                return "victory"
            if ally["current_hp"] <= 0:
                return "dead"

        except (ValueError, IndexError):
            c_print("  Invalid choice.")
            return "retry"
        return "continue"

    return "retry"


# ══════════════════════════════════════════════════════════════════════════════
# Wonderland Heroine System (Phase 17 & 18)
# ══════════════════════════════════════════════════════════════════════════════

HEROINE_ALLY_STAT_PER_LEVEL = 0.22   # Heroines get +0.22 stats per level (vs 0.18 for regular)
HEROINE_ALLY_HP_PER_LEVEL = 4        # HP = base_hp + (level - 1) * 4

_HEROINE_TEMPLATE_KEYS = {
    "alice":     "wonderland_alice",
    "red_hood":  "wonderland_red_hood",
    "dorothy":   "wonderland_dorothy",
    "palette":   "wonderland_palette",
}

_HEROINE_INTERNAL_KEYS = {
    "alice":     "wl_alice_state",
    "red_hood":  "wl_redhood_state",
    "dorothy":   "wl_dorothy_state",
    "palette":   "palette_state",
}

_HEROINE_PERMANENT_FLAGS = {
    "alice":     "wonderland_heroine_alice_permanent",
    "red_hood":  "wonderland_heroine_redhood_permanent",
    "dorothy":   "wonderland_heroine_dorothy_permanent",
    "palette":   "palette_heroine_permanent",
}

# ── Auto-equip builds for temp heroines (4 slots per heroine) ──────────
# Each tuple is (weapon_id, armor_id, accessory1_id, accessory2_id)
_HEROINE_EQUIPMENT_BUILDS = {
    "alice":    ("inferno_greatsword", "blaze_battle_harness", "stone_belt", "ember_bracers"),
    "red_hood": ("zephyr_bow", "shadow_wraps", "gale_boots", "cyclone_anklet"),
    "dorothy":  ("nether_grimoire", "arcane_vestments", "mystic_crown", "astral_ring"),
}

def _get_heroine_floor_rarity(floor):
    """Determine equipment rarity for a heroine based on the floor they join.
    
    Returns (rarity_str, enhance_level) tuple.
    """
    if floor <= 20:
        return "common", 5
    elif floor <= 35:
        return "uncommon", 5
    elif floor <= 45:
        return "rare", 5
    else:
        return "epic", 5


def _auto_equip_heroine(ally, heroine_key, floor):
    """Auto-equip a temp heroine with 4 pieces of gear based on floor tier.
    
    The gear is built directly onto the ally — it does NOT go through the
    player's inventory. This represents the heroine's own starting equipment.
    
    Args:
        ally: the heroine ally dict (mutated in-place)
        heroine_key: "alice", "red_hood", or "dorothy"
        floor: the dungeon floor at which they joined
    """
    from resources.items import build_item

    build = _HEROINE_EQUIPMENT_BUILDS.get(heroine_key)
    if not build:
        return

    rarity, enhance = _get_heroine_floor_rarity(floor)

    slot_map = ["weapon", "armor", "accessory1", "accessory2"]
    for item_id, slot in zip(build, slot_map):
        try:
            item = build_item(item_id, rarity=rarity, enhance=enhance)
            ally["equipped"][slot] = item
        except KeyError:
            # Skip if item_id doesn't exist (safety)
            pass

    # Recalculate elemental profile after equipping
    from combat.elemental import compute_ally_elemental
    e_res, e_dmg = compute_ally_elemental(ally)
    ally["elemental_res"] = e_res
    ally["elemental_dmg"] = e_dmg


def compute_heroine_temp_stats(base_mods, player_level):
    """Compute heroine stats at player level using heroine formula.
    
    Heroines use: stat = max(1, base_mod + (player_level - 1) * 0.22)
    No 0.85 multiplier — heroines are special characters.
    """
    from resources.races_classes import ATTRIBUTES
    scaled = {}
    for attr in ATTRIBUTES:
        base = base_mods.get(attr, 0)
        scaled[attr] = max(1, int(base + (player_level - 1) * HEROINE_ALLY_STAT_PER_LEVEL))
    return scaled


def create_heroine_ally(player, heroine_key, floor=None):
    """Create a combat-ready heroine ally scaled to player level.
    
    Args:
        player: player dict
        heroine_key: "alice", "red_hood", or "dorothy"
        floor: current dungeon floor (for auto-equip scaling); defaults to 1 if None
    
    Returns:
        ally dict ready for combat, or None if template not found
    """
    from resources.enemies import ENEMIES
    from combat.elemental import compute_ally_elemental
    from resources.races_classes import ATTRIBUTES

    template_key = _HEROINE_TEMPLATE_KEYS.get(heroine_key)
    if not template_key:
        return None

    template = ENEMIES.get(template_key)
    if not template:
        return None

    player_level = player.get("level", 1)

    # Compute stats using heroine formula
    base_mods = template.get("mods", {})
    scaled_attrs = compute_heroine_temp_stats(base_mods, player_level)

    # Compute HP: base_hp + (level - 1) * 4
    base_hp = template.get("base_hp", 20)
    hp = base_hp + (player_level - 1) * HEROINE_ALLY_HP_PER_LEVEL

    race = template.get("race", "Human")
    name = template.get("name", heroine_key.title())

    ally = {
        "name": name,
        "key": template_key,
        "level": player_level,           # Frozen at join level
        "attributes": scaled_attrs,
        "current_hp": hp,
        "max_hp": hp,
        "equipped": {"weapon": None, "armor": None, "accessory1": None, "accessory2": None},
        "active_buffs": [],
        "active_debuffs": [],
        "blinded": False,
        "slowed": False,
        "stunned": False,
        "frozen": False,
        "cursed": False,
        "dreaded": False,
        "silenced": False,
        "is_ally": True,
        "affection": 50,
        "affection_cap": 100,
        "engaged": False,
        "married": False,
        "monster_girl": False,
        "exp": 0,
        "level_hp_bonus": max(0, (player_level - 1) * 4),
        "level_cap": 10,
        "defeated": False,
        # Heroine-specific fields
        "_heroine_key": heroine_key,
        "_wonderland_temp": True,
        "_heroine_passive": template.get("_heroine_passive"),
        # Skill system
        "passive_skill": None,
        "innate_skills": [],
        "learned_skills": [],
        "learning": None,
        "skill_cooldowns": {},
        "skill_mastery": {},
        "race": race,
    }

    # Add elemental stats
    e_res, e_dmg = compute_ally_elemental(ally)
    ally["elemental_res"] = e_res
    ally["elemental_dmg"] = e_dmg

    # Initialize skill system
    from combat.ally_skills import initialize_ally_skills
    initialize_ally_skills(ally, template_key, race)

    # Auto-equip based on floor tier and build (temp heroines only)
    effective_floor = floor if floor is not None else player.get("saved_dungeon_floor", 1)
    _auto_equip_heroine(ally, heroine_key, effective_floor)

    return ally


def promote_heroine_to_permanent(player, ally, join_level=None):
    """Promote a temp heroine to permanent status.
    
    Called when the heroine's associated superboss is defeated.
    
    - Freezes stats at current values
    - Sets exp to 0 so they can start gaining XP
    - Enables equipment slots
    - Sets high base affection
    - Marks _wonderland_temp = False
    
    Args:
        player: player dict
        ally: the heroine ally dict
        join_level: the level at which they joined (frozen level)
    """
    if join_level is None:
        join_level = ally.get("level", 1)

    ally["_wonderland_temp"] = False
    ally["level"] = join_level
    ally["level_hp_bonus"] = max(0, (join_level - 1) * 4)
    ally["exp"] = 0
    ally["affection"] = 60  # High base — they chose to stay
    ally["affection_cap"] = 100
    ally["level_cap"] = 99  # No cap for permanent heroines

    # Preserve ALL equipped items on promote (not just quest items)
    # This fixes the bug where auto-equip gear was being deleted when a
    # heroine became permanent.  Quest items (Vorpal Blade, Grandmother's
    # Axe, Ruby Slippers) are now preserved alongside any other gear the
    # heroine was wearing.
    old_equipped = ally.get("equipped", {})
    ally["equipped"] = {
        "weapon": old_equipped.get("weapon"),
        "armor": old_equipped.get("armor"),
        "accessory1": old_equipped.get("accessory1"),
        "accessory2": old_equipped.get("accessory2"),
    }

    # Strip wonderland_only flag from equipped items now that the heroine
    # is permanent — these items will exist outside Wonderland.
    for slot in ally["equipped"]:
        item = ally["equipped"].get(slot)
        if item and item.get("wonderland_only"):
            item.pop("wonderland_only", None)

    ally["monster_girl"] = False

    # Grant permanent unlock passive skill
    heroine_key = ally.get("_heroine_key")
    perm_passive_map = {
        "alice":    "vorpal_instinct",
        "red_hood": "grandmothers_lesson",
        "dorothy":  "somewhere_over_rainbow",
        "palette":  "living_pigment",
    }
    perm_passive = perm_passive_map.get(heroine_key)
    if perm_passive:
        ally["_heroine_permanent_passive"] = perm_passive

    return ally


def get_heroine_passive_def(passive_id):
    """Get the definition for a heroine passive skill."""
    from combat.ally_skills import _load_innate_and_learnable
    _, learnable_data = _load_innate_and_learnable()
    heroine_passives = learnable_data.get("heroine_passives", {})
    return heroine_passives.get(passive_id)


def get_heroine_in_party(player, heroine_key):
    """Find a heroine in the player's party by key ("alice", "red_hood", "dorothy")."""
    for ally in player.get("allies", []):
        if ally.get("_heroine_key") == heroine_key:
            return ally
    return None


def set_heroine_state(player, heroine_key, state):
    """Set the state of a heroine quest line.
    
    Args:
        player: player dict
        heroine_key: "alice", "red_hood", or "dorothy"
        state: "unmet", "intro", "temp", "permanent", or "declined"
    """
    state_key = _HEROINE_INTERNAL_KEYS.get(heroine_key)
    if state_key:
        player[state_key] = state

    if state == "permanent":
        perm_key = _HEROINE_PERMANENT_FLAGS.get(heroine_key)
        if perm_key:
            player[perm_key] = True


def get_heroine_state(player, heroine_key):
    """Get the current state of a heroine quest line."""
    state_key = _HEROINE_INTERNAL_KEYS.get(heroine_key)
    if state_key:
        return player.get(state_key, "unmet")
    return "unmet"


def apply_heroine_permanent_passive(ally):
    """Apply the permanent unlock passive to a heroine ally.
    
    Called after promote_heroine_to_permanent() to grant the special passive.
    """
    perm_passive_id = ally.get("_heroine_permanent_passive")
    if not perm_passive_id:
        return

    passive_def = get_heroine_passive_def(perm_passive_id)
    if not passive_def:
        return

    # Store the passive definition on the ally for combat checks
    ally["_heroine_perm_passive_def"] = passive_def


def trigger_heroine_permanent_unlock(player, heroine_key, boss_flag=None):
    """Standard handler for superboss defeat → heroine permanent unlock.
    
    Call this from superboss on_kill hooks to promote the associated heroine.
    
    Args:
        player: player dict
        heroine_key: "alice", "red_hood", or "dorothy"
        boss_flag: player flag to set (e.g., "wl_boss_defeated_jabberwock")
    
    Returns:
        ally dict if heroine was found and promoted, None otherwise
    """
    ally = get_heroine_in_party(player, heroine_key)
    if not ally:
        return None

    join_level = ally.get("level", player.get("level", 1))
    promote_heroine_to_permanent(player, ally, join_level)
    set_heroine_state(player, heroine_key, "permanent")

    if boss_flag:
        player[boss_flag] = True

    return ally
