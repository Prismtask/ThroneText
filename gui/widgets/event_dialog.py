"""
gui/widgets/event_dialog.py — Modal "Event Notice" popup (level-up style).

Shows queued world events (day-rollover events that fired while the player
was away in the dungeon) when they return to a city. Styled like the
level-up dialog: modal Toplevel, gold header, event name + day + duration
+ description, and a Continue button.

The session log history (📜 popup) is kept separate — this dialog is
purely the attention-grabbing notice.

Usage:

    from gui.widgets.event_dialog import show_event_notice
    show_event_notice(events, day_text="Day 169 (M6-D19)", parent=root)
"""

import queue
import threading
import tkinter as tk
from typing import List, Optional

from gui.theme import Theme

# All world events are daily (daily_effects cleared on day rollover).
_DEFAULT_DURATION = "Until the end of the day"


def _safe_toplevel(parent=None):
    """Return a usable tkinter toplevel/root, trying several fallbacks."""
    try:
        return parent.winfo_toplevel()
    except (tk.TclError, AttributeError):
        pass
    try:
        if tk._default_root:
            return tk._default_root
    except Exception:
        pass
    root = tk.Tk()
    root.withdraw()
    return root


def _has_gui():
    """Return True if tkinter has a root window (GUI is available)."""
    try:
        return tk._default_root is not None
    except Exception:
        return False


def _is_main_thread():
    """Return True if the calling thread is the main thread."""
    return threading.current_thread() is threading.main_thread()


def show_event_notice(events: List[dict],
                      day_text: Optional[str] = None,
                      parent=None):
    """Show a modal popup for one or more queued world events.

    Blocks until the player clicks Continue. Safe to call from any thread.
    No-op when the GUI is not available or there are no events.
    """
    if not events or not _has_gui():
        return

    if _is_main_thread():
        dlg = _EventNoticeDialog(events, day_text, parent)
        dlg.dialog.wait_window()
    else:
        result_queue = queue.Queue()

        def _build():
            dlg = _EventNoticeDialog(events, day_text, parent)
            dlg._result_queue = result_queue

        root = tk._default_root
        if root is None:
            return
        root.after(0, _build)

        try:
            result_queue.get(timeout=120)
        except queue.Empty:
            pass


class _EventNoticeDialog:
    """Modal Toplevel showing event notices (level-up dialog style)."""

    def __init__(self, events, day_text=None, parent=None):
        self._result_queue = None  # Set externally for cross-thread use

        top = _safe_toplevel(parent) if parent else _safe_toplevel()
        self.dialog = tk.Toplevel(top)
        self.dialog.title("Event Notice")
        self.dialog.transient(top)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)
        self.dialog.configure(bg=Theme.BG_DARK)

        # ── Header ────────────────────────────────────────────────────
        header = tk.Frame(self.dialog, bg=Theme.BG_DARK)
        header.pack(fill=tk.X, padx=24, pady=(18, 8))

        tk.Label(
            header,
            text="\U0001f4dc  EVENT NOTICE  \U0001f4dc",
            bg=Theme.BG_DARK,
            fg="#ffd166",
            font=Theme.FONT_LARGE,
        ).pack()

        subtitle = (
            f"{len(events)} events occurred" if len(events) > 1
            else "Something happened while you were away"
        )
        tk.Label(
            header,
            text=subtitle,
            bg=Theme.BG_DARK,
            fg=Theme.ACCENT,
            font=Theme.FONT_BOLD,
        ).pack(pady=(2, 0))

        if day_text:
            tk.Label(
                header,
                text=f"\U0001f4c5 {day_text}",
                bg=Theme.BG_DARK,
                fg=Theme.TEXT_DIM,
                font=Theme.FONT,
            ).pack(pady=(2, 0))

        # ── Body: one block per event ─────────────────────────────────
        body = tk.Frame(self.dialog, bg=Theme.BG_DARK)
        body.pack(fill=tk.BOTH, expand=True, padx=24, pady=4)

        for i, evt in enumerate(events):
            if i > 0:
                tk.Frame(body, bg=Theme.BORDER, height=1).pack(
                    fill=tk.X, pady=6)

            tag = "[FIXED]" if evt.get("fixed") else "[RANDOM]"
            tk.Label(
                body,
                text=f"{evt.get('name', 'Unknown Event')}  {tag}",
                bg=Theme.BG_DARK,
                fg="#ffd166",
                font=Theme.FONT_BOLD,
                wraplength=380,
                justify=tk.LEFT,
            ).pack(anchor=tk.W, pady=(0, 2))

            duration = evt.get("duration") or _DEFAULT_DURATION
            tk.Label(
                body,
                text=f"\u23f3 Duration: {duration}",
                bg=Theme.BG_DARK,
                fg=Theme.ACCENT_HOVER,
                font=Theme.FONT,
                wraplength=380,
                justify=tk.LEFT,
            ).pack(anchor=tk.W, pady=(0, 4))

            tk.Label(
                body,
                text=evt.get("desc", ""),
                bg=Theme.BG_DARK,
                fg=Theme.TEXT,
                font=Theme.FONT,
                wraplength=380,
                justify=tk.LEFT,
            ).pack(anchor=tk.W)

        # ── Continue button ───────────────────────────────────────────
        btn_area = tk.Frame(self.dialog, bg=Theme.BG_DARK)
        btn_area.pack(fill=tk.X, pady=(8, 16))

        cont_btn = tk.Button(
            btn_area,
            text="Continue",
            command=self._dismiss,
            bg=Theme.ACCENT,
            fg=Theme.TEXT_HEADER,
            activebackground=Theme.ACCENT_HOVER,
            font=Theme.FONT_BOLD,
            cursor="hand2",
            width=14,
            padx=8,
            pady=4,
        )
        cont_btn.pack()
        cont_btn.focus_set()

        self.dialog.bind("<Return>", lambda e: self._dismiss())
        self.dialog.bind("<KP_Enter>", lambda e: self._dismiss())
        self.dialog.bind("<Escape>", lambda e: self._dismiss())
        self.dialog.protocol("WM_DELETE_WINDOW", self._dismiss)

        # Size & center — grows with the number of events
        needed_h = 210 + len(events) * 95
        self._center(440, min(needed_h, 600))

        self.dialog.wait_visibility()
        self.dialog.lift()
        self.dialog.focus_force()

    def _dismiss(self, _event=None):
        if self._result_queue is not None:
            self._result_queue.put(True)
        self.dialog.destroy()

    def _center(self, width, height):
        try:
            sw = self.dialog.winfo_screenwidth()
            sh = self.dialog.winfo_screenheight()
            x = (sw - width) // 2
            y = (sh - height) // 2
        except Exception:
            x, y = 200, 150
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")
