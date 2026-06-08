# facilities/herbalist.py
from utils import advance_time
from inventory import add_item_to_inventory
from city_dialogue import service_dialogue
from resources.items import build_item  # <-- Import the unified builder

def herbalist_service(player, city_id):
    """Herbalist: buy healing potions or herbs."""
    service_dialogue(city_id, "herbalist", "enter")
    print("The herbalist displays jars of strange ingredients.")
    print("1. Buy healing potion (40 gold)")
    print("2. Buy antidote (30 gold)")
    print("3. Leave")
    choice = input("\nChoice: ").strip()
    
    if choice == "1":
        cost = 40
        if player.get("gold", 0) >= cost:
            player["gold"] -= cost
            # Build using the database dictionary structure
            potion = build_item("healing_potion", rarity="common")
            add_item_to_inventory(player, potion)
            print("You receive a healing potion.")
            service_dialogue(city_id, "herbalist", "buy")
        else:
            print("Not enough gold.")
            
    elif choice == "2":
        cost = 30
        if player.get("gold", 0) >= cost:
            player["gold"] -= cost
            # Since 'Antidote' isn't explicitly in items.py yet, we match its mechanics 
            # to your scroll of cleansing or structural standards. 
            # (Recommendation: Add "antidote" to your ITEMS dictionary in items.py)
            antidote = {
                "id": "antidote",
                "name": "Common Antidote",
                "type": "consumable",
                "power": 0,
                "cure_curse": False, # Or add an explicit 'cure_poison' flag to combat.py if needed
            }
            add_item_to_inventory(player, antidote)
            print("You receive an antidote.")
            service_dialogue(city_id, "herbalist", "buy")
        else:
            print("Not enough gold.")
    else:
        service_dialogue(city_id, "herbalist", "leave")
        
    input("\nPress Enter...")
    advance_time(player, 30)