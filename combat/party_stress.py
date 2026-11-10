"""Combat-driven party stress — the ally-side partner of `time_blocks` stress.

Design: docs/stress_system_design.md (locked 2026-10-30)

Two meters, one source
──────────────────────
* **Player** — `time_blocks.get_stress()/add_stress()` (0–100, converts into
  fatigue stacks). A companion falling in a fight is worth
  `PLAYER_STRESS_PER_FALL` to the player.
* **Companions** — `ally["stress"]` (0–100, same scale). They never convert
  into fatigue; instead high stress wears them down:
    Weary (≥50) −1 all attributes, Frayed (≥75) −2, Burned Out (≥90) −3,
    and a Burned Out companion **refuses to fight** that encounter.

Falls are detected with a combat-scoped marker (`_combat_started_alive`)
instead of patching every knockout site — the engine, AoE helpers, superboss
loops and boss scripts all flip `defeated` in their own way.

Call sites
──────────
* `combat_engine.combat()` / `superboss_common.superboss_combat_loop` →
  `begin_encounter(player)` (settles the previous fight, then refusals).
* `combat_engine._end_combat_with_result()` → `settle_pending_falls(player)`.
* House / inn / camp sleep → `on_party_sleep(player)` (settle + −10 recovery).
"""

import random

# ── Tuning (locked 2026-10-30) ─────────────────────────────────────────────
PLAYER_STRESS_PER_FALL = 34      # a companion falling, per fall
ALLY_STRESS_FALLEN = 34          # the companion who fell
ALLY_STRESS_WITNESS = 20         # every other living companion, per fall
SLEEP_STRESS_RECOVERY = 10       # real sleep, per companion

STRESS_WEARY_MIN = 50            # mirrors facilities/dispatch.stress_band()
STRESS_FRAYED_MIN = 75
STRESS_BURNOUT_MIN = 90
REFUSE_MIN = STRESS_BURNOUT_MIN

# Generic refusal lines — a template may override with
# ENEMIES[key]["dialogue"]["stress_refusal"] ({name} is substituted).
REFUSAL_LINES = (
    "\"I can't. Not again today.\" {name} sits down and will not get up.",
    "{name} looks at the enemy, then at her own hands. \"I'm sorry. I can't stop shaking.\"",
    "{name}: \"Give me one night. One night, and I'll fight anything you point me at.\"",
    "{name} turns away, jaw set. She is done for today.",
    "\"Go on without me,\" {name} says quietly. \"I'd only get someone killed.\"",
    "{name} shakes her head slowly. Whatever nerve she had, it is spent.",
)


# ── Meter helpers ──────────────────────────────────────────────────────────

def _as_int(value, default=0):
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def stress_of(actor):
    """Companion stress, clamped 0–100."""
    return max(0, min(100, _as_int((actor or {}).get("stress", 0))))


def add_ally_stress(ally, amount):
    """Add (or relieve) companion stress; returns the new value."""
    amount = _as_int(amount)
    ally["stress"] = max(0, min(100, stress_of(ally) + amount))
    return ally["stress"]


def stress_band(actor):
    """'calm' | 'weary' | 'frayed' | 'burnout' (dispatch's bands, renamed)."""
    value = stress_of(actor)
    if value >= STRESS_BURNOUT_MIN:
        return "burnout"
    if value >= STRESS_FRAYED_MIN:
        return "frayed"
    if value >= STRESS_WEARY_MIN:
        return "weary"
    return "calm"


def stress_penalty(actor):
    """All-attribute combat penalty: Weary −1, Frayed −2, Burned Out −3."""
    return {"calm": 0, "weary": 1, "frayed": 2, "burnout": 3}[stress_band(actor)]


def stress_tag(actor):
    """Short HUD tag (None while calm). EXH = exhausted, not the Burn status."""
    return {"calm": None, "weary": "WEA", "frayed": "FRY",
            "burnout": "EXH"}[stress_band(actor)]


def is_sitting_out(ally):
    """True while a Burned Out companion has refused this encounter."""
    return bool((ally or {}).get("_stress_sit_out"))


# ── Encounter lifecycle ────────────────────────────────────────────────────

def _ally_list(player):
    return [a for a in (player.get("allies") or []) if isinstance(a, dict)]


def _downed(ally):
    return bool(ally.get("defeated")) or _as_int(ally.get("current_hp", 0)) <= 0


def refusal_line(ally):
    """Template-specific refusal line, else a generic one ({name} filled)."""
    line = None
    try:
        from resources.enemies import ENEMIES
        template = ENEMIES.get(ally.get("key", ""), {}) or {}
        line = (template.get("dialogue") or {}).get("stress_refusal")
    except Exception:
        line = None
    if not line:
        line = random.choice(REFUSAL_LINES)
    return str(line).replace("{name}", str(ally.get("name", "Your companion")))


def begin_encounter(player):
    """Prepare the party for a fight. Returns player-facing message lines.

    1. Settle any falls the previous fight left behind (superboss loops have
       several exits and may not have settled).
    2. Clear the previous encounter's markers.
    3. Burned Out companions refuse this encounter (they sit it out).
    4. Mark everyone still standing so a fall can be detected at settle time.
    """
    messages = settle_pending_falls(player)

    for ally in _ally_list(player):
        ally.pop("_stress_sit_out", None)
        ally.pop("_combat_started_alive", None)

    # Only the front row can refuse — a bench girl has not been asked to fight.
    try:
        from combat.ally import get_active_allies
        front_row = get_active_allies(player)
    except Exception:
        front_row = [a for a in _ally_list(player) if not _downed(a)]
    for ally in front_row:
        if _downed(ally):
            continue
        if stress_of(ally) >= REFUSE_MIN:
            ally["_stress_sit_out"] = True
            messages.append("  " + refusal_line(ally))

    for ally in _ally_list(player):
        if _downed(ally) or is_sitting_out(ally):
            continue
        ally["_combat_started_alive"] = True
    return messages


def settle_pending_falls(player):
    """Charge stress for companions who ended the last fight still down.

    Returns player-facing message lines. Idempotent: the marker is popped,
    so a second call (or a save/load in between) cannot double-charge.
    """
    allies = _ally_list(player)
    fallen = [a for a in allies
              if a.pop("_combat_started_alive", False) and _downed(a)]

    # The encounter is over either way — refusals only last one fight.
    for ally in allies:
        ally.pop("_stress_sit_out", None)

    if not fallen:
        return []

    # Time pockets and frozen clocks carry no stress (matches the player's
    # suppression in time_blocks.add_stress) — the fall still happened, but
    # the meter does not move.
    if player.get("_eh_in_run") or player.get("wonderland_active"):
        return []

    messages = []
    for ally in fallen:
        name = ally.get("name", "Your companion")
        messages.append(f"  {name} fell in the fighting — the party saw it happen.")
        add_ally_stress(ally, ALLY_STRESS_FALLEN)
        for witness in allies:
            if witness is ally or _downed(witness):
                continue
            add_ally_stress(witness, ALLY_STRESS_WITNESS)

    import time_blocks
    gain = PLAYER_STRESS_PER_FALL * len(fallen)
    fatigue_gained = time_blocks.add_stress(player, gain)
    messages.append(f"  Stress +{gain} (now {time_blocks.get_stress(player)}).")
    if fatigue_gained:
        messages.append(f"  The weight of it becomes Fatigue "
                        f"{time_blocks.get_fatigue_stacks(player)}.")
    if time_blocks.is_rattled(player):
        messages.append("  You are rattled — the dark will feel closer tonight.")
    return messages


def on_party_sleep(player):
    """Real sleep: settle outstanding falls, then let the party recover.

    Player stress clears in `time_blocks.end_day(slept=True)`; companions
    only shed `SLEEP_STRESS_RECOVERY` here (house nightly decay handles the
    ones who stay home).
    """
    messages = settle_pending_falls(player)

    # Deed titles: First Page improves real rest recovery.
    from titles import mod as _title_mod
    recovery = SLEEP_STRESS_RECOVERY + int(round(
        SLEEP_STRESS_RECOVERY * _title_mod(player, "rest_heal_pct")))
    rested = 0
    for ally in _ally_list(player):
        if stress_of(ally) <= 0:
            continue
        add_ally_stress(ally, -recovery)
        rested += 1
    if rested:
        messages.append(f"  The party sleeps it off — companion stress "
                        f"−{recovery} ({rested}).")
    return messages
