# resources/item_generation.py — Compositional equipment grid (Form × Element × Grade)
"""Generation for the compositional item system.

Designs:
  • weapons     — docs/compositional_equipment_design.md (locked 2026-10-18)
  • armor/acc.  — docs/compositional_armor_design.md (locked 2026-10-18)

An equipment piece is composed from:
  Form    — shape + stat template (e.g. Greatsword, Plate Armor, Crown)
  Element — identity: weapon damage / armor or accessory resistance
  Grade   — power tier 1–3 with canonical prefix (Ember / Blaze / Inferno)

Grade effects:
  • weapons:      +2 primary stat, element 1.10 / 1.30 / 1.50, value +0 / +2 / +5
  • armor:        +1 primary stat, res 1.15 / 1.25 / 1.35,      value +0 / +1 / +3
  • accessories:  +1 primary stat, res 1.05 / 1.10 / 1.15,      value +0 / +1 / +2
  • rarity soft ceiling (audit D-N): g1 epic 60% / legendary 15%,
    g2 legendary 40%, g3 unrestricted (demote one step and re-check)

Existing curated equipment is kept (never overwritten) and receives inferred
`grade`/`grade_premium` metadata so caps/values work uniformly. install_grid()
is called at the bottom of resources/items.py.
"""
import random

ELEMENTS = ["fire", "water", "thunder", "wind", "earth", "light", "dark", "physical", "magical"]

# Canonical prefix per element per grade (g1, g2, g3) — blueprint §3a.
ELEMENT_PREFIXES = {
    "physical": ["Iron", "Steel", "Titan"],
    "fire": ["Ember", "Blaze", "Inferno"],
    "water": ["Frost", "Glacier", "Abyssal"],
    "thunder": ["Spark", "Storm", "Tempest"],
    "wind": ["Gale", "Zephyr", "Cyclone"],
    "earth": ["Stone", "Grave", "Bedrock"],
    "light": ["Radiant", "Divine", "Solar"],
    "dark": ["Shadow", "Void", "Nether"],
    "magical": ["Arcane", "Mystic", "Astral"],
}

GRADE_STAT_BONUS = 2
GRADE_ELEMENT = {1: 1.10, 2: 1.30, 3: 1.50}
GRADE_VALUE_PREMIUM = {1: 0, 2: 2, 3: 5}
# Soft rarity ceiling (audit D-N / P1): a rarity rolled above the grade's
# ceiling only survives with the listed probability, otherwise it demotes
# one step and is re-checked. Grade 3 is unrestricted. GRADE_RARITY_CAP is
# kept for legacy callers but no longer restricts any grade.
GRADE_RARITY_CAP = {1: "legendary", 2: "legendary", 3: "legendary"}
GRADE_RARITY_PASS = {
    1: {"epic": 0.60, "legendary": 0.15},
    2: {"legendary": 0.40},
    3: {},
}

# ── Weapon forms ─────────────────────────────────────────────────────────────
# template: base stats (first key is the primary stat and receives grade bonus)
# base:     base damage axis ("physical" or "magical")
WEAPON_FORMS = [
    {"key": "sword", "noun": "Sword", "weapon_type": "sword",
     "scaling": "Strength", "template": {"Strength": 2}, "base": "physical"},
    {"key": "greatsword", "noun": "Greatsword", "weapon_type": "greatsword",
     "scaling": "Strength", "template": {"Strength": 4}, "base": "physical"},
    {"key": "axe", "noun": "Axe", "weapon_type": "axe",
     "scaling": "Strength", "template": {"Strength": 4}, "base": "physical"},
    {"key": "flail", "noun": "Flail", "weapon_type": "flail",
     "scaling": "Strength", "template": {"Strength": 3, "Constitution": 1}, "base": "physical"},
    {"key": "hammer", "noun": "Hammer", "weapon_type": "hammer",
     "scaling": "Strength", "template": {"Strength": 4}, "base": "physical"},
    {"key": "mace", "noun": "Mace", "weapon_type": "mace",
     "scaling": "Strength", "template": {"Strength": 3, "Wisdom": 1}, "base": "physical"},
    {"key": "maul", "noun": "Maul", "weapon_type": "maul",
     "scaling": "Strength", "template": {"Strength": 4, "Constitution": 1}, "base": "physical"},
    {"key": "spear", "noun": "Spear", "weapon_type": "spear",
     "scaling": "Strength", "template": {"Strength": 3, "Dexterity": 1}, "base": "physical"},
    {"key": "halberd", "noun": "Halberd", "weapon_type": "halberd",
     "scaling": "Strength", "template": {"Strength": 4, "Dexterity": 1}, "base": "physical"},
    {"key": "shield", "noun": "Shield", "weapon_type": "shield",
     "scaling": "Constitution", "template": {"Constitution": 3}, "base": "physical",
     "flags": {"scaling_mult": 0.5, "con_defense": True}},
    {"key": "gauntlets", "noun": "Gauntlets", "weapon_type": "gauntlets",
     "scaling": "Constitution", "template": {"Constitution": 2, "Strength": 1}, "base": "physical",
     "flags": {"scaling_mult": 0.5, "con_defense": True}},
    {"key": "dagger", "noun": "Dagger", "weapon_type": "dagger",
     "scaling": "Dexterity", "template": {"Dexterity": 3}, "base": "physical"},
    {"key": "tongue_dagger", "noun": "Tongue Dagger", "weapon_type": "dagger",
     "scaling": "Charisma", "template": {"Charisma": 3, "Dexterity": 2}, "base": "physical"},
    {"key": "blade", "noun": "Blade", "weapon_type": "blade",
     "scaling": "Strength", "template": {"Strength": 4, "Dexterity": 2}, "base": "physical"},
    {"key": "spellblade", "noun": "Spellblade", "weapon_type": "blade",
     "scaling": "Learning", "template": {"Learning": 3, "Wisdom": 2}, "base": "magical"},
    {"key": "rapier", "noun": "Rapier", "weapon_type": "rapier",
     "scaling": "Dexterity", "template": {"Dexterity": 4, "Charisma": 1}, "base": "physical"},
    {"key": "bow", "noun": "Bow", "weapon_type": "bow",
     "scaling": "Dexterity", "template": {"Dexterity": 4}, "base": "physical"},
    {"key": "crossbow", "noun": "Crossbow", "weapon_type": "crossbow",
     "scaling": "Dexterity", "template": {"Dexterity": 3, "Learning": 1}, "base": "physical"},
    {"key": "chakram", "noun": "Chakram", "weapon_type": "chakram",
     "scaling": "Dexterity", "template": {"Dexterity": 3, "Strength": 1}, "base": "physical"},
    {"key": "staff", "noun": "Staff", "weapon_type": "staff",
     "scaling": "Wisdom", "template": {"Wisdom": 4}, "base": "magical"},
    {"key": "greatstaff", "noun": "Greatstaff", "weapon_type": "staff",
     "scaling": "Learning", "template": {"Learning": 4}, "base": "magical"},
    {"key": "wand", "noun": "Wand", "weapon_type": "wand",
     "scaling": "Learning", "template": {"Learning": 2, "Wisdom": 1}, "base": "magical"},
    {"key": "orb", "noun": "Orb", "weapon_type": "orb",
     "scaling": "Learning", "template": {"Learning": 3, "Charisma": 1}, "base": "magical"},
    {"key": "focus_orb", "noun": "Focus Orb", "weapon_type": "orb",
     "scaling": "Wisdom", "template": {"Wisdom": 3, "Learning": 1}, "base": "magical"},
    {"key": "scepter", "noun": "Scepter", "weapon_type": "scepter",
     "scaling": "Wisdom", "template": {"Wisdom": 3, "Charisma": 2}, "base": "magical"},
    {"key": "grimoire", "noun": "Grimoire", "weapon_type": "grimoire",
     "scaling": "Learning", "template": {"Learning": 4}, "base": "magical"},
    {"key": "lute", "noun": "Lute", "weapon_type": "lute",
     "scaling": "Charisma", "template": {"Charisma": 4, "Learning": 1}, "base": "magical"},
    {"key": "harp", "noun": "Harp", "weapon_type": "harp",
     "scaling": "Charisma", "template": {"Charisma": 3, "Dexterity": 2}, "base": "magical"},
    {"key": "bell", "noun": "Bell", "weapon_type": "bell",
     "scaling": "Charisma", "template": {"Charisma": 3, "Learning": 2}, "base": "magical"},
]

# ── Armor forms (design §3.1) ────────────────────────────────────────────────
# template: base stats (first key = primary stat, +1 per grade)
# entries:  how many resistance entries the form carries
# drawback: includes the element triangle's weakness entry
ARMOR_FORMS = [
    {"key": "padded_armor", "noun": "Padded Armor",
     "template": {"Constitution": 2}, "entries": 2},
    {"key": "chainmail", "noun": "Chainmail",
     "template": {"Constitution": 3}, "entries": 3},
    {"key": "scale_armor", "noun": "Scale Armor",
     "template": {"Constitution": 3, "Strength": 1}, "entries": 3},
    {"key": "banded_mail", "noun": "Banded Mail",
     "template": {"Constitution": 4, "Dexterity": -1}, "entries": 4, "drawback": True},
    {"key": "plate_armor", "noun": "Plate Armor",
     "template": {"Constitution": 5, "Dexterity": -1}, "entries": 4, "drawback": True},
    {"key": "leathers", "noun": "Leathers",
     "template": {"Dexterity": 2, "Constitution": 1}, "entries": 2},
    {"key": "elven_mail", "noun": "Elven Mail",
     "template": {"Dexterity": 3, "Learning": 1}, "entries": 3},
    {"key": "dragonhide", "noun": "Dragonhide",
     "template": {"Constitution": 4, "Dexterity": 2}, "entries": 3},
    {"key": "battle_harness", "noun": "Battle Harness",
     "template": {"Strength": 2, "Constitution": 2}, "entries": 3},
    {"key": "fur_mantle", "noun": "Fur Mantle",
     "template": {"Constitution": 2, "Wisdom": 1}, "entries": 3},
    {"key": "robes", "noun": "Robes",
     "template": {"Learning": 3, "Wisdom": 1}, "entries": 3, "drawback": True},
    {"key": "vestments", "noun": "Vestments",
     "template": {"Learning": 4, "Constitution": 1}, "entries": 3},
    {"key": "regalia", "noun": "Regalia",
     "template": {"Charisma": 4, "Wisdom": 1}, "entries": 3},
    {"key": "silk_garb", "noun": "Silk Garb",
     "template": {"Charisma": 3, "Dexterity": 1}, "entries": 2},
    {"key": "wraps", "noun": "Wraps",
     "template": {"Dexterity": 4, "Charisma": 1}, "entries": 2},
    {"key": "runic_plate", "noun": "Runic Plate",
     "template": {"Constitution": 4, "Learning": 2}, "entries": 5},
]

# element -> (primary resist, secondary resist, drawback) — design §3.2
ARMOR_ELEMENT_TRIANGLE = {
    "fire":     ("fire",     "earth",   "water"),
    "water":    ("water",    "wind",    "thunder"),
    "thunder":  ("thunder",  "wind",    "earth"),
    "wind":     ("wind",     "thunder", "earth"),
    "earth":    ("earth",    "fire",    "wind"),
    "light":    ("light",    "magical", "dark"),
    "dark":     ("dark",     "magical", "light"),
    "magical":  ("magical",  "dark",    "physical"),
    "physical": ("physical", "fire",    "magical"),
}

ARMOR_RES_PRIMARY = {1: 1.15, 2: 1.25, 3: 1.35}
ARMOR_RES_SECONDARY = {1: 1.05, 2: 1.10, 3: 1.15}
ARMOR_RES_DRAWBACK = 0.85
ARMOR_RES_FILLER = 1.05
ARMOR_GRADE_VALUE_PREMIUM = {1: 0, 2: 1, 3: 3}
# Filler order for deep resistance sets; physical first keeps armor familiar.
ARMOR_RES_FILLER_ORDER = [
    "physical", "earth", "fire", "magical", "thunder",
    "wind", "water", "light", "dark",
]

# ── Accessory forms (design §3.3) ────────────────────────────────────────────
# stats: 1 (single-affinity) or 2 (split-affinity); budget: total stat points
ACCESSORY_FORMS = [
    {"key": "ring", "noun": "Ring", "stats": 1, "budget": 3},
    {"key": "band", "noun": "Band", "stats": 2, "budget": 4},
    {"key": "signet", "noun": "Signet", "stats": 1, "budget": 4},
    {"key": "amulet", "noun": "Amulet", "stats": 1, "budget": 3},
    {"key": "pendant", "noun": "Pendant", "stats": 2, "budget": 4},
    {"key": "talisman", "noun": "Talisman", "stats": 2, "budget": 4},
    {"key": "cloak", "noun": "Cloak", "stats": 2, "budget": 3},
    {"key": "bracers", "noun": "Bracers", "stats": 1, "budget": 3},
    {"key": "gloves", "noun": "Gloves", "stats": 2, "budget": 3},
    {"key": "boots", "noun": "Boots", "stats": 1, "budget": 3},
    {"key": "belt", "noun": "Belt", "stats": 2, "budget": 5},
    {"key": "brooch", "noun": "Brooch", "stats": 2, "budget": 4},
    {"key": "crown", "noun": "Crown", "stats": 2, "budget": 6},
    {"key": "tome", "noun": "Tome", "stats": 1, "budget": 3},
    {"key": "earring", "noun": "Earring", "stats": 2, "budget": 3},
    {"key": "monocle", "noun": "Monocle", "stats": 2, "budget": 3},
    {"key": "eye", "noun": "Eye", "stats": 2, "budget": 4},
]

# form key -> (primary stat, secondary stat) — the form's innate affinity.
# Drops are elementless base forms, so the FORM decides which stats an
# uninfused accessory grants. Without this every accessory read Strength /
# Constitution (the physical element affinity). One-stat forms use the first
# entry only; two-stat forms split the budget ceil/floor.
ACCESSORY_FORM_AFFINITY = {
    "ring":     ("Dexterity",),
    "band":     ("Charisma", "Constitution"),
    "signet":   ("Charisma",),
    "amulet":   ("Constitution",),
    "pendant":  ("Wisdom", "Charisma"),
    "talisman": ("Constitution", "Wisdom"),
    "cloak":    ("Dexterity", "Charisma"),
    "bracers":  ("Strength",),
    "gloves":   ("Strength", "Dexterity"),
    "boots":    ("Dexterity",),
    "belt":     ("Constitution", "Strength"),
    "brooch":   ("Charisma", "Dexterity"),
    "crown":    ("Charisma", "Wisdom"),
    "tome":     ("Learning",),
    "earring":  ("Learning", "Charisma"),
    "monocle":  ("Learning", "Wisdom"),
    "eye":      ("Wisdom", "Learning"),
}

# element -> (primary stat, secondary stat) — design §3.3 (infused grid)
ACCESSORY_AFFINITY = {
    "fire":     ("Strength", "Constitution"),
    "water":    ("Constitution", "Dexterity"),
    "thunder":  ("Dexterity", "Strength"),
    "wind":     ("Dexterity", "Charisma"),
    "earth":    ("Constitution", "Strength"),
    "light":    ("Charisma", "Wisdom"),
    "dark":     ("Charisma", "Dexterity"),
    "magical":  ("Learning", "Wisdom"),
    "physical": ("Strength", "Constitution"),
}

# Base accessories carry no elemental protection: early-game defence comes
# from armor. Flowers (infusion) are the way to add resistance later.
ACCESSORY_BASE_RES = {"physical": 1.0}

ACCESSORY_RES_PRIMARY = {1: 1.05, 2: 1.10, 3: 1.15}
ACCESSORY_RES_SECONDARY = {1: 1.00, 2: 1.05, 3: 1.10}
ACCESSORY_GRADE_VALUE_PREMIUM = {1: 0, 2: 1, 3: 2}

# ── Unique form tags (D-J, 2026-10-19) ──────────────────────────────────────
# Uniques keep their hand-tuned stats and specials, but carry a form so they
# participate in the form-perk layer. Ambiguous names map by description.
UNIQUE_FORM_TAGS = {
    # weapons
    "abyss_fang": "blade",
    "cutlass_of_the_captain": "sword",
    "last_oath": "rapier",
    "moonlight_greatsword": "greatsword",
    "certain_someone_black_gloves": "gauntlets",
    "palette_brush": "wand",
    "vorpal_blade_rusted": "blade",
    "vorpal_blade": "blade",
    "woodcutters_broken_axe": "axe",
    "grandmothers_axe": "axe",
    # armor
    "tarnished_jade": "runic_plate",
    "blank_canvas_shawl": "robes",
    "chronoweave_mantle": "elven_mail",
    "decaying_aegis": "runic_plate",
    "old_dopo_robe": "robes",
    # engagement rings + wedding accessories (noun-based)
    "ruby_engagement_ring": "ring",
    "sapphire_engagement_ring": "ring",
    "emerald_engagement_ring": "ring",
    "topaz_engagement_ring": "ring",
    "amethyst_engagement_ring": "ring",
    "diamond_engagement_ring": "ring",
    "wedding_goblin_girl": "ring",
    "wedding_harpy_scout": "earring",
    "wedding_alraune_fledger": "amulet",
    "wedding_kobold_tinkerer": "ring",
    "wedding_dryad_protector": "band",
    "wedding_ghost_maid": "cloak",
    "wedding_centaur_scout": "brooch",
    "wedding_moth_girl_flutterer": "pendant",
    "wedding_slime_girl": "amulet",
    "wedding_lamia_constrictor": "ring",
    "wedding_lizard_queen": "crown",
    "wedding_mimic_girl": "talisman",
    "wedding_umbral_weaver": "ring",
    "wedding_winter_fairy": "talisman",
    "wedding_holstaur_brawler": "signet",
    "wedding_gargoyle_watcher": "amulet",
    "wedding_vampire_seductress": "ring",
    "wedding_yuki_onna": "cloak",
    "wedding_amazon_warrior": "belt",
    "wedding_banshee_wailer": "amulet",
    "wedding_neko_ninja": "earring",
    "wedding_arachne_weaver": "band",
    "wedding_mummy_princess": "band",
    "wedding_oni_bruiser": "ring",
    "wedding_salamander_dancer": "ring",
    "wedding_succubus_seductress": "ring",
    "wedding_dullahan_knight": "signet",
    "wedding_kitsune_miko": "band",
    "wedding_siren_empress": "crown",
    "wedding_crimson_countess": "signet",
    "wedding_demon_whip_master": "belt",
    "wedding_minotaur_gladiator": "signet",
    "wedding_vampire_matriarch": "talisman",
    "wedding_centaur_champion": "ring",
    "wedding_infernal_empress": "signet",
    "wedding_scylla_wrecker": "belt",
    "wedding_gorgon_petrifier": "ring",
    "wedding_ninetales_fox": "band",
    "wedding_mermaid_siren_queen": "ring",
    "wedding_draconic_valkyrie": "signet",
    "wedding_sphinx_riddler": "band",
    "wedding_lich_queen_avatar": "amulet",
    "wedding_valkyrie_commander": "ring",
    "wedding_dragon_goddess_avatar": "crown",
    "wedding_arachne_brood_queen": "cloak",
    "wedding_cosmic_slime_empress": "amulet",
    "wedding_gnome_gear_maiden": "pendant",
    "wedding_orc_war_sister": "belt",
    "wedding_shadow_dusk_weaver": "cloak",
    "wedding_clockwork_automata_doll": "amulet",
    "wedding_giant_maiden_of_stone": "band",
    "wedding_dragonkin_flame_heart": "amulet",
    "wedding_angel_seraph_ascendant": "earring",
    "wedding_fey_star_court_dancer": "ring",
    "wedding_demon_infernal_bride": "band",
    "wedding_undead_grave_queen": "crown",
    "wedding_wonderland_palette": "brooch",
    "wedding_wonderland_dorothy": "amulet",
    "wedding_wonderland_alice": "pendant",
    "wedding_wonderland_red_hood": "talisman",
    "wedding_sylvana": "amulet",
    # special / story accessories (description-based)
    "sky_piercer": "talisman",
    "prescript_ledger": "tome",
    "vileheart_pendant": "pendant",
    "perception_blocking_mask": "eye",
    "chance_and_choice": "talisman",
    "piece_of_relationship": "amulet",
    "silver_slippers": "boots",
    "pocket_watch": "pendant",
    "ruby_slippers": "boots",
    "rose_tinted_crown": "crown",
    "witch_hat": "crown",
    "authors_pen": "tome",
    "no_place_charm": "talisman",
}

_FORM_KEYS_BY_SLOT = {
    "weapon": tuple(f["key"] for f in WEAPON_FORMS),
    "armor": tuple(f["key"] for f in ARMOR_FORMS),
    "accessory": tuple(f["key"] for f in ACCESSORY_FORMS),
}

# Curated (hand-written, non-unique) items whose id suffix does not match a
# form key. Mapped by noun/description so every equipment piece has a form.
CURATED_FORM_TAGS = {
    "stone_plate": "shield",          # "plate" is not a weapon form; it is a shield
    "hook_hand": "dagger",            # Captain's Hook — a hooked sidearm
    "broomstick": "staff",            # Wonderland broom, wielded as a staff
    "blaze_gauntlets": "gloves",      # accessory "Gauntlets" → Gloves form
    "magma_locket": "amulet",
    "cyclone_anklet": "band",
}

UNMAPPED_UNIQUE_FORMS = []

# ── Retired curated generics ─────────────────────────────────────────────
# Non-unique hand-written equipment is retired: grid coordinates are dropped
# and regenerated from their form/element/grade, while the few nouns that are
# not grid coordinates move here so old saves keep working (they no longer
# drop or appear in shops).
LEGACY_ITEMS = {}
RETIRED_GENERIC_IDS = []
_GRID_PREFIXES = {p.lower() for ps in ELEMENT_PREFIXES.values() for p in ps}

# Flowers — one core item per element, used by the blacksmith tempering service.
FLOWER_ITEMS = {
    "physical": "ironbriar",
    "fire": "emberbloom",
    "water": "frostlotus",
    "thunder": "stormlily",
    "wind": "galeorchid",
    "earth": "stonebloom",
    "light": "sunpetal",
    "dark": "nightbloom",
    "magical": "manabloom",
}


def flower_for_element(element):
    """Item id of the flower matching an element (None when unknown)."""
    return FLOWER_ITEMS.get(element)


_FLOWER_IDS = frozenset(FLOWER_ITEMS.values())


def is_flower_item(item):
    """True for a flower stack (older saves lack the ``flower_element`` field)."""
    if not isinstance(item, dict):
        return False
    return bool(item.get("flower_element")) or item.get("id") in _FLOWER_IDS


def pick_flower_id(biome=None, rng=random, enemy_element=None,
                   enemy_share=0.60):
    """Pick a flower id — 60% the enemy's element, 40% biome weights.

    ``enemy_share`` of the time a defeated enemy's own attack element wins
    (so fighting fire creatures feeds fire flowers regardless of region);
    otherwise the biome's element weights decide. Neutral enemies and
    room-cache rewards pass no element and stay purely biome-weighted.
    """
    if enemy_element in FLOWER_ITEMS and rng.random() < enemy_share:
        return FLOWER_ITEMS[enemy_element]
    elements = list(FLOWER_ITEMS)
    weights_map = _element_weights(biome)
    weights = [weights_map.get(el, 1) for el in elements]
    return FLOWER_ITEMS[rng.choices(elements, weights=weights)[0]]


def parse_grid_coordinate(item_id, slot):
    """Return (prefix, form_key) when an id is a grid coordinate, else None."""
    for key in sorted(_FORM_KEYS_BY_SLOT.get(slot, ()), key=len, reverse=True):
        suffix = "_" + key
        if item_id.endswith(suffix):
            prefix = item_id[:-len(suffix)]
            if prefix in _GRID_PREFIXES:
                return prefix, key
    return None


def _retire_curated_generics(items):
    """Move hand-written non-unique equipment out of the live registry."""
    del RETIRED_GENERIC_IDS[:]
    for item_id, data in list(items.items()):
        if data.get("type") != "equipment":
            continue
        if data.get("unique") or data.get("composed"):
            continue
        slot = data.get("slot")
        if slot not in _FORM_KEYS_BY_SLOT:
            continue
        RETIRED_GENERIC_IDS.append(item_id)
        data = items.pop(item_id)
        if parse_grid_coordinate(item_id, slot) is None:
            LEGACY_ITEMS[item_id] = data


def infer_form_key(item_id, slot):
    """Best-effort form key from an item id suffix (longest match wins)."""
    for key in sorted(_FORM_KEYS_BY_SLOT.get(slot, ()), key=len, reverse=True):
        if item_id.endswith("_" + key):
            return key
    return None


def tag_forms(items):
    """Give every equipment definition a ``form`` (live, legacy, unique)."""
    del UNMAPPED_UNIQUE_FORMS[:]
    for source in (items, LEGACY_ITEMS):
        for item_id, data in source.items():
            if data.get("type") != "equipment":
                continue
            slot = data.get("slot")
            if slot not in _FORM_KEYS_BY_SLOT:
                continue
            form = data.get("form")
            if not form:
                form = (UNIQUE_FORM_TAGS.get(item_id)
                        or CURATED_FORM_TAGS.get(item_id)
                        or infer_form_key(item_id, slot))
            if form:
                data["form"] = form
            elif data.get("unique"):
                UNMAPPED_UNIQUE_FORMS.append(item_id)


# ── Regional element weights (docs D-H) ──────────────────────────────────────
ELEMENT_WEIGHTS_BY_BIOME = {
    "tundra": {"water": 3, "wind": 2, "earth": 1},
    "temperate": {el: 1 for el in ELEMENTS},
    "swamp": {"water": 3, "earth": 2, "dark": 2},
    "mountain": {"earth": 3, "physical": 2, "fire": 1},
    "magical": {"magical": 3, "light": 1, "dark": 1, "thunder": 1},
    "celestial": {"light": 3, "wind": 2, "magical": 2, "thunder": 1},
    "volcanic": {"fire": 3, "earth": 2, "dark": 1},
    "forest": {"earth": 2, "wind": 2, "water": 1, "light": 1},
    "savanna": {"fire": 2, "earth": 2, "wind": 2, "physical": 1},
    "coastal": {"water": 3, "wind": 2, "thunder": 2},
    "desert": {"fire": 3, "earth": 2, "wind": 1},
    "tropical": {"water": 2, "earth": 2, "fire": 1, "wind": 1},
    "sea_caves": {"water": 3, "dark": 1, "thunder": 2},
    "pandemonium": {"dark": 3, "fire": 2, "magical": 2},
    "wonderland": {"magical": 2, "light": 2, "dark": 2, "wind": 1},
}

# ── Runtime pools (filled by install_grid) ───────────────────────────────────
_WEAPON_POOLS = {1: {}, 2: {}, 3: {}}      # grade -> element -> [item_id]
_ARMOR_POOLS = {1: {}, 2: {}, 3: {}}
_ACCESSORY_POOLS = {1: {}, 2: {}, 3: {}}
_POOLS = {
    "weapon": _WEAPON_POOLS,
    "armor": _ARMOR_POOLS,
    "accessory": _ACCESSORY_POOLS,
}

SLOT_GRADE_PREMIUM = {
    "weapon": GRADE_VALUE_PREMIUM,
    "armor": ARMOR_GRADE_VALUE_PREMIUM,
    "accessory": ACCESSORY_GRADE_VALUE_PREMIUM,
}

GRADE_BANDS = ((10, 1), (25, 2))
FAMILY_WEIGHTS = {"weapon": 48, "armor": 20, "accessory": 32}
SHOP_GRADE_WEIGHTS = {
    "early": [100, 0, 0],
    "mid": [70, 30, 0],
    "late": [40, 35, 25],
}


def compose_weapon_def(form, element, grade):
    """Build a weapon definition dict for (form, element, grade)."""
    prefix = ELEMENT_PREFIXES[element][grade - 1]
    template = dict(form["template"])
    primary = next(iter(template))
    template[primary] += GRADE_STAT_BONUS * (grade - 1)

    base = form["base"]
    grade_val = GRADE_ELEMENT[grade]
    if element == base:
        elemental = {element: grade_val}
    else:
        elemental = {base: 1.20, element: grade_val}

    data = {
        "name": f"{prefix} {form['noun']}",
        "weapon_type": form["weapon_type"],
        "type": "equipment",
        "slot": "weapon",
        "base_mods": template,
        "scaling_stat": form["scaling"],
        "primary_element": element,
        "elemental_dmg": elemental,
        "grade": grade,
        "grade_premium": GRADE_VALUE_PREMIUM[grade],
        "form": form["key"],
        "composed": True,
    }
    if form.get("flags"):
        data.update(form["flags"])
    return data


def compose_armor_def(form, element, grade):
    """Build an armor definition dict for (form, element, grade)."""
    prefix = ELEMENT_PREFIXES[element][grade - 1]
    template = dict(form["template"])
    primary = next(iter(template))
    template[primary] += grade - 1

    primary_el, secondary_el, drawback_el = ARMOR_ELEMENT_TRIANGLE[element]
    res = {
        primary_el: ARMOR_RES_PRIMARY[grade],
        secondary_el: ARMOR_RES_SECONDARY[grade],
    }
    if form.get("drawback"):
        res.setdefault(drawback_el, ARMOR_RES_DRAWBACK)
    for filler in ARMOR_RES_FILLER_ORDER:
        if len(res) >= form["entries"]:
            break
        res.setdefault(filler, ARMOR_RES_FILLER)
    if len(res) > form["entries"]:
        res = dict(list(res.items())[:form["entries"]])

    return {
        "name": f"{prefix} {form['noun']}",
        "type": "equipment",
        "slot": "armor",
        "base_mods": template,
        "primary_element": element,
        "elemental_res": res,
        "grade": grade,
        "grade_premium": ARMOR_GRADE_VALUE_PREMIUM[grade],
        "form": form["key"],
        "composed": True,
    }


def compose_accessory_def(form, element, grade):
    """Build an accessory definition dict for (form, element, grade)."""
    prefix = ELEMENT_PREFIXES[element][grade - 1]
    primary_stat, secondary_stat = ACCESSORY_AFFINITY[element]

    if form["stats"] >= 2:
        head = (form["budget"] + 1) // 2
        mods = {primary_stat: head, secondary_stat: form["budget"] - head}
        mods = {k: v for k, v in mods.items() if v}
    else:
        mods = {primary_stat: form["budget"]}
    mods[primary_stat] += grade - 1

    primary_el, secondary_el, _ = ARMOR_ELEMENT_TRIANGLE[element]
    res = {primary_el: ACCESSORY_RES_PRIMARY[grade]}
    if grade >= 2:
        res[secondary_el] = ACCESSORY_RES_SECONDARY[grade]

    return {
        "name": f"{prefix} {form['noun']}",
        "type": "equipment",
        "slot": "accessory",
        "base_mods": mods,
        "primary_element": element,
        "elemental_res": res,
        "grade": grade,
        "grade_premium": ACCESSORY_GRADE_VALUE_PREMIUM[grade],
        "form": form["key"],
        "composed": True,
    }


# ── Base forms (canonical catalog, docs/rarity_grade_flower_audit.md §12) ────
# The grade grid above is legacy/dormant one chapter. Everything drops as a
# base form; element and trait progression come from flower infusions.
BASE_FORM_IDS = {"weapon": [], "armor": [], "accessory": []}

# Infusion model constants.
INFUSION_START = 1.10
INFUSION_STEP = 0.05
# Exact per-slot ladders (primary / secondary / tertiary). The primary's last
# step closes the 1.45 -> 1.48 gap called out in the design doc.
WEAPON_SLOT_LADDERS = (
    (1.10, 1.15, 1.20, 1.25, 1.30, 1.35, 1.40, 1.48),
    (1.10, 1.15, 1.20),
    (1.10, 1.15),
)
WEAPON_SLOT_CAPS = tuple(ladder[-1] for ladder in WEAPON_SLOT_LADDERS)
TRAIT_THRESHOLDS = (1.25, 1.35, 1.48)          # trait I / II / III (primary only)
# Weapon display words move at these primary values. Word II starts at the old
# grade-2 element value (1.30), so a 1.25 weapon still reads as tier I; word III
# keeps the 7th-infusion threshold (1.40). Trait tiers remain 1.25/1.35/1.48.
WEAPON_NAME_TIER_THRESHOLDS = (1.30, 1.40)
ARMOR_RES_PRIMARY_TIERS = (1.15, 1.25, 1.35)
ARMOR_RES_SECONDARY_TIERS = (1.05, 1.10, 1.15)
ACCESSORY_RES_PRIMARY_TIERS = (1.05, 1.10, 1.15)
ACCESSORY_RES_SECONDARY_TIERS = (1.00, 1.05, 1.10)
# Armor and accessories use the same three-slot rule as weapons. Each slot
# carries its own three-tier resistance track; the first slot is the piece's
# identity and owns the form drawback. Later slots add coverage and can
# override that weakness.
RES_ELEMENT_SLOTS = 3

PREFIX_TO_ELEMENT = {p.lower(): el for el, prefixes in ELEMENT_PREFIXES.items()
                     for p in prefixes}

# Unique equipment is standardized as one primary element (2026-11-09):
# hand-tuned multi-element profiles are replaced by a single identity element.
# The primary slot is fixed; flowers fill the secondary/tertiary slots (two
# infusions). Unique weapons keep the tier-II value + trait II; armor and
# accessories keep their authored primary resistance/damage values.
UNIQUE_TRAIT_TIER = 2
UNIQUE_ELEMENT_VALUE = 1.35
UNIQUE_FLOWER_SLOTS = 2  # primary is locked; two flower slots remain
# Explicit identities where the highest value is ambiguous or the theme wins.
UNIQUE_PRIMARY_ELEMENTS = {
    "cutlass_of_the_captain": "water",
    "captain_cutlass": "water",  # legacy alias used by older tests/specials
    # Base form is deliberately PHYSICAL; Moonlight is what turns it magical.
    "moonlight_greatsword": "physical",
    # Damage accessories: keep the authored caster identity over ties.
    "authors_pen": "magical",
    "vileheart_pendant": "dark",
    # Resistance-only uniques whose theme beats the ELEMENTS tie-break.
    "chronoweave_mantle": "light",
    "wedding_banshee_wailer": "dark",
    "wedding_mummy_princess": "dark",
    "wedding_lizard_queen": "earth",
    "wedding_cosmic_slime_empress": "water",
    "wedding_dragon_goddess_avatar": "light",
}


# Unique stat budgets (2026-10-20): totals AT +5 enhance, by slot. Base mods
# are normalized to budget − 5×stat_count so the +5 enhance cap lands exactly
# on the budget. Weapons/armor sit near a maxed two-stat base form; accessories
# sit above maxed base accessories. The old hidden +5 compensation is gone.
UNIQUE_STAT_BUDGET = {"weapon": 32, "armor": 33, "accessory": 26}
UNIQUE_ENHANCE_CAP = 5


def normalize_unique_mods(base_mods, slot):
    """Scale a unique's base stats to its slot budget (proportional, integer)."""
    positive = {k: int(v) for k, v in (base_mods or {}).items() if int(v) > 0}
    if not positive:
        return dict(base_mods or {})
    target_total = UNIQUE_STAT_BUDGET.get(slot, 26) - UNIQUE_ENHANCE_CAP * len(positive)
    current_total = sum(positive.values())
    if current_total <= 0 or target_total <= 0:
        return dict(base_mods or {})
    scaled = {k: max(1, int(round(v * target_total / current_total)))
              for k, v in positive.items()}
    keys = list(scaled)
    diff = target_total - sum(scaled.values())
    i = 0
    while diff != 0 and keys:
        key = keys[i % len(keys)]
        if diff > 0:
            scaled[key] += 1
            diff -= 1
        elif scaled[key] > 1:
            scaled[key] -= 1
            diff += 1
        i += 1
    result = dict(base_mods or {})
    result.update(scaled)
    return result


def normalize_unique_stats(items):
    """Apply slot budgets to every unique equipment definition at install."""
    for data in items.values():
        if data.get("type") != "equipment" or not data.get("unique"):
            continue
        slot = data.get("slot")
        if slot in UNIQUE_STAT_BUDGET and data.get("base_mods"):
            data["base_mods"] = normalize_unique_mods(data["base_mods"], slot)


def unique_primary_element(item_id, base_def):
    """Primary element for a unique (explicit map first, then highest).

    Damage profiles win over resistance profiles so caster accessories keep
    their offensive identity (Author's Pen stays magical, Vileheart stays
    dark). Ties resolve by the canonical ELEMENTS order.
    """
    explicit = UNIQUE_PRIMARY_ELEMENTS.get(item_id)
    if explicit:
        return explicit
    for key in ("elemental_dmg", "elemental_res"):
        profile = base_def.get(key) or {}
        best, best_val = None, 0.0
        for element in ELEMENTS:
            value = profile.get(element, 0.0)
            if value > best_val + 1e-9:
                best, best_val = element, value
        if best:
            return best
    return None


def normalize_unique_elements(items):
    """Collapse every unique equipment piece to one primary element.

    Unique gear keeps one identity element in its authored profile; the other
    entries are removed. Flowers (``apply_infusion``) fill the two remaining
    secondary/tertiary slots at the blacksmith, so multi-element uniques are
    built by infusion instead of being handed out fully attuned.
    """
    for item_id, data in items.items():
        if data.get("type") != "equipment" or not data.get("unique"):
            continue
        if data.get("slot") not in ("weapon", "armor", "accessory"):
            continue
        primary = unique_primary_element(item_id, data)
        if not primary:
            continue
        data["primary_element"] = primary
        for key in ("elemental_dmg", "elemental_res"):
            profile = data.get(key)
            if not profile:
                continue
            if primary in profile:
                data[key] = {primary: profile[primary]}
            else:
                data.pop(key, None)


def element_for_prefix(prefix):
    """Map a grid prefix ("ember") back to its element ("fire")."""
    return PREFIX_TO_ELEMENT.get(str(prefix or "").lower())


def armor_res_profile(element, tier, entries, drawback):
    """Resistance triangle for an infused armor element at a 0-based tier."""
    primary_el, secondary_el, drawback_el = ARMOR_ELEMENT_TRIANGLE[element]
    tier = max(0, min(2, int(tier)))
    res = {primary_el: ARMOR_RES_PRIMARY_TIERS[tier],
           secondary_el: ARMOR_RES_SECONDARY_TIERS[tier]}
    if drawback:
        res.setdefault(drawback_el, ARMOR_RES_DRAWBACK)
    for filler in ARMOR_RES_FILLER_ORDER:
        if len(res) >= entries:
            break
        res.setdefault(filler, ARMOR_RES_FILLER)
    return dict(list(res.items())[:entries])


def accessory_res_profile(element, tier):
    """Resistance profile for an infused accessory element at a 0-based tier."""
    primary_el, secondary_el, _ = ARMOR_ELEMENT_TRIANGLE[element]
    tier = max(0, min(2, int(tier)))
    res = {primary_el: ACCESSORY_RES_PRIMARY_TIERS[tier]}
    if tier >= 1:
        res[secondary_el] = ACCESSORY_RES_SECONDARY_TIERS[tier]
    return res


def _res_tier(infusion):
    return max(0, min(2, int(infusion.get("tier", 0))))


def armor_res_profile_multi(infusions, entries, drawback):
    """Merge every infused armor element into one resistance profile.

    Each slot contributes its primary and secondary resistance. Only the
    first slot owns the form's drawback, so extra slots add coverage instead
    of new weaknesses; a resistance from any slot overrides that drawback
    (max merge). The form's entry count grows by one per extra slot.
    """
    if not infusions:
        return armor_res_profile("physical", 0, entries, drawback)
    if len(infusions) == 1:
        inf = infusions[0]
        return armor_res_profile(inf["element"], _res_tier(inf), entries, drawback)

    tiers = []
    for inf in infusions:
        element = inf.get("element")
        if element in ARMOR_ELEMENT_TRIANGLE:
            tiers.append((element, _res_tier(inf)))
    if not tiers:
        return armor_res_profile("physical", 0, entries, drawback)

    res = {}
    # 1. Every slot's primary resistance.
    for element, tier in tiers:
        primary_el = ARMOR_ELEMENT_TRIANGLE[element][0]
        res[primary_el] = max(res.get(primary_el, 0.0),
                              ARMOR_RES_PRIMARY_TIERS[tier])
    # 2. The first slot's drawback, unless another slot resists that element.
    if drawback:
        drawback_el = ARMOR_ELEMENT_TRIANGLE[tiers[0][0]][2]
        res[drawback_el] = max(res.get(drawback_el, 0.0), ARMOR_RES_DRAWBACK)
    # 3. Secondary resistances (one per slot).
    for element, tier in tiers:
        secondary_el = ARMOR_ELEMENT_TRIANGLE[element][1]
        res[secondary_el] = max(res.get(secondary_el, 0.0),
                                ARMOR_RES_SECONDARY_TIERS[tier])
    # 4. Fillers keep the form's entry-count identity; each extra slot adds one.
    max_entries = entries + max(0, len(tiers) - 1)
    for filler in ARMOR_RES_FILLER_ORDER:
        if len(res) >= max_entries:
            break
        res.setdefault(filler, ARMOR_RES_FILLER)
    return dict(list(res.items())[:max_entries])


def accessory_res_profile_multi(infusions):
    """Merge every infused accessory element into one resistance profile.

    Accessories have no drawback: each slot contributes its primary, plus
    its secondary once the slot reaches tier II. A max merge means the best
    value per element wins when two slots overlap.
    """
    if not infusions:
        return dict(ACCESSORY_BASE_RES)
    if len(infusions) == 1:
        inf = infusions[0]
        return accessory_res_profile(inf["element"], _res_tier(inf))

    res = {}
    for inf in infusions:
        element = inf.get("element")
        if element not in ARMOR_ELEMENT_TRIANGLE:
            continue
        tier = _res_tier(inf)
        primary_el, secondary_el, _ = ARMOR_ELEMENT_TRIANGLE[element]
        res[primary_el] = max(res.get(primary_el, 0.0),
                              ACCESSORY_RES_PRIMARY_TIERS[tier])
        if tier >= 1:
            res[secondary_el] = max(res.get(secondary_el, 0.0),
                                    ACCESSORY_RES_SECONDARY_TIERS[tier])
    return res or dict(ACCESSORY_BASE_RES)


def accessory_form_mods(form):
    """Innate stat mods for an accessory form (its thematic affinity)."""
    affinity = ACCESSORY_FORM_AFFINITY.get(
        form["key"], ("Strength", "Constitution"))
    budget = int(form["budget"])
    if form["stats"] >= 2:
        head = (budget + 1) // 2
        mods = {affinity[0]: head, affinity[1]: budget - head}
        return {k: v for k, v in mods.items() if v}
    return {affinity[0]: budget}


def trait_tier_for_value(value, element, base_axis):
    """Primary-slot trait tier (1/2/3) from its multiplier value.

    The form's innate axis keeps trait I even at 1.10 (an uninfused sword
    keeps Sunder); a newly awakened element needs 1.25 for trait I.
    """
    if element == base_axis and value <= INFUSION_START + 1e-9:
        return 1
    for idx, threshold in enumerate(TRAIT_THRESHOLDS, start=1):
        if value >= threshold - 1e-9:
            tier = idx
    return tier if value >= TRAIT_THRESHOLDS[0] - 1e-9 else None


def unique_infusion_axes(base_def):
    """Profile axes a unique's flower slots extend (damage and/or resistance).

    Unique gear keeps the profile it was authored with: weapons and caster
    accessories gain damage, armor and defensive accessories gain resistance,
    and dual-profile accessories gain both. Elementless uniques default to
    resistance, matching ordinary accessories.
    """
    axes = []
    if base_def.get("elemental_dmg"):
        axes.append("dmg")
    if base_def.get("elemental_res"):
        axes.append("res")
    if not axes:
        axes.append("dmg" if base_def.get("slot") == "weapon" else "res")
    return axes


def unique_res_primary_value(slot, tier):
    """Resistance a flower slot adds for its own element (unique gear)."""
    tier = max(0, min(2, int(tier)))
    ladder = (ACCESSORY_RES_PRIMARY_TIERS if slot == "accessory"
              else ARMOR_RES_PRIMARY_TIERS)
    return ladder[tier]


def unique_res_secondary_value(slot, tier):
    """Resistance a flower slot adds for its triangle partner (unique gear)."""
    tier = max(0, min(2, int(tier)))
    ladder = (ACCESSORY_RES_SECONDARY_TIERS if slot == "accessory"
              else ARMOR_RES_SECONDARY_TIERS)
    return ladder[tier]


def refresh_unique_instance(item, base_def):
    """Rebuild a unique instance: one primary element + flower slots.

    The primary element is locked to the authored identity for weapons,
    armor and accessories. ``infusions`` only ever holds the two flower
    slots, so a multi-element unique is rebuilt through flowers instead of
    carrying hand-tuned secondary/tertiary entries. Names, stats and
    specials stay hand-authored; rarity never scales unique stats.
    """
    slot = base_def.get("slot")
    primary = base_def.get("primary_element") or item.get("primary_element")
    enhance = int(item.get("enhance", 0))
    infusions = [dict(i) for i in (item.get("infusions") or [])][:UNIQUE_FLOWER_SLOTS]
    axes = unique_infusion_axes(base_def)

    if base_def.get("unique"):
        item["unique"] = True
    if primary:
        item["primary_element"] = primary

    dmg = dict(base_def.get("elemental_dmg") or {})
    if slot == "weapon" and primary:
        # Unique weapons are standardized to the infusion tier-II value.
        dmg = {primary: UNIQUE_ELEMENT_VALUE}
    res = dict(base_def.get("elemental_res") or {})

    # An elementless unique's first flower claims the primary slot.
    if item.get("primary_infused") and primary:
        if "dmg" in axes and primary not in dmg:
            dmg[primary] = UNIQUE_ELEMENT_VALUE
        if "res" in axes and primary not in res:
            res[primary] = unique_res_primary_value(slot, 0)

    for inf in infusions:
        element = inf.get("element")
        if not element or element == primary or element not in ARMOR_ELEMENT_TRIANGLE:
            continue
        if "dmg" in axes:
            dmg[element] = round(float(inf.get("value", INFUSION_START)), 2)
        if "res" in axes:
            tier = max(0, min(2, int(inf.get("tier", 0))))
            primary_el, secondary_el, _ = ARMOR_ELEMENT_TRIANGLE[element]
            res[primary_el] = max(res.get(primary_el, 0.0),
                                  unique_res_primary_value(slot, tier))
            if slot != "accessory" or tier >= 1:
                res[secondary_el] = max(res.get(secondary_el, 0.0),
                                        unique_res_secondary_value(slot, tier))

    if dmg:
        item["elemental_dmg"] = dmg
    else:
        item.pop("elemental_dmg", None)
    if res:
        item["elemental_res"] = res
    else:
        item.pop("elemental_res", None)

    if slot == "weapon":
        item["trait_tier"] = (base_def.get("trait_tier", UNIQUE_TRAIT_TIER)
                              if primary else None)

    mods = base_def.get("base_mods") or {}
    item["mods"] = {stat: int(val + enhance) for stat, val in mods.items()}
    name = base_def.get("name") or item.get("name", "")
    if enhance > 0:
        name = f"{name} +{enhance}"
    item["name"] = name
    if infusions:
        item["infusions"] = infusions
    else:
        item.pop("infusions", None)
    return item


def refresh_infused_instance(item, base_def):
    """Rebuild an infused instance's element/res profiles and stats in place."""
    from resources.items import compute_equipment_mods

    if base_def.get("unique") or item.get("unique"):
        return refresh_unique_instance(item, base_def)

    slot = base_def.get("slot")
    rarity = item.get("rarity", "common")
    enhance = int(item.get("enhance", 0))
    infusions = [dict(i) for i in (item.get("infusions") or [])]

    if slot == "weapon":
        item["elemental_dmg"] = {inf["element"]: round(inf["value"], 2)
                                  for inf in infusions}
        if not item["elemental_dmg"]:
            item["elemental_dmg"] = dict(base_def.get("elemental_dmg") or {})
        primary_el = infusions[0]["element"] if infusions else base_def.get("primary_element")
        item["primary_element"] = primary_el
        if infusions:
            item["trait_tier"] = trait_tier_for_value(
                infusions[0]["value"], primary_el, base_def.get("primary_element"))
        else:
            item["trait_tier"] = 1  # innate form trait (uninfused)
        item["mods"] = compute_equipment_mods(base_def, rarity, enhance)
    elif slot == "armor":
        if infusions:
            item["primary_element"] = infusions[0]["element"]
            item["elemental_res"] = armor_res_profile_multi(
                infusions,
                base_def.get("form_entries", 3),
                base_def.get("form_drawback", False))
        else:
            item["primary_element"] = base_def.get("primary_element")
            item["elemental_res"] = dict(base_def.get("elemental_res") or {})
        item["mods"] = compute_equipment_mods(base_def, rarity, enhance)
    else:  # accessory
        if infusions:
            item["primary_element"] = infusions[0]["element"]
            item["elemental_res"] = accessory_res_profile_multi(infusions)
        else:
            item["primary_element"] = base_def.get("primary_element")
            item["elemental_res"] = dict(base_def.get("elemental_res") or {})
        # Form affinity is the accessory's identity. Flowers add resistance;
        # they must never rewrite the stats the form was rolled with.
        item["mods"] = compute_equipment_mods(base_def, rarity, enhance)

    item["name"] = infused_item_name(item, base_def)
    return item


def infusion_tier_index(item, base_def):
    """0-based tier index (0..2) of the item's primary infusion, or None.

    Weapon words move with the primary value: word I below 1.30, word II from
    1.30, word III from 1.40 (``WEAPON_NAME_TIER_THRESHOLDS``). Armor and
    accessories store their tier directly (0..2). The tier index answers
    "which word names this piece".
    """
    infusions = item.get("infusions") or []
    if not infusions:
        return None
    first = infusions[0]
    if base_def.get("slot") == "weapon":
        value = float(first.get("value", INFUSION_START))
        if value >= WEAPON_NAME_TIER_THRESHOLDS[1] - 1e-9:
            return 2
        if value >= WEAPON_NAME_TIER_THRESHOLDS[0] - 1e-9:
            return 1
        return 0
    return max(0, min(2, int(first.get("tier", 0))))


def infused_item_name(item, base_def):
    """Display name: [Rarity] [Element tier prefix] Form [+enhance].

    The prefix is the element's flower-tier word — fire reads Ember (I) →
    Blaze (II) → Inferno (III) — so the name tracks infusion investment now
    that grade is retired. Uninfused gear carries no prefix; the tier words
    come from ``ELEMENT_PREFIXES`` (three per element). Uniques keep their
    hand-authored names — flowers never rename a unique.
    """
    if base_def.get("unique") or item.get("unique"):
        name = base_def.get("name") or item.get("name", "")
        enhance = int(item.get("enhance", 0))
        return name + (f" +{enhance}" if enhance > 0 else "")
    rarity = str(item.get("rarity", "common")).title()
    infusions = item.get("infusions") or []
    element_prefix = ""
    tier = infusion_tier_index(item, base_def)
    if infusions and tier is not None:
        prefixes = ELEMENT_PREFIXES.get(infusions[0]["element"])
        if prefixes:
            element_prefix = prefixes[min(tier, len(prefixes) - 1)] + " "
    name = f"{rarity} {element_prefix}{base_def.get('name', '')}".strip()
    enhance = int(item.get("enhance", 0))
    if enhance > 0:
        name += f" +{enhance}"
    return name


def _unique_infusion_entry(element, axes):
    """New flower slot for a unique (damage and/or resistance)."""
    entry = {"element": element}
    if "dmg" in axes:
        entry["value"] = INFUSION_START
    if "res" in axes:
        entry["tier"] = 0
    return entry


def _upgrade_unique_entry(entry, axes, slot_index):
    """Advance one unique flower slot; False when every axis is capped."""
    upgraded = False
    if "dmg" in axes:
        # Unique primary is locked, so the first flower slot is the weapon's
        # secondary ladder and the second is the tertiary ladder.
        ladder = WEAPON_SLOT_LADDERS[
            min(slot_index + 1, len(WEAPON_SLOT_LADDERS) - 1)]
        current = float(entry.get("value", INFUSION_START))
        nxt = next((v for v in ladder if v > current + 1e-9), None)
        if nxt is not None:
            entry["value"] = nxt
            upgraded = True
    if "res" in axes:
        tier = int(entry.get("tier", 0))
        if tier < 2:
            entry["tier"] = tier + 1
            upgraded = True
    return upgraded


def _apply_unique_infusion(item, element, base_def, infusions):
    """Flower infusion for unique gear: primary locked, two open slots."""
    infusions = infusions[:UNIQUE_FLOWER_SLOTS]
    primary = base_def.get("primary_element") or item.get("primary_element")
    if not primary:
        # Elementless flavour unique: the first flower claims its primary.
        item["primary_element"] = element
        item["primary_infused"] = True
        item["infusions"] = infusions
        refresh_infused_instance(item, base_def)
        return True, ""
    if element == primary:
        return False, "primary element is fixed"

    axes = unique_infusion_axes(base_def)
    idx = next((i for i, inf in enumerate(infusions)
                if inf.get("element") == element), None)
    if idx is not None:
        if not _upgrade_unique_entry(infusions[idx], axes, idx):
            return False, "slot at cap"
    elif len(infusions) < UNIQUE_FLOWER_SLOTS:
        infusions.append(_unique_infusion_entry(element, axes))
    else:
        infusions[UNIQUE_FLOWER_SLOTS - 1] = _unique_infusion_entry(element, axes)

    item["infusions"] = infusions
    refresh_infused_instance(item, base_def)
    return True, ""


def apply_infusion(item, element, base_def):
    """Apply one flower infusion to an item instance (no UI / no inventory).

    Returns (ok, reason). Base forms hold up to three element slots
    (primary / secondary / tertiary); armor and accessories hold up to three
    resistance slots, each with its own three-tier track. Uniques keep their
    authored primary element locked and accept flowers only into their two
    remaining secondary/tertiary slots. Same element upgrades its slot; a
    new distinct element fills the next empty slot (or replaces the last when
    every slot is full).
    """
    if element not in FLOWER_ITEMS:
        return False, "unknown element"
    infusions = [dict(i) for i in (item.get("infusions") or [])]

    if base_def.get("unique") or item.get("unique"):
        return _apply_unique_infusion(item, element, base_def, infusions)

    if base_def.get("slot") == "weapon":
        idx = next((i for i, inf in enumerate(infusions) if inf["element"] == element), None)
        if idx is not None:
            ladder = WEAPON_SLOT_LADDERS[idx]
            current = infusions[idx]["value"]
            nxt = next((v for v in ladder if v > current + 1e-9), None)
            if nxt is None:
                return False, "slot at cap"
            infusions[idx]["value"] = nxt
        elif len(infusions) < 3:
            infusions.append({"element": element, "value": INFUSION_START})
        else:
            infusions[2] = {"element": element, "value": INFUSION_START}
    else:
        idx = next((i for i, inf in enumerate(infusions)
                    if inf.get("element") == element), None)
        if idx is not None:
            tier = int(infusions[idx].get("tier", 0))
            if tier >= 2:
                return False, "element at cap"
            infusions[idx] = {"element": element, "tier": tier + 1}
        elif len(infusions) < RES_ELEMENT_SLOTS:
            infusions.append({"element": element, "tier": 0})
        else:
            infusions[RES_ELEMENT_SLOTS - 1] = {"element": element, "tier": 0}

    item["infusions"] = infusions
    refresh_infused_instance(item, base_def)
    return True, ""


def roll_reforge_element(item, slot_index, rng=random):
    """Return a new element for one infusion slot without mutating the item.

    The new element is never the current one and never duplicates another
    slot's element (weapons collapse duplicates in their damage dict).
    """
    infusions = item.get("infusions") or []
    if not (0 <= slot_index < len(infusions)):
        return None
    current = infusions[slot_index].get("element")
    used = {inf.get("element") for i, inf in enumerate(infusions) if i != slot_index}
    if item.get("unique") and item.get("primary_element"):
        # A unique's primary element is locked and cannot be rolled into a
        # secondary/tertiary slot.
        used.add(item.get("primary_element"))
    candidates = [el for el in FLOWER_ITEMS if el != current and el not in used]
    return rng.choice(candidates) if candidates else None


def apply_reforge_element(item, base_def, slot_index, element):
    """Set one infusion slot's element and rebuild the item in place."""
    infusions = [dict(i) for i in (item.get("infusions") or [])]
    if not (0 <= slot_index < len(infusions)) or element not in FLOWER_ITEMS:
        return False
    if item.get("unique") and element == item.get("primary_element"):
        return False
    if any(i != slot_index and inf.get("element") == element
           for i, inf in enumerate(infusions)):
        return False
    infusions[slot_index]["element"] = element
    item["infusions"] = infusions
    refresh_infused_instance(item, base_def)
    return True


def install_base_forms(items):
    """Install the canonical base-form catalog (one item per form)."""
    del BASE_FORM_IDS["weapon"][:]
    del BASE_FORM_IDS["armor"][:]
    del BASE_FORM_IDS["accessory"][:]

    for form in WEAPON_FORMS:
        item_id = form["key"]
        if item_id in items or item_id in LEGACY_ITEMS:
            continue
        template = dict(form["template"])
        data = {
            "name": form["noun"],
            "weapon_type": form["weapon_type"],
            "type": "equipment",
            "slot": "weapon",
            "base_mods": template,
            "scaling_stat": form["scaling"],
            "primary_element": form["base"],
            "elemental_dmg": {form["base"]: INFUSION_START},
            "form": form["key"],
            "base_form": True,
        }
        if form.get("flags"):
            data.update(form["flags"])
        items[item_id] = data
        BASE_FORM_IDS["weapon"].append(item_id)

    for form in ARMOR_FORMS:
        item_id = form["key"]
        if item_id in items or item_id in LEGACY_ITEMS:
            continue
        items[item_id] = {
            "name": form["noun"],
            "type": "equipment",
            "slot": "armor",
            "base_mods": dict(form["template"]),
            "primary_element": "physical",
            "elemental_res": armor_res_profile("physical", 0, form["entries"], form.get("drawback", False)),
            "form": form["key"],
            "form_entries": form["entries"],
            "form_drawback": bool(form.get("drawback")),
            "base_form": True,
        }
        BASE_FORM_IDS["armor"].append(item_id)

    for form in ACCESSORY_FORMS:
        item_id = form["key"]
        if item_id in items or item_id in LEGACY_ITEMS:
            continue
        def_data = {
            "name": form["noun"],
            "type": "equipment",
            "slot": "accessory",
            "base_mods": accessory_form_mods(form),
            "primary_element": "physical",
            "elemental_res": dict(ACCESSORY_BASE_RES),
            "form": form["key"],
            "form_budget": form["budget"],
            "form_stats": form["stats"],
            "base_form": True,
        }
        items[item_id] = def_data
        BASE_FORM_IDS["accessory"].append(item_id)


def _infer_curated_grade(data):
    """Infer grade metadata for a curated weapon (prefix first, stats fallback)."""
    element = data.get("primary_element", "physical")
    first_word = str(data.get("name", "")).split()[0].lower()
    for el, prefixes in ELEMENT_PREFIXES.items():
        if el != element:
            continue
        for idx, prefix in enumerate(prefixes, start=1):
            if first_word == prefix.lower():
                return idx
    stat_sum = sum(int(v) for v in (data.get("base_mods") or {}).values())
    return 1 if stat_sum <= 3 else (2 if stat_sum <= 5 else 3)


def install_grid(items):
    """Retire curated generics, generate the legacy grid, install base forms.

    The grade grid is kept as dormant legacy data for one chapter (old saves
    resolve their ids; nothing drops it). The canonical catalog is the
    base-form set installed at the end — see docs/rarity_grade_flower_audit.md §12.
    """
    _retire_curated_generics(items)

    for item_id, data in items.items():
        if data.get("type") != "equipment":
            continue
        if data.get("unique") or data.get("wonderland_only") or data.get("black_market_only"):
            continue
        slot = data.get("slot")
        if slot not in SLOT_GRADE_PREMIUM:
            continue
        grade = data.setdefault("grade", _infer_curated_grade(data))
        if grade not in SLOT_GRADE_PREMIUM[slot]:
            grade = data["grade"] = 1
        data.setdefault("grade_premium", SLOT_GRADE_PREMIUM[slot][grade])
        element = data.get("primary_element", "physical")
        _POOLS[slot][grade].setdefault(element, []).append(item_id)

    for form in WEAPON_FORMS:
        for element in ELEMENTS:
            for grade in (1, 2, 3):
                prefix = ELEMENT_PREFIXES[element][grade - 1]
                item_id = f"{prefix.lower()}_{form['key']}"
                if item_id in items or item_id in LEGACY_ITEMS:
                    continue  # curated/legacy item wins
                items[item_id] = compose_weapon_def(form, element, grade)
                _WEAPON_POOLS[grade].setdefault(element, []).append(item_id)

    for slot, forms, composer in (
        ("armor", ARMOR_FORMS, compose_armor_def),
        ("accessory", ACCESSORY_FORMS, compose_accessory_def),
    ):
        pools = _POOLS[slot]
        for form in forms:
            for element in ELEMENTS:
                for grade in (1, 2, 3):
                    prefix = ELEMENT_PREFIXES[element][grade - 1]
                    item_id = f"{prefix.lower()}_{form['key']}"
                    if item_id in items or item_id in LEGACY_ITEMS:
                        continue  # curated/legacy item wins
                    items[item_id] = composer(form, element, grade)
                    pools[grade].setdefault(element, []).append(item_id)

    install_base_forms(items)
    normalize_unique_stats(items)
    normalize_unique_elements(items)
    tag_forms(items)


# ── Pickers ──────────────────────────────────────────────────────────────────
# Equipment drops are elementless base forms (§12): form is the only roll, and
# elements/traits come from flower infusions. The grade arguments are kept so
# existing call sites stay source-compatible; they are intentionally ignored.

def grade_for_level(level):
    """Deprecated: grade bands are gone. Kept for legacy callers/tests."""
    return 1


def roll_shop_grade(tier, rng=random):
    """Deprecated: grade bands are gone. Kept for legacy callers."""
    return 1


def _element_weights(biome):
    return ELEMENT_WEIGHTS_BY_BIOME.get(biome or "", {el: 1 for el in ELEMENTS})


# Dungeon/city form identity (weapons doc §10, folded into the flower rework).
# Preferred forms are 3x more likely in their biome; everything stays possible.
FORM_WEIGHTS_BY_BIOME = {
    "tundra": ("spear", "crossbow", "greatstaff", "harp"),
    "temperate": ("sword", "greatsword", "shield", "bow"),
    "swamp": ("dagger", "tongue_dagger", "mace", "orb"),
    "mountain": ("hammer", "maul", "shield", "halberd",
                 "plate_armor", "chainmail", "scale_armor"),
    "magical": ("staff", "greatstaff", "grimoire", "orb",
                "robes", "vestments", "runic_plate", "tome", "crown"),
    "celestial": ("staff", "greatstaff", "grimoire", "crown",
                  "regalia", "vestments", "robes", "monocle"),
    "volcanic": ("axe", "hammer", "flail", "greatsword",
                 "plate_armor", "banded_mail", "battle_harness"),
    "forest": ("bow", "spear", "dagger", "lute",
               "leathers", "elven_mail", "silk_garb"),
    "savanna": ("spear", "chakram", "axe", "rapier"),
    "coastal": ("rapier", "crossbow", "orb", "harp"),
    "desert": ("axe", "chakram", "spear", "wand", "wraps", "leathers"),
    "tropical": ("dagger", "bow", "chakram", "bell", "silk_garb", "wraps"),
    "sea_caves": ("spear", "dagger", "orb", "wand"),
    "pandemonium": ("tongue_dagger", "axe", "flail", "grimoire",
                    "runic_plate", "regalia"),
    "wonderland": ("rapier", "wand", "lute", "bell", "regalia", "crown", "monocle"),
}


def _pick_base_form(slot, biome=None, rng=random):
    ids = BASE_FORM_IDS.get(slot) or []
    if not ids:
        return None
    preferred = set(FORM_WEIGHTS_BY_BIOME.get(biome or "", ()))
    weights = [3 if item_id in preferred else 1 for item_id in ids]
    return rng.choices(ids, weights=weights)[0]


def biome_craft_hint(biome, limit=6):
    """Comma list of the forms this biome favours (3x drop weight), or "".

    Used by the dungeon header so the regional craft signature is visible in
    play instead of only existing in data.
    """
    keys = FORM_WEIGHTS_BY_BIOME.get(biome or "", ())
    if not keys:
        return ""
    from resources.items import ITEMS
    names = []
    for key in keys[:limit]:
        name = (ITEMS.get(key) or {}).get("name") or key.replace("_", " ").title()
        if name not in names:
            names.append(name)
    if not names:
        return ""
    if len(names) == 1:
        return names[0]
    return ", ".join(names[:-1]) + " and " + names[-1]


def pick_weapon_id(grade=None, biome=None, rng=random):
    """Pick a base weapon form (grade arg is legacy; biome biases the form)."""
    return _pick_base_form("weapon", biome, rng) or "sword"


def pick_family_id(family, grade=None, biome=None, rng=random):
    """Pick a base armor/accessory form (grade arg is legacy; biome biases)."""
    if family not in ("armor", "accessory"):
        family = "armor"
    return _pick_base_form(family, biome, rng) or ("padded_armor" if family == "armor" else "ring")


def pick_equipment_id(level=None, biome=None, rng=random):
    """Pick any base equipment form (level arg is legacy; biome biases)."""
    family = rng.choices(list(FAMILY_WEIGHTS), weights=list(FAMILY_WEIGHTS.values()))[0]
    if family == "weapon":
        return pick_weapon_id(biome=biome, rng=rng)
    return pick_family_id(family, biome=biome, rng=rng)


def player_biome(player):
    """Best-effort biome for the player's current location (None if unknown)."""
    try:
        from leveling import get_current_city_id
        from resources.cities import CITIES
        city = CITIES.get(get_current_city_id(player), {})
        return city.get("biome")
    except Exception:
        return None


def dungeon_biome(player):
    """Biome for loot rolled INSIDE a dungeon run (audit P4).

    City-floor runs set ``dungeon_region`` from the city biome, so this is
    usually identical to ``player_biome``. Wild dungeons and world-map ruins
    set it to their own biome, while ``player_biome`` still resolves the
    origin city — dungeon loot must follow the run, not the city.
    """
    if player.get("pandemonium_mode"):
        return "pandemonium"
    return player.get("dungeon_region") or player_biome(player)
