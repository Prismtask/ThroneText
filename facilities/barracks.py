# facilities/barracks.py
from utils import advance_time, clear_screen
from city_dialogue import service_dialogue
from combat.ally_skills import (
    teach_ally_skill, get_learnable_skills_by_category, 
    get_learnable_skill_def, format_skill_learning_progress
)


def barracks_service(player, city_id):
    """Barracks: train to gain temporary stat buffs or teach allies skills."""
    service_dialogue(city_id, "barracks", "enter")
    print("The drill sergeant offers combat training.")
    print("1. Train (75 gold – gain +2 Strength for next dungeon run)")
    print("2. Teach Ally Skill")
    print("3. Leave")
    choice = input("\nChoice: ").strip()
    
    if choice == "1":
        if player.get("gold", 0) >= 225:
            player["gold"] -= 225
            player["training_buff"] = {"strength": 2, "expires_after": 1}
            print("You sweat through brutal drills. You feel stronger.")
            service_dialogue(city_id, "barracks", "train")
        else:
            print("Not enough gold.")
    elif choice == "2":
        teach_skill_menu(player)
    else:
        service_dialogue(city_id, "barracks", "leave")
    
    input("\nPress Enter...")
    advance_time(player, 30)


def teach_skill_menu(player):
    """Menu to select an ally and teach them a skill."""
    from .house import get_current_house_allies, get_house_data, save_house_data
    
    allies = get_current_house_allies(player)
    if not allies:
        print("You don't have any allies in your house.")
        return
    
    clear_screen()
    print("=== TEACH SKILL ===")
    print("Select an ally to teach:")
    for i, ally_data in enumerate(allies, 1):
        print(f"{i}. {ally_data['name']} (Level {ally_data['level']})")
    print(f"{len(allies) + 1}. Cancel")
    
    try:
        choice = int(input("\nChoice: ").strip()) - 1
        if choice < 0 or choice >= len(allies):
            return
    except ValueError:
        return
    
    selected_ally = allies[choice]
    teach_ally_skill_submenu(player, selected_ally)


def teach_ally_skill_submenu(player, ally_data):
    """Submenu to choose which skill to teach an ally."""
    clear_screen()
    print(f"=== TEACH SKILL TO {ally_data['name'].upper()} ===")
    
    # Show current learning status
    if ally_data.get("learning"):
        print(f"\nCurrently learning: {format_skill_learning_progress(ally_data)}")
        confirm = input("Replace current learning? (y/n): ").strip().lower()
        if confirm != 'y':
            return
    
    # Show learned skills
    learned = ally_data.get("learned_skills", [])
    if learned:
        print(f"\nAlready knows: {', '.join(learned[:3])}" + (" ..." if len(learned) > 3 else ""))
    
    # Show skill categories
    print("\nSelect skill category:")
    print("1. Offensive")
    print("2. Defensive")
    print("3. Support")
    print("4. Back")
    
    try:
        cat_choice = int(input("\nChoice: ").strip())
    except ValueError:
        return
    
    categories = {1: "offensive", 2: "defensive", 3: "support"}
    if cat_choice not in categories:
        return
    
    category = categories[cat_choice]
    select_skill_from_category(player, ally_data, category)


def select_skill_from_category(player, ally_data, category):
    """Let player choose a specific skill to teach."""
    clear_screen()
    print(f"=== SELECT {category.upper()} SKILL ===")
    
    skills_dict = get_learnable_skills_by_category(category)
    learned = set(ally_data.get("learned_skills", []))
    
    # Filter out already learned skills
    available_skills = [(sid, sdef) for sid, sdef in skills_dict.items() if sid not in learned]
    
    if not available_skills:
        print(f"No available {category} skills to learn.")
        input("Press Enter...")
        return
    
    for i, (skill_id, skill_def) in enumerate(available_skills, 1):
        name = skill_def.get("name", skill_id)
        desc = skill_def.get("description", "")
        print(f"{i}. {name} - {desc}")
    
    print(f"{len(available_skills) + 1}. Back")
    
    try:
        choice = int(input("\nChoice: ").strip()) - 1
        if choice < 0 or choice >= len(available_skills):
            return
    except ValueError:
        return
    
    chosen_skill_id, chosen_skill_def = available_skills[choice]
    skill_name = chosen_skill_def.get("name", chosen_skill_id)
    
    # Confirm teaching
    clear_screen()
    print(f"Teach {ally_data['name']} the skill: {skill_name}?")
    print(f"Description: {chosen_skill_def.get('description', '')}")
    print(f"Learning time: 300 EXP")
    confirm = input("\n(y/n): ").strip().lower()
    
    if confirm == 'y':
        # Update the active party ally directly (recruited allies are not in house)
        from .house import get_house_data, save_house_data
        house_data = get_house_data(player)
        
        # Find and update the active party ally
        success = False
        for party_ally in player.get("allies", []):
            if party_ally.get("name") == ally_data['name']:
                success = teach_ally_skill(party_ally, chosen_skill_id)
                if success:
                    print(f"\n{ally_data['name']} is now learning {skill_name}!")
                break
        
        # Also update the house copy if she exists there (for non-recruited girls)
        if success:
            for girl in house_data:
                if girl['name'] == ally_data['name']:
                    teach_ally_skill(girl, chosen_skill_id)
                    break
            save_house_data(player, house_data)
        else:
            print(f"\nFailed to teach skill (already learning or already knows it).")
