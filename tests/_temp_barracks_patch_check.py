# Temp verification: Barracks skill fixes
# (flat buff scaling, regen max HP, Dodge DEX, single-target Slow/Blind)
import sys
sys.path.insert(0, "c:/Code/Pandemonium")

import combat.ally_skills as ask

# Silence I/O
ask.c_print = lambda *a, **k: ""
ask.c_input = lambda prompt="": "1"


def make_enemy(name, hp=500):
    return {"name": name, "hp": hp, "max_hp": hp, "con_mod": 0,
            "active_debuffs": [], "active_buffs": [],
            "elemental_res": {}, "elemental_dmg": {},
            "slowed": False, "blinded": False}


def make_player():
    return {
        "name": "Hero", "class": "Warrior", "level": 15,
        "current_hp": 45, "passive_unlocked": True,
        "attributes": {"Strength": 10, "Constitution": 10, "Dexterity": 10,
                       "Wisdom": 10, "Learning": 10, "Charisma": 10},
        "level_hp_bonus": 0,
        "equipped": {"weapon": None, "armor": None, "accessory1": None, "accessory2": None},
        "active_buffs": [], "active_debuffs": [],
        "elemental_dmg": {}, "elemental_res": {},
        "inventory": [], "allies": [],
    }


def make_ally(level=15, max_hp=200):
    return {
        "name": "Luna", "is_ally": True, "race": "Human", "level": level,
        "current_hp": max_hp, "max_hp": max_hp,
        "attributes": {"Strength": 10, "Constitution": 10, "Dexterity": 10,
                       "Wisdom": 10, "Learning": 10, "Charisma": 10},
        "equipped": {"weapon": None, "armor": None, "accessory1": None, "accessory2": None},
        "active_buffs": [], "active_debuffs": [],
        "elemental_dmg": {}, "elemental_res": {},
        "skill_cooldowns": {}, "skill_mastery": {},
    }


def find_buff(actor, **match):
    for b in actor.get("active_buffs", []):
        if all(b.get(k) == v for k, v in match.items()):
            return b
    return None


# ── 1. _scale_effect_value math ──
f = ask._scale_effect_value
assert f({"value": 2, "scale_per_level": 0.15}, 1) == 2
assert f({"value": 2, "scale_per_level": 0.15}, 15) == 4
assert f({"value": 2, "scale_per_level": 0.15}, 40) == 7
assert f({"value": 3, "scale_per_level": 0.15}, 60) == 11
assert f({"value": 2, "scale_per_level": 0.10}, 40) == 5
assert f({"value": 2}, 40) == 2  # no key → flat

# ── 2. Strength Buff scales with caster level (player is the only party member) ──
# Level scaling (+0.15/lvl) plus the +1 baseline: base 2 -> 5 at Lv15.
player = make_player()
ally = make_ally(level=15)
skill = ask.get_learnable_skill_def("strength_buff")
msg, _ = ask.execute_ally_skill(ally, player, "strength_buff", skill, [], [])
buff = find_buff(player, stat="Strength")
assert buff and buff["value"] == 5, (msg, player["active_buffs"])

# ── 3. Heroic Onslaught scales and hits the whole party ──
player = make_player()
ally = make_ally(level=40)
skill = ask.get_learnable_skill_def("heroic_onslaught")
msg, _ = ask.execute_ally_skill(ally, player, "heroic_onslaught", skill, [], [ally])
# base 3 + 1 baseline + 39 * 0.15 = 9.85 -> 10 at Lv40
assert find_buff(player, stat="Strength")["value"] == 10, (msg, player["active_buffs"])
assert find_buff(ally, stat="Strength")["value"] == 10, (msg, ally["active_buffs"])

# ── 4. Weakening Curse scales (single target; 2 enemies → input picks #1) ──
player = make_player()
ally = make_ally(level=40)
e1, e2 = make_enemy("Goblin A"), make_enemy("Goblin B")
skill = ask.get_learnable_skill_def("weakening_curse")
msg, _ = ask.execute_ally_skill(ally, player, "weakening_curse", skill, [e1, e2], [])
curse = next(d for d in e1["active_debuffs"] if d["type"] == "curse")
assert curse["penalty"] == 5, (msg, e1["active_debuffs"])
assert not any(d["type"] == "curse" for d in e2["active_debuffs"]), e2["active_debuffs"]

# ── 5. Regenerate on player uses real max HP (45 → 4/tick, not 10) ──
player = make_player()
ally = make_ally(level=15)
skill = ask.get_learnable_skill_def("regenerate")
msg, _ = ask.execute_ally_skill(ally, player, "regenerate", skill, [], [])
hot = find_buff(player, type="hot")
assert hot and hot["value"] == 4, (msg, player["active_buffs"])

# ── 6. Mass Regenerate: player 45*0.08=3, ally 200*0.08=16 ──
player = make_player()
ally = make_ally(level=15, max_hp=200)
skill = ask.get_learnable_skill_def("mass_regenerate")
msg, _ = ask.execute_ally_skill(ally, player, "mass_regenerate", skill, [], [ally])
assert find_buff(player, type="hot")["value"] == 3, (msg, player["active_buffs"])
assert find_buff(ally, type="hot")["value"] == 16, (msg, ally["active_buffs"])

# ── 7. Dodge grants evasion + 2 DEX ──
player = make_player()
ally = make_ally(level=15)
skill = ask.get_learnable_skill_def("dodge")
msg, _ = ask.execute_ally_skill(ally, player, "dodge", skill, [], [])
assert find_buff(ally, type="evasion") is not None, (msg, ally["active_buffs"])
dex = find_buff(ally, stat="Dexterity")
# base 2 + 1 baseline + 14 * 0.15 = 5.1 -> 5 at Lv15
assert dex and dex["value"] == 5, (msg, ally["active_buffs"])

# ── 8. Slow hits only the chosen target ──
player = make_player()
ally = make_ally(level=15)
e1, e2 = make_enemy("Goblin A"), make_enemy("Goblin B")
skill = ask.get_learnable_skill_def("slow")
msg, _ = ask.execute_ally_skill(ally, player, "slow", skill, [e1, e2], [])
assert e1["slowed"] and not e2["slowed"], (msg, e1["slowed"], e2["slowed"])

# ── 9. Blind hits only the chosen target ──
e1, e2 = make_enemy("Goblin A"), make_enemy("Goblin B")
skill = ask.get_learnable_skill_def("blind")
msg, _ = ask.execute_ally_skill(ally, player, "blind", skill, [e1, e2], [])
assert e1["blinded"] and not e2["blinded"], (msg, e1["blinded"], e2["blinded"])

# ── 10. Rescaled tier gates + ascension caps (YAML sanity) ──
expected = {1: (1, 300, 0), 2: (8, 800, 0), 3: (16, 2000, 20), 4: (25, 5000, 30),
            5: (35, 10000, 40), 6: (45, 20000, 50)}
all_skills = ask.get_all_learnable_skills()
assert len(all_skills) == 47, len(all_skills)
for sid, sd in all_skills.items():
    lvl, cost, cap = expected[sd.get("tier", 1)]
    assert sd.get("required_level") == lvl, (sid, sd.get("required_level"), lvl)
    assert sd.get("exp_cost") == cost, (sid, sd.get("exp_cost"), cost)
    assert sd.get("required_cap", 0) == cap, (sid, sd.get("required_cap", 0), cap)

# ── 11. Teaching respects the new level gate ──
assert ask.teach_ally_skill(make_ally(level=7), "power_strike") is False
ok = make_ally(level=8)
assert ask.teach_ally_skill(ok, "power_strike") is True
assert ok["learning"]["exp_needed"] == 800, ok["learning"]

# ── 12. Ascension (level-cap) gate: captured girls can't skip tiers ──
t3 = ask.get_learnable_skill_def("multi_hit")
t4 = ask.get_learnable_skill_def("annihilate")
captured = make_ally(level=30)  # high level, default cap 10
assert not ask.meets_skill_requirements(captured, t3)
assert not ask.meets_skill_requirements(captured, t4)
assert ask.teach_ally_skill(make_ally(level=30), "annihilate") is False
captured["level_cap"] = 20
assert ask.meets_skill_requirements(captured, t3)
assert not ask.meets_skill_requirements(captured, t4)
captured["level_cap"] = 30
assert ask.meets_skill_requirements(captured, t4)
ok30 = make_ally(level=30)
ok30["level_cap"] = 30
assert ask.teach_ally_skill(ok30, "annihilate") is True

# ── 13. Revive clears the defeated flag (bug fix) ──
from combat.ally import get_alive_allies
player = make_player()
caster = make_ally(level=35)
fallen = make_ally(level=35, max_hp=200)
fallen["current_hp"] = 0
fallen["defeated"] = True
skill = ask.get_innate_skill_def("raise_dead")
assert skill is not None
ask.c_input = lambda prompt="": "2"  # pick the fallen ally (index 2)
msg, _ = ask.execute_ally_skill(caster, player, "raise_dead", skill, [], [fallen])
assert fallen["current_hp"] == 60, (msg, fallen["current_hp"])
assert fallen["defeated"] is False, msg
player["allies"] = [fallen]
assert fallen in get_alive_allies(player), msg

# ✦✦ mastery: Raise Dead rises to 50%
player = make_player()
caster = make_ally(level=35)
caster["skill_mastery"]["raise_dead"] = 150
fallen = make_ally(level=35, max_hp=200)
fallen["current_hp"] = 0
fallen["defeated"] = True
ask.c_input = lambda prompt="": "2"
msg, _ = ask.execute_ally_skill(caster, player, "raise_dead", skill, [], [fallen])
assert fallen["current_hp"] == 100, (msg, fallen["current_hp"])

# ── 14. Aegis Shell sizes its barrier from the caster's max HP ──
from combat.status_effects import try_consume_death_ward
player = make_player()
caster = make_ally(level=35, max_hp=300)
skill = ask.get_learnable_skill_def("aegis_shell")
ask.c_input = lambda prompt="": "2"  # pick the caster from [player, caster]
msg, _ = ask.execute_ally_skill(caster, player, "aegis_shell", skill, [], [caster])
barrier = find_buff(caster, type="barrier")
assert barrier and barrier["value"] == 90, (msg, caster["active_buffs"])

# ── 15. Radiant Rebirth: mastery-scaled revive (45% base → 70% at ✦✦) + 15% caster-HP shield ──
player = make_player()
caster = make_ally(level=45, max_hp=400)
fallen = make_ally(level=45, max_hp=200)
fallen["current_hp"] = 0
fallen["defeated"] = True
skill = ask.get_learnable_skill_def("radiant_rebirth")
msg, _ = ask.execute_ally_skill(caster, player, "radiant_rebirth", skill, [], [fallen])
assert fallen["current_hp"] == 90, (msg, fallen["current_hp"])
assert fallen["defeated"] is False, msg
shield = find_buff(fallen, type="barrier")
assert shield and shield["value"] == 60, (msg, fallen["active_buffs"])

# ✦✦ mastery: 70% revive
player = make_player()
caster = make_ally(level=45, max_hp=400)
caster["skill_mastery"]["radiant_rebirth"] = 150
fallen = make_ally(level=45, max_hp=200)
fallen["current_hp"] = 0
fallen["defeated"] = True
msg, _ = ask.execute_ally_skill(caster, player, "radiant_rebirth", skill, [], [fallen])
assert fallen["current_hp"] == 140, (msg, fallen["current_hp"])

# Phoenix Call: 20% base → 35% at ✦✦
phoenix = ask.get_learnable_skill_def("phoenix_call")
for uses, expected_hp in ((0, 40), (150, 70)):
    player = make_player()
    caster = make_ally(level=35)
    if uses:
        caster["skill_mastery"]["phoenix_call"] = uses
    fallen = make_ally(level=35, max_hp=200)
    fallen["current_hp"] = 0
    fallen["defeated"] = True
    msg, _ = ask.execute_ally_skill(caster, player, "phoenix_call", phoenix, [], [fallen])
    assert fallen["current_hp"] == expected_hp, (msg, fallen["current_hp"])

# ── 16. Undying Vow applies a death ward that saves from lethal ──
player = make_player()
caster = make_ally(level=45)
skill = ask.get_learnable_skill_def("undying_vow")
msg, _ = ask.execute_ally_skill(caster, player, "undying_vow", skill, [], [caster])
assert find_buff(caster, type="death_ward") is not None, (msg, caster["active_buffs"])
assert find_buff(player, type="death_ward") is not None, (msg, player["active_buffs"])
caster["current_hp"] = 0
assert try_consume_death_ward(caster) is True
assert caster["current_hp"] == 1
assert find_buff(caster, type="death_ward") is None
assert try_consume_death_ward(caster) is False

# ── 17. Mastery extension: thresholds, bonus table, labels, and ally hooks ──
from combat.skills import (
    MASTERY_THRESHOLDS, get_mastery_bonuses, get_skill_mastery_level,
    format_mastery_label,
)
assert MASTERY_THRESHOLDS == [10, 25, 50, 90, 150], MASTERY_THRESHOLDS
b = get_mastery_bonuses
assert b("s", 0)["power_mult"] == 1.0 and b("s", 0)["duration_bonus"] == 0
assert b("s", 1)["power_mult"] == 1.15
assert b("s", 2)["cooldown_reduction"] == 1 and b("s", 2)["power_mult"] == 1.15
assert b("s", 3)["power_mult"] == 1.30 and b("s", 3)["extra_effect"] and b("s", 3)["status_mult"] == 1.5
assert b("s", 4)["power_mult"] == 1.45 and b("s", 4)["duration_bonus"] == 1 and b("s", 4)["status_mult"] == 1.75
assert b("s", 5)["power_mult"] == 1.60 and b("s", 5)["cooldown_reduction"] == 2 and b("s", 5)["status_mult"] == 2.0
counter = {"skill_mastery": {"s": 89}}
assert get_skill_mastery_level(counter, "s") == 3
counter["skill_mastery"]["s"] = 90
assert get_skill_mastery_level(counter, "s") == 4
counter["skill_mastery"]["s"] = 149
assert get_skill_mastery_level(counter, "s") == 4
counter["skill_mastery"]["s"] = 150
assert get_skill_mastery_level(counter, "s") == 5

# Display convention: ★ / ★★ / ★★★ / ✦ / ✦✦
counter["skill_mastery"]["s"] = 50
assert format_mastery_label("s", counter) == "★★★"
counter["skill_mastery"]["s"] = 90
assert format_mastery_label("s", counter) == "✦"
counter["skill_mastery"]["s"] = 150
assert format_mastery_label("s", counter) == "✦✦"
lbl_ally = make_ally(level=15)
lbl_ally["skill_mastery"]["x"] = 90
assert ask.format_ally_mastery_label("x", lbl_ally) == "✦"
lbl_ally["skill_mastery"]["x"] = 150
assert ask.format_ally_mastery_label("x", lbl_ally) == "✦✦"

# Ally duration hook: Dodge's 2-turn evasion lasts 3 turns at ★4
player = make_player()
ally = make_ally(level=15)
ally["skill_mastery"]["dodge"] = 90
skill = ask.get_learnable_skill_def("dodge")
msg, _ = ask.execute_ally_skill(ally, player, "dodge", skill, [], [])
assert find_buff(ally, type="evasion")["remaining"] == 3, (msg, ally["active_buffs"])

# Ally status potency: Poison Strike's 4/tick poison becomes 8 at ★5
player = make_player()
ally = make_ally(level=15)
ally["skill_mastery"]["poison_strike"] = 150
e1 = make_enemy("Goblin")
skill = ask.get_learnable_skill_def("poison_strike")
msg, _ = ask.execute_ally_skill(ally, player, "poison_strike", skill, [e1], [])
poison = next(d for d in e1["active_debuffs"] if d["type"] == "poison")
assert poison["damage"] == 8, (msg, e1["active_debuffs"])

# Ally cooldown cap: Benediction CD 5 becomes 3 at ★5
player = make_player()
ally = make_ally(level=15)
ally["skill_mastery"]["benediction"] = 150
skill = ask.get_learnable_skill_def("benediction")
msg, _ = ask.execute_ally_skill(ally, player, "benediction", skill, [], [])
assert ally["skill_cooldowns"]["benediction"] == 3, (msg, ally["skill_cooldowns"])

# ── 18. Player-side mastery hooks: duration_bonus (✦) and status_mult (✦✦) ──
import combat.skills as psk
psk.c_print = lambda *a, **k: ""
psk.c_input = lambda prompt="": "1"


def make_skill_player(cls):
    p = make_player()
    p["class"] = cls
    p["skills"] = []
    p["skill_mastery"] = {}
    p["skill_cooldowns"] = {}
    return p

# Battle Cry ★0 regression: 3 turns; ★4: 4 turns + message reflects it
p = make_skill_player("Warrior")
msg, _ = psk.execute_skill(p, "war_battlecry", [], 10, 10, 10, 10, 10, 10)
assert all(b["remaining"] == 3 for b in p["active_buffs"]), (msg, p["active_buffs"])
p = make_skill_player("Warrior")
p["skill_mastery"]["war_battlecry"] = 90
msg, _ = psk.execute_skill(p, "war_battlecry", [], 10, 10, 10, 10, 10, 10)
assert all(b["remaining"] == 4 for b in p["active_buffs"]), (msg, p["active_buffs"])
assert "for 4 turns!" in msg, msg

# Divine Shield ★4: 3 (extra effect) + 1 (✦) = 4 turns
p = make_skill_player("Cleric")
p["skill_mastery"]["clr_shield"] = 90
msg, _ = psk.execute_skill(p, "clr_shield", [], 10, 10, 10, 10, 10, 10)
assert p["active_buffs"][0]["remaining"] == 4, (msg, p["active_buffs"])

# Berserk ★4: 4 double-attack turns
p = make_skill_player("Barbarian")
p["skill_mastery"]["bar_berserk"] = 90
msg, _ = psk.execute_skill(p, "bar_berserk", [], 10, 10, 10, 10, 10, 10)
assert p["berserk_turns"] == 4, (msg, p.get("berserk_turns"))

# Sunder Armor ★4: value 3+2=5 (★3 extra), duration 3+1=4 (✦)
p = make_skill_player("Barbarian")
p["skill_mastery"]["bar_sunder"] = 90
e1 = make_enemy("Goblin")
msg, _ = psk.execute_skill(p, "bar_sunder", [e1], 10, 10, 10, 10, 10, 10)
sunder = next(d for d in e1["active_debuffs"] if d["type"] == "sunder")
assert sunder["value"] == 5 and sunder["remaining"] == 4, (msg, sunder)

# Venomous Blade ★5: 5/tick poison doubled to 10
p = make_skill_player("Rogue")
p["skill_mastery"]["rog_venom"] = 150
e1 = make_enemy("Goblin")
msg, _ = psk.execute_skill(p, "rog_venom", [e1], 10, 10, 10, 10, 10, 10)
poison = next(d for d in e1["active_debuffs"] if d["type"] == "poison")
assert poison["damage"] == 10, (msg, e1["active_debuffs"])

# Soul Fire ✦✦: base 6 (Burn, tier 2) upgraded +2 tiers → Inferno (tier 4)
from combat.status_effects import damage_to_burn_tier
p = make_skill_player("Warlock")
p["skill_mastery"]["lck_soul_fire"] = 150
e1 = make_enemy("Goblin")
msg, _ = psk.execute_skill(p, "lck_soul_fire", [e1], 10, 10, 10, 10, 10, 10)
burn = next(d for d in e1["active_debuffs"] if d["type"] == "burn")
assert burn["tier"] == damage_to_burn_tier(6) + 2, (msg, e1["active_debuffs"])

# Bastion of Light ★4: whole party gets a 4-turn defense buff
p = make_skill_player("Paladin")
p["skill_mastery"]["pal_bastion"] = 90
ally = make_ally(level=15)
msg, _ = psk.execute_skill(p, "pal_bastion", [], 10, 10, 10, 10, 10, 10, allies=[ally])
assert find_buff(p, type="defense")["remaining"] == 4, (msg, p["active_buffs"])
assert find_buff(ally, type="defense")["remaining"] == 4, (msg, ally["active_buffs"])

# Smoke Bomb ★4: blind lasts 4 turns
p = make_skill_player("Rogue")
p["skill_mastery"]["rog_smoke"] = 90
e1 = make_enemy("Goblin")
msg, _ = psk.execute_skill(p, "rog_smoke", [e1], 10, 10, 10, 10, 10, 10)
blind = next(d for d in e1["active_debuffs"] if d["type"] == "blind")
assert blind["remaining"] == 4, (msg, e1["active_debuffs"])

# ── 19. Support potency scaling: status_mult on magnitudes + burn tier ladder ──

# Battle Cry ✦✦: level-scaled base 5 (Lv15) doubled by status_mult → 10
p = make_skill_player("Warrior")
p["skill_mastery"]["war_battlecry"] = 150
msg, _ = psk.execute_skill(p, "war_battlecry", [], 10, 10, 10, 10, 10, 10)
assert all(b["value"] == 10 for b in p["active_buffs"]), (msg, p["active_buffs"])

# Hunter's Mark ✦✦: +50% → +100% damage taken
p = make_skill_player("Ranger")
p["skill_mastery"]["rng_mark"] = 150
e1 = make_enemy("Goblin")
msg, _ = psk.execute_skill(p, "rng_mark", [e1], 10, 10, 10, 10, 10, 10)
assert e1["hunters_mark_bonus"] == 1.0, (msg, e1.get("hunters_mark_bonus"))

# Dark Curse ✦: penalty 2 → 4
p = make_skill_player("Warlock")
p["skill_mastery"]["lck_curse"] = 90
e1 = make_enemy("Goblin")
msg, _ = psk.execute_skill(p, "lck_curse", [e1], 10, 10, 10, 10, 10, 10)
assert e1["active_debuffs"][0]["penalty"] == 4, (msg, e1["active_debuffs"])

# Soul Fear ✦✦: 20% less damage → 40%
p = make_skill_player("Warlock")
p["skill_mastery"]["lck_fear"] = 150
e1 = make_enemy("Goblin")
msg, _ = psk.execute_skill(p, "lck_fear", [e1], 10, 10, 10, 10, 10, 10)
fear = next(d for d in e1["active_debuffs"] if d["type"] == "fear")
assert fear["value"] == 0.40, (msg, e1["active_debuffs"])

# Burn tier ladder: Soul Fire ★3 = Blaze (base tier 2 + 1)
p = make_skill_player("Warlock")
p["skill_mastery"]["lck_soul_fire"] = 50
e1 = make_enemy("Goblin")
msg, _ = psk.execute_skill(p, "lck_soul_fire", [e1], 10, 10, 10, 10, 10, 10)
burn = next(d for d in e1["active_debuffs"] if d["type"] == "burn")
assert burn["tier"] == damage_to_burn_tier(6) + 1, (msg, e1["active_debuffs"])

# Aura of Despair ✦✦: +15% → +30% damage taken
player = make_player()
ally = make_ally(level=35)
ally["skill_mastery"]["aura_of_despair"] = 150
e1 = make_enemy("Goblin")
aura = ask.get_learnable_skill_def("aura_of_despair")
msg, _ = ask.execute_ally_skill(ally, player, "aura_of_despair", aura, [e1], [])
dt = next(d for d in e1["active_debuffs"] if d["type"] == "damage_taken_up")
assert dt["value"] == 0.30, (msg, e1["active_debuffs"])

# Thunderfall ✦✦: shock 12 → 24
player = make_player()
ally = make_ally(level=35)
ally["skill_mastery"]["thunderfall"] = 150
e1 = make_enemy("Goblin")
tf = ask.get_learnable_skill_def("thunderfall")
msg, _ = ask.execute_ally_skill(ally, player, "thunderfall", tf, [e1], [])
shock = next(d for d in e1["active_debuffs"] if d["type"] == "shock")
assert shock["damage"] == 24, (msg, e1["active_debuffs"])

# Weakening Curse ✦✦: level-scaled 5 → 10
player = make_player()
ally = make_ally(level=40)
ally["skill_mastery"]["weakening_curse"] = 150
e1 = make_enemy("Goblin")
skill = ask.get_learnable_skill_def("weakening_curse")
msg, _ = ask.execute_ally_skill(ally, player, "weakening_curse", skill, [e1], [])
curse = next(d for d in e1["active_debuffs"] if d["type"] == "curse")
assert curse["penalty"] == 10, (msg, e1["active_debuffs"])

# Aegis Shell ✦✦: barrier 90 → 180
player = make_player()
caster = make_ally(level=35, max_hp=300)
caster["skill_mastery"]["aegis_shell"] = 150
skill = ask.get_learnable_skill_def("aegis_shell")
ask.c_input = lambda prompt="": "2"  # pick the caster from [player, caster]
msg, _ = ask.execute_ally_skill(caster, player, "aegis_shell", skill, [], [caster])
barrier = find_buff(caster, type="barrier")
assert barrier and barrier["value"] == 180, (msg, caster["active_buffs"])

# Dodge ✦: 50% evasion → 87.5%
player = make_player()
ally = make_ally(level=15)
ally["skill_mastery"]["dodge"] = 90
skill = ask.get_learnable_skill_def("dodge")
msg, _ = ask.execute_ally_skill(ally, player, "dodge", skill, [], [])
assert find_buff(ally, type="evasion")["value"] == 0.875, (msg, ally["active_buffs"])

print("BARRACKS PATCH CHECK PASSED")
