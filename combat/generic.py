# combat.py – generic turn‑based combat (no super boss mechanics)

import random
from resources.enemies import ENEMIES, ENEMY_RACES
from resources.races_classes import ATTRIBUTES
from inventory import use_consumable, get_total_equipment_mods
from utils import get_difficulty_multiplier_from_time, clear_screen
from character import player_max_hp
from combat.status_effects import (
    apply_poison, apply_curse,
    apply_weaken, apply_bleed, apply_silence, apply_drain, apply_dread,
    tick_enemy_debuffs, tick_player_debuffs, tick_player_buffs,
    cure_curse,
    get_weaken_penalty, is_silenced, is_dreaded,
    format_player_status_line,
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

def get_effective_attribute(player, attr_name):
    """Return effective attribute value after applying curse penalty.
    Works for Strength, Constitution, Dexterity, Charisma, Learning, Wisdom, etc.
    """
    base = player["attributes"].get(attr_name, 0)
    equip_mods = get_total_equipment_mods(player)
    total = base + equip_mods.get(attr_name, 0)
    
    for debuff in player.get("active_debuffs", []):
        if debuff.get("type") == "curse":
            penalty = debuff.get("penalty", 2)
            total -= penalty

    if attr_name == "Strength":
        total -= get_weaken_penalty(player)
    
    for buff in player.get("active_buffs", []):
        if buff.get("type") == "blessing" or buff.get("stat") == "all":
            total += buff.get("value", 0)
        elif buff.get("stat") == attr_name:
            total += buff.get("value", 0)
    
    return total

def player_str_mod(player):
    return player["attributes"]["Strength"]


def player_con_mod(player):
    return player["attributes"]["Constitution"]


def player_dex_mod(player):
    return player["attributes"]["Dexterity"]


def compute_player_stats(player):
    p_str = get_effective_attribute(player, "Strength")
    p_con = get_effective_attribute(player, "Constitution")
    p_dex = get_effective_attribute(player, "Dexterity")
    if player.get("training_buff"):
        p_str += player["training_buff"].get("strength", 0)
    return p_str, p_con, p_dex


def format_enemy_status_line(enemy, extra=""):
    statuses = []
    if enemy.get("slowed"):
        statuses.append("Slowed")
    if enemy.get("stunned"):
        statuses.append("Stunned")
    if enemy.get("blinded"):
        statuses.append("Blinded")
    if enemy.get("frozen"):
        statuses.append("Frozen")
    if any(d["type"] == "burn" for d in enemy.get("active_debuffs", [])):
        statuses.append("Burning")
    if enemy.get("expose_stacks", 0) > 0:
        statuses.append(f"Exposed×{enemy['expose_stacks']}")
    status_str = f" ({', '.join(statuses)})" if statuses else ""
    return f"{enemy['name']} - HP: {enemy['hp']}{status_str}{extra}"


def prune_dead(enemies):
    return [e for e in enemies if e["hp"] > 0]

def print_superboss_header(player, floor, boss_name, extra_gimmick_line=""):
    from utils import format_time
    time_str = format_time(player.get("time_minutes", 0))
    print(f"Dungeon Floor {floor} - Superboss: {boss_name} | Time: {time_str}")
    if extra_gimmick_line:
        print(extra_gimmick_line)
    status_line = format_player_status_line(player)
    tempo_str = " [Abyssal Tempo]" if player.get("abyss_triple_actions", 0) > 0 else ""
    print(f"\nYour HP: {player['current_hp']} {status_line}{tempo_str}".rstrip())

def enemy_attack(enemy, player, p_con, defending, extra_logic=None, armor_mult=1.0, temp_str_bonus=0):
    msgs, died = tick_enemy_debuffs(enemy)
    for m in msgs:
        print(m)
    if died:
        return "died"

    if enemy.get("stunned"):
        print(f"The {enemy['name']} is stunned and cannot act!")
        enemy["stunned"] = False
        return "stunned"

    if enemy.get("frozen"):
        print(f"The {enemy['name']} is frozen solid and cannot act!")
        return "stunned"

    block = p_con + (5 if defending else 0)
    block = int(block * armor_mult)
    
    enemy_dmg = random.randint(2, 7) + enemy["str_mod"] + temp_str_bonus - block
    enemy_dmg = max(0, enemy_dmg)
    
    player["current_hp"] -= enemy_dmg

    if enemy_dmg > 0:
        print(f"The {enemy['name']} hits you for {enemy_dmg} damage!")
    else:
        print(f"The {enemy['name']} attacks but you block all incoming damage!")

    if extra_logic:
        msg = extra_logic(enemy, player, enemy_dmg)
        if msg:
            print(msg)

    if player["current_hp"] <= 0:
        return "dead"
    return "hit"


def superboss_combat_loop(player, enemies, floor, boss_name, context,
                          pre_player_hook=None,
                          custom_hud_hook=None,
                          on_kill_hook=None,
                          player_action_override=None,
                          enemy_turn_hook=None,
                          post_round_hook=None):
    while True:
        if player.get("abyss_tempo_pending", 0) > 0:
            pending = player.pop("abyss_tempo_pending")
            player["abyss_triple_actions"] = pending
            print(f"⚔️  The Abyss awakens! Triple actions for {pending} turns!")
        enemies[:] = [e for e in enemies if e["hp"] > 0]
        if not enemies:
            return "victory"

        p_str, p_con, p_dex = compute_player_stats(player)

        if pre_player_hook:
            result = pre_player_hook(context, enemies)
            if result in ("dead", "victory"): return result

        if context.get("skip_player_turn"):
            context["skip_player_turn"] = False
            continue
        if custom_hud_hook:
            custom_hud_hook(context, enemies)
        else:
            clear_screen()
            print_superboss_header(player, floor, boss_name, "")
            print("\nEnemies:")
            for idx, e in enumerate(enemies):
                print(f"  [{idx + 1}] {format_enemy_status_line(e)}")
            print("[A]ttack  [D]efend  [F]lee  [U]se item")

        action = player_action_override(context) if player_action_override else input("Choose: ").strip().lower()

        result, defending = handle_player_turn(
            player, enemies, p_str, p_con, p_dex,
            on_kill=lambda target, elist: on_kill_hook(target, elist, context) if on_kill_hook else None,
            _action_override=action
        )

        if result == "retry":
            continue
        if result in ("fled", "victory", "dead"):
            return result

        def _hud_func():
            clear_screen()
            print_superboss_header(player, floor, boss_name, "")
            print("\nEnemies:")
            for idx, e in enumerate([e for e in enemies if e["hp"] > 0]):
                print(f"  [{idx + 1}] {format_enemy_status_line(e)}")
            print("[A]ttack  [D]efend  [F]lee  [U]se item")

        triple_result = superboss_triple_action_loop(
            player, enemies, p_str, p_con, p_dex,
            on_kill=lambda target, elist: on_kill_hook(target, elist, context) if on_kill_hook else None,
            print_hud_func=_hud_func
        )
        if triple_result is not None:
            return triple_result

        enemies[:] = [e for e in enemies if e["hp"] > 0]
        for enemy in enemies[:]:
            if enemy["hp"] <= 0: continue
            
            actions = 1
            skip_attack = False
            extra_logic = None
            armor_mult = 1.0
            temp_str = 0

            if enemy_turn_hook:
                hook_res = enemy_turn_hook(enemy, context, player, p_con, defending)
                if hook_res == "dead": return "dead"
                if hook_res:
                    actions, skip_attack, extra_logic, armor_mult, temp_str = hook_res

            if not skip_attack:
                for action_idx in range(actions):
                    if actions > 1:
                        print(f"\n⚡ FAST ACTION! {enemy['name']} unleashes Action {action_idx + 1}/{actions}!")
                    
                    outcome = enemy_attack(enemy, player, p_con, defending, 
                                           extra_logic=extra_logic, 
                                           armor_mult=armor_mult, 
                                           temp_str_bonus=temp_str)
                    if outcome == "dead":
                        print("You have been slain.")
                        return "dead"

        if post_round_hook:
            if post_round_hook(context, enemies) == "dead": return "dead"

        enemies[:] = [e for e in enemies if e["hp"] > 0]
        if not enemies:
            return "victory"

        if player.get("abyss_fang_cooldown", 0) > 0:
            player["abyss_fang_cooldown"] -= 1
            if player["abyss_fang_cooldown"] == 0:
                print("⚔️  The Abyss Fang hums — its hunger is renewed.")
        if player.get("abyss_triple_actions", 0) > 0:
            player["abyss_triple_actions"] -= 1
            if player["abyss_triple_actions"] == 0:
                print("⚔️  Nightmare Tempo fades. The triple-action fury ends.")

        msgs, died = tick_player_debuffs(player)
        for m in msgs: print(m)
        if died:
            print("You have been slain.")
            return "dead"

        for m in tick_player_buffs(player): print(m)

        print("\n" + "-" * 50)
        input("Press Enter to continue...")


def _player_has_abyss_fang(player):
    equipment = player.get("equipped", {})
    if isinstance(equipment, dict):
        weapon = equipment.get("weapon")
        if weapon and weapon.get("special") == "dream_devour":
            return weapon
        
    return None


def handle_player_turn(player, enemies, p_str, p_con, p_dex, on_kill=None, _action_override=None):
    if _action_override is None:
        status_str = format_player_status_line(player)
        tempo_str = " [Abyssal Tempo]" if player.get("abyss_triple_actions", 0) > 0 else ""
        print(f"\nYour HP: {player['current_hp']} {status_str}{tempo_str}".rstrip())
        print("Enemies in the room:")
        for idx, e in enumerate(enemies):
            print(f"  [{idx + 1}] {format_enemy_status_line(e)}")
        abyss_fang = _player_has_abyss_fang(player)
        abyss_cd = player.get("abyss_fang_cooldown", 0)
        if abyss_fang and abyss_cd <= 0:
            print("[A]ttack  [D]efend  [F]lee  [U]se item  [W]ield the Abyss")
        elif abyss_fang and abyss_cd > 0:
            print(f"[A]ttack  [D]efend  [F]lee  [U]se item  (Abyss Fang recharging: {abyss_cd} turn(s))")
        else:
            print("[A]ttack  [D]efend  [F]lee  [U]se item")
        action = input("Choose: ").strip().lower()
    else:
        action = _action_override

    # ----- ATTACK ----- (Modified to scale based on weapon attribute rule)
    if action == "a":
        if is_dreaded(player) and random.random() < 0.40:
            print("Dread grips your weapon arm — your strike goes wide! (Miss)")
            return "continue", False
        if player.get("blinded") and random.random() < 0.25:
            print("You're blinded – your attack misses!")
            return "continue", False
    
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

        # Calculate dynamic weapon attribute scaling
        equipped_weapon = player.get("equipped", {}).get("weapon")
        scaling_stat = equipped_weapon.get("scaling_stat", "Strength") if equipped_weapon else "Strength"
        
        if scaling_stat == "Strength":
            scaling_val = p_str
        elif scaling_stat == "Dexterity":
            scaling_val = p_dex
        else:
            scaling_val = get_effective_attribute(player, scaling_stat)

        dmg = random.randint(4, 10) + scaling_val - target["con_mod"]
        dmg = max(0, dmg)
        target["hp"] -= dmg
        
        # dynamic flavor verbs based on scaling stat
        verb = "strike"
        if scaling_stat == "Dexterity":
            verb = "shoot" if "bow" in equipped_weapon.get("id", "") else "pierce"
        elif scaling_stat == "Learning":
            verb = "blast"

        print(f"You {verb} {target['name']} for {dmg} damage!")
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
        if is_silenced(player):
            print("You are silenced! Your hands cannot reach your pack.")
            return "retry", False
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
            if item.get("cure_poison"):
                before = len([d for d in player.get("active_debuffs", []) if d["type"] == "poison"])
                player["active_debuffs"] = [d for d in player.get("active_debuffs", []) if d["type"] != "poison"]
                after = len([d for d in player.get("active_debuffs", []) if d["type"] == "poison"])
                if before > after:
                    msg += "The poison is cleansed from your body. "
                else:
                    msg += "You are not poisoned. "
            if "base_power" in item and "damage_over_time" not in item and "stun_chance" not in item:
                dmg = item["base_power"]
                armor = target["con_mod"]
                if "armor_pierce" in item:
                    armor = max(0, armor - item["armor_pierce"])
                    msg += f"(ignores {item['armor_pierce']} armor) "
                final_dmg = max(1, dmg - armor)
                target["hp"] -= final_dmg
                msg += f"You deal {final_dmg} damage to the {target['name']}! "
            if "poison_damage" in item:
                from combat.status_effects import apply_poison
                apply_poison(target, item["poison_damage"], item.get("poison_duration", 3))
                msg += f"The {target['name']} is poisoned! "
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

    # ----- WIELD THE ABYSS -----
    elif action == "w":
        abyss_fang = _player_has_abyss_fang(player)
        if not abyss_fang:
            print("You have no weapon that responds to that command.")
            return "retry", False
        abyss_cd = player.get("abyss_fang_cooldown", 0)
        if abyss_cd > 0:
            print(f"The Abyss Fang is still recharging. ({abyss_cd} turn(s) remaining)")
            return "retry", False

        print("\n" + "≈" * 55)
        print("The Abyss Fang SCREAMS. A void tears open across your")
        print("vision — stolen faces from the Slitcurrent's body flash")
        print("across the blade, mouthing silent warnings. You grip it")
        print("anyway. Reality peels back. You are the wound now.")
        print("≈" * 55)
        input("Press Enter to unleash it...")

        max_hp = player_max_hp(player)
        hp_cost = int(max_hp * 0.40)
        player["current_hp"] = max(1, player["current_hp"] - hp_cost)
        print(f"\nThe blade drinks deep — you lose {hp_cost} HP ({player['current_hp']}/{max_hp} remaining).")

        str_bonus = 8
        player.setdefault("active_buffs", []).append({
            "stat": "Strength",
            "value": str_bonus,
            "remaining": 4,
            "source": "abyss_fang",
        })
        print(f"⚔️  Abyss-Tempered: Strength +{str_bonus} for 4 turns!")

        player["abyss_tempo_pending"] = 4
        print("⚔️  The Abyss stirs... its full fury will awaken next round!")

        player["abyss_fang_cooldown"] = 6
        print("(The blade will recharge in 6 turns.)\n")

        return "continue", False

    # ----- FLEE -----
    elif action == "f":
        effective_player_dex = p_dex
        for debuff in player.get("active_debuffs", []):
            if debuff["type"] == "slow":
                effective_player_dex -= 3

            if player.get("blinded"):
                effective_player_dex -= 2
                print("Your blindness makes escape harder!")
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
        if is_dreaded(player):
            difficulty += 4
        if roll >= difficulty:
            return "fled", False
        else:
            print("You fail to escape and expose yourself!")
            return "continue", False

    return "retry", False

def superboss_triple_action_loop(player, enemies, p_str, p_con, p_dex, on_kill, print_hud_func):
    triple_remaining = player.get("abyss_triple_actions", 0)
    if triple_remaining <= 0:
        return None

    for extra_num in range(2):
        enemies[:] = [e for e in enemies if e["hp"] > 0]
        if not enemies:
            return "victory"

        print(f"\n⚔️  ABYSS TEMPO — extra action ({extra_num + 2}/3)!")
        print_hud_func()

        action = input("Choose: ").strip().lower()
        result, _ = handle_player_turn(
            player, enemies, p_str, p_con, p_dex,
            on_kill=on_kill,
            _action_override=action,
        )
        if result in ("fled", "victory", "dead"):
            return result

    return None


def get_race_extra_logic(enemy):
    race = ENEMIES[enemy["key"]]["race"]

    if race == "Beast":
        def beast_bleed(e, player, dmg):
            if dmg > 0 and random.random() < 0.35:
                bleed_dmg = max(2, dmg // 3)
                result = apply_bleed(player, damage=bleed_dmg, duration=4)
                if result == "applied":
                    return f"The {e['name']}'s claws open a wound! You bleed for {bleed_dmg}/round."
                elif result == "refreshed":
                    return f"The {e['name']} tears your wound wider! ({bleed_dmg}/round)"
            return None
        return beast_bleed

    if race == "Undead":
        def undead_curse(e, player, dmg):
            if dmg > 0 and random.random() < 0.20:
                result = apply_curse(player)
                if result == "applied":
                    return f"The {e['name']}'s touch carries a dark curse! All attributes reduced."
                elif result == "already_cursed":
                    return f"The {e['name']}'s curse washes over you, but you are already afflicted."
            return None
        return undead_curse

    if race == "Shadow":
        def shadow_dread(e, player, dmg):
            if dmg > 0 and random.random() < 0.30:
                result = apply_dread(player, duration=2)
                if result == "applied":
                    return f"The {e['name']}'s darkness fills you with supernatural dread!"
            return None
        return shadow_dread

    if race == "Demon":
        def demon_weaken(e, player, dmg):
            if dmg > 0 and random.random() < 0.25:
                result = apply_weaken(player, str_penalty=2, duration=3)
                if result == "applied":
                    return f"The {e['name']}'s hellfire saps your strength! STR reduced for 3 turns."
                elif result == "refreshed":
                    return f"Your weakness deepens under the {e['name']}'s assault!"
            return None
        return demon_weaken

    if race == "Vampire":
        def vampire_drain(e, player, dmg):
            if dmg > 0:
                drained = apply_drain(player, e, drain_amount=max(1, dmg // 2))
                if drained > 0:
                    return f"The {e['name']} drains {drained} HP from your life force!"
            return None
        return vampire_drain

    if race == "Fey":
        def fey_silence(e, player, dmg):
            if dmg > 0 and random.random() < 0.25:
                result = apply_silence(player, duration=2)
                if result == "applied":
                    return f"The {e['name']}'s enchantment seals your pack shut for 2 turns!"
            return None
        return fey_silence

    if race == "Abomination":
        def abomination_weaken(e, player, dmg):
            if dmg > 0 and random.random() < 0.35:
                result = apply_weaken(player, str_penalty=3, duration=3)
                if result == "applied":
                    return f"The {e['name']}'s corrosive flesh weakens your muscles! STR -3 for 3 turns."
                elif result == "refreshed":
                    return f"The corruption deepens — your strength ebbs further!"
            return None
        return abomination_weaken

    if race == "Giant":
        def giant_weaken(e, player, dmg):
            if dmg > 0 and random.random() < 0.30:
                result = apply_weaken(player, str_penalty=4, duration=2)
                if result == "applied":
                    return f"The {e['name']}'s crushing blow leaves your arms numb! STR -4 for 2 turns."
                elif result == "refreshed":
                    return f"Another bone-crushing hit — your strength fails!"
            return None
        return giant_weaken

    if race == "Gnome":
        def gnome_silence(e, player, dmg):
            if dmg > 0 and random.random() < 0.20:
                result = apply_silence(player, duration=2)
                if result == "applied":
                    return f"The {e['name']}'s arcane static disrupts your concentration!"
            return None
        return gnome_silence
    
    if race == "Elemental":
        def elemental_blind(e, player, dmg):
            if dmg > 0 and random.random() < 0.30:
                from combat.status_effects import apply_blind
                result = apply_blind(player, duration=2)
                if result == "applied":
                    return f"A burst of searing light from the {e['name']} blinds you!"
                elif result == "refreshed":
                    return f"The {e['name']}'s radiance deepens your blindness!"
            return None
        return elemental_blind

    return None


def combat(player, enemy_keys, floor=None, room_num=None, total_rooms=None):
    player["abyss_triple_actions"] = 0

    enemies = [enemy_stats(k, player) for k in enemy_keys]
    print("\nEnemies approach!")
    for e in enemies:
        print(f"- A {e['name']} appears! (HP: {e['hp']})")

    while True:
        if floor is not None and room_num is not None and total_rooms is not None:
            from utils import format_time
            header = f"Dungeon Floor {floor} - Room {room_num}/{total_rooms} | Time: {format_time(player.get('time_minutes', 0))}"
            print(header)

        if player.get("abyss_tempo_pending", 0) > 0:
            pending = player.pop("abyss_tempo_pending")
            player["abyss_triple_actions"] = pending
            print(f"⚔️  The Abyss awakens! Triple actions for {pending} turns!")

        p_str, p_con, p_dex = compute_player_stats(player)
        enemies = prune_dead(enemies)
        if not enemies:
            print("All enemies have been defeated!")
            player["abyss_triple_actions"] = 0
            return "victory"

        result, defending = handle_player_turn(player, enemies, p_str, p_con, p_dex)
        if result == "retry":
            continue
        if result in ("fled", "victory", "dead"):
            player["abyss_triple_actions"] = 0
            player["abyss_tempo_pending"] = 0
            return result

        triple_remaining = player.get("abyss_triple_actions", 0)
        if triple_remaining > 0:
            for extra_num in range(1, 3):
                enemies = prune_dead(enemies)
                if not enemies:
                    break
                print(f"\n⚔️  ABYSS TEMPO — Extra Action {extra_num + 1}/3!")
                sub_result, _ = handle_player_turn(
                    player, enemies, p_str, p_con, p_dex,
                    on_kill=None, _action_override=None
                )
                if sub_result in ("fled", "victory", "dead"):
                    player["abyss_triple_actions"] = 0
                    player["abyss_tempo_pending"] = 0
                    return sub_result

        for enemy in enemies[:]:
            if enemy["hp"] <= 0:
                continue
            extra = get_race_extra_logic(enemy)
            outcome = enemy_attack(enemy, player, p_con, defending, extra_logic=extra)
            if outcome == "dead":
                print("You have been slain.")
                player["abyss_triple_actions"] = 0
                return "dead"

        input("\nPress Enter to continue...")
        clear_screen()

        enemies = prune_dead(enemies)
        if not enemies:
            print("All enemies have been defeated!")
            return "victory"

        if player.get("abyss_fang_cooldown", 0) > 0:
            player["abyss_fang_cooldown"] -= 1
            if player["abyss_fang_cooldown"] == 0:
                print("⚔️  The Abyss Fang hums — its hunger is renewed.")
        if player.get("abyss_triple_actions", 0) > 0:
            player["abyss_triple_actions"] -= 1
            if player["abyss_triple_actions"] == 0:
                print("⚔️  Nightmare Tempo fades. The triple-action fury ends.")

        msgs, died = tick_player_debuffs(player)
        for m in msgs:
            print(m)
        if died:
            print("You have been slain.")
            player["abyss_triple_actions"] = 0
            return "dead"

        for m in tick_player_buffs(player):
            print(m)