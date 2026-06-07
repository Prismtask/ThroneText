# facilities/port.py
from utils import advance_time
from city_dialogue import service_dialogue

def port_service(player, city_id):
    """Portmaster: buy travel tickets."""
    service_dialogue(city_id, "port", "enter")
    print("\nThe portmaster eyes your coin purse.")
    print("1. Buy passage (100 gold, 2 hours travel) – placeholder")
    print("2. Leave")
    choice = input("\nChoice: ").strip()
    if choice == "1":
        cost = 100
        if player.get("gold", 0) >= cost:
            player["gold"] -= cost
            advance_time(player, 120)
            print("You book passage on a ship. The voyage is uneventful.")
            service_dialogue(city_id, "port", "buy_ticket")
        else:
            print("Not enough gold.")
    else:
        service_dialogue(city_id, "port", "leave")
    input("\nPress Enter...")