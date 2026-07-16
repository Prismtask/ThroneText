from combat.abyss_fang import (
    apply_abyss_tempo_round_start,
    tick_abyss_fang_cooldown,
    tick_abyssal_tempo,
    clear_abyss_fang_state,
    get_abyssal_tempo_count,
)
from combat.captain_cutlass import (
    clear_captain_cutlass_state,
    tick_captain_cutlass,
)
from combat.authors_pen import (
    snapshot_party_hp,
    compute_last_round_damage,
    tick_authors_pen_cooldown,
    clear_authors_pen_state,
)
# combat_engine.py – main combat orchestrators
import random
from combat.stats import compute_player_stats, enemy_stats
from combat.enemy_ai import enemy_attack, get_race_extra_logic
from combat.player_actions import handle_player_turn
from combat.combat_ui import (
    print_combat_hud, print_turn_order, print_round_header, print_pre_initiative_enemies
)
from combat.status_effects import tick_player_debuffs, tick_player_buffs
from combat.ally import (
    get_alive_allies, get_active_allies, compute_ally_stats, handle_ally_turn,
    auto_fill_active_slots, can_switch, swap_party_member,
)
from combat.wedding_specials import (
    begin_wedding_combat, end_wedding_combat,
    apply_wedding_combat_start, apply_wedding_end_of_round
)
from utils import format_time
from combat.combat_io import c_print, c_input, c_clear


def prune_dead(enemies):
    return [e for e in enemies if e["hp"] > 0 and not e.get("captured")]


def roll_initiative(player, enemies):
    """Return sorted turn order list including player and allies."""
    combatants = []
    p_str, p_con, p_dex, p_ler, p_wis, p_cha = compute_player_stats(player)

    # Player
    from combat.stat_milestones import get_wisdom_bonus
    from combat.black_silence_gloves import get_gloves_initiative_bonus
    from combat.status_effects import get_haste_initiative_bonus
    from wonderland_curses import roll_d20_with_looking_glass
    d20_roll, _ = roll_d20_with_looking_glass(player, verbose=False)
    player_speed = d20_roll + p_dex + get_wisdom_bonus(player) + get_gloves_initiative_bonus(player) + get_haste_initiative_bonus(player)
    combatants.append({
        "type": "player",
        "speed": player_speed,
        "label": "You",
        "entity": player,
        "extra_turn": None,
    })

    # Allies (active combat row only)
    allies = get_active_allies(player)
    for idx, ally in enumerate(allies):
        a_str, a_con, a_dex, a_ler, a_wis, a_cha = compute_ally_stats(ally)
        eff_dex = a_dex
        if ally.get("slowed"):
            eff_dex = max(-10, eff_dex - 3)
        speed = random.randint(1, 20) + eff_dex + get_wisdom_bonus(ally) + get_gloves_initiative_bonus(ally) + get_haste_initiative_bonus(ally)
        combatants.append({
            "type": "ally",
            "speed": speed,
            "label": f"{ally['name']}",
            "entity": ally,
            "extra_turn": None,
        })

    # Enemies
    pandemonium_speed_bonus = 0
    if player.get("pandemonium_curse"):
        from pandemonium_curses import get_enemy_initiative_bonus
        pandemonium_speed_bonus = get_enemy_initiative_bonus(player)

    # Wonderland Shadow: Cheshire Cat's Absence — enemy initiative bonus
    from wonderland_curses import get_shadow_initiative_bonus
    shadow_init_bonus = get_shadow_initiative_bonus(player)

    for idx, enemy in enumerate(enemies):
        eff_dex = enemy["dex_mod"]
        if enemy.get("slowed"):
            eff_dex = max(-10, eff_dex - 3)
        speed = random.randint(1, 20) + eff_dex + pandemonium_speed_bonus + shadow_init_bonus
        combatants.append({
            "type": "enemy",
            "speed": speed,
            "label": f"[{idx + 1}] {enemy['name']}",
            "entity": enemy,
            "extra_turn": None,
        })

    combatants.sort(key=lambda c: (c["speed"], random.random()), reverse=True)
    return combatants


def _get_alive_party(player):
    """Return [player] + active (front-row) alive allies."""
    party = [player]
    party.extend(get_active_allies(player))
    return party


def _tick_all_state(player):
    """Tick all combat state for player and allies. Returns 'dead' if player died from DoT, else None."""
    tick_abyss_fang_cooldown(player)
    tick_abyssal_tempo(player)
    tick_captain_cutlass(player)
    tick_authors_pen_cooldown(player)

    # Tick ally specials
    from combat.captain_cutlass import _tick_captain_cutlass_actor
    for ally in player.get("allies", []):
        if ally.get("current_hp", 0) > 0:
            tick_abyss_fang_cooldown(ally)
            tick_abyssal_tempo(ally)
            _tick_captain_cutlass_actor(ally, player_ref=player)

    from combat.skills import tick_skill_cooldowns
    tick_skill_cooldowns(player)
    for ally in player.get("allies", []):
        tick_skill_cooldowns(ally)

    if player.get("berserk_turns", 0) > 0:
        player["berserk_turns"] -= 1
        if player["berserk_turns"] == 0:
            dmg = random.randint(1, 6)
            player["current_hp"] = max(1, player["current_hp"] - dmg)
            c_print(f"  Your berserk rage subsides. You take {dmg} exhaustion damage.")
        else:
            c_print(f"  Berserk active — {player['berserk_turns']} turn(s) remaining.")

    if player.get("bloodlust_turns", 0) > 0:
        player["bloodlust_turns"] -= 1
        if player["bloodlust_turns"] == 0:
            c_print("  Your bloodlust fades. The thirst for blood subsides.")
        else:
            c_print(f"  Bloodlust active — {player['bloodlust_turns']} turn(s) remaining.")

    # ── Potion Sickness tick ──
    if player.get("potion_sickness", 0) > 0:
        player["potion_sickness"] -= 1
        if player["potion_sickness"] == 0:
            c_print("  Your stomach settles. You can use another potion.")
        else:
            c_print(f"  Potion sickness — {player['potion_sickness']} turn(s) remaining.")

    player.pop("smoke_bomb_flee", False)

    # ── Wonderland: Painting the Roses Red — reduce bleed/poison duration ──
    from wonderland_curses import get_painting_roses_reduction
    rose_reduction = get_painting_roses_reduction(player)
    if rose_reduction > 0:
        for debuff in player.get("active_debuffs", []):
            if debuff.get("type") in ("bleed", "poison"):
                debuff["remaining"] = max(1, debuff.get("remaining", 1) - int(rose_reduction))

    # ── Wonderland Shadow: Rose Wilt — extend bleed/poison duration ──
    from wonderland_curses import get_shadow_bleed_poison_extension
    rose_extension = get_shadow_bleed_poison_extension(player)
    if rose_extension > 0:
        for debuff in player.get("active_debuffs", []):
            if debuff.get("type") in ("bleed", "poison"):
                debuff["remaining"] = debuff.get("remaining", 1) + int(rose_extension)

    msgs, died = tick_player_debuffs(player)
    for m in msgs:
        c_print(m)
    if died:
        c_print("  You have been slain.")
        return "dead"

    for m in tick_player_buffs(player):
        c_print(m)

    for ally in get_alive_allies(player):
        # ── Ally Potion Sickness tick ──
        if ally.get("potion_sickness", 0) > 0:
            ally["potion_sickness"] -= 1
            if ally["potion_sickness"] == 0:
                c_print(f"  {ally['name']}'s stomach settles.")
            else:
                c_print(f"  {ally['name']} potion sickness — {ally['potion_sickness']} turn(s) remaining.")

        # Wonderland: Painting Roses for allies too
        if rose_reduction > 0:
            for debuff in ally.get("active_debuffs", []):
                if debuff.get("type") in ("bleed", "poison"):
                    debuff["remaining"] = max(1, debuff.get("remaining", 1) - int(rose_reduction))
        # Wonderland Shadow: Rose Wilt for allies too
        if rose_extension > 0:
            for debuff in ally.get("active_debuffs", []):
                if debuff.get("type") in ("bleed", "poison"):
                    debuff["remaining"] = debuff.get("remaining", 1) + int(rose_extension)
                    debuff["remaining"] = max(1, debuff.get("remaining", 1) - int(rose_reduction))
        ally_msgs, ally_died = tick_player_debuffs(ally)
        for m in ally_msgs:
            c_print(f"  {ally['name']}: {m}")
        if ally_died:
            c_print(f"  {ally['name']} succumbs to their wounds!")
        for m in tick_player_buffs(ally):
            c_print(f"  {ally['name']}: {m}")

    # Apply race passive regen (Fey, etc.)
    for ally in get_alive_allies(player):
        from combat.ally_skills import get_race_passive
        race_passive = get_race_passive(ally.get("race"))
        if race_passive:
            effect = race_passive.get("effect", {})
            if effect.get("type") == "regen":
                regen_val = int(ally["max_hp"] * effect.get("value", 0))
                if regen_val > 0:
                    old_hp = ally["current_hp"]
                    ally["current_hp"] = min(old_hp + regen_val, ally["max_hp"])
                    actual = ally["current_hp"] - old_hp
                    if actual > 0:
                        c_print(f"  [{race_passive['name']}] {ally['name']} regenerates {actual} HP.")

    apply_wedding_end_of_round(player)
    return None


def _end_combat_with_result(player, result):
    """Tick all combat state and return the requested result, unless DoT kills the player."""
    clear_abyss_fang_state(player)
    clear_authors_pen_state(player)
    # Clear Black Silence Gloves state for player
    from combat.black_silence_gloves import clear_gloves_state
    clear_gloves_state(player)
    # Clear ally specials
    for ally in player.get("allies", []):
        clear_abyss_fang_state(ally)
        clear_gloves_state(ally)
    # Reset potion sickness between combats
    player["potion_sickness"] = 0
    tick_result = _tick_all_state(player)
    return tick_result if tick_result == "dead" else result


def combat(player, enemy_keys, floor=None, room_num=None, total_rooms=None, enemies=None):
    """Generic combat loop supporting player + allies vs enemies.
    
    Args:
        enemies: Optional pre-created enemy dicts. If provided, combat uses
                 these instances directly instead of creating new ones.
    """
    # ── Reconcile vorpal skills before combat ────────────────────────────
    # Safety net: ensures all heroines' innate/learned skills match their
    # vorpal flags before combat actions are built.  This catches cases
    # where the load-time reconciliation in ensure_player_fields was missed.
    from character import _reconcile_heroine_vorpal_skills
    for ally in player.get("allies", []):
        _reconcile_heroine_vorpal_skills(ally, player)

    begin_wedding_combat(player, floor, room_num)
    try:
        return _combat_inner(player, enemy_keys, floor, room_num, total_rooms, enemies=enemies)
    finally:
        end_wedding_combat(player)


def _combat_inner(player, enemy_keys, floor=None, room_num=None, total_rooms=None, enemies=None):
    """Generic combat loop supporting player + allies vs enemies."""
    clear_abyss_fang_state(player)
    clear_captain_cutlass_state(player)
    clear_authors_pen_state(player)
    player["tarnished_jade_pins"] = 1
    player["tarnished_jade_weakened"] = False

    # Initialize Black Silence Gloves state for player
    from combat.black_silence_gloves import init_gloves_state, clear_gloves_state, _actor_has_black_silence_gloves
    if _actor_has_black_silence_gloves(player):
        init_gloves_state(player)

    # Init/clear ally specials
    for ally in player.get("allies", []):
        if ally.get("current_hp", 0) > 0:
            clear_abyss_fang_state(ally)
            # Clear cutlass state on ally (actor version)
            from combat.captain_cutlass import _clear_captain_cutlass_state_actor
            _clear_captain_cutlass_state_actor(ally, player_ref=player)
            ally["tarnished_jade_pins"] = 0
            ally["tarnished_jade_weakened"] = False
            if _actor_has_black_silence_gloves(ally):
                init_gloves_state(ally)

    if enemies is None:
        enemies = [enemy_stats(k, player) for k in enemy_keys]
    else:
        # Use provided enemies directly (GUI mode shares state)
        pass


    # --- Reset High Tide if floor changed ---
    if floor is not None and player.get("cutlass_high_tide_floor") != floor:
        player["cutlass_high_tide_stacks"] = 0
        player["cutlass_high_tide_floor"] = floor

    # --- NEW: Buff the normal enemy acting as the Floor Boss ---
    if floor is not None and room_num is not None and total_rooms is not None:
        # If it's the final room, and NOT a true boss floor (every 5th)
        if room_num == total_rooms and floor % 5 != 0 and enemies:
            main_enemy = enemies[0]
            main_enemy["name"] = f"Empowered {main_enemy['name']}"
            main_enemy["max_hp"] = int(main_enemy["max_hp"] * 1.30)
            main_enemy["hp"] = main_enemy["max_hp"]
            main_enemy["str_mod"] = int(main_enemy["str_mod"] * 1.20)
            main_enemy["con_mod"] = int(main_enemy["con_mod"] * 1.20)
            main_enemy["dex_mod"] = int(main_enemy["dex_mod"] * 1.20)

    c_print("\nEnemies approach!")
    for e in enemies:
        c_print(f"- A {e['name']} appears! (HP: {e['hp']})")

    # Auto-fill active slots from reserve if front row has gaps
    fill_msgs = auto_fill_active_slots(player)
    for m in fill_msgs:
        c_print(f"  {m}")

    c_input("Press Enter to begin...")

    apply_wedding_combat_start(player, enemies)

    round_num = 0
    while True:
        round_num += 1

        # ── Author's Pen: snapshot party HP for Rewrite damage tracking ──
        snapshot_party_hp(player)

        apply_abyss_tempo_round_start(player)
        # Apply Abyss Tempo round start for active allies too
        for ally in get_active_allies(player):
            apply_abyss_tempo_round_start(ally)

        enemies[:] = prune_dead(enemies)
        if not enemies:
            c_print("All enemies have been defeated!")
            return _end_combat_with_result(player, "victory")

        p_str, p_con, p_dex, p_ler, p_wis, p_cha = compute_player_stats(player)

        c_clear()
        time_str = format_time(player)

        print_round_header(round_num, floor=floor, room_num=room_num,
                           total_rooms=total_rooms, time_str=time_str)

        print_pre_initiative_enemies(enemies)

        # --- Tarnished Jade: turn-start pin damage ---
        from combat.tarnished_jade import apply_tarnished_jade_turn_start
        tj_triggered = apply_tarnished_jade_turn_start(player, enemies)
        if tj_triggered:
            enemies[:] = prune_dead(enemies)
            if not enemies:
                c_print("\n  All enemies have been defeated!")
                return _end_combat_with_result(player, "victory")
            c_print("\n  The divine sorrow subsides. The battle continues...")

        # --- Ally Tarnished Jade: turn-start pin damage ---
        for ally in player.get("allies", []):
            if ally.get("current_hp", 0) > 0 and ally.get("tarnished_jade_pins", 0) > 0:
                tj_triggered = apply_tarnished_jade_turn_start(ally, enemies, is_player=False)
                if tj_triggered:
                    enemies[:] = prune_dead(enemies)
                    if not enemies:
                        c_print("\n  All enemies have been defeated!")
                        return _end_combat_with_result(player, "victory")

        c_print("\n  Rolling initiative...")
        turn_order = roll_initiative(player, enemies)

        # Black Silence Gloves: First Strike detection
        from combat.black_silence_gloves import set_first_strike, _actor_has_black_silence_gloves
        if _actor_has_black_silence_gloves(player):
            # Player acts first if their entry comes before all enemies
            player_idx = next((i for i, c in enumerate(turn_order) if c["type"] == "player"), None)
            enemy_indices = [i for i, c in enumerate(turn_order) if c["type"] == "enemy"]
            is_first = player_idx is not None and (not enemy_indices or player_idx < min(enemy_indices))
            set_first_strike(player, is_first)
            if is_first:
                c_print("  🖤 Silence strikes first! +15% damage this round.")

        # Ally Black Silence Gloves: First Strike detection
        for ally in player.get("allies", []):
            if ally.get("current_hp", 0) > 0 and _actor_has_black_silence_gloves(ally):
                ally_idx = next((i for i, c in enumerate(turn_order) if c.get("entity") is ally), None)
                enemy_indices = [i for i, c in enumerate(turn_order) if c["type"] == "enemy"]
                is_first = ally_idx is not None and (not enemy_indices or ally_idx < min(enemy_indices))
                set_first_strike(ally, is_first)
                if is_first:
                    c_print(f"  🖤 {ally['name']} strikes first! +15% damage this round.")

        # Abyss Tempo: add extra player turns
        abyss_count = get_abyssal_tempo_count(player)
        if abyss_count > 0:
            first_p_idx = next((i for i, c in enumerate(turn_order)
                                if c["type"] == "player"), None)
            if first_p_idx is not None:
                base_speed = turn_order[first_p_idx]["speed"]
                for extra_num in range(1, 3):
                    turn_order.insert(first_p_idx + extra_num, {
                        "type": "player",
                        "speed": base_speed,
                        "label": "You (Abyss Extra)",
                        "entity": player,
                        "extra_turn": extra_num + 1,
                    })

        # Abyss Tempo: add extra ally turns
        for ally in get_active_allies(player):
            ally_abyss_count = get_abyssal_tempo_count(ally)
            if ally_abyss_count > 0:
                ally_idx = next((i for i, c in enumerate(turn_order)
                                    if c.get("entity") is ally), None)
                if ally_idx is not None:
                    base_speed = turn_order[ally_idx]["speed"]
                    for extra_num in range(1, 3):
                        turn_order.insert(ally_idx + extra_num, {
                            "type": "ally",
                            "speed": base_speed,
                            "label": f"{ally['name']} (Abyss Extra)",
                            "entity": ally,
                            "extra_turn": extra_num + 1,
                        })

        # Berserk: add one extra player turn
        if player.get("berserk_turns", 0) > 0:
            first_p_idx = next((i for i, c in enumerate(turn_order)
                                if c["type"] == "player"), None)
            if first_p_idx is not None:
                base_speed = turn_order[first_p_idx]["speed"]
                turn_order.insert(first_p_idx + 1, {
                    "type": "player",
                    "speed": base_speed,
                    "label": "You (Berserk)",
                    "entity": player,
                    "extra_turn": "berserk",
                })

        print_turn_order(turn_order)
        c_input("\n  Press Enter to start the round...")

        c_print(f"\n  ⚔️  ROUND {round_num}: ACTION PHASE")
        c_print("  " + "─" * 66)

        defending = False

        for step_idx, combatant in enumerate(turn_order):
            live_enemies = prune_dead(enemies)
            if not live_enemies:
                break

            # Check if party is still alive
            alive_party = _get_alive_party(player)
            if player["current_hp"] <= 0:
                c_print("\n  You have been slain.")
                return _end_combat_with_result(player, "dead")

            # Skip dead allies
            if combatant["type"] == "ally":
                ally = combatant["entity"]
                if ally.get("current_hp", 0) <= 0:
                    continue

            c_print(f"\n  [{step_idx + 1}/{len(turn_order)}] {combatant['label']}'s Turn:")

            if combatant["type"] == "player":
                if player["current_hp"] <= 0:
                    c_print("  You have been slain.")
                    return _end_combat_with_result(player, "dead")

                # Pandemonium: Echoing Madness curse — chance to skip turn
                if player.get("pandemonium_curse"):
                    from pandemonium_curses import roll_skip_turn
                    if roll_skip_turn(player):
                        c_print("  🌀  Echoing whispers overwhelm you — you lose your turn!")
                        continue

                if combatant.get("extra_turn"):
                    c_print(f"  ⚔️  ABYSS TEMPO — Extra Action {combatant['extra_turn']}/3!")

                # ── Wonderland Shadow: Down the Rabbit Hole — skip turn chance ──
                from wonderland_curses import get_shadow_skip_chance
                skip_chance = get_shadow_skip_chance(player)
                if skip_chance > 0 and random.random() < skip_chance:
                    c_print(f"\n  🕳️  The ground shifts beneath you — you lose your footing and miss your turn!")
                    continue

                while True:
                    result, new_def = handle_player_turn(
                        player, live_enemies, p_str, p_con, p_dex, p_ler, p_wis, p_cha
                    )
                    if result != "retry":
                        break

                if result == "continue":
                    if new_def:
                        defending = True
                    enemies[:] = prune_dead(enemies)
                    if not enemies:
                        c_print("\n  All enemies have been defeated!")
                        return _end_combat_with_result(player, "victory")
                elif result == "victory":
                    enemies[:] = prune_dead(enemies)
                    return _end_combat_with_result(player, "victory")
                elif result in ("fled", "dead"):
                    return _end_combat_with_result(player, result)

            elif combatant["type"] == "ally":
                ally = combatant["entity"]
                if ally.get("current_hp", 0) <= 0:
                    continue

                if combatant.get("extra_turn"):
                    c_print(f"  ⚔️  ABYSS TEMPO — {ally['name']} Extra Action {combatant['extra_turn']}/3!")

                # ── Wonderland Shadow: Down the Rabbit Hole — ally skip chance ──
                skip_chance = get_shadow_skip_chance(player)
                if skip_chance > 0 and random.random() < skip_chance:
                    c_print(f"\n  🕳️  The ground shifts beneath {ally['name']} — they stumble and miss their turn!")
                    continue

                # Player controls ally's action
                while True:
                    result = handle_ally_turn(
                        ally, player, live_enemies, p_str, p_con, p_dex, p_ler, p_wis, p_cha
                    )
                    if result != "retry":
                        break

                if result == "continue":
                    # ── Push Initiative: move enemies to bottom of turn order ──
                    if ally.get("_push_initiative_flag"):
                        ally["_push_initiative_flag"] = False
                        future_enemies = []
                        future_others = []
                        for i in range(step_idx + 1, len(turn_order)):
                            if turn_order[i]["type"] == "enemy":
                                future_enemies.append(turn_order[i])
                            else:
                                future_others.append(turn_order[i])
                        if future_enemies:
                            turn_order[step_idx + 1:] = future_others + future_enemies
                            c_print(f"\n  🌪️ {ally['name']} pushes enemies to the bottom of initiative!")
                    enemies[:] = prune_dead(enemies)
                    if not enemies:
                        c_print("\n  All enemies have been defeated!")
                        return _end_combat_with_result(player, "victory")
                elif result == "victory":
                    enemies[:] = prune_dead(enemies)
                    return _end_combat_with_result(player, "victory")
                elif result == "dead":
                    # Ally death doesn't end combat
                    pass

            else:  # enemy
                enemy = combatant["entity"]
                if enemy["hp"] <= 0:
                    c_print(f"  ({enemy['name']} is already defeated.)")
                    continue
                if enemy.get("captured"):
                    c_print(f"  ({enemy['name']} is captured and cannot act.)")
                    continue

                # Pick a target from alive party members
                alive_party = _get_alive_party(player)
                if not alive_party:
                    c_print("  Your entire party has fallen!")
                    return _end_combat_with_result(player, "dead")

                # Target selection: weighted 50% player, 50% random ally
                if len(alive_party) == 1:
                    target = alive_party[0]
                else:
                    weights = []
                    for member in alive_party:
                        if member is player:
                            weights.append(2.0)
                        else:
                            weights.append(1.0)
                    target = random.choices(alive_party, weights=weights)[0]

                # Determine if the target was defending
                is_defending = False
                if target is player:
                    is_defending = defending

                # Get target's Constitution for damage reduction
                if target is player:
                    target_con = p_con
                else:
                    a_str, a_con, a_dex, a_ler, a_wis, a_cha = compute_ally_stats(target)
                    target_con = a_con

                extra = get_race_extra_logic(enemy)
                enemy["_combat_round"] = round_num
                outcome = enemy_attack(enemy, target, target_con, is_defending, extra_logic=extra, all_enemies=enemies, actual_player=player)
                if outcome == "dead":
                    if target is player:
                        c_print("  You have been slain.")
                        return _end_combat_with_result(player, "dead")
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

        enemies[:] = prune_dead(enemies)
        if not enemies:
            c_print("\n  All enemies have been defeated!")
            return _end_combat_with_result(player, "victory")

        # Check player death after round
        if player["current_hp"] <= 0:
            c_print("\n  You have been slain.")
            return _end_combat_with_result(player, "dead")

        # ── Author's Pen: compute last round's damage for Rewrite ──
        compute_last_round_damage(player)

        tick_result = _tick_all_state(player)
        if tick_result == "dead":
            return _end_combat_with_result(player, "dead")

        c_print("\n  " + "─" * 66)
        c_input("  Press Enter to continue...")
