"""
gui/terminal.py — GUI-aware replacement for print()/input() in facility code.

Facility functions import `term` from this module and use:
    term.print(text)        — display text in the GUI output area
    term.clear()            — clear the output area
    term.menu(options)      — show buttons, return chosen index (0-based)
    term.confirm(prompt)    — Yes/No, returns bool
    term.pause(prompt)      — show continue button, wait for click
    term.input(prompt)      — free-text input (fallback for complex cases)

Under the hood, these communicate with the FacilityScreen via thread-safe
queues. The facility function still runs in a background thread, but all
user interaction happens through proper tkinter widgets (buttons, etc.)
rather than a raw text entry.
"""

import threading
import queue
from typing import Optional, List


# ── Thread-local terminal reference ────────────────────────────────────────
# Each facility thread gets its own Terminal instance, set by FacilityScreen
# before the facility function runs.

_thread_local = threading.local()


def get_terminal():
    """Return the Terminal instance for the current facility thread."""
    return getattr(_thread_local, 'terminal', None)


def _set_terminal(terminal):
    """Set the Terminal instance for the current thread. Called by FacilityScreen."""
    _thread_local.terminal = terminal


def _clear_terminal():
    """Remove the Terminal reference. Called after facility exits."""
    _thread_local.terminal = None


class Terminal:
    """
    GUI-aware terminal for facility functions.

    Facility functions call term.print(), term.menu(), etc.
    These methods communicate with the FacilityScreen on the main thread
    via queues, blocking the facility thread until the user responds.
    """

    def __init__(self, screen=None):
        self._screen = screen
        self._stopped = False

    def set_screen(self, screen):
        """Bind to a FacilityScreen instance (called before facility starts)."""
        self._screen = screen

    def stop(self):
        """Signal that the facility should terminate."""
        self._stopped = True
        # Unblock any waiting input
        if self._screen:
            self._screen._input_queue.put("")

    # ── Output ──────────────────────────────────────────────────────────

    def print(self, *args, sep=" ", flush=False):
        """Display text in the GUI output area. Thread-safe.
        
        Args:
            flush: If True, waits briefly for the GUI to render the text
                   before returning. Use before screen transitions or combat.
        """
        text = sep.join(str(a) for a in args)
        if self._screen:
            self._screen._append_output(text)
            if flush:
                # Give the main thread a moment to process the pending output
                # before the facility thread continues (e.g., into combat).
                import time
                time.sleep(0.15)

    def clear(self):
        """Clear the output area."""
        if self._screen:
            self._screen._clear_output()

    def sleep(self, seconds: float = 0.5):
        """Pause the facility thread briefly to let the GUI render pending text.
        
        Use before screen transitions (leave dialogue, combat overlay, etc.)
        so the player can read the last message before the screen changes.
        """
        import time
        time.sleep(seconds)

    # ── Input ───────────────────────────────────────────────────────────

    def pause(self, prompt="Press Continue..."):
        """Show a Continue button and wait for the user to click it."""
        if self._stopped:
            from gui.screens.facility_screen import _FacilityStopped
            raise _FacilityStopped()
        if self._screen:
            self._screen._show_buttons([prompt], allow_cancel=False)
            self._screen._input_queue.get()  # Block until button clicked

    def menu(self, options: List[str], prompt: str = "Choose an option:",
             allow_cancel: bool = False, cancel_label: str = "Cancel",
             styles: list = None):
        """
        Show a list of options as buttons and wait for the user to click one.

        Args:
            options: List of option labels to display as buttons.
            prompt: Header text shown above the buttons.
            allow_cancel: If True, adds a cancel button (returns -1).
                         Defaults to False — most facilities have their own Back/Leave option.
            cancel_label: Label for the cancel button.
            styles: Optional list of dicts (same length as options) for per-button
                    style overrides. Each dict can have: bg, fg, active_bg, active_fg.
                    Use None for default style.

        Returns:
            int: 0-based index of the chosen option, or -1 if cancelled.
        """
        if self._stopped:
            from gui.screens.facility_screen import _FacilityStopped
            raise _FacilityStopped()
        if self._screen:
            self._screen._show_buttons(
                options, prompt=prompt,
                allow_cancel=allow_cancel, cancel_label=cancel_label,
                styles=styles,
            )
            result = self._screen._input_queue.get()  # Block until button clicked
            try:
                return int(result)
            except (ValueError, TypeError):
                return -1
        return -1

    def confirm(self, prompt: str, yes_label: str = "Yes", no_label: str = "No"):
        """
        Ask a yes/no question with buttons. Returns True for yes.
        """
        idx = self.menu([yes_label, no_label], prompt=prompt, allow_cancel=False)
        return idx == 0

    def input(self, prompt: str = "") -> str:
        """
        Free-text input. Falls back to text entry for complex cases
        (e.g., entering numbers, names, etc.).
        """
        if self._stopped:
            from gui.screens.facility_screen import _FacilityStopped
            raise _FacilityStopped()
        if self._screen:
            self._screen._show_input_prompt(prompt)
            return self._screen._input_queue.get()
        return ""

    def open_inventory(self):
        """
        Open the GUI InventoryScreen as an overlay and block until closed.

        This allows dungeon post-room menus to show a proper GUI inventory
        instead of running the terminal-based inventory in the dungeon log.
        """
        if self._stopped:
            from gui.screens.facility_screen import _FacilityStopped
            raise _FacilityStopped()
        if self._screen:
            import queue as _queue
            result_queue = _queue.Queue()

            def _open_overlay():
                from gui.screens.inventory_screen import InventoryScreen
                self._screen.sm.push_overlay(
                    InventoryScreen,
                    is_overlay=True,
                    on_dismiss=lambda: result_queue.put(True),
                )

            self._screen.after(0, _open_overlay)
            result_queue.get()  # Block until inventory overlay is dismissed

    def set_curse_bar(self, floor, curse_name, curse_icon, tier_name):
        """Push Pandemonium curse info to the GUI top bar (thread-safe)."""
        if self._screen and self._screen.sm:
            text = f"☠ Pandemonium | Floor {floor} | {curse_icon} {curse_name} ({tier_name})"
            self._screen.after(0, lambda: self._screen.sm.update_top_bar(text))

    def set_quirk_bar(self, floor, quirk_summary, region_name="Wonderland"):
        """Push Wonderland quirk/shadow info to the GUI top bar (thread-safe)."""
        if self._screen and self._screen.sm:
            if quirk_summary:
                text = f"✨ {region_name} | Floor {floor} | {quirk_summary}"
            else:
                text = f"✨ {region_name} | Floor {floor}"
            self._screen.after(0, lambda: self._screen.sm.update_top_bar(text))


# ── Module-level singleton for convenience ─────────────────────────────────
# Facility functions can do:  from gui.terminal import term
# and then call term.print(...), term.menu(...), etc.

term = Terminal()
