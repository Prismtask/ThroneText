# facilities/barracks.py
from utils import advance_time
from city_dialogue import service_dialogue

def barracks_service(player, city_id):
    """Barracks: train to gain temporary stat buffs."""
    service_dialogue(city_id, "barracks", "enter")
    print("The drill sergeant offers combat training.")
    print("1. Train (75 gold – gain +2 Strength for next dungeon run)")
    print("2. Leave")
    choice = input("\nChoice: ").strip()
    if choice == "1":
        if player.get("gold", 0) >= 75:
            player["gold"] -= 75
            player["training_buff"] = {"strength": 2, "expires_after": 1}
            print("You sweat through brutal drills. You feel stronger.")
            service_dialogue(city_id, "barracks", "train")
        else:
            print("Not enough gold.")
    else:
        service_dialogue(city_id, "barracks", "leave")
    input("\nPress Enter...")
    advance_time(player, 30)