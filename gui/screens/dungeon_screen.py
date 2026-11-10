"""
gui/screens/dungeon_screen.py — Dungeon crawl GUI wrapper.

Runs the dungeon in a background thread with I/O redirected to a GUI panel.
Combat rooms are already handled by the existing CombatScreen via combat_override.
Non-combat rooms, ASCII map, and post-room menus are displayed in the output panel.

This is essentially a FacilityScreen with dungeon-specific branding and an ASCII
map side panel.
"""

import threading
import queue
import time
import tkinter as tk

from gui.screens.facility_screen import FacilityScreen
from gui.theme import Theme
from gui.widgets.confirm_dialog import confirm_dialog
from gui.screens.city_screen import CityScreen
from utils import strip_ansi, display_name


class DungeonScreen(FacilityScreen):
    """
    Dungeon crawl interface.

    Constructor kwargs:
        on_result   — callback(result_str) when dungeon ends
                      ("dead", "fled", "save_exit", or True for success)
    """

    def __init__(self, parent, screen_manager, on_result=None, **kwargs):
        self._on_result = on_result

        # Build the dungeon runner function
        def _run_dungeon():
            from dungeon import explore_dungeon
            return explore_dungeon(self.player, combat_override=self._gui_combat,
                                   superboss_override=self._gui_superboss,
                                   floor_clear_override=self._gui_floor_clear)

        super().__init__(
            parent,
            screen_manager,
            title="Dungeon",
            func=_run_dungeon,
            func_args=(),
            func_kwargs={},
            on_close=self._handle_result,
            **kwargs,
        )

        # Track whether we're in a combat callback
        self._combat_result_queue = None

    def build_ui(self):
        """Override to add a side-by-side layout: map + output."""
        self.sm.clear_log()

        # ── Determine dungeon name and info (city floors vs wild ruin) ───
        origin_city = self.player.get("origin_city", "solmere")
        from resources.cities import CITIES
        city = CITIES.get(origin_city, CITIES["solmere"])
        region = self.player.get("dungeon_region", "temperate")
        self._wild_dungeon = None
        self._eh_run = False
        if self.player.get("_eh_in_run") and (self.player.get("event_horizon") or {}).get("run_active"):
            # Event Horizon: endless rooms (docs/event_horizon_design.md §8)
            import event_horizon as eh
            state = eh.ensure_eh_state(self.player)
            self._eh_run = True
            dungeon_name = "Event Horizon"
            floor = int(state.get("room", 0)) + 1
            max_floor = None
            region = "the Distortion"
            motes = int(state.get("motes", 0))
            if state.get("rush_mode"):
                total = int(state.get("rush_total", 0) or 0)
                felled = total - len(state.get("rush_queue") or [])
                subtitle = f"Space-Time Distortion · Boss Rush {felled}/{total}"
                top_line = f"{dungeon_name} \u2014 Boss Rush {felled}/{total}"
            else:
                subtitle = (f"Space-Time Distortion · Room {floor}"
                            f" · ◎ {motes} Motes")
                top_line = f"{dungeon_name} — Room {floor} · ◎ {motes}"
        elif self.player.get("wild_dungeon_id"):
            from wild_dungeons import get_wild_dungeon
            wild = get_wild_dungeon(self.player, self.player["wild_dungeon_id"])
            if wild:
                self._wild_dungeon = wild
                dungeon_name = wild.get("name", "Wild Dungeon")
                region = wild.get("biome", region)
                floor = int(wild.get("highest_floor_cleared", 0)) + 1
                max_floor = max(1, int(wild.get("total_floors", 1) or 1))
            else:
                dungeon_name = "Wild Dungeon"
                floor, max_floor = 1, 1
            subtitle = f"{region.title()} Region · Floor {floor}"
            top_line = f"{dungeon_name} — Floor {floor}/{max_floor}"
        else:
            dungeon_name = ("Pandemonium" if self.player.get("pandemonium_mode")
                            else f"{city['name']} Dungeon")
            city_prog = self.player.get("city_floors", {}).get(origin_city, {})
            floor = city_prog.get("floor", 1)
            max_floor = city_prog.get("max_floor", 1)
            subtitle = f"{region.title()} Region · Floor {floor}"
            top_line = f"{dungeon_name} — Floor {floor}/{max_floor}"

        # Store for _update_top_bar (called by clock tick)
        self._dungeon_name = dungeon_name
        self._dungeon_floor = floor
        self._dungeon_max_floor = max_floor
        self._dungeon_region = region

        self.sm.update_top_bar(top_line)

        # ── Dungeon info header (shown before the main layout) ───────────
        header_frame = tk.Frame(self, bg=Theme.BG_DARK)
        header_frame.pack(fill=tk.X, padx=10, pady=(10, 0))

        tk.Label(
            header_frame,
            text=dungeon_name.upper(),
            bg=Theme.BG_DARK,
            fg=Theme.ACCENT,
            font=Theme.FONT_LARGE,
        ).pack()

        # Kept as an attribute so _update_top_bar can refresh it — the
        # subtitle is captured at build time, and a run that is resumed
        # (or simply descends) would otherwise keep showing the floor the
        # screen was built on.
        self._subtitle_label = tk.Label(
            header_frame,
            text=subtitle,
            bg=Theme.BG_DARK,
            fg=Theme.TEXT_DIM,
            font=Theme.FONT_SMALL,
        )
        self._subtitle_label.pack(pady=(2, 0))

        # Regional craft signature — favoured forms drop 3x as often here.
        craft_hint = ""
        if not self._eh_run:
            from resources.item_generation import biome_craft_hint
            forms = biome_craft_hint(region)
            if forms:
                craft_hint = f"Local crafts favour {forms}"
        if craft_hint:
            tk.Label(
                header_frame,
                text=craft_hint,
                bg=Theme.BG_DARK,
                fg=Theme.TEXT_DIM,
                font=Theme.FONT_SMALL,
                wraplength=760,
                justify=tk.CENTER,
            ).pack(pady=(1, 0))

        # Log dungeon entry to session log
        if self._eh_run:
            self.sm.log(f"Entering {dungeon_name} — Room {floor} "
                        f"(The Distortion)", category="info")
        else:
            self.sm.log(f"Entering {dungeon_name} — Floor {floor} ({region.title()} Region)", category="info")

        # Main container with two columns
        container = tk.Frame(self, bg=Theme.BG_DARK)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        container.grid_columnconfigure(0, weight=1)  # left panels
        container.grid_columnconfigure(1, weight=3)  # output panel
        container.grid_rowconfigure(0, weight=1)   # main content (map, party, log)
        container.grid_rowconfigure(1, weight=0)   # input / buttons
        container.grid_rowconfigure(2, weight=0)   # action buttons (flee)

        # ── Left column: sub-container for Map (top) + Party Status (bottom) ──
        left_frame = tk.Frame(container, bg=Theme.BG_DARK)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=5)
        left_frame.grid_rowconfigure(0, weight=2)   # Map — smaller
        left_frame.grid_rowconfigure(1, weight=3)   # Party Status — bigger
        left_frame.grid_columnconfigure(0, weight=1)
        left_frame.grid_propagate(False)
        left_width = max(200, Theme.FONT_SIZE * 20)
        left_frame.config(width=left_width)

        # ── Top: Map panel (relabeled "Rift" during Event Horizon runs) ────
        map_frame = tk.LabelFrame(
            left_frame,
            text=(" Rift " if self._eh_run else " Map "),
            bg=Theme.BG_DARK,
            fg=Theme.TEXT,
            font=Theme.FONT_BOLD,
            highlightthickness=1,
            highlightbackground=Theme.BORDER,
        )
        map_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 3))
        map_frame.grid_rowconfigure(0, weight=1)
        map_frame.grid_columnconfigure(0, weight=1)

        self.map_text = tk.Text(
            map_frame,
            wrap=tk.NONE,
            state=tk.DISABLED,
            bg=Theme.BG_DARK,
            fg=Theme.TEXT_DIM,
            font=Theme.FONT,
            width=24,
            height=7,
            highlightthickness=0,
            borderwidth=0,
            padx=4,
            pady=4,
        )
        self.map_text.grid(row=0, column=0, sticky="nsew")

        map_scroll = tk.Scrollbar(map_frame, command=self.map_text.yview, bg=Theme.BG_MID)
        map_scroll.grid(row=0, column=1, sticky="ns")
        self.map_text.config(yscrollcommand=map_scroll.set)

        # ── Bottom: Party Status panel (modern GUI with HP bars) ──────────
        self._party_frame = tk.LabelFrame(
            left_frame,
            text=" Party Status ",
            bg=Theme.BG_DARK,
            fg=Theme.ACCENT,
            font=Theme.FONT_BOLD,
            highlightthickness=1,
            highlightbackground=Theme.BORDER,
        )
        self._party_frame.grid(row=1, column=0, sticky="nsew", pady=(3, 0))
        self._party_frame.grid_rowconfigure(0, weight=1)
        self._party_frame.grid_columnconfigure(0, weight=1)

        # Scrollable canvas for party members
        self._party_canvas = tk.Canvas(
            self._party_frame,
            bg=Theme.BG_DARK,
            highlightthickness=0,
            borderwidth=0,
        )
        self._party_scrollbar = tk.Scrollbar(
            self._party_frame,
            orient=tk.VERTICAL,
            command=self._party_canvas.yview,
            bg=Theme.BG_MID,
            troughcolor=Theme.BG_DARK,
        )
        self._party_canvas.configure(yscrollcommand=self._party_scrollbar.set)
        self._party_canvas.grid(row=0, column=0, sticky="nsew")
        self._party_scrollbar.grid(row=0, column=1, sticky="ns")

        # Inner frame inside canvas — party member widgets go here
        self._party_inner = tk.Frame(self._party_canvas, bg=Theme.BG_DARK)
        self._party_canvas_window = self._party_canvas.create_window(
            (0, 0), window=self._party_inner, anchor=tk.NW, tags="party_inner"
        )

        # Track per-member widget frames for efficient updates
        self._party_member_frames = []
        self._party_member_widgets = []

        # Configure canvas scrolling
        self._party_canvas.bind("<Configure>", self._on_party_canvas_configure)
        self._party_inner.bind("<Configure>", self._on_party_inner_configure)

        # Mouse wheel scrolling over the party panel
        def _party_mousewheel(event):
            self._party_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        self._party_canvas.bind("<Enter>", lambda e: self._party_canvas.bind_all("<MouseWheel>", _party_mousewheel))
        self._party_canvas.bind("<Leave>", lambda e: self._party_canvas.unbind_all("<MouseWheel>"))

        # ── Right: Output panel (same as FacilityScreen) ────────────────────────
        output_frame = tk.LabelFrame(
            container,
            text=" Dungeon Log ",
            bg=Theme.BG_DARK,
            fg=Theme.TEXT,
            font=Theme.FONT_BOLD,
            highlightthickness=1,
            highlightbackground=Theme.BORDER,
        )
        output_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=5)
        output_frame.grid_rowconfigure(0, weight=1)
        output_frame.grid_columnconfigure(0, weight=1)

        self.output_text = tk.Text(
            output_frame,
            wrap=tk.WORD,
            state=tk.DISABLED,
            bg=Theme.BG_DARK,
            fg=Theme.TEXT,
            font=Theme.FONT,
            highlightthickness=0,
            borderwidth=0,
            padx=8,
            pady=8,
        )
        self.output_text.grid(row=0, column=0, sticky="nsew")

        out_scroll = tk.Scrollbar(output_frame, command=self.output_text.yview, bg=Theme.BG_MID)
        out_scroll.grid(row=0, column=1, sticky="ns")
        self.output_text.config(yscrollcommand=out_scroll.set)

        # ── Bottom: Input area ───────────────────────────────────────────────────
        input_frame = tk.Frame(container, bg=Theme.BG_DARK)
        input_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=(0, 5))
        input_frame.grid_columnconfigure(1, weight=1)

        self.prompt_label = tk.Label(
            input_frame,
            text="",
            bg=Theme.BG_DARK,
            fg=Theme.ACCENT,
            font=Theme.FONT_BOLD,
            width=12,
            anchor=tk.W,
        )
        self.prompt_label.grid(row=0, column=0, padx=(0, 5))

        self.input_entry = tk.Entry(
            input_frame,
            bg=Theme.BG_MID,
            fg=Theme.TEXT,
            font=Theme.FONT,
            insertbackground=Theme.TEXT,
            highlightthickness=1,
            highlightbackground=Theme.BORDER,
            highlightcolor=Theme.ACCENT,
            state=tk.DISABLED,
        )
        self.input_entry.grid(row=0, column=1, sticky="ew", padx=5)
        self.input_entry.bind("<Return>", self._on_input_submit)

        self.continue_btn = self.styled_button(
            input_frame,
            text="Continue",
            command=self._on_continue_click,
            width=10,
        )
        self.continue_btn.grid(row=0, column=2, padx=5)
        self.continue_btn.config(state=tk.DISABLED)

        # ── Button panel (for menu choices — replaces text input) ──────────────
        self._button_frame = tk.Frame(container, bg=Theme.BG_DARK)
        self._button_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=5, pady=(0, 5))
        self._button_frame.grid_rowconfigure(1, weight=1)
        self._button_frame.grid_columnconfigure(0, weight=1)
        self._button_prompt = tk.Label(
            self._button_frame,
            text="",
            bg=Theme.BG_DARK,
            fg=Theme.ACCENT,
            font=Theme.FONT_BOLD,
            anchor=tk.W,
        )
        self._button_prompt.grid(row=0, column=0, sticky="ew", padx=5, pady=(2, 4))

        # Scrollable canvas for choice buttons
        self._button_canvas = tk.Canvas(
            self._button_frame,
            bg=Theme.BG_DARK,
            highlightthickness=0,
            borderwidth=0,
            height=180,
        )
        self._button_scrollbar = tk.Scrollbar(
            self._button_frame,
            orient=tk.VERTICAL,
            command=self._button_canvas.yview,
            bg=Theme.BG_MID,
            troughcolor=Theme.BG_DARK,
        )
        self._button_canvas.configure(yscrollcommand=self._button_scrollbar.set)
        self._button_canvas.grid(row=1, column=0, sticky="nsew")
        self._button_scrollbar.grid(row=1, column=1, sticky="ns")

        # Inner container inside the canvas
        self._button_container = tk.Frame(self._button_canvas, bg=Theme.BG_DARK)
        self._button_canvas_window = self._button_canvas.create_window(
            (0, 0), window=self._button_container, anchor=tk.NW, tags="btn_container"
        )

        # Cancel button area (outside scroll, always visible)
        self._cancel_frame = tk.Frame(self._button_frame, bg=Theme.BG_DARK)
        self._cancel_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(4, 0))
        self._cancel_frame.grid_remove()

        # Bind canvas resize to update inner container width
        self._button_canvas.bind("<Configure>", self._on_button_canvas_configure)
        self._button_container.bind("<Configure>", self._on_button_container_configure)

        # Mouse wheel scrolling
        self._button_canvas.bind("<Enter>", lambda e: self._bind_mousewheel(e))
        self._button_canvas.bind("<Leave>", lambda e: self._unbind_mousewheel(e))

        self._button_frame.grid_remove()  # Hidden by default

        # Action buttons
        action_frame = tk.Frame(container, bg=Theme.BG_DARK)
        action_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

        self.back_btn = self.styled_button(
            action_frame,
            text=("\u2190 Leave Rift" if self._eh_run
                  else "\u2190 Flee to City"),
            command=self._on_flee,
            width=16,
        )
        self.back_btn.pack(side=tk.LEFT)

        # ── Keyboard shortcuts ──────────────────────────────────────────────────
        self.bind("<KeyPress-f>", self._on_flee_key)
        self.bind("<KeyPress-F>", self._on_flee_key)
        # Permanent <KeyPress> handler + focus (same pattern as CityScreen / CombatScreen)
        self._setup_facility_keys()

        # ── Override the facility thread start ───────────────────────────────────
        self._start_facility()

        # ── Restore saved dungeon log from previous sessions ────────────────────
        saved_log = self.player.get("_dungeon_log", [])
        if saved_log:
            self.output_text.config(state=tk.NORMAL)
            for line in saved_log:
                self.output_text.insert(tk.END, strip_ansi(line) + "\n")
            self.output_text.see(tk.END)
            self.output_text.config(state=tk.DISABLED)

    def _set_subtitle(self, text):
        """Refresh the header subtitle (floor/room line)."""
        label = getattr(self, "_subtitle_label", None)
        if label is None:
            return
        try:
            label.config(text=text)
        except tk.TclError:
            pass  # Screen torn down

    def _update_top_bar(self):
        """Refresh the dungeon header (time spends / screen builds)."""
        p = self.player
        if not p:
            return
        from time_blocks import format_block_track
        track = format_block_track(p, include_day=False)
        # Event Horizon: endless room counter + motes (no floors)
        if getattr(self, "_eh_run", False):
            import event_horizon as eh
            state = eh.ensure_eh_state(p)
            motes = int(state.get("motes", 0))
            if state.get("rush_mode"):
                total = int(state.get("rush_total", 0) or 0)
                felled = total - len(state.get("rush_queue") or [])
                self._set_subtitle(
                    f"Space-Time Distortion \u00b7 Boss Rush {felled}/{total}")
                rush_top = f"{self._dungeon_name} \u2014 Boss Rush {felled}/{total}"
                if track:
                    rush_top += f" | {track}"
                self.sm.update_top_bar(rush_top)
                return
            room = int(state.get("room", 0)) + 1
            self._set_subtitle(
                f"Space-Time Distortion \u00b7 Room {room} \u00b7 \u25ce {motes} Motes")
            eh_top = f"{self._dungeon_name} \u2014 Room {room} \u00b7 \u25ce {motes}"
            if track:
                eh_top += f" | {track}"
            self.sm.update_top_bar(eh_top)
            return
        # Wild ruin: floor progress lives on the dungeon record, not city_floors
        if getattr(self, "_wild_dungeon", None) is not None:
            from wild_dungeons import get_wild_dungeon
            wild = get_wild_dungeon(p, p.get("wild_dungeon_id")) or self._wild_dungeon
            floor = int(wild.get("highest_floor_cleared", 0)) + 1
            max_floor = max(1, int(wild.get("total_floors", 1) or 1))
            self._set_subtitle(
                f"{self._dungeon_region.title()} Region · Floor {floor}")
            wild_top = f"{self._dungeon_name} — Floor {floor}/{max_floor}"
            if track:
                wild_top += f" | {track}"
            self.sm.update_top_bar(wild_top)
            return
        # Re-read floor from city progress (may have advanced)
        origin_city = p.get("origin_city", "solmere")
        city_prog = p.get("city_floors", {}).get(origin_city, {})
        floor = city_prog.get("floor", self._dungeon_floor)
        max_floor = city_prog.get("max_floor", self._dungeon_max_floor)
        self._set_subtitle(
            f"{self._dungeon_region.title()} Region · Floor {floor}")
        top = f"{self._dungeon_name} — Floor {floor}/{max_floor}"
        if track:
            top += f" | {track}"
        if p.get("pandemonium_mode"):
            curse = p.get("pandemonium_curse")
            if curse:
                top += f" | {curse.get('icon', '☠️')} {curse.get('name', '')}"
        elif p.get("dungeon_region") == "wonderland":
            from wonderland_curses import format_quirk_summary
            qs = format_quirk_summary(p)
            if qs:
                top += f" | {qs}"
        self.sm.update_top_bar(top)

    def _flush_output(self):
        """Override to also persist dungeon log lines to player save data."""
        with self._pending_lock:
            lines = self._pending_lines[:]
            self._pending_lines.clear()

        if not lines:
            return

        # Hide loading indicator on first output
        if hasattr(self, 'loading_label') and self.loading_label:
            try:
                self.loading_label.place_forget()
                self.loading_label = None
            except tk.TclError:
                pass

        self.output_text.config(state=tk.NORMAL)
        for line in lines:
            self.output_text.insert(tk.END, strip_ansi(line) + "\n")
        self.output_text.see(tk.END)
        self.output_text.config(state=tk.DISABLED)

        # Persist to player save data so the log survives leaving the dungeon
        log = self.player.get("_dungeon_log", None)
        if log is None:
            log = []
            self.player["_dungeon_log"] = log
        log.extend(lines)
        # Trim to a reasonable limit
        max_lines = 500
        if len(log) > max_lines:
            self.player["_dungeon_log"] = log[-max_lines:]

    def _run_facility(self):
        """Override to intercept render_ascii_map and render_party_status.

        render_ascii_map → updates the Map panel.
        render_party_status → updates the Party Status panel.
        prompt_acquire_item → intercepted for full-backpack GUI dialog.
        """
        import dungeon_rooms
        _orig_render = dungeon_rooms.render_ascii_map
        _orig_party = dungeon_rooms.render_party_status
        _orig_eh_status = dungeon_rooms.render_event_horizon_status

        def _gui_render(rooms, explored, current_room_idx, floor, player=None):
            map_str = _orig_render(rooms, explored, current_room_idx, floor, player=player)
            if map_str:
                self._update_map(map_str)
            return ""  # panel shows it — suppress duplicate log output

        def _gui_party(player):
            # Render modern GUI party panel directly (no ASCII text in log)
            self._update_party(player=player)
            return ""  # Suppress ASCII output to dungeon log

        def _gui_eh_status(player):
            # Event Horizon has no map — fill the Rift panel with a status block
            text = _orig_eh_status(player)
            if text:
                self._update_map(text)
            return ""  # Suppress ASCII output to dungeon log

        dungeon_rooms.render_ascii_map = _gui_render
        dungeon_rooms.render_party_status = _gui_party
        dungeon_rooms.render_event_horizon_status = _gui_eh_status

        # ── Intercept full-backpack prompt ───────────────────────────────
        import inventory_ui
        _orig_acquire = inventory_ui.prompt_acquire_item

        def _gui_acquire(player, item):
            # First try normal add — if it fits, no dialog needed
            from inventory import add_item_to_inventory
            if add_item_to_inventory(player, item):
                return True
            # Inventory full — show the GUI dialog on the MAIN thread and block
            # this (background) dungeon thread until the player decides.
            # Creating tkinter widgets from this thread would corrupt Tk and
            # produce blank/orphaned windows.
            import queue as _queue
            result_q = _queue.Queue()

            def _show():
                try:
                    result_q.put(self._show_acquire_dialog(player, item))
                except Exception:
                    result_q.put(False)

            try:
                self.after(0, _show)
            except (RuntimeError, tk.TclError):
                return False
            # No AFK timeout: the dialog is modal, so the only ways out are
            # choosing (keep/discard) or closing it (drop) — an idle player
            # must never auto-drop the loot. The only bail-out is the
            # dungeon screen itself being torn down mid-prompt.
            while True:
                try:
                    return result_q.get(timeout=0.5)
                except _queue.Empty:
                    if (getattr(self, "_stopped", False)
                            or getattr(self, "_finished", False)):
                        return False

        inventory_ui.prompt_acquire_item = _gui_acquire

        try:
            super()._run_facility()
        finally:
            dungeon_rooms.render_ascii_map = _orig_render
            dungeon_rooms.render_party_status = _orig_party
            dungeon_rooms.render_event_horizon_status = _orig_eh_status
            inventory_ui.prompt_acquire_item = _orig_acquire

    def _show_acquire_dialog(self, player, item):
        """Show a GUI dialog when inventory is full after a dungeon drop."""
        from gui.widgets.acquire_dialog import show_acquire_dialog
        return show_acquire_dialog(
            self, self.sm, player, item, log_fn=self._append_output,
        )

    # ── Combat integration ────────────────────────────────────────────────────

    def _await_combat_result(self, result_queue, label="Combat"):
        """Block the dungeon thread until the combat overlay delivers a result.

        No AFK timeout: a fight may sit parked on an input prompt for as
        long as the player likes — being idle must never end the run. The
        only abort path is a true deadlock: the battle screen disappeared
        without delivering a result (its thread died silently, or the
        screen was torn down). A deployed overlay that later vanishes gets
        a short grace window; an overlay that never appeared (e.g. its
        constructor crashed) gets a longer startup grace.
        """
        from gui.screens.combat_screen import CombatScreen

        seen_overlay = False
        missing_since = None
        while True:
            try:
                return result_queue.get(timeout=0.5)
            except queue.Empty:
                pass

            if isinstance(self.sm.get_top_screen(), CombatScreen):
                seen_overlay = True
                missing_since = None
                continue

            if missing_since is None:
                missing_since = time.monotonic()
                continue

            grace = 10.0 if seen_overlay else 30.0
            if time.monotonic() - missing_since >= grace:
                self._append_output(
                    f"\n[ERROR: {label} screen vanished without a result — "
                    f"aborting the encounter.]")
                if seen_overlay:
                    # Dismiss the orphaned overlay on the GUI thread
                    try:
                        self.sm.root.after(0, self.sm.dismiss_overlay)
                    except tk.TclError:
                        pass  # Root is gone — app is closing anyway
                return "timeout"

    def _gui_combat(self, player, enemy_keys, floor=None, room_num=None,
                    total_rooms=None, enemies=None):
        """Callback passed to explore_dungeon as combat_override.

        Shows CombatScreen as an overlay (does NOT destroy DungeonScreen),
        so the dungeon thread's I/O redirects remain active after combat.
        Blocks the dungeon thread until combat finishes.
        """
        result_queue = queue.Queue()

        def start_combat():
            from gui.screens.combat_screen import CombatScreen
            self.sm.push_overlay(
                CombatScreen,
                enemy_keys=enemy_keys,
                enemies=enemies,
                floor=floor,
                room_num=room_num,
                total_rooms=total_rooms,
                on_result=lambda r: result_queue.put(r),
                is_overlay=True,
            )

        self.sm.root.after(0, start_combat)
        return self._await_combat_result(result_queue, "Combat")

    def _gui_floor_clear(self, player, floor_num=None, total_floors=None,
                         name=None):
        """Callback passed to explore_dungeon as floor_clear_override.

        Wild runs call this after each cleared floor (except the last). Shows
        the floor-clear window on the GUI thread and blocks the dungeon
        thread until the player picks an option. Returns "continue",
        "city", or "save_exit".
        """
        result_queue = queue.Queue()
        floor_num = int(floor_num or 0)
        total_floors = int(total_floors or 0)

        def show():
            try:
                from gui.widgets.confirm_dialog import choice_dialog
                from character import player_max_hp
                from time_blocks import format_block_track

                hp_max = player_max_hp(player)
                details = [f"HP: {player.get('current_hp', 0)}/{hp_max}",
                           f"Gold: {player.get('gold', 0)}"]
                track = format_block_track(player)
                if track:
                    details.append(f"Time: {track}")

                next_floor = min(floor_num + 1, total_floors)
                choice_dialog(
                    parent=self,
                    title="Floor Cleared!",
                    heading=f"=== FLOOR {floor_num}/{total_floors} CLEARED ===",
                    subtitle=(f"{name or 'Wild Dungeon'} — "
                              f"now entering Floor {next_floor}/{total_floors}"),
                    details="\n".join(details),
                    options=[
                        ("continue", "1. Continue to next floor"),
                        ("city", "2. Return to city"),
                        ("save_exit", "3. Save and return to main menu"),
                    ],
                    on_choice=result_queue.put,
                    default_choice="continue",
                )
            except Exception:
                # Never leave the dungeon thread waiting on a window that
                # failed to open (screen destroyed / TclError).
                import traceback
                traceback.print_exc()
                result_queue.put("continue")

        try:
            self.sm.root.after(0, show)
        except (tk.TclError, RuntimeError):
            return "continue"  # GUI gone — keep the run going headless

        while True:
            try:
                return result_queue.get(timeout=0.5)
            except queue.Empty:
                if self._stopped:
                    return "continue"

    def _gui_superboss(self, tier, floor):
        """Callback passed to explore_dungeon as superboss_override.

        Shows CombatScreen as an overlay for superboss encounters.
        Maps the tier number to the correct superboss combat function
        and enemy key, then launches the CombatScreen with the custom func.
        """
        result_queue = queue.Queue()

        # ── Boss Rush (Event Horizon): dict spec {"rush": True, ...} ─────
        if isinstance(tier, dict) and tier.get("rush"):
            import event_horizon as eh
            boss = eh.rush_boss_by_id(tier.get("boss_id"))
            if boss is None:
                return "victory"
            combat_fn = eh.rush_boss_combat(boss)
            enemy_keys = list(boss.get("keys") or [boss["id"]])
            index = int(tier.get("index", 1) or 1)
            total = int(tier.get("total", 1) or 1)

            def start_rush_combat():
                from gui.screens.combat_screen import CombatScreen
                self.sm.push_overlay(
                    CombatScreen,
                    enemy_keys=enemy_keys,
                    on_result=lambda r: result_queue.put(r),
                    is_overlay=True,
                    combat_func=combat_fn,
                    combat_context="boss_rush",
                    room_num=index,
                    total_rooms=total,
                )

            self.sm.root.after(0, start_rush_combat)
            return self._await_combat_result(result_queue, "Boss Rush combat")

        # Handle Chrysalis (Pandemonium floor 20 override, passed as string tier)
        if tier == "chrysalis":
            boss_key = "entangled_chrysalis"

            def start_combat():
                from combat.entangled_chrysalis import combat_entangled_chrysalis
                from gui.screens.combat_screen import CombatScreen
                self.sm.push_overlay(
                    CombatScreen,
                    enemy_keys=[boss_key, "temporal_shard_pyre", "temporal_shard_pulse", "temporal_shard_ruin"],
                    floor=floor,
                    on_result=lambda r: result_queue.put(r),
                    is_overlay=True,
                    combat_func=combat_entangled_chrysalis,
                    combat_context="superboss",
                )

            self.sm.root.after(0, start_combat)
            return self._await_combat_result(result_queue, "Superboss combat")

        # Handle White Knight (Pandemonium floor 40 override, passed as string tier)
        if tier == "white_knight":
            boss_key = "white_knight"

            def start_combat():
                from combat.white_knight import combat_white_knight
                from gui.screens.combat_screen import CombatScreen
                self.sm.push_overlay(
                    CombatScreen,
                    enemy_keys=[boss_key],
                    floor=floor,
                    on_result=lambda r: result_queue.put(r),
                    is_overlay=True,
                    combat_func=combat_white_knight,
                    combat_context="superboss",
                )

            self.sm.root.after(0, start_combat)
            return self._await_combat_result(result_queue, "Superboss combat")

        # ── Wonderland Superbosses (string tier names from _wonderland_superboss_dispatch) ──
        wl_superboss_map = {
            "queen_of_hearts": ("wl_queen_of_hearts", None),
            "big_bad_wolf":    ("wl_big_bad_wolf", None),
            "wicked_witch":    ("wl_wicked_witch", None),
            "wicked_witch_of_the_west": ("wl_wicked_witch", None),
            "jabberwock":      ("wl_jabberwock", None),
            "mary_sue":        ("wl_mary_sue", None),
        }
        wl_entry = wl_superboss_map.get(tier)
        if wl_entry is not None:
            boss_key = wl_entry[0]

            if tier == "queen_of_hearts":
                from combat.queen_of_hearts import combat_queen_of_hearts as func
            elif tier == "big_bad_wolf":
                from combat.big_bad_wolf import combat_big_bad_wolf as func
            elif tier in ("wicked_witch", "wicked_witch_of_the_west"):
                from combat.wicked_witch import combat_wicked_witch as func
            elif tier == "jabberwock":
                from combat.jabberwock import combat_jabberwock as func
            elif tier == "mary_sue":
                from combat.mary_sue import combat_mary_sue as func
            else:
                return "victory"

            def start_wl_combat():
                from gui.screens.combat_screen import CombatScreen
                self.sm.push_overlay(
                    CombatScreen,
                    enemy_keys=[boss_key],
                    floor=floor,
                    on_result=lambda r: result_queue.put(r),
                    is_overlay=True,
                    combat_func=func,
                    combat_context="superboss",
                )

            self.sm.root.after(0, start_wl_combat)
            return self._await_combat_result(result_queue, "Superboss combat")

        # Map tier → (boss_enemy_key, combat_function)
        superboss_map = {
            0: ("broodmother_vileheart", None),       # imported below
            1: ("dream_devouring_slitcurrent", None),
            2: ("queen_of_mirrors_sylvana", None),
            3: ("melt_forge_golem_ignis", None),
            4: ("heaven_banished_dragon_yinglong", None),
            5: ("rientrante_frostbound", None),
            6: ("captain_everlong_ship", None),
            7: ("black_silence", None),
            8: ("chromatic_artisan", None),
        }
        entry = superboss_map.get(tier)
        if entry is None:
            return "victory"  # Unknown tier — shouldn't happen

        boss_key = entry[0]

        # Import the combat function lazily to avoid circular imports
        if tier == 0:
            from combat.broodmother import combat_broodmother as func
        elif tier == 1:
            from combat.slitcurrent import combat_slitcurrent as func
        elif tier == 2:
            from combat.sylvana import combat_sylvana as func
        elif tier == 3:
            from combat.ignis import combat_ignis as func
        elif tier == 4:
            from combat.yinglong import combat_yinglong as func
        elif tier == 5:
            from combat.rientrante import combat_rientrante as func
        elif tier == 6:
            from combat.everlong_ship import combat_everlong_ship as func
        elif tier == 7:
            from combat.black_silence import combat_black_silence as func
        elif tier == 8:
            from combat.palette_chromatic_artisan import combat_palette as func
        else:
            return "victory"

        def start_combat():
            from gui.screens.combat_screen import CombatScreen
            self.sm.push_overlay(
                CombatScreen,
                enemy_keys=[boss_key],
                floor=floor,
                on_result=lambda r: result_queue.put(r),
                is_overlay=True,
                combat_func=func,
                combat_context="superboss",
            )

        self.sm.root.after(0, start_combat)
        return self._await_combat_result(result_queue, "Superboss combat")

    # ── Result handling ───────────────────────────────────────────────────────

    def _handle_result(self, result=None):
        """Called when the dungeon thread exits."""
        if self._on_result:
            try:
                self._on_result(result)
            except Exception:
                # A result callback crash must never strand the player on a
                # finished dungeon screen (2026-10-23: the wild completion
                # dialog was parented to the already-destroyed WorldMapScreen
                # → TclError, and every button was a no-op afterwards).
                import traceback
                traceback.print_exc()
                self._on_result = None
                self.sm.switch_to(CityScreen)
        else:
            self.sm.switch_to(CityScreen)

    def _on_flee(self):
        """User clicked the leave button — confirm and force exit.

        Event Horizon runs have no flee: leaving SUSPENDS the run (resumable
        at the site). The confirm defaults to "Keep Going" because the player
        may still be mid-Enter on the "Press Enter to descend" prompt — an
        accidental Yes used to flash the dialog away into the city (playtest).
        """
        if self._confirm_dialog_open:
            return
        self._confirm_dialog_open = True

        def _do_flee():
            self._confirm_dialog_open = False
            self._stop_facility(result="fled")

        if self._eh_run:
            import event_horizon as eh
            state = eh.ensure_eh_state(self.player)
            best = max(int(state.get("best_room", 0)),
                       int(state.get("room", 0)))
            confirm_dialog(
                parent=self,
                title="Leave the Event Horizon?",
                message=("There is no fleeing the rift — leaving now "
                         "SUSPENDS your run.\n\n"
                         f"Save & quit to the city? Resume later at the site "
                         f"(best room: {best}).\n\n"
                         "Abandoning your run is a separate choice after "
                         "each room."),
                on_yes=_do_flee,
                on_no=lambda: setattr(self, '_confirm_dialog_open', False),
                yes_text="Save & Quit",
                no_text="Keep Going",
                focus_no=True,
            )
            return

        confirm_dialog(
            parent=self,
            title="Flee Dungeon?",
            message="Flee the dungeon and return to the city?",
            on_yes=_do_flee,
            on_no=lambda: setattr(self, '_confirm_dialog_open', False),
        )

    def _on_flee_key(self, event=None):
        """Handle 'f' keyboard shortcut for fleeing the dungeon.
        
        Only triggers when the text input entry does NOT have focus
        (so the player can still type 'f' normally in text prompts).
        """
        # Don't intercept 'f' when the user is typing in the text entry
        if self._input_mode:
            try:
                focused = self.focus_get()
                if focused is self.input_entry:
                    return  # Let 'f' be typed into the entry normally
            except Exception:
                pass
        self._on_flee()

    def _stop_facility(self, result=None):
        """Stop the background facility thread, passing the exit result."""
        self._stopped = True
        self._input_queue.put("")
        if not self._finished:
            self._finish(result)

    # ── Map update (called from dungeon thread via redirected print) ───────────

    def _update_map(self, text):
        """Update the ASCII map panel."""
        try:
            self.after(0, lambda: self._set_map(text))
        except (RuntimeError, tk.TclError):
            pass

    def _set_map(self, text):
        """Set map text (main thread only)."""
        try:
            self.map_text.config(state=tk.NORMAL)
            self.map_text.delete("1.0", tk.END)
            self.map_text.insert(tk.END, text)
            self.map_text.config(state=tk.DISABLED)
        except tk.TclError:
            pass  # widget destroyed (screen dismissed while update pending)

    def _on_party_canvas_configure(self, event):
        """Keep the inner party frame's width matched to the canvas."""
        self._party_canvas.itemconfig(self._party_canvas_window, width=event.width)

    def _on_party_inner_configure(self, event):
        """Update scroll region when inner frame resizes."""
        self._party_canvas.configure(scrollregion=self._party_canvas.bbox("all"))

    def _update_party(self, player=None):
        """Update the Party Status panel with modern GUI widgets.
        
        Called from the dungeon thread.  Extracts all needed data immediately
        (to avoid race conditions with the background thread), then schedules
        the GUI update on the main thread via after().
        """
        if player is None:
            return
        # ── Snapshot player data in the calling thread ───────────────────
        from combat.ally import (ensure_party_order,
                                 get_all_active_allies_including_defeated,
                                 get_all_reserve_allies_including_defeated)
        from combat.combat_ui import _get_entity_buff_tags
        from character import player_max_hp
        from titles import format_name as _format_title_name

        ensure_party_order(player)
        front_allies = get_all_active_allies_including_defeated(player)
        back_allies = get_all_reserve_allies_including_defeated(player)

        members = []

        # Player
        members.append({
            "name": _format_title_name(
                player, "compact",
                show_title=self.sm.settings.get("show_title_beside_name", True)),
            "level": player.get("level", 1),
            "hp": player.get("current_hp", 0),
            "max_hp": player_max_hp(player),
            "tags": _get_entity_buff_tags(player),
            "section": "player",
            "color": Theme.ACCENT,
            "defeated": False,
            "section_label": "",
        })

        # Front allies
        for ally in front_allies:
            defeated = ally.get("defeated") or ally.get("current_hp", 0) <= 0
            members.append({
                "name": display_name(ally),
                "level": ally.get("level", 1),
                "hp": 0 if defeated else ally.get("current_hp", 0),
                "max_hp": ally.get("max_hp", 1),
                "tags": _get_entity_buff_tags(ally),
                "section": "front",
                "color": Theme.TEXT_DIM if defeated else Theme.TEXT,
                "defeated": defeated,
                "section_label": "FRONT",
            })

        # Back allies
        for ally in back_allies:
            defeated = ally.get("defeated") or ally.get("current_hp", 0) <= 0
            members.append({
                "name": display_name(ally),
                "level": ally.get("level", 1),
                "hp": 0 if defeated else ally.get("current_hp", 0),
                "max_hp": ally.get("max_hp", 1),
                "tags": _get_entity_buff_tags(ally),
                "section": "back",
                "color": "#8b7355" if not defeated else "#555555",
                "defeated": defeated,
                "section_label": "BACK",
            })

        try:
            self.after(0, lambda: self._render_party_gui(members))
        except (RuntimeError, tk.TclError):
            pass

    def _render_party_gui(self, members):
        """Build/render the party status panel with HPBar widgets (main thread).
        
        Accepts a pre-built list of member dicts (already extracted from player
        data in the calling thread to avoid race conditions).
        """
        from gui.widgets.hp_bar import HPBar

        # ── Rebuild widgets ───────────────────────────────────────────────
        try:
            inner = self._party_inner
        except (tk.TclError, AttributeError):
            return  # Widget destroyed

        # Destroy old widgets
        for frame in self._party_member_frames:
            try:
                frame.destroy()
            except tk.TclError:
                pass
        self._party_member_frames.clear()
        self._party_member_widgets.clear()

        last_section = None

        for i, m in enumerate(members):
            # Section separator (skip for player)
            if m["section"] != last_section and m["section"] != "player":
                sep_frame = tk.Frame(inner, bg=Theme.BG_DARK, height=1)
                sep_frame.pack(fill=tk.X, padx=4, pady=(4, 0))
                tk.Label(
                    sep_frame,
                    text=f"── {m['section_label']} ──",
                    bg=Theme.BG_DARK,
                    fg=Theme.TEXT_DIM,
                    font=(Theme.FONT_FAMILY, 8, "bold"),
                ).pack(anchor=tk.W, padx=2)
                self._party_member_frames.append(sep_frame)

            last_section = m["section"]

            # Per-member frame
            row = tk.Frame(inner, bg=Theme.BG_DARK)
            row.pack(fill=tk.X, padx=4, pady=(3 if i > 0 else 1, 1))
            self._party_member_frames.append(row)

            # Top line: name + level + defeated marker
            name_line = tk.Frame(row, bg=Theme.BG_DARK)
            name_line.pack(fill=tk.X)

            dflag = "† " if m.get("defeated") else ""
            name_color = m["color"]
            name_display = f"{dflag}{m['name']}  Lv.{m['level']}"
            tk.Label(
                name_line,
                text=name_display,
                bg=Theme.BG_DARK,
                fg=name_color,
                font=(Theme.FONT_FAMILY, 8, "bold"),
                anchor=tk.W,
            ).pack(side=tk.LEFT)

            # HP bar
            ratio = m["hp"] / max(1, m["max_hp"])
            if m["defeated"]:
                hp_fill = "#333333"
            elif m["section"] == "back":
                if ratio > 0.5:
                    hp_fill = "#7a6a4a"
                elif ratio > 0.25:
                    hp_fill = "#8b6914"
                else:
                    hp_fill = "#aa4444"
            else:
                if ratio > 0.5:
                    hp_fill = Theme.HP_BAR_FILL
                elif ratio > 0.25:
                    hp_fill = "#f39c12"
                else:
                    hp_fill = Theme.ACCENT

            hp_bar = HPBar(
                row,
                current=m["hp"],
                maximum=m["max_hp"],
                width=130,
                height=13,
                show_text=True,
                fill_color=hp_fill,
            )
            hp_bar.pack(anchor=tk.W, pady=(1, 0))

            # Status tags
            tag_text = m["tags"].strip() if m["tags"] else " "
            tk.Label(
                row,
                text=tag_text,
                bg=Theme.BG_DARK,
                fg=Theme.BUFF_NEUTRAL,
                font=(Theme.FONT_FAMILY, 7),
                anchor=tk.W,
            ).pack(anchor=tk.W)

            self._party_member_widgets.append({"row": row, "hp_bar": hp_bar})

        # ── Update canvas scroll region ────────────────────────────────────
        inner.update_idletasks()
        self._party_canvas.configure(scrollregion=self._party_canvas.bbox("all"))

    def handle_escape(self):
        """Override: Esc does nothing in dungeon (input entry handles its own Esc)."""
        pass  # Dungeon wraps FacilityScreen which handles input; no modal to cancel
