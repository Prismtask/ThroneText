"""Diagnostic: base-form catalog, flower infusion model, trait ladders, v4 migration.

Run: .venv\\Scripts\\python.exe tests/_diag_infusion.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from resources.items import ITEMS, build_item, intrinsic_value
from resources.item_generation import (
    BASE_FORM_IDS, WEAPON_SLOT_CAPS, apply_infusion,
    pick_weapon_id, pick_family_id, pick_equipment_id,
)
from combat.elemental_traits import get_trait_for_weapon
from character import (
    _migrate_item_instance_v4, _refresh_base_form_name, _refresh_unique_instance,
)

failures = []


def check(label, got, expected):
    ok = got == expected
    print(f"  {'OK  ' if ok else 'FAIL'} {label}: got {got}, expected {expected}")
    if not ok:
        failures.append(label)


def near(label, got, expected, tol=1e-6):
    ok = abs(got - expected) <= tol
    print(f"  {'OK  ' if ok else 'FAIL'} {label}: got {got}, expected {expected}")
    if not ok:
        failures.append(label)


print("=== Base-form catalog ===")
check("weapon forms", len(BASE_FORM_IDS["weapon"]), 29)
check("armor forms", len(BASE_FORM_IDS["armor"]), 16)
check("accessory forms", len(BASE_FORM_IDS["accessory"]), 17)
check("all base ids in ITEMS", all(i in ITEMS for ids in BASE_FORM_IDS.values() for i in ids), True)
check("greatsword base", ITEMS["greatsword"]["base_form"], True)
check("greatsword STR", ITEMS["greatsword"]["base_mods"], {"Strength": 4})
check("greatsword element", ITEMS["greatsword"]["elemental_dmg"], {"physical": 1.10})
check("plate form entries", (ITEMS["plate_armor"]["form_entries"], ITEMS["plate_armor"]["form_drawback"]), (4, True))
check("crown budget", (ITEMS["crown"]["form_budget"], ITEMS["crown"]["form_stats"]), (6, 2))

print("=== Pickers return base forms ===")
base_ids = set(i for ids in BASE_FORM_IDS.values() for i in ids)
picks = [pick_weapon_id(1) for _ in range(100)] + [pick_family_id("armor") for _ in range(100)] + [pick_equipment_id(20) for _ in range(100)]
check("pickers only base forms", [p for p in picks if p not in base_ids], [])

print("=== Rarity compression (stats only) ===")
legend = build_item("greatsword", "legendary")
check("legendary STR", legend["mods"], {"Strength": 5})   # int(4 x 1.40)
check("legendary element unchanged", legend["elemental_dmg"], {"physical": 1.10})
check("uninfused trait I", legend.get("trait_tier"), 1)

print("=== Weapon infusion track (primary 1.10 -> 0.05 -> 1.48) ===")
sword = build_item("greatsword", "common")
check("infuse fire", apply_infusion(sword, "fire", ITEMS["greatsword"]), (True, ""))
check("fire 1.10", sword["elemental_dmg"], {"fire": 1.10})
check("new element dormant trait", sword.get("trait_tier"), None)
check("primary element", sword["primary_element"], "fire")
for step, value in ((2, 1.15), (3, 1.20)):
    apply_infusion(sword, "fire", ITEMS["greatsword"])
    near(f"fire step {step}", sword["infusions"][0]["value"], value)
check("still dormant at 1.20", sword.get("trait_tier"), None)
apply_infusion(sword, "fire", ITEMS["greatsword"])
check("trait I at 1.25", sword.get("trait_tier"), 1)
for _ in range(2):
    apply_infusion(sword, "fire", ITEMS["greatsword"])
check("trait II at 1.35", sword.get("trait_tier"), 2)
for _ in range(2):
    apply_infusion(sword, "fire", ITEMS["greatsword"])
near("primary cap", sword["infusions"][0]["value"], WEAPON_SLOT_CAPS[0])
check("trait III at 1.48", sword.get("trait_tier"), 3)
check("cap refuses", apply_infusion(sword, "fire", ITEMS["greatsword"]), (False, "slot at cap"))

print("=== Secondary / tertiary slots ===")
check("add secondary", apply_infusion(sword, "dark", ITEMS["greatsword"]), (True, ""))
check("secondary 1.10", sword["elemental_dmg"].get("dark"), 1.10)
for _ in range(2):
    apply_infusion(sword, "dark", ITEMS["greatsword"])
near("secondary cap", sword["infusions"][1]["value"], WEAPON_SLOT_CAPS[1])
check("secondary cap refuses", apply_infusion(sword, "dark", ITEMS["greatsword"]), (False, "slot at cap"))
check("add tertiary", apply_infusion(sword, "water", ITEMS["greatsword"]), (True, ""))
apply_infusion(sword, "water", ITEMS["greatsword"])
near("tertiary cap", sword["infusions"][2]["value"], WEAPON_SLOT_CAPS[2])
check("tertiary cap refuses", apply_infusion(sword, "water", ITEMS["greatsword"]), (False, "slot at cap"))
check("fourth element replaces tertiary", apply_infusion(sword, "thunder", ITEMS["greatsword"]), (True, ""))
check("tertiary replaced", sword["infusions"][2], {"element": "thunder", "value": 1.10})
check("primary kept", sword["infusions"][0]["element"], "fire")

print("=== Trait ladders resolve from infusion tier ===")
check("fire trait I burn tier", get_trait_for_weapon(build_item("greatsword", "common") | {"trait_tier": 1, "primary_element": "fire"}, "common")["on_hit_burn_tier"], 2)
check("fire trait II burn tier", get_trait_for_weapon(build_item("greatsword", "common") | {"trait_tier": 2, "primary_element": "fire"}, "common")["on_hit_burn_tier"], 4)
check("fire trait III burn tier", get_trait_for_weapon(build_item("greatsword", "common") | {"trait_tier": 3, "primary_element": "fire"}, "common")["on_hit_burn_tier"], 5)
check("physical innate sunder", get_trait_for_weapon(build_item("greatsword", "common"), "common")["on_hit_armor_pen"], 0.15)
check("physical trait II sunder", get_trait_for_weapon(build_item("greatsword", "common") | {"trait_tier": 2}, "common")["on_hit_armor_pen"], 0.22)
check("dormant trait", get_trait_for_weapon(build_item("greatsword", "common") | {"trait_tier": None, "primary_element": "fire"}, "common"), None)

print("=== Armor / accessory resistance slots ===")
# Same element keeps upgrading its own slot (plate: 4 entries incl. drawback).
plate = build_item("plate_armor", "common")
check("infuse armor fire", apply_infusion(plate, "fire", ITEMS["plate_armor"]), (True, ""))
check("armor fire tier I", plate["elemental_res"], {"fire": 1.15, "earth": 1.05, "water": 0.85, "physical": 1.05})
apply_infusion(plate, "fire", ITEMS["plate_armor"])
check("armor fire tier II", plate["elemental_res"], {"fire": 1.25, "earth": 1.10, "water": 0.85, "physical": 1.05})
apply_infusion(plate, "fire", ITEMS["plate_armor"])
check("armor fire tier III", plate["elemental_res"], {"fire": 1.35, "earth": 1.15, "water": 0.85, "physical": 1.05})
check("armor tier cap refuses", apply_infusion(plate, "fire", ITEMS["plate_armor"]), (False, "element at cap"))

# A new element fills slot 2 instead of replacing slot 1. Water overrides the
# fire tree's water drawback, so the armor's weakness is covered.
multi_plate = build_item("plate_armor", "common")
apply_infusion(multi_plate, "fire", ITEMS["plate_armor"])
check("slot 2 water", apply_infusion(multi_plate, "water", ITEMS["plate_armor"]), (True, ""))
check("two res elements merge (weakness covered)",
      multi_plate["elemental_res"],
      {"fire": 1.15, "water": 1.15, "earth": 1.05, "wind": 1.05, "physical": 1.05})
check("slot 2 keeps the first element as primary",
      multi_plate["primary_element"], "fire")

# The wearer's merged profile now resists both elements — the old water
# drawback is covered, which is the endgame defence fix.
from combat.elemental import compute_player_elemental
wearer_res, _ = compute_player_elemental(
    {"race": "Human", "class": "Warrior",
     "equipped": {"armor": multi_plate}})
check("multi-res armor keeps its primary resistance",
      round(wearer_res["fire"], 2) > 1.0, True)
check("multi-res armor covers its old drawback",
      round(wearer_res["water"], 2) > 1.0, True)

check("third res slot", apply_infusion(multi_plate, "thunder", ITEMS["plate_armor"]), (True, ""))
check("three res elements merge",
      multi_plate["elemental_res"],
      {"fire": 1.15, "water": 1.15, "thunder": 1.15,
       "earth": 1.05, "wind": 1.05, "physical": 1.05})
apply_infusion(multi_plate, "fire", ITEMS["plate_armor"])   # slot 1 -> tier II
check("same flower still upgrades its own slot",
      multi_plate["elemental_res"],
      {"fire": 1.25, "water": 1.15, "thunder": 1.15,
       "earth": 1.10, "wind": 1.05, "physical": 1.05})
check("fourth element replaces slot 3",
      apply_infusion(multi_plate, "dark", ITEMS["plate_armor"]), (True, ""))
check("slot 3 replaced, first two kept",
      multi_plate["elemental_res"],
      {"fire": 1.25, "water": 1.15, "dark": 1.15,
       "earth": 1.10, "wind": 1.05, "magical": 1.05})
check("armor stats unchanged by infusion",
      multi_plate["mods"], {"Constitution": 5, "Dexterity": -1})

# Accessories use the same three-slot rule, without a drawback.
ring = build_item("ring", "common")
check("ring form stats (DEX)", ring["mods"], {"Dexterity": 3})
check("ring starts uninfused (no resistance)", ring["elemental_res"], {"physical": 1.0})
check("infuse ring fire", apply_infusion(ring, "fire", ITEMS["ring"]), (True, ""))
check("ring fire res", ring["elemental_res"], {"fire": 1.05})
check("ring fire keeps form stats", ring["mods"], {"Dexterity": 3})
check("ring second res slot", apply_infusion(ring, "dark", ITEMS["ring"]), (True, ""))
check("ring res slots merge", ring["elemental_res"], {"fire": 1.05, "dark": 1.05})
check("ring dark keeps form stats", ring["mods"], {"Dexterity": 3})
apply_infusion(ring, "fire", ITEMS["ring"])                 # slot 1 -> tier II
check("ring slot 1 upgrade adds its secondary",
      ring["elemental_res"], {"fire": 1.10, "earth": 1.05, "dark": 1.05})
check("ring third res slot", apply_infusion(ring, "water", ITEMS["ring"]), (True, ""))
check("ring three res slots merge",
      ring["elemental_res"],
      {"fire": 1.10, "earth": 1.05, "dark": 1.05, "water": 1.05})
check("ring fourth element replaces slot 3",
      apply_infusion(ring, "light", ITEMS["ring"]), (True, ""))
check("ring slot 3 replaced, first two kept",
      ring["elemental_res"],
      {"fire": 1.10, "earth": 1.05, "dark": 1.05, "light": 1.05})
check("ring stats stay DEX through every slot", ring["mods"], {"Dexterity": 3})

print("=== Tier names (Ember -> Blaze -> Inferno) ===")
named = build_item("greatsword", "common")
check("uninfused name", named["name"], "Common Greatsword")
apply_infusion(named, "fire", ITEMS["greatsword"])
check("fire tier I name", named["name"], "Common Ember Greatsword")
for _ in range(2):
    apply_infusion(named, "fire", ITEMS["greatsword"])       # 1.20
check("still tier I at 1.20", named["name"], "Common Ember Greatsword")
apply_infusion(named, "fire", ITEMS["greatsword"])           # 1.25
check("still tier I at 1.25", named["name"], "Common Ember Greatsword")
apply_infusion(named, "fire", ITEMS["greatsword"])           # 1.30
check("tier II at 1.30", named["name"], "Common Blaze Greatsword")
apply_infusion(named, "fire", ITEMS["greatsword"])           # 1.35
check("still tier II at 1.35", named["name"], "Common Blaze Greatsword")
apply_infusion(named, "fire", ITEMS["greatsword"])           # 1.40
check("tier III at 1.40", named["name"], "Common Inferno Greatsword")
apply_infusion(named, "fire", ITEMS["greatsword"])           # 1.48
check("still tier III at 1.48", named["name"], "Common Inferno Greatsword")
apply_infusion(named, "wind", ITEMS["greatsword"])
check("secondary does not rename", named["name"], "Common Inferno Greatsword")

phys_named = build_item("greatsword", "common")
apply_infusion(phys_named, "physical", ITEMS["greatsword"])
check("innate axis gets prefix", phys_named["name"], "Common Iron Greatsword")

storm = build_item("sword", "rare")
apply_infusion(storm, "thunder", ITEMS["sword"])
check("thunder tier I word", storm["name"], "Rare Spark Sword")

plate_named = build_item("plate_armor", "uncommon")
apply_infusion(plate_named, "water", ITEMS["plate_armor"])
check("armor tier I word", plate_named["name"], "Uncommon Frost Plate Armor")
for _ in range(2):
    apply_infusion(plate_named, "water", ITEMS["plate_armor"])
check("armor tier III word", plate_named["name"], "Uncommon Abyssal Plate Armor")

print("=== v4 migration ===")
old = {"id": "inferno_greatsword", "name": "Inferno Greatsword", "type": "equipment",
       "slot": "weapon", "rarity": "rare", "enhance": 2}
_migrate_item_instance_v4(old)
check("migrated id", old["id"], "greatsword")
check("migrated primary", old["infusions"][0], {"element": "fire", "value": 1.48})
check("migrated secondary", old["infusions"][1], {"element": "physical", "value": 1.10})
check("migrated rarity/enhance", (old["rarity"], old["enhance"]), ("rare", 2))
check("migrated stats", old["mods"], {"Strength": 7})   # int((4+2) x 1.20)
check("migrated name", old["name"], "Rare Inferno Greatsword +2")
check("migrated trait III", old.get("trait_tier"), 3)
check("migrated value includes trait", intrinsic_value(old) > 0, True)

legacy = {"id": "magma_locket", "type": "equipment", "slot": "accessory",
          "rarity": "rare", "enhance": 0, "mods": {"Constitution": 4, "Strength": 1}}
_migrate_item_instance_v4(legacy)
check("legacy trophy untouched id", legacy["id"], "magma_locket")

print("=== Unique equipment: one primary + two flower slots ===")
vorpal = build_item("vorpal_blade", "unique")
check("vorpal primary", vorpal.get("primary_element"), "light")
check("unique name from template", vorpal["name"], "Vorpal Blade")
check("unique has no infusions", vorpal.get("infusions"), None)
_refresh_base_form_name(vorpal)
check("unique name untouched by load refresh", vorpal["name"], "Vorpal Blade")
check("vorpal single element", vorpal["elemental_dmg"], {"light": 1.35})
check("vorpal trait tier", vorpal.get("trait_tier"), 2)
check("vorpal trait II (Purge)", get_trait_for_weapon(vorpal, "unique").get("on_kill_cleanse"), 2)
fang = build_item("abyss_fang", "unique")
check("fang primary", fang.get("primary_element"), "dark")
check("fang trait II (Leech)", get_trait_for_weapon(fang, "unique").get("on_hit_leech_pct"), 0.12)
cutlass = build_item("cutlass_of_the_captain", "unique")
check("cutlass primary (explicit)", cutlass.get("primary_element"), "water")
check("cutlass trait II (Douse)", get_trait_for_weapon(cutlass, "unique").get("on_kill_cd_reduce"), 2)
wedding = build_item("wedding_centaur_scout", "unique")
check("unique accessories collapse to one element", wedding.get("elemental_dmg"), {"wind": 1.2})

print("=== Unique flower slots ===")
check("primary lock refuses", apply_infusion(fang, "dark", ITEMS["abyss_fang"]),
      (False, "primary element is fixed"))
check("add unique secondary", apply_infusion(fang, "fire", ITEMS["abyss_fang"]), (True, ""))
check("unique secondary 1.10", fang["elemental_dmg"],
      {"dark": 1.35, "fire": 1.10})
apply_infusion(fang, "fire", ITEMS["abyss_fang"])
apply_infusion(fang, "fire", ITEMS["abyss_fang"])
near("unique secondary caps at 1.20", fang["elemental_dmg"]["fire"], 1.20)
check("unique secondary cap refuses", apply_infusion(fang, "fire", ITEMS["abyss_fang"]),
      (False, "slot at cap"))
check("add unique tertiary", apply_infusion(fang, "water", ITEMS["abyss_fang"]), (True, ""))
check("unique tertiary 1.10", fang["elemental_dmg"],
      {"dark": 1.35, "fire": 1.20, "water": 1.10})
check("unique trait stays II", fang.get("trait_tier"), 2)
check("unique name never takes a flower word", fang["name"], "Abyss Fang")
apply_infusion(fang, "thunder", ITEMS["abyss_fang"])
check("unique fourth element replaces tertiary", fang["elemental_dmg"],
      {"dark": 1.35, "fire": 1.20, "thunder": 1.10})

jade = build_item("tarnished_jade", "unique")
check("unique armor primary", jade.get("primary_element"), "light")
check("unique armor one resistance", jade.get("elemental_res"), {"light": 1.3})
check("unique armor flower", apply_infusion(jade, "fire", ITEMS["tarnished_jade"]), (True, ""))
check("unique armor adds triangle resistances", jade.get("elemental_res"),
      {"light": 1.3, "fire": 1.15, "earth": 1.05})
check("unique armor primary lock", apply_infusion(jade, "light", ITEMS["tarnished_jade"]),
      (False, "primary element is fixed"))

pen = build_item("authors_pen", "unique")
check("damage accessory one primary", pen.get("elemental_dmg"), {"magical": 1.3})
check("damage accessory flower", apply_infusion(pen, "fire", ITEMS["authors_pen"]), (True, ""))
check("damage accessory flower adds damage", pen.get("elemental_dmg"),
      {"magical": 1.3, "fire": 1.10})

vile = build_item("vileheart_pendant", "unique")
check("dual accessory one dmg + one res",
      (vile.get("elemental_dmg"), vile.get("elemental_res")),
      ({"dark": 1.15}, {"dark": 1.2}))
check("dual accessory flower", apply_infusion(vile, "fire", ITEMS["vileheart_pendant"]), (True, ""))
check("dual accessory adds damage + resistance",
      (vile.get("elemental_dmg"), vile.get("elemental_res")),
      ({"dark": 1.15, "fire": 1.10}, {"dark": 1.2, "fire": 1.05}))

chance = build_item("chance_and_choice", "unique")
check("elementless unique has no primary", chance.get("primary_element"), None)
check("first flower claims elementless primary",
      apply_infusion(chance, "fire", ITEMS["chance_and_choice"]), (True, ""))
check("elementless primary is set", chance.get("primary_element"), "fire")
check("elementless primary gains resistance", chance.get("elemental_res"), {"fire": 1.05})

print("=== Unique load refresh (old saves) ===")
legacy_unique = {
    "id": "authors_pen", "type": "equipment", "slot": "accessory",
    "unique": True, "rarity": "unique", "enhance": 0,
    "mods": {"Charisma": 15, "Learning": 12, "Wisdom": 9},
    "elemental_dmg": {"magical": 1.3, "light": 1.3, "dark": 1.3},
}
_refresh_unique_instance(legacy_unique)
check("load refresh collapses old multi-profile", legacy_unique["elemental_dmg"],
      {"magical": 1.3})
legacy_unique["infusions"] = [{"element": "fire", "value": 1.15}]
_refresh_unique_instance(legacy_unique)
check("load refresh keeps flower slot", legacy_unique["elemental_dmg"],
      {"magical": 1.3, "fire": 1.15})
check("load refresh keeps authored name", legacy_unique["name"], "The Author's Pen")

print()
if failures:
    print("FAILED:", ", ".join(failures))
    sys.exit(1)
print("base forms + infusion model OK")
