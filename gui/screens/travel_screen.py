"""
gui/screens/travel_screen.py — Overland travel destination selection screen.

Replaces the old terminal-based destination picker with a proper GUI:
- Scrollable destination cards with city name, travel time, danger, biome
- Mount status display with speed/safety bonuses
- Cancel button to return to city
- On selection, hands off to FacilityScreen for the actual journey events
- Travel combat uses proper GUI CombatScreen overlay (not redirected I/O)
"""

import tkinter as tk
import queue as _queue

from gui.screens.base_screen import BaseScreen
from gui.theme import Theme
from gui.widgets.confirm_dialog import confirm_dialog

from resources.cities import CITIES


# How many cards to show at once before scrolling kicks in
VISIBLE_CARD_COUNT = 4
CARD_HEIGHT_ESTIMATE = 90  # approximate px per card (name + desc + padding)


class TravelScreen(BaseScreen):
    """
    GUI screen for selecting an overland travel destination.

    Shows all land connections from the current city as clickable cards
    inside a scrollable region, with mount bonuses, travel time, and
    danger indicators.  A Cancel button always stays visible at the bottom.

    On selection:
        1. Opens a confirmation dialog
        2. Hands off to FacilityScreen for the journey events
           (travel combat uses a proper GUI CombatScreen overlay)
        3. On journey completion / cancellation, navigates directly to CityScreen
    """

    def __init__(self, parent, screen_manager, **kwargs):
        super().__init__(parent, screen_manager, **kwargs)

    # ── Helpers ───────────────────────────────────────────────────────────────

    @property
    def city_id(self):
        """Current city ID from player state."""
        if not self.player:
            return "solmere"
        loc = self.player.get("location", "solmere")
        if loc == "dungeon":
            loc = self.player.get("origin_city", "solmere")
        return loc

    @property
    def city(self):
        return CITIES.get(self.city_id, CITIES["solmere"])

    @property
    def land_routes(self):
        """All land-type connections from the current city."""
        all_conn = self.city.get("travel", {}).get("connections", [])
        return [c for c in all_conn if c.get("type", "land") == "land"]

    def _effective_time(self, raw_time):
        """Apply mount time reduction."""
        mount_id = self.player.get("mount_id") if self.player else None
        if mount_id:
            from resources.mounts import get_mount
            mount = get_mount(mount_id)
            if mount:
                return int(raw_time * (1 - mount.get("time_reduction", 0)))
        return raw_time

    def _danger_level(self, travel_time):
        """Return (label, color) for danger indicator."""
        if travel_time >= 200:
            return "\u26a0 High Risk", Theme.BUFF_NEGATIVE
        elif travel_time >= 120:
            return "~ Moderate", Theme.BUFF_NEUTRAL
        else:
            return "\u2713 Safe", Theme.BUFF_POSITIVE

    def _mount_info(self):
        """Return (name, speed_pct, safety_pct) or None."""
        if not self.player:
            return None
        mount_id = self.player.get("mount_id")
        if not mount_id:
            return None
        from resources.mounts import get_mount
        mount = get_mount(mount_id)
        if not mount:
            return None
        return (
            mount["name"],
            int(mount["time_reduction"] * 100),
            int(mount["event_mitigation"] * 100),
        )

    # ── GUI combat override ──────────────────────────────────────────────────

    def _make_combat_override(self):
        """
        Build a combat_override callback that shows CombatScreen as an overlay.

        This is called from within the FacilityScreen's background thread
        (which runs embark_journey).  We capture the ScreenManager reference
        now while we're on the main thread, then use root.after(0, ...) to
        schedule the overlay from the background thread.
        """
        sm = self.sm  # ScreenManager — valid even after TravelScreen is destroyed

        def gui_combat(player, enemy_keys, **kwargs):
            result_queue = _queue.Queue()

            def _show_combat():
                from gui.screens.combat_screen import CombatScreen
                sm.push_overlay(
                    CombatScreen,
                    enemy_keys=enemy_keys,
                    combat_context="travel",
                    on_result=lambda r: result_queue.put(r),
                    is_overlay=True,
                )

            sm.root.after(0, _show_combat)
            try:
                return result_queue.get(timeout=300)
            except _queue.Empty:
                return "timeout"

        return gui_combat

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_wonderland_cheshire(self):
        """Show Cheshire Cat art instead of the travel menu when in Wonderland."""
        # Clear everything
        for child in self.winfo_children():
            child.destroy()

        container = self.styled_frame(self)
        container.pack(fill=tk.BOTH, expand=True)

        # Cheshire Cat ASCII art
        cat_art = (
            "                              .'\\   /`.\n"
            "                            .'.-.`-'.-.`.\n"
            "                        ..._:   .-. .-.   :_...\n"
            "                    .'    '-.(o ) (o ).-'    `.\n"
            "                    :  _    _ _`~(_)~`_ _    _  :\n"
            "                    :  /:   ' .-=_   _=-. `   ;\\  :\n"
            "                    :   :|-.._  '     `  _..-|:   :\n"
            "                    :   `:| |`:-:-.-:-:'| |:'   :\n"
            "                    `.   `.| | | | | | |.'   .'\n"
            "                        `.   `-:_| | |_:-'   .'\n"
            "                         `-._   ````    _.-'\n"
            "                            ``-------''\n"
        )

        art_label = tk.Label(
            container,
            text=cat_art,
            bg=Theme.BG_DARK,
            fg=Theme.ACCENT,
            font=("Courier New", 10),
            justify=tk.CENTER,
        )
        art_label.pack(pady=(40, 10))

        # Cheshire Cat quote
        quote = (
            '"Oh, you\'re looking for a map? How delightfully linear of you.\n'
            ' There is no map. There is no \'north.\' There is only where you are,\n'
            ' and where you aren\'t, and the difference is mostly academic.\n\n'
            ' But if you must go somewhere... try the book. It\'s how you came in.\n'
            ' It\'s how you\'ll leave. Everything else is just scenery."\n\n'
            '                    \u2014 The Cheshire Cat'
        )

        quote_label = tk.Label(
            container,
            text=quote,
            bg=Theme.BG_DARK,
            fg=Theme.TEXT_DIM,
            font=Theme.FONT,
            justify=tk.CENTER,
        )
        quote_label.pack(pady=(10, 30))

        # Back button
        self.styled_button(
            container,
            text="\u2190 Back to Wonderland",
            command=self._go_back,
            width=22,
            bg="#5a3a5a",
        ).pack(pady=10)

    # ── UI construction ───────────────────────────────────────────────────────

    def _update_top_bar(self):
        """Show the origin city format with live time — same as CityScreen."""
        p = self.player
        if not p:
            self.sm.update_top_bar("Pandemonium")
            return
        cid = self.city_id
        city = self.city
        city_name = city.get("name", cid) if isinstance(city, dict) else str(city)
        _cf = p.get("city_floors", {}).get(cid, {})
        _cur = _cf.get("floor", 1)
        _max = _cf.get("max_floor", 1)
        from events import format_date
        from utils import format_time
        text = (
            f"{p['name']} | {city_name} | Floor {_cur}/{_max} | "
            f"{format_date(p)} | {format_time(p)}"
        )
        self.sm.update_top_bar(text)

    def build_ui(self):
        self.sm.clear_log()
        self._update_top_bar()

        # ── Wonderland: Cheshire Cat replaces travel ─────────────────────
        if self.player and self.player.get("wonderland_active"):
            self._build_wonderland_cheshire()
            return

        # ── Main container ─────────────────────────────────────────────────
        self.content = self.styled_frame(self)
        self.content.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Header
        tk.Label(
            self.content,
            text="OVERLAND TRAVEL",
            bg=Theme.BG_DARK,
            fg=Theme.ACCENT,
            font=Theme.FONT_LARGE,
        ).pack(pady=(0, 2))

        tk.Label(
            self.content,
            text=f"Departing from {city_name}",
            bg=Theme.BG_DARK,
            fg=Theme.TEXT_DIM,
            font=Theme.FONT,
        ).pack(pady=(0, 4))

        # ── Mount status card ───────────────────────────────────────────────
        mount = self._mount_info()
        if mount:
            mount_card = tk.Frame(
                self.content,
                bg=Theme.BG_CARD,
                highlightthickness=1,
                highlightbackground=Theme.BUFF_NEUTRAL,
            )
            mount_card.pack(fill=tk.X, padx=40, pady=(4, 10))

            tk.Label(
                mount_card,
                text=f"\U0001f434  {mount[0]} is ready",
                bg=Theme.BG_CARD,
                fg=Theme.TEXT,
                font=Theme.FONT_BOLD,
            ).pack(side=tk.LEFT, padx=12, pady=6)

            tk.Label(
                mount_card,
                text=f"  {mount[1]}% faster  |  {mount[2]}% safer",
                bg=Theme.BG_CARD,
                fg=Theme.BUFF_NEUTRAL,
                font=Theme.FONT_SMALL,
            ).pack(side=tk.LEFT, padx=4, pady=6)

        # ── No routes fallback ──────────────────────────────────────────────
        routes = self.land_routes
        if not routes:
            tk.Label(
                self.content,
                text="There are no overland roads leading out of this city.",
                bg=Theme.BG_DARK,
                fg=Theme.TEXT_DIM,
                font=Theme.FONT,
            ).pack(pady=20)

            self.styled_button(
                self.content,
                text="\u2190 Back to City",
                command=self._go_back,
                width=18,
            ).pack(pady=10)
            return

        # ── Section label ───────────────────────────────────────────────────
        tk.Label(
            self.content,
            text="Choose your destination:",
            bg=Theme.BG_DARK,
            fg=Theme.TEXT,
            font=Theme.FONT_BOLD,
        ).pack(anchor=tk.W, padx=40, pady=(8, 4))

        # ── Scrollable card area ────────────────────────────────────────────
        # Create a canvas + scrollbar so many routes don't push the Cancel
        # button off-screen.
        needs_scroll = len(routes) > VISIBLE_CARD_COUNT

        scroll_container = tk.Frame(self.content, bg=Theme.BG_DARK)
        scroll_container.pack(fill=tk.BOTH, expand=True, padx=10)

        if needs_scroll:
            self._card_canvas = tk.Canvas(
                scroll_container,
                bg=Theme.BG_DARK,
                highlightthickness=0,
                borderwidth=0,
            )
            scrollbar = tk.Scrollbar(
                scroll_container,
                orient=tk.VERTICAL,
                command=self._card_canvas.yview,
                bg=Theme.BG_MID,
                troughcolor=Theme.BG_DARK,
            )
            self._card_canvas.configure(yscrollcommand=scrollbar.set)

            self._card_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            # Inner frame that holds all the cards
            self._cards_frame = tk.Frame(self._card_canvas, bg=Theme.BG_DARK)
            self._card_canvas_window = self._card_canvas.create_window(
                (0, 0), window=self._cards_frame, anchor=tk.NW,
            )

            # Make the inner frame resize to match the canvas width
            self._cards_frame.bind("<Configure>", self._on_cards_configure)
            self._card_canvas.bind("<Configure>", self._on_canvas_configure)

            # Mousewheel scrolling
            self._card_canvas.bind("<Enter>", self._bind_mousewheel)
            self._card_canvas.bind("<Leave>", self._unbind_mousewheel)
        else:
            self._cards_frame = tk.Frame(scroll_container, bg=Theme.BG_DARK)
            self._cards_frame.pack(fill=tk.BOTH, expand=True)
            self._card_canvas = None

        # Build each destination card inside the (possibly scrollable) frame
        for i, conn in enumerate(routes):
            dest_id = conn["dest"]
            dest = CITIES.get(dest_id, {})
            dest_name = dest.get("name", dest_id)
            raw_time = conn["travel_time"]
            effective_time = self._effective_time(raw_time)
            danger_label, danger_color = self._danger_level(effective_time)
            biome = dest.get("biome", "unknown").title()
            desc = dest.get("description", "")
            if len(desc) > 80:
                desc = desc[:77] + "..."

            self._build_destination_card(
                self._cards_frame,
                index=i + 1,
                dest_id=dest_id,
                dest_name=dest_name,
                travel_time=effective_time,
                raw_time=raw_time,
                danger_label=danger_label,
                danger_color=danger_color,
                biome=biome,
                description=desc,
            )

        # ── Cancel button (always visible below the scroll area) ───────────
        btn_frame = tk.Frame(self.content, bg=Theme.BG_DARK)
        btn_frame.pack(fill=tk.X, pady=(12, 6))

        self.styled_button(
            btn_frame,
            text="\u2190 Cancel (Stay in City)",
            command=self._go_back,
            width=24,
            bg="#5a3a5a",
        ).pack(side=tk.LEFT, padx=30)

        # ── Keyboard bindings ───────────────────────────────────────────────
        self._setup_keys()

    # ── Scroll helpers ───────────────────────────────────────────────────────

    def _on_cards_configure(self, event):
        """Update the scroll region when the inner frame changes size."""
        if self._card_canvas is not None:
            self._card_canvas.configure(
                scrollregion=self._card_canvas.bbox("all")
            )

    def _on_canvas_configure(self, event):
        """Keep the inner frame as wide as the canvas."""
        if self._card_canvas is not None:
            self._card_canvas.itemconfig(
                self._card_canvas_window, width=event.width
            )

    def _bind_mousewheel(self, event):
        if self._card_canvas is not None:
            self._mw_bind_id = self._card_canvas.bind("<MouseWheel>", self._on_mousewheel)

    def _unbind_mousewheel(self, event):
        if self._card_canvas is not None and hasattr(self, '_mw_bind_id'):
            self._card_canvas.unbind("<MouseWheel>", self._mw_bind_id)
            del self._mw_bind_id

    def _on_mousewheel(self, event):
        if self._card_canvas is not None:
            self._card_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # ── Destination card builder ─────────────────────────────────────────────

    def _build_destination_card(self, parent, index, dest_id, dest_name,
                                 travel_time, raw_time, danger_label,
                                 danger_color, biome, description):
        """Create a single clickable destination card."""
        card = tk.Frame(
            parent,
            bg=Theme.BG_CARD,
            highlightthickness=1,
            highlightbackground=Theme.BORDER,
            cursor="hand2",
        )
        card.pack(fill=tk.X, pady=4, padx=10)

        # Click / hover handlers
        on_click = lambda e, d=dest_id, dn=dest_name, tt=travel_time, rt=raw_time: \
            self._select_destination(d, dn, tt, rt)

        card.bind("<Button-1>", on_click)
        card.bind("<Enter>", lambda e, c=card: c.configure(
            highlightbackground=Theme.ACCENT))
        card.bind("<Leave>", lambda e, c=card: c.configure(
            highlightbackground=Theme.BORDER))

        # Left side: number + city name + biome
        left_frame = tk.Frame(card, bg=Theme.BG_CARD)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=12, pady=8)
        left_frame.bind("<Button-1>", on_click)
        left_frame.bind("<Enter>", lambda e, c=card: c.configure(
            highlightbackground=Theme.ACCENT))
        left_frame.bind("<Leave>", lambda e, c=card: c.configure(
            highlightbackground=Theme.BORDER))

        # Index badge
        idx_badge = tk.Label(
            left_frame,
            text=f" {index} ",
            bg=Theme.ACCENT,
            fg="#ffffff",
            font=Theme.FONT_BOLD,
        )
        idx_badge.pack(side=tk.LEFT, padx=(0, 10))
        idx_badge.bind("<Button-1>", on_click)

        # City name
        name_lbl = tk.Label(
            left_frame,
            text=dest_name,
            bg=Theme.BG_CARD,
            fg=Theme.TEXT,
            font=Theme.FONT_BOLD,
        )
        name_lbl.pack(side=tk.LEFT, padx=(0, 8))
        name_lbl.bind("<Button-1>", on_click)

        # Biome tag
        biome_lbl = tk.Label(
            left_frame,
            text=f"[{biome}]",
            bg=Theme.BG_CARD,
            fg=Theme.TEXT_DIM,
            font=Theme.FONT_SMALL,
        )
        biome_lbl.pack(side=tk.LEFT)
        biome_lbl.bind("<Button-1>", on_click)

        # Description (below name row)
        desc_frame = tk.Frame(card, bg=Theme.BG_CARD)
        desc_frame.pack(fill=tk.X, padx=12, pady=(0, 6))
        desc_frame.bind("<Button-1>", on_click)

        if description:
            desc_lbl = tk.Label(
                desc_frame,
                text=description,
                bg=Theme.BG_CARD,
                fg=Theme.TEXT_DIM,
                font=Theme.FONT_SMALL,
                wraplength=550,
                justify=tk.LEFT,
            )
            desc_lbl.pack(anchor=tk.W)
            desc_lbl.bind("<Button-1>", on_click)

        # Right side: travel time + danger
        right_frame = tk.Frame(card, bg=Theme.BG_CARD)
        right_frame.pack(side=tk.RIGHT, padx=12, pady=8)
        right_frame.bind("<Button-1>", on_click)

        if travel_time != raw_time:
            time_text = f"{travel_time} min"
            time_sub = f"({raw_time} min base)"
        else:
            time_text = f"{travel_time} min"
            time_sub = ""

        time_lbl = tk.Label(
            right_frame,
            text=time_text,
            bg=Theme.BG_CARD,
            fg=Theme.TEXT,
            font=Theme.FONT_BOLD,
        )
        time_lbl.pack(anchor=tk.E)
        time_lbl.bind("<Button-1>", on_click)

        if time_sub:
            sub_lbl = tk.Label(
                right_frame,
                text=time_sub,
                bg=Theme.BG_CARD,
                fg=Theme.TEXT_DIM,
                font=Theme.FONT_SMALL,
            )
            sub_lbl.pack(anchor=tk.E)
            sub_lbl.bind("<Button-1>", on_click)

        danger_lbl = tk.Label(
            right_frame,
            text=danger_label,
            bg=Theme.BG_CARD,
            fg=danger_color,
            font=Theme.FONT_SMALL,
        )
        danger_lbl.pack(anchor=tk.E, pady=(2, 0))
        danger_lbl.bind("<Button-1>", on_click)

    # ── Actions ───────────────────────────────────────────────────────────────

    def _select_destination(self, dest_id, dest_name, travel_time, raw_time):
        """Called when a destination card is clicked — confirm then embark."""
        self.sm.log(f"Selected destination: {dest_name}")

        def _do_embark():
            self._embark(dest_id, dest_name, travel_time)

        confirm_dialog(
            parent=self,
            title="Embark on Journey",
            message=(
                f"Travel to {dest_name}?\n\n"
                f"Estimated journey: {travel_time} minutes.\n"
                f"Keep your eyes open on the road."
            ),
            on_yes=_do_embark,
        )

    def _embark(self, dest_id, dest_name, travel_time):
        """Begin the journey — hand off to FacilityScreen for travel events.

        A combat_override is injected so that travel combat opens the
        proper GUI CombatScreen overlay instead of using redirected I/O.
        """
        origin_biome = self.city.get("biome", "temperate")
        combat_override = self._make_combat_override()
        # Capture the root window now while TravelScreen is still alive, so the
        # after(0, …) deferred switch works even after TravelScreen is destroyed.
        _root = self.sm.root

        from facilities.travel import embark_journey
        from gui.screens.facility_screen import FacilityScreen

        def _after_journey(result):
            """Called when the FacilityScreen (journey) closes.

            IMPORTANT: This runs inside FacilityScreen._finish, so we must NOT
            synchronously call switch_to (which would destroy FacilityScreen
            while we're still in its call stack).  Defer to the next main-loop
            iteration via after(0, …).
            """
            if result == "dead" or (self.player and self.player.get("current_hp", 1) <= 0):
                # Defer death-screen transition as well
                _root.after(0, self._handle_death)
                return
            # Arrived safely — go to the (possibly new) city
            from gui.screens.city_screen import CityScreen
            _root.after(0, lambda: self.sm.switch_to(CityScreen, push_history=False))

        self.sm.switch_to(
            FacilityScreen,
            title=f"Journey to {dest_name}",
            func=embark_journey,
            func_args=(self.player, dest_id, dest_name, travel_time, origin_biome),
            func_kwargs={"combat_override": combat_override},
            on_close=_after_journey,
        )

    def _go_back(self):
        """Return to city without travelling."""
        from gui.screens.city_screen import CityScreen
        self.sm.switch_to(CityScreen, push_history=False)

    def _handle_death(self):
        """Player died during travel."""
        from gui.screens.death_screen import DeathScreen

        def _continue_game():
            from utils import apply_death_penalty
            apply_death_penalty(self.player)
            from gui.screens.city_screen import CityScreen
            self.sm.switch_to(CityScreen, push_history=False)

        def _quit_to_menu():
            self.sm.player = None
            from gui.screens.main_menu_screen import MainMenuScreen
            self.sm.switch_to(MainMenuScreen)

        city_id = self.city_id
        self.sm.switch_to(
            DeathScreen,
            floor=self.player.get("city_floors", {}).get(city_id, {}).get("floor", "?"),
            city_id=city_id,
            death_type="travel",
            on_continue=_continue_game,
            on_quit=_quit_to_menu,
        )

    # ── Keyboard shortcuts ───────────────────────────────────────────────────

    def _setup_keys(self):
        """Bind number keys for quick destination selection."""
        self.bind("<KeyPress>", self._on_key)
        self.focus_set()

    def _on_key(self, event):
        """Number keys 1-9 → select destination, Escape → cancel."""
        if event.char in "123456789":
            idx = int(event.char) - 1
            routes = self.land_routes
            if idx < len(routes):
                conn = routes[idx]
                dest_id = conn["dest"]
                dest = CITIES.get(dest_id, {})
                dest_name = dest.get("name", dest_id)
                raw_time = conn["travel_time"]
                effective_time = self._effective_time(raw_time)
                self._select_destination(dest_id, dest_name, effective_time, raw_time)
            return

        if event.keysym == "Escape":
            self._go_back()
