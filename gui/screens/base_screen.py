"""
gui/screens/base_screen.py — Abstract base class for all game screens.

Every screen inherits from BaseScreen and implements build_ui().
Screens are tkinter Frames that fill the content area managed by ScreenManager.
"""

import tkinter as tk
from abc import ABC, abstractmethod

from gui.theme import Theme


def city_header_parts(player, city_id=None):
    """Build the two-tier city top bar as ``(primary, secondary)`` text.

    Header space is scarce, so only glanceable, non-redundant info is kept.
    Priority order:
      1. Phase track — time is the resource every action spends.
      2. Day + season — daily limits, events, weather.
      3. Floor x/y — dungeon progression.
      4. Karma — city gate thresholds (hidden when the rule is off).
      5. Watched marker — only while the watch is active.

    Player name, city name and the M#-D# month grid are deliberately omitted:
    the hero card and the big city title on screen already show them.
    """
    if not player:
        return "Pandemonium", ""

    from events import format_date
    from time_blocks import format_block_track

    if not city_id:
        city_id = player.get("location") or "solmere"
        if city_id == "dungeon":
            city_id = player.get("origin_city", "solmere")

    # Primary tier — the clock: phase pips first, then the date (dd/mm).
    track = format_block_track(player, include_day=False)
    date_text = format_date(player)
    primary = f"{track}  ·  {date_text}" if track else date_text

    # Secondary tier — context you check between actions.
    secondary = []
    from resources.cities import CITIES
    city = CITIES.get(city_id) or {}
    if not isinstance(city, dict):
        city = {}
    cf = player.get("city_floors", {}).get(city_id, {})
    start = max(1, int(city.get("dungeon_start_floor", 1) or 1))
    cur = int(cf.get("floor", start) or start)
    deepest = int(cf.get("max_floor", start) or start)
    secondary.append(f"Floor {cur}/{deepest}")

    import karma
    if karma.is_enabled(player):
        tier = karma.get_karma_tier(player)
        value = karma.get_karma(player)
        label = f"Karma {tier['label']} {value:+d}"
        if city_id == "blackwake":
            label += " · respected" if value < 0 else " · saint tax"
        secondary.append(label)

    gate = player.get("karma_gate") or {}
    watched_until = int(gate.get("watched_until", 0) or 0)
    if watched_until and watched_until >= int(player.get("day", 1) or 1):
        secondary.append("👁 Watched")

    return primary, "  ·  ".join(secondary)


class BaseScreen(tk.Frame, ABC):
    """
    Abstract base for all Pandemonium GUI screens.

    Subclasses must implement build_ui() to create their widgets.
    The screen is automatically packed into the ScreenManager's content frame.
    """

    def __init__(self, parent: tk.Widget, screen_manager, **kwargs):
        # Pop custom kwargs before passing to tk.Frame
        self.sm = screen_manager
        self.player = screen_manager.player if screen_manager else None

        super().__init__(
            parent,
            bg=Theme.BG_DARK,
            **kwargs,
        )
        self.build_ui()

    @abstractmethod
    def build_ui(self):
        """Create all widgets for this screen. Must be implemented by subclasses."""
        pass

    # ── Convenience helpers for subclasses ────────────────────────────────────

    def styled_button(self, parent, text, command=None, **extra):
        """Create a consistently-styled Button."""
        defaults = {
            "bg": Theme.BUTTON_BG,
            "fg": Theme.BUTTON_FG,
            "activebackground": Theme.BUTTON_ACTIVE_BG,
            "activeforeground": Theme.BUTTON_ACTIVE_FG,
            "font": Theme.FONT_BOLD,
            "relief": tk.RAISED,
            "borderwidth": 2,
            "cursor": "hand2",
        }
        defaults.update(extra)
        btn = tk.Button(parent, text=text, command=command, **defaults)
        return btn

    def styled_label(self, parent, text, **extra):
        """Create a consistently-styled Label."""
        defaults = {
            "bg": Theme.BG_DARK,
            "fg": Theme.TEXT,
            "font": Theme.FONT,
        }
        defaults.update(extra)
        return tk.Label(parent, text=text, **defaults)

    def styled_frame(self, parent, **extra):
        """Create a consistently-styled Frame."""
        defaults = {"bg": Theme.BG_DARK}
        defaults.update(extra)
        return tk.Frame(parent, **defaults)

    def log(self, message: str):
        """Shorthand to write to the global log panel."""
        if self.sm:
            self.sm.log(message)

    def handle_escape(self):
        """Default: navigate back. Subclasses may override for custom behavior."""
        if self.sm:
            self.sm.go_back()
