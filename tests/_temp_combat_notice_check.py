# Temp check (2026-11-05): combat notices survive turn sweeps + combat end.
#
# Repro: capturing the last enemy in Voss's "A Place to Belong" ended the
# fight instantly; _handle_result wiped the 3-line ticker, so the capture
# message, quest completion and follow-up quest never showed.
#
# Run: .venv\Scripts\python.exe tests\_temp_combat_notice_check.py
import sys
import tkinter as tk
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gui.screens.combat_screen import CombatScreen


class FakeSM:
    def __init__(self):
        self.player = {
            "name": "Tester",
            "allies": [],
            "party_order": [],
            "attributes": {"Speed": 10},
        }
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


# The exact burst printed by attempt_capture() + update_quests().
CAPTURE_BURST = [
    "The Harpy Scout squawks in surprise, then softens as she lands beside you.",
    "(The Stellar Field Kit's weave closes.)",
    "💕 Harpy Scout has been added to your house in Skylume!",
    "📜 Quest complete: A Place to Belong",
    "   +200 XP",
    "   Command Resonance — new grade: Pitch",
    "📜 New Main Quest: A Willing Bond",
]


def main():
    root = tk.Tk()
    root.geometry("1x1+0+0")
    errors = []
    root.report_callback_exception = lambda exc, val, tb: errors.append(
        f"{exc.__name__}: {val}")

    container = tk.Frame(root)
    container.pack()
    screen = TestCombatScreen(container, FakeSM())

    # 1. Classification: quest/capture lines are notices; flavour is not.
    assert screen._is_notice_line("📜 Quest complete: A Place to Belong")
    assert screen._is_notice_line("📜 New Main Quest: A Willing Bond")
    assert screen._is_notice_line("💕 Harpy Scout has been added to your house in Skylume!")
    assert screen._is_notice_line("  ✦ You obtained: ABYSS FANG (Unique) ✦")
    assert screen._is_notice_line("   +200 XP")
    assert screen._is_notice_line("   +80 gold")
    assert screen._is_notice_line("   Command Resonance — new grade: Pitch")
    assert screen._is_notice_line("   Received: Cracked Orb")
    # Capture FAILURE feedback is an action line, not a pinned notice.
    assert not screen._is_notice_line("The Slime Girl slips through your net and escapes!")
    assert not screen._is_notice_line("You need a Capture Net to attempt this!")
    assert not screen._is_notice_line("No capturable monster girls present.")
    assert not screen._is_notice_line("Ninetales Fox → Wolf: 30 dmg")
    assert not screen._is_notice_line("The Harpy Scout squawks in surprise.")
    print("OK — notice classification")

    # 2. Notices pin in the ticker and never get a turn prefix.
    for line in CAPTURE_BURST:
        screen._append_log(line)
        screen._handle_output(line)
    txt = screen.ticker_label.cget("text")
    assert "📜 New Main Quest: A Willing Bond" in txt, f"latest notice missing: {txt!r}"
    assert "[1/" not in txt, f"notice got a turn prefix: {txt!r}"
    # 💕 house join + 📜 complete + +XP + grade + 📜 next quest
    assert len(screen._notices) == 5, screen._notices
    assert any("Quest complete: A Place to Belong" in m for _, m in screen.sm.logs), \
        "quest completion missing from the session log"
    print("OK — notices pinned in feed, no turn prefix, mirrored to session log")

    # 3. A turn header must NOT sweep the pinned notice.
    screen._handle_output("[1/4] Tester's Turn:")
    txt = screen.ticker_label.cget("text")
    assert "📜 New Main Quest: A Willing Bond" in txt, \
        f"turn header swept the notice: {txt!r}"
    print("OK — notice survives the turn sweep")

    # 3b. Round-start CLEAR resets the ticker but keeps the fight history
    #     (c_clear() runs every round in the engine; wiping the GUI log here
    #     used to hide every earlier round, including capture failures).
    screen._handle_output("[1/4] Tester's Turn:")
    screen._handle_output("The Slime Girl slips through your net and escapes!")
    assert "slips through your net" in screen.ticker_label.cget("text")
    screen._handle_output("[2/4] Wolf's Turn:")
    assert "slips through your net" in screen.ticker_label.cget("text"), \
        "failed capture should persist as an action line through the header"
    root.update_idletasks()
    before = screen.log_text.get("1.0", "end-1c")
    assert "slips through your net" in before, before
    screen._reset_round_feed()
    after = screen.log_text.get("1.0", "end-1c")
    assert after == before, "round reset must not erase the combat log history"
    assert "slips through your net" not in screen.ticker_label.cget("text"), \
        "capture failure is action feedback, not a pinned notice"
    print("OK — round reset keeps log history; capture failure is not pinned")

    # 3c. The previous combatant's action must not sit next to enemy actions:
    #     it stays readable across the next turn header, then the first
    #     action line of the new combatant sweeps it.
    screen._ticker_feed = []
    screen._handle_output("[1/6] Alraune Fledger's Turn:")
    screen._handle_output("Alraune Fledger [Root Strike] → Shadow Reaver: 51 dmg [EARTH]")
    assert "51 dmg" in screen.ticker_label.cget("text")
    screen._handle_output("[2/6] Veil Hunter's Turn:")
    assert "51 dmg" in screen.ticker_label.cget("text"), \
        "damage line should stay readable across the turn header"
    screen._handle_output("The Veil Hunter attacks but hundur blocks all incoming damage!")
    txt = screen.ticker_label.cget("text")
    assert "51 dmg" not in txt, f"old ally action leaked into the enemy turn: {txt!r}"
    assert "Veil Hunter attacks" in txt, txt
    print("OK — new combatant's first action sweeps the previous action")

    # 3d. Item-use action lines persist across the next turn header too
    #     (2026-11-07 report: the item line vanished immediately).
    screen._handle_output("[3/6] hundur's Turn:")
    screen._handle_output("You use Smoke Bomb. The stun attempt fails.")
    assert "You use Smoke Bomb" in screen.ticker_label.cget("text")
    screen._handle_output("[4/6] Veil Hunter's Turn:")
    assert "You use Smoke Bomb" in screen.ticker_label.cget("text"), \
        "item-use line should survive the turn header"
    screen._handle_output("The Veil Hunter attacks but hundur blocks all incoming damage!")
    assert "You use Smoke Bomb" not in screen.ticker_label.cget("text"), \
        "the next combatant's action should sweep the item line"
    print("OK — item-use action line persists until the next combatant acts")

    # 4. Combat end keeps the notices and lists them above Leave Battle.
    screen.on_result = lambda result: None
    screen._handle_result("victory")
    txt = screen.ticker_label.cget("text")
    assert "VICTORY" in txt.upper(), f"result line missing: {txt!r}"
    # Stale capture feedback must not override the result line.
    assert "slips through your net" not in txt, \
        f"capture feedback overrode the result ticker: {txt!r}"

    body = screen.result_notice_label.cget("text")
    assert "📜 Quest complete: A Place to Belong" in body, body
    assert "+200 XP" in body, body
    assert "Command Resonance" in body, body
    assert "📜 New Main Quest: A Willing Bond" in body, body
    assert "💕 Harpy Scout has been added" in body, body
    # Failed-capture feedback is ticker/log-only, not a spoils notice.
    assert "slips through your net" not in body, body
    assert screen.result_notice_label.winfo_manager() == "pack", \
        "result notice label was not packed"
    root.update_idletasks()
    # Pack order: label first → it sits above the Leave Battle button.
    assert screen.continue_wrap.pack_slaves()[:2] == [
        screen.result_notice_label, screen.continue_btn], \
        screen.continue_wrap.pack_slaves()
    need = (screen.result_notice_label.winfo_reqheight()
            + screen.continue_btn.winfo_reqheight())
    assert need <= screen.action_panel.reserved_height, \
        f"notices ({need}px) overflow the fixed result slot"
    print("OK — result slot lists quest completion + follow-up + capture")

    # 5. The old star border is retired from the capture module.
    src = (Path(__file__).resolve().parent.parent / "combat" / "capture.py").read_text(
        encoding="utf-8")
    assert '"✨" * 20' not in src, "capture star border is still printed"
    assert "✨" * 20 not in src, "capture star border is still printed"
    print("OK — capture emoji border retired")

    screen.destroy()
    root.update()

    if errors:
        print("FAILURES — exceptions escaped:")
        for e in errors:
            print("  " + e)
        root.destroy()
        return 1

    root.destroy()
    print("\nAll combat notice checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
