# dungeon_rooms.py — Non-combat room handlers and ASCII exploration map
"""
Room types:
    fountain    — Healing and buffing magical fountain
    merchant    — Wandering merchant (reuses travel merchant logic)
    stat_check  — Narrative skill challenge (player or ally can attempt)
    treasure    — Guaranteed rare+ item cache
    trap        — Avoidable hazard (DEX+WIS check)
"""

import random
from character import player_max_hp
from combat.stats import compute_player_stats
from utils import clear_screen, advance_time
from resources.items import ITEMS, ITEM_RARITY, build_item
from inventory import add_item_to_inventory, remove_item_by_reference
from leveling import gain_exp, gain_exp_ally
from combat.combat_engine import combat
from combat.ally import get_alive_allies

# Import merchant helpers from travel events
from facilities.travel_events import (
    _random_item_id, _item_stat_line, _charisma_discount,
    _merchant_price, _sell_price, _merchant_stock_rarity, _add_to_inv
)

# ── GUI terminal detection (safe import for terminal mode) ──────────
try:
    from gui.terminal import get_terminal as _get_gui_terminal
except ImportError:
    _get_gui_terminal = lambda: None


def _term():
    """Return the GUI Terminal if running in GUI mode, else None."""
    return _get_gui_terminal()


def _tprint(*args, sep=" "):
    """Print to GUI if available, else to terminal."""
    t = _term()
    text = sep.join(str(a) for a in args)
    if t:
        t.print(text)
    else:
        print(text)


def _tpause(prompt="Press Enter to continue..."):
    """Pause for user acknowledgement."""
    t = _term()
    if t:
        t.pause(prompt)
    else:
        input(prompt)


def _tclear():
    """Clear screen (no-op in GUI since output is managed by the panel)."""
    t = _term()
    if t:
        t.clear()
    else:
        from utils import clear_screen
        clear_screen()


def _tmenu(options, prompt="Choose an option:", allow_cancel=False, cancel_label="Cancel"):
    """Show a menu; returns 0-based index or -1."""
    t = _term()
    if t:
        return t.menu(options, prompt=prompt, allow_cancel=allow_cancel, cancel_label=cancel_label)
    else:
        for i, opt in enumerate(options):
            print(f"{i+1}. {opt}")
        if allow_cancel:
            print(f"0. {cancel_label}")
        try:
            choice = input(prompt + " ").strip()
            idx = int(choice) - 1
            if allow_cancel and idx == -1:
                return -1
            if 0 <= idx < len(options):
                return idx
        except (ValueError, IndexError):
            pass
        return -1


def _tinput(prompt=""):
    """Free-text input. Falls back to terminal input() if no GUI."""
    t = _term()
    if t:
        return t.input(prompt)
    else:
        return input(prompt)


# ── Room type weights ─────────────────────────────────────────────
ROOM_TYPE_WEIGHTS = {
    "fountain": 20,
    "merchant": 15,
    "stat_check": 25,
    "treasure": 20,
    "trap": 20,
}

# ── Stat check events ───────────────────────────────────────────────
STAT_CHECK_EVENTS = {
    "heal_wounded": {
        "name": "Wounded Adventurer",
        "desc": "A wounded adventurer lies against the wall, bleeding from a nasty gash. They look at you with pleading eyes.",
        "stat": "Wisdom",
        "base_dc": 12,
        "dc_floor_mult": 0.6,
    },
    "bury_corpse": {
        "name": "Ancient Corpse",
        "desc": "The skeletal remains of a long-dead explorer rest in the corner. Their equipment is rusted, but their spirit seems restless.",
        "stat": "Strength",
        "base_dc": 10,
        "dc_floor_mult": 0.8,
    },
    "monster_approaching": {
        "name": "Monster Approaching",
        "desc": "A low growl echoes from the shadows. A beast emerges from the darkness, sizing up your party.",
        "stat": "Charisma",
        "base_dc": 11,
        "dc_floor_mult": 0.6,
    },
}

# ── Wonderland stat check events ─────────────────────────────────────
WL_STAT_CHECK_EVENTS = {
    "wl_tea_party": {
        "name": "The Mad Hatter's Tea Party",
        "desc": "A long table stretches across the chamber, set with countless teapots, cups, and half-eaten pastries. "
               "The Mad Hatter and March Hare wave you over. 'Clean cup! Move down!' The Dormouse snores into a sugar bowl.",
        "stat": "Charisma",
        "base_dc": 11,
        "dc_floor_mult": 0.6,
    },
    "wl_paint_roses": {
        "name": "Painting the Roses Red",
        "desc": "Three card soldiers huddle around a rose bush growing impossibly through the floor. "
               "They're frantically painting white roses red. 'Oh dear, oh dear! The Queen will have our heads!' "
               "One of them shoves a paintbrush toward you.",
        "stat": "Dexterity",
        "base_dc": 10,
        "dc_floor_mult": 0.7,
    },
    "wl_cat_riddle": {
        "name": "The Cheshire Cat's Riddle",
        "desc": "A grin appears in the air — first the teeth, then the stripes, then the rest of the Cat. "
               "He coils around a floating branch. 'I have a riddle for you. Answer well... or I might just have to play.' "
               "His claws gleam in the dim light.",
        "stat": "Wisdom",
        "base_dc": 12,
        "dc_floor_mult": 0.7,
    },
}


ROOM_LABELS = {
    "combat": "--- Combat Chamber ---",
    "fountain": "✨  Fountain Chamber",
    "merchant": "🏺  Merchant's Corner",
    "stat_check": "📜  Mysterious Scene",
    "treasure": "💎  Treasure Vault",
    "trap": "⚠️   Suspicious Passage",
}

# ── Wonderland room labels ───────────────────────────────────────────
WL_ROOM_LABELS = {
    "combat": "🐇  Curiouser Chamber",
    "fountain": "🫖  Tea Party Nook",
    "merchant": "🐛  Caterpillar's Clearing",
    "stat_check": "🎩  Wonderland Encounter",
    "treasure": "👑  Queen's Cache",
    "trap": "🃏  Card Soldiers' Ambush",
}


def get_stat_check_events(region=None):
    """Return the appropriate stat check events dict for the given region."""
    if region == "wonderland":
        return WL_STAT_CHECK_EVENTS
    return STAT_CHECK_EVENTS


def get_room_labels(region=None):
    """Return the appropriate room labels dict for the given region."""
    if region == "wonderland":
        return WL_ROOM_LABELS
    return ROOM_LABELS


def pick_non_combat_type():
    """Pick a random non-combat room type using weighted selection."""
    types = list(ROOM_TYPE_WEIGHTS.keys())
    weights = list(ROOM_TYPE_WEIGHTS.values())
    return random.choices(types, weights=weights)[0]


# ═══════════════════════════════════════════════════════════════════
# PARTY MEMBER SELECTION
# ═══════════════════════════════════════════════════════════════════

def _calc_pass_probability(stat, dc):
    """Calculate the probability (0.0–1.0) of passing a d20 + stat vs DC check.
    Accounts for natural 1 auto-fail and natural 20 auto-success."""
    need = dc - stat  # minimum d20 roll needed
    if need <= 1:
        return 0.95  # natural 1 still fails
    if need >= 20:
        return 0.05  # natural 20 still succeeds
    return min(0.95, max(0.05, (21 - need) / 20))


def _select_party_member(player, stat_name=None, dc=None):
    """Show alive party members and let player choose who performs a check.
    If stat_name and dc are provided, shows the pass probability for each member."""
    party = []
    if player.get("current_hp", 0) > 0:
        party.append(player)
    party.extend(get_alive_allies(player))
    if not party:
        return None

    show_prob = stat_name is not None and dc is not None

    _tprint("\nWho will attempt this?")
    options = []
    for member in party:
        if member is player:
            line = f"{player['name']} (You) — HP: {player['current_hp']}/{player_max_hp(player)}"
            if show_prob:
                mstat = _get_member_stat(member, stat_name, player)
                prob = _calc_pass_probability(mstat, dc)
                line += f"  |  Pass: {prob:.0%}"
        else:
            line = f"{member['name']} — HP: {member['current_hp']}/{member['max_hp']}"
            if show_prob:
                mstat = _get_member_stat(member, stat_name, player)
                prob = _calc_pass_probability(mstat, dc)
                line += f"  |  Pass: {prob:.0%}"
        options.append(line)

    choice_idx = _tmenu(options, prompt="Choice:", allow_cancel=True, cancel_label="Leave it alone")
    if choice_idx == -1:
        return None
    if 0 <= choice_idx < len(party):
        return party[choice_idx]
    return None


def _get_member_stat(member, stat_name, player):
    """Get the relevant stat for a party member.
    Special composite stats:
      "Agility" → (DEX + WIS) // 2 (used by trap rooms)
    """
    # Composite stats
    if stat_name == "Agility":
        if member is player:
            _, _, dex, _, wis, _ = compute_player_stats(member)
        else:
            dex = member["attributes"].get("Dexterity", 0)
            wis = member["attributes"].get("Wisdom", 0)
        return (dex + wis) // 2

    if member is player:
        s, c, d, l, w, ch = compute_player_stats(member)
        return {
            "Strength": s,
            "Constitution": c,
            "Dexterity": d,
            "Learning": l,
            "Wisdom": w,
            "Charisma": ch,
        }.get(stat_name, 0)
    else:
        return member["attributes"].get(stat_name, 0)


def _roll_stat_check(member, stat_name, dc, player):
    """Roll a d20 + stat against DC. Returns (success, roll, total, stat)."""
    stat = _get_member_stat(member, stat_name, player)
    # Wonderland: Through the Looking Glass — reroll low d20 rolls
    from wonderland_curses import roll_d20_with_looking_glass
    roll, _ = roll_d20_with_looking_glass(player, verbose=True)
    total = roll + stat
    success = total >= dc
    return success, roll, total, stat


# ═══════════════════════════════════════════════════════════════════
# ASCII MAP
# ═══════════════════════════════════════════════════════════════════

def render_ascii_map(rooms, explored, current_room_idx, floor, player=None):
    """Return a 5×2 ASCII grid string showing dungeon floor progress.
    
    No party status — that is rendered separately via render_party_status().
    The player parameter is accepted for backward compatibility but unused here.
    """
    def get_symbol(idx):
        if idx == current_room_idx:
            return "P"
        if idx in explored:
            room_type = rooms[idx].get("type", "combat")
            if room_type == "combat":
                if rooms[idx].get("is_boss"):
                    return "B"
                return "C"
            return "N"
        return "?"

    lines = []
    lines.append(f"=== FLOOR {floor} MAP ===")
    lines.append("")

    # 5×2 grid
    lines.append("┌───┬───┬───┬───┬───┐")
    row1 = "│"
    for i in range(5):
        row1 += f" {get_symbol(i)} │"
    lines.append(row1)

    nums1 = "│"
    for i in range(5):
        nums1 += f"{i + 1:^3}│"
    lines.append(nums1)

    lines.append("├───┼───┼───┼───┼───┤")

    row2 = "│"
    for i in range(5, 10):
        row2 += f" {get_symbol(i)} │"
    lines.append(row2)

    nums2 = "│"
    for i in range(5, 10):
        nums2 += f"{i + 1:^3}│"
    lines.append(nums2)

    lines.append("└───┴───┴───┴───┴───┘")

    lines.append("")
    lines.append("  [P] You  [C] Combat  [N] Special  [B] Boss")
    lines.append("  [?] Unexplored")
    lines.append(f"\nCompleted: {len(explored)}/{len(rooms)} rooms")

    return "\n".join(lines)


def render_party_status(player):
    """Return an ASCII string showing all party members with HP and buff/debuff tags.
    
    Split into FRONT (active combat, first 4 including player) and 
    BACK (reserve) rows. Designed for display in a separate frame from the map.
    """
    from combat.ally import (ensure_party_order,
                             get_all_active_allies_including_defeated,
                             get_all_reserve_allies_including_defeated)
    from combat.combat_ui import _get_entity_buff_tags, _hp_bar
    from character import player_max_hp

    ensure_party_order(player)
    front_allies = get_all_active_allies_including_defeated(player)
    back_allies = get_all_reserve_allies_including_defeated(player)

    lines = []
    lines.append("─" * 24)
    lines.append("  PARTY STATUS")
    lines.append("─" * 24)

    # Player (no sword emoji — saves width for 8 allies)
    php = player.get("current_hp", 0)
    pmax = player_max_hp(player)
    pbar = _hp_bar(php, pmax, width=8)
    ptag = _get_entity_buff_tags(player)
    lines.append(f"  {player['name'][:12]:<12} {pbar} {php:>3}/{pmax:<3}{ptag}")

    # Front row allies (wider name field — no emoji prefix)
    if front_allies:
        lines.append("  [FRONT]")
        for ally in front_allies:
            ahp = ally.get("current_hp", 0)
            amax = ally.get("max_hp", 1)
            abar = _hp_bar(ahp, amax, width=8)
            atag = _get_entity_buff_tags(ally)
            dflag = "†" if (ally.get("defeated") or ahp <= 0) else " "
            lines.append(f"  {dflag}{ally['name'][:12]:<12} {abar} {ahp:>3}/{amax:<3}{atag}")
    else:
        lines.append("  [FRONT] (empty)")

    # Back row allies (wider name field — no emoji prefix)
    if back_allies:
        lines.append("  [BACK]")
        for ally in back_allies:
            ahp = ally.get("current_hp", 0)
            amax = ally.get("max_hp", 1)
            abar = _hp_bar(ahp, amax, width=8)
            atag = _get_entity_buff_tags(ally)
            dflag = "†" if (ally.get("defeated") or ahp <= 0) else " "
            lines.append(f"  {dflag}{ally['name'][:12]:<12} {abar} {ahp:>3}/{amax:<3}{atag}")
    else:
        lines.append("  [BACK] (empty)")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════
# ROOM HANDLERS
# ═══════════════════════════════════════════════════════════════════

def handle_fountain_room(player, floor):
    """Sparkling fountain with healing and buffing properties."""
    _tprint("\n" + "=" * 50)
    _tprint("✨  A sparkling fountain bubbles with magical energy!")
    _tprint("The water glows faintly, shifting colors in the dim light.")
    _tprint("=" * 50)

    max_hp = player_max_hp(player)

    while True:
        _tprint("\nWhat do you do?")
        options = [
            "Drink — Restore 30% of your max HP",
            "Immerse yourself — Gain a random stat buff",
            "Splash water on allies — Heal allies for 15% HP",
            "Leave it be",
        ]
        choice_idx = _tmenu(options, prompt="Choice:")

        if choice_idx == 0:
            old_hp = player["current_hp"]
            from combat.stat_milestones import get_wisdom_bonus
            heal = int(max_hp * 0.30) + get_wisdom_bonus(player)
            player["current_hp"] = min(old_hp + heal, max_hp)
            actual = player["current_hp"] - old_hp
            _tprint(f"\nThe cool water revitalizes you! Healed {actual} HP.")
            _tprint(f"HP: {player['current_hp']}/{max_hp}")
            _tpause()
            return "continue"

        elif choice_idx == 1:
            stat = random.choice(["Strength", "Dexterity", "Constitution", "Wisdom", "Learning", "Charisma"])
            player.setdefault("active_buffs", []).append({
                "type": "floor_buff", "stat": stat, "value": 2, "remaining": 2, "source": "fountain"
            })
            _tprint(f"\nMagical energy surges through you! +2 {stat} for 2 floors.")
            _tpause()
            return "continue"

        elif choice_idx == 2:
            allies = get_alive_allies(player)
            if not allies:
                _tprint("\nYou have no allies to heal.")
                continue
            for ally in allies:
                old_hp = ally["current_hp"]
                heal = int(ally["max_hp"] * 0.15)
                ally["current_hp"] = min(old_hp + heal, ally["max_hp"])
                actual = ally["current_hp"] - old_hp
                _tprint(f"  {ally['name']} healed {actual} HP.")
            _tpause()
            return "continue"

        elif choice_idx == 3:
            _tprint("\nYou decide to leave the fountain untouched.")
            return "continue"
        else:
            _tprint("Invalid choice.")


def handle_merchant_room(player, floor):
    """Wandering merchant in a dungeon chamber."""
    _tprint("\n" + "=" * 50)
    _tprint("🏺  A wandering merchant has set up a makeshift stall!")
    _tprint('"Wares! Quality goods — fair price for a fellow crawler!"')
    _tprint("=" * 50)

    # Build stock: 2–3 items, floor-influenced rarity
    stock = []
    for _ in range(random.randint(2, 3)):
        item_id = _random_item_id()
        rarity = _merchant_stock_rarity(player)
        item = build_item(item_id, rarity)
        your_price, road_price = _merchant_price(player, item)
        stock.append((item, your_price, road_price))

    cha_disc = _charisma_discount(player)
    gold_line = f"\nYour gold: {player.get('gold', 0)}g"
    if cha_disc > 0:
        gold_line += f"  |  Charisma discount: {cha_disc:.0f}%"
    _tprint(gold_line)

    for i, (item, your_price, road_price) in enumerate(stock, 1):
        stat = _item_stat_line(item)
        if cha_disc > 0 and your_price < road_price:
            price_str = f"{your_price}g (road: {road_price}g)"
        else:
            price_str = f"{your_price}g"
        _tprint(f"  {i}. {item['name']}  {stat}  —  {price_str}")

    options = [f"Buy: {item['name']}" for item, _, _ in stock]
    options.append("Sell an item")
    options.append("Move on")

    while True:
        choice_idx = _tmenu(options, prompt="Choice:")
        if choice_idx == len(options) - 1 or choice_idx < 0:
            _tprint('"Safe roads... or rather, safe dungeons!"')
            _tpause()
            return "continue"

        if choice_idx == len(options) - 2:
            inv = player.get("inventory", [])
            if not inv:
                _tprint('  "Nothing I want off you."')
                _tpause()
                return "continue"

            _tprint("\nYour inventory:")
            sell_options = []
            for i, item in enumerate(inv):
                unit_price = _sell_price(player, item)
                count = item.get("count", 1)
                stack_price = unit_price * count
                count_str = f" (x{count})" if count > 1 else ""
                sell_options.append(f"{item['name']}{count_str}  —  {stack_price}g")

            sell_idx = _tmenu(sell_options, prompt="Sell which item?", allow_cancel=True, cancel_label="Never mind")
            if 0 <= sell_idx < len(inv):
                item = inv[sell_idx]
                gold = _sell_price(player, item) * item.get("count", 1)
                remove_item_by_reference(player, item, item.get("count", 1))
                player["gold"] = player.get("gold", 0) + gold
                _tprint(f'  Sold [{item["name"]}] for {gold}g.')
            else:
                _tprint("  Nothing sold.")
            _tpause()
            return "continue"

        if 0 <= choice_idx < len(stock):
            item, your_price, _ = stock[choice_idx]
            if player.get("gold", 0) >= your_price:
                player["gold"] -= your_price
                if _add_to_inv(player, item.copy()):
                    _tprint(f'  You purchase [{item["name"]}] for {your_price}g.')
                else:
                    _tprint('  Your bag is full — item dropped!')
                    player["gold"] += your_price
            else:
                _tprint(f'  "You\'re {your_price - player.get("gold", 0)}g short, friend."')
            _tpause()
            return "continue"
        else:
            _tprint("Invalid choice.")


def handle_treasure_room(player, floor):
    """Treasure room with guaranteed rare+ item."""
    _tprint("\n" + "=" * 50)
    _tprint("💎  A forgotten hoard gleams in the torchlight!")
    _tprint("Someone — or something — left these treasures here long ago.")
    _tprint("=" * 50)

    # Guaranteed rare+ item
    rarities = ["rare", "epic", "legendary"]
    if floor <= 10:
        weights = [0.60, 0.35, 0.05]
    elif floor <= 25:
        weights = [0.40, 0.45, 0.15]
    else:
        weights = [0.25, 0.50, 0.25]

    rarity = random.choices(rarities, weights=weights)[0]
    item_id = _random_item_id()
    item = build_item(item_id, rarity)

    _tprint(f"\nYou found: {item['name']}  {_item_stat_line(item)}")
    from inventory_ui import prompt_acquire_item
    prompt_acquire_item(player, item.copy())

    # Bonus gold
    gold = 20 + floor * 5 + random.randint(5, 15)
    player["gold"] = player.get("gold", 0) + gold
    _tprint(f"You also found {gold} gold in a small chest!")

    _tpause()
    return "continue"


def handle_trap_room(player, floor):
    """Trap room that can be avoided with a DEX + WIS check."""
    _tprint("\n" + "=" * 50)
    _tprint("⚠️  The floor ahead looks suspicious...")
    _tprint("Loose stones, scorch marks, and tiny needle holes dot the walls.")
    _tprint("=" * 50)

    dc = int(10 + floor * 1.5)
    _tprint(f"\nTrap Difficulty: {dc}")

    # For trap rooms: use the average of DEX + WIS (display as "Agility")
    member = _select_party_member(player, stat_name="Agility", dc=dc)
    if member is None:
        _tprint("\nYou carefully back away and find another path around the trap.")
        return "continue"

    # Determine stat to use
    if member is player:
        _, _, dex, _, wis, _ = compute_player_stats(player)
    else:
        dex = member["attributes"].get("Dexterity", 0)
        wis = member["attributes"].get("Wisdom", 0)

    stat = (dex + wis) // 2
    roll = random.randint(1, 20)
    total = roll + stat
    success = total >= dc

    name = member.get("name", "You") if member is player else member["name"]
    _tprint(f"\n{name} attempts to disarm the trap...")
    _tprint(f"Roll: {roll} + {stat} (DEX+WIS) = {total} vs DC {dc}")

    if success:
        _tprint(f"\n✅  Success! The trap is carefully disarmed.")
        # Hidden loot
        gold = 15 + floor * 4 + random.randint(3, 10)
        player["gold"] = player.get("gold", 0) + gold
        _tprint(f"You find {gold} gold hidden in the trap mechanism!")

        # Small chance for extra item
        if random.random() < 0.30:
            rarity = random.choices(["common", "uncommon", "rare"], weights=[0.50, 0.35, 0.15])[0]
            item_id = _random_item_id()
            item = build_item(item_id, rarity)
            if not _add_to_inv(player, item.copy()):
                _tprint(f"You also found: {item['name']}! (but your bag is full — dropped!)")
            else:
                _tprint(f"You also found: {item['name']}!")
    else:
        max_hp = player_max_hp(player) if member is player else member.get("max_hp", 50)
        damage = max(3, int(max_hp * random.uniform(0.08, 0.15)))
        if member is player:
            player["current_hp"] = max(1, player["current_hp"] - damage)
            _tprint(f"\n💥  The trap springs! You take {damage} damage.")
            _tprint(f"HP: {player['current_hp']}/{max_hp}")
        else:
            member["current_hp"] = max(1, member["current_hp"] - damage)
            _tprint(f"\n💥  The trap springs! {member['name']} takes {damage} damage.")
            _tprint(f"HP: {member['current_hp']}/{member['max_hp']}")

        if member is player and player["current_hp"] <= max_hp * 0.25:
            _tprint("⚠️  Critically wounded!")

    _tpause()
    return "continue"


def handle_stat_check_room(player, floor, event_key, combat_override=None):
    """Stat check room with narrative choice and dice roll."""
    # Look up event in both standard and Wonderland event pools
    event = STAT_CHECK_EVENTS.get(event_key) or WL_STAT_CHECK_EVENTS.get(event_key)
    if event is None:
        _tprint(f"\n  ERROR: Unknown event key '{event_key}'.")
        _tpause()
        return "continue"
    _tprint("\n" + "=" * 50)
    _tprint(f"📜  {event['name']}")
    _tprint(event["desc"])
    _tprint("=" * 50)

    dc = int(event["base_dc"] + floor * event["dc_floor_mult"])

    # Pandemonium: Mirrored Mind / Unstable Ground curses increase DC
    from pandemonium_curses import get_stat_check_dc_modifier
    dc_mod = get_stat_check_dc_modifier(player, event["stat"])
    if dc_mod > 0:
        dc += dc_mod
        _tprint(f"  ⚠️  Pandemonium's curse twists reality... DC increased by {dc_mod}!")

    # Wonderland: Caterpillar's Insight reduces DC
    from wonderland_curses import get_caterpillars_insight_reduction
    wl_reduction = get_caterpillars_insight_reduction(player)
    if wl_reduction > 0:
        dc = max(1, dc - int(wl_reduction))
        _tprint(f"  🐛 The Caterpillar's wisdom guides you... DC reduced by {int(wl_reduction)}!")

    # Wonderland Shadow: Author's Will increases DC
    from wonderland_curses import get_shadow_stat_check_dc_increase
    wl_shadow_dc = get_shadow_stat_check_dc_increase(player)
    if wl_shadow_dc > 0:
        dc += int(wl_shadow_dc)
        _tprint(f"  📖 The Author's pen scratches — DC increased by {int(wl_shadow_dc)}!")

    _tprint(f"\nRequired check: {event['stat']} (DC {dc})")

    member = _select_party_member(player, stat_name=event["stat"], dc=dc)
    if member is None:
        _tprint(f"\nYou ignore the {event['name'].lower()} and move on.")
        return "continue"

    success, roll, total, stat = _roll_stat_check(member, event["stat"], dc, player)

    name = member.get("name", "You") if member is player else member["name"]
    _tprint(f"\n{name} attempts the task...")
    _tprint(f"Roll: {roll} + {stat} ({event['stat']}) = {total} vs DC {dc}")

    if event_key == "heal_wounded":
        if success:
            gold = 15 + floor * 2
            _tprint(f"\n✅  Success! You stabilize the wounded adventurer.")
            _tprint(f"They reward you with {gold} gold and their eternal gratitude.")
            player["gold"] = player.get("gold", 0) + gold

            # Favor bonus in current city
            city_id = player.get("origin_city", "solmere")
            if "favor" not in player:
                player["favor"] = {}
            if city_id not in player["favor"]:
                player["favor"][city_id] = 0
            favor_gain = 3 + random.randint(1, 3)
            player["favor"][city_id] += favor_gain
            _tprint(f"Gained {favor_gain} favor in {city_id.title()}!")
        else:
            _tprint(f"\n❌  Failure! The wounds are too deep. The adventurer passes away.")
            city_id = player.get("origin_city", "solmere")
            if "favor" in player and city_id in player["favor"]:
                favor_loss = min(5, player["favor"][city_id])
                player["favor"][city_id] -= favor_loss
                _tprint(f"Word spreads. You lose {favor_loss} favor in {city_id.title()}.")
            _tprint("A heavy weight settles on your conscience.")

    elif event_key == "bury_corpse":
        if success:
            _tprint(f"\n✅  Success! The remains are laid to rest with proper rites.")
            _tprint("A gentle warmth fills the room — a blessing from the spirits.")
            player.setdefault("active_buffs", []).append({
                "type": "blessing", "stat": "all", "value": 2, "remaining": 2, "source": "corpse_blessing"
            })
            _tprint("Gained +2 to all stats for this floor!")
        else:
            # Damage goes to the character who attempted the check (member), not always the player
            if member is player:
                max_hp = player_max_hp(player)
                damage = max(5, int(max_hp * 0.10))
                player["current_hp"] = max(1, player["current_hp"] - damage)
                _tprint(f"\n❌  Failure! Disturbed spirits lash out!")
                _tprint(f"You take {damage} damage. HP: {player['current_hp']}/{max_hp}")
            else:
                max_hp = member.get("max_hp", member.get("current_hp", 10))
                damage = max(5, int(max_hp * 0.10))
                member["current_hp"] = max(1, member.get("current_hp", max_hp) - damage)
                _tprint(f"\n❌  Failure! Disturbed spirits lash out!")
                _tprint(f"{member['name']} takes {damage} damage. HP: {member['current_hp']}/{max_hp}")

    elif event_key == "monster_approaching":
        if success:
            xp = floor * 15
            _tprint(f"\n✅  Success! You calm the creature with soothing words.")
            _tprint(f"It leaves peacefully, and you gain {xp} XP from the experience.")
            gain_exp(player, xp)
            for ally in player.get("allies", []):
                if ally.get("current_hp", 0) > 0:
                    gain_exp_ally(ally, xp)
        else:
            _tprint(f"\n❌  Failure! The creature snarls and attacks!")
            # Spawn a single enemy of the floor's level
            # Local import to avoid circular dependency at module load
            from resources.enemies import ENEMIES
            from dungeon import get_random_enemy_key

            region = player.get("dungeon_region", "temperate")
            enemy_key = get_random_enemy_key(floor, boss=False, region=region, player=player)
            enemy_name = ENEMIES[enemy_key]["name"]
            _tprint(f"\nA {enemy_name} attacks!")
            _tpause("Press Enter to fight...")

            result = combat_override(player, [enemy_key], floor=floor) if combat_override else combat(player, [enemy_key], floor=floor)
            if result == "dead":
                return "dead"
            elif result == "fled":
                return "fled"
            elif result == "victory":
                # Award reduced XP for this forced fight
                enemy_level = ENEMIES[enemy_key]["level"]
                gain_exp(player, enemy_level * 8)
                for ally in player.get("allies", []):
                    if ally.get("current_hp", 0) > 0:
                        gain_exp_ally(ally, enemy_level * 8)
                # Chance for drop
                if random.random() < 0.40:
                    rarities = ["common", "uncommon", "rare"]
                    weights = [0.50, 0.35, 0.15]
                    rarity = random.choices(rarities, weights=weights)[0]
                    item_id = _random_item_id()
                    item = build_item(item_id, rarity)
                    if not _add_to_inv(player, item.copy()):
                        _tprint(f"\nFound: {item['name']} (but your bag is full — dropped!)")
                    else:
                        _tprint(f"\nFound: {item['name']}")
                # Small gold
                gold = enemy_level * 5 + random.randint(3, 10)
                player["gold"] = player.get("gold", 0) + gold
                _tprint(f"Found {gold} gold.")

                # Wedding end-of-combat rewards
                from combat.wedding_specials import apply_wedding_combat_end
                apply_wedding_combat_end(player, victory=True)

                _tpause()

    # ── Wonderland events ────────────────────────────────────────────
    elif event_key == "wl_tea_party":
        if success:
            gold = 15 + floor * 3
            _tprint(f"\n✅  Success! You navigate the tea party's impossible etiquette.")
            _tprint(f"'Oh, you DO know how to hold a teacup!' The Hatter beams.")
            _tprint(f"He presses {gold} gold into your hand and a spare pocket watch into your pocket.")
            player["gold"] = player.get("gold", 0) + gold

            # Tea blessing — small heal + buff
            max_hp = player_max_hp(player)
            heal = int(max_hp * 0.15)
            player["current_hp"] = min(player["current_hp"] + heal, max_hp)
            _tprint(f"The tea warms you. Healed {heal} HP.")
            player.setdefault("active_buffs", []).append({
                "type": "tea_blessing", "stat": "Charisma", "value": 2, "remaining": 2,
                "source": "hatter_tea"
            })
            _tprint("Gained +2 Charisma for 2 floors! (The tea was excellent.)")
        else:
            _tprint(f"\n❌  Failure! You use the wrong spoon. The Hatter's face darkens.")
            _tprint("'No jam for YOU today! Or ever!' Teacups fly across the table.")
            if member is player:
                max_hp = player_max_hp(player)
                damage = max(5, int(max_hp * 0.08))
                player["current_hp"] = max(1, player["current_hp"] - damage)
                _tprint(f"You take {damage} damage from flying crockery. HP: {player['current_hp']}/{max_hp}")
            else:
                max_hp = member.get("max_hp", member.get("current_hp", 10))
                damage = max(5, int(max_hp * 0.08))
                member["current_hp"] = max(1, member.get("current_hp", max_hp) - damage)
                _tprint(f"{member['name']} takes {damage} damage from flying crockery. HP: {member['current_hp']}/{max_hp}")

    elif event_key == "wl_paint_roses":
        if success:
            _tprint(f"\n✅  Success! You paint the roses flawlessly — not a single white petal remains.")
            _tprint("The card soldiers weep with relief. 'You've saved our heads! Literally!'")
            _tprint("One of them hands you a hidden cache they were guarding.")
            # Guaranteed item drop
            rarities = ["uncommon", "rare", "epic"]
            if floor <= 10:
                weights = [0.55, 0.35, 0.10]
            elif floor <= 25:
                weights = [0.35, 0.45, 0.20]
            else:
                weights = [0.20, 0.50, 0.30]
            rarity = random.choices(rarities, weights=weights)[0]
            item_id = _random_item_id()
            item = build_item(item_id, rarity)
            if not _add_to_inv(player, item.copy()):
                _tprint(f"Received: {item['name']} (but your bag is full — dropped!)")
            else:
                _tprint(f"Received: {item['name']} [{rarity}]!")
            gold = 10 + floor * 2 + random.randint(5, 15)
            player["gold"] = player.get("gold", 0) + gold
            _tprint(f"Also found {gold} gold among the paint cans.")
        else:
            _tprint(f"\n❌  Failure! Your hand slips — red paint splatters everywhere!")
            _tprint("The card soldiers shriek. 'THE QUEEN WILL KNOW! RUN!'")
            _tprint("In their panic, they bump into you and flee the chamber.")
            # Minor damage
            if member is player:
                max_hp = player_max_hp(player)
                damage = max(3, int(max_hp * 0.06))
                player["current_hp"] = max(1, player["current_hp"] - damage)
                _tprint(f"You take {damage} damage in the chaos. HP: {player['current_hp']}/{max_hp}")
            else:
                max_hp = member.get("max_hp", member.get("current_hp", 10))
                damage = max(3, int(max_hp * 0.06))
                member["current_hp"] = max(1, member.get("current_hp", max_hp) - damage)
                _tprint(f"{member['name']} takes {damage} damage in the chaos. HP: {member['current_hp']}/{max_hp}")

    elif event_key == "wl_cat_riddle":
        if success:
            xp = floor * 18
            _tprint(f"\n✅  Success! You answer the riddle correctly.")
            _tprint("The Cheshire Cat's grin widens impossibly. 'Clever thing. Most everyone's mad here... "
                     "but you're the interesting kind.'")
            _tprint(f"He applauds slowly, each clap showering you with {xp} XP worth of insight.")
            gain_exp(player, xp)
            for ally in player.get("allies", []):
                if ally.get("current_hp", 0) > 0:
                    gain_exp_ally(ally, xp)
            # Cat's gift — chance for a wonderland-themed item or blessing
            if random.random() < 0.30:
                player.setdefault("active_buffs", []).append({
                    "type": "cat_grin", "stat": "Wisdom", "value": 3, "remaining": 1,
                    "source": "cheshire_grin"
                })
                _tprint("The Cat's grin lingers. +3 Wisdom for 1 floor!")
        else:
            _tprint(f"\n❌  Failure! 'Wrong answer!' The Cat's grin turns sharp.")
            _tprint("'I suppose I'll have to play with you after all.' He fades, but not before "
                     "unleashing something from the shadows.")
            # Spawn a Wonderland enemy
            from resources.enemies import ENEMIES
            from dungeon import get_random_enemy_key

            region = "wonderland"
            enemy_key = get_random_enemy_key(floor, boss=False, region=region, player=player)
            enemy_name = ENEMIES[enemy_key]["name"]
            _tprint(f"\nA {enemy_name} materializes from the Cat's fading grin!")
            _tpause("Press Enter to fight...")

            result = combat_override(player, [enemy_key], floor=floor) if combat_override else combat(player, [enemy_key], floor=floor)
            if result == "dead":
                return "dead"
            elif result == "fled":
                return "fled"
            elif result == "victory":
                enemy_level = ENEMIES[enemy_key]["level"]
                gain_exp(player, enemy_level * 10)
                for ally in player.get("allies", []):
                    if ally.get("current_hp", 0) > 0:
                        gain_exp_ally(ally, enemy_level * 10)
                if random.random() < 0.40:
                    rarities = ["common", "uncommon", "rare"]
                    weights = [0.45, 0.35, 0.20]
                    rarity = random.choices(rarities, weights=weights)[0]
                    item_id = _random_item_id()
                    item = build_item(item_id, rarity)
                    if not _add_to_inv(player, item.copy()):
                        _tprint(f"\nFound: {item['name']} (but your bag is full — dropped!)")
                    else:
                        _tprint(f"\nFound: {item['name']}")
                gold = enemy_level * 6 + random.randint(5, 15)
                player["gold"] = player.get("gold", 0) + gold
                _tprint(f"Found {gold} gold.")

                from combat.wedding_specials import apply_wedding_combat_end
                apply_wedding_combat_end(player, victory=True)

                _tpause()

    _tpause()
    return "continue"
