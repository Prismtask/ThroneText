"""Diagnostic: deed titles (docs/titles_design.md) Phase 1.

Run: .venv\\Scripts\\python.exe tests/_diag_titles.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import titles
from resources.titles import TITLES, TITLES_BY_ID

failures = []


def check(label, got, expected):
    ok = got == expected
    print(f"  {'OK  ' if ok else 'FAIL'} {label}: got {got}, expected {expected}")
    if not ok:
        failures.append(label)


def make_player(name="Aria"):
    return {
        "name": name,
        "day": 3,
        "level": 10,
        "karma": 0,
        "karma_enabled": False,
        "family_enabled": False,
        "city_floors": {"solmere": {"floor": 1, "max_floor": 1}},
        "bestiary": {},
        "defeated_superbosses": [],
        "bounties_completed": 0,
        "high_bounties_completed": 0,
        "houses": {},
        "children": [],
        "quests": {"flags": {}, "completed": []},
        "journal": {"events": [], "main_quests": [], "side_quests": []},
        "wedding_combat_active": False,
        "event_horizon": {"best_room": 0},
    }


def effect_within_budget(key, value):
    if key == "combat_stat":
        return isinstance(value, dict) and 0 <= int(value.get("value", 0) or 0) <= 2
    return key in titles.EFFECT_CAPS and 0 <= float(value) <= titles.EFFECT_CAPS[key]


print("=== Registry sanity ===")
check("unique ids", len({t["id"] for t in TITLES}), len(TITLES))
check("all conditions declarative", all(isinstance(t.get("condition"), dict) for t in TITLES), True)
check("all effects within caps",
      all(all(effect_within_budget(k, v) for k, v in t["effects"].items())
          for t in TITLES),
      True)
check("all drawbacks within caps",
      all(all(k in titles.EFFECT_CAPS
              and 0 <= float(v) <= titles.EFFECT_CAPS[k]
              for k, v in t.get("drawbacks", {}).items())
          for t in TITLES),
      True)

print("=== State + unlock ===")
p = make_player()
titles.ensure_state(p)
check("fields created", isinstance(p["titles_unlocked"], dict), True)
check("no unlocks yet", len(p["titles_unlocked"]), 0)

p["bestiary"] = {f"enemy_{i}": {"defeated": 1, "captured": 0} for i in range(10)}
new = titles.check_unlock(p)
check("first blood unlocked", "first_blood" in p["titles_unlocked"], True)
check("journal entry written", any(e.get("tag") == "[TITLE]" for e in p["journal"]["events"]), True)
check("unlock idempotent", titles.check_unlock(p), [])

print("=== Equip / effects ===")
ok, msg = titles.equip_title(p, "first_blood")
check("equip ok", ok, True)
check("active id", p["title_active"], "first_blood")
check("xp bonus", round(titles.mod(p, "xp_pct"), 4), 0.01)
check("full name", titles.format_name(p, "full"), "Aria the First-Blooded")
check("compact name", titles.format_name(p, "compact"), "Aria (First Blood)")
check("plain name", titles.format_name(p, "plain"), "Aria")
check("show_title off", titles.format_name(p, "full", show_title=False), "Aria")
check("effect line", "XP" in titles.format_effect_line(TITLES_BY_ID["first_blood"]), True)

print("=== Caps + gold find ===")
p["title_active"] = "haggler"
p["titles_unlocked"]["haggler"] = {"day": 1, "seen": True}
check("shop cap", round(titles.mod(p, "shop_discount_pct"), 4), 0.03)
p["title_active"] = "pathfinder"
p["titles_unlocked"]["pathfinder"] = {"day": 1, "seen": True}
check("gold find T1", titles.apply_gold_find(p, 100), 102)

print("=== Old-save reconcile ===")
old = make_player("Old Save")
old["titles_version"] = 0
old["city_floors"] = {"solmere": {"floor": 1, "max_floor": 31}}
old["bestiary"] = {f"enemy_{i}": {"defeated": 5, "captured": 1} for i in range(30)}
new = titles.reconcile(old)
check("reconcile unlocks", bool(new), True)
check("pathfinder derived floors", "pathfinder" in old["titles_unlocked"], True)
check("delver derived floors", "delver" in old["titles_unlocked"], True)
check("beast-tamer captures", "beast_tamer" in old["titles_unlocked"], True)
check("reconcile sets version", old["titles_version"], titles.TITLES_VERSION)
check("reconcile only once", titles.reconcile(old), [])

print("=== Locked presentation ===")
locked = make_player("Locked")
titles.ensure_state(locked)
row = next(r for r in titles.list_titles(locked) if r["id"] == "first_blood")
check("locked name hidden", row["name"], "???")
check("locked effect hidden", row["effect_line"], "")
check("locked hint present", bool(row["hint"]), True)
check("locked progress present", bool(row["progress"]), True)

print("=== Swap guard ===")
locked["wedding_combat_active"] = True
check("cannot swap in combat", titles.can_swap(locked), False)
locked["wedding_combat_active"] = False
check("can swap outside combat", titles.can_swap(locked), True)
ok, _ = titles.equip_title(locked, "first_blood")
check("cannot equip unearned", ok, False)

print("=== Condition edge cases ===")
k = make_player("Karma")
k["karma"] = 39
check("outlaw karma progress uses signed values", titles.condition_progress(
    k, {"type": "karma", "at_most": -75}),
    ("Karma (toward Outlaw)", 39, -75))
k["karma"] = -80
check("karma at_most", titles.condition_met(
    k, {"type": "karma", "at_most": -75}), True)
check("karma at_least", titles.condition_met(
    k, {"type": "karma", "at_least": -50}), False)
check("composite all", titles.condition_met(k, {"type": "all", "all": [
    {"type": "level", "level": 5},
    {"type": "karma", "at_most": -75},
]}), True)

print("=== Phase 2 titles ===")
from resources.enemies import ENEMIES
_dragon_keys = [key for key, data in ENEMIES.items()
                if data.get("race") == "Dragonkin"]
check("dragonkin pool exists", bool(_dragon_keys), True)

p2 = make_player("Phase Two")
p2["bestiary"] = {_dragon_keys[0]: {"defeated": 10, "captured": 0}}
p2["bounties_completed"] = 50
p2["houses"] = {"solmere": {"level": 3}}
p2["children"] = [{"name": "Test Child"}]
p2["family_enabled"] = True
p2["karma_enabled"] = True
p2["karma"] = 80
titles.check_unlock(p2)
for _tid in ("dragon_slayer", "contracted", "hearthkeeper", "honest"):
    check(f"{_tid} unlocked", _tid in p2["titles_unlocked"], True)

p2["title_active"] = "dragon_slayer"
check("combat stat bonus", titles.combat_stat_bonus(p2, "Strength"), 1)
check("combat stat other attr", titles.combat_stat_bonus(p2, "Dexterity"), 0)
check("dragon effect line", "Strength" in titles.format_effect_line(
    TITLES_BY_ID["dragon_slayer"]), True)

p2["title_active"] = "contracted"
check("bounty gold bonus", round(titles.mod(p2, "bounty_gold_pct"), 4), 0.05)
p2["title_active"] = "hearthkeeper"
check("upkeep cut", round(titles.mod(p2, "upkeep_pct"), 4), 0.05)
p2["title_active"] = "honest"
check("honest shop bonus", round(titles.mod(p2, "shop_discount_pct"), 4), 0.05)

k2 = make_player("Outlaw")
k2["karma_enabled"] = True
k2["karma"] = -80
titles.check_unlock(k2)
check("unrepentant unlocked", "unrepentant" in k2["titles_unlocked"], True)
k2["title_active"] = "unrepentant"
check("black market bonus", round(titles.mod(k2, "black_market_pct"), 4), 0.05)

k3 = make_player("Karma Off")
k3["karma_enabled"] = False
k3["karma"] = 100
titles.check_unlock(k3)
check("karma titles gated by rule", "honest" in k3["titles_unlocked"], False)

k4 = make_player("Karma Hook")
k4["karma_enabled"] = True
k4["karma"] = 79
from karma import change_karma
change_karma(k4, 1, "diag")
check("karma change triggers unlock", "honest" in k4["titles_unlocked"], True)

print("=== Phase 3 titles ===")
from bestiary import get_total_enemy_count, is_bestiary_candidate
p3 = make_player("Endgame")
p3["defeated_superbosses"] = [f"boss_{i}" for i in range(9)]
p3["event_horizon"] = {"best_room": 50}
p3["quests"]["flags"]["voss_epilogue_seen"] = True
_target = int(round(get_total_enemy_count() * 0.8))
_candidates = [k for k in ENEMIES if is_bestiary_candidate(k)][:_target]
p3["bestiary"] = {k: {"defeated": 1, "captured": 0} for k in _candidates}
titles.check_unlock(p3)
for _tid in ("stormbreaker", "abyss_walker", "collector", "worldbreaker", "first_page"):
    check(f"{_tid} unlocked", _tid in p3["titles_unlocked"], True)

p3["title_active"] = "stormbreaker"
check("stormbreaker stat", titles.combat_stat_bonus(p3, "Strength"), 2)
check("stormbreaker other attr", titles.combat_stat_bonus(p3, "Dexterity"), 0)
p3["title_active"] = "abyss_walker"
check("abyss xp", round(titles.mod(p3, "xp_pct"), 4), 0.06)
p3["title_active"] = "collector"
check("collector learning", titles.combat_stat_bonus(p3, "Learning"), 2)
check("collector xp", round(titles.mod(p3, "xp_pct"), 4), 0.05)
p3["title_active"] = "worldbreaker"
check("worldbreaker strength", titles.combat_stat_bonus(p3, "Strength"), 2)
check("worldbreaker dexterity", titles.combat_stat_bonus(p3, "Dexterity"), 2)
check("worldbreaker learning", titles.combat_stat_bonus(p3, "Learning"), 2)
check("worldbreaker drawback", round(titles.mod(p3, "shop_discount_pct"), 4), -0.10)
check("worldbreaker effect line", "drawback" in titles.format_effect_line(
    TITLES_BY_ID["worldbreaker"]), True)
p3["title_active"] = "first_page"
check("first page rest bonus", round(titles.mod(p3, "rest_heal_pct"), 4), 0.10)

from karma_dialogue import title_line
check("title greeting", bool(title_line(p3, "shop")), True)
check("collection summary", "Acknowledged 5" in titles.collection_summary(p3), True)

print("=== Casino titles ===")
c = make_player("Casino")
c["title_stats"] = {
    "casino_hands_won": 100,
    "casino_biggest_win": 4_750,
    "casino_cheats_unseen": 10,
    "casino_cheats_caught": 3,
}
c["casino"] = {
    "hands_won": 100,
    "biggest_win": 4_750,
    "cheats_unseen": 10,
    "cheats_caught": 3,
}
titles.check_unlock(c)
for _tid in ("the_gambler", "sleight_hand", "marked"):
    check(f"{_tid} unlocked", _tid in c["titles_unlocked"], True)

c_big = make_player("Big Win")
c_big["title_stats"] = {"casino_hands_won": 0, "casino_biggest_win": 4_000}
titles.check_unlock(c_big)
check("gambler biggest-win branch", "the_gambler" in c_big["titles_unlocked"], True)

c["title_active"] = "the_gambler"
check("gambler payout mod", round(titles.mod(c, "casino_payout_pct"), 4), 0.01)
check("gambler effect line",
      "casino payouts" in titles.format_effect_line(TITLES_BY_ID["the_gambler"]),
      True)
c["title_active"] = "sleight_hand"
check("sleight black market mod",
      round(titles.mod(c, "black_market_pct"), 4), 0.03)
check("sleight effect line has no phantom shop bonus",
      "shop discount" not in titles.format_effect_line(
          TITLES_BY_ID["sleight_hand"]), True)
c["title_active"] = "marked"
check("marked black market mod",
      round(titles.mod(c, "black_market_pct"), 4), 0.05)
check("marked shop drawback",
      round(titles.mod(c, "shop_discount_pct"), 4), -0.05)
check("marked effect line",
      "drawback" in titles.format_effect_line(TITLES_BY_ID["marked"])
      and "Black Market" in titles.format_effect_line(TITLES_BY_ID["marked"]),
      True)

rows = titles.list_titles(c)
gambler_row = next(r for r in rows if r["id"] == "the_gambler")
check("gambler record line", "Hands won: 100" in gambler_row["record_line"], True)
check("gambler biggest record", "4,750g" in gambler_row["record_line"], True)
locked_c = make_player("Casino Locked")
titles.ensure_state(locked_c)
locked_row = next(r for r in titles.list_titles(locked_c) if r["id"] == "the_gambler")
check("locked record line", "Hands won: 0" in locked_row["record_line"], True)

print("=== Wonderland titles ===")
w = make_player("Storybook")
w["wonderland_visited"] = True
w["wl_hatter_three_guests_seen"] = True
w["wl_boss_defeated_queen_of_hearts"] = True
w["wl_boss_defeated_big_bad_wolf"] = True
w["wl_boss_defeated_wicked_witch"] = True
w["wl_boss_defeated_jabberwock"] = True
w["wl_boss_defeated_mary_sue"] = True
w["wonderland_heroine_redhood_permanent"] = True
w["wonderland_heroine_dorothy_permanent"] = True
w["wonderland_heroine_alice_permanent"] = True
w["title_stats"] = {"wonderland_shadows_taken": 2}
titles.check_unlock(w)
for _tid in ("curiouser", "tea_party_guest", "shadow_touched", "heartsbane",
             "wolf_hunter", "witch_breaker", "vorpal_hand", "authors_bane",
             "happily_ever_after"):
    check(f"{_tid} unlocked", _tid in w["titles_unlocked"], True)

w["title_active"] = "heartsbane"
check("heartsbane gold", titles.apply_gold_find(w, 100), 103)
w["title_active"] = "wolf_hunter"
check("wolf hunter strength", titles.combat_stat_bonus(w, "Strength"), 1)
w["title_active"] = "witch_breaker"
check("witch breaker xp", round(titles.mod(w, "xp_pct"), 4), 0.06)
w["title_active"] = "vorpal_hand"
check("vorpal damage", round(titles.mod(w, "damage_pct"), 4), 0.04)
w["title_active"] = "authors_bane"
check("author learning", titles.combat_stat_bonus(w, "Learning"), 2)
check("author xp", round(titles.mod(w, "xp_pct"), 4), 0.04)
w["title_active"] = "happily_ever_after"
check("ever after all stats", titles.combat_stat_bonus(w, "Dexterity"), 1)
check("ever after effect line", "all attributes" in titles.format_effect_line(
    TITLES_BY_ID["happily_ever_after"]), True)

w_locked = make_player("Before the Book")
titles.ensure_state(w_locked)
check("wonderland flag progress label",
      titles.condition_progress(
          w_locked, TITLES_BY_ID["curiouser"]["condition"]),
      ("Wonderland entered", 0, 1))

w["title_stats"] = {}
titles.note_deed(w, "wonderland_shadows_taken", 1)
check("shadow deed counter increments",
      w["title_stats"].get("wonderland_shadows_taken"), 1)

w_old = make_player("Mid-Cycle")
w_old["wonderland_shadows"] = ["off_with_heads", "rose_wilt"]
titles.ensure_state(w_old)
check("shadow counter backfills from active shadows",
      w_old["title_stats"].get("wonderland_shadows_taken"), 2)

print()
if failures:
    print("FAILED:", ", ".join(failures))
    sys.exit(1)
print("titles diagnostics OK")
