"""Headless GUI smoke: Event Horizon inventory tab + unique Examine buttons.

Builds the real InventoryScreen against a stub screen-manager with a fake
player, then checks:
  1. The EH tab exists and renders while a run is active (motes, flasks, cards)
  2. The EH tab is absent when no run is active
  3. Unique equipment shows an Examine button in the Bag

Run: c:/Code/Pandemonium/.venv/Scripts/python.exe tests/_diag_eh_phase4.py
"""

import os
import sys
import tkinter as tk

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import event_horizon as eh
from character import ensure_player_fields
from resources.items import build_item

_results = []


def check(label, cond, detail=""):
    status = "ok" if cond else "FAIL"
    _results.append(status)
    line = f"  [{status}] {label}"
    if detail and not cond:
        line += f"  ({detail})"
    print(line)


class _StubSM:
    """Minimal ScreenManager stand-in for screen construction."""

    def __init__(self, player):
        self.player = player

    def clear_log(self):
        pass

    def update_top_bar(self, *a, **k):
        pass

    def log(self, *a, **k):
        pass


def _fake_player(run_active):
    attrs = {a: 10 for a in ("Strength", "Constitution", "Dexterity",
                             "Wisdom", "Learning", "Charisma")}
    p = {
        "name": "Diag",
        "current_hp": 100, "max_hp": 100, "level": 30, "gold": 100,
        "attributes": attrs,
        "inventory": [build_item("chance_and_choice"), build_item("beating_root")],
        "allies": [],
    }
    ensure_player_fields(p)
    state = eh.ensure_eh_state(p)
    if run_active:
        state["run_active"] = True
        state["room"] = 12
        state["motes"] = 77
        state["positive_cards"] = [
            {"name": "Unity", "tier": 2, "desc": "team deals +6% damage"},
        ]
        state["negative_cards"] = [
            {"name": "Chitin", "tier": 2,
             "desc": "enemies gain +12% CON/DEX", "entropy_cost": 4},
        ]
        state["actor_flasks"] = {
            "player": [{"name": "Fervor", "tier": 3,
                        "label": "Fervor Flask (T3) — +4% damage dealt"}],
        }
        state["entropy_afflictions"] = ["burn"]
        state["joker_cards"] = [
            {"id": "joker_strength", "name": "Strength",
             "desc": "+20% damage dealt · always act last in battle",
             "effects": [], "drawback": {"type": "slow"}},
        ]
        p["_eh_in_run"] = run_active and True
    return p


def _walk(w):
    for c in w.winfo_children():
        yield c
        yield from _walk(c)


root = tk.Tk()
root.withdraw()

from gui.screens.inventory_screen import InventoryScreen  # noqa: E402

# ── 1. Active run (inside) → tab exists with content ────────────────────────
p = _fake_player(True)
scr = InventoryScreen(root, _StubSM(p))
scr.update_idletasks()
check("EH tab built while run active", hasattr(scr, "eh_frame"))
labels = [w.cget("text") for w in _walk(scr.eh_frame)
          if isinstance(w, tk.Label)]
joined = "\n".join(labels)
check("motes rendered", "77" in joined)
check("flask effect rendered", "Fervor Flask (T3)" in joined)
check("positive card rendered", "Unity" in joined)
check("negative card rendered", "Chitin" in joined)
check("entropy row rendered", "Entropy" in joined)
check("affliction rendered", "Burn" in joined)
check("tarot hand rendered", "Hand: 1 / 7" in joined and "Strength" in joined)
check("IN RUN banner", "IN RUN" in joined)
check("best/room rows rendered", "Best room ever" in joined)

# ── 1b. Suspended run → banner says so ──────────────────────────────────────
p_susp = _fake_player(True)
p_susp.pop("_eh_in_run", None)
scr_susp = InventoryScreen(root, _StubSM(p_susp))
scr_susp.update_idletasks()
susp_labels = "\n".join(w.cget("text") for w in _walk(scr_susp.eh_frame)
                       if isinstance(w, tk.Label))
check("SUSPENDED banner", "SUSPENDED" in susp_labels)

# ── 2. No run, no history → no tab; history → stub tab ──────────────────────
p2 = _fake_player(False)
scr2 = InventoryScreen(root, _StubSM(p2))
check("no EH tab without run/history", not hasattr(scr2, "eh_frame"))

p3 = _fake_player(False)
eh.ensure_eh_state(p3)["best_room"] = 7
scr3 = InventoryScreen(root, _StubSM(p3))
scr3.update_idletasks()
check("history stub tab after a past run", hasattr(scr3, "eh_frame"))
hist_labels = "\n".join(w.cget("text") for w in _walk(scr3.eh_frame)
                      if isinstance(w, tk.Label))
check("history stub text", "No active Event Horizon run" in hist_labels)
check("history shows best", "7" in hist_labels)

# ── 3. Unique + key items expose Examine in the bag ─────────────────────────
btns = [w for w in _walk(scr) if isinstance(w, tk.Button)]
examine = [b for b in btns if b.cget("text") == "Examine"]
check("unique + key items examinable", len(examine) >= 2,
      f"found {len(examine)}")

# ── 4. Beating Root: Use button + third-slot row visibility ──────────────────
use_btns = [b for b in btns if b.cget("text") == "Use"]
check("Beating Root Use button", len(use_btns) == 1,
      f"found {len(use_btns)}")
all_labels = "\n".join(w.cget("text") for w in _walk(scr)
                       if isinstance(w, tk.Label))
check("no Accessory 3 row while locked", "Accessory 3" not in all_labels)

p5 = _fake_player(False)
p5["acc3_unlocked"] = True
p5["equipped"]["accessory3"] = None
scr5 = InventoryScreen(root, _StubSM(p5))
scr5.update_idletasks()
labels5 = "\n".join(w.cget("text") for w in _walk(scr5)
                    if isinstance(w, tk.Label))
check("Accessory 3 row when unlocked", "Accessory 3" in labels5)

root.destroy()

print()
fails = _results.count("FAIL")
print(f"── {len(_results) - fails}/{len(_results)} checks passed "
      f"({fails} failed) ──")
sys.exit(1 if fails else 0)
