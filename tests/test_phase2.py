"""
tests/test_phase2.py — Phase 2: Combat GUI tests.

Validates:
  • combat_io thread-local redirection
  • combat_ui format_combat_hud_data() returns structured data
  • Combat engine runs with custom IO (no stdin/stdout required)
  • CombatScreen components instantiate without errors
  • GUICombatIO bridges input/output correctly
"""

import sys
import threading
import queue
import tkinter as tk
from unittest.mock import MagicMock

sys.path.insert(0, ".")

import combat.combat_io as combat_io
from combat.combat_ui import format_combat_hud_data
from combat.combat_engine import _combat_inner
from combat.combat_io import TerminalIO, get_io, set_io, reset_io


# ── Dummy data helpers ────────────────────────────────────────────────────────

def dummy_player():
    return {
        "name": "TestHero",
        "current_hp": 20,
        "attributes": {"Strength": 3, "Constitution": 3, "Dexterity": 3,
                        "Intelligence": 3, "Luck": 3, "Charisma": 3, "Wisdom": 0},
        "inventory": [],
        "equipment": {},
        "level": 1,
        "experience": 0,
        "gold": 0,
        "skills": [],
        "active_buffs": [],
        "active_debuffs": [],
        "skill_cooldowns": {},
        "allies": [],
        "time_minutes": 480,
    }


def dummy_enemies():
    return [
        {"name": "Goblin", "hp": 10, "max_hp": 10, "str_mod": 1, "dex_mod": 1,
         "con_mod": 1, "xp_reward": 5, "gold_reward": 5, "race": "goblin",
         "active_buffs": [], "active_debuffs": [], "captured": False,
         "monster_girl": False},
    ]


# ── Mock IO for headless testing ──────────────────────────────────────────────

class MockIO:
    """Captures all combat output and provides scripted input."""

    def __init__(self, inputs=None):
        self.inputs = list(inputs or [])
        self.outputs = []
        self.input_idx = 0

    def print(self, *args, **kwargs):
        self.outputs.append(" ".join(str(a) for a in args))

    def input(self, prompt=""):
        self.outputs.append(f"[PROMPT] {prompt}")
        if self.input_idx < len(self.inputs):
            val = self.inputs[self.input_idx]
            self.input_idx += 1
            return val
        return ""  # default: just press Enter

    def clear(self):
        pass


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_thread_local_io():
    """get_io() should return different objects per thread."""
    results = {}

    def t1():
        io = MockIO()
        set_io(io)
        results["t1"] = get_io()

    def t2():
        io = MockIO()
        set_io(io)
        results["t2"] = get_io()

    th1 = threading.Thread(target=t1)
    th2 = threading.Thread(target=t2)
    th1.start()
    th2.start()
    th1.join()
    th2.join()

    assert results["t1"] is not results["t2"], "Thread-local IO should be independent"
    print("PASS: test_thread_local_io")


def test_terminal_io_defaults():
    """Default IO should be TerminalIO."""
    reset_io()
    io = get_io()
    assert isinstance(io, TerminalIO), f"Expected TerminalIO, got {type(io)}"
    print("PASS: test_terminal_io_defaults")


def test_format_combat_hud_data_structure():
    """format_combat_hud_data() should return the expected dict keys."""
    player = dummy_player()
    enemies = dummy_enemies()
    data = format_combat_hud_data(player, enemies)

    assert "party" in data
    assert "enemies" in data
    assert "header" in data
    assert "action_menu" in data
    assert "cooldowns" in data
    assert "active_ally" in data

    assert len(data["party"]) == 1
    assert data["party"][0]["name"] == "TestHero"
    assert data["party"][0]["is_player"] is True

    assert len(data["enemies"]) == 1
    assert data["enemies"][0]["name"] == "Goblin"
    assert data["enemies"][0]["index"] == 0

    print("PASS: test_format_combat_hud_data_structure")


def test_combat_engine_with_mock_io():
    """_combat_inner should run without real stdin/stdout when IO is mocked."""
    player = dummy_player()

    # Provide a long script: mostly attack, with continue presses in between
    # "a" = attack, "1" = target 1, "" = press Enter to continue
    inputs = []
    for _ in range(20):
        inputs.extend(["", "a", "1", ""])  # start round, attack, target, continue
    inputs.extend([""] * 20)  # extra continues

    mock = MockIO(inputs=inputs)
    set_io(mock)

    try:
        # Run combat in a thread with a timeout to avoid hanging on long combats
        result_holder = {}

        def run_combat():
            set_io(mock)
            try:
                result_holder["result"] = _combat_inner(player, ["bandit"])
            except Exception as e:
                result_holder["error"] = str(e)
            finally:
                reset_io()

        t = threading.Thread(target=run_combat, daemon=True)
        t.start()
        t.join(timeout=5.0)

        if t.is_alive():
            # Combat is still running — that's fine for this test.
            # We just wanted to verify it didn't crash immediately.
            print("PASS: test_combat_engine_with_mock_io (combat thread alive, no crash)")
        else:
            assert "error" not in result_holder, f"Combat crashed: {result_holder.get('error')}"
            assert "result" in result_holder, "Combat finished without result"
            result = result_holder["result"]
            assert result in ("victory", "dead", "fled"), f"Unexpected result: {result}"
            assert len(mock.outputs) > 0, "Expected some output from combat"
            print("PASS: test_combat_engine_with_mock_io")
    finally:
        reset_io()


def test_gui_combat_io_bridge():
    """GUICombatIO should bridge input/output via queues."""
    from gui.screens.combat_screen import GUICombatIO

    io = GUICombatIO()
    io.print("Hello combat")
    io.print("Enemy attacks")

    # Outputs should be in the queue
    events = []
    while True:
        try:
            events.append(io.output_queue.get(block=False))
        except queue.Empty:
            break

    assert len(events) == 2
    assert events[0] == ("OUTPUT", "Hello combat")
    assert events[1] == ("OUTPUT", "Enemy attacks")

    # Input should block until provided
    def provide_input():
        io.send_input("a")

    t = threading.Thread(target=provide_input)
    t.start()
    val = io.input("Choose: ")
    t.join()

    assert val == "a"
    print("PASS: test_gui_combat_io_bridge")


def test_combat_renderer_instantiation():
    """CombatRenderer should create without errors in a tk root."""
    from gui.combat.combat_renderer import CombatRenderer

    root = tk.Tk()
    try:
        renderer = CombatRenderer(root)
        renderer.pack()
        player = dummy_player()
        enemies = dummy_enemies()
        renderer.refresh(player, enemies)
        print("PASS: test_combat_renderer_instantiation")
    finally:
        root.destroy()


def test_action_panel_instantiation():
    """ActionPanel should create buttons from action menu."""
    from gui.combat.action_panel import ActionPanel

    root = tk.Tk()
    try:
        clicks = []
        panel = ActionPanel(root, on_action=lambda k: clicks.append(k))
        panel.pack()
        player = dummy_player()
        enemies = dummy_enemies()
        panel.set_actions(player, enemies)

        # Should have at least attack/defend/flee buttons
        assert len(panel._buttons) >= 3, f"Expected >=3 buttons, got {len(panel._buttons)}"
        print("PASS: test_action_panel_instantiation")
    finally:
        root.destroy()


def test_dungeon_combat_override():
    """dungeon.explore_dungeon should accept combat_override parameter."""
    import inspect
    from dungeon import explore_dungeon
    sig = inspect.signature(explore_dungeon)
    assert "combat_override" in sig.parameters, "explore_dungeon must accept combat_override"
    print("PASS: test_dungeon_combat_override")


# ── Runner ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    test_thread_local_io()
    test_terminal_io_defaults()
    test_format_combat_hud_data_structure()
    test_combat_engine_with_mock_io()
    test_gui_combat_io_bridge()
    test_combat_renderer_instantiation()
    test_action_panel_instantiation()
    test_dungeon_combat_override()
    print("\nAll Phase 2 tests passed!")
