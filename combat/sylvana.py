# sylvana.py – Queen of Mirrors Sylvana super boss encounter

import random
from utils import clear_screen
from combat.generic import (
    enemy_stats, compute_player_stats, handle_player_turn,
    format_enemy_status_line,
)
from character import player_max_hp
from combat.status_effects import (
    apply_poison, apply_curse,
    tick_enemy_debuffs, tick_player_debuffs, tick_player_buffs,
    cure_curse, apply_weaken,
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


def _apply_blind_to_player(player):
    """Apply a 2-turn blind debuff to the player."""
    # Reuse the silence-style approach: track as a plain active_debuff
    for d in player.get("active_debuffs", []):
        if d.get("type") == "blind":
            d["remaining"] = 2
            return "refreshed"
    player.setdefault("active_debuffs", []).append({
        "type": "blind",
        "remaining": 2,
    })
    player["blinded"] = True
    return "applied"


def _tick_player_blind(player):
    """Tick the player's blind debuff. Returns list of messages."""
    messages = []
    for d in player.get("active_debuffs", [])[:]:
        if d.get("type") == "blind":
            d["remaining"] -= 1
            if d["remaining"] <= 0:
                player["active_debuffs"].remove(d)
                player["blinded"] = False
                messages.append("The illusory haze lifts from your eyes.")
    return messages


def _nullify_player_buff(player):
    """
    Null ability – remove one random active buff from the player.
    Returns a message string, or None if no buffs to remove.
    """
    buffs = player.get("active_buffs", [])
    # Filter out 'blessing' if you want to leave those untouched (optional).
    # For now, everything is fair game.
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
    _apply_blind_to_player(player)
    # Defense buff: reduces effective damage dealt to the boss for 1 round
    boss["veil_defense"] = boss.get("veil_defense", 0) + 3
    return (
        "🪞 Illusory Veil! Sylvana blurs into fractured reflections – "
        "you are Blinded and her form becomes harder to hit! (+3 defense)"
    )


# ---------------------------------------------------------------------------
# Main combat function
# ---------------------------------------------------------------------------

def combat_sylvana(player):
    """
    Special combat for Queen of Mirrors Sylvana super boss.

    Gimmick phases
    ──────────────
    • Illusory Veil    – 25% chance each turn: blind player + boss gains temp DEF.
    • Mirror Reflection – triggered at ≤ 65% HP, then every 3 turns in Final Form:
        Sylvana spawns 1 mirror copy (fake). Killing the fake = boss double-actions
        for 2 turns; killing the real one is just correct play.
    • Null             – high chance to strip one player buff.
    • Final Form       – below 30% HP: permanent double action +
        Mirror Reflection spawns 2 fakes instead of 1.

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
    mirror_phase_triggered = False      # first Mirror Reflection (≤ 65%)
    boss_double_actions = 0             # turns of double-action penalty
    final_form = False                  # activated below 30% HP
    reflection_turn_counter = 0         # used in final form for periodic re-splits
    split_active = False                # True while mirror copies are on the field

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
        # First trigger at ≤ 65% HP; after final form triggers every 3 turns
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
            # Shuffle so the real boss isn't always first
            random.shuffle(enemies)
            split_active = True
            fake_label = "two illusory copies" if num_fakes == 2 else "an illusory copy"
            print(f"\n🪞 [GIMMICK] Mirror Reflection! Sylvana fractures into {fake_label}!")
            print("One of them is the REAL Sylvana. The copies bear subtly wrong names.")
            print("Hint: look carefully at the capitalisation of each enemy's name.")
            input("Press Enter...")

        # ── PLAYER TURN ──────────────────────────────────────────────────────
        # Custom HUD for Sylvana fight
        clear_screen()
        from combat.status_effects import format_player_status_line
        status_str = format_player_status_line(player)
        blind_warn = " ⚠️ BLINDED" if player.get("blinded") else ""
        print(f"\nYour HP: {player['current_hp']}{blind_warn} {status_str}".rstrip())

        if boss_double_actions > 0:
            print(f"⚡ PENALTY: Sylvana has double-actions for {boss_double_actions} more turn(s)!")

        print("\nEnemies:")
        for idx, e in enumerate(enemies):
            extra = " [REAL]" if not e.get("is_fake") and len(enemies) > 1 else ""
            # Don't spoil it — only show [REAL] hint if player uses an item that reveals it
            # (we remove the hint above in production; kept here as a dev reminder)
            extra = ""  # Remove real-flag hint from display
            print(f"  [{idx + 1}] {format_enemy_status_line(e, extra)}")

        print("[A]ttack  [D]efend  [F]lee  [U]se item")
        action = input("Choose: ").strip().lower()

        def on_kill_sylvana(target, enemies):
            nonlocal boss_double_actions, split_active
            if target.get("is_fake"):
                print("\n🪞 That was just a mirror! Sylvana laughs as you strike the illusion.")
                print("Her rage crystalises — DOUBLE ACTIONS for 2 turns!")
                boss_double_actions += 2
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

        # Prune again after player turn
        enemies = [e for e in enemies if e["hp"] > 0]
        if not enemies:
            return "victory"

        # ── ENEMY TURN PHASE ─────────────────────────────────────────────────
        for enemy in enemies[:]:
            if enemy["hp"] <= 0:
                continue

            # Fake copy: applies blind on hit, then vanishes after attacking once
            if enemy.get("is_fake"):
                block = p_con + (5 if defending else 0)
                fake_dmg = max(0, random.randint(2, 6) + enemy["str_mod"] - block)
                player["current_hp"] -= fake_dmg
                if fake_dmg > 0:
                    print(f"\n🪞 {enemy['name']} flickers and strikes you for {fake_dmg} damage!")
                    status = _apply_blind_to_player(player)
                    if status == "applied":
                        print("The illusion's touch blinds you!")
                    else:
                        print("The illusion refreshes your blindness!")
                else:
                    print(f"\n🪞 {enemy['name']} flickers through you — you block the illusion!")
                print(f"The copy shatters after attacking!")
                enemy["hp"] = 0   # copies vanish after one attack
                if player["current_hp"] <= 0:
                    print("You have been slain.")
                    return "dead"
                continue

            # Real Sylvana
            is_sylvana_real = _is_sylvana(enemy)
            actions = 2 if (is_sylvana_real and (final_form or boss_double_actions > 0)) else 1

            for action_idx in range(actions):
                if actions > 1:
                    print(f"\n⚡ Sylvana acts with blinding speed — Action {action_idx + 1}/2!")

                # ── Illusory Veil (25% per action) ──
                veil_msg = _illusory_veil(enemy, player)
                if veil_msg:
                    print(veil_msg)

                # ── Null (70% chance) ──
                if random.random() < 0.70:
                    null_msg = _nullify_player_buff(player)
                    if null_msg:
                        print(null_msg)

                # ── Normal attack ──
                veil_def = enemy.pop("veil_defense", 0)  # consume this round's veil bonus
                block = p_con + (5 if defending else 0) + veil_def
                enemy_dmg = random.randint(3, 9) + enemy["str_mod"] - block
                enemy_dmg = max(0, enemy_dmg)
                player["current_hp"] -= enemy_dmg

                if enemy_dmg > 0:
                    print(f"The {enemy['name']} strikes you for {enemy_dmg} damage!")
                else:
                    print(f"The {enemy['name']} attacks but you weather the blow!")

                # ── Fey race passive: Silence on hit (25%) — inherited ──
                if enemy_dmg > 0 and random.random() < 0.25:
                    from combat.status_effects import apply_silence
                    res = apply_silence(player, duration=2)
                    if res == "applied":
                        print("Sylvana's fey magic seals your pack shut for 2 turns!")

                if player["current_hp"] <= 0:
                    print("You have been slain by the Queen of Mirrors.")
                    return "dead"

        # Decrement double-action penalty counter (only if the penalty was used)
        if boss_double_actions > 0 and not final_form:
            boss_double_actions -= 1
            if boss_double_actions == 0:
                print("\n✨ Sylvana's double-action fury subsides… for now.")

        # Prune vanished copies
        enemies = [e for e in enemies if e["hp"] > 0]
        if all(e.get("is_fake") for e in enemies) and enemies:
            # All remaining are fakes (shouldn't happen, but safety)
            enemies = []
        if not enemies:
            return "victory"

        # Check if split is resolved (no fakes remain)
        if split_active and not any(e.get("is_fake") for e in enemies):
            split_active = False

        # ── END-OF-ROUND MAINTENANCE ─────────────────────────────────────────
        # Player blind tick
        for m in _tick_player_blind(player):
            print(m)

        # Player debuffs (poison, bleed, etc.)
        msgs, died = tick_player_debuffs(player)
        for m in msgs:
            print(m)
        if died:
            print("You have been slain.")
            return "dead"

        # Player buffs (HoT, etc.)
        for m in tick_player_buffs(player):
            print(m)

        print("\n" + "-" * 50)
        input("Press Enter to continue...")
        clear_screen()