# Temp verification (2026-10-15): Wave-2 player skills (Lv 20/26/32) + Phase 2
# (capstones Lv 40 + Battle Loadout) of docs/player_skill_extension_design.md.
# Covers: YAML structure, generic on-hit statuses (fallback), AoE bleed, barrier,
# regen_pct, evasion/crit buffs, crit_damage buff math, elemental buff math,
# mark bonus buff, blood pact HP cost, siphon drain, self-vulnerability.
import sys
sys.path.insert(0, "c:/Code/Pandemonium")
import random

import yaml
import combat.stats as pstats
import combat.skills as psk
import combat.elemental as pel

# ── Silence I/O (skill menus / target prompts: "1" = first option) ──
psk.c_print = lambda *a, **k: ""
_CHOICE = {"v": "1"}
psk.c_input = lambda *a, **k: _CHOICE["v"]

# ── Deterministic RNG: no crits, no dodges, stun procs, fixed rolls ──
pstats.roll_critical_hit = lambda *a, **k: (False, 0.0, 0.0)
pstats.roll_skill_dodge = lambda *a, **k: False
random.random = lambda: 0.0
random.randint = lambda a, b: 7

ATTRS = ("Strength", "Constitution", "Dexterity", "Wisdom", "Learning", "Charisma")
D = 10 ** 6

# ── 1. YAML structure ──
with open("c:/Code/Pandemonium/resources/skill_book/skill_list.yaml", encoding="utf-8") as f:
    data = yaml.safe_load(f)
class_skills = data["class_skills"]
WAVE2 = {
    "Warrior": {"war_reckless_charge": 20, "war_banner": 26, "war_titan_swing": 32},
    "Mage": {"mage_elemental_focus": 20, "mage_glacial_prison": 26, "mage_singularity": 32},
    "Rogue": {"rog_caltrops": 20, "rog_nightshade": 26, "rog_perfect_opening": 32},
    "Cleric": {"clr_prayer_mending": 20, "clr_blessed_aegis": 26, "clr_wrath_of_heaven": 32},
    "Ranger": {"rng_camouflage": 20, "rng_blast_arrow": 26, "rng_hawks_eye": 32},
    "Paladin": {"pal_blessing": 20, "pal_censure": 26, "pal_dawnbreaker": 32},
    "Warlock": {"lck_grasp_void": 20, "lck_blood_pact": 26, "lck_siphon_soul": 32},
    "Barbarian": {"bar_battle_trance": 20, "bar_reckless_abandon": 26, "bar_skullbreaker": 32},
}
CAPSTONES = {
    "Warrior": "war_cap_onslaught",
    "Mage": "mage_cap_cataclysm",
    "Rogue": "rog_cap_deaths_embrace",
    "Cleric": "clr_cap_providence",
    "Ranger": "rng_cap_skyfall_volley",
    "Paladin": "pal_cap_heavens_sword",
    "Warlock": "lck_cap_dark_apotheosis",
    "Barbarian": "bar_cap_wrath_incarnate",
}
all_ids = []
for cls, wave in WAVE2.items():
    skills = class_skills[cls]
    assert len(skills) == 10, (cls, len(skills))
    for sid, lvl in wave.items():
        assert sid in skills, (cls, sid)
        assert skills[sid]["unlock_level"] == lvl, (sid, skills[sid]["unlock_level"])
    cap = CAPSTONES[cls]
    assert cap in skills, (cls, cap)
    assert skills[cap]["unlock_level"] == 40, (cap, skills[cap]["unlock_level"])
    assert skills[cap]["cooldown"] == 9, (cap, skills[cap]["cooldown"])
    assert skills[cap].get("capstone") is True, cap
    all_ids.extend(skills)
assert len(all_ids) == len(set(all_ids)), "duplicate class skill ids"
learnable_ids = {sid for cat in data.get("learnable_skills", {}).values() for sid in cat}
clash = set()
for wave in WAVE2.values():
    clash |= set(wave) & learnable_ids
assert not clash, f"wave-2 ids clash with learnable ids: {clash}"
print("OK: YAML — 10 actives/class, wave-2 ids + levels correct, capstones at 40/CD 9, no id clashes")


def make_enemy(hp=D, con_mod=0):
    return {"name": "Dummy", "hp": hp, "max_hp": hp, "con_mod": con_mod,
            "active_debuffs": [], "active_buffs": [],
            "elemental_res": {}, "elemental_dmg": {}}


def make_player(cls="Warrior", level=32):
    p = {"name": "Hero", "class": cls, "level": level,
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
    return {"name": "Luna", "is_ally": True, "race": "Human", "level": 32,
            "current_hp": 100, "max_hp": 200,
            "attributes": {a: 10 for a in ATTRS},
            "equipped": {"weapon": None, "armor": None, "accessory1": None, "accessory2": None},
            "active_buffs": [], "active_debuffs": [],
            "elemental_dmg": {}, "elemental_res": {},
            "skill_cooldowns": {}, "skill_mastery": {},
            "innate_skills": [], "learned_skills": []}


def has_buff(actor, btype):
    return [b for b in actor["active_buffs"] if b.get("type") == btype]


def has_debuff(actor, dtype):
    return [d for d in actor["active_debuffs"] if d.get("type") == dtype]


# ── 2. single-target fallback: Titan's Swing ignores armor ──
p, e = make_player("Warrior"), make_enemy(con_mod=100)
msg, _ = psk.execute_skill(p, "war_titan_swing", [e], 10, 10, 10, 10, 10, 10)
dmg = D - e["hp"]
assert dmg == 39, dmg  # 24 + 10 STR + 5 LRN//2 = 39, armor ignored
print("OK: Titan's Swing — armor ignored (39 damage through 100 armor)")

# ── 3. Reckless Charge: damage + self vulnerability ──
p, e = make_player("Warrior"), make_enemy()
msg, _ = psk.execute_skill(p, "war_reckless_charge", [e], 10, 10, 10, 10, 10, 10)
assert has_debuff(p, "vulnerable"), p["active_debuffs"]
assert has_debuff(p, "vulnerable")[0]["value"] == 0.10
assert "leave yourself open" in msg.lower(), msg
print("OK: Reckless Charge — self vulnerable 10% applied")

# ── 4. Glacial Prison: stun (RNG forced) ──
p, e = make_player("Mage"), make_enemy()
msg, _ = psk.execute_skill(p, "mage_glacial_prison", [e], 10, 10, 10, 10, 10, 10)
assert e.get("stunned"), msg
print("OK: Glacial Prison — stun applied")

# ── 5. Caltrops: AoE slow + bleed ──
p, e1, e2 = make_player("Rogue"), make_enemy(), make_enemy()
msg, _ = psk.execute_skill(p, "rog_caltrops", [e1, e2], 10, 10, 10, 10, 10, 10)
for e in (e1, e2):
    assert e.get("slowed") or any(d.get("type") == "slow" for d in e["active_debuffs"]), e
    assert has_debuff(e, "bleed"), e["active_debuffs"]
    assert has_debuff(e, "bleed")[0]["damage"] == 4
print("OK: Caltrops — AoE slowed + bleeding (4/turn)")

# ── 6. Grasp of the Void: fallback slow + bleed ──
p, e = make_player("Warlock"), make_enemy()
msg, _ = psk.execute_skill(p, "lck_grasp_void", [e], 10, 10, 10, 10, 10, 10)
assert e.get("slowed") or any(d.get("type") == "slow" for d in e["active_debuffs"])
assert has_debuff(e, "bleed")
print("OK: Grasp of the Void — slow + bleed via generic fallback")

# ── 7. Nightshade: poison ──
p, e = make_player("Rogue"), make_enemy()
msg, _ = psk.execute_skill(p, "rog_nightshade", [e], 10, 10, 10, 10, 10, 10)
assert has_debuff(e, "poison"), e["active_debuffs"]
print("OK: Nightshade — poison applied")

# ── 8. Dawnbreaker: blind ──
p, e = make_player("Paladin"), make_enemy()
msg, _ = psk.execute_skill(p, "pal_dawnbreaker", [e], 10, 10, 10, 10, 10, 10)
assert e.get("blinded") and has_debuff(e, "blind"), e
print("OK: Dawnbreaker — blinded")

# ── 9. Censure: weaken via fallback ──
p, e = make_player("Paladin"), make_enemy()
msg, _ = psk.execute_skill(p, "pal_censure", [e], 10, 10, 10, 10, 10, 10)
assert has_debuff(e, "weaken"), e["active_debuffs"]
print("OK: Censure — weakened")

# ── 10. Skullbreaker: stun (RNG forced) ──
p, e = make_player("Barbarian"), make_enemy()
msg, _ = psk.execute_skill(p, "bar_skullbreaker", [e], 10, 10, 10, 10, 10, 10)
assert e.get("stunned")
print("OK: Skullbreaker — stunned")

# ── 11. Blessed Aegis: barrier on ally (caster-sized) ──
p, ally = make_player("Cleric"), make_ally()
al = [ally]
_CHOICE["v"] = "2"  # pick the ally (player is option 1)
msg, _ = psk.execute_skill(p, "clr_blessed_aegis", [], 10, 10, 10, 10, 10, 10, allies=al)
_CHOICE["v"] = "1"
bar = has_buff(ally, "barrier")
assert bar and bar[0]["value"] > 0, ally["active_buffs"]
print(f"OK: Blessed Aegis — barrier {bar[0]['value']} on ally")

# ── 12. Prayer of Mending: regen_pct HoT on ally ──
p, ally = make_player("Cleric"), make_ally()
al = [ally]
_CHOICE["v"] = "2"
msg, _ = psk.execute_skill(p, "clr_prayer_mending", [], 10, 10, 10, 10, 10, 10, allies=al)
_CHOICE["v"] = "1"
regen = has_buff(ally, "regen_pct")
assert regen and abs(regen[0]["value"] - 0.06) < 1e-9, ally["active_buffs"]
print("OK: Prayer of Mending — 6% max-HP regen_pct on ally")

# ── 13. War Banner: party Strength + regen ──
# base 2 + 1 baseline + 31 * 0.15 = 7.65 -> 8 at Lv32
p, ally = make_player("Warrior"), make_ally()
al = [ally]
msg, _ = psk.execute_skill(p, "war_banner", [], 10, 10, 10, 10, 10, 10, allies=al)
for member in (p, ally):
    strs = [b for b in member["active_buffs"] if b.get("stat") == "Strength"]
    assert strs and strs[0]["value"] == 8, member["active_buffs"]
    assert has_buff(member, "regen_pct"), member["active_buffs"]
print("OK: War Banner — party STR +8 and regen applied")

# ── 14. Blessing of the Faithful: heal + defense buff ──
p, ally = make_player("Paladin"), make_ally()
al = [ally]
_CHOICE["v"] = "2"
msg, _ = psk.execute_skill(p, "pal_blessing", [], 10, 10, 10, 10, 10, 10, allies=al)
_CHOICE["v"] = "1"
assert ally["current_hp"] > 100, ally["current_hp"]
assert has_buff(ally, "defense"), ally["active_buffs"]
print("OK: Blessing — healed + defense buff on ally")

# ── 15. Buffs: crit / crit_damage / evasion / elemental / mark ──
p, e = make_player("Rogue"), make_enemy()
psk.execute_skill(p, "rog_perfect_opening", [], 10, 10, 10, 10, 10, 10)
assert has_buff(p, "crit_chance") and has_buff(p, "crit_damage")

p2, e2 = make_player("Ranger"), make_enemy()
psk.execute_skill(p2, "rng_camouflage", [], 10, 10, 10, 10, 10, 10)
assert has_buff(p2, "evasion") and has_buff(p2, "crit_chance")

p3, _ = make_player("Mage"), None
psk.execute_skill(p3, "mage_elemental_focus", [], 10, 10, 10, 10, 10, 10)
assert has_buff(p3, "elemental_dmg")

p4, _ = make_player("Ranger"), None
psk.execute_skill(p4, "rng_hawks_eye", [], 10, 10, 10, 10, 10, 10)
assert has_buff(p4, "mark_damage_bonus")
print("OK: Perfect Opening / Camouflage / Elemental Focus / Hawk's Eye buffs applied")

# ── 16. crit_damage buff math (resolve_critical_chance overflow) ──
p = make_player("Rogue")
chance0, over0 = pstats.resolve_critical_chance(p)
assert over0 == 0.0
p["active_buffs"].append({"type": "crit_damage", "value": 0.25, "remaining": 3})
chance1, over1 = pstats.resolve_critical_chance(p)
assert abs(over1 - 0.25) < 1e-9, over1
print("OK: crit_damage buff adds +0.25 to the crit multiplier bonus")

# ── 17. elemental_dmg buff math ──
att = {"name": "A", "elemental_dmg": {"fire": 1.0}, "active_buffs": []}
tgt = {"name": "T", "elemental_res": {"fire": 1.0}, "active_debuffs": [], "active_buffs": []}
base = pel.calculate_elemental_damage(100, att, tgt, "fire")
att["active_buffs"].append({"type": "elemental_dmg", "value": 0.15, "remaining": 3})
boosted = pel.calculate_elemental_damage(100, att, tgt, "fire")
# int() truncation is intentional (mirrors the EH flask pattern) — allow 114/115
assert base == 100 and boosted in (114, 115), (base, boosted)
print(f"OK: elemental_dmg buff +15% (100 -> {boosted})")

# ── 18. Hawk's Eye boosts damage vs a marked target ──
for buffed in (False, True):
    p, e = make_player("Ranger"), make_enemy()
    e["hunters_mark"] = True
    e["hunters_mark_bonus"] = 0.50
    if buffed:
        p["active_buffs"].append({"type": "mark_damage_bonus", "value": 0.25, "remaining": 3})
    psk.execute_skill(p, "rng_pierce", [e], 0, 0, 10, 10, 0, 0)
    dealt = D - e["hp"]
    if not buffed:
        plain = dealt
    else:
        marked = dealt
assert marked > plain, (plain, marked)
print(f"OK: Hawk's Eye mark bonus ({plain} -> {marked} vs marked target)")

# ── 19. Blood Pact: HP cost + stat buffs ──
p = make_player("Warlock")
hp0 = p["current_hp"]
psk.execute_skill(p, "lck_blood_pact", [], 10, 10, 10, 10, 10, 10)
assert p["current_hp"] < hp0, (hp0, p["current_hp"])
stats_buffed = {b.get("stat") for b in p["active_buffs"]}
assert {"Learning", "Charisma"} <= stats_buffed, stats_buffed
print("OK: Blood Pact — HP paid, Learning/Charisma buffs applied")

# ── 20. Siphon Soul: drain heals for damage dealt ──
p, e = make_player("Warlock"), make_enemy()
p["current_hp"] = 10
p["attributes"]["Wisdom"] = 0  # keep the wisdom heal bonus out of the math
msg, _ = psk.execute_skill(p, "lck_siphon_soul", [e], 0, 0, 0, 10, 0, 0)
dealt = D - e["hp"]
healed = p["current_hp"] - 10
assert dealt == 35, dealt  # 20 base + 10 LER + 5 LRN//2
assert healed == dealt, (dealt, healed)
print(f"OK: Siphon Soul — drained {dealt}, healed {healed}")

# ── 21. Battle Trance + Reckless Abandon ──
p = make_player("Barbarian")
psk.execute_skill(p, "bar_battle_trance", [], 10, 10, 10, 10, 10, 10)
assert any(b.get("stat") == "Strength" for b in p["active_buffs"]) and has_buff(p, "crit_chance")
p2 = make_player("Barbarian")
psk.execute_skill(p2, "bar_reckless_abandon", [], 10, 10, 10, 10, 10, 10)
assert has_buff(p2, "crit_damage") and has_debuff(p2, "vulnerable")
print("OK: Battle Trance / Reckless Abandon buffs applied")

# ── 22. Mastery XP accrues for a new skill ──
p, e = make_player("Warrior"), make_enemy()
psk.execute_skill(p, "war_titan_swing", [e], 10, 10, 10, 10, 10, 10)
assert p["skill_mastery"].get("war_titan_swing") == 1, p["skill_mastery"]
print("OK: mastery XP accrues for wave-2 skills")

# ═══════════════════════════════════════════════════════════════════════════
# PHASE 2 — Capstones & Battle Loadout
# ═══════════════════════════════════════════════════════════════════════════

# ── 23. Loadout: legacy (no key, under cap) = everything equipped ──
p = make_player("Warrior", level=15)
p["skills"] = []
p.pop("skill_loadout", None)
names = psk.unlock_skills_for_level(p)
assert len(p["skills"]) == 6 and p.get("skill_loadout") is None, (p["skills"], p.get("skill_loadout"))
assert len(psk.get_equipped_skill_ids(p)) == 6
print("OK: legacy saves without a loadout key equip everything while under the cap")

# ── 24. Loadout materialises when the pool outgrows the cap ──
p = make_player("Warrior", level=40)
p["skills"] = []
p.pop("skill_loadout", None)
names = psk.unlock_skills_for_level(p)
assert len(p["skills"]) == 10
assert isinstance(p.get("skill_loadout"), list) and len(p["skill_loadout"]) == 9
assert CAPSTONES["Warrior"] not in p["skill_loadout"]
assert any("loadout full" in n for n in names), names
print("OK: pool > 9 materialises the loadout; the capstone queues with a 'loadout full' notice")

# ── 25. Loadout filters the combat menu ──
p = make_player("Warrior", level=40)
all_war = [sid for sid in class_skills["Warrior"]]
p["skills"] = list(all_war)
p["skill_loadout"] = all_war[:9]
avail = [sid for sid, _ in psk.get_available_skills(p)]
assert "war_cap_onslaught" not in avail and len(avail) == 9, avail
assert psk.is_skill_available(p, "war_cap_onslaught") is False
p["skill_loadout"] = all_war[1:]  # swap: drop the first skill, bring the capstone
avail = [sid for sid, _ in psk.get_available_skills(p)]
assert "war_cap_onslaught" in avail and all_war[0] not in avail, avail
print("OK: loadout filters get_available_skills + is_skill_available; swaps work")

# ── 26. New unlocks auto-equip while under the cap ──
p = make_player("Mage", level=19)
p["skills"] = ["mage_fireball", "mage_frostnova", "mage_arcane", "mage_meteor", "mage_timewarp", "mage_overload"]
p["skill_loadout"] = list(p["skills"])
p["level"] = 20
psk.unlock_skills_for_level(p)
assert "mage_elemental_focus" in p["skill_loadout"], p["skill_loadout"]
assert len(p["skill_loadout"]) == 7
print("OK: new unlock auto-joins the loadout while under the cap")

# ── 27. Onslaught: five blows, the final one executes below 30% ──
p, e = make_player("Warrior", level=40), make_enemy(hp=3100)
e["max_hp"] = 10000
msg, _ = psk.execute_skill(p, "war_cap_onslaught", [e], 10, 10, 10, 10, 10, 10)
assert e["hp"] == 0, e["hp"]
assert "executes" in msg.lower(), msg
print("OK: Onslaught — final blow executed a target at 29.8% HP")

# ── 28. Death's Embrace: execute + cooldown refund on kill ──
p, e = make_player("Rogue", level=40), make_enemy(hp=100)
e["max_hp"] = 1000  # 10% -> execute
msg, _ = psk.execute_skill(p, "rog_cap_deaths_embrace", [e], 10, 10, 10, 10, 10, 10)
assert e["hp"] == 0
assert p.get("refund_cooldown_skill") == "rog_cap_deaths_embrace"
psk.set_skill_cooldown(p, "rog_cap_deaths_embrace")
assert "rog_cap_deaths_embrace" not in p.get("skill_cooldowns", {})
p2, e2 = make_player("Rogue", level=40), make_enemy()
psk.execute_skill(p2, "rog_cap_deaths_embrace", [e2], 10, 10, 10, 10, 10, 10)
assert "refund_cooldown_skill" not in p2
psk.set_skill_cooldown(p2, "rog_cap_deaths_embrace")
assert p2["skill_cooldowns"].get("rog_cap_deaths_embrace") == 9
print("OK: Death's Embrace — execute refunds the cooldown; non-kills still pay CD 9")

# ── 29. Providence: party heal + shielded revive ──
p, ally = make_player("Cleric", level=40), make_ally()
ally["current_hp"] = 0
msg, _ = psk.execute_skill(p, "clr_cap_providence", [], 10, 10, 10, 10, 10, 10, allies=[ally])
assert ally["current_hp"] > 0 and ally.get("defeated") is False, ally
assert has_buff(ally, "barrier"), ally["active_buffs"]
print("OK: Providence — revived a fallen ally with a barrier")

# ── 30. Skyfall Volley: two waves on every enemy + slow ──
p, e1, e2 = make_player("Ranger", level=40), make_enemy(), make_enemy()
msg, _ = psk.execute_skill(p, "rng_cap_skyfall_volley", [e1, e2], 0, 0, 10, 10, 0, 0)
assert D - e1["hp"] == 56 and D - e2["hp"] == 56, (D - e1["hp"], D - e2["hp"])
for e in (e1, e2):
    assert e.get("slowed") or any(d.get("type") == "slow" for d in e["active_debuffs"]), e
print("OK: Skyfall Volley — 2x28 to every enemy, all slowed")

# ── 31. Heaven's Sword: heavy single damage + party heal ──
p, ally, e = make_player("Paladin", level=40), make_ally(), make_enemy()
ally["current_hp"] = 50
p["current_hp"] = 20
msg, _ = psk.execute_skill(p, "pal_cap_heavens_sword", [e], 10, 0, 0, 10, 0, 0, allies=[ally])
assert D - e["hp"] == 55, D - e["hp"]  # 40 + 10 STR + 5 LRN//2
assert ally["current_hp"] == 79, ally["current_hp"]  # +29 ((55//2) + 2 WIS milestone)
print("OK: Heaven's Sword — 55 damage, party healed +29")

# ── 32. Dark Apotheosis: AoE drain + self empower ──
p, e = make_player("Warlock", level=40), make_enemy()
p["current_hp"] = 1
msg, _ = psk.execute_skill(p, "lck_cap_dark_apotheosis", [e], 0, 0, 0, 10, 0, 0)
dealt = D - e["hp"]
assert dealt == 35, dealt  # 20 + 10 LER + 5 LRN//2
assert p["current_hp"] == 36, p["current_hp"]  # drank the full 35
assert any(b.get("stat") == "Learning" for b in p["active_buffs"])
assert any(b.get("stat") == "Charisma" for b in p["active_buffs"])
print("OK: Dark Apotheosis — drained 35 HP and empowered LER/CHA")

# ── 33. Wrath Incarnate: AoE crush + stun + self heal ──
p, e = make_player("Barbarian", level=40), make_enemy()
p["current_hp"] = 10
msg, _ = psk.execute_skill(p, "bar_cap_wrath_incarnate", [e], 10, 0, 0, 0, 0, 0)
assert e.get("stunned"), msg
assert p["current_hp"] == 21, p["current_hp"]  # +25% of 45 = 11
print("OK: Wrath Incarnate — stunned + healed 11 (25% max HP)")

# ── 34. Cataclysm: AoE + Inferno burn ──
p, e1, e2 = make_player("Mage", level=40), make_enemy(), make_enemy()
msg, _ = psk.execute_skill(p, "mage_cap_cataclysm", [e1, e2], 0, 0, 0, 10, 0, 0)
assert D - e1["hp"] == 45 and D - e2["hp"] == 45, (D - e1["hp"], D - e2["hp"])
for e in (e1, e2):
    assert has_debuff(e, "burn"), e["active_debuffs"]
print("OK: Cataclysm — 45 to all + burn")

# ── 35. Support skills now earn mastery XP (wrapper) ──
p = make_player("Warrior", level=40)
psk.execute_skill(p, "war_banner", [], 10, 10, 10, 10, 10, 10, allies=[])
assert p["skill_mastery"].get("war_banner") == 1, p["skill_mastery"]
print("OK: effect-only skills accrue mastery XP")

# ═══════════════════════════════════════════════════════════════════════════
# PHASE 3 — Professions
# ═══════════════════════════════════════════════════════════════════════════

# ── 36. Profession YAML structure ──
profs = data.get("professions", {})
assert len(profs) == 8, len(profs)
prof_ids = []
for cls, branches in profs.items():
    assert len(branches) == 2, cls
    for pid, pdata in branches.items():
        assert len(pdata.get("skills", {})) == 3, (cls, pid)
        assert sorted(s.get("unlock_level") for s in pdata["skills"].values()) == [40, 50, 60], (cls, pid)
        assert pdata.get("passive", {}).get("effects"), (cls, pid)
        prof_ids.extend(pdata["skills"])
assert len(prof_ids) == len(set(prof_ids)) == 48
print("OK: professions YAML — 8 classes x 2 branches x 3 skills at 40/50/60 + upgraded passives")

# ── 37. Model: merge + lockout + ceremony eligibility ──
p = make_player("Warrior", level=60)
p["skills"] = []
p.pop("skill_loadout", None)
psk.unlock_skills_for_level(p)
assert len(psk.get_class_skill_map(p)) == 10
assert psk.can_choose_profession(p) is True
assert psk.get_class_capstone_id("Warrior") == "war_cap_onslaught"
p["profession"] = "warlord"
merged = psk.get_class_skill_map(p)
assert "war_wl_iron_command" in merged and "war_sent_guardian_stance" not in merged
psk.unlock_skills_for_level(p)
assert {"war_wl_iron_command", "war_wl_decimation", "war_wl_reign"} <= set(p["skills"])
assert "war_sent_guardian_stance" not in p["skills"]
assert psk.can_choose_profession(p) is False
print("OK: profession merge + lockout (unchosen branch never enters the map or skill list)")

# ── 38. Upgraded passives: stats / DR / crit / evasion / elemental / low-HP ──
p = make_player("Warrior", level=60); p["profession"] = "warlord"
assert len(psk.get_player_passive_effects(p)) == 2
assert pstats.get_effective_attribute(p, "Strength") == 2   # 0 base + 2
assert pstats.get_effective_attribute(p, "Constitution") == 12  # 10 base + 2
p = make_player("Warrior", level=60); p["profession"] = "sentinel"
assert psk.apply_passive_to_damage_taken(p, 100) == 90
p = make_player("Barbarian", level=60); p["profession"] = "juggernaut"
assert psk.apply_passive_to_damage_taken(p, 100) == 80
assert pstats.get_effective_attribute(p, "Constitution") == 12
p = make_player("Rogue", level=60); p["profession"] = "assassin"
plain = make_player("Rogue", level=60)
assert abs(pstats.get_raw_critical_chance(p) - pstats.get_raw_critical_chance(plain) - 0.08) < 1e-9
p = make_player("Rogue", level=60); p["profession"] = "shadowdancer"
attacker = make_player("Rogue", level=60)
assert abs(pstats.get_dodge_chance(p, attacker) - pstats.get_dodge_chance(plain, attacker) - 0.08) < 1e-9
p = make_player("Mage", level=60); p["profession"] = "evoker"
p["elemental_dmg"] = {"fire": 1.0}
tgt = {"name": "T", "elemental_res": {"fire": 1.0}, "active_debuffs": [], "active_buffs": []}
assert pel.calculate_elemental_damage(100, p, tgt, "fire") in (109, 110)
p2 = make_player("Mage", level=60); p2["elemental_dmg"] = {"fire": 1.0}
assert pel.calculate_elemental_damage(100, p2, tgt, "fire") == 100
p = make_player("Barbarian", level=60); p["profession"] = "berserker"
p["current_hp"] = 45
assert psk.get_player_passive_low_hp_mult(p) == 1.0
p["current_hp"] = 20
assert abs(psk.get_player_passive_low_hp_mult(p) - 1.10) < 1e-9
print("OK: upgraded passives — stats, DR, crit, evasion, elemental, low-HP all live")

# ── 39. Battle-start passives (Chronomancer start-CD, Hierophant regen) ──
p = make_player("Mage", level=60); p["profession"] = "chronomancer"
p["skill_cooldowns"] = {"mage_fireball": 3}
psk.apply_profession_battle_start(p)
assert p["skill_cooldowns"].get("mage_fireball") == 2
p = make_player("Cleric", level=60); p["profession"] = "hierophant"
psk.apply_profession_battle_start(p)
assert any(b.get("type") == "regen_pct" for b in p["active_buffs"])
print("OK: battle-start passives — start-CD and regen apply")

# ── 40. Warlord: Iron Command + Warlord's Reign ──
p, ally = make_player("Warrior", level=60), make_ally()
p["profession"] = "warlord"
psk.execute_skill(p, "war_wl_iron_command", [], 10, 10, 10, 10, 10, 10, allies=[ally])
for m in (p, ally):
    assert any(b.get("type") == "damage_boost" for b in m["active_buffs"]), m
    assert any(b.get("type") == "fear_immunity" for b in m["active_buffs"]), m
e1, e2 = make_enemy(), make_enemy()
psk.execute_skill(p, "war_wl_reign", [e1, e2], 10, 10, 10, 10, 10, 10)
assert e1.get("hunters_mark") and e2.get("hunters_mark")
print("OK: Iron Command + Warlord's Reign")

# ── 41. Sentinel: Guardian Stance / Living Fortress / Unbreakable ──
p, ally = make_player("Warrior", level=60), make_ally()
p["profession"] = "sentinel"
psk.execute_skill(p, "war_sent_guardian_stance", [], 10, 10, 10, 10, 10, 10)
assert any(b.get("type") == "reflection" for b in p["active_buffs"])
psk.execute_skill(p, "war_sent_living_fortress", [], 10, 10, 10, 10, 10, 10, allies=[ally])
assert any(b.get("type") == "defense" for b in ally["active_buffs"])
psk.execute_skill(p, "war_sent_unbreakable", [], 10, 10, 10, 10, 10, 10)
assert any(b.get("type") == "death_ward" for b in p["active_buffs"])
print("OK: Sentinel — reflection, party DR, death ward")

# ── 42. Chronomancer: Time Stop + Temporal Acceleration + Rewind ──
p, ally, e1, e2 = make_player("Mage", level=60), make_ally(), make_enemy(), make_enemy()
p["profession"] = "chronomancer"
psk.execute_skill(p, "mage_chr_time_stop", [e1, e2], 10, 10, 10, 10, 10, 10)
assert e1.get("stunned") and e2.get("stunned")
p["skill_cooldowns"] = {"mage_fireball": 5}
ally["skill_cooldowns"] = {"some_skill": 4}
psk.execute_skill(p, "mage_chr_temporal_acceleration", [], 10, 10, 10, 10, 10, 10, allies=[ally])
assert p["skill_cooldowns"]["mage_fireball"] == 3 and ally["skill_cooldowns"]["some_skill"] == 2
p["current_hp"] = 10
p["skill_cooldowns"] = {"a": 6, "b": 3}
psk.execute_skill(p, "mage_chr_rewind", [], 10, 10, 10, 10, 10, 10)
assert p["current_hp"] == 28, p["current_hp"]        # +18 (40% of 45)
assert p["skill_cooldowns"]["a"] == 2 and p["skill_cooldowns"]["b"] == 0
print("OK: Chronomancer — Time Stop, party cooldown unwind, Rewind")

# ── 43. Assassin: Mark for Death + Mortal Blow + Thousand Cuts ──
p, e = make_player("Rogue", level=60), make_enemy()
p["profession"] = "assassin"
psk.execute_skill(p, "rog_asm_mark_for_death", [e], 10, 10, 10, 10, 10, 10)
assert any(d.get("type") == "damage_taken_up" for d in e["active_debuffs"])
e2 = make_enemy(hp=100); e2["max_hp"] = 1000
psk.execute_skill(p, "rog_asm_mortal_blow", [e2], 0, 0, 10, 10, 0, 0)
assert e2["hp"] == 0
e3 = make_enemy()
psk.execute_skill(p, "rog_asm_thousand_cuts", [e3], 0, 0, 10, 10, 0, 0)
assert D - e3["hp"] == 100, D - e3["hp"]  # (10 + 10 + 5) x 4
print("OK: Assassin — mark, execute, four cuts")

# ── 44. Shadowdancer + Hierophant ──
p, ally = make_player("Rogue", level=60), make_ally()
p["profession"] = "shadowdancer"
psk.execute_skill(p, "rog_shd_veil_of_shadows", [], 10, 10, 10, 10, 10, 10, allies=[ally])
assert any(b.get("type") == "evasion" for b in ally["active_buffs"])
p, ally = make_player("Cleric", level=60), make_ally()
p["profession"] = "hierophant"
p["active_debuffs"] = [{"type": "poison", "damage": 5, "remaining": 3}]
psk.execute_skill(p, "clr_hie_sanctuary", [], 10, 10, 10, 10, 10, 10, allies=[ally])
assert any(b.get("type") == "regen_pct" for b in p["active_buffs"])
assert not p["active_debuffs"]
ally["current_hp"] = 0
_CHOICE["v"] = "2"
psk.execute_skill(p, "clr_hie_greater_resurrection", [], 10, 10, 10, 10, 10, 10, allies=[ally])
_CHOICE["v"] = "1"
assert ally["current_hp"] == 150 and ally.get("defeated") is False
assert any(b.get("type") == "barrier" for b in ally["active_buffs"])
print("OK: Shadowdancer veil + Hierophant sanctuary/revive")

# ── 45. Inquisitor / Crusader / Templar ──
p, e = make_player("Cleric", level=60), make_enemy()
p["profession"] = "inquisitor"
psk.execute_skill(p, "clr_inq_verdict", [e], 0, 0, 0, 10, 0, 0)
assert any(d.get("type") == "damage_taken_up" for d in e["active_debuffs"])
p, e = make_player("Paladin", level=60), make_enemy()
p["profession"] = "crusader"
psk.execute_skill(p, "pal_cru_condemn", [e], 10, 0, 0, 0, 0, 0)
assert e.get("stunned") and any(d.get("type") == "damage_taken_up" for d in e["active_debuffs"])
p, ally = make_player("Paladin", level=60), make_ally()
p["profession"] = "templar"
psk.execute_skill(p, "pal_tmp_aegis", [], 10, 10, 10, 10, 10, 10, allies=[ally])
assert any(b.get("type") == "barrier" for b in p["active_buffs"])
assert any(b.get("type") == "barrier" for b in ally["active_buffs"])
print("OK: Inquisitor brand + Crusader condemn + Templar aegis")

# ── 46. Warlock / Barbarian / generic profession skills ──
p, e1, e2 = make_player("Warlock", level=60), make_enemy(), make_enemy()
p["profession"] = "infernalist"
psk.execute_skill(p, "lck_inf_hellfire", [e1, e2], 0, 0, 0, 10, 0, 0)
for e in (e1, e2):
    assert any(d.get("type") == "burn" for d in e["active_debuffs"])
p = make_player("Barbarian", level=60); p["profession"] = "juggernaut"
p["current_hp"] = 10
e3 = make_enemy()
psk.execute_skill(p, "bar_jug_mountain_breaker", [e3], 10, 0, 0, 0, 0, 0)
assert p["current_hp"] == 16, p["current_hp"]  # +15% of 45
p = make_player("Barbarian", level=60); p["profession"] = "berserker"
psk.execute_skill(p, "bar_bsk_bloodrage", [], 10, 10, 10, 10, 10, 10)
assert p["bloodlust_turns"] >= 3
psk.execute_skill(p, "bar_bsk_undying_rage", [], 10, 10, 10, 10, 10, 10)
assert any(b.get("type") == "death_ward" for b in p["active_buffs"])
p = make_player("Barbarian", level=60); p["profession"] = "juggernaut"
p["active_debuffs"] = [{"type": "poison", "damage": 5, "remaining": 3}]
psk.execute_skill(p, "bar_jug_unyielding", [], 10, 10, 10, 10, 10, 10)
assert not p["active_debuffs"]
print("OK: Hellfire / Mountain Breaker / Bloodrage / Undying Rage / Unyielding")

print("\nALL PHASE 1 + PHASE 2 + PHASE 3 CHECKS PASSED")
