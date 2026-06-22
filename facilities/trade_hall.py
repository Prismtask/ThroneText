# facilities/trade_hall.py
"""
Trade Hall service.

Sells:
  1. Trade Permit   (200 gold, one-time, global) — unlocks special trades.
  2. House Deed     (500 gold, per city)          — lets the player own a house
                                                    in ANY city they choose.
  3. Sell bulk goods (placeholder, 50 gold).

House placement rules
─────────────────────
  • The player picks which city to register the deed in from a numbered list.
  • Certain locations are excluded (isle_of_glass — no permanent residents;
    blackwake — no legal property ownership).
  • One house per city; the player can own houses in multiple cities.
"""

from utils import advance_time
from city_dialogue import service_dialogue
from resources.cities import CITIES

# Cities where property ownership isn't possible / doesn't make sense.
_DEED_EXCLUDED = {"isle_of_glass", "blackwake"}

HOUSE_DEED_COST    = 500
TRADE_PERMIT_COST  = 200
BULK_SELL_REWARD   = 50


def _sell_house_deed(player):
    """Walk the player through buying and placing a house deed."""
    if player.get("gold", 0) < HOUSE_DEED_COST:
        print(f"A House Deed costs {HOUSE_DEED_COST} gold. You don't have enough.")
        input("\nPress Enter...")
        return

    player.setdefault("houses", {})

    if len(player.get("houses", {})) >= 1:
        print("You already own a house. You may only have one house.")
        input("\nPress Enter...")
        return

    # Build the list of cities where the player can place a deed.
    eligible = [
        (city_id, data)
        for city_id, data in CITIES.items()
        if city_id not in _DEED_EXCLUDED
    ]

    print("\n=== Choose a City for Your New Home ===")
    print("(You may only own one house. It will be your home anywhere in the world.)\n")

    for i, (city_id, data) in enumerate(eligible, 1):
        owned = "✓ Owned" if city_id in player["houses"] else ""
        print(f"  {i:2}. {data['name']:<20} {owned}")

    print(f"\n  0. Cancel")

    while True:
        try:
            raw = input("\nChoose city number: ").strip()
            if raw == "0":
                print("Purchase cancelled.")
                input("\nPress Enter...")
                return
            idx = int(raw) - 1
            if not (0 <= idx < len(eligible)):
                print("Invalid choice.")
                continue
            chosen_id, chosen_data = eligible[idx]
            break
        except ValueError:
            print("Please enter a number.")

    if chosen_id in player["houses"]:
        print(f"You already own a house in {chosen_data['name']}.")
        input("\nPress Enter...")
        return

    # Confirm purchase.
    print(f"\nPurchase a house deed for {chosen_data['name']}?")
    print(f"  Cost: {HOUSE_DEED_COST} gold  (current: {player.get('gold', 0)})")
    confirm = input("Proceed? (y/n): ").strip().lower()
    if confirm != "y":
        print("Purchase cancelled.")
        input("\nPress Enter...")
        return

    # Complete purchase.
    player["gold"] -= HOUSE_DEED_COST
    player["houses"][chosen_id] = {
        "level":           1,
        "storage":         [],
        "last_income_day": player.get("day", 1),
    }
    print(f"\nCongratulations! You now own a Hovel in {chosen_data['name']}.")
    print("Visit that city and choose 'Your House' from the city menu.")
    print(f"  Remaining gold: {player['gold']}")
    input("\nPress Enter...")


def trade_hall_service(player, city_id):
    """Trade hall: exchange goods or get trade permits."""
    service_dialogue(city_id, "trade_hall", "enter")
    print("You browse trade ledgers and exotic goods.")

    while True:
        print()
        # Option 1: Trade Permit
        permit_label = (
            "Trade permit — already owned"
            if player.get("trade_permit")
            else f"Buy trade permit ({TRADE_PERMIT_COST} gold) — unlocks special trades"
        )
        print(f"1. {permit_label}")

        # Option 2: House Deed
        houses_owned = len(player.get("houses", {}))
        deed_label = (
            f"Buy house deed ({HOUSE_DEED_COST} gold) — place a home in any city"
            + (f"  [You own {houses_owned} house(s)]" if houses_owned else "")
        )
        print(f"2. {deed_label}")

        print(f"3. Sell bulk goods — {BULK_SELL_REWARD} gold")
        print("4. Leave")

        choice = input("\nChoice: ").strip()

        if choice == "1":
            if player.get("trade_permit"):
                print("You already hold a trade permit.")
            elif player.get("gold", 0) >= TRADE_PERMIT_COST:
                player["gold"] -= TRADE_PERMIT_COST
                player["trade_permit"] = True
                print("You obtain a trade permit. New opportunities await.")
                service_dialogue(city_id, "trade_hall", "success")
            else:
                print("Insufficient gold.")
            input("\nPress Enter...")

        elif choice == "2":
            _sell_house_deed(player)

        elif choice == "3":
            player["gold"] = player.get("gold", 0) + BULK_SELL_REWARD
            print(f"The merchants offer {BULK_SELL_REWARD} gold for your spare goods.")
            print(f"  Gold: {player['gold']}")
            input("\nPress Enter...")

        elif choice == "4":
            service_dialogue(city_id, "trade_hall", "leave")
            break

        else:
            print("Invalid choice.")

    advance_time(player, 30)