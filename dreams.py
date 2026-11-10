"""Dream events at sleep — Phase 1 runtime.

Design: docs/dream_events_design.md (decisions locked 2026-10-30)

Phase 1 scope
─────────────
* One roll per sleep at home / the inn / camp (20% base + soft pity, D1/D2).
* Boon and burden dreams only — no choices, no story dreams.
* Wonderland and Event Horizon roll nothing (D7); the death path never dreams.
* Every dream writes a ``[DREAM]`` Journal entry. Journal + ``term`` only —
  no toasts, no tkinter from a background thread.

Public API
──────────
``maybe_offer_dream(player, location, term=None, rng=None, pause=False)``
    Called after ``end_day(player, slept=True)`` (house, inn, camp). Returns
    the fired dream dict, or None when the night passed dreamlessly.

``roll_dream(player, location, rng=None)``
    Pool + weighted pick without side effects (testable).

All randomness goes through the injected ``rng`` so tests can seed it.
"""

import random as _random

from resources.dreams import DREAMS, category_of, dream_location_allowed

# ── Tuning (D1, §4.2, §4.4) ─────────────────────────────────────────────────
DREAM_CHANCE = 0.20          # base chance per sleep
PITY_START = 5               # dreamless sleeps before the soft pity starts
PITY_STEP = 0.05             # +5% chance per further dreamless sleep
PITY_CAP = 0.60              # never guaranteed

REPEAT_DECAY = 0.6           # weight x0.6 per previous sighting
REPEAT_FLOOR = 0.2           # ... but never below 20% of the base weight

BURDEN_STRESS_MULT = 2.0     # any party girl at stress >= 60
BURDEN_STRESS_MIN = 60
BURDEN_FATIGUE_MULT = 1.5    # fatigue stacks >= 2
BURDEN_FATIGUE_MIN = 2
BURDEN_NOSPIRAL_MULT = 0.5   # the previous dream was a burden
BOND_MULT = 2.0              # an engaged/married girl is in the party
FRESH_LOCATION_MULT = 1.5    # Memory/Omen dreams, first one in a location

GOLD_LOSS_PCT = 0.05         # D4 — gold is the only stealable resource
GOLD_LOSS_CAP = 50


# ── State ───────────────────────────────────────────────────────────────────

def ensure_state(player):
    """Initialize the dream state block (old-save safe, idempotent)."""
    state = player.setdefault("dreams", {})
    state.setdefault("seen", {})          # dream id -> times seen
    state.setdefault("last_day", 0)       # day the last dream fired
    state.setdefault("streak", 0)         # consecutive dreamless sleeps
    state.setdefault("last_category", None)
    state.setdefault("last_location", None)
    state.setdefault("queue", [])         # queued story-dream ids (§4.5)
    return state


def _dreams_enabled(player):
    """Dreams never fire in Wonderland, Event Horizon, or on the death path."""
    if player.get("wonderland_active") or player.get("_eh_in_run"):
        return False
    return int(player.get("current_hp", 1) or 0) > 0


def _day(player):
    try:
        return int(player.get("day", 1) or 1)
    except (TypeError, ValueError):
        return 1


def _has_flag(player, flag):
    """Quest flag or a top-level story flag (recruitment, boss kills)."""
    flags = (player.get("quests") or {}).get("flags") or {}
    return bool(flags.get(flag) or player.get(flag))


# ── Party helpers ───────────────────────────────────────────────────────────

def _living_party(player):
    return [a for a in (player.get("allies") or [])
            if isinstance(a, dict) and int(a.get("current_hp", 0) or 0) > 0]


def _max_party_stress(player):
    return max((int(a.get("stress", 0) or 0) for a in _living_party(player)),
               default=0)


def _party_has_partner(player):
    engaged = player.get("engaged_girls") or []
    married = player.get("married_girls") or []
    for girl in _living_party(player):
        if girl.get("engaged") or girl.get("married"):
            return True
        if girl.get("key") in engaged or girl.get("key") in married:
            return True
    return False


# ── Eligibility & pool ──────────────────────────────────────────────────────

def _meets_conditions(dream, player, location):
    if not dream_location_allowed(dream, location):
        return False
    cond = dream.get("conditions") or {}

    if _day(player) < int(cond.get("min_day", 0) or 0):
        return False
    for flag in cond.get("flags") or []:
        if not _has_flag(player, flag):
            return False
    for flag in cond.get("not_flags") or []:
        if _has_flag(player, flag):
            return False
    if len(_living_party(player)) < int(cond.get("party_min", 0) or 0):
        return False
    party_race = cond.get("party_race")
    if party_race and not any(str(a.get("race", "")) == str(party_race)
                              for a in _living_party(player)):
        return False

    if dream.get("content_level"):
        from family import get_content_level
        level = get_content_level()
        wanted = dream["content_level"]
        if wanted == "any":
            # "any" = intimacy content is on (fade-to-black or written).
            if level == "off":
                return False
        elif level != wanted:
            return False
    if dream.get("family"):
        from family import family_system_enabled
        if not family_system_enabled(player):
            return False
    return True


def build_pool(player, location="home", rng=None):
    """Return [(dream, weight), ...] for the current context (no side effects)."""
    state = ensure_state(player)
    seen = state.get("seen") or {}
    last_category = state.get("last_category")
    fresh_location = state.get("last_location") != location

    burden_mult = 1.0
    if _max_party_stress(player) >= BURDEN_STRESS_MIN:
        burden_mult *= BURDEN_STRESS_MULT
    if int(player.get("fatigue_stacks", 0) or 0) >= BURDEN_FATIGUE_MIN:
        burden_mult *= BURDEN_FATIGUE_MULT
    if last_category == "burden":
        burden_mult *= BURDEN_NOSPIRAL_MULT
    bond_mult = BOND_MULT if _party_has_partner(player) else 1.0

    pool = []
    for dream in DREAMS:
        # Story dreams are queued beats, never rolled (§4.5).
        if category_of(dream) == "story":
            continue
        if not _meets_conditions(dream, player, location):
            continue
        times_seen = int(seen.get(dream["id"], 0) or 0)
        if dream.get("once") and times_seen > 0:
            continue

        base = max(1.0, float(dream.get("weight", 1) or 1))
        weight = max(base * (REPEAT_DECAY ** times_seen), base * REPEAT_FLOOR)

        category = category_of(dream)
        if category == "burden":
            weight *= burden_mult
        if "affection" in (dream.get("effects") or {}):
            weight *= bond_mult
        if dream.get("new_city_bonus") and fresh_location:
            weight *= FRESH_LOCATION_MULT

        pool.append((dream, weight))
    return pool


def roll_dream(player, location="home", rng=None):
    """Weighted pick from the eligible pool. No state is changed."""
    rng = rng or _random
    pool = build_pool(player, location)
    if not pool:
        return None
    total = sum(weight for _, weight in pool)
    if total <= 0:
        return None
    threshold = rng.random() * total
    running = 0.0
    for dream, weight in pool:
        running += weight
        if threshold < running:
            return dream
    return pool[-1][0]


def dream_chance(player):
    """Base chance plus the soft pity for a run of dreamless sleeps."""
    state = ensure_state(player)
    streak = int(state.get("streak", 0) or 0)
    chance = DREAM_CHANCE
    if streak >= PITY_START:
        chance += PITY_STEP * (streak - PITY_START + 1)
    return min(PITY_CAP, chance)


def journal_entries(player):
    """Seen dreams for the Dream Journal page, in registry order.

    Returns a list of dicts: id, name, category, lines (str), journal, count.
    """
    seen = (player.get("dreams") or {}).get("seen") or {}
    entries = []
    for dream in DREAMS:
        count = int(seen.get(dream["id"], 0) or 0)
        if count <= 0:
            continue
        entries.append({
            "id": dream["id"],
            "name": dream.get("name", "A dream"),
            "category": category_of(dream),
            "lines": " ".join(str(l) for l in (dream.get("lines") or [])),
            "journal": dream.get("journal") or "",
            "count": count,
        })
    return entries


# ── Effects ─────────────────────────────────────────────────────────────────

def _grant_item(player, item_id, count):
    from inventory import add_item_to_inventory
    from resources.items import build_item
    try:
        item = build_item(item_id)
    except KeyError:
        return None
    item["count"] = max(1, int(count or 1))
    if add_item_to_inventory(player, item):
        return f"  Received {item.get('name', item_id)} ×{item['count']}."
    return ("  The gift slips away as you wake — your bag had no room for it.")


def _apply_buff(actor, spec):
    """Merge an effect buff onto an actor (max value / max duration)."""
    from family import grant_sleep_buff
    buff_type = spec.get("type", "dream_blessed")
    rooms = max(1, int(spec.get("rooms", 2) or 2))
    if buff_type == "dream_blessed":
        grant_sleep_buff(actor, buff_type, spec.get("value", 1), rooms)
        return
    buffs = actor.setdefault("active_buffs", [])
    existing = next((b for b in buffs if b.get("type") == buff_type), None)
    if existing is not None:
        existing["value"] = max(float(existing.get("value", 0) or 0),
                                float(spec.get("value", 0) or 0))
        existing["remaining"] = max(int(existing.get("remaining", 0) or 0), rooms)
        return
    buffs.append({"type": buff_type, "stat": spec.get("stat", "all"),
                  "value": spec.get("value", 0), "remaining": rooms})


def _apply_effects(player, dream, effects=None):
    """Apply a dream's effects; return player-facing message lines.

    ``effects`` overrides the dream's own block — choice dreams pass the
    chosen prompt's effects here.
    """
    effects = dream.get("effects") or {} if effects is None else effects
    messages = []
    party = _living_party(player)

    xp = int(effects.get("xp", 0) or 0)
    if xp:
        from leveling import gain_exp
        gain_exp(player, xp)
        messages.append(f"  +{xp} XP.")

    ally_xp = int(effects.get("ally_xp", 0) or 0)
    if ally_xp and party:
        from leveling import gain_exp_ally
        gain_exp_ally(party[0], ally_xp)
        messages.append(f"  {party[0].get('name', 'Your companion')} +{ally_xp} XP.")

    stress = int(effects.get("girl_stress", 0) or 0)
    if stress and party:
        for girl in party:
            girl["stress"] = max(0, min(100, int(girl.get("stress", 0) or 0) + stress))
        messages.append(f"  Party stress {stress:+d}.")

    player_stress = int(effects.get("player_stress", 0) or 0)
    if player_stress:
        import time_blocks
        band_before = time_blocks.stress_band(player)
        gained = time_blocks.add_stress(player, player_stress)
        band_now = time_blocks.stress_band(player)
        detail = f"  Stress {player_stress:+d} (now {time_blocks.get_stress(player)}"
        if band_now != "calm":
            detail += f" · {band_now}"
        messages.append(detail + ").")
        if gained:
            messages.append(f"  The night's weight becomes Fatigue "
                            f"{time_blocks.get_fatigue_stacks(player)}.")
        if band_now == "rattled" and band_before != "rattled":
            messages.append("  You wake rattled — the dark will feel closer tonight.")

    affection = int(effects.get("affection", 0) or 0)
    if affection and party:
        girl = party[0]
        cap = int(girl.get("affection_cap", 200) or 200)
        girl["affection"] = max(0, min(cap, int(girl.get("affection", 30) or 0)
                                      + affection))
        messages.append(f"  {girl.get('name', 'Your companion')} affection "
                        f"{affection:+d} (now {girl['affection']}/{cap}).")

    if effects.get("gold_loss"):
        gold = int(player.get("gold", 0) or 0)
        loss = min(int(gold * GOLD_LOSS_PCT), GOLD_LOSS_CAP, gold)
        if loss > 0:
            player["gold"] = gold - loss
            messages.append(f"  Lost {loss}g.")
        else:
            messages.append("  It found nothing worth taking.")

    buff = effects.get("buff")
    if buff:
        targets = [player] + party if buff.get("target") == "party" else [player]
        for actor in targets:
            _apply_buff(actor, buff)
        buf_type = buff.get("type", "dream_blessed")
        if buf_type == "dream_blessed":
            messages.append(f"  Dream-Blessed: +{buff.get('value', 1)} all stats "
                            f"for {buff.get('rooms', 2)} room(s).")
        elif buf_type == "crit_chance":
            messages.append(f"  Steady hands: +{int(float(buff.get('value', 0)) * 100)}% "
                            f"crit for {buff.get('rooms', 2)} room(s).")

    for entry in effects.get("items") or []:
        msg = _grant_item(player, entry.get("id"), entry.get("count", 1))
        if msg:
            messages.append(msg)

    return messages


def _substitute(line, player, location):
    """Token substitution for dream lines ({name}, {girl}, {location}, {day})."""
    party = _living_party(player)
    girl = party[0].get("name", "A familiar face") if party else "No one"
    return (line
            .replace("{name}", str(player.get("name", "you")))
            .replace("{girl}", str(girl))
            .replace("{location}", str(location))
            .replace("{day}", str(_day(player))))


def _journal(player, dream, messages, choice=None):
    """Append a [DREAM] Journal entry (Journal + log only — no toasts)."""
    try:
        from events import ensure_journal
        ensure_journal(player)
        desc = dream.get("journal") or ""
        if choice == "skipped":
            desc = f"{desc} (let it go)" if desc else "You woke before the dream finished."
        elif choice:
            desc = f"{desc} — {choice}" if desc else str(choice)
        extra = [m.strip() for m in messages if m.strip()]
        if extra:
            desc = f"{desc} ({' '.join(extra)})" if desc else " ".join(extra)
        player["journal"]["events"].append({
            "day": _day(player),
            "name": dream.get("name", "A dream"),
            "desc": desc,
            "tag": "[DREAM]",
            "fixed": False,
        })
    except Exception:
        pass


# ── Choice dreams (Phase 2) ─────────────────────────────────────────────────

def _run_choice(player, dream, term, location, seen_before=0):
    """Play a choice dream. Returns (messages, chosen_option_text).

    Repeatable dreams whose choice was seen before gain a **Skip** option
    (§1: dreams are skippable). Story dreams never reach the random pool and
    are never skipped — they are one-time beats.
    """
    prompts = [p for p in (dream.get("prompts") or []) if p.get("text")]
    if not prompts:
        return _apply_effects(player, dream), None

    options = [_substitute(str(p["text"]), player, location) for p in prompts]
    skip_index = None
    if seen_before > 0 and dream.get("skippable", True):
        skip_index = len(options)
        options.append("Wake up. (let the dream go)")

    choice_idx = term.menu(options, prompt=dream.get("prompt", "What do you do?"),
                           allow_cancel=False, columns=2)
    try:
        choice_idx = int(choice_idx)
    except (TypeError, ValueError):
        choice_idx = 0

    if skip_index is not None and choice_idx == skip_index:
        term.print("  You surface before the dream can finish.")
        return [], "skipped"
    if choice_idx < 0 or choice_idx >= len(prompts):
        choice_idx = 0

    prompt = prompts[choice_idx]
    reply = prompt.get("reply")
    if reply:
        term.print(f"  {_substitute(str(reply), player, location)}")
    messages = _apply_effects(player, dream, prompt.get("effects") or {})
    return messages, str(prompt["text"])


# ── Story-dream queue (§4.5) ────────────────────────────────────────────────
def check_story_triggers(player, location="home"):
    """Queue every eligible story dream. Returns the newly queued ids.

    Story dreams are never rolled; they become part of the queue the moment
    their conditions hold, and the next sleep delivers them. Idempotent —
    a dream already seen or already queued is skipped.
    """
    state = ensure_state(player)
    seen = state.get("seen") or {}
    queue = state.setdefault("queue", [])
    queued = []
    for dream in DREAMS:
        if category_of(dream) != "story":
            continue
        if dream["id"] in seen or dream["id"] in queue:
            continue
        if not _meets_conditions(dream, player, location):
            continue
        queue.append(dream["id"])
        queued.append(dream["id"])
    return queued

def queue_story_dream(player, dream_id):
    """Queue a scripted story dream for the next sleep. Returns True if added."""
    from resources.dreams import get_dream
    if get_dream(dream_id) is None:
        return False
    queue = ensure_state(player).setdefault("queue", [])
    if dream_id in queue:
        return False
    queue.append(dream_id)
    return True


def _pop_queued_story(player):
    """Pop the next deliverable queued dream (skips unknown ids)."""
    from resources.dreams import get_dream
    queue = ensure_state(player).setdefault("queue", [])
    while queue:
        dream = get_dream(queue.pop(0))
        if dream is not None:
            return dream
    return None


# ── Entry point ─────────────────────────────────────────────────────────────

def _deliver(player, dream, location, term, pause=False):
    """Mark the dream seen, play it, apply effects and journal it."""
    state = ensure_state(player)
    seen = state.setdefault("seen", {})
    seen_before = int(seen.get(dream["id"], 0) or 0)

    # ── Mark state BEFORE effects (effects may level up / change the day) ──
    state["streak"] = 0
    state["last_day"] = _day(player)
    state["last_category"] = category_of(dream)
    state["last_location"] = location
    seen[dream["id"]] = seen_before + 1

    # Story dreams may set story flags (design §2.4).
    for flag in dream.get("flags_set") or []:
        player[flag] = True
        try:
            player.setdefault("quests", {}).setdefault("flags", {})[flag] = True
        except Exception:
            pass

    # ── Scene ──
    term.print("")
    term.print("── DREAM ──")
    for line in dream.get("lines") or []:
        term.print(f"  {_substitute(line, player, location)}")
    term.print("")

    choice = None
    if dream.get("prompts"):
        messages, choice = _run_choice(player, dream, term, location, seen_before)
    else:
        messages = _apply_effects(player, dream)
    for msg in messages:
        term.print(msg)
    if messages:
        term.print("")

    _journal(player, dream, messages, choice)
    if pause:
        term.pause("The dream lets you go. Press Continue...")
    return dream


def maybe_offer_dream(player, location="home", term=None, rng=None, pause=False):
    """Roll one dream after a sleep. Returns the dream dict or None.

    ``location`` is "home" | "inn" | "camp". Call this after
    ``time_blocks.end_day(player, slept=True)`` and before the morning pause.
    A queued story dream is delivered before the random roll.
    """
    if term is None:
        from gui.terminal import term as _term
        term = _term
    rng = rng or _random

    state = ensure_state(player)
    if not _dreams_enabled(player):
        return None

    # Story beats queue themselves as soon as their flags hold (§4.5).
    check_story_triggers(player, location)

    dream = _pop_queued_story(player)
    if dream is None:
        if rng.random() >= dream_chance(player):
            state["streak"] = int(state.get("streak", 0) or 0) + 1
            return None
        dream = roll_dream(player, location, rng=rng)
        if dream is None:
            state["streak"] = int(state.get("streak", 0) or 0) + 1
            return None

    return _deliver(player, dream, location, term, pause=pause)
