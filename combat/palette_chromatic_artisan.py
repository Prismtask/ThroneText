# combat/palette_chromatic_artisan.py
"""Palette, the Chromatic Artisan — Superboss encounter.

A painter whose canvas is reality. Cycles through 7 color stances; each color
determines attacks, on-hit debuffs, resistances and a boss passive. Attacks
stack Paint on the party that bursts into color-matched debuffs.

Design doc: unrelated for coding/palette_superboss_blueprint.md
"""

import random

from combat.stats import enemy_stats, compute_player_stats
from combat.ally import get_active_allies, compute_ally_stats
from combat.combat_ui import print_combat_hud
from combat.superboss_common import superboss_combat_loop
from combat.combat_io import c_print, c_input
from combat.helpers import format_damage_msg
from combat.elemental import calculate_elemental_damage
from combat.elemental_debuffs import (
    get_elemental_debuff_params,
    DEBUFF_APPLY_MAP,
)

# ═══════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════

BOSS_KEY = "chromatic_artisan"
BOSS_LER = 12          # Palette attacks scale on Learning (the artisan's mind)

# Paint system
PAINT_BURST_THRESHOLD = 5
PAINT_CAP_P1 = 5
PAINT_CAP_P2P3 = 7

# Signature (P3 finisher)
SIGNATURE_HP_GATE = 0.10     # boss HP% at which Signature becomes available
SIGNATURE_CHARGE_TURNS = 2   # boss turns spent painting before it fires
SIGNATURE_INTERRUPT_DMG = 40 # party damage needed during the charge to interrupt
SIGNATURE_COOLDOWN = 2       # boss turns before Signature can be charged again

# Stance pacing
TURNS_PER_COLOR_P1 = 3
TURNS_PER_COLOR_P2P3 = 2

FIXATIVE_TURNS = 3

COLOR_CYCLE = ["crimson", "azure", "gold", "verdant", "umber", "alabaster", "obsidian"]

COLOR_NAMES = {
    "crimson":   "Crimson",
    "azure":     "Azure",
    "gold":      "Gold",
    "verdant":   "Verdant",
    "umber":     "Umber",
    "alabaster": "Alabaster",
    "obsidian":  "Obsidian",
}

COLOR_DATA = {
    "crimson":   {"element": "fire",    "emoji": "🔴", "debuff": "burn",    "resist": "fire",     "weak": "water",   "passive": "+15% damage dealt"},
    "azure":     {"element": "water",   "emoji": "🔵", "debuff": "slow",    "resist": "water",    "weak": "thunder", "passive": "Heal 3% max HP/turn"},
    "gold":      {"element": "thunder", "emoji": "🟡", "debuff": "shock",   "resist": "thunder",  "weak": "earth",   "passive": "+10 initiative"},
    "verdant":   {"element": "wind",    "emoji": "🟢", "debuff": "blind",   "resist": "wind",     "weak": "earth",   "passive": "+15% dodge"},
    "umber":     {"element": "earth",   "emoji": "🟤", "debuff": "weaken",  "resist": "earth",    "weak": "wind",    "passive": "+20% defense"},
    "alabaster": {"element": "light",   "emoji": "⚪", "debuff": "silence", "resist": "light",    "weak": "dark",    "passive": "Clears 1 self-debuff/turn"},
    "obsidian":  {"element": "dark",    "emoji": "⚫", "debuff": "dread",   "resist": "dark",     "weak": "light",   "passive": "8% lifesteal"},
}


class _PaletteBossDict(dict):
    """Intercept HP decreases to apply damage_taken_mult (Umber stance defense).

    Mirrors the wrapper pattern used by Slitcurrent / Rientrante.
    """

    def __setitem__(self, key, value):
        if key == "hp" and "hp" in self and value < self["hp"]:
            mult = self.get("damage_taken_mult", 1.0)
            if mult != 1.0:
                dmg = self["hp"] - value
                dmg = max(0, int(dmg * mult))
                value = self["hp"] - dmg
        super().__setitem__(key, value)


# ═══════════════════════════════════════════════════════════════════
# STANCE HELPERS
# ═══════════════════════════════════════════════════════════════════

def _turns_per_color(ctx):
    return TURNS_PER_COLOR_P1 if ctx["phase"] == 1 else TURNS_PER_COLOR_P2P3


def _active_colors(ctx):
    """Return the list of active colors (primary, optional secondary)."""
    colors = [ctx["current_color"]]
    if ctx.get("secondary_color"):
        colors.append(ctx["secondary_color"])
    return colors


def _apply_stance(boss, ctx):
    """Rebuild resistances, damage profile and passive fields from active colors."""
    colors = _active_colors(ctx)

    res = {"physical": 0.8, "magical": 0.8}
    dmg = {}
    for color in colors:
        data = COLOR_DATA[color]
        res[data["resist"]] = min(res.get(data["resist"], 1.0), 0.6)
        res[data["weak"]] = max(res.get(data["weak"], 1.0), 1.4)
        dmg[data["element"]] = 1.5

    boss["elemental_res"] = res
    boss["elemental_dmg"] = dmg

    # Umber: +20% defense (incoming damage x0.8 via dict wrapper)
    boss["damage_taken_mult"] = 0.8 if "umber" in colors else 1.0

    # Gold: +10 initiative (read by roll_initiative)
    boss["initiative_bonus"] = 10 if "gold" in colors else 0

    # Crimson: +15% damage dealt (applied in the attack math)
    boss["_crimson_bonus"] = "crimson" in colors

    # Verdant: +15% dodge (evasion buff read by get_dodge_chance)
    boss["active_buffs"] = [b for b in boss.get("active_buffs", []) if b.get("source") != "palette_stance"]
    if "verdant" in colors:
        boss.setdefault("active_buffs", []).append({
            "type": "evasion", "source": "palette_stance", "value": 0.15, "remaining": 999,
        })

    boss["_palette_colors"] = colors


def _next_color_in_cycle(current, ctx):
    """Return the next color in the cycle, skipping the secondary in P3."""
    idx = COLOR_CYCLE.index(current)
    nxt = COLOR_CYCLE[(idx + 1) % len(COLOR_CYCLE)]
    if ctx.get("secondary_color") and nxt == ctx["secondary_color"]:
        nxt = COLOR_CYCLE[(idx + 2) % len(COLOR_CYCLE)]
    return nxt


def _shift_color(boss, ctx):
    """Advance Palette's stance and rebuild everything."""
    new_color = _next_color_in_cycle(ctx["current_color"], ctx)
    ctx["current_color"] = new_color
    ctx["turns_in_color"] = _turns_per_color(ctx)
    _apply_stance(boss, ctx)

    data = COLOR_DATA[new_color]
    c_print(f"\n🎨  Palette dips their brush into {COLOR_NAMES[new_color]}!")
    c_print(f"    {data['emoji']} Stance: {data['element'].upper()} — passive: {data['passive']}")
    c_print(f"    Resists {data['resist'].upper()} (0.6) — weak to {data['weak'].upper()} (1.4)")
    if ctx.get("secondary_color"):
        sec = COLOR_DATA[ctx["secondary_color"]]
        c_print(f"    🖌️  Secondary canvas: {sec['emoji']} {COLOR_NAMES[ctx['secondary_color']]} ({sec['element'].upper()})")


def _telegraph_next(ctx):
    """Announce the upcoming color one turn before the shift."""
    nxt = _next_color_in_cycle(ctx["current_color"], ctx)
    data = COLOR_DATA[nxt]
    c_print(f"  👁️  Palette eyes the {COLOR_NAMES[nxt]} pigment...")


# ═══════════════════════════════════════════════════════════════════
# PAINT SYSTEM
# ═══════════════════════════════════════════════════════════════════

def _get_paint(target):
    return next((d for d in target.get("active_debuffs", []) if d.get("type") == "paint"), None)


def _paint_stacks(target):
    d = _get_paint(target)
    return d.get("stacks", 0) if d else 0


def _apply_color_debuff(target, debuff_type, level, empowered=False):
    """Apply a color-matched debuff to a party member (player or ally)."""
    duration, strength = get_elemental_debuff_params(debuff_type, level)
    if empowered:
        duration = max(1, int(duration * 1.5))
        for key in list(strength.keys()):
            if key == "tier":
                strength[key] = min(4, strength[key] + 1)
            elif key in ("damage", "str_penalty"):
                strength[key] = max(1, int(strength[key] * 1.5))

    apply_func = DEBUFF_APPLY_MAP.get(debuff_type)
    if apply_func is None:
        return None
    apply_func(target, duration, strength)
    return None


def _add_paint(target, amount, ctx, boss, is_player, name_hint=None):
    """Add paint stacks to a party member. Returns a burst message or None.

    Paint bursts at PAINT_BURST_THRESHOLD+ stacks: 5 = Pigment Burst,
    6-7 = Pigment Explosion (+50% debuff potency).
    """
    if amount <= 0 or target.get("current_hp", 0) <= 0:
        return None

    # Fixative freezes all paint — no growth, no burst
    if ctx.get("fixative_turns", 0) > 0:
        return None

    # Blank Canvas Shawl Afterimage deflects incoming paint
    from combat.weapon.blank_canvas_shawl import try_consume_afterimage
    if try_consume_afterimage(target):
        c_print(f"  👻 Afterimage! {target.get('name', 'you')} brushes the paint away!")
        return None

    name = name_hint or target.get("name", "you")
    debuff = _get_paint(target)
    current = debuff.get("stacks", 0) if debuff else 0
    new_total = current + amount
    cap = PAINT_CAP_P1 if ctx["phase"] == 1 else PAINT_CAP_P2P3

    if new_total < PAINT_BURST_THRESHOLD:
        if debuff is None:
            target.setdefault("active_debuffs", []).append({
                "type": "paint", "stacks": new_total, "remaining": 999,
            })
        else:
            debuff["stacks"] = new_total
        c_print(f"  🎨 +{amount} paint on {name} ({new_total}/{cap})")
        return None

    # ── Burst ──
    empowered = new_total >= 6
    color = ctx["current_color"]
    data = COLOR_DATA[color]

    target["active_debuffs"] = [
        d for d in target.get("active_debuffs", []) if d.get("type") != "paint"
    ]

    if is_player:
        ctx["player_survived_burst"] = True

    _apply_color_debuff(target, data["debuff"], boss.get("level", 35), empowered)

    kind = "💥 PIGMENT EXPLOSION" if empowered else "🖌️ PIGMENT BURST"
    label = f"{COLOR_NAMES[color]} paint"
    return f"  {kind}! {label} ignites on {name} — {data['debuff'].upper()}{' (+50%)' if empowered else ''}!"


# ═══════════════════════════════════════════════════════════════════
# ATTACKS
# ═══════════════════════════════════════════════════════════════════

def _alive_party(player):
    party = [player] + [a for a in get_active_allies(player) if a.get("current_hp", 0) > 0]
    return party


def _roll_damage(boss, target, mult, element, defending, ignore_con_pct=0.0, t_con=None):
    """Roll, defend, and element-scale a single Palette hit."""
    base = random.randint(4, 10) + BOSS_LER
    eff_con = int(t_con * (1.0 - ignore_con_pct))
    dmg = max(0, int(base * mult) - eff_con)
    if defending:
        dmg = int(dmg * 0.5)
    if boss.get("_crimson_bonus"):
        dmg = int(dmg * 1.15)
    return calculate_elemental_damage(dmg, boss, target, element)


def _hit_target(ctx, boss, target, mult, element, defending, ignore_con_pct=0.0, skill_name=None):
    """Deal one hit to one target. Returns damage dealt."""
    if target.get("current_hp", 0) <= 0:
        return 0
    t_con = target.get("con_mod", 5)
    if target.get("is_ally"):
        _, t_con, _, _, _, _ = compute_ally_stats(target)
    else:
        t_con = compute_player_stats(target)[1]

    dmg = _roll_damage(boss, target, mult, element, defending, ignore_con_pct, t_con)
    if dmg > 0:
        target["current_hp"] -= dmg
        ctx["turn_damage"] += dmg
    c_print(format_damage_msg(boss["name"], target["name"], dmg, element=element, skill_name=skill_name))
    return dmg


def _take_study_bonus(ctx):
    """Consume the Study bonus (+2 paint on the next paint-granting attack)."""
    bonus = ctx.get("study_bonus", 0) or 0
    ctx["study_bonus"] = 0
    return bonus


def _attack_brushstroke(ctx, boss, target, defending):
    element = COLOR_DATA[ctx["current_color"]]["element"]
    dmg = _hit_target(ctx, boss, target, 1.0, element, defending, skill_name="Brushstroke")
    if dmg > 0:
        burst_msg = _add_paint(target, 1 + _take_study_bonus(ctx), ctx, boss, target is boss.get("_player_ref"))
        if burst_msg:
            c_print(burst_msg)


def _attack_wash(ctx, boss, party):
    element = COLOR_DATA[ctx["current_color"]]["element"]
    for member in party:
        _hit_target(ctx, boss, member, 0.5, element, False, skill_name="Wash")
    ctx["shift_early"] = True
    c_print("  💧 The wash bleeds — Palette will shift color early!")


def _attack_study(ctx, boss):
    ctx["study_bonus"] = 2
    c_print(f"  👁️  {boss['name']} studies the subject — the next stroke paints +2!")


def _attack_impasto(ctx, boss, party):
    element = COLOR_DATA[ctx["current_color"]]["element"]
    for member in party:
        dmg = _hit_target(ctx, boss, member, 0.8, element, False, skill_name="Impasto")
        if dmg > 0:
            burst_msg = _add_paint(member, 2 + _take_study_bonus(ctx), ctx, boss, member is boss.get("_player_ref"))
            if burst_msg:
                c_print(burst_msg)


def _attack_glaze(ctx, boss, target, defending):
    element = COLOR_DATA[ctx["current_color"]]["element"]
    dmg = _hit_target(ctx, boss, target, 0.6, element, defending, skill_name="Glaze")
    if dmg > 0:
        next_color = _next_color_in_cycle(ctx["current_color"], ctx)
        data = COLOR_DATA[next_color]
        debuff_type = data["debuff"]
        duration, strength = get_elemental_debuff_params(debuff_type, boss.get("level", 35))
        duration = max(1, int(duration / 2))
        apply_func = DEBUFF_APPLY_MAP.get(debuff_type)
        if apply_func:
            apply_func(target, duration, strength)
            c_print(f"  🖌️ Glaze seeps in — {target['name']} is touched by {COLOR_NAMES[next_color]}'s {debuff_type.upper()} (half duration)!")


def _attack_drybrush(ctx, boss, target, defending):
    element = COLOR_DATA[ctx["current_color"]]["element"]
    dmg = _hit_target(ctx, boss, target, 1.3, element, defending, ignore_con_pct=0.30, skill_name="Drybrush")
    if dmg > 0:
        burst_msg = _add_paint(target, 1 + _take_study_bonus(ctx), ctx, boss, target is boss.get("_player_ref"))
        if burst_msg:
            c_print(burst_msg)


def _attack_chiaroscuro(ctx, boss, target):
    c_print("  🌗 Chiaroscuro — light and shadow strike as one!")
    total = 0
    for element in ("light", "dark"):
        # Unblockable: ignore con and defending entirely
        base = random.randint(4, 10) + BOSS_LER
        dmg = int(base * 0.6)
        if boss.get("_crimson_bonus"):
            dmg = int(dmg * 1.15)
        dmg = calculate_elemental_damage(dmg, boss, target, element)
        total += max(0, dmg)
        if dmg > 0:
            target["current_hp"] -= dmg
            ctx["turn_damage"] += dmg
        c_print(format_damage_msg(boss["name"], target["name"], max(0, dmg), element=element, skill_name="Chiaroscuro"))
    if total > 0:
        burst_msg = _add_paint(target, 3 + _take_study_bonus(ctx), ctx, boss, target is boss.get("_player_ref"))
        if burst_msg:
            c_print(burst_msg)


def _attack_spectrum(ctx, boss, party):
    elements = ["fire", "water", "thunder", "wind", "earth", "light", "dark"]
    c_print("  🌈 Spectrum — the canvas erupts in four colors!")
    for member in party:
        for _ in range(4):
            if member.get("current_hp", 0) <= 0:
                break
            element = random.choice(elements)
            dmg = _hit_target(ctx, boss, member, 0.4, element, False, skill_name="Spectrum")
            if dmg > 0:
                burst_msg = _add_paint(member, 1 + _take_study_bonus(ctx), ctx, boss, member is boss.get("_player_ref"))
                if burst_msg:
                    c_print(burst_msg)


def _attack_fixative(ctx, boss, party):
    ctx["fixative_turns"] = FIXATIVE_TURNS
    locked_any = False
    for member in party:
        d = _get_paint(member)
        if d:
            d["fixed"] = True
            locked_any = True
    c_print("  🫙 Fixative mist settles — all paint is locked in place!")
    c_print(f"    (Paint cannot grow, burst, or be cleansed for {FIXATIVE_TURNS} turns.)")
    if not locked_any:
        c_print("    ...but no paint is on the canvas. The fixative drifts away.")


def _start_signature(ctx, boss):
    ctx["signature_charging"] = SIGNATURE_CHARGE_TURNS
    ctx["signature_dmg"] = 0
    c_print("\n" + "=" * 50)
    c_print("  🖋️  Palette steps back. The brush stills.")
    c_print("      In the corner of the canvas, a name begins to form —")
    c_print("      YOUR name.")
    c_print("      Signature is being painted! Deal " + str(SIGNATURE_INTERRUPT_DMG) +
            "+ damage to interrupt it!")
    c_print("=" * 50)


# ═══════════════════════════════════════════════════════════════════
# AI
# ═══════════════════════════════════════════════════════════════════

def _choose_action(ctx, boss, player, party):
    """Weighted random action selection — never fully scripted."""
    phase = ctx["phase"]

    # Signature gate: P3 and boss nearly finished
    if (phase == 3 and ctx.get("signature_charging") is None
            and ctx.get("signature_cooldown", 0) <= 0
            and boss["hp"] / boss.get("max_hp", 1) <= SIGNATURE_HP_GATE):
        return "signature"

    player_hp_pct = player["current_hp"] / max(1, player.get("max_hp", 1))
    player_paint = _paint_stacks(player)
    player_weak = player.get("elemental_res", {}).get(COLOR_DATA[ctx["current_color"]]["element"], 1.0) < 1.0
    allies_alive = len([m for m in party if m is not player])

    pool = []

    def w(key, weight):
        pool.extend([key] * max(1, int(weight)))

    if phase == 1:
        w("brushstroke", 20)
        w("wash", 12)
        w("study", 6)
        if player_hp_pct < 0.25:
            w("brushstroke", 18)
        if player_paint >= 4:
            w("brushstroke", 25)
        if player_weak:
            w("wash", 20)
        if allies_alive:
            w("wash", 12)

    elif phase == 2:
        w("brushstroke", 16)
        w("wash", 10)
        w("study", 5)
        w("impasto", 16)
        w("glaze", 12)
        w("drybrush", 15)
        if player_hp_pct < 0.25:
            w("drybrush", 15)
        if player_paint >= 4:
            w("impasto", 25)
        if player_weak:
            w("impasto", 18)
        if allies_alive:
            w("impasto", 15)

    else:  # phase 3
        w("brushstroke", 12)
        w("wash", 8)
        w("impasto", 14)
        w("glaze", 10)
        w("drybrush", 12)
        w("chiaroscuro", 18)
        w("spectrum", 18)
        if player_hp_pct < 0.25:
            w("chiaroscuro", 20)
        if player_paint >= 4:
            w("spectrum", 22)
        if player_weak:
            w("spectrum", 15)
        if allies_alive:
            w("spectrum", 15)
        # Fixative: only when paint is on the canvas and off cooldown
        any_paint = any(_paint_stacks(m) > 0 for m in party)
        if any_paint and ctx.get("fixative_cooldown", 0) <= 0:
            w("fixative", 6)

    return random.choice(pool) if pool else "brushstroke"


def _execute_action(ctx, boss, player, party, action, defending):
    if action == "brushstroke":
        target = random.choice(party)
        _attack_brushstroke(ctx, boss, target, target is player and defending)
    elif action == "wash":
        _attack_wash(ctx, boss, party)
    elif action == "study":
        _attack_study(ctx, boss)
    elif action == "impasto":
        _attack_impasto(ctx, boss, party)
    elif action == "glaze":
        target = random.choice(party)
        _attack_glaze(ctx, boss, target, target is player and defending)
    elif action == "drybrush":
        target = random.choice(party)
        _attack_drybrush(ctx, boss, target, target is player and defending)
    elif action == "chiaroscuro":
        target = random.choice(party)
        _attack_chiaroscuro(ctx, boss, target)
    elif action == "spectrum":
        _attack_spectrum(ctx, boss, party)
    elif action == "fixative":
        _attack_fixative(ctx, boss, party)
    elif action == "signature":
        _start_signature(ctx, boss)


def _boss_passive_tick(ctx, boss):
    """End-of-turn stance passives (heal, lifesteal, self-cleanse)."""
    colors = boss.get("_palette_colors", [])

    # Azure: heal 3% max HP
    if "azure" in colors:
        heal = int(boss.get("max_hp", 900) * 0.03)
        if heal > 0 and boss["hp"] < boss.get("max_hp", boss["hp"]):
            boss["hp"] = min(boss["hp"] + heal, boss.get("max_hp", boss["hp"]))
            c_print(f"  🌊 The Azure glaze runs — Palette recovers {heal} HP!")

    # Obsidian: 8% lifesteal on this turn's damage
    if "obsidian" in colors and ctx.get("turn_damage", 0) > 0:
        heal = int(ctx["turn_damage"] * 0.08)
        if heal > 0:
            boss["hp"] = min(boss["hp"] + heal, boss.get("max_hp", boss["hp"]))
            c_print(f"  ⚫ Obsidian drinks the pigments — Palette recovers {heal} HP!")

    # Alabaster: clear 1 self-debuff
    if "alabaster" in colors and boss.get("active_debuffs"):
        removed = boss["active_debuffs"].pop(0)
        c_print(f"  ⚪ The Alabaster self-cleans — {removed.get('type', 'a debuff').upper()} is wiped away!")


# ═══════════════════════════════════════════════════════════════════
# PHASE TRANSITIONS
# ═══════════════════════════════════════════════════════════════════

def _wipe_entity_debuffs(entity):
    entity["active_debuffs"] = []
    for flag in ("stunned", "slowed", "blinded", "silenced", "dreaded", "frozen", "confused", "cursed", "weakened", "void_touched"):
        if flag in entity:
            entity[flag] = False


def _blank_canvas_transition(ctx, boss, player):
    """Phase 1 → 2: wipe every stain — party and boss — and heal 5%."""
    ctx["phase"] = 2
    ctx["phase2_done"] = True
    ctx["turns_in_color"] = _turns_per_color(ctx)
    ctx["study_bonus"] = 0
    ctx["shift_early"] = False

    for member in [player] + [a for a in player.get("allies", []) if a.get("current_hp", 0) > 0]:
        _wipe_entity_debuffs(member)
    _wipe_entity_debuffs(boss)

    heal = int(boss.get("max_hp", 900) * 0.05)
    boss["hp"] = min(boss["hp"] + heal, boss.get("max_hp", boss["hp"]))

    c_print("\n" + "-" * 50)
    c_print("  Palette sweeps the canvas clean. Begin again.")
    c_print("  All Paint, debuffs, and afflictions — yours and theirs — are gone.")
    c_print(f"  The pristine surface restores Palette for {heal} HP.")
    c_print("-" * 50)
    c_input("\nPress Enter...")


def _final_canvas_transition(ctx, boss, player):
    """Phase 2 → 3: Dual Palette — a primary and a secondary color."""
    ctx["phase"] = 3
    ctx["phase3_done"] = True
    ctx["secondary_color"] = _next_color_in_cycle(ctx["current_color"], ctx)
    ctx["turns_in_color"] = _turns_per_color(ctx)
    _apply_stance(boss, ctx)

    sec = COLOR_DATA[ctx["secondary_color"]]
    c_print("\n" + "-" * 50)
    c_print("  Palette smiles — the first true smile of the evening.")
    c_print('  "Now," they whisper, "the masterpiece."')
    c_print(f"  DUAL PALETTE: {sec['emoji']} {COLOR_NAMES[ctx['secondary_color']]} joins the canvas!")
    c_print("  Both colors' passives, resistances, and weaknesses are active.")
    c_print("-" * 50)
    c_input("\nPress Enter...")


def _apply_signature_ko(pl, ctx):
    """Fire the Signature at the player. Routes the instant KO through
    death-prevention effects (Chronoweave Mantle, wedding fatal survival).

    Returns True if the player survives — the "You held the canvas" mark.
    """
    from combat.weapon.chronoweave import check_chronoweave_fatal_survival
    from combat.weapon.wedding_specials import apply_wedding_fatal_blow_survival
    lethal = max(1, pl.get("current_hp", 1))
    lethal, _survived = check_chronoweave_fatal_survival(pl, lethal)
    lethal = apply_wedding_fatal_blow_survival(pl, lethal)
    pl["current_hp"] = max(0, pl["current_hp"] - lethal)
    return pl["current_hp"] > 0


# ═══════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════

def combat_palette(player, floor=None, enemies=None):
    """Superboss: Palette, the Chromatic Artisan."""
    boss_key = BOSS_KEY

    if enemies is None:
        raw_boss = enemy_stats(boss_key, player)
        boss = _PaletteBossDict(raw_boss)
        boss["max_hp"] = boss["hp"]
        enemies = [boss]
    else:
        boss = None
        for i, e in enumerate(enemies):
            if e.get("key") == boss_key:
                wrapped = _PaletteBossDict(e)
                wrapped["max_hp"] = wrapped["hp"]
                enemies[i] = wrapped
                boss = wrapped
                break
        if boss is None:
            raw_boss = enemy_stats(boss_key, player)
            boss = _PaletteBossDict(raw_boss)
            boss["max_hp"] = boss["hp"]
            enemies.append(boss)

    # Paint is the ONLY debuff channel for this fight — suppress the generic proc
    boss["_suppress_elemental_debuff"] = True
    boss["_player_ref"] = player

    # Opening narration
    c_print("\n" + "=" * 60)
    c_print("The walls here are not walls. They are canvas — stretched over nothing,")
    c_print("stapled to the air itself. Half-finished landscapes bleed into each other:")
    c_print("a burning forest drowning in a frozen sea, a lightning-struck desert.")
    c_print("")
    c_print("At the easel stands a figure in a coat of seven stains. Their brush drips")
    c_print("with a color you cannot name, because it is every color at once.")
    c_print("")
    c_print("They turn. Their eyes are blank, wet canvases.")
    c_print("")
    c_print('"Be still," they say, "or do not. A smear is still a mark."')
    c_print("=" * 60)
    c_print(f"\n  Palette, the Chromatic Artisan — HP: {boss['hp']}")
    c_input("\nPress Enter to face the Chromatic Artisan...")

    # Context state
    context = {
        "phase": 1,
        "phase2_done": False,
        "phase3_done": False,
        "current_color": COLOR_CYCLE[0],
        "secondary_color": None,
        "turns_in_color": TURNS_PER_COLOR_P1,
        "shift_early": False,
        "study_bonus": 0,
        "turn_damage": 0,
        "fixative_turns": 0,
        "fixative_cooldown": 0,
        "signature_charging": None,
        "signature_dmg": 0,
        "signature_cooldown": 0,
        "player_survived_burst": False,
        "player_held_the_canvas": False,
    }

    _apply_stance(boss, context)

    # ═══════════════════════════════════════════════════════════════
    # HOOKS
    # ═══════════════════════════════════════════════════════════════

    def pre_player_hook(ctx, elist):
        b = next((e for e in elist if e.get("key") == boss_key), None)
        if not b:
            return

        hp_pct = b["hp"] / b.get("max_hp", 1)

        # Phase 1 → 2: Blank Canvas
        if ctx["phase"] == 1 and hp_pct <= 0.65 and not ctx["phase2_done"]:
            _blank_canvas_transition(ctx, b, player)

        # Phase 2 → 3: Final Canvas (Dual Palette)
        if ctx["phase"] == 2 and hp_pct <= 0.30 and not ctx["phase3_done"]:
            _final_canvas_transition(ctx, b, player)

    def party_damage_hook(dmg, ctx):
        """Accumulate party damage against the boss (Signature interrupt check)."""
        if ctx.get("signature_charging") is not None:
            ctx["signature_dmg"] = ctx.get("signature_dmg", 0) + dmg
            c_print(f"  🖋️  Signature pressure: {ctx['signature_dmg']}/{SIGNATURE_INTERRUPT_DMG}")

    def enemy_turn_hook(enemy, ctx, pl, p_con, defending, **kwargs):
        if enemy.get("key") != boss_key:
            return 1, False, None, 1.0, 0

        boss_ref = enemy

        # Stun
        if boss_ref.get("stunned"):
            c_print(f"The {boss_ref['name']} is stunned and cannot act!")
            boss_ref["stunned"] = False
            return 0, True, None, 1.0, 0

        # ── Signature charge flow ──
        if ctx.get("signature_charging") is not None:
            ctx["signature_charging"] -= 1
            if ctx["signature_charging"] > 0:
                c_print(f"  🖋️  Palette paints... the name nears completion! ({ctx['signature_charging']} turn(s) left)")
                return 0, True, None, 1.0, 0

            # Fires now
            if ctx.get("signature_dmg", 0) >= SIGNATURE_INTERRUPT_DMG:
                c_print("\n  💥 The canvas tears! Your blows scatter the pigment —")
                c_print("     the Signature is RUINED! Palette staggers back.")
                ctx["signature_charging"] = None
                ctx["signature_cooldown"] = SIGNATURE_COOLDOWN
                return 0, True, None, 1.0, 0

            c_print("\n" + "=" * 50)
            c_print(f"  🖋️  The name is finished. {pl['name']}.")
            c_print("      Palette flicks the brush once — and the canvas decides.")
            c_print("      SIGNATURE — instant defeat. It cannot be defended.")
            c_print("=" * 50)

            # Route the instant KO through death-prevention effects.
            # Surviving is the rarest mark — "You held the canvas."
            survived = _apply_signature_ko(pl, ctx)

            if survived:
                ctx["player_held_the_canvas"] = True
                c_print("\n  ✨ The canvas howls — and you are STILL STANDING.")
                c_print("      Against every stroke, every law of paint and line,")
                c_print("      you held the canvas. Palette stares, brush trembling.")
                ctx["signature_charging"] = None
                ctx["signature_cooldown"] = SIGNATURE_COOLDOWN
                return 0, True, None, 1.0, 0

            c_print(f"  {pl['name']} has been slain.")
            return "dead"

        # ── Color shift / telegraph ──
        turns_per = _turns_per_color(ctx)
        if ctx.get("shift_early") or ctx["turns_in_color"] <= 0:
            ctx["shift_early"] = False
            _shift_color(boss_ref, ctx)
        else:
            ctx["turns_in_color"] -= 1
            if ctx["turns_in_color"] == 1:
                _telegraph_next(ctx)

        # Cooldowns
        if ctx.get("signature_cooldown", 0) > 0:
            ctx["signature_cooldown"] -= 1
        if ctx.get("fixative_cooldown", 0) > 0:
            ctx["fixative_cooldown"] -= 1
        if ctx.get("fixative_turns", 0) > 0:
            ctx["fixative_turns"] -= 1
            if ctx["fixative_turns"] <= 0:
                for member in _alive_party(pl):
                    d = _get_paint(member)
                    if d:
                        d.pop("fixed", None)
                c_print("  🫙 The fixative thins — paint flows freely again!")

        party = _alive_party(pl)
        actions = 2 if ctx["phase"] >= 2 else 1

        ctx["turn_damage"] = 0

        for action_num in range(actions):
            if pl["current_hp"] <= 0:
                break
            if actions > 1:
                c_print(f"\n⚡ FAST ACTION! {boss_ref['name']} — Action {action_num + 1}/{actions}!")

            action = _choose_action(ctx, boss_ref, pl, party)
            _execute_action(ctx, boss_ref, pl, party, action, defending)

            # Signature replaces all remaining actions this turn
            if ctx.get("signature_charging") is not None:
                break

        _boss_passive_tick(ctx, boss_ref)

        if pl["current_hp"] <= 0:
            c_print(f"{pl['name']} has been slain.")
            return "dead"

        return 0, True, None, 1.0, 0

    def post_round_hook(ctx, elist):
        b = next((e for e in elist if e.get("key") == boss_key), None)
        if not b:
            return

        # Tick the boss's own debuffs (burn/bleed from the party keep hurting)
        from combat.status_effects import tick_enemy_debuffs
        msgs, died = tick_enemy_debuffs(b)
        for m in msgs:
            c_print(m)

    def custom_hud_hook(ctx, elist):
        b = next((e for e in elist if e.get("key") == boss_key), None)
        if b:
            primary = COLOR_DATA[ctx["current_color"]]
            stance_line = (f"  Phase {ctx['phase']} | {primary['emoji']} {COLOR_NAMES[ctx['current_color']]}"
                           f" [{primary['element'].upper()}] — {primary['passive']}")
            if ctx.get("secondary_color"):
                sec = COLOR_DATA[ctx["secondary_color"]]
                stance_line += f" + {sec['emoji']} {COLOR_NAMES[ctx['secondary_color']]}"
            if ctx.get("signature_charging") is not None:
                stance_line += f" | 🖋️ Signature {ctx['signature_dmg']}/{SIGNATURE_INTERRUPT_DMG}"
            c_print(stance_line)

            # Party paint status
            for member in [player] + get_active_allies(player):
                stacks = _paint_stacks(member)
                if stacks > 0:
                    fixed = " [FIXED]" if _get_paint(member).get("fixed") else ""
                    c_print(f"  🎨 {member['name']}: {stacks} paint stacks{fixed}")

        print_combat_hud(player, elist, header="Superboss: Palette, the Chromatic Artisan")

    # ═══════════════════════════════════════════════════════════════
    # RUN COMBAT
    # ═══════════════════════════════════════════════════════════════

    result = superboss_combat_loop(
        player, enemies, floor, "Palette, the Chromatic Artisan", context,
        pre_player_hook=pre_player_hook,
        custom_hud_hook=custom_hud_hook,
        enemy_turn_hook=enemy_turn_hook,
        post_round_hook=post_round_hook,
        party_damage_hook=party_damage_hook,
    )

    # ═══════════════════════════════════════════════════════════════
    # POST-COMBAT (victory)
    # ═══════════════════════════════════════════════════════════════

    if result == "victory":
        if not player.get("boss_defeated_palette"):
            c_print("\n" + "=" * 60)
            c_print("Palette's brush falls. It rolls once, leaving a single perfect")
            c_print("line of white across the floor.")
            c_print("")
            c_print("The living canvas shudders — and goes still. The landscapes")
            c_print("stop bleeding into one another. For the first time, the atelier")
            c_print("is simply... a room.")
            c_print("")
            c_print("Palette sinks to their knees, staring at their hands.")
            c_print('"...you finished it," they whisper. "The painting is done."')
            c_print("=" * 60)

            # Grant loot
            from resources.items import build_item
            from inventory_ui import prompt_acquire_item

            brush = build_item("palette_brush", rarity="unique")
            c_print(f"\n  🎁 Received: {brush['name']}!")
            prompt_acquire_item(player, brush)

            shawl = build_item("blank_canvas_shawl", rarity="unique")
            c_print(f"  🎁 Received: {shawl['name']}!")
            prompt_acquire_item(player, shawl)

            player["boss_defeated_palette"] = True

        # ── Recruitment — "The Artist's Choice" ──
        held_canvas = context.get("player_held_the_canvas")
        let_it_dry = context.get("player_survived_burst")
        if (held_canvas or let_it_dry) and not player.get("palette_recruited") and not player.get("palette_recruit_declined"):
            c_print("\n" + "-" * 50)
            if held_canvas:
                c_print("As you turn to leave, Palette speaks — and this time the")
                c_print("hollow Artisan voice cracks into something small and shaken.")
                c_print("")
                c_print('"The Signature... it was FINISHED. Your name was on the')
                c_print('canvas. Every painter knows what that means." They fidget,')
                c_print('staring at you like you are a theorem that refuses to solve.')
                c_print('')
                c_print('"But you... you HELD it. The canvas folded for everyone')
                c_print('else. For you it stayed still. Nobody holds the canvas."')
                c_print('')
                c_print('"If... if there is room on your canvas — I mean, in your')
                c_print('company — I would very much like to... to paint alongside')
                c_print('you. Not as the Artisan. Just as... Palette."')
            else:
                c_print("As you turn to leave, Palette speaks — not in the hollow")
                c_print("voice of the fight, but small and uncertain.")
                c_print("")
                c_print('"You... you let it dry," they say, gesturing at the paint')
                c_print('still staining your skin. "Nobody lets it dry. They wipe it')
                c_print('off, or they run. You let it DRY."')
                c_print("")
                c_print("They fidget with the bristles of their brush, then meet your")
                c_print("eyes for a single heartbeat before looking away, flustered.")
                c_print("")
                c_print('"If... if there is room on your canvas — I mean, in your')
                c_print('company — I would very much like to... to paint alongside')
                c_print('you. Not as the Artisan. Just as... Palette."')
            c_print("-" * 50)

            choice = c_input("\nLet Palette join your party? (y/n): ").strip().lower()
            if choice == "y":
                from combat.ally import (
                    create_heroine_ally,
                    promote_heroine_to_permanent,
                    set_heroine_state,
                    get_heroine_in_party,
                )
                existing = get_heroine_in_party(player, "palette")
                if existing:
                    c_print(f"  {existing['name']} is already in your party!")
                else:
                    ally = create_heroine_ally(player, "palette", floor)
                    if ally is None:
                        c_print("  (Palette's template could not be found — she will return when the atelier is ready.)")
                    else:
                        promote_heroine_to_permanent(player, ally, ally.get("level"))
                        set_heroine_state(player, "palette", "permanent")
                        player["allies"].append(ally)
                        player["palette_recruited"] = True
                        c_print(f"\n  🎨 {ally['name']} joins your party! She clutches her brush")
                        c_print("    like a lifeline, and smiles — shy, and very real.")
            else:
                c_print("\n  Palette nods, a little crestfallen, and begins packing")
                c_print("  their brushes into a satchel that holds far more than it should.")
                player["palette_recruit_declined"] = True

    return result
