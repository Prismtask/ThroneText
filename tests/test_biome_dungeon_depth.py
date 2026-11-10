"""Shared dungeon depth per biome (2026-11-04).

Cities of the same biome are entrances into one dungeon: ``max_floor`` is
shared across the group, while each city keeps its own ``floor`` cursor.
Covers the helpers, the dungeon entry seeding, save migration, and the
consumers that must count unique biomes instead of city records.
"""

import unittest

from leveling import (
    cities_in_biome,
    get_shared_biome_max_floor,
    get_biomes_cleared_to_cap,
    is_pandemonium_unlocked,
    sync_biome_dungeon_depth,
)
from titles import _floors_cleared
from events import check_wonderland_unlock_conditions
from dungeon import _ensure_city_floors, _advance_city_floor


def make_player(city_floors=None, max_floor=1, **extra):
    player = {
        "city_floors": city_floors or {},
        "max_floor": max_floor,
        "inventory": [],
        "day": 1,
    }
    player.update(extra)
    return player


class TestBiomeGroups(unittest.TestCase):

    def test_temperate_group(self):
        self.assertEqual(
            set(cities_in_biome("solmere")),
            {"thornwall", "solmere", "greyharbor"},
        )

    def test_unique_biome_group(self):
        self.assertEqual(cities_in_biome("irondeep"), ["irondeep"])

    def test_shared_depth_is_group_max(self):
        player = make_player({
            "solmere": {"floor": 4, "max_floor": 12},
            "thornwall": {"floor": 1, "max_floor": 5},
        })
        self.assertEqual(get_shared_biome_max_floor(player, "solmere"), 12)
        self.assertEqual(get_shared_biome_max_floor(player, "irondeep"), 1)


class TestSyncMigration(unittest.TestCase):

    def test_sync_raises_same_biome_records_only(self):
        player = make_player({
            "solmere": {"floor": 4, "max_floor": 12},
            "thornwall": {"floor": 1, "max_floor": 5},
            "greyharbor": {"floor": 2, "max_floor": 12},
            "irondeep": {"floor": 3, "max_floor": 3},
            "wonderland": {"floor": 1, "max_floor": 1},
        }, max_floor=3)

        sync_biome_dungeon_depth(player)

        self.assertEqual(player["city_floors"]["solmere"]["max_floor"], 12)
        self.assertEqual(player["city_floors"]["thornwall"]["max_floor"], 12)
        self.assertEqual(player["city_floors"]["greyharbor"]["max_floor"], 12)
        self.assertEqual(player["city_floors"]["irondeep"]["max_floor"], 3)
        self.assertEqual(player["city_floors"]["wonderland"]["max_floor"], 1)
        self.assertEqual(player["max_floor"], 12)
        # Cursors are entrance-local and never changed by a sync.
        self.assertEqual(player["city_floors"]["thornwall"]["floor"], 1)

    def test_sync_idempotent(self):
        player = make_player({
            "solmere": {"floor": 4, "max_floor": 12},
            "thornwall": {"floor": 1, "max_floor": 5},
        }, max_floor=12)
        sync_biome_dungeon_depth(player)
        first = {cid: dict(prog) for cid, prog in player["city_floors"].items()}
        sync_biome_dungeon_depth(player)
        self.assertEqual(player["city_floors"], first)

    def test_sync_handles_bad_values(self):
        player = make_player({
            "solmere": {"floor": 4, "max_floor": "bad"},
            "thornwall": {"floor": 1, "max_floor": 7},
        })
        sync_biome_dungeon_depth(player)
        self.assertEqual(player["city_floors"]["solmere"]["max_floor"], 7)
        self.assertEqual(player["city_floors"]["thornwall"]["max_floor"], 7)


class TestDungeonEntrances(unittest.TestCase):

    def test_new_entrance_inherits_biome_depth(self):
        player = make_player({
            "solmere": {"floor": 2, "max_floor": 12},
        }, max_floor=12)

        _ensure_city_floors(player, "thornwall")

        prog = player["city_floors"]["thornwall"]
        self.assertEqual(prog["floor"], 1)
        self.assertEqual(prog["max_floor"], 12)

    def test_new_entrance_other_biome_starts_at_one(self):
        player = make_player({
            "solmere": {"floor": 2, "max_floor": 12},
        }, max_floor=12)

        _ensure_city_floors(player, "irondeep")

        prog = player["city_floors"]["irondeep"]
        self.assertEqual(prog["floor"], 1)
        self.assertEqual(prog["max_floor"], 1)

    def test_existing_record_is_raised_to_shared_depth(self):
        player = make_player({
            "solmere": {"floor": 2, "max_floor": 12},
            "thornwall": {"floor": 3, "max_floor": 4},
        }, max_floor=12)

        _ensure_city_floors(player, "thornwall")

        self.assertEqual(player["city_floors"]["thornwall"]["max_floor"], 12)
        self.assertEqual(player["city_floors"]["thornwall"]["floor"], 3)

    def test_legacy_empty_city_floors_keeps_global_depth(self):
        player = make_player({}, max_floor=25)
        _ensure_city_floors(player, "solmere")
        self.assertEqual(player["city_floors"]["solmere"]["max_floor"], 25)

    def test_advance_shares_depth_not_cursor(self):
        player = make_player({
            "solmere": {"floor": 12, "max_floor": 12},
            "greyharbor": {"floor": 1, "max_floor": 12},
        }, max_floor=12)

        old_max = _advance_city_floor(
            player, "solmere", player["city_floors"]["solmere"], 13)

        self.assertEqual(old_max, 12)
        self.assertEqual(player["city_floors"]["solmere"]["floor"], 13)
        self.assertEqual(player["city_floors"]["solmere"]["max_floor"], 13)
        self.assertEqual(player["city_floors"]["greyharbor"]["floor"], 1)
        self.assertEqual(player["city_floors"]["greyharbor"]["max_floor"], 13)
        self.assertEqual(player["floor"], 13)
        self.assertEqual(player["max_floor"], 13)


class TestBiomeCountConsumers(unittest.TestCase):

    def test_floors_cleared_counts_each_biome_once(self):
        player = make_player({
            "solmere": {"max_floor": 21},
            "thornwall": {"max_floor": 21},
            "greyharbor": {"max_floor": 21},
            "irondeep": {"max_floor": 6},
            "wonderland": {"max_floor": 1},
        })
        # temperate 20 + mountain 5 (wonderland contributes 0)
        self.assertEqual(_floors_cleared(player), 25)

    def test_wonderland_gate_needs_two_biomes(self):
        player = make_player({
            "solmere": {"max_floor": 20},
            "thornwall": {"max_floor": 20},
            "greyharbor": {"max_floor": 20},
        }, day=60, inventory=[{"id": "looking_glass_shard"}])
        self.assertFalse(check_wonderland_unlock_conditions(player))

        player["city_floors"]["irondeep"] = {"max_floor": 20}
        self.assertTrue(check_wonderland_unlock_conditions(player))

    def test_pandemonium_gate_ignores_duplicate_biomes(self):
        player = make_player({
            "solmere": {"max_floor": 40},
            "thornwall": {"max_floor": 40},
            "greyharbor": {"max_floor": 40},
            "irondeep": {"max_floor": 40},
        })
        self.assertFalse(is_pandemonium_unlocked(player))
        self.assertEqual(len(get_biomes_cleared_to_cap(player, 40)), 2)

        player["city_floors"]["elderfen"] = {"max_floor": 40}
        player["city_floors"]["skylume"] = {"max_floor": 40}
        self.assertTrue(is_pandemonium_unlocked(player))


if __name__ == "__main__":
    unittest.main()
