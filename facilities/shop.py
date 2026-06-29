# facilities/shop.py
import random
from resources.items import ITEMS, build_item, ITEM_RARITY
from resources.cities import CITIES
from utils import clear_screen, advance_time, format_time
from inventory import add_item_to_inventory, get_total_equipment_mods, get_inventory_caps, count_inventory, get_sorted_equipment, get_sorted_items
from combat.stats import get_effective_attribute
from inventory_ui import display_player_status
from city_dialogue import service_dialogue   # changed import
from facilities.travel_events import _item_stat_line

def get_effective_charisma(player):
    return get_effective_attribute(player, "Charisma")

def get_discounted_price(base_price, player, city_id):
    charisma = get_effective_charisma(player)
    favor = player.get("favor", {}).get(city_id, 0)
    
    # Max 40% from Charisma, Max 30% from Favor, Max Total 70%
    discount_percent = min(40, max(0, (charisma - 8) * 0.5))
    favor_discount = min(30, favor * 0.5) 
    total_discount = min(70, discount_percent + favor_discount)
    
    discounted = int(base_price * (100 - total_discount) / 100)
    return max(1, discounted)


def _sell_price(item, player):
    rarity_mult = ITEM_RARITY.get(item.get("rarity", "common"), {}).get("price_mult", 1.0)
    base = int(12 * rarity_mult)
    charisma = get_effective_charisma(player)
    return int(base * (1 + (charisma - 8) / 100))


def sell_items(player):
    from inventory import remove_item_by_reference
    inv = player.get("inventory", [])
    if not inv:
        print("No items to sell.")
        return
    print("\nYour inventory:")
    sorted_equip = get_sorted_equipment(player)
    sorted_items = get_sorted_items(player)
    all_items = sorted_equip + sorted_items
    for i, item in enumerate(all_items):
        unit_price = _sell_price(item, player)
        count = item.get("count", 1)
        stack_price = unit_price * count
        tag = f"[{item.get('rarity','common')}]"
        count_str = f" (x{count})" if count > 1 else ""
        if item.get("type") == "equipment":
            stat = _item_stat_line(item)
            print(f"{i+1}. {item['name']}{count_str} ({item['slot']}) {stat} {tag} — {stack_price} gold")
        else:
            print(f"{i+1}. {item['name']}{count_str} ({item['type']}) {tag} — {stack_price} gold")
    print("\nEnter numbers to sell (e.g. '1 3 5', '1-4', or 'all'). 0 to cancel.")
    raw = input("Sell which items? ").strip().lower()
    if raw in ("", "0", "cancel"):
        print("Cancelled.")
        return

    indices = set()
    if raw == "all":
        indices = set(range(len(all_items)))
    else:
        for part in raw.split():
            if "-" in part:
                try:
                    a, b = part.split("-", 1)
                    indices.update(range(int(a) - 1, int(b)))
                except ValueError:
                    pass
            else:
                try:
                    indices.add(int(part) - 1)
                except ValueError:
                    pass

    indices = sorted([i for i in indices if 0 <= i < len(all_items)], reverse=True)
    if not indices:
        print("No valid items selected.")
        return

    from combat.wedding_specials import is_wedding_item_soulbound
    # Filter out soulbound wedding items
    filtered_indices = []
    filtered_names = []
    for i in indices:
        item = all_items[i]
        if is_wedding_item_soulbound(item):
            print(f"  - {item['name']} [SOULBOUND — cannot be sold]")
        else:
            filtered_indices.append(i)
            filtered_names.append(item['name'])
    
    if not filtered_indices:
        print("\nNo valid items to sell (all selected items are soulbound).")
        return

    total_gold = sum(_sell_price(all_items[i], player) * all_items[i].get("count", 1) for i in filtered_indices)
    print(f"\nYou will sell {len(filtered_indices)} item stack(s) for {total_gold} gold:")
    for n in filtered_names:
        print(f"  - {n}")
    confirm = input("Confirm? (y/n): ").strip().lower()
    if confirm != "y":
        print("Cancelled.")
        return

    for i in filtered_indices:
        item = all_items[i]
        remove_item_by_reference(player, item, item.get("count", 1))

    player["gold"] = player.get("gold", 0) + total_gold
    print(f"Sold {len(filtered_indices)} item stack(s) for {total_gold} gold.")


def upgrade_backpack(player):
    """Upgrade inventory capacity at the shop."""
    upgrade = player.get("inventory_upgrade", 0)
    cost = 200 * (2 ** upgrade)
    equip_cap, other_cap = get_inventory_caps(player)
    next_equip = 10 + (upgrade + 1) * 5
    next_other = 20 + (upgrade + 1) * 10 + len(player.get("allies", [])) * 5
    print(f"\n=== Backpack Upgrade (Level {upgrade}) ===")
    print(f"Current capacity: {equip_cap} equipment, {other_cap} other items")
    print(f"Next level: {next_equip} equipment, {next_other} other items")
    print(f"Cost: {cost} gold")
    print(f"Your gold: {player.get('gold', 0)}")
    confirm = input("Upgrade? (y/n): ").strip().lower()
    if confirm != "y":
        print("Upgrade cancelled.")
        return
    if player.get("gold", 0) < cost:
        print("Not enough gold.")
        return
    player["gold"] -= cost
    player["inventory_upgrade"] = upgrade + 1
    print(f"Backpack upgraded to level {upgrade + 1}!")


def city_shop(player, city_id="solmere"):
    clear_screen()
    service_dialogue(city_id, "shop", "enter")   # changed
    city = CITIES.get(city_id, CITIES["solmere"])
    shop_config = city["shop"]
    stock_key = f"shop_stock_{city_id}"
    day_key = f"last_shop_day_{city_id}"
    if stock_key not in player or player.get(day_key) != player.get("day", 1):
        player[stock_key] = []
        stock_size = shop_config.get("stock_size", 8)
        
        # Filter out unique items so they don't randomly show up in the shop stock
        available_item_ids = [k for k, v in ITEMS.items() if not v.get("unique")]
        
        for _ in range(stock_size):
            item_id = random.choice(available_item_ids)
            if shop_config.get("rarity_bias") == "higher":
                rarity = random.choices(["common", "uncommon", "rare", "epic"], weights=[30, 35, 25, 10])[0]
            else:
                rarity = random.choices(["common", "uncommon", "rare", "epic"], weights=[40, 35, 20, 5])[0]
            item = build_item(item_id, rarity)
            base_price = shop_config.get("base_price_consumable" if item["type"] == "consumable" else "base_price_other", 45)
            base_price = int(base_price * ITEM_RARITY[rarity]["price_mult"])
            player[stock_key].append((item, base_price))
        player[day_key] = player.get("day", 1)
    shop_stock = player[stock_key]

    def show_shop():
        clear_screen()
        service_dialogue(city_id, "shop", "enter")
        equip_cap, other_cap = get_inventory_caps(player)
        equip_count, other_count = count_inventory(player)
        print(f"=== {city['name'].upper()} MARKET ===")
        print(f"Time: {format_time(player['time_minutes'])} | Gold: {player.get('gold', 0)}")
        print(f"Inventory: {equip_count}/{equip_cap} equipment | {other_count}/{other_cap} items")
        
        # Display favor and total discount
        favor = player.get('favor', {}).get(city_id, 0)
        c_disc = min(40, max(0, (get_effective_charisma(player) - 8) * 0.5))
        f_disc = min(30, favor * 0.5)
        total_disc = min(70, c_disc + f_disc)
        
        print(f"Charisma & Favor ({favor}): → {100 - total_disc:.0f}% of base price (max 70%)\n")
        print("--- Shop Stock ---")
        for i, (item, base_price) in enumerate(shop_stock, 1):
            final_price = get_discounted_price(base_price, player, city_id)  # Pass city_id here!
            stat = _item_stat_line(item)
            print(f"{i}. {item['name']}  {stat} — {final_price} gold (base: {base_price})")
        print("\nOptions:")
        print("1) Buy   2) Sell   3) Upgrade Backpack   4) View Stats   5) Back to City")

    while True:
        show_shop()
        choice = input("\nChoice: ").strip().lower()
        if choice == "1":
            try:
                idx = int(input("Buy which item? (number): ")) - 1
                if 0 <= idx < len(shop_stock):
                    item, base_price = shop_stock[idx]
                    final_price = get_discounted_price(base_price, player, city_id)
                    if player.get("gold", 0) >= final_price:
                        # Check inventory capacity before buying
                        equip_cap, other_cap = get_inventory_caps(player)
                        equip_count, other_count = count_inventory(player)
                        if item["type"] == "equipment" and equip_count >= equip_cap:
                            print("Your equipment bag is full! Upgrade your backpack or store items.")
                            input("\nPress Enter to continue...")
                            continue
                        if item["type"] != "equipment" and other_count >= other_cap:
                            print("Your item bag is full! Upgrade your backpack or store items.")
                            input("\nPress Enter to continue...")
                            continue
                        player["gold"] -= final_price
                        if add_item_to_inventory(player, item.copy()):
                            del shop_stock[idx]
                            service_dialogue(city_id, "shop", "success")
                            advance_time(player, 15)
                            input("\nPress Enter to continue...")
                        else:
                            print("Could not add item to inventory (full).")
                            input("\nPress Enter to continue...")
                    else:
                        service_dialogue(city_id, "shop", "fail")
                        advance_time(player, 10)
                        input("\nPress Enter to continue...")
                else:
                    service_dialogue(city_id, "shop", "fail")
                    input("\nPress Enter to continue...")
            except:
                service_dialogue(city_id, "shop", "fail")
                input("\nPress Enter to continue...")
        elif choice == "2":
            sell_items(player)
            advance_time(player, 15)
            input("\nPress Enter to continue...")
        elif choice == "3":
            upgrade_backpack(player)
            advance_time(player, 15)
            input("\nPress Enter to continue...")
        elif choice == "4":
            display_player_status(player)
            advance_time(player, 10)
            input("\nPress Enter to continue...")
        elif choice == "5":
            service_dialogue(city_id, "shop", "leave")
            advance_time(player, 30)
            break
        else:
            service_dialogue(city_id, "shop", "fail")
            advance_time(player, 10)
            input("\nPress Enter to continue...")
