# facilities/skill_book.py – Skill Book / Skill Menu
from utils import clear_screen
from combat.skills import (
    CLASS_SKILLS, PASSIVE_SKILLS,
    get_class_skill_map, get_all_unlocked_skills,
    get_skill_mastery_level, get_mastery_bonuses,
    format_mastery_label,
)
from character import player_max_hp


def display_skill_book(player):
    """Display the player's skill book with all known skills, mastery levels, and descriptions."""
    clear_screen()
    print(f"=== {player['name']}'s Skill Book ===")
    print(f"Class: {player['class']} | Level: {player.get('level', 1)}")
    print("=" * 60)

    # Passive skill
    passive = PASSIVE_SKILLS.get(player.get("class"))
    if passive:
        print(f"\n[PASSIVE] {passive['name']}")
        print(f"    {passive['description']}")
        print("    Always active.")

    # Active skills
    skill_map = get_class_skill_map(player)
    if not skill_map:
        print("\nNo skills available for your class.")
        input("\nPress Enter to return...")
        return

    unlocked = set(player.get("skills", []))
    level = player.get("level", 1)
    cooldowns = player.get("skill_cooldowns", {})
    mastery_data = player.get("skill_mastery", {})

    # Group by tier
    tiers = {
        "Tier 1 (Level 3-8)": [],
        "Tier 2 (Level 10-15)": [],
    }

    for sid, sdef in skill_map.items():
        ul = sdef["unlock_level"]
        if ul <= 8:
            tiers["Tier 1 (Level 3-8)"].append((sid, sdef))
        else:
            tiers["Tier 2 (Level 10-15)"].append((sid, sdef))

    for tier_name, skills in tiers.items():
        print(f"\n--- {tier_name} ---")
        for sid, sdef in skills:
            name = sdef["name"]
            ul = sdef["unlock_level"]
            cd = sdef["cooldown"]
            is_unlocked = sid in unlocked and level >= ul
            is_on_cd = cooldowns.get(sid, 0) > 0
            mastery = mastery_data.get(sid, 0)
            mastery_lvl = get_skill_mastery_level(player, sid)
            mastery_label = format_mastery_label(sid, player)

            status = ""
            if not is_unlocked:
                status = " [LOCKED]"
            elif is_on_cd:
                status = f" [CD: {cooldowns[sid]}]"

            print(f"\n  {name}{status} {mastery_label}")
            print(f"    Unlock: Level {ul} | Cooldown: {cd} turns")
            print(f"    {sdef['description']}")
            if mastery_lvl > 0:
                bonuses = get_mastery_bonuses(sid, mastery_lvl)
                print(f"    Mastery Lv.{mastery_lvl} ({mastery} uses):")
                if bonuses["power_mult"] > 1.0:
                    print(f"      +{int((bonuses['power_mult']-1)*100)}% power")
                if bonuses["cooldown_reduction"] > 0:
                    print(f"      -{bonuses['cooldown_reduction']} turn cooldown")
                if bonuses["extra_effect"]:
                    print(f"      Bonus effect at ★★★")

    print("\n" + "=" * 60)
    input("Press Enter to return...")


def skill_book_menu(player):
    """Main skill book loop."""
    while True:
        clear_screen()
        print(f"=== {player['name']}'s Skill Book ===")
        print("1. View Skills")
        print("2. Back")
        choice = input("\nChoice: ").strip()
        if choice == "1":
            display_skill_book(player)
        elif choice == "2":
            break
        else:
            print("Invalid choice.")
            input("Press Enter...")
