# facilities/travel.py

from resources.cities import CITIES
from utils import advance_time
from character import player_max_hp


def _danger_tag(travel_time):
    """Return a short danger hint based on journey length."""
    if travel_time >= 200:
        return "  [⚠ Long — high encounter risk]"
    if travel_time >= 120:
        return "  [~ Moderate distance]"
    return ""


def _effective_travel_time(player, raw_time):
    """Apply mount time reduction for overland journeys."""
    mount_id = player.get("mount_id")
    if mount_id:
        from resources.mounts import get_mount
        mount = get_mount(mount_id)
        if mount:
            reduction = mount.get("time_reduction", 0)
            return int(raw_time * (1 - reduction))
    return raw_time


def travel_to_city(player, current_city_id):
    """
    Overland travel between cities.

    Returns
    -------
    "dead"  – player died during a travel encounter
    None    – player arrived safely (or cancelled)
    """
    from facilities.travel_events import run_travel_events

    city            = CITIES.get(current_city_id, CITIES["solmere"])
    all_connections = city.get("travel", {}).get("connections", [])
    land_routes     = [c for c in all_connections if c.get("type", "land") == "land"]

    if not land_routes:
        print("\nThere are no overland roads leading out of this city.")
        input("Press Enter...")
        return

    # Show mount status if any
    mount_id = player.get("mount_id")
    if mount_id:
        from resources.mounts import get_mount
        mount = get_mount(mount_id)
        if mount:
            print(f"\n[Your {mount['name']} is ready. "
                  f"{int(mount['time_reduction']*100)}% faster, "
                  f"{int(mount['event_mitigation']*100)}% safer]")

    print(f"\n=== OVERLAND TRAVEL from {city['name']} ===")
    for i, conn in enumerate(land_routes, 1):
        dest_name = CITIES.get(conn["dest"], {}).get("name", conn["dest"])
        actual_time = _effective_travel_time(player, conn["travel_time"])
        tag       = _danger_tag(actual_time)
        print(f"  {i}. {dest_name}  ({actual_time} min){tag}")
    print("  0. Cancel")

    try:
        idx = int(input("\nChoose destination: ").strip()) - 1
    except ValueError:
        return

    if idx < 0 or idx >= len(land_routes):
        return

    chosen      = land_routes[idx]
    dest_id     = chosen["dest"]
    dest_name   = CITIES.get(dest_id, {}).get("name", dest_id)
    raw_time    = chosen["travel_time"]
    travel_time = _effective_travel_time(player, raw_time)

    # Use origin city biome for thematic enemy selection on this road
    origin_biome = city.get("biome", "temperate")

    print(f"\nYou shoulder your pack and step onto the road to {dest_name}.")
    print(f"Estimated journey: {travel_time} minutes. Keep your eyes open.")
    input("Press Enter to set out...")

    # ── Travel events ────────────────────────────────────────────────────────
    outcome = run_travel_events(
        player,
        travel_time,
        travel_type="land",
        region=origin_biome,
    )

    if outcome == "dead":
        print("\n  You have perished on the road. Your journey ends here...")
        player["current_hp"] = 0
        input("  Press Enter...")
        return "dead"

    # ── Safe arrival ─────────────────────────────────────────────────────────
    advance_time(player, travel_time)
    player["location"] = dest_id

    print(f"\n{'─' * 52}")
    print(f"  You arrive in {dest_name}.")
    print(f"  HP: {player.get('current_hp', '?')}/{player_max_hp(player)}"
          f"  |  Gold: {player.get('gold', 0)}")
    input("  Press Enter to enter the city...")
