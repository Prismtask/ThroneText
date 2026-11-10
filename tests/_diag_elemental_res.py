"""Diagnostic: elemental resistance rating convention.

Ratings are authored "higher = stronger": >1.0 = resistant, 1.0 = neutral,
<1.0 = weak. Damage-taken multiplier = clamp(2.0 - rating, 0.0, 2.0).

Run: .venv\\Scripts\\python.exe tests/_diag_elemental_res.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from combat.elemental import calculate_elemental_damage, resistance_multiplier
from combat.dummy import create_dummy_enemy


def dmg(res_rating, debuffs=None, buffs=None):
    attacker = {"name": "attacker", "elemental_dmg": {"fire": 1.3}}
    target = {
        "name": "target",
        "elemental_res": {"fire": res_rating},
        "active_debuffs": debuffs or [],
        "active_buffs": buffs or [],
    }
    return calculate_elemental_damage(100, attacker, target, "fire")


failures = []


def check(label, got, expected):
    ok = got == expected
    print(f"  {'OK  ' if ok else 'FAIL'} {label}: got {got}, expected {expected}")
    if not ok:
        failures.append(label)


print("=== Resistance multiplier (2 - rating, clamped) ===")
check("neutral 1.0", resistance_multiplier(1.0), 1.0)
check("resist 1.3", round(resistance_multiplier(1.3), 3), 0.7)
check("weak 0.7", round(resistance_multiplier(0.7), 3), 1.3)
check("clamp high rating 3.0", resistance_multiplier(3.0), 0.0)
check("clamp low rating -1.0", resistance_multiplier(-1.0), 2.0)

print("=== Damage (base 100, attacker fire x1.3) ===")
check("neutral", dmg(1.0), 130)
check("30% resist", dmg(1.3), 91)
check("30% weakness", dmg(0.7), 169)

print("=== Rating modifiers ===")
weakness = [{"type": "elemental_weakness", "value": 0.2, "remaining": 3}]
check("weakness debuff (rating 1.0 -> 0.8)", dmg(1.0, debuffs=weakness), 156)
adapt = [{"type": "elemental_adapt_res", "element": "fire", "value": 0.5, "remaining": 3}]
check("adapt-res buff (rating 1.0 -> 1.5)", dmg(1.0, buffs=adapt), 65)

print("=== Training dummy ===")
dummy = create_dummy_enemy()
check("dummy default rating", dummy["elemental_res"]["fire"], 1.0)
check(
    "dummy default damage",
    calculate_elemental_damage(100, {"elemental_dmg": {"fire": 1.3}}, dummy, "fire"),
    130,
)
dummy_res = create_dummy_enemy(
    {"elemental_res": {el: 1.8 for el in dummy["elemental_res"]}}
)
check(
    "dummy +80% resist damage",
    calculate_elemental_damage(100, {"elemental_dmg": {"fire": 1.3}}, dummy_res, "fire"),
    26,
)

print()
if failures:
    print("FAILED:", ", ".join(failures))
    sys.exit(1)
print("elemental resistance convention OK")
