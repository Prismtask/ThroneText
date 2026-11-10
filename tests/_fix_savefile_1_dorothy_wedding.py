"""Repair savegame_1.json — Dorothy's wedding completion (2026-10-14).

Background (why this repair exists):
- The wonderland heroines had NO `wedding_<key>` accessory in resources/items.py,
  so when Dorothy's wedding fired, the game printed
  "(Wedding item 'wedding_wonderland_dorothy' not found — this is a bug.)"
  and granted nothing.
- Her affection cap had been reset to 100 by an old bug, so the wedding
  triggered at 100/100 instead of the intended 200-affection arc — and being
  engaged before the ring-transfer worked, she never received a ring bonus.

This script completes the marriage retroactively (user-approved 2026-10-14):
- timestamped backup first (savefile/savegame_1.backup_YYYYMMDD_HHMMSS.json);
- restores Dorothy's affection_cap to 200 (matches every other married girl);
- grants "Homeward Locket" (wedding_wonderland_dorothy) to the bag — skipped
  if already owned.

Run:
    .venv\\Scripts\\python.exe tests\\_fix_savefile_1_dorothy_wedding.py
"""
import json
import os
import shutil
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PATH = "savefile/savegame_1.json"
BACKUP = f"savefile/savegame_1.backup_{time.strftime('%Y%m%d_%H%M%S')}.json"

shutil.copy2(PATH, BACKUP)
print(f"Backup written: {BACKUP}")

with open(PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

from resources.items import build_item
from inventory import add_item_to_inventory

ITEM_ID = "wedding_wonderland_dorothy"

# ── Find Dorothy ─────────────────────────────────────────────────────────
dorothy = None
for ally in data.get("allies", []):
    if ally.get("_heroine_key") == "dorothy" or ally.get("key") == "wonderland_dorothy":
        dorothy = ally
        break

assert dorothy, "Dorothy not found in player['allies']"
assert dorothy.get("married"), "Dorothy is not married — aborting (rollback chosen?)"

old_cap = dorothy.get("affection_cap")
dorothy["affection_cap"] = 200
print(f"Dorothy cap: {old_cap} -> 200 (affection {dorothy.get('affection')}/200)")

# ── Grant the wedding accessory ──────────────────────────────────────────
inv = data.setdefault("inventory", [])
owned = any(it.get("id") == ITEM_ID for it in inv)
if not owned:
    item = build_item(ITEM_ID, "unique")
    if add_item_to_inventory(data, item):
        print(f"Granted: {item['name']} ({ITEM_ID})")
    else:
        print("!! Bag is full — free one slot and re-run (backup already made).")
else:
    print(f"Already owned {ITEM_ID} — nothing to grant.")

with open(PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
print("Save updated.")
