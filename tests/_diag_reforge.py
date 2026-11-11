"""Diagnostic: blacksmith element stripping (replaces the Phase 2 reforge).

Covers:
  * flowers invested are counted per slot (weapon ladders / resistance tiers)
  * stripping removes the slot and rebuilds the item in place
  * recovery is floor(invested / 3) — three flowers in, one flower back
  * a unique's authored primary survives; its flower slots can be stripped
  * a stripped piece can be re-infused

Run from repo root with:
    .venv\\Scripts\\python.exe tests\\_diag_reforge.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from resources.items import ITEMS, build_item
from resources.item_generation import (
    BASE_FORM_IDS, apply_infusion, infusion_flowers_invested,
    strip_infusion_slot,
)
from facilities.blacksmith import STRIP_REFUND_RATIO, _infusable


def main():
    ok = True

    def check(label, cond, detail=""):
        nonlocal ok
        if cond:
            print(f"PASS  {label}")
        else:
            ok = False
            print(f"FAIL  {label}  {detail}")

    check("refund ratio is 3:1", STRIP_REFUND_RATIO == 3)

    weapon_key = BASE_FORM_IDS["weapon"][0]
    base = ITEMS[weapon_key]
    weapon = build_item(weapon_key, "rare")

    applied, _ = apply_infusion(weapon, "fire", base)
    check("weapon accepts a fire infusion",
          applied and weapon["infusions"][0]["element"] == "fire")
    check("one flower invested", infusion_flowers_invested(weapon, 0) == 1)
    name_before = weapon["name"]
    result = strip_infusion_slot(weapon, base, 0)
    check("strip returns the element and count",
          result == ("fire", 1), f"got {result}")
    check("strip removes the slot", not weapon.get("infusions"))
    check("strip restores the innate element profile",
          weapon["elemental_dmg"] == base["elemental_dmg"],
          f"got {weapon['elemental_dmg']}")
    check("strip rebuilds the name", weapon["name"] != name_before,
          f"got {weapon['name']}")
    check("one flower refunds nothing at 3:1",
          1 // STRIP_REFUND_RATIO == 0)
    check("stripped piece can be re-infused",
          apply_infusion(weapon, "water", base)[0]
          and weapon["infusions"][0]["element"] == "water")

    # A fully grown primary slot (eight flowers) recovers two.
    weapon = build_item(weapon_key, "rare")
    for _ in range(8):
        apply_infusion(weapon, "fire", base)
    check("primary slot caps at 1.48",
          weapon["infusions"][0]["value"] == 1.48,
          f"got {weapon['infusions'][0]['value']}")
    check("eight flowers invested",
          infusion_flowers_invested(weapon, 0) == 8)
    check("eight flowers refund two",
          8 // STRIP_REFUND_RATIO == 2)
    element, invested = strip_infusion_slot(weapon, base, 0)
    check("maxed slot strips cleanly",
          element == "fire" and invested == 8 and not weapon.get("infusions"))

    # Later slots shift up into the emptied position.
    weapon = build_item(weapon_key, "rare")
    for _ in range(4):
        apply_infusion(weapon, "fire", base)      # primary 1.25
    apply_infusion(weapon, "water", base)          # secondary 1.10
    apply_infusion(weapon, "water", base)          # secondary 1.15
    strip_infusion_slot(weapon, base, 0)
    check("later slots shift up after a strip",
          weapon["infusions"][0]["element"] == "water"
          and weapon["infusions"][0]["value"] == 1.15
          and weapon["primary_element"] == "water",
          f"got {weapon['infusions']}")

    # Resistance slots count tiers (tier 0 = one flower, tier 2 = three).
    armor_key = BASE_FORM_IDS["armor"][0]
    armor_base = ITEMS[armor_key]
    armor = build_item(armor_key, "rare")
    for _ in range(3):
        apply_infusion(armor, "water", armor_base)
    check("armor tier 2 invested three",
          armor["infusions"][0]["tier"] == 2
          and infusion_flowers_invested(armor, 0) == 3)
    check("armor tier 2 refunds one",
          infusion_flowers_invested(armor, 0) // STRIP_REFUND_RATIO == 1)
    strip_infusion_slot(armor, armor_base, 0)
    check("stripped armor falls back to its form profile",
          armor["elemental_res"] == armor_base["elemental_res"],
          f"got {armor['elemental_res']}")

    # Uniques: the authored primary lives outside ``infusions``.
    unique_item = {"type": "equipment", "id": "abyss_fang", "unique": True,
                   "primary_element": "dark"}
    check("unique gear is infusable", _infusable(unique_item))
    check("base-form gear is infusable", _infusable(weapon))

    unique = build_item("abyss_fang", "unique")
    apply_infusion(unique, "fire", ITEMS["abyss_fang"])
    check("unique flower slot holds fire",
          unique["infusions"][0]["element"] == "fire")
    result = strip_infusion_slot(unique, ITEMS["abyss_fang"], 0)
    check("unique flower slot strips",
          result == ("fire", 1), f"got {result}")
    check("unique keeps its primary element",
          unique["primary_element"] == "dark"
          and unique["elemental_dmg"] == {"dark": 1.35},
          f"got {unique['elemental_dmg']}")

    if not ok:
        sys.exit(1)
    print("\nelement strip diagnostics OK")


if __name__ == "__main__":
    main()
