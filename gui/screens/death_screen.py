"""
gui/screens/death_screen.py — Player death GUI.

Shown when the player dies in combat or dungeon. Offers clear choices:
continue (with penalties) or quit to main menu.
"""

import tkinter as tk

from gui.screens.base_screen import BaseScreen
from gui.theme import Theme


class DeathScreen(BaseScreen):
    """Screen shown on player death."""

    def __init__(self, parent, screen_manager,
                 floor=None, city_id="solmere",
                 on_continue=None, on_quit=None,
                 death_type="dungeon", **kwargs):
        self.death_floor = floor
        self.death_city = city_id
        self.death_type = death_type
        self.on_continue = on_continue
        self.on_quit = on_quit
        super().__init__(parent, screen_manager, **kwargs)

    def build_ui(self):
        self.sm.update_top_bar("☠ You Died ☠")
        self.sm.clear_log()
        self.sm.root.configure(bg=Theme.BG_DARK)

        container = self.styled_frame(self)
        container.place(relx=0.5, rely=0.45, anchor=tk.CENTER)

        # Skull icon / title with pulse animation
        self.skull_label = tk.Label(
            container,
            text="☠ YOU DIED ☠",
            bg=Theme.BG_DARK,
            fg=Theme.BUFF_NEGATIVE,
            font=(Theme.FONT_FAMILY, 24, "bold"),
        )
        self.skull_label.pack(pady=(0, 16))
        self._pulse_skull(0)

        # Death details
        city_name = self.death_city.replace("_", " ").title()
        if self.death_type == "travel":
            detail = f"You were slain on the road to {city_name}."
        else:
            detail = f"You were slain on Floor {self.death_floor or '?'} of {city_name}."
        tk.Label(
            container,
            text=detail,
            bg=Theme.BG_DARK,
            fg=Theme.TEXT,
            font=Theme.FONT,
        ).pack(pady=(0, 4))

        tk.Label(
            container,
            text="You lost some gold. Time has passed...",
            bg=Theme.BG_DARK,
            fg=Theme.TEXT_DIM,
            font=Theme.FONT_SMALL,
        ).pack(pady=(0, 24))

        # Buttons — hidden initially, revealed after a dramatic pause
        self.btn_frame = tk.Frame(container, bg=Theme.BG_DARK)

        self.continue_btn = self.styled_button(
            self.btn_frame,
            text="Continue",
            command=self._do_continue,
            bg=Theme.ACCENT,
            fg=Theme.TEXT_HEADER,
            width=16,
        )
        self.continue_btn.pack(side=tk.LEFT, padx=8)

        self.quit_btn = self.styled_button(
            self.btn_frame,
            text="Quit to Menu",
            command=self._do_quit,
            width=16,
        )
        self.quit_btn.pack(side=tk.LEFT, padx=8)

        # Reveal buttons after 1.5 second delay for dramatic effect
        self.after(1500, self._reveal_buttons)

    def _pulse_skull(self, step):
        """Animate the skull label with a subtle pulse."""
        if not hasattr(self, 'skull_label'):
            return
        sizes = [24, 26, 28, 26, 24]
        if step < len(sizes):
            try:
                self.skull_label.config(font=(Theme.FONT_FAMILY, sizes[step], "bold"))
            except tk.TclError:
                return
            self.after(200, lambda s=step+1: self._pulse_skull(s))

    def _reveal_buttons(self):
        """Show the action buttons after the dramatic pause."""
        try:
            self.btn_frame.pack()
        except tk.TclError:
            pass

    def _do_continue(self):
        if self.on_continue:
            self.on_continue()
        else:
            # Default: apply death penalty and return to city
            from utils import apply_death_penalty
            apply_death_penalty(self.player)
            from gui.screens.city_screen import CityScreen
            self.sm.switch_to(CityScreen, push_history=False)

    def _do_quit(self):
        if self.on_quit:
            self.on_quit()
        else:
            self.sm.player = None
            from gui.screens.main_menu_screen import MainMenuScreen
            self.sm.switch_to(MainMenuScreen)
