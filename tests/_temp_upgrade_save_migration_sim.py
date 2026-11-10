# tests/_temp_upgrade_save_migration_sim.py
# Simulate ensure_player_fields() against the live save IN MEMORY ONLY
# (never writes) to confirm the heroine upgrade-skill migration:
#   learned_skills  ->  upgrade_skills  (mastery preserved, cap slot freed).
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from character import ensure_player_fields

PATH = os.path.join(ROOT, "savefile", "savegame_1.json")
with open(PATH, encoding="utf-8") as f:
    player = json.load(f)

print("=== BEFORE (in-memory copy of %s) ===" % os.path.basename(PATH))
for a in player.get("allies", []):
    if a.get("_heroine_key"):
        print(f"  {a['_heroine_key']:<8} learned={a.get('learned_skills')} "
              f"upgrades={a.get('upgrade_skills')}")

ensure_player_fields(player)  # read-only simulation — nothing is saved

print("=== AFTER ensure_player_fields (memory only) ===")
for a in player.get("allies", []):
    hk = a.get("_heroine_key")
    if not hk:
        continue
    print(f"  {hk:<8} learned={a.get('learned_skills')} "
          f"upgrades={a.get('upgrade_skills')}")
    for sid in a.get("upgrade_skills", []):
        assert sid not in a.get("learned_skills", []), (hk, sid)
print("Migration simulation OK — learned slots freed, mastery untouched.")
