# Temp smoke test for Palette's Palette wedding accessory (Masterclass) — phase 4
import sys
sys.path.insert(0, "c:/Code/Pandemonium")

import combat.weapon.palette_brush as pb
import combat.weapon.wedding_specials as wed
from resources.items import build_item, ITEMS

pb.c_print = lambda *a, **k: None
pb.c_input = lambda prompt="": "0"

# ── 1. Item data ──
assert "wedding_wonderland_palette" in ITEMS
item = build_item("wedding_wonderland_palette", "unique")
assert item["name"] == "Palette's Palette"
assert item["special"] == "palettes_palette"
assert wed.is_wedding_item_soulbound(item) is True

# ── 2. Detection: player + accessory + Palette in party ──
palette_ally = {"name": "Palette", "key": "wonderland_palette", "current_hp": 100, "max_hp": 100}
brush_actor = {
    "name": "Hero",
    "equipped": {
        "weapon": {"id": "palette_brush", "elemental_dmg": {"magical": 1.3}},
        "armor": None,
        "accessory1": item,
        "accessory2": None,
    },
    "allies": [palette_ally],
    "active_buffs": [], "active_debuffs": [],
    "elemental_res": {}, "elemental_dmg": {"magical": 1.3},
    "current_hp": 100, "max_hp": 100,
}
pb.init_brush_state(brush_actor)
assert wed.get_active_wedding_item(brush_actor) is item
assert wed.is_bonded(brush_actor, item) is True
assert pb._masterclass_active(brush_actor) is True

# Without Palette in party → inactive
brush_actor["allies"] = []
assert pb._masterclass_active(brush_actor) is False

# Allies can never trigger it (wedding accessories are player-only)
ally_actor = dict(brush_actor)
ally_actor["is_ally"] = True
ally_actor["allies"] = [palette_ally]
assert pb._masterclass_active(ally_actor) is False

# ── 3. Early exhibit unlocks (5/10/15) ──
brush_actor["allies"] = [palette_ally]
brush_actor["brush_total_strokes"] = 5
unlocked = [k for k, _ in pb.get_brush_exhibits(brush_actor)]
assert unlocked == ["impasto"], unlocked
brush_actor["brush_total_strokes"] = 10
unlocked = [k for k, _ in pb.get_brush_exhibits(brush_actor)]
assert unlocked == ["impasto", "chiaroscuro"], unlocked
brush_actor["brush_total_strokes"] = 15
unlocked = [k for k, _ in pb.get_brush_exhibits(brush_actor)]
assert unlocked == ["impasto", "chiaroscuro", "signature"], unlocked

# Without Masterclass the thresholds stay 6/12/18
brush_actor["allies"] = []
brush_actor["brush_total_strokes"] = 5
assert pb.get_brush_exhibits(brush_actor) == []

# ── 4. Exhibit damage +15% (deterministic via patched randint) ──
brush_actor["allies"] = [palette_ally]
target = {"name": "Dummy", "hp": 100, "con_mod": 6, "active_debuffs": [],
          "active_buffs": [], "elemental_res": {}, "elemental_dmg": {}}
stats = (0, 0, 0, 10, 12, 9)  # scaling = wis+ler+cha = 31
pb.random.randint = lambda a, b: 6  # base = 37

# With Masterclass: 37 - 6 = 31 → magical 1.3 → 40 → +15% → 46
target["hp"] = 100
pb.execute_impasto_exhibit(brush_actor, [target], stats, True)
assert target["hp"] == 100 - 45, target["hp"]  # (37-6)=31, +15% -> 35, magical 1.3 -> 45

# Without Masterclass: 40
brush_actor["allies"] = []
brush_actor["brush_exhibits_used"] = set()  # reset so impasto can fire again
target["hp"] = 100
pb.execute_impasto_exhibit(brush_actor, [target], stats, True)
assert target["hp"] == 100 - 40, target["hp"]  # (37-6)=31, magical 1.3 -> 40

print("WEDDING SMOKE OK")
