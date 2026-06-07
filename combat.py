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

    for debuff in player.get("active_debuffs", []):
        if debuff["type"] == "slow":
            p_dex -= 3
        if debuff["type"] == "curse":
            p_str -= 2
            p_con -= 2
            p_dex -= 2

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
            dmg = random.randint(4, 10) + p_str - enemy["con_mod"]
            dmg = max(0, dmg)
            enemy["hp"] -= dmg
            print(f"You strike for {dmg} damage!")
            if enemy["hp"] <= 0:
                print(f"You defeated {enemy['name']}!")
                return "victory"
        elif action == "d":
            defending = True
            print("You brace for impact, raising your guard.")
        elif action == "u":
            combat_inventory = [
                (idx, item) for idx, item in enumerate(player.get("inventory", []))
                if item.get("type") in ["consumable", "utility"]
            ]
            if not combat_inventory:
                print("You have no items usable in combat.")
                continue

            print("\nYour Battle Inventory:")
            for display_idx, (_, itm) in enumerate(combat_inventory):
                print(f"{display_idx+1}. {itm['name']} ({itm['type']})")
            try:
                choice = int(input("Use which item? (0 to cancel): ")) - 1
                if choice < 0 or choice >= len(combat_inventory):
                    continue
                true_idx, item = combat_inventory[choice]
                msg = ""
                if "power" in item:
                    heal = item["power"]
                    player["current_hp"] = min(player["current_hp"] + heal, player.get("max_hp", 999))
                    msg += f"You recover {heal} HP. "
                if "heal_over_time" in item:
                    player.setdefault("active_buffs", []).append({
                        "type": "hot",
                        "value": item["heal_over_time"],
                        "remaining": item.get("duration", 3)
                    })
                    msg += f"You start regenerating {item['heal_over_time']} HP each turn. "
                if "temp_stat" in item:
                    stat = item["temp_stat"]
                    val = item.get("base_power", 3)
                    player.setdefault("active_buffs", []).append({
                        "stat": stat,
                        "value": val,
                        "remaining": item.get("duration", 4)
                    })
                    msg += f"Your {stat} increases by {val} for {item.get('duration',4)} turns. "
                if "defense_buff" in item:
                    player.setdefault("active_buffs", []).append({
                        "type": "defense",
                        "value": item["defense_buff"],
                        "remaining": item.get("duration", 3)
                    })
                    msg += f"Damage taken reduced by {item['defense_buff']} for {item.get('duration',3)} turns. "
                if item.get("cure_curse"):
                    if player.get("cursed", False):
                        player["cursed"] = False
                        if player.get("active_debuffs"):
                            player["active_debuffs"] = [d for d in player["active_debuffs"] if d.get("type") != "curse"]
                        msg += "The dark curse is lifted from your body! "
                    else:
                        msg += "You are not cursed. "
                if "base_power" in item and "damage_over_time" not in item and "stun_chance" not in item:
                    dmg = item["base_power"]
                    armor = enemy["con_mod"]
                    if "armor_pierce" in item:
                        armor = max(0, armor - item["armor_pierce"])
                        msg += f"(ignores {item['armor_pierce']} armor) "
                    final_dmg = max(1, dmg - armor)
                    enemy["hp"] -= final_dmg
                    msg += f"You deal {final_dmg} damage to the {enemy['name']}! "
                if "damage_over_time" in item:
                    enemy.setdefault("active_debuffs", []).append({
                        "type": "dot",
                        "damage": item["damage_over_time"],
                        "remaining": item.get("duration", 3)
                    })
                    msg += f"The {enemy['name']} is poisoned/burning! "
                if "stun_chance" in item:
                    if random.random() < item["stun_chance"]:
                        enemy["stunned"] = True
                        msg += f"The {enemy['name']} is stunned and loses its next turn! "
                    else:
                        msg += "The stun attempt fails. "
                if item.get("status") == "slow":
                    enemy_slowed = True
                    msg += "The enemy is slowed. "
                if item.get("blind_enemy"):
                    enemy["blinded"] = True
                    enemy.setdefault("active_debuffs", []).append({
                        "type": "blind",
                        "remaining": 3
                    })
                    msg += "The enemy is blinded (reduced dexterity). "
                if "escape_bonus" in item:
                    print(msg)
                    player["inventory"].pop(true_idx)
                    return "fled"

                print(msg)
                player["inventory"].pop(true_idx)

                if enemy["hp"] <= 0:
                    return "victory"
                if player["current_hp"] <= 0:
                    return "dead"

            except (ValueError, IndexError):
                print("Invalid choice.")
                continue
        elif action == "f":
            effective_player_dex = p_dex
            for debuff in player.get("active_debuffs", []):
                if debuff["type"] == "slow":
                    effective_player_dex -= 3
            effective_enemy_dex = enemy["dex_mod"]
            if enemy_slowed:
                effective_enemy_dex -= 2
            if enemy.get("blinded"):
                effective_enemy_dex -= 3
            roll = random.randint(1,20) + effective_player_dex
            difficulty = 10 + effective_enemy_dex
            if roll >= difficulty:
                print("You successfully flee from battle!")
                return "fled"
            else:
                print("You fail to escape and expose yourself!")

        # Enemy turn (only if enemy is still alive)
        if enemy["hp"] <= 0:
            continue

        # Check if enemy is stunned
        if enemy.get("stunned"):
            print(f"The {enemy['name']} is stunned and cannot act!")
            enemy["stunned"] = False
        else:
            # Calculate damage
            block = p_con + (5 if defending else 0)
            enemy_dmg = random.randint(2, 7) + enemy["str_mod"] - block
            enemy_dmg = max(0, enemy_dmg)
            player["current_hp"] -= enemy_dmg

            if enemy_dmg > 0:
                print(f"The {enemy['name']} hits you for {enemy_dmg} damage!")
            else:
                print(f"The {enemy['name']} attacks but you block all damage!")

            if player["current_hp"] <= 0:
                print("You have been slain.")
                return "dead"

            # Enemy applies debuff (poison/slow/curse) after attacking
            race = ENEMIES[enemy_key]["race"]
            debuff_chance = 0.3
            if race in ["Undead", "Demon", "Shadow", "Vampire"]:
                debuff_chance = 0.45
            if random.random() < debuff_chance:
                if race in ["Undead", "Shadow", "Vampire"]:
                    effect = random.choices(["poison", "slow", "curse"], weights=[30, 30, 40])[0]
                elif race in ["Demon", "Abomination"]:
                    effect = random.choices(["poison", "curse", "slow"], weights=[25, 50, 25])[0]
                elif race in ["Beast", "Lizardfolk"]:
                    effect = random.choices(["poison", "slow"], weights=[70, 30])[0]
                else:
                    effect = random.choice(["poison", "slow"])

                if effect == "poison":
                    dmg = random.randint(3, 7)
                    player.setdefault("active_debuffs", []).append({
                        "type": "poison",
                        "damage": dmg,
                        "remaining": 3
                    })
                    print(f"The {enemy['name']} poisons you! You will take {dmg} damage each turn for 3 turns.")
                elif effect == "slow":
                    player.setdefault("active_debuffs", []).append({
                        "type": "slow",
                        "remaining": 3
                    })
                    print(f"The {enemy['name']} slows you! Your dexterity is reduced for 3 turns.")
                elif effect == "curse":
                    if not player.get("cursed"):
                        player["cursed"] = True
                        player.setdefault("active_debuffs", []).append({
                            "type": "curse",
                            "remaining": -1
                        })
                        print(f"A dark curse falls upon you! It will not fade on its own. Visit a temple to remove it.")
                    else:
                        print("You are already cursed. The enemy's curse fails to take hold.")

        # Process active debuffs on player (poison, etc.) at end of turn
        if player.get("active_debuffs"):
            for debuff in player["active_debuffs"][:]:
                if debuff["type"] == "poison":
                    dmg = debuff["damage"]
                    player["current_hp"] -= dmg
                    print(f"You suffer {dmg} poison damage!")
                    debuff["remaining"] -= 1
                    if debuff["remaining"] <= 0:
                        player["active_debuffs"].remove(debuff)
                elif debuff["type"] == "slow":
                    debuff["remaining"] -= 1
                    if debuff["remaining"] <= 0:
                        player["active_debuffs"].remove(debuff)
                # curse has no auto-removal

        # Process active buffs on player
        if player.get("active_buffs"):
            for buff in player["active_buffs"][:]:
                buff["remaining"] -= 1
                if buff["remaining"] <= 0:
                    player["active_buffs"].remove(buff)
                    if "stat" in buff:
                        print(f"Your {buff['stat']} buff wears off.")