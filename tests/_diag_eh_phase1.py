"""Phase 1 import/data sanity check for Event Horizon.

Manual diagnostic (run directly, not under pytest):
    c:/Code/Pandemonium/.venv/Scripts/python.exe tests/_diag_eh_phase1.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

FAILS = []


def check(label, cond, detail=""):
    status = "ok" if cond else "FAIL"
    print(f"[{status}] {label}" + (f" — {detail}" if detail and not cond else ""))
    if not cond:
        FAILS.append(label)


# 1. Imports of every touched module (catches cycles / syntax regressions)
import combat.stats          # noqa: E402
import combat.skills         # noqa: E402
import combat.ally           # noqa: E402
import combat.ally_skills    # noqa: E402
import combat.enemy_ai       # noqa: E402
import combat.combat_engine  # noqa: E402
import character             # noqa: E402
import utils                 # noqa: E402
import save_load             # noqa: E402
import event_horizon as eh   # noqa: E402

check("module imports", True)

# 2. Every weapon item has a formal weapon_type
from resources.items import ITEMS, build_item  # noqa: E402

weapons = {k: v for k, v in ITEMS.items() if v.get("slot") == "weapon"}
missing = [k for k, v in weapons.items() if not v.get("weapon_type")]
check("all weapons have weapon_type", not missing, f"missing: {missing}")
check("weapon count intact (51+)", len(weapons) >= 51, f"found {len(weapons)}")

swords = [k for k, v in weapons.items() if v.get("weapon_type") in
          ("sword", "blade", "greatsword", "rapier", "cutlass")]
check("sword family non-empty", len(swords) >= 8, f"{swords}")

# 3. Trophy item defs + build_item round-trip
for item_id in ("chance_and_choice", "old_dopo_robe", "piece_of_relationship"):
    item = build_item(item_id)
    check(f"build {item_id}", bool(item) and item.get("name"), repr(item))
    if item:
        check(f"{item_id} has special", bool(item.get("special")))
        check(f"{item_id} has description", bool(item.get("description")))
check("POR is player_only", bool(ITEMS["piece_of_relationship"].get("player_only")))

# 4. enemy_stats hook runs both outside and inside a run
from combat.stats import enemy_stats  # noqa: E402


def _fake_player(run=False):
    p = {
        "name": "Hero", "level": 50, "max_floor": 30, "gold": 0,
        "current_hp": 100, "max_hp": 100,
        "attributes": {a: 10 for a in ("Strength", "Constitution", "Dexterity",
                                       "Wisdom", "Learning", "Charisma")},
        "active_buffs": [], "active_debuffs": [], "allies": [],
    }
    state = eh.ensure_eh_state(p)
    if run:
        p["_eh_in_run"] = True
        state["run_active"] = True
        state["room"] = 20
    return p


enemy_key = next(iter(ITEMS and []), None) or "goblin_scout"
try:
    base = enemy_stats("goblin_scout", _fake_player(False))
    scaled = enemy_stats("goblin_scout", _fake_player(True))
    check("enemy_stats outside run", base["hp"] > 0)
    check("enemy_stats scaled inside run", scaled["hp"] > base["hp"],
          f"{base['hp']} -> {scaled['hp']}")
except KeyError:
    print("[skip] 'goblin_scout' not in ENEMIES — trying any enemy")
    from resources.enemies import ENEMIES  # noqa: E402
    k = next(kk for kk, vv in ENEMIES.items()
             if not vv.get("super_boss") and not vv.get("minion_only")
             and not vv.get("_heroin") and not vv.get("_heroine"))
    base = enemy_stats(k, _fake_player(False))
    scaled = enemy_stats(k, _fake_player(True))
    check(f"enemy_stats hook ({k})", scaled["hp"] > base["hp"],
          f"{base['hp']} -> {scaled['hp']}")

# 5. Entropy read in effective attribute
from combat.stats import get_effective_attribute  # noqa: E402

p = _fake_player(True)
eh.ensure_eh_state(p)["room"] = 60
eh.sync_entropy(p)
raw_total = get_effective_attribute(p, "Strength")
p2 = _fake_player(False)
check("entropy reduces attributes", raw_total < get_effective_attribute(p2, "Strength"),
      f"{raw_total}")

print()
if FAILS:
    print(f"FAILURES: {FAILS}")
    sys.exit(1)
print("All Phase 1 sanity checks passed.")
