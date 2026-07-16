# combat/black_silence.py
"""The Black Silence — Superboss encounter.

Three-phase fight with 9 workshop attacks, revival mechanic, and Furioso.
Uses the same 9 workshops the player's Black Silence Gloves would grant.
"""

import random
from combat.stats import enemy_stats, compute_player_stats
from combat.player_actions import handle_player_turn
from combat.combat_ui import format_enemy_status_line, print_superboss_header, print_combat_hud
from combat.superboss_common import superboss_combat_loop
from combat.status_effects import apply_bleed
from combat.helpers import format_damage_msg
from combat.combat_io import c_print, c_input

# ═══════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════

BOSS_KEY = "black_silence"

# Workshop definitions (mirrors player gloves)
# Format: (name, scaling_stat, target_mode, dmg_mult, special_effect_desc)
WORKSHOP_DEFS = {
    1: {"name": "Allas Workshop",       "stat": "str", "target": "single", "mult": 1.40},
    2: {"name": "Wheels Industry",      "stat": "str", "target": "aoe",    "mult": 0.80},
    3: {"name": "Zelkova Workshop",     "stat": "dex", "target": "single", "mult": 1.00, "double_hit": True},
    4: {"name": "Old Boys Workshop",    "stat": "str", "target": "single", "mult": 1.20},
    5: {"name": "Mook Workshop",        "stat": "wis", "target": "aoe",    "mult": 0.70},
    6: {"name": "Ranga Workshop",       "stat": "dex", "target": "single", "mult": 1.20},
    7: {"name": "Crystal Atelier",      "stat": "dex", "target": "single", "mult": 1.10},
    8: {"name": "Atelier Logic",        "stat": "wis", "target": "single", "mult": 2.20},
    9: {"name": "Durandal",             "stat": "ler", "target": "random3", "mult": 0.90},
}

ALL_WORKSHOP_IDS = list(range(1, 10))

# Phase configs
PHASE1_WORKSHOP_COUNT = 4
PHASE2_WORKSHOP_COUNT = 6
PHASE3_WORKSHOP_COUNT = 9
PHASE2_DEX_BONUS = 2
REVIVAL_HP_PCT = 0.55
FURIOSO_TIMER_MAX = 4


# ═══════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════

def _get_boss(elist):
    return next((e for e in elist if e.get("key") == BOSS_KEY), None)


def _get_boss_stat(boss, stat_key):
    """Get effective stat: str_mod, dex_mod, wis_mod, ler_mod"""
    if stat_key == "str":
        return boss.get("str_mod", 0)
    elif stat_key == "dex":
        return boss.get("dex_mod", 0)
    elif stat_key == "wis":
        return 4  # Boss has 4 base Wisdom
    elif stat_key == "ler":
        return 8  # Boss has 8 base Learning
    return 0


def _reroll_workshops(ctx):
    """Re-roll available workshops based on current phase."""
    phase = ctx["phase"]
    if phase == 1:
        count = PHASE1_WORKSHOP_COUNT
    elif phase == 2:
        count = PHASE2_WORKSHOP_COUNT
    else:
        count = PHASE3_WORKSHOP_COUNT

    ctx["workshops_available"] = random.sample(ALL_WORKSHOP_IDS, min(count, len(ALL_WORKSHOP_IDS)))
    ctx["workshops_used_this_cycle"] = []
    ctx["cycle_turns_remaining"] = 2
    if ctx["phase"] >= 2:
        ctx["cycle_turns_remaining"] = 2  # same cycle length


def _select_workshop(ctx, boss, player, previous_pick=None):
    """AI decision for which workshop to use."""
    phase = ctx["phase"]
    available = [w for w in ctx.get("workshops_available", [])
                 if w != previous_pick and w not in ctx.get("workshops_used_this_cycle", [])]

    if not available:
        # If all available workshops used this cycle, pick from all available
        available = [w for w in ctx.get("workshops_available", []) if w != previous_pick]
    if not available:
        return None

    boss_hp_pct = boss["hp"] / boss.get("max_hp", 1)
    player_hp_pct = player["current_hp"] / max(1, player.get("max_hp", 1))
    player_defending = player.get("_defending", False)

    # Phase 1 & 2 AI priorities
    # Priority 1: Mook (5) if boss is injured
    if boss_hp_pct < 0.30 and 5 in available:
        return 5
    if phase == 2 and boss_hp_pct < 0.55 and 5 in available and previous_pick != 5:
        return 5

    # Priority 2: Allas (1) if player defending
    if player_defending and 1 in available:
        return 1

    # Priority 3: Old Boys (4) if player is low
    if player_hp_pct <= 0.50 and 4 in available:
        return 4

    # Priority 4: Ranga (6) if player not bleeding
    has_bleed = any(d.get("type") == "poison" for d in player.get("active_debuffs", []))
    if not has_bleed and 6 in available:
        return 6

    # Priority 5: Crystal Atelier (7) for defense
    if phase >= 2 and 7 in available and not any(
        b.get("source") == "crystal_atelier" for b in boss.get("active_buffs", [])
    ):
        return 7

    # Priority 6: Zelkova (3) — reliable damage
    if 3 in available:
        return 3

    return random.choice(available)


def _execute_boss_workshop(boss, player, workshop_id, ctx, defending):
    """Execute a single workshop attack for the boss against the player."""
    ws = WORKSHOP_DEFS[workshop_id]
    stat_key = ws["stat"]
    scaling = _get_boss_stat(boss, stat_key)
    base_dmg = random.randint(4, 10) + scaling
    mult = ws["mult"]
    p_con = compute_player_stats(player)[1]  # p_con is index 1

    ws_name = ws["name"]
    messages = []

    if ws["target"] == "single":
        if workshop_id == 1:  # Allas — 20% con ignore
            eff_con = int(p_con * 0.80)
            dmg = max(0, int(base_dmg * mult) - eff_con)
        elif workshop_id == 3:  # Zelkova — double hit
            dmg = 0
            for _ in range(2):
                roll = random.randint(4, 10) + scaling
                hit = max(0, int(roll * mult) - p_con)
                dmg += hit
            player["current_hp"] -= max(0, dmg)
            return max(0, dmg), False  # messages handled outside
        elif workshop_id == 4:  # Old Boys — 65% stun
            dmg = max(0, int(base_dmg * mult) - p_con)
            if random.random() < 0.65:
                player["stunned"] = True
                messages.append("  💥 You are STUNNED!")
        elif workshop_id == 6:  # Ranga — 70% bleed
            dmg = max(0, int(base_dmg * mult) - p_con)
            if random.random() < 0.70:
                apply_bleed(player, 6, 3)
                messages.append("  🩸 You are BLEEDING! (6 dmg x 3 turns)")
        elif workshop_id == 7:  # Crystal Atelier — +20% dodge for boss
            dmg = max(0, int(base_dmg * mult) - p_con)
            boss.setdefault("active_buffs", []).append({
                "type": "evasion",
                "source": "crystal_atelier",
                "value": 0.20,
                "remaining": 2,
            })
            messages.append(f"  💎 {boss['name']} gains +20% Dodge for 2 turns!")
        elif workshop_id == 8:  # Atelier Logic — 2.0x
            dmg = max(0, int(base_dmg * mult) - p_con)
        else:
            dmg = max(0, int(base_dmg * mult) - p_con)

        # Apply defending
        if defending:
            dmg = int(dmg * 0.5)

        player["current_hp"] -= max(0, dmg)
        c_print(format_damage_msg(boss["name"], player["name"], max(0, dmg),
                                   element="dark", skill_name=ws_name))
        for m in messages:
            c_print(m)

        return dmg, player["current_hp"] <= 0

    elif ws["target"] == "aoe":
        # Hit player (AoE in boss context is just the player since boss fights solo)
        dmg = max(0, int(base_dmg * mult) - p_con)
        if workshop_id == 5:  # Mook — 50% lifesteal
            heal = int(dmg * 0.50)
            boss["hp"] = min(boss["hp"] + heal, boss.get("max_hp", boss["hp"]))
            if heal > 0:
                messages.append(f"  🩸 Mook lifesteal: {boss['name']} recovers {heal} HP!")
        elif workshop_id == 2:  # Wheels — 30% stun
            if random.random() < 0.30:
                player["stunned"] = True
                messages.append("  ⚡ You are STUNNED!")

        if defending:
            dmg = int(dmg * 0.5)

        player["current_hp"] -= max(0, dmg)
        c_print(format_damage_msg(boss["name"], player["name"], max(0, dmg),
                                   element="dark", skill_name=ws_name))
        for m in messages:
            c_print(m)

        return dmg, player["current_hp"] <= 0

    elif ws["target"] == "random3":
        # Durandal: 3 hits on player
        total_dmg = 0
        for hit_num in range(3):
            roll = random.randint(4, 10) + scaling
            dmg = max(0, int(roll * mult) - p_con)
            if defending:
                dmg = int(dmg * 0.5)
            total_dmg += max(0, dmg)
            hit_label = f"Durandal ({hit_num + 1}/3)"
            c_print(format_damage_msg(boss["name"], player["name"], max(0, dmg),
                                       element="dark", skill_name=hit_label))

        player["current_hp"] -= max(0, total_dmg)
        return total_dmg, player["current_hp"] <= 0

    return 0, False


def _execute_boss_furioso(boss, player, ctx, defending):
    """Boss executes Furioso — 9 attacks at 0.75x, effects at 50% potency."""
    c_print("\n" + "=" * 50)
    c_print("⚔️  The Black Silence extends both hands.")
    c_print("    Nine spectral weapons fan out — a halo of steel and sorrow.")
    c_print('    "FURIOSO."')
    c_print("=" * 50)

    p_con = compute_player_stats(player)[1]
    furioso_mult = 0.75
    effect_potency = 0.50

    total_dmg = 0

    # Build randomized Furioso order: shuffle 1-8, Durandal (9) always last
    furioso_order = list(range(1, 9))
    random.shuffle(furioso_order)
    furioso_order.append(9)

    for workshop_id in furioso_order:
        if player["current_hp"] <= 0:
            break

        ws = WORKSHOP_DEFS[workshop_id]
        stat_key = ws["stat"]
        scaling = _get_boss_stat(boss, stat_key)

        if workshop_id == 1:  # Allas — 10% CON ignore
            base_dmg = random.randint(4, 10) + scaling
            eff_con = int(p_con * 0.90)
            dmg = max(0, int(base_dmg * ws["mult"] * furioso_mult) - eff_con)
        elif workshop_id == 3:  # Zelkova — double hit at 0.70 * 0.75
            dmg = 0
            for _ in range(2):
                roll = random.randint(4, 10) + scaling
                hit = max(0, int(roll * ws["mult"] * furioso_mult) - p_con)
                dmg += hit
        elif workshop_id == 9:  # Durandal — 3 hits at 0.45x
            dmg = 0
            for _ in range(3):
                roll = random.randint(4, 10) + scaling
                hit = max(0, int(roll * ws["mult"] * furioso_mult) - p_con)
                dmg += hit
        else:
            base_dmg = random.randint(4, 10) + scaling
            dmg = max(0, int(base_dmg * ws["mult"] * furioso_mult) - p_con)

        if defending:
            dmg = int(dmg * 0.5)

        total_dmg += max(0, dmg)
        player["current_hp"] -= max(0, dmg)

        skill_label = f"Furioso: {ws['name']}"
        c_print(format_damage_msg(boss["name"], player["name"], max(0, dmg),
                                   element="dark", skill_name=skill_label))

        # Effects at 50% potency
        if workshop_id == 2 and player["current_hp"] > 0:  # Wheels — 15% stun
            if random.random() < 0.15:
                player["stunned"] = True
                c_print("  ⚡ You are STUNNED!")
        elif workshop_id == 4 and player["current_hp"] > 0:  # Old Boys — 32.5% stun
            if random.random() < 0.325:
                player["stunned"] = True
                c_print("  💥 You are STUNNED!")
        elif workshop_id == 5:  # Mook — 25% lifesteal (halved)
            heal = int(max(0, dmg) * 0.25)
            boss["hp"] = min(boss["hp"] + heal, boss.get("max_hp", boss["hp"]))
            if heal > 0:
                c_print(f"  🩸 {boss['name']} recovers {heal} HP!")
        elif workshop_id == 6 and player["current_hp"] > 0:  # Ranga — 35% bleed
            if random.random() < 0.35:
                apply_bleed(player, 6, 3)
                c_print("  🩸 You are BLEEDING!")
        elif workshop_id == 7:  # Crystal Atelier — +10% dodge
            boss.setdefault("active_buffs", []).append({
                "type": "evasion",
                "source": "crystal_atelier",
                "value": 0.10,
                "remaining": 2,
            })
            c_print("  💎 The Black Silence gains +10% Dodge for 2 turns!")

    c_print(f"\n  Furioso Total: {total_dmg} damage dealt!")

    # Reset boss workshop state
    ctx["workshops_used_this_cycle"] = []
    ctx["furioso_timer"] = 0

    return total_dmg, player["current_hp"] <= 0


def _trigger_revival(boss, ctx):
    """Trigger the revival sequence."""
    c_print("\n" + "-" * 40)
    c_print("The Black Silence collapses. The gloves fall still.")
    c_input("\nPress Enter...")
    c_print("...")
    c_input("Press Enter...")
    c_print("A heartbeat. Singular. Defiant.")
    c_input("Press Enter...")
    c_print("The figure rises. The mask is gone. Beneath it:")
    c_print("eyes that have seen everything and lost more.")
    c_print('"\\"That\'s that, and this is this.\\""')
    c_print("The gloves ignite. All nine voices scream at once.")
    c_print("-" * 40)

    # Restore HP
    max_hp = boss.get("max_hp", 500)
    restore_hp = int(max_hp * REVIVAL_HP_PCT)
    boss["hp"] = restore_hp
    c_print(f"\n  The Black Silence rises with {boss['hp']} HP!")

    # Clear all debuffs on boss
    boss.pop("stunned", None)
    boss.pop("slowed", None)
    boss.pop("active_debuffs", None)
    # Clear all buffs on boss
    boss.pop("active_buffs", None)
    boss.pop("damage_taken_mult", None)

    ctx["revived"] = True
    ctx["phase"] = 3
    ctx["furioso_timer"] = 0
    _reroll_workshops(ctx)

    c_input("\nPress Enter to continue...")


# ═══════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════

def combat_black_silence(player, floor=None, enemies=None):
    """Superboss: The Black Silence.

    Args:
        enemies: Optional pre-created enemy list for GUI mode state sharing.
    """
    boss_key = BOSS_KEY

    if enemies is None:
        boss = enemy_stats(boss_key, player)
        boss["max_hp"] = boss["hp"]
        enemies = [boss]
    else:
        boss = None
        for i, e in enumerate(enemies):
            if e.get("key") == boss_key:
                boss = e
                boss["max_hp"] = boss["hp"]
                break
        if boss is None:
            boss = enemy_stats(boss_key, player)
            boss["max_hp"] = boss["hp"]
            enemies.append(boss)

    # Opening narration
    c_print("\n" + "=" * 60)
    c_print("You find yourself in a ruined workshop — or perhaps nine workshops,")
    c_print("collapsed into one another like a deck of cards shuffled by grief.")
    c_print("")
    c_print("A figure stands in the center. Black coat. Black gloves. No face —")
    c_print("only a mask of silence.")
    c_print("")
    c_print("They do not speak. They do not need to. The gloves clench.")
    c_print("")
    c_print("Nine names are stitched into the leather. They whisper.")
    c_print("=" * 60)
    c_print(f"\n  The Black Silence — HP: {boss['hp']}")
    c_input("\nPress Enter to face the Silence...")

    # Context state
    context = {
        "phase": 1,
        "revived": False,
        "phase2_triggered": False,
        "workshops_available": [],
        "workshops_used_this_cycle": [],
        "cycle_turns_remaining": 0,
        "furioso_timer": 0,
        "phase2_dex_bonus_applied": False,
    }

    # Initial workshop roll
    _reroll_workshops(context)

    # ═══════════════════════════════════════════════════════════════
    # HOOKS
    # ═══════════════════════════════════════════════════════════════

    def pre_player_hook(ctx, elist):
        b = _get_boss(elist)
        if not b:
            return

        hp_pct = b["hp"] / b.get("max_hp", 1)

        # Phase 1 → 2 transition
        if ctx["phase"] == 1 and hp_pct <= 0.60 and not ctx["phase2_triggered"]:
            ctx["phase"] = 2
            ctx["phase2_triggered"] = True
            ctx["cycle_turns_remaining"] = 0  # Force re-roll

            if not ctx["phase2_dex_bonus_applied"]:
                b["dex_mod"] = b.get("dex_mod", 0) + PHASE2_DEX_BONUS
                ctx["phase2_dex_bonus_applied"] = True

            c_print("\n" + "-" * 40)
            c_print("The Black Silence staggers. The mask cracks —")
            c_print("not physically, but in the way reality bends around them.")
            c_print("They roll their shoulders.")
            c_print("")
            c_print("A fifth glove materializes from shadow. Then a sixth.")
            c_print('"No more holding back."')
            c_print("-" * 40)
            c_input("\nPress Enter...")

        # Re-roll workshops
        if ctx["cycle_turns_remaining"] <= 0 or not ctx["workshops_available"]:
            _reroll_workshops(ctx)

    def enemy_turn_hook(enemy, ctx, pl, p_con, defending, **kwargs):
        if enemy.get("key") != boss_key:
            return 1, False, None, 1.0, 0

        b = enemy
        phase = ctx["phase"]
        actions_per_turn = 2 if phase == 2 else 1

        total_dmg = 0
        player_died = False

        for action_num in range(actions_per_turn):
            if pl["current_hp"] <= 0:
                break

            if actions_per_turn > 1:
                c_print(f"\n⚡ FAST ACTION! {b['name']} — Action {action_num + 1}/{actions_per_turn}!")

            # Check stun
            if b.get("stunned"):
                c_print(f"The {b['name']} is stunned and cannot act!")
                b["stunned"] = False
                continue

            # Store defending state for AI
            pl["_defending"] = defending

            previous_pick = ctx.get("_previous_workshop", None)
            workshop_id = _select_workshop(ctx, b, pl, previous_pick=previous_pick)
            if workshop_id:
                dmg, died = _execute_boss_workshop(b, pl, workshop_id, ctx, defending)
                total_dmg += dmg
                ctx["workshops_used_this_cycle"].append(workshop_id)
                ctx["_previous_workshop"] = workshop_id
                if died:
                    player_died = True
                    break

        # Clean up temp key
        pl.pop("_defending", None)
        ctx.pop("_previous_workshop", None)

        # Furioso check in Phase 3
        if phase == 3 and not player_died:
            ctx["furioso_timer"] += 1
            all_used = len(set(ctx.get("workshops_used_this_cycle", []))) >= 9
            if ctx["furioso_timer"] >= FURIOSO_TIMER_MAX or all_used:
                dmg, died = _execute_boss_furioso(b, pl, ctx, defending)
                total_dmg += dmg
                if died:
                    c_print(f"{pl['name']} has been slain.")
                    return "dead"

        if player_died:
            c_print(f"{pl['name']} has been slain.")
            return "dead"

        # Return: (attacks_to_do, skip_normal_attack, extra_logic, armor_mult, temp_str)
        return 0, True, None, 1.0, 0

    def post_round_hook(ctx, elist):
        ctx["cycle_turns_remaining"] = max(0, ctx["cycle_turns_remaining"] - 1)

        b = _get_boss(elist)
        if not b:
            return

        # Check for death → revival (Phase 2 → Phase 3)
        if b["hp"] <= 0 and not ctx["revived"]:
            _trigger_revival(b, ctx)
            return

        # Phase 3: warn about Furioso
        if ctx["phase"] == 3 and ctx["furioso_timer"] >= 3:
            turns_left = FURIOSO_TIMER_MAX - ctx["furioso_timer"]
            c_print(f"⚠️  The gloves glow brighter... Furioso in {turns_left} turn(s)!")

    def custom_hud_hook(ctx, elist):
        b = _get_boss(elist)
        if b:
            phase_label = f"Phase {ctx['phase']}"
            if ctx["phase"] == 3:
                phase_label += f" | Furioso in {FURIOSO_TIMER_MAX - ctx['furioso_timer']}t"
            c_print(f"  {phase_label} | Workshops: {len(ctx.get('workshops_available', []))} available")
        print_combat_hud(player, elist, header="Superboss: The Black Silence")

    # ═══════════════════════════════════════════════════════════════
    # RUN COMBAT
    # ═══════════════════════════════════════════════════════════════

    result = superboss_combat_loop(
        player, enemies, floor, "The Black Silence", context,
        pre_player_hook=pre_player_hook,
        custom_hud_hook=custom_hud_hook,
        enemy_turn_hook=enemy_turn_hook,
        post_round_hook=post_round_hook,
    )

    # ═══════════════════════════════════════════════════════════════
    # POST-COMBAT (victory)
    # ═══════════════════════════════════════════════════════════════

    if result == "victory":
        # Guard: only award loot once per save
        if not player.get("boss_defeated_black_silence"):
            c_print("\n" + "=" * 60)
            c_print("The Black Silence kneels. The gloves fall still.")
            c_print("")
            c_print("For a long moment, there is only silence — not the silence")
            c_print("of absence, but the silence of peace. Of an oath finally fulfilled.")
            c_print("")
            c_print("The figure looks at you, and for the first time, almost smiles.")
            c_print('"You remind me of someone I used to know."')
            c_print("")
            c_print("They press the gloves into your hands.")
            c_print("They are warm. They are waiting.")
            c_print("=" * 60)

            # Grant loot
            from resources.items import build_item
            from inventory_ui import prompt_acquire_item
            gloves = build_item("certain_someone_black_gloves", rarity="unique")
            c_print(f"\n  🎁 Received: {gloves['name']}!")
            prompt_acquire_item(player, gloves)

            # Optional vanity item
            mask = build_item("perception_blocking_mask", rarity="unique")
            c_print(f"  🎭 Received: {mask['name']}!")
            prompt_acquire_item(player, mask)

            # Set defeated flag AFTER awarding loot
            player["boss_defeated_black_silence"] = True

    return result
