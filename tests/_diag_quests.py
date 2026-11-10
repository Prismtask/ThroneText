"""Headless smoke test for the quest system (Phases 1-3 + MQ3-MQ6 chain).

Exercises: state seeding, start_quest, state-based objectives, hook updates,
auto-completion, rewards, journal sync, idempotency, the story queue,
party-cap grades, roster backfill, and the main-quest chain catch-up.

Run:
    .venv\\Scripts\\python.exe tests\\_diag_quests.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# Headless runs must never open the level-up UI.
import leveling
leveling.gain_exp = lambda player, amount: print(f"    [stub] gain_exp({amount})")

from character import build_character
import quests
import wonderland_guests

ATTRS = {"Strength": 5, "Constitution": 5, "Dexterity": 5,
         "Learning": 5, "Wisdom": 5, "Charisma": 5}

player = build_character("1", "1", ATTRS, "Diag", 1)
assert "quests" in player, "build_character must seed quests state"

print("== start quest ==")
for m in quests.start_quest(player, "mq_archivist_01"):
    print("  ", m)
assert quests.quest_state(player, "mq_archivist_01") == "active"
assert len(player["journal"]["main_quests"]) == 1

print("== travel to Skylume ==")
player["location"] = "skylume"
quests.update_quests(player, "visit_city", "skylume")
q = player["journal"]["main_quests"][0]
assert q["objectives"][0]["done"], "Reach Skylume should be done"
assert not q["objectives"][1]["done"], "Star Tower should still be pending"

print("== enter Star Tower ==")
quests.update_quests(player, "visit_service", "star_tower")
q = player["journal"]["main_quests"][0]
assert q["objectives"][1]["done"], "Enter the Star Tower should be done"

print("== speak with Voss (auto-completes) ==")
for m in quests.update_quests(player, "talk_npc", "archivist_voss"):
    print("  ", m)

assert quests.quest_state(player, "mq_archivist_01") == "completed"
q = next(e for e in player["journal"]["main_quests"] if e["id"] == "mq_archivist_01")
assert q["status"] == "complete"
assert all(o["done"] for o in q["objectives"])
assert player["quests"]["flags"].get("met_voss"), "met_voss flag should be set"
assert player["gold"] == 180, f"gold should be 100+80, got {player['gold']}"

print("== journal events ==")
evt_names = [e["name"] for e in player["journal"]["events"]]
assert "Quest Started: The Stellar Summons" in evt_names
assert "Quest Complete: The Stellar Summons" in evt_names

print("== idempotency ==")
assert quests.update_quests(player, "talk_npc", "archivist_voss") == []
assert quests.start_quest(player, "mq_archivist_01") == []
assert quests.start_quest(player, "not_a_quest") == []

print("== story queue ==")
quests.queue_story(player, "archivist_intro")
quests.queue_story(player, "archivist_intro")   # dedupe
assert quests.pop_pending_story(player) == "archivist_intro"
assert quests.pop_pending_story(player) is None

print("\nJournal entry shown to the player:")
print("  status:", q["status"], "| day:", q["day"])
for o in q["objectives"]:
    print("   ", "x" if o["done"] else " ", o["label"])
print("  gold:", player["gold"],
      "| resonance tier:", quests.get_resonance_tier(player),
      f"({quests.get_player_grade(player)['name']})")

# ── Phase 2: tutorial allowance, story delivery, Star Tower ──────────────────
print("\n== Phase 2: tutorial field allowance ==")
from facilities.tutorial import _grant_field_allowance
p_tutorial = build_character("1", "1", ATTRS, "Diag2", 2)
_grant_field_allowance(p_tutorial)
assert p_tutorial["gold"] == 300, p_tutorial["gold"]
_grant_field_allowance(p_tutorial)          # idempotent
assert p_tutorial["gold"] == 300

# Never write a real savefile during the smoke test.
import save_load
save_load.save_game = lambda *args, **kwargs: print("    [stub] save_game")

print("== Phase 2: archivist intro (story screen body) ==")
from facilities.archivist_intro import archivist_intro
p_story = build_character("1", "1", ATTRS, "Diag3", 3)
archivist_intro(p_story)
assert p_story["quests"]["flags"].get("intro_seen")
assert quests.quest_state(p_story, "mq_archivist_01") == "active"

print("== Phase 2: star tower audience ==")
p_story["location"] = "skylume"
from facilities.star_tower import star_tower_service
star_tower_service(p_story, "skylume")
assert quests.quest_state(p_story, "mq_archivist_01") == "completed"
assert p_story["quests"]["flags"].get("met_voss")
assert p_story["quests"]["flags"].get("stellar_field_kit")
kit = next((i for i in p_story["inventory"] if i.get("id") == "stellar_field_kit"), None)
assert kit is not None, "audience should grant the Stellar Field Kit"
assert kit.get("capture_net") and kit.get("guaranteed_capture")
assert kit.get("capture_level_cap") == 8
assert quests.quest_state(p_story, "mq_archivist_02") == "active"
from facilities.star_tower import _field_kit_retired
assert not _field_kit_retired(p_story), "MQ2 is still active — kit is still issued"

orb = next((i for i in p_story["inventory"] if i.get("id") == "resonance_orb"), None)
assert orb is not None, "audience should grant the resonance orb"
assert orb["name"] == "Shattered Orb", orb["name"]
assert orb["rarity"] == "common", orb["rarity"]
assert orb["resonance_meter"].startswith("✦ ·"), orb["resonance_meter"]
print("== Phase 2: field study state checks ==")
p_story["houses"] = {"solmere": {"level": 1, "storage": [],
                                 "monster_girls": [{"key": "goblin_girl",
                                                    "name": "Goblin Girl"}]}}
msgs = quests.update_quests(p_story)        # sync pass resolves both stages
assert quests.quest_state(p_story, "mq_archivist_02") == "completed"
assert quests.get_resonance_tier(p_story) == 1
assert quests.get_player_grade(p_story)["name"] == "Pitch"
orb = next(i for i in p_story["inventory"] if i.get("id") == "resonance_orb")
assert orb["name"] == "Cracked Orb", orb["name"]        # tier 1 -> cracked
assert orb["resonance_meter"] == "✦ ✦ · · · ·", orb["resonance_meter"]
assert "Grade: Pitch" in orb["description"], orb["description"]
print("   sync messages:", "; ".join(msgs) if msgs else "(none)")

print("== Phase 2: field kit retired after Study One ==")
from facilities.star_tower import _give_field_kit
assert _field_kit_retired(p_story), "MQ2 completed — kit must be retired"
inventory_before = len(p_story["inventory"])
refusal = _give_field_kit(p_story)
assert len(p_story["inventory"]) == inventory_before, refusal
assert not any("received" in line or "reissued" in line for line in refusal), refusal
print("  ", refusal[0])

print("== Phase 2: archive menu entry (no crash) ==")
star_tower_service(p_story, "skylume")
print("   ...menu path ok")

# ── Phase 3: Command Resonance caps + roster backfill ────────────────────────
print("\n== Phase 3: party capacity by grade ==")
import combat.ally as ca
caps = [ca.get_party_capacity({"quests": {"resonance_tier": t}}) for t in range(6)]
print("   caps by tier (front allies, bench):", caps)
assert caps == [(1, 0), (2, 0), (2, 1), (2, 2), (3, 2), (3, 4)]

print("== Phase 3: front/bench slicing ==")
p_slice = build_character("1", "1", ATTRS, "Diag4", 4)
p_slice["quests"]["resonance_tier"] = 3          # Cadence: 2 front / 2 bench
p_slice["allies"] = [
    {"key": f"test_{i}", "name": f"Ally {i}", "current_hp": 10, "max_hp": 10}
    for i in range(5)
]
ca.ensure_party_order(p_slice)
assert [a["name"] for a in ca.get_active_allies(p_slice)] == ["Ally 0", "Ally 1"]
assert [a["name"] for a in ca.get_reserve_allies(p_slice)] == ["Ally 2", "Ally 3"]
assert len(ca.get_all_reserve_allies_including_defeated(p_slice)) == 2
p_slice["quests"]["resonance_tier"] = 5          # Crescendo restores old caps
assert len(ca.get_active_allies(p_slice)) == 3
assert len(ca.get_reserve_allies(p_slice)) == 2  # only 5 allies owned
print("   slicing ok")

print("== Phase 3: roster backfill ==")
from resources.enemies import ENEMIES
mg_keys = [k for k, v in ENEMIES.items()
           if v.get("monster_girl") and v.get("race") and not v.get("_heroine")]
by_race = {}
for k in mg_keys:
    by_race.setdefault(ENEMIES[k]["race"], k)
cover = list(by_race.values())                  # one girl per race
assert len(cover) >= 5, f"expected 5+ monster-girl races, got {len(cover)}"

p_back = build_character("1", "1", ATTRS, "Diag5", 5)
assert quests.compute_roster_tier(p_back) == 0
p_back["houses"] = {"solmere": {"level": 1, "storage": [],
                                 "monster_girls": [{"key": cover[0], "name": "G0"}]}}
assert quests.compute_roster_tier(p_back) == 1
p_back["allies"] = [{"key": cover[0], "name": "G0"}]
assert quests.compute_roster_tier(p_back) == 2
p_back["allies"] = [{"key": cover[i], "name": f"G{i}"} for i in range(3)]
assert quests.compute_roster_tier(p_back) == 3
p_back["houses"]["solmere"]["monster_girls"] = [{"key": k} for k in cover[:6]]
assert quests.compute_roster_tier(p_back) == 4
extras = [k for k in mg_keys if k not in cover][:5]
p_back["houses"]["solmere"]["monster_girls"] = [{"key": k} for k in cover[:5] + extras]
p_back["married_girls"] = ["G0"]
assert quests.compute_roster_tier(p_back) == 5

assert quests.get_resonance_tier(p_back) == 0
msgs = quests.update_quests(p_back)
assert quests.get_resonance_tier(p_back) == 5
assert any("Crescendo" in m for m in msgs), msgs
print("   backfill ok —", "; ".join(msgs))

# ── Phase 3b: full quest chain (MQ3-MQ6) + catch-up for old saves ────────────
print("\n== Phase 3b: chain progresses for a fresh household ==")
# p_story completed MQ2 earlier; the follow-up (MQ3) must now start by itself.
quests.update_quests(p_story)
assert quests.quest_state(p_story, "mq_archivist_03") == "active"
assert quests.quest_state(p_story, "mq_archivist_04") is None

p_story["allies"] = [{"key": cover[0], "name": "G0"}]
quests.update_quests(p_story, "recruit_ally", "any")
assert quests.quest_state(p_story, "mq_archivist_03") == "completed"
assert quests.quest_state(p_story, "mq_archivist_04") == "active"   # wants 3
p_story["allies"] = [{"key": cover[i], "name": f"G{i}"} for i in range(3)]
quests.update_quests(p_story, "recruit_ally", "any")
assert quests.quest_state(p_story, "mq_archivist_04") == "completed"
assert quests.quest_state(p_story, "mq_archivist_05") == "active"   # wants 6 owned
orb = next(i for i in p_story["inventory"] if i.get("id") == "resonance_orb")
assert orb["name"] == "Whole Orb", orb["name"]           # tier 3 -> whole
assert orb["rarity"] == "epic", orb["rarity"]
print("   recruit milestones ok")

print("== Phase 3b: old save catch-up cascades to the frontier ==")
p_chain = build_character("1", "1", ATTRS, "Diag6", 6)
p_chain["quests"]["completed"] = ["mq_archivist_01", "mq_archivist_02"]
p_chain["quests"]["flags"]["met_voss"] = True
p_chain["houses"] = {"solmere": {"level": 1, "storage": [],
                                 "monster_girls": [{"key": k} for k in cover[:5] + extras]}}
p_chain["allies"] = [{"key": cover[i], "name": f"G{i}"} for i in range(3)]
p_chain["married_girls"] = ["G0"]
msgs = quests.update_quests(p_chain)
for qid in ("mq_archivist_03", "mq_archivist_04",
            "mq_archivist_05", "mq_archivist_06"):
    assert quests.quest_state(p_chain, qid) == "completed", \
        (qid, quests.quest_state(p_chain, qid))
assert quests.get_resonance_tier(p_chain) == 5
assert quests.update_quests(p_chain) == [], "chain sync must be idempotent"
orb = next(i for i in p_chain["inventory"] if i.get("id") == "resonance_orb")
assert orb["name"] == "Resonant Orb", orb["name"]       # backfilled at tier 5
assert orb["rarity"] == "mythic", orb["rarity"]
assert orb["resonance_meter"] == "✦ ✦ ✦ ✦ ✦ ✦", orb["resonance_meter"]
print("   orb backfill ok —", orb["name"])
jids = [e["id"] for e in p_chain["journal"]["main_quests"]]
assert jids.count("mq_archivist_06") == 1
print("   cascade ok —", "; ".join(msgs[:4]), "...")

# ── Key item naming: no rarity prefixes (2026-09-28) ─────────────────────────
print("\n== Key item naming (no rarity prefixes) ==")
from resources.items import build_item as _build_item
assert _build_item("glass_anchor")["name"] == "Glass Anchor", _build_item("glass_anchor")["name"]
assert _build_item("wolfs_tooth")["name"] == "Wolf's Tooth"
p_norm = build_character("1", "1", ATTRS, "Diag7", 2)
legacy_anchor = {"id": "glass_anchor", "name": "Legendary Glass Anchor",
                 "type": "key_item", "rarity": "legendary", "count": 1}
p_norm["inventory"].append(legacy_anchor)
from character import ensure_player_fields
ensure_player_fields(p_norm)
assert legacy_anchor["name"] == "Glass Anchor", legacy_anchor["name"]
_orb = next((i for i in p_norm["inventory"] if i.get("id") == "resonance_orb"), None)
assert _orb is None, "fresh save without met_voss should not have the orb"
print("   naming ok — build + migration strips prefixes")

# ── Wonderland side-quest chain ──────────────────────────────────────────────
print("\n== Wonderland: way-in guide ==")
p_guide = build_character("1", "1", ATTRS, "Diag10", 10)
assert quests.quest_state(p_guide, "sq_wonderland_00") is None
assert quests.update_quests(p_guide) == [], "guide must wait for a relevant milestone"

p_guide["city_floors"] = {"solmere": {"floor": 1, "max_floor": 20}}
quests.update_quests(p_guide)
assert quests.quest_state(p_guide, "sq_wonderland_00") == "active"
guide = next(e for e in p_guide["journal"]["side_quests"]
             if e["id"] == "sq_wonderland_00")
assert [o["done"] for o in guide["objectives"]] == [False, False, False]

# A second city in the same biome must not satisfy the gate.
p_guide["city_floors"]["thornwall"] = {"floor": 1, "max_floor": 20}
quests.update_quests(p_guide)
guide = next(e for e in p_guide["journal"]["side_quests"]
             if e["id"] == "sq_wonderland_00")
assert guide["objectives"][0]["done"] is False

p_guide["city_floors"]["stormhold"] = {"floor": 1, "max_floor": 20}
p_guide["inventory"].append({
    "id": "looking_glass_shard", "name": "Looking Glass Shard",
    "type": "key_item", "rarity": "rare", "count": 1,
})
quests.update_quests(p_guide)
guide = next(e for e in p_guide["journal"]["side_quests"]
             if e["id"] == "sq_wonderland_00")
assert [o["done"] for o in guide["objectives"]] == [True, True, False]

p_guide["wonderland_visited"] = True
p_guide["wonderland_active"] = True
p_guide["city_floors"]["wonderland"] = {"floor": 1, "max_floor": 1}
quests.update_quests(p_guide)
assert quests.quest_state(p_guide, "sq_wonderland_00") == "completed"
assert quests.quest_state(p_guide, "sq_wonderland_01") == "active"
print("   two-biome gate / shard / book objectives resolve")

print("\n== Wonderland: entry chain + heroine arcs ==")
p_wl = build_character("1", "1", ATTRS, "Diag8", 8)
assert quests.quest_state(p_wl, "sq_wonderland_01") is None
assert quests.update_quests(p_wl) == [], "Wonderland quests must wait for the book"

# Unlocking (the Veilholt event) shows the quest, but does not check off the
# "enter the book" objective — only an actual visit does.
p_wl["wonderland_unlocked"] = True
quests.update_quests(p_wl)
assert quests.quest_state(p_wl, "sq_wonderland_01") == "active"
intro_j = next(e for e in p_wl["journal"]["side_quests"]
               if e["id"] == "sq_wonderland_01")
assert [o["done"] for o in intro_j["objectives"]] == [False, False, False]

p_wl["wonderland_visited"] = True
p_wl["wonderland_active"] = True
p_wl["city_floors"] = {"wonderland": {"floor": 11, "max_floor": 11}}
p_wl["wl_boss_defeated_queen_of_hearts"] = True
scenes = wonderland_guests.on_inn_enter(p_wl)
assert "three_guests" in scenes, scenes
assert p_wl["wl_hatter_three_guests_seen"]
assert wonderland_guests.get_guest_state(p_wl, "red_hood") == "invited"
msgs = quests.update_quests(p_wl)
print("   entry:", "; ".join(msgs[:4]))
assert quests.quest_state(p_wl, "sq_wonderland_01") == "completed"
assert quests.quest_state(p_wl, "sq_wonderland_02") == "active"
assert "The Storybook Road" in [e["name"] for e in p_wl["journal"]["side_quests"]]

# Meeting the heroines starts their arcs; a temp Red Hood also checks off
# "recruited", while Alice (intro) and Dorothy (declined) only check "met".
p_wl["wl_alice_state"] = "intro"
p_wl["wl_redhood_state"] = "temp"
p_wl["wl_dorothy_state"] = "declined"
wonderland_guests.set_guest_state(p_wl, "alice", "invited")
wonderland_guests.set_guest_state(p_wl, "red_hood", "accepted")
wonderland_guests.set_guest_state(p_wl, "dorothy", "invited")
msgs = quests.update_quests(p_wl)
assert quests.quest_state(p_wl, "sq_wonderland_alice") == "active"
assert quests.quest_state(p_wl, "sq_wonderland_red_hood") == "active"
assert quests.quest_state(p_wl, "sq_wonderland_dorothy") == "active"

alice_j = next(e for e in p_wl["journal"]["side_quests"]
               if e["id"] == "sq_wonderland_alice")
red_j = next(e for e in p_wl["journal"]["side_quests"]
             if e["id"] == "sq_wonderland_red_hood")
assert [o["done"] for o in alice_j["objectives"]] == [True, False, False, False]
assert [o["done"] for o in red_j["objectives"]] == [True, True, False, False]

# Floor progress + boss flags resolve the road and the arcs.
p_wl["city_floors"]["wonderland"]["max_floor"] = 41
p_wl["wl_boss_defeated_big_bad_wolf"] = True
p_wl["wl_boss_defeated_wicked_witch"] = True
p_wl["wl_boss_defeated_jabberwock"] = True
p_wl["wonderland_heroine_redhood_permanent"] = True
p_wl["wl_redhood_state"] = "permanent"
wonderland_guests.set_guest_state(p_wl, "red_hood", "resolved")
msgs = quests.update_quests(p_wl)
assert quests.quest_state(p_wl, "sq_wonderland_02") == "completed"
assert quests.quest_state(p_wl, "sq_wonderland_03") == "active"
assert quests.quest_state(p_wl, "sq_wonderland_red_hood") == "completed"
assert quests.quest_state(p_wl, "sq_wonderland_alice") == "active"
assert quests.quest_state(p_wl, "sq_wonderland_dorothy") == "active"

# The finale and the remaining heroine arcs close together.
p_wl["city_floors"]["wonderland"]["max_floor"] = 51
p_wl["wl_boss_defeated_mary_sue"] = True
p_wl["wonderland_heroine_alice_permanent"] = True
p_wl["wl_alice_state"] = "permanent"
p_wl["wonderland_heroine_dorothy_permanent"] = True
p_wl["wl_dorothy_state"] = "permanent"
wonderland_guests.set_guest_state(p_wl, "alice", "resolved")
wonderland_guests.set_guest_state(p_wl, "dorothy", "resolved")
quests.update_quests(p_wl)
for qid in ("sq_wonderland_01", "sq_wonderland_02", "sq_wonderland_03",
            "sq_wonderland_alice", "sq_wonderland_red_hood",
            "sq_wonderland_dorothy"):
    assert quests.quest_state(p_wl, qid) == "completed", \
        (qid, quests.quest_state(p_wl, qid))
assert quests.update_quests(p_wl) == [], "Wonderland quest sync must be idempotent"
print("   chain + heroine arcs ok")

print("== Wonderland: old-save catch-up (flags missing) ==")
p_old = build_character("1", "1", ATTRS, "Diag9", 9)
p_old["wonderland_unlocked"] = True
p_old["city_floors"] = {"wonderland": {"floor": 41, "max_floor": 41}}
# No wl_boss_defeated_* flags at all — the floor fallback must carry it.
quests.update_quests(p_old)
assert quests.quest_state(p_old, "sq_wonderland_01") == "completed"
assert quests.quest_state(p_old, "sq_wonderland_02") == "completed"
assert quests.quest_state(p_old, "sq_wonderland_03") == "active"
finale = next(e for e in p_old["journal"]["side_quests"]
              if e["id"] == "sq_wonderland_03")
assert [o["done"] for o in finale["objectives"]] == [True, True, True, False]
print("   floor fallback ok")

print("\nAll quest-core smoke checks passed.")
