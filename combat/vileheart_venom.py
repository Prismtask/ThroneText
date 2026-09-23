# combat/vileheart_venom.py
"""Vileheart Venom — passive poison-on-hit from the Vileheart Pendant.

Superboss drop from Broodmother Vileheart. When equipped as accessory,
physical attacks gain a chance to apply poison.
"""

import random
from combat.status_effects import apply_poison


def _actor_has_vileheart_pendant(actor):
    """Return True if the actor has the Vileheart Pendant equipped."""
    equipment = actor.get("equipped", {})
    if isinstance(equipment, dict):
        for slot in ("accessory1", "accessory2", "accessory"):
            acc = equipment.get(slot)
            if acc and acc.get("special") == "vileheart_venom":
                return True
    return False


def try_vileheart_venom_proc(actor, target):
    """Attempt to apply poison via the Vileheart Pendant passive.

    Called after a successful physical attack lands on a target.
    - 25% base chance to apply Poison (4 dmg x 3 turns).
    - 50% chance if the target is already poisoned (refreshes duration).

    Returns True if poison was applied/refreshed.
    """
    if not _actor_has_vileheart_pendant(actor):
        return False

    # Check if target is already poisoned
    already_poisoned = any(
        d.get("type") == "poison"
        for d in target.get("active_debuffs", [])
    )
    chance = 0.50 if already_poisoned else 0.25

    if random.random() < chance:
        result = apply_poison(target, damage=4, duration=3)
        return result in ("applied", "refreshed")

    return False
