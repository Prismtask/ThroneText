"""Shared helper functions for combat modules."""


# Sentinel message returned by skill/exhibit/workshop executors when the acting
# actor canceled target selection (Esc/0 or invalid input). Callers must treat
# it as a cancel: reopen the action menu without consuming the turn or setting
# cooldowns / consuming resources.
ACTION_CANCELLED_MSG = "Action canceled."


# ── Element / Crit tag maps ─────────────────────────────────────────────────

ELEMENT_TAGS = {
    "fire": "[FIRE]", "water": "[WATER]", "thunder": "[THUNDER]",
    "wind": "[WIND]", "earth": "[EARTH]", "light": "[LIGHT]", "dark": "[DARK]",
    "physical": "[PHYSICAL]", "magical": "[MAGICAL]",
}


class DamageResult(int):
    """Damage amount that remembers whether the hit was a critical.

    Skill damage helpers (``combat/skills.py::_calc_dmg``) return this instead
    of a bare ``int`` so the ``(CRITICAL!)`` tag lands on the damage line at
    every call site without threading a second return value through each of
    them. It behaves exactly like ``int`` in arithmetic and comparisons.
    """

    crit: bool

    def __new__(cls, value, crit=False):
        obj = super().__new__(cls, int(value))
        obj.crit = bool(crit)
        return obj


def format_damage_msg(source_name, target_name, damage, element=None, crit=False, skill_name=None):
    """Build a consistent combat‑log damage message.

    Standard format:
        Source [skill] → Target: N dmg (CRITICAL!) [ELEMENT]

    Parameters
    ----------
    source_name : str   – name of the attacker
    target_name : str   – name of the defender
    damage      : int   – final HP reduction dealt (a ``DamageResult`` also
                          carries its own crit flag, which turns on the tag)
    element     : str or None – elemental flavour key (see ELEMENT_TAGS)
    crit        : bool  – was this a critical hit?
    skill_name  : str or None – skill name to append (e.g. "Fireball")

    Returns
    -------
    str – ready‑to‑print log line
    """
    tag = ELEMENT_TAGS.get(element, "")
    if not crit:
        crit = bool(getattr(damage, "crit", False))
    crit_tag = " (CRITICAL!)" if crit else ""
    skill_part = f" [{skill_name}]" if skill_name else ""
    return f"{source_name}{skill_part} → {target_name}: {damage} dmg{crit_tag} {tag}".strip()


def _player_has_tarnished_jade(player):
    """Return True if player has Tarnished Jade equipped as armor."""
    equipment = player.get("equipped", {})
    if isinstance(equipment, dict):
        armor = equipment.get("armor")
        if armor and armor.get("id") == "tarnished_jade":
            return True
    return None
