# travel.py
from resources.cities import CITIES
from utils import advance_time

def travel_to_city(player, current_city_id):
    city = CITIES.get(current_city_id, CITIES["solmere"])
    all_connections = city.get("travel", {}).get("connections", [])
    
    # FILTER: Only allow land travel from this menu
    land_connections = [c for c in all_connections if c.get("type", "land") == "land"]
    
    if not land_connections:
        print("There are no overland roads leading out of this city.")
        input("Press Enter...")
        return

    print(f"\nAvailable overland destinations from {city['name']}:")
    for i, conn in enumerate(land_connections, 1):
        dest_id = conn["dest"]
        dest_name = CITIES.get(dest_id, {}).get("name", dest_id)
        print(f"{i}. {dest_name} ({conn['travel_time']} minutes walk)")

    try:
        idx = int(input("Choose destination (0 to cancel): ")) - 1
        if idx < 0 or idx >= len(land_connections):
            return
        
        chosen_route = land_connections[idx]
        dest_id = chosen_route["dest"]
        dest_name = CITIES.get(dest_id, {}).get("name", dest_id)
        
        print(f"Traveling on foot to {dest_name}... ({chosen_route['travel_time']} minutes)")
        advance_time(player, chosen_route["travel_time"])
        player["location"] = dest_id
        print(f"Arrived in {dest_name}!")
    except ValueError:
        return