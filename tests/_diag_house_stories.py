"""Headless smoke test for Fireside Tales (house stories).

Covers: state seeding, roster collection/dedupe, requirement gates,
effects/affection clamps, progression, city triggers, replay safety and
data integrity.

Run:
    .venv\\Scripts\\python.exe tests\\_diag_house_stories.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# Headless runs must never open the level-up UI, and must never write saves.
import leveling
leveling.gain_exp = lambda player, amount: None
import save_load
save_load.save_game = lambda player: None

from character import build_character
from resources.house_stories import HOUSE_STORIES, ensure_state, get_part
import facilities.house_stories as hs
import quests


# ── Fixtures ────────────────────────────────────────────────────────────────

ATTRS = {"Strength": 5, "Constitution": 5, "Dexterity": 5,
         "Learning": 5, "Wisdom": 5, "Charisma": 5}

player = build_character("1", "1", ATTRS, "Diag", 1)
player.pop("save_slot", None)
player["gold"] = 100
player["houses"] = {
    "solmere": {"level": 2, "storage": [], "last_income_day": 1, "monster_girls": []},
}
player["allies"] = []
player["wonderland_benched_allies"] = []


def add_girl(group, key, name, affection, cap=100):
    girl = {"key": key, "name": name, "affection": affection,
            "affection_cap": cap, "level": 5, "stress": 10}
    group.append(girl)
    return girl


goblin = add_girl(player["houses"]["solmere"]["monster_girls"],
                  "goblin_girl", "Goblin Girl", 50)
harpy = add_girl(player["allies"], "harpy_scout", "Harpy Scout", 45)
slime = add_girl(player["wonderland_benched_allies"], "slime_girl", "Slime Girl", 40)


# ── State seeding ───────────────────────────────────────────────────────────

print("== state seeding ==")
old_save = {"name": "Old Save"}
ensure_state(old_save)
assert old_save["house_stories"] == {"seen": {}}
assert "house_stories" in player, "build_character must seed house_stories"
assert isinstance(ensure_state(player)["seen"], dict)
print("   ok")


# ── Roster collection ───────────────────────────────────────────────────────

print("== roster collection ==")
owned = hs.all_owned_girls(player)
assert len(owned) == 3, f"expected 3 girls, got {len(owned)}"
# Duplicate the same girl in a second list -> dedupe by key:name.
player["houses"]["solmere"]["monster_girls"].append(
    {"key": "goblin_girl", "name": "Goblin Girl", "affection": 99})
assert len(hs.all_owned_girls(player)) == 3, "duplicate roster entry counted twice"
player["houses"]["solmere"]["monster_girls"].pop()
assert hs.find_girl(player, "goblin_girl") is goblin
assert hs.find_girl(player, "nobody") is None
print("   ok")


# ── Requirement gates ───────────────────────────────────────────────────────

print("== requirement gates ==")
story = HOUSE_STORIES["lucky_coin"]
part1 = get_part("lucky_coin_1")[3]
req1 = hs.merge_requirements(story, part1)
met, missing = hs.requirement_status(player, req1)
assert met, f"lucky coin part 1 should be ready: {missing}"

goblin["affection"] = 20
met, missing = hs.requirement_status(player, req1)
assert not met, "low affection should lock the part"
assert any("Goblin Girl" in line or "affection" in line for line in missing), missing
goblin["affection"] = 50

# Featured girl absent.
player["houses"]["solmere"]["monster_girls"].remove(goblin)
met, missing = hs.requirement_status(player, req1)
assert not met and any("Goblin Girl" in line for line in missing), missing
player["houses"]["solmere"]["monster_girls"].append(goblin)

# Ensemble gate: 3 girls at 40+, house level 2.
small = HOUSE_STORIES["small_hours"]
info = hs.story_status(player, small, "solmere")
assert info["state"] == "ready", info
player["houses"]["solmere"]["level"] = 1
info = hs.story_status(player, small, "solmere")
assert info["state"] == "locked", info
assert any("house level" in line for line in info["missing"]), info["missing"]
player["houses"]["solmere"]["level"] = 2
print("   ok")


# ── Designated allies & superboss gates ─────────────────────────────────────

print("== designated allies ==")
centaur = add_girl(player["houses"]["solmere"]["monster_girls"],
                   "centaur_scout", "Centaur Scout", 50)
harpy["affection"] = 50
pair = HOUSE_STORIES["two_of_a_kind"]
info = hs.story_status(player, pair, "solmere")
assert info["state"] == "ready", info
player["houses"]["solmere"]["monster_girls"].remove(centaur)
info = hs.story_status(player, pair, "solmere")
assert info["state"] == "locked", info
assert any("Centaur Scout" in line for line in info["missing"]), info["missing"]
player["houses"]["solmere"]["monster_girls"].append(centaur)

# Pair effects target only the two designated girls.
snapshot = (goblin["affection"], harpy["affection"], centaur["affection"])
hs.apply_effects(player, pair, get_part("two_of_a_kind_1")[3])
assert harpy["affection"] == snapshot[1] + 2, "pair effect missed the harpy"
assert centaur["affection"] == snapshot[2] + 2, "pair effect missed the centaur"
assert goblin["affection"] == snapshot[0], "pair effect leaked onto a bystander"
print("   ok")

print("== superboss gates ==")
palette_arc = HOUSE_STORIES["palette_afterimage"]
player.pop("boss_defeated_palette", None)
player["defeated_superbosses"] = [k for k in player.get("defeated_superbosses", [])
                                  if k != "chromatic_artisan"]
info = hs.story_status(player, palette_arc, "solmere")
assert info["state"] == "locked", info
assert any("Palette" in line for line in info["missing"]), info["missing"]

# The top-level fight flag is enough (old saves may lack the shared ledger).
player["boss_defeated_palette"] = True
info = hs.story_status(player, palette_arc, "solmere")
assert info["state"] == "ready" and info["next_part"]["id"] == "palette_afterimage_1", info

# Part 2 requires Palette in the household; part 3 also needs 100 affection.
info = hs.story_status(player, palette_arc, "solmere")
assert info["state"] == "ready"
assert hs.play_part(player, "palette_afterimage_1")
info = hs.story_status(player, palette_arc, "solmere")
assert info["state"] == "locked", info
assert any("Palette" in line for line in info["missing"]), info["missing"]

palette = add_girl(player["allies"], "wonderland_palette", "Palette", 60)
info = hs.story_status(player, palette_arc, "solmere")
assert info["state"] == "ready" and info["next_part"]["id"] == "palette_afterimage_2", info
palette["affection"] = 100
info = hs.story_status(player, palette_arc, "solmere")
assert info["state"] == "ready" and info["next_part"]["id"] == "palette_afterimage_2", info
hs.play_part(player, "palette_afterimage_2")
info = hs.story_status(player, palette_arc, "solmere")
assert info["state"] == "ready" and info["next_part"]["id"] == "palette_afterimage_3", info

# White Knight gate comes from the shared kill ledger.
oath = HOUSE_STORIES["oath_after"]
player["defeated_superbosses"] = [k for k in player.get("defeated_superbosses", [])
                                  if k != "white_knight"]
info = hs.story_status(player, oath, "solmere")
assert info["state"] == "locked", info
assert any("White Knight" in line for line in info["missing"]), info["missing"]
player["defeated_superbosses"].append("white_knight")
info = hs.story_status(player, oath, "solmere")
assert info["state"] == "ready" and info["next_part"]["id"] == "oath_after_1", info
print("   ok")


# ── Effects & clamps ────────────────────────────────────────────────────────

print("== effects ==")
story_before = goblin["affection"]
messages = hs.apply_effects(player, story, get_part("lucky_coin_3")[3])
assert goblin["affection"] == story_before + 6, messages
assert any("affection" in m for m in messages), messages
assert player["gold"] == 100, "lucky coin part 3 grants no gold"

# Ensemble effect hits every qualifying girl and clamps at the cap.
harpy["affection_cap"] = 45
harpy["affection"] = 45
stress_before = [g["stress"] for g in (goblin, harpy, slime)]
hs.apply_effects(player, small, get_part("small_hours_1")[3])
assert harpy["affection"] == 45, "affection must clamp at cap"
assert all(g["stress"] <= s for g, s in zip((goblin, harpy, slime), stress_before)), \
    "stress should relax, never rise"
print("   ok")


# ── City trigger + progression ──────────────────────────────────────────────

print("== city trigger ==")
# Reset the moth arc state; keep three girls at 40+.
hs.ensure_house_story_state(player)["seen"].clear()
flags = quests.ensure_quest_state(player)["flags"]
flags.pop("met_voss", None)
assert hs.claim_city_trigger(player, "skylume") is None, \
    "moth arc must wait for met_voss"
flags["met_voss"] = True
assert hs.claim_city_trigger(player, "solmere") is None, \
    "moth arc part 1 is a Skylume trigger"
part = hs.claim_city_trigger(player, "skylume")
assert part and part["id"] == "moth_window_1", part
print("   ok")

print("== play + replay ==")
goblin["affection"] = 50
before = goblin["affection"]
assert hs.play_part(player, "moth_window_1", city_id="skylume")
assert "moth_window_1" in hs.ensure_house_story_state(player)["seen"]
assert goblin["affection"] == before + 1, "part-1 affection_all should land once"
events = [e for e in player["journal"]["events"] if e.get("tag") == "[STORY]"]
assert any("The Letter" in e["name"] for e in events), events

# City part is no longer claimable once read, and the next part is a house part.
assert hs.claim_city_trigger(player, "skylume") is None
info = hs.story_status(player, HOUSE_STORIES["moth_at_the_window"], "solmere")
assert info["state"] == "ready" and info["next_part"]["id"] == "moth_window_2", info

# Replay must not re-apply effects.
after_first = goblin["affection"]
assert hs.play_part(player, "moth_window_1", replay=True, city_id="skylume")
assert goblin["affection"] == after_first, "replay re-applied effects"
print("   ok")

print("== readiness badge ==")
ready = hs.available_ready_count(player, "solmere")
assert ready >= 2, f"expected at least lucky_coin + small_hours ready, got {ready}"
print("   ", ready, "ready arcs")


# ── Data integrity ──────────────────────────────────────────────────────────

print("== data integrity ==")
part_ids = set()
for story_id, story in HOUSE_STORIES.items():
    assert story.get("title") and story.get("parts"), story_id
    for number, part in enumerate(story["parts"], start=1):
        pid = part.get("id")
        assert pid and pid not in part_ids, f"duplicate part id: {pid}"
        part_ids.add(pid)
        assert part.get("title") and part.get("lines"), pid
        for line in part["lines"]:
            assert isinstance(line, str) and line.strip(), (pid, line)
print("   ", len(HOUSE_STORIES), "arcs,", len(part_ids), "parts")

print("\nAll Fireside Tales checks passed.")
