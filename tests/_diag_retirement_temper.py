"""Diagnostic: curated-generic retirement, flowers and the tempering service.

Run: .venv\\Scripts\\python.exe tests/_diag_retirement_temper.py
"""
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from resources.items import ITEMS, build_item, intrinsic_value, item_value
from resources.item_generation import (
    LEGACY_ITEMS, RETIRED_GENERIC_IDS, FLOWER_ITEMS, ELEMENT_PREFIXES, _FORM_KEYS_BY_SLOT,
    flower_for_element, pick_flower_id, _WEAPON_POOLS, _ARMOR_POOLS, _ACCESSORY_POOLS,
)
from facilities.blacksmith import COMMISSION, TRANSMUTE_RATIO, transmute_flower

failures = []


def check(label, got, expected):
    ok = got == expected
    print(f"  {'OK  ' if ok else 'FAIL'} {label}: got {got}, expected {expected}")
    if not ok:
        failures.append(label)


print("=== Registry retirement ===")
curated_left = [i for i, d in ITEMS.items()
                if d.get("type") == "equipment" and not d.get("unique")
                and not d.get("composed") and not d.get("base_form")]
check("no hand-written generics in ITEMS", curated_left, [])
check("legacy table size", len(LEGACY_ITEMS), 12)
check("retired count (85)", len(RETIRED_GENERIC_IDS), 85)
check("composed weapons", sum(len(v) for v in _WEAPON_POOLS[1].values())
      + sum(len(v) for v in _WEAPON_POOLS[2].values())
      + sum(len(v) for v in _WEAPON_POOLS[3].values()), 782)
check("composed armor", sum(len(v) for g in _ARMOR_POOLS.values() for v in g.values()), 432)
check("composed accessories", sum(len(v) for g in _ACCESSORY_POOLS.values() for v in g.values()), 459)

print("=== Legacy items still work ===")
legacy = build_item("magma_locket", "rare")
check("legacy build name", legacy["name"], "Rare Magma Locket")
check("legacy build form", legacy.get("form"), "amulet")
check("legacy instance intrinsic (mods fallback)",
      intrinsic_value({"id": "magma_locket", "mods": {"Constitution": 4, "Strength": 1}}), 5)
check("legacy instance value", item_value({"id": "magma_locket", "rarity": "rare",
                                           "mods": {"Constitution": 4, "Strength": 1}}), 11)

print("=== v4 migration: grid -> base form + infusion ===")
from character import _migrate_item_economy
old = {"id": "steel_sword", "name": "Steel Sword", "type": "equipment", "slot": "weapon",
       "rarity": "common", "enhance": 0, "mods": {"Strength": 3}}
player = {"equipped": {"weapon": old}, "inventory": [], "allies": [],
          "wonderland_benched_allies": [], "houses": {}}
_migrate_item_economy(player)
check("steel sword rescaled to base STR", old["mods"]["Strength"], 2)
check("migrated to base form", old["id"], "sword")
check("migrated infusion (grade 2 -> 1.25)", old["infusions"], [{"element": "physical", "value": 1.25}])
check("name refreshed with tier word", old["name"], "Common Iron Sword")
check("migration version", player["item_formula_version"], 4)

print("=== Flowers ===")
check("flower count", len(FLOWER_ITEMS), 9)
check("fire flower", flower_for_element("fire"), "emberbloom")
check("dark flower", flower_for_element("dark"), "nightbloom")
check("unknown element", flower_for_element("void"), None)
for element, item_id in FLOWER_ITEMS.items():
    d = ITEMS.get(item_id, {})
    check(f"{item_id} element/type", (d.get("flower_element"), d.get("type")), (element, "crafting_material"))
    check(f"{item_id} not shop stock", bool(d.get("no_random_stock")), True)

random.seed(7)
picks = [pick_flower_id("volcanic") for _ in range(2000)]
fire_share = sum(1 for i in picks if i == "emberbloom") / len(picks)
check("volcanic favours emberbloom (>18%)", fire_share > 0.18, True)

# 60% enemy element / 40% biome blend
random.seed(21)
blended = [pick_flower_id("tundra", enemy_element="fire") for _ in range(4000)]
blend_share = sum(1 for i in blended if i == "emberbloom") / len(blended)
check("blend leans on the enemy element (~63%)", 0.58 <= blend_share <= 0.70, True)
random.seed(21)
neutral = [pick_flower_id("tundra", enemy_element=None) for _ in range(4000)]
neutral_fire = sum(1 for i in neutral if i == "emberbloom") / len(neutral)
check("neutral enemy stays biome-weighted (~8%)", 0.05 <= neutral_fire <= 0.13, True)
import dungeon
check("enemy element helper", dungeon._enemy_attack_element("beast_thunder_bird"), "thunder")
check("neutral enemy falls back to physical", dungeon._enemy_attack_element("human_footpad"), "physical")

# Every flower must have at least one biome where its element is favoured
from resources.item_generation import ELEMENT_WEIGHTS_BY_BIOME
no_favoured = [el for el in FLOWER_ITEMS
               if max(w.get(el, 1) for w in ELEMENT_WEIGHTS_BY_BIOME.values()) < 2]
check("every flower has a favoured biome", no_favoured, [])

print("=== Flower drops ===")
import dungeon
random.seed(11)
drops = [dungeon.roll_drop(10, biome="forest") for _ in range(2000)]
flowers = [d for d in drops if d and d[0] in FLOWER_ITEMS.values()]
check("roll_drop yields flowers", len(flowers) > 20, True)
check("flower rarity is common", all(r == "common" for _i, r in flowers), True)
check("all drops are valid ids", all(d is None or d[0] in ITEMS for d in drops), True)

print("=== Biome craft signature (form bias) ===")
from resources.item_generation import biome_craft_hint
volcanic_hint = biome_craft_hint("volcanic")
check("volcanic names axe/hammer", ("Axe" in volcanic_hint and "Hammer" in volcanic_hint), True)
check("mountain names maul", "Maul" in biome_craft_hint("mountain"), True)
check("unknown biome has no hint", biome_craft_hint("nowhere"), "")
check("empty biome has no hint", biome_craft_hint(None), "")

print("=== Infusion model (full coverage in _diag_infusion.py) ===")
from resources.item_generation import apply_infusion, WEAPON_SLOT_LADDERS, TRAIT_THRESHOLDS
s = build_item("greatsword", "common")
check("apply fire infusion", apply_infusion(s, "fire", ITEMS["greatsword"])[0], True)
check("primary ladder cap", WEAPON_SLOT_LADDERS[0][-1], 1.48)
check("secondary/tertiary caps", (WEAPON_SLOT_LADDERS[1][-1], WEAPON_SLOT_LADDERS[2][-1]), (1.20, 1.15))
check("trait thresholds", TRAIT_THRESHOLDS, (1.25, 1.35, 1.48))
check("infusion sets element", s["elemental_dmg"], {"fire": 1.10})
check("uniques keep one identity element", ITEMS["vorpal_blade"]["elemental_dmg"], {"light": 1.5})

print("=== Forge Commission (P7) ===")
check("commission cost", COMMISSION, {"flowers": 1, "gold": 600})
missing_commission = []
for slot, forms in _FORM_KEYS_BY_SLOT.items():
    for form in forms:
        for element, prefixes in ELEMENT_PREFIXES.items():
            item_id = f"{prefixes[0].lower()}_{form}"
            if item_id not in ITEMS or ITEMS[item_id].get("grade") != 1:
                missing_commission.append(item_id)
check("every commission coordinate exists (g1)", missing_commission, [])

print("=== Flower transmutation (3:1) ===")
from facilities.blacksmith import TRANSMUTE_RATIO, transmute_flower
check("ratio is 3", TRANSMUTE_RATIO, 3)
p = {"inventory": [build_item("emberbloom", "common")]}
p["inventory"][0]["count"] = 3
check("3 emberbloom -> 1 nightbloom", transmute_flower(p, "fire", "dark"), True)
check("fire flowers consumed",
      sum(it.get("count", 1) for it in p["inventory"] if it.get("id") == "emberbloom"), 0)
check("dark flower gained",
      sum(it.get("count", 1) for it in p["inventory"] if it.get("id") == "nightbloom"), 1)
p2 = {"inventory": [build_item("emberbloom", "common")]}
p2["inventory"][0]["count"] = 2
check("insufficient flowers refused", transmute_flower(p2, "fire", "dark"), False)
check("same element refused", transmute_flower(p, "dark", "dark"), False)
check("unknown element refused", transmute_flower(p, "fire", "void"), False)

print("=== Flower consumption ===")
from inventory import consume_stackable_items
player = {"inventory": [build_item("emberbloom", "common") for _ in range(2)]}
player["inventory"][0]["count"] = 2
player["inventory"][1]["count"] = 2
consume_stackable_items(player, lambda it: it.get("id") == "emberbloom", 3)
left = sum(it.get("count", 1) for it in player["inventory"] if it.get("id") == "emberbloom")
check("consumed 3 of 4 flowers", left, 1)

print()
if failures:
    print("FAILED:", ", ".join(failures))
    sys.exit(1)
print("retirement + infusion OK")
