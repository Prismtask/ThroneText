# facilities/black_market.py
from utils import advance_time
from inventory import add_item_to_inventory
from resources.items import random_equipment
from city_dialogue import service_dialogue

def black_market_service(player, city_id):
    """Black market: buy rare/illegal items at high prices."""
    service_dialogue(city_id, "black_market", "enter")
    print("A shadowy figure whispers about forbidden wares.")
    print("1. Buy mysterious relic (150 gold) – random rare item")
    print("2. Leave")
    choice = input("\nChoice: ").strip()
    if choice == "1":
        cost = 150
        if player.get("gold", 0) >= cost:
            player["gold"] -= cost
            item = random_equipment(rarity="rare")
            add_item_to_inventory(player, item)
            print(f"You acquire: {item['name']}")
            service_dialogue(city_id, "black_market", "buy")
        else:
            print("Not enough gold.")
    else:
        service_dialogue(city_id, "black_market", "leave")
    input("\nPress Enter...")
    advance_time(player, 30)