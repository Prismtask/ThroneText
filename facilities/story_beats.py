"""Story-beat registry — beat id -> script callable.

Beats are queued via quests.queue_story() and delivered as StoryScreen
conversations when the player enters a city
(see gui/screens/city_screen.py::_check_story_beats). The Archivist intro
also has its own flag check ("intro_seen") so it is delivered even on
paths that predate the queue.

Add new beats here: STORY_BEATS["some_beat"] = some_facility_function
"""

from facilities.archivist_intro import archivist_intro

STORY_BEATS = {
    "archivist_intro": archivist_intro,
}


def get_story_beat(beat_id):
    """Return the script callable for a beat id, or None."""
    return STORY_BEATS.get(beat_id)
