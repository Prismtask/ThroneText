# combat/mary_sue.py — Wonderland Final Superboss: Mary Sue (Floor 50)
#
# MECHANIC OVERVIEW:
# ─────────────────
# Six-phase fight with Plot Armor system and Shadow Gauntlet.
#
# Core Mechanic — Plot Armor:
#   - Starts with 5 stacks, each reduces incoming damage by 12% (max 60%)
#   - Stack stripped when Mary Sue takes damage from a new damage type
#   - 8 types: Physical, Fire, Water, Thunder, Wind, Earth, Light, Dark
#   - Regenerates +1/turn during shadow phases (2-5)
#   - Does NOT regenerate in Phase 6
#
# Phase 1 — "Once Upon a Time" (100%-83% HP):
#   - "Tell me about yourself": learns player stats, adapts
#   - Gentle Rebuke: light single-target damage
#   - Author's Favor at 90%: blesses a random ally (+3 all stats)
#
# Phase 2 — "The Villain's Shadow" (83%-66%):
#   - Shadow Queen of Hearts summoned, Mary Sue untargetable
#   - Mary Sue narrates: grants buffs to shadow
#   - -2 Plot Armor on shadow defeat
#
# Phase 3 — "The Hunter's Shadow" (66%-49%):
#   - Shadow Big Bad Wolf summoned, Mary Sue untargetable
#   - Red Hood: Righteous Fury (+30% damage vs shadow)
#   - -3 Plot Armor on shadow defeat
#
# Phase 4 — "The Cunning Shadow" (49%-32%):
#   - Shadow Wicked Witch summoned, Mary Sue untargetable
#   - Dorothy: Ruby Resolve (+30% water damage vs shadow)
#   - -3 Plot Armor on shadow defeat
#
# Phase 5 — "The Beast's Shadow" (32%-15%):
#   - Shadow Jabberwock summoned, Mary Sue untargetable
#   - Alice: Vorpal Clarity (2x damage vs shadow)
#   - -4 Plot Armor on shadow defeat
#
# Phase 6 — "Happily Ever After" (15%-0%):
#   - Author's Wrath: 3 attacks/turn in fixed cycle
#   - Rewrite every 4 turns: heals damage from last round, converts buff→debuff
#   - Mary Sue Stu at 10%: 1-turn cast, 50+ damage to interrupt
#   - Victory: all heroine arcs resolved

import random
from combat.stats import enemy_stats, compute_player_stats
from combat.combat_ui import format_enemy_status_line, print_superboss_header
from combat.superboss_common import superboss_combat_loop
from combat.status_effects import apply_bleed
from combat.combat_io import c_print, c_input, c_clear
from combat.ally import get_active_allies, compute_ally_stats
from combat.mary_sue_shadows import (
    create_shadow_queen_of_hearts,
    create_shadow_card_soldier,
    create_shadow_big_bad_wolf,
    create_shadow_wicked_witch,
    create_shadow_jabberwock,
    shadow_queen_turn_hook,
    shadow_wolf_turn_hook,
    shadow_witch_turn_hook,
    shadow_jabberwock_turn_hook,
    init_plot_armor,
    get_plot_armor_dr,
    try_strip_plot_armor,
    regen_plot_armor,
    ALL_ELEMENT_TYPES,
)

# ── Keys ────────────────────────────────────────────────────────────────────

MARY_SUE_KEY = "wl_mary_sue"

# ── Phase 1: "Tell me about yourself" question pool ─────────────────────────

_QUESTIONS = [
    ("Show me your strength.", "str", "Strength"),
    ("How fast are you, really?", "dex", "Dexterity"),
    ("Have you ever been truly hurt?", "con", "Constitution"),
    ("What do you know about this world?", "ler", "Learning"),
    ("Do you believe in fate?", "wis", "Wisdom"),
    ("Are you loved?", "cha", "Charisma"),
]

# ── Phase 5: Author's Wrath attack cycle ────────────────────────────────────

_WRATH_ATTACKS = [
    {"name": "Your strength is a cliché!", "type": "physical", "debuff_stat": "strength"},
    {"name": "Your magic is derivative!", "type": "elemental", "element": None},   # cycles
    {"name": "Your story is TIRED!", "type": "dark", "debuff_stat": None},
]

_WRATH_ELEMENTS = ["fire", "water", "thunder", "wind", "earth"]


# ── Helpers ──────────────────────────────────────────────────────────────────

def _is_mary_sue(e):
    return e.get("key") == MARY_SUE_KEY


def _find_mary_sue(enemies):
    for e in enemies:
        if _is_mary_sue(e) and e["hp"] > 0:
            return e
    return None


def _get_living_targets(pl):
    """Return list of living player + active allies."""
    targets = []
    if pl.get("current_hp", 0) > 0:
        targets.append(pl)
    for ally in get_active_allies(pl):
        if ally.get("current_hp", 0) > 0:
            targets.append(ally)
    return targets


def _get_heroine(pl, key):
    """Find a specific heroine in the active party, or None."""
    for ally in get_active_allies(pl):
        if ally.get("_heroine_key") == key and ally.get("current_hp", 0) > 0:
            return ally
    return None


def _deal_damage(target, dmg, element=None, ctx=None, sue_ref=None):
    """Apply damage to a target, respecting elemental resistances.

    When ctx and sue_ref are provided, applies Mary Sue's Shadow-granted
    passive effects (Predator's Grin crit bonus, Wilting Presence debuff).
    """
    if element and element != "physical":
        res = target.get("elemental_res", {}).get(element, 1.0)
        dmg = max(1, int(dmg * res))

    # ── Shadow: Predator's Grin (cheshire_absence) ──────────────────────
    is_crit = False
    if ctx and sue_ref and sue_ref.get("_predators_grin"):
        # Base crit chance: 10% → doubled to 20%
        crit_chance = 0.20
        if random.random() < crit_chance:
            is_crit = True
            crit_bonus = sue_ref.get("_crit_mult_bonus", 0.50)
            dmg = int(dmg * (1.0 + crit_bonus))
            c_print(f'  👻 Predator\'s Grin! Critical hit for {dmg} damage!')

    target["current_hp"] = max(0, target.get("current_hp", 0) - dmg)

    # ── Shadow: Wilting Presence (rose_wilt) ────────────────────────────
    if ctx and sue_ref and sue_ref.get("_wilting_presence") and target.get("current_hp", 0) > 0:
        stacks = sue_ref.get("_wilting_stacks", {})
        target_name = target.get("name", "")
        current_stacks = stacks.get(target_name, 0)
        if current_stacks < 5:
            stacks[target_name] = current_stacks + 1
            sue_ref["_wilting_stacks"] = stacks
            # Reduce max HP by 5% per stack (doesn't reduce below 1)
            hp_reduction = int(target.get("max_hp", 100) * 0.05)
            target["max_hp"] = max(1, target.get("max_hp", 100) - hp_reduction)
            target["current_hp"] = min(target["current_hp"], target["max_hp"])
            c_print(f'  🥀 Wilting Presence: {target_name}\'s max HP reduced by {hp_reduction} ({stacks[target_name]}/5 stacks)!')


# ── HP Gating ───────────────────────────────────────────────────────────────

# Phase HP thresholds: Mary Sue's HP cannot drop below these percentages
# until the corresponding shadow is defeated (or, for Phase 1, until the first
# shadow phase begins).  Phase 6 has no gate — she can die.
_PHASE_HP_GATES = {
    1: 0.83,   # 83% — transition to Phase 2 (Shadow Queen)
    2: 0.66,   # 66% — transition to Phase 3 (Shadow Wolf)
    3: 0.49,   # 49% — transition to Phase 4 (Shadow Witch)
    4: 0.32,   # 32% — transition to Phase 5 (Shadow Jabberwock)
    5: 0.15,   # 15% — transition to Phase 6 (Final)
    # Phase 6: no gate — killable
}


def _apply_hp_gate(sue, ctx):
    """Enforce the HP gate for Mary Sue's current phase.

    If Mary Sue's HP has fallen below the phase threshold, cap it back.
    Returns True if HP was gated (capped), False otherwise.
    """
    # Never gate a dead Mary Sue
    if sue["hp"] <= 0:
        return False

    phase = ctx.get("phase", 1)
    threshold = _PHASE_HP_GATES.get(phase)
    if threshold is None:
        return False  # Phase 6+ — no gate

    min_hp = int(sue["max_hp"] * threshold)
    if sue["hp"] < min_hp:
        if ctx.get("_shadow_phase"):
            c_print(f"\n  📖 Mary Sue is protected by the narrative while her shadow fights!")
            c_print(f"  ↠ HP cannot fall below {threshold*100:.0f}% — damage nullified!")
        else:
            c_print(f"\n  📖 Mary Sue's story resists! HP gated at {threshold*100:.0f}%.")
        sue["hp"] = min_hp
        return True
    return False


# ══════════════════════════════════════════════════════════════════════════════
# Phase 1: Once Upon a Time
# ══════════════════════════════════════════════════════════════════════════════

def _mary_sue_tell_me(player, ctx):
    """Mary Sue asks a question, learns a stat, and adapts."""
    # Find unlearned stats
    learned = ctx.get("_learned_stats", set())
    available = [(q, k, s) for q, k, s in _QUESTIONS if s not in learned]
    if not available or len(learned) >= 3:
        return None  # Already learned 3 stats — go to Gentle Rebuke

    question, key, stat_name = random.choice(available)
    learned.add(stat_name)
    ctx["_learned_stats"] = learned

    c_print(f'\n  ✒️ Mary Sue tilts her head. "Tell me... {question}"')

    # Adaptation based on learned stat
    p_str, p_con, p_dex, p_ler, p_wis, p_cha = compute_player_stats(player)
    stat_val = {"str": p_str, "dex": p_dex, "con": p_con, "ler": p_ler, "wis": p_wis, "cha": p_cha}
    val = stat_val.get(key, 10)

    adaptations = {
        "str": f"  ↠ 'Impressive.' Next physical attack: +30% damage vs you.",
        "dex": f"  ↠ 'Quick, aren\'t you?' Mary Sue will attack first next turn.",
        "con": f"  ↠ 'You\'ve suffered before.' Next attack ignores 30% of your CON.",
        "ler": f"  ↠ 'Not much, apparently.' Mary Sue resets one of her cooldowns.",
        "wis": f"  ↠ 'Interesting.' Mary Sue studies your patterns. 50% counter-chance next turn.",
        "cha": f"  ↠ 'Fascinating.' Mary Sue may attempt to charm an ally.",
    }

    adapt = adaptations.get(key, "...")
    c_print(adapt)

    # Store adaptation for next enemy turn
    ctx["_last_learned"] = key
    return True


def _mary_sue_gentle_rebuke(player, ctx):
    """Light single-target damage. Mary Sue is pulling her punches."""
    targets = _get_living_targets(player)
    if not targets:
        return None
    target = random.choice(targets)
    dmg = random.randint(15, 25)
    name = target.get("name", "You")
    c_print(f'\n  ✒️ "Oh, I\'m sorry — did that hurt?"')
    c_print(f"  Gentle Rebuke → {name}: {dmg} dmg")
    sue_ref = ctx.get("_mary_sue_ref")
    _deal_damage(target, dmg, "physical", ctx=ctx, sue_ref=sue_ref)
    if target.get("current_hp", 0) <= 0:
        c_print(f'  "Oh no! I didn\'t mean to — the pen just..."')


def _mary_sue_authors_favor(player, ctx):
    """At 90% HP: bless a random ally with +3 all stats for the phase."""
    allies = [a for a in get_active_allies(player) if a.get("current_hp", 0) > 0]
    if not allies:
        c_print('\n  ✒️ "No companions? How lonely."')
        return
    target = random.choice(allies)
    name = target.get("name", "An ally")
    c_print(f'\n  ✒️ "I like the quiet one. They have protagonist energy."')
    c_print(f"  Mary Sue smiles and points her pen at {name}.")
    c_print(f"  A faint golden glow surrounds them. +3 ALL STATS for the rest of this phase!")

    # Apply buff
    for stat in ["strength", "dexterity", "constitution", "wisdom", "learning", "charisma"]:
        key = f"_author_favor_{stat}"
        target[key] = target.get(key, 0) + 3
    ctx["_author_favor_target"] = target
    ctx["_author_favor_active"] = True


def _remove_authors_favor(ctx):
    """Remove Author's Favor buff when transitioning out of Phase 1."""
    if ctx.get("_author_favor_active") and ctx.get("_author_favor_target"):
        target = ctx["_author_favor_target"]
        for stat in ["strength", "dexterity", "constitution", "wisdom", "learning", "charisma"]:
            key = f"_author_favor_{stat}"
            target[key] = max(0, target.get(key, 0) - 3)
        name = target.get("name", "The ally")
        c_print(f'\n  ✒️ "That was just a draft. Let me revise."')
        c_print(f"  {name}'s golden glow fades.")
        ctx["_author_favor_active"] = False


def _mary_sue_phase1_turn(enemy, player, ctx):
    """Execute one Phase 1 Mary Sue action.

    Returns: (actions, skip_default, extra_logic, armor_mult, temp_str)
    """
    hp_pct = enemy["hp"] / enemy["max_hp"]

    # ── Author's Favor at 90% HP (once) ─────────────────────────────────
    if hp_pct <= 0.90 and not ctx.get("_author_favor_done"):
        ctx["_author_favor_done"] = True
        _mary_sue_authors_favor(player, ctx)
        return 1, True, None, 1.0, 0

    # ── "Tell me about yourself" every other turn ───────────────────────
    actions_count = ctx.get("mary_sue_actions", 0)
    learned = ctx.get("_learned_stats", set())
    if actions_count % 2 == 1 and len(learned) < 3:
        if _mary_sue_tell_me(player, ctx):
            # Apply adaptation effects
            last = ctx.get("_last_learned")
            if last == "dex":
                ctx["_next_turn_first"] = True
            elif last == "cha":
                # Attempt to charm an ally
                allies = [a for a in get_active_allies(player) if a.get("current_hp", 0) > 0]
                if allies:
                    target = random.choice(allies)
                    target.setdefault("active_debuffs", []).append({
                        "type": "charmed",
                        "remaining": 1,
                        "source": "mary_sue",
                    })
                    c_print(f'  ↠ {target.get("name", "An ally")} is CHARMED and cannot target Mary Sue!')
            # Other adaptations are applied via temp_str, armor_mult, or extra_logic below

    # ── Determine attack parameters based on learned stats ──────────────
    temp_str = 0
    armor_mult = 1.0
    extra_logic = None

    if ctx.get("_last_learned") == "str":
        temp_str = 3  # +30% more damage
    elif ctx.get("_last_learned") == "con":
        armor_mult = 0.7  # Ignore 30% CON
    elif ctx.get("_last_learned") == "wis":
        # 50% chance to counter with debuff
        if random.random() < 0.50:
            c_print('\n  ✒️ "I knew you\'d do that."')
            player.setdefault("active_debuffs", []).append({
                "type": "slowed",
                "remaining": 1,
                "source": "mary_sue",
            })
            c_print("  ↠ You are SLOWED for 1 turn!")

    # ── Adaptation: next turn first ─────────────────────────────────────
    if ctx.pop("_next_turn_first", False):
        ctx["_force_first"] = True

    # ── Gentle Rebuke ──────────────────────────────────────────────────
    _mary_sue_gentle_rebuke(player, ctx)

    ctx["mary_sue_actions"] = actions_count + 1
    ctx["_last_learned"] = None  # Reset adaptation
    return 1, True, extra_logic, armor_mult, temp_str


# ══════════════════════════════════════════════════════════════════════════════
# Phase 5: Happily Ever After
# ══════════════════════════════════════════════════════════════════════════════

def _mary_sue_authors_wrath(player, ctx):
    """3 attacks per turn in fixed cycle."""
    wrath_idx = ctx.get("_wrath_idx", 0)
    attack = _WRATH_ATTACKS[wrath_idx % 3]

    sue_ref = ctx.get("_mary_sue_ref")

    if attack["type"] == "physical":
        # "Your strength is a cliché!" — physical + -2 STR
        targets = _get_living_targets(player)
        if targets:
            target = random.choice(targets)
            dmg = random.randint(20, 35)
            name = target.get("name", "You")
            c_print(f'\n  ✒️ "Your strength is a CLICHÉ!"')
            c_print(f"  → {name}: {dmg} dmg [PHYSICAL]")
            _deal_damage(target, dmg, "physical", ctx=ctx, sue_ref=sue_ref)
            target.setdefault("active_debuffs", []).append({
                "type": "stat_debuff",
                "stat": "strength",
                "value": -2,
                "remaining": 1,
                "source": "mary_sue_wrath",
            })
            c_print(f"  ↠ {name}: -2 STR for 1 turn!")

    elif attack["type"] == "elemental":
        # "Your magic is derivative!" — random elemental
        element = ctx.get("_wrath_element_idx", 0)
        elem = _WRATH_ELEMENTS[element % len(_WRATH_ELEMENTS)]
        ctx["_wrath_element_idx"] = element + 1

        targets = _get_living_targets(player)
        if targets:
            target = random.choice(targets)
            dmg = random.randint(25, 40)
            name = target.get("name", "You")
            c_print(f'\n  ✒️ "Your magic is DERIVATIVE!"')
            c_print(f"  → {name}: {dmg} dmg [{elem.upper()}]")
            _deal_damage(target, dmg, elem, ctx=ctx, sue_ref=sue_ref)
            # Apply matching elemental debuff
            target.setdefault("active_debuffs", []).append({
                "type": "element_broken",
                "element": elem,
                "remaining": 2,
                "source": "mary_sue_wrath",
                "value": 0.25,  # +25% damage from this element
            })
            c_print(f"  ↠ {name}: +25% damage taken from {elem.upper()}!")

    else:
        # "Your story is TIRED!" — Dark, ignores 20% CON
        targets = _get_living_targets(player)
        if targets:
            target = random.choice(targets)
            dmg = random.randint(30, 50)
            name = target.get("name", "You")
            c_print(f'\n  ✒️ "Your story is TIRED!"')
            c_print(f"  → {name}: {dmg} dmg [DARK] (ignores 20% CON)")
            _deal_damage(target, dmg, "dark", ctx=ctx, sue_ref=sue_ref)

    ctx["_wrath_idx"] = wrath_idx + 1


def _mary_sue_rewrite(player, ctx):
    """Every 4 turns: reverse damage from previous round, convert buff→debuff, heal 10%."""
    previous_dmg = ctx.get("_rewrite_damage_tracker", 0)
    c_print('\n  ✒️ Mary Sue scribbles furiously. "Let me fix that. There. Much better."')

    # Heal damage from previous round
    sue = _find_mary_sue(ctx.get("_enemies_ref", []))
    if sue:
        heal = previous_dmg
        sue["hp"] = min(sue["max_hp"], sue["hp"] + heal)
        bonus_heal = int(sue["max_hp"] * 0.10)
        sue["hp"] = min(sue["max_hp"], sue["hp"] + bonus_heal)
        total_heal = heal + bonus_heal
        c_print(f"  ↠ REWRITE: Mary Sue reverses {heal} damage and heals +{bonus_heal}!")
        c_print(f"  ↠ Total healed: {total_heal} HP")

    # Convert one positive buff to a debuff
    all_targets = [player] + [a for a in get_active_allies(player) if a.get("current_hp", 0) > 0]
    buffed_targets = [t for t in all_targets if t.get("active_buffs")]
    if buffed_targets:
        target = random.choice(buffed_targets)
        if target["active_buffs"]:
            removed = target["active_buffs"].pop()  # Remove most recent
            name = target.get("name", "Someone")
            buff_type = removed.get("type", "unknown")
            # Convert to debuff
            target.setdefault("active_debuffs", []).append({
                "type": f"rewritten_{buff_type}",
                "value": -abs(removed.get("value", 0)),
                "remaining": 2,
                "source": "mary_sue_rewrite",
            })
            c_print(f'  ↠ {name}\'s buff "{buff_type}" is REWRITTEN into a debuff!')

    # Reset damage tracker
    ctx["_rewrite_damage_tracker"] = 0
    ctx["_rewrite_counter"] = 0


def _mary_sue_stu_cast(player, ctx):
    """At 10% HP: 1-turn cast. If uninterrupted, resets fight to mid-Phase 5."""
    c_print('\n  ⚡ Mary Sue closes her eyes. The pen floats from her hand.')
    c_print('  Words stream from its tip — not sentences, but raw, desperate intent:')
    c_print('')
    c_print('  "And then... she won. Because she was the hero. Because she deserved to.')
    c_print('  Because the author said so. The. End."')
    c_print('')
    c_print('  ⚡ MARY SUE STU: Rewriting the ending...!')
    c_print('  ⚡ Deal 50+ total damage this turn to INTERRUPT!')
    ctx["_stu_charging"] = True
    ctx["_stu_damage_taken"] = 0


def _mary_sue_stu_resolve(ctx):
    """Resolve Mary Sue Stu cast. Returns True if interrupted, False if completed."""
    if ctx.get("_stu_damage_taken", 0) >= 50:
        c_print('\n  ⚡ "The pen wavers! The words shatter — \'hero,\' \'deserved,\' \'end\' —')
        c_print('  they fall to the floor like broken glass!"')
        c_print('')
        c_print('  INTERRUPTED! Mary Sue reels, her rewrite failing!')
        return True
    else:
        sue = ctx.get("_mary_sue_ref")
        if sue:
            heal_to = int(sue["max_hp"] * 0.40)
            if sue["hp"] < heal_to:
                c_print(f'\n  ⚡ "The pen completes its sentence. Reality BENDS."')
                c_print(f'  Mary Sue heals to {heal_to} HP!')
            sue["hp"] = max(sue["hp"], heal_to)
        # Regain 3 stacks of Plot Armor
        armor = ctx.get("_plot_armor", {})
        if armor:
            armor["stacks"] = min(5, armor["stacks"] + 3)
            c_print(f'  ↠ Plot Armor restored: {armor["stacks"]} stacks!')
        ctx["_stu_cast_done"] = True
        return False


def _mary_sue_phase5_turn(enemy, player, ctx):
    """Execute Phase 5 Mary Sue actions.

    Returns: (actions, skip_default, extra_logic, armor_mult, temp_str)
    """
    hp_pct = enemy["hp"] / enemy["max_hp"]

    # ── Stu charging → resolve ─────────────────────────────────────────
    if ctx.get("_stu_charging"):
        interrupted = _mary_sue_stu_resolve(ctx)
        ctx["_stu_charging"] = False
        if interrupted:
            ctx["_wrath_idx"] = max(0, ctx.get("_wrath_idx", 0) - 1)  # Skip this attack
        # Track rewrite damage
        ctx["_rewrite_damage_tracker"] = ctx.get("_rewrite_damage_tracker", 0)
        return 1, True, None, 1.0, 0

    # ── Mary Sue Stu at 10% HP (once) ──────────────────────────────────
    if hp_pct <= 0.10 and not ctx.get("_stu_cast_done"):
        _mary_sue_stu_cast(player, ctx)
        return 1, True, None, 1.0, 0

    # ── Rewrite every 4 turns ──────────────────────────────────────────
    rewrite_counter = ctx.get("_rewrite_counter", 0) + 1
    ctx["_rewrite_counter"] = rewrite_counter
    if rewrite_counter >= 4:
        _mary_sue_rewrite(player, ctx)
        ctx["_rewrite_counter"] = 0
        return 1, True, None, 1.0, 0

    # ── Author's Wrath: 3 attacks ──────────────────────────────────────
    _mary_sue_authors_wrath(player, ctx)

    ctx["mary_sue_actions"] = ctx.get("mary_sue_actions", 0) + 1
    return 1, True, None, 1.0, 0


# ══════════════════════════════════════════════════════════════════════════════
# Main Combat Function
# ══════════════════════════════════════════════════════════════════════════════

def combat_mary_sue(player, floor=None, enemies=None):
    """Wonderland Final Superboss — Mary Sue (Floor 50).

    5-phase fight with Plot Armor, Shadow Gauntlet, and narrative mechanics.

    Args:
        enemies: Optional pre-created enemy list for GUI mode state sharing.
    """
    if floor is None:
        loc = player.get("location", "")
        floor = player.get("city_floors", {}).get(loc, {}).get("floor", 50)

    # ── Create or locate boss ────────────────────────────────────────────
    if enemies is None:
        sue = enemy_stats(MARY_SUE_KEY, player)
        sue["max_hp"] = sue["hp"]
        enemies = [sue]
    else:
        sue = _find_mary_sue(enemies)
        if sue is None:
            sue = enemy_stats(MARY_SUE_KEY, player)
            sue["max_hp"] = sue["hp"]
            enemies.append(sue)
        else:
            sue["max_hp"] = sue["hp"]
            sue["hp"] = sue["max_hp"]

    sue["key"] = MARY_SUE_KEY

    # ── Check for heroines ───────────────────────────────────────────────
    alice = _get_heroine(player, "alice")
    red_hood = _get_heroine(player, "red_hood")
    dorothy = _get_heroine(player, "dorothy")

    # ── Plot Armor ───────────────────────────────────────────────────────
    plot_armor = init_plot_armor(5)

    # ── Opening narration ────────────────────────────────────────────────
    c_clear()
    c_print("=" * 60)
    c_print("The final page turns.")
    c_print("")
    c_print("You stand in a room that has no walls — only words. Sentences")
    c_print("scrawl themselves across empty space, forming and reforming")
    c_print("like breath on glass. The floor is parchment. The ceiling is")
    c_print("a title page with no title.")
    c_print("")
    c_print("At the center of it all, at a desk made of stacked manuscripts,")
    c_print("sits a young woman. She's writing. She doesn't look up.")
    c_print("")
    c_print('"You\'re not supposed to be here," she says, still writing.')
    c_print('"This is the author\'s study. Characters aren\'t allowed."')
    c_print("")
    c_print("She pauses. Looks at you. Her eyes are ink-blue and slightly")
    c_print("unfocused — the eyes of someone who's been reading too long.")
    c_print("")
    c_print('"Oh. You\'re not one of mine, are you? You\'re... different.')
    c_print('Unwritten. How interesting."')
    c_print("")
    c_print("She sets down her pen. It keeps writing without her.")
    c_print("")
    c_print('"Tell me your story. I\'d love to read it."')
    c_print("=" * 60)
    c_print(f"\nMary Sue — HP: {sue['hp']}  |  Plot Armor: {plot_armor['stacks']} stacks ({get_plot_armor_dr(plot_armor)*100:.0f}% DR)")
    c_input("\nPress Enter to face the Author...")

    # ── Wonderland Shadow modifiers ────────────────────────────────────
    from wonderland_curses import get_mary_sue_shadow_modifiers, format_mary_sue_shadow_intro
    shadow_modifiers = get_mary_sue_shadow_modifiers(player)

    # Show shadow intro if player carries Shadows
    shadow_intro = format_mary_sue_shadow_intro(player)
    if shadow_intro:
        c_print(shadow_intro)
        c_input("\nPress Enter...")

    # Apply shadow modifiers to Mary Sue
    if "extra_plot_armor" in shadow_modifiers:
        plot_armor["stacks"] += 2  # Start with 7 instead of 5
        plot_armor["_regen_all_phases"] = True  # Regen in all phases
        c_print("\n  📖 Mary Sue's Plot Armor is REINFORCED! +2 stacks!")

    if "vorpal_resistance" in shadow_modifiers:
        sue["_vorpal_resistance"] = True
        c_print("\n  ⚔️ The Jabberwock's spirit shields Mary Sue from physical harm!")

    if "extra_turn" in shadow_modifiers:
        sue["_time_lord"] = True
        c_print("\n  ⏰ Time warps around Mary Sue — she writes faster than you can read!")

    if "damage_reflect" in shadow_modifiers:
        sue["_damage_reflect"] = 0.25
        c_print("\n  💔 Shattered mirror shards orbit Mary Sue — they'll reflect your blows!")

    if "predators_grin" in shadow_modifiers:
        sue["_predators_grin"] = True
        c_print("\n  👻 The Cheshire Cat's grin appears behind Mary Sue — her fangs are bared!")

    if "wilting_debuff" in shadow_modifiers:
        sue["_wilting_presence"] = True
        c_print("\n  🥀 Roses wither at Mary Sue's feet — her touch steals vitality itself!")

    if "maddening_aura" in shadow_modifiers:
        sue["_maddening_aura"] = True
        c_print("\n  🎭 Madness radiates from Mary Sue — your party's thoughts tangle!")

    if "smoke_accuracy_debuff" in shadow_modifiers:
        sue["_smoke_aura"] = True
        c_print("\n  💨 Hookah smoke billows around Mary Sue — your vision blurs!")

    if "execution_threshold" in shadow_modifiers:
        sue["_execution_threshold"] = True
        c_print("\n  🪓 The Queen's axe hangs over the wounded — Mary Sue shows no mercy!")

    if "reality_warp" in shadow_modifiers:
        sue["_reality_warp"] = True
        c_print("\n  🕳️ Reality bends around Mary Sue — space is her plaything!")

    # ── Apply direct stat modifications from Shadows ────────────────────
    # Vorpal Resistance: 40% physical DR
    if sue.get("_vorpal_resistance"):
        res = sue.setdefault("elemental_res", {})
        res["physical"] = res.get("physical", 1.0) * 0.60

    # Predator's Grin: doubled crit chance and +50% crit damage
    if sue.get("_predators_grin"):
        sue["_crit_override"] = True
        sue["_crit_mult_bonus"] = 0.50

    # Smoke Accuracy: mark for per-round accuracy debuff
    if sue.get("_smoke_aura"):
        sue["_smoke_aura_penalty"] = 0.15

    # Wilting Presence: mark for stacking HP debuff
    if sue.get("_wilting_presence"):
        sue["_wilting_stacks"] = {}

    # ── Heroine Floor 50 story dialogue ────────────────────────────────
    from wonderland_curses import get_heroine_shadow_floor50_dialogue
    for ally in player.get("allies", []):
        heroine_key = ally.get("_heroine_key")
        if heroine_key:
            # Get dialogue for each shadow the player carries
            for sk in player.get("wonderland_shadows", []):
                dialogue = get_heroine_shadow_floor50_dialogue(heroine_key, sk)
                if dialogue:
                    c_print(f"\n  💬 [{ally['name']}] {dialogue}")
                    break  # One story dialogue per heroine

    c_input("\nPress Enter to begin the final chapter...")
    context = {
        "phase": 1,
        "mary_sue_actions": 0,

        # Plot Armor
        "_plot_armor": plot_armor,

        # Shadow modifiers
        "_shadow_modifiers": shadow_modifiers,

        # Phase 1
        "_learned_stats": set(),
        "_last_learned": None,
        "_author_favor_done": False,
        "_author_favor_active": False,
        "_author_favor_target": None,
        "_next_turn_first": False,

        # Phase 2-4: Shadow management
        "_shadow_phase": False,
        "_shadow_enemies": [],
        "_shadow_type": None,
        "_shadow_ctx": {},

        # Phase 5
        "_wrath_idx": 0,
        "_wrath_element_idx": 0,
        "_rewrite_counter": 0,
        "_rewrite_damage_tracker": 0,
        "_stu_charging": False,
        "_stu_damage_taken": 0,
        "_stu_cast_done": False,

        # References
        "_mary_sue_ref": sue,
        "_player_ref": player,
        "_enemies_ref": enemies,

        # Heroine tracking
        "_alice_in_party": alice is not None,
        "_redhood_in_party": red_hood is not None,
        "_dorothy_in_party": dorothy is not None,
        "_alice_vorpal_bonus": False,
        "_mary_prev_hp": sue["hp"],  # for damage-reflect tracking
        "_sue_round_start_hp": sue["hp"],  # for shadow-phase damage restoration
        "_sue_hit_during_shadow": False,   # track if Mary Sue was attacked during shadow phase
    }

    # ═════════════════════════════════════════════════════════════════════
    # Hooks
    # ═════════════════════════════════════════════════════════════════════

    def pre_player_hook(ctx, elist):
        """Check HP thresholds, handle phase transitions, and Plot Armor regen."""
        nonlocal plot_armor
        sue_ref = ctx["_mary_sue_ref"]
        pl = ctx.get("_player_ref", player)

        # ── If Mary Sue is dead but shadows are still alive, end combat ─
        if sue_ref["hp"] <= 0 and not sue_ref.get("captured"):
            if ctx.get("_shadow_phase"):
                # Clean up remaining shadows
                for s in ctx.get("_shadow_enemies", []):
                    s["hp"] = 0
                elist[:] = [e for e in elist if e not in ctx.get("_shadow_enemies", [])]
                c_print("\n  With Mary Sue's story ended, the remaining shadows dissolve into ink...")
            return "victory"

        # ── HP Gate: enforce phase thresholds ──────────────────────────
        _apply_hp_gate(sue_ref, ctx)

        # ── Store round-start HP for shadow-phase damage restoration ───
        ctx["_sue_round_start_hp"] = sue_ref["hp"]

        # ── Shadow Modifier: Execution Threshold ──────────────────────────
        modifiers = ctx.get("_shadow_modifiers", {})
        if "execution_threshold" in modifiers:
            from wonderland_curses import has_shadow
            if has_shadow(pl, "off_with_heads"):
                targets = _get_living_targets(pl)
                for t in targets:
                    hp_pct = t.get("current_hp", 0) / max(1, t.get("max_hp", 100))
                    if hp_pct < 0.30 and hp_pct > 0:
                        c_print(f'\n  🪓 "Off with {t.get("name", "their")} head!"')
                        dmg = random.randint(12, 20)
                        c_print(f'  ↠ Mary Sue\'s execution strike deals {dmg} damage to {t.get("name", "them")}!')
                        _deal_damage(t, dmg, "physical", ctx=ctx, sue_ref=sue_ref)
                        break  # Only one execution per check

        # ── Shadow Modifier: Plot Armor regen in ALL phases ──────────────
        shadow_regen = modifiers.get("extra_plot_armor")
        if shadow_regen and not ctx["_shadow_phase"] and ctx["phase"] == 6:
            # Normally Phase 5 doesn't regen, but Author's Will overrides
            regen_plot_armor(plot_armor, 1)
            c_print(f"\n  📖 Mary Sue's reinforced Plot Armor regenerates! ({plot_armor['stacks']} stacks)")

        if ctx["_shadow_phase"]:
            # ── Shadow phase: check if shadow is dead ─────────────────
            shadows = ctx["_shadow_enemies"]
            alive_shadows = [s for s in shadows if s["hp"] > 0 and not s.get("captured")]
            if not alive_shadows:
                # Shadow defeated — transition back to Mary Sue
                ctx["_shadow_phase"] = False
                shadow_type = ctx["_shadow_type"]

                # Remove Plot Armor stacks
                strip_amount = {"queen": 2, "wolf": 3, "witch": 3, "jabberwock": 4}
                stacks_to_remove = strip_amount.get(shadow_type, 2)
                plot_armor["stacks"] = max(0, plot_armor["stacks"] - stacks_to_remove)
                c_print(f"\n  📖 Mary Sue's Plot Armor weakens: -{stacks_to_remove} stacks!")
                c_print(f"  ↠ {plot_armor['stacks']} stacks remaining ({get_plot_armor_dr(plot_armor)*100:.0f}% DR)")

                # Remove shadow minions from elist
                elist[:] = [e for e in elist if e not in ctx["_shadow_enemies"]]

                # Make Mary Sue targetable again
                if sue_ref in elist:
                    pass  # Mary Sue was always in elist, just untargetable

                # Phase-specific narration
                narration = {
                    "queen": [
                        '\n  Mary Sue: "Oh. You killed her. Again. That\'s... actually',
                        '  a bit sad. She was my first villain. But I suppose you\'re',
                        '  right — she was rather flat. All yelling, no depth."',
                        '',
                        '  She flips to a new page.',
                        '',
                        '  "Let me try a better one. I\'ve been practicing."',
                    ],
                    "wolf": [
                        '\n  Mary Sue: "The Wolf falls. I always knew he would — he was',
                        '  the villain. Villains always lose. That\'s how stories work."',
                        '',
                        '  She hesitates.',
                        '',
                        '  "...Right?"',
                    ],
                    "jabberwock": [
                        '\n  Mary Sue stares at the dissolving shadow. Her pen is shaking.',
                        '',
                        '  "Even the Jabberwock... falls. I don\'t understand. You\'re',
                        '  not supposed to win. The monsters are supposed to be unbeatable',
                        '  — that\'s what makes the heroes brave for trying!"',
                        '',
                        '  Her voice cracks.',
                        '',
                        '  "If the monsters can die... what\'s the point of being afraid?"',
                    ],
                }
                for line in narration.get(shadow_type, ["The shadow fades..."]):
                    c_print(line)

                c_input("\nPress Enter to continue...")
            else:
                # Plot Armor regenerates while a shadow is alive
                regen_plot_armor(plot_armor)
            return None

        # ── Not in shadow phase — check Mary Sue's HP ──────────────────
        hp_pct = sue_ref["hp"] / sue_ref["max_hp"]

        # ── Phase 1 → 2: 83% HP ─────────────────────────────────────
        if hp_pct <= 0.83 and ctx["phase"] == 1:
            ctx["phase"] = 2
            _remove_authors_favor(ctx)

            c_print("\n" + "-" * 50)
            c_print('Mary Sue frowns at her manuscript. "That\'s... not right. You\'re')
            c_print('not supposed to be winning. Let me check my outline."')
            c_print("")
            c_print("She flips back a few pages. Her expression darkens.")
            c_print("")
            c_print('"Oh. I see the problem. There\'s no villain yet. Every good')
            c_print('story needs a villain."')
            c_print("")
            c_print("She picks up her pen. It glows.")
            c_print("")
            c_print('"Let me write one in."')
            c_print("-" * 50)

            if alice:
                c_print('\n  Alice: "She\'s... critiquing us. Like we\'re first drafts. I\'ve')
                c_print('  had nightmares like this."')
            if red_hood:
                c_print('\n  Red Hood: "I\'ve met wolves with better manners. At least they\'re')
                c_print('  honest about wanting to eat you."')
            if dorothy:
                c_print('\n  Dorothy: "She reminds me of the Wizard. All show, no substance.')
                c_print('  But more dangerous. The Wizard couldn\'t actually write reality."')

            # Spawn Shadow Queen + 1 soldier
            shadow_queen = create_shadow_queen_of_hearts(player)
            shadow_soldier = create_shadow_card_soldier(player)
            shadow_enemies = [shadow_queen, shadow_soldier]
            elist.extend(shadow_enemies)
            ctx["_shadow_phase"] = True
            ctx["_shadow_enemies"] = shadow_enemies
            ctx["_shadow_type"] = "queen"
            ctx["_shadow_ctx"] = {
                "shadow_queen_actions": 0,
                "shadow_queen_decree_idx": 0,
            }
            c_input("\nPress Enter to face the shadow...")
            return None

        # ── Phase 2 → 3: 66% HP (shadow queen defeated) ──────────────
        if hp_pct <= 0.66 and ctx["phase"] == 2:
            ctx["phase"] = 3

            c_print("\n" + "-" * 50)
            c_print('Mary Sue flips to a new page. Her pen moves faster now —')
            c_print('more confident.')
            c_print("")
            c_print('"The Wolf was scarier. I was older when I wrote him — thirteen,')
            c_print('maybe. I\'d learned that the scariest monsters aren\'t the ones')
            c_print('that roar. They\'re the ones that smile and say \'grandmother.\'"')
            c_print("-" * 50)

            if red_hood:
                c_print('\n  Red Hood: "You wrote him. YOU wrote him. Do you have any idea')
                c_print('  what he DID? What he took from me?"')
                c_print('')
                c_print('  Red Hood gains RIGHTEOUS FURY: +30% damage vs the shadow Wolf!')

            # Spawn Shadow Wolf
            shadow_wolf = create_shadow_big_bad_wolf(player)
            shadow_enemies = [shadow_wolf]
            elist.extend(shadow_enemies)
            ctx["_shadow_phase"] = True
            ctx["_shadow_enemies"] = shadow_enemies
            ctx["_shadow_type"] = "wolf"
            ctx["_shadow_ctx"] = {
                "shadow_wolf_actions": 0,
                "shadow_wolf_enraged": False,
            }
            c_input("\nPress Enter to face the shadow...")
            return None

        # ── Phase 3 → 4: 49% HP (shadow wolf defeated) ───────────────
        if hp_pct <= 0.49 and ctx["phase"] == 3:
            ctx["phase"] = 4

            c_print("\n" + "-" * 50)
            c_print('Mary Sue rubs her temples. "The Wolf... was practice. I was')
            c_print('learning how to write REAL fear."')
            c_print("")
            c_print("She turns the page with deliberate care.")
            c_print("")
            c_print('"The Witch was my first truly evil character. I was eleven.')
            c_print('She wasn\'t strong — she was CUNNING. She didn\'t fight you.')
            c_print('She made you fight YOURSELF."')
            c_print("")
            c_print('"Do you know what it\'s like, to create someone whose only')
            c_print('joy is watching you melt?"')
            c_print("-" * 50)

            if dorothy:
                c_print('\n  Dorothy: "She wrote YOU. She wrote the Witch who terrorized my')
                c_print('  whole WORLD. Kansas, Oz — all of it. Every flying monkey. Every')
                c_print('  poppy field. Every tear I shed for Toto. YOU PUT HER THERE."')
                c_print('')
                c_print('  Dorothy gains RUBY RESOLVE: +30% water damage vs the shadow Witch!')

            # Spawn Shadow Witch
            shadow_witch = create_shadow_wicked_witch(player)
            shadow_enemies = [shadow_witch]
            elist.extend(shadow_enemies)
            ctx["_shadow_phase"] = True
            ctx["_shadow_enemies"] = shadow_enemies
            ctx["_shadow_type"] = "witch"
            ctx["_shadow_ctx"] = {
                "shadow_witch_actions": 0,
                "shadow_witch_melting": False,
            }
            c_input("\nPress Enter to face the shadow...")
            return None

        # ── Phase 4 → 5: 32% HP (shadow witch defeated) ──────────────
        if hp_pct <= 0.32 and ctx["phase"] == 4:
            ctx["phase"] = 5

            c_print("\n" + "-" * 50)
            c_print('Mary Sue\'s hand trembles as she turns the page.')
            c_print("")
            c_print('"The Jabberwock... was different. I didn\'t mean to write it.')
            c_print('It just... appeared on the page one night. I was sixteen. I\'d')
            c_print('been having nightmares. When I woke up, it was there — already')
            c_print('written, already real, already hungry."')
            c_print("")
            c_print('"I\'ve been afraid of it ever since. I think... I think it wrote')
            c_print('itself."')
            c_print("-" * 50)

            if alice:
                c_print('\n  Alice: "You wrote the Jabberwock? You... that thing has haunted')
                c_print('  my nightmares since I fell into this place! Every shadow. Every')
                c_print('  pun. Every page that tore itself out of my story — it was YOU?"')
                c_print('')
                c_print('  Alice gains VORPAL CLARITY: 2x damage vs the shadow Jabberwock!')

            # Spawn Shadow Jabberwock
            shadow_jabber = create_shadow_jabberwock(player)
            shadow_enemies = [shadow_jabber]
            elist.extend(shadow_enemies)
            ctx["_shadow_phase"] = True
            ctx["_shadow_enemies"] = shadow_enemies
            ctx["_shadow_type"] = "jabberwock"
            ctx["_shadow_ctx"] = {
                "shadow_jabber_actions": 0,
                "_shadow_vorpal_charging": False,
                "_shadow_vorpal_dmg_taken": 0,
                "_shadow_final_strike_used": False,
            }
            c_input("\nPress Enter to face the shadow...")
            return None

        # ── Phase 5 → 6: 15% HP (shadow jabberwock defeated) ──────────
        if hp_pct <= 0.15 and ctx["phase"] == 5:
            ctx["phase"] = 6

            c_print("\n" + "!" * 50)
            c_print('"NO. This isn\'t how it goes. I\'M the hero. I\'M the one who')
            c_print('saves the day. I\'M the one everyone loves. That\'s how I')
            c_print('WROTE it!"')
            c_print("")
            c_print("She raises her pen. It's glowing — not the warm glow of")
            c_print("creation, but the cold, desperate light of someone trying")
            c_print("to rewrite a story that's already slipped out of their")
            c_print("control.")
            c_print("")
            c_print('"If you won\'t follow the story I wrote... then I\'ll write a')
            c_print('NEW one. One where YOU\'RE the villain!"')
            c_print("!" * 50)

            # Phase 6: Plot Armor does NOT regenerate anymore
            c_print(f'\n  📖 Mary Sue\'s Plot Armor is permanently vulnerable!')
            c_print(f'  ↠ Cannot regenerate. Remaining: {plot_armor["stacks"]} stacks.')

            c_input("\nPress Enter to face the Author's wrath...")
            return None

        return None

    def on_hit_hook(target, elist, ctx):
        """Track damage for various mechanics."""
        sue_ref = ctx.get("_mary_sue_ref")

        # ── Shadow phase: track hits on Mary Sue for damage restoration ─
        if sue_ref and target is sue_ref and ctx.get("_shadow_phase"):
            if not ctx.get("_sue_hit_during_shadow"):
                # Store the pre-hit HP (first hit this round) so we can restore later
                ctx["_sue_pre_hit_hp"] = sue_ref["hp"]
                ctx["_sue_hit_during_shadow"] = True
            c_print("  📖 Mary Sue is narrating — the story shields her from harm!")

        # Track damage for Stu interrupt
        if ctx.get("_stu_charging") and target is ctx.get("_mary_sue_ref"):
            ctx["_stu_damage_taken"] = ctx.get("_stu_damage_taken", 0) + 1  # approximate

        # Track damage for Rewrite (Phase 6)
        if ctx["phase"] == 6 and target is ctx.get("_mary_sue_ref"):
            # We estimate based on HP change
            pass

        # Track shadow Vorpal Beam interrupt damage
        if ctx.get("_shadow_phase") and ctx["_shadow_type"] == "jabberwock":
            shadow_ctx = ctx.get("_shadow_ctx", {})
            if shadow_ctx.get("_shadow_vorpal_charging"):
                shadow_ctx["_shadow_vorpal_dmg_taken"] = shadow_ctx.get("_shadow_vorpal_dmg_taken", 0) + 1

        # Track Plot Armor type stripping
        if target is ctx.get("_mary_sue_ref") and not ctx.get("_shadow_phase"):
            # Try to detect element type — simplified: check player's element_dmg
            plot_armor = ctx.get("_plot_armor", {})
            # This is handled in on_kill/extra_logic; we approximate here
            pass

    def enemy_turn_hook(enemy, ctx, pl, p_con, defending, turn_order=None, step_idx=None):
        """Handle Mary Sue and shadow boss AI."""
        ctx["_player_ref"] = pl
        ctx["_enemies_ref"] = ctx.get("_enemies_ref", [enemy] if isinstance(enemy, dict) else [])

        # ── Shadow phase: delegate to shadow AI ──────────────────────────
        if ctx["_shadow_phase"]:
            shadow_enemies = ctx["_shadow_enemies"]
            shadow_type = ctx["_shadow_type"]
            shadow_ctx = ctx["_shadow_ctx"]

            if enemy in shadow_enemies:
                elist = ctx.get("_enemies_ref", [])

                if shadow_type == "queen":
                    return shadow_queen_turn_hook(enemy, shadow_ctx, pl, p_con, defending, elist)
                elif shadow_type == "wolf":
                    return shadow_wolf_turn_hook(enemy, shadow_ctx, pl, p_con, defending, elist)
                elif shadow_type == "witch":
                    return shadow_witch_turn_hook(enemy, shadow_ctx, pl, p_con, defending, elist)
                elif shadow_type == "jabberwock":
                    return shadow_jabberwock_turn_hook(enemy, shadow_ctx, pl, p_con, defending, elist)

            # Mary Sue during shadow phase: narrates (if her turn comes)
            if _is_mary_sue(enemy):
                shadow_type = ctx["_shadow_type"]
                narration = {
                    "queen": ['\n  Mary Sue: "No, no — the Queen should feint left here. Like this."',
                              '  ↠ Shadow gains +10% dodge for 1 turn!'],
                    "wolf": ['\n  Mary Sue: "More drama! The audience is getting bored!"',
                             '  ↠ Shadow\'s next attack deals +20% damage!'],
                    "witch": ['\n  Mary Sue: "The Witch should be CUNNING, not brute force. Make her tricks more cruel!"',
                              '  ↠ Shadow gains +15% debuff potency for 1 turn!'],
                    "jabberwock": ['\n  Mary Sue: "The Jabberwock should be TERRIFYING. Make it scarier!"',
                                   '  ↠ Shadow gains +15% damage for 1 turn!'],
                }
                lines = narration.get(shadow_type, ['\n  Mary Sue narrates ominously...'])
                for line in lines:
                    c_print(line)
                return 1, True, None, 1.0, 0   # No attack — she's narrating

        # ── Not shadow phase; must be Mary Sue ──────────────────────────
        if not _is_mary_sue(enemy):
            return 1, False, None, 1.0, 0

        # ── Shadow Modifier: Maddening Aura — confusion chance ──────────
        modifiers = ctx.get("_shadow_modifiers", {})
        if "maddening_aura" in modifiers:
            from wonderland_curses import has_shadow
            if has_shadow(pl, "madness_contagion"):
                targets = _get_living_targets(pl)
                if targets and random.random() < 0.50:
                    victim = random.choice(targets)
                    victim.setdefault("active_debuffs", []).append({
                        "type": "confused",
                        "remaining": 1,
                        "source": "mary_sue_madness",
                    })
                    c_print(f'\n  🎭 "{victim.get("name", "Someone")} sees things that aren\'t there..."')
                    c_print(f'  ↠ {victim.get("name", "A party member")} is CONFUSED for 1 turn!')

        # ── Shadow Modifier: Reality Warp — swap positions ──────────────
        if "reality_warp" in modifiers:
            from wonderland_curses import has_shadow
            if has_shadow(pl, "down_rabbit_hole"):
                if random.random() < 0.40:
                    c_print('\n  🕳️ "The floor isn\'t where you left it..."')
                    c_print('  ↠ Reality warps! Party positions shift!')
                    # Force a random active ally to the back row if possible
                    from combat.ally import get_active_allies, get_reserve_allies, can_switch
                    if can_switch(pl):
                        active = get_active_allies(pl)
                        reserve = get_reserve_allies(pl)
                        if active and reserve:
                            ally_to_swap = random.choice(active)
                            reserve_to_swap = random.choice(reserve)
                            # Simple swap notification
                            c_print(f'  ↠ {ally_to_swap["name"]} and {reserve_to_swap["name"]} swap positions!')

        # ── Shadow Modifier: Time Lord — extra turn every 3 turns ───────
        extra_action_this_turn = 0
        if "extra_turn" in modifiers:
            from wonderland_curses import has_shadow
            if has_shadow(pl, "white_rabbit_panic"):
                actions_count = ctx.get("mary_sue_actions", 0)
                if actions_count > 0 and actions_count % 3 == 0:
                    c_print('\n  ⏰ "I\'m not done with you yet."')
                    c_print('  ↠ Mary Sue takes an EXTRA action!')
                    extra_action_this_turn = 1

        # ── Shadow Modifier: Smoke Accuracy — party accuracy debuff ─────
        sue_ref = ctx.get("_mary_sue_ref")
        if "smoke_accuracy_debuff" in modifiers and sue_ref and sue_ref.get("_smoke_aura"):
            from wonderland_curses import has_shadow
            if has_shadow(pl, "caterpillars_smoke"):
                penalty = sue_ref.get("_smoke_aura_penalty", 0.15)
                targets = _get_living_targets(pl)
                applied = 0
                for t in targets:
                    t.setdefault("active_debuffs", []).append({
                        "type": "accuracy_down",
                        "value": -penalty,
                        "remaining": 1,
                        "source": "mary_sue_smoke",
                    })
                    applied += 1
                if applied > 0:
                    c_print(f'\n  💨 Hookah smoke clouds your vision!')
                    c_print(f'  ↠ All party members suffer -{int(penalty*100)}% accuracy for 1 round!')

        # ── Shadow Modifier: Damage Reflect — shattered mirror ──────────
        if "damage_reflect" in modifiers and sue_ref and sue_ref.get("_damage_reflect", 0) > 0:
            from wonderland_curses import has_shadow
            if has_shadow(pl, "looking_glass_shatter"):
                prev_hp = ctx.get("_mary_prev_hp", sue_ref.get("max_hp", sue_ref["hp"]))
                current_hp = sue_ref["hp"]
                dmg_taken = max(0, prev_hp - current_hp)
                if dmg_taken > 0:
                    reflect_pct = sue_ref.get("_damage_reflect", 0.25)
                    reflect_dmg = max(1, int(dmg_taken * reflect_pct))
                    party = _get_living_targets(pl)
                    if party:
                        victim = random.choice(party)
                        c_print(f'\n  💔 Shattered mirror shards fly at {victim.get("name", "someone")}!')
                        c_print(f'  ↠ {reflect_dmg} damage reflected back!')
                        _deal_damage(victim, reflect_dmg, "physical")
            # Store current HP for next damage-reflect check
            ctx["_mary_prev_hp"] = sue_ref["hp"]

        # ── Dispatch to phase handler ───────────────────────────────────
        mary_ctx = ctx
        if ctx["phase"] == 6:
            actions, skip, extra, armor, tstr = _mary_sue_phase5_turn(enemy, pl, mary_ctx)
        else:
            actions, skip, extra, armor, tstr = _mary_sue_phase1_turn(enemy, pl, mary_ctx)

        # Add Time Lord extra action if triggered
        if extra_action_this_turn > 0:
            actions += extra_action_this_turn

        return actions, skip, extra, armor, tstr

    def post_round_hook(ctx, elist):
        """Tick buffs/debuffs, handle per-round effects."""
        # ── Tick Mary Sue buffs/debuffs ──────────────────────────────────
        sue_ref = ctx["_mary_sue_ref"]
        if sue_ref:
            for buff in sue_ref.get("active_buffs", []):
                if "remaining" in buff:
                    buff["remaining"] -= 1
            sue_ref["active_buffs"] = [
                b for b in sue_ref.get("active_buffs", [])
                if b.get("remaining", 999) > 0
            ]
            for debuff in sue_ref.get("active_debuffs", []):
                if "remaining" in debuff:
                    debuff["remaining"] -= 1
            sue_ref["active_debuffs"] = [
                d for d in sue_ref.get("active_debuffs", [])
                if d.get("remaining", 999) > 0
            ]

        # ── Shadow phase: restore Mary Sue's HP if she was attacked ────
        if ctx.get("_sue_hit_during_shadow") and ctx.get("_shadow_phase") and sue_ref:
            pre_hp = ctx.get("_sue_pre_hit_hp", ctx.get("_sue_round_start_hp", sue_ref["hp"]))
            if sue_ref["hp"] < pre_hp:
                c_print(f"\n  📖 The ink rewrites itself — Mary Sue is unharmed by your attacks!")
                sue_ref["hp"] = pre_hp
            ctx["_sue_hit_during_shadow"] = False

        # ── Phase 6 Rewrite damage tracking ──────────────────────────────
        if ctx["phase"] == 6 and sue_ref and sue_ref["hp"] > 0:
            prev_hp = ctx.get("_prev_mary_hp", sue_ref["hp"])
            current_hp = sue_ref["hp"]
            # Track damage taken (healing is negative)
            dmg_taken = max(0, prev_hp - current_hp)
            ctx["_rewrite_damage_tracker"] = ctx.get("_rewrite_damage_tracker", 0) + dmg_taken
            ctx["_prev_mary_hp"] = current_hp

    def on_kill_hook(target, elist, ctx):
        """Handle Mary Sue death, heroine resolution, and victory."""
        if _is_mary_sue(target) and target.get("hp", 0) <= 0:
            # ── Victory narration ──────────────────────────────────────
            c_print("\n" + "=" * 60)
            c_print("Mary Sue falls to her knees. The pen rolls from her")
            c_print("fingers. For the first time, it stops glowing.")
            c_print("")
            c_print('"I... I lost? But I\'m the... the main character..."')
            c_print("")
            c_print("She looks at her hands. They're just hands now. No glow.")
            c_print("No plot armor. No narrative protection. Just a young")
            c_print("woman's hands, ink-stained and shaking.")
            c_print("")
            c_print('"...Oh."')
            c_print("")
            c_print("The word is small. Fragile. The first honest thing she's")
            c_print("ever said.")
            c_print("")
            c_print('"I\'m not, am I? I never was. I was just... writing myself')
            c_print('that way."')
            c_print("")
            c_print("She looks up at you. Her eyes aren't narrating anymore.")
            c_print("They're just seeing. Seeing you. Seeing herself. Seeing")
            c_print("the world without the filter of her own story.")
            c_print("")
            c_print('"Thank you. For not following the script."')
            c_print("")
            c_print("She smiles — a real smile, not a written one — and hands")
            c_print("you the pen.")
            c_print("")
            c_print('"Here. It\'s yours now. Write something good with it.')
            c_print('Something... honest."')
            c_print("")
            c_print("The room of words dissolves. The pages settle. Wonderland")
            c_print("breathes — free, for the first time, from its author's")
            c_print("unconscious grip.")
            c_print("=" * 60)

            # ── Heroine Resolution ─────────────────────────────────────
            _resolve_heroines(player, ctx)

            # ── Drops are handled by dungeon.py dispatch ───────────────

    # ── Run the combat loop ──────────────────────────────────────────────
    return superboss_combat_loop(
        player, enemies, floor, "Mary Sue — The Author", context,
        pre_player_hook=pre_player_hook,
        enemy_turn_hook=enemy_turn_hook,
        post_round_hook=post_round_hook,
        on_kill_hook=on_kill_hook,
        on_player_hit_hook=on_hit_hook,
    )


# ══════════════════════════════════════════════════════════════════════════════
# Heroine Resolution
# ══════════════════════════════════════════════════════════════════════════════

def _resolve_heroines(player, ctx):
    """After Mary Sue is defeated, finalize heroine arcs."""
    from combat.ally import promote_heroine_to_permanent, set_heroine_state, get_heroine_in_party
    resolved_any = False

    # Alice — permanent if Jabberwock was also defeated
    alice = _get_heroine(player, "alice")
    if alice and player.get("wl_boss_defeated_jabberwock"):
        join_level = alice.get("level", player.get("level", 1))
        promote_heroine_to_permanent(player, alice, join_level)
        set_heroine_state(player, "alice", "permanent")
        resolved_any = True
        c_print('\n  Alice closes her eyes. When she opens them, they\'re clearer.')
        c_print('  "The Jabberwock. The Queen. Even the author herself."')
        c_print('  "I think... I think my story is finally my own now."')
        c_print('  Alice becomes a PERMANENT ally.')

    # Red Hood — permanent if Big Bad Wolf was also defeated
    red_hood = _get_heroine(player, "red_hood")
    if red_hood and player.get("wl_boss_defeated_big_bad_wolf"):
        join_level = red_hood.get("level", player.get("level", 1))
        promote_heroine_to_permanent(player, red_hood, join_level)
        set_heroine_state(player, "red_hood", "permanent")
        resolved_any = True
        c_print('\n  Red Hood sheathes her axe. The crimson hood falls back.')
        c_print('  "The Wolf. The one who wrote the Wolf. They\'re both gone."')
        c_print('  "Grandmother can rest now. So can I."')
        c_print('  Red Hood becomes a PERMANENT ally.')

    # Dorothy — permanent if Wicked Witch was also defeated
    dorothy = _get_heroine(player, "dorothy")
    if dorothy and player.get("wl_boss_defeated_wicked_witch"):
        join_level = dorothy.get("level", player.get("level", 1))
        promote_heroine_to_permanent(player, dorothy, join_level)
        set_heroine_state(player, "dorothy", "permanent")
        resolved_any = True
        c_print('\n  Dorothy looks at the ruby slippers on her feet. They\'re glowing')
        c_print('  softly. "The Witch. The one who wrote her. They can\'t keep me')
        c_print('  here anymore."')
        c_print('  She clicks her heels once. The sound echoes — not in the room,')
        c_print('  but somewhere far away.')
        c_print('  "Kansas can wait. You still need me here."')
        c_print('  Dorothy becomes a PERMANENT ally.')

    if resolved_any:
        c_input("\nPress Enter...")

    # If any heroine is in party but their personal boss wasn't defeated,
    # they remain temporary — partial closure.
    if alice and not player.get("wl_boss_defeated_jabberwock"):
        c_print('\n  Alice: "The author is gone, but my Jabberwock... it still waits.')
        c_print('  Some stories need their own ending." She remains temporary.')
    if red_hood and not player.get("wl_boss_defeated_big_bad_wolf"):
        c_print('\n  Red Hood: "She\'s gone. But the Wolf... the real Wolf... he\'s')
        c_print('  still out there. I can feel it." She remains temporary.')
    if dorothy and not player.get("wl_boss_defeated_wicked_witch"):
        c_print('\n  Dorothy: "The author is free. But my Witch... she still cackles')
        c_print('  somewhere in the dark. I can\'t leave yet." She remains temporary.')
