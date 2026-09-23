# facilities/blacksmith.py
import random
from resources.items import ITEM_RARITY
from resources.dialogues import BLACKSMITH_DIALOGUES
from inventory import apply_scroll_to_item, remove_item_by_reference
from utils import advance_time
from gui.terminal import term
from gui.theme import Theme
from facilities.shop import get_discounted_price

def blacksmith_greeting(dialogues):
    term.print(random.choice(dialogues["greeting"]))

def blacksmith_farewell(dialogues):
    term.print(random.choice(dialogues["farewell"]))

def _rarity_style(item):
    """Return a button style dict for the given item based on its rarity."""
    rarity = item.get("rarity", "common")
    color = Theme.RARITY_COLORS.get(rarity, Theme.BUTTON_FG)
    darker = _darken_color(color)
    return {"fg": color, "active_fg": color, "bg": darker, "active_bg": darker}


def _darken_color(hex_color):
    """Darken a hex color slightly for button background."""
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    r, g, b = max(0, r - 60), max(0, g - 60), max(0, b - 60)
    return f"#{r:02x}{g:02x}{b:02x}"


def enhance_item(player, dialogues, city_id):
    # 1. Build a unified pool of items tracking where they live
    enhanceable_pool = []
    
    # Add player's equipped items first (Weapon, Armor, Accessory)
    equipped_slots = ["weapon", "armor", "accessory1", "accessory2"]
    for slot in equipped_slots:
        equipped_item = player.get("equipped", {}).get(slot)
        if equipped_item:
            enhanceable_pool.append((True, "Player", equipped_item))
            
    # Add ally equipped items
    for ally in player.get("allies", []):
        for slot in equipped_slots:
            equipped_item = ally.get("equipped", {}).get(slot)
            if equipped_item:
                enhanceable_pool.append((True, ally["name"], equipped_item))
            
    # Add unequipped equipment from inventory
    inv = player.get("inventory", [])
    for idx, item in enumerate(inv):
        if item.get("type") == "equipment":
            enhanceable_pool.append((False, None, item))
            
    if not enhanceable_pool:
        term.print(dialogues["no_equipment"])
        term.pause()
        return
        
    term.print("\n--- Enhance Equipment ---")
    options = []
    styles = []
    for i, (is_equipped, owner_name, item) in enumerate(enhanceable_pool):
        tag = f" (Equipped by {owner_name})" if is_equipped else ""
        term.print(f"{i+1}. {item['name']}{tag} (enhance +{item.get('enhance', 0)})")
        options.append(f"{item['name']}{tag} (+{item.get('enhance', 0)})")
        styles.append(_rarity_style(item))
        
    choice = term.menu(options, prompt="Choose item to enhance:", allow_cancel=True, styles=styles)
    if choice < 0:
        return
            
    is_equipped, owner_name, item = enhanceable_pool[choice]
    
    current_enhance = item.get("enhance", 0)
    if current_enhance >= 10:
        term.print(dialogues["max_enhance"])
        term.pause()
        return

    # Unique items cannot be enhanced past +5
    if item.get("unique") and current_enhance >= 5:
        term.print("Unique items cannot be enhanced past +5 — their essence resists further tempering.")
        term.pause()
        return
        
    new_enhance = current_enhance + 1
    rarity_mult = ITEM_RARITY[item["rarity"]]["price_mult"]
    
    # Exponential cost scaling by enchant level: each +1 costs ~1.5× more than the last.
    # This closes the exploit where players could degrade rarity, enchant cheaply,
    # then upgrade rarity back — high-enchant items are always expensive regardless.
    base_cost = int(50 * rarity_mult * (1.5 ** new_enhance))
    cost = get_discounted_price(base_cost, player, city_id)
    term.print(f"Enhance to +{new_enhance} costs {cost} gold (Discounts applied).")

    if not term.confirm("Proceed?"):
        return
        
    if player.get("gold", 0) < cost:
        term.print(dialogues["not_enough_gold"])
        term.pause()
        return
            
    player["gold"] -= cost
    item["enhance"] = new_enhance
    
    if "mods" in item:
        for stat in item["mods"]:
            item["mods"][stat] += 1
            
    base_display_name = item["name"].split(" +")[0]
    item["name"] = f"{base_display_name} +{new_enhance}"
    
    term.print(dialogues["enhance_success"].format(item['name']))
        
    term.pause()

def fuse_scroll_with_item(player, dialogues, city_id):
    # Enforce standard item filtration matching index integrity updates
    inv = player.get("inventory", [])
    scrolls = [(idx, itm) for idx, itm in enumerate(inv) if itm["type"] == "scroll"]
    if not scrolls:
        term.print(dialogues["no_scrolls"])
        term.pause()
        return
    term.print("\n--- Available Scrolls ---")
    scroll_options = []
    for i, (idx, s) in enumerate(scrolls):
        term.print(f"{i+1}. {s['name']} (Target: {s.get('target_rarity','any')})")
        scroll_options.append(f"{s['name']} (Target: {s.get('target_rarity','any')})")
    
    choice = term.menu(scroll_options, prompt="Choose scroll:", allow_cancel=True)
    if choice < 0:
        return
    scroll_idx, scroll = scrolls[choice]
    
    # Build combined pool of weapon slots for fusion targets
    enhanceable_pool = []
    equipped_slots = ["weapon", "armor", "accessory1", "accessory2"]
    for slot in equipped_slots:
        equipped_item = player.get("equipped", {}).get(slot)
        if equipped_item:
            enhanceable_pool.append((True, "Player", equipped_item))
    for ally in player.get("allies", []):
        for slot in equipped_slots:
            equipped_item = ally.get("equipped", {}).get(slot)
            if equipped_item:
                enhanceable_pool.append((True, ally["name"], equipped_item))
    for idx, item in enumerate(inv):
        if item.get("type") == "equipment":
            enhanceable_pool.append((False, None, item))
            
    if not enhanceable_pool:
        term.print(dialogues["no_equipment"])
        term.pause()
        return
        
    term.print("\n--- Choose Equipment for Scroll Fusion ---")
    eq_options = []
    eq_styles = []
    for i, (is_equipped, owner_name, item) in enumerate(enhanceable_pool):
        tag = f" (Equipped by {owner_name})" if is_equipped else ""
        term.print(f"{i+1}. {item['name']}{tag}")
        eq_options.append(f"{item['name']}{tag}")
        eq_styles.append(_rarity_style(item))
        
    choice_eq = term.menu(eq_options, prompt="Choose equipment:", allow_cancel=True, styles=eq_styles)
    if choice_eq < 0:
        return
    is_equipped, owner_name, eq_item = enhanceable_pool[choice_eq]
    
    # Apply standard fusion pricing rules modified by Charisma value
    base_cost = 150
    cost = get_discounted_price(base_cost, player, city_id)
    term.print(f"Fusing {scroll['name']} into {eq_item['name']} costs {cost} gold.")

    if not term.confirm("Proceed?"):
        return

    if player.get("gold", 0) < cost:
        term.print(dialogues["not_enough_gold"])
        term.pause()
        return
        
    if apply_scroll_to_item(eq_item, scroll):
        player["gold"] -= cost
        # Extract scroll instance safely from total inventory tracking list
        remove_item_by_reference(player, scroll)
        term.print(dialogues["fusion_success"].format(eq_item['name'], scroll['target_rarity']))
    else:
        term.print(dialogues["fusion_failed"])
    term.pause()

def blacksmith_menu(player, city_id="solmere"):
    dialogues = BLACKSMITH_DIALOGUES.get(city_id, BLACKSMITH_DIALOGUES["solmere"])
    while True:
        term.clear()
        blacksmith_greeting(dialogues)
        term.print("=== BLACKSMITH FORGE === ")
        term.print(f"Gold: {player.get('gold', 0)}")
        
        choice = term.menu([
            "Enhance Equipment",
            "Fuse (Scroll + Equipment)",
            "Leave"
        ], prompt="What would you like to forge?")
        
        if choice == 0:
            enhance_item(player, dialogues, city_id)
            advance_time(player, 30)
        elif choice == 1:
            fuse_scroll_with_item(player, dialogues, city_id)
            advance_time(player, 30)
        elif choice == 2 or choice == -1:
            blacksmith_farewell(dialogues)
            advance_time(player, 15)
            break
        else:
            term.print("Invalid Choice.")
            advance_time(player, 10)
            term.pause()