"""
gui/app.py — Main tkinter application class and entry point for GUI mode.

Creates the root window, sets up the ScreenManager, and launches the
first screen (main menu or splash). Manages global keyboard shortcuts
and settings persistence.
"""

import tkinter as tk
from tkinter import font as tkfont

from gui.theme import (
    Theme,
    WINDOW_DEFAULT_SIZE,
    WINDOW_MIN_WIDTH,
    WINDOW_MIN_HEIGHT,
    WINDOW_TITLE,
    set_font_size,
)
from gui.screen_manager import ScreenManager
from gui.settings import load_settings, save_settings


class PandemoniumApp:
    """
    Main application wrapper for the GUI version of Pandemonium.

    Responsibilities:
    - Create and configure the root tk.Tk window
    - Load and apply GUI settings
    - Set up the ScreenManager
    - Register global keyboard shortcuts
    - Show splash screen (optional), then main menu
    - Handle clean shutdown with settings persistence
    """

    def __init__(self, player: dict = None):
        # ── Load settings before window creation ──────────────────────────
        self.settings = load_settings()

        # Apply font size before any widgets are created
        set_font_size(self.settings.get("font_size", 11))

        self.root = tk.Tk()
        self.root.title(WINDOW_TITLE)
        self.root.geometry(self.settings.get("window_size", WINDOW_DEFAULT_SIZE))
        self.root.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.root.configure(bg=Theme.BG_DARK)

        # Suppress known Tkinter internal race-condition errors that occur
        # when after() callbacks fire after a widget's Tcl context is torn down.
        # These are harmless and unrecoverable at the application level.
        def _tk_error_handler(exc_type, exc_val, exc_tb):
            import traceback
            msg = str(exc_val)
            # Known Tcl-level race conditions during widget destruction
            if ("can't delete Tcl command" in msg or
                    "'NoneType' object has no attribute 'remove'" in msg):
                return  # Silently suppress — harmless race condition
            # For everything else, print the full traceback
            traceback.print_exception(exc_type, exc_val, exc_tb)

        self.root.report_callback_exception = _tk_error_handler

        # Restore window position if saved
        pos = self.settings.get("window_position")
        if pos:
            try:
                self.root.geometry(pos)
            except tk.TclError:
                pass

        # Ensure monospace font is available
        self._ensure_monospace_font()

        # Shared game state (None until a save is loaded or character is created)
        self.player = player

        # Screen manager handles all screen transitions
        self.screen_manager = ScreenManager(self.root, player=self.player, settings=self.settings)

        # Register global keyboard shortcuts
        self._setup_global_bindings()

        # Save settings on window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _ensure_monospace_font(self):
        """Pre-load the monospace font family so widgets can reference it."""
        families = tkfont.families(self.root)
        # The Theme module already defines FONT_FAMILY based on platform.

    def _setup_global_bindings(self):
        """Bind global keyboard shortcuts on the root window."""
        if not self.settings.get("keyboard_mode", True):
            return

        self.root.bind("<Escape>", self._on_global_escape)
        self.root.bind("<KeyPress-i>", self._on_inventory_key)
        self.root.bind("<KeyPress-I>", self._on_inventory_key)
        self.root.bind("<Control-q>", lambda e: self._on_close())
        self.root.bind("<Control-Q>", lambda e: self._on_close())

    def _on_global_escape(self, event):
        """Global Escape key handler — delegates to current screen."""
        screen = self.screen_manager.current_screen
        if screen and hasattr(screen, "handle_escape"):
            screen.handle_escape()

    def _on_inventory_key(self, event):
        """Global 'I' key — opens inventory. Uses overlay for DungeonScreen
        to avoid destroying the dungeon thread mid-run.

        NOTE: CityScreen has its own local 'I' handler in _on_city_key,
        so we skip CityScreen here to avoid double-dispatch.
        """
        from gui.screens.dungeon_screen import DungeonScreen
        from gui.screens.inventory_screen import InventoryScreen

        screen = self.screen_manager.current_screen
        if isinstance(screen, DungeonScreen):
            self.screen_manager.push_overlay(
                InventoryScreen,
                is_overlay=True,
            )

    def _on_close(self):
        """Save settings and clean up before closing."""
        try:
            # Capture current window size and position
            geo = self.root.geometry()
            self.settings["window_size"] = geo.split("+")[0] if "+" in geo else geo
            # Save position offset
            parts = geo.split("+")
            if len(parts) >= 3:
                self.settings["window_position"] = f"+{parts[1]}+{parts[2]}"
            save_settings(self.settings)
        except Exception:
            pass
        self.root.destroy()

    def run(self):
        """Start the tkinter main loop. Optionally shows splash screen first."""
        if self.settings.get("show_splash", True):
            from gui.screens.splash_screen import SplashScreen

            def _after_splash():
                from gui.screens.main_menu_screen import MainMenuScreen
                self.screen_manager.switch_to(MainMenuScreen, push_history=False)

            self.screen_manager.switch_to(
                SplashScreen,
                push_history=False,
                on_complete=_after_splash,
            )
        else:
            from gui.screens.main_menu_screen import MainMenuScreen
            self.screen_manager.switch_to(MainMenuScreen, push_history=False)
        self.root.mainloop()


def run_gui(player: dict = None):
    """Convenience entry point: create app and run it."""
    app = PandemoniumApp(player=player)
    app.run()
