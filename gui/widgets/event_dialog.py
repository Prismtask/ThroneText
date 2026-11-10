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
    show_event_notice(events, day_text="19/02 · Summer", parent=root)
"""

import queue
import threading
import tkinter as tk
from typing import List, Optional

from gui.theme import Theme

# All world events are daily (daily_effects cleared on day rollover).
_DEFAULT_DURATION = "Until the end of the day"


def _safe_toplevel(parent=None):
    """Return a usable tkinter toplevel/root, or None if unavailable.

    Never creates a fresh Tk root — that flashes a blank window with the
    default Tk icon and creates a second Tcl interpreter.
    """
    try:
        if parent is not None:
            return parent.winfo_toplevel()
    except (tk.TclError, AttributeError):
        pass
    try:
        return tk._default_root
    except Exception:
        return None


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
        try:
            dlg = _EventNoticeDialog(events, day_text, parent)
            dlg.dialog.wait_window()
        except Exception:
            pass  # Dialog is cosmetic — never crash the game over it
    else:
        result_queue = queue.Queue()

        def _build():
            try:
                dlg = _EventNoticeDialog(events, day_text, parent)
                dlg._result_queue = result_queue
            except Exception:
                result_queue.put(None)

        root = tk._default_root
        if root is None:
            return
        root.after(0, _build)

        try:
            result_queue.get(timeout=120)
        except queue.Empty:
            pass


# ── Dialog sizing ─────────────────────────────────────────────────────────────
# A fixed height cannot know how many lines a wrapped description will take
# (wild-dungeon spawn notices list every ruin). Build the content first, then
# size the window to it; when the events would overflow the screen the body
# becomes scrollable instead of clipping its labels.
_DIALOG_WIDTH = 460
_PAD_X = 24
_SCROLL_GUTTER = 26   # room for the vertical scrollbar when it appears
_SCREEN_MARGIN = 80   # keep the whole dialog on screen
# Fixed vertical chrome: header pady (18+8) + body pady (4+4) + buttons (8+16)
_CHROME_PAD_Y = 58


class _EventNoticeDialog:
    """Modal Toplevel showing event notices (level-up dialog style)."""

    def __init__(self, events, day_text=None, parent=None):
        self._result_queue = None  # Set externally for cross-thread use
        self._scrollable = False

        top = _safe_toplevel(parent) if parent else _safe_toplevel()
        if top is None:
            raise RuntimeError("Event Notice dialog: no tkinter root available")
        self.dialog = tk.Toplevel(top)
        self.dialog.title("Event Notice")
        self.dialog.transient(top)
        self.dialog.resizable(False, False)
        self.dialog.configure(bg=Theme.BG_DARK)
        self.dialog.withdraw()  # lay out offscreen, then reveal fully sized

        # ── Header ────────────────────────────────────────────────────
        header = tk.Frame(self.dialog, bg=Theme.BG_DARK)
        header.pack(fill=tk.X, padx=_PAD_X, pady=(18, 8))

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

        # Width follows the header so larger font settings are not clipped.
        self.dialog.update_idletasks()
        width = max(_DIALOG_WIDTH, header.winfo_reqwidth() + 2 * _PAD_X + 8)
        wrap = max(160, width - 2 * _PAD_X - _SCROLL_GUTTER)

        # ── Continue button (packed BEFORE the body so it can't clip) ──
        btn_area = tk.Frame(self.dialog, bg=Theme.BG_DARK)
        btn_area.pack(side=tk.BOTTOM, fill=tk.X, pady=(8, 16))

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

        # ── Body: scrollable list, one block per event ────────────────
        body_outer = tk.Frame(self.dialog, bg=Theme.BG_DARK)
        body_outer.pack(fill=tk.BOTH, expand=True, padx=_PAD_X, pady=4)

        canvas = tk.Canvas(body_outer, bg=Theme.BG_DARK, bd=0,
                           highlightthickness=0)
        self._body_canvas = canvas
        body = tk.Frame(canvas, bg=Theme.BG_DARK)
        canvas.create_window((0, 0), window=body, anchor="nw", width=wrap)
        scrollbar = tk.Scrollbar(body_outer, orient=tk.VERTICAL,
                                 command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        for i, evt in enumerate(events):
            if i > 0:
                tk.Frame(body, bg=Theme.BORDER, height=1).pack(
                    fill=tk.X, pady=6)

            tag = "[FIXED]" if evt.get("fixed") else "[RANDOM]"
            tk.Label(
                body,
                text=f"{evt.get('name') or 'Unknown Event'}  {tag}",
                bg=Theme.BG_DARK,
                fg="#ffd166",
                font=Theme.FONT_BOLD,
                wraplength=wrap,
                justify=tk.LEFT,
            ).pack(anchor=tk.W, pady=(0, 2))

            duration = evt.get("duration") or _DEFAULT_DURATION
            tk.Label(
                body,
                text=f"\u23f3 Duration: {duration}",
                bg=Theme.BG_DARK,
                fg=Theme.ACCENT_HOVER,
                font=Theme.FONT,
                wraplength=wrap,
                justify=tk.LEFT,
            ).pack(anchor=tk.W, pady=(0, 4))

            tk.Label(
                body,
                text=evt.get("desc") or "",
                bg=Theme.BG_DARK,
                fg=Theme.TEXT,
                font=Theme.FONT,
                wraplength=wrap,
                justify=tk.LEFT,
            ).pack(anchor=tk.W)

        # ── Size to content; scroll only when the screen can't fit it ──
        self.dialog.update_idletasks()
        body_h = max(body.winfo_reqheight(), 1)
        chrome_h = (header.winfo_reqheight()
                    + btn_area.winfo_reqheight() + _CHROME_PAD_Y)
        needed_h = chrome_h + body_h
        try:
            max_h = max(260, self.dialog.winfo_screenheight() - _SCREEN_MARGIN)
        except tk.TclError:
            max_h = 640
        view_h = min(needed_h, max_h)
        canvas_h = max(1, view_h - chrome_h)

        canvas.configure(height=canvas_h, width=wrap)
        if body_h > canvas_h:
            self._scrollable = True
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            canvas.configure(scrollregion=(0, 0, body.winfo_reqwidth(), body_h))
            body.bind("<Configure>", self._sync_scrollregion)
            self.dialog.bind("<MouseWheel>", self._on_mousewheel, add="+")
            self.dialog.bind("<Button-4>", self._on_mousewheel, add="+")
            self.dialog.bind("<Button-5>", self._on_mousewheel, add="+")
            self.dialog.bind("<Prior>", lambda e: self._scroll(-1, "pages"))
            self.dialog.bind("<Next>", lambda e: self._scroll(1, "pages"))
        else:
            canvas.pack(fill=tk.BOTH, expand=True)

        self._center(width, view_h)

        self.dialog.bind("<Return>", lambda e: self._dismiss())
        self.dialog.bind("<KP_Enter>", lambda e: self._dismiss())
        self.dialog.bind("<Escape>", lambda e: self._dismiss())
        self.dialog.protocol("WM_DELETE_WINDOW", self._dismiss)

        self.dialog.deiconify()
        try:
            self.dialog.wait_visibility()
        except tk.TclError:
            pass
        try:
            self.dialog.grab_set()
        except tk.TclError:
            pass
        self.dialog.lift()
        self.dialog.focus_force()

    # ── Scrolling ─────────────────────────────────────────────────────

    def _on_mousewheel(self, event):
        if not self._scrollable:
            return None
        if getattr(event, "num", None) == 4:
            steps = -1
        elif getattr(event, "num", None) == 5:
            steps = 1
        else:
            if event.delta == 0:
                return None
            steps = -1 if event.delta > 0 else 1
        self._body_canvas.yview_scroll(steps, "units")
        return "break"

    def _scroll(self, amount, what):
        if not self._scrollable:
            return None
        self._body_canvas.yview_scroll(amount, what)
        return "break"

    def _sync_scrollregion(self, _event=None):
        try:
            self._body_canvas.configure(
                scrollregion=self._body_canvas.bbox("all"))
        except tk.TclError:
            pass

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
