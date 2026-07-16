"""
tests/test_phase4.py — Phase 4: Polish verification tests.

Covers:
  - Settings load/save roundtrip
  - All Phase 4 screens import and instantiate
  - apply_death_penalty applies correct penalties
  - Keyboard shortcut support exists in key screens
  - handle_escape exists on all screen classes
  - Splash screen and settings screen exist
"""

import unittest
import tkinter as tk
import os
import tempfile


class TestPhase4Settings(unittest.TestCase):
    """Verify settings persistence."""

    def test_load_defaults(self):
        from gui.settings import load_settings, DEFAULT_SETTINGS
        s = load_settings()
        self.assertIn("font_size", s)
        self.assertIn("window_size", s)
        self.assertEqual(s["font_size"], DEFAULT_SETTINGS["font_size"])

    def test_save_and_reload(self):
        from gui.settings import load_settings, save_settings, DEFAULT_SETTINGS
        import gui.settings as gs
        # Use a temp file
        orig = gs.SETTINGS_FILE
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tf:
                gs.SETTINGS_FILE = tf.name
            test_settings = DEFAULT_SETTINGS.copy()
            test_settings["font_size"] = 14
            save_settings(test_settings)
            loaded = load_settings()
            self.assertEqual(loaded["font_size"], 14)
        finally:
            gs.SETTINGS_FILE = orig
            if os.path.exists(tf.name):
                os.unlink(tf.name)


class TestPhase4DeathPenalty(unittest.TestCase):
    """Verify apply_death_penalty works correctly."""

    def test_penalty_applied(self):
        from utils import apply_death_penalty
        # Use a mock player to avoid save side-effects
        save_file = os.path.join("savefile", "savegame_99.json")
        player = {
            "name": "TestDeath",
            "gold": 1000,
            "save_slot": 99,  # Required by save_game
            "current_hp": 0,
            "location": "dungeon",
            "origin_city": "solmere",
            "allies": [{"name": "Test", "current_hp": 0}],
            "abyss_triple_actions": 5,
            "abyss_tempo_pending": True,
            "saved_dungeon_floor": 5,
            "saved_dungeon_rooms": [],
            "saved_dungeon_room_index": 3,
        }
        try:
            penalty = apply_death_penalty(player)
            # Gold penalty: 20% of 1000 = 200
            self.assertEqual(penalty, 200)
            self.assertEqual(player["gold"], 800)
            self.assertEqual(player["current_hp"], 1)
            self.assertEqual(player["location"], "solmere")
            self.assertEqual(player["allies"][0]["current_hp"], 1)
            self.assertEqual(player.get("abyss_triple_actions", 0), 0)
            self.assertNotIn("saved_dungeon_floor", player)
            self.assertNotIn("saved_dungeon_rooms", player)
            self.assertNotIn("saved_dungeon_room_index", player)
        finally:
            # Clean up test save file
            if os.path.exists(save_file):
                os.unlink(save_file)

    def test_terminal_handler_still_works(self):
        from utils import handle_player_death
        self.assertTrue(callable(handle_player_death))


class TestPhase4Imports(unittest.TestCase):
    """Verify all Phase 4 modules import cleanly."""

    def test_settings_screen_import(self):
        from gui.screens.settings_screen import SettingsScreen
        self.assertTrue(callable(SettingsScreen))

    def test_death_screen_import(self):
        from gui.screens.death_screen import DeathScreen
        self.assertTrue(callable(DeathScreen))

    def test_post_floor_screen_import(self):
        from gui.screens.post_floor_screen import PostFloorScreen
        self.assertTrue(callable(PostFloorScreen))

    def test_splash_screen_import(self):
        from gui.screens.splash_screen import SplashScreen
        self.assertTrue(callable(SplashScreen))

    def test_notification_toast_import(self):
        from gui.widgets.notification_toast import NotificationToast
        self.assertTrue(callable(NotificationToast))

    def test_log_window_import(self):
        from gui.widgets.log_window import LogWindow
        self.assertTrue(callable(LogWindow))

    def test_settings_module_import(self):
        from gui import settings
        self.assertTrue(callable(settings.load_settings))
        self.assertTrue(callable(settings.save_settings))


class TestPhase4Screens(unittest.TestCase):
    """Verify Phase 4 screens instantiate without errors."""

    @classmethod
    def setUpClass(cls):
        cls.root = tk.Tk()
        cls.root.withdraw()
        from gui.screen_manager import ScreenManager
        cls.sm = ScreenManager(cls.root, player={"name": "Test", "gold": 100, "location": "solmere"})

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()

    def test_settings_screen_instantiation(self):
        from gui.screens.settings_screen import SettingsScreen
        s = SettingsScreen(self.root, self.sm)
        self.assertIsNotNone(s)
        s.destroy()

    def test_death_screen_instantiation(self):
        from gui.screens.death_screen import DeathScreen
        s = DeathScreen(self.root, self.sm, floor=7, city_id="solmere")
        self.assertIsNotNone(s)
        s.destroy()

    def test_post_floor_screen_instantiation(self):
        from gui.screens.post_floor_screen import PostFloorScreen
        s = PostFloorScreen(self.root, self.sm, floor=7, loot=["Sword"], xp=500, gold=200)
        self.assertIsNotNone(s)
        s.destroy()

    def test_splash_screen_instantiation(self):
        from gui.screens.splash_screen import SplashScreen
        s = SplashScreen(self.root, self.sm)
        self.assertIsNotNone(s)
        s.destroy()


class TestPhase4KeyboardSupport(unittest.TestCase):
    """Verify handle_escape exists on all key screen classes."""

    @classmethod
    def setUpClass(cls):
        cls.root = tk.Tk()
        cls.root.withdraw()
        from gui.screen_manager import ScreenManager
        cls.sm = ScreenManager(cls.root)

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()

    def test_base_screen_has_handle_escape(self):
        from gui.screens.base_screen import BaseScreen
        self.assertTrue(hasattr(BaseScreen, "handle_escape"))

    def test_combat_screen_has_handle_escape(self):
        from gui.screens.combat_screen import CombatScreen
        self.assertTrue(hasattr(CombatScreen, "handle_escape"))

    def test_city_screen_has_handle_escape(self):
        from gui.screens.city_screen import CityScreen
        self.assertTrue(hasattr(CityScreen, "handle_escape"))

    def test_inventory_screen_has_handle_escape(self):
        from gui.screens.inventory_screen import InventoryScreen
        self.assertTrue(hasattr(InventoryScreen, "handle_escape"))

    def test_facility_screen_has_handle_escape(self):
        from gui.screens.facility_screen import FacilityScreen
        self.assertTrue(hasattr(FacilityScreen, "handle_escape"))

    def test_char_create_screen_has_handle_escape(self):
        from gui.screens.char_create_screen import CharCreateScreen
        self.assertTrue(hasattr(CharCreateScreen, "handle_escape"))

    def test_dungeon_screen_has_handle_escape(self):
        from gui.screens.dungeon_screen import DungeonScreen
        self.assertTrue(hasattr(DungeonScreen, "handle_escape"))

    def test_combat_screen_has_key_binds(self):
        from gui.screens.combat_screen import CombatScreen
        self.assertTrue(hasattr(CombatScreen, "_setup_key_binds"))
        self.assertTrue(hasattr(CombatScreen, "_on_key"))

    def test_app_has_global_bindings(self):
        from gui.app import PandemoniumApp
        self.assertTrue(hasattr(PandemoniumApp, "_setup_global_bindings"))
        self.assertTrue(hasattr(PandemoniumApp, "_on_global_escape"))
        self.assertTrue(hasattr(PandemoniumApp, "_on_inventory_key"))


class TestPhase4Utils(unittest.TestCase):
    """Verify utils changes."""

    def test_apply_death_penalty_exists(self):
        from utils import apply_death_penalty
        self.assertTrue(callable(apply_death_penalty))

    def test_handle_player_death_still_exists(self):
        from utils import handle_player_death
        self.assertTrue(callable(handle_player_death))

    def test_set_font_size_exists(self):
        from gui.theme import set_font_size
        self.assertTrue(callable(set_font_size))

    def test_screen_manager_has_new_methods(self):
        from gui.screen_manager import ScreenManager
        self.assertTrue(hasattr(ScreenManager, "refresh_top_bar"))
        self.assertTrue(hasattr(ScreenManager, "show_toast"))
        self.assertTrue(hasattr(ScreenManager, "_open_log_window"))
        # _log_entries is an instance attribute, verify it's set in __init__
        root = tk.Tk()
        root.withdraw()
        sm = ScreenManager(root)
        self.assertTrue(hasattr(sm, "_log_entries"))
        self.assertIsInstance(sm._log_entries, list)
        root.destroy()


if __name__ == "__main__":
    unittest.main()
