from resources.constants import BASE_EXP_FOR_NEXT_LEVEL, EXP_SCALING
from character import player_max_hp

def exp_needed_for_next_level(level):
    return int(BASE_EXP_FOR_NEXT_LEVEL * (EXP_SCALING ** (level - 1)))

def gain_exp(player, amount):
    player["exp"] = player.get("exp", 0) + amount
    leveled = False
    while player["exp"] >= exp_needed_for_next_level(player["level"]):
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
            chosen = "Strength"
            print("Invalid choice, defaulting to Strength.")
        
        player["attributes"][chosen] += 1
        print(f"{chosen} increased to {player['attributes'][chosen]}.")
        
        # HP Rewards
        player["level_hp_bonus"] = player.get("level_hp_bonus", 0) + 4   # ← HP BUFF
        
        new_max = player_max_hp(player)
        player["current_hp"] += (new_max - old_max)
        print(f"Maximum HP increased by {new_max - old_max}. New max: {new_max}")
    
    return leveled