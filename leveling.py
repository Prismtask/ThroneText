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

def get_next_level_cap(current_cap):
    return ((current_cap // 10) + 1) * 10

def can_ascend_level_cap(player):
    """Check if ALL dungeons in ALL cities have been cleared to the current level cap."""
    current_cap = player.get("level_cap", 10)
    for city_id in CITIES:
        dungeons = get_city_dungeon_progress(player, city_id)
        for _, max_floor in dungeons:
            if max_floor < current_cap:
                return False
    return True

def get_incomplete_dungeons(player):
    """Return list of (city_name, dungeon_name, max_floor, required) for incomplete dungeons."""
    current_cap = player.get("level_cap", 10)
    incomplete = []
    for city_id in CITIES:
        city_name = CITIES.get(city_id, {}).get("name", city_id)
        dungeons = get_city_dungeon_progress(player, city_id)
        for dungeon_name, max_floor in dungeons:
            if max_floor < current_cap:
                incomplete.append((city_name, dungeon_name, max_floor, current_cap))
    return incomplete

def get_current_city_id(player):
    loc = player.get("location", "solmere")
    if loc == "dungeon":
        return player.get("origin_city", "solmere")
    return loc

def check_level_cap_milestone(player, city_id):
    """Check if all dungeons in ALL cities have reached the current level cap milestone.
    Prints a message when the global milestone is newly reached."""
    current_cap = player.get("level_cap", 10)
    
    notified = player.setdefault("ascension_notified", {})
    global_key = f"global_{current_cap}"
    
    if notified.get(global_key):
        return  # Already notified for this milestone
    
    if can_ascend_level_cap(player):
        city_name = CITIES.get(city_id, {}).get("name", city_id)
        print(f"\n{'='*50}")
        print(f"  A surge of primal energy flows through you!")
        print(f"  All dungeons across the world have been conquered to Floor {current_cap}.")
        print(f"  You feel ready to become stronger.")
        print(f"  Visit any Guild to Ascend!")
        print(f"{'='*50}")
        notified[global_key] = True

def gain_exp(player, amount):
    from combat.stat_milestones import get_learning_bonus, check_milestone_notification
    amount = int(amount * get_learning_bonus(player))
    old_attributes = player["attributes"].copy()
    player["exp"] = player.get("exp", 0) + amount
    leveled = False
    while player["exp"] >= exp_needed_for_next_level(player["level"]):
        # Level cap check
        if player["level"] >= player.get("level_cap", 10):
            current_cap = player.get("level_cap", 10)
            if can_ascend_level_cap(player):
                print(f"\n*** LEVEL CAP REACHED: Level {player['level_cap']} ***")
                print(f"You have conquered the dungeons of the world — but your potential remains sealed.")
                print("Visit any Guild to Ascend and break through!")
            else:
                print(f"\n*** LEVEL CAP REACHED: Level {player['level_cap']} ***")
                print(f"Clear every dungeon in every city to Floor {current_cap} to grow stronger.")
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

    ally["exp"] = ally.get("exp", 0) + amount
    leveled = False
    while ally["exp"] >= exp_needed_for_next_level(ally["level"]):
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
