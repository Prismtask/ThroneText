# Temp smoke test for Palette superboss integration (boss module phase)
import sys
sys.path.insert(0, "c:/Code/Pandemonium")

import combat.palette_chromatic_artisan as pca
from resources.enemies import ENEMIES
from combat.stats import enemy_stats
from resources.items import build_item
from combat.ally import _HEROINE_TEMPLATE_KEYS, _HEROINE_PERMANENT_FLAGS
import resources.skill_loader as sl
from combat.ally_skills import HEROINE_PASSIVES

# 1. YAML entries load
assert "chromatic_artisan" in ENEMIES, "superbosses.yaml entry missing"
assert "wonderland_palette" in ENEMIES, "heroine template missing"

# 2. Boss creation + stance math
boss = pca._PaletteBossDict(enemy_stats("chromatic_artisan"))
assert boss["max_hp"] >= 900, boss["max_hp"]
assert boss["name"] == "Palette, the Chromatic Artisan"

ctx = {"phase": 1, "current_color": "crimson", "secondary_color": None,
       "turns_in_color": 3, "fixative_turns": 0}
pca._apply_stance(boss, ctx)
assert boss["elemental_res"]["water"] == 1.4, boss["elemental_res"]
assert boss["elemental_res"]["fire"] == 0.6, boss["elemental_res"]
assert boss["elemental_res"]["physical"] == 0.8, boss["elemental_res"]
assert boss["elemental_dmg"] == {"fire": 1.5}, boss["elemental_dmg"]
assert boss["_crimson_bonus"] is True

# Umber defense wrapper
boss["damage_taken_mult"] = 0.8
boss["hp"] = 900
boss["hp"] = 800  # 100 damage -> should be reduced to 80
assert boss["hp"] == 820, boss["hp"]
boss["damage_taken_mult"] = 1.0

# 3. Paint stacking + burst
target = {"name": "Test", "current_hp": 100, "active_debuffs": []}
assert pca._add_paint(target, 2, ctx, boss, True) is None
assert target["active_debuffs"][0]["stacks"] == 2
pca._add_paint(target, 2, ctx, boss, True)
assert target["active_debuffs"][0]["stacks"] == 4
msg = pca._add_paint(target, 1, ctx, boss, True)
assert msg and "PIGMENT BURST" in msg, msg
assert any(d["type"] == "burn" for d in target["active_debuffs"]), target["active_debuffs"]
assert ctx["player_survived_burst"] is True

# 4. Fixative freezes paint
target2 = {"name": "Test2", "current_hp": 100, "active_debuffs": []}
pca._add_paint(target2, 3, ctx, boss, False)
ctx["fixative_turns"] = 3
assert pca._add_paint(target2, 2, ctx, boss, False) is None
assert pca._paint_stacks(target2) == 3

# 5. Phase transitions
ctx["phase"] = 3
ctx["secondary_color"] = pca._next_color_in_cycle("crimson", ctx)
pca._apply_stance(boss, ctx)
assert "water" in boss["elemental_res"] or "thunder" in boss["elemental_res"]

# 6. Items build
brush = build_item("palette_brush", rarity="unique")
assert brush["name"] == "Palette's Brush", brush
shawl = build_item("blank_canvas_shawl", rarity="unique")
assert shawl["slot"] == "armor"

# 7. Heroine plumbing
assert _HEROINE_TEMPLATE_KEYS["palette"] == "wonderland_palette"
assert _HEROINE_PERMANENT_FLAGS["palette"]
assert "living_pigment" in HEROINE_PASSIVES
assert sl.RACE_PASSIVES.get("Elemental") is not None

# 8. Dungeon registration
import dungeon  # noqa: E402

# 9. In-process combat simulation — every stance, action, passive, transition
pl = {"name": "Hero", "current_hp": 200, "max_hp": 200,
      "elemental_res": {"fire": 1.0, "water": 1.0, "dark": 1.2},
      "active_debuffs": [], "active_buffs": [], "allies": []}
ally = {"name": "TestAlly", "is_ally": True, "current_hp": 100, "max_hp": 100,
        "elemental_res": {}, "active_debuffs": [], "active_buffs": []}
pl["allies"] = [ally]

pca.compute_player_stats = lambda p: (5, 10, 5, 5, 5, 5)
pca.compute_ally_stats = lambda a: (5, 8, 5, 5, 5, 5)
pca.get_active_allies = lambda p: p.get("allies", [])
pca.c_input = lambda prompt="": ""
pca.c_print = lambda *a, **k: None

sim_boss = pca._PaletteBossDict(enemy_stats("chromatic_artisan"))
sim_boss["_player_ref"] = pl
sim_ctx = {"phase": 1, "current_color": COLOR_CYCLE[0] if False else "crimson",
           "secondary_color": None, "turns_in_color": 3, "fixative_turns": 0,
           "shift_early": False, "study_bonus": 0, "turn_damage": 0,
           "fixative_cooldown": 0, "signature_charging": None,
           "signature_dmg": 0, "signature_cooldown": 0,
           "player_survived_burst": False}

for color in pca.COLOR_CYCLE:
    sim_ctx["current_color"] = color
    sim_ctx["turns_in_color"] = 3
    pca._apply_stance(sim_boss, sim_ctx)
    for _ in range(25):
        action = pca._choose_action(sim_ctx, sim_boss, pl, pca._alive_party(pl))
        assert action in ("brushstroke", "wash", "study", "impasto", "glaze",
                          "drybrush", "chiaroscuro", "spectrum", "fixative"), action
    for action in ("brushstroke", "wash", "study", "impasto", "glaze",
                   "drybrush", "chiaroscuro", "spectrum", "fixative"):
        pca._execute_action(sim_ctx, sim_boss, pl, pca._alive_party(pl), action, False)
    pca._boss_passive_tick(sim_ctx, sim_boss)

# Study bonus carries across turns and is consumed once
pl["current_hp"] = 200
ally["current_hp"] = 100
sim_ctx["study_bonus"] = 2
pca._execute_action(sim_ctx, sim_boss, pl, [pl], "brushstroke", False)
assert sim_ctx["study_bonus"] == 0, sim_ctx["study_bonus"]

# Phase transitions
sim_ctx["phase"] = 1
sim_ctx["current_color"] = "crimson"
pca._blank_canvas_transition(sim_ctx, sim_boss, pl)
assert sim_ctx["phase"] == 2 and not pl["active_debuffs"]
pca._final_canvas_transition(sim_ctx, sim_boss, pl)
assert sim_ctx["phase"] == 3 and sim_ctx["secondary_color"] is not None
pca._apply_stance(sim_boss, sim_ctx)
assert "water" in sim_boss["elemental_res"] or "thunder" in sim_boss["elemental_res"]

# Signature gate at <=10% HP in P3
sim_boss["hp"] = int(sim_boss["max_hp"] * 0.08)
sim_ctx["signature_charging"] = None
sim_ctx["signature_cooldown"] = 0
picked = pca._choose_action(sim_ctx, sim_boss, pl, pca._alive_party(pl))
assert picked == "signature", picked
pca._start_signature(sim_ctx, sim_boss)
assert sim_ctx["signature_charging"] == pca.SIGNATURE_CHARGE_TURNS
assert sim_ctx["signature_dmg"] == 0

print("SIMULATION OK: all stances, attacks, passives, transitions, signature gate")
print("SMOKE OK:", boss["name"], "| HP:", boss["max_hp"],
      "| template:", ENEMIES["wonderland_palette"]["name"], ENEMIES["wonderland_palette"]["race"])
