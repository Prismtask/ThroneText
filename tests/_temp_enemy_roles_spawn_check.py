"""Check (2026-11-03): enemy attacker/supporter roles + role-weighted spawns.

Run: .venv\\Scripts\\python.exe tests\\_temp_enemy_roles_spawn_check.py
"""
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import combat.enemy_skills as es
from combat.stats import enemy_stats
from resources.enemies import ENEMIES
import dungeon

failures = []


def check(label, ok, detail=""):
    print(f"  {'OK  ' if ok else 'FAIL'} {label}{(' — ' + detail) if detail else ''}")
    if not ok:
        failures.append(label)


def role_of(key):
    return es.get_enemy_role(ENEMIES[key])


def count_supporters(keys):
    return sum(1 for k in keys if role_of(k) == es.ROLE_SUPPORTER)


print("=== Role inference ===")
check("Goblin Shaman is a supporter", role_of("goblin_shaman") == es.ROLE_SUPPORTER)
check("Goblin Knifer is an attacker", role_of("goblin_knifer") == es.ROLE_ATTACKER)
check("Light Warden is a supporter (Angel race)",
      role_of("angel_lightwarden") == es.ROLE_SUPPORTER)
check("Name keyword infers supporter",
      es.get_enemy_role({"name": "Swamp Witch", "race": "Lizardfolk"}) == es.ROLE_SUPPORTER)
check("Explicit role overrides the name",
      es.get_enemy_role({"name": "High Priest", "race": "Human",
                         "role": "attacker"}) == es.ROLE_ATTACKER)
check("Explicit damage abilities make an attacker",
      es.get_enemy_role({"name": "Cultist", "race": "Human",
                         "abilities": [{"type": "skill", "name": "Dark Bolt"}]})
      == es.ROLE_ATTACKER)
check("Explicit heal abilities make a supporter",
      es.get_enemy_role({"name": "Bandit", "race": "Human",
                         "abilities": [{"type": "heal", "name": "Field Dressing"}]})
      == es.ROLE_SUPPORTER)

shaman = enemy_stats("goblin_shaman")
es.get_enemy_kit(shaman)
knifer = enemy_stats("goblin_knifer")
es.get_enemy_kit(knifer)
check("Runtime role matches kit role",
      shaman["role"] == es.ROLE_SUPPORTER and knifer["role"] == es.ROLE_ATTACKER,
      f"shaman={shaman['role']} knifer={knifer['role']}")

print("=== Supporter action weighting ===")
# Patient attacker with an explicit heal ability must not heal.
attacker_heal = {
    "name": "Selfish Duelist", "race": "Human", "level": 20,
    "role": "attacker", "hp": 20, "max_hp": 20,
    "abilities": [
        {"type": "heal", "name": "Second Wind", "heal_pct": 0.3,
         "cooldown": 2, "min_level": 1},
    ],
}
# get_enemy_kit caches the role; keep it explicit.
es.get_enemy_kit(attacker_heal)
choice = es.choose_enemy_action(attacker_heal, attacker_heal["_enemy_ai_kit"],
                                [attacker_heal], [])
check("Attacker with a heal ability ignores healing", choice is None,
      f"kind={choice[0] if choice else None}")

# A supporter uses the same heal ability.
supporter_heal = dict(attacker_heal)
supporter_heal["role"] = "supporter"
supporter_heal["name"] = "Field Medic"
supporter_heal.pop("_enemy_ai_kit", None)
supporter_heal.pop("_enemy_ai_kit_resolved", None)
es.get_enemy_kit(supporter_heal)
supporter_heal["hp"] = 4
choice = es.choose_enemy_action(supporter_heal, supporter_heal["_enemy_ai_kit"],
                                [supporter_heal], [])
check("Supporter uses its heal ability",
      choice and choice[0] == "heal", f"kind={choice[0] if choice else None}")

print("=== Role-filtered pools ===")
random.seed(7)
supporters = [es.get_enemy_role(ENEMIES[key])
              for key in (dungeon.get_random_enemy_key(
                  25, role=es.ROLE_SUPPORTER) for _ in range(60))]
check("Supporter pool only returns supporters",
      supporters and all(r == es.ROLE_SUPPORTER for r in supporters),
      f"roles={set(supporters)}")

attackers = [es.get_enemy_role(ENEMIES[key])
             for key in (dungeon.get_random_enemy_key(
                 25, role=es.ROLE_ATTACKER) for _ in range(60))]
check("Attacker pool only returns attackers",
      attackers and all(r == es.ROLE_ATTACKER for r in attackers),
      f"roles={set(attackers)}")

print("=== Group composition ===")
from dungeon import build_enemy_group

random.seed(11)
low_counts = [count_supporters(build_enemy_group(2, 4)) for _ in range(400)]
random.seed(12)
high_counts = [count_supporters(build_enemy_group(45, 4)) for _ in range(400)]
check("No group exceeds two supporters", max(low_counts + high_counts) <= 2,
      f"max={max(low_counts + high_counts)}")
check("Every group keeps at least one attacker",
      all(c < 4 for c in low_counts + high_counts))
check("High-level rooms field more support than low-level rooms",
      sum(high_counts) > sum(low_counts),
      f"low={sum(low_counts)} high={sum(high_counts)}")

random.seed(13)
single_groups = [build_enemy_group(30, 1) for _ in range(50)]
check("Lone-enemy groups stay size 1",
      all(len(g) == 1 for g in single_groups))

random.seed(14)
floor_rooms = []
for _ in range(20):
    for room in dungeon.generate_floor(30):
        if room.get("type") == "combat" and not room.get("is_boss"):
            floor_rooms.append(room["enemies"])
check("Generated normal rooms always include an attacker",
      all(count_supporters(room) < len(room) for room in floor_rooms),
      f"rooms={len(floor_rooms)}")
check("Generated normal rooms never exceed two supporters",
      all(count_supporters(room) <= 2 for room in floor_rooms))


print()
if failures:
    print(f"FAILED ({len(failures)}): {failures}")
    sys.exit(1)
print("OK — enemy roles, role-filtered pools and spawn composition verified")
