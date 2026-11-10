# Temp verification (2026-10-13): Ignite (fire weapon trait) follows its advertised
# rarity curve — Common=Burn, Uncommon/Rare=Blaze, Epic=Inferno, Legendary=Conflagration.
# The old generic +1-per-rarity math made Rare/Epic land one tier higher than documented.
# Also verifies unknown rarities fall back to common and non-fire traits are unchanged.
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import combat.elemental_traits as et

et.c_print = lambda *a, **k: None  # silence the combat log lines


def resolve(rarity, element="fire"):
    return et.get_trait_for_weapon({"primary_element": element}, rarity)


def make_enemy():
    return {"name": "Dummy", "hp": 500, "max_hp": 500, "con_mod": 5,
            "active_debuffs": [], "active_buffs": []}


def burn_tier(e):
    d = next((d for d in e["active_debuffs"] if d["type"] == "burn"), None)
    return d["tier"] if d else None


# ── 1. Fire curve ──
expected = {"common": 2, "uncommon": 3, "rare": 3, "epic": 4, "legendary": 5}
for r, t in expected.items():
    got = resolve(r)["on_hit_burn_tier"]
    assert got == t, f"{r}: expected tier {t}, got {got}"
print("OK — Ignite curve: common=2, uncommon=3, rare=3, epic=4, legendary=5")

# ── 2. Unknown rarities fall back to common ──
for r in ("unique", "mystery"):
    got = resolve(r)["on_hit_burn_tier"]
    assert got == 2, f"{r}: expected fallback tier 2, got {got}"
print("OK — unknown/unique rarity falls back to common tier (Burn)")

# ── 3. End-to-end: apply_trait burns at the right tier ──
player = {"name": "Hero", "current_hp": 50}

e = make_enemy()  # legendary → Conflagration immediately
et.apply_trait(resolve("legendary"), player, e, [e], 40)
assert burn_tier(e) == 5, burn_tier(e)
print("OK — legendary hit applies Conflagration directly")

e = make_enemy()  # epic → Inferno, then intensifies to Conflagration on the 2nd hit
et.apply_trait(resolve("epic"), player, e, [e], 40)
assert burn_tier(e) == 4, burn_tier(e)
et.apply_trait(resolve("epic"), player, e, [e], 40)
assert burn_tier(e) == 5, burn_tier(e)
print("OK — epic hit applies Inferno, second hit intensifies to Conflagration")

e = make_enemy()  # rare → Blaze, then Inferno on the 2nd hit
et.apply_trait(resolve("rare"), player, e, [e], 40)
assert burn_tier(e) == 3, burn_tier(e)
et.apply_trait(resolve("rare"), player, e, [e], 40)
assert burn_tier(e) == 4, burn_tier(e)
print("OK — rare hit applies Blaze, second hit intensifies to Inferno")

# ── 4. Non-fire traits keep the generic +1-per-rarity scaling ──
assert resolve("common", "thunder")["on_hit_chain_chance"] == 0.15
assert abs(resolve("legendary", "thunder")["on_hit_chain_chance"] - 0.35) < 1e-9
assert resolve("common", "wind")["on_hit_init_bonus"] == 2
assert resolve("epic", "wind")["on_hit_init_bonus"] == 5
print("OK — non-fire traits unchanged (thunder chain chance, wind swift)")

print("\nAll Ignite curve checks passed.")
