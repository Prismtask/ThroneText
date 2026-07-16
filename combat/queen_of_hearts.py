# combat/queen_of_hearts.py – Wonderland Superboss: Queen of Hearts (Floor 10)
#
# MECHANIC OVERVIEW:
# ─────────────────
# Single-phase fight with 2 Card Soldier minions.
#
# Royal Decree (every 3 Queen turns, cycling):
#   1. "Off with their heads!"  – Heavy physical single-target.
#      Execute: instantly kills target below 20% HP (10% if Defending).
#   2. "Painting the roses red!" – AoE bleed: 3 dmg × 3 turns to all party.
#      Unavoidable unless Defending (halved).
#   3. "All ways are my ways!"   – Self-buff: +30% damage, +15% defense, 2 turns.
#
# Card Soldiers:
#   - Queen can sacrifice a soldier to heal 15% max HP.
#   - Soldiers respawn once when Queen reaches 50% HP.
#
# Temper Tantrum (30% HP):
#   - Clears ALL buffs/debuffs on all combatants.
#   - Respawns Card Soldiers.
#   - Queen gains Haste: 2 actions/turn for 3 turns.
#
# Mercy Rule (5% HP):
#   - Fight ends automatically (victory).

import random
from combat.stats import enemy_stats, compute_player_stats
from combat.player_actions import handle_player_turn
from combat.combat_ui import format_enemy_status_line, print_superboss_header
from combat.superboss_common import superboss_combat_loop
from combat.status_effects import apply_bleed
from combat.combat_io import c_print, c_input, c_clear

# ── Boss keys ────────────────────────────────────────────────────────────────

QUEEN_KEY   = "wl_queen_of_hearts"
SOLDIER_KEY = "wl_card_soldier"

# ── Decree definitions ───────────────────────────────────────────────────────

DECREE_NAMES = [
    "Off with their heads!",
    "Painting the roses red!",
    "All ways are my ways!",
]

DECREE_DESCRIPTIONS = [
    "A heavy executioner's strike — lethal to the wounded.",
    "A bloody wave that paints all in crimson. Bleeds everyone.",
    "The Queen steels herself with royal authority.",
]


def _is_queen(e):
    return e.get("key") == QUEEN_KEY


def _is_soldier(e):
    return e.get("key") == SOLDIER_KEY


def _count_live_soldiers(enemies):
    return sum(1 for e in enemies if _is_soldier(e) and e["hp"] > 0 and not e.get("captured"))


def _spawn_soldiers(player, enemies, count=2):
    """Spawn Card Soldiers and add them to the enemy list."""
    spawned = []
    for _ in range(count):
        soldier = enemy_stats(SOLDIER_KEY, player)
        soldier["key"] = SOLDIER_KEY
        soldier["max_hp"] = soldier["hp"]
        enemies.append(soldier)
        spawned.append(soldier)
    return spawned


def combat_queen_of_hearts(player, floor=None, enemies=None):
    """Wonderland Superboss — Queen of Hearts (Floor 10).

    Args:
        enemies: Optional pre-created enemy list for GUI mode state sharing.
    """
    if floor is None:
        loc = player.get("location", "")
        floor = player.get("city_floors", {}).get(loc, {}).get("floor", 10)

    # ── Create or locate boss and minions ─────────────────────────────────
    if enemies is None:
        boss = enemy_stats(QUEEN_KEY, player)
        boss["max_hp"] = boss["hp"]
        enemies = [boss]
        _spawn_soldiers(player, enemies, 2)
    else:
        # GUI mode: locate existing boss, set max_hp
        boss = None
        for e in enemies:
            if _is_queen(e):
                e["max_hp"] = e["hp"]
                boss = e
                break
        if boss is None:
            boss = enemy_stats(QUEEN_KEY, player)
            boss["max_hp"] = boss["hp"]
            enemies.append(boss)
        # Ensure max_hp set for soldiers too
        for e in enemies:
            if _is_soldier(e):
                e["max_hp"] = e["hp"]
        # If no soldiers present, spawn them
        if _count_live_soldiers(enemies) == 0:
            _spawn_soldiers(player, enemies, 2)

    # ── Opening narration ─────────────────────────────────────────────────
    c_clear()
    c_print("=" * 60)
    c_print("You push through a hedge of perfectly manicured roses —")
    c_print("half red, half white. The gardeners flee at your approach,")
    c_print("their paintbrushes clattering to the ground.")
    c_print("")
    c_print("At the far end of the garden, on a throne of stacked playing")
    c_print("cards, sits a woman in a gown the colour of fresh-spilled")
    c_print("wine. Two Card Soldiers snap to attention at her sides.")
    c_print("")
    c_print('"WHO DARES TRAMPLE MY ROSES?"')
    c_print("=" * 60)
    c_print(f"\nQueen of Hearts — HP: {boss['hp']}")
    for e in enemies:
        if _is_soldier(e):
            c_print(f"{e['name']} — HP: {e['hp']}")
    c_input("\nPress Enter to face the Queen of Hearts...")

    # ── Combat context ────────────────────────────────────────────────────
    context = {
        "queen_actions": 0,          # how many times the Queen has acted
        "next_decree_idx": 0,        # index into DECREE_NAMES for next action
        "telegraphed_decree": None,  # (decree_idx, name) telegraphed from previous turn
        "soldiers_respawned": False, # whether 50% respawn has happened
        "temper_triggered": False,   # whether Temper Tantrum has fired
        "haste_remaining": 0,        # remaining Haste turns
    }

    # ── Hooks ─────────────────────────────────────────────────────────────

    def pre_player_hook(ctx, elist):
        """Check HP thresholds before the player acts each round."""
        queen = next((e for e in elist if _is_queen(e) and e["hp"] > 0), None)
        if queen is None:
            return None

        hp_pct = queen["hp"] / queen["max_hp"]

        # ── Mercy Rule (5% HP) ────────────────────────────────────────
        if hp_pct <= 0.05 and not queen.get("captured"):
            c_print("\n" + "─" * 50)
            c_print("The Queen throws her crown to the ground.")
            c_print("Cards scatter everywhere like startled birds.")
            c_print("")
            c_print('"Enough! ENOUGH! I\'ll behave! Just... just don\'t write me out.')
            c_print(' Do you know what happens to characters who get written out?')
            c_print(' They don\'t even get to be FOOTNOTES!"')
            c_print("")
            c_print("She sinks onto her throne, suddenly very small.")
            c_print("─" * 50)
            c_input("Press Enter...")
            queen["hp"] = 0  # Defeat the Queen
            return "victory"

        # ── Temper Tantrum (30% HP) ───────────────────────────────────
        if hp_pct <= 0.30 and not ctx["temper_triggered"]:
            ctx["temper_triggered"] = True
            c_print("\n" + "!" * 50)
            c_print('"THIS IS COMPLETELY UNACCEPTABLE!!!"')
            c_print("!" * 50)

            # Clear ALL buffs and debuffs on all combatants
            for e in elist:
                e["active_buffs"] = []
                e["active_debuffs"] = []
            player["active_buffs"] = []
            player["active_debuffs"] = []
            for ally in player.get("allies", []):
                ally["active_buffs"] = []
                ally["active_debuffs"] = []

            c_print("  ↠ All buffs and debuffs have been CLEARED!")

            # Respawn Card Soldiers
            living = _count_live_soldiers(elist)
            if living < 2:
                spawned = _spawn_soldiers(player, elist, 2 - living)
                c_print(f"  ↠ {2 - living} Card Soldiers reinforce the Queen!")
            else:
                c_print("  ↠ The Card Soldiers stand firm at her side!")

            # Queen gains Haste: 2 actions/turn for 3 turns
            ctx["haste_remaining"] = 3
            c_print("  ↠ The Queen gains HASTE (2 actions/turn) for 3 turns!")

            # Reset decree cycle
            ctx["queen_actions"] = 0
            ctx["next_decree_idx"] = 0
            ctx["telegraphed_decree"] = None

            c_input("\nPress Enter to weather the tantrum...")

        # ── 50% HP: respawn soldiers once ─────────────────────────────
        if hp_pct <= 0.50 and not ctx["soldiers_respawned"]:
            ctx["soldiers_respawned"] = True
            living = _count_live_soldiers(elist)
            if living < 2:
                spawned = _spawn_soldiers(player, elist, 2 - living)
                c_print(f'\n"SUMMON THE RESERVES!"')
                c_print(f"  ↠ {2 - living} fresh Card Soldiers march in!")
                c_input("Press Enter...")

        return None

    def enemy_turn_hook(enemy, ctx, pl, p_con, defending, **kwargs):
        """Handle Queen decrees, soldier sacrifice, and basic attacks."""
        is_queen = _is_queen(enemy)
        is_soldier = _is_soldier(enemy)

        actions = 1
        extra_logic = None
        armor_mult = 1.0
        temp_str = 0

        if is_soldier:
            # Soldiers do basic physical attacks
            return actions, False, None, armor_mult, temp_str

        if not is_queen:
            return actions, False, None, armor_mult, temp_str

        # ── Haste: extra action ─────────────────────────────────────────
        if ctx["haste_remaining"] > 0:
            actions = 2

        # ── Sacrifice check ─────────────────────────────────────────────
        queen = enemy
        hp_pct = queen["hp"] / queen["max_hp"]
        # Use the closure-captured enemies list to find live soldiers
        live_soldiers = [e for e in enemies
                         if _is_soldier(e) and e["hp"] > 0 and not e.get("captured")]

        # Sacrifice if: Queen HP < 40% AND soldiers available
        should_sacrifice = (
            hp_pct < 0.40
            and len(live_soldiers) > 0
        )

        # ── Decree turn? Every 3rd Queen action ──────────────────────────
        is_decree_turn = (ctx["queen_actions"] % 3 == 0)
        skip_default = False

        if is_decree_turn:
            decree_idx = ctx["next_decree_idx"]
            decree_name = DECREE_NAMES[decree_idx]

            # Print the decree
            c_print(f'\n  👑 Queen of Hearts decrees: "{decree_name}"')

            if decree_idx == 0:
                # "Off with their heads!" — Heavy physical single-target
                # Execute: instantly kills target below 20% HP (10% if Defending)
                def execution_strike(e, p, dmg):
                    threshold = 0.10 if defending else 0.20
                    if dmg > 0 and p["current_hp"] <= int(p.get("max_hp", p["current_hp"]) * threshold):
                        c_print(f'\n  💀 "OFF WITH YOUR HEAD!"')
                        c_print(f"  The axe falls. There is no appeal.")
                        p["current_hp"] = 0
                        return f"💀 EXECUTED!"
                    return None
                extra_logic = execution_strike
                temp_str = 4   # Heavy hit

            elif decree_idx == 1:
                # "Painting the roses red!" — AoE bleed to all party members
                def rose_bleed(e, p, dmg):
                    bleed_dmg = 3
                    dur = 3
                    if defending:
                        bleed_dmg = max(1, bleed_dmg // 2)
                        msg = f"🩸 Defended! Bleed reduced to {bleed_dmg} × {dur} turns."
                    else:
                        msg = f"🩸 Painted red! Bleed: {bleed_dmg} × {dur} turns."
                    apply_bleed(p, bleed_dmg, dur)

                    # Also bleed allies
                    for ally in player.get("allies", []):
                        if ally.get("current_hp", 0) > 0:
                            apply_bleed(ally, bleed_dmg, dur)

                    if player.get("allies"):
                        msg += " (All party members affected!)"
                    return msg
                extra_logic = rose_bleed

            elif decree_idx == 2:
                # "All ways are my ways!" — Self-buff, no attack
                c_print(f"  ↠ +30% damage, +15% defense for 2 turns!")
                queen.setdefault("active_buffs", []).append({
                    "type": "royal_decree",
                    "source": "royal_decree",
                    "remaining": 2,
                    "value": 0,
                })
                queen["_royal_dmg_buff"] = True
                queen["_royal_def_buff"] = True
                skip_default = True   # No attack this turn

            # Advance decree cycle
            ctx["next_decree_idx"] = (decree_idx + 1) % 3

        else:
            # ── Non-decree turn: sacrifice or basic attack ──────────────
            if should_sacrifice:
                victim = live_soldiers[0]
                heal_amount = int(queen["max_hp"] * 0.15)
                queen["hp"] = min(queen["max_hp"], queen["hp"] + heal_amount)
                victim["hp"] = 0
                c_print(f'\n  👑 "You! Take the fall for your Queen!"')
                c_print(f"  ↠ {victim["name"]} is sacrificed! Queen heals {heal_amount} HP.")
                skip_default = True

            elif ctx["haste_remaining"] > 0:
                temp_str = 2  # Slightly stronger during haste

        # Increment Queen's action count
        ctx["queen_actions"] += 1

        return actions, skip_default, extra_logic, armor_mult, temp_str

    def post_round_hook(ctx, elist):
        """Tick haste duration and clean up round state."""
        if ctx["haste_remaining"] > 0:
            ctx["haste_remaining"] -= 1
            if ctx["haste_remaining"] == 0:
                c_print("\n  ⏳ The Queen's Haste wears off...")

        # Tick royal decree buffs on Queen
        for e in elist:
            if _is_queen(e):
                for buff in e.get("active_buffs", []):
                    if buff.get("source") == "royal_decree":
                        buff["remaining"] -= 1
                e["active_buffs"] = [b for b in e.get("active_buffs", [])
                                     if b.get("remaining", 0) > 0]
                # Remove flag markers if buff expired
                has_decree = any(b.get("source") == "royal_decree"
                                 for b in e.get("active_buffs", []))
                if not has_decree:
                    e.pop("_royal_dmg_buff", None)
                    e.pop("_royal_def_buff", None)

    # ── Run the combat loop ────────────────────────────────────────────────
    return superboss_combat_loop(
        player, enemies, floor, "Queen of Hearts", context,
        pre_player_hook=pre_player_hook,
        enemy_turn_hook=enemy_turn_hook,
        post_round_hook=post_round_hook,
    )
