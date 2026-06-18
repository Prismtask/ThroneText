# combat_engine.py – main combat orchestrators
import random
from combat.stats import compute_player_stats, enemy_stats
from combat.enemy_ai import enemy_attack, get_race_extra_logic
from combat.player_actions import handle_player_turn
from combat.combat_ui import print_superboss_header, print_player_mini_hud, format_enemy_status_line
from combat.status_effects import tick_player_debuffs, tick_player_buffs
from utils import clear_screen, format_time


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