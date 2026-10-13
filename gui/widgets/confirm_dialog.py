"""
gui/widgets/confirm_dialog.py — Yes/No, OK/Cancel reusable modal dialogs.

Built with tkinter Toplevel windows so they block input to the parent
until dismissed (true modal behavior).
"""

import tkinter as tk
from typing import Callable, Optional

from gui.theme import Theme


def _safe_toplevel(parent: tk.Widget) -> tk.Toplevel:
    """Return parent.winfo_toplevel(), falling back to the default root window."""
    try:
        return parent.winfo_toplevel()
    except tk.TclError:
        # Parent destroyed — fall back to the tkinter root
        return parent._root() if hasattr(parent, '_root') else parent.master.winfo_toplevel()
    except Exception:
        # Last resort
        import tkinter as _tk
        return _tk._default_root


# Rough metrics for the dialog font (Consolas ~7px per char at the sizes used).
_CHAR_PX = 7
_LINE_HEIGHT = 18


def _estimate_dialog_size(message, min_width, base_height, max_width):
    """Estimate a dialog's pixel size, accounting for text wrapping.

    The message label wraps at (width - 40) px, so one long source line can
    occupy several visual lines; the height estimate must count those or the
    button row ends up clipped (fixed 2026-09-28 — Glass Anchor examine).
    """
    lines = message.split("\n")
    max_line_len = max((len(line) for line in lines), default=30)
    dw = max(min_width, min(max_width, max_line_len * _CHAR_PX + 60))
    chars_per_line = max(20, (int(dw) - 40) // _CHAR_PX)
    visual_lines = sum(
        max(1, (len(line) + chars_per_line - 1) // chars_per_line)
        for line in lines
    )
    dh = base_height + visual_lines * _LINE_HEIGHT + 24
    return int(dw), int(dh)


def confirm_dialog(
    parent: tk.Widget,
    title: str,
    message: str,
    on_yes: Optional[Callable] = None,
    on_no: Optional[Callable] = None,
    yes_text: str = "Yes",
    no_text: str = "No",
    focus_no: bool = False,
    on_close: Optional[Callable] = None,
):
    """
    Show a Yes/No confirmation dialog.

    Keyboard shortcuts: Enter = Yes, Escape = No (or close).

    Args:
        parent: Parent widget (usually self or self.winfo_toplevel()).
        title: Window title.
        message: Body text.
        on_yes: Callback if user clicks Yes / presses Enter.
        on_no: Callback if user clicks No / presses Escape / closes window.
        yes_text: Label for the affirmative button.
        no_text: Label for the negative button. If None, only the Yes button is shown.
        focus_no: Focus the No button instead of Yes — for dialogs that pop up
                  while the player may be mid-Enter (e.g. after "Press Enter"
                  prompts), preventing an accidental instant confirm.
        on_close: Optional callback for the window X. When None, X behaves
                  like No (legacy); pass a no-op to make X a pure cancel.
    """
    # ── Auto-size based on message (wrapped-line aware) ───────────────
    dw, dh = _estimate_dialog_size(message, min_width=340, base_height=100,
                                   max_width=520)

    # Clamp to screen-visible size
    try:
        screen_h = parent.winfo_screenheight()
        screen_w = parent.winfo_screenwidth()
        dh = min(dh, screen_h - 80)
        dw = min(dw, screen_w - 40)
    except Exception:
        pass

    dialog = tk.Toplevel(parent)
    dialog.title(title)
    dialog.transient(_safe_toplevel(parent))
    dialog.withdraw()   # build offscreen to avoid a blank flash
    dialog.resizable(False, False)
    dialog.configure(bg=Theme.BG_DARK)

    # Center the dialog over the parent
    dialog.update_idletasks()
    try:
        px = _safe_toplevel(parent).winfo_x()
        py = _safe_toplevel(parent).winfo_y()
        pw = _safe_toplevel(parent).winfo_width()
        ph = _safe_toplevel(parent).winfo_height()
    except Exception:
        px = py = 100
        pw = ph = 600
    dialog.geometry(f"{int(dw)}x{int(dh)}+{px + (pw - int(dw)) // 2}+{py + (ph - int(dh)) // 2}")

    # Buttons — packed BEFORE the message so a cramped height can never
    # clip the button row (it gets first claim on the space it needs).
    btn_frame = tk.Frame(dialog, bg=Theme.BG_DARK)
    btn_frame.pack(side=tk.BOTTOM, pady=(0, 16))

    # Message
    msg_label = tk.Label(
        dialog,
        text=message,
        bg=Theme.BG_DARK,
        fg=Theme.TEXT,
        font=Theme.FONT,
        wraplength=int(dw) - 40,
        justify=tk.CENTER,
    )
    msg_label.pack(padx=20, pady=(16, 14), fill=tk.BOTH, expand=True)

    def _yes(_event=None):
        dialog.destroy()
        if on_yes:
            on_yes()

    def _no(_event=None):
        dialog.destroy()
        if on_no:
            on_no()

    yes_btn = tk.Button(
        btn_frame,
        text=yes_text,
        command=_yes,
        width=12,
        bg=Theme.ACCENT,
        fg=Theme.TEXT_HEADER,
        activebackground=Theme.ACCENT_HOVER,
        font=Theme.FONT_BOLD,
        cursor="hand2",
    )
    yes_btn.pack(side=tk.LEFT, padx=8)

    if no_text is not None:
        no_btn = tk.Button(
            btn_frame,
            text=no_text,
            command=_no,
            width=12,
            bg=Theme.BUTTON_BG,
            fg=Theme.TEXT,
            activebackground=Theme.BUTTON_ACTIVE_BG,
            font=Theme.FONT_BOLD,
            cursor="hand2",
        )
        no_btn.pack(side=tk.LEFT, padx=8)
    else:
        no_btn = None

    # ── Keyboard shortcuts ────────────────────────────────────────────
    dialog.bind("<Return>", _yes)
    dialog.bind("<KP_Enter>", _yes)
    dialog.bind("<Escape>", _no)

    def _close(_event=None):
        """X button: pure cancel when on_close is provided (no action fires)."""
        dialog.destroy()
        if on_close:
            on_close()

    # Focus the yes button by default (X = on_close, else legacy on_no)
    dialog.protocol("WM_DELETE_WINDOW", _close if on_close else _no)

    # Show only once the content is built (prevents a blank window flash)
    dialog.deiconify()
    dialog.lift()
    dialog.grab_set()
    if focus_no and no_btn is not None:
        no_btn.focus_set()
    else:
        yes_btn.focus_set()


def ok_dialog(
    parent: tk.Widget,
    title: str,
    message: str,
    on_ok: Optional[Callable] = None,
):
    """Show a simple OK dialog.  Enter or Escape = dismiss."""
    # Auto-size (wrapped-line aware)
    dw, dh = _estimate_dialog_size(message, min_width=300, base_height=90,
                                   max_width=480)
    try:
        screen_h = parent.winfo_screenheight()
        screen_w = parent.winfo_screenwidth()
        dh = min(dh, screen_h - 80)
        dw = min(dw, screen_w - 40)
    except Exception:
        pass

    dialog = tk.Toplevel(parent)
    dialog.title(title)
    dialog.transient(_safe_toplevel(parent))
    dialog.withdraw()   # build offscreen to avoid a blank flash
    dialog.resizable(False, False)
    dialog.configure(bg=Theme.BG_DARK)

    dialog.update_idletasks()
    try:
        px = _safe_toplevel(parent).winfo_x()
        py = _safe_toplevel(parent).winfo_y()
        pw = _safe_toplevel(parent).winfo_width()
        ph = _safe_toplevel(parent).winfo_height()
    except Exception:
        px = py = 100
        pw = ph = 600
    dialog.geometry(f"{int(dw)}x{int(dh)}+{px + (pw - int(dw)) // 2}+{py + (ph - int(dh)) // 2}")

    msg_label = tk.Label(
        dialog,
        text=message,
        bg=Theme.BG_DARK,
        fg=Theme.TEXT,
        font=Theme.FONT,
        wraplength=int(dw) - 40,
        justify=tk.CENTER,
    )

    def _ok(_event=None):
        dialog.destroy()
        if on_ok:
            on_ok()

    ok_btn = tk.Button(
        dialog,
        text="OK",
        command=_ok,
        width=12,
        bg=Theme.ACCENT,
        fg=Theme.TEXT_HEADER,
        activebackground=Theme.ACCENT_HOVER,
        font=Theme.FONT_BOLD,
        cursor="hand2",
    )
    # Button first (bottom) so it can never be clipped on cramped heights;
    # the message fills whatever space is left.
    ok_btn.pack(side=tk.BOTTOM, pady=(0, 12))
    msg_label.pack(padx=20, pady=(16, 14), fill=tk.BOTH, expand=True)

    dialog.bind("<Return>", _ok)
    dialog.bind("<KP_Enter>", _ok)
    dialog.bind("<Escape>", _ok)
    dialog.protocol("WM_DELETE_WINDOW", _ok)

    # Show only once the content is built (prevents a blank window flash)
    dialog.deiconify()
    dialog.lift()
    dialog.grab_set()
    ok_btn.focus_set()
