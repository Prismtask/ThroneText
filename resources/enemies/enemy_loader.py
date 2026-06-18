import yaml
import os

# Global containers for extra data extracted from YAML files
CAPTURE_MESSAGES = {}
AFFECTION_GIFTS = {}

def load_enemies():
    """Load enemies from all YAML files in enemies_data/.
    
    Handles three formats:
    1. Grouped: top-level keys are categories (races, "Superbosses", etc.),
       and each value is a dict of enemy entries.
    2. Flat: top-level keys are enemy IDs directly.
    3. Special: top-level keys "capture_messages" and "affection_gifts"
       are loaded into global dictionaries.
    """
    enemies = {}
    
    # Determine base directory
    if '__file__' in globals():
        base_dir = os.path.dirname(os.path.abspath(__file__))
    else:
        base_dir = os.path.dirname(os.path.abspath('resources/enemies.py'))
        if not os.path.exists(os.path.join(base_dir, 'enemies_data')):
            base_dir = os.getcwd()
    
    yaml_dir = os.path.join(base_dir, 'enemies_data')
    
    # Collect all YAML files
    yaml_files = [f for f in os.listdir(yaml_dir) 
                  if f.endswith(('.yaml', '.yml'))]
    
    for filename in yaml_files:
        filepath = os.path.join(yaml_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            continue
        
        if data is None or not isinstance(data, dict):
            continue
        
        for key, value in data.items():
            # --- Special sections --------------------------------------------------
            if key == "capture_messages" and isinstance(value, dict):
                # Merge capture messages (warn on duplicates)
                for sub_key, msg in value.items():
                    if sub_key in CAPTURE_MESSAGES:
                        print(f"Warning: duplicate capture message for '{sub_key}' in {filename}")
                    CAPTURE_MESSAGES[sub_key] = msg
                continue

            if key == "affection_gifts" and isinstance(value, dict):
                # Merge affection gift tables (warn on duplicates)
                for sub_key, gifts in value.items():
                    if sub_key in AFFECTION_GIFTS:
                        print(f"Warning: duplicate affection gifts for '{sub_key}' in {filename}")
                    AFFECTION_GIFTS[sub_key] = gifts
                continue

            # --- Enemy entries ----------------------------------------------------
            if not isinstance(value, dict):
                continue
            
            # Check if this is a single enemy entry (flat format)
            if "name" in value and "level" in value:
                enemies[key] = value
            else:
                # Assume it's a group (e.g., "Beast", "Superbosses")
                # Each sub-item should be an enemy
                for sub_key, sub_value in value.items():
                    if isinstance(sub_value, dict) and "name" in sub_value and "level" in sub_value:
                        if sub_key in enemies:
                            print(f"Warning: Duplicate enemy ID '{sub_key}' found in {filename}, overriding.")
                        enemies[sub_key] = sub_value
                    else:
                        print(f"Warning: Skipping unexpected entry '{sub_key}' in group '{key}' from {filename}")
    
    # Ensure consistent fields (optional)
    for enemy in enemies.values():
        enemy.setdefault('boss', False)
        enemy.setdefault('super_boss', False)
        enemy.setdefault('monster_girl', False)
    
    print(f"Total enemies loaded: {len(enemies)}")
    return enemies

ENEMIES = load_enemies()

# Alias for compatibility with existing imports
MONSTER_GIRL_MESSAGES = CAPTURE_MESSAGES

# Race/biome data (keep as before)
try:
    from .enemy_races import ENEMY_RACES
    from .biome_races import BIOME_RACES
except ImportError:
    ENEMY_RACES = {}
    BIOME_RACES = {}