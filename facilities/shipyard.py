# facilities/shipyard.py
from utils import advance_time
from city_dialogue import service_dialogue

def shipyard_service(player, city_id):
    """Shipyard: buy/repair ships (placeholder)."""
    service_dialogue(city_id, "shipyard", "enter")
    print("1. Buy a small ship (500 gold) – placeholder")
    print("2. Leave")
    choice = input("\nChoice: ").strip()
    if choice == "1":
        cost = 500
        if player.get("gold", 0) >= cost:
            player["gold"] -= cost
            player["has_ship"] = True
            print("You purchase a sturdy vessel.")
            service_dialogue(city_id, "shipyard", "buy_ship")
        else:
            print("Not enough gold.")
    else:
        service_dialogue(city_id, "shipyard", "leave")
    input("\nPress Enter...")
    advance_time(player, 30)