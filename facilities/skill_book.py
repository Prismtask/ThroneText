# facilities/skill_book.py – Skill Book / Skill Menu
from utils import clear_screen
from combat.skills import (
    CLASS_SKILLS, PASSIVE_SKILLS,
    get_class_skill_map, get_all_unlocked_skills,
    get_skill_mastery_level, get_mastery_bonuses,
    format_mastery_label,
)
from character import player_max_hp
from combat.ally import get_alive_allies
from combat.ally_skills import (
    get_race_passive, get_innate_skill_def, get_learnable_skill_def,
    get_ally_skill_mastery_level, format_skill_learning_progress
)


def display_skill_book(player):
    """Display the full party skill book with all skills, mastery levels, and descriptions."""
    clear_screen()
    print(f"=== {player['name']}'s Skill Book ===")
    print(f"Class: {player['class']} | Level: {player.get('level', 1)}")
    print("=" * 60)

    # ── Player Skills ──
    _display_player_skill_book(player)

    # ── Ally Skills ──
    allies = get_alive_allies(player)
    if allies:
        for ally in allies:
            _display_ally_skill_book(ally)

    print("\n" + "=" * 60)
    input("Press Enter to return...")


def _display_player_skill_book(player):
    """Display the player's class skills with locked/unlocked status."""
    # Passive skill
    passive = PASSIVE_SKILLS.get(player.get("class"))
    if passive:
        print(f"\n[Player Passive] {passive['name']}")
        print(f"    {passive['description']}")

    # Active skills
    skill_map = get_class_skill_map(player)
    if not skill_map:
        print("\nNo skills available for your class.")
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


def _display_ally_skill_book(ally):
    """Display an ally's skill book: passive, innate, learned, and learning progress."""
    print(f"\n--- {ally['name']} (Level {ally.get('level', 1)}) ---")

    # Race passive
    race = ally.get("race")
    if race:
        passive = get_race_passive(race)
        if passive:
            print(f"  [Passive] {passive['name']}")
            print(f"    {passive['description']}")

    # Innate skills
    innate_ids = ally.get("innate_skills", [])
    if innate_ids:
        print("\n  --- Innate Skills ---")
        for sid in innate_ids:
            sdef = get_innate_skill_def(sid)
            if not sdef:
                continue
            cd = sdef.get("cooldown", 1)
            mastery = get_ally_skill_mastery_level(ally, sid)
            mastery_label = "★" * mastery if mastery > 0 else ""
            cd_str = ""
            if ally.get("skill_cooldowns", {}).get(sid, 0) > 0:
                cd_str = f" [CD: {ally['skill_cooldowns'][sid]}]"
            print(f"  {sdef['name']}{cd_str} {mastery_label}")
            print(f"    {sdef.get('description', '')}")
            print(f"    Cooldown: {cd} turns | Target: {sdef.get('target', 'enemy')}")
            if mastery > 0:
                print(f"    Mastery Lv.{mastery}")

    # Learned skills
    learned_ids = ally.get("learned_skills", [])
    if learned_ids:
        print("\n  --- Learned Skills ---")
        for sid in learned_ids:
            sdef = get_learnable_skill_def(sid)
            if not sdef:
                continue
            cd = sdef.get("cooldown", 1)
            mastery = get_ally_skill_mastery_level(ally, sid)
            mastery_label = "★" * mastery if mastery > 0 else ""
            cd_str = ""
            if ally.get("skill_cooldowns", {}).get(sid, 0) > 0:
                cd_str = f" [CD: {ally['skill_cooldowns'][sid]}]"
            print(f"  {sdef['name']}{cd_str} {mastery_label}")
            print(f"    {sdef.get('description', '')}")
            print(f"    Cooldown: {cd} turns | Target: {sdef.get('target', 'enemy')}")
            if mastery > 0:
                print(f"    Mastery Lv.{mastery}")

    # Currently learning
    if ally.get("learning"):
        progress = format_skill_learning_progress(ally)
        print(f"\n  [Learning] {progress}")


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
