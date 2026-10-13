"""
version.py — Single source of truth for the game's version.

Scheme: custom 4-part MAJOR.DEVELOPMENT.FEATURE.PATCH (NOT strict SemVer):
  - The 3rd digit opens a named feature chapter and resets the 4th to 0
    (0.1.7.0 "The Chromatic Artisan" → 0.1.8.0 "The Distant Journey").
  - The 4th digit counts quick fixes / small updates within a chapter
    (0.1.8.0 → 0.1.8.1).
The game is pre-1.0, so IS_BETA stays True until the first stable release.

Bump procedure:
  1. Update GAME_VERSION / VERSION_NAME here (IS_BETA only at 1.0.0).
  2. Prepend the new version block (header + sections) at the TOP of
     gui/screens/changelog_screen.py — never edit older headers.
  3. Run tests/_diag_version_consistency.py — expect "version consistency OK".
"""

GAME_VERSION = "0.1.8.0"
VERSION_NAME = "The Distant Journey"

# Pre-1.0 beta: features, balance, and save formats may change between builds.
# Flip to False only when declaring the first stable release (1.0.0).
IS_BETA = True

# Pure version header — matches the changelog's newest (current) header.
VERSION_DISPLAY = f"v{GAME_VERSION} — {VERSION_NAME}"

# Player-facing label (adds the beta clarifier while IS_BETA).
VERSION_LABEL = VERSION_DISPLAY + (" (beta)" if IS_BETA else "")
