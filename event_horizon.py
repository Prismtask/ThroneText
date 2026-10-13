"""event_horizon.py — the Event Horizon infinite dungeon (docs/event_horizon_design.md).

Phase 1 core: run state, constants, enemy scaling math, flask rolls +
application, trial-card rolls + application, Entropy (pressure + reward
weight), battle-start debuffs, payout math, milestone schedule, and
wipe/strip helpers.

Gating
------
Every COMBAT hook is a no-op unless BOTH hold:
    player["_eh_in_run"]                    (transient, never saved)
    player["event_horizon"]["run_active"]   (persistent run state)

The transient flag is popped before saves and defensively scrubbed in
`save_load.load_game` / `utils.apply_death_penalty` / city launches
(pandemonium-lesson pattern — see docs/event_horizon_design.md §6.3).

Permanence model
----------------
Flask/card buffs on actors carry ``permanent: True`` and
``remaining: 9999``.  They are never "ticked to death" in practice and are
stripped only by :func:`strip_event_horizon_effects` on run end — so no
changes to the status-effect tick routines are required.
"""

import random

from resources.races_classes import ATTRIBUTES

EH_SOURCE = "event_horizon"

# ── Tunable constants (docs/event_horizon_design.md §12) ────────────────────
EH_UNLOCK_MAX_FLOOR = 20
EH_ENEMY_HP_PER_ROOM = 0.018    # curve cut (playtest 2026-10-07)
EH_ENEMY_DMG_PER_ROOM = 0.013
EH_ENEMY_DEF_PER_ROOM = 0.010
EH_LEVEL_PER_ROOM = 3           # rooms per +1 enemy level
EH_ENEMY_START_LEVEL = 20       # flat room-1 band (decoupled from max_floor)
EH_ENEMY_LEVEL_CAP = 56         # max regular enemy level — band would empty
                                # past this; per-room multipliers carry on
EH_ENEMY_BAND_FLOOR = 30        # band lower edge never rises above this —
                                # capped-depth rooms keep rolling weaker foes
EH_TIME_DIFFICULTY = 1.4        # frozen difficulty baseline inside runs
EH_ENTROPY_START_ROOM = 5
EH_ENTROPY_STEP_STACKS = 20     # stat penalty steps: −3% per full 20 stacks
EH_ENTROPY_STEP_VALUE = 0.03
EH_ENTROPY_CAP = 0.45           # stat penalty cap (reward weight is uncapped)
EH_JOKER_EVERY = 25             # the Joker visits every 25th cleared room
EH_JOKER_HAND_CAP = 7           # arcana a run may hold (throw one to replace)
EH_JOKER_DEAL = 2               # faces dealt per encounter (keep at most one)
EH_TRIAL_ENTROPY_COSTS = {1: 2, 2: 4, 3: 6, 4: 8}
EH_BS_TIER_STEP = 15            # battle-start tier = min(4, 1 + entropy // 15)
EH_BS_SECOND_CHANCE = {1: 0.0, 2: 0.15, 3: 0.30, 4: 0.50}
EH_ENTROPY_AFFLICTION_EVERY = 10  # stacks per random Entropy Affliction
EH_GOLD_BASE = 10
EH_GOLD_PER_ROOM = 2
EH_GOLD_PER_ENTROPY = 0.02      # reward weight per entropy stack (uncapped)
EH_FLASK_TIER_PER_ROOMS = 6     # tier_max = min(7, 1 + room // 6)
EH_TRIAL_EVERY = 5
EH_TRIAL_MIN_ROOM = 10
EH_POSITIVE_TRIAL_EVERY = 15    # positive cadence (was 20, playtest 2026-10-07)
EH_MILESTONE_FLASK_EVERY = 25
EH_MILESTONE_BOON_EVERY = 50
EH_BEATING_ROOT_FIRST = 125     # every 25 past r100, one per milestone per save
EH_BEATING_ROOT_EVERY = 25

# ── Boss Rush (arrival offer — docs §6.4) ───────────────────────────────────
EH_RUSH_MIN_BOSSES = 3          # overworld superbosses felled (pool floor)
EH_RUSH_MIN_BEST_ROOM = 50      # rift depth: deepest run must reach this
EH_RUSH_MIN_MAX_FLOOR = 40      # world progress: Pandemonium F40+ reached
EH_RUSH_MIN_LEVEL = 40          # flat rush level floor ("40+")
EH_RUSH_LEVEL_PER_BOSS = 5      # +5 per echo in the pool
EH_RUSH_LEVEL_PER_PANDEMONIUM = 10  # +10 extra per Pandemonium boss
EH_RUSH_STAT_BASE = 1.25        # rush stats always beat the original fight
EH_RUSH_STAT_PER_LEVEL = 0.03   # +3% stats per level above the 40 floor
EH_RUSH_CLEAR_BONUS_BASE = 100  # full-circuit gold bonus
EH_RUSH_CLEAR_BONUS_PER_BOSS = 25

# Boss Rush — the gathered echoes, ordered by original level (difficulty
# ramp). ``id`` matches the overworld defeat-ledger ids (dungeon.py);
# ``keys`` are ENEMIES keys for the combat HUD; ``module``/``func`` resolve
# lazily. ``pandemonium`` marks the two Pandemonium event bosses (+10).
BOSS_RUSH_ROSTER = [
    {"id": "wl_queen_of_hearts", "name": "Queen of Hearts",
     "keys": ["wl_queen_of_hearts"],
     "module": "combat.queen_of_hearts", "func": "combat_queen_of_hearts"},
    {"id": "dream_devouring_slitcurrent", "name": "Dream-Devouring Slitcurrent",
     "keys": ["dream_devouring_slitcurrent"],
     "module": "combat.slitcurrent", "func": "combat_slitcurrent"},
    {"id": "melt_forge_golem_ignis", "name": "Ignis, the Melt-Forge Golem",
     "keys": ["melt_forge_golem_ignis"],
     "module": "combat.ignis", "func": "combat_ignis"},
    {"id": "queen_of_mirrors_sylvana", "name": "Queen of Mirrors Sylvana",
     "keys": ["queen_of_mirrors_sylvana"],
     "module": "combat.sylvana", "func": "combat_sylvana"},
    {"id": "captain_everlong_ship", "name": "Captain of the Everlong Ship",
     "keys": ["captain_everlong_ship"],
     "module": "combat.everlong_ship", "func": "combat_everlong_ship"},
    {"id": "broodmother_vileheart", "name": "Broodmother Vileheart",
     "keys": ["broodmother_vileheart"],
     "module": "combat.broodmother", "func": "combat_broodmother"},
    {"id": "wl_big_bad_wolf", "name": "Big Bad Wolf",
     "keys": ["wl_big_bad_wolf"],
     "module": "combat.big_bad_wolf", "func": "combat_big_bad_wolf"},
    {"id": "heaven_banished_dragon_yinglong", "name": "Yinglong, Heaven-Banished Dragon",
     "keys": ["heaven_banished_dragon_yinglong"],
     "module": "combat.yinglong", "func": "combat_yinglong"},
    {"id": "rientrante_frostbound", "name": "Rientrante, the Administrator",
     "keys": ["rientrante_frostbound"],
     "module": "combat.rientrante", "func": "combat_rientrante"},
    {"id": "black_silence", "name": "The Black Silence",
     "keys": ["black_silence"],
     "module": "combat.black_silence", "func": "combat_black_silence"},
    {"id": "wl_wicked_witch", "name": "Wicked Witch of the West",
     "keys": ["wl_wicked_witch"],
     "module": "combat.wicked_witch", "func": "combat_wicked_witch"},
    {"id": "chromatic_artisan", "name": "Palette, the Chromatic Artisan",
     "keys": ["chromatic_artisan"],
     "module": "combat.palette_chromatic_artisan", "func": "combat_palette"},
    {"id": "entangled_chrysalis", "name": "Chrysalis, the Entangled One",
     "keys": ["entangled_chrysalis", "temporal_shard_pyre",
              "temporal_shard_pulse", "temporal_shard_ruin"],
     "module": "combat.entangled_chrysalis", "func": "combat_entangled_chrysalis",
     "pandemonium": True},
    {"id": "wl_jabberwock", "name": "The Jabberwock",
     "keys": ["wl_jabberwock"],
     "module": "combat.jabberwock", "func": "combat_jabberwock"},
    {"id": "white_knight", "name": "White Knight of the Fallen Empire",
     "keys": ["white_knight"],
     "module": "combat.white_knight", "func": "combat_white_knight",
     "pandemonium": True},
    {"id": "wl_mary_sue", "name": "Mary Sue",
     "keys": ["wl_mary_sue"],
     "module": "combat.mary_sue", "func": "combat_mary_sue"},
]

# One-time trophy grants by room (docs §10.3/§10.5).
TROPHY_GRANTS = {
    50: "chance_and_choice",
    75: "old_dopo_robe",
    100: "piece_of_relationship",
}


# ═══════════════════════════════════════════════════════════════════════════
# State
# ═══════════════════════════════════════════════════════════════════════════

def _default_state():
    return {
        "run_active": False,
        "room": 0,                 # last cleared room number
        "current_room": None,      # pending room snapshot (Phase 2 suspend/resume)
        "pending_flask": None,     # unconsumed flask awaiting a drinker
        "actor_flasks": {},        # {actor_key: [flask records]} — display log
        "positive_cards": [],
        "negative_cards": [],
        "joker_cards": [],         # accepted Jokers (outside the decks)
        "motes": 0,
        "entropy": 0,
        "trial_done_for": 0,       # last milestone room whose trial was resolved
        "pending_trophies": [],    # trophies awaiting bag space (retried per room)
        "best_room": 0,            # persists ACROSS runs
        "origin_city": "solmere",
        "started_day": 0,
        "entropy_afflictions": [],  # acquired battle-start debuff pool (§2.4)
        # Boss Rush (docs §6.4) — mode + per-run queue; records persist.
        "rush_mode": False,
        "rush_queue": [],          # remaining boss ids (current run)
        "rush_defeated": [],       # boss ids felled this run
        "rush_total": 0,
        "rush_level": 0,           # flat level locked at rush start
        "rush_clears": 0,          # persists ACROSS runs (full circuits)
        "rush_best": 0,            # persists ACROSS runs (most echoes felled)
    }


def ensure_eh_state(player):
    """Guarantee ``player["event_horizon"]`` exists and is complete (migration)."""
    state = player.get("event_horizon")
    if not isinstance(state, dict):
        state = {}
        player["event_horizon"] = state
    for key, value in _default_state().items():
        if key not in state:
            state[key] = value if not isinstance(value, (list, dict)) else type(value)()
    # Mid-run saves from before Entropy Afflictions: backfill the set.
    if state.get("entropy", 0) and not state.get("entropy_afflictions"):
        _sync_entropy_afflictions(state, int(state.get("entropy", 0)))
    # Deck rule (2026-10-07): each (card, tier) is a unique deck entry —
    # collapse only EXACT duplicates (different tiers legitimately stack).
    # Entries without an id (raw/legacy records) are left untouched.
    for key in ("negative_cards", "positive_cards"):
        cards = state.get(key) or []
        if len(cards) < 2:
            continue
        seen = set()
        kept = []
        changed = False
        for c in cards:
            cid = c.get("id")
            if not cid:
                kept.append(c)
                continue
            entry = (cid, int(c.get("tier", 0)))
            if entry in seen:
                changed = True
                continue
            seen.add(entry)
            kept.append(c)
        if changed:
            state[key] = kept
    return state


def in_run(player):
    """True while combat hooks should apply Event Horizon rules."""
    if not player:
        return False
    return bool(player.get("_eh_in_run")) and bool(
        (player.get("event_horizon") or {}).get("run_active")
    )


def actor_key(actor, player):
    """Stable per-actor key for flask logs (mirrors house ``_girl_unique_id``)."""
    if actor is player:
        return "player"
    return f"{actor.get('key', '?')}:{actor.get('name', '?')}"


def get_room(player):
    return int(ensure_eh_state(player).get("room", 0))


# ═══════════════════════════════════════════════════════════════════════════
# Entropy (pressure + reward weight)
# ═══════════════════════════════════════════════════════════════════════════

def base_entropy_for_room(room):
    """+1 stack per cleared room, starting at room EH_ENTROPY_START_ROOM."""
    return max(0, int(room) - (EH_ENTROPY_START_ROOM - 1))


def get_entropy_total(player):
    return int(ensure_eh_state(player).get("entropy", 0))


def entropy_stat_penalty(total):
    """Attribute penalty for `total` Entropy: −3% per full 20 stacks (cap −45%)."""
    steps = int(total) // EH_ENTROPY_STEP_STACKS
    return min(EH_ENTROPY_CAP, steps * EH_ENTROPY_STEP_VALUE)


def sync_entropy(player):
    """Recompute entropy from room + trial costs, then refresh actor entries."""
    state = ensure_eh_state(player)
    # Boss Rush runs are flat (docs §6.4) — no room-count entropy accrues.
    room = 0 if state.get("rush_mode") else int(state.get("room", 0))
    card_cost = sum(int(c.get("entropy_cost", 0)) for c in state.get("negative_cards", []))
    total = base_entropy_for_room(room) + card_cost
    state["entropy"] = total
    penalty = entropy_stat_penalty(total)
    refresh_entropy_entries(player, total, penalty)
    _sync_entropy_afflictions(state, total)
    return total


def refresh_entropy_entries(player, total, penalty):
    """Maintain ONE ``eh_entropy`` debuff entry on the player + every owned ally."""
    actors = [player] + list(player.get("allies", []))
    for actor in actors:
        debuffs = actor.setdefault("active_debuffs", [])
        entry = next((d for d in debuffs if d.get("type") == "eh_entropy"), None)
        if total <= 0 or penalty <= 0:
            if entry is not None:
                debuffs.remove(entry)
            continue
        if entry is None:
            entry = {"type": "eh_entropy", "remaining": -1, "permanent": True}
            debuffs.append(entry)
        entry["stacks"] = total
        entry["value"] = penalty
        entry["source"] = EH_SOURCE


def _alive_active_allies(player):
    """Local helper — avoid importing combat.ally at module scope (cycles)."""
    try:
        from combat.ally import get_active_allies
        actives = [a for a in get_active_allies(player) if a.get("current_hp", 0) > 0]
        if actives:
            return actives
    except Exception:
        pass
    return [a for a in player.get("allies", []) if a.get("current_hp", 0) > 0]


# ═══════════════════════════════════════════════════════════════════════════
# Enemy scaling + negative trial cards
# ═══════════════════════════════════════════════════════════════════════════

def enemy_level_for_room(player, room=None):
    """Enemy pool level for a room: flat start, +1 level per 3 rooms.

    Deliberately ignores the player's ``max_floor`` (docs §2.1, locked
    2026-10-06): every run opens with warm-up opposition and climbs past the
    player's home depth as rooms stack. The per-room HP/DMG/DEF multipliers
    carry scaling after the level cap.
    """
    state = ensure_eh_state(player)
    room = int(state.get("room", 0) if room is None else room)
    level = EH_ENEMY_START_LEVEL + max(0, room - 1) // EH_LEVEL_PER_ROOM
    return max(1, min(EH_ENEMY_LEVEL_CAP, level))


def enemy_band_for_room(player, room=None):
    """``(level, band_lo)`` for spawning: target level + widened band edge.

    The standard picker band is ``[level − (6 + level//10), level + 3]``.
    Once its lower edge would rise past ``EH_ENEMY_BAND_FLOOR`` it stays
    there (locked 2026-10-06), so at capped depth weak stragglers still ride
    along with the elites — variety + breathing room.
    """
    level = enemy_level_for_room(player, room)
    standard_lo = max(1, level - (6 + level // 10))
    return level, min(standard_lo, EH_ENEMY_BAND_FLOOR)


def _negative_card_totals(state):
    """Aggregate active negative cards (trial burdens) into display totals.

    ``hp``/``dmg``/``def``/``ele_dmg`` are multiplicative totals (≥1.0);
    ``status_res``/``regen`` are additive (capped / summed — same math as
    :func:`get_enemy_mods`).
    """
    totals = {"hp": 1.0, "dmg": 1.0, "def": 1.0, "ele_dmg": 1.0,
              "status_res": 0.0, "regen": 0.0}
    for card in state.get("negative_cards", []):
        eff = card.get("effects", {})
        totals["hp"] *= 1.0 + eff.get("hp", 0.0)
        totals["dmg"] *= 1.0 + eff.get("dmg", 0.0)
        totals["def"] *= 1.0 + eff.get("def", 0.0)
        totals["ele_dmg"] *= 1.0 + eff.get("ele_dmg", 0.0)
        totals["status_res"] += eff.get("status_res", 0.0)
        totals["regen"] += eff.get("regen", 0.0)
    totals["status_res"] = min(1.0, totals["status_res"])
    return totals


def trial_burden_tags(player):
    """Compact 'what the trial burdens do' tags for the enemy HUD.

    Playtest 2026-10-06: ``TRL×N`` alone told the player nothing — list the
    active negative-card effects instead (stamped onto each enemy by
    :func:`apply_enemy_scaling`).
    """
    totals = _negative_card_totals(ensure_eh_state(player))
    tags = []
    if totals["hp"] > 1.0:
        tags.append(f"HP+{round((totals['hp'] - 1) * 100)}%")
    if totals["dmg"] > 1.0:
        tags.append(f"DMG+{round((totals['dmg'] - 1) * 100)}%")
    if totals["def"] > 1.0:
        tags.append(f"DEF+{round((totals['def'] - 1) * 100)}%")
    if totals["ele_dmg"] > 1.0:
        tags.append(f"ELE+{round((totals['ele_dmg'] - 1) * 100)}%")
    if totals["status_res"] > 0:
        tags.append(f"RES+{round(totals['status_res'] * 100)}%")
    if totals["regen"] > 0:
        tags.append(f"REG+{round(totals['regen'] * 100)}%")
    return tags


def get_enemy_mods(player):
    """Combined room-scaling + negative-card modifiers for spawned enemies."""
    state = ensure_eh_state(player)
    room = max(1, int(state.get("room", 1) or 1))
    cards = _negative_card_totals(state)
    return {
        "hp": (1.0 + EH_ENEMY_HP_PER_ROOM * (room - 1)) * cards["hp"],
        "dmg": (1.0 + EH_ENEMY_DMG_PER_ROOM * (room - 1)) * cards["dmg"],
        "def": (1.0 + EH_ENEMY_DEF_PER_ROOM * (room - 1)) * cards["def"],
        "status_res": cards["status_res"],
        "ele_dmg": cards["ele_dmg"],
        "regen": cards["regen"],
    }


def apply_enemy_scaling(enemy, player):
    """Hook for ``combat/stats.enemy_stats`` — no-op outside an active run."""
    if not in_run(player):
        return
    # Boss Rush: FLAT scaling keyed to the locked rush level — room progress
    # and trial cards do not apply (docs §6.4).
    if ensure_eh_state(player).get("rush_mode"):
        apply_rush_scaling(enemy, player)
        return
    mods = get_enemy_mods(player)
    enemy["hp"] = max(1, int(enemy.get("hp", 1) * mods["hp"]))
    enemy["max_hp"] = max(1, int(enemy.get("max_hp", 1) * mods["hp"]))
    enemy["str_mod"] = int(enemy.get("str_mod", 0) * mods["dmg"])
    enemy["con_mod"] = int(enemy.get("con_mod", 0) * mods["def"])
    enemy["dex_mod"] = int(enemy.get("dex_mod", 0) * mods["def"])
    enemy["status_res"] = min(1.0, enemy.get("status_res", 0.0) + mods["status_res"])
    if mods["ele_dmg"] != 1.0:
        for el, val in enemy.get("elemental_dmg", {}).items():
            enemy["elemental_dmg"][el] = val * mods["ele_dmg"]
    if mods["regen"] > 0:
        enemy["rift_regen_pct"] = mods["regen"]
    # Trial-burden indicator: stamp the active negative-card count + what the
    # burdens do, so the combat HUD can show "TRL×N: HP+20% DMG+9%" on every
    # rift enemy (docs §2.1, playtest 2026-10-06).
    trial_count = len(ensure_eh_state(player).get("negative_cards") or [])
    if trial_count:
        enemy["_eh_trial_count"] = trial_count
        enemy["_eh_trial_tags"] = trial_burden_tags(player)
    # Wheel of Fortune — luck cuts both ways: the enemy crit cap rises.
    if joker_drawbacks_active(player, "joker_wheel"):
        enemy["_eh_crit_cap"] = 0.24


# ═══════════════════════════════════════════════════════════════════════════
# Boss Rush (docs §6.4)
# ═══════════════════════════════════════════════════════════════════════════

def build_boss_rush_pool(player):
    """Every defeated superboss (overworld ledger), in ramp order.

    Bosses not yet felled in the overworld are skipped entirely — an echo
    only answers for kills the player actually earned.
    """
    kills = set(player.get("defeated_superbosses", []) or [])
    return [dict(b) for b in BOSS_RUSH_ROSTER if b["id"] in kills]


def boss_rush_requirements(player):
    """``(ok, unmet_reasons)`` — minimum-progress gates for the Boss Rush."""
    state = ensure_eh_state(player)
    reasons = []
    pool = build_boss_rush_pool(player)
    if len(pool) < EH_RUSH_MIN_BOSSES:
        reasons.append(f"only {len(pool)} overworld superbosses felled "
                       f"(need {EH_RUSH_MIN_BOSSES})")
    if int(state.get("best_room", 0) or 0) < EH_RUSH_MIN_BEST_ROOM:
        reasons.append(f"deepest rift run is below room {EH_RUSH_MIN_BEST_ROOM}")
    if int(player.get("max_floor", 1) or 1) < EH_RUSH_MIN_MAX_FLOOR:
        reasons.append(f"world progress is below floor {EH_RUSH_MIN_MAX_FLOOR}")
    return (not reasons), reasons


def boss_rush_available(player):
    """True when the arrival scene should offer the Boss Rush."""
    if ensure_eh_state(player).get("run_active"):
        return False        # a suspended/active run claims the seam
    return boss_rush_requirements(player)[0]


def rush_level_for_pool(pool):
    """Flat rush level: 40 + 5/echo + 10 extra per Pandemonium echo."""
    pandemonium = sum(1 for b in pool if b.get("pandemonium"))
    return (EH_RUSH_MIN_LEVEL
            + EH_RUSH_LEVEL_PER_BOSS * len(pool)
            + EH_RUSH_LEVEL_PER_PANDEMONIUM * pandemonium)


def rush_level(player):
    """Stored flat level for the active rush (recomputed if missing)."""
    state = ensure_eh_state(player)
    level = int(state.get("rush_level", 0) or 0)
    if level <= 0:
        level = rush_level_for_pool(build_boss_rush_pool(player))
    return level


def rush_stat_mult(player):
    """Flat stat multiplier for rush enemies — always above the original."""
    level = rush_level(player)
    return (EH_RUSH_STAT_BASE
            + EH_RUSH_STAT_PER_LEVEL * max(0, level - EH_RUSH_MIN_LEVEL))


def apply_rush_scaling(enemy, player):
    """Flat Boss Rush scaling: level = formula, stats × mult (docs §6.4).

    Replaces room/trial scaling for every enemy spawned during a rush —
    minions included, so mid-fight spawns stay proportional.
    """
    level = rush_level(player)
    mult = rush_stat_mult(player)
    original = int(enemy.get("level", 0) or 0)
    enemy["level"] = max(original, level)   # never below the original fight
    enemy["hp"] = max(1, int(enemy.get("hp", 1) * mult))
    enemy["max_hp"] = max(1, int(enemy.get("max_hp", 1) * mult))
    enemy["str_mod"] = int(enemy.get("str_mod", 0) * mult)
    enemy["con_mod"] = int(enemy.get("con_mod", 0) * mult)
    enemy["dex_mod"] = int(enemy.get("dex_mod", 0) * mult)
    enemy["_eh_rush"] = True


def rush_boss_by_id(boss_id):
    """Roster entry (copy) for a boss id, or None when unknown."""
    for boss in BOSS_RUSH_ROSTER:
        if boss["id"] == boss_id:
            return dict(boss)
    return None


def rush_boss_combat(boss):
    """Resolve a roster entry's ``combat_*`` callable (lazy — import cycles)."""
    import importlib
    module = importlib.import_module(boss["module"])
    return getattr(module, boss["func"])


# Card templates. Each instance adds a "tier" + resolved value(s) + label.
NEGATIVE_CARDS = [
    {"id": "status_ward", "name": "Status Ward", "key": "status_res",
     "values": [0.08, 0.12, 0.16, 0.20], "desc": "enemies gain +{v}% status resistance"},
    {"id": "bloodlust", "name": "Bloodlust", "key": "dmg",
     "values": [0.06, 0.09, 0.12, 0.15], "desc": "enemies deal +{v}% damage"},
    {"id": "marrow", "name": "Marrow", "key": "hp",
     "values": [0.10, 0.15, 0.20, 0.25], "desc": "enemies gain +{v}% max HP"},
    {"id": "elemental_surge", "name": "Elemental Surge", "key": "ele_dmg",
     "values": [0.06, 0.09, 0.12, 0.15], "desc": "enemies gain +{v}% elemental damage"},
    {"id": "mending_roil", "name": "Mending Roil", "key": "regen",
     "values": [0.02, 0.03, 0.04, 0.05], "desc": "enemies regenerate {v}% max HP per turn"},
    {"id": "chitin", "name": "Chitin", "key": "def",
     "values": [0.08, 0.12, 0.16, 0.20], "desc": "enemies gain +{v}% CON/DEX"},
]

POSITIVE_CARDS = [
    {"id": "unity", "name": "Unity", "effects": [{"type": "damage_boost", "values": [0.04, 0.06, 0.08, 0.10]}],
     "desc": "team deals +{v}% damage"},
    {"id": "bulwark", "name": "Bulwark", "effects": [{"type": "defense_pct", "values": [0.04, 0.06, 0.08, 0.10]}],
     "desc": "team takes −{v}% damage"},
    {"id": "harmony", "name": "Harmony", "effects": [{"type": "regen", "values": [1, 2, 3, 4]}],
     "desc": "team regenerates {v} HP per round"},
    {"id": "insight", "name": "Insight", "effects": [{"type": "stat", "stat": "all", "values": [2, 3, 4, 5]}],
     "desc": "team gains +{v} all attributes"},
    {"id": "aftershock", "name": "Aftershock", "effects": [{"type": "eh_ele_dmg", "values": [0.05, 0.08, 0.10, 0.12]}],
     "desc": "team gains +{v}% elemental damage"},
    {"id": "celerity", "name": "Celerity",
     "effects": [{"type": "stat", "stat": "Dexterity", "values": [1, 2, 3, 4]},
                 {"type": "crit_chance", "values": [0.02, 0.03, 0.04, 0.05]}],
     "desc": "team gains +{v} DEX and crit"},
]


def card_tier_for_room(room):
    return max(1, min(4, 1 + int(room) // 15))


def _build_card(template, tier, positive, room):
    card = {
        "id": template["id"],
        "name": template["name"],
        "tier": tier,
        "room": int(room),
        "positive": positive,
        "desc": "",
    }
    if positive:
        effects = []
        for eff in template["effects"]:
            value = eff["values"][tier - 1]
            entry = {"type": eff["type"], "value": value}
            if "stat" in eff:
                entry["stat"] = eff["stat"]
            effects.append(entry)
        card["effects"] = effects
        card["entropy_cost"] = 0
        v = template["effects"][0]["values"][tier - 1]
        if template["id"] == "celerity":
            card["desc"] = f"team gains +{v} DEX and +{round(template['effects'][1]['values'][tier-1]*100)}% crit"
        else:
            card["desc"] = template["desc"].format(v=round(v * 100) if isinstance(v, float) else v)
    else:
        value = template["values"][tier - 1]
        card["effects"] = {template["key"]: value}
        card["entropy_cost"] = EH_TRIAL_ENTROPY_COSTS.get(tier, 2)
        shown = round(value * 100) if isinstance(value, float) else value
        card["desc"] = template["desc"].format(v=shown)
    return card


def _picked_entries(player, positive=False):
    """(card id, tier) pairs already claimed — unique deck entries."""
    state = ensure_eh_state(player)
    key = "positive_cards" if positive else "negative_cards"
    return {(c.get("id"), int(c.get("tier", 0))) for c in state.get(key, [])}


def roll_trial_cards(player, positive=False, count=3):
    """Offer up to `count` cards (distinct kinds) from the remaining deck.

    Deck rule (playtest 2026-10-07, corrected): every (kind, tier) pair is a
    UNIQUE card — an exact duplicate never appears twice, but same-kind cards
    at different tiers both exist and STACK (effects add). A card's tier must
    be unlocked by depth (`card_tier_for_room`, T4 from r45), so an unpicked
    T1 can still surface at a late room. Returns [] when nothing eligible is
    left to offer.
    """
    state = ensure_eh_state(player)
    room = max(1, int(state.get("room", 1) or 1))
    tier_cap = card_tier_for_room(room)
    pool = POSITIVE_CARDS if positive else NEGATIVE_CARDS
    picked = _picked_entries(player, positive)

    by_kind = {}
    for template in pool:
        tiers = [t for t in range(1, tier_cap + 1)
                 if (template["id"], t) not in picked]
        if tiers:
            by_kind[template["id"]] = (template, tiers)

    if not by_kind:
        return []
    kinds = random.sample(list(by_kind.keys()), min(count, len(by_kind)))
    return [_build_card(by_kind[k][0], random.choice(by_kind[k][1]),
                        positive, room) for k in kinds]


def format_card_label(card):
    """Terminal/GUI menu label for a card offer."""
    base = f"{card['name']} (T{card['tier']}) — {card['desc']}"
    if card.get("entropy_cost"):
        base += f"  ·  Entropy +{card['entropy_cost']}"
    return base


def apply_negative_card(player, card):
    """Persist an enemy handicap card (unique (kind, tier) deck entry)."""
    state = ensure_eh_state(player)
    record = dict(card)
    record["entropy_cost"] = int(card.get("entropy_cost", EH_TRIAL_ENTROPY_COSTS.get(card.get("tier", 1), 2)))
    cards = state.setdefault("negative_cards", [])
    if any(c.get("id") == record["id"]
           and int(c.get("tier", 0)) == int(record["tier"]) for c in cards):
        return (f"{record['name']} (T{record['tier']}) is already carried — "
                "the card stays unplayed.")
    cards.append(record)
    sync_entropy(player)
    return f"Trial accepted: {record['name']} — enemies empowered (Entropy +{record['entropy_cost']})."


def _apply_permanent_effect(actor, eff, label=None):
    entry = {
        "type": eff["type"],
        "value": eff.get("value", 0),
        "remaining": 9999,
        "permanent": True,
        "source": EH_SOURCE,
    }
    if eff.get("stat"):
        entry["stat"] = eff["stat"]
    if label:
        entry["label"] = label
    actor.setdefault("active_buffs", []).append(entry)


def apply_positive_card(player, card):
    """Persist a team boon card (unique (kind, tier) deck entry; stacks)."""
    state = ensure_eh_state(player)
    record = dict(card)
    cards = state.setdefault("positive_cards", [])
    if any(c.get("id") == record["id"]
           and int(c.get("tier", 0)) == int(record["tier"]) for c in cards):
        return (f"{record['name']} (T{record['tier']}) is already carried — "
                "the card stays unplayed.")
    cards.append(record)
    _apply_card_effects_to_roster(player, record)
    return f"Deep boon: {record['name']} — {record['desc']} (permanent for the run)."


def _apply_card_effects_to_roster(player, card):
    """Apply a positive card's effects to every actor (no state write)."""
    actors = [player] + list(player.get("allies", []))
    for actor in actors:
        for eff in card.get("effects", []):
            _apply_permanent_effect(actor, eff, label=card.get("name"))


# ═══════════════════════════════════════════════════════════════════════════
# The Joker — the 22 Major Arcana (docs/joker_cards_proposal.md)
# ═══════════════════════════════════════════════════════════════════════════

# Every rn+25 the Joker deals 2 faces from the unowned pool; the player keeps
# at most one (or refuses). The hand is capped (EH_JOKER_HAND_CAP), holds
# distinct arcana, and is replaceable — a thrown face returns to the deck.
# Boost/drawback routing: effect entries apply to their ``actors`` spec
# ("all" default, "player", "allies"); actor-entry drawbacks route to the
# roster, behavioural drawbacks (prices, cuts, locks, gates) live only in the
# run record and are read where they matter. ``ready`` gates the deal pool
# while a face's hook audit finishes — every face ships eventually.
JOKER_CARDS = [
    # ── ready faces ────────────────────────────────────────────────────────
    {"id": "joker_strength", "name": "Strength", "ready": True,
     "desc": "+20% damage dealt · always act last in battle",
     "effects": [{"type": "damage_boost", "value": 0.20}],
     "drawback": {"type": "slow"}},
    {"id": "joker_temperance", "name": "Temperance", "ready": True,
     "desc": "−20% damage taken · −15% dealt · −25% Horizon Motes",
     "effects": [{"type": "defense_pct", "value": 0.20}],
     "drawback": [{"type": "damage_boost", "value": -0.15},
                  {"type": "mote_gain_down", "value": 0.25}]},
    {"id": "joker_wheel", "name": "Wheel of Fortune", "ready": True,
     "desc": "+20% crit chance · enemies' crit cap doubles",
     "effects": [{"type": "crit_chance", "value": 0.20}],
     "drawback": {"type": "enemy_crit_up"}},
    {"id": "joker_magician", "name": "The Magician", "ready": True,
     "desc": "+50% elemental damage · hits off the enemy's weakness deal 25%",
     "effects": [{"type": "eh_ele_dmg", "value": 0.50}],
     "drawback": {"type": "weakness_gate"}},
    {"id": "joker_hermit", "name": "The Hermit", "ready": True,
     "desc": "+6 all attributes · −50% gold & Horizon Motes",
     "effects": [{"type": "stat", "stat": "all", "value": 6}],
     "drawback": [{"type": "gold_gain_down", "value": 0.50},
                  {"type": "mote_gain_down", "value": 0.50}]},
    {"id": "joker_empress", "name": "The Empress", "ready": True,
     "desc": "+2.5% max HP per round · −15% damage dealt",
     "effects": [{"type": "regen_pct", "value": 0.025}],
     "drawback": {"type": "damage_boost", "value": -0.15}},
    {"id": "joker_chariot", "name": "The Chariot", "ready": True,
     "desc": "+30% damage dealt · +20% damage taken",
     "effects": [{"type": "damage_boost", "value": 0.30}],
     "drawback": {"type": "damage_taken_up", "value": 0.20}},
    {"id": "joker_devil", "name": "The Devil", "ready": True,
     "desc": "+25% damage dealt · rift shop prices +20%",
     "effects": [{"type": "damage_boost", "value": 0.25}],
     "drawback": {"type": "shop_price_up", "value": 0.20}},
    {"id": "joker_moon", "name": "The Moon", "ready": True,
     "desc": "each battle: 2 random buffs · 2 random debuffs",
     "effects": [], "drawback": {"type": "battle_gamble"}},
    {"id": "joker_tower", "name": "The Tower", "ready": True,
     "desc": "flasks drunk after this grant ×2 · 2% max HP per turn per 5 flasks",
     "effects": [{"type": "flask_double"}],
     "drawback": {"type": "tower_drain"}},
    {"id": "joker_lovers", "name": "The Lovers", "ready": True,
     "desc": "allies +25% dealt, −15% taken · the MC deals −15%",
     "effects": [{"type": "damage_boost", "value": 0.25, "actors": "allies"},
                 {"type": "defense_pct", "value": 0.15, "actors": "allies"}],
     "drawback": {"type": "damage_boost", "value": -0.15,
                  "actors": "player"}},
    {"id": "joker_world", "name": "The World", "ready": True,
     "desc": "every other arcana loses its drawback · the deal ends",
     "effects": [{"type": "world_suppress"}],
     "drawback": {"type": "deal_end"}},
    # ── hook audits in progress (excluded from deals until ready) ─────────
    {"id": "joker_death", "name": "Death", "ready": True,
     "desc": "attacks heal 10% of damage dealt · all other healing −50%",
     "effects": [{"type": "lifesteal", "value": 0.10}],
     "drawback": {"type": "healing_down", "value": 0.50}},
    {"id": "joker_fool", "name": "The Fool", "ready": True,
     "desc": "+2 initiative · +10% dodge · 10% chance your attacks miss",
     "effects": [{"type": "initiative", "value": 2},
                 {"type": "evasion", "value": 0.10}],
     "drawback": {"type": "miss_chance", "value": 0.10}},
    {"id": "joker_priestess", "name": "The High Priestess", "ready": True,
     "desc": "skill cooldowns −2 turns · basic attacks deal 50% damage",
     "effects": [{"type": "cooldown_down", "value": 2}],
     "drawback": {"type": "basic_damage_down", "value": 0.50}},
    {"id": "joker_emperor", "name": "The Emperor", "ready": True,
     "desc": "once per battle: survive a lethal hit · saved actor silenced 2 rounds",
     "effects": [{"type": "cheat_death"}],
     "drawback": {"type": "silence_on_save"}},
    {"id": "joker_hierophant", "name": "The Hierophant", "ready": True,
     "desc": "+25% skill damage · basic attacks −25%",
     "effects": [{"type": "skill_damage", "value": 0.25}],
     "drawback": {"type": "basic_damage_down", "value": 0.25}},
    {"id": "joker_justice", "name": "Justice", "ready": True,
     "desc": "every debuff is inflicted back on its source — enemy and party alike",
     "effects": [{"type": "debuff_mirror"}],
     "drawback": {"type": "debuff_mirror_backfire"}},
    {"id": "joker_hanged_man", "name": "The Hanged Man", "ready": True,
     "desc": "+30% damage dealt · cannot act in round 1",
     "effects": [{"type": "damage_boost", "value": 0.30}],
     "drawback": {"type": "skip_round_one"}},
    {"id": "joker_star", "name": "The Star", "ready": True,
     "desc": "debuffs on the party last 1 turn less · −15% damage dealt",
     "effects": [{"type": "debuff_duration_down", "value": 1}],
     "drawback": {"type": "damage_boost", "value": -0.15}},
    {"id": "joker_sun", "name": "The Sun", "ready": True,
     "desc": "crits deal +30% more · non-crit hits −15%",
     "effects": [{"type": "crit_damage", "value": 0.30}],
     "drawback": {"type": "nonscrit_damage_down", "value": 0.15}},
    {"id": "joker_judgement", "name": "Judgement", "ready": True,
     "desc": "round start: all enemies lose 20% max HP (pure) · from round 3, the party too",
     "effects": [{"type": "round_pulse", "value": 0.20}],
     "drawback": {"type": "round_pulse_self", "value": 0.20,
                  "from_round": 3}},
]

JOKER_CARD = JOKER_CARDS[0]  # default (tests / single-card callers)

# Actor-entry drawback kinds: routed to the roster. Everything else is a
# behavioural drawback (record-only — read where it matters).
_JOKER_ENTRY_DRAWBACKS = {"damage_taken_up", "slow", "damage_boost",
                          "defense_pct", "crit_chance", "eh_ele_dmg",
                          "regen_pct", "stat"}

# Behavioural effect kinds: no roster entry — read from the run record (or a
# per-actor flag) where they matter.
_JOKER_BEHAVIOURAL_EFFECTS = {"flask_double", "world_suppress", "cheat_death",
                              "lifesteal", "cooldown_down",
                              "debuff_duration_down", "initiative",
                              "crit_damage", "round_pulse", "debuff_mirror",
                              # legacy — retired hooks keep old records inert
                              "reflect", "kill_heal"}


def owned_jokers(player):
    """The run's hand: owned arcana records, in acquisition order."""
    return list(ensure_eh_state(player).get("joker_cards", []))


def owned_joker_ids(player):
    return {r.get("id") for r in owned_jokers(player)}


def has_owned_joker(player, joker_id):
    return joker_id in owned_joker_ids(player)


def joker_hand_full(player):
    return len(owned_jokers(player)) >= EH_JOKER_HAND_CAP


def _joker_world_owned(player):
    return has_owned_joker(player, "joker_world")


def joker_drawbacks_active(player, joker_id):
    """True when `joker_id`'s drawback is live (World lifts every other)."""
    if not has_owned_joker(player, joker_id):
        return False
    if joker_id != "joker_world" and _joker_world_owned(player):
        return False
    return True


def available_joker_faces(player):
    """Dealable faces: ready, not owned. A thrown face returns here."""
    owned = owned_joker_ids(player)
    return [c for c in JOKER_CARDS
            if c.get("ready") and c["id"] not in owned]


def deal_joker_faces(player, count=EH_JOKER_DEAL):
    """Deal `count` distinct unowned faces (may deal fewer near pool end)."""
    pool = available_joker_faces(player)
    if not pool:
        return []
    return random.sample(pool, min(count, len(pool)))


def _joker_drawbacks(record):
    draw = record.get("drawback")
    if not draw:
        return []
    return draw if isinstance(draw, list) else [draw]


def _joker_targets(player, spec):
    who = spec.get("actors", "all")
    if who == "player":
        return [player]
    if who == "allies":
        return list(player.get("allies", []))
    return [player] + list(player.get("allies", []))


def _joker_entry(spec, label):
    entry = {"type": spec["type"], "value": spec.get("value", 0),
             "remaining": 9999, "permanent": True, "source": EH_SOURCE,
             "label": label, "eh_joker": True, "eh_joker_drawback": True}
    if spec.get("stat"):
        entry["stat"] = spec["stat"]
    return entry


def _apply_joker_drawback(actor, draw, label):
    """Route one actor-entry drawback to the roster (behavioural ones skip)."""
    etype = draw.get("type")
    if etype not in _JOKER_ENTRY_DRAWBACKS:
        return
    if etype == "slow":
        actor["slowed"] = True
        debuffs = actor.setdefault("active_debuffs", [])
        if not any(e.get("type") == "slow" and e.get("label") == label
                   for e in debuffs):
            debuffs.append({"type": "slow", "remaining": 9999,
                            "permanent": True, "source": EH_SOURCE,
                            "label": label, "eh_joker": True,
                            "eh_joker_drawback": True})
        return
    if etype == "damage_taken_up":
        actor.setdefault("active_debuffs", []).append(_joker_entry(draw, label))
    else:
        # Negative stat-family entry (e.g. −15% dealt) — a buff so the
        # damage reads pick it up (Warden precedent).
        actor.setdefault("active_buffs", []).append(_joker_entry(draw, label))


def _apply_joker_to_roster(player, record):
    """(Re)attach a Joker's boost + drawback to its target actors.

    The World lifts every *other* arcana's drawback — both for freshly
    applied records and on the restore path (the state already lists all
    records when restore replays them).
    """
    suppress = _joker_world_owned(player) and record.get("id") != "joker_world"
    for eff in record.get("effects", []):
        if eff.get("type") in _JOKER_BEHAVIOURAL_EFFECTS:
            continue
        for actor in _joker_targets(player, eff):
            _apply_permanent_effect(actor, eff, label=record.get("name"))
    if not suppress:
        for draw in _joker_drawbacks(record):
            for actor in _joker_targets(player, draw):
                _apply_joker_drawback(actor, draw, record.get("name"))


def _joker_entry_belongs(entry, label):
    return ((entry.get("source") == EH_SOURCE or entry.get("eh_joker"))
            and entry.get("label") == label)


def _entry_is_joker_drawback(entry):
    if entry.get("eh_joker_drawback"):
        return True
    if entry.get("type") == "damage_taken_up":
        return True
    try:
        return float(entry.get("value", 0)) < 0
    except (TypeError, ValueError):
        return False


def _clear_removed_slow_flag(actor, removed):
    if any(e.get("type") == "slow" for e in removed):
        if not any(e.get("type") == "slow"
                   for e in actor.get("active_debuffs", [])):
            actor.pop("slowed", None)


def _sweep_joker_drawbacks(player):
    """The World: strip every actor-entry drawback of the other arcana."""
    names = {r.get("name") for r in owned_jokers(player)
             if r.get("id") != "joker_world"}
    for actor in [player] + list(player.get("allies", [])):
        for key in ("active_buffs", "active_debuffs"):
            kept, removed = [], []
            for entry in actor.get(key, []):
                if (entry.get("label") in names
                        and _joker_entry_belongs(entry, entry.get("label"))
                        and _entry_is_joker_drawback(entry)):
                    removed.append(entry)
                else:
                    kept.append(entry)
            actor[key] = kept
            _clear_removed_slow_flag(actor, removed)


def _refresh_joker_actor_flags(player):
    """Sync every per-actor joker behaviour flag (all hooks read these).

    Boosts read plain ownership; drawbacks read ``joker_drawbacks_active``
    so The World can lift them. A ``None`` value means "pop the flag".
    """
    owned = owned_joker_ids(player)

    def _act(jid):
        return joker_drawbacks_active(player, jid)

    flag_values = {
        "_eh_joker_weakness_gate": True if _act("joker_magician") else None,
        "_eh_joker_emperor": True if _act("joker_emperor") else None,
        "_eh_joker_init": 2 if "joker_fool" in owned else None,
        "_eh_joker_miss": 0.10 if _act("joker_fool") else None,
        "_eh_joker_skill_mult": 1.25 if "joker_hierophant" in owned else None,
        "_eh_joker_basic_mult": 0.75 if _act("joker_hierophant") else None,
        "_eh_joker_sun_crit": 0.30 if "joker_sun" in owned else None,
        "_eh_joker_sun_pen": 0.15 if _act("joker_sun") else None,
        "_eh_joker_lifesteal": 0.10 if "joker_death" in owned else None,
        "_eh_joker_healing_mult": 0.5 if _act("joker_death") else None,
        "_eh_joker_star": True if "joker_star" in owned else None,
        "_eh_joker_skip_r1": True if _act("joker_hanged_man") else None,
        "_eh_joker_priestess": True if "joker_priestess" in owned else None,
        "_eh_joker_priestess_pen": 0.5 if _act("joker_priestess") else None,
    }
    for actor in [player] + list(player.get("allies", [])):
        for key, val in flag_values.items():
            if val is not None:
                actor[key] = val
            else:
                actor.pop(key, None)
        if flag_values["_eh_joker_emperor"] is None:
            actor.pop("_eh_emperor_used", None)


def try_emperor_save(actor):
    """The Emperor — once per battle, hold at 1 HP (silenced 2 rounds after).

    Called through ``status_effects.try_consume_death_ward`` so direct hits,
    DoTs, and superboss specials all funnel through it.
    """
    if not actor.get("_eh_joker_emperor") or actor.get("_eh_emperor_used"):
        return False
    actor["_eh_emperor_used"] = True
    actor["_eh_emperor_saved"] = True
    actor["current_hp"] = 1
    from combat import status_effects as se
    from combat.combat_io import c_print
    se.apply_silence(actor, duration=2)
    name = actor.get("name", "You")
    c_print(f"  ♠ The Emperor commands — {name} holds at 1 HP! "
            f"(silenced 2 rounds)")
    return True


def joker_initiative_bonus(actor):
    """The Fool: +2 initiative (read by ``roll_initiative``)."""
    return actor.get("_eh_joker_init", 0) or 0


def joker_attack_missed(attacker):
    """The Fool: a 10% chance any attack fails outright."""
    pct = attacker.get("_eh_joker_miss", 0) or 0
    if pct <= 0 or random.random() >= pct:
        return False
    from combat.combat_io import c_print
    c_print(f"  ♠ The Fool's luck turns — {attacker.get('name', 'your')}"
            f"'s attack goes wide!")
    return True


def joker_damage_multiplier(attacker, kind):
    """The Hierophant: +25% skill damage · basic attacks ×0.75.
    The High Priestess: basic attacks ×0.5 (drawback)."""
    if kind == "skill":
        return attacker.get("_eh_joker_skill_mult", 1.0) or 1.0
    mult = attacker.get("_eh_joker_basic_mult", 1.0) or 1.0
    pen = attacker.get("_eh_joker_priestess_pen", 0) or 0
    if pen:
        mult *= (1 - pen)
    return mult


def joker_crit_modifier(attacker, is_crit, dmg):
    """The Sun: crits +30% more · non-crit hits ×0.85."""
    if is_crit:
        bonus = attacker.get("_eh_joker_sun_crit", 0) or 0
        if bonus:
            return int(dmg * (1 + bonus))
    else:
        pen = attacker.get("_eh_joker_sun_pen", 0) or 0
        if pen:
            return int(dmg * (1 - pen))
    return dmg


def _actor_max_hp(actor):
    if actor.get("is_ally"):
        return int(actor.get("max_hp", 100))
    from character import player_max_hp
    return int(player_max_hp(actor))


def joker_judgement_pulse(player, enemies, round_num):
    """Judgement: round-start pure damage.

    Every standing enemy loses 20% of max HP; from round 3 the party
    suffers the same (drawback — World lifts it; the party never drops
    below 1 HP). Called by the combat engine at the start of each round.
    """
    if not has_owned_joker(player, "joker_judgement"):
        return []
    msgs = []
    pct = 0.20
    hits = 0
    for enemy in (enemies or []):
        if enemy.get("hp", 0) <= 0:
            continue
        max_hp = int(enemy.get("max_hp", enemy.get("hp", 1)) or 1)
        enemy["hp"] = enemy.get("hp", 0) - max(1, int(max_hp * pct))
        hits += 1
    if hits:
        msgs.append(f"  ⚖ Judgement falls — {hits} foe(s) lose "
                    f"{int(pct * 100)}% max HP (pure damage).")
    if round_num >= 3 and joker_drawbacks_active(player, "joker_judgement"):
        for actor in [player] + _alive_active_allies(player):
            if actor.get("current_hp", 0) <= 0:
                continue
            dmg = max(1, int(_actor_max_hp(actor) * pct))
            actor["current_hp"] = max(1, actor.get("current_hp", 1) - dmg)
        msgs.append(f"  ⚖ Judgement's scales tip — the party bleeds "
                    f"{int(pct * 100)}% max HP (pure damage).")
    return msgs


def debuff_signature(actors):
    """Per-type (count, total duration) across the actors' debuffs.

    The engine snapshots this before an action and hands it to
    ``joker_mirror_debuffs`` — any type whose count or duration grew was
    inflicted (or refreshed) during the action.
    """
    sig = {}
    for actor in actors or []:
        for d in actor.get("active_debuffs", []):
            kind = d.get("type")
            if not kind:
                continue
            cnt, dur = sig.get(kind, (0, 0))
            sig[kind] = (cnt + 1, dur + int(d.get("remaining", 0) or 0))
    return sig


def _mirror_one_debuff(actor, debuff):
    """Re-inflict one debuff entry on `actor` (Justice's mirror).

    Uses the standard appliers (flags/merges behave; immunities and status
    resistance still apply) with a scrubbed entry-copy fallback for exotic
    kinds. Returns False when the infliction was explicitly resisted.
    """
    from combat import status_effects as se
    kind = debuff.get("type")
    dur = max(1, min(int(debuff.get("remaining", 3) or 3), 99))
    is_party = "current_hp" in actor
    try:
        if kind == "poison":
            res = se.apply_poison(actor, int(debuff.get("damage", 3) or 3), dur)
            return res not in ("resisted", "immune")
        if kind == "bleed":
            res = se.apply_bleed(actor, int(debuff.get("damage", 3) or 3), dur)
            return res not in ("resisted", "immune")
        if kind == "burn":
            if is_party:
                res = se.apply_burn_to_player(actor, tier=debuff.get("tier"),
                                              duration=dur,
                                              damage=debuff.get("damage"))
            else:
                res = se.apply_burn(actor, tier=debuff.get("tier"),
                                    duration=dur, damage=debuff.get("damage"))
            return res not in ("resisted", "immune")
        if kind == "weaken":
            res = se.apply_weaken(actor,
                                  penalty_pct=debuff.get("penalty_pct",
                                                         debuff.get("value", 0.15)),
                                  duration=dur)
            return res not in ("resisted", "immune")
        if kind == "slow":
            if is_party:
                res = se.apply_slow_to_player(actor, duration=dur)
            else:
                res = se.apply_slow_to_enemy(actor, duration=dur)
            return res not in ("resisted", "immune")
        if kind == "blind":
            res = se.apply_blind(actor, duration=dur)
            return res not in ("resisted", "immune")
        if kind == "silence":
            res = se.apply_silence(actor, duration=dur)
            return res not in ("resisted", "immune")
        if kind == "dread":
            res = se.apply_dread(actor, duration=dur)
            return res not in ("resisted", "immune")
        if kind == "damage_taken_up":
            res = se.apply_damage_taken_up(actor, debuff.get("value", 0.15), dur)
            return res not in ("resisted", "immune")
    except Exception:
        pass
    # Fallback: copy the entry itself (markers scrubbed).
    entry = {k: v for k, v in debuff.items()
             if k not in ("label", "source", "eh_joker", "eh_joker_drawback")}
    entry["remaining"] = dur
    actor.setdefault("active_debuffs", []).append(dict(entry))
    return True


def joker_mirror_debuffs(player, inflictor, targets, before_sig):
    """Justice — every debuff is inflicted back on whoever inflicted it.

    ``before_sig`` is a ``debuff_signature(targets)`` taken before the
    action. Newly-inflicted (or refreshed) debuff types on the targets
    are re-inflicted on the `inflictor` — once per type per action, so an
    ally's AoE burn mires the caster once, not once per enemy hit. An
    enemy's infliction mirrors for free; the party's own infliction is
    the drawback (The World lifts it).
    """
    if not has_owned_joker(player, "joker_justice"):
        return []
    inflictor_is_party = "current_hp" in inflictor
    if inflictor_is_party and not joker_drawbacks_active(player, "joker_justice"):
        return []
    after = debuff_signature(targets)
    new_types = []
    for kind, (cnt, dur) in after.items():
        b_cnt, b_dur = before_sig.get(kind, (0, 0))
        if cnt > b_cnt or dur > b_dur:
            new_types.append(kind)
    if not new_types:
        return []
    exemplar = {}
    for actor in targets or []:
        for d in actor.get("active_debuffs", []):
            kind = d.get("type")
            if kind in new_types and kind not in exemplar:
                exemplar[kind] = d
    msgs = []
    name = inflictor.get("name", "You")
    for kind in new_types:
        if not _mirror_one_debuff(inflictor, exemplar[kind]):
            continue
        msgs.append(f"  ⚖ Justice mirrors — {name} suffers the "
                    f"{kind.replace('_', ' ')} they inflicted.")
    return msgs


def flask_effect_multiplier(player):
    """The Tower: flasks drunk after it is taken grant ×2 (boost — World
    does NOT suppress boosts)."""
    return 2.0 if has_owned_joker(player, "joker_tower") else 1.0


def _refresh_tower_drain(player):
    """Recompute each actor's Tower drain: 2% max HP per battle round per
    full 5 flasks that actor has consumed (pre- + post-Tower)."""
    state = ensure_eh_state(player)
    active = joker_drawbacks_active(player, "joker_tower")
    for actor in [player] + list(player.get("allies", [])):
        debuffs = actor.setdefault("active_debuffs", [])
        existing = next((d for d in debuffs
                         if d.get("type") == "eh_tower_drain"), None)
        if not active:
            if existing is not None:
                debuffs.remove(existing)
            continue
        key = actor_key(actor, player)
        count = len((state.get("actor_flasks") or {}).get(key, []))
        pct = 0.02 * (count // 5)
        if pct <= 0:
            if existing is not None:
                debuffs.remove(existing)
            continue
        if existing is None:
            debuffs.append({"type": "eh_tower_drain", "value": pct,
                            "remaining": 9999, "permanent": True,
                            "source": EH_SOURCE, "label": "The Tower",
                            "eh_joker": True, "eh_joker_drawback": True})
        else:
            existing["value"] = pct


def joker_economy_multipliers(player):
    """(gold_mult, mote_mult) from Temperance / The Hermit drawbacks."""
    gold = 1.0
    mote = 1.0
    if joker_drawbacks_active(player, "joker_temperance"):
        mote *= 0.75
    if joker_drawbacks_active(player, "joker_hermit"):
        gold *= 0.5
        mote *= 0.5
    return gold, mote


def apply_mote_multiplier(player, amount):
    """Scale one mote award by the economy drawbacks (min 1)."""
    if amount <= 0:
        return amount
    _gold, mote = joker_economy_multipliers(player)
    return max(1, int(amount * mote))


def joker_shop_multiplier(player):
    """The Devil: rift shop prices +20% (again: nothing else suppresses)."""
    return 1.2 if joker_drawbacks_active(player, "joker_devil") else 1.0


def discard_joker(player, record):
    """Throw an owned arcana back into the deck (strips all its entries)."""
    state = ensure_eh_state(player)
    cards = state.get("joker_cards", [])
    if record not in cards:
        return "That arcana is not in your hand."
    cards.remove(record)
    label = record.get("name")
    for actor in [player] + list(player.get("allies", [])):
        for key in ("active_buffs", "active_debuffs"):
            kept, removed = [], []
            for entry in actor.get(key, []):
                if _joker_entry_belongs(entry, label):
                    removed.append(entry)
                else:
                    kept.append(entry)
            actor[key] = kept
            _clear_removed_slow_flag(actor, removed)
    _refresh_joker_actor_flags(player)
    _refresh_tower_drain(player)
    return f"{label} is thrown back into the deck."


def apply_joker(player, card=None, replace=None):
    """Keep one dealt face (persist it + spread the trade-off).

    At the hand cap a `replace` record must be supplied — it is thrown back
    into the deck first. The World closes the deal once taken.
    """
    card = card or JOKER_CARD
    state = ensure_eh_state(player)
    cards = state.setdefault("joker_cards", [])
    if any(r.get("id") == card["id"] for r in cards):
        return (f"{card['name']} is already in your hand — the deal passes.")
    if _joker_world_owned(player) and card.get("id") != "joker_world":
        return "The deal is closed — no further arcana can be taken."
    if len(cards) >= EH_JOKER_HAND_CAP:
        if replace is None:
            return "Your hand is full — throw an arcana to take another."
        if replace not in cards:
            return "That arcana is not in your hand."
        discard_joker(player, replace)
    record = {
        "id": card["id"], "name": card["name"], "desc": card["desc"],
        "room": int(state.get("room", 0)),
        "effects": [dict(e) for e in card.get("effects", [])],
        "drawback": card.get("drawback"),
    }
    cards.append(record)
    _apply_joker_to_roster(player, record)
    _refresh_joker_actor_flags(player)
    _refresh_tower_drain(player)
    if record["id"] == "joker_world":
        _sweep_joker_drawbacks(player)
        _refresh_joker_actor_flags(player)
        _refresh_tower_drain(player)
        return (f"The World is laid down — every other arcana's burden "
                f"lifts. The deal is closed: no further cards will be dealt, "
                f"and your hand can no longer be thrown.")
    return f"The Joker is played: {record['name']} — {record['desc']} (run-long)."


# The Moon — battle-start gamble (2 random buffs & 2 random debuffs/actor)
_MOON_BUFFS = ("haste", "damage_boost", "defense_pct", "regen_pct")
_MOON_DEBUFFS = ("weaken", "slow", "blind", "poison", "burn")


def _apply_and_tag(actor, key, etype, factory):
    """Run `factory`; tag any newly created entry of `etype` as The Moon's."""
    before = {id(e) for e in actor.get(key, [])}
    factory()
    for entry in actor.get(key, []):
        if id(entry) not in before and entry.get("type") == etype:
            entry["label"] = "The Moon"
            entry["eh_joker"] = True


def apply_joker_battle_start(player):
    """Round-1 hook: per-battle Joker states reset + The Moon's gamble."""
    if not in_run(player):
        return 0
    # Once-per-battle joker states (The Emperor's save) reset each battle.
    for actor in [player] + list(player.get("allies", [])):
        actor.pop("_eh_emperor_used", None)
    if not has_owned_joker(player, "joker_moon"):
        return 0
    from combat import status_effects as se
    from combat.combat_io import c_print
    actors = [player] + _alive_active_allies(player)
    applied = 0
    for actor in actors:
        gain, suffer = [], []
        for kind in random.sample(_MOON_BUFFS, 2):
            if kind == "haste":
                _apply_and_tag(actor, "active_buffs", "haste",
                               lambda a=actor: se.apply_haste(a, duration=2, init_bonus=2, cd_reduction=1))
                gain.append("Haste")
            elif kind == "damage_boost":
                actor.setdefault("active_buffs", []).append(
                    {"type": "damage_boost", "value": 0.10, "remaining": 3,
                     "label": "The Moon", "eh_joker": True})
                gain.append("+10% damage")
            elif kind == "defense_pct":
                actor.setdefault("active_buffs", []).append(
                    {"type": "defense_pct", "value": 0.15, "remaining": 3,
                     "label": "The Moon", "eh_joker": True})
                gain.append("−15% taken")
            else:  # regen_pct
                actor.setdefault("active_buffs", []).append(
                    {"type": "regen_pct", "value": 0.02, "remaining": 3,
                     "label": "The Moon", "eh_joker": True})
                gain.append("regen")
        for kind in random.sample(_MOON_DEBUFFS, 2):
            if kind == "weaken":
                _apply_and_tag(actor, "active_debuffs", "weaken",
                               lambda a=actor: se.apply_weaken(a, penalty_pct=0.15, duration=2))
                suffer.append("weakened")
            elif kind == "slow":
                _apply_and_tag(actor, "active_debuffs", "slow",
                               lambda a=actor: se.apply_slow_to_player(a, duration=2))
                suffer.append("slowed")
            elif kind == "blind":
                _apply_and_tag(actor, "active_debuffs", "blind",
                               lambda a=actor: se.apply_blind(a, duration=2))
                suffer.append("blinded")
            elif kind == "poison":
                _apply_and_tag(actor, "active_debuffs", "poison",
                               lambda a=actor: se.apply_poison(a, 4, 2))
                suffer.append("poisoned")
            else:  # burn
                _apply_and_tag(actor, "active_debuffs", "burn",
                               lambda a=actor: se.apply_burn(a, tier=2, duration=2))
                suffer.append("burning")
        name = actor.get("name", "You")
        c_print(f"  ♠ The Moon turns for {name}: gains "
                f"{', '.join(gain)} — suffers {', '.join(suffer)}!")
        applied += 1
    return applied


# ═══════════════════════════════════════════════════════════════════════════
# Flasks (permanent-per-run, single-actor)
# ═══════════════════════════════════════════════════════════════════════════

FLASK_ARCHETYPES = {
    "fervor": {"name": "Fervor", "kind": "damage_boost",
               "values": [0.02, 0.03, 0.04, 0.05, 0.06, 0.08, 0.10]},
    "prism": {"name": "Prism", "kind": "eh_ele_dmg",
              "values": [0.02, 0.03, 0.04, 0.05, 0.06, 0.08, 0.10]},
    "bastion": {"name": "Bastion", "kind": "defense_pct",
                "values": [0.01, 0.02, 0.025, 0.03, 0.04, 0.05, 0.06]},
    "might": {"name": "Might", "kind": "stat",
              "values": [1, 2, 3, 4, 5, 6, 8]},
    # Vitality heals a PERCENT of max HP per round (playtest 2026-10-07 —
    # the old flat 1-8 HP had become dead weight past the early rooms).
    "vitality": {"name": "Vitality", "kind": "regen_pct",
                 "values": [0.005, 0.0075, 0.01, 0.0125, 0.015, 0.0175, 0.02]},
    "edge": {"name": "Edge", "kind": "crit_chance",
             "values": [0.01, 0.015, 0.02, 0.025, 0.03, 0.04, 0.05]},
}


def flask_tier_max(room):
    return max(1, min(7, 1 + int(room) // EH_FLASK_TIER_PER_ROOMS))


def roll_flask(room, tier=None, kind=None):
    """Roll one flask: random archetype + depth-scaled tier (1–7).

    Pass ``tier`` to force a specific grade (milestone flasks); pass ``kind``
    to force an archetype (merchant wares).
    """
    kind_key = kind if kind in FLASK_ARCHETYPES else random.choice(
        list(FLASK_ARCHETYPES.keys()))
    archetype = FLASK_ARCHETYPES[kind_key]
    if tier is None:
        tier = random.randint(1, flask_tier_max(room))
    tier = max(1, min(7, int(tier)))
    flask = {
        "kind": kind_key,
        "type": archetype["kind"],
        "name": archetype["name"],
        "tier": tier,
        "value": archetype["values"][tier - 1],
        "stat": random.choice(list(ATTRIBUTES)) if kind_key == "might" else None,
    }
    flask["label"] = format_flask_label(flask)
    return flask


def format_flask_label(flask):
    value = flask.get("value", 0)
    kind = flask.get("type")
    if kind in ("damage_boost", "eh_ele_dmg", "defense_pct", "crit_chance"):
        amt = f"{round(value * 100)}%"
    elif kind == "regen_pct":
        amt = f"{value * 100:g}%"
    else:
        amt = f"+{value}"
    extra = ""
    if kind == "stat" and flask.get("stat"):
        extra = f" {flask['stat']}"
    if kind == "damage_boost":
        return f"{flask['name']} Flask (T{flask['tier']}) — +{amt} damage dealt"
    if kind == "eh_ele_dmg":
        return f"{flask['name']} Flask (T{flask['tier']}) — +{amt} elemental damage"
    if kind == "defense_pct":
        return f"{flask['name']} Flask (T{flask['tier']}) — −{amt} damage taken"
    if kind == "crit_chance":
        return f"{flask['name']} Flask (T{flask['tier']}) — +{amt} crit chance"
    if kind == "regen":
        return f"{flask['name']} Flask (T{flask['tier']}) — regain {value} HP per round"
    if kind == "regen_pct":
        return f"{flask['name']} Flask (T{flask['tier']}) — regain {amt} max HP per round"
    return f"{flask['name']} Flask (T{flask['tier']}) — {amt}{extra}"


def format_flask_summary(records):
    """Return a compact total of an actor's flask effects (EH inventory tab).

    Example: ``"+14% dmg · +4% elem · −6% taken · +0.5% HP/round · +2% crit ·
    +6 Learning"``. Legacy/unknown records are skipped. Used to show each
    actor's running total beside their name in the Flask Effects section
    (2026-10-08 request).
    """
    totals = {}
    stats = {}
    flat_regen = 0
    for rec in records or []:
        eff = _flask_effect_from_record(rec)
        if not eff:
            continue
        kind = eff.get("type")
        val = eff.get("value", 0) or 0
        if kind == "stat":
            stat = eff.get("stat")
            if stat:
                stats[stat] = stats.get(stat, 0) + val
            continue
        if kind == "regen":
            flat_regen += val
            continue
        totals[kind] = totals.get(kind, 0) + val

    def pct(v):
        return f"{v * 100:g}"

    parts = []
    if totals.get("damage_boost"):
        parts.append(f"+{pct(totals['damage_boost'])}% dmg")
    if totals.get("eh_ele_dmg"):
        parts.append(f"+{pct(totals['eh_ele_dmg'])}% elem")
    if totals.get("defense_pct"):
        parts.append(f"\u2212{pct(totals['defense_pct'])}% taken")
    if totals.get("crit_chance"):
        parts.append(f"+{pct(totals['crit_chance'])}% crit")
    if totals.get("regen_pct"):
        parts.append(f"+{pct(totals['regen_pct'])}% HP/round")
    if flat_regen:
        parts.append(f"+{flat_regen:g} HP/round")
    # Stable attribute order for the Might flasks
    from resources.races_classes import ATTRIBUTES
    for stat in ATTRIBUTES:
        if stats.get(stat):
            parts.append(f"+{stats[stat]:g} {stat}")
    return " \u00b7 ".join(parts)


def apply_flask(player, actor, flask):
    """Consume `flask` on `actor` (permanent for the run). Returns a record.

    The Tower doubles the value of every flask drunk AFTER it is taken —
    retroactivity is inherent (earlier records keep their stored value).
    """
    mult = flask_effect_multiplier(player)
    value = flask["value"] * mult
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    effect = {"type": flask["type"], "value": value}
    if flask.get("stat"):
        effect["stat"] = flask["stat"]
    _apply_permanent_effect(actor, effect, label=f"{flask['name']} Flask")
    label = flask["label"] + (" ×2" if mult != 1.0 else "")
    record = {"name": flask["name"], "tier": flask["tier"],
              "label": label, "effect": dict(effect)}
    state = ensure_eh_state(player)
    key = actor_key(actor, player)
    state.setdefault("actor_flasks", {}).setdefault(key, []).append(record)
    _refresh_tower_drain(player)
    flask["consumed"] = True
    state["pending_flask"] = None
    return record


# ═══════════════════════════════════════════════════════════════════════════
# Entropy battle-start debuffs (docs §2.4)
# ═══════════════════════════════════════════════════════════════════════════

# Pool uses player-capable appliers only; `curse` is excluded because the
# curse debuff is indefinite (no tick-out) and would stack across battles.
ENTROPY_DEBUFF_POOL = (
    "poison", "bleed", "burn", "weaken", "slow",
    "blind", "silence", "confusion", "dread", "damage_taken_up",
)

# Entropy Afflictions (docs §2.4 redesign, locked 2026-10-06): as Entropy
# climbs it permanently acquires random affliction types — one distinct type
# per EH_ENTROPY_AFFLICTION_EVERY stacks, visible in the inventory tab.
# Battle-start debuffs roll from the ACQUIRED set only (merciful early game;
# negative-card-like persistence; random identity — "a burn Entropy").
ENTROPY_AFFLICTION_INFO = {
    "poison": ("Poison", "damage each turn"),
    "bleed": ("Bleed", "damage each turn"),
    "burn": ("Burn", "rising burn damage each turn"),
    "weaken": ("Weaken", "reduced damage dealt"),
    "slow": ("Slow", "acts later in the turn order"),
    "blind": ("Blind", "attacks can miss"),
    "silence": ("Silence", "cannot use skills"),
    "confusion": ("Confusion", "may act unpredictably"),
    "dread": ("Dread", "attacks may fail outright"),
    "damage_taken_up": ("Exposure", "takes increased damage"),
}


def _sync_entropy_afflictions(state, total):
    """Top the affliction set up to ``total // EH_ENTROPY_AFFLICTION_EVERY``.

    Types are drawn without replacement; once every type is owned, nothing
    further is added. Mutates + returns ``state["entropy_afflictions"]``.
    """
    owned = state.setdefault("entropy_afflictions", [])
    target = min(len(ENTROPY_DEBUFF_POOL),
                 int(total) // EH_ENTROPY_AFFLICTION_EVERY)
    remaining = [t for t in ENTROPY_DEBUFF_POOL if t not in owned]
    while len(owned) < target and remaining:
        pick = random.choice(remaining)
        remaining.remove(pick)
        owned.append(pick)
    return owned


_BS_DOT_BASE = {1: 2, 2: 4, 3: 6, 4: 8}
_BS_DURATION = {1: 2, 2: 2, 3: 3, 4: 3}
_BS_WEAKEN = {1: 0.15, 2: 0.20, 3: 0.25, 4: 0.30}
_BS_DT = {1: 0.08, 2: 0.10, 3: 0.12, 4: 0.15}
_BS_CURSE_PENALTY = {1: 2, 2: 3, 3: 4, 4: 5}


def battle_start_tier(player):
    total = get_entropy_total(player)
    return max(1, min(4, 1 + total // EH_BS_TIER_STEP))


def _apply_one_entropy_debuff(actor, debuff_type, tier):
    """Apply one random Entropy debuff via the shared status-effect helpers."""
    from combat import status_effects as se
    from combat.combat_io import c_print

    duration = _BS_DURATION[tier]
    name = actor.get("name", "You")
    if debuff_type == "poison":
        dmg = _BS_DOT_BASE[tier] + random.randint(0, 2)
        se.apply_poison(actor, dmg, duration)
        msg = f"Entropy grips {name} — poison {dmg}×{duration}t!"
    elif debuff_type == "bleed":
        dmg = _BS_DOT_BASE[tier] + 2
        se.apply_bleed(actor, dmg, duration, source="entropy")
        msg = f"Entropy tears at {name} — bleed {dmg}×{duration}t!"
    elif debuff_type == "burn":
        tier_val = min(5, max(1, tier))
        se.apply_burn(actor, tier=tier_val, duration=duration)
        msg = f"Entropy ignites {name} — burning (T{tier_val})!"
    elif debuff_type == "weaken":
        se.apply_weaken(actor, penalty_pct=_BS_WEAKEN[tier], duration=duration)
        msg = f"Entropy saps {name} — weakened (−{round(_BS_WEAKEN[tier] * 100)}%)!"
    elif debuff_type == "slow":
        se.apply_slow_to_player(actor, duration=duration)
        msg = f"Entropy slows {name} to a crawl!"
    elif debuff_type == "blind":
        se.apply_blind(actor, duration=duration)
        msg = f"Entropy clouds {name}'s sight — blinded!"
    elif debuff_type == "silence":
        se.apply_silence(actor, duration=duration)
        msg = f"Entropy seals {name}'s voice — silenced!"
    elif debuff_type == "confusion":
        se.apply_confusion_to_player(actor, duration=duration)
        msg = f"Entropy scrambles {name}'s thoughts — confused!"
    elif debuff_type == "dread":
        se.apply_dread(actor, duration=duration)
        msg = f"Dread coils around {name}!"
    else:  # damage_taken_up
        value = _BS_DT[tier]
        se.apply_damage_taken_up(actor, value, duration)
        msg = f"Entropy exposes {name} — +{round(value * 100)}% damage taken!"
    # Mark the applied debuff type so the run-exit sweep strips leftovers —
    # this covers entries the application merely refreshed/merged into
    # (playtest: a pre-marking DT+8% survived suspend because the refresh
    # path created no new entry to tag).
    for entry in actor.get("active_debuffs", []):
        if entry.get("type") == debuff_type:
            entry["_eh_entropy"] = True
    c_print(f"  🌀 {msg}")


def apply_entropy_battle_start(player):
    """Round-1 hook: party suffers debuffs drawn from Entropy Afflictions.

    Battles only roll from the afflictions already acquired (docs §2.4) — the
    set grows by one distinct random type per ``EH_ENTROPY_AFFLICTION_EVERY``
    stacks and is shown in the inventory tab. No afflictions yet → no
    battle-start pressure (merciful early game).
    """
    if not in_run(player):
        return 0
    state = ensure_eh_state(player)
    owned = list(state.get("entropy_afflictions") or [])
    if not owned:
        return 0
    tier = battle_start_tier(player)
    actors = [player] + _alive_active_allies(player)
    applied = 0
    for actor in actors:
        count = 1
        if random.random() < EH_BS_SECOND_CHANCE[tier]:
            count += 1
        for debuff_type in random.sample(owned, min(count, len(owned))):
            _apply_one_entropy_debuff(actor, debuff_type, tier)
            applied += 1
    return applied


# ═══════════════════════════════════════════════════════════════════════════
# Milestones
# ═══════════════════════════════════════════════════════════════════════════

def get_milestone_rewards(player, room):
    """Return the milestone reward events for clearing `room` (not yet granted).

    Event kinds: ``high_flask``, ``boon``, ``trophy``, ``beating_root``.
    One-time grants are reported only once (flag-checked here; claiming is the
    caller's job via :func:`claim_milestone`).
    """
    room = int(room)
    events = []
    if room >= EH_MILESTONE_FLASK_EVERY and room % EH_MILESTONE_FLASK_EVERY == 0:
        events.append({"kind": "high_flask"})
    if room >= EH_MILESTONE_BOON_EVERY and room % EH_MILESTONE_BOON_EVERY == 0:
        events.append({"kind": "boon"})
    trophy = TROPHY_GRANTS.get(room)
    if trophy and not player.get(f"eh_trophy_{trophy}"):
        events.append({"kind": "trophy", "item_id": trophy})
    if room >= EH_BEATING_ROOT_FIRST and room % EH_BEATING_ROOT_EVERY == 0:
        flag = f"eh_root_{room}"
        if not player.get(flag):
            events.append({"kind": "beating_root", "flag": flag})
    return events


def claim_milestone(player, event):
    """Mark a one-time milestone event as claimed. Returns True if it was new."""
    kind = event.get("kind")
    if kind == "trophy":
        flag = f"eh_trophy_{event['item_id']}"
        if player.get(flag):
            return False
        player[flag] = True
        return True
    if kind == "beating_root":
        flag = event.get("flag") or f"eh_root_{ensure_eh_state(player).get('room', 0)}"
        if player.get(flag):
            return False
        player[flag] = True
        return True
    return True  # high_flask / boon are repeatable every milestone


# ═══════════════════════════════════════════════════════════════════════════
# Beating Root — per-actor third accessory slot (docs §10.6, Phase 5)
# ═══════════════════════════════════════════════════════════════════════════

def consume_beating_root(player, actor):
    """Consume one Beating Root; open `actor`'s permanent 3rd accessory slot.

    The item is consumed only on success. The unlock persists on the actor
    (player or ally) across saves, house round-trips, and runs.
    Returns a result message.
    """
    from inventory import remove_item_by_reference
    name = "You" if actor is player else actor.get("name", "the ally")
    if actor.get("acc3_unlocked"):
        return f"{name} has already taken a root — the third slot is open."
    item = next((i for i in player.get("inventory", [])
                 if i.get("special") == "beating_root"), None)
    if item is None:
        return "No Beating Root in the bag."
    if not remove_item_by_reference(player, item, 1):
        return "No Beating Root in the bag."
    actor["acc3_unlocked"] = True
    actor.setdefault("equipped", {}).setdefault("accessory3", None)
    if actor is player:
        return ("The root sinks into your chest — a third accessory slot "
                "opens. Equip it in Inventory → Stats & Equip.")
    return (f"The root sinks into {name}'s chest — a third accessory slot "
            f"opens for her. Equip it in Inventory → Allies.")


# ═══════════════════════════════════════════════════════════════════════════
# Payout / wipe / strip
# ═══════════════════════════════════════════════════════════════════════════

def compute_payout(player):
    """End-of-run gold: rooms cleared × Entropy weight (full on any outcome)."""
    state = ensure_eh_state(player)
    rooms = int(state.get("room", 0))
    if rooms <= 0:
        return 0
    rooms_gold = sum(EH_GOLD_BASE + EH_GOLD_PER_ROOM * r for r in range(1, rooms + 1))
    weight = 1.0 + get_entropy_total(player) * EH_GOLD_PER_ENTROPY
    gold_mult, _mote = joker_economy_multipliers(player)
    return int(rooms_gold * weight * gold_mult)


def grant_payout(player, death=False):
    """Grant the run payout. Death defers it to after the death toll.

    Returns ``(amount, deferred)``. On death the amount is stashed in
    ``player["_eh_pending_payout"]`` and paid by ``utils.apply_death_penalty``
    AFTER the 20% toll, so the payout itself is exempt.
    """
    amount = compute_payout(player)
    if amount <= 0:
        return 0, False
    if death:
        player["_eh_pending_payout"] = player.get("_eh_pending_payout", 0) + amount
        return amount, True
    player["gold"] = player.get("gold", 0) + amount
    return amount, False


def strip_event_horizon_effects(player, legacy=False):
    """Detach every Event Horizon buff/debuff entry from the whole roster.

    Covers flask/card buffs (``source == EH_SOURCE``), the Entropy stat
    penalty entry, entropy-tagged bleeds (``source == "entropy"``), and any
    leftover battle-start debuffs marked ``_eh_entropy`` — including their
    flag mirrors (``slowed``/``blinded``/``silenced``/``dreaded``) so no HUD
    tag can outlive the rift.
    ``legacy=True`` additionally sweeps pre-marking leftovers that carry no
    tag: unmarked ``damage_taken_up`` entries matching the Entropy tier
    ladder (0.08/0.10/0.12/0.15, remaining ≤ 3). Run data
    (``actor_flasks``/cards/entropy) stays in state for
    :func:`restore_event_horizon_effects`.
    """
    flag_map = {"slow": "slowed", "blind": "blinded",
                "silence": "silenced", "dread": "dreaded"}
    legacy_dt = (0.08, 0.10, 0.12, 0.15)
    actors = [player] + list(player.get("allies", []))
    for actor in actors:
        removed_types = set()
        for key in ("active_buffs", "active_debuffs"):
            entries = actor.get(key)
            if not entries:
                continue
            kept = []
            for entry in entries:
                strip = (entry.get("source") == EH_SOURCE
                         or entry.get("source") == "entropy"
                         or entry.get("type") == "eh_entropy"
                         or entry.get("eh_joker")
                         or entry.get("_eh_entropy"))
                if not strip and legacy and entry.get("type") == "damage_taken_up":
                    try:
                        val = float(entry.get("value", 0))
                    except (TypeError, ValueError):
                        val = 0.0
                    if (any(abs(val - v) < 1e-9 for v in legacy_dt)
                            and int(entry.get("remaining", 99)) <= 3):
                        strip = True
                if strip:
                    if key == "active_debuffs":
                        removed_types.add(entry.get("type"))
                else:
                    kept.append(entry)
            actor[key] = kept
        # Clear flag mirrors whose only source was a stripped entropy debuff
        remaining_types = {e.get("type")
                           for e in actor.get("active_debuffs", [])}
        for dtype, flag in flag_map.items():
            if dtype in removed_types and dtype not in remaining_types:
                actor.pop(flag, None)
        # Joker behaviour flags never outlive the run.
        for key in ("_eh_joker_weakness_gate", "_eh_joker_emperor",
                    "_eh_emperor_used", "_eh_emperor_saved",
                    "_eh_joker_init", "_eh_joker_miss",
                    "_eh_joker_skill_mult", "_eh_joker_basic_mult",
                    "_eh_joker_sun_crit", "_eh_joker_sun_pen",
                    "_eh_joker_lifesteal", "_eh_joker_healing_mult",
                    "_eh_joker_star",
                    "_eh_joker_skip_r1", "_eh_joker_priestess",
                    "_eh_joker_priestess_pen"):
            actor.pop(key, None)
    return True


def _actor_for_key(player, key):
    """Resolve an ``actor_key`` back to the actor dict (player or ally)."""
    if key == "player":
        return player
    for ally in player.get("allies", []):
        if actor_key(ally, player) == key:
            return ally
    return None


def _flask_effect_from_record(rec):
    """Rebuild a flask's buff effect from its log record (legacy-safe)."""
    eff = rec.get("effect")
    if eff:
        return dict(eff)
    # Legacy records predate effect storage — rebuild from archetype + tier.
    for arch in FLASK_ARCHETYPES.values():
        if arch["name"] == rec.get("name"):
            tier = max(1, min(7, int(rec.get("tier", 1))))
            out = {"type": arch["kind"], "value": arch["values"][tier - 1]}
            if arch["kind"] == "stat":
                out["stat"] = rec.get("stat") or "Strength"
            return out
    return None


def restore_event_horizon_effects(player):
    """Re-attach run effects from state (call when entering/resuming).

    Idempotent: strips any existing EH entries first, then rebuilds from
    ``player["event_horizon"]`` — Entropy (sync), positive cards, and every
    per-actor flask entry.
    """
    strip_event_horizon_effects(player)
    state = ensure_eh_state(player)
    sync_entropy(player)
    for card in state.get("positive_cards", []):
        _apply_card_effects_to_roster(player, card)
    for key, recs in (state.get("actor_flasks") or {}).items():
        actor = _actor_for_key(player, key)
        if actor is None:
            continue
        for rec in recs:
            eff = _flask_effect_from_record(rec)
            if eff:
                _apply_permanent_effect(
                    actor, eff, label=f"{rec.get('name', 'Flask')} Flask")
    for joker in state.get("joker_cards", []):
        _apply_joker_to_roster(player, joker)
    _refresh_joker_actor_flags(player)
    _refresh_tower_drain(player)
    return True


def clear_run(player):
    """Wipe the run (keep best_room, rush records + player-level flags)."""
    state = ensure_eh_state(player)
    best = max(int(state.get("best_room", 0)), int(state.get("room", 0)))
    rush_clears = int(state.get("rush_clears", 0) or 0)
    rush_best = int(state.get("rush_best", 0) or 0)
    strip_event_horizon_effects(player, legacy=True)
    player["event_horizon"] = _default_state()
    player["event_horizon"]["best_room"] = best
    player["event_horizon"]["rush_clears"] = rush_clears
    player["event_horizon"]["rush_best"] = rush_best
    player.pop("_eh_in_run", None)
    return best


def payout_summary(amount):
    return f"  ◎ The Horizon pays out: +{amount} gold."


def build_run_summary(player, payout=0, fatal=False):
    """Snapshot a run BEFORE ``clear_run`` for the aftermath display.

    Returns ``{"subtitle": str, "lines": [str], "data": {...}}``; the GUI
    aftermath dialog renders ``lines`` and tests read ``data``.
    """
    state = ensure_eh_state(player)
    room = int(state.get("room", 0) or 0)
    best = max(int(state.get("best_room", 0) or 0), room)
    motes = int(state.get("motes", 0) or 0)
    entropy = get_entropy_total(player)
    pct = int(round(entropy_stat_penalty(entropy) * 100))
    pos = [dict(c) for c in state.get("positive_cards", [])]
    neg = [dict(c) for c in state.get("negative_cards", [])]
    jokers = [dict(r) for r in state.get("joker_cards", [])]
    flasks = {k: [dict(r) for r in v]
              for k, v in (state.get("actor_flasks") or {}).items()}
    total_flasks = sum(len(v) for v in flasks.values())

    lines = [
        f"Rooms cleared this run  : {room}",
        f"Deepest room ever       : {best}",
    ]
    if state.get("rush_mode"):
        felled = len(state.get("rush_defeated") or [])
        total = int(state.get("rush_total", 0) or 0)
        lines.append(f"Boss Rush               : {felled}/{total} echoes felled")
    lines += [
        f"Final Entropy           : {entropy} stacks   (all attributes −{pct}%)",
        "",
    ]
    if payout:
        if fatal:
            lines.append(f"Gold recovered          : +{payout}  "
                         "(paid after the death toll — exempt from it)")
        else:
            lines.append(f"Gold paid out           : +{payout}")
    else:
        lines.append("Gold paid out           : none")
    lines.append(f"Horizon Motes forfeited : {motes}")
    lines.append(f"Flasks consumed         : {total_flasks}")
    lines.append("")
    lines.append("CARDS TAKEN (run-wide)")
    if pos:
        for c in pos:
            lines.append(f"  + {c.get('name', '?')} (T{c.get('tier', '?')})"
                         f" — {c.get('desc', '')}")
    else:
        lines.append("  + (none)")
    if neg:
        for c in neg:
            lines.append(f"  − {c.get('name', '?')} (T{c.get('tier', '?')})"
                         f" — {c.get('desc', '')}"
                         f"  [Entropy +{c.get('entropy_cost', 0)}]")
    else:
        lines.append("  − (none)")
    lines.append("")
    lines.append("TAROT — the Joker's hand")
    if jokers:
        for j in jokers:
            lines.append(f"  ♠ {j.get('name', '?')} — {j.get('desc', '')}")
    else:
        lines.append("  ♠ (none)")
    lines.append("")
    lines.append("FLASK EFFECTS (by actor)")
    if flasks:
        for key in sorted(flasks):
            who = "You" if key == "player" else str(key).split(":", 1)[-1]
            lines.append(f"  {who}:")
            for rec in flasks[key]:
                lines.append(f"    • {rec.get('label') or rec.get('name', '?')}")
    else:
        lines.append("  (no flasks consumed)")

    subtitle = ("The run ends in death — the Horizon keeps its part."
                if fatal else
                "The Horizon releases you. The run is over.")
    return {
        "subtitle": subtitle,
        "lines": lines,
        "data": {
            "room": room,
            "best": best,
            "motes": motes,
            "rush": ({"felled": len(state.get("rush_defeated") or []),
                      "total": int(state.get("rush_total", 0) or 0)}
                     if state.get("rush_mode") else None),
            "entropy": entropy,
            "entropy_pct": pct,
            "payout": payout,
            "fatal": bool(fatal),
            "positive": [(c.get("name"), c.get("tier")) for c in pos],
            "negative": [(c.get("name"), c.get("tier")) for c in neg],
            "tarot": [r.get("name") for r in jokers],
            "flasks": {k: [r.get("label") for r in v]
                       for k, v in flasks.items()},
            "total_flasks": total_flasks,
        },
    }


# ═══════════════════════════════════════════════════════════════════════════
# World-map site + travel (Phase 3)
# ═══════════════════════════════════════════════════════════════════════════

EVENT_HORIZON_NAME = "The Event Horizon"
EVENT_HORIZON_POSITION = (730, 280)   # fixed remote coordinate (docs §6.1)


def site_unlocked(player):
    """The distortion appears on the world map once the gate is met."""
    return int(player.get("max_floor", 1) or 1) >= EH_UNLOCK_MAX_FLOOR


def event_horizon_site(player):
    """Site info dict for the world map / journeys (None while locked)."""
    if not site_unlocked(player):
        return None
    from wild_dungeons import find_nearest_city
    return {
        "id": "event_horizon",
        "name": EVENT_HORIZON_NAME,
        "position": EVENT_HORIZON_POSITION,
        "nearest_city": find_nearest_city(EVENT_HORIZON_POSITION),
        "biome": "magical",
        "level": int(player.get("max_floor", 1) or 1),
    }


def build_journey_to_site(player):
    """City route + off-road leg to the distortion (mirrors wild journeys)."""
    site = event_horizon_site(player)
    if site is None:
        return None
    from wild_dungeons import build_journey_to_dungeon
    return build_journey_to_dungeon(player, site, to="horizon")


def begin_run(player, origin_city=None):
    """Start a fresh run if none is active; a suspended run is kept as-is."""
    state = ensure_eh_state(player)
    if not state.get("run_active"):
        state["run_active"] = True
        state["room"] = 0
        state["current_room"] = None
        state["pending_flask"] = None
        state["actor_flasks"] = {}
        state["positive_cards"] = []
        state["negative_cards"] = []
        state["motes"] = 0
        state["entropy"] = 0
        state["trial_done_for"] = 0
        state["pending_trophies"] = []
        state["started_day"] = int(player.get("day", 0) or 0)
        # A normal fresh run must never inherit a rush queue.
        state["rush_mode"] = False
        state["rush_queue"] = []
        state["rush_defeated"] = []
        state["rush_total"] = 0
        state["rush_level"] = 0
    if origin_city:
        state["origin_city"] = origin_city
    return state


def begin_rush(player, origin_city=None):
    """Start a fresh Boss Rush run. Returns ``(ok, unmet_reasons)``.

    Requires the minimum-progress gates (docs §6.4) and no active/suspended
    run; the pool is every superboss already felled in the overworld.
    """
    if ensure_eh_state(player).get("run_active"):
        return False, ["a run is already turning"]
    ok, reasons = boss_rush_requirements(player)
    if not ok:
        return False, reasons
    state = begin_run(player, origin_city)
    pool = build_boss_rush_pool(player)
    state["rush_mode"] = True
    state["rush_queue"] = [b["id"] for b in pool]
    state["rush_defeated"] = []
    state["rush_total"] = len(pool)
    state["rush_level"] = rush_level_for_pool(pool)
    return True, []
