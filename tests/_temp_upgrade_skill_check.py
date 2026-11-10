# tests/_temp_upgrade_skill_check.py
# Verify the heroine facility-upgrade skill category fix:
#   upgrade skills (Frabjous Day / Through the Forest / Emerald City's Light)
#   live in their own `upgrade_skills` category — they do not consume one of
#   the MAX_LEARNED_SKILLS slots, are not teachable/replaceable at the
#   Barracks, survive save/load + house round-trips, and legacy saves that
#   stored them in learned_skills are migrated on load.
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from combat.ally_skills import (
    UPGRADE_SKILL_IDS,
    MAX_LEARNED_SKILLS,
    is_upgrade_skill,
    initialize_ally_skills,
    teach_ally_skill,
    replace_ally_learned_skill,
    get_usable_skills_in_combat,
    get_all_ally_skills,
    get_all_available_skills,
    grant_dorothy_upgrade_skill,
    revert_dorothy_to_normal_skills,
)
from combat.ally import _ally_to_house_record
from character import _reconcile_heroine_vorpal_skills
import facilities.barracks  # smoke: module imports cleanly with the new filter

print("=== Heroine upgrade-skill category check ===")

# ── 1. Registry ───────────────────────────────────────────────────────────
assert UPGRADE_SKILL_IDS == {"frabjous_day", "through_the_forest", "emerald_citys_light"}
assert is_upgrade_skill("emerald_citys_light")
assert not is_upgrade_skill("haste")
print("1. registry + is_upgrade_skill  [ok]")

# ── 2. initialize_ally_skills adds the field ──────────────────────────────
ally = {"name": "Test", "race": "Human"}
initialize_ally_skills(ally, "some_key_not_in_map", "Human")
assert ally["upgrade_skills"] == []
print("2. initialize_ally_skills defaults upgrade_skills  [ok]")

# ── 3. Collectors include upgrade skills ──────────────────────────────────
ally["upgrade_skills"] = ["emerald_citys_light"]
ally["skill_cooldowns"] = {}
usable = [sid for sid, _ in get_usable_skills_in_combat(ally)]
assert "emerald_citys_light" in usable, usable
all_skills = [sid for sid, _ in get_all_ally_skills(ally)]
assert "emerald_citys_light" in all_skills, all_skills
assert get_all_available_skills(ally)["upgrade"][0]["name"] == "Emerald City's Light"
ally["skill_cooldowns"]["emerald_citys_light"] = 3
assert "emerald_citys_light" not in [sid for sid, _ in get_usable_skills_in_combat(ally)]
print("3. combat collectors include upgrade skills (respect cooldowns)  [ok]")

# ── 4. Not teachable / not replaceable; normal teaching still works ───────
assert teach_ally_skill(ally, "emerald_citys_light") is False
assert teach_ally_skill(ally, "frabjous_day") is False
ally["skill_cooldowns"] = {}
ally["learned_skills"] = ["dodge"]
assert teach_ally_skill(ally, "protect") is True  # sanity: normal path intact
assert replace_ally_learned_skill(ally, "dodge", "protect") is True  # sanity: replace path intact
ally["learned_skills"] = ["dodge", "emerald_citys_light"]
assert replace_ally_learned_skill(ally, "emerald_citys_light", "protect") is False
assert "emerald_citys_light" in ally["learned_skills"]  # guard did not mutate
print("4. upgrade skills not teachable/replaceable; normal paths intact  [ok]")

# ── 5. Legacy save migration via reconcile (flag true) ────────────────────
player = {"wl_wizard_slippers_upgraded": True}
legacy = {
    "_heroine_key": "dorothy",
    "equipped": {},
    "innate_skills": ["cyclones_call", "heart_of_tin"],
    "learned_skills": ["haste", "radiant_rebirth", "emerald_citys_light"],
    "skill_mastery": {"emerald_citys_light": 150, "haste": 10},
    "skill_cooldowns": {},
}
_reconcile_heroine_vorpal_skills(legacy, player)
assert legacy["learned_skills"] == ["haste", "radiant_rebirth"], legacy["learned_skills"]
assert legacy["upgrade_skills"] == ["emerald_citys_light"], legacy["upgrade_skills"]
assert legacy["skill_mastery"]["emerald_citys_light"] == 150  # mastery preserved
assert legacy["_dorothy_vorpal_upgraded"] is True
real = [s for s in legacy["learned_skills"] if not is_upgrade_skill(s)]
assert len(real) < MAX_LEARNED_SKILLS  # slots freed
print("5. legacy learned_skills migration moves + preserves mastery  [ok]")

# ── 6. No flag, no weapon → stray learned copy stripped, not granted ──────
stray = {
    "_heroine_key": "dorothy",
    "equipped": {},
    "learned_skills": ["haste", "emerald_citys_light"],
    "skill_mastery": {},
    "skill_cooldowns": {},
}
_reconcile_heroine_vorpal_skills(stray, {})
assert stray["learned_skills"] == ["haste"], stray["learned_skills"]
assert "emerald_citys_light" not in stray.get("upgrade_skills", [])
print("6. stray copy without upgrade flag is stripped  [ok]")

# ── 7. grant is idempotent + never touches learned_skills ────────────────
dor = {
    "_heroine_key": "dorothy",
    "_dorothy_vorpal_skills": True,
    "learned_skills": [],
    "upgrade_skills": [],
}
grant_dorothy_upgrade_skill(dor)
grant_dorothy_upgrade_skill(dor)
assert dor["upgrade_skills"] == ["emerald_citys_light"]
assert dor["learned_skills"] == []
dor["learned_skills"] = ["emerald_citys_light"]  # legacy copy cleanup on grant
grant_dorothy_upgrade_skill(dor)
assert dor["learned_skills"] == []
assert dor["upgrade_skills"] == ["emerald_citys_light"]
print("7. grant writes upgrade_skills only (idempotent)  [ok]")

# ── 8. revert keeps the permanent upgrade skill ──────────────────────────
dor2 = {
    "_heroine_key": "dorothy",
    "_dorothy_vorpal_skills": True,
    "innate_skills": ["cyclones_call", "heart_of_tin"],
    "learned_skills": [],
    "upgrade_skills": ["emerald_citys_light"],
    "skill_cooldowns": {},
}
revert_dorothy_to_normal_skills(dor2)
assert dor2["innate_skills"] == ["no_place_like_home", "ruby_blink"]
assert dor2["upgrade_skills"] == ["emerald_citys_light"]  # permanent facility reward
print("8. weapon unequip reverts innates but keeps upgrade skill  [ok]")

# ── 9. House round-trip keeps the category ────────────────────────────────
rec_ally = {
    "key": "wonderland_dorothy", "name": "Dorothy", "level": 20,
    "current_hp": 50, "attributes": {}, "learned_skills": ["haste"],
    "upgrade_skills": ["emerald_citys_light"],
}
record = _ally_to_house_record(rec_ally, {})
assert record["upgrade_skills"] == ["emerald_citys_light"], record.get("upgrade_skills")
print("9. _ally_to_house_record persists upgrade_skills  [ok]")

print("All upgrade-skill category checks passed.")
