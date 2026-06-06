from utils import clear_screen, advance_time, format_time
from character import player_max_hp
from resources.cities import CITIES
from city import innkeeper_dialogue

def inn_menu(player, city_id="solmere"):
    clear_screen()
    innkeeper_dialogue(city_id, "enter")
    city = CITIES.get(city_id, CITIES["solmere"])
    inn_config = city["inn"]
    print(f"=== THE WARM HEARTH INN - {city['name']} ===")
    print(f"Time: {format_time(player['time_minutes'])}")
    while True:
        print("\n1. Rest (Full Heal - 30 min)")
        print(f"2. Sleep (Full Heal + 8 hours) - Available after {inn_config['sleep_after_hour']}:00")
        print("3. Back")
        choice = input("\nChoice: ").strip()
        if choice == "1":
            player["current_hp"] = player_max_hp(player)
            innkeeper_dialogue(city_id, "rest")
            advance_time(player, 30)
            input("\nPress Enter to return...")
            break
        elif choice == "2":
            current_hour = player["time_minutes"] // 60
            sleep_hour = inn_config.get("sleep_after_hour")
            if current_hour >= sleep_hour or current_hour < 4:
                player["current_hp"] = player_max_hp(player)
                innkeeper_dialogue(city_id, "sleep")
                advance_time(player, 480)
                input("\nYou wake up refreshed the next morning...")
                break
            else:
                innkeeper_dialogue(city_id, "early_sleep")
        elif choice == "3":
            innkeeper_dialogue(city_id, "leave")
            break
        else:
            print("Invalid choice.")