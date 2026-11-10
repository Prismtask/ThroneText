# Temp check (2026-11-07): legacy menus must not leak into the GUI combat log.
#
# Playtest report: "help for use item, currently the entire inventory leaked
# into combat log, because of the game legacy mode".
#
# The tkinter GUI builds its own item / capture-net / reserve-party panels from
# live state, so the engine's numbered list prints are pure log noise. They are
# now gated behind BaseCombatIO.renders_menus / c_renders_menus().
#
# Run: .venv\Scripts\python.exe tests\_temp_item_menu_leak_check.py
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from combat.combat_io import (          # noqa: E402
    BaseCombatIO, get_io, reset_io, set_io, TerminalIO, c_renders_menus,
)
from combat.player_actions import handle_player_turn   # noqa: E402


class FakeIO(BaseCombatIO):
    """Captures prints/prompts; `renders_menus` mimics the GUI bridge."""

    def __init__(self, renders_menus=False, inputs=()):
        self.renders_menus = renders_menus
        self.out = []
        self.prompts = []
        self._inputs = list(inputs)

    def print(self, *args, **kwargs):
        self.out.append(" ".join(str(a) for a in args))

    def input(self, prompt=""):
        self.prompts.append(prompt)
        return self._inputs.pop(0) if self._inputs else "0"

    def clear(self):
        pass


def make_player(inventory):
    return {
        "name": "You",
        "current_hp": 30,
        "max_hp": 50,
        "attributes": {k: 10 for k in (
            "Strength", "Constitution", "Dexterity",
            "Learning", "Wisdom", "Charisma")},
        "allies": [],
        "inventory": inventory,
        "level": 1,
    }


ITEM_BAG = [
    {"name": "Health Potion", "type": "consumable", "power": 20, "count": 2},
    {"name": "Smoke Bomb", "type": "utility", "count": 1},
]


def run_item_turn(renders_menus):
    """Drive the player's Use Item branch with the given bridge flavour."""
    io = FakeIO(renders_menus=renders_menus, inputs=["1"])
    set_io(io)
    try:
        player = make_player([dict(i) for i in ITEM_BAG])
        handle_player_turn(player, [], 10, 10, 10, 10, 10, 10,
                           _action_override="u")
    finally:
        reset_io()
    return io


def guarded_prints(rel_path):
    """Return the print statements directly guarded by c_renders_menus()."""
    src = (ROOT / rel_path).read_text(encoding="utf-8")
    return re.findall(r"if not c_renders_menus\(\):\s*\n\s*c_print\((.*)", src)


def main():
    # 1. Flag plumbing: terminal bridge keeps the menus, GUI bridge drops them.
    assert c_renders_menus() is False, "terminal IO must render legacy menus"
    assert getattr(TerminalIO, "renders_menus", False) is False
    from gui.screens.combat_screen import GUICombatIO
    assert GUICombatIO.renders_menus is True, "GUI bridge must claim menus"
    print("OK — renders_menus flag: terminal False, GUI True")

    # 2. GUI mode: no inventory dump, but the prompt still opens the panel and
    #    the action-result line is still emitted.
    gui = run_item_turn(True)
    txt = "\n".join(gui.out)
    assert "Battle Inventory" not in txt, f"legacy header leaked: {txt!r}"
    assert not re.search(r"^\s*\d+\.\s+\S+.*\((consumable|utility)\)", txt, re.M), \
        f"legacy item rows leaked: {txt!r}"
    assert any("Use which item?" in p for p in gui.prompts), gui.prompts
    assert "You use Health Potion" in txt, f"action line missing: {txt!r}"
    print("OK — GUI mode sends the prompt + action line, no inventory dump")

    # 3. Terminal mode still prints the readable menu.
    term = run_item_turn(False)
    txt = "\n".join(term.out)
    assert "Your Battle Inventory:" in txt, txt
    assert re.search(r"^\s*1\.\s+Health Potion x2 \(consumable\)", txt, re.M), txt
    assert re.search(r"^\s*2\.\s+Smoke Bomb \(utility\)", txt, re.M), txt
    print("OK — terminal mode still prints the numbered item menu")

    # 4. Every legacy list is gated (ally bag, capture nets, backup party).
    player_guards = " ".join(guarded_prints("combat/player_actions.py"))
    ally_guards = " ".join(guarded_prints("combat/ally.py"))
    assert "Your Battle Inventory" in player_guards, player_guards
    assert "Select capture net to use" in player_guards, player_guards
    assert "Shared Battle Inventory" in ally_guards, ally_guards
    assert "BACKUP PARTY" in ally_guards, ally_guards
    print("OK — ally bag, capture-net list and backup party are gated too")

    # 5. Combat target rosters: the HUD draws the cards/badges, so the numbered
    #    rows must not be printed in GUI mode (the header line stays — the
    #    screen parses it to pick ally/revive target mode).
    for rel in ("combat/skills.py", "combat/ally_skills.py"):
        src = (ROOT / rel).read_text(encoding="utf-8")
        rosters = re.findall(r"if not c_renders_menus\(\):\s*\n\s+for ", src)
        assert rosters, f"{rel} still prints target rosters in GUI mode"
        assert 'c_print("Select target:")' in src or \
            "Select target for" in src, f"{rel} lost its context header"
    print("OK — ally/party/revive target rosters are gated, headers kept")

    # 6. Blacksmith lists were exact duplicates of its buttons.
    bs = (ROOT / "facilities" / "blacksmith.py").read_text(encoding="utf-8")
    assert 'term.print(f"{i+1}.' not in bs, "blacksmith still prints its item lists"
    print("OK — blacksmith no longer double-prints its item lists")

    print("\nAll item-menu leak checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
