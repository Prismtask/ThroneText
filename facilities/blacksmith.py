import random
from resources.items import ITEMS, ITEM_RARITY
from resources.dialogues import BLACKSMITH_DIALOGUES
from inventory import add_item_to_inventory, apply_scroll_to_item
from utils import clear_screen, advance_time, format_time

def blacksmith_greeting(dialogues):
    print(random.choice(dialogues["greeting"]))

def blacksmith_farewell(dialogues):
    print(random.choice(dialogues["farewell"]))

def enhance_item(player, dialogues):
    # 1. Build a unified list of options: (is_equipped, item_key_or_idx, item_dict)
    enhanceable_pool = []
    
    # Add equipped items first (Weapon, Armor, Accessory)
    equipped_slots = ["weapon", "armor", "accessory"]
    for slot in equipped_slots:
        equipped_item = player.get("equipped", {}).get(slot)
        if equipped_item: # Make sure the slot isn't empty (None)
            enhanceable_pool.append((True, slot, equipped_item))
            
    # Add unequipped equipment from inventory
    inv = player.get("inventory", [])
    for idx, item in enumerate(inv):
        if item.get("type") == "equipment":
            enhanceable_pool.append((False, idx, item))
            
    # If no items were found at all, back out
    if not enhanceable_pool:
        print(dialogues["no_equipment"])
        input("Press Enter...")
        return
        
    print("\n--- Enhance Equipment ---")
    # 2. Display the list (Equipped items appear first)
    for i, (is_equipped, _, item) in enumerate(enhanceable_pool):
        tag = " (Equipped)" if is_equipped else ""
        print(f"{i+1}. {item['name']}{tag} (enhance +{item.get('enhance', 0)})")
        
    try:
        choice = int(input("Choose item to enhance (0 cancel): ")) - 1
        if choice < 0:
            return
            
        # Extract the chosen item details
        is_equipped, location_key, item = enhanceable_pool[choice]
        
        current_enhance = item.get("enhance", 0)
        if current_enhance >= 10:
            print(dialogues["max_enhance"])
            input("Press Enter...")
            return
            
        new_enhance = current_enhance + 1
        rarity_mult = ITEM_RARITY[item["rarity"]]["price_mult"]
        cost = int(50 * new_enhance * rarity_mult)
        
        print(f"Enhance to +{new_enhance} costs {cost} gold.")
        confirm = input("Proceed? (y/n): ").strip().lower()
        if confirm != 'y':
            return
            
        if player.get("gold", 0) < cost:
            print(dialogues["not_enough_gold"])
            input("Press Enter...")
            return
            
        # Process payment
        player["gold"] -= cost
        item["enhance"] = new_enhance
        
        # Safe stat boost calculation (keeps random custom modifiers safe)
        if "mods" in item:
            for stat in item["mods"]:
                item["mods"][stat] += 1
                
        # Handle renaming cleanly without piling up (+1 +2) suffixes
        base_display_name = item["name"].split(" +")[0]
        item["name"] = f"{base_display_name} +{new_enhance}"
        
        print(dialogues["enhance_success"].format(item['name']))
        
    except (ValueError, IndexError):
        print(dialogues["invalid_choice"])
        
    input("Press Enter...")

def fuse_scroll_with_item(player, dialogues):
    inv = player.get("inventory", [])
    scrolls = [(idx, itm) for idx, itm in enumerate(inv) if itm["type"] == "scroll"]
    equip = [(idx, itm) for idx, itm in enumerate(inv) if itm["type"] == "equipment"]
    if not scrolls:
        print(dialogues["no_scrolls"])
        input("Press Enter...")
        return
    if not equip:
        print(dialogues["no_equipment_fuse"])
        input("Press Enter...")
        return
    print("\n--- Fuse: Scroll + Equipment ---")
    print("Choose a scroll:")
    for i, (idx, sc) in enumerate(scrolls):
        print(f"{i+1}. {sc['name']} (upgrade items to {sc['target_rarity']})")
    try:
        s_choice = int(input("Scroll number (0 cancel): ")) - 1
        if s_choice < 0:
            return
        scroll_idx, scroll = scrolls[s_choice]
        print("\nChoose equipment to upgrade:")
        for i, (idx, eq) in enumerate(equip):
            print(f"{i+1}. {eq['name']} (current rarity: {eq['rarity']})")
        e_choice = int(input("Equipment number: ")) - 1
        if e_choice < 0:
            return
        eq_idx, eq_item = equip[e_choice]
        rarities = ["common", "uncommon", "rare", "epic", "legendary"]
        current_rank = rarities.index(eq_item["rarity"])
        target_rank = rarities.index(scroll["target_rarity"])
        if target_rank <= current_rank:
            print(dialogues["scroll_not_higher"])
            input("Press Enter...")
            return
        cost = 100 * (target_rank - current_rank)
        print(f"Fusion cost: {cost} gold.")
        confirm = input("Proceed with fusion? (y/n): ").strip().lower()
        if confirm != 'y':
            return
        if player.get("gold", 0) < cost:
            print(dialogues["not_enough_gold"])
            input("Press Enter...")
            return
        if apply_scroll_to_item(eq_item, scroll):
            player["gold"] -= cost
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
        print("=== BLACKSMITH FORGE ===")
        print(f"Gold: {player.get('gold', 0)} | Time: {format_time(player.get('time_minutes', 480))}")
        print("1. Enhance Equipment")
        print("2. Fuse (Scroll + Equipment)")
        print("3. Leave")
        choice = input("Choice: ").strip()
        if choice == "1":
            enhance_item(player, dialogues)
            advance_time(player, 30)
        elif choice == "2":
            fuse_scroll_with_item(player, dialogues)
            advance_time(player, 30)
        elif choice == "3":
            blacksmith_farewell(dialogues)
            advance_time(player, 30)
            break
        else:
            print(dialogues["invalid_choice"])
            advance_time(player, 15)