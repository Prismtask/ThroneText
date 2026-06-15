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
    p_ler = get_effective_attribute(player, "Learning")
    p_wis = get_effective_attribute(player, "Wisdom")
    p_cha = get_effective_attribute(player, "Charisma")
    if player.get("training_buff"):
        p_str += player["training_buff"].get("strength", 0)
    return p_str, p_con, p_dex, p_ler, p_wis, p_cha


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
    print(f"\n{player['name']}: {player['current_hp']} {status_line}{tempo_str}".rstrip())

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
        print(f"The {enemy['name']} hits {player['name']} for {enemy_dmg} damage!")
    else:
        print(f"The {enemy['name']} attacks but {player['name']} blocks all incoming damage!")

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
    """
    Initiative-based superboss combat loop.

    Round structure
    ───────────────
    1. pre_player_hook  – phase transitions, spawns, gimmick checks (round start).
    2. HUD              – custom_hud_hook (or default) shows boss-specific status;
                          the initiative order is printed beneath it.
    3. Action phase     – all combatants act in speed order.
       • Player slot    – inline mini-HUD (no clear_screen, preserving earlier
                          messages), then player_action_override / handle_player_turn.
       • Enemy slot     – enemy_turn_hook → enemy_attack (supports multi-action).
    4. post_round_hook  – end-of-round gimmick bookkeeping.
    5. Ticks            – debuffs, buffs, cooldowns.

    The context key "skip_player_turn" is honoured during the player's slot so
    that stun mechanics (e.g. Slitcurrent Nightmarish Tide) work unchanged.
    """
    on_kill_fn = (
        lambda target, elist: on_kill_hook(target, elist, context)
        if on_kill_hook else None
    )
    round_num = 0

    while True:
        round_num += 1

        # ── Abyss Tempo activation ───────────────────────────────────────────
        if player.get("abyss_tempo_pending", 0) > 0:
            pending = player.pop("abyss_tempo_pending")
            player["abyss_triple_actions"] = pending
            print(f"⚔️  The Abyss awakens! Triple actions for {pending} turns!")

        enemies[:] = [e for e in enemies if e["hp"] > 0]
        if not enemies:
            return "victory"

        p_str, p_con, p_dex, p_ler, p_wis, p_cha = compute_player_stats(player)

        # ── Phase transitions / round-start gimmicks ─────────────────────────
        if pre_player_hook:
            result = pre_player_hook(context, enemies)
            if result in ("dead", "victory"):
                return result

        enemies[:] = [e for e in enemies if e["hp"] > 0]
        if not enemies:
            return "victory"

        # ── HUD (context-specific status info) ───────────────────────────────
        if custom_hud_hook:
            custom_hud_hook(context, enemies)
        else:
            clear_screen()
            print_superboss_header(player, floor, boss_name, "")
            print("\nEnemies:")
            for idx, e in enumerate(enemies):
                print(f"  [{idx + 1}] {format_enemy_status_line(e)}")

        # ── Initiative phase ─────────────────────────────────────────────────
        print("\nInitiative Phase")
        print("Rolling speeds...")

        turn_order = roll_initiative(p_dex, enemies)

        # Abyss Tempo: inject extra player slots after the first one
        abyss_count = player.get("abyss_triple_actions", 0)
        if abyss_count > 0:
            first_p_idx = next(
                (i for i, c in enumerate(turn_order) if c["type"] == "player"),
                None
            )
            if first_p_idx is not None:
                base_speed = turn_order[first_p_idx]["speed"]
                for extra_num in range(1, 3):
                    turn_order.insert(first_p_idx + extra_num, {
                        "type":       "player",
                        "speed":      base_speed,
                        "label":      f"You (Abyss Extra {extra_num + 1}/3)",
                        "enemy":      None,
                        "extra_turn": extra_num + 1,
                    })

        print("\nTurn Order for this Round:")
        stunned_this_round = context.get("skip_player_turn", False)
        for i, c in enumerate(turn_order):
            suffix = " [STUNNED — will skip]" if stunned_this_round and c["type"] == "player" and not c.get("extra_turn") else ""
            print(f"  {i + 1:>2}. {c['label']} (Speed: {c['speed']}){suffix}")

        input("\nPress Enter to start the round...")

        # ── Action phase ─────────────────────────────────────────────────────
        print(f"\n⚔️  Round {round_num}: Action Phase")

        defending = False

        for step_idx, combatant in enumerate(turn_order):
            live_enemies = [e for e in enemies if e["hp"] > 0]
            if not live_enemies:
                break

            slot_label = f"[{step_idx + 1}/{len(turn_order)}]"
            print(f"\n{slot_label} {combatant['label']}'s Turn:")

            # ── Player slot ──────────────────────────────────────────────────
            if combatant["type"] == "player":
                if player["current_hp"] <= 0:
                    print(f"{player['name']} has been slain.")
                    return "dead"

                # Stun skip (e.g. Slitcurrent Nightmarish Tide)
                if context.get("skip_player_turn") and not combatant.get("extra_turn"):
                    print(f"{player['name']} is stunned and cannot act!")
                    context["skip_player_turn"] = False
                    continue

                extra_turn = combatant.get("extra_turn")
                if extra_turn:
                    print(f"⚔️  ABYSS TEMPO — Extra Action {extra_turn}/3!")

                # Inline mini-HUD (no clear_screen; enemy messages stay visible)
                status_str = format_player_status_line(player)
                tempo_str  = " [Abyssal Tempo]" if player.get("abyss_triple_actions", 0) > 0 else ""
                print(f"\n{player['name']}: {player['current_hp']} {status_str}{tempo_str}".rstrip())
                print("Enemies:")
                for idx, e in enumerate(live_enemies):
                    print(f"  [{idx + 1}] {format_enemy_status_line(e)}")
                print("[A]ttack  [D]efend  [F]lee  [U]se item")

                # Action input + handle (retry loops in place, no re-roll)
                while True:
                    action = (
                        player_action_override(context)
                        if player_action_override
                        else input("Choose: ").strip().lower()
                    )
                    result, new_def = handle_player_turn(
                        player, live_enemies, p_str, p_con, p_dex, p_ler, p_wis, p_cha,
                        on_kill=on_kill_fn,
                        _action_override=action,
                    )
                    if result != "retry":
                        break
                    # Re-print choices on invalid input before re-prompting
                    print("[A]ttack  [D]efend  [F]lee  [U]se item")

                if result == "continue":
                    if new_def:
                        defending = True
                    if not [e for e in enemies if e["hp"] > 0]:
                        return "victory"
                elif result == "victory":
                    return "victory"
                elif result in ("fled", "dead"):
                    return result

            # ── Enemy slot ───────────────────────────────────────────────────
            else:
                enemy = combatant["enemy"]
                if enemy["hp"] <= 0:
                    print(f"  ({enemy['name']} is already defeated.)")
                    continue

                actions    = 1
                skip_atk   = False
                extra_logic = None
                armor_mult  = 1.0
                temp_str    = 0

                if enemy_turn_hook:
                    hook_res = enemy_turn_hook(enemy, context, player, p_con, defending)
                    if hook_res == "dead":
                        return "dead"
                    if hook_res:
                        actions, skip_atk, extra_logic, armor_mult, temp_str = hook_res

                if not skip_atk:
                    for action_idx in range(actions):
                        if actions > 1:
                            print(f"\n⚡ FAST ACTION! {enemy['name']} unleashes Action {action_idx + 1}/{actions}!")
                        outcome = enemy_attack(
                            enemy, player, p_con, defending,
                            extra_logic=extra_logic,
                            armor_mult=armor_mult,
                            temp_str_bonus=temp_str,
                        )
                        if outcome == "dead":
                            print(f"{player['name']} has been slain.")
                            return "dead"

        # ── Post-round gimmick bookkeeping ────────────────────────────────────
        if post_round_hook:
            if post_round_hook(context, enemies) == "dead":
                return "dead"

        enemies[:] = [e for e in enemies if e["hp"] > 0]
        if not enemies:
            return "victory"

        # Cooldowns
        if player.get("abyss_fang_cooldown", 0) > 0:
            player["abyss_fang_cooldown"] -= 1
            if player["abyss_fang_cooldown"] == 0:
                print("⚔️  The Abyss Fang hums — its hunger is renewed.")
        if player.get("abyss_triple_actions", 0) > 0:
            player["abyss_triple_actions"] -= 1
            if player["abyss_triple_actions"] == 0:
                print("⚔️  Nightmare Tempo fades. The triple-action fury ends.")

        # Debuff / buff ticks
        msgs, died = tick_player_debuffs(player)
        for m in msgs:
            print(m)
        if died:
            print(f"{player['name']} has been slain.")
            return "dead"

        for m in tick_player_buffs(player):
            print(m)

        print("\n" + "-" * 50)
        input("Press Enter to continue...")


def _player_has_abyss_fang(player):
    equipment = player.get("equipped", {})
    if isinstance(equipment, dict):
        weapon = equipment.get("weapon")
        if weapon and weapon.get("special") == "dream_devour":
            return weapon
        
    return None


def handle_player_turn(player, enemies, p_str, p_con, p_dex, p_ler, p_wis, p_cha, on_kill=None, _action_override=None):
    if _action_override is None:
        status_str = format_player_status_line(player)
        tempo_str = " [Abyssal Tempo]" if player.get("abyss_triple_actions", 0) > 0 else ""
        print(f"\n{player['name']}: {player['current_hp']} {status_str}{tempo_str}".rstrip())
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
        
        # Safely grab the scaling stat(s) and force it into a list format
        raw_scaling = equipped_weapon.get("scaling_stat", ["Strength"]) if equipped_weapon else ["Strength"]
        scaling_stats = raw_scaling if isinstance(raw_scaling, list) else [raw_scaling]
        
        scaling_val = 0
        
        # Loop through all scaling stats and add them together
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
                scaling_val += get_effective_attribute(player, stat)

        dmg = random.randint(4, 10) + scaling_val - target["con_mod"]
        dmg = max(0, dmg)
        target["hp"] -= dmg
        
        # dynamic flavor verbs based on scaling stat
        verb = "strike"
        if "Dexterity" in scaling_stats:
            verb = "shoot" if "bow" in equipped_weapon.get("id", "") else "pierce"
        elif "Learning" in scaling_stats:
            verb = "blast"

        print(f"{player['name']} {verb} {target['name']} for {dmg} damage!")
        if target["hp"] <= 0:
            print(f"{player['name']} defeated {target['name']}!")
            if on_kill:
                on_kill(target, enemies)
        return "continue", False

    # ----- DEFEND -----
    elif action == "d":
        print(f"{player['name']} braces for impact, raising {player['possessive']} guard.")
        return "continue", True

    # ----- USE ITEM -----
    elif action == "u":
        if is_silenced(player):
            print(f"{player['name']} is silenced! {player['possessive']} hands cannot reach {player['object_pronoun']}.")
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

def superboss_triple_action_loop(player, enemies, p_str, p_con, p_dex, p_ler, p_wis, p_cha, on_kill, print_hud_func):
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
            player, enemies, p_str, p_con, p_dex, p_ler, p_wis, p_cha,
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
                    return f"The {e['name']}'s claws open a wound! {player['name']} bleed for {bleed_dmg}/round."
                elif result == "refreshed":
                    return f"The {e['name']} tears {player['name']}'s wound wider! ({bleed_dmg}/round)"
            return None
        return beast_bleed

    if race == "Undead":
        def undead_curse(e, player, dmg):
            if dmg > 0 and random.random() < 0.20:
                result = apply_curse(player)
                if result == "applied":
                    return f"The {e['name']}'s touch carries a dark curse! All attributes reduced."
                elif result == "already_cursed":
                    return f"The {e['name']}'s curse washes over {player['name']}, but already afflicted."
            return None
        return undead_curse

    if race == "Shadow":
        def shadow_dread(e, player, dmg):
            if dmg > 0 and random.random() < 0.30:
                result = apply_dread(player, duration=2)
                if result == "applied":
                    return f"The {e['name']}'s darkness fills {player['name']} with supernatural dread!"
            return None
        return shadow_dread

    if race == "Demon":
        def demon_weaken(e, player, dmg):
            if dmg > 0 and random.random() < 0.25:
                result = apply_weaken(player, str_penalty=2, duration=3)
                if result == "applied":
                    return f"The {e['name']}'s hellfire saps {player['name']}'s strength! STR reduced for 3 turns."
                elif result == "refreshed":
                    return f"{player['name']}'s weakness deepens under the {e['name']}'s assault!"
            return None
        return demon_weaken

    if race == "Vampire":
        def vampire_drain(e, player, dmg):
            if dmg > 0:
                drained = apply_drain(player, e, drain_amount=max(1, dmg // 2))
                if drained > 0:
                    return f"The {e['name']} drains {drained} HP from {player['name']}'s life force!"
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
                    return f"The {e['name']}'s corrosive flesh weakens {player['name']}'s muscles! STR -3 for 3 turns."
                elif result == "refreshed":
                    return f"The corruption deepens — {player['name']}'s strength ebbs further!"
            return None
        return abomination_weaken

    if race == "Giant":
        def giant_weaken(e, player, dmg):
            if dmg > 0 and random.random() < 0.30:
                result = apply_weaken(player, str_penalty=4, duration=2)
                if result == "applied":
                    return f"The {e['name']}'s crushing blow leaves {player['name']} arms numb! STR -4 for 2 turns."
                elif result == "refreshed":
                    return f"Another bone-crushing hit — {player['name']}'s strength fails!"
            return None
        return giant_weaken

    if race == "Gnome":
        def gnome_silence(e, player, dmg):
            if dmg > 0 and random.random() < 0.20:
                result = apply_silence(player, duration=2)
                if result == "applied":
                    return f"The {e['name']}'s arcane static disrupts {player['name']}'s concentration!"
            return None
        return gnome_silence
    
    if race == "Elemental":
        def elemental_blind(e, player, dmg):
            if dmg > 0 and random.random() < 0.30:
                from combat.status_effects import apply_blind
                result = apply_blind(player, duration=2)
                if result == "applied":
                    return f"A burst of searing light from the {e['name']} blinds {player['name']}!"
                elif result == "refreshed":
                    return f"The {e['name']}'s radiance deepens {player['name']}'s blindness!"
            return None
        return elemental_blind

    return None


def roll_initiative(player_dex, enemies):
    """
    Roll speed for every combatant and return a sorted turn-order list.

    Speed = d20 + effective Dexterity.
    Slowed enemies suffer a -3 dex penalty to their roll.
    Stunned / frozen enemies still appear in the list so their slot can be
    skipped visibly ("X is stunned and cannot act!") rather than silently.

    Returns a list of dicts, fastest first:
      {
        "type":       "player" | "enemy",
        "speed":      int,
        "label":      str,          # display name
        "enemy":      dict | None,  # enemy dict (None for player slots)
        "extra_turn": int | None,   # Abyss Tempo slot index (None = normal)
      }
    """
    combatants = []

    # Player slot
    player_speed = random.randint(1, 20) + player_dex
    combatants.append({
        "type":       "player",
        "speed":      player_speed,
        "label":      "You",
        "enemy":      None,
        "extra_turn": None,
    })

    # One slot per enemy
    for idx, enemy in enumerate(enemies):
        eff_dex = enemy["dex_mod"]
        if enemy.get("slowed"):
            eff_dex = max(-10, eff_dex - 3)
        speed = random.randint(1, 20) + eff_dex
        combatants.append({
            "type":       "enemy",
            "speed":      speed,
            "label":      f"[{idx + 1}] {enemy['name']}",
            "enemy":      enemy,
            "extra_turn": None,
        })

    # Fastest first; random tiebreak so equal speeds don't always favour the
    # same entity.
    combatants.sort(key=lambda c: (c["speed"], random.random()), reverse=True)
    return combatants


def combat(player, enemy_keys, floor=None, room_num=None, total_rooms=None):
    """
    Main generic combat loop.

    Turn structure each round
    ─────────────────────────
    1. Initiative phase  – roll speed for every combatant, sort fastest→slowest,
                           optionally inject Abyss Tempo extra-player slots.
    2. Action phase      – iterate through the ordered list; each entity acts in
                           sequence.  The player chooses [A]ttack/[D]efend/[F]lee/
                           [U]se item on their slot.  The "defending" flag only
                           reduces damage from enemies whose slot comes *after*
                           the player's in the same round.
    3. End-of-round      – tick debuffs/buffs, decrement cooldowns.
    """
    player["abyss_triple_actions"] = 0

    enemies = [enemy_stats(k, player) for k in enemy_keys]
    print("\nEnemies approach!")
    for e in enemies:
        print(f"- A {e['name']} appears! (HP: {e['hp']})")
    input("Press Enter to begin...")

    round_num = 0

    while True:
        round_num += 1

        # ── Abyss Tempo activation ───────────────────────────────────────────
        if player.get("abyss_tempo_pending", 0) > 0:
            pending = player.pop("abyss_tempo_pending")
            player["abyss_triple_actions"] = pending
            print(f"⚔️  The Abyss awakens! Triple actions for {pending} turns!")

        enemies = prune_dead(enemies)
        if not enemies:
            print("All enemies have been defeated!")
            player["abyss_triple_actions"] = 0
            return "victory"

        p_str, p_con, p_dex, p_ler, p_wis, p_cha = compute_player_stats(player)

        # ── Round header ─────────────────────────────────────────────────────
        clear_screen()
        if floor is not None and room_num is not None and total_rooms is not None:
            from utils import format_time
            time_str = format_time(player.get("time_minutes", 0))
            print(f"Dungeon Floor {floor} - Room {room_num}/{total_rooms} "
                  f"| Turn {round_num} | Time: {time_str}")

        status_str = format_player_status_line(player)
        tempo_str  = " [Abyssal Tempo]" if player.get("abyss_triple_actions", 0) > 0 else ""
        print(f"Your HP: {player['current_hp']} {status_str}{tempo_str}".rstrip())
        print("Enemies in the room:")
        for idx, e in enumerate(enemies):
            print(f"  [{idx + 1}] {format_enemy_status_line(e)}")

        # ── Initiative phase ─────────────────────────────────────────────────
        print("\nInitiative Phase")
        print("Rolling speeds...")

        turn_order = roll_initiative(p_dex, enemies)

        # Abyss Tempo: inject 2 extra player slots directly after the first one
        abyss_count = player.get("abyss_triple_actions", 0)
        if abyss_count > 0:
            first_p_idx = next(
                (i for i, c in enumerate(turn_order) if c["type"] == "player"),
                None
            )
            if first_p_idx is not None:
                base_speed = turn_order[first_p_idx]["speed"]
                for extra_num in range(1, 3):       # slots 2 and 3 of 3
                    turn_order.insert(first_p_idx + extra_num, {
                        "type":       "player",
                        "speed":      base_speed,
                        "label":      f"You (Abyss Extra {extra_num + 1}/3)",
                        "enemy":      None,
                        "extra_turn": extra_num + 1,
                    })

        print("\nTurn Order for this Round:")
        for i, c in enumerate(turn_order):
            print(f"  {i + 1:>2}. {c['label']} (Speed: {c['speed']})")

        input("\nPress Enter to start the round...")

        # ── Action phase ─────────────────────────────────────────────────────
        print(f"\n⚔️  Round {round_num}: Action Phase")

        defending = False   # reset every round; only protects against later slots

        for step_idx, combatant in enumerate(turn_order):
            live_enemies = prune_dead(enemies)
            if not live_enemies:
                break

            slot_label = f"[{step_idx + 1}/{len(turn_order)}]"
            print(f"\n{slot_label} {combatant['label']}'s Turn:")

            # ── Player slot ──────────────────────────────────────────────────
            if combatant["type"] == "player":
                if player["current_hp"] <= 0:
                    print("You have been slain.")
                    player["abyss_triple_actions"] = 0
                    return "dead"

                extra_turn = combatant.get("extra_turn")
                if extra_turn:
                    print(f"⚔️  ABYSS TEMPO — Extra Action {extra_turn}/3!")

                # Keep re-prompting on invalid input (retry) without
                # re-rolling initiative.
                while True:
                    result, new_def = handle_player_turn(
                        player, live_enemies, p_str, p_con, p_dex
                    )
                    if result != "retry":
                        break

                if result == "continue":
                    if new_def:
                        defending = True    # applies to later enemy slots
                    # Quick win check: did the player just kill the last enemy?
                    if not prune_dead(enemies):
                        print("\nAll enemies have been defeated!")
                        player["abyss_triple_actions"] = 0
                        return "victory"
                elif result == "victory":
                    # handle_player_turn returns "victory" when a consumable
                    # finishes off the last enemy.
                    player["abyss_triple_actions"] = 0
                    player.pop("abyss_tempo_pending", None)
                    return "victory"
                elif result in ("fled", "dead"):
                    player["abyss_triple_actions"] = 0
                    player.pop("abyss_tempo_pending", None)
                    return result

            # ── Enemy slot ───────────────────────────────────────────────────
            else:
                enemy = combatant["enemy"]
                if enemy["hp"] <= 0:
                    print(f"  ({enemy['name']} is already defeated.)")
                    continue

                extra = get_race_extra_logic(enemy)
                outcome = enemy_attack(
                    enemy, player, p_con, defending, extra_logic=extra
                )
                if outcome == "dead":
                    print("You have been slain.")
                    player["abyss_triple_actions"] = 0
                    return "dead"

        # ── End-of-round bookkeeping ─────────────────────────────────────────
        enemies = prune_dead(enemies)
        if not enemies:
            print("\nAll enemies have been defeated!")
            player["abyss_triple_actions"] = 0
            return "victory"

        # Cooldowns
        if player.get("abyss_fang_cooldown", 0) > 0:
            player["abyss_fang_cooldown"] -= 1
            if player["abyss_fang_cooldown"] == 0:
                print("⚔️  The Abyss Fang hums — its hunger is renewed.")
        if player.get("abyss_triple_actions", 0) > 0:
            player["abyss_triple_actions"] -= 1
            if player["abyss_triple_actions"] == 0:
                print("⚔️  Nightmare Tempo fades. The triple-action fury ends.")

        # Debuff / buff ticks
        msgs, died = tick_player_debuffs(player)
        for m in msgs:
            print(m)
        if died:
            print("You have been slain.")
            player["abyss_triple_actions"] = 0
            return "dead"

        for m in tick_player_buffs(player):
            print(m)

        print("\n" + "-" * 50)
        input("Press Enter to continue...")