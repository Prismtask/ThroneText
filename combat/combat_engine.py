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
    get_alive_allies, compute_ally_stats, handle_ally_turn
)
from utils import clear_screen, format_time


def prune_dead(enemies):
    return [e for e in enemies if e["hp"] > 0 and not e.get("captured")]


def roll_initiative(player, enemies):
    """Return sorted turn order list including player and allies."""
    combatants = []
    p_str, p_con, p_dex, p_ler, p_wis, p_cha = compute_player_stats(player)

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


def _get_alive_party(player):
    """Return [player] + alive allies."""
    party = [player]
    party.extend(get_alive_allies(player))
    return party


def combat(player, enemy_keys, floor=None, room_num=None, total_rooms=None):
    """Generic combat loop supporting player + allies vs enemies."""
    player["abyss_triple_actions"] = 0
    enemies = [enemy_stats(k, player) for k in enemy_keys]

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
        time_str = format_time(player.get("time_minutes", 0))

        print_round_header(round_num, floor=floor, room_num=room_num,
                           total_rooms=total_rooms, time_str=time_str)

        print_pre_initiative_enemies(enemies)

        print("\n  Rolling initiative...")
        turn_order = roll_initiative(player, enemies)

        # Abyss Tempo: add extra player turns
        abyss_count = player.get("abyss_triple_actions", 0)
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
        input("\n  Press Enter to start the round...")

        print(f"\n  ⚔️  ROUND {round_num}: ACTION PHASE")
        print("  " + "─" * 66)

        defending = False

        for step_idx, combatant in enumerate(turn_order):
            live_enemies = prune_dead(enemies)
            if not live_enemies:
                break

            # Check if party is still alive
            alive_party = _get_alive_party(player)
            if player["current_hp"] <= 0:
                print("\n  You have been slain.")
                player["abyss_triple_actions"] = 0
                return "dead"

            # Skip dead allies
            if combatant["type"] == "ally":
                ally = combatant["entity"]
                if ally.get("current_hp", 0) <= 0:
                    continue

            print(f"\n  [{step_idx + 1}/{len(turn_order)}] {combatant['label']}'s Turn:")

            if combatant["type"] == "player":
                if player["current_hp"] <= 0:
                    print("  You have been slain.")
                    player["abyss_triple_actions"] = 0
                    return "dead"

                if combatant.get("extra_turn"):
                    print(f"  ⚔️  ABYSS TEMPO — Extra Action {combatant['extra_turn']}/3!")

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
                        print("\n  All enemies have been defeated!")
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

            elif combatant["type"] == "ally":
                ally = combatant["entity"]
                if ally.get("current_hp", 0) <= 0:
                    continue

                # Player controls ally's action
                while True:
                    result = handle_ally_turn(
                        ally, player, live_enemies, p_str, p_con, p_dex, p_ler, p_wis, p_cha
                    )
                    if result != "retry":
                        break

                if result == "continue":
                    if not prune_dead(enemies):
                        print("\n  All enemies have been defeated!")
                        player["abyss_triple_actions"] = 0
                        return "victory"
                elif result == "victory":
                    player["abyss_triple_actions"] = 0
                    player.pop("abyss_tempo_pending", None)
                    return "victory"
                elif result == "dead":
                    # Ally death doesn't end combat
                    pass

            else:  # enemy
                enemy = combatant["entity"]
                if enemy["hp"] <= 0:
                    print(f"  ({enemy['name']} is already defeated.)")
                    continue
                if enemy.get("captured"):
                    print(f"  ({enemy['name']} is captured and cannot act.)")
                    continue

                # Pick a target from alive party members
                alive_party = _get_alive_party(player)
                if not alive_party:
                    print("  Your entire party has fallen!")
                    player["abyss_triple_actions"] = 0
                    return "dead"

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
                outcome = enemy_attack(enemy, target, target_con, is_defending, extra_logic=extra)
                if outcome == "dead":
                    if target is player:
                        print("  You have been slain.")
                        player["abyss_triple_actions"] = 0
                        return "dead"
                    else:
                        print(f"  {target['name']} has fallen!")

        enemies = prune_dead(enemies)
        if not enemies:
            print("\n  All enemies have been defeated!")
            player["abyss_triple_actions"] = 0
            return "victory"

        # Check player death after round
        if player["current_hp"] <= 0:
            print("\n  You have been slain.")
            player["abyss_triple_actions"] = 0
            return "dead"

        if player.get("abyss_fang_cooldown", 0) > 0:
            player["abyss_fang_cooldown"] -= 1
            if player["abyss_fang_cooldown"] == 0:
                print("  ⚔️  The Abyss Fang hums — its hunger is renewed.")
        if player.get("abyss_triple_actions", 0) > 0:
            player["abyss_triple_actions"] -= 1
            if player["abyss_triple_actions"] == 0:
                print("  ⚔️  Nightmare Tempo fades. The triple-action fury ends.")

        # Tick skill cooldowns
        from combat.skills import tick_skill_cooldowns
        tick_skill_cooldowns(player)
        for ally in player.get("allies", []):
            tick_skill_cooldowns(ally)

        # Tick Berserk (Barbarian skill)
        if player.get("berserk_turns", 0) > 0:
            player["berserk_turns"] -= 1
            if player["berserk_turns"] == 0:
                dmg = random.randint(1, 6)
                player["current_hp"] = max(1, player["current_hp"] - dmg)
                print(f"  Your berserk rage subsides. You take {dmg} exhaustion damage.")
            else:
                print(f"  Berserk active — {player['berserk_turns']} turn(s) remaining.")

        # Tick Bloodlust (Barbarian skill)
        if player.get("bloodlust_turns", 0) > 0:
            player["bloodlust_turns"] -= 1
            if player["bloodlust_turns"] == 0:
                print("  Your bloodlust fades. The thirst for blood subsides.")
            else:
                print(f"  Bloodlust active — {player['bloodlust_turns']} turn(s) remaining.")

        # Clear smoke bomb flee guarantee if it wasn't used this round
        if player.pop("smoke_bomb_flee", False):
            pass  # It was already consumed during the round if used

        msgs, died = tick_player_debuffs(player)
        for m in msgs:
            print(m)
        if died:
            print("  You have been slain.")
            player["abyss_triple_actions"] = 0
            return "dead"

        for m in tick_player_buffs(player):
            print(m)

        # Tick ally debuffs/buffs (allies use player-style ticking since they have current_hp)
        for ally in get_alive_allies(player):
            ally_msgs, ally_died = tick_player_debuffs(ally)
            for m in ally_msgs:
                print(f"  {ally['name']}: {m}")
            if ally_died:
                print(f"  {ally['name']} succumbs to their wounds!")
            for m in tick_player_buffs(ally):
                print(f"  {ally['name']}: {m}")

        print("\n  " + "─" * 66)
        input("  Press Enter to continue...")
