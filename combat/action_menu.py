# combat/action_menu.py
from combat.capture import is_monster_girl
from combat.helpers import _player_has_abyss_fang          # <-- changed import
from combat.status_effects import is_silenced


def get_action_menu(player, enemies):
    """
    Build the action menu string and the list of valid keys.
    Returns: (menu_string, valid_keys_list)
    """
    actions = []

    # Capture – only if a monster girl is alive
    if any(is_monster_girl(e) for e in enemies):
        actions.append(('c', 'Capture'))

    # Core actions
    actions.append(('a', 'Attack'))
    actions.append(('d', 'Defend'))
    actions.append(('f', 'Flee'))

    # Use item – blocked if silenced
    if not is_silenced(player):
        actions.append(('u', 'Use item'))

    # Abyss Fang – only if equipped and not on cooldown
    abyss_fang = _player_has_abyss_fang(player)
    abyss_cd = player.get('abyss_fang_cooldown', 0)
    if abyss_fang and abyss_cd <= 0:
        actions.append(('w', 'Wield the Abyss'))

    menu_str = '  '.join(f'[{key.upper()}]{label}' for key, label in actions)
    valid_keys = [key for key, _ in actions]

    return menu_str, valid_keys