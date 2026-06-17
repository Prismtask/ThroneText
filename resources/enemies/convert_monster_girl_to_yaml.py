"""
Convert monster_girls.py to a single YAML file, sorted by level.
Run this script from the directory containing your monster_girls.py.
"""

import os
import sys
import importlib.util
import yaml

def load_monster_girls_from_file(filepath):
    """Dynamically import monster_girls.py and return the MONSTER_GIRLS dict."""
    spec = importlib.util.spec_from_file_location("monster_girls_module", filepath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, "MONSTER_GIRLS", {})

def sort_by_level(monster_girls):
    """Sort items by level, then by key for stability."""
    items = list(monster_girls.items())
    items.sort(key=lambda item: (item[1].get("level", 0), item[0]))
    return dict(items)  # Python 3.7+ preserves insertion order

def write_yaml(data, output_file="monster_girls_sorted.yaml"):
    with open(output_file, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False, indent=2)
    print(f"Written to {output_file}")

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Join it with the filename
    mg_file = os.path.join(script_dir, "monster_girls.py")
    if not os.path.isfile(mg_file):
        print(f"Error: {mg_file} not found.")
        sys.exit(1)

    print(f"Loading monster girls from {mg_file} ...")
    monster_girls = load_monster_girls_from_file(mg_file)
    print(f"Loaded {len(monster_girls)} entries.")

    sorted_data = sort_by_level(monster_girls)

    write_yaml(sorted_data, "monster_girls_sorted.yaml")
    print("Done!")

if __name__ == "__main__":
    main()