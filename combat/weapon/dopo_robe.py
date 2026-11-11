"""Old Dopo Robe — Event Horizon trophy armor (docs/event_horizon_design.md §10.5).

Blade-synergy aura, live-read at damage time (handles mid-combat ally swaps):

- The whole effect requires the *wearer* to wield a blade.
- Wearer:   ×1.40 base, +5% per other blade-wielder, UNCAPPED. All recruited
            allies count (including benched). When an ALLY wears the robe, a
            blade-wielding player also counts.
- Each other blade-wielder (excluding the wearer): ×1.15.

Actor-based: the player or any ally may wear the robe (they become the wearer).
Wired into the four party damage paths (player basic / skills, ally basic /
skills).
"""

BLADE_TYPE = "blade"

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


def weapon_is_blade(item):
    return _weapon_type(item) == BLADE_TYPE


def find_wearer(player):
    """Return the actor wearing the robe (player or ally), else None."""
    if has_dopo_robe(player):
        return player
    for ally in player.get("allies", []):
        if has_dopo_robe(ally):
            return ally
    return None


def count_blade_allies(player, wearer):
    """All other blade-wielders, excluding the wearer.

    Counts every recruited ally (including benched). When an ally wears the
    robe, the player also counts if they wield a blade.
    """
    count = 0
    if wearer is not player and weapon_is_blade(_weapon_of(player)):
        count += 1
    for ally in player.get("allies", []):
        if ally is wearer:
            continue
        if weapon_is_blade(_weapon_of(ally)):
            count += 1
    return count


def get_robe_multiplier(attacker, player):
    """Damage multiplier for `attacker` (1.0 when the robe is not in play)."""
    if not attacker or not player:
        return 1.0
    wearer = find_wearer(player)
    if wearer is None or not weapon_is_blade(_weapon_of(wearer)):
        return 1.0
    if attacker is wearer:
        return WEARER_BASE + WEARER_PER_ALLY * count_blade_allies(player, wearer)
    if weapon_is_blade(_weapon_of(attacker)):
        return ALLY_BONUS
    return 1.0
