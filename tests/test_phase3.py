"""
tests/test_phase3.py — Phase 3 verification tests.

Covers:
  - FacilityScreen imports and basic instantiation
  - InventoryScreen imports and basic instantiation
  - DungeonScreen imports and basic instantiation
  - CityScreen integration (Phase 3 wiring)
  - inventory_ui.py still compiles (no breaking changes)
"""

import unittest
import tkinter as tk


class TestPhase3Imports(unittest.TestCase):
    """Verify all Phase 3 modules import cleanly."""

    def test_facility_screen_import(self):
        from gui.screens.facility_screen import FacilityScreen
        self.assertTrue(callable(FacilityScreen))

    def test_inventory_screen_import(self):
        from gui.screens.inventory_screen import InventoryScreen
        self.assertTrue(callable(InventoryScreen))

    def test_dungeon_screen_import(self):
        from gui.screens.dungeon_screen import DungeonScreen
        self.assertTrue(callable(DungeonScreen))

    def test_city_screen_import(self):
        from gui.screens.city_screen import CityScreen
        self.assertTrue(callable(CityScreen))

    def test_inventory_ui_unchanged(self):
        """inventory_ui.py should still import and provide core functions."""
        from inventory_ui import prompt_acquire_item, _format_equipment_stat_line
        self.assertTrue(callable(prompt_acquire_item))
        self.assertTrue(callable(_format_equipment_stat_line))


class TestPhase3Screens(unittest.TestCase):
    """Verify screen instantiation without tkinter errors."""

    @classmethod
    def setUpClass(cls):
        cls.root = tk.Tk()
        cls.root.withdraw()
        from gui.screen_manager import ScreenManager
        cls.sm = ScreenManager(cls.root)
        # Create a minimal player dict for screens that need it
        cls.sm.player = {
            "name": "TestHero",
            "level": 5,
            "attributes": {
                "Strength": 8, "Constitution": 8, "Dexterity": 5,
                "Learning": 5, "Wisdom": 5, "Charisma": 5,
            },
            "current_hp": 80,
            "gold": 1000,
            "inventory": [],
            "equipped": {},
            "skills": [],
            "allies": [],
            "active_bounties": [],
            "active_buffs": [],
            "city_floors": {"solmere": {"floor": 1, "max_floor": 1}},
            "location": "solmere",
            "origin_city": "solmere",
            "time_minutes": 480,
            "day": 1,
            "houses": {},
        }

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()

    def test_facility_screen_instantiation(self):
        from gui.screens.facility_screen import FacilityScreen

        def dummy_facility(player, city_id):
            return "done"

        screen = FacilityScreen(
            self.sm.content_frame, self.sm,
            title="Test Shop",
            func=dummy_facility,
            func_args=(self.sm.player, "solmere"),
        )
        self.assertIsNotNone(screen)
        self.assertEqual(screen.facility_title, "Test Shop")
        screen.destroy()

    def test_inventory_screen_instantiation(self):
        from gui.screens.inventory_screen import InventoryScreen
        screen = InventoryScreen(self.sm.content_frame, self.sm)
        self.assertIsNotNone(screen)
        screen.destroy()

    def test_dungeon_screen_instantiation(self):
        from gui.screens.dungeon_screen import DungeonScreen
        screen = DungeonScreen(
            self.sm.content_frame, self.sm,
            on_result=lambda r: None,
        )
        self.assertIsNotNone(screen)
        screen.destroy()

    def test_city_screen_instantiation(self):
        from gui.screens.city_screen import CityScreen
        screen = CityScreen(self.sm.content_frame, self.sm)
        self.assertIsNotNone(screen)
        screen.destroy()

    def test_io_redirection_helpers(self):
        """Verify the I/O redirection module functions exist."""
        from gui.screens import facility_screen as fs
        self.assertTrue(callable(fs._redirected_print))
        self.assertTrue(callable(fs._redirected_input))
        self.assertTrue(callable(fs._install_redirects))
        self.assertTrue(callable(fs._uninstall_redirects))


class TestPhase3BackwardsCompatibility(unittest.TestCase):
    """Ensure terminal mode is still intact."""

    def test_dungeon_combat_override_still_exists(self):
        """explore_dungeon still accepts combat_override parameter."""
        import inspect
        from dungeon import explore_dungeon
        sig = inspect.signature(explore_dungeon)
        self.assertIn("combat_override", sig.parameters)

    def test_inventory_ui_data_functions_exist(self):
        """Key inventory functions still exist."""
        from inventory_ui import (
            prompt_acquire_item, _format_equipment_stat_line,
        )
        self.assertTrue(callable(prompt_acquire_item))
        self.assertTrue(callable(_format_equipment_stat_line))


if __name__ == "__main__":
    unittest.main()
