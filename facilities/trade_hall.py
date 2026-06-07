# facilities/trade_hall.py
from utils import advance_time
from city_dialogue import service_dialogue

def trade_hall_service(player, city_id):
    """Trade hall: exchange goods or get trade permits."""
    service_dialogue(city_id, "trade_hall", "enter")
    print("You browse trade ledgers and exotic goods.")
    print("1. Buy trade permit (200 gold) – unlocks special trades")
    print("2. Sell bulk goods (placeholder)")
    print("3. Leave")
    choice = input("\nChoice: ").strip()
    if choice == "1":
        cost = 200
        if player.get("gold", 0) >= cost:
            player["gold"] -= cost
            player["trade_permit"] = True
            print("You obtain a trade permit. New opportunities await.")
            service_dialogue(city_id, "trade_hall", "success")
        else:
            print("Insufficient gold.")
    elif choice == "2":
        print("The merchants offer 50 gold for your spare goods.")
        player["gold"] = player.get("gold", 0) + 50
        print("You receive 50 gold.")
    else:
        service_dialogue(city_id, "trade_hall", "leave")
    input("\nPress Enter...")
    advance_time(player, 30)