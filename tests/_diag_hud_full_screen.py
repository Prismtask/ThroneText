"""Diag: fully-loaded combat HUD (4-row party, N enemies, ticker, actions).

Boots the real CombatScreen (no combat thread) with a full party + allies,
fills the feed + action panel like a live fight, prints vertical/horizontal
space numbers, then keeps the window open for a screenshot.

Run: .venv\\Scripts\\python.exe tests\\_diag_hud_full_screen.py [n_enemies]
"""
import sys
import tkinter as tk
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gui.screens.combat_screen import CombatScreen
from gui.theme import Theme, WINDOW_DEFAULT_SIZE


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
        "inventory": [],
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


def snapshot(screen, tag):
    ec = screen.renderer.enemy_col
    pc = screen.renderer.party_col
    cols = ec.master
    vis = [f for f in screen.renderer._enemy_frames if f.winfo_manager()]
    cards_need = sum(f.winfo_reqheight() for f in vis)
    clip = []
    inner_h = ec.winfo_height()
    for i, f in enumerate(vis):
        bottom = f.winfo_y() + f.winfo_height()
        if bottom > inner_h - 2:
            clip.append(i)
    print(f"[{tag}] window={screen.winfo_toplevel().geometry().split('+')[0]} "
          f"renderer={screen.renderer.winfo_height()}px "
          f"(req {screen.renderer.winfo_reqheight()}) "
          f"columns={cols.winfo_height()}px")
    print(f"    enemy_col={ec.winfo_width()}x{ec.winfo_height()} "
          f"(req {ec.winfo_reqwidth()}x{ec.winfo_reqheight()}) "
          f"party_col={pc.winfo_width()}x{pc.winfo_height()}")
    print(f"    enemy cards: {len(vis)} visible, need {cards_need}px, "
          f"clipped={clip}")
    print(f"    ticker={screen.ticker_label.winfo_height()}px "
          f"action_panel={screen.action_panel.winfo_height()}px "
          f"visible={screen.action_panel.winfo_ismapped()}")


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 5

    root = tk.Tk()
    root.title("HUD5")
    # Mirror the user's saved settings: 1536x793, font size 10
    from gui.theme import set_font_size
    set_font_size(10)
    root.geometry("1536x793")
    root.configure(bg=Theme.BG_DARK)

    player = make_player()
    keys = ["human_footpad", "human_peasant_brigand", "thief",
            "coastal_raider", "temperate_bandit_leader", "novice_mage"]
    screen = TestCombatScreen(root, FakeSM(player), enemy_keys=keys[:n])
    screen.pack(fill=tk.BOTH, expand=True)

    # Statuses on the enemies, like mid-fight
    if screen.enemies:
        screen.enemies[0]["active_debuffs"] = [
            {"type": "burn", "tier": 2, "turns": 3, "pct": 0.05}
        ]
    if len(screen.enemies) > 1:
        screen.enemies[1]["stunned"] = True

    # Populate ticker like a real fight
    screen._append_log("[3/7] Footpad's Turn:")
    screen._append_log("prism → Footpad: 34 dmg")
    screen._append_log("Footpad is burning!")

    # Populate action panel like the player's turn
    screen.action_panel.set_actions(player, screen.enemies)

    from combat.stats import enemy_stats
    # Render a full wave first, then settle on the requested count — the
    # box heights must stay identical between the two states.
    for count in dict.fromkeys((5, n)):
        screen.enemies = [enemy_stats(k, player) for k in keys[:count]]
        if screen.enemies:
            screen.enemies[0]["active_debuffs"] = [
                {"type": "burn", "tier": 2, "turns": 3, "pct": 0.05}
            ]
        if len(screen.enemies) > 1:
            screen.enemies[1]["stunned"] = True
        screen._refresh_hud()
        root.update_idletasks()
        root.update()
        snapshot(screen, f"n={count}")

    root.mainloop()


if __name__ == "__main__":
    main()
