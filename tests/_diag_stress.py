"""Headless diagnostic: player stress meter (decision-locked 2026-10-30).

Rules under test
────────────────
* One skipped night = **+50 stress** (no fatigue). A full meter (100)
  converts into **+1 fatigue stack**; only real sleep clears stress/ fatigue.
* Wonderland (time pocket) and Event Horizon (frozen clock) accrue nothing;
  Pandemonium accrues normally.
* Bands: calm (<34) · worn (34–66) · rattled (67–99).
* Rattled adds +1 hallucination tier and unlocks hallucinations on its own.
* Burden dreams feed the meter (`player_stress` effect).

Run:
    .venv\\Scripts\\python.exe tests\\_diag_stress.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# Headless: no level-up UI, no saves.
import leveling
leveling.gain_exp = lambda player, amount: None
leveling.gain_exp_ally = lambda ally, amount: None
import save_load
save_load.save_game = lambda player: None

import time_blocks as tb
from character import build_character, ensure_player_fields
import dreams
from resources.dreams import get_dream
import combat.hallucination as hal

CHECKS = []


def check(name, ok, detail=""):
    CHECKS.append((name, bool(ok), detail))
    tag = "OK  " if ok else "FAIL"
    print(f"[{tag}] {name}" + (f" — {detail}" if detail and not ok else ""))


ATTRS = {"Strength": 5, "Constitution": 5, "Dexterity": 5,
         "Learning": 5, "Wisdom": 5, "Charisma": 5}


def new_player():
    player = build_character("1", "1", ATTRS, "Diag", 1)
    player.pop("save_slot", None)
    ensure_player_fields(player)
    return player


def unslept(player):
    tb.end_day(player, slept=False)


# ── 1. Seeding ──────────────────────────────────────────────────────────────
player = new_player()
check("build_character + ensure_player_fields seed stress = 0",
      player.get("stress") == 0)

raw = {"day": 1, "day_blocks": 0, "fatigue_stacks": 0}
check("missing stress reads as 0 on raw dicts", tb.get_stress(raw) == 0)

# ── 2. Accrual + conversion ────────────────────────────────────────────────
player = new_player()
unslept(player)
check("one skipped night = +50 stress and no fatigue",
      player["stress"] == 50 and player["fatigue_stacks"] == 0,
      f"stress={player['stress']} fatigue={player['fatigue_stacks']}")
check("the block track shows the meter",
      "STRESS 50" in tb.format_block_track(player),
      tb.format_block_track(player))

unslept(player)
check("a full meter converts into Fatigue I and resets stress",
      player["fatigue_stacks"] == 1 and player["stress"] == 0,
      f"stress={player['stress']} fatigue={player['fatigue_stacks']}")
check("the track shows FATIGUE I after conversion",
      "FATIGUE I" in tb.format_block_track(player),
      tb.format_block_track(player))

for _ in range(4):
    unslept(player)
check("two more conversions reach Fatigue III (cap)",
      player["fatigue_stacks"] == 3 and player["stress"] == 0,
      f"stress={player['stress']} fatigue={player['fatigue_stacks']}")

unslept(player)
check("stress still accrues at the fatigue cap", player["stress"] == 50)
unslept(player)
check("a conversion at the cap drops the excess instead of banking it",
      player["fatigue_stacks"] == 3 and player["stress"] == 0,
      f"stress={player['stress']} fatigue={player['fatigue_stacks']}")

# ── 3. Sleep is the only reset ─────────────────────────────────────────────
player = new_player()
player["stress"] = 84
player["fatigue_stacks"] = 2
tb.end_day(player, slept=True)
check("sleep clears both stress and fatigue",
      player["stress"] == 0 and player["fatigue_stacks"] == 0)

player = new_player()
player["stress"] = 84
player["fatigue_stacks"] = 1
from utils import advance_time as _advance_time  # noqa: E402  (delegates to blocks)
_advance_time(player, 60)
check("a normal block spend does not touch stress", player["stress"] == 84)

# ── 4. Suppressions ────────────────────────────────────────────────────────
wl = dict(new_player(), wonderland_active=True, day_blocks=23)
tb.end_day(wl, slept=False)
check("Wonderland accrues nothing",
      wl.get("stress", 0) == 0 and wl["fatigue_stacks"] == 0)

eh = dict(new_player(), _eh_in_run=True, event_horizon={"run_active": True},
          day_blocks=23)
tb.end_day(eh, slept=False)
check("Event Horizon accrues nothing",
      eh.get("stress", 0) == 0 and eh["fatigue_stacks"] == 0)

pande = dict(new_player(), pandemonium_mode=True, day_blocks=23)
tb.end_day(pande, slept=False)
check("Pandemonium accrues stress", pande.get("stress") == 50)

# ── 5. Bands + HUD ─────────────────────────────────────────────────────────
bands = {0: "calm", 33: "calm", 34: "worn", 66: "worn",
         67: "rattled", 99: "rattled", 100: "rattled"}
check("band thresholds are exact",
      all(tb.stress_band({"stress": v}) == name for v, name in bands.items()),
      str({v: tb.stress_band({"stress": v}) for v in bands}))

track = tb.format_block_track({"day": 2, "day_blocks": 0, "fatigue_stacks": 0,
                               "stress": 84})
check("rattled stress carries the eye marker", "\U0001F441 STRESS 84" in track, track)
track = tb.format_block_track({"day": 2, "day_blocks": 0, "fatigue_stacks": 0,
                               "stress": 0})
check("a calm night shows no stress text", "STRESS" not in track, track)

# ── 6. add_stress edge cases ───────────────────────────────────────────────
player = new_player()
tb.add_stress(player, -200)
check("relief clamps at 0", player["stress"] == 0)
player["stress"] = 90
gained = tb.add_stress(player, 10)
check("exactly-full converts cleanly",
      gained == 1 and player["fatigue_stacks"] == 1 and player["stress"] == 0,
      f"gained={gained} stress={player['stress']}")

# ── 7. Burden dreams feed the meter ────────────────────────────────────────
player = new_player()
ally = {"key": "harpy_scout", "name": "Harpy", "level": 5, "current_hp": 40,
        "max_hp": 40, "stress": 0, "affection": 30, "affection_cap": 100}
player["allies"] = [ally]
dreams._apply_effects(player, get_dream("dream_thin_place"))
check("Nightmare adds player stress", player["stress"] == 34,
      f"stress={player['stress']}")
dreams._apply_effects(player, get_dream("dream_thin_place"))
check("two nightmares reach the rattled band",
      player["stress"] == 68 and tb.is_rattled(player),
      f"stress={player['stress']}")
dreams._apply_effects(player, get_dream("dream_thin_place"))
check("a third nightmare converts into fatigue",
      player["stress"] == 2 and player["fatigue_stacks"] == 1,
      f"stress={player['stress']} fatigue={player['fatigue_stacks']}")

# ── 8. Hallucination wiring ────────────────────────────────────────────────
player = new_player()
check("a calm, rested player has no hallucination tier",
      hal.hallucination_tier(player) == 0, f"{hal.hallucination_tier(player)}")

player["stress"] = 84
check("rattled alone reaches tier 2", hal.hallucination_tier(player) == 2,
      f"{hal.hallucination_tier(player)}")

player["fatigue_stacks"] = 2
check("rattled + Fatigue II reaches tier 3",
      hal.hallucination_tier(player) == 3, f"{hal.hallucination_tier(player)}")

player["stress"] = 0
check("Fatigue II without stress stays at tier 2",
      hal.hallucination_tier(player) == 2, f"{hal.hallucination_tier(player)}")

wl = new_player()
wl["wonderland_active"] = True
wl["stress"] = 84
check("Wonderland ignores the rattled bump",
      hal.hallucination_tier(wl) == 0, f"{hal.hallucination_tier(wl)}")

# should_trigger: night phase + full HP + no boss room
_player_random = hal.random.random
hal.random.random = lambda: 0.0
try:
    night = new_player()
    night["day_blocks"] = 16          # Night begins at block 16
    check("night phase recognised for the trigger test",
          tb.get_day_phase(night) == "night")

    night["stress"] = 84              # rattled, no fatigue
    check("rattled unlocks hallucinations without exhaustion",
          hal.should_trigger(night) is True)

    night["stress"] = 0               # calm, no fatigue
    check("calm + rested never hallucinates", hal.should_trigger(night) is False)

    night["fatigue_stacks"] = 1       # one stack is still safe
    check("a single fatigue stack alone never hallucinates",
          hal.should_trigger(night) is False)

    night["fatigue_stacks"] = 2
    check("Fatigue II still triggers (legacy rule)",
          hal.should_trigger(night) is True)
finally:
    hal.random.random = _player_random

# ── 9. Wiring guards ──────────────────────────────────────────────────────
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import inspect
src = inspect.getsource(tb.end_day)
check("end_day routes unslept rollovers through add_stress",
      "add_stress" in src and "get_fatigue_stacks(player) + 1" not in src)
check("sleep clears stress in end_day", 'player["stress"] = 0' in src)

dream_src = inspect.getsource(dreams._apply_effects)
check("dream effects apply player_stress", "player_stress" in dream_src)

failed = [name for name, ok, _ in CHECKS if not ok]
print()
print(f"{len(CHECKS) - len(failed)}/{len(CHECKS)} checks passed")
if failed:
    print("FAILED:")
    for name in failed:
        print(f"  - {name}")
    sys.exit(1)
print("player stress OK")
