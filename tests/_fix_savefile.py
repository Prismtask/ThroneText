"""Script to fix the savefile with the 3 upgraded Wonderland quest items."""
import json

# Load savefile
with open('savefile/savegame_1.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# === 1. Build Grandmother's Axe +5 for Red Hood ===
grandmothers_axe = {
    "id": "grandmothers_axe",
    "name": "Grandmother's Axe +5",
    "type": "equipment",
    "rarity": "unique",
    "enhance": 5,
    "slot": "weapon",
    "mods": {"Strength": 32, "Dexterity": 24},
    "special": "grandmothers_axe",
    "unique": True,
    "drop_rarity": "unique",
    "scaling_stat": ["Strength", "Dexterity"],
    "elemental_dmg": {"physical": 1.4, "light": 1.3},
    "wonderland_only": True,
    "count": 1
}

# === 2. Build Ruby Slippers +5 for Dorothy ===
ruby_slippers = {
    "id": "ruby_slippers",
    "name": "Ruby Slippers +5",
    "type": "equipment",
    "rarity": "unique",
    "enhance": 5,
    "slot": "accessory",
    "mods": {"Dexterity": 19, "Charisma": 19},
    "special": "ruby_slippers",
    "unique": True,
    "drop_rarity": "unique",
    "elemental_res": {"magical": 1.2, "light": 1.3},
    "wonderland_only": True,
    "count": 1
}

# === 3. Find allies and apply fixes ===
allies = data.get("allies", [])
benched = data.get("wonderland_benched_allies", [])

# Find Red Hood in active allies and equip Grandmother's Axe
for ally in allies:
    if ally.get("_heroine_key") == "red_hood":
        ally["equipped"]["weapon"] = grandmothers_axe
        print(f"Equipped Grandmother's Axe +5 on {ally['name']} (active party)")
        break

# Find Dorothy in active allies and equip Ruby Slippers
for ally in allies:
    if ally.get("_heroine_key") == "dorothy":
        ally["equipped"]["accessory1"] = ruby_slippers
        print(f"Equipped Ruby Slippers +5 on {ally['name']} (active party)")
        break

# === 4. Handle duplicate Alice ===
# Active Alice (level 45, no Vorpal Blade) vs Benched Alice (level 43, HAS Vorpal Blade +5)
# Strategy: Move Vorpal Blade from benched Alice to active Alice, remove benched Alice duplicate
active_alice = None
benched_alice = None
benched_alice_idx = None

for ally in allies:
    if ally.get("_heroine_key") == "alice":
        active_alice = ally
        break

for i, ally in enumerate(benched):
    if ally.get("_heroine_key") == "alice":
        benched_alice = ally
        benched_alice_idx = i
        break

if active_alice and benched_alice:
    vorpal_blade = benched_alice.get("equipped", {}).get("weapon")
    if vorpal_blade:
        active_alice["equipped"]["weapon"] = vorpal_blade
        print(f"Transferred {vorpal_blade['name']} from benched Alice to active Alice")

    # Copy relevant flags from benched Alice to active Alice
    for key in ["_alice_original_innate", "_alice_vorpal_skills", "_alice_vorpal_upgraded"]:
        if key in benched_alice:
            active_alice[key] = benched_alice[key]

    # Copy skill data from benched Alice to active Alice
    for key in ["innate_skills", "learned_skills", "skill_cooldowns", "skill_mastery"]:
        if key in benched_alice:
            active_alice[key] = benched_alice[key]

    active_alice["_heroine_passive"] = "vorpal_instinct"
    active_alice["_heroine_permanent_passive"] = "vorpal_instinct"

    # Remove benched Alice duplicate
    del benched[benched_alice_idx]
    print("Removed duplicate benched Alice")

data["wonderland_benched_allies"] = benched

# === 5. Remove wonderland_only flag from quest items on permanent heroines ===
# When a heroine is permanent, their quest items lose the wonderland restriction
for ally in allies:
    if ally.get("_heroine_key") in ("alice", "dorothy") and not ally.get("_wonderland_temp", True):
        for slot in ["weapon", "armor", "accessory1", "accessory2"]:
            item = ally.get("equipped", {}).get(slot)
            if item and item.get("wonderland_only"):
                item.pop("wonderland_only", None)
                print(f"Removed wonderland_only from {ally['name']}'s {item['name']}")

# Red Hood is still temp, but her axe should still work
# (The wonderland_only flag doesn't affect functionality while in Wonderland)

# === 6. Grant missing vorpal upgrade skills ===
# These were not set because the original facility code directly assigned
# equipment without calling swap/grant functions, and the fix script didn't
# set them either.  We now patch the missing flags and learned skills.

for ally in allies:
    hk = ally.get("_heroine_key", "")

    if hk == "red_hood":
        # Ensure vorpal skill swap is recorded (it should already be)
        if not ally.get("_redhood_vorpal_skills"):
            ally["_redhood_original_innate"] = list(ally.get("innate_skills", []))
            ally["innate_skills"] = ["what_big_teeth", "fell_the_wolf"]
            ally["_redhood_vorpal_skills"] = True
            ally["skill_cooldowns"] = {}
            print(f"Swapped {ally['name']} to Grandmother's Axe skills")

        # Grant Through the Forest upgrade skill
        learned = ally.setdefault("learned_skills", [])
        if "through_the_forest" not in learned:
            learned.append("through_the_forest")
            print(f"Granted 'Through the Forest' to {ally['name']}")
        ally["_redhood_vorpal_upgraded"] = True

    elif hk == "dorothy":
        # Ensure vorpal skill swap is recorded (it should already be)
        if not ally.get("_dorothy_vorpal_skills"):
            ally["_dorothy_original_innate"] = list(ally.get("innate_skills", []))
            ally["innate_skills"] = ["cyclones_call", "heart_of_tin"]
            ally["_dorothy_vorpal_skills"] = True
            ally["skill_cooldowns"] = {}
            print(f"Swapped {ally['name']} to Ruby Slippers skills")

        # Grant Emerald City's Light upgrade skill
        learned = ally.setdefault("learned_skills", [])
        if "emerald_citys_light" not in learned:
            learned.append("emerald_citys_light")
            print(f"Granted 'Emerald City\\'s Light' to {ally['name']}")
        ally["_dorothy_vorpal_upgraded"] = True

    elif hk == "alice":
        # Ensure Alice's upgrade is consistent (already set from benched copy above)
        if ally.get("_alice_vorpal_skills") and not ally.get("_alice_vorpal_upgraded"):
            learned = ally.setdefault("learned_skills", [])
            if "frabjous_day" not in learned:
                learned.append("frabjous_day")
                print(f"Granted 'Frabjous Day' to {ally['name']}")
            ally["_alice_vorpal_upgraded"] = True

# Write back
with open('savefile/savegame_1.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("\nSavefile updated successfully!")
print("Summary:")
print("  - Grandmother's Axe +5 → Red Hood (active party)")
print("  - Ruby Slippers +5 → Dorothy (active party)")
print("  - Vorpal Blade +5 transferred from benched Alice → active Alice")
print("  - Duplicate benched Alice removed")
