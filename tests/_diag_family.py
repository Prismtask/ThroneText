"""Diagnostic: Family system Phase 1.

Checks the content switch, state migration, affection ladder v2 caps,
sleep-sharing eligibility, season/moon initiation chance, pregnancy period
tracking, conception helpers, growth stages, round-trip fields, and the
day-tick scaffolding — all headless.

Run:  .venv\\Scripts\\python.exe tests\\_diag_family.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import facilities.house  # noqa: F401  (circular-import smoke test)
import facilities.dispatch as D
import family as F
import quests
from combat.ally import (_ally_to_house_record, recruit_ally_from_house,
                         ally_max_hp, create_ally_from_girl)
from combat.elemental import compute_ally_elemental
from combat.stats import get_dodge_chance, get_raw_critical_chance
from combat.status_effects import tick_player_buffs
from combat.combat_ui import _get_entity_buff_tags
from facilities.sleep_sharing import apply_action, new_state
from resources.enemies import ENEMIES, ENEMY_RACES
from resources.family_scenes import (ACTION_LINES, ACTION_PROMPTS,
                                     ENDING_LINES, GIRL_ACTION_LINES,
                                     CHILD_RACE_GIFT, CHILD_RACE_TALK,
                                     WRITTEN_ACTION_LINES, WRITTEN_ENDING_LINES,
                                     child_gift_lines, child_talk_lines,
                                     written_action_lines_for,
                                     written_ending_lines_for)

FAILED = []


class FixedRNG:
    """Deterministic RNG for the mini-game/conception checks."""

    def __init__(self, roll=0.99, randint_value=0):
        self.roll = roll
        self.randint_value = randint_value

    def random(self):
        return self.roll

    def randint(self, a, b):
        return max(a, min(b, self.randint_value))

    def randrange(self, n):
        return 0

    def choice(self, seq):
        return seq[0]


def check(label, cond):
    if cond:
        print(f"[OK] {label}")
    else:
        FAILED.append(label)
        print(f"[FAIL] {label}")


def make_girl(name="Mira", **kw):
    girl = {
        "key": f"test_{name.lower()}",
        "name": name,
        "level": 10,
        "affection": 30,
        "affection_cap": 100,
        "engaged": False,
        "married": False,
        "current_hp": 40,
        "max_hp": 40,
        "stress": 0,
        "attributes": {"Strength": 8, "Constitution": 8, "Dexterity": 8,
                       "Wisdom": 8, "Learning": 8, "Charisma": 8},
        "level_hp_bonus": 0,
        "equipped": {},
    }
    girl.update(kw)
    return girl


def make_player(**kw):
    house = {"level": 3, "monster_girls": [], "storage": []}
    player = {
        "day": 1,
        "origin_city": "solmere",
        "houses": {"solmere": house},
        "allies": [],
        "wonderland_benched_allies": [],
        "children": [],
        "daily_effects": {},
        "family_enabled": True,
        "inventory": [],
        "equipped": {},
    }
    player.update(kw)
    return player


# 1. Content switch -------------------------------------------------------
print("\n-- content switch --")
check("default fade-to-black", F.get_content_level({}) == "fade-to-black")
check("explicit off", F.get_content_level({"content_level": "off"}) == "off")
check("explicit written", F.get_content_level({"content_level": "written"}) == "written")
check("invalid falls back", F.get_content_level({"content_level": "bogus"}) == "fade-to-black")
check("off disables intimacy", not F.intimacy_enabled({"content_level": "off"}))
check("fade-to-black enables intimacy", F.intimacy_enabled({"content_level": "fade-to-black"}))
check("written enables intimacy", F.intimacy_enabled({"content_level": "written"}))

# 2. State + cap migration ------------------------------------------------
print("\n-- state + affection ladder --")
p = make_player()
p["allies"] = [make_girl("Active", affection_cap=100)]
p["houses"]["solmere"]["monster_girls"] = [
    make_girl("Engaged", engaged=True, affection_cap=200),
    make_girl("Married", married=True, affection_cap=100),
    make_girl("HighCap", affection_cap=250),
]
p["wonderland_benched_allies"] = [make_girl("Benched", affection_cap=100)]
F.ensure_family_fields(p)

check("children list seeded", p.get("children") == [])
check("active base cap -> 200", p["allies"][0]["affection_cap"] == 200)
check("engaged cap -> 300", p["houses"]["solmere"]["monster_girls"][0]["affection_cap"] == 300)
check("married cap -> 300", p["houses"]["solmere"]["monster_girls"][1]["affection_cap"] == 300)
check("higher cap not lowered", p["houses"]["solmere"]["monster_girls"][2]["affection_cap"] == 250)
check("benched cap -> 200", p["wonderland_benched_allies"][0]["affection_cap"] == 200)
check("pregnancy fields seeded", p["allies"][0]["pregnant"] is False
      and p["allies"][0]["due_day"] == 0
      and p["allies"][0]["pregnancy_pity"] == 0)
check("family flags seeded",
      p["houses"]["solmere"]["monster_girls"][0]["is_trueborn"] is False
      and p["houses"]["solmere"]["monster_girls"][0]["no_romance"] is False)

p["houses"]["solmere"]["monster_girls"].append(
    make_girl("Trueborn", is_trueborn=True, no_romance=True, affection_cap=100))
F.migrate_affection_caps(p)
check("true-born child keeps bond cap 100",
      p["houses"]["solmere"]["monster_girls"][-1]["affection_cap"] == 100)

# 3. Sleep-sharing eligibility -------------------------------------------
print("\n-- eligibility --")
S = {"content_level": "fade-to-black"}
g = make_girl("Eligible", affection=140)
check("player 139 blocked", not F.share_night_eligibility(
    make_player(), make_girl("Low", affection=139), True, S)[0])
check("player 140 allowed", F.share_night_eligibility(
    make_player(), make_girl("OK", affection=140), True, S)[0])
check("ally 159 blocked", not F.share_night_eligibility(
    make_player(), make_girl("Low2", affection=159), False, S)[0])
check("ally 160 allowed", F.share_night_eligibility(
    make_player(), make_girl("OK2", affection=160), False, S)[0])
check("pregnant blocked", not F.share_night_eligibility(
    make_player(), make_girl("Preg", affection=200, pregnant=True), True, S)[0])
check("no_romance blocked", not F.share_night_eligibility(
    make_player(), make_girl("Child", affection=200, no_romance=True), True, S)[0])
check("dispatch blocked", not F.share_night_eligibility(
    make_player(), make_girl("Away", affection=200, dispatch_mission={"id": "x"}), True, S)[0])
check("injured blocked", not F.share_night_eligibility(
    {"day": 3}, make_girl("Hurt", affection=200, injured_until=5), True, S)[0])
check("post-birth recovery blocked", not F.share_night_eligibility(
    {"day": 10}, make_girl("Recovering", affection=200, recovery_until=12), True, S)[0])
check("content off blocks", not F.share_night_eligibility(
    make_player(), g, True, {"content_level": "off"})[0])

# 4. Season / moon initiation chance --------------------------------------
print("\n-- season / moon chance --")
check("spring + full moon = 14%", abs(F.initiation_chance(
    {"day": 15, "daily_effects": {"full_moon": True}}, g) - 0.14) < 1e-9)
check("spring new moon = 11%", abs(F.initiation_chance(
    {"day": 1, "daily_effects": {}}, g) - 0.11) < 1e-9)
check("summer + full moon = 12%", abs(F.initiation_chance(
    {"day": 45, "daily_effects": {"full_moon": True}}, g) - 0.12) < 1e-9)
check("autumn + full moon = 11%", abs(F.initiation_chance(
    {"day": 75, "daily_effects": {"full_moon": True}}, g) - 0.11) < 1e-9)
check("winter + full moon = 13%", abs(F.initiation_chance(
    {"day": 105, "daily_effects": {"full_moon": True}}, g) - 0.13) < 1e-9)
check("monster girl season +3%", abs(F.initiation_chance(
    {"day": 16, "daily_effects": {"capture_bonus": 15}}, g) - 0.12) < 1e-9)
check("wary prey -3%", abs(F.initiation_chance(
    {"day": 16, "daily_effects": {"capture_bonus": -10}}, g) - 0.06) < 1e-9)
check("blessed wind +2%", abs(F.initiation_chance(
    {"day": 16, "daily_effects": {"all_stats": 1}}, g) - 0.11) < 1e-9)
check("chance clamps at 25%", abs(F.initiation_chance(
    {"day": 15, "daily_effects": {"full_moon": True, "capture_bonus": 15,
                                  "all_stats": 1}},
    make_girl("Married", affection=200, married=True)) - 0.25) < 1e-9)
check("content off = 0%", F.initiation_chance(
    {"day": 15, "daily_effects": {}}, g, settings={"content_level": "off"}) == 0.0)

# 5. Pregnancy periods ----------------------------------------------------
print("\n-- pregnancy periods --")
pg = make_girl("Pregnant")
F.start_pregnancy(pg, 10)
check("due day 40", pg["due_day"] == 40)
check("period 1 at conception", F.pregnancy_period(pg, 10) == 1)
check("period 1 at day 19", F.pregnancy_period(pg, 19) == 1)
check("period 2 at day 20", F.pregnancy_period(pg, 20) == 2)
check("period 3 at day 30", F.pregnancy_period(pg, 30) == 3)
check("period 3 while due", F.pregnancy_period(pg, 40) == 3)
check("not due at 39", not F.pregnancy_due(pg, 39))
check("due at 40", F.pregnancy_due(pg, 40))
F.finish_pregnancy(pg, 40)
check("pregnancy cleared", pg["pregnant"] is False and pg["due_day"] == 0)
check("recovery 7 days", pg["recovery_until"] == 47)
check("conception cooldown 30 days", pg["next_conception_day"] == 70)
check("cooldown blocks day 69", not F.can_conceive(pg, 69))
check("cooldown opens day 70", F.can_conceive(pg, 70))

# 6. Conception helpers ---------------------------------------------------
print("\n-- conception --")
cg = make_girl("Conceive")
check("family off = 0", F.conception_chance({"family_enabled": False}, cg, "together") == 0.0)
check("together base = 20%", abs(F.conception_chance({"family_enabled": True}, cg, "together") - 0.20) < 1e-9)
check("warm base = 16%", abs(F.conception_chance({"family_enabled": True}, cg, "warm") - 0.16) < 1e-9)
check("quiet base = 12%", abs(F.conception_chance({"family_enabled": True}, cg, "quiet") - 0.12) < 1e-9)
check("rest = no roll", F.conception_chance({"family_enabled": True}, cg, "rest") == 0.0)
check("married together = 30%", abs(F.conception_chance(
    {"family_enabled": True}, make_girl("Wife", married=True), "together") - 0.30) < 1e-9)
cg["pregnancy_pity"] = 7
check("pity guarantee at 8th attempt", F.conception_chance({"family_enabled": True}, cg, "together") == 1.0)
cg["pregnancy_pity"] = 0
F.record_conception_attempt(cg, False)
check("attempt increments pity", cg["pregnancy_pity"] == 1)
F.record_conception_attempt(cg, True)
check("conception resets pity", cg["pregnancy_pity"] == 0)

# 7. Growth stages --------------------------------------------------------
print("\n-- growth --")
child = {"born_day": 1, "stage": "infant"}
check("infant at day 15", F.growth_stage_for_child(child, 15) == "infant")
check("child at day 16", F.growth_stage_for_child(child, 16) == "child")
check("child at day 40", F.growth_stage_for_child(child, 40) == "child")
check("adult at day 41", F.growth_stage_for_child(child, 41) == "adult")
check("prime at day 61", F.is_prime(child, 61))
check("not prime at day 60", not F.is_prime(child, 60))
check("infant remaining", F.growth_days_remaining(child, 1) == 15)
check("child remaining", F.growth_days_remaining(child, 16) == 25)
check("adult remaining 0", F.growth_days_remaining(child, 41) == 0)
check("prime remaining", F.growth_days_to_prime(child, 41) == 20)

# 8. Round-trip fields ----------------------------------------------------
print("\n-- round-trip --")
ally = make_girl("Roundtrip", pregnant=True, conceived_day=10, due_day=40,
                 next_conception_day=70, pregnancy_pity=3,
                 is_trueborn=True, no_romance=True, stage="adult", prime=True,
                 mother_key="goblin_girl")
record = _ally_to_house_record(ally, {})
check("record keeps pregnancy", record.get("pregnant") is True
      and record.get("conceived_day") == 10
      and record.get("due_day") == 40)
check("record keeps cooldown/pity", record.get("next_conception_day") == 70
      and record.get("pregnancy_pity") == 3)
check("record keeps true-born flags", record.get("is_trueborn") is True
      and record.get("no_romance") is True)
check("record keeps stage/prime", record.get("stage") == "adult"
      and record.get("prime") is True)
check("record keeps mother_key", record.get("mother_key") == "goblin_girl")

# 9. Day-tick scaffolding -------------------------------------------------
print("\n-- day tick --")
p = make_player(day=31)
p["allies"] = [make_girl("Expecting", pregnant=True, conceived_day=10, due_day=40)]
p["children"] = [{"born_day": 1, "stage": "infant"}]
F.family_tick(p, 30)
check("third-period girl left party", p["allies"] == [])
check("girl moved to house", len(p["houses"]["solmere"]["monster_girls"]) == 1)
check("house record still pregnant",
      p["houses"]["solmere"]["monster_girls"][0].get("pregnant") is True)
check("child stage updated", p["children"][0]["stage"] == "child")

# 10. Shared Night — Attunement ------------------------------------------
print("\n-- shared night (attunement) --")
state = new_state(("tender", "shy"), FixedRNG(roll=0.99),
                  moods=["tender", "playful", "shy"])
check("attunement starts at 0", state["attunement"] == 0 and state["round"] == 1)
check("mood shown", state["mood"] == "tender")

state = new_state(("tender", "shy"), moods=["tender", "playful", "shy"])
r = apply_action(state, "tender", FixedRNG(roll=0.99))
check("exact match +2", r["score"] == 2 and state["attunement"] == 2
      and state["mood"] == "playful")

r = apply_action(state, "shy", FixedRNG(roll=0.99))
check("opposite energy +0", r["score"] == 0 and state["attunement"] == 2
      and state["mood"] == "shy")

r = apply_action(state, "bold", FixedRNG(roll=0.99))
check("quiet ending", state["done"] and state["ending"] == "quiet")

state = new_state(("tender", "playful"), moods=["playful", "playful", "playful"])
r = apply_action(state, "bold", FixedRNG(roll=0.99))
check("same energy +1", r["score"] == 1 and state["attunement"] == 1)

state = new_state(("tender",), moods=["tender", "tender", "tender"])
for _ in range(3):
    apply_action(state, "tender")
check("perfect night => together", state["ending"] == "together"
      and state["attunement"] == 6)

state = new_state(("tender",), moods=["tender", "playful", "shy"])
apply_action(state, "tender")  # +2
apply_action(state, "bold")    # +1 (playful family)
apply_action(state, "playful") # +0 (shy family)
check("mixed night => warm", state["ending"] == "warm" and state["attunement"] == 3)

state = new_state(("tender",), moods=["tender", "playful", "shy"])
apply_action(state, "end")
check("end => rest", state["done"] and state["ending"] == "rest")

# 11. Sleep outcome / conception / buffs ---------------------------------
print("\n-- sleep outcome --")
p = make_player(day=10)
p["family_enabled"] = True
g = make_girl("Night", affection=200, affection_cap=300, stress=50)
out = F.apply_sleep_outcome(p, g, "together", rng=FixedRNG(roll=0.0))
check("sleep affection +4", g["affection"] == 204)
check("sleep stress -20", g["stress"] == 30)
check("shared_night buff", any(b.get("type") == "shared_night" for b in p["active_buffs"]))
check("beloved buff", any(b.get("type") == "beloved" for b in g["active_buffs"]))
check("conception on together", out["conceived"] and g["pregnant"])
check("pregnancy due 30 days", g["due_day"] == 40)
check("family journal entry", any(e.get("tag") == "[FAMILY]" for e in p["journal"]["events"]))

g_warm = make_girl("Warm", affection=200, affection_cap=300, stress=50)
out_warm = F.apply_sleep_outcome(make_player(day=10), g_warm, "warm", rng=FixedRNG(roll=0.99))
check("warm affection +3", g_warm["affection"] == 203 and g_warm["stress"] == 35)
check("warm no conception on miss", not out_warm["conceived"])

g_quiet = make_girl("Quiet", affection=200, affection_cap=300, stress=50)
out_quiet = F.apply_sleep_outcome(make_player(day=10), g_quiet, "quiet", rng=FixedRNG(roll=0.0))
check("quiet affection +1", g_quiet["affection"] == 201 and g_quiet["stress"] == 40)
check("quiet conception at base", out_quiet["conceived"])
check("quiet no beloved buff", not any(b.get("type") == "beloved"
                                      for b in g_quiet.get("active_buffs", [])))

p2 = make_player(day=10)
p2["family_enabled"] = False
g2 = make_girl("NoFamily", affection=200, affection_cap=300)
out2 = F.apply_sleep_outcome(p2, g2, "together", rng=FixedRNG(roll=0.0))
check("family off skips conception", not out2["conceived"] and not g2.get("pregnant"))

g3 = make_girl("RestOnly", affection=200, affection_cap=300)
out3 = F.apply_sleep_outcome(make_player(day=10), g3, "rest", rng=FixedRNG(roll=0.0))
check("rest skips conception", not out3["conceived"])

actor = {"active_buffs": [{"type": "well_rested", "stat": "all", "value": 2, "remaining": 3}]}
F.grant_sleep_buff(actor, "shared_night", 1, 2)
check("weaker shared buff merges", actor["active_buffs"][0]["type"] == "well_rested"
      and actor["active_buffs"][0]["value"] == 2)
check("merged shared marker", actor["active_buffs"][0].get("shared_night") is True)
check("shared night HUD label", "SHR" in _get_entity_buff_tags(actor))
F.grant_sleep_buff(actor, "shared_night", 3, 2)
check("stronger shared buff replaces", actor["active_buffs"][0]["type"] == "shared_night"
      and actor["active_buffs"][0]["value"] == 3 and len(actor["active_buffs"]) == 1)

check("beloved multiplier on", abs(F.beloved_multiplier(
    make_girl("Beloved", beloved_until_day=11), 11) - 1.1) < 1e-9)
check("beloved multiplier expires", F.beloved_multiplier(
    make_girl("Beloved2", beloved_until_day=11), 12) == 1.0)

# Room-based sleep buffs: stat application + combat-round immunity.
from combat.stats import get_effective_attribute
from combat.ally import get_ally_effective_attribute

p = make_player()
p["attributes"] = {a: 10 for a in F.ATTRIBUTES}
p["active_buffs"] = [{"type": "shared_night", "stat": "all",
                       "value": 1, "remaining": 2, "_tick_grace": True}]
check("shared_night applies to MC stats",
      get_effective_attribute(p, "Strength") == 11)
tick_player_buffs(p)
check("shared_night survives combat tick",
      p["active_buffs"] and p["active_buffs"][0]["remaining"] == 2)

beloved = make_girl("BelovedBuff", is_ally=True)
beloved["active_buffs"] = [{"type": "beloved", "stat": "Strength",
                            "value": 2, "remaining": 2, "_tick_grace": True}]
check("beloved applies to ally stats",
      get_ally_effective_attribute(beloved, "Strength") == 10)
tick_player_buffs(beloved)
check("beloved survives combat tick",
      beloved["active_buffs"] and beloved["active_buffs"][0]["remaining"] == 2)
check("beloved HUD label", "BLV" in _get_entity_buff_tags(beloved))
plain_rest = make_girl("PlainRest", is_ally=True,
                       active_buffs=[{"type": "well_rested", "stat": "all",
                                      "value": 2, "remaining": 2}])
check("plain rest keeps RST", "RST" in _get_entity_buff_tags(plain_rest)
      and "SHR" not in _get_entity_buff_tags(plain_rest))

# 12. Initiation roll ----------------------------------------------------
print("\n-- initiation roll --")
p = make_player(day=15)  # spring + full moon
p["daily_effects"] = {"full_moon": True}
g = make_girl("Eager", affection=200)
p["allies"] = [g]
check("eligible girl initiates", F.roll_sleep_initiation(
    p, p["houses"]["solmere"], rng=FixedRNG(roll=0.0)) is g)
p["allies"] = [make_girl("LowAff", affection=159)]
check("low affection does not initiate", F.roll_sleep_initiation(
    p, p["houses"]["solmere"], rng=FixedRNG(roll=0.0)) is None)

# 13. Birth + naming -----------------------------------------------------
print("\n-- birth --")
p = make_player(day=31)
g = make_girl("Goblin Mother", key="goblin_girl", pregnant=True,
              conceived_day=1, due_day=31)
p["houses"]["solmere"]["monster_girls"] = [g]
F.family_tick(p, 30)
check("birth clears pregnancy", not g["pregnant"])

p_rec = make_player(day=32)
g_rec = make_girl("Recovering", recovery_until=38)
p_rec["houses"]["solmere"]["monster_girls"] = [g_rec]
rec_ally, rec_msg = recruit_ally_from_house(p_rec, g_rec, p_rec["houses"]["solmere"])
check("recovery blocks party recruit", rec_ally is None and "recovering" in rec_msg.lower())
check("mother recovery/cooldown", g["recovery_until"] == 38 and g["next_conception_day"] == 61)
check("child created", len(p["children"]) == 1)
child = p["children"][0]
check("child pending name", child["pending_name"] and child["stage"] == "infant")
check("child inherits innate skills", bool(child["innate_skills"]))
check("child has father legacy", child["legacy"].get("type") is not None)
check("child base attributes", all(child["attributes"].get(a, 0) >= 1 for a in F.ATTRIBUTES))
check("birth queued for scene", len(p["family_births_pending"]) == 1)

check("name child", F.name_child(child, "Nia") and child["name"] == "Nia"
      and not child["pending_name"])

# 14. Adult conversion ---------------------------------------------------
print("\n-- adult conversion --")
p = make_player(day=91)
p["children"] = [{
    "key": "trueborn_goblin_girl_1", "name": "Nia", "mother_key": "goblin_girl",
    "mother_name": "Goblin Mother", "race": "Goblin", "born_day": 1, "stage": "child",
    "affection": 40, "affection_cap": 100,
    "attributes": {a: 8 for a in F.ATTRIBUTES},
    "innate_skills": ["test_skill"], "passive_skill": "test_passive",
    "preferred_tones": ["tender"], "home_city": "solmere",
    "legacy": {"type": "attributes", "count": 2, "value": 1, "chosen": []},
    "is_trueborn": True, "no_romance": True,
}]
F.family_tick(p, 90)
check("child converted to house", len(p["children"]) == 0
      and len(p["houses"]["solmere"]["monster_girls"]) == 1)
rec = p["houses"]["solmere"]["monster_girls"][0]
check("adult true-born flags", rec["is_trueborn"] and rec["no_romance"]
      and rec["affection_cap"] == 100)
check("adult record keeps mother_key", rec.get("mother_key") == "goblin_girl")
check("legacy attributes applied", sum(rec["attributes"][a] for a in rec["father_legacy"]["chosen"]) == 18)
check("house record keeps skills", rec["innate_skills"] == ["test_skill"]
      and rec["passive_skill"] == "test_passive")

p_full = make_player(day=91)
p_full["houses"]["solmere"]["level"] = 1  # cap 2
p_full["houses"]["solmere"]["monster_girls"] = [make_girl("A"), make_girl("B")]
p_full["children"] = [{
    "key": "trueborn_goblin_girl_2", "name": "Waiting", "mother_key": "goblin_girl",
    "mother_name": "Goblin Mother", "race": "Goblin", "born_day": 1, "stage": "child",
    "affection": 30, "affection_cap": 100,
    "attributes": {a: 8 for a in F.ATTRIBUTES},
    "innate_skills": [], "passive_skill": None, "preferred_tones": [],
    "home_city": "solmere", "legacy": {"type": "passive", "passive": "dodge", "value": 0.05},
    "is_trueborn": True, "no_romance": True,
}]
F.family_tick(p_full, 90)
check("house cap keeps adult child waiting", len(p_full["children"]) == 1
      and len(p_full["houses"]["solmere"]["monster_girls"]) == 2)

# 15. Phase 3 — integration gates + Father's Legacy ----------------------
print("\n-- phase 3 gates --")

p = make_player()
child = make_girl("Daughter", key="trueborn_goblin_girl_1", is_trueborn=True,
                 no_romance=False, engaged=True, married=True,
                 affection=250, affection_cap=300)
p["houses"]["solmere"]["monster_girls"] = [child]
p["engaged_girls"] = ["trueborn_goblin_girl_1"]
p["married_girls"] = ["trueborn_goblin_girl_1"]
F.ensure_family_fields(p)
check("true-born enforces no-romance", child["no_romance"] is True)
check("no-romance clears engagement", not child["engaged"] and not child["married"])
check("bond cap clamps to 100", child["affection_cap"] == 100
      and child["affection"] == 100)
check("romance lists cleared", not p["engaged_girls"] and not p["married_girls"])
check("minor helper", F.is_trueborn_minor(child) is False
      and F.is_trueborn_minor(make_girl("Young", is_trueborn=True, stage="child")))

p = make_player(day=10)
house = p["houses"]["solmere"]
preg = make_girl("Preg", pregnant=True)
recovering = make_girl("Recovering", recovery_until=15)
minor = make_girl("Minor", is_trueborn=True, stage="child")
healthy = make_girl("Healthy")
house["monster_girls"] = [preg, recovering, minor, healthy]
eligible = D.eligible_girls(p, house)
check("dispatch only healthy girl", eligible == [healthy])
check("dispatch blocks pregnancy", "expecting" in D.dispatch_block_reason(preg, 10))
check("dispatch blocks recovery", "recovering" in D.dispatch_block_reason(recovering, 10))
check("dispatch blocks minors", "too young" in D.dispatch_block_reason(minor, 10))

p = make_player(day=10)
house = p["houses"]["solmere"]
house["monster_girls"] = [preg]
offer = {"id": "test_offer", "hours": 1, "power": 5, "risk": 1, "stars": 1}
inst, msg = D.create_instance(p, "solmere", house, offer, [preg])
check("launch rejects pregnancy", inst is None and "expecting" in msg)

p = make_player(day=10)
preg = make_girl("PregAscend", level=10, level_cap=10, pregnant=True)
check("ascension blocked while pregnant", not facilities.house._can_ascend_ally(p, preg))
awaken_girl = make_girl("Awaken", key="goblin_girl", level=40, level_cap=40,
                        affection=200, pregnant=True)
ok, reason = facilities.house.can_awaken_girl(awaken_girl, 10)
check("awakening blocked while pregnant", not ok and reason == "expecting")
recovering = make_girl("RecoverAwaken", key="goblin_girl", level=40, level_cap=40,
                       affection=200, recovery_until=15)
ok, reason = facilities.house.can_awaken_girl(recovering, 10)
check("awakening blocked in recovery", not ok and reason == "recovering")

p = make_player(day=10)
house = p["houses"]["solmere"]
child = make_girl("YoungRecruit", key="trueborn_goblin_girl_2", is_trueborn=True,
                  stage="child")
house["monster_girls"] = [child]
ally, msg = recruit_ally_from_house(p, child, house)
check("recruitment blocks minors", ally is None and "child" in msg)

adult_child = make_girl("AdultChild", key="trueborn_goblin_girl_3",
                        is_trueborn=True, no_romance=True, stage="adult",
                        affection=60, affection_cap=100)
house["monster_girls"] = [adult_child]
ally, msg = recruit_ally_from_house(p, adult_child, house)
check("adult child can join the party", ally is not None
      and ally.get("stage") == "adult" and ally.get("no_romance"))

awaken_child = make_girl("AwakenChild", key="trueborn_goblin_girl_4",
                         mother_key="goblin_girl", is_trueborn=True,
                         no_romance=True, stage="adult", level=40,
                         level_cap=40, affection=200)
ok, reason = facilities.house.can_awaken_girl(awaken_child, 10)
check("true-born can awaken via mother", ok)
from combat.ally_skills import apply_awakening_skills
apply_awakening_skills(awaken_child, "goblin_girl")
awaken_child["awakened"] = True
awakened_ally = create_ally_from_girl(awaken_child)
check("awakened child kit survives recruitment",
      awakened_ally.get("awakened") and awakened_ally.get("awakened_skills")
      and awakened_ally.get("mother_key") == "goblin_girl")

# Father's Legacy (non-Human passives)
base = make_girl("Base", is_ally=True)
base_hp = ally_max_hp(base)
dwarf = make_girl("DwarfLegacy", is_ally=True,
                  father_legacy={"type": "passive", "passive": "max_hp_pct",
                                 "value": 0.075, "label": "+7.5% max HP"})
check("Dwarf legacy adds max HP", ally_max_hp(dwarf) == int(base_hp * 1.075))

attacker = make_girl("Attacker")
elven = make_girl("ElfLegacy", is_ally=True,
                  father_legacy={"type": "passive", "passive": "dodge",
                                 "value": 0.05, "label": "+5% dodge"})
check("Elf legacy adds dodge",
      get_dodge_chance(elven, attacker) - get_dodge_chance(base, attacker) > 0.049)

halfling = make_girl("HalflingLegacy", is_ally=True,
                     father_legacy={"type": "passive", "passive": "crit",
                                    "value": 0.05, "label": "+5% crit"})
check("Halfling legacy adds crit",
      get_raw_critical_chance(halfling, "ally") - get_raw_critical_chance(base, "ally") > 0.049)

orc = make_girl("OrcLegacy", is_ally=True, current_hp=40, max_hp=100,
                father_legacy={"type": "passive", "passive": "low_hp_damage",
                               "value": 0.075, "label": "+7.5% below 50%"})
check("Orc legacy low-HP damage", abs(F.father_legacy_damage_mult(orc) - 1.075) < 1e-9)
orc["current_hp"] = 60
check("Orc legacy inactive above 50%", F.father_legacy_damage_mult(orc) == 1.0)

fire_child = make_girl("FireLegacy", is_ally=True,
                       father_legacy={"type": "passive", "passive": "fire_dark_damage",
                                      "value": 0.075, "label": "+7.5% fire/dark"})
res, dmg = compute_ally_elemental(fire_child)
check("Tiefling legacy adds fire/dark",
      abs(dmg["fire"] - 1.075) < 1e-9 and abs(dmg["dark"] - 1.075) < 1e-9)

item_child = make_girl("ItemLegacy", is_ally=True,
                       father_legacy={"type": "passive", "passive": "item_effectiveness",
                                      "value": 0.05, "label": "+5% items"})
check("Gnome item legacy", abs(F.father_legacy_item_mult(item_child) - 1.05) < 1e-9)

check("child talk lines", bool(child_talk_lines("mid")))
check("child gift is positive", 8 <= facilities.house.get_gift_reaction(
    "trueborn_goblin_girl_1", "sweet", is_trueborn=True) <= 14)

# 16. Phase 4 content coverage -------------------------------------------
print("\n-- phase 4 content --")


class FakeTerm:
    def __init__(self):
        self.lines = []

    def clear(self):
        self.lines.clear()

    def print(self, *args, **kwargs):
        self.lines.append(" ".join(str(a) for a in args))

    def pause(self, *args, **kwargs):
        pass

    def menu(self, options, **kwargs):
        return 0

    def input(self, prompt=""):
        return "Nia"

capturable = {key for key, template in ENEMIES.items()
              if template.get("monster_girl")}
missing_lines = sorted(key for key in capturable if key not in GIRL_ACTION_LINES)
check("all capturable girls have night lines", not missing_lines)
check("Wonderland heroines have night lines", all(
    key in GIRL_ACTION_LINES for key in
    ("wonderland_alice", "wonderland_red_hood", "wonderland_dorothy")))
check("all races have child talk", all(
    race in CHILD_RACE_TALK for race in ENEMY_RACES))
check("all races have child gifts", all(
    race in CHILD_RACE_GIFT for race in ENEMY_RACES))
check("child race pools differ", child_talk_lines("mid", "Goblin")
      != child_talk_lines("mid", "Fey"))
check("child race gift pool", child_gift_lines(True, "Dragonkin")
      != child_gift_lines(False, "Dragonkin"))
check("mother child override", "coin" in child_talk_lines(
    "low", "Goblin", "goblin_girl")[0])
check("mother dialogue child key", "coin" in ENEMIES["goblin_girl"][
    "dialogue"].get("child_talk_low", ""))
check("written action pool", bool(written_action_lines_for("goblin_girl", "tender")))
check("written ending pool", bool(written_ending_lines_for("goblin_girl", "together")))
check("wide generic actions", all(len(pool) >= 8 for pool in ACTION_LINES.values()))
check("wide written actions", all(len(pool) >= 5 for pool in WRITTEN_ACTION_LINES.values()))
check("wide endings", all(len(pool) >= 6 for pool in ENDING_LINES.values()))
check("wide written endings", all(len(pool) >= 4
                                   for pool in WRITTEN_ENDING_LINES.values()))

# Voss & Lumen epilogue trigger + scene
from facilities.story_beats import ensure_city_story_triggers, get_story_beat

p = make_player(day=100)
quests.ensure_quest_state(p)["completed"].append("mq_archivist_06")
p["house_stories"] = {"seen": {"moth_window_3": 1}}
ensure_city_story_triggers(p, "solmere")
check("epilogue waits for Skylume", not quests.has_pending_story(p))
ensure_city_story_triggers(p, "skylume")
check("epilogue queued in Skylume", quests.has_pending_story(p))
check("epilogue registered", get_story_beat("voss_epilogue") is not None)

from facilities import star_tower
p = make_player(day=100)
fake = FakeTerm()
old_term = star_tower.term
star_tower.term = fake
import save_load
old_save = save_load.save_game
save_load.save_game = lambda *_args, **_kwargs: None
try:
    star_tower.voss_epilogue(p)
finally:
    star_tower.term = old_term
    save_load.save_game = old_save
check("epilogue sets flag", quests.ensure_quest_state(p)["flags"].get(
    "voss_epilogue_seen") is True)
check("epilogue grants keepsake", any(
    item.get("id") == "archive_first_page" for item in p["inventory"]))
check("epilogue text", any("first true-born" in line for line in fake.lines)
      and any("The First Page" in line for line in fake.lines))

# 17. UI smoke: shared night + birth naming ------------------------------
print("\n-- UI smoke --")



class SeqTerm(FakeTerm):
    """FakeTerm with a scripted menu choice sequence."""

    def __init__(self, picks):
        super().__init__()
        self.picks = list(picks)

    def menu(self, options, **kwargs):
        return self.picks.pop(0) if self.picks else -1


from facilities.family_ui import process_pending_births
from facilities.sleep_sharing_ui import run_sleep_sharing

p = make_player(day=10)
p["family_enabled"] = True
girl = make_girl("Harpy Scout", key="harpy_scout", affection=200, affection_cap=300)
fake = FakeTerm()
out = run_sleep_sharing(p, girl, fake, rng=FixedRNG(roll=0.99))
check("UI shared night completes", out["ending"] == "together")
check("UI shared night applies affection", girl["affection"] == 204)
check("UI printed fade to black", any("Fade to black" in line for line in fake.lines))
check("UI uses per-girl line", any("folds a wing" in line for line in fake.lines))
check("UI appends personal closing line", any("kiss" in line.lower() for line in fake.lines))
check("UI hides tone labels", not any("Her mood:" in line or "(Tender" in line
                                     or "(Playful" in line or "(Bold" in line
                                     or "(Shy" in line for line in fake.lines))
check("prompts use action language", not any(
    tone in prompt for prompt in ACTION_PROMPTS.values()
    for tone in ("Tender", "Playful", "Bold", "Shy")))

p = make_player(day=10)
p["family_enabled"] = True
written_girl = make_girl("Written", key="goblin_girl", affection=200,
                         affection_cap=300)
written_term = FakeTerm()
written_out = run_sleep_sharing(p, written_girl, written_term,
                                rng=FixedRNG(roll=0.99),
                                content_level="written")
check("written mode completes", written_out["ending"] == "together")
check("written mode adds prose", any("small of your back" in line
                                     for line in written_term.lines))
check("written mode has no fade", not any("Fade to black" in line
                                          for line in written_term.lines))

p = make_player(day=31)
g = make_girl("Goblin Mother", key="goblin_girl", pregnant=True,
              conceived_day=1, due_day=31)
p["houses"]["solmere"]["monster_girls"] = [g]
F.family_tick(p, 30)
fake = FakeTerm()
process_pending_births(p, fake)
check("UI birth names child", p["children"][0]["name"] == "Nia")

# Lounge smoke: true-born adults use Daughter/Bond language and child talk.
p = make_player(day=10)
daughter = make_girl("DaughterUI", key="trueborn_goblin_girl_ui",
                     is_trueborn=True, no_romance=True, stage="adult",
                     affection=60, affection_cap=100)
p["houses"]["solmere"]["monster_girls"] = [daughter]
lounge_term = SeqTerm([0, 0, -1, -1])
old_term = facilities.house.term
facilities.house.term = lounge_term
try:
    facilities.house._house_lounge(p, "solmere", p["houses"]["solmere"])
finally:
    facilities.house.term = old_term
check("lounge shows Bond label", any("Bond:" in line for line in lounge_term.lines))
check("lounge shows Daughter status", any("Daughter" in line for line in lounge_term.lines))
check("lounge child talk gains bond", daughter["affection"] > 60)

if FAILED:
    print(f"\n{len(FAILED)} FAILURE(S): {FAILED}")
    sys.exit(1)
print("\nFamily Phase 1 + Phase 2 + Phase 3 + Phase 4 diagnostics OK")
