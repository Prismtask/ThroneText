# Temp verification (2026-10-15): Tarnished Jade shatter (Divine Intervention) checks.
#
# Bug report: "it triggers every round ... i cant seem to die here".
# Two loops used to live in the shatter checks:
#   a) with 0 pin stacks, the Wedge branch still repelled every blow while
#      consuming nothing (trigger_wedge_backlash no-op'd);
#   b) with a rebuilt single pin, a full repulse re-armed on every second
#      hit at low HP.
# The Jade's rule is now arrival + pins:
#   - a shatter needs pins to consume (no pins, no absorb);
#   - a shatter fires only when a blow (attack path) or the pins' own turn
#     toll (turn-start path) brings the wearer DOWN to the 20% line from
#     at/above it. Already under the line the Jade is spent: blows land and
#     the pins only dig deeper until the wearer climbs back above the line.
import sys
sys.path.insert(0, "c:/Code/Pandemonium")

import combat.weapon.tarnished_jade as tj

# Silence the flavor text (Divine Lament / Wedge Backlash banners).
tj.c_print = lambda *a, **k: None

ATTRS = ("Strength", "Constitution", "Dexterity", "Wisdom", "Learning", "Charisma")


def make_actor(hp, pins):
    a = {
        "name": "prism",
        "current_hp": hp,
        "max_hp": hp,
        "level": 50,
        "level_hp_bonus": 0,
        "attributes": {x: 10 for x in ATTRS},   # CON 10 → player max HP 45
        "equipped": {"armor": {"id": "tarnished_jade"}},
        "active_buffs": [], "active_debuffs": [],
        "inventory": [],
    }
    a["tarnished_jade_pins"] = pins
    return a


_probe = make_actor(0, 0)
MAX_HP = tj._get_actor_max_hp(_probe)       # 45 (15 + CON 10×3)
THRESHOLD = int(MAX_HP * 0.20)              # 9

enemy = {"name": "The Hollow You", "hp": 500, "max_hp": 500}

# ── 1. THE BUG — 0 pins, crossing the line: damage must APPLY ─────────────
a = make_actor(THRESHOLD + 2, 0)
should_apply, _ = tj.check_tarnished_jade_trigger(a, MAX_HP, [enemy], enemy)
assert should_apply is True, "0 pins must not repel the blow"
assert a["current_hp"] == THRESHOLD + 2, "a silent no-op must not touch HP"
print("OK 1 — 0 pins: the blow lands (no more free repulse)")

# ── 2. Pins exist but the wearer is ALREADY under the line: it lands ───────
a = make_actor(THRESHOLD - 2, 3)
should_apply, _ = tj.check_tarnished_jade_trigger(a, 50, [enemy], enemy)
assert should_apply is True, "under the line, the Jade cannot keep saying no"
assert a["tarnished_jade_pins"] == 3 and not a.get("tarnished_jade_weakened")
print("OK 2 — below 20%: blows land (you can die again)")

# ── 3. Pins present but not crossing the line: lands, pins untouched ──────
a = make_actor(THRESHOLD + 30, 3)
should_apply, _ = tj.check_tarnished_jade_trigger(a, 5, [enemy], enemy)
assert should_apply is True
assert a["tarnished_jade_pins"] == 3
assert not a.get("tarnished_jade_weakened")
print("OK 3 — above the line: normal damage, pins untouched")

# ── 4. Wedge Backlash — fewer than 6 pins crossing the line ───────────────
a = make_actor(THRESHOLD + 10, 5)
hp_before = a["current_hp"]
attacker = {"name": "The Hollow You", "hp": 500, "max_hp": 500}
should_apply, _ = tj.check_tarnished_jade_trigger(a, 11, [attacker], attacker)
assert should_apply is False, "the wedge shatter absorbs the blow"
assert a["tarnished_jade_pins"] == 0, "the shatter consumes every pin"
assert a["tarnished_jade_weakened"] is True, "the wedge curse lands"
assert a["current_hp"] > hp_before, "the wearer heals instead of taking damage"
assert attacker["hp"] < 500, "the wedge blast hits the attacker"
print("OK 4 — wedge: absorbs once, consumes pins, curses, heals")

# ── 5. Divine Lament — 6+ pins crossing the line ──────────────────────────
a = make_actor(THRESHOLD + 5, 6)
hp_before = a["current_hp"]
foes = [{"name": "Foe A", "hp": 500, "max_hp": 500},
        {"name": "Foe B", "hp": 500, "max_hp": 500}]
should_apply, _ = tj.check_tarnished_jade_trigger(a, 6, foes, foes[0])
assert should_apply is False
assert a["tarnished_jade_pins"] == 0
assert a["current_hp"] > hp_before, "lament heals the wearer"
assert all(f["hp"] < 500 for f in foes), "lament hits every enemy"
print("OK 5 — lament: absorbs once, consumes pins, bursts all foes, heals")

# ── 6. After the shatter (0 pins), the NEXT blow lands — no loop ──────────
a["current_hp"] = THRESHOLD - 1
should_apply, _ = tj.check_tarnished_jade_trigger(a, MAX_HP, [enemy], enemy)
assert should_apply is True, "a spent Jade must stop repelling"
print("OK 6 — spent Jade: subsequent blows land")

# ── 7. Turn-start path with 0 pins stays a silent no-op ───────────────────
a = make_actor(THRESHOLD - 1, 0)
hp_before = a["current_hp"]
assert tj.apply_tarnished_jade_turn_start(a, [enemy]) is False
assert a["current_hp"] == hp_before
print("OK 7 — turn-start with 0 pins: no damage, no trigger")

# ── 8. Turn start UNDER the line with pins: the toll bites, no rescue ─────
a = make_actor(THRESHOLD - 1, 2)
hp_before = a["current_hp"]
assert tj.apply_tarnished_jade_turn_start(a, [enemy]) is False
assert a["current_hp"] < hp_before, "the pin toll must still bite"
assert a["tarnished_jade_pins"] == 2, "no shatter under the line"
print("OK 8 — turn start below 20%: the toll bites, no rescue banner")

# ── 9. Turn start ABOVE the line, the pin toll crosses it: Lament fires ───
a = make_actor(THRESHOLD + 3, 6)          # pin toll 30% of max → crosses hard
assert tj.apply_tarnished_jade_turn_start(a, [enemy]) is True
assert a["tarnished_jade_pins"] == 0
assert enemy["hp"] < 500
print("OK 9 — turn start above 20%: the pins' own toll shatters them")

print("\nAll Tarnished Jade trigger checks passed.")
