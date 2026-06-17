#!/usr/bin/env python3
"""
Split enemies.py into YAML files by race, sorted by level.
Run this script from the directory containing your enemies.py.
"""

import os
import sys
import importlib.util
from collections import defaultdict
import yaml

def load_enemies_from_file(filepath):
    """Dynamically import enemies.py and return the ENEMIES dict."""
    spec = importlib.util.spec_from_file_location("enemies_module", filepath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, "ENEMIES", {})

def group_and_sort(enemies):
    groups = defaultdict(list)
    for key, data in enemies.items():
        race = data.get("race", "Unknown")
        groups[race].append((key, data))
    
    # Sort each group by level (ascending), then by name
    for race in groups:
        groups[race].sort(key=lambda item: (item[1].get("level", 0), item[0]))
    
    # Convert list of tuples back to a dict for each race
    return {race: dict(items) for race, items in groups.items()}

def write_yaml_files(groups, output_dir="enemies_yaml"):
    os.makedirs(output_dir, exist_ok=True)
    
    # Write one YAML file per race
    for race, enemies_dict in groups.items():
        filename = race.lower().replace(" ", "_") + ".yaml"
        filepath = os.path.join(output_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            yaml.dump({race: enemies_dict}, f, allow_unicode=True, sort_keys=False, indent=2)
    
    # Write a combined file with all races
    combined_path = os.path.join(output_dir, "all_enemies.yaml")
    with open(combined_path, "w", encoding="utf-8") as f:
        yaml.dump(groups, f, allow_unicode=True, sort_keys=False, indent=2)
    
    print(f"YAML files written to '{output_dir}/'")

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Join it with the filename
    enemies_file = os.path.join(script_dir, "enemies.py")
    if not os.path.isfile(enemies_file):
        print(f"Error: {enemies_file} not found.")
        sys.exit(1)
    
    print(f"Loading enemies from {enemies_file} ...")
    enemies = load_enemies_from_file(enemies_file)
    print(f"Loaded {len(enemies)} enemy entries.")
    
    groups = group_and_sort(enemies)
    print(f"Grouped into {len(groups)} races.")
    
    output_dir = "enemies_yaml"
    write_yaml_files(groups, output_dir)
    print("Done!")

if __name__ == "__main__":
    main()