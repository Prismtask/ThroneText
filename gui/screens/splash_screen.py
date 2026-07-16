"""
gui/screens/splash_screen.py — Title splash shown on launch.

Displays the game title and subtitle for a brief period before
switching to the main menu. Can be skipped via settings.
"""

import tkinter as tk

from gui.screens.base_screen import BaseScreen
from gui.theme import Theme


class SplashScreen(BaseScreen):
    """Brief title card shown before the main menu."""

    def __init__(self, parent, screen_manager, on_complete=None, **kwargs):
        self._on_complete = on_complete
        super().__init__(parent, screen_manager, **kwargs)

    def build_ui(self):
        self.sm.update_top_bar("")
        self.sm.clear_log()

        # Title
        tk.Label(
            self,
            text="PANDEMONIUM",
            bg=Theme.BG_DARK,
            fg=Theme.ACCENT,
            font=(Theme.FONT_FAMILY, 28, "bold"),
        ).pack(expand=True)

        tk.Label(
            self,
            text="Mystery of the Accord",
            bg=Theme.BG_DARK,
            fg=Theme.TEXT_DIM,
            font=Theme.FONT,
        ).pack()

        # Auto-advance after 2.5 seconds
        self.after(2500, self._finish)

        # Click to skip
        self.bind("<Button-1>", lambda e: self._finish())
        for child in self.winfo_children():
            child.bind("<Button-1>", lambda e: self._finish())

    def _finish(self):
        """Switch to the next screen."""
        if self._on_complete:
            self._on_complete()
