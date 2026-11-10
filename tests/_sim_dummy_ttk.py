"""Simulate the Training Dummy fight for savegame_1 to estimate turns-to-kill.

Usage:
    .venv\\Scripts\\python.exe tests/_sim_dummy_ttk.py [solo|party] [max_rounds] [trace]

Runs the REAL combat engine (combat/combat_engine.py) with a scripted I/O bridge:
- Player: Black Silence glove workshops (all 9, damage-first order), then Furioso; repeat.
- Allies (party mode): basic attack every turn.
The dummy config matches the user's barracks setup:
    HP 999999, STR -100, CON 20, DEX -100,
    res: fire .8 / water .5 / thunder .7 / light 1.0 / dark .8 / physical .5 / magical .6,
    wind & earth 0.0 (untouched).
"""

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from character import ensure_player_fields
from combat.combat_io import BaseCombatIO, set_io
from combat.dummy import create_dummy_enemy, _run_dummy_combat
from save_load import load_game

DUMMY_CFG = {
    "hp": 999999,
    "str_mod": -100,
    "con_mod": 20,
    "dex_mod": -100,
    "elemental_res": {
        "fire": 0.8, "water": 0.5, "thunder": 0.7, "wind": 0.0, "earth": 0.0,
        "light": 1.0, "dark": 0.8, "physical": 0.5, "magical": 0.6,
    },
}

# Workshop execution order (all 9 must be used to unlock Furioso).
ORDER = (8, 1, 4, 3, 9, 6, 7, 5, 2)

KEEP_TRACE = False
PROGRESS_EVERY = 500


class ScriptIO(BaseCombatIO):
    def __init__(self, player):
        self.player = player
        self.player_turns = 0
        self.furiosos = 0
        self.laments = 0
        self.backlashes = 0
        self.unhandled = 0
        self.trace = []

    def print(self, *args, **kwargs):
        text = " ".join(str(a) for a in args)
        if "DIVINE LAMENT" in text:
            self.laments += 1
        if "WEDGE BACKLASH" in text:
            self.backlashes += 1
        if KEEP_TRACE:
            self.trace.append(text)

    def clear(self):
        pass

    def input(self, prompt=""):
        p = self.player
        if prompt == "Choose: ":
            self.player_turns += 1
            if p.get("gloves_furioso_available"):
                self.furiosos += 1
                return "0"
            used = p.get("gloves_workshop_used")
            if not isinstance(used, (set, list)):
                used = set()
            for wid in ORDER:
                if wid not in used:
                    return str(wid)
            return "0"
        if "Choose action" in prompt:
            return "a"
        if "Press Enter" in prompt:
            return ""
        if "Select target" in prompt:
            return "1"
        if "Use which item" in prompt:
            return "0"
        self.unhandled += 1
        if KEEP_TRACE:
            self.trace.append(f"UNHANDLED INPUT PROMPT: {prompt!r}")
        return ""


def main():
    global KEEP_TRACE
    mode = sys.argv[1] if len(sys.argv) > 1 else "party"
    max_rounds = int(sys.argv[2]) if len(sys.argv) > 2 else 40000
    KEEP_TRACE = len(sys.argv) > 3 and sys.argv[3] == "trace"

    player = load_game(1)
    if player is None:
        print("savegame_1 not found")
        return
    ensure_player_fields(player)

    if mode == "solo":
        player["allies"] = []
    # keep a pristine copy of ally hp in case ensure_player_fields mutated things
    dummy = create_dummy_enemy(DUMMY_CFG)
    io = ScriptIO(player)
    set_io(io)

    import combat.combat_engine as ce
    orig_roll = ce.roll_initiative
    rounds = {"n": 0}

    def capped_roll(p, enemies):
        rounds["n"] += 1
        if rounds["n"] > max_rounds:
            raise KeyboardInterrupt("round cap reached")
        if rounds["n"] % PROGRESS_EVERY == 0:
            print(f"  ... round {rounds['n']}: dummy hp={dummy['hp']}")
        return orig_roll(p, enemies)

    ce.roll_initiative = capped_roll

    start = time.time()
    try:
        result = _run_dummy_combat(player, DUMMY_CFG, enemies=[dummy])
    except KeyboardInterrupt:
        result = "ROUND CAP"
    except Exception as exc:  # pragma: no cover
        import traceback
        traceback.print_exc()
        result = f"crashed: {exc}"
    finally:
        ce.roll_initiative = orig_roll
        elapsed = time.time() - start

    dealt = 999999 - dummy["hp"]
    print("=" * 60)
    print(f"mode={mode}  result={result}  elapsed={elapsed:.1f}s")
    print(f"rounds={rounds['n']}  player turns={io.player_turns}  furiosos={io.furiosos}")
    print(f"player laments={io.laments}  wedge backlashes={io.backlashes}  unhandled_prompts={io.unhandled}")
    print(f"dummy hp left={dummy['hp']}  damage dealt={dealt}")
    if rounds["n"] and dealt:
        print(f"avg damage per round (all sources)={dealt / rounds['n']:.1f}")
        print(f"projected rounds for 999999 = {999999 / (dealt / rounds['n']):.0f}")
    if io.player_turns and dealt:
        print(f"avg per player turn={dealt / io.player_turns:.1f}")
    print("=" * 60)


if __name__ == "__main__":
    main()
