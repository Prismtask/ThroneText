from inventory import equip_item, unequip_slot, use_consumable, get_total_equipment_mods
from character import player_max_hp
from resources.races_classes import ATTRIBUTES
from utils import clear_screen, format_time

def display_player_status(player):
    """Show player name, level, HP, attributes (with equipment and buff bonuses), and equipped items."""
    equip_mods = get_total_equipment_mods(player)
    
    # Calculate additional bonuses from active buffs/blessings
    buff_mods = {}
    for buff in player.get("active_buffs", []):
        if buff.get("stat") == "all" or buff.get("type") == "blessing":
            for attr in ATTRIBUTES:
                buff_mods[attr] = buff_mods.get(attr, 0) + buff["value"]
        elif buff.get("stat") in ATTRIBUTES:
            attr = buff["stat"]
            buff_mods[attr] = buff_mods.get(attr, 0) + buff["value"]

    print(f"\n=== {player['name']} (Level {player.get('level',1)}) ===")
    print(f"HP: {player['current_hp']}/{player_max_hp(player)}")
    print(f"Time: {format_time(player.get('time_minutes', 480))}")
    print(f"Gold: {player['gold']}")
    print("Attributes (base + equipment + buffs):")
    for attr in ATTRIBUTES:
        base = player["attributes"][attr]
        eq_bonus = equip_mods.get(attr, 0)
        bf_bonus = buff_mods.get(attr, 0)
        total_bonus = eq_bonus + bf_bonus
        
        # Display breakdown if there is a buff active
        if bf_bonus > 0:
            print(f"  {attr}: {base} + {eq_bonus}(eq) + {bf_bonus}(buff) = {base + total_bonus}")
        else:
            print(f"  {attr}: {base} + {eq_bonus} = {base + total_bonus}")
            
    print("\nEquipment:")
    for slot in ["weapon", "armor", "accessory"]:
        item = player.get("equipped", {}).get(slot)
        if item:
            print(f"  {slot.title()}: {item['name']} ({item.get('rarity','common')})")
        else:
            print(f"  {slot.title()}: empty")

def display_inventory_menu_options():
    """Print the main inventory menu choices."""
    print("\nOptions:")
    print("1. Manage Equipment (equip/unequip)")
    print("2. View Bag (use/drop items)")
    print("3. Back to game")

def handle_inventory_choice(player, choice):
    """
    Process the user's menu choice.
    Returns a string indicating the action: "back", "quit", or None to continue loop.
    """
    if choice == "1":
        manage_equipment_submenu(player)
    elif choice == "2":
        manage_bag_submenu(player)
    elif choice == "3":
        return "back"
    else:
        print("Invalid choice.")
        input("Press Enter...")
    return None

def manage_inventory_menu(player):
    """Main inventory/stats screen – now a clean loop."""
    while True:
        clear_screen()
        display_player_status(player)
        display_inventory_menu_options()
        choice = input("Choice: ").strip()
        result = handle_inventory_choice(player, choice)
        if result == "back":
            break
        elif result == "quit":
            return "quit"
    return None

def manage_equipment_submenu(player):
    """Submenu for equipping/unequipping items."""
    while True:
        clear_screen()
        print("Equipment management:")
        print("1. Equip from inventory")
        print("2. Unequip a slot")
        print("3. Back")
        sub = input("Choice: ")
        if sub == "1":
            equip_items = [i for i in player.get("inventory", []) if i["type"] == "equipment"]
            if not equip_items:
                print("No equipment in bag.")
                input("Press Enter...")
                continue
            for idx, itm in enumerate(equip_items):
                print(f"{idx+1}. {itm['name']} (slot: {itm['slot']})")
            try:
                idx = int(input("Equip which? (0 cancel): ")) - 1
                if idx >= 0:
                    item = equip_items[idx]
                    orig_idx = player["inventory"].index(item)
                    player["inventory"].pop(orig_idx)
                    equip_item(player, item)
            except:
                pass
        elif sub == "2":
            print("Slots: weapon, armor, accessory")
            slot = input("Slot to unequip: ").strip().lower()
            if slot in ["weapon","armor","accessory"]:
                unequip_slot(player, slot)
            else:
                print("Invalid slot.")
            input("Press Enter...")
        elif sub == "3":
            break

def manage_bag_submenu(player):
    """Submenu for using/dropping items from inventory."""
    while True:
        clear_screen()
        inv = player.get("inventory", [])
        if not inv:
            print("Your bag is empty.")
            input("Press Enter...")
            break
        print("Your items:")
        for idx, itm in enumerate(inv):
            print(f"{idx+1}. {itm['name']} ({itm['type']})")
        print("\n[U]se item  [D]rop item  [B]ack")
        act = input("Choice: ").strip().lower()
        if act == "u":
            try:
                idx = int(input("Item number: ")) - 1
                if 0 <= idx < len(inv):
                    item = inv[idx]
                    if item["type"] in ("consumable","utility"):
                        msg = use_consumable(player, item, combat_state=None)
                        print(msg)
                        player["inventory"].pop(idx)
                        input("Press Enter...")
                    else:
                        print("You can only use consumables/utility outside combat.")
                        input("Press Enter...")
            except:
                pass
        elif act == "d":
            try:
                idx = int(input("Drop which? ")) - 1
                if 0 <= idx < len(inv):
                    dropped = player["inventory"].pop(idx)
                    print(f"You drop {dropped['name']}.")
                    input("Press Enter...")
            except:
                pass
        elif act == "b":
            break