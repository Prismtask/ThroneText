# facilities/house.py
"""
Player House system.

Data layout in player dict
──────────────────────────
player["houses"] = {
    city_id: {
        "level":           int (1–3),
        "storage":         list of item dicts,
        "last_income_day": int  (game day when income was last collected),
    }
}

House levels
────────────
  Lv1 – Hovel     : storage 10 slots,  income  8 gold/day, rest time 90 min, bed buff +1 all / 1 floor
  Lv2 – Cottage   : storage 20 slots,  income 18 gold/day, rest time 70 min, bed buff +2 all / 2 floors
  Lv3 – Manor     : storage 35 slots,  income 35 gold/day, rest time 50 min, bed buff +3 all / 3 floors

Upgrade costs: Lv1→2 = 600 gold,  Lv2→3 = 1 500 gold

Bed buff uses the same active_buffs / "blessing" format as temple.py so
get_effective_attribute() in stats.py picks it up automatically.
"""

from utils import clear_screen, advance_time
from character import player_max_hp
import random
from resources.enemies import AFFECTION_GIFTS, ENEMIES

RECRUIT_AFFECTION_THRESHOLD = 50  # Minimum affection needed to recruit a girl

# ── Constants ────────────────────────────────────────────────────────────────

HOUSE_LEVELS = {
    1: {"name": "Hovel",   "storage_cap": 10, "income_per_day": 8,  "rest_minutes": 90,  "upgrade_cost": 600,  "bed_buff_value": 1, "bed_buff_floors": 1},
    2: {"name": "Cottage", "storage_cap": 20, "income_per_day": 18, "rest_minutes": 70,  "upgrade_cost": 1500, "bed_buff_value": 2, "bed_buff_floors": 2},
    3: {"name": "Manor",   "storage_cap": 35, "income_per_day": 35, "rest_minutes": 50,  "upgrade_cost": None, "bed_buff_value": 3, "bed_buff_floors": 3},
}

HOUSE_MONSTER_GIRL_LIMITS = {
    1: 2,   # Hovel: max 2 girls
    2: 4,   # Cottage: max 4 girls
    3: 8    # Manor: max 8 girls
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


def _pending_income(player, city_id, house):
    """Calculate gold owed since last collection, capped at MAX_INCOME_DAYS."""
    current_day = player.get("day", 1)
    last_day    = house.get("last_income_day", current_day)
    days_passed = min(current_day - last_day, MAX_INCOME_DAYS)
    if days_passed <= 0:
        return 0
    base      = _house_level_data(house)["income_per_day"]
    mult      = CITY_INCOME_MULT.get(city_id, 1.0)
    return int(days_passed * base * mult)


def _reset_daily_limits(player):
    """Reset daily talk/gift counters if the day has changed."""
    today = player.get("day", 1)
    last_day = player.get("girl_daily_last_day", 0)
    if today != last_day:
        player["girl_talk_today"] = {}
        player["girl_gift_today"] = {}
        player["girl_daily_last_day"] = today


def _talks_remaining(player, girl_key):
    """Return how many talks remain for this girl today (2–3 per day)."""
    _reset_daily_limits(player)
    talks_done = player.get("girl_talk_today", {}).get(girl_key, 0)
    # Randomize daily limit between 2 and 3, seeded by day + girl_key for consistency
    import hashlib
    seed = int(hashlib.md5(f"{player.get('day',1)}-{girl_key}".encode()).hexdigest(), 16)
    daily_limit = 2 + (seed % 2)  # 2 or 3
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
    """Rest at home — free full heal + well-rested buff, costs time based on house level.

    Buff format mirrors temple.py's blessing so stats.py picks it up automatically:
      { "type": "well_rested", "stat": "all", "value": N, "remaining": F }
    Only one well-rested buff is allowed at a time; resting again refreshes it.
    """
    lvl_data   = _house_level_data(house)
    rest_mins  = lvl_data["rest_minutes"]
    buff_val   = lvl_data["bed_buff_value"]
    buff_floors = lvl_data["bed_buff_floors"]
    max_hp     = player_max_hp(player)

    # Heal
    old_hp               = player["current_hp"]
    player["current_hp"] = max_hp
    healed               = max_hp - old_hp

    # Heal allies too
    for ally in player.get("allies", []):
        if ally.get("current_hp", 0) > 0:
            ally_old = ally["current_hp"]
            ally["current_hp"] = ally["max_hp"]
            ally_healed = ally["max_hp"] - ally_old
            print(f"  {ally['name']} healed {ally_healed} HP → {ally['max_hp']}/{ally['max_hp']}")

    # Remove any existing well-rested buff before applying a fresh one
    player.setdefault("active_buffs", [])
    player["active_buffs"] = [
        b for b in player["active_buffs"] if b.get("type") != "well_rested"
    ]

    # Apply new well-rested buff (same structure as temple blessing)
    player["active_buffs"].append({
        "type":      "well_rested",
        "stat":      "all",
        "value":     buff_val,
        "remaining": buff_floors,
    })

    # Also apply well-rested buff to allies
    for ally in player.get("allies", []):
        if ally.get("current_hp", 0) > 0:
            ally.setdefault("active_buffs", [])
            ally["active_buffs"] = [b for b in ally["active_buffs"] if b.get("type") != "well_rested"]
            ally["active_buffs"].append({
                "type":      "well_rested",
                "stat":      "all",
                "value":     buff_val,
                "remaining": buff_floors,
            })

    advance_time(player, rest_mins)

    home_name = lvl_data["name"].lower()
    print(f"You sleep soundly in your {home_name}.")
    if healed > 0:
        print(f"  Healed {healed} HP → {max_hp}/{max_hp}")
    else:
        print(f"  You were already at full health, but the rest still does you good.")
    print(f"  Well-Rested: +{buff_val} to all stats for {buff_floors} dungeon floor(s).")
    print(f"  ({rest_mins} minutes pass.)")
    input("\nPress Enter...")


from inventory import get_inventory_caps, count_inventory, get_sorted_equipment, get_sorted_items, remove_item_by_reference, consume_stackable_items

def _house_storage(player, city_id, house):
    """Move items between inventory and house storage chest."""
    lvl_data = _house_level_data(house)
    cap      = lvl_data["storage_cap"]
    storage  = house["storage"]

    while True:
        clear_screen()
        inv     = player.get("inventory", [])
        equip_cap, other_cap = get_inventory_caps(player)
        equip_count, other_count = count_inventory(player)
        print(f"=== House Storage ({len(storage)}/{cap} slots used) ===")
        print(f"Your Bag: {equip_count}/{equip_cap} equipment | {other_count}/{other_cap} items")

        print("\n-- Chest --")
        if storage:
            for i, itm in enumerate(storage):
                print(f"  {i+1}. {itm['name']} ({itm['type']})")
        else:
            print("  (empty)")

        print("\n-- Your Bag --")
        if inv:
            sorted_equip = get_sorted_equipment(player)
            sorted_items = get_sorted_items(player)
            all_sorted = sorted_equip + sorted_items
            for i, itm in enumerate(all_sorted):
                tag = f"[{itm.get('rarity','common')}]"
                if itm.get("type") == "equipment":
                    print(f"  {i+1}. {itm['name']} ({itm['slot']}) {tag}")
                else:
                    print(f"  {i+1}. {itm['name']} ({itm['type']}) {tag}")
        else:
            print("  (empty)")

        print("\n[D]eposit to chest  [W]ithdraw from chest  [B]ack")
        act = input("Choice: ").strip().lower()

        if act == "d":
            if not inv:
                print("Your bag is empty.")
                input("Press Enter...")
                continue
            if len(storage) >= cap:
                print(f"Chest is full ({cap} slots).")
                input("Press Enter...")
                continue
            print("\nEnter numbers to deposit (e.g. '1 3 5', '1-4', or 'all'). 0 to cancel.")
            raw = input("Deposit which items? ").strip().lower()
            if raw in ("", "0", "cancel"):
                print("Cancelled.")
                input("Press Enter...")
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
                print("No valid items selected.")
                input("Press Enter...")
                continue

            # Check capacity before depositing
            from combat.wedding_specials import is_wedding_item_soulbound
            filtered_indices = []
            for i in indices:
                item = all_sorted[i]
                if is_wedding_item_soulbound(item):
                    print(f"  {item['name']} is soulbound — it cannot leave your side.")
                else:
                    filtered_indices.append(i)
            
            if not filtered_indices:
                print("No valid items to deposit (all selected items are soulbound).")
                input("Press Enter...")
                continue

            deposit_count = len(filtered_indices)
            if len(storage) + deposit_count > cap:
                print(f"Not enough chest space. Can only store {cap - len(storage)} more items.")
                input("Press Enter...")
                continue

            for i in filtered_indices:
                item = all_sorted[i]
                orig_idx = next(idx for idx, itm in enumerate(player["inventory"]) if itm is item)
                player["inventory"].pop(orig_idx)
                storage.append(item)
            print(f"Stored {deposit_count} item(s) in your chest.")
            input("Press Enter...")

        elif act == "w":
            if not storage:
                print("The chest is empty.")
                input("Press Enter...")
                continue
            print("\nEnter numbers to withdraw (e.g. '1 3 5', '1-4', or 'all'). 0 to cancel.")
            raw = input("Withdraw which items? ").strip().lower()
            if raw in ("", "0", "cancel"):
                print("Cancelled.")
                input("Press Enter...")
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
                print("No valid items selected.")
                input("Press Enter...")
                continue

            # Check bag capacity before withdrawing
            withdraw_equip = sum(1 for i in indices if storage[i].get("type") == "equipment")
            withdraw_other = len(indices) - withdraw_equip
            equip_cap, other_cap = get_inventory_caps(player)
            equip_count, other_count = count_inventory(player)
            if equip_count + withdraw_equip > equip_cap:
                print(f"Not enough equipment bag space. Can hold {equip_cap - equip_count} more equipment.")
                input("Press Enter...")
                continue
            if other_count + withdraw_other > other_cap:
                print(f"Not enough item bag space. Can hold {other_cap - other_count} more items.")
                input("Press Enter...")
                continue

            for i in indices:
                item = storage.pop(i)
                player.setdefault("inventory", []).append(item)
            print(f"Took {len(indices)} item(s) from the chest.")
            input("Press Enter...")

        elif act == "b":
            break


def _house_collect_income(player, city_id, house):
    """Collect accumulated passive income."""
    gold = _pending_income(player, city_id, house)
    if gold <= 0:
        print("No income has accumulated yet. Come back tomorrow.")
    else:
        player["gold"]              = player.get("gold", 0) + gold
        house["last_income_day"]    = player.get("day", 1)
        print(f"You collect {gold} gold from your {_house_level_data(house)['name'].lower()}'s rental income.")
        print(f"  Gold: {player['gold']}")
    input("\nPress Enter...")


def _house_upgrade(player, city_id, house):
    """Upgrade the house to the next level."""
    lvl      = house["level"]
    lvl_data = HOUSE_LEVELS[lvl]
    cost     = lvl_data["upgrade_cost"]

    if cost is None:
        print("Your Manor is already at its grandest — no further upgrades available.")
        input("\nPress Enter...")
        return

    next_data = HOUSE_LEVELS[lvl + 1]
    print(f"Upgrade to {next_data['name']}?")
    print(f"  Cost         : {cost} gold")
    print(f"  Storage      : {lvl_data['storage_cap']} → {next_data['storage_cap']} slots")
    print(f"  Daily income : {lvl_data['income_per_day']} → {next_data['income_per_day']} gold")
    print(f"  Rest time    : {lvl_data['rest_minutes']} → {next_data['rest_minutes']} min")
    print(f"  Bed buff     : +{lvl_data['bed_buff_value']} all stats ({lvl_data['bed_buff_floors']} floor) "
          f"→ +{next_data['bed_buff_value']} all stats ({next_data['bed_buff_floors']} floors)")
    confirm = input("\nProceed? (y/n): ").strip().lower()

    if confirm != "y":
        print("Upgrade cancelled.")
        input("\nPress Enter...")
        return

    if player.get("gold", 0) < cost:
        print(f"Insufficient gold. You need {cost} gold.")
        input("\nPress Enter...")
        return

    player["gold"] -= cost
    house["level"]  = lvl + 1
    print(f"Your home has been expanded into a fine {next_data['name']}!")
    print(f"  Remaining gold: {player['gold']}")
    input("\nPress Enter...")


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


def _house_lounge(player, city_id, house):
    clear_screen()
    lvl_data = _house_level_data(house)
    girls = house.get("monster_girls", [])
    max_girls = HOUSE_MONSTER_GIRL_LIMITS.get(house["level"], 2)
    allies = player.get("allies", [])
    total_girls = len(girls) + len(allies)

    print(f"=== {lvl_data['name'].upper()} LOUNGE ===")
    print(f"Monster Girls: {total_girls}/{max_girls}")
    if allies:
        print(f"Active Party: {len(allies)}/3 allies")
    print()

    # Build combined list of all interactable girls
    all_girls = []
    for girl in girls:
        all_girls.append(("lounge", girl))
    for ally in allies:
        all_girls.append(("active", ally))

    if not all_girls:
        print("The lounge is quiet... no companions yet.")
        input("\nPress Enter...")
        return

    for i, (where, g) in enumerate(all_girls):
        aff = g.get("affection", 30)
        aff_cap = g.get("affection_cap", 100)
        status = "💍" if g.get("married") else "💎" if g.get("engaged") else "💖" if aff >= 80 else "❤️" if aff >= 50 else "😐"
        ready = " ✓" if aff >= RECRUIT_AFFECTION_THRESHOLD else ""
        active_tag = " [ACTIVE]" if where == "active" else ""
        cap_tag = " [CAP]" if where == "active" and g["level"] >= g.get("level_cap", 10) else ""
        aff_str = f"{aff}/{aff_cap}"
        if where == "active":
            print(f"  {i+1}. {g['name']} (Lv {g['level']}{cap_tag}){active_tag} — HP: {g['current_hp']}/{g['max_hp']} — {status} Affection: {aff_str}{ready}")
        else:
            print(f"  {i+1}. {g['name']} (Lv {g['level']}){active_tag} — {status} Affection: {aff_str}{ready}")

    try:
        idx = int(input("\nSelect a girl (number) or 0 to go back: ")) - 1
        if idx < 0 or idx >= len(all_girls):
            return
    except ValueError:
        return

    where, girl = all_girls[idx]
    girl_key = girl.get("key", "")
    template = ENEMIES.get(girl_key, {})
    dialogue = template.get("dialogue", {})
    aff = girl.get("affection", 30)

    # --- Sub-menu for this girl ---
    while True:
        clear_screen()
        aff_cap = girl.get("affection_cap", 100)
        engaged = girl.get("engaged", False)
        married = girl.get("married", False)
        print(f"=== {girl['name']} ===")
        print(f"  Affection: {aff}/{aff_cap}")
        status_label = "Married" if married else "Engaged" if engaged else "Active" if where == "active" else "At home"
        print(f"  Status: {status_label}")
        if where == "active":
            cap = girl.get("level_cap", 10)
            print(f"  Level: {girl['level']}/{cap}")
        print()

        talks_left = _talks_remaining(player, _girl_unique_id(girl))
        gift_ready = _gifts_remaining(player, _girl_unique_id(girl))
        can_propose = (aff >= 100 and not engaged and not married and _has_engagement_ring(player))

        print(f"1. Talk  ({talks_left} left today)")
        print(f"2. Give a gift  ({'ready' if gift_ready else 'already gifted today'})")
        if aff >= 60:
            print("3. Ask for blessing")
        if aff >= 80:
            print("4. Share a kiss")

        opt_num = 5
        if can_propose:
            print(f"{opt_num}. Propose marriage")
            opt_num += 1

        can_ascend = where == "active" and _can_ascend_ally(player, girl)
        at_cap = where == "active" and girl["level"] >= girl.get("level_cap", 10)
        if can_ascend:
            print(f"{opt_num}. Ascend (break level limit)")
            opt_num += 1
        elif at_cap:
            # Show what stones are needed
            requirements = _get_ascension_requirements(girl.get("level_cap", 10))
            needs = ", ".join(f"{count} Stone {_int_to_roman(tier)}" for tier, count in requirements)
            print(f"  [Ascend: needs {needs}]")
        if where == "lounge":
            print(f"{opt_num}. Recruit to party")
        print("0. Back")

        choice = input("\nChoice: ").strip()
        if choice == "0":
            break

        elif choice == "1":  # Talk
            if talks_left <= 0:
                print(f"\n{girl['name']} seems tired of talking. Come back tomorrow.")
                input("\nPress Enter...")
                continue

            # Wedding gift check (affection at cap and engaged but not married)
            if engaged and not married and aff >= aff_cap:
                special_line = dialogue.get("house_special_gift",
                    f"{girl['name']} pulls out a beautifully wrapped box. 'This is for you, my love.'")
                print("\n" + (special_line.format(name=girl['name']) if "{name}" in special_line else special_line))
                # Give wedding accessory
                wedding_id = f"wedding_{girl_key}"
                from resources.items import build_item, ITEMS
                if wedding_id in ITEMS:
                    wedding_item = build_item(wedding_id, "legendary")
                    wedding_item["unique"] = True
                    from inventory import add_item_to_inventory
                    if add_item_to_inventory(player, wedding_item):
                        print(f"\n  *** You received: {wedding_item['name']} ***")
                    else:
                        print(f"\n  Your inventory is full! The {wedding_item['name']} was left on the table.")
                else:
                    print(f"\n  (Wedding item '{wedding_id}' not found — this is a bug.)")
                girl["married"] = True
                player.setdefault("married_girls", [])
                if girl_key not in player["married_girls"]:
                    player["married_girls"].append(girl_key)
                # Remove from engaged list
                player.setdefault("engaged_girls", [])
                if girl_key in player["engaged_girls"]:
                    player["engaged_girls"].remove(girl_key)
                print(f"\n  *** {girl['name']} is now your wife! ***")
                input("\nPress Enter...")
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
            print("\n" + line)

            # Increase affection
            gain = random.randint(3, 7)
            girl["affection"] = min(aff_cap, aff + gain)
            aff = girl["affection"]
            print(f"\nAffection +{gain} (now {aff}/{aff_cap})")

            # Track daily talk
            _reset_daily_limits(player)
            uid = _girl_unique_id(girl)
            player["girl_talk_today"][uid] = player["girl_talk_today"].get(uid, 0) + 1
            input("\nPress Enter...")

        elif choice == "2":  # Gift
            if not gift_ready:
                print(f"\n{girl['name']} has already received a gift today.")
                input("\nPress Enter...")
                continue

            gifts = [it for it in player.get("inventory", []) if it.get("type") == "gift"]
            if not gifts:
                print("You have no gifts.")
                input("Press Enter...")
                continue

            print("\nYour Gifts:")
            for i, g in enumerate(gifts):
                print(f"{i+1}. {g['name']}")
            try:
                gidx = int(input("Choose gift: ")) - 1
                if gidx < 0 or gidx >= len(gifts):
                    print("Invalid gift.")
                    input("Press Enter...")
                    continue
                gift = gifts[gidx]
                # Remove from inventory
                gift_type = gift.get("gift_type", "unknown")
                reaction = get_gift_reaction(girl_key, gift_type)
                remove_item_by_reference(player, gift)

                # Show love/hate dialogue
                if reaction > 0:
                    love_line = dialogue.get("house_gift_love", f"{girl['name']} beams with joy!")
                    print(love_line.format(name=girl['name']) if "{name}" in love_line else love_line)
                elif reaction < 0:
                    hate_line = dialogue.get("house_gift_hate", f"{girl['name']} sighs, disappointed.")
                    print(hate_line.format(name=girl['name']) if "{name}" in hate_line else hate_line)
                else:
                    print(f"{girl['name']} shrugs indifferently.")

                # Apply reaction
                old_aff = aff
                girl["affection"] = max(0, min(aff_cap, aff + reaction))
                aff = girl["affection"]
                print(f"Reaction: {reaction:+} affection (now {aff}/{aff_cap})")

                # Track daily gift
                _reset_daily_limits(player)
                uid = _girl_unique_id(girl)
                player["girl_gift_today"][uid] = True
                input("\nPress Enter...")
            except (ValueError, IndexError):
                print("Invalid choice.")
                input("Press Enter...")

        elif choice == "3" and aff >= 60:  # Blessing
            buff_line = dialogue.get("house_buff", f"{girl['name']} grants you a blessing.")
            print(buff_line.format(name=girl['name']) if "{name}" in buff_line else buff_line)
            # Apply a buff: +1 all stats for 1 floor
            player.setdefault("active_buffs", [])
            player["active_buffs"] = [b for b in player["active_buffs"] if b.get("type") != "girl_blessing"]
            player["active_buffs"].append({
                "type": "girl_blessing",
                "stat": "all",
                "value": 1,
                "remaining": 1,
            })
            print("You feel a warm glow – +1 to all stats for 1 floor.")
            input("\nPress Enter...")

        elif choice == "4" and aff >= 80:  # Kiss
            kiss_line = dialogue.get("house_bond_kiss", f"{girl['name']} kisses you tenderly.")
            print(kiss_line.format(name=girl['name']) if "{name}" in kiss_line else kiss_line)
            # Heal and boost affection
            player["current_hp"] = min(player["current_hp"] + 20, player_max_hp(player))
            gain = random.randint(5, 10)
            girl["affection"] = min(aff_cap, aff + gain)
            aff = girl["affection"]
            print(f"Affection +{gain} (now {aff}/{aff_cap}). You feel renewed (healed 20 HP).")
            input("\nPress Enter...")

        elif choice == "5" and can_propose:
            # ── PROPOSE ──
            ring = _get_engagement_ring_item(player)
            if not ring:
                print("You don't have an engagement ring.")
                input("Press Enter...")
                continue

            engaged_line = dialogue.get("house_engaged", f"{girl['name']} gasps, her eyes sparkling with tears of joy. 'Yes! Yes, I will marry you!' She throws her arms around you.")
            print("\n" + (engaged_line.format(name=girl['name']) if "{name}" in engaged_line else engaged_line))
            girl["engaged"] = True
            girl["affection_cap"] = 200
            player.setdefault("engaged_girls", [])
            if girl_key not in player["engaged_girls"]:
                player["engaged_girls"].append(girl_key)
            print(f"\n  *** {girl['name']} is now engaged to you! Affection cap raised to 200. ***")
            input("\nPress Enter...")
            continue

        elif choice == str(5 + (1 if can_propose else 0)):
            if can_ascend:
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
                        print("You do not have enough Ascension Stones.")
                        input("Press Enter...")
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
                print("\n" + pre_line)
                input("\nPress Enter to begin the ceremony...")

                girl["level_cap"] = old_cap + 10

                # Dialogue 2: The ascension itself (from monster_girls.yaml)
                post_line = dialogue.get("ascension_post_ceremony",
                    f"The {highest_stone['name'] if highest_stone else 'stone'} shatters into motes of prismatic light!\nAncient power surges through {girl['name']}.\nHer form shimmers, breaking the seal of Level {old_cap}.")
                post_line = post_line.format(name=girl['name'], stone=highest_stone['name'] if highest_stone else 'stone', old_cap=old_cap)
                print(f"\n{'='*50}")
                print("  " + post_line.replace("\n", "\n  "))
                print(f"  Stones consumed: {stone_summary}")
                print(f"  *** LEVEL CAP INCREASED: {old_cap} → {girl['level_cap']} ***")
                print(f"{'='*50}")

                print(f"\n{girl['name']} opens her eyes, renewed and stronger.")
                print("'I can feel it... the path ahead is open once more.'")
                input("\nPress Enter...")
            elif where == "lounge":
                # ── RECRUIT ──
                aff = girl.get("affection", 30)
                if aff < RECRUIT_AFFECTION_THRESHOLD:
                    denied_msg = dialogue.get("recruit_denied",
                        f"{girl['name']} looks at you uncertainly. 'I don't know you well enough yet...'")
                    print(denied_msg.format(name=girl['name']))
                    print(f"  (Need {RECRUIT_AFFECTION_THRESHOLD}+ affection. Currently: {aff}/{aff_cap})")
                    input("\nPress Enter...")
                else:
                    accepted_msg = dialogue.get("recruit_accepted",
                        f"{girl['name']} smiles warmly. 'I'll fight beside you!'")
                    print(accepted_msg.format(name=girl['name']))
                    from combat.ally import recruit_ally_from_house
                    ally, msg = recruit_ally_from_house(player, girl, house)
                    print(msg)
                    if ally:
                        print(f"{ally['name']}'s stats:")
                        print(f"  HP: {ally['max_hp']}")
                        print(f"  STR: {ally['attributes']['Strength']}  CON: {ally['attributes']['Constitution']}  DEX: {ally['attributes']['Dexterity']}")
                    input("\nPress Enter...")
                    break  # after recruitment, return to girl list
            else:
                print("Invalid option.")
                input("Press Enter...")

        elif choice == str(6 + (1 if can_propose else 0)) and can_ascend and where == "lounge":
            # ── RECRUIT (when Ascend pushes number to 6/7) ──
            aff = girl.get("affection", 30)
            if aff < RECRUIT_AFFECTION_THRESHOLD:
                denied_msg = dialogue.get("recruit_denied",
                    f"{girl['name']} looks at you uncertainly. 'I don't know you well enough yet...'")
                print(denied_msg.format(name=girl['name']))
                print(f"  (Need {RECRUIT_AFFECTION_THRESHOLD}+ affection. Currently: {aff}/{aff_cap})")
                input("\nPress Enter...")
            else:
                accepted_msg = dialogue.get("recruit_accepted",
                    f"{girl['name']} smiles warmly. 'I'll fight beside you!'")
                print(accepted_msg.format(name=girl['name']))
                from combat.ally import recruit_ally_from_house
                ally, msg = recruit_ally_from_house(player, girl, house)
                print(msg)
                if ally:
                    print(f"{ally['name']}'s stats:")
                    print(f"  HP: {ally['max_hp']}")
                    print(f"  STR: {ally['attributes']['Strength']}  CON: {ally['attributes']['Constitution']}  DEX: {ally['attributes']['Dexterity']}")
                input("\nPress Enter...")
                break  # after recruitment, return to girl list

        else:
            print("Invalid option.")
            input("Press Enter...")

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
        print("You don't own a house here.")
        input("\nPress Enter...")
        return

    while True:
        clear_screen()
        lvl_data = _house_level_data(house)
        pending  = _pending_income(player, city_id, house)

        print(f"=== Your {lvl_data['name']} ===")
        print(f"  Level    : {house['level']} — {lvl_data['name']}")
        print(f"  Storage  : {len(house['storage'])}/{lvl_data['storage_cap']} slots")
        print(f"  Pending  : {pending} gold")
        print(f"  Gold     : {player.get('gold', 0)}")
        print()
        print("1. Rest (free heal)")
        print("2. Storage chest")
        print("3. Collect income")
        print("4. Lounge")
        if house["level"] < 3:
            print("5. Upgrade house")
            print("6. Leave")
            leave_opt = "6"
            upgrade_opt = "5"
        else:
            print("5. Leave")
            leave_opt = "5"
            upgrade_opt = None

        choice = input("\nChoice: ").strip()

        if choice == "1":
            _house_rest(player, city_id, house)
        elif choice == "2":
            _house_storage(player, city_id, house)
        elif choice == "3":
            _house_collect_income(player, city_id, house)
        elif choice == "4":
            _house_lounge(player, city_id, house)
        elif upgrade_opt and choice == upgrade_opt:
            _house_upgrade(player, city_id, house)
        elif choice == leave_opt:
            break
        else:
            print("Invalid choice.")
            input("Press Enter...")