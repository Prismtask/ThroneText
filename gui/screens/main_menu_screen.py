"""
gui/screens/main_menu_screen.py — Main menu: New Game, Load Game, Settings, Changelog, Quit.
"""

import tkinter as tk

from gui.screens.base_screen import BaseScreen
from gui.theme import Theme
from gui.widgets.confirm_dialog import confirm_dialog, ok_dialog

from version import VERSION_LABEL


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
            text="Load Game",
            command=self._on_load_game,
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

        # Version label + beta clarifier (single source of truth: version.py)
        tk.Label(
            container,
            text=VERSION_LABEL,
            bg=Theme.BG_DARK,
            fg=Theme.TEXT_DIM,
            font=Theme.FONT_SMALL,
        ).pack(pady=(20, 0))

    # ── Button handlers ───────────────────────────────────────────────────────

    def _on_new_game(self):
        from gui.screens.char_create_screen import CharCreateScreen
        self.sm.switch_to(CharCreateScreen)

    def _on_load_game(self):
        self._show_save_browser()

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

    # ── Save browser (combined Load / Delete) ─────────────────────────────────

    def _show_save_browser(self):
        """Unified, scrollable save browser — click a card, then Load or Delete.

        Replaces the old fixed-height Load/Delete dialogs, whose action buttons
        got squeezed once more than ~4 saves existed.  Every action asks for
        confirmation, and cancelling backs out of the pending action.
        """
        from save_load import list_save_details, load_game, delete_save
        from character import ensure_player_fields
        from gui.screens.city_screen import CityScreen

        if not list_save_details():
            ok_dialog(self, "Save Files", "No save files found.")
            return

        dialog = tk.Toplevel(self)
        dialog.title("Save Files")
        dialog.transient(self.winfo_toplevel())
        dialog.resizable(True, True)
        dialog.configure(bg=Theme.BG_DARK)
        dialog.withdraw()  # build offscreen to avoid a blank flash

        dialog.update_idletasks()
        px = self.winfo_toplevel().winfo_x()
        py = self.winfo_toplevel().winfo_y()
        pw = self.winfo_toplevel().winfo_width()
        ph = self.winfo_toplevel().winfo_height()
        dw, dh = 520, 480
        dialog.geometry(f"{dw}x{dh}+{px + (pw - dw) // 2}+{py + (ph - dh) // 2}")
        dialog.minsize(460, 340)

        tk.Label(
            dialog,
            text="Select a save file:",
            bg=Theme.BG_DARK,
            fg=Theme.TEXT,
            font=Theme.FONT_BOLD,
        ).pack(padx=20, pady=(16, 8))

        # ── Scrollable card list ─────────────────────────────────────────
        list_outer = tk.Frame(dialog, bg=Theme.BG_DARK)
        list_outer.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 8))

        canvas = tk.Canvas(list_outer, bg=Theme.BG_DARK, highlightthickness=0, bd=0)
        scrollbar = tk.Scrollbar(list_outer, orient=tk.VERTICAL, command=canvas.yview)
        cards = tk.Frame(canvas, bg=Theme.BG_DARK)

        window_id = canvas.create_window((0, 0), window=cards, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # The scroll region is anchored at (0, 0) and never shorter than the
        # canvas itself — otherwise a viewport taller than the cards lets the
        # view drift above the first card into empty space (fixed 2026-10-06).
        def _sync_scrollregion(_event=None):
            bbox = canvas.bbox("all")
            if bbox:
                canvas.configure(
                    scrollregion=(0, 0, bbox[2], max(bbox[3], canvas.winfo_height()))
                )

        # Keep cards stretched to the canvas width + refresh the region
        def _on_canvas_configure(event):
            canvas.itemconfigure(window_id, width=event.width)
            _sync_scrollregion()

        cards.bind("<Configure>", _sync_scrollregion)
        canvas.bind("<Configure>", _on_canvas_configure)

        # Mouse-wheel scrolling — bound app-wide while the modal browser is
        # open so it also works over the cards, then unbound on close.
        def _on_mousewheel(event):
            try:
                step = int(-1 * (event.delta / 120))
                first, last = canvas.yview()
                if (step < 0 and first <= 0.0) or (step > 0 and last >= 1.0):
                    return  # already at the top / bottom
                canvas.yview_scroll(step, "units")
            except tk.TclError:
                pass

        dialog.bind_all("<MouseWheel>", _on_mousewheel)

        # ── Action bar (fixed — buttons never shrink with the save count) ─
        action_bar = tk.Frame(dialog, bg=Theme.BG_DARK)
        action_bar.pack(fill=tk.X, padx=20, pady=(0, 14))

        hint = tk.Label(
            action_bar,
            text="Click a save file to load or delete it.",
            bg=Theme.BG_DARK,
            fg=Theme.TEXT_DIM,
            font=Theme.FONT_SMALL,
        )
        hint.pack(side=tk.LEFT)

        state = {"slot": None, "info": {}, "cards": {}}

        def _regrab():
            try:
                dialog.grab_set()
            except tk.TclError:
                pass

        def _close():
            try:
                dialog.unbind_all("<MouseWheel>")
            except tk.TclError:
                pass
            dialog.destroy()

        # ── Actions (each one asks for confirmation / cancel) ────────────
        def _do_load(slot):
            name = state["info"].get(slot, {}).get("name", "Unknown")

            def _confirmed():
                player = load_game(slot)
                if player is None:
                    ok_dialog(self, "Error", f"Failed to load Savefile {slot}.",
                              on_ok=_regrab)
                    return
                _close()
                ensure_player_fields(player)
                self.sm.player = player
                self.sm.log(f"Loaded {player['name']} — {player['race']} {player['class']}")
                self.sm.switch_to(CityScreen)

            confirm_dialog(
                parent=dialog,
                title="Confirm Load",
                message=f"Load '{name}' (Savefile {slot})?",
                on_yes=_confirmed,
                on_no=_regrab,
                yes_text="Load",
                no_text="Cancel",
            )

        def _do_delete(slot):
            name = state["info"].get(slot, {}).get("name", "Unknown")

            def _confirmed():
                if delete_save(slot):
                    _rebuild()
                    _regrab()
                else:
                    ok_dialog(self, "Error", f"Could not delete Savefile {slot}.",
                              on_ok=_regrab)

            confirm_dialog(
                parent=dialog,
                title="Confirm Deletion",
                message=f"Permanently delete '{name}' (Savefile {slot})?\nThis cannot be undone.",
                on_yes=_confirmed,
                on_no=_regrab,
                yes_text="Delete",
                no_text="Cancel",
            )

        # One bottom button: "Close" normally, flips to "Cancel" while a save
        # is selected — cancel backs out of the selection, close shuts the
        # window.  (Escape follows the same rule.)
        def _on_bottom_action():
            if state["slot"] is not None:
                _select(None)
            else:
                _close()

        bottom_btn = tk.Button(
            action_bar, text="Close", command=_on_bottom_action, width=10,
            bg=Theme.BUTTON_BG, fg=Theme.TEXT,
            activebackground=Theme.BUTTON_ACTIVE_BG,
            font=Theme.FONT_BOLD, cursor="hand2",
        )
        bottom_btn.pack(side=tk.RIGHT)

        # ── Selection state ──────────────────────────────────────────────
        def _select(slot):
            state["slot"] = slot
            for s, entry in state["cards"].items():
                if s == slot:
                    entry["card"].configure(highlightbackground=Theme.ACCENT,
                                            highlightthickness=2)
                    entry["slot_lbl"].pack_forget()
                    entry["btn_frame"].pack(anchor=tk.E)
                else:
                    entry["card"].configure(highlightbackground=Theme.BORDER,
                                            highlightthickness=1)
                    entry["btn_frame"].pack_forget()
                    entry["slot_lbl"].pack(anchor=tk.E)
            if slot is None:
                bottom_btn.configure(text="Close")
                hint.configure(text="Click a save file to load or delete it.",
                               fg=Theme.TEXT_DIM)
            else:
                bottom_btn.configure(text="Cancel")
                name = state["info"].get(slot, {}).get("name", "Unknown")
                hint.configure(text=f"Selected: Savefile {slot} — {name}",
                               fg=Theme.TEXT)

        # ── Card rendering ───────────────────────────────────────────────
        def _make_card(slot, info):
            card = tk.Frame(
                cards, bg=Theme.BG_CARD,
                highlightthickness=1, highlightbackground=Theme.BORDER,
                cursor="hand2",
            )
            card.pack(fill=tk.X, pady=4)

            # Right side: "Savefile N" normally, replaced by Load / Delete
            # when this card is selected.  Packed first so the buttons always
            # get their space and can never be squeezed out.
            right = tk.Frame(card, bg=Theme.BG_CARD)
            right.pack(side=tk.RIGHT, anchor=tk.E, padx=(8, 12), pady=6)

            slot_lbl = tk.Label(
                right, text=f"Savefile {slot}",
                bg=Theme.BG_CARD, fg=Theme.TEXT_HEADER, font=Theme.FONT_BOLD,
            )
            slot_lbl.pack(anchor=tk.E)

            btn_frame = tk.Frame(right, bg=Theme.BG_CARD)
            card_load_btn = tk.Button(
                btn_frame, text="Load", command=lambda s=slot: _do_load(s),
                width=6, bg=Theme.ACCENT, fg=Theme.TEXT_HEADER,
                activebackground=Theme.ACCENT_HOVER,
                font=Theme.FONT_BOLD, cursor="hand2",
            )
            card_load_btn.pack(side=tk.LEFT)
            card_delete_btn = tk.Button(
                btn_frame, text="Delete", command=lambda s=slot: _do_delete(s),
                width=7, bg=Theme.BUTTON_BG, fg=Theme.ACCENT,
                activebackground=Theme.BUTTON_ACTIVE_BG,
                activeforeground=Theme.ACCENT_HOVER,
                font=Theme.FONT_BOLD, cursor="hand2",
            )
            card_delete_btn.pack(side=tk.LEFT, padx=(6, 0))

            # Left side: character info (always visible)
            info_frame = tk.Frame(card, bg=Theme.BG_CARD)
            info_frame.pack(side=tk.LEFT, anchor=tk.W, padx=(12, 8), pady=8)
            name_lbl = tk.Label(
                info_frame, text=info["name"],
                bg=Theme.BG_CARD, fg=Theme.TEXT_HEADER, font=Theme.FONT_BOLD,
            )
            name_lbl.pack(anchor=tk.W)
            detail_lbl = tk.Label(
                info_frame,
                text=f"Lv {info['level']}  •  {info['race']}  •  {info['class']}",
                bg=Theme.BG_CARD, fg=Theme.TEXT_DIM, font=Theme.FONT_SMALL,
            )
            detail_lbl.pack(anchor=tk.W)

            # Clicking anywhere on the card toggles selection; clicking the
            # selected card again backs out of the pending action.
            def _click(_event=None, s=slot):
                _select(None if state["slot"] == s else s)

            for widget in (card, info_frame, name_lbl, detail_lbl, slot_lbl):
                widget.bind("<Button-1>", _click)
            state["cards"][slot] = {
                "card": card, "slot_lbl": slot_lbl, "btn_frame": btn_frame,
            }

        def _rebuild():
            state["slot"] = None
            for child in cards.winfo_children():
                child.destroy()
            state["cards"].clear()
            state["info"] = list_save_details()
            for slot in sorted(state["info"]):
                _make_card(slot, state["info"][slot])
            if not state["info"]:
                tk.Label(
                    cards, text="No save files found.",
                    bg=Theme.BG_DARK, fg=Theme.TEXT_DIM, font=Theme.FONT,
                ).pack(pady=24)
            _select(None)
            canvas.yview_moveto(0)

        def _on_escape(_event=None):
            _on_bottom_action()   # Escape = Cancel while selected, else Close

        dialog.protocol("WM_DELETE_WINDOW", _close)
        dialog.bind("<Escape>", _on_escape)

        _rebuild()
        dialog.deiconify()
        dialog.lift()
        dialog.grab_set()
        dialog.focus_set()

