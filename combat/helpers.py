"""Shared helper functions for combat modules."""

def _player_has_abyss_fang(player):
    """Return the Abyss Fang weapon dict if equipped, else None."""
    equipment = player.get("equipped", {})
    if isinstance(equipment, dict):
        weapon = equipment.get("weapon")
        if weapon and weapon.get("special") == "dream_devour":
            return weapon
    return None