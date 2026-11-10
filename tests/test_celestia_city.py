"""Celestia — the northern celestial city and its Floor 30 dungeon (2026-11-04).

Covers the city/world-map data, the Sigil gate, the Floor 30 starting depth,
and the celestial loot/theme tables.
"""

import unittest
from unittest.mock import patch

import dungeon
from dungeon import (
    _ensure_city_floors,
    _advance_city_floor,
    _city_start_floor,
    _grant_celestial_sigil,
    CELESTIAL_START_FLOOR,
)
from resources.cities import CITIES
from resources.items import ITEMS
from resources.item_generation import (
    BASE_FORM_IDS, FORM_WEIGHTS_BY_BIOME, ELEMENT_WEIGHTS_BY_BIOME,
)
from resources.wild_dungeon_themes import WILD_DUNGEON_THEMES
from resources.world_layout import CITY_POSITIONS, REGIONS
from leveling import get_incomplete_biomes
from wild_dungeons import (
    _available_seed_cities,
    _city_accessible,
    ensure_wild_dungeon_state,
    find_nearest_city,
    get_active_dungeons,
    maybe_spawn_cycle,
)


def make_player(city_floors=None, max_floor=1, inventory=None):
    return {
        "city_floors": city_floors or {},
        "max_floor": max_floor,
        "inventory": inventory or [],
    }


class TestCelestiaData(unittest.TestCase):

    def test_city_entry(self):
        city = CITIES["celestia"]
        self.assertEqual(city["name"], "Celestia")
        self.assertEqual(city["biome"], "celestial")
        self.assertEqual(city["entry_item"], "celestial_sigil")
        self.assertEqual(city["dungeon_start_floor"], CELESTIAL_START_FLOOR)
        self.assertIn("shop", city["services"])
        self.assertIn("inn", city["services"])
        self.assertIn("temple", city["services"])

    def test_world_map_placement_is_northern(self):
        self.assertIn("celestia", CITY_POSITIONS)
        self.assertIn("celestia", REGIONS["North"])
        x, y = CITY_POSITIONS["celestia"]
        # North band: above Solmere (y=160) and Stormhold (y=60).
        self.assertLess(y, 60)

    def test_connections_are_bidirectional(self):
        destinations = {
            c["dest"] for c in CITIES["celestia"]["travel"]["connections"]
        }
        self.assertEqual(destinations, {"stormhold", "thornwall"})
        for city_id in destinations:
            neighbours = {
                c["dest"] for c in CITIES[city_id]["travel"]["connections"]
            }
            self.assertIn("celestia", neighbours)

    def test_sigil_item_exists(self):
        item = ITEMS["celestial_sigil"]
        self.assertEqual(item["type"], "key_item")
        self.assertEqual(item["name"], "Celestial Sigil")

    def test_city_map_and_service_positions(self):
        from resources.city_maps import (
            CITY_MAPS, CITY_SERVICE_POSITIONS, verify_all_cities_mapped,
        )
        self.assertIn("celestia", CITY_MAPS)
        positions = CITY_SERVICE_POSITIONS["celestia"]
        for service in CITIES["celestia"]["services"] + ["dungeon"]:
            self.assertIn(service, positions)
        self.assertEqual(verify_all_cities_mapped(CITIES), ["All cities have maps. OK"])


class TestCelestiaDungeon(unittest.TestCase):

    def test_start_floor_is_data_driven(self):
        self.assertEqual(_city_start_floor("celestia"), CELESTIAL_START_FLOOR)
        self.assertEqual(_city_start_floor("solmere"), 1)

    def test_unvisited_celestia_reports_floor_30(self):
        player = make_player()
        player["level_cap"] = 10
        rows = [r for r in get_incomplete_biomes(player)
                if r[0] == "Celestial"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][2], CELESTIAL_START_FLOOR)

    def test_new_entrance_starts_at_floor_30(self):
        player = make_player({"solmere": {"floor": 4, "max_floor": 4}})
        _ensure_city_floors(player, "celestia")
        prog = player["city_floors"]["celestia"]
        self.assertEqual(prog["floor"], CELESTIAL_START_FLOOR)
        self.assertEqual(prog["max_floor"], CELESTIAL_START_FLOOR)

    def test_legacy_celestial_record_is_raised_to_30(self):
        player = make_player({"celestia": {"floor": 1, "max_floor": 1}})
        _ensure_city_floors(player, "celestia")
        prog = player["city_floors"]["celestia"]
        self.assertEqual(prog["floor"], CELESTIAL_START_FLOOR)
        self.assertEqual(prog["max_floor"], CELESTIAL_START_FLOOR)

    def test_sigil_grant_is_idempotent(self):
        player = make_player()
        self.assertTrue(_grant_celestial_sigil(player, announce=False))
        self.assertTrue(any(i.get("id") == "celestial_sigil"
                            for i in player["inventory"]))
        self.assertFalse(_grant_celestial_sigil(player, announce=False))
        self.assertEqual(
            sum(1 for i in player["inventory"]
                if i.get("id") == "celestial_sigil"),
            1,
        )

    def test_crossing_floor_30_requests_sigil(self):
        player = make_player({
            "celestia": {"floor": 29, "max_floor": 29},
        }, max_floor=29)
        calls = []
        original = dungeon._grant_celestial_sigil
        dungeon._grant_celestial_sigil = lambda p, announce=True: calls.append(p)
        try:
            _advance_city_floor(
                player, "celestia", player["city_floors"]["celestia"], 30)
        finally:
            dungeon._grant_celestial_sigil = original
        self.assertEqual(len(calls), 1)

    def test_below_30_does_not_request_sigil(self):
        player = make_player({
            "celestia": {"floor": 28, "max_floor": 28},
        }, max_floor=28)
        calls = []
        original = dungeon._grant_celestial_sigil
        dungeon._grant_celestial_sigil = lambda p, announce=True: calls.append(p)
        try:
            _advance_city_floor(
                player, "celestia", player["city_floors"]["celestia"], 29)
        finally:
            dungeon._grant_celestial_sigil = original
        self.assertEqual(calls, [])


class TestCelestialWildDungeons(unittest.TestCase):

    def test_celestia_seed_requires_sigil(self):
        player = make_player()
        self.assertFalse(_city_accessible(player, "celestia"))
        self.assertTrue(_city_accessible(player, "solmere"))
        self.assertNotIn("celestia", _available_seed_cities(player))

        player["inventory"].append({"id": "celestial_sigil"})
        self.assertTrue(_city_accessible(player, "celestia"))
        self.assertIn("celestia", _available_seed_cities(player))

    def test_hidden_until_sigil(self):
        player = make_player()
        state = ensure_wild_dungeon_state(player)
        state["active"] = [
            {"id": "wild_1", "seed_city": "celestia",
             "nearest_city": "celestia", "biome": "celestial"},
            {"id": "wild_2", "seed_city": "solmere",
             "nearest_city": "solmere", "biome": "temperate"},
        ]
        self.assertEqual([d["id"] for d in get_active_dungeons(player)],
                         ["wild_2"])

        player["inventory"].append({"id": "celestial_sigil"})
        self.assertEqual({d["id"] for d in get_active_dungeons(player)},
                         {"wild_1", "wild_2"})

    def test_nearest_city_respects_allowed(self):
        celestia_center = (
            CITY_POSITIONS["celestia"][0] + 60,
            CITY_POSITIONS["celestia"][1] + 19,
        )
        allowed = {"stormhold", "thornwall"}
        self.assertNotEqual(
            find_nearest_city(celestia_center, allowed=allowed), "celestia")

    def test_spawn_pool_includes_celestia_only_after_sigil(self):
        import wild_dungeons

        player = make_player()
        player["day"] = 7
        captured = {}

        def fake_sample(population, k):
            captured["population"] = list(population)
            return list(population)[:k]

        with patch.object(wild_dungeons.random, "sample", side_effect=fake_sample):
            maybe_spawn_cycle(player)
        self.assertNotIn("celestia", captured["population"])

        player["inventory"].append({"id": "celestial_sigil"})
        player["wild_dungeons"]["last_spawn_day"] = 0
        with patch.object(wild_dungeons.random, "sample", side_effect=fake_sample):
            maybe_spawn_cycle(player)
        self.assertIn("celestia", captured["population"])


class TestCelestialTables(unittest.TestCase):

    def test_form_weights_reference_real_forms(self):
        forms = set(FORM_WEIGHTS_BY_BIOME["celestial"])
        self.assertTrue(forms)
        all_forms = set()
        for ids in BASE_FORM_IDS.values():
            all_forms.update(ids)
        self.assertTrue(forms <= all_forms, forms - all_forms)

    def test_element_weights_present(self):
        weights = ELEMENT_WEIGHTS_BY_BIOME["celestial"]
        self.assertEqual(weights["light"], 3)

    def test_wild_theme_present(self):
        theme = WILD_DUNGEON_THEMES["celestial"]
        self.assertTrue(theme["adjectives"])
        self.assertTrue(theme["ruins"])


if __name__ == "__main__":
    unittest.main()
