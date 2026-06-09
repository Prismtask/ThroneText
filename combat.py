# combat.py – generic turn‑based combat (no super boss mechanics)

import random
from resources.enemies import ENEMIES, ENEMY_RACES
from resources.races_classes import ATTRIBUTES
from inventory import use_consumable, get_total_equipment_mods
from utils import get_difficulty_multiplier_from_time
from character import player_max_hp
from status_effects import (
    apply_poison, apply_curse,
    tick_enemy_debuffs, tick_player_debuffs, tick_player_buffs,
    cure_curse,
)


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
    template = ENEMIES[enemy_key]
    attrs = compute_enemy_attributes(enemy_key)
    
    multiplier = get_difficulty_multiplier_from_time(player) if player else 1.0
    
    base_hp = template["base_hp"]
    str_mod = attrs["Strength"]
    con_mod = attrs["Constitution"]
    dex_mod = attrs["Dexterity"]

    scaled_hp = int(base_hp * multiplier)
    scaled_str = int(str_mod * (1 + (multiplier - 1) * 0.7))
    scaled_con = int(con_mod * (1 + (multiplier - 1) * 0.6))
    scaled_dex = int(dex_mod * (1 + (multiplier - 1) * 0.5))

    return {
        "key": enemy_key,
        "name": template["name"],
        "hp": scaled_hp,
        "max_hp": scaled_hp,
        "str_mod": scaled_str,
        "con_mod": scaled_con,
        "dex_mod": scaled_dex,
        "level": template["level"],
        "multiplier": round(multiplier, 2)
    }


def player_str_mod(player):
    return player["attributes"]["Strength"]


def player_con_mod(player):
    return player["attributes"]["Constitution"]


def player_dex_mod(player):
    return player["attributes"]["Dexterity"]


def compute_player_stats(player):
    """Compute effective p_str/p_con/p_dex from base attributes, equipment, buffs, and debuffs."""
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
        if buff.get("stat") == "all" or buff.get("type") == "blessing":
            p_str += buff["value"]
            p_con += buff["value"]
            p_dex += buff["value"]
        else:
            if buff.get("stat") == "Strength":
                p_str += buff["value"]
            elif buff.get("stat") == "Constitution":
                p_con += buff["value"]
            elif buff.get("stat") == "Dexterity":
                p_dex += buff["value"]

    return p_str, p_con, p_dex


def handle_player_turn(player, enemies, p_str, p_con, p_dex, on_kill=None, _action_override=None):
    """
    Handle a single player turn: Attack, Defend, Use item, or Flee.

    Parameters
    ----------
    player   : player dict (mutated in place)
    enemies  : list of live enemy dicts (mutated in place)
    p_str/p_con/p_dex : effective player stats for this combat
    on_kill  : optional callable(target, enemies) called after a kill via [A]ttack.
               Lets superboss encounters hook in gimmick logic (e.g. floatsam stacks).
    _action_override : if the caller already read the action input (e.g. to render a
               custom HUD first), pass it here to skip the built-in prompt.

    Returns
    -------
    ('continue', defending)  – normal turn completed; defending=True if [D] was chosen
    ('fled',     False)      – player successfully fled or used an escape item
    ('victory',  False)      – all enemies dead after item use
    ('dead',     False)      – player died during item use
    ('retry',    False)      – invalid input; caller should re-prompt the same turn
    """
    if _action_override is None:
        print(f"\nYour HP: {player['current_hp']}")
        print("Enemies in the room:")
        for idx, e in enumerate(enemies):
            statuses = []
            if e.get("slowed"):
                statuses.append("Slowed")
            if e.get("stunned"):
                statuses.append("Stunned")
            if e.get("blinded"):
                statuses.append("Blinded")
            status_str = f" ({', '.join(statuses)})" if statuses else ""
            print(f"  [{idx + 1}] {e['name']} - HP: {e['hp']}{status_str}")

        print("[A]ttack  [D]efend  [F]lee  [U]se item")
        action = input("Choose: ").strip().lower()
    else:
        action = _action_override

    # ----- ATTACK -----
    if action == "a":
        if len(enemies) > 1:
            try:
                choice = int(input("Select target number: ")) - 1
                if choice < 0 or choice >= len(enemies):
                    print("Invalid target selection.")
                    return "retry", False
                target = enemies[choice]
            except ValueError:
                print("Please enter a valid number.")
                return "retry", False
        else:
            target = enemies[0]

        dmg = random.randint(4, 10) + p_str - target["con_mod"]
        dmg = max(0, dmg)
        target["hp"] -= dmg
        print(f"You strike {target['name']} for {dmg} damage!")
        if target["hp"] <= 0:
            print(f"You defeated {target['name']}!")
            if on_kill:
                on_kill(target, enemies)
        return "continue", False

    # ----- DEFEND -----
    elif action == "d":
        print("You brace for impact, raising your guard.")
        return "continue", True

    # ----- USE ITEM -----
    elif action == "u":
        combat_inventory = [
            (idx, item) for idx, item in enumerate(player.get("inventory", []))
            if item.get("type") in ["consumable", "utility"]
        ]
        if not combat_inventory:
            print("You have no items usable in combat.")
            return "retry", False

        print("\nYour Battle Inventory:")
        for display_idx, (_, itm) in enumerate(combat_inventory):
            print(f"{display_idx+1}. {itm['name']} ({itm['type']})")
        try:
            choice = int(input("Use which item? (0 to cancel): ")) - 1
            if choice < 0 or choice >= len(combat_inventory):
                return "retry", False
            true_idx, item = combat_inventory[choice]
            msg = ""
            target = None

            affects_enemy = any(k in item for k in ["status", "blind_enemy", "base_power", "damage_over_time", "stun_chance"])
            if affects_enemy:
                if len(enemies) > 1:
                    try:
                        t_choice = int(input(f"Select target for {item['name']}: ")) - 1
                        if t_choice < 0 or t_choice >= len(enemies):
                            print("Invalid target choice.")
                            return "retry", False
                        target = enemies[t_choice]
                    except ValueError:
                        print("Invalid input.")
                        return "retry", False
                else:
                    target = enemies[0]

            if "power" in item:
                old_hp = player["current_hp"]
                new_hp = min(old_hp + item["power"], player_max_hp(player))
                healed_amount = new_hp - old_hp
                player["current_hp"] = new_hp
                msg += f"You recover {healed_amount} HP. "
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
                result = cure_curse(player)
                if result == "cured":
                    msg += "The dark curse is lifted! "
                else:
                    msg += "You are not cursed. "
            if "base_power" in item and "damage_over_time" not in item and "stun_chance" not in item:
                dmg = item["base_power"]
                armor = target["con_mod"]
                if "armor_pierce" in item:
                    armor = max(0, armor - item["armor_pierce"])
                    msg += f"(ignores {item['armor_pierce']} armor) "
                final_dmg = max(1, dmg - armor)
                target["hp"] -= final_dmg
                msg += f"You deal {final_dmg} damage to the {target['name']}! "
            if "damage_over_time" in item:
                target.setdefault("active_debuffs", []).append({
                    "type": "dot",
                    "damage": item["damage_over_time"],
                    "remaining": item.get("duration", 3)
                })
                msg += f"The {target['name']} is poisoned/burning! "
            if "stun_chance" in item:
                if random.random() < item["stun_chance"]:
                    target["stunned"] = True
                    msg += f"The {target['name']} is stunned and loses its next turn! "
                else:
                    msg += "The stun attempt fails. "
            if item.get("status") == "slow":
                target["slowed"] = True
                msg += f"The {target['name']} is slowed. "
            if item.get("blind_enemy"):
                target["blinded"] = True
                target.setdefault("active_debuffs", []).append({
                    "type": "blind",
                    "remaining": 3
                })
                msg += f"The {target['name']} is blinded (reduced dexterity). "
            if "escape_bonus" in item:
                print(msg)
                player["inventory"].pop(true_idx)
                return "fled", False

            print(msg)
            player["inventory"].pop(true_idx)

            enemies[:] = [e for e in enemies if e["hp"] > 0]
            if not enemies:
                return "victory", False
            if player["current_hp"] <= 0:
                return "dead", False

        except (ValueError, IndexError):
            print("Invalid choice.")
            return "retry", False

        return "continue", False

    # ----- FLEE -----
    elif action == "f":
        effective_player_dex = p_dex
        for debuff in player.get("active_debuffs", []):
            if debuff["type"] == "slow":
                effective_player_dex -= 3

        max_enemy_dex = -999
        for e in enemies:
            eff_enemy_dex = e["dex_mod"]
            if e.get("slowed"):
                eff_enemy_dex -= 2
            if e.get("blinded"):
                eff_enemy_dex -= 3
            if eff_enemy_dex > max_enemy_dex:
                max_enemy_dex = eff_enemy_dex

        roll = random.randint(1, 20) + effective_player_dex
        difficulty = 10 + max_enemy_dex
        if roll >= difficulty:
            print("You successfully flee from battle!")
            return "fled", False
        else:
            print("You fail to escape and expose yourself!")
            return "continue", False

    return "retry", False


def combat(player, enemy_keys):
    """Generic turn‑based battle. Returns 'victory', 'fled', or 'dead'."""
    enemies = [enemy_stats(k, player) for k in enemy_keys]

    p_str, p_con, p_dex = compute_player_stats(player)

    print("\nEnemies approach!")
    for e in enemies:
        print(f"- A {e['name']} appears! (HP: {e['hp']})")

    while True:
        # Remove dead enemies
        enemies = [e for e in enemies if e["hp"] > 0]
        if not enemies:
            print("All enemies have been defeated!")
            return "victory"

        result, defending = handle_player_turn(player, enemies, p_str, p_con, p_dex)
        if result == "retry":
            continue
        if result in ("fled", "victory", "dead"):
            return result

        # ----- ENEMY TURN PHASE -----
        for enemy in enemies[:]:
            if enemy["hp"] <= 0:
                continue

            # Process enemy status effects (dot, blind) before acting
            msgs, died = tick_enemy_debuffs(enemy)
            for m in msgs:
                print(m)
            if died:
                continue

            if enemy.get("stunned"):
                print(f"The {enemy['name']} is stunned and cannot act!")
                enemy["stunned"] = False
            else:
                block = p_con + (5 if defending else 0)
                enemy_dmg = random.randint(2, 7) + enemy["str_mod"] - block
                enemy_dmg = max(0, enemy_dmg)
                player["current_hp"] -= enemy_dmg

                if enemy_dmg > 0:
                    print(f"The {enemy['name']} hits you for {enemy_dmg} damage!")
                else:
                    print(f"The {enemy['name']} attacks but you block all incoming damage!")

                if player["current_hp"] <= 0:
                    print("You have been slain.")
                    return "dead"

        # ----- END OF ROUND MAINTENANCE -----
        enemies = [e for e in enemies if e["hp"] > 0]
        if not enemies:
            print("All enemies have been defeated!")
            return "victory"

        # Player status effect ticks (poison, slow)
        msgs, died = tick_player_debuffs(player)
        for m in msgs:
            print(m)
        if died:
            print("You have been slain.")
            return "dead"

        # Player buff
        for m in tick_player_buffs(player):
            print(m)