"""Diagnostic: global status resistance (status_res) system.

Run: python tests/_diag_status_res.py
Exit code 0 = all checks passed.
"""
import sys
import random

sys.path.insert(0, ".")

from resources.enemies import ENEMIES
from combat.stats import enemy_stats
from combat.status_effects import (
    get_status_res,
    check_status_resisted,
    apply_bleed,
    apply_burn,
    apply_freeze,
    apply_weaken,
    apply_poison,
    apply_expose,
    apply_sleep,
)

EXPECTED = {
    "broodmother_vileheart": 0.25,
    "dream_devouring_slitcurrent": 0.25,
    "queen_of_mirrors_sylvana": 0.30,
    "melt_forge_golem_ignis": 0.30,
    "heaven_banished_dragon_yinglong": 0.40,
    "rientrante_frostbound": 0.40,
    "captain_everlong_ship": 0.30,
    "black_silence": 0.50,
    "chromatic_artisan": 0.50,
    "entangled_chrysalis": 0.60,
    "wl_queen_of_hearts": 0.20,
    "wl_big_bad_wolf": 0.25,
    "wl_wicked_witch": 0.40,
    "wl_jabberwock": 0.40,
    "wl_mary_sue": 0.60,
}

failures = []


def check(cond, label):
    if cond:
        print(f"  PASS  {label}")
    else:
        print(f"  FAIL  {label}")
        failures.append(label)


def make_enemy(res):
    return {
        "key": f"diag_res_{res}",
        "name": f"Diag Dummy ({res})",
        "hp": 100,
        "max_hp": 100,
        "con_mod": 8,
        "status_res": res,
        "active_debuffs": [],
        "active_buffs": [],
    }


print("== 1. Rollout: every superboss template carries status_res ==")
for key, expected in EXPECTED.items():
    tpl = ENEMIES.get(key)
    check(tpl is not None, f"{key} template present")
    if tpl is None:
        continue
    check(abs(tpl.get("status_res", -1) - expected) < 1e-9,
          f"{key} status_res == {expected}")

print("== 2. Loader: enemy_stats propagates the field ==")
for key in ("black_silence", "wl_mary_sue", "broodmother_vileheart"):
    inst = enemy_stats(key)
    check(abs(inst.get("status_res", -1) - EXPECTED[key]) < 1e-9,
          f"{key} runtime dict status_res carried through")

print("== 3. Full immunity (1.0) resists everything ==")
immune = make_enemy(1.0)
check(apply_bleed(immune, 5, 3) == "resisted", "bleed resisted")
check(apply_burn(immune, tier=3) == "resisted", "burn resisted")
check(apply_freeze(immune) == "resisted", "freeze resisted")
check(apply_weaken(immune) == "resisted", "weaken resisted")
check(apply_poison(immune, 4, 3) == "resisted", "poison resisted")
check(apply_sleep(immune) == "resisted", "sleep resisted")
result, con = apply_expose(immune, 2)
check(result == "resisted" and con == 8 and immune.get("expose_stacks", 0) == 0,
      "expose resisted, con unchanged")
check(not immune["active_debuffs"] and not immune.get("frozen") and not immune.get("asleep"),
      "no status side-effects applied")
check("burn_original_con" not in immune, "burn CON-shred side-effect skipped")

print("== 4. Zero resistance (0.0) behaves exactly as before ==")
plain = make_enemy(0.0)
check(apply_bleed(plain, 5, 3) == "applied", "bleed applies")
check(apply_burn(plain, tier=2) == "applied", "burn applies")
check(apply_weaken(plain) == "applied", "weaken applies")
fresh = make_enemy(0.0)
result, con = apply_expose(fresh, 2)
check(result == "applied" and con == 6, "expose applies (con 8 -> 6)")

print("== 5. Partial resistance uses a probability roll ==")
hits = 0
TRIALS = 600
for i in range(TRIALS):
    e = make_enemy(0.5)
    if apply_bleed(e, 5, 3) == "resisted":
        hits += 1
check(0.35 * TRIALS < hits < 0.65 * TRIALS,
      f"~50% resist observed ({hits}/{TRIALS})")

print("== 6. Entities without the field are untouched (players/allies) ==")
player_like = {"name": "Player-like", "current_hp": 50, "active_debuffs": []}
check(get_status_res(player_like) == 0.0, "missing field defaults to 0")
check(apply_bleed(player_like, 3, 2) == "applied", "player bleed unaffected")
check(not player_like["active_debuffs"] or player_like["active_debuffs"][0]["type"] == "bleed",
      "player debuff list correct")

if failures:
    print(f"\nFAILED: {len(failures)} check(s)")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)
print("\nALL STATUS-RES DIAGNOSTICS PASSED")
