"""facilities/house/core.py — house state resolution and economy helpers.

Owns the player["houses"] layout helpers:

    player["houses"] = {
        city_id: {
            "level":           int (1–8),
            "storage":         list of item dicts,
            "last_income_day": int  (game day when income was last collected),
            "monster_girls":   list of girl dicts,
        }
    }

Reads and writes resolve the target house identically (see _resolve_house),
so a get_house_data() → save_house_data() cycle can never target a different
house than the one it read.
"""

from .constants import (
    CITY_INCOME_MULT,
    ENGAGEMENT_RING_IDS,
    HOUSE_FLOOR_BONUS_CAP,
    HOUSE_FLOOR_BONUS_DIVISOR,
    HOUSE_LEVELS,
    MAX_INCOME_DAYS,
)


def _affection_gain(girl, gain, day):
    """Apply the `beloved` +10% affection bonus to a positive gain."""
    if gain <= 0:
        return gain
    try:
        from family import beloved_multiplier
        return int(round(gain * beloved_multiplier(girl, day)))
    except Exception:
        return gain


# ── Helpers ──────────────────────────────────────────────────────────────────

def _get_house(player, city_id):
    """Return house dict for city, or None if the player has no house there."""
    return player.get("houses", {}).get(city_id)


def _house_level_data(house):
    return HOUSE_LEVELS[house["level"]]


def _get_highest_floor(player):
    """Return the highest dungeon floor ever cleared across all cities."""
    highest = player.get("max_floor", 1)
    for cf in player.get("city_floors", {}).values():
        highest = max(highest, cf.get("max_floor", 1))
    return highest


def _house_floor_mult(player):
    """Progress multiplier: 1.0 early, capped at 4.0 from floor 45."""
    highest_floor = _get_highest_floor(player)
    return 1.0 + min(HOUSE_FLOOR_BONUS_CAP,
                     highest_floor / HOUSE_FLOOR_BONUS_DIVISOR)


def _daily_income(player, city_id, level):
    """House income per day (the displayed rate, paid in full)."""
    base = HOUSE_LEVELS[level]["income_per_day"]
    city_mult = CITY_INCOME_MULT.get(city_id, 1.0)
    return int(round(base * city_mult * _house_floor_mult(player)))


def _pending_income(player, city_id, house):
    """Gold owed since the last collection, capped at MAX_INCOME_DAYS."""
    current_day = player.get("day", 1)
    last_day    = house.get("last_income_day", current_day)
    days_passed = min(current_day - last_day, MAX_INCOME_DAYS)
    if days_passed <= 0:
        return 0
    return int(round(days_passed * _daily_income(player, city_id, house["level"])))


def _reset_daily_limits(player):
    """Reset daily talk/gift counters if the day has changed."""
    today = player.get("day", 1)
    last_day = player.get("girl_daily_last_day", 0)
    if today != last_day:
        player["girl_talk_today"] = {}
        player["girl_gift_today"] = {}
        player["girl_daily_last_day"] = today


def _talks_remaining(player, girl_key):
    """Return how many talks remain for this girl today (always 3 per day)."""
    _reset_daily_limits(player)
    talks_done = player.get("girl_talk_today", {}).get(girl_key, 0)
    daily_limit = 3
    return max(0, daily_limit - talks_done)


def _gifts_remaining(player, girl_key):
    """Return whether this girl can receive a gift today (1 per day)."""
    _reset_daily_limits(player)
    return not player.get("girl_gift_today", {}).get(girl_key, False)


def _has_engagement_ring(player):
    """Return True if the player has any engagement ring in their inventory."""
    return bool(_get_engagement_rings(player))


def _get_engagement_rings(player):
    """Return every engagement ring in the player's inventory (bag order)."""
    return [item for item in player.get("inventory", [])
            if item.get("id") in ENGAGEMENT_RING_IDS]


def _apply_ring_bonus_to_girl(girl, ring):
    """Transfer an engagement ring's stat bonus onto a girl, permanently.

    Stored as ``girl["ring_stat_bonus"]`` (lounge display + save), and — when
    the girl already has stored attributes — added directly to them so the
    bonus applies immediately everywhere (combat, level-ups, dispatch).
    Girls without stored attributes receive the bonus dynamically via
    ``compute_girl_attributes()`` once their stats are first computed.
    """
    ring_bonus = dict(ring.get("mods") or ring.get("base_mods") or {})
    if not ring_bonus:
        return {}
    girl["ring_stat_bonus"] = ring_bonus
    stored = girl.get("attributes")
    if stored:
        for stat, val in ring_bonus.items():
            if stat in stored:
                stored[stat] = stored[stat] + val
    return ring_bonus


def _girl_unique_id(girl):
    """Return a stable unique identifier for a girl (key + name)."""
    return f"{girl.get('key', '')}:{girl.get('name', '')}"


def get_current_house_allies(player):
    """Return list of all monster girl allies currently in the active party."""
    return player.get("allies", [])


def _resolve_house(player, city_id=None):
    """Return (city_id, house) for the player's home house.

    Resolution order: the explicitly requested city if the player owns a
    house there → the origin city's house if owned → the first owned house.

    ``player["origin_city"]`` is repointed by travel and dungeons (nearest
    city context), so it must never be trusted as "the home city" on its own:
    reads and writes resolve identically here, which keeps a
    get_house_data() → save_house_data() cycle from ever targeting a
    different house than the one it read (that mismatch wiped savegame_1).
    """
    houses = player.get("houses") or {}
    if not houses:
        return city_id, None
    if city_id and city_id in houses:
        return city_id, houses[city_id]
    origin = player.get("origin_city")
    if origin and origin in houses:
        return origin, houses[origin]
    first_city = next(iter(houses))
    return first_city, houses[first_city]


def get_house_data(player, city_id=None):
    """Return the live monster_girls list for the player's house."""
    _, house = _resolve_house(player, city_id)
    if house is None:
        return []
    # Live list: callers mutate the house record in place, and a later
    # save_house_data(player, girls) writes back to this same house.
    return house.setdefault("monster_girls", [])


def save_house_data(player, girls_data, city_id=None):
    """Persist the house's monster_girls list.

    The target house is resolved exactly like in get_house_data(), so a list
    read from get_house_data() always round-trips to the same house no matter
    where the volatile origin_city currently points. This function never
    redirects girls to a different house than the one they were read from.

    A new Hovel is only auto-created when the player owns no house at all
    (fallback for early captures before buying a deed).
    """
    if not player.get("houses"):
        player["houses"] = {}
    houses = player["houses"]

    city_id, house = _resolve_house(player, city_id)
    if house is None:
        # No house at all: auto-create a basic Hovel so the player isn't
        # locked out of the monster-girl system.
        city_id = city_id or player.get("origin_city", "solmere")
        house = {"level": 1, "storage": [], "last_income_day": player.get("day", 1)}
        houses[city_id] = house

    # Callers normally pass the live list returned by get_house_data(); only
    # replace the stored list when a genuinely different list is supplied.
    if girls_data is not house.get("monster_girls"):
        house["monster_girls"] = girls_data
