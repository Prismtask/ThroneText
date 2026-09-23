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
"""

import tkinter as tk
import queue as _queue
import random

from gui.screens.base_screen import BaseScreen
from gui.theme import Theme
from gui.widgets.confirm_dialog import confirm_dialog

from resources.cities import CITIES
from resources.items import ITEMS, build_item, ITEM_RARITY
from facilities.pathfinding import find_shortest_path
from facilities.travel_events import (
    _random_item_id, _discovery_rarity, _merchant_stock_rarity,
    _merchant_price, _sell_price, _item_stat_line, _charisma_discount,
)
from inventory import add_item_to_inventory, remove_item_by_reference
from combat.stats import get_effective_attribute
from utils import advance_time, get_difficulty_multiplier_from_time
from character import player_max_hp


# ═══════════════════════════════════════════════════════════════════════════
#  CITY LAYOUT
# ═══════════════════════════════════════════════════════════════════════════

_CITY_POSITIONS = {
    "stormhold": (80, 60),
    "thornwall": (230, 80),
    "solmere":    (200, 160),
    "greyharbor": (120, 220),
    "elderfen":   (310, 230),
    "irondeep":   (450, 140),
    "skylume":    (580, 80),
    "cinderpeak": (570, 190),
    "veilholt":   (680, 140),
    "sunreach":   (170, 330),
    "brinewatch": (60, 410),
    "mirefall":   (250, 380),
    "ashkara":    (100, 480),
    "dunemar":    (200, 510),
    "saltmarsh":  (310, 430),
    "tidebreak":    (450, 400),
    "coralhaven":   (600, 380),
    "blackwake":    (520, 500),
    "isle_of_glass": (650, 500),
}

_REGIONS = {
    "North":       ("stormhold", "thornwall"),
    "Central":     ("solmere", "greyharbor", "elderfen"),
    "East":        ("irondeep", "skylume", "cinderpeak", "veilholt"),
    "South":       ("sunreach", "brinewatch", "mirefall", "ashkara",
                    "dunemar", "saltmarsh"),
    "Far Reaches": ("tidebreak", "coralhaven", "blackwake", "isle_of_glass"),
}

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

_NODE_W = 120
_NODE_H = 38
_ANIM_STEPS = 30        # animation frames per segment
_ANIM_INTERVAL = 40     # ms between frames
_EVENT_CHECKPOINTS = 3  # event slots per segment


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
        self._node_rects = {}
        self._canvas = None
        self._info_frame = None
        self._travel_mode = travel_mode  # True = travel mode (pathfinding + highlights + Travel Here)
        self._path_result = None        # cached pathfinding result for travel mode
        self._route_lines = {}           # (a,b) sorted tuple → [canvas line IDs]

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
        self._travel_time_acc = 0.0   # fractional minutes accumulated during animation
        self._travel_combat_result = None  # set by _check, handled on overlay dismiss

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

    @property
    def tick_interval_ms(self):
        """During animation, per-frame stepping handles time advancement.
        The background clock should stay quiet so it doesn't double-tick."""
        if self._travel_segments:
            return 86_400_000  # effectively never (once per day)
        return 2000            # Default: 1 game minute per 2 real seconds

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
        from utils import format_time
        text = (
            f"{self.player['name']} | {city_name} | Floor {_cur}/{_max} | "
            f"{format_date(self.player)} | {format_time(self.player)}"
        )
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

        self._canvas.bind("<Button-1>", self._on_canvas_click)
        self._canvas.bind("<Motion>", self._on_canvas_motion)

        # Bottom bar
        self._bottom_bar = tk.Frame(self, bg=Theme.BG_DARK)
        self._bottom_bar.pack(fill=tk.X, padx=20, pady=(8, 12))

        self._btn_back = self.styled_button(
            self._bottom_bar, text="\u2190 Back to City",
            command=self._go_back, width=18, bg="#5a3a5a",
        )
        self._btn_back.pack(side=tk.LEFT, padx=4)

        self._btn_travel = self.styled_button(
            self._bottom_bar, text="\u25b6 Travel Here",
            command=self._on_travel_here, width=16, bg=Theme.ACCENT,
        )

        self._btn_legend = self.styled_button(
            self._bottom_bar, text="Show Legend",
            command=self._show_legend, width=16,
        )
        self._btn_legend.pack(side=tk.RIGHT, padx=4)

        self.bind("<Escape>", lambda e: self._on_escape())
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
                self._canvas.create_text(
                    mid_x, mid_y - 6, text=f"{raw_time}m",
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

    # ── Canvas events ────────────────────────────────────────────────────

    def _find_city_at(self, ex, ey):
        for city_id, (cx, cy) in _CITY_POSITIONS.items():
            if cx <= ex <= cx + _NODE_W and cy <= ey <= cy + _NODE_H:
                return city_id
        return None

    def _on_canvas_motion(self, event):
        if self._mode == self.MODE_TRAVEL:
            return
        city = self._find_city_at(event.x, event.y)
        self._canvas.config(cursor="hand2" if city else "")

    def _on_canvas_click(self, event):
        if self._mode == self.MODE_TRAVEL:
            return
        city = self._find_city_at(event.x, event.y)
        if city is None:
            return
        if city == self._selected_city:
            self._deselect_city()
        else:
            self._select_city(city)

    def _on_escape(self):
        if self._mode == self.MODE_TRAVEL:
            return
        if self._selected_city is not None:
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

        # In travel mode: compute path, highlight it, show route info + Travel Here
        if self._travel_mode and city_id != self.city_id:
            self._path_result = find_shortest_path(self.player, self.city_id, city_id)
            if self._path_result and self._path_result["segments"]:
                self._highlight_path(self._path_result)
            self._build_travel_info_panel(city_id, self._path_result)
            self._btn_travel.pack(side=tk.LEFT, padx=4, before=self._btn_legend)
        else:
            self._path_result = None
            self._build_city_info_panel(city_id)
            # No Travel Here button in browse mode

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
        self._btn_travel.pack_forget()

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
            text="Click a city on the\nmap to view details.",
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
                tk.Label(inner,
                         text=f"  {icon} {dest_name} — {raw} min ({type_label})",
                         bg=Theme.BG_CARD, fg=Theme.TEXT_DIM,
                         font=Theme.FONT_SMALL).pack(
                    anchor=tk.W, padx=10, pady=(1, 0))

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
            tk.Label(inner, text=f"Total: {path_result['total_time']} min",
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

    # ── Travel initiation ────────────────────────────────────────────────

    def _on_travel_here(self):
        if self._selected_city is None or self._selected_city == self.city_id:
            return

        # Use cached path result if available (travel mode), else compute
        result = self._path_result
        if result is None:
            result = find_shortest_path(self.player, self.city_id, self._selected_city)
        if result is None or not result["segments"]:
            self.sm.log("No route found to that city.")
            return

        gold = self.player.get("gold", 0)
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
            self._start_travel(result)

        confirm_dialog(
            parent=self, title="Embark on Journey",
            message=(
                f"Travel to {dest_name}?\n\n"
                f"Route: {' → '.join(result['path'])}\n"
                f"Total: {result['total_time']} min  |  "
                f"Segments: {len(result['segments'])}\n"
                + (f"Ferry cost: {result['total_cost']}g\n"
                   if result['total_cost'] > 0 else "")
                + "\nKeep your wits about you."
            ),
            on_yes=_do_embark,
            yes_text="Begin Journey",
            no_text="Cancel",
        )

    def _start_travel(self, result):
        """Enter travel mode."""
        self._mode = self.MODE_TRAVEL
        self._travel_segments = result["segments"]
        self._travel_path = result["path"]
        self._travel_seg_idx = 0
        self._travel_paused = False
        self._travel_player_dead = False

        self._btn_travel.pack_forget()
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

        if from_id not in _CITY_POSITIONS or to_id not in _CITY_POSITIONS:
            self._travel_seg_idx += 1
            self._animate_next_segment()
            return

        fx, fy = _CITY_POSITIONS[from_id]
        tx, ty = _CITY_POSITIONS[to_id]
        self._travel_seg_start = (fx + _NODE_W // 2, fy + _NODE_H // 2)
        self._travel_seg_end = (tx + _NODE_W // 2, ty + _NODE_H // 2)

        from_name = CITIES.get(from_id, {}).get("name", from_id)
        to_name = CITIES.get(to_id, {}).get("name", to_id)
        seg_type = seg["type"]
        icon = "\u26f5" if seg_type == "sea" else "\U0001f9b6"
        self._log(f"{icon} {from_name} → {to_name}  "
                  f"({seg['effective_time']} min, {seg_type})", "text")

        self._travel_event_queue = self._roll_events(seg)
        self._travel_event_idx = 0
        self._travel_step = 0
        self._travel_time_acc = 0.0   # reset per-segment accumulator
        self._travel_paused = False
        self._do_anim_step()

    def _do_anim_step(self):
        if self._travel_paused or self._travel_player_dead:
            return

        seg = self._travel_segments[self._travel_seg_idx]
        total = _ANIM_STEPS
        self._travel_step += 1

        # ── Advance time smoothly per frame ─────────────────────────────
        minutes_per_step = seg["effective_time"] / total
        self._travel_time_acc += minutes_per_step
        while self._travel_time_acc >= 1.0:
            advance_time(self.player, 1)
            self._travel_time_acc -= 1.0
        self._update_top_bar()

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

        # Advance any remaining fractional time from this segment
        if self._travel_time_acc >= 0.5:
            advance_time(self.player, 1)

        self.player["location"] = to_id

        to_name = CITIES.get(to_id, {}).get("name", to_id)
        self._log(f"Arrived at {to_name}.", "green")
        self._update_top_bar()  # update city + time in top bar

        self._travel_seg_idx += 1
        if self._travel_seg_idx >= len(self._travel_segments):
            self._on_arrival()
            return

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
        has_ship = self.player.get("has_ship", False)
        cost = next_seg.get("cost", 0)
        eff_time = next_seg["effective_time"]

        if has_ship:
            msg = (f"You've arrived at {port_name}.\n\n"
                   f"Next: \u26f5 Sea voyage to {dest_name}\n"
                   f"({eff_time} min, your ship is ready)\n\n"
                   f"Continue your journey?")
        else:
            msg = (f"You've arrived at {port_name}.\n\n"
                   f"Next: \u26f5 Ferry to {dest_name}\n"
                   f"({eff_time} min, ticket: {cost}g)\n\n"
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
        dw2, dh2 = 460, min(140 + len(inv) * 44, 520)

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
                cur_inv = player.get("inventory", [])
                if idx < 0 or idx >= len(cur_inv):
                    _close_sell()
                    return
                item = cur_inv[idx]
                if is_wedding_item_soulbound(item):
                    self._log(f"[{item['name']}] is soulbound — cannot be sold.", "red")
                    _close_sell()
                    return
                if item.get("unique"):
                    self._log(f"[{item['name']}] is unique — cannot be sold.", "red")
                    _close_sell()
                    return
                unit_price = _sell_price(item, player)
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
        needs_scroll = len(inv) > 6
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

        for i, item in enumerate(inv):
            unit_price = _sell_price(item, player)
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
        """Show storm popup with flavor text and effects."""
        difficulty_mult = get_difficulty_multiplier_from_time(self.player)
        max_hp = player_max_hp(self.player)

        if random.random() < 0.45 * difficulty_mult:
            damage = max(6, int(max_hp * 0.12 * difficulty_mult))
            self.player["current_hp"] = max(1, self.player.get("current_hp", 1) - damage)
            advance_time(self.player, 90)
            msg = (f"A black wall of clouds swallows the horizon — "
                   f"the storm hits fast.\n\n"
                   f"Mountainous waves batter the hull for an hour and a half.\n"
                   f"You take {damage} damage and arrive late.\n"
                   f"HP: {self.player['current_hp']}/{max_hp}")
            self._log("\U0001f32a Storm! Mountainous waves batter the hull.", "red")
            self._log(f"  -{damage} HP, delayed 90 min", "red")
        else:
            advance_time(self.player, 30)
            msg = (f"A black wall of clouds swallows the horizon.\n\n"
                   f"You reef the sails and ride out the squall.\n"
                   f"Unharmed — but delayed 30 minutes.")
            self._log("\U0001f32a Storm — delayed 30 min, unharmed.", "cyan")

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
        dest_name = CITIES.get(dest_id, {}).get("name", dest_id)
        self._log("\u2500" * 28, "dim")
        self._log(f"\u2714 Arrived at {dest_name}!", Theme.ACCENT)
        self.player["location"] = dest_id
        self._finish_travel()

    def _finish_travel(self, dead=False):
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

        if dead:
            self._handle_death()
        else:
            from gui.screens.city_screen import CityScreen
            self.sm.switch_to(CityScreen, push_history=False)

    # ── Navigation ──────────────────────────────────────────────────────

    def _go_back(self):
        if self._mode == self.MODE_TRAVEL:
            return
        from gui.screens.city_screen import CityScreen
        self.sm.switch_to(CityScreen, push_history=False)

    def _handle_death(self):
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
        self.sm.switch_to(
            DeathScreen,
            floor=self.player.get("city_floors", {}).get(city_id, {}).get("floor", "?"),
            city_id=city_id, death_type="travel", on_continue=_cont, on_quit=_quit,
        )

    def _show_legend(self):
        legend = (
            "MAP LEGEND\n\n"
            "Colored nodes = Cities (by biome)\n"
            "\u2605  = Your current location\n"
            "\u2693  = Port city (sea travel)\n"
            "\u2014\u2014 Solid line = Land route\n"
            "- - Dashed line = Sea route\n\n"
            "Click a city to view details.\n"
            "Click 'Travel Here' to journey there.\n"
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
