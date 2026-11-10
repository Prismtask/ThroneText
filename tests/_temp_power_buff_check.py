# Temp verification (2026-10-03): power_buff (Overclock / Tinker Enhancement) now works
# for the player, is consumed by basic attacks on both sides, applies to every hit of a
# multi-hit skill, and is no longer wasted by heal/support casts.
import sys
sys.path.insert(0, "c:/Code/Pandemonium")
import random

import combat.stats as pstats
import combat.skills as psk
import combat.player_actions as pact
import combat.ally as amod
import combat.ally_skills as ask
import combat.combat_ui as cui

# ── Silence I/O / HUD (menus: "a" = attack; numbered prompts: "1") ──
for mod in (psk, pact, amod, ask):
    if hasattr(mod, "c_print"):
        mod.c_print = lambda *a, **k: ""
psk.c_input = lambda *a, **k: "1"
ask.c_input = lambda *a, **k: "1"
pact.c_input = lambda *a, **k: "a"
amod.c_input = lambda *a, **k: "a"
cui.print_combat_hud = lambda *a, **k: None

# ── Deterministic RNG: no crits, no dodges, fixed basic-attack rolls ──
pstats.roll_critical_hit = lambda *a, **k: (False, 0.0, 0.0)
pstats.roll_dodge = lambda *a, **k: (False, 0.0)
random.randint = lambda a, b: 7

ATTRS = ("Strength", "Constitution", "Dexterity", "Wisdom", "Learning", "Charisma")
D = 10**6


def make_enemy(hp=D):
    return {"name": "Dummy", "hp": hp, "max_hp": hp, "con_mod": 0,
            "active_debuffs": [], "active_buffs": [],
            "elemental_res": {}, "elemental_dmg": {}}


def make_player(cls="Warrior"):
    p = {"name": "Hero", "class": cls, "level": 15,
         "current_hp": 45, "passive_unlocked": True,
         "attributes": {a: 10 for a in ATTRS},
         "level_hp_bonus": 0,
         "equipped": {"weapon": None, "armor": None, "accessory1": None, "accessory2": None},
         "active_buffs": [], "active_debuffs": [],
         "elemental_dmg": {}, "elemental_res": {},
         "inventory": [], "allies": [],
         "skills": [], "skill_mastery": {}, "skill_cooldowns": {}}
    p["attributes"]["Strength"] = 0  # keep STR milestones out of the math
    return p


def make_ally():
    return {"name": "Luna", "is_ally": True, "race": "Human", "level": 15,
            "current_hp": 200, "max_hp": 200,
            "attributes": {a: 10 for a in ATTRS},
            "equipped": {"weapon": None, "armor": None, "accessory1": None, "accessory2": None},
            "active_buffs": [], "active_debuffs": [],
            "elemental_dmg": {}, "elemental_res": {},
            "skill_cooldowns": {}, "skill_mastery": {},
            "innate_skills": [], "learned_skills": []}


def has_pbuff(actor):
    return any(b.get("type") == "power_buff" for b in actor["active_buffs"])


# ── 1. Player class skill: consumes and applies (war_execute, STR) ──
p, e = make_player(), make_enemy()
msg, _ = psk.execute_skill(p, "war_execute", [e], 0, 10, 10, 10, 10, 10)
base = D - e["hp"]
assert base == 15, base  # (10 base + 0 STR + 5 LRN//2) × 1.0
p, e = make_player(), make_enemy()
p["active_buffs"].append({"type": "power_buff", "value": 0.5, "remaining": 2})
msg, _ = psk.execute_skill(p, "war_execute", [e], 0, 10, 10, 10, 10, 10)
buffed = D - e["hp"]
assert buffed == 22, buffed  # int(15 × 1.5)
assert not has_pbuff(p), p["active_buffs"]
assert "Empowered!" in msg, msg
print("OK: player class skill consumes power_buff and deals 1.5x (15 -> 22)")

# ── 2. Multi-hit skill: consumed once, every hit empowered ──
p, e = make_player("Ranger"), make_enemy()
p["active_buffs"].append({"type": "power_buff", "value": 0.5, "remaining": 2})
msg, _ = psk.execute_skill(p, "rng_rapid", [e], 10, 10, 10, 10, 10, 10)
total = D - e["hp"]
assert total == 102, total  # 3 hits × int((8+10+5) × 1.5) = 3 × 34
assert msg.count("Empowered!") == 1, msg
assert not has_pbuff(p)
print("OK: multi-hit consumes once, all hits empowered (3 × 34 = 102)")

# ── 3. Non-damage skill: buff survives ──
p = make_player()
p["active_buffs"].append({"type": "power_buff", "value": 0.5, "remaining": 2})
msg, _ = psk.execute_skill(p, "war_battlecry", [], 10, 10, 10, 10, 10, 10)
assert has_pbuff(p), p["active_buffs"]
assert "Empowered!" not in msg, msg
print("OK: player buff skill does not consume power_buff")

# ── 4. Player heal: buff survives ──
p = make_player("Cleric")
p["current_hp"] = 10
p["active_buffs"].append({"type": "power_buff", "value": 0.5, "remaining": 2})
msg, _ = psk.execute_skill(p, "clr_heal", [], 10, 10, 10, 10, 10, 10)
assert has_pbuff(p), p["active_buffs"]
assert "Empowered!" not in msg, msg
print("OK: player heal does not consume power_buff")

# ── 5a. Ally damaging skill: still consumes ──
a, p, e = make_ally(), make_player(), make_enemy()
a["active_buffs"].append({"type": "power_buff", "value": 0.5, "remaining": 2})
skill = ask.get_learnable_skill_def("poison_strike")
msg, _ = ask.execute_ally_skill(a, p, "poison_strike", skill, [e], [])
assert not has_pbuff(a), a["active_buffs"]
assert "Empowered!" in msg, msg
assert any(d["type"] == "poison" for d in e["active_debuffs"])
print("OK: ally damaging skill still consumes power_buff")

# ── 5b. Ally heal: no longer wastes it ──
a, p = make_ally(), make_player()
a["active_buffs"].append({"type": "power_buff", "value": 0.5, "remaining": 2})
skill = ask.get_learnable_skill_def("ocean_lullaby")
msg, _ = ask.execute_ally_skill(a, p, "ocean_lullaby", skill, [], [])
assert has_pbuff(a), a["active_buffs"]
assert "Empowered!" not in msg, msg
print("OK: ally heal no longer wastes power_buff")

# ── 6. Player basic attack: consumes and applies ──
p, e = make_player(), make_enemy()
pact.handle_player_turn(p, [e], 10, 10, 10, 10, 10, 10, _action_override="a")
assert D - e["hp"] == 17, D - e["hp"]  # randint=7 + STR 10 + milestone 0
p, e = make_player(), make_enemy()
p["active_buffs"].append({"type": "power_buff", "value": 0.5, "remaining": 2})
pact.handle_player_turn(p, [e], 10, 10, 10, 10, 10, 10, _action_override="a")
assert D - e["hp"] == 25, D - e["hp"]  # int(17 × 1.5)
assert not has_pbuff(p), p["active_buffs"]
print("OK: player basic attack consumes power_buff and deals 1.5x (17 -> 25)")

# ── 7. Ally basic attack: consumes and applies ──
a, p, e = make_ally(), make_player(), make_enemy()
a["active_buffs"].append({"type": "power_buff", "value": 0.5, "remaining": 2})
amod.handle_ally_turn(a, p, [e], 10, 10, 10, 10, 10, 10)
assert D - e["hp"] == 30, D - e["hp"]  # 7 + a_str 11 (Human passive) + milestone 2 = 20, ×1.5
assert not has_pbuff(a), a["active_buffs"]
print("OK: ally basic attack consumes power_buff and deals 1.5x (20 -> 30)")

# ── 8. HUD tag while empowered ──
p = make_player()
p["active_buffs"].append({"type": "power_buff", "value": 0.8, "remaining": 2})
tags = cui._get_entity_buff_tags(p)
assert "PWR+80%" in tags, tags
print("OK: combat HUD shows PWR+80% tag")

print("\nALL POWER_BUFF CHECKS PASSED")
