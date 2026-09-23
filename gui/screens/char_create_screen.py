"""
gui/screens/char_create_screen.py — Step-based character creation wizard.

Steps:
  1. Race selection     (cards with descriptions)
  2. Class selection    (cards with descriptions)
  3. Point allocation   (+/- buttons per attribute)
  4. Name & Save Slot   (Entry + dropdown)
"""

import tkinter as tk
from tkinter import ttk

from gui.screens.base_screen import BaseScreen
from gui.theme import Theme
from gui.widgets.confirm_dialog import ok_dialog

from resources.races_classes import RACES, CLASSES, ATTRIBUTES, TOTAL_POINTS
from character import build_character, player_max_hp
from save_load import save_game, list_saves, get_next_free_slot


# ── Stat Tooltip Descriptions ────────────────────────────────────────────────
STAT_TOOLTIPS = {
    "Strength":     "Increases weapon damage.\nEvery 5 points grants +1 flat damage to all attacks.",
    "Constitution": "Increases max HP (+3 per point).\nEvery 5 points reduces damage taken by 1.",
    "Dexterity":    "Increases dodge chance (+4% per 5 pts) and initiative.\nBoosts thrown/utility item damage.",
    "Wisdom":       "Improves all healing (+1 HP per 5 pts).\nContributes to combat initiative rolls.",
    "Learning":     "Increases XP gain (+1% per 5 pts).\nUsed for some weapon and skill scaling.",
    "Charisma":     "Lowers shop prices (up to 40%) and raises sell prices.\nImproves monster capture chance (+2% per 5 pts).",
}


class ToolTip:
    """Simple hover tooltip that appears near the mouse cursor."""

    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        widget.bind("<Enter>", self._show)
        widget.bind("<Leave>", self._hide)

    def _show(self, event=None):
        if self.tip_window:
            return
        x = self.widget.winfo_rootx() + self.widget.winfo_width() + 8
        y = self.widget.winfo_rooty()
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            tw,
            text=self.text,
            justify=tk.LEFT,
            bg="#2a2a4a",
            fg=Theme.TEXT,
            font=Theme.FONT_SMALL,
            relief=tk.SOLID,
            borderwidth=1,
            padx=8,
            pady=6,
        )
        label.pack()

    def _hide(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None


class CharCreateScreen(BaseScreen):
    """Interactive character creation wizard."""

    def build_ui(self):
        self.sm.update_top_bar("Create Character")
        self.sm.clear_log()

        # ── State ──────────────────────────────────────────────────────────────
        self.step = 1
        self.race_key = None
        self.class_key = None
        self.base_attrs = {attr: 0 for attr in ATTRIBUTES}
        self.allocated = {attr: 0 for attr in ATTRIBUTES}
        self.name_var = tk.StringVar()
        self.slot_var = tk.IntVar()

        # ── Main layout ────────────────────────────────────────────────────────
        self.content = self.styled_frame(self)
        self.content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Step header
        self.header = tk.Label(
            self.content,
            text="Step 1/4: Choose Race",
            bg=Theme.BG_DARK,
            fg=Theme.ACCENT,
            font=Theme.FONT_LARGE,
        )
        self.header.pack(pady=(0, 16))

        # Dynamic step container
        self.step_frame = self.styled_frame(self.content)
        self.step_frame.pack(fill=tk.BOTH, expand=True)

        # Navigation buttons
        self.nav_frame = tk.Frame(self.content, bg=Theme.BG_DARK)
        self.nav_frame.pack(fill=tk.X, pady=(16, 0))

        self.back_btn = self.styled_button(
            self.nav_frame,
            text="Back",
            command=self._prev_step,
        )
        self.back_btn.pack(side=tk.LEFT, padx=5)

        self.next_btn = self.styled_button(
            self.nav_frame,
            text="Next",
            command=self._next_step,
            bg=Theme.ACCENT,
            fg=Theme.TEXT_HEADER,
        )
        self.next_btn.pack(side=tk.RIGHT, padx=5)

        self._render_step()

    # ── Step rendering ────────────────────────────────────────────────────────

    def _render_step(self):
        """Clear and rebuild the current step UI."""
        for w in self.step_frame.winfo_children():
            w.destroy()

        if self.step == 1:
            self.header.config(text="Step 1/4: Choose Race")
            self._build_race_selection()
        elif self.step == 2:
            self.header.config(text="Step 2/4: Choose Class")
            self._build_class_selection()
        elif self.step == 3:
            self.header.config(text="Step 3/4: Allocate Points")
            self._build_stat_allocation()
        elif self.step == 4:
            self.header.config(text="Step 4/4: Name & Save Slot")
            self._build_name_slot()

        # Update nav buttons
        self.back_btn.config(state=tk.NORMAL)
        if self.step == 1:
            self.back_btn.config(text="Main Menu")
        else:
            self.back_btn.config(text="Back")
        if self.step == 4:
            self.next_btn.config(text="Create Character", command=self._create_character)
        else:
            self.next_btn.config(text="Next", command=self._next_step)

    # ── Step 1: Race ──────────────────────────────────────────────────────────

    def _build_race_selection(self):
        grid = tk.Frame(self.step_frame, bg=Theme.BG_DARK)
        grid.pack(expand=True)

        self.race_var = tk.StringVar(value=self.race_key or "")

        for idx, (key, data) in enumerate(RACES.items()):
            row, col = divmod(idx, 2)
            card = tk.Frame(
                grid,
                bg=Theme.BG_CARD if self.race_key != key else Theme.BG_LIGHT,
                highlightthickness=2,
                highlightbackground=Theme.BORDER_FOCUS if self.race_key == key else Theme.BORDER,
                relief=tk.RAISED,
                borderwidth=1,
                cursor="hand2",
            )
            card.grid(row=row, column=col, padx=8, pady=6, sticky="nsew")
            card.bind("<Button-1>", lambda e, k=key: self._select_race(k))

            tk.Label(
                card,
                text=data["name"],
                bg=card.cget("bg"),
                fg=Theme.TEXT_HEADER,
                font=Theme.FONT_BOLD,
            ).pack(anchor="w", padx=10, pady=(8, 2))

            mods = data.get("mods", {})
            mod_text = " | ".join(f"{k[:3]} {v:+.0f}" for k, v in mods.items()) if mods else "No modifiers"
            tk.Label(
                card,
                text=mod_text,
                bg=card.cget("bg"),
                fg=Theme.TEXT_DIM,
                font=Theme.FONT_SMALL,
            ).pack(anchor="w", padx=10, pady=(0, 2))

            tk.Label(
                card,
                text=data["desc"],
                bg=card.cget("bg"),
                fg=Theme.TEXT,
                font=Theme.FONT_SMALL,
                wraplength=280,
                justify=tk.LEFT,
            ).pack(anchor="w", padx=10, pady=(0, 8))

            # Make child labels also clickable
            for child in card.winfo_children():
                child.bind("<Button-1>", lambda e, k=key: self._select_race(k))

    def _select_race(self, key):
        self.race_key = key
        self._render_step()

    # ── Step 2: Class ─────────────────────────────────────────────────────────

    def _build_class_selection(self):
        grid = tk.Frame(self.step_frame, bg=Theme.BG_DARK)
        grid.pack(expand=True)

        for idx, (key, data) in enumerate(CLASSES.items()):
            row, col = divmod(idx, 2)
            card = tk.Frame(
                grid,
                bg=Theme.BG_CARD if self.class_key != key else Theme.BG_LIGHT,
                highlightthickness=2,
                highlightbackground=Theme.BORDER_FOCUS if self.class_key == key else Theme.BORDER,
                relief=tk.RAISED,
                borderwidth=1,
                cursor="hand2",
            )
            card.grid(row=row, column=col, padx=8, pady=6, sticky="nsew")
            card.bind("<Button-1>", lambda e, k=key: self._select_class(k))

            tk.Label(
                card,
                text=data["name"],
                bg=card.cget("bg"),
                fg=Theme.TEXT_HEADER,
                font=Theme.FONT_BOLD,
            ).pack(anchor="w", padx=10, pady=(8, 2))

            mods = data.get("mods", {})
            mod_text = " | ".join(f"{k[:3]} {v:+.0f}" for k, v in mods.items()) if mods else "No modifiers"
            tk.Label(
                card,
                text=mod_text,
                bg=card.cget("bg"),
                fg=Theme.TEXT_DIM,
                font=Theme.FONT_SMALL,
            ).pack(anchor="w", padx=10, pady=(0, 2))

            tk.Label(
                card,
                text=data["desc"],
                bg=card.cget("bg"),
                fg=Theme.TEXT,
                font=Theme.FONT_SMALL,
                wraplength=280,
                justify=tk.LEFT,
            ).pack(anchor="w", padx=10, pady=(0, 8))

            for child in card.winfo_children():
                child.bind("<Button-1>", lambda e, k=key: self._select_class(k))

    def _select_class(self, key):
        self.class_key = key
        self._render_step()

    # ── Step 3: Point Allocation ──────────────────────────────────────────────

    def _build_stat_allocation(self):
        # Compute base attrs from race/class
        self.base_attrs = {attr: 0 for attr in ATTRIBUTES}
        race_mods = RACES.get(self.race_key, {}).get("mods", {})
        class_mods = CLASSES.get(self.class_key, {}).get("mods", {})
        for attr, mod in race_mods.items():
            self.base_attrs[attr] += mod
        for attr, mod in class_mods.items():
            self.base_attrs[attr] += mod

        # Reset allocations so going back/forward doesn't preserve old stats
        self.allocated = {attr: 0 for attr in ATTRIBUTES}

        # Remaining points label
        self.remaining_var = tk.IntVar(value=TOTAL_POINTS)
        self.remaining_label = tk.Label(
            self.step_frame,
            text=f"Points remaining: {TOTAL_POINTS}",
            bg=Theme.BG_DARK,
            fg=Theme.ACCENT,
            font=Theme.FONT_BOLD,
        )
        self.remaining_label.pack(pady=(0, 12))

        # Attribute rows
        self.attr_vars = {}
        self.attr_total_labels = {}
        rows_frame = tk.Frame(self.step_frame, bg=Theme.BG_DARK)
        rows_frame.pack()

        for attr in ATTRIBUTES:
            row = tk.Frame(rows_frame, bg=Theme.BG_DARK)
            row.pack(fill=tk.X, pady=4)

            base = self.base_attrs[attr]
            alloc = self.allocated.get(attr, 0)
            total = base + alloc

            attr_label = tk.Label(
                row,
                text=f"{attr[:3].upper()}",
                bg=Theme.BG_DARK,
                fg=Theme.TEXT,
                font=Theme.FONT_BOLD,
                width=6,
                anchor="w",
                cursor="question_arrow",
            )
            attr_label.pack(side=tk.LEFT)
            # Attach tooltip with stat description
            tip_text = STAT_TOOLTIPS.get(attr, "")
            if tip_text:
                ToolTip(attr_label, tip_text)

            tk.Label(
                row,
                text=f"Base: {base}",
                bg=Theme.BG_DARK,
                fg=Theme.TEXT_DIM,
                font=Theme.FONT_SMALL,
                width=8,
            ).pack(side=tk.LEFT, padx=(4, 0))

            minus = self.styled_button(row, text="-", command=lambda a=attr: self._adjust_attr(a, -1))
            minus.config(width=2)
            minus.pack(side=tk.LEFT, padx=4)

            val_label = tk.Label(
                row,
                text=str(alloc),
                bg=Theme.BG_DARK,
                fg=Theme.TEXT_HEADER,
                font=Theme.FONT_BOLD,
                width=3,
            )
            val_label.pack(side=tk.LEFT)
            self.attr_vars[attr] = val_label

            plus = self.styled_button(row, text="+", command=lambda a=attr: self._adjust_attr(a, 1))
            plus.config(width=2)
            plus.pack(side=tk.LEFT, padx=4)

            total_label = tk.Label(
                row,
                text=f"= {total}",
                bg=Theme.BG_DARK,
                fg=Theme.BUFF_POSITIVE,
                font=Theme.FONT_BOLD,
                width=5,
            )
            total_label.pack(side=tk.LEFT, padx=(8, 0))
            self.attr_total_labels[attr] = total_label

    def _adjust_attr(self, attr, delta):
        remaining = self.remaining_var.get()
        current = self.allocated.get(attr, 0)
        if delta > 0 and remaining <= 0:
            return
        if delta < 0 and current <= 0:
            return
        new_alloc = current + delta
        self.allocated[attr] = new_alloc
        self.remaining_var.set(remaining - delta)
        self.remaining_label.config(text=f"Points remaining: {self.remaining_var.get()}")
        self.attr_vars[attr].config(text=str(new_alloc))
        # Update the total (= base + allocated) label dynamically
        new_total = self.base_attrs[attr] + new_alloc
        self.attr_total_labels[attr].config(text=f"= {new_total}")

    # ── Step 4: Name & Slot ───────────────────────────────────────────────────

    def _build_name_slot(self):
        # Name
        name_frame = tk.Frame(self.step_frame, bg=Theme.BG_DARK)
        name_frame.pack(pady=(20, 10))

        tk.Label(
            name_frame,
            text="Character Name:",
            bg=Theme.BG_DARK,
            fg=Theme.TEXT,
            font=Theme.FONT_BOLD,
        ).pack(side=tk.LEFT)

        name_entry = tk.Entry(
            name_frame,
            textvariable=self.name_var,
            bg=Theme.BG_MID,
            fg=Theme.TEXT,
            font=Theme.FONT,
            insertbackground=Theme.TEXT,
            width=24,
        )
        name_entry.pack(side=tk.LEFT, padx=8)
        name_entry.focus()

        # Slot
        slot_frame = tk.Frame(self.step_frame, bg=Theme.BG_DARK)
        slot_frame.pack(pady=10)

        tk.Label(
            slot_frame,
            text="Save Slot:",
            bg=Theme.BG_DARK,
            fg=Theme.TEXT,
            font=Theme.FONT_BOLD,
        ).pack(side=tk.LEFT)

        saves = list_saves()
        next_free = get_next_free_slot()
        self.slot_var.set(next_free)

        slot_options = []
        for s in range(1, max(max(saves.keys(), default=0), next_free) + 3):
            label = f"Slot {s}"
            if s in saves:
                label += f" ({saves[s]})"
            elif s == next_free:
                label += " (new)"
            slot_options.append((label, s))

        slot_combo = ttk.Combobox(
            slot_frame,
            textvariable=self.slot_var,
            values=[s[1] for s in slot_options],
            state="readonly",
            width=20,
        )
        slot_combo.pack(side=tk.LEFT, padx=8)
        # Set display text manually
        slot_combo.set(next_free)

        # Summary
        final_attrs = {attr: self.base_attrs[attr] + self.allocated[attr] for attr in ATTRIBUTES}
        summary = (
            f"Race: {RACES[self.race_key]['name']}  |  "
            f"Class: {CLASSES[self.class_key]['name']}\n"
            f"HP: {player_max_hp(final_attrs)}  |  "
            f"STR {final_attrs['Strength']}  CON {final_attrs['Constitution']}  "
            f"DEX {final_attrs['Dexterity']}  WIS {final_attrs['Wisdom']}  "
            f"LRN {final_attrs['Learning']}  CHA {final_attrs['Charisma']}"
        )
        tk.Label(
            self.step_frame,
            text=summary,
            bg=Theme.BG_DARK,
            fg=Theme.TEXT_DIM,
            font=Theme.FONT_SMALL,
            justify=tk.CENTER,
        ).pack(pady=(20, 0))

    # ── Navigation ────────────────────────────────────────────────────────────

    def _next_step(self):
        if self.step == 1 and not self.race_key:
            ok_dialog(self, "Select Race", "Please choose a race before continuing.")
            return
        if self.step == 2 and not self.class_key:
            ok_dialog(self, "Select Class", "Please choose a class before continuing.")
            return
        self.step += 1
        self._render_step()

    def _prev_step(self):
        if self.step > 1:
            self.step -= 1
            self._render_step()
        else:
            # On step 1, go back to main menu
            self.sm.go_back()

    def handle_escape(self):
        """Override: Esc goes to previous step or back to main menu."""
        self._prev_step()

    def _create_character(self):
        name = self.name_var.get().strip()
        if not name:
            ok_dialog(self, "Name Required", "Please enter a character name.")
            return

        slot = self.slot_var.get()
        saves = list_saves()
        if slot in saves:
            from gui.widgets.confirm_dialog import confirm_dialog
            confirm_dialog(
                parent=self,
                title="Overwrite Save?",
                message=f"Slot {slot} already contains '{saves[slot]}'.\nOverwrite?",
                on_yes=self._do_create,
            )
            return
        self._do_create()

    def _do_create(self):
        name = self.name_var.get().strip()
        slot = self.slot_var.get()
        final_attrs = {attr: self.base_attrs[attr] + self.allocated[attr] for attr in ATTRIBUTES}

        player = build_character(self.race_key, self.class_key, final_attrs, name, slot)
        save_game(player)
        self.sm.player = player
        self.sm.log(f"Character '{name}' created and saved to slot {slot}.")

        # New characters get a short tutorial through the facility UI
        # (the same terminal-style wrapper used by shops, inns, etc.).
        from facilities.tutorial import tutorial_menu, TutorialScreen
        from gui.screens.city_screen import CityScreen
        sm = self.sm
        self.sm.switch_to(
            TutorialScreen,
            push_history=False,
            title="Tutorial",
            func=tutorial_menu,
            func_args=(player,),
            on_close=lambda _result: sm.switch_to(CityScreen, push_history=False),
        )
