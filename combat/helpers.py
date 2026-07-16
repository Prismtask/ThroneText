"""Shared helper functions for combat modules."""


# ── Element / Crit tag maps ─────────────────────────────────────────────────

ELEMENT_TAGS = {
    "fire": "[FIRE]", "water": "[ICE]", "thunder": "[THUNDER]",
    "wind": "[WIND]", "earth": "[EARTH]", "light": "[LIGHT]", "dark": "[DARK]",
    "physical": "[PHYSICAL]", "magical": "[MAGICAL]",
}


def format_damage_msg(source_name, target_name, damage, element=None, crit=False, skill_name=None):
    """Build a consistent combat‑log damage message.

    Standard format:
        Source [skill] → Target: N dmg [ELEMENT] (CRITICAL!)

    Parameters
    ----------
    source_name : str   – name of the attacker
    target_name : str   – name of the defender
    damage      : int   – final HP reduction dealt
    element     : str or None – elemental flavour key (see ELEMENT_TAGS)
    crit        : bool  – was this a critical hit?
    skill_name  : str or None – skill name to append (e.g. "Fireball")

    Returns
    -------
    str – ready‑to‑print log line
    """
    tag = ELEMENT_TAGS.get(element, "")
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
