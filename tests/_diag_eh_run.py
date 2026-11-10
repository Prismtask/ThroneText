"""
tests/_diag_eh_run.py — Manual end-to-end check of the Event Horizon run loop.

Not collected by pytest (underscore prefix). Run directly:
    c:/Code/Pandemonium/.venv/Scripts/python.exe tests/_diag_eh_run.py

Exercises dungeon.explore_dungeon's Event Horizon branch with stubbed I/O:
  A. Three rooms cleared → suspend (save & quit) — checkpoints, motes, flask log
  B. Abandon → payout paid, run wiped, exit to origin city
  C. Death → payout deferred (`_eh_pending_payout`), run wiped, gold untouched
  D. Trial scheduling — r10 spawns trial_neg, does not count as progress
  E. Milestone r50 — high flask + deep boon + trophy (+ pending-trophy retry)
  F. Rift shop — mote purchase + free visit flask
  G. Boss Rush — full circuit: queue order, flat scaling, payout + records
"""

import builtins
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import dungeon as dungeon_mod
import event_horizon as eh
import event_horizon_rooms as ehr
import inventory_ui
from resources.enemies import ENEMIES

# ── Stub I/O so the loop runs headless ──────────────────────────────────────
builtins.input = lambda *a, **k: ""
dungeon_mod.save_game = lambda p: None


def _fake_acquire(player, item):
    player.setdefault("inventory", []).append(item)
    return True


inventory_ui.prompt_acquire_item = _fake_acquire

_TEST_ENEMY = next(
    k for k, d in ENEMIES.items()
    if not d.get("boss") and not d.get("minion_only") and not d.get("super_boss")
    and not d.get("_shadow") and not d.get("_heroine")
)

# ── Scripting hooks ─────────────────────────────────────────────────────────
_SCRIPT = []     # _tmenu answers: int or callable(len(options) -> idx)
_CHOICES = []    # post_room_choice answers
_RESULTS = []    # combat results
_ROOMS = []      # scripted rooms (generate_room patch)

_ORIG_GENERATE = ehr.generate_room
_ORIG_CHOICE = ehr.post_room_choice


def _scripted_tmenu(options, prompt="", **kwargs):
    if _SCRIPT:
        item = _SCRIPT.pop(0)
        return item(len(options)) if callable(item) else item
    return 0


def _scripted_choice(player):
    return _CHOICES.pop(0) if _CHOICES else "suspend"


def _scripted_combat(player, enemies, **kwargs):
    return _RESULTS.pop(0) if _RESULTS else "victory"


def _scripted_rooms(player):
    return _ROOMS.pop(0)


ehr._tmenu = _scripted_tmenu


def _base_player():
    return {
        "name": "TestHero",
        "level": 50,
        "level_cap": 80,
        "exp": 100,
        "attributes": {"Strength": 40, "Constitution": 40, "Dexterity": 30,
                       "Learning": 20, "Wisdom": 20, "Charisma": 20},
        "current_hp": 300,
        "gold": 0,
        "inventory": [],
        "allies": [],
        "skills": [],
        "skill_cooldowns": {},
        "active_buffs": [],
        "active_debuffs": [],
        "active_bounties": [],
        "city_floors": {"solmere": {"floor": 3, "max_floor": 12}},
        "location": "dungeon",
        "origin_city": "solmere",
        "time_minutes": 480,
        "day": 10,
        "daily_effects": {},
        "floor": 12,          # transient pre-run cursor — must be restored
        "max_floor": 30,
        "save_slot": 99,
    }


def _start_run(player, room=0):
    state = eh.ensure_eh_state(player)
    state["run_active"] = True
    state["room"] = room
    player["_eh_in_run"] = True
    return state


def _snapshot(player):
    return {
        "max_floor": player["max_floor"],
        "city_floors": {k: dict(v) for k, v in player["city_floors"].items()},
        "floor": player["floor"],
    }


def _assert_protected(player, snap, ctx):
    assert player["max_floor"] == snap["max_floor"], f"{ctx}: max_floor changed"
    assert player["city_floors"] == snap["city_floors"], f"{ctx}: city_floors changed"
    assert player["floor"] == snap["floor"], f"{ctx}: floor not restored ({player['floor']})"
    assert "_eh_prev_floor" not in player, f"{ctx}: floor snapshot leaked"


def _combat_room(n):
    return {"type": "combat", "number": n, "enemies": [_TEST_ENEMY]}


def test_suspend_after_three_rooms():
    random.seed(201)
    player = _base_player()
    state = _start_run(player)
    snap = _snapshot(player)
    # Pre-marking leftover (like the reported stuck DT+8%): must be swept by
    # the legacy pass on exit, even without an `_eh_entropy` tag.
    player["active_debuffs"].append({"type": "damage_taken_up",
                                     "value": 0.08, "remaining": 2})

    _ROOMS[:] = [_combat_room(1), _combat_room(2), _combat_room(3)]
    _CHOICES[:] = ["continue", "continue", "suspend"]
    _RESULTS[:] = ["victory", "victory", "victory"]
    _SCRIPT[:] = []
    ehr.generate_room = _scripted_rooms
    ehr.post_room_choice = _scripted_choice

    result = dungeon_mod.explore_dungeon(player, combat_override=_scripted_combat)

    assert result == "save_exit", result
    assert state["room"] == 3, state["room"]
    assert state["motes"] == 6 + 7 + 7, state["motes"]
    assert state["run_active"] is True, "suspend must keep the run"
    assert state["current_room"] is None
    assert "_eh_in_run" not in player
    assert len(state["actor_flasks"].get("player", [])) == 3, state["actor_flasks"]
    assert state["entropy"] == 0  # rooms 1-4 carry no Entropy yet
    # Suspend detaches rift effects: nothing may leak into cities (§6.3).
    for actor in [player] + player.get("allies", []):
        assert not any(b.get("source") == eh.EH_SOURCE
                       for b in actor["active_buffs"]), "suspend leaked buffs"
        assert not any(d.get("type") == "eh_entropy" or d.get("_eh_entropy")
                       for d in actor["active_debuffs"]), "suspend leaked debuffs"
        assert not any(d.get("type") == "damage_taken_up"
                       for d in actor["active_debuffs"]), "legacy DT leaked"
    # Restore round-trips the flask effects (data survived the strip).
    eh.restore_event_horizon_effects(player)
    assert any(b.get("source") == eh.EH_SOURCE for b in player["active_buffs"]), \
        "restore did not re-attach flask effects"
    eh.strip_event_horizon_effects(player)
    _assert_protected(player, snap, "suspend")
    print("[OK] suspend: 3 rooms, 20 motes, 3 flask logs, run kept, floor restored")


def test_abandon_pays_and_wipes():
    random.seed(202)
    player = _base_player()
    state = _start_run(player)
    snap = _snapshot(player)

    _ROOMS[:] = [_combat_room(1)]
    _CHOICES[:] = ["abandon"]
    _RESULTS[:] = ["victory"]
    _SCRIPT[:] = []
    ehr.generate_room = _scripted_rooms
    ehr.post_room_choice = _scripted_choice

    result = dungeon_mod.explore_dungeon(player, combat_override=_scripted_combat)

    assert result == "eh_quit", result
    expected = int((eh.EH_GOLD_BASE + eh.EH_GOLD_PER_ROOM * 1) * 1.0)
    assert player["gold"] == expected, (player["gold"], expected)
    assert player["event_horizon"]["run_active"] is False
    assert player["event_horizon"]["motes"] == 0
    assert player["event_horizon"]["actor_flasks"] == {}
    assert player["location"] == "solmere", player["location"]
    assert "_eh_in_run" not in player
    assert not any(b.get("source") == eh.EH_SOURCE for b in player["active_buffs"])
    summary = player.get("_eh_last_summary")
    assert summary, "abandon must stash a GUI run summary"
    assert summary["data"]["payout"] == expected, summary["data"]
    assert summary["data"]["room"] == 1, summary["data"]
    assert summary["data"]["total_flasks"] == 1, summary["data"]
    assert any("Run" in l or "Rooms cleared" in l for l in summary["lines"])
    _assert_protected(player, snap, "abandon")
    print(f"[OK] abandon: +{expected} gold, run wiped, exited to origin city, "
          f"summary stashed")


def test_death_defers_payout():
    random.seed(203)
    player = _base_player()
    state = _start_run(player)
    snap = _snapshot(player)

    _ROOMS[:] = [_combat_room(1), _combat_room(2)]
    _CHOICES[:] = ["continue"]
    _RESULTS[:] = ["victory", "dead"]
    _SCRIPT[:] = []
    ehr.generate_room = _scripted_rooms
    ehr.post_room_choice = _scripted_choice

    result = dungeon_mod.explore_dungeon(player, combat_override=_scripted_combat)

    assert result == "dead", result
    expected = int((eh.EH_GOLD_BASE + eh.EH_GOLD_PER_ROOM * 1) * 1.0)
    assert player.get("_eh_pending_payout") == expected, player.get("_eh_pending_payout")
    assert player["gold"] == 0, "payout must be deferred, not banked"
    assert player["event_horizon"]["run_active"] is False
    assert "_eh_in_run" not in player
    summary = player.get("_eh_last_summary")
    assert summary, "death must stash a GUI run summary"
    assert summary["data"]["fatal"] is True, summary["data"]
    assert summary["data"]["payout"] == expected, summary["data"]
    _assert_protected(player, snap, "death")
    print(f"[OK] death: payout {expected}g deferred, run wiped, gold untouched, "
          f"fatal summary stashed")


def test_trial_after_ten():
    random.seed(204)
    player = _base_player()
    state = _start_run(player, room=10)

    # Real generator: deterministic trial detection (no combat rolling needed)
    trial = _ORIG_GENERATE(player)
    assert trial["type"] == "trial_neg" and trial["for_room"] == 10, trial

    state["room"] = 20
    state["trial_done_for"] = 0
    trial_neg = _ORIG_GENERATE(player)
    assert trial_neg["type"] == "trial_neg" and trial_neg["for_room"] == 20, trial_neg

    state["room"] = 30
    state["trial_done_for"] = 0
    trial_pos = _ORIG_GENERATE(player)
    assert trial_pos["type"] == "trial_pos" and trial_pos["for_room"] == 30, trial_pos

    # Now run the loop past a trial + r11 with scripted rooms
    state["room"] = 10
    state["trial_done_for"] = 0
    snap = _snapshot(player)
    _ROOMS[:] = [{"type": "trial_neg", "for_room": 10}, _combat_room(11)]
    _CHOICES[:] = ["continue", "suspend"]
    _RESULTS[:] = ["victory"]
    ehr.generate_room = _scripted_rooms
    ehr.post_room_choice = _scripted_choice
    _SCRIPT[:] = [0, 0]  # trial card pick #1, flask drinker

    result = dungeon_mod.explore_dungeon(player, combat_override=_scripted_combat)

    assert result == "save_exit", result
    assert state["trial_done_for"] == 10, state["trial_done_for"]
    assert state["room"] == 11, state["room"]
    assert len(state["negative_cards"]) == 1, state["negative_cards"]
    card_cost = state["negative_cards"][0]["entropy_cost"]
    assert state["entropy"] == eh.base_entropy_for_room(11) + card_cost, state["entropy"]
    assert state["motes"] == 12 + 11, state["motes"]  # trial 10+10//5; r11 6+11//2
    _assert_protected(player, snap, "trial")
    print("[OK] trial: r10 -> trial (no progress) -> r11; entropy + motes correct")


def test_milestone_r50_trophies():
    random.seed(205)
    player = _base_player()
    state = _start_run(player, room=49)
    state["pending_trophies"] = ["old_dopo_robe"]  # simulate an earlier full bag
    snap = _snapshot(player)

    _ROOMS[:] = [_combat_room(50)]
    _CHOICES[:] = ["suspend"]
    _RESULTS[:] = ["victory"]
    ehr.generate_room = _scripted_rooms
    ehr.post_room_choice = _scripted_choice
    _SCRIPT[:] = [0, 0, 0, 2]  # high-flask, boon, room-flask, refuse the r50 spread

    result = dungeon_mod.explore_dungeon(player, combat_override=_scripted_combat)

    assert result == "save_exit", result
    assert state["room"] == 50
    inv_ids = [it.get("id") for it in player["inventory"]]
    assert "chance_and_choice" in inv_ids, inv_ids
    assert "old_dopo_robe" in inv_ids, inv_ids
    assert player.get("eh_trophy_chance_and_choice") is True
    assert state["pending_trophies"] == [], state["pending_trophies"]
    assert len(state["positive_cards"]) == 1, state["positive_cards"]
    assert state.get("joker_cards", []) == [], "refused Joker must not be stored"
    flask_log = state["actor_flasks"].get("player", [])
    assert any(f["tier"] >= 6 for f in flask_log), flask_log  # milestone flask
    _assert_protected(player, snap, "milestone")
    print("[OK] milestones r50: high flask + deep boon + trophy (+ pending retry)")


def test_shop_purchase():
    random.seed(206)
    player = _base_player()
    state = _start_run(player)
    state["room"] = 40          # tier cap 7 → wares at T6/T7
    state["motes"] = 5000

    # drink visit flask, buy first ware, pick drinker, leave
    _SCRIPT[:] = [0, 0, lambda n: n - 1, lambda n: n - 1]
    ehr.handle_eh_shop(player)

    recs = state["actor_flasks"].get("player", [])
    assert len(recs) == 2, f"visit + purchased flask expected, got {len(recs)}"
    bought = recs[-1]
    assert bought["tier"] >= 6, bought         # grade scales with room
    full = ehr._shop_flask_price(bought["tier"])
    spent = 5000 - state["motes"]
    # One ware per visit is 40% off — the bought ware may or may not be it.
    assert spent in (full, max(1, int(full * 0.6))), (spent, full)
    print(f"[OK] shop: bought {bought['label']}, {spent} motes spent (full {full})")


def test_joker_offer():
    random.seed(207)
    player = _base_player()
    state = _start_run(player, room=24)
    snap = _snapshot(player)

    _ROOMS[:] = [_combat_room(25)]
    _CHOICES[:] = ["suspend"]
    _RESULTS[:] = ["victory"]
    ehr.generate_room = _scripted_rooms
    ehr.post_room_choice = _scripted_choice
    _SCRIPT[:] = [0, 0, 0]  # milestone flask, room flask, keep the first dealt face

    result = dungeon_mod.explore_dungeon(player, combat_override=_scripted_combat)

    assert result == "save_exit", result
    assert state["room"] == 25
    jokers = state.get("joker_cards", [])
    assert len(jokers) == 1, jokers
    rec = jokers[0]
    # Off-deck: entropy is rooms-only (no card costs), payout untouched
    assert state["entropy"] == eh.base_entropy_for_room(25), state["entropy"]
    # Suspend detaches the Joker with everything else; restore re-attaches
    assert not any(b.get("label") == rec["name"] for b in player["active_buffs"])
    assert not any(d.get("label") == rec["name"] for d in player["active_debuffs"])
    eh.restore_event_horizon_effects(player)

    entry_effects = [e for e in (rec.get("effects") or [])
                     if e.get("type") not in ("flask_double", "world_suppress")]
    draws = rec.get("drawback") or {}
    draws = draws if isinstance(draws, list) else [draws]
    entry_draws = [d for d in draws if d.get("type") in
                   ("damage_taken_up", "slow", "damage_boost", "defense_pct",
                    "crit_chance", "eh_ele_dmg", "regen_pct", "stat")]
    if entry_effects or entry_draws:
        attached = [e for e in player["active_buffs"] + player["active_debuffs"]
                    if e.get("label") == rec["name"]]
        assert attached, f"restore did not re-attach {rec['name']}"
    eh.strip_event_horizon_effects(player)
    _assert_protected(player, snap, "joker")
    print(f"[OK] joker: dealt at r25, kept {rec['name']}, off-deck, detach+restore")


def test_boss_rush_full_circuit():
    random.seed(208)
    player = _base_player()
    player["defeated_superbosses"] = ["broodmother_vileheart", "black_silence",
                                      "white_knight"]
    player["max_floor"] = 40
    state = eh.ensure_eh_state(player)
    state["best_room"] = 50
    ok, reasons = eh.begin_rush(player, "solmere")
    assert ok, reasons
    player["_eh_in_run"] = True
    snap = _snapshot(player)

    calls = []

    def rush_override(spec, floor):
        calls.append((spec["boss_id"], spec["index"], spec["total"]))
        return "victory"

    # Normal room generation must never run during a rush.
    ehr.generate_room = lambda p: (_ for _ in ()).throw(
        AssertionError("normal room rolled during rush"))
    ehr.post_room_choice = _scripted_choice
    _CHOICES[:] = ["continue", "continue"]
    _SCRIPT[:] = []   # no flask drinker menus — flasks removed from the rush

    result = dungeon_mod.explore_dungeon(
        player, combat_override=_scripted_combat,
        superboss_override=rush_override)

    assert result == "eh_rush_complete", result
    assert calls == [("broodmother_vileheart", 1, 3),
                     ("black_silence", 2, 3),
                     ("white_knight", 3, 3)], calls
    after = eh.ensure_eh_state(player)
    assert after["rush_clears"] == 1, after["rush_clears"]
    assert after["rush_best"] == 3, after["rush_best"]
    assert after["rush_mode"] is False and after["run_active"] is False
    assert after["motes"] == 0 and after["actor_flasks"] == {}
    # Payout rooms 1-3 (12+14+16) + full-circuit bonus (100 + 25×3).
    assert player["gold"] == 42 + 175, player["gold"]
    summary = player.get("_eh_last_summary")
    assert summary and summary["data"]["rush"] == {"felled": 3, "total": 3}
    assert summary["data"]["motes"] == 0, summary["data"]["motes"]
    assert summary["data"]["entropy"] == 0, summary["data"]["entropy"]
    assert summary["data"]["total_flasks"] == 0, summary["data"]["total_flasks"]
    assert player["location"] == "solmere", player["location"]
    assert "_eh_in_run" not in player
    _assert_protected(player, snap, "boss rush")
    ehr.generate_room = _ORIG_GENERATE
    print(f"[OK] boss rush: 3 echoes felled in ramp order, +{42 + 175} gold, "
          f"records kept, no motes/flasks (pure linear)")


def run_all():
    test_suspend_after_three_rooms()
    test_abandon_pays_and_wipes()
    test_death_defers_payout()
    test_trial_after_ten()
    test_milestone_r50_trophies()
    test_shop_purchase()
    test_joker_offer()
    test_boss_rush_full_circuit()
    print("\nAll Event Horizon Phase 2 run diagnostics passed.")


if __name__ == "__main__":
    run_all()
