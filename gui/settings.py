"""
gui/settings.py — GUI preferences persistence.

Load and save GUI-only settings independently of the game save file.
This keeps save compatibility at 100% while letting the GUI remember
user preferences across sessions.
"""

import json
import os
import sys

if getattr(sys, 'frozen', False):
    _BASE_DIR = os.path.dirname(sys.executable)
else:
    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SETTINGS_FILE = os.path.join(_BASE_DIR, "savefile", "gui_settings.json")

DEFAULT_SETTINGS = {
    "window_size": "900x700",
    "window_position": None,          # "+x+y" or None for center
    "font_size": 11,
    "theme": "dark",                   # "dark" | "light" | "high_contrast"
    "sound_enabled": False,            # Reserved for future sound system
    "keyboard_mode": True,            # Enable keyboard shortcuts globally
    "show_splash": True,
    "log_max_lines": 1000,             # Combat/dungeon log scrollback
}


def load_settings() -> dict:
    """Load GUI settings from disk, merging with defaults."""
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            # Merge with defaults so new fields are backward-compatible
            merged = DEFAULT_SETTINGS.copy()
            merged.update(loaded)
            return merged
        except (json.JSONDecodeError, OSError):
            pass
    return DEFAULT_SETTINGS.copy()


def save_settings(settings: dict):
    """Save GUI settings to disk."""
    os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)
