import re

# combat/elemental.py – Elemental damage/resistance system
"""Dynamic elemental / type system. Every entity has elemental_res and elemental_dmg.

Includes the 7 classic elements (fire, water, thunder, wind, earth, light, dark)
plus two damage-type axes:
  physical  – melee/weapon-based damage
  magical   – spell/arcane-based damage

res  > 1.0 = resistant (takes less damage)   ← rating: higher = stronger
res  = 1.0 = neutral
res  < 1.0 = weak (takes more damage)
Damage-taken multiplier = 2.0 - res, clamped to [0.0, 2.0]
(e.g. res 1.3 → ×0.7, res 0.7 → ×1.3).

dmg  < 1.0 = weak output with that element/type
dmg  = 1.0 = neutral
dmg  > 1.0 = strong output with that element/type
"""

ELEMENTS = ["fire", "water", "thunder", "wind", "earth", "light", "dark", "physical", "magical"]


def resistance_multiplier(rating):
    """Convert a resistance rating (higher = stronger) to a damage-taken multiplier.

    Ratings are authored around 1.0 (neutral). The multiplier is ``2.0 - rating``
    clamped to [0.0, 2.0]: 1.3 → ×0.7 (30% resistance), 0.7 → ×1.3 (30% weakness).
    Rounded to 4 decimals to keep float noise (e.g. 2 - 1.8) from truncating damage.
    """
    mult = max(0.0, min(2.0, 2.0 - float(rating)))
    return round(mult, 4)


def get_damage_element(profile):
    """Return the single element a creature attacks with, or None if neutral.

    Every attack resolves against exactly ONE element — skills carry their own
    YAML ``elemental`` and basic attacks read ``get_attack_element``; the
    profile only supplies that element's multiplier. Extra >1.0 entries in a
    damage profile therefore never contribute to damage. Enemy AI, the
    elemental-debuff channel and the single-element enemy profile all use this
    picker so they can never disagree. Ties resolve to ``ELEMENTS`` order
    (fire → water → thunder → wind → earth → light → dark → physical → magical).
    """
    best_el = None
    best_val = 1.0
    for el in ELEMENTS:
        val = profile.get(el, 1.0)
        if val > best_val:
            best_val = val
            best_el = el
    return best_el


# ── Keyword-based elemental specialisation ─────────────────────────────────
# When an enemy/ally name contains one of these keywords (case-insensitive),
# the corresponding elemental_dmg and elemental_res overrides are applied on
# top of the racial profile.  This lets "Lightning Orb" feel like thunder
# even though its race (Elemental) is generic.
#
# Format: keyword_lowercase → {"elemental_dmg": {...}, "elemental_res": {...}}
# Values follow the same convention: >1.0 = stronger resistance/output, <1.0 = weaker.

ELEMENTAL_KEYWORDS = {
    # ── Thunder / Lightning ──
    "lightning": {
        "elemental_dmg": {"thunder": 1.4, "water": 1.1},
        "elemental_res": {"thunder": 1.3, "earth": 0.7},
    },
    "thunder": {
        "elemental_dmg": {"thunder": 1.4},
        "elemental_res": {"thunder": 1.3, "earth": 0.7},
    },
    "plasma": {
        "elemental_dmg": {"thunder": 1.3, "fire": 1.2},
        "elemental_res": {"thunder": 1.3, "fire": 1.2, "water": 0.7},
    },

    # ── Fire / Flame / Magma ──
    "flame": {
        "elemental_dmg": {"fire": 1.4},
        "elemental_res": {"fire": 1.3, "water": 0.7},
    },
    "magma": {
        "elemental_dmg": {"fire": 1.3, "earth": 1.2},
        "elemental_res": {"fire": 1.3, "earth": 1.2, "water": 0.7},
    },
    "fire": {
        "elemental_dmg": {"fire": 1.4},
        "elemental_res": {"fire": 1.3, "water": 0.7},
    },

    # ── Water / Frost / Ice ──
    "frost": {
        "elemental_dmg": {"water": 1.4},
        "elemental_res": {"water": 1.3, "fire": 0.7},
    },
    "ice": {
        "elemental_dmg": {"water": 1.4},
        "elemental_res": {"water": 1.3, "fire": 0.7},
    },
    "water": {
        "elemental_dmg": {"water": 1.3},
        "elemental_res": {"water": 1.3, "thunder": 0.7},
    },

    # ── Wind / Storm ──
    "storm": {
        "elemental_dmg": {"wind": 1.3, "thunder": 1.3},
        "elemental_res": {"wind": 1.2, "thunder": 1.2, "earth": 0.7},
    },
    "wind": {
        "elemental_dmg": {"wind": 1.4},
        "elemental_res": {"wind": 1.3, "earth": 0.7},
    },

    # ── Earth / Stone / Crystal ──
    "earth": {
        "elemental_dmg": {"earth": 1.4},
        "elemental_res": {"earth": 1.3, "wind": 0.7},
    },
    "stone": {
        "elemental_dmg": {"earth": 1.4},
        "elemental_res": {"earth": 1.3, "wind": 0.7},
    },
    "crystal": {
        "elemental_dmg": {"earth": 1.3, "light": 1.1},
        "elemental_res": {"earth": 1.3, "light": 1.2, "dark": 0.7},
    },

    # ── Dark / Shadow / Void / Abyss ──
    "abyss": {
        "elemental_dmg": {"dark": 1.5},
        "elemental_res": {"dark": 1.4, "light": 0.6},
    },
    "abyssal": {
        "elemental_dmg": {"dark": 1.5},
        "elemental_res": {"dark": 1.4, "light": 0.6},
    },
    "void": {
        "elemental_dmg": {"dark": 1.4},
        "elemental_res": {"dark": 1.3, "light": 0.6},
    },
    "shadow": {
        "elemental_dmg": {"dark": 1.4},
        "elemental_res": {"dark": 1.3, "light": 0.6},
    },
    "dark": {
        "elemental_dmg": {"dark": 1.4},
        "elemental_res": {"dark": 1.3, "light": 0.7},
    },
    "darkness": {
        "elemental_dmg": {"dark": 1.4},
        "elemental_res": {"dark": 1.3, "light": 0.6},
    },

    # ── Light / Holy / Radiant ──
    "holy": {
        "elemental_dmg": {"light": 1.4},
        "elemental_res": {"light": 1.3, "dark": 0.6},
    },
    "radiant": {
        "elemental_dmg": {"light": 1.4},
        "elemental_res": {"light": 1.3, "dark": 0.6},
    },
    "light": {
        "elemental_dmg": {"light": 1.4},
        "elemental_res": {"light": 1.3, "dark": 0.7},
    },

    # ── Physical / Brute Force ──
    "brute": {
        "elemental_dmg": {"physical": 1.4},
        "elemental_res": {"physical": 1.3, "magical": 0.7},
    },
    "savage": {
        "elemental_dmg": {"physical": 1.4},
        "elemental_res": {"physical": 1.3, "magical": 0.7},
    },
    "iron": {
        "elemental_dmg": {"physical": 1.3},
        "elemental_res": {"physical": 1.3, "magical": 0.8},
    },
    "steel": {
        "elemental_dmg": {"physical": 1.4},
        "elemental_res": {"physical": 1.3, "magical": 0.8},
    },
    "blade": {
        "elemental_dmg": {"physical": 1.3},
        "elemental_res": {"magical": 0.85},
    },

    # ── Magical / Arcane ──
    "arcane": {
        "elemental_dmg": {"magical": 1.4},
        "elemental_res": {"magical": 1.3, "physical": 0.7},
    },
    "sorcerer": {
        "elemental_dmg": {"magical": 1.4},
        "elemental_res": {"magical": 1.3, "physical": 0.7},
    },
    "sorceress": {
        "elemental_dmg": {"magical": 1.4},
        "elemental_res": {"magical": 1.3, "physical": 0.7},
    },
    "wizard": {
        "elemental_dmg": {"magical": 1.4},
        "elemental_res": {"magical": 1.3, "physical": 0.7},
    },
    "witch": {
        "elemental_dmg": {"magical": 1.4},
        "elemental_res": {"magical": 1.3, "physical": 0.7},
    },
    "mage": {
        "elemental_dmg": {"magical": 1.4},
        "elemental_res": {"magical": 1.3, "physical": 0.7},
    },
    "enchant": {
        "elemental_dmg": {"magical": 1.3},
        "elemental_res": {"magical": 1.3, "physical": 0.8},
    },
    "runic": {
        "elemental_dmg": {"magical": 1.3},
        "elemental_res": {"magical": 1.3, "physical": 0.75},
    },
    "mystic": {
        "elemental_dmg": {"magical": 1.3},
        "elemental_res": {"magical": 1.3, "physical": 0.8},
    },
}


# Name hints for neutral enemies (the Human race has no elemental profile):
# caster-flavoured names attack magically, every other neutral enemy
# attacks physically. Whole-word matches avoid "mage" inside other words.
CASTER_NAME_HINTS = (
    "mage", "wizard", "witch", "sorcerer", "sorceress", "warlock",
    "cultist", "priest", "priestess", "cleric", "acolyte", "enchanter",
    "enchantress", "necromancer", "summoner", "oracle", "seer", "diviner",
    "mystic", "arcane", "runic", "spellcaster", "spell",
)

# Baseline multiplier for the fallback attack type. Kept low: this is a
# natural damage-type trait, not a specialisation like race profiles (1.2-1.5).
DEFAULT_ATTACK_MULTIPLIER = 1.2


def _default_attack_element(name):
    """Fallback damage type for an enemy with no elemental profile.

    Human enemies use this: caster names (Novice Mage, Cultist, ...) attack
    magically; martial names (Bandit, Elite Assassin, ...) attack physically.
    """
    lower = (name or "").lower()
    for hint in CASTER_NAME_HINTS:
        if re.search(r'\b' + re.escape(hint) + r'\b', lower):
            return "magical"
    return "physical"


def _get_keyword_elemental(name):
    """Check an entity name for known elemental keywords (whole-word match).
    
    Returns (elemental_dmg dict, elemental_res dict) with values to merge
    on top of the racial profile.
    """
    if not name:
        return {}, {}
    lower = name.lower()
    dmg = {}
    res = {}
    for keyword, profile in ELEMENTAL_KEYWORDS.items():
        # Use word-boundary regex so "light" doesn't match inside "lightning"
        if re.search(r'\b' + re.escape(keyword) + r'\b', lower):
            for el, val in profile.get("elemental_dmg", {}).items():
                # Take the highest dmg override if multiple keywords match
                dmg[el] = max(dmg.get(el, 1.0), val)
            for el, val in profile.get("elemental_res", {}).items():
                # For res, take the most extreme (furthest from 1.0)
                existing = res.get(el, 1.0)
                if abs(val - 1.0) > abs(existing - 1.0):
                    res[el] = val
    return dmg, res


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
    """Compute enemy's total elemental profile from race + keyword + individual overrides."""
    from resources.enemies import ENEMIES, ENEMY_RACES
    
    key = enemy.get("key")
    if key:
        template = ENEMIES.get(key, {})
        race_name = template.get("race", "Human")
        enemy_name = template.get("name", enemy.get("name", ""))
    else:
        template = {}
        race_name = "Human"
        enemy_name = enemy.get("name", "")
    
    race_data = ENEMY_RACES.get(race_name, {})
    
    res = merge_profiles(neutral_profile(), race_data.get("elemental_res", {}))
    dmg = merge_profiles(neutral_profile(), race_data.get("elemental_dmg", {}))
    
    # Apply keyword-based specialisation (e.g. "Lightning Orb" → thunder)
    kw_dmg, kw_res = _get_keyword_elemental(enemy_name)
    res = merge_profiles(res, kw_res)
    dmg = merge_profiles(dmg, kw_dmg)
    
    # Apply individual overrides from enemy template (highest priority)
    res = merge_profiles(res, template.get("elemental_res", {}))
    dmg = merge_profiles(dmg, template.get("elemental_dmg", {}))
    
    # Enemies attack with exactly one element (AI + debuff proc both read the
    # single highest entry), so report only that entry. Secondary >1.0 values
    # never contributed to damage — they only made profiles advertise
    # multi-element output. Resistances intentionally stay multi-element.
    element = get_damage_element(dmg)
    if element is None:
        # Natural fallback: neutral races (Human) and custom enemies still
        # get a physical/magical attack trait instead of a blank HUD tag.
        element = _default_attack_element(enemy_name)
        dmg[element] = DEFAULT_ATTACK_MULTIPLIER
    dmg = {element: round(dmg[element], 4)} if element else {}

    return res, dmg


def compute_ally_elemental(ally):
    """Compute ally's total elemental profile from enemy race + keyword + equipment."""
    from resources.enemies import ENEMIES, ENEMY_RACES
    
    key = ally.get("key")
    if key:
        template = ENEMIES.get(key, {})
        race_name = template.get("race", "Human")
        ally_name = template.get("name", ally.get("name", ""))
    else:
        race_name = "Human"
        ally_name = ally.get("name", "")
    
    race_data = ENEMY_RACES.get(race_name, {})
    
    base_res = merge_profiles(neutral_profile(), race_data.get("elemental_res", {}))
    base_dmg = merge_profiles(neutral_profile(), race_data.get("elemental_dmg", {}))
    
    # Apply keyword-based specialisation
    kw_dmg, kw_res = _get_keyword_elemental(ally_name)
    base_res = merge_profiles(base_res, kw_res)
    base_dmg = merge_profiles(base_dmg, kw_dmg)

    # Race passive elemental modifiers (Dragonkin, Demon, Elemental, Gnome)
    from combat.ally_skills import get_race_passive_effects
    for effect in get_race_passive_effects(ally.get("race") or race_name):
        if effect.get("type") != "elemental":
            continue
        elements = effect.get("elements", "all")
        dmg_v = effect.get("dmg_value", 0)
        res_v = effect.get("res_value", 0)
        for el in ELEMENTS:
            if elements != "all" and el not in elements:
                continue
            if dmg_v:
                base_dmg[el] += dmg_v
            if res_v:
                base_res[el] += res_v

    # Father's Legacy (Tiefling fire/dark, Dragonborn all-element)
    from family import father_legacy_elemental_bonus
    for el in ELEMENTS:
        legacy_bonus = father_legacy_elemental_bonus(ally, el)
        if legacy_bonus:
            base_dmg[el] += legacy_bonus

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

    The weapon's ``primary_element`` is the source of truth — it drives the
    elemental trait (Ignite/Chain/...) and set the weapon's identity. Many
    weapons tie their element with a secondary one in ``elemental_dmg``
    (Blaze Axe: physical 1.3 / fire 1.3), and dict order used to silently
    resolve those as [PHYSICAL] in the log while the HUD showed something
    else entirely (2026-10-08 bug report: Dorothy's Blaze Lute). Weapons
    without a ``primary_element`` (legacy/unsaved pieces) keep the old
    highest-value pick.

    Returns an element string or None for neutral/physical attacks.
    """
    # Palette's Brush: committed stance overrides the weapon's default element
    from combat.weapon.palette_brush import get_brush_stance_element
    stance_el = get_brush_stance_element(attacker)
    if stance_el:
        return stance_el

    if equipped_weapon and "elemental_dmg" in equipped_weapon:
        e_dmg = equipped_weapon["elemental_dmg"]
        # Explicit primary element wins when it actually deals elemental damage.
        primary = equipped_weapon.get("primary_element")
        if primary and e_dmg.get(primary, 0.0) > 1.0:
            return primary
        # Fallback: highest damage multiplier > 1.0
        best_el = None
        best_val = 1.0
        for el, val in e_dmg.items():
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
    Momentum buff (+3% per stack) applies in both cases.
    """
    if element is None:
        element = get_attack_element(attacker)
    
    if not element or element not in ELEMENTS:
        final_dmg = base_dmg
    else:
        # Get attacker's damage multiplier for this element
        attacker_dmg = attacker.get("elemental_dmg", {})
        dmg_mult = attacker_dmg.get(element, 1.0)
        
        # Arcane Blessing: Elemental Attunement boost
        from facilities.arcane_tower import get_arcane_elemental_boost
        boost = get_arcane_elemental_boost(attacker)
        if boost > 0:
            dmg_mult += boost
        
        # Get target's resistance RATING to this element (higher = stronger).
        # The damage-taken multiplier is 2.0 - rating (see resistance_multiplier).
        target_res = target.get("elemental_res", {})
        res_rating = target_res.get(element, 1.0)

        # Apply elemental_weakness debuff (lowers the resistance rating)
        for debuff in target.get("active_debuffs", []):
            if debuff.get("type") == "elemental_weakness":
                weakness = debuff.get("value", 0)
                res_rating -= weakness
                break

        # Perfect Mimicry: adapted element → bonus damage / resistance
        for buff in attacker.get("active_buffs", []):
            if (buff.get("type") == "elemental_adapt_dmg"
                    and buff.get("element") == element and buff.get("remaining", 0) > 0):
                dmg_mult += buff.get("value", 0)
                break
        for buff in target.get("active_buffs", []):
            if (buff.get("type") == "elemental_adapt_res"
                    and buff.get("element") == element and buff.get("remaining", 0) > 0):
                res_rating += buff.get("value", 0)
                break

        # Event Horizon: flask/boon elemental damage (+% to all elements;
        # stacks additively, unlike the single-entry adapt buffs above)
        for buff in attacker.get("active_buffs", []):
            if buff.get("type") == "eh_ele_dmg":
                dmg_mult += buff.get("value", 0)

        # Elemental Focus (skill) — +% to all elements for a few turns
        for buff in attacker.get("active_buffs", []):
            if buff.get("type") == "elemental_dmg":
                dmg_mult += buff.get("value", 0)

        # Elemental damage for a specific element (Infernal Avatar)
        for buff in attacker.get("active_buffs", []):
            if buff.get("type") == "elemental_dmg_elem" and buff.get("element") == element:
                dmg_mult += buff.get("value", 0)

        # Profession passive elemental bonus (player only)
        if not attacker.get("is_ally"):
            from combat.skills import get_player_passive_elem_bonus
            dmg_mult += get_player_passive_elem_bonus(attacker, element)

        # Form tradition resistance (Steadfast — only the item's primary element)
        from combat.form_perks import get_form_res_rating_bonus
        res_rating += get_form_res_rating_bonus(target, element)

        final_dmg = int(base_dmg * dmg_mult * resistance_multiplier(res_rating))

    # Event Horizon — The Magician's oath: attacks that do not strike the
    # target's weakness element are maimed to 25%. Targets with no weakness
    # element take normal damage (×1.0). Neutral hits fail the gate when
    # the target has weaknesses.
    if attacker.get("_eh_joker_weakness_gate"):
        weak = [el for el in ELEMENTS
                if target.get("elemental_res", {}).get(el, 1.0) < 1.0]
        if weak and (element is None or element not in weak):
            final_dmg = int(final_dmg * 0.25)
    
    # Momentum buff: +3% damage per stack (Chronoweave Mantle).
    # Integer math avoids float rounding (0.03 * N truncation issues).
    from combat.status_effects import get_momentum_stacks
    momentum_stacks = get_momentum_stacks(attacker)
    if momentum_stacks > 0:
        final_dmg = int(final_dmg * (100 + momentum_stacks * 3) / 100)
    
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
