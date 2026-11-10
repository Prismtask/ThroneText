# Temp verification (2026-10-12): Sunfire Band (legendary_flame) bonded spread is a
# seed-only application — it never double-counts with a direct hit inside one action,
# so a single AoE can no longer escalate a whole pack to Inferno. Two band
# applications per enemy always take two actions, and the combat log reports the
# tier actually reached instead of always claiming Blaze.
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from character import build_character
from resources.items import build_item
import combat.weapon.wedding_specials as ws

ATTRS = {"Strength": 5, "Constitution": 5, "Dexterity": 5,
         "Learning": 5, "Wisdom": 5, "Charisma": 5}

# Capture the band's combat-log lines instead of printing them.
msgs = []
ws._msg = lambda text: msgs.append(text)


def make_player(bonded=True):
    p = build_character("1", "1", ATTRS, "prism", 1)
    p["equipped"]["accessory1"] = build_item("wedding_ninetales_fox")
    if bonded:
        p["allies"] = [{"key": "ninetales_fox", "name": "Ninetales Fox"}]
    return p


def make_enemy(name="Wolf", status_res=0.0):
    return {"name": name, "hp": 500, "max_hp": 500, "con_mod": 5, "status_res": status_res,
            "active_debuffs": [], "active_buffs": []}


def burn_entry(e):
    return next((d for d in e.get("active_debuffs", []) if d.get("type") == "burn"), None)


def tier(e):
    d = burn_entry(e)
    return d["tier"] if d else None


def hit(player, target, enemies):
    ws.apply_wedding_on_hit(player, target, enemies, 40)


def aoe_cast(player, enemies):
    """Mirror the class-skill loop: the hook fires once per enemy."""
    for tgt in list(enemies):
        ws.apply_wedding_on_hit(player, tgt, enemies, 40)


# ── 1. Bonded single-target strike 1: target Blaze, others seeded Blaze ──
p = make_player()
a, b, c = make_enemy("A"), make_enemy("B"), make_enemy("C")
msgs.clear()
hit(p, a, [a, b, c])
assert [tier(a), tier(b), tier(c)] == [3, 3, 3], (tier(a), tier(b), tier(c))
assert burn_entry(b).get("sunfire_seed") and burn_entry(c).get("sunfire_seed")
assert not burn_entry(a).get("sunfire_seed")
assert [e["con_mod"] for e in (a, b, c)] == [4, 4, 4], "CON shred must apply exactly once per enemy"
assert any("engulfed" in m for m in msgs)
assert any("spreads to" in m and "B" in m and "C" in m for m in msgs)
print("OK — single strike: target Blaze, others seeded Blaze (no Inferno)")

# ── 2. Strike 2 on the same target: only THAT enemy intensifies ──
msgs.clear()
hit(p, a, [a, b, c])
assert tier(a) == 4, tier(a)
assert [tier(b), tier(c)] == [3, 3], (tier(b), tier(c))
assert any("intensify into Inferno" in m for m in msgs), msgs
assert not any("spreads to" in m for m in msgs), msgs
print("OK — strike 2 intensifies only the struck enemy; seeded fire holds")

# ── 3. First direct strike on a seeded enemy fans the flame (no escalation) ──
msgs.clear()
hit(p, b, [a, b, c])
assert tier(b) == 3 and not burn_entry(b).get("sunfire_seed"), burn_entry(b)
hit(p, b, [a, b, c])
assert tier(b) == 4, tier(b)
assert tier(c) == 3, "seed-only enemies must stay at Blaze"
print("OK — seeded enemy: first strike fans, second intensifies (2 strikes per enemy)")

# ── 4. One full AoE action must NOT escalate the pack ──
p = make_player()
a, b, c = make_enemy("A"), make_enemy("B"), make_enemy("C")
msgs.clear()
aoe_cast(p, [a, b, c])
assert [tier(a), tier(b), tier(c)] == [3, 3, 3], (tier(a), tier(b), tier(c))
assert not any(d["tier"] >= 4 for e in (a, b, c) for d in e["active_debuffs"] if d["type"] == "burn")
assert sum("spreads to" in m for m in msgs) == 1, msgs
assert sum("intensify" in m for m in msgs) == 0, msgs
assert [e["con_mod"] for e in (a, b, c)] == [4, 4, 4], "one CON shred each"
print("OK — one AoE action: whole pack at Blaze, zero escalation, one CON shred each")

# ── 5. Second AoE action: pack reaches Inferno (two applications, two actions) ──
msgs.clear()
aoe_cast(p, [a, b, c])
assert [tier(a), tier(b), tier(c)] == [4, 4, 4], (tier(a), tier(b), tier(c))
assert sum("intensify into Inferno" in m for m in msgs) == 3, msgs
assert [e["con_mod"] for e in (a, b, c)] == [4, 4, 4], "no extra CON shred on escalation"
print("OK — second AoE action: pack reaches Inferno, still one CON shred each")

# ── 6. Non-bonded control: no spread, ladder climbs one step per strike ──
p = make_player(bonded=False)
d = make_enemy("D")
msgs.clear()
hit(p, d, [d])
assert tier(d) == 2, tier(d)
hit(p, d, [d])
assert tier(d) == 3, tier(d)
hit(p, d, [d])
assert tier(d) == 3, "a T2 source cannot push past Blaze"
assert not any("spreads to" in m for m in msgs), msgs
assert not burn_entry(d).get("sunfire_seed")
print("OK — non-bonded: Burn -> Blaze ladder, no spread, no seed flag")

# ── 7. Resistance still blocks the direct hit and is reported honestly ──
p = make_player()
e_res, f = make_enemy("Resister", status_res=1.0), make_enemy("F")
msgs.clear()
hit(p, e_res, [e_res, f])
assert tier(e_res) is None, burn_entry(e_res)
assert any("resists the legendary flame" in m for m in msgs), msgs
assert tier(f) == 3 and burn_entry(f).get("sunfire_seed"), "spread still seeds the others"
print("OK — resist blocks the hit and is reported; spread still seeds the others")

print("\nAll Sunfire Band seed checks passed.")
