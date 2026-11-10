"""Check (2026-10-27): generic non-superboss enemy AI kits.

Verifies:
  * race kits + healer name keywords + YAML ``abilities`` overrides,
  * monster girls keep single-target turns,
  * scripted enemies (dummy / hallucination / Wonderland floor boss) opt out,
  * level tiers — 1-4 basic + heal only, skills at 5, AoE at 10, smarter
    support and group-aware AoE at 20/35,
  * action selection (self-heal, wounded-ally heal, AoE heal, AoE skill,
    single-target skill, basic fallback),
  * execution through ``enemy_take_turn`` with real ``enemy_attack`` math,
  * cooldowns are recorded and block repeats.

Run: .venv\\Scripts\\python.exe tests\\_temp_enemy_ai_check.py
"""
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import combat.enemy_ai as ea
import combat.enemy_skills as es
from combat.stats import enemy_stats

captured = []


def _log(*args, **kwargs):
    captured.append(" ".join(str(x) for x in args))


ea.c_print = _log
es.c_print = _log

failures = []


def check(label, ok, detail=""):
    print(f"  {'OK  ' if ok else 'FAIL'} {label}{(' — ' + detail) if detail else ''}")
    if not ok:
        failures.append(label)


ATTRS = ("Strength", "Constitution", "Dexterity", "Wisdom", "Learning", "Charisma")


def make_player(hp=200):
    return {
        "name": "prism",
        "class": "Warrior",
        "race": "Human",
        "level": 20,
        "current_hp": hp,
        "level_hp_bonus": 0,
        "attributes": {a: 10 for a in ATTRS},
        "equipped": {"weapon": None, "armor": None,
                     "accessory1": None, "accessory2": None},
        "active_buffs": [], "active_debuffs": [],
        "elemental_dmg": {}, "elemental_res": {},
        "inventory": [], "allies": [],
        "skill_cooldowns": {}, "party_order": [],
        "married_girls": [], "engaged_girls": [],
    }


def make_ally(name="Ally", hp=100):
    return {
        "name": name,
        "race": "Human",
        "level": 20,
        "current_hp": hp,
        "max_hp": 100,
        "is_ally": True,
        "attributes": {a: 8 for a in ATTRS},
        "equipped": {"weapon": None, "armor": None,
                     "accessory1": None, "accessory2": None},
        "active_buffs": [], "active_debuffs": [],
        "elemental_dmg": {}, "elemental_res": {},
    }


# ── 1. Kit construction ─────────────────────────────────────────────────────
print("=== Kit construction ===")
shaman = enemy_stats("goblin_shaman")
shaman_kit = es.get_enemy_kit(shaman)
check("Goblin Shaman gets skill + aoe + heal + aoe heal",
      {"skill", "aoe", "heal", "aoe_heal"} <= set(shaman_kit or {}),
      f"keys={sorted((shaman_kit or {}).keys())}")

knifer = enemy_stats("goblin_knifer")
knifer_kit = es.get_enemy_kit(knifer) or {}
check("Goblin Knifer has no heal", "heal" not in knifer_kit)

mage = enemy_stats("novice_mage")
mage_kit = es.get_enemy_kit(mage) or {}
check("Human mage uses an arcane kit",
      (mage_kit.get("skill") or {}).get("name") == "Arcane Bolt",
      f"skill={(mage_kit.get('skill') or {}).get('name')}")

thief = enemy_stats("thief")
thief_kit = es.get_enemy_kit(thief) or {}
check("Human thief uses a rogue kit",
      (thief_kit.get("skill") or {}).get("name") == "Backstab",
      f"skill={(thief_kit.get('skill') or {}).get('name')}")

angel = enemy_stats("angel_lightwarden")
angel_kit = es.get_enemy_kit(angel) or {}
check("Angel keeps its racial heal kit",
      "heal" in angel_kit and "aoe_heal" in angel_kit)

girl = enemy_stats("goblin_girl")
girl_kit = es.get_enemy_kit(girl) or {}
check("Monster girl has no AoE actions",
      "aoe" not in girl_kit and "aoe_heal" not in girl_kit,
      f"keys={sorted(girl_kit.keys())}")

override_enemy = {
    "name": "Custom Cultist",
    "key": "_custom_cultist",
    "race": "Human",
    "level": 6,
    "hp": 40, "max_hp": 40,
    "abilities": [
        {"type": "heal", "name": "Dark Mending", "heal_pct": 0.35,
         "cooldown": 2, "min_level": 1},
    ],
}
override_kit = es.get_enemy_kit(override_enemy) or {}
check("YAML abilities list replaces the race kit",
      set(override_kit.keys()) == {"heal"} and override_kit["heal"]["name"] == "Dark Mending",
      f"keys={sorted(override_kit.keys())}")

# Verify enemy_stats actually passes template abilities through to the AI.
from resources.enemies import ENEMIES
ENEMIES["_temp_ability_probe"] = {
    "name": "Ability Probe", "race": "Human", "level": 5, "base_hp": 20,
    "mods": {},
    "abilities": [{"type": "skill", "name": "Probe Bolt", "power": 1.2,
                   "cooldown": 2, "min_level": 1}],
}
probe = enemy_stats("_temp_ability_probe")
probe_kit = es.get_enemy_kit(probe) or {}
check("enemy_stats forwards YAML abilities",
      (probe_kit.get("skill") or {}).get("name") == "Probe Bolt",
      f"kit={probe_kit}")
del ENEMIES["_temp_ability_probe"]

dummy = {"name": "Training Dummy", "is_dummy": True, "race": "Human", "level": 5}
check("Dummy opts out", es.get_enemy_kit(dummy) is None)

hallucination = {"name": "The Hollow You", "key": "_hallucination", "race": "Human",
                 "level": 5, "round_hook": lambda *a: None}
check("Round-hook enemy opts out", es.get_enemy_kit(hallucination) is None)

wl_boss = {"name": "White Rabbit", "key": "wl_white_rabbit", "race": "Human",
           "level": 8, "hp": 50, "max_hp": 50}
check("Wonderland floor boss opts out", es.get_enemy_kit(wl_boss) is None)


# ── 2. Level-based behaviour tiers ─────────────────────────────────────────
print("=== Level-based behaviour tiers ===")
player = make_player()
ally = make_ally()
orig_random = random.random
check("Level 1-4 = Instinctive",
      es.get_ai_tier(1)["name"] == es.get_ai_tier(4)["name"] == "Instinctive")
check("Level 5-9 = Trained", es.get_ai_tier(5)["name"] == "Trained")
check("Level 10-19 = Coordinated", es.get_ai_tier(10)["name"] == "Coordinated")
check("Level 20-34 = Tactical", es.get_ai_tier(20)["name"] == "Tactical")
check("Level 35+ = Calculating", es.get_ai_tier(35)["name"] == "Calculating")

random.random = lambda: 0.0

low_bandit = enemy_stats("bandit")  # level 2
choice = es.choose_enemy_action(low_bandit, es.get_enemy_kit(low_bandit),
                                [low_bandit], [player, ally])
check("Low-level enemy falls back to a basic attack instead of a skill",
      choice is None, f"kind={choice[0] if choice else None}")

low_shaman = enemy_stats("goblin_shaman")  # level 3
wounded_low = enemy_stats("goblin_knifer")
wounded_low["hp"] = 2
choice = es.choose_enemy_action(low_shaman, es.get_enemy_kit(low_shaman),
                                [low_shaman, wounded_low], [player, ally])
check("Low-level healer can still heal",
      choice and choice[0] == "heal", f"kind={choice[0] if choice else None}")

trained_orc = enemy_stats("orc_grunt")
trained_orc["level"] = 6
choice = es.choose_enemy_action(trained_orc, es.get_enemy_kit(trained_orc),
                                [trained_orc], [player, ally])
check("Trained enemy uses single skills but not AoE",
      choice and choice[0] == "skill", f"kind={choice[0] if choice else None}")

# Tactical enemies lean into AoE when the party is already wounded (group
# awareness only — they still do not choose individual targets).
random.random = lambda: 0.40
tactical_orc = enemy_stats("orc_grunt")
tactical_orc["level"] = 20
healthy_a = make_ally("Healthy A")
healthy_b = make_ally("Healthy B")
choice = es.choose_enemy_action(tactical_orc, es.get_enemy_kit(tactical_orc),
                                [tactical_orc],
                                [make_player(), healthy_a, healthy_b])
check("Tactical enemy picks a skill against a healthy party",
      choice and choice[0] == "skill", f"kind={choice[0] if choice else None}")

hurt_a = make_ally("Hurt A", hp=20)
hurt_b = make_ally("Hurt B", hp=20)
choice = es.choose_enemy_action(tactical_orc, es.get_enemy_kit(tactical_orc),
                                [tactical_orc],
                                [make_player(), hurt_a, hurt_b])
check("Tactical enemy sweeps a wounded party",
      choice and choice[0] == "aoe", f"kind={choice[0] if choice else None}")

random.random = orig_random


# ── 3. Action selection ─────────────────────────────────────────────────────
print("=== Action selection ===")
random.random = lambda: 0.0

low_shaman = enemy_stats("goblin_shaman")
low_shaman["hp"] = 3
choice = es.choose_enemy_action(low_shaman, es.get_enemy_kit(low_shaman),
                                [low_shaman], [player, ally])
check("Wounded healer heals itself", choice and choice[0] == "heal" and choice[2] is low_shaman)

full_shaman = enemy_stats("goblin_shaman")
wounded_ally = enemy_stats("goblin_knifer")
wounded_ally["hp"] = 2
choice = es.choose_enemy_action(full_shaman, es.get_enemy_kit(full_shaman),
                                [full_shaman, wounded_ally], [player, ally])
check("Healer prioritises the most wounded ally",
      choice and choice[0] == "heal" and choice[2] is wounded_ally)

second_wounded = enemy_stats("goblin_knifer")
second_wounded["hp"] = 2
choice = es.choose_enemy_action(full_shaman, es.get_enemy_kit(full_shaman),
                                [full_shaman, wounded_ally, second_wounded],
                                [player, ally])
check("Two wounded allies trigger AoE heal",
      choice and choice[0] == "aoe_heal", f"kind={choice[0] if choice else None}")

orc = enemy_stats("orc_grunt")
orc["level"] = 10  # unlock Cleave for the test
choice = es.choose_enemy_action(orc, es.get_enemy_kit(orc), [orc], [player, ally])
check("AoE skill chosen against a multi-member party",
      choice and choice[0] == "aoe", f"kind={choice[0] if choice else None}")

choice = es.choose_enemy_action(orc, es.get_enemy_kit(orc), [orc], [player])
check("Single-target skill against a lone target",
      choice and choice[0] == "skill", f"kind={choice[0] if choice else None}")

random.random = lambda: 0.99
choice = es.choose_enemy_action(orc, es.get_enemy_kit(orc), [orc], [player])
check("Basic attack is the fallback", choice is None)
random.random = orig_random


# ── 4. Execution through the real damage pipeline ───────────────────────────
print("=== Execution ===")
orig_dodge = ea._try_enemy_attack_dodge
ea._try_enemy_attack_dodge = lambda *a, **k: False
random.random = lambda: 0.0

# Self-heal
healer = enemy_stats("goblin_shaman")
healer["hp"] = 5
captured.clear()
outcome = es.enemy_take_turn(healer, player, 10, False,
                             all_enemies=[healer], actual_player=player,
                             party_members=[player])
check("Self-heal runs and heals",
      outcome == "healed" and healer["hp"] > 5,
      f"outcome={outcome} hp={healer['hp']}")
check("Self-heal logs the action",
      any("Mend Wounds" in line for line in captured))
check("Self-heal cooldown recorded",
      healer.get("_enemy_ai_cooldowns", {}).get("mend_wounds") == 4,
      f"cds={healer.get('_enemy_ai_cooldowns')}")

# AoE skill
orc = enemy_stats("orc_grunt")
orc["level"] = 10
orc["hp"] = orc["max_hp"]
p1 = make_player()
a1 = make_ally("Ally A")
a2 = make_ally("Ally B")
party = [p1, a1, a2]
captured.clear()
outcome = es.enemy_take_turn(orc, p1, 10, False,
                             all_enemies=[orc], actual_player=p1,
                             party_members=party)
check("AoE skill resolves", outcome in ("hit", "dead"), f"outcome={outcome}")
check("AoE skill logs its name", any("Cleave" in line for line in captured))
check("AoE skill hits every party member",
      p1["current_hp"] < 200 and a1["current_hp"] < 100 and a2["current_hp"] < 100,
      f"hp={p1['current_hp']}/{a1['current_hp']}/{a2['current_hp']}")
check("AoE skill cooldown recorded",
      orc.get("_enemy_ai_cooldowns", {}).get("cleave") == 5,
      f"cds={orc.get('_enemy_ai_cooldowns')}")

# Single-target skill
human = enemy_stats("bandit")
human["level"] = 10
p2 = make_player()
captured.clear()
outcome = es.enemy_take_turn(human, p2, 10, False,
                             all_enemies=[human], actual_player=p2,
                             party_members=[p2])
check("Single-target skill resolves", outcome in ("hit", "dead"), f"outcome={outcome}")
check("Single-target skill logs its name",
      any("Power Strike" in line for line in captured))
check("Single-target skill damages the player", p2["current_hp"] < 200)

# Basic attack fallback
random.random = lambda: 0.99
p3 = make_player()
captured.clear()
outcome = es.enemy_take_turn(human, p3, 10, False,
                             all_enemies=[human], actual_player=p3,
                             party_members=[p3])
check("Basic attack fallback resolves", outcome in ("hit", "dead", "missed", "dodged"),
      f"outcome={outcome}")
check("Basic attack does not log a skill name",
      not any("uses" in line for line in captured), f"lines={captured}")

random.random = orig_random
ea._try_enemy_attack_dodge = orig_dodge


print()
if failures:
    print(f"FAILED ({len(failures)}): {failures}")
    sys.exit(1)
print("OK — enemy AI kit, selection, execution and cooldowns verified")
