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

# ── Constants ────────────────────────────────────────────────────────────────

HOUSE_LEVELS = {
    1: {"name": "Hovel",   "storage_cap": 10, "income_per_day": 8,  "rest_minutes": 90,  "upgrade_cost": 600,  "bed_buff_value": 1, "bed_buff_floors": 1},
    2: {"name": "Cottage", "storage_cap": 20, "income_per_day": 18, "rest_minutes": 70,  "upgrade_cost": 1500, "bed_buff_value": 2, "bed_buff_floors": 2},
    3: {"name": "Manor",   "storage_cap": 35, "income_per_day": 35, "rest_minutes": 50,  "upgrade_cost": None, "bed_buff_value": 3, "bed_buff_floors": 3},
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


def _house_storage(player, city_id, house):
    """Move items between inventory and house storage chest."""
    lvl_data = _house_level_data(house)
    cap      = lvl_data["storage_cap"]
    storage  = house["storage"]

    while True:
        clear_screen()
        inv     = player.get("inventory", [])
        print(f"=== House Storage ({len(storage)}/{cap} slots used) ===")

        print("\n-- Chest --")
        if storage:
            for i, itm in enumerate(storage):
                print(f"  {i+1}. {itm['name']} ({itm['type']})")
        else:
            print("  (empty)")

        print("\n-- Your Bag --")
        if inv:
            for i, itm in enumerate(inv):
                print(f"  {i+1}. {itm['name']} ({itm['type']})")
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
            try:
                idx = int(input("Deposit which item? (number): ")) - 1
                if 0 <= idx < len(inv):
                    item = inv.pop(idx)
                    storage.append(item)
                    print(f"Stored {item['name']} in your chest.")
                    input("Press Enter...")
            except (ValueError, IndexError):
                pass

        elif act == "w":
            if not storage:
                print("The chest is empty.")
                input("Press Enter...")
                continue
            try:
                idx = int(input("Withdraw which item? (number): ")) - 1
                if 0 <= idx < len(storage):
                    item = storage.pop(idx)
                    player.setdefault("inventory", []).append(item)
                    print(f"Took {item['name']} from the chest.")
                    input("Press Enter...")
            except (ValueError, IndexError):
                pass

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


def _house_lounge(player, city_id, house):
    """Lounge — reserved for the ally system. Placeholder."""
    print("╔══════════════════════════════╗")
    print("║         THE LOUNGE           ║")
    print("╠══════════════════════════════╣")
    print("║  [Coming soon]               ║")
    print("║                              ║")
    print("║  Once you have companions,   ║")
    print("║  they can gather here to     ║")
    print("║  plan, rest, and bond.       ║")
    print("╚══════════════════════════════╝")
    input("\nPress Enter...")


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
        print("4. Lounge  [Coming soon — Ally System]")
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