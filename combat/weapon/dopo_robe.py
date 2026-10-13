"""Old Dopo Robe — Event Horizon trophy armor (docs/event_horizon_design.md §10.5).

Sword-synergy aura, live-read at damage time (handles mid-combat ally swaps):

- The whole effect requires the *wearer* to wield a sword-family weapon.
- Wearer:   ×1.40 base, +5% per sword-wielding ALLY (all recruited allies,
            including benched), UNCAPPED.
- Each sword-wielding ally (excluding the wearer): ×1.15.

Actor-based: the player or any ally may wear the robe (they become the wearer).
Wired into the four party damage paths (player basic / skills, ally basic /
skills).
"""

# Sword family = formal weapon_type values (Phase 1 data pass on all weapons).
SWORD_TYPES = frozenset({"sword", "blade", "greatsword", "rapier", "cutlass"})

WEARER_BASE = 1.40
WEARER_PER_ALLY = 0.05
ALLY_BONUS = 1.15

_ITEM_ID = "old_dopo_robe"
_SPECIAL = "dopo_robe"


def _equipped_items(actor):
    return [it for it in (actor.get("equipped", {}) or {}).values() if it]


def has_dopo_robe(actor):
    if not actor:
        return False
    for item in _equipped_items(actor):
        if item.get("special") == _SPECIAL or item.get("id") == _ITEM_ID:
            return True
    return False


def _weapon_type(item):
    if not item:
        return None
    wt = item.get("weapon_type")
    if wt:
        return wt
    # Old-save fallback: some item instances were built before the field pass
    try:
        from resources.items import ITEMS
        return (ITEMS.get(item.get("id"), {}) or {}).get("weapon_type")
    except Exception:
        return None


def _weapon_of(actor):
    return (actor.get("equipped", {}) or {}).get("weapon")


def weapon_is_sword(item):
    return _weapon_type(item) in SWORD_TYPES


def find_wearer(player):
    """Return the actor wearing the robe (player or ally), else None."""
    if has_dopo_robe(player):
        return player
    for ally in player.get("allies", []):
        if has_dopo_robe(ally):
            return ally
    return None


def count_sword_allies(player, wearer):
    """All recruited allies wielding a sword (incl. benched), excluding wearer."""
    count = 0
    for ally in player.get("allies", []):
        if ally is wearer:
            continue
        if weapon_is_sword(_weapon_of(ally)):
            count += 1
    return count


def get_robe_multiplier(attacker, player):
    """Damage multiplier for `attacker` (1.0 when the robe is not in play)."""
    if not attacker or not player:
        return 1.0
    wearer = find_wearer(player)
    if wearer is None or not weapon_is_sword(_weapon_of(wearer)):
        return 1.0
    if attacker is wearer:
        return WEARER_BASE + WEARER_PER_ALLY * count_sword_allies(player, wearer)
    if weapon_is_sword(_weapon_of(attacker)):
        return ALLY_BONUS
    return 1.0
