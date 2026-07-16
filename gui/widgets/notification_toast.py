"""
gui/widgets/notification_toast.py — Slide-in toast notifications.

Renders NotificationQueue entries as colored banners at the top-right
of the window. Auto-dismisses after a configurable duration.
"""

import tkinter as tk

from gui.theme import Theme


class NotificationToast(tk.Frame):
    """A toast notification that auto-dismisses after duration_ms."""

    CATEGORY_COLORS = {
        "info": Theme.BG_LIGHT,
        "success": Theme.BUFF_POSITIVE,
        "warning": Theme.BUFF_NEUTRAL,
        "error": Theme.BUFF_NEGATIVE,
        "event": Theme.ACCENT,
    }

    def __init__(self, parent, message, category="info", duration_ms=3000):
        bg = self.CATEGORY_COLORS.get(category, Theme.BG_LIGHT)
        super().__init__(parent, bg=bg, highlightthickness=1, highlightbackground=Theme.BORDER)

        self.label = tk.Label(
            self,
            text=message,
            bg=bg,
            fg=Theme.TEXT_HEADER,
            font=Theme.FONT_BOLD,
            wraplength=320,
            justify=tk.LEFT,
            padx=10,
            pady=6,
        )
        self.label.pack()

        # Auto-dismiss
        self._dismiss_id = self.after(duration_ms, self.destroy)

    def dismiss(self):
        """Manually dismiss the toast."""
        if self._dismiss_id:
            try:
                self.after_cancel(self._dismiss_id)
            except (ValueError, AttributeError):
                pass
            self._dismiss_id = None
        try:
            self.destroy()
        except (AttributeError, tk.TclError):
            pass  # Widget already torn down — suppress race condition
