"""facilities/house/ — Player House system.

Data layout in player dict
──────────────────────────
player["houses"] = {
    city_id: {
        "level":           int (1–8),
        "storage":         list of item dicts,
        "last_income_day": int  (game day when income was last collected),
        "monster_girls":   list of girl dicts,
    }
}

House levels
────────────
  Lv1 – Hovel       : storage 10 slots,  income  8 gold/day,  rest 1 block
  Lv2 – Cottage     : storage 20 slots,  income 18 gold/day,  rest 1 block
  Lv3 – Manor       : storage 35 slots,  income 35 gold/day,  rest 1 block
  Lv4 – Villa       : storage 55 slots,  income 65 gold/day,  rest free
  Lv5 – Estate      : storage 80 slots,  income 110 gold/day, rest free
  Lv6 – Palace      : storage 120 slots, income 200 gold/day, rest free
  Lv7 – Citadel     : storage 170 slots, income 320 gold/day, rest free
  Lv8 – Sanctuary   : storage 230 slots, income 480 gold/day, rest free

Upgrade costs: Lv1→2 = 600, Lv2→3 = 1500, Lv3→4 = 3000, Lv4→5 = 6000,
               Lv5→6 = 12000, Lv6→7 = 25000, Lv7→8 = 50000

Passive income scales with your highest dungeon floor cleared across all
regions: 1 + min(3, floor / 15), max 4x. The displayed daily rate is the
amount paid; income is banked for at most 5 days.

Module split
────────────
  constants.py       static tiers/caps/thresholds (pure data)
  core.py            house state resolution + income math
  rest.py            quick rest / full sleep
  storage.py         storage chest
  management.py      income collection / upgrades
  lounge.py          companion interactions
  dispatch_board.py  dispatch missions
  family_menu.py     family status / naming
  menu.py            main house menu (wires the above together)

This package re-exports the public names (and the previous private helpers)
so existing imports keep working: ``from facilities.house import house_menu``
and friends are unchanged. Heroine quests live in ``heroine_quests/`` — the
house only offers their entry points.
"""

from .constants import (
    AWAKEN_AFFECTION_REQ,
    AWAKEN_CAP_REQ,
    AWAKEN_LEVEL_REQ,
    CITY_INCOME_MULT,
    ENGAGEMENT_RING_IDS,
    HOUSE_FLOOR_BONUS_CAP,
    HOUSE_FLOOR_BONUS_DIVISOR,
    HOUSE_LEVELS,
    HOUSE_MONSTER_GIRL_LIMITS,
    MAX_INCOME_DAYS,
    RECRUIT_AFFECTION_THRESHOLD,
)
from .core import (
    _affection_gain,
    _apply_ring_bonus_to_girl,
    _daily_income,
    _get_engagement_rings,
    _get_house,
    _get_highest_floor,
    _gifts_remaining,
    _girl_unique_id,
    _has_engagement_ring,
    _house_floor_mult,
    _house_level_data,
    _pending_income,
    _reset_daily_limits,
    _resolve_house,
    _talks_remaining,
    get_current_house_allies,
    get_house_data,
    save_house_data,
)
from .dispatch_board import _dispatch_board, _dispatch_team_select
from .family_menu import _house_family
from .lounge import (
    _can_ascend_ally,
    _fmt_dialogue,
    _get_ascension_requirements,
    _house_lounge,
    _sort_girls,
    can_awaken_girl,
    get_gift_reaction,
)
from .management import _house_collect_income, _house_upgrade
from .menu import house_menu
from .rest import _house_rest, _house_sleep, _rest_blocks_label
from .storage import _house_storage

__all__ = [
    # constants
    "RECRUIT_AFFECTION_THRESHOLD",
    "HOUSE_LEVELS",
    "HOUSE_MONSTER_GIRL_LIMITS",
    "CITY_INCOME_MULT",
    "MAX_INCOME_DAYS",
    "HOUSE_FLOOR_BONUS_CAP",
    "HOUSE_FLOOR_BONUS_DIVISOR",
    "ENGAGEMENT_RING_IDS",
    "AWAKEN_LEVEL_REQ",
    "AWAKEN_CAP_REQ",
    "AWAKEN_AFFECTION_REQ",
    # core
    "_affection_gain",
    "_get_house",
    "_house_level_data",
    "_get_highest_floor",
    "_house_floor_mult",
    "_daily_income",
    "_pending_income",
    "_reset_daily_limits",
    "_talks_remaining",
    "_gifts_remaining",
    "_has_engagement_ring",
    "_get_engagement_rings",
    "_apply_ring_bonus_to_girl",
    "_girl_unique_id",
    "get_current_house_allies",
    "_resolve_house",
    "get_house_data",
    "save_house_data",
    # actions
    "_rest_blocks_label",
    "_house_rest",
    "_house_sleep",
    "_house_storage",
    "_house_collect_income",
    "_house_upgrade",
    # lounge
    "_get_ascension_requirements",
    "_can_ascend_ally",
    "can_awaken_girl",
    "_fmt_dialogue",
    "_sort_girls",
    "_house_lounge",
    "get_gift_reaction",
    # sub-screens
    "_dispatch_board",
    "_dispatch_team_select",
    "_house_family",
    "house_menu",
]
