"""Repro for: TclError "invalid command name ...!button" in CombatScreen._handle_result.

Simulates the training-dummy flow (CityScreen -> `switch_to(CombatScreen, ...)`)
where the `on_result` callback synchronously destroys the CombatScreen before
`_handle_result` has finished updating its widgets.  Any widget access after
the synchronous teardown (e.g. continue_btn.config) raises TclError.
"""
import sys
import tkinter as tk
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gui.screens.combat_screen import CombatScreen


class FakeSM:
    """Minimal screen-manager stand-in for widget construction."""

    def __init__(self):
        self.player = {
            "name": "Tester",
            "allies": [],
            "party_order": [],
            "attributes": {"Speed": 10},
        }

    def clear_log(self, *a, **k):
        pass

    def update_top_bar(self, *a, **k):
        pass

    def log(self, *a, **k):
        pass


class TestCombatScreen(CombatScreen):
    """CombatScreen without starting a real combat thread."""

    def _start_combat(self):
        pass

    def _refresh_hud(self):
        """HUD rendering needs a full player dict — not part of this repro."""
        pass


def main():
    root = tk.Tk()
    root.withdraw()
    errors = []
    root.report_callback_exception = lambda exc, val, tb: errors.append(f"{exc.__name__}: {val}")

    container = tk.Frame(root)
    container.pack()

    screen = TestCombatScreen(container, FakeSM())

    # The training-dummy flow: on_result synchronously tears the screen down
    # (CityScreen._after_dummy_combat -> ScreenManager.switch_to -> destroy).
    screen.on_result = lambda result: screen.destroy()

    screen.after(0, lambda: screen._handle_result("victory"))
    root.update()

    if errors:
        print("BUG REPRODUCED — exceptions escaped from a destroyed screen:")
        for e in errors:
            print("  " + e)
        root.destroy()
        return 1

    # ── Regression checks ────────────────────────────────────────────────
    # 1. The normal overlay flow (on_result does NOT destroy the screen)
    #    must still show the "Leave Battle" button.
    screen2 = TestCombatScreen(container, FakeSM())
    screen2.on_result = lambda result: None  # overlay flow: queue put
    screen2.after(0, lambda: screen2._handle_result("victory"))
    root.update()
    if screen2.continue_btn.winfo_manager() == "pack" and screen2.continue_btn.cget("text") == "▶ Leave Battle":
        print("OK — Leave Battle button still shown in the overlay flow")
    else:
        print("FAIL — overlay flow no longer shows the Leave Battle button")
        print(f"  manager={screen2.continue_btn.winfo_manager()!r} "
              f"text={screen2.continue_btn.cget('text')!r} "
              f"destroyed={screen2._destroyed} "
              f"alive={screen2._widgets_alive()} "
              f"errors={errors}")
        root.destroy()
        return 1
    screen2.destroy()

    # 2. A stale _poll must stop when the widget tree is gone even if the
    #    _destroyed flag was never set (Tcl-level teardown path).
    screen3 = TestCombatScreen(container, FakeSM())
    tk.Frame.destroy(screen3)  # bypasses CombatScreen.destroy / _cancel_polls
    screen3._poll()
    if screen3._destroyed:
        print("OK — stale poll detected the dead widget tree and stopped")
    else:
        print("FAIL — stale poll kept running on a dead widget tree")
        root.destroy()
        return 1

    root.destroy()

    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
