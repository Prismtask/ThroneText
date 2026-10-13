# facilities/shop.py
import random
from resources.items import ITEMS, build_item, ITEM_RARITY, is_unique_item
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


_SELL_RARITY_KEYWORDS = {"common", "uncommon", "rare", "epic", "legendary", "unique"}

_SELL_TYPE_KEYWORDS = {
    "weapon": "weapon", "weapons": "weapon",
    "armor": "armor", "armour": "armor",
    "accessory": "accessory", "accessories": "accessory",
    "equipment": "equipment",
    "consumable": "consumable", "consumables": "consumable",
    "scroll": "scroll", "scrolls": "scroll",
    "utility": "utility",
}


def _sell_filter_matches(item, rarity, type_filter):
    """True if an item matches a rarity and/or type filter (both optional)."""
    if rarity and item.get("rarity", "common") != rarity:
        return False
    if not type_filter:
        return True
    if type_filter == "equipment":
        return item.get("type") == "equipment"
    if type_filter in ("weapon", "armor", "accessory"):
        return item.get("slot") == type_filter
    return item.get("type") == type_filter


def _parse_sell_selection(raw, all_items):
    """Parse sell input into a set of indices into all_items.

    Supports explicit numbers/ranges ('1 3 5', '1-4'), 'all', and keyword
    filters by rarity ('common'), type ('weapon', 'consumable'), or both
    ('common weapon', 'rare armor'). Separate filters combine as a union;
    an adjacent rarity+type pair matches items satisfying both.
    """
    tokens = raw.replace(",", " ").split()
    wants_all = "all" in tokens
    tokens = [t for t in tokens if t != "all"]

    indices = set()
    filters = []

    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if any(ch.isdigit() for ch in tok):
            if "-" in tok:
                try:
                    a, b = tok.split("-", 1)
                    indices.update(range(int(a) - 1, int(b)))
                except ValueError:
                    pass
            else:
                try:
                    indices.add(int(tok) - 1)
                except ValueError:
                    pass
            i += 1
            continue

        rarity = tok if tok in _SELL_RARITY_KEYWORDS else None
        type_filter = _SELL_TYPE_KEYWORDS.get(tok)
        if rarity or type_filter:
            nxt = tokens[i + 1] if i + 1 < len(tokens) else None
            nxt_rarity = nxt if nxt in _SELL_RARITY_KEYWORDS else None
            nxt_type = _SELL_TYPE_KEYWORDS.get(nxt) if nxt else None
            if rarity and nxt_type:
                filters.append((rarity, nxt_type))            # e.g. 'common weapon'
                i += 2
                continue
            if type_filter and nxt_rarity:
                filters.append((nxt_rarity, type_filter))     # e.g. 'weapon common'
                i += 2
                continue
            filters.append((rarity, type_filter))
        i += 1

    if wants_all and not indices and not filters:
        return set(range(len(all_items)))

    for rarity, type_filter in filters:
        for idx, item in enumerate(all_items):
            if _sell_filter_matches(item, rarity, type_filter):
                indices.add(idx)
    return indices


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
    
    term.print("Tip: you can sell by rarity/type — e.g. 'common', 'uncommon weapon', 'rare armor'.")
    raw = term.input("Sell which items? (e.g. '1 3 5', '1-4', or 'all'). 0 to cancel: ").strip().lower()
    if raw in ("", "0", "cancel"):
        term.print("Cancelled.")
        return

    indices = _parse_sell_selection(raw, all_items)

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
        elif is_unique_item(item):
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


def _cargo_market(player, city_id):
    """Permit-gated cargo trading: buy local stock, sell held cargo."""
    from inventory import remove_item_by_reference, get_cargo_items
    from resources.trade_goods import (
        TRADE_GOODS, build_cargo, cargo_buy_price, cargo_sell_price,
        cargo_total_weight, cargo_capacity, cargo_overload_limit,
        roll_daily_cargo_stock, DAILY_RESTOCK, cargo_demand, THEMES,
    )

    if not player.get("trade_permit"):
        term.print("\nA guarded counter sits behind a velvet rope.")
        term.print("The clerk waves you off. 'Trade permit required.'")
        term.pause()
        return

    stock_key = f"cargo_stock_{city_id}"
    day_key   = f"last_cargo_day_{city_id}"

    if stock_key not in player or player.get(day_key) != player.get("day", 1):
        # 2-3 distinct goods, 5 units each, origin-weighted selection
        goods = roll_daily_cargo_stock(city_id, random.randint(2, 3))
        player[stock_key] = [[gid, DAILY_RESTOCK] for gid in goods]
        player[day_key] = player.get("day", 1)

    stock  = player[stock_key]
    weight = cargo_total_weight(player)
    cap    = cargo_capacity(player)
    limit  = cargo_overload_limit(player)

    def _load_line():
        if cap > 0:
            return f"Load: {weight}/{cap} wt  (overload cap {limit})"
        return f"Load: {weight}/0 wt — no mount (can't buy cargo)"

    while True:
        term.clear()
        term.print("=== CARGO MARKET ===")
        term.print(f"Gold: {player.get('gold', 0)}")
        term.print(_load_line())
        theme_parts = "  |  ".join(f"{t} ×{cargo_demand(city_id, t):.1f}" for t in THEMES)
        term.print(f"Local demand — {theme_parts}")
        if cap <= 0:
            term.print("(Buy a mount or caravan at the Trade Hall to haul goods.)")
        term.print("")

        choice = term.menu(["Buy goods", "Sell cargo", "Back"], prompt="Options:")

        if choice == 0:
            # ── Buy ─────────────────────────────────────────────────
            stock = [entry for entry in stock if entry[1] > 0]
            if not stock:
                term.print("Nothing left in stock today. Come back tomorrow.")
                term.pause()
                continue
            buy_options = []
            for gid, units in stock:
                g = TRADE_GOODS[gid]
                price = cargo_buy_price(gid, player)
                buy_options.append(f"{g['name']} — {price}g  (wt {g['weight']})  [{units} left]")
            buy_choice = term.menu(buy_options, prompt="Buy which good?", allow_cancel=True)
            if buy_choice < 0:
                continue
            gid, units = stock[buy_choice]
            g = TRADE_GOODS[gid]
            price = cargo_buy_price(gid, player)
            if player.get("gold", 0) < price:
                term.print("Not enough gold.")
                term.pause()
                continue
            if weight + g["weight"] > limit:
                term.print(f"Your transport can't haul that — overload cap is {limit} wt.")
                term.pause()
                continue
            player["gold"] -= price
            item = build_cargo(gid)
            if add_item_to_inventory(player, item):
                stock[buy_choice][1] -= 1
                weight += g["weight"]
                term.print(f"You load {g['name']} ({g['weight']} wt) for {price}g.")
                advance_time(player, 15)
            else:
                player["gold"] += price
                term.print("Could not add cargo to inventory.")
            term.pause()

        elif choice == 1:
            # ── Sell ────────────────────────────────────────────────
            cargo_items = get_cargo_items(player)
            if not cargo_items:
                term.print("You have no cargo to sell.")
                term.pause()
                continue
            sell_options = []
            for item in cargo_items:
                count = item.get("count", 1)
                price = cargo_sell_price(item, player, city_id)
                count_str = f" (x{count})" if count > 1 else ""
                sell_options.append(f"{item['name']}{count_str} — {price * count}g ({price}g each)")
            sell_choice = term.menu(sell_options, prompt="Sell which cargo?", allow_cancel=True)
            if sell_choice < 0:
                continue
            item = cargo_items[sell_choice]
            price = cargo_sell_price(item, player, city_id)
            gold = price * item.get("count", 1)
            weight -= item.get("weight", 0) * item.get("count", 1)
            remove_item_by_reference(player, item, item.get("count", 1))
            player["gold"] = player.get("gold", 0) + gold
            term.print(f"Sold {item['name']} for {gold}g.")
            advance_time(player, 15)
            term.pause()

        elif choice == 2 or choice == -1:
            break


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
        available_item_ids = [k for k, v in ITEMS.items() if not v.get("unique") and v.get("type") != "ascension" and not v.get("wonderland_only") and not v.get("black_market_only") and not v.get("no_random_stock")]
        
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
        # Travel staple: every shop carries one Portable Camp (§8 camping)
        if not any(i.get("id") == "portable_camp" for i, _p in player[stock_key]):
            player[stock_key].append((build_item("portable_camp", "common"), 250))
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
        cargo_label = (
            "Cargo Market" if player.get("trade_permit")
            else "??? — Requires Trade Permit"
        )
        choice = term.menu([
            "Buy",
            "Sell",
            "Upgrade Backpack",
            "View Stats",
            cargo_label,
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
        elif choice == 4:
            _cargo_market(player, city_id)
        elif choice == 5 or choice == -1:
            service_dialogue(city_id, "shop", "leave")
            break
        else:
            service_dialogue(city_id, "shop", "fail")
            advance_time(player, 10)
            term.pause()
