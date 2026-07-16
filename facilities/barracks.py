# facilities/barracks.py
from utils import advance_time, clear_screen
from city_dialogue import service_dialogue
from combat.ally_skills import (
    teach_ally_skill, replace_ally_learned_skill, MAX_LEARNED_SKILLS,
    get_learnable_skills_by_category, 
    get_learnable_skill_def, format_skill_learning_progress
)
from gui.terminal import term, get_terminal


TIER_LABELS = {1: "I", 2: "II", 3: "III", 4: "IV"}
TIER_NAMES = {1: "Novice", 2: "Adept", 3: "Veteran", 4: "Master"}


def barracks_service(player, city_id):
    """Barracks: train to gain temporary stat buffs, spar with dummy, or teach allies skills."""
    service_dialogue(city_id, "barracks", "enter")
    
    choice = term.menu([
        "Train (225 gold – gain +2 Strength for next dungeon run)",
        "Teach Ally Skill",
        "Spar with Training Dummy",
        "Leave"
    ], prompt="The drill sergeant offers combat training.")
    
    if choice == 0:
        if player.get("gold", 0) >= 225:
            player["gold"] -= 225
            player["training_buff"] = {"strength": 2, "expires_after": 1}
            term.print("You sweat through brutal drills. You feel stronger.")
            service_dialogue(city_id, "barracks", "train")
        else:
            term.print("Not enough gold.")
    elif choice == 1:
        teach_skill_menu(player)
    elif choice == 2:
        _dummy_spar_flow(player)
    else:
        service_dialogue(city_id, "barracks", "leave")
    
    # If launching dummy combat (GUI mode), skip pause/advance — the combat
    # screen will handle itself.
    if player.get("_pending_dummy_combat"):
        return

    term.pause()
    advance_time(player, 30)


def teach_skill_menu(player):
    """Menu to select an ally and teach them a skill."""
    from .house import get_current_house_allies, get_house_data, save_house_data
    
    allies = get_current_house_allies(player)
    if not allies:
        term.print("You don't have any allies in your house.")
        return
    
    term.clear()
    options = [f"{ally_data['name']} (Level {ally_data['level']})" for ally_data in allies]
    
    choice = term.menu(options, prompt="=== TEACH SKILL ===\nSelect an ally to teach:")
    
    if choice < 0 or choice >= len(allies):
        return
    
    selected_ally = allies[choice]
    teach_ally_skill_submenu(player, selected_ally)


def teach_ally_skill_submenu(player, ally_data):
    """Submenu to choose which skill to teach an ally."""
    term.clear()
    term.print(f"=== TEACH SKILL TO {ally_data['name'].upper()} ===")
    
    # Show current learning status
    if ally_data.get("learning"):
        term.print(f"\nCurrently learning: {format_skill_learning_progress(ally_data)}")
        if not term.confirm("Replace current learning?"):
            return
    
    # Show learned skills
    learned = ally_data.get("learned_skills", [])
    if learned:
        term.print(f"\nAlready knows: {', '.join(learned[:3])}" + (" ..." if len(learned) > 3 else ""))
    
    # Show skill categories
    choice = term.menu([
        "Offensive",
        "Defensive",
        "Support",
        "Back"
    ], prompt="Select skill category:")
    
    categories = {0: "offensive", 1: "defensive", 2: "support"}
    if choice not in categories:
        return
    
    category = categories[choice]
    select_skill_from_category(player, ally_data, category)


def _format_tier_line(skill_def, ally_level):
    """Return a formatted skill listing line with tier/cost/lock status."""
    tier = skill_def.get("tier", 1)
    exp_cost = skill_def.get("exp_cost", 300)
    req_level = skill_def.get("required_level", 1)
    name = skill_def.get("name", "Unknown")
    desc = skill_def.get("description", "")
    tier_name = TIER_NAMES.get(tier, "Unknown")
    
    if ally_level < req_level:
        lock = "[LOCKED]"
        return f"  {lock} {name} (Tier {TIER_LABELS.get(tier, '?')} {tier_name}) — Requires Lv.{req_level} | {exp_cost} EXP"
    else:
        return f"  {name} (Tier {TIER_LABELS.get(tier, '?')} {tier_name}) — {exp_cost} EXP\n      {desc}"


def select_skill_from_category(player, ally_data, category):
    """Let player choose a specific skill to teach, grouped by tier."""
    term.clear()
    term.print(f"=== SELECT {category.upper()} SKILL ===")
    term.print(f"Ally: {ally_data['name']} (Level {ally_data['level']})")
    
    skills_dict = get_learnable_skills_by_category(category)
    learned = set(ally_data.get("learned_skills", []))
    ally_level = ally_data.get("level", 1)
    
    # Filter out already learned skills
    available_skills = [(sid, sdef) for sid, sdef in skills_dict.items() if sid not in learned]
    
    if not available_skills:
        term.print(f"No available {category} skills to learn.")
        term.pause()
        return
    
    # Sort by tier then name
    available_skills.sort(key=lambda x: (x[1].get("tier", 1), x[1].get("name", "")))
    
    # Build display and menu options
    current_tier = None
    skill_index_map = {}
    options = []
    
    for sid, sdef in available_skills:
        tier = sdef.get("tier", 1)
        if tier != current_tier:
            current_tier = tier
            tier_name = TIER_NAMES.get(tier, "Unknown")
            term.print(f"\n--- Tier {TIER_LABELS.get(tier, '?')} ({tier_name}) ---")
        
        idx = len(options)
        skill_index_map[idx] = (sid, sdef)
        line = _format_tier_line(sdef, ally_level)
        term.print(f"{idx + 1}.{line}")
        
        # Build short option label for buttons
        name = sdef.get("name", "Unknown")
        req = sdef.get("required_level", 1)
        exp_cost = sdef.get("exp_cost", 300)
        lock = " [LOCKED]" if ally_level < req else ""
        options.append(f"{name}{lock} — {exp_cost} EXP")
    
    choice = term.menu(options, prompt=f"Choose a {category} skill:", allow_cancel=True)
    
    if choice < 0 or choice >= len(skill_index_map):
        return
    
    chosen_skill_id, chosen_skill_def = skill_index_map[choice]
    skill_name = chosen_skill_def.get("name", chosen_skill_id)
    exp_cost = chosen_skill_def.get("exp_cost", 300)
    req_level = chosen_skill_def.get("required_level", 1)
    tier = chosen_skill_def.get("tier", 1)
    
    # Check level requirement
    if ally_level < req_level:
        term.clear()
        term.print(f"{ally_data['name']} is not experienced enough to learn this skill.")
        term.print(f"Required: Level {req_level} | Current: Level {ally_level}")
        term.pause()
        return
    
    # ── Cap check: if ally already knows 3 skills, must replace one ──
    learned_list = ally_data.get("learned_skills", [])
    replaced_skill_id = None  # Track which skill is being replaced
    
    if len(learned_list) >= MAX_LEARNED_SKILLS:
        # Show replacement menu
        term.clear()
        term.print(f"=== SKILL SLOTS FULL ({len(learned_list)}/{MAX_LEARNED_SKILLS}) ===")
        term.print(f"{ally_data['name']} already knows the maximum number of skills.")
        term.print(f"You must replace an existing skill to learn {skill_name}.")
        term.print()
        
        # Build replacement options with skill names
        replace_options = []
        for sid in learned_list:
            sdef = get_learnable_skill_def(sid)
            sname = sdef.get("name", sid) if sdef else sid
            mastery = ally_data.get("skill_mastery", {}).get(sid, 0)
            replace_options.append(f"{sname} (Mastery: {mastery})")
        
        replace_choice = term.menu(
            replace_options + ["Cancel — don't learn new skill"],
            prompt="Choose a skill to replace:",
            allow_cancel=True
        )
        
        if replace_choice < 0 or replace_choice >= len(learned_list):
            return  # Cancelled
        
        replaced_skill_id = learned_list[replace_choice]
        replaced_sdef = get_learnable_skill_def(replaced_skill_id)
        replaced_name = replaced_sdef.get("name", replaced_skill_id) if replaced_sdef else replaced_skill_id
        
        # Confirm replacement
        term.clear()
        term.print(f"Replace {replaced_name} with {skill_name}?")
        term.print(f"New skill: {chosen_skill_def.get('description', '')}")
        term.print(f"Tier: {TIER_LABELS.get(tier, '?')} ({TIER_NAMES.get(tier, 'Unknown')}) | Cost: {exp_cost} EXP")
        term.print(f"\n⚠ This will permanently forget {replaced_name} and all its mastery progress.")
        
        if not term.confirm("Proceed with replacement?"):
            return
    else:
        # Confirm teaching (normal path)
        term.clear()
        term.print(f"Teach {ally_data['name']} the skill: {skill_name}?")
        term.print(f"Description: {chosen_skill_def.get('description', '')}")
        term.print(f"Tier: {TIER_LABELS.get(tier, '?')} ({TIER_NAMES.get(tier, 'Unknown')})")
        term.print(f"Learning cost: {exp_cost} EXP")
        
        if not term.confirm("Proceed with teaching?"):
            return
    
    # Update the active party ally directly (recruited allies are not in house)
    from .house import get_house_data, save_house_data
    house_data = get_house_data(player)
    
    # Find and update the active party ally
    success = False
    for party_ally in player.get("allies", []):
        if party_ally.get("name") == ally_data['name']:
            if replaced_skill_id:
                success = replace_ally_learned_skill(party_ally, replaced_skill_id, chosen_skill_id)
            else:
                success = teach_ally_skill(party_ally, chosen_skill_id)
            if success:
                if replaced_skill_id:
                    term.print(f"\n{ally_data['name']} replaced {replaced_name} and is now learning {skill_name}!")
                else:
                    term.print(f"\n{ally_data['name']} is now learning {skill_name}!")
                term.print(f"Progress: 0 / {exp_cost} EXP")
            break
    
    # Also update the house copy if she exists there (for non-recruited girls)
    if success:
        for girl in house_data:
            if girl['name'] == ally_data['name']:
                if replaced_skill_id:
                    replace_ally_learned_skill(girl, replaced_skill_id, chosen_skill_id)
                else:
                    teach_ally_skill(girl, chosen_skill_id)
                break
        save_house_data(player, house_data)
    else:
        term.print(f"\nFailed to teach skill (already learning, already knows it, or level too low).")
    
    term.pause()


# ── Training Dummy ────────────────────────────────────────────────────────────

def _dummy_spar_flow(player):
    """Show dummy configuration and launch sparring.

    In terminal mode, runs combat directly via spar_with_dummy().
    In GUI/FacilityScreen mode, stores config on player and returns
    so the city screen can launch CombatScreen.
    """
    from combat.dummy import (
        DEFAULT_DUMMY_CONFIG, create_dummy_enemy,
        spar_with_dummy, prepare_dummy_for_gui,
    )
    from combat.elemental import ELEMENTS

    dummy_state = DEFAULT_DUMMY_CONFIG.copy()

    while True:
        result = _dummy_config_menu(dummy_state)
        if result == "start":
            break
        elif result == "back":
            return

    # Build the dummy enemy config
    config = _build_dummy_config(dummy_state)

    # Check if we're running in GUI/FacilityScreen mode
    if get_terminal() is not None:
        # GUI mode: replace the facility's on_close callback to launch
        # CombatScreen directly, bypassing _after_facility entirely.
        # This avoids issues with the CityScreen having been destroyed.
        t = get_terminal()
        screen = t._screen
        if screen is not None:
            player["_pending_dummy_combat"] = config
            # Replace on_close so when the facility closes, it opens combat
            screen.on_close = lambda _result: _launch_dummy_combat_from_facility(
                screen, player
            )
        term.print("\nEntering sparring arena...")
        return
    else:
        # Terminal mode: run combat directly
        spar_with_dummy(player, config)


def _dummy_config_menu(dummy_state):
    """Show the dummy configuration menu using term API (GUI-compatible)."""
    from combat.elemental import ELEMENTS

    while True:
        res = dummy_state.get("elemental_res", {})
        hp = dummy_state.get("hp", 999999)
        str_mod = dummy_state.get("str_mod", -100)
        con_mod = dummy_state.get("con_mod", 0)
        dex_mod = dummy_state.get("dex_mod", -100)

        term.clear()
        term.print("=== TRAINING DUMMY CONFIGURATION ===")
        term.print(f"  HP:       {hp}")
        term.print(f"  STR mod:  {str_mod}  (negative = harmless)")
        term.print(f"  CON mod:  {con_mod}")
        term.print(f"  DEX mod:  {dex_mod}  (negative = easy flee)")

        # Summarise resistances
        res_parts = []
        for el in ELEMENTS:
            val = res.get(el, 0.0)
            if val != 0.0:
                res_parts.append(f"{el[:4].capitalize()}:{val*100:+.0f}%")
        if res_parts:
            term.print(f"  Resists:  {', '.join(res_parts)}")
        else:
            term.print(f"  Resists:  all neutral (0%)")

        choice = term.menu([
            "Change HP",
            "Change Strength mod",
            "Change Constitution mod",
            "Change Dexterity mod",
            "Elemental Resistances",
            "Reset to Defaults",
            "START SPARRING",
            "Back to Barracks",
        ], prompt="Adjust the training dummy:")

        if choice == 0:
            _set_numeric_term(dummy_state, "hp", "HP", 1, 99999999)
        elif choice == 1:
            _set_numeric_term(dummy_state, "str_mod", "STR mod", -200, 200)
        elif choice == 2:
            _set_numeric_term(dummy_state, "con_mod", "CON mod", -200, 200)
        elif choice == 3:
            _set_numeric_term(dummy_state, "dex_mod", "DEX mod", -200, 200)
        elif choice == 4:
            _configure_resistances_term(dummy_state)
        elif choice == 5:
            dummy_state.clear()
            dummy_state.update(DEFAULT_DUMMY_CONFIG)
            term.print("Dummy reset to defaults.")
            term.pause()
        elif choice == 6:
            return "start"
        elif choice in (7, -1):
            return "back"


def _set_numeric_term(dummy_state, key, label, min_val, max_val):
    """Prompt for a numeric value using term API."""
    current = dummy_state.get(key, "?")
    val_str = term.input(f"Current {label}: {current}\nNew value ({min_val}-{max_val}): ")
    try:
        val = int(val_str.strip()) if val_str else None
        if val is not None and min_val <= val <= max_val:
            dummy_state[key] = val
        elif val is not None:
            term.print(f"Value must be between {min_val} and {max_val}.")
            term.pause()
    except ValueError:
        term.print("Invalid number.")
        term.pause()


def _configure_resistances_term(dummy_state):
    """Sub-menu for elemental resistances using term API."""
    from combat.elemental import ELEMENTS

    res = dummy_state.setdefault("elemental_res", {el: 0.0 for el in ELEMENTS})
    el_list = list(ELEMENTS)

    while True:
        term.clear()
        term.print("=== ELEMENTAL RESISTANCES ===")
        term.print("  (Positive = resist, Negative = weakness, 0 = neutral)")
        options = []
        for el in el_list:
            val = res.get(el, 0.0)
            pct = f"{val*100:+.0f}%"
            options.append(f"{el.capitalize():12s} {pct}")
        options.append("Back")

        choice = term.menu(options, prompt="Select element to adjust:")
        if 0 <= choice < len(el_list):
            el = el_list[choice]
            _set_float_term(res, el, f"{el.capitalize()} resistance", -1.0, 1.0)
        else:
            return


def _set_float_term(d, key, label, min_val, max_val):
    """Prompt for a float value using term API."""
    current = d.get(key, 0.0)
    val_str = term.input(f"Current {label}: {current:+.0%}\nNew value ({min_val:.1f}-{max_val:.1f}): ")
    try:
        val = float(val_str.strip()) if val_str else None
        if val is not None and min_val <= val <= max_val:
            d[key] = val
        elif val is not None:
            term.print(f"Value must be between {min_val} and {max_val}.")
            term.pause()
    except ValueError:
        term.print("Invalid number.")
        term.pause()


def _build_dummy_config(dummy_state):
    """Build the final dummy config dict from the state dict."""
    from combat.elemental import ELEMENTS
    return {
        "hp": dummy_state.get("hp", 999999),
        "str_mod": dummy_state.get("str_mod", -100),
        "con_mod": dummy_state.get("con_mod", 0),
        "dex_mod": dummy_state.get("dex_mod", -100),
        "elemental_res": {
            el: dummy_state.get("elemental_res", {}).get(el, 0.0)
            for el in ELEMENTS
        },
    }


def _launch_dummy_combat_from_facility(facility_screen, player):
    """Called from FacilityScreen.on_close to launch dummy combat directly.

    This bypasses the CityScreen._after_facility flow entirely, avoiding
    issues with the CityScreen having been destroyed during switch_to.
    Runs on the main thread (called from _do_finish via after()).
    """
    config = player.pop("_pending_dummy_combat", None)
    if not config:
        # Fallback: go to city
        from gui.screens.city_screen import CityScreen
        facility_screen.sm.switch_to(CityScreen, push_history=False)
        return

    sm = facility_screen.sm
    sm.log("Entering sparring arena...")
    sm.update_top_bar("⚔ Training Dummy")

    def dummy_combat_func(p, floor=None, enemies=None):
        """Custom combat function for the training dummy."""
        from combat.dummy import create_dummy_enemy, _run_dummy_combat

        dummy = create_dummy_enemy(config)
        if enemies is not None:
            enemies.clear()
            enemies.append(dummy)

        return _run_dummy_combat(p, config, enemies=enemies)

    from gui.screens.combat_screen import CombatScreen
    sm.switch_to(
        CombatScreen,
        enemy_keys=[],
        combat_context="training",
        combat_func=dummy_combat_func,
        on_result=lambda result: _after_dummy_combat_from_facility(sm, player, result),
    )


def _after_dummy_combat_from_facility(sm, player, result):
    """Handle return from dummy sparring — go back to city."""
    sm.log(f"Sparring ended: {result.upper()}")
    if player and player.get("current_hp", 1) <= 0:
        from gui.screens.death_screen import DeathScreen
        def _continue():
            from utils import apply_death_penalty
            apply_death_penalty(player)
            from gui.screens.city_screen import CityScreen
            sm.switch_to(CityScreen, push_history=False)
        def _quit():
            sm.player = None
            from gui.screens.main_menu_screen import MainMenuScreen
            sm.switch_to(MainMenuScreen)
        sm.switch_to(DeathScreen, on_continue=_continue, on_quit=_quit)
    else:
        from gui.screens.city_screen import CityScreen
        sm.switch_to(CityScreen, push_history=False)
