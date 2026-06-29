"""Shared helper functions for combat modules."""


def _player_has_tarnished_jade(player):
    """Return True if player has Tarnished Jade equipped as armor."""
    equipment = player.get("equipped", {})
    if isinstance(equipment, dict):
        armor = equipment.get("armor")
        if armor and armor.get("id") == "tarnished_jade":
            return True
    return None
