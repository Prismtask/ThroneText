# facilities/gift_shop.py
import random
from utils import advance_time
from inventory import add_item_to_inventory
from city_dialogue import service_dialogue

GIFT_TYPES = ["flowers", "jewelry", "weapon", "candy", "book"]

ENGAGEMENT_RINGS = [
    ("ruby_engagement_ring", "Ruby Engagement Ring", "Strength", 600),
    ("sapphire_engagement_ring", "Sapphire Engagement Ring", "Wisdom", 600),
    ("emerald_engagement_ring", "Emerald Engagement Ring", "Dexterity", 600),
    ("topaz_engagement_ring", "Topaz Engagement Ring", "Learning", 600),
    ("amethyst_engagement_ring", "Amethyst Engagement Ring", "Charisma", 600),
    ("diamond_engagement_ring", "Diamond Engagement Ring", "Constitution", 600),
]

def _show_engagement_rings(player, city_id):
    print("\n=== Engagement Rings ===")
    print("A token of commitment. Propose to a girl at 100 affection.")
    print("Each ring grants a permanent flat stat bonus while equipped.")
    for i, (item_id, name, stat, cost) in enumerate(ENGAGEMENT_RINGS, 1):
        print(f"{i}. {name} (+3 {stat}) — {cost} gold")
    print("0. Back")
    try:
        choice = int(input("Choice: ").strip())
        if choice == 0:
            return
        if 1 <= choice <= len(ENGAGEMENT_RINGS):
            item_id, name, stat, cost = ENGAGEMENT_RINGS[choice - 1]
            if player.get("gold", 0) < cost:
                print("Not enough gold.")
                return
            from resources.items import build_item
            item = build_item(item_id, "legendary")
            if add_item_to_inventory(player, item):
                player["gold"] -= cost
                print(f"You bought the {name}!")
                service_dialogue(city_id, "gift_shop", "success")
            else:
                print("Your bag is full! Cannot carry the ring.")
        else:
            print("Invalid choice.")
    except ValueError:
        print("Invalid input.")


def gift_shop_service(player, city_id):
    service_dialogue(city_id, "gift_shop", "enter")
    print("=== GIFT SHOP ===")
    print("Special gifts for your companions.\n")

    print("Available Gifts:")
    for i, gtype in enumerate(GIFT_TYPES, 1):
        print(f"{i}. {gtype.title()} (30 gold)")
    print("7. Engagement Rings")
    print("0. Leave")

    choice = input("\nChoice: ").strip()
    if choice == "0":
        service_dialogue(city_id, "gift_shop", "leave")
        advance_time(player, 20)
        return
    if choice == "7":
        _show_engagement_rings(player, city_id)
        advance_time(player, 25)
        input("\nPress Enter...")
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
        if add_item_to_inventory(player, gift_item):
            print(f"You bought a {gift_type.title()} gift!")
            service_dialogue(city_id, "gift_shop", "buy")
        else:
            print("Your bag is full! Cannot carry the gift.")
            player["gold"] += cost  # refund

    except ValueError:
        print("Invalid input.")

    advance_time(player, 25)
    input("\nPress Enter...")