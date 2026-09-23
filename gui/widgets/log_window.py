"""
gui/widgets/log_window.py — Session log popup (travel-log style).

A Toplevel window showing the full session log history with category
filtering, search, and per-category colors. This is the single log surface
in GUI mode — the old always-visible bottom bar was removed. Opened from
the 📜 button in the top bar, and auto-opens when important messages
(e.g. events) are logged.
"""

import tkinter as tk
from tkinter import scrolledtext

from gui.theme import Theme

# Category → color mapping (travel-log style)
_CATEGORY_COLORS = {
    "event": "#ffd166",
    "dialogue": "#00d2d3",
    "info": Theme.TEXT,
    "dungeon": "#a78bfa",
    "facility": "#51cf66",
    "combat": "#ff6b6b",
    "system": Theme.TEXT_DIM,
}


class LogWindow(tk.Toplevel):
    """Popup log history window with filtering."""

    def __init__(self, parent, log_entries, on_close=None):
        super().__init__(parent)
        self.title("Session Log")
        self.configure(bg=Theme.BG_DARK)
        self.geometry("700x500")
        self.transient(parent)
        self.grab_set()

        self._all_entries = list(log_entries)  # list of (category, message)
        self._on_close = on_close

        # Filter bar
        filter_frame = tk.Frame(self, bg=Theme.BG_DARK)
        filter_frame.pack(fill=tk.X, padx=8, pady=(8, 4))

        tk.Label(
            filter_frame,
            text="Filter:",
            bg=Theme.BG_DARK,
            fg=Theme.TEXT,
            font=Theme.FONT_BOLD,
        ).pack(side=tk.LEFT)

        self._filter_var = tk.StringVar(value="all")
        for cat in ("all", "event", "dialogue", "info", "dungeon", "facility", "combat", "system"):
            tk.Radiobutton(
                filter_frame,
                text=cat.title(),
                variable=self._filter_var,
                value=cat,
                bg=Theme.BG_DARK,
                fg=Theme.TEXT,
                selectcolor=Theme.BG_MID,
                activebackground=Theme.BG_DARK,
                font=Theme.FONT_SMALL,
                command=self._apply_filter,
            ).pack(side=tk.LEFT, padx=4)

        # Search box
        search_frame = tk.Frame(self, bg=Theme.BG_DARK)
        search_frame.pack(fill=tk.X, padx=8, pady=4)

        tk.Label(
            search_frame,
            text="Search:",
            bg=Theme.BG_DARK,
            fg=Theme.TEXT,
            font=Theme.FONT_BOLD,
        ).pack(side=tk.LEFT)

        self.search_entry = tk.Entry(
            search_frame,
            bg=Theme.BG_MID,
            fg=Theme.TEXT,
            font=Theme.FONT,
            insertbackground=Theme.TEXT,
            highlightthickness=1,
            highlightbackground=Theme.BORDER,
            highlightcolor=Theme.ACCENT,
        )
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)
        self.search_entry.bind("<Return>", lambda e: self._apply_filter())

        self.styled_button(search_frame, text="Find", command=self._apply_filter).pack(side=tk.LEFT)

        # Log text
        self.log_text = scrolledtext.ScrolledText(
            self,
            wrap=tk.WORD,
            state=tk.DISABLED,
            bg=Theme.BG_DARK,
            fg=Theme.TEXT,
            font=Theme.FONT,
            highlightthickness=0,
            borderwidth=0,
            padx=8,
            pady=8,
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        # Category color tags (travel-log style)
        for cat, color in _CATEGORY_COLORS.items():
            self.log_text.tag_configure(cat, foreground=color)

        # Bottom buttons
        btn_frame = tk.Frame(self, bg=Theme.BG_DARK)
        btn_frame.pack(fill=tk.X, padx=8, pady=(0, 8))

        self.styled_button(btn_frame, text="Clear", command=self._clear).pack(side=tk.LEFT)
        self.styled_button(btn_frame, text="Close", command=self._on_destroy).pack(side=tk.RIGHT)

        self._apply_filter()

        self.protocol("WM_DELETE_WINDOW", self._on_destroy)

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
        return tk.Button(parent, text=text, command=command, **defaults)

    def _apply_filter(self):
        """Refresh the text widget based on current filter + search."""
        category = self._filter_var.get()
        query = self.search_entry.get().strip().lower()

        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        for cat, msg in self._all_entries:
            if category != "all" and cat != category:
                continue
            if query and query not in msg.lower():
                continue
            tag = cat if cat in _CATEGORY_COLORS else "system"
            self.log_text.insert(tk.END, msg + "\n", tag)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def _clear(self):
        """Clear all log entries."""
        self._all_entries.clear()
        self._apply_filter()

    def _on_destroy(self):
        if self._on_close:
            self._on_close()
        self.destroy()
        self.destroy()
