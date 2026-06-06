# save_load.py
import json
import os
import glob

SAVE_DIR = "savefile"
SAVE_PREFIX = "savegame_"

def ensure_save_directory():
    """Ensure the save directory exists so Python doesn't throw errors."""
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)

def get_filename(slot):
    """Return filename inside the designated savefile folder."""
    ensure_save_directory()
    return os.path.join(SAVE_DIR, f"{SAVE_PREFIX}{slot}.json")

def list_saves():
    """Return a dict {slot: player_name} for all existing save files inside SAVE_DIR."""
    saves = {}
    pattern = os.path.join(SAVE_DIR, f"{SAVE_PREFIX}*.json")
    
    for fname in glob.glob(pattern):
        try:
            base_name = os.path.basename(fname)
            slot = int(base_name.split('_')[-1].split('.')[0])
            with open(fname, 'r') as f:
                data = json.load(f)
                name = data.get("name", "Unknown")
                saves[slot] = name
        except (ValueError, json.JSONDecodeError, KeyError):
            continue
    return saves

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
    with open(filename, 'w') as f:
        json.dump(player, f, indent=2)

def load_game(slot):
    """Load player data from savefile/savegame_<slot>.json, or return None."""
    filename = get_filename(slot)
    if not os.path.exists(filename):
        return None
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None