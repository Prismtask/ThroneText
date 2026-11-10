"""White Knight full-fight regression harness (2026-10-14).

Run A: deterministic ally-skill vs 100% skill-dodge — regression for the
       "cannot unpack non-iterable int object" crash (ally_skills._calc_dmg).
Run B: partial fight — the caller's enemies list must receive HP changes and
       the wrapped boss (GUI shared-state contract; never copy the list).
Run C: full fight with two allies — riposte / judgment burst / flurry paths,
       phase transitions, victory, no exception.
Run D: turn-order emission — the numbered list must match the GUI's compact
       "Turn Order:" line (the CombatScreen card parses only that format).

Run: python tests/_diag_white_knight_fight.py
"""
import sys
import traceback

sys.path.insert(0, "c:/Code/Pandemonium")

from combat.combat_io import set_io, reset_io
from combat.stats import enemy_stats
from resources.skill_loader import CLASS_SKILLS

ATTRS = ("Strength", "Constitution", "Dexterity", "Wisdom", "Learning", "Charisma")
FAILS = []


def check(label, cond):
    print(("PASS" if cond else "FAIL"), "-", label)
    if not cond:
        FAILS.append(label)


class ScriptedIO:
    def __init__(self, max_turns=45, attack="a"):
        self.log = []
        self.max_turns = max_turns
        self.turns = 0
        self.attack = attack

    def print(self, *a, **k):
        self.log.append(" ".join(str(x) for x in a))

    def input(self, prompt=""):
        if "Choose" in str(prompt):
            self.turns += 1
            if self.turns > self.max_turns:
                raise KeyboardInterrupt("turn cap reached")
            return self.attack
        return ""

    def clear(self):
        pass


def make_player(strength=80):
    p = {
        "name": "Hero", "class": list(CLASS_SKILLS.keys())[0], "level": 50,
        "current_hp": 20000, "passive_unlocked": True,
        "attributes": {a: 40 for a in ATTRS},
        "level_hp_bonus": 0,
        "equipped": {"weapon": None, "armor": None, "accessory1": None, "accessory2": None},
        "active_buffs": [], "active_debuffs": [],
        "elemental_dmg": {}, "elemental_res": {},
        "inventory": [], "allies": [],
        "skills": [], "skill_mastery": {}, "skill_cooldowns": {},
    }
    p["attributes"]["Strength"] = strength
    return p


def make_ally(name):
    return {
        "name": name, "is_ally": True, "race": "Human", "level": 50,
        "current_hp": 3000, "max_hp": 3000,
        "attributes": {a: 40 for a in ATTRS},
        "equipped": {"weapon": None, "armor": None, "accessory1": None, "accessory2": None},
        "active_buffs": [], "active_debuffs": [],
        "elemental_dmg": {}, "elemental_res": {},
        "skill_cooldowns": {}, "skill_mastery": {},
        "innate_skills": [], "learned_skills": [],
        "defending_this_turn": False,
    }


# ── Run A: deterministic crash path (ally skill vs 100% skill dodge) ─────────
import combat.ally_skills as ask

ally_skill = None
for key, ids in ask.INNATE_SKILLS_MAP.items():
    for sid in ids:
        sdef = ask.get_innate_skill_def(sid)
        if sdef and sdef.get("target", "enemy") == "enemy" and sdef.get("base_power"):
            ally_skill = (sid, sdef)
            break
    if ally_skill:
        break

check("found an ally damaging skill", ally_skill is not None)
if ally_skill:
    sid, sdef = ally_skill
    a = make_ally("Luna")
    a["innate_skills"] = [sid]
    player = make_player()
    target = {"name": "White Knight", "key": "white_knight", "hp": 500, "max_hp": 500,
              "con_mod": 0, "active_debuffs": [], "active_buffs": [],
              "elemental_res": {}, "elemental_dmg": {},
              "skill_dodge_chance": 1.0}
    io = ScriptedIO()
    set_io(io)
    crashed = None
    msg = victory = None
    try:
        msg, victory = ask.execute_ally_skill(a, player, sid, sdef, [target], [a])
    except Exception:
        crashed = traceback.format_exc()
    finally:
        reset_io()
    check(f"ally skill vs 100% skill dodge does not crash ({sid})", crashed is None)
    if crashed:
        print(crashed)
    check("skill dodge -> target unharmed", target["hp"] == 500)

# ── Run B: partial fight — external list must mutate (frozen HP fix) ─────────
from combat.white_knight import _PhaseLockedKnight, combat_white_knight

player_b = make_player(strength=250)
boss_b = enemy_stats("white_knight", player_b)
boss_b["max_hp"] = 4000
boss_b["hp"] = 4000
enemies_b = [boss_b]
io_b = ScriptedIO(max_turns=8)
set_io(io_b)
try:
    combat_white_knight(player_b, 40, enemies_b)
except KeyboardInterrupt:
    pass  # expected: we bail out after a few turns
finally:
    reset_io()
check("external list boss is the phase-locked wrapper",
      bool(enemies_b) and isinstance(enemies_b[0], _PhaseLockedKnight))
check("external list boss HP moved (GUI HUD would show damage)",
      bool(enemies_b) and enemies_b[0].get("hp", 4000) < 4000)
print(f"  [diag] Run B boss hp after {io_b.turns} turns: "
      f"{enemies_b[0]['hp'] if enemies_b else 'pruned'}/4000")

# ── Run C: full fight with two allies — all phases, no exception ─────────────
player_c = make_player(strength=90)
player_c["allies"] = [make_ally("Luna"), make_ally("Rin")]
player_c["expose_stacks"] = 6  # forces a Judgment Burst on the first enemy turn
boss_c = enemy_stats("white_knight", player_c)
boss_c["max_hp"] = 1400
boss_c["hp"] = 1400
enemies_c = [boss_c]
crashed_c = None
result_c = None
io_c = ScriptedIO(max_turns=90)
set_io(io_c)
try:
    result_c = combat_white_knight(player_c, 40, enemies_c)
except KeyboardInterrupt as e:
    crashed_c = f"turn cap: {e}"
except Exception:
    crashed_c = traceback.format_exc()
finally:
    reset_io()
check("full fight (2 allies) completes without exception", crashed_c is None)
if crashed_c:
    print(crashed_c)
check(f"full fight result is a valid value (got {result_c!r})",
      result_c in ("victory", "defeat", "flee", "timeout"))
joined = "\n".join(io_c.log)
check("riposte path exercised", "[RIPOSTE]" in joined)
check("judgment burst path exercised", "JUDGMENT BURST" in joined)
check("phase 2 reached", "Oathguard" in joined)
check("phase 3 reached", "last vigil" in joined.lower() or "Phase 3" in joined)
check("victory pruned the shared list", result_c != "victory" or len(enemies_c) == 0)
print(f"  [diag] flurry seen: {'Falling Star Flurry' in joined}")
print()

# ── Run D: turn-order emission contract (GUI card) ──────────────────────────
# The GUI parses only the compact "Turn Order: A -> B" line into the live
# card. The superboss loop used to print just a numbered list, so the card
# kept showing a stale speed preview (2026-10-14 bug report). Every numbered
# list must now be followed by a compact line with the same labels in order,
# before the round's first "[n/m] ...'s Turn:" step.
print("== Turn-order emission (GUI card contract) ==")
import re as _re

round_starts = [i for i, l in enumerate(io_c.log) if "Turn Order for this Round:" in l]
check("numbered turn order emitted each round", len(round_starts) >= 3)
same_order = True
before_steps = True
for i in round_starts:
    numbered, compact = [], None
    j = i + 1
    while j < len(io_c.log):
        l = io_c.log[j]
        m = _re.match(r"\s*\d+\.\s+(.+?)\s+\(Speed:", l)
        if m:
            numbered.append(m.group(1).strip())
        elif "Turn Order:" in l:
            compact = [p.strip() for p in l.split("Turn Order:", 1)[-1].split("->")]
            break
        elif _re.match(r"\s*\[\d+/\d+\]", l):
            before_steps = False
            break
        j += 1
    if compact is None or numbered != compact:
        same_order = False
check("numbered list matches the compact line (same labels, same order)", same_order)
check("compact line arrives before the first [n/m] action step", before_steps)

try:
    import types as _types

    from gui.screens.combat_screen import CombatScreen
    _fake = _types.SimpleNamespace(_actual_turn_order=None)
    _first_compact = next(l for l in io_c.log if "Turn Order:" in l)
    CombatScreen._on_turn_order(_fake, _first_compact)
    _parsed = [e["label"] for e in _fake._actual_turn_order]
    check(f"CombatScreen parses the superboss compact line ({len(_parsed)} labels)",
          len(_parsed) >= 2 and all(_parsed))
    # Initiative noise (numbered list/headers) is UI info, not a combat event
    check("initiative noise filtered from the GUI log",
          not CombatScreen._is_combat_event(_fake, "Turn Order for this Round:")
          and not CombatScreen._is_combat_event(_fake, "   1. Hero (Speed: 53)")
          and not CombatScreen._is_combat_event(_fake, "Initiative Phase")
          and not CombatScreen._is_combat_event(_fake, "Rolling speeds..."))
    check("real combat events still pass the log filter",
          CombatScreen._is_combat_event(
              _fake, "Hero → White Knight of the Fallen Empire: 54 dmg"))
except Exception as _exc:
    check(f"GUI parse simulation failed: {_exc!r}", False)

if FAILS:
    print(f"{len(FAILS)} FAIL(S):")
    for f in FAILS:
        print(" -", f)
else:
    print("ALL CHECKS PASSED")
