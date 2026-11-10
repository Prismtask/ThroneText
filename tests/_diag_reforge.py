"""Diagnostic: Phase 2 reforge — cost, pure roll, apply, slot preservation,
unique flower slots (primary locked).

Covers docs/gold_economy_pacing_design.md D2:
  * fee = 40 x item_value (power-based, not market-indexed)
  * re-roll is pure until applied (keep-or-replace is possible)
  * weapons keep their infusion value; armor/accessories keep their tier
  * uniques can reforge their two flower slots but never their primary

Run from repo root with:
    .venv\\Scripts\\python.exe tests\\_diag_reforge.py
"""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from resources.items import ITEMS, build_item, item_value, reforge_cost
from resources.item_generation import (
    BASE_FORM_IDS, apply_infusion, roll_reforge_element, apply_reforge_element,
)
from facilities.blacksmith import _infusable


def main():
    ok = True

    def check(label, cond, detail=""):
        nonlocal ok
        if cond:
            print(f"PASS  {label}")
        else:
            ok = False
            print(f"FAIL  {label}  {detail}")

    weapon_key = BASE_FORM_IDS["weapon"][0]
    base = ITEMS[weapon_key]
    weapon = build_item(weapon_key, "rare")
    applied, _ = apply_infusion(weapon, "fire", base)
    check("weapon starts with fire",
          applied and weapon["infusions"][0]["element"] == "fire")
    value_before = weapon["infusions"][0]["value"]
    name_before = weapon["name"]

    check("reforge cost = 40 x item_value",
          reforge_cost(weapon) == int(round(40 * item_value(weapon))),
          f"got {reforge_cost(weapon)} vs {40 * item_value(weapon)}")

    before = [dict(i) for i in weapon["infusions"]]
    new_element = roll_reforge_element(weapon, 0, rng=random.Random(7))
    check("roll returns a different element",
          bool(new_element) and new_element != "fire", f"got {new_element}")
    check("roll does not mutate the item",
          weapon["infusions"] == before, f"got {weapon['infusions']}")

    applied = apply_reforge_element(weapon, base, 0, new_element)
    check("apply changes the element",
          applied and weapon["infusions"][0]["element"] == new_element)
    check("apply preserves the weapon value",
          weapon["infusions"][0]["value"] == value_before)
    check("apply rebuilds the item name",
          weapon["name"] != name_before, f"got {weapon['name']}")

    armor_key = BASE_FORM_IDS["armor"][0]
    armor_base = ITEMS[armor_key]
    armor = build_item(armor_key, "rare")
    apply_infusion(armor, "water", armor_base)
    tier_before = armor["infusions"][0]["tier"]
    new_armor_element = roll_reforge_element(armor, 0, rng=random.Random(11))
    apply_reforge_element(armor, armor_base, 0, new_armor_element)
    check("armor keeps its infusion tier",
          armor["infusions"][0]["tier"] == tier_before)
    check("armor element changed",
          armor["infusions"][0]["element"] == new_armor_element)

    unique_item = {"type": "equipment", "id": "abyss_fang", "unique": True,
                   "primary_element": "dark"}
    check("unique gear is infusable", _infusable(unique_item))
    check("base-form gear is infusable", _infusable(weapon))

    unique = build_item("abyss_fang", "unique")
    apply_infusion(unique, "fire", ITEMS["abyss_fang"])
    unique_value_before = unique["infusions"][0]["value"]
    new_unique_element = roll_reforge_element(unique, 0, rng=random.Random(7))
    check("unique reforge skips its locked primary",
          bool(new_unique_element) and new_unique_element not in ("dark", "fire"),
          f"got {new_unique_element}")
    apply_reforge_element(unique, ITEMS["abyss_fang"], 0, new_unique_element)
    check("unique flower slot keeps its value",
          unique["infusions"][0]["value"] == unique_value_before)
    check("unique primary survives reforge",
          unique["primary_element"] == "dark"
          and unique["elemental_dmg"].get("dark") == 1.35)

    print("\nReforge cost examples:")
    for rarity in ("common", "rare", "epic", "legendary"):
        item = build_item(weapon_key, rarity)
        apply_infusion(item, "fire", base)
        print(f"  {rarity.title():<10} value {item_value(item):>4}  cost {reforge_cost(item):>5}g")

    if not ok:
        sys.exit(1)
    print("\nreforge diagnostics OK")


if __name__ == "__main__":
    main()
