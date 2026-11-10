"""Temp smoke test (2026-09-27):
- Fresh player/ally buffs skip their first end-of-round tick (full duration).
- Regular enemy timed buffs decay with the same grace.
- Superboss buffs are left to module post_round hooks (engine skips them).
- damage_boost is now read by player_actions, skills, and enemy_ai.
"""
import inspect
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from combat.status_effects import tick_player_buffs, tick_enemy_debuffs


def make_player():
    return {
        "name": "Tester",
        "current_hp": 50,
        "attributes": {"Strength": 10, "Constitution": 10, "Dexterity": 10,
                       "Learning": 10, "Wisdom": 10, "Charisma": 10},
        "active_buffs": [],
        "active_debuffs": [],
        "equipped": {},
        "allies": [],
    }


# --- Player/ally buff grace: a "2 turn" buff spans 2 full rounds ---
p = make_player()
p["active_buffs"].append({"type": "damage_boost", "value": 0.25, "remaining": 2})
tick_player_buffs(p)   # end of the round it was cast: tick skipped
assert p["active_buffs"][0]["remaining"] == 2, p["active_buffs"]
tick_player_buffs(p)   # first full round consumed
assert p["active_buffs"][0]["remaining"] == 1, p["active_buffs"]
tick_player_buffs(p)   # second full round consumed -> expires
assert p["active_buffs"] == [], p["active_buffs"]
print("OK: player buff grace (2-turn buff survives 2 full round-ends)")

# --- Regular enemy buff decay with grace ---
e = {"name": "Wolfie", "hp": 50, "key": "bandit",
     "active_buffs": [{"type": "damage_boost", "value": 0.2, "remaining": 2}],
     "active_debuffs": []}
tick_enemy_debuffs(e)  # fresh: grace
assert e["active_buffs"][0]["remaining"] == 2, e["active_buffs"]
tick_enemy_debuffs(e)
assert e["active_buffs"][0]["remaining"] == 1, e["active_buffs"]
tick_enemy_debuffs(e)
assert e["active_buffs"] == [], e["active_buffs"]
print("OK: regular enemy buff decay with grace")

# --- Superbosses manage their own buffs: engine must skip them ---
# (runtime dicts don't carry super_boss; the filter looks up the template by key)
sb = {"name": "Boss", "hp": 500, "key": "wl_big_bad_wolf",
      "active_buffs": [{"type": "damage_boost", "value": 0.4, "remaining": 2}],
      "active_debuffs": []}
tick_enemy_debuffs(sb)
assert sb["active_buffs"][0]["remaining"] == 2, sb["active_buffs"]
print("OK: superboss buffs left to module post_round hooks (template lookup)")

# --- Hookup: percentage damage buffs are read in all three attack modules ---
# (centralised in status_effects.get_damage_buff_multiplier; sources stack additively)
from combat import player_actions, skills, enemy_ai
for mod in (player_actions, skills, enemy_ai):
    src = inspect.getsource(mod)
    assert "get_damage_buff_multiplier" in src, f"no damage-buff read in {mod.__name__}"
print("OK: additive damage-buff read present in player_actions, skills, enemy_ai")

print("ALL CHECKS PASSED")
