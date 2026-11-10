# Temp end-to-end sim (2026-10-15): enemy_attack vs a low-HP Jade wearer with
# 0 pins. Before the fix the blow was silently repelled forever; now it lands.
import sys
sys.path.insert(0, "c:/Code/Pandemonium")
import random

import combat.enemy_ai as ea

captured = []
ea.c_print = lambda *a, **k: captured.append(" ".join(str(x) for x in a))
ea.random.random = lambda: 0.99   # no dodges, no crits
ea.random.randint = lambda a, b: b  # max-ish variance, deterministic

ATTRS = ("Strength", "Constitution", "Dexterity", "Wisdom", "Learning", "Charisma")
player = {
    "name": "prism",
    "class": "Warrior",
    "race": "Human",
    "level": 50,
    "current_hp": 6,          # under the 20% line (max will be 45)
    "level_hp_bonus": 0,
    "attributes": {a: 10 for a in ATTRS},
    "equipped": {"weapon": None, "armor": {"id": "tarnished_jade"}, "accessory1": None, "accessory2": None},
    "active_buffs": [], "active_debuffs": [],
    "elemental_dmg": {}, "elemental_res": {},
    "inventory": [], "allies": [],
    "tarnished_jade_pins": 0,
    "tarnished_jade_weakened": False,
}
enemy = {
    "name": "The Hollow You", "key": "_hallucination",
    "hp": 500, "max_hp": 500, "str_mod": 8, "dex_mod": 5, "con_mod": 0,
    "active_buffs": [], "active_debuffs": [],
    "elemental_dmg": {}, "elemental_res": {},
}

outcome = ea.enemy_attack(enemy, player, p_con=20, defending=False,
                          all_enemies=[enemy], actual_player=player)
print("outcome:", outcome)
print("player hp:", player["current_hp"])
for line in captured:
    print("   |", line)
assert outcome == "hit", outcome
assert not any("REPULSED" in l for l in captured), "0-pin Jade must not repel"
assert player["current_hp"] < 6, "the blow must land now"
print("OK — enemy_attack lands the blow on a spent (0-pin) Jade")
