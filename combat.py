import random
from resources.enemies import ENEMIES, ENEMY_RACES
from resources.races_classes import ATTRIBUTES
from inventory import use_consumable, get_total_equipment_mods
from utils import get_difficulty_multiplier_from_time

def compute_enemy_attributes(enemy_key):
    template = ENEMIES[enemy_key]
    race_name = template["race"]
    race_mods = ENEMY_RACES[race_name].get("mods", {})
    personal_mods = template.get("mods", {})

    base = {attr: 0 for attr in ATTRIBUTES}
    for attr, mod in race_mods.items():
        base[attr] += mod
    for attr, mod in personal_mods.items():
        base[attr] += mod
    return base

def enemy_stats(enemy_key, player=None):
    """Now accepts dungeon_time for scaling."""
    template = ENEMIES[enemy_key]
    attrs = compute_enemy_attributes(enemy_key)
    
    multiplier = get_difficulty_multiplier_from_time(player) if player else 1.0
    
    base_hp = template["base_hp"]
    str_mod = attrs["Strength"]
    con_mod = attrs["Constitution"]
    dex_mod = attrs["Dexterity"]

    scaled_hp = int(base_hp * multiplier)
    scaled_str = int(str_mod * (1 + (multiplier - 1) * 0.7))  # Attack scales a bit slower
    scaled_con = int(con_mod * (1 + (multiplier - 1) * 0.6))
    scaled_dex = int(dex_mod * (1 + (multiplier - 1) * 0.5))

    return {
        "name": template["name"],
        "hp": scaled_hp,
        "str_mod": scaled_str,
        "con_mod": scaled_con,
        "dex_mod": scaled_dex,
        "level": template["level"],
        "multiplier": round(multiplier, 2)  # for debugging
    }


def player_str_mod(player):
    return player["attributes"]["Strength"]


def player_con_mod(player):
    return player["attributes"]["Constitution"]


def player_dex_mod(player):
    return player["attributes"]["Dexterity"]


def combat(player, enemy_key):
    """Run turn‑based battle. Returns 'victory', 'fled', or 'dead'."""
    enemy = enemy_stats(enemy_key, player)
    player_hp = player["current_hp"]   # backup

    enemy_slowed = False

    equip_mods = get_total_equipment_mods(player)
    p_str = player_str_mod(player) + equip_mods.get("Strength", 0)
    p_con = player_con_mod(player) + equip_mods.get("Constitution", 0)
    p_dex = player_dex_mod(player) + equip_mods.get("Dexterity", 0)

    for buff in player.get("active_buffs", []):
        if buff["stat"] == "Strength": p_str += buff["value"]
        elif buff["stat"] == "Constitution": p_con += buff["value"]
        elif buff["stat"] == "Dexterity": p_dex += buff["value"]

    print(f"\nA {enemy['name']} appears! (HP: {enemy['hp']})")

    while True:
        print(f"\nYour HP: {player['current_hp']}  |  {enemy['name']} HP: {enemy['hp']}")
        if enemy_slowed:
            print(f"(The {enemy['name']} is slowed!)")
        print("[A]ttack  [D]efend  [F]lee  [U]se item")
        action = input("Choose: ").strip().lower()

        defending = False
        if action == "a":
            # Improved player damage
            dmg = random.randint(4, 10) + p_str - enemy["con_mod"]   # ← BUFF
            dmg = max(0, dmg)
            enemy["hp"] -= dmg
            print(f"You strike for {dmg} damage!")
            if enemy["hp"] > 0:
                print(f"The {enemy['name']} has {enemy['hp']} HP remaining.")
            if enemy["hp"] <= 0:
                print(f"You defeated {enemy['name']}!")
                return "victory"
        elif action == "d":
            defending = True
            print("You brace for impact, raising your guard.")
        elif action == "u":
            # 1. Build a filtered list of only consumables and utilities, tracking original indices
            combat_inventory = [
                (original_idx, item) 
                for original_idx, item in enumerate(player.get("inventory", []))
                if item.get("type") in ["consumable", "utility"]
            ]

            if not combat_inventory:
                print("You have no items usable in combat.")
                continue

            print("\nYour Battle Inventory:")
            for display_idx, (original_idx, itm) in enumerate(combat_inventory):
                print(f"{display_idx + 1}. {itm['name']} ({itm['type']})")
            
            try:
                choice = int(input("Use which item? (0 to cancel): ")) - 1
                if choice < 0: 
                    continue
                
                # Validate selection against the displayed combat inventory bounds
                if choice >= len(combat_inventory):
                    print("Invalid choice.")
                    continue

                # 2. Extract the true inventory index and item details
                true_inventory_idx, item = combat_inventory[choice]
                
                combat_state = {
                    "player_hp": player["current_hp"],  # Fixed stale HP variable bug
                    "enemy_hp": enemy["hp"],
                    "enemy_race": ENEMIES[enemy_key]["race"],
                    "enemy_slowed": False,
                    "forced_flee": False
                }
                
                msg = use_consumable(player, item, combat_state)
                print(msg)
                
                # 3. Safely update enemy HP and remove the item using its true position
                enemy["hp"] = combat_state["enemy_hp"]
                player["inventory"].pop(true_inventory_idx)

                if combat_state.get("enemy_slowed"):
                    enemy_slowed = True
                    print("The enemy is slowed!")
                if combat_state.get("forced_flee"):
                    return "fled"
                if enemy["hp"] <= 0:
                    return "victory"
                if player["current_hp"] <= 0:
                    return "dead"
                    
            except (ValueError, IndexError):
                print("Invalid choice.")
                continue
        elif action == "f":
            effective_enemy_dex = enemy["dex_mod"] - (2 if enemy_slowed else 0)
            roll = random.randint(1, 20) + p_dex
            difficulty = 10 + effective_enemy_dex
            if roll >= difficulty:
                print("You successfully flee from battle!")
                return "fled"
            else:
                print("You fail to escape and expose yourself!")
        else:
            print("Invalid action. Turn wasted.")

        # Enemy attack
        if enemy["hp"] > 0:
            block = p_con + (5 if defending else 0)          # ← Improved defend
            enemy_dmg = random.randint(2, 7) + enemy["str_mod"] - block   # ← Slightly reduced
            enemy_dmg = max(0, enemy_dmg)
            player["current_hp"] -= enemy_dmg
            if enemy_dmg > 0:
                print(f"The {enemy['name']} hits you for {enemy_dmg} damage!")
            else:
                print(f"The {enemy['name']} attacks but you block all damage!")
            if player["current_hp"] <= 0:
                print("You have been slain.")
                return "dead"

        # Buff tick
        if player.get("active_buffs"):
            for buff in player["active_buffs"][:]:
                buff["remaining"] -= 1
                if buff["remaining"] <= 0:
                    player["active_buffs"].remove(buff)
                    print(f"Your {buff['stat']} buff wears off.")