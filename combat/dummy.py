# combat/dummy.py — Training dummy for damage testing in the barracks.
"""
Provides a configurable training dummy enemy with adjustable stats and
elemental resistances. The dummy is a passive target: its stats are set
so that it always deals 0 damage and the player can always flee.

Usage (terminal mode):
    from combat.dummy import spar_with_dummy
    spar_with_dummy(player)

Usage (GUI mode):
    The barracks sets player['_pending_dummy_combat'] with the dummy
    configuration.  The city screen then launches CombatScreen with
    the pre-built dummy enemy dict.
"""

from combat.combat_engine import combat
from combat.combat_io import c_print, c_input, c_clear
from combat.elemental import ELEMENTS


# ── Default dummy configuration ──────────────────────────────────────────────

DEFAULT_DUMMY_CONFIG = {
    "hp": 999999,
    "str_mod": -100,
    "con_mod": 0,
    "dex_mod": -100,
    "elemental_res": {el: 0.0 for el in ELEMENTS},
}


def create_dummy_enemy(config=None):
    """Build a training dummy enemy dict from configuration.

    Args:
        config: dict with keys hp, str_mod, con_mod, dex_mod, elemental_res.
                Defaults to DEFAULT_DUMMY_CONFIG if None.

    Returns:
        Enemy dict ready for the combat engine (no key lookup needed).
    """
    if config is None:
        config = DEFAULT_DUMMY_CONFIG.copy()

    hp = config.get("hp", 999999)
    res = config.get("elemental_res", {})

    return {
        "key": "_training_dummy",  # Placeholder key for compatibility
        "name": "Training Dummy",
        "hp": hp,
        "max_hp": hp,
        "str_mod": config.get("str_mod", -100),
        "con_mod": config.get("con_mod", 0),
        "dex_mod": config.get("dex_mod", -100),
        "level": 1,
        "multiplier": 1.0,
        "monster_girl": False,
        "dialogue": {},
        "elemental_res": {el: res.get(el, 0.0) for el in ELEMENTS},
        "elemental_dmg": {el: 1.0 for el in ELEMENTS},
        "active_debuffs": [],
        "is_dummy": True,
    }


def _get_dummy_config(dummy_state):
    """Merge saved dummy state with defaults."""
    config = DEFAULT_DUMMY_CONFIG.copy()
    config.update(dummy_state)
    return config


# ── Configuration menus ──────────────────────────────────────────────────────

def _configure_dummy(dummy_state):
    """Interactive menu to adjust dummy stats. Returns updated dummy_state dict."""
    while True:
        c_clear()
        c_print("=== TRAINING DUMMY CONFIGURATION ===")
        c_print(f"  1. HP:          {dummy_state.get('hp', 999999)}")
        c_print(f"  2. Strength:    {dummy_state.get('str_mod', -100)}  (negative = harmless)")
        c_print(f"  3. Constitution:{dummy_state.get('con_mod', 0)}")
        c_print(f"  4. Dexterity:   {dummy_state.get('dex_mod', -100)}  (negative = easy flee)")
        c_print(f"  5. Elemental Resistances")
        c_print(f"  6. Reset to Defaults")
        c_print(f"  7. Start Sparring")
        c_print(f"  8. Back to Barracks")

        choice = c_input("Choose: ").strip()
        if choice == "1":
            _set_numeric(dummy_state, "hp", "HP", 1, 99999999)
        elif choice == "2":
            _set_numeric(dummy_state, "str_mod", "Strength mod", -200, 200)
        elif choice == "3":
            _set_numeric(dummy_state, "con_mod", "Constitution mod", -200, 200)
        elif choice == "4":
            _set_numeric(dummy_state, "dex_mod", "Dexterity mod", -200, 200)
        elif choice == "5":
            _configure_resistances(dummy_state)
        elif choice == "6":
            dummy_state.clear()
            dummy_state.update(DEFAULT_DUMMY_CONFIG)
            c_print("Dummy reset to defaults.")
            c_input("Press Enter...")
        elif choice == "7":
            return "start"
        elif choice == "8":
            return "back"


def _set_numeric(dummy_state, key, label, min_val, max_val):
    """Prompt for a numeric value and store it."""
    c_print(f"\nCurrent {label}: {dummy_state.get(key, '?')}")
    try:
        val = int(c_input(f"New {label} ({min_val}-{max_val}): ").strip())
        if min_val <= val <= max_val:
            dummy_state[key] = val
        else:
            c_print(f"Value must be between {min_val} and {max_val}.")
            c_input("Press Enter...")
    except ValueError:
        c_print("Invalid number.")
        c_input("Press Enter...")


def _configure_resistances(dummy_state):
    """Sub-menu for elemental resistances."""
    res = dummy_state.setdefault("elemental_res", {el: 0.0 for el in ELEMENTS})
    while True:
        c_clear()
        c_print("=== ELEMENTAL RESISTANCES ===")
        c_print("  (Positive = resist, Negative = weakness, 0 = neutral)")
        el_list = list(ELEMENTS)
        for i, el in enumerate(el_list):
            val = res.get(el, 0.0)
            pct = f"{val*100:+.0f}%"
            c_print(f"  {i+1}. {el.capitalize():12s} {pct}")
        c_print(f"  {len(el_list)+1}. Back")
        choice = c_input("Choose: ").strip()
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(el_list):
                el = el_list[idx]
                _set_float(res, el, f"{el.capitalize()} resistance", -1.0, 1.0)
            elif idx == len(el_list):
                return
        else:
            return


def _set_float(d, key, label, min_val, max_val):
    """Prompt for a float value and store it."""
    c_print(f"\nCurrent {label}: {d.get(key, 0.0):+.0%}")
    try:
        val = float(c_input(f"New {label} ({min_val:.1f}-{max_val:.1f}): ").strip())
        if min_val <= val <= max_val:
            d[key] = val
        else:
            c_print(f"Value must be between {min_val} and {max_val}.")
            c_input("Press Enter...")
    except ValueError:
        c_print("Invalid number.")
        c_input("Press Enter...")


# ── Terminal-mode sparring ───────────────────────────────────────────────────

def spar_with_dummy(player, dummy_config=None):
    """Launch a sparring match against the training dummy (terminal mode).

    Args:
        player: The player dict.
        dummy_config: Optional dict overriding default dummy stats.

    Returns:
        Combat result string ('victory', 'fled', 'dead').
    """
    if dummy_config is None:
        dummy_config = DEFAULT_DUMMY_CONFIG.copy()

    dummy = create_dummy_enemy(dummy_config)

    c_clear()
    c_print("=== SPARRING WITH TRAINING DUMMY ===")
    c_print(f"Dummy HP: {dummy['hp']}")
    c_print("The dummy stands motionless, waiting for your strikes.")
    c_print("(Flee to leave at any time — it won't stop you.)")
    c_input("Press Enter to begin...")

    # Temporarily disable Pandemonium flee blocking so the player can always
    # leave the sparring arena.
    result = _run_dummy_combat(player, dummy_config)

    c_print(f"\nSparring ended: {result.upper()}")
    if result == "victory":
        c_print("The training dummy crumbles to pieces! (It will be rebuilt.)")
    elif result == "fled":
        c_print("You step back from the training dummy, satisfied with your practice.")

    return result


def _run_dummy_combat(player, dummy_config, enemies=None):
    """Run a combat session with the dummy, ensuring flee always works.

    Temporarily saves and clears Pandemonium mode/curse so that flee is
    never blocked during sparring. Restores original state afterward.

    Args:
        player: The player dict.
        dummy_config: Dummy configuration dict.
        enemies: Optional pre-built enemies list. If provided, the dummy
                 is appended to this list (GUI mode for shared HUD state).
                 If None, a new list is created (terminal mode).
    """
    saved_pmode = player.get("pandemonium_mode", False)
    saved_pcurse = player.get("pandemonium_curse", False)
    # Clear any flee-blocking curses
    player["pandemonium_mode"] = False
    player["pandemonium_curse"] = False

    try:
        if enemies is not None:
            # GUI mode: enemies is self.enemies (shared with HUD, already populated)
            combat_enemies = enemies
        else:
            combat_enemies = [create_dummy_enemy(dummy_config)]
        return combat(player, [], enemies=combat_enemies)
    finally:
        player["pandemonium_mode"] = saved_pmode
        player["pandemonium_curse"] = saved_pcurse


# ── GUI helper ────────────────────────────────────────────────────────────────

def prepare_dummy_for_gui(player, dummy_config=None):
    """Prepare the dummy config and store it on the player for the GUI to pick up.

    Called from barracks when running in GUI/FacilityScreen mode.
    The city screen's _after_facility will detect the flag and launch CombatScreen.

    Args:
        player: The player dict.
        dummy_config: Optional dict overriding default dummy stats.
    """
    if dummy_config is None:
        dummy_config = DEFAULT_DUMMY_CONFIG.copy()
    player["_pending_dummy_combat"] = dummy_config
