# ignis.py – Melt-Forge Golem Ignis super boss encounter
import random
from combat.stats import enemy_stats
from combat.combat_ui import print_combat_hud
from combat.superboss_common import superboss_combat_loop
from combat.status_effects import apply_weaken, apply_burn_to_player
from combat.combat_io import c_print, c_input
from combat.helpers import format_damage_msg


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

def combat_ignis(player, floor=None, enemies=None):
    """Superboss: Melt-Forge Golem Ignis.

    Args:
        enemies: Optional pre-created enemy list for GUI mode state sharing.
                 If provided, the first entry matching 'melt_forge_golem_ignis'
                 is used as the boss. Otherwise a new boss is created.
    """
    boss_key = "melt_forge_golem_ignis"

    if enemies is None:
        boss = enemy_stats(boss_key, player)
        boss["max_hp"] = boss["hp"]
        boss["base_con_mod"] = boss["con_mod"]
        enemies = [boss]
    else:
        # GUI mode: enemies list is shared with the CombatScreen renderer.
        # Find the boss in the pre-created list and set max_hp / base_con_mod.
        boss = None
        for e in enemies:
            if e.get("key") == boss_key:
                e["max_hp"] = e["hp"]
                e["base_con_mod"] = e["con_mod"]
                boss = e
                break
        if boss is None:
            # Fallback: create the boss if not found in the shared list
            boss = enemy_stats(boss_key, player)
            boss["max_hp"] = boss["hp"]
            boss["base_con_mod"] = boss["con_mod"]
            enemies.append(boss)

    c_print("\n" + "=" * 55)
    c_print("The chamber floor groans under immense weight.")
    c_print("A featureless iron colossus rises from the forge-pit...")
    c_print(f"Ignis, the Melt-Forge Golem — HP: {boss['hp']}")
    c_print("=" * 55)
    c_input("Press Enter to face the Melt-Forge...")

    context = {
        "heat_level": 0,
        "forge_intensifies": False,   # Phase 2: burn tier upgrades to Inferno
        "final_form": False           # Phase 3: double actions, guaranteed heat
    }

    def pre_player_hook(ctx, elist):
        b = next((e for e in elist if e.get("key") == boss_key), None)
        if b is None:
            return

        # ── Phase 3: Final Form at ≤30% HP ──
        if not ctx["final_form"] and b["hp"] <= int(b["max_hp"] * 0.30):
            ctx["final_form"] = True
            c_print("\n" + "!" * 55)
            c_print("[CRITICAL OVERHEATING] Ignis exceeds every thermal limit.")
            c_print("The forge burns white-hot. Heat builds every turn. Double actions!")
            c_print("!" * 55)

        # ── Phase 2: Forge Intensifies at ≤60% HP ──
        if not ctx["forge_intensifies"] and b["hp"] <= int(b["max_hp"] * 0.60):
            ctx["forge_intensifies"] = True
            c_print("\n💥 [FORGE INTENSIFIES] Ignis's internal furnace glows blinding white!")
            c_print("⚠️  The golem's flames intensify — its attacks now inflict INFERNO!")

        # ── Heat buildup ──
        if ctx["final_form"]:
            ctx["heat_level"] += 1
            c_print(f"\n♨️  [CRITICAL OVERHEATING] Heat surges uncontrolled! heat_level → {ctx['heat_level']}")
        elif ctx["forge_intensifies"]:
            # Phase 2: the forge stokes relentlessly — guaranteed heat every turn
            ctx["heat_level"] += 1
            c_print(f"\n♨️  [Heat Induction] The forge stokes relentlessly. heat_level → {ctx['heat_level']}")
        elif random.random() < 0.30:
            ctx["heat_level"] += 1
            c_print(f"\n♨️  [Heat Induction] Ignis stokes its internal furnace. heat_level → {ctx['heat_level']}")

        # ── Heat erodes Ignis's own armour ──
        b["con_mod"] = max(0, int(b["base_con_mod"] * (1.0 - _heat_defense_reduction(ctx["heat_level"]))))

        # ── Slag Purge: heat ≥ 4 vents in a fiery blast (suppressed in Final Form) ──
        if not ctx["final_form"] and ctx["heat_level"] >= 4:
            purge_dmg = int(random.randint(4, 7) * ctx["heat_level"] * _heat_damage_bonus(ctx["heat_level"]))
            ctx["heat_level"] = 0
            b["con_mod"] = b["base_con_mod"]

            c_print(f"\n🌋 [SLAG PURGE] " + format_damage_msg("Ignis", player['name'], purge_dmg, element="fire", skill_name="Slag Purge"))
            player["current_hp"] -= purge_dmg
            slow_result = _apply_slow_to_player(player, 2)
            c_print("The slag congeals around your legs — Slowed for 2 turns!" if slow_result == "applied" else "Slag refreshes your Slow.")

            if player["current_hp"] <= 0:
                return "dead"

    def custom_hud(ctx, elist):
        hl = ctx["heat_level"]
        if ctx["forge_intensifies"]:
            burn_label = "INFERNO"
            burn_icon = "💥"
        else:
            burn_label = "BLAZE"
            burn_icon = "🔥"
        c_print(f"  Heat Level: {hl} (Ignis +{hl * 5}% damage | armour at {max(0, 100 - hl * 3)}% | {burn_icon} {burn_label})")
        print_combat_hud(player, elist, header="Superboss: Melt-Forge Golem Ignis")

    def player_action_override(ctx):
        # No more Meltdown self-bleed — just a normal action prompt
        return c_input("Choose: ").strip().lower()

    def enemy_turn_hook(enemy, ctx, pl, p_con, defending, **kwargs):
        actions = 2 if ctx["final_form"] else 1
        heat_mult = _heat_damage_bonus(ctx["heat_level"])

        # Bonus STR from heat amplification (does not mutate base stats)
        temp_str = int(enemy["str_mod"] * (heat_mult - 1.0))

        def ignis_extra(e, p, dmg):
            msgs = []
            if ctx["heat_level"] > 0 and dmg > 0:
                msgs.append(f"  (Heat ×{heat_mult:.2f} amplification)")

            if dmg > 0:
                if ctx["forge_intensifies"] or ctx["final_form"]:
                    # ── Phase 2 & 3: apply Tier-4 INFERNO ──
                    burn_result = apply_burn_to_player(p, tier=4, duration=3)
                    if burn_result == "applied":
                        msgs.append("💥 Ignis's molten fists sear your flesh — INFERNO!")
                    elif burn_result == "upgraded":
                        msgs.append("💥 The flames erupt into an INFERNO!")
                    elif burn_result == "intensified":
                        msgs.append("☀️  INFERNO intensifies into CONFLAGRATION!")
                else:
                    # ── Phase 1: apply Tier-3 BLAZE (intensifies to Inferno on repeat) ──
                    burn_result = apply_burn_to_player(p, tier=3, duration=3)
                    if burn_result == "applied":
                        msgs.append("🔥 Ignis's heated body scorches you — BLAZE!")
                    elif burn_result == "intensified":
                        msgs.append("💥 BLAZE intensifies into INFERNO!")

            # ── Final Form: 50 % chance to Weaken on hit ──
            if ctx["final_form"] and dmg > 0 and random.random() < 0.50:
                if apply_weaken(p, str_penalty=3, duration=2) == "applied":
                    msgs.append("🔩 Ignis's blows sap your muscles — Weakened! (STR −3, 2 turns)")

            return "\n".join(msgs) if msgs else None

        return actions, False, ignis_extra, 1.0, temp_str

    return superboss_combat_loop(
        player, enemies, floor, "Melt-Forge Golem Ignis", context,
        pre_player_hook=pre_player_hook,
        custom_hud_hook=custom_hud,
        player_action_override=player_action_override,
        enemy_turn_hook=enemy_turn_hook
    )