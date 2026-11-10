"""
tests/test_house_routing.py — House routing regression tests.

Bug history (2026-10-04): get_house_data()/save_house_data() defaulted the
target city to player["origin_city"], which is repointed by travel/dungeon
systems as "nearest city" context. When origin_city held a city without a
house, get_house_data() returned a fresh empty list and save_house_data()
rerouted that empty list onto the first owned house — replacing its
monster_girls and wiping it. Trigger: the barracks skill-teach flow, which
does exactly this read → save cycle after every successful lesson. This cost
savegame_1 its 40-girl Skylume harem.
"""

import unittest

# Make repo root importable when running this file directly (python tests/test_house_routing.py)
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from facilities.house import get_house_data, save_house_data  # noqa: E402


def make_player(origin_city="irondeep"):
    """Player with a home house in skylume and an empty house in sunreach."""
    return {
        "day": 10,
        "origin_city": origin_city,
        "houses": {
            "skylume": {
                "level": 3,
                "storage": [],
                "last_income_day": 1,
                "monster_girls": [
                    {"key": "goblin_girl", "name": "Goblin Girl", "level": 10},
                    {"key": "harpy_scout", "name": "Harpy Scout", "level": 12},
                ],
            },
            "sunreach": {
                "level": 1,
                "storage": [],
                "last_income_day": 1,
                "monster_girls": [],
            },
        },
    }


class HouseRoutingTests(unittest.TestCase):
    """origin_city must never cause a read/write mismatch on the home house."""

    def test_barracks_style_cycle_preserves_girls_when_origin_city_unowned(self):
        # Exact cycle that wiped savegame_1: origin_city points at a city the
        # player has no house in, then a read → save round-trip runs.
        player = make_player(origin_city="irondeep")
        house_data = get_house_data(player)
        self.assertEqual(len(house_data), 2)
        save_house_data(player, house_data)
        self.assertEqual(len(player["houses"]["skylume"]["monster_girls"]), 2)

    def test_get_house_data_returns_the_live_list(self):
        player = make_player()
        house_data = get_house_data(player)
        house_data.append({"key": "slime_girl", "name": "Slime Girl", "level": 1})
        self.assertEqual(len(player["houses"]["skylume"]["monster_girls"]), 3)

    def test_origin_city_house_is_used_when_owned(self):
        player = make_player(origin_city="sunreach")
        self.assertIs(
            get_house_data(player),
            player["houses"]["sunreach"]["monster_girls"],
        )

    def test_explicit_owned_city_is_honored(self):
        player = make_player()
        player["houses"]["sunreach"]["monster_girls"] = [
            {"key": "yuki_onna", "name": "Yuki-onna"}
        ]
        self.assertEqual(get_house_data(player, "sunreach")[0]["key"], "yuki_onna")

    def test_read_and_save_with_same_args_target_same_house(self):
        # Unknown city_id: read and write must resolve to the SAME house.
        player = make_player(origin_city="irondeep")
        house_data = get_house_data(player, city_id="solmere")
        save_house_data(player, house_data, city_id="solmere")
        self.assertEqual(len(player["houses"]["skylume"]["monster_girls"]), 2)

    def test_explicit_replacement_list_is_written(self):
        player = make_player()
        save_house_data(player, [{"key": "oni_bruiser", "name": "Oni Bruiser"}])
        self.assertEqual(
            [g["key"] for g in player["houses"]["skylume"]["monster_girls"]],
            ["oni_bruiser"],
        )

    def test_auto_create_house_only_when_none_owned(self):
        player = {"day": 3, "origin_city": "solmere"}
        save_house_data(player, [{"key": "slime_girl", "name": "Slime Girl"}])
        self.assertEqual(player["houses"]["solmere"]["level"], 1)
        self.assertEqual(len(player["houses"]["solmere"]["monster_girls"]), 1)

    def test_no_house_read_returns_empty_list(self):
        player = {"day": 3, "origin_city": "solmere"}
        self.assertEqual(get_house_data(player), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)