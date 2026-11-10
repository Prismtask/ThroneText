import random

# Fixed events keyed by day-of-month (1-30)
FIXED_EVENTS = {
    1:  {
        "id": "new_moon",
        "name": "New Moon Festival",
        "desc": "The guild celebrates the new moon! +25% bounty gold today.",
        "effect": {"bounty_bonus": 0.25},
    },
    7:  {
        "id": "market_day",
        "name": "Traveling Merchant",
        "desc": "A traveling merchant sets up shop in the city square. Check the guild hall!",
        "effect": {"traveling_merchant": True},
    },
    15: {
        "id": "full_moon",
        "name": "Full Moon",
        "desc": "The full moon rises. Monsters grow restless... (+20% dungeon difficulty, +30% gold drops)",
        "effect": {"full_moon": True, "gold_bonus": 0.30},
    },
    21: {
        "id": "market_day",
        "name": "Traveling Merchant",
        "desc": "A traveling merchant sets up shop in the city square. Check the guild hall!",
        "effect": {"traveling_merchant": True},
    },
    30: {
        "id": "month_end",
        "name": "Month-End Festival",
        "desc": "City-wide celebration! All shops offer 20% discounts today.",
        "effect": {"shop_discount": 0.20},
    },
}

# Random event pool — weighted by the "weight" field
RANDOM_EVENT_POOL = [
    {
        "id": "lucky_day",
        "name": "Lucky Day",
        "desc": "Fortune smiles upon you! +15% gold find for today.",
        "effect": {"gold_bonus": 0.15},
        "weight": 10,
    },
    {
        "id": "rainy_day",
        "name": "Heavy Rain",
        "desc": "Rain lashes the city. Travel costs +2 blocks today.",
        "effect": {"rain_level": 2, "weather": "rain"},
        "weight": 10,
        "season_weights": {"spring": 1.6, "summer": 0.6,
                           "autumn": 1.2, "winter": 0.3},
    },
    {
        "id": "snowy_day",
        "name": "Heavy Snow",
        "desc": "Snow blankets the roads. Travel costs +2 blocks today.",
        "effect": {"rain_level": 2, "weather": "snow"},
        "weight": 10,
        "season_weights": {"spring": 0.2, "summer": 0.0,
                           "autumn": 0.4, "winter": 2.2},
    },
    {
        "id": "foggy_day",
        "name": "Thick Fog",
        "desc": "Fog swallows the roads. Travel costs +1 block today.",
        "effect": {"rain_level": 1, "weather": "fog"},
        "weight": 8,
        "season_weights": {"spring": 1.0, "summer": 0.2,
                           "autumn": 2.0, "winter": 0.8},
    },
    {
        "id": "bounty_rush",
        "name": "Bounty Rush",
        "desc": "The guild posts emergency bounties! Bounty gold is increased by 50% today.",
        "effect": {"bounty_bonus": 0.50},
        "weight": 8,
    },
    {
        "id": "monster_surge",
        "name": "Monster Surge",
        "desc": "A monster surge has been reported! Dungeon enemies are more numerous.",
        "effect": {"monster_surge": True},
        "weight": 7,
    },
    {
        "id": "blessed_wind",
        "name": "Blessed Wind",
        "desc": "A warm wind carries whispers of ancient blessings. +1 to all attributes for today.",
        "effect": {"all_stats": 1},
        "weight": 5,
    },
    {
        "id": "ill_omen",
        "name": "Ill Omen",
        "desc": "A dark cloud hangs over the city. Gold is scarce and dungeons swarm with foes...",
        "effect": {"gold_bonus": -0.05, "monster_surge": True},
        "weight": 5,
    },
    {
        "id": "tax_day",
        "name": "Tax Day",
        "desc": "The crown's collectors swarm the markets! Shop prices are 15% higher today.",
        "effect": {"shop_surcharge": 0.15},
        "weight": 6,
    },
    {
        "id": "scholars_day",
        "name": "Scholar's Day",
        "desc": "The sages open their libraries to the city! You gain 25% more XP today.",
        "effect": {"xp_bonus": 0.25},
        "weight": 9,
    },
    {
        "id": "peaceful_skies",
        "name": "Peaceful Skies",
        "desc": "An unnatural calm settles over the land. Monsters are 10% weaker today.",
        "effect": {"difficulty_mod": -0.10},
        "weight": 7,
    },
    {
        "id": "crimson_dawn",
        "name": "Crimson Dawn",
        "desc": "The sky burns red at daybreak. Monsters fight 15% harder today.",
        "effect": {"difficulty_mod": 0.15},
        "weight": 5,
    },
    {
        "id": "monster_girl_season",
        "name": "Monster Girl Season",
        "desc": "Monster girls emerge from their dens in force! +15 to capture attempts today.",
        "effect": {"capture_bonus": 15},
        "weight": 8,
    },
    {
        "id": "wary_prey",
        "name": "Wary Prey",
        "desc": "Rumors of hunters sweep the wilds. Monster girls are skittish: -10 to capture attempts today.",
        "effect": {"capture_bonus": -10},
        "weight": 6,
    },
]


# ── Helpers ───────────────────────────────────────────────────────────────

def get_month_day(global_day):
    """Convert a global day counter to (month, day_of_month)."""
    month = (global_day - 1) // 30 + 1
    day_of_month = (global_day - 1) % 30 + 1
    return month, day_of_month


# ── Seasons ─────────────────────────────────────────────────────────────
# Months are 30 days and repeat forever; one season per month keeps the
# world visibly changing (a full cycle is 120 days):
#   M1 Spring · M2 Summer · M3 Autumn · M4 Winter · M5 Spring ...
SEASONS = (
    ("spring", "Spring"),
    ("summer", "Summer"),
    ("autumn", "Autumn"),
    ("winter", "Winter"),
)


def get_season(day_or_player):
    """Return ``(id, name)`` for a global day or a player dict.

    Seasons only route flavor and the weather table — they never add a
    combat/gold/XP multiplier (weather is the single numeric dial).
    """
    if isinstance(day_or_player, dict):
        day = day_or_player.get("day", 1)
    else:
        day = day_or_player
    try:
        day = max(1, int(day or 1))
    except (TypeError, ValueError):
        day = 1
    month, _ = get_month_day(day)
    return SEASONS[(month - 1) % len(SEASONS)]


# ── Wonderland date flavours ────────────────────────────────────────────
_WL_DATE_FLAVORS = [
    ("Unbirthday", "Happy Unbirthday to you!"),
    ("Jam Yesterday, Jam Tomorrow", "But never jam today."),
    ("The 32nd of Never", "The calendar has given up."),
    ("Tuesday (allegedly)", "It's always Tuesday. Or is it Thursday?"),
    ("⏳:⌛", "The hourglass has unionized."),
    ("Chapter VII, Page 42", "The book is still being written."),
    ("Teatime", "The eternal hour of tea."),
    ("Curiouser Day", "Days get curiouser and curiouser."),
    ("Yesterday's Tomorrow", "Or perhaps tomorrow's yesterday."),
    ("???", "The caterpillar asks: 'Who are you?'"),
    ("Croquet Season", "The Queen plays croquet. Forever."),
    ("Half a Day Late", "The White Rabbit will be late."),
    ("The Endless Afternoon", "The Dormouse hasn't woken up yet."),
    ("Month of Madness", "We're all mad here."),
    ("Once Upon a Time", "…and they're still living."),
]


def format_short_date(global_day):
    """Return a calendar stamp ``dd/mm`` for a global day.

    Months are 30 days and the calendar year is four season-months (120
    days), so the month wraps 1–4: day 13 → ``13/01``, day 121 → ``01/01``.
    """
    try:
        day = max(1, int(global_day or 1))
    except (TypeError, ValueError):
        day = 1
    month, dom = get_month_day(day)
    month = (month - 1) % len(SEASONS) + 1
    return f"{dom:02d}/{month:02d}"


def format_date(player_or_day):
    """Return the calendar date, e.g. '13/01 · Spring'.

    When the player is in Wonderland, returns a whimsical date flavour instead.
    """
    if isinstance(player_or_day, dict):
        if player_or_day.get("wonderland_active"):
            date_str, flavor = random.choice(_WL_DATE_FLAVORS)
            return f"{date_str}  — {flavor}"
        day = player_or_day.get("day", 1)
    else:
        day = player_or_day
    return f"{format_short_date(day)} · {get_season(day)[1]}"


# ── Relative day phrasing ─────────────────────────────────────────────────

def _global_day(value, default=1):
    """Best-effort day int from a player dict, a day number, or None."""
    if isinstance(value, dict):
        value = value.get("day", default)
    try:
        return max(1, int(value))
    except (TypeError, ValueError):
        return default


def days_until(target_day, current_day=1):
    """Whole days from ``current_day`` to ``target_day`` (negative = past)."""
    return _global_day(target_day) - _global_day(current_day)


def format_day_delta(target_day, current_day=1):
    """Relative day phrase: ``today``, ``tomorrow``, ``in 4 days``, ``2 days ago``."""
    delta = days_until(target_day, current_day)
    if delta == 0:
        return "today"
    if delta == 1:
        return "tomorrow"
    if delta == -1:
        return "yesterday"
    if delta > 1:
        return f"in {delta} days"
    return f"{-delta} days ago"


def format_days_left(target_day, current_day=1):
    """Days remaining as ``1 day`` / ``4 days``, clamped at zero."""
    left = max(0, days_until(target_day, current_day))
    return "1 day" if left == 1 else f"{left} days"


def format_return_time(target_abs_minutes, current_abs_minutes):
    """Relative clock stamp: ``today at 14:00``, ``tomorrow at 04:00``."""
    try:
        target = max(0, int(target_abs_minutes))
        current = max(0, int(current_abs_minutes))
    except (TypeError, ValueError):
        return "soon"
    target_day, mins = divmod(target, 1440)
    current_day = current // 1440
    clock = f"{mins // 60:02d}:{mins % 60:02d}"
    delta = target_day - current_day
    if delta <= 0:
        return f"today at {clock}"
    if delta == 1:
        return f"tomorrow at {clock}"
    return f"in {delta} days at {clock}"


# ── Event checking ────────────────────────────────────────────────────────

def _pick_random_event(day):
    """Pick a random event using the day as seed (reproducible per day).

    Season only reweights the pool (weather events are seasonal); it never
    introduces a second combat/gold/XP modifier.
    """
    rng = random.Random(day)
    if rng.random() >= 0.20:          # 20% chance for a random event
        return None
    season_id, _ = get_season(day)
    pool = []
    weights = []
    for evt in RANDOM_EVENT_POOL:
        weight = evt["weight"]
        season_weights = evt.get("season_weights")
        if season_weights:
            weight *= season_weights.get(season_id, 1.0)
        if weight <= 0:
            continue
        pool.append(evt)
        weights.append(weight)
    chosen = rng.choices(pool, weights=weights, k=1)[0]
    return dict(chosen)


def check_events_for_day(day):
    """Return a list of all events (fixed + random) for a given global day."""
    events = []

    # Fixed event
    _, dom = get_month_day(day)
    fixed = FIXED_EVENTS.get(dom)
    if fixed:
        evt = dict(fixed)
        evt["day"] = day
        evt["fixed"] = True
        events.append(evt)

    # Random event
    random_evt = _pick_random_event(day)
    if random_evt:
        random_evt["day"] = day
        random_evt["fixed"] = False
        events.append(random_evt)

    return events


# ── Effects ─────────────────────────────────────────────────────────────

def apply_event_effects(player, event):
    """Apply an event's effects to the player."""
    effects = event.get("effect", {})
    if not effects:
        return

    daily = player.setdefault("daily_effects", {})
    for key, val in effects.items():
        # Numeric effects stack; flag effects overwrite
        if isinstance(val, (int, float)) and not isinstance(val, bool):
            daily[key] = daily.get(key, 0) + val
        else:
            daily[key] = val

    # Special handling for all_stats → add a temporary buff
    if "all_stats" in effects:
        _apply_all_stats_buff(player, effects["all_stats"])


def _apply_all_stats_buff(player, bonus):
    """Give the player a one-day buff that boosts all attributes."""
    buff = {
        "type": "daily_buff",
        "stat": "all",
        "value": bonus,
        "remaining": 1,   # expires after 1 floor/day transition
    }
    player.setdefault("active_buffs", []).append(buff)


def get_daily_effect(player, key, default=None):
    """Read a value from the player's currently-active daily effects."""
    return player.get("daily_effects", {}).get(key, default)


def get_daily_bonus_multiplier(player, key):
    """Return 1.0 + a numeric daily effect (e.g. gold_bonus) as a multiplier.

    Safe for missing/corrupt values — always returns a float >= 1.0.
    """
    try:
        value = float(player.get("daily_effects", {}).get(key, 0))
    except (TypeError, ValueError):
        value = 0.0
    return 1.0 + value


# ── Display ─────────────────────────────────────────────────────────────

def format_event_alert(event):
    """Build a formatted multi-line string for an event."""
    tag = "[FIXED]" if event.get("fixed") else "[RANDOM]"
    lines = [
        "",
        "=" * 50,
        f"  [EVENT]  {event['name'].upper()}  {tag}",
        "=" * 50,
        f"  {event['desc']}",
    ]
    return "\n".join(lines)


def ensure_journal(player):
    """Initialize the journal structure if it doesn't exist."""
    player.setdefault("journal", {
        "events": [],
        "main_quests": [],
        "side_quests": [],
    })


def record_event(player, event):
    """Record an event in the player's journal. Deduplicates by (day, name)."""
    ensure_journal(player)
    journal_events = player["journal"]["events"]
    # Deduplicate: don't add the same event twice for the same day
    event_day = event.get("day", 0)
    event_name = event.get("name", "")
    for existing in journal_events:
        if existing.get("day") == event_day and existing.get("name") == event_name:
            return  # Already recorded
    # Store a lightweight copy (strip effect details that might be large)
    journal_events.append({
        "day": event_day,
        "name": event_name,
        "desc": event.get("desc", ""),
        "tag": "[FIXED]" if event.get("fixed") else "[RANDOM]",
        "fixed": event.get("fixed", False),
    })


def queue_event_alerts(player, events):
    """Store events so they can be shown when the player leaves the dungeon.

    All event notices are delivered by the GUI Event Notice popup. There is
    no console/terminal rendering path any more.
    """
    queue = player.setdefault("event_queue", [])
    queue.extend(events)


def get_event_queue_events(player):
    """Pop and return queued raw event dicts, or empty list if none.

    Used by the GUI event notice popup, which needs structured data
    (name, day, duration, description) rather than formatted strings.
    """
    return player.pop("event_queue", [])


# ── Wonderland Unlock ───────────────────────────────────────────────────

def check_wonderland_unlock_conditions(player):
    """Return True if all Wonderland unlock conditions are met.

    Conditions:
      1. Floor 20+ cleared in at least 2 different biomes
      2. Player possesses a Looking Glass Shard in inventory
    """
    if player.get("wonderland_unlocked"):
        return False

    # Condition 1: Floor 20+ cleared in ≥2 biomes. Same-biome cities share
    # one dungeon depth (2026-11-04), so counting city records would let two
    # entrances of the same dungeon satisfy this gate.
    from leveling import get_biomes_cleared_to_cap
    if len(get_biomes_cleared_to_cap(player, 20)) < 2:
        return False

    # Condition 2: Looking Glass Shard in inventory
    has_shard = any(
        item.get("id") == "looking_glass_shard"
        for item in player.get("inventory", [])
    )
    if not has_shard:
        return False

    return True


def trigger_wonderland_unlock(player):
    """Display the Wonderland unlock event and set the flag.

    Returns the formatted event text so callers can display it.
    Call this once on the player's next city visit after conditions are met.
    """
    player["wonderland_unlocked"] = True

    lines = [
        "",
        "=" * 56,
        "  \u2728  A SHIMMERING PORTAL HAS APPEARED  \u2728",
        "=" * 56,
        "",
        '  "A shimmering portal has appeared in the Veilholt forest.',
        "   The locals whisper of a realm that exists between",
        '   pages \u2014 Wonderland."',
        "",
        "   (Visit the Veilholt Arcane Tower to investigate.)",
        "",
        "=" * 56,
    ]
    return "\n".join(lines)


# ── Day rollover (called by advance_time) ───────────────────────────────

def process_day_rollover(player, days_passed, old_day):
    """
    Process events for every day that passed during a time advance.
    Effects are applied immediately so the game world reacts.
    Returns the list of events that were triggered.
    """
    all_events = []

    for offset in range(1, days_passed + 1):
        day = old_day + offset
        # Clear yesterday's daily effects
        player["daily_effects"] = {}
        # Blessed Wind (+all stats) wears off at the day change
        player["active_buffs"] = [
            b for b in player.get("active_buffs", [])
            if b.get("type") != "daily_buff"
        ]
        events = check_events_for_day(day)
        for evt in events:
            apply_event_effects(player, evt)
            record_event(player, evt)  # Store in journal for GUI display
            all_events.append(evt)

    # ── Wild dungeons: weekly spawn cycle (docs/wild_dungeon_design.md) ──
    # Expires overdue dungeons and rolls 3-7 new ones every 7 game days.
    # Idempotent — a cycle already rolled this week does not roll again.
    from wild_dungeons import maybe_spawn_cycle
    _, spawn_event = maybe_spawn_cycle(player)
    if spawn_event:
        all_events.append(spawn_event)

    return all_events
