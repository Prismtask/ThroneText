"""Diagnostic: compositional weapon grid (Form × Element × Grade).

Run: .venv\\Scripts\\python.exe tests/_diag_weapon_grid.py
"""
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from resources.items import ITEMS, build_item, ITEM_RARITY
from resources.item_generation import (
    WEAPON_FORMS, ELEMENTS, ELEMENT_PREFIXES, BASE_FORM_IDS,
    grade_for_level, pick_weapon_id, pick_equipment_id, apply_infusion,
)

failures = []


def check(label, got, expected):
    ok = got == expected
    print(f"  {'OK  ' if ok else 'FAIL'} {label}: got {got}, expected {expected}")
    if not ok:
        failures.append(label)


print("=== Grid installation ===")
composed = [i for i, d in ITEMS.items() if d.get("composed")]
check("composed weapons generated (>600)", len(composed) > 600, True)
check("form count", len(WEAPON_FORMS), 29)

ember_gs = ITEMS["ember_greatsword"]
check("ember_greatsword name", ember_gs["name"], "Ember Greatsword")
check("ember_greatsword grade", ember_gs["grade"], 1)
check("ember_greatsword primary", ember_gs["primary_element"], "fire")
check("ember_greatsword STR", ember_gs["base_mods"]["Strength"], 4)
check("ember_greatsword fire", ember_gs["elemental_dmg"]["fire"], 1.10)

blaze_gs = ITEMS["blaze_greatsword"]
check("blaze_greatsword STR", blaze_gs["base_mods"]["Strength"], 6)
check("blaze_greatsword fire", blaze_gs["elemental_dmg"]["fire"], 1.30)

check("curated inferno_greatsword keeps grade 3", ITEMS["inferno_greatsword"]["grade"], 3)

titan_sword = ITEMS["titan_sword"]
check("titan_sword STR (sword g3)", titan_sword["base_mods"]["Strength"], 6)
check("titan_sword physical", titan_sword["elemental_dmg"]["physical"], 1.50)

print("=== Base forms + rarity compression (flower rework) ===")
check("grade_for_level deprecated", (grade_for_level(5), grade_for_level(30)), (1, 1))
check("base weapon forms", len(BASE_FORM_IDS["weapon"]), 29)
check("uninfused greatsword element", ITEMS["greatsword"]["elemental_dmg"], {"physical": 1.10})
check("rarity stat mult legendary", ITEM_RARITY["legendary"]["stat_mult"], 1.40)
legend = build_item("greatsword", "legendary")
check("legendary STR compressed", legend["mods"], {"Strength": 5})
check("rarity never scales element", legend["elemental_dmg"], {"physical": 1.10})
check("uninfused trait I", legend.get("trait_tier"), 1)
check("legacy grid ids remain dormant", ("inferno_greatsword" in ITEMS, "iron_sword" in ITEMS), (True, True))

print("=== Pickers return base forms ===")
base_ids = set(BASE_FORM_IDS["weapon"])
for label, picks in (
    ("pick_weapon_id", [pick_weapon_id(1) for _ in range(200)]),
    ("pick_equipment_id", [i for i in (pick_equipment_id(15) for _ in range(200))
                          if ITEMS[i].get("slot") == "weapon"]),
):
    bad = [i for i in picks if i not in base_ids]
    check(f"{label} returns base forms", bad, [])
    check(f"{label} ids exist", all(i in ITEMS for i in picks), True)

print("=== Element comes from infusion (not enhance) ===")
plain = build_item("greatsword", "legendary", enhance=0)
plus10 = build_item("greatsword", "legendary", enhance=10)
check("legendary +10 elemental unchanged", plus10["elemental_dmg"], {"physical": 1.10})
check("legendary +0 elemental", plain["elemental_dmg"], {"physical": 1.10})
infused = build_item("greatsword", "legendary")
apply_infusion(infused, "fire", ITEMS["greatsword"])
check("infusion sets element", infused["elemental_dmg"], {"fire": 1.10})
check("infusion keeps stats", infused["mods"], {"Strength": 5})

print("=== Every element/grade has a greatsword ===")
missing = []
for element in ELEMENTS:
    for grade in (1, 2, 3):
        prefix = ELEMENT_PREFIXES[element][grade - 1]
        item_id = f"{prefix.lower()}_greatsword"
        if item_id not in ITEMS:
            missing.append(item_id)
check("greatsword grid complete", missing, [])

print()
if failures:
    print("FAILED:", ", ".join(failures))
    sys.exit(1)
print("compositional weapon grid OK")
