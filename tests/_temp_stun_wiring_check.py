# Temp verification (2026-10-26): party-side STUN is now wired.
# - consume_stun() costs one action and clears the flag + marker entries
# - handle_player_turn / handle_ally_turn skip the action when stunned
# - clear_battle_scoped_state scrubs stale stuns at combat end
import sys
sys.path.insert(0, "c:/Code/Pandemonium")

import combat.player_actions as pact
import combat.ally as amod
import combat.combat_ui as cui
import combat.status_effects as se
import combat.combat_engine as eng

pact.c_print = lambda *a, **k: ""
amod.c_print = lambda *a, **k: ""
cui.print_combat_hud = lambda *a, **k: None

CHECKS = []


def check(name, cond, detail=""):
    CHECKS.append((name, bool(cond), detail))
    print(("PASS" if cond else "FAIL") + f" — {name}" + (f" ({detail})" if detail and not cond else ""))


def no_prompt(*a, **k):
    raise AssertionError("c_input was called while stunned")


ATTRS = ("Strength", "Constitution", "Dexterity", "Wisdom", "Learning", "Charisma")


def make_player():
    p = {"name": "hanafi", "class": "Warrior", "level": 15,
         "current_hp": 90, "passive_unlocked": True,
         "attributes": {a: 10 for a in ATTRS},
         "level_hp_bonus": 0,
         "equipped": {"weapon": None, "armor": None, "accessory1": None, "accessory2": None},
         "active_buffs": [], "active_debuffs": [],
         "elemental_dmg": {}, "elemental_res": {},
         "inventory": [], "allies": [],
         "skills": [], "skill_mastery": {}, "skill_cooldowns": {}}
    p["attributes"]["Strength"] = 0
    return p


def make_ally():
    return {"name": "Harpy Scout", "is_ally": True, "race": "Harpy", "level": 15,
            "current_hp": 57, "max_hp": 57,
            "attributes": {a: 10 for a in ATTRS},
            "equipped": {"weapon": None, "armor": None, "accessory1": None, "accessory2": None},
            "active_buffs": [], "active_debuffs": [],
            "elemental_dmg": {}, "elemental_res": {},
            "skills": [], "skill_mastery": {}, "skill_cooldowns": {}}


def make_enemy(hp=1000):
    return {"name": "Plasma Sphere", "hp": hp, "max_hp": hp, "con_mod": 0,
            "dex_mod": 0, "str_mod": 0,
            "active_debuffs": [], "active_buffs": [],
            "elemental_res": {}, "elemental_dmg": {}}


# 1. Clean actor is not stunned
p = make_player()
check("clean actor is not stunned", se.consume_stun(p) is False)

# 2. Stun consumed once: flag cleared, marker entries removed, other debuffs kept
p["stunned"] = True
p["active_debuffs"] = [{"type": "stun", "remaining": 1},
                       {"type": "poison", "damage": 1, "remaining": 2}]
check("stunned actor loses the action", se.consume_stun(p) is True)
check("stunned flag cleared", p["stunned"] is False)
check("stun marker entries removed", [d["type"] for d in p["active_debuffs"]] == ["poison"],
      str(p["active_debuffs"]))
check("second consume does nothing", se.consume_stun(p) is False)

# 3. handle_player_turn skips the action without prompting
p = make_player()
p["stunned"] = True
p["active_debuffs"] = [{"type": "stun", "remaining": 1}]
enemies = [make_enemy()]
_old_player_input = pact.c_input
pact.c_input = no_prompt
try:
    result, new_def = pact.handle_player_turn(p, enemies, 0, 0, 0, 0, 0, 0)
finally:
    pact.c_input = _old_player_input
check("player turn skipped by stun", result == "continue" and new_def is False,
      f"result={result} new_def={new_def}")
check("player stun cleared after skip", p.get("stunned") is False
      and not any(d.get("type") == "stun" for d in p["active_debuffs"]))

# 4. handle_ally_turn skips the action without prompting
ally = make_ally()
ally["stunned"] = True
ally["active_debuffs"] = [{"type": "stun", "remaining": 1}]
p = make_player()
p["allies"] = [ally]
_old_ally_input = amod.c_input
amod.c_input = no_prompt
try:
    result = amod.handle_ally_turn(ally, p, [make_enemy()], 0, 0, 0, 0, 0, 0)
finally:
    amod.c_input = _old_ally_input
check("ally turn skipped by stun", result == "continue", f"result={result}")
check("ally stun cleared after skip", ally.get("stunned") is False
      and not any(d.get("type") == "stun" for d in ally["active_debuffs"]))

# 5. Regression: an unstunned player still acts normally afterwards
p = make_player()
enemies = [make_enemy()]
_old_player_input = pact.c_input
pact.c_input = lambda *a, **k: "a"
try:
    result, _ = pact.handle_player_turn(p, enemies, 0, 0, 0, 0, 0, 0)
finally:
    pact.c_input = _old_player_input
check("unstunned player still attacks", result == "continue" and enemies[0]["hp"] < enemies[0]["max_hp"],
      f"result={result} enemy_hp={enemies[0]['hp']}")

# 6. Combat-end scrub clears stale stuns (e.g. fight ended before the skip)
p = make_player()
a1 = make_ally()
p["stunned"] = True
p["active_debuffs"] = [{"type": "stun", "remaining": 1}]
a1["stunned"] = True
a1["active_debuffs"] = [{"type": "stun", "remaining": 1},
                        {"type": "bleed", "damage": 2, "remaining": 2}]
p["allies"] = [a1]
eng.clear_battle_scoped_state(p)
check("combat end clears player stun", p["stunned"] is False
      and not any(d.get("type") == "stun" for d in p["active_debuffs"]))
check("combat end clears ally stun but keeps other debuffs",
      a1["stunned"] is False
      and [d["type"] for d in a1["active_debuffs"]] == ["bleed"],
      str(a1["active_debuffs"]))

failed = [c for c in CHECKS if not c[1]]
print(f"\n{len(CHECKS) - len(failed)}/{len(CHECKS)} checks passed")
sys.exit(1 if failed else 0)
