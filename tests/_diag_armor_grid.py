"""Diagnostic: compositional armor & accessory grid (Form × Element × Grade).

Run: .venv\\Scripts\\python.exe tests/_diag_armor_grid.py
"""
import os
import random
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from resources.items import ITEMS, build_item, cap_rarity_for_item, soften_rarity, intrinsic_value, ITEM_RARITY
from resources.item_generation import (
    ARMOR_FORMS, ACCESSORY_FORMS, ELEMENTS, ELEMENT_PREFIXES, BASE_FORM_IDS,
    ARMOR_ELEMENT_TRIANGLE, ACCESSORY_AFFINITY, apply_infusion,
    _ARMOR_POOLS, _ACCESSORY_POOLS,
    pick_family_id, pick_equipment_id,
)

failures = []


def check(label, got, expected):
    ok = got == expected
    print(f"  {'OK  ' if ok else 'FAIL'} {label}: got {got}, expected {expected}")
    if not ok:
        failures.append(label)


print("=== Grid installation ===")
armor_composed = [i for i, d in ITEMS.items() if d.get("composed") and d.get("slot") == "armor"]
acc_composed = [i for i, d in ITEMS.items() if d.get("composed") and d.get("slot") == "accessory"]
check("composed armor > 400", len(armor_composed) > 400, True)
check("composed accessories > 400", len(acc_composed) > 400, True)
check("armor form count", len(ARMOR_FORMS), 16)
check("accessory form count", len(ACCESSORY_FORMS), 17)

names = Counter(d["name"] for d in ITEMS.values() if d.get("type") == "equipment")
check("duplicate equipment names", {n: c for n, c in names.items() if c > 1}, {})

print("=== Form templates (every coordinate) ===")
bad_stats, bad_entries, bad_affinity = [], [], []
for form in ARMOR_FORMS:
    for element in ELEMENTS:
        for grade in (1, 2, 3):
            item_id = f"{ELEMENT_PREFIXES[element][grade - 1].lower()}_{form['key']}"
            data = ITEMS.get(item_id)
            if data is None or not data.get("composed"):
                continue  # curated override
            template = dict(form["template"])
            primary = next(iter(template))
            template[primary] += grade - 1
            if data["base_mods"] != template:
                bad_stats.append((item_id, data["base_mods"], template))
            if len(data["elemental_res"]) != form["entries"]:
                bad_entries.append((item_id, len(data["elemental_res"]), form["entries"]))
            res = data["elemental_res"]
            draw_el = ARMOR_ELEMENT_TRIANGLE[element][2]
            if bool(form.get("drawback")) and draw_el not in res:
                bad_entries.append((item_id, "missing drawback", draw_el))
check("armor stat templates match forms", bad_stats, [])
check("armor res entry counts match forms", bad_entries, [])

for form in ACCESSORY_FORMS:
    for element in ELEMENTS:
        for grade in (1, 2, 3):
            item_id = f"{ELEMENT_PREFIXES[element][grade - 1].lower()}_{form['key']}"
            data = ITEMS.get(item_id)
            if data is None or not data.get("composed"):
                continue
            primary, secondary = ACCESSORY_AFFINITY[element]
            expected_stats = 1 if form["stats"] == 1 else 2
            if len(data["base_mods"]) != expected_stats or primary not in data["base_mods"]:
                bad_affinity.append((item_id, data["base_mods"], primary, secondary))
            if sum(data["base_mods"].values()) != form["budget"] + (grade - 1):
                bad_affinity.append((item_id, "budget", data["base_mods"], form["budget"]))
            expected_res = 1 if grade == 1 else 2
            if len(data["elemental_res"]) != expected_res:
                bad_entries.append((item_id, len(data["elemental_res"]), expected_res))
check("accessory affinities/budgets", bad_affinity, [])
check("accessory res entries gated by grade", bad_entries, [])

print("=== Samples ===")
check("ember_plate_armor CON", ITEMS["ember_plate_armor"]["base_mods"],
      {"Constitution": 5, "Dexterity": -1})
check("blaze_plate_armor CON", ITEMS["blaze_plate_armor"]["base_mods"],
      {"Constitution": 6, "Dexterity": -1})
check("inferno_plate_armor CON", ITEMS["inferno_plate_armor"]["base_mods"],
      {"Constitution": 7, "Dexterity": -1})
check("ember_plate_armor res", ITEMS["ember_plate_armor"]["elemental_res"],
      {"fire": 1.15, "earth": 1.05, "water": 0.85, "physical": 1.05})
check("inferno_plate_armor res", ITEMS["inferno_plate_armor"]["elemental_res"],
      {"fire": 1.35, "earth": 1.15, "water": 0.85, "physical": 1.05})
check("ember_crown stats", ITEMS["ember_crown"]["base_mods"],
      {"Strength": 3, "Constitution": 3})
check("inferno_crown stats", ITEMS["inferno_crown"]["base_mods"],
      {"Strength": 5, "Constitution": 3})
check("frost_band stats (g1 split)", ITEMS["frost_band"]["base_mods"],
      {"Constitution": 2, "Dexterity": 2})
check("ember_crown res (g1 primary only)", ITEMS["ember_crown"]["elemental_res"], {"fire": 1.05})

print("=== Grade premiums by slot ===")
check("weapon g3 premium", ITEMS["inferno_greatsword"]["grade_premium"], 5)
check("armor g3 premium", ITEMS["inferno_plate_armor"]["grade_premium"], 3)
check("accessory g3 premium", ITEMS["inferno_crown"]["grade_premium"], 2)

print("=== Valuation ===")
check("blaze_plate_armor intrinsic", intrinsic_value("blaze_plate_armor"), 9)
check("inferno_crown intrinsic", intrinsic_value("inferno_crown"), 11)

print("=== Soft rarity ceiling (D-N) ===")
check("armor g1 hard cap removed", cap_rarity_for_item("ember_padded_armor", "legendary"), "legendary")
check("armor g3 never softens", soften_rarity("inferno_plate_armor", "legendary"), "legendary")
random.seed(9)
armor_g1 = [soften_rarity("ember_padded_armor", "legendary") for _ in range(10000)]
check("armor g1 legendary survives ~15%", 0.12 <= armor_g1.count("legendary") / 10000 <= 0.18, True)
check("accessory g1 epic survives ~60%",
      0.55 <= ([soften_rarity("frost_band", "epic") for _ in range(10000)].count("epic") / 10000) <= 0.65, True)

print("=== Pickers return base forms ===")
for slot in ("armor", "accessory"):
    picks = [pick_family_id(slot) for _ in range(200)]
    base_ids = set(BASE_FORM_IDS[slot])
    check(f"pick_family_id({slot}) returns base forms", [i for i in picks if i not in base_ids], [])
for level in (5, 15, 30):
    picks = [pick_equipment_id(level) for _ in range(300)]
    gear = [i for i in picks if ITEMS[i].get("slot") in ("armor", "accessory")]
    base_all = set(BASE_FORM_IDS["armor"]) | set(BASE_FORM_IDS["accessory"])
    check(f"pick_equipment_id({level}) returns base forms", [i for i in gear if i not in base_all], [])

print("=== Build path (base forms, compressed rarity) ===")
legend_crown = build_item("crown", "legendary")
check("legendary crown CHA", legend_crown["mods"], {"Charisma": 4, "Wisdom": 4})
check("default crown carries no protection", legend_crown["elemental_res"], {"physical": 1.0})
check("rarity never scales res", legend_crown["elemental_res"], {"physical": 1.0})
check("base forms carry form metadata", ITEMS["crown"].get("base_form"), True)
plate_infused = build_item("plate_armor", "common")
apply_infusion(plate_infused, "fire", ITEMS["plate_armor"])
check("armor infusion sets res triangle", plate_infused["elemental_res"],
      {"fire": 1.15, "earth": 1.05, "water": 0.85, "physical": 1.05})

print("=== Pools exclude specials ===")
special = [i for pools in (_ARMOR_POOLS, _ACCESSORY_POOLS)
           for g in pools.values() for ids in g.values() for i in ids
           if ITEMS[i].get("unique") or ITEMS[i].get("wonderland_only") or ITEMS[i].get("black_market_only")]
check("no specials in armor/accessory pools", special, [])

print()
if failures:
    print("FAILED:", ", ".join(failures))
    sys.exit(1)
print("compositional armor grid OK")
