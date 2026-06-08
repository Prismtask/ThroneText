import random
from resources.enemies import ENEMIES
from resources.items import build_item, ITEMS, ITEM_RARITY
from resources.cities import CITIES
from combat import combat, player_con_mod
from character import player_max_hp
from save_load import save_game
from utils import clear_screen, advance_time, get_difficulty_multiplier_from_time, format_time
from inventory_ui import manage_inventory_menu
from leveling import gain_exp


def get_random_enemy_key(floor, boss=False):
    """Pick a random enemy suitable for the current floor."""
    pool = []
    for key, data in ENEMIES.items():
        if boss and not data.get("boss", False):
            continue
        if boss:
            if data["level"] >= floor + 1 and data["level"] <= floor + 5:
                pool.append(key)
        else:
            if data["level"] >= max(1, floor - 1) and data["level"] <= floor + 3:
                pool.append(key)

    if not pool:
        pool = [k for k, d in ENEMIES.items() 
                if d.get("boss", False) == boss and d["level"] >= floor - 2]
    if not pool:
        pool = [k for k, d in ENEMIES.items() if d.get("boss", False) == boss]

    return random.choice(pool)


def generate_floor(floor):
    """Create a list of enemy keys: 4 normal rooms + 1 boss."""
    enemies = [get_random_enemy_key(floor, boss=False) for _ in range(4)]
    boss = get_random_enemy_key(floor, boss=True)
    enemies.append(boss)
    return enemies


def roll_drop(enemy_level):
    """Improved drop rate and better rarity distribution."""
    if random.random() > 0.50:          # ← Increased from 0.3 to 50%
        return None

    rarities = ["common", "uncommon", "rare", "epic", "legendary"]
    
    if enemy_level <= 3:
        weights = [0.50, 0.35, 0.12, 0.03, 0.00]
    elif enemy_level <= 6:
        weights = [0.35, 0.40, 0.18, 0.06, 0.01]
    elif enemy_level <= 9:
        weights = [0.20, 0.35, 0.30, 0.12, 0.03]
    else:
        weights = [0.10, 0.25, 0.35, 0.20, 0.10]

    rarity = random.choices(rarities, weights=weights)[0]
    item_id = random.choice(list(ITEMS.keys()))
    return (item_id, rarity)

def roll_gold_drop(enemy_key, is_boss=False):
    """Roll gold drop from defeated enemy."""
    enemy_level = ENEMIES[enemy_key]["level"]
    
    # Base gold
    base_gold = enemy_level * 8 + random.randint(5, 15)
    
    if is_boss:
        base_gold = int(base_gold * 2.5) + random.randint(20, 40)
    
    # Bonus gold chance (25% chance for big bonus)
    if random.random() < 0.25:
        base_gold = int(base_gold * 1.6)
    
    gold = max(8, base_gold)  # Minimum gold
    
    return gold


def add_drop_to_inventory(player, enemy_level):
    drop = roll_drop(enemy_level)
    if drop:
        item_id, rarity = drop
        item = build_item(item_id, rarity)
        player.setdefault("inventory", []).append(item)
        print(f"\nYou found: {item['name']}!")
        return True
    return False

def add_gold_drop(player, enemy_key):
    """Add gold from enemy to player and print message."""
    is_boss = ENEMIES[enemy_key].get("boss", False)
    gold = roll_gold_drop(enemy_key, is_boss)
    
    player["gold"] = player.get("gold", 0) + gold
    print(f"You found {gold} gold on the enemy!")

def explore_dungeon(player):
    """Main dungeon loop. Clears one floor. Returns False if player dies."""
    floor = player["floor"]
    print(f"\n=== DESCENDING INTO DUNGEON FLOOR {floor} ===")
    input("Press Enter to begin your descent...")

    rooms = generate_floor(floor)
    total_rooms = len(rooms)

    for i, enemy_key in enumerate(rooms):
        if i == total_rooms - 1:
            print(f"\n*** BOSS ROOM ***")
        else:
            print(f"\n--- Room {i+1} ---")
        input("Press Enter to enter the room...")

        # Advance time by 1 hour per room
        advance_time(player, 60)

        while True:
            clear_screen()
            print(f"Dungeon Floor {floor} - Room {i+1}/{total_rooms} | Time: {format_time(player.get('time_minutes', 480))}")
            result = combat(player, enemy_key)

            if result == "victory":
                enemy_level = ENEMIES[enemy_key]["level"]
                gain_exp(player, enemy_level * 12)
                add_drop_to_inventory(player, enemy_level)
                add_gold_drop(player, enemy_key)

                # Heal after victory
                heal = random.randint(1, 5) + player_con_mod(player)
                player["current_hp"] = min(
                    player["current_hp"] + heal,
                    player_max_hp(player)
                )
                print(f"You catch your breath and recover {heal} HP.")

                while True:
                    print("\n[Enter] to continue  [I]nventory/Stats  [S]ave and quit")
                    cmd = input().strip().lower()
                    if cmd == "":
                        break
                    elif cmd == "i":
                        manage_inventory_menu(player)
                        continue
                    elif cmd == "s":
                        save_game(player)
                        print("Game saved. Exiting to menu.")
                        return "save_exit"
                    else:
                        continue
                break

            elif result == "fled":
                print("You retreat from the room. The enemy remains.")
                continue
            elif result == "dead":
                print("Your adventure ends here...")
                return False

    # Floor cleared
    player["floor"] += 1

    if player.get("active_buffs"):
        orig_len = len(player["active_buffs"])
        player["active_buffs"] = [b for b in player["active_buffs"] if b.get("type") != "blessing"]
        if len(player["active_buffs"]) < orig_len:
            print("\nYour divine temple blessing has worn off as you transition floors.")
    # Advance time by 1 hour for floor completion
    current_time = advance_time(player, 60)
    
    print(f"\nYou have cleared Floor {floor}!")
    print(f"Current time: {current_time} | Gold: {player.get('gold', 0)}")

    player["current_hp"] = player_max_hp(player)
    save_game(player)
    return True