from combat.combat_io import c_print, c_input, c_clear
import random
from character import player_max_hp
from combat.status_effects import cure_curse, apply_poison, is_silenced, is_dreaded, format_player_status_line
from combat.combat_ui import print_combat_hud, format_enemy_status_line
from combat.abyss_fang import wield_abyss_fang
from combat.wedding_specials import (
    apply_wedding_attack_bonus_procs,
    apply_wedding_on_hit,
    apply_wedding_on_kill,
)
from combat.action_menu import get_action_menu
from combat.capture import is_monster_girl, is_capturable, attempt_capture
from combat.stat_milestones import get_strength_bonus, get_wisdom_bonus, get_dexterity_damage_bonus
from combat.skills import get_available_skills, execute_skill, set_skill_cooldown, format_mastery_label, get_passive_skill
from inventory import remove_item_by_reference


def handle_player_turn(player, enemies, p_str, p_con, p_dex, p_ler, p_wis, p_cha, on_kill=None, on_hit=None, _action_override=None):
    if _action_override is None:
        # Normal player input
        print_combat_hud(player, enemies)
        menu_str, valid_actions, _disabled = get_action_menu(player, enemies)
        action = c_input("Choose: ").strip().lower()
        while action not in valid_actions:
            c_print(f"Invalid choice. Available: {', '.join(valid_actions)}")
            action = c_input("Choose: ").strip().lower()
    else:
        # Override from superboss loop
        action = _action_override
        _, valid_actions, _disabled = get_action_menu(player, enemies)
        if action not in valid_actions:
            c_print(f"Internal error: override action '{action}' is not available.")
            return "retry", False

    # ----- SKILLS (numbered 1-9) or GLOVES WORKSHOPS -----
    if action.isdigit():
        # Check if Black Silence Gloves are equipped — workshop attacks replace skills
        from combat.black_silence_gloves import _player_has_black_silence_gloves, execute_workshop, execute_furioso

        if _player_has_black_silence_gloves(player):
            if action == '0':
                # FURIOSO
                c_print("\n>>> FURIOSO: All nine workshops in sequence! <<<")
                enemies_before = [e for e in enemies if e["hp"] > 0]
                msg, victory = execute_furioso(
                    player, enemies, p_str, p_con, p_dex, p_ler, p_wis, p_cha,
                )
                c_print(msg)
                # Fire on_kill for enemies actually killed by the attack (snapshot before side effects)
                if on_kill:
                    killed_by_attack = [e for e in enemies_before if e["hp"] <= 0]
                    for e in killed_by_attack:
                        on_kill(e, enemies)
                if victory:
                    return "victory", False
                return "continue", False
            else:
                workshop_id = int(action)
                if workshop_id < 1 or workshop_id > 9:
                    c_print("Invalid workshop choice.")
                    return "retry", False
                # Guard: reject already-used workshops
                ws_used = player.get("gloves_workshop_used", set())
                if not isinstance(ws_used, (set, list)):
                    ws_used = set()
                if workshop_id in ws_used:
                    c_print("That workshop has already been used this cycle!")
                    return "retry", False
                from combat.black_silence_gloves import WORKSHOPS
                ws = WORKSHOPS.get(workshop_id, {})
                ws_name = ws.get("name", f"Workshop {workshop_id}")
                ws_desc = ws.get("desc", "")
                c_print(f"\n>>> {ws_name}: {ws_desc}")
                c_input("Press Enter to use it...")
                enemies_before = [e for e in enemies if e["hp"] > 0]
                msg, victory = execute_workshop(
                    player, enemies, workshop_id,
                    p_str, p_con, p_dex, p_ler, p_wis, p_cha,
                )
                c_print(msg)
                # Fire on_kill for enemies actually killed by the attack (snapshot before side effects)
                if on_kill:
                    killed_by_attack = [e for e in enemies_before if e["hp"] <= 0]
                    for e in killed_by_attack:
                        on_kill(e, enemies)
                if victory:
                    return "victory", False
                return "continue", False

        # Normal skills (no gloves)
        skill_idx = int(action) - 1
        available_skills = get_available_skills(player)
        if skill_idx < 0 or skill_idx >= len(available_skills):
            c_print("Invalid skill choice.")
            return "retry", False
        skill_id, skill_def = available_skills[skill_idx]
        from combat.combat_ui import format_skill_elemental_tag
        elem_tag = format_skill_elemental_tag(skill_def)
        c_print(f"\n>>> {skill_def['name']}{elem_tag}: {skill_def['description']}")
        mastery_label = format_mastery_label(skill_id, player)
        if mastery_label:
            c_print(f"    Mastery: {mastery_label}")
        c_input("Press Enter to use it...")

        from combat.ally import get_alive_allies
        allies = get_alive_allies(player)
        # Track enemies alive before skill so on_kill can fire for newly-dead ones
        enemies_before = [e for e in enemies if e["hp"] > 0]
        msg, victory = execute_skill(
            player, skill_id, enemies,
            p_str, p_con, p_dex, p_ler, p_wis, p_cha,
            allies=allies
        )
        c_print(msg)
        # Fire on_kill for enemies actually killed by the skill (snapshot before side effects
        # like boss-death triggers destroying linked minions)
        if on_kill:
            killed_by_skill = [e for e in enemies_before if e["hp"] <= 0]
            for e in killed_by_skill:
                on_kill(e, enemies)
        # Re-check victory after on_kill callbacks (e.g. boss death may destroy linked minions)
        if not victory:
            if not [e for e in enemies if e["hp"] > 0]:
                victory = True
        cd_msg = set_skill_cooldown(player, skill_id)
        if cd_msg:
            c_print(cd_msg)
        if victory:
            return "victory", False
        return "continue", False

    # ----- ATTACK -----
    if action == "a":
        if len(enemies) > 1:
            try:
                choice = int(c_input("Select target number: ")) - 1
                if choice < 0 or choice >= len(enemies):
                    c_print("Invalid target selection.")
                    return "retry", False
                target = enemies[choice]
            except ValueError:
                c_print("Please enter a valid number.")
                return "retry", False
        else:
            target = enemies[0]

        # --- ENEMY DODGE CHECK ---
        from combat.stats import roll_dodge
        is_dodged, dodge_chance = roll_dodge(target, player)
        if is_dodged:
            c_print(f"The {target['name']} dodges your attack!")
            return "continue", False

        # ── Wonderland Shadow: Caterpillar's Smoke — accuracy penalty ──
        from wonderland_curses import get_shadow_accuracy_penalty
        smoke_penalty = get_shadow_accuracy_penalty(player)
        if smoke_penalty > 0 and random.random() < smoke_penalty:
            c_print(f"  💨 The Caterpillar's smoke clouds your vision — your attack goes wide!")
            return "continue", False

        equipped_weapon = player.get("equipped", {}).get("weapon")

        # ── Elemental Trait System (Phase 4) ──
        from combat.elemental_traits import (
            get_trait_for_weapon, apply_trait_pre_damage,
            apply_trait, apply_trait_on_kill,
        )
        trait = get_trait_for_weapon(equipped_weapon, equipped_weapon.get("rarity", "common")) if equipped_weapon else None
        pre_dmg = apply_trait_pre_damage(trait, target) if trait else None

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

        # Apply weapon's scaling_mult (e.g. Constitution weapons use 0.5 for half scaling)
        if equipped_weapon and equipped_weapon.get("scaling_mult"):
            scaling_val = int(scaling_val * equipped_weapon["scaling_mult"])

        # ── Sunder (Physical trait): armor penetration ──
        effective_con_mod = target["con_mod"]
        if pre_dmg and pre_dmg.get("armor_pen", 1.0) < 1.0:
            pen_pct = int((1.0 - pre_dmg["armor_pen"]) * 100)
            effective_con_mod = int(target["con_mod"] * pre_dmg["armor_pen"])
            if target["con_mod"] > 0:
                c_print(f"  ⚔️ Sunder! {pen_pct}% armor penetration — {target['name']}'s armor: {target['con_mod']}→{effective_con_mod}.")
            else:
                c_print(f"  ⚔️ Sunder! {pen_pct}% armor penetration.")
        dmg = random.randint(4, 10) + scaling_val + get_strength_bonus(player) - effective_con_mod
        dmg = max(0, dmg)

        # Rogue sneak attack bonus vs slowed/stunned enemies
        passive = get_passive_skill(player)
        if passive and passive.get("effect", {}).get("type") == "vulnerable_bonus":
            if target.get("slowed") or target.get("stunned"):
                bonus = passive["effect"]["value"]
                dmg = int(dmg * (1 + bonus))
                c_print(f"Sneak Attack! +{int(bonus*100)}% damage to the vulnerable target!")

        # Critical hit check
        from combat.stats import roll_critical_hit, apply_critical_damage, format_critical_tag
        is_crit, _ = roll_critical_hit(player, "player")
        dmg = apply_critical_damage(dmg, is_crit)

        # Wedding accessory attack bonuses
        is_first = not player.get("wedding_first_attack_done")
        wedding_bonus = apply_wedding_attack_bonus_procs(player, target, dmg, is_first)
        dmg += wedding_bonus
        if wedding_bonus > 0:
            dmg = max(0, dmg)

        # Apply elemental damage
        from combat.elemental import calculate_elemental_damage, get_attack_element
        element = get_attack_element(player, equipped_weapon)
        final_dmg = calculate_elemental_damage(dmg, player, target, element)

        # ── Pierce (Magical trait): ignore portion of enemy elemental resistance ──
        if pre_dmg and pre_dmg.get("res_ignore", 0) > 0 and element:
            ignore_pct = int(pre_dmg["res_ignore"] * 100)
            target_res = target.get("elemental_res", {}).get(element, 1.0)
            if target_res < 1.0:  # enemy resists this element
                attacker_dmg_mult = player.get("elemental_dmg", {}).get(element, 1.0)
                mitigated_res = 1.0 + (target_res - 1.0) * (1.0 - pre_dmg["res_ignore"])
                final_dmg = int(dmg * attacker_dmg_mult * mitigated_res)
                final_dmg = max(0, final_dmg)
                c_print(f"  🔮 Pierce! {target['name']}'s {element} resistance bypassed ({ignore_pct}%).")
            else:
                c_print(f"  🔮 Pierce! {ignore_pct}% resistance penetration active.")

        # Apply Hunter's Mark damage bonus
        if target.get("hunters_mark"):
            bonus = target.get("hunters_mark_bonus", 0.50)
            final_dmg = int(final_dmg * (1 + bonus))

        # Captain's Cutlass: High Tide + Rally attack bonuses
        from combat.captain_cutlass import get_high_tide_attack_bonus, get_rally_attack_bonus
        final_dmg += get_high_tide_attack_bonus(player, final_dmg)
        final_dmg += get_rally_attack_bonus(player, final_dmg)
        final_dmg = max(0, final_dmg)

        # Pandemonium: Weakened Resolve curse — player deals less damage
        if player.get("pandemonium_curse"):
            from pandemonium_curses import apply_damage_dealt_multiplier
            final_dmg = apply_damage_dealt_multiplier(player, final_dmg)

        # Wonderland: Jabberwock's Bane — bonus damage vs boss enemies
        if target.get("boss"):
            from wonderland_curses import get_jabberwock_bane_multiplier
            bane_mult = get_jabberwock_bane_multiplier(player)
            if bane_mult > 0:
                bonus_dmg = int(final_dmg * bane_mult)
                final_dmg += bonus_dmg
                if bonus_dmg > 0:
                    c_print(f"  ⚔️ Vorpal blessing surges! +{bonus_dmg} bonus damage!")

        if on_hit:
            on_hit(target, enemies)
        target["hp"] -= final_dmg
        # Wake sleeping enemy on damage
        from combat.status_effects import wake_on_damage
        wake_msg = wake_on_damage(target)
        if wake_msg:
            c_print(f"  {wake_msg}")
        # ── Elemental Trait: on-hit effects (Ignite, Chain, Leech, Swift, Bulwark) ──
        if trait:
            apply_trait(trait, player, target, enemies, final_dmg)

        # Wedding on-hit effects
        apply_wedding_on_hit(player, target, enemies, final_dmg)

        # Vileheart Pendant: chance to poison on physical hit
        from combat.vileheart_venom import try_vileheart_venom_proc
        if try_vileheart_venom_proc(player, target):
            c_print(f"  🧪 Vileheart Pendant: {target['name']} is poisoned!")

        player["wedding_first_attack_done"] = True

        verb = "strike"
        if "Dexterity" in scaling_stats:
            verb = "shoot" if "bow" in equipped_weapon.get("id", "") else "pierce"
        elif "Learning" in scaling_stats:
            verb = "blast"

        crit_tag = format_critical_tag(is_crit)
        is_crit_bool = bool(crit_tag)
        from combat.helpers import format_damage_msg
        c_print(format_damage_msg(player['name'], target['name'], final_dmg, element=element, crit=is_crit_bool))
        if target["hp"] <= 0:
            c_print(f"{player['name']} defeated {target['name']}!")
            if on_kill:
                on_kill(target, enemies)
            apply_wedding_on_kill(player, target, enemies)

            # ── Elemental Trait: on-kill effects (Douse, Purge) ──
            if trait:
                apply_trait_on_kill(trait, player, target, enemies)

            # Captain's Cutlass: High Tide stack on kill
            from combat.captain_cutlass import check_high_tide_kill
            check_high_tide_kill(player, target)
        return "continue", False

    # ----- DEFEND -----
    elif action == "d":
        c_print(f"{player['name']} braces for impact, raising {player['name']} guard.")
        return "continue", True

    # ----- USE ITEM -----
    elif action == "u":
        if is_silenced(player):
            c_print(f"{player['name']} is silenced! {player['name']} hands cannot reach the bag.")
            return "retry", False

        combat_inventory = [
            (idx, item) for idx, item in enumerate(player.get("inventory", []))
            if item.get("type") in ["consumable", "utility"]
        ]
        if not combat_inventory:
            c_print("You have no items usable in combat.")
            return "retry", False

        c_print("\nYour Battle Inventory:")
        for display_idx, (_, itm) in enumerate(combat_inventory):
            qty = itm.get("count", 1)
            qty_str = f" x{qty}" if qty > 1 else ""
            c_print(f"{display_idx+1}. {itm['name']}{qty_str} ({itm['type']})")
        try:
            choice = int(c_input("Use which item? (0 to cancel): ")) - 1
            if choice < 0 or choice >= len(combat_inventory):
                return "retry", False
            true_idx, item = combat_inventory[choice]
            msg = ""
            target = None

            # ── Potion Sickness: only blocks healing consumables (not buffs/utility items) ──
            is_healing_item = (
                item.get("type") == "consumable" and
                item.get("power", 0) > 0
            )
            if is_healing_item and player.get("potion_sickness", 0) > 0:
                c_print(f"You're still queasy from the last potion! ({player['potion_sickness']} turn(s) remaining)")
                return "retry", False

            # Items that need an enemy target: utility items with debuff/damage keys.
            # Consumables never need a target (they always affect the player).
            # Escape/flee/capture items handle their own target logic separately.
            affects_enemy = (
                any(k in item for k in ["status", "blind_enemy", "damage_over_time",
                                         "poison_damage", "stun_chance", "expose_armor",
                                         "burn_tier", "shock_damage"]) or
                (item.get("type") == "utility" and
                 item.get("power", item.get("base_power", 0)) > 0 and
                 "escape_bonus" not in item and
                 not item.get("fixed_flee") and
                 not item.get("capture_net"))
            )
            if affects_enemy:
                if len(enemies) > 1:
                    try:
                        t_choice = int(c_input(f"Select target for {item['name']}: ")) - 1
                        if t_choice < 0 or t_choice >= len(enemies):
                            c_print("Invalid target choice.")
                            return "retry", False
                        target = enemies[t_choice]
                    except ValueError:
                        c_print("Invalid input.")
                        return "retry", False
                else:
                    target = enemies[0]

            if item.get("capture_net"):
                mg_targets = [e for e in enemies if is_capturable(e) and e["hp"] > 0]
                if not mg_targets:
                    c_print("No capturable monster girls present.")
                    return "retry", False
                if len(mg_targets) > 1:
                    c_print("Select target to capture:")
                    for i, e in enumerate(mg_targets):
                        c_print(f"{i+1}. {e['name']}")
                    try:
                        idx = int(c_input("Choice: ")) - 1
                        target = mg_targets[idx]
                    except:
                        return "retry", False
                else:
                    target = mg_targets[0]
                remove_item_by_reference(player, item)
                if attempt_capture(player, target, net=item):
                    enemies.remove(target)
                return "continue", False

            if "power" in item and item.get("type") == "consumable":
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
            # ── Elemental consumable effects (Phase 3) ──
            if item.get("buff_fire_resist"):
                pct = int(item["buff_fire_resist"] * 100)
                player.setdefault("active_buffs", []).append({
                    "type": "fire_resist",
                    "value": item["buff_fire_resist"],
                    "remaining": item.get("buff_duration", 2)
                })
                msg += f"Fire resistance increased by {pct}% for {item.get('buff_duration',2)} turns. "
            if item.get("cleanse_burn_poison"):
                before_count = len(player.get("active_debuffs", []))
                player["active_debuffs"] = [d for d in player.get("active_debuffs", [])
                                            if d.get("type") not in ("burn", "poison")]
                removed = before_count - len(player["active_debuffs"])
                if removed > 0:
                    msg += f"Burns and poisons are cleansed! ({removed} removed) "
                else:
                    msg += "No burns or poisons to cleanse. "
            if item.get("cooldown_reduce"):
                reduced = 0
                for skill_id in list(player.get("skill_cooldowns", {}).keys()):
                    if player["skill_cooldowns"][skill_id] > 0:
                        player["skill_cooldowns"][skill_id] = max(0, player["skill_cooldowns"][skill_id] - item["cooldown_reduce"])
                        reduced += 1
                if reduced > 0:
                    msg += f"All skill cooldowns reduced by {item['cooldown_reduce']}! "
                else:
                    msg += "No skills on cooldown. "
            if item.get("init_bonus"):
                player.setdefault("active_buffs", []).append({
                    "type": "initiative",
                    "value": item["init_bonus"],
                    "remaining": item.get("buff_duration", 3)
                })
                msg += f"Initiative increased by {item['init_bonus']} for {item.get('buff_duration',3)} turns. "
            if item.get("cleanse_curse_debuff"):
                # Cure curse
                result = cure_curse(player)
                if result == "cured":
                    msg += "The dark curse is lifted! "
                # Remove 1 random debuff
                debuffs = player.get("active_debuffs", [])
                if debuffs:
                    removed_debuff = random.choice(debuffs)
                    player["active_debuffs"].remove(removed_debuff)
                    msg += f"A {removed_debuff.get('type','debuff')} is cleansed! "
            if item.get("dodge_next"):
                player.setdefault("active_buffs", []).append({
                    "type": "dodge",
                    "value": 1,
                    "remaining": 1,
                    "source": "shadow_essence"
                })
                msg += "You feel ethereal — the next attack will miss! "
            if item.get("restore_random_skill"):
                on_cd = [sid for sid, cd in player.get("skill_cooldowns", {}).items() if cd > 0]
                if on_cd:
                    chosen = random.choice(on_cd)
                    player["skill_cooldowns"][chosen] = 0
                    msg += f"A random skill's cooldown is restored! "
                else:
                    msg += "No skills on cooldown to restore. "
            if item.get("expose_armor"):
                if target is None:
                    # Fallback: affects_enemy should have caught this; if not, pick first alive enemy
                    alive = [e for e in enemies if e["hp"] > 0]
                    if alive:
                        target = alive[0]
                    else:
                        c_print("No valid target for armour shatter!")
                        return "retry", False
                from combat.status_effects import apply_expose
                result, new_con = apply_expose(target, item["expose_armor"])
                if result == "applied":
                    msg += f"{target['name']}'s armour is shattered! Armour reduced to {new_con}. "
                else:
                    msg += f"{target['name']}'s armour is already fully exposed! "
            if item.get("burn_tier"):
                from combat.status_effects import apply_burn
                result = apply_burn(target, tier=item["burn_tier"], duration=item.get("burn_duration", 3))
                if result == "applied":
                    msg += f"{target['name']} catches fire! "
                elif result == "upgraded":
                    msg += f"The flames intensify on {target['name']}! "
                elif result == "intensified":
                    msg += f"The blaze grows stronger on {target['name']}! "
                else:
                    msg += f"The burn on {target['name']} is refreshed. "
            if item.get("shock_damage"):
                from combat.status_effects import apply_shock
                result = apply_shock(target, item["shock_damage"], item.get("shock_duration", 3))
                if result == "applied":
                    msg += f"{target['name']} is jolted with electricity! "
                else:
                    msg += f"The shock on {target['name']} is renewed! "
            if item.get("type") == "utility" and "damage_over_time" not in item and "stun_chance" not in item:
                item_power = item.get("power", item.get("base_power", 0))
                if item_power > 0:
                    dmg = item_power + get_dexterity_damage_bonus(player)
                    armor = target["con_mod"]
                    if "armor_pierce" in item:
                        armor = max(0, armor - item["armor_pierce"])
                        msg += f"(ignores {item['armor_pierce']} armor) "
                    final_dmg = max(1, dmg - armor)
                    target["hp"] -= final_dmg
                    # Wake sleeping enemy on damage
                    from combat.status_effects import wake_on_damage
                    wake_msg = wake_on_damage(target)
                    if wake_msg:
                        msg += f"  {wake_msg} "
                    from combat.helpers import format_damage_msg
                    msg += format_damage_msg(player['name'], target['name'], final_dmg, skill_name=item.get('name', 'Item')) + " "
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
                from pandemonium_curses import is_flee_blocked
                if is_flee_blocked(player):
                    c_print("The crystalline walls seal shut — there is NO escape from this floor!")
                    return "continue", False
                c_print(msg)
                remove_item_by_reference(player, item)
                return "fled", False

            if item.get("fixed_flee"):
                from pandemonium_curses import is_flee_blocked
                if is_flee_blocked(player):
                    c_print("The crystalline walls seal shut — there is NO escape from this floor!")
                    return "continue", False
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
                    c_print(f"\n✨ The {item['name']} tears open a rift! You successfully escape the fray!")
                    remove_item_by_reference(player, item)
                    return "fled", False
                else:
                    c_print(f"\n💨 The {item['name']} sputters and fizzles out! Escape failed!")
                    remove_item_by_reference(player, item)
                    return "continue", False

            c_print(msg)
            remove_item_by_reference(player, item)
            if is_healing_item:
                player["potion_sickness"] = 2

            if not [e for e in enemies if e["hp"] > 0]:
                return "victory", False
            if player["current_hp"] <= 0:
                return "dead", False

        except (ValueError, IndexError):
            c_print("Invalid choice.")
            return "retry", False
        return "continue", False

    # ----- WIELD THE ABYSS -----
    elif action == "w":
        return wield_abyss_fang(player)

    # ----- CREW RALLY -----
    elif action == "r":
        from combat.captain_cutlass import use_crew_rally
        return use_crew_rally(player)

    # ----- REWRITE (Author's Pen) -----
    elif action == "e":
        from combat.authors_pen import use_rewrite
        return use_rewrite(player)

    # ----- FLEE -----
    elif action == "f":
        # Pandemonium: Crystalline Prison curse blocks all fleeing
        from pandemonium_curses import is_flee_blocked
        if is_flee_blocked(player):
            c_print("The crystalline walls seal shut — there is NO escape from this floor!")
            return "continue", False

        # Smoke Bomb guarantee
        if player.pop("smoke_bomb_flee", False):
            c_print("You vanish effortlessly through the smoke! Escape successful!")
            return "fled", False

        effective_player_dex = p_dex + get_wisdom_bonus(player)
        for debuff in player.get("active_debuffs", []):
            if debuff["type"] == "slow":
                effective_player_dex -= 3
            if player.get("blinded"):
                effective_player_dex -= 2
                c_print("Your blindness makes escape harder!")
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
            c_print("You fail to escape and expose yourself!")
            return "continue", False
        
    elif action == "c":
        mg_targets = [e for e in enemies if is_capturable(e) and e["hp"] > 0]
        if not mg_targets:
            c_print("No capturable monster girls present.")
            return "retry", False

        # Gather capture nets from inventory
        nets = [item for item in player.get("inventory", []) if item.get("capture_net")]
        if not nets:
            c_print("You need a Capture Net to attempt this!")
            return "retry", False

        # Pick which net to use
        if len(nets) == 1:
            chosen_net = nets[0]
        else:
            c_print("Select capture net to use:")
            for i, net in enumerate(nets):
                name = net.get("name", "Capture Net")
                bonus = net.get("rarity_mult_bonus", 25)
                count = net.get("count", 1)
                c_print(f"{i+1}. {name} (+{bonus} catch) x{count}")
            try:
                idx = int(c_input("Net choice (0 to cancel): ")) - 1
                if idx < 0 or idx >= len(nets):
                    c_print("Invalid choice.")
                    return "retry", False
                chosen_net = nets[idx]
            except:
                return "retry", False

        # Pick target
        if len(mg_targets) > 1:
            c_print("Select target to capture:")
            for i, e in enumerate(mg_targets):
                c_print(f"{i+1}. {e['name']}")
            try:
                idx = int(c_input("Choice: ")) - 1
                target = mg_targets[idx]
            except:
                return "retry", False
        else:
            target = mg_targets[0]

        # Consume the chosen net before attempting capture
        remove_item_by_reference(player, chosen_net)
        if attempt_capture(player, target, net=chosen_net):
            enemies.remove(target)  # remove from combat
            return "continue", False
        else:
            return "continue", False

    return "retry", False