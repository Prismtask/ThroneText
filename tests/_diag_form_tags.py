"""Diagnostic: equipment form tags (D-J) — composed, curated and unique gear.

Run: .venv\\Scripts\\python.exe tests/_diag_form_tags.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from resources.items import ITEMS, build_item
from resources.item_generation import (
    WEAPON_FORMS, ARMOR_FORMS, ACCESSORY_FORMS,
    UNIQUE_FORM_TAGS, UNMAPPED_UNIQUE_FORMS, LEGACY_ITEMS,
)

failures = []


def check(label, got, expected):
    ok = got == expected
    print(f"  {'OK  ' if ok else 'FAIL'} {label}: got {got}, expected {expected}")
    if not ok:
        failures.append(label)


FORM_KEYS = {
    "weapon": {f["key"] for f in WEAPON_FORMS},
    "armor": {f["key"] for f in ARMOR_FORMS},
    "accessory": {f["key"] for f in ACCESSORY_FORMS},
}
ALL = {**LEGACY_ITEMS, **ITEMS}

print("=== Unique coverage ===")
check("unmapped uniques", UNMAPPED_UNIQUE_FORMS, [])
uniques = [(i, d) for i, d in ITEMS.items()
           if d.get("type") == "equipment" and d.get("unique")]
check("unique equipment count", len(uniques), len(UNIQUE_FORM_TAGS))
bad_unique = [(i, d.get("slot"), d.get("form")) for i, d in uniques
              if d.get("form") not in FORM_KEYS.get(d.get("slot"), set())]
check("every unique has a slot-valid form", bad_unique, [])

print("=== Registry retirement ===")
curated_left = [i for i, d in ITEMS.items()
                if d.get("type") == "equipment" and not d.get("unique")
                and not d.get("composed") and not d.get("base_form")]
check("no hand-written generics left in ITEMS", curated_left, [])
check("legacy table size", len(LEGACY_ITEMS), 12)
legacy_untagged = [i for i, d in LEGACY_ITEMS.items()
                   if d.get("form") not in FORM_KEYS.get(d.get("slot"), set())]
check("every legacy item is form-tagged", legacy_untagged, [])

print("=== Composed grid ===")
composed = [(i, d) for i, d in ITEMS.items() if d.get("composed")]
bad_composed = [(i, d.get("slot"), d.get("form")) for i, d in composed
                if d.get("form") not in FORM_KEYS.get(d.get("slot"), set())]
check("every composed item has a slot-valid form", bad_composed, [])
check("composed count", len(composed) > 1500, True)

print("=== Curated inference (id suffix) ===")
expected = {
    "iron_sword": "sword",
    "steel_sword": "sword",
    "inferno_greatsword": "greatsword",
    "shadow_tongue_dagger": "tongue_dagger",
    "frost_blade": "blade",
    "titan_shield": "shield",
    "ember_dragonhide": "dragonhide",
    "blaze_battle_harness": "battle_harness",
    "iron_padded_armor": "padded_armor",
    "steel_chainmail": "chainmail",
    "steel_scale_armor": "scale_armor",
    "bedrock_plate_armor": "plate_armor",
    "shadow_wraps": "wraps",
    "mystic_runic_plate": "runic_plate",
    "ember_ring": "ring",
    "blaze_band": "band",
    "radiant_signet": "signet",
    "divine_pendant": "pendant",
    "mystic_crown": "crown",
    "zephyr_gloves": "gloves",
    "gale_boots": "boots",
    "stone_belt": "belt",
    "divine_eye": "eye",
    "arcane_tome": "tome",
    "mystic_monocle": "monocle",
    "magma_locket": "amulet",
    "cyclone_anklet": "band",
    "blaze_gauntlets": "gloves",
    "stone_plate": "shield",
    "hook_hand": "dagger",
    "broomstick": "staff",
}
missing_ids = [i for i in expected if i not in ALL]
check("spot-check ids exist", missing_ids, [])
wrong = {i: (ALL[i].get("form"), form) for i, form in expected.items()
         if i in ALL and ALL[i].get("form") != form}
check("curated form inference", wrong, {})

print("=== Every equipment piece is tagged ===")
untagged = [(i, d.get("slot")) for i, d in ALL.items()
            if d.get("type") == "equipment" and not d.get("form")]
check("untagged equipment", untagged, [])

print("=== Explicit curated mappings (suffix cannot infer) ===")
curated_expected = {
    "stone_plate": "shield",
    "hook_hand": "dagger",
    "broomstick": "staff",
    "blaze_gauntlets": "gloves",
    "magma_locket": "amulet",
    "cyclone_anklet": "band",
}
wrong_c = {i: (ALL[i].get("form"), form) for i, form in curated_expected.items()
           if ALL[i].get("form") != form}
check("curated form mapping", wrong_c, {})

print("=== Instances carry the tag ===")
check("built weapon form", build_item("inferno_greatsword", "rare").get("form"), "greatsword")
check("built armor form", build_item("ember_dragonhide", "rare").get("form"), "dragonhide")
check("built accessory form", build_item("ember_ring", "rare").get("form"), "ring")
check("built unique form", build_item("vorpal_blade", "unique").get("form"), "blade")
check("built legacy form", build_item("magma_locket", "rare").get("form"), "amulet")

print("=== Spot-check unique mappings ===")
unique_expected = {
    "abyss_fang": "blade",
    "cutlass_of_the_captain": "sword",
    "last_oath": "rapier",
    "certain_someone_black_gloves": "gauntlets",
    "palette_brush": "wand",
    "tarnished_jade": "runic_plate",
    "old_dopo_robe": "robes",
    "sky_piercer": "talisman",
    "prescript_ledger": "tome",
    "chance_and_choice": "talisman",
    "silver_slippers": "boots",
    "witch_hat": "crown",
}
wrong_u = {i: (ITEMS[i].get("form"), form) for i, form in unique_expected.items()
           if ITEMS[i].get("form") != form}
check("unique form mapping", wrong_u, {})

print()
if failures:
    print("FAILED:", ", ".join(failures))
    sys.exit(1)
print("equipment form tags OK")
