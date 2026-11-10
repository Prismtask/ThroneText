"""Temp diag (2026-10-14): measure the bottom-area height across the combat
states the user flagged — start of combat (Continue), skill description
(target phase after a skill), target selection, and end of combat (Leave
Battle) — to find which states shift the HUD.

Boots the real CombatScreen with no combat thread, cycles the states, and
prints the height of every bottom widget + the renderer for each state.

Run: .venv\\Scripts\\python.exe tests\\_temp_combat_states_check.py
"""
import sys
import tkinter as tk
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gui.screens.combat_screen import CombatScreen
from gui.theme import Theme


class FakeSM:
    def __init__(self, player):
        self.player = player

    def clear_log(self, *a, **k):
        pass

    def update_top_bar(self, *a, **k):
        pass

    def log(self, *a, **k):
        pass


def make_ally(name, race, level=50):
    return {
        "name": name,
        "nickname": "",
        "awakened_name": "",
        "is_ally": True,
        "race": race,
        "level": level,
        "level_cap": level,
        "current_hp": 240, "max_hp": 240,
        "attributes": {"Strength": 22, "Constitution": 20, "Dexterity": 24,
                       "Wisdom": 18, "Learning": 19, "Charisma": 16, "Speed": 22},
        "equipped": {},
        "innate_skills": ["sunfire_breath"],
        "learned_skills": [],
        "skill_cooldowns": {},
        "active_buffs": [],
        "active_debuffs": [],
    }


def make_player():
    allies = [
        make_ally("Ninetales Fox", "Beast"),
        make_ally("Red Hood", "Human"),
        make_ally("Alice", "Elemental"),
    ]
    return {
        "name": "prism",
        "class": "Warrior",
        "allies": allies,
        "party_order": [0, 1, 2],
        "quests": {"resonance_tier": 5},
        "attributes": {"Strength": 30, "Constitution": 30, "Dexterity": 40,
                       "Learning": 30, "Wisdom": 10, "Charisma": 10, "Speed": 25},
        "current_hp": 207, "max_hp": 207,
        "equipped": {},
        "inventory": [
            {"name": "Health Potion", "type": "consumable", "count": 2},
            {"name": "Antidote", "type": "consumable", "count": 1},
            {"name": "Ether", "type": "consumable", "count": 3},
            {"name": "Bomb", "type": "consumable", "count": 1},
            {"name": "Smoke Bomb", "type": "utility", "count": 5},
        ],
        "active_buffs": [],
        "active_debuffs": [],
        "skill_cooldowns": {},
    }


class TestCombatScreen(CombatScreen):
    def _start_combat(self):
        pass

    def _schedule_poll(self):
        pass

    def _schedule_hud_refresh(self):
        pass


def report(screen, tag):
    """Print + return (bottom_total, renderer_height) for state comparison."""
    root = screen.winfo_toplevel()
    root.update_idletasks()

    def box(w):
        return f"{w.winfo_height()}px" if w.winfo_ismapped() else "hidden"

    renderer = screen.renderer.winfo_height()
    ticker_row = screen.ticker_label.master
    bottom = ticker_row.winfo_height()
    for w in (screen.action_panel, screen.continue_wrap, screen.item_frame):
        if w.winfo_ismapped():
            bottom += w.winfo_height()
    print(f"[{tag}]")
    print(f"    renderer={renderer}px  ticker_row={box(ticker_row)}  "
          f"action_panel={box(screen.action_panel)}  "
          f"continue_wrap={box(screen.continue_wrap)}  "
          f"item_frame={box(screen.item_frame)}")
    print(f"    bottom_total(ticker+panel/btn)={bottom}px  "
          f"window={root.winfo_height()}px")
    return bottom, renderer


FAILS = []


def check(label, cond, extra=""):
    print(("PASS" if cond else "FAIL"), "-", label, extra)
    if not cond:
        FAILS.append(label)


def main():
    root = tk.Tk()
    root.title("CombatStates")
    root.geometry("1536x793")
    root.configure(bg=Theme.BG_DARK)

    player = make_player()
    keys = ["human_footpad", "human_peasant_brigand", "thief"]
    screen = TestCombatScreen(root, FakeSM(player), enemy_keys=keys,
                              on_result=lambda r: None)
    screen.pack(fill=tk.BOTH, expand=True)
    root.update()

    # ── A: baseline — normal action prompt ──
    screen._handle_input_needed("Choose action: ")
    root.update()
    a = report(screen, "A: action prompt")

    # ── B: start of combat — 'Press Enter to begin...' ──
    screen._handle_input_needed("Press Enter to begin...")
    root.update()
    b = report(screen, "B: start of combat (Continue)")

    # ── C: skill description — '>>> desc' + 'Press Enter to use it...' ──
    screen._handle_output(">>> Nine Tails Strike: Spectral tails lash out at "
                          "every foe, searing them with foxfire and leaving "
                          "behind a burning brand that weakens their guard.")
    screen._handle_input_needed("Press Enter to use it...")
    root.update()
    c = report(screen, "C: skill description (Continue)")

    # Continue clicked → engine moves on to target selection
    screen._on_continue_click()
    root.update()

    # ── D: target selection ──
    screen._handle_input_needed("Select target number: ")
    root.update()
    d = report(screen, "D: target selection")

    # ── F: item selection (Use item) — two columns, same slot height ──
    screen._handle_input_needed("Use which item? ")
    root.update()
    f = report(screen, "F: item selection")
    print(f"    item cols: left x={screen.item_listbox.winfo_x()} "
          f"w={screen.item_listbox.winfo_width()} | "
          f"right x={screen.item_listbox2.winfo_x()} "
          f"w={screen.item_listbox2.winfo_width()}")
    check("item slot = action panel reserved height",
          screen.item_frame.winfo_height() == screen.action_panel.reserved_height,
          f"({screen.item_frame.winfo_height()} vs {screen.action_panel.reserved_height})")
    check("item columns equally wide (±1px rounding)",
          abs(screen.item_listbox.winfo_width() - screen.item_listbox2.winfo_width()) <= 1,
          f"({screen.item_listbox.winfo_width()} vs {screen.item_listbox2.winfo_width()})")
    check("5 items split 3 + 2 (+ blank padding row)",
          (screen.item_listbox.size(), screen.item_listbox2.size()) == (3, 3),
          f"{screen.item_listbox.size()} + {screen.item_listbox2.size()}")
    check("left column shows 1., 3., 5.",
          [screen.item_listbox.get(i) for i in range(3)]
          == ["1. Health Potion x2", "3. Ether x3", "5. Smoke Bomb x5"],
          str([screen.item_listbox.get(i) for i in range(3)]))
    check("right column shows 2., 4., blank",
          [screen.item_listbox2.get(i) for i in range(3)]
          == ["2. Antidote", "4. Bomb", ""],
          str([screen.item_listbox2.get(i) for i in range(3)]))

    # Confirm mapping: right col row 0 = display 2, left col row 2 = display 5.
    while not screen.io.input_queue.empty():
        screen.io.input_queue.get_nowait()
    screen.item_listbox2.selection_set(0)
    screen._on_item_confirmed()
    sent_right = screen.io.input_queue.get_nowait()
    check("right column row 0 confirms as item 2", sent_right == "2", f"(sent {sent_right!r})")

    screen._show_item_selection()
    root.update()
    screen.item_listbox.selection_set(2)
    screen._on_item_confirmed()
    sent_left = screen.io.input_queue.get_nowait()
    check("left column row 2 confirms as item 5", sent_left == "5", f"(sent {sent_left!r})")

    # The blank padding row must not confirm anything.
    screen._show_item_selection()
    root.update()
    while not screen.io.input_queue.empty():
        screen.io.input_queue.get_nowait()
    screen.item_listbox2.selection_set(2)
    screen._on_item_confirmed()
    check("blank padding row sends no input",
          screen.io.input_queue.empty(), "(input was sent)")

    # ── E: end of combat — Leave Battle button ──
    screen._handle_result("victory")
    root.update()
    e = report(screen, "E: end of combat (Leave Battle)")

    bottoms = {"A": a[0], "B": b[0], "C": c[0], "D": d[0], "F": f[0], "E": e[0]}
    renderers = {"A": a[1], "B": b[1], "C": c[1], "D": d[1], "F": f[1], "E": e[1]}
    print()
    check("bottom area height constant across all states",
          len(set(bottoms.values())) == 1, f"{bottoms}")
    check("renderer (HUD) height constant across all states",
          len(set(renderers.values())) == 1, f"{renderers}")

    root.destroy()
    print()
    if FAILS:
        print("FAILURES:", FAILS)
        sys.exit(1)
    print("OK: combat states all keep the same layout")


if __name__ == "__main__":
    main()
