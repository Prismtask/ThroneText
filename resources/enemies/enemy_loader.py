import yaml
import os

def load_enemies():
    """Load enemies from YAML files.
    - all_enemies.yaml: grouped by race (standard)
    - monster_girls.yaml: flat (special case — handled automatically)
    """
    enemies = {}
    # Handle both normal import and direct exec
    if '__file__' in globals():
        base_dir = os.path.dirname(os.path.abspath(__file__))
    else:
        base_dir = os.path.dirname(os.path.abspath('resources/enemies.py'))
        if not os.path.exists(os.path.join(base_dir, 'enemies_data')):
            base_dir = os.getcwd()
    
    yaml_dir = os.path.join(base_dir, 'enemies_data')
    
    # Load race-grouped enemies (all_enemies.yaml + per-race files if any)
    all_path = os.path.join(yaml_dir, 'all_enemies.yaml')
    if os.path.exists(all_path):
        with open(all_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            if isinstance(data, dict):
                for race, race_dict in data.items():
                    if isinstance(race_dict, dict):
                        for key, enemy in race_dict.items():
                            enemies[key] = enemy
    else:
        print(f"Warning: {all_path} not found")
    
    # Load monster_girls.yaml — flat structure, no race grouping
    # This is the special case you mentioned. Handled here so no other code breaks.
    mg_path = os.path.join(yaml_dir, 'monster_girls.yaml')
    if os.path.exists(mg_path):
        with open(mg_path, 'r', encoding='utf-8') as f:
            mg_data = yaml.safe_load(f)
            if isinstance(mg_data, dict):
                for key, enemy in mg_data.items():
                    # Ensure consistent structure with other enemies
                    enemy.setdefault('boss', False)
                    enemy.setdefault('super_boss', False)
                    enemies[key] = enemy
        print(f"Loaded {len(mg_data)} monster girls from flat YAML")
    else:
        print(f"Warning: {mg_path} not found")
    
    print(f"Total enemies loaded: {len(enemies)}")
    return enemies

ENEMIES = load_enemies()

# Race/biome data (with fallback)
try:
    from .enemy_races import ENEMY_RACES
    from .biome_races import BIOME_RACES
except ImportError:
    ENEMY_RACES = {}
    BIOME_RACES = {}