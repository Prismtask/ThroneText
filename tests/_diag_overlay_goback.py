"""Diagnostic: Escape with an active overlay must not stack screens.

Reproduces the 'VEILHOLT peeking under the combat screen' report:
- CityScreen (A) -> WorldMapScreen (B) via switch_to (history=[A])
- push_overlay(CombatScreen-like C)  -> B hidden, C packed
- sm.go_back() (what BaseScreen.handle_escape used to do) -> with the fix
  it dismisses overlay C and leaves B alone; it must NOT pack A beneath C.

Pre-fix output: packed after go_back: ['DummyCombat', 'DummyCity'] (bug).
Post-fix:       packed after go_back: ['DummyWorldMap'], overlay dismissed,
                and Escape dispatch targets the overlay via get_top_screen().
Also verifies gui/app.py::_on_inventory_key uses get_top_screen() so the
inventory overlay can no longer dismiss a live combat overlay.
"""

import tkinter as tk

from gui.screen_manager import ScreenManager


class DummyCity(tk.Frame):
    """Stand-in for CityScreen (top widget would be the city name label)."""

    def __init__(self, parent, screen_manager, **kwargs):
        super().__init__(parent, bg="#101010")
        self.sm = screen_manager
        tk.Label(self, text="VEILHOLT", bg="#101010", fg="#e94560",
                 font=("Consolas", 14, "bold")).pack(pady=10)


class DummyWorldMap(tk.Frame):
    """Stand-in for WorldMapScreen (inherits default handle_escape -> go_back)."""

    def __init__(self, parent, screen_manager, **kwargs):
        super().__init__(parent, bg="#202020")
        self.sm = screen_manager
        tk.Label(self, text="WORLD MAP", bg="#202020", fg="white").pack()


class DummyCombat(tk.Frame):
    """Stand-in for the CombatScreen overlay."""

    def __init__(self, parent, screen_manager, **kwargs):
        super().__init__(parent, bg="#303030")
        self.sm = screen_manager
        tk.Label(self, text="COMBAT HUD", bg="#303030", fg="white").pack()


def main():
    root = tk.Tk()
    root.withdraw()
    sm = ScreenManager(root, player={"name": "prism"}, settings={})

    sm.switch_to(DummyCity)          # history=[]
    sm.switch_to(DummyWorldMap)      # history=[DummyCity]
    sm.push_overlay(DummyCombat)     # world map pack_forget'ed, combat packed

    packed_before = [type(w).__name__ for w in sm.content_frame.pack_slaves()]
    print("packed before go_back:", packed_before)
    print("top screen (input target):", type(sm.get_top_screen()).__name__)

    sm.go_back()                     # what BaseScreen.handle_escape used to do
    root.update_idletasks()

    packed_after = [type(w).__name__ for w in sm.content_frame.pack_slaves()]
    print("packed after  go_back:", packed_after)

    overlay_alive = sm._overlay_screen is not None and sm._overlay_screen.winfo_exists()
    print("overlay still alive:", overlay_alive)
    print("current screen:", type(sm.current_screen).__name__ if sm.current_screen else None)

    # Also verify the real WorldMapScreen now overrides the destructive default
    from gui.screens.world_map_screen import WorldMapScreen
    from gui.screens.base_screen import BaseScreen
    print("WorldMapScreen.handle_escape overridden:",
          WorldMapScreen.handle_escape is not BaseScreen.handle_escape)

    # ── Global 'I' key routing (gui/app.py::_on_inventory_key) ──────────
    from gui.app import PandemoniumApp
    from gui.screens.dungeon_screen import DungeonScreen

    class FakeApp:
        def __init__(self, screen_manager):
            self.screen_manager = screen_manager

    fake = FakeApp(sm)
    pushes = []
    sm.push_overlay = lambda *a, **k: pushes.append((a, k))

    # Overlay active (combat): 'I' must be ignored.
    sm._overlay_screen = DummyCombat(sm.content_frame, sm)
    PandemoniumApp._on_inventory_key(fake, None)
    print("'I' with overlay -> pushes:", len(pushes), "(expect 0)")

    # No overlay, current screen is a DungeonScreen: 'I' pushes inventory.
    sm._overlay_screen = None
    sm.current_screen = object.__new__(DungeonScreen)
    PandemoniumApp._on_inventory_key(fake, None)
    print("'I' on dungeon -> pushes:", len(pushes), "(expect 1)")

    double_packed = len(packed_after) > 1
    print("RESULT:", "FAIL — screens stacked" if double_packed else "OK — no stacking")

    root.destroy()


if __name__ == "__main__":
    main()
