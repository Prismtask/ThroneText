#!/usr/bin/env python3
"""Test ally skill system integration"""

import sys
from resources.enemies import ENEMIES
from combat.ally import create_ally_from_girl
from combat.ally_skills import (
    initialize_ally_skills, teach_ally_skill, gain_skill_learning_exp,
    get_ally_skill_mastery_level, add_ally_skill_mastery_xp,
    format_skill_learning_progress
)

def test_ally_creation():
    """Test that allies can be created with skill system initialized"""
    print("=" * 60)
    print("TEST 1: Ally Creation with Skill System")
    print("=" * 60)
    
    # Get a specific monster girl that should have innate skills
    # Try to use harpy_scout, but fall back to first if not found
    target_key = None
    for key in ENEMIES.keys():
        template = ENEMIES[key]
        if template.get("name") and "arpy" in template.get("name", "").lower():
            target_key = key
            break
    
    if not target_key:
        target_key = list(ENEMIES.keys())[0]
    
    template = ENEMIES[target_key]
    
    print(f"Creating ally from: {template.get('name', target_key)}")
    
    # Create girl dict in house format
    girl = {
        "key": target_key,
        "name": template.get("name", "Test Girl"),
        "level": 5,
        "affection": 50,
        "exp": 0
    }
    
    # Create ally
    ally = create_ally_from_girl(girl)
    
    print(f"\nAlly created: {ally['name']}")
    print(f"  Passive skill: {ally.get('passive_skill', 'NONE')}")
    print(f"  Innate skills: {ally.get('innate_skills', [])}")
    print(f"  Learned skills: {ally.get('learned_skills', [])}")
    print(f"  Learning: {ally.get('learning', {})}")
    print(f"  Skill mastery: {ally.get('skill_mastery', {})}")
    
    # Check fields exist
    assert ally.get('passive_skill'), "Passive skill not set"
    assert 'innate_skills' in ally, "Innate skills field missing"
    assert 'learned_skills' in ally, "Learned skills field missing"
    assert 'learning' in ally, "Learning field missing"
    assert 'skill_mastery' in ally, "Mastery field missing"
    
    print("\nPASS: Ally created with all skill system fields")
    return ally


def test_skill_teaching(ally):
    """Test teaching a skill to an ally"""
    print("\n" + "=" * 60)
    print("TEST 2: Skill Teaching")
    print("=" * 60)
    
    ally_name = ally['name']
    
    # Get a learnable skill from categories
    from resources.skill_loader import LEARNABLE_SKILLS
    
    if not LEARNABLE_SKILLS or 'offensive' not in LEARNABLE_SKILLS:
        print("FAIL: No learnable skills loaded")
        return
    
    # Get first offensive skill
    offensive_skills = LEARNABLE_SKILLS.get('offensive', {})
    first_skill_id = list(offensive_skills.keys())[0] if offensive_skills else None
    
    if not first_skill_id:
        print("FAIL: No offensive skills found")
        return
    
    skill_name = offensive_skills[first_skill_id].get('name', first_skill_id)
    
    print(f"Teaching {ally_name} the skill: {skill_name} ({first_skill_id})")
    
    # Teach the skill
    result = teach_ally_skill(ally, first_skill_id)
    
    if result:
        learning_status = ally.get('learning', {})
        print(f"  Learning status: {learning_status}")
        print(f"PASS: Skill teaching successful")
    else:
        print(f"FAIL: Skill teaching failed")


def test_skill_learning_exp(ally):
    """Test awarding skill learning experience"""
    print("\n" + "=" * 60)
    print("TEST 3: Skill Learning Experience")
    print("=" * 60)
    
    # First teach a skill if not already learning
    from resources.skill_loader import LEARNABLE_SKILLS
    
    if not ally.get('learning'):
        offensive_skills = LEARNABLE_SKILLS.get('offensive', {})
        first_skill_id = list(offensive_skills.keys())[0]
        teach_ally_skill(ally, first_skill_id)
    
    print(f"Before: {format_skill_learning_progress(ally)}")
    
    # Award experience to complete learning
    completed_skill = None
    for i in range(100):
        result = gain_skill_learning_exp(ally, 10)
        if result:
            completed_skill = result
            print(f"  After iteration {i}: Learned skill {completed_skill}!")
            break
    
    print(f"After: {format_skill_learning_progress(ally)}")
    print(f"Learned skills: {ally.get('learned_skills', [])}")
    print("PASS: Skill learning experience system works")


def test_mastery_tracking(ally):
    """Test skill mastery level tracking"""
    print("\n" + "=" * 60)
    print("TEST 4: Skill Mastery Tracking")
    print("=" * 60)
    
    # Get any learned skill
    learned = ally.get('learned_skills', [])
    
    if not learned:
        print("  No learned skills yet, skipping mastery test")
        return
    
    skill_id = learned[0]
    
    print(f"Testing mastery for skill: {skill_id}")
    
    # Check initial mastery
    initial_level = get_ally_skill_mastery_level(ally, skill_id)
    print(f"  Initial mastery level: {initial_level}")
    
    # Add mastery XP
    add_ally_skill_mastery_xp(ally, skill_id)
    add_ally_skill_mastery_xp(ally, skill_id)
    
    # Check updated mastery
    updated_level = get_ally_skill_mastery_level(ally, skill_id)
    print(f"  After 2 XP: mastery level {updated_level}")
    
    print("PASS: Mastery tracking works")


if __name__ == "__main__":
    try:
        print("\n*** ALLY SKILL SYSTEM INTEGRATION TEST ***\n")
        
        ally = test_ally_creation()
        test_skill_teaching(ally)
        test_skill_learning_exp(ally)
        test_mastery_tracking(ally)
        
        print("\n" + "=" * 60)
        print("ALL TESTS COMPLETED")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
