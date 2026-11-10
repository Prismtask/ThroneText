# facilities/port.py

from city_dialogue import service_dialogue
import karma
import karma_dialogue
from resources.cities import CITIES
from character import player_max_hp
from gui.terminal import term


def _danger_tag(travel_time):
    """Return a short danger hint based on voyage length."""
    if travel_time >= 120:
        return "  [⚠ Long voyage — rough seas likely]"
    if travel_time >= 80:
        return "  [~ Fair-weather crossing]"
    return "  [Short hop]"


def _ticket_cost(player, city_id):
    """Blackwake outlaws get a 50g smuggler's berth instead of the 100g ferry."""
    if (city_id == "blackwake" and karma.is_enabled(player)
            and karma.get_karma(player) <= -25):
        return 50
    return 100


def _apply_cargo(player, travel_time, ship_cap):
    """Apply the cargo load penalty to a sea voyage.

    Weather is charged once, as blocks, by `time_blocks.travel_blocks()` —
    never as a minutes multiplier here.
    """
    from resources.trade_goods import cargo_travel_penalty
    penalty = cargo_travel_penalty(player, ship_cap)
    if penalty > 0:
        travel_time = int(travel_time * (1 + penalty))
    return travel_time


def port_service(player, city_id):
    """Portmaster — ferry tickets and personal ship sailing, now with sea events."""
    service_dialogue(city_id, "port", "enter")
    port_line = karma_dialogue.service_line(player, "port", city_id)
    if port_line:
        term.print(f'  "{port_line}"')

    city            = CITIES.get(city_id, {})
    all_connections = city.get("travel", {}).get("connections", [])
    sea_routes      = [c for c in all_connections if c.get("type") == "sea"]

    if not sea_routes:
        term.print("\nThis port currently has no active shipping lanes.")
        term.pause()
        return

    ship_id = player.get("ship_id")
    ship = None
    if ship_id:
        from resources.ships import get_ship
        ship = get_ship(ship_id)
    ship_name = ship["name"] if ship else None

    from resources.trade_goods import (
        cargo_travel_penalty, cargo_overloaded_for_travel,
        cargo_total_weight,
    )
    ship_cap = ship.get("cargo_capacity", 0) if ship else 0

    term.print(f"\n--- {city['name']} Docks ---")
    if ship:
        term.print(f"  Your {ship_name} is moored and ready. "
                   f"({int(ship['sea_time_reduction']*100)}% faster, no ticket cost)")
    else:
        term.print("  You do not own a ship — passenger ticket required (100g per voyage).")
    load = cargo_total_weight(player)
    if load > 0:
        cap_str = f"{load}/{ship_cap} wt" if ship_cap > 0 else f"{load} wt (no ship — hauled aboard)"
        term.print(f"  Cargo load: {cap_str}")

    # ── Cargo overload check (own ship only; ferries just slow you down) ──
    if ship and cargo_overloaded_for_travel(player, ship_cap):
        term.print("\n[Your ship is overloaded with cargo!]")
        term.print("Sell cargo at a shop market or stash it in your house before sailing.")
        term.pause()
        return

    ticket_cost = _ticket_cost(player, city_id)
    if not ship and ticket_cost < 100:
        term.print("  A smuggler's berth is available — 50g, no papers, no questions.")

    options = []
    for conn in sea_routes:
        dest_name   = CITIES.get(conn["dest"], {}).get("name", conn["dest"])
        raw_time    = conn["travel_time"]
        if ship:
            actual_time = int(raw_time * (1 - ship["sea_time_reduction"]))
        else:
            actual_time = raw_time
        actual_time = _apply_cargo(player, actual_time, ship_cap)
        cost        = 0 if ship else ticket_cost
        tag         = _danger_tag(actual_time)
        options.append(f"{dest_name} — {actual_time} min, {cost}g{tag}")

    choice = term.menu(options, prompt="Where would you like to sail?", allow_cancel=True, cancel_label="Leave the docks")

    if choice < 0 or choice >= len(sea_routes):
        service_dialogue(city_id, "port", "leave")
        return

    chosen      = sea_routes[choice]
    dest_id     = chosen["dest"]
    dest_name   = CITIES.get(dest_id, {}).get("name", dest_id)
    cost        = 0 if ship else ticket_cost
    if ship:
        travel_time = int(chosen["travel_time"] * (1 - ship["sea_time_reduction"]))
    else:
        travel_time = chosen["travel_time"]
    travel_time = _apply_cargo(player, travel_time, ship_cap)

    if player.get("gold", 0) < cost:
        term.print("\n  You cannot afford a passage ticket.")
        term.pause()
        return

    player["gold"] -= cost

    if ship:
        term.print(f"\n  You captain your {ship_name} out of the harbour, bow aimed at {dest_name}...")
    else:
        term.print(f"\n  You board the passenger ferry bound for {dest_name}...")

    import time_blocks
    voyage_blocks = time_blocks.travel_blocks(player, travel_time)
    voyage_label = f"{voyage_blocks} block{'s' if voyage_blocks != 1 else ''}"
    term.print(f"  Estimated voyage: ≈{voyage_label}. Keep your eyes on the horizon.")
    term.pause("  Press Continue to cast off...")

    # ── Sea travel events ─────────────────────────────────────────────────────
    from facilities.travel_events import run_travel_events
    outcome = run_travel_events(player, travel_time, travel_type="sea")

    if outcome == "dead":
        term.print("\n  You are lost to the deep. Your story ends here...")
        player["current_hp"] = 0
        term.pause()
        return   # city.py detects hp == 0 and propagates the death

    # ── Safe arrival ──────────────────────────────────────────────────────────
    time_blocks.spend_blocks(player, voyage_blocks)
    player["location"] = dest_id
    karma.mark_city_arrival(player)

    term.print(f"\n{'─' * 52}")
    term.print(f"  You dock safely at {dest_name}.")
    term.print(f"  HP: {player.get('current_hp', '?')}/{player_max_hp(player)}"
          f"  |  Gold: {player.get('gold', 0)}")
    service_dialogue(dest_id, "port", "enter")

    term.pause()