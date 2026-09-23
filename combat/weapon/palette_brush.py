# combat/weapon/palette_brush.py
"""Palette's Brush — unique weapon logic (actor-based, player AND allies).

The game's second "no-skills" weapon. Equipping it replaces all class skills
with the brush's own kit:
  - Brush Stance: free once-per-turn color commitment (attacks deal that
    element at 1.35x; no stance = generic magical 1.3x from the weapon).
  - Strokes: each basic attack paints +1 stroke on the target; the 3rd stroke
    completes the painting -> Pigment Explosion (+50% damage) and grants a
    pigment of the finishing stroke's color.
  - Wet Palette: pigments are never consumed. Up to 3 permanent battle auras,
    rankable to 3 by painting the same color again (FIFO when full).
  - Exhibits: one-use finishers unlocked by lifetime strokes (6/12/18).

State keys on the actor dict (cleared at combat end):
    brush_stance            : str element or None
    brush_stance_changed    : bool (once per turn)
    brush_strokes           : {id(enemy): int}
    brush_palette           : [{"color": str, "rank": int}] max 3
    brush_total_strokes     : int
    brush_exhibits_used     : set of {"impasto", "chiaroscuro", "signature"}
"""

import random

from combat.combat_io import c_print, c_input
from combat.helpers import format_damage_msg
from combat.elemental import calculate_elemental_damage

# ═══════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════

BRUSH_ITEM_ID = "palette_brush"

STANCE_MULT = 1.35
STROKES_PER_PIGMENT = 3
PIGMENT_EXPLOSION_PCT = 0.50
PALETTE_SLOTS = 3
MAX_AURA_RANK = 3
EXHIBIT_STROKES = {"impasto": 6, "chiaroscuro": 12, "signature": 18}

# Masterclass (Palette's Palette wedding accessory): Exhibits unlock earlier
MASTERCLASS_THRESHOLDS = {"impasto": 5, "chiaroscuro": 10, "signature": 15}
MASTERCLASS_DMG_BONUS = 0.15

COLOR_ORDER = ["crimson", "azure", "gold", "verdant", "umber", "alabaster", "obsidian"]

COLOR_NAMES = {
    "crimson": "Crimson", "azure": "Azure", "gold": "Gold", "verdant": "Verdant",
    "umber": "Umber", "alabaster": "Alabaster", "obsidian": "Obsidian",
}

COLOR_TO_ELEMENT = {
    "crimson": "fire", "azure": "water", "gold": "thunder", "verdant": "wind",
    "umber": "earth", "alabaster": "light", "obsidian": "dark",
}
ELEMENT_TO_COLOR = {v: k for k, v in COLOR_TO_ELEMENT.items()}

# Color -> debuff applied by Impasto Exhibit / paint bursts (boss table)
COLOR_DEBUFF = {
    "crimson": "burn", "azure": "slow", "gold": "shock", "verdant": "blind",
    "umber": "weaken", "alabaster": "silence", "obsidian": "dread",
}

# Wet Palette aura table (rank 1 / 2 / 3)
AURA_DATA = {
    "crimson":   {"label": "On-attack Burn",      "ranks": [{"tier": 2}, {"tier": 3}, {"tier": 4}]},
    "azure":     {"label": "On-attack Slow",      "ranks": [{"dur": 2}, {"dur": 3}, {"dur": 3}]},
    "gold":      {"label": "On-attack Shock",     "ranks": [{"dmg": 3}, {"dmg": 4}, {"dmg": 6}]},
    "verdant":   {"label": "Initiative",          "ranks": [{"init": 3}, {"init": 5}, {"init": 8}]},
    "umber":     {"label": "Damage reduction",    "ranks": [{"dr": 0.08}, {"dr": 0.12}, {"dr": 0.16}]},
    "alabaster": {"label": "On-attack Silence",   "ranks": [{"dur": 2}, {"dur": 3}, {"dur": 3}]},
    "obsidian":  {"label": "Lifesteal",           "ranks": [{"ls": 0.08}, {"ls": 0.12}, {"ls": 0.16}]},
}

# On-attack proc chances per rank for the four proc auras
AURA_PROC_CHANCES = {
    "crimson":   [0.25, 0.40, 0.55],
    "azure":     [0.25, 0.40, 0.55],
    "gold":      [0.20, 0.35, 0.50],
    "alabaster": [0.20, 0.35, 0.50],
}


# ═══════════════════════════════════════════════════════════════════
# STATE MANAGEMENT
# ═══════════════════════════════════════════════════════════════════

def _actor_has_palette_brush(actor):
    """Check if an actor has Palette's Brush equipped in the weapon slot."""
    equipped = actor.get("equipped", {})
    if isinstance(equipped, dict):
        weapon = equipped.get("weapon")
        if weapon and weapon.get("id") == BRUSH_ITEM_ID:
            return True
    return False


def init_brush_state(actor):
    """Called at combat start to set up brush state on an actor."""
    actor["brush_stance"] = None
    actor["brush_stance_changed"] = False
    actor["brush_strokes"] = {}
    actor["brush_palette"] = []
    actor["brush_total_strokes"] = 0
    actor["brush_exhibits_used"] = set()


def clear_brush_state(actor):
    """Called at combat end to clean up brush state."""
    actor.pop("brush_stance", None)
    actor.pop("brush_stance_changed", None)
    actor.pop("brush_strokes", None)
    actor.pop("brush_palette", None)
    actor.pop("brush_total_strokes", None)
    actor.pop("brush_exhibits_used", None)


def begin_actor_turn(actor):
    """Reset the once-per-turn stance flag at the start of the actor's turn."""
    if _actor_has_palette_brush(actor):
        actor["brush_stance_changed"] = False


# ═══════════════════════════════════════════════════════════════════
# AURA LOOKUPS
# ═══════════════════════════════════════════════════════════════════

def get_aura_rank(actor, color):
    """Return the stored aura rank (1-3) for a color, or 0."""
    for p in actor.get("brush_palette", []):
        if p.get("color") == color:
            return p.get("rank", 0)
    return 0


def _aura_value(actor, color, key, default=0.0):
    rank = get_aura_rank(actor, color)
    if rank <= 0:
        return default
    data = AURA_DATA.get(color, {})
    ranks = data.get("ranks", [])
    entry = ranks[min(rank, MAX_AURA_RANK) - 1] if ranks else {}
    return entry.get(key, default)


def get_brush_stance_element(actor):
    """Return the stance element (or None) — read by get_attack_element."""
    if not _actor_has_palette_brush(actor):
        return None
    return actor.get("brush_stance")


def get_brush_damage_mult(actor):
    """Stance damage multiplier (1.35x in a stance; default 1.0 = weapon's magical 1.3x).

    Recruited Palette wielding her own brush remembers the boss: Crimson +7% damage.
    """
    if not _actor_has_palette_brush(actor):
        return 1.0
    mult = STANCE_MULT if actor.get("brush_stance") else 1.0
    if actor.get("_heroine_key") == "palette" and actor.get("brush_stance") == "fire":
        mult += 0.07
    return mult


def get_brush_initiative_bonus(actor):
    """Verdant aura initiative (+3/5/8). Palette heroine in Gold stance: +5."""
    if not _actor_has_palette_brush(actor):
        return 0
    bonus = _aura_value(actor, "verdant", "init", 0)
    if actor.get("_heroine_key") == "palette" and actor.get("brush_stance") == "thunder":
        bonus += 5
    return bonus


def get_brush_dodge_bonus(actor):
    """Palette heroine in Verdant stance: +7% dodge (half boss passive)."""
    if not _actor_has_palette_brush(actor):
        return 0.0
    if actor.get("_heroine_key") == "palette" and actor.get("brush_stance") == "wind":
        return 0.07
    return 0.0


def get_brush_damage_reduction(actor):
    """Umber aura damage reduction (8/12/16%). Palette heroine in Umber stance: +10%."""
    if not _actor_has_palette_brush(actor):
        return 0.0
    dr = _aura_value(actor, "umber", "dr", 0.0)
    if actor.get("_heroine_key") == "palette" and actor.get("brush_stance") == "earth":
        dr += 0.10
    return min(dr, 0.5)


def get_brush_lifesteal(actor):
    """Obsidian aura lifesteal (8/12/16%). Palette heroine in Obsidian stance: +4%."""
    if not _actor_has_palette_brush(actor):
        return 0.0
    ls = _aura_value(actor, "obsidian", "ls", 0.0)
    if actor.get("_heroine_key") == "palette" and actor.get("brush_stance") == "dark":
        ls += 0.04
    return ls


# ═══════════════════════════════════════════════════════════════════
# PIGMENTS / WET PALETTE
# ═══════════════════════════════════════════════════════════════════

def add_pigment(actor, color):
    """Add a pigment of `color` to the Wet Palette. Returns a message string."""
    if not _actor_has_palette_brush(actor):
        return ""
    palette = actor.setdefault("brush_palette", [])
    existing = next((p for p in palette if p.get("color") == color), None)

    if existing:
        if existing["rank"] < MAX_AURA_RANK:
            existing["rank"] += 1
            return (f"  ✨ {COLOR_NAMES[color]} aura intensified — "
                    f"{AURA_DATA[color]['label']} now rank {existing['rank']}!")
        return f"  ✨ {COLOR_NAMES[color]} aura is already at full strength!"

    if len(palette) >= PALETTE_SLOTS:
        removed = palette.pop(0)
        old_color = COLOR_NAMES.get(removed["color"], removed["color"])
        palette.append({"color": color, "rank": 1})
        return (f"  ✨ {old_color} aura fades — the palette slot is repainted with "
                f"{COLOR_NAMES[color]}: {AURA_DATA[color]['label']} rank 1!")
    palette.append({"color": color, "rank": 1})
    return f"  ✨ {COLOR_NAMES[color]} pigment stored — {AURA_DATA[color]['label']} rank 1!"


def get_brush_exhibits(actor):
    """Return [(key, label)] for exhibits unlocked and unused."""
    total = actor.get("brush_total_strokes", 0)
    used = actor.get("brush_exhibits_used", set())
    labels = {
        "impasto": "Impasto (AoE + stance debuff)",
        "chiaroscuro": "Chiaroscuro (2.2x, ignores defense)",
        "signature": "Signature (3.0x + max-rank an aura)",
    }
    out = []
    for key, need in _exhibit_thresholds(actor).items():
        if total >= need and key not in used:
            out.append((key, labels[key]))
    return out


def _masterclass_active(actor):
    """True if the PLAYER wears Palette's Palette (wedding accessory) with
    Palette in the active party — Exhibits unlock early and hit harder."""
    if actor.get("is_ally"):
        return False
    from combat.weapon.wedding_specials import get_active_wedding_item, is_bonded
    item = get_active_wedding_item(actor)
    if not item or item.get("special") != "palettes_palette":
        return False
    return is_bonded(actor, item)


def _exhibit_thresholds(actor):
    if _masterclass_active(actor):
        return MASTERCLASS_THRESHOLDS
    return EXHIBIT_STROKES


# ═══════════════════════════════════════════════════════════════════
# ENEMY-SIDE DEBUFF APPLICATION (auras + Impasto exhibit)
# ═══════════════════════════════════════════════════════════════════

def _apply_color_debuff_to_enemy(target, color):
    """Apply the color's matching debuff to an enemy. Returns a message."""
    from combat.status_effects import apply_burn, apply_shock

    kind = COLOR_DEBUFF.get(color)
    if kind == "burn":
        result = apply_burn(target, tier=2, duration=3)
        return f"{target['name']} ignites! (Burn tier 2, 3 turns)" if result != "refreshed" else f"{target['name']} keeps burning!"
    if kind == "slow":
        target["slowed"] = True
        target.setdefault("active_debuffs", []).append({"type": "slow", "remaining": 2})
        return f"{target['name']} is slowed! (2 turns)"
    if kind == "shock":
        apply_shock(target, 3, 3)
        return f"{target['name']} is shocked! (3 dmg x 3 turns)"
    if kind == "blind":
        target["blinded"] = True
        target.setdefault("active_debuffs", []).append({"type": "blind", "remaining": 2})
        return f"{target['name']} is blinded! (2 turns)"
    if kind == "weaken":
        target.setdefault("active_debuffs", []).append({"type": "weaken", "value": 1, "remaining": 3})
        return f"{target['name']} is weakened! (-1 STR, 3 turns)"
    if kind == "silence":
        target["silenced"] = True
        target.setdefault("active_debuffs", []).append({"type": "silence", "remaining": 2})
        return f"{target['name']} is silenced! (2 turns)"
    if kind == "dread":
        target["dreaded"] = True
        target.setdefault("active_debuffs", []).append({"type": "dread", "remaining": 2})
        return f"{target['name']} is filled with dread! (2 turns)"
    return ""


def _roll_aura_procs(actor, target):
    """Roll the on-attack aura procs (burn/slow/shock/silence) for a hit."""
    msgs = []
    for color, chances in AURA_PROC_CHANCES.items():
        rank = get_aura_rank(actor, color)
        if rank <= 0 or target.get("hp", 0) <= 0:
            continue
        chance = chances[min(rank, MAX_AURA_RANK) - 1]
        if random.random() >= chance:
            continue
        if color == "crimson":
            from combat.status_effects import apply_burn
            tier = _aura_value(actor, "crimson", "tier", 2)
            apply_burn(target, tier=tier, duration=3)
            msgs.append(f"  🔴 Brush aura: {target['name']} ignites! (Burn tier {tier})")
        elif color == "azure":
            dur = _aura_value(actor, "azure", "dur", 2)
            target["slowed"] = True
            target.setdefault("active_debuffs", []).append({"type": "slow", "remaining": dur})
            msgs.append(f"  🔵 Brush aura: {target['name']} is slowed! ({dur} turns)")
        elif color == "gold":
            from combat.status_effects import apply_shock
            dmg = _aura_value(actor, "gold", "dmg", 3)
            apply_shock(target, dmg, 3)
            msgs.append(f"  🟡 Brush aura: {target['name']} is shocked! ({dmg} dmg x 3)")
        elif color == "alabaster":
            dur = _aura_value(actor, "alabaster", "dur", 2)
            target["silenced"] = True
            target.setdefault("active_debuffs", []).append({"type": "silence", "remaining": dur})
            msgs.append(f"  ⚪ Brush aura: {target['name']} is silenced! ({dur} turns)")
    return msgs


# ═══════════════════════════════════════════════════════════════════
# STROKE / PIGMENT EXPLOSION (called from the attack paths)
# ═══════════════════════════════════════════════════════════════════

def on_brush_attack_hit(actor, target, dmg, enemies):
    """Process strokes, Pigment Explosion, aura procs and lifesteal after a
    landed brush basic attack. Returns a list of message strings."""
    if not _actor_has_palette_brush(actor) or dmg <= 0:
        return []

    msgs = []

    # ── Strokes ──
    alive_ids = {id(e) for e in enemies if e.get("hp", 0) > 0}
    strokes = actor.setdefault("brush_strokes", {})
    strokes = {k: v for k, v in strokes.items() if k in alive_ids}
    actor["brush_strokes"] = strokes

    n = strokes.get(id(target), 0) + 1
    strokes[id(target)] = n
    actor["brush_total_strokes"] = actor.get("brush_total_strokes", 0) + 1

    if n >= STROKES_PER_PIGMENT:
        # ── Pigment Explosion ──
        extra = int(dmg * PIGMENT_EXPLOSION_PCT)
        if extra > 0 and target.get("hp", 0) > 0:
            target["hp"] = max(0, target["hp"] - extra)
            msgs.append(format_damage_msg(actor["name"], target["name"], extra,
                                          skill_name="Pigment Explosion"))
        msgs.append(f"  💥 Painting complete! Pigment Explosion on {target['name']} (+50%)!")
        strokes.pop(id(target), None)
        target.pop("brush_strokes_display", None)

        stance_el = actor.get("brush_stance")
        color = ELEMENT_TO_COLOR.get(stance_el) if stance_el else None
        if color:
            msgs.append(add_pigment(actor, color))
        else:
            msgs.append("  (No stance pigment — the paint runs neutral.)")
    else:
        target["brush_strokes_display"] = f"🎨 {n}/{STROKES_PER_PIGMENT}"
        msgs.append(f"  🎨 Brushstroke {n}/{STROKES_PER_PIGMENT} painted on {target['name']}!")

        # Exhibit unlock announcements
        total = actor.get("brush_total_strokes", 0)
        for key, need in _exhibit_thresholds(actor).items():
            if total == need:
                label = {"impasto": "Impasto", "chiaroscuro": "Chiaroscuro", "signature": "Signature"}[key]
                msgs.append(f"  🖼️  Exhibit unlocked: {label}!")

    # ── On-attack aura procs ──
    msgs.extend(_roll_aura_procs(actor, target))

    # ── Lifesteal aura ──
    ls = get_brush_lifesteal(actor)
    if ls > 0 and dmg > 0:
        heal = int(dmg * ls)
        if heal > 0:
            old_hp = actor["current_hp"]
            max_hp = actor.get("max_hp", old_hp)
            actor["current_hp"] = min(old_hp + heal, max_hp)
            actual = actor["current_hp"] - old_hp
            if actual > 0:
                msgs.append(f"  ⚫ Obsidian aura: {actor['name']} recovers {actual} HP!")

    return msgs


# ═══════════════════════════════════════════════════════════════════
# STANCE
# ═══════════════════════════════════════════════════════════════════

def set_brush_stance(actor):
    """Prompt for and commit to a color stance. Returns a message string."""
    c_print("\n  Choose a brush stance (committed before attacking):")
    for i, color in enumerate(COLOR_ORDER):
        c_print(f"    [{i + 1}] {COLOR_NAMES[color]} ({COLOR_TO_ELEMENT[color].upper()})")
    c_print("    [0] Clear stance (default magical)")
    while True:
        choice = c_input("  Stance: ").strip()
        if choice == "0":
            actor["brush_stance"] = None
            actor["brush_stance_changed"] = True
            return "  Stance cleared — attacks default to magical."
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(COLOR_ORDER):
                color = COLOR_ORDER[idx]
                actor["brush_stance"] = COLOR_TO_ELEMENT[color]
                actor["brush_stance_changed"] = True
                return f"  🎨 Stance committed: {COLOR_NAMES[color]} ({COLOR_TO_ELEMENT[color].upper()})."
        except ValueError:
            pass
        c_print("  Invalid choice.")


# ═══════════════════════════════════════════════════════════════════
# EXHIBITS
# ═══════════════════════════════════════════════════════════════════

def _exhibit_roll(actor, target, mult, element, ignore_con, stats):
    """Roll + element-scale an exhibit hit. stats = (str, con, dex, ler, wis, cha)."""
    scaling = stats[4] + stats[3] + stats[5]  # Wisdom + Learning + Charisma
    base = random.randint(4, 10) + scaling
    con = 0 if ignore_con else target.get("con_mod", 0)
    dmg = max(0, int(base * mult) - con)
    dmg = int(dmg * get_brush_damage_mult(actor))
    # Masterclass: Exhibit damage +15% while Palette is in the party
    if _masterclass_active(actor):
        dmg = int(dmg * (1 + MASTERCLASS_DMG_BONUS))
    return calculate_elemental_damage(dmg, actor, target, element)


def _mark_exhibit_used(actor, key):
    actor.setdefault("brush_exhibits_used", set()).add(key)


def execute_impasto_exhibit(actor, enemies, stats, is_player=True):
    """Impasto Exhibit: AoE in stance color; applies the stance's aura debuff
    to ALL enemies (no roll). Returns (msg, victory)."""
    stance_el = actor.get("brush_stance")
    element = stance_el or "magical"
    color = ELEMENT_TO_COLOR.get(stance_el)
    msgs = ["🖌️  EXHIBIT: IMPASTO — the canvas floods in one thick stroke!"]
    for target in [e for e in enemies if e.get("hp", 0) > 0]:
        dmg = _exhibit_roll(actor, target, 1.0, element, False, stats)
        if dmg > 0:
            target["hp"] = max(0, target["hp"] - dmg)
        msgs.append(format_damage_msg(actor["name"], target["name"], dmg, element=element, skill_name="Impasto"))
        if color:
            deb_msg = _apply_color_debuff_to_enemy(target, color)
            if deb_msg:
                msgs.append(f"  {deb_msg}")
    _mark_exhibit_used(actor, "impasto")
    enemies[:] = [e for e in enemies if e.get("hp", 0) > 0 and not e.get("captured")]
    return "\n".join(msgs), len(enemies) == 0


def execute_chiaroscuro_exhibit(actor, enemies, stats, is_player=True):
    """Chiaroscuro Exhibit: single target 2.2x total (light + dark), ignores
    defense, +1 stroke. Returns (msg, victory)."""
    alive = [e for e in enemies if e.get("hp", 0) > 0]
    if not alive:
        return "No enemies to target.", False

    if len(alive) > 1:
        try:
            choice = int(c_input("Select target for Chiaroscuro: ")) - 1
            if choice < 0 or choice >= len(alive):
                return "Invalid target.", False
            target = alive[choice]
        except ValueError:
            return "Invalid input.", False
    else:
        target = alive[0]

    msgs = ["🌗  EXHIBIT: CHIAROSCURO — light and shadow strike as one!"]
    total = 0
    for element in ("light", "dark"):
        dmg = _exhibit_roll(actor, target, 1.1, element, True, stats)
        total += max(0, dmg)
        if dmg > 0:
            target["hp"] = max(0, target["hp"] - dmg)
        msgs.append(format_damage_msg(actor["name"], target["name"], max(0, dmg), element=element, skill_name="Chiaroscuro"))

    # +1 stroke via the standard stroke path
    msgs.extend(on_brush_attack_hit(actor, target, total, enemies))

    _mark_exhibit_used(actor, "chiaroscuro")
    enemies[:] = [e for e in enemies if e.get("hp", 0) > 0 and not e.get("captured")]
    return "\n".join(msgs), len(enemies) == 0


def execute_signature_exhibit(actor, enemies, stats, is_player=True):
    """Signature Exhibit: 3.0x single target + instant full rank-up of one
    chosen aura. Returns (msg, victory)."""
    alive = [e for e in enemies if e.get("hp", 0) > 0]
    if not alive:
        return "No enemies to target.", False

    if len(alive) > 1:
        try:
            choice = int(c_input("Select target for Signature: ")) - 1
            if choice < 0 or choice >= len(alive):
                return "Invalid target.", False
            target = alive[choice]
        except ValueError:
            return "Invalid input.", False
    else:
        target = alive[0]

    stance_el = actor.get("brush_stance")
    element = stance_el or "magical"
    msgs = ["\n" + "=" * 50]
    msgs.append("🖋️  EXHIBIT: SIGNATURE — your name in seven colors.")
    msgs.append("=" * 50)

    dmg = _exhibit_roll(actor, target, 3.0, element, False, stats)
    if dmg > 0:
        target["hp"] = max(0, target["hp"] - dmg)
    msgs.append(format_damage_msg(actor["name"], target["name"], dmg, element=element, skill_name="Signature"))

    # Full rank-up of one chosen aura
    palette = actor.get("brush_palette", [])
    if palette:
        c_print("  Choose an aura to master:")
        for i, p in enumerate(palette):
            c_print(f"    [{i + 1}] {COLOR_NAMES.get(p['color'], p['color'])} "
                    f"({AURA_DATA.get(p['color'], {}).get('label', '?')}, rank {p['rank']})")
        try:
            pick = int(c_input("  Aura: ")) - 1
            if 0 <= pick < len(palette):
                color = palette[pick]["color"]
                palette[pick]["rank"] = MAX_AURA_RANK
                msgs.append(f"  ✨ {COLOR_NAMES.get(color, color)} aura mastered — rank {MAX_AURA_RANK}!")
        except ValueError:
            pass

    _mark_exhibit_used(actor, "signature")
    enemies[:] = [e for e in enemies if e.get("hp", 0) > 0 and not e.get("captured")]
    return "\n".join(msgs), len(enemies) == 0


# ═══════════════════════════════════════════════════════════════════
# PALETTE HEROINE PASSIVES (ticked at round end via tick_player_buffs)
# ═══════════════════════════════════════════════════════════════════

def tick_palette_brush_passives(actor):
    """Tick Palette-the-heroine's brush passives (Azure heal, Alabaster
    self-cleanse) at round end. No-op for non-Palette actors."""
    if not _actor_has_palette_brush(actor) or actor.get("_heroine_key") != "palette":
        return []

    msgs = []
    stance = actor.get("brush_stance")

    # Azure: heal 1.5% max HP per turn
    if stance == "water" and actor.get("current_hp", 0) > 0:
        max_hp = actor.get("max_hp", 1)
        heal = int(max_hp * 0.015)
        if heal > 0 and actor["current_hp"] < max_hp:
            old_hp = actor["current_hp"]
            actor["current_hp"] = min(old_hp + heal, max_hp)
            actual = actor["current_hp"] - old_hp
            if actual > 0:
                msgs.append(f"🎨 {actor['name']}'s Azure glaze restores {actual} HP.")

    # Alabaster: clear 1 self-debuff per turn
    if stance == "light" and actor.get("active_debuffs"):
        removed = actor["active_debuffs"].pop(0)
        msgs.append(f"⚪ {actor['name']}'s Alabaster self-cleans {removed.get('type', 'a debuff').upper()}.")

    return msgs


# ═══════════════════════════════════════════════════════════════════
# ACTION MENU (player + ally)
# ═══════════════════════════════════════════════════════════════════

def get_brush_action_menu(actor, player, enemies, is_player):
    """Build the action menu when Palette's Brush is equipped.

    Returns (menu_str, valid_keys, disabled_keys).
    """
    from combat.capture import is_capturable
    from combat.status_effects import is_silenced

    actions = []
    disabled_keys = []

    if is_player and any(is_capturable(e) for e in enemies):
        actions.append(('c', 'Capture'))

    actions.append(('a', 'Attack'))

    # Stance: free action, once per turn
    if actor.get("brush_stance_changed"):
        actions.append(('t', f'Stance [{(actor.get("brush_stance") or "none").upper()}]'))
        disabled_keys.append('t')
    else:
        actions.append(('t', 'Stance'))

    actions.append(('d', 'Defend'))
    if is_player:
        actions.append(('f', 'Flee'))
    else:
        from combat.ally import can_switch
        if can_switch(player):
            actions.append(('s', 'Switch'))

    if is_player:
        if not is_silenced(actor):
            actions.append(('u', 'Use item'))
    else:
        combat_items = [
            item for item in player.get("inventory", [])
            if item.get("type") in ["consumable", "utility"]
        ]
        if combat_items:
            actions.append(('u', 'Use Item'))

    # Blank Canvas Shawl (armor special, free action)
    from combat.weapon.blank_canvas_shawl import _actor_has_blank_canvas_shawl
    if _actor_has_blank_canvas_shawl(actor) and not actor.get("blank_canvas_used"):
        actions.append(('b', 'Blank Canvas'))

    # Exhibits
    exhibit_keys = {"impasto": 'i', "chiaroscuro": 'k', "signature": 'g'}
    for key, label in get_brush_exhibits(actor):
        actions.append((exhibit_keys[key], label))

    menu_str = '  '.join(f'[{k.upper()}]{label}' for k, label in actions)
    valid_keys = [k for k, _ in actions if k not in disabled_keys]
    return menu_str, valid_keys, disabled_keys
