"""
gui/widgets/hp_bar.py — Visual HP/MP/XP bar widget using tkinter Canvas.

More flexible than ttk.Progressbar for custom colors and sizing.
"""

import tkinter as tk

from gui.theme import Theme


class HPBar(tk.Canvas):
    """
    A custom horizontal bar widget for displaying HP, MP, XP, etc.

    Usage:
        bar = HPBar(parent, current=50, maximum=100, width=200, height=20,
                    fill_color=Theme.HP_BAR_FILL, empty_color=Theme.HP_BAR_EMPTY)
        bar.set_value(75)
        bar.set_maximum(150)
    """

    def __init__(
        self,
        parent,
        current: int = 100,
        maximum: int = 100,
        width: int = 200,
        height: int = 20,
        fill_color: str = Theme.HP_BAR_FILL,
        empty_color: str = Theme.HP_BAR_EMPTY,
        text_color: str = Theme.TEXT,
        show_text: bool = True,
        **kwargs,
    ):
        super().__init__(
            parent,
            width=width,
            height=height,
            bg=empty_color,
            highlightthickness=1,
            highlightbackground=Theme.BORDER,
            **kwargs,
        )

        self._current = max(0, current)
        self._maximum = max(1, maximum)
        self._width = width
        self._height = height
        self._fill_color = fill_color
        self._empty_color = empty_color
        self._text_color = text_color
        self._show_text = show_text

        self._draw()

    # ── Core drawing ──────────────────────────────────────────────────────────

    def _draw(self):
        self.delete("all")

        ratio = min(self._current / self._maximum, 1.0)
        fill_width = int(self._width * ratio)

        # Filled portion
        if fill_width > 0:
            self.create_rectangle(
                0, 0, fill_width, self._height,
                fill=self._fill_color,
                outline="",
            )

        # Empty portion outline (subtle)
        if fill_width < self._width:
            self.create_rectangle(
                fill_width, 0, self._width, self._height,
                fill=self._empty_color,
                outline="",
            )

        # Text overlay — left-aligned inside the bar
        if self._show_text:
            text = f"{self._current}/{self._maximum}"
            self.create_text(
                6,
                self._height // 2,
                text=text,
                anchor=tk.W,
                fill=self._text_color,
                font=("Consolas", 9, "bold"),
            )

    # ── Public API ────────────────────────────────────────────────────────────

    def set_value(self, value: int):
        """Update the current value and redraw."""
        self._current = max(0, value)
        self._draw()

    def set_maximum(self, maximum: int):
        """Update the maximum value and redraw."""
        self._maximum = max(1, maximum)
        self._draw()

    def set_both(self, current: int, maximum: int):
        """Update both values and redraw."""
        self._current = max(0, current)
        self._maximum = max(1, maximum)
        self._draw()

    def get_percentage(self) -> float:
        """Return the fill percentage (0.0–100.0)."""
        return (self._current / self._maximum) * 100.0
