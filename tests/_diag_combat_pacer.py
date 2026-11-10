"""Diag: combat pacer — classification, holds, skip lifecycle (mocked sleep).

The pacer sleeps on the engine thread; this test injects a recording sleep
function so the computed waits are asserted without real timing.

Run:
    .venv\\Scripts\\python.exe tests\\_diag_combat_pacer.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gui.combat_pacer import (CombatPacer, HOLD_ENEMY, HOLD_PARTY, HOLD_ROUND,
                              STAGGER, INPUT_SETTLE, RESOLVE_LEAD)

PARTY = ["prism", "Alice", "Ninetales Fox", "Red Hood"]


class Recorder:
    def __init__(self):
        self.calls = []

    def __call__(self, seconds):
        self.calls.append(seconds)


def make(speed="normal"):
    rec = Recorder()
    pacer = CombatPacer(active_fn=lambda: True, sleep_fn=rec)
    pacer.configure(party_names=PARTY, speed=speed)
    return pacer, rec


def total_ms(rec):
    return round(sum(rec.calls) * 1000)


def main():
    # 1. Classification → correct hold per line kind.
    p, rec = make()
    p.after_print(">> ROUND 2 | Floor 46")
    assert total_ms(rec) == 0, total_ms(rec)   # round beat retired — top bar shows it
    rec.calls.clear()
    p.after_print("[3/7] World Serpent's Turn:")
    assert total_ms(rec) == HOLD_ENEMY, total_ms(rec)
    rec.calls.clear()
    p.after_print("[2/7] Alice's Turn:")
    assert total_ms(rec) == HOLD_PARTY, total_ms(rec)
    rec.calls.clear()
    p.after_print("Ninetales Fox [Sunfire Breath] → Eclipse Countess: 120 dmg [FIRE]")
    assert total_ms(rec) == STAGGER, total_ms(rec)
    rec.calls.clear()
    p.after_print("  World Serpent is burning!")          # status hint
    assert total_ms(rec) == STAGGER, total_ms(rec)
    rec.calls.clear()
    p.after_print(">> 1. Attack (STR)")                   # menu line → no wait
    assert rec.calls == [], rec.calls
    rec.calls.clear()
    p.after_print(">>> Sunfire Breath: deals damage to all foes")  # banner → no wait
    assert rec.calls == [], rec.calls
    rec.calls.clear()
    p.after_print("\n=== Combat ended: VICTORY ===")      # narrative → no wait
    assert rec.calls == [], rec.calls
    rec.calls.clear()
    p.after_print("== log dump\n[5/7] Goblin Demolition Squad's Turn:")  # multiline
    assert total_ms(rec) == HOLD_ENEMY, total_ms(rec)
    print("OK — classification + holds")

    # 2. Instant = zero waits everywhere.
    p, rec = make("instant")
    p.after_print(">> ROUND 1")
    p.after_print("[3/7] World Serpent's Turn:")
    p.after_print("X → Y: 10 dmg")
    p.before_input()
    assert rec.calls == [], rec.calls
    print("OK — instant mode has no waits")

    # 3. Speed multipliers scale the waits.
    p, rec = make("slow")
    p.after_print("[3/7] World Serpent's Turn:")
    assert total_ms(rec) == HOLD_ENEMY * 2, total_ms(rec)
    p, rec = make("fast")
    p.after_print("[3/7] World Serpent's Turn:")
    assert total_ms(rec) == HOLD_ENEMY // 2, total_ms(rec)
    print("OK — speed multipliers")

    # 4. Skip: one request finishes the current beat; next header paces again.
    p, rec = make()
    p.after_print("[3/7] World Serpent's Turn:")   # normal hold
    p.request_skip()
    rec.calls.clear()
    p.after_print("X → Y: 10 dmg")                 # skip consumed here
    assert rec.calls == [], rec.calls
    p.after_print("Y is burning!")                 # still suppressed
    assert rec.calls == [], rec.calls
    rec.calls.clear()
    p.after_print("[4/7] Alice's Turn:")           # new beat resets
    assert total_ms(rec) == HOLD_PARTY, total_ms(rec)
    print("OK — skip lifecycle (one request = one beat)")

    # 5. Prompts are instant; entering an input phase clears stale skips.
    p, rec = make()
    p.request_skip()
    rec.calls.clear()
    p.before_input()
    assert total_ms(rec) == 0, total_ms(rec)
    print("OK — prompts instant; stale skips cleared")

    # 6. Teardown: inactive bridge (stop() sets _active False + abort) → no waits.
    state = {"active": True}
    rec = Recorder()
    p = CombatPacer(active_fn=lambda: state["active"], sleep_fn=rec)
    p.after_print("[3/7] Wolf's Turn:")
    assert sum(rec.calls) > 0
    p.abort()
    state["active"] = False
    rec.calls.clear()
    p.after_print("[3/7] Wolf's Turn:")
    p.before_input()
    assert rec.calls == [], rec.calls
    print("OK — teardown suppresses waits")

    # 7. Unknown/blank chunks never sleep.
    p, rec = make()
    p.after_print("")
    p.after_print("\n")
    assert rec.calls == []
    print("OK — blank chunks ignored")

    # 8. Confirm → delay → damage: one lead-in before the first event after
    #    any input; banners don't consume it, later events don't re-lead.
    p, rec = make()
    p.mark_input_received()
    p.before_print(">>> Skill: deals damage to a foe")   # banner: not an event
    assert rec.calls == [], rec.calls
    p.before_print("Wolfling → Wolf: 10 dmg")            # first event → lead
    assert total_ms(rec) == RESOLVE_LEAD, total_ms(rec)
    rec.calls.clear()
    p.before_print("Wolf is burning!")                   # lead fires once
    assert rec.calls == [], rec.calls
    print("OK — confirm lead-in (delay lands before the damage)")

    print("\nAll combat pacer checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
