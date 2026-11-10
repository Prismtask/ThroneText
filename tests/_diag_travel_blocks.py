"""Diagnostic: travel block spending & camping (docs/time_system_design.md §8).

Covers the Stage C travel model:
  1. can_camp: Caravan mount / Portable Camp item / neither.
  2. spend_travel_segment — sub-boundary: blocks just accumulate.
  3. March through a boundary: day rolls, +1 fatigue stack, overflow on the new day.
  4. Camp at the boundary: no fatigue, remainder resumes in the morning.
  5. Camp with an exact fill: last block fills the day, then the night.
  6. Camp sleep clears fatigue stacks that had already accrued.
  7. Journey totals = per-hop sums (30-min rounding + mount shave).
  8. Wonderland time pocket — travel spends are nullified.

Run from repo root with:
    .venv\\Scripts\\python.exe -m tests._diag_travel_blocks
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:  # piped consoles on Windows may default to a legacy codepage
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass

import time_blocks as tb


def _player(**kw):
    p = {"day": 3, "day_blocks": 0, "fatigue_stacks": 0,
         "time_minutes": tb.DAY_START_MINUTES, "inventory": []}
    p.update(kw)
    return p


def main():
    # 1. can_camp
    assert not tb.can_camp(_player())
    assert tb.can_camp(_player(mount_id="caravan"))
    assert tb.can_camp(_player(inventory=[{"id": "portable_camp",
                                           "name": "Portable Camp"}]))
    assert not tb.can_camp(_player(mount_id="horse"))
    print("PASS 1: can_camp = Caravan mount or Portable Camp item")

    # 2. no boundary — plain accumulation
    p = _player(day_blocks=2)
    days = tb.spend_travel_segment(p, 3)
    assert days == 0 and p["day_blocks"] == 5 and p["day"] == 3
    assert p["fatigue_stacks"] == 0
    print("PASS 2: sub-boundary segments accumulate, no day roll")

    # 3. march through the boundary
    p = _player(day_blocks=22)
    days = tb.spend_travel_segment(p, 4, camp=False)
    assert days == 1 and p["day"] == 4 and p["day_blocks"] == 2
    assert p["fatigue_stacks"] == 1
    print("PASS 3: marching rolls the day with +1 fatigue, overflow lands next day")

    # 4. camp at the boundary
    p = _player(day_blocks=22)
    days = tb.spend_travel_segment(p, 4, camp=True)
    assert days == 1 and p["day"] == 4 and p["day_blocks"] == 2
    assert p["fatigue_stacks"] == 0
    print("PASS 4: camping clears fatigue and resumes in the morning")

    # 5. camp with an exact fill
    p = _player(day_blocks=22)
    days = tb.spend_travel_segment(p, 2, camp=True)
    assert days == 1 and p["day"] == 4 and p["day_blocks"] == 0
    assert p["fatigue_stacks"] == 0
    print("PASS 5: exact-fill camp spends the last block, then sleeps")

    # 6. camp sleep resets existing stacks
    p = _player(day_blocks=23, fatigue_stacks=2)
    tb.spend_travel_segment(p, 2, camp=True)
    assert p["fatigue_stacks"] == 0 and p["day_blocks"] == 1
    print("PASS 6: camp sleep resets fatigue stacks that had accrued")

    # 7. journey totals = per-hop sums (rounding + supply + mount shave)
    hops = [100, 90, 110, 80]
    assert sum(tb.travel_blocks_for(m) for m in hops) == 6 + 5 + 6 + 5
    assert sum(tb.travel_blocks_for(m, mount_tier=4) for m in hops) == 4 + 3 + 4 + 3
    print("PASS 7: journey totals are per-hop sums (supply + mount shave)")

    # 8. Wonderland time pocket
    p = _player(wonderland_active=True, day_blocks=3)
    days = tb.spend_travel_segment(p, 5, camp=True)
    assert days == 0 and p["day_blocks"] == 3 and p["day"] == 3
    print("PASS 8: Wonderland nullifies travel spends (time pocket)")

    print("\nAll travel-block diagnostics passed.")


if __name__ == "__main__":
    main()
