# facilities/temple.py
import random
from utils import clear_screen, advance_time, format_time
from character import player_max_hp
from city_dialogue import service_dialogue   # changed

def temple_menu(player, city_id="solmere"):
    while True:
        clear_screen()
        service_dialogue(city_id, "temple", "enter")
        print(f"=== TEMPLE OF {city_id.upper()} ===")
        print(f"Gold: {player.get('gold', 0)} | Time: {format_time(player.get('time_minutes', 480))}")
        
        if player.get("cursed"):
            print("\nYou feel a dark curse weighing upon your soul.")
        else:
            print("\nYou feel at peace in this sacred place.")
        
        print("\n1. Remove Curse (100 gold)")
        print("2. Receive Blessing (50 gold – temporary +2 to all stats for next dungeon floor)")
        print("3. Leave")
        
        choice = input("\nChoice: ").strip()
        
        if choice == "1":
            remove_curse(player, city_id)
            advance_time(player, 30)
        elif choice == "2":
            receive_blessing(player, city_id)
            advance_time(player, 30)
        elif choice == "3":
            service_dialogue(city_id, "temple", "leave")
            advance_time(player, 30)
            break
        else:
            print("Invalid choice.")
            input("Press Enter...")
            advance_time(player, 15)

def remove_curse(player, city_id):
    if not player.get("cursed"):
        print("You are not cursed. No need for cleansing.")
        input("Press Enter...")
        return
    
    cost = 100
    if player.get("gold", 0) < cost:
        print("You don't have enough gold for the ritual.")
        input("Press Enter...")
        return
    
    player["gold"] -= cost
    player["cursed"] = False
    
    if player.get("active_debuffs"):
        player["active_debuffs"] = [d for d in player["active_debuffs"] if d.get("type") != "curse"]
    
    print("The priestess chants ancient prayers. The dark curse lifts from your body.")
    print("The ritual is complete. You feel cleansed.")
    input("Press Enter...")

def receive_blessing(player, city_id):
    cost = 50
    if player.get("gold", 0) < cost:
        print("You cannot afford a blessing.")
        input("Press Enter...")
        return
    
    player["gold"] -= cost
    
    blessing = {
        "type": "blessing",
        "stat": "all",
        "value": 2,
        "remaining": 1
    }
    player.setdefault("active_buffs", []).append(blessing)
    
    print("The temple's light washes over you. You feel divinely empowered (+2 to all stats for the next floor).")
    service_dialogue(city_id, "temple", "bless")
    input("Press Enter...")