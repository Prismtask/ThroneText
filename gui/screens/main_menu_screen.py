"""
gui/screens/main_menu_screen.py — Main menu: New Game, Continue, Delete Save, Quit.
"""

import tkinter as tk

from gui.screens.base_screen import BaseScreen
from gui.theme import Theme
from gui.widgets.confirm_dialog import confirm_dialog, ok_dialog


class MainMenuScreen(BaseScreen):
    """The game's main menu — first screen shown on launch."""

    def build_ui(self):
        self.sm.clear_history()
        self.sm.player = None
        self.sm.update_top_bar("Pandemonium — Main Menu")
        self.sm.clear_log()

        # ── Center container ───────────────────────────────────────────────────
        container = self.styled_frame(self)
        container.place(relx=0.5, rely=0.45, anchor=tk.CENTER)

        # Title
        tk.Label(
            container,
            text="PANDEMONIUM",
            bg=Theme.BG_DARK,
            fg=Theme.ACCENT,
            font=Theme.FONT_LARGE,
        ).pack(pady=(0, 8))

        tk.Label(
            container,
            text="Mystery of the Accord",
            bg=Theme.BG_DARK,
            fg=Theme.TEXT_DIM,
            font=Theme.FONT_SMALL,
        ).pack(pady=(0, 30))

        # Buttons
        btn_width = 20
        btn_pady = 6

        self.styled_button(
            container,
            text="New Game",
            command=self._on_new_game,
            width=btn_width,
        ).pack(pady=btn_pady)

        self.styled_button(
            container,
            text="Continue",
            command=self._on_continue,
            width=btn_width,
        ).pack(pady=btn_pady)

        self.styled_button(
            container,
            text="Delete Save",
            command=self._on_delete,
            width=btn_width,
        ).pack(pady=btn_pady)

        self.styled_button(
            container,
            text="Settings",
            command=self._on_settings,
            width=btn_width,
        ).pack(pady=btn_pady)

        self.styled_button(
            container,
            text="Changelog",
            command=self._on_changelog,
            width=btn_width,
        ).pack(pady=btn_pady)

        self.styled_button(
            container,
            text="Quit",
            command=self._on_quit,
            width=btn_width,
        ).pack(pady=btn_pady)

        # Version label
        tk.Label(
            container,
            text="v0.1.7.0 — The Chromatic Artisan",
            bg=Theme.BG_DARK,
            fg=Theme.TEXT_DIM,
            font=Theme.FONT_SMALL,
        ).pack(pady=(20, 0))

    # ── Button handlers ───────────────────────────────────────────────────────

    def _on_new_game(self):
        from gui.screens.char_create_screen import CharCreateScreen
        self.sm.switch_to(CharCreateScreen)

    def _on_continue(self):
        self._show_load_dialog()

    def _on_delete(self):
        self._show_delete_dialog()

    def _on_quit(self):
        confirm_dialog(
            parent=self,
            title="Quit Game",
            message="Are you sure you want to quit?",
            on_yes=lambda: self.sm.root.destroy(),
        )

    def _on_settings(self):
        from gui.screens.settings_screen import SettingsScreen
        self.sm.switch_to(SettingsScreen, push_history=True)

    def _on_changelog(self):
        from gui.screens.changelog_screen import ChangelogScreen
        self.sm.switch_to(ChangelogScreen, push_history=True)

    # ── Load dialog ───────────────────────────────────────────────────────────

    def _show_load_dialog(self):
        from save_load import list_saves, load_game
        from character import ensure_player_fields
        from gui.screens.city_screen import CityScreen

        saves = list_saves()
        if not saves:
            ok_dialog(self, "Continue", "No save files found.")
            return

        dialog = tk.Toplevel(self)
        dialog.title("Load Game")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        dialog.resizable(False, False)
        dialog.configure(bg=Theme.BG_DARK)

        dialog.update_idletasks()
        px = self.winfo_toplevel().winfo_x()
        py = self.winfo_toplevel().winfo_y()
        pw = self.winfo_toplevel().winfo_width()
        ph = self.winfo_toplevel().winfo_height()
        dw, dh = 340, 280
        dialog.geometry(f"{dw}x{dh}+{px + (pw - dw) // 2}+{py + (ph - dh) // 2}")

        tk.Label(
            dialog,
            text="Select a save to load:",
            bg=Theme.BG_DARK,
            fg=Theme.TEXT,
            font=Theme.FONT_BOLD,
        ).pack(padx=20, pady=(16, 10))

        list_frame = tk.Frame(dialog, bg=Theme.BG_DARK)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)

        selected_slot = tk.IntVar(value=0)

        for slot, name in sorted(saves.items()):
            row = tk.Frame(list_frame, bg=Theme.BG_DARK)
            row.pack(fill=tk.X, pady=2)
            tk.Radiobutton(
                row,
                text=f"Slot {slot}: {name}",
                variable=selected_slot,
                value=slot,
                bg=Theme.BG_DARK,
                fg=Theme.TEXT,
                selectcolor=Theme.BG_MID,
                activebackground=Theme.BG_DARK,
                font=Theme.FONT,
            ).pack(side=tk.LEFT)

        def _do_load():
            slot = selected_slot.get()
            if slot == 0:
                dialog.destroy()
                return
            player = load_game(slot)
            dialog.destroy()
            if player is None:
                ok_dialog(self, "Error", "Failed to load save file.")
                return
            ensure_player_fields(player)
            self.sm.player = player
            self.sm.log(f"Loaded {player['name']} — {player['race']} {player['class']}")
            self.sm.switch_to(CityScreen)

        tk.Button(
            dialog,
            text="Load",
            command=_do_load,
            width=12,
            bg=Theme.ACCENT,
            fg=Theme.TEXT_HEADER,
            activebackground=Theme.ACCENT_HOVER,
            font=Theme.FONT_BOLD,
            cursor="hand2",
        ).pack(pady=(10, 6))

        tk.Button(
            dialog,
            text="Cancel",
            command=dialog.destroy,
            width=12,
            bg=Theme.BUTTON_BG,
            fg=Theme.TEXT,
            activebackground=Theme.BUTTON_ACTIVE_BG,
            font=Theme.FONT_BOLD,
            cursor="hand2",
        ).pack(pady=(0, 12))

    # ── Delete dialog ─────────────────────────────────────────────────────────

    def _show_delete_dialog(self):
        from save_load import list_saves, delete_save

        saves = list_saves()
        if not saves:
            ok_dialog(self, "Delete Save", "No save files found.")
            return

        dialog = tk.Toplevel(self)
        dialog.title("Delete Save")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        dialog.resizable(False, False)
        dialog.configure(bg=Theme.BG_DARK)

        dialog.update_idletasks()
        px = self.winfo_toplevel().winfo_x()
        py = self.winfo_toplevel().winfo_y()
        pw = self.winfo_toplevel().winfo_width()
        ph = self.winfo_toplevel().winfo_height()
        dw, dh = 340, 280
        dialog.geometry(f"{dw}x{dh}+{px + (pw - dw) // 2}+{py + (ph - dh) // 2}")

        tk.Label(
            dialog,
            text="Select a save to delete:",
            bg=Theme.BG_DARK,
            fg=Theme.ACCENT,
            font=Theme.FONT_BOLD,
        ).pack(padx=20, pady=(16, 10))

        list_frame = tk.Frame(dialog, bg=Theme.BG_DARK)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)

        selected_slot = tk.IntVar(value=0)

        for slot, name in sorted(saves.items()):
            row = tk.Frame(list_frame, bg=Theme.BG_DARK)
            row.pack(fill=tk.X, pady=2)
            tk.Radiobutton(
                row,
                text=f"Slot {slot}: {name}",
                variable=selected_slot,
                value=slot,
                bg=Theme.BG_DARK,
                fg=Theme.TEXT,
                selectcolor=Theme.BG_MID,
                activebackground=Theme.BG_DARK,
                font=Theme.FONT,
            ).pack(side=tk.LEFT)

        def _do_delete():
            slot = selected_slot.get()
            if slot == 0:
                dialog.destroy()
                return
            name = saves.get(slot, "Unknown")

            def _confirmed():
                dialog.destroy()
                if delete_save(slot):
                    ok_dialog(self, "Deleted", f"Save '{name}' (Slot {slot}) deleted.")
                else:
                    ok_dialog(self, "Error", f"Could not delete Slot {slot}.")

            confirm_dialog(
                parent=self,
                title="Confirm Deletion",
                message=f"Permanently delete '{name}' (Slot {slot})?\nThis cannot be undone.",
                on_yes=_confirmed,
                on_no=lambda: None,
            )

        tk.Button(
            dialog,
            text="Delete",
            command=_do_delete,
            width=12,
            bg=Theme.ACCENT,
            fg=Theme.TEXT_HEADER,
            activebackground=Theme.ACCENT_HOVER,
            font=Theme.FONT_BOLD,
            cursor="hand2",
        ).pack(pady=(10, 6))

        tk.Button(
            dialog,
            text="Cancel",
            command=dialog.destroy,
            width=12,
            bg=Theme.BUTTON_BG,
            fg=Theme.TEXT,
            activebackground=Theme.BUTTON_ACTIVE_BG,
            font=Theme.FONT_BOLD,
            cursor="hand2",
        ).pack(pady=(0, 12))
