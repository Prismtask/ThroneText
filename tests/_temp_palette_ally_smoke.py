# Temp smoke test for Palette ally kit + "You held the canvas" recruitment — phase 3
import sys
sys.path.insert(0, "c:/Code/Pandemonium")

import combat.ally as ally_mod
import combat.ally_skills as ask
import combat.palette_ally as pal
import combat.palette_chromatic_artisan as pca
import combat.weapon.chronoweave as chrono
import combat.weapon.palette_brush as pb

# Silence I/O
def _quiet(*a, **k):
    return ""
ally_mod.c_print = _quiet
ally_mod.c_input = lambda prompt="": "0"
ask.c_print = _quiet
ask.c_input = lambda prompt="": "0"
pal.c_input = lambda prompt="": "0"
pca.c_print = _quiet

# ── 1. YAML: Palette's innate skills load ──
assert ask.INNATE_SKILLS_MAP.get("wonderland_palette") == [
    "palette_brushstroke", "palette_spectrum", "palette_signature",
], ask.INNATE_SKILLS_MAP.get("wonderland_palette")
for sid in ("palette_brushstroke", "palette_spectrum", "palette_signature"):
    assert ask.get_innate_skill_def(sid), sid

# ── 2. Create the heroine ally via the real pipeline ──
player = {
    "name": "Hero",
    "level": 30,
    "saved_dungeon_floor": 12,
    "current_hp": 200,
    "attributes": {"Strength": 10, "Constitution": 10, "Dexterity": 10,
                   "Wisdom": 10, "Learning": 10, "Charisma": 10},
    "equipped": {"weapon": None, "armor": None, "accessory1": None, "accessory2": None},
    "active_buffs": [], "active_debuffs": [],
    "inventory": [], "allies": [],
}
pal_ally = ally_mod.create_heroine_ally(player, "palette", 12)
assert pal_ally is not None, "create_heroine_ally returned None"
assert pal_ally["name"] == "Palette"
assert pal_ally["race"] == "Elemental"
assert pal_ally["_heroine_key"] == "palette"
assert pal_ally["innate_skills"] == ["palette_brushstroke", "palette_spectrum", "palette_signature"]
assert pal_ally["passive_skill"] == "elemental_passive"
assert pal_ally["equipped"]["weapon"] is None  # joins without gear
player["allies"].append(pal_ally)

# ── 3. Color cycle ──
assert pal.is_palette_ally(pal_ally)
start = pal.get_palette_ally_color(pal_ally)
for _ in range(7):
    nxt = pal.advance_palette_ally_color(pal_ally)
    assert nxt in pb.COLOR_ORDER
assert pal.get_palette_ally_color(pal_ally) == start  # full cycle returns
assert pal.get_palette_ally_color_element(pal_ally) in ("fire", "water", "thunder", "wind", "earth", "light", "dark")

# ── 4. Degraded kit via execute_ally_skill ──
def make_enemy(hp=200, con=6):
    return {"name": "Dummy", "hp": hp, "max_hp": hp, "con_mod": con,
            "active_debuffs": [], "active_buffs": [], "elemental_res": {},
            "elemental_dmg": {}, "slowed": False, "blinded": False,
            "silenced": False, "stunned": False, "dreaded": False}

enemies = [make_enemy()]
sig_def = ask.get_innate_skill_def("palette_signature")
msg, victory = ask.execute_ally_skill(pal_ally, player, "palette_signature", sig_def, enemies, [])
assert pal.has_pending_signature(pal_ally), "telegraph not set"
assert pal_ally["skill_cooldowns"]["palette_signature"] == 4
assert "NEXT turn" in msg

# Signature fires on her next turn (handle_ally_turn path simulated via fire_)
msg = pal.fire_palette_signature(pal_ally, player, enemies, None)
assert not pal.has_pending_signature(pal_ally)
assert "Signature" in msg
assert enemies[0]["hp"] < 200  # 2.5x ignore-con damage landed

# Spectrum
enemies = [make_enemy()]
spec_def = ask.get_innate_skill_def("palette_spectrum")
msg, victory = ask.execute_ally_skill(pal_ally, player, "palette_spectrum", spec_def, enemies, [])
assert not victory
assert pal_ally["skill_cooldowns"]["palette_spectrum"] == 3
assert msg.count("Spectrum") >= 2  # header + hits

# Brushstroke uses her current color element (dynamic)
enemies = [make_enemy(hp=500)]
brush_def = ask.get_innate_skill_def("palette_brushstroke")
msg, victory = ask.execute_ally_skill(pal_ally, player, "palette_brushstroke", brush_def, enemies, [])
assert not victory and enemies[0]["hp"] < 500
assert "Brushstroke" in msg

# Cooldown gating: signature not usable while on cooldown
usable = ask.get_usable_skills_in_combat(pal_ally)
usable_ids = [sid for sid, _ in usable]
assert "palette_signature" not in usable_ids

# ── 5. Lifecycle clears ──
pal_ally["palette_signature_pending"] = True
pal.clear_palette_ally_state(pal_ally)
assert not pal.has_pending_signature(pal_ally)

# ── 6. "You held the canvas" — Signature survival ──
def fake_chrono_survive(actor, dmg):
    return max(0, actor.get("current_hp", 1) - 1), True
chrono.check_chronoweave_fatal_survival = fake_chrono_survive

fake_player = {"name": "Hero", "current_hp": 150, "active_buffs": [],
               "active_debuffs": [], "equipped": {"accessory1": None, "accessory2": None}}
ctx = {}
assert pca._apply_signature_ko(fake_player, ctx) is True
assert fake_player["current_hp"] == 1

# Without any survival effect the player dies
chrono.check_chronoweave_fatal_survival = lambda a, d: (d, False)
import combat.weapon.wedding_specials as wed
wed.apply_wedding_fatal_blow_survival = lambda a, d: d
fake_player["current_hp"] = 150
assert pca._apply_signature_ko(fake_player, ctx) is False
assert fake_player["current_hp"] == 0

print("ALLY + RECRUIT SMOKE OK")
