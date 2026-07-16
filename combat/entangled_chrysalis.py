# combat/entangled_chrysalis.py
"""Chrysalis, the Entangled One — Superboss encounter.

Pandemonium floor 20 exclusive. Three Temporal Aspects (Past/Present/Future),
three immortal linked shards, Paradox Fracture vulnerability mechanic.
"""

import random
from combat.stats import enemy_stats, compute_player_stats
from combat.superboss_common import superboss_combat_loop
from combat.status_effects import (
    apply_burn, apply_burn_to_player, apply_bleed, apply_weaken,
    apply_momentum, clear_momentum, get_momentum_stacks,
    detonate_burn, detonate_bleed,
)
from combat.ally import get_alive_allies, get_active_allies, compute_ally_stats
from combat.helpers import format_damage_msg
from combat.combat_io import c_print, c_input

# ═══════════════════════════════════════════════════════════════════
# PARADOX FRACTURE HP WRAPPER
# ═══════════════════════════════════════════════════════════════════

class _ParadoxFractureDict(dict):
    """Tiny dict wrapper: intercepts hp reductions to apply Paradox Fracture multiplier.

    When hp is set to a lower value, the decrease is amplified by the
    current Paradox Fracture stacks from the context.
    """
    def __init__(self, base_dict, ctx_ref):
        super().__init__(base_dict)
        self._ctx = ctx_ref  # Reference to mutable context dict

    def __setitem__(self, key, value):
        if key == "hp" and value < self.get("hp", 0):
            pf = self._ctx.get("paradox_fracture", 0)
            if pf > 0:
                diff = self.get("hp", 0) - value
                amplified = int(diff * (1.0 + pf * 0.10))
                super().__setitem__(key, self.get("hp", 0) - amplified)
                return
        super().__setitem__(key, value)


# ═══════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════

BOSS_KEY = "entangled_chrysalis"
SHARD_PYRE = "temporal_shard_pyre"
SHARD_PULSE = "temporal_shard_pulse"
SHARD_RUIN = "temporal_shard_ruin"

SHARD_KEYS = {"past": SHARD_PYRE, "present": SHARD_PULSE, "future": SHARD_RUIN}
SHARD_TO_ASPECT = {SHARD_PYRE: "past", SHARD_PULSE: "present", SHARD_RUIN: "future"}

ASPECT_ICONS = {"past": "🔥", "present": "⚔︁", "future": "🩸"}
ASPECT_NAMES = {"past": "Past", "present": "Present", "future": "Future"}

PHASE_LABELS = {1: "The Weave Awakens", 2: "Threads Tighten", 3: "The Cocoon Breaks"}
MOMENTUM_CAP_P1P2 = 20
MOMENTUM_CAP_P3 = 30

# ═══════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════

def _get_boss(elist):
    return next((e for e in elist if e.get("key") == BOSS_KEY), None)


def _get_shard(elist, shard_key):
    return next((e for e in elist if e.get("key") == shard_key), None)


def _get_stack_threshold(stacks):
    """Return tier based on stack count: 0=base, 1=empowered, 2=transcendent."""
    if stacks >= 21:
        return 2
    elif stacks >= 11:
        return 1
    return 0


def _get_paradox_multiplier(ctx):
    """Damage multiplier for Paradox Fracture on boss (vulnerability)."""
    pf = ctx.get("paradox_fracture", 0)
    return 1.0 + (pf * 0.10)


def _get_momentum_multiplier(boss, defending=False):
    """Return damage multiplier from Momentum stacks. Reduced to 1/3 if Defended."""
    stacks = get_momentum_stacks(boss)
    if stacks <= 0:
        return 1.0
    base = 1.0 + (stacks * 0.03)
    if defending:
        return 1.0 + (base - 1.0) / 3.0
    return base


def _get_boss_stat(boss, stat_key):
    """Get effective stat from boss dict."""
    if stat_key == "str":
        return boss.get("str_mod", 0)
    elif stat_key == "dex":
        return boss.get("dex_mod", 0)
    elif stat_key == "wis":
        return boss.get("wis_mod", 0)
    elif stat_key == "ler":
        return boss.get("ler_mod", 0)
    return 0


def _calc_damage(base_roll, stat_mod, target_con, defending=False, ignore_defend=False):
    """Standard damage calc with optional Defend bypass."""
    raw = base_roll + stat_mod
    block = target_con // 2
    if defending and not ignore_defend:
        block += 5
    dmg = max(0, raw - block)
    if defending and not ignore_defend:
        dmg = int(dmg * 0.5)
    return max(0, dmg)


def _get_target_con(target, player, p_con):
    """Get CON value for a target (player or ally)."""
    if target is player:
        return p_con
    _, a_con, _, _, _, _ = compute_ally_stats(target)
    return a_con


def _get_alive_party(player):
    """Return [player] + active alive allies."""
    party = [player]
    party.extend(get_active_allies(player))
    return party


def _count_burn_bleed(target):
    """Return total (burn_damage, burn_remaining, bleed_damage, bleed_remaining)."""
    burn_dmg, burn_rem, bleed_dmg, bleed_rem = 0, 0, 0, 0
    for d in target.get("active_debuffs", []):
        if d["type"] == "burn":
            burn_dmg = d.get("damage", 0)
            burn_rem = d.get("remaining", 0)
        elif d["type"] == "bleed":
            bleed_dmg = d.get("damage", 0)
            bleed_rem = d.get("remaining", 0)
    return burn_dmg, burn_rem, bleed_dmg, bleed_rem




# ═══════════════════════════════════════════════════════════════════
# DAMAGE HELPERS
# ═══════════════════════════════════════════════════════════════════

def _apply_boss_damage(boss, player, dmg, element="physical", skill_name=None):
    """Apply damage from Chrysalis to player. Returns damage dealt."""
    dmg = max(0, dmg)
    player["current_hp"] -= dmg
    c_print(format_damage_msg(boss["name"], player["name"], dmg,
                               element=element, skill_name=skill_name))
    return dmg


def _heal_boss(boss, amount):
    """Heal boss, capped at max_hp. Returns amount healed."""
    old = boss["hp"]
    boss["hp"] = min(boss.get("max_hp", boss["hp"]), boss["hp"] + amount)
    return boss["hp"] - old


# ═══════════════════════════════════════════════════════════════════
# SKILL: SHARED
# ═══════════════════════════════════════════════════════════════════

def _skill_fluttering_havoc(boss, player, p_con, defending, ctx):
    """Shared: 2-hit physical, applies bleed/burn, Momentum."""
    phase = ctx["phase"]
    dex = _get_boss_stat(boss, "dex")
    # calc burn+bleed on player for scaling
    burn_dmg, burn_rem, bleed_dmg, bleed_rem = _count_burn_bleed(player)
    total_dots = burn_dmg + burn_rem + bleed_dmg + bleed_rem
    dot_bonus = min(3, total_dots // 8)
    mom_mult = _get_momentum_multiplier(boss, defending)

    total_dmg = 0
    # Hit 1: Apply 1 burn
    dmg1 = _calc_damage(random.randint(4, 10), dex, p_con, defending,
                         ignore_defend=(phase >= 3))
    dmg1 = int((dmg1 + dot_bonus) * mom_mult)
    total_dmg += dmg1
    _apply_boss_damage(boss, player, dmg1, element="physical", skill_name="Fluttering Havoc (1/2)")
    apply_burn_to_player(player, tier=5, duration=3)
    c_print("  🔥 Burn applied!")

    # Hit 2: +1 burn duration, +1 bleed duration, Phase 2+ ignores Defend
    dmg2 = _calc_damage(random.randint(4, 10), dex, p_con, defending,
                         ignore_defend=(phase >= 2))
    dmg2 = int((dmg2 + dot_bonus) * mom_mult)
    total_dmg += dmg2
    _apply_boss_damage(boss, player, dmg2, element="physical", skill_name="Fluttering Havoc (2/2)")
    # Extend burn/bleed duration
    for d in player.get("active_debuffs", []):
        if d["type"] == "burn":
            d["remaining"] = d.get("remaining", 0) + 1
        elif d["type"] == "bleed":
            d["remaining"] = d.get("remaining", 0) + 1
    apply_bleed(player, damage=4, duration=3)
    c_print("  🩸 Bleed extended!")

    # Gain Momentum
    apply_momentum(boss, 2, cap=MOMENTUM_CAP_P3 if phase >= 3 else MOMENTUM_CAP_P1P2)

    return total_dmg


def _skill_pulverization(boss, player, p_con, defending, ctx):
    """Shared: 2-hit physical (mirror of Fluttering Havoc with reversed order)."""
    phase = ctx["phase"]
    dex = _get_boss_stat(boss, "dex")
    burn_dmg, burn_rem, bleed_dmg, bleed_rem = _count_burn_bleed(player)
    total_dots = burn_dmg + burn_rem + bleed_dmg + bleed_rem
    dot_bonus = min(3, total_dots // 8)
    mom_mult = _get_momentum_multiplier(boss, defending)

    total_dmg = 0
    # Hit 1: Extend durations
    dmg1 = _calc_damage(random.randint(4, 10), dex, p_con, defending,
                         ignore_defend=(phase >= 3))
    dmg1 = int((dmg1 + dot_bonus) * mom_mult)
    total_dmg += dmg1
    _apply_boss_damage(boss, player, dmg1, element="physical", skill_name="Pulverization (1/2)")
    for d in player.get("active_debuffs", []):
        if d["type"] == "burn":
            d["remaining"] = d.get("remaining", 0) + 1
        elif d["type"] == "bleed":
            d["remaining"] = d.get("remaining", 0) + 1

    # Hit 2: Apply burn
    dmg2 = _calc_damage(random.randint(4, 10), dex, p_con, defending,
                         ignore_defend=(phase >= 2))
    dmg2 = int((dmg2 + dot_bonus) * mom_mult)
    total_dmg += dmg2
    _apply_boss_damage(boss, player, dmg2, element="physical", skill_name="Pulverization (2/2)")
    apply_burn_to_player(player, tier=5, duration=3)
    c_print("  🔥 Burn applied!")

    apply_momentum(boss, 2, cap=MOMENTUM_CAP_P3 if phase >= 3 else MOMENTUM_CAP_P1P2)

    return total_dmg


def _skill_chaotic_turmoil(boss, player, p_con, defending, ctx):
    """Shared: Dark 1-hit ignores Defend, repeats based on missing HP."""
    phase = ctx["phase"]
    ler = _get_boss_stat(boss, "ler")
    burn_dmg, burn_rem, bleed_dmg, bleed_rem = _count_burn_bleed(player)
    total_dots = burn_dmg + burn_rem + bleed_dmg + bleed_rem
    dot_bonus = min(6, total_dots // 6)
    mom = get_momentum_stacks(boss)
    mom_bonus = min(3, mom // 6)

    hp_pct = boss["hp"] / max(1, boss.get("max_hp", 1))
    if hp_pct > 0.66:
        repeats = 1
    elif hp_pct > 0.33:
        repeats = 2
    else:
        repeats = 3

    total_dmg = 0
    for i in range(repeats):
        if player["current_hp"] <= 0:
            break
        dmg = _calc_damage(random.randint(6, 14), ler, p_con, False, ignore_defend=True)
        dmg = dmg + dot_bonus + mom_bonus
        total_dmg += dmg
        _apply_boss_damage(boss, player, dmg, element="dark",
                           skill_name=f"Chaotic Turmoil ({i+1}/{repeats})")
        apply_burn_to_player(player, tier=5, duration=3)
        apply_bleed(player, damage=4, duration=3)
        apply_momentum(boss, 1, cap=MOMENTUM_CAP_P3 if phase >= 3 else MOMENTUM_CAP_P1P2)
        c_print("  🔥🩸 Burn + Bleed applied!")

    return total_dmg


# ═══════════════════════════════════════════════════════════════════
# SKILL: PAST ASPECT (🔥 Fire / Burn)
# ═══════════════════════════════════════════════════════════════════

def _skill_temper_and_cast(boss, player, p_con, defending, ctx):
    """Past: 2-hit fire, detonates burn on hit 2."""
    phase = ctx["phase"]
    past_stacks = ctx["past_stacks"]
    wis = _get_boss_stat(boss, "wis")
    burn_dmg, burn_rem, _, _ = _count_burn_bleed(player)
    burn_bonus = min(6, (burn_dmg + burn_rem) // 6)

    total_dmg = 0
    # Hit 1: Apply burn
    dmg1 = _calc_damage(random.randint(5, 10), wis, p_con, defending,
                         ignore_defend=(phase >= 3))
    dmg1 += burn_bonus
    total_dmg += dmg1
    _apply_boss_damage(boss, player, dmg1, element="fire", skill_name="Temper and Cast (1/2)")
    apply_burn_to_player(player, tier=5, duration=3)
    # +1 burn duration
    for d in player.get("active_debuffs", []):
        if d["type"] == "burn":
            d["remaining"] = d.get("remaining", 0) + 1

    # Hit 2: Detonate burn
    dmg2 = _calc_damage(random.randint(5, 10), wis, p_con, defending,
                         ignore_defend=(phase >= 2))
    dmg2 += burn_bonus
    total_dmg += dmg2
    _apply_boss_damage(boss, player, dmg2, element="fire", skill_name="Temper and Cast (2/2)")

    # Detonate
    party = _get_alive_party(player)
    det_dmg, msgs = detonate_burn(player, all_party=party)
    if det_dmg == 0:
        # Fallback
        fallback = past_stacks * 2
        player["current_hp"] = max(0, player["current_hp"] - fallback)
        c_print(f"  🔥 No burn to detonate —{fallback} damage")
        total_dmg += fallback
    else:
        total_dmg += det_dmg
        for m in msgs:
            c_print(f"  {m}")

    return total_dmg


def _skill_immolation(boss, player, p_con, defending, ctx):
    """Past: 3-hit fire, heavy burn detonation."""
    phase = ctx["phase"]
    past_stacks = ctx["past_stacks"]
    wis = _get_boss_stat(boss, "wis")
    burn_dmg, burn_rem, _, _ = _count_burn_bleed(player)
    burn_bonus = min(6, (burn_dmg + burn_rem) // 6)
    past_pct = min(60, past_stacks * 2) / 100.0

    total_dmg = 0
    # Hit 1: +2 burn duration
    dmg1 = _calc_damage(random.randint(5, 12), wis, p_con, defending,
                         ignore_defend=(phase >= 3))
    dmg1 = int((dmg1 + burn_bonus) * (1.0 + past_pct))
    total_dmg += dmg1
    _apply_boss_damage(boss, player, dmg1, element="fire", skill_name="Immolation (1/3)")
    for d in player.get("active_debuffs", []):
        if d["type"] == "burn":
            d["remaining"] = d.get("remaining", 0) + 2

    # Hit 2: Apply 3 burn
    dmg2 = _calc_damage(random.randint(5, 12), wis, p_con, defending,
                         ignore_defend=(phase >= 3))
    dmg2 = int((dmg2 + burn_bonus) * (1.0 + past_pct))
    total_dmg += dmg2
    _apply_boss_damage(boss, player, dmg2, element="fire", skill_name="Immolation (2/3)")
    apply_burn_to_player(player, tier=5, duration=3)
    c_print("  🔥 Heavy burn applied!")

    # Hit 3: Detonate (ignores Defend DR)
    dmg3 = _calc_damage(random.randint(5, 12), wis, p_con, False, ignore_defend=True)
    dmg3 = int((dmg3 + burn_bonus) * (1.0 + past_pct))
    total_dmg += dmg3
    _apply_boss_damage(boss, player, dmg3, element="fire", skill_name="Immolation (3/3)")

    party = _get_alive_party(player)
    det_dmg, msgs = detonate_burn(player, all_party=party)
    if det_dmg == 0:
        fallback = past_stacks * 3
        player["current_hp"] = max(0, player["current_hp"] - fallback)
        c_print(f"  🔥 No burn to detonate —{fallback} damage")
        total_dmg += fallback
    else:
        total_dmg += det_dmg
        for m in msgs:
            c_print(f"  {m}")

    # If player Defended or Phase 3: re-apply a small burn then detonate again
    if defending or phase >= 3:
        apply_burn_to_player(player, tier=5, duration=2)
        det_dmg2, msgs2 = detonate_burn(player, all_party=party)
        if det_dmg2 > 0:
            total_dmg += det_dmg2
            for m in msgs2:
                c_print(f"  {m}")

    return total_dmg


def _skill_kalpagni(boss, player, p_con, defending, ctx):
    """Past Signature: 4-hit fire, all ignore Defend DR."""
    past_stacks = ctx["past_stacks"]
    wis = _get_boss_stat(boss, "wis")
    burn_dmg, burn_rem, _, _ = _count_burn_bleed(player)
    burn_bonus = min(6, (burn_dmg + burn_rem) // 6)
    past_pct = min(120, past_stacks * 4) / 100.0

    total_dmg = 0
    # Hit 1: Apply burn, +1 duration
    dmg1 = _calc_damage(random.randint(6, 14), wis, p_con, False, ignore_defend=True)
    dmg1 = int((dmg1 + 2) * (1.0 + past_pct))  # +2 flat from signature
    total_dmg += dmg1
    _apply_boss_damage(boss, player, dmg1, element="fire", skill_name="Kalpāgni (1/4)")
    apply_burn_to_player(player, tier=5, duration=3)
    for d in player.get("active_debuffs", []):
        if d["type"] == "burn":
            d["remaining"] = d.get("remaining", 0) + 1

    # Hit 2: Apply burn, +1 duration
    dmg2 = _calc_damage(random.randint(6, 14), wis, p_con, False, ignore_defend=True)
    dmg2 = int((dmg2 + 2) * (1.0 + past_pct))
    total_dmg += dmg2
    _apply_boss_damage(boss, player, dmg2, element="fire", skill_name="Kalpāgni (2/4)")
    apply_burn_to_player(player, tier=5, duration=3)
    for d in player.get("active_debuffs", []):
        if d["type"] == "burn":
            d["remaining"] = d.get("remaining", 0) + 1

    # Hit 3: Detonate
    dmg3 = _calc_damage(random.randint(6, 14), wis, p_con, False, ignore_defend=True)
    dmg3 = int((dmg3 + 2) * (1.0 + past_pct))
    total_dmg += dmg3
    _apply_boss_damage(boss, player, dmg3, element="fire", skill_name="Kalpāgni (3/4)")
    party = _get_alive_party(player)
    det_dmg, msgs = detonate_burn(player, all_party=party)
    if det_dmg == 0:
        fallback = past_stacks * 3
        player["current_hp"] = max(0, player["current_hp"] - fallback)
        c_print(f"  🔥 No burn to detonate —{fallback} raw damage!")
        total_dmg += fallback
    else:
        total_dmg += det_dmg
        for m in msgs:
            c_print(f"  {m}")

    # Hit 4: Curse damage (past_stacks / 2)
    curse_dmg = past_stacks // 2
    player["current_hp"] = max(0, player["current_hp"] - curse_dmg)
    c_print(f"  💀 Kalpāgni final strike: {curse_dmg} curse damage!")
    total_dmg += curse_dmg
    # Re-apply 1 burn
    apply_burn_to_player(player, tier=5, duration=3)

    # After skill: if Defended, halve past stacks + Weaken + Slow
    if defending:
        ctx["past_stacks"] = ctx["past_stacks"] // 2
        c_print("  🌫 Past stacks halved! Chrysalis is weakened and slowed.")
        boss["slowed"] = True
        boss.setdefault("active_debuffs", []).append({"type": "weaken", "remaining": 2})
        if "str_mod" in boss:
            boss["str_mod"] = max(0, boss.get("str_mod", 0) - 2)
    else:
        ctx["past_stacks"] = min(30, ctx["past_stacks"] + 5)
        c_print(f"  🔥 Past Aspect surges! ({ctx['past_stacks']}/30)")

    # Phase 3: detonate again
    if ctx["phase"] >= 3:
        det_dmg3, msgs3 = detonate_burn(player, all_party=party)
        if det_dmg3 > 0:
            total_dmg += det_dmg3
            for m in msgs3:
                c_print(f"  {m}")

    return total_dmg


# ═══════════════════════════════════════════════════════════════════
# SKILL: PRESENT ASPECT (⚔︁Physical / Momentum)
# ═══════════════════════════════════════════════════════════════════

def _skill_anitya(boss, player, p_con, defending, ctx):
    """Present: 2-hit physical, Momentum scaling."""
    phase = ctx["phase"]
    dex = _get_boss_stat(boss, "dex")
    mom = get_momentum_stacks(boss)
    mom_bonus = min(6, mom // 6)
    mom_mult = _get_momentum_multiplier(boss, defending)

    # Before attack: gain 2 Momentum
    apply_momentum(boss, 2, cap=MOMENTUM_CAP_P3 if phase >= 3 else MOMENTUM_CAP_P1P2)
    mom = get_momentum_stacks(boss)

    total_dmg = 0
    # Hit 1: Gain 1 Momentum
    dmg1 = _calc_damage(random.randint(4, 10), dex, p_con, defending,
                         ignore_defend=(phase >= 3))
    dmg1 = int((dmg1 + mom_bonus) * mom_mult)
    total_dmg += dmg1
    _apply_boss_damage(boss, player, dmg1, element="physical", skill_name="Anitya (1/2)")
    apply_momentum(boss, 1, cap=MOMENTUM_CAP_P3 if phase >= 3 else MOMENTUM_CAP_P1P2)

    # Hit 2: Deal (Momentum_stacks / 2) bonus damage
    dmg2 = _calc_damage(random.randint(4, 10), dex, p_con, defending,
                         ignore_defend=(phase >= 2))
    dmg2 = int((dmg2 + mom_bonus) * mom_mult)
    bonus = get_momentum_stacks(boss) // 2
    dmg2 += bonus
    total_dmg += dmg2
    _apply_boss_damage(boss, player, dmg2, element="physical", skill_name="Anitya (2/2)")
    if bonus > 0:
        c_print(f"  ⚔︁ +{bonus} Momentum bonus damage!")

    return total_dmg


def _skill_skypiercer(boss, player, p_con, defending, ctx):
    """Present: 4-hit physical, heavy Momentum scaling."""
    phase = ctx["phase"]
    dex = _get_boss_stat(boss, "dex")
    present_stacks = ctx["present_stacks"]
    mom_bonus = min(6, get_momentum_stacks(boss) // 6)
    present_pct = min(60, present_stacks * 2) / 100.0
    mom_mult = _get_momentum_multiplier(boss, defending)

    cap = MOMENTUM_CAP_P3 if phase >= 3 else MOMENTUM_CAP_P1P2
    apply_momentum(boss, 3, cap=cap)
    mom = get_momentum_stacks(boss)

    total_dmg = 0
    # Hit 1: Gain 1 Momentum
    dmg1 = _calc_damage(random.randint(5, 12), dex, p_con, defending,
                         ignore_defend=(phase >= 3))
    dmg1 = int((dmg1 + mom_bonus) * mom_mult * (1.0 + present_pct))
    total_dmg += dmg1
    _apply_boss_damage(boss, player, dmg1, element="physical", skill_name="Skypiercer (1/4)")
    apply_momentum(boss, 1, cap=cap)

    # Hit 2: Gain 2 Momentum
    dmg2 = _calc_damage(random.randint(5, 12), dex, p_con, defending,
                         ignore_defend=(phase >= 3))
    dmg2 = int((dmg2 + mom_bonus) * mom_mult * (1.0 + present_pct))
    total_dmg += dmg2
    _apply_boss_damage(boss, player, dmg2, element="physical", skill_name="Skypiercer (2/4)")
    apply_momentum(boss, 2, cap=cap)

    # Hit 3: +(Momentum)% bonus damage, ignores Defend DR
    dmg3 = _calc_damage(random.randint(5, 12), dex, p_con, False, ignore_defend=True)
    mom = get_momentum_stacks(boss)
    mom_pct = min(50, mom) / 100.0
    if defending:
        mom_pct = mom_pct / 2.0
    dmg3 = int((dmg3 + mom_bonus) * mom_mult * (1.0 + present_pct + mom_pct))
    total_dmg += dmg3
    _apply_boss_damage(boss, player, dmg3, element="physical", skill_name="Skypiercer (3/4)")

    # Hit 4: +(Momentum * 2)% bonus damage, ignores Defend DR
    dmg4 = _calc_damage(random.randint(5, 12), dex, p_con, False, ignore_defend=True)
    mom_pct2 = min(100, mom * 2) / 100.0
    if defending:
        mom_pct2 = mom_pct2 / 2.0
    dmg4 = int((dmg4 + mom_bonus) * mom_mult * (1.0 + present_pct + mom_pct2))
    total_dmg += dmg4
    _apply_boss_damage(boss, player, dmg4, element="physical", skill_name="Skypiercer (4/4)")

    return total_dmg


def _skill_smite_the_wicked(boss, player, p_con, defending, ctx):
    """Present Signature: 1-hit heavy physical, ignores Defend, kill chain."""
    present_stacks = ctx["present_stacks"]
    dex = _get_boss_stat(boss, "dex")
    mom = get_momentum_stacks(boss)
    mom_bonus = min(6, mom // 6)
    present_pct = min(120, present_stacks * 4) / 100.0
    mom_mult = _get_momentum_multiplier(boss, defending)

    cap = MOMENTUM_CAP_P3 if ctx["phase"] >= 3 else MOMENTUM_CAP_P1P2
    apply_momentum(boss, 4, cap=cap)
    mom = get_momentum_stacks(boss)

    # If 20+ Momentum and not Defending: consume surplus for bonus
    surplus_bonus = 0
    if mom >= 20 and not defending:
        surplus = min(20, mom - 4)  # 4 was just added
        if surplus > 0:
            surplus_bonus = surplus * 5  # +5% per surplus
            # Consume surplus Momentum
            for b in boss.get("active_buffs", []):
                if b.get("type") == "momentum":
                    b["value"] = max(0, b["value"] - surplus)

    # Physical penetration: 50% resist ignore
    dmg = _calc_damage(random.randint(10, 20), dex, p_con, False, ignore_defend=True)
    dmg = int((dmg + mom_bonus + 2) * mom_mult * (1.0 + present_pct + surplus_bonus / 100.0))

    _apply_boss_damage(boss, player, dmg, element="physical", skill_name="Smite the Wicked")
    total_dmg = dmg

    # After skill
    if defending:
        ctx["present_stacks"] = ctx["present_stacks"] // 2
        c_print("  ⚔︁ Present stacks halved! Chrysalis is weakened and slowed.")
        boss["slowed"] = True
        boss.setdefault("active_debuffs", []).append({"type": "weaken", "remaining": 1})
        if "str_mod" in boss:
            boss["str_mod"] = max(0, boss.get("str_mod", 0) - 2)
        if ctx["phase"] >= 3:
            # Bonus damage even on Defend
            bonus = dmg // 2
            player["current_hp"] = max(0, player["current_hp"] - bonus)
            c_print(f"  ⚔︁ Phase 3: +{bonus} bonus damage pierces your guard!")
            total_dmg += bonus
    else:
        ctx["present_stacks"] = min(30, ctx["present_stacks"] + 5)
        c_print(f"  ⚔︁ Present Aspect surges! ({ctx['present_stacks']}/30)")
        # Target gains Vulnerable
        player.setdefault("active_debuffs", []).append({
            "type": "vulnerable", "remaining": 1, "value": 25
        })
        c_print("  💔 You are Vulnerable (+25% damage taken, 1 turn)!")

    # Kill chain (not applicable in single-player boss fight, but for consistency)
    if player["current_hp"] <= 0:
        c_print("  ☠ Smite the Wicked claims its target!")

    return total_dmg


# ═══════════════════════════════════════════════════════════════════
# SKILL: FUTURE ASPECT (🩸 Dark / Bleed)
# ═══════════════════════════════════════════════════════════════════

def _skill_corrosive_disintegration(boss, player, p_con, defending, ctx):
    """Future: 2-hit dark, detonates bleed on hit 2."""
    phase = ctx["phase"]
    future_stacks = ctx["future_stacks"]
    ler = _get_boss_stat(boss, "ler")
    _, _, bleed_dmg, bleed_rem = _count_burn_bleed(player)
    bleed_bonus = min(6, (bleed_dmg + bleed_rem) // 6)

    total_dmg = 0
    # Hit 1: Apply bleed
    dmg1 = _calc_damage(random.randint(4, 10), ler, p_con, defending,
                         ignore_defend=(phase >= 3))
    dmg1 += bleed_bonus
    total_dmg += dmg1
    _apply_boss_damage(boss, player, dmg1, element="dark", skill_name="Corrosive Disintegration (1/2)")
    apply_bleed(player, damage=5, duration=3)
    c_print("  🩸 Bleed applied!")

    # Hit 2: Detonate bleed
    dmg2 = _calc_damage(random.randint(4, 10), ler, p_con, defending,
                         ignore_defend=(phase >= 2))
    dmg2 += bleed_bonus
    total_dmg += dmg2
    _apply_boss_damage(boss, player, dmg2, element="dark", skill_name="Corrosive Disintegration (2/2)")

    det_dmg, msgs = detonate_bleed(player)
    if det_dmg == 0:
        fallback = future_stacks * 2
        player["current_hp"] = max(0, player["current_hp"] - fallback)
        c_print(f"  🩸 No bleed to detonate —{fallback} raw damage!")
        total_dmg += fallback
        _heal_boss(boss, fallback)
    else:
        total_dmg += det_dmg
        for m in msgs:
            c_print(f"  {m}")
        healed = _heal_boss(boss, det_dmg)
        if healed > 0:
            c_print(f"  🩸 Chrysalis heals {healed} HP from detonation!")

    return total_dmg


def _skill_rotting_annihilation(boss, player, p_con, defending, ctx):
    """Future: 2-hit dark, heavy bleed detonation."""
    phase = ctx["phase"]
    future_stacks = ctx["future_stacks"]
    ler = _get_boss_stat(boss, "ler")
    _, _, bleed_dmg, bleed_rem = _count_burn_bleed(player)
    bleed_bonus = min(6, (bleed_dmg + bleed_rem) // 6)
    future_pct = min(60, future_stacks * 2) / 100.0

    total_dmg = 0
    # Hit 1: Apply 2 bleed, +2 duration
    dmg1 = _calc_damage(random.randint(5, 12), ler, p_con, defending,
                         ignore_defend=(phase >= 3))
    dmg1 = int((dmg1 + bleed_bonus) * (1.0 + future_pct))
    total_dmg += dmg1
    _apply_boss_damage(boss, player, dmg1, element="dark", skill_name="Rotting Annihilation (1/2)")
    apply_bleed(player, damage=6, duration=4)
    for d in player.get("active_debuffs", []):
        if d["type"] == "bleed":
            d["remaining"] = d.get("remaining", 0) + 2
    c_print("  🩸 Heavy bleed applied!")

    # Hit 2: Detonate (ignores Defend DR)
    dmg2 = _calc_damage(random.randint(5, 12), ler, p_con, False, ignore_defend=True)
    dmg2 = int((dmg2 + bleed_bonus) * (1.0 + future_pct))
    total_dmg += dmg2
    _apply_boss_damage(boss, player, dmg2, element="dark", skill_name="Rotting Annihilation (2/2)")

    det_dmg, msgs = detonate_bleed(player)
    if det_dmg == 0:
        fallback = future_stacks * 3
        player["current_hp"] = max(0, player["current_hp"] - fallback)
        c_print(f"  🩸 No bleed to detonate —{fallback} raw damage!")
        total_dmg += fallback
        _heal_boss(boss, fallback)
    else:
        total_dmg += det_dmg
        for m in msgs:
            c_print(f"  {m}")
        healed = _heal_boss(boss, det_dmg)
        if healed > 0:
            c_print(f"  🩸 Chrysalis heals {healed} HP from detonation!")

    # If Defended or Phase 3: re-apply a small bleed then detonate again
    if defending or phase >= 3:
        apply_bleed(player, damage=3, duration=2)
        det_dmg2, msgs2 = detonate_bleed(player)
        if det_dmg2 > 0:
            total_dmg += det_dmg2
            for m in msgs2:
                c_print(f"  {m}")
            healed2 = _heal_boss(boss, det_dmg2)
            if healed2 > 0:
                c_print(f"  🩸 Chrysalis heals {healed2} HP from second detonation!")

    return total_dmg


def _skill_bloodflower(boss, player, p_con, defending, ctx):
    """Future Signature: 2-hit dark, all ignore Defend, cross-Aspect contamination."""
    future_stacks = ctx["future_stacks"]
    ler = _get_boss_stat(boss, "ler")
    _, _, bleed_dmg, bleed_rem = _count_burn_bleed(player)
    bleed_bonus = min(6, (bleed_dmg + bleed_rem) // 6)
    future_pct = min(120, future_stacks * 4) / 100.0

    total_dmg = 0
    # Hit 1: Apply 1 bleed, +1 duration
    dmg1 = _calc_damage(random.randint(6, 16), ler, p_con, False, ignore_defend=True)
    dmg1 = int((dmg1 + 2) * (1.0 + future_pct))  # +2 flat
    total_dmg += dmg1
    _apply_boss_damage(boss, player, dmg1, element="dark", skill_name="Bloodflower (1/2)")
    apply_bleed(player, damage=5, duration=3)
    for d in player.get("active_debuffs", []):
        if d["type"] == "bleed":
            d["remaining"] = d.get("remaining", 0) + 1

    # Hit 2: Detonate + cross-Aspect contamination
    dmg2 = _calc_damage(random.randint(6, 16), ler, p_con, False, ignore_defend=True)
    dmg2 = int((dmg2 + 2) * (1.0 + future_pct))
    total_dmg += dmg2
    _apply_boss_damage(boss, player, dmg2, element="dark", skill_name="Bloodflower (2/2)")

    det_dmg, msgs = detonate_bleed(player)
    if det_dmg == 0:
        fallback = future_stacks * 3
        player["current_hp"] = max(0, player["current_hp"] - fallback)
        c_print(f"  🩸 No bleed to detonate —{fallback} raw damage!")
        total_dmg += fallback
        _heal_boss(boss, fallback)
    else:
        total_dmg += det_dmg
        for m in msgs:
            c_print(f"  {m}")
        healed = _heal_boss(boss, det_dmg)
        if healed > 0:
            c_print(f"  🩸 Chrysalis heals {healed} HP from detonation!")

    # Cross-Aspect contamination: inflict 2 burn + 3 burn duration
    apply_burn_to_player(player, tier=5, duration=5)
    for d in player.get("active_debuffs", []):
        if d["type"] == "burn":
            d["remaining"] = d.get("remaining", 0) + 2
    c_print("  🔥 Cross-Aspect contamination: Burn applied!")

    # Signature bonus heal
    sig_heal = future_stacks * 3
    healed_sig = _heal_boss(boss, sig_heal)
    if healed_sig > 0:
        c_print(f"  🩸 Bloodflower heals Chrysalis for {healed_sig} HP!")

    # After skill
    if defending:
        ctx["future_stacks"] = ctx["future_stacks"] // 2
        c_print("  🌫 Future stacks halved! Chrysalis is weakened and slowed.")
        boss["slowed"] = True
        boss.setdefault("active_debuffs", []).append({"type": "weaken", "remaining": 2})
        if "str_mod" in boss:
            boss["str_mod"] = max(0, boss.get("str_mod", 0) - 2)
    else:
        ctx["future_stacks"] = min(30, ctx["future_stacks"] + 5)
        c_print(f"  🩸 Future Aspect surges! ({ctx['future_stacks']}/30)")

    # Phase 3: re-apply a small bleed then detonate again
    if ctx["phase"] >= 3:
        apply_bleed(player, damage=3, duration=2)
        det_dmg3, msgs3 = detonate_bleed(player)
        if det_dmg3 > 0:
            total_dmg += det_dmg3
            for m in msgs3:
                c_print(f"  {m}")
            healed3 = _heal_boss(boss, det_dmg3)
            if healed3 > 0:
                c_print(f"  🩸 Chrysalis heals {healed3} HP from Phase 3 detonation!")

    return total_dmg


# ═══════════════════════════════════════════════════════════════════
# SKILL DISPATCH
# ═══════════════════════════════════════════════════════════════════

# Skill cycles per Aspect, per phase
# Phase 1: [shared, aspect_basic, aspect_sig]
# Phase 2: [shared, aspect_mid, aspect_sig]  (2 actions)
# Phase 3: [aspect_basic, aspect_mid, aspect_sig]  (2 actions, shortened)

def _get_skill_for_cycle(aspect, cycle, phase):
    """Return (skill_name, skill_func) for current cycle position."""
    if phase == 1:
        # Phase 1: 3-turn cycle with shared skills (1 action/turn)
        # Turn 1: Fluttering Havoc, Turn 2: Aspect basic, Turn 3: Aspect signature
        if cycle == 0:
            return "Fluttering Havoc", _skill_fluttering_havoc
        elif cycle == 1:
            if aspect == "past":
                return "Temper and Cast", _skill_temper_and_cast
            elif aspect == "present":
                return "Anitya", _skill_anitya
            else:
                return "Corrosive Disintegration", _skill_corrosive_disintegration
        else:  # cycle == 2
            if aspect == "past":
                return "Kalpāgni", _skill_kalpagni
            elif aspect == "present":
                return "Smite the Wicked", _skill_smite_the_wicked
            else:
                return "Bloodflower", _skill_bloodflower
    elif phase == 2:
        # Phase 2: 5-skill expanded cycle (2 actions/turn)
        # Past:    Temper →Fluttering →Immolation →Pulverization →Kalpāgni
        # Present: Anitya →Fluttering →Skypiercer →Pulverization →Smite the Wicked
        # Future:  Corrosive →Fluttering →Rotting Annih. →Pulverization →Bloodflower
        if cycle == 0:
            if aspect == "past":
                return "Temper and Cast", _skill_temper_and_cast
            elif aspect == "present":
                return "Anitya", _skill_anitya
            else:
                return "Corrosive Disintegration", _skill_corrosive_disintegration
        elif cycle == 1:
            return "Fluttering Havoc", _skill_fluttering_havoc
        elif cycle == 2:
            if aspect == "past":
                return "Immolation", _skill_immolation
            elif aspect == "present":
                return "Skypiercer", _skill_skypiercer
            else:
                return "Rotting Annihilation", _skill_rotting_annihilation
        elif cycle == 3:
            return "Pulverization", _skill_pulverization
        else:  # cycle == 4
            if aspect == "past":
                return "Kalpāgni", _skill_kalpagni
            elif aspect == "present":
                return "Smite the Wicked", _skill_smite_the_wicked
            else:
                return "Bloodflower", _skill_bloodflower
    else:
        # Phase 3: 3-skill shortened cycle (2 actions/turn, empowered)
        # Past:    Temper and Cast →Immolation →Kalpāgni
        # Present: Anitya →Skypiercer →Smite the Wicked
        # Future:  Corrosive →Rotting Annih. →Bloodflower
        if cycle == 0:
            if aspect == "past":
                return "Temper and Cast", _skill_temper_and_cast
            elif aspect == "present":
                return "Anitya", _skill_anitya
            else:
                return "Corrosive Disintegration", _skill_corrosive_disintegration
        elif cycle == 1:
            if aspect == "past":
                return "Immolation", _skill_immolation
            elif aspect == "present":
                return "Skypiercer", _skill_skypiercer
            else:
                return "Rotting Annihilation", _skill_rotting_annihilation
        else:  # cycle == 2
            if aspect == "past":
                return "Kalpāgni", _skill_kalpagni
            elif aspect == "present":
                return "Smite the Wicked", _skill_smite_the_wicked
            else:
                return "Bloodflower", _skill_bloodflower


# ═══════════════════════════════════════════════════════════════════
# HOOKS
# ═══════════════════════════════════════════════════════════════════

def _pre_player_hook(ctx, enemies):
    """Round-start: phase transitions, Aspect switching, Paradox Fracture, shard regen."""
    boss = _get_boss(enemies)
    if not boss:
        return None

    # ── Shard damage redirect (from last round's damage) ────
    for aspect, shard_key in SHARD_KEYS.items():
        shard = _get_shard(enemies, shard_key)
        if shard and "_hp_snapshot" in shard:
            lost = shard["_hp_snapshot"] - shard["hp"]
            if lost > 0:
                redirect = lost // 2
                if redirect > 0:
                    boss["hp"] = max(0, boss["hp"] - redirect)
                    c_print(f"  {shard['name']} transfers {redirect} damage to Chrysalis through the temporal bond.")

    # ── Safety: if Chrysalis died from redirect damage, destroy shards ──
    if boss["hp"] <= 0:
        c_print("\n  💥 The Entangled One collapses from the temporal backlash!")
        for e in enemies:
            if e.get("key") in SHARD_KEYS.values():
                e["hp"] = 0
        return None  # Let prune_dead handle victory

    hp_pct = boss["hp"] / max(1, boss.get("max_hp", 1))

    # ── Phase transitions ────────────────────────────────────
    if hp_pct <= 0.33 and ctx["phase"] < 3:
        ctx["phase"] = 3
        active = ctx["active_aspect"]
        for asp in ["past", "present", "future"]:
            bonus = 15 if asp == active else 5
            ctx[f"{asp}_stacks"] = min(30, ctx[f"{asp}_stacks"] + bonus)
        c_print("\n[PHASE 3] 'THE COCOON BREAKS.' All attacks ignore Defend DR!")
        c_print(f"  {active.title()} Aspect surges +15, others +5!")
    elif hp_pct <= 0.66 and ctx["phase"] < 2:
        ctx["phase"] = 2
        active = ctx["active_aspect"]
        for asp in ["past", "present", "future"]:
            bonus = 15 if asp == active else 5
            ctx[f"{asp}_stacks"] = min(30, ctx[f"{asp}_stacks"] + bonus)
        c_print(f"\n[PHASE 2] 'THE WEAVE TIGHTENS.' {active.title()} Aspect surges +15!")
        c_print(f"  Other Aspects +5. 2 actions per turn!")

    # ── Determine active Aspect ──────────────────────────────
    stacks = {
        "past": ctx["past_stacks"],
        "present": ctx["present_stacks"],
        "future": ctx["future_stacks"],
    }
    max_aspect = max(stacks, key=stacks.get)
    max_val = stacks[max_aspect]
    tied = [a for a, v in stacks.items() if v == max_val]

    if len(tied) > 1 and ctx["active_aspect"] in tied:
        pass  # Stay on current
    elif max_aspect != ctx["active_aspect"]:
        old = ctx["active_aspect"]
        ctx["active_aspect"] = max_aspect
        ctx["paradox_fracture"] = min(10, ctx["paradox_fracture"] + 1)
        c_print(f"\n⏳ TEMPORAL SHIFT: {old.upper()} → {max_aspect.upper()}!")
        c_print(f"   Paradox Fracture: {ctx['paradox_fracture']}/10 (+{ctx['paradox_fracture']*10}% damage taken)")

        # Clear Momentum if switching away from Present
        if old == "present":
            clear_momentum(boss)
            c_print("   ⚔︁ Momentum dissipates as the Present slips away.")

        # Announce at thresholds
        pf = ctx["paradox_fracture"]
        if pf >= 10:
            c_print("💥 PARADOX FRACTURE MAX! The timelines collapse — Chrysalis is EXPOSED!")
            boss["slowed"] = True
            boss.setdefault("active_debuffs", []).append({"type": "weaken", "remaining": 1})
            if "str_mod" in boss:
                boss["str_mod"] = max(0, boss.get("str_mod", 0) - 3)
            if "dex_mod" in boss:
                boss["dex_mod"] = max(0, boss.get("dex_mod", 0) - 3)
            boss["_paradox_exposed"] = True
        elif pf >= 7:
            c_print("  ⚠ Chrysalis's form wavers — paradox tears at its being!")
        elif pf >= 5:
            c_print("  ⚡ The timelines strain against each other...")

    # ── Shard regeneration (unhit shards give +3 stacks) ────
    if not boss.get("stunned"):
        for aspect in ["past", "present", "future"]:
            if aspect not in ctx.get("shards_hit_this_round", set()):
                key = f"{aspect}_stacks"
                ctx[key] = min(30, ctx[key] + 3)
    ctx["shards_hit_this_round"] = set()

    # ── Aspect passives ─────────────────────────────────────
    player = ctx.get("_player_ref")
    if ctx["active_aspect"] == "past":
        _apply_past_passive(ctx, enemies)
    elif ctx["active_aspect"] == "present":
        _apply_present_passive(ctx, boss)
    elif ctx["active_aspect"] == "future" and player:
        _apply_future_passive(ctx, player, enemies)

    # ── HP snapshots for shard damage redirect ──────────────
    for shard_key in SHARD_KEYS.values():
        shard = _get_shard(enemies, shard_key)
        if shard:
            shard["_hp_snapshot"] = shard["hp"]

    # ── Sync entity buff tags for GUI ───────────────────────
    _sync_entity_tags(ctx, enemies)

    return None


def _sync_entity_tags(ctx, enemies):
    """Populate _custom_tags on shards and boss so the GUI renders Aspect stacks,
    Paradox Fracture, and Momentum as entity buff tags (e.g. [🔥 Past 13/30]).
    """
    active = ctx["active_aspect"]
    phase = ctx["phase"]
    boss = _get_boss(enemies)

    # ── Shards: Aspect stack tags ───────────────────────────
    for shard_key in SHARD_KEYS.values():
        shard = _get_shard(enemies, shard_key)
        if not shard:
            continue
        aspect = SHARD_TO_ASPECT[shard_key]
        stacks = ctx[f"{aspect}_stacks"]
        marker = " ◀" if aspect == active else ""
        tag = f"{ASPECT_ICONS[aspect]} {ASPECT_NAMES[aspect]} {stacks}/30{marker}"
        shard["_custom_tags"] = [tag]

    # ── Boss: Paradox Fracture + Momentum ────────────────────
    if boss:
        boss_tags = []
        pf = ctx["paradox_fracture"]
        boss_tags.append(f"💔PF {pf}/10")
        if active == "present":
            mom = get_momentum_stacks(boss)
            cap = MOMENTUM_CAP_P3 if phase >= 3 else MOMENTUM_CAP_P1P2
            boss_tags.append(f"⚔MOM {mom}/{cap}")
        boss["_custom_tags"] = boss_tags


def _apply_past_passive(ctx, enemies):
    """Past passive: check party for burn-heavy members, apply healing-down."""
    player = ctx.get("_player_ref")
    if not player:
        return
    boss = _get_boss(enemies)
    if not boss:
        return

    party = _get_alive_party(player)
    for member in party:
        burn_dmg, burn_rem, _, _ = _count_burn_bleed(member)
        total_burn = burn_dmg + burn_rem
        if total_burn >= 10:
            # Apply healing-down
            existing_hd = next(
                (d for d in member.get("active_debuffs", []) if d.get("type") == "healing_down"),
                None
            )
            if existing_hd:
                existing_hd["remaining"] = 1
            else:
                member.setdefault("active_debuffs", []).append({
                    "type": "healing_down", "remaining": 1, "value": 50
                })
            # Apply Wrath Fragility — take +30% fire damage
            existing_wf = next(
                (d for d in member.get("active_debuffs", []) if d.get("type") == "wrath_fragility"),
                None
            )
            if existing_wf:
                existing_wf["remaining"] = 1
            else:
                member.setdefault("active_debuffs", []).append({
                    "type": "wrath_fragility", "remaining": 1, "value": 30
                })
            c_print(f"  🔥 Past Aspect: {member.get('name', 'Ally')} is seared — healing halved, +30% fire damage taken!")


def _apply_present_passive(ctx, boss):
    """Present passive: gain (2 + party_size) Momentum."""
    party_size = ctx.get("_party_size", 1)
    cap = MOMENTUM_CAP_P3 if ctx["phase"] >= 3 else MOMENTUM_CAP_P1P2
    gain = 2 + party_size
    result = apply_momentum(boss, gain, cap=cap)


def _apply_future_passive(ctx, player, enemies):
    """Future passive: immediate bleed tick on all bleeding party members, heal boss."""
    if not player:
        return
    boss = _get_boss(enemies)
    if not boss:
        return
    total_heal = 0
    for member in _get_alive_party(player):
        for d in member.get("active_debuffs", [])[:]:
            if d["type"] == "bleed" and d.get("remaining", 0) > 0:
                dmg = d.get("damage", 0)
                hp_key = "current_hp" if "current_hp" in member else "hp"
                member[hp_key] = max(0, member[hp_key] - dmg)
                total_heal += dmg
                c_print(f"  🩸 Future Aspect: {member.get('name', 'Ally')} bleeds for {dmg}!")
    if total_heal > 0:
        healed = _heal_boss(boss, total_heal)
        if healed > 0:
            c_print(f"  🩸 Chrysalis drinks deep: +{healed} HP.")


def _enemy_turn_hook(enemy, ctx, player, p_con, defending, **kwargs):
    """Custom turn logic for Chrysalis. Shards do nothing."""
    if enemy.get("key") != BOSS_KEY:
        # Shards do nothing — skip their turn
        return 1, True, None, 1.0, 0  # skip_atk=True

    aspect = ctx["active_aspect"]
    cycle = ctx["turn_in_cycle"]
    phase = ctx["phase"]
    boss = enemy

    # Actions per phase
    if phase == 1:
        num_actions = 1
    else:
        num_actions = 2

    # Get skill for current cycle
    skill_name, skill_fn = _get_skill_for_cycle(aspect, cycle, phase)

    # Advance cycle — Phase 2 uses 5-skill cycle, others use 3
    cycle_mod = 5 if phase == 2 else 3
    ctx["turn_in_cycle"] = (cycle + 1) % cycle_mod

    c_print(f"\n  {boss['name']} uses [{skill_name}] ({ASPECT_ICONS[aspect]} {ASPECT_NAMES[aspect]} Aspect)")

    total_dmg = 0
    for action_i in range(num_actions):
        if player["current_hp"] <= 0:
            return "dead"
        if action_i > 0:
            c_print(f"\n⚡ FAST ACTION! {boss['name']} unleashes Action {action_i+1}/{num_actions}!")
            # Pick next skill in cycle
            cycle_mod2 = 5 if phase == 2 else 3
            skill_name, skill_fn = _get_skill_for_cycle(aspect, ctx["turn_in_cycle"], phase)
            ctx["turn_in_cycle"] = (ctx["turn_in_cycle"] + 1) % cycle_mod2
            c_print(f"  Follow-up: [{skill_name}]")

        # Paradox Fracture: increase damage TAKEN (applied to boss as vulnerability)
        # Actually, PF doesn't affect boss's outgoing damage. It affects damage the boss RECEIVES.
        # Boss self-inflicted damage (from shard redirect) is affected.
        # For boss outgoing damage, we apply the inverse — but actually PF doesn't amp boss damage,
        # it makes the boss take more damage. So we don't modify outgoing.

        dmg = skill_fn(boss, player, p_con, defending, ctx)
        total_dmg += dmg

    if total_dmg > 0:
        c_print(f"\n  Total this turn: {total_dmg} damage")
    else:
        c_print(f"\n  No damage dealt this turn.")

    # Return: actions=0 (already executed), skip_atk=True, no extra logic
    return 0, True, None, 1.0, 0


def _post_round_hook(ctx, enemies):
    """Future bleed lifesteal + Paradox Fracture cleanup."""
    boss = _get_boss(enemies)
    if not boss:
        return None

    # ── Future passive: bleed lifesteal ─────────────────────
    if ctx["active_aspect"] == "future":
        # Player is accessible through ctx
        player = ctx.get("_player_ref")
        if player:
            total_bleed = 0
            for entity in _get_alive_party(player):
                for d in entity.get("active_debuffs", []):
                    if d["type"] == "bleed" and d.get("remaining", 0) > 0:
                        total_bleed += d.get("damage", 0)
            if total_bleed > 0:
                healed = _heal_boss(boss, total_bleed)
                if healed > 0:
                    c_print(f"  🩸 Future Aspect: Chrysalis drinks deep from wounds yet to open... +{healed} HP.")

    # ── Clear Paradox Exposed flag ──────────────────────────
    if boss.get("_paradox_exposed"):
        boss.pop("_paradox_exposed")
        ctx["paradox_fracture"] = 0

    # ── Sync entity buff tags for GUI (round-end, after all actions) ──
    _sync_entity_tags(ctx, enemies)

    return None


def _on_kill_hook(target, elist, ctx):
    """Handle shard 'death' — prevent removal, drain stacks.
    When Chrysalis itself is killed, destroy all shards so the fight ends.
    """
    aspect = SHARD_TO_ASPECT.get(target.get("key"))
    if aspect:
        # Prevent death — reset HP to 1
        target["hp"] = 1

        # Drain 1 stack from the linked Aspect
        key = f"{aspect}_stacks"
        ctx[key] = max(0, ctx[key] - 1)

        # Mark as hit this round
        ctx.setdefault("shards_hit_this_round", set()).add(aspect)

        c_print(f"  {target['name']} shatters and reforms!")
        c_print(f"     Chrysalis loses 1 {ASPECT_NAMES[aspect]} stack. ({ctx[key]}/30)")

        # Heal the attacker (player reference from ctx)
        player = ctx.get("_player_ref")
        if player:
            player["current_hp"] = min(
                player.get("max_hp", player["current_hp"]),
                player["current_hp"] + 5
            )
            c_print("     You recover 5 HP from the temporal resonance.")

        # Sync entity tags so GUI updates the shard's aspect stack tag immediately
        _sync_entity_tags(ctx, elist)

    elif target.get("key") == BOSS_KEY:
        # Chrysalis itself has been slain — destroy all temporal shards
        c_print("\n  💥 The Entangled One collapses — the temporal shards shatter in unison!")
        for e in elist:
            if e.get("key") in SHARD_KEYS.values():
                e["hp"] = 0


def _on_player_hit_hook(target, elist, ctx):
    """Handle player hits against Chrysalis or shards.

    - Past Aspect: retaliatory burn on attacker
    - Paradox Fracture: bonus damage on Chrysalis
    """
    player = ctx.get("_player_ref")
    if not player:
        return

    # Is the target Chrysalis?
    if target.get("key") == BOSS_KEY:
        # Past retaliatory burn
        if ctx["active_aspect"] == "past":
            apply_burn_to_player(player, tier=5, duration=3)
            c_print("  🔥 Past Aspect: Retaliatory burn! You are burned.")


# ═══════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════

def combat_entangled_chrysalis(player, floor=None, enemies=None):
    """Superboss: Chrysalis, the Entangled One.

    Pandemonium floor 20 exclusive.
    Three Temporal Aspects, immortal shards, Paradox Fracture vulnerability.

    Args:
        enemies: Optional pre-created enemy list for GUI mode state sharing.
    """
    boss_key = BOSS_KEY

    if enemies is None:
        boss = enemy_stats(boss_key, player)
        boss["max_hp"] = boss["hp"]
        shard_pyre = enemy_stats(SHARD_PYRE, player)
        shard_pyre["max_hp"] = shard_pyre["hp"]
        shard_pulse = enemy_stats(SHARD_PULSE, player)
        shard_pulse["max_hp"] = shard_pulse["hp"]
        shard_ruin = enemy_stats(SHARD_RUIN, player)
        shard_ruin["max_hp"] = shard_ruin["hp"]
        enemies = [boss, shard_pyre, shard_pulse, shard_ruin]
    else:
        boss = None
        for e in enemies:
            if e.get("key") == boss_key:
                boss = e
                boss["max_hp"] = boss["hp"]
                break
        if boss is None:
            boss = enemy_stats(boss_key, player)
            boss["max_hp"] = boss["hp"]
            enemies.append(boss)
        # Ensure shards exist
        for shard_key in SHARD_KEYS.values():
            if not _get_shard(enemies, shard_key):
                shard = enemy_stats(shard_key, player)
                shard["max_hp"] = shard["hp"]
                enemies.append(shard)

    # Opening narration
    c_print("\n" + "=" * 60)
    c_print("The chamber stretches beyond what geometry should allow. Three hourglasses")
    c_print("hover at its vertices — one dripping amber sand upward, one pulsing with")
    c_print("silver light, one bleeding violet grains into an infinite abyss.")
    c_print("")
    c_print("At the center, suspended by threads of crystallized time, a cocoon pulses.")
    c_print("It thrums with three heartbeats, each at a different tempo.")
    c_print("")
    c_print("The threads snap.")
    c_print("")
    c_print("What emerges is not a creature. It is a moment — stretched across")
    c_print("past, present, and future simultaneously. Wings of fractured glass.")
    c_print("Eyes that have seen every version of this fight. Every outcome.")
    c_print("=" * 60)
    c_input("\nPress Enter to face the Entangled One...")

    # Shard HP snapshots
    for shard_key in SHARD_KEYS.values():
        shard = _get_shard(enemies, shard_key)
        if shard:
            shard["_hp_snapshot"] = shard["hp"]

    # Context state
    context = {
        "past_stacks": 10,
        "present_stacks": 10,
        "future_stacks": 10,
        "active_aspect": "present",  # Present wins ties
        "paradox_fracture": 0,
        "phase": 1,
        "turn_in_cycle": 0,
        "shards_hit_this_round": set(),
        "skip_player_turn": False,
        "_player_ref": player,
        "_party_size": 1 + len(get_active_allies(player)),
    }

    # ═══════════════════════════════════════════════════════════════
    # Wrap boss with Paradox Fracture dict for damage amplification
    # ═══════════════════════════════════════════════════════════════
    # Replace boss in enemies list with wrapped version
    boss_idx = next((i for i, e in enumerate(enemies) if e.get("key") == BOSS_KEY), None)
    if boss_idx is not None:
        enemies[boss_idx] = _ParadoxFractureDict(enemies[boss_idx], context)

    # Initial entity tag sync (before first round)
    _sync_entity_tags(context, enemies)

    # ═══════════════════════════════════════════════════════════════
    # HOOK WRAPPERS (clean closure references)
    # ═══════════════════════════════════════════════════════════════

    def pre_player_hook(ctx, elist):
        # Update party size each round (allies can die/swap)
        ctx["_party_size"] = 1 + len(get_active_allies(player))
        ctx["_player_ref"] = player
        return _pre_player_hook(ctx, elist)

    def enemy_turn_hook(enemy, ctx, pl, p_con, defending, **kwargs):
        return _enemy_turn_hook(enemy, ctx, player, p_con, defending, **kwargs)

    def post_round_hook(ctx, elist):
        # Past passive: retaliatory burn is handled in on_player_hit_hook
        return _post_round_hook(ctx, elist)

    def on_kill_hook(target, elist, ctx):
        _on_kill_hook(target, elist, ctx)

    def on_player_hit_hook(target, elist, ctx):
        _on_player_hit_hook(target, elist, ctx)

    # ═══════════════════════════════════════════════════════════════
    # COMBAT LOOP
    # ═══════════════════════════════════════════════════════════════

    result = superboss_combat_loop(
        player, enemies, floor,
        boss_name="Chrysalis, the Entangled One",
        context=context,
        pre_player_hook=pre_player_hook,
        on_kill_hook=on_kill_hook,
        on_player_hit_hook=on_player_hit_hook,
        enemy_turn_hook=enemy_turn_hook,
        post_round_hook=post_round_hook,
    )

    if result == "victory":
        # Guard: only award loot once per save
        if not player.get("boss_defeated_entangled_chrysalis"):
            # Victory narration
            c_print("\n" + "=" * 60)
            c_print("The three hourglasses crack simultaneously. Sand — amber, silver, violet")
            c_print("spills across the chamber floor and evaporates into mist.")
            c_print("")
            c_print("Chrysalis lowers its head. The wings fold. For a single, perfect moment,")
            c_print("all three heartbeats align.")
            c_print("")
            c_print("'It has always known you would defeat it.'")
            c_print("")
            c_print("The creature dissolves into threads of light. They weave themselves into")
            c_print("a mantle that settles gently across your shoulders.")
            c_print("=" * 60)

            # Loot: Chronoweave Mantle (100%) + Fractured Hourglass (100%)
            from resources.items import build_item
            from inventory_ui import prompt_acquire_item
            mantle = build_item("chronoweave_mantle", "unique")
            hourglass = build_item("fractured_hourglass", "legendary")

            c_print(f"\n  🎁 Loot: {mantle['name']}")
            c_print(f"  🎁 Loot: {hourglass['name']}")

            # Add to inventory via prompt (shows discard dialog if full)
            prompt_acquire_item(player, mantle)
            prompt_acquire_item(player, hourglass)

            # Set defeated flag AFTER awarding loot
            player["boss_defeated_entangled_chrysalis"] = True

    return result