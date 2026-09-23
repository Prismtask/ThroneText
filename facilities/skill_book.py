# facilities/skill_book.py – Skill Book / Skill Menu
from combat.skills import (
    PASSIVE_SKILLS,
    get_class_skill_map, get_skill_mastery_level, get_mastery_bonuses,
    format_mastery_label,
)
from combat.ally import get_alive_allies
from combat.ally_skills import (
    get_race_passive, get_innate_skill_def, get_learnable_skill_def,
    get_ally_skill_mastery_level, format_skill_learning_progress
)
from gui.terminal import term


def display_skill_book(player):
    """Display the full party skill book with all skills, mastery levels, and descriptions."""
    term.clear()
    term.print(f"=== {player['name']}'s Skill Book ===")
    term.print(f"Class: {player['class']} | Level: {player.get('level', 1)}")
    term.print("=" * 60)

    # ── Player Skills ──
    _display_player_skill_book(player)

    # ── Ally Skills ──
    allies = get_alive_allies(player)
    if allies:
        for ally in allies:
            _display_ally_skill_book(ally)

    term.print("\n" + "=" * 60)
    term.pause("Press Continue to return...")


def _display_player_skill_book(player):
    """Display the player's class skills with locked/unlocked status."""
    # Passive skill
    passive = PASSIVE_SKILLS.get(player.get("class"))
    if passive:
        term.print(f"\n[Player Passive] {passive['name']}")
        term.print(f"    {passive['description']}")

    # Active skills
    skill_map = get_class_skill_map(player)
    if not skill_map:
        term.print("\nNo skills available for your class.")
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
        term.print(f"\n--- {tier_name} ---")
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

            term.print(f"\n  {name}{status} {mastery_label}")
            term.print(f"    Unlock: Level {ul} | Cooldown: {cd} turns")
            term.print(f"    {sdef['description']}")
            if mastery_lvl > 0:
                bonuses = get_mastery_bonuses(sid, mastery_lvl)
                term.print(f"    Mastery Lv.{mastery_lvl} ({mastery} uses):")
                if bonuses["power_mult"] > 1.0:
                    term.print(f"      +{int((bonuses['power_mult']-1)*100)}% power")
                if bonuses["cooldown_reduction"] > 0:
                    term.print(f"      -{bonuses['cooldown_reduction']} turn cooldown")
                if bonuses["extra_effect"]:
                    term.print(f"      Bonus effect at ★★★")


def _display_ally_skill_book(ally):
    """Display an ally's skill book: passive, innate, learned, and learning progress."""
    term.print(f"\n--- {ally['name']} (Level {ally.get('level', 1)}) ---")

    # Race passive
    race = ally.get("race")
    passive = get_race_passive(race) if race else None
    if not passive and ally.get("passive_skill"):
        from combat.ally_skills import get_passive_by_id
        passive = get_passive_by_id(ally["passive_skill"])
    if not passive and ally.get("key"):
        from resources.enemies import ENEMIES
        template = ENEMIES.get(ally["key"], {})
        template_race = template.get("race")
        if template_race:
            passive = get_race_passive(template_race)
    if passive:
        term.print(f"  [Passive] {passive['name']}")
        term.print(f"    {passive['description']}")

    # Innate skills
    innate_ids = ally.get("innate_skills", [])
    if innate_ids:
        term.print("\n  --- Innate Skills ---")
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
            term.print(f"  {sdef['name']}{cd_str} {mastery_label}")
            term.print(f"    {sdef.get('description', '')}")
            term.print(f"    Cooldown: {cd} turns | Target: {sdef.get('target', 'enemy')}")
            if mastery > 0:
                term.print(f"    Mastery Lv.{mastery}")

    # Learned skills
    learned_ids = ally.get("learned_skills", [])
    if learned_ids:
        term.print("\n  --- Learned Skills ---")
        for sid in learned_ids:
            sdef = get_learnable_skill_def(sid)
            if not sdef:
                continue
            cd = sdef.get("cooldown", 1)
            tier = sdef.get("tier", 1)
            exp_cost = sdef.get("exp_cost", 300)
            mastery = get_ally_skill_mastery_level(ally, sid)
            mastery_label = "★" * mastery if mastery > 0 else ""
            cd_str = ""
            if ally.get("skill_cooldowns", {}).get(sid, 0) > 0:
                cd_str = f" [CD: {ally['skill_cooldowns'][sid]}]"
            tier_labels = {1: "I", 2: "II", 3: "III", 4: "IV"}
            tier_str = tier_labels.get(tier, "?")
            term.print(f"  {sdef['name']}{cd_str} {mastery_label} [Tier {tier_str}]")
            term.print(f"    {sdef.get('description', '')}")
            term.print(f"    Cooldown: {cd} turns | Target: {sdef.get('target', 'enemy')} | Cost: {exp_cost} EXP")
            if mastery > 0:
                term.print(f"    Mastery Lv.{mastery}")

    # Currently learning
    if ally.get("learning"):
        progress = format_skill_learning_progress(ally)
        term.print(f"\n  [Learning] {progress}")


def skill_book_menu(player):
    """Main skill book loop."""
    while True:
        term.clear()
        term.print(f"=== {player['name']}'s Skill Book ===")
        choice = term.menu([
            "View Skills",
            "Back"
        ], prompt="What would you like to do?")
        if choice == 0:
            display_skill_book(player)
        elif choice == 1 or choice == -1:
            break
