# Temp check (2026-11-08): superboss UI cleanup.
#
# Playtest report: superbosses printed their own terminal headers
# ("⚔️ Round 1: Action Phase", "  >> ROUND 1" without floor/time), dumped
# gimmick explainers into the 3-line combat strip, and wrapped narration in
# "====!" banners that ate the message rows.
#
# Run: .venv\Scripts\python.exe tests\_temp_superboss_ui_check.py
import re
import sys
import tkinter as tk
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from gui.screens.combat_screen import CombatScreen, GUICombatIO   # noqa: E402


class FakeSM:
    def __init__(self):
        self.player = {"name": "Tester", "allies": [], "party_order": [],
                       "attributes": {"Speed": 10}}
        self.logs = []

    def clear_log(self, *a, **k):
        pass

    def update_top_bar(self, *a, **k):
        pass

    def log(self, message, category="system"):
        self.logs.append((category, message))


class TestCombatScreen(CombatScreen):
    def _start_combat(self):
        pass

    def _refresh_hud(self):
        pass


# Superboss modules that print combat text.
BOSS_FILES = [
    "big_bad_wolf", "black_silence", "broodmother", "entangled_chrysalis",
    "everlong_ship", "ignis", "jabberwock", "mary_sue",
    "palette_chromatic_artisan", "queen_of_hearts", "rientrante",
    "slitcurrent", "sylvana", "white_knight", "wicked_witch", "yinglong",
    "superboss_common",
]


def main():
    root = tk.Tk()
    root.geometry("1x1+0+0")
    container = tk.Frame(root)
    container.pack()
    sm = FakeSM()
    screen = TestCombatScreen(container, sm)

    # 1. Every superboss runs the shared loop, and the loop now prints the
    #    standard round header (floor + time) instead of "  >> ROUND n".
    src = (ROOT / "combat" / "superboss_common.py").read_text(encoding="utf-8")
    assert "print_round_header(round_num" in src, \
        "superboss loop still uses its own round header"
    assert 'c_print(f"  >> ROUND {round_num}")' not in src, \
        "bare '>> ROUND n' header is still printed"
    assert "Round {round_num}: Action Phase" not in src, \
        "superboss loop still prints its own action-phase header"
    assert '⚔️  ROUND {round_num}: ACTION PHASE' in src, \
        "superboss action-phase header should match the standard engine"
    # The header carries the phase track, not the retired HH:MM clock.
    for rel in ("combat/superboss_common.py", "combat/combat_engine.py"):
        text = (ROOT / rel).read_text(encoding="utf-8")
        assert "current_time_label(player)" in text, f"{rel} still uses the old clock"
        assert "time_str = format_time(" not in text, f"{rel} still uses format_time"
    ui = (ROOT / "combat" / "combat_ui.py").read_text(encoding="utf-8")
    assert 'parts.append(f"Time: {time_str}")' not in ui, \
        "round header still labels the clock as 'Time:'"
    users = [p.stem for p in (ROOT / "combat").glob("*.py")
             if "superboss_combat_loop" in p.read_text(encoding="utf-8")]
    assert len(users) >= 17, f"expected 17 superboss modules, found {sorted(users)}"
    print(f"OK — {len(users)} superboss modules share the standard round header")

    # 2. No boss module prints a decorative divider any more.
    border_re = re.compile(r'c_print\([^)]*"[=!~─═\-]" \* \d+')
    offenders = []
    for name in BOSS_FILES:
        text = (ROOT / "combat" / f"{name}.py").read_text(encoding="utf-8")
        if border_re.search(text):
            offenders.append(name)
    assert not offenders, f"divider prints remain in {offenders}"
    print("OK — no '!!!' / '===' / '───' dividers left in superboss files")

    # 3. The GUI bridge drops divider lines even if a module still prints one.
    io = GUICombatIO()
    io.pacer.before_print = lambda text: None
    io.pacer.after_print = lambda text: None
    io.print("=" * 60)
    io.print("\n" + "!" * 50)
    io.print("─" * 50)
    assert io.output_queue.empty(), "border lines reached the GUI queue"
    io.print("\n⚙ [GIMMICK] Mirror Reflection!")
    assert not io.output_queue.empty(), "real output was swallowed"
    kind, text = io.output_queue.get_nowait()
    assert kind == "OUTPUT" and "GIMMICK" in text, (kind, text)
    print("OK — dividers are dropped at the bridge, real lines are kept")

    # 4. Gimmick banners pin in the strip, survive the turn sweep, and reach
    #    the session log; explaining lines stay normal feed lines.
    screen._handle_output("\n⚙ [GIMMICK] Mirror Reflection! Sylvana fractures into an illusory copy!")
    screen._handle_output("One of them is the REAL Sylvana. The copies bear subtly wrong names.")
    txt = screen.ticker_label.cget("text")
    assert "[GIMMICK] Mirror Reflection!" in txt, f"gimmick not pinned: {txt!r}"
    screen._handle_output("[1/4] Umbra Weaver's Turn:")
    screen._handle_output("[1/4] Critical hit! Umbra Weaver → Sylvana: 214 dmg")
    txt = screen.ticker_label.cget("text")
    assert "[GIMMICK] Mirror Reflection!" in txt, \
        f"gimmick banner was swept by the action feed: {txt!r}"
    body = [m for c, m in sm.logs if "GIMMICK" in m]
    assert body, "gimmick banner was not mirrored to the session log"
    print("OK — gimmick banner pinned in the strip + mirrored to the log")

    # 5. Phase tags are recognised too, and the banner clears at combat end.
    for tag in ("[PHASE 2] The 'ice' cracks like broken glass.",
                "[FINAL FORM] Sylvana screams.",
                "[GIMMICK] All data fragments purged!"):
        assert screen._is_gimmick_line(tag), tag
    assert not screen._is_gimmick_line("[1/4] Critical hit! Umbra → Sylvana: 9 dmg")
    screen.on_result = lambda result: None
    screen._handle_result("victory")
    txt = screen.ticker_label.cget("text")
    assert "GIMMICK" not in txt, f"gimmick banner survived combat end: {txt!r}"
    assert "VICTORY" in txt.upper(), txt
    print("OK — gimmick banner clears at combat end")

    screen.destroy()
    root.update()
    root.destroy()
    print("\nAll superboss UI checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
