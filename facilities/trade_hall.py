# facilities/trade_hall.py
"""
Trade Hall service.

Sells:
  1. Trade Permit   (200 gold, one-time, global) — unlocks special trades.
  2. House Deed     (500 gold, per city)          — lets the player own a house
                                                    in ANY city they choose.
  3. Mount / Stable / Caravan — buy, upgrade, or downgrade overland transport.
  4. Sell bulk goods (placeholder, 50 gold).

House placement rules
─────────────────────
  • The player picks which city to register the deed in from a numbered list.
  • Certain locations are excluded (isle_of_glass — no permanent residents;
    blackwake — no legal property ownership).
  • One house per city; the player can own houses in multiple cities.

Mount rules
───────────
  • Only one mount at a time.
  • Upgrade = pay the difference in cost between tiers.
  • Downgrade = receive half the difference back, get the lower-tier mount.
  • Sell = remove mount entirely, receive half its purchase cost.
  • Mounts only affect overland travel (land routes), not sea voyages.
"""

from utils import advance_time
from city_dialogue import service_dialogue
from resources.cities import CITIES
from resources.mounts import (
    MOUNTS,
    get_mount,
    get_mount_by_tier,
    sell_value,
    upgrade_cost,
    downgrade_refund,
)

# Cities where property ownership isn't possible / doesn't make sense.
_DEED_EXCLUDED = {"isle_of_glass", "blackwake"}

HOUSE_DEED_COST    = 500
TRADE_PERMIT_COST  = 200
BULK_SELL_REWARD   = 50


# ═══════════════════════════════════════════════════════════════
# HOUSE DEED
# ═══════════════════════════════════════════════════════════════

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


# ═══════════════════════════════════════════════════════════════
# MOUNT / STABLE / CARAVAN
# ═══════════════════════════════════════════════════════════════

def _mount_info_line(mount_id):
    """One-line summary of a mount's stats."""
    m = get_mount(mount_id)
    if not m:
        return ""
    return (f"{m['name']}  —  {int(m['time_reduction']*100)}% faster, "
            f"{int(m['event_mitigation']*100)}% safer  ({m['cost']}g)")


def _buy_mount(player, mount_id):
    """Purchase a mount outright (player currently has none)."""
    mount = get_mount(mount_id)
    if not mount:
        return

    cost = mount["cost"]
    if player.get("gold", 0) < cost:
        print(f"You need {cost}g for a {mount['name']}. You only have {player.get('gold', 0)}g.")
        input("\nPress Enter...")
        return

    print(f"\nPurchase a {mount['name']} for {cost}g?")
    print(f"  Travel: {int(mount['time_reduction']*100)}% faster")
    print(f"  Safety: {int(mount['event_mitigation']*100)}% fewer road events")
    confirm = input("Proceed? (y/n): ").strip().lower()
    if confirm != "y":
        print("Purchase cancelled.")
        input("\nPress Enter...")
        return

    player["gold"] -= cost
    player["mount_id"] = mount_id
    print(f"\nYou acquire a {mount['name']}. Road journeys will be smoother.")
    print(f"  Remaining gold: {player['gold']}")
    input("\nPress Enter...")


def _upgrade_mount(player):
    """Trade current mount + gold difference for the next tier."""
    current_id = player.get("mount_id")
    current = get_mount(current_id)
    if not current:
        print("You don't own a mount to upgrade.")
        input("\nPress Enter...")
        return

    next_id, next_mount = get_mount_by_tier(current["tier"] + 1)
    if not next_mount:
        print(f"Your {current['name']} is already the finest beast on the road.")
        input("\nPress Enter...")
        return

    cost = upgrade_cost(current_id, next_id)
    if player.get("gold", 0) < cost:
        print(f"Upgrading to a {next_mount['name']} costs an additional {cost}g.")
        print(f"You only have {player.get('gold', 0)}g.")
        input("\nPress Enter...")
        return

    print(f"\nUpgrade your {current['name']} to a {next_mount['name']}?")
    print(f"  Additional cost: {cost}g")
    print(f"  Travel: {int(next_mount['time_reduction']*100)}% faster (was {int(current['time_reduction']*100)}%)")
    print(f"  Safety: {int(next_mount['event_mitigation']*100)}% safer (was {int(current['event_mitigation']*100)}%)")
    confirm = input("Proceed? (y/n): ").strip().lower()
    if confirm != "y":
        print("Upgrade cancelled.")
        input("\nPress Enter...")
        return

    player["gold"] -= cost
    player["mount_id"] = next_id
    print(f"\nYou now ride a {next_mount['name']}. The road fears you.")
    print(f"  Remaining gold: {player['gold']}")
    input("\nPress Enter...")


def _downgrade_mount(player):
    """Trade current mount down to previous tier, receive a partial refund."""
    current_id = player.get("mount_id")
    current = get_mount(current_id)
    if not current:
        print("You don't own a mount to downgrade.")
        input("\nPress Enter...")
        return

    prev_id, prev_mount = get_mount_by_tier(current["tier"] - 1)
    if not prev_mount:
        print(f"A {current['name']} is the lowest tier. You cannot downgrade further.")
        print("Use 'Sell mount' if you wish to part with it entirely.")
        input("\nPress Enter...")
        return

    refund = downgrade_refund(current_id, prev_id)
    print(f"\nDowngrade your {current['name']} to a {prev_mount['name']}?")
    print(f"  Refund: {refund}g")
    print(f"  Travel: {int(prev_mount['time_reduction']*100)}% faster (was {int(current['time_reduction']*100)}%)")
    print(f"  Safety: {int(prev_mount['event_mitigation']*100)}% safer (was {int(current['event_mitigation']*100)}%)")
    confirm = input("Proceed? (y/n): ").strip().lower()
    if confirm != "y":
        print("Downgrade cancelled.")
        input("\nPress Enter...")
        return

    player["gold"] += refund
    player["mount_id"] = prev_id
    print(f"\nYou trade your {current['name']} for a {prev_mount['name']}.")
    print(f"  Received: {refund}g  |  Remaining gold: {player['gold']}")
    input("\nPress Enter...")


def _sell_mount(player):
    """Sell the current mount for half its purchase cost."""
    current_id = player.get("mount_id")
    current = get_mount(current_id)
    if not current:
        print("You have no mount to sell.")
        input("\nPress Enter...")
        return

    refund = sell_value(current_id)
    print(f"\nSell your {current['name']} for {refund}g?")
    confirm = input("Proceed? (y/n): ").strip().lower()
    if confirm != "y":
        print("Sale cancelled.")
        input("\nPress Enter...")
        return

    player["gold"] += refund
    player["mount_id"] = None
    print(f"\nYou part with your {current['name']} for {refund}g.")
    print(f"  Remaining gold: {player['gold']}")
    input("\nPress Enter...")


def _mount_menu(player):
    """Sub-menu for stable / mount transactions."""
    while True:
        print("\n=== Stable & Caravan ===")
        current_id = player.get("mount_id")

        if current_id:
            current = get_mount(current_id)
            print(f"Current mount: {_mount_info_line(current_id)}")
            print()
            print("1. Upgrade mount")
            print("2. Downgrade mount")
            print("3. Sell mount")
            print("4. Back")
        else:
            print("You have no mount. The stable-master shows you what is available.")
            print()
            # Show all mounts for purchase
            opts = []
            for mid, data in sorted(MOUNTS.items(), key=lambda x: x[1]["tier"]):
                opts.append(mid)
                print(f"{len(opts)}. Buy {_mount_info_line(mid)}")
            print(f"{len(opts)+1}. Back")

        choice = input("\nChoice: ").strip()

        if current_id:
            if choice == "1":
                _upgrade_mount(player)
                return
            elif choice == "2":
                _downgrade_mount(player)
                return
            elif choice == "3":
                _sell_mount(player)
                return
            elif choice == "4":
                return
            else:
                print("Invalid choice.")
        else:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(opts):
                    _buy_mount(player, opts[idx])
                    return
                elif idx == len(opts):
                    return
                else:
                    print("Invalid choice.")
            except ValueError:
                print("Invalid choice.")


# ═══════════════════════════════════════════════════════════════
# MAIN TRADE HALL SERVICE
# ═══════════════════════════════════════════════════════════════

def trade_hall_service(player, city_id):
    """Trade hall: exchange goods, get trade permits, or manage mounts."""
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

        # Option 3: Mount / Stable
        mount_id = player.get("mount_id")
        if mount_id:
            m = get_mount(mount_id)
            mount_label = f"Stable / Caravan — current: {m['name']}"
        else:
            mount_label = "Stable / Caravan — buy a mount"
        print(f"3. {mount_label}")

        print(f"4. Sell bulk goods — {BULK_SELL_REWARD} gold")
        print("5. Leave")

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
            _mount_menu(player)

        elif choice == "4":
            player["gold"] = player.get("gold", 0) + BULK_SELL_REWARD
            print(f"The merchants offer {BULK_SELL_REWARD} gold for your spare goods.")
            print(f"  Gold: {player['gold']}")
            input("\nPress Enter...")

        elif choice == "5":
            service_dialogue(city_id, "trade_hall", "leave")
            break

        else:
            print("Invalid choice.")

    advance_time(player, 30)
