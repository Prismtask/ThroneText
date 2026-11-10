"""
tests/_diag_wild_map.py — Manual smoke test for wild dungeon map markers + panel.

Not collected by pytest (underscore prefix). Run directly:
    c:/Code/Pandemonium/.venv/Scripts/python.exe tests/_diag_wild_map.py

Requires a display (Tk). Exercises WorldMapScreen's wild dungeon drawing,
hit-testing, selection highlight, and info panel rendering against a stub
object (no full screen-manager needed).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Force UTF-8 output so piped runs don't crash on legacy console encodings
# (e.g. cp932) when printing em-dashes / box glyphs.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import tkinter as tk

from gui.screens.world_map_screen import (
    WorldMapScreen, _WILD_MARKER_W, _WILD_MARKER_H,
)


def _fake_dungeon(dungeon_id, name, position, level=14,
                  floors=4, cleared=1, expire=12):
    return {
        "id": dungeon_id,
        "name": name,
        "biome": "temperate",
        "level": level,
        "total_floors": floors,
        "highest_floor_cleared": cleared,
        "position": position,
        "spawn_day": 8,
        "expire_day": expire,
        "seed_city": "solmere",
        "nearest_city": "solmere",
        "attempted": cleared > 0,
        "reward_pool": [
            {"item_id": "iron_sword", "rarity": "epic"},
            {"item_id": "healing_potion", "rarity": "common"},
            {"item_id": "greater_healing_potion", "rarity": "uncommon"},
        ],
    }


def _all_texts(widget):
    out = []
    for child in widget.winfo_children():
        try:
            text = child.cget("text")
            if text:
                out.append(str(text))
        except tk.TclError:
            pass
        out.extend(_all_texts(child))
    return out


class FakeScreenManager:
    """Captures switch_to calls for assertions."""

    def __init__(self):
        self.calls = []

    def switch_to(self, screen_class, **kwargs):
        self.calls.append((screen_class, kwargs))

    def log(self, *args, **kwargs):
        pass


class ScreenHarness(WorldMapScreen):
    """WorldMapScreen with __init__/BaseScreen bypassed — only the map-state
    attributes the wild dungeon methods touch."""

    def __init__(self, canvas, info_frame, player):
        self._canvas = canvas
        self._info_frame = info_frame
        self.player = player
        self._selected_wild = None
        self._selected_city = None
        self._wild_rect_ids = {}
        self._wild_hitboxes = {}
        self._node_rects = {}
        self._path_result = None
        # Travel state
        self._mode = self.MODE_BROWSE
        self._travel_wild = None
        self._travel_anim_job = None
        self._travel_check_job = None
        self._travel_dot = None
        self._travel_segments = []
        self._travel_paused = False
        self.sm = FakeScreenManager()


def main():
    root = tk.Tk()
    root.withdraw()

    player = {
        "day": 10,
        "max_floor": 15,
        "gold": 100,
        "name": "Test",
        "location": "solmere",
        "wild_dungeons": {
            "active": [
                _fake_dungeon("wild_1", "Forgotten Crypt", [300, 300]),
                _fake_dungeon("wild_2", "Sunken Barrens", [500, 250],
                              level=18, expire=10),
            ],
            "completed": [],
            "next_id": 3,
            "last_spawn_day": 10,
        },
    }

    canvas = tk.Canvas(root)
    info_frame = tk.Frame(root)
    screen = ScreenHarness(canvas, info_frame, player)

    # ── 1. Drawing populates marker bookkeeping ──────────────────────────
    screen._draw_wild_dungeons()
    assert set(screen._wild_hitboxes) == {"wild_1", "wild_2"}, screen._wild_hitboxes
    assert set(screen._wild_rect_ids) == {"wild_1", "wild_2"}

    x1, y1, x2, y2 = screen._wild_hitboxes["wild_1"]
    assert x1 == 300 - _WILD_MARKER_W // 2, (x1,)
    assert y1 == 300 - _WILD_MARKER_H // 2, (y1,)
    assert x2 - x1 == _WILD_MARKER_W and y2 - y1 == _WILD_MARKER_H
    # Markers carry their biome glyph (fixtures are temperate → 🌿)
    marker_texts = [canvas.itemcget(i, "text")
                    for i in canvas.find_withtag("wild_node")
                    if canvas.type(i) == "text"]
    assert any("\U0001F33F" in t and "Lv 14" in t for t in marker_texts), marker_texts
    print("[OK] markers drawn at centered positions with biome glyphs")

    # ── 2. Hit-testing ───────────────────────────────────────────────────
    assert screen._find_wild_at(300, 300) == "wild_1"
    assert screen._find_wild_at(500, 250) == "wild_2"
    assert screen._find_wild_at(10, 10) is None
    assert screen._find_wild_at(x2 + 5, y1) is None
    print("[OK] hit-testing inside/outside bounds")

    # ── 3. Selection highlight + info panel ──────────────────────────────
    screen._select_wild("wild_1")
    assert screen._selected_wild == "wild_1"
    rect_id = screen._wild_rect_ids["wild_1"]
    cfg = canvas.itemconfig(rect_id)
    assert "#f1c40f" in cfg.get("outline", ()), cfg

    texts = _all_texts(info_frame)
    joined = " ".join(texts)
    assert "FORGOTTEN CRYPT" in joined, joined
    assert "REWARD POOL" in joined, joined
    assert "DUNGEON" in joined, joined
    assert any("[EPIC]" in t for t in texts), texts
    assert any("[COMMON]" in t for t in texts), texts
    assert any("Level" == t for t in texts), texts
    assert any("in 2 day(s)" == t for t in texts), texts  # expire 12 - day 10
    assert any("1/4 floors" == t for t in texts), texts   # progress row
    assert any("Est. travel" == t for t in texts), texts  # travel estimate row
    assert any(t.startswith("\u2248") and "blocks" in t for t in texts), texts
    assert any("\U0001F33F" in t for t in texts), texts   # biome glyph in subtitle
    print("[OK] info panel shows name, details, progress, reward pool, travel est.")

    # ── 4. Deselect restores outline + placeholder ───────────────────────
    screen._deselect_wild()
    assert screen._selected_wild is None
    cfg = canvas.itemconfig(rect_id)
    assert "#c44dff" in cfg.get("outline", ()), cfg
    placeholder = [t for t in _all_texts(info_frame) if "Click a city" in t]
    assert placeholder, "placeholder should return after deselect"
    print("[OK] deselect restores marker + placeholder")

    # ── 5. Switching selection between markers ───────────────────────────
    screen._select_wild("wild_1")
    screen._select_wild("wild_2")
    assert screen._selected_wild == "wild_2"
    cfg1 = canvas.itemconfig(screen._wild_rect_ids["wild_1"])
    assert "#c44dff" in cfg1.get("outline", ()), \
        "previous marker should restore its outline"
    cfg2 = canvas.itemconfig(screen._wild_rect_ids["wild_2"])
    assert "#f1c40f" in cfg2.get("outline", ()), "new marker should highlight"
    texts = _all_texts(info_frame)
    assert any("SUNKEN BARRENS" in t for t in texts), texts
    print("[OK] switching selection restores previous marker + rebuilds panel")

    # ── 6. Expired dungeon disappears from next draw ─────────────────────
    # wild_1 expire_day 12; keep wild_2 alive through day 13
    player["day"] = 13
    player["wild_dungeons"]["active"][1]["expire_day"] = 13
    from wild_dungeons import expire_dungeons
    expired = expire_dungeons(player)
    assert {d["id"] for d in expired} == {"wild_1"}, expired
    screen._draw_wild_dungeons()
    assert set(screen._wild_hitboxes) == {"wild_2"}, screen._wild_hitboxes
    print("[OK] expired dungeon removed from map on redraw")

    # ── 7. Travel endpoint resolution (wild: targets) ────────────────────
    dungeon = player["wild_dungeons"]["active"][0]
    assert dungeon["id"] == "wild_2"
    screen._travel_wild = dungeon
    assert screen._canvas_node_pos("wild:wild_2") == (500, 250)
    assert screen._canvas_node_pos("solmere") == (260, 179)
    assert screen._canvas_node_pos("atlantis") is None
    assert screen._node_display_name("wild:wild_2") == "Sunken Barrens"
    assert screen._node_display_name("solmere") == "Solmere"
    print("[OK] wild travel endpoints resolve to canvas positions + names")

    # ── 8. Wild arrival sets entry fields + launches DungeonScreen ───────
    screen.sm.calls.clear()
    screen._arrive_at_wild_dungeon()
    assert player["wild_dungeon_id"] == "wild_2"
    assert player["origin_city"] == dungeon["nearest_city"]
    assert player["location"] == "dungeon"
    assert screen._travel_wild is None
    cls, kwargs = screen.sm.calls[-1]
    assert cls.__name__ == "DungeonScreen", cls
    assert "on_result" in kwargs, kwargs
    print("[OK] arrival sets entry fields + launches DungeonScreen")

    # ── 9. Expiry grace mid-journey → nearest city ───────────────────────
    player["day"] = 50  # far past expire_day 13
    player.pop("wild_dungeon_id", None)
    screen._travel_wild = dungeon
    screen.sm.calls.clear()
    screen._arrive_at_wild_dungeon()
    assert player.get("wild_dungeon_id") is None
    assert player["location"] == dungeon["nearest_city"]
    cls, kwargs = screen.sm.calls[-1]
    assert cls.__name__ == "CityScreen", cls
    print("[OK] crumbled ruin mid-journey delivers to nearest city")

    # ── 10. Wild run result handling ─────────────────────────────────────
    player["location"] = "dungeon"
    player["origin_city"] = dungeon["nearest_city"]
    screen.sm.calls.clear()
    screen._on_wild_result("fled")
    cls, kwargs = screen.sm.calls[-1]
    assert cls.__name__ == "CityScreen", cls
    screen.sm.calls.clear()
    screen._on_wild_result("dead")
    cls, kwargs = screen.sm.calls[-1]
    assert cls.__name__ == "DeathScreen", cls
    assert kwargs.get("death_type") == "dungeon", kwargs
    assert kwargs.get("city_id") == dungeon["nearest_city"], kwargs
    print("[OK] wild results route: fled→city, dead→death screen (dungeon type)")

    # ── 11. explore_dungeon wild branch wiring ───────────────────────────
    # Full wild-run behavior (victory/flee/death/crumble) is covered by
    # tests/_diag_wild_run.py. Here we only verify the branch delegates.
    import dungeon as dungeon_mod
    assert callable(dungeon_mod._explore_wild_dungeon)
    gone_player = {
        "day": 10, "max_floor": 12, "location": "dungeon",
        "origin_city": "elderfen",
        "wild_dungeon_id": "wild_404",
        "wild_dungeons": {"active": [], "completed": [],
                          "next_id": 9, "last_spawn_day": 7},
    }
    import builtins
    old_input = builtins.input
    builtins.input = lambda *a, **k: ""
    old_save = dungeon_mod.save_game
    dungeon_mod.save_game = lambda p: None
    try:
        result = dungeon_mod.explore_dungeon(gone_player)
    finally:
        builtins.input = old_input
        dungeon_mod.save_game = old_save
    assert result == "fled", result
    assert gone_player["location"] == "elderfen"
    assert "wild_dungeon_id" not in gone_player
    print("[OK] explore_dungeon wild branch delegates + missing ruin exits safely")

    # ── 12. City travel panel carries the Travel Here button ────────────
    screen._selected_city = "skylume"
    screen._build_travel_info_panel("skylume", None)
    texts = _all_texts(info_frame)
    assert any("Travel Here" in t for t in texts), texts
    print("[OK] city info panel carries the Travel Here button")

    # ── 13. Wild hit-testing honours the drag-pan offset ────────────────
    canvas.config(scrollregion=(0, 0, 1600, 900), width=800, height=600)
    root.update_idletasks()
    canvas.xview_moveto(0.25)
    canvas.yview_moveto(0.25)
    root.update_idletasks()
    ox, oy = canvas.canvasx(0), canvas.canvasy(0)
    # Widget point that visually sits on wild_2's marker (canvas 500, 250);
    # without the canvasx/canvasy conversion this returns None after panning.
    assert screen._find_wild_at(500 - ox, 250 - oy) == "wild_2", (ox, oy)
    print(f"[OK] wild hit-testing honours pan offset (dx={ox}, dy={oy})")

    root.destroy()
    print("\nWild dungeon map smoke test PASSED.")


if __name__ == "__main__":
    main()
