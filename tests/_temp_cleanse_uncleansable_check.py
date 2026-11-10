# tests/_temp_cleanse_uncleansable_check.py
# Verify every party-side cleanse path skips uncleansable wounds (Vorpal Wound).
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

WOUND = {"type": "bleed", "damage": 10, "remaining": 4, "source": "vorpal_wound", "_uncleansable": True}
POISON = {"type": "poison", "damage": 3, "remaining": 2}

# ── 1. Palette Alabaster self-cleanse (brush passive) ────────────────────────
from combat.weapon.palette_brush import tick_palette_brush_passives
actor = {
    "name": "Palette", "_heroine_key": "palette", "brush_stance": "light",
    "equipped": {"weapon": {"id": "palette_brush"}},
    "active_debuffs": [dict(POISON), dict(WOUND)],
}
msgs = tick_palette_brush_passives(actor)
assert len(actor["active_debuffs"]) == 1, actor["active_debuffs"]
assert actor["active_debuffs"][0]["_uncleansable"] is True

# ── 2. Ally skill cleanse paths (cleanse_all_debuffs / cleanse_one_debuff) ───
from combat.ally_skills import execute_ally_skill


def make_ally(debuffs):
    return {
        "name": "Vesper", "is_ally": True, "race": "Human", "level": 15,
        "current_hp": 100, "max_hp": 150,
        "attributes": {"Strength": 10, "Constitution": 10, "Dexterity": 10,
                       "Wisdom": 20, "Learning": 10, "Charisma": 10},
        "equipped": {"weapon": None, "armor": None, "accessory1": None, "accessory2": None},
        "active_buffs": [], "active_debuffs": debuffs,
        "elemental_dmg": {}, "elemental_res": {},
        "skill_cooldowns": {}, "skill_mastery": {}, "inventory": [],
    }


player = {
    "name": "You", "is_ally": False, "level": 15, "current_hp": 100,
    "attributes": {"Strength": 10, "Constitution": 10, "Dexterity": 10,
                   "Wisdom": 10, "Learning": 10, "Charisma": 10},
    "equipped": {"weapon": None, "armor": None, "accessory1": None, "accessory2": None},
    "active_buffs": [], "active_debuffs": [], "elemental_dmg": {}, "elemental_res": {},
}

# cleanse_all: wound survives, poison is removed, message flags the resistance
ally = make_ally([dict(POISON), dict(WOUND)])
skill_all = {"name": "Mending Circle", "target": "all_allies", "power_type": "wis",
             "base_power": 0, "heal_percent": 0.10, "cleanse_all_debuffs": True, "cooldown": 1}
msg, victory = execute_ally_skill(ally, player, "mending_circle", skill_all, [], [ally])
assert len(ally["active_debuffs"]) == 1 and ally["active_debuffs"][0].get("_uncleansable"), (msg, ally["active_debuffs"])
assert "resist" in msg, msg

# cleanse_one: only the cleansable entry is consumed, wound survives
ally = make_ally([dict(WOUND), dict(POISON)])
skill_one = {"name": "Heart's Ease", "target": "all_allies", "power_type": "wis",
             "base_power": 0, "heal_percent": 0.10, "cleanse_one_debuff": True, "cooldown": 1}
msg, victory = execute_ally_skill(ally, player, "hearts_ease", skill_one, [], [ally])
assert len(ally["active_debuffs"]) == 1 and ally["active_debuffs"][0].get("_uncleansable"), (msg, ally["active_debuffs"])

print("UNCLEANSABLE CLEANSE CHECKS PASSED")
