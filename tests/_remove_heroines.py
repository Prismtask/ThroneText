"""Remove the bugged Red Hood + Dorothy copies from savegame_1.json.

Sends both heroines back to the house (gear returns to inventory, including
Grandmother's Axe +5 and Ruby Slippers +5) and removes them from the party.
Heroine states stay 'permanent', so the fixed inn/house code can re-recruit
them correctly later with their affection/exp preserved.
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

from combat.ally import _return_ally_to_house

houses = data.get("houses", {})
house_city, house = next(iter(houses.items()))

allies = data.get("allies", [])
removed = []
for ally in list(allies):
    if ally.get("_heroine_key") in ("red_hood", "dorothy"):
        _return_ally_to_house(data, ally, house)
        allies.remove(ally)
        removed.append(f"{ally['name']} (lvl {ally['level']}, aff {ally['affection']})")
        print(f"Sent {ally['name']} back to the house; gear returned to inventory.")

data["party_order"] = list(range(len(allies)))

with open(PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("\nRemoved from party:")
for r in removed:
    print(f"  - {r}")
print(f"\nRemaining party ({len(allies)} allies):")
for i, ally in enumerate(allies):
    print(f"  [{i}] {ally['name']!r} lvl={ally.get('level')}")
print("\nHouse heroine records:")
for g in house.get("monster_girls", []):
    if g.get("key", "").startswith("wonderland_"):
        print(f"  {g['name']!r} lvl={g.get('level')} aff={g.get('affection')}")
