"""
tests/_diag_wild_clear_ui.py — Manual smoke test for the wild clear windows.

Not collected by pytest (underscore prefix). Run directly:
    c:/Code/Pandemonium/.venv/Scripts/python.exe tests/_diag_wild_clear_ui.py

Requires a display (Tk). Verifies:
  A. The conquest window builds even though the callback runs on the
     DESTROYED WorldMapScreen instance, offers a single "Return to City"
     button, and switches to CityScreen when clicked.
  B. The generic choice dialog resolves its default option when the window
     is closed (no stuck modal).
"""

import os
import sys
import types

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Force UTF-8 output so piped runs don't crash on legacy console encodings
# (e.g. cp932) when printing em-dashes / box glyphs.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import tkinter as tk

from gui.screens.world_map_screen import WorldMapScreen
from gui.widgets.confirm_dialog import choice_dialog


def _walk(widget):
    yield widget
    for child in widget.winfo_children():
        yield from _walk(child)


def _texts(widget):
    out = []
    for w in _walk(widget):
        try:
            text = w.cget("text")
        except tk.TclError:
            continue
        if text:
            out.append(str(text))
    return out


def _toplevels(root):
    return [w for w in root.winfo_children() if isinstance(w, tk.Toplevel)]


class _FakeSM:
    """Minimal screen manager: root + live top screen + switch recorder."""

    def __init__(self, root, top):
        self.root = root
        self._top = top
        self.switched = []

    def get_top_screen(self):
        return self._top

    def switch_to(self, screen_cls, **kwargs):
        self.switched.append((screen_cls, kwargs))


def test_completion_window():
    root = tk.Tk()
    root.withdraw()
    live = tk.Frame(root)          # stands in for the live DungeonScreen
    sm = _FakeSM(root, live)

    # The real callback runs on the WorldMapScreen that was destroyed when
    # the run started — simulate that with a non-widget object.
    stale_world_map = types.SimpleNamespace(
        player={"_wild_completion": {
            "name": "Smoking Caldera", "level": 3, "floors": 6,
            "gold": 450, "exp": 720,
            "items": [{"name": "Rare Spear", "rarity": "rare"}],
        }},
        sm=sm,
    )

    WorldMapScreen._show_wild_completion(stale_world_map)
    root.update()

    dialogs = _toplevels(root)
    assert len(dialogs) == 1, dialogs
    joined = "\n".join(_texts(dialogs[0]))
    assert "SMOKING CALDERA CONQUERED" in joined, joined
    assert "All 6 floors cleared" in joined, joined
    assert "+450 gold" in joined and "+720 XP" in joined, joined
    assert "Rare Spear" in joined, joined

    buttons = [w for w in _walk(dialogs[0]) if isinstance(w, tk.Button)]
    assert len(buttons) == 1, [str(b.cget("text")) for b in buttons]
    assert "Return to City" in str(buttons[0].cget("text"))

    buttons[0].invoke()
    root.update()
    assert sm.switched, sm.switched
    assert sm.switched[0][0].__name__ == "CityScreen", sm.switched
    print("[OK] conquest window: builds on a stale callback, "
          "single Return to City, switches to city")

    root.destroy()


def test_choice_dialog_default():
    root = tk.Tk()
    root.withdraw()
    live = tk.Frame(root)
    picked = []

    choice_dialog(
        parent=live, title="Floor Cleared!", heading="H",
        options=[("continue", "1. Continue"), ("city", "2. City")],
        on_choice=picked.append, default_choice="continue",
    )
    root.update()

    dialogs = _toplevels(root)
    assert len(dialogs) == 1, dialogs
    # Window X → default option (thread waiting on the choice never hangs)
    root.tk.call(dialogs[0].protocol("WM_DELETE_WINDOW"))
    root.update()
    assert picked == ["continue"], picked
    print("[OK] choice dialog: window close resolves the default option")

    root.destroy()


def main():
    test_completion_window()
    test_choice_dialog_default()
    print("\nWild clear windows smoke test PASSED.")


if __name__ == "__main__":
    main()
