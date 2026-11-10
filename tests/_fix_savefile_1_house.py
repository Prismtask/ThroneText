"""Repair savegame_1.json — restore the monster-girl harem wiped by the
house routing bug (see facilities/house.py::_resolve_house docstring).

What happened:
- facilities/barracks.py::teach_ally_skill_submenu does a read → save cycle:
      house_data = get_house_data(player)     # resolved via player["origin_city"]
      save_house_data(player, house_data)     # resolved via player["origin_city"]
- origin_city had been repointed to "irondeep" (travel/dungeon nearest-city
  context) where the player owns no house, so the read returned a fresh empty
  list and the save rerouted it onto the first owned house (skylume) —
  replacing its 40-girl monster_girls list with []. Only Ninetales Fox
  survived because she had been recruited into the party first.

This script:
- Backs up the current save (savefile/savegame_1.backup_<timestamp>.json).
- Copies the monster_girls records from the 2026-09-26 backup.
- Skips any girl already in the current party (Ninetales Fox) or already in
  the current house list (safety).
- Writes the merged save in the exact format save_load.save_game uses
  (json.dump(..., indent=2, ensure_ascii=False)).
"""
import json
import os
import shutil
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PATH = "savefile/savegame_1.json"
SOURCE = "savefile/savegame_1.backup_20260926_014448.json"
BACKUP = f"savefile/savegame_1.backup_{time.strftime('%Y%m%d_%H%M%S')}.json"

shutil.copy2(PATH, BACKUP)
print(f"Safety backup written: {BACKUP}")

with open(PATH, "r", encoding="utf-8") as f:
    data = json.load(f)
with open(SOURCE, "r", encoding="utf-8") as f:
    source = json.load(f)

houses = data.get("houses") or {}
assert houses, "current save has no houses — aborting"
home_city, home = next(iter(houses.items()))
print(f"Home house: {home_city} (level {home.get('level')})")

source_house = (source.get("houses") or {}).get(home_city)
assert source_house is not None, f"backup has no house in {home_city} — aborting"
source_girls = source_house.get("monster_girls", [])
print(f"Backup girls in {home_city}: {len(source_girls)}")

current = home.setdefault("monster_girls", [])
print(f"Current girls in {home_city}: {len(current)}")

party_keys = {a.get("key") for a in data.get("allies", [])}
present = {(g.get("key"), g.get("name")) for g in current}

restored, skipped_party, skipped_present = [], [], []
for girl in source_girls:
    key, name = girl.get("key"), girl.get("name")
    if key in party_keys:
        skipped_party.append(f"{name} ({key}) — already in party")
        continue
    if (key, name) in present:
        skipped_present.append(f"{name} ({key}) — already in house")
        continue
    restored.append(girl)

home["monster_girls"] = current + restored

with open(PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"\nRestored {len(restored)} girls into {home_city} "
      f"(house now holds {len(home['monster_girls'])}):")
for g in restored:
    aff = g.get("affection")
    cap = g.get("affection_cap", 100)
    flags = []
    if g.get("married"):
        flags.append("married")
    elif g.get("engaged"):
        flags.append("engaged")
    flag_str = f" [{', '.join(flags)}]" if flags else ""
    print(f"  - {g.get('name')} (Lv {g.get('level')}, affection {aff}/{cap}){flag_str}")

for msg in skipped_party:
    print(f"\nSkipped (in party): {msg}")
for msg in skipped_present:
    print(f"Skipped (already in house): {msg}")

print(f"\nSave repaired: {PATH}")
