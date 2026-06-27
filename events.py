import random

# Fixed events keyed by day-of-month (1-30)
FIXED_EVENTS = {
    1:  {
        "id": "new_moon",
        "name": "New Moon Festival",
        "desc": "The guild celebrates the new moon! +25% favor from bounties today.",
        "effect": {"favor_bonus": 0.25},
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
        "desc": "Rain lashes the city. Travel takes 30% longer.",
        "effect": {"travel_time_mult": 1.30},
        "weight": 10,
    },
    {
        "id": "bounty_rush",
        "name": "Bounty Rush",
        "desc": "The guild posts emergency bounties! Bounty rewards are increased by 50% today.",
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
        "desc": "A dark cloud hangs over the city. You feel uneasy...",
        "effect": {"ill_omen": True},
        "weight": 5,
    },
]


# ── Helpers ───────────────────────────────────────────────────────────────

def get_month_day(global_day):
    """Convert a global day counter to (month, day_of_month)."""
    month = (global_day - 1) // 30 + 1
    day_of_month = (global_day - 1) % 30 + 1
    return month, day_of_month


def format_date(player_or_day):
    """Return a compact date string, e.g. 'Day 45 (M2-D15)'."""
    if isinstance(player_or_day, dict):
        day = player_or_day.get("day", 1)
    else:
        day = player_or_day
    month, dom = get_month_day(day)
    return f"Day {day} (M{month}-D{dom})"


# ── Event checking ────────────────────────────────────────────────────────

def _pick_random_event(day):
    """Pick a random event using the day as seed (reproducible per day)."""
    rng = random.Random(day)
    if rng.random() >= 0.20:          # 20% chance for a random event
        return None
    pool = [e for e in RANDOM_EVENT_POOL]
    weights = [e["weight"] for e in pool]
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


def display_event_alert(event):
    """Print a single event directly to the console."""
    print(format_event_alert(event))


def queue_event_alerts(player, events):
    """Store events so they can be shown when the player leaves the dungeon."""
    queue = player.setdefault("event_queue", [])
    queue.extend(events)


def flush_event_queue(player):
    """Display and clear all queued events. Returns count shown."""
    queue = player.pop("event_queue", [])
    if not queue:
        return 0

    print("\n" + "=" * 50)
    print("  [EVENT]  EVENTS WHILE YOU WERE AWAY")
    print("=" * 50)
    for evt in queue:
        print(format_event_alert(evt))
    print("=" * 50)
    input("\nPress Enter to continue...")
    return len(queue)


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
        events = check_events_for_day(day)
        for evt in events:
            apply_event_effects(player, evt)
            all_events.append(evt)

    return all_events
