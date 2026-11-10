"""Diagnostic: Dispatch system Phase 1.

Checks level curves, offer generation + 3-day cycle, naming, mood, launch +
slot cap, time-based resolution + idempotency, HP/stress round-trip, report
collection, and nightly recovery — all headless.

Run:  .venv\\Scripts\\python.exe tests\\_diag_dispatch.py
"""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
random.seed(42)

import facilities.house  # noqa: F401  (circular-import smoke test)
from facilities import dispatch as D


def make_girl(name, level=8, stress=0, hp=None):
    g = {
        "key": f"test_{name.lower()}",
        "name": name,
        "level": level,
        "affection": 60,
        "stress": stress,
        "exp": 0,
        "level_cap": 30,
        "attributes": {"Strength": 8, "Constitution": 8, "Dexterity": 8,
                       "Wisdom": 8, "Learning": 8, "Charisma": 8},
        "level_hp_bonus": (level - 1) * 4,
    }
    if hp is not None:
        g["current_hp"] = hp
    return g


def make_player(house_level=3, max_floor=12):
    house = {
        "level": house_level, "storage": [], "last_income_day": 1,
        "monster_girls": [make_girl("Mira"), make_girl("Tessa"),
                          make_girl("Pella"), make_girl("Rho")],
    }
    return {
        "day": 1, "time_minutes": 8 * 60, "gold": 100, "inventory": [],
        "allies": [], "houses": {"solmere": house},
        "city_floors": {"solmere": {"floor": 1, "max_floor": max_floor}},
        "max_floor": max_floor, "origin_city": "solmere",
        "journal": {"events": [], "main_quests": [], "side_quests": []},
    }


# 1. Level curves ---------------------------------------------------------
assert D.star_for_power(15) == 1 and D.star_for_power(16) == 2
assert D.star_for_power(120) == 5 and D.star_for_power(121) == 6
assert [D.slot_cap(l) for l in range(1, 9)] == [1, 1, 2, 2, 2, 2, 3, 3]
assert [D.team_cap(l) for l in range(1, 9)] == [2, 2, 3, 3, 3, 3, 4, 4]
assert [D.star_cap(l) for l in range(1, 9)] == [3, 3, 4, 4, 5, 5, 6, 6]
assert [D.offer_count(l) for l in range(1, 9)] == [4, 4, 5, 5, 6, 6, 7, 7]
print("[OK] level curves")

# 2. Offers: count, star cap, names, cycle stability ----------------------
player = make_player()
house = player["houses"]["solmere"]
offers = D.ensure_offers(player, "solmere", house)
assert len(offers) == 5, len(offers)
assert all(o["stars"] <= D.star_cap(3) for o in offers)
assert all(o["name"] and " " in o["name"] for o in offers)
assert D.ensure_offers(player, "solmere", house) is offers  # no re-roll mid-cycle
sweep = next(o for o in offers if o["kind"] == "sweep")
assert sweep["floors"] and sweep["floors"][1] <= 12
print(f"[OK] offers ({len(offers)}): " + " | ".join(o["name"] for o in offers))

player["day"] = 4
offers_next = D.ensure_offers(player, "solmere", house)
assert offers_next is not offers  # cycle rolled over
player["day"] = 1
offers = D.ensure_offers(player, "solmere", house)  # back on cycle 0 → fresh board
sweep = next(o for o in offers if o["kind"] == "sweep")
print("[OK] 3-day offer cycle")

# 3. Mood ----------------------------------------------------------------
calm = make_girl("Calm"); calm["affection"] = 130  # ladder v2: Spirited at 120+
assert D.mood_of(calm, 1)[0] == "Spirited"
assert D.mood_of(make_girl("Tired", stress=55), 1)[0] == "Tired"
assert D.mood_of(make_girl("Weary", stress=80), 1)[0] == "Weary"
burned = D.mood_of(make_girl("Burned", stress=95), 1)
assert burned[0] == "Burned Out" and burned[2] is True
print("[OK] mood")

# 4. Launch + slot cap ----------------------------------------------------
mira, tessa, pella = house["monster_girls"][:3]
inst, msg = D.create_instance(player, "solmere", house, sweep, [mira, tessa])
assert inst and mira["dispatch_mission"] == inst["instance_id"]
inst2, _ = D.create_instance(player, "solmere", house, offers[0], [pella])
assert inst2  # 2 slots at house level 3
inst3, err3 = D.create_instance(player, "solmere", house, offers[0], [house["monster_girls"][3]])
assert inst3 is None and "slots" in err3  # slot cap rejects before consumption

# 4b. Launched offers are consumed from the board
remaining = {o["id"] for o in D.get_dispatch_state(player)["offers"]}
assert sweep["id"] not in remaining and offers[0]["id"] not in remaining
assert len(remaining) == len(offers) - 2
print("[OK] launch + slot cap + offer consumption")

# 4c. A cleared-out board stays empty until the next cycle (no infinite regen)
d = D.get_dispatch_state(player)
d["offers"] = []
assert D.ensure_offers(player, "solmere", house) == []
player["day"] = 4
assert len(D.ensure_offers(player, "solmere", house)) == 5
player["day"] = 1
print("[OK] cleared board waits for refresh")

# 5. Resolution + idempotency --------------------------------------------
player["day"] = 2
player["time_minutes"] = 23 * 60  # well past both return times
D.process_dispatch_progress(player, days_passed=1)
st = D.get_dispatch_state(player)
assert len(st["active"]) == 0, st["active"]
assert len(st["reports"]) == 2
assert not mira.get("dispatch_mission")
assert int(mira["current_hp"]) >= 1
assert 0 <= int(mira["stress"]) <= 100
D.process_dispatch_progress(player, days_passed=0)
assert len(D.get_dispatch_state(player)["reports"]) == 2  # no double resolve
print("[OK] resolution + idempotency")
for rep in st["reports"]:
    print(f"   - {rep['name']} → {rep['outcome']} (gold={rep['gold']}, items={rep['items']})")

# 6. HP / stress round-trip ---------------------------------------------
hp_girl = house["monster_girls"][3]
hp_girl["current_hp"] = 11
hp_girl["stress"] = 30
from combat.ally import create_ally_from_girl, _return_ally_to_house
ally = create_ally_from_girl(hp_girl)
assert ally["current_hp"] == 11, ally["current_hp"]
assert ally["stress"] == 30
ally["current_hp"] = 7
house["monster_girls"].remove(hp_girl)
_return_ally_to_house(player, ally, house)
back = next(g for g in house["monster_girls"] if g["name"] == hp_girl["name"])
assert back["current_hp"] == 7, back.get("current_hp")
assert back["stress"] == 30
print("[OK] HP/stress round-trip")

# 7. Collect -------------------------------------------------------------
gold_before = player["gold"]
D.collect_reports(player, "solmere", house)
assert D.get_dispatch_state(player)["reports"] == []
assert player["gold"] >= gold_before
assert "favor" not in player
print(f"[OK] collect (gold {gold_before} → {player['gold']}, no City Favor)")

# 8. Nightly recovery ----------------------------------------------------
night = make_girl("Night", stress=50, hp=10)
house["monster_girls"].append(night)
D.process_dispatch_progress(player, days_passed=2)
expected = 50 - 2 * (5 + min(3, 6) + 2)
assert night["stress"] == expected, (night["stress"], expected)
assert night["current_hp"] > 10
print("[OK] night recovery")

# 9. Journal entries -----------------------------------------------------
tags = [e.get("tag") for e in player["journal"]["events"]]
assert "[DISPATCH]" in tags
print("[OK] journal [DISPATCH] entries")

# 10. Guards: burnout refusal, injured recruit block, Wonderland freeze ---
fresh = D.ensure_offers(player, "solmere", house)
assert fresh, "expected a fresh board for guard tests"

burned_girl = make_girl("Smolder", stress=95)
house["monster_girls"].append(burned_girl)
assert burned_girl not in D.eligible_girls(player, house)
no_inst, err = D.create_instance(player, "solmere", house, fresh[0], [burned_girl])
assert no_inst is None and "burned out" in err

hurt_girl = make_girl("Bruise")
hurt_girl["injured_until"] = player["day"] + 1
house["monster_girls"].append(hurt_girl)
from combat.ally import recruit_ally_from_house
ally_no, msg_no = recruit_ally_from_house(player, hurt_girl, house)
assert ally_no is None and "injured" in msg_no
print("[OK] burnout refusal + injured recruit block")

frost = make_girl("Frost")
house["monster_girls"].append(frost)
inst_w, _ = D.create_instance(player, "solmere", house, fresh[0], [frost])
assert inst_w
from utils import advance_time
player["wonderland_active"] = True
advance_time(player, 3 * 1440)  # three days inside Wonderland
assert D.get_dispatch_state(player)["active"], "missions must not progress in Wonderland"
player.pop("wonderland_active", None)
print("[OK] Wonderland freeze (no dispatch progress)")

# 12. Phase 2: bath salts + Temple respite --------------------------------
from resources.items import build_item
salts = build_item("herbal_bath_salts")
assert salts["type"] == "house_item" and salts["stress_relief"] == 20
assert salts["type"] not in ("consumable", "utility")  # never appears in combat menus
assert "description" in salts

from facilities.temple import _stressed_companions, _day_of_respite
mira["stress"] = 40
player["gold"] = 1000
stressed_before = len(_stressed_companions(player))
assert stressed_before >= 1
_day_of_respite(player, "solmere")
assert player["gold"] == 1000 - 50 * stressed_before
print("[OK] Phase 2 items (bath salts + Day of Respite)")

print("All dispatch diagnostics passed.")
