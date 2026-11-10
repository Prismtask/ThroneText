"""Verify the house-wipe fix (in memory; does NOT write to disk).

Old bug: get_house_data()/save_house_data() resolved the target city from the
volatile player["origin_city"]. If it held a city without a house, the read
returned an empty list and the save rerouted it onto the first owned house —
wiping its monster_girls. The barracks skill-teach flow performed exactly this
read → save cycle.

Expected after fix: a read → save round-trip always targets the SAME house,
regardless of origin_city, so the girls survive.
"""
import json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from facilities.house import get_house_data, save_house_data  # noqa: E402

# ── Scenario: backup save (40 girls) but origin_city points at a city with no
#    house — this is the exact state that wiped the live save. ──────────────
bk = json.load(open("savefile/savegame_1.backup_20260926_014448.json", encoding="utf-8"))
bk["origin_city"] = "irondeep"  # simulation: travel/dungeon repointed origin_city

before = len(bk["houses"]["skylume"]["monster_girls"])
house_data = get_house_data(bk)
print(f"origin_city=irondeep, get_house_data -> {len(house_data)} girls (was {before} in house)")
save_house_data(bk, house_data)
after = len(bk["houses"]["skylume"]["monster_girls"])
print(f"after read -> save cycle      -> {after} girls")
print("=> FIXED: house preserved" if after == before == 40 else "=> STILL BROKEN")

# ── Real current save: resolving must be consistent (no crash, live list) ──
cur = json.load(open("savefile/savegame_1.json", encoding="utf-8"))
hd = get_house_data(cur)
save_house_data(cur, hd)
print(f"\ncurrent savegame_1: resolved house has {len(hd)} girls "
      f"(empty until the restore script runs)")
