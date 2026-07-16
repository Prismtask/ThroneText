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
from gui.terminal import term

# Cities where property ownership isn't possible / doesn't make sense.
_DEED_EXCLUDED = {"isle_of_glass", "blackwake"}

HOUSE_DEED_COST    = 500
TRADE_PERMIT_COST  = 200
BULK_SELL_REWARD   = 50


# ═══════════════════════════════════════════════════════════════
# HOUSE DEED
# ═══════════════════════════════════════════════════════════════

def _sell_house_deed(player):
    """Walk the player through buying and placing a house deed.
    
    If the player already owns a house, buying a new deed moves the existing
    house (with all its data: level, storage, monster girls, income timing)
    to the newly chosen city instead of creating a second house.
    """
    if player.get("gold", 0) < HOUSE_DEED_COST:
        term.print(f"A House Deed costs {HOUSE_DEED_COST} gold. You don't have enough.")
        term.pause()
        return

    player.setdefault("houses", {})
    houses = player.get("houses", {})

    # Determine if the player already has a house (and where).
    existing_city_id = None
    existing_house = None
    if houses:
        # There should only be one, but grab the first just in case.
        existing_city_id = next(iter(houses))
        existing_house = houses[existing_city_id]

    if existing_house:
        old_city_name = CITIES.get(existing_city_id, {}).get("name", existing_city_id)
        from facilities.house import HOUSE_LEVELS
        old_level_name = HOUSE_LEVELS.get(existing_house.get("level", 1), {}).get("name", "Hovel")
        term.print(f"\nYou already own a {old_level_name} in {old_city_name}.")
        term.print(f"Buying a new deed will MOVE your house to the new city")
        term.print(f"(keeping its level, storage, and residents).")

    # Build the list of cities where the player can place a deed.
    eligible = [
        (city_id, data)
        for city_id, data in CITIES.items()
        if city_id not in _DEED_EXCLUDED
        and city_id != existing_city_id  # Don't show the city the house is already in
    ]

    if not eligible:
        term.print("No other cities are available to move your house to.")
        term.pause()
        return

    if existing_house:
        term.print("\n=== Choose a City to Move Your House To ===")
    else:
        term.print("\n=== Choose a City for Your New Home ===")
    term.print("(You may only own one house. It will be your home anywhere in the world.)\n")

    options = [data['name'] for _, data in eligible]

    prompt = "Choose city to move your house to:" if existing_house else "Choose city for your new home:"
    choice = term.menu(options, prompt=prompt, allow_cancel=True)

    if choice < 0:
        term.print("Purchase cancelled.")
        term.pause()
        return

    chosen_id, chosen_data = eligible[choice]

    # Confirm purchase / move.
    if existing_house:
        term.print(f"\nMove your {old_level_name} from {old_city_name} to {chosen_data['name']}?")
    else:
        term.print(f"\nPurchase a house deed for {chosen_data['name']}?")
    term.print(f"  Cost: {HOUSE_DEED_COST} gold  (current: {player.get('gold', 0)})")

    if not term.confirm("Proceed?"):
        term.print("Purchase cancelled.")
        term.pause()
        return

    # Complete purchase / move.
    player["gold"] -= HOUSE_DEED_COST

    if existing_house:
        # Move the existing house to the new city, preserving all data.
        player["houses"][chosen_id] = existing_house
        del player["houses"][existing_city_id]
        level_name = HOUSE_LEVELS.get(existing_house.get("level", 1), {}).get("name", "Hovel")
        term.print(f"\nYour {level_name} has been moved from {old_city_name} to {chosen_data['name']}!")
    else:
        player["houses"][chosen_id] = {
            "level":           1,
            "storage":         [],
            "last_income_day": player.get("day", 1),
        }
        term.print(f"\nCongratulations! You now own a Hovel in {chosen_data['name']}.")

    term.print("Visit that city and choose 'Your House' from the city menu.")
    term.print(f"  Remaining gold: {player['gold']}")
    term.pause()


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
        term.print(f"You need {cost}g for a {mount['name']}. You only have {player.get('gold', 0)}g.")
        term.pause()
        return

    term.print(f"\nPurchase a {mount['name']} for {cost}g?")
    term.print(f"  Travel: {int(mount['time_reduction']*100)}% faster")
    term.print(f"  Safety: {int(mount['event_mitigation']*100)}% fewer road events")
    if not term.confirm("Proceed?"):
        term.print("Purchase cancelled.")
        term.pause()
        return

    player["gold"] -= cost
    player["mount_id"] = mount_id
    term.print(f"\nYou acquire a {mount['name']}. Road journeys will be smoother.")
    term.print(f"  Remaining gold: {player['gold']}")
    term.pause()


def _upgrade_mount(player):
    """Trade current mount + gold difference for the next tier."""
    current_id = player.get("mount_id")
    current = get_mount(current_id)
    if not current:
        term.print("You don't own a mount to upgrade.")
        term.pause()
        return

    next_id, next_mount = get_mount_by_tier(current["tier"] + 1)
    if not next_mount:
        term.print(f"Your {current['name']} is already the finest beast on the road.")
        term.pause()
        return

    cost = upgrade_cost(current_id, next_id)
    if player.get("gold", 0) < cost:
        term.print(f"Upgrading to a {next_mount['name']} costs an additional {cost}g.")
        term.print(f"You only have {player.get('gold', 0)}g.")
        term.pause()
        return

    term.print(f"\nUpgrade your {current['name']} to a {next_mount['name']}?")
    term.print(f"  Additional cost: {cost}g")
    term.print(f"  Travel: {int(next_mount['time_reduction']*100)}% faster (was {int(current['time_reduction']*100)}%)")
    term.print(f"  Safety: {int(next_mount['event_mitigation']*100)}% safer (was {int(current['event_mitigation']*100)}%)")
    if not term.confirm("Proceed?"):
        term.print("Upgrade cancelled.")
        term.pause()
        return

    player["gold"] -= cost
    player["mount_id"] = next_id
    term.print(f"\nYou now ride a {next_mount['name']}. The road fears you.")
    term.print(f"  Remaining gold: {player['gold']}")
    term.pause()


def _downgrade_mount(player):
    """Trade current mount down to previous tier, receive a partial refund."""
    current_id = player.get("mount_id")
    current = get_mount(current_id)
    if not current:
        term.print("You don't own a mount to downgrade.")
        term.pause()
        return

    prev_id, prev_mount = get_mount_by_tier(current["tier"] - 1)
    if not prev_mount:
        term.print(f"A {current['name']} is the lowest tier. You cannot downgrade further.")
        term.print("Use 'Sell mount' if you wish to part with it entirely.")
        term.pause()
        return

    refund = downgrade_refund(current_id, prev_id)
    term.print(f"\nDowngrade your {current['name']} to a {prev_mount['name']}?")
    term.print(f"  Refund: {refund}g")
    term.print(f"  Travel: {int(prev_mount['time_reduction']*100)}% faster (was {int(current['time_reduction']*100)}%)")
    term.print(f"  Safety: {int(prev_mount['event_mitigation']*100)}% safer (was {int(current['event_mitigation']*100)}%)")
    if not term.confirm("Proceed?"):
        term.print("Downgrade cancelled.")
        term.pause()
        return

    player["gold"] += refund
    player["mount_id"] = prev_id
    term.print(f"\nYou trade your {current['name']} for a {prev_mount['name']}.")
    term.print(f"  Received: {refund}g  |  Remaining gold: {player['gold']}")
    term.pause()


def _sell_mount(player):
    """Sell the current mount for half its purchase cost."""
    current_id = player.get("mount_id")
    current = get_mount(current_id)
    if not current:
        term.print("You have no mount to sell.")
        term.pause()
        return

    refund = sell_value(current_id)
    term.print(f"\nSell your {current['name']} for {refund}g?")
    if not term.confirm("Proceed?"):
        term.print("Sale cancelled.")
        term.pause()
        return

    player["gold"] += refund
    player["mount_id"] = None
    term.print(f"\nYou part with your {current['name']} for {refund}g.")
    term.print(f"  Remaining gold: {player['gold']}")
    term.pause()


def _mount_menu(player):
    """Sub-menu for stable / mount transactions."""
    while True:
        current_id = player.get("mount_id")

        if current_id:
            current = get_mount(current_id)
            term.print(f"Current mount: {_mount_info_line(current_id)}")
            choice = term.menu([
                "Upgrade mount",
                "Downgrade mount",
                "Sell mount",
                "Back"
            ], prompt="=== Stable & Caravan ===")
            
            if choice == 0:
                _upgrade_mount(player)
                return
            elif choice == 1:
                _downgrade_mount(player)
                return
            elif choice == 2:
                _sell_mount(player)
                return
            elif choice == 3 or choice == -1:
                return
        else:
            opts = []
            options = []
            for mid, data in sorted(MOUNTS.items(), key=lambda x: x[1]["tier"]):
                opts.append(mid)
                options.append(f"Buy {_mount_info_line(mid)}")
            
            choice = term.menu(options, prompt="You have no mount. The stable-master shows you what is available:", allow_cancel=True)
            
            if 0 <= choice < len(opts):
                _buy_mount(player, opts[choice])
                return
            elif choice == -1:
                return


# ═══════════════════════════════════════════════════════════════
# MAIN TRADE HALL SERVICE
# ═══════════════════════════════════════════════════════════════

def trade_hall_service(player, city_id):
    """Trade hall: exchange goods, get trade permits, or manage mounts."""
    service_dialogue(city_id, "trade_hall", "enter")

    while True:
        # Option 1: Trade Permit
        permit_label = (
            "Trade permit — already owned"
            if player.get("trade_permit")
            else f"Buy trade permit ({TRADE_PERMIT_COST} gold) — WIP"
        )

        # Option 2: House Deed
        houses_owned = len(player.get("houses", {}))
        deed_label = (
            f"Buy house deed ({HOUSE_DEED_COST} gold) — place a home in any city"
            + (f"  [You own {houses_owned} house(s)]" if houses_owned else "")
        )

        # Option 3: Mount / Stable
        mount_id = player.get("mount_id")
        if mount_id:
            m = get_mount(mount_id)
            mount_label = f"Stable / Caravan — current: {m['name']}"
        else:
            mount_label = "Stable / Caravan — buy a mount"

        options = [
            permit_label,
            deed_label,
            mount_label,
            f"Sell bulk goods — {BULK_SELL_REWARD} gold",
            "Leave"
        ]
        
        choice = term.menu(options, prompt="You browse trade ledgers and exotic goods.")

        if choice == 0:
            if player.get("trade_permit"):
                term.print("You already hold a trade permit.")
            elif player.get("gold", 0) >= TRADE_PERMIT_COST:
                player["gold"] -= TRADE_PERMIT_COST
                player["trade_permit"] = True
                term.print("You obtain a trade permit. New opportunities await.")
                service_dialogue(city_id, "trade_hall", "success")
            else:
                term.print("Insufficient gold.")
            term.pause()

        elif choice == 1:
            _sell_house_deed(player)

        elif choice == 2:
            _mount_menu(player)

        elif choice == 3:
            player["gold"] = player.get("gold", 0) + BULK_SELL_REWARD
            term.print(f"The merchants offer {BULK_SELL_REWARD} gold for your spare goods.")
            term.print(f"  Gold: {player['gold']}")
            term.pause()

        elif choice == 4 or choice == -1:
            service_dialogue(city_id, "trade_hall", "leave")
            break

    advance_time(player, 30)
