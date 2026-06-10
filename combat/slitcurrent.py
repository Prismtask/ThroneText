# slitcurrent_combat.py – Dream-Devouring Slitcurrent super boss encounter

import random
from utils import clear_screen
from combat.generic import (
    enemy_stats, compute_player_stats, handle_player_turn,
    format_enemy_status_line,
)
from combat.status_effects import (
    apply_poison, apply_curse,
    tick_enemy_debuffs, tick_player_debuffs, tick_player_buffs,
    cure_curse,
)


def combat_slitcurrent(player):
    boss_key = "dream_devouring_slitcurrent"
    boss = enemy_stats(boss_key, player)
    boss["max_hp"] = boss["hp"]
    enemies = [boss]

    p_str, p_con, p_dex = compute_player_stats(player)

    print("\n" + "=" * 50)
    print("The air ripples with distorted dreams... Dream-Devouring Slitcurrent rises from the abyss!")
    print(f"{boss['name']} - HP: {boss['hp']}")
    print("=" * 50)

    # ----- State variables -----
    devour_focus_stacks = 0
    floatsam_spawned = False          # spawn only once at ≤80% HP
    turn_counter = 0                  # for Nightmarish Tide
    boss_stun_turns = 0               # 2-turn stun counter
    failure_timer = 0                 # turns Floatsam have been alive without hitting 3 stacks
    boss_buff_turns = 0               # temporary all-stats buff after failure
    massive_attack_triggered = False  # prevent multiple failure triggers
    player_stunned = False

    def on_kill_floatsam(target, enemies):
        nonlocal devour_focus_stacks, failure_timer, boss_stun_turns
        if target.get("key") == "dream_floatsam":
            devour_focus_stacks += 1
            print(f"[GIMMICK] Slitcurrent devours the remains! Devour Focus +1 ({devour_focus_stacks}/3)")
            failure_timer = 0  # reset failure timer when a Floatsam dies
            if devour_focus_stacks >= 3:
                print("\n[GIMMICK] NIGHTMARE OVERLOAD! Slitcurrent is stunned for 2 turns and takes +40% damage!")
                boss_stun_turns = 2
                boss["stunned"] = True      # immediate effect
                devour_focus_stacks = 0

    while True:
        enemies = [e for e in enemies if e["hp"] > 0]
        if not enemies:
            print("Dream-Devouring Slitcurrent has been devoured by reality!")
            return "victory"
        
        p_str, p_con, p_dex = compute_player_stats(player)

        # ----- FLOATSAM SPAWN (once at ≤80% HP) -----
        if not floatsam_spawned and boss["hp"] <= boss["max_hp"] * 0.8:
            print("\n[GIMMICK] Slitcurrent shrieks and spawns 3 Dream Floatsam from the abyss!")
            for _ in range(3):
                m_stats = enemy_stats("dream_floatsam", player)
                m_stats["key"] = "dream_floatsam"
                m_stats["max_hp"] = m_stats["hp"]
                enemies.append(m_stats)
            floatsam_spawned = True
            failure_timer = 0

        # ----- Check if any Floatsam are alive -----
        floatsam_alive = any(e.get("key") == "dream_floatsam" for e in enemies)

        # ----- Failure timer (if Floatsam alive for 5+ turns without reaching 3 stacks) -----
        if floatsam_alive and not massive_attack_triggered and devour_focus_stacks < 3:
            failure_timer += 1
            if failure_timer >= 5:
                print("\n[GIMMICK] The Floatsam fester too long! Slitcurrent explodes in rage!")
                # Massive attack
                massive_dmg = random.randint(15, 25) + boss["str_mod"] - p_con
                massive_dmg = max(5, massive_dmg)
                player["current_hp"] -= massive_dmg
                print(f"Slitcurrent unleashes DREAM SURGE for {massive_dmg} damage!")
                if player["current_hp"] <= 0:
                    print("You have been slain.")
                    return "dead"
                # Clear stacks and buff boss
                devour_focus_stacks = 0
                boss_buff_turns = 2
                print("Slitcurrent gains TEMPORARY ALL-STATS BUFF for 2 turns!")
                massive_attack_triggered = True
        elif not floatsam_alive:
            failure_timer = 0           # reset if no Floatsam
            massive_attack_triggered = False

        # ----- Apply temporary boss buff (stats increase) -----
        if boss_buff_turns > 0:
            # Increase damage output
            boss["temp_str_bonus"] = 5
            boss_buff_turns -= 1
            if boss_buff_turns == 0:
                boss.pop("temp_str_bonus", None)
                print("Slitcurrent's rage subsides.")
        else:
            boss.pop("temp_str_bonus", None)

        # ----- Player turn (custom HUD shows stacks & multi-turn stun counter) -----
        if player_stunned:
            print("\nYou are STUNNED from the Nightmarish Tide and cannot act this turn!")
            input("Press Enter to yield your turn...")
            player_stunned = False # Reset the stun status
            result = "skipped"
        else:
            # Your normal input interface code here:
            print(f"\nYour HP: {player['current_hp']}")
            print("Enemies in the room:")
            for idx, e in enumerate(enemies):
                extra = ""
                if e.get("key") == "dream_devouring_slitcurrent":
                    extra = f" [Devour: {devour_focus_stacks}/3]"
                    if boss_stun_turns > 0:
                        extra += f" [Stunned: {boss_stun_turns} turns left]"
                print(f"  [{idx + 1}] {format_enemy_status_line(e, extra)}")
            print("[A]ttack  [D]efend  [F]lee  [U]se item")
            action = input("Choose: ").strip().lower()

        result, defending = handle_player_turn(
            player, enemies, p_str, p_con, p_dex,
            on_kill=on_kill_floatsam,
            _action_override=action,
        )
        if result == "retry":
            continue
        if result in ("fled", "victory", "dead"):
            return result

        # ----- INCREMENT TURN COUNTER (for Nightmarish Tide) -----
        turn_counter += 1

        # ----- ENEMY TURN PHASE -----
        for enemy in enemies[:]:
            if enemy["hp"] <= 0:
                continue

            # Process debuffs (dot, blind) – same as original
            msgs, died = tick_enemy_debuffs(enemy)
            for m in msgs:
                print(m)
            if died:
                continue

            # ----- STUN HANDLING (multi-turn) -----
            if enemy.get("key") == "dream_devouring_slitcurrent" and boss_stun_turns > 0:
                print(f"The {enemy['name']} is stunned and cannot act! ({boss_stun_turns} turns remain)")
                boss_stun_turns -= 1
                if boss_stun_turns == 0:
                    enemy["stunned"] = False
                continue
            elif enemy.get("stunned"):
                print(f"The {enemy['name']} is stunned and cannot act!")
                enemy["stunned"] = False
                continue

            # Determine attack power
            is_empowered = floatsam_alive and enemy.get("key") == "dream_devouring_slitcurrent"
            temp_bonus = enemy.get("temp_str_bonus", 0)

            # ----- NIGHTMARISH TIDE (every 3 turns, high damage + stun) -----
            if enemy.get("key") == "dream_devouring_slitcurrent" and turn_counter % 3 == 0:
                print("\n🌊 The abyss churns – NIGHTMARISH TIDE!")
                # High damage, ignores some block
                tide_dmg = random.randint(12, 20) + enemy["str_mod"] + temp_bonus - p_con
                tide_dmg = max(5, tide_dmg)
                player["current_hp"] -= tide_dmg
                print(f"Slitcurrent washes over you for {tide_dmg} damage!")
                # Apply stun to player
                player["stunned"] = True
                print("You are STUNNED and will lose your next turn!")
                player_stunned = True
                if player["current_hp"] <= 0:
                    print("You have been slain.")
                    return "dead"
                # Boss does not perform normal attack this turn
                continue

            # Normal or empowered attack
            block = p_con + (5 if defending else 0)
            base_dmg = random.randint(4, 9) if is_empowered else random.randint(2, 7)
            enemy_dmg = base_dmg + enemy["str_mod"] + temp_bonus - block
            enemy_dmg = max(0, enemy_dmg)

            if is_empowered:
                print(f"⚠️ {enemy['name']} channels abyssal power through its floatsam! (Empowered)")

            player["current_hp"] -= enemy_dmg
            if enemy_dmg > 0:
                print(f"The {enemy['name']} hits you for {enemy_dmg} damage!")
            else:
                print(f"The {enemy['name']} attacks but you block all incoming damage!")

            if player["current_hp"] <= 0:
                print("You have been slain.")
                return "dead"

            # Curse / poison (unchanged)
            if enemy.get("key") == "dream_devouring_slitcurrent" and random.random() < 0.4:
                if random.random() < 0.5:
                    poison_dmg = 5
                    apply_poison(player, poison_dmg, 3)
                    print(f"Nightmarish venom from {enemy['name']}!")
                else:
                    if apply_curse(player) == "applied":
                        print(f"A dream curse grips you from the {enemy['name']}!")

        # ----- END OF ROUND MAINTENANCE (unchanged from original) -----
        enemies = [e for e in enemies if e["hp"] > 0]
        if not enemies:
            return "victory"

        # Player debuffs (poison, slow)
        msgs, died = tick_player_debuffs(player)
        for m in msgs:
            print(m)
        if died:
            return "dead"

        for m in tick_player_buffs(player):
            print(m)

        print("\n" + "-" * 40)
        input("Press Enter to proceed to the next round...")
        clear_screen()