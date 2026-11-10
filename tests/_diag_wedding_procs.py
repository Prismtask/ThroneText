"""Diag: wedding accessory procs on glove workshops + skills (2026-10-04).

Before this fix, wedding hooks (attack bonus / on-hit / on-kill) fired ONLY on
basic attacks. Black Silence gloves replace basic attacks (and all skills) with
workshop attacks, so glove users could never proc their wedding item at all.
Skills had the same gap. This verifies both pipelines now proc.

Run:
    .venv\\Scripts\\python.exe tests\\_diag_wedding_procs.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from character import build_character
from resources.items import build_item

ATTRS = {"Strength": 5, "Constitution": 5, "Dexterity": 5,
         "Learning": 5, "Wisdom": 5, "Charisma": 5}


def make_player():
    p = build_character("1", "1", ATTRS, "prism", 1)
    p["equipped"]["accessory1"] = build_item("wedding_ninetales_fox")  # legendary_flame
    return p


def make_enemy():
    return {"name": "Wolf", "hp": 500, "max_hp": 500, "con_mod": 5, "dex_mod": 5,
            "active_debuffs": [], "active_buffs": [], "elemental_res": {}, "spd": 5}


def has_burn(enemy):
    return any(d.get("type") == "burn" for d in enemy.get("active_debuffs", []))


def main():
    from combat.weapon import black_silence_gloves as g

    # 1. Workshop hit procs the wedding on-hit (legendary_flame burn).
    player = make_player()
    enemy = make_enemy()
    g._execute_workshop_actor(player, [enemy], 1, 10, 10, 10, 10, 10, 10)
    assert has_burn(enemy), f"no burn from workshop hit: {enemy['active_debuffs']}"
    assert player.get("wedding_first_attack_done"), "first-attack flag not consumed"
    print("OK — workshop hit procs wedding on-hit (burn)")

    # 2. Furioso hits use the same helper.
    player2 = make_player()
    enemy2 = make_enemy()
    g._execute_furioso_actor(player2, [enemy2], 10, 10, 10, 10, 10, 10)
    assert has_burn(enemy2), f"no burn from Furioso: {enemy2['active_debuffs']}"
    print("OK — Furioso hit procs wedding on-hit (burn)")

    # 3. Skill hits proc via execute_skill (skills count as attacks now).
    from combat.skills import get_available_skills, execute_skill, unlock_skills_for_level
    player3 = make_player()
    player3["level"] = 20                      # fresh characters have no skills yet
    unlock_skills_for_level(player3)
    enemy3 = make_enemy()
    skills = get_available_skills(player3)
    assert skills, "no skills to test with"
    proc = False
    for sid, _sdef in skills:
        try:
            execute_skill(player3, sid, [enemy3], 10, 10, 10, 10, 10, 10)
        except Exception:
            continue
        if has_burn(enemy3):
            proc = True
            break
    assert proc, f"no wedding proc via skills (tried {len(skills)}): {enemy3['active_debuffs']}"
    print("OK — skill hit procs wedding on-hit (burn)")

    # 4. Non-wedding actors are unaffected (no flags/state pollution).
    plain = build_character("1", "1", ATTRS, "plain", 1)
    enemy4 = make_enemy()
    g._execute_workshop_actor(plain, [enemy4], 1, 10, 10, 10, 10, 10, 10)
    assert not has_burn(enemy4), "procs fired without a wedding item"
    print("OK — no wedding item, no procs")

    # 5. Bonded Stardust Crown (starfire_breath): attacks inflict Burn — the
    #    bonded rider was in the design doc but never implemented until now.
    player5 = make_player()
    player5["equipped"]["accessory1"] = build_item("wedding_dragon_goddess_avatar")
    player5["allies"] = [{"key": "dragon_goddess_avatar", "name": "Dragon Goddess Avatar"}]
    enemy5 = make_enemy()
    g._execute_workshop_actor(player5, [enemy5], 1, 10, 10, 10, 10, 10, 10)
    assert has_burn(enemy5), f"no starfire burn (bonded): {enemy5['active_debuffs']}"
    print("OK — bonded Stardust Crown burn procs")

    # 6. Blurb table speaks burn-tier names (Burn / Blaze), not pre-rework numbers.
    from combat.weapon.wedding_specials import wedding_special_blurb
    base_blurb = wedding_special_blurb("legendary_flame")
    bonded_blurb = wedding_special_blurb("legendary_flame", bonded=True)
    assert "Burn" in base_blurb and "6" not in base_blurb, f"stale base blurb: {base_blurb!r}"
    assert "Blaze" in bonded_blurb and "10" not in bonded_blurb, f"stale bonded blurb: {bonded_blurb!r}"
    print("OK — blurb uses burn tier names (Burn/Blaze)")

    print("\nAll wedding proc checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
