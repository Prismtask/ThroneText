"""The Archivist's summons — "A Message in Starlight" (Main Quest 1 delivery).

Runs inside gui/screens/story_screen.py (a paused-clock FacilityScreen):
text appears in the GUI output panel; each pause becomes a Continue button.

The quest is granted BEFORE the first beat renders, so a player who closes
the window early still gets the Journal entry — the safety net.

Entry point: archivist_intro(player)
"""

from gui.terminal import term
from save_load import save_game
import quests

INTRO_SEEN_FLAG = "intro_seen"


def _header(text):
    rule = "═" * min(len(text) + 4, 70)
    term.print(rule)
    term.print(f"  {text}")
    term.print(rule)


def grant_archivist_intro(player):
    """Grant MQ1 and mark the intro seen. Idempotent; returns grant messages."""
    messages = quests.start_quest(player, "mq_archivist_01")
    quests.ensure_quest_state(player)["flags"][INTRO_SEEN_FLAG] = True
    return messages


def archivist_intro(player, city_id=None):
    """Story screen entry point: play the recorded message and grant MQ1."""
    grant_messages = grant_archivist_intro(player)

    term.clear()
    _header("A MESSAGE IN STARLIGHT")

    term.print("A mote of light detaches from the air above you and unfolds into")
    term.print("a wavering, star-patterned projection of a tall, tidy man at a")
    term.print("desk.")
    term.pause("Continue")

    term.print("")
    term.print('"Ah — good, it found you. I am Quillan Voss, Archivist of the')
    term.print(' Star Tower. Please don\'t try to shake my hand; I\'m a recording."')
    term.print("")
    term.print("A moth the size of a teacup flutters through the edge of the")
    term.print("projection and settles on his shoulder, glowing faintly. He doesn't")
    term.print("acknowledge it. She studies you with open, happy curiosity.")
    term.pause("Continue")

    term.print("")
    term.print('"The Archive keeps records of bonds — the echoes left behind when')
    term.print(' a mortal and a monster girl choose to fight as one. Fascinating.')
    term.print(' And mostly unreadable from a desk."')
    term.print("")
    term.print('"I need field readings. What I need is someone who actually walks')
    term.print(' beside them. You, I am told."')
    term.pause("Continue")

    term.print("")
    term.print('"Come to Skylume. Climb the Star Tower — it is the rightmost of')
    term.print(' the five; it hums at night. Ask for me."')
    term.print("")
    term.print("(a pause — the moth bumps his ear)")
    term.print('"…Take the east road when you\'re ready. There\'s no rush. But do')
    term.print(' come."')
    term.print("")
    term.print("The projection folds back into a mote, and drifts away like a")
    term.print("firefly.")
    term.pause("Continue")

    if grant_messages:
        term.print("")
        for msg in grant_messages:
            term.print(msg)
        term.print("Your Journal now tracks it under Main Quest. (Inventory → Journal.)")
    term.pause("Continue")

    try:
        save_game(player)
    except Exception:
        pass  # Never block play because of a save hiccup.
