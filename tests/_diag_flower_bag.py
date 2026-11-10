"""Headless check: flowers are visible in the Bag with live counts.

Flowers are crafting materials, so they used to sit buried in Key Items (and
the Bag could go stale after a dungeon run since it was built once at login).
This checks the dedicated Flowers subtab, its count label, element ordering,
Key Items exclusion, and the refresh-on-tab-switch fix.

Run: .venv\\Scripts\\python.exe tests/_diag_flower_bag.py
"""
import os
import sys
import tkinter as tk

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from character import ensure_player_fields
from resources.items import build_item
from inventory import add_item_to_inventory, get_flower_items

_results = []


def check(label, cond, detail=""):
    status = "ok" if cond else "FAIL"
    _results.append(status)
    line = f"  [{status}] {label}"
    if detail and not cond:
        line += f"  ({detail})"
    print(line)


class _StubSM:
    def __init__(self, player):
        self.player = player

    def clear_log(self):
        pass

    def update_top_bar(self, *a, **k):
        pass

    def log(self, *a, **k):
        pass


def _walk(w):
    for c in w.winfo_children():
        yield c
        yield from _walk(c)


def _player():
    p = {
        "name": "Diag", "current_hp": 100, "max_hp": 100, "level": 10, "gold": 0,
        "max_floor": 1, "attributes": {a: 10 for a in
                                       ("Strength", "Constitution", "Dexterity",
                                        "Wisdom", "Learning", "Charisma")},
        "active_buffs": [], "active_debuffs": [], "inventory": [],
        "allies": [], "equipped": {},
    }
    ensure_player_fields(p)
    return p


def _tabs(sub):
    return [sub.tab(i, "text") for i in range(sub.index("end"))]


def _label_texts(sub, index):
    tab = sub.nametowidget(sub.tabs()[index])
    return [w.cget("text") for w in _walk(tab) if isinstance(w, tk.Label)]


p = _player()
ember = build_item("emberbloom")
ember["count"] = 3
p["inventory"].append(ember)
add_item_to_inventory(p, build_item("frostlotus"))
add_item_to_inventory(p, build_item("ironbriar"))
add_item_to_inventory(p, build_item("beating_root"))

check("flower helper finds stacks", [i["id"] for i in get_flower_items(p)],
      ["ironbriar", "emberbloom", "frostlotus"])

root = tk.Tk()
root.withdraw()

from gui.screens.inventory_screen import InventoryScreen  # noqa: E402

scr = InventoryScreen(root, _StubSM(p))
scr.update_idletasks()

tabs = _tabs(scr.bag_sub)
check("Flowers subtab exists with total", " Flowers (5) " in tabs, str(tabs))

flower_idx = tabs.index(" Flowers (5) ")
flower_texts = _label_texts(scr.bag_sub, flower_idx)
joined = " | ".join(flower_texts)
check("flower stack shows count", "Emberbloom (x3)  (Flower)" in joined, joined)
check("flower sorted by element",
      [t for t in flower_texts if "(Flower)" in t]
      == ["Ironbriar  (Flower)", "Emberbloom (x3)  (Flower)", "Frostlotus  (Flower)"],
      joined)

key_idx = tabs.index(" Key Items ")
key_texts = " | ".join(_label_texts(scr.bag_sub, key_idx))
check("key items keep non-flowers", "Beating Root" in key_texts, key_texts)
check("flowers leave Key Items", "Emberbloom" not in key_texts, key_texts)

# ── Staleness: loot added while the Bag is hidden must appear on switch ──
add_item_to_inventory(p, build_item("galeorchid"))
scr.notebook.select(scr.bag_frame)
scr._on_main_tab_changed()
scr.update_idletasks()
tabs = _tabs(scr.bag_sub)
check("bag refreshes on tab switch", " Flowers (6) " in tabs, str(tabs))

print()
fails = [r for r in _results if r == "FAIL"]
print(f"{len(_results) - len(fails)}/{len(_results)} checks passed")
sys.exit(1 if fails else 0)
