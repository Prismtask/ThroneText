from resources.cities import CITIES
from utils import advance_time, format_time

def travel_to_city(player, current_city_id):
    city = CITIES.get(current_city_id, CITIES["solmere"])
    connections = city.get("travel", {}).get("connections", [])
    travel_times = city.get("travel", {}).get("travel_time", {})
    if not connections:
        print("No other cities connected from here.")
        input("Press Enter...")
        return
    print(f"\nAvailable destinations from {city['name']}:")
    for i, dest_id in enumerate(connections, 1):
        dest = CITIES.get(dest_id, {})
        minutes = travel_times.get(dest_id, 60)
        print(f"{i}. {dest.get('name', dest_id)} ({minutes} minutes)")
    try:
        idx = int(input("Choose destination (0 to cancel): ")) - 1
        if idx < 0 or idx >= len(connections):
            return
        dest_id = connections[idx]
        dest_name = CITIES.get(dest_id, {}).get("name", dest_id)
        travel_minutes = travel_times.get(dest_id, 60)
        print(f"Traveling to {dest_name}... ({travel_minutes} minutes)")
        advance_time(player, travel_minutes)
        player["location"] = dest_id
        print(f"Arrived in {dest_name}!")
        input("Press Enter to continue...")
    except:
        print("Travel cancelled.")