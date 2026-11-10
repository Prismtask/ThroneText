"""Ally reinforcement rule — fallen front allies are replaced by the earliest
living bench ally at the start of every combat round.

Applies to both combat loops:
  * ``combat/combat_engine.py`` (``_combat_inner``) — city/wild/EH/travel fights
  * ``combat/superboss_common.py`` (``superboss_combat_loop``) — superbosses
    incl. the Event Horizon Boss Rush

Run: c:/Code/Pandemonium/.venv/Scripts/python.exe -m pytest tests/test_party_reinforcement.py
"""

import unittest

from combat.ally import (ensure_party_order, get_active_limit,
                         get_bench_limit, reinforce_fallen_allies)
from resources.races_classes import ATTRIBUTES


def make_ally(name, hp=50, max_hp=50, defeated=False):
    return {
        "name": name, "key": "test_girl", "is_ally": True,
        "current_hp": hp, "max_hp": max_hp, "defeated": defeated,
        "attributes": {a: 10 for a in ATTRIBUTES},
        "active_buffs": [], "active_debuffs": [],
    }


def make_player(allies):
    return {
        "name": "Hero", "current_hp": 100, "gold": 0,
        "attributes": {a: 10 for a in ATTRIBUTES},
        "allies": allies,
        "quests": {"resonance_tier": 5},   # 3 front allies / 4 bench slots
        "active_buffs": [], "active_debuffs": [],
    }


def _front_names(p):
    order = p["party_order"]
    return [p["allies"][i]["name"] for i in order[:get_active_limit(p)]]


def _bench_names(p):
    order = p["party_order"]
    limit = get_active_limit(p)
    return [p["allies"][i]["name"]
            for i in order[limit:limit + get_bench_limit(p)]]


class TestReinforceFallen(unittest.TestCase):
    def test_dead_front_swapped_with_earliest_bench(self):
        a, b, c, d = (make_ally(n) for n in "ABCD")
        p = make_player([a, b, c, d])
        b["current_hp"] = 0
        b["defeated"] = True
        msgs = reinforce_fallen_allies(p)
        self.assertEqual(msgs, ["D steps in for the fallen B!"])
        self.assertEqual(_front_names(p), ["A", "D", "C"])
        self.assertEqual(_bench_names(p), ["B"])

    def test_multiple_deaths_pull_bench_in_order(self):
        allies = [make_ally(n) for n in ("A", "B", "C", "D", "E")]
        p = make_player(allies)
        allies[1]["current_hp"] = 0
        allies[1]["defeated"] = True
        allies[2]["current_hp"] = 0
        allies[2]["defeated"] = True
        msgs = reinforce_fallen_allies(p)
        self.assertEqual(len(msgs), 2)
        self.assertIn("D steps in for the fallen B!", msgs)
        self.assertIn("E steps in for the fallen C!", msgs)
        self.assertEqual(sorted(_front_names(p)), ["A", "D", "E"])

    def test_no_living_reserve_no_swap(self):
        allies = [make_ally(n) for n in ("A", "B", "C", "D")]
        p = make_player(allies)
        allies[1]["current_hp"] = 0            # front B fallen
        allies[3]["current_hp"] = 0            # bench D also dead
        msgs = reinforce_fallen_allies(p)
        self.assertEqual(msgs, [])
        self.assertEqual(_front_names(p), ["A", "B", "C"])

    def test_swallowed_ally_with_hp_is_not_swapped(self):
        # Big Bad Wolf SWALLOW: defeated=True but HP intact — a temporary
        # field removal restored in place by the fight. Must NOT be replaced.
        a, b, c, d = (make_ally(n) for n in "ABCD")
        p = make_player([a, b, c, d])
        b["defeated"] = True                   # hp still 50
        msgs = reinforce_fallen_allies(p)
        self.assertEqual(msgs, [])
        self.assertEqual(_front_names(p), ["A", "B", "C"])

    def test_no_deaths_leaves_order_untouched(self):
        allies = [make_ally(n) for n in ("A", "B", "C", "D")]
        p = make_player(allies)
        ensure_party_order(p)
        before = list(p["party_order"])
        msgs = reinforce_fallen_allies(p)
        self.assertEqual(msgs, [])
        self.assertEqual(p["party_order"], before)


if __name__ == "__main__":
    unittest.main()
