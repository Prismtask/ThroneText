from utils import clear_screen, advance_time, format_time
from character import player_max_hp
from resources.cities import CITIES
from save_load import save_game
import random
from resources.dialogues import (
    SOLMERE_RECEPTIONIST_DIALOGUE,
    SOLMERE_SHOPKEEPER_DIALOGUE,
    SOLMERE_INNKEEPER_DIALOGUE,
    BRINEWATCH_RECEPTIONIST_DIALOGUE,
    BRINEWATCH_SHOPKEEPER_DIALOGUE,
    BRINEWATCH_INNKEEPER_DIALOGUE,
    ELDERFEN_RECEPTIONIST_DIALOGUE,
    ELDERFEN_SHOPKEEPER_DIALOGUE,
    ELDERFEN_INNKEEPER_DIALOGUE,
    IRONDEEP_RECEPTIONIST_DIALOGUE,
    IRONDEEP_SHOPKEEPER_DIALOGUE,
    IRONDEEP_INNKEEPER_DIALOGUE,
    SKYLUME_RECEPTIONIST_DIALOGUE,
    SKYLUME_SHOPKEEPER_DIALOGUE,
    SKYLUME_INNKEEPER_DIALOGUE,
    ASHKARA_RECEPTIONIST_DIALOGUE,
    ASHKARA_SHOPKEEPER_DIALOGUE,
    ASHKARA_INNKEEPER_DIALOGUE,
)

CITY_DIALOGUES = {
    "solmere": {
        "receptionist": SOLMERE_RECEPTIONIST_DIALOGUE,
        "shopkeeper": SOLMERE_SHOPKEEPER_DIALOGUE,
        "innkeeper": SOLMERE_INNKEEPER_DIALOGUE,
    },
    "brinewatch": {
        "receptionist": BRINEWATCH_RECEPTIONIST_DIALOGUE,
        "shopkeeper": BRINEWATCH_SHOPKEEPER_DIALOGUE,
        "innkeeper": BRINEWATCH_INNKEEPER_DIALOGUE,
    },
    "elderfen": {
        "receptionist": ELDERFEN_RECEPTIONIST_DIALOGUE,
        "shopkeeper": ELDERFEN_SHOPKEEPER_DIALOGUE,
        "innkeeper": ELDERFEN_INNKEEPER_DIALOGUE,
    },
    "irondeep": {
        "receptionist": IRONDEEP_RECEPTIONIST_DIALOGUE,
        "shopkeeper": IRONDEEP_SHOPKEEPER_DIALOGUE,
        "innkeeper": IRONDEEP_INNKEEPER_DIALOGUE,
    },
    "skylume": {
        "receptionist": SKYLUME_RECEPTIONIST_DIALOGUE,
        "shopkeeper": SKYLUME_SHOPKEEPER_DIALOGUE,
        "innkeeper": SKYLUME_INNKEEPER_DIALOGUE,
    },
    "ashkara": {
        "receptionist": ASHKARA_RECEPTIONIST_DIALOGUE,
        "shopkeeper": ASHKARA_SHOPKEEPER_DIALOGUE,
        "innkeeper": ASHKARA_INNKEEPER_DIALOGUE,
    },
}

def get_city_dialogues(city_id):
    return CITY_DIALOGUES.get(city_id, CITY_DIALOGUES["solmere"])

def receptionist_dialogue(player, city_id, context="enter"):
    dialogues = get_city_dialogues(city_id)["receptionist"]
    if context == "tip":
        print(random.choice(dialogues["tip"]))
    else:
        print(random.choice(dialogues[context]))

def shopkeeper_dialogue(city_id, context="enter"):
    dialogues = get_city_dialogues(city_id)["shopkeeper"]
    print(random.choice(dialogues[context]))

def innkeeper_dialogue(city_id, context="enter"):
    dialogues = get_city_dialogues(city_id)["innkeeper"]
    print(random.choice(dialogues[context]))

def visit_city(player, city_id=None):
    # Lazy imports from facilities
    from facilities.shop import city_shop
    from facilities.inn import inn_menu
    from facilities.travel import travel_to_city
    from facilities.blacksmith import blacksmith_menu   # note: blacksmith now in facilities
    from inventory_ui import manage_inventory_menu

    if city_id is None:
        city_id = player.get("location", "solmere") if player.get("location") != "dungeon" else "solmere"

    if "time_minutes" not in player:
        player["time_minutes"] = 8 * 60
    if "day" not in player:
        player["day"] = 1

    city = CITIES.get(city_id, CITIES["solmere"])

    receptionist_dialogue(player, city_id, "enter")
    print(f"\nA kind but stern receptionist nods at you from the guild desk in {city['name']}.")

    while True:
        clear_screen()
        current_time_str = format_time(player["time_minutes"])
        print(f"=== {city['name'].upper()} ===")
        receptionist_dialogue(player, city_id, "enter")
        print(f"Adventurer: {player['name']} | Floor: {player['floor']} | Time: {current_time_str} | Gold: {player.get('gold', 0)}")

        print("\nAvailable Services:")
        if "shop" in city["services"]:
            print("1. Enter Market (Shop)")
        if "inn" in city["services"]:
            print("2. Visit the Inn")
        if "blacksmith" in city["services"]:
            print("3. Visit Blacksmith")
        print("4. View Stats / Inventory")
        print("5. Travel to Another City")
        print("6. Return to Dungeon")
        print("7. Save & Return to Main Menu")

        choice = input("\nChoice: ").strip()

        if choice == "1" and "shop" in city["services"]:
            advance_time(player, 30)
            city_shop(player, city_id)
        elif choice == "2" and "inn" in city["services"]:
            advance_time(player, 30)
            inn_menu(player, city_id)
        elif choice == "3" and "blacksmith" in city["services"]:
            advance_time(player, 30)
            blacksmith_menu(player, city_id)
        elif choice == "4":
            advance_time(player, 30)
            manage_inventory_menu(player)
        elif choice == "5":
            travel_to_city(player, city_id)
            if player.get("location") != city_id:
                return True
        elif choice == "6":
            receptionist_dialogue(player, city_id, "leave")
            advance_time(player, 30)
            print("You head back into the dungeon...")
            player["location"] = "dungeon"
            return True
        elif choice == "7":
            player["location"] = city_id
            save_game(player)
            print("Game saved. Returning to menu.")
            return False
        else:
            print("Invalid choice.")