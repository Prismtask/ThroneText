"""Diagnostic: shared dungeon depth per biome (2026-11-04).

Run: .venv\\Scripts\\python.exe tests/_diag_biome_depth.py [slot ...]

Read-only smoke test: loads real savefiles, runs `ensure_player_fields()`
in memory (which performs the depth migration), and verifies that

  * same-biome city records share one max_floor,
  * per-city floor cursors are untouched,
  * no record's depth is lowered, and
  * biome gates count unique biomes.

It never calls save_game().
"""

import io
import os
import sys
from contextlib import redirect_stdout

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

try:  # piped/redirected runs on Windows default to cp932
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from character import ensure_player_fields
from leveling import cities_in_biome, get_biomes_cleared_to_cap
from resources.cities import CITIES
from save_load import load_game

failures = []


def check(label, ok, detail=""):
    print(f"  {'OK  ' if ok else 'FAIL'} {label}"
          + (f" — {detail}" if detail else ""))
    if not ok:
        failures.append(label)


def snapshot(player):
    return {
        cid: {"floor": int(prog.get("floor", 1) or 1),
              "max_floor": int(prog.get("max_floor", 1) or 1)}
        for cid, prog in (player.get("city_floors") or {}).items()
        if isinstance(prog, dict)
    }


def run_slot(slot):
    player = load_game(slot)
    print(f"\n=== savegame_{slot} ===")
    if not isinstance(player, dict):
        check("save loads", False, "not found / invalid")
        return
    before = snapshot(player)
    before_global = int(player.get("max_floor", 1) or 1)

    with redirect_stdout(io.StringIO()):
        ensure_player_fields(player)

    after = snapshot(player)
    check("records retained", set(before) <= set(after),
          f"{len(before)} -> {len(after)}")

    for cid, prog in before.items():
        check(f"{cid}: depth never lowered",
              after.get(cid, {}).get("max_floor", 1) >= prog["max_floor"],
              f"{prog['max_floor']} -> {after.get(cid, {}).get('max_floor')}")
        check(f"{cid}: floor cursor untouched",
              after.get(cid, {}).get("floor") == prog["floor"],
              f"{prog['floor']} -> {after.get(cid, {}).get('floor')}")

    for cid, prog in after.items():
        biome = CITIES.get(cid, {}).get("biome", "temperate")
        group = [c for c in cities_in_biome(cid) if c in after]
        depths = sorted({after[c]["max_floor"] for c in group})
        check(f"{cid}: biome '{biome}' shares depth", len(depths) == 1,
              f"{group} -> {depths}")

    check("global max_floor never lowered",
          int(player.get("max_floor", 1) or 1) >= before_global,
          f"{before_global} -> {player.get('max_floor')}")
    check("wonderland gate counts biomes",
          len(get_biomes_cleared_to_cap(player, 20)) <= 13,
          f"{sorted(get_biomes_cleared_to_cap(player, 20))}")

    print(f"  biomes at Floor 20: {sorted(get_biomes_cleared_to_cap(player, 20))}")
    print(f"  biomes at Floor 40: {sorted(get_biomes_cleared_to_cap(player, 40))}")


def main():
    slots = [int(a) for a in sys.argv[1:] if a.isdigit()] or [1, 2, 3]
    for slot in slots:
        run_slot(slot)
    print(f"\n{'FAILED: ' + ', '.join(failures) if failures else 'biome depth OK'}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
