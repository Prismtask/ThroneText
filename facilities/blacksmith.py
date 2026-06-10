# facilities/blacksmith.py
import random
from resources.items import ITEMS, ITEM_RARITY
from resources.dialogues import BLACKSMITH_DIALOGUES
from inventory import add_item_to_inventory, apply_scroll_to_item
from utils import clear_screen, advance_time, format_time
from combat.generic import get_effective_attribute

def blacksmith_greeting(dialogues):
    print(random.choice(dialogues["greeting"]))

def blacksmith_farewell(dialogues):
    print(random.choice(dialogues["farewell"]))

def get_effective_charisma(player):
    """Fetch the player's true charisma attribute score including equipment."""
    return get_effective_attribute(player, "Charisma")

def get_discounted_blacksmith_price(base_price, player, city_id):
    charisma = get_effective_charisma(player)
    favor = player.get("favor", {}).get(city_id, 0)
    
    discount_percent = min(40, max(0, (charisma - 8) * 0.5))
    favor_discount = min(30, favor * 0.5)
    total_discount = min(70, discount_percent + favor_discount)
    
    discounted = int(base_price * (100 - total_discount) / 100)
    return max(1, discounted)

def enhance_item(player, dialogues, city_id):
    # 1. Build a unified pool of items tracking where they live
    enhanceable_pool = []
    
    # Add equipped items first (Weapon, Armor, Accessory)
    equipped_slots = ["weapon", "armor", "accessory"]
    for slot in equipped_slots:
        equipped_item = player.get("equipped", {}).get(slot)
        if equipped_item:
            enhanceable_pool.append((True, slot, equipped_item))
            
    # Add unequipped equipment from inventory
    inv = player.get("inventory", [])
    for idx, item in enumerate(inv):
        if item.get("type") == "equipment":
            enhanceable_pool.append((False, idx, item))
            
    if not enhanceable_pool:
        print(dialogues["no_equipment"])
        input("Press Enter...")
        return
        
    print("\n--- Enhance Equipment ---")
    for i, (is_equipped, _, item) in enumerate(enhanceable_pool):
        tag = " (Equipped)" if is_equipped else ""
        print(f"{i+1}. {item['name']}{tag} (enhance +{item.get('enhance', 0)})")
        
    try:
        choice = int(input("Choose item to enhance (0 cancel): ")) - 1
        if choice < 0:
            return
            
        is_equipped, location_key, item = enhanceable_pool[choice]
        
        current_enhance = item.get("enhance", 0)
        if current_enhance >= 10:
            print(dialogues["max_enhance"])
            input("Press Enter...")
            return
            
        new_enhance = current_enhance + 1
        rarity_mult = ITEM_RARITY[item["rarity"]]["price_mult"]
        
        # Calculate raw cost and apply Charisma negotiation modifier
        base_cost = int(50 * new_enhance * rarity_mult)
        cost = get_discounted_blacksmith_price(base_cost, player, city_id)
        print(f"Enhance to +{new_enhance} costs {cost} gold (Discounts applied).")
        
        print(f"Enhance to +{new_enhance} costs {cost} gold (Charisma discount applied).")
        confirm = input("Proceed? (y/n): ").strip().lower()
        if confirm != 'y':
            return
            
        if player.get("gold", 0) < cost:
            print(dialogues["not_enough_gold"])
            input("Press Enter...")
            return
            
        # Complete transactions safely
        player["gold"] -= cost
        item["enhance"] = new_enhance
        
        if "mods" in item:
            for stat in item["mods"]:
                item["mods"][stat] += 1
                
        base_display_name = item["name"].split(" +")[0]
        item["name"] = f"{base_display_name} +{new_enhance}"
        
        print(dialogues["enhance_success"].format(item['name']))
        
    except (ValueError, IndexError):
        print(dialogues["invalid_choice"])
        
    input("Press Enter...")

def fuse_scroll_with_item(player, dialogues, city_id):
    # Enforce standard item filtration matching index integrity updates
    inv = player.get("inventory", [])
    scrolls = [(idx, itm) for idx, itm in enumerate(inv) if itm["type"] == "scroll"]
    if not scrolls:
        print(dialogues["no_scrolls"])
        input("Press Enter...")
        return
    print("\n--- Available Scrolls ---")
    for i, (idx, s) in enumerate(scrolls):
        print(f"{i+1}. {s['name']} (Target: {s.get('target_rarity','any')})")
    try:
        choice = int(input("Choose scroll (0 cancel): ")) - 1
        if choice < 0: return
        scroll_idx, scroll = scrolls[choice]
        
        # Build combined pool of weapon slots for fusion targets
        enhanceable_pool = []
        equipped_slots = ["weapon", "armor", "accessory"]
        for slot in equipped_slots:
            equipped_item = player.get("equipped", {}).get(slot)
            if equipped_item:
                enhanceable_pool.append((True, slot, equipped_item))
        for idx, item in enumerate(inv):
            if item.get("type") == "equipment":
                enhanceable_pool.append((False, idx, item))
                
        if not enhanceable_pool:
            print(dialogues["no_equipment"])
            input("Press Enter...")
            return
            
        print("\n--- Choose Equipment for Scroll Fusion ---")
        for i, (is_equipped, _, item) in enumerate(enhanceable_pool):
            tag = " (Equipped)" if is_equipped else ""
            print(f"{i+1}. {item['name']}{tag}")
            
        choice_eq = int(input("Choose equipment: ")) - 1
        is_equipped, location_key, eq_item = enhanceable_pool[choice_eq]
        
        # Apply standard fusion pricing rules modified by Charisma value
        base_cost = 150
        cost = get_discounted_blacksmith_price(base_cost, player, city_id)
        
        if player.get("gold", 0) < cost:
            print(dialogues["not_enough_gold"])
            input("Press Enter...")
            return
            
        if apply_scroll_to_item(eq_item, scroll):
            player["gold"] -= cost
            # Extract scroll instance safely from total inventory tracking list
            player["inventory"].pop(scroll_idx)
            print(dialogues["fusion_success"].format(eq_item['name'], scroll['target_rarity']))
        else:
            print(dialogues["fusion_failed"])
    except (ValueError, IndexError):
        print(dialogues["invalid_choice"])
    input("Press Enter...")

def blacksmith_menu(player, city_id="solmere"):
    dialogues = BLACKSMITH_DIALOGUES.get(city_id, BLACKSMITH_DIALOGUES["solmere"])
    while True:
        clear_screen()
        blacksmith_greeting(dialogues)
        print("=== BLACKSMITH FORGE === ")
        print(f"Gold: {player.get('gold', 0)} | Time: {format_time(player.get('time_minutes', 480))}")
        print("1. Enhance Equipment")
        print("2. Fuse (Scroll + Equipment)")
        print("3. Leave")
        choice = input("Choice: ").strip()
        if choice == "1":
            enhance_item(player, dialogues, city_id)
            advance_time(player, 30)
        elif choice == "2":
            fuse_scroll_with_item(player, dialogues, city_id)
            advance_time(player, 30)
        elif choice == "3":
            blacksmith_farewell(dialogues)
            advance_time(player, 15)
            break
        else:
            print("Invalid Choice.")
            advance_time(player, 10)
            input("Press Enter...")