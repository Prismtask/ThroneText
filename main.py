from character import create_character, player_max_hp, ensure_player_fields
from dungeon import explore_dungeon
from save_load import list_saves, load_game, save_game, delete_save  # Added delete_save
from city import visit_city
from resources.cities import CITIES
from utils import clear_screen, format_time, handle_player_death

def main_menu():
    while True:
        clear_screen()
        print("=" * 40)
        print("     TEXT RPG - Throne of Plaintext")
        print("=" * 40)
        print("1. New Game")
        print("2. Continue")
        print("3. Delete Save")  # New option
        print("4. Quit")         # Shifted down
        choice = input("\nEnter choice: ").strip()

        if choice == "1":
            player = create_character()
            ensure_player_fields(player)
            play_game(player)

        elif choice == "2":
            saves = list_saves()
            if not saves:
                print("No save files found.")
                input("Press Enter...")
                continue

            print("\nAvailable saves:")
            for slot, name in saves.items():
                print(f"  {slot}. {name}")

            try:
                slot = int(input("Enter slot number to load: ").strip())
                player = load_game(slot)
                if player is None:
                    print("Invalid slot or corrupted save.")
                    input("Press Enter...")
                    continue
            except ValueError:
                print("Invalid input.")
                input("Press Enter...")
                continue

            print(f"\nLoaded {player['name']} - {player['race']} {player['class']}")
            ensure_player_fields(player)
            # Show per-city floor progress on load screen only when in dungeon
            loc = player.get("location", "dungeon")
            if loc == "dungeon":
                _cf_city = player.get("origin_city") or "solmere"
                _cf = player.get("city_floors", {}).get(_cf_city, {})
                _cur = _cf.get("floor", 1)
                _max = _cf.get("max_floor", 1)
                print(f"HP: {player['current_hp']}/{player_max_hp_display(player)} | "
                      f"City: {_cf_city.title()} | Floor: {_cur} (max {_max})")
            else:
                print(f"HP: {player['current_hp']}/{player_max_hp_display(player)}")
            print(f"Time: {format_time(player.get('time_minutes', 480))}")
            print(f"Location: {loc}")
            input("Press Enter to continue...")

            play_game(player)

        elif choice == "3":  # Handle deletion menu
            saves = list_saves()
            if not saves:
                print("No save files found to delete.")
                input("Press Enter...")
                continue

            print("\nAvailable saves:")
            for slot, name in saves.items():
                print(f"  {slot}. {name}")

            try:
                slot_input = input("\nEnter slot number to delete (or press Enter to cancel): ").strip()
                if not slot_input:
                    continue
                
                slot = int(slot_input)
                if slot not in saves:
                    print("Invalid slot number.")
                    input("Press Enter...")
                    continue

                # Confirm choice before wiping progress
                confirm = input(f"Are you sure you want to permanently delete '{saves[slot]}' (Slot {slot})? (y/n): ").strip().lower()
                if confirm == 'y':
                    if delete_save(slot):
                        print("Save file successfully deleted.")
                    else:
                        print("Error: Could not delete the save file.")
                else:
                    print("Deletion cancelled.")
                input("Press Enter...")

            except ValueError:
                print("Invalid input.")
                input("Press Enter...")
                continue

        elif choice == "4":  # Updated choice index
            print("Farewell, adventurer.")
            break
        else:
            print("Invalid choice.")
            input("Press Enter...")


def player_max_hp_display(player):
    """Helper to avoid import issues in main."""
    from character import player_max_hp
    return player_max_hp(player)


def play_game(player):
    """Main game loop with optional City visits and proper save location handling."""

    # Restore last location if it exists, default to dungeon for old saves
    if "location" not in player:
        player["location"] = "dungeon"

    while True:
        if player.get("location") not in ["dungeon", None]:
            city_id = player["location"]
            print(f"\nYou are in {CITIES.get(city_id, CITIES['solmere'])['name']}...")
            city_result = visit_city(player, city_id)
            if city_result == "save_exit":
                return  # Saved and quit
            if city_result == "dead":
                if not handle_player_death(player):
                    return  # Quit to main menu
                # Player continues; they'll be in the city now
                continue
            if player.get("location") == city_id:
                player["location"] = "dungeon"
            continue

        # === Enter Dungeon ===
        result = explore_dungeon(player)

        if result == "save_exit":
            print("Game saved. Returning to menu.")
            break

        if result == "fled":
            # Player fled back to city – do not advance floor, just loop to city
            # player["location"] is already set to origin_city inside explore_dungeon
            continue

        if result == "dead":
            if not handle_player_death(player):
                input("Press Enter to return to main menu...")
                break
            # Player chose to continue; they're now in the city
            continue

        # Floor cleared
        # explore_dungeon() already advanced city_floors[city]["floor/max_floor"],
        # so we read the cleared floor from there.
        city_id = player.get("origin_city", "solmere")
        city_prog = player["city_floors"].get(city_id, {"floor": 1})
        cleared_floor = city_prog["floor"] - 1   # floor that was just beaten
        print(f"\nYou have successfully cleared Floor {cleared_floor}!\n")

        # Full heal already done inside explore_dungeon; save was also called.
        # Re-save here as well in case post-floor logic drifts.
        player["current_hp"] = player_max_hp(player)
        save_game(player)

        # Post‑floor menu
        while True:
            clear_screen()
            print(f"=== FLOOR {cleared_floor} CLEARED ===")
            print(f"Now entering Floor {city_prog['floor']}")
            print(f"HP: {player['current_hp']}/{player_max_hp(player)}")
            print(f"Gold: {player.get('gold', 0)}")
            print(f"Time: {format_time(player.get('time_minutes', 480))}\n")
            print("1. Continue to next floor")
            print("2. Return to city")
            print("3. Save and return to main menu")
            choice = input("Choice: ").strip()

            if choice == '1':
                # Proceed to next floor
                player["location"] = "dungeon"
                break

            elif choice == '2':
                # Go back to the city this dungeon belongs to
                city_id = player.get("origin_city") or player.get("location")
                if city_id in (None, "dungeon"):
                    city_id = "solmere"
                player["location"] = city_id
                city_result = visit_city(player, city_id)
                if city_result == "save_exit":
                    return   # player saved & quit from within city
                if city_result == "dead":
                    if not handle_player_death(player):
                        return  # Quit to main menu
                    break
                break

            elif choice == '3':
                save_game(player)
                print("Game saved. Returning to menu.")
                return

            else:
                print("Invalid choice. Please enter 1, 2, or 3.")
                input("Press Enter...")


if __name__ == "__main__":
    main_menu()