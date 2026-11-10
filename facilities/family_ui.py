"""facilities/family_ui.py — Birth scenes and child naming (facility UI).

Birth state is created in family.family_tick() (no I/O). This module delivers
the scene and name prompt at the next safe home-sleep point.
"""

from resources.family_scenes import BIRTH_LINES, BIRTH_NAME_PROMPT
from family import name_child


def process_pending_births(player, term):
    """Show birth scenes and name any pending children. Idempotent per child."""
    pending = player.pop("family_births_pending", []) or []
    children = player.get("children", []) or []

    keys = [entry.get("child_key") for entry in pending]
    # Also catch births that happened outside the home-sleep flow.
    for child in children:
        if child.get("pending_name") and child.get("key") not in keys:
            keys.append(child.get("key"))

    for key in keys:
        child = next((c for c in children if c.get("key") == key), None)
        if child is None:
            continue
        mother = child.get("mother_name", "your companion")
        term.clear()
        term.print("═" * 60)
        term.print("  A CHILD IS BORN")
        term.print("═" * 60)
        for line in BIRTH_LINES:
            term.print(line.format(mother=mother))
        term.print("")
        new_name = term.input(BIRTH_NAME_PROMPT + " (leave blank to decide later): ").strip()
        if name_child(child, new_name):
            term.print(f"\n  Welcome to the house, {child['name']}.")
        else:
            # Keep the temporary name but stop prompting every sleep; the
            # Family menu/rename path can change it later.
            child["pending_name"] = False
            term.print(f"\n  For now, the house calls the child {child['name']}.")
        term.pause()
