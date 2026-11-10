"""Diagnostic: Karma Phase 3 — hallucination, dialogue, travel, Blackwake stock.

Run: python tests/_diag_karma_phase3.py
Exit code 0 = all checks passed.
"""
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

sys.path.insert(0, ".")

import karma
import karma_dialogue
from combat import hallucination
import facilities.travel_events as travel_events
import facilities.black_market as black_market
import facilities.port as port

failures = []


def check(cond, label):
    if cond:
        print(f"  PASS  {label}")
    else:
        print(f"  FAIL  {label}")
        failures.append(label)


def make_player(karma_value=0, enabled=True, day=5):
    return {
        "karma_enabled": enabled,
        "karma": karma_value,
        "karma_log": [],
        "karma_daily": {"day": day, "gained": 0},
        "karma_gate": {
            "cooldown": {},
            "warning_seen": False,
            "watched_until": 0,
            "jail_karma_day": -99,
            "check_pending": False,
            "atonement_day": -99,
        },
        "day": day,
        "gold": 100,
        "fatigue_stacks": 0,
    }


print("== 1. Hallucination Karma shift ==")
p = make_player(karma_value=0)
p["fatigue_stacks"] = 2
check(hallucination.hallucination_tier(p) == 2, "Neutral Karma keeps stack II at tier 2")

p["karma"] = 50
check(hallucination.hallucination_tier(p) == 1, "+50 Karma softens stack II to tier 1")
p["karma"] = -50
check(hallucination.hallucination_tier(p) == 3, "-50 Karma worsens stack II to tier 3")

p["fatigue_stacks"] = 3
p["karma"] = 50
check(hallucination.hallucination_tier(p) == 2, "+50 Karma softens stack III to tier 2")
p["karma"] = -100
check(hallucination.hallucination_tier(p) == 3, "Low Karma never exceeds tier 3")

p["fatigue_stacks"] = 2
p["karma"] = -100
p["karma_enabled"] = False
check(hallucination.hallucination_tier(p) == 2, "Karma-off saves never shift hallucination tier")

p["karma_enabled"] = True
p["karma"] = -100
p["wonderland_active"] = True
check(hallucination.hallucination_tier(p) == 2,
      "Wonderland ignores the Karma hallucination shift")
p.pop("wonderland_active")
p["dungeon_region"] = "wonderland"
check(hallucination.hallucination_tier(p) == 2,
      "Wonderland region ignores the Karma hallucination shift")
p["wonderland_active"] = True
check(hallucination.should_trigger(p) is False,
      "Wonderland never triggers a hallucination")

import time_blocks as _tb
_orig_stacks = _tb.get_fatigue_stacks
_orig_phase = _tb.get_day_phase
_orig_max = hallucination.player_max_hp
try:
    p = make_player(karma_value=-100)
    p["current_hp"] = 100
    _tb.get_fatigue_stacks = lambda _p: 1
    _tb.get_day_phase = lambda _p: "night"
    hallucination.player_max_hp = lambda _p: 100
    check(hallucination.should_trigger(p) is False,
          "Low Karma cannot trigger a hallucination at stack I")
finally:
    _tb.get_fatigue_stacks = _orig_stacks
    _tb.get_day_phase = _orig_phase
    hallucination.player_max_hp = _orig_max
print()

print("== 2. Karma-tier dialogue ==")
p = make_player(karma_value=0)
check(karma_dialogue.service_line(p, "receptionist", "solmere") is None,
      "Neutral Karma has no tier line")
p["karma"] = 40
check(karma_dialogue.service_line(p, "receptionist", "solmere") is not None,
      "High Karma has a receptionist line")
check(karma_dialogue.service_line(p, "shop", "solmere") is not None,
      "High Karma has a shop line")
p["karma"] = -40
check(karma_dialogue.service_line(p, "guard", "solmere") is not None,
      "Low Karma has a guard line")
check(karma_dialogue.service_line(p, "receptionist", "wonderland") is None,
      "Wonderland has no Karma dialogue")
check(karma_dialogue.service_line(p, "black_market", "blackwake") is not None,
      "Blackwake has a negative-Karma line")
check(karma_dialogue.service_line(p, "inn", "blackwake") is not None,
      "Blackwake has an innkeeper line")
check(karma_dialogue.service_line(p, "inn", "solmere") is None,
      "Non-Blackwake inns stay neutral")
p["karma"] = 40
check(karma_dialogue.service_line(p, "black_market", "blackwake") is not None,
      "Blackwake has a positive-Karma line")
p["karma_enabled"] = False
check(karma_dialogue.service_line(p, "receptionist", "solmere") is None,
      "Karma-off saves have no Karma dialogue")
print()

print("== 3. Travel moral event ==")


class _TermStub:
    def __init__(self, choice=0):
        self.choice = choice
        self.lines = []
        self.options = []

    def clear(self):
        pass

    def print(self, *args):
        self.lines.append(" ".join(str(a) for a in args))

    def pause(self, *args, **kwargs):
        pass

    def menu(self, options, **kwargs):
        self.options = list(options)
        return self.choice


_orig_term = travel_events.term
try:
    p = make_player(karma_value=0)
    stub = _TermStub(choice=0)
    travel_events.term = stub
    travel_events._handle_moral_choice(p, "land")
    check(p["karma"] == 2, "Helping a stranded traveler grants +2 Karma")
    check(stub.options and "Help them" in stub.options[0], "Moral event shows help choice")

    p = make_player(karma_value=-10)
    stub = _TermStub(choice=1)
    travel_events.term = stub
    before = p["gold"]
    travel_events._handle_moral_choice(p, "sea")
    check(p["gold"] > before, "Robbing a castaway grants gold")
    check(p["karma"] == -13, "Robbing a castaway costs -3 Karma")

    p = make_player(karma_value=-10)
    stub = _TermStub(choice=2)
    travel_events.term = stub
    travel_events._handle_moral_choice(p, "land")
    check(p["karma"] == -10, "Walking away does not change Karma")

    p = make_player(karma_value=0)
    p["karma_daily"] = {"day": 5, "gained": 8}
    stub = _TermStub(choice=0)
    travel_events.term = stub
    travel_events._handle_moral_choice(p, "land")
    check(p["karma"] == 0, "Travel kindness respects the shared daily cap")

    p = make_player(karma_value=0, enabled=False)
    stub = _TermStub(choice=0)
    travel_events.term = stub
    travel_events._handle_moral_choice(p, "land")
    check(p["karma"] == 0 and not stub.options,
          "Karma-off saves never see the moral event")

    pool_on = travel_events._event_pool(make_player(enabled=True), "land")
    pool_off = travel_events._event_pool(make_player(enabled=False), "land")
    check(any(e["type"] == "moral" for e in pool_on),
          "Karma-on land pool includes the moral event")
    check(not any(e["type"] == "moral" for e in pool_off),
          "Karma-off land pool excludes the moral event")
finally:
    travel_events.term = _orig_term
print()

print("== 3b. World-map moral dialog ==")
import gui.screens.world_map_screen as world_map_screen
import gui.widgets.confirm_dialog as confirm_dialog_mod

_orig_choice_dialog = confirm_dialog_mod.choice_dialog
try:
    captured = {}

    def _capture_choice(**kwargs):
        captured.update(kwargs)

    confirm_dialog_mod.choice_dialog = _capture_choice

    p = make_player(karma_value=0)
    screen = object.__new__(world_map_screen.WorldMapScreen)
    screen.player = p
    screen.logs = []
    screen._log = lambda message, color=None: screen.logs.append(message)
    screen._resume_anim = lambda: setattr(screen, "resumed", True)

    world_map_screen.WorldMapScreen._handle_moral_gui(
        screen, {"seg": {"type": "land"}}
    )
    check([key for key, _label in captured["options"]] ==
          ["help", "rob", "leave"],
          "World-map moral dialog offers help / rob / leave")
    captured["on_choice"]("help")
    check(p["karma"] == 2, "World-map help grants +2 Karma")
    check(getattr(screen, "resumed", False), "World-map moral dialog resumes travel")

    p = make_player(karma_value=0, enabled=False)
    screen = object.__new__(world_map_screen.WorldMapScreen)
    screen.player = p
    screen.logs = []
    screen._log = lambda message, color=None: screen.logs.append(message)
    screen._resume_anim = lambda: setattr(screen, "resumed", True)
    captured.clear()
    world_map_screen.WorldMapScreen._handle_moral_gui(
        screen, {"seg": {"type": "land"}}
    )
    check(not captured, "Karma-off world-map travel skips the moral dialog")
    check(getattr(screen, "resumed", False),
          "Karma-off world-map travel resumes immediately")
finally:
    confirm_dialog_mod.choice_dialog = _orig_choice_dialog
print()

print("== 4. Black Market outlaw stock ==")
p = make_player(karma_value=-30)
check(black_market._outlaw_stock_available(p, "ashkara") is True,
      "Outlaw stock appears at -25 Karma")
p["karma"] = 0
check(black_market._outlaw_stock_available(p, "ashkara") is False,
      "Outlaw stock is hidden at neutral Karma")
p["karma"] = -30
check(black_market._outlaw_stock_available(p, "wonderland") is False,
      "Outlaw stock is hidden in Wonderland")
p["karma_enabled"] = False
check(black_market._outlaw_stock_available(p, "ashkara") is False,
      "Outlaw stock is hidden when Karma is off")
print()

print("== 4b. Black Market outlaw option ==")
_orig_bm_term = black_market.term
_orig_bm_dialogue = black_market.service_dialogue
_orig_bm_random = black_market.random_equipment
_orig_bm_value = black_market.item_value
_orig_bm_add = black_market.add_item_to_inventory
_orig_bm_advance = black_market.advance_time
try:
    p = make_player(karma_value=-30)
    p["gold"] = 10000
    p["inventory"] = []
    item = {"name": "Outlaw Relic", "type": "equipment", "rarity": "epic"}
    stub = _TermStub(choice=2)
    black_market.term = stub
    black_market.service_dialogue = lambda *a, **k: None
    black_market.random_equipment = lambda rarity=None: item
    black_market.item_value = lambda _item: 20
    black_market.add_item_to_inventory = (
        lambda _p, _i: _p["inventory"].append(_i) or True
    )
    black_market.advance_time = lambda *a, **k: None
    black_market.black_market_service(p, "ashkara")
    check(item in p["inventory"], "Outlaw crate option grants an epic relic")
    check(p["gold"] < 10000, "Outlaw crate option deducts gold")
    check(any("outlaw crate" in opt.lower() for opt in stub.options),
          "Outlaw crate appears in the Black Market menu")
finally:
    black_market.term = _orig_bm_term
    black_market.service_dialogue = _orig_bm_dialogue
    black_market.random_equipment = _orig_bm_random
    black_market.item_value = _orig_bm_value
    black_market.add_item_to_inventory = _orig_bm_add
    black_market.advance_time = _orig_bm_advance
print()

print("== 5. Blackwake smuggler fare ==")
p = make_player(karma_value=-30)
check(port._ticket_cost(p, "blackwake") == 50,
      "Negative Karma gets the Blackwake smuggler fare")
p["karma"] = 30
check(port._ticket_cost(p, "blackwake") == 100,
      "Positive Karma pays the normal Blackwake fare")
p["karma"] = -30
check(port._ticket_cost(p, "solmere") == 100,
      "Smuggler fare is Blackwake-only")
p["karma_enabled"] = False
check(port._ticket_cost(p, "blackwake") == 100,
      "Smuggler fare is hidden when Karma is off")
print()

print("== 6. Arrival helper ==")
p = make_player()
karma.mark_city_arrival(p)
check(p["karma_gate"]["check_pending"] is True,
      "mark_city_arrival sets the one-shot gate flag")
print()

if failures:
    print(f"FAILED: {len(failures)} check(s)")
    for f in failures:
        print("  -", f)
    sys.exit(1)
print("All Karma Phase 3 diagnostics passed.")
