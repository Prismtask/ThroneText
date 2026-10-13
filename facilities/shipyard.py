# facilities/shipyard.py
from utils import advance_time
from city_dialogue import service_dialogue
from gui.terminal import term
from resources.ships import SHIPS, get_ship, get_ship_by_tier


def _ship_info_line(sid):
    s = SHIPS[sid]
    return (f"{s['name']} — {int(s['sea_time_reduction']*100)}% faster, "
            f"{int(s['event_mitigation']*100)}% safer, cargo {s['cargo_capacity']} wt, "
            f"upkeep {s['monthly_fee']}g/mo  ({s['cost']}g)")


def _buy_ship(player, sid):
    s = SHIPS[sid]
    if player.get("gold", 0) < s["cost"]:
        term.print("Not enough gold.")
        term.pause()
        return
    player["gold"] -= s["cost"]
    player["ship_id"] = sid
    term.print(f"You take ownership of the {s['name']}!")
    term.print(f"  (Monthly upkeep: {s['monthly_fee']}g, due on the 1st of each month.)")
    advance_time(player, 30)
    term.pause()


def _upgrade_ship(player):
    current = get_ship(player.get("ship_id"))
    if not current:
        return
    nxt_id, nxt = get_ship_by_tier(current["tier"] + 1)
    if not nxt:
        term.print("Your ship is already top-tier.")
        term.pause()
        return
    diff = max(0, nxt["cost"] - current["cost"])
    if not term.confirm(f"Upgrade {current['name']} → {nxt['name']} for {diff}g?"):
        return
    if player.get("gold", 0) < diff:
        term.print("Not enough gold.")
        term.pause()
        return
    player["gold"] -= diff
    player["ship_id"] = nxt_id
    term.print(f"Your ship has been refitted into the {nxt['name']}!")
    advance_time(player, 30)
    term.pause()


def _downgrade_ship(player):
    current = get_ship(player.get("ship_id"))
    if not current:
        return
    prev_id, prev = get_ship_by_tier(current["tier"] - 1)
    if not prev:
        term.print("You already have the smallest vessel.")
        term.pause()
        return
    refund = max(0, (current["cost"] - prev["cost"]) // 2)
    if not term.confirm(f"Trade down to the {prev['name']} for {refund}g back?"):
        return
    player["ship_id"] = prev_id
    player["gold"] = player.get("gold", 0) + refund
    term.print(f"You settle for the {prev['name']} and pocket {refund}g.")
    advance_time(player, 30)
    term.pause()


def _sell_ship(player):
    current = get_ship(player.get("ship_id"))
    if not current:
        term.print("You have no ship to sell.")
        term.pause()
        return
    refund = current["cost"] // 2
    if not term.confirm(f"Sell your {current['name']} for {refund}g?"):
        return
    player["ship_id"] = None
    player["gold"] = player.get("gold", 0) + refund
    term.print(f"The {current['name']} is sold for {refund}g.")
    advance_time(player, 30)
    term.pause()


def shipyard_service(player, city_id):
    """Shipyard: buy, upgrade, downgrade, or sell sea-going vessels."""
    service_dialogue(city_id, "shipyard", "enter")

    ship = get_ship(player.get("ship_id"))

    from resources.trade_goods import cargo_total_weight
    load = cargo_total_weight(player)
    if load > 0:
        cap = ship["cargo_capacity"] if ship else 0
        term.print(f"Cargo load: {load}{f'/{cap}' if cap else ''} wt")

    if ship:
        choice = term.menu([
            "Upgrade ship",
            "Downgrade ship",
            "Sell ship",
            "Leave",
        ], prompt=f"Your {ship['name']} is moored here "
                  f"(upkeep {ship['monthly_fee']}g/month). What do you need?")
        if choice == 0:
            _upgrade_ship(player)
        elif choice == 1:
            _downgrade_ship(player)
        elif choice == 2:
            _sell_ship(player)
        else:
            service_dialogue(city_id, "shipyard", "leave")
    else:
        opts = []
        sids = []
        for sid, _s in sorted(SHIPS.items(), key=lambda kv: kv[1]["tier"]):
            sids.append(sid)
            opts.append(f"Buy {_ship_info_line(sid)}")
        opts.append("Leave")
        choice = term.menu(opts, prompt="The shipwright gestures at the dry-docks:")
        if 0 <= choice < len(sids):
            _buy_ship(player, sids[choice])
        else:
            service_dialogue(city_id, "shipyard", "leave")

    term.pause()
    advance_time(player, 15)