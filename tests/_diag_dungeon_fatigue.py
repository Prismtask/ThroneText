"""Diagnostic: fatigue behavior inside dungeon runs (answer-locking checks).

Covers the 2026-10-14 question: "fatigue doesn't seem to be added in dungeons".

  1. Normal dungeon rooms (60 min = 1 block each) roll the day after 24 rooms
     and add +50 stress (stress system, 2026-10-30) — fatigue is NOT
     suppressed in normal dungeons. A second unslept day converts the full
     meter into Fatigue I.
  2. The top bar refreshes from the dungeon WORKER thread (rooms run off the
     tk main thread): a boundary-crossing spend makes STRESS appear.
  3. Wonderland / Event Horizon suppress stress; Pandemonium accrues (rev 3.5)
     (time pockets / frozen clocks — normal dungeons all accrue)
     by design.

Run from repo root with:
    .venv\\Scripts\\python.exe -m tests._diag_dungeon_fatigue
"""
import sys
import threading
import time
import tkinter as tk
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:  # piped consoles on Windows may default to a legacy codepage
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass

import time_blocks as tb
from gui.screen_manager import ScreenManager


class DummyDungeon(tk.Frame):
    """Minimal stand-in for DungeonScreen (own top-bar builder)."""

    def __init__(self, parent, screen_manager, **kwargs):
        super().__init__(parent, bg="#111111")
        self.sm = screen_manager
        self.ticks = 0

    def _update_top_bar(self):
        self.ticks += 1
        p = self.sm.player
        track = tb.format_block_track(p, include_day=False)
        self.sm.update_top_bar(f"Dungeon — Floor 3 | {track}" if track
                               else "Dungeon — Floor 3")


def pump(root, seconds):
    end = time.time() + seconds
    while time.time() < end:
        root.update()
        time.sleep(0.005)


def main():
    # ── 1. Engine: 24 normal dungeon rooms roll the day, +1 fatigue ──────
    p = {"day": 3, "day_blocks": 0, "fatigue_stacks": 0, "stress": 0,
         "time_minutes": tb.DAY_START_MINUTES, "location": "dungeon",
         "allies": [], "inventory": []}
    for _ in range(24):
        tb.advance_time(p, 60)          # one room = 60 min = 1 block
    assert p["day"] == 4 and p["fatigue_stacks"] == 0 and p["stress"] == 50, p
    assert "STRESS 50" in tb.format_block_track(p)
    for _ in range(24):
        tb.advance_time(p, 60)          # a second unslept day converts
    assert p["day"] == 5 and p["fatigue_stacks"] == 1 and p["stress"] == 0, p
    assert "FATIGUE I" in tb.format_block_track(p)
    print("PASS 1: 24 rooms = +50 stress; a second unslept day converts to Fatigue I")

    # ── 2. Worker-thread spends refresh the dungeon header ───────────────
    # Run inside a REAL mainloop (real play): tkinter only marshals calls
    # from worker threads while the main thread is in mainloop.
    root = tk.Tk()
    root.withdraw()
    player = {"name": "Tester", "level": 10, "day": 3, "day_blocks": 0,
              "fatigue_stacks": 0, "stress": 0,
              "time_minutes": tb.DAY_START_MINUTES,
              "location": "dungeon", "allies": [], "inventory": []}
    sm = ScreenManager(root, player=player)
    sm.switch_to(DummyDungeon)
    d = sm.current_screen
    d._update_top_bar()

    results = {}

    def _scenario():
        # Runs on the main thread inside mainloop. Never join the worker
        # here: tkinter marshals cross-thread calls to the main loop, so
        # blocking the main thread on the worker would deadlock the
        # after() call the worker itself triggers.
        before = d.ticks
        threading.Thread(target=lambda: tb.spend_blocks(player, 1),
                         daemon=True).start()

        def _check_refresh():
            results["refreshed"] = d.ticks > before
            # Boundary roll from the worker: FATIGUE must appear in the bar.
            player["day_blocks"] = 23
            threading.Thread(target=lambda: tb.spend_blocks(player, 1),
                             daemon=True).start()
            root.after(250, _check_fatigue)

        def _check_fatigue():
            # NOTE: update_top_bar() writes the text into top_name
            # (top_info is cleared) — read the right label.
            results["txt"] = sm.top_name.cget("text")
            results["state"] = (player["day"], player["fatigue_stacks"],
                                tb.get_stress(player))
            root.quit()

        root.after(250, _check_refresh)

    root.after(50, _scenario)
    root.mainloop()

    assert results.get("refreshed"), \
        "worker-thread spend did not refresh the header (under mainloop)"
    assert results.get("state") == (4, 0, 50), results
    assert "STRESS 50" in results.get("txt", ""), results
    print("PASS 2: worker-thread spends refresh the header (STRESS 50 visible)")

    # ── 3. By-design suppressions ────────────────────────────────────────
    wl = dict(player, wonderland_active=True, day_blocks=23,
              day=4, fatigue_stacks=0, stress=0)
    tb.advance_time(wl, 60)
    assert wl["day"] == 4 and wl["fatigue_stacks"] == 0 and wl["stress"] == 0
    pn = dict(player, pandemonium_mode=True, day_blocks=23,
              day=4, fatigue_stacks=0, stress=0)
    tb.advance_time(pn, 60)
    assert pn["stress"] == 50 and pn["fatigue_stacks"] == 0
    eh = dict(player, _eh_in_run=True, event_horizon={"run_active": True},
              day_blocks=23, day=4, fatigue_stacks=0, stress=0)
    tb.advance_time(eh, 60)
    assert eh["fatigue_stacks"] == 0 and eh["stress"] == 0
    print("PASS 3: Wonderland / EH suppress stress; Pandemonium accrues (+50)")

    root.destroy()
    print("\nAll dungeon-fatigue diagnostics passed.")


if __name__ == "__main__":
    main()
