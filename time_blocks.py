"""time_blocks.py — Block-based time engine (docs/time_system_design.md, rev 3.2).

A day is **24 blocks** across three phases (60 min each):
    Morning (blocks 0–7) · Noon (8–15) · Night (16–23)

Time only moves when the player acts. This module is the switchover target
for `utils.advance_time`: while the legacy wall clock is still live, these
functions are **dormant** (nothing in the game calls them yet) and
`tests/_diag_block_time.py` exercises them standalone.

Key rules (rev 3 design):
  - Cost: ≤15 min free, 16–90 min = 1 block, 91+ min = 2 blocks.
  - Overflow: a cost may exceed the remaining day — the excess eats the
    next day's blocks (the day rolls at the boundary).
  - A day ends by Sleep (Night only, clears fatigue) or by exhaustion
    (24 blocks spent → +1 fatigue stack, cap 3).
  - Fatigue stacks accrue everywhere — including Pandemonium (rev 3.5) —
    except inside Event Horizon runs.
  - Wonderland is a **time pocket**: block costs are nullified and the
    outside day is untouched (exit shows the same day/blocks as entry).
  - Wait ("a brief moment") passes **one block** at any phase; waiting
    "a while" passes to the next phase — from Night it greets the
    morning unslept (+1 fatigue; §6).

Compatibility: `time_minutes` is kept as a derived value for legacy
readers (day starts 06:00, block = 60 min — the legacy clock stays coherent).
"""

DAY_BLOCKS = 24
BLOCKS_PER_PHASE = 8
MINUTES_PER_BLOCK = 60
DAY_MINUTES = 1440
DAY_START_MINUTES = 360          # block 0 == 06:00 (Morning)
FREE_MINUTES = 15                # ≤ this costs nothing
STANDARD_MINUTES = 90            # 16–90 = 1 block; 91+ = 2 blocks
MAX_FATIGUE = 3

# (id, icon) in day order — Morning / Noon / Night
PHASES = (("morning", "☀"), ("noon", "🌤"), ("night", "🌙"))
PHASE_ORDER = {pid: idx for idx, (pid, _icon) in enumerate(PHASES)}
ALL_PHASES = ("morning", "noon", "night")

# ── Default service hours (docs/time_system_design.md §9) ───────────────────
# Template only — cities may override (per-city flavor, confirmed). Missing
# services are always open (inn, house, guild).
SERVICE_DEFAULT_HOURS = {
    "shop":          ("morning", "noon"),
    "blacksmith":    ("morning", "noon"),
    "herbalist":     ("morning", "noon"),
    "temple":        ("morning", "noon"),
    "arcane_tower":  ALL_PHASES,   # towers keep working into the night
    "barracks":      ("morning", "noon"),
    "gift_shop":     ("morning", "noon"),
    "trade_hall":    ("morning", "noon"),
    "shipyard":      ("morning", "noon"),
    "star_tower":    ("noon", "night"),
    "black_market":  ("night",),
}


# ── Cost conversion ─────────────────────────────────────────────────────────

def blocks_for_minutes(minutes):
    """Convert a legacy minute cost into block cost (table in §4).

    Sleep (480) is handled by callers via end_day() — this converter clamps
    everything above STANDARD_MINUTES to 2 blocks by design.
    """
    try:
        minutes = int(minutes or 0)
    except (TypeError, ValueError):
        minutes = 0
    if minutes <= FREE_MINUTES:
        return 0
    if minutes <= STANDARD_MINUTES:
        return 1
    return 2


# ── Travel pricing (rev 3.2 — playtest 2026-10-13) ──────────────────────────
# Travel has its OWN conversion — one block per STARTED 30 minutes
# (30min -> 3, 40min -> 4, 220min -> 10) PLUS a flat +2 supply overhead per
# hop (pacing: even short trips should matter; mount shaves cancel it),
# minimum 1 block. Mounts shave blocks by tier // 2 (T2/T3 -1, T4 -2; T1 -0)
# and KEEP their encounter mitigation either way. Rain adds +1 block, heavy
# rain +2; tier 3+ mounts ignore plain rain and take only +1 from heavy rain.

TRAVEL_MINUTES_PER_BLOCK = 30
TRAVEL_MIN_BLOCKS = 1
TRAVEL_SUPPLY_OVERHEAD = 2       # flat per-hop supplies/pacing cost (rev 3.2)


def travel_blocks_for(minutes, mount_tier=0, rain=0):
    """Travel cost in blocks: ceil(min/30) + 2 supply, mount shave, then rain.

    rain: 0 = clear, 1 = rain (+1), 2 = heavy rain (+2);
    tier 3+ mounts take only +1 from heavy rain (plain rain ignored).
    """
    try:
        minutes = int(minutes or 0)
    except (TypeError, ValueError):
        minutes = 0
    if minutes <= 0:
        return 0

    blocks = max(TRAVEL_MIN_BLOCKS,
                 -(-minutes // TRAVEL_MINUTES_PER_BLOCK)  # ceil division
                 + TRAVEL_SUPPLY_OVERHEAD)
    try:
        tier = int(mount_tier or 0)
    except (TypeError, ValueError):
        tier = 0
    blocks = max(TRAVEL_MIN_BLOCKS, blocks - tier // 2)
    try:
        rain = max(0, int(rain or 0))
    except (TypeError, ValueError):
        rain = 0
    if rain:
        if tier >= 3:
            blocks += 1 if rain >= 2 else 0
        else:
            blocks += rain
    return blocks


def travel_rain_level(player):
    """Current rain level for travel pricing: 0 clear, 1 rain, 2 heavy rain.

    Reads `daily_effects["rain_level"]`; falls back to the legacy
    `travel_time_mult` value so existing events keep working mid-migration
    (>= +25% counts as heavy rain).
    """
    eff = (player or {}).get("daily_effects", {}) or {}
    try:
        lvl = int(eff.get("rain_level", 0) or 0)
    except (TypeError, ValueError):
        lvl = 0
    if lvl:
        return min(2, max(0, lvl))
    try:
        mult = float(eff.get("travel_time_mult", 1.0) or 1.0)
    except (TypeError, ValueError):
        mult = 1.0
    if mult >= 1.25:
        return 2
    if mult > 1.0:
        return 1
    return 0


def travel_blocks(player, minutes):
    """Player-aware travel cost: pulls mount tier and rain level itself."""
    tier = 0
    mount_id = (player or {}).get("mount_id")
    if mount_id:
        try:
            from resources.mounts import get_mount
            mount = get_mount(mount_id)
            tier = int(mount.get("tier", 0)) if mount else 0
        except Exception:
            tier = 0
    return travel_blocks_for(minutes, mount_tier=tier,
                             rain=travel_rain_level(player))


# ── Phase / display helpers ─────────────────────────────────────────────────

def _blocks_of(player_or_blocks):
    if isinstance(player_or_blocks, dict):
        try:
            return int(player_or_blocks.get("day_blocks", 0) or 0)
        except (TypeError, ValueError):
            return 0
    try:
        return int(player_or_blocks or 0)
    except (TypeError, ValueError):
        return 0


def get_day_phase(player_or_blocks):
    """Return 'morning' | 'noon' | 'night' for a player dict or block count."""
    blocks = max(0, min(DAY_BLOCKS - 1, _blocks_of(player_or_blocks)))
    return PHASES[min(2, blocks // BLOCKS_PER_PHASE)][0]


def blocks_remaining(player):
    """Blocks left today (0–24)."""
    return max(0, DAY_BLOCKS - _blocks_of(player))


def format_block_track(player, include_day=True):
    """Compact display track, e.g. `☀ Morning ▮▮▯▯ · Day 12`.

    Pips are the *remaining* blocks of the current phase (drain as time
    passes); the day counter comes from the player dict. Wonderland is a
    time pocket: no track at all (returns "") — the whimsical flavor day
    line carries the display instead (docs §7, rev 3.4).
    """
    if (player or {}).get("wonderland_active"):
        return ""
    blocks = max(0, min(DAY_BLOCKS - 1, _blocks_of(player)))
    phase_idx = min(2, blocks // BLOCKS_PER_PHASE)
    name, icon = PHASES[phase_idx]
    spent_in_phase = blocks % BLOCKS_PER_PHASE
    pips = "▮" * (BLOCKS_PER_PHASE - spent_in_phase) + "▯" * spent_in_phase
    text = f"{icon} {name.title()} {pips}"
    stacks = get_fatigue_stacks(player)
    if stacks > 0:
        roman = {1: "I", 2: "II", 3: "III"}.get(stacks, str(stacks))
        text += (" · \U0001F441 FATIGUE " if stacks >= 2 else " · FATIGUE ") + roman
    if include_day:
        text += f" · Day {player.get('day', 1)}"
    return text


def get_fatigue_stacks(player):
    try:
        return max(0, min(MAX_FATIGUE, int(player.get("fatigue_stacks", 0) or 0)))
    except (TypeError, ValueError):
        return 0


def get_fatigue_penalty(player):
    """All-stat penalty from fatigue (−N where N = stacks)."""
    return -get_fatigue_stacks(player)


# ── Service hours (§9) ──────────────────────────────────────────────────────

def service_hours_for(service, city_id=None):
    """Opening phases for a service: city override → config 'hours' → defaults."""
    try:
        from resources.cities import CITIES
        city = CITIES.get(city_id or "", {}) or {}
        overrides = city.get("service_hours") or {}
        if service in overrides:
            return tuple(overrides[service])
        cfg = city.get(service)
        if isinstance(cfg, dict) and "hours" in cfg:
            return tuple(cfg["hours"])
    except Exception:
        pass
    return SERVICE_DEFAULT_HOURS.get(service, ALL_PHASES)


def is_service_open(player, service, city_id=None):
    """True while the service's phase schedule includes the current phase.

    Wonderland is a time pocket: opening hours don't apply — every service
    is open (docs §7/§9, rev 3.4).
    """
    if (player or {}).get("wonderland_active"):
        return True
    hours = service_hours_for(service, city_id)
    if len(hours) >= len(ALL_PHASES):
        return True
    return get_day_phase(player) in hours


def service_closed_message(player, service, city_id=None):
    """Human-readable closed message, or None when the service is open."""
    if is_service_open(player, service, city_id):
        return None
    hours = service_hours_for(service, city_id)
    cur = PHASE_ORDER.get(get_day_phase(player), 0)
    later = sorted((h for h in hours if PHASE_ORDER.get(h, -1) > cur),
                   key=lambda h: PHASE_ORDER[h])
    if later:
        return f"Closed — opens at {later[0]}."
    return "Closed — opens tomorrow morning."


# ── Time-advance listener (top-bar refresh at switchover) ───────────────────

_time_listeners = []


def register_time_listener(fn):
    """Register a callback(player) invoked after the clock state changes."""
    if fn not in _time_listeners:
        _time_listeners.append(fn)


def _notify_time_advanced(player):
    for fn in list(_time_listeners):
        try:
            fn(player)
        except Exception:
            pass


# ── Compatibility sync ──────────────────────────────────────────────────────

def _sync_minutes(player):
    """Keep legacy `time_minutes` coherent (block 0 == 06:00)."""
    player["time_minutes"] = (DAY_START_MINUTES
                              + _blocks_of(player) * MINUTES_PER_BLOCK) % DAY_MINUTES


def migrate_legacy_time_to_blocks(player):
    """Derive `day_blocks` from legacy `time_minutes` once (switchover).

    Runs exactly once per save (marker `time_blocks_migrated`); new games
    created after the switchover should set the marker themselves.
    """
    if player.get("time_blocks_migrated"):
        return
    try:
        minutes = int(player.get("time_minutes", 8 * 60) or 0)
    except (TypeError, ValueError):
        minutes = 8 * 60
    try:
        day = int(player.get("day", 1) or 1)
    except (TypeError, ValueError):
        day = 1
    if day <= 1:
        # Brand-new saves start at Morning; a legacy day-1 clock offset is
        # not worth preserving.
        player["day_blocks"] = 0
    else:
        player["day_blocks"] = max(0, min(DAY_BLOCKS - 1,
                                          minutes // MINUTES_PER_BLOCK))
    player["fatigue_stacks"] = get_fatigue_stacks(player)
    player["time_blocks_migrated"] = True


# ── Day rollover ────────────────────────────────────────────────────────────

def _fatigue_suppressed(player):
    """Fatigue stacks don't accumulate inside Event Horizon runs (§10).

    Pandemonium accrues fatigue as of rev 3.5 (player call) — only EH's
    frozen clock keeps stacks out.
    """
    try:
        from event_horizon import in_run
        return bool(in_run(player))
    except Exception:
        return False


def _apply_day_rollover(player, days_passed, old_day):
    """Day-transition processing (events, bounties, billing, dispatch).

    Deliberately mirrors `utils.advance_time`'s rollover block; the
    switchover batch deletes the duplicate there and delegates here.
    """
    from events import process_day_rollover, display_event_alert, queue_event_alerts
    events = process_day_rollover(player, days_passed, old_day)

    if events:
        # GUI mode: always queue — the Event Notice popup surfaces them
        # (city entry / safe moments). Terminal: dungeon queues, others print.
        try:
            import tkinter as tk
            gui_mode = bool(tk._default_root and tk._default_root.winfo_exists())
        except Exception:
            gui_mode = False
        if player.get("location") == "dungeon" or gui_mode:
            queue_event_alerts(player, events)
        else:
            for evt in events:
                display_event_alert(evt)

    # Bounty expiry after day rollover
    from facilities.guild import check_bounty_expiry
    expired = check_bounty_expiry(player)
    if expired:
        from events import ensure_journal
        ensure_journal(player)
        day = player.get("day", 1)
        for b in expired:
            player["journal"]["events"].append({
                "day": day,
                "name": "Bounty Expired",
                "desc": f"Bounty for {b['target_name']} expired (deadline passed).",
                "tag": "[BOUNTY]",
                "fixed": False,
            })

    # Monthly maintenance billing (1st of each month)
    from events import get_month_day, record_event
    from facilities.monthly_billing import process_monthly_billing
    month_boundaries = [
        old_day + offset
        for offset in range(1, days_passed + 1)
        if get_month_day(old_day + offset)[1] == 1
    ]
    for bill_day in month_boundaries:
        bill = process_monthly_billing(player, bill_day)
        if bill:
            record_event(player, bill)
            try:
                import tkinter as tk
                gui_mode = bool(tk._default_root and tk._default_root.winfo_exists())
            except Exception:
                gui_mode = False
            if player.get("location") == "dungeon" or gui_mode:
                queue_event_alerts(player, [bill])
            else:
                display_event_alert(bill)

    # Dispatch: resolve returns + nightly recovery
    if player.get("dispatch"):
        from facilities.dispatch import process_dispatch_progress
        process_dispatch_progress(player, days_passed)


def end_day(player, slept):
    """End the current day now.

    slept=True (inn/home Sleep) clears all fatigue stacks; exhaustion
    (slept=False) adds one, unless suppressed (Event Horizon only).
    Wonderland is a time pocket — the outside day is untouched.
    """
    if player.get("wonderland_active"):
        return
    old_day = int(player.get("day", 1) or 1)
    player["day"] = old_day + 1
    player["day_blocks"] = 0
    if slept:
        player["fatigue_stacks"] = 0
    elif not _fatigue_suppressed(player):
        player["fatigue_stacks"] = min(MAX_FATIGUE, get_fatigue_stacks(player) + 1)
    _sync_minutes(player)
    _apply_day_rollover(player, 1, old_day)
    _notify_time_advanced(player)


# ── Spending blocks ─────────────────────────────────────────────────────────

def spend_blocks(player, blocks, source=None):
    """Spend action blocks. Returns the number of days rolled (0 = same day).

    Overflow (confirmed rule): if the cost exceeds the remaining blocks,
    the day rolls at the boundary and the excess is deducted from the next
    day's blocks. Wonderland nullifies costs entirely.
    """
    try:
        blocks = int(blocks or 0)
    except (TypeError, ValueError):
        blocks = 0
    if blocks <= 0 or player.get("wonderland_active"):
        return 0

    # Defensive defaults for raw dicts (tests, legacy flows)
    player.setdefault("day_blocks", 0)
    player.setdefault("fatigue_stacks", 0)
    player.setdefault("day", 1)

    days_rolled = 0
    remaining = DAY_BLOCKS - _blocks_of(player)
    while blocks > 0:
        if blocks < remaining:
            player["day_blocks"] = _blocks_of(player) + blocks
            blocks = 0
        else:
            blocks -= remaining
            end_day(player, slept=False)
            days_rolled += 1
            remaining = DAY_BLOCKS

    _sync_minutes(player)
    _notify_time_advanced(player)

    if days_rolled == 0 and player.get("dispatch"):
        # Hour-precise dispatch resolution checks (parity with advance_time)
        from facilities.dispatch import process_dispatch_progress
        process_dispatch_progress(player, 0)
    return days_rolled


# ── Travel spending & camping (§8) ──────────────────────────────────────────

def can_camp(player):
    """Camp capability: a Portable Camp in the bag or the Caravan mount."""
    if (player or {}).get("mount_id") == "caravan":
        return True
    for item in ((player or {}).get("inventory") or []):
        if item.get("id") == "portable_camp":
            return True
    return False


def spend_travel_segment(player, blocks, camp=False):
    """Spend one travel segment's blocks at its completion (§8).

    camp=True: the party camps at the day boundary — the rest of today walks
    away, the night passes as rest (slept=True clears fatigue), and the
    remainder of the segment's blocks come out of the fresh morning.
    camp=False: march on — regular overflow rolls the day (+1 fatigue stack).

    Returns the number of days rolled (0 = still the same day).
    """
    try:
        blocks = int(blocks or 0)
    except (TypeError, ValueError):
        blocks = 0
    if blocks <= 0 or player.get("wonderland_active"):
        return 0

    remaining = DAY_BLOCKS - _blocks_of(player)
    if blocks < remaining:
        return spend_blocks(player, blocks)

    if camp:
        # Walk out the rest of today, camp, resume at morning.
        player["day_blocks"] = DAY_BLOCKS
        _sync_minutes(player)
        end_day(player, slept=True)
        rest = blocks - remaining
        if rest > 0:
            spend_blocks(player, rest)      # remainder on the fresh day
        else:
            _notify_time_advanced(player)
        return 1
    return spend_blocks(player, blocks)


def wait_blocks(player, blocks=1):
    """Wait N blocks (1 by default), at any phase — including Night.

    Day rollover applies the normal exhaustion rule: an unslept day adds
    +1 fatigue, which is exactly how waiting can be used to force a stack
    (playtest 2026-10-13). Wonderland nullifies the spend.
    """
    if player.get("wonderland_active"):
        return 0
    return spend_blocks(player, blocks, source="wait")


def wait_to_next_phase(player):
    """Pass to the next phase — "wait a while" (rev 3.2 playtest wording).

    Spends the current phase's remaining blocks (8 per phase). From Night
    there is no later phase — the wait carries through to the morning and
    the day ends as exhaustion (+1 fatigue outside Pande/EH). Wonderland
    is a time pocket: no-op, returns None.
    """
    if player.get("wonderland_active"):
        return None
    blocks = _blocks_of(player)
    phase_idx = min(2, blocks // BLOCKS_PER_PHASE)
    if phase_idx >= 2:
        end_day(player, slept=False)
        return "morning"
    target = (phase_idx + 1) * BLOCKS_PER_PHASE
    spend_blocks(player, target - blocks, source="wait")
    return PHASES[phase_idx + 1][0]


# ── advance_time (switchover target for utils.advance_time) ─────────────────

def advance_time(player, minutes):
    """Block-model time advance — public-API compatible with utils.advance_time.

    Converts minutes to blocks via the §4 table; whole days (1440+ minutes,
    used by tests / scripted skips) roll the day once per 1440. Sleep is a
    caller-side special path (`end_day(player, slept=True)`), not a 480-min
    advance.
    """
    from utils import format_time  # lazy — utils delegates here at switchover

    if player.get("wonderland_active"):
        # Time pocket: costs nullified; flavor rendering is display-time.
        return format_time(player)

    try:
        minutes = int(minutes or 0)
    except (TypeError, ValueError):
        minutes = 0

    if minutes >= DAY_MINUTES:
        days, rem = divmod(minutes, DAY_MINUTES)
        if rem:
            spend_blocks(player, blocks_for_minutes(rem))
        for _ in range(days):
            end_day(player, slept=False)
    else:
        cost = blocks_for_minutes(minutes)
        spend_blocks(player, cost)
        if cost <= 0 and player.get("dispatch"):
            # Free actions still ran the hour-precise dispatch check before
            # the switchover (spend_blocks skips its check at zero cost).
            from facilities.dispatch import process_dispatch_progress
            process_dispatch_progress(player, 0)

    return format_time(player)
