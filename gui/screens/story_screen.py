"""
gui/screens/story_screen.py — Reusable story-beat conversation window.

Runs a story script (facilities/archivist_intro.py, etc.) in the same
terminal-style FacilityScreen wrapper used by shops and the tutorial, with
the game clock paused while the player reads.

Used two ways:
  - Chained after character creation (gui/screens/char_create_screen.py),
    via switch_to with an on_close callback.
  - As an overlay when the player enters a city (gui/screens/city_screen.py);
    pass on_close=lambda _result: screen_manager.dismiss_overlay().
"""

from gui.screens.facility_screen import FacilityScreen


class StoryScreen(FacilityScreen):
    """FacilityScreen used for story conversations (block time is action-only)."""
