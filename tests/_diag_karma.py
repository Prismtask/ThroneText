"""Diagnostic: Karma Phase 1 foundation.

Checks tier boundaries, toggle behavior, daily cap, legacy favor handling,
Karma-only shop/bill math, gate responses, and character-creation rule plumbing.
Headless — no save mutation.

Run:  .venv\\Scripts\\python.exe tests\\_diag_karma.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import karma
from character import build_character, ensure_player_fields


def make_player(charisma=8, karma_value=0, enabled=True):
    return {
        "attributes": {
            "Strength": 8, "Constitution": 8, "Dexterity": 8,
            "Wisdom": 8, "Learning": 8, "Charisma": charisma,
        },
        "equipped": {"weapon": None, "armor": None,
                     "accessory1": None, "accessory2": None},
        "active_buffs": [],
        "active_debuffs": [],
        "passive_unlocked": False,
        "karma_enabled": enabled,
        "karma": karma_value,
        "karma_migrated": True,
        "karma_log": [],
        "karma_daily": {"day": 0, "gained": 0},
        "karma_gate": {
            "cooldown": {}, "warning_seen": False,
            "watched_until": 0, "jail_karma_day": -99,
        },
        "daily_effects": {},
        "day": 1,
        "level": 10,
        "journal": {"events": [], "main_quests": [], "side_quests": []},
    }


# 1. Tier boundaries ------------------------------------------------------
cases = [
    (-100, "Outlaw"), (-75, "Outlaw"), (-74, "Wanted"), (-50, "Wanted"),
    (-49, "Suspect"), (-25, "Suspect"), (-24, "Shady"), (-10, "Shady"),
    (-9, "Neutral"), (0, "Neutral"), (9, "Neutral"), (10, "Good"),
    (24, "Good"), (25, "Respected"), (49, "Respected"), (50, "Virtuous"),
    (79, "Virtuous"), (80, "Paragon"), (100, "Paragon"),
]
for value, label in cases:
    got = karma.get_karma_tier({"karma": value, "karma_enabled": True})["label"]
    assert got == label, (value, got, label)
print("[OK] tier boundaries")

# 2. Toggle behavior ------------------------------------------------------
p = make_player(enabled=False, karma_value=50)
assert karma.is_enabled(p) is False
assert karma.get_shop_karma_pct(p) == 0
assert karma.get_bills_mult(p) == 1.0
assert karma.change_karma(p, 10, "disabled") == 0
assert p["karma"] == 50
assert karma.get_gate_response(p, "solmere") is None
print("[OK] disabled toggle is inert")

# 3. Daily cap and negative uncapped -------------------------------------
p = make_player(karma_value=0)
assert karma.change_karma(p, 5, "deed") == 5
assert karma.change_karma(p, 5, "deed") == 3       # +8/day cap
assert karma.change_karma(p, 1, "deed") == 0       # cap reached
assert karma.change_karma(p, -10, "crime") == -10   # negative uncapped
assert p["karma"] == -2
p["day"] = 2
assert karma.change_karma(p, 10, "quest", bypass_cap=True) == 10
assert p["karma"] == 8
assert len(p["karma_log"]) == 4
print("[OK] daily cap (+8) and uncapped negative")

# 4. Clamp ---------------------------------------------------------------
p = make_player(karma_value=99)
assert karma.change_karma(p, 10, "cap", bypass_cap=True) == 1
assert p["karma"] == 100
p["karma"] = -99
assert karma.change_karma(p, -10, "floor") == -1
assert p["karma"] == -100
print("[OK] Karma clamps to -100..+100")

# 5. Legacy helper no longer reads City Favor --------------------------
p = {
    "favor": {"solmere": 60, "greyharbor": 40},   # legacy data, deliberately ignored
    "karma_enabled": False,
    "karma_migrated": False,
    "day": 1,
    "journal": {"events": [], "main_quests": [], "side_quests": []},
}
assert karma.enable_karma(p) is True
assert p["karma_enabled"] is True
assert p["karma"] == 0          # no favor seed; Karma stays where it was
assert karma.enable_karma(p) is False
assert p["karma"] == 0          # enabling again never reseeds
print("[OK] legacy helper ignores City Favor")

# 5b. ensure_player_fields defaults a pre-Karma save to OFF ---------------
attrs = {
    "Strength": 10, "Constitution": 10, "Dexterity": 10,
    "Wisdom": 10, "Learning": 10, "Charisma": 10,
}
old = build_character("1", "1", attrs, "OldSave", 903)
for key in ("karma_enabled", "karma_migrated", "family_enabled",
            "difficulty", "game_rules_version", "karma", "karma_log",
            "karma_daily", "karma_gate"):
    old.pop(key, None)
ensure_player_fields(old)
assert old["karma_enabled"] is False
assert old["karma_migrated"] is False
assert old["family_enabled"] is False
assert old["difficulty"] == "normal"
assert old["game_rules_version"] == 1
assert old["karma_gate"]["warning_seen"] is False
assert old["karma"] == 0          # no player-facing enable/seed
print("[OK] ensure_player_fields defaults pre-Karma saves to OFF")

# 6. Shop formula --------------------------------------------------------
from facilities.shop import get_discounted_price
from resources.cities import CITIES
assert "guild" in CITIES["solmere"]["services"]
assert "guild" not in CITIES["stormhold"]["services"]

base = 1000
p = make_player(charisma=88, karma_value=100)
assert get_discounted_price(base, p, "solmere") == 400   # 40% CHA + 20% Karma
p = make_player(charisma=8, karma_value=-100)
assert get_discounted_price(base, p, "solmere") == 1200  # 20% surcharge
p = make_player(charisma=8, karma_value=100)
assert get_discounted_price(base, p, "stormhold") == 800  # no city-specific score
assert get_discounted_price(base, p, "solmere") == 800
p = make_player(charisma=8, karma_value=0, enabled=False)
assert get_discounted_price(base, p, "solmere") == 1000   # Charisma only
p = make_player(charisma=88, karma_value=0, enabled=False)
assert get_discounted_price(base, p, "solmere") == 600    # 40% off, no favor

# Tax Day: high Karma exempt, low Karma pays double, off is Charisma-only.
p = make_player(charisma=8, karma_value=0)
p["daily_effects"] = {"shop_surcharge": 0.15}
assert get_discounted_price(base, p, "solmere") == 1150
p = make_player(charisma=8, karma_value=50)
p["daily_effects"] = {"shop_surcharge": 0.15}
assert get_discounted_price(base, p, "solmere") == 850
p = make_player(charisma=8, karma_value=-50)
p["daily_effects"] = {"shop_surcharge": 0.15}
assert get_discounted_price(base, p, "solmere") == 1495
p = make_player(charisma=8, karma_value=0, enabled=False)
p["daily_effects"] = {"shop_surcharge": 0.15}
assert get_discounted_price(base, p, "solmere") == 1150
print("[OK] shop formula (Karma, Charisma-only, Tax Day)")

# 7. Bills multiplier ----------------------------------------------------
p = make_player(karma_value=80)
assert abs(karma.get_bills_mult(p) - 0.70) < 1e-9
p = make_player(karma_value=-80)
assert abs(karma.get_bills_mult(p) - 1.20) < 1e-9
p = make_player(karma_value=80, enabled=False)
assert karma.get_bills_mult(p) == 1.0
print("[OK] bills multiplier")

# 8. Black Market inverse pricing ---------------------------------------
from facilities.black_market import _karma_price
p = make_player(karma_value=-100)
assert _karma_price(p, 1000) == 800
p = make_player(karma_value=100)
assert _karma_price(p, 1000) == 1000
p = make_player(karma_value=-100, enabled=False)
assert _karma_price(p, 1000) == 1000
print("[OK] Black Market inverse pricing")

# 9. Gate responses ------------------------------------------------------
p = make_player(karma_value=-25)
assert karma.get_gate_response(p, "solmere")["tier"] == "warning"
p["karma_gate"]["warning_seen"] = True
assert karma.get_gate_response(p, "solmere")["tier"] == "suspect"
p["karma"] = -60
assert karma.get_gate_response(p, "solmere")["tier"] == "wanted"
p["karma"] = -80
assert karma.get_gate_response(p, "solmere")["tier"] == "outlaw"
assert karma.get_gate_response(p, "blackwake") is None
p["karma_gate"]["cooldown"]["solmere"] = 99
assert karma.get_gate_response(p, "solmere") is None
p = make_player(karma_value=-80, enabled=False)
assert karma.get_gate_response(p, "solmere") is None
print("[OK] gate responses and Blackwake exclusion")

# 10. Character creation plumbing ---------------------------------------
attrs = {
    "Strength": 10, "Constitution": 10, "Dexterity": 10,
    "Wisdom": 10, "Learning": 10, "Charisma": 10,
}
p_on = build_character("1", "1", attrs, "KarmaOn", 901)
assert p_on["karma_enabled"] is True
assert p_on["karma"] == 0
assert p_on["karma_migrated"] is True
p_off = build_character("1", "1", attrs, "KarmaOff", 902,
                        game_rules={"karma_enabled": False,
                                    "family_enabled": True,
                                    "difficulty": "hard"})
assert p_off["karma_enabled"] is False
assert p_off["karma_migrated"] is False   # legacy seeding flag (not player-facing)
assert p_off["family_enabled"] is True
assert p_off["difficulty"] == "hard"
print("[OK] build_character Game Rules plumbing")

# 11. Event choice labels include Karma once -----------------------------
import dungeon_rooms

captured = {}


def _fake_menu(options, **kwargs):
    captured["options"] = options
    return 0


_orig_tmenu = dungeon_rooms._tmenu
try:
    dungeon_rooms._tmenu = _fake_menu
    choice = dungeon_rooms._prompt_event_choice(
        dungeon_rooms.STAT_CHECK_EVENTS["forgotten_shrine"]["choices"]
    )
finally:
    dungeon_rooms._tmenu = _orig_tmenu

assert choice and choice["id"] == "offer"
assert captured["options"] == [
    "Leave 50 gold and pray (+2 Karma)",
    "Take the offerings (DEX check, +gold) (-3 Karma)",
], captured["options"]
print("[OK] event choice labels show Karma once")

print("\nAll Karma diagnostics passed.")
