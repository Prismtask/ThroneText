# combat/action_menu.py
from combat.capture import is_monster_girl, is_capturable
from combat.abyss_fang import is_abyss_fang_available
from combat.captain_cutlass import is_captain_cutlass_available
from combat.authors_pen import is_authors_pen_available
from combat.status_effects import is_silenced
from combat.skills import get_available_skills


def _player_has_black_silence_gloves(player):
    """Check if the player has Black Silence gloves equipped in weapon slot."""
    equipped = player.get("equipped", {})
    if isinstance(equipped, dict):
        weapon = equipped.get("weapon")
        if weapon and weapon.get("id") == "certain_someone_black_gloves":
            return True
    return False


def get_action_menu(player, enemies):
    """
    Build the action menu string and the list of valid keys.
    Returns: (menu_string, valid_keys_list, disabled_keys_list)
    
    Note: Switch is only available to allies, not the player.
    """
    actions = []

    # Check if Black Silence Gloves are equipped — replaces entire menu
    if _player_has_black_silence_gloves(player):
        return _get_gloves_menu(player, enemies)

    # Capture – only if a capturable monster girl is alive
    if any(is_capturable(e) for e in enemies):
        actions.append(('c', 'Capture'))

    # Core actions
    actions.append(('a', 'Attack'))
    actions.append(('d', 'Defend'))
    actions.append(('f', 'Flee'))

    # Use item – blocked if silenced
    if not is_silenced(player):
        actions.append(('u', 'Use item'))

    # Abyss Fang – only if equipped and not on cooldown
    if is_abyss_fang_available(player):
        actions.append(('w', 'Wield the Abyss'))

    # Captain's Cutlass – Crew Rally
    if is_captain_cutlass_available(player):
        actions.append(('r', 'Crew Rally'))

    # Author's Pen – Rewrite
    if is_authors_pen_available(player):
        actions.append(('e', 'Rewrite'))

    # Skills – add available class skills as numbered options
    available_skills = get_available_skills(player)
    for idx, (sid, sdef) in enumerate(available_skills):
        key = str(idx + 1)
        actions.append((key, sdef['name']))

    menu_str = '  '.join(f'[{key.upper()}]{label}' for key, label in actions)
    valid_keys = [key for key, _ in actions]

    return menu_str, valid_keys, []


def _get_gloves_menu(player, enemies):
    """Build the action menu when Black Silence gloves are equipped.
    Replaces attack, skills, and special weapon actions with 9 workshop attacks + Furioso.
    
    Returns: (menu_string, valid_keys_list, disabled_keys_list)
    """
    actions = []
    disabled_keys = []

    # Capture
    if any(is_capturable(e) for e in enemies):
        actions.append(('c', 'Capture'))

    # Core actions (no Attack — gloves replace it)
    actions.append(('d', 'Defend'))
    actions.append(('f', 'Flee'))

    # Use item (blocked if silenced)
    if not is_silenced(player):
        actions.append(('u', 'Use item'))

    # Workshop attacks 1-9
    workshop_state = player.get("gloves_workshop_used", set())
    if not isinstance(workshop_state, (set, list)):
        workshop_state = set()
    workshop_menu = [
        ('1', 'Allas Workshop [STR]'),
        ('2', 'Wheels Industry [STR]'),
        ('3', 'Zelkova Workshop [DEX]'),
        ('4', 'Old Boys Workshop [STR]'),
        ('5', 'Mook Workshop [WIS]'),
        ('6', 'Ranga Workshop [DEX]'),
        ('7', 'Crystal Atelier [DEX]'),
        ('8', 'Atelier Logic [WIS]'),
        ('9', 'Durandal [LEA]'),
    ]
    for key, label in workshop_menu:
        if int(key) not in workshop_state:
            actions.append((key, label))
        else:
            actions.append((key, f'{label} [USED]'))
            disabled_keys.append(key)

    # Furioso — only if all 9 used
    if player.get("gloves_furioso_available"):
        actions.append(('0', 'FURIOSO'))

    menu_str = '  '.join(f'[{key.upper()}]{label}' for key, label in actions)
    valid_keys = [key for key, _ in actions if key not in disabled_keys]

    return menu_str, valid_keys, disabled_keys