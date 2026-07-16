"""
gui/combat/combat_renderer.py — Combat HUD renderer (party vs enemies).

Renders the combat state using HPBar widgets, buff tags, and labels.
Updates dynamically as combat progresses.
"""

import tkinter as tk

from gui.theme import Theme
from gui.widgets.hp_bar import HPBar
from combat.combat_ui import format_combat_hud_data


class CombatRenderer(tk.Frame):
    """
    Displays the combat HUD: left column = party, right column = enemies.
    Call refresh() with the current player / enemy state to update.
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=Theme.BG_DARK, **kwargs)
        self._party_frames = []
        self._enemy_frames = []
        self._click_callback = None  # Stored so new frames get click bindings
        self._build_layout()

    # ── Layout construction ───────────────────────────────────────────────────

    def _build_layout(self):
        # Header label
        self.header_label = tk.Label(
            self,
            text="",
            bg=Theme.BG_DARK,
            fg=Theme.ACCENT,
            font=Theme.FONT_LARGE,
        )
        self.header_label.pack(fill=tk.X, pady=(0, 8))

        # Main columns container
        columns = tk.Frame(self, bg=Theme.BG_DARK)
        columns.pack(fill=tk.BOTH, expand=True)
        columns.grid_columnconfigure(0, weight=1, uniform="col")
        columns.grid_columnconfigure(1, weight=1, uniform="col")

        # Left: Party
        self.party_col = tk.LabelFrame(
            columns,
            text=" YOUR PARTY ",
            bg=Theme.BG_DARK,
            fg=Theme.TEXT,
            font=Theme.FONT_BOLD,
            highlightthickness=1,
            highlightbackground=Theme.BORDER,
        )
        self.party_col.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        # Right: Enemies
        self.enemy_col = tk.LabelFrame(
            columns,
            text=" ENEMIES ",
            bg=Theme.BG_DARK,
            fg=Theme.TEXT,
            font=Theme.FONT_BOLD,
            highlightthickness=1,
            highlightbackground=Theme.BORDER,
        )
        self.enemy_col.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        # Turn order bar
        self.turn_order_label = tk.Label(
            self,
            text="",
            bg=Theme.BG_MID,
            fg=Theme.TEXT_DIM,
            font=Theme.FONT_SMALL,
            anchor=tk.W,
        )
        self.turn_order_label.pack(fill=tk.X, pady=(8, 0))

    # ── Public refresh ────────────────────────────────────────────────────────

    def refresh(self, player, enemies, active_ally=None, header="", turn_order=None):
        """Redraw the entire HUD from current game state."""
        data = format_combat_hud_data(player, enemies, active_ally=active_ally, header=header)

        # Header
        self.header_label.config(text=data["header"] or "")

        # Party
        self._refresh_column(self.party_col, data["party"], self._party_frames, side="right")

        # Enemies — or Backup Party in switch mode
        if data.get("switch_mode"):
            self.enemy_col.config(text=" YOUR PARTY [Backup] ", fg=Theme.ACCENT)
            self._refresh_column(self.enemy_col, data["reserve_party"], self._enemy_frames, side="left")
        else:
            self.enemy_col.config(text=" ENEMIES ", fg=Theme.TEXT)
            self._refresh_column(self.enemy_col, data["enemies"], self._enemy_frames, side="left")

        # Turn order
        if turn_order:
            labels = [c.get("label", "?") for c in turn_order]
            self.turn_order_label.config(text="Turn Order:  " + "  →  ".join(labels))
        else:
            self.turn_order_label.config(text="")

    def _refresh_column(self, parent, entities, frame_cache, side="right"):
        """Render a list of entity dicts into a column."""
        # Ensure we have enough frames
        while len(frame_cache) < len(entities):
            new_frame = self._create_entity_frame(parent)
            frame_cache.append(new_frame)
            idx = len(frame_cache) - 1
            # Bind click on newly created frame if callback is registered
            if self._click_callback is not None and frame_cache is self._enemy_frames:
                self._bind_recursive(new_frame, idx, self._click_callback)
            # Also bind party frames if party click callback is registered
            if getattr(self, '_party_click_callback', None) is not None and frame_cache is self._party_frames:
                self._bind_recursive(new_frame, idx, self._party_click_callback)

        # Hide excess frames
        for i in range(len(entities), len(frame_cache)):
            frame_cache[i].pack_forget()

        # Update visible frames
        for i, entity in enumerate(entities):
            self._update_entity_frame(frame_cache[i], entity)
            frame_cache[i].pack(fill=tk.X, padx=6, pady=4)

    def _create_entity_frame(self, parent):
        """Create a reusable frame for one entity."""
        frame = tk.Frame(parent, bg=Theme.BG_DARK)

        # Name + active indicator
        name_frame = tk.Frame(frame, bg=Theme.BG_DARK)
        name_frame.pack(fill=tk.X)

        active_lbl = tk.Label(
            name_frame,
            text="",
            bg=Theme.BG_DARK,
            fg=Theme.ACCENT,
            font=Theme.FONT_BOLD,
            width=2,
        )
        active_lbl.pack(side=tk.LEFT)

        name_lbl = tk.Label(
            name_frame,
            text="",
            bg=Theme.BG_DARK,
            fg=Theme.TEXT,
            font=Theme.FONT_BOLD,
            anchor=tk.W,
        )
        name_lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)

        mg_lbl = tk.Label(
            name_frame,
            text="",
            bg=Theme.BG_DARK,
            fg=Theme.ACCENT,
            font=Theme.FONT_BOLD,
            width=2,
        )
        mg_lbl.pack(side=tk.RIGHT)

        # Elemental tags (⚔FIR 🛡DAR↑) — beside name, same line
        elem_lbl = tk.Label(
            name_frame,
            text="",
            bg=Theme.BG_DARK,
            fg=Theme.BUFF_NEUTRAL,
            font=(Theme.FONT_FAMILY, 8),
            anchor=tk.W,
        )
        elem_lbl.pack(side=tk.RIGHT, padx=(4, 0))

        # HP bar
        hp_bar = HPBar(frame, current=1, maximum=1, width=140, height=16)
        hp_bar.pack(anchor=tk.W, pady=(2, 0))

        # Buff tags
        buff_lbl = tk.Label(
            frame,
            text="",
            bg=Theme.BG_DARK,
            fg=Theme.BUFF_NEUTRAL,
            font=(Theme.FONT_FAMILY, 8),
            anchor=tk.W,
        )
        buff_lbl.pack(fill=tk.X, pady=(2, 0))

        # Store widgets for later update
        frame.widgets = {
            "active": active_lbl,
            "name": name_lbl,
            "mg": mg_lbl,
            "elem": elem_lbl,
            "hp_bar": hp_bar,
            "buffs": buff_lbl,
        }
        return frame

    def _update_entity_frame(self, frame, entity):
        w = frame.widgets

        # Active indicator
        if entity.get("is_active"):
            w["active"].config(text=">")
        else:
            w["active"].config(text="")

        # Name — indent + dim back-row allies to distinguish from active front row
        name = entity.get("name", "")
        if entity.get("is_back") and not entity.get("is_player"):
            name = f"  {name}"
            w["name"].config(fg=Theme.TEXT_DIM, font=(Theme.FONT_FAMILY, Theme.FONT_SIZE, "italic"))
        else:
            w["name"].config(fg=Theme.TEXT, font=Theme.FONT_BOLD)
        w["name"].config(text=name)

        # Monster girl symbol
        if entity.get("monster_girl"):
            w["mg"].config(text="♀")
        else:
            w["mg"].config(text="")

        # Elemental tags
        elem_text = entity.get("elem_tags", "").strip()
        w["elem"].config(text=elem_text)

        # HP bar
        w["hp_bar"].set_both(entity["hp"], entity["max_hp"])

        # Color HP bar by health %
        ratio = entity["hp"] / max(1, entity["max_hp"])
        if ratio > 0.5:
            w["hp_bar"]._fill_color = Theme.HP_BAR_FILL
        elif ratio > 0.25:
            w["hp_bar"]._fill_color = "#f39c12"  # orange
        else:
            w["hp_bar"]._fill_color = Theme.ACCENT  # red
        w["hp_bar"]._draw()

        # Buff tags
        buff_text = entity.get("buff_tags", "").strip()
        w["buffs"].config(text=buff_text)

    # ── Party click bindings ─────────────────────────────────────────────────

    def bind_party_clicks(self, callback):
        """Store callback and recursively bind click on every party frame + all descendants."""
        self._party_click_callback = callback
        for i, frame in enumerate(self._party_frames):
            if frame:
                self._bind_recursive(frame, i, callback)

    # ── Target selection helpers ──────────────────────────────────────────────

    def clear_target_highlight(self):
        """Remove all target selection highlights from both enemy and party frames."""
        for frame in self._enemy_frames:
            try:
                frame.config(highlightbackground=Theme.BORDER, highlightthickness=1)
            except tk.TclError:
                pass
        for frame in self._party_frames:
            try:
                frame.config(highlightbackground=Theme.BORDER, highlightthickness=1)
            except tk.TclError:
                pass

    def highlight_enemy(self, index):
        """Highlight a specific enemy as a selectable target."""
        if 0 <= index < len(self._enemy_frames):
            self._enemy_frames[index].config(
                highlightbackground=Theme.ACCENT,
                highlightthickness=2,
            )

    def highlight_ally(self, index):
        """Highlight a specific party member as a selectable target."""
        if 0 <= index < len(self._party_frames):
            self._party_frames[index].config(
                highlightbackground=Theme.ACCENT,
                highlightthickness=2,
            )

    def get_enemy_frame(self, index):
        """Return the tk.Frame for an enemy (for binding click events)."""
        if 0 <= index < len(self._enemy_frames):
            return self._enemy_frames[index]
        return None

    def get_party_frame(self, index):
        """Return the tk.Frame for a party member (for binding click events)."""
        if 0 <= index < len(self._party_frames):
            return self._party_frames[index]
        return None

    def bind_enemy_clicks(self, callback):
        """Store callback and recursively bind click on every enemy frame + all descendants."""
        self._click_callback = callback
        for i, frame in enumerate(self._enemy_frames):
            if frame:
                self._bind_recursive(frame, i, callback)

    def _bind_recursive(self, widget, idx, callback):
        """Bind callback to widget and all its descendants recursively."""
        widget.bind("<Button-1>", lambda e, i=idx: callback(i))
        for child in widget.winfo_children():
            self._bind_recursive(child, idx, callback)

    # ── Target selection indicators ──────────────────────────────────────────

    def show_target_indicators(self, indices: list):
        """Add number badges [1] [2] ... to specific enemy frames for target selection.

        Args:
            indices: List of enemy indices (positions in self._enemy_frames) to badge.
                     The badge number is the 1-based position in this list.
        """
        self._target_labels = []
        for badge_num, idx in enumerate(indices):
            if 0 <= idx < len(self._enemy_frames):
                frame = self._enemy_frames[idx]
                if not frame.winfo_ismapped():
                    continue  # Skip hidden frames (dead enemies already pruned from display)
                # Set cursor to hand for clickability
                frame.config(cursor="hand2")
                self._set_cursor_recursive(frame, "hand2")
                # Add number badge
                badge = tk.Label(
                    frame,
                    text=f"[{badge_num + 1}]",
                    bg=Theme.BG_DARK,
                    fg=Theme.ACCENT,
                    font=Theme.FONT_BOLD,
                )
                badge.place(relx=1.0, rely=0.0, anchor=tk.NE, x=-4, y=4)
                self._target_labels.append(badge)

    def show_ally_target_indicators(self, indices: list):
        """Add number badges [1] [2] ... to specific party frames for target selection.

        Args:
            indices: List of party indices (positions in self._party_frames) to badge.
                     The badge number is the 1-based position in this list.
        """
        self._target_labels = getattr(self, '_target_labels', [])
        for badge_num, idx in enumerate(indices):
            if 0 <= idx < len(self._party_frames):
                frame = self._party_frames[idx]
                if not frame.winfo_ismapped():
                    continue
                # Set cursor to hand for clickability
                frame.config(cursor="hand2")
                self._set_cursor_recursive(frame, "hand2")
                # Add number badge
                badge = tk.Label(
                    frame,
                    text=f"[{badge_num + 1}]",
                    bg=Theme.BG_DARK,
                    fg=Theme.ACCENT,
                    font=Theme.FONT_BOLD,
                )
                badge.place(relx=1.0, rely=0.0, anchor=tk.NE, x=-4, y=4)
                self._target_labels.append(badge)

    def hide_target_indicators(self):
        """Remove target number badges and reset cursors."""
        if hasattr(self, '_target_labels') and self._target_labels:
            for badge in self._target_labels:
                try:
                    badge.destroy()
                except tk.TclError:
                    pass
            self._target_labels.clear()
        # Reset cursors on enemy frames
        for frame in self._enemy_frames:
            try:
                frame.config(cursor="")
            except tk.TclError:
                pass
            self._set_cursor_recursive(frame, "")
        # Reset cursors on party frames
        for frame in self._party_frames:
            try:
                frame.config(cursor="")
            except tk.TclError:
                pass
            self._set_cursor_recursive(frame, "")

    def _set_cursor_recursive(self, widget, cursor):
        """Set cursor on a widget and all its descendants."""
        try:
            widget.config(cursor=cursor)
        except tk.TclError:
            pass
        for child in widget.winfo_children():
            self._set_cursor_recursive(child, cursor)
