# facilities/port.py
from utils import advance_time
from city_dialogue import service_dialogue
from resources.cities import CITIES

def port_service(player, city_id):
    """Portmaster: manages ferry tickets and personal ship sailing."""
    service_dialogue(city_id, "port", "enter")
    
    city = CITIES.get(city_id)
    all_connections = city.get("travel", {}).get("connections", [])
    # FILTER: Find sea routes departing from this port
    sea_connections = [c for c in all_connections if c.get("type") == "sea"]

    if not sea_connections:
        print("\nThis port currently has no active shipping lanes.")
        input("\nPress Enter...")
        return

    has_own_ship = player.get("has_ship", False)

    print(f"\n--- {city['name']} Docks ---")
    if has_own_ship:
        print("Your personal vessel is docked here and ready to sail!")
    else:
        print("You do not own a ship. You must purchase a passenger ticket.")

    print("\nAvailable sea voyages:")
    for i, conn in enumerate(sea_connections, 1):
        dest_name = CITIES.get(conn["dest"], {}).get("name", conn["dest"])
        # If player owns a ship, travel cost is 0! Otherwise, tickets cost 100 gold
        cost = 0 if has_own_ship else 100
        print(f"{i}. Sail to {dest_name} (Cost: {cost}g, Time: {conn['travel_time']} mins)")
    print(f"{len(sea_connections) + 1}. Leave Docks")

    choice = input("\nWhere would you like to sail? ").strip()
    
    try:
        idx = int(choice) - 1
        if idx < 0 or idx >= len(sea_connections):
            service_dialogue(city_id, "port", "leave")
            return

        chosen_voyage = sea_connections[idx]
        dest_id = chosen_voyage["dest"]
        dest_name = CITIES.get(dest_id, {}).get("name", dest_id)
        cost = 0 if has_own_ship else 100

        if player.get("gold", 0) >= cost:
            player["gold"] -= cost
            
            # Mechanical flavor: Personal ships travel 30% faster!
            travel_time = chosen_voyage["travel_time"]
            if has_own_ship:
                travel_time = int(travel_time * 0.7)
                print(f"\nYou captain your ship out into open waters toward {dest_name}...")
            else:
                print(f"\nYou board the passenger ferry bound for {dest_name}...")

            advance_time(player, travel_time)
            player["location"] = dest_id  # <-- Updates player position!
            
            # Optional: Trigger random sea encounter here! (e.g., pirates/storms)
            # trigger_sea_event(player)

            print(f"You have safely docked at {dest_name}.")
            service_dialogue(dest_id, "port", "enter") # Play arrival dialogue for the new city
        else:
            print("You cannot afford a ticket!")
            
    except ValueError:
        print("Invalid selection.")
        
    input("\nPress Enter...")