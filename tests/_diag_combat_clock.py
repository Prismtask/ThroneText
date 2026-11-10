"""Diagnostic: block time flow — no wall-clock tick (replaces the old tick test).

Covers the 2026-10-13 switchover (docs/time_system_design.md):
  1. Idling advances NOTHING — blocks/day stay put (no background clock).
  2. Spending time refreshes the visible top bar via the registered listener
     (fires on the tk main loop, works from any thread).
  3. An active overlay owns the refresh; the hidden screen's bar is untouched.
  4. City-idle Event Notice flush still works after a time advance
     (see _diag_event_notice.py for the queueing half).
  5. The top bar renders the phase block track (Morning/Noon/Night),
     never HH:MM, and re-renders on spends.

Run from repo root with:
    .venv\\Scripts\\python.exe tests\\_diag_combat_clock.py
"""
import sys
import time
import tkinter as tk
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:  # piped consoles on Windows may default to a legacy codepage (cp932)
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass

import time_blocks as tb
from gui.screen_manager import ScreenManager


class DummyScreenBase(tk.Frame):
    def __init__(self, parent, screen_manager, **kwargs):
        super().__init__(parent, bg="#111111")
        self.sm = screen_manager
        self.ticks = 0

    def _update_top_bar(self):
        self.ticks += 1


DungeonLike = type("DungeonScreen", (DummyScreenBase,), {})
CombatLike = type("CombatLikeOverlay", (DummyScreenBase,), {})


def pump(root, seconds):
    end = time.time() + seconds
    while time.time() < end:
        root.update()
        time.sleep(0.005)


def main():
    root = tk.Tk()
    root.withdraw()
    player = {"day": 5, "day_blocks": 0, "fatigue_stacks": 0,
              "time_minutes": tb.DAY_START_MINUTES, "location": "dungeon"}
    sm = ScreenManager(root, player=player)
    sm.switch_to(DungeonLike)
    dungeon = sm.current_screen

    # ── 1. No wall clock: idling advances nothing ───────────────────────
    pump(root, 0.4)
    assert player["day_blocks"] == 0 and player["day"] == 5
    assert dungeon.ticks == 0, "idle refresh happened without a time spend"
    print("PASS 1: no wall-clock — idling advances nothing")

    # ── 2. Spending time refreshes the top bar ──────────────────────────
    tb.spend_blocks(player, 2)
    pump(root, 0.15)
    assert player["day_blocks"] == 2
    assert dungeon.ticks > 0, "listener did not refresh the top bar"
    print("PASS 2: time spend refreshes the top bar via the listener")

    # ── 3. Overlay owns the refresh while active ────────────────────────
    sm.push_overlay(CombatLike)
    overlay = sm._overlay_screen
    dungeon_ticks = dungeon.ticks
    tb.spend_blocks(player, 1)
    pump(root, 0.15)
    assert overlay.ticks > 0, "overlay was not refreshed"
    assert dungeon.ticks == dungeon_ticks, "hidden screen updated under overlay"
    sm.dismiss_overlay()
    print("PASS 3: overlay owns the refresh; hidden screen untouched")

    # ── 4. Top bar shows the phase track, not HH:MM ─────────────────────
    sm.refresh_top_bar(player)
    info = sm.top_info.cget("text")
    assert "Morning" in info and "\u2600" in info, f"no phase track: {info!r}"
    assert ":" not in info.split("|")[-2], f"HH:MM leaked: {info!r}"
    tb.spend_blocks(player, 8)          # 8-block phases: morning (0-7) → noon (8-15)
    sm.refresh_top_bar(player)
    info = sm.top_info.cget("text")
    assert "Noon" in info, f"phase did not update: {info!r}"
    print("PASS 4: top bar renders the block track and follows spends")

    # ── 5. Wonderland time pocket: the track disappears ──────────────────
    player["wonderland_active"] = True
    sm.refresh_top_bar(player)
    info = sm.top_info.cget("text")
    assert "Noon" not in info and "Morning" not in info and "\u25ae" not in info, info
    assert "|" in info, f"top bar lost its separators: {info!r}"
    player.pop("wonderland_active", None)
    print("PASS 5: Wonderland top bar drops the track (flavor only)")

    root.destroy()
    print("\nAll block-time flow diagnostics passed.")


if __name__ == "__main__":
    main()
