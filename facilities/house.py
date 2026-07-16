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

from utils import clear_screen, advance_time
from events import format_date
from character import player_max_hp
import random
from resources.enemies import AFFECTION_GIFTS, ENEMIES
from gui.terminal import term

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
    for item in player.get("inventory", []):
        if item.get("id") in ENGAGEMENT_RING_IDS:
            return True
    return False


def _get_engagement_ring_item(player):
    """Return the first engagement ring found in inventory, or None."""
    for item in player.get("inventory", []):
        if item.get("id") in ENGAGEMENT_RING_IDS:
            return item
    return None


def _girl_unique_id(girl):
    """Return a stable unique identifier for a girl (key + name)."""
    return f"{girl.get('key', '')}:{girl.get('name', '')}"


def get_current_house_allies(player):
    """Return list of all monster girl allies currently in the active party."""
    return player.get("allies", [])


def get_house_data(player, city_id=None):
    """Return the list of monster girls in the first house (or specified city)."""
    if not city_id:
        city_id = player.get("origin_city", "solmere")
    house = _get_house(player, city_id)
    if not house:
        return []
    return house.get("monster_girls", [])


def save_house_data(player, girls_data, city_id=None):
    """Save monster girl data back to the house."""
    if not city_id:
        city_id = player.get("origin_city", "solmere")
    if not player.get("houses"):
        player["houses"] = {}
    if not player["houses"].get(city_id):
        player["houses"][city_id] = {"level": 1, "storage": [], "last_income_day": player.get("day", 1)}
    player["houses"][city_id]["monster_girls"] = girls_data


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
            recovered_line = dialogue.get("is_recovered", f"{ally['name']} is back on their feet!")
            if "{name}" in recovered_line:
                recovered_line = recovered_line.format(name=ally['name'])
            term.print(f"  {recovered_line}")
        elif ally.get("current_hp", 0) > 0:
            ally_old = ally["current_hp"]
            ally["current_hp"] = ally["max_hp"]
            ally_healed = ally["max_hp"] - ally_old
            term.print(f"  {ally['name']} healed {ally_healed} HP → {ally['max_hp']}/{ally['max_hp']}")

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
    """Sleep at home — full heal + 8 hours pass. Only available between 20:00 and 04:00.
    From Manor onward, also grants a Well-Rested stat buff that lasts for dungeon rooms.
    Stat bonus: +1 (Manor–Villa), +2 (Estate–Citadel), +3 (Sanctuary)."""
    current_hour = player.get("time_minutes", 0) // 60
    if not (current_hour >= 20 or current_hour < 4):
        term.print("You can only sleep at home between 20:00 and 04:00.")
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
            recovered_line = dialogue.get("is_recovered", f"{ally['name']} is back on their feet!")
            if "{name}" in recovered_line:
                recovered_line = recovered_line.format(name=ally['name'])
            term.print(f"  {recovered_line}")
        elif ally.get("current_hp", 0) > 0:
            ally_old = ally["current_hp"]
            ally["current_hp"] = ally["max_hp"]
            ally_healed = ally["max_hp"] - ally_old
            term.print(f"  {ally['name']} healed {ally_healed} HP → {ally['max_hp']}/{ally['max_hp']}")

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

    advance_time(player, 480)

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
            from combat.wedding_specials import is_wedding_item_soulbound
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


def _int_to_roman(num):
    """Convert integer (1-10) to Roman numeral."""
    val = [10, 9, 5, 4, 1]
    syms = ["X", "IX", "V", "IV", "I"]
    roman = ""
    i = 0
    while num > 0:
        d = num // val[i]
        roman += syms[i] * d
        num -= d * val[i]
        i += 1
    return roman


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
            term.print(f"Active Party: {len(allies)}/3 allies")

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
            if where == "active":
                if g.get("defeated") or g.get("current_hp", 0) <= 0:
                    hp_str = "[INCAPACITATED]"
                else:
                    hp_str = f"HP: {g['current_hp']}/{g['max_hp']}"
                term.print(f"  {i+1}. {g['name']} (Lv {g['level']}{cap_tag}){active_tag} — {hp_str} — {status} Affection: {aff_str}{ready}")
            else:
                term.print(f"  {i+1}. {g['name']} (Lv {g['level']}){active_tag} — {status} Affection: {aff_str}{ready}")

        # ── Build menu: girl options + filter controls + back ───────────────
        girl_options = []
        girl_styles = []
        for where, g in all_girls:
            aff = g.get("affection", 30)
            active_tag = " [ACTIVE]" if where == "active" else ""
            girl_options.append(f"{g['name']} (Lv {g['level']}){active_tag} — \u2665{aff}")
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
            aff_cap = girl.get("affection_cap", 100)
            engaged = girl.get("engaged", False)
            married = girl.get("married", False)
            term.print(f"=== {girl['name']} ===")
            term.print(f"  Affection: {aff}/{aff_cap}")
            status_label = "Married" if married else "Engaged" if engaged else "Active" if where == "active" else "At home"
            term.print(f"  Status: {status_label}")
            ring_bonus = girl.get("ring_stat_bonus")
            if ring_bonus:
                bonus_lines = [f"{stat} +{val}" for stat, val in ring_bonus.items()]
                term.print(f"  Ring Blessing: {', '.join(bonus_lines)}")
            if where == "active":
                cap = girl.get("level_cap", 10)
                term.print(f"  Level: {girl['level']}/{cap}")
            term.print()

            talks_left = _talks_remaining(player, _girl_unique_id(girl))
            gift_ready = _gifts_remaining(player, _girl_unique_id(girl))
            can_propose = (aff >= 100 and not engaged and not married and _has_engagement_ring(player))

            can_ascend = where == "active" and _can_ascend_ally(player, girl)
            at_cap = where == "active" and girl["level"] >= girl.get("level_cap", 10)

            # Build dynamic menu options
            menu_options = []
            menu_actions = []

            menu_options.append(f"Talk  ({talks_left} left today)")
            menu_actions.append("talk")

            menu_options.append(f"Give a gift  ({'ready' if gift_ready else 'already gifted today'})")
            menu_actions.append("gift")

            if aff >= 60:
                menu_options.append("Ask for blessing")
                menu_actions.append("blessing")

            if aff >= 80:
                menu_options.append("Share a kiss")
                menu_actions.append("kiss")

            if can_propose:
                menu_options.append("Propose marriage")
                menu_actions.append("propose")

            if can_ascend:
                menu_options.append("Ascend (break level limit)")
                menu_actions.append("ascend")
            elif at_cap:
                requirements = _get_ascension_requirements(girl.get("level_cap", 10))
                needs = ", ".join(f"{count} Stone {_int_to_roman(tier)}" for tier, count in requirements)
                term.print(f"  [Ascend: needs {needs}]")

            if where == "lounge":
                menu_options.append("Recruit to party")
                menu_actions.append("recruit")

            if where == "active":
                menu_options.append("Remove from party")
                menu_actions.append("dismiss")

            menu_options.append("Back")
            menu_actions.append("back")

            choice_idx = term.menu(menu_options, prompt=f"What to do with {girl['name']}?")
            if choice_idx < 0:
                break
            action = menu_actions[choice_idx] if choice_idx < len(menu_actions) else "back"

            if action == "back":
                break

            elif action == "talk":
                if talks_left <= 0:
                    term.print(f"\n{girl['name']} seems tired of talking. Come back tomorrow.")
                    term.pause()
                    continue

                # Wedding gift check (affection at cap and engaged but not married)
                if engaged and not married and aff >= aff_cap:
                    special_line = dialogue.get("house_special_gift",
                        f"{girl['name']} pulls out a beautifully wrapped box. 'This is for you, my love.'")
                    term.print("\n" + (special_line.format(name=girl['name']) if "{name}" in special_line else special_line))
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
                    term.print(f"\n  *** {girl['name']} is now your wife! ***")
                    term.pause()
                    continue

                # Determine dialogue key
                if engaged and not married:
                    # Alternate between engaged_1 and engaged_2
                    if player.get("day", 1) % 2 == 0:
                        dialog_key = "house_talk_engaged_2"
                        default = f"{girl['name']} leans against you, smiling. 'Every day with you feels like a dream. I can't wait for our wedding.'"
                    else:
                        dialog_key = "house_talk_engaged_1"
                        default = f"{girl['name']} beams at you, her engagement ring catching the light. 'Can you believe it? We're going to be together forever!'"
                    line = dialogue.get(dialog_key, default)
                elif aff <= 30:
                    dialog_key = "house_talk_low"
                    line = dialogue.get(dialog_key, f"{girl['name']} looks at you expectantly.")
                elif aff <= 60:
                    dialog_key = "house_talk_mid"
                    line = dialogue.get(dialog_key, f"{girl['name']} looks at you expectantly.")
                elif aff <= 80:
                    dialog_key = "house_talk_high"
                    line = dialogue.get(dialog_key, f"{girl['name']} looks at you expectantly.")
                else:
                    dialog_key = "house_talk_max"
                    line = dialogue.get(dialog_key, f"{girl['name']} looks at you expectantly.")

                line = line.format(name=girl['name']) if "{name}" in line else line
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
                term.pause()

            elif action == "gift":
                if not gift_ready:
                    term.print(f"\n{girl['name']} has already received a gift today.")
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
                    love_line = dialogue.get("house_gift_love", f"{girl['name']} beams with joy!")
                    term.print(love_line.format(name=girl['name']) if "{name}" in love_line else love_line)
                elif reaction < 0:
                    hate_line = dialogue.get("house_gift_hate", f"{girl['name']} sighs, disappointed.")
                    term.print(hate_line.format(name=girl['name']) if "{name}" in hate_line else hate_line)
                else:
                    term.print(f"{girl['name']} shrugs indifferently.")

                # Apply reaction
                girl["affection"] = max(0, min(aff_cap, aff + reaction))
                aff = girl["affection"]
                term.print(f"Reaction: {reaction:+} affection (now {aff}/{aff_cap})")

                # Track daily gift
                _reset_daily_limits(player)
                uid = _girl_unique_id(girl)
                player["girl_gift_today"][uid] = True
                term.pause()

            elif action == "blessing":  # Blessing
                buff_line = dialogue.get("house_buff", f"{girl['name']} grants you a blessing.")
                term.print(buff_line.format(name=girl['name']) if "{name}" in buff_line else buff_line)
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
                kiss_line = dialogue.get("house_bond_kiss", f"{girl['name']} kisses you tenderly.")
                term.print(kiss_line.format(name=girl['name']) if "{name}" in kiss_line else kiss_line)
                # Heal and boost affection
                player["current_hp"] = min(player["current_hp"] + 20, player_max_hp(player))
                gain = random.randint(5, 10)
                girl["affection"] = min(aff_cap, aff + gain)
                aff = girl["affection"]
                term.print(f"Affection +{gain} (now {aff}/{aff_cap}). You feel renewed (healed 20 HP).")
                term.pause()

            elif action == "propose":
                # ── PROPOSE ──
                ring = _get_engagement_ring_item(player)
                if not ring:
                    term.print("You don't have an engagement ring.")
                    term.pause()
                    continue

                engaged_line = dialogue.get("house_engaged", f"{girl['name']} gasps, her eyes sparkling with tears of joy. 'Yes! Yes, I will marry you!' She throws her arms around you.")
                term.print("\n" + (engaged_line.format(name=girl['name']) if "{name}" in engaged_line else engaged_line))
                # Consume the ring
                remove_item_by_reference(player, ring)

                # Store the ring's stat bonus on the girl (persisted in house save)
                ring_bonus = ring.get("base_mods", {})
                if ring_bonus:
                    girl["ring_stat_bonus"] = ring_bonus.copy()
                    bonus_lines = [f"{stat} +{val}" for stat, val in ring_bonus.items()]
                    term.print(f"  The ring's power flows into {girl['name']}: {', '.join(bonus_lines)}.")

                girl["engaged"] = True
                girl["affection_cap"] = 200
                player.setdefault("engaged_girls", [])
                if girl_key not in player["engaged_girls"]:
                    player["engaged_girls"].append(girl_key)
                term.print(f"\n  *** {girl['name']} is now engaged to you! Affection cap raised to 200. ***")
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
                    f"{girl['name']} kneels before you, her eyes closed in reverence.\n'I feel the chains upon my soul. Please... set me free.'")
                pre_line = pre_line.format(name=girl['name'], stone=highest_stone['name'] if highest_stone else 'stone', old_cap=old_cap)
                term.print("\n" + pre_line)
                term.pause("Press Continue to begin the ceremony...")

                girl["level_cap"] = old_cap + 10

                # Dialogue 2: The ascension itself (from monster_girls.yaml)
                post_line = dialogue.get("ascension_post_ceremony",
                    f"The {highest_stone['name'] if highest_stone else 'stone'} shatters into motes of prismatic light!\nAncient power surges through {girl['name']}.\nHer form shimmers, breaking the seal of Level {old_cap}.")
                post_line = post_line.format(name=girl['name'], stone=highest_stone['name'] if highest_stone else 'stone', old_cap=old_cap)
                term.print(f"\n{'='*50}")
                term.print("  " + post_line.replace("\n", "\n  "))
                term.print(f"  Stones consumed: {stone_summary}")
                term.print(f"  *** LEVEL CAP INCREASED: {old_cap} → {girl['level_cap']} ***")
                term.print(f"{'='*50}")

                term.print(f"\n{girl['name']} opens her eyes, renewed and stronger.")
                term.print("'I can feel it... the path ahead is open once more.'")
                term.pause()

            elif action == "recruit":
                # ── RECRUIT ──
                aff = girl.get("affection", 30)
                if aff < RECRUIT_AFFECTION_THRESHOLD:
                    denied_msg = dialogue.get("recruit_denied",
                        f"{girl['name']} looks at you uncertainly. 'I don't know you well enough yet...'")
                    term.print(denied_msg.format(name=girl['name']))
                    term.print(f"  (Need {RECRUIT_AFFECTION_THRESHOLD}+ affection. Currently: {aff}/{aff_cap})")
                    term.pause()
                else:
                    accepted_msg = dialogue.get("recruit_accepted",
                        f"{girl['name']} smiles warmly. 'I'll fight beside you!'")
                    term.print(accepted_msg.format(name=girl['name']))
                    from combat.ally import recruit_ally_from_house
                    ally, msg = recruit_ally_from_house(player, girl, house)
                    term.print(msg)
                    if ally:
                        term.print(f"{ally['name']}'s stats:")
                        term.print(f"  HP: {ally['max_hp']}")
                        term.print(f"  STR: {ally['attributes']['Strength']}  CON: {ally['attributes']['Constitution']}  DEX: {ally['attributes']['Dexterity']}")
                    term.pause()
                    break  # after recruitment, return to girl list

            elif action == "dismiss":
                # ── DISMISS ──
                dismiss_msg = dialogue.get("dismiss",
                    f"{girl['name']} nods quietly. 'I'll be here when you need me.'")
                term.print(dismiss_msg.format(name=girl['name']) if "{name}" in dismiss_msg else dismiss_msg)
                from combat.ally import _return_ally_to_house
                _return_ally_to_house(player, girl, house)
                player["allies"] = [a for a in player.get("allies", []) if not (a.get("key") == girl.get("key") and a.get("name") == girl.get("name"))]
                term.print(f"{girl['name']} has been returned to the lounge.")
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
            "Sleep (full heal + 8 hours) — Available 20:00–04:00",
            "Storage chest",
            "Collect income",
            "Lounge",
        ]
        if house["level"] < max_level:
            next_name = HOUSE_LEVELS[house["level"] + 1]["name"]
            options.append(f"Upgrade to {next_name}")
        options.append("Leave")

        choice = term.menu(options, prompt="What would you like to do?")

        if choice == 0:
            _house_rest(player, city_id, house)
        elif choice == 1:
            _house_sleep(player, city_id, house)
        elif choice == 2:
            _house_storage(player, city_id, house)
        elif choice == 3:
            _house_collect_income(player, city_id, house)
        elif choice == 4:
            _house_lounge(player, city_id, house)
        elif choice == 5 and house["level"] >= max_level:
            break  # Leave (at max level, Leave is index 5)
        elif choice == 5:
            _house_upgrade(player, city_id, house)  # Upgrade (not at max)
        elif choice == 6 or choice == -1:
            break  # Leave or cancelled
        else:
            term.print("Invalid choice.")
            term.pause()