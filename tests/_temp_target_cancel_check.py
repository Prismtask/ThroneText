# Temp verification (2026-10-04): canceling target selection must NOT consume the
# actor's turn or put skills on cooldown. Covers: player skill, player attack,
# ally skill, brush exhibit, and gloves workshop cancel paths.
import sys
sys.path.insert(0, "c:/Code/Pandemonium")

import combat.skills as psk
import combat.player_actions as pact
import combat.ally as amod
import combat.ally_skills as ask
import combat.combat_ui as cui
import combat.weapon.palette_brush as pb
import combat.weapon.black_silence_gloves as bsg
from combat.helpers import ACTION_CANCELLED_MSG

# ── Silence console output ──
for mod in (psk, pact, amod, ask, pb, bsg, cui):
    if hasattr(mod, "c_print"):
        mod.c_print = lambda *a, **k: ""
cui.print_combat_hud = lambda *a, **k: None
pact.print_combat_hud = lambda *a, **k: None

FAILS = []


def check(label, cond):
    print(("PASS" if cond else "FAIL"), "-", label)
    if not cond:
        FAILS.append(label)


ATTRS = ("Strength", "Constitution", "Dexterity", "Wisdom", "Learning", "Charisma")


def make_enemy(name):
    return {"name": name, "hp": 500, "max_hp": 500, "con_mod": 0,
            "active_debuffs": [], "active_buffs": [],
            "elemental_res": {}, "elemental_dmg": {}}


def make_player(cls):
    from resources.skill_loader import CLASS_SKILLS
    p = {"name": "Hero", "class": cls, "level": 40,
         "current_hp": 500, "passive_unlocked": True,
         "attributes": {a: 10 for a in ATTRS},
         "level_hp_bonus": 0,
         "equipped": {"weapon": None, "armor": None, "accessory1": None, "accessory2": None},
         "active_buffs": [], "active_debuffs": [],
         "elemental_dmg": {}, "elemental_res": {},
         "inventory": [], "allies": [],
         "skills": list(CLASS_SKILLS.get(cls, {}).keys()),
         "skill_mastery": {}, "skill_cooldowns": {}}
    return p


def make_ally():
    return {"name": "Luna", "is_ally": True, "race": "Human", "level": 40,
            "current_hp": 300, "max_hp": 300,
            "attributes": {a: 10 for a in ATTRS},
            "equipped": {"weapon": None, "armor": None, "accessory1": None, "accessory2": None},
            "active_buffs": [], "active_debuffs": [],
            "elemental_dmg": {}, "elemental_res": {},
            "skill_cooldowns": {}, "skill_mastery": {},
            "innate_skills": [], "learned_skills": [],
            "defending_this_turn": False}


# ── 1. Player skill: cancel target selection → retry, no cooldown ──
from resources.skill_loader import CLASS_SKILLS
found = None
for cls in CLASS_SKILLS:
    p = make_player(cls)
    for idx, (sid, sdef) in enumerate(psk.get_available_skills(p)):
        if sdef.get("target", "enemy") == "enemy":
            found = (cls, p, sid, idx)
            break
    if found:
        break

check("found a player enemy-target skill", found is not None)
if found:
    cls, p, sid, idx = found
    e1, e2 = make_enemy("A"), make_enemy("B")
    enemies = [e1, e2]
    pact.c_input = lambda *a, **k: ""     # "Press Enter to use it..."
    psk.c_input = lambda *a, **k: "0"     # "Select target number:" → cancel
    result, _ = pact.handle_player_turn(p, enemies, 10, 10, 10, 10, 10, 10,
                                        _action_override=str(idx + 1))
    check(f"player skill cancel ({cls}/{sid}) → retry", result == "retry")
    check("player skill cancel → no cooldown set", sid not in p.get("skill_cooldowns", {}))
    check("player skill cancel → enemies untouched", e1["hp"] == 500 and e2["hp"] == 500)

    # ── 1b. Player skill: valid target still executes + sets cooldown ──
    p1b = make_player(cls)
    eA, eB = make_enemy("A2"), make_enemy("B2")
    pact.c_input = lambda *a, **k: ""     # "Press Enter to use it..."
    psk.c_input = lambda *a, **k: "1"     # first enemy
    result, _ = pact.handle_player_turn(p1b, [eA, eB], 10, 10, 10, 10, 10, 10,
                                        _action_override=str(idx + 1))
    check("player skill valid target → continue", result == "continue")
    check("player skill valid target → cooldown set",
          p1b.get("skill_cooldowns", {}).get(sid, 0) > 0)
    check("player skill valid target → enemy damaged", eA["hp"] < 500)

# ── 2. Player attack: cancel still retry (unchanged sanity) ──
p2 = make_player(list(CLASS_SKILLS.keys())[0])
e3, e4 = make_enemy("C"), make_enemy("D")
pact.c_input = lambda *a, **k: "0"
result, _ = pact.handle_player_turn(p2, [e3, e4], 10, 10, 10, 10, 10, 10,
                                    _action_override="a")
check("player attack cancel → retry", result == "retry")

# ── 3. Ally skill: cancel target selection → retry, no cooldown ──
ally_skill = None
for key, ids in ask.INNATE_SKILLS_MAP.items():
    for sid in ids:
        sdef = ask.get_innate_skill_def(sid)
        if sdef and sdef.get("target", "enemy") == "enemy":
            ally_skill = (sid, sdef)
            break
    if ally_skill:
        break

check("found an ally enemy-target skill", ally_skill is not None)
if ally_skill:
    a = make_ally()
    a["innate_skills"] = [ally_skill[0]]
    player = make_player(list(CLASS_SKILLS.keys())[0])
    e5, e6 = make_enemy("E"), make_enemy("F")
    usable = ask.get_usable_skills_in_combat(a)
    skill_idx = [s for s, _ in usable].index(ally_skill[0])
    seq = [str(skill_idx + 1), ""]  # choose skill, press Enter

    def seq_input(*args, **kwargs):
        return seq.pop(0) if seq else ""

    amod.c_input = seq_input
    ask.c_input = lambda *a, **k: "0"  # target cancel
    result = amod.handle_ally_turn(a, player, [e5, e6], 10, 10, 10, 10, 10, 10)
    check(f"ally skill cancel ({ally_skill[0]}) → retry", result == "retry")
    check("ally skill cancel → no cooldown set",
          ally_skill[0] not in a.get("skill_cooldowns", {}))

# ── 4. Brush exhibit: cancel → sentinel, exhibit not marked used ──
p3 = make_player(list(CLASS_SKILLS.keys())[0])
e7, e8 = make_enemy("G"), make_enemy("H")
pb.c_input = lambda *a, **k: "0"
msg, _ = pb.execute_chiaroscuro_exhibit(p3, [e7, e8], (10,) * 6, True)
check("chiaroscuro cancel → sentinel", msg == ACTION_CANCELLED_MSG)
check("chiaroscuro cancel → exhibit not used", "chiaroscuro" not in p3.get("brush_exhibits_used", set()))

# ── 5. Gloves workshop: cancel → sentinel, workshop not marked used ──
p4 = make_player(list(CLASS_SKILLS.keys())[0])
e9, e10 = make_enemy("I"), make_enemy("J")
bsg.c_input = lambda *a, **k: "0"
msg, _ = bsg.execute_workshop(p4, [e9, e10], 1, 10, 10, 10, 10, 10, 10)
check("workshop cancel → sentinel", msg == ACTION_CANCELLED_MSG)
check("workshop cancel → workshop not used", 1 not in p4.get("gloves_workshop_used", set()))

# ── 6. Capture target: entering 0 must NOT select the last monster girl ──
p5 = make_player(list(CLASS_SKILLS.keys())[0])
p5["inventory"] = [{"name": "Net", "capture_net": True, "count": 1}]
mg1, mg2 = make_enemy("MG1"), make_enemy("MG2")
mg1["monster_girl"] = mg2["monster_girl"] = True
pact.c_input = lambda *a, **k: "0"  # "Choice: " → cancel
enemies5 = [mg1, mg2]
result, _ = pact.handle_player_turn(p5, enemies5, 10, 10, 10, 10, 10, 10,
                                    _action_override="c")
check("capture target cancel → retry", result == "retry")
check("capture target cancel → net not consumed", len(p5["inventory"]) == 1)
check("capture target cancel → enemies untouched",
      enemies5 == [mg1, mg2] and mg1["hp"] == 500 and mg2["hp"] == 500)

print()
print("FAILURES:", FAILS if FAILS else "none")
sys.exit(1 if FAILS else 0)
