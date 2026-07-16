# facilities/port.py

from utils import advance_time
from city_dialogue import service_dialogue
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


def port_service(player, city_id):
    """Portmaster — ferry tickets and personal ship sailing, now with sea events."""
    service_dialogue(city_id, "port", "enter")

    city            = CITIES.get(city_id, {})
    all_connections = city.get("travel", {}).get("connections", [])
    sea_routes      = [c for c in all_connections if c.get("type") == "sea"]

    if not sea_routes:
        term.print("\nThis port currently has no active shipping lanes.")
        term.pause()
        return

    has_ship  = player.get("has_ship", False)
    ship_name = player.get("ship_type", "vessel").title() if has_ship else None

    term.print(f"\n--- {city['name']} Docks ---")
    if has_ship:
        term.print(f"  Your {ship_name} is moored and ready. (30% faster, no ticket cost)")
    else:
        term.print("  You do not own a ship — passenger ticket required (100g per voyage).")

    options = []
    for conn in sea_routes:
        dest_name   = CITIES.get(conn["dest"], {}).get("name", conn["dest"])
        raw_time    = conn["travel_time"]
        actual_time = int(raw_time * 0.7) if has_ship else raw_time
        cost        = 0 if has_ship else 100
        tag         = _danger_tag(actual_time)
        options.append(f"{dest_name} — {actual_time} min, {cost}g{tag}")

    choice = term.menu(options, prompt="Where would you like to sail?", allow_cancel=True, cancel_label="Leave the docks")

    if choice < 0 or choice >= len(sea_routes):
        service_dialogue(city_id, "port", "leave")
        return

    chosen      = sea_routes[choice]
    dest_id     = chosen["dest"]
    dest_name   = CITIES.get(dest_id, {}).get("name", dest_id)
    cost        = 0 if has_ship else 100
    travel_time = int(chosen["travel_time"] * 0.7) if has_ship else chosen["travel_time"]

    if player.get("gold", 0) < cost:
        term.print("\n  You cannot afford a passage ticket.")
        term.pause()
        return

    player["gold"] -= cost

    if has_ship:
        term.print(f"\n  You captain your {ship_name} out of the harbour, bow aimed at {dest_name}...")
    else:
        term.print(f"\n  You board the passenger ferry bound for {dest_name}...")

    term.print(f"  Estimated voyage: {travel_time} minutes. Keep your eyes on the horizon.")
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
    advance_time(player, travel_time)
    player["location"] = dest_id

    term.print(f"\n{'─' * 52}")
    term.print(f"  You dock safely at {dest_name}.")
    term.print(f"  HP: {player.get('current_hp', '?')}/{player_max_hp(player)}"
          f"  |  Gold: {player.get('gold', 0)}")
    service_dialogue(dest_id, "port", "enter")

    term.pause()