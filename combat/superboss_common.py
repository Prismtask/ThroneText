from combat.abyss_fang import (
    apply_abyss_tempo_round_start,
    tick_abyss_fang_cooldown,
    tick_abyssal_tempo,
    clear_abyss_fang_state,
    get_abyssal_tempo_count,
)
# combat/superboss_common.py
"""Shared functions for superboss fights, extracted to break circular imports."""

from combat.stats import compute_player_stats
from combat.enemy_ai import enemy_attack
from combat.player_actions import handle_player_turn
from combat.combat_ui import print_combat_hud, print_superboss_header, print_player_mini_hud, format_enemy_status_line
from combat.status_effects import tick_player_debuffs, tick_player_buffs
from combat.skills import tick_skill_cooldowns
from combat.ally import get_alive_allies, compute_ally_stats, handle_ally_turn
from utils import clear_screen
import random


def prune_dead(enemies):
    return [e for e in enemies if e["hp"] > 0]


def roll_initiative(player, enemies):
    """Return sorted turn order list including player and allies."""
    p_str, p_con, p_dex, p_ler, p_wis, p_cha = compute_player_stats(player)
    combatants = []

    # Player
    player_speed = random.randint(1, 20) + p_dex
    combatants.append({
        "type": "player",
        "speed": player_speed,
        "label": "You",
        "entity": player,
        "extra_turn": None,
    })

    # Allies
    allies = get_alive_allies(player)
    for idx, ally in enumerate(allies):
        a_str, a_con, a_dex, a_ler, a_wis, a_cha = compute_ally_stats(ally)
        eff_dex = a_dex
        if ally.get("slowed"):
            eff_dex = max(-10, eff_dex - 3)
        speed = random.randint(1, 20) + eff_dex
        combatants.append({
            "type": "ally",
            "speed": speed,
            "label": f"{ally['name']}",
            "entity": ally,
            "extra_turn": None,
        })

    # Enemies
    for idx, enemy in enumerate(enemies):
        eff_dex = enemy["dex_mod"]
        if enemy.get("slowed"):
            eff_dex = max(-10, eff_dex - 3)
        speed = random.randint(1, 20) + eff_dex
        combatants.append({
            "type": "enemy",
            "speed": speed,
            "label": f"[{idx + 1}] {enemy['name']}",
            "entity": enemy,
            "extra_turn": None,
        })

    combatants.sort(key=lambda c: (c["speed"], random.random()), reverse=True)
    return combatants


def superboss_triple_action_loop(player, enemies, p_str, p_con, p_dex, p_ler, p_wis, p_cha, on_kill, print_hud_func):
    triple_remaining = get_abyssal_tempo_count(player)
    if triple_remaining <= 0:
        return None

    for extra_num in range(2):
        enemies[:] = [e for e in enemies if e["hp"] > 0 and not e.get("captured")]
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


def _insert_extra_turn(turn_order, after_idx, source_combatant, label_suffix=" [ADVANCE]"):
    """Insert an extra turn immediately after the current combatant."""
    extra = {
        "type": source_combatant["type"],
        "speed": source_combatant["speed"],
        "label": f"{source_combatant['label']}{label_suffix}",
        "entity": source_combatant["entity"],
        "extra_turn": "advance",
    }
    turn_order.insert(after_idx + 1, extra)


def superboss_combat_loop(player, enemies, floor, boss_name, context,
                          pre_player_hook=None,
                          custom_hud_hook=None,
                          on_kill_hook=None,
                          on_player_hit_hook=None,
                          player_action_override=None,
                          enemy_turn_hook=None,
                          post_round_hook=None):
    """
    Initiative‑based superboss combat loop with hooks for special mechanics.
    """
    on_kill_fn = (
        lambda target, elist: on_kill_hook(target, elist, context)
        if on_kill_hook else None
    )
    
    # ADD THIS WRAPPER:
    on_hit_fn = (
        lambda target, elist: on_player_hit_hook(target, elist, context)
        if on_player_hit_hook else None
    )
    player["tarnished_jade_pins"] = 0
    player["tarnished_jade_weakened"] = False
    round_num = 0

    while True:
        round_num += 1

        apply_abyss_tempo_round_start(player)

        enemies[:] = [e for e in enemies if e["hp"] > 0 and not e.get("captured")]
        if not enemies:
            return "victory"

        p_str, p_con, p_dex, p_ler, p_wis, p_cha = compute_player_stats(player)

        clear_screen()

        if pre_player_hook:
            result = pre_player_hook(context, enemies)
            if result in ("dead", "victory"):
                return result

        enemies[:] = [e for e in enemies if e["hp"] > 0 and not e.get("captured")]
        if not enemies:
            return "victory"

        if custom_hud_hook:
            custom_hud_hook(context, enemies)
        else:
            print_combat_hud(player, enemies, header=f"Superboss: {boss_name}")

        # --- Tarnished Jade: turn-start pin damage ---
        from combat.tarnished_jade import apply_tarnished_jade_turn_start
        tj_triggered = apply_tarnished_jade_turn_start(player, enemies)
        if tj_triggered:
            enemies[:] = [e for e in enemies if e["hp"] > 0 and not e.get("captured")]
            if not enemies:
                print("\n  All enemies have been defeated!")
                input("  Press Enter to continue...")
                return "victory"
            print("\n  The divine sorrow subsides. The battle continues...")

        print("\nInitiative Phase\nRolling speeds...")
        turn_order = roll_initiative(player, enemies)

        abyss_count = get_abyssal_tempo_count(player)
        if abyss_count > 0:
            first_p_idx = next((i for i, c in enumerate(turn_order) if c["type"] == "player"), None)
            if first_p_idx is not None:
                base_speed = turn_order[first_p_idx]["speed"]
                for extra_num in range(1, 3):
                    turn_order.insert(first_p_idx + extra_num, {
                        "type": "player",
                        "speed": base_speed,
                        "label": f"You (Abyss Extra {extra_num + 1}/3)",
                        "entity": player,
                        "extra_turn": extra_num + 1,
                    })

        print("\nTurn Order for this Round:")
        stunned_this_round = context.get("skip_player_turn", False)
        for i, c in enumerate(turn_order):
            suffix = " [STUNNED — will skip]" if stunned_this_round and c["type"] == "player" and not c.get("extra_turn") else ""
            print(f"  {i + 1:>2}. {c['label']} (Speed: {c['speed']}){suffix}")
        input("\nPress Enter to start the round...")

        print(f"\n⚔️  Round {round_num}: Action Phase")
        defending = False

        for step_idx, combatant in enumerate(turn_order):
            live_enemies = [e for e in enemies if e["hp"] > 0 and not e.get("captured")]
            if not live_enemies:
                break

            print(f"\n[{step_idx + 1}/{len(turn_order)}] {combatant['label']}'s Turn:")

            if combatant["type"] == "player":
                if player["current_hp"] <= 0:
                    print(f"{player['name']} has been slain.")
                    return "dead"

                if context.get("skip_player_turn") and not combatant.get("extra_turn"):
                    print(f"{player['name']} is stunned and cannot act!")
                    context["skip_player_turn"] = False
                    continue

                if combatant.get("extra_turn"):
                    if combatant["extra_turn"] == "advance":
                        print(f"⚡ ACTION ADVANCE — {combatant['label']} surges forward!")
                    else:
                        print(f"⚔️  ABYSS TEMPO — Extra Action {combatant['extra_turn']}/3!")

                print_player_mini_hud(player, live_enemies)

                while True:
                    action = (
                        player_action_override(context)
                        if player_action_override
                        else input("Choose: ").strip().lower()
                    )
                    result, new_def = handle_player_turn(
                        player, live_enemies, p_str, p_con, p_dex, p_ler, p_wis, p_cha,
                        on_kill=on_kill_fn,
                        on_hit=on_hit_fn,
                        _action_override=action,
                    )
                    if result != "retry":
                        break
                    print("[A]ttack  [D]efend  [F]lee  [U]se item")

                if result == "continue":
                    if new_def:
                        defending = True
                elif result == "victory":
                    break
                elif result in ("fled", "dead"):
                    return result

            elif combatant["type"] == "ally":
                ally = combatant["entity"]
                if ally.get("current_hp", 0) <= 0:
                    continue

                if combatant.get("extra_turn") == "advance":
                    print(f"⚡ ACTION ADVANCE — {ally['name']} surges forward!")
                elif combatant.get("extra_turn") == "clone":
                    print(f"👁️  MIRROR CLONE — {ally['name']} mirrors the enemy!")

                while True:
                    result = handle_ally_turn(
                        ally, player, live_enemies, p_str, p_con, p_dex, p_ler, p_wis, p_cha,
                        on_kill=on_kill_fn,
                    )
                    if result != "retry":
                        break

                if result == "continue":
                    if not prune_dead(enemies):
                        break
                elif result == "victory":
                    break
                elif result == "dead":
                    pass  # Ally death doesn't end combat

                # Clean up clones after their turn
                if ally.get("is_clone"):
                    print(f"\n💨 {ally['name']} shatters — the mirror copy fades!")
                    if ally in player.get("allies", []):
                        player["allies"].remove(ally)

            else:  # enemy
                enemy = combatant["entity"]
                if enemy["hp"] <= 0:
                    print(f"  ({enemy['name']} is already defeated.)")
                    continue
                if enemy.get("captured"):
                    print(f"  ({enemy['name']} is captured and cannot act.)")
                    continue

                actions = 1
                skip_atk = False
                extra_logic = None
                armor_mult = 1.0
                temp_str = 0

                if enemy_turn_hook:
                    hook_res = enemy_turn_hook(enemy, context, player, p_con, defending, turn_order=turn_order, step_idx=step_idx)
                    if hook_res == "dead":
                        return "dead"
                    if hook_res:
                        actions, skip_atk, extra_logic, armor_mult, temp_str = hook_res

                if not skip_atk:
                    for action_idx in range(actions):
                        if actions > 1:
                            print(f"\n⚡ FAST ACTION! {enemy['name']} unleashes Action {action_idx + 1}/{actions}!")

                        # Target selection from alive party
                        alive_party = [player] + get_alive_allies(player)
                        if not alive_party:
                            print("Your entire party has fallen!")
                            return "dead"

                        if len(alive_party) == 1:
                            target = alive_party[0]
                        else:
                            weights = [2.0 if m is player else 1.0 for m in alive_party]
                            target = random.choices(alive_party, weights=weights)[0]

                        is_defending = (target is player and defending)
                        if target is player:
                            target_con = p_con
                        else:
                            a_str, a_con, a_dex, a_ler, a_wis, a_cha = compute_ally_stats(target)
                            target_con = a_con

                        outcome = enemy_attack(
                            enemy, target, target_con, is_defending,
                            extra_logic=extra_logic,
                            armor_mult=armor_mult,
                            temp_str_bonus=temp_str,
                            all_enemies=enemies,
                            actual_player=player,
                        )
                        if outcome == "dead":
                            if target is player:
                                print(f"{player['name']} has been slain.")
                                return "dead"
                            else:
                                print(f"  {target['name']} has fallen!")

            # Action Advance mechanic: insert extra turns for this entity
            entity = combatant["entity"]
            advances = entity.pop("action_advances", 0)
            for _ in range(advances):
                _insert_extra_turn(turn_order, step_idx, combatant)

        if post_round_hook:
            if post_round_hook(context, enemies) == "dead":
                return "dead"

        enemies[:] = [e for e in enemies if e["hp"] > 0 and not e.get("captured")]
        if not enemies:
            print("\n  All enemies have been defeated!")
            input("  Press Enter to continue...")
            return "victory"

        tick_abyss_fang_cooldown(player, prefix="")
        tick_abyssal_tempo(player, prefix="")


        tick_skill_cooldowns(player)
        for ally in get_alive_allies(player):
            tick_skill_cooldowns(ally)
        msgs, died = tick_player_debuffs(player)
        for m in msgs:
            print(m)
        if died:
            print(f"{player['name']} has been slain.")
            return "dead"

        for m in tick_player_buffs(player):
            print(m)

        # Tick ally debuffs/buffs
        for ally in get_alive_allies(player):
            ally_msgs, ally_died = tick_player_debuffs(ally)
            for m in ally_msgs:
                print(f"  {ally['name']}: {m}")
            if ally_died:
                print(f"  {ally['name']} succumbs to their wounds!")
            for m in tick_player_buffs(ally):
                print(f"  {ally['name']}: {m}")

        print("\n" + "-" * 50)
        input("Press Enter to continue...")
