"""Temp smoke test (2026-09-27): Aura of Despair rework + fear immunity wiring.

- damage_taken_up: apply / refresh / additive multiplier / tick expiry.
- has_fear_immunity + wl_floor_bosses._apply_fear respects it.
- get_damage_taken_multiplier read in all four attack paths.
- Wicked Witch fear respects immunity.
"""
import inspect
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from combat.status_effects import (
    apply_damage_taken_up, get_damage_taken_multiplier, has_fear_immunity,
    tick_enemy_debuffs,
)

# ── damage_taken_up: apply / refresh / stack / read ──
e = {"name": "Mook", "hp": 100, "active_debuffs": [], "active_buffs": []}
assert apply_damage_taken_up(e, 0.15, 3) == "applied"
assert abs(get_damage_taken_multiplier(e) - 1.15) < 1e-9
assert apply_damage_taken_up(e, 0.10, 5) == "refreshed"  # keeps stronger value, longer duration
d = e["active_debuffs"][0]
assert abs(d["value"] - 0.15) < 1e-9 and d["remaining"] == 5, d
# a second source stacks additively
e["active_debuffs"].append({"type": "damage_taken_up", "value": 0.15, "remaining": 3})
assert abs(get_damage_taken_multiplier(e) - 1.30) < 1e-9
print("OK: apply / refresh / additive multiplier")

# ── tick expiry + message ──
t = {"name": "Mook", "hp": 100, "key": "bandit",
     "active_debuffs": [{"type": "damage_taken_up", "value": 0.15, "remaining": 2}],
     "active_buffs": []}
_msgs, _died = tick_enemy_debuffs(t)
assert t["active_debuffs"][0]["remaining"] == 1, t["active_debuffs"]
msgs, _died = tick_enemy_debuffs(t)
assert t["active_debuffs"] == [], t["active_debuffs"]
assert any("despair" in m.lower() for m in msgs), msgs
print("OK: damage_taken_up ticks and expires")

# ── fear immunity helper + floor-boss fear blocked ──
p = {"name": "You", "active_buffs": []}
assert not has_fear_immunity(p)
p["active_buffs"].append({"type": "fear_immunity", "remaining": 2})
assert has_fear_immunity(p)

from combat.wl_floor_bosses import _apply_fear
immune = {"name": "You", "current_hp": 50,
          "active_buffs": [{"type": "fear_immunity", "remaining": 2}],
          "active_debuffs": []}
assert _apply_fear(immune, duration=2) == "immune"
assert not immune["active_debuffs"], immune["active_debuffs"]
open_target = {"name": "You", "current_hp": 50, "active_buffs": [], "active_debuffs": []}
assert _apply_fear(open_target, duration=2) == "applied"
assert open_target["active_debuffs"][0]["type"] == "fear"
print("OK: floor-boss fear blocked by immunity, applied without it")

# ── read sites: all four attack paths + witch immunity wiring ──
from combat import player_actions, skills, ally, ally_skills, wicked_witch
for mod in (player_actions, skills, ally, ally_skills):
    assert "get_damage_taken_multiplier" in inspect.getsource(mod), mod.__name__
assert "has_fear_immunity" in inspect.getsource(wicked_witch)
print("OK: damage_taken_up read in 4 attack paths; wicked witch immunity wired")

print("ALL CHECKS PASSED")
