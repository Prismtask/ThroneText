"""Repair savegame_1.json — Wonderland heroine dupe / lost-equipment bug.

What happened (root cause, summarized):
1. Leaving Wonderland (_leave_wonderland in facilities/arcane_tower.py) rebuilds
   the party from scratch and SILENTLY DROPS any heroine whose state it can't
   classify. A dropped heroine keeps her equipped items — they are never
   returned to inventory.
2. Party overflow sent heroines back to the house via _return_ally_to_house,
   which unequips gear; if inventory was full the item was destroyed
   ("was dropped") — that's how Ruby Slippers vanished.
3. House-recruited heroines (create_ally_from_girl) are missing _heroine_key,
   so get_heroine_in_party() can't find them. The Wonderland inn then offers
   "rejoin", which calls create_heroine_ally() — a FRESH copy with common
   auto-gear. Result: duplicates and lost signature items.

This script fixes the save:
- Keeps one Red Hood / one Dorothy (the upgraded copies), removes the dupes.
- Merges affection/exp from the house copies into the kept ones.
- Re-equips Grandmother's Axe +5 on Red Hood (from inventory) and rebuilds
  Ruby Slippers +5 for Dorothy (the upgrade flags are already set in-save).
- Re-applies the vorpal skill swaps, restores permanent passives, fixes caps.
"""
import json
import os
import shutil
import sys
import time

# Make repo root importable when running this script from tests/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PATH = "savefile/savegame_1.json"
BACKUP = f"savefile/savegame_1.backup_{time.strftime('%Y%m%d_%H%M%S')}.json"

shutil.copy2(PATH, BACKUP)
print(f"Backup written: {BACKUP}")

with open(PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

from resources.items import build_item
from combat.ally import equip_ally_item
from combat.ally_skills import (
    swap_redhood_to_vorpal_skills, grant_redhood_upgrade_skill,
    swap_dorothy_to_vorpal_skills, grant_dorothy_upgrade_skill,
)

allies = data.get("allies", [])
inv = data.setdefault("inventory", [])

# ── 1. Identify main vs duplicate heroine entries ────────────────────────
redhood_main = dorothy_main = None
redhood_house = dorothy_house = None
for ally in allies:
    if ally.get("_heroine_key") == "red_hood":
        redhood_main = ally
    elif ally.get("_heroine_key") == "dorothy":
        dorothy_main = ally
    elif ally.get("key") == "wonderland_red_hood":
        redhood_house = ally   # house-copy dupe (no _heroine_key)
    elif ally.get("key") == "wonderland_dorothy":
        dorothy_house = ally   # house-copy dupe (no _heroine_key)

assert redhood_main and dorothy_main, "Could not find main heroine entries!"

# ── 2. Merge house-copy progress into the kept copies ────────────────────
for main, house in ((redhood_main, redhood_house), (dorothy_main, dorothy_house)):
    if house:
        main["exp"] = house.get("exp", main.get("exp", 0))
        main["affection"] = house.get("affection", main.get("affection", 50))
        main["affection_cap"] = house.get("affection_cap", main.get("affection_cap", 100))
        main["engaged"] = house.get("engaged", main.get("engaged", False))
        main["married"] = house.get("married", main.get("married", False))
    main["level_cap"] = 99          # permanent heroines are uncapped
    main["_wonderland_temp"] = False

# ── 3. Red Hood: equip Grandmother's Axe +5 (from inventory) ──────────────
axe = next((i for i in inv if i.get("id") == "grandmothers_axe"), None)
if axe is None:
    axe = build_item("grandmothers_axe", rarity="unique", enhance=5)
    inv.append(axe)
print("Red Hood equip:", equip_ally_item(redhood_main, axe, data))

# ── 4. Dorothy: rebuild Ruby Slippers +5 and equip on accessory1 ──────────
ruby = build_item("ruby_slippers", rarity="unique", enhance=5)
inv.append(ruby)
print("Dorothy equip:", equip_ally_item(dorothy_main, ruby, data, target_slot="accessory1"))

# ── 5. Re-apply skill swaps + permanent passives ──────────────────────────
swap_redhood_to_vorpal_skills(redhood_main)
grant_redhood_upgrade_skill(redhood_main)
redhood_main["_heroine_permanent_passive"] = "grandmothers_lesson"

swap_dorothy_to_vorpal_skills(dorothy_main)
grant_dorothy_upgrade_skill(dorothy_main)
dorothy_main["_heroine_permanent_passive"] = "somewhere_over_rainbow"

# ── 6. Strip wonderland_only from equipped quest items (permanent now) ────
for ally in (redhood_main, dorothy_main):
    for slot in ("weapon", "armor", "accessory1", "accessory2"):
        item = ally.get("equipped", {}).get(slot)
        if item and item.get("wonderland_only"):
            item.pop("wonderland_only", None)

# ── 7. Remove duplicate house copies from the party ───────────────────────
for dupe in (redhood_house, dorothy_house):
    if dupe is not None and dupe in allies:
        allies.remove(dupe)

# ── 8. Rebuild party order ────────────────────────────────────────────────
data["party_order"] = list(range(len(allies)))

with open(PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("\nSave repaired:")
for i, ally in enumerate(allies):
    eq = {s: (ally.get("equipped", {}).get(s) or {}).get("id")
          for s in ("weapon", "armor", "accessory1", "accessory2")}
    print(f"  [{i}] {ally['name']!r} hk={ally.get('_heroine_key')!r} "
          f"inn={ally.get('innate_skills')} learned={ally.get('learned_skills')} eq={eq}")
