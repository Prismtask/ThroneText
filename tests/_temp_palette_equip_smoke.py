# Temp smoke test for Palette unique equipment (brush + shawl) — phase 2
import sys
sys.path.insert(0, "c:/Code/Pandemonium")

import random
import combat.weapon.palette_brush as pb
import combat.weapon.blank_canvas_shawl as sh
from combat.elemental import get_attack_element, calculate_elemental_damage

# Silence output for deterministic test runs
def _quiet(*a, **k):
    return ""
pb.c_print = _quiet
pb.c_input = lambda prompt="": "0"
sh_player = None  # placeholder


def make_actor(with_brush=False, with_shawl=False, heroine=None):
    actor = {
        "name": "TestActor",
        "current_hp": 100,
        "max_hp": 100,
        "equipped": {
            "weapon": {"id": "palette_brush", "elemental_dmg": {"magical": 1.3}} if with_brush else None,
            "armor": {"id": "blank_canvas_shawl"} if with_shawl else None,
            "accessory1": None,
            "accessory2": None,
        },
        "active_buffs": [],
        "active_debuffs": [],
        "elemental_res": {},
        "elemental_dmg": {"magical": 1.3} if with_brush else {},
        "is_ally": False,
    }
    if heroine:
        actor["_heroine_key"] = heroine
    return actor


def make_enemy(hp=100, con=8):
    return {"name": "Dummy", "hp": hp, "con_mod": con,
            "active_debuffs": [], "active_buffs": [],
            "elemental_res": {}, "elemental_dmg": {},
            "slowed": False, "blinded": False, "silenced": False,
            "stunned": False, "dreaded": False}


# ── 1. Brush state lifecycle ──
a = make_actor(with_brush=True)
pb.init_brush_state(a)
assert a["brush_palette"] == [] and a["brush_total_strokes"] == 0
pb.clear_brush_state(a)
assert "brush_stance" not in a

# ── 2. Stance element override in get_attack_element ──
a = make_actor(with_brush=True)
pb.init_brush_state(a)
assert get_attack_element(a, a["equipped"]["weapon"]) == "magical"  # no stance
a["brush_stance"] = "fire"
assert get_attack_element(a, a["equipped"]["weapon"]) == "fire"
assert abs(pb.get_brush_damage_mult(a) - 1.35) < 0.001
a["brush_stance"] = None
assert pb.get_brush_damage_mult(a) == 1.0
# non-brush actor unaffected
b = make_actor(with_brush=False)
assert get_attack_element(b, None) is None
assert pb.get_brush_damage_mult(b) == 1.0

# ── 3. Strokes → Pigment Explosion → pigment ──
a = make_actor(with_brush=True)
pb.init_brush_state(a)
a["brush_stance"] = "dark"  # obsidian
e1 = make_enemy()
enemies = [e1]
msgs = pb.on_brush_attack_hit(a, e1, 10, enemies)
assert a["brush_strokes"][id(e1)] == 1, msgs
assert e1["brush_strokes_display"] == "🎨 1/3"
pb.on_brush_attack_hit(a, e1, 10, enemies)
assert a["brush_strokes"][id(e1)] == 2
hp_before = e1["hp"]
msgs = pb.on_brush_attack_hit(a, e1, 10, enemies)  # 3rd → explosion
assert e1["hp"] == hp_before - 5, (e1["hp"], msgs)  # +50% of the 10-dmg hit
assert id(e1) not in a["brush_strokes"]
assert a["brush_palette"] == [{"color": "obsidian", "rank": 1}], a["brush_palette"]
assert a["brush_total_strokes"] == 3

# rank-up + FIFO slots
pb.add_pigment(a, "obsidian")
pb.add_pigment(a, "obsidian")
assert a["brush_palette"] == [{"color": "obsidian", "rank": 3}]
pb.add_pigment(a, "crimson")
pb.add_pigment(a, "azure")
pb.add_pigment(a, "gold")  # full → FIFO replaces obsidian
assert len(a["brush_palette"]) == 3
assert a["brush_palette"][0]["color"] == "crimson", a["brush_palette"]

# ── 4. Auras ──
assert pb.get_aura_rank(a, "crimson") == 1
assert pb.get_brush_lifesteal(a) == 0.0  # obsidian replaced
a2 = make_actor(with_brush=True)
pb.init_brush_state(a2)
a2["brush_palette"] = [{"color": "umber", "rank": 2}, {"color": "verdant", "rank": 1},
                       {"color": "obsidian", "rank": 3}]
assert abs(pb.get_brush_damage_reduction(a2) - 0.12) < 0.001
assert pb.get_brush_initiative_bonus(a2) == 3
assert abs(pb.get_brush_lifesteal(a2) - 0.16) < 0.001
# Palette heroine half passives
a3 = make_actor(with_brush=True, heroine="palette")
pb.init_brush_state(a3)
a3["brush_stance"] = "thunder"
assert pb.get_brush_initiative_bonus(a3) == 5
a3["brush_stance"] = "wind"
assert abs(pb.get_brush_dodge_bonus(a3) - 0.07) < 0.001
a3["brush_stance"] = "earth"
assert abs(pb.get_brush_damage_reduction(a3) - 0.10) < 0.001
a3["brush_stance"] = "fire"
assert abs(pb.get_brush_damage_mult(a3) - 1.42) < 0.001
a3["brush_stance"] = "dark"
assert abs(pb.get_brush_lifesteal(a3) - 0.04) < 0.001

# ── 5. Aura on-attack procs (forced) ──
random.seed(1)
a4 = make_actor(with_brush=True)
pb.init_brush_state(a4)
a4["brush_palette"] = [{"color": "crimson", "rank": 3}, {"color": "azure", "rank": 3},
                       {"color": "gold", "rank": 3}]
e2 = make_enemy(hp=500)
msgs = pb.on_brush_attack_hit(a4, e2, 10, [e2])
# at least the stroke message; procs are random — run 30 hits to guarantee some proc
procs = []
for _ in range(30):
    e2 = make_enemy(hp=500)
    procs.extend(pb.on_brush_attack_hit(a4, e2, 10, [e2]))
assert any("aura" in m for m in procs), procs

# ── 6. Exhibits ──
a5 = make_actor(with_brush=True)
pb.init_brush_state(a5)
a5["brush_stance"] = "fire"
a5["brush_total_strokes"] = 18
assert [k for k, _ in pb.get_brush_exhibits(a5)] == ["impasto", "chiaroscuro", "signature"]
stats = (5, 8, 5, 10, 12, 9)

e3, e4 = make_enemy(hp=300), make_enemy(hp=300)
enemies = [e3, e4]
msg, victory = pb.execute_impasto_exhibit(a5, enemies, stats, True)
assert not victory
assert "impasto" in a5["brush_exhibits_used"]
assert e3["active_debuffs"] or e4["active_debuffs"]  # burn applied no-roll
assert e3["active_debuffs"][0]["type"] == "burn"

e5 = make_enemy(hp=300)
msg, victory = pb.execute_chiaroscuro_exhibit(a5, [e5], stats, True)
assert "chiaroscuro" in a5["brush_exhibits_used"]
assert a5["brush_strokes"].get(id(e5), 0) == 1  # +1 stroke
assert e5["hp"] < 300

a5["brush_palette"] = [{"color": "verdant", "rank": 1}]
e6 = make_enemy(hp=300)
pb.c_input = lambda prompt="": "1"  # pick the first aura for Signature's rank-up
msg, victory = pb.execute_signature_exhibit(a5, [e6], stats, True)
assert "signature" in a5["brush_exhibits_used"]
assert a5["brush_palette"][0]["rank"] == 3

# ── 7. Menus ──
player = make_actor(with_brush=True)
player["inventory"] = [{"type": "consumable", "name": "Potion"}]
player["allies"] = []
pb.init_brush_state(player)
menu, valid, disabled = pb.get_brush_action_menu(player, player, [make_enemy()], True)
assert 'a' in valid and 't' in valid and 'd' in valid and 'f' in valid
assert 't' not in disabled
player["brush_stance_changed"] = True
menu, valid, disabled = pb.get_brush_action_menu(player, player, [make_enemy()], True)
assert 't' in disabled

# ── 8. Shawl ──
s = make_actor(with_shawl=True)
s["current_hp"] = 50
s["active_debuffs"] = [
    {"type": "poison", "damage": 3, "remaining": 2},
    {"type": "paint", "stacks": 4, "remaining": 999, "fixed": True},  # fixative-locked survives
]
s["active_buffs"] = [{"type": "defense", "value": 5, "remaining": 2}]
s["slowed"] = True
msgs = sh.use_blank_canvas(s, False, None)
assert s["current_hp"] == 65, s["current_hp"]  # 50 + 15
assert len(s["active_debuffs"]) == 1 and s["active_debuffs"][0]["type"] == "paint"
assert s["slowed"] is False
assert s["active_buffs"] == []
assert s["blank_canvas_used"] is True
assert s["afterimage_turns"] == 2 and s["afterimage_charges"] == 2

# Afterimage blocks 2 debuffs
from combat.status_effects import apply_poison, apply_bleed, apply_slow_to_player
assert apply_poison(s, 3, 2) is None
assert apply_bleed(s, 4, 2) is None
assert s.get("afterimage_charges", 0) == 0  # charges spent
assert apply_slow_to_player(s, 2) == "applied"  # charges spent → applies again
# tick expires afterimage
s["afterimage_turns"] = 1
s["afterimage_charges"] = 2
msgs = sh.tick_afterimage(s)
assert "afterimage_turns" not in s

# Palette heroine: party-wide version
palette_ally = make_actor(with_shawl=True, heroine="palette")
palette_ally["name"] = "Palette"
palette_ally["current_hp"] = 40
palette_ally["max_hp"] = 100
ally_member = make_actor(with_shawl=False)
ally_member["name"] = "Ally"
ally_member["current_hp"] = 30
ally_member["max_hp"] = 100
ally_member["active_debuffs"] = [{"type": "poison", "damage": 3, "remaining": 2}]
ally_member["is_ally"] = True
fake_player = make_actor(with_shawl=False)
fake_player["name"] = "Hero"
fake_player["current_hp"] = 20
fake_player["max_hp"] = 100
fake_player["attributes"] = {"Constitution": 5, "Strength": 5, "Dexterity": 5,
                            "Wisdom": 5, "Learning": 5, "Charisma": 5}
fake_player["active_debuffs"] = [{"type": "burn", "damage": 4, "remaining": 2}]
fake_player["allies"] = [ally_member]
import combat.ally
combat.ally.get_active_allies = lambda p: p.get("allies", [])
msgs = sh.use_blank_canvas(palette_ally, False, fake_player)
assert fake_player["active_debuffs"] == [], fake_player["active_debuffs"]
assert ally_member["active_debuffs"] == []
assert fake_player["current_hp"] == 23, fake_player["current_hp"]  # 20 + 10% of player_max_hp(30)
assert ally_member["current_hp"] == 40
assert palette_ally["afterimage_turns"] == 2

# ── 9. Paint gate respects Afterimage (boss module) ──
import combat.palette_chromatic_artisan as pca
pca.c_print = _quiet
ctx = {"phase": 1, "current_color": "crimson", "fixative_turns": 0, "player_survived_burst": False}
boss = {"name": "Palette", "level": 35}
target = make_actor(with_shawl=True)
target["afterimage_turns"] = 2
target["afterimage_charges"] = 1
target["active_debuffs"] = []
res = pca._add_paint(target, 1, ctx, boss, True)
assert res is None and target["active_debuffs"] == []
assert "afterimage_charges" not in target  # consumed
res = pca._add_paint(target, 1, ctx, boss, True)  # no charges left → paint lands
assert target["active_debuffs"][0]["stacks"] == 1

print("EQUIPMENT SMOKE OK")
