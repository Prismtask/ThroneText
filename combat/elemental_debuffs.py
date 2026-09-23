# combat/elemental_debuffs.py — Elemental Profile Debuff System
"""
Secondary debuff channel driven by enemy elemental_dmg profiles.

Every enemy already has an elemental_dmg profile. This module maps each
element to a thematically appropriate debuff that can proc on-hit based on
the enemy's strongest elemental affinity.

Proc chance scales dynamically with:
  - Base chance (per-element, reflecting debuff potency)
  - Round number (longer combat = more dangerous)
  - Enemy level (higher level = more proficient)

Design doc: unrelated for coding/debuff_and_ai_analysis.md §6
"""

import random
from combat.status_effects import (
    apply_burn_to_player,
    apply_bleed,
    apply_weaken,
    apply_silence,
    apply_dread,
    apply_blind,
    apply_shock_to_player,
    apply_slow_to_player,
    apply_confusion_to_player,
)

# ── Element → (debuff_type, base_chance) ──────────────────────────────────
# Base chances reflect debuff potency: stronger debuffs have lower chances.
ELEMENT_DEBUFF_MAP = {
    "fire":     ("burn",       0.12),
    "water":    ("slow",       0.10),
    "thunder":  ("shock",      0.08),
    "wind":     ("blind",      0.10),
    "earth":    ("weaken",     0.12),
    "light":    ("silence",    0.08),
    "dark":     ("dread",      0.10),
    "physical": ("bleed",      0.15),
    "magical":  ("confusion",  0.08),
}

# ── Debuff → (duration, strength_kwargs) defaults ─────────────────────────
# Strength kwargs are passed directly to the apply_* function.
ELEMENTAL_DEBUFF_DEFAULTS = {
    "burn":       {"duration": 3, "strength": {"tier": None}},   # tier set dynamically
    "slow":       {"duration": 2, "strength": {}},
    "shock":      {"duration": 3, "strength": {"damage": 2}},
    "blind":      {"duration": 2, "strength": {}},
    "weaken":     {"duration": 3, "strength": {"str_penalty": 1}},
    "silence":    {"duration": 2, "strength": {}},
    "dread":      {"duration": 2, "strength": {}},
    "bleed":      {"duration": 4, "strength": {"damage": 2}},
    "confusion":  {"duration": 2, "strength": {}},
}


def get_elemental_debuff(enemy):
    """Return (debuff_type, base_chance) for the enemy's strongest element,
    or None if no element exceeds 1.0 affinity.

    Picks the element with the highest elemental_dmg value > 1.0.
    This keeps the system predictable — players can learn what secondary
    debuff to expect from each enemy type.
    """
    dmg_profile = enemy.get("elemental_dmg", {})
    if not dmg_profile:
        return None

    best_element = None
    best_value = 0.0
    for el, val in dmg_profile.items():
        if val > 1.0 and val > best_value:
            best_value = val
            best_element = el

    if best_element is None:
        return None

    return ELEMENT_DEBUFF_MAP.get(best_element)


def calc_elemental_proc_chance(base_chance, round_num, enemy_level):
    """Calculate scaled proc chance using the formula:

        P = BASE × round_factor × level_factor

    round_factor = 1.0 + (round_num - 1) × 0.08   (caps at 2.5)
    level_factor = 0.5 + (enemy_level / 40)        (caps at 2.0)
    """
    round_factor = min(2.5, 1.0 + (round_num - 1) * 0.08)
    level_factor = min(2.0, 0.5 + (enemy_level / 40))

    return base_chance * round_factor * level_factor


def get_elemental_debuff_params(debuff_type, enemy_level):
    """Return (duration, strength_kwargs) tuned for the given enemy level.

    Strength scales weakly with level so low-level enemies aren't oppressive
    but high-level enemies feel dangerous.
    """
    defaults = ELEMENTAL_DEBUFF_DEFAULTS.get(debuff_type, {})
    duration = defaults.get("duration", 2)
    strength = dict(defaults.get("strength", {}))

    # Per-debuff level scaling
    if debuff_type == "burn":
        # Burn tier scales with enemy level: tier 1 at low levels, up to tier 3 for non-boss
        from combat.status_effects import damage_to_burn_tier
        raw_damage = max(3, enemy_level // 3 + 1)
        strength["tier"] = min(3, damage_to_burn_tier(raw_damage))

    elif debuff_type == "bleed":
        strength["damage"] = max(2, enemy_level // 4)

    elif debuff_type == "shock":
        strength["damage"] = max(2, enemy_level // 5)

    elif debuff_type == "weaken":
        strength["str_penalty"] = max(1, enemy_level // 10)

    return duration, strength


# ── Dispatcher: call the right apply_* function ────────────────────────────
DEBUFF_APPLY_MAP = {
    "burn":       lambda player, dur, kw: apply_burn_to_player(player, tier=kw.get("tier", 1), duration=dur),
    "slow":       lambda player, dur, kw: apply_slow_to_player(player, duration=dur),
    "shock":      lambda player, dur, kw: apply_shock_to_player(player, damage=kw.get("damage", 2), duration=dur),
    "blind":      lambda player, dur, kw: apply_blind(player, duration=dur),
    "weaken":     lambda player, dur, kw: apply_weaken(player, str_penalty=kw.get("str_penalty", 1), duration=dur),
    "silence":    lambda player, dur, kw: apply_silence(player, duration=dur),
    "dread":      lambda player, dur, kw: apply_dread(player, duration=dur),
    "bleed":      lambda player, dur, kw: apply_bleed(player, damage=kw.get("damage", 2), duration=dur),
    "confusion":  lambda player, dur, kw: apply_confusion_to_player(player, duration=dur),
}


def try_apply_elemental_debuff(enemy, player, enemy_dmg):
    """Check and apply elemental debuff after a successful hit.

    Call this after the racial extra_logic in enemy_attack().
    Only procs if damage > 0 (hit landed).

    Returns a message string or None.
    """
    if enemy_dmg <= 0:
        return None

    # Palette, the Chromatic Artisan: paint bursts are the ONLY debuff channel
    if enemy.get("_suppress_elemental_debuff"):
        return None

    elem_result = get_elemental_debuff(enemy)
    if elem_result is None:
        return None

    debuff_type, base_chance = elem_result

    round_num = enemy.get("_combat_round", 1)
    enemy_level = enemy.get("level", 1)
    proc_chance = calc_elemental_proc_chance(base_chance, round_num, enemy_level)

    if random.random() >= proc_chance:
        return None

    # Get tuned params and apply
    duration, strength_kwargs = get_elemental_debuff_params(debuff_type, enemy_level)
    apply_func = DEBUFF_APPLY_MAP.get(debuff_type)
    if apply_func is None:
        return None

    result = apply_func(player, duration, strength_kwargs)

    # Build flavour message — determine which element triggered
    elem_names = {
        "fire": "flames", "water": "frost", "thunder": "sparks",
        "wind": "gale", "earth": "force", "light": "radiance",
        "dark": "shadow", "physical": "savagery", "magical": "arcane feedback",
    }
    debuff_display = {
        "burn": "burning", "slow": "slowed", "shock": "shocked",
        "blind": "blinded", "weaken": "weakened", "silence": "silenced",
        "dread": "dread-filled", "bleed": "bleeding", "confusion": "confused",
    }

    # Find which element triggered this (strongest > 1.0)
    best_el = None
    best_val = 0.0
    for el, val in enemy.get("elemental_dmg", {}).items():
        if val > 1.0 and val > best_val:
            best_val = val
            best_el = el
    aura_name = elem_names.get(best_el, "aura")
    state = debuff_display.get(debuff_type, debuff_type)

    return f"  ✦ The {enemy['name']}'s {aura_name} leaves {player.get('name', 'you')} {state}!"
