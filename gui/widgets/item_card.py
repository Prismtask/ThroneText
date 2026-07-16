"""
gui/widgets/item_card.py — Equipment/item display with rarity color coding.

Shows item name, rarity, and stat bonuses in a compact card format.
"""

import tkinter as tk

from gui.theme import Theme


class ItemCard(tk.Frame):
    """
    A compact card representing an item with rarity-colored name and stats.

    Usage:
        card = ItemCard(parent, item={
            "name": "Iron Sword",
            "rarity": "rare",
            "slot": "weapon",
            "stats": {"atk": 5},
            "description": "A sturdy iron blade.",
        })
    """

    def __init__(self, parent, item: dict = None, on_click=None, **kwargs):
        super().__init__(parent, bg=Theme.BG_CARD, **kwargs)

        self.item = item or {}
        self._on_click = on_click

        self.config(
            highlightthickness=1,
            highlightbackground=Theme.BORDER,
            relief=tk.RAISED,
            borderwidth=1,
        )

        self._build()

        if on_click:
            self.bind("<Button-1>", lambda e: on_click(self.item))
            for child in self.winfo_children():
                child.bind("<Button-1>", lambda e: on_click(self.item))

    def _build(self):
        item = self.item
        if not item:
            tk.Label(
                self,
                text="(empty)",
                bg=Theme.BG_CARD,
                fg=Theme.TEXT_DIM,
                font=Theme.FONT,
            ).pack(padx=8, pady=6)
            return

        rarity = item.get("rarity", "common").lower()
        color = Theme.RARITY_COLORS.get(rarity, Theme.RARITY_COMMON)

        # Name row
        name_frame = tk.Frame(self, bg=Theme.BG_CARD)
        name_frame.pack(fill=tk.X, padx=8, pady=(6, 2))

        tk.Label(
            name_frame,
            text=item.get("name", "Unknown Item"),
            bg=Theme.BG_CARD,
            fg=color,
            font=Theme.FONT_BOLD,
        ).pack(side=tk.LEFT)

        tk.Label(
            name_frame,
            text=f"[{rarity.upper()}]",
            bg=Theme.BG_CARD,
            fg=color,
            font=Theme.FONT_SMALL,
        ).pack(side=tk.LEFT, padx=(4, 0))

        # Slot
        slot = item.get("slot", "")
        if slot:
            tk.Label(
                name_frame,
                text=f"({slot})",
                bg=Theme.BG_CARD,
                fg=Theme.TEXT_DIM,
                font=Theme.FONT_SMALL,
            ).pack(side=tk.RIGHT)

        # Stats line
        stats = item.get("stats", {})
        if stats:
            stat_text = " | ".join(f"{k.upper()}: {v:+d}" for k, v in stats.items())
            tk.Label(
                self,
                text=stat_text,
                bg=Theme.BG_CARD,
                fg=Theme.TEXT_DIM,
                font=Theme.FONT_SMALL,
            ).pack(fill=tk.X, padx=8, pady=(0, 2))

        # Elemental Trait line (Phase 4)
        primary_el = item.get("primary_element")
        if primary_el:
            from combat.elemental_traits import ELEMENTAL_TRAITS
            trait_def = ELEMENTAL_TRAITS.get(primary_el, {})
            trait_name = trait_def.get("name", primary_el.title())
            trait_icon = {
                "physical": "⚔️", "fire": "🔥", "water": "💧", "thunder": "⚡",
                "wind": "💨", "earth": "🛡️", "light": "✨", "dark": "🩸", "magical": "🔮",
            }.get(primary_el, "")
            tk.Label(
                self,
                text=f"{trait_icon} {trait_name} ({primary_el.title()})",
                bg=Theme.BG_CARD,
                fg=Theme.TEXT_HEADER,
                font=Theme.FONT_SMALL,
            ).pack(fill=tk.X, padx=8, pady=(0, 2))

        # Description
        desc = item.get("description", "")
        if desc:
            tk.Label(
                self,
                text=desc,
                bg=Theme.BG_CARD,
                fg=Theme.TEXT_DIM,
                font=Theme.FONT_SMALL,
                wraplength=280,
                justify=tk.LEFT,
            ).pack(fill=tk.X, padx=8, pady=(0, 6))

    # ── Public API ────────────────────────────────────────────────────────────

    def update_item(self, item: dict):
        """Replace the displayed item and redraw."""
        self.item = item
        for widget in self.winfo_children():
            widget.destroy()
        self._build()
