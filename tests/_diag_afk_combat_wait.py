"""Diagnostic: DungeonScreen._await_combat_result — no AFK kick, deadlock safety.

Verifies the 2026-10-13 change that removed the fixed 300s/600s/1200s
deadlock timeouts from gui/screens/dungeon_screen.py:

  1. A combat sitting parked on an input prompt (idle player) must NEVER
     abort the run — the result is delivered no matter how long it takes.
  2. If the battle screen vanishes without delivering a result (its thread
     died silently, screen torn down), the dungeon thread must still unblock
     ("timeout") so the run isn't hung forever.

Run from repo root with:
    .venv\\Scripts\\python.exe tests\\_diag_afk_combat_wait.py
"""
import queue
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import gui.screens.dungeon_screen as ds
import gui.screens.combat_screen as cs


# ── Stand-ins ─────────────────────────────────────────────────────────────

class FakeCombatScreen:
    """Matches the isinstance() check in _await_combat_result."""


class FakeRoot:
    def __init__(self):
        self.scheduled = []

    def after(self, delay, func=None, *args):
        self.scheduled.append(func)
        return "fake-id"


class FakeSM:
    def __init__(self):
        self.top = None
        self.root = FakeRoot()

    def get_top_screen(self):
        return self.top

    def dismiss_overlay(self):
        pass


class Stub:
    """Carries the real method; _append_output captured for assertions."""

    _await_combat_result = ds.DungeonScreen._await_combat_result

    def __init__(self):
        self.sm = FakeSM()
        self.output = []

    def _append_output(self, text):
        self.output.append(text)


class FakeTime:
    """Monotonic clock that jumps 20s per call to keep the test fast."""

    def __init__(self):
        self.t = 0.0

    def monotonic(self):
        self.t += 20.0
        return self.t


def main():
    real_combat = cs.CombatScreen
    cs.CombatScreen = FakeCombatScreen  # patch before importing callers
    try:
        # ── 1. Idle player parked on an input prompt: never kicked ───────
        stub = Stub()
        q = queue.Queue()
        stub.sm.top = FakeCombatScreen()

        def deliver_late():
            time.sleep(1.5)  # far beyond the 0.5s poll interval — "AFK"
            q.put("victory")

        t = threading.Thread(target=deliver_late, daemon=True)
        t.start()
        result = stub._await_combat_result(q, "Combat")
        t.join(timeout=5)
        assert result == "victory", f"expected victory, got {result!r}"
        assert not stub.output, f"idle wait must not abort: {stub.output}"
        print("PASS 1: idle player kept the fight open until the result arrived")

        # ── 2. Battle screen vanished without a result → deadlock abort ──
        stub2 = Stub()
        q2 = queue.Queue()
        stub2.sm.top = FakeCombatScreen()  # overlay is up (helper sees it
        #                                    during its first poll)...
        def vanish_after_seen():
            time.sleep(0.8)
            stub2.sm.top = None            # ...then it vanishes, no result

        threading.Thread(target=vanish_after_seen, daemon=True).start()

        real_time = ds.time
        ds.time = FakeTime()
        try:
            result2 = stub2._await_combat_result(q2, "Combat")
        finally:
            ds.time = real_time

        assert result2 == "timeout", f"expected timeout, got {result2!r}"
        assert any("vanished" in o for o in stub2.output), stub2.output
        assert stub2.sm.root.scheduled, "overlay dismissal was not scheduled"
        print("PASS 2: vanished battle screen still unblocks with 'timeout'")

        # ── 3. Startup grace: overlay not yet built → no instant abort ───
        stub3 = Stub()
        q3 = queue.Queue()  # top stays None from the very first poll

        def deliver_after_startup():
            time.sleep(1.0)  # overlay "constructor" just being slow
            q3.put("fled")

        t3 = threading.Thread(target=deliver_after_startup, daemon=True)
        t3.start()
        result3 = stub3._await_combat_result(q3, "Combat")
        t3.join(timeout=5)
        assert result3 == "fled", f"expected fled, got {result3!r}"
        assert not stub3.output, f"slow startup must not abort: {stub3.output}"
        print("PASS 3: slow overlay startup did not trigger a false abort")

        print("\nAll _await_combat_result diagnostics passed.")
    finally:
        cs.CombatScreen = real_combat


if __name__ == "__main__":
    main()
