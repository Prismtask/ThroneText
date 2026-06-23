from resources.races_classes import RACES, CLASSES, ATTRIBUTES, TOTAL_POINTS
from save_load import save_game, list_saves, get_next_free_slot
from utils import clear_screen
import random

def ensure_player_fields(player):
    """Ensure loaded saves have all required fields for new systems."""
    player.setdefault("skills", [])
    player.setdefault("skill_cooldowns", {})
    player.setdefault("skill_mastery", {})
    player.setdefault("passive_unlocked", True)
    player.setdefault("berserk_turns", 0)
    player.setdefault("bloodlust_turns", 0)
    from combat.skills import unlock_skills_for_level
    unlock_skills_for_level(player)

    # Ensure elemental fields for new saves
    if "elemental_res" not in player or "elemental_dmg" not in player:
        from combat.elemental import compute_player_elemental
        res, dmg = compute_player_elemental(player)
        player["elemental_res"] = res
        player["elemental_dmg"] = dmg

    # Ensure ally and house girl fields for leveling system
    for ally in player.get("allies", []):
        ally.setdefault("exp", 0)
        ally.setdefault("level_hp_bonus", 0)
        ally.setdefault("cursed", False)
        ally.setdefault("dreaded", False)
        ally.setdefault("silenced", False)
        if "elemental_res" not in ally or "elemental_dmg" not in ally:
            from combat.elemental import compute_ally_elemental
            res, dmg = compute_ally_elemental(ally)
            ally["elemental_res"] = res
            ally["elemental_dmg"] = dmg

    for house in player.get("houses", {}).values():
        for girl in house.get("monster_girls", []):
            girl.setdefault("exp", 0)
            girl.setdefault("level_hp_bonus", 0)


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

    from combat.elemental import neutral_profile, merge_profiles
    race_res = merge_profiles(neutral_profile(), RACES[race_key].get("elemental_res", {}))
    race_dmg = merge_profiles(neutral_profile(), RACES[race_key].get("elemental_dmg", {}))
    class_res = merge_profiles(neutral_profile(), CLASSES[class_key].get("elemental_res", {}))
    class_dmg = merge_profiles(neutral_profile(), CLASSES[class_key].get("elemental_dmg", {}))
    
    base_res = {}
    base_dmg = {}
    for el in ["fire", "water", "thunder", "wind", "earth", "light", "dark"]:
        base_res[el] = max(0.0, min(2.0, race_res[el] + class_res[el] - 1.0))
        base_dmg[el] = max(0.0, min(2.0, race_dmg[el] + class_dmg[el] - 1.0))

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
        "superboss_seed": random.randint(1, 999999),
        "allies": [],  # Active combat companions (max 3)
        "skills": [],
        "skill_cooldowns": {},
        "skill_mastery": {},
        "passive_unlocked": True,
        "elemental_res": base_res,
        "elemental_dmg": base_dmg,
    }

    save_game(player)
    print(f"\nCharacter '{name}' created and saved.")
    input("Press Enter to begin your dungeon adventure...")
    return player