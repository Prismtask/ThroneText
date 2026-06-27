# facilities/temple.py
import random
from utils import clear_screen, advance_time, format_time
from character import player_max_hp
from city_dialogue import service_dialogue
from facilities.shop import get_discounted_price
from resources.items import build_item
from inventory import add_item_to_inventory, get_inventory_caps, count_inventory


# ── Roman numeral helpers ───────────────────────────────────────────────────

def _int_to_roman(num):
    """Convert integer (1-10) to Roman numeral."""
    val = [10, 9, 5, 4, 1]
    syms = ["X", "IX", "V", "IV", "I"]
    roman = ""
    i = 0
    while num > 0:
        d = num // val[i]
        roman += syms[i] * d
        num -= d * val[i]
        i += 1
    return roman


def _get_global_max_floor(player):
    """Return the highest max_floor reached across all city dungeons."""
    max_floor = 0
    for city_prog in player.get("city_floors", {}).values():
        max_floor = max(max_floor, city_prog.get("max_floor", 1))
    return max_floor


def _get_available_ascension_stones(player):
    """Return list of (tier, item_id, name) for stones the player can currently buy."""
    global_max = _get_global_max_floor(player)
    available = []
    # Stones unlock at floor 10, 20, 30, ...
    tier = 1
    while tier * 10 <= global_max:
        roman = _int_to_roman(tier)
        item_id = f"ascension_stone_{roman.lower().replace(' ', '_')}"
        # Map to actual item IDs (e.g., ascension_stone_i, ascension_stone_ii)
        # The item IDs use lowercase roman without spaces: i, ii, iii, iv, v, vi
        item_id_map = {
            1: "ascension_stone_i",
            2: "ascension_stone_ii",
            3: "ascension_stone_iii",
            4: "ascension_stone_iv",
            5: "ascension_stone_v",
            6: "ascension_stone_vi",
        }
        actual_id = item_id_map.get(tier)
        if actual_id:
            available.append((tier, actual_id, f"Ascension Stone {roman}"))
        tier += 1
    return available


def _ascension_stone_base_price(tier):
    """Linear pricing: 500 gold per tier."""
    return 500 * tier


def _buy_ascension_stone(player, city_id):
    """Show available ascension stones and handle purchase."""
    stones = _get_available_ascension_stones(player)
    if not stones:
        print("No Ascension Stones are available yet. Clear deeper dungeon floors to unlock them.")
        input("Press Enter...")
        return

    print("\n--- Ascension Stones ---")
    print("These sacred stones can break the level limit of your allies.")
    print("(Use them in your House -> Lounge on an ally who has reached their cap.)\n")

    for i, (tier, item_id, name) in enumerate(stones, 1):
        base_price = _ascension_stone_base_price(tier)
        final_price = get_discounted_price(base_price, player, city_id)
        print(f"{i}. {name} — {final_price} gold (base: {base_price})")

    try:
        choice = int(input("\nBuy which stone? (0 to cancel): ").strip())
        if choice == 0:
            print("Cancelled.")
            input("Press Enter...")
            return
        if choice < 1 or choice > len(stones):
            print("Invalid choice.")
            input("Press Enter...")
            return
    except ValueError:
        print("Invalid input.")
        input("Press Enter...")
        return

    tier, item_id, name = stones[choice - 1]
    base_price = _ascension_stone_base_price(tier)
    final_price = get_discounted_price(base_price, player, city_id)

    if player.get("gold", 0) < final_price:
        print("You cannot afford this stone.")
        input("Press Enter...")
        return

    # Check inventory space
    equip_cap, other_cap = get_inventory_caps(player)
    equip_count, other_count = count_inventory(player)
    if other_count >= other_cap:
        print("Your item bag is full! Store or use some items first.")
        input("Press Enter...")
        return

    item = build_item(item_id, rarity="common")
    if not add_item_to_inventory(player, item):
        print("Could not add stone to inventory (full).")
        input("Press Enter...")
        return

    player["gold"] -= final_price
    print(f"\nThe priestess hands you a {name}.")
    print("'May this light shatter the chains that bind your companions.'")
    print(f"You paid {final_price} gold. Remaining: {player['gold']}")
    input("Press Enter...")


# ── Main menu ────────────────────────────────────────────────────────────────

def temple_menu(player, city_id="solmere"):
    while True:
        clear_screen()
        service_dialogue(city_id, "temple", "enter")
        print(f"=== TEMPLE OF {city_id.upper()} ===")
        print(f"Gold: {player.get('gold', 0)} | Time: {format_time(player.get('time_minutes', 480))}")
        
        # NEW: Check if the player OR any ally has a curse
        party_cursed = player.get("cursed") or any(
            ally.get("cursed") or any(d.get("type") == "curse" for d in ally.get("active_debuffs", []))
            for ally in player.get("allies", [])
        )
        
        if party_cursed:
            print("\nYou feel a dark curse weighing upon your party.")
        else:
            print("\nYou feel at peace in this sacred place.")
        
        # Check if ascension stones are available
        stones_available = bool(_get_available_ascension_stones(player))
        
        print("\n1. Remove Curse (100 gold)")
        print("2. Receive Blessing (50 gold – temporary +2 to all stats for next dungeon floor)")
        if stones_available:
            print("3. Buy Ascension Stone")
            print("4. Leave")
        else:
            print("3. Leave")
        
        choice = input("\nChoice: ").strip()
        
        if choice == "1":
            remove_curse(player, city_id)
            advance_time(player, 30)
        elif choice == "2":
            receive_blessing(player, city_id)
            advance_time(player, 30)
        elif choice == "3":
            if stones_available:
                _buy_ascension_stone(player, city_id)
                advance_time(player, 15)
            else:
                service_dialogue(city_id, "temple", "leave")
                advance_time(player, 30)
                break
        elif choice == "4" and stones_available:
            service_dialogue(city_id, "temple", "leave")
            advance_time(player, 30)
            break
        else:
            print("Invalid choice.")
            input("Press Enter...")
            advance_time(player, 15)

def remove_curse(player, city_id):
    # NEW: Find which allies are cursed (flag or active_debuffs)
    cursed_allies = [
        ally for ally in player.get("allies", [])
        if ally.get("cursed") or any(d.get("type") == "curse" for d in ally.get("active_debuffs", []))
    ]
    is_player_cursed = player.get("cursed")

    # NEW: Check if anyone needs cleansing
    if not is_player_cursed and not cursed_allies:
        print("Your party is not cursed. No need for cleansing.")
        input("Press Enter...")
        return
    
    cost = 100
    if player.get("gold", 0) < cost:
        print("You don't have enough gold for the ritual.")
        input("Press Enter...")
        return
    
    player["gold"] -= cost
    
    # Cleanse the Player
    if is_player_cursed:
        player["cursed"] = False
        if player.get("active_debuffs"):
            player["active_debuffs"] = [d for d in player["active_debuffs"] if d.get("type") != "curse"]
            
    # Cleanse all affected Allies
    for ally in cursed_allies:
        ally["cursed"] = False
        if ally.get("active_debuffs"):
            ally["active_debuffs"] = [d for d in ally["active_debuffs"] if d.get("type") != "curse"]
    
    print("The priestess chants ancient prayers. The dark curse lifts from your party.")
    print("The ritual is complete. You all feel cleansed.")
    input("Press Enter...")

def receive_blessing(player, city_id):
    cost = 50
    if player.get("gold", 0) < cost:
        print("You cannot afford a blessing.")
        input("Press Enter...")
        return
    
    player["gold"] -= cost
    
    blessing = {
        "type": "blessing",
        "stat": "all",
        "value": 2,
        "remaining": 1
    }
    player.setdefault("active_buffs", []).append(blessing)
    
    print("The temple's light washes over you. You feel divinely empowered (+2 to all stats for the next floor).")
    service_dialogue(city_id, "temple", "bless")
    input("Press Enter...")
