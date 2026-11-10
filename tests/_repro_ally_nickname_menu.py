"""Repro: renamed ally (nickname) during combat shows the PLAYER's action menu.

Playtest report (2026-10-06, Skylume dungeon): the player wears the Black
Gloves; Ninetales Fox was renamed to "Ran Yakumo" (house nickname system).
On her turn the engine prompts "(Ran Yakumo) Choose action:", but
CombatScreen._resolve_active_ally compared the prompt against the raw
`name` field ("Ninetales Fox") -> no match -> _active_ally None -> the
player's Black Gloves menu was rendered. Clicking its workshop keys sent
digits the engine consumed as the ALLY's skill numbers (e.g. [2] Wheels
Industry -> Judgment), while other clicks looked dead ("Invalid choice"
lines are filtered out of the log). The turn order bar correctly said it
was her turn — hence "something is overriding the UI".

Run: .venv\\Scripts\\python.exe tests\\_repro_ally_nickname_menu.py
"""
import sys
import tkinter as tk
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gui.screens.combat_screen import CombatScreen


class FakeSM:
    """Minimal screen-manager stand-in for widget construction."""

    def __init__(self, player):
        self.player = player

    def clear_log(self, *a, **k):
        pass

    def update_top_bar(self, *a, **k):
        pass

    def log(self, *a, **k):
        pass


def make_player():
    gloves = {
        "id": "certain_someone_black_gloves",
        "name": "Certain Someone Black Gloves +5",
        "type": "equipment", "slot": "weapon", "enhance": 5,
    }
    ninetales = {
        "name": "Ninetales Fox",
        "nickname": "Ran Yakumo",
        "awakened_name": "",
        "is_ally": True,
        "race": "Beast",
        "level": 50,
        "level_cap": 50,
        "current_hp": 241,
        "max_hp": 241,
        "attributes": {"Strength": 12, "Constitution": 10, "Dexterity": 11,
                       "Wisdom": 18, "Learning": 19, "Charisma": 12, "Speed": 12},
        "equipped": {"weapon": {"id": "astral_orb", "name": "Astral Orb",
                                "slot": "weapon", "type": "equipment"}},
        "innate_skills": ["sunfire_breath", "nine_tails_strike"],
        "learned_skills": ["aura_of_despair", "judgment"],
        "skill_cooldowns": {},
        "active_buffs": [],
        "active_debuffs": [],
    }
    player = {
        "name": "Tester",
        "class": "Warrior",
        "allies": [ninetales],
        "party_order": [0],
        "quests": {"resonance_tier": 5},
        "attributes": {"Strength": 10, "Constitution": 10, "Dexterity": 10,
                       "Wisdom": 10, "Learning": 10, "Charisma": 10, "Speed": 10},
        "current_hp": 200,
        "max_hp": 200,
        "equipped": {"weapon": gloves},
        "inventory": [],
        "active_buffs": [],
        "active_debuffs": [],
        "skill_cooldowns": {},
    }
    return player, ninetales


class TestCombatScreen(CombatScreen):
    """CombatScreen without starting a real combat thread."""

    def _start_combat(self):
        pass

    def _refresh_hud(self):
        pass

    def _get_current_cooldowns(self):
        return []


def buttons(screen):
    return {k: b.cget("text") for k, b in screen.action_panel._buttons.items()}


def main():
    root = tk.Tk()
    root.geometry("1x1+0+0")
    player, ninetales = make_player()
    screen = TestCombatScreen(root, FakeSM(player))
    failures = []
    try:
        # 1. Nicknamed ally's turn: the prompt carries the DISPLAY name.
        screen._handle_input_needed("  (Ran Yakumo) Choose action: ")
        if screen._active_ally is not ninetales:
            failures.append(
                f"nickname prompt failed to resolve active ally (got {screen._active_ally!r})")
        btns = buttons(screen)
        if "a" not in btns:
            failures.append(f"expected the ally's menu (Attack) — got player's menu: {btns}")
        if "f" in btns:
            failures.append(f"player gloves Flee button leaked into ally menu: {btns}")
        if "Sunfire Breath" not in btns.get("1", ""):
            failures.append(f"ally skill list not shown on key 1: {btns}")
        if not failures:
            print("OK — nickname prompt resolves to the ally + her menu is shown")

        # 2. Raw species name still resolves (no nickname case / legibility).
        screen._handle_input_needed("  (Ninetales Fox) Choose action: ")
        if screen._active_ally is not ninetales:
            failures.append("raw name prompt must still resolve")
        else:
            print("OK — raw name prompt still resolves")

        # 3. Player's own turn still shows the gloves menu (gloves are equipped).
        screen._handle_input_needed("Choose: ")
        if screen._active_ally is not None:
            failures.append("player turn must not resolve an active ally")
        btns = buttons(screen)
        if "1" not in btns or "Allas" not in btns.get("1", ""):
            failures.append(f"player turn should show the Black Gloves menu: {btns}")
        else:
            print("OK — player turn still shows the gloves menu")
    finally:
        screen.destroy()
        root.destroy()

    if failures:
        print("FAILURES:")
        for f in failures:
            print("  - " + f)
        return 1
    print("\nAll ally-nickname menu checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
