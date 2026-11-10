"""Diag: combat ticker + log popup + turn/hit flashes (2026-10-04).

The always-visible Combat Log pane was removed (it cost ~114px of vertical
budget and 5-enemy fights clipped the HUD). The full log now lives in a
hidden Toplevel; a one-line ticker shows the latest event. This script
verifies the new wiring without starting a real combat thread.

Run:
    .venv\\Scripts\\python.exe tests\\_diag_combat_ticker.py
"""
import sys
import tkinter as tk
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gui.screens.combat_screen import CombatScreen
from gui.theme import Theme


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
        """HUD rendering needs a full player dict — not part of this test."""
        pass


def main():
    # NOTE: the root must be mapped for the popup's WM state to update —
    # a withdrawn root leaves deiconified Toplevels reporting "withdrawn".
    root = tk.Tk()
    root.geometry("1x1+0+0")
    errors = []
    root.report_callback_exception = lambda exc, val, tb: errors.append(f"{exc.__name__}: {val}")

    container = tk.Frame(root)
    container.pack()
    screen = TestCombatScreen(container, FakeSM())

    # 1. Popup exists but stays hidden; ticker starts blank.
    assert screen.log_window.winfo_exists(), "log popup missing"
    root.update()
    assert screen.log_window.state() == "withdrawn", \
        f"log popup should start hidden, got {screen.log_window.state()!r}"
    assert not screen.ticker_label.cget("text").strip(), "ticker should start blank"
    print("OK — popup hidden, ticker blank")

    # 2. The feed shows the recent lines (not just the last one).
    screen._append_log(">> ROUND 2")
    screen._append_log("✦ pins dig deeper — 11 damage!")
    screen._append_log("♥ Sunfire Band +5 [Bonded] — attacks leave a 3-turn Burn.")
    txt = screen.ticker_label.cget("text")
    assert "pins dig deeper" in txt and "Sunfire Band" in txt, f"feed missing lines: {txt!r}"
    assert "ROUND" not in txt, f"round header leaked into the feed: {txt!r}"
    print("OK — feed shows recent lines (round header excluded)")

    # 2b. A skill line pins its description as the banner and survives results.
    screen._append_log(">>> Sunfire Breath: Exhale a cone of searing flame")
    screen._append_log("Ninetales Fox → Wolf: 30 dmg [FIRE]")
    txt = screen.ticker_label.cget("text")
    assert txt.startswith("▶") and "Sunfire Breath" in txt, f"banner missing: {txt!r}"
    assert txt.count("Sunfire Breath") == 1, f"banner duplicated in feed: {txt!r}"
    print("OK — skill banner pinned")

    # 2c. Two-line mastery prints (Jade pins + bonus line) both reach the feed.
    screen._append_log("\n  ⚡ prism Tarnished Jade's 2 pins dig deeper — 11 damage!")
    screen._append_log("  (+0 STR, +0 WIS from the embedded pins)")
    txt = screen.ticker_label.cget("text")
    assert "dig deeper" in txt and "embedded pins" in txt, \
        f"mastery lines split: {txt!r}"
    print("OK — two-line mastery prints stay together in the feed")

    # 3. The popup toggles via repeated clicks (no need for the X).
    screen.open_log_popup()
    root.update()
    assert screen.log_window.state() == "normal", "popup should open"
    screen.open_log_popup()
    root.update()
    assert screen.log_window.state() == "withdrawn", "second click should hide the popup"
    screen.open_log_popup()
    root.update()
    assert screen.log_window.state() == "normal", "popup should reopen"
    screen._close_log_popup()
    root.update()
    assert screen.log_window.state() == "withdrawn"
    print("OK — popup toggles open/closed")

    # 4. _clear_log resets feed + banner.
    screen._clear_log()
    assert not screen.ticker_label.cget("text").strip(), "ticker not cleared"
    print("OK — clear resets ticker")

    # 4b. Overlong content trims from the top, keeping the newest tail.
    screen._append_log("x" * 900)
    txt = screen.ticker_label.cget("text")
    assert txt.startswith("\u2026"), f"expected tail-trim marker: {txt[:24]!r}"
    print("OK — overlong feed trims to the newest tail")

    # 5. Turn headers flash the actor and clear only the banner.
    screen._append_log(">>> Some Skill: does things")
    screen._handle_output("[2/9] Alice's Turn:")
    assert screen._turn_step_prefix == "[2/9]"
    assert "\u25b6" not in screen.ticker_label.cget("text"), \
        "turn header should clear the banner"
    screen._handle_output("Ninetales Fox [Sunfire Breath] → Alice: 87 dmg [FIRE]")
    assert "87 dmg" in screen.ticker_label.cget("text")
    print("OK — turn/damage lines wired to flash + ticker")

    # 5b. ALL action results survive the next turn header; the new
    #     combatant's first action line then sweeps the previous actor's feed.
    screen._append_log("  ↳ Alice is reeling!")  # non-damage action line
    screen._handle_output("[3/9] Bob's Turn:")
    txt = screen.ticker_label.cget("text")
    assert "87 dmg" in txt, f"damage line should survive the turn header: {txt!r}"
    assert "reeling" in txt, \
        f"non-damage action lines should persist too: {txt!r}"
    screen._handle_output("Bob [Cleave] → Alice: 40 dmg [PHYS]")
    txt = screen.ticker_label.cget("text")
    assert "40 dmg" in txt and "87 dmg" not in txt and "reeling" not in txt, \
        f"new actor's first action should sweep the old feed: {txt!r}"
    print("OK — action lines persist until the next combatant acts")

    # 5c. Same-actor multi-hits accumulate instead of overriding each other.
    screen._handle_output("Bob [Cleave] → Alice: 12 dmg [PHYS]")
    txt = screen.ticker_label.cget("text")
    assert "40 dmg" in txt and "12 dmg" in txt, f"multi-hits should accumulate: {txt!r}"
    print("OK — same-actor multi-hits accumulate in the feed")

    # 5d. Evasion results persist across the next turn header — a blinded
    #     attacker's dodge line used to flash for one pacing beat and get
    #     swept before it could be read (2026-10-08 bug report).
    screen._handle_output("The Wolf dodges Bob's attack!")
    txt = screen.ticker_label.cget("text")
    assert "dodges" in txt, f"evasion line missing after output: {txt!r}"
    screen._handle_output("[4/9] Carol's Turn:")
    txt = screen.ticker_label.cget("text")
    assert "dodges" in txt, f"evasion line should survive the turn header: {txt!r}"
    print("OK — evasion results persist across turn headers")

    # 6. flash_entity matches cards via the frame cache (use the real path).
    rend = screen.renderer
    rend._refresh_column(rend.party_col,
                         [{"name": "Alice", "hp": 10, "max_hp": 10, "buff_tags": ""}],
                         rend._party_frames)
    assert rend.flash_entity("Nobody") is False
    assert rend.flash_entity("Alice") is True
    assert rend.flash_entity("alice", kind="hit", party_only=True) is True
    rend._refresh_column(rend.enemy_col,
                         [{"name": "Wolf", "hp": 10, "max_hp": 10, "buff_tags": ""}],
                         rend._enemy_frames)
    assert rend.flash_entity("Wolf", party_only=True) is False, \
        "party_only flash must not touch enemy cards"
    print("OK — flash_entity matching works")

    # 6b. Turn-order bar highlights the acting actor.
    turn_order = [{"label": "You"}, {"label": "Alice"}, {"label": "[5] World Serpent"}]
    rend._update_turn_order(turn_order, "World Serpent")
    fgs = {norm: w.cget("fg") for norm, w in rend._turn_order_tokens}
    # Tokens keep the enemy's [N] index; the bare-name fallback still finds
    # the unique match.
    assert fgs.get("[5] world serpent") == Theme.ACCENT, fgs
    assert fgs.get("you") == Theme.TEXT_DIM, fgs
    rend._update_turn_order(turn_order, "Alice")
    fgs = {norm: w.cget("fg") for norm, w in rend._turn_order_tokens}
    assert fgs.get("alice") == Theme.ACCENT, fgs
    assert fgs.get("[5] world serpent") == Theme.TEXT_DIM, fgs
    print("OK — turn order highlights the acting actor")

    # 6c. The turn-order preview uses the MC's full name (engine label parity,
    #     no 8-char truncation) — the engine and the preview used to disagree
    #     (name vs "You"), flipping the card mid-fight (2026-10-08 report).
    preview = screen._compute_turn_order()
    assert preview and preview[0]["label"] == "Tester", preview
    print("OK — turn-order preview uses the MC's name")

    # 7. Combat end: the result lands on a clean feed (leftovers swept).
    screen._append_log("✦ leftover action line")
    screen.on_result = lambda result: None
    screen._handle_result("victory")
    txt = screen.ticker_label.cget("text")
    assert "VICTORY" in txt.upper()
    assert "leftover" not in txt, f"end-of-fight should clear leftovers: {txt!r}"
    assert str(screen.log_btn.cget("bg")).lower() == str(Theme.ACCENT).lower(), \
        f"log button not highlighted: {screen.log_btn.cget('bg')!r}"
    print("OK — end-of-fight shows the victory line on a clean feed")

    # 8. The popup dies with the screen (child Toplevel teardown).
    screen.destroy()
    root.update()
    assert not screen.log_window.winfo_exists(), "popup outlived the screen"
    print("OK — popup destroyed with the screen")

    if errors:
        print("FAILURES — exceptions escaped:")
        for e in errors:
            print("  " + e)
        root.destroy()
        return 1

    root.destroy()
    print("\nAll combat ticker checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
