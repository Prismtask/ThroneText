"""Diagnostic: Karma Phase 2 — gates, guards, jail, atonement.

Run: python tests/_diag_karma_phase2.py
Exit code 0 = all checks passed.
"""
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

sys.path.insert(0, ".")

import bestiary
import combat.combat_engine as engine
import facilities.guild as guild
import facilities.temple as temple
import karma
from character import build_character
from combat import city_guards

failures = []


def check(cond, label):
    if cond:
        print(f"  PASS  {label}")
    else:
        print(f"  FAIL  {label}")
        failures.append(label)


def make_player(name="Tester", level=1, karma_value=0, day=1, gold=1000):
    attrs = {k: 10 for k in
             ("Strength", "Constitution", "Dexterity", "Wisdom",
              "Learning", "Charisma")}
    p = build_character("1", "1", attrs, name, 990, game_rules={"karma_enabled": True})
    p["level"] = level
    p["karma"] = karma_value
    p["gold"] = gold
    p["day"] = day
    p["karma_daily"] = {"day": day, "gained": 0}
    p["karma_gate"] = {
        "cooldown": {},
        "warning_seen": False,
        "watched_until": 0,
        "jail_karma_day": -99,
        "check_pending": False,
        "atonement_day": -99,
    }
    return p


class _TermStub:
    def __init__(self, choice=0):
        self.choice = choice
        self.lines = []
        self.options = []

    def clear(self):
        pass

    def print(self, *args):
        self.lines.append(" ".join(str(a) for a in args))

    def pause(self):
        pass

    def menu(self, options, **kwargs):
        self.options = list(options)
        return self.choice


print("== 1. Gate responses ==")
p = make_player(level=20, karma_value=-24)
check(karma.get_gate_response(p, "solmere") is None, "-24 Karma -> no gate")

p["karma"] = -25
resp = karma.get_gate_response(p, "solmere")
check(resp and resp["tier"] == "warning" and resp["fee"] == 50,
      "-25 Karma -> one-time warning")
p["karma_gate"]["warning_seen"] = True
resp = karma.get_gate_response(p, "solmere")
check(resp and resp["tier"] == "suspect" and resp["fee"] == 200,
      "Suspect fee scales with level")
check(resp["guards"] == 0 and resp["elite"] == 0, "Suspect has no guard fight")

p["karma"] = -50
resp = karma.get_gate_response(p, "solmere")
check(resp and resp["tier"] == "wanted" and resp["guards"] == 3,
      "-50 Karma -> Wanted with 3 guards")
check(resp["fee"] == 400, "Wanted fee scales with level")

p["karma"] = -75
resp = karma.get_gate_response(p, "solmere")
check(resp and resp["tier"] == "outlaw" and resp["guards"] == 2
      and resp["elite"] == 2, "-75 Karma -> Outlaw with 2 elites + 2 guards")

p["karma"] = -100
check(karma.get_gate_talkdown_dc(p) == 26, "Talk-down DC uses |Karma| // 10")
check(karma.get_gate_response(p, "blackwake") is None, "Blackwake has no gate")
check(karma.get_gate_response(p, "wonderland") is None, "Wonderland has no gate")
p["_eh_in_run"] = True
check(karma.get_gate_response(p, "solmere") is None, "Event Horizon has no gate")
p.pop("_eh_in_run")
p["karma_enabled"] = False
check(karma.get_gate_response(p, "solmere") is None, "Karma-off saves never gate")
p["karma_enabled"] = True

p["karma"] = -30
p["karma_gate"]["cooldown"]["solmere"] = 23
p["day"] = 20
check(karma.get_gate_response(p, "solmere") is None, "Cooldown quiets the gate")
p["day"] = 23
check(karma.get_gate_response(p, "solmere") is not None,
      "Cooldown expires on the listed day")
print()

print("== 2. Guard squads ==")
p = make_player(level=20, karma_value=-60)
wanted = city_guards.spawn_city_guards(p, "wanted")
outlaw = city_guards.spawn_city_guards(p, "outlaw")
check(len(wanted) == 3, "Wanted spawns 3 guards")
check(len(outlaw) == 4, "Outlaw spawns 4 enemies")
check(sum(1 for e in outlaw if e["key"] == "city_guard_elite") == 2,
      "Outlaw includes 2 elite guards")
check(all(e.get("nonlethal") and e.get("no_bestiary")
          and e.get("no_loot") and e.get("no_xp") for e in wanted + outlaw),
      "All guards carry non-lethal/no-reward flags")
check(all(e["level"] >= 20 for e in wanted), "Guards scale to player level")
check(all(e["level"] == 23 for e in outlaw if e["key"] == "city_guard_elite"),
      "Elites scale to player level + 3")
check(all(e["max_hp"] > 0 and e["hp"] == e["max_hp"] for e in wanted),
      "Guard HP is initialized")

from resources.enemies import ENEMIES
from dungeon import get_random_enemy_key
from facilities.travel_events import _pick_travel_enemy

check(ENEMIES["city_guard"].get("city_only")
      and ENEMIES["city_guard_elite"].get("city_only"),
      "Guard templates are marked city-only")
random_keys = {get_random_enemy_key(1, region="temperate") for _ in range(300)}
check(not any("city_guard" in k for k in random_keys),
      "City guards never enter the dungeon random pool")
travel_keys = {
    _pick_travel_enemy({"floor": 1}, "land", "temperate")
    for _ in range(200)
}
check(not any(k and "city_guard" in k for k in travel_keys),
      "City guards never enter the travel encounter pool")

p = make_player(level=20, karma_value=-40, day=10)
board_targets = {b["target_enemy"] for b in guild.generate_bounties(p, "solmere")}
check(not any("city_guard" in k for k in board_targets),
      "City guards never appear on guild bounty boards")

from bestiary import get_total_enemy_count
expected_total = sum(
    1 for t in ENEMIES.values()
    if not t.get("_heroine") and not t.get("city_only")
)
check(get_total_enemy_count() == expected_total,
      "Bestiary completion count excludes city-only guards")
print()

print("== 3. Non-lethal bestiary ==")
recorded = []
orig_record = bestiary.record_defeat
try:
    bestiary.record_defeat = lambda *a, **k: recorded.append(a[1].get("name"))
    dead = [
        {"name": "Guard", "hp": 0, "no_bestiary": True},
        {"name": "Bandit", "hp": 0},
    ]
    engine.prune_dead(dead, make_player())
    check(recorded == ["Bandit"], "prune_dead skips no_bestiary enemies")
finally:
    bestiary.record_defeat = orig_record
print()

print("== 4. Jail ==")
p = make_player(level=1, karma_value=-40, day=5, gold=1000)
p["current_hp"] = 1
p["allies"] = [{"name": "Ally", "max_hp": 100, "current_hp": 1, "defeated": True}]
info = city_guards.city_guard_jail(p, "solmere")
check(info["fine"] == 100 and p["gold"] == 900, "Jail fine is clamped")
check(p["current_hp"] >= 22, "Player healed to at least 50%")
check(p["allies"][0]["current_hp"] >= 50 and not p["allies"][0]["defeated"],
      "Defeated ally revived to 50%")
check(p["karma"] == -37, "Jail grants +3 Karma")
check(p["day"] == 6, "Jail advances to the next morning")
check(p["karma_gate"]["cooldown"]["solmere"] == 8, "Jail sets a 3-day cooldown")
check(p["karma_gate"]["jail_karma_day"] == 5, "Jail records the atonement day")

p["day"] = 7
p["karma_gate"]["jail_karma_day"] = 5
info = city_guards.city_guard_jail(p, "solmere")
check(info["karma"] == 0 and p["karma"] == -37, "Jail atonement has a 3-day cooldown")

p["day"] = 8
p["karma"] = -20
p["karma_daily"] = {"day": 8, "gained": 8}
info = city_guards.city_guard_jail(p, "solmere")
check(info["karma"] == 0, "Jail respects the shared daily positive cap")
check(p["karma_gate"]["jail_karma_day"] == 5,
      "Capped jail does not consume the 3-day window")

p = make_player(level=10, karma_value=-2, day=5, gold=0)
info = city_guards.city_guard_jail(p, "solmere")
check(info["fine"] == 0 and p["gold"] == 0, "Jail never makes gold negative")
check(p["karma"] == 0, "Jail atonement never crosses above 0")
print()

print("== 5. Victory / flee ==")
p = make_player(karma_value=-60, day=10)
city_guards.city_guard_victory(p, "solmere")
check(p["karma_gate"]["cooldown"]["solmere"] == 13, "Victory sets a 3-day cooldown")
check(p["karma_gate"]["watched_until"] == 12, "Victory marks the player watched")
check(p["karma"] == -60, "Victory does not change Karma")

p = make_player(karma_value=-60, day=10)
city_guards.city_guard_flee(p, "solmere")
check(p["karma_gate"]["cooldown"]["solmere"] == 11, "Flee sets a 1-day cooldown")
check(p["karma"] == -60, "Flee does not change Karma")
print()

print("== 6. Temple contrition ==")
orig_term = temple.term
orig_dialogue = temple.service_dialogue
try:
    p = make_player(karma_value=-20, day=5, gold=1000)
    stub = _TermStub(choice=0)
    temple.term = stub
    temple.service_dialogue = lambda *a, **k: None
    temple._act_of_contrition(p, "solmere")
    check(p["karma"] == -19 and p["gold"] == 950,
          "Contrition buys one point for 50 gold")
    check(p["karma_daily"]["gained"] == 1, "Contrition consumes the daily cap")

    p = make_player(karma_value=-20, day=5, gold=1000)
    stub = _TermStub(choice=7)  # restore 8 points
    temple.term = stub
    temple._act_of_contrition(p, "solmere")
    check(p["karma"] == -12 and p["gold"] == 600,
          "Contrition restores up to the +8/day cap")

    p = make_player(karma_value=-3, day=5, gold=1000)
    stub = _TermStub(choice=2)  # restore 3 points
    temple.term = stub
    temple._act_of_contrition(p, "solmere")
    check(p["karma"] == 0 and p["gold"] == 850,
          "Contrition stops at 0")

    p = make_player(karma_value=-20, day=5, gold=1000)
    p["karma_daily"] = {"day": 5, "gained": 8}
    stub = _TermStub(choice=0)
    temple.term = stub
    temple._act_of_contrition(p, "solmere")
    check(p["karma"] == -20 and p["gold"] == 1000,
          "Contrition refuses at the daily cap")

    p = make_player(karma_value=10, day=5)
    stub = _TermStub(choice=0)
    temple.term = stub
    temple._act_of_contrition(p, "solmere")
    check(p["karma"] == 10, "Contrition does nothing at positive Karma")
finally:
    temple.term = orig_term
    temple.service_dialogue = orig_dialogue
print()

print("== 7. Guild atonement contract ==")
p = make_player(level=20, karma_value=-40, day=10)
board = guild.generate_bounties(p, "solmere")
atonements = [b for b in board if b.get("atonement")]
check(len(atonements) == 1, "Negative Karma adds one atonement contract")
check(atonements[0]["reward_karma"] == 5, "Atonement contract grants 5 Karma")
check(p["karma_gate"]["atonement_day"] == 10, "Atonement board cooldown recorded")
board2 = guild.generate_bounties(p, "solmere")
check(not any(b.get("atonement") for b in board2),
      "No second atonement contract in the same week")
p["day"] = 17
board3 = guild.generate_bounties(p, "solmere")
check(any(b.get("atonement") for b in board3),
      "Atonement contract returns after 7 days")

orig_term = guild.term
orig_advance = guild.advance_time
try:
    p = make_player(level=10, karma_value=-20, day=5, gold=0)
    p["active_bounties"] = [{
        "id": "atonement_test",
        "target_enemy": "bandit",
        "target_name": "Bandit",
        "target_level": 2,
        "required": 3,
        "current": 3,
        "deadline": 12,
        "days_given": 7,
        "reward_gold": 25,
        "reward_karma": 5,
        "atonement": True,
        "city": "solmere",
        "difficulty": "Atonement",
    }]
    stub = _TermStub(choice=0)
    guild.term = stub
    guild.advance_time = lambda *a, **k: None
    guild._manage_bounties(p, "solmere")
    check(p["gold"] == 25, "Atonement turn-in pays its gold reward")
    check(p["karma"] == -15, "Atonement turn-in grants +5 Karma")
    check("favor" not in p, "Atonement turn-in does not write City Favor")
    check(not p["active_bounties"], "Atonement contract is consumed")

    p = make_player(level=10, karma_value=0, day=5, gold=0)
    p["daily_effects"] = {"bounty_bonus": 0.5}
    p["active_bounties"] = [{
        "id": "normal_test",
        "target_enemy": "bandit",
        "target_name": "Bandit",
        "target_level": 5,
        "required": 2,
        "current": 2,
        "deadline": 12,
        "days_given": 7,
        "reward_gold": 100,
        "city": "solmere",
        "difficulty": "Silver ★★",
    }]
    stub = _TermStub(choice=0)
    guild.term = stub
    guild._manage_bounties(p, "solmere")
    check(p["gold"] == 150, "Normal bounty still applies Bounty Rush gold")
    check("favor" not in p, "Normal bounty no longer writes City Favor")
    check(p.get("bounties_completed") == 1, "Normal bounty completion still counts")
finally:
    guild.term = orig_term
    guild.advance_time = orig_advance
print()

print("== 7b. Guild bounties scale from Karma ==")
p_high = make_player(level=20, karma_value=100, day=10)
p_low = make_player(level=20, karma_value=-100, day=10)
high_board = guild.generate_bounties(p_high, "solmere")
low_board = guild.generate_bounties(p_low, "solmere")
check(len(high_board) == 7, "Paragon gets the full 7-contract board")
check(len(low_board) == 3, "Outlaw gets 2 normal contracts + 1 atonement")
check(any(b.get("atonement") for b in low_board),
      "Outlaw board includes an atonement contract")
check(not any(b.get("atonement") for b in high_board),
      "Paragon board has no atonement contract")
check(all("reward_favor" not in b for b in high_board + low_board),
      "Bounty entries no longer carry reward_favor")
check("favor" not in p_high and "favor" not in p_low,
      "Generating bounties does not write City Favor")
from events import FIXED_EVENTS
check(FIXED_EVENTS[1]["effect"].get("bounty_bonus") == 0.25,
      "New Moon grants a 25% bounty-gold bonus")
print()

print("== 8. Gate pending flag ==")
p = make_player()
karma.ensure_state(p)
check(p["karma_gate"]["check_pending"] is False, "New save starts with no pending gate")
p["karma_gate"]["check_pending"] = True
check(p["karma_gate"].pop("check_pending") is True, "Pending gate is one-shot")
print()

print("== 9. Gate choice menu ==")
import gui.screens.city_screen as city_screen_mod
from resources.cities import CITIES

_orig_choice_dialog = city_screen_mod.choice_dialog
try:
    captured = {}

    def _capture(**kwargs):
        captured.clear()
        captured.update(kwargs)

    city_screen_mod.choice_dialog = _capture

    screen = object.__new__(city_screen_mod.CityScreen)
    screen.city_id = "solmere"
    screen.city = CITIES["solmere"]

    def _options_for(karma_value, gold=1000, tier=None):
        p = make_player(level=20, karma_value=karma_value, gold=gold)
        p["karma_gate"]["warning_seen"] = tier != "warning"
        screen.player = p
        response = {
            "tier": tier or ("warning" if karma_value == -25 else
                             "suspect" if karma_value < -25 else
                             "wanted" if karma_value <= -50 else "outlaw"),
            "fee": 50 if tier == "warning" else 200,
            "guards": 0 if tier in ("warning", "suspect") else 3,
            "elite": 2 if tier == "outlaw" else 0,
        }
        screen._show_karma_gate(response)
        return [key for key, _label in captured["options"]]

    check(_options_for(-25, tier="warning") == ["pay", "leave"],
          "Warning offers pay / turn away")
    check(_options_for(-25, gold=0, tier="warning") == ["leave"],
          "Broke player cannot pay the warning fee")
    check(_options_for(-30, tier="suspect") == ["pay", "leave"],
          "Suspect offers pay / turn away")
    check(_options_for(-60, tier="wanted") == ["pay", "talk", "submit", "fight", "leave"],
          "Wanted offers pay / talk / submit / fight / leave")
    check(_options_for(-90, tier="outlaw") == ["pay", "talk", "submit", "fight", "leave"],
          "Outlaw offers pay / talk / submit / fight / leave")

    p = make_player(level=20, karma_value=-30)
    p["karma_gate"]["check_pending"] = True
    screen.player = p
    check(screen._start_karma_gate() is True, "Pending low-Karma gate opens")
    check(p["karma_gate"]["check_pending"] is False,
          "Gate check consumes the pending flag")
finally:
    city_screen_mod.choice_dialog = _orig_choice_dialog
print()

print("== 10. Gate action wiring ==")


class _SMStub:
    def __init__(self):
        self.logs = []
        self.switched = None

    def log(self, message, **kwargs):
        self.logs.append(message)

    def switch_to(self, screen_class, **kwargs):
        self.switched = (screen_class, kwargs)


def _screen_for(p):
    screen = object.__new__(city_screen_mod.CityScreen)
    screen.player = p
    screen.city_id = "solmere"
    screen.city = CITIES["solmere"]
    screen.sm = _SMStub()
    screen._refresh_after_gate = lambda: None
    screen._resume_arrival = lambda: setattr(screen, "_resumed", True)
    return screen

p = make_player(karma_value=-25, day=5, gold=1000)
screen = _screen_for(p)
screen._gate_pay({"tier": "warning", "fee": 50})
check(p["gold"] == 950, "Paying a gate fee deducts gold")
check(p["karma_gate"]["warning_seen"] is True, "Paying the warning marks it seen")
check(p["karma_gate"]["cooldown"]["solmere"] == 6,
      "Paying the warning starts a 1-day cooldown")
check(getattr(screen, "_resumed", False), "Paying resumes city arrival checks")

p = make_player(karma_value=-30, day=5, gold=1000)
screen = _screen_for(p)
screen._gate_pay({"tier": "suspect", "fee": 200})
check(p["gold"] == 800, "Paying the Suspect fee deducts gold")
check(p["karma_gate"]["cooldown"]["solmere"] == 8,
      "Paying the Suspect fee starts a 3-day cooldown")
check(p["karma"] == -30, "Paying a gate fee never changes Karma")

p = make_player(karma_value=-40, day=5, gold=1000)
screen = _screen_for(p)
screen._gate_submit({"tier": "wanted", "fee": 400})
check(p["gold"] == 900, "Submitting to judgment pays the jail fine")
check(p["day"] == 6, "Submitting to judgment advances the day")
check(p["karma"] == -37, "Submitting to judgment grants jail Karma")
check(screen.sm.switched and screen.sm.switched[0].__name__ == "CityScreen",
      "Submitting rebuilds the city screen")

p = make_player(karma_value=-60, day=5)
screen = _screen_for(p)
screen._after_city_guard_combat("victory")
check(p["karma_gate"]["cooldown"]["solmere"] == 8,
      "Guard victory sets the gate cooldown")
check(p["karma"] == -60, "Guard victory does not change Karma")
check(screen.sm.switched and screen.sm.switched[0].__name__ == "CityScreen",
      "Guard victory returns to the city")

p = make_player(karma_value=-60, day=5, gold=1000)
screen = _screen_for(p)
screen._after_city_guard_combat("dead")
check(p["day"] == 6 and p["gold"] == 900,
      "Guard defeat goes to jail, not DeathScreen")
check(p["karma"] == -57, "Guard defeat grants jail Karma")
check(screen.sm.switched and screen.sm.switched[0].__name__ == "CityScreen",
      "Guard defeat returns to the city")

p = make_player(karma_value=-60, day=5)
screen = _screen_for(p)
screen._after_city_guard_combat("fled")
check(p["karma_gate"]["cooldown"]["solmere"] == 6,
      "Guard flee sets a 1-day cooldown")
check(screen.sm.switched and screen.sm.switched[0].__name__ == "WorldMapScreen",
      "Guard flee returns to the world map")
print()

print("== 11. Talk-down / fight launch ==")
import random as _random
import combat.stats as combat_stats

_orig_randint = _random.randint
_orig_player_stats = combat_stats.compute_player_stats
_orig_ok_dialog = city_screen_mod.ok_dialog
try:
    combat_stats.compute_player_stats = lambda p: (0, 0, 0, 0, 0, 50)
    _random.randint = lambda a, b: 20

    p = make_player(karma_value=-60, day=5, gold=1000)
    p["karma_gate"]["warning_seen"] = True
    screen = _screen_for(p)
    screen._gate_talk({"tier": "wanted", "fee": 400})
    check(p["gold"] == 800, "Successful talk-down pays half the fee")
    check(p["karma_gate"]["cooldown"]["solmere"] == 8,
          "Successful talk-down sets a 3-day cooldown")
    check(getattr(screen, "_resumed", False), "Successful talk-down resumes arrival")

    combat_stats.compute_player_stats = lambda p: (0, 0, 0, 0, 0, 0)
    _random.randint = lambda a, b: 1
    p = make_player(karma_value=-60, day=5, gold=1000)
    screen = _screen_for(p)
    captured = {}
    city_screen_mod.ok_dialog = lambda parent, title, message, on_ok=None: captured.update(
        {"title": title, "message": message, "on_ok": on_ok}
    )
    screen._gate_talk({"tier": "wanted", "fee": 400})
    check("Talk-Down Failed" in captured.get("title", ""),
          "Failed talk-down shows the roll result")
    check(callable(captured.get("on_ok")), "Failed talk-down offers a fight")
    check(p["gold"] == 1000, "Failed talk-down does not charge gold")

    p = make_player(karma_value=-60, day=5)
    screen = _screen_for(p)
    screen._gate_fight({"tier": "outlaw", "fee": 600})
    check(screen.sm.switched and screen.sm.switched[0].__name__ == "CombatScreen",
          "Fighting the gate launches CombatScreen")
    enemies = screen.sm.switched[1].get("enemies", [])
    check(len(enemies) == 4 and all(e.get("nonlethal") for e in enemies),
          "Outlaw gate fight passes the non-lethal guard squad")
finally:
    combat_stats.compute_player_stats = _orig_player_stats
    _random.randint = _orig_randint
    city_screen_mod.ok_dialog = _orig_ok_dialog
print()

if failures:
    print(f"FAILED: {len(failures)} check(s)")
    for f in failures:
        print("  -", f)
    sys.exit(1)
print("All Karma Phase 2 diagnostics passed.")
