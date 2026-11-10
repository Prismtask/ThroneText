"""Diagnostic: form perks (D-G) — resolver, stacking and combat hooks.

Run: .venv\\Scripts\\python.exe tests/_diag_form_perks.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from resources.items import build_item
from combat.form_perks import (
    FORM_PERKS, get_form_perk_bonus, get_form_crit_chance_bonus,
    get_form_crit_damage_bonus, get_form_damage_reduction, get_form_evasion,
    get_form_initiative, get_form_healing_bonus, get_form_res_rating_bonus,
    get_outgoing_damage_multiplier, get_armor_pen_multiplier,
    describe_item_perk, get_item_form_perk,
)

failures = []


def check(label, got, expected):
    ok = got == expected
    print(f"  {'OK  ' if ok else 'FAIL'} {label}: got {got}, expected {expected}")
    if not ok:
        failures.append(label)


def near(label, got, expected, tol=1e-9):
    ok = abs(got - expected) <= tol
    print(f"  {'OK  ' if ok else 'FAIL'} {label}: got {got}, expected ~{expected}")
    if not ok:
        failures.append(label)


def actor(**equipped):
    return {"equipped": equipped, "attributes": {"Dexterity": 10, "Wisdom": 10},
            "active_buffs": [], "active_debuffs": []}


print("=== Data table sanity ===")
check("weapon forms covered", len(FORM_PERKS["weapon"]), 29)
check("armor forms covered", len(FORM_PERKS["armor"]), 16)
check("accessory forms covered", len(FORM_PERKS["accessory"]), 17)
check("greatsword perk", FORM_PERKS["weapon"]["greatsword"], ("damage_dealt", 0.10))
check("axe perk", FORM_PERKS["weapon"]["axe"], ("crit_damage", 0.15))
check("hammer perk", FORM_PERKS["weapon"]["hammer"], ("armor_pen", 0.10))

print("=== Resolution from instances ===")
p = actor(weapon=build_item("inferno_greatsword", "rare"),
          armor=build_item("ember_dragonhide", "rare"),
          accessory1=build_item("ember_ring", "rare"),
          accessory2=build_item("blaze_band", "rare"))
check("greatsword Cleaving", get_form_perk_bonus(p, "damage_dealt"), 0.10)
check("dragonhide Steadfast", get_form_perk_bonus(p, "res_rating"), 0.05)
check("ring Keen", get_form_crit_chance_bonus(p), 0.04)
check("band Brutal", get_form_crit_damage_bonus(p), 0.06)
check("outgoing mult (greatsword)", get_outgoing_damage_multiplier(p), 1.10)
near("steadfast fire rating", get_form_res_rating_bonus(p, "fire"), 0.05)
near("steadfast water rating", get_form_res_rating_bonus(p, "water"), 0.0)

print("=== All-equipped stacking (4 base, 5 with the Root) ===")
p2 = actor(weapon=build_item("ember_ring", "rare"),  # ring is not a weapon — no perk
           armor=build_item("ember_ring", "rare"),   # ring is not armor — no perk
           accessory1=build_item("ember_ring", "rare"),
           accessory2=build_item("ember_ring", "rare"),
           accessory3=build_item("ember_ring", "rare"))
near("two accessories", get_form_crit_chance_bonus(p2), 0.08)
p2["acc3_unlocked"] = True
near("three accessories", get_form_crit_chance_bonus(p2), 0.12)

print("=== Unique participation (D-J) ===")
p3 = actor(weapon=build_item("vorpal_blade", "unique"))
check("unique blade Cleaving", get_form_perk_bonus(p3, "damage_dealt"), 0.08)
old_instance = {"id": "vorpal_blade", "slot": "weapon"}
old_actor = {"equipped": {"weapon": old_instance}, "attributes": {}, "active_buffs": []}
check("old instance without form", get_form_perk_bonus(old_actor, "damage_dealt"), 0.08)
p4 = actor(accessory1=build_item("wedding_dryad_protector", "unique"))
check("wedding band Brutal", get_form_crit_damage_bonus(p4), 0.06)
p5 = actor(accessory1=build_item("magma_locket", "rare"))
near("magma locket amulet Steadfast", get_form_res_rating_bonus(p5, "fire"), 0.04)
p6 = actor(accessory1=build_item("cyclone_anklet", "rare"))
check("cyclone anklet band Brutal", get_form_crit_damage_bonus(p6), 0.06)

print("=== Facing no equipment ===")
check("enemy has no perk", get_form_perk_bonus({"name": "goblin"}, "damage_dealt"), 0.0)

print("=== Hook: crit chance & crit damage ===")
from combat.stats import get_raw_critical_chance, resolve_critical_chance
bare = {"attributes": {}, "equipped": {}, "active_buffs": [], "active_debuffs": []}
keen = actor(accessory1=build_item("ember_ring", "rare"))
base_crit = get_raw_critical_chance(bare, "player", dex=10, lrn=10)
keen_crit = get_raw_critical_chance(keen, "player", dex=10, lrn=10)
near("crit chance +4%", keen_crit - base_crit, 0.04)
_, base_dmg_bonus = resolve_critical_chance(bare, "player", 10, 10)
_, band_bonus = resolve_critical_chance(actor(accessory1=build_item("blaze_band", "rare")), "player", 10, 10)
near("crit damage +0.06", band_bonus - base_dmg_bonus, 0.06)

print("=== Hook: dodge & damage reduction ===")
from combat.stats import get_dodge_chance
defender = {"attributes": {"Dexterity": 20, "Wisdom": 10}, "equipped": {}, "active_buffs": []}
attacker = {"attributes": {"Dexterity": 10, "Wisdom": 10}, "active_buffs": []}
base_dodge = get_dodge_chance(defender, attacker)
defender["equipped"] = {"accessory1": build_item("ember_cloak", "rare")}  # Cloak: Nimble +4%, no DEX/WIS mods
near("dodge +4%", get_dodge_chance(defender, attacker) - base_dodge, 0.04)
check("shield Guarded", get_form_damage_reduction(actor(weapon=build_item("titan_shield", "rare"))), 0.08)
check("boots Swift", get_form_initiative(actor(accessory1=build_item("gale_boots", "rare"))), 1.0)
check("earring Swift", get_form_initiative(actor(accessory2=build_item("arcane_earring", "rare"))), 1.0)

print("=== Hook: resistance (Steadfast) ===")
from combat.elemental import calculate_elemental_damage
target = {"elemental_res": {"fire": 1.0}, "equipped": {}, "active_buffs": [], "active_debuffs": []}
atk = {"elemental_dmg": {"fire": 1.0}, "active_buffs": []}
check("neutral fire damage", calculate_elemental_damage(100, atk, target, "fire"), 100)
target["equipped"] = {"accessory1": build_item("magma_locket", "rare")}
check("steadfast fire damage", calculate_elemental_damage(100, atk, target, "fire"), 96)
target["equipped"] = {}
target["elemental_res"] = {"water": 1.0}
target["equipped"] = {"accessory1": build_item("magma_locket", "rare")}
check("steadfast other element unaffected", calculate_elemental_damage(100, atk, target, "water"), 100)

print("=== Hook: healing (Mending) ===")
from combat.status_effects import apply_healing
heal_target = {"current_hp": 10, "max_hp": 100}
check("plain heal", apply_healing(heal_target, 25), 25)
heal_target = {"current_hp": 10, "max_hp": 100}
healer = actor(accessory1=build_item("divine_pendant", "rare"))
check("mending heal", apply_healing(heal_target, 25, source=healer), 26)

print("=== Hook: damage dealt / armour pen ===")
near("magical weapon Focused", get_outgoing_damage_multiplier(actor(weapon=build_item("inferno_staff", "rare"))), 1.08)
near("magical weapon + robes", get_outgoing_damage_multiplier(actor(
    weapon=build_item("inferno_staff", "rare"),
    armor=build_item("arcane_robes", "rare"))), 1.14)
near("hammer pen", get_armor_pen_multiplier(actor(weapon=build_item("inferno_hammer", "rare"))), 0.90)
near("sunder + hammer pen", get_armor_pen_multiplier(
    actor(weapon=build_item("inferno_hammer", "rare")), {"armor_pen": 0.85}), 0.765)
near("no pen", get_armor_pen_multiplier(actor(weapon=build_item("iron_sword", "rare"))), 1.0)

print("=== Display ===")
check("ring perk text", describe_item_perk(build_item("ember_ring", "rare")), "Keen: +4% critical chance")
check("boots perk text", describe_item_perk(build_item("gale_boots", "rare")), "Swift: +1 initiative")
check("dragonhide perk text", describe_item_perk(build_item("ember_dragonhide", "rare")),
      "Steadfast: +0.05 fire resistance")
check("consumable has no perk", describe_item_perk(build_item("healing_potion", "common")), "")

print()
if failures:
    print("FAILED:", ", ".join(failures))
    sys.exit(1)
print("form perks OK")
