"""Diag: wonderland wedding accessories + engagement-ring transfer (2026-10-14).

Covers the lounge marriage fixes:
1. The three new wonderland wedding items exist, build, and have blurbs.
2. homeward_locket: once per combat, below 35% HP — hearth-light heal
   (bonded: stronger + shares 5% with living allies).
3. rabbit_time: apply_wedding_initiative_bonus returns +2 (+3 bonded) and
   roll_initiative consumes it without errors.
4. huntsman_oath: first attack gets +30% (+45% bonded) bonus damage; no
   bonus on subsequent attacks.
5. _apply_ring_bonus_to_girl: folds base_mods into stored attributes and
   stores ring_stat_bonus; without stored attributes the bonus is applied
   dynamically by compute_girl_attributes.
6. _ally_to_house_record keeps ring_stat_bonus across the party round-trip.

Run:
    .venv\\Scripts\\python.exe tests\\_diag_wedding_wonderland.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from character import build_character, player_max_hp
from resources.items import build_item, ITEMS

ATTRS = {"Strength": 5, "Constitution": 5, "Dexterity": 5,
         "Learning": 5, "Wisdom": 5, "Charisma": 5}


def make_player(accessory=None, bonded_girl_key=None):
    p = build_character("1", "1", ATTRS, "prism", 1)
    if accessory:
        p["equipped"]["accessory1"] = build_item(accessory)
    if bonded_girl_key:
        p["allies"] = [{"name": "Bonded", "key": bonded_girl_key,
                        "current_hp": 5, "max_hp": 10}]
    return p


def main():
    from combat.weapon import wedding_specials as ws

    # 1. Items exist + are describable.
    for iid in ("wedding_wonderland_dorothy", "wedding_wonderland_alice",
                "wedding_wonderland_red_hood"):
        assert iid in ITEMS, f"missing item {iid}"
        item = build_item(iid)
        assert item.get("special"), f"{iid} has no special"
        assert ws.wedding_special_blurb(item["special"]), \
            f"no blurb for {item['special']}"
    print("OK — 3 wonderland wedding items exist with blurbs")

    # 2. homeward_locket — base heal, once per combat.
    p = make_player("wedding_wonderland_dorothy")
    ws.begin_wedding_combat(p)
    max_hp = player_max_hp(p)
    p["current_hp"] = 1
    ws.apply_wedding_on_damage_taken(p, {"name": "Wolf"}, 0, "hit")
    healed = p["current_hp"] - 1
    assert healed == int(max_hp * 0.20), f"homeward heal {healed} != {int(max_hp * 0.20)}"
    assert p["wedding_homeward_used"], "homeward flag not set"
    p["current_hp"] = 1
    ws.apply_wedding_on_damage_taken(p, {"name": "Wolf"}, 0, "hit")
    assert p["current_hp"] == 1, "homeward fired twice"
    print(f"OK — homeward_locket heals {healed} HP once per combat")

    # 2b. homeward_locket — bonded: stronger + party share.
    p = make_player("wedding_wonderland_dorothy", "wonderland_dorothy")
    ws.begin_wedding_combat(p)
    p["current_hp"] = 1
    ally_before = p["allies"][0]["current_hp"]
    ws.apply_wedding_on_damage_taken(p, {"name": "Wolf"}, 0, "hit")
    expected_hp = min(1 + int(player_max_hp(p) * 0.30), player_max_hp(p))
    assert p["current_hp"] == expected_hp, \
        f"bonded homeward heal {p['current_hp']} != {expected_hp}"
    assert p["allies"][0]["current_hp"] > ally_before, "bonded share did not heal ally"
    print("OK — bonded homeward_locket heals 30% + shares with allies")

    # 3. rabbit_time — initiative helper + roll_initiative integration.
    p = make_player("wedding_wonderland_alice")
    assert ws.apply_wedding_initiative_bonus(p) == 2
    p_b = make_player("wedding_wonderland_alice", "wonderland_alice")
    assert ws.apply_wedding_initiative_bonus(p_b) == 3
    from combat.combat_engine import roll_initiative
    order = roll_initiative(p, [{"name": "Wolf", "key": "wolf", "hp": 10, "max_hp": 10,
                                 "dex_mod": 5, "active_buffs": [], "active_debuffs": [],
                                 "elemental_res": {}}])
    assert order, "roll_initiative returned nothing"
    print("OK — rabbit_time grants +2 (+3 bonded) and rides roll_initiative")

    # 4. huntsman_oath — first attack only.
    p = make_player("wedding_wonderland_red_hood")
    assert ws.apply_wedding_attack_bonus(p, {"name": "Wolf"}, 100, True) >= 30
    assert ws.apply_wedding_attack_bonus(p, {"name": "Wolf"}, 100, False) == 0
    p_b = make_player("wedding_wonderland_red_hood", "wonderland_red_hood")
    assert ws.apply_wedding_attack_bonus(p_b, {"name": "Wolf"}, 100, True) >= 45
    print("OK — huntsman_oath boosts the first attack only (+30%/+45% bonded)")

    # 5. Engagement-ring transfer.
    from facilities.house import _apply_ring_bonus_to_girl
    from combat.ally import compute_girl_attributes
    ring = build_item("ruby_engagement_ring")
    ring_mods = dict(ring.get("mods") or {})
    assert ring_mods, "built ring has no mods"

    girl = {"attributes": {a: 10 for a in ATTRS}}
    out = _apply_ring_bonus_to_girl(girl, ring)
    assert out == ring_mods
    assert girl["attributes"]["Strength"] == 10 + ring_mods["Strength"], \
        "ring bonus not folded into stored attributes"
    assert girl["ring_stat_bonus"] == ring_mods
    # no stored attributes -> dynamic application at compute time
    bare = {"key": "goblin_girl", "level": 5}
    base = compute_girl_attributes(bare)
    with_ring = compute_girl_attributes({**bare, "ring_stat_bonus": {"Strength": 9}})
    assert with_ring["Strength"] == base["Strength"] + 9, "dynamic ring bonus missing"
    print("OK — ring bonus applies to stored and computed girls")

    # 6. Round-trip persistence.
    from combat.ally import _ally_to_house_record
    rec = _ally_to_house_record({"key": "x", "name": "X", "level": 1,
                                 "attributes": {}, "ring_stat_bonus": {"Charisma": 9}}, {})
    assert rec.get("ring_stat_bonus") == {"Charisma": 9}, "ring bonus lost on return home"
    print("OK — ring bonus survives the party round-trip")

    print("\nAll wonderland wedding checks passed.")


if __name__ == "__main__":
    main()
