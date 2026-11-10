"""Diagnostic: item economy tuning (valuation, caps, multiplicative enhance, fusion fee, migration).

Run: .venv\\Scripts\\python.exe tests/_diag_item_economy.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from resources.items import (
    ITEMS, build_item, intrinsic_value, item_value, item_value_at_rarity,
    cap_rarity_for_item, fusion_fee,
)

failures = []


def check(label, got, expected):
    ok = got == expected
    print(f"  {'OK  ' if ok else 'FAIL'} {label}: got {got}, expected {expected}")
    if not ok:
        failures.append(label)


print("=== Intrinsic value (stats + extra elements + specials) ===")
check("iron_sword", intrinsic_value("iron_sword"), 2)
check("inferno_greatsword", intrinsic_value("inferno_greatsword"), 14)
check("frost_blade", intrinsic_value("frost_blade"), 7)
check("stone_mace", intrinsic_value("stone_mace"), 5)
check("titan_shield (con_defense + scaling_mult + grade 3)", intrinsic_value("titan_shield"), 14)

print("=== Item value (intrinsic + enhance) x rarity ===")
check("greatsword common", item_value(build_item("greatsword", "common")), 5)
check("greatsword legendary", item_value(build_item("greatsword", "legendary")), 40)
check(
    "greatsword legendary +10",
    item_value(build_item("greatsword", "legendary", enhance=10)),
    120,
)
check(
    "value at rarity (fusion preview)",
    item_value_at_rarity(build_item("greatsword", "common"), "legendary"),
    40,
)

print("=== Rarity ceiling (D-N - soft, not clamped) ===")
check("iron sword (grade 1) hard cap removed", cap_rarity_for_item("iron_sword", "legendary"), "legendary")
check("stone mace (grade 1) hard cap removed", cap_rarity_for_item("stone_mace", "legendary"), "legendary")
check("inferno greatsword (grade 3) legendary", cap_rarity_for_item("inferno_greatsword", "legendary"), "legendary")

print("=== Compressed enhancement (stats only) ===")
common10 = build_item("greatsword", "common", enhance=10)
legend10 = build_item("greatsword", "legendary", enhance=10)
legend0 = build_item("greatsword", "legendary", enhance=0)
check("common +10 STR", common10["mods"]["Strength"], 14)      # int((4+10) x 1.0)
check("legendary +0 STR", legend0["mods"]["Strength"], 5)      # int(4 x 1.4)
check("legendary +10 STR", legend10["mods"]["Strength"], 19)   # int((4+10) x 1.4)
check("enhance never touches element", (common10["elemental_dmg"], legend10["elemental_dmg"]),
      ({"physical": 1.10}, {"physical": 1.10}))

print("=== Fusion fee (50 x value delta, min 150) ===")
check("greatsword common -> rare fee", fusion_fee(build_item("greatsword", "common"), "rare"), 300)
gs_common10 = build_item("greatsword", "common", enhance=10)
check("greatsword +10 common -> legendary fee", fusion_fee(gs_common10, "legendary"), 5250)
check("minimum fee", fusion_fee(build_item("sword", "common"), "rare"), 200)

print("=== Owned-item migration (v4) ===")
from character import _migrate_item_economy

old = {
    "id": "inferno_greatsword", "name": "Inferno Greatsword +5",
    "type": "equipment", "slot": "weapon", "rarity": "legendary",
    "enhance": 5, "mods": {"Strength": 10},
}
player = {
    "equipped": {"weapon": old, "armor": None},
    "inventory": [],
    "allies": [{"equipped": {"weapon": dict(old, mods={"Strength": 10})}}],
    "wonderland_benched_allies": [],
    "houses": {"solmere": {"storage": [dict(old, mods={"Strength": 10})]}},
}
_migrate_item_economy(player)
expected = int((4 + 5) * 1.4)
check("equipped weapon rescaled", old["mods"]["Strength"], expected)
check("migrated to base form", old["id"], "greatsword")
check("migrated infusion", old["infusions"][0], {"element": "fire", "value": 1.48})
check("ally weapon rescaled", player["allies"][0]["equipped"]["weapon"]["mods"]["Strength"], expected)
check("house storage rescaled", player["houses"]["solmere"]["storage"][0]["mods"]["Strength"], expected)
check("migration flag", player["item_econ_migrated"], True)
check("migration version", player["item_formula_version"], 4)
old["mods"]["Strength"] = 999
_migrate_item_economy(player)
check("migration is idempotent (flag)", old["mods"]["Strength"], 999)

print("=== Rarity-linked enhancement cap ===")
from resources.items import ENHANCE_CAP_BY_RARITY, enhance_cap_for
check("common cap", enhance_cap_for({"rarity": "common"}), 5)
check("rare cap", enhance_cap_for({"rarity": "rare"}), 7)
check("epic cap", enhance_cap_for({"rarity": "epic"}), 8)
check("legendary cap", enhance_cap_for({"rarity": "legendary"}), 10)
check("unique cap", enhance_cap_for({"rarity": "unique", "unique": True}), 5)
check("cap ladder", list(ENHANCE_CAP_BY_RARITY.values()), [5, 6, 7, 8, 10])

print("=== Unique items: slot budgets ===")
unique = build_item("abyss_fang", enhance=2)
check("unique rarity", unique["rarity"], "unique")
check("unique +2 uses base + enhance (no hidden bonus)",
      sum(unique["mods"].values()), sum(ITEMS["abyss_fang"]["base_mods"].values()) + 2 * len(unique["mods"]))
maxed = build_item("abyss_fang", enhance=5)
check("unique weapon total at +5", sum(maxed["mods"].values()), 32)
armor_maxed = build_item("tarnished_jade", enhance=5)
check("unique armor total at +5", sum(armor_maxed["mods"].values()), 33)
accessory_maxed = build_item("wedding_centaur_scout", enhance=5)
check("unique accessory total at +5", sum(accessory_maxed["mods"].values()), 26)

print()
if failures:
    print("FAILED:", ", ".join(failures))
    sys.exit(1)
print("item economy tuning OK")
