# combat_engine.py – main combat orchestrators
import random
from combat.stats import compute_player_stats, enemy_stats
from combat.enemy_ai import enemy_attack, get_race_extra_logic
from combat.player_actions import handle_player_turn
from combat.combat_ui import print_superboss_header, print_player_mini_hud, format_enemy_status_line
from combat.status_effects import tick_player_debuffs, tick_player_buffs
from utils import clear_screen


def prune_dead(enemies):
    return [e for e in enemies if e["hp"] > 0]


def roll_initiative(player_dex, enemies):
    """Return sorted turn order list."""
    combatants = []

    # Player
    player_speed = random.randint(1, 20) + player_dex
    combatants.append({
        "type": "player",
        "speed": player_speed,
        "label": "You",
        "enemy": None,
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
            "enemy": enemy,
            "extra_turn": None,
        })

    combatants.sort(key=lambda c: (c["speed"], random.random()), reverse=True)
    return combatants


def combat(player, enemy_keys, floor=None, room_num=None, total_rooms=None):
    """Generic combat loop (original behaviour)."""
    player["abyss_triple_actions"] = 0
    enemies = [enemy_stats(k, player) for k in enemy_keys]

    print("\nEnemies approach!")
    for e in enemies:
        print(f"- A {e['name']} appears! (HP: {e['hp']})")
    input("Press Enter to begin...")

    round_num = 0
    while True:
        round_num += 1

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

        clear_screen()
        if floor is not None and room_num is not None and total_rooms is not None:
            from utils import format_time
            time_str = format_time(player.get("time_minutes", 0))
            print(f"Dungeon Floor {floor} - Room {room_num}/{total_rooms} "
                  f"| Turn {round_num} | Time: {time_str}")

        from combat.status_effects import format_player_status_line
        status_str = format_player_status_line(player)
        tempo_str = " [Abyssal Tempo]" if player.get("abyss_triple_actions", 0) > 0 else ""
        print(f"Your HP: {player['current_hp']} {status_str}{tempo_str}".rstrip())
        print("Enemies in the room:")
        for idx, e in enumerate(enemies):
            print(f"  [{idx + 1}] {format_enemy_status_line(e)}")

        print("\nInitiative Phase\nRolling speeds...")
        turn_order = roll_initiative(p_dex, enemies)

        abyss_count = player.get("abyss_triple_actions", 0)
        if abyss_count > 0:
            first_p_idx = next((i for i, c in enumerate(turn_order) if c["type"] == "player"), None)
            if first_p_idx is not None:
                base_speed = turn_order[first_p_idx]["speed"]
                for extra_num in range(1, 3):
                    turn_order.insert(first_p_idx + extra_num, {
                        "type": "player",
                        "speed": base_speed,
                        "label": f"You (Abyss Extra {extra_num + 1}/3)",
                        "enemy": None,
                        "extra_turn": extra_num + 1,
                    })

        print("\nTurn Order for this Round:")
        for i, c in enumerate(turn_order):
            print(f"  {i + 1:>2}. {c['label']} (Speed: {c['speed']})")
        input("\nPress Enter to start the round...")

        print(f"\n⚔️  Round {round_num}: Action Phase")
        defending = False

        for step_idx, combatant in enumerate(turn_order):
            live_enemies = prune_dead(enemies)
            if not live_enemies:
                break

            print(f"\n[{step_idx + 1}/{len(turn_order)}] {combatant['label']}'s Turn:")

            if combatant["type"] == "player":
                if player["current_hp"] <= 0:
                    print("You have been slain.")
                    player["abyss_triple_actions"] = 0
                    return "dead"

                if combatant.get("extra_turn"):
                    print(f"⚔️  ABYSS TEMPO — Extra Action {combatant['extra_turn']}/3!")

                while True:
                    result, new_def = handle_player_turn(
                        player, live_enemies, p_str, p_con, p_dex, p_ler, p_wis, p_cha
                    )
                    if result != "retry":
                        break

                if result == "continue":
                    if new_def:
                        defending = True
                    if not prune_dead(enemies):
                        print("\nAll enemies have been defeated!")
                        player["abyss_triple_actions"] = 0
                        return "victory"
                elif result == "victory":
                    player["abyss_triple_actions"] = 0
                    player.pop("abyss_tempo_pending", None)
                    return "victory"
                elif result in ("fled", "dead"):
                    player["abyss_triple_actions"] = 0
                    player.pop("abyss_tempo_pending", None)
                    return result

            else:  # enemy
                enemy = combatant["enemy"]
                if enemy["hp"] <= 0:
                    print(f"  ({enemy['name']} is already defeated.)")
                    continue

                extra = get_race_extra_logic(enemy)
                outcome = enemy_attack(enemy, player, p_con, defending, extra_logic=extra)
                if outcome == "dead":
                    print("You have been slain.")
                    player["abyss_triple_actions"] = 0
                    return "dead"

        enemies = prune_dead(enemies)
        if not enemies:
            print("\nAll enemies have been defeated!")
            player["abyss_triple_actions"] = 0
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

        print("\n" + "-" * 50)
        input("Press Enter to continue...")


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


def superboss_combat_loop(player, enemies, floor, boss_name, context,
                          pre_player_hook=None,
                          custom_hud_hook=None,
                          on_kill_hook=None,
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
    round_num = 0

    while True:
        round_num += 1

        if player.get("abyss_tempo_pending", 0) > 0:
            pending = player.pop("abyss_tempo_pending")
            player["abyss_triple_actions"] = pending
            print(f"⚔️  The Abyss awakens! Triple actions for {pending} turns!")

        enemies[:] = [e for e in enemies if e["hp"] > 0]
        if not enemies:
            return "victory"

        p_str, p_con, p_dex, p_ler, p_wis, p_cha = compute_player_stats(player)

        if pre_player_hook:
            result = pre_player_hook(context, enemies)
            if result in ("dead", "victory"):
                return result

        enemies[:] = [e for e in enemies if e["hp"] > 0]
        if not enemies:
            return "victory"

        if custom_hud_hook:
            custom_hud_hook(context, enemies)
        else:
            clear_screen()
            print_superboss_header(player, floor, boss_name, "")
            print("\nEnemies:")
            for idx, e in enumerate(enemies):
                print(f"  [{idx + 1}] {format_enemy_status_line(e)}")

        print("\nInitiative Phase\nRolling speeds...")
        turn_order = roll_initiative(p_dex, enemies)

        abyss_count = player.get("abyss_triple_actions", 0)
        if abyss_count > 0:
            first_p_idx = next((i for i, c in enumerate(turn_order) if c["type"] == "player"), None)
            if first_p_idx is not None:
                base_speed = turn_order[first_p_idx]["speed"]
                for extra_num in range(1, 3):
                    turn_order.insert(first_p_idx + extra_num, {
                        "type": "player",
                        "speed": base_speed,
                        "label": f"You (Abyss Extra {extra_num + 1}/3)",
                        "enemy": None,
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
            live_enemies = [e for e in enemies if e["hp"] > 0]
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
                        _action_override=action,
                    )
                    if result != "retry":
                        break
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

            else:  # enemy
                enemy = combatant["enemy"]
                if enemy["hp"] <= 0:
                    print(f"  ({enemy['name']} is already defeated.)")
                    continue

                actions = 1
                skip_atk = False
                extra_logic = None
                armor_mult = 1.0
                temp_str = 0

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

        if post_round_hook:
            if post_round_hook(context, enemies) == "dead":
                return "dead"

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
        for m in msgs:
            print(m)
        if died:
            print(f"{player['name']} has been slain.")
            return "dead"

        for m in tick_player_buffs(player):
            print(m)

        print("\n" + "-" * 50)
        input("Press Enter to continue...")