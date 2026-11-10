"""casino.py — Tavern and back-room gambling rules (docs/casino_games_design.md).

Phases 1–3:
  * Under & Over (2d6)
  * Blackjack (Hit/Stand)
  * Inn tables and the Black Market back room
  * Stake/level/Karma gates, pot caps, daily net caps, hand limits
  * Back-room cheating and the three casino deed titles

No terminal I/O lives here; the UI is facilities/casino_ui.py.  All
randomness is injectable through ``rng`` so tests/_diag_casino.py can
verify RTP deterministically.
"""

import random

import karma

HANDS_PER_DAY = 12
MINUTES_PER_HAND = 20
MAX_CHEATS_PER_DAY = 2
CHEAT_PAYOUT = 1.30
CHEAT_KARMA_PENALTY = -2
CHEAT_BLACKLIST_DAYS = 7
CHEAT_MAX_CHANCE = 0.70
CHEAT_CAP_NEED = int(round(21 - CHEAT_MAX_CHANCE * 20))  # 7 -> 70%
CHEAT_BASE_DCS = {250: 16, 1000: 18, 2500: 20}

# Tier tuple: (stake, min_level, karma_max)
# karma_max is the highest Karma allowed (None = no Karma gate).  The
# first back-room tier uses -1, i.e. "Karma strictly below 0".
VENUES = {
    "inn": {
        "name": "Tavern Tables",
        "stake_tiers": (
            (25, 1, None),
            (100, 5, None),
            (250, 10, None),
        ),
        "pot_cap": 1000,
        "net_cap": 1000,
        "under_over_pay": 2.20,
        "exact_seven_pay": 5.50,
        "blackjack_pay": 2.00,
        "natural_pay": 2.20,
    },
    "black_market": {
        "name": "The Back Room",
        "stake_tiers": (
            (250, 5, -1),
            (1000, 15, -15),
            (2500, 25, -40),
        ),
        "pot_cap": 10000,
        "net_cap": 5000,
        "under_over_pay": 2.30,
        "exact_seven_pay": 5.75,
        "blackjack_pay": 2.00,
        "natural_pay": 2.20,
    },
}


# ── Player state ────────────────────────────────────────────────────────────

def _as_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def ensure_state(player):
    """Idempotently add/heal the casino save state."""
    if not isinstance(player, dict):
        return {}
    casino = player.get("casino")
    if not isinstance(casino, dict):
        casino = {}
        player["casino"] = casino

    casino["day"] = _as_int(casino.get("day"), 0)
    if casino["day"] <= 0:
        casino["day"] = max(1, _as_int(player.get("day", 1), 1))
    for key in (
        "hands_today", "hands_played", "hands_won", "biggest_win",
        "total_wagered", "total_returned", "cheats_today",
        "cheats_unseen", "cheats_caught",
    ):
        casino[key] = max(0, _as_int(casino.get(key), 0))
    casino["ban_until_day"] = max(0, _as_int(casino.get("ban_until_day"), 0))

    net = casino.get("net")
    if not isinstance(net, dict):
        net = {}
        casino["net"] = net
    for venue in VENUES:
        net[venue] = _as_int(net.get(venue), 0)

    closed = casino.get("closed")
    if not isinstance(closed, dict):
        closed = {}
        casino["closed"] = closed
    for venue in VENUES:
        closed[venue] = bool(closed.get(venue, False))

    # Phase 3: backfill the title counters from lifetime casino stats so old
    # saves reconcile their gambling titles on load.  max() keeps a higher
    # title-side value if one ever exists.
    try:
        title_stats = player.get("title_stats")
        if not isinstance(title_stats, dict):
            title_stats = {}
            player["title_stats"] = title_stats
        for title_key, casino_key in (
            ("casino_hands_won", "hands_won"),
            ("casino_biggest_win", "biggest_win"),
            ("casino_cheats_unseen", "cheats_unseen"),
            ("casino_cheats_caught", "cheats_caught"),
        ):
            title_stats[title_key] = max(
                _as_int(title_stats.get(title_key), 0),
                _as_int(casino.get(casino_key), 0),
            )
    except Exception:
        pass
    return casino


def reset_daily(player):
    """Reset per-day counters when the calendar day changes."""
    casino = ensure_state(player)
    day = max(1, _as_int(player.get("day", 1), 1))
    if _as_int(casino.get("day"), 0) != day:
        casino["day"] = day
        casino["hands_today"] = 0
        casino["cheats_today"] = 0
        casino["net"] = {venue: 0 for venue in VENUES}
        casino["closed"] = {venue: False for venue in VENUES}
    return casino


def hands_remaining(player):
    casino = reset_daily(player)
    return max(0, HANDS_PER_DAY - _as_int(casino.get("hands_today"), 0))


def is_closed(player, venue):
    casino = reset_daily(player)
    return bool((casino.get("closed") or {}).get(venue, False))


# ── Access gates ────────────────────────────────────────────────────────────

def stake_allowed(player, venue, stake):
    """Return (allowed, reason) for a stake at a venue."""
    config = VENUES.get(venue)
    if not config:
        return False, "Unknown table."
    stake = _as_int(stake, -1)
    tier = next((t for t in config["stake_tiers"] if t[0] == stake), None)
    if tier is None:
        return False, "That stake is not offered here."

    _stake, min_level, karma_max = tier
    level = _as_int(player.get("level", 1), 1)
    if level < min_level:
        return False, f"That table needs level {min_level}."

    if karma.is_enabled(player) and karma_max is not None:
        current = karma.get_karma(player)
        if current > karma_max:
            if karma_max == -1:
                return False, "That table is for customers with a little dirt on them (Karma below 0)."
            return False, f"That table needs Karma \u2264 {karma_max}."
    return True, ""


def stake_options(player, venue):
    """Return display rows for every stake tier at a venue."""
    config = VENUES[venue]
    karma_on = karma.is_enabled(player)
    gold = _as_int(player.get("gold", 0), 0)
    rows = []
    for stake, min_level, karma_max in config["stake_tiers"]:
        allowed, reason = stake_allowed(player, venue, stake)
        requirements = []
        if min_level > 1:
            requirements.append(f"L{min_level}")
        if karma_on and karma_max is not None:
            if karma_max == -1:
                requirements.append("Karma < 0")
            else:
                requirements.append(f"Karma \u2264 {karma_max}")
        label = f"{stake:,}g"
        if requirements:
            label += f" ({', '.join(requirements)})"
        if not allowed:
            label += " \u2014 locked"
        elif gold < stake:
            label += f" \u2014 need {stake - gold:,}g more"
        rows.append({
            "stake": stake,
            "allowed": allowed,
            "reason": reason,
            "label": label,
        })
    return rows


def back_room_status(player):
    """Return the back-room access state for the current day."""
    casino = ensure_state(player)
    day = max(1, _as_int(player.get("day", 1), 1))
    ban_until = _as_int(casino.get("ban_until_day"), 0)
    if ban_until > day:
        return {"ok": False, "reason": "blacklisted", "days_left": ban_until - day}

    if karma.is_enabled(player) and karma.get_karma(player) >= 0:
        return {"ok": False, "reason": "karma", "karma": karma.get_karma(player)}

    level = _as_int(player.get("level", 1), 1)
    if level < 5:
        return {"ok": False, "reason": "level", "level": level}
    return {"ok": True}


def back_room_entry_label(player):
    """Label for the Black Market's back-room menu option."""
    status = back_room_status(player)
    if status["ok"]:
        return "Step into the back room"
    if status["reason"] == "blacklisted":
        days = status["days_left"]
        suffix = "day" if days == 1 else "days"
        return f"The back room (closed for {days} more {suffix})"
    return "Ask about the back room"


# ── Cheating (back room only) ──────────────────────────────────────────────

def cheats_remaining(player):
    casino = reset_daily(player)
    return max(0, MAX_CHEATS_PER_DAY - _as_int(casino.get("cheats_today"), 0))


def cheat_stat(player):
    """Effective (DEX + CHA) // 2, including gear/passives."""
    try:
        from combat.stats import compute_player_stats
        _s, _c, dex, _l, _w, cha = compute_player_stats(player)
        return (int(dex) + int(cha)) // 2
    except Exception:
        attrs = player.get("attributes") or {}
        try:
            dex = int(attrs.get("Dexterity", 0) or 0)
            cha = int(attrs.get("Charisma", 0) or 0)
        except (TypeError, ValueError):
            return 0
        return (dex + cha) // 2


def cheat_chance(player, stake):
    """Return (success chance, DEX+CHA stat, effective DC).

    The base DC is 16/18/20 by stake.  The effective DC is raised to
    ``stat + 7`` when needed so the chance never exceeds 70%.
    """
    stat = cheat_stat(player)
    base_dc = CHEAT_BASE_DCS.get(_as_int(stake, 0), 18)
    dc = max(base_dc, stat + CHEAT_CAP_NEED)
    need = dc - stat
    if need <= 1:
        chance = 0.95
    elif need >= 20:
        chance = 0.05
    else:
        chance = (21 - need) / 20.0
    return chance, stat, dc


def begin_cheat(player, venue, stake):
    """Validate and pay for an Under & Over cheat attempt."""
    if venue != "black_market":
        return False, "The inn doesn't deal that way."
    if not back_room_status(player).get("ok"):
        return False, "The back room is closed to you."
    casino = reset_daily(player)
    if _as_int(casino.get("cheats_today"), 0) >= MAX_CHEATS_PER_DAY:
        return False, "The dealer is watching you too closely today."
    ok, message = begin_hand(player, venue, stake)
    if not ok:
        return False, message
    casino["cheats_today"] = _as_int(casino.get("cheats_today"), 0) + 1
    return True, ""


def begin_blackjack_cheat(player, venue):
    """Validate a blackjack cheat. The hand is already staked/counted."""
    if venue != "black_market":
        return False, "The inn doesn't deal that way."
    if not back_room_status(player).get("ok"):
        return False, "The back room is closed to you."
    casino = reset_daily(player)
    if _as_int(casino.get("cheats_today"), 0) >= MAX_CHEATS_PER_DAY:
        return False, "The dealer is watching you too closely today."
    casino["cheats_today"] = _as_int(casino.get("cheats_today"), 0) + 1
    return True, ""


def resolve_cheat(player, venue, stake, rng=None):
    """Roll the DEX+CHA check. Returns the raw cheat result."""
    chance, stat, dc = cheat_chance(player, stake)
    r = rng or random
    roll = r.randint(1, 20)
    if roll == 1:
        success = False
    elif roll == 20:
        success = True
    else:
        success = (roll + stat) >= dc
    return {
        "success": success,
        "roll": roll,
        "stat": stat,
        "dc": dc,
        "chance": chance,
        "payout": stake * CHEAT_PAYOUT if success else 0.0,
    }


def _add_caught_journal(player, karma_lost, days):
    player.setdefault("journal", {"events": [], "main_quests": [], "side_quests": []})
    events = player["journal"].setdefault("events", [])
    desc = f"The dealer caught you cheating at the back-room table. Barred from every back room for {days} days."
    if karma_lost:
        desc = (f"The dealer caught you cheating at the back-room table. Karma {karma_lost:+d}; "
                f"barred from every back room for {days} days.")
    events.append({
        "day": player.get("day", 1),
        "name": "Caught cheating at the back room",
        "desc": desc,
        "tag": "[CASINO]",
        "fixed": False,
    })
    if len(events) > 200:
        del events[:-200]


def _check_title_unlocks(player):
    """Let the deed-title system see the updated casino counters."""
    try:
        from titles import check_unlock as _check
        _check(player)
    except Exception:
        pass


def _record_cheat(player, success):
    """Increment the unseen/caught counters and mirror them to title stats."""
    casino = ensure_state(player)
    if success:
        casino["cheats_unseen"] = _as_int(casino.get("cheats_unseen"), 0) + 1
    else:
        casino["cheats_caught"] = _as_int(casino.get("cheats_caught"), 0) + 1
    try:
        title_stats = player.setdefault("title_stats", {})
        title_stats["casino_cheats_unseen"] = max(
            _as_int(title_stats.get("casino_cheats_unseen"), 0),
            _as_int(casino.get("cheats_unseen"), 0),
        )
        title_stats["casino_cheats_caught"] = max(
            _as_int(title_stats.get("casino_cheats_caught"), 0),
            _as_int(casino.get("cheats_caught"), 0),
        )
    except Exception:
        pass
    _check_title_unlocks(player)
    return casino


def record_cheat_success(player):
    """Record a successful blackjack cheat without settling the hand."""
    _record_cheat(player, True)


def _apply_caught_penalty(player):
    """Blacklist + caught-only Karma + Journal entry. Returns (karma, days)."""
    casino = ensure_state(player)
    day = max(1, _as_int(player.get("day", 1), 1))
    casino["ban_until_day"] = max(
        _as_int(casino.get("ban_until_day"), 0), day + CHEAT_BLACKLIST_DAYS
    )
    days_left = casino["ban_until_day"] - day
    karma_lost = karma.change_karma(
        player, CHEAT_KARMA_PENALTY, "Caught cheating at the back-room tables"
    )
    _add_caught_journal(player, karma_lost, days_left)
    return karma_lost, days_left


def finish_cheat(player, venue, stake, result):
    """Settle an Under & Over cheat, including caught-only penalties."""
    caught = not result.get("success", False)
    _record_cheat(player, not caught)
    settled = finish_hand(player, venue, stake, result.get("payout", 0.0))
    settled["caught"] = caught
    settled["karma_lost"] = 0
    settled["days_left"] = 0
    if caught:
        karma_lost, days_left = _apply_caught_penalty(player)
        settled["karma_lost"] = karma_lost
        settled["days_left"] = days_left
    return settled


def finish_blackjack_cheat(player, venue, stake):
    """Settle a caught blackjack cheat: the hand is lost and penalties apply."""
    _record_cheat(player, False)
    settled = finish_hand(player, venue, stake, 0.0)
    settled["caught"] = True
    karma_lost, days_left = _apply_caught_penalty(player)
    settled["karma_lost"] = karma_lost
    settled["days_left"] = days_left
    return settled


# ── Hand lifecycle ──────────────────────────────────────────────────────────

def begin_hand(player, venue, stake):
    """Validate a hand, deduct the stake, and count it. Returns (ok, message)."""
    casino = reset_daily(player)
    stake = _as_int(stake, -1)
    if stake <= 0:
        return False, "Invalid stake."

    allowed, reason = stake_allowed(player, venue, stake)
    if not allowed:
        return False, reason

    if _as_int(casino.get("hands_today"), 0) >= HANDS_PER_DAY:
        return False, "You've had enough hands for one day."
    if (casino.get("closed") or {}).get(venue):
        return False, "The house has closed this table for the day."

    gold = _as_int(player.get("gold", 0), 0)
    if gold < stake:
        return False, f"You need {stake:,} gold to sit at that table."

    player["gold"] = gold - stake
    casino["hands_today"] = _as_int(casino.get("hands_today"), 0) + 1
    casino["hands_played"] = _as_int(casino.get("hands_played"), 0) + 1
    casino["total_wagered"] = _as_int(casino.get("total_wagered"), 0) + stake
    return True, ""


def finalize_payout(player, venue, raw_payout, stake=None):
    """Apply the title bonus and pot cap. Returns (payout, capped).

    The Gambler adds 1% of the stake to genuine winning payouts (never
    pushes/returns).  Adding a flat stake percentage rather than
    multiplying the payout keeps the back-room blackjack RTP under 97%.
    """
    config = VENUES.get(venue)
    if not config:
        return 0, False
    try:
        payout = max(0.0, float(raw_payout))
    except (TypeError, ValueError):
        payout = 0.0

    # Phase 3 hook: The Gambler's +1% payout.  No title means 0.
    is_win = stake is None or payout > float(stake)
    if player is not None and is_win and stake:
        try:
            from titles import mod as _title_mod
            pct = _title_mod(player, "casino_payout_pct")
            if pct > 0:
                payout += max(1, int(round(float(stake) * pct)))
        except Exception:
            pass

    payout = int(round(payout))
    cap = _as_int(config.get("pot_cap"), 0)
    if payout > cap:
        return cap, True
    return payout, False


def finish_hand(player, venue, stake, raw_payout):
    """Add winnings, update counters/caps, and return a settlement dict."""
    casino = ensure_state(player)
    if venue not in VENUES:
        return {"payout": 0, "capped": False, "won": False, "net": 0, "closed": False}

    stake = _as_int(stake, 0)
    payout, capped = finalize_payout(player, venue, raw_payout, stake)
    player["gold"] = _as_int(player.get("gold", 0), 0) + payout
    delta = payout - stake
    casino["net"][venue] = _as_int(casino["net"].get(venue), 0) + delta
    casino["total_returned"] = _as_int(casino.get("total_returned"), 0) + payout

    won = payout > stake
    if won:
        casino["hands_won"] = _as_int(casino.get("hands_won"), 0) + 1
        net_win = payout - stake
        if net_win > _as_int(casino.get("biggest_win"), 0):
            casino["biggest_win"] = net_win

    # Phase 3 title counters; harmless before the titles exist.
    try:
        title_stats = player.setdefault("title_stats", {})
        title_stats["casino_hands_won"] = max(
            _as_int(title_stats.get("casino_hands_won"), 0),
            _as_int(casino.get("hands_won"), 0),
        )
        title_stats["casino_biggest_win"] = max(
            _as_int(title_stats.get("casino_biggest_win"), 0),
            _as_int(casino.get("biggest_win"), 0),
        )
    except Exception:
        pass
    _check_title_unlocks(player)

    if casino["net"][venue] >= VENUES[venue]["net_cap"]:
        casino["closed"][venue] = True

    return {
        "payout": payout,
        "capped": capped,
        "won": won,
        "net": delta,
        "closed": bool(casino["closed"].get(venue, False)),
    }


# ── Under & Over ────────────────────────────────────────────────────────────

def exact_seven_allowed(venue, stake):
    """Exactly 7 is hidden when its payout would hit the table's pot cap."""
    config = VENUES[venue]
    return float(stake) * config["exact_seven_pay"] <= config["pot_cap"] + 1e-9


def resolve_under_over(stake, bet, venue, rng=None):
    """Roll 2d6 and return the raw payout (before title bonus/pot cap)."""
    config = VENUES[venue]
    r = rng or random
    d1 = r.randint(1, 6)
    d2 = r.randint(1, 6)
    total = d1 + d2

    if bet == "under":
        won = total < 7
        multiplier = config["under_over_pay"]
    elif bet == "over":
        won = total > 7
        multiplier = config["under_over_pay"]
    elif bet == "seven":
        won = total == 7
        multiplier = config["exact_seven_pay"]
    else:
        raise ValueError(f"Unknown Under & Over bet: {bet}")

    return {
        "dice": (d1, d2),
        "total": total,
        "bet": bet,
        "won": won,
        "multiplier": multiplier,
        "payout": stake * multiplier if won else 0.0,
    }


def simulate_under_over(venue, stake, bet, rng=None, player=None):
    """Raw payout for one hand, with title/cap applied."""
    result = resolve_under_over(stake, bet, venue, rng)
    payout, _capped = finalize_payout(player, venue, result["payout"], stake)
    return payout


# ── Blackjack ───────────────────────────────────────────────────────────────

_RANK_LABELS = {11: "J", 12: "Q", 13: "K", 14: "A"}
SUITS = ("♠", "♥", "♦", "♣")


def make_deck(rng=None):
    """One fresh 52-card deck of (rank, suit) cards; ace high."""
    r = rng or random
    deck = [(rank, suit) for suit in SUITS for rank in range(2, 15)]
    r.shuffle(deck)
    return deck


def _rank_of(card):
    """Rank from a (rank, suit) card; plain ints stay supported."""
    if isinstance(card, (tuple, list)) and card:
        return card[0]
    return card


def _card_value(card):
    """Rank value: 2–10 face value, J/Q/K = 10, ace = 11."""
    rank = _rank_of(card)
    if rank == 14:
        return 11
    if rank >= 11:
        return 10
    return rank


def hand_value(cards):
    """Best blackjack total for (rank, suit) cards (ace = 14)."""
    total = sum(_card_value(card) for card in cards)
    aces = sum(1 for card in cards if _rank_of(card) == 14)
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total


def is_soft(cards):
    """True when at least one ace is still counted as 11."""
    total = sum(_card_value(card) for card in cards)
    aces = sum(1 for card in cards if _rank_of(card) == 14)
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return aces > 0 and total <= 21


def format_cards(cards):
    parts = []
    for card in cards:
        if isinstance(card, (tuple, list)) and len(card) >= 2:
            rank, suit = card[0], card[1]
            parts.append(f"{_RANK_LABELS.get(rank, str(rank))}{suit}")
        else:
            parts.append(_RANK_LABELS.get(card, str(card)))
    return " ".join(parts)


def hand_description(cards):
    total = hand_value(cards)
    if total > 21:
        return f"{format_cards(cards)} = bust ({total})"
    soft = " soft" if is_soft(cards) else ""
    return f"{format_cards(cards)} = {total}{soft}"


def deal_blackjack(rng=None):
    deck = make_deck(rng)
    return deck, [deck.pop(), deck.pop()], [deck.pop(), deck.pop()]


def dealer_should_hit(cards):
    """Dealer hits while below 17 and stands on all 17s."""
    return hand_value(cards) < 17


def dealer_play(deck, dealer_cards):
    """Dealer hits to 17 and stands on all 17s."""
    cards = list(dealer_cards)
    while dealer_should_hit(cards):
        cards.append(deck.pop())
    return cards


def resolve_blackjack(stake, player_cards, dealer_cards, venue):
    """Return the raw payout (before title bonus/pot cap)."""
    config = VENUES[venue]
    player_total = hand_value(player_cards)
    dealer_total = hand_value(dealer_cards)
    player_natural = len(player_cards) == 2 and player_total == 21
    dealer_natural = len(dealer_cards) == 2 and dealer_total == 21
    tie_multiplier = 0.5 if venue == "inn" else 1.0

    result = {
        "player_total": player_total,
        "dealer_total": dealer_total,
        "player_natural": player_natural,
        "dealer_natural": dealer_natural,
        "multiplier": 0.0,
        "payout": 0.0,
    }

    if player_total > 21:
        result["outcome"] = "bust"
        return result

    if player_natural and dealer_natural:
        result["outcome"] = "tie"
        result["multiplier"] = tie_multiplier
        result["payout"] = stake * tie_multiplier
        return result

    if player_natural:
        result["outcome"] = "natural"
        result["multiplier"] = config["natural_pay"]
        result["payout"] = stake * config["natural_pay"]
        return result

    if dealer_natural:
        result["outcome"] = "dealer_natural"
        return result

    if dealer_total > 21:
        result["outcome"] = "dealer_bust"
        result["multiplier"] = config["blackjack_pay"]
        result["payout"] = stake * config["blackjack_pay"]
        return result

    if player_total > dealer_total:
        result["outcome"] = "win"
        result["multiplier"] = config["blackjack_pay"]
        result["payout"] = stake * config["blackjack_pay"]
        return result

    if player_total < dealer_total:
        result["outcome"] = "lose"
        return result

    result["outcome"] = "tie"
    result["multiplier"] = tie_multiplier
    result["payout"] = stake * tie_multiplier
    return result


def basic_policy(player_cards, dealer_upcard=None):
    """Fixed Hit/Stand basic strategy (no double/split/surrender).

    Hard 13–16 stands vs dealer 2–6; hard 12 stands vs 4–6; soft 18
    stands vs dealer 2–8; everything else below 17 hits.  Used by the
    RTP simulation.
    """
    total = hand_value(player_cards)
    if total >= 21:
        return "stand"

    up = _card_value(dealer_upcard) if dealer_upcard is not None else 10

    if is_soft(player_cards):
        if total >= 19:
            return "stand"
        if total == 18:
            return "stand" if up <= 8 else "hit"
        return "hit"

    if total >= 17:
        return "stand"
    if 13 <= total <= 16:
        return "stand" if 2 <= up <= 6 else "hit"
    if total == 12:
        return "stand" if 4 <= up <= 6 else "hit"
    return "hit"


def simulate_blackjack(venue, stake, policy=basic_policy, rng=None, player=None):
    """Raw payout for one hand, with title/cap applied."""
    deck, player_cards, dealer_cards = deal_blackjack(rng)

    while hand_value(player_cards) < 21:
        if policy(player_cards, dealer_cards[0]) == "stand":
            break
        player_cards.append(deck.pop())

    if hand_value(player_cards) <= 21:
        dealer_cards = dealer_play(deck, dealer_cards)

    result = resolve_blackjack(stake, player_cards, dealer_cards, venue)
    payout, _capped = finalize_payout(player, venue, result["payout"], stake)
    return payout
