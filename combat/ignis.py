# ignis.py – Melt-Forge Golem Ignis super boss encounter

import random
from utils import clear_screen
from combat.generic import (
    enemy_stats, compute_player_stats, handle_player_turn,
    enemy_attack, format_enemy_status_line,
)
from character import player_max_hp
from combat.status_effects import (
    apply_weaken, apply_bleed,
    tick_enemy_debuffs, tick_player_debuffs, tick_player_buffs,
)


# ---------------------------------------------------------------------------
# Meltdown helpers  (new permanent debuff, lives only in this module)
# ---------------------------------------------------------------------------

def apply_meltdown(player):
    """Mark the player with the permanent Meltdown debuff.

    Meltdown is not a timed debuff and is never removed by tick_player_debuffs.
    It is stored as a simple flag on the player dict so the attack handler
    below can check it without touching the shared status_effects module.

    Returns 'applied' or 'already_melting'.
    """
    if player.get("meltdown"):
        return "already_melting"
    player["meltdown"] = True
    return "applied"


def meltdown_self_bleed(player):
    """Called after every player physical attack when Meltdown is active.

    The degraded armor causes a small wound on each swing.
    Bleed damage scales with existing bleed stacks to avoid repeated resets
    overwriting a worse wound.  Returns a message or None.
    """
    bleed_dmg = random.randint(1, 3)
    result = apply_bleed(player, damage=bleed_dmg, duration=3)
    if result in ("applied", "refreshed"):
        return f"🔥 Your melted armor bites back — you bleed for {bleed_dmg}/round! (Meltdown)"
    return None


# ---------------------------------------------------------------------------
# Slow helper (mirrors how items apply slow to the player)
# ---------------------------------------------------------------------------

def _apply_slow_to_player(player, duration=2):
    """Apply a timed Slow debuff to the player (tick_player_debuffs handles removal)."""
    for d in player.get("active_debuffs", []):
        if d.get("type") == "slow":
            d["remaining"] = max(d["remaining"], duration)
            return "refreshed"
    player.setdefault("active_debuffs", []).append({
        "type": "slow",
        "remaining": duration,
    })
    return "applied"


# ---------------------------------------------------------------------------
# Heat-scaling helpers
# ---------------------------------------------------------------------------

def _heat_damage_bonus(heat_level):
    """Each stack adds 5% to a base multiplier (so 4 stacks = ×1.20)."""
    return 1.0 + heat_level * 0.05


def _heat_defense_reduction(heat_level):
    """Each stack reduces effective con_mod by 3% of its base value (floored)."""
    return heat_level * 0.03   # multiplier subtracted from armour fraction


# ---------------------------------------------------------------------------
# Main combat function
# ---------------------------------------------------------------------------

def combat_ignis(player):
    """
    Special combat for Ignis, the Melt-Forge Golem super boss.

    Gimmick summary
    ───────────────
    Heat Induction   – 30 % chance/turn: boss gains +1 heat_level.
                       Each stack: +5 % damage, −3 % effective con_mod.
    Melt Armor       – once at ≤ 60 % HP: applies permanent Meltdown to player.
    Slag Purge        – at heat_level ≥ 4: unblockable fire damage per cleared
                       stack (scaled by heat bonus), clears stacks, Slows player.
    Final Form        – below 30 % HP: Slag Purge disabled; +1 heat_level every
                       turn (guaranteed); permanent double action; 50 % chance
                       to Weaken on each hit.

    Returns 'victory', 'fled', or 'dead'.
    """
    boss_key = "melt_forge_golem_ignis"
    boss = enemy_stats(boss_key, player)
    boss["max_hp"] = boss["hp"]
    boss["base_con_mod"] = boss["con_mod"]   # store original for heat scaling
    enemies = [boss]

    print("\n" + "=" * 55)
    print("The chamber floor groans under immense weight.")
    print("A featureless iron colossus rises from the forge-pit,")
    print("its seams bleeding white-hot light. No words. No mercy.")
    print(f"Ignis, the Melt-Forge Golem — HP: {boss['hp']}")
    print("=" * 55)
    input("Press Enter to face the Melt-Forge...")

    # Phase state
    heat_level = 0
    melt_armor_triggered = False   # fires once at ≤ 60 % HP
    final_form = False

    while True:
        # ── Prune dead ───────────────────────────────────────────────────────
        enemies = [e for e in enemies if e["hp"] > 0]
        if not enemies:
            print("\nIgnis collapses — a white-hot avalanche of cooling slag.")
            print("The forge goes dark for the first time in centuries.")
            return "victory"

        p_str, p_con, p_dex = compute_player_stats(player)

        # ── FINAL FORM CHECK ─────────────────────────────────────────────────
        if not final_form and boss["hp"] <= int(boss["max_hp"] * 0.30):
            final_form = True
            print("\n" + "!" * 55)
            print("[CRITICAL OVERHEATING] Ignis exceeds every thermal limit.")
            print("Slag Purge is impossible — the heat is no longer cycling.")
            print("Heat builds every turn. Double actions. Relentless.")
            print("!" * 55)
            input("Press Enter...")

        # ── MELT ARMOR (once at ≤ 60 % HP) ──────────────────────────────────
        if not melt_armor_triggered and boss["hp"] <= int(boss["max_hp"] * 0.60):
            melt_armor_triggered = True
            result = apply_meltdown(player)
            print("\n🔥 [MELT ARMOR] Ignis vents superheated slag across the floor!")
            print("Your armor warps and softens. Every strike you land will tear")
            print("through the gaps in your own degraded protection.")
            if result == "applied":
                print("⚠️  MELTDOWN applied — your attacks now cause self-inflicted Bleeding.")
            input("Press Enter...")

        # ── HEAT INDUCTION (30 % chance; Final Form guarantees +1) ──────────
        if final_form:
            heat_level += 1
            print(f"\n♨️  [CRITICAL OVERHEATING] Heat surges uncontrolled! "
                  f"heat_level → {heat_level}")
        elif random.random() < 0.30:
            heat_level += 1
            print(f"\n♨️  [Heat Induction] Ignis stokes its internal furnace. "
                  f"heat_level → {heat_level}  "
                  f"(+{heat_level * 5}% dmg / armor liquefying)")

        # Recompute boss con_mod from heat scaling each turn
        raw_con = boss["base_con_mod"]
        reduction = _heat_defense_reduction(heat_level)
        boss["con_mod"] = max(0, int(raw_con * (1.0 - reduction)))

        # ── SLAG PURGE (at heat_level ≥ 4, disabled in Final Form) ──────────
        if not final_form and heat_level >= 4:
            stacks_cleared = heat_level
            # Each stack contributes flat damage scaled by the heat bonus it
            # was part of — we treat the full bonus as if all stacks fired together.
            heat_mult = _heat_damage_bonus(stacks_cleared)
            base_per_stack = random.randint(4, 7)
            purge_dmg = int(base_per_stack * stacks_cleared * heat_mult)

            heat_level = 0
            # Restore armour now that slag is vented
            boss["con_mod"] = boss["base_con_mod"]

            print(f"\n🌋 [SLAG PURGE] Ignis tears open its chest cavity!")
            print(f"  {stacks_cleared} heat stacks discharged as molten slag.")
            print(f"  {purge_dmg} unblockable fire damage — nothing shields you from this.")

            player["current_hp"] -= purge_dmg   # truly unblockable — ignore p_con

            slow_result = _apply_slow_to_player(player, duration=2)
            slow_msg = ("The slag congeals around your legs — Slowed for 2 turns!"
                        if slow_result == "applied"
                        else "The slag refreshes your Slow — still stuck.")
            print(slow_msg)

            if player["current_hp"] <= 0:
                print("The molten deluge consumes you. You have been slain.")
                return "dead"

            input("Press Enter to continue...")

        # ── PLAYER TURN ──────────────────────────────────────────────────────
        clear_screen()
        from combat.status_effects import format_player_status_line
        status_str = format_player_status_line(player)
        melt_warn = " 🔥 MELTDOWN" if player.get("meltdown") else ""
        print(f"\nYour HP: {player['current_hp']}{melt_warn} {status_str}".rstrip())
        print(f"heat_level: {heat_level}  "
              f"(Ignis +{heat_level * 5}% dmg | armor at "
              f"{max(0, 100 - heat_level * 3)}%)")

        print("\nEnemies:")
        for idx, e in enumerate(enemies):
            extra = f" [Heat: {heat_level}]" if e.get("key") == boss_key else ""
            print(f"  [{idx + 1}] {format_enemy_status_line(e, extra)}")

        print("[A]ttack  [D]efend  [F]lee  [U]se item")
        action = input("Choose: ").strip().lower()

        def on_kill_ignis(target, enemies_list):
            pass  # No special on-kill gimmick for Ignis

        # Intercept attack action to apply meltdown self-bleed
        if action == "a" and player.get("meltdown"):
            result, defending = handle_player_turn(
                player, enemies, p_str, p_con, p_dex,
                on_kill=on_kill_ignis,
                _action_override=action,
            )
            if result not in ("retry", "fled", "victory", "dead"):
                bleed_msg = meltdown_self_bleed(player)
                if bleed_msg:
                    print(bleed_msg)
                if player["current_hp"] <= 0:
                    print("The self-inflicted wounds finish you. You have been slain.")
                    return "dead"
        else:
            result, defending = handle_player_turn(
                player, enemies, p_str, p_con, p_dex,
                on_kill=on_kill_ignis,
                _action_override=action,
            )

        if result == "retry":
            continue
        if result in ("fled", "victory", "dead"):
            return result

        # Prune after player turn
        enemies = [e for e in enemies if e["hp"] > 0]
        if not enemies:
            return "victory"

        # ── ENEMY TURN PHASE ─────────────────────────────────────────────────
        actions = 2 if final_form else 1

        for action_idx in range(actions):
            if not enemies:
                break

            if final_form and actions > 1:
                print(f"\n⚙️  [CRITICAL OVERHEATING] Ignis acts relentlessly — "
                      f"Action {action_idx + 1}/2!")

            # Heat bonus applied to outgoing damage
            heat_mult = _heat_damage_bonus(heat_level)

            # Extra logic closure — captures heat_mult + final_form per action
            _heat_mult_snapshot = heat_mult
            _final_form_snapshot = final_form

            _heat_level_snapshot = heat_level

            def ignis_extra(enemy, pl, dmg_taken,
                            _hm=_heat_mult_snapshot,
                            _ff=_final_form_snapshot,
                            _hl=_heat_level_snapshot):
                msgs = []
                # Apply heat multiplier visually (damage already rolled below)
                if _hl > 0 and dmg_taken > 0:
                    msgs.append(f"  (Heat ×{_hm:.2f} amplification)")
                # Final Form: 50% Weaken on hit
                if _ff and dmg_taken > 0 and random.random() < 0.50:
                    res = apply_weaken(pl, str_penalty=3, duration=2)
                    if res == "applied":
                        msgs.append("🔩 Ignis's blows sap your muscles — Weakened! (STR −3, 2 turns)")
                    elif res == "refreshed":
                        msgs.append("🔩 The Weaken deepens — your arms grow heavier.")
                return "\n".join(msgs) if msgs else None

            # Scaled attack: temporarily boost str_mod by heat effect
            heat_str_bonus = int(boss["str_mod"] * (heat_mult - 1.0))
            boss["str_mod"] += heat_str_bonus

            outcome = enemy_attack(boss, player, p_con, defending,
                                   extra_logic=ignis_extra)

            boss["str_mod"] -= heat_str_bonus  # restore

            if outcome == "dead":
                print("Ignis's heat consumes you. You have been slain.")
                return "dead"

        # ── END-OF-ROUND MAINTENANCE ─────────────────────────────────────────
        enemies = [e for e in enemies if e["hp"] > 0]
        if not enemies:
            return "victory"

        msgs, died = tick_player_debuffs(player)
        for m in msgs:
            print(m)
        if died:
            print("You have been slain.")
            return "dead"

        for m in tick_player_buffs(player):
            print(m)

        print("\n" + "-" * 50)
        input("Press Enter to proceed to the next round...")
        clear_screen()