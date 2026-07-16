"""
gui/widgets/stat_display.py — Attribute line widget: STR, DEX, CON, etc.

Renders a stat label with breakdown: base + equipment + buff = total.
"""

import tkinter as tk

from gui.theme import Theme


class StatDisplay(tk.Frame):
    """
    A single-line stat display with optional breakdown.

    Usage:
        stat = StatDisplay(parent, name="STR", base=8, equipment=2, buff=1)
        # Renders:  STR: 8 + 2(eq) + 1(buff) = 11
    """

    def __init__(
        self,
        parent,
        name: str,
        base: int = 0,
        equipment: int = 0,
        buff: int = 0,
        show_breakdown: bool = True,
        **kwargs,
    ):
        super().__init__(parent, bg=Theme.BG_DARK, **kwargs)

        self._name = name
        self._base = base
        self._equipment = equipment
        self._buff = buff
        self._show_breakdown = show_breakdown

        self._build()

    def _build(self):
        total = self._base + self._equipment + self._buff

        # Stat name
        tk.Label(
            self,
            text=f"{self._name}:",
            bg=Theme.BG_DARK,
            fg=Theme.TEXT,
            font=Theme.FONT_BOLD,
            width=5,
            anchor="w",
        ).pack(side=tk.LEFT)

        if self._show_breakdown:
            # Base value
            tk.Label(
                self,
                text=str(self._base),
                bg=Theme.BG_DARK,
                fg=Theme.TEXT,
                font=Theme.FONT,
            ).pack(side=tk.LEFT)

            if self._equipment != 0:
                tk.Label(
                    self,
                    text=f" {'+' if self._equipment >= 0 else ''}{self._equipment}(eq)",
                    bg=Theme.BG_DARK,
                    fg=Theme.RARITY_UNCOMMON,
                    font=Theme.FONT_SMALL,
                ).pack(side=tk.LEFT)

            if self._buff != 0:
                tk.Label(
                    self,
                    text=f" {'+' if self._buff >= 0 else ''}{self._buff}(buff)",
                    bg=Theme.BG_DARK,
                    fg=Theme.BUFF_POSITIVE if self._buff >= 0 else Theme.BUFF_NEGATIVE,
                    font=Theme.FONT_SMALL,
                ).pack(side=tk.LEFT)

            tk.Label(
                self,
                text=f" = {total}",
                bg=Theme.BG_DARK,
                fg=Theme.TEXT_HEADER,
                font=Theme.FONT_BOLD,
            ).pack(side=tk.LEFT)
        else:
            tk.Label(
                self,
                text=str(total),
                bg=Theme.BG_DARK,
                fg=Theme.TEXT_HEADER,
                font=Theme.FONT_BOLD,
            ).pack(side=tk.LEFT)

    # ── Public API ────────────────────────────────────────────────────────────

    def update_values(self, base=None, equipment=None, buff=None):
        """Update stat components and redraw."""
        if base is not None:
            self._base = base
        if equipment is not None:
            self._equipment = equipment
        if buff is not None:
            self._buff = buff

        for widget in self.winfo_children():
            widget.destroy()
        self._build()
