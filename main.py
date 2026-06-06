from character import create_character
from dungeon import explore_dungeon
from save_load import list_saves, load_game, save_game
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
        print("3. Quit")
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

        elif choice == "3":
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
            elif player.get("location") != "dungeon":
                continue 
            elif player.get("location") == "dungeon":
                player["location"] = "dungeon"

        # === Enter Dungeon ===
        result = explore_dungeon(player)

        if result == "save_exit":
            print("Game saved. Returning to menu.")
            break

        if not result:  # Player died
            print("Your adventure has ended...")
            input("Press Enter to return to main menu...")
            break

        # Floor cleared
        print(f"\nYou have successfully cleared Floor {player['floor'] - 1}!\n")

        # === Optional City Visit ===
        while True:
            choice = input("Return to a city to rest and trade? (y/n): ").strip().lower()
            if choice == 'y':
                # Default to last city or solmere
                city_id = player.get("location") if player.get("location") not in ["dungeon", None] else "solmere"
                print(f"\nYou return to {CITIES.get(city_id, CITIES['solmere'])['name']}...")
                player["location"] = city_id
                
                if not visit_city(player, city_id):
                    return  # saved & quit
                
                # Only reset to dungeon if we're still intending to go back
                if player.get("location") == city_id:  # didn't travel away
                    player["location"] = "dungeon"
                # else: we traveled to another city → keep the new location
                
                break
            elif choice == 'n':
                print("You decide to continue deeper into the dungeon.")
                player["location"] = "dungeon"
                break
            else:
                print("Please enter y or n.")

        # Ask to continue to next floor
        while True:
            cont = input("\nContinue to next floor? (y/n): ").strip().lower()
            if cont == 'y':
                break
            elif cont == 'n':
                save_game(player)
                print("Progress saved. You return to the surface.")
                return
            else:
                print("Please enter y or n.")


if __name__ == "__main__":
    main_menu()