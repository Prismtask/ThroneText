"""Diagnostic: seasons & weather (events.py / time_blocks.py).

Covers the 2026-10-30 slice:
  1. get_season: 30-day months, one season per month, 4-month cycle.
  2. format_date carries the season; format_block_track swaps the phase
     icon for the weather glyph and appends the season with the day.
  3. Weather severity is charged exactly once, as blocks
     (light +1 / heavy +2, tier 3+ mounts mitigate).
  4. The random-event pool is season-weighted (snow only in winter, etc.)
     and no event still carries the legacy `travel_time_mult`.
  5. legacy fallback: `travel_time_mult` alone still maps to a rain level.

Run from repo root with:
    .venv\\Scripts\\python.exe tests\\_diag_season_weather.py
"""
import collections
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:  # piped consoles on Windows may default to a legacy codepage
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass

import events
import time_blocks as tb


def main():
    # ── 1. Seasons ────────────────────────────────────────────────────────
    assert events.get_season(1) == ("spring", "Spring")
    assert events.get_season(30) == ("spring", "Spring")
    assert events.get_season(31) == ("summer", "Summer")
    assert events.get_season(61) == ("autumn", "Autumn")
    assert events.get_season(91) == ("winter", "Winter")
    assert events.get_season(121) == ("spring", "Spring")
    assert events.get_season({"day": 61}) == ("autumn", "Autumn")
    print("PASS 1: seasons rotate one per 30-day month (4-month cycle)")

    # ── 2. Display ────────────────────────────────────────────────────────
    assert "Spring" in events.format_date(1)
    assert "Winter" in events.format_date(91)

    rain_player = {"day": 31, "day_blocks": 8,
                   "daily_effects": {"weather": "rain", "rain_level": 2}}
    track = tb.format_block_track(rain_player)
    assert track.startswith("⛈ Noon"), track            # weather replaces the icon
    assert "Summer" in track, track

    clear = tb.format_block_track({"day": 1, "day_blocks": 0})
    assert clear == "☀ Morning ▮▮▮▮▮▮▮▮ · Day 1 · Spring", clear
    print("PASS 2: weather glyph replaces the phase icon; season rides the day")

    # ── 3. Glyph table + single-charge travel ────────────────────────────
    for kind, sev, icon in (("rain", 1, "🌧"), ("rain", 2, "⛈"),
                            ("snow", 1, "🌨"), ("snow", 2, "❄"),
                            ("fog", 1, "🌫"), ("fog", 0, "🌫")):
        got = tb.weather_icon({"daily_effects": {"weather": kind,
                                                 "rain_level": sev}})
        assert got == icon, (kind, sev, got)
    assert tb.weather_icon({"daily_effects": {}}) == ""

    assert tb.travel_blocks_for(30, 0, 0) == 3
    assert tb.travel_blocks_for(30, 0, 1) == 4
    assert tb.travel_blocks_for(30, 0, 2) == 5
    assert tb.travel_blocks_for(30, 3, 0) == 2   # tier 3 shave (3 - 1)
    assert tb.travel_blocks_for(30, 3, 1) == 2   # tier 3+ ignores light weather
    assert tb.travel_blocks_for(30, 3, 2) == 3   # takes +1 from heavy weather
    print("PASS 3: weather adds blocks once (light +1 / heavy +2)")

    # ── 4. Season-weighted pool ──────────────────────────────────────────
    # Large seed sweep so the weighted ordering is statistically stable
    # (weather days are only ~20% of all days).
    by_season = collections.defaultdict(collections.Counter)
    for day in range(1, 120001):
        evt = events._pick_random_event(day)
        if evt:
            by_season[events.get_season(day)[0]][evt["id"]] += 1

    rain = {s: by_season[s]["rainy_day"] for s in by_season}
    snow = {s: by_season[s]["snowy_day"] for s in by_season}
    fog = {s: by_season[s]["foggy_day"] for s in by_season}
    assert rain["spring"] > rain["autumn"] > rain["summer"] > rain["winter"], rain
    assert snow["summer"] == 0, snow
    assert snow["winter"] > snow["autumn"] > snow["spring"] > snow["summer"], snow
    assert fog["autumn"] > fog["spring"] > fog["winter"] > fog["summer"], fog
    assert all("travel_time_mult" not in e.get("effect", {})
               for e in events.RANDOM_EVENT_POOL)
    print("PASS 4: weather is season-weighted; no legacy time multiplier")

    # ── 5. Legacy fallback (pre-block saves) ─────────────────────────────
    assert tb.travel_rain_level({"daily_effects": {"travel_time_mult": 1.3}}) == 2
    assert tb.travel_rain_level({"daily_effects": {"travel_time_mult": 1.1}}) == 1
    assert tb.travel_rain_level({}) == 0
    print("PASS 5: legacy travel_time_mult maps to weather severity")

    print("\nAll season/weather diagnostics passed.")


if __name__ == "__main__":
    main()
