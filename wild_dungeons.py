"""
wild_dungeons.py — Wild dungeon runtime.

Design: docs/wild_dungeon_design.md

Wild dungeons are one-time, limited-floor dungeons that surface on the world
map on a weekly roll (3-7 per cycle), last a few game days, and scale to the
player's progress (max_floor −8 to +8, with the + side scaling in at low
floors; clamped 1-80). Their reward pool is pre-rolled at spawn time so the
world map can preview it before traveling.

State lives in player["wild_dungeons"]; name themes live in
resources/wild_dungeon_themes.py; map layout lives in resources/world_layout.py.

No GUI imports — safe to import from facilities, combat, events, and tests.
"""

import math
import random

from resources.cities import CITIES
from resources.world_layout import city_node_centers, map_bounds
from resources.wild_dungeon_themes import get_theme

# ── Spawn tuning (docs/wild_dungeon_design.md §0, §2) ──────────────────────
SPAWN_PER_CYCLE_MIN = 3          # never fewer than 3 per weekly cycle
SPAWN_PER_CYCLE_MAX = 7          # never more than 7 per weekly cycle
SPAWN_INTERVAL_DAYS = 7          # one cycle per week

LEVEL_BAND = 8                   # max_floor −8 to +8 at depth
LEVEL_BAND_UP_MIN = 2            # upward offset at floor 1 (before scaling)
LEVEL_BAND_UP_STEP = 3           # +1 upward offset per N floors of progress
LEVEL_MIN = 1
LEVEL_MAX = 80

MIN_FLOORS = 2
MAX_FLOORS = 6

MIN_LIFESPAN_DAYS = 3            # dungeons live spawn_day + 3..5 days
MAX_LIFESPAN_DAYS = 5

MIN_CITY_DIST = 90               # px from city node centers (squared compare)
MIN_DUNGEON_DIST = 70            # px between same-cycle dungeon markers

TOP_ITEM_EPIC_FLOOR = 25         # top pool item rarity floor: epic here, rare below

WILD_OFFROAD_MIN_MINUTES = 60    # off-road leg from nearest city to the ruin
WILD_OFFROAD_MAX_MINUTES = 90

_POSITION_ATTEMPTS = 300


# ── State ──────────────────────────────────────────────────────────────────

def _default_state():
    return {
        "active": [],            # [dungeon dict, ...] — spawned, not yet cleared/expired
        "completed": [],         # [dungeon_id, ...] — permanent record
        "next_id": 1,            # monotonically increasing dungeon id counter
        "last_spawn_day": 0,     # throttle for the weekly cycle
    }


def ensure_wild_dungeon_state(player):
    """Initialize/migrate the wild dungeon state block on a player dict."""
    state = player.setdefault("wild_dungeons", _default_state())
    for key, value in _default_state().items():
        state.setdefault(key, value)
    return state


def get_active_dungeons(player):
    """Return the list of active (spawned, not yet cleared/expired) dungeons."""
    return ensure_wild_dungeon_state(player)["active"]


def get_wild_dungeon(player, dungeon_id):
    """Return the active dungeon dict for *dungeon_id*, or None."""
    for dungeon in get_active_dungeons(player):
        if dungeon.get("id") == dungeon_id:
            return dungeon
    return None


def get_completed_dungeon_ids(player):
    """Return the list of cleared wild dungeon ids (permanent record)."""
    return ensure_wild_dungeon_state(player)["completed"]


# ── Generation helpers ──────────────────────────────────────────────────────

def _player_max_floor(player):
    """Player's global max floor (safe for legacy saves)."""
    return max(1, int(player.get("max_floor", 1) or 1))


def _level_band_up(base):
    """Upward offset of the dungeon level band for a base floor.

    The band reaches the full +8 at depth, but the + side scales in at low
    floors so an early player isn't saddled with near-double-level ruins.
    The game's core content caps normal enemies at floor+3 and bosses at
    floor+1..3, so a floor-1 ruin tops out at level 3.

        base  1 → +2      base 10 → +5
        base  4 → +3      base 16 → +7
        base  7 → +4      base 18+ → +8 (cap)
    """
    return min(LEVEL_BAND,
               LEVEL_BAND_UP_MIN + base // LEVEL_BAND_UP_STEP)


def roll_dungeon_level(player):
    """Dungeon level for the player's progress.

    Range: [max_floor − LEVEL_BAND, max_floor + scaled up-band], clamped
    to 1-80. The base is clamped into [1, 80] *before* applying the band so
    an over-cap max_floor (e.g. 100) never produces an empty randint range.
    """
    base = _player_max_floor(player)
    base = max(LEVEL_MIN, min(LEVEL_MAX, base))
    lo = max(LEVEL_MIN, base - LEVEL_BAND)
    hi = min(LEVEL_MAX, base + _level_band_up(base))
    return random.randint(lo, hi)


def find_nearest_city(position):
    """Return the city id whose node center is closest to *position*."""
    best, best_dist = "solmere", float("inf")
    for cid, (cx, cy) in city_node_centers().items():
        dist = (cx - position[0]) ** 2 + (cy - position[1]) ** 2
        if dist < best_dist:
            best, best_dist = cid, dist
    return best


def _roll_name(biome):
    theme = get_theme(biome)
    return f"{random.choice(theme['adjectives'])} {random.choice(theme['ruins'])}"


def _pick_position(existing_positions, near_city=None):
    """Pick a random canvas point inside the map bounds, clear of city nodes
    and other same-cycle dungeon markers.

    When *near_city* is given, the point is drawn from a ring around that
    city's node center so the dungeon's biome matches its surroundings.
    """
    x_min, y_min, x_max, y_max = map_bounds()
    centers = city_node_centers()
    fallback = [x_min, y_min]
    for _ in range(_POSITION_ATTEMPTS):
        if near_city and near_city in centers:
            cx0, cy0 = centers[near_city]
            radius = random.randint(MIN_CITY_DIST, 260)
            angle = random.uniform(0, 2 * math.pi)
            x = int(cx0 + radius * math.cos(angle))
            y = int(cy0 + radius * math.sin(angle))
        else:
            x = random.randint(x_min, x_max)
            y = random.randint(y_min, y_max)
        # Clamp to the canvas bounds
        x = max(x_min, min(x, x_max))
        y = max(y_min, min(y, y_max))
        fallback = [x, y]
        if any((x - cx) ** 2 + (y - cy) ** 2 < MIN_CITY_DIST ** 2
               for cx, cy in centers.values()):
            continue
        if any((x - px) ** 2 + (y - py) ** 2 < MIN_DUNGEON_DIST ** 2
               for px, py in existing_positions):
            continue
        return [x, y]
    return fallback


def generate_reward_pool(level, total_floors):
    """Pre-roll the completion rewards at spawn time (previewable on the map).

    Always returns exactly ``total_floors + 2`` entries. The first entry is
    guaranteed equipment with rarity >= epic at level >= 25, >= rare below.
    The rest are standard drop rolls, re-rolled until a drop lands.

    Only item ids + rarities are stored — item stats are rolled at acquisition
    time via build_item(), so the preview shows names but not exact mods.
    """
    # Lazy import: dungeon.py pulls in combat/curses and would create an
    # import cycle if loaded at module import time.
    from dungeon import _roll_equipment_drop, roll_drop

    pool = []

    # ── Top item: forced rarity floor ────────────────────────────────────
    allowed = ("epic", "legendary") if level >= TOP_ITEM_EPIC_FLOOR \
        else ("rare", "epic", "legendary")
    top_id, top_rarity = "iron_sword", "rare"
    for _ in range(100):
        item_id, rarity = _roll_equipment_drop(level, pandemonium=False)
        top_id, top_rarity = item_id, rarity
        if rarity in allowed:
            break
    pool.append({"item_id": top_id, "rarity": top_rarity})

    # ── Remaining entries: standard drops, no None rolls ─────────────────
    while len(pool) < total_floors + 2:
        drop = roll_drop(level)
        if not drop:
            continue
        item_id, rarity = drop
        pool.append({"item_id": item_id, "rarity": rarity})

    return pool


# ── Lifecycle ───────────────────────────────────────────────────────────────

def expire_dungeons(player):
    """Remove dungeons past their expire_day. Returns the expired dungeons."""
    state = ensure_wild_dungeon_state(player)
    day = player.get("day", 1)
    kept, expired = [], []
    for dungeon in state["active"]:
        if int(dungeon.get("expire_day", 0) or 0) < day:
            expired.append(dungeon)
        else:
            kept.append(dungeon)
    state["active"] = kept
    return expired


def _spawn_one(player, state, seed_city, taken_positions):
    """Create one dungeon dict (does not append to state)."""
    dungeon_id = f"wild_{state['next_id']}"
    state["next_id"] += 1

    biome = CITIES.get(seed_city, {}).get("biome", "temperate")
    level = roll_dungeon_level(player)
    total_floors = random.randint(MIN_FLOORS, MAX_FLOORS)
    position = _pick_position(taken_positions, near_city=seed_city)
    day = int(player.get("day", 1) or 1)
    lifespan = random.randint(MIN_LIFESPAN_DAYS, MAX_LIFESPAN_DAYS)

    return {
        "id": dungeon_id,
        "name": _roll_name(biome),
        "biome": biome,
        "level": level,
        "total_floors": total_floors,
        "highest_floor_cleared": 0,
        "position": position,
        "spawn_day": day,
        "expire_day": day + lifespan,
        "seed_city": seed_city,
        "nearest_city": find_nearest_city(position),
        "attempted": False,
        "reward_pool": generate_reward_pool(level, total_floors),
    }


def maybe_spawn_cycle(player):
    """Weekly spawn cycle: expire old dungeons, then spawn 3-7 new ones.

    Called from events.process_day_rollover (and idempotently elsewhere).
    A cycle already rolled this week does not roll again.

    Returns
    -------
    (spawned, event) — spawned is the list of new dungeon dicts ([] if no
    cycle ran); event is a journal/alert event dict for display, or None.
    """
    state = ensure_wild_dungeon_state(player)
    expire_dungeons(player)

    day = int(player.get("day", 1) or 1)
    if day - int(state.get("last_spawn_day", 0) or 0) < SPAWN_INTERVAL_DAYS:
        return [], None

    state["last_spawn_day"] = day

    city_ids = [cid for cid in CITIES if cid in city_node_centers()]
    if not city_ids:
        return [], None

    count = random.randint(SPAWN_PER_CYCLE_MIN, SPAWN_PER_CYCLE_MAX)
    seed_cities = random.sample(city_ids, k=min(count, len(city_ids)))

    taken = [tuple(d.get("position", (0, 0))) for d in state["active"]]
    spawned = []
    for seed_city in seed_cities:
        dungeon = _spawn_one(player, state, seed_city, taken)
        taken.append(tuple(dungeon["position"]))
        state["active"].append(dungeon)
        spawned.append(dungeon)

    event = _build_spawn_event(player, spawned)
    return spawned, event


def _build_spawn_event(player, spawned):
    """Build the combined journal/alert event for a spawn cycle."""
    lines = [
        f"  • {d['name']} — Lv {d['level']} ({d['total_floors']} floors) near "
        f"{CITIES.get(d['nearest_city'], {}).get('name', d['nearest_city'])}"
        for d in spawned
    ]
    event = {
        "id": "wild_dungeon_spawn",
        "name": "Strange Ruins Surfaced",
        "desc": (f"{len(spawned)} wild dungeons appeared on the world map:\n"
                 + "\n".join(lines)),
        "day": int(player.get("day", 1) or 1),
        "fixed": False,
    }
    # Lazy import to avoid a module-level cycle with events.py.
    from events import record_event
    record_event(player, event)
    return event


def complete_wild_dungeon(player, dungeon_id):
    """Move a cleared dungeon into the completed record. Returns the dungeon
    dict if it was still active, or None.

    Idempotent: completing a dungeon that already expired off the active
    list still records the completion (no duplicate entries).
    """
    state = ensure_wild_dungeon_state(player)
    found = None
    for i, dungeon in enumerate(state["active"]):
        if dungeon.get("id") == dungeon_id:
            found = state["active"].pop(i)
            break
    if dungeon_id not in state["completed"]:
        state["completed"].append(dungeon_id)
    return found


def record_completion_event(player, dungeon, gold, exp):
    """Append a completion entry to the journal's Event tab.

    Direct append (not record_event) so two ruins cleared on the same day
    both appear. The Journal UI renders the date from the entry's ``day``
    field — dungeon name and level sit in the header/description.
    """
    from events import ensure_journal
    ensure_journal(player)
    name = dungeon.get("name", "Wild Dungeon")
    level = int(dungeon.get("level", 1) or 1)
    floors = int(dungeon.get("total_floors", 1) or 1)
    player["journal"]["events"].append({
        "day": int(player.get("day", 1) or 1),
        "name": f"Conquered: {name}",
        "desc": (f"Lv {level} wild dungeon — all {floors} floors cleared. "
                 f"Spoils: +{gold} gold, +{exp} XP."),
        "tag": "[WILD]",
        "fixed": False,
    })


# ── Travel (shared by GUI world map and terminal mode) ──────────────────────

def offroad_segment(player, dungeon, to=None):
    """Build the synthetic final travel segment (nearest city → dungeon).

    Mirrors facilities.pathfinding's land-segment math — mount time
    reduction, daily travel effect (e.g. Heavy Rain), and cargo
    penalty/overload — so the off-road leg behaves like any other road.

    The segment's ``to`` is ``"wild:<id>"``; GUI/terminal travel code
    recognizes this prefix instead of a city key.
    """
    # Lazy imports — keep this module import-light and cycle-free.
    from resources.mounts import get_mount
    from resources.trade_goods import (
        cargo_travel_penalty, cargo_overloaded_for_travel,
    )

    mount = None
    if player.get("mount_id"):
        mount = get_mount(player["mount_id"])
    mount_reduction = mount.get("time_reduction", 0) if mount else 0.0
    mount_cap = mount.get("cargo_capacity", 0) if mount else 0

    raw_time = random.randint(WILD_OFFROAD_MIN_MINUTES, WILD_OFFROAD_MAX_MINUTES)
    effective_time = int(raw_time * (1 - mount_reduction))

    daily_time_mult = player.get("daily_effects", {}).get("travel_time_mult", 1.0)
    if daily_time_mult != 1.0:
        effective_time = int(effective_time * daily_time_mult)

    penalty = cargo_travel_penalty(player, mount_cap)
    if penalty > 0:
        effective_time = int(effective_time * (1 + penalty))
    blocked = cargo_overloaded_for_travel(player, mount_cap)

    nearest = dungeon.get("nearest_city", "solmere")
    return {
        "from": nearest,
        "to": to or f"wild:{dungeon['id']}",
        "type": "land",
        "raw_time": raw_time,
        "effective_time": effective_time,
        "biome": CITIES.get(nearest, {}).get("biome", "temperate"),
        "cost": 0,
        "blocked": blocked,
    }


def build_journey_to_dungeon(player, dungeon, to=None):
    """Combine the city route to the nearest city with the off-road leg.

    Returns a find_shortest_path()-shaped dict (path / total_time /
    total_cost / ferry_segments / segments / blocked_segments), or None
    when no route exists. When the player already stands in the nearest
    city, the route is just the off-road leg.
    """
    from facilities.pathfinding import find_shortest_path

    origin = player.get("location", "solmere")
    if origin == "dungeon":
        origin = player.get("origin_city", "solmere")

    nearest = dungeon.get("nearest_city", "solmere")
    route = find_shortest_path(player, origin, nearest)
    if route is None:
        return None

    segment = offroad_segment(player, dungeon, to=to)
    segments = list(route["segments"]) + [segment]
    path = list(route["path"]) + [segment["to"]]
    blocked = list(route.get("blocked_segments", []))
    if segment.get("blocked"):
        blocked.append(segment)

    return {
        "path": path,
        "total_time": route["total_time"] + segment["effective_time"],
        "total_cost": route["total_cost"],
        "ferry_segments": route.get("ferry_segments", 0),
        "segments": segments,
        "blocked_segments": blocked,
    }


def embark_wild_dungeon_journey(player, dungeon, combat_override=None):
    """Terminal-mode journey to a wild dungeon.

    Runs the city legs and the off-road leg through the existing travel
    event system, then sets the wild-dungeon entry fields on arrival.

    Returns
    -------
    "dead"     – player died en route
    "blocked"  – cargo overloaded for the journey
    "no_route" – no path to the nearest city
    None       – arrived at the dungeon (player["wild_dungeon_id"] set)
    """
    journey = build_journey_to_dungeon(player, dungeon)
    if journey is None:
        return "no_route"
    if journey.get("blocked_segments"):
        return "blocked"

    from facilities.travel import embark_multi_leg_journey
    return embark_multi_leg_journey(
        player, journey["segments"],
        combat_override=combat_override,
        wild_dungeon=dungeon,
    )
