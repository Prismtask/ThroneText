"""facilities/sleep_sharing.py — Pure "Shared Night" mini-game logic.

No I/O. The UI layer (`facilities/sleep_sharing_ui.py`) drives this with the
house facility terminal. See docs/family_system_design.md §4 for the
Attunement rules.

Each of three rounds shows the companion's current mood. The player answers
with an action whose tone either matches exactly (+2 Attunement), shares the
mood's energy family (+1), or clashes with it (+0). The total decides the
night: together / warm / quiet. Ending early gives rest.
"""

import random

ACTIONS = ("tender", "playful", "bold", "shy", "end")

# Two compatible "energies" — matching her exact mood is best (+2); the same
# energy family still helps (+1); the opposite energy misses (+0).
TONE_FAMILY = {
    "tender": "soft",
    "shy": "soft",
    "playful": "energetic",
    "bold": "energetic",
}

ROUNDS = 3
MAX_ATTUNEMENT = ROUNDS * 2
PREFERRED_MOOD_CHANCE = 0.75
RANDOM_BEAT_CHANCE = 0.20


def new_state(preferred_tones=(), rng=None, moods=None):
    """Start a 3-round night.

    Her mood each round is shown to the player (no hidden numbers). Moods
    favor her preferred tones (75%) so reading her is achievable, but they
    can still surprise.
    """
    rng = rng or random
    tones = tuple(preferred_tones) or ("tender", "playful")
    all_tones = tuple(TONE_FAMILY.keys())

    if moods is None:
        moods = []
        for _ in range(ROUNDS):
            if rng.random() < PREFERRED_MOOD_CHANCE:
                moods.append(rng.choice(tones))
            else:
                moods.append(rng.choice(all_tones))
    moods = list(moods)[:ROUNDS]
    while len(moods) < ROUNDS:
        moods.append(rng.choice(tones))

    return {
        "round": 1,
        "attunement": 0,
        "done": False,
        "ending": None,
        "moods": moods,
        "mood": moods[0],
    }


def apply_action(state, action, rng=None):
    """Apply one tone action. Mutates state and returns a round result.

    Scoring: exact mood match = +2, same energy family = +1, opposite = 0.
    After 3 rounds: 5–6 Together, 3–4 Warm, 0–2 Quiet. `end` stops early
    with the Rest ending.
    """
    rng = rng or random
    if state.get("done"):
        return {"action": action, "score": 0, "ending": state.get("ending"),
                "mood": state.get("mood"), "attunement": state.get("attunement", 0)}

    if action == "end":
        state["done"] = True
        state["ending"] = "rest"
        return {"action": action, "score": 0, "ending": "rest",
                "mood": state.get("mood"), "attunement": state.get("attunement", 0)}

    if action not in TONE_FAMILY:
        action = "tender"

    mood = state.get("mood", "tender")
    if action == mood:
        score = 2
    elif TONE_FAMILY[action] == TONE_FAMILY[mood]:
        score = 1
    else:
        score = 0

    state["attunement"] = int(state.get("attunement", 0)) + score
    state["round"] = int(state.get("round", 1)) + 1

    ending = None
    if state["round"] > ROUNDS:
        att = state["attunement"]
        ending = "together" if att >= 5 else "warm" if att >= 3 else "quiet"
        state["done"] = True
        state["ending"] = ending
    else:
        state["mood"] = state["moods"][state["round"] - 1]

    return {
        "action": action,
        "score": score,
        "mood": mood,
        "attunement": state["attunement"],
        "ending": ending,
    }


def ending_tier(ending):
    """Short display title for an ending key."""
    from resources.family_scenes import ENDING_TITLES
    return ENDING_TITLES.get(ending, "Rest")
