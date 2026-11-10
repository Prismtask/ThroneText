# Temp check (2026-11-06): neutral enemies get a physical/magical attack trait.
#
# Repro: the Human race has an empty elemental profile, so Elite Assassin /
# Bandit Bruiser showed no attack tag at all (not even PHY or MAG).
#
# Run: .venv\Scripts\python.exe tests\_temp_human_elemental_check.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from combat.elemental import compute_enemy_elemental, DEFAULT_ATTACK_MULTIPLIER
from combat.combat_ui import _get_entity_elem_tags


def profile(key):
    res, dmg = compute_enemy_elemental({"key": key})
    return res, dmg


def tag(key):
    res, dmg = profile(key)
    return _get_entity_elem_tags(
        {"name": key, "elemental_res": res, "elemental_dmg": dmg},
        is_enemy=True,
    )


def main():
    # Martial humans → physical fallback.
    for key in ("elite_assassin", "bandit_bruiser", "human_swordmaster",
                "city_guard", "human_bounty_hunter", "human_fencer"):
        _, dmg = profile(key)
        assert dmg == {"physical": DEFAULT_ATTACK_MULTIPLIER}, (key, dmg)
        assert "⚔PHY" in tag(key), (key, tag(key))
        print(f"OK — {key}: ⚔PHY")

    # "Mage" names already have the magical keyword (1.4); other caster
    # names use the magical fallback (1.2).
    for key in ("novice_mage", "human_high_mage"):
        _, dmg = profile(key)
        assert dmg == {"magical": 1.4}, (key, dmg)
        assert "⚔MAG" in tag(key), (key, tag(key))
        print(f"OK — {key}: ⚔MAG (keyword)")
    for key in ("cultist",):
        _, dmg = profile(key)
        assert dmg == {"magical": DEFAULT_ATTACK_MULTIPLIER}, (key, dmg)
        assert "⚔MAG" in tag(key), (key, tag(key))
        print(f"OK — {key}: ⚔MAG (fallback)")

    # Existing race/keyword traits must be untouched.
    _, gnome = profile("gnome_potion_thrower")
    assert gnome == {"thunder": 1.3}, gnome
    _, skeleton = profile("skeleton")
    assert skeleton == {"dark": 1.3}, skeleton
    _, blade = profile("elven_blade_dancer")
    assert blade == {"physical": 1.3}, blade
    _, dark_knight = profile("dark_knight")
    assert dark_knight == {"dark": 1.4}, dark_knight
    print("OK — race/keyword specialisations unchanged")

    # The HUD tag is driven by the same profile.
    assert "⚔THU" in tag("gnome_potion_thrower"), tag("gnome_potion_thrower")
    assert "⚔DAR" in tag("skeleton"), tag("skeleton")
    print("OK — HUD tags follow the resolved profile")

    print("\nAll human elemental-fallback checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
