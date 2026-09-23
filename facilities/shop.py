# facilities/shop.py
import random
from resources.items import ITEMS, build_item, ITEM_RARITY
from resources.cities import CITIES
from utils import advance_time
from inventory import add_item_to_inventory, get_inventory_caps, count_inventory, get_sorted_equipment, get_sorted_items
from combat.stats import get_effective_attribute
from city_dialogue import service_dialogue   # changed import
from facilities.travel_events import _item_stat_line
from gui.terminal import term

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
    # Daily events: Month-End Festival — extra 20% off everything
    event_discount = player.get("daily_effects", {}).get("shop_discount", 0.0)
    if event_discount:
        discounted = int(round(discounted * (1.0 - event_discount)))
    # Daily events: Tax Day — the crown takes its cut on all goods
    surcharge = player.get("daily_effects", {}).get("shop_surcharge", 0.0)
    if surcharge:
        discounted = int(round(discounted * (1.0 + surcharge)))
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
        term.print("No items to sell.")
        return
    term.print("\nYour inventory:")
    sorted_equip = get_sorted_equipment(player)
    sorted_items = get_sorted_items(player)
    all_items = sorted_equip + sorted_items
    # Filter out key items and crafting materials (cannot be sold)
    all_items = [i for i in all_items if i.get("type") not in ("key_item", "crafting_material")]
    if not all_items:
        term.print("No sellable items.")
        return
    for i, item in enumerate(all_items):
        unit_price = _sell_price(item, player)
        count = item.get("count", 1)
        stack_price = unit_price * count
        tag = f"[{item.get('rarity','common')}]"
        count_str = f" (x{count})" if count > 1 else ""
        if item.get("type") == "equipment":
            stat = _item_stat_line(item)
            term.print(f"{i+1}. {item['name']}{count_str} ({item['slot']}) {stat} {tag} — {stack_price} gold")
        else:
            term.print(f"{i+1}. {item['name']}{count_str} ({item['type']}) {tag} — {stack_price} gold")
    
    raw = term.input("Sell which items? (e.g. '1 3 5', '1-4', or 'all'). 0 to cancel: ").strip().lower()
    if raw in ("", "0", "cancel"):
        term.print("Cancelled.")
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
        term.print("No valid items selected.")
        return

    from combat.weapon.wedding_specials import is_wedding_item_soulbound
    # Filter out soulbound wedding items and unique items
    filtered_indices = []
    filtered_names = []
    for i in indices:
        item = all_items[i]
        if is_wedding_item_soulbound(item):
            term.print(f"  - {item['name']} [SOULBOUND — cannot be sold]")
        elif item.get("unique"):
            term.print(f"  - {item['name']} [UNIQUE — cannot be sold]")
        else:
            filtered_indices.append(i)
            filtered_names.append(item['name'])
    
    if not filtered_indices:
        term.print("\nNo valid items to sell (all selected items are soulbound or unique).")
        return

    total_gold = sum(_sell_price(all_items[i], player) * all_items[i].get("count", 1) for i in filtered_indices)
    term.print(f"\nYou will sell {len(filtered_indices)} item stack(s) for {total_gold} gold:")
    for n in filtered_names:
        term.print(f"  - {n}")
    if not term.confirm("Confirm sale?"):
        term.print("Cancelled.")
        return

    for i in filtered_indices:
        item = all_items[i]
        remove_item_by_reference(player, item, item.get("count", 1))

    player["gold"] = player.get("gold", 0) + total_gold
    term.print(f"Sold {len(filtered_indices)} item stack(s) for {total_gold} gold.")


def upgrade_backpack(player):
    """Upgrade inventory capacity at the shop."""
    upgrade = player.get("inventory_upgrade", 0)
    cost = 200 * (2 ** upgrade)
    equip_cap, other_cap = get_inventory_caps(player)
    next_equip = 10 + (upgrade + 1) * 5
    next_other = 20 + (upgrade + 1) * 10 + len(player.get("allies", [])) * 5
    term.print(f"\n=== Backpack Upgrade (Level {upgrade}) ===")
    term.print(f"Current capacity: {equip_cap} equipment, {other_cap} other items")
    term.print(f"Next level: {next_equip} equipment, {next_other} other items")
    term.print(f"Cost: {cost} gold")
    term.print(f"Your gold: {player.get('gold', 0)}")
    if not term.confirm("Upgrade?"):
        term.print("Upgrade cancelled.")
        return
    if player.get("gold", 0) < cost:
        term.print("Not enough gold.")
        return
    player["gold"] -= cost
    player["inventory_upgrade"] = upgrade + 1
    term.print(f"Backpack upgraded to level {upgrade + 1}!")


def city_shop(player, city_id="solmere"):
    term.clear()
    service_dialogue(city_id, "shop", "enter")   # changed
    city = CITIES.get(city_id, CITIES["solmere"])
    shop_config = city["shop"]
    stock_key = f"shop_stock_{city_id}"
    day_key = f"last_shop_day_{city_id}"
    if stock_key not in player or player.get(day_key) != player.get("day", 1):
        player[stock_key] = []
        stock_size = shop_config.get("stock_size", 8)
        
        # Filter out unique items, ascension stones (temple-only), and wonderland-only items
        available_item_ids = [k for k, v in ITEMS.items() if not v.get("unique") and v.get("type") != "ascension" and not v.get("wonderland_only") and not v.get("black_market_only")]
        
        for _ in range(stock_size):
            item_id = random.choice(available_item_ids)
            base_def = ITEMS[item_id]
            is_equipment = base_def.get("type") == "equipment"
            
            if is_equipment:
                # Equipment: roll rarity with new narrower weights (includes legendary now)
                if shop_config.get("rarity_bias") == "higher":
                    rarity = random.choices(
                        ["common", "uncommon", "rare", "epic", "legendary"],
                        weights=[15, 25, 28, 20, 12])[0]
                else:
                    rarity = random.choices(
                        ["common", "uncommon", "rare", "epic", "legendary"],
                        weights=[30, 32, 22, 12, 4])[0]
            else:
                # Consumables/utilities/scrolls: always common — no rarity scaling
                rarity = "common"
            
            item = build_item(item_id, rarity)
            if is_equipment:
                base_price = shop_config.get("base_price_other", 45)
                base_price = int(base_price * ITEM_RARITY[rarity]["price_mult"])
            else:
                # Consumables/utility/scroll: flat price, no rarity multiplier
                base_price = shop_config.get("base_price_consumable", 45)
            player[stock_key].append((item, base_price))
        player[day_key] = player.get("day", 1)
    shop_stock = player[stock_key]

    def show_shop():
        term.clear()
        service_dialogue(city_id, "shop", "enter")
        equip_cap, other_cap = get_inventory_caps(player)
        equip_count, other_count = count_inventory(player)
        term.print(f"=== {city['name'].upper()} MARKET ===")
        term.print(f"Gold: {player.get('gold', 0)}")
        term.print(f"Inventory: {equip_count}/{equip_cap} equipment | {other_count}/{other_cap} items")
        
        # Display favor and total discount
        favor = player.get('favor', {}).get(city_id, 0)
        c_disc = min(40, max(0, (get_effective_charisma(player) - 8) * 0.5))
        f_disc = min(30, favor * 0.5)
        total_disc = min(70, c_disc + f_disc)
        
        term.print(f"Charisma & Favor ({favor}): → {100 - total_disc:.0f}% of base price (max 70%)\n")
        if player.get("daily_effects", {}).get("shop_discount"):
            term.print("🏮 Month-End Festival: all shops offer 20% off today!\n")
        if player.get("daily_effects", {}).get("shop_surcharge"):
            term.print("🧾 Tax Day: the crown takes a 15% cut on all goods!\n")
        term.print("--- Shop Stock ---")
        for i, (item, base_price) in enumerate(shop_stock, 1):
            final_price = get_discounted_price(base_price, player, city_id)  # Pass city_id here!
            stat = _item_stat_line(item)
            term.print(f"{i}. {item['name']}  {stat} — {final_price} gold (base: {base_price})")

    while True:
        show_shop()
        choice = term.menu([
            "Buy",
            "Sell",
            "Upgrade Backpack",
            "View Stats",
            "Back to City"
        ], prompt="Options:")
        
        if choice == 0:
            # Buy - show stock items as menu
            if not shop_stock:
                term.print("Nothing in stock!")
                term.pause()
                continue
            stock_options = []
            for item, base_price in shop_stock:
                final_price = get_discounted_price(base_price, player, city_id)
                stock_options.append(f"{item['name']} — {final_price}g")
            buy_choice = term.menu(stock_options, prompt="Buy which item?", allow_cancel=True)
            if buy_choice < 0:
                continue
            item, base_price = shop_stock[buy_choice]
            final_price = get_discounted_price(base_price, player, city_id)
            if player.get("gold", 0) >= final_price:
                # Check inventory capacity before buying
                equip_cap, other_cap = get_inventory_caps(player)
                equip_count, other_count = count_inventory(player)
                if item["type"] == "equipment" and equip_count >= equip_cap:
                    term.print("Your equipment bag is full! Upgrade your backpack or store items.")
                    term.pause()
                    continue
                if item["type"] != "equipment" and other_count >= other_cap:
                    term.print("Your item bag is full! Upgrade your backpack or store items.")
                    term.pause()
                    continue
                player["gold"] -= final_price
                if add_item_to_inventory(player, item.copy()):
                    del shop_stock[buy_choice]
                    service_dialogue(city_id, "shop", "success")
                    advance_time(player, 15)
                    term.pause()
                else:
                    term.print("Could not add item to inventory (full).")
                    term.pause()
            else:
                service_dialogue(city_id, "shop", "fail")
                advance_time(player, 10)
                term.pause()
        elif choice == 1:
            sell_items(player)
            advance_time(player, 15)
            term.pause()
        elif choice == 2:
            upgrade_backpack(player)
            advance_time(player, 15)
            term.pause()
        elif choice == 3:
            # GUI mode: open the proper inventory overlay instead of raw text in the log
            if term._screen is not None:
                term.open_inventory()
                # Restore top bar — InventoryScreen overwrites it with "Inventory"
                term._screen.sm.update_top_bar("Shop")
                advance_time(player, 10)
                # No term.pause() needed — the overlay dismissal is the natural pause
            else:
                # Terminal fallback
                term.print("Character stats are only available in GUI mode.")
                advance_time(player, 10)
                term.pause()
        elif choice == 4 or choice == -1:
            service_dialogue(city_id, "shop", "leave")
            advance_time(player, 30)
            break
        else:
            service_dialogue(city_id, "shop", "fail")
            advance_time(player, 10)
            term.pause()
