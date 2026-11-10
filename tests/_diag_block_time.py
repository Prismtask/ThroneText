"""Diagnostic: block time engine (`time_blocks.py`) — dormant until switchover.

Covers the core rules from docs/time_system_design.md (rev 3):
conversion table, sequential spend, exact-fill and multi-day overflow,
fatigue stacks (cap, sleep reset, Event Horizon suppression), wait (1 block / until-morning),
phases/track display, service hours (+ per-city override), the Wonderland
time pocket, legacy migration, and the block-model `advance_time`.

Run from repo root with:
    .venv\\Scripts\\python.exe tests\\_diag_block_time.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import events
import facilities.dispatch as dispatch_mod
import facilities.guild as guild_mod
import facilities.monthly_billing as billing_mod
import time_blocks as tb
from resources.cities import CITIES


def make_player(**kw):
    p = {
        "day": 5,
        "day_blocks": 0,
        "fatigue_stacks": 0,
        "stress": 0,
        "time_minutes": tb.DAY_START_MINUTES,
        "location": "solmere",
    }
    p.update(kw)
    return p


class RolloverSpy:
    def __init__(self):
        self.calls = []

    def __call__(self, player, days_passed, old_day):
        self.calls.append((player.get("day"), days_passed, old_day))
        return []


def main():
    real_rollover = events.process_day_rollover
    real_bounty = guild_mod.check_bounty_expiry
    real_billing = billing_mod.process_monthly_billing
    real_dispatch = dispatch_mod.process_dispatch_progress

    spy = RolloverSpy()
    dispatch_calls = []
    events.process_day_rollover = spy
    guild_mod.check_bounty_expiry = lambda p: []
    billing_mod.process_monthly_billing = lambda p, d: None
    dispatch_mod.process_dispatch_progress = lambda p, d=0: dispatch_calls.append(d)

    try:
        # ── 1. Conversion table ─────────────────────────────────────────
        assert tb.blocks_for_minutes(0) == 0
        assert tb.blocks_for_minutes(15) == 0
        assert tb.blocks_for_minutes(16) == 1
        assert tb.blocks_for_minutes(60) == 1
        assert tb.blocks_for_minutes(90) == 1
        assert tb.blocks_for_minutes(91) == 2
        assert tb.blocks_for_minutes(240) == 2
        assert tb.blocks_for_minutes(480) == 2  # sleep = caller-side end_day()
        print("PASS 1: minute→block conversion table")

        # ── 2. Same-day accumulation ────────────────────────────────────
        p = make_player()
        assert tb.spend_blocks(p, 1) == 0
        assert tb.spend_blocks(p, 2) == 0
        assert p["day_blocks"] == 3 and p["day"] == 5
        assert p["fatigue_stacks"] == 0 and spy.calls == []
        print("PASS 2: same-day spending accumulates without rolling")

        # ── 3. Exact fill rolls the day (+fatigue +rollover) ────────────
        p = make_player(day_blocks=23)
        spy.calls.clear()
        assert tb.spend_blocks(p, 1) == 1
        assert p["day"] == 6 and p["day_blocks"] == 0
        assert p["fatigue_stacks"] == 0 and p["stress"] == 50
        assert spy.calls == [(6, 1, 5)], spy.calls
        assert p["time_minutes"] == tb.DAY_START_MINUTES
        print("PASS 3: exact fill rolls the day, +50 stress, rollover processed")

        # ── 4. Overflow eats the next day's blocks ──────────────────────
        p = make_player(day_blocks=23)
        assert tb.spend_blocks(p, 2) == 1
        assert p["day"] == 6 and p["day_blocks"] == 1
        assert p["fatigue_stacks"] == 0 and p["stress"] == 50
        print("PASS 4: overflow consumes the next day's blocks")

        # ── 5. Multi-day overflow ───────────────────────────────────────
        p = make_player()
        assert tb.spend_blocks(p, 50) == 2
        assert p["day"] == 7 and p["day_blocks"] == 2
        assert p["fatigue_stacks"] == 1 and p["stress"] == 0
        print("PASS 5: multi-day overflow rolls once per full day (2 nights = Fatigue I)")

        # ── 6. Fatigue caps at 3 ────────────────────────────────────────
        p = make_player()
        for _ in range(8):
            tb.spend_blocks(p, 24)
        assert p["fatigue_stacks"] == tb.MAX_FATIGUE and p["stress"] == 0
        print("PASS 6: fatigue caps at 3")

        # ── 7. Sleep clears stacks ──────────────────────────────────────
        p = make_player(fatigue_stacks=3, stress=84)
        tb.end_day(p, slept=True)
        assert p["fatigue_stacks"] == 0 and p["stress"] == 0
        assert p["day"] == 6 and p["day_blocks"] == 0
        print("PASS 7: sleep ends the day and clears fatigue + stress")

        # ── 8. Pande accrues (rev 3.5); Event Horizon suppresses ────────
        p = make_player(day_blocks=23, pandemonium_mode=True)
        tb.spend_blocks(p, 1)
        assert p["stress"] == 50 and p["fatigue_stacks"] == 0
        p = make_player(day_blocks=23, _eh_in_run=True,
                        event_horizon={"run_active": True})
        tb.spend_blocks(p, 1)
        assert p["fatigue_stacks"] == 0 and p["stress"] == 0
        print("PASS 8: stress accrues in Pandemonium; suppressed in Event Horizon")

        # ── 9. Dispatch checks on spend + rollover ─────────────────────
        p = make_player(dispatch={"active": []})
        dispatch_calls.clear()
        tb.spend_blocks(p, 1)
        assert dispatch_calls == [0], dispatch_calls
        dispatch_calls.clear()
        tb.advance_time(p, 5)          # zero-cost action (≤15 min)
        assert dispatch_calls == [0], dispatch_calls
        p2 = make_player(day_blocks=23, dispatch={"active": []})
        dispatch_calls.clear()
        tb.spend_blocks(p2, 1)
        assert dispatch_calls == [1], dispatch_calls
        print("PASS 9: dispatch resolution checks run on spends and rollovers")

        # ── 10. Wait: 1 block per use; until-morning marches (+fatigue) ──
        p = make_player(day_blocks=1)
        assert tb.wait_blocks(p, 1) == 0 and p["day_blocks"] == 2
        assert tb.wait_blocks(p) == 0 and p["day_blocks"] == 3
        p_wait = make_player(day_blocks=23)        # last block of the day
        assert tb.wait_blocks(p_wait, 1) == 1      # rolls the day, +50 stress
        assert (p_wait["day"], p_wait["day_blocks"]) == (6, 0)
        assert p_wait["fatigue_stacks"] == 0 and p_wait["stress"] == 50
        p_phase = make_player(day_blocks=4)
        assert tb.wait_to_next_phase(p_phase) == "noon"
        assert (p_phase["day"], p_phase["day_blocks"]) == (5, 8)
        p_night = make_player(day_blocks=18)
        assert tb.wait_to_next_phase(p_night) == "morning"
        assert (p_night["day"], p_night["day_blocks"]) == (6, 0)
        assert p_night["fatigue_stacks"] == 0 and p_night["stress"] == 50
        print("PASS 10: wait = 1 block; a-while = next phase (Night \u2192 morning +50 stress)")

        # ── 11. Phases + block track (24-block day, 8 per phase) ────────
        assert tb.get_day_phase(make_player(day_blocks=0)) == "morning"
        assert tb.get_day_phase(make_player(day_blocks=7)) == "morning"
        assert tb.get_day_phase(make_player(day_blocks=8)) == "noon"
        assert tb.get_day_phase(make_player(day_blocks=15)) == "noon"
        assert tb.get_day_phase(make_player(day_blocks=16)) == "night"
        assert tb.get_day_phase(make_player(day_blocks=23)) == "night"
        track = tb.format_block_track(make_player(day_blocks=3, day=12))
        assert "Morning" in track and "Day 12" in track
        assert track.count("▮") == 5 and track.count("▯") == 3, track
        sick = tb.format_block_track(make_player(fatigue_stacks=2))
        assert "FATIGUE II" in sick and "\U0001F441" in sick, sick
        print("PASS 11: phase mapping and block track (incl. fatigue display)")

        # ── 12. Service hours defaults + messages ───────────────────────
        morning = make_player(day_blocks=0)
        night = make_player(day_blocks=16)
        assert tb.is_service_open(morning, "shop", "solmere")
        assert not tb.is_service_open(night, "shop", "solmere")
        assert tb.is_service_open(night, "black_market", "solmere")
        assert not tb.is_service_open(morning, "black_market", "solmere")
        assert tb.is_service_open(morning, "guild", "solmere")
        assert tb.is_service_open(night, "guild", "solmere")
        assert not tb.is_service_open(morning, "star_tower", "skylume")
        assert tb.is_service_open(night, "star_tower", "skylume")
        assert tb.is_service_open(night, "inn", "solmere")
        assert tb.is_service_open(night, "port", "solmere")   # night sailings
        msg = tb.service_closed_message(night, "shop", "solmere")
        assert msg and "tomorrow morning" in msg, msg
        msg2 = tb.service_closed_message(morning, "black_market", "solmere")
        assert msg2 and "night" in msg2, msg2
        print("PASS 12: service hours defaults + closed messages")

        # ── 13. Per-city hours override ─────────────────────────────────
        CITIES["testville"] = {"service_hours": {"shop": ["night"]}}
        try:
            assert tb.is_service_open(night, "shop", "testville")
            assert not tb.is_service_open(morning, "shop", "testville")
        finally:
            CITIES.pop("testville", None)
        print("PASS 13: per-city hours override")

        # ── 14. Wonderland time pocket ──────────────────────────────────
        p = make_player(wonderland_active=True, day_blocks=5)
        assert tb.spend_blocks(p, 3) == 0
        assert p["day_blocks"] == 5 and p["day"] == 5
        tb.end_day(p, slept=False)
        assert p["day"] == 5 and p["day_blocks"] == 5
        assert tb.wait_blocks(p, 1) == 0 and p["day_blocks"] == 5
        assert tb.wait_to_next_phase(p) is None and p["day"] == 5
        assert tb.format_block_track(p) == ""        # no track in the pocket
        assert tb.is_service_open(p, "black_market", "solmere")   # hours bypassed
        assert tb.is_service_open(p, "shop", "solmere")
        print("PASS 14: Wonderland nullifies costs, preserves the day, hides the clock")

        # ── 15. Legacy migration runs once ──────────────────────────────
        p = {"day": 5, "time_minutes": 1234}
        tb.migrate_legacy_time_to_blocks(p)
        assert p["day_blocks"] == 20 and p["time_blocks_migrated"] is True
        p2 = {"day": 5, "time_minutes": 1234, "day_blocks": 2,
              "time_blocks_migrated": True}
        tb.migrate_legacy_time_to_blocks(p2)
        assert p2["day_blocks"] == 2
        p_fresh = {"day": 1, "time_minutes": 480}
        tb.migrate_legacy_time_to_blocks(p_fresh)
        assert p_fresh["day_blocks"] == 0
        print("PASS 15: legacy save migration (day 1 → morning; once only)")

        # ── 16. Block-model advance_time ────────────────────────────────
        p = make_player()
        spy.calls.clear()
        tb.advance_time(p, 60)
        assert p["day_blocks"] == 1
        tb.advance_time(p, tb.DAY_MINUTES * 2 + 60)
        assert p["day"] == 7 and p["day_blocks"] == 0
        assert p["fatigue_stacks"] == 1 and p["stress"] == 0
        assert len(spy.calls) == 2
        p_wl = make_player(wonderland_active=True)
        assert isinstance(tb.advance_time(p_wl, 999), str)
        print("PASS 16: block-model advance_time (incl. whole-day skips)")

        # ── 17. Fatigue accessors ───────────────────────────────────────
        assert tb.get_fatigue_penalty(make_player(fatigue_stacks=2)) == -2
        assert tb.get_fatigue_stacks(make_player(fatigue_stacks=99)) == tb.MAX_FATIGUE
        print("PASS 17: fatigue accessors")

        # ── 18. Travel pricing (rev 3.2: +2 supply overhead) ────────────
        tbf = tb.travel_blocks_for
        assert tbf(0) == 0 and tbf(10) == 3            # min 1 + 2 supply
        assert tbf(30) == 3 and tbf(31) == 4 and tbf(40) == 4
        assert tbf(60) == 4 and tbf(90) == 5 and tbf(220) == 10
        # Mounts: tier // 2 shave, floor at 1
        assert tbf(60, mount_tier=1) == 4
        assert tbf(60, mount_tier=2) == 3
        assert tbf(60, mount_tier=4) == 2
        assert tbf(100, mount_tier=2) == 5
        assert tbf(100, mount_tier=4) == 4
        assert tbf(220, mount_tier=4) == 8
        # Rain: +1 / +2; tier 3+ ignore plain rain, heavy rain only +1
        assert tbf(90, 0, 1) == 6 and tbf(90, 0, 2) == 7
        assert tbf(90, 3, 1) == 4 and tbf(90, 3, 2) == 5
        assert tbf(90, 4, 1) == 3 and tbf(90, 4, 2) == 4
        # Player-aware wrapper (mount tier + rain level)
        p_horse = make_player(mount_id="horse",
                              daily_effects={"rain_level": 2})
        assert tb.travel_blocks(p_horse, 100) == 7     # 4+2 -1 +2
        p_cara = make_player(mount_id="caravan",
                             daily_effects={"rain_level": 2})
        assert tb.travel_blocks(p_cara, 100) == 5      # 4+2 -2 +1
        assert tb.travel_blocks(make_player(), 90) == 5
        # Legacy multiplier fallback for the rain level
        p_legacy = make_player(daily_effects={"travel_time_mult": 1.4})
        assert tb.travel_rain_level(p_legacy) == 2
        assert tb.travel_rain_level(make_player()) == 0
        print("PASS 18: travel pricing (+2 supply, mount shave, rain)")

        print("\nAll block-time engine diagnostics passed.")
    finally:
        events.process_day_rollover = real_rollover
        guild_mod.check_bounty_expiry = real_bounty
        billing_mod.process_monthly_billing = real_billing
        dispatch_mod.process_dispatch_progress = real_dispatch


if __name__ == "__main__":
    main()
