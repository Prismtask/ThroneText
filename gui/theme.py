"""
gui/theme.py — Color scheme, fonts, and styling constants for Pandemonium GUI.

Dark theme optimized for ASCII art preservation and readability.
"""

import platform

# ── Font Configuration ────────────────────────────────────────────────────────
# Monospace is mandatory: combat HUD, dungeon map, and stat tables rely on
# fixed-width alignment. A proportional font will break the layout.

FONT_FAMILY = {
    "Windows": "Consolas",
    "Darwin": "Menlo",
    "Linux": "DejaVu Sans Mono",
}.get(platform.system(), "Courier")

FONT_SIZE = 11
FONT_SIZE_LARGE = 14
FONT_SIZE_SMALL = 9

FONT = (FONT_FAMILY, FONT_SIZE)
FONT_BOLD = (FONT_FAMILY, FONT_SIZE, "bold")
FONT_LARGE = (FONT_FAMILY, FONT_SIZE_LARGE, "bold")
FONT_SMALL = (FONT_FAMILY, FONT_SIZE_SMALL)


# ── Dynamic font size helper ──────────────────────────────────────────────────
def set_font_size(size: int):
    """Rebuild font tuples at runtime. Call once at app startup after load_settings."""
    global FONT_SIZE, FONT_SIZE_LARGE, FONT_SIZE_SMALL
    global FONT, FONT_BOLD, FONT_LARGE, FONT_SMALL
    FONT_SIZE = size
    FONT_SIZE_LARGE = size + 3
    FONT_SIZE_SMALL = max(8, size - 2)
    FONT = (FONT_FAMILY, FONT_SIZE)
    FONT_BOLD = (FONT_FAMILY, FONT_SIZE, "bold")
    FONT_LARGE = (FONT_FAMILY, FONT_SIZE_LARGE, "bold")
    FONT_SMALL = (FONT_FAMILY, FONT_SIZE_SMALL)
    # Update Theme class references
    Theme.FONT_SIZE = FONT_SIZE
    Theme.FONT_SIZE_LARGE = FONT_SIZE_LARGE
    Theme.FONT_SIZE_SMALL = FONT_SIZE_SMALL
    Theme.FONT = FONT
    Theme.FONT_BOLD = FONT_BOLD
    Theme.FONT_LARGE = FONT_LARGE
    Theme.FONT_SMALL = FONT_SMALL


# ── Color Palette (Dark Theme) ────────────────────────────────────────────────
class Theme:
    """Centralized color and style constants."""

    # Fonts (monospace family is mandatory for ASCII art)
    FONT_FAMILY = FONT_FAMILY
    FONT = FONT
    FONT_BOLD = FONT_BOLD
    FONT_LARGE = FONT_LARGE
    FONT_SMALL = FONT_SMALL

    # Backgrounds
    BG_DARK = "#1a1a2e"
    BG_MID = "#16213e"
    BG_LIGHT = "#0f3460"
    BG_CARD = "#1e1e3f"

    # Accents
    ACCENT = "#e94560"
    ACCENT_HOVER = "#ff6b81"
    ACCENT_DIM = "#a01830"

    # Text
    TEXT = "#eaeaea"
    TEXT_DIM = "#a0a0a0"
    TEXT_HEADER = "#ffffff"

    # HP / Resource bars
    HP_BAR_FILL = "#4ecca3"
    HP_BAR_EMPTY = "#2d3436"
    MP_BAR_FILL = "#3498db"
    MP_BAR_EMPTY = "#2d3436"
    XP_BAR_FILL = "#f1c40f"
    XP_BAR_EMPTY = "#2d3436"

    # Status / buff colors
    BUFF_POSITIVE = "#2ecc71"
    BUFF_NEGATIVE = "#e74c3c"
    BUFF_NEUTRAL = "#f39c12"

    # Rarity colors for items
    RARITY_COMMON = "#b0b0b0"
    RARITY_UNCOMMON = "#1abc9c"
    RARITY_RARE = "#3498db"
    RARITY_EPIC = "#9b59b6"
    RARITY_LEGENDARY = "#f1c40f"
    RARITY_MYTHIC = "#ff6b6b"

    RARITY_COLORS = {
        "common": RARITY_COMMON,
        "uncommon": RARITY_UNCOMMON,
        "rare": RARITY_RARE,
        "epic": RARITY_EPIC,
        "legendary": RARITY_LEGENDARY,
        "mythic": RARITY_MYTHIC,
        "unique": RARITY_MYTHIC,
    }

    # Border / separator
    BORDER = "#2d3436"
    BORDER_FOCUS = "#e94560"

    # Button styles
    BUTTON_BG = BG_MID
    BUTTON_FG = TEXT
    BUTTON_ACTIVE_BG = BG_LIGHT
    BUTTON_ACTIVE_FG = TEXT_HEADER

    # Log / notification
    LOG_BG = BG_DARK
    LOG_BORDER = BORDER


# ── Window Defaults ───────────────────────────────────────────────────────────
WINDOW_MIN_WIDTH = 900
WINDOW_MIN_HEIGHT = 700
WINDOW_DEFAULT_SIZE = f"{WINDOW_MIN_WIDTH}x{WINDOW_MIN_HEIGHT}"
WINDOW_TITLE = "Pandemonium"

# ── Layout Constants ──────────────────────────────────────────────────────────
TOP_BAR_HEIGHT = 40
PADDING = 10
