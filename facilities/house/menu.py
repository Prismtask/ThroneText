"""facilities/house/menu.py — main house facility menu.

This is the entry point called from city.py ("Your House"). It only wires
the sub-screens together; each action lives in its own module:

    rest.py            quick rest / sleep
    storage.py         storage chest
    management.py      passive income / upgrades
    lounge.py          companions (talk, gifts, engagement, ascension, …)
    dispatch_board.py  dispatch missions
    family_menu.py     pregnancy / children
    house_stories.py   fireside tales (sibling module)
    heroine_quests/     heroine quests launched from the house (e.g. the
                        Sylvana mirror restoration)
"""

from events import format_date
from gui.terminal import term

from facilities.dispatch import board_label
from facilities.house_stories import available_ready_count, house_storybook
from heroine_quests import sylvana_mirror as sylvana_quest

from .constants import HOUSE_LEVELS, HOUSE_MONSTER_GIRL_LIMITS
from .core import _daily_income, _get_house, _house_level_data, _pending_income
from .dispatch_board import _dispatch_board
from .family_menu import _house_family
from .lounge import _house_lounge
from .management import _house_collect_income, _house_upgrade
from .rest import _house_rest, _house_sleep
from .storage import _house_storage


def house_menu(player, city_id):
    """Entry point called from city.py when player chooses 'Your House'."""
    house    = _get_house(player, city_id)
    if house is None:
        term.print("You don't own a house here.")
        term.pause()
        return

    max_level = max(HOUSE_LEVELS)

    while True:
        term.clear()
        lvl_data = _house_level_data(house)
        pending  = _pending_income(player, city_id, house)
        total_girls = len(house.get("monster_girls", [])) + len(player.get("allies", []))
        max_girls = HOUSE_MONSTER_GIRL_LIMITS.get(house["level"], 2)

        term.print(f"=== Your {lvl_data['name']} ===")
        term.print(f"  Level    : {house['level']} — {lvl_data['name']}")
        term.print(f"  Girls    : {total_girls}/{max_girls}")
        term.print(f"  Storage  : {len(house['storage'])}/{lvl_data['storage_cap']} slots")
        term.print(f"  Income   : {_daily_income(player, city_id, house['level'])} gold/day")
        term.print(f"  Pending  : {pending} gold")
        term.print(f"  Gold     : {player.get('gold', 0)}")
        term.print(f"  Date     : {format_date(player)}")

        story_count = available_ready_count(player, city_id)
        story_label = (f"Fireside tales ({story_count} ready)" if story_count
                       else "Fireside tales")

        options = [
            "Rest (quick heal)",
            "Sleep (full heal; Night only)",
            "Wait (a brief moment)",
            "Wait (a while)",
            "Storage chest",
            "Collect income",
            "Lounge",
            story_label,
        ]
        actions = ["rest", "sleep", "wait1", "waitwhile", "storage", "income",
                   "lounge", "stories"]

        # Heroine quest hooks: the house offers the entry point only — the
        # quest module owns eligibility, cost, progress, and recruitment.
        if sylvana_quest.is_available(player):
            _mirror_idx = actions.index("lounge") + 1
            options.insert(_mirror_idx, sylvana_quest.menu_label(player))
            actions.insert(_mirror_idx, "mirror")

        has_family = bool(player.get("children")) or any(
            g.get("pregnant") for g in
            list(house.get("monster_girls", [])) + list(player.get("allies", []))
        )
        if has_family:
            lounge_idx = actions.index("lounge")
            options.insert(lounge_idx + 1, "Family")
            actions.insert(lounge_idx + 1, "family")

        options.append(board_label(player))
        actions.append("dispatch")

        if house["level"] < max_level:
            next_name = HOUSE_LEVELS[house["level"] + 1]["name"]
            options.append(f"Upgrade to {next_name}")
            actions.append("upgrade")
        options.append("Leave")
        actions.append("leave")

        choice = term.menu(options, prompt="What would you like to do?")
        action = actions[choice] if 0 <= choice < len(actions) else ("leave" if choice == -1 else None)

        if action == "rest":
            _house_rest(player, city_id, house)
        elif action == "sleep":
            _house_sleep(player, city_id, house)
        elif action == "wait1":
            import time_blocks
            time_blocks.wait_blocks(player, 1)
            term.print("Time passes...")
            term.pause()
        elif action == "waitwhile":
            import time_blocks
            result = time_blocks.wait_to_next_phase(player)
            if result is None:
                term.print("You wait. Wonderland waits with you. Nothing passes.")
            elif result == "morning":
                term.print("You sit through the night and greet the morning, exhausted.")
            else:
                term.print(f"A while passes... it is now {result}.")
            term.pause()
        elif action == "storage":
            _house_storage(player, city_id, house)
        elif action == "income":
            _house_collect_income(player, city_id, house)
        elif action == "lounge":
            _house_lounge(player, city_id, house)
        elif action == "mirror":
            sylvana_quest.run_quest(player, house)
        elif action == "family":
            _house_family(player, city_id, house)
        elif action == "stories":
            house_storybook(player, city_id)
        elif action == "dispatch":
            _dispatch_board(player, city_id, house)
        elif action == "upgrade":
            _house_upgrade(player, city_id, house)
        elif action == "leave":
            break
        else:
            term.print("Invalid choice.")
            term.pause()
