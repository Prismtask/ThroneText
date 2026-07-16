import random
from resources.constants import EXP_COEFF_A, EXP_COEFF_B, EXP_POWER
from resources.cities import CITIES
from character import player_max_hp
from combat.skills import unlock_skills_for_level

# ── GUI terminal detection (safe import for terminal mode) ──────────
try:
    from gui.terminal import get_terminal as _get_gui_terminal
except ImportError:
    _get_gui_terminal = lambda: None

# ── GUI level-up dialog (safe import) ──────────────────────────────────
try:
    from gui.widgets.level_up_dialog import (
        choose_level_up_attribute as _gui_choose_attr,
        show_level_up_results as _gui_show_results,
    )
except ImportError:
    _gui_choose_attr = None
    _gui_show_results = None


def _term():
    """Return the GUI Terminal if running in GUI mode, else None."""
    return _get_gui_terminal()


def _tprint(*args, sep=" "):
    """Print to GUI if available, else to terminal."""
    t = _term()
    text = sep.join(str(a) for a in args)
    if t:
        t.print(text)
    else:
        print(text)


def _tpause(prompt="Press Enter to continue..."):
    """Pause for user acknowledgement."""
    t = _term()
    if t:
        t.pause(prompt)
    else:
        input(prompt)


def _tmenu(options, prompt="Choose an option:", allow_cancel=False, cancel_label="Cancel"):
    """Show a menu; returns 0-based index or -1."""
    t = _term()
    if t:
        return t.menu(options, prompt=prompt, allow_cancel=allow_cancel, cancel_label=cancel_label)
    else:
        for i, opt in enumerate(options):
            print(f"{i+1}. {opt}")
        if allow_cancel:
            print(f"0. {cancel_label}")
        try:
            choice = input(prompt + " ").strip()
            idx = int(choice) - 1
            if allow_cancel and idx == -1:
                return -1
            if 0 <= idx < len(options):
                return idx
        except (ValueError, IndexError):
            pass
        return -1


# ── Level-up I/O helpers (GUI-first, terminal fallback) ──────────────

def _choose_level_attr(entity_name, level, attributes):
    """
    Ask the user to pick an attribute to increase.

    Tries the GUI dialog first. If unavailable or cancelled, falls back
    to the terminal menu. Returns (attr_key, used_gui) where used_gui
    indicates whether the GUI was used for the pick (and thus whether
    results should also be shown via GUI).
    """
    # Try GUI dialog first
    if _gui_choose_attr is not None:
        try:
            chosen = _gui_choose_attr(entity_name, level, attributes)
            if chosen is not None:
                return chosen, True
        except Exception:
            pass  # Fall through to terminal

    # Terminal fallback
    _tprint(f"\n*** LEVEL UP! {entity_name} is now level {level} ***")
    _tprint("Choose an attribute to increase by 1:")
    attrs = ["Strength", "Constitution", "Dexterity", "Wisdom", "Learning", "Charisma"]
    attr_options = [f"{a} (current: {attributes[a]})" for a in attrs]
    choice_idx = _tmenu(attr_options, prompt="Choose attribute:")
    if 0 <= choice_idx < len(attrs):
        return attrs[choice_idx], False
    else:
        chosen = random.choice(attrs)
        _tprint(f"Invalid choice, {chosen} was chosen.")
        return chosen, False


def _show_level_results(entity_name, level, chosen_attr, new_value,
                        hp_increase, new_max_hp, new_skills, milestones,
                        used_gui):
    """
    Display level-up results.

    If the attribute was chosen via GUI dialog, shows results in a
    matching GUI dialog. Otherwise prints to the terminal.
    """
    if used_gui and _gui_show_results is not None:
        try:
            _gui_show_results(
                entity_name=entity_name,
                level=level,
                chosen_attr=chosen_attr,
                new_value=new_value,
                hp_increase=hp_increase,
                new_max_hp=new_max_hp,
                new_skills=new_skills if new_skills else None,
                milestones=milestones if milestones else None,
            )
            return
        except Exception:
            pass  # Fall through to terminal

    # Terminal fallback
    _tprint(f"{chosen_attr} increased to {new_value}.")
    if hp_increase > 0:
        _tprint(f"Maximum HP increased by {hp_increase}. New max: {new_max_hp}")
    if new_skills:
        _tprint(f"\n*** NEW SKILL(S) UNLOCKED: {', '.join(new_skills)} ***")
    for msg in (milestones or []):
        _tprint(msg)

def exp_needed_for_next_level(level):
    return int(EXP_COEFF_A * (level ** EXP_POWER) + EXP_COEFF_B * level)

def get_city_dungeon_progress(player, city_id):
    """Return list of (dungeon_name, max_floor) for all dungeons in a city.
    Future-proof: if multiple dungeons per city are added, extend this."""
    city_prog = player.get("city_floors", {}).get(city_id, {})
    # Main dungeon (currently one per city; extend here for multiple)
    progress = [("Main Dungeon", city_prog.get("max_floor", 1))]
    return progress


def _get_unique_biomes():
    """Return the set of all unique biome names across all cities.
    Wonderland is excluded — it is a hidden realm that does not count toward ascension."""
    return {CITIES[c].get("biome", "temperate") for c in CITIES
            if CITIES[c].get("biome", "") != "wonderland"}


def get_biomes_cleared_to_cap(player, cap):
    """Return set of unique biomes with at least one city dungeon cleared to `cap`.
    Wonderland is excluded — it does not count toward ascension requirements."""
    cleared = set()
    for city_id in CITIES:
        biome = CITIES[city_id].get("biome", "temperate")
        if biome == "wonderland":
            continue
        city_prog = player.get("city_floors", {}).get(city_id, {})
        if city_prog.get("max_floor", 1) >= cap:
            cleared.add(biome)
    return cleared


def get_required_biomes_for_cap(current_cap):
    """How many biomes must be cleared to unlock the next cap."""
    total_biomes = len(_get_unique_biomes())
    # 1 biome at 10→20, 2 at 20→30, 3 at 30→40, 4 at 40→50, 5 at 50→60
    required = current_cap // 10
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

    # Group cities by biome (exclude Wonderland)
    biome_cities = {}
    for city_id, data in CITIES.items():
        biome = data.get("biome", "temperate")
        if biome == "wonderland":
            continue
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


def is_pandemonium_unlocked(player):
    """Check if the player has cleared Floor 40 in at least 4 unique biomes.
    Wonderland is excluded — it does not count toward pandemonium unlock."""
    required_floors = 40
    required_biomes = 4
    cleared_biomes = set()
    for city_id in CITIES:
        biome = CITIES[city_id].get("biome", "temperate")
        if biome == "wonderland":
            continue
        city_prog = player.get("city_floors", {}).get(city_id, {})
        if city_prog.get("max_floor", 1) >= required_floors:
            cleared_biomes.add(biome)
    return len(cleared_biomes) >= required_biomes


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
        _tprint(f"\n{'='*50}")
        _tprint(f"  A surge of primal energy flows through you!")
        _tprint(f"  {cleared} biomes have been conquered to Floor {current_cap}.")
        _tprint(f"  You feel ready to become stronger.")
        _tprint(f"  Visit any Guild to Ascend!")
        _tprint(f"{'='*50}")
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
                _tprint(f"\n*** LEVEL CAP REACHED: Level {player['level_cap']} ***")
                _tprint("You have conquered enough biomes — but your potential remains sealed.")
                _tprint("Visit any Guild to Ascend and break through!")
            else:
                _tprint(f"\n*** LEVEL CAP REACHED: Level {player['level_cap']} ***")
                _tprint(f"Biomes conquered to Floor {current_cap}: {cleared}/{required}")
                _tprint(f"Clear dungeons in {required - cleared} more biome(s) to grow stronger.")
            break
        
        player["exp"] -= exp_needed_for_next_level(player["level"])
        player["level"] += 1
        leveled = True
        
        old_max = player_max_hp(player)
        
        # Choose attribute (GUI dialog or terminal menu)
        chosen, used_gui = _choose_level_attr(
            player.get("name", "You"), player["level"], player["attributes"]
        )
        
        player["attributes"][chosen] += 1
        new_val = player["attributes"][chosen]
        
        # HP Rewards
        player["level_hp_bonus"] = player.get("level_hp_bonus", 0) + 4   # ← HP BUFF
        
        new_max = player_max_hp(player)
        hp_increase = new_max - old_max
        player["current_hp"] += hp_increase
        
        # Check for new skill unlocks
        new_skills = unlock_skills_for_level(player)
        
        # Check for stat milestone notifications
        milestones = check_milestone_notification(player, old_attributes)
        
        # Show results (GUI dialog or terminal)
        _show_level_results(
            entity_name=player.get("name", "You"),
            level=player["level"],
            chosen_attr=chosen,
            new_value=new_val,
            hp_increase=hp_increase,
            new_max_hp=new_max,
            new_skills=new_skills if new_skills else None,
            milestones=milestones if milestones else None,
            used_gui=used_gui,
        )
    
    return leveled

def gain_exp_ally(ally, amount):
    """Award XP to an ally and handle level-ups using the same HUD as player."""
    from combat.ally import ally_max_hp
    from combat.ally_skills import gain_skill_learning_exp
    from combat.stat_milestones import get_learning_bonus, check_milestone_notification

    # ── Skill learning always progresses regardless of level cap ──
    learned_skill = gain_skill_learning_exp(ally, amount)
    if learned_skill:
        from combat.ally_skills import get_learnable_skill_def
        skill_def = get_learnable_skill_def(learned_skill)
        skill_name = skill_def.get("name", learned_skill) if skill_def else learned_skill
        _tprint(f"*** {ally['name']} has mastered {skill_name}! ***")

    # ── Level XP is blocked at level cap ──
    if ally["level"] >= ally.get("level_cap", 10):
        return False

    # Apply Learning milestone bonus (same as player)
    amount = int(amount * get_learning_bonus(ally))
    old_attributes = ally.get("attributes", {}).copy()

    ally["exp"] = ally.get("exp", 0) + amount
    leveled = False
    while ally["exp"] >= exp_needed_for_next_level(ally["level"]):
        # Level cap check
        if ally["level"] >= ally.get("level_cap", 10):
            _tprint(f"\n*** LEVEL CAP REACHED: {ally['name']} is at Level {ally['level_cap']} ***")
            _tprint("An Ascension Stone is needed to break through their limit.")
            break

        ally["exp"] -= exp_needed_for_next_level(ally["level"])
        ally["level"] += 1
        leveled = True

        old_max = ally_max_hp(ally)

        # Choose attribute (GUI dialog or terminal menu)
        chosen, used_gui = _choose_level_attr(
            ally["name"], ally["level"], ally.get("attributes", {})
        )

        ally["attributes"][chosen] += 1
        new_val = ally["attributes"][chosen]

        # Check for stat milestone notifications
        milestones = check_milestone_notification(ally, old_attributes)
        old_attributes = ally["attributes"].copy()

        # HP Rewards
        ally["level_hp_bonus"] = ally.get("level_hp_bonus", 0) + 4

        new_max = ally_max_hp(ally)
        hp_increase = new_max - old_max
        ally["max_hp"] = new_max
        ally["current_hp"] += hp_increase

        # Show results (GUI dialog or terminal)
        _show_level_results(
            entity_name=ally["name"],
            level=ally["level"],
            chosen_attr=chosen,
            new_value=new_val,
            hp_increase=hp_increase,
            new_max_hp=new_max,
            new_skills=None,
            milestones=milestones if milestones else None,
            used_gui=used_gui,
        )


    return leveled
