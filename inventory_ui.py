from combat.skills import get_passive_skill, get_all_unlocked_skills
from inventory import (equip_item, unequip_slot, use_consumable, get_total_equipment_mods,
                       get_inventory_caps, count_inventory, get_sorted_equipment, get_sorted_items,
                       add_item_to_inventory)
from character import player_max_hp
from resources.races_classes import ATTRIBUTES
from utils import clear_screen, format_time
from combat.ally import get_alive_allies, format_ally_status_line
from combat.stat_milestones import format_milestone_label

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
        milestone = format_milestone_label(player, attr)
        milestone_str = f"  [{milestone}]" if milestone else ""
        
        # Display breakdown if there is a buff active
        if bf_bonus > 0:
            print(f"  {attr}: {base} + {eq_bonus}(eq) + {bf_bonus}(buff) = {base + total_bonus}{milestone_str}")
        else:
            print(f"  {attr}: {base} + {eq_bonus} = {base + total_bonus}{milestone_str}")
            
    print("\nEquipment:")
    for slot in ["weapon", "armor", "accessory"]:
        item = player.get("equipped", {}).get(slot)
        if item:
            print(f"  {slot.title()}: {item['name']} ({item.get('rarity','common')})")
        else:
            print(f"  {slot.title()}: empty")

    # Show allies
    allies = get_alive_allies(player)
    if allies:
        print("\n--- Allies ---")
        for i, ally in enumerate(allies):
            print(f"\n  === {ally['name']} (Level {ally.get('level', 1)}) ===")
            print(f"  HP: {ally['current_hp']}/{ally['max_hp']}")

            # Calculate equipment and buff bonuses for ally
            ally_eq_mods = get_total_equipment_mods(ally)
            ally_buff_mods = {}
            for buff in ally.get("active_buffs", []):
                if buff.get("stat") == "all" or buff.get("type") == "blessing":
                    for attr in ATTRIBUTES:
                        ally_buff_mods[attr] = ally_buff_mods.get(attr, 0) + buff["value"]
                elif buff.get("stat") in ATTRIBUTES:
                    attr = buff["stat"]
                    ally_buff_mods[attr] = ally_buff_mods.get(attr, 0) + buff["value"]

            print("  Attributes (base + equipment + buffs):")
            for attr in ATTRIBUTES:
                base = ally["attributes"][attr]
                eq_bonus = ally_eq_mods.get(attr, 0)
                bf_bonus = ally_buff_mods.get(attr, 0)
                total_bonus = eq_bonus + bf_bonus
                milestone = format_milestone_label(ally, attr)
                milestone_str = f"  [{milestone}]" if milestone else ""
                if bf_bonus > 0:
                    print(f"    {attr}: {base} + {eq_bonus}(eq) + {bf_bonus}(buff) = {base + total_bonus}{milestone_str}")
                else:
                    print(f"    {attr}: {base} + {eq_bonus} = {base + total_bonus}{milestone_str}")

            print("  Equipment:")
            for slot in ["weapon", "armor", "accessory"]:
                item = ally.get("equipped", {}).get(slot)
                if item:
                    print(f"    {slot.title()}: {item['name']} ({item.get('rarity', 'common')})")
                else:
                    print(f"    {slot.title()}: empty")

    # Show passive skill
    passive = get_passive_skill(player)
    if passive:
        print(f"\n--- Passive Skill ---")
        print(f"  {passive['name']}: {passive['description']}")

    # Show stat milestone bonuses
    from combat.stat_milestones import format_milestone_bonuses
    milestone_text = format_milestone_bonuses(player)
    if milestone_text:
        print(f"\n{milestone_text}")

    # Show active skills
    unlocked_skills = get_all_unlocked_skills(player)
    if unlocked_skills:
        print(f"\n--- Active Skills ({len(unlocked_skills)} unlocked) ---")
        cooldowns = player.get("skill_cooldowns", {})
        for sid, sdef in unlocked_skills:
            cd = cooldowns.get(sid, 0)
            cd_str = f" [CD: {cd}]" if cd > 0 else ""
            print(f"  {sdef['name']}{cd_str} - Lv.{sdef['unlock_level']}")

    display_active_bounties(player)

def display_active_bounties(player):
    """Show active bounties and which are ready to turn in."""
    bounties = player.get("active_bounties", [])
    if not bounties:
        return
    print("\n--- Active Bounties ---")
    for b in bounties:
        ready = "✓ READY TO CLAIM" if b.get("current", 0) >= b["required"] else f"{b.get('current',0)}/{b['required']}"
        days_left = b["deadline"] - player.get("day", 1)
        print(f"  {b['target_name']}: {ready} (expires in {days_left} days)")

def display_inventory_menu_options():
    """Print the main inventory menu choices."""
    print("\nOptions:")
    print("1. Manage Equipment (equip/unequip - you & allies)")
    print("2. View Bag (use/drop items)")
    print("3. Skill Book")
    print("4. Back to game")

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
        from facilities.skill_book import skill_book_menu
        skill_book_menu(player)
    elif choice == "4":
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
    """Submenu for equipping/unequipping items on player and allies."""
    from combat.ally import get_alive_allies, equip_ally_item, unequip_ally_slot

    while True:
        clear_screen()
        equip_cap, other_cap = get_inventory_caps(player)
        equip_count, other_count = count_inventory(player)
        print(f"Equipment: {equip_count}/{equip_cap} | Other: {other_count}/{other_cap}")
        print("Equipment management:")
        print("1. Equip on yourself")
        print("2. Unequip your slot")
        print("3. Equip on ally")
        print("4. Unequip ally slot")
        print("5. Back")
        sub = input("Choice: ")
        if sub == "1":
            equip_items = get_sorted_equipment(player)
            if not equip_items:
                print("No equipment in bag.")
                input("Press Enter...")
                continue
            for idx, itm in enumerate(equip_items):
                print(f"{idx+1}. {itm['name']} (slot: {itm['slot']}) [{itm.get('rarity','common')}]")
            try:
                idx = int(input("Equip which? (0 cancel): ")) - 1
                if idx >= 0:
                    item = equip_items[idx]
                    orig_idx = next(i for i, itm in enumerate(player["inventory"]) if itm is item)
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
            allies = get_alive_allies(player)
            if not allies:
                print("No allies in your party.")
                input("Press Enter...")
                continue
            equip_items = get_sorted_equipment(player)
            if not equip_items:
                print("No equipment in bag.")
                input("Press Enter...")
                continue
            print("\nChoose ally:")
            for i, a in enumerate(allies):
                print(f"{i+1}. {a['name']}")
            try:
                a_idx = int(input("Ally: ")) - 1
                if 0 <= a_idx < len(allies):
                    ally = allies[a_idx]
                    print(f"\nEquipping {ally['name']}:")
                    for idx, itm in enumerate(equip_items):
                        print(f"{idx+1}. {itm['name']} (slot: {itm['slot']}) [{itm.get('rarity','common')}]")
                    i_idx = int(input("Equip which? (0 cancel): ")) - 1
                    if i_idx >= 0:
                        item = equip_items[i_idx]
                        print(equip_ally_item(ally, item, player))
            except:
                pass
            input("Press Enter...")
        elif sub == "4":
            allies = get_alive_allies(player)
            if not allies:
                print("No allies in your party.")
                input("Press Enter...")
                continue
            print("\nChoose ally:")
            for i, a in enumerate(allies):
                print(f"{i+1}. {a['name']}")
            try:
                a_idx = int(input("Ally: ")) - 1
                if 0 <= a_idx < len(allies):
                    ally = allies[a_idx]
                    print(f"\n{ally['name']}'s equipment:")
                    for slot in ["weapon", "armor", "accessory"]:
                        item = ally.get("equipped", {}).get(slot)
                        if item:
                            print(f"  {slot.title()}: {item['name']}")
                        else:
                            print(f"  {slot.title()}: empty")
                    slot = input("Slot to unequip: ").strip().lower()
                    if slot in ["weapon", "armor", "accessory"]:
                        print(unequip_ally_slot(ally, slot, player))
                    else:
                        print("Invalid slot.")
            except:
                pass
            input("Press Enter...")
        elif sub == "5":
            break

def manage_bag_submenu(player):
    """Submenu for using/dropping items from inventory."""
    while True:
        clear_screen()
        equip_cap, other_cap = get_inventory_caps(player)
        equip_count, other_count = count_inventory(player)
        inv = player.get("inventory", [])
        if not inv:
            print("Your bag is empty.")
            input("Press Enter...")
            break
        print(f"Equipment: {equip_count}/{equip_cap} | Other: {other_count}/{other_cap}")
        print("\nYour items:")
        sorted_equip = get_sorted_equipment(player)
        sorted_items = get_sorted_items(player)
        all_sorted = sorted_equip + sorted_items
        if sorted_equip:
            print("-- Equipment --")
            for idx, itm in enumerate(sorted_equip):
                print(f"  {idx+1}. {itm['name']} ({itm['slot']}) [{itm.get('rarity','common')}]")
        if sorted_items:
            print("-- Items --")
            for idx, itm in enumerate(sorted_items):
                offset = len(sorted_equip)
                print(f"  {idx+1+offset}. {itm['name']} ({itm['type']}) [{itm.get('rarity','common')}]")
        print("\n[U]se item  [D]rop item  [B]ack")
        act = input("Choice: ").strip().lower()
        if act == "u":
            try:
                idx = int(input("Item number: ")) - 1
                if 0 <= idx < len(all_sorted):
                    item = all_sorted[idx]
                    if item["type"] in ("consumable","utility"):
                        msg = use_consumable(player, item, combat_state=None)
                        print(msg)
                        orig_idx = next(i for i, itm in enumerate(player["inventory"]) if itm is item)
                        player["inventory"].pop(orig_idx)
                        input("Press Enter...")
                    else:
                        print("You can only use consumables/utility outside combat.")
                        input("Press Enter...")
            except:
                pass
        elif act == "d":
            try:
                idx = int(input("Drop which? ")) - 1
                if 0 <= idx < len(all_sorted):
                    item = all_sorted[idx]
                    orig_idx = next(i for i, itm in enumerate(player["inventory"]) if itm is item)
                    dropped = player["inventory"].pop(orig_idx)
                    print(f"You drop {dropped['name']}.")
                    input("Press Enter...")
            except:
                pass
        elif act == "b":
            break


def prompt_acquire_item(player, item):
    """Try to add item to inventory. If full, prompt player to discard an existing item or drop the new one.
    Returns True if the item ends up in inventory, False if it was dropped.
    """
    if add_item_to_inventory(player, item):
        return True

    equip_cap, other_cap = get_inventory_caps(player)
    equip_count, other_count = count_inventory(player)

    is_equip = item.get("type") == "equipment"
    cat_name = "Equipment" if is_equip else "Items"
    cur_count = equip_count if is_equip else other_count
    cur_cap = equip_cap if is_equip else other_cap

    print(f"\n⚠️  Your {cat_name.lower()} bag is full! ({cur_count}/{cur_cap})")

    if is_equip:
        candidates = get_sorted_equipment(player)
        header = "-- Equipment --"
    else:
        candidates = get_sorted_items(player)
        header = "-- Items --"

    if not candidates:
        print(f"You have no {cat_name.lower()} to discard. The item is dropped.")
        return False

    print(f"\n{header}")
    for idx, itm in enumerate(candidates):
        extra = f" ({itm['slot']})" if is_equip else f" ({itm['type']})"
        print(f"  {idx+1}. {itm['name']}{extra} [{itm.get('rarity','common')}]")

    print(f"\n[D]rop the new item  or  enter a number (1-{len(candidates)}) to discard that item instead.")
    choice = input("Choice: ").strip().lower()

    if choice == "d":
        print(f"You drop the {item['name']}.")
        return False

    try:
        idx = int(choice) - 1
        if 0 <= idx < len(candidates):
            discarded = candidates[idx]
            orig_idx = next(i for i, itm in enumerate(player["inventory"]) if itm is discarded)
            removed = player["inventory"].pop(orig_idx)
            player.setdefault("inventory", []).append(item)
            print(f"Discarded {removed['name']}. Acquired {item['name']}!")
            return True
        else:
            print("Invalid choice. Dropping the new item.")
            return False
    except (ValueError, StopIteration):
        print("Invalid choice. Dropping the new item.")
        return False
