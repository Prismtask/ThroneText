from utils import advance_time
from inventory import add_item_to_inventory
from resources.items import random_equipment, build_item
from city_dialogue import service_dialogue
import random

def black_market_service(player, city_id):
    """Black market: buy rare/illegal items at high prices."""
    service_dialogue(city_id, "black_market", "enter")
    print("A shadowy figure whispers about forbidden wares.")

    print("\nAvailable goods:")
    print("1. Buy mysterious relic (450 gold) – random rare item")
    print("2. Buy Capture Net - 550 gold")
    print("3. Leave")

    choice = input("\nChoice: ").strip()

    if choice == "1":
        cost = 450
        if player.get("gold", 0) >= cost:
            player["gold"] -= cost
            item = random_equipment(rarity="rare")
            add_item_to_inventory(player, item)
            print(f"You acquire: {item['name']}")
            service_dialogue(city_id, "black_market", "buy")
        else:
            print("Not enough gold.")

    elif choice == "2":
        # Count how many capture nets the player already owns
        current_nets = sum(1 for item in player.get("inventory", []) if item.get("capture_net"))
        if current_nets >= 5:
            print("The dealer smirks. 'You've already bought the maximum I can risk selling you (5 Max).'")
        else:
            cost = 550
            if player.get("gold", 0) >= cost:
                player["gold"] -= cost
                # Random rarity (common/uncommon/rare) via build_item
                rarity = random.choice(["common", "uncommon", "rare", "epic", "legendary"])
                net = build_item("capture_net", rarity=rarity)
                add_item_to_inventory(player, net)
                print(f"You acquire: {net['name']} (x1)")
                service_dialogue(city_id, "black_market", "buy")
            else:
                print("Not enough gold.")

    else:
        service_dialogue(city_id, "black_market", "leave")

    input("\nPress Enter...")
    advance_time(player, 30)