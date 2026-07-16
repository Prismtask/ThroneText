"""
gui/widgets/city_map.py — Clickable ASCII city map widget.

A reusable tk.Text-based widget that renders an ASCII city map and makes
service/dungeon regions clickable using tag bindings.
"""

import tkinter as tk
import tkinter.font as tkfont
from gui.theme import Theme


class CityMapWidget(tk.Text):
    """Renders a city ASCII map with clickable service regions."""

    def __init__(self, parent, city_id, city, positions,
                 on_service_click=None, on_dungeon_click=None, **kwargs):
        self.city_id = city_id
        self.city = city
        self.positions = positions
        self.on_service_click = on_service_click
        self.on_dungeon_click = on_dungeon_click

        # Count map lines from the city's ASCII art
        from resources.city_maps import get_city_map
        map_art = get_city_map(city_id) or ""
        self._map_lines = map_art.count('\n')

        # Use a slightly smaller font for the map to fit more content
        map_font = (Theme.FONT_FAMILY, max(8, Theme.FONT_SIZE - 1))

        super().__init__(
            parent,
            bg=Theme.BG_DARK,
            fg=Theme.TEXT,
            font=map_font,
            wrap=tk.NONE,
            cursor="arrow",
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=0,
            selectbackground=Theme.BG_DARK,
            selectforeground=Theme.TEXT,
            padx=6,
            pady=4,
            height=self._map_lines,
            state=tk.DISABLED,
            takefocus=0,
            **kwargs,
        )

        # Create a centering tag (low priority – created before service tags).
        # lmargin1 shifts the first (and only, since wrap=NONE) display line
        # of every logical line, centering the whole block without touching
        # the raw text or invalidating CITY_SERVICE_POSITIONS indices.
        self.tag_configure("center", lmargin1=0, lmargin2=0)

        # Make read-only but allow programmatic changes
        self.configure(state=tk.NORMAL)
        self._render_map(map_art)
        # Apply the centering tag to every character so lmargin1 takes effect
        self.tag_add("center", "1.0", tk.END)
        self._apply_service_tags()
        self._apply_dungeon_tag()
        self.configure(state=tk.DISABLED)

        # Track hover state for cursor changes
        self._hovered_tag = None

        # Defer centering until the widget has a real width on screen.
        # Also re-center whenever the widget is resized.
        self.bind("<Configure>", self._on_configure)
        self._center_pending = self.after(50, self._center_content)

    def _render_map(self, map_art):
        """Insert the ASCII map string with base styling."""
        self.delete("1.0", tk.END)
        self.insert("1.0", map_art)

    # ── Centering ─────────────────────────────────────────────────────────

    def _on_configure(self, event):
        """Debounced re-center on resize – only act when our own width changes."""
        # Ignore events fired by child widgets or other noise
        if event.widget is not self:
            return
        w = getattr(self, '_last_width', -1)
        if event.width == w:
            return
        self._last_width = event.width
        # Cancel any pending centering and schedule a fresh one
        if self._center_pending:
            self.after_cancel(self._center_pending)
        self._center_pending = self.after(50, self._center_content)

    def _center_content(self, event=None):
        """Measure the longest map line and apply lmargin1 to center the block.

        Uses the same font that the widget was created with so pixel
        measurements are accurate.  If the widget hasn't been mapped yet
        (width <= 1) we bail out – the <Configure> handler will retry.
        """
        self._center_pending = None

        widget_width = self.winfo_width()
        if widget_width <= 1:
            return  # not mapped yet

        try:
            map_font = (Theme.FONT_FAMILY, max(8, Theme.FONT_SIZE - 1))
            measure_font = tkfont.Font(family=map_font[0], size=map_font[1])

            raw = self.get("1.0", tk.END).rstrip('\n')
            lines = raw.split('\n')
            max_px = 0
            for line in lines:
                w = measure_font.measure(line)
                if w > max_px:
                    max_px = w

            # padx is applied symmetrically, so the usable text area is narrower
            padx_val = 6
            usable = widget_width - 2 * padx_val
            left_margin = max(0, (usable - max_px) // 2)

            self.tag_configure("center", lmargin1=left_margin, lmargin2=0)
        except Exception:
            pass  # widget may be in a transitional state

    def _apply_service_tags(self):
        """Create clickable tags for each service position."""
        service_colors = {
            "shop":         "#f1c40f",  # gold
            "inn":          "#3498db",  # blue
            "barracks":     "#e74c3c",  # red
            "blacksmith":   "#e67e22",  # orange
            "arcane_tower": "#9b59b6",  # purple
            "temple":       "#f39c12",  # amber
            "herbalist":    "#2ecc71",  # green
            "guild":        "#1abc9c",  # teal
            "trade_hall":   "#e84393",  # pink
            "gift_shop":    "#fd79a8",  # light pink
            "port":         "#0984e3",  # steel blue
            "shipyard":     "#636e72",  # grey
            "black_market": "#6c5ce7",  # indigo
        }

        for svc_key, (line, start_col, end_col) in self.positions.items():
            if svc_key == "dungeon":
                continue  # Handled separately

            tag_name = f"svc_{svc_key}"
            color = service_colors.get(svc_key, Theme.ACCENT)

            # Tag spans exactly the service name region
            start_idx = f"{line + 1}.{start_col}"
            end_idx = f"{line + 1}.{end_col}"
            self.tag_add(tag_name, start_idx, end_idx)

            # Normal style
            self.tag_configure(
                tag_name,
                foreground=Theme.TEXT,
                background="",
            )

            # Hover style
            hover_tag = f"svc_{svc_key}_hover"
            self.tag_configure(
                hover_tag,
                foreground=color,
                underline=True,
                background="",
            )

            # Bind hover enter/leave
            self.tag_bind(tag_name, "<Enter>",
                          lambda e, t=tag_name, h=hover_tag: self._on_tag_enter(t, h))
            self.tag_bind(tag_name, "<Leave>",
                          lambda e, t=tag_name, h=hover_tag: self._on_tag_leave(t, h))

            # Bind click
            self.tag_bind(tag_name, "<Button-1>",
                          lambda e, s=svc_key: self._on_service_clicked(s))

    def _apply_dungeon_tag(self):
        """Create clickable dungeon tag at the bottom of the map."""
        dungeon_pos = self.positions.get("dungeon")
        if not dungeon_pos:
            return
        line, start_col, end_col = dungeon_pos

        tag_name = "svc_dungeon"
        start_idx = f"{line + 1}.{start_col}"
        end_idx = f"{line + 1}.{end_col}"
        self.tag_add(tag_name, start_idx, end_idx)

        self.tag_configure(
            tag_name,
            foreground=Theme.TEXT_DIM,
            background="",
        )

        hover_tag = "svc_dungeon_hover"
        self.tag_configure(
            hover_tag,
            foreground=Theme.ACCENT,
            underline=True,
            background="",
        )

        self.tag_bind(tag_name, "<Enter>",
                      lambda e: self._on_tag_enter(tag_name, hover_tag))
        self.tag_bind(tag_name, "<Leave>",
                      lambda e: self._on_tag_leave(tag_name, hover_tag))
        self.tag_bind(tag_name, "<Button-1>",
                      lambda e: self._on_dungeon_clicked())

    def _on_tag_enter(self, tag_name, hover_tag):
        """Apply hover style and change cursor."""
        self.configure(cursor="hand2")
        self.tag_add(hover_tag, *self.tag_ranges(tag_name))

    def _on_tag_leave(self, tag_name, hover_tag):
        """Remove hover style."""
        self.configure(cursor="arrow")
        self.tag_delete(hover_tag)

    def _on_service_clicked(self, service_key):
        """Handle click on a service region."""
        if self.on_service_click:
            self.on_service_click(service_key)

    def _on_dungeon_clicked(self):
        """Handle click on the dungeon region."""
        if self.on_dungeon_click:
            self.on_dungeon_click()

    def refresh(self, city_id, city, positions):
        """Re-render the widget for a different city."""
        from resources.city_maps import get_city_map
        map_art = get_city_map(city_id) or ""
        new_lines = map_art.count('\n')

        self.city_id = city_id
        self.city = city
        self.positions = positions

        self.configure(state=tk.NORMAL, height=new_lines)
        self.delete("1.0", tk.END)

        # Remove all old tags
        for tag in list(self.tag_names()):
            self.tag_delete(tag)

        # Re-create the centering tag (must exist before tag_add)
        self.tag_configure("center", lmargin1=0, lmargin2=0)

        self._map_lines = new_lines
        self._render_map(map_art)
        self.tag_add("center", "1.0", tk.END)
        self._apply_service_tags()
        self._apply_dungeon_tag()
        self.configure(state=tk.DISABLED)

        # Re-center for the new map
        if self._center_pending:
            self.after_cancel(self._center_pending)
        self._center_pending = self.after(50, self._center_content)
