"""Diagnose monster girls stored in houses for a savefile (read-only)."""
import json
import sys

PATH = sys.argv[1] if len(sys.argv) > 1 else "savefile/savegame_1.json"
with open(PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"== {PATH} ==")
print(f"player keys with 'house': {[k for k in data if 'house' in k.lower()]}")
print(f"allies: {[(a.get('name'), a.get('key'), a.get('_heroine_key')) for a in data.get('allies', [])]}")

for city_id, house in (data.get("houses") or {}).items():
    girls = house.get("monster_girls", [])
    print(f"\n-- {city_id}: house keys={list(house.keys())} girls={len(girls)}")
    for g in girls:
        print(f"   name={g.get('name')!r} key={g.get('key')!r} level={g.get('level')} "
              f"affection={g.get('affection')} "
              f"hk={g.get('_heroine_key')!r} perm={g.get('permanent')!r}")

# Check other possible storage locations
for k, v in data.items():
    if isinstance(v, dict) and any("girl" in str(kk).lower() for kk in v.keys()):
        print(f"\n!! top-level dict '{k}' has girl-ish keys: {list(v.keys())[:20]}")
    if isinstance(v, list) and v and isinstance(v[0], dict) and "girl" in str(v[0].get("key", "")).lower():
        print(f"\n!! top-level list '{k}' len={len(v)}")

# count of monster girls anywhere
import re
raw = json.dumps(data)
print(f"\nsave size: {len(raw)} bytes")
for term in ("monster_girls", "monster_girl", "harem", "house_monster"):
    print(f"  occurrences of {term!r}: {raw.count(term)}")
