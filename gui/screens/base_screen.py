"""
gui/screens/base_screen.py — Abstract base class for all game screens.

Every screen inherits from BaseScreen and implements build_ui().
Screens are tkinter Frames that fill the content area managed by ScreenManager.
"""

import tkinter as tk
from abc import ABC, abstractmethod

from gui.theme import Theme


class BaseScreen(tk.Frame, ABC):
    """
    Abstract base for all Pandemonium GUI screens.

    Subclasses must implement build_ui() to create their widgets.
    The screen is automatically packed into the ScreenManager's content frame.
    """

    def __init__(self, parent: tk.Widget, screen_manager, **kwargs):
        # Pop custom kwargs before passing to tk.Frame
        self.sm = screen_manager
        self.player = screen_manager.player if screen_manager else None

        super().__init__(
            parent,
            bg=Theme.BG_DARK,
            **kwargs,
        )
        self.build_ui()

    @abstractmethod
    def build_ui(self):
        """Create all widgets for this screen. Must be implemented by subclasses."""
        pass

    # ── Convenience helpers for subclasses ────────────────────────────────────

    def styled_button(self, parent, text, command=None, **extra):
        """Create a consistently-styled Button."""
        defaults = {
            "bg": Theme.BUTTON_BG,
            "fg": Theme.BUTTON_FG,
            "activebackground": Theme.BUTTON_ACTIVE_BG,
            "activeforeground": Theme.BUTTON_ACTIVE_FG,
            "font": Theme.FONT_BOLD,
            "relief": tk.RAISED,
            "borderwidth": 2,
            "cursor": "hand2",
        }
        defaults.update(extra)
        btn = tk.Button(parent, text=text, command=command, **defaults)
        return btn

    def styled_label(self, parent, text, **extra):
        """Create a consistently-styled Label."""
        defaults = {
            "bg": Theme.BG_DARK,
            "fg": Theme.TEXT,
            "font": Theme.FONT,
        }
        defaults.update(extra)
        return tk.Label(parent, text=text, **defaults)

    def styled_frame(self, parent, **extra):
        """Create a consistently-styled Frame."""
        defaults = {"bg": Theme.BG_DARK}
        defaults.update(extra)
        return tk.Frame(parent, **defaults)

    def log(self, message: str):
        """Shorthand to write to the global log panel."""
        if self.sm:
            self.sm.log(message)

    def handle_escape(self):
        """Default: navigate back. Subclasses may override for custom behavior."""
        if self.sm:
            self.sm.go_back()
