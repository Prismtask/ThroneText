"""Headless check: unique equipment equip effects in the Examine popup.

Verifies:
  1. Every unique equipment special has a documented effect — either in
     resources/unique_effects.py or the wedding registry — and every key in
     UNIQUE_EFFECTS actually belongs to an item (no typos).
  2. The Examine popup shows "Equip Effect:" for a boss drop (Abyss Fang),
     an Event Horizon trophy (Chance and Choice), and a wedding accessory
     (base + bonded note). Flavour-only uniques say so; uniques without a
     special (engagement rings) get no effect line; key-item lore is intact.
  3. Unique gear that is EQUIPPED exposes its own Examine button on the
     Stats & Equip tab and on ally pages (not just while it sits in the bag).

Run: c:/Code/Pandemonium/.venv/Scripts/python.exe tests/_diag_unique_examine.py
"""

import os
import sys
import tkinter as tk

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import event_horizon as eh
from character import ensure_player_fields
from resources.items import ITEMS, build_item
from resources.unique_effects import UNIQUE_EFFECTS, unique_effect_text

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


def _fake_player():
    attrs = {a: 10 for a in ("Strength", "Constitution", "Dexterity",
                             "Wisdom", "Learning", "Charisma")}
    ally = {
        "name": "Test Ally", "key": "harpy_scout", "is_ally": True,
        "race": "Human", "level": 40, "current_hp": 50, "max_hp": 50,
        "affection": 0,
        "attributes": dict(attrs),
        "active_buffs": [], "active_debuffs": [],
        "innate_skills": [], "learned_skills": [], "skill_cooldowns": {},
        "equipped": {"weapon": None, "armor": None,
                     "accessory1": build_item("chance_and_choice"),
                     "accessory2": None},
    }
    p = {
        "name": "Diag", "current_hp": 100, "max_hp": 100, "level": 50, "gold": 0,
        "max_floor": 30,
        "attributes": dict(attrs),
        "active_buffs": [], "active_debuffs": [],
        "inventory": [build_item("beating_root")],
        "allies": [ally],
        "equipped": {"weapon": build_item("abyss_fang"), "armor": None,
                     "accessory1": build_item("ruby_engagement_ring"),
                     "accessory2": None},
    }
    ensure_player_fields(p)
    eh.ensure_eh_state(p)
    return p


def _walk(w):
    for c in w.winfo_children():
        yield c
        yield from _walk(c)


# ── 1. Registry coverage ────────────────────────────────────────────────────
from combat.weapon.wedding_specials import wedding_special_blurb  # noqa: E402

missing = []
for item_id, base in ITEMS.items():
    if not base.get("unique") or base.get("type") != "equipment":
        continue
    special = base.get("special")
    if not special:
        continue
    if not unique_effect_text(special) and not wedding_special_blurb(special):
        missing.append(f"{item_id}:{special}")
check("every unique special documented", not missing, ", ".join(missing))

all_specials = {v.get("special") for v in ITEMS.values() if v.get("special")}
typos = [k for k in UNIQUE_EFFECTS if k not in all_specials]
check("no orphan UNIQUE_EFFECTS keys", not typos, ", ".join(typos))

# ── 2. Popup content ────────────────────────────────────────────────────────
root = tk.Tk()
root.withdraw()

import gui.widgets.confirm_dialog as confirm_mod  # noqa: E402
from gui.screens.inventory_screen import InventoryScreen  # noqa: E402

captured = {}


def _fake_ok(parent, title, message, **kw):
    captured["title"] = title
    captured["message"] = message


confirm_mod.ok_dialog = _fake_ok

p = _fake_player()
scr = InventoryScreen(root, _StubSM(p))
scr.update_idletasks()

scr._examine_item(build_item("abyss_fang"))
check("Abyss Fang shows equip effect",
      "Equip Effect:" in captured["message"]
      and "Wield the Abyss" in captured["message"])
check("Abyss Fang names its damage element",
      "This weapon causes Dark damage" in captured["message"])
check("element line carries its trait tier",
      "Leech II" in captured["message"])
check("unique name stays hand-authored",
      captured["message"].startswith("Abyss Fang"))

scr._examine_item(build_item("chance_and_choice"))
check("Chance and Choice shows coin effect",
      "Equip Effect:" in captured["message"] and "coin" in captured["message"])

scr._examine_item(build_item("wedding_goblin_girl"))
check("wedding accessory shows base + bonded note",
      "Equip Effect:" in captured["message"]
      and "Bonded (girl in active party):" in captured["message"])
check("accessories do not claim a weapon element",
      "This weapon causes" not in captured["message"])

scr._examine_item(build_item("pocket_watch"))
check("flavour-only unique states no effect",
      "No active combat effect" in captured["message"])

scr._examine_item(build_item("ruby_engagement_ring"))
check("no-special unique has no effect line",
      "Equip Effect:" not in captured["message"])

scr._examine_item(build_item("beating_root"))
check("key-item lore unchanged", "third accessory slot" in captured["message"])
check("key items carry no weapon element line",
      "This weapon causes" not in captured["message"])

# ── 3. Equipped unique gear exposes Examine (player + ally pages) ───────────
stats_btns = [b for b in _walk(scr.stats_frame) if isinstance(b, tk.Button)]
check("equipped unique examinable in Stats & Equip",
      any(b.cget("text") == "Examine" for b in stats_btns))

ally_btns = [b for b in _walk(scr.allies_frame) if isinstance(b, tk.Button)]
check("equipped unique examinable on ally page",
      any(b.cget("text") == "Examine" for b in ally_btns))

# ── Result ──────────────────────────────────────────────────────────────────
fails = [r for r in _results if r == "FAIL"]
print(f"\n{len(_results) - len(fails)}/{len(_results)} checks passed")
sys.exit(1 if fails else 0)
