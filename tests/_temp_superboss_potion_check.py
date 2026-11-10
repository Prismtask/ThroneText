# Temp verification (2026-10-27): potion sickness now ticks once per round in
# superboss fights (player + allies), matching the standard engine.
import sys
sys.path.insert(0, "c:/Code/Pandemonium")

import combat.superboss_common as sbc
import combat.ally as amod
import combat.combat_ui as cui
from combat.stats import enemy_stats

# ── Silence I/O / HUD ──
sbc.c_print = lambda *a, **k: ""
sbc.c_input = lambda *a, **k: "d"
sbc.print_combat_hud = lambda *a, **k: None
sbc.print_player_mini_hud = lambda *a, **k: None
sbc.print_superboss_header = lambda *a, **k: None
sbc.print_turn_order = lambda *a, **k: None
amod.c_print = lambda *a, **k: ""
amod.c_input = lambda *a, **k: "d"
cui.print_combat_hud = lambda *a, **k: None

ATTRS = ("Strength", "Constitution", "Dexterity", "Wisdom", "Learning", "Charisma")


def make_player():
    p = {"name": "hanafi", "class": "Warrior", "level": 15,
         "current_hp": 400, "passive_unlocked": True,
         "attributes": {a: 10 for a in ATTRS},
         "level_hp_bonus": 0,
         "equipped": {"weapon": None, "armor": None, "accessory1": None, "accessory2": None},
         "active_buffs": [], "active_debuffs": [],
         "elemental_dmg": {}, "elemental_res": {},
         "inventory": [], "allies": [],
         "skills": [], "skill_mastery": {}, "skill_cooldowns": {},
         "potion_sickness": 2}
    p["attributes"]["Strength"] = 0
    return p


def make_ally():
    return {"name": "Harpy Scout", "is_ally": True, "race": "Human", "level": 15,
            "current_hp": 300, "max_hp": 300,
            "attributes": {a: 10 for a in ATTRS},
            "equipped": {"weapon": None, "armor": None, "accessory1": None, "accessory2": None},
            "active_buffs": [], "active_debuffs": [],
            "elemental_dmg": {}, "elemental_res": {},
            "skills": [], "skill_mastery": {}, "skill_cooldowns": {},
            "potion_sickness": 2}


player = make_player()
ally = make_ally()
player["allies"] = [ally]
enemies = [enemy_stats("gnome_aether_engineer", player)]

rounds = {"n": 0}


def pre_hook(ctx, elist):
    rounds["n"] += 1
    if rounds["n"] > 1:
        return "victory"   # stop after one full round
    return None


result = sbc.superboss_combat_loop(
    player, enemies, floor=1, boss_name="Test Boss", context={},
    pre_player_hook=pre_hook,
)

checks = [
    ("fight ended cleanly", result == "victory", result),
    ("one full round ran", rounds["n"] == 2, rounds["n"]),
    ("player potion sickness ticked 2->1", player["potion_sickness"] == 1,
     player["potion_sickness"]),
    ("ally potion sickness ticked 2->1", ally["potion_sickness"] == 1,
     ally["potion_sickness"]),
]
failed = 0
for name, ok, detail in checks:
    print(("PASS" if ok else "FAIL") + f" — {name} ({detail})")
    failed += 0 if ok else 1
print(f"\n{len(checks) - failed}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
