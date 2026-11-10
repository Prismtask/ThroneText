"""Temp smoke test (2026-09-27): crit rework — 100% cap + overflow to damage.

- Raw vs resolved chance below/above the cap.
- Overflow converts to crit damage at 2:1 (EV-continuous with the 1.5x base).
- Enemies stay capped at 12% with no conversion.
- roll_critical_hit returns (is_crit, chance, overflow) — no wasted crit chance.
- All attack paths consume the overflow bonus; player skills use crit_bonus.
"""
import inspect
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from combat.stats import (
    get_raw_critical_chance, resolve_critical_chance, format_crit_summary,
    roll_critical_hit, apply_critical_damage, CRIT_MULTIPLIER,
    CRIT_CHANCE_CAP, CRIT_OVERFLOW_TO_DAMAGE,
)


def ent(buffs=(), debuffs=()):
    return {"active_buffs": list(buffs), "active_debuffs": list(debuffs)}


# ── Below the cap: flat buffs add up, unchanged resolution ──
e = ent(buffs=[{"type": "crit_chance", "value": 0.20}])
raw = get_raw_critical_chance(e, "player", dex=20, lrn=10)  # 5 + 6 + 2 + 20
assert abs(raw - 0.33) < 1e-9, raw
chance, overflow = resolve_critical_chance(e, "player", dex=20, lrn=10)
assert abs(chance - 0.33) < 1e-9 and overflow == 0.0

# ── Above the cap: 100% chance, overflow -> +0.5 dmg per 100% overflow ──
e2 = ent(buffs=[{"type": "crit_chance", "value": 0.20}])
raw2 = get_raw_critical_chance(e2, "player", dex=60, lrn=60, bonus=1.0)  # 5+8+5+20+100
assert abs(raw2 - 1.38) < 1e-9, raw2
chance2, overflow2 = resolve_critical_chance(e2, "player", dex=60, lrn=60, bonus=1.0)
assert chance2 == CRIT_CHANCE_CAP, chance2
assert abs(overflow2 - 0.38 * CRIT_OVERFLOW_TO_DAMAGE) < 1e-9, overflow2
assert abs((CRIT_MULTIPLIER + overflow2) - 1.69) < 1e-9
print("OK: 100% cap + 2:1 overflow conversion")

# ── crit_chance_down still subtracts; chance never negative ──
e3 = ent(debuffs=[{"type": "crit_chance_down", "value": 2.0}])
chance3, overflow3 = resolve_critical_chance(e3, "player", dex=0, lrn=0)
assert chance3 == 0.0 and overflow3 == 0.0, (chance3, overflow3)

# ── Enemies: old 12% cap, no conversion ──
en = ent()
echance, eoverflow = resolve_critical_chance(en, "enemy", dex=50)  # 3 + 6
assert abs(echance - 0.09) < 1e-9 and eoverflow == 0.0
echance2, eoverflow2 = resolve_critical_chance(en, "enemy", dex=50, bonus=5.0)
assert echance2 == 0.12 and eoverflow2 == 0.0
print("OK: enemies capped at 12%, no conversion")

# ── Roll returns 3-tuple; huge chance always crits with big overflow ──
is_crit, chance, overflow = roll_critical_hit(ent(), "player", dex=60, lrn=60, bonus=10.0)
assert is_crit and chance == 1.0, (is_crit, chance, overflow)
assert abs(overflow - (10.18 - 1.0) * 0.5) < 1e-9, overflow

# ── Overflow feeds the damage multiplier ──
assert apply_critical_damage(100, True, multiplier=CRIT_MULTIPLIER + 0.2) == 170

# ── Summary strings ──
s_compact = format_crit_summary(ent(), "player", dex=20, lrn=10, compact=True)
assert s_compact == "Crit: 13%  (×1.50)", s_compact
s_long = format_crit_summary(
    ent(buffs=[{"type": "crit_chance", "value": 1.0}]),
    "player", dex=60, lrn=60,
)  # raw 1.18 -> 100%, overflow 0.18 -> +0.09 -> ×1.59
assert "100% chance" in s_long and "1.59" in s_long and "overflow bonus +9%" in s_long, s_long
print("OK: format_crit_summary strings")

# ── All attack paths consume the overflow bonus ──
from combat import player_actions, skills, ally, ally_skills
from combat.weapon import black_silence_gloves
for mod in (player_actions, skills, ally, ally_skills):
    assert "overflow_crit" in inspect.getsource(mod), mod.__name__
assert "overflow_crit" in inspect.getsource(black_silence_gloves)
assert "crit_bonus" in inspect.getsource(skills)
print("OK: overflow consumed in all attack paths; player skills read crit_bonus")

# ── Combat HUD integration: party entries carry a compact crit line ──
from combat.combat_ui import format_combat_hud_data
player = {
    "name": "Tester", "current_hp": 50, "level": 5,
    "attributes": {"Strength": 10, "Constitution": 10, "Dexterity": 40,
                   "Learning": 30, "Wisdom": 10, "Charisma": 10},
    "active_buffs": [], "active_debuffs": [], "equipped": {}, "allies": [],
    "skill_cooldowns": {}, "party_order": [],
}
enemies = [{"name": "Mook", "hp": 20, "max_hp": 20, "con_mod": 0}]
data = format_combat_hud_data(player, enemies, active_ally=None, header="")
crit_line = data["party"][0]["crit_text"]
# dex 40 -> +8% (capped), lrn 30 -> +5% (capped): 18% total
assert crit_line == "Crit: 18%  (×1.50)", crit_line
print("OK: combat HUD crit line:", crit_line)

print("ALL CHECKS PASSED")
