"""Diagnostic: post-audit rarity cadence, shop floor, biome source, roll-site plumbing.

Verifies the audit §6 expected legendary cadence after P1 (soft ceiling) and
P2 (shop legendary floor), plus P4 (`dungeon_biome`) and P5 (leak removal).

Run: .venv\\Scripts\\python.exe tests/_diag_rarity_rates.py
"""
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import dungeon
from facilities.shop import _gate_legendary, SHOP_LEGENDARY_MIN_GRADE
from resources.item_generation import dungeon_biome
from facilities import travel_events

failures = []


def check(label, got, expected):
    ok = got == expected
    print(f"  {'OK  ' if ok else 'FAIL'} {label}: got {got}, expected {expected}")
    if not ok:
        failures.append(label)


def near(label, got, expected, tolerance=0.20):
    ok = abs(got - expected) <= expected * tolerance
    print(f"  {'OK  ' if ok else 'FAIL'} {label}: got {got:.4f}, expected {expected:.4f} +/-{int(tolerance * 100)}%")
    if not ok:
        failures.append(label)


print("=== Dungeon biome source (P4) ===")
check("pandemonium flag wins", dungeon_biome({"pandemonium_mode": True, "dungeon_region": "volcanic"}), "pandemonium")
check("run region wins over city", dungeon_biome({"dungeon_region": "tundra"}), "tundra")
check("falls back to city biome", dungeon_biome({}), "temperate")  # solmere

print("=== Shop legendary floor (D-O) ===")
check("legendary demoted to epic", _gate_legendary("greatsword", "legendary"), "epic")
check("epic stays", _gate_legendary("greatsword", "epic"), "epic")
check("common stays", _gate_legendary("greatsword", "common"), "common")

print("=== Uniform pool helper removed (P5) ===")
check("_random_item_id deleted", hasattr(travel_events, "_random_item_id"), False)

print("=== Legendary cadence (no grade softening on base forms) ===")
# Expected per-kill legendary rates: gate x (1 - flower) x equipment x weight.
CASES = [
    # (label, level, pandemonium, expected)
    ("normal Lv 6-10", 8, False, 0.5 * 0.88 * 0.60 * 0.01),
    ("normal Lv 11-20", 15, False, 0.5 * 0.88 * 0.60 * 0.03),
    ("normal Lv 21-25", 23, False, 0.5 * 0.88 * 0.60 * 0.06),
    ("normal Lv 26-30", 28, False, 0.5 * 0.88 * 0.60 * 0.06),
    ("pande Lv <=5", 5, True, 0.7 * 0.88 * 0.60 * 0.06),
    ("pande Lv 11-20", 15, True, 0.7 * 0.88 * 0.60 * 0.10),
    ("pande Lv 26+", 28, True, 0.7 * 0.88 * 0.60 * 0.10),
]
random.seed(1234)
for label, level, pande, expected in CASES:
    samples = 120000
    legendaries = sum(
        1 for _ in range(samples)
        if (d := dungeon.roll_drop(level, pandemonium=pande, biome=None)) and d[1] == "legendary"
    )
    near(label, legendaries / samples, expected)

print("=== Base forms pass rarity through (no grade softening) ===")
from resources.items import soften_rarity
check("soften is identity for base forms", soften_rarity("greatsword", "legendary"), "legendary")
check("soften is identity for epic base forms", soften_rarity("greatsword", "epic"), "epic")

print()
if failures:
    print("FAILED:", ", ".join(failures))
    sys.exit(1)
print("rarity rates OK")
