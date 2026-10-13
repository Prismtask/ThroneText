# facilities/camp.py
"""Night camp on the road (docs/time_system_design.md §8).

Runs inside a FacilityScreen overlay while travelling. The caller handles
the actual day transition — `time_blocks.spend_travel_segment(..., camp=True)`
— so camping counts as rest: the night ends via `end_day(slept=True)` and
no fatigue stack accrues. Requires camp capability: a Portable Camp item
or the Caravan mount (`time_blocks.can_camp`).
"""

from character import player_max_hp
from gui.terminal import term


def camp_event(player, city_id=None):
    """One night at camp. Returns when the party breaks camp at dawn."""
    term.print("=== SET CAMP ===")
    term.print("")
    term.print("You leave the road as dusk bleeds into true dark and find a")
    term.print("sheltered hollow: flat ground, a windbreak of thorn, water close by.")
    term.print("The horses are hobbled; the fire catches on the third try.")
    term.print("")

    choice = term.menu(
        [
            "Sleep soundly (full heal for the party)",
            "Keep watch in shifts (heal half — tired, but sharp)",
        ],
        prompt="How does the night pass?",
        allow_cancel=False,
    )

    if choice == 1:
        # ── Watch in shifts: half heal, small all-stats buff for 3 rooms ──
        targets = [player] + [a for a in player.get("allies", [])
                              if a.get("current_hp", 0) > 0]
        for target in targets:
            if target is player:
                max_hp = player_max_hp(player)
            else:
                max_hp = target.get("max_hp", target.get("current_hp", 1))
            hp = target.get("current_hp", 0)
            if hp > 0:
                target["current_hp"] = min(max_hp, hp + max(1, (max_hp - hp) // 2))
            target.setdefault("active_buffs", [])
            target["active_buffs"] = [b for b in target["active_buffs"]
                                      if b.get("type") != "camp_watch"]
            target["active_buffs"].append({
                "type": "camp_watch",
                "stat": "all",
                "value": 1,
                "remaining": 3,
            })
        term.print("")
        term.print("Nothing troubles the fire — but the wild is loud out there.")
        term.print("You wake tired but alert.  (+1 all stats, 3 rooms)")
    else:
        # ── Sleep soundly: full heal for everyone ──
        player["current_hp"] = player_max_hp(player)
        for ally in player.get("allies", []):
            if ally.get("current_hp", 0) > 0:
                ally["current_hp"] = ally.get("max_hp", ally.get("current_hp", 1))
        term.print("")
        term.print("You sleep like the dead and wake with the birds.")
        term.print("The whole party is back to full health.")

    term.print("")
    term.print("You break camp at first light.")
    term.pause("Press Continue to take to the road...")
