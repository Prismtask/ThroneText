from character import create_character, player_max_hp
from dungeon import explore_dungeon
from save_load import list_saves, load_game, save_game, delete_save  # Added delete_save
from city import visit_city
from resources.cities import CITIES
from utils import clear_screen, format_time

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
            print(f"Dungeon Floor: {player['floor']}  HP: {player['current_hp']}/{player_max_hp_display(player)}")
            print(f"Time: {format_time(player.get('time_minutes', 480))}")
            print(f"Location: {player.get('location', 'dungeon')}")
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
            if not visit_city(player, city_id):
                return  # Saved and quit
            if player.get("location") == city_id:
                player["location"] = "dungeon"
            continue

        # === Enter Dungeon ===
        result = explore_dungeon(player)

        if result == "save_exit":
            print("Game saved. Returning to menu.")
            break

        if not result:  # Player died
            input("Press Enter to return to main menu...")
            break

        # Floor cleared
        print(f"\nYou have successfully cleared Floor {player['floor']}!\n")
        player["floor"] += 1
        if player["floor"] > player["max_floor"]:
            player["max_floor"] = player["floor"]
        player["current_hp"] = player_max_hp(player)   # full heal after floor
        save_game(player)                              # auto-save floor progress

        # Post‑floor menu
        while True:
            clear_screen()
            print(f"=== FLOOR {player['floor'] - 1} CLEARED ===")
            print(f"Now entering Floor {player['floor']}")
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
                # Go to city
                city_id = player.get("location") if player.get("location") not in ["dungeon", None] else "solmere"
                player["location"] = city_id
                if not visit_city(player, city_id):
                    return   # player saved & quit from within city
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