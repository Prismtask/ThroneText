# Temp smoke test: Sky Piercer unique accessory (execute-on-threshold)
import sys
sys.path.insert(0, "c:/Code/Pandemonium")

from combat.weapon import sky_piercer as sp
import combat.skills as skills_mod
import combat.ally_skills as ask

# Silence I/O
def _quiet(*a, **k):
    return ""
sp.c_print = _quiet
skills_mod.c_print = _quiet
skills_mod.c_input = lambda prompt="": "0"
ask.c_print = _quiet
ask.c_input = lambda prompt="": "0"


def make_actor():
    return {"name": "Hero", "equipped": {
        "weapon": None, "armor": None, "accessory1": None, "accessory2": None}}


def equip(actor, enhance=0, slot="accessory1"):
    actor["equipped"][slot] = {"id": "sky_piercer", "enhance": enhance, "special": "sky_piercer"}


def make_enemy(hp, max_hp, **flags):
    e = {"name": "Dummy", "hp": hp, "max_hp": max_hp,
         "con_mod": 0, "active_debuffs": [], "active_buffs": [],
         "elemental_res": {}, "elemental_dmg": {},
         "super_boss": False, "captured": False,
         "slowed": False, "blinded": False, "silenced": False,
         "stunned": False, "dreaded": False}
    e.update(flags)
    return e


# ── 1. Detection ──
actor = make_actor()
assert not sp._actor_has_sky_piercer(actor)
equip(actor)
assert sp._actor_has_sky_piercer(actor)

# ── 2. Threshold scaling: 5 + 3*enhance, cap 20 ──
for enh, want in [(0, 5), (1, 8), (2, 11), (3, 14), (4, 17), (5, 20)]:
    equip(actor, enh)
    assert sp.get_sky_piercer_threshold_pct(actor) == want, (enh, sp.get_sky_piercer_threshold_pct(actor))

# ── 3. Execute at threshold ──
equip(actor, 0)  # 5%
e = make_enemy(50, 1000)
sp.check_sky_piercer_execute(actor, e, 10)
assert e["hp"] == 0

# ── 4. No execute above threshold ──
e = make_enemy(60, 1000)
sp.check_sky_piercer_execute(actor, e, 10)
assert e["hp"] == 60

# ── 5. No execute on superboss ──
e = make_enemy(50, 1000, super_boss=True)
sp.check_sky_piercer_execute(actor, e, 10)
assert e["hp"] == 50

# ── 6. No execute on zero damage ──
e = make_enemy(50, 1000)
sp.check_sky_piercer_execute(actor, e, 0)
assert e["hp"] == 50

# ── 7. No execute on captured enemy ──
e = make_enemy(50, 1000, captured=True)
sp.check_sky_piercer_execute(actor, e, 10)
assert e["hp"] == 50

# ── 8. Actor without accessory: no effect ──
e = make_enemy(50, 1000)
sp.check_sky_piercer_execute(make_actor(), e, 10)
assert e["hp"] == 50

# ── 9. Player skill integration (execute_skill end-pass) ──
player = {
    "name": "Hero", "class": "Warrior", "level": 15,
    "current_hp": 200, "passive_unlocked": True,
    "attributes": {"Strength": 10, "Constitution": 10, "Dexterity": 10,
                   "Wisdom": 10, "Learning": 10, "Charisma": 10},
    "equipped": {"weapon": None, "armor": None, "accessory1": None, "accessory2": None},
    "active_buffs": [], "active_debuffs": [],
    "elemental_dmg": {}, "elemental_res": {},
    "inventory": [], "allies": [],
    "skills": [], "skill_cooldowns": {}, "skill_mastery": {},
}
equip(player, 0)
aoe_id = next(sid for sid, sd in skills_mod.CLASS_SKILLS["Warrior"].items()
              if sd.get("target") == "enemies")
player["skills"] = [aoe_id]

enemies = [make_enemy(101, 2000, con_mod=999)]  # 1 dmg → 100/2000 = 5% → execute
msg, victory = skills_mod.execute_skill(player, aoe_id, enemies, 10, 10, 10, 10, 10, 10)
assert victory, msg
assert enemies[0]["hp"] == 0, enemies[0]

# Same setup without the accessory: no execute, no victory
player2 = dict(player)
player2["equipped"] = {"weapon": None, "armor": None, "accessory1": None, "accessory2": None}
enemies = [make_enemy(101, 2000, con_mod=999)]
msg2, victory2 = skills_mod.execute_skill(player2, aoe_id, enemies, 10, 10, 10, 10, 10, 10)
assert not victory2 and enemies[0]["hp"] == 100, (msg2, enemies[0])

# Superboss target: no execute even with accessory
enemies = [make_enemy(101, 2000, con_mod=999, super_boss=True)]
msg3, victory3 = skills_mod.execute_skill(player, aoe_id, enemies, 10, 10, 10, 10, 10, 10)
assert not victory3 and enemies[0]["hp"] == 100, (msg3, enemies[0])

# ── 10. Ally skill integration (execute_ally_skill end-pass) ──
ally = {
    "name": "Luna", "is_ally": True, "race": "Human", "level": 15,
    "current_hp": 150, "max_hp": 150,
    "attributes": {"Strength": 10, "Constitution": 10, "Dexterity": 10,
                   "Wisdom": 10, "Learning": 10, "Charisma": 10},
    "equipped": {"weapon": None, "armor": None, "accessory1": None, "accessory2": None},
    "active_buffs": [], "active_debuffs": [],
    "elemental_dmg": {}, "elemental_res": {},
    "skill_cooldowns": {}, "skill_mastery": {},
}
equip(ally, 0)
skill_def = {"name": "Test Strike", "target": "enemy", "power_type": "str",
             "base_power": 10, "hits": 1, "cooldown": 1}
enemies = [make_enemy(101, 2000, con_mod=999)]
msg4, victory4 = ask.execute_ally_skill(ally, player, "test_strike", skill_def, enemies, [])
assert victory4 and enemies[0]["hp"] == 0, (msg4, enemies[0])

print("SKY PIERCER SMOKE TEST PASSED")
