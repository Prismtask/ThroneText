"""Diagnostic: day-rollover Event Notices reach the popup pipeline.

Covers the 2026-10-13 fix ("event window won't appear without the
necessary trigger"):
  1. utils.advance_time in GUI mode queues rollover events even when the
     player is NOT in a dungeon (before: silently dropped — the Event
     Notice popup never saw them).
  2. Dungeon rollovers still queue (unchanged behaviour).
  3. ScreenManager surfaces queued events while the player idles on the
     city screen (via the clock tick), and leaves them alone elsewhere.

Run from repo root with:
    .venv\\Scripts\\python.exe tests\\_diag_event_notice.py
"""
import sys
import time
import tkinter as tk
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import events
import gui.screens.city_screen as city_mod
import gui.widgets.event_dialog as evdlg
import time_blocks as tb
from gui.screen_manager import ScreenManager
from utils import advance_time


TEST_EVENT = {"name": "Test Omen", "desc": "The moons align.", "fixed": True}


def _make_player(location):
    return {
        "time_minutes": 23 * 60 + 59,
        "day": 5,
        "location": location,
        "origin_city": "solmere",
        "daily_effects": {},
        "active_buffs": [],
        "inventory": [],
    }


def main():
    root = tk.Tk()
    root.withdraw()

    real_check = events.check_events_for_day
    real_city_cls = city_mod.CityScreen
    real_show = evdlg.show_event_notice

    shown = []

    class DummyScreenBase(tk.Frame):
        def __init__(self, parent, screen_manager, **kwargs):
            super().__init__(parent)
            self.sm = screen_manager

        def _update_top_bar(self):
            pass

    DummyCity = type("CityScreen", (DummyScreenBase,), {})
    DungeonLike = type("DungeonScreen", (DummyScreenBase,), {})

    try:
        events.check_events_for_day = lambda day: [dict(TEST_EVENT, day=day)]
        city_mod.CityScreen = DummyCity  # isinstance target for the flush
        evdlg.show_event_notice = (
            lambda events, day_text=None, parent=None: shown.append(list(events)))

        # ── 1. GUI rollover outside a dungeon → queued ──────────────────
        p_city = _make_player("solmere")
        p_city["day_blocks"] = 23      # one action away from the day boundary
        advance_time(p_city, 60)       # 16–90 min = 1 block → rolls the day
        assert p_city["day"] == 6, p_city["day"]
        queued = p_city.get("event_queue", [])
        assert any(e.get("name") == TEST_EVENT["name"] for e in queued), queued
        print("PASS 1: city rollover queues the Event Notice (was dropped)")

        # ── 2. Dungeon rollover still queues ────────────────────────────
        p_dun = _make_player("dungeon")
        p_dun["day_blocks"] = 23
        advance_time(p_dun, 60)
        assert any(e.get("name") == TEST_EVENT["name"]
                   for e in p_dun.get("event_queue", [])), p_dun.get("event_queue")
        print("PASS 2: dungeon rollover still queues for city return")

        # ── 3. City-idle flush surfaces the queue via a clock tick ──────
        player = {"time_minutes": 8 * 60, "day": 6, "location": "solmere",
                  "event_queue": [dict(TEST_EVENT, day=6)]}
        sm = ScreenManager(root, player=player)
        sm.switch_to(DungeonLike)
        tb.spend_blocks(player, 1)     # time advances → listener fires
        end = time.time() + 0.3
        while time.time() < end:
            root.update()
            time.sleep(0.005)
        assert player["event_queue"], "dungeon screen must not pop the queue"
        assert not shown, "notice shown outside a city"

        sm.switch_to(DummyCity)
        tb.spend_blocks(player, 1)     # next advance surfaces queued notices
        end = time.time() + 0.6
        while time.time() < end and not shown:
            root.update()
            time.sleep(0.005)
        assert shown, "queued notice was not surfaced while idling in city"
        assert shown[0][0].get("name") == TEST_EVENT["name"], shown
        assert not player.get("event_queue"), "queue not cleared after showing"
        print("PASS 3: city idle surfaces queued notices; dungeon leaves them")

        print("\nAll event-notice diagnostics passed.")
    finally:
        events.check_events_for_day = real_check
        city_mod.CityScreen = real_city_cls
        evdlg.show_event_notice = real_show
        root.destroy()


if __name__ == "__main__":
    main()
