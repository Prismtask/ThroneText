"""
tests/_diag_wild_run.py — Manual end-to-end check of the wild dungeon loop.

Not collected by pytest (underscore prefix). Run directly:
    c:/Code/Pandemonium/.venv/Scripts/python.exe tests/_diag_wild_run.py

Exercises dungeon.explore_dungeon's wild branch with stubbed I/O:
  A. Full victory — floors cleared, reward pool granted, bookkeeping done
  B. Flee — nearest city, dungeon retryable (still active, attempted)
  C. Death — returns "dead", run state cleaned
  D. Crumble mid-run — ruin expires during a floor, safe exit
  E. Entry with an already-gone dungeon — safe exit
"""

import builtins
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Force UTF-8 output so piped runs don't crash on legacy console encodings
# (e.g. cp932) when printing em-dashes / box glyphs.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import dungeon as dungeon_mod
import inventory_ui
from resources.enemies import ENEMIES

# ── Stub I/O so the loop runs headless ──────────────────────────────────────
builtins.input = lambda *a, **k: ""              # answer every _tpause()
dungeon_mod.save_game = lambda p: None           # don't write save files


def _fake_acquire(player, item):
    player.setdefault("inventory", []).append(item)
    return True


inventory_ui.prompt_acquire_item = _fake_acquire


def _check_combat_context(player, kwargs, ctx):
    """The wild loop must expose the floor index for headers while the
    combat `floor` argument keeps carrying the ruin's level (scaling)."""
    wild = next(d for d in player["wild_dungeons"]["active"]
                if d["id"] == player["wild_dungeon_id"])
    floor_idx = int(wild.get("highest_floor_cleared", 0)) + 1
    expected = f"{floor_idx}/{wild['total_floors']}"
    assert player.get("_combat_floor_label") == expected, \
        f"{ctx}: floor label {player.get('_combat_floor_label')!r} != {expected!r}"
    assert kwargs.get("floor") == wild["level"], \
        f"{ctx}: combat floor arg {kwargs.get('floor')} != level {wild['level']}"


def _combat_victory(player, enemies, **kwargs):
    _check_combat_context(player, kwargs, "victory combat")
    return "victory"


def _combat_flee(player, enemies, **kwargs):
    _check_combat_context(player, kwargs, "flee combat")
    return "fled"


def _combat_dead(player, enemies, **kwargs):
    _check_combat_context(player, kwargs, "death combat")
    return "dead"


# Deterministic 10-room floors of pure combat
_TEST_ENEMY = next(
    k for k, d in ENEMIES.items()
    if not d.get("boss") and not d.get("minion_only") and not d.get("super_boss")
    and not d.get("_shadow") and not d.get("_heroine")
)


def _fake_generate_floor(floor, region=None, player=None):
    rooms = [{"type": "combat", "enemies": [_TEST_ENEMY]} for _ in range(9)]
    rooms.append({"type": "combat", "enemies": [_TEST_ENEMY], "is_boss": True})
    return rooms


dungeon_mod.generate_floor = _fake_generate_floor


def _base_player():
    return {
        "name": "TestHero",
        "level": 5,
        "level_cap": 20,
        "exp": 100,
        "attributes": {"Strength": 8, "Constitution": 8, "Dexterity": 5,
                       "Learning": 5, "Wisdom": 5, "Charisma": 5},
        "current_hp": 60,
        "gold": 500,
        "inventory": [],
        "allies": [],
        "skills": [],
        "skill_cooldowns": {},
        "active_buffs": [],
        "active_debuffs": [],
        "active_bounties": [],
        "city_floors": {"elderfen": {"floor": 1, "max_floor": 1}},
        "location": "dungeon",
        "origin_city": "elderfen",
        "time_minutes": 480,
        "day": 10,
        "daily_effects": {},
        "floor": 5,          # transient pre-run cursor — must be restored
        "max_floor": 5,
        "save_slot": 99,
    }


def _dungeon(dungeon_id="wild_7", expire=20, floors=2, pool=None):
    return {
        "id": dungeon_id,
        "name": "Forgotten Crypt",
        "biome": "swamp",
        "level": 8,
        "total_floors": floors,
        "highest_floor_cleared": 0,
        "position": [320, 240],
        "spawn_day": 7,
        "expire_day": expire,
        "seed_city": "elderfen",
        "nearest_city": "elderfen",
        "attempted": False,
        "reward_pool": pool or [
            {"item_id": "iron_sword", "rarity": "epic"},
            {"item_id": "healing_potion", "rarity": "common"},
            {"item_id": "greater_healing_potion", "rarity": "uncommon"},
        ],
    }


def _attach(player, dungeon):
    player["wild_dungeons"] = {
        "active": [dungeon], "completed": [], "next_id": 8, "last_spawn_day": 7,
    }
    player["wild_dungeon_id"] = dungeon["id"]


def _protection_snapshot(player):
    """Capture progress state that wild runs must NEVER modify."""
    return {
        "max_floor": player["max_floor"],
        "city_floors": {k: dict(v) for k, v in player["city_floors"].items()},
        "floor": player["floor"],
    }


def _assert_protected(player, snap, ctx):
    assert player["max_floor"] == snap["max_floor"], \
        f"{ctx}: max_floor changed from {snap['max_floor']} to {player['max_floor']}"
    assert player["city_floors"] == snap["city_floors"], \
        f"{ctx}: city floor progress changed"
    assert player["floor"] == snap["floor"], \
        f"{ctx}: transient floor {snap['floor']} not restored (got {player['floor']})"
    assert "_wild_prev_floor" not in player, f"{ctx}: floor snapshot leaked"
    assert "_combat_floor_label" not in player, f"{ctx}: combat floor label leaked"
    assert "wild_dungeon_id" not in player, f"{ctx}: wild id leaked"


def test_victory():
    random.seed(101)
    player = _base_player()
    dungeon = _dungeon()
    _attach(player, dungeon)
    snap = _protection_snapshot(player)

    result = dungeon_mod.explore_dungeon(player, combat_override=_combat_victory)

    assert result == "wild_complete", result
    _assert_protected(player, snap, "victory")
    assert player["location"] == "elderfen", player["location"]
    assert dungeon["highest_floor_cleared"] == 2, dungeon["highest_floor_cleared"]
    assert player["wild_dungeons"]["active"] == []
    assert "wild_7" in player["wild_dungeons"]["completed"]

    inv = player["inventory"]
    assert any(it.get("id") == "iron_sword" and it.get("rarity") == "epic"
               for it in inv), "previewed epic sword should be granted"
    assert player["gold"] > 500, player["gold"]
    assert player["exp"] > 100 or player["level"] > 5

    info = player.pop("_wild_completion", None)
    assert info and info["name"] == "Forgotten Crypt"
    assert info["gold"] > 0 and info["exp"] > 0
    assert len(info["items"]) >= 3, info["items"]
    assert not any(k.startswith("saved_wild_") for k in player)

    # Completion journal entry: name + level + day (date rendered by the UI)
    wild_entries = [e for e in player["journal"]["events"]
                    if e.get("tag") == "[WILD]"]
    assert len(wild_entries) == 1, wild_entries
    entry = wild_entries[0]
    assert "Forgotten Crypt" in entry["name"], entry
    assert "Lv 8" in entry["desc"], entry
    assert entry["day"] == player["day"], entry
    print("[OK] victory: pool granted, dungeon recorded, exited to nearest city")
    print("     max_floor/city_floors untouched, transient floor restored")
    print("     journal entry: name + level + day recorded [WILD]")


def test_flee():
    random.seed(102)
    player = _base_player()
    dungeon = _dungeon()
    _attach(player, dungeon)
    snap = _protection_snapshot(player)

    result = dungeon_mod.explore_dungeon(player, combat_override=_combat_flee)

    assert result == "fled", result
    _assert_protected(player, snap, "flee")
    assert player["location"] == "elderfen", player["location"]
    # Retryable: still active, flagged as attempted, progress untouched
    assert player["wild_dungeons"]["active"][0]["id"] == "wild_7"
    assert player["wild_dungeons"]["active"][0]["attempted"] is True
    assert dungeon["highest_floor_cleared"] == 0
    assert not any(k.startswith("saved_wild_") for k in player)
    print("[OK] flee: nearest city, ruin stays retryable")


def test_death():
    random.seed(103)
    player = _base_player()
    dungeon = _dungeon()
    _attach(player, dungeon)
    snap = _protection_snapshot(player)

    result = dungeon_mod.explore_dungeon(player, combat_override=_combat_dead)

    assert result == "dead", result
    _assert_protected(player, snap, "death")
    assert player["wild_dungeons"]["active"][0]["attempted"] is True
    assert not any(k.startswith("saved_wild_") for k in player)
    print("[OK] death: run state cleaned, 'dead' returned for penalty flow")
    print("     max_floor/city_floors untouched, transient floor restored")


def test_crumble_mid_run():
    """The ruin expires between floors — the run exits safely."""
    random.seed(104)
    player = _base_player()
    dungeon = _dungeon(floors=3)
    _attach(player, dungeon)
    snap = _protection_snapshot(player)

    from wild_dungeons import expire_dungeons

    calls = {"n": 0}

    def _combat_expire(player_, enemies, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            # First combat of the run: end of floor 1 → ruin crumbles
            player_["day"] = 99
            expire_dungeons(player_)
        return "victory"

    result = dungeon_mod.explore_dungeon(player, combat_override=_combat_expire)

    assert result == "fled", result
    _assert_protected(player, snap, "crumble")
    assert player["location"] == "elderfen", player["location"]
    assert not any(k.startswith("saved_wild_") for k in player)
    print("[OK] crumble mid-run: safe exit to nearest city")
    print("     max_floor/city_floors untouched, transient floor restored")


def test_entry_with_gone_dungeon():
    random.seed(105)
    player = _base_player()
    player["wild_dungeon_id"] = "wild_404"
    player["wild_dungeons"] = {
        "active": [], "completed": [], "next_id": 9, "last_spawn_day": 7,
    }
    snap = _protection_snapshot(player)

    result = dungeon_mod.explore_dungeon(player, combat_override=_combat_victory)

    assert result == "fled", result
    _assert_protected(player, snap, "missing-ruin entry")
    assert player["location"] == "elderfen"
    print("[OK] missing ruin on entry: safe exit")


def test_floor_clear_choices():
    """floor_clear_override drives the GUI floor-clear window choices."""
    random.seed(106)
    seen = []

    def _override_continue(player_, **kwargs):
        seen.append(kwargs)
        return "continue"

    # (a) continue → descends and completes the run
    player = _base_player()
    dungeon = _dungeon(floors=2)
    _attach(player, dungeon)
    result = dungeon_mod.explore_dungeon(
        player, combat_override=_combat_victory,
        floor_clear_override=_override_continue)
    assert result == "wild_complete", result
    assert len(seen) == 1, seen          # only the intermediate floor
    assert seen[0]["floor_num"] == 1 and seen[0]["total_floors"] == 2, seen
    assert dungeon["highest_floor_cleared"] == 2
    print("[OK] floor-clear window: 'continue' descends to the next floor")

    # (b) city → leaves the ruin (retryable), floor progress kept
    player = _base_player()
    dungeon = _dungeon(floors=3)
    _attach(player, dungeon)
    snap = _protection_snapshot(player)
    result = dungeon_mod.explore_dungeon(
        player, combat_override=_combat_victory,
        floor_clear_override=lambda player_, **kw: "city")
    assert result == "fled", result
    _assert_protected(player, snap, "floor-clear city")
    assert player["location"] == "elderfen", player["location"]
    assert dungeon["highest_floor_cleared"] == 1
    assert not any(k.startswith("saved_wild_") for k in player)
    print("[OK] floor-clear window: 'city' exits to nearest city, progress kept")

    # (c) save_exit → suspends; resume keys stay so re-entry continues
    player = _base_player()
    dungeon = _dungeon(floors=3)
    _attach(player, dungeon)
    snap = _protection_snapshot(player)
    result = dungeon_mod.explore_dungeon(
        player, combat_override=_combat_victory,
        floor_clear_override=lambda player_, **kw: "save_exit")
    assert result == "save_exit", result
    assert player["floor"] == snap["floor"], player["floor"]
    assert "_wild_prev_floor" not in player
    assert "_combat_floor_label" not in player
    assert dungeon["highest_floor_cleared"] == 1
    assert player["wild_dungeon_id"] == "wild_7"   # kept for resume
    assert player["max_floor"] == snap["max_floor"]
    assert player["city_floors"] == snap["city_floors"]
    print("[OK] floor-clear window: 'save_exit' suspends the run")


def main():
    test_victory()
    test_flee()
    test_death()
    test_crumble_mid_run()
    test_entry_with_gone_dungeon()
    test_floor_clear_choices()
    print("\nWild dungeon run smoke test PASSED.")


if __name__ == "__main__":
    main()
