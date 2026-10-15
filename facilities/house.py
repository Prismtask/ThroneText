# facilities/house.py
"""Player House system.

Data layout in player dict
──────────────────────────
player["houses"] = {
    city_id: {
        "level":           int (1–8),
        "storage":         list of item dicts,
        "last_income_day": int  (game day when income was last collected),
    }
}

House levels
────────────
  Lv1 – Hovel       : storage 10 slots,  income  8 gold/day,  rest 30 min
  Lv2 – Cottage     : storage 20 slots,  income 18 gold/day,  rest 25 min
  Lv3 – Manor       : storage 35 slots,  income 35 gold/day,  rest 20 min
  Lv4 – Villa       : storage 55 slots,  income 65 gold/day,  rest 15 min
  Lv5 – Estate      : storage 80 slots,  income 110 gold/day, rest 10 min
  Lv6 – Palace      : storage 120 slots, income 200 gold/day, rest 10 min
  Lv7 – Citadel     : storage 170 slots, income 320 gold/day, rest 5 min
  Lv8 – Sanctuary   : storage 230 slots, income 480 gold/day, rest 5 min

Upgrade costs: Lv1→2 = 600, Lv2→3 = 1500, Lv3→4 = 3000, Lv4→5 = 6000,
               Lv5→6 = 12000, Lv6→7 = 25000, Lv7→8 = 50000

Passive income now scales with your highest dungeon floor cleared across all
regions so it stays relevant in late game.
"""

from utils import advance_time, _int_to_roman, display_name, display_name_with_species
from events import format_date
from character import player_max_hp
import random
from resources.enemies import AFFECTION_GIFTS, ENEMIES
from gui.terminal import term
from facilities.dispatch import (
    board_label, adjust_stress, girl_status_line, dispatch_return_text, injured_text,
)

RECRUIT_AFFECTION_THRESHOLD = 50  # Minimum affection needed to recruit a girl

# ── Constants ────────────────────────────────────────────────────────────────

HOUSE_LEVELS = {
    1: {"name": "Hovel",     "storage_cap": 10,  "income_per_day": 8,   "rest_minutes": 30, "upgrade_cost": 600,   "bed_buff_value": 0, "bed_buff_floors": 1},
    2: {"name": "Cottage",   "storage_cap": 20,  "income_per_day": 18,  "rest_minutes": 25, "upgrade_cost": 1500,  "bed_buff_value": 0, "bed_buff_floors": 2},
    3: {"name": "Manor",     "storage_cap": 35,  "income_per_day": 35,  "rest_minutes": 20, "upgrade_cost": 3000,  "bed_buff_value": 1, "bed_buff_floors": 3},
    4: {"name": "Villa",     "storage_cap": 55,  "income_per_day": 65,  "rest_minutes": 15, "upgrade_cost": 6000,  "bed_buff_value": 1, "bed_buff_floors": 4},
    5: {"name": "Estate",    "storage_cap": 80,  "income_per_day": 110, "rest_minutes": 10, "upgrade_cost": 12000, "bed_buff_value": 2, "bed_buff_floors": 5},
    6: {"name": "Palace",    "storage_cap": 120, "income_per_day": 200, "rest_minutes": 10, "upgrade_cost": 25000, "bed_buff_value": 2, "bed_buff_floors": 6},
    7: {"name": "Citadel",   "storage_cap": 170, "income_per_day": 320, "rest_minutes": 5,  "upgrade_cost": 50000, "bed_buff_value": 2, "bed_buff_floors": 7},
    8: {"name": "Sanctuary", "storage_cap": 230, "income_per_day": 480, "rest_minutes": 5,  "upgrade_cost": None,  "bed_buff_value": 3, "bed_buff_floors": 8},
}

HOUSE_MONSTER_GIRL_LIMITS = {
    1: 2,    # Hovel
    2: 4,    # Cottage
    3: 8,    # Manor
    4: 14,   # Villa
    5: 24,   # Estate
    6: 50,   # Palace  (room for 48 current + future)
    7: 75,   # Citadel
    8: 100,  # Sanctuary
}

# Multiplier on income per day based on a city's wealth (derived from inn cost).
# Wealthier cities yield more passive income.
CITY_INCOME_MULT = {
    "solmere":     1.0,
    "greyharbor":  1.0,
    "elderfen":    0.8,
    "thornwall":   0.9,
    "stormhold":   0.9,
    "irondeep":    1.1,
    "skylume":     1.4,
    "cinderpeak":  1.2,
    "veilholt":    1.1,
    "sunreach":    1.0,
    "brinewatch":  1.2,
    "mirefall":    0.7,
    "ashkara":     1.3,
    "dunemar":     1.1,
    "saltmarsh":   0.8,
    "tidebreak":   1.5,
    "coralhaven":  1.3,
    "blackwake":   0.9,
    "isle_of_glass": 1.6,
}

MAX_INCOME_DAYS = 10  # Income caps after this many days (prevents idle exploit)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _get_house(player, city_id):
    """Return house dict for city, or None if the player has no house there."""
    return player.get("houses", {}).get(city_id)


def _house_level_data(house):
    return HOUSE_LEVELS[house["level"]]


def _get_highest_floor(player):
    """Return the highest dungeon floor ever cleared across all cities."""
    highest = player.get("max_floor", 1)
    for cf in player.get("city_floors", {}).values():
        highest = max(highest, cf.get("max_floor", 1))
    return highest


def _pending_income(player, city_id, house):
    """Calculate gold owed since last collection, capped at MAX_INCOME_DAYS."""
    current_day = player.get("day", 1)
    last_day    = house.get("last_income_day", current_day)
    days_passed = min(current_day - last_day, MAX_INCOME_DAYS)
    if days_passed <= 0:
        return 0
    base      = _house_level_data(house)["income_per_day"]
    mult      = CITY_INCOME_MULT.get(city_id, 1.0)
    highest_floor = _get_highest_floor(player)
    floor_mult = max(1.0, highest_floor / 3.0)
    return int(days_passed * base * mult * floor_mult)


def _reset_daily_limits(player):
    """Reset daily talk/gift counters if the day has changed."""
    today = player.get("day", 1)
    last_day = player.get("girl_daily_last_day", 0)
    if today != last_day:
        player["girl_talk_today"] = {}
        player["girl_gift_today"] = {}
        player["girl_daily_last_day"] = today


def _talks_remaining(player, girl_key):
    """Return how many talks remain for this girl today (always 3 per day)."""
    _reset_daily_limits(player)
    talks_done = player.get("girl_talk_today", {}).get(girl_key, 0)
    daily_limit = 3
    return max(0, daily_limit - talks_done)


def _gifts_remaining(player, girl_key):
    """Return whether this girl can receive a gift today (1 per day)."""
    _reset_daily_limits(player)
    return not player.get("girl_gift_today", {}).get(girl_key, False)


ENGAGEMENT_RING_IDS = {
    "ruby_engagement_ring", "sapphire_engagement_ring", "emerald_engagement_ring",
    "topaz_engagement_ring", "amethyst_engagement_ring", "diamond_engagement_ring",
}


def _has_engagement_ring(player):
    """Return True if the player has any engagement ring in their inventory."""
    return bool(_get_engagement_rings(player))


def _get_engagement_rings(player):
    """Return every engagement ring in the player's inventory (bag order)."""
    return [item for item in player.get("inventory", [])
            if item.get("id") in ENGAGEMENT_RING_IDS]


def _apply_ring_bonus_to_girl(girl, ring):
    """Transfer an engagement ring's stat bonus onto a girl, permanently.

    Stored as ``girl["ring_stat_bonus"]`` (lounge display + save), and — when
    the girl already has stored attributes — added directly to them so the
    bonus applies immediately everywhere (combat, level-ups, dispatch).
    Girls without stored attributes receive the bonus dynamically via
    ``compute_girl_attributes()`` once their stats are first computed.
    """
    ring_bonus = dict(ring.get("mods") or ring.get("base_mods") or {})
    if not ring_bonus:
        return {}
    girl["ring_stat_bonus"] = ring_bonus
    stored = girl.get("attributes")
    if stored:
        for stat, val in ring_bonus.items():
            if stat in stored:
                stored[stat] = stored[stat] + val
    return ring_bonus


def _girl_unique_id(girl):
    """Return a stable unique identifier for a girl (key + name)."""
    return f"{girl.get('key', '')}:{girl.get('name', '')}"


def get_current_house_allies(player):
    """Return list of all monster girl allies currently in the active party."""
    return player.get("allies", [])


def _resolve_house(player, city_id=None):
    """Return (city_id, house) for the player's home house.

    Resolution order: the explicitly requested city if the player owns a
    house there → the origin city's house if owned → the first owned house.

    ``player["origin_city"]`` is repointed by travel and dungeons (nearest
    city context), so it must never be trusted as "the home city" on its own:
    reads and writes resolve identically here, which keeps a
    get_house_data() → save_house_data() cycle from ever targeting a
    different house than the one it read (that mismatch wiped savegame_1).
    """
    houses = player.get("houses") or {}
    if not houses:
        return city_id, None
    if city_id and city_id in houses:
        return city_id, houses[city_id]
    origin = player.get("origin_city")
    if origin and origin in houses:
        return origin, houses[origin]
    first_city = next(iter(houses))
    return first_city, houses[first_city]


def get_house_data(player, city_id=None):
    """Return the live monster_girls list for the player's house."""
    _, house = _resolve_house(player, city_id)
    if house is None:
        return []
    # Live list: callers mutate the house record in place, and a later
    # save_house_data(player, girls) writes back to this same house.
    return house.setdefault("monster_girls", [])


def save_house_data(player, girls_data, city_id=None):
    """Persist the house's monster_girls list.

    The target house is resolved exactly like in get_house_data(), so a list
    read from get_house_data() always round-trips to the same house no matter
    where the volatile origin_city currently points. This function never
    redirects girls to a different house than the one they were read from.

    A new Hovel is only auto-created when the player owns no house at all
    (fallback for early captures before buying a deed).
    """
    if not player.get("houses"):
        player["houses"] = {}
    houses = player["houses"]

    city_id, house = _resolve_house(player, city_id)
    if house is None:
        # No house at all: auto-create a basic Hovel so the player isn't
        # locked out of the monster-girl system.
        city_id = city_id or player.get("origin_city", "solmere")
        house = {"level": 1, "storage": [], "last_income_day": player.get("day", 1)}
        houses[city_id] = house

    # Callers normally pass the live list returned by get_house_data(); only
    # replace the stored list when a genuinely different list is supplied.
    if girls_data is not house.get("monster_girls"):
        house["monster_girls"] = girls_data


# ── Sub-menus ────────────────────────────────────────────────────────────────

def _house_rest(player, city_id, house):
    """Quick rest at home — free full heal, costs a small amount of time."""
    lvl_data   = _house_level_data(house)
    rest_mins  = lvl_data["rest_minutes"]
    max_hp     = player_max_hp(player)

    # Heal player
    old_hp               = player["current_hp"]
    player["current_hp"] = max_hp
    healed               = max_hp - old_hp

    # Heal allies too (including defeated allies — recovery)
    for ally in player.get("allies", []):
        if ally.get("defeated"):
            ally["defeated"] = False
            ally["current_hp"] = ally["max_hp"]
            # Print is_recovered dialogue
            from resources.enemies import ENEMIES
            template = ENEMIES.get(ally.get("key", ""), {})
            dialogue = template.get("dialogue", {})
            recovered_line = dialogue.get("is_recovered", f"{display_name(ally)} is back on their feet!")
            if "{name}" in recovered_line:
                recovered_line = recovered_line.format(name=display_name(ally))
            term.print(f"  {recovered_line}")
        elif ally.get("current_hp", 0) > 0:
            ally_old = ally["current_hp"]
            ally["current_hp"] = ally["max_hp"]
            ally_healed = ally["max_hp"] - ally_old
            term.print(f"  {display_name(ally)} healed {ally_healed} HP → {ally['max_hp']}/{ally['max_hp']}")

    advance_time(player, rest_mins)

    home_name = lvl_data["name"].lower()
    term.print(f"You take a quick rest in your {home_name}.")
    if healed > 0:
        term.print(f"  Healed {healed} HP → {max_hp}/{max_hp}")
    else:
        term.print(f"  You were already at full health, but the brief rest feels nice.")
    term.print(f"  ({rest_mins} minutes pass.)")
    term.pause()


def _house_sleep(player, city_id, house):
    """Sleep at home — full heal; usable only at Night (sleep starts a new day).
    From Manor onward, also grants a Well-Rested stat buff that lasts for dungeon rooms.
    Stat bonus: +1 (Manor–Villa), +2 (Estate–Citadel), +3 (Sanctuary)."""
    import time_blocks
    if time_blocks.get_day_phase(player) != "night":
        term.print("You can only sleep at home during the night.")
        term.pause()
        return

    lvl_data   = _house_level_data(house)
    buff_val   = lvl_data["bed_buff_value"]
    buff_rooms = lvl_data["bed_buff_floors"]
    max_hp     = player_max_hp(player)

    # Heal player
    old_hp               = player["current_hp"]
    player["current_hp"] = max_hp
    healed               = max_hp - old_hp

    # Heal allies too (including defeated allies — recovery)
    for ally in player.get("allies", []):
        if ally.get("defeated"):
            ally["defeated"] = False
            ally["current_hp"] = ally["max_hp"]
            # Print is_recovered dialogue
            from resources.enemies import ENEMIES
            template = ENEMIES.get(ally.get("key", ""), {})
            dialogue = template.get("dialogue", {})
            recovered_line = dialogue.get("is_recovered", f"{display_name(ally)} is back on their feet!")
            if "{name}" in recovered_line:
                recovered_line = recovered_line.format(name=display_name(ally))
            term.print(f"  {recovered_line}")
        elif ally.get("current_hp", 0) > 0:
            ally_old = ally["current_hp"]
            ally["current_hp"] = ally["max_hp"]
            ally_healed = ally["max_hp"] - ally_old
            term.print(f"  {display_name(ally)} healed {ally_healed} HP → {ally['max_hp']}/{ally['max_hp']}")

    # Apply / refresh Well-Rested buff (Manor and above)
    if buff_val > 0:
        player.setdefault("active_buffs", [])
        player["active_buffs"] = [b for b in player["active_buffs"] if b.get("type") != "well_rested"]
        player["active_buffs"].append({
            "type":      "well_rested",
            "stat":      "all",
            "value":     buff_val,
            "remaining": buff_rooms,
        })

        for ally in player.get("allies", []):
            if ally.get("current_hp", 0) > 0:
                ally.setdefault("active_buffs", [])
                ally["active_buffs"] = [b for b in ally["active_buffs"] if b.get("type") != "well_rested"]
                ally["active_buffs"].append({
                    "type":      "well_rested",
                    "stat":      "all",
                    "value":     buff_val,
                    "remaining": buff_rooms,
                })

    time_blocks.end_day(player, slept=True)

    home_name = lvl_data["name"].lower()
    term.print(f"You settle into a deep sleep in your {home_name}.")
    if healed > 0:
        term.print(f"  Healed {healed} HP → {max_hp}/{max_hp}")
    else:
        term.print(f"  You were already at full health, but the sleep restores your spirit.")
    if buff_val > 0:
        term.print(f"  Well-Rested: +{buff_val} to all stats for {buff_rooms} dungeon room(s).")
    term.print("  (8 hours pass.)")
    term.pause()


from inventory import get_inventory_caps, count_inventory, get_sorted_equipment, get_sorted_items, remove_item_by_reference, consume_stackable_items

def _house_storage(player, city_id, house):
    """Move items between inventory and house storage chest."""
    lvl_data = _house_level_data(house)
    cap      = lvl_data["storage_cap"]
    storage  = house["storage"]

    while True:
        term.clear()
        inv     = player.get("inventory", [])
        equip_cap, other_cap = get_inventory_caps(player)
        equip_count, other_count = count_inventory(player)
        term.print(f"=== House Storage ({len(storage)}/{cap} slots used) ===")
        term.print(f"Your Bag: {equip_count}/{equip_cap} equipment | {other_count}/{other_cap} items")

        term.print("\n-- Chest --")
        if storage:
            for i, itm in enumerate(storage):
                term.print(f"  {i+1}. {itm['name']} ({itm['type']})")
        else:
            term.print("  (empty)")

        term.print("\n-- Your Bag --")
        if inv:
            sorted_equip = get_sorted_equipment(player)
            sorted_items = get_sorted_items(player)
            all_sorted = sorted_equip + sorted_items
            for i, itm in enumerate(all_sorted):
                if itm.get("type") == "equipment":
                    tag = f"[{itm.get('rarity','common')}]"
                    term.print(f"  {i+1}. {itm['name']} ({itm['slot']}) {tag}")
                else:
                    term.print(f"  {i+1}. {itm['name']} ({itm['type']})")
        else:
            term.print("  (empty)")

        act_idx = term.menu(["Deposit to chest", "Withdraw from chest", "Back"], prompt="Storage action:")
        if act_idx == 0:
            act = "d"
        elif act_idx == 1:
            act = "w"
        else:
            act = "b"

        if act == "d":
            if not inv:
                term.print("Your bag is empty.")
                term.pause()
                continue
            if len(storage) >= cap:
                term.print(f"Chest is full ({cap} slots).")
                term.pause()
                continue
            term.print("\nEnter numbers to deposit (e.g. '1 3 5', '1-4', or 'all'). 0 to cancel.")
            raw = term.input("Deposit which items? ").strip().lower()
            if raw in ("", "0", "cancel"):
                term.print("Cancelled.")
                term.pause()
                continue

            sorted_equip = get_sorted_equipment(player)
            sorted_items = get_sorted_items(player)
            all_sorted = sorted_equip + sorted_items
            indices = set()
            if raw == "all":
                indices = set(range(len(all_sorted)))
            else:
                for part in raw.split():
                    if "-" in part:
                        try:
                            a, b = part.split("-", 1)
                            indices.update(range(int(a) - 1, int(b)))
                        except ValueError:
                            pass
                    else:
                        try:
                            indices.add(int(part) - 1)
                        except ValueError:
                            pass

            indices = sorted([i for i in indices if 0 <= i < len(all_sorted)], reverse=True)
            if not indices:
                term.print("No valid items selected.")
                term.pause()
                continue

            # Check capacity before depositing
            from combat.weapon.wedding_specials import is_wedding_item_soulbound
            filtered_indices = []
            for i in indices:
                item = all_sorted[i]
                if is_wedding_item_soulbound(item):
                    term.print(f"  {item['name']} is soulbound — it cannot leave your side.")
                else:
                    filtered_indices.append(i)
            
            if not filtered_indices:
                term.print("No valid items to deposit (all selected items are soulbound).")
                term.pause()
                continue

            deposit_count = len(filtered_indices)
            if len(storage) + deposit_count > cap:
                term.print(f"Not enough chest space. Can only store {cap - len(storage)} more items.")
                term.pause()
                continue

            for i in filtered_indices:
                item = all_sorted[i]
                orig_idx = next(idx for idx, itm in enumerate(player["inventory"]) if itm is item)
                player["inventory"].pop(orig_idx)
                storage.append(item)
            term.print(f"Stored {deposit_count} item(s) in your chest.")
            term.pause()

        elif act == "w":
            if not storage:
                term.print("The chest is empty.")
                term.pause()
                continue
            term.print("\nEnter numbers to withdraw (e.g. '1 3 5', '1-4', or 'all'). 0 to cancel.")
            raw = term.input("Withdraw which items? ").strip().lower()
            if raw in ("", "0", "cancel"):
                term.print("Cancelled.")
                term.pause()
                continue

            indices = set()
            if raw == "all":
                indices = set(range(len(storage)))
            else:
                for part in raw.split():
                    if "-" in part:
                        try:
                            a, b = part.split("-", 1)
                            indices.update(range(int(a) - 1, int(b)))
                        except ValueError:
                            pass
                    else:
                        try:
                            indices.add(int(part) - 1)
                        except ValueError:
                            pass

            indices = sorted([i for i in indices if 0 <= i < len(storage)], reverse=True)
            if not indices:
                term.print("No valid items selected.")
                term.pause()
                continue

            # Check bag capacity before withdrawing
            withdraw_equip = sum(1 for i in indices if storage[i].get("type") == "equipment")
            withdraw_other = len(indices) - withdraw_equip
            equip_cap, other_cap = get_inventory_caps(player)
            equip_count, other_count = count_inventory(player)
            if equip_count + withdraw_equip > equip_cap:
                term.print(f"Not enough equipment bag space. Can hold {equip_cap - equip_count} more equipment.")
                term.pause()
                continue
            if other_count + withdraw_other > other_cap:
                term.print(f"Not enough item bag space. Can hold {other_cap - other_count} more items.")
                term.pause()
                continue

            for i in indices:
                item = storage.pop(i)
                player.setdefault("inventory", []).append(item)
            term.print(f"Took {len(indices)} item(s) from the chest.")
            term.pause()

        elif act == "b":
            break


def _house_collect_income(player, city_id, house):
    """Collect accumulated passive income."""
    gold = _pending_income(player, city_id, house)
    if gold <= 0:
        term.print("No income has accumulated yet. Come back tomorrow.")
    else:
        player["gold"]              = player.get("gold", 0) + gold
        house["last_income_day"]    = player.get("day", 1)
        term.print(f"You collect {gold} gold from your {_house_level_data(house)['name'].lower()}'s rental income.")
        term.print(f"  Gold: {player['gold']}")
    term.pause()


def _house_upgrade(player, city_id, house):
    """Upgrade the house to the next level."""
    lvl      = house["level"]
    lvl_data = HOUSE_LEVELS[lvl]
    cost     = lvl_data["upgrade_cost"]
    max_level = max(HOUSE_LEVELS)

    if cost is None or lvl >= max_level:
        term.print(f"Your {_house_level_data(house)['name']} is already at its grandest — no further upgrades available.")
        term.pause()
        return

    next_data = HOUSE_LEVELS[lvl + 1]
    from facilities.house import HOUSE_MONSTER_GIRL_LIMITS
    term.print(f"Upgrade to {next_data['name']}?")
    term.print(f"  Cost           : {cost} gold")
    term.print(f"  Storage        : {lvl_data['storage_cap']} → {next_data['storage_cap']} slots")
    term.print(f"  Daily income   : {lvl_data['income_per_day']} → {next_data['income_per_day']} gold")
    term.print(f"  Rest time      : {lvl_data['rest_minutes']} → {next_data['rest_minutes']} min")
    term.print(f"  Monster girls  : {HOUSE_MONSTER_GIRL_LIMITS[lvl]} → {HOUSE_MONSTER_GIRL_LIMITS[lvl + 1]}")
    if not term.confirm("Proceed with upgrade?"):
        term.print("Upgrade cancelled.")
        term.pause()
        return

    if player.get("gold", 0) < cost:
        term.print(f"Insufficient gold. You need {cost} gold.")
        term.pause()
        return

    player["gold"] -= cost
    house["level"]  = lvl + 1
    term.print(f"Your home has been expanded into a fine {next_data['name']}!")
    term.print(f"  Remaining gold: {player['gold']}")
    term.pause()


def _get_ascension_requirements(current_cap):
    """
    Returns a list of (tier, count) tuples for ascending from current_cap.
    Formula: to ascend from cap C, need (C/10 - t + 1) stones of tier t
    for t = 1 .. C/10.
    Example: C=20 → [(1, 2), (2, 1)]  → 2 Stone I + 1 Stone II
             C=30 → [(1, 3), (2, 2), (3, 1)]
    """
    max_tier = current_cap // 10
    requirements = []
    for tier in range(1, max_tier + 1):
        count = max_tier - tier + 1
        requirements.append((tier, count))
    return requirements


def _can_ascend_ally(player, ally):
    """Check if ally is at their level cap and player has ALL required stones."""
    current_cap = ally.get("level_cap", 10)
    if ally["level"] < current_cap:
        return False
    requirements = _get_ascension_requirements(current_cap)
    # Count available stones per tier in inventory (stack-aware)
    available = {}
    for item in player.get("inventory", []):
        tier = item.get("ascension_tier")
        if tier:
            available[tier] = available.get(tier, 0) + item.get("count", 1)
    # Check all requirements
    for tier, count in requirements:
        if available.get(tier, 0) < count:
            return False
    return True


# ── Awakening (docs/awakening_design.md Part C) ─────────────────────────────
AWAKEN_LEVEL_REQ = 40
AWAKEN_CAP_REQ = 40
AWAKEN_AFFECTION_REQ = 150


def can_awaken_girl(girl):
    """Return (eligible, reason) for the House Lounge Awaken action.

    Covers the girl-side gates only (candidate, level, cap, affection, not yet
    awakened); the Sigil cost is checked when the action is taken.
    """
    from combat.ally_skills import has_awakening
    if girl.get("awakened"):
        return False, "already awakened"
    if not has_awakening(girl.get("key", "")):
        return False, "no awakening available"
    if girl.get("level", 1) < AWAKEN_LEVEL_REQ:
        return False, f"needs Lv {AWAKEN_LEVEL_REQ}"
    if girl.get("level_cap", 10) < AWAKEN_CAP_REQ:
        return False, f"needs level cap {AWAKEN_CAP_REQ}"
    if girl.get("affection", 0) < AWAKEN_AFFECTION_REQ:
        return False, f"needs affection {AWAKEN_AFFECTION_REQ}"
    return True, "ready"


def _fmt_dialogue(line, **tokens):
    """Replace {token} placeholders without str.format (dialogue-safe)."""
    for key, val in tokens.items():
        line = line.replace("{" + key + "}", str(val))
    return line


def _sort_girls(all_girls, sort_by, sort_dir):
    """Sort the combined girls list by the given criteria.

    Args:
        all_girls: list of (where, girl_dict) tuples
        sort_by: "capture_order", "level", or "affection"
        sort_dir: "asc" (top→bottom) or "desc" (bottom→top)

    Returns:
        Sorted list of (where, girl_dict) tuples
    """
    reverse = (sort_dir == "desc")

    if sort_by == "level":
        return sorted(all_girls, key=lambda x: x[1].get("level", 1), reverse=reverse)
    elif sort_by == "affection":
        return sorted(all_girls, key=lambda x: x[1].get("affection", 30), reverse=reverse)
    else:  # capture_order (default)
        # Sort by captured_on day (lower = caught earlier).
        # Active allies and girls without captured_on get a high sentinel value.
        def _cap_key(item):
            g = item[1]
            return g.get("captured_on", 9999)
        return sorted(all_girls, key=_cap_key, reverse=reverse)


def _house_lounge(player, city_id, house):
    # ── Filter / sort state (persists across re-displays) ──────────────────
    sort_by = "capture_order"   # "capture_order" | "level" | "affection"
    sort_dir = "asc"            # "asc" (top→bottom) | "desc" (bottom→top)

    SORT_LABELS = {
        "capture_order": "Capture Order",
        "level":         "Level",
        "affection":     "Affection",
    }
    DIR_LABEL = {"asc": "Top→Bottom", "desc": "Bottom→Top"}

    # ── Outer loop: re-display after filter changes ─────────────────────────
    while True:
        term.clear()
        lvl_data = _house_level_data(house)
        girls = house.get("monster_girls", [])
        max_girls = HOUSE_MONSTER_GIRL_LIMITS.get(house["level"], 2)
        allies = player.get("allies", [])
        total_girls = len(girls) + len(allies)

        term.print(f"=== {lvl_data['name'].upper()} LOUNGE ===")
        term.print(f"Monster Girls: {total_girls}/{max_girls}")
        if allies:
            from resources.quests import format_resonance_status
            tier = (player.get("quests") or {}).get("resonance_tier", 0)
            term.print(f"Active Party: {len(allies)} allies")
            term.print(format_resonance_status(tier))
        sigil_count = player.get("awakening_sigils", 0)
        shard_count = player.get("awakening_shards", 0)
        if sigil_count or shard_count:
            term.print(f"Awakening Sigils: {sigil_count}   ·   Sigil Shards: {shard_count}")

        # ── Filter / sort info bar ──────────────────────────────────────────
        term.print(f"Sort: [{SORT_LABELS[sort_by]}]  |  View: [{DIR_LABEL[sort_dir]}]")
        term.print()

        # Build combined list
        all_girls = []
        for girl in girls:
            all_girls.append(("lounge", girl))
        for ally in allies:
            all_girls.append(("active", ally))

        if not all_girls:
            term.print("The lounge is quiet... no companions yet.")
            term.pause()
            return

        # ── Apply sort ──────────────────────────────────────────────────────
        all_girls = _sort_girls(all_girls, sort_by, sort_dir)

        # ── Display girl list ───────────────────────────────────────────────
        for i, (where, g) in enumerate(all_girls):
            aff = g.get("affection", 30)
            aff_cap = g.get("affection_cap", 100)
            status = "💍" if g.get("married") else "💎" if g.get("engaged") else "💖" if aff >= 80 else "❤️" if aff >= 50 else "😐"
            ready = " ✓" if aff >= RECRUIT_AFFECTION_THRESHOLD else ""
            active_tag = " [ACTIVE]" if where == "active" else ""
            cap_tag = " [CAP]" if where == "active" and g["level"] >= g.get("level_cap", 10) else ""
            aff_str = f"{aff}/{aff_cap}"
            disp_full = display_name_with_species(g)
            if where == "active":
                if g.get("defeated") or g.get("current_hp", 0) <= 0:
                    hp_str = "[INCAPACITATED]"
                else:
                    hp_str = f"HP: {g['current_hp']}/{g['max_hp']}"
                term.print(f"  {i+1}. {disp_full} (Lv {g['level']}{cap_tag}){active_tag} — {hp_str} — {status} Affection: {aff_str}{ready}")
            else:
                duty_tag = ""
                if g.get("dispatch_mission"):
                    duty_tag = " [AWAY]"
                elif int(g.get("injured_until", 0) or 0) > player.get("day", 1):
                    duty_tag = " [INJURED]"
                term.print(f"  {i+1}. {disp_full} (Lv {g['level']}){active_tag}{duty_tag} — {status} Affection: {aff_str}{ready}")

        # ── Build menu: girl options + filter controls + back ───────────────
        girl_options = []
        girl_styles = []
        for where, g in all_girls:
            aff = g.get("affection", 30)
            active_tag = " [ACTIVE]" if where == "active" else ""
            girl_options.append(f"{display_name_with_species(g)} (Lv {g['level']}){active_tag} — \u2665{aff}")
            girl_styles.append(None)  # default style

        # Pad to next full row so filters start on their own row (4-column grid)
        num_girls = len(all_girls)
        pad_count = (4 - (num_girls % 4)) % 4
        for _ in range(pad_count):
            girl_options.append("")
            girl_styles.append({"bg": "#1a1a2e", "fg": "#1a1a2e", "active_bg": "#1a1a2e", "active_fg": "#1a1a2e"})

        # Filter style: warm amber/gold to stand out from blue girl buttons
        FILTER_STYLE = {"bg": "#5a4a1a", "fg": "#f0d060", "active_bg": "#7a6a2a", "active_fg": "#ffe080"}

        # Append filter/sort toggles with distinct styling
        girl_options.append("\u2014 Sort by Capture Order \u2014")
        girl_styles.append(FILTER_STYLE)
        girl_options.append("\u2014 Sort by Level \u2014")
        girl_styles.append(FILTER_STYLE)
        girl_options.append("\u2014 Sort by Affection \u2014")
        girl_styles.append(FILTER_STYLE)
        girl_options.append(f"\u2014 Toggle View: {'Bottom\u2192Top' if sort_dir == 'asc' else 'Top\u2192Bottom'} \u2014")
        girl_styles.append(FILTER_STYLE)

        idx = term.menu(girl_options, prompt="Select companion or change sort:", allow_cancel=True, cancel_label="Back", styles=girl_styles)
        if idx < 0:
            return  # Back to house menu

        # ── Check if user picked a filter option ────────────────────────────
        filter_start = num_girls + pad_count
        if idx == filter_start:
            sort_by = "capture_order"
            continue  # re-display
        elif idx == filter_start + 1:
            sort_by = "level"
            continue  # re-display
        elif idx == filter_start + 2:
            sort_by = "affection"
            continue  # re-display
        elif idx == filter_start + 3:
            sort_dir = "desc" if sort_dir == "asc" else "asc"
            continue  # re-display

        # ── Handle clicks on invisible spacer buttons ───────────────────────
        if idx >= num_girls:
            continue  # clicked a spacer, re-display

        where, girl = all_girls[idx]
        girl_key = girl.get("key", "")
        template = ENEMIES.get(girl_key, {})
        dialogue = template.get("dialogue", {})
        aff = girl.get("affection", 30)

        # ── Sub-menu for this girl ──────────────────────────────────────────
        while True:
            term.clear()
            disp = display_name(girl)
            engaged = girl.get("engaged", False)
            married = girl.get("married", False)
            # Stale-cap heal: engaged/married girls belong at cap 200. An old
            # bug could reset the cap to 100, letting a single talk trigger
            # the wedding at 100 affection instead of the intended 200.
            if (engaged or married) and girl.get("affection_cap", 100) < 200:
                girl["affection_cap"] = 200
            aff_cap = girl.get("affection_cap", 100)
            term.print(f"=== {disp} ===")
            if girl.get("nickname"):
                term.print(f"  Species: {girl['name']}")
            term.print(f"  Affection: {aff}/{aff_cap}")
            status_label = "Married" if married else "Engaged" if engaged else "Active" if where == "active" else "At home"
            term.print(f"  Status: {status_label}")
            term.print(f"  {girl_status_line(girl, player.get('day', 1))}")
            away_line = dispatch_return_text(player, girl)
            if away_line:
                term.print(f"  {away_line}")
            hurt_line = injured_text(girl, player.get("day", 1))
            if hurt_line:
                term.print(f"  {hurt_line}")
            ring_bonus = girl.get("ring_stat_bonus")
            if ring_bonus:
                bonus_lines = [f"{stat} +{val}" for stat, val in ring_bonus.items()]
                term.print(f"  Ring Blessing: {', '.join(bonus_lines)}")
            from combat.ally import get_growth_label
            growth_label = get_growth_label(girl)
            if growth_label != "—":
                term.print(f"  Growth: {growth_label} (late bloomer)")
            if girl.get("awakened"):
                term.print("  ✦ Awakened — her innate skills are empowered.")
            if where == "active":
                cap = girl.get("level_cap", 10)
                term.print(f"  Level: {girl['level']}/{cap}")
            term.print()

            talks_left = _talks_remaining(player, _girl_unique_id(girl))
            gift_ready = _gifts_remaining(player, _girl_unique_id(girl))
            can_propose = (aff >= 100 and not engaged and not married and _has_engagement_ring(player))

            can_ascend = where == "active" and _can_ascend_ally(player, girl)
            at_cap = where == "active" and girl["level"] >= girl.get("level_cap", 10)
            can_awaken, _awaken_reason = can_awaken_girl(girl)

            # Build dynamic menu options
            menu_options = []
            menu_actions = []

            menu_options.append(f"Talk  ({talks_left} left today)")
            menu_actions.append("talk")

            menu_options.append(f"Give a gift  ({'ready' if gift_ready else 'already gifted today'})")
            menu_actions.append("gift")

            bath_item = next((it for it in player.get("inventory", [])
                              if it.get("id") == "herbal_bath_salts"), None)
            if bath_item and not girl.get("dispatch_mission") and int(girl.get("stress", 0)) > 0:
                menu_options.append(f"Draw a warm bath (Herbal Bath Salts ×{bath_item.get('count', 1)}, −20 stress)")
                menu_actions.append("bath")

            if aff >= 60:
                menu_options.append("Ask for blessing")
                menu_actions.append("blessing")

            if aff >= 80:
                menu_options.append("Share a kiss")
                menu_actions.append("kiss")

            if can_propose:
                menu_options.append("Propose marriage")
                menu_actions.append("propose")

            menu_options.append("Rename" if girl.get("nickname") else "Give a name")
            menu_actions.append("rename")

            if can_ascend:
                menu_options.append("Ascend (break level limit)")
                menu_actions.append("ascend")
            elif at_cap:
                requirements = _get_ascension_requirements(girl.get("level_cap", 10))
                needs = ", ".join(f"{count} Stone {_int_to_roman(tier)}" for tier, count in requirements)
                term.print(f"  [Ascend: needs {needs}]")

            if can_awaken:
                sigil_now = player.get("awakening_sigils", 0)
                menu_options.append(f"Awaken (1 Awakening Sigil) [{'ready' if sigil_now else 'no Sigil'}]")
                menu_actions.append("awaken")

            if where == "lounge":
                menu_options.append("Recruit to party")
                menu_actions.append("recruit")

            if where == "active":
                menu_options.append("Remove from party")
                menu_actions.append("dismiss")

            menu_options.append("Back")
            menu_actions.append("back")

            choice_idx = term.menu(menu_options, prompt=f"What to do with {disp}?")
            if choice_idx < 0:
                break
            action = menu_actions[choice_idx] if choice_idx < len(menu_actions) else "back"

            if action == "back":
                break

            elif action == "rename":
                # ── RENAME ──
                current_nick = girl.get("nickname", "")
                if current_nick:
                    prompt = (f"Current name: {current_nick} (originally {girl['name']})\n"
                              "Enter a new name, or leave blank to restore her original name:")
                else:
                    prompt = f"Enter a name for {girl['name']} (leave blank to cancel):"
                new_name = term.input(prompt).strip()
                # Single line only, and short enough for the combat HUD (12 chars shown).
                new_name = " ".join(new_name.split())[:16]
                if new_name:
                    girl["nickname"] = new_name
                    term.print(f"\n{girl['name']} will now answer to \"{new_name}\".")
                elif current_nick:
                    girl["nickname"] = ""
                    term.print(f"\nShe's back to being called {girl['name']}.")
                else:
                    term.print("\n(No change.)")
                term.pause()

            elif action == "talk":
                if talks_left <= 0:
                    term.print(f"\n{disp} seems tired of talking. Come back tomorrow.")
                    term.pause()
                    continue

                # Wedding gift check (200 affection, earned after engagement)
                if engaged and not married and aff >= 200:
                    special_line = dialogue.get("house_special_gift",
                        f"{disp} pulls out a beautifully wrapped box. 'This is for you, my love.'")
                    term.print("\n" + (special_line.format(name=disp) if "{name}" in special_line else special_line))
                    # Give wedding accessory
                    wedding_id = f"wedding_{girl_key}"
                    from resources.items import build_item, ITEMS
                    if wedding_id in ITEMS:
                        wedding_item = build_item(wedding_id, "unique")
                        from inventory import add_item_to_inventory
                        if add_item_to_inventory(player, wedding_item):
                            term.print(f"\n  *** You received: {wedding_item['name']} ***")
                        else:
                            term.print(f"\n  Your inventory is full! The {wedding_item['name']} was left on the table.")
                    else:
                        term.print(f"\n  (Wedding item '{wedding_id}' not found — this is a bug.)")
                    girl["married"] = True
                    player.setdefault("married_girls", [])
                    if girl_key not in player["married_girls"]:
                        player["married_girls"].append(girl_key)
                    # Remove from engaged list
                    player.setdefault("engaged_girls", [])
                    if girl_key in player["engaged_girls"]:
                        player["engaged_girls"].remove(girl_key)
                    term.print(f"\n  *** {disp} is now your wife! ***")
                    term.pause()
                    continue

                # Determine dialogue key
                if engaged and not married:
                    # Alternate between engaged_1 and engaged_2
                    if player.get("day", 1) % 2 == 0:
                        dialog_key = "house_talk_engaged_2"
                        default = f"{disp} leans against you, smiling. 'Every day with you feels like a dream. I can't wait for our wedding.'"
                    else:
                        dialog_key = "house_talk_engaged_1"
                        default = f"{disp} beams at you, her engagement ring catching the light. 'Can you believe it? We're going to be together forever!'"
                    line = dialogue.get(dialog_key, default)
                else:
                    if aff <= 30:
                        aff_tier = "low"
                    elif aff <= 60:
                        aff_tier = "mid"
                    elif aff <= 80:
                        aff_tier = "high"
                    else:
                        aff_tier = "max"
                    if girl.get("awakened"):
                        # Awakened girls have their own daily-talk set
                        dialog_key = f"awakened_talk_{aff_tier}"
                        line = dialogue.get(dialog_key,
                            dialogue.get(f"house_talk_{aff_tier}", f"{disp} looks at you expectantly."))
                    else:
                        dialog_key = f"house_talk_{aff_tier}"
                        line = dialogue.get(dialog_key, f"{disp} looks at you expectantly.")

                line = line.format(name=disp) if "{name}" in line else line
                term.print("\n" + line)

                # Increase affection
                gain = random.randint(3, 7)
                girl["affection"] = min(aff_cap, aff + gain)
                aff = girl["affection"]
                term.print(f"\nAffection +{gain} (now {aff}/{aff_cap})")

                # Track daily talk
                _reset_daily_limits(player)
                uid = _girl_unique_id(girl)
                player["girl_talk_today"][uid] = player["girl_talk_today"].get(uid, 0) + 1
                stress_now = adjust_stress(girl, -3)
                term.print(f"  The talk eases her mind — Stress −3 (now {stress_now}).")
                term.pause()

            elif action == "gift":
                if not gift_ready:
                    term.print(f"\n{disp} has already received a gift today.")
                    term.pause()
                    continue

                gifts = [it for it in player.get("inventory", []) if it.get("type") == "gift"]
                if not gifts:
                    term.print("You have no gifts.")
                    term.pause()
                    continue

                gift_names = [g['name'] for g in gifts]
                gift_names.append("Back")
                gidx = term.menu(gift_names, prompt="Choose gift:")
                if gidx < 0 or gidx >= len(gifts):
                    # Back or cancelled
                    continue
                gift = gifts[gidx]
                # Remove from inventory
                gift_type = gift.get("gift_type", "unknown")
                reaction = get_gift_reaction(girl_key, gift_type)
                remove_item_by_reference(player, gift)

                # Show love/hate dialogue
                if reaction > 0:
                    love_line = dialogue.get("house_gift_love", f"{disp} beams with joy!")
                    term.print(love_line.format(name=disp) if "{name}" in love_line else love_line)
                elif reaction < 0:
                    hate_line = dialogue.get("house_gift_hate", f"{disp} sighs, disappointed.")
                    term.print(hate_line.format(name=disp) if "{name}" in hate_line else hate_line)
                else:
                    term.print(f"{disp} shrugs indifferently.")

                # Apply reaction
                girl["affection"] = max(0, min(aff_cap, aff + reaction))
                aff = girl["affection"]
                term.print(f"Reaction: {reaction:+} affection (now {aff}/{aff_cap})")

                # Track daily gift
                _reset_daily_limits(player)
                uid = _girl_unique_id(girl)
                player["girl_gift_today"][uid] = True
                stress_delta = -12 if reaction > 0 else (-6 if reaction == 0 else 4)
                stress_now = adjust_stress(girl, stress_delta)
                term.print(f"  Stress {stress_delta:+d} (now {stress_now}).")
                term.pause()

            elif action == "bath":
                remove_item_by_reference(player, bath_item)
                stress_now = adjust_stress(girl, -20)
                term.print(f"\nYou draw a warm bath for {disp}. She sinks in with a long sigh and comes out loose-limbed and calm.")
                term.print(f"  Stress −20 (now {stress_now}).")
                term.pause()

            elif action == "blessing":  # Blessing
                buff_line = dialogue.get("house_buff", f"{disp} grants you a blessing.")
                term.print(buff_line.format(name=disp) if "{name}" in buff_line else buff_line)
                # Apply a buff: +1 all stats for 1 floor
                player.setdefault("active_buffs", [])
                player["active_buffs"] = [b for b in player["active_buffs"] if b.get("type") != "girl_blessing"]
                player["active_buffs"].append({
                    "type": "girl_blessing",
                    "stat": "all",
                    "value": 1,
                    "remaining": 1,
                })
                term.print("You feel a warm glow – +1 to all stats for 1 floor.")
                term.pause()

            elif action == "kiss":  # Kiss
                kiss_line = dialogue.get("house_bond_kiss", f"{disp} kisses you tenderly.")
                term.print(kiss_line.format(name=disp) if "{name}" in kiss_line else kiss_line)
                # Heal and boost affection
                player["current_hp"] = min(player["current_hp"] + 20, player_max_hp(player))
                gain = random.randint(5, 10)
                girl["affection"] = min(aff_cap, aff + gain)
                aff = girl["affection"]
                term.print(f"Affection +{gain} (now {aff}/{aff_cap}). You feel renewed (healed 20 HP).")
                stress_now = adjust_stress(girl, -4)
                term.print(f"  She looks a little lighter — Stress −4 (now {stress_now}).")
                term.pause()

            elif action == "propose":
                # ── PROPOSE ──
                # Let the player choose which ring to offer — its stats become
                # her permanent engagement bonus, so the choice matters.
                rings = _get_engagement_rings(player)
                if not rings:
                    term.print("You don't have an engagement ring.")
                    term.pause()
                    continue
                if len(rings) == 1:
                    ring = rings[0]
                else:
                    ring_labels = []
                    for r in rings:
                        mods = r.get("mods") or r.get("base_mods") or {}
                        mod_txt = ", ".join(f"+{v} {stat}" for stat, v in mods.items())
                        ring_labels.append(f"{r['name']} ({mod_txt})" if mod_txt else r["name"])
                    ridx = term.menu(ring_labels + ["Back"],
                                     prompt=f"Which ring will you offer to {disp}?")
                    if ridx < 0 or ridx >= len(rings):
                        continue
                    ring = rings[ridx]

                engaged_line = dialogue.get("house_engaged", f"{disp} gasps, her eyes sparkling with tears of joy. 'Yes! Yes, I will marry you!' She throws her arms around you.")
                term.print("\n" + (engaged_line.format(name=disp) if "{name}" in engaged_line else engaged_line))
                # Consume the chosen ring
                remove_item_by_reference(player, ring)

                # The ring's power becomes her permanent engagement bonus
                # (folded into her stored stats so it shows up everywhere).
                ring_bonus = _apply_ring_bonus_to_girl(girl, ring)
                if ring_bonus:
                    bonus_lines = [f"{stat} +{val}" for stat, val in ring_bonus.items()]
                    term.print(f"  The ring's power flows into {disp}: {', '.join(bonus_lines)}.")

                girl["engaged"] = True
                girl["affection_cap"] = 200
                player.setdefault("engaged_girls", [])
                if girl_key not in player["engaged_girls"]:
                    player["engaged_girls"].append(girl_key)
                term.print(f"\n  *** {disp} is now engaged to you! Affection cap raised to 200. ***")
                term.pause()
                continue

            elif action == "ascend":
                # ── ASCEND ──
                current_cap = girl.get("level_cap", 10)
                requirements = _get_ascension_requirements(current_cap)

                # Gather all required stones from inventory (stack-aware)
                inv = player.get("inventory", [])
                consumed_refs = []
                for tier, count in requirements:
                    tier_consumed = consume_stackable_items(player, lambda item: item.get("ascension_tier") == tier, count)
                    total_found = sum(amt for _, amt in tier_consumed)
                    if total_found < count:
                        term.print("You do not have enough Ascension Stones.")
                        term.pause()
                        continue
                    consumed_refs.extend(tier_consumed)

                # Build summary of consumed stones for display
                stone_summary = ", ".join(
                    f"{count} Stone {_int_to_roman(tier)}"
                    for tier, count in requirements
                )
                # Pick the highest-tier stone for dialogue reference
                highest_stone = next(
                    (item for item, _ in consumed_refs if item.get("ascension_tier") == current_cap // 10),
                    consumed_refs[0][0] if consumed_refs else None
                )

                # Capture old cap before the ceremony
                old_cap = girl["level_cap"]

                # Dialogue 1: Ally's reaction (from monster_girls.yaml)
                pre_line = dialogue.get("ascension_pre_ceremony",
                    f"{disp} kneels before you, her eyes closed in reverence.\n'I feel the chains upon my soul. Please... set me free.'")
                pre_line = pre_line.format(name=disp, stone=highest_stone['name'] if highest_stone else 'stone', old_cap=old_cap)
                term.print("\n" + pre_line)
                term.pause("Press Continue to begin the ceremony...")

                girl["level_cap"] = old_cap + 10

                # Dialogue 2: The ascension itself (from monster_girls.yaml)
                post_line = dialogue.get("ascension_post_ceremony",
                    f"The {highest_stone['name'] if highest_stone else 'stone'} shatters into motes of prismatic light!\nAncient power surges through {disp}.\nHer form shimmers, breaking the seal of Level {old_cap}.")
                post_line = post_line.format(name=disp, stone=highest_stone['name'] if highest_stone else 'stone', old_cap=old_cap)
                term.print(f"\n{'='*50}")
                term.print("  " + post_line.replace("\n", "\n  "))
                term.print(f"  Stones consumed: {stone_summary}")
                term.print(f"  *** LEVEL CAP INCREASED: {old_cap} → {girl['level_cap']} ***")
                term.print(f"{'='*50}")

                term.print(f"\n{disp} opens her eyes, renewed and stronger.")
                term.print("'I can feel it... the path ahead is open once more.'")
                term.pause()

            elif action == "awaken":
                # ── AWAKEN (docs/awakening_design.md Part C) ──
                if player.get("awakening_sigils", 0) < 1:
                    term.print("\nYou have no Awakening Sigils.")
                    term.print("Sigils come from your first-ever superboss kill, from Mary Sue,")
                    term.print("or from the Arcane Tower — Awakening Research")
                    term.print("(4 Sigil Shards + 25,000 gold). Shards drop from first-time superbosses.")
                    term.pause()
                    continue

                from combat.ally_skills import apply_awakening_skills, get_innate_skill_def
                awakened_name = template.get("awakened_name") or girl.get("name", disp)

                # Dialogue 1: her plea
                pre_line = dialogue.get("awakening_pre_ceremony",
                    f"{disp} takes your hands, her eyes shining. 'I can feel it — the person I was meant to be. Please... call me by my true name.'")
                term.print("\n" + _fmt_dialogue(pre_line, name=disp, new_name=awakened_name))
                term.pause("Press Continue to begin the awakening...")

                # Consume the Sigil and perform the awakening
                player["awakening_sigils"] = player.get("awakening_sigils", 0) - 1
                apply_awakening_skills(girl, girl_key)
                girl["awakened"] = True
                girl["awakened_name"] = awakened_name

                # The one-time special scene (multi-beat)
                scene = dialogue.get("awakening_scene",
                    f"Light gathers around {disp} like a rising tide.\nHer old name sloughs away like a shed skin.\nWhen the glow fades she stands taller — and smiles.\n'{awakened_name}... I like the sound of that. Yours, always.'")
                term.print(f"\n{'='*50}")
                term.print("  " + _fmt_dialogue(scene, name=disp, new_name=awakened_name).replace("\n", "\n  "))
                term.print(f"{'='*50}")

                # Dialogue 2: her vow, under the new name
                post_line = dialogue.get("awakening_post_ceremony",
                    f"{awakened_name} flexes her fingers, feeling the new strength in them. 'I'm ready. Whatever comes next — we face it together.'")
                term.print("\n" + _fmt_dialogue(post_line, name=awakened_name, new_name=awakened_name))

                # Show the upgraded kit
                term.print(f"\n  *** {disp} awakens as {awakened_name}! ***")
                for sid in girl.get("awakened_skills", []):
                    sdef = get_innate_skill_def(sid)
                    if sdef:
                        term.print(f"    ★ {sdef['name']} — {sdef.get('description', '')}")
                term.print(f"  (Awakening Sigils left: {player['awakening_sigils']})")
                term.pause()
                continue

            elif action == "recruit":
                # ── RECRUIT ──
                aff = girl.get("affection", 30)
                if aff < RECRUIT_AFFECTION_THRESHOLD:
                    denied_msg = dialogue.get("recruit_denied",
                        f"{disp} looks at you uncertainly. 'I don't know you well enough yet...'")
                    term.print(denied_msg.format(name=disp))
                    term.print(f"  (Need {RECRUIT_AFFECTION_THRESHOLD}+ affection. Currently: {aff}/{aff_cap})")
                    term.pause()
                else:
                    day_now = player.get("day", 1)
                    if girl.get("dispatch_mission"):
                        term.print(f"{disp} is away on a dispatch — she'll see you when she's back.")
                        term.pause()
                        continue
                    if int(girl.get("injured_until", 0) or 0) > day_now:
                        term.print(f"{disp} is injured (recovering until Day {girl['injured_until']}) and can't join the party yet.")
                        term.pause()
                        continue
                    accepted_msg = dialogue.get("recruit_accepted",
                        f"{disp} smiles warmly. 'I'll fight beside you!'")
                    term.print(accepted_msg.format(name=disp))
                    from combat.ally import recruit_ally_from_house
                    ally, msg = recruit_ally_from_house(player, girl, house)
                    term.print(msg)
                    if ally:
                        term.print(f"{display_name(ally)}'s stats:")
                        term.print(f"  HP: {ally['max_hp']}")
                        term.print(f"  STR: {ally['attributes']['Strength']}  CON: {ally['attributes']['Constitution']}  DEX: {ally['attributes']['Dexterity']}")
                    term.pause()
                    break  # after recruitment, return to girl list

            elif action == "dismiss":
                # ── DISMISS ──
                dismiss_msg = dialogue.get("dismiss",
                    f"{disp} nods quietly. 'I'll be here when you need me.'")
                term.print(dismiss_msg.format(name=disp) if "{name}" in dismiss_msg else dismiss_msg)
                from combat.ally import _return_ally_to_house
                _return_ally_to_house(player, girl, house)
                player["allies"] = [a for a in player.get("allies", []) if not (a.get("key") == girl.get("key") and a.get("name") == girl.get("name"))]
                term.print(f"{disp} has been returned to the lounge.")
                term.pause()
                break  # after dismissal, return to girl list

            else:
                term.print("Invalid option.")
                term.pause()

def get_gift_reaction(girl_key, gift_type):
    """Load personalized gift reactions from monster_girls.yaml"""
    try:
        reactions = AFFECTION_GIFTS.get(girl_key, {})
        return reactions.get(gift_type, random.randint(-15, 25))
    except:
        return random.randint(-10, 30)


# ── Main house menu ───────────────────────────────────────────────────────────

def _dispatch_board(player, city_id, house):
    """Dispatch board (Phase 1) — send housed girls on sweeps and errands.

    Operates on the effective home house (explicit city → origin → first
    owned, via _resolve_house) even if the player opened a secondary house.
    """
    from resources.cities import CITIES
    from facilities.dispatch import (
        ensure_offers, slot_cap, star_cap, refresh_day, get_dispatch_state,
        sanitize_flags, collect_reports,
    )

    home_city, home_house = _resolve_house(player)
    if home_house is None:
        term.print("You don't have a home yet.")
        term.pause()
        return

    sanitize_flags(player, home_house)

    while True:
        term.clear()
        d = get_dispatch_state(player)
        level = int(home_house.get("level", 1))
        active = list(d.get("active", []))
        offers = ensure_offers(player, home_city, home_house)
        city_name = CITIES.get(home_city, {}).get("name", home_city)

        term.print(f"=== DISPATCH BOARD ===  ({city_name})")
        term.print(f"  Slots: {len(active)}/{slot_cap(level)} used · "
                   f"House limit: {'★' * star_cap(level)}")
        for inst in active:
            day, mins = divmod(int(inst.get("return_abs", 0)), 1440)
            term.print(f"  Away: {'★' * int(inst.get('stars', 1))} {inst['name']}")
            term.print(f"        Team: {', '.join(inst.get('girl_names', []))} — "
                       f"back Day {day}, {mins // 60:02d}:{mins % 60:02d}")
        rep_count = len(d.get("reports", []))
        if rep_count:
            term.print(f"  Reports: {rep_count} ready to collect")
        term.print(f"  Offers refresh: Day {refresh_day(player.get('day', 1))} (3-day cycle)")
        if not offers:
            term.print("  No missions left on the board this cycle.")
        term.print()

        options, actions = [], []
        for offer in offers:
            options.append(f"{'★' * offer['stars']} {offer['name']} — {offer['label']}, "
                           f"power {offer['power']}, ~{offer['hours']}h, risk {offer['risk']}")
            actions.append(("offer", offer))
        options.append("View active dispatches")
        actions.append(("view", None))
        if rep_count:
            options.append(f"Collect reports ({rep_count})")
            actions.append(("collect", None))

        idx = term.menu(options, prompt="Choose a mission:", allow_cancel=True,
                        cancel_label="Back", columns=2)
        if idx < 0:
            return
        kind, payload = actions[idx]

        if kind == "offer":
            if len(active) >= slot_cap(level):
                term.print("All dispatch slots are in use — wait for a team to return.")
                term.pause()
                continue
            _dispatch_team_select(player, home_city, home_house, payload)
        elif kind == "view":
            term.clear()
            if not active:
                term.print("No active dispatches.")
            for inst in active:
                day, mins = divmod(int(inst.get("return_abs", 0)), 1440)
                term.print(f"{'★' * int(inst.get('stars', 1))} {inst['name']}")
                term.print(f"  Team: {', '.join(inst.get('girl_names', []))}")
                term.print(f"  Returns: Day {day}, {mins // 60:02d}:{mins % 60:02d}")
            term.pause()
        elif kind == "collect":
            collect_reports(player, home_city, home_house)


def _dispatch_team_select(player, home_city, house, offer):
    """Toggle-select a team, preview success, and launch the mission."""
    from facilities.dispatch import (
        eligible_girls, team_cap, success_chance_for, create_instance,
    )
    cap = team_cap(house.get("level", 1))
    team = []

    while True:
        term.clear()
        day = player.get("day", 1)
        term.print(f"=== {offer['name']} ===")
        term.print(f"  {'★' * offer['stars']} {offer['label']} · power {offer['power']} · "
                   f"~{offer['hours']}h · risk {offer['risk']}")
        if offer.get("floors"):
            term.print(f"  Floors {offer['floors'][0]}–{offer['floors'][1]}")
        term.print(f"  Team: {len(team)}/{cap} — press a name to add/remove it")
        term.print()

        LAUNCH_STYLE = {"bg": "#2f6b2f", "fg": "#e0ffe0",
                        "active_bg": "#3f8b3f", "active_fg": "#f0fff0"}

        pool = eligible_girls(player, house)
        options, actions, styles = [], [], []
        for g in pool:
            mark = "★" if any(g is m for m in team) else " "
            options.append(f"[{mark}] {display_name(g)} Lv{g.get('level', 1)} — {girl_status_line(g, day)}")
            actions.append(("toggle", g))
            styles.append(None)
        if not pool:
            term.print("No girls are available (away, injured, or burned out).")
        if team:
            chance = success_chance_for(offer, team, day)
            names = ", ".join(display_name(g) for g in team)
            options.append(f"▶ Launch — {names} (projected success ~{chance}%)")
            actions.append(("launch", None))
            styles.append(LAUNCH_STYLE)

        idx = term.menu(options, prompt="Assemble your team:", allow_cancel=True,
                        cancel_label="Back", styles=styles, columns=2)
        if idx < 0:
            return
        kind, payload = actions[idx]

        if kind == "toggle":
            if payload in team:
                team.remove(payload)
            elif len(team) >= cap:
                term.print(f"At most {cap} girls can go on one mission.")
                term.pause()
            else:
                team.append(payload)
        elif kind == "launch":
            if not team:
                term.print("Pick at least one girl.")
                term.pause()
                continue
            names = ", ".join(display_name(g) for g in team)
            if not term.confirm(f"Send {names} on \"{offer['name']}\"?"):
                continue
            inst, msg = create_instance(player, home_city, house, offer, team)
            term.print(msg)
            if inst:
                advance_time(player, 30)  # organizing the send-off
            term.pause()
            return


def house_menu(player, city_id):
    """Entry point called from city.py when player chooses 'Your House'."""
    house    = _get_house(player, city_id)
    if house is None:
        term.print("You don't own a house here.")
        term.pause()
        return

    max_level = max(HOUSE_LEVELS)

    while True:
        term.clear()
        lvl_data = _house_level_data(house)
        pending  = _pending_income(player, city_id, house)
        total_girls = len(house.get("monster_girls", [])) + len(player.get("allies", []))
        max_girls = HOUSE_MONSTER_GIRL_LIMITS.get(house["level"], 2)

        term.print(f"=== Your {lvl_data['name']} ===")
        term.print(f"  Level    : {house['level']} — {lvl_data['name']}")
        term.print(f"  Girls    : {total_girls}/{max_girls}")
        term.print(f"  Storage  : {len(house['storage'])}/{lvl_data['storage_cap']} slots")
        term.print(f"  Pending  : {pending} gold")
        term.print(f"  Gold     : {player.get('gold', 0)}")
        term.print(f"  Date     : {format_date(player)}")

        options = [
            "Rest (quick heal)",
            "Sleep (full heal; Night only)",
            "Wait (a brief moment)",
            "Wait (a while)",
            "Storage chest",
            "Collect income",
            "Lounge",
        ]
        actions = ["rest", "sleep", "wait1", "waitwhile", "storage", "income", "lounge"]

        options.append(board_label(player))
        actions.append("dispatch")

        if house["level"] < max_level:
            next_name = HOUSE_LEVELS[house["level"] + 1]["name"]
            options.append(f"Upgrade to {next_name}")
            actions.append("upgrade")
        options.append("Leave")
        actions.append("leave")

        choice = term.menu(options, prompt="What would you like to do?")
        action = actions[choice] if 0 <= choice < len(actions) else ("leave" if choice == -1 else None)

        if action == "rest":
            _house_rest(player, city_id, house)
        elif action == "sleep":
            _house_sleep(player, city_id, house)
        elif action == "wait1":
            import time_blocks
            time_blocks.wait_blocks(player, 1)
            term.print("Time passes...")
            term.pause()
        elif action == "waitwhile":
            import time_blocks
            result = time_blocks.wait_to_next_phase(player)
            if result is None:
                term.print("You wait. Wonderland waits with you. Nothing passes.")
            elif result == "morning":
                term.print("You sit through the night and greet the morning, exhausted.")
            else:
                term.print(f"A while passes... it is now {result}.")
            term.pause()
        elif action == "storage":
            _house_storage(player, city_id, house)
        elif action == "income":
            _house_collect_income(player, city_id, house)
        elif action == "lounge":
            _house_lounge(player, city_id, house)
        elif action == "dispatch":
            _dispatch_board(player, city_id, house)
        elif action == "upgrade":
            _house_upgrade(player, city_id, house)
        elif action == "leave":
            break
        else:
            term.print("Invalid choice.")
            term.pause()