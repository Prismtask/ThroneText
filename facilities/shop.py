# facilities/shop.py
import random
from resources.items import ITEMS, build_item, ITEM_RARITY
from resources.cities import CITIES
from utils import clear_screen, advance_time, format_time
from inventory import add_item_to_inventory, get_total_equipment_mods
from combat.stats import get_effective_attribute
from inventory_ui import display_player_status
from city_dialogue import service_dialogue   # changed import

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

def sell_items(player):
    inv = player.get("inventory", [])
    if not inv:
        print("No items to sell.")
        return
    print("\nYour inventory:")
    for i, item in enumerate(inv):
        rarity_mult = ITEM_RARITY.get(item.get("rarity", "common"))["price_mult"]
        sell_price = int(12 * rarity_mult)
        charisma = get_effective_charisma(player)
        sell_price = int(sell_price * (1 + (charisma - 8) / 100))
        print(f"{i+1}. {item['name']} - {sell_price} gold")
    try:
        idx = int(input("\nSell which item? (0 to cancel): ")) - 1
        if 0 <= idx < len(inv):
            item = inv.pop(idx)
            rarity_mult = ITEM_RARITY.get(item.get("rarity", "common"))["price_mult"]
            gold = int(12 * rarity_mult)
            player["gold"] += gold
            print(f"Sold {item['name']} for {gold} gold.")
    except:
        print("Cancelled.")

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
        print(f"=== {city['name'].upper()} MARKET ===")
        print(f"Time: {format_time(player['time_minutes'])} | Gold: {player.get('gold', 0)}")
        
        # Display favor and total discount
        favor = player.get('favor', {}).get(city_id, 0)
        c_disc = min(40, max(0, (get_effective_charisma(player) - 8) * 0.5))
        f_disc = min(30, favor * 0.5)
        total_disc = min(70, c_disc + f_disc)
        
        print(f"Charisma & Favor ({favor}): → {100 - total_disc:.0f}% of base price (max 70%)\n")
        print("--- Shop Stock ---")
        for i, (item, base_price) in enumerate(shop_stock, 1):
            final_price = get_discounted_price(base_price, player, city_id)  # Pass city_id here!
            print(f"{i}. {item['name']} - {final_price} gold (base: {base_price})")
        print("\nOptions:")
        print("1) Buy   2) Sell   3) View Stats   4) Back to City")

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
                        player["gold"] -= final_price
                        add_item_to_inventory(player, item.copy())
                        del shop_stock[idx]
                        service_dialogue(city_id, "shop", "success")
                        advance_time(player, 15)
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
            display_player_status(player)
            advance_time(player, 10)
            input("\nPress Enter to continue...")
        elif choice == "4":
            service_dialogue(city_id, "shop", "leave")
            advance_time(player, 30)
            break
        else:
            service_dialogue(city_id, "shop", "fail")
            advance_time(player, 10)
            input("\nPress Enter to continue...")