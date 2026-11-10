"""Temp verification (2026-10-24): Mage rework — Time Warp + Cataclysm.

Covers:
  1. YAML: level swap, free-action flag, seven-element Cataclysm.
  2. UI: multi-element tag.
  3. Time Warp: cooldown reduction + free-action flag + handle_player_turn retry.
  4. Cataclysm: seven elemental hits, round-robin spread, Inferno on Fire,
     mastery burn upgrade (Conflagration) without extra hits.
"""
import sys

sys.path.insert(0, "c:/Code/Pandemonium")

import random
import yaml

import combat.skills as psk
import combat.stats as pstats
import combat.player_actions as pa
from combat.combat_ui import format_skill_elemental_tag

# ── Silence skill IO / force deterministic combat rolls ──
psk.c_print = lambda *a, **k: ""
psk.c_input = lambda *a, **k: "1"
pstats.roll_critical_hit = lambda *a, **k: (False, 0.0, 0.0)
pstats.roll_skill_dodge = lambda *a, **k: False
random.random = lambda: 0.0

failures = []


def check(label, cond, extra=""):
    status = "PASS" if cond else "FAIL"
    print(f"[{status}] {label}" + (f" — {extra}" if extra else ""))
    if not cond:
        failures.append(label)


# ── 1. YAML ──────────────────────────────────────────────────────────────
with open("c:/Code/Pandemonium/resources/skill_book/skill_list.yaml", encoding="utf-8") as f:
    data = yaml.safe_load(f)
mage = data["class_skills"]["Mage"]

check("Time Warp unlocks at Lv 20", mage["mage_timewarp"]["unlock_level"] == 20,
      str(mage["mage_timewarp"]["unlock_level"]))
check("Time Warp is a free action", mage["mage_timewarp"].get("free_action") is True)
check("Elemental Focus unlocks at Lv 12", mage["mage_elemental_focus"]["unlock_level"] == 12,
      str(mage["mage_elemental_focus"]["unlock_level"]))

cat = mage["mage_cap_cataclysm"]
EXPECTED_ELEMENTS = ["fire", "water", "thunder", "wind", "earth", "light", "dark"]
check("Cataclysm uses all seven elements", cat.get("elements") == EXPECTED_ELEMENTS,
      str(cat.get("elements")))
check("Cataclysm base power is 8", cat.get("base_power") == 8, str(cat.get("base_power")))
check("Cataclysm keeps Inferno", cat.get("burn_damage") == 18 and cat.get("burn_duration") == 4,
      f"{cat.get('burn_damage')}/{cat.get('burn_duration')}")

# ── 2. UI tag ────────────────────────────────────────────────────────────
check("Cataclysm tag is [MULTI]", format_skill_elemental_tag(cat) == " [MULTI]",
      repr(format_skill_elemental_tag(cat)))
check("Time Warp tag is [MAGICAL]", "[MAGICAL]" in format_skill_elemental_tag(mage["mage_timewarp"]))

# ── Fixtures ─────────────────────────────────────────────────────────────
ATTRS = ("Strength", "Constitution", "Dexterity", "Wisdom", "Learning", "Charisma")
D = 10 ** 6


def make_player(level=40, learning=10):
    p = {
        "name": "Hero", "class": "Mage", "level": level,
        "current_hp": 999, "passive_unlocked": True,
        "attributes": {a: 10 for a in ATTRS},
        "level_hp_bonus": 0,
        "equipped": {"weapon": None, "armor": None, "accessory1": None, "accessory2": None},
        "active_buffs": [], "active_debuffs": [],
        "elemental_dmg": {}, "elemental_res": {},
        "inventory": [], "allies": [],
        "skills": list(mage.keys()), "skill_mastery": {}, "skill_cooldowns": {},
    }
    p["attributes"]["Strength"] = 0
    p["attributes"]["Learning"] = learning
    return p


def make_enemy(hp=D):
    return {
        "name": "Dummy", "hp": hp, "max_hp": hp, "con_mod": 0,
        "active_debuffs": [], "active_buffs": [],
        "elemental_res": {}, "elemental_dmg": {},
    }


def burns(enemy):
    return [d for d in enemy.get("active_debuffs", []) if d.get("type") == "burn"]


# Actual unlock behavior at the swapped levels.
from combat.skills import unlock_skills_for_level

p12 = make_player(level=12)
p12["skills"] = []
p12["skill_loadout"] = None
unlock_skills_for_level(p12)
check("Lv 12 Mage unlocks Elemental Focus",
      "mage_elemental_focus" in p12["skills"], str(p12["skills"]))
check("Lv 12 Mage does not unlock Time Warp",
      "mage_timewarp" not in p12["skills"], str(p12["skills"]))

p20 = make_player(level=20)
p20["skills"] = []
p20["skill_loadout"] = None
unlock_skills_for_level(p20)
check("Lv 20 Mage unlocks Time Warp",
      "mage_timewarp" in p20["skills"], str(p20["skills"]))


# ── 3. Time Warp direct + player path ────────────────────────────────────
p = make_player(level=20)
p["skill_cooldowns"] = {"fireball": 3, "mage_frostnova": 2}
msg, _ = psk.execute_skill(p, "mage_timewarp", [make_enemy()], 0, 10, 10, 10, 10, 10)
check("Time Warp reduces cooldowns by 2", p["skill_cooldowns"] == {"fireball": 1},
      str(p["skill_cooldowns"]))
check("Time Warp sets the free-action flag", p.get("_skill_free_action") is True)
check("Time Warp message says act again", "act again" in msg.lower(), msg)

# Full handle_player_turn path: the turn must continue ("retry") and the
# skill must be clamped to >=1 cooldown before the menu reopens.
p = make_player(level=20)
p["skill_cooldowns"] = {"fireball": 3}
p["active_buffs"] = [{"type": "cooldown_reduction", "value": 99, "remaining": 2}]
logs = []
pa.c_print = lambda *a, **k: logs.append(" ".join(str(x) for x in a))
pa.c_input = lambda *a, **k: "1"
pa.print_combat_hud = lambda *a, **k: None
pa.get_action_menu = lambda *a, **k: ("", ["1"], set())
pa.get_available_skills = lambda player: [("mage_timewarp", mage["mage_timewarp"])]

res = pa.handle_player_turn(
    p, [make_enemy()], 0, 10, 10, 10, 10, 10, _action_override="1"
)
check("Time Warp returns retry (turn kept)", res == ("retry", False), str(res))
check("Time Warp clamp prevents same-turn recast",
      p["skill_cooldowns"].get("mage_timewarp") == 1, str(p.get("skill_cooldowns")))
check("Time Warp still reduces other cooldowns", p["skill_cooldowns"].get("fireball") == 1,
      str(p.get("skill_cooldowns")))
check("Free-action flag is consumed", "_skill_free_action" not in p)
check("Time Warp log includes act again",
      any("act again" in line.lower() for line in logs), str(logs))

# Even if a wedding accessory skips the cooldown, the free-action skill must
# still be clamped so it cannot be recast in the same turn.
p = make_player(level=20)
p["skill_cooldowns"] = {}
_orig_set_cd = pa.set_skill_cooldown
pa.set_skill_cooldown = lambda player, skill_id: None  # simulate cooldown-skip proc
res = pa.handle_player_turn(
    p, [make_enemy()], 0, 10, 10, 10, 10, 10, _action_override="1"
)
pa.set_skill_cooldown = _orig_set_cd
check("Time Warp clamp survives cooldown-skip procs",
      p["skill_cooldowns"].get("mage_timewarp") == 1, str(p.get("skill_cooldowns")))
check("Time Warp still returns retry after a cooldown skip",
      res == ("retry", False), str(res))

# ── 4. Cataclysm ─────────────────────────────────────────────────────────
# Single enemy: 7 hits of (8 + 10 LER + 5 LER//2) = 7 × 23 = 161.
p, e = make_player(), make_enemy()
msg, _ = psk.execute_skill(p, "mage_cap_cataclysm", [e], 0, 10, 10, 10, 10, 10)
total = D - e["hp"]
check("Cataclysm deals 7 hits to one enemy", total == 161, str(total))
check("Cataclysm logs 7 damage lines", msg.count("[Cataclysm]") == 7,
      str(msg.count("[Cataclysm]")))
for tag in ("[FIRE]", "[WATER]", "[THUNDER]", "[WIND]", "[EARTH]", "[LIGHT]", "[DARK]"):
    check(f"Cataclysm logs {tag}", tag in msg)
check("Cataclysm applies exactly one Inferno", len(burns(e)) == 1, str(burns(e)))
check("Cataclysm Inferno tier is 4", burns(e) and burns(e)[0].get("tier") == 4,
      str(burns(e)))
check("Cataclysm Inferno lasts 4 turns", burns(e) and burns(e)[0].get("remaining") == 4,
      str(burns(e)))

# Five enemies: 7 hits spread round-robin, all five damaged, one burn.
p = make_player()
enemies = [make_enemy() for _ in range(5)]
msg, _ = psk.execute_skill(p, "mage_cap_cataclysm", enemies, 0, 10, 10, 10, 10, 10)
total = sum(D - en["hp"] for en in enemies)
check("Cataclysm total damage is unchanged vs 5 enemies", total == 161, str(total))
check("Cataclysm damages every enemy", all(en["hp"] < D for en in enemies),
      str([D - en["hp"] for en in enemies]))
check("Cataclysm applies one burn across the field",
      sum(1 for en in enemies if burns(en)) == 1,
      str([len(burns(en)) for en in enemies]))
check("Cataclysm still logs 7 damage lines in AoE",
      msg.count("[Cataclysm]") == 7, str(msg.count("[Cataclysm]")))

# Mastery ★★★: Fire strike upgrades Inferno -> Conflagration, still 7 hits.
p = make_player()
p["skill_mastery"] = {"mage_cap_cataclysm": 50}
e = make_enemy()
msg, _ = psk.execute_skill(p, "mage_cap_cataclysm", [e], 0, 10, 10, 10, 10, 10)
check("Cataclysm mastery 3 keeps 7 hits", msg.count("[Cataclysm]") == 7,
      str(msg.count("[Cataclysm]")))
check("Cataclysm mastery 3 upgrades burn to Conflagration",
      burns(e) and burns(e)[0].get("tier") == 5, str(burns(e)))

# ── Result ───────────────────────────────────────────────────────────────
print()
if failures:
    print(f"RESULT: {len(failures)} FAILURE(S): {failures}")
    sys.exit(1)
print("RESULT: all checks passed.")
