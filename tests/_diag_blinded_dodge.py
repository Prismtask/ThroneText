# Temp diagnostic (2026-10-08): capture output when a blinded player attacks.
import sys
sys.path.insert(0, "c:/Code/Pandemonium")
import random

import combat.player_actions as pact
import combat.stats as pstats

captured = []
pact.c_print = lambda *a, **k: captured.append(" ".join(str(x) for x in a))
pact.c_input = lambda *a, **k: "a"

ATTRS = ("Strength", "Constitution", "Dexterity", "Wisdom", "Learning", "Charisma")
player = {
    "name": "Hero", "class": "Warrior", "level": 15, "current_hp": 45,
    "passive_unlocked": True,
    "attributes": {a: 10 for a in ATTRS},
    "level_hp_bonus": 0,
    "equipped": {"weapon": None, "armor": None, "accessory1": None, "accessory2": None},
    "active_buffs": [], "active_debuffs": [{"type": "blind", "remaining": 2}],
    "blinded": True,
    "elemental_dmg": {}, "elemental_res": {},
    "inventory": [], "allies": [],
    "skills": [], "skill_mastery": {}, "skill_cooldowns": {},
}
enemy = {
    "name": "Dummy", "hp": 10**6, "max_hp": 10**6, "con_mod": 0, "dex_mod": 5,
    "active_debuffs": [], "active_buffs": [],
    "elemental_res": {}, "elemental_dmg": {},
}

# Force the dodge roll to succeed and suppress crits
pstats.roll_critical_hit = lambda *a, **k: (False, 0.0, 0.0)
pact.random.random = lambda: 0.0  # dodge always triggers

res = pact.handle_player_turn(player, [enemy], 10, 10, 10, 10, 10, 10)
print("result:", res)
print("captured output:")
for line in captured:
    print(repr(line))
dodge_up = pstats.get_dodge_chance(enemy, player)
print("dodge chance vs blinded attacker:", dodge_up)
