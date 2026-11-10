# titles.py — deed-title state, unlock checks, and effect reads.
"""Runtime helpers for the titles system (docs/titles_design.md).

The registry is data-only (`resources/titles.py`).  This module owns:
- player state (`titles_unlocked`, `title_active`, `title_stats`, `titles_version`)
- declarative condition evaluation + progress strings
- unlock checks/journal entries and old-save reconciliation
- effect reads (`mod`) and the name honourific (`format_name`).

One title is active at a time.  Unlocks are permanent per save.
"""

from resources.titles import TITLES, TITLES_BY_ID
from resources.cities import CITIES

TITLES_VERSION = 1
MAX_JOURNAL_EVENTS = 200

# Hook-side hard caps (docs/titles_design.md §5.2).  `mod()` clamps here so a
# bad registry entry can never bypass the design budget.
EFFECT_CAPS = {
    "shop_discount_pct": 0.10,
    "black_market_pct": 0.10,
    "travel_time_pct": 0.10,
    "xp_pct": 0.10,
    "capture_pct": 0.10,
    "gold_find_pct": 0.10,
    "bounty_gold_pct": 0.10,
    "upkeep_pct": 0.10,
    "rest_heal_pct": 0.20,
    "damage_pct": 0.04,
    "casino_payout_pct": 0.01,
}

_DEED_LABELS = {
    "gold_spent_shops": "gold spent in shops",
    "travel_segments": "travel segments",
    "floors_cleared": "floors cleared",
    "casino_hands_won": "casino hands won",
    "casino_biggest_win": "biggest casino win",
    "casino_cheats_unseen": "cheats unseen",
    "casino_cheats_caught": "cheats caught",
    "wonderland_shadows_taken": "Wonderland Shadows accepted",
}


def ensure_state(player):
    """Idempotently add title fields to a player dict."""
    if not isinstance(player, dict):
        return player
    player.setdefault("titles_unlocked", {})
    player.setdefault("title_active", None)
    stats = player.setdefault("title_stats", {})
    stats.setdefault("gold_spent_shops", 0)
    stats.setdefault("travel_segments", 0)
    stats.setdefault("casino_hands_won", 0)
    stats.setdefault("casino_biggest_win", 0)
    stats.setdefault("casino_cheats_unseen", 0)
    stats.setdefault("casino_cheats_caught", 0)
    stats.setdefault("wonderland_shadows_taken", 0)
    player.setdefault("titles_version", 0)
    # Old-save safety: a save caught mid-Shadow-cycle already earned the deed
    # even though the lifetime counter did not exist when the Shadow was taken.
    try:
        active_shadows = len(player.get("wonderland_shadows") or [])
    except TypeError:
        active_shadows = 0
    if active_shadows > stats["wonderland_shadows_taken"]:
        stats["wonderland_shadows_taken"] = active_shadows
    return player


def _rule_enabled(player, rule_id):
    """True when a Game Rules toggle is enabled for this save."""
    if not rule_id:
        return True
    try:
        from character import GAME_RULES
        for rule in GAME_RULES:
            if rule.get("id") == rule_id:
                default = rule.get("default_old", False)
                return bool(player.get(rule_id, default))
    except Exception:
        pass
    return bool(player.get(rule_id, False))


def _floors_cleared(player):
    """Distinct floors cleared, summed once per biome.

    Same-biome cities share one dungeon depth (2026-11-04), so counting
    every city record would multiply the same progress.
    """
    best_by_biome = {}
    for city_id, prog in (player.get("city_floors") or {}).items():
        if not isinstance(prog, dict):
            continue
        if city_id in CITIES:
            biome = CITIES[city_id].get("biome", "temperate")
        else:
            biome = f"unknown:{city_id}"
        try:
            depth = max(0, int(prog.get("max_floor", 1) or 1) - 1)
        except (TypeError, ValueError):
            continue
        if depth > best_by_biome.get(biome, -1):
            best_by_biome[biome] = depth
    return sum(best_by_biome.values())


def _deed_value(player, key):
    if key == "floors_cleared":
        return _floors_cleared(player)
    stats = player.get("title_stats") or {}
    try:
        return max(0, int(stats.get(key, 0) or 0))
    except (TypeError, ValueError):
        return 0


def _bestiary_count(player, field, key=None, race=None):
    ledger = player.get("bestiary") or {}
    total = 0
    enemy_data = None
    if race:
        try:
            from resources.enemies import ENEMIES
            enemy_data = ENEMIES
        except Exception:
            enemy_data = {}
    for enemy_key, entry in ledger.items():
        if not isinstance(entry, dict):
            continue
        if key and enemy_key != key:
            continue
        if race:
            template = (enemy_data or {}).get(enemy_key) or {}
            if template.get("race") != race and template.get("secondary_race") != race:
                continue
        try:
            total += max(0, int(entry.get(field, 0) or 0))
        except (TypeError, ValueError):
            continue
    return total


def _has_flag(player, flag):
    """True for a top-level story flag or a quest-runtime flag."""
    if not flag:
        return False
    if player.get(flag):
        return True
    return bool(((player.get("quests") or {}).get("flags") or {}).get(flag))


def _quest_done(player, quest_id):
    state = player.get("quests") or {}
    completed = state.get("completed") or []
    if quest_id in completed:
        return True
    return _has_flag(player, quest_id)


def condition_progress(player, condition):
    """Return (label, current, target) for display, or None.

    Composite conditions show the first unmet part (all) or the first met part
    (any).  This is used only for the locked-card progress line.
    """
    if not condition:
        return None
    ctype = condition.get("type")

    if ctype == "all":
        for sub in condition.get("all") or []:
            prog = condition_progress(player, sub)
            if prog and prog[1] < prog[2]:
                return prog
        return None
    if ctype == "any":
        for sub in condition.get("any") or []:
            prog = condition_progress(player, sub)
            if prog and prog[1] >= prog[2]:
                return prog
        for sub in condition.get("any") or []:
            prog = condition_progress(player, sub)
            if prog:
                return prog
        return None

    if ctype == "deed_stat":
        key = condition.get("key", "")
        target = max(1, int(condition.get("count", 1) or 1))
        return (_DEED_LABELS.get(key, key.replace("_", " ")),
                _deed_value(player, key), target)

    if ctype == "bestiary":
        field = condition.get("field", "defeated")
        target = max(1, int(condition.get("count", 1) or 1))
        race = condition.get("race")
        key = condition.get("key")
        label = field if field in ("defeated", "captured") else "recorded"
        if race:
            label = f"{race} {label}"
        return (label, _bestiary_count(player, field, key=key, race=race), target)

    if ctype == "bounty":
        high = bool(condition.get("high"))
        target = max(1, int(condition.get("count", 1) or 1))
        if high:
            current = int(player.get("high_bounties_completed", 0) or 0)
            return ("high-level contracts", current, target)
        current = int(player.get("bounties_completed", 0) or 0)
        return ("honoured contracts", current, target)

    if ctype == "superboss":
        target = max(1, int(condition.get("count", 1) or 1))
        current = len(player.get("defeated_superbosses") or [])
        return ("superbosses defeated", current, target)

    if ctype == "house_level":
        target = max(1, int(condition.get("level", 1) or 1))
        levels = [int(h.get("level", 1) or 1)
                  for h in (player.get("houses") or {}).values()]
        return ("house level", max(levels) if levels else 0, target)

    if ctype == "children":
        target = max(1, int(condition.get("count", 1) or 1))
        return ("children", len(player.get("children") or []), target)

    if ctype == "level":
        target = max(1, int(condition.get("level", 1) or 1))
        return ("character level", int(player.get("level", 1) or 1), target)

    if ctype == "eh_room":
        target = max(1, int(condition.get("count", 1) or 1))
        current = int((player.get("event_horizon") or {}).get("best_room", 0) or 0)
        return ("Event Horizon room", current, target)

    if ctype == "bestiary_fraction":
        try:
            from bestiary import get_total_enemy_count, is_bestiary_candidate
            total_candidates = max(1, int(get_total_enemy_count()))
            ledger = player.get("bestiary") or {}
            recorded = sum(
                1 for key, entry in ledger.items()
                if isinstance(entry, dict) and is_bestiary_candidate(key)
                and (int(entry.get("defeated", 0) or 0) > 0
                     or int(entry.get("captured", 0) or 0) > 0)
            )
        except Exception:
            total_candidates = 1
            recorded = 0
        try:
            fraction = float(condition.get("fraction", 0.8) or 0.8)
        except (TypeError, ValueError):
            fraction = 0.8
        target = max(1, int(round(total_candidates * fraction)))
        return ("bestiary entries", recorded, target)

    if ctype == "karma":
        target = int(condition.get("at_least", condition.get("at_most", 0)) or 0)
        try:
            from karma import get_karma
            current = int(get_karma(player))
        except Exception:
            current = int(player.get("karma", 0) or 0)
        if "at_most" in condition:
            return ("Karma (toward Outlaw)", current, target)
        return ("Karma", current, target)

    if ctype == "flag":
        flag = condition.get("flag", "")
        label = condition.get("label") or "deed"
        return (label, 1 if _has_flag(player, flag) else 0, 1)

    if ctype == "quest":
        quest_id = condition.get("quest_id", "")
        return ("quest", 1 if _quest_done(player, quest_id) else 0, 1)

    return None


def condition_met(player, condition):
    if not condition:
        return False
    ctype = condition.get("type")
    if ctype == "all":
        return all(condition_met(player, sub)
                   for sub in (condition.get("all") or []))
    if ctype == "any":
        return any(condition_met(player, sub)
                   for sub in (condition.get("any") or []))
    if ctype == "karma" and "at_most" in condition:
        try:
            from karma import get_karma
            current = int(get_karma(player))
        except Exception:
            current = int(player.get("karma", 0) or 0)
        return current <= int(condition.get("at_most", 0) or 0)
    prog = condition_progress(player, condition)
    if prog is None:
        return False
    _label, current, target = prog
    return current >= target


def get_active(player):
    """Return the active title dict, or None (read-only; never mutates).

    Combat calls this for allies too via ``get_effective_attribute``, so it
    must not add player-only fields to ally dicts.
    """
    if not isinstance(player, dict):
        return None
    title_id = player.get("title_active")
    if not title_id:
        return None
    if title_id not in (player.get("titles_unlocked") or {}):
        return None
    return TITLES_BY_ID.get(title_id)


def mod(player, key, default=0.0):
    """Read one numeric effect minus any drawback, capped by design limits.

    Negative values are allowed so a visible drawback (Worldbreaker) can
    intentionally worsen a price without bypassing the positive cap.
    """
    title = get_active(player)
    if not title:
        return default
    try:
        effect = float((title.get("effects") or {}).get(key, 0) or 0)
        drawback = float((title.get("drawbacks") or {}).get(key, 0) or 0)
        value = effect - drawback
    except (TypeError, ValueError):
        return default
    cap = EFFECT_CAPS.get(key)
    if cap is not None:
        value = min(float(cap), value)
    return value


def combat_stat_bonus(player, stat):
    """Flat player-only attribute bonus from the active title (cap +2)."""
    title = get_active(player)
    if not title:
        return 0
    raw = (title.get("effects") or {}).get("combat_stat")
    if not isinstance(raw, dict):
        return 0
    if raw.get("stat") not in ("all", stat):
        return 0
    try:
        value = int(raw.get("value", 0) or 0)
    except (TypeError, ValueError):
        return 0
    return max(0, min(2, value))


def apply_gold_find(player, amount):
    """Apply the active title's dungeon-gold bonus to a gold amount."""
    try:
        amount = int(amount)
    except (TypeError, ValueError):
        return amount
    if amount <= 0:
        return amount
    pct = mod(player, "gold_find_pct")
    if pct <= 0:
        return amount
    return max(1, int(round(amount * (1.0 + pct))))


def format_effect_line(title):
    """Human-readable one-line effect summary for a title dict."""
    if not title:
        return ""
    effects = title.get("effects") or {}
    parts = []
    for key, raw in effects.items():
        if key == "combat_stat":
            if isinstance(raw, dict):
                stat_name = raw.get("stat", "attribute")
                if stat_name == "all":
                    stat_name = "all attributes"
                parts.append(
                    f"+{int(raw.get('value', 0) or 0)} {stat_name}"
                )
            continue
        try:
            value = float(raw)
        except (TypeError, ValueError):
            continue
        if key == "shop_discount_pct":
            parts.append(f"+{round(value * 100)}% shop discount")
        elif key == "black_market_pct":
            parts.append(f"+{round(value * 100)}% Black Market discount")
        elif key == "casino_payout_pct":
            parts.append(f"+{round(value * 100)}% casino payouts")
        elif key == "travel_time_pct":
            parts.append(f"−{round(value * 100)}% travel time")
        elif key == "xp_pct":
            parts.append(f"+{round(value * 100)}% XP")
        elif key == "capture_pct":
            parts.append(f"+{round(value * 100)}% capture chance")
        elif key == "gold_find_pct":
            parts.append(f"+{round(value * 100)}% dungeon gold")
        elif key == "bounty_gold_pct":
            parts.append(f"+{round(value * 100)}% bounty gold")
        elif key == "upkeep_pct":
            parts.append(f"−{round(value * 100)}% monthly bills")
        elif key == "rest_heal_pct":
            parts.append(f"+{round(value * 100)}% rest healing")
        elif key == "damage_pct":
            parts.append(f"+{round(value * 100)}% damage")
        else:
            parts.append(f"{key}: {value}")
    for key, raw in (title.get("drawbacks") or {}).items():
        try:
            value = float(raw)
        except (TypeError, ValueError):
            continue
        if key == "shop_discount_pct":
            parts.append(f"drawback: −{round(value * 100)}% shop discount")
        else:
            parts.append(f"drawback: {key} {value}")
    return " · ".join(parts)


def format_name(player, style="full", show_title=True):
    """Return the player's display name with the equipped title.

    ``player["name"]`` is never modified.  ``compact`` falls back to the base
    name when the combined string would overflow the 31-char combat column.
    """
    base = (player.get("name") or "Adventurer") if isinstance(player, dict) else "Adventurer"
    title = get_active(player) if isinstance(player, dict) else None
    if not show_title or not title:
        return base
    if style == "plain":
        return base
    if style == "compact":
        candidate = f"{base} ({title.get('compact') or title.get('name', '')})"
        return candidate if len(candidate) <= 31 else base
    epithet = (title.get("epithet") or title.get("name") or "").strip()
    return f"{base} {epithet}".strip()


def _add_unlock_journal(player, title):
    journal = player.setdefault("journal", {
        "events": [],
        "main_quests": [],
        "side_quests": [],
    })
    events = journal.setdefault("events", [])
    events.append({
        "day": int(player.get("day", 1) or 1),
        "name": f"Title unlocked — {title['name']}",
        "desc": f"{format_effect_line(title)} · {title.get('description', '')}".strip(" ·"),
        "tag": "[TITLE]",
        "fixed": False,
    })
    if len(events) > MAX_JOURNAL_EVENTS:
        del events[:-MAX_JOURNAL_EVENTS]


def check_unlock(player, event=None):
    """Unlock every title whose condition now holds. Returns new title dicts."""
    ensure_state(player)
    unlocked = player.setdefault("titles_unlocked", {})
    new_titles = []
    for title in TITLES:
        title_id = title["id"]
        if title_id in unlocked:
            continue
        rule = title.get("requires_rule")
        if rule and not _rule_enabled(player, rule):
            continue
        if condition_met(player, title.get("condition") or {}):
            unlocked[title_id] = {
                "day": int(player.get("day", 1) or 1),
                "seen": False,
            }
            _add_unlock_journal(player, title)
            new_titles.append(title)
    return new_titles


def reconcile(player):
    """Backfill unlocks once per ``titles_version`` (old-save safety)."""
    ensure_state(player)
    try:
        current = int(player.get("titles_version", 0) or 0)
    except (TypeError, ValueError):
        current = 0
    if current < TITLES_VERSION:
        player["titles_version"] = TITLES_VERSION
    # Always re-check: unlock state is monotonic and cheap (nine entries),
    # and this repairs saves whose version flag was set but fields were lost.
    return check_unlock(player)


def can_swap(player):
    """False while combat is active (title changes are safe-point only)."""
    if not isinstance(player, dict):
        return False
    if player.get("wedding_combat_active"):
        return False
    if player.get("in_combat"):
        return False
    return True


def equip_title(player, title_id):
    """Equip a previously unlocked title. Returns (ok, message)."""
    ensure_state(player)
    title = TITLES_BY_ID.get(title_id)
    if not title:
        return False, "Unknown title."
    if title_id not in (player.get("titles_unlocked") or {}):
        return False, "That title has not been earned yet."
    rule = title.get("requires_rule")
    if rule and not _rule_enabled(player, rule):
        return False, "That title is unavailable — its game rule is disabled."
    if not can_swap(player):
        return False, "You can't change titles right now."
    player["title_active"] = title_id
    return True, f"Title equipped: {title['name']}."


def unequip_title(player):
    ensure_state(player)
    if not can_swap(player):
        return False, "You can't change titles right now."
    player["title_active"] = None
    return True, "Title removed."


def note_deed(player, key, amount=1):
    """Increment a deed counter and check for unlocks."""
    ensure_state(player)
    stats = player.setdefault("title_stats", {})
    try:
        stats[key] = max(0, int(stats.get(key, 0) or 0) + int(amount))
    except (TypeError, ValueError):
        stats[key] = int(amount)
    return check_unlock(player)


COLLECTION_MILESTONES = ((5, "Acknowledged"), (10, "Renowned"), (15, "Legendary"))


def collection_summary(player):
    """One-line collection milestone summary for the Titles tab."""
    ensure_state(player)
    count = len(player.get("titles_unlocked") or {})
    parts = []
    for needed, label in COLLECTION_MILESTONES:
        mark = "✓" if count >= needed else "—"
        parts.append(f"{label} {needed} {mark}")
    return f"Collection milestones: " + " · ".join(parts)


def _casino_record_line(player):
    """Shared lifetime record for the three gambling titles."""
    casino = player.get("casino") or {}
    stats = player.get("title_stats") or {}
    if not isinstance(casino, dict):
        casino = {}
    if not isinstance(stats, dict):
        stats = {}

    def value(casino_key, title_key):
        try:
            return max(
                0,
                int(casino.get(casino_key, 0) or 0),
                int(stats.get(title_key, 0) or 0),
            )
        except (TypeError, ValueError):
            return 0

    hands_won = value("hands_won", "casino_hands_won")
    biggest_win = value("biggest_win", "casino_biggest_win")
    unseen = value("cheats_unseen", "casino_cheats_unseen")
    caught = value("cheats_caught", "casino_cheats_caught")
    return (
        f"Hands won: {hands_won:,} · Biggest win: {biggest_win:,}g · "
        f"Cheats unseen: {unseen:,} · Caught: {caught:,}"
    )


def list_titles(player):
    """Return registry state for the Journal UI."""
    ensure_state(player)
    unlocked = player.get("titles_unlocked") or {}
    active = player.get("title_active")
    rows = []
    for title in TITLES:
        title_id = title["id"]
        is_unlocked = title_id in unlocked
        rule = title.get("requires_rule")
        available = _rule_enabled(player, rule)
        record_line = ""
        if title.get("record") == "casino":
            record_line = _casino_record_line(player)
        rows.append({
            "id": title_id,
            "name": title["name"] if is_unlocked else "???",
            "epithet": title.get("epithet", ""),
            "tier": int(title.get("tier", 1) or 1),
            "category": title.get("category", "deed"),
            "hint": title.get("hint", ""),
            "description": title.get("description", "") if is_unlocked else "",
            "effect_line": format_effect_line(title) if is_unlocked else "",
            "record_line": record_line,
            "unlocked": is_unlocked,
            "active": is_unlocked and active == title_id,
            "available": available,
            "progress": None if is_unlocked else condition_progress(
                player, title.get("condition") or {}
            ),
        })
    return rows
