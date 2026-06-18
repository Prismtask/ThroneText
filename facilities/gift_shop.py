# facilities/gift_shop.py
import random
from utils import advance_time
from inventory import add_item_to_inventory
from city_dialogue import service_dialogue

GIFT_TYPES = ["flowers", "jewelry", "weapon", "candy", "book"]

def gift_shop_service(player, city_id):
    service_dialogue(city_id, "gift_shop", "enter")
    print("=== GIFT SHOP ===")
    print("Special gifts for your companions.\n")

    print("Available Gifts:")
    for i, gtype in enumerate(GIFT_TYPES, 1):
        print(f"{i}. {gtype.title()} (30 gold)")

    print("0. Leave")

    choice = input("\nChoice: ").strip()
    if choice == "0":
        service_dialogue(city_id, "gift_shop", "leave")
        advance_time(player, 20)
        return

    try:
        idx = int(choice) - 1
        if idx < 0 or idx >= len(GIFT_TYPES):
            print("Invalid choice.")
            advance_time(player, 10)
            return

        gift_type = GIFT_TYPES[idx]
        cost = 30

        if player.get("gold", 0) < cost:
            print("Not enough gold.")
            advance_time(player, 10)
            return

        player["gold"] -= cost
        gift_item = {
            "name": f"Romantic {gift_type.title()}",
            "type": "gift",
            "gift_type": gift_type,
            "value": 1
        }
        add_item_to_inventory(player, gift_item)
        print(f"You bought a {gift_type.title()} gift!")
        service_dialogue(city_id, "gift_shop", "buy")

    except ValueError:
        print("Invalid input.")

    advance_time(player, 25)
    input("\nPress Enter...")