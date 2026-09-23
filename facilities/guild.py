# facilities/guild.py
import random
from utils import advance_time
from resources.cities import CITIES
from resources.enemies import ENEMIES, BIOME_RACES
from city_dialogue import service_dialogue
from gui.terminal import term


def generate_bounties(player, city_id):
    """Generate flexible bounties scaling with player level and favor."""
    city = CITIES[city_id]
    biome = city.get("biome", "temperate")
    allowed_races = BIOME_RACES.get(biome, BIOME_RACES["temperate"])
    
    possible_enemies = {k: v for k, v in ENEMIES.items() 
                        if (v.get("race") in allowed_races or v.get("secondary_race") in allowed_races)
                        and not v.get("boss") 
                        and not v.get("super_boss")
                        and not v.get("minion_only")
                        and not v.get("_heroine")
                        and not v.get("_shadow")
                        and not (v.get("secondary_race") == "Storybook" and biome != "wonderland")}
    if not possible_enemies:
        possible_enemies = {k: v for k, v in ENEMIES.items() 
                            if not v.get("boss") and not v.get("super_boss")
                            and not v.get("minion_only")
                            and not v.get("_heroine")
                            and not v.get("_shadow")
                            and not (v.get("secondary_race") == "Storybook" and biome != "wonderland")}
    
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
        
        # ---------- 1. Rank Calculation (Based on Absolute Enemy Level) ----------
        if enemy_level <= 3:
            rank_name = "Bronze"
        elif enemy_level <= 6:
            rank_name = "Silver"
        elif enemy_level <= 9:
            rank_name = "Gold"
        else:
            rank_name = "Platinum"
        
        # ---------- 2. Star Difficulty Calculation (Relative 1–5 Scale) ----------
        level_diff = enemy_level - player_level
        
        # Base rating determined by target level vs player level
        if level_diff < -1:
            base_stars = 1      # Trivial relative to player
        elif level_diff <= 1:
            base_stars = 2      # Even match
        elif level_diff <= 3:
            base_stars = 3      # Challenging
        else:
            base_stars = 4      # Dangerous
            
        # Modifiers for heavy hunting loads and intense time pressure
        kill_modifier = 1 if kills_needed >= 8 else 0
        time_modifier = 1 if deadline <= 2 else 0
        
        stars = clamp(base_stars + kill_modifier + time_modifier, 1, 5)
        
        # Compile into a scannable string expression (e.g., "Gold ★★★")
        difficulty_display = f"{rank_name} " + ("★" * stars)
        # -------------------------------------------------------------------------
        
        bounties.append({
            "id": f"bounty_{random.randint(10000, 99999)}",
            "target_enemy": target,
            "target_name": enemy_data["name"],
            "required": kills_needed,
            "difficulty": difficulty_display,   # Store the formatted dynamic rank + stars
            "days_given": deadline,
            "reward_gold": reward_gold,
            "reward_favor": reward_favor
        })
    
    return bounties

def clamp(value, min_val, max_val):
    """Helper to keep difficulty strictly within boundaries."""
    return max(min_val, min(max_val, value))

def _get_floor_pool(floor, biome, boss=False):
    """
    Mirror get_random_enemy_key() from dungeon.py exactly.
    Normal: level in [max(1, floor-1), floor+3]
    Boss:   level in [floor+1,          floor+5]   (excludes super_boss)
    Falls back to ignoring biome if the biome-filtered pool is empty.
    Returns list of (key, data) tuples — every entry has equal spawn weight.
    """
    allowed_races = set(BIOME_RACES.get(biome, BIOME_RACES["temperate"]))

    def _passes_level(data):
        lvl = data["level"]
        if boss:
            return floor + 1 <= lvl <= floor + 3
        else:
            return max(1, floor - 4) <= lvl <= floor + 3

    def _build(use_race_filter):
        pool = []
        for key, data in ENEMIES.items():
            if data.get("super_boss"):
                continue
            if data.get("minion_only"):
                continue
            if data.get("_heroine"):
                continue
            if data.get("_shadow"):
                continue
            # Only show Storybook enemies when viewing a wonderland dungeon
            if data.get("secondary_race") == "Storybook" and biome != "wonderland":
                continue
            if boss != bool(data.get("boss")):
                continue
            if not _passes_level(data):
                continue
            if use_race_filter and data.get("race") not in allowed_races \
                    and data.get("secondary_race") not in allowed_races:
                continue
            pool.append((key, data))
        return pool

    pool = _build(use_race_filter=True)
    if not pool:
        pool = _build(use_race_filter=False)   # dungeon fallback: drop biome filter
    return pool


def _view_enemy_intelligence(player, city_id):
    """
    Show a paginated floor-by-floor breakdown of what can actually spawn in this dungeon.
    Spawn % mirrors the uniform random selection in get_random_enemy_key().
    Active bounty targets are flagged. Boss pool shown separately below each floor.
    """
    city   = CITIES[city_id]
    biome  = city.get("biome", "temperate")

    bounty_targets = {b["target_enemy"] for b in player.get("active_bounties", [])}

    MAX_FLOOR = 40
    valid_floors = []
    for f in range(1, MAX_FLOOR + 1):
        if _get_floor_pool(f, biome, boss=False) or _get_floor_pool(f, biome, boss=True):
            valid_floors.append(f)

    FLOORS_PER_PAGE = 3
    page            = 0
    total_pages     = max(1, (len(valid_floors) + FLOORS_PER_PAGE - 1) // FLOORS_PER_PAGE)

    while True:
        term.clear()
        term.print(f"=== ENEMY INTELLIGENCE — {city['name'].upper()} ({biome.title()} Dungeon) ===")

        start       = page * FLOORS_PER_PAGE
        page_floors = valid_floors[start : start + FLOORS_PER_PAGE]

        for floor in page_floors:
            normal_pool = _get_floor_pool(floor, biome, boss=False)
            boss_pool   = _get_floor_pool(floor, biome, boss=True)

            # ---- normal enemies ----
            term.print(f"  ══ Floor {floor} ══")
            if normal_pool:
                n = len(normal_pool)
                pct = 100.0 / n
                for key, data in sorted(normal_pool, key=lambda x: x[1]["level"]):
                    tag = "  ★ BOUNTY" if key in bounty_targets else ""
                    term.print(f"    {data['name']:<28} Lv{data['level']:<3} "
                          f"({pct:4.1f}%){tag}")
            else:
                term.print("    (no regular enemies)")

            # ---- boss enemies ----
            if boss_pool:
                b_n  = len(boss_pool)
                b_pct = 100.0 / b_n
                term.print(f"    -- Boss Room --")
                for key, data in sorted(boss_pool, key=lambda x: x[1]["level"]):
                    tag = "  ★ BOUNTY" if key in bounty_targets else ""
                    term.print(f"    {data['name']:<28} Lv{data['level']:<3} "
                          f"({b_pct:4.1f}%){tag}")
            term.print("")

        term.print(f"  Page {page + 1}/{total_pages}")

        nav_options = []
        if page < total_pages - 1:
            nav_options.append("Next Page")
        if page > 0:
            nav_options.insert(0, "Previous Page")
        nav_options.append("Back")
        
        choice_idx = term.menu(nav_options, prompt="Navigation:")
        
        # Map back based on available options
        if page > 0 and page < total_pages - 1:
            # Options: [Prev, Next, Back]
            if choice_idx == 0:
                page -= 1
            elif choice_idx == 1:
                page += 1
            else:
                break
        elif page == 0 and page < total_pages - 1:
            # Options: [Next, Back]
            if choice_idx == 0:
                page += 1
            else:
                break
        elif page > 0:
            # Options: [Prev, Back]
            if choice_idx == 0:
                page -= 1
            else:
                break
        else:
            break


def _ascend_level_cap(player, city_id):
    """Guild ceremony to increase the player's level cap."""
    from leveling import (
        can_ascend_level_cap, get_next_level_cap, get_incomplete_biomes,
        get_biomes_cleared_to_cap, get_required_biomes_for_cap
    )

    current_cap = player.get("level_cap", 10)
    next_cap = get_next_level_cap(current_cap)

    if not can_ascend_level_cap(player):
        incomplete = get_incomplete_biomes(player)
        cleared = len(get_biomes_cleared_to_cap(player, current_cap))
        required = get_required_biomes_for_cap(current_cap)
        term.print(f"\n*** ASCENSION DENIED ***")
        term.print(f"Biomes conquered to Floor {current_cap}: {cleared}/{required}")
        term.print(f"\nUncleared Biomes:")
        for biome_name, example_city, max_floor, required_floor in incomplete:
            term.print(f"  {biome_name} (e.g., {example_city}): Floor {max_floor}/{required_floor}")
        term.print(f"\nClear any city dungeon in {required - cleared} more biome(s) to ascend.")
        term.pause()
        return

    term.print(f"\n{'='*50}")
    term.print("  The Guild Master lays a weathered hand on your shoulder.")
    term.print(f"  'You have conquered the depths of Floor {current_cap}, adventurer.'")
    term.print("  'The seal upon your soul may now be broken.'")
    term.print(f"{'='*50}")

    if not term.confirm("Begin the Ascension ceremony?"):
        term.print("\nThe Guild Master nods solemnly. 'Return when you are ready.'")
        term.pause()
        return

    # Perform ascension
    old_cap = current_cap
    player["level_cap"] = next_cap
    term.print(f"\n{'='*50}")
    term.print(f"*** LEVEL CAP INCREASED: {old_cap} → {next_cap} ***")
    term.print("  The Guild seal erupts in prismatic light!")
    term.print("  Your soul expands, shattering its former limits.")
    term.print(f"  You may now grow to Level {next_cap}!")
    term.print(f"{'='*50}")

    # Reset the global notification for the old cap so the next milestone can trigger
    notified = player.get("ascension_notified", {})
    global_key = f"global_{old_cap}"
    if global_key in notified:
        del notified[global_key]

    advance_time(player, 30)
    term.pause()


def _legendary_rewards(player, city_id):
    """Guild legacy rewards: Sky Piercer for defeating 5 distinct superbosses.

    The option always exists but is rejected unless the requirement is met.
    """
    term.clear()
    required = 5
    progress = len(set(player.get("defeated_superbosses", [])))

    term.print("=== GUILD LEGACY REWARDS ===")
    term.print("The Guild Master unrolls a ledger older than the guild itself.")
    term.print("")
    term.print("  ☁️  Sky Piercer — unique accessory")
    term.print("     Executes non-Super-Boss enemies left at low HP by your attacks.")
    term.print(f"     Requirement: defeat {required} different Super Bosses")
    term.print(f"     Progress: {min(progress, required)}/{required}")

    if player.get("sky_piercer_claimed"):
        term.print("")
        term.print("*** CLAIM REJECTED ***")
        term.print("The Sky Piercer already rests with you. The ledger is closed.")
        term.pause()
        return

    if progress < required:
        term.print("")
        term.print("*** CLAIM REJECTED ***")
        term.print(f"The ledger is incomplete. Defeat {required - progress} more different Super Bosses to prove your worth.")
        term.pause()
        return

    from resources.items import build_item
    from inventory import add_item_to_inventory
    item = build_item("sky_piercer")
    add_item_to_inventory(player, item)
    player["sky_piercer_claimed"] = True
    term.print("")
    term.print("The Guild Master bows. 'Take it. The sky will not forget your name.'")
    term.print(f"*** Received unique accessory: {item['name']} ***")
    term.pause()


def _traveling_merchant(player):
    """Market Day event: a traveling merchant sells wares inside the guild hall."""
    from facilities.travel_events import (
        _random_item_id, _merchant_stock_rarity, _merchant_price,
        _charisma_discount, _item_stat_line,
    )
    from resources.items import build_item
    from inventory import add_item_to_inventory

    term.clear()
    term.print("=== TRAVELING MERCHANT ===")
    term.print('  A road-worn merchant has set up a stall in the corner of the guild hall.')
    term.print('  "Wares! Quality goods — fair price for a fellow traveler!"\n')

    # Build stock: filtered item pool, floor-influenced rarity (no legendaries)
    stock = []
    for _ in range(random.randint(2, 3)):
        item_id     = _random_item_id()
        rarity      = _merchant_stock_rarity(player)
        item        = build_item(item_id, rarity)
        your_price, road_price = _merchant_price(player, item)
        stock.append((item, your_price, road_price))

    # Display
    cha_disc = _charisma_discount(player)
    gold_info = f"  Your gold: {player.get('gold', 0)}g"
    if cha_disc > 0:
        gold_info += f"  |  Charisma discount: {cha_disc:.0f}%"
    term.print(gold_info)

    term.print("")
    options = []
    for item, your_price, road_price in stock:
        stat = _item_stat_line(item)
        if cha_disc > 0 and your_price < road_price:
            price_str = f"{your_price}g  (road: {road_price}g)"
        else:
            price_str = f"{your_price}g"
        term.print(f"  {len(options) + 1}. {item['name']}  {stat}  —  {price_str}")
        options.append(f"Buy: {item['name']}  {stat}  —  {your_price}g")
    options.append("Sell an item")
    options.append("Leave the stall")

    while True:
        choice = term.menu(options, prompt="What will you do?",
                           allow_cancel=True, cancel_label="Leave the stall")

        if choice == -1 or choice == len(options) - 1:
            term.print('  "Safe roads, traveler!"')
            break

        if choice == len(options) - 2:  # Sell
            _merchant_sell(player)
            break

        if 0 <= choice < len(stock):
            item, your_price, _ = stock[choice]
            if player.get("gold", 0) >= your_price:
                player["gold"] -= your_price
                if add_item_to_inventory(player, item.copy()):
                    term.print(f'  You purchase [{item["name"]}] for {your_price}g.')
                    term.print('  "Pleasure doing business!" The merchant tips his hat.')
                else:
                    term.print('  "Your bag looks stuffed, friend. Make room and come back!"')
                    player["gold"] += your_price  # refund
            else:
                term.print(f'  "You\'re {your_price - player.get("gold", 0)}g short, friend."')
        break

    term.pause()


def _merchant_sell(player):
    """Sell items to the guild-hall traveling merchant at road rates."""
    from facilities.travel_events import _sell_price, _item_stat_line
    from inventory import remove_item_by_reference

    inv = player.get("inventory", [])
    if not inv:
        term.print('  "Nothing I want off you — yet." The merchant shrugs.')
        term.pause()
        return

    term.print("\n  The merchant eyes your pack with practiced interest.")
    term.print("  (Road sell rate: ~75% of city shop value)\n")

    for i, item in enumerate(inv):
        unit_price  = _sell_price(item, player)
        count       = item.get("count", 1)
        stack_price = unit_price * count
        count_str   = f" (x{count})" if count > 1 else ""
        term.print(f"  {i+1:>2}. {item['name']}{count_str}  {_item_stat_line(item)}  —  {stack_price}g")

    try:
        raw = term.input("\n  Sell which item number? (0 to cancel): ")
        idx = int(raw.strip()) - 1
        if 0 <= idx < len(inv):
            item = inv[idx]
            gold = _sell_price(item, player) * item.get("count", 1)
            remove_item_by_reference(player, item, item.get("count", 1))
            player["gold"] = player.get("gold", 0) + gold
            term.print(f'  Sold [{item["name"]}] for {gold}g. "A fair deal for the road!"')
        else:
            term.print('  "Changing your mind is free."')
    except (ValueError, IndexError):
        term.print("  Nothing sold.")

    term.pause()


def guild_service(player, city_id="solmere"):
    term.clear()
    
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
        term.clear()
        term.print(f"=== {CITIES[city_id]['name'].upper()} GUILD HALL ===")
        service_dialogue(city_id, "receptionist", "enter")
        term.print(f"Favor: {player['favor'].get(city_id, 0)} | Gold: {player.get('gold', 0)}")
        
        from leveling import can_ascend_level_cap, get_next_level_cap
        can_ascend = can_ascend_level_cap(player)
        if can_ascend:
            term.print("\n  🌟 ASCENSION READY! Your power yearns to break through!")

        merchant_active = bool(player.get("daily_effects", {}).get("traveling_merchant"))
        if merchant_active:
            term.print("\n  🏪 A traveling merchant has set up a stall in the corner of the hall!")

        options = [
            "View Bounty Board",
            "Manage Active Bounties",
            "Enemy Intelligence",
            "Ascend Level Cap",
            "Legendary Rewards",
        ]
        if merchant_active:
            options.append("Visit the Traveling Merchant")
        options.append("Leave")

        choice = term.menu(options, prompt="What would you like to do?")

        if choice == 0:
            _view_bounty_board(player, city_id, stock_key)
        elif choice == 1:
            _manage_bounties(player, city_id)
        elif choice == 2:
            _view_enemy_intelligence(player, city_id)
        elif choice == 3:
            _ascend_level_cap(player, city_id)
        elif choice == 4:
            _legendary_rewards(player, city_id)
        elif merchant_active and choice == 5:
            _traveling_merchant(player)
        elif choice == len(options) - 1 or choice == -1:
            service_dialogue(city_id, "receptionist", "leave")
            advance_time(player, 15)
            break

def _view_bounty_board(player, city_id, stock_key):
    while True:
        term.clear()
        term.print("=== BOUNTY BOARD ===")
        bounties = player.get(stock_key, [])
        if not bounties:
            term.print("No bounties available. Check back when the board refreshes.")
            term.pause()
            break
        else:
            term.print(f"Board refreshes on Day: {player.get(f'bounty_refresh_day_{city_id}')}\n")
            options = []
            for i, b in enumerate(bounties):
                term.print(f"{i+1}. Hunt {b['required']} {b['target_name']} (Difficulty {b['difficulty']})")
                term.print(f"   Reward: {b['reward_gold']}g, +{b['reward_favor']} Favor | Deadline: {b['days_given']} Days")
                options.append(f"Hunt {b['target_name']} — {b['reward_gold']}g + {b['reward_favor']} Favor")
        
        choice = term.menu(options, prompt="Select a bounty to accept:", allow_cancel=True, cancel_label="Back")
        if choice < 0:
            break
        elif 0 <= choice < len(bounties):
            bounty = bounties.pop(choice)
            bounty["current"] = 0
            bounty["deadline"] = player.get("day", 1) + bounty["days_given"]
            bounty["city"] = city_id
            player["active_bounties"].append(bounty)
            term.print(f"Accepted bounty to hunt {bounty['target_name']}!")
            advance_time(player, 5)
            term.pause()
            break

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
        term.clear()
        term.print("=== ACTIVE BOUNTIES ===")
        active = player.get("active_bounties", [])
        current_day = player.get("day", 1)
        
        # Clean up expired bounties
        valid_bounties = []
        for b in active:
            if current_day > b["deadline"]:
                term.print(f"FAILED: Bounty for {b['target_name']} has expired!")
            else:
                valid_bounties.append(b)
        player["active_bounties"] = valid_bounties
        active = valid_bounties

        if not active:
            term.print("You have no active bounties.")
            term.pause()
            break
            
        options = []
        for i, b in enumerate(active):
            status = "READY TO TURN IN" if b["current"] >= b["required"] else f"{b['current']}/{b['required']}"
            days_left = b["deadline"] - current_day
            term.print(f"{i+1}. {b['target_name']} [{status}] - Expires in {days_left} days (Issuer: {CITIES[b['city']]['name']})")
            options.append(f"{b['target_name']} [{status}]")
            
        choice = term.menu(options, prompt="Select bounty to turn in:", allow_cancel=True, cancel_label="Back")
        if choice < 0:
            break
        elif 0 <= choice < len(active):
            b = active[choice]
            if b["city"] != city_id:
                term.print(f"You must return to {CITIES[b['city']]['name']} to turn this in.")
                term.pause()
            elif b["current"] < b["required"]:
                term.print("Bounty conditions not met yet.")
                term.pause()
            else:
                # Event bonuses: Bounty Rush (+50% rewards) and New Moon Festival (+25% favor)
                daily        = player.get("daily_effects", {})
                gold_reward  = b["reward_gold"]
                favor_reward = b["reward_favor"]
                notes = []
                if daily.get("bounty_bonus"):
                    gold_reward  = int(gold_reward * 1.5)
                    favor_reward = int(favor_reward * 1.5)
                    notes.append("Bounty Rush +50%")
                if daily.get("favor_bonus"):
                    favor_reward += int(b["reward_favor"] * 0.25)
                    notes.append("New Moon +25% favor")
                note = f" ({', '.join(notes)})" if notes else ""
                term.print(f"Bounty Complete! Earned {gold_reward} gold and {favor_reward} Favor in {CITIES[b['city']]['name']}.{note}")
                player["gold"] = player.get("gold", 0) + gold_reward
                player["favor"][city_id] = player["favor"].get(city_id, 0) + favor_reward
                active.pop(choice)
                advance_time(player, 10)
                term.pause()