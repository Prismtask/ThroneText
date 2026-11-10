"""Diagnostic: enemy damage profiles collapse to one element.

Enemies attack with exactly one element — ``enemy_ai`` and the elemental
debuff channel both read the single highest ``elemental_dmg`` entry > 1.0, so
``compute_enemy_elemental`` now reports only that entry while resistances stay
multi-element. Also covers the Event Horizon scaling guard that used to turn
neutral 1.0 placeholders into a phantom fire element.

Run: .venv\\Scripts\\python.exe tests/_diag_enemy_elemental.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from resources.enemies import ENEMIES, ENEMY_RACES
from combat.elemental import (
    DEFAULT_ATTACK_MULTIPLIER,
    ELEMENTS,
    _get_keyword_elemental,
    compute_enemy_elemental,
    get_damage_element,
    merge_profiles,
    neutral_profile,
)
from combat.elemental_debuffs import ELEMENT_DEBUFF_MAP, get_elemental_debuff
from event_horizon import scale_enemy_elemental

failures = []


def check(label, got, expected):
    ok = got == expected
    print(f"  {'OK  ' if ok else 'FAIL'} {label}: got {got}, expected {expected}")
    if not ok:
        failures.append(label)


def raw_damage_profile(key):
    """Pre-normalization profile, rebuilt from the same three sources."""
    template = ENEMIES.get(key, {})
    race = ENEMY_RACES.get(template.get("race", "Human"), {})
    dmg = merge_profiles(neutral_profile(), race.get("elemental_dmg", {}))
    kw_dmg, _ = _get_keyword_elemental(template.get("name", ""))
    dmg = merge_profiles(dmg, kw_dmg)
    return merge_profiles(dmg, template.get("elemental_dmg", {}))


print("=== Every enemy reports at most one damage element ===")
multi, preserved, neutral, fallback_bad, raw_neutral = [], [], 0, [], 0
for key in ENEMIES:
    _, dmg = compute_enemy_elemental({"key": key})
    over = {el: v for el, v in dmg.items() if v > 1.0}
    if len(over) > 1:
        multi.append((key, over))
    if not over:
        neutral += 1
    raw = raw_damage_profile(key)
    raw_el = get_damage_element(raw)
    if raw_el is None:
        # Neutral profiles (the Human race) must use the PHY/MAG fallback.
        raw_neutral += 1
        if dmg not in ({"physical": DEFAULT_ATTACK_MULTIPLIER},
                       {"magical": DEFAULT_ATTACK_MULTIPLIER}):
            fallback_bad.append((key, dmg))
        continue
    expect = {raw_el: round(raw[raw_el], 4)}
    if dmg != expect:
        preserved.append((key, dmg, expect))

check("no enemy has >1 damage element", multi[:5], [])
check("normalization keeps the old max element", preserved[:5], [])
check("neutral profiles receive the PHY/MAG fallback", fallback_bad[:5], [])
print(f"  neutral profiles: {raw_neutral}/{len(ENEMIES)} "
      f"(all fallback); still neutral: {neutral}")
check("no enemy reports an empty damage profile", neutral, 0)

print("=== Spot checks ===")
check(
    "beast_thunder_bird -> thunder",
    compute_enemy_elemental({"key": "beast_thunder_bird"})[1],
    {"thunder": 1.4},
)
check(
    "fey tie resolves to light (ELEMENTS order)",
    compute_enemy_elemental({"key": "fey_sprite"})[1],
    {"light": 1.3},
)
check(
    "elite_assassin -> physical fallback",
    compute_enemy_elemental({"key": "elite_assassin"})[1],
    {"physical": DEFAULT_ATTACK_MULTIPLIER},
)
check(
    "novice_mage -> magical keyword",
    compute_enemy_elemental({"key": "novice_mage"})[1],
    {"magical": 1.4},
)
check(
    "cultist -> magical fallback",
    compute_enemy_elemental({"key": "cultist"})[1],
    {"magical": DEFAULT_ATTACK_MULTIPLIER},
)

print("=== Resistances stay multi-element ===")
multi_res = sum(
    1
    for k in ENEMIES
    if sum(1 for v in compute_enemy_elemental({"key": k})[0].values() if v != 1.0) >= 2
)
print(f"  enemies with >=2 non-neutral resistances: {multi_res}/{len(ENEMIES)}")
if multi_res < 100:
    failures.append("multi-element resistances look collapsed")
check("resistances are not collapsed", multi_res >= 100, True)

print("=== AI and debuff channel agree ===")
mismatch = []
for key in ENEMIES:
    _, dmg = compute_enemy_elemental({"key": key})
    picked = get_damage_element(dmg)
    if picked is None:
        continue
    if get_elemental_debuff({"elemental_dmg": dmg}) != ELEMENT_DEBUFF_MAP.get(picked):
        mismatch.append((key, picked))
check("debuff channel matches attack element", mismatch[:5], [])

print("=== Event Horizon scaling keeps neutrality ===")
neutral_enemy = {"elemental_dmg": {el: 1.0 for el in ELEMENTS}}
scale_enemy_elemental(neutral_enemy, 1.25)
check("neutral stays neutral", get_damage_element(neutral_enemy["elemental_dmg"]), None)
check("neutral entries untouched", neutral_enemy["elemental_dmg"]["fire"], 1.0)

fire_enemy = {"elemental_dmg": {"fire": 1.4}}
scale_enemy_elemental(fire_enemy, 1.25)
check("fire scaled", round(fire_enemy["elemental_dmg"]["fire"], 4), 1.75)
check("no phantom elements added", sorted(fire_enemy["elemental_dmg"]), ["fire"])

noop = {"elemental_dmg": {"thunder": 1.3}}
scale_enemy_elemental(noop, 1.0)
check("factor 1.0 is a no-op", noop["elemental_dmg"], {"thunder": 1.3})

print()
if failures:
    print("FAILED:", ", ".join(failures))
    sys.exit(1)
print("enemy elemental normalization OK")
