"""
gui/screens/world_map_screen.py — Interactive world map (unified travel hub).

Replaces both the old TravelScreen and port-service UI with a single canvas-based
world map that supports:

  BROWSE MODE — click any city to see its details, services, and connections.
                A "Travel Here" button starts an animated multi-leg journey.

  TRAVEL MODE — a dot animates along the computed route on the canvas.
                The right panel becomes a live travel log.
                The dot pauses at each city; sea segments trigger a port prompt.
                Combat and other events fire mid-segment.

  Both modes support drag-panning: press and drag the map to reach cities
  that lie outside the window (small windows, or as the map grows).
"""

import tkinter as tk
import queue as _queue
import random

from gui.screens.base_screen import BaseScreen
from gui.theme import Theme
from gui.widgets.confirm_dialog import confirm_dialog

from resources.cities import CITIES
from resources.items import ITEMS, build_item, ITEM_RARITY, is_unique_item
from resources.trade_goods import (
    roll_cargo_good, build_cargo,
    cargo_merchant_stock_price, cargo_merchant_sell_price,
)
from facilities.pathfinding import find_shortest_path
from facilities.travel_events import (
    _random_item_id, _discovery_rarity, _merchant_stock_rarity,
    _merchant_price, _sell_price, _item_stat_line, _charisma_discount,
)
from inventory import add_item_to_inventory, remove_item_by_reference
from combat.stats import get_effective_attribute
from utils import get_difficulty_multiplier_from_time
from character import player_max_hp
from events import get_daily_bonus_multiplier
from wild_dungeons import (
    get_active_dungeons, get_wild_dungeon, maybe_spawn_cycle,
    build_journey_to_dungeon,
)


# ═══════════════════════════════════════════════════════════════════════════
#  CITY LAYOUT
# ═══════════════════════════════════════════════════════════════════════════
# Positions/regions live in resources/world_layout.py so runtime systems
# (e.g. wild_dungeons.py) can place markers without importing GUI modules.
# Private aliases keep the rest of this file unchanged.
from resources.world_layout import (
    CITY_POSITIONS as _CITY_POSITIONS,
    REGIONS as _REGIONS,
    NODE_W as _NODE_W,
    NODE_H as _NODE_H,
)

_REGION_COLORS = {
    "North":       "#1a3a5c",
    "Central":     "#2d4a3a",
    "East":        "#3a2d4a",
    "South":       "#4a3a2d",
    "Far Reaches": "#1a4a4a",
}

_BIOME_COLORS = {
    "tundra":       "#c8d6e5",
    "temperate":    "#78e08f",
    "swamp":        "#38ada9",
    "mountain":     "#b8b8b8",
    "magical":      "#d980fa",
    "volcanic":     "#e55039",
    "forest":       "#6ab04c",
    "savanna":      "#e1b12c",
    "coastal":      "#3867d6",
    "desert":       "#f6b93b",
    "tropical":     "#00d2d3",
    "sea_caves":    "#576574",
    "pandemonium":  "#c44dff",
}

_SERVICE_ICONS = {
    "shop": "\U0001f6d2", "inn": "\U0001f6cf", "blacksmith": "\U0001f528",
    "trade_hall": "\U0001f3ea", "temple": "\U0001f3db", "port": "\u2693",
    "shipyard": "\U0001f6a2", "herbalist": "\U0001f33f", "barracks": "\U0001f6e1",
    "black_market": "\U0001f441", "arcane_tower": "\U0001fa84",
    "gift_shop": "\U0001f381", "guild": "\U0001f465",
}

_ANIM_STEPS = 30        # animation frames per segment
_ANIM_INTERVAL = 40     # ms between frames
_EVENT_CHECKPOINTS = 3  # event slots per segment

# Wild dungeon marker appearance (canvas px)
_WILD_MARKER_W = 96
_WILD_MARKER_H = 30
_WILD_MARKER_FILL = "#2b1622"
_WILD_MARKER_OUTLINE = "#c44dff"
_WILD_MARKER_SELECTED = "#f1c40f"

# Wild dungeon marker glyphs by biome — themed after each biome's races
# (see resources/enemies/biome_races.py). Fallback is the skull glyph.
_WILD_BIOME_ICONS = {
    "tundra":      "\u2744",        # ❄
    "temperate":   "\U0001F33F",    # 🌿
    "swamp":       "\U0001F438",    # 🐸
    "mountain":    "\u26F0",        # ⛰
    "magical":     "\u2728",        # ✨
    "volcanic":    "\U0001F30B",    # 🌋
    "forest":      "\U0001F332",    # 🌲
    "savanna":     "\U0001F981",    # 🦁
    "coastal":     "\U0001F30A",    # 🌊
    "desert":      "\U0001F335",    # 🌵
    "tropical":    "\U0001F334",    # 🌴
    "sea_caves":   "\U0001F41A",    # 🐚
    "pandemonium": "\U0001F48E",    # 💎
    "wonderland":  "\U0001F407",    # 🐇
}
_WILD_FALLBACK_ICON = "\u2620"      # ☠


# ═══════════════════════════════════════════════════════════════════════════
#  WORLD MAP SCREEN
# ═══════════════════════════════════════════════════════════════════════════

class WorldMapScreen(BaseScreen):
    """Unified world map — browse cities or travel with animated dot."""

    MODE_BROWSE = "browse"
    MODE_TRAVEL = "travel"

    def __init__(self, parent, screen_manager, travel_mode=False, **kwargs):
        self._mode = self.MODE_BROWSE
        self._selected_city = None
        self._selected_wild = None       # dungeon id of the selected wild dungeon
        self._wild_rect_ids = {}         # dungeon_id -> canvas rect item id (marker)
        self._wild_hitboxes = {}         # dungeon_id -> (x1, y1, x2, y2)
        self._selected_horizon = False   # Event Horizon site selected
        self._horizon_rect_id = None     # canvas rect id of the site marker
        self._horizon_hitbox = None      # (x1, y1, x2, y2)
        self._node_rects = {}
        self._canvas = None
        self._info_frame = None
        self._travel_mode = travel_mode  # True = travel mode (pathfinding + highlights + Travel Here)
        self._path_result = None        # cached pathfinding result for travel mode
        self._route_lines = {}           # (a,b) sorted tuple → [canvas line IDs]

        # Map panning (drag) state
        self._drag_start = None          # (x, y) where the mouse was pressed
        self._dragging_map = False       # True once the drag threshold is passed

        # Travel state
        self._travel_segments = []
        self._travel_path = []
        self._travel_seg_idx = 0
        self._travel_dot = None
        self._travel_paused = False
        self._travel_anim_job = None
        self._travel_check_job = None  # after() ID for combat result polling
        self._travel_event_queue = []
        self._travel_event_idx = 0
        self._travel_step = 0
        self._travel_seg_start = (0, 0)
        self._travel_seg_end = (0, 0)
        self._travel_player_dead = False
        self._travel_combat_result = None  # set by _check, handled on overlay dismiss
        self._travel_wild = None      # wild dungeon dict when journeying to a ruin
        self._travel_horizon = None   # EH site dict when journeying to the distortion

        super().__init__(parent, screen_manager, **kwargs)

    # ── Properties ───────────────────────────────────────────────────────

    @property
    def city_id(self):
        if not self.player:
            return "solmere"
        loc = self.player.get("location", "solmere")
        if loc == "dungeon":
            loc = self.player.get("origin_city", "solmere")
        return loc

    @property
    def city(self):
        return CITIES.get(self.city_id, CITIES["solmere"])

    @staticmethod
    def _has_port(city_id):
        c = CITIES.get(city_id, {})
        return "port" in c.get("services", [])

    def _update_top_bar(self):
        """Show the origin city format with live time — same as CityScreen."""
        if not self.player:
            cur_name = self.city.get("name", "Unknown City")
            self.sm.update_top_bar(f"World Map — Current: {cur_name}")
            return
        cid = self.city_id
        city = self.city
        city_name = city.get("name", cid) if isinstance(city, dict) else str(city)
        _cf = self.player.get("city_floors", {}).get(cid, {})
        _cur = _cf.get("floor", 1)
        _max = _cf.get("max_floor", 1)
        from events import format_date
        from time_blocks import format_block_track
        track = format_block_track(self.player, include_day=False)
        segments = [self.player['name'], city_name, f"Floor {_cur}/{_max}"]
        if track:
            segments.append(track)
        segments.append(format_date(self.player))
        text = " | ".join(segments)
        self.sm.update_top_bar(text)

    # ── UI construction ──────────────────────────────────────────────────

    def build_ui(self):
        self.sm.clear_log()
        self._update_top_bar()

        # ── Wonderland: Cheshire Cat replaces the world map ──────────────
        if self.player and self.player.get("wonderland_active"):
            self._build_wonderland_cheshire()
            return

        main = self.styled_frame(self)
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        canvas_frame = tk.Frame(main, bg=Theme.BG_DARK)
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._canvas = tk.Canvas(
            canvas_frame, bg="#0a0a1a",
            highlightthickness=0, borderwidth=0,
        )
        self._canvas.pack(fill=tk.BOTH, expand=True, padx=(0, 5))

        self._info_frame = tk.Frame(
            main, bg=Theme.BG_CARD, width=300,
            highlightthickness=1, highlightbackground=Theme.BORDER,
        )
        self._info_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        self._info_frame.pack_propagate(False)

        self._show_info_placeholder()

        self._draw_region_backgrounds()
        self._draw_routes()
        self._draw_city_nodes()

        # ── Wild dungeons: expire overdue + idempotent weekly spawn, then draw ──
        # (docs/wild_dungeon_design.md §2 — world-map open is a safe check point)
        if self.player:
            spawned, _ = maybe_spawn_cycle(self.player)
            if spawned:
                self.sm.log(
                    f"{len(spawned)} wild dungeon(s) surfaced "
                    f"— check the world map.",
                    category="event",
                )
            self._draw_wild_dungeons()
            self._draw_event_horizon()

        # Allow drag-panning when the map is larger than the viewport
        self._update_map_scrollregion()
        self._canvas.bind("<ButtonPress-1>", self._on_canvas_press)
        self._canvas.bind("<B1-Motion>", self._on_canvas_drag)
        self._canvas.bind("<ButtonRelease-1>", self._on_canvas_release)
        self._canvas.bind("<Motion>", self._on_canvas_motion)

        # Bottom bar
        self._bottom_bar = tk.Frame(self, bg=Theme.BG_DARK)
        self._bottom_bar.pack(fill=tk.X, padx=20, pady=(8, 12))

        self._btn_back = self.styled_button(
            self._bottom_bar, text="\u2190 Back to City",
            command=self._go_back, width=18, bg="#5a3a5a",
        )
        self._btn_back.pack(side=tk.LEFT, padx=4)

        self._btn_legend = self.styled_button(
            self._bottom_bar, text="Show Legend",
            command=self._show_legend, width=16,
        )
        self._btn_legend.pack(side=tk.RIGHT, padx=4)

        self.bind("<Escape>", self._on_escape_event)
        self.focus_set()

    # ── Drawing ──────────────────────────────────────────────────────────

    def _build_wonderland_cheshire(self):
        """Show Cheshire Cat art instead of the world map when in Wonderland."""
        import textwrap

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

    # ── Drawing ──────────────────────────────────────────────────────────

    def _draw_region_backgrounds(self):
        padding = 30
        for region_name, city_ids in _REGIONS.items():
            xs = [_CITY_POSITIONS[c][0] for c in city_ids]
            ys = [_CITY_POSITIONS[c][1] for c in city_ids]
            x1 = min(xs) - padding
            y1 = min(ys) - padding
            x2 = max(xs) + _NODE_W + padding
            y2 = max(ys) + _NODE_H + padding
            color = _REGION_COLORS.get(region_name, "#1a1a2e")
            self._canvas.create_rectangle(
                x1, y1, x2, y2, fill=color, outline="#2d3436", width=1,
                tags=("region_bg",), stipple="gray25",
            )
            self._canvas.create_text(
                x1 + 10, y1 + 12, text=region_name.upper(),
                anchor=tk.NW, fill=Theme.TEXT_DIM,
                font=(Theme.FONT_FAMILY, 8, "bold"), tags=("region_label",),
            )

    def _draw_routes(self):
        drawn = set()
        for city_id, city_data in CITIES.items():
            for conn in city_data.get("travel", {}).get("connections", []):
                dest = conn["dest"]
                edge_key = tuple(sorted([city_id, dest]))
                if edge_key in drawn:
                    continue
                drawn.add(edge_key)
                if city_id not in _CITY_POSITIONS or dest not in _CITY_POSITIONS:
                    continue
                x1, y1 = _CITY_POSITIONS[city_id]
                x2, y2 = _CITY_POSITIONS[dest]
                cx1 = x1 + _NODE_W // 2
                cy1 = y1 + _NODE_H // 2
                cx2 = x2 + _NODE_W // 2
                cy2 = y2 + _NODE_H // 2
                seg_type = conn.get("type", "land")
                tags = ("route", seg_type)
                if seg_type == "sea":
                    lid = self._canvas.create_line(
                        cx1, cy1, cx2, cy2,
                        fill="#4a6fa5", width=1.2, dash=(5, 4), tags=tags,
                    )
                else:
                    lid = self._canvas.create_line(
                        cx1, cy1, cx2, cy2,
                        fill="#5a7a5a", width=1.2, tags=tags,
                    )
                # Store for path highlighting
                ek = tuple(sorted([city_id, dest]))
                self._route_lines.setdefault(ek, []).append(lid)
                mid_x = (cx1 + cx2) / 2
                mid_y = (cy1 + cy2) / 2
                raw_time = conn.get("travel_time", 0)
                import time_blocks as _tb_edge
                edge_blocks = _tb_edge.travel_blocks(self.player, raw_time)
                self._canvas.create_text(
                    mid_x, mid_y - 6, text=f"{edge_blocks}b",
                    fill=Theme.TEXT_DIM, font=(Theme.FONT_FAMILY, 7),
                    tags=("route_label",),
                )

    def _draw_city_nodes(self):
        current = self.city_id
        for city_id, (cx, cy) in _CITY_POSITIONS.items():
            city_data = CITIES.get(city_id, {})
            city_name = city_data.get("name", city_id)
            biome = city_data.get("biome", "temperate")
            fill_color = _BIOME_COLORS.get(biome, "#78e08f")
            is_current = (city_id == current)
            has_port = self._has_port(city_id)
            display = f"\u2693 {city_name}" if has_port else city_name

            rect_id = self._canvas.create_rectangle(
                cx, cy, cx + _NODE_W, cy + _NODE_H,
                fill=fill_color,
                outline=Theme.ACCENT if is_current else "#2d3436",
                width=2 if is_current else 1,
                tags=("node", city_id, "node_rect"),
            )
            text_color = "#111" if biome in (
                "temperate", "savanna", "desert", "tropical", "magical"
            ) else "#fff"
            self._canvas.create_text(
                cx + _NODE_W // 2, cy + _NODE_H // 2,
                text=display, fill=text_color,
                font=(Theme.FONT_FAMILY, 8, "bold"),
                tags=("node", city_id, "node_text"),
            )
            if is_current:
                self._canvas.create_text(
                    cx + _NODE_W - 12, cy + 8,
                    text="\u2605", fill="#f1c40f",
                    font=(Theme.FONT_FAMILY, 10),
                    tags=("node", city_id),
                )
            self._node_rects[city_id] = rect_id

    def _draw_wild_dungeons(self):
        """Draw markers for active wild dungeons (distinct from city nodes)."""
        self._wild_rect_ids = {}
        self._wild_hitboxes = {}
        for dungeon in get_active_dungeons(self.player):
            dungeon_id = dungeon.get("id")
            position = dungeon.get("position")
            if not dungeon_id or not position:
                continue
            x, y = position[0], position[1]
            x1 = x - _WILD_MARKER_W // 2
            y1 = y - _WILD_MARKER_H // 2
            x2 = x1 + _WILD_MARKER_W
            y2 = y1 + _WILD_MARKER_H
            selected = (dungeon_id == self._selected_wild)
            rect_id = self._canvas.create_rectangle(
                x1, y1, x2, y2,
                fill=_WILD_MARKER_FILL,
                outline=_WILD_MARKER_SELECTED if selected else _WILD_MARKER_OUTLINE,
                width=2.5 if selected else 1.5,
                tags=("wild_node", dungeon_id),
            )
            icon = _WILD_BIOME_ICONS.get(dungeon.get("biome"), _WILD_FALLBACK_ICON)
            self._canvas.create_text(
                x, y,
                text=f"{icon} Lv {dungeon.get('level', '?')}",
                fill=Theme.RARITY_LEGENDARY,
                font=(Theme.FONT_FAMILY, 8, "bold"),
                tags=("wild_node", dungeon_id),
            )
            self._wild_rect_ids[dungeon_id] = rect_id
            self._wild_hitboxes[dungeon_id] = (x1, y1, x2, y2)

    # ── Event Horizon site (endless run; docs/event_horizon_design.md §6.1) ──

    def _draw_event_horizon(self):
        """Draw the distortion's site marker once the unlock gate is met."""
        from event_horizon import EVENT_HORIZON_POSITION, site_unlocked
        self._horizon_rect_id = None
        self._horizon_hitbox = None
        if not self.player or not site_unlocked(self.player):
            return
        px, py = EVENT_HORIZON_POSITION
        x1, y1 = px - 75, py - 15
        x2, y2 = px + 75, py + 15
        selected = self._selected_horizon
        self._horizon_rect_id = self._canvas.create_rectangle(
            x1, y1, x2, y2,
            fill="#12101d",
            outline=_WILD_MARKER_SELECTED if selected else "#8e6bff",
            width=2.5 if selected else 2,
            tags=("horizon_node",),
        )
        self._canvas.create_text(
            px, py, text="\U0001F300 EVENT HORIZON",
            fill="#c9b6ff",
            font=(Theme.FONT_FAMILY, 8, "bold"),
            tags=("horizon_node",),
        )
        self._horizon_hitbox = (x1, y1, x2, y2)

    def _find_horizon_at(self, ex, ey):
        """True when the click hits the EH marker (widget -> canvas coords)."""
        if self._horizon_hitbox is None:
            return False
        ex = self._canvas.canvasx(ex)
        ey = self._canvas.canvasy(ey)
        x1, y1, x2, y2 = self._horizon_hitbox
        return x1 <= ex <= x2 and y1 <= ey <= y2

    def _select_horizon(self):
        self._selected_horizon = True
        if self._horizon_rect_id:
            self._canvas.itemconfig(self._horizon_rect_id,
                                    outline=_WILD_MARKER_SELECTED, width=2.5)
        self._build_horizon_info_panel()

    def _deselect_horizon(self):
        self._selected_horizon = False
        if self._horizon_rect_id:
            self._canvas.itemconfig(self._horizon_rect_id,
                                    outline="#8e6bff", width=2)
        self._show_info_placeholder()

    def _build_horizon_info_panel(self):
        """EH site details: run status, best depth, travel estimate."""
        import event_horizon as eh
        inner = self._make_scrollable_info()
        site = eh.event_horizon_site(self.player)
        if site is None:
            self._show_info_placeholder()
            return
        state = eh.ensure_eh_state(self.player)
        active = bool(state.get("run_active"))
        room = int(state.get("room", 0))
        best = int(state.get("best_room", 0))
        nearest_id = site.get("nearest_city", "solmere")
        nearest = CITIES.get(nearest_id, {}).get("name", nearest_id)

        est_travel = None
        try:
            journey = eh.build_journey_to_site(self.player)
            if journey is not None:
                est_travel = journey["total_time"]
        except Exception:
            journey = None
        est_blocks = self._journey_blocks(journey) if journey else None

        tk.Label(inner, text="THE EVENT HORIZON",
                 bg=Theme.BG_CARD, fg="#8e6bff",
                 font=Theme.FONT_BOLD).pack(anchor=tk.W, padx=10, pady=(10, 2))
        tk.Label(inner, text="[\U0001F300 Space-Time Distortion \u00b7 Endless]",
                 bg=Theme.BG_CARD, fg=Theme.TEXT_DIM,
                 font=Theme.FONT_SMALL).pack(anchor=tk.W, padx=10)

        sep = tk.Frame(inner, bg=Theme.BORDER, height=1)
        sep.pack(fill=tk.X, padx=8, pady=6)
        tk.Label(inner, text="RUN STATUS",
                 bg=Theme.BG_CARD, fg=Theme.TEXT,
                 font=(Theme.FONT_FAMILY, 9, "bold")).pack(
            anchor=tk.W, padx=10, pady=(0, 4))

        rows = [
            ("Status", (f"Suspended at room {room + 1}" if active and room > 0
                        else ("Ready to begin" if not active else "In progress"))),
            ("Deepest room", str(best)),
            ("Nearest city", nearest),
            ("Est. travel", (f"≈{est_blocks} blocks"
                             if est_blocks is not None else "no route")),
        ]
        for label, value in rows:
            row = tk.Frame(inner, bg=Theme.BG_CARD)
            row.pack(fill=tk.X, padx=10, pady=1)
            tk.Label(row, text=label, bg=Theme.BG_CARD, fg=Theme.TEXT_DIM,
                     font=Theme.FONT_SMALL).pack(side=tk.LEFT)
            tk.Label(row, text=value, bg=Theme.BG_CARD, fg=Theme.TEXT,
                     font=Theme.FONT_SMALL).pack(side=tk.RIGHT)

        tk.Label(
            inner,
            text=("Endless rooms \u2014 every clear deepens the distortion. "
                  "Feed flasks to one actor or spread them; carry hard trial "
                  "cards for a richer payout. Progress suspends on save & "
                  "quit, and is lost on death or abandon."),
            bg=Theme.BG_CARD, fg=Theme.TEXT_DIM,
            font=Theme.FONT_SMALL, wraplength=270, justify=tk.LEFT,
        ).pack(anchor=tk.W, padx=10, pady=(6, 8))

        self.styled_button(
            inner,
            text="\u25b6 Travel to the Distortion",
            command=self._on_travel_to_horizon,
            width=24, bg=Theme.ACCENT, fg=Theme.TEXT_HEADER,
        ).pack(pady=(2, 12))

    # ── Canvas events ────────────────────────────────────────────────────

    def _update_map_scrollregion(self):
        """Size the canvas scroll region to the drawn map content.

        Without a scroll region Tk anchors the view at (0, 0) and anything
        past the window edge is unreachable.  A content-based region lets
        the player drag the map when the window is small (and keeps working
        automatically if the map grows later).
        """
        bbox = self._canvas.bbox("all")
        if not bbox:
            return
        pad = 40  # breathing room around the outermost nodes
        self._canvas.configure(
            scrollregion=(bbox[0] - pad, bbox[1] - pad,
                          bbox[2] + pad, bbox[3] + pad),
            confine=True,
        )

    def _find_city_at(self, ex, ey):
        # Mouse events arrive in widget coords; the map lives in canvas
        # coords, which shift when the view is drag-panned.
        ex = self._canvas.canvasx(ex)
        ey = self._canvas.canvasy(ey)
        for city_id, (cx, cy) in _CITY_POSITIONS.items():
            if cx <= ex <= cx + _NODE_W and cy <= ey <= cy + _NODE_H:
                return city_id
        return None

    def _find_wild_at(self, ex, ey):
        """Return the wild dungeon id whose marker contains the click point.

        Mouse events arrive in widget coords; the map lives in canvas
        coords, which shift when the view is drag-panned — same conversion
        as _find_city_at, so markers stay clickable after panning.
        """
        ex = self._canvas.canvasx(ex)
        ey = self._canvas.canvasy(ey)
        for dungeon_id, (x1, y1, x2, y2) in self._wild_hitboxes.items():
            if x1 <= ex <= x2 and y1 <= ey <= y2:
                return dungeon_id
        return None

    # ── Drag-panning ─────────────────────────────────────────────────────

    def _on_canvas_press(self, event):
        """Arm a potential drag and remember the pan anchor."""
        self._drag_start = (event.x, event.y)
        self._dragging_map = False
        self._canvas.scan_mark(event.x, event.y)

    def _on_canvas_drag(self, event):
        """Pan the map once the pointer moves past the click threshold."""
        if self._drag_start is None:
            return
        dx = event.x - self._drag_start[0]
        dy = event.y - self._drag_start[1]
        if not self._dragging_map and max(abs(dx), abs(dy)) >= 4:
            self._dragging_map = True
            self._canvas.config(cursor="fleur")
        if self._dragging_map:
            self._canvas.scan_dragto(event.x, event.y, gain=1)

    def _on_canvas_release(self, event):
        """Finish a drag, or treat a stationary press as a city click."""
        was_dragging = self._dragging_map
        self._drag_start = None
        self._dragging_map = False
        self._canvas.config(cursor="")
        if was_dragging:
            return  # a pan, not a click — don't select a city
        self._on_canvas_click(event)

    def _on_canvas_motion(self, event):
        if self._dragging_map:
            return  # keep the panning cursor while dragging
        if self._mode == self.MODE_TRAVEL:
            return
        target = self._find_city_at(event.x, event.y) or \
            self._find_wild_at(event.x, event.y) or \
            self._find_horizon_at(event.x, event.y)
        self._canvas.config(cursor="hand2" if target else "")

    def _on_canvas_click(self, event):
        if self._mode == self.MODE_TRAVEL:
            return
        city = self._find_city_at(event.x, event.y)
        if city is not None:
            if self._selected_wild is not None:
                self._deselect_wild()
            if self._selected_horizon:
                self._deselect_horizon()
            if city == self._selected_city:
                self._deselect_city()
            else:
                self._select_city(city)
            return
        wild_id = self._find_wild_at(event.x, event.y)
        if wild_id is not None:
            if self._selected_horizon:
                self._deselect_horizon()
            if wild_id == self._selected_wild:
                self._deselect_wild()
            else:
                self._select_wild(wild_id)
            return
        if self._find_horizon_at(event.x, event.y):
            if self._selected_wild is not None:
                self._deselect_wild()
            if self._selected_city is not None:
                self._deselect_city()
            if self._selected_horizon:
                self._deselect_horizon()
            else:
                self._select_horizon()

    def _on_escape_event(self, _event=None):
        """Frame-level <Escape> binding.

        Returns "break" so the root-level global handler (gui/app.py) does
        not dispatch the same keypress a second time — both bindings fire
        while this screen itself holds focus.
        """
        self._on_escape()
        return "break"

    def handle_escape(self):
        """Root-dispatched Escape (focus on a child widget).

        The BaseScreen default calls sm.go_back(), which rebuilds the
        previous screen beneath any active overlay. Mirror the frame-level
        binding instead (deselect, or leave the map only when idle).
        """
        self._on_escape()

    def _on_escape(self):
        if self._mode == self.MODE_TRAVEL:
            return
        if self._selected_wild is not None:
            self._deselect_wild()
        elif self._selected_horizon:
            self._deselect_horizon()
        elif self._selected_city is not None:
            self._deselect_city()
        else:
            self._go_back()

    # ── Browse: city selection ───────────────────────────────────────────

    def _select_city(self, city_id):
        # Restore previous selection
        self._clear_path_highlight()
        if self._selected_city and self._selected_city in self._node_rects:
            self._canvas.itemconfig(
                self._node_rects[self._selected_city],
                outline=(Theme.ACCENT if self._selected_city == self.city_id
                         else "#2d3436"),
                width=(2 if self._selected_city == self.city_id else 1),
            )
        self._selected_city = city_id
        if city_id != self.city_id and city_id in self._node_rects:
            self._canvas.itemconfig(self._node_rects[city_id],
                                    outline="#f1c40f", width=2)

        # In travel mode: compute path, highlight it, show route info.
        # The "Travel Here" button lives inside the info panel itself
        # (see _build_travel_info_panel), matching the wild dungeon panel.
        if self._travel_mode and city_id != self.city_id:
            self._path_result = find_shortest_path(self.player, self.city_id, city_id)
            if self._path_result and self._path_result["segments"]:
                self._highlight_path(self._path_result)
            self._build_travel_info_panel(city_id, self._path_result)
        else:
            self._path_result = None
            self._build_city_info_panel(city_id)
            # No Travel Here in browse mode

    def _deselect_city(self):
        self._clear_path_highlight()
        self._path_result = None
        if self._selected_city and self._selected_city in self._node_rects:
            self._canvas.itemconfig(
                self._node_rects[self._selected_city],
                outline=(Theme.ACCENT if self._selected_city == self.city_id
                         else "#2d3436"),
                width=(2 if self._selected_city == self.city_id else 1),
            )
        self._selected_city = None
        self._show_info_placeholder()

    # ── Browse: wild dungeon selection ───────────────────────────────────

    def _select_wild(self, dungeon_id):
        """Select a wild dungeon marker and show its info panel."""
        if self._selected_city is not None:
            self._deselect_city()
        self._restore_wild_marker(self._selected_wild)
        self._selected_wild = dungeon_id
        rect_id = self._wild_rect_ids.get(dungeon_id)
        if rect_id:
            try:
                self._canvas.itemconfig(rect_id,
                                        outline=_WILD_MARKER_SELECTED,
                                        width=2.5)
            except tk.TclError:
                pass
        dungeon = get_wild_dungeon(self.player, dungeon_id)
        if dungeon:
            self._build_wild_info_panel(dungeon)

    def _deselect_wild(self):
        """Clear the wild dungeon selection and restore the placeholder."""
        self._restore_wild_marker(self._selected_wild)
        self._selected_wild = None
        self._show_info_placeholder()

    def _restore_wild_marker(self, dungeon_id):
        """Restore a wild marker's default outline after deselection."""
        if not dungeon_id:
            return
        rect_id = self._wild_rect_ids.get(dungeon_id)
        if not rect_id:
            return
        try:
            self._canvas.itemconfig(rect_id,
                                    outline=_WILD_MARKER_OUTLINE,
                                    width=1.5)
        except tk.TclError:
            pass

    # ── Path highlighting ────────────────────────────────────────────────

    def _highlight_path(self, result):
        """Draw gold highlights along the computed path."""
        for seg in result["segments"]:
            ek = tuple(sorted([seg["from"], seg["to"]]))
            for lid in self._route_lines.get(ek, []):
                if seg["type"] == "sea":
                    self._canvas.itemconfig(lid, fill="#f1c40f", width=2.5, dash=(5, 4))
                else:
                    self._canvas.itemconfig(lid, fill="#f1c40f", width=2.5, dash=())
                self._canvas.lift(lid)

    def _clear_path_highlight(self):
        """Restore all route lines to default appearance."""
        for ek, lids in self._route_lines.items():
            a, b = ek
            cdata = CITIES.get(a, {})
            is_sea = False
            for conn in cdata.get("travel", {}).get("connections", []):
                if conn["dest"] == b and conn.get("type") == "sea":
                    is_sea = True
                    break
            for lid in lids:
                if is_sea:
                    self._canvas.itemconfig(lid, fill="#4a6fa5", width=1.2, dash=(5, 4))
                else:
                    self._canvas.itemconfig(lid, fill="#5a7a5a", width=1.2, dash=())

    # ── Info panel ───────────────────────────────────────────────────────

    def _clear_info_panel(self):
        for child in self._info_frame.winfo_children():
            child.destroy()

    def _show_info_placeholder(self):
        self._clear_info_panel()
        tk.Label(
            self._info_frame,
            text="Click a city or a ruin marker\non the map to view details.\n\nDrag the map to pan.",
            bg=Theme.BG_CARD, fg=Theme.TEXT_DIM,
            font=Theme.FONT_SMALL, justify=tk.CENTER,
        ).pack(expand=True)

    def _make_scrollable_info(self):
        self._clear_info_panel()
        canvas = tk.Canvas(self._info_frame, bg=Theme.BG_CARD,
                           highlightthickness=0, borderwidth=0)
        scrollbar = tk.Scrollbar(self._info_frame, orient=tk.VERTICAL,
                                 command=canvas.yview,
                                 bg=Theme.BG_MID, troughcolor=Theme.BG_DARK)
        inner = tk.Frame(canvas, bg=Theme.BG_CARD)
        inner.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor=tk.NW)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        def _mw(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind("<Enter>", lambda e: canvas.bind("<MouseWheel>", _mw))
        canvas.bind("<Leave>", lambda e: canvas.unbind("<MouseWheel>"))
        return inner

    def _build_city_info_panel(self, city_id):
        """Show city details, facilities, and connections."""
        inner = self._make_scrollable_info()
        city_data = CITIES.get(city_id, {})
        name = city_data.get("name", city_id)
        biome = city_data.get("biome", "unknown").title()
        desc = city_data.get("description", "")
        if len(desc) > 130:
            desc = desc[:127] + "..."

        tk.Label(inner, text=name.upper(),
                 bg=Theme.BG_CARD, fg=Theme.ACCENT,
                 font=Theme.FONT_BOLD).pack(anchor=tk.W, padx=10, pady=(10, 2))
        tk.Label(inner, text=f"[{biome}]",
                 bg=Theme.BG_CARD, fg=Theme.TEXT_DIM,
                 font=Theme.FONT_SMALL).pack(anchor=tk.W, padx=10)
        tk.Label(inner, text=desc, bg=Theme.BG_CARD, fg=Theme.TEXT_DIM,
                 font=Theme.FONT_SMALL, wraplength=270, justify=tk.LEFT,
                 ).pack(anchor=tk.W, padx=10, pady=(4, 8))

        # Facilities
        sep = tk.Frame(inner, bg=Theme.BORDER, height=1)
        sep.pack(fill=tk.X, padx=8, pady=4)
        tk.Label(inner, text="FACILITIES",
                 bg=Theme.BG_CARD, fg=Theme.TEXT,
                 font=(Theme.FONT_FAMILY, 9, "bold")).pack(
            anchor=tk.W, padx=10, pady=(0, 4))

        services = city_data.get("services", [])
        if services:
            fac_frame = tk.Frame(inner, bg=Theme.BG_CARD)
            fac_frame.pack(fill=tk.X, padx=10, pady=(0, 4))
            r = c = 0
            for svc in services:
                icon = _SERVICE_ICONS.get(svc, "?")
                label = svc.replace("_", " ").title()
                tk.Label(fac_frame, text=f"{icon} {label}",
                         bg=Theme.BG_CARD, fg=Theme.TEXT,
                         font=Theme.FONT_SMALL).grid(
                    row=r, column=c, sticky=tk.W, padx=4, pady=2)
                c += 1
                if c >= 2:
                    c = 0
                    r += 1

        # Connections
        sep2 = tk.Frame(inner, bg=Theme.BORDER, height=1)
        sep2.pack(fill=tk.X, padx=8, pady=6)
        tk.Label(inner, text="CONNECTIONS",
                 bg=Theme.BG_CARD, fg=Theme.TEXT,
                 font=(Theme.FONT_FAMILY, 9, "bold")).pack(
            anchor=tk.W, padx=10, pady=(0, 4))

        conns = city_data.get("travel", {}).get("connections", [])
        if conns:
            for conn in conns:
                dest_id = conn["dest"]
                dest_name = CITIES.get(dest_id, {}).get("name", dest_id)
                ctype = conn.get("type", "land")
                raw = conn.get("travel_time", 0)
                icon = "\u26f5" if ctype == "sea" else "\U0001f9b6"
                type_label = "Sea" if ctype == "sea" else "Land"
                import time_blocks as _tb_conn
                conn_blocks = _tb_conn.travel_blocks(self.player, raw)
                tk.Label(inner,
                         text=f"  {icon} {dest_name} — ≈{conn_blocks} blocks ({type_label})",
                         bg=Theme.BG_CARD, fg=Theme.TEXT_DIM,
                         font=Theme.FONT_SMALL).pack(
                    anchor=tk.W, padx=10, pady=(1, 0))

    def _build_wild_info_panel(self, dungeon):
        """Show wild dungeon details + the previewable reward pool."""
        inner = self._make_scrollable_info()

        biome = str(dungeon.get("biome", "unknown")).title()
        level = dungeon.get("level", 1)
        total_floors = dungeon.get("total_floors", 1)
        cleared = dungeon.get("highest_floor_cleared", 0)
        day = self.player.get("day", 1) if self.player else 1
        days_left = max(0, int(dungeon.get("expire_day", day)) - day)
        nearest_id = dungeon.get("nearest_city", "solmere")
        nearest = CITIES.get(nearest_id, {}).get("name", nearest_id)

        # ── Header ───────────────────────────────────────────────────────
        tk.Label(inner, text=dungeon.get("name", "Wild Dungeon").upper(),
                 bg=Theme.BG_CARD, fg=_WILD_MARKER_OUTLINE,
                 font=Theme.FONT_BOLD).pack(anchor=tk.W, padx=10, pady=(10, 2))
        biome_icon = _WILD_BIOME_ICONS.get(dungeon.get("biome"), _WILD_FALLBACK_ICON)
        tk.Label(inner, text=f"[{biome_icon} {biome} \u00b7 Wild Dungeon]",
                 bg=Theme.BG_CARD, fg=Theme.TEXT_DIM,
                 font=Theme.FONT_SMALL).pack(anchor=tk.W, padx=10)

        # ── Details ──────────────────────────────────────────────────────
        sep = tk.Frame(inner, bg=Theme.BORDER, height=1)
        sep.pack(fill=tk.X, padx=8, pady=6)
        tk.Label(inner, text="DUNGEON",
                 bg=Theme.BG_CARD, fg=Theme.TEXT,
                 font=(Theme.FONT_FAMILY, 9, "bold")).pack(
            anchor=tk.W, padx=10, pady=(0, 4))

        # ── Travel-time estimate (same math as the embark flow; the
        #    off-road leg rolls fresh each call, so this is an estimate) ──
        est_travel = None
        est_blocks = None
        ferry_cost = 0
        if self.player:
            try:
                journey = build_journey_to_dungeon(self.player, dungeon)
            except Exception:
                journey = None
            if journey is not None:
                est_travel = journey["total_time"]
                est_blocks = self._journey_blocks(journey)
                ferry_cost = journey["total_cost"]

        rows = [
            ("Level", str(level)),
            ("Floors", str(total_floors)),
            ("Expires", f"in {days_left} day(s)" if days_left > 0 else "today"),
            ("Est. travel", (f"≈{est_blocks} blocks"
                             if est_blocks is not None else "no route")),
            ("Nearest city", nearest),
        ]
        if ferry_cost > 0:
            rows.append(("Ferry cost", f"{ferry_cost}g"))
        if cleared > 0:
            rows.append(("Progress", f"{cleared}/{total_floors} floors"))
        for label, value in rows:
            row = tk.Frame(inner, bg=Theme.BG_CARD)
            row.pack(fill=tk.X, padx=10, pady=1)
            tk.Label(row, text=label, bg=Theme.BG_CARD, fg=Theme.TEXT_DIM,
                     font=Theme.FONT_SMALL).pack(side=tk.LEFT)
            tk.Label(row, text=value, bg=Theme.BG_CARD, fg=Theme.TEXT,
                     font=Theme.FONT_SMALL).pack(side=tk.RIGHT)

        tk.Label(
            inner,
            text=(f"Clear every floor to claim the pool. "
                  f"Fleeing or falling returns you to {nearest}. "
                  f"Retryable until it crumbles."),
            bg=Theme.BG_CARD, fg=Theme.TEXT_DIM,
            font=Theme.FONT_SMALL, wraplength=270, justify=tk.LEFT,
        ).pack(anchor=tk.W, padx=10, pady=(6, 2))

        # ── Reward pool preview ──────────────────────────────────────────
        sep2 = tk.Frame(inner, bg=Theme.BORDER, height=1)
        sep2.pack(fill=tk.X, padx=8, pady=6)
        tk.Label(inner, text="REWARD POOL",
                 bg=Theme.BG_CARD, fg=Theme.TEXT,
                 font=(Theme.FONT_FAMILY, 9, "bold")).pack(
            anchor=tk.W, padx=10, pady=(0, 4))

        for entry in dungeon.get("reward_pool", []):
            item_id = entry.get("item_id", "")
            rarity = str(entry.get("rarity", "common")).lower()
            item_name = ITEMS.get(item_id, {}).get("name", item_id)
            color = Theme.RARITY_COLORS.get(rarity, Theme.RARITY_COMMON)
            row = tk.Frame(inner, bg=Theme.BG_CARD)
            row.pack(fill=tk.X, padx=10, pady=1)
            tk.Label(row, text=item_name, bg=Theme.BG_CARD, fg=color,
                     font=Theme.FONT_SMALL, anchor=tk.W, justify=tk.LEFT,
                     wraplength=180).pack(side=tk.LEFT)
            tk.Label(row, text=f"[{rarity.upper()}]", bg=Theme.BG_CARD,
                     fg=color, font=(Theme.FONT_FAMILY, 7)).pack(side=tk.RIGHT)

        tk.Label(inner, text="Item stats are rolled on acquisition.",
                 bg=Theme.BG_CARD, fg=Theme.TEXT_DIM,
                 font=(Theme.FONT_FAMILY, 7, "italic")).pack(
            anchor=tk.W, padx=10, pady=(6, 10))

        # ── Travel button ────────────────────────────────────────────────
        self.styled_button(
            inner,
            text="\u25b6 Travel to Dungeon",
            command=lambda: self._on_travel_to_dungeon(dungeon.get("id")),
            width=22, bg=Theme.ACCENT, fg=Theme.TEXT_HEADER,
        ).pack(pady=(2, 12))

    def _build_travel_info_panel(self, city_id, path_result):
        """Show destination details + route breakdown + Travel Here button (travel mode)."""
        inner = self._make_scrollable_info()
        city_data = CITIES.get(city_id, {})
        name = city_data.get("name", city_id)
        biome = city_data.get("biome", "unknown").title()
        desc = city_data.get("description", "")
        if len(desc) > 100:
            desc = desc[:97] + "..."

        tk.Label(inner, text=name.upper(),
                 bg=Theme.BG_CARD, fg=Theme.ACCENT,
                 font=Theme.FONT_BOLD).pack(anchor=tk.W, padx=10, pady=(10, 2))
        tk.Label(inner, text=f"[{biome}]",
                 bg=Theme.BG_CARD, fg=Theme.TEXT_DIM,
                 font=Theme.FONT_SMALL).pack(anchor=tk.W, padx=10)
        tk.Label(inner, text=desc, bg=Theme.BG_CARD, fg=Theme.TEXT_DIM,
                 font=Theme.FONT_SMALL, wraplength=270, justify=tk.LEFT,
                 ).pack(anchor=tk.W, padx=10, pady=(4, 6))

        # Route breakdown
        if path_result and path_result["segments"]:
            sep = tk.Frame(inner, bg=Theme.BORDER, height=1)
            sep.pack(fill=tk.X, padx=8, pady=4)
            tk.Label(inner, text="ROUTE",
                     bg=Theme.BG_CARD, fg=Theme.TEXT,
                     font=(Theme.FONT_FAMILY, 9, "bold")).pack(
                anchor=tk.W, padx=10, pady=(0, 4))

            for i, city_id_in_path in enumerate(path_result["path"]):
                pname = CITIES.get(city_id_in_path, {}).get("name", city_id_in_path)
                indent = "  " * i
                prefix = "\u2514\u2500" if i > 0 else ""
                if i > 0:
                    seg = path_result["segments"][i - 1]
                    icon = "\u26f5" if seg["type"] == "sea" else "\U0001f9b6"
                    label = f"{indent}{prefix}{icon} {seg['effective_time']}m \u2192 {pname}"
                else:
                    label = f"{pname}"
                tk.Label(inner, text=label,
                         bg=Theme.BG_CARD,
                         fg=Theme.TEXT if i == len(path_result["path"]) - 1 else Theme.TEXT_DIM,
                         font=Theme.FONT_SMALL).pack(anchor=tk.W, padx=10, pady=(1, 0))

            tk.Label(inner, text="",
                     bg=Theme.BG_CARD, font=(Theme.FONT_FAMILY, 2)).pack()
            tk.Label(inner,
                     text=(f"Total: ≈{self._journey_blocks(path_result)} blocks"),
                     bg=Theme.BG_CARD, fg=Theme.TEXT,
                     font=Theme.FONT_BOLD).pack(anchor=tk.W, padx=10)
            if path_result["total_cost"] > 0:
                tk.Label(inner, text=f"Ferry cost: {path_result['total_cost']}g",
                         bg=Theme.BG_CARD, fg=Theme.BUFF_NEUTRAL,
                         font=Theme.FONT_SMALL).pack(anchor=tk.W, padx=10)

        # Facilities
        sep2 = tk.Frame(inner, bg=Theme.BORDER, height=1)
        sep2.pack(fill=tk.X, padx=8, pady=6)
        tk.Label(inner, text="FACILITIES",
                 bg=Theme.BG_CARD, fg=Theme.TEXT,
                 font=(Theme.FONT_FAMILY, 9, "bold")).pack(
            anchor=tk.W, padx=10, pady=(0, 4))

        services = city_data.get("services", [])
        if services:
            fac_frame = tk.Frame(inner, bg=Theme.BG_CARD)
            fac_frame.pack(fill=tk.X, padx=10, pady=(0, 4))
            r = c = 0
            for svc in services:
                icon = _SERVICE_ICONS.get(svc, "?")
                label = svc.replace("_", " ").title()
                tk.Label(fac_frame, text=f"{icon} {label}",
                         bg=Theme.BG_CARD, fg=Theme.TEXT,
                         font=Theme.FONT_SMALL).grid(
                    row=r, column=c, sticky=tk.W, padx=4, pady=2)
                c += 1
                if c >= 2:
                    c = 0
                    r += 1

        # ── Travel button (right column, matches the wild dungeon panel) ─
        self.styled_button(
            inner,
            text="\u25b6 Travel Here",
            command=self._on_travel_here,
            width=22, bg=Theme.ACCENT, fg=Theme.TEXT_HEADER,
        ).pack(pady=(10, 12))

    # ── Travel initiation ────────────────────────────────────────────────

    def _on_travel_here(self):
        if self._selected_city is None or self._selected_city == self.city_id:
            return

        # Always recompute — cargo load may have changed since the route was
        # first highlighted, and the graph is tiny.
        result = find_shortest_path(self.player, self.city_id, self._selected_city)
        if result is None or not result["segments"]:
            self.sm.log("No route found to that city.")
            return

        gold = self.player.get("gold", 0)

        # ── Cargo load info for the embark prompt ──────────────────────
        from resources.trade_goods import (
            cargo_total_weight, cargo_capacity, cargo_travel_penalty,
        )
        load = cargo_total_weight(self.player)
        cargo_lines = ""
        if load > 0:
            parts = []
            if any(s["type"] == "land" for s in result["segments"]):
                mcap = cargo_capacity(self.player)
                pen = int(cargo_travel_penalty(self.player) * 100)
                if mcap > 0:
                    parts.append(f"Mount: {load}/{mcap} wt  (+{pen}% time)")
                else:
                    parts.append(f"On foot: {load} wt  (+{pen}% time)")
            if any(s["type"] == "sea" for s in result["segments"]):
                ship = None
                if self.player.get("ship_id"):
                    from resources.ships import get_ship
                    ship = get_ship(self.player["ship_id"])
                scap = ship["cargo_capacity"] if ship else 0
                pen = int(cargo_travel_penalty(self.player, scap) * 100)
                if ship:
                    parts.append(f"{ship['name']}: {load}/{scap} wt  (+{pen}% time)")
                else:
                    parts.append(f"Ferry: {load} wt  (+{pen}% time)")
            cargo_lines = "\n" + "  |  ".join(parts) + "\n"

        # ── Cargo overload check (per-segment, vehicle-aware) ──────────
        blocked = result.get("blocked_segments", [])
        if blocked:
            lines = []
            for seg in blocked:
                frm = CITIES.get(seg["from"], {}).get("name", seg["from"])
                to = CITIES.get(seg["to"], {}).get("name", seg["to"])
                lines.append(f"• {frm} → {to}")
            confirm_dialog(
                parent=self, title="Overloaded",
                message="Your cargo exceeds 1.8× your transport's capacity on:\n\n"
                        + "\n".join(lines)
                        + "\n\nSell cargo at a shop market or stash it in your "
                        "house before traveling.",
                on_yes=lambda: None, yes_text="OK", no_text=None,
            )
            return

        if result["total_cost"] > gold:
            confirm_dialog(
                parent=self, title="Cannot Afford",
                message=f"You need {result['total_cost']}g for ferry tickets, "
                        f"but only have {gold}g.",
                on_yes=lambda: None, yes_text="OK", no_text=None,
            )
            return

        dest_name = CITIES.get(self._selected_city, {}).get("name",
                                                            self._selected_city)

        def _do_embark():
            self._travel_wild = None
            self._start_travel(result)

        confirm_dialog(
            parent=self, title="Embark on Journey",
            message=(
                f"Travel to {dest_name}?\n\n"
                f"Route: {' → '.join(result['path'])}\n"
                f"Total: ≈{self._journey_blocks(result)} blocks  |  "
                f"Segments: {len(result['segments'])}\n"
                + (f"Ferry cost: {result['total_cost']}g\n"
                   if result['total_cost'] > 0 else "")
                + cargo_lines
                + "\nKeep your wits about you."
            ),
            on_yes=_do_embark,
            yes_text="Begin Journey",
            no_text="Cancel",
        )

    def _on_travel_to_dungeon(self, dungeon_id):
        """Travel to a wild dungeon: city route + off-road leg into the ruin."""
        dungeon = get_wild_dungeon(self.player, dungeon_id)
        if dungeon is None:
            self.sm.log("That ruin is no longer on the map.")
            return

        day = self.player.get("day", 1)
        if int(dungeon.get("expire_day", day) or day) < day:
            self.sm.log(f"{dungeon.get('name', 'That ruin')} has already "
                        "crumbled to dust.")
            self._deselect_wild()
            self._draw_wild_dungeons()
            return

        journey = build_journey_to_dungeon(self.player, dungeon)
        if journey is None:
            self.sm.log(f"No route found to {dungeon.get('name', 'the ruin')}.")
            return

        gold = self.player.get("gold", 0)

        # ── Cargo overload check (mirrors _on_travel_here) ──────────────
        blocked = journey.get("blocked_segments", [])
        if blocked:
            lines = []
            for seg in blocked:
                frm = CITIES.get(seg["from"], {}).get("name", seg["from"])
                if str(seg["to"]).startswith("wild:"):
                    to = dungeon.get("name", seg["to"])
                else:
                    to = CITIES.get(seg["to"], {}).get("name", seg["to"])
                lines.append(f"\u2022 {frm} \u2192 {to}")
            confirm_dialog(
                parent=self, title="Overloaded",
                message="Your cargo exceeds 1.8\u00d7 your transport's capacity on:\n\n"
                        + "\n".join(lines)
                        + "\n\nSell cargo at a shop market or stash it in your "
                        "house before traveling.",
                on_yes=lambda: None, yes_text="OK", no_text=None,
            )
            return

        if journey["total_cost"] > gold:
            confirm_dialog(
                parent=self, title="Cannot Afford",
                message=(f"You need {journey['total_cost']}g for ferry tickets, "
                         f"but only have {gold}g."),
                on_yes=lambda: None, yes_text="OK", no_text=None,
            )
            return

        # ── Route summary ────────────────────────────────────────────────
        route_parts = []
        for node in journey["path"]:
            if str(node).startswith("wild:"):
                icon = _WILD_BIOME_ICONS.get(dungeon.get("biome"),
                                             _WILD_FALLBACK_ICON)
                route_parts.append(f"{icon} {dungeon.get('name', node)}")
            else:
                route_parts.append(CITIES.get(node, {}).get("name", node))
        route_line = " \u2192 ".join(route_parts)

        def _do_embark():
            self._travel_wild = dungeon
            self._start_travel(journey)

        confirm_dialog(
            parent=self, title="Embark on Journey",
            message=(
                f"Travel to {dungeon.get('name', 'the ruin')} "
                f"(Lv {dungeon.get('level', '?')})?\n\n"
                f"Route: {route_line}\n"
                f"Total: ≈{self._journey_blocks(journey)} blocks  |  "
                f"Segments: {len(journey['segments'])}\n"
                + (f"Ferry cost: {journey['total_cost']}g\n"
                   if journey["total_cost"] > 0 else "")
                + "\nThe ruin will not wait forever. Keep your wits about you."
            ),
            on_yes=_do_embark,
            yes_text="Begin Journey",
            no_text="Cancel",
        )

    def _journey_blocks(self, journey):
        """Total block cost of a journey (per-hop rounding; docs §8/§16)."""
        import time_blocks
        total = 0
        for seg in (journey or {}).get("segments", []) or []:
            total += time_blocks.travel_blocks(self.player,
                                               seg.get("effective_time", 0))
        return total

    def _start_travel(self, result):
        """Enter travel mode. Night sailings are allowed (playtest 2026-10-13) —
        the phase's danger is the price, not a closed harbour."""
        self._mode = self.MODE_TRAVEL
        self._travel_segments = result["segments"]
        self._travel_path = result["path"]
        self._travel_seg_idx = 0
        self._travel_paused = False
        self._travel_player_dead = False

        self._btn_back.config(state=tk.DISABLED, text="\u23f3 Traveling...")
        self._canvas.config(cursor="")
        self._update_top_bar()  # show departure city

        self._build_travel_log()

        # Place dot at start city
        start_city = self._travel_path[0]
        if start_city in _CITY_POSITIONS:
            sx, sy = _CITY_POSITIONS[start_city]
            cx = sx + _NODE_W // 2
            cy = sy + _NODE_H // 2
            self._travel_dot = self._canvas.create_oval(
                cx - 5, cy - 5, cx + 5, cy + 5,
                fill="#f1c40f", outline="#fff", width=1.5,
                tags=("travel_dot",),
            )

        self._log(f"Departing {CITIES.get(start_city, {}).get('name', start_city)}...",
                  "text")
        total_blocks = self._journey_blocks(result)
        self._log(f"The road ahead: ≈{total_blocks} blocks of travel.", "dim")
        self._log("\u2500" * 28, "dim")

        if result["total_cost"] > 0:
            self.player["gold"] = self.player.get("gold", 0) - result["total_cost"]
            self._log(f"Ferry tickets: -{result['total_cost']}g  "
                      f"(Balance: {self.player['gold']}g)", "gold")

        self._animate_next_segment()

    # ── Travel log UI ────────────────────────────────────────────────────

    def _build_travel_log(self):
        self._clear_info_panel()
        tk.Label(self._info_frame, text="TRAVEL LOG",
                 bg=Theme.BG_CARD, fg=Theme.ACCENT,
                 font=Theme.FONT_BOLD).pack(pady=(10, 4))

        log_container = tk.Frame(self._info_frame, bg=Theme.BG_CARD)
        log_container.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 6))

        self._log_text = tk.Text(
            log_container, wrap=tk.WORD, state=tk.DISABLED,
            bg="#0d0d1f", fg=Theme.TEXT_DIM,
            font=Theme.FONT_SMALL, highlightthickness=0, borderwidth=0,
            height=18,
        )
        scrollbar = tk.Scrollbar(log_container, orient=tk.VERTICAL,
                                 command=self._log_text.yview,
                                 bg=Theme.BG_MID, troughcolor=Theme.BG_DARK)
        self._log_text.configure(yscrollcommand=scrollbar.set)
        self._log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        for tag_name, fg_color in [
            ("text", Theme.TEXT), ("dim", Theme.TEXT_DIM),
            ("gold", Theme.BUFF_NEUTRAL), ("red", Theme.BUFF_NEGATIVE),
            ("green", Theme.BUFF_POSITIVE), ("cyan", "#00d2d3"),
        ]:
            self._log_text.tag_configure(tag_name, foreground=fg_color)

    def _log(self, text, tag="text"):
        if not hasattr(self, '_log_text') or not self._log_text.winfo_exists():
            return
        try:
            self._log_text.config(state=tk.NORMAL)
            self._log_text.insert(tk.END, text + "\n", tag)
            self._log_text.see(tk.END)
            self._log_text.config(state=tk.DISABLED)
        except tk.TclError:
            pass

    # ── Segment animation ────────────────────────────────────────────────

    def _animate_next_segment(self):
        if self._travel_player_dead:
            return
        if self._travel_seg_idx >= len(self._travel_segments):
            self._on_arrival()
            return

        seg = self._travel_segments[self._travel_seg_idx]
        from_id = seg["from"]
        to_id = seg["to"]

        start = self._canvas_node_pos(from_id)
        end = self._canvas_node_pos(to_id)
        if start is None or end is None:
            self._travel_seg_idx += 1
            self._animate_next_segment()
            return
        self._travel_seg_start = start
        self._travel_seg_end = end

        from_name = CITIES.get(from_id, {}).get("name", from_id)
        to_name = self._node_display_name(to_id)
        seg_type = seg["type"]
        icon = "\u26f5" if seg_type == "sea" else "\U0001f9b6"
        import time_blocks as _tb_hop
        _hop_blocks = _tb_hop.travel_blocks(self.player, seg["effective_time"])
        self._log(f"{icon} {from_name} → {to_name}  "
                  f"(≈{_hop_blocks} blocks, {seg_type})", "text")

        self._travel_event_queue = self._roll_events(seg)
        self._travel_event_idx = 0
        self._travel_step = 0
        self._travel_paused = False
        self._do_anim_step()

    # ── Event Horizon travel + result routing ───────────────────────────

    def _on_travel_to_horizon(self):
        """Travel to the distortion: city route + off-road leg into the tear."""
        import event_horizon as eh
        site = eh.event_horizon_site(self.player)
        if site is None:
            self.sm.log("The distortion is not visible to you yet.")
            return
        journey = eh.build_journey_to_site(self.player)
        if journey is None:
            self.sm.log("No route found to the Event Horizon.")
            return
        gold = self.player.get("gold", 0)
        blocked = journey.get("blocked_segments", [])
        if blocked:
            lines = []
            for seg in blocked:
                frm = CITIES.get(seg["from"], {}).get("name", seg["from"])
                to = ("the Event Horizon" if str(seg["to"]) == "horizon"
                      else CITIES.get(seg["to"], {}).get("name", seg["to"]))
                lines.append(f"\u2022 {frm} \u2192 {to}")
            confirm_dialog(
                parent=self, title="Overloaded",
                message=("Your cargo exceeds 1.8\u00d7 your transport's capacity on:\n\n"
                         + "\n".join(lines)
                         + "\n\nSell cargo at a shop market or stash it in your "
                           "house before traveling."),
                on_yes=lambda: None, yes_text="OK", no_text=None,
            )
            return
        if journey["total_cost"] > gold:
            confirm_dialog(
                parent=self, title="Cannot Afford",
                message=(f"You need {journey['total_cost']}g for ferry tickets, "
                         f"but only have {gold}g."),
                on_yes=lambda: None, yes_text="OK", no_text=None,
            )
            return

        route_parts = []
        for node in journey["path"]:
            if node == "horizon":
                route_parts.append("\U0001F300 The Event Horizon")
            else:
                route_parts.append(CITIES.get(node, {}).get("name", node))
        route_line = " \u2192 ".join(route_parts)

        def _do_embark():
            self._travel_horizon = site
            self._start_travel(journey)

        confirm_dialog(
            parent=self, title="Embark on Journey",
            message=(f"Travel to THE EVENT HORIZON?\n\n{route_line}\n\n"
                     f"Est. journey: ≈{self._journey_blocks(journey)} blocks"
                     + (f"  |  Ferry cost: {journey['total_cost']}g"
                        if journey["total_cost"] else "")
                     + "\n\nVesper waits at the site."),
            on_yes=_do_embark, on_no=lambda: None,
            yes_text="Embark", no_text="Cancel",
        )

    def _arrive_at_horizon(self):
        """End the journey, then play Vesper's arrival scene (docs §6.1)."""
        player = self.player
        site = self._travel_horizon or {}
        nearest = site.get("nearest_city", player.get("location", "solmere"))
        player["origin_city"] = nearest
        self._stop_travel_visuals()
        self._travel_horizon = None
        self._log("\u2500" * 28, "dim")
        self._log("\U0001F300 The air tears open ahead \u2014 "
                  "THE EVENT HORIZON.", "cyan")
        self._log("Vesper is waiting at the seam.", "dim")

        from gui.screens.facility_screen import FacilityScreen
        from facilities.event_horizon_intro import event_horizon_arrival_service
        self.sm.switch_to(
            FacilityScreen,
            title="The Event Horizon",
            func=event_horizon_arrival_service,
            func_args=(player, nearest),
            on_close=self._after_eh_scene,
            push_history=False,
        )

    def _after_eh_scene(self, result):
        """Route the arrival scene's choice: enter / resume / fresh / boss_rush / leave."""
        import event_horizon as eh
        player = self.player
        nearest = player.get("origin_city", "solmere")

        if result in ("enter", "resume", "fresh", "boss_rush", "boss_rush_fresh"):
            def _launch_eh_run():
                # Never show another dungeon's log under the EH branding.
                player.pop("_dungeon_log", None)
                # Region hygiene: stops stale Wonderland quirks / biome checks
                # from bleeding into rift combat displays.
                player["dungeon_region"] = "event_horizon"
                # Re-attach suspended run effects (flasks/cards/Entropy) —
                # idempotent; fresh runs restore nothing.
                eh.restore_event_horizon_effects(player)
                room = int(eh.ensure_eh_state(player).get("room", 0))
                player["_eh_in_run"] = True
                player["location"] = "dungeon"
                if result == "resume":
                    self.sm.log(
                        f"\U0001F300 The Horizon resumes you at room {room + 1}.")
                else:
                    self.sm.log("\U0001F300 Space folds open. Vesper's mark "
                                "burns \u2014 and the world inverts.")
                from gui.screens.dungeon_screen import DungeonScreen
                self.sm.switch_to(DungeonScreen, on_result=self._on_eh_result,
                                  push_history=False)

            if result in ("fresh", "boss_rush_fresh"):
                amount, _ = eh.grant_payout(player, death=False)
                summary = eh.build_run_summary(player, payout=amount)
                best = eh.clear_run(player)
                if result == "fresh":
                    eh.begin_run(player, nearest)
                    self.sm.log(
                        f"The old run collapses \u2014 +{amount} gold recovered "
                        f"(deepest room {best}).")
                else:
                    ok, reasons = eh.begin_rush(player, nearest)
                    if not ok:
                        # Gates changed underneath us — fall back to a run.
                        eh.begin_run(player, nearest)
                        self.sm.log("The echoes do not answer: "
                                    + "; ".join(reasons) + ".")
                    else:
                        self.sm.log(
                            f"\u2694 The sitting run collapses \u2014 +{amount} gold "
                            f"recovered (deepest room {best}). The gathered "
                            f"echoes rise.")
                player["_eh_last_summary"] = summary
                self._show_eh_summary_then(_launch_eh_run)
                return
            if result == "enter":
                eh.begin_run(player, nearest)
            if result == "boss_rush":
                ok, reasons = eh.begin_rush(player, nearest)
                if not ok:
                    self.sm.log("The echoes do not answer: "
                                + "; ".join(reasons) + ".")
                    player["location"] = nearest
                    from gui.screens.city_screen import CityScreen
                    self.sm.switch_to(CityScreen, push_history=False)
                    return
                self.sm.log("\u2694 The gathered echoes rise \u2014 the Boss Rush begins.")
            _launch_eh_run()
            return

        # "leave" (or scene aborted) \u2014 back to the nearest city.
        player["location"] = nearest
        self.sm.log("You leave the seam to its turning.")
        from gui.screens.city_screen import CityScreen
        self.sm.switch_to(CityScreen, push_history=False)

    def _show_eh_summary_then(self, on_close):
        """Show the stashed EH run aftermath (if any), then run `on_close`."""
        summary = self.player.pop("_eh_last_summary", None)
        if not summary:
            on_close()
            return
        from gui.widgets.run_summary_dialog import run_summary_dialog
        # This screen may already be destroyed (switch_to destroys the old
        # screen before on_result/on_close fire) — parent to the app root.
        parent = getattr(getattr(self, "sm", None), "root", None) or self
        run_summary_dialog(
            parent,
            title="Event Horizon \u2014 Run Summary",
            heading="THE EVENT HORIZON \u2014 RUN SUMMARY",
            subtitle=summary.get("subtitle", ""),
            body="\n".join(summary.get("lines", [])),
            on_close=on_close,
        )

    def _on_eh_result(self, result):
        """DungeonScreen on_result for Event Horizon runs."""
        if result == "dead":
            summary = self.player.get("_eh_last_summary") or {}
            room = summary.get("data", {}).get("room", "?")

            def _to_death():
                self._handle_death(death_type="event_horizon", floor=room)

            self._show_eh_summary_then(_to_death)
            return
        if result == "save_exit":
            self.sm.log("Game saved. Exiting to menu.")
            self.sm.player = None
            from gui.screens.main_menu_screen import MainMenuScreen
            self.sm.switch_to(MainMenuScreen)
            return

        # "eh_quit" / "timeout" / None — defensive scrub (button-flees kill the
        # dungeon thread before its in-dungeon cleanup can run; idempotent
        # otherwise). Suspended-run state stays untouched here.
        p = self.player
        p.pop("_eh_in_run", None)
        prev_floor = p.pop("_eh_prev_floor", None)
        if prev_floor is not None:
            p["floor"] = prev_floor
        p["cutlass_high_tide_stacks"] = 0
        p.pop("cutlass_high_tide_floor", None)
        if p.get("location") == "dungeon":
            p["location"] = p.get("origin_city", "solmere")
        # Button-flee leaves the run suspended rather than ended — detach its
        # effects so no ENT/flask tags leak into cities (idempotent; the
        # eh_quit path already stripped via the wipe).
        import event_horizon as eh
        eh.strip_event_horizon_effects(p, legacy=True)
        if result == "eh_rush_complete":
            self.sm.log("⚔ The last echo falls — the Boss Rush is complete.")
        elif result == "eh_quit":
            self.sm.log("The Horizon releases you. The run is over.")
        elif result == "fled":
            self.sm.log("You step out of the rift — the run is suspended. "
                        "Resume at the Event Horizon site.")
        from gui.screens.city_screen import CityScreen

        def _to_city():
            self.sm.switch_to(CityScreen, push_history=False)

        self._show_eh_summary_then(_to_city)

    def _canvas_node_pos(self, node_id):
        """Canvas center (x, y) for a city / wild / horizon travel target."""
        if node_id in _CITY_POSITIONS:
            x, y = _CITY_POSITIONS[node_id]
            return (x + _NODE_W // 2, y + _NODE_H // 2)
        if str(node_id).startswith("wild:") and self._travel_wild:
            px, py = self._travel_wild.get("position", (0, 0))
            return (px, py)
        if node_id == "horizon" and self._travel_horizon:
            px, py = self._travel_horizon.get("position", (0, 0))
            return (px, py)
        return None

    def _node_display_name(self, node_id):
        """Display name for a city / wild / horizon travel target."""
        name = CITIES.get(node_id, {}).get("name")
        if name:
            return name
        if str(node_id).startswith("wild:") and self._travel_wild:
            return self._travel_wild.get("name", node_id)
        if node_id == "horizon" and self._travel_horizon:
            return self._travel_horizon.get("name", "The Event Horizon")
        return node_id

    def _do_anim_step(self):
        if self._travel_paused or self._travel_player_dead:
            return

        total = _ANIM_STEPS
        self._travel_step += 1

        t = self._travel_step / total
        t_smooth = t * t * (3 - 2 * t)  # ease in-out
        sx, sy = self._travel_seg_start
        ex, ey = self._travel_seg_end
        cx = sx + (ex - sx) * t_smooth
        cy = sy + (ey - sy) * t_smooth

        if self._travel_dot:
            self._canvas.coords(self._travel_dot, cx - 5, cy - 5, cx + 5, cy + 5)
            self._canvas.lift(self._travel_dot)

        # Check for event at checkpoints
        cps = [int(total * (i + 1) / (_EVENT_CHECKPOINTS + 1))
               for i in range(_EVENT_CHECKPOINTS)]
        if (self._travel_event_idx < len(self._travel_event_queue) and
                self._travel_event_idx < len(cps) and
                self._travel_step >= cps[self._travel_event_idx]):
            evt = self._travel_event_queue[self._travel_event_idx]
            self._travel_event_idx += 1
            self._travel_paused = True
            self._handle_event(evt)
            return

        if self._travel_step >= total:
            self._on_segment_done()
        else:
            self._travel_anim_job = self.after(_ANIM_INTERVAL, self._do_anim_step)

    def _on_segment_done(self):
        seg = self._travel_segments[self._travel_seg_idx]
        to_id = seg["to"]

        to_name = self._node_display_name(to_id)
        if str(to_id).startswith("wild:") or to_id == "horizon":
            # Off-road leg done — entry handled by _on_arrival
            self._log(f"You reach the {to_name}.", "green")
        else:
            self.player["location"] = to_id
            self._log(f"Arrived at {to_name}.", "green")
        self._update_top_bar()  # update city in top bar

        # ── Segment cost in blocks; the day boundary offers camp (§8) ────
        import time_blocks
        seg_blocks = time_blocks.travel_blocks(self.player, seg["effective_time"])
        if (seg_blocks >= time_blocks.blocks_remaining(self.player)
                and time_blocks.can_camp(self.player)):
            self._travel_paused = True
            next_idx = self._travel_seg_idx + 1
            next_target = (self._travel_segments[next_idx]["to"]
                           if next_idx < len(self._travel_segments) else None)
            ahead = (self._node_display_name(next_target)
                     if next_target else "your destination")
            confirm_dialog(
                parent=self, title="Nightfall on the Road",
                message=(f"The day runs out before you reach {ahead}.\n\n"
                         "Set camp for the night? You resume at morning, "
                         "without exhaustion."),
                on_yes=lambda: self._start_camp(seg_blocks),
                on_no=lambda: self._resolve_segment_spend(seg_blocks, camp=False),
                yes_text="Set Camp", no_text="March On",
            )
            return
        self._resolve_segment_spend(seg_blocks, camp=False)

    def _start_camp(self, seg_blocks):
        """Open the camp FacilityScreen as an overlay; travel resumes after."""
        try:
            from facilities.camp import camp_event
            from gui.screens.facility_screen import FacilityScreen

            def _after_camp(_result=None):
                try:
                    self.sm.dismiss_overlay()
                except Exception:
                    pass
                self._resolve_segment_spend(seg_blocks, camp=True)

            self.sm.push_overlay(
                FacilityScreen,
                title="Set Camp",
                func=camp_event,
                func_args=(self.player,),
                on_close=_after_camp,
            )
        except Exception:
            # Fallback: log-only camp (no overlay) — still restful.
            self._resolve_segment_spend(seg_blocks, camp=True)

    def _resolve_segment_spend(self, seg_blocks, camp):
        """Apply the segment's block cost, then continue the journey."""
        import time_blocks
        days = time_blocks.spend_travel_segment(self.player, seg_blocks, camp=camp)
        if camp:
            self._log("You sleep under canvas; the road continues at dawn.", "green")
        elif days:
            self._log("You marched through the night — exhaustion sets in.", "red")
        self._travel_paused = False
        self._update_top_bar()
        self._continue_after_segment()

    def _continue_after_segment(self):
        self._travel_seg_idx += 1
        if self._travel_seg_idx >= len(self._travel_segments):
            self._on_arrival()
            return

        to_id = self._travel_segments[self._travel_seg_idx - 1]["to"]
        next_seg = self._travel_segments[self._travel_seg_idx]
        if next_seg["type"] == "sea" and self._has_port(to_id):
            self._travel_paused = True
            self._show_sea_prompt(to_id, next_seg)
            return

        self._log("Continuing journey...", "dim")
        self.after(600, self._animate_next_segment)

    # ── Sea prompt ───────────────────────────────────────────────────────

    def _show_sea_prompt(self, port_city_id, next_seg):
        port_name = CITIES.get(port_city_id, {}).get("name", port_city_id)
        dest_name = CITIES.get(next_seg["to"], {}).get("name", next_seg["to"])
        ship = None
        ship_id = self.player.get("ship_id")
        if ship_id:
            from resources.ships import get_ship
            ship = get_ship(ship_id)
        cost = next_seg.get("cost", 0)
        eff_time = next_seg["effective_time"]
        import time_blocks as _tb_sea
        sea_blocks = _tb_sea.travel_blocks(self.player, eff_time)

        if ship:
            msg = (f"You've arrived at {port_name}.\n\n"
                   f"Next: \u26f5 Sea voyage to {dest_name}\n"
                   f"(≈{sea_blocks} blocks, your {ship['name']} is ready)\n\n"
                   f"Continue your journey?")
        else:
            msg = (f"You've arrived at {port_name}.\n\n"
                   f"Next: \u26f5 Ferry to {dest_name}\n"
                   f"(≈{sea_blocks} blocks, ticket: {cost}g)\n\n"
                   f"Continue your journey?")

        def _yes():
            self._log(f"Setting sail for {dest_name}...", "cyan")
            self._travel_paused = False
            self.after(400, self._animate_next_segment)

        def _no():
            self._log(f"Decided to stay in {port_name}.", "dim")
            self._log(f"Journey ended at {port_name}.", Theme.ACCENT)
            self._finish_travel()

        confirm_dialog(
            parent=self, title=f"{port_name} — Port",
            message=msg, on_yes=_yes, on_no=_no,
            yes_text="Continue", no_text="Stay Here",
        )

    # ── Travel events ────────────────────────────────────────────────────

    def _roll_events(self, seg):
        from facilities.travel_events import LAND_EVENTS, SEA_EVENTS
        pool = SEA_EVENTS if seg["type"] == "sea" else LAND_EVENTS
        events = []
        for _ in range(_EVENT_CHECKPOINTS):
            if random.random() < 0.35:
                weights = [e["weight"] for e in pool]
                evt = random.choices(pool, weights=weights)[0]
                events.append({"type": evt["type"], "seg": seg})
        return events

    def _handle_event(self, event):
        etype = event["type"]
        seg = event["seg"]

        if etype == "combat":
            self._log("\u2694 Enemies approach!", "red")
            self._launch_combat(seg)
        elif etype == "discovery":
            self._log("\u2728 You find something interesting on the path.", "green")
            self.after(0, lambda: self._handle_discovery_gui(event))
        elif etype == "hazard":
            self.after(0, lambda: self._handle_hazard_gui(event))
        elif etype == "merchant":
            self._log("\U0001f3ea A wandering merchant offers wares.", "gold")
            self.after(0, lambda: self._handle_merchant_gui(event))
        elif etype == "storm":
            self.after(0, lambda: self._handle_storm_gui(event))
        elif etype == "calm":
            self.after(0, lambda: self._handle_calm_gui(event))
        else:
            self._resume_anim()

    # ── Event handlers (GUI dialogs) ────────────────────────────────────

    def _handle_merchant_gui(self, event):
        """Show a merchant buy/sell dialog styled like the shop UI.

        Deferred with after(0, ...) to avoid event-loop issues when
        creating a grab-set Toplevel during an animation callback.
        """
        # Defer dialog creation to the next mainloop iteration (same pattern
        # as _launch_combat), avoiding grab/deadlock issues.
        self.after(0, lambda: self._build_merchant_dialog(event))

    def _build_merchant_dialog(self, event):
        """Build and show the wandering merchant dialog (called via after(0))."""
        player = self.player

        # Build stock using same logic as travel_events._handle_merchant
        stock = []
        for _ in range(random.randint(2, 3)):
            if random.random() < 0.30:
                good_id = roll_cargo_good()
                item = build_cargo(good_id)
                your_price, road_price = cargo_merchant_stock_price(good_id, player)
                stock.append((item, your_price, road_price))
                continue
            item_id = _random_item_id()
            rarity = _merchant_stock_rarity(player)
            item = build_item(item_id, rarity)
            your_price, road_price = _merchant_price(player, item)
            stock.append((item, your_price, road_price))

        cha_disc = _charisma_discount(player)

        # ── Build toplevel dialog ────────────────────────────────────────
        try:
            parent = self.winfo_toplevel()
        except tk.TclError:
            parent = self
        dialog = tk.Toplevel(parent)
        dialog.title("Wandering Merchant")
        dialog.transient(parent)
        dialog.resizable(False, False)
        dialog.configure(bg=Theme.BG_DARK)

        # Wider dialog to prevent Buy button cutoff
        dw, dh = 540, 360 + len(stock) * 56
        try:
            dh = min(dh, parent.winfo_screenheight() - 80)
        except Exception:
            pass

        # ── Header ──────────────────────────────────────────────────────
        tk.Label(
            dialog, text='"Wares! Quality goods — fair price for a fellow traveler!"',
            bg=Theme.BG_DARK, fg=Theme.ACCENT, font=Theme.FONT_BOLD,
            wraplength=dw - 40, justify=tk.CENTER,
        ).pack(padx=20, pady=(14, 2))

        gold_text = f"Your gold: {player.get('gold', 0)}g"
        if cha_disc > 0:
            gold_text += f"  |  Charisma discount: {cha_disc:.0f}%"
        gold_label = tk.Label(
            dialog, text=gold_text,
            bg=Theme.BG_DARK, fg=Theme.TEXT_DIM, font=Theme.FONT_SMALL,
        )
        gold_label.pack(padx=20, pady=(0, 8))

        # ── Stock items ─────────────────────────────────────────────────
        sep = tk.Frame(dialog, bg=Theme.BORDER, height=1)
        sep.pack(fill=tk.X, padx=20)

        stock_frame = tk.Frame(dialog, bg=Theme.BG_DARK)
        stock_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)

        # Track buy buttons so we can disable them after purchase
        buy_buttons = []

        def _refresh_gold():
            new_text = f"Your gold: {player.get('gold', 0)}g"
            if cha_disc > 0:
                new_text += f"  |  Charisma discount: {cha_disc:.0f}%"
            try:
                gold_label.configure(text=new_text)
            except tk.TclError:
                pass

        # ── Callbacks ───────────────────────────────────────────────────
        def _do_buy(idx):
            """Buy stock[idx]. Disable button after purchase (1 per item)."""
            try:
                item, your_price, _ = stock[idx]
                if player.get("gold", 0) >= your_price:
                    player["gold"] -= your_price
                    if add_item_to_inventory(player, item.copy()):
                        self._log(f'Bought [{item["name"]}] for {your_price}g.', "gold")
                        # Disable the button — merchant only has 1 of each
                        buy_buttons[idx].configure(
                            text="Sold", state=tk.DISABLED,
                            bg=Theme.BG_MID, fg=Theme.TEXT_DIM,
                        )
                    else:
                        self._log(f'Bag full! [{item["name"]}] could not be purchased.', "red")
                        player["gold"] += your_price  # refund
                else:
                    self._log(f'Not enough gold for [{item["name"]}] '
                              f'(need {your_price}g).', "red")
                _refresh_gold()
            except Exception as ex:
                self._log(f"[Merchant error: {ex}]", "red")

        def _do_sell():
            """Defer sell dialog to avoid nested grab issues."""
            dialog.grab_release()
            # Use after(0) so sell dialog opens in a clean event-loop iteration
            dialog.after(0, lambda: self._merchant_sell_dialog(player, dialog, _refresh_gold))

        def _do_leave():
            """Close dialog and resume travel."""
            try:
                self._log('"Safe roads, traveler!"', "dim")
            except Exception:
                pass
            try:
                dialog.grab_release()
                dialog.destroy()
            except tk.TclError:
                pass
            self._resume_anim()

        # ── Build stock item rows ───────────────────────────────────────
        for i, (item, your_price, road_price) in enumerate(stock):
            # Card frame for this item
            card = tk.Frame(stock_frame, bg=Theme.BG_CARD,
                            highlightthickness=1, highlightbackground=Theme.BORDER)
            card.pack(fill=tk.X, pady=2, padx=4)

            # Top row: item name + stat (wraps full width, no button competition)
            stat = _item_stat_line(item)
            name_lbl = tk.Label(
                card, text=f"{item['name']}  {stat}",
                bg=Theme.BG_CARD, fg=Theme.TEXT, font=Theme.FONT_SMALL,
                wraplength=dw - 60, justify=tk.LEFT, anchor=tk.W,
            )
            name_lbl.pack(fill=tk.X, padx=10, pady=(6, 0))

            # Bottom row: price (left) + Buy button (right)
            bottom = tk.Frame(card, bg=Theme.BG_CARD)
            bottom.pack(fill=tk.X, padx=10, pady=(2, 6))

            if cha_disc > 0 and your_price < road_price:
                price_str = f"{your_price}g  (road: {road_price}g)"
            else:
                price_str = f"{your_price}g"
            tk.Label(
                bottom, text=price_str,
                bg=Theme.BG_CARD, fg=Theme.BUFF_NEUTRAL, font=Theme.FONT_BOLD,
            ).pack(side=tk.LEFT)

            btn = tk.Button(
                bottom, text="Buy",
                bg=Theme.ACCENT, fg="#ffffff", font=Theme.FONT_SMALL,
                activebackground="#45a049", activeforeground="#ffffff",
                relief=tk.FLAT, padx=12, pady=2, cursor="hand2",
                command=lambda idx=i: _do_buy(idx),
            )
            btn.pack(side=tk.RIGHT)
            buy_buttons.append(btn)

        # ── Bottom buttons ──────────────────────────────────────────────
        btn_frame = tk.Frame(dialog, bg=Theme.BG_DARK)
        btn_frame.pack(fill=tk.X, padx=20, pady=(8, 14))

        sell_btn = tk.Button(
            btn_frame, text="Sell Items",
            bg=Theme.BG_MID, fg=Theme.TEXT, font=Theme.FONT,
            activebackground="#3a3a5a", activeforeground=Theme.TEXT,
            relief=tk.FLAT, padx=12, pady=4, cursor="hand2",
            command=_do_sell,
        )
        sell_btn.pack(side=tk.LEFT)

        leave_btn = tk.Button(
            btn_frame, text="Move On",
            bg="#5a3a5a", fg=Theme.TEXT, font=Theme.FONT,
            activebackground="#6a4a6a", activeforeground=Theme.TEXT,
            relief=tk.FLAT, padx=12, pady=4, cursor="hand2",
            command=_do_leave,
        )
        leave_btn.pack(side=tk.RIGHT)

        # ── Keyboard / close bindings ────────────────────────────────────
        dialog.bind("<Escape>", lambda e: _do_leave())
        dialog.protocol("WM_DELETE_WINDOW", _do_leave)

        # ── NOW center, map, grab, and focus ────────────────────────────
        dialog.update_idletasks()
        try:
            px = parent.winfo_x()
            py = parent.winfo_y()
            pw = parent.winfo_width()
            ph = parent.winfo_height()
            dialog.geometry(f"{dw}x{dh}+{px + (pw - dw) // 2}+{py + (ph - dh) // 2}")
        except Exception:
            pass

        # Use update() instead of wait_visibility() to avoid hangs
        dialog.update()
        dialog.grab_set()
        leave_btn.focus_set()

    def _merchant_sell_dialog(self, player, merchant_dialog=None, on_done=None):
        """Show a sell-to-merchant dialog (nested popup).

        Args:
            player: Player state dict.
            merchant_dialog: The parent merchant Toplevel (to re-grab after close).
            on_done: Optional callback() called after the sell dialog closes.
        """
        inv = player.get("inventory", [])
        if not inv:
            self._log('"Nothing I want off you — yet."', "dim")
            if on_done:
                on_done()
            if merchant_dialog:
                try:
                    merchant_dialog.grab_set()
                except tk.TclError:
                    pass
            return

        # Cargo sells at road cargo rates; everything else at the normal rate
        sellable = []
        for i in inv:
            if i.get("type") == "cargo":
                sellable.append((i, cargo_merchant_sell_price(i)))
            else:
                sellable.append((i, _sell_price(i, player)))
        if not sellable:
            self._log('"Nothing I want off you — yet."', "dim")
            if on_done:
                on_done()
            if merchant_dialog:
                try:
                    merchant_dialog.grab_set()
                except tk.TclError:
                    pass
            return

        try:
            parent = self.winfo_toplevel()
        except tk.TclError:
            parent = self
        sd = tk.Toplevel(parent)
        sd.title("Sell to Merchant")
        sd.transient(parent)
        sd.resizable(False, False)
        sd.configure(bg=Theme.BG_DARK)

        # Dynamic height based on inventory size
        dw2, dh2 = 460, min(140 + len(sellable) * 44, 520)

        tk.Label(
            sd, text="The merchant eyes your pack with practiced interest.\n"
                     "(Road sell rate: ~75% of city shop value)",
            bg=Theme.BG_DARK, fg=Theme.TEXT_DIM, font=Theme.FONT_SMALL,
            wraplength=dw2 - 40, justify=tk.CENTER,
        ).pack(padx=20, pady=(12, 6))

        sep2 = tk.Frame(sd, bg=Theme.BORDER, height=1)
        sep2.pack(fill=tk.X, padx=20)

        # ── Callbacks ───────────────────────────────────────────────────
        def _do_sell_item(idx):
            """Sell one item and close the dialog (one sale per open)."""
            try:
                from combat.weapon.wedding_specials import is_wedding_item_soulbound
                if idx < 0 or idx >= len(sellable):
                    _close_sell()
                    return
                item, unit_price = sellable[idx]
                if is_wedding_item_soulbound(item):
                    self._log(f"[{item['name']}] is soulbound — cannot be sold.", "red")
                    _close_sell()
                    return
                if is_unique_item(item):
                    self._log(f"[{item['name']}] is unique — cannot be sold.", "red")
                    _close_sell()
                    return
                count = item.get("count", 1)
                gold = unit_price * count
                remove_item_by_reference(player, item, count)
                player["gold"] = player.get("gold", 0) + gold
                self._log(f'Sold [{item["name"]}] for {gold}g.', "gold")
            except Exception as ex:
                self._log(f"[Sell error: {ex}]", "red")
            _close_sell()

        def _close_sell():
            """Close sell dialog and restore merchant dialog grab."""
            try:
                sd.grab_release()
                sd.destroy()
            except tk.TclError:
                pass
            if on_done:
                on_done()
            if merchant_dialog:
                try:
                    merchant_dialog.grab_set()
                except tk.TclError:
                    pass

        # ── Build sell rows (scrollable if many items) ──────────────────
        # Canvas + scrollbar for long inventories
        needs_scroll = len(sellable) > 6
        if needs_scroll:
            sell_canvas = tk.Canvas(sd, bg=Theme.BG_DARK, highlightthickness=0, height=280)
            sell_scroll = tk.Scrollbar(sd, orient=tk.VERTICAL, command=sell_canvas.yview,
                                       bg=Theme.BG_MID, troughcolor=Theme.BG_DARK)
            sell_canvas.configure(yscrollcommand=sell_scroll.set)
            sell_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=6)
            sell_scroll.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 10), pady=6)
            sell_frame = tk.Frame(sell_canvas, bg=Theme.BG_DARK)
            sell_canvas.create_window((0, 0), window=sell_frame, anchor=tk.NW,
                                      tags="sell_inner")
            sell_frame.bind("<Configure>",
                            lambda e: sell_canvas.configure(
                                scrollregion=sell_canvas.bbox("all")))
            sell_canvas.bind("<Configure>",
                             lambda e: sell_canvas.itemconfig(
                                 "sell_inner", width=e.width))
            def _mw(event):
                sell_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            sell_canvas.bind("<Enter>", lambda e: sell_canvas.bind("<MouseWheel>", _mw))
            sell_canvas.bind("<Leave>", lambda e: sell_canvas.unbind("<MouseWheel>"))
        else:
            sell_frame = tk.Frame(sd, bg=Theme.BG_DARK)
            sell_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)

        for i, (item, unit_price) in enumerate(sellable):
            count = item.get("count", 1)
            total_price = unit_price * count
            count_str = f" (x{count})" if count > 1 else ""
            stat = _item_stat_line(item)

            row = tk.Frame(sell_frame, bg=Theme.BG_CARD,
                           highlightthickness=1, highlightbackground=Theme.BORDER)
            row.pack(fill=tk.X, pady=1, padx=2)

            # Item name + stat on top row
            name_text = f"{item['name']}{count_str}  {stat}"
            tk.Label(
                row, text=name_text, bg=Theme.BG_CARD, fg=Theme.TEXT,
                font=Theme.FONT_SMALL, wraplength=dw2 - 50, anchor=tk.W,
            ).pack(fill=tk.X, padx=10, pady=(4, 0))

            # Price + Sell button on bottom row
            bottom = tk.Frame(row, bg=Theme.BG_CARD)
            bottom.pack(fill=tk.X, padx=10, pady=(2, 4))

            tk.Label(
                bottom, text=f"{total_price}g",
                bg=Theme.BG_CARD, fg=Theme.BUFF_NEUTRAL, font=Theme.FONT_BOLD,
            ).pack(side=tk.LEFT)

            tk.Button(
                bottom, text="Sell", bg=Theme.BUFF_NEGATIVE, fg="#ffffff",
                font=Theme.FONT_SMALL, activebackground="#c0392b",
                activeforeground="#ffffff", relief=tk.FLAT, padx=12, pady=2,
                cursor="hand2",
                command=lambda idx=i: _do_sell_item(idx),
            ).pack(side=tk.RIGHT)

        # ── Bottom button ───────────────────────────────────────────────
        btn_row = tk.Frame(sd, bg=Theme.BG_DARK)
        btn_row.pack(fill=tk.X, padx=20, pady=(8, 12))

        done_btn = tk.Button(
            btn_row, text="Done Selling",
            bg=Theme.BG_MID, fg=Theme.TEXT, font=Theme.FONT,
            activebackground="#3a3a5a", activeforeground=Theme.TEXT,
            relief=tk.FLAT, padx=12, pady=4, cursor="hand2",
            command=_close_sell,
        )
        done_btn.pack(side=tk.RIGHT)

        sd.bind("<Escape>", lambda e: _close_sell())
        sd.protocol("WM_DELETE_WINDOW", _close_sell)

        # ── NOW center, map, grab, and focus ────────────────────────────
        sd.update_idletasks()
        try:
            px2 = parent.winfo_x()
            py2 = parent.winfo_y()
            pw2 = parent.winfo_width()
            ph2 = parent.winfo_height()
            sd.geometry(f"{dw2}x{dh2}+{px2 + (pw2 - dw2) // 2}+{py2 + (ph2 - dh2) // 2}")
        except Exception:
            pass

        sd.update()
        sd.grab_set()
        done_btn.focus_set()

    def _handle_discovery_gui(self, event):
        """Show a discovery popup with gold or item found."""
        player = self.player
        seg = event["seg"]
        travel_type = seg.get("type", "land")
        find_gold = random.random() < 0.55

        if travel_type == "sea":
            if find_gold:
                gold = random.randint(20, 80)
                gold = int(gold * get_daily_bonus_multiplier(self.player, "gold_bonus"))
                player["gold"] = player.get("gold", 0) + gold
                msg = f"A barnacled crate bobs alongside.\nInside: {gold} gold in waxed pouches!"
                self._log(f"+{gold} gold found at sea!", "green")
            else:
                rarity = _discovery_rarity(player)
                item = build_item(_random_item_id(), rarity)
                added = add_item_to_inventory(player, item.copy())
                msg = f"A waterlogged satchel surfaces from the deep.\nYou haul it aboard.\n\n"
                msg += f"Found: {item['name']}  {_item_stat_line(item)}"
                if added:
                    self._log(f"Found: {item['name']} {_item_stat_line(item)}", "green")
                else:
                    msg += "\n\n(Bag full — item dropped!)"
                    self._log(f"Found: {item['name']} (bag full — dropped!)", "red")
        else:
            if find_gold:
                gold = random.randint(10, 50)
                gold = int(gold * get_daily_bonus_multiplier(self.player, "gold_bonus"))
                player["gold"] = player.get("gold", 0) + gold
                msg = f"A traveler's purse lies abandoned at the roadside.\nYou pocket {gold} gold."
                self._log(f"+{gold} gold found on the road!", "green")
            else:
                rarity = _discovery_rarity(player)
                item = build_item(_random_item_id(), rarity)
                added = add_item_to_inventory(player, item.copy())
                msg = f"A hollow tree stump — something's wedged inside.\n\n"
                msg += f"Found: {item['name']}  {_item_stat_line(item)}"
                if added:
                    self._log(f"Found: {item['name']} {_item_stat_line(item)}", "green")
                else:
                    msg += "\n\n(Bag full — item dropped!)"
                    self._log(f"Found: {item['name']} (bag full — dropped!)", "red")

        # Show popup then resume
        self._show_event_popup("Discovery!", msg)

    def _handle_hazard_gui(self, event):
        """Show hazard popup with flavor text and damage."""
        seg = event["seg"]
        travel_type = seg.get("type", "land")
        difficulty_mult = get_difficulty_multiplier_from_time(self.player)
        max_hp = player_max_hp(self.player)
        damage = max(5, int(max_hp * 0.08 * difficulty_mult))

        if travel_type == "sea":
            desc = random.choice([
                "Rogue waves crash over the deck — rigging snaps and splinters fly!",
                "A hidden reef grinds the hull. The impact sends you sprawling hard.",
                "A waterspout erupts fifty yards off the bow. You cling to the mast.",
                "Poisonous jellyfish swarm the hull. Tentacles whip across the railing.",
            ])
        else:
            desc = random.choice([
                "The trail crumbles into a ravine edge. You slip and tumble down the slope.",
                "A concealed spike trap snaps shut — the spikes nick through your boot.",
                "Hailstones the size of coins hammer the exposed road. No shelter in sight.",
                "Thorned briar walls the overgrown path. You push through, paying in blood.",
                "Loose shale shifts underfoot on the mountain pass. The fall is brutal.",
            ])

        self.player["current_hp"] = max(1, self.player.get("current_hp", 1) - damage)
        self._log(f"\u26a1 {desc}", "red")
        self._log(f"  -{damage} HP  (HP: {self.player['current_hp']}/{max_hp})", "red")

        if self.player["current_hp"] <= max_hp * 0.25:
            self._log("  \u26a0 Critically wounded!", "red")

        self._show_event_popup("Hazard!", f"{desc}\n\nYou take {damage} damage.\n"
                                f"HP: {self.player['current_hp']}/{max_hp}")

    def _handle_storm_gui(self, event):
        """Show storm popup with flavor text and effects (delays are flavor only, §8)."""
        difficulty_mult = get_difficulty_multiplier_from_time(self.player)
        max_hp = player_max_hp(self.player)

        if random.random() < 0.58 * difficulty_mult:
            damage = max(6, int(max_hp * 0.15 * difficulty_mult))
            self.player["current_hp"] = max(1, self.player.get("current_hp", 1) - damage)
            msg = (f"A black wall of clouds swallows the horizon — "
                   f"the storm hits fast.\n\n"
                   f"Mountainous waves batter the hull for what feels like hours.\n"
                   f"You take {damage} damage.\n"
                   f"HP: {self.player['current_hp']}/{max_hp}")
            self._log("\U0001f32a Storm! Mountainous waves batter the hull.", "red")
            self._log(f"  -{damage} HP", "red")
        else:
            msg = (f"A black wall of clouds swallows the horizon.\n\n"
                   f"You reef the sails and ride out the squall.\n"
                   f"Unharmed.")
            self._log("\U0001f32a Storm — unharmed.", "cyan")

        self._show_event_popup("Storm!", msg)

    def _handle_calm_gui(self, event):
        """Show calm seas popup with HP recovery."""
        regen = random.randint(5, 15)
        max_hp = player_max_hp(self.player)
        self.player["current_hp"] = min(
            self.player.get("current_hp", max_hp) + regen, max_hp
        )
        msg = (f"The sea lies flat as polished obsidian.\n"
               f"The crew rests.\n\n"
               f"You recover {regen} HP.\n"
               f"HP: {self.player['current_hp']}/{max_hp}")
        self._log(f"\u2600 Calm waters — recover {regen} HP.", "green")

        self._show_event_popup("Calm Seas", msg)

    def _show_event_popup(self, title, message):
        """Show a brief event popup that resumes travel when dismissed."""
        try:
            parent = self.winfo_toplevel()
        except tk.TclError:
            parent = self

        lines = message.split("\n")
        max_line = max((len(l) for l in lines), default=30)
        est_w = max(280, min(500, max_line * 7 + 60))
        line_h = 18
        msg_h = max(len(lines), 1) * line_h + 30
        dw = max(340, int(est_w))
        dh = 90 + msg_h

        popup = tk.Toplevel(parent)
        popup.title(title)
        popup.transient(parent)
        popup.resizable(False, False)
        popup.configure(bg=Theme.BG_DARK)

        tk.Label(
            popup, text=message,
            bg=Theme.BG_DARK, fg=Theme.TEXT, font=Theme.FONT,
            wraplength=dw - 40, justify=tk.CENTER,
        ).pack(padx=20, pady=(16, 10), fill=tk.BOTH, expand=True)

        def _close():
            try:
                popup.grab_release()
                popup.destroy()
            except tk.TclError:
                pass
            self._resume_anim()

        cont_btn = tk.Button(
            popup, text="Continue",
            bg=Theme.ACCENT, fg="#ffffff", font=Theme.FONT_BOLD,
            activebackground="#45a049", activeforeground="#ffffff",
            relief=tk.FLAT, padx=20, pady=6, cursor="hand2",
            command=_close,
        )
        cont_btn.pack(pady=(0, 16))

        popup.bind("<Return>", lambda e: _close())
        popup.bind("<Escape>", lambda e: _close())
        popup.bind("<space>", lambda e: _close())
        popup.protocol("WM_DELETE_WINDOW", _close)

        # ── NOW center, map, grab, and focus ────────────────────────────
        popup.update_idletasks()
        try:
            px = parent.winfo_x()
            py = parent.winfo_y()
            pw = parent.winfo_width()
            ph = parent.winfo_height()
            popup.geometry(f"{dw}x{dh}+{px + (pw - dw) // 2}+{py + (ph - dh) // 2}")
        except Exception:
            pass

        popup.wait_visibility()
        popup.grab_set()
        cont_btn.focus_set()

    # ── Combat overlay ──────────────────────────────────────────────────

    def _launch_combat(self, seg):
        from facilities.travel_events import _pick_travel_enemy

        travel_type = seg["type"]  # "land" or "sea"
        region = seg.get("biome", None) if travel_type == "land" else None
        num = random.randint(1, min(3, max(1, self.player.get("floor", 1) // 2 + 1)))
        enemy_keys = [k for k in
                      (_pick_travel_enemy(self.player, travel_type, region) for _ in range(num))
                      if k]

        if not enemy_keys:
            self._log("A shadow crosses the road... and vanishes. Nothing to fight.", "dim")
            self._resume_anim()
            return

        # Cancel any stale combat result polling from a previous combat
        if self._travel_check_job:
            self.after_cancel(self._travel_check_job)
            self._travel_check_job = None

        result_queue = _queue.Queue()
        sm = self.sm
        player = self.player

        def _on_overlay_dismissed():
            """Called when the combat overlay is dismissed.
            Process any deferred level-ups and resume travel."""
            if not self.winfo_exists():
                return
            result = self._travel_combat_result
            self._travel_combat_result = None
            if result == "dead":
                self._finish_travel(dead=True)
            elif result == "victory":
                # Process level-ups now that the overlay is gone
                from leveling import gain_exp
                gain_exp(player, 0)
                self._resume_anim()
            elif result == "fled":
                self._resume_anim()
            # If None, the overlay was dismissed before combat finished
            # (shouldn't happen, but be safe)

        def _show():
            from gui.screens.combat_screen import CombatScreen
            sm.push_overlay(CombatScreen,
                            on_dismiss=_on_overlay_dismissed,
                            enemy_keys=enemy_keys,
                            combat_context="travel",
                            on_result=lambda r: result_queue.put(r),
                            is_overlay=True)

        sm.root.after(0, _show)

        def _check():
            if not self.winfo_exists():
                return
            try:
                r = result_queue.get_nowait()
            except _queue.Empty:
                self._travel_check_job = self.after(200, _check)
                return
            self._travel_check_job = None
            if r == "dead" or player.get("current_hp", 1) <= 0:
                self._travel_player_dead = True
                self._log("You have fallen in battle...", "red")
                self._travel_combat_result = "dead"
            elif r == "victory":
                # ── Post-combat rewards (mirrors travel_events._handle_combat) ──
                from resources.enemies import ENEMIES
                from resources.items import build_item
                from facilities.travel_events import _combat_drop_rarity, _random_item_id, _add_to_inv

                total_xp = sum(ENEMIES[k]["level"] * 10 for k in enemy_keys)
                total_gold = sum(ENEMIES[k]["level"] * 5 + random.randint(3, 12)
                                 for k in enemy_keys)
                player["gold"] = player.get("gold", 0) + total_gold
                # Add XP now but defer level-up processing until the overlay
                # is dismissed (avoids freezing the GUI with input()).
                from combat.stat_milestones import get_learning_bonus
                bonus = get_learning_bonus(player)
                player["exp"] = player.get("exp", 0) + int(total_xp * bonus)
                self._log(f"+{total_gold} gold  |  +{total_xp} XP", "gold")

                for key in enemy_keys:
                    if random.random() < 0.40:
                        enemy_level = ENEMIES[key]["level"]
                        rarity = _combat_drop_rarity(enemy_level)
                        item_id = _random_item_id()
                        item = build_item(item_id, rarity)
                        if not _add_to_inv(player, item.copy()):
                            self._log(f"Found: {item['name']} (bag full — dropped!)", "dim")
                        else:
                            self._log(f"Found: {item['name']}", "green")

                from combat.weapon.wedding_specials import apply_wedding_combat_end
                apply_wedding_combat_end(player, victory=True)

                self._log("Enemies defeated!", "green")
                self._travel_combat_result = "victory"
            else:
                # "fled" or "error" — treat as fled
                self._log("You escaped the encounter.", "dim")
                self._travel_combat_result = "fled"

            # If the overlay was already dismissed (race condition),
            # handle the result immediately.
            if sm._overlay_screen is None:
                _on_overlay_dismissed()

        self._travel_check_job = self.after(300, _check)

    def _resume_anim(self):
        self._travel_paused = False
        self._update_top_bar()  # restore header after combat/event overlay
        if self.player and self.player.get("current_hp", 1) <= 0:
            self._travel_player_dead = True
            self._finish_travel(dead=True)
            return
        self._do_anim_step()

    # ── Arrival / finish ─────────────────────────────────────────────────

    def _on_arrival(self):
        dest_id = self._travel_path[-1] if self._travel_path else self.city_id
        if self._travel_wild is not None and str(dest_id).startswith("wild:"):
            self._arrive_at_wild_dungeon()
            return
        if self._travel_horizon is not None and dest_id == "horizon":
            self._arrive_at_horizon()
            return
        dest_name = CITIES.get(dest_id, {}).get("name", dest_id)
        self._log("\u2500" * 28, "dim")
        self._log(f"\u2714 Arrived at {dest_name}!", Theme.ACCENT)
        self.player["location"] = dest_id
        self._finish_travel()

    def _arrive_at_wild_dungeon(self):
        """Set up wild dungeon entry and launch the dungeon screen."""
        dungeon = self._travel_wild
        player = self.player
        day = player.get("day", 1)

        # Expiry grace: if it crumbled mid-journey, deliver to the nearest city
        if int(dungeon.get("expire_day", day) or day) < day:
            nearest = dungeon.get("nearest_city", "solmere")
            nearest_name = CITIES.get(nearest, {}).get("name", nearest)
            self._log("\u2500" * 28, "dim")
            self._log("The ruin has crumbled to dust during your journey...", "red")
            self._log(f"You make instead for {nearest_name}.", Theme.ACCENT)
            player["location"] = nearest
            self._finish_travel()
            return

        player["wild_dungeon_id"] = dungeon["id"]
        # Flee / death / timeout exits all route to origin_city — point it at
        # the nearest city so wild dungeon failures send the player there.
        player["origin_city"] = dungeon.get("nearest_city", "solmere")
        player["dungeon_region"] = dungeon.get("biome", "temperate")
        player["location"] = "dungeon"

        self._log("\u2500" * 28, "dim")
        arrive_icon = _WILD_BIOME_ICONS.get(dungeon.get("biome"),
                                            _WILD_FALLBACK_ICON)
        self._log(f"{arrive_icon} You arrive at {dungeon.get('name', 'the ruin')} "
                  f"(Lv {dungeon.get('level', '?')}).", Theme.ACCENT)
        self._finish_travel(wild_arrival=True)

    def _stop_travel_visuals(self):
        """Cancel travel animation jobs/reset travel mode (no navigation)."""
        if self._travel_anim_job:
            self.after_cancel(self._travel_anim_job)
            self._travel_anim_job = None
        if self._travel_check_job:
            self.after_cancel(self._travel_check_job)
            self._travel_check_job = None
        if self._travel_dot:
            self._canvas.delete(self._travel_dot)
            self._travel_dot = None
        self._mode = self.MODE_BROWSE
        self._travel_segments = []
        self._travel_paused = False

    def _finish_travel(self, dead=False, wild_arrival=False):
        self._stop_travel_visuals()
        self._travel_wild = None
        self._travel_horizon = None

        if dead:
            self._handle_death()
        elif wild_arrival:
            from gui.screens.dungeon_screen import DungeonScreen
            self.sm.switch_to(DungeonScreen, on_result=self._on_wild_result,
                              push_history=False)
        else:
            from gui.screens.city_screen import CityScreen
            self.sm.switch_to(CityScreen, push_history=False)

    def _on_wild_result(self, result):
        """Called when a wild dungeon run ends (DungeonScreen on_result)."""
        if result == "dead":
            # Same death flow as dungeon deaths; the penalty sends the
            # player to origin_city (the ruin's nearest city).
            self._handle_death(death_type="dungeon",
                               floor=self.player.get("floor", "?"))
            return
        if result == "wild_complete":
            self._show_wild_completion()
            return
        if result == "save_exit":
            self.sm.log("Game saved. Exiting to menu.")
            self.sm.player = None
            from gui.screens.main_menu_screen import MainMenuScreen
            self.sm.switch_to(MainMenuScreen)
            return

        # "fled" / "timeout" / None — button-flees kill the dungeon thread
        # before its in-dungeon cleanup can run, so scrub run state here
        # too (idempotent when the in-dungeon exit already cleaned up).
        self.player.pop("wild_dungeon_id", None)
        prev_floor = self.player.pop("_wild_prev_floor", None)
        if prev_floor is not None:
            self.player["floor"] = prev_floor
        for key in ("saved_wild_floor", "saved_wild_rooms", "saved_wild_room_index"):
            self.player.pop(key, None)
        self.player.pop("pandemonium_mode", None)
        self.player["cutlass_high_tide_stacks"] = 0
        self.player.pop("cutlass_high_tide_floor", None)
        if self.player.get("location") == "dungeon":
            self.player["location"] = self.player.get("origin_city", "solmere")
        from gui.screens.city_screen import CityScreen
        self.sm.switch_to(CityScreen, push_history=False)

    def _show_wild_completion(self):
        """Reward summary for a conquered ruin, then return to the city."""
        info = self.player.pop("_wild_completion", None) or {}
        name = info.get("name", "Wild Dungeon")
        lines = [
            f"You have conquered {name}!",
            "",
            f"Floors cleared: {info.get('floors', '?')}  |  "
            f"Level: {info.get('level', '?')}",
            f"Spoils: +{info.get('gold', 0)} gold  |  +{info.get('exp', 0)} XP",
        ]
        items = info.get("items", [])
        if items:
            lines.append("")
            lines.append("Recovered from the hoard:")
            for it in items:
                lines.append(f"  \u2022 {it.get('name', '?')} "
                             f"[{str(it.get('rarity', '')).upper()}]")

        from gui.widgets.confirm_dialog import ok_dialog
        ok_dialog(self, f"\u2605 {name} Conquered", "\n".join(lines))

        from gui.screens.city_screen import CityScreen
        self.sm.switch_to(CityScreen, push_history=False)

    # ── Navigation ──────────────────────────────────────────────────────

    def _go_back(self):
        if self._mode == self.MODE_TRAVEL:
            return
        from gui.screens.city_screen import CityScreen
        self.sm.switch_to(CityScreen, push_history=False)

    def _handle_death(self, death_type="travel", floor=None):
        from gui.screens.death_screen import DeathScreen

        def _cont():
            from utils import apply_death_penalty
            apply_death_penalty(self.player)
            from gui.screens.city_screen import CityScreen
            self.sm.switch_to(CityScreen, push_history=False)

        def _quit():
            self.sm.player = None
            from gui.screens.main_menu_screen import MainMenuScreen
            self.sm.switch_to(MainMenuScreen)

        city_id = self.city_id
        if floor is None:
            floor = self.player.get("city_floors", {}).get(city_id, {}).get("floor", "?")
        self.sm.switch_to(
            DeathScreen,
            floor=floor,
            city_id=city_id, death_type=death_type, on_continue=_cont, on_quit=_quit,
        )

    def _show_legend(self):
        legend = (
            "MAP LEGEND\n\n"
            "Colored nodes = Cities (by biome)\n"
            "\u2605  = Your current location\n"
            "\u2693  = Port city (sea travel)\n"
            "\u2620  = Wild dungeon (glyph shows its biome)\n"
            "\u2014\u2014 Solid line = Land route\n"
            "- - Dashed line = Sea route\n\n"
            "Click a city or wild dungeon to view details.\n"
            "Click 'Travel Here' to journey there.\n"
            "Drag the map to pan around.\n"
            "Press Esc to deselect / go back."
        )
        from gui.widgets.confirm_dialog import ok_dialog
        ok_dialog(self, "Map Legend", legend)

    def destroy(self):
        if self._travel_anim_job:
            self.after_cancel(self._travel_anim_job)
        if self._travel_check_job:
            self.after_cancel(self._travel_check_job)
        super().destroy()
