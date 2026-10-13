"""
gui/screen_manager.py — Handles screen transitions, back-stack, and shared game state.

Screen Manager Pattern:
- Every major game state gets its own screen class
- Screens are swapped in-place inside the main window's content area
- A back-stack enables "Back" navigation where appropriate
"""

import tkinter as tk

from gui.theme import Theme

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

        # Block time (docs/time_system_design.md): no wall clock. The top bar
        # refreshes when time is SPENT, and queued Event Notices surface at
        # the next safe moment.
        from time_blocks import register_time_listener
        register_time_listener(self._on_time_advanced)

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
        # Game notifications must never leak into the main menu (e.g. when
        # the player quits while a quest toast is still showing).
        if screen_class.__name__ == "MainMenuScreen":
            self.clear_toasts()

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

    def get_top_screen(self):
        """Return the screen that should receive input right now.

        An active overlay sits above the current screen and is the only one
        visible, so input dispatch (Escape, global keys) must target it.
        """
        if self._overlay_screen is not None:
            return self._overlay_screen
        return self.current_screen

    def _dismiss_overlay(self):
        """Internal: destroy overlay and restore underlying screen."""
        if self._overlay_screen is None:
            return

        try:
            self._overlay_screen.destroy()
        except (tk.TclError, AttributeError):
            pass
        self._overlay_screen = None

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
        # An active overlay is the topmost layer — back-navigation closes it
        # instead of rebuilding the screen underneath. Without this guard the
        # rebuilt screen stayed stacked below the overlay (2026-10-08: Escape
        # during a travel encounter packed CityScreen under the still-running
        # combat overlay — its city name banner peeked out at the bottom).
        if self._overlay_screen is not None:
            self._dismiss_overlay()
            return

        if not self._screen_history:
            return
        prev_class = self._screen_history.pop()
        # Same guard as switch_to: no game toasts over the main menu.
        if prev_class.__name__ == "MainMenuScreen":
            self.clear_toasts()
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

    def clear_history(self):
        """Clear the back-stack (useful on major state changes, e.g. new game)."""
        self._screen_history.clear()

    # ── Block time (docs/time_system_design.md) ─────────────────────────────

    def _on_time_advanced(self, player=None):
        """Time was spent — schedule a top-bar refresh on the tk main loop.

        Fires from whatever thread spent the time (facility workers included),
        so never touch widgets directly here.
        """
        try:
            self.root.after(0, self._refresh_after_time_advance)
        except (tk.TclError, RuntimeError):
            pass

    def _refresh_after_time_advance(self):
        """Refresh the visible screen's top bar; surface ready Event Notices."""
        try:
            if not self.root.winfo_exists():
                return
            screen = self.get_top_screen()
            if screen is not None and hasattr(screen, "_update_top_bar"):
                try:
                    screen._update_top_bar()
                except Exception:
                    self.refresh_top_bar(self.player)
            else:
                self.refresh_top_bar(self.player)

            # Day-rollover Event Notices surface at the next safe moment (the
            # player is on a city screen with no overlay up).
            self._flush_event_notices_in_city()
        except tk.TclError:
            pass  # Root/widgets torn down (teardown or a replaced manager)

    def _flush_event_notices_in_city(self):
        """Show queued Event Notices while the player is on a city screen.

        Day-rollover events queue up and are normally surfaced on city entry
        (gui/screens/city_screen.py). When a rollover happens while the player
        is ALREADY in a safe city state, the notice would otherwise sit
        unread until they left and returned. Only fires with no overlay up so
        combat / story / facility flows are never interrupted.
        """
        if self._overlay_screen is not None or self.player is None:
            return
        screen = self.current_screen
        from gui.screens.city_screen import CityScreen
        if not isinstance(screen, CityScreen):
            return
        if not self.player.get("event_queue"):
            return
        try:
            from events import get_event_queue_events, format_event_alert, format_date
            events = get_event_queue_events(self.player)
            if not events:
                return
            for evt in events:
                self.log(format_event_alert(evt), category="event")
            from gui.widgets.event_dialog import show_event_notice
            # Defer the modal so this tick finishes and the next one is
            # scheduled first (time keeps flowing while the player reads).
            self.root.after(150, lambda: show_event_notice(
                events, day_text=format_date(self.player), parent=self.root))
        except Exception:
            pass  # Notice is cosmetic — never let it break the clock

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

        from time_blocks import format_block_track
        from events import format_date
        time_str = format_block_track(p, include_day=False)
        date_str = format_date(p)

        self.top_name.config(text=f"{name}  Lv.{level}")
        if time_str:
            self.top_info.config(text=f"{city}  |  {time_str}  |  {date_str}")
        else:
            # Wonderland time pocket: no track — the flavor rides with the date
            self.top_info.config(text=f"{city}  |  {date_str}")

    # ── Log / notifications ───────────────────────────────────────────────────

    def log(self, message: str, category: str = "system"):
        """Record a line in the persistent session log.

        The old always-visible bottom bar was removed. Messages are stored
        in the session history, viewable via the 📜 popup (top-right).
        Event notices surface through the level-up style event dialog
        (gui/widgets/event_dialog.py) instead.
        """
        self._log_entries.append((category, message))
        # Trim if needed
        max_lines = self.settings.get("log_max_lines", 1000)
        if len(self._log_entries) > max_lines:
            self._log_entries = self._log_entries[-max_lines:]

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

    def clear_toasts(self):
        """Dismiss every active toast immediately.

        Used when leaving the game for the main menu so queued game
        notifications never bleed into menu screens.
        """
        container = getattr(self, "_toast_container", None)
        if not container:
            return
        for child in list(container.winfo_children()):
            dismiss = getattr(child, "dismiss", None)
            try:
                if callable(dismiss):
                    dismiss()
                else:
                    child.destroy()
            except tk.TclError:
                pass  # Widget already gone — nothing to do.

    def _open_log_window(self):
        """Open the log popup.

        During combat the combat log is the relevant history (the session
        log is cleared when a fight starts), so the top-bar 📜 routes to
        the combat log popup whenever a combat screen is showing.
        """
        for screen in (self._overlay_screen, self.current_screen):
            opener = getattr(screen, "open_log_popup", None)
            if callable(opener):
                opener()
                return

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
