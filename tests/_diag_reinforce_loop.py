"""
tests/_diag_reinforce_loop.py — Real-loop check of the ally reinforcement rule.

Not collected by pytest (underscore prefix). Run directly:
    c:/Code/Pandemonium/.venv/Scripts/python.exe tests/_diag_reinforce_loop.py

Runs the REAL combat engine (combat/combat_engine.py) with a scripted I/O
bridge: front ally A is poisoned and dies at the end of round 1; round 2 must
open with the earliest bench ally (D) replacing them ("steps in for the
fallen A!"), before initiative.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from combat.combat_io import BaseCombatIO, set_io
from combat.ally import (get_all_active_allies_including_defeated,
                         get_all_reserve_allies_including_defeated)
from resources.races_classes import ATTRIBUTES
import combat.combat_engine as ce


def make_ally(name, hp=30, max_hp=30):
    return {
        "name": name, "key": f"test_{name.lower()}", "is_ally": True,
        "race": "Beast",
        "current_hp": hp, "max_hp": max_hp, "defeated": False,
        "level": 50,
        "attributes": {a: 5 for a in ATTRIBUTES},
        "active_buffs": [], "active_debuffs": [],
        "skill_cooldowns": {}, "equipped": {},
    }


class ScriptIO(BaseCombatIO):
    def __init__(self):
        self.lines = []

    def print(self, *args, **kwargs):
        self.lines.append(" ".join(str(a) for a in args))

    def clear(self):
        pass

    def input(self, prompt=""):
        if "Press Enter" in prompt:
            return ""
        if "Choose action" in prompt:       # ally menu
            return "a"
        if "Choose" in prompt:              # player menu ("Choose: ")
            return "a"
        if "Select target" in prompt:
            return "1"
        if "Use which item" in prompt:
            return "0"
        return ""


class _RoundCap(Exception):
    pass


def main():
    player = {
        "name": "Hero", "current_hp": 500, "max_hp": 500, "gold": 0,
        "level": 50, "exp": 0,
        "attributes": {a: 20 for a in ATTRIBUTES},
        "allies": [make_ally(n) for n in ("A", "B", "C", "D")],
        "quests": {"resonance_tier": 5},    # 3 front allies / 4 bench
        "active_buffs": [], "active_debuffs": [],
        "skill_cooldowns": {}, "inventory": [],
        "equipped": {}, "save_slot": 99,
    }
    # Lethal poison on A — the round-end tick kills them after round 1.
    a = player["allies"][0]
    a["active_debuffs"].append({"type": "poison", "damage": 9999,
                                "remaining": 5})

    enemy = {
        "key": "test_target", "name": "Punching Bag",
        "hp": 100000, "max_hp": 100000,
        "str_mod": 0, "con_mod": 0, "dex_mod": 0,
        "elemental_res": {}, "elemental_dmg": {},
        "status_res": 0.0, "active_buffs": [], "active_debuffs": [],
    }

    io = ScriptIO()
    set_io(io)

    rounds = {"n": 0}
    orig_roll = ce.roll_initiative

    def capped_roll(p, enemies):
        rounds["n"] += 1
        if rounds["n"] > 3:
            raise _RoundCap()
        return orig_roll(p, enemies)

    ce.roll_initiative = capped_roll
    try:
        ce.combat(player, [], enemies=[enemy])
    except _RoundCap:
        pass
    finally:
        ce.roll_initiative = orig_roll

    text = "\n".join(io.lines)
    assert rounds["n"] >= 3, f"fight did not reach round 3 (rounds={rounds['n']})"
    assert a["current_hp"] <= 0, f"A survived the poison: {a['current_hp']} HP"
    assert "steps in for the fallen A!" in text, \
        "reinforcement message missing from combat output"
    front = [al["name"] for al in get_all_active_allies_including_defeated(player)]
    bench = [al["name"] for al in get_all_reserve_allies_including_defeated(player)]
    assert "D" in front, f"D not in the front row: {front}"
    assert "A" in bench, f"A not on the bench: {bench}"
    print("[OK] reinforcement: A fell to poison at end of r1; D stepped in at "
          "r2 before initiative (message + lineup verified)")


if __name__ == "__main__":
    main()
