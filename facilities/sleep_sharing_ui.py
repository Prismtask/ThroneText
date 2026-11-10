"""facilities/sleep_sharing_ui.py — Story/facility UI for Shared Night.

Runs the pure mini-game in facilities/sleep_sharing.py through the existing
house facility terminal (`term.print` / `term.menu` / `term.pause`). No new UI
system and no tkinter calls off the main thread.
"""

from utils import display_name
from facilities.sleep_sharing import (
    ACTIONS, MAX_ATTUNEMENT, RANDOM_BEAT_CHANCE, apply_action, ending_tier, new_state,
)
from resources.family_scenes import (
    ACTION_PROMPTS, COMPATIBLE_LINES, MATCH_LINES, MISS_LINES, RANDOM_BEATS,
    action_lines_for, ending_lines_for, mood_line_for,
    written_action_lines_for, written_ending_lines_for,
)
from family import apply_sleep_outcome, get_content_level, get_preferred_tones


def _attunement_bar(value, width=MAX_ATTUNEMENT):
    filled = max(0, min(width, int(value)))
    return "◆" * filled + "◇" * (width - filled)


def run_sleep_sharing(player, girl, term, rng=None, content_level=None):
    """Play one Shared Night (Attunement) and apply its outcome."""
    from resources.enemies import ENEMIES

    rng = rng or __import__("random")
    template = ENEMIES.get(girl.get("key"), {}) or {}
    tones = get_preferred_tones(girl, template)
    name = display_name(girl)
    girl_key = girl.get("key")
    written = (content_level or get_content_level()) == "written"

    term.clear()
    term.print("═" * 60)
    term.print(f"  A SHARED NIGHT — {name}")
    term.print("═" * 60)
    term.print("Three moments. Read her mood, then choose the answer that fits.")
    term.print("The closer the fit, the more Attunement you gain (max 6).")
    term.pause("Begin")

    state = new_state(tones, rng)

    while not state["done"]:
        mood = state["mood"]
        term.print("")
        term.print(f"  Attunement  {_attunement_bar(state['attunement'])}  "
                   f"{state['attunement']}/{MAX_ATTUNEMENT}")
        term.print(f"  {rng.choice(mood_line_for(girl_key, mood))}")
        term.print("")

        options = [ACTION_PROMPTS[a] for a in ACTIONS]
        choice = term.menu(options, prompt="How do you answer her?")
        if choice < 0 or choice >= len(ACTIONS):
            choice = ACTIONS.index("end")
        action = ACTIONS[choice]
        result = apply_action(state, action, rng)

        if action != "end":
            line = rng.choice(action_lines_for(girl_key, action))
            term.print("  " + (line.format(name=name) if "{name}" in line else line))
            if written:
                wline = rng.choice(written_action_lines_for(girl_key, action))
                term.print("  " + (wline.format(name=name) if "{name}" in wline else wline))
            score = result.get("score", 0)
            if score == 2:
                term.print("  " + rng.choice(MATCH_LINES))
            elif score == 1:
                term.print("  " + rng.choice(COMPATIBLE_LINES))
            else:
                term.print("  " + rng.choice(MISS_LINES))
            if not state["done"] and rng.random() < RANDOM_BEAT_CHANCE:
                term.print("  " + rng.choice(RANDOM_BEATS))

        if not state["done"]:
            term.pause("Continue")

    term.print("")
    ending_pool = (written_ending_lines_for(girl_key, state["ending"])
                   if written else ending_lines_for(girl_key, state["ending"]))
    ending_line = rng.choice(ending_pool)
    term.print("  " + (ending_line.format(name=name) if "{name}" in ending_line else ending_line))

    # Personal closing line: a dedicated night line wins; otherwise her own
    # kiss line gives the scene her voice (present for every girl).
    dialogue = template.get("dialogue", {}) or {}
    personal = dialogue.get("house_night_ending") or dialogue.get("house_bond_kiss")
    if personal:
        term.print("  " + (personal.format(name=name) if "{name}" in personal else personal))

    term.print("  (The rest is yours.)" if written else "  (Fade to black.)")
    term.print("")

    outcome = apply_sleep_outcome(player, girl, state["ending"], rng=rng)
    term.print(f"  {ending_tier(state['ending'])} — Affection +{outcome.get('affection', 0)}"
               f" · Stress {outcome.get('stress', 0)}")
    if outcome.get("conceived"):
        term.print("  ...Something feels different in the quiet afterward.")
    term.pause()
    return outcome
