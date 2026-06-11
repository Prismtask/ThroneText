# sylvana.py – Queen of Mirrors Sylvana super boss encounter

import random
from utils import clear_screen
from combat.generic import (
    enemy_stats, compute_player_stats, handle_player_turn,
    format_enemy_status_line, print_superboss_header
)
from character import player_max_hp
from combat.status_effects import (
    apply_poison, apply_curse,
    tick_enemy_debuffs, tick_player_debuffs, tick_player_buffs,
    cure_curse, apply_weaken, format_player_status_line, apply_silence, apply_blind
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _scramble_name(name):
    """Return the name with random letters uppercased – marks the fake copy."""
    chars = list(name)
    indices = random.sample(range(len(chars)), k=max(2, len(chars) // 3))
    for i in indices:
        if chars[i].isalpha():
            chars[i] = chars[i].upper() if chars[i].islower() else chars[i].lower()
    # Guarantee at least one upper-case letter is present so it's visible
    while not any(c.isupper() for c in chars if c.isalpha()):
        idx = random.choice([i for i, c in enumerate(chars) if c.isalpha()])
        chars[idx] = chars[idx].upper()
    return "".join(chars)


def _make_fake_copy(boss):
    """Create a mirror illusion with identical stats but a scrambled name."""
    fake = dict(boss)
    fake["key"] = "sylvana_mirror_copy"
    fake["name"] = _scramble_name(boss["name"])
    fake["is_fake"] = True
    fake["hp"] = boss["hp"]
    fake["max_hp"] = boss["max_hp"]
    return fake


def _is_sylvana(e):
    return e.get("key") == "queen_of_mirrors_sylvana"

def _nullify_player_buff(player):
    """
    Null ability – remove one random active buff from the player.
    Returns a message string, or None if no buffs to remove.
    """
    buffs = player.get("active_buffs", [])
    eligible = [b for b in buffs if b.get("type") != "blessing"]
    if not eligible:
        return None
    target_buff = random.choice(eligible)
    buffs.remove(target_buff)
    label = target_buff.get("stat") or target_buff.get("type") or "buff"
    return f"✨ Sylvana's Null shatters your {label}! The enchantment unravels."

def _illusory_veil(boss, player):
    """
    25% chance per turn:
      – Blind the player
      – Give the boss a temporary defense_buff (stored on the enemy dict).
    Returns a message, or None.
    """
    if random.random() >= 0.25:
        return None
    apply_blind(player, duration=2)
    boss["veil_defense"] = boss.get("veil_defense", 0) + 3
    return (
        "🪞 Illusory Veil! Sylvana blurs into fractured reflections – "
        "you are Blinded and her form becomes harder to hit! (+3 defense)"
    )


# ---------------------------------------------------------------------------
# Main combat function
# ---------------------------------------------------------------------------

def combat_sylvana(player, floor=None):
    """
    Special combat for Queen of Mirrors Sylvana super boss.

    Gimmick phases
    ──────────────
    • Illusory Veil    – 25% chance each turn: blind player + boss gains temp DEF.
    • Mirror Reflection – triggered at ≤ 65% HP, then every 3 turns in Final Form:
        Sylvana spawns copies. Killing a fake = boss gains extra actions
        (in Final Form this becomes TRIPLE action).
    • Null             – high chance to strip one player buff.
    • Final Form       – below 30% HP: permanent double action +
        Mirror Reflection spawns 2 fakes instead of 1.
        Killing fakes in Final Form grants TRIPLE action for 2 turns.

    Returns 'victory', 'fled', or 'dead'.
    """
    boss_key = "queen_of_mirrors_sylvana"
    boss = enemy_stats(boss_key, player)
    boss["max_hp"] = boss["hp"]
    enemies = [boss]

    print("\n" + "=" * 55)
    print("A thousand reflections shatter apart and reassemble —")
    print("Queen of Mirrors Sylvana steps forward, smiling coldly.")
    print(f"{boss['name']} — HP: {boss['hp']}")
    print("=" * 55)
    input("Press Enter to face the Queen of Mirrors...")

    # Phase state
    mirror_phase_triggered = False
    boss_extra_actions = 0          # renamed for clarity - turns of extra-action penalty
    final_form = False
    reflection_turn_counter = 0
    split_active = False
    extra_actions_granted_this_round = False


    while True:
        # Prune dead enemies
        enemies = [e for e in enemies if e["hp"] > 0]
        if not enemies:
            print("\n✨ The mirrors all shatter at once. Sylvana dissipates into shards of light.")
            return "victory"

        p_str, p_con, p_dex = compute_player_stats(player)

        # ── FINAL FORM CHECK ────────────────────────────────────────────────
        if not final_form and boss["hp"] <= int(boss["max_hp"] * 0.30):
            final_form = True
            print("\n" + "!" * 55)
            print("[FINAL FORM] Sylvana screams. Every surface erupts into mirrors!")
            print("Her reflection multiplies endlessly — she is EVERYWHERE NOW.")
            print("Double actions become permanent. Reflections spawn every 3 turns.")
            print("!" * 55)
            input("Press Enter...")

        # ── MIRROR REFLECTION TRIGGER ────────────────────────────────────────
        should_spawn_reflection = False

        if not mirror_phase_triggered and boss["hp"] <= int(boss["max_hp"] * 0.65):
            should_spawn_reflection = True
            mirror_phase_triggered = True

        if final_form and not split_active:
            reflection_turn_counter += 1
            if reflection_turn_counter >= 3:
                should_spawn_reflection = True
                reflection_turn_counter = 0

        if should_spawn_reflection:
            num_fakes = 2 if final_form else 1
            for _ in range(num_fakes):
                fake = _make_fake_copy(boss)
                enemies.append(fake)
            random.shuffle(enemies)
            split_active = True
            fake_label = "two illusory copies" if num_fakes == 2 else "an illusory copy"
            print(f"\n🪞 [GIMMICK] Mirror Reflection! Sylvana fractures into {fake_label}!")
            print("One of them is the REAL Sylvana. The copies bear subtly wrong names.")
            print("Hint: look carefully at the capitalisation of each enemy's name.")
            input("Press Enter...")

        # ── PLAYER TURN ──────────────────────────────────────────────────────
        clear_screen()
        status_str = format_player_status_line(player)
        blind_warn = " ⚠️ BLINDED" if player.get("blinded") else ""

        # Action status display
        if final_form and boss_extra_actions > 0:
            action_status = f"⚡ TRIPLE ACTION ({boss_extra_actions} turn(s) left)"
        elif final_form:
            action_status = "⚡ PERMANENT DOUBLE ACTION"
        elif boss_extra_actions > 0:
            action_status = f"⚡ DOUBLE ACTION PENALTY ({boss_extra_actions} turn(s) left)"
        else:
            action_status = "Normal actions"

        print_superboss_header(player, floor, "Queen of Mirrors Sylvana", "")
        print(f"└─ {action_status}")

        if boss_extra_actions > 0:
            print(f"⚡ PENALTY: Sylvana has extra actions for {boss_extra_actions} more turn(s)!")

        print("\nEnemies:")
        for idx, e in enumerate(enemies):
            extra = ""
            print(f"  [{idx + 1}] {format_enemy_status_line(e, extra)}")

        print("[A]ttack  [D]efend  [F]lee  [U]se item")
        action = input("Choose: ").strip().lower()

        def on_kill_sylvana(target, enemies):
            nonlocal boss_extra_actions, split_active, extra_actions_granted_this_round
            if target.get("is_fake"):
                print("\n🪞 That was just a mirror! Sylvana laughs as you strike the illusion.")
                if final_form:
                    print("Her rage surges — TRIPLE ACTIONS for 2 turns!")
                else:
                    print("Her rage crystalises — DOUBLE ACTIONS for 2 turns!")
                boss_extra_actions += 2
                extra_actions_granted_this_round = True   # ← add this
            else:
                split_active = False

        result, defending = handle_player_turn(
            player, enemies, p_str, p_con, p_dex,
            on_kill=on_kill_sylvana,
            _action_override=action,
        )

        if result == "retry":
            continue
        if result in ("fled", "victory", "dead"):
            return result

        # ----- ABYSS FANG TRIPLE ACTION (Sylvana fight) -----
        triple_remaining = player.get("abyss_triple_actions", 0)
        if triple_remaining > 0 and result == "continue":
            for attack_num in range(2):
                live = [e for e in enemies if e["hp"] > 0]
                if not live:
                    break
                print(f"\n⚔️  ABYSS TEMPO — extra action ({attack_num + 2}/3)!")
                clear_screen()
                print_superboss_header(player, floor, "Queen of Mirrors Sylvana", "")
                print("\nEnemies:")
                for idx, e in enumerate(live):
                    print(f"  [{idx + 1}] {format_enemy_status_line(e)}")
                print("[A]ttack  [D]efend  [F]lee  [U]se item")
                sub_action = input("Choose: ").strip().lower()
                sub_result, _ = handle_player_turn(
                    player, live, p_str, p_con, p_dex,
                    on_kill=on_kill_sylvana,
                    _action_override=sub_action,
                )
                enemies = live
                if sub_result in ("fled", "victory", "dead"):
                    return sub_result

        # Prune again after player turn
        enemies = [e for e in enemies if e["hp"] > 0]
        if not enemies:
            return "victory"

        # ── ENEMY TURN PHASE ─────────────────────────────────────────────────
        for enemy in enemies[:]:
            if enemy["hp"] <= 0:
                continue

            # Fake copy logic
            if enemy.get("is_fake"):
                block = p_con + (5 if defending else 0)
                fake_dmg = max(0, random.randint(2, 6) + enemy["str_mod"] - block)
                player["current_hp"] -= fake_dmg
                if fake_dmg > 0:
                    print(f"\n🪞 {enemy['name']} flickers and strikes you for {fake_dmg} damage!")
                    status = apply_blind(player, duration=2)
                    if status == "applied":
                        print("The illusion's touch blinds you!")
                    else:
                        print("The illusion refreshes your blindness!")
                else:
                    print(f"\n🪞 {enemy['name']} flickers through you — you block the illusion!")
                print(f"The copy shatters after attacking!")
                enemy["hp"] = 0
                if player["current_hp"] <= 0:
                    print("You have been slain.")
                    return "dead"
                continue

            # Real Sylvana
            is_sylvana_real = _is_sylvana(enemy)

            # Determine number of actions this turn
            if final_form and boss_extra_actions > 0:
                actions = 3
            elif final_form or boss_extra_actions > 0:
                actions = 2
            else:
                actions = 1

            for action_idx in range(actions):
                if actions > 1:
                    action_label = "TRIPLE" if actions == 3 else "DOUBLE"
                    print(f"\n⚡ {action_label} ACTION — Sylvana moves ({action_idx + 1}/{actions})!")
                
                # Illusory Veil (25% per action)
                veil_msg = _illusory_veil(enemy, player)
                if veil_msg:
                    print(veil_msg)
                
                # Null (70% chance)
                if random.random() < 0.70:
                    null_msg = _nullify_player_buff(player)
                    if null_msg:
                        print(null_msg)
                
                # Normal attack
                veil_def = enemy.pop("veil_defense", 0)
                block = p_con + (5 if defending else 0) + veil_def
                enemy_dmg = random.randint(3, 9) + enemy["str_mod"] - block
                enemy_dmg = max(0, enemy_dmg)
                player["current_hp"] -= enemy_dmg
                
                if enemy_dmg > 0:
                    print(f"The {enemy['name']} strikes you for {enemy_dmg} damage!")
                else:
                    print(f"The {enemy['name']} attacks but you weather the blow!")
                
                # Fey race passive: Silence on hit (25%)
                if enemy_dmg > 0 and random.random() < 0.25:
                    from combat.status_effects import apply_silence
                    res = apply_silence(player, duration=2)
                    if res == "applied":
                        print("Sylvana's fey magic seals your pack shut for 2 turns!")
                
                if player["current_hp"] <= 0:
                    print("You have been slain by the Queen of Mirrors.")
                    return "dead"

        # Decrement extra-action counter AFTER the full enemy phase
        if boss_extra_actions > 0 and not extra_actions_granted_this_round:
            boss_extra_actions -= 1
            if boss_extra_actions == 0:
                print("\n✨ Sylvana's extra fury subsides...")
        extra_actions_granted_this_round = False

        # Prune vanished copies
        enemies = [e for e in enemies if e["hp"] > 0]
        if all(e.get("is_fake") for e in enemies) and enemies:
            enemies = []
        if not enemies:
            return "victory"

        # Check if split is resolved
        if split_active and not any(e.get("is_fake") for e in enemies):
            split_active = False

        # ── END-OF-ROUND MAINTENANCE ─────────────────────────────────────────
        # Tick Abyss Fang cooldown and triple-action counter
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
            return "dead"

        for m in tick_player_buffs(player):
            print(m)

        print("\n" + "-" * 50)
        input("Press Enter to continue...")
        clear_screen()