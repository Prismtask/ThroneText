import random
from character import player_max_hp
from combat.status_effects import cure_curse, apply_poison, is_silenced, is_dreaded, format_player_status_line
from combat.combat_ui import print_combat_hud, format_enemy_status_line
from combat.wedding_specials import (
    apply_wedding_attack_bonus_procs,
    apply_wedding_on_hit,
    apply_wedding_on_kill,
)
from combat.action_menu import get_action_menu
from combat.capture import is_monster_girl, attempt_capture
from combat.stat_milestones import get_strength_bonus, get_wisdom_bonus
from combat.skills import get_available_skills, execute_skill, set_skill_cooldown, format_mastery_label


def handle_player_turn(player, enemies, p_str, p_con, p_dex, p_ler, p_wis, p_cha, on_kill=None, on_hit=None, _action_override=None):
    if _action_override is None:
        # Normal player input
        print_combat_hud(player, enemies)
        menu_str, valid_actions = get_action_menu(player, enemies)
        action = input("Choose: ").strip().lower()
        while action not in valid_actions:
            print(f"Invalid choice. Available: {', '.join(valid_actions)}")
            action = input("Choose: ").strip().lower()
    else:
        # Override from superboss loop
        action = _action_override
        _, valid_actions = get_action_menu(player, enemies)
        if action not in valid_actions:
            print(f"Internal error: override action '{action}' is not available.")
            return "retry", False

    # ----- SKILLS (numbered 1-9) -----
    if action.isdigit():
        skill_idx = int(action) - 1
        available_skills = get_available_skills(player)
        if skill_idx < 0 or skill_idx >= len(available_skills):
            print("Invalid skill choice.")
            return "retry", False
        skill_id, skill_def = available_skills[skill_idx]
        print(f"\n>>> {skill_def['name']}: {skill_def['description']}")
        mastery_label = format_mastery_label(skill_id, player)
        if mastery_label:
            print(f"    Mastery: {mastery_label}")
        input("Press Enter to use it...")

        from combat.ally import get_alive_allies
        allies = get_alive_allies(player)
        msg, victory = execute_skill(
            player, skill_id, enemies,
            p_str, p_con, p_dex, p_ler, p_wis, p_cha,
            allies=allies
        )
        print(msg)
        set_skill_cooldown(player, skill_id)
        if victory:
            return "victory", False
        return "continue", False

    # ----- ATTACK -----
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

        equipped_weapon = player.get("equipped", {}).get("weapon")
        raw_scaling = equipped_weapon.get("scaling_stat", ["Strength"]) if equipped_weapon else ["Strength"]
        scaling_stats = raw_scaling if isinstance(raw_scaling, list) else [raw_scaling]

        scaling_val = 0
        for stat in scaling_stats:
            if stat == "Strength":
                scaling_val += p_str
            elif stat == "Dexterity":
                scaling_val += p_dex
            elif stat == "Constitution":
                scaling_val += p_con
            elif stat == "Learning":
                scaling_val += p_ler
            elif stat == "Wisdom":
                scaling_val += p_wis
            elif stat == "Charisma":
                scaling_val += p_cha
            else:
                from stats import get_effective_attribute
                scaling_val += get_effective_attribute(player, stat)

        dmg = random.randint(4, 10) + scaling_val + get_strength_bonus(player) - target["con_mod"]
        dmg = max(0, dmg)

        # Apply elemental damage
        from combat.elemental import calculate_elemental_damage, get_attack_element
        element = get_attack_element(player, equipped_weapon)
        final_dmg = calculate_elemental_damage(dmg, player, target, element)
        if on_hit:
            on_hit(target, enemies) 
        target["hp"] -= final_dmg

        verb = "strike"
        if "Dexterity" in scaling_stats:
            verb = "shoot" if "bow" in equipped_weapon.get("id", "") else "pierce"
        elif "Learning" in scaling_stats:
            verb = "blast"

        # Elemental flavor text
        elemental_tags = {"fire": "[FIRE]", "water": "[ICE]", "thunder": "[THUNDER]",
                          "wind": "[WIND]", "earth": "[EARTH]", "light": "[LIGHT]", "dark": "[DARK]"}
        tag = elemental_tags.get(element, "")
        if tag:
            print(f"{player['name']} {verb} {target['name']} for {final_dmg} damage! {tag}")
        else:
            print(f"{player['name']} {verb} {target['name']} for {final_dmg} damage!")
        if target["hp"] <= 0:
            print(f"{player['name']} defeated {target['name']}!")
            if on_kill:
                on_kill(target, enemies)
        return "continue", False

    # ----- DEFEND -----
    elif action == "d":
        print(f"{player['name']} braces for impact, raising {player['name']} guard.")
        return "continue", True

    # ----- USE ITEM -----
    elif action == "u":
        if is_silenced(player):
            print(f"{player['name']} is silenced! {player['name']} hands cannot reach the bag.")
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

            if item.get("capture_net"):
                mg_targets = [e for e in enemies if is_monster_girl(e) and e["hp"] > 0]
                if not mg_targets:
                    print("No monster girls present.")
                    return "retry", False
                if len(mg_targets) > 1:
                    print("Select target to capture:")
                    for i, e in enumerate(mg_targets):
                        print(f"{i+1}. {e['name']}")
                    try:
                        idx = int(input("Choice: ")) - 1
                        target = mg_targets[idx]
                    except:
                        return "retry", False
                else:
                    target = mg_targets[0]
                player["inventory"].pop(true_idx)
                if attempt_capture(player, target, net=item):
                    enemies.remove(target)
                return "continue", False

            if "power" in item:
                old_hp = player["current_hp"]
                heal = item["power"] + get_wisdom_bonus(player)
                new_hp = min(old_hp + heal, player_max_hp(player))
                healed_amount = new_hp - old_hp
                player["current_hp"] = new_hp
                msg += f"{player['name']} recover {healed_amount} HP. "
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
                # REMOVE the is_fake block entirely
                msg += f"You deal {final_dmg} damage to the {target['name']}! "
            if "poison_damage" in item:
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

            if item.get("fixed_flee"):
                rarity_rates = {
                    "common": 0.40,
                    "uncommon": 0.60,
                    "rare": 0.80,
                    "epic": 0.95,
                    "legendary": 1.00
                }
                item_rarity = item.get("rarity", "common")
                success_chance = rarity_rates.get(item_rarity, 0.40)
                if random.random() < success_chance:
                    print(f"\n✨ The {item['name']} tears open a rift! You successfully escape the fray!")
                    player["inventory"].pop(true_idx)
                    return "fled", False
                else:
                    print(f"\n💨 The {item['name']} sputters and fizzles out! Escape failed!")
                    player["inventory"].pop(true_idx)
                    return "continue", False

            print(msg)
            player["inventory"].pop(true_idx)

            if not [e for e in enemies if e["hp"] > 0]:
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
        # Smoke Bomb guarantee
        if player.pop("smoke_bomb_flee", False):
            print("You vanish effortlessly through the smoke! Escape successful!")
            return "fled", False

        effective_player_dex = p_dex + get_wisdom_bonus(player)
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
        
    elif action == "c":
        mg_targets = [e for e in enemies if is_monster_girl(e) and e["hp"] > 0]
        if not mg_targets:
            print("No monster girls present.")
            return "retry", False

        # Pick target
        if len(mg_targets) > 1:
            print("Select target to capture:")
            for i, e in enumerate(mg_targets):
                print(f"{i+1}. {e['name']}")
            try:
                idx = int(input("Choice: ")) - 1
                target = mg_targets[idx]
            except:
                return "retry", False
        else:
            target = mg_targets[0]

        if attempt_capture(player, target):
            enemies.remove(target)  # remove from combat
            return "continue", False
        else:
            return "continue", False

    return "retry", False