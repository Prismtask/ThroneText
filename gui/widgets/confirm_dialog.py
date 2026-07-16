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


def confirm_dialog(
    parent: tk.Widget,
    title: str,
    message: str,
    on_yes: Optional[Callable] = None,
    on_no: Optional[Callable] = None,
    yes_text: str = "Yes",
    no_text: str = "No",
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
    """
    # ── Auto-size based on message ────────────────────────────────────
    lines = message.split("\n")
    max_line_len = max((len(line) for line in lines), default=30)
    # Estimate pixel width needed (Consolas ~7px per char at 11pt)
    est_msg_width = max(280, min(520, max_line_len * 7 + 60))
    line_height = 18
    msg_height = max(len(lines), 1) * line_height + 24

    dw = max(340, int(est_msg_width))
    dh = 100 + msg_height  # title bar + message + button row + padding

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
    dialog.grab_set()
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

    # Message
    tk.Label(
        dialog,
        text=message,
        bg=Theme.BG_DARK,
        fg=Theme.TEXT,
        font=Theme.FONT,
        wraplength=int(dw) - 40,
        justify=tk.CENTER,
    ).pack(padx=20, pady=(16, 14), fill=tk.BOTH, expand=True)

    # Buttons
    btn_frame = tk.Frame(dialog, bg=Theme.BG_DARK)
    btn_frame.pack(pady=(0, 16))

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

    # Focus the yes button by default
    yes_btn.focus_set()

    dialog.protocol("WM_DELETE_WINDOW", _no)


def ok_dialog(
    parent: tk.Widget,
    title: str,
    message: str,
    on_ok: Optional[Callable] = None,
):
    """Show a simple OK dialog.  Enter or Escape = dismiss."""
    # Auto-size
    lines = message.split("\n")
    max_line_len = max((len(line) for line in lines), default=20)
    est_msg_width = max(260, min(480, max_line_len * 7 + 60))
    line_height = 18
    msg_height = max(len(lines), 1) * line_height + 24

    dw = max(300, int(est_msg_width))
    dh = 90 + msg_height
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
    dialog.grab_set()
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

    tk.Label(
        dialog,
        text=message,
        bg=Theme.BG_DARK,
        fg=Theme.TEXT,
        font=Theme.FONT,
        wraplength=int(dw) - 40,
        justify=tk.CENTER,
    ).pack(padx=20, pady=(16, 14), fill=tk.BOTH, expand=True)

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
    ok_btn.pack(pady=(0, 12))
    ok_btn.focus_set()

    dialog.bind("<Return>", _ok)
    dialog.bind("<KP_Enter>", _ok)
    dialog.bind("<Escape>", _ok)
    dialog.protocol("WM_DELETE_WINDOW", _ok)
