import random
from resources.enemies import ENEMIES
from resources.items import build_item, ITEMS, ITEM_RARITY
from resources.cities import CITIES
from combat import combat, player_con_mod
from superboss_combat import combat_broodmother, combat_slitcurrent
from character import player_max_hp
from save_load import save_game
from utils import clear_screen, advance_time, get_difficulty_multiplier_from_time, format_time
from inventory_ui import manage_inventory_menu
from leveling import gain_exp


def get_random_enemy_key(floor, boss=False):
    """Pick a random enemy suitable for the current floor."""
    pool = []
    for key, data in ENEMIES.items():
        # Skip super bosses on regular floors
        if floor % 10 != 0 and data.get("super_boss", False):
            continue
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
    """Create a list of rooms, where each room contains a list of enemy keys (up to 5)."""
    rooms = []
    max_enemies = min(5, floor)  # Max group size matches floor level up to a hard cap of 5

    # Generate 4 normal rooms
    for _ in range(4):
        num_enemies = random.randint(1, max_enemies)
        room_enemies = [get_random_enemy_key(floor, boss=False) for _ in range(num_enemies)]
        rooms.append(room_enemies)

    # Generate 1 Boss Room (Boss + scaled minion pack up to max cap of 5 characters total)
    boss_room = [get_random_enemy_key(floor, boss=True)]
    num_minions = random.randint(0, min(4, floor - 1))
    for _ in range(num_minions):
        boss_room.append(get_random_enemy_key(floor, boss=False))
    rooms.append(boss_room)

    return rooms


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
        print(f"You found: {item['name']}!")
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
    
    # ----- SUPER BOSS ENCOUNTER (every 10th floor) -----
    if floor % 10 == 0:
        print("\n" + "="*50)
        print("⚠️  A dark, suffocating energy fills the air...")
        if (floor // 10) % 2 == 0:
            print("The walls are covered in dense, toxic cobwebs.")
        else:
            print("Reality itself frays... distorted dream fragments float everywhere.")
        print("You have stumbled directly into a SUPER BOSS ARENA!")
        print("="*50)
        input("Press Enter to face the horror...")

        # Combat loop – cannot flee (if flee, restart combat)
        while True:
            advance_time(player, 60)   # time passes
            if (floor // 10) % 2 == 0:
                result = combat_broodmother(player)
            else:
                result = combat_slitcurrent(player)
            if result == "victory":
                # Reward
                super_boss_exp = 500 + (floor * 50)
                super_boss_gold = 300 + (floor * 30)
                player["gold"] = player.get("gold", 0) + super_boss_gold
                print(f"\n🏆 Super Boss Defeated! Bonus: +{super_boss_gold} gold, +{super_boss_exp} XP!")
                gain_exp(player, super_boss_exp)
                
                # Full heal and save (outer loop will increment floor and heal again, but that's fine)
                player["current_hp"] = player_max_hp(player)
                save_game(player)
                return True   # floor cleared, outer loop will handle floor+1 and full heal
            elif result == "fled":
                print("You cannot flee from a milestone Super Boss! The webs trap you.")
                input("Press Enter to continue the fight...")
                continue
            elif result == "dead":
                return False

    # ----- NORMAL FLOORS (non‑milestone) -----
    print(f"\n=== DESCENDING INTO DUNGEON FLOOR {floor} ===")
    input("Press Enter to begin your descent...")

    rooms = generate_floor(floor)
    total_rooms = len(rooms)

    for i, enemy_keys in enumerate(rooms):
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
            result = combat(player, enemy_keys)

            if result == "victory":
                print("\n--- Room Victory Rewards ---")
                for enemy_key in enemy_keys:
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
                print(f"\nYou catch your breath and recover {heal} HP.")

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
                print("You retreat from the room. The enemies remain.")
                continue
            elif result == "dead":
                print("Your adventure ends here...")
                return False

    # Floor cleared (normal)

    if player.get("active_buffs"):
        orig_len = len(player["active_buffs"])
        player["active_buffs"] = [b for b in player["active_buffs"] if b.get("type") != "blessing"]
        if len(player["active_buffs"]) < orig_len:
            print("\nYour divine temple blessing has worn off as you transition floors.")
    
    # Advance time by 1 hour for floor completion
    current_time = advance_time(player, 60)
    
    print(f"Current time: {current_time} | Gold: {player.get('gold', 0)}")

    player["current_hp"] = player_max_hp(player)
    save_game(player)
    return True