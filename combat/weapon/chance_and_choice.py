"""Chance and Choice — Event Horizon trophy accessory (docs/event_horizon_design.md §10.5).

Once per damaging ACTION, a 50/50 coin scales the action's damage:
50% → ×0.25 ("disaster"), 50% → ×1.75 ("fortune"). Expected value = 1.0 —
pure volatility, no expected-power change.

Per-action state lives in the caller's damage closure::

    _cac_state = {"rolled": False, "mult": 1.0}   # once per action
    dmg = apply_chance_and_choice(actor, dmg, _cac_state)

Basic attacks (one damage instance per action) may pass ``state=None`` —
the roll then happens per call, which is still once per action.

Applies to direct damaging actions only (not DoTs, heals, or traps).
"""

import random

from combat.combat_io import c_print

LOW_MULT = 0.25
HIGH_MULT = 1.75
LOW_CHANCE = 0.5

_ITEM_ID = "chance_and_choice"
_SPECIAL = "chance_and_choice"


def actor_has_chance_and_choice(actor):
    if not actor:
        return False
    for item in (actor.get("equipped", {}) or {}).values():
        if item and (item.get("special") == _SPECIAL or item.get("id") == _ITEM_ID):
            return True
    return False


def apply_chance_and_choice(actor, damage, state=None):
    """Apply the coin multiplier to `damage`. See module docstring."""
    if damage <= 0 or not actor_has_chance_and_choice(actor):
        return damage
    if state is not None and state.get("rolled"):
        mult = state.get("mult", 1.0)
        return max(0, int(damage * mult))

    if random.random() < LOW_CHANCE:
        mult = LOW_MULT
        c_print("  🪙 The coin lands on its edge — disaster! (damage ×0.25)")
    else:
        mult = HIGH_MULT
        c_print("  🪙 The coin lands true — fortune! (damage ×1.75)")
    if state is not None:
        state["rolled"] = True
        state["mult"] = mult
    return max(0, int(damage * mult))
