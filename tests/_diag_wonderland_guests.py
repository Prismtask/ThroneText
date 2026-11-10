"""Headless smoke test for the Wonderland guest pacing rework.

Covers: empty inn before Floor 10, the three-guest scene, strict Red Hood ->
Dorothy -> Alice order, boss variants arming only on acceptance, late arcs,
permanence, and the Mary Sue fallback.

Run:
    .venv\\Scripts\\python.exe tests\\_diag_wonderland_guests.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import leveling
leveling.gain_exp = lambda player, amount: None

from character import build_character
import wonderland_guests as wg
from combat.ally import create_heroine_ally

ATTRS = {"Strength": 5, "Constitution": 5, "Dexterity": 5,
         "Learning": 5, "Wisdom": 5, "Charisma": 5}


def _new_player(name, slot):
    return build_character("1", "1", ATTRS, name, slot)


print("== empty inn before Floor 10 ==")
p = _new_player("Guests1", 1)
assert wg.get_guest_state(p, "red_hood") == "away"
assert wg.get_guest_state(p, "dorothy") == "away"
assert wg.get_guest_state(p, "alice") == "away"
assert wg.menu_keys(p) == []
assert wg.on_inn_enter(p) == []
print("   empty ok")

print("== Floor 10 clear + inn entry ==")
p["city_floors"]["wonderland"] = {"floor": 11, "max_floor": 11}
p["wl_boss_defeated_queen_of_hearts"] = True
scenes = wg.on_inn_enter(p)
assert "three_guests" in scenes, scenes
assert p["wl_hatter_three_guests_seen"]
assert wg.get_guest_state(p, "red_hood") == "invited"
assert wg.get_guest_state(p, "dorothy") == "away"
assert wg.get_guest_state(p, "alice") == "away"
assert wg.menu_keys(p) == ["red_hood"]
print("   three guests / Red Hood invited")

print("== strict order: Red Hood must finish before Dorothy ==")
p["wl_boss_defeated_big_bad_wolf"] = True
scenes = wg.on_inn_enter(p)
assert wg.get_guest_state(p, "red_hood") == "late"
assert wg.get_guest_state(p, "dorothy") == "invited"
assert "dorothy_arrives" in scenes, scenes
assert wg.get_guest_state(p, "alice") == "away"
print("   Red Hood late; Dorothy invited; Alice still away")

print("== boss variants arm only on acceptance ==")
p2 = _new_player("Guests2", 2)
p2["city_floors"]["wonderland"] = {"floor": 11, "max_floor": 11}
p2["wl_boss_defeated_queen_of_hearts"] = True
wg.on_inn_enter(p2)
assert not wg.is_variant_active(p2, "red_hood")
ally = create_heroine_ally(p2, "red_hood", floor=11)
p2["allies"].append(ally)
wg.set_guest_state(p2, "red_hood", "accepted")
assert wg.is_variant_active(p2, "red_hood")
wg.set_guest_state(p2, "red_hood", "invited")
assert not wg.is_variant_active(p2, "red_hood")
wg.set_guest_state(p2, "red_hood", "accepted")
print("   variant gating ok")

print("== late arc keeps permanence + upgrade path ==")
p["inventory"].append({"id": "woodcutters_broken_axe",
                       "name": "Woodcutter's Broken Axe"})
assert wg.late_arc_available(p, "red_hood")
ok, msg = wg.resolve_late_arc(p, "red_hood")
assert ok, msg
assert wg.get_guest_state(p, "red_hood") == "resolved"
assert p["wonderland_heroine_redhood_permanent"] is True
assert any(i.get("id") == "woodcutters_broken_axe" for i in p["inventory"])
print("   ", msg)

print("== Alice is last ==")
assert wg.get_guest_state(p, "alice") == "away", "Alice must wait for Floor 30"
p["wl_boss_defeated_wicked_witch"] = True
scenes = wg.on_inn_enter(p)
assert wg.get_guest_state(p, "dorothy") == "late"
assert "alice_arrives" in scenes, scenes
assert wg.get_guest_state(p, "alice") == "invited"
print("   Alice arrives only after Dorothy's chapter closes")

print("== Mary Sue fallback ==")
p3 = _new_player("Guests3", 3)
p3["city_floors"]["wonderland"] = {"floor": 51, "max_floor": 51}
for flag in ("wl_boss_defeated_queen_of_hearts",
             "wl_boss_defeated_big_bad_wolf",
             "wl_boss_defeated_wicked_witch",
             "wl_boss_defeated_jabberwock",
             "wl_boss_defeated_mary_sue"):
    p3[flag] = True
wg.on_inn_enter(p3)
wg.on_boss_defeated(p3, "mary_sue")
assert all(wg.get_guest_state(p3, k) in ("late", "resolved")
           for k in wg.GUEST_ORDER)
print("   fallback leaves no guest missable")

print("\nAll Wonderland guest pacing checks passed.")
