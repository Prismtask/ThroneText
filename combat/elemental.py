# combat/elemental.py – Elemental damage/resistance system
"""Dynamic elemental system. Every entity has elemental_res and elemental_dmg.

res  < 1.0 = resistant (take less damage)
res  = 1.0 = neutral
res  > 1.0 = weak (take more damage)

dmg  < 1.0 = weak output with that element
dmg  = 1.0 = neutral
dmg  > 1.0 = strong output with that element
"""

ELEMENTS = ["fire", "water", "thunder", "wind", "earth", "light", "dark"]


def neutral_profile():
    """Return a neutral (1.0) profile for all elements."""
    return {el: 1.0 for el in ELEMENTS}


def merge_profiles(base, override):
    """Merge two elemental profiles, with override values replacing base."""
    result = base.copy()
    if override:
        for el, val in override.items():
            if el in result:
                result[el] = val
    return result


def add_profiles(a, b):
    """Add two profiles together, capped at 0.0 minimum, 2.0 maximum."""
    result = {}
    for el in ELEMENTS:
        total = a.get(el, 1.0) + b.get(el, 0.0) - 1.0
        result[el] = max(0.0, min(2.0, total))
    return result


def _get_equipment_elemental(player_or_ally, which):
    """Sum elemental stats from equipped items.
    
    which: 'elemental_res' for armor resistances, 'elemental_dmg' for weapon damage.
    """
    total = {}
    for slot, item in player_or_ally.get("equipped", {}).items():
        if item and which in item:
            for el, val in item[which].items():
                total[el] = total.get(el, 0.0) + val
    return total


def compute_player_elemental(player):
    """Compute player's total elemental profile from race + class + equipment."""
    from resources.races_classes import RACES, CLASSES
    race_name = player.get("race", "Human")
    class_name = player.get("class", "Warrior")
    
    # Find race key by name
    race_profile_res = neutral_profile()
    race_profile_dmg = neutral_profile()
    for key, data in RACES.items():
        if data["name"] == race_name:
            race_profile_res = merge_profiles(race_profile_res, data.get("elemental_res", {}))
            race_profile_dmg = merge_profiles(race_profile_dmg, data.get("elemental_dmg", {}))
            break
    
    # Find class key by name
    class_profile_res = neutral_profile()
    class_profile_dmg = neutral_profile()
    for key, data in CLASSES.items():
        if data["name"] == class_name:
            class_profile_res = merge_profiles(class_profile_res, data.get("elemental_res", {}))
            class_profile_dmg = merge_profiles(class_profile_dmg, data.get("elemental_dmg", {}))
            break
    
    # Combine base (race + class, but offset by 1.0 since both are full profiles)
    base_res = {}
    base_dmg = {}
    for el in ELEMENTS:
        base_res[el] = max(0.0, min(2.0, race_profile_res[el] + class_profile_res[el] - 1.0))
        base_dmg[el] = max(0.0, min(2.0, race_profile_dmg[el] + class_profile_dmg[el] - 1.0))
    
    # Add equipment
    equip_res = _get_equipment_elemental(player, "elemental_res")
    equip_dmg = _get_equipment_elemental(player, "elemental_dmg")
    
    final_res = {}
    final_dmg = {}
    for el in ELEMENTS:
        # Equipment adds delta (val - 1.0) to base
        res_bonus = equip_res.get(el, 1.0)
        dmg_bonus = equip_dmg.get(el, 1.0)
        final_res[el] = max(0.0, min(2.0, base_res[el] + res_bonus - 1.0))
        final_dmg[el] = max(0.0, min(2.0, base_dmg[el] + dmg_bonus - 1.0))
    
    return final_res, final_dmg


def compute_enemy_elemental(enemy):
    """Compute enemy's total elemental profile from race + individual overrides."""
    from resources.enemies import ENEMIES, ENEMY_RACES
    
    key = enemy.get("key")
    if key:
        template = ENEMIES.get(key, {})
        race_name = template.get("race", "Human")
    else:
        template = {}
        race_name = "Human"
    
    race_data = ENEMY_RACES.get(race_name, {})
    
    res = merge_profiles(neutral_profile(), race_data.get("elemental_res", {}))
    dmg = merge_profiles(neutral_profile(), race_data.get("elemental_dmg", {}))
    
    # Apply individual overrides from enemy template
    res = merge_profiles(res, template.get("elemental_res", {}))
    dmg = merge_profiles(dmg, template.get("elemental_dmg", {}))
    
    return res, dmg


def compute_ally_elemental(ally):
    """Compute ally's total elemental profile from enemy race + equipment."""
    from resources.enemies import ENEMIES, ENEMY_RACES
    
    key = ally.get("key")
    if key:
        template = ENEMIES.get(key, {})
        race_name = template.get("race", "Human")
    else:
        race_name = "Human"
    
    race_data = ENEMY_RACES.get(race_name, {})
    
    base_res = merge_profiles(neutral_profile(), race_data.get("elemental_res", {}))
    base_dmg = merge_profiles(neutral_profile(), race_data.get("elemental_dmg", {}))
    
    # Add equipment
    equip_res = _get_equipment_elemental(ally, "elemental_res")
    equip_dmg = _get_equipment_elemental(ally, "elemental_dmg")
    
    final_res = {}
    final_dmg = {}
    for el in ELEMENTS:
        res_bonus = equip_res.get(el, 1.0)
        dmg_bonus = equip_dmg.get(el, 1.0)
        final_res[el] = max(0.0, min(2.0, base_res[el] + res_bonus - 1.0))
        final_dmg[el] = max(0.0, min(2.0, base_dmg[el] + dmg_bonus - 1.0))
    
    return final_res, final_dmg


def get_attack_element(attacker, equipped_weapon=None):
    """Determine the element of a basic attack based on equipped weapon.
    Returns an element string or None for neutral/physical.
    """
    if equipped_weapon and "elemental_dmg" in equipped_weapon:
        # Return the element with the highest damage multiplier > 1.0
        best_el = None
        best_val = 1.0
        for el, val in equipped_weapon["elemental_dmg"].items():
            if val > best_val:
                best_val = val
                best_el = el
        if best_el:
            return best_el
    return None


def calculate_elemental_damage(base_dmg, attacker, target, element=None):
    """Apply elemental modifiers to base damage.
    
    If element is None, attempts to auto-detect from attacker's weapon.
    If no element is found, damage is neutral (1.0).
    """
    if element is None:
        element = get_attack_element(attacker)
    
    if not element or element not in ELEMENTS:
        return base_dmg
    
    # Get attacker's damage multiplier for this element
    attacker_dmg = attacker.get("elemental_dmg", {})
    dmg_mult = attacker_dmg.get(element, 1.0)
    
    # Get target's resistance to this element
    target_res = target.get("elemental_res", {})
    res_mult = target_res.get(element, 1.0)
    
    final_dmg = int(base_dmg * dmg_mult * res_mult)
    return max(0, final_dmg)


def format_elemental_short(profile):
    """Format a compact elemental profile string for display.
    Only shows values that differ from 1.0."""
    parts = []
    for el in ELEMENTS:
        val = profile.get(el, 1.0)
        if val != 1.0:
            sign = "+" if val > 1.0 else ""
            parts.append(f"{el[:3].upper()}{sign}{val:.1f}")
    return " ".join(parts) if parts else "Neutral"
