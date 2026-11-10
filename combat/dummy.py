# combat/dummy.py — Training dummy for damage testing in the barracks.
"""
Provides a configurable training dummy enemy with adjustable stats and
elemental resistances. The dummy is a passive target: its stats are set
so that it always deals 0 damage and the player can always flee.

Usage (GUI):
    The barracks sets player['_pending_dummy_combat'] with the dummy
    configuration.  The city screen then launches CombatScreen with
    the pre-built dummy enemy dict.
"""

from combat.combat_engine import combat
from combat.elemental import ELEMENTS


# ── Default dummy configuration ──────────────────────────────────────────────

DEFAULT_DUMMY_CONFIG = {
    "hp": 999999,
    "str_mod": -100,
    "con_mod": 0,
    "dex_mod": -100,
    "elemental_res": {el: 1.0 for el in ELEMENTS},
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
        "elemental_res": {el: res.get(el, 1.0) for el in ELEMENTS},
        "elemental_dmg": {el: 1.0 for el in ELEMENTS},
        "active_debuffs": [],
        "is_dummy": True,
    }


# ── GUI helpers ───────────────────────────────────────────────────────────────

def _run_dummy_combat(player, dummy_config, enemies=None):
    """Run a combat session with the dummy, ensuring flee always works.

    Temporarily saves and clears Pandemonium mode/curse so that flee is
    never blocked during sparring. Restores original state afterward.

    Args:
        player: The player dict.
        dummy_config: Dummy configuration dict.
        enemies: Optional pre-built enemies list. If provided, the dummy
                 is appended to this list (GUI CombatScreen shared HUD state).
                 If None, a new list is created (tests/headless).
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
