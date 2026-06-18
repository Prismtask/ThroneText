#!/usr/bin/env python3
"""
Split enemies.py into YAML files by race, but move ALL superbosses
(super_boss: True) into a separate 'superbosses.yaml' file.
Sorted by level within each file.
"""

import os
import sys
import importlib.util
from collections import defaultdict
import yaml

# -------------------------------------------------------------------
# 1. Load the existing ENEMIES dict
# -------------------------------------------------------------------

def load_enemies_from_file(filepath):
    spec = importlib.util.spec_from_file_location("enemies_module", filepath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, "ENEMIES", {})

# -------------------------------------------------------------------
# 2. Group by race, but pull out superbosses first
# -------------------------------------------------------------------

def group_and_sort(enemies):
    groups = defaultdict(list)      # race -> list of (key, data)
    superbosses = []                # list of (key, data)

    for key, data in enemies.items():
        if data.get("super_boss", False):
            superbosses.append((key, data))
        else:
            race = data.get("race", "Unknown")
            groups[race].append((key, data))

    # Sort each race group by level, then by key
    for race in groups:
        groups[race].sort(key=lambda item: (item[1].get("level", 0), item[0]))

    # Sort superbosses by level
    superbosses.sort(key=lambda item: (item[1].get("level", 0), item[0]))

    # Convert to dicts (preserving order)
    result = {}
    for race, items in groups.items():
        result[race] = dict(items)

    if superbosses:
        result["Superbosses"] = dict(superbosses)

    return result

# -------------------------------------------------------------------
# 3. Write YAML files
# -------------------------------------------------------------------

def write_yaml_files(groups, output_dir="enemies_yaml"):
    os.makedirs(output_dir, exist_ok=True)

    # One file per group (race, plus Superbosses)
    for group_name, enemies_dict in groups.items():
        if group_name == "Superbosses":
            filename = "superbosses.yaml"
        else:
            filename = group_name.lower().replace(" ", "_") + ".yaml"

        filepath = os.path.join(output_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            yaml.dump({group_name: enemies_dict}, f, allow_unicode=True, sort_keys=False, indent=2)

    # Optional: write a single combined file
    combined_path = os.path.join(output_dir, "all_enemies.yaml")
    with open(combined_path, "w", encoding="utf-8") as f:
        yaml.dump(groups, f, allow_unicode=True, sort_keys=False, indent=2)

    print(f"YAML files written to '{output_dir}/'")

# -------------------------------------------------------------------
# 4. Main
# -------------------------------------------------------------------

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Join it with the filename
    enemies_file = os.path.join(script_dir, "enemy_dict_old.py")
    if not os.path.isfile(enemies_file):
        print(f"Error: {enemies_file} not found.")
        print("Run this script from the folder that contains enemies.py")
        sys.exit(1)

    print(f"Loading enemies from {enemies_file} ...")
    enemies = load_enemies_from_file(enemies_file)
    print(f"Loaded {len(enemies)} enemy entries.")

    groups = group_and_sort(enemies)
    print(f"Grouped into {len(groups)} categories (races + Superbosses).")

    output_dir = "enemies_yaml"
    write_yaml_files(groups, output_dir)
    print("Done!")

if __name__ == "__main__":
    main()