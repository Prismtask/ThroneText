# facilities/guild.py
import random
import karma
import karma_dialogue
from utils import advance_time
from resources.cities import CITIES
from resources.enemies import ENEMIES, BIOME_RACES
from city_dialogue import service_dialogue
from events import format_day_delta
from gui.terminal import term


def generate_bounties(player, city_id):
    """Generate flexible bounties scaling with player level and Karma."""
    city = CITIES[city_id]
    biome = city.get("biome", "temperate")
    allowed_races = BIOME_RACES.get(biome, BIOME_RACES["temperate"])
    
    possible_enemies = {k: v for k, v in ENEMIES.items() 
                        if (v.get("race") in allowed_races or v.get("secondary_race") in allowed_races)
                        and not v.get("boss") 
                        and not v.get("super_boss")
                        and not v.get("minion_only")
                        and not v.get("city_only")
                        and not v.get("_heroine")
                        and not v.get("_shadow")
                        and not (v.get("secondary_race") == "Storybook" and biome != "wonderland")}
    if not possible_enemies:
        possible_enemies = {k: v for k, v in ENEMIES.items() 
                            if not v.get("boss") and not v.get("super_boss")
                            and not v.get("minion_only")
                            and not v.get("city_only")
                            and not v.get("_heroine")
                            and not v.get("_shadow")
                            and not (v.get("secondary_race") == "Storybook" and biome != "wonderland")}
    
    player_level = player.get("level", 1)
    # Karma is the single standing score. High Karma earns harder, richer
    # contracts; low Karma keeps the board at its minimum and pays less.
    # No per-city favor.
    karma_score = karma.get_karma(player) if karma.is_enabled(player) else 0
    positive_karma = max(0, karma_score)
    
    level_offset = max(1, min(5, 2 + karma_score // 30))
    min_level = max(1, player_level - 2)
    max_level = player_level + level_offset
    
    candidates = [k for k, v in possible_enemies.items() 
                  if min_level <= v["level"] <= max_level]
    
    num_bounties = max(2, min(7, 2 + karma_score // 20))
    bounties = []
    
    for _ in range(num_bounties):
        if not candidates:
            candidates = list(possible_enemies.keys())
        target = random.choice(candidates)
        enemy_data = ENEMIES[target]
        enemy_level = enemy_data["level"]
        
        base_kills = random.randint(3, 6) + (positive_karma // 25)
        kills_needed = max(2, int(base_kills * random.uniform(0.8, 1.5)))
        
        deadline_base = 7 - (positive_karma // 25) - (kills_needed // 6)
        deadline = max(1, deadline_base)
        tightness = 1.0 + (max(0, 6 - deadline) * 0.15)
        
        base_gold_per_kill = enemy_level * random.randint(8, 12)
        karma_mult = 1.0 + (karma_score / 200)
        reward_gold = int(kills_needed * base_gold_per_kill * karma_mult * tightness)
        
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
            "target_level": enemy_level,
            "required": kills_needed,
            "difficulty": difficulty_display,   # Store the formatted dynamic rank + stars
            "days_given": deadline,
            "reward_gold": reward_gold,
        })

    # Atonement contract: one per 7-day guild refresh, only for negative Karma.
    # It shares the normal bounty-shaped flow but grants Karma instead of gold-only.
    if karma.is_enabled(player) and karma.get_karma(player) <= -25:
        karma.ensure_state(player)
        gate = player["karma_gate"]
        current_day = int(player.get("day", 1) or 1)
        if current_day >= int(gate.get("atonement_day", -99) or -99) + 7:
            if not candidates:
                candidates = list(possible_enemies.keys())
            if candidates:
                target = random.choice(candidates)
                enemy_data = ENEMIES[target]
                bounties.append({
                    "id": f"atonement_{random.randint(10000, 99999)}",
                    "target_enemy": target,
                    "target_name": enemy_data["name"],
                    "target_level": enemy_data["level"],
                    "required": 3,
                    "difficulty": "Atonement",
                    "days_given": 7,
                    "reward_gold": 25,
                    "reward_karma": 5,
                    "atonement": True,
                })
                gate["atonement_day"] = current_day

    return bounties

def clamp(value, min_val, max_val):
    """Helper to keep difficulty strictly within boundaries."""
    return max(min_val, min(max_val, value))


# ── Prescript Ledger gate: Level 20+ bounty completions ──────────────
HIGH_BOUNTY_LEVEL = 20


def _bounty_target_level(bounty):
    """Best-effort target level (stored at generation; template fallback for old saves)."""
    lvl = bounty.get("target_level")
    if lvl is None:
        lvl = (ENEMIES.get(bounty.get("target_enemy")) or {}).get("level", 0)
    return int(lvl or 0)


def _record_bounty_completion(player, bounty):
    """Count a turned-in bounty. Returns (total, high, counted_high).

    `high_bounties_completed` (Level 20+ targets) is the Prescript Ledger gate;
    `bounties_completed` counts every honored contract.
    """
    player["bounties_completed"] = player.get("bounties_completed", 0) + 1
    counted_high = _bounty_target_level(bounty) >= HIGH_BOUNTY_LEVEL
    if counted_high:
        player["high_bounties_completed"] = player.get("high_bounties_completed", 0) + 1
    from titles import check_unlock
    check_unlock(player)
    return (player["bounties_completed"],
            player.get("high_bounties_completed", 0),
            counted_high)

BESTIARY_PER_PAGE = 4

_ATTRIBUTE_ORDER = ("Strength", "Constitution", "Dexterity",
                    "Wisdom", "Learning", "Charisma")
_ATTRIBUTE_LABELS = {
    "Strength": "STR", "Constitution": "CON", "Dexterity": "DEX",
    "Wisdom": "WIS", "Learning": "LRN", "Charisma": "CHA",
}
_ELEMENT_ORDER = ("fire", "water", "thunder", "wind", "earth",
                  "light", "dark", "physical", "magical")


def _format_elemental_profile(profile):
    """Compact 'Fire 1.20, Dark 0.80' line; neutral entries are omitted."""
    parts = []
    for element in _ELEMENT_ORDER:
        try:
            value = float(profile.get(element, 1.0))
        except (TypeError, ValueError):
            continue
        if abs(value - 1.0) < 0.005:
            continue
        parts.append(f"{element.title()} {value:.2f}")
    return ", ".join(parts) if parts else "—"


def _view_bestiary(player, city_id):
    """Paginated record of every enemy defeated or captured at least once."""
    from bestiary import get_discovered_cards, get_total_enemy_count

    cards = get_discovered_cards(player)
    total = max(1, get_total_enemy_count())
    total_pages = max(1, (len(cards) + BESTIARY_PER_PAGE - 1) // BESTIARY_PER_PAGE)
    page = 0

    while True:
        term.clear()
        term.print(f"=== BESTIARY — {CITIES[city_id]['name'].upper()} GUILD HALL ===")
        term.print(f"  Discovered: {len(cards)}/{total}"
                   f"   (RES: >1.00 resistant, <1.00 weak)")
        term.print("")

        if not cards:
            term.print("  These pages are empty. Defeat or capture a creature to record it.")
            term.pause()
            return

        start = page * BESTIARY_PER_PAGE
        for card in cards[start:start + BESTIARY_PER_PAGE]:
            attrs = card["attributes"]
            stat_line = "  ".join(
                f"{_ATTRIBUTE_LABELS.get(attr, attr)} {attrs.get(attr, 0)}"
                for attr in _ATTRIBUTE_ORDER
            )
            dungeons = ", ".join(card["dungeons"]) if card["dungeons"] else "Unknown"
            term.print(f"  ── {card['name']}  [{card['type']}]  Lv {card['level']}")
            term.print(f"     Race: {card['race']}   Dungeon: {dungeons}")
            term.print(f"     HP {card['hp']}   {stat_line}")
            term.print(f"     DMG: {_format_elemental_profile(card['elemental_dmg'])}"
                       f"   RES: {_format_elemental_profile(card['elemental_res'])}")
            term.print(f"     {card['description']}")
            term.print(f"     Defeated: {card['defeated']}   Captured: {card['captured']}")
            term.print("")

        term.print(f"  Page {page + 1}/{total_pages}")

        nav_options = []
        if page > 0:
            nav_options.append("Previous Page")
        if page < total_pages - 1:
            nav_options.append("Next Page")
        nav_options.append("Back")

        choice_idx = term.menu(nav_options, prompt="Navigation:")
        if choice_idx < 0:
            break
        selection = nav_options[choice_idx]
        if selection == "Previous Page":
            page -= 1
        elif selection == "Next Page":
            page += 1
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
    """Guild legacy rewards: Sky Piercer, Prescript Ledger, Moonlight Greatsword.

    Three entries, each claimable once, each with its own requirement.
    """
    term.clear()
    term.print("=== GUILD LEGACY REWARDS ===")
    term.print("The Guild Master unrolls a ledger older than the guild itself.")
    term.print("")

    sky_required = 5
    sky_progress = len(set(player.get("defeated_superbosses", [])))
    ledger_required = 10
    ledger_progress = player.get("high_bounties_completed", 0)
    moon_required = 3
    moon_progress = len(set(player.get("defeated_superbosses", [])))

    term.print("  ☁️  Sky Piercer — unique accessory")
    term.print("     Executes non-Super-Boss enemies left at low HP by your attacks.")
    term.print(f"     Requirement: defeat {sky_required} different Super Bosses")
    if player.get("sky_piercer_claimed"):
        term.print("     Status: CLAIMED")
    else:
        term.print(f"     Progress: {min(sky_progress, sky_required)}/{sky_required}")

    term.print("")
    term.print("  📜  Prescript Ledger — unique accessory")
    term.print("     Records every honored contract. Its pages issue commands in battle:")
    term.print("     fulfil them for Grace; let them slip and the debt comes due.")
    term.print(f"     Requirement: fulfill {ledger_required} guild bounties against Level {HIGH_BOUNTY_LEVEL}+ targets")
    if player.get("prescript_ledger_claimed"):
        term.print("     Status: CLAIMED")
    else:
        term.print(f"     Progress: {min(ledger_progress, ledger_required)}/{ledger_required}")

    term.print("")
    term.print("  🌙  Moonlight Greatsword — unique weapon")
    term.print("     Moonlight (action, 5-turn cooldown): for the next 3 rounds,")
    term.print("     basic attacks become magical waves that strike every enemy for 75% damage.")
    term.print(f"     Requirement: defeat {moon_required} different Super Bosses")
    if player.get("moonlight_greatsword_claimed"):
        term.print("     Status: CLAIMED")
    else:
        term.print(f"     Progress: {min(moon_progress, moon_required)}/{moon_required}")

    options = []
    claims = []
    if not player.get("sky_piercer_claimed"):
        options.append("Claim Sky Piercer")
        claims.append("sky")
    if not player.get("prescript_ledger_claimed"):
        options.append("Claim Prescript Ledger")
        claims.append("ledger")
    if not player.get("moonlight_greatsword_claimed"):
        options.append("Claim Moonlight Greatsword")
        claims.append("moon")
    if not options:
        term.print("")
        term.print("All three relics already rest with you. The ledger is closed.")
        term.pause()
        return

    term.print("")
    choice = term.menu(options, prompt="Make your claim:", allow_cancel=True, cancel_label="Back")
    if choice < 0 or choice >= len(claims):
        return
    claim = claims[choice]

    from resources.items import build_item
    from inventory import add_item_to_inventory

    if claim == "sky":
        if sky_progress < sky_required:
            term.print("")
            term.print("*** CLAIM REJECTED ***")
            term.print(f"The ledger is incomplete. Defeat {sky_required - sky_progress} more different Super Bosses to prove your worth.")
            term.pause()
            return
        item = build_item("sky_piercer")
        add_item_to_inventory(player, item)
        player["sky_piercer_claimed"] = True
        term.print("")
        term.print("The Guild Master bows. 'Take it. The sky will not forget your name.'")
        term.print(f"*** Received unique accessory: {item['name']} ***")
        term.pause()
        return

    if claim == "moon":
        _legendary_moon_claim(player, moon_required, moon_progress)
        return

    if ledger_progress < ledger_required:
        term.print("")
        term.print("*** CLAIM REJECTED ***")
        term.print(f"The ledger is incomplete. Honour {ledger_required - ledger_progress} more bounties against Level {HIGH_BOUNTY_LEVEL}+ targets.")
        term.pause()
        return
    item = build_item("prescript_ledger")
    add_item_to_inventory(player, item)
    player["prescript_ledger_claimed"] = True
    term.print("")
    term.print("The Guild Master traces a new page. 'Every contract honored was already written here.'")
    term.print(f"*** Received unique accessory: {item['name']} ***")
    term.pause()


def _legendary_moon_claim(player, moon_required, moon_progress):
    """Claim the Moonlight Greatsword from the Guild's legacy ledger."""
    if moon_progress < moon_required:
        term.print("")
        term.print("*** CLAIM REJECTED ***")
        term.print(f"The ledger is incomplete. Defeat {moon_required - moon_progress} more different Super Bosses.")
        term.pause()
        return
    from resources.items import build_item
    from inventory import add_item_to_inventory
    item = build_item("moonlight_greatsword", "unique")
    add_item_to_inventory(player, item)
    player["moonlight_greatsword_claimed"] = True
    term.print("")
    term.print("The Guild Master sets a pale blade on the table. 'The moon is a")
    term.print("patient creditor. It has been waiting for someone to carry this.'")
    term.print(f"*** Received unique weapon: {item['name']} ***")
    term.pause()


def _traveling_merchant(player, city_id):
    """Market Day event: a traveling merchant sells wares inside the guild hall."""
    from facilities.travel_events import (
        _merchant_stock_rarity, _merchant_price,
        _charisma_discount, _item_stat_line,
    )
    from resources.items import build_item, soften_rarity
    from resources.item_generation import pick_equipment_id, player_biome
    from resources.trade_goods import (
        roll_cargo_good, build_cargo, cargo_merchant_stock_price,
    )
    from inventory import add_item_to_inventory

    term.clear()
    term.print("=== TRAVELING MERCHANT ===")
    term.print('  A road-worn merchant has set up a stall in the corner of the guild hall.')
    term.print('  "Wares! Quality goods — fair price for a fellow traveler!"\n')

    # Build stock: filtered item pool, floor-influenced rarity, ~30% cargo
    stock = []
    for _ in range(random.randint(2, 3)):
        if random.random() < 0.30:
            good_id = roll_cargo_good(city_id)
            item = build_cargo(good_id)
            your_price, road_price = cargo_merchant_stock_price(good_id, player)
            stock.append((item, your_price, road_price))
            continue
        item_id     = pick_equipment_id(max(1, player.get("floor", 1)), player_biome(player))
        rarity      = _merchant_stock_rarity(player)
        rarity      = soften_rarity(item_id, rarity)
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
        choice = term.menu(options, prompt="What will you do?")

        if choice == -1 or choice == len(options) - 1:
            term.print('  "Safe roads, traveler!"')
            break

        if choice == len(options) - 2:  # Sell
            _merchant_sell(player, city_id)
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


def _merchant_sell(player, city_id=None):
    """Sell items to the guild-hall traveling merchant at road rates."""
    from facilities.travel_events import _sell_price, _item_stat_line
    from resources.trade_goods import cargo_merchant_sell_price
    from inventory import remove_item_by_reference, is_sellable_item
    from combat.weapon.wedding_specials import is_wedding_item_soulbound
    from resources.items import is_unique_item

    inv = player.get("inventory", [])
    if not inv:
        term.print('  "Nothing I want off you — yet." The merchant shrugs.')
        term.pause()
        return

    # Cargo sells at the local demand rate; everything else at the road rate.
    # Key items and crafting materials (flowers) are never sellable.
    sellable = []
    for i in inv:
        if i.get("type") == "cargo":
            sellable.append((i, cargo_merchant_sell_price(i, city_id)))
        elif is_sellable_item(i):
            sellable.append((i, _sell_price(i, player)))
    if not sellable:
        term.print('  "Nothing I want off you — yet." The merchant shrugs.')
        term.pause()
        return

    term.print("\n  The merchant eyes your pack with practiced interest.")
    term.print("  (Road sell rate: ~75% of city shop value)\n")

    for i, (item, unit_price) in enumerate(sellable):
        count       = item.get("count", 1)
        stack_price = unit_price * count
        count_str   = f" (x{count})" if count > 1 else ""
        term.print(f"  {i+1:>2}. {item['name']}{count_str}  {_item_stat_line(item)}  —  {stack_price}g")

    try:
        raw = term.input("\n  Sell which item number? (0 to cancel): ")
        idx = int(raw.strip()) - 1
        if 0 <= idx < len(sellable):
            item, unit_price = sellable[idx]
            if is_wedding_item_soulbound(item):
                term.print(f'  [{item["name"]}] is soulbound — cannot be sold.')
            elif is_unique_item(item):
                term.print(f'  [{item["name"]}] is unique — cannot be sold.')
            else:
                gold = unit_price * item.get("count", 1)
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
        guild_line = karma_dialogue.service_line(player, "guild", city_id)
        if guild_line:
            term.print(f'  "{guild_line}"')
        if karma.is_enabled(player):
            tier = karma.get_karma_tier(player)
            term.print(f"Karma: {tier['label']} ({karma.get_karma(player):+d}) "
                       f"| Gold: {player.get('gold', 0)}")
        else:
            term.print(f"Gold: {player.get('gold', 0)}")
        
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
            "Bestiary",
            "Ascend Level Cap",
            "Legendary Rewards",
        ]
        action_keys = ["bounty", "manage", "bestiary", "ascend", "legendary"]
        from combat.skills import can_choose_profession
        if can_choose_profession(player):
            options.append("Choose Profession (permanent)")
            action_keys.append("profession")
        if merchant_active:
            options.append("Visit the Traveling Merchant")
            action_keys.append("merchant")
        options.append("Leave")

        choice = term.menu(options, prompt="What would you like to do?")

        if choice == len(options) - 1 or choice == -1:
            service_dialogue(city_id, "receptionist", "leave")
            advance_time(player, 15)
            break
        if choice < 0 or choice >= len(action_keys):
            continue
        action = action_keys[choice]
        if action == "bounty":
            _view_bounty_board(player, city_id, stock_key)
        elif action == "manage":
            _manage_bounties(player, city_id)
        elif action == "bestiary":
            _view_bestiary(player, city_id)
        elif action == "ascend":
            _ascend_level_cap(player, city_id)
        elif action == "legendary":
            _legendary_rewards(player, city_id)
        elif action == "profession":
            _choose_profession(player, city_id)
        elif action == "merchant":
            _traveling_merchant(player, city_id)

def _choose_profession(player, city_id):
    """One-time, permanent profession ceremony (capstone required)."""
    from resources.skill_loader import PROFESSIONS
    from combat.skills import unlock_skills_for_level
    cls = player.get("class")
    branches = PROFESSIONS.get(cls, {})
    if not branches or player.get("profession"):
        return

    term.clear()
    term.print("=== CHOOSE YOUR PROFESSION ===")
    term.print("The guildmaster speaks: 'This choice is PERMANENT. The other path is closed forever.'")
    options = []
    keys = []
    for pid, pdata in branches.items():
        options.append(f"{pdata['name']} — {pdata.get('tagline', '')}")
        keys.append(pid)
    options.append("Not yet")
    choice = term.menu(options, prompt="Which path do you walk?")
    if choice < 0 or choice >= len(keys):
        return
    pid = keys[choice]
    pdata = branches[pid]

    term.clear()
    term.print(f"=== {pdata['name'].upper()} ===")
    term.print(pdata.get("tagline", ""))
    passive = pdata.get("passive", {})
    if passive:
        term.print(f"\nPassive — {passive.get('name', '')}: {passive.get('description', '')}")
    term.print("\nSkills:")
    for sid, sdef in sorted(pdata.get("skills", {}).items(), key=lambda kv: kv[1].get("unlock_level", 0)):
        term.print(f"  {sdef['name']} (Lv {sdef.get('unlock_level', '?')}) — {sdef.get('description', '')}")
    other = ", ".join(p['name'] for op, p in branches.items() if op != pid)
    term.print(f"\nLocked out forever: {other}")

    confirm = term.menu(["Confirm — this choice is permanent", "Go back"], prompt="Are you ready?")
    if confirm != 0:
        return
    player["profession"] = pid
    new_skills = unlock_skills_for_level(player)
    term.print(f"\n*** You are now a {pdata['name']}! ***")
    for name in new_skills:
        term.print(f"  Learned: {name}")
    if not new_skills:
        term.print("  (Your signature skill is already known.)")
    term.print("\nThe guildmaster nods. 'Walk your path well.'")
    term.pause()

def _view_bounty_board(player, city_id, stock_key):
    current_day = player.get("day", 1)
    while True:
        term.clear()
        term.print("=== BOUNTY BOARD ===")
        bounties = player.get(stock_key, [])
        if not bounties:
            term.print("No bounties available. Check back when the board refreshes.")
            term.pause()
            break
        else:
            refresh_day = int(player.get(f'bounty_refresh_day_{city_id}', current_day) or current_day)
            term.print(f"Board refreshes {format_day_delta(refresh_day, current_day)}\n")
            options = []
            for i, b in enumerate(bounties):
                if b.get("atonement"):
                    term.print(f"{i+1}. Atonement — Hunt {b['required']} {b['target_name']} (Difficulty Atonement)")
                    term.print(f"   Reward: {b['reward_gold']}g, +{b.get('reward_karma', 5)} Karma | Deadline: {b['days_given']} Days")
                    options.append(f"Atonement: {b['target_name']} — +{b.get('reward_karma', 5)} Karma")
                else:
                    term.print(f"{i+1}. Hunt {b['required']} {b['target_name']} (Difficulty {b['difficulty']})")
                    term.print(f"   Reward: {b['reward_gold']}g | Deadline: {b['days_given']} Days")
                    options.append(f"Hunt {b['target_name']} — {b['reward_gold']}g")
        
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
            term.print(f"{i+1}. {b['target_name']} [{status}] - "
                       f"Expires {format_day_delta(b['deadline'], current_day)} "
                       f"(Issuer: {CITIES[b['city']]['name']})")
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
                gold_reward = int(b.get("reward_gold", 0) or 0)
                # Deed titles: Contracted improves all bounty payouts.
                from titles import mod as _title_mod
                _bounty_bonus = _title_mod(player, "bounty_gold_pct")
                if _bounty_bonus:
                    gold_reward = int(round(gold_reward * (1.0 + _bounty_bonus)))
                if b.get("atonement"):
                    reward_karma = int(b.get("reward_karma", 5) or 5)
                    applied = karma.change_karma_toward_zero(
                        player, reward_karma, "Guild atonement contract"
                    )
                    player["gold"] = player.get("gold", 0) + gold_reward
                    term.print(f"Atonement contract complete! Earned {gold_reward} gold.")
                    if applied:
                        term.print(
                            f"Karma {applied:+d} "
                            f"({karma.get_karma_tier(player)['label']} "
                            f"{karma.get_karma(player):+d})."
                        )
                    else:
                        term.print("Your conscience can only grow so much in a day.")
                else:
                    # Event bonuses: Bounty Rush and New Moon Festival boost gold.
                    daily = player.get("daily_effects", {})
                    try:
                        bounty_bonus = float(daily.get("bounty_bonus", 0) or 0)
                    except (TypeError, ValueError):
                        bounty_bonus = 0.0
                    notes = []
                    if bounty_bonus:
                        gold_reward = int(gold_reward * (1.0 + bounty_bonus))
                        notes.append(f"Bounty bonus +{bounty_bonus:.0%}")
                    note = f" ({', '.join(notes)})" if notes else ""
                    term.print(f"Bounty Complete! Earned {gold_reward} gold in {CITIES[b['city']]['name']}.{note}")
                    player["gold"] = player.get("gold", 0) + gold_reward
                    total_contracts, high_contracts, _counted_high = _record_bounty_completion(player, b)
                    term.print(f"(The Guild's ledger records {total_contracts} honored contracts — "
                               f"{high_contracts} against Level {HIGH_BOUNTY_LEVEL}+ foes.)")
                active.pop(choice)
                advance_time(player, 10)
                term.pause()