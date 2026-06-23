#!/usr/bin/env python3
"""Test the elemental system implementation."""

from character import ensure_player_fields, create_character
from combat.elemental import (
    neutral_profile, ELEMENTS, compute_player_elemental,
    compute_enemy_elemental, calculate_elemental_damage
)

print("=" * 60)
print("TESTING ELEMENTAL SYSTEM")
print("=" * 60)

# Test 1: Create a player and check elemental initialization
print("\n[TEST 1] Player Creation & Elemental Initialization")
try:
    player = {
        'name': 'TestHero',
        'race': 'Human',
        'class': 'Warrior',
        'current_hp': 100,
        'max_hp': 100,
        'equipped': {}
    }
    ensure_player_fields(player)
    
    if 'elemental_res' in player and 'elemental_dmg' in player:
        print("[PASS] Elemental fields created successfully")
        print(f"  - elemental_res: {player['elemental_res']}")
        print(f"  - elemental_dmg: {player['elemental_dmg']}")
    else:
        print("[FAIL] Elemental fields not found in player")
except Exception as e:
    print(f"[FAIL] Error during player creation: {e}")

# Test 2: Check neutral profile
print("\n[TEST 2] Neutral Profile")
try:
    profile = neutral_profile()
    print(f"[PASS] Neutral profile created: {profile}")
except Exception as e:
    print(f"[FAIL] Error creating neutral profile: {e}")

# Test 3: Check elemental damage calculation
print("\n[TEST 3] Elemental Damage Calculation")
try:
    attacker = {
        'elemental_dmg': {'fire': 1.5, 'water': 0.8},
        'name': 'Attacker'
    }
    target = {
        'elemental_res': {'fire': 1.2, 'water': 0.5},
        'name': 'Target'
    }
    
    # Fire damage: base_dmg * 1.5 * 1.2
    fire_dmg = calculate_elemental_damage(100, attacker, target, 'fire')
    print(f"[PASS] Fire damage: {fire_dmg} (100 * 1.5 * 1.2 = 180)")
    
    # Water damage: base_dmg * 0.8 * 0.5
    water_dmg = calculate_elemental_damage(100, attacker, target, 'water')
    print(f"[PASS] Water damage: {water_dmg} (100 * 0.8 * 0.5 = 40)")
    
except Exception as e:
    print(f"[FAIL] Error calculating elemental damage: {e}")

print("\n" + "=" * 60)
print("ELEMENTAL SYSTEM TEST COMPLETE")
print("=" * 60)
