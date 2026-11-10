"""Diagnostic: accessory form affinities, base protection, and Examine popups.

Verifies:
  1. Every accessory base form has a thematic stat affinity, keeps its budget,
     and the catalog covers all six attributes (no more all-Str/Con drops).
  2. Uninfused accessories carry NO elemental resistance (1.0 everywhere) —
     early-game defence comes from armor; flowers add accessory resistance.
  3. Old-save accessory instances are re-synced to the current form template
     on load (stats + resistance + name).
  4. Flower infusion still re-attunes the stats to the element's affinity.
  5. The new Examine popup: non-unique equipment shows
     "<rarity + element + form + enhance>" as the title with Affinity/Effect
     lines and no lore; every bag/equipped piece exposes an Examine button.

Run: c:/Code/Pandemonium/.venv/Scripts/python.exe tests/_diag_accessory_affinity.py
"""

import os
import sys
import tkinter as tk

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from character import _refresh_base_form_name, ensure_player_fields
from combat.elemental import ELEMENTS
from resources.items import ITEMS, build_item
from resources.item_generation import (
    ACCESSORY_FORM_AFFINITY, ACCESSORY_FORMS, FLOWER_ITEMS, apply_infusion,
    flower_for_element, pick_family_id,
)

_results = []


def check(label, cond, detail=""):
    status = "ok" if cond else "FAIL"
    _results.append(status)
    line = f"  [{status}] {label}"
    if detail and not cond:
        line += f"  ({detail})"
    print(line)


# ── 1. Form affinities ──────────────────────────────────────────────────────
missing = [f["key"] for f in ACCESSORY_FORMS
           if f["key"] not in ACCESSORY_FORM_AFFINITY]
check("every accessory form has an affinity", not missing, ", ".join(missing))

bad = []
stats_used = set()
for form in ACCESSORY_FORMS:
    base = ITEMS[form["key"]]
    mods = base["base_mods"]
    expected_keys = 2 if form["stats"] >= 2 else 1
    if len(mods) != expected_keys or sum(mods.values()) != form["budget"]:
        bad.append((form["key"], mods, form["budget"], expected_keys))
        continue
    affinity = ACCESSORY_FORM_AFFINITY[form["key"]]
    if affinity[0] not in mods:
        bad.append((form["key"], mods, "primary", affinity[0]))
    if expected_keys == 2 and affinity[1] not in mods:
        bad.append((form["key"], mods, "secondary", affinity[1]))
    stats_used.update(mods)
check("form budgets and affinities match the table", not bad, str(bad))
check("accessories cover all six attributes",
      stats_used == {"Strength", "Constitution", "Dexterity",
                     "Wisdom", "Learning", "Charisma"},
      str(sorted(stats_used)))

str_con_only = [f["key"] for f in ACCESSORY_FORMS
                if set(ITEMS[f["key"]]["base_mods"]) <= {"Strength", "Constitution"}]
check("not every accessory is STR/CON",
      len(str_con_only) < len(ACCESSORY_FORMS), ", ".join(str_con_only))

picks = [pick_family_id("accessory") for _ in range(400)]
affinities = {frozenset(ITEMS[p]["base_mods"]) for p in picks}
check("accessory drops span many affinities", len(affinities) >= 8,
      f"{len(affinities)} distinct")

# ── 2. No innate protection ─────────────────────────────────────────────────
protected = {
    f["key"]: ITEMS[f["key"]]["elemental_res"]
    for f in ACCESSORY_FORMS
    if any(v != 1.0 for v in ITEMS[f["key"]]["elemental_res"].values())
}
check("base accessories carry no elemental resistance", not protected, str(protected))

built = build_item("brooch", "epic")
check("built accessory also has no innate resistance",
      built["elemental_res"], {"physical": 1.0})

# ── 3. Old-save instance re-sync ────────────────────────────────────────────
old = build_item("brooch", "epic")
old["mods"] = {"Strength": 2, "Constitution": 2}
old["elemental_res"] = {"physical": 1.05}
_refresh_base_form_name(old)
check("old accessory stats follow the form affinity",
      old["mods"], {"Charisma": 2, "Dexterity": 2})
check("old accessory loses the innate 1.05 resistance",
      old["elemental_res"], {"physical": 1.0})

# ── 4. Infusion keeps form identity ─────────────────────────────────────────
ring = build_item("ring", "common")
check("ring form affinity", ring["mods"], {"Dexterity": 3})
apply_infusion(ring, "dark", ITEMS["ring"])
check("infusion keeps the form's stats", ring["mods"], {"Dexterity": 3})
check("infusion adds resistance", ring["elemental_res"], {"dark": 1.05})
check("infused name keeps rarity + element + form",
      ring["name"], "Common Shadow Ring")

# Form identity survives repeated infusions, including element swaps.
tome = build_item("tome", "common")
apply_infusion(tome, "fire", ITEMS["tome"])
check("fire tome keeps its Learning identity", tome["mods"], {"Learning": 3})
check("fire tome gains fire resistance", tome["elemental_res"], {"fire": 1.05})
apply_infusion(tome, "water", ITEMS["tome"])
check("adding a second element keeps Learning", tome["mods"], {"Learning": 3})
check("adding a second element keeps both resistances",
      tome["elemental_res"], {"fire": 1.05, "water": 1.05})

# Blacksmith wiring: equipped gear keeps identity and refreshes the actor's
# cached elemental profile in the same visit (no re-equip needed).
import facilities.blacksmith as blacksmith  # noqa: E402


class _SmithTerm:
    def __init__(self):
        self.calls = 0

    def print(self, *a, **k):
        pass

    def pause(self, *a, **k):
        pass

    def menu(self, options, prompt="", allow_cancel=False, styles=None):
        self.calls += 1
        if self.calls == 1:
            return 0
        return list(FLOWER_ITEMS).index("fire")


blacksmith.term = _SmithTerm()
smith_player = {
    "name": "Diag", "race": "Human", "class": "Warrior",
    "equipped": {"weapon": None, "armor": None,
                 "accessory1": build_item("tome", "common"),
                 "accessory2": None},
    "allies": [],
    "inventory": [build_item(flower_for_element("fire"), "common")],
    "elemental_res": {el: 1.0 for el in ELEMENTS},
    "elemental_dmg": {el: 1.0 for el in ELEMENTS},
}
blacksmith.infuse_item(smith_player, {}, "skylume")
smith_tome = smith_player["equipped"]["accessory1"]
check("blacksmith infusion keeps the tome's Learning identity",
      smith_tome["mods"], {"Learning": 3})
check("blacksmith infusion adds fire resistance",
      smith_tome["elemental_res"], {"fire": 1.05})
check("blacksmith infusion refreshes the wearer's cached profile",
      round(smith_player["elemental_res"]["fire"], 2), 1.05)
check("blacksmith infusion consumes the flower",
      smith_player["inventory"] == [], str(smith_player["inventory"]))

# The weapon's primary element feeds matching skill damage through the
# actor's merged elemental profile (same path secondary/tertiary use).
from combat.elemental import compute_player_elemental  # noqa: E402

base_actor = {"race": "Human", "class": "Warrior", "equipped": {}}
_, base_dmg = compute_player_elemental(base_actor)
skill_weapon = build_item("sword", "common")
apply_infusion(skill_weapon, "light", ITEMS["sword"])
_, skill_dmg = compute_player_elemental(
    {**base_actor, "equipped": {"weapon": skill_weapon}})
check("weapon primary feeds matching skill damage",
      round(skill_dmg["light"] - base_dmg["light"], 2), 0.10)

# ── 5. Examine popup + buttons ──────────────────────────────────────────────
class _StubSM:
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
        "race": "Human", "level": 10, "current_hp": 50, "max_hp": 50,
        "affection": 0,
        "attributes": dict(attrs),
        "active_buffs": [], "active_debuffs": [],
        "innate_skills": [], "learned_skills": [], "skill_cooldowns": {},
        "equipped": {"weapon": None, "armor": build_item("leathers", "uncommon"),
                     "accessory1": build_item("boots", "rare"),
                     "accessory2": None},
    }
    p = {
        "name": "Diag", "current_hp": 100, "max_hp": 100, "level": 20, "gold": 0,
        "max_floor": 30,
        "attributes": dict(attrs),
        "active_buffs": [], "active_debuffs": [],
        "inventory": [build_item("brooch", "epic"),
                      build_item("greatsword", "rare"),
                      build_item("plate_armor", "uncommon")],
        "allies": [ally],
        "equipped": {"weapon": build_item("sword", "rare"),
                     "armor": build_item("padded_armor", "common"),
                     "accessory1": build_item("tome", "uncommon"),
                     "accessory2": None},
    }
    ensure_player_fields(p)
    return p


def _walk(w):
    for c in w.winfo_children():
        yield c
        yield from _walk(c)


root = tk.Tk()
root.withdraw()

import gui.widgets.confirm_dialog as confirm_mod  # noqa: E402
from gui.screens.inventory_screen import InventoryScreen  # noqa: E402

captured = {}


def _fake_ok(parent, title, message, **kw):
    captured["title"] = title
    captured["message"] = message


confirm_mod.ok_dialog = _fake_ok

scr = InventoryScreen(root, _StubSM(_fake_player()))
scr.update_idletasks()

scr._examine_item(build_item("brooch", "epic"))
check("examine title is rarity + form", captured["title"] == "Epic Brooch",
      captured["title"])
check("examine lists the form affinity",
      "Affinity: Charisma +2, Dexterity +2" in captured["message"],
      captured["message"])
check("accessory examine names the missing resistance",
      "No elemental resistance" in captured["message"])
check("examine carries an Effect line",
      "Effect:" in captured["message"] and "Tradition —" in captured["message"])
check("ordinary equipment has no lore block",
      "description" not in captured["message"].lower())

scr._examine_item(build_item("greatsword", "rare"))
check("weapon examine carries rarity + form", captured["title"] == "Rare Greatsword",
      captured["title"])
check("weapon examine lists scaling",
      "Scales: STR" in captured["message"], captured["message"])
check("weapon examine states its damage element",
      "This weapon causes Physical damage" in captured["message"],
      captured["message"])
check("weapon examine says the primary also powers matching skills",
      "powers Physical skills" in captured["message"], captured["message"])
check("single-element weapon has no skill-boost line",
      "boosts skills" not in captured["message"], captured["message"])

multi = build_item("greatsword", "rare")
apply_infusion(multi, "fire", ITEMS["greatsword"])
apply_infusion(multi, "water", ITEMS["greatsword"])
apply_infusion(multi, "dark", ITEMS["greatsword"])
scr._examine_item(multi)
check("multi-element weapon names its skill-only slots",
      "This weapon boosts skills with Water (×1.10) and Dark (×1.10)."
      in captured["message"], captured["message"])
check("multi-element weapon says the primary powers matching skills",
      "powers Fire skills" in captured["message"], captured["message"])

dual = build_item("sword", "common")
apply_infusion(dual, "fire", ITEMS["sword"])
apply_infusion(dual, "water", ITEMS["sword"])
scr._examine_item(dual)
check("one secondary uses singular wording",
      "This weapon boosts skills with Water (×1.10)." in captured["message"],
      captured["message"])

scr._examine_item(build_item("plate_armor", "uncommon"))
check("armor examine shows its resistances",
      "Resists Physical" in captured["message"], captured["message"])
check("armor examine calls out the drawback",
      "weak to Magical" in captured["message"], captured["message"])

brooch = build_item("brooch", "rare")
apply_infusion(brooch, "fire", ITEMS["brooch"])
scr._examine_item(brooch)
check("infused examine title includes the element word",
      captured["title"] == "Rare Ember Brooch", captured["title"])
check("infused examine keeps the form affinity and shows the resistance",
      "Charisma +2, Dexterity +2" in captured["message"]
      and "Fire ×1.05" in captured["message"], captured["message"])

bag_btns = [b for b in _walk(scr.bag_frame) if isinstance(b, tk.Button)]
check("bag equipment exposes Examine",
      sum(1 for b in bag_btns if b.cget("text") == "Examine") >= 3,
      str([b.cget("text") for b in bag_btns]))
stats_btns = [b for b in _walk(scr.stats_frame) if isinstance(b, tk.Button)]
check("equipped gear exposes Examine on Stats & Equip",
      sum(1 for b in stats_btns if b.cget("text") == "Examine") >= 3,
      str([b.cget("text") for b in stats_btns]))
ally_btns = [b for b in _walk(scr.allies_frame) if isinstance(b, tk.Button)]
check("ally gear exposes Examine",
      sum(1 for b in ally_btns if b.cget("text") == "Examine") >= 2,
      str([b.cget("text") for b in ally_btns]))

# ── Result ──────────────────────────────────────────────────────────────────
fails = [r for r in _results if r == "FAIL"]
print(f"\n{len(_results) - len(fails)}/{len(_results)} checks passed")
sys.exit(1 if fails else 0)
