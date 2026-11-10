"""facilities/house/rest.py — quick rest and full sleep at home.

Rest heals for a small time cost that scales with the house tier; sleep is
Night-only, starts a new day, and grants the Well-Rested buff from Manor
onward. Shared Night / family scenes are triggered from sleep.
"""

from utils import advance_time, display_name
from character import player_max_hp
from resources.enemies import ENEMIES
from gui.terminal import term

from .core import _house_level_data


def _rest_blocks_label(minutes):
    """Player-facing rest cost for a house tier (blocks, not minutes)."""
    import time_blocks
    blocks = time_blocks.blocks_for_minutes(minutes)
    return "free" if blocks <= 0 else f"{blocks} block{'s' if blocks > 1 else ''}"


def _house_rest(player, city_id, house):
    """Quick rest at home — free full heal, costs a small amount of time."""
    lvl_data   = _house_level_data(house)
    rest_mins  = lvl_data["rest_minutes"]
    max_hp     = player_max_hp(player)

    # Heal player
    old_hp               = player["current_hp"]
    player["current_hp"] = max_hp
    healed               = max_hp - old_hp

    # Heal allies too (including defeated allies — recovery)
    for ally in player.get("allies", []):
        if ally.get("defeated"):
            ally["defeated"] = False
            ally["current_hp"] = ally["max_hp"]
            # Print is_recovered dialogue
            from resources.enemies import ENEMIES
            template = ENEMIES.get(ally.get("key", ""), {})
            dialogue = template.get("dialogue", {})
            recovered_line = dialogue.get("is_recovered", f"{display_name(ally)} is back on their feet!")
            if "{name}" in recovered_line:
                recovered_line = recovered_line.format(name=display_name(ally))
            term.print(f"  {recovered_line}")
        elif ally.get("current_hp", 0) > 0:
            ally_old = ally["current_hp"]
            ally["current_hp"] = ally["max_hp"]
            ally_healed = ally["max_hp"] - ally_old
            term.print(f"  {display_name(ally)} healed {ally_healed} HP → {ally['max_hp']}/{ally['max_hp']}")

    advance_time(player, rest_mins)
    import time_blocks
    rest_blocks = time_blocks.blocks_for_minutes(rest_mins)

    home_name = lvl_data["name"].lower()
    term.print(f"You take a quick rest in your {home_name}.")
    if healed > 0:
        term.print(f"  Healed {healed} HP → {max_hp}/{max_hp}")
    else:
        term.print(f"  You were already at full health, but the brief rest feels nice.")
    if rest_blocks > 0:
        term.print(f"  ({rest_blocks} block{'s' if rest_blocks > 1 else ''} passes.)")
    else:
        term.print("  (A quick breather — no time passes.)")
    term.pause()


def _house_sleep(player, city_id, house, partner=None):
    """Sleep at home — full heal; usable only at Night (sleep starts a new day).
    From Manor onward, also grants a Well-Rested stat buff that lasts for dungeon rooms.
    Stat bonus: +1 (Manor–Villa), +2 (Estate–Citadel), +3 (Sanctuary).

    If `partner` is provided (player-initiated), the Shared Night event runs
    with her; otherwise an eligible girl may initiate on her own.
    """
    import time_blocks
    if time_blocks.get_day_phase(player) != "night":
        term.print("You can only sleep at home during the night.")
        term.pause()
        return

    # Combat stress: settle outstanding falls, then let the party rest it off
    # (docs/stress_system_design.md).
    from combat.party_stress import on_party_sleep
    _stress_msgs = on_party_sleep(player)
    for _msg in _stress_msgs:
        term.print(_msg)
    if _stress_msgs:
        term.print("")

    # Shared Night (docs/family_system_design.md §4). Content-level off means
    # no event at all; family_enabled is only checked for conception.
    from family import roll_sleep_initiation, share_night_eligibility
    event_girl = partner
    if event_girl is not None and not share_night_eligibility(player, event_girl, True)[0]:
        event_girl = None
    if event_girl is None:
        event_girl = roll_sleep_initiation(player, house)
    if event_girl is not None:
        from facilities.sleep_sharing_ui import run_sleep_sharing
        run_sleep_sharing(player, event_girl, term)

    lvl_data   = _house_level_data(house)
    buff_val   = lvl_data["bed_buff_value"]
    buff_rooms = lvl_data["bed_buff_floors"]
    max_hp     = player_max_hp(player)

    # Heal player
    old_hp               = player["current_hp"]
    player["current_hp"] = max_hp
    healed               = max_hp - old_hp

    # Heal allies too (including defeated allies — recovery)
    for ally in player.get("allies", []):
        if ally.get("defeated"):
            ally["defeated"] = False
            ally["current_hp"] = ally["max_hp"]
            # Print is_recovered dialogue
            from resources.enemies import ENEMIES
            template = ENEMIES.get(ally.get("key", ""), {})
            dialogue = template.get("dialogue", {})
            recovered_line = dialogue.get("is_recovered", f"{display_name(ally)} is back on their feet!")
            if "{name}" in recovered_line:
                recovered_line = recovered_line.format(name=display_name(ally))
            term.print(f"  {recovered_line}")
        elif ally.get("current_hp", 0) > 0:
            ally_old = ally["current_hp"]
            ally["current_hp"] = ally["max_hp"]
            ally_healed = ally["max_hp"] - ally_old
            term.print(f"  {display_name(ally)} healed {ally_healed} HP → {ally['max_hp']}/{ally['max_hp']}")

    # Apply / refresh Well-Rested buff (Manor and above). Merge with any
    # shared_night buff — take the stronger value/duration, never stack.
    if buff_val > 0:
        from family import grant_sleep_buff
        grant_sleep_buff(player, "well_rested", buff_val, buff_rooms)
        for ally in player.get("allies", []):
            if ally.get("current_hp", 0) > 0:
                grant_sleep_buff(ally, "well_rested", buff_val, buff_rooms)

    time_blocks.end_day(player, slept=True)

    home_name = lvl_data["name"].lower()
    term.print(f"You settle into a deep sleep in your {home_name}.")
    if healed > 0:
        term.print(f"  Healed {healed} HP → {max_hp}/{max_hp}")
    else:
        term.print(f"  You were already at full health, but the sleep restores your spirit.")
    if buff_val > 0:
        term.print(f"  Well-Rested: +{buff_val} to all stats for {buff_rooms} dungeon room(s).")
    term.print("  (The night passes — you wake to a new morning.)")

    # Births resolve during the day roll; deliver scenes/names at this safe point.
    from facilities.family_ui import process_pending_births
    process_pending_births(player, term)

    # Dream events (docs/dream_events_design.md) — one roll per sleep.
    from dreams import maybe_offer_dream
    maybe_offer_dream(player, "home", term)

    term.pause()
