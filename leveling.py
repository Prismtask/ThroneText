import random
from resources.constants import BASE_EXP_FOR_NEXT_LEVEL, EXP_SCALING
from resources.cities import CITIES
from character import player_max_hp
from combat.skills import unlock_skills_for_level

def exp_needed_for_next_level(level):
    return int(BASE_EXP_FOR_NEXT_LEVEL * (EXP_SCALING ** (level - 1)))

def get_city_dungeon_progress(player, city_id):
    """Return list of (dungeon_name, max_floor) for all dungeons in a city.
    Future-proof: if multiple dungeons per city are added, extend this."""
    city_prog = player.get("city_floors", {}).get(city_id, {})
    # Main dungeon (currently one per city; extend here for multiple)
    progress = [("Main Dungeon", city_prog.get("max_floor", 1))]
    return progress


def _get_unique_biomes():
    """Return the set of all unique biome names across all cities."""
    return {CITIES[c].get("biome", "temperate") for c in CITIES}


def get_biomes_cleared_to_cap(player, cap):
    """Return set of unique biomes with at least one city dungeon cleared to `cap`."""
    cleared = set()
    for city_id in CITIES:
        city_prog = player.get("city_floors", {}).get(city_id, {})
        if city_prog.get("max_floor", 1) >= cap:
            biome = CITIES[city_id].get("biome", "temperate")
            cleared.add(biome)
    return cleared


def get_required_biomes_for_cap(current_cap):
    """How many biomes must be cleared to unlock the next cap."""
    total_biomes = len(_get_unique_biomes())
    # 2 biomes at 10→20, 4 at 20→30, 6 at 30→40, 8 at 40→50, 10 at 50→60
    required = (current_cap // 10) * 2
    return min(required, total_biomes)


def can_ascend_level_cap(player):
    """Check if enough unique biomes have been cleared to the current level cap."""
    current_cap = player.get("level_cap", 10)
    cleared = get_biomes_cleared_to_cap(player, current_cap)
    required = get_required_biomes_for_cap(current_cap)
    return len(cleared) >= required


def get_incomplete_biomes(player):
    """Return list of (biome_name, example_city, max_floor, required) for uncleared biomes."""
    current_cap = player.get("level_cap", 10)
    cleared_biomes = get_biomes_cleared_to_cap(player, current_cap)

    # Group cities by biome
    biome_cities = {}
    for city_id, data in CITIES.items():
        biome = data.get("biome", "temperate")
        biome_cities.setdefault(biome, []).append((city_id, data["name"]))

    incomplete = []
    for biome in sorted(biome_cities.keys()):
        if biome not in cleared_biomes:
            # Find the city with the highest progress in this biome
            best_city = None
            best_floor = 0
            for city_id, city_name in biome_cities[biome]:
                city_prog = player.get("city_floors", {}).get(city_id, {})
                max_floor = city_prog.get("max_floor", 1)
                if max_floor > best_floor:
                    best_floor = max_floor
                    best_city = city_name
            if best_city:
                incomplete.append((biome.title(), best_city, best_floor, current_cap))
    return incomplete


def get_next_level_cap(current_cap):
    return ((current_cap // 10) + 1) * 10

def get_current_city_id(player):
    loc = player.get("location", "solmere")
    if loc == "dungeon":
        return player.get("origin_city", "solmere")
    return loc

def check_level_cap_milestone(player, city_id):
    """Check if enough unique biomes have been cleared to the current cap.
    Prints a message when the global milestone is newly reached."""
    current_cap = player.get("level_cap", 10)
    required = get_required_biomes_for_cap(current_cap)
    
    notified = player.setdefault("ascension_notified", {})
    global_key = f"global_{current_cap}"
    
    if notified.get(global_key):
        return  # Already notified for this milestone
    
    if can_ascend_level_cap(player):
        cleared = len(get_biomes_cleared_to_cap(player, current_cap))
        city_name = CITIES.get(city_id, {}).get("name", city_id)
        print(f"\n{'='*50}")
        print(f"  A surge of primal energy flows through you!")
        print(f"  {cleared} biomes have been conquered to Floor {current_cap}.")
        print(f"  You feel ready to become stronger.")
        print(f"  Visit any Guild to Ascend!")
        print(f"{'='*50}")
        notified[global_key] = True

def gain_exp(player, amount):
    from combat.stat_milestones import get_learning_bonus, check_milestone_notification
    
    # If already at the level cap, silently discard XP (don't accumulate)
    if player["level"] >= player.get("level_cap", 10):
        return False
    
    amount = int(amount * get_learning_bonus(player))
    old_attributes = player["attributes"].copy()
    player["exp"] = player.get("exp", 0) + amount
    leveled = False
    while player["exp"] >= exp_needed_for_next_level(player["level"]):
        # Level cap check
        if player["level"] >= player.get("level_cap", 10):
            current_cap = player.get("level_cap", 10)
            required = get_required_biomes_for_cap(current_cap)
            cleared = len(get_biomes_cleared_to_cap(player, current_cap))
            if can_ascend_level_cap(player):
                print(f"\n*** LEVEL CAP REACHED: Level {player['level_cap']} ***")
                print(f"You have conquered enough biomes — but your potential remains sealed.")
                print("Visit any Guild to Ascend and break through!")
            else:
                print(f"\n*** LEVEL CAP REACHED: Level {player['level_cap']} ***")
                print(f"Biomes conquered to Floor {current_cap}: {cleared}/{required}")
                print(f"Clear dungeons in {required - cleared} more biome(s) to grow stronger.")
            break
        
        player["exp"] -= exp_needed_for_next_level(player["level"])
        player["level"] += 1
        leveled = True
        print(f"\n*** LEVEL UP! You are now level {player['level']} ***")
        
        old_max = player_max_hp(player)
        
        # Choose attribute
        print("Choose an attribute to increase by 1:")
        attrs = ["Strength", "Constitution", "Dexterity", "Wisdom", "Learning", "Charisma"]
        for i, a in enumerate(attrs, 1):
            print(f"{i}. {a} (current: {player['attributes'][a]})")
        try:
            idx = int(input("Enter number: ").strip()) - 1
            chosen = attrs[idx]
        except:
            chosen = random.choice(attrs)
            print(f"Invalid choice, {chosen} was chosen.")
        
        player["attributes"][chosen] += 1
        print(f"{chosen} increased to {player['attributes'][chosen]}.")
        
        # HP Rewards
        player["level_hp_bonus"] = player.get("level_hp_bonus", 0) + 4   # ← HP BUFF
        
        new_max = player_max_hp(player)
        player["current_hp"] += (new_max - old_max)
        print(f"Maximum HP increased by {new_max - old_max}. New max: {new_max}")
        
        # Check for new skill unlocks
        new_skills = unlock_skills_for_level(player)
        if new_skills:
            print(f"\n*** NEW SKILL(S) UNLOCKED: {', '.join(new_skills)} ***")
        
        # Check for stat milestone notifications
        for msg in check_milestone_notification(player, old_attributes):
            print(msg)
    
    return leveled

def gain_exp_ally(ally, amount):
    """Award XP to an ally and handle level-ups using the same HUD as player."""
    from combat.ally import ally_max_hp

    # If already at the level cap, silently discard XP
    if ally["level"] >= ally.get("level_cap", 10):
        return False

    ally["exp"] = ally.get("exp", 0) + amount
    leveled = False
    while ally["exp"] >= exp_needed_for_next_level(ally["level"]):
        # Level cap check
        if ally["level"] >= ally.get("level_cap", 10):
            print(f"\n*** LEVEL CAP REACHED: {ally['name']} is at Level {ally['level_cap']} ***")
            print("An Ascension Stone is needed to break through their limit.")
            break

        ally["exp"] -= exp_needed_for_next_level(ally["level"])
        ally["level"] += 1
        leveled = True
        print(f"\n*** LEVEL UP! {ally['name']} is now level {ally['level']} ***")

        old_max = ally_max_hp(ally)

        # Choose attribute
        print("Choose an attribute to increase by 1:")
        attrs = ["Strength", "Constitution", "Dexterity", "Wisdom", "Learning", "Charisma"]
        for i, a in enumerate(attrs, 1):
            print(f"{i}. {a} (current: {ally['attributes'][a]})")
        try:
            idx = int(input("Enter number: ").strip()) - 1
            chosen = attrs[idx]
        except:
            chosen = random.choice(attrs)
            print(f"Invalid choice, {chosen} was chosen.")

        ally["attributes"][chosen] += 1
        print(f"{chosen} increased to {ally['attributes'][chosen]}.")

        # HP Rewards
        ally["level_hp_bonus"] = ally.get("level_hp_bonus", 0) + 4

        new_max = ally_max_hp(ally)
        ally["max_hp"] = new_max
        ally["current_hp"] += (new_max - old_max)
        print(f"Maximum HP increased by {new_max - old_max}. New max: {new_max}")

    return leveled
