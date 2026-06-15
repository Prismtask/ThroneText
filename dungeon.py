import random
from resources.enemies import ENEMIES, BIOME_RACES
from resources.items import build_item, ITEMS, ITEM_RARITY
from resources.cities import CITIES
from combat.combat_engine import combat
from combat.stats import player_con_mod
from combat.broodmother import combat_broodmother 
from combat.slitcurrent import combat_slitcurrent
from combat.sylvana import combat_sylvana
from combat.ignis import combat_ignis
from character import player_max_hp
from save_load import save_game
from utils import clear_screen, advance_time, get_difficulty_multiplier_from_time, format_time
from inventory_ui import manage_inventory_menu
from leveling import gain_exp


def get_random_enemy_key(floor, boss=False, region=None):
    """Pick a random enemy suitable for the current floor."""
    pool = []
    allowed_races = None
    if region and region in BIOME_RACES:
        allowed_races = set(BIOME_RACES[region])
    for key, data in ENEMIES.items():
        # skip super bosses on non‑milestone floors
        if floor % 10 != 0 and data.get("super_boss", False):
            continue
        if boss and not data.get("boss", False):
            continue
        if boss:
            # TWEAK HERE IF YOU WANT BOSSES TO BE MORE SPREAD OUT TOO
            if not (data["level"] >= floor + 1 and data["level"] <= floor + 3):
                continue
        else:
            # TWEAK HERE: Changed 'floor - 1' to 'floor - 6' to allow lower levels on higher floors
            if not (data["level"] >= max(1, floor - 4) and data["level"] <= floor + 3):
                continue

        # region filter
        if allowed_races:
            enemy_race = data.get("race")
            if enemy_race not in allowed_races:
                continue

        pool.append(key)

    if not pool:
        # fallback – ignore region but keep level constraints
        # TWEAK HERE: Changed 'floor - 2' to 'floor - 6' to match the new spread
        pool = [k for k, d in ENEMIES.items()
            if (d.get("boss", False) == boss)
            and (d["level"] >= max(1, floor - 6))
            and not (floor % 10 != 0 and d.get("super_boss", False))]
    if not pool:
        pool = [k for k, d in ENEMIES.items() if d.get("boss", False) == boss]

    return random.choice(pool)


def generate_floor(floor, region=None):
    rooms = []
    max_enemies = min(5, floor)

    for _ in range(4):
        num_enemies = random.randint(1, max_enemies)
        room_enemies = [get_random_enemy_key(floor, boss=False, region=region)
                        for _ in range(num_enemies)]
        rooms.append(room_enemies)

    boss_room = [get_random_enemy_key(floor, boss=True, region=region)]
    num_minions = random.randint(0, min(4, floor - 1))
    for _ in range(num_minions):
        boss_room.append(get_random_enemy_key(floor, boss=False, region=region))
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

    # ----- Determine current dungeon region -----
    # If we already have a region stored, use it (e.g. after loading)
    # Otherwise, derive from the city the player is in (if any)
    if "dungeon_region" not in player or player["dungeon_region"] is None:
        current_city = player.get("location")
        if current_city and current_city != "dungeon":
            city_data = CITIES.get(current_city, CITIES["solmere"])
            player["dungeon_region"] = city_data.get("biome", "temperate")
        else:
            player["dungeon_region"] = "temperate"

    region = player["dungeon_region"]
    
    # ----- SUPER BOSS ENCOUNTER (every 10th floor) -----
    if floor % 10 == 0:
        if "superboss_seed" not in player:
            player["superboss_seed"] = random.randint(1, 999999)
        print("\n" + "="*50)
        print("⚠️  A dark, suffocating energy fills the air...")
        rng = random.Random(player["superboss_seed"] + floor)
        tier = rng.randint(0, 3)
        if tier == 0:
            print("The walls are covered in dense, toxic cobwebs.")
        elif tier == 1:
            print("Reality itself frays... distorted dream fragments float everywhere.")
        elif tier == 2:
            print("Every surface becomes a mirror. You see a thousand versions of yourself — all afraid.")
        elif tier == 3:
            print("The air shimmers with heat haze. The stone floor has begun to glow.")
        print("You have stumbled directly into a SUPER BOSS ARENA!")
        print("="*50)
        input("Press Enter to face the horror...")

        # Combat loop – cannot flee (if flee, restart combat)
        while True:
            advance_time(player, 60)   # time passes
            if tier == 0:
                result = combat_broodmother(player)
            elif tier == 1:
                result = combat_slitcurrent(player)
            elif tier == 2:
                result = combat_sylvana(player)
            elif tier == 3:
                result = combat_ignis(player)
            if result == "victory":
                # Reward
                super_boss_exp = 500 + (floor * 50)
                super_boss_gold = 300 + (floor * 30)
                player["gold"] = player.get("gold", 0) + super_boss_gold
                print(f"\n Super Boss Defeated! Bonus: +{super_boss_gold} gold, +{super_boss_exp} XP!")
                gain_exp(player, super_boss_exp)
                
                # Full heal and save (outer loop will increment floor and heal again, but that's fine)
                player["current_hp"] = player_max_hp(player)
                save_game(player)
                return True   # floor cleared, outer loop will handle floor+1 and full heal
            elif result == "fled":
                print("You cannot flee from a milestone Super Boss!")
                input("Press Enter to continue the fight...")
                continue
            elif result == "dead":
                return False

    # ----- NORMAL FLOORS (non‑milestone) -----
    print(f"\n=== DESCENDING INTO {region.upper()} DUNGEON – FLOOR {floor} ===")
    input("Press Enter to begin...")
    clear_screen()
    rooms = generate_floor(floor, region=region)
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
            result = combat(player, enemy_keys, floor=floor, room_num=i+1, total_rooms=total_rooms)

            if result == "victory":
                print("\n--- Room Victory Rewards ---")
                for enemy_key in enemy_keys:
                    enemy_level = ENEMIES[enemy_key]["level"]
                    gain_exp(player, enemy_level * 12)
                    add_drop_to_inventory(player, enemy_level)
                    add_gold_drop(player, enemy_key)
                    
                    # BOUNTY TRACKING:
                    if "active_bounties" in player:
                        for b in player["active_bounties"]:
                            if b["target_enemy"] == enemy_key and b["current"] < b["required"]:
                                b["current"] += 1
                                if b["current"] == b["required"]:
                                    print(f"★ Bounty objective complete: Hunt {b['required']} {b['target_name']}!")

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
                print("You flee from the dungeon and return to the city.")
                input("Press Enter to continue...")
                # Go back to the city you came from
                origin = player.get("origin_city", "solmere")
                player["location"] = origin
                # Do not clear the floor; next descent will restart this floor
                return "fled"
            elif result == "dead":
                print("Your adventure ends here...")
                return False

    # Floor cleared (normal)

    if player.get("active_buffs"):
        orig_len = len(player["active_buffs"])
        player["active_buffs"] = [b for b in player["active_buffs"] if b.get("type") != "blessing"]
        if len(player["active_buffs"]) < orig_len:
            print("\nYour divine temple blessing has worn off as you transition floors.")
    if player.get("training_buff"):
        player["training_buff"]["expires_after"] -= 1
        if player["training_buff"]["expires_after"] <= 0:
            del player["training_buff"]
            print("\nYour barracks training exhaustion catches up to you. The strength buff has worn off.")

    # Advance time by 1 hour for floor completion
    current_time = advance_time(player, 60)
    
    print(f"Current time: {current_time} | Gold: {player.get('gold', 0)}")

    player["current_hp"] = player_max_hp(player)
    save_game(player)
    return True