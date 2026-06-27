# stats.py – attribute math, scaling, and enemy stats
from resources.enemies import ENEMIES, ENEMY_RACES
from resources.races_classes import ATTRIBUTES
from inventory import get_total_equipment_mods
from utils import get_difficulty_multiplier_from_time
from combat.status_effects import get_weaken_penalty


def compute_enemy_attributes(enemy_key):
    template = ENEMIES[enemy_key]
    race_name = template["race"]
    race_mods = ENEMY_RACES[race_name].get("mods", {})
    personal_mods = template.get("mods", {})

    base = {attr: 0 for attr in ATTRIBUTES}
    for attr, mod in race_mods.items():
        base[attr] += mod
    for attr, mod in personal_mods.items():
        base[attr] += mod
    return base


def enemy_stats(enemy_key, player=None):
    template = ENEMIES[enemy_key]
    attrs = compute_enemy_attributes(enemy_key)

    multiplier = get_difficulty_multiplier_from_time(player) if player else 1.0

    base_hp = template["base_hp"]
    str_mod = attrs["Strength"]
    con_mod = attrs["Constitution"]
    dex_mod = attrs["Dexterity"]

    scaled_hp = int(base_hp * multiplier)
    scaled_str = int(str_mod * (1 + (multiplier - 1) * 0.7))
    scaled_con = int(con_mod * (1 + (multiplier - 1) * 0.6))
    scaled_dex = int(dex_mod * (1 + (multiplier - 1) * 0.5))

    result = {
        "key": enemy_key,
        "name": template["name"],
        "hp": scaled_hp,
        "max_hp": scaled_hp,
        "str_mod": scaled_str,
        "con_mod": scaled_con,
        "dex_mod": scaled_dex,
        "level": template["level"],
        "multiplier": round(multiplier, 2),
        "monster_girl": template.get("monster_girl", False)
    }

    # Add elemental stats
    from combat.elemental import compute_enemy_elemental
    e_res, e_dmg = compute_enemy_elemental(result)
    result["elemental_res"] = e_res
    result["elemental_dmg"] = e_dmg

    return result


def get_effective_attribute(player, attr_name):
    """Return effective attribute value after curse/weaken/buffs/equipment/passive."""
    base = player["attributes"].get(attr_name, 0)
    equip_mods = get_total_equipment_mods(player)
    total = base + equip_mods.get(attr_name, 0)

    # Apply passive skill bonuses
    from combat.skills import get_passive_skill
    passive = get_passive_skill(player)
    if passive and player.get("passive_unlocked", True):
        effect = passive.get("effect", {})
        if effect.get("stat") == "all":
            affected = effect.get("stats", [])
            if attr_name in affected:
                total += effect.get("value", 0)
        elif effect.get("stat") == attr_name:
            total += effect.get("value", 0)

    for debuff in player.get("active_debuffs", []):
        if debuff.get("type") == "curse":
            penalty = debuff.get("penalty", 2)
            total -= penalty

    if attr_name == "Strength":
        total -= get_weaken_penalty(player)

    for buff in player.get("active_buffs", []):
        if buff.get("type") in ("blessing", "well_rested") or buff.get("stat") == "all":
            total += buff.get("value", 0)
        elif buff.get("stat") == attr_name:
            total += buff.get("value", 0)

    # Apply percentage buffs (e.g., cosmic_gravity)
    pct_mult = 1.0
    for buff in player.get("active_buffs", []):
        if buff.get("type") == "wedding_stats":
            pct_mult += buff.get("value", 0)
    if pct_mult != 1.0:
        total = int(total * pct_mult)

    return total


def compute_player_stats(player):
    p_str = get_effective_attribute(player, "Strength")
    p_con = get_effective_attribute(player, "Constitution")
    p_dex = get_effective_attribute(player, "Dexterity")
    p_ler = get_effective_attribute(player, "Learning")
    p_wis = get_effective_attribute(player, "Wisdom")
    p_cha = get_effective_attribute(player, "Charisma")
    if player.get("training_buff"):
        p_str += player["training_buff"].get("strength", 0)
    return p_str, p_con, p_dex, p_ler, p_wis, p_cha

def player_str_mod(player):
    return player["attributes"]["Strength"]

def player_con_mod(player):
    return player["attributes"]["Constitution"]

def player_dex_mod(player):
    return player["attributes"]["Dexterity"]

def player_wis_mod(player):
    return player["attributes"]["Wisdom"]

def player_ler_mod(player):
    return player["attributes"]["Learning"]

def player_chr_mod(player):
    return player["attributes"]["Charisma"]