# combat/palette_ally.py
"""Palette the heroine — the "Degraded Masterpiece" ally kit.

Her default skills are weakened boss moves (no Paint stacks in ally form):
  - Brushstroke: 0.7x, always her current color's element.
  - Spectrum: 3 hits at 0.3x, one random element per hit (3-turn cooldown).
  - Signature: 2.5x, ignores defense, 1-turn telegraph, 4-turn cooldown.

Her colors cycle in boss order, one shift per turn (skipped while she wields
her own brush — the brush kit replaces this one entirely).
"""

import random

from combat.combat_io import c_input
from combat.helpers import format_damage_msg
from combat.elemental import calculate_elemental_damage
from combat.weapon.palette_brush import (
    COLOR_ORDER as COLOR_CYCLE,
    COLOR_NAMES,
    COLOR_TO_ELEMENT,
)

SIGNATURE_MULT = 2.5
SPECTRUM_HITS = 3
SPECTRUM_MULT = 0.3

SIGNATURE_COOLDOWN = 4
SPECTRUM_COOLDOWN = 3


def is_palette_ally(actor):
    """True if the actor is the recruited Palette heroine."""
    return actor.get("_heroine_key") == "palette"


def get_palette_ally_color(ally):
    """Her current color (stored as an index; safe on any dict)."""
    idx = ally.get("palette_color_idx", 0) % len(COLOR_CYCLE)
    return COLOR_CYCLE[idx]


def advance_palette_ally_color(ally):
    """Advance her color by one step (boss order) and return the new color."""
    ally["palette_color_idx"] = ally.get("palette_color_idx", 0) + 1
    return get_palette_ally_color(ally)


def get_palette_ally_color_element(ally):
    """The element of her current color."""
    return COLOR_TO_ELEMENT[get_palette_ally_color(ally)]


def has_pending_signature(ally):
    """True if she telegraphed a Signature that must strike this turn."""
    return bool(ally.get("palette_signature_pending"))


def clear_palette_ally_state(ally):
    """Clear deferred-kit state at combat end (pending Signature telegraph)."""
    ally.pop("palette_signature_pending", None)


# ═══════════════════════════════════════════════════════════════════
# SKILL EXECUTION (called from ally_skills.execute_ally_skill / handle_ally_turn)
# ═══════════════════════════════════════════════════════════════════

def _pick_enemy(live, prompt):
    if not live:
        return None
    if len(live) == 1:
        return live[0]
    try:
        choice = int(c_input(prompt)) - 1
        if 0 <= choice < len(live):
            return live[choice]
    except ValueError:
        pass
    return live[0]


def start_palette_signature(ally):
    """Begin painting — the Signature strikes on her NEXT turn."""
    ally["palette_signature_pending"] = True
    color = COLOR_NAMES[get_palette_ally_color(ally)]
    return (f"  🖋️  {ally['name']} begins painting the target's name in {color}... "
            f"The Signature will strike NEXT turn! (cannot be defended)")


def fire_palette_signature(ally, player, enemies, on_kill=None):
    """Resolve the telegraphed Signature: 2.5x, ignores defense, current color."""
    ally.pop("palette_signature_pending", None)

    live = [e for e in enemies if e["hp"] > 0]
    target = _pick_enemy(live, "  Signature target: ")
    if target is None:
        return f"  🖋️  {ally['name']}'s Signature fizzles — no enemies remain."

    from combat.ally import compute_ally_stats
    _s, _c, _d, a_ler, a_wis, _ch = compute_ally_stats(ally)
    scaling = a_wis + a_ler // 2
    base = random.randint(4, 10) + scaling
    dmg = int(base * SIGNATURE_MULT)  # ignores defense entirely
    element = get_palette_ally_color_element(ally)
    dmg = calculate_elemental_damage(dmg, ally, target, element)
    target["hp"] = max(0, target["hp"] - dmg)

    msgs = [format_damage_msg(ally["name"], target["name"], dmg,
                              element=element, skill_name="Signature")]
    if target["hp"] <= 0:
        msgs.append(f"  {target['name']} is defeated!")
        if on_kill:
            on_kill(target, enemies)
    enemies[:] = [e for e in enemies if e["hp"] > 0 and not e.get("captured")]
    return "\n".join(msgs)


def palette_spectrum_attack(ally, player, enemies):
    """Spectrum: 3 hits at 0.3x, one random element each, on one target.

    Returns (message, victory).
    """
    live = [e for e in enemies if e["hp"] > 0]
    target = _pick_enemy(live, "  Spectrum target: ")
    if target is None:
        return "No enemies to target.", False

    from combat.ally import compute_ally_stats
    _s, _c, _d, a_ler, a_wis, _ch = compute_ally_stats(ally)
    scaling = a_ler + a_wis // 2
    elements = ["fire", "water", "thunder", "wind", "earth", "light", "dark"]

    msgs = [f"  🌈 {ally['name']} scatters a Spectrum of three colors!"]
    for _ in range(SPECTRUM_HITS):
        if target["hp"] <= 0:
            break
        element = random.choice(elements)
        base = random.randint(4, 10) + scaling
        dmg = max(0, int(base * SPECTRUM_MULT) - target.get("con_mod", 0))
        dmg = calculate_elemental_damage(dmg, ally, target, element)
        if dmg > 0:
            target["hp"] = max(0, target["hp"] - dmg)
        msgs.append(format_damage_msg(ally["name"], target["name"], max(0, dmg),
                                      element=element, skill_name="Spectrum"))

    if target["hp"] <= 0:
        msgs.append(f"  {target['name']} is defeated!")
    enemies[:] = [e for e in enemies if e["hp"] > 0 and not e.get("captured")]
    return "\n".join(msgs), len(enemies) == 0
