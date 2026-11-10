# Temp check (2026-10-08): evasion lines classified correctly for ticker persistence.
import sys
sys.path.insert(0, "c:/Code/Pandemonium")
from gui.screens.combat_screen import CombatScreen

tests = [
    "The Wolf dodges your attack!",
    "The Wolf dodges Dorothy's attack!",
    "The Wolf is blinded and flails wildly — it misses!",
    "The Harpy lunges at You — but You dodges out of the way!",
    "  💨 The Wolf reads the strike and slips aside!",
    "  💨 The smoke clouds your vision — your attack goes wide!",
    "  Alice is reeling!",  # control: must NOT persist
]
for t in tests:
    keep = CombatScreen._is_evade_line(None, t)
    evt = CombatScreen._is_combat_event(None, t)
    print(f"persist={str(keep):5s} log={str(evt):5s} | {t}")

assert CombatScreen._is_evade_line(None, "The Wolf dodges your attack!")
assert CombatScreen._is_evade_line(None, "  💨 The Wolf reads the strike and slips aside!")
assert not CombatScreen._is_evade_line(None, "  Alice is reeling!")
print("OK — evasion classification correct")
