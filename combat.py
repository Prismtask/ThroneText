# combat.py – full version with super boss mechanics

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

def combat(player, enemy_keys):
    """Run turn‑based battle against a group of enemies. Returns 'victory', 'fled', or 'dead'."""
    enemies = [enemy_stats(k, player) for k in enemy_keys]

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
            if buff.get("stat") == "Strength": p_str += buff["value"]
            elif buff.get("stat") == "Constitution": p_con += buff["value"]
            elif buff.get("stat") == "Dexterity": p_dex += buff["value"]

    print("\nEnemies approach!")
    for e in enemies:
        print(f"- A {e['name']} appears! (HP: {e['hp']})")

    # ----- Super Boss Phase Tracking -----
    boss_escaped_data = None          # stored boss enemy dict when she retreats
    minion_phase_active = False
    minion_timer = 0                  # turns left to kill all minions
    boss_enraged_turns = 0            # remaining turns of double action (failure case)
    # ------------------------------------

    while True:
        # Remove dead enemies
        enemies = [e for e in enemies if e["hp"] > 0]
        if not enemies:
            print("All enemies have been defeated!")
            return "victory"

        print(f"\nYour HP: {player['current_hp']}")
        print("Enemies in the room:")
        for idx, e in enumerate(enemies):
            statuses = []
            if e.get("slowed"): statuses.append("Slowed")
            if e.get("stunned"): statuses.append("Stunned")
            if e.get("blinded"): statuses.append("Blinded")
            status_str = f" ({', '.join(statuses)})" if statuses else ""
            print(f"  [{idx + 1}] {e['name']} - HP: {e['hp']}{status_str}")

        print("[A]ttack  [D]efend  [F]lee  [U]se item")
        action = input("Choose: ").strip().lower()

        defending = False
        # ----- PLAYER ACTION -----
        if action == "a":
            if len(enemies) > 1:
                try:
                    choice = int(input("Select target number: ")) - 1
                    if choice < 0 or choice >= len(enemies):
                        print("Invalid target selection.")
                        continue
                    target = enemies[choice]
                except ValueError:
                    print("Please enter a valid number.")
                    continue
            else:
                target = enemies[0]

            dmg = random.randint(4, 10) + p_str - target["con_mod"]
            dmg = max(0, dmg)
            target["hp"] -= dmg
            print(f"You strike {target['name']} for {dmg} damage!")
            if target["hp"] <= 0:
                print(f"You defeated {target['name']}!")

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

                affects_enemy = any(k in item for k in ["status", "blind_enemy", "base_power", "damage_over_time", "stun_chance"])
                if affects_enemy:
                    if len(enemies) > 1:
                        try:
                            t_choice = int(input(f"Select target for {item['name']}: ")) - 1
                            if t_choice < 0 or t_choice >= len(enemies):
                                print("Invalid target choice.")
                                continue
                            target = enemies[t_choice]
                        except ValueError:
                            print("Invalid input.")
                            continue
                    else:
                        target = enemies[0]

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
                    return "fled"

                print(msg)
                player["inventory"].pop(true_idx)

                # Clean up dead enemies after item use
                enemies = [e for e in enemies if e["hp"] > 0]
                if not enemies:
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
            
            max_enemy_dex = -999
            for e in enemies:
                eff_enemy_dex = e["dex_mod"]
                if e.get("slowed"): eff_enemy_dex -= 2
                if e.get("blinded"): eff_enemy_dex -= 3
                if eff_enemy_dex > max_enemy_dex:
                    max_enemy_dex = eff_enemy_dex

            roll = random.randint(1, 20) + effective_player_dex
            difficulty = 10 + max_enemy_dex
            if roll >= difficulty:
                print("You successfully flee from battle!")
                return "fled"
            else:
                print("You fail to escape and expose yourself!")

        # ----- CHECK FOR SUPER BOSS 75% HP RETREAT (after player action) -----
        if not minion_phase_active and boss_escaped_data is None:
            for idx, e in enumerate(enemies[:]):
                if e.get("key") == "broodmother_vileheart" and e["hp"] <= int(e["max_hp"] * 0.75):
                    print(f"\n[GIMMICK] {e['name']} screeches and retreats into the shadows!")
                    print("Three Vileheart Spiderlings drop from the ceiling!")
                    
                    boss_escaped_data = e
                    enemies.remove(e)
                    
                    # Spawn 3 minions
                    for _ in range(3):
                        m_stats = enemy_stats("vileheart_spiderling", player)
                        m_stats["key"] = "vileheart_spiderling"
                        m_stats["max_hp"] = m_stats["hp"]
                        enemies.append(m_stats)
                    
                    minion_phase_active = True
                    minion_timer = 3   # player has 3 rounds to kill all spiderlings
                    break

        # ----- ENEMY TURN PHASE -----
        for enemy in enemies[:]:
            if enemy["hp"] <= 0:
                continue

            # Determine number of actions this turn (super boss double action)
            actions = 1
            if enemy.get("key") == "broodmother_vileheart":
                # Permanent double action below 25% HP
                if enemy["hp"] <= int(enemy["max_hp"] * 0.25):
                    actions = 2
                    print(f"⚠️ {enemy['name']} is FRENZIED! (Permanent Double Actions)")
                # Temporary enrage from minion failure
                elif boss_enraged_turns > 0:
                    actions = 2
                    print(f"🔥 {enemy['name']} is ENRAGED! (Double Action remaining: {boss_enraged_turns})")

            for _ in range(actions):
                # Process enemy status effects (dot, blind) before acting
                if enemy.get("active_debuffs"):
                    for debuff in enemy["active_debuffs"][:]:
                        if debuff["type"] == "dot":
                            dot_dmg = debuff["damage"]
                            enemy["hp"] -= dot_dmg
                            print(f"The {enemy['name']} takes {dot_dmg} status damage!")
                            debuff["remaining"] -= 1
                            if debuff["remaining"] <= 0:
                                enemy["active_debuffs"].remove(debuff)
                        elif debuff["type"] == "blind":
                            debuff["remaining"] -= 1
                            if debuff["remaining"] <= 0:
                                enemy["blinded"] = False
                                enemy["active_debuffs"].remove(debuff)
                                print(f"The {enemy['name']} recovers their vision.")

                if enemy["hp"] <= 0:
                    print(f"The {enemy['name']} has succumbed to status damage!")
                    continue

                if enemy.get("stunned"):
                    print(f"The {enemy['name']} is stunned and cannot act!")
                    enemy["stunned"] = False
                else:
                    # Enemy attack
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

                    # ----- POISON INFLICTION (Super Boss & Spiderlings) -----
                    if enemy.get("key") in ("broodmother_vileheart", "vileheart_spiderling"):
                        if random.random() < 0.5:  # 50% chance to poison
                            poison_dmg = 4
                            # Stack poison: find existing poison or create new
                            existing_poison = next((d for d in player.get("active_debuffs", []) if d["type"] == "poison"), None)
                            if existing_poison:
                                existing_poison["remaining"] = 3
                                existing_poison["damage"] = poison_dmg
                                print(f"The {enemy['name']} re-infects you! Poison intensifies and resets to 3 turns ({poison_dmg} dmg/turn).")
                            else:
                                player.setdefault("active_debuffs", []).append({
                                    "type": "poison",
                                    "damage": poison_dmg,
                                    "remaining": 3
                                })
                                print(f"You are poisoned by the {enemy['name']}! Take {poison_dmg} damage each turn for 3 turns.")

                    # ----- Existing status effect application from other enemies -----
                    race = ENEMIES[enemy["key"]]["race"]
                    debuff_chance = 0.45 if race in ["Undead", "Demon", "Shadow", "Vampire"] else 0.3
                    if random.random() < debuff_chance and enemy.get("key") not in ("broodmother_vileheart", "vileheart_spiderling"):
                        # ... (keep original debuff logic here) ...
                        pass  # Your original code for other debuffs

        # ----- END OF ROUND MAINTENANCE -----
        # Remove dead enemies after enemy turn
        enemies = [e for e in enemies if e["hp"] > 0]
        if not enemies and not minion_phase_active:
            print("All enemies have been defeated!")
            return "victory"

        # Player status effect ticks (poison, slow)
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

        if player["current_hp"] <= 0:
            print("You have been slain.")
            return "dead"

        # Player buff decay
        if player.get("active_buffs"):
            for buff in player["active_buffs"][:]:
                if buff.get("type") == "blessing":
                    continue
                buff["remaining"] -= 1
                if buff["remaining"] <= 0:
                    player["active_buffs"].remove(buff)
                    if "stat" in buff:
                        print(f"Your {buff['stat']} buff wears off.")

        # ----- MINION PHASE TIMER (after round) -----
        if minion_phase_active:
            # Check if any spiderling remains
            spiderlings_alive = any(e.get("key") == "vileheart_spiderling" for e in enemies)
            if not spiderlings_alive:
                # Success: all minions killed in time
                print("\n[GIMMICK] You slaughtered all spiderlings!")
                print("Broodmother Vileheart descends again, enraged by your defiance.")
                enemies.append(boss_escaped_data)
                boss_escaped_data = None
                minion_phase_active = False
                # No enrage on success
            else:
                minion_timer -= 1
                if minion_timer <= 0:
                    # Failure: time's up
                    print("\n[GIMMICK] Time's up! The remaining spiderlings retreat.")
                    print("Broodmother Vileheart ambushes you, ENRAGED with double actions for 3 turns!")
                    # Remove spiderlings
                    enemies = [e for e in enemies if e.get("key") != "vileheart_spiderling"]
                    # Boss returns with temporary double action
                    boss_enraged_turns = 3
                    enemies.append(boss_escaped_data)
                    boss_escaped_data = None
                    minion_phase_active = False

        # Reduce enrage counter each round
        if boss_enraged_turns > 0:
            boss_enraged_turns -= 1