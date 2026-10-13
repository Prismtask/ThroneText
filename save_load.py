# save_load.py
import json
import os
import glob
import sys

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SAVE_DIR = os.path.join(BASE_DIR, "savefile")
SAVE_PREFIX = "savegame_"


def _make_json_safe(obj):
    """Recursively convert non-JSON-serializable types (e.g. set→list)."""
    if isinstance(obj, dict):
        return {k: _make_json_safe(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_make_json_safe(v) for v in obj]
    elif isinstance(obj, set):
        return list(obj)
    return obj

def ensure_save_directory():
    """Ensure the save directory exists so Python doesn't throw errors."""
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)

def get_filename(slot):
    """Return filename inside the designated savefile folder."""
    ensure_save_directory()
    return os.path.join(SAVE_DIR, f"{SAVE_PREFIX}{slot}.json")

def list_save_details():
    """Return {slot: {"name", "class", "race", "level"}} for all existing save files.

    Used by the GUI save browser to render one info card per save.  Unknown,
    corrupt, or non-dict files are skipped, mirroring list_saves().
    """
    details = {}
    pattern = os.path.join(SAVE_DIR, f"{SAVE_PREFIX}*.json")

    for fname in glob.glob(pattern):
        try:
            base_name = os.path.basename(fname)
            slot = int(base_name.split('_')[-1].split('.')[0])
            with open(fname, 'r', encoding='utf-8') as f:
                data = json.load(f)
            details[slot] = {
                "name": data.get("name", "Unknown"),
                "class": data.get("class", "Unknown"),
                "race": data.get("race", "Unknown"),
                "level": data.get("level", 1),
            }
        except (ValueError, json.JSONDecodeError, KeyError, AttributeError):
            continue
    return details


def list_saves():
    """Return a dict {slot: player_name} for all existing save files inside SAVE_DIR."""
    return {slot: info["name"] for slot, info in list_save_details().items()}

def get_next_free_slot():
    """Finds the lowest positive slot number that doesn't have a save file yet."""
    saves = list_saves()
    slot = 1
    while slot in saves:
        slot += 1
    return slot

def save_game(player):
    """Write player dict to savefile/savegame_<slot>.json using player['save_slot']."""
    slot = player.get("save_slot")
    if slot is None:
        raise ValueError("Player dict missing 'save_slot' key.")
    filename = get_filename(slot)
    safe_data = _make_json_safe(player)
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(safe_data, f, indent=2, ensure_ascii=False)

def load_game(slot):
    """Load player data from savefile/savegame_<slot>.json, or return None."""
    filename = get_filename(slot)
    if not os.path.exists(filename):
        return None
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # A loaded game always resumes in a city, so any run-only dungeon
        # flags baked into the save (e.g. pandemonium_mode from an in-dungeon
        # save or an interrupted run) are stale. Clear it here as a safety
        # net; it is re-established on dungeon entry.
        data.pop("pandemonium_mode", None)
        # Event Horizon: transient in-run gate — never valid after a load
        # (suspended runs persist via player["event_horizon"], not this flag).
        data.pop("_eh_in_run", None)
        # Run-end aftermath stash — display-only, never valid after a load.
        data.pop("_eh_last_summary", None)
        # Rift effects live in player["event_horizon"] while suspended, never
        # on actors (docs §6.3). Scrub baked-in entries from saves written
        # before detach-on-suspend — legacy sweep included, since pre-marking
        # battle-start debuffs (e.g. a stuck DT+8%) carry no tag.
        eh_state = data.get("event_horizon")
        if isinstance(eh_state, dict) and (eh_state.get("run_active")
                                           or eh_state.get("best_room")):
            from event_horizon import strip_event_horizon_effects
            strip_event_horizon_effects(data, legacy=True)
        return data
    except (json.JSONDecodeError, IOError, UnicodeDecodeError):
        return None
    
def delete_save(slot):
    """Delete savefile/savegame_<slot>.json if it exists. Returns True if successful."""
    filename = get_filename(slot)
    if os.path.exists(filename):
        try:
            os.remove(filename)
            return True
        except OSError:
            return False
    return False