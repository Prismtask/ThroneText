# ignis.py – Melt-Forge Golem Ignis super boss encounter
import random
from utils import clear_screen
from combat.stats import enemy_stats, compute_player_stats
from combat.player_actions import handle_player_turn
from combat.combat_ui import format_enemy_status_line, print_superboss_header, print_combat_hud
from combat.superboss_common import superboss_triple_action_loop, superboss_combat_loop
from combat.status_effects import apply_weaken, apply_bleed, format_player_status_line


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

def combat_ignis(player, floor=None):
    boss_key = "melt_forge_golem_ignis"
    boss = enemy_stats(boss_key, player)
    boss["max_hp"] = boss["hp"]
    boss["base_con_mod"] = boss["con_mod"]
    enemies = [boss]

    print("\n" + "=" * 55)
    print("The chamber floor groans under immense weight.")
    print("A featureless iron colossus rises from the forge-pit...")
    print(f"Ignis, the Melt-Forge Golem — HP: {boss['hp']}")
    print("=" * 55)
    input("Press Enter to face the Melt-Forge...")

    context = {
        "heat_level": 0,
        "melt_armor_triggered": False,
        "final_form": False
    }

    def pre_player_hook(ctx, elist):
        b = elist[0]
        if not ctx["final_form"] and b["hp"] <= int(b["max_hp"] * 0.30):
            ctx["final_form"] = True
            print("\n" + "!" * 55)
            print("[CRITICAL OVERHEATING] Ignis exceeds every thermal limit.")
            print("Slag Purge is impossible. Heat builds every turn. Double actions.")
            print("!" * 55)

        if not ctx["melt_armor_triggered"] and b["hp"] <= int(b["max_hp"] * 0.60):
            ctx["melt_armor_triggered"] = True
            result = apply_meltdown(player)
            print("\n🔥 [MELT ARMOR] Ignis vents superheated slag across the floor!")
            if result == "applied":
                print("⚠️  MELTDOWN applied — your attacks now cause self-inflicted Bleeding.")

        if ctx["final_form"]:
            ctx["heat_level"] += 1
            print(f"\n♨️  [CRITICAL OVERHEATING] Heat surges uncontrolled! heat_level → {ctx['heat_level']}")
        elif random.random() < 0.30:
            ctx["heat_level"] += 1
            print(f"\n♨️  [Heat Induction] Ignis stokes its internal furnace. heat_level → {ctx['heat_level']}")

        b["con_mod"] = max(0, int(b["base_con_mod"] * (1.0 - _heat_defense_reduction(ctx["heat_level"]))))

        if not ctx["final_form"] and ctx["heat_level"] >= 4:
            purge_dmg = int(random.randint(4, 7) * ctx["heat_level"] * _heat_damage_bonus(ctx["heat_level"]))
            ctx["heat_level"] = 0
            b["con_mod"] = b["base_con_mod"]

            print(f"\n🌋 [SLAG PURGE] Ignis discharges {purge_dmg} unblockable fire damage!")
            player["current_hp"] -= purge_dmg
            print("The slag congeals around your legs — Slowed for 2 turns!" if _apply_slow_to_player(player, 2) == "applied" else "Slag refreshes your Slow.")
            
            if player["current_hp"] <= 0: return "dead"

    def custom_hud(ctx, elist):
        hl = ctx["heat_level"]
        print(f"  Heat Level: {hl} (Ignis +{hl * 5}% damage | armor at {max(0, 100 - hl * 3)}%)")
        print_combat_hud(player, elist, header="Superboss: Melt-Forge Golem Ignis")

    def player_action_override(ctx):
        action = input("Choose: ").strip().lower()
        if action == "a" and player.get("meltdown"):
            bleed_msg = meltdown_self_bleed(player)
            if bleed_msg: print(bleed_msg)
        return action

    def enemy_turn_hook(enemy, ctx, pl, p_con, defending):
        actions = 2 if ctx["final_form"] else 1
        heat_mult = _heat_damage_bonus(ctx["heat_level"])
        
        # Calculate bonus str points instead of mutating base stats
        temp_str = int(enemy["str_mod"] * (heat_mult - 1.0))

        def ignis_extra(e, p, dmg):
            msgs = []
            if ctx["heat_level"] > 0 and dmg > 0:
                msgs.append(f"  (Heat ×{heat_mult:.2f} amplification)")
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