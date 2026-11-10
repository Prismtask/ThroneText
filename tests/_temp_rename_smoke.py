"""Smoke test — monster girl nicknames (2026-10).

Verifies:
  1. display_name / display_name_with_species helpers
  2. a nickname survives recruitment (house girl -> active ally)
  3. a nickname survives dismissal (active ally -> house record)
  4. the species `name` field is never overwritten (save matching depends on it)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import display_name, display_name_with_species
from resources.enemies import ENEMIES
from combat.ally import create_ally_from_girl, _return_ally_to_house, recruit_ally_from_house

KEY = "goblin_girl"
TEMPLATE = ENEMIES[KEY]
SPECIES = TEMPLATE["name"]

# ── 1. Display helpers ───────────────────────────────────────────────────────
g_nick = {"key": KEY, "name": SPECIES, "level": 5, "affection": 30, "captured_on": 1, "nickname": "Luna"}
assert display_name(g_nick) == "Luna"
assert display_name_with_species(g_nick) == f"Luna ({SPECIES})"
g_plain = {"key": KEY, "name": SPECIES, "level": 5, "affection": 30}
assert display_name(g_plain) == SPECIES
assert display_name_with_species(g_plain) == SPECIES

# ── 2. Rename survives recruitment ──────────────────────────────────────────
player = {
    "name": "Hero", "allies": [], "inventory": [], "quests": {},
    "houses": {"solmere": {"monster_girls": []}},
}
house = player["houses"]["solmere"]
house["monster_girls"].append(dict(g_nick))
ally, msg = recruit_ally_from_house(player, house["monster_girls"][0], house)
assert ally.get("nickname") == "Luna", ally.get("nickname")
assert display_name(ally) == "Luna"
assert "Luna" in msg, msg
assert not house["monster_girls"], "girl should have left the house"

# Also check create_ally_from_girl directly
ally_direct = create_ally_from_girl(dict(g_nick))
assert ally_direct.get("nickname") == "Luna", ally_direct.get("nickname")

# ── 3. Rename survives dismissal ────────────────────────────────────────────
_return_ally_to_house(player, ally, house)
assert len(house["monster_girls"]) == 1
rec = house["monster_girls"][0]
assert rec.get("nickname") == "Luna", rec

# ── 4. Species name untouched; clearing nickname restores species ───────────
assert rec["name"] == SPECIES and rec["key"] == KEY
rec["nickname"] = ""
assert display_name(rec) == SPECIES

print("Rename smoke test OK")
