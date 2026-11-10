"""Restore the Fractured Hourglass to savegame_1.json.

Why: the Fractured Hourglass was bugged — it was consumed on use and did
nothing. The fix (combat/fractured_hourglass.py) makes it a reusable free
action: using it reduces all of the user's cooldowns by 1 (the user keeps
their turn), the item is never consumed, and the hourglass itself recharges
for 3 turns. It is combat-only.

This script gives the consumed hourglass back to save slot 1:
- Backs up the current save (savefile/savegame_1.backup_<timestamp>.json).
- Builds the item exactly like the Chrysalis drop does (build_item).
- Adds it via inventory.add_item_to_inventory() (respects bag caps).
- Refuses to add a duplicate if one is already present.
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
from inventory import add_item_to_inventory

inv = data.setdefault("inventory", [])
existing = [i for i in inv if i.get("id") == "fractured_hourglass"]

if existing:
    print("Fractured Hourglass already present in savegame_1 — nothing to do.")
else:
    # Same call as the Chrysalis victory drop
    item = build_item("fractured_hourglass", "legendary")
    if not add_item_to_inventory(data, item):
        raise SystemExit("Bag is full — no room to restore the hourglass. Nothing was changed.")
    print(f"Added: {item['name']} (id={item['id']}, special={item.get('special')})")

with open(PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

# ── Verify ───────────────────────────────────────────────────────────────
with open(PATH, "r", encoding="utf-8") as f:
    check = json.load(f)

found = [i for i in check.get("inventory", []) if i.get("id") == "fractured_hourglass"]
print(f"Verified: {len(found)} Fractured Hourglass in savegame_1 inventory.")
for i in found:
    print("  ", {k: i.get(k) for k in ("id", "name", "type", "rarity", "count", "special")})
