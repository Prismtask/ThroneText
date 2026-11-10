"""Diagnostic: White Knight module + Last Oath wiring.

Run: python tests/_diag_white_knight.py
Exit code 0 = all checks passed.
"""
import sys

sys.path.insert(0, ".")

from resources.enemies import ENEMIES
from combat.stats import (
    enemy_stats, get_dodge_chance, roll_dodge,
    roll_skill_dodge, roll_accuracy_penalty,
)
from combat.white_knight import (
    _armor_mult_for, _set_dodge, combat_white_knight, BOSS_KEY,
)
from combat.weapon.last_oath import _actor_has_last_oath, try_last_oath_expose

failures = []


def check(cond, label):
    if cond:
        print(f"  PASS  {label}")
    else:
        print(f"  FAIL  {label}")
        failures.append(label)


print("== 1. YAML template + loader ==")
tpl = ENEMIES.get("white_knight")
check(tpl is not None, "white_knight template present")
check(abs(tpl.get("status_res", 0) - 0.75) < 1e-9, "status_res == 0.75")
check(tpl.get("race") == "Undead", "race Undead")
inst = enemy_stats("white_knight")
check(inst.get("level") == 48, "runtime level 48")
check(inst.get("status_res") == 0.75, "runtime status_res carried")
check(inst.get("elemental_res", {}).get("light") == 0.7, "blessed plate: light 0.7")
check(inst.get("elemental_res", {}).get("dark") == 1.3, "fallen weakness: dark 1.3")
check(inst.get("elemental_dmg", {}).get("light") == 1.4, "holy damage: light 1.4")

print("== 2. Expose -> armor mult math ==")
u = {"expose_stacks": 0}
check(_armor_mult_for(u) == 1.0, "0 stacks -> no CON ignore")
u["expose_stacks"] = 3
check(abs(_armor_mult_for(u) - 0.7) < 1e-9, "3 stacks -> 30% CON ignore")
u["expose_stacks"] = 6
check(abs(_armor_mult_for(u) - 0.4) < 1e-9, "6 stacks -> 60% CON ignore")
u["expose_stacks"] = 99
check(abs(_armor_mult_for(u) - 0.4) < 1e-9, "clamped at 60%")

print("== 3. Dodge cap override + state profile ==")
boss = {
    "name": "WK", "dex_mod": 15, "dodge_cap_override": 0.70,
    "active_buffs": [{"type": "evasion", "value": 1.0, "source": "wk_dodge"}],
}
att = {"name": "p", "dex_mod": 10}
chance = get_dodge_chance(boss, att)
check(abs(chance - 0.70) < 1e-9, "state dodge 70% beats the 50% enemy cap")
boss["dodge_cap_override"] = 0.55
chance = get_dodge_chance(boss, att)
check(abs(chance - 0.55) < 1e-9, "P1 dodge 55% (above normal cap)")
boss["dodge_cap_override"] = 0.35
chance = get_dodge_chance(boss, att)
check(abs(chance - 0.35) < 1e-9, "recovery window 35%")
_, chance = roll_dodge(boss, att, extra_chance=0.20)
check(abs(chance - 0.55) < 1e-9, "ally penalty +20 pushed 0.35->0.55 for the roll")

b2 = {"active_buffs": []}
_set_dodge(b2, 0.70, skill_dodge=0.5)
check(b2["dodge_cap_override"] == 0.70 and b2["skill_dodge_chance"] == 0.5,
      "_set_dodge sets cap + skill dodge")
check(sum(1 for b in b2["active_buffs"] if b.get("source") == "wk_dodge") == 1,
      "single wk_dodge buff")
_set_dodge(b2, 0.35)
check(b2["active_buffs"][0]["value"] == 0.35 and b2["skill_dodge_chance"] == 0.0,
      "_set_dodge updates in place and clears skill dodge")

print("== 4. Skill dodge: once per activation ==")
t = {"name": "T", "skill_dodge_chance": 1.0}
check(roll_skill_dodge(t) is True, "first roll dodges")
check(roll_skill_dodge(t) is False, "marked: no second roll same action")
t.pop("_skill_dodge_used")
check(roll_skill_dodge(t) is True, "reset marker -> rolls again")
plain = {"name": "P"}
check(roll_skill_dodge(plain) is False and "_skill_dodge_used" not in plain,
      "no chance -> no roll, no marker")

print("== 5. Accuracy penalty: once per action, capped ==")
a = {"name": "A", "ally_accuracy_penalty": 0.20}
first = roll_accuracy_penalty(a)
check(first in (True, False) and a.get("_accuracy_penalty_used") is True,
      "penalty rolls once and marks")
check(roll_accuracy_penalty(a) is False, "marked: no second roll same action")
z = {"name": "Z"}
check(roll_accuracy_penalty(z) is False and "_accuracy_penalty_used" not in z,
      "no penalty -> no roll")

print("== 6. Last Oath (Expose-on-hit reward) ==")
actor = {"equipped": {"weapon": {"special": "last_oath", "name": "Last Oath"}}}
check(_actor_has_last_oath(actor) is not None, "wielder detected")
target = {"name": "Dummy", "hp": 50, "con_mod": 8, "active_debuffs": []}
msg = try_last_oath_expose(actor, target, is_crit=False)
check(target["con_mod"] == 7 and msg, "normal hit: Expose -1 armor")
msg = try_last_oath_expose(actor, target, is_crit=True)
check(target["con_mod"] == 5 and msg, "crit: Expose -2 armor")
non = {"equipped": {"weapon": {"special": "captain_cutlass"}}}
check(try_last_oath_expose(non, target) is None, "non-wielder: no proc")

print("== 7. Entry point + item registration ==")
from resources.items import build_item
check(callable(combat_white_knight), "combat_white_knight callable")
item = build_item("last_oath", "unique")
check(item is not None and item.get("name") == "Last Oath", "Last Oath item builds")
check(item.get("drop_source") == "white_knight", "drop_source registered")

print("== 8. Phase floors (anti-skip / anti-one-shot) ==")
from combat.white_knight import _PhaseLockedKnight
k = _PhaseLockedKnight({"max_hp": 1500, "hp": 1500, "_wk_phase": 1, "_wk_round": 1})
k["hp"] = k["hp"] - 9999
check(k["hp"] == 975, "P1 floor: lethal burst clamps at 65% (975/1500)")
k["_wk_phase"] = 2
k["hp"] = 10
check(k["hp"] == 450, "P2 floor: clamps at 30% (450/1500)")
k["_wk_phase"] = 3
k["hp"] = 10
check(k["hp"] == 10, "P3: no floor - kill window open")
k2 = _PhaseLockedKnight({"max_hp": 1500, "hp": 1500, "_wk_phase": 1, "_wk_round": 1})
k2["hp"] = 1100
check(k2["hp"] == 1100, "damage above the floor is untouched")
k3 = _PhaseLockedKnight({"max_hp": 1500, "hp": 975, "_wk_phase": 1, "_wk_round": 1})
k3["hp"] = 900
check(k3["hp"] == 975, "P1: cannot dip below floor even by a small hit")

print("== 9. Shared-list contract (GUI HUD sees live damage) ==")
import random as _rnd

from combat.combat_io import set_io, reset_io
from resources.skill_loader import CLASS_SKILLS

_ATTRS = ("Strength", "Constitution", "Dexterity", "Wisdom", "Learning", "Charisma")


class _CapIO:
    """Swallows output; returns 'a' for action prompts, bails after N turns."""

    def __init__(self, max_turns=4):
        self.max_turns = max_turns
        self.turns = 0

    def print(self, *a, **k):
        pass

    def input(self, prompt=""):
        if "Choose" in str(prompt):
            self.turns += 1
            if self.turns > self.max_turns:
                raise KeyboardInterrupt
            return "a"
        return ""

    def clear(self):
        pass


_p = {"name": "Hero", "class": list(CLASS_SKILLS.keys())[0], "level": 50,
      "current_hp": 99999, "passive_unlocked": True,
      "attributes": {a: 40 for a in _ATTRS}, "level_hp_bonus": 0,
      "equipped": {"weapon": None, "armor": None, "accessory1": None, "accessory2": None},
      "active_buffs": [], "active_debuffs": [], "elemental_dmg": {}, "elemental_res": {},
      "inventory": [], "allies": [], "skills": [], "skill_mastery": {}, "skill_cooldowns": {}}
_p["attributes"]["Strength"] = 250
_b = enemy_stats("white_knight", _p)
_b["max_hp"] = 4000
_b["hp"] = 4000
_shared = [_b]
# Deterministic: no dodge/crit rolls during this block (random.random -> 1.0).
_orig_random = _rnd.random
_rnd.random = lambda: 1.0
set_io(_CapIO(4))
try:
    combat_white_knight(_p, 40, _shared)
except KeyboardInterrupt:
    pass  # expected: scripted bail-out after a few turns
finally:
    reset_io()
    _rnd.random = _orig_random
check(bool(_shared) and isinstance(_shared[0], _PhaseLockedKnight),
      "boss wrap lands in the caller's shared list (not a copy)")
check(bool(_shared) and _shared[0]["hp"] < 4000,
      "fight damage lands on the shared list (GUI HP bar moves)")

print("== 10. Ally skill vs skill dodge: (dmg, did_crit) tuple contract ==")
import combat.ally_skills as _ask

_skill = None
for _key, _ids in _ask.INNATE_SKILLS_MAP.items():
    for _sid in _ids:
        _sdef = _ask.get_innate_skill_def(_sid)
        if _sdef and _sdef.get("target", "enemy") == "enemy" and _sdef.get("base_power"):
            _skill = (_sid, _sdef)
            break
    if _skill:
        break
check(_skill is not None, "found a damaging ally skill for the contract check")
if _skill:
    _sid, _sdef = _skill
    _ally = {"name": "Luna", "is_ally": True, "race": "Human", "level": 50,
             "current_hp": 3000, "max_hp": 3000,
             "attributes": {a: 40 for a in _ATTRS},
             "equipped": {"weapon": None, "armor": None, "accessory1": None, "accessory2": None},
             "active_buffs": [], "active_debuffs": [], "elemental_dmg": {}, "elemental_res": {},
             "skill_cooldowns": {}, "skill_mastery": {}, "innate_skills": [_sid],
             "learned_skills": [], "defending_this_turn": False}
    _tgt = {"name": "White Knight", "key": "white_knight", "hp": 500, "max_hp": 500,
            "con_mod": 0, "active_debuffs": [], "active_buffs": [],
            "elemental_res": {}, "elemental_dmg": {}, "skill_dodge_chance": 1.0}
    set_io(_CapIO(0))
    _crashed = None
    try:
        _ask.execute_ally_skill(_ally, _p, _sid, _sdef, [_tgt], [_ally])
    except Exception as _exc:  # noqa: BLE001 - diagnostic wants any failure
        _crashed = repr(_exc)
    finally:
        reset_io()
    check(_crashed is None, f"ally skill dodge path returns a tuple, no crash ({_sid})")
    check(_tgt["hp"] == 500, "dodged ally skill leaves the target unharmed")

if failures:
    print(f"\nFAILED: {len(failures)} check(s)")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)
print("\nALL WHITE KNIGHT DIAGNOSTICS PASSED")
