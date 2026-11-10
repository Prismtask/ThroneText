"""karma.py — global moral axis and single standing score.

City Favor is removed; Karma is the only standing score and follows the player
to every city. It is a per-save rule chosen in the character-creation Game
Rules step. New characters default ON; old saves default OFF. The choice is
final for the save — there is no in-game enable/disable path. Every gameplay
hook must check ``is_enabled(player)`` before changing or displaying Karma.
"""

KARMA_MIN = -100
KARMA_MAX = 100
KARMA_DAILY_CAP = 8
JAIL_KARMA_GAIN = 3
JAIL_KARMA_COOLDOWN_DAYS = 3

# (min_karma, label, buy_pct, bills_pct)
# buy_pct: positive = shop discount, negative = surcharge.
# bills_pct: negative = cheaper monthly bills, positive = more expensive.
KARMA_TIERS = (
    (80, "Paragon", 20, -30),
    (50, "Virtuous", 15, -20),
    (25, "Respected", 10, -10),
    (10, "Good", 5, -5),
    (-9, "Neutral", 0, 0),
    (-24, "Shady", -5, 5),
    (-49, "Suspect", -10, 10),
    (-74, "Wanted", -15, 15),
    (-100, "Outlaw", -20, 20),
)

EXCLUDED_GATE_CITIES = frozenset({"wonderland", "blackwake"})
LAWLESS_CITY = "blackwake"


def is_enabled(player):
    """True when this save has Karma enabled."""
    return bool(player and player.get("karma_enabled", False))


def ensure_state(player):
    """Ensure the Karma fields exist on a player dict (idempotent)."""
    player.setdefault("karma", 0)
    if not isinstance(player.get("karma_log"), list):
        player["karma_log"] = []
    daily = player.get("karma_daily")
    if not isinstance(daily, dict):
        daily = {"day": 0, "gained": 0}
        player["karma_daily"] = daily
    daily.setdefault("day", 0)
    daily.setdefault("gained", 0)
    gate = player.get("karma_gate")
    if not isinstance(gate, dict):
        gate = {}
        player["karma_gate"] = gate
    gate.setdefault("cooldown", {})
    if not isinstance(gate.get("cooldown"), dict):
        gate["cooldown"] = {}
    gate.setdefault("warning_seen", False)
    gate.setdefault("watched_until", 0)
    gate.setdefault("jail_karma_day", -99)
    gate.setdefault("check_pending", False)
    gate.setdefault("atonement_day", -99)


def get_karma(player):
    """Return the clamped Karma score."""
    try:
        value = int(player.get("karma", 0))
    except (TypeError, ValueError):
        value = 0
    return max(KARMA_MIN, min(KARMA_MAX, value))


def get_karma_tier(player):
    """Return the tier dict for the current Karma score."""
    value = get_karma(player)
    for min_karma, label, buy_pct, bills_pct in KARMA_TIERS:
        if value >= min_karma:
            return {
                "min": min_karma,
                "label": label,
                "buy_pct": buy_pct,
                "bills_pct": bills_pct,
            }
    # Defensive fallback; the last tier starts at KARMA_MIN.
    return {"min": KARMA_MIN, "label": "Outlaw", "buy_pct": -20, "bills_pct": 20}


def get_shop_karma_pct(player):
    """Karma's contribution to the shop discount (0 when disabled)."""
    return get_karma_tier(player)["buy_pct"] if is_enabled(player) else 0


def get_bills_mult(player):
    """Multiplier applied to monthly upkeep (1.0 when Karma is disabled)."""
    if not is_enabled(player):
        return 1.0
    mult = 1.0 + (get_karma_tier(player)["bills_pct"] / 100.0)
    return max(0.5, min(1.5, mult))


def is_lawless_city(city_id):
    """Blackwake: no Karma gate, no guards, no jail."""
    return city_id == LAWLESS_CITY


def add_journal(player, name, desc):
    """Append a Karma-tagged Journal entry (used by choices and jail)."""
    player.setdefault("journal", {
        "events": [],
        "main_quests": [],
        "side_quests": [],
    })
    events = player["journal"].setdefault("events", [])
    events.append({
        "day": player.get("day", 1),
        "name": name,
        "desc": desc,
        "tag": "[KARMA]",
        "fixed": False,
    })
    if len(events) > 200:
        del events[:-200]


def change_karma(player, delta, reason, bypass_cap=False):
    """Apply a Karma change and return the actual delta applied.

    Positive changes share the +8/day cap unless ``bypass_cap`` is set for a
    one-time quest/story reward. Negative changes are uncapped.
    """
    if not is_enabled(player) or not delta:
        return 0
    ensure_state(player)

    before = get_karma(player)
    before_tier = get_karma_tier(player)["label"]
    delta = int(delta)
    daily = None

    if delta > 0 and not bypass_cap:
        day = int(player.get("day", 1))
        daily = player["karma_daily"]
        if int(daily.get("day", 0)) != day:
            daily["day"] = day
            daily["gained"] = 0
        remaining = max(0, KARMA_DAILY_CAP - int(daily.get("gained", 0)))
        if remaining <= 0:
            return 0
        delta = min(delta, remaining)

    after = max(KARMA_MIN, min(KARMA_MAX, before + delta))
    actual = after - before
    if actual == 0:
        return 0

    if daily is not None and actual > 0:
        daily["gained"] = int(daily.get("gained", 0)) + actual

    player["karma"] = after
    player["karma_log"].append({
        "day": player.get("day", 1),
        "delta": actual,
        "reason": reason,
        "total": after,
    })
    del player["karma_log"][:-50]

    after_tier = get_karma_tier(player)["label"]
    if after_tier != before_tier:
        add_journal(
            player,
            f"Karma: {after_tier} ({after:+d})",
            f"{reason} — Karma moved from {before_tier} to {after_tier}.",
        )
    # Deed titles: Honest / Unrepentant watch Karma thresholds.
    from titles import check_unlock as _check_title_unlock
    _check_title_unlock(player)
    return actual


def get_daily_positive_remaining(player):
    """Positive Karma still available under today's shared +8 cap."""
    if not is_enabled(player):
        return 0
    ensure_state(player)
    daily = player["karma_daily"]
    day = int(player.get("day", 1) or 1)
    if int(daily.get("day", 0) or 0) != day:
        return KARMA_DAILY_CAP
    return max(0, KARMA_DAILY_CAP - int(daily.get("gained", 0) or 0))


def change_karma_toward_zero(player, delta, reason, bypass_cap=False):
    """Apply a positive Karma change without ever crossing above 0."""
    if delta <= 0:
        return change_karma(player, delta, reason, bypass_cap=bypass_cap)
    current = get_karma(player)
    if current >= 0:
        return 0
    return change_karma(
        player, min(int(delta), -current), reason, bypass_cap=bypass_cap
    )


def get_gate_talkdown_dc(player):
    """DC for talking city guards down: 16 + |Karma| // 10, capped at 30."""
    return min(30, 16 + abs(get_karma(player)) // 10)


def mark_city_arrival(player):
    """Flag the next CityScreen build for a one-shot gate check."""
    if not player:
        return
    ensure_state(player)
    player["karma_gate"]["check_pending"] = True


def enable_karma(player):
    """Legacy/tooling helper — not called by any player-facing screen.

    The character-creation Game Rules step is final for a save. This helper
    remains for save tooling and diagnostics only. Legacy City Favor data is
    deliberately ignored; Karma starts wherever the save's Karma field says.
    """
    if is_enabled(player):
        return False
    ensure_state(player)
    player["karma_enabled"] = True
    add_journal(player, "Karma awakened", "Karma is now active.")
    return True


def get_gate_response(player, city_id):
    """Return the city-gate response dict, or None when no gate applies."""
    if not is_enabled(player):
        return None
    if city_id in EXCLUDED_GATE_CITIES or player.get("_eh_in_run"):
        return None
    ensure_state(player)

    karma = get_karma(player)
    if karma > -25:
        return None

    try:
        day = int(player.get("day", 1) or 1)
    except (TypeError, ValueError):
        day = 1
    cooldown = player["karma_gate"].get("cooldown", {}) or {}
    try:
        quiet_until = int(cooldown.get(city_id, -1) or -1)
    except (TypeError, ValueError):
        quiet_until = -1
    if day < quiet_until:
        return None

    try:
        level = max(1, int(player.get("level", 1) or 1))
    except (TypeError, ValueError):
        level = 1
    if not player["karma_gate"].get("warning_seen"):
        return {"tier": "warning", "fee": 50, "guards": 0, "elite": 0}
    if karma >= -49:
        return {"tier": "suspect", "fee": max(50, level * 10),
                "guards": 0, "elite": 0}
    if karma >= -74:
        return {"tier": "wanted", "fee": max(100, level * 20),
                "guards": 3, "elite": 0}
    return {"tier": "outlaw", "fee": max(200, level * 30),
            "guards": 2, "elite": 2}
