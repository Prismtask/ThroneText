"""facilities/house/management.py — income collection and house upgrades."""

from gui.terminal import term

from .constants import HOUSE_LEVELS, HOUSE_MONSTER_GIRL_LIMITS
from .core import _daily_income, _house_level_data, _pending_income
from .rest import _rest_blocks_label


def _house_collect_income(player, city_id, house):
    """Collect accumulated passive income."""
    gold = _pending_income(player, city_id, house)
    if gold <= 0:
        term.print("No income has accumulated yet. Come back tomorrow.")
    else:
        player["gold"]              = player.get("gold", 0) + gold
        house["last_income_day"]    = player.get("day", 1)
        term.print(f"You collect {gold} gold from your {_house_level_data(house)['name'].lower()}'s rental income.")
        term.print(f"  Gold: {player['gold']}")
    term.pause()


def _house_upgrade(player, city_id, house):
    """Upgrade the house to the next level."""
    lvl      = house["level"]
    lvl_data = HOUSE_LEVELS[lvl]
    cost     = lvl_data["upgrade_cost"]
    max_level = max(HOUSE_LEVELS)

    if cost is None or lvl >= max_level:
        term.print(f"Your {_house_level_data(house)['name']} is already at its grandest — no further upgrades available.")
        term.pause()
        return

    next_data = HOUSE_LEVELS[lvl + 1]
    term.print(f"Upgrade to {next_data['name']}?")
    term.print(f"  Cost           : {cost} gold")
    term.print(f"  Storage        : {lvl_data['storage_cap']} → {next_data['storage_cap']} slots")
    term.print(f"  Daily income   : {_daily_income(player, city_id, lvl)} → {_daily_income(player, city_id, lvl + 1)} gold/day")
    term.print(f"  Rest cost      : {_rest_blocks_label(lvl_data['rest_minutes'])} → {_rest_blocks_label(next_data['rest_minutes'])}")
    term.print(f"  Monster girls  : {HOUSE_MONSTER_GIRL_LIMITS[lvl]} → {HOUSE_MONSTER_GIRL_LIMITS[lvl + 1]}")
    if not term.confirm("Proceed with upgrade?"):
        term.print("Upgrade cancelled.")
        term.pause()
        return

    if player.get("gold", 0) < cost:
        term.print(f"Insufficient gold. You need {cost} gold.")
        term.pause()
        return

    player["gold"] -= cost
    house["level"]  = lvl + 1
    from titles import check_unlock as _check_title_unlock
    _check_title_unlock(player)
    term.print(f"Your home has been expanded into a fine {next_data['name']}!")
    term.print(f"  Remaining gold: {player['gold']}")
    term.pause()
