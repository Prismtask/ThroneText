"""Form perks — static, always-on modifiers granted by equipped equipment forms.

Design: docs/compositional_equipment_design.md §6.1 (D-G, proposal v2 2026-10-19).

Rules
-----
* One perk per equipped piece: weapon, armor, accessory1, accessory2 and —
  only when the actor has consumed the Beating Root (``acc3_unlocked``) —
  accessory3.  That is 4 active perks by default, 5 with the Root.
* Perks are form-level: every item of the same form grants the same perk,
  regardless of grade, rarity, enhancement or whether it is composed,
  curated or unique.
* Identical archetypes stack additively across slots.
* Perks never scale with grade/rarity/enhance and never appear in item value.

Elements own procs (Sunder/Ignite/Chain/...); forms own these static modifiers.
"""
import math

# Slot groups — weapons/armor/accessories have separate form namespaces.
SLOT_GROUPS = {
    "weapon": "weapon",
    "armor": "armor",
    "accessory": "accessory",
    "accessory1": "accessory",
    "accessory2": "accessory",
    "accessory3": "accessory",
}

PERK_NAMES = {
    "crit_chance": "Keen",
    "crit_damage": "Brutal",
    "damage_dealt": "Cleaving",
    "armor_pen": "Sundering",
    "damage_reduction": "Guarded",
    "evasion": "Nimble",
    "initiative": "Swift",
    "magical_damage": "Focused",
    "healing": "Mending",
    "res_rating": "Steadfast",
}

# slot group -> form key -> (perk type, value)
FORM_PERKS = {
    "weapon": {
        "sword": ("crit_chance", 0.05),
        "greatsword": ("damage_dealt", 0.10),
        "axe": ("crit_damage", 0.15),
        "flail": ("damage_dealt", 0.08),
        "hammer": ("armor_pen", 0.10),
        "mace": ("armor_pen", 0.10),
        "maul": ("damage_dealt", 0.10),
        "spear": ("initiative", 2.0),
        "halberd": ("armor_pen", 0.12),
        "shield": ("damage_reduction", 0.08),
        "gauntlets": ("damage_reduction", 0.06),
        "dagger": ("crit_chance", 0.10),
        "tongue_dagger": ("crit_damage", 0.15),
        "blade": ("damage_dealt", 0.08),
        "spellblade": ("magical_damage", 0.08),
        "rapier": ("crit_chance", 0.08),
        "bow": ("crit_chance", 0.08),
        "crossbow": ("armor_pen", 0.10),
        "chakram": ("initiative", 2.0),
        "staff": ("magical_damage", 0.08),
        "greatstaff": ("magical_damage", 0.10),
        "wand": ("magical_damage", 0.06),
        "orb": ("magical_damage", 0.08),
        "focus_orb": ("healing", 0.10),
        "scepter": ("healing", 0.08),
        "grimoire": ("magical_damage", 0.10),
        "lute": ("healing", 0.10),
        "harp": ("healing", 0.08),
        "bell": ("initiative", 2.0),
    },
    "armor": {
        "padded_armor": ("evasion", 0.03),
        "chainmail": ("damage_reduction", 0.04),
        "scale_armor": ("damage_reduction", 0.04),
        "banded_mail": ("damage_reduction", 0.05),
        "plate_armor": ("damage_reduction", 0.06),
        "leathers": ("evasion", 0.04),
        "elven_mail": ("evasion", 0.04),
        "dragonhide": ("res_rating", 0.05),
        "battle_harness": ("damage_reduction", 0.03),
        "fur_mantle": ("healing", 0.05),
        "robes": ("magical_damage", 0.06),
        "vestments": ("healing", 0.06),
        "regalia": ("magical_damage", 0.04),
        "silk_garb": ("evasion", 0.05),
        "wraps": ("evasion", 0.04),
        "runic_plate": ("damage_reduction", 0.05),
    },
    "accessory": {
        "ring": ("crit_chance", 0.04),
        "band": ("crit_damage", 0.06),
        "signet": ("crit_chance", 0.04),
        "amulet": ("res_rating", 0.04),
        "pendant": ("healing", 0.04),
        "talisman": ("evasion", 0.03),
        "cloak": ("evasion", 0.04),
        "bracers": ("damage_reduction", 0.03),
        "gloves": ("crit_chance", 0.04),
        "boots": ("initiative", 1.0),
        "belt": ("damage_reduction", 0.03),
        "brooch": ("healing", 0.04),
        "crown": ("magical_damage", 0.04),
        "tome": ("magical_damage", 0.04),
        "earring": ("initiative", 1.0),
        "monocle": ("crit_chance", 0.04),
        "eye": ("crit_chance", 0.04),
    },
}


# ── Resolution ──────────────────────────────────────────────────────────────

def _slots(entity):
    """Equipped slots that contribute a perk (accessory3 needs the Root)."""
    equipped = entity.get("equipped")
    if not isinstance(equipped, dict):
        return ()
    slots = ["weapon", "armor", "accessory1", "accessory2"]
    if entity.get("acc3_unlocked"):
        slots.append("accessory3")
    return [s for s in slots if equipped.get(s)]


def _item_form(item):
    """Form key for an item instance (old instances fall back to the template)."""
    if not isinstance(item, dict):
        return None
    form = item.get("form")
    if form:
        return form
    item_id = item.get("id")
    if item_id:
        from resources.items import ITEMS
        return (ITEMS.get(item_id) or {}).get("form")
    return None


def get_item_form_perk(item, slot=None):
    """(perk type, value) for a single item, or None.

    ``slot`` is the equipment slot the item occupies. When given, the item's
    own ``slot`` must belong to the same group (a ring in the weapon slot
    grants nothing).
    """
    form = _item_form(item)
    if not form:
        return None
    group = SLOT_GROUPS.get(item.get("slot"))
    if not group:
        return None
    if slot is not None and SLOT_GROUPS.get(slot) != group:
        return None
    return FORM_PERKS.get(group, {}).get(form)


def get_form_perk_bonus(entity, perk_type):
    """Total additive value of ``perk_type`` from every equipped slot."""
    if not isinstance(entity, dict):
        return 0.0
    total = 0.0
    equipped = entity.get("equipped") or {}
    for slot in _slots(entity):
        perk = get_item_form_perk(equipped[slot], slot)
        if perk and perk[0] == perk_type:
            total += perk[1]
    return total


def get_form_crit_chance_bonus(entity):
    return get_form_perk_bonus(entity, "crit_chance")


def get_form_crit_damage_bonus(entity):
    return get_form_perk_bonus(entity, "crit_damage")


def get_form_damage_reduction(entity):
    return min(0.75, get_form_perk_bonus(entity, "damage_reduction"))


def get_form_evasion(entity):
    return get_form_perk_bonus(entity, "evasion")


def get_form_initiative(entity):
    return get_form_perk_bonus(entity, "initiative")


def get_form_healing_bonus(entity):
    return get_form_perk_bonus(entity, "healing")


def get_form_res_rating_bonus(entity, element):
    """Steadfast: +rating to the item's own primary element only."""
    if not isinstance(entity, dict) or not element:
        return 0.0
    total = 0.0
    equipped = entity.get("equipped") or {}
    for slot in _slots(entity):
        item = equipped[slot]
        perk = get_item_form_perk(item, slot)
        if perk and perk[0] == "res_rating" and item.get("primary_element") == element:
            total += perk[1]
    return total


def _weapon_is_magical(entity):
    weapon = (entity.get("equipped") or {}).get("weapon") or {}
    return "magical" in (weapon.get("elemental_dmg") or {})


def get_outgoing_damage_multiplier(entity):
    """Cleaving (+% damage) and Focused (+% magical damage) combined."""
    if not isinstance(entity, dict):
        return 1.0
    mult = 1.0 + get_form_perk_bonus(entity, "damage_dealt")
    if _weapon_is_magical(entity):
        mult += get_form_perk_bonus(entity, "magical_damage")
    return mult


def get_armor_pen_multiplier(entity, pre_dmg=None):
    """Multiplier applied to enemy armour (1.0 = none, lower = more pen)."""
    mult = pre_dmg.get("armor_pen", 1.0) if isinstance(pre_dmg, dict) else 1.0
    perk = get_form_perk_bonus(entity, "armor_pen")
    if perk:
        mult *= max(0.0, 1.0 - perk)
    return mult


# ── Display ────────────────────────────────────────────────────────────────

def describe_perk(perk, element=None):
    """Human-readable perk line, e.g. 'Keen: +5% critical chance'."""
    if not perk:
        return ""
    perk_type, value = perk
    name = PERK_NAMES.get(perk_type, "Tradition")
    if perk_type == "initiative":
        text = f"+{int(value)} initiative"
    elif perk_type == "res_rating":
        el = f" {element}" if element else ""
        text = f"+{value:.2f}{el} resistance"
    else:
        text = f"+{int(math.floor(value * 100 + 0.5))}% " + {
            "crit_chance": "critical chance",
            "crit_damage": "critical damage",
            "damage_dealt": "damage dealt",
            "armor_pen": "armour penetration",
            "damage_reduction": "damage reduction",
            "evasion": "dodge",
            "magical_damage": "magical damage",
            "healing": "healing",
        }.get(perk_type, "")
    return f"{name}: {text}"


def describe_item_perk(item):
    """Perk line for an item instance/definition ('' when it has no form)."""
    if not isinstance(item, dict):
        return ""
    perk = get_item_form_perk(item)
    if not perk:
        return ""
    return describe_perk(perk, element=item.get("primary_element"))
