# bestiary.py — discovered-enemy journal used by the Guild Hall.
"""Bestiary tracking and display data.

The old guild "Enemy Intelligence" screen exposed every spawn-table entry
before the player had met any of them.  The bestiary instead reveals a
creature only after it has been defeated or captured at least once.

Ledger shape stored on the player::

    player["bestiary"][enemy_key] = {
        "defeated": int,
        "captured": int,
        "regions": ["forest", ...],
    }
"""

from resources.enemies import ENEMIES, BIOME_RACES

# Sort order for the bestiary pages (matches the type labels shown to players).
TYPE_ORDER = {
    "Common": 0,
    "Monster Girl": 1,
    "Boss": 2,
    "Superboss": 3,
}

_REGION_LABELS = {
    "temperate": "Temperate",
    "coastal": "Coastal",
    "sea_caves": "Sea Caves",
    "forest": "Forest",
    "swamp": "Swamp",
    "mountain": "Mountain",
    "desert": "Desert",
    "volcanic": "Volcanic",
    "magical": "Magical",
    "pandemonium": "Pandemonium",
    "wonderland": "Wonderland",
    "celestial": "Celestial",
    "event_horizon": "Event Horizon",
}

# Short race-flavoured lines used when an enemy template has no explicit
# ``description``.  Authors can add per-enemy ``description:`` fields in YAML
# later and those override these fallbacks automatically.
_RACE_DESCRIPTIONS = {
    "Human": "A human dungeon-dweller, dangerous through cunning and adaptability.",
    "Goblin": "A wiry goblin raider that trusts numbers, traps, and stolen steel.",
    "Orc": "An orcish bruiser who solves problems with overwhelming strength.",
    "Undead": "A deathless husk that hungers for the warmth of the living.",
    "Beast": "A predatory beast whose instincts sharpen every strike.",
    "Demon": "A demon of fire and malice, never more dangerous than when cornered.",
    "Construct": "An artificial guardian animated by old magic and unfeeling duty.",
    "Dragonkin": "A dragonkin warrior carrying the pride and elemental breath of its elders.",
    "Fey": "A fey creature weaving glamour and restless wind into every attack.",
    "Elemental": "A living knot of elemental force bound to one overwhelming nature.",
    "Giant": "A giant whose sheer mass turns the ground itself into a weapon.",
    "Vampire": "A vampire that stalks from the dark and trades blood for power.",
    "Lizardfolk": "A lizardfolk hunter moving with patient, cold-blooded precision.",
    "Gnome": "A gnome tinkerer whose contraptions crackle with stored thunder.",
    "Shadow": "A shadow-thing that drinks the light and slips between strikes.",
    "Clockwork": "A clockwork construct driven by ticking gears and crackling charge.",
    "Abomination": "An abomination of stitched flesh and bottomless appetite.",
    "Storybook": "A storybook creature, vivid and cruel in the way only a fairy tale can be.",
    "Angel": "A radiant angel whose judgment burns away all doubt.",
}

_FALLBACK_DESCRIPTION = "A creature of the dungeons whose nature is written in its scars."

# Sentinel so callers can distinguish "use the current dungeon" from
# "record no region" (save backfills must not stamp the current biome).
_UNSET = object()


def _safe_int(value):
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


# ── Ledger helpers ──────────────────────────────────────────────────────────

def ensure_bestiary(player):
    """Return the player's bestiary ledger, creating it when missing."""
    ledger = player.get("bestiary")
    if not isinstance(ledger, dict):
        ledger = {}
        player["bestiary"] = ledger
    return ledger


def _get_entry(ledger, key):
    entry = ledger.get(key)
    if not isinstance(entry, dict):
        entry = {}
        ledger[key] = entry
    entry["defeated"] = _safe_int(entry.get("defeated"))
    entry["captured"] = _safe_int(entry.get("captured"))
    regions = entry.get("regions")
    if not isinstance(regions, list):
        regions = []
        entry["regions"] = regions
    return entry


def _resolve_key(enemy):
    if isinstance(enemy, dict):
        return enemy.get("key")
    if isinstance(enemy, str):
        return enemy
    return None


def is_bestiary_candidate(key):
    """True if this enemy key belongs in the bestiary.

    Internal heroine ally templates are excluded; every real enemy, minion and
    shadow copy can be recorded.
    """
    template = ENEMIES.get(key)
    return bool(template) and not template.get("_heroine")


def _current_region(player):
    region = player.get("dungeon_region")
    if isinstance(region, str) and region.strip():
        return region.strip()
    return None


def _remember_region(entry, region):
    if not region:
        return
    regions = entry.setdefault("regions", [])
    if region not in regions:
        regions.append(region)


def record_defeat(player, enemy, *, once=False, region=_UNSET):
    """Record a defeat.

    ``enemy`` may be an enemy dict (from combat) or a bare enemy key (used by
    the superboss kill ledger / save backfill).  When a dict is passed it is
    marked so the same enemy instance cannot be counted twice by different
    combat paths (on-kill callbacks + round pruning).

    ``once=True`` only increments the count when no defeat was recorded yet.
    Regions are still merged so later encounters can broaden the entry.
    """
    key = _resolve_key(enemy)
    if not key or not is_bestiary_candidate(key):
        return False
    if isinstance(enemy, dict) and enemy.get("_bestiary_defeat_logged"):
        return False

    ledger = ensure_bestiary(player)
    entry = _get_entry(ledger, key)
    if not once or not entry.get("defeated"):
        entry["defeated"] = int(entry.get("defeated", 0)) + 1
    if region is _UNSET:
        region = _current_region(player)
    _remember_region(entry, region)
    if isinstance(enemy, dict):
        enemy["_bestiary_defeat_logged"] = True
    from titles import check_unlock
    check_unlock(player)
    return True


def record_capture(player, enemy, *, once=False, region=_UNSET):
    """Record a successful capture (same argument rules as ``record_defeat``)."""
    key = _resolve_key(enemy)
    if not key or not is_bestiary_candidate(key):
        return False
    if isinstance(enemy, dict) and enemy.get("_bestiary_capture_logged"):
        return False

    ledger = ensure_bestiary(player)
    entry = _get_entry(ledger, key)
    if not once or not entry.get("captured"):
        entry["captured"] = int(entry.get("captured", 0)) + 1
    if region is _UNSET:
        region = _current_region(player)
    _remember_region(entry, region)
    if isinstance(enemy, dict):
        enemy["_bestiary_capture_logged"] = True
    from titles import check_unlock
    check_unlock(player)
    return True


# ── Display data ────────────────────────────────────────────────────────────

def classify_enemy(template):
    """Return the bestiary type label for a template."""
    if template.get("super_boss"):
        return "Superboss"
    if template.get("boss"):
        return "Boss"
    if template.get("monster_girl"):
        return "Monster Girl"
    return "Common"


def get_total_enemy_count():
    """Number of enemies that can appear in the bestiary."""
    return sum(
        1 for t in ENEMIES.values()
        if not t.get("_heroine") and not t.get("city_only")
    )


def get_description(key):
    """Short flavour description: YAML override first, then a race/role line."""
    template = ENEMIES.get(key, {})
    override = template.get("description") or template.get("desc")
    if override:
        return " ".join(str(override).split())

    parts = [_RACE_DESCRIPTIONS.get(template.get("race", ""), _FALLBACK_DESCRIPTION)]
    enemy_type = classify_enemy(template)
    if enemy_type == "Superboss":
        parts.append("A legendary superboss whose presence warps the dungeon around it.")
    elif enemy_type == "Boss":
        parts.append("It rules the deepest rooms of its dungeon as a floor boss.")
    if template.get("monster_girl"):
        parts.append("A monster girl — a capture net can bring her home.")
    elif template.get("minion_only"):
        parts.append("It rarely fights without a greater master at its side.")
    return " ".join(parts)


def get_dungeon_labels(key, entry=None):
    """Dungeons the creature is tied to (recorded regions first, then spawn data)."""
    regions = []
    if isinstance(entry, dict):
        raw = entry.get("regions")
        if isinstance(raw, list):
            regions = [r for r in raw if isinstance(r, str) and r]
    if not regions:
        template = ENEMIES.get(key, {})
        races = {template.get("race"), template.get("secondary_race")}
        races.discard(None)
        regions = [biome for biome, allowed in BIOME_RACES.items()
                   if races & set(allowed)]
    labels = []
    for region in regions:
        label = _REGION_LABELS.get(region, region.replace("_", " ").title())
        if label not in labels:
            labels.append(label)
    return labels


def get_enemy_card(key, entry=None):
    """Build everything the guild UI needs to render one bestiary entry."""
    from combat.stats import compute_enemy_attributes
    from combat.elemental import compute_enemy_elemental

    template = ENEMIES.get(key)
    if not template:
        return None

    attrs = compute_enemy_attributes(key)
    res, dmg = compute_enemy_elemental({"key": key})
    race = template.get("race", "Unknown")
    secondary = template.get("secondary_race")
    race_display = f"{race} / {secondary}" if secondary and secondary != race else race

    return {
        "key": key,
        "name": template.get("name", key),
        "race": race_display,
        "level": int(template.get("level", 1) or 1),
        "type": classify_enemy(template),
        "hp": int(template.get("base_hp", 0) or 0),
        "attributes": attrs,
        "elemental_res": res,
        "elemental_dmg": dmg,
        "description": get_description(key),
        "dungeons": get_dungeon_labels(key, entry),
        "defeated": _safe_int((entry or {}).get("defeated", 0)),
        "captured": _safe_int((entry or {}).get("captured", 0)),
    }


def get_discovered_cards(player):
    """Return cards for every defeated/captured enemy, grouped by type."""
    ledger = ensure_bestiary(player)
    cards = []
    for key, entry in ledger.items():
        if not isinstance(entry, dict):
            continue
        if not entry.get("defeated") and not entry.get("captured"):
            continue
        card = get_enemy_card(key, entry)
        if card is None:
            continue
        cards.append(card)
    cards.sort(key=lambda c: (TYPE_ORDER.get(c["type"], 99), c["level"], c["name"].lower()))
    return cards
