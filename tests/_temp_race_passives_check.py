# tests/_temp_race_passives_check.py
# Verify the finalized race passive kits (docs/awakening_design.md Part B).
import os
import sys
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from combat.ally import get_ally_effective_attribute
from combat.ally_skills import (
    RACE_PASSIVES,
    get_race_damage_multiplier,
    get_race_damage_reduction,
    get_race_evasion,
    get_race_lifesteal,
    get_race_passive_effects,
    get_race_regen,
    has_status_immunity,
    is_heal_blocked,
    maybe_stun_on_basic,
)
from combat.status_effects import apply_bleed, apply_healing, apply_poison
from resources.enemies import ENEMY_RACES

ATTRS = ("Strength", "Constitution", "Dexterity", "Wisdom", "Learning", "Charisma")


def make_ally(race, values=None):
    values = values or {a: 10 for a in ATTRS}
    return {
        "name": "Test",
        "race": race,
        "is_ally": True,
        "attributes": dict(values),
        "equipped": {"weapon": None, "armor": None, "accessory1": None, "accessory2": None},
        "active_buffs": [],
        "active_debuffs": [],
    }


print("=== Race passive check (docs/awakening_design.md Part B) ===")

# ── 1. Every race exposes at least one effect block ──────────────────────
for race in RACE_PASSIVES:
    assert get_race_passive_effects(race), race
print(f"1. all {len(RACE_PASSIVES)} race passives expose effect blocks  [ok]")

# ── 2. Stat kits ─────────────────────────────────────────────────────────
assert get_ally_effective_attribute(make_ally("Beast"), "Strength") == 12
assert get_ally_effective_attribute(make_ally("Beast"), "Dexterity") == 13
assert get_ally_effective_attribute(make_ally("Lizardfolk"), "Strength") == 12
assert get_ally_effective_attribute(make_ally("Lizardfolk"), "Constitution") == 11
for attr in ("Strength", "Dexterity", "Wisdom"):
    assert get_ally_effective_attribute(make_ally("Abomination"), attr) == 11, attr
assert get_ally_effective_attribute(make_ally("Abomination"), "Charisma") == 10
assert get_ally_effective_attribute(make_ally("Orc"), "Strength") == 12
assert get_ally_effective_attribute(make_ally("Gnome"), "Learning") == 12
assert get_ally_effective_attribute(make_ally("Angel"), "Wisdom") == 11
assert get_ally_effective_attribute(make_ally("Angel"), "Charisma") == 11
assert get_ally_effective_attribute(make_ally("Clockwork"), "Constitution") == 12
assert get_ally_effective_attribute(make_ally("Goblin"), "Dexterity") == 12
assert get_ally_effective_attribute(make_ally("Human"), "Charisma") == 11
assert get_ally_effective_attribute(make_ally("Shadow"), "Dexterity") == 12
assert get_ally_effective_attribute(make_ally("Dragonkin"), "Strength") == 12
assert get_ally_effective_attribute(make_ally("Giant"), "Strength") == 13
assert get_ally_effective_attribute(make_ally("Vampire"), "Charisma") == 11
assert get_ally_effective_attribute(make_ally("Construct"), "Constitution") == 13
print("2. stat kits (Beast/Abomination/Giant/Angel/…)  [ok]")

# ── 3. Typed effect helpers ──────────────────────────────────────────────
assert get_race_lifesteal({"race": "Vampire"}) == 0.25
assert get_race_damage_reduction({"race": "Giant"}) == 0.1
assert get_race_damage_reduction({"race": "Abomination"}) == 0.1
assert get_race_regen({"race": "Fey"}) == 0.1
assert get_race_regen({"race": "Undead"}) == 0.05
assert get_race_evasion({"race": "Goblin"}) == 0.2
assert get_race_evasion({"race": "Shadow"}) == 0.15
assert get_race_evasion({"race": "Human"}) == 0.0
print("3. typed helpers: lifesteal / DR / regen / evasion  [ok]")

# ── 4. Dodge integration (race evasion reaches get_dodge_chance) ─────────
from combat.stats import get_dodge_chance

attacker = {"dex_mod": 10, "active_buffs": [], "active_debuffs": []}
fey = make_ally("Fey")
goblin = make_ally("Goblin")
shadow = make_ally("Shadow")
base_dodge = get_dodge_chance(fey, attacker)
assert get_dodge_chance(goblin, attacker) - base_dodge >= 0.1999
assert get_dodge_chance(shadow, attacker) - base_dodge >= 0.1499
print("4. dodge: Goblin +20% / Shadow +15% applied  [ok]")

# ── 5. Elemental profiles ────────────────────────────────────────────────
from combat.elemental import compute_ally_elemental

def elemental(key, race):
    return compute_ally_elemental({"key": key, "race": race,
                                   "equipped": {"weapon": None, "armor": None,
                                                "accessory1": None, "accessory2": None}})

_, demon_dmg = elemental("demon_whip_master", "Demon")
base = ENEMY_RACES["Demon"]["elemental_dmg"]["fire"]
assert abs(demon_dmg["fire"] - (base + 0.15)) < 1e-9, demon_dmg["fire"]
assert abs(demon_dmg["dark"] - (ENEMY_RACES["Demon"]["elemental_dmg"]["dark"] + 0.15)) < 1e-9

_, gnome_dmg = elemental("gnome_gear_maiden", "Gnome")
assert abs(gnome_dmg["thunder"] - (ENEMY_RACES["Gnome"]["elemental_dmg"]["thunder"] + 0.15)) < 1e-9

ele_res, ele_dmg = elemental("slime_girl", "Elemental")
for el in ("fire", "water", "thunder", "wind", "earth", "light", "dark", "magical"):
    assert abs(ele_dmg[el] - (ENEMY_RACES["Elemental"]["elemental_dmg"].get(el, 1.0) + 0.1)) < 1e-9, (el, ele_dmg[el])
    assert abs(ele_res[el] - (ENEMY_RACES["Elemental"]["elemental_res"].get(el, 1.0) + 0.1)) < 1e-9, (el, ele_res[el])

_, drag_dmg = elemental("kobold_tinkerer", "Dragonkin")
fire_base = ENEMY_RACES["Dragonkin"]["elemental_dmg"].get("fire", 1.0)
assert abs(drag_dmg["fire"] - (fire_base + 0.08)) < 1e-9
print("5. elemental: Demon fire/dark, Gnome thunder, Elemental all, Dragonkin all  [ok]")

# ── 6. Outgoing damage multipliers (Angel / Clockwork) ───────────────────
assert get_race_damage_multiplier({"race": "Angel"}, {"key": "demon_whip_master"}) == 1.05
assert get_race_damage_multiplier({"race": "Angel"}, {"key": "harpy_scout"}) == 1.0
shocked = {"name": "D", "key": "harpy_scout", "active_debuffs": [{"type": "shock"}]}
calm = {"name": "D", "key": "harpy_scout", "active_debuffs": []}
assert get_race_damage_multiplier({"race": "Clockwork"}, shocked) == 1.10
assert get_race_damage_multiplier({"race": "Clockwork"}, calm) == 1.0
print("6. damage mult: Angel +5% vs Demon, Clockwork +10% vs shocked  [ok]")

# ── 7. Construct poison/bleed immunity ───────────────────────────────────
construct = {"is_ally": True, "race": "Construct", "active_debuffs": [], "hp": 10}
assert apply_poison(construct, 4, 3) == "immune"
assert apply_bleed(construct, 4, 3) == "immune"
assert construct["active_debuffs"] == []
human = {"is_ally": True, "race": "Human", "active_debuffs": [], "hp": 10}
assert apply_poison(human, 4, 3) == "applied"
assert has_status_immunity(construct, "poison") is True
assert has_status_immunity(construct, "burn") is False
print("7. Construct: poison/bleed immune, others unaffected  [ok]")

# ── 8. Undead heal block (allied blocked, self allowed) ──────────────────
undead = make_ally("Undead", values={a: 10 for a in ATTRS})
undead["current_hp"] = 10
undead["max_hp"] = 100
healer = {"name": "Priest", "is_ally": True}
assert is_heal_blocked(undead, healer) is True
assert is_heal_blocked(undead, undead) is False
assert is_heal_blocked(undead, None) is False
assert apply_healing(undead, 30, source=healer) == 0
assert undead["current_hp"] == 10
assert apply_healing(undead, 30, source=undead) == 30
assert undead["current_hp"] == 40
print("8. Undead: allied heals blocked, self-heal works  [ok]")

# ── 9. Orc stun on basic attack ──────────────────────────────────────────
orc = {"race": "Orc"}
target = {"name": "Dummy", "hp": 10, "active_debuffs": []}
_orig_random = random.random
try:
    random.random = lambda: 0.05
    msg = maybe_stun_on_basic(orc, target)
finally:
    random.random = _orig_random
assert msg and "stunned" in msg.lower(), msg
assert target.get("stunned") is True
assert any(d.get("type") == "stun" for d in target["active_debuffs"])

miss_target = {"name": "Dummy2", "hp": 10, "active_debuffs": []}
try:
    random.random = lambda: 0.5
    assert maybe_stun_on_basic(orc, miss_target) is None
finally:
    random.random = _orig_random
assert maybe_stun_on_basic(orc, {"name": "Dead", "hp": 0, "active_debuffs": []}) is None
print("9. Orc: 10% stun roll on basic attack  [ok]")

print("\nAll race passive checks passed.")
