"""Diag: boss-intro paging + deferred ending dialogue (2026-11-10).

Playtest report: the arena scene plays in the dungeon log, then the
superboss intro dumps ~20 prose lines into the combat log — but the combat
screen only has a 3-line ticker, so the two scenes competed and the intro
was unreadable without opening the popup.

Fix under test:
  1. The first Continue prompt of a fight reveals the intro prose in
     3-line pages (one page per Continue press).
  2. Heroine ending prose is deferred to the dungeon screen via
     combat_ui.defer_dialogue (played by dungeon._play_deferred_dialogue).
  3. Wild-dungeon entry clears the previous run's dungeon log.

Run:
    .venv\\Scripts\\python.exe tests\\_diag_combat_intro_pages.py
"""
import sys
import tkinter as tk
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from gui.screens.combat_screen import CombatScreen            # noqa: E402
from combat.combat_ui import defer_dialogue, take_deferred_dialogue  # noqa: E402


class FakeSM:
    """Minimal screen-manager stand-in for widget construction."""

    def __init__(self):
        self.player = {"name": "Tester", "allies": [], "party_order": [],
                       "attributes": {"Speed": 10}}

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
        pass

    def _schedule_poll(self):
        pass


class FakeIO:
    """Captures the values the screen would send to the engine thread."""

    def __init__(self):
        self.sent = []
        self.stopped = False

    def send_input(self, text):
        self.sent.append(text)

    def stop(self):
        self.stopped = True


def _shown_lines(screen):
    return [l for l in screen.log_text.get("1.0", "end-1c").splitlines() if l.strip()]


def main():
    root = tk.Tk()
    root.geometry("1x1+0+0")
    container = tk.Frame(root)
    container.pack()
    screen = TestCombatScreen(container, FakeSM())
    io = FakeIO()
    screen.io = io

    # ── 1. A long intro is revealed 3 lines at a time ──────────────────
    intro = [f"Intro line {i:02d}" for i in range(1, 14)]  # 13 lines → 5 pages
    for line in intro:
        screen._handle_output(line)

    screen._handle_input_needed("Press Enter to face the Witch...")
    assert _shown_lines(screen) == intro[:3], _shown_lines(screen)
    label = screen.continue_btn.cget("text")
    assert "Continue" in label and "1/5" in label, label
    assert not io.sent, "engine must stay blocked until every page is read"
    print("OK — page 1/5 shown, engine still blocked")

    for shown_count, page in ((6, "2/5"), (9, "3/5"), (12, "4/5")):
        screen._on_continue_click()
        assert _shown_lines(screen) == intro[:shown_count], _shown_lines(screen)
        assert page in screen.continue_btn.cget("text"), screen.continue_btn.cget("text")
        assert not io.sent, io.sent
        print(f"OK — Continue revealed page {page}")

    screen._on_continue_click()  # final page (1 line)
    assert _shown_lines(screen) == intro, _shown_lines(screen)
    assert screen.continue_btn.cget("text").strip() == "▶ Continue", \
        screen.continue_btn.cget("text")
    assert not io.sent, "the last page still waits for its own Continue"
    screen._on_continue_click()
    assert io.sent == [""], io.sent
    print("OK — last page then Enter sent to the engine")

    # ── 2. Only the FIRST prompt paginates ─────────────────────────────
    for line in ("Round output 1", "Round output 2", "Round output 3",
                 "Round output 4", "Round output 5"):
        screen._handle_output(line)
    screen._handle_input_needed("Press Enter to start the round...")
    assert screen._narration_pages == [], "round prompts must not re-page the feed"
    assert "/" not in screen.continue_btn.cget("text"), screen.continue_btn.cget("text")
    screen._on_continue_click()
    assert io.sent == ["", ""], "round prompts must send input on the first click"
    print("OK — later 'Press Enter' prompts send input immediately")

    # ── 3. Short intros keep the plain single Continue ─────────────────
    root2 = tk.Tk()
    root2.geometry("1x1+0+0")
    cont2 = tk.Frame(root2)
    cont2.pack()
    screen2 = TestCombatScreen(cont2, FakeSM())
    io2 = FakeIO()
    screen2.io = io2
    screen2._handle_output("Enemies approach!")
    screen2._handle_output("Intro line A")
    screen2._handle_input_needed("Press Enter to begin...")
    assert screen2._narration_pages == []
    assert screen2.continue_btn.cget("text").strip() == "▶ Continue"
    screen2._on_continue_click()
    assert io2.sent == [""], io2.sent
    screen2.destroy()
    root2.update()
    root2.destroy()
    print("OK — short intro keeps the single Continue")

    # ── 4. Deferred dialogue queue roundtrip ───────────────────────────
    player = {}
    defer_dialogue(player, ["first"], title="Dorothy")
    defer_dialogue(player, ["second", "third"])
    payload = take_deferred_dialogue(player)
    assert payload == {"title": "Dorothy", "lines": ["first", "second", "third"]}, payload
    assert take_deferred_dialogue(player) is None, "payload must not survive a second take"
    print("OK — deferred dialogue queue roundtrip")

    # ── 5. Wiring: dungeon plays it, wild entry clears the log ─────────
    dungeon_src = (ROOT / "dungeon.py").read_text(encoding="utf-8")
    assert "_play_deferred_dialogue(player)" in dungeon_src, \
        "Wonderland dispatch no longer plays deferred dialogue"
    wild_src = (ROOT / "gui" / "screens" / "world_map_screen.py").read_text(encoding="utf-8")
    assert 'player.pop("_dungeon_log", None)' in wild_src, \
        "wild-dungeon entry still inherits the previous run's log"
    for rel in ("combat/big_bad_wolf.py", "combat/wicked_witch.py",
                "combat/jabberwock.py", "combat/mary_sue.py"):
        text = (ROOT / rel).read_text(encoding="utf-8")
        assert "defer_dialogue(" in text, f"{rel} still prints its ending in combat"
        assert "becomes a" in text and "ally." in text, \
            f"{rel} lost its promotion line"
    print("OK — ending prose is deferred and wild runs start with a clean log")

    screen.destroy()
    root.update()
    root.destroy()
    print("\nAll intro paging / deferred dialogue checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
