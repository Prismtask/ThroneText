# combat/weapon/sky_piercer.py
"""Sky Piercer — unique guild legacy accessory.

When the wielder's attack leaves a non-Super-Boss enemy at or below the
execute threshold, the enemy is slain instantly. The threshold scales with
the accessory's enhance level: 5% + 3% per enhance, capped at 20% of max HP.

Actor-based: works for the player and any ally who has it equipped.
"""

from combat.combat_io import c_print

_SLOTS = ("accessory1", "accessory2", "accessory")


def _get_equipped_sky_piercer(actor):
    """Return the equipped Sky Piercer item dicts, or []."""
    equipment = actor.get("equipped", {})
    if not isinstance(equipment, dict):
        return []
    accs = []
    for slot in _SLOTS:
        acc = equipment.get(slot)
        if acc and acc.get("id") == "sky_piercer":
            accs.append(acc)
    return accs


def _actor_has_sky_piercer(actor):
    """Return True if actor has Sky Piercer equipped as an accessory."""
    return bool(_get_equipped_sky_piercer(actor))


def get_sky_piercer_threshold_pct(actor):
    """Execute threshold as % of max HP: 5 + 3*enhance, capped at 20."""
    accs = _get_equipped_sky_piercer(actor)
    if not accs:
        return 0
    enhance = max(acc.get("enhance", 0) for acc in accs)
    return min(20, 5 + 3 * enhance)


def check_sky_piercer_execute(actor, target, dmg):
    """Call immediately after the actor deals damage to a target.

    If the actor wields Sky Piercer and the target survives the hit at or
    below the execute threshold (and is not a Super Boss), the target's HP
    is set to 0 so existing death/on-kill handling fires normally.
    """
    if not _actor_has_sky_piercer(actor):
        return
    if dmg is None or dmg <= 0:
        return
    if target.get("super_boss") or target.get("captured"):
        return
    hp = target.get("hp", 0)
    max_hp = target.get("max_hp", 0)
    if hp <= 0 or max_hp <= 0:
        return
    threshold = get_sky_piercer_threshold_pct(actor)
    if threshold <= 0:
        return
    if hp / max_hp * 100.0 <= threshold:
        target["hp"] = 0
        c_print(f"  ☁️ Sky Piercer! {target['name']} is pierced through the heavens!")
