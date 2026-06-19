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
from combat.yinglong import combat_yinglong
from character import player_max_hp
from save_load import save_game
from utils import clear_screen, advance_time, get_difficulty_multiplier_from_time, format_time
from inventory_ui import manage_inventory_menu
from leveling import gain_exp


def get_random_enemy_key(floor, boss=False, region=None):
    """Pick a random enemy suitable for the current floor (1‑40)."""
    pool = []
    allowed_races = None
    if region and region in BIOME_RACES:
        allowed_races = set(BIOME_RACES[region])

    for key, data in ENEMIES.items():
        # Skip superbosses on non‑milestone floors
        if floor % 10 != 0 and data.get("super_boss", False):
            continue
        if boss != data.get("boss", False):
            continue

        # Level constraints
        if boss:
            # Boss: 1–3 levels above current floor
            if not (data["level"] >= floor + 1 and data["level"] <= floor + 3):
                continue
        else:
            # Normal: 6 levels below up to 3 levels above, but never below 1 or above 40
            if not (data["level"] >= max(1, floor - 6) and data["level"] <= min(40, floor + 3)):
                continue

        # Region filter
        if allowed_races:
            enemy_race = data.get("race")
            if enemy_race not in allowed_races:
                continue

        pool.append(key)

    # Fallback – ignore region but keep level and boss/superboss constraints
    if not pool:
        for key, data in ENEMIES.items():
            if floor % 10 != 0 and data.get("super_boss", False):
                continue
            if boss != data.get("boss", False):
                continue
            if boss:
                if not (data["level"] >= floor + 1 and data["level"] <= floor + 3):
                    continue
            else:
                if not (data["level"] >= max(1, floor - 6) and data["level"] <= min(40, floor + 3)):
                    continue
            pool.append(key)

    if not pool:
        # Ultimate fallback – any enemy of the right boss type
        pool = [k for k, d in ENEMIES.items() if d.get("boss", False) == boss]
    
    if not pool:
        # Emergency fallback – any enemy at all
        pool = list(ENEMIES.keys())
    
    if not pool:
        # Critical error – no enemies loaded
        raise RuntimeError(
            f"No enemies found! ENEMIES has {len(ENEMIES)} entries. "
            f"floor={floor}, boss={boss}, region={region}"
        )

    return random.choice(pool)


def generate_floor(floor, region=None):
    rooms = []
    max_enemies = min(5, floor)

    for _ in range(4):
        num_enemies = random.randint(1, max_enemies)
        room_enemies = [get_random_enemy_key(floor, boss=False, region=region)
                        for _ in range(num_enemies)]
        rooms.append(room_enemies)

    # Every 5th floor gets a True Boss. Otherwise, pick a normal enemy to act as the floor boss
    is_true_boss_floor = (floor % 5 == 0)
    boss_room = [get_random_enemy_key(floor, boss=is_true_boss_floor, region=region)]
    
    num_minions = random.randint(0, min(4, floor - 1))
    for _ in range(num_minions):
        boss_room.append(get_random_enemy_key(floor, boss=False, region=region))
    rooms.append(boss_room)

    return rooms

def roll_drop(enemy_level):
    if random.random() > 0.50:
        return None

    rarities = ["common", "uncommon", "rare", "epic", "legendary"]

    if enemy_level <= 5:
        weights = [0.45, 0.35, 0.15, 0.05, 0.00]
    elif enemy_level <= 10:
        weights = [0.30, 0.35, 0.22, 0.10, 0.03]
    elif enemy_level <= 20:
        weights = [0.20, 0.30, 0.28, 0.15, 0.07]
    elif enemy_level <= 30:
        weights = [0.10, 0.25, 0.30, 0.20, 0.15]
    else:  # 31–40
        weights = [0.05, 0.20, 0.25, 0.30, 0.20]

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


def _ensure_city_floors(player, city_id):
    """Guarantee city_floors[city_id] exists, migrating legacy saves if needed."""
    if "city_floors" not in player:
        player["city_floors"] = {}
    if city_id not in player["city_floors"]:
        # Old save: inherit the global floor/max_floor for the origin city only.
        if player.get("origin_city") == city_id or player.get("location") in (city_id, "dungeon"):
            player["city_floors"][city_id] = {
                "floor":     player.get("floor", 1),
                "max_floor": player.get("max_floor", 1),
            }
        else:
            player["city_floors"][city_id] = {"floor": 1, "max_floor": 1}


def explore_dungeon(player):
    """Main dungeon loop. Clears one floor. Returns False if player dies."""
    # ── Resolve origin city and ensure per-city progress record exists ─────
    origin_city = player.get("origin_city", "solmere")
    _ensure_city_floors(player, origin_city)
    city_prog = player["city_floors"][origin_city]

    # player["floor"] is the transient cursor set by city.py before entry;
    # treat it as authoritative for this run.
    floor = city_prog["floor"]

    # ----- Determine current dungeon region -----
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
        print("\n" + "="*50)
        print("⚠️  A dark, suffocating energy fills the air...")
        
        # 1. Initialize or refill the superboss pool if it's empty or missing
        if not player.get("superboss_pool"):
            pool = [0, 1, 2, 3, 4]
            # Use seed + floor to keep the shuffle consistent per run/floor 
            # but fall back to a random seed if missing to prevent crashes
            rng = random.Random(player.get("superboss_seed", random.randint(1, 99999)) + floor)
            rng.shuffle(pool)
            player["superboss_pool"] = pool
            
        # 2. Peek at the next boss in the pool (do not remove until defeated!)
        tier = player["superboss_pool"][0]
        
        if tier == 0:
            print("The walls are covered in dense, toxic cobwebs.")
        elif tier == 1:
            print("Reality itself frays... distorted dream fragments float everywhere.")
        elif tier == 2:
            print("Every surface becomes a mirror. You see a thousand versions of yourself — all afraid.")
        elif tier == 3:
            print("The air shimmers with heat haze. The stone floor has begun to glow.")
        elif tier == 4:
            print("The sky above the dungeon cracks open. Something vast descends.")
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
            elif tier == 4:
                result = combat_yinglong(player)
                
            if result == "victory":
                # 3. Remove the defeated boss from the pool so it won't spawn again until reshuffled
                player["superboss_pool"].pop(0)
                
                # Reward
                super_boss_exp = 500 + (floor * 50)
                super_boss_gold = 300 + (floor * 30)
                player["gold"] = player.get("gold", 0) + super_boss_gold
                print(f"\n Super Boss Defeated! Bonus: +{super_boss_gold} gold, +{super_boss_exp} XP!")
                gain_exp(player, super_boss_exp)

                # Sync per-city progress
                next_floor = floor + 1
                city_prog["floor"]     = next_floor
                city_prog["max_floor"] = max(city_prog["max_floor"], next_floor)

                # Full heal and save
                player["current_hp"] = player_max_hp(player)
                save_game(player)
                return True   # floor cleared, outer loop will handle full heal
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

    # ── Sync per-city floor progress ────────────────────────────────────────
    # Advance the city record to the next floor.  main.py will also do
    # player["floor"] += 1, but we mirror it here so city_prog stays in sync
    # whether control returns through main.py or any other path.
    next_floor = floor + 1
    city_prog["floor"]     = next_floor
    city_prog["max_floor"] = max(city_prog["max_floor"], next_floor)

    # Advance time by 1 hour for floor completion
    current_time = advance_time(player, 60)

    print(f"Current time: {current_time} | Gold: {player.get('gold', 0)}")

    player["current_hp"] = player_max_hp(player)
    save_game(player)
    return True