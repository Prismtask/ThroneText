from resources.races_classes import RACES, CLASSES, ATTRIBUTES, TOTAL_POINTS
from save_load import save_game, list_saves, get_next_free_slot
from utils import clear_screen
import random

def player_max_hp(player_or_attrs):
    """Improved HP formula."""
    if isinstance(player_or_attrs, dict) and "attributes" in player_or_attrs:
        attrs = player_or_attrs["attributes"]
        bonus = player_or_attrs.get("level_hp_bonus", 0)
    else:
        attrs = player_or_attrs
        bonus = 0
    return 15 + attrs["Constitution"] * 3 + bonus


def allocate_points(base_attributes):
    """Fixed point allocation - handles negative base values and 0 remaining points."""
    print(f"\nYou have {TOTAL_POINTS} points to distribute.")
    temp = base_attributes.copy()
    remaining = TOTAL_POINTS

    for attr in ATTRIBUTES:
        while True:
            print(f"Remaining points: {remaining}")
            val = input(f"{attr} (current {temp[attr]}): ").strip()

            if val == "" or val.lower() == "skip":
                # Allow skipping when no points left or to accept current value
                if remaining == 0 or temp[attr] >= 0:
                    print(f"{attr} remains at {temp[attr]}.")
                    break
                else:
                    print(f"You must bring {attr} to at least 0.")
                    continue

            try:
                pts = int(val)
                if pts < 0:
                    print("Points cannot be negative.")
                    continue
                if pts > remaining:
                    print(f"You only have {remaining} points left.")
                    continue

                new_val = temp[attr] + pts
                if new_val < 0:
                    print("Attribute cannot go below 0.")
                    continue

                temp[attr] = new_val
                remaining -= pts
                break
            except ValueError:
                print("Please enter an integer or press Enter to skip.")

    # Final check
    if remaining != 0:
        print(f"\nYou still have {remaining} points left. Let's try again.")
        return allocate_points(base_attributes)

    return temp


def create_character():
    """Full new‑game character creation."""
    clear_screen()
    print("=== New Game ===")

    # Race
    print("\nChoose your race:")
    for k, v in RACES.items():
        print(f"  {k}. {v['name']} - {v['desc']}")
    race_key = input("Enter number: ").strip()
    while race_key not in RACES:
        race_key = input("Invalid, choose again: ").strip()
    race_mods = RACES[race_key]["mods"]

    # Class
    print("\nChoose your class:")
    for k, v in CLASSES.items():
        print(f"  {k}. {v['name']} - {v['desc']}")
    class_key = input("Enter number: ").strip()
    while class_key not in CLASSES:
        class_key = input("Invalid, choose again: ").strip()
    class_mods = CLASSES[class_key]["mods"]

    # Base attributes
    base_attrs = {attr: 0 for attr in ATTRIBUTES}
    for attr, mod in race_mods.items():
        base_attrs[attr] += mod
    for attr, mod in class_mods.items():
        base_attrs[attr] += mod

    print("\nBase attributes after race & class:")
    for attr in ATTRIBUTES:
        print(f"{attr}: {base_attrs[attr]}")

    final_attrs = allocate_points(base_attrs)

    name = input("\nName your protagonist: ").strip()
    while not name:
        name = input("Name cannot be empty: ").strip()

    # Choose save slot
    print("\nSave slots available:")
    saves = list_saves()
    for slot, save_name in saves.items():        # ← changed
        print(f"  Slot {slot}: {save_name}")     # ← changed
    next_free = get_next_free_slot()
    print(f"  Slot {next_free}: (new)")
    
    while True:
        try:
            slot_str = input(f"Enter save slot number (new: {next_free}): ").strip()
            slot = int(slot_str) if slot_str else next_free
            if slot < 1:
                print("Slot must be a positive integer.")
                continue
            if slot in saves:
                overwrite = input(f"Slot {slot} already contains '{saves[slot]}'. Overwrite? (y/n): ").strip().lower()
                if overwrite != 'y':
                    continue
            break
        except ValueError:
            print("Please enter a number.")

    player = {
        "name": name,
        "race": RACES[race_key]["name"],
        "class": CLASSES[class_key]["name"],
        "attributes": final_attrs,
        # Per-city dungeon progress: { city_id: {"floor": N, "max_floor": N} }
        # "floor" = the floor the player will descend to next in that city's dungeon.
        # "max_floor" = the highest floor ever cleared (unlock ceiling for floor select).
        "city_floors": {
            "solmere": {"floor": 1, "max_floor": 1}
        },
        # "floor" is kept as a transient cursor while inside a dungeon run.
        # It is always synced back to city_floors on exit.
        "current_hp": player_max_hp(final_attrs),
        "level": 1,
        "exp": 0,
        "level_hp_bonus": 0,
        "inventory": [],
        "equipped": {"weapon": None, "armor": None, "accessory": None},
        "active_buffs": [],
        "save_slot": slot,
        "dungeon_time": 0,
        "gold": 100,
        "time_minutes": 8 * 60,  # Start at 08:00
        "location": "solmere",  # Start in first city
        "superboss_seed": random.randint(1, 999999)
    }

    save_game(player)
    print(f"\nCharacter '{name}' created and saved.")
    input("Press Enter to begin your dungeon adventure...")
    return player