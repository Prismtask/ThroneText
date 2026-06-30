import yaml
from collections import defaultdict
import os

ATTRIBUTES = ["Strength", "Constitution", "Dexterity", "Wisdom", "Learning", "Charisma"]

RACE_BIAS = {
    "Human":       (0.17, 0.17, 0.17, 0.17, 0.16, 0.16),
    "Elf":         (0.10, 0.12, 0.25, 0.20, 0.18, 0.15),
    "Dwarf":       (0.25, 0.25, 0.10, 0.15, 0.12, 0.13),
    "Halfling":    (0.08, 0.15, 0.25, 0.18, 0.17, 0.17),
    "Orc":         (0.30, 0.25, 0.12, 0.08, 0.10, 0.15),
    "Gnome":       (0.10, 0.15, 0.15, 0.20, 0.25, 0.15),
    "Tiefling":    (0.12, 0.12, 0.18, 0.12, 0.18, 0.28),
    "Dragonborn":  (0.25, 0.25, 0.12, 0.15, 0.10, 0.13),
    "Beast":       (0.22, 0.22, 0.22, 0.12, 0.10, 0.12),
    "Fey":         (0.10, 0.12, 0.22, 0.20, 0.18, 0.18),
    "Goblin":      (0.12, 0.14, 0.25, 0.10, 0.14, 0.25),
    "Demon":       (0.20, 0.18, 0.18, 0.12, 0.12, 0.20),
    "Lizardfolk":  (0.20, 0.20, 0.20, 0.15, 0.10, 0.15),
    "Elemental":   (0.18, 0.22, 0.16, 0.14, 0.18, 0.12),
    "Giant":       (0.30, 0.28, 0.08, 0.10, 0.10, 0.14),
    "Undead":      (0.18, 0.20, 0.18, 0.14, 0.16, 0.14),
    "Shadow":      (0.12, 0.14, 0.28, 0.16, 0.15, 0.15),
    "Vampire":     (0.16, 0.16, 0.22, 0.14, 0.14, 0.18),
    "Clockwork":   (0.18, 0.22, 0.14, 0.12, 0.20, 0.14),
    "Abomination": (0.25, 0.25, 0.12, 0.12, 0.12, 0.14),
    "Construct":   (0.22, 0.25, 0.12, 0.12, 0.14, 0.15),
    "Dragonkin":   (0.25, 0.22, 0.16, 0.14, 0.12, 0.11),
}
FALLBACK = (0.17, 0.17, 0.17, 0.17, 0.16, 0.16)

def get_bias(race):
    return RACE_BIAS.get(race, FALLBACK)

def distribute_points(level, existing_mods, race):
    # Total points: roughly 1 per level + 8 base, but at least 6
    total = max(6, level + 8)   # level 40 -> 48
    bias = get_bias(race)

    # Start with race-biased distribution
    base = [bias[i] * total for i in range(6)]

    # Add extra from existing mods (each mod adds its value directly to that stat)
    extra = [0]*6
    for attr, val in existing_mods.items():
        if attr in ATTRIBUTES:
            idx = ATTRIBUTES.index(attr)
            extra[idx] = max(0, val)   # keep positive

    raw = [base[i] + extra[i] for i in range(6)]
    raw_sum = sum(raw)
    if raw_sum == 0:
        raw = [total/6]*6
        raw_sum = total

    # Normalise to total
    factor = total / raw_sum
    final = [max(1, int(round(v * factor))) for v in raw]

    # Adjust rounding errors
    diff = total - sum(final)
    if diff != 0:
        order = sorted(range(6), key=lambda i: final[i], reverse=True)
        for i in order:
            if diff > 0:
                final[i] += 1
                diff -= 1
                if diff == 0:
                    break
            elif diff < 0 and final[i] > 1:
                final[i] -= 1
                diff += 1
                if diff == 0:
                    break

    return dict(zip(ATTRIBUTES, final))

def process_entry(entry):
    if not entry or not isinstance(entry, dict):
        return
    level = entry.get('level', 1)
    race = entry.get('race', 'Human')
    old_mods = entry.get('mods', {})
    new_mods = distribute_points(level, old_mods, race)
    entry['mods'] = new_mods

def process_file(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    if data is None or not isinstance(data, dict):
        print(f"Skipping {filename}: not a valid YAML dict")
        return

    for key, value in data.items():
        if value is None:
            continue
        # Flat format: top-level key is an enemy ID (e.g. monster_girls.yaml)
        if isinstance(value, dict) and 'level' in value:
            process_entry(value)
        # Grouped format: top-level key is a category, value is dict of enemies
        elif isinstance(value, dict):
            for sub_key, entry in value.items():
                process_entry(entry)

    with open(filename, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
    print(f"Rebalanced: {filename}")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    enemies_dir = os.path.join(base_dir, "resources", "enemies", "enemies_data")

    files_to_process = [
        "all_enemies.yaml",
        "monster_girls.yaml",
        "superbosses.yaml",
        "sea_caves.yaml",
    ]

    for filename in files_to_process:
        filepath = os.path.join(enemies_dir, filename)
        if os.path.exists(filepath):
            process_file(filepath)
        else:
            print(f"Warning: {filepath} not found, skipping.")

    print("Done.")