"""
gui/combat/combat_renderer.py — Combat HUD renderer (party vs enemies).

Renders the combat state using HPBar widgets, buff tags, and labels.
Updates dynamically as combat progresses.
"""

import re
import tkinter as tk

from gui.theme import Theme
from gui.widgets.hp_bar import HPBar
from combat.combat_ui import format_combat_hud_data

# Flash feedback colors (turn spotlight / ally under fire)
_FLASH_COLORS = {
    "acting": "#ffd166",
    "hit": "#ff6b6b",
}

# The ENEMIES column always reserves this many entity slots. The box is
# therefore sized for a full 5-enemy wave from the start and keeps that
# height for the whole fight, instead of growing when a 5th enemy spawns
# and shrinking as enemies die (playtest 2026-10-07: "5 enemy can still
# cause the box to widen — default it to 5 entity size").
ENEMY_SLOTS = 5

# Sentinel fed to _update_entity_frame() for a reserved (empty) slot.
_EMPTY_SLOT = {"name": "", "hp": 0, "max_hp": 0, "_empty_slot": True}


def _norm_turn_label(label):
    """'[5] World Serpent' / 'You' → comparable lowercase label.

    The '[N] ' enemy index is deliberately KEPT: two enemies can share a
    name, and only the index tells their entries apart (e.g. '[1] Reality
    Engineer' vs '[3] Reality Engineer').
    """
    if not label:
        return ""
    return re.sub(r"\s+", " ", str(label)).strip().lower()


def _turn_label_name(label):
    """'[5] World Serpent' → 'world serpent' (index stripped)."""
    return re.sub(r"^\[\d+\]\s*", "", _norm_turn_label(label))


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

        # Turn order bar — one label per combatant so the actor currently
        # acting can be highlighted (progresses naturally during the round).
        self.turn_order_bar = tk.Frame(self, bg=Theme.BG_MID)
        self.turn_order_bar.pack(fill=tk.X, pady=(8, 0))
        self._turn_order_labels = []   # raw labels currently displayed
        self._turn_order_tokens = []   # [(normalized_label, label_widget)]

    # ── Public refresh ────────────────────────────────────────────────────────

    def refresh(self, player, enemies, active_ally=None, header="",
                turn_order=None, active_label=None):
        """Redraw the entire HUD from current game state."""
        data = format_combat_hud_data(player, enemies, active_ally=active_ally, header=header)

        # Header
        self.header_label.config(text=data["header"] or "")

        # Party
        self._refresh_column(self.party_col, data["party"], self._party_frames, side="right")

        # Enemies — or Backup Party in switch mode. Both reserve a full
        # 5-slot layout so the box height never changes mid-fight.
        if data.get("switch_mode"):
            self.enemy_col.config(text=" YOUR PARTY [Backup] ", fg=Theme.ACCENT)
            self._refresh_column(self.enemy_col, data["reserve_party"], self._enemy_frames,
                                 side="left", min_slots=ENEMY_SLOTS)
        else:
            self.enemy_col.config(text=" ENEMIES ", fg=Theme.TEXT)
            self._refresh_column(self.enemy_col, data["enemies"], self._enemy_frames,
                                 side="left", min_slots=ENEMY_SLOTS)

        # Turn order — rebuild tokens when the list changes, then re-tint
        self._update_turn_order(turn_order, active_label)

    def _update_turn_order(self, turn_order, active_label=None):
        """Render the turn-order bar; highlight the actor currently acting."""
        labels = [str(c.get("label", "?")) for c in turn_order] if turn_order else []
        if labels != self._turn_order_labels:
            self._turn_order_labels = labels
            for child in self.turn_order_bar.winfo_children():
                child.destroy()
            self._turn_order_tokens = []
            if labels:
                tk.Label(
                    self.turn_order_bar, text="Turn Order:", bg=Theme.BG_MID,
                    fg=Theme.TEXT_DIM, font=Theme.FONT_SMALL,
                ).pack(side=tk.LEFT, padx=(4, 6))
                for i, label in enumerate(labels):
                    if i:
                        tk.Label(
                            self.turn_order_bar, text="→", bg=Theme.BG_MID,
                            fg=Theme.TEXT_DIM, font=Theme.FONT_SMALL,
                        ).pack(side=tk.LEFT, padx=2)
                    token = tk.Label(
                        self.turn_order_bar, text=label, bg=Theme.BG_MID,
                        fg=Theme.TEXT_DIM, font=Theme.FONT_SMALL,
                    )
                    token.pack(side=tk.LEFT, padx=2)
                    self._turn_order_tokens.append((_norm_turn_label(label), token))

        key = _norm_turn_label(active_label)
        # Exact full-label match first: enemy labels carry their own [N] index,
        # so identical enemies ("[1] Reality Engineer" vs "[3] Reality
        # Engineer") highlight one at a time instead of both together.
        matches = [token for norm, token in self._turn_order_tokens
                   if key and norm == key]
        if key and not re.match(r"^\[\d+\]", key) and len(matches) > 1:
            # Index-less key (player / ally / preview names): several identical
            # labels are genuinely ambiguous — light nothing rather than all.
            matches = []
        if not matches and key:
            # Fallback for index-less bars (local preview before the engine's
            # first turn-order line): match the bare name, but only when it is
            # unique — an ambiguous duplicate must light nothing rather than
            # two tokens at once.
            name_key = _turn_label_name(active_label)
            named = [token for norm, token in self._turn_order_tokens
                     if _turn_label_name(norm) == name_key]
            if len(named) == 1:
                matches = named
        matched = {id(t) for t in matches}
        for norm, token in self._turn_order_tokens:
            try:
                token.config(
                    fg=Theme.ACCENT if id(token) in matched else Theme.TEXT_DIM
                )
            except tk.TclError:
                pass

    def _refresh_column(self, parent, entities, frame_cache, side="right", min_slots=0):
        """Render a list of entity dicts into a column.

        min_slots keeps at least that many card slots in the column; slots
        without an entity render blank (no name, HP bar or tags) but keep
        their full height, so the column is pre-sized for the worst case.
        """
        total = max(len(entities), min_slots)

        # Ensure we have enough frames
        while len(frame_cache) < total:
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
        for i in range(total, len(frame_cache)):
            frame_cache[i].pack_forget()

        # Update visible frames (real entity or reserved empty slot)
        for i in range(total):
            entity = entities[i] if i < len(entities) else _EMPTY_SLOT
            self._update_entity_frame(frame_cache[i], entity)
            frame_cache[i].pack(fill=tk.X, padx=6, pady=4)

    def _create_entity_frame(self, parent):
        """Create a reusable frame for one entity."""
        # highlightthickness is reserved for turn/hit flashes: invisible at
        # rest (same color as the background), tinted briefly when the
        # combatant acts or takes a hit.
        frame = tk.Frame(parent, bg=Theme.BG_DARK,
                         highlightthickness=2,
                         highlightbackground=Theme.BG_DARK)

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

        # Crit summary — party members only; shown beside the name (left of the
        # elemental tags) and packed lazily when there is text
        crit_lbl = tk.Label(
            name_frame,
            text="",
            bg=Theme.BG_DARK,
            fg=Theme.TEXT_DIM,
            font=(Theme.FONT_FAMILY, 8),
            anchor=tk.E,
        )

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
            "crit": crit_lbl,
        }
        return frame

    def _update_entity_frame(self, frame, entity):
        w = frame.widgets

        # Reserved empty slot (enemy column pre-sized for a 5-entity wave):
        # render the card blank but keep its full height. The resting
        # highlight is restored so an earlier target-selection outline on
        # this frame can't leak into the empty slot.
        if entity.get("_empty_slot"):
            frame.entity_name = ""
            try:
                frame.config(highlightbackground=Theme.BG_DARK, highlightthickness=2)
            except tk.TclError:
                pass
            w["active"].config(text="")
            w["name"].config(text="", fg=Theme.TEXT, font=Theme.FONT_BOLD)
            w["mg"].config(text="")
            w["elem"].config(text="")
            w["buffs"].config(text="")
            if w["crit"].winfo_manager():
                w["crit"].pack_forget()
            w["hp_bar"].config(bg=Theme.BG_DARK, highlightbackground=Theme.BG_DARK)
            w["hp_bar"].delete("all")
            return

        # Remember the raw name so flash_entity() can find this card
        frame.entity_name = entity.get("name", "")

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

        # HP bar — restore the normal chrome in case this frame previously
        # rendered as a reserved empty slot.
        w["hp_bar"].config(bg=Theme.HP_BAR_EMPTY, highlightbackground=Theme.BORDER)
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

        # Buff tags — the row keeps its space even when empty so every card
        # has a consistent height (collapse experiment reverted 2026-10-04).
        buff_text = entity.get("buff_tags", "").strip()
        w["buffs"].config(text=buff_text)

        # Crit summary (party members only; beside the name, hidden when empty)
        crit_text = entity.get("crit_text", "").strip()
        if crit_text:
            w["crit"].config(text=crit_text)
            if not w["crit"].winfo_manager():
                w["crit"].pack(side=tk.RIGHT, padx=(0, 6))
        elif w["crit"].winfo_manager():
            w["crit"].pack_forget()

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
            # Reserved empty slots have no entity — leave them invisible.
            if not getattr(frame, "entity_name", ""):
                continue
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

    def flash_entity(self, name, kind="acting", party_only=False, duration=650):
        """Briefly outline a combatant's card (turn spotlight / hit pulse).

        Args:
            name: raw entity name as printed by the combat engine.
            kind: "acting" (gold) or "hit" (red).
            party_only: if True, never flash an enemy card (for ally hits).
            duration: how long the tint lasts, in ms.
        Returns True if a visible card matched.
        """
        if not name:
            return False
        color = _FLASH_COLORS.get(kind, _FLASH_COLORS["acting"])
        key = name.strip().lower()
        caches = [self._party_frames]
        if not party_only:
            caches.append(self._enemy_frames)
        for cache in caches:
            for frame in cache:
                if not frame.winfo_manager():
                    continue  # cached but hidden (pack_forget)
                if getattr(frame, "entity_name", "").strip().lower() == key:
                    try:
                        frame.config(highlightbackground=color)
                        self.after(duration, lambda f=frame: self._reset_flash(f))
                    except tk.TclError:
                        pass
                    return True
        return False

    def _reset_flash(self, frame):
        try:
            if frame.winfo_exists():
                frame.config(highlightbackground=Theme.BG_DARK)
        except tk.TclError:
            pass

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

    def show_ally_target_indicators(self, frame_to_badge: dict):
        """Add number badges to party frames for ally target selection.

        Args:
            frame_to_badge: Mapping of party frame index → badge number.
                The badge number is the 1-based position of that member in
                the combat engine's own list ([player] + all allies), which
                can include benched allies that have no HUD frame.
        """
        self._target_labels = getattr(self, '_target_labels', [])
        for frame_idx, badge_num in frame_to_badge.items():
            if 0 <= frame_idx < len(self._party_frames):
                frame = self._party_frames[frame_idx]
                if not frame.winfo_ismapped():
                    continue
                # Set cursor to hand for clickability
                frame.config(cursor="hand2")
                self._set_cursor_recursive(frame, "hand2")
                # Add number badge
                badge = tk.Label(
                    frame,
                    text=f"[{badge_num}]",
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
