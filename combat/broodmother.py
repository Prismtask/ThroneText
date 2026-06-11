# broodmother_combat.py – Broodmother Vileheart super boss encounter

import random
from utils import clear_screen
from combat.generic import (
    enemy_stats, compute_player_stats, handle_player_turn,
    enemy_attack, format_enemy_status_line, print_superboss_header
)
from character import player_max_hp
from combat.status_effects import (
    apply_poison, apply_curse,
    tick_enemy_debuffs, tick_player_debuffs, tick_player_buffs,
    cure_curse,
)


def combat_broodmother(player, floor=None):
    """
    Special combat for the Broodmother Vileheart super boss.
    Implements retreat at 75% HP, minion phase, enrage, double actions,
    and poison mechanics.
    Returns 'victory', 'fled', or 'dead'.
    """
    boss_key = "broodmother_vileheart"
    boss = enemy_stats(boss_key, player)
    boss["max_hp"] = boss["hp"]
    enemies = [boss]

    print("\n" + "=" * 60)
    print("The air grows thick with the stench of rot and venom.")
    print("Hundreds of tiny legs skitter in the darkness above and below.")
    print("A monstrous, bloated silhouette rises — crowned with thrashing")
    print("limbs and dripping fangs. Countless spider eyes gleam with")
    print("pure, instinctual hunger.")
    print(f"\nBroodmother Vileheart — HP: {boss['hp']}")
    print("=" * 60)
    input("\nPress Enter to face the Broodmother...")

    # Phase tracking
    boss_escaped_data = None
    minion_phase_active = False
    minion_timer = 0
    boss_enraged_turns = 0

    def _broodmother_poison(enemy, player, enemy_dmg):
        """50% chance to poison the player on any Broodmother-family hit."""
        if enemy.get("key") not in ("broodmother_vileheart", "vileheart_spiderling"):
            return None
        if random.random() >= 0.5:
            return None
        status = apply_poison(player, 4, 3)
        if status == "applied":
            return f"You are poisoned by the {enemy['name']}!"
        return f"The {enemy['name']} re-infects you!"

    while True:
        enemies = [e for e in enemies if e["hp"] > 0]
        if not enemies:
            print("Broodmother Vileheart has been defeated!")
            return "victory"
        
        clear_screen()
        p_str, p_con, p_dex = compute_player_stats(player)

        print_superboss_header(player, floor, "Broodmother Vileheart", "")

        result, defending = handle_player_turn(player, enemies, p_str, p_con, p_dex)
        if result == "retry":
            continue
        if result in ("fled", "victory", "dead"):
            return result

        # ----- SUPER BOSS PHASE CHECK (retreat at 75% HP) -----
        if not minion_phase_active and boss_escaped_data is None:
            for e in enemies[:]:
                if e.get("key") == "broodmother_vileheart" and e["hp"] <= int(e["max_hp"] * 0.75):
                    print(f"\n[GIMMICK] {e['name']} screeches and retreats into the shadows!")
                    print("Three Vileheart Spiderlings drop from the ceiling!")
                    boss_escaped_data = e
                    enemies.remove(e)
                    for _ in range(3):
                        m_stats = enemy_stats("vileheart_spiderling", player)
                        m_stats["key"] = "vileheart_spiderling"
                        m_stats["max_hp"] = m_stats["hp"]
                        enemies.append(m_stats)
                    minion_phase_active = True
                    minion_timer = 3
                    break

        # ----- ENEMY TURN PHASE -----
        for enemy in enemies[:]:
            if enemy["hp"] <= 0:
                continue

            # Check if this specific enemy is the enraged boss
            is_boss = (enemy.get("key") == "broodmother_vileheart")
            is_enraged = (is_boss and boss_enraged_turns > 0)
            
            # If enraged, it executes 2 actions, otherwise 1
            actions = 2 if is_enraged else 1

            for action_idx in range(actions):
                # ─── VISUAL INDICATOR FOR DOUBLE ATTACKS ───
                if is_enraged:
                    print(f"\n⚡ ENRAGED SPEED! {enemy['name']} unleashes Action {action_idx + 1}/2!")

                # Determine boss custom ability modifiers or generic actions
                extra = None
                if is_boss:
                    # Gimmick: Poison bite or sweeping strike logic
                    r = random.random()
                    if r < 0.4:
                        # Vile Poison Strike
                        def poison_strike_logic(dmg_taken):
                            if dmg_taken > 0:
                                p_dmg = 6 if is_enraged else 4
                                apply_poison(player, p_dmg, 3)
                                return f"🧪 Vileheart toxins seep into your veins! (Poisoned)"
                            return None
                        extra = poison_strike_logic
                    elif r < 0.7:
                        # Heavy Trample (ignores 30% armor calculation)
                        enemy["attributes"]["Strength"] += 3  # Temporary bump
                        # The base attack script handles the rest
                
                # Execute the actual health point deductions and attack printing
                outcome = enemy_attack(enemy, player, p_con, defending, extra_logic=extra)
                
                # Clean up temporary stat bumps if applicable
                if is_boss and extra is None and 0.4 <= r < 0.7:
                    enemy["attributes"]["Strength"] -= 3

                if outcome == "dead":
                    print("You have been slain.")
                    return "dead"

        # ----- END OF ROUND MAINTENANCE -----
        enemies = [e for e in enemies if e["hp"] > 0]
        if not enemies and not minion_phase_active:
            print("Broodmother Vileheart has been defeated!")
            return "victory"

        # Player status effect ticks (poison, slow)
        msgs, died = tick_player_debuffs(player)
        for m in msgs:
            print(m)
        if died:
            print("You have been slain.")
            return "dead"

        # Player buffs (HoT, etc.)
        for m in tick_player_buffs(player):
            print(m)

        # ----- MINION PHASE TIMER -----
        if minion_phase_active:
            spiderlings_alive = any(e.get("key") == "vileheart_spiderling" for e in enemies)
            if not spiderlings_alive:
                print("\n[GIMMICK] You slaughtered all spiderlings!")
                print("Broodmother Vileheart descends again, enraged by your defiance.")
                enemies.append(boss_escaped_data)
                boss_escaped_data = None
                minion_phase_active = False
            else:
                minion_timer -= 1
                if minion_timer <= 0:
                    print("\n[GIMMICK] Time's up! The remaining spiderlings retreat.")
                    print("Broodmother Vileheart ambushes you, ENRAGED with double actions for 3 turns!")
                    enemies = [e for e in enemies if e.get("key") != "vileheart_spiderling"]
                    boss_enraged_turns = 3
                    enemies.append(boss_escaped_data)
                    boss_escaped_data = None
                    minion_phase_active = False

        print("\n" + "-" * 40)
        input("Press Enter to continue.....")
        clear_screen()

        if boss_enraged_turns > 0:
            boss_enraged_turns -= 1