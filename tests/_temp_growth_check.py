# tests/_temp_growth_check.py
# Verify the late-bloomer growth system + parity tweak (docs/awakening_design.md Part A).
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from combat.ally import (
    ALLY_LEVEL_STAT_BONUS,
    GROWTH_TARGET_SUM,
    _ally_to_house_record,
    apply_ally_growth,
    compute_girl_attributes,
    create_ally_from_girl,
    get_growth_label,
    get_growth_rate,
)
from resources.enemies import ENEMIES

print("=== Growth system check (docs/awakening_design.md Part A) ===")

# ── 1. Parity tweak: capture scaling == manual +1/level total ─────────────
assert abs(ALLY_LEVEL_STAT_BONUS * 6 - 1.0) < 1e-9, ALLY_LEVEL_STAT_BONUS
print("1. parity tweak: capture scaling == manual +1/level  [ok]")

# ── 2. Formula ────────────────────────────────────────────────────────────
goblin = {"key": "goblin_girl"}
harpy = {"key": "harpy_scout"}
lich = {"key": "lich_queen_avatar"}
g_gob = get_growth_rate(goblin)
g_harpy = get_growth_rate(harpy)
assert abs(g_gob - (GROWTH_TARGET_SUM - 10) * 0.85 / 50) < 1e-9, g_gob
assert abs(g_harpy - (GROWTH_TARGET_SUM - 13) * 0.85 / 50) < 1e-9, g_harpy
assert get_growth_rate(lich) < 0.02, get_growth_rate(lich)
assert get_growth_label(goblin) == "High"
assert get_growth_label(harpy) == "High"
assert get_growth_label(lich) == "—"
print(f"2. formula: Goblin {g_gob:.3f}/lv, Harpy {g_harpy:.3f}/lv, Lich {get_growth_rate(lich):.3f}  [ok]")

# ── 3. Delta math: Lv 2 → 50 grants exactly floor(49 × rate) ─────────────
ally = {
    "key": "goblin_girl", "name": "Goblin Girl", "monster_girl": True, "level": 2,
    "attributes": compute_girl_attributes({"key": "goblin_girl", "level": 2}),
    "growth_applied": 0,
}
start_total = sum(ally["attributes"].values())
manual = 0
for lvl in range(3, 51):
    ally["level"] = lvl
    ally["attributes"]["Strength"] += 1  # manual pick each level
    manual += 1
    msgs = apply_ally_growth(ally)
    if msgs:
        assert "Late Bloomer" in msgs[0], msgs
growth_total = sum(ally["attributes"].values()) - start_total - manual
expected = int(49 * g_gob)
assert growth_total == expected, (growth_total, expected)
assert ally["growth_applied"] == expected
print(f"3. Lv2→50 delta math: +{growth_total} growth points (expected +{expected})  [ok]")

# ── 4. Repeat call at the same level: no double-grant ────────────────────
before = dict(ally["attributes"])
assert apply_ally_growth(ally) == []
assert ally["attributes"] == before
print("4. repeat call at same level: no double-grant  [ok]")

# ── 5. Distribution: points go to the highest current attribute ──────────
test = {
    "key": "goblin_girl", "name": "Goblin Girl", "monster_girl": True, "level": 12,
    "attributes": {"Strength": 5, "Constitution": 10, "Dexterity": 6,
                   "Wisdom": 2, "Learning": 2, "Charisma": 3},
    "growth_applied": 0,
}
gain = int(11 * g_gob)
msgs = apply_ally_growth(test)
assert test["attributes"]["Constitution"] == 10 + gain, test["attributes"]
assert sum(test["attributes"].values()) == 28 + gain
assert msgs == [f"[Late Bloomer] Goblin Girl: +{gain} Constitution (growth)"], msgs
print(f"5. distribution: +{gain} → highest stat (CON 10→{10 + gain})  [ok]")

# ── 6. Tie-break: all equal → ATTRIBUTES order (Strength first) ──────────
tie = {
    "key": "goblin_girl", "name": "Tie", "monster_girl": True, "level": 12,
    "attributes": {a: 5 for a in ("Strength", "Constitution", "Dexterity",
                                  "Wisdom", "Learning", "Charisma")},
    "growth_applied": 0,
}
apply_ally_growth(tie)
assert tie["attributes"]["Strength"] == 5 + gain, tie["attributes"]
assert tie["attributes"]["Constitution"] == 5
print("6. tie-break: ATTRIBUTES order (Strength)  [ok]")

# ── 7. House round-trip persists growth_applied + attributes ─────────────
girl = {"key": "goblin_girl", "name": "Goblin Girl", "level": 3, "affection": 30}
ally = create_ally_from_girl(girl)
ally["level"] = 12
ally["growth_applied"] = 5
ally["attributes"]["Dexterity"] += 5
record = _ally_to_house_record(ally, {})
assert record["growth_applied"] == 5, record
restored = create_ally_from_girl(record)
assert restored["growth_applied"] == 5
assert restored["attributes"] == ally["attributes"]
print("7. house round-trip: growth_applied + attributes survive  [ok]")

# ── 8. Exclusions: heroines / non-monster / missing template / no attrs ──
hero_key = next((k for k, t in ENEMIES.items() if t.get("_heroine")), None)
if hero_key:
    assert get_growth_rate({"key": hero_key}) == 0.0, hero_key
assert get_growth_rate({"key": "no_such_key"}) == 0.0
assert get_growth_rate({"key": "goblin_girl", "_heroine_key": "goblin"}) == 0.0
assert apply_ally_growth({"key": "goblin_girl", "level": 10, "attributes": {}}) == []
print("8. exclusions: heroines / non-monster / no attrs  [ok]")

# ── 9. Legacy save: missing counter grants the floor total once ──────────
legacy = {
    "key": "harpy_scout", "name": "Harpy Scout", "monster_girl": True, "level": 20,
    "attributes": compute_girl_attributes({"key": "harpy_scout", "level": 20}),
    # no growth_applied → pre-patch save
}
msgs = apply_ally_growth(legacy)
expected = int(19 * g_harpy)
assert legacy["growth_applied"] == expected, legacy["growth_applied"]
assert msgs, "expected a catch-up grant"
print(f"9. legacy save: first application grants floor((L-1)×rate) = +{expected} once  [ok]")

# ── 10. gain_exp_ally integration (monkeypatched UI) ─────────────────────
import leveling

leveling._choose_level_attr = lambda name, level, attrs: ("Strength", False)
shown = []
leveling._show_level_results = lambda **kw: shown.append(kw)

ally = {
    "key": "goblin_girl", "name": "Goblin Girl", "monster_girl": True, "level": 2,
    "attributes": compute_girl_attributes({"key": "goblin_girl", "level": 2}),
    "growth_applied": 0, "exp": 0, "level_cap": 50,
    "max_hp": 100, "current_hp": 100, "level_hp_bonus": 4,
}
leveling.gain_exp_ally(ally, 10_000_000)  # level to cap (50)
assert ally["level"] == 50, ally["level"]
assert ally["growth_applied"] == int(49 * g_gob), ally["growth_applied"]
growth_lines = [m for kw in shown for m in (kw.get("milestones") or []) if "Late Bloomer" in m]
assert growth_lines, "level-up popup never showed a growth line"
print(f"10. gain_exp_ally: Lv2→50 popups included growth lines ({len(growth_lines)} shown)  [ok]")

print("\nAll growth checks passed.")
