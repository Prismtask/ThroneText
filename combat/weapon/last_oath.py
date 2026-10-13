"""Last Oath — unique rapier (White Knight of the Fallen Empire reward).

Basic attacks apply Expose to the target through the shared item-side
``apply_expose()`` system: 1 armor reduction normally, 2 on a crit.
Respects the existing 5-total reduction cap and the global status_res roll.

Actor-based per the unique-equipment convention — works for the player
and allies alike.
"""


def _actor_has_last_oath(actor):
    """Return the Last Oath weapon dict if equipped on the actor, else None."""
    equipment = actor.get("equipped", {})
    if isinstance(equipment, dict):
        weapon = equipment.get("weapon")
        if weapon and weapon.get("special") == "last_oath":
            return weapon
    return None


def try_last_oath_expose(actor, target, is_crit=False):
    """Apply Expose on a landed basic attack. Returns a message or None.

    A resisted application is silent (too spammy on 75%-resist superbosses);
    the HUD still shows whether the enemy's armour actually changed.
    """
    if target.get("hp", 0) <= 0 or not _actor_has_last_oath(actor):
        return None
    from combat.status_effects import apply_expose
    result, new_con = apply_expose(target, 2 if is_crit else 1)
    if result == "applied":
        return f"  ⚜ Last Oath finds the seam — {target['name']}'s armour: {new_con}!"
    return None
