"""facilities/house/family_menu.py — Family status screen.

Shows expecting companions, child growth stages, and lets the player name or
rename children. Family rules live in family.py.
"""

from events import format_day_delta
from utils import display_name
from gui.terminal import term


def _house_family(player, city_id, house):
    """Family status: pregnant companions, children, and naming."""
    from family import (
        growth_days_remaining, growth_days_to_prime, growth_stage_for_child,
        is_prime, name_child, pregnancy_period,
    )

    while True:
        term.clear()
        term.print("=== FAMILY ===")
        day = player.get("day", 1)

        girls = list(house.get("monster_girls", [])) + list(player.get("allies", []))
        expecting = [g for g in girls if g.get("pregnant")]
        if expecting:
            term.print("Expecting:")
            for g in expecting:
                period = pregnancy_period(g, day)
                note = "resting at home" if period == 3 else "still able to travel"
                due_text = format_day_delta(g.get("due_day"), day) if g.get("due_day") else "?"
                term.print(f"  {display_name(g)} — period {period}/3 · "
                           f"due {due_text} ({note})")
        else:
            term.print("Expecting: —")

        children = player.get("children", []) or []
        if children:
            term.print("Children:")
            for i, child in enumerate(children, 1):
                stage = growth_stage_for_child(child, day)
                child["stage"] = stage
                prime = is_prime(child, day) or bool(child.get("prime"))
                label = f"{stage}, prime" if prime else stage
                if stage == "adult":
                    if prime:
                        progress = "adult (aging stopped)"
                    else:
                        progress = (f"adult — {growth_days_to_prime(child, day)} "
                                    f"day(s) to prime")
                else:
                    progress = f"{growth_days_remaining(child, day)} day(s) to the next stage"
                home = child.get("home_city") or city_id
                term.print(f"  {i}. {child.get('name')} ({label}) — {progress} · {home}")
        else:
            term.print("Children: —")

        term.print()
        options = []
        actions = []
        if children:
            options.append("Name or rename a child")
            actions.append("rename")
        options.append("Back")
        actions.append("back")

        choice = term.menu(options, prompt="Family:")
        if choice < 0 or actions[choice] == "back":
            return

        names = [f"{c.get('name')} ({c.get('stage')})" for c in children] + ["Back"]
        idx = term.menu(names, prompt="Which child?")
        if 0 <= idx < len(children):
            new_name = term.input("New name (leave blank to cancel): ").strip()
            if new_name:
                name_child(children[idx], new_name)
                term.print(f"  She is now called {children[idx]['name']}.")
            term.pause()
