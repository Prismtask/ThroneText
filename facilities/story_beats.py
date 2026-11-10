"""Story-beat registry — beat id -> script callable.

Beats are queued via quests.queue_story() and delivered as StoryScreen
conversations when the player enters a city
(see gui/screens/city_screen.py::_check_story_beats). The Archivist intro
also has its own flag check ("intro_seen") so it is delivered even on
paths that predate the queue.

Add new beats here: STORY_BEATS["some_beat"] = some_facility_function

ensure_city_story_triggers() handles one-time beats whose conditions are
checked on city entry (currently the Voss & Lumen epilogue).
"""

from facilities.archivist_intro import archivist_intro
from facilities.star_tower import voss_epilogue

STORY_BEATS = {
    "archivist_intro": archivist_intro,
    "voss_epilogue": voss_epilogue,
}


def ensure_city_story_triggers(player, city_id=None):
    """Queue one-time city-entry story beats whose conditions are now met.

    The Voss & Lumen epilogue opens on entering Skylume after Grand Resonance
    (MQ6) and the "A Moth at the Window" house arc are both complete.
    """
    if city_id != "skylume":
        return
    import quests
    state = quests.ensure_quest_state(player)
    if state["flags"].get("voss_epilogue_seen"):
        return
    if quests.quest_state(player, "mq_archivist_06") != "completed":
        return
    seen = (player.get("house_stories") or {}).get("seen") or {}
    if "moth_window_3" not in seen:
        return
    quests.queue_story(player, "voss_epilogue")


def get_story_beat(beat_id):
    """Return the script callable for a beat id, or None."""
    return STORY_BEATS.get(beat_id)
