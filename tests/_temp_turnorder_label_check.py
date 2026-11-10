# Temp check (2026-10-08): roll_initiative labels the MC by name, not "You".
import sys
sys.path.insert(0, "c:/Code/Pandemonium")

from combat.combat_engine import roll_initiative

ATTRS = ("Strength", "Constitution", "Dexterity", "Wisdom", "Learning", "Charisma")
player = {
    "name": "Prism", "class": "Warrior", "race": "Human", "level": 15,
    "current_hp": 45, "passive_unlocked": True,
    "attributes": {a: 10 for a in ATTRS},
    "level_hp_bonus": 0,
    "equipped": {"weapon": None, "armor": None, "accessory1": None, "accessory2": None},
    "active_buffs": [], "active_debuffs": [],
    "elemental_dmg": {}, "elemental_res": {},
    "inventory": [], "allies": [],
    "skills": [], "skill_mastery": {}, "skill_cooldowns": {},
    "party_order": [],
}
enemies = [
    {"name": "Goblin", "hp": 10, "max_hp": 10, "dex_mod": 5,
     "active_buffs": [], "active_debuffs": [], "key": "goblin"},
]
order = roll_initiative(player, enemies)
p_entry = next(c for c in order if c["type"] == "player")
print("player label:", repr(p_entry["label"]))
assert p_entry["label"] == "Prism", p_entry["label"]

# Falls back to "You" only when a name is genuinely missing.
player.pop("name")
order = roll_initiative(player, enemies)
p_entry = next(c for c in order if c["type"] == "player")
assert p_entry["label"] == "You", p_entry["label"]
print("OK — turn-order label uses the MC name (fallback 'You' when missing)")
