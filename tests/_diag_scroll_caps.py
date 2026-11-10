"""Diagnostic: fusion scrolls are no longer capped by grade (audit P6 / D-N).

Run: .venv\\Scripts\\python.exe tests/_diag_scroll_caps.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from resources.items import build_item, cap_rarity_for_item
from inventory import apply_scroll_to_item

failures = []


def check(label, got, expected):
    ok = got == expected
    print(f"  {'OK  ' if ok else 'FAIL'} {label}: got {got}, expected {expected}")
    if not ok:
        failures.append(label)


def scroll(rarity):
    return {"name": f"{rarity.title()} Scroll", "type": "scroll", "target_rarity": rarity}


print("=== Grade 1 (no ceiling - D-N) ===")
ember = build_item("ember_greatsword", "common")
check("legendary accepted", apply_scroll_to_item(ember, scroll("legendary")), True)
check("rarity legendary", ember["rarity"], "legendary")
check("stats rescaled", ember["mods"], {"Strength": 5})  # int(4 x 1.40)
check("name updated", ember["name"], "Legendary Ember Greatsword")
check("downgrade refused", apply_scroll_to_item(ember, scroll("common")), False)
check("same rarity refused", apply_scroll_to_item(ember, scroll("legendary")), False)

print("=== Grade 2 (no ceiling - D-N) ===")
blaze = build_item("blaze_greatsword", "common")
check("epic accepted", apply_scroll_to_item(blaze, scroll("epic")), True)
blaze2 = build_item("blaze_greatsword", "common")
check("legendary accepted", apply_scroll_to_item(blaze2, scroll("legendary")), True)
check("rarity legendary", blaze2["rarity"], "legendary")

print("=== Grade 3 (any) ===")
inferno = build_item("inferno_greatsword", "common")
check("legendary accepted", apply_scroll_to_item(inferno, scroll("legendary")), True)
check("rarity legendary", inferno["rarity"], "legendary")

print("=== Unique gear ===")
unique = build_item("vorpal_blade", "unique")
check("unique refused", apply_scroll_to_item(unique, scroll("legendary")), False)

print("=== Legacy gear (scrolls uncapped) ===")
legacy = build_item("magma_locket", "common")
check("legacy rare accepted", apply_scroll_to_item(legacy, scroll("rare")), True)
check("legacy name", legacy["name"], "Rare Magma Locket")
legacy2 = build_item("magma_locket", "common")
check("legacy legendary accepted", apply_scroll_to_item(legacy2, scroll("legendary")), True)
check("legacy rarity now legendary", legacy2["rarity"], "legendary")

print("=== Hard cap is gone (soft ceiling lives at roll time) ===")
check("g1 cap helper no-op", cap_rarity_for_item(build_item("ember_greatsword", "common"), "legendary"), "legendary")
check("g2 cap helper no-op", cap_rarity_for_item(build_item("blaze_greatsword", "common"), "legendary"), "legendary")
check("g3 cap helper no-op", cap_rarity_for_item(build_item("inferno_greatsword", "common"), "legendary"), "legendary")

print()
if failures:
    print("FAILED:", ", ".join(failures))
    sys.exit(1)
print("scroll grade ceilings removed OK")
