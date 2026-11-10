"""Headless smoke test for Wonderland heroine auto-equipment tiers.

Covers the 15/25/35 floor bands, the rare +4 enhancement cap, the Wonderland
progress-floor fallback used by the inn, and the one-time re-tier migration
for temporary heroines already in old saves.

Run:
    .venv\\Scripts\\python.exe tests\\_diag_heroine_gear.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from combat.ally import (
    _get_heroine_floor_rarity,
    create_heroine_ally,
    migrate_heroine_auto_gear,
)
from resources.items import build_item

SLOTS = ("weapon", "armor", "accessory1", "accessory2")


def _player(max_floor, level=26):
    return {
        "level": level,
        "city_floors": {"wonderland": {"floor": max_floor,
                                       "max_floor": max_floor}},
    }


def _tiers(ally):
    return {(ally["equipped"][slot].get("rarity"),
             ally["equipped"][slot].get("enhance")) for slot in SLOTS}


print("== floor bands ==")
for floor, expected in (
    (1, ("common", 0)),
    (15, ("common", 0)),
    (16, ("uncommon", 1)),
    (25, ("uncommon", 1)),
    (26, ("rare", 3)),
    (35, ("rare", 3)),
    (36, ("rare", 4)),
    (50, ("rare", 4)),
):
    assert _get_heroine_floor_rarity(floor) == expected, (
        floor, _get_heroine_floor_rarity(floor))
print("   bands ok")

print("== Wonderland progress overrides the stale saved-dungeon floor ==")
for max_floor, expected in (
    (11, ("common", 0)),      # Red Hood, after Floor 10
    (21, ("uncommon", 1)),    # Dorothy, after Floor 20
    (31, ("rare", 3)),        # Alice, after Floor 30
    (41, ("rare", 4)),        # late rejoin / endgame
):
    p = _player(max_floor)
    for key in ("red_hood", "dorothy", "alice"):
        # floor=1 mimics the old inn fallback after a floor clear.
        ally = create_heroine_ally(p, key, floor=1)
        assert _tiers(ally) == {expected}, (max_floor, key, _tiers(ally))
print("   progress fallback ok")

print("== migration re-tiers only matching auto-equip pieces ==")
p = _player(11)
p["allies"] = [{
    "_heroine_key": "red_hood",
    "_wonderland_temp": True,
    "equipped": {
        "weapon": build_item("zephyr_bow", rarity="common", enhance=5),
        "armor": build_item("shadow_wraps", rarity="common", enhance=5),
        "accessory1": build_item("gale_boots", rarity="common", enhance=5),
        "accessory2": build_item("cyclone_anklet", rarity="common", enhance=5),
    },
}]
migrate_heroine_auto_gear(p)
assert p["heroine_gear_tier_version"] == 2
assert _tiers(p["allies"][0]) == {("common", 0)}, _tiers(p["allies"][0])
print("   temp heroine re-tiered")

print("== quest weapon and permanent heroines are preserved ==")
p = _player(31)
vorpal = build_item("vorpal_blade")
p["allies"] = [{
    "_heroine_key": "alice",
    "_wonderland_temp": True,
    "equipped": {
        "weapon": vorpal,
        "armor": build_item("blaze_battle_harness", rarity="common", enhance=5),
        "accessory1": build_item("stone_belt", rarity="common", enhance=5),
        "accessory2": build_item("ember_bracers", rarity="common", enhance=5),
    },
}, {
    "_heroine_key": "dorothy",
    "_wonderland_temp": False,
    "equipped": {
        "weapon": build_item("nether_grimoire", rarity="common", enhance=5),
        "armor": build_item("arcane_vestments", rarity="common", enhance=5),
        "accessory1": build_item("mystic_crown", rarity="common", enhance=5),
        "accessory2": build_item("astral_ring", rarity="common", enhance=5),
    },
}]
migrate_heroine_auto_gear(p)
alice, dorothy = p["allies"]
assert alice["equipped"]["weapon"]["id"] == "vorpal_blade"
assert alice["equipped"]["weapon"]["mods"] == vorpal["mods"]
assert all(alice["equipped"][slot].get("rarity") == "rare"
           for slot in ("armor", "accessory1", "accessory2"))
assert _tiers(dorothy) == {("common", 5)}, _tiers(dorothy)
print("   quest weapon + permanent heroine untouched")

print("")
print("Heroine auto-gear OK")
