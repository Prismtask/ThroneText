# facilities/guild.py
import random
from utils import clear_screen, advance_time
from resources.cities import CITIES
from resources.enemies import ENEMIES, BIOME_RACES
from city_dialogue import service_dialogue


def generate_bounties(player, city_id):
    """Generate flexible bounties scaling with player level and favor."""
    city = CITIES[city_id]
    biome = city.get("biome", "temperate")
    allowed_races = BIOME_RACES.get(biome, BIOME_RACES["temperate"])
    
    possible_enemies = {k: v for k, v in ENEMIES.items() 
                        if v.get("race") in allowed_races 
                        and not v.get("boss") 
                        and not v.get("super_boss")}
    if not possible_enemies:
        possible_enemies = {k: v for k, v in ENEMIES.items() 
                            if not v.get("boss") and not v.get("super_boss")}
    
    player_level = player.get("level", 1)
    favor = player.get("favor", {}).get(city_id, 0)
    
    level_offset = min(5, 2 + favor // 30)
    min_level = max(1, player_level - 2)
    max_level = player_level + level_offset
    
    candidates = [k for k, v in possible_enemies.items() 
                  if min_level <= v["level"] <= max_level]
    
    num_bounties = min(7, 2 + (favor // 20))
    bounties = []
    
    for _ in range(num_bounties):
        if not candidates:
            candidates = list(possible_enemies.keys())
        target = random.choice(candidates)
        enemy_data = ENEMIES[target]
        enemy_level = enemy_data["level"]
        
        base_kills = random.randint(3, 6) + (favor // 25)
        kills_needed = max(2, int(base_kills * random.uniform(0.8, 1.5)))
        
        deadline_base = 7 - (favor // 25) - (kills_needed // 6)
        deadline = max(1, deadline_base)
        tightness = 1.0 + (max(0, 6 - deadline) * 0.15)
        
        base_gold_per_kill = enemy_level * random.randint(8, 12)
        favor_mult = 1.0 + (favor / 100)
        reward_gold = int(kills_needed * base_gold_per_kill * favor_mult * tightness)
        reward_favor = int((5 + random.randint(0, 10)) * (0.8 + tightness * 0.5))
        
        # ---------- Difficulty calculation (1–20) ----------
        # Level difference (enemy - player), clamped and mapped to 1–10
        level_diff = enemy_level - player_level
        # Clamp to [-5, +10]
        clamped_diff = max(-5, min(10, level_diff))
        # Map to 1–10: -5 → 1, 0 → 5, +10 → 10
        level_factor = int(5 + (clamped_diff * 0.5))
        level_factor = max(1, min(10, level_factor))
        
        # Kills factor: kills_needed / 5, max 5
        kills_factor = min(5, kills_needed / 5)
        
        # Deadline factor: inverse of deadline (1–7) → 5 down to 0
        deadline_factor = max(0, 5 - deadline)
        
        total = level_factor + kills_factor + deadline_factor
        difficulty = int(max(1, min(20, round(total))))
        # ---------------------------------------------------
        
        bounties.append({
            "id": f"bounty_{random.randint(10000, 99999)}",
            "target_enemy": target,
            "target_name": enemy_data["name"],
            "required": kills_needed,
            "difficulty": difficulty,   # Now 1–20
            "days_given": deadline,
            "reward_gold": reward_gold,
            "reward_favor": reward_favor
        })
    
    return bounties

def guild_service(player, city_id="solmere"):
    clear_screen()
    
    if "favor" not in player:
        player["favor"] = {}
    if city_id not in player["favor"]:
        player["favor"][city_id] = 0
        
    if "active_bounties" not in player:
        player["active_bounties"] = []
        
    day_key = f"bounty_refresh_day_{city_id}"
    stock_key = f"bounty_board_{city_id}"
    current_day = player.get("day", 1)
    
    # 7-day refresh logic
    if stock_key not in player or current_day >= player.get(day_key, 0):
        player[stock_key] = generate_bounties(player, city_id)
        player[day_key] = current_day + 7
        
    while True:
        clear_screen()
        print(f"=== {CITIES[city_id]['name'].upper()} GUILD HALL ===")
        service_dialogue(city_id, "receptionist", "enter")
        print(f"Favor: {player['favor'].get(city_id, 0)} | Gold: {player.get('gold', 0)} | Day: {player.get('day', 1)}")
        print("1. View Bounty Board")
        print("2. Manage Active Bounties")
        print("3. Leave")
        
        choice = input("Choice: ").strip()
        if choice == "1":
            _view_bounty_board(player, city_id, stock_key)
        elif choice == "2":
            _manage_bounties(player, city_id)
        elif choice == "3":
            service_dialogue(city_id, "receptionist", "leave")
            advance_time(player, 15)
            break

def _view_bounty_board(player, city_id, stock_key):
    while True:
        clear_screen()
        print("=== BOUNTY BOARD ===")
        bounties = player.get(stock_key, [])
        if not bounties:
            print("No bounties available. Check back when the board refreshes.")
        else:
            print(f"Board refreshes on Day: {player.get(f'bounty_refresh_day_{city_id}')}\n")
            for i, b in enumerate(bounties):
                print(f"{i+1}. Hunt {b['required']} {b['target_name']} (Difficulty {b['difficulty']})")
                print(f"   Reward: {b['reward_gold']}g, +{b['reward_favor']} Favor | Deadline: {b['days_given']} Days")
        
        choice = input("\n[Number] to take bounty | [B]ack\nChoice: ").strip().lower()
        if choice == 'b':
            break
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(bounties):
                bounty = bounties.pop(idx)
                bounty["current"] = 0
                bounty["deadline"] = player.get("day", 1) + bounty["days_given"]
                bounty["city"] = city_id
                player["active_bounties"].append(bounty)
                print(f"Accepted bounty to hunt {bounty['target_name']}!")
                advance_time(player, 5)
                input("Press Enter...")

def check_bounty_expiry(player):
    """Remove expired bounties and return list of expired ones."""
    if "active_bounties" not in player:
        return []
    expired = []
    remaining = []
    current_day = player.get("day", 1)
    for bounty in player["active_bounties"]:
        if current_day > bounty["deadline"]:
            expired.append(bounty)
        else:
            remaining.append(bounty)
    player["active_bounties"] = remaining
    return expired

def _manage_bounties(player, city_id):
    while True:
        clear_screen()
        print("=== ACTIVE BOUNTIES ===")
        active = player.get("active_bounties", [])
        current_day = player.get("day", 1)
        
        # Clean up expired bounties
        valid_bounties = []
        for b in active:
            if current_day > b["deadline"]:
                print(f"FAILED: Bounty for {b['target_name']} has expired!")
            else:
                valid_bounties.append(b)
        player["active_bounties"] = valid_bounties
        active = valid_bounties

        if not active:
            print("You have no active bounties.")
            input("Press Enter...")
            break
            
        for i, b in enumerate(active):
            status = "READY TO TURN IN" if b["current"] >= b["required"] else f"{b['current']}/{b['required']}"
            days_left = b["deadline"] - current_day
            print(f"{i+1}. {b['target_name']} [{status}] - Expires in {days_left} days (Issuer: {CITIES[b['city']]['name']})")
            
        choice = input("\n[Number] to turn in completed bounty | [B]ack\nChoice: ").strip().lower()
        if choice == 'b':
            break
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(active):
                b = active[idx]
                if b["city"] != city_id:
                    print(f"You must return to {CITIES[b['city']]['name']} to turn this in.")
                    input("Press Enter...")
                elif b["current"] < b["required"]:
                    print("Bounty conditions not met yet.")
                    input("Press Enter...")
                else:
                    print(f"Bounty Complete! Earned {b['reward_gold']} gold and {b['reward_favor']} Favor in {CITIES[b['city']]['name']}.")
                    player["gold"] = player.get("gold", 0) + b["reward_gold"]
                    player["favor"][city_id] = player["favor"].get(city_id, 0) + b["reward_favor"]
                    active.pop(idx)
                    advance_time(player, 10)
                    input("Press Enter...")