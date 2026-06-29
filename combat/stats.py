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
    pandemonium_mult = 1.7 if player and player.get("pandemonium_mode") else 1.0

    base_hp = template["base_hp"]
    str_mod = attrs["Strength"]
    con_mod = attrs["Constitution"]
    dex_mod = attrs["Dexterity"]

    scaled_hp = int(base_hp * multiplier * pandemonium_mult)
    scaled_str = int(str_mod * (1 + (multiplier - 1) * 0.7) * pandemonium_mult)
    scaled_con = int(con_mod * (1 + (multiplier - 1) * 0.6) * pandemonium_mult)
    scaled_dex = int(dex_mod * (1 + (multiplier - 1) * 0.5) * pandemonium_mult)

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
        "monster_girl": template.get("monster_girl", False),
        "dialogue": template.get("dialogue", {})
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

    # --- Tarnished Jade stat bonuses ---
    from combat.tarnished_jade import get_tarnished_jade_str_bonus, get_tarnished_jade_wis_bonus
    total += get_tarnished_jade_str_bonus(player)
    total += get_tarnished_jade_wis_bonus(player)

    # --- Tarnished Jade Wedge Backlash 50% debuff ---
    if player.get("tarnished_jade_weakened"):
        total = int(total * 0.5)

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

# ── Critical Hit System ─────────────────────────────────────────────────────

import random

CRIT_MULTIPLIER = 1.5


def get_critical_chance(entity, entity_type="player", dex=None, lrn=None):
    """Calculate critical hit chance with diminishing returns and hard caps.

    Formula (Player / Ally):
        Base 5% + min(DEX * 0.003, 8%) + min(LRN * 0.002, 5%)
        Hard cap: 20%

    Formula (Enemy):
        Base 3% + min(DEX * 0.003, 6%)
        Hard cap: 12%

    Optional dex / lrn can be passed in to avoid circular imports for allies.
    """
    if entity_type == "enemy":
        base = 0.03
        dex_val = dex if dex is not None else entity.get("dex_mod", 0)
        dex_bonus = min(dex_val * 0.003, 0.06)
        cap = 0.12
        crit_chance = base + dex_bonus
    else:
        base = 0.05
        if dex is None:
            dex = get_effective_attribute(entity, "Dexterity")
        if lrn is None:
            lrn = get_effective_attribute(entity, "Learning")
        dex_bonus = min(dex * 0.003, 0.08)
        lrn_bonus = min(lrn * 0.002, 0.05)
        cap = 0.20
        crit_chance = base + dex_bonus + lrn_bonus

    # Temporary buffs / debuffs that affect crit chance
    for buff in entity.get("active_buffs", []):
        if buff.get("type") == "crit_chance":
            crit_chance += buff.get("value", 0)
    for debuff in entity.get("active_debuffs", []):
        if debuff.get("type") == "crit_chance_down":
            crit_chance -= debuff.get("value", 0)

    return max(0.0, min(crit_chance, cap))


def roll_critical_hit(entity, entity_type="player", dex=None, lrn=None):
    """Roll for a critical hit. Returns (is_crit, crit_chance)."""
    chance = get_critical_chance(entity, entity_type, dex, lrn)
    return random.random() < chance, chance


def apply_critical_damage(damage, is_crit, multiplier=CRIT_MULTIPLIER):
    """Apply critical hit multiplier to damage."""
    if is_crit:
        return int(damage * multiplier)
    return damage


def format_critical_tag(is_crit):
    """Return a combat message tag for critical hits."""
    return " [CRITICAL!]" if is_crit else ""
