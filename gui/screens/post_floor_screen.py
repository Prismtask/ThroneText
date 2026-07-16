"""
gui/screens/post_floor_screen.py — Floor cleared rewards GUI.

Shown after defeating a dungeon floor boss. Displays loot summary
and offers choices: continue deeper, return to city, or save & quit.
"""

import tkinter as tk

from gui.screens.base_screen import BaseScreen
from gui.theme import Theme


class PostFloorScreen(BaseScreen):
    """Screen shown after clearing a dungeon floor."""

    def __init__(self, parent, screen_manager,
                 floor=None, loot=None, xp=0, gold=0,
                 on_continue=None, on_return=None, on_save_quit=None, **kwargs):
        self.cleared_floor = floor
        self.loot = loot or []
        self.xp_gained = xp
        self.gold_gained = gold
        self.on_continue = on_continue
        self.on_return = on_return
        self.on_save_quit = on_save_quit
        super().__init__(parent, screen_manager, **kwargs)

    def build_ui(self):
        self.sm.update_top_bar(f"✦ Floor {self.cleared_floor or '?'} Cleared! ✦")
        self.sm.clear_log()

        container = self.styled_frame(self)
        container.place(relx=0.5, rely=0.45, anchor=tk.CENTER)

        # Title
        tk.Label(
            container,
            text=f"✦ Floor {self.cleared_floor or '?'} Cleared! ✦",
            bg=Theme.BG_DARK,
            fg=Theme.BUFF_POSITIVE,
            font=(Theme.FONT_FAMILY, 22, "bold"),
        ).pack(pady=(0, 16))

        # Loot summary
        if self.loot:
            loot_text = "Loot: " + ", ".join(str(l) for l in self.loot)
        else:
            loot_text = "No special loot."

        tk.Label(
            container,
            text=loot_text,
            bg=Theme.BG_DARK,
            fg=Theme.TEXT,
            font=Theme.FONT,
            wraplength=600,
            justify=tk.CENTER,
        ).pack(pady=(0, 4))

        rewards = []
        if self.gold_gained:
            rewards.append(f"{self.gold_gained}g")
        if self.xp_gained:
            rewards.append(f"{self.xp_gained} XP")
        if rewards:
            tk.Label(
                container,
                text=" | ".join(rewards),
                bg=Theme.BG_DARK,
                fg=Theme.BUFF_NEUTRAL,
                font=Theme.FONT_BOLD,
            ).pack(pady=(0, 20))

        # Buttons
        btn_frame = tk.Frame(container, bg=Theme.BG_DARK)
        btn_frame.pack()

        if self.on_continue:
            self.styled_button(
                btn_frame,
                text="Continue to Next Floor",
                command=self._do_continue,
                bg=Theme.ACCENT,
                fg=Theme.TEXT_HEADER,
                width=20,
            ).pack(side=tk.LEFT, padx=6, pady=4)

        if self.on_return:
            self.styled_button(
                btn_frame,
                text="Return to City",
                command=self._do_return,
                width=18,
            ).pack(side=tk.LEFT, padx=6, pady=4)

        if self.on_save_quit:
            self.styled_button(
                btn_frame,
                text="Save & Quit",
                command=self._do_save_quit,
                width=16,
            ).pack(side=tk.LEFT, padx=6, pady=4)

    def _do_continue(self):
        if self.on_continue:
            self.on_continue()
        else:
            self.sm.go_back()

    def _do_return(self):
        if self.on_return:
            self.on_return()
        else:
            from gui.screens.city_screen import CityScreen
            self.sm.switch_to(CityScreen)

    def _do_save_quit(self):
        if self.on_save_quit:
            self.on_save_quit()
        else:
            from save_load import save_game
            if self.player:
                save_game(self.player)
            self.sm.player = None
            from gui.screens.main_menu_screen import MainMenuScreen
            self.sm.switch_to(MainMenuScreen)
