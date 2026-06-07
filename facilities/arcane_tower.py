# facilities/arcane_tower.py
from utils import advance_time
from city_dialogue import service_dialogue

def arcane_tower_service(player, city_id):
    """Arcane tower: research to gain experience or identify items."""
    service_dialogue(city_id, "arcane_tower", "enter")
    print("The archmage offers to share arcane secrets.")
    print("1. Research (100 gold – gain 50 XP)")
    print("2. Leave")
    choice = input("\nChoice: ").strip()
    if choice == "1":
        cost = 100
        if player.get("gold", 0) >= cost:
            player["gold"] -= cost
            player["xp"] = player.get("xp", 0) + 50
            print("You spend hours studying. You feel wiser.")
            service_dialogue(city_id, "arcane_tower", "research")
        else:
            print("Insufficient gold.")
    else:
        service_dialogue(city_id, "arcane_tower", "leave")
    input("\nPress Enter...")
    advance_time(player, 30)