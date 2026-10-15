from combat.weapon.abyss_fang import (
    apply_abyss_tempo_round_start,
    tick_abyss_fang_cooldown,
    tick_abyssal_tempo,
    clear_abyss_fang_state,
    get_abyssal_tempo_count,
)
from combat.weapon.captain_cutlass import (
    clear_captain_cutlass_state,
    tick_captain_cutlass,
)
from combat.weapon.authors_pen import (
    snapshot_party_hp,
    compute_last_round_damage,
    tick_authors_pen_cooldown,
)
# combat/superboss_common.py
"""Shared functions for superboss fights, extracted to break circular imports."""

from combat.stats import compute_player_stats
from combat.enemy_ai import enemy_attack
from combat.player_actions import handle_player_turn
from combat.combat_ui import print_combat_hud, print_superboss_header, print_player_mini_hud, format_enemy_status_line, print_turn_order
from combat.status_effects import tick_player_debuffs, tick_player_buffs, try_consume_death_ward
from combat.skills import tick_skill_cooldowns
from combat.fractured_hourglass import tick_hourglass_cooldown
from combat.ally import (
    get_alive_allies, get_active_allies, compute_ally_stats, handle_ally_turn,
    reinforce_fallen_allies,
)
from combat.combat_io import c_print, c_input, c_clear
from combat.combat_engine import prune_dead, roll_initiative
from utils import display_name
import random


def superboss_triple_action_loop(player, enemies, p_str, p_con, p_dex, p_ler, p_wis, p_cha, on_kill, print_hud_func):
    triple_remaining = get_abyssal_tempo_count(player)
    if triple_remaining <= 0:
        return None

    for extra_num in range(2):
        enemies[:] = [e for e in enemies if e["hp"] > 0 and not e.get("captured")]
        if not enemies:
            return "victory"

        c_print(f"\n⚔️  ABYSS TEMPO — extra action ({extra_num + 2}/3)!")
        print_hud_func()

        action = c_input("Choose: ").strip().lower()
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
                          post_round_hook=None,
                          party_damage_hook=None):
    """
    Initiative‑based superboss combat loop with hooks for special mechanics.
    """
    on_kill_fn = (
        lambda target, elist: on_kill_hook(target, elist, context)
        if on_kill_hook else None
    )
    
    # ADD THIS WRAPPER:
    on_hit_fn = (
        lambda target, elist, attacker=None: on_player_hit_hook(target, elist, context, attacker=attacker)
        if on_player_hit_hook else None
    )
    from combat.weapon.tarnished_jade import _actor_has_tarnished_jade
    # Pins only start accumulating if the Jade is actually equipped
    player["tarnished_jade_pins"] = 1 if _actor_has_tarnished_jade(player) else 0
    player["tarnished_jade_weakened"] = False
    clear_captain_cutlass_state(player)

    # Palette's Brush + Blank Canvas Shawl state (player)
    from combat.weapon.palette_brush import init_brush_state, _actor_has_palette_brush
    from combat.weapon.blank_canvas_shawl import clear_shawl_state
    clear_shawl_state(player)
    if _actor_has_palette_brush(player):
        init_brush_state(player)

    # Prescript Ledger: clear stale state, then keep reset helper in scope
    from combat.weapon.prescript_ledger import reset_all_state as reset_prescript_state
    reset_prescript_state(player)

    # Init/clear ally unique-equipment state (mirrors combat_engine._combat_inner)
    from combat.weapon.black_silence_gloves import init_gloves_state, _actor_has_black_silence_gloves
    from combat.weapon.authors_pen import clear_authors_pen_state
    from combat.weapon.captain_cutlass import _clear_captain_cutlass_state_actor
    for ally in player.get("allies", []):
        if ally.get("current_hp", 0) > 0:
            clear_authors_pen_state(ally)
            _clear_captain_cutlass_state_actor(ally, player_ref=player)
            ally["tarnished_jade_pins"] = 1 if _actor_has_tarnished_jade(ally) else 0
            ally["tarnished_jade_weakened"] = False
            # Mirror player context onto allies (Wonderland checks, floor-tracking uniques)
            ally["floor"] = player.get("floor")
            ally["dungeon_region"] = player.get("dungeon_region")
            if _actor_has_black_silence_gloves(ally):
                init_gloves_state(ally)
            clear_shawl_state(ally)
            from combat.palette_ally import clear_palette_ally_state
            clear_palette_ally_state(ally)
            if _actor_has_palette_brush(ally):
                init_brush_state(ally)

    # Reset High Tide if floor changed
    if floor is not None and player.get("cutlass_high_tide_floor") != floor:
        player["cutlass_high_tide_stacks"] = 0
        player["cutlass_high_tide_floor"] = floor
    round_num = 0

    while True:
        round_num += 1

        apply_abyss_tempo_round_start(player)

        # ── Author's Pen: snapshot party HP for Rewrite damage tracking ──
        snapshot_party_hp(player)

        # Chronoweave Mantle: turn-start Momentum gain (player + allies)
        from combat.weapon.chronoweave import apply_chronoweave_turn_start
        apply_chronoweave_turn_start(player)
        for ally in get_active_allies(player):
            apply_chronoweave_turn_start(ally)

        enemies[:] = [e for e in enemies if e["hp"] > 0 and not e.get("captured")]
        if not enemies:
            return "victory"

        p_str, p_con, p_dex, p_ler, p_wis, p_cha = compute_player_stats(player)

        c_clear()

        c_print(f"  >> ROUND {round_num}")

        if pre_player_hook:
            result = pre_player_hook(context, enemies)
            if result in ("dead", "victory"):
                return result

        # ── Safety cap: never allow more than 5 enemies (HUD limit) ──
        MAX_COMBAT_ENEMIES = 5
        if len(enemies) > MAX_COMBAT_ENEMIES:
            # Cull lowest-HP non-boss enemies first
            non_boss = [e for e in enemies if not e.get("super_boss") and not e.get("boss")]
            non_boss.sort(key=lambda e: e.get("hp", 0))
            to_remove = len(enemies) - MAX_COMBAT_ENEMIES
            for e in non_boss[:to_remove]:
                c_print(f"\n  ⚠️  The arena cannot sustain so many foes — {e['name']} dissipates!")
                e["hp"] = 0

        enemies[:] = [e for e in enemies if e["hp"] > 0 and not e.get("captured")]
        if not enemies:
            return "victory"

        # Prescript Ledger — issue this round's Prescripts and mark the Target
        from combat.weapon.prescript_ledger import issue_prescripts
        issue_prescripts(player, enemies)

        if custom_hud_hook:
            custom_hud_hook(context, enemies)
        else:
            print_combat_hud(player, enemies, header=f"Superboss: {boss_name}")

        # --- Tarnished Jade: turn-start pin damage ---
        from combat.weapon.tarnished_jade import apply_tarnished_jade_turn_start
        tj_triggered = apply_tarnished_jade_turn_start(player, enemies)
        if tj_triggered:
            enemies[:] = [e for e in enemies if e["hp"] > 0 and not e.get("captured")]
            if not enemies:
                c_print("\n  All enemies have been defeated!")
                c_input("  Press Enter to continue...")
                return "victory"
            c_print("\n  The divine sorrow subsides. The battle continues...")

        c_print("\nInitiative Phase\nRolling speeds...")
        # Reinforcement rule (2026-10-12) — same as the standard engine loop:
        # fallen front allies are replaced by the earliest living bench ally.
        for _rmsg in reinforce_fallen_allies(player):
            c_print(f"  {_rmsg}")
        turn_order = roll_initiative(player, enemies)

        # Black Silence Gloves: First Strike detection
        from combat.weapon.black_silence_gloves import set_first_strike, _actor_has_black_silence_gloves
        if _actor_has_black_silence_gloves(player):
            # Player acts first only if they are the very first combatant (before allies too)
            player_idx = next((i for i, c in enumerate(turn_order) if c["type"] == "player"), None)
            is_first = player_idx == 0
            set_first_strike(player, is_first)
            if is_first:
                c_print("  🖤 Silence strikes first! +15% damage this round.")

        # Ally Black Silence Gloves: First Strike detection
        for ally in player.get("allies", []):
            if ally.get("current_hp", 0) > 0 and _actor_has_black_silence_gloves(ally):
                ally_idx = next((i for i, c in enumerate(turn_order) if c.get("entity") is ally), None)
                is_first = ally_idx == 0
                set_first_strike(ally, is_first)
                if is_first:
                    c_print(f"  🖤 {display_name(ally)} strikes first! +15% damage this round.")

        abyss_count = get_abyssal_tempo_count(player)
        if abyss_count > 0:
            first_p_idx = next((i for i, c in enumerate(turn_order) if c["type"] == "player"), None)
            if first_p_idx is not None:
                base_speed = turn_order[first_p_idx]["speed"]
                pname = player.get("name") or "You"
                for extra_num in range(1, 3):
                    turn_order.insert(first_p_idx + extra_num, {
                        "type": "player",
                        "speed": base_speed,
                        "label": f"{pname} (Abyss Extra {extra_num + 1}/3)",
                        "entity": player,
                        "extra_turn": extra_num + 1,
                    })

        c_print("\nTurn Order for this Round:")
        stunned_this_round = context.get("skip_player_turn", False)
        for i, c in enumerate(turn_order):
            suffix = " [STUNNED — will skip]" if stunned_this_round and c["type"] == "player" and not c.get("extra_turn") else ""
            c_print(f"  {i + 1:>2}. {c['label']} (Speed: {c['speed']}){suffix}")
        # Compact line in the standard engine's format — the GUI's CombatScreen
        # parses "Turn Order: A -> B -> ..." into the live turn-order bar. The
        # numbered list above never matched the parser, so the card used to
        # keep showing a stale speed preview all fight (2026-10-14 bug report).
        print_turn_order(turn_order)
        c_input("\nPress Enter to start the round...")

        c_print(f"\n⚔️  Round {round_num}: Action Phase")
        defending = False

        for step_idx, combatant in enumerate(turn_order):
            live_enemies = [e for e in enemies if e["hp"] > 0 and not e.get("captured")]
            if not live_enemies:
                break

            c_print(f"\n[{step_idx + 1}/{len(turn_order)}] {combatant['label']}'s Turn:")

            if combatant["type"] == "player":
                if player["current_hp"] <= 0:
                    c_print(f"{player['name']} has been slain.")
                    reset_prescript_state(player)
                    return "dead"

                if context.get("skip_player_turn") and not combatant.get("extra_turn"):
                    c_print(f"{player['name']} is stunned and cannot act!")
                    context["skip_player_turn"] = False
                    continue

                if combatant.get("extra_turn"):
                    if combatant["extra_turn"] == "advance":
                        c_print(f"⚡ ACTION ADVANCE — {combatant['label']} surges forward!")
                    else:
                        c_print(f"⚔️  ABYSS TEMPO — Extra Action {combatant['extra_turn']}/3!")

                print_player_mini_hud(player, live_enemies)

                pre_turn_enemy_hp = sum(e.get("hp", 0) for e in live_enemies if e.get("hp", 0) > 0)
                while True:
                    action = (
                        player_action_override(context)
                        if player_action_override
                        else c_input("Choose: ").strip().lower()
                    )
                    hp_before_action = {id(e): e.get("hp", 0) for e in live_enemies}
                    result, new_def = handle_player_turn(
                        player, live_enemies, p_str, p_con, p_dex, p_ler, p_wis, p_cha,
                        on_kill=on_kill_fn,
                        _action_override=action,
                    )
                    # Hit hook: fires for every enemy damaged by the action
                    # (any attack type — basic, skill, glove workshop, brush)
                    if result != "retry":
                        from combat.weapon.prescript_ledger import report_damage as report_prescript_damage
                        for e in live_enemies:
                            if hp_before_action.get(id(e), e.get("hp", 0)) > e.get("hp", 0):
                                report_prescript_damage(player, e)
                                if on_hit_fn:
                                    on_hit_fn(e, live_enemies, player)
                    if result != "retry":
                        break
                    c_print("[A]ttack  [D]efend  [F]lee  [U]se item")

                if result == "continue":
                    if new_def:
                        defending = True
                    enemies[:] = prune_dead(enemies)
                    if not enemies:
                        break
                elif result == "victory":
                    break
                elif result in ("fled", "dead"):
                    return result

                # Party damage tracking (e.g. Palette's Signature interrupt)
                if party_damage_hook:
                    post_hp = sum(e.get("hp", 0) for e in live_enemies if e.get("hp", 0) > 0)
                    dealt = max(0, pre_turn_enemy_hp - post_hp)
                    if dealt > 0:
                        party_damage_hook(dealt, context)

            elif combatant["type"] == "ally":
                ally = combatant["entity"]
                if ally.get("current_hp", 0) <= 0:
                    continue

                if combatant.get("extra_turn") == "advance":
                    c_print(f"⚡ ACTION ADVANCE — {display_name(ally)} surges forward!")
                elif combatant.get("extra_turn") == "clone":
                    c_print(f"👁️  MIRROR CLONE — {display_name(ally)} mirrors the enemy!")

                pre_turn_enemy_hp = sum(e.get("hp", 0) for e in live_enemies if e.get("hp", 0) > 0)
                while True:
                    hp_before_action = {id(e): e.get("hp", 0) for e in live_enemies}
                    result = handle_ally_turn(
                        ally, player, live_enemies, p_str, p_con, p_dex, p_ler, p_wis, p_cha,
                        on_kill=on_kill_fn,
                    )
                    # Hit hook: fires for every enemy damaged by the ally's action
                    if result != "retry":
                        from combat.weapon.prescript_ledger import report_damage as report_prescript_damage
                        for e in live_enemies:
                            if hp_before_action.get(id(e), e.get("hp", 0)) > e.get("hp", 0):
                                report_prescript_damage(ally, e)
                                if on_hit_fn:
                                    on_hit_fn(e, live_enemies, ally)
                    if result != "retry":
                        break

                if result == "continue":
                    enemies[:] = prune_dead(enemies)
                    if not enemies:
                        break
                elif result == "victory":
                    break
                elif result == "dead":
                    pass  # Ally death doesn't end combat

                # Party damage tracking (e.g. Palette's Signature interrupt)
                if party_damage_hook:
                    post_hp = sum(e.get("hp", 0) for e in live_enemies if e.get("hp", 0) > 0)
                    dealt = max(0, pre_turn_enemy_hp - post_hp)
                    if dealt > 0:
                        party_damage_hook(dealt, context)

                # Clean up clones after their turn
                if ally.get("is_clone"):
                    c_print(f"\n💨 {display_name(ally)} shatters — the mirror copy fades!")
                    if ally in player.get("allies", []):
                        player["allies"].remove(ally)

            else:  # enemy
                enemy = combatant["entity"]
                if enemy["hp"] <= 0:
                    c_print(f"  ({enemy['name']} is already defeated.)")
                    continue
                if enemy.get("captured"):
                    c_print(f"  ({enemy['name']} is captured and cannot act.)")
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
                            c_print(f"\n⚡ FAST ACTION! {enemy['name']} unleashes Action {action_idx + 1}/{actions}!")

                        # Target selection from alive party (active combat row only)
                        alive_party = [player] + get_active_allies(player)
                        if not alive_party:
                            c_print("Your entire party has fallen!")
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
                            if try_consume_death_ward(target):
                                if not target.pop("_eh_emperor_saved", False):
                                    if target is player:
                                        c_print(f"  {player['name']}'s Undying Vow flares — survival at 1 HP!")
                                    else:
                                        c_print(f"  Undying Vow holds — {target['name']} survives at 1 HP!")
                            elif target is player:
                                c_print(f"{player['name']} has been slain.")
                                return "dead"
                            else:
                                target["defeated"] = True
                                target["current_hp"] = 0
                                # Print is_defeated dialogue if available
                                from resources.enemies import ENEMIES
                                template = ENEMIES.get(target.get("key", ""), {})
                                dialogue = template.get("dialogue", {})
                                defeated_line = dialogue.get("is_defeated", f"{target['name']} has fallen!")
                                if "{name}" in defeated_line:
                                    defeated_line = defeated_line.format(name=target['name'])
                                c_print(f"  {defeated_line}")

            # Action Advance mechanic: insert extra turns for this entity
            entity = combatant["entity"]
            advances = entity.pop("action_advances", 0)
            for _ in range(advances):
                _insert_extra_turn(turn_order, step_idx, combatant)

        if post_round_hook:
            hook_result = post_round_hook(context, enemies)
            if hook_result == "dead":
                reset_prescript_state(player)
                return "dead"
            if hook_result == "spared":
                reset_prescript_state(player)
                return "spared"

        enemies[:] = [e for e in enemies if e["hp"] > 0 and not e.get("captured")]
        if not enemies:
            c_print("\n  All enemies have been defeated!")
            c_input("  Press Enter to continue...")
            reset_prescript_state(player)
            return "victory"

        # ── Prescript Ledger: round-end resolution (waive / punish / retribution / regen) ──
        from combat.weapon.prescript_ledger import evaluate_round as evaluate_prescript_round
        if evaluate_prescript_round(player, enemies) == "dead":
            reset_prescript_state(player)
            return "dead"

        tick_abyss_fang_cooldown(player, prefix="")
        tick_abyssal_tempo(player, prefix="")
        tick_captain_cutlass(player, prefix="")

        # Author's Pen: round-end damage tracking + cooldown
        compute_last_round_damage(player)
        tick_authors_pen_cooldown(player, prefix="")

        # Tick ally weapon specials (Abyss Fang, Captain's Cutlass, Abyssal Tempo)
        from combat.weapon.captain_cutlass import _tick_captain_cutlass_actor
        for ally in get_alive_allies(player):
            tick_abyss_fang_cooldown(ally, prefix="")
            tick_abyssal_tempo(ally, prefix="")
            _tick_captain_cutlass_actor(ally, player_ref=player)
            tick_authors_pen_cooldown(ally, prefix="")

        tick_skill_cooldowns(player)
        tick_hourglass_cooldown(player, prefix="")
        for ally in get_alive_allies(player):
            tick_skill_cooldowns(ally)
            tick_hourglass_cooldown(ally, prefix="")
        msgs, died = tick_player_debuffs(player)
        for m in msgs:
            c_print(m)
        if died:
            if try_consume_death_ward(player):
                if not player.pop("_eh_emperor_saved", False):
                    c_print(f"  {player['name']}'s Undying Vow flares — survival at 1 HP!")
            else:
                c_print(f"{player['name']} has been slain.")
                return "dead"

        for m in tick_player_buffs(player):
            c_print(m)

        # Tick ally debuffs/buffs
        for ally in get_alive_allies(player):
            ally_msgs, ally_died = tick_player_debuffs(ally)
            for m in ally_msgs:
                c_print(f"  {display_name(ally)}: {m}")
            if ally_died:
                if try_consume_death_ward(ally):
                    if not ally.pop("_eh_emperor_saved", False):
                        c_print(f"  Undying Vow holds — {display_name(ally)} survives at 1 HP!")
                else:
                    c_print(f"  {display_name(ally)} succumbs to their wounds!")
            for m in tick_player_buffs(ally):
                c_print(f"  {display_name(ally)}: {m}")

        c_print("\n" + "-" * 50)
        c_input("Press Enter to continue...")
