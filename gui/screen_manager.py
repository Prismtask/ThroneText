"""
gui/screen_manager.py — Handles screen transitions, back-stack, and shared game state.

Screen Manager Pattern:
- Every major game state gets its own screen class
- Screens are swapped in-place inside the main window's content area
- A back-stack enables "Back" navigation where appropriate
"""

import tkinter as tk

from gui.theme import Theme

# ── Real-time game clock ──────────────────────────────────────────────────
# Game time advances at 1 in-game minute per TICK_INTERVAL_MS real milliseconds.
TICK_INTERVAL_MS = 2000   # 2 seconds real time = 1 game minute

# Screen class names where the game clock should tick.
# Overlays (combat, inventory, facilities) are excluded — the clock pauses
# when an overlay is pushed.
_GAME_SCREENS = {
    "CityScreen",
    "DungeonScreen",
    "WorldMapScreen",
    "PostFloorScreen",
    "FacilityScreen",
}


class ScreenManager:
    """Manages the current screen and transitions between game states."""

    def __init__(self, root_window: tk.Tk, player: dict = None, settings: dict = None):
        self.root = root_window
        self.player = player  # Shared game state (mutated in-place by screens)
        self.settings = settings or {}  # GUI settings dict
        self.current_screen = None
        self._screen_history = []  # Simple back-stack
        self._log_entries = []  # Persistent session log: list of (category, message)
        self._log_window = None  # Reference to open LogWindow
        self._overlay_screen = None  # Temporary overlay (not destroyed on pop)
        self._overlay_on_close = None  # Callback to call when overlay is dismissed

        # Real-time game clock
        self._clock_id = None          # tk after() ID for the game tick
        self._clock_paused = False     # True when an overlay is active

        # ── Main layout frames ───────────────────────────────────────────────
        # Top bar (always visible — status info)
        self.top_bar = tk.Frame(
            self.root,
            height=40,
            bg=Theme.BG_MID,
            highlightthickness=1,
            highlightbackground=Theme.BORDER,
        )
        self.top_bar.pack(side=tk.TOP, fill=tk.X)
        self.top_bar.pack_propagate(False)

        # Structured top bar widgets
        self.top_name = tk.Label(
            self.top_bar,
            text="Pandemonium",
            font=Theme.FONT_BOLD,
            bg=Theme.BG_MID,
            fg=Theme.TEXT_HEADER,
        )
        self.top_name.pack(side=tk.LEFT, padx=(10, 4), pady=5)

        self.top_info = tk.Label(
            self.top_bar,
            text="",
            font=Theme.FONT,
            bg=Theme.BG_MID,
            fg=Theme.TEXT_HEADER,
        )
        self.top_info.pack(side=tk.LEFT, padx=4, pady=5)

        # Session log button (top-right — opens the log popup)
        self._log_btn = tk.Button(
            self.top_bar,
            text="📜",
            bg=Theme.BG_MID,
            fg=Theme.TEXT_DIM,
            font=(Theme.FONT_FAMILY, 10),
            relief=tk.FLAT,
            cursor="hand2",
            activebackground=Theme.BG_MID,
            command=self._open_log_window,
        )
        self._log_btn.pack(side=tk.RIGHT, padx=(0, 12), pady=4)

        # Gold is now displayed in the hero card — top bar gold widget hidden
        self.top_gold = tk.Label(
            self.top_bar,
            text="",
            font=Theme.FONT,
            bg=Theme.BG_MID,
            fg=Theme.BUFF_NEUTRAL,
        )
        # self.top_gold.pack(side=tk.RIGHT, padx=(4, 10), pady=5)  # hidden: gold shown in hero card

        # Content area (screens render here)
        self.content_frame = tk.Frame(self.root, bg=Theme.BG_DARK)
        self.content_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Toast container (overlay on root)
        self._toast_container = tk.Frame(self.root, bg="")
        self._toast_container.place(relx=1.0, y=50, anchor=tk.NE, x=-10)

    # ── Navigation ────────────────────────────────────────────────────────────

    def switch_to(self, screen_class, push_history=True, **kwargs):
        """
        Replace the current screen with a new one.

        Args:
            screen_class: A subclass of BaseScreen.
            push_history: If True, the current screen class is pushed to back-stack.
            **kwargs: Extra arguments forwarded to the screen constructor.
        """
        # If there's an overlay active, dismiss it first instead of destroying
        # the underlying screen (which may still have a running facility thread).
        if self._overlay_screen is not None:
            self._dismiss_overlay()

        if self.current_screen is not None:
            if push_history:
                self._screen_history.append(type(self.current_screen))
            self.current_screen.destroy()
            self.current_screen = None

        self.current_screen = screen_class(
            parent=self.content_frame,
            screen_manager=self,
            **kwargs,
        )
        self.current_screen.pack(fill=tk.BOTH, expand=True)
        # Auto-focus new screen for keyboard input
        self.current_screen.focus_set()

        # ── Auto-manage game clock ───────────────────────────────────────
        screen_name = screen_class.__name__
        if screen_name in _GAME_SCREENS and self.player is not None:
            self.start_game_clock()
        else:
            self.stop_game_clock()

    def push_overlay(self, screen_class, on_dismiss=None, **kwargs):
        """
        Show a screen as a temporary overlay on top of the current screen.

        The current screen is hidden (pack_forget) but NOT destroyed, so any
        background threads or I/O redirects remain active. When the overlay
        is dismissed, the underlying screen is restored.

        Args:
            screen_class: A subclass of BaseScreen.
            on_dismiss: Optional callback() when overlay is dismissed.
            **kwargs: Extra arguments forwarded to the screen constructor.
                      (on_dismiss is NOT forwarded — it is consumed here.)
        """
        if self._overlay_screen is not None:
            # Dismiss any existing overlay first
            self._dismiss_overlay()

        self._overlay_on_close = on_dismiss

        # ── Pause game clock while overlay is active ────────────────────
        self._clock_paused = True

        # Hide (don't destroy) the current screen
        if self.current_screen is not None:
            self.current_screen.pack_forget()

        self._overlay_screen = screen_class(
            parent=self.content_frame,
            screen_manager=self,
            **kwargs,
        )
        self._overlay_screen.pack(fill=tk.BOTH, expand=True)
        self._overlay_screen.focus_set()

    def dismiss_overlay(self):
        """
        Dismiss the current overlay and restore the underlying screen.

        Called by the overlay screen when it's done (e.g. combat finished).
        """
        self._dismiss_overlay()

    def _dismiss_overlay(self):
        """Internal: destroy overlay and restore underlying screen."""
        if self._overlay_screen is None:
            return

        try:
            self._overlay_screen.destroy()
        except (tk.TclError, AttributeError):
            pass
        self._overlay_screen = None

        # ── Resume game clock after overlay is dismissed ────────────────
        self._clock_paused = False
        self._schedule_tick()  # Restart the clock tick (was stopped by pause)

        # Restore the underlying screen
        if self.current_screen is not None:
            try:
                self.current_screen.pack(fill=tk.BOTH, expand=True)
                self.current_screen.focus_set()
            except (tk.TclError, AttributeError):
                pass

        # Notify
        cb = self._overlay_on_close
        self._overlay_on_close = None
        if cb:
            cb()

    def go_back(self):
        """Pop the previous screen from history and switch to it."""
        if not self._screen_history:
            return
        prev_class = self._screen_history.pop()
        # Switch without pushing current onto history (we're going back)
        if self.current_screen is not None:
            self.current_screen.destroy()
            self.current_screen = None
        self.current_screen = prev_class(
            parent=self.content_frame,
            screen_manager=self,
        )
        self.current_screen.pack(fill=tk.BOTH, expand=True)
        self.current_screen.focus_set()

        # ── Auto-manage game clock for back-navigation ──────────────────
        screen_name = prev_class.__name__
        if screen_name in _GAME_SCREENS and self.player is not None:
            self.start_game_clock()
        else:
            self.stop_game_clock()

    def clear_history(self):
        """Clear the back-stack (useful on major state changes, e.g. new game)."""
        self._screen_history.clear()

    # ── Real-time game clock ─────────────────────────────────────────────────

    def start_game_clock(self):
        """Begin ticking game time forward every TICK_INTERVAL_MS milliseconds.

        Safe to call repeatedly — if the clock is already running this is a no-op.
        """
        if self._clock_id is not None:
            return  # Already ticking
        self._clock_paused = False
        self._schedule_tick()

    def stop_game_clock(self):
        """Stop the game clock. Safe to call even if not running."""
        if self._clock_id is not None:
            self.root.after_cancel(self._clock_id)
            self._clock_id = None
        self._clock_paused = False

    def _schedule_tick(self):
        """Schedule the next game tick via tk.after()."""
        if self._clock_id is not None:
            return  # Already scheduled
        interval = TICK_INTERVAL_MS
        screen = self.current_screen
        if screen is not None:
            interval = getattr(screen, 'tick_interval_ms', TICK_INTERVAL_MS)
        self._clock_id = self.root.after(interval, self._game_tick)

    def _game_tick(self):
        """Advance game time by 1 minute and refresh the current screen's display."""
        self._clock_id = None  # Clear the ID — tick has fired

        # Don't tick if paused, no player, or root is destroyed
        if self._clock_paused:
            return
        if self.player is None:
            return
        try:
            if not self.root.winfo_exists():
                return
        except (tk.TclError, RuntimeError):
            return

        # Advance time
        from utils import advance_time
        advance_time(self.player, 1)

        # Refresh the current screen's time display.
        # Prefer the screen's own _update_top_bar() so per-screen formatting
        # (e.g. CityScreen shows Floor + date) is preserved.
        screen = self.current_screen
        if screen is not None and hasattr(screen, '_update_top_bar'):
            try:
                screen._update_top_bar()
            except Exception:
                self.refresh_top_bar(self.player)
        else:
            self.refresh_top_bar(self.player)

        # Schedule the next tick.
        # Screens can override tick_interval_ms for faster/slower rates
        # (e.g. travel journeys tick faster to show time passing).
        interval = TICK_INTERVAL_MS
        if screen is not None:
            interval = getattr(screen, 'tick_interval_ms', TICK_INTERVAL_MS)
        self._clock_id = self.root.after(interval, self._game_tick)

    # ── Top-bar updates ───────────────────────────────────────────────────────

    def update_top_bar(self, text: str):
        """Update the persistent top status bar (legacy simple string)."""
        self.top_name.config(text=text)
        self.top_info.config(text="")

    def refresh_top_bar(self, player=None):
        """Update structured top bar from player dict."""
        p = player or self.player
        if not p:
            self.top_name.config(text="Pandemonium")
            self.top_info.config(text="")
            self.top_gold.config(text="")
            return

        name = p.get("name", "Unknown")
        level = p.get("level", 1)
        city = p.get("location", "solmere").replace("_", " ").title()
        if city == "Dungeon":
            city = p.get("origin_city", "solmere").replace("_", " ").title()

        from utils import format_time
        from events import format_date
        time_str = format_time(p)
        date_str = format_date(p)

        self.top_name.config(text=f"{name}  Lv.{level}")
        self.top_info.config(text=f"{city}  |  {date_str}  |  {time_str}")

    # ── Log / notifications ───────────────────────────────────────────────────

    def log(self, message: str, category: str = "system"):
        """Record a line in the persistent session log.

        The old always-visible bottom bar was removed. Messages are stored
        in the session history, viewable via the 📜 popup (top-right).
        Important categories (events) auto-open the popup so the player
        never misses them.
        """
        self._log_entries.append((category, message))
        # Trim if needed
        max_lines = self.settings.get("log_max_lines", 1000)
        if len(self._log_entries) > max_lines:
            self._log_entries = self._log_entries[-max_lines:]

        # Auto-open the log popup for important categories
        if category == "event":
            self.root.after(200, self._open_log_window)

    def clear_log(self):
        """Compatibility no-op — the bottom log panel was removed.

        Screens still call this on build; the session history is preserved.
        """
        pass

    def show_toast(self, message: str, category: str = "info", duration_ms: int = 3000):
        """Show a slide-in toast notification."""
        from gui.widgets.notification_toast import NotificationToast
        toast = NotificationToast(self._toast_container, message, category, duration_ms)
        toast.pack(anchor=tk.NE, pady=2)

    def _open_log_window(self):
        """Open the persistent log history popup."""
        from gui.widgets.log_window import LogWindow
        if self._log_window is not None and self._log_window.winfo_exists():
            self._log_window.lift()
            return
        self._log_window = LogWindow(
            self.root,
            self._log_entries,
            on_close=lambda: setattr(self, "_log_window", None),
        )


# ── Note: The ScreenManager class is defined at the top of this file. ──
# This module intentionally has no second ScreenManager definition.
