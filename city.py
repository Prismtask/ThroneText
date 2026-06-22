# city.py (simplified – handlers removed, now imports from facility modules and city_dialogue)
from utils import clear_screen, advance_time, format_time
from character import player_max_hp
from resources.cities import CITIES
from save_load import save_game
from city_dialogue import service_dialogue

# Import all facility handlers
from facilities.shop import city_shop
from facilities.inn import inn_menu
from facilities.blacksmith import blacksmith_menu
from facilities.temple import temple_menu
from facilities.port import port_service
from facilities.shipyard import shipyard_service
from facilities.trade_hall import trade_hall_service
from facilities.barracks import barracks_service
from facilities.herbalist import herbalist_service
from facilities.arcane_tower import arcane_tower_service
from facilities.black_market import black_market_service
from facilities.guild import guild_service
from facilities.house import house_menu
from facilities.gift_shop import gift_shop_service

# Map service names to handler functions
SERVICE_HANDLERS = {
    "shop":          city_shop,
    "inn":           inn_menu,
    "blacksmith":    blacksmith_menu,
    "port":          port_service,
    "shipyard":      shipyard_service,
    "trade_hall":    trade_hall_service,
    "temple":        temple_menu,
    "barracks":      barracks_service,
    "herbalist":     herbalist_service,
    "arcane_tower":  arcane_tower_service,
    "black_market":  black_market_service,
    "guild":         guild_service,
    "gift_shop":     gift_shop_service,
}


def visit_city(player, city_id=None):
    if city_id is None:
        city_id = player.get("location", "solmere") if player.get("location") != "dungeon" else "solmere"

    if "time_minutes" not in player:
        player["time_minutes"] = 8 * 60
    if "day" not in player:
        player["day"] = 1

    city = CITIES.get(city_id, CITIES["solmere"])

    service_dialogue(city_id, "receptionist", "enter")
    print(f"\nA kind but stern receptionist nods at you from the guild desk in {city['name']}.")

    while True:
        clear_screen()
        current_time_str = format_time(player["time_minutes"])
        print(f"=== {city['name'].upper()} ===")
        service_dialogue(city_id, "receptionist", "enter")
        status_effects = []
        if any(buff.get("type") == "blessing" for buff in player.get("active_buffs", [])):
            status_effects.append("Blessed")
        if player.get("cursed"):
            status_effects.append("Cursed")
        status_field = f" | Status: {' & '.join(status_effects)}" if status_effects else ""
        # Show floor progress specific to this city's dungeon
        _cf     = player.get("city_floors", {}).get(city_id, {})
        _cur_fl = _cf.get("floor", 1) 
        _max_fl = _cf.get("max_floor", player.get("max_floor", 1))
        print(f"Adventurer: {player['name']} | {city['name']} Dungeon: {_cur_fl}/{_max_fl} | Time: {current_time_str} | Gold: {player.get('gold', 0)}{status_field}")

        print("\nAvailable Services:")
        menu_options = {}
        option_num = 1
        for service in city["services"]:
            if service in SERVICE_HANDLERS:
                display_name = service.replace("_", " ").title()
                print(f"{option_num}. {display_name}")
                menu_options[str(option_num)] = service
                option_num += 1

        # ── House option (shown only when the player owns a house here) ───────
        has_house = city_id in player.get("houses", {})
        house_option = None
        if has_house:
            house_data  = player["houses"][city_id]
            from facilities.house import HOUSE_LEVELS, _pending_income
            lvl_name    = HOUSE_LEVELS[house_data["level"]]["name"]
            pending_g   = _pending_income(player, city_id, house_data)
            pending_str = f"  [{pending_g}g ready]" if pending_g > 0 else ""
            print(f"{option_num}. Your House ({lvl_name}){pending_str}")
            house_option = str(option_num)
            option_num += 1

        print(f"{option_num}. View Stats / Inventory")
        inv_option = str(option_num)
        option_num += 1
        print(f"{option_num}. Skill Book")
        skill_option = str(option_num)
        option_num += 1
        print(f"{option_num}. Travel to Another City")
        travel_option = str(option_num)
        option_num += 1
        print(f"{option_num}. Enter the Dungeon")
        dungeon_option = str(option_num)
        option_num += 1
        print(f"{option_num}. Save & Return to Main Menu")
        save_option = str(option_num)

        choice = input("\nChoice: ").strip()

        if choice in menu_options:
            service = menu_options[choice]
            SERVICE_HANDLERS[service](player, city_id)
            if player.get("current_hp", 1) <= 0:
                return False               # killed during a service (e.g. sea voyage)
            if player.get("location") != city_id:
                return True

        elif house_option and choice == house_option:
            house_menu(player, city_id)

        elif choice == inv_option:
            advance_time(player, 30)
            from inventory_ui import manage_inventory_menu
            manage_inventory_menu(player)

        elif choice == skill_option:
            from facilities.skill_book import skill_book_menu
            skill_book_menu(player)

        elif choice == travel_option:
            from facilities.travel import travel_to_city
            result = travel_to_city(player, city_id)
            if result == "dead":
                return False                 # propagate death to game loop
            if player.get("location") != city_id:
                return True

        elif choice == dungeon_option:
            service_dialogue(city_id, "receptionist", "leave")
            advance_time(player, 30)

            # ── Per-city floor progress ──────────────────────────────────────
            if "city_floors" not in player:
                player["city_floors"] = {}
            if city_id not in player["city_floors"]:
                if player.get("origin_city") == city_id or player.get("location") == city_id:
                    player["city_floors"][city_id] = {
                        "floor":     player.get("floor", 1),
                        "max_floor": player.get("max_floor", 1),
                    }
                else:
                    player["city_floors"][city_id] = {"floor": 1, "max_floor": 1}

            city_prog    = player["city_floors"][city_id]
            max_unlocked = city_prog["max_floor"]

            print(f"\n=== Entering {city.get('name', city_id)} Dungeon "
                  f"(Max Unlocked: Floor {max_unlocked}) ===")
            while True:
                try:
                    target = input(
                        f"Enter floor to descend to (1-{max_unlocked}): "
                    ).strip()
                    chosen_floor = int(target)
                    if 1 <= chosen_floor <= max_unlocked:
                        city_prog["floor"] = chosen_floor
                        break
                    else:
                        print(f"Invalid floor. Choose between 1 and {max_unlocked}.")
                except ValueError:
                    print("Please enter a valid floor number.")

            player["dungeon_region"] = city.get("biome", "temperate")
            player["origin_city"]    = city_id
            player["location"]       = "dungeon"
            return True

        elif choice == save_option:
            player["location"] = city_id
            save_game(player)
            print("Game saved. Returning to menu.")
            return False

        else:
            print("Invalid choice.")
            input("\nPress Enter to continue...")