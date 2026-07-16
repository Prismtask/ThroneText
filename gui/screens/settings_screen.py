"""
gui/screens/settings_screen.py — Settings UI.

Allows the player to adjust GUI preferences: font size, window size,
keyboard shortcuts, splash screen, and (reserved) audio options.
"""

import tkinter as tk
from tkinter import ttk

from gui.screens.base_screen import BaseScreen
from gui.theme import Theme
from gui.settings import save_settings


class SettingsScreen(BaseScreen):
    """GUI settings screen."""

    FONT_SIZE_OPTIONS = [9, 10, 11, 12, 13, 14, 16]
    WINDOW_SIZE_OPTIONS = ["800x600", "900x700", "1024x768", "1280x720", "1400x900"]

    def build_ui(self):
        self.sm.update_top_bar("Settings")
        self.sm.clear_log()

        container = self.styled_frame(self)
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Title
        tk.Label(
            container,
            text="Settings",
            bg=Theme.BG_DARK,
            fg=Theme.ACCENT,
            font=Theme.FONT_LARGE,
        ).pack(anchor=tk.W, pady=(0, 16))

        # ── Display section ────────────────────────────────────────────────────
        disp = tk.LabelFrame(
            container,
            text=" Display ",
            bg=Theme.BG_DARK,
            fg=Theme.TEXT,
            font=Theme.FONT_BOLD,
            highlightthickness=1,
            highlightbackground=Theme.BORDER,
        )
        disp.pack(fill=tk.X, pady=6)

        # Font size
        fs_frame = tk.Frame(disp, bg=Theme.BG_DARK)
        fs_frame.pack(fill=tk.X, padx=10, pady=6)

        tk.Label(
            fs_frame,
            text="Font Size:",
            bg=Theme.BG_DARK,
            fg=Theme.TEXT,
            font=Theme.FONT_BOLD,
            width=12,
            anchor=tk.W,
        ).pack(side=tk.LEFT)

        self.font_var = tk.IntVar(value=self.sm.settings.get("font_size", 11))
        font_combo = ttk.Combobox(
            fs_frame,
            textvariable=self.font_var,
            values=self.FONT_SIZE_OPTIONS,
            state="readonly",
            width=8,
        )
        font_combo.pack(side=tk.LEFT, padx=8)

        # Window size
        ws_frame = tk.Frame(disp, bg=Theme.BG_DARK)
        ws_frame.pack(fill=tk.X, padx=10, pady=6)

        tk.Label(
            ws_frame,
            text="Window Size:",
            bg=Theme.BG_DARK,
            fg=Theme.TEXT,
            font=Theme.FONT_BOLD,
            width=12,
            anchor=tk.W,
        ).pack(side=tk.LEFT)

        self.window_var = tk.StringVar(value=self.sm.settings.get("window_size", "900x700"))
        win_combo = ttk.Combobox(
            ws_frame,
            textvariable=self.window_var,
            values=self.WINDOW_SIZE_OPTIONS,
            state="readonly",
            width=12,
        )
        win_combo.pack(side=tk.LEFT, padx=8)

        # ── Gameplay section ───────────────────────────────────────────────────
        game = tk.LabelFrame(
            container,
            text=" Gameplay ",
            bg=Theme.BG_DARK,
            fg=Theme.TEXT,
            font=Theme.FONT_BOLD,
            highlightthickness=1,
            highlightbackground=Theme.BORDER,
        )
        game.pack(fill=tk.X, pady=6)

        self.keyboard_var = tk.BooleanVar(value=self.sm.settings.get("keyboard_mode", True))
        tk.Checkbutton(
            game,
            text="Enable keyboard shortcuts",
            variable=self.keyboard_var,
            bg=Theme.BG_DARK,
            fg=Theme.TEXT,
            selectcolor=Theme.BG_MID,
            activebackground=Theme.BG_DARK,
            font=Theme.FONT,
        ).pack(anchor=tk.W, padx=10, pady=4)

        self.splash_var = tk.BooleanVar(value=self.sm.settings.get("show_splash", True))
        tk.Checkbutton(
            game,
            text="Show splash screen on launch",
            variable=self.splash_var,
            bg=Theme.BG_DARK,
            fg=Theme.TEXT,
            selectcolor=Theme.BG_MID,
            activebackground=Theme.BG_DARK,
            font=Theme.FONT,
        ).pack(anchor=tk.W, padx=10, pady=4)

        # ── Audio (reserved) section ───────────────────────────────────────────
        audio = tk.LabelFrame(
            container,
            text=" Audio (Reserved) ",
            bg=Theme.BG_DARK,
            fg=Theme.TEXT_DIM,
            font=Theme.FONT_BOLD,
            highlightthickness=1,
            highlightbackground=Theme.BORDER,
        )
        audio.pack(fill=tk.X, pady=6)

        self.sound_var = tk.BooleanVar(value=self.sm.settings.get("sound_enabled", False))
        tk.Checkbutton(
            audio,
            text="Enable sound effects (requires restart)",
            variable=self.sound_var,
            bg=Theme.BG_DARK,
            fg=Theme.TEXT_DIM,
            selectcolor=Theme.BG_MID,
            activebackground=Theme.BG_DARK,
            font=Theme.FONT,
        ).pack(anchor=tk.W, padx=10, pady=4)

        # ── Bottom buttons ─────────────────────────────────────────────────────
        btn_frame = tk.Frame(container, bg=Theme.BG_DARK)
        btn_frame.pack(fill=tk.X, pady=(20, 0))

        self.styled_button(
            btn_frame,
            text="Reset to Defaults",
            command=self._reset_defaults,
        ).pack(side=tk.LEFT)

        self.styled_button(
            btn_frame,
            text="Apply & Close",
            command=self._apply_and_close,
            bg=Theme.ACCENT,
            fg=Theme.TEXT_HEADER,
        ).pack(side=tk.RIGHT)

    def _apply_and_close(self):
        """Save settings and go back."""
        self.sm.settings["font_size"] = self.font_var.get()
        self.sm.settings["window_size"] = self.window_var.get()
        self.sm.settings["keyboard_mode"] = self.keyboard_var.get()
        self.sm.settings["show_splash"] = self.splash_var.get()
        self.sm.settings["sound_enabled"] = self.sound_var.get()
        save_settings(self.sm.settings)

        # Apply font size immediately
        from gui.theme import set_font_size
        set_font_size(self.font_var.get())

        # Apply window size if changed
        current_size = self.sm.root.geometry().split("+")[0]
        new_size = self.window_var.get()
        if current_size != new_size:
            try:
                w, h = new_size.split("x")
                self.sm.root.geometry(f"{w}x{h}")
            except (ValueError, AttributeError):
                pass

        self.sm.log("Settings saved.")
        self.sm.go_back()

    def _reset_defaults(self):
        """Reset all settings to defaults."""
        from gui.settings import DEFAULT_SETTINGS
        self.sm.settings.update(DEFAULT_SETTINGS.copy())
        self.font_var.set(self.sm.settings["font_size"])
        self.window_var.set(self.sm.settings["window_size"])
        self.keyboard_var.set(self.sm.settings["keyboard_mode"])
        self.splash_var.set(self.sm.settings["show_splash"])
        self.sound_var.set(self.sm.settings["sound_enabled"])
        save_settings(self.sm.settings)
        self.sm.log("Settings reset to defaults.")
