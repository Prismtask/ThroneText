"""
gui/widgets/run_summary_dialog.py — scrollable modal run-summary dialog.

Long-form aftermath text (e.g. an Event Horizon run end: depth, payout,
cards, flask effects) in a monospace scrollable body with a single dismiss
button. Enter / Escape / window close all dismiss.

Mirrors confirm_dialog's center-over-parent + grab_set pattern; the button
row is packed FIRST (bottom) so it can never be clipped on small screens.
"""

import tkinter as tk
from typing import Callable, Optional

from gui.theme import Theme
from gui.widgets.confirm_dialog import _safe_toplevel


def run_summary_dialog(
    parent: tk.Widget,
    title: str = "Run Summary",
    heading: str = "RUN SUMMARY",
    body: str = "",
    subtitle: str = "",
    on_close: Optional[Callable] = None,
    close_text: str = "Continue",
):
    """Show a scrollable read-only summary modal. `on_close` runs after dismiss."""
    dw, dh = 680, 560
    try:
        dh = min(dh, parent.winfo_screenheight() - 80)
        dw = min(dw, parent.winfo_screenwidth() - 40)
    except Exception:
        pass

    dialog = tk.Toplevel(parent)
    dialog.title(title)
    dialog.transient(_safe_toplevel(parent))
    dialog.withdraw()   # build offscreen to avoid a blank flash
    dialog.resizable(True, True)
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

    # Heading + subtitle
    tk.Label(
        dialog, text=heading, bg=Theme.BG_DARK, fg=Theme.ACCENT,
        font=Theme.FONT_BOLD,
    ).pack(padx=20, pady=(14, 2))
    if subtitle:
        tk.Label(
            dialog, text=subtitle, bg=Theme.BG_DARK, fg=Theme.TEXT_DIM,
            font=Theme.FONT_SMALL, wraplength=int(dw) - 40, justify=tk.CENTER,
        ).pack(padx=20, pady=(0, 8))

    # Button row FIRST (bottom) — it gets first claim on vertical space
    btn_frame = tk.Frame(dialog, bg=Theme.BG_DARK)
    btn_frame.pack(side=tk.BOTTOM, pady=(6, 14))

    # Scrollable monospace body
    body_frame = tk.Frame(dialog, bg=Theme.BG_DARK)
    body_frame.pack(fill=tk.BOTH, expand=True, padx=18, pady=(4, 2))
    scrollbar = tk.Scrollbar(body_frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    text = tk.Text(
        body_frame, wrap=tk.WORD, yscrollcommand=scrollbar.set,
        bg=Theme.BG_CARD, fg=Theme.TEXT,
        font=(Theme.FONT_FAMILY, 10),
        relief=tk.FLAT, padx=12, pady=10,
        cursor="arrow",
    )
    text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.config(command=text.yview)
    text.insert("1.0", body)
    text.config(state=tk.DISABLED)

    def _close(_event=None):
        dialog.destroy()
        if on_close:
            on_close()

    close_btn = tk.Button(
        btn_frame, text=close_text, command=_close, width=14,
        bg=Theme.ACCENT, fg=Theme.TEXT_HEADER,
        activebackground=Theme.ACCENT_HOVER,
        font=Theme.FONT_BOLD, cursor="hand2",
    )
    close_btn.pack()

    dialog.bind("<Return>", _close)
    dialog.bind("<KP_Enter>", _close)
    dialog.bind("<Escape>", _close)
    dialog.protocol("WM_DELETE_WINDOW", _close)

    # Show only once the content is built (prevents a blank window flash)
    dialog.deiconify()
    dialog.lift()
    dialog.grab_set()
    close_btn.focus_set()
