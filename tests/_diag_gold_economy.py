"""Diagnostic: gold economy — Phase 1 house/scroll and Phase 3 market index.

Covers docs/gold_economy_pacing_design.md:
  * house floor multiplier 1 + min(3, floor/15), capped at 4x
  * income paid in full (no hidden upkeep), bank capped at 5 days
  * value-derived scroll ladder (2,000 / 2,800 / 4,400 / 8,000 / 16,000)
  * market index k(anchor) + kill-gold offset (D9–D12)
  * 20k-kill loot-share table at L5/L20/L42

Run from repo root with:
    .venv\\Scripts\\python.exe tests\\_diag_gold_economy.py
"""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from facilities.house import (
    HOUSE_LEVELS, MAX_INCOME_DAYS, _daily_income, _house_floor_mult,
    _pending_income,
)
from facilities.arcane_tower import _scroll_craft_cost
from resources.items import (
    ITEMS, build_item, item_value, market_anchor_level, market_index,
    market_value, kill_gold_offset,
)
from dungeon import ENEMIES, roll_drop, roll_gold_drop


def sim_loot(level, n=20_000):
    """Average unindexed loot sell value per kill at a given enemy level."""
    random.seed(9000 + level)
    loot = 0.0
    for _ in range(n):
        drop = roll_drop(level)
        if not drop:
            continue
        item_id, rarity = drop
        item = build_item(item_id, rarity)
        if not item:
            continue
        if item.get("type") == "equipment":
            loot += 2.5 * item_value(item)
        elif item.get("type") == "consumable":
            loot += 12
    return loot / n


def make_player(day=40, floor=40):
    return {
        "day": day,
        "max_floor": floor,
        "city_floors": {},
        "houses": {},
        "gold": 0,
    }


def make_house(level=8, last_day=1):
    return {"level": level, "storage": [], "last_income_day": last_day}


def main():
    ok = True

    def check(label, cond, detail=""):
        nonlocal ok
        if cond:
            print(f"PASS  {label}")
        else:
            ok = False
            print(f"FAIL  {label}  {detail}")

    check("bank cap is 5 days", MAX_INCOME_DAYS == 5, f"got {MAX_INCOME_DAYS}")

    p40 = make_player(floor=40)
    check("F40 floor multiplier ~3.667",
          abs(_house_floor_mult(p40) - (1.0 + 40 / 15.0)) < 1e-9,
          f"got {_house_floor_mult(p40):.4f}")
    check("floor multiplier caps at 4.0",
          abs(_house_floor_mult(make_player(floor=100)) - 4.0) < 1e-9,
          f"got {_house_floor_mult(make_player(floor=100)):.4f}")

    income = _daily_income(p40, "tidebreak", 8)
    check("F40 Sanctuary/Tidebreak income 2640", income == 2640, f"got {income}")

    p = make_player(day=40, floor=40)
    h = make_house(level=8, last_day=30)  # 10 days banked -> capped at 5
    check("10-day bank caps at 5 (13200)",
          _pending_income(p, "tidebreak", h) == 13200,
          f"got {_pending_income(p, 'tidebreak', h)}")

    expected = {"common": 2000, "uncommon": 2800, "rare": 4400,
                "epic": 8000, "legendary": 16000}
    got = {r: _scroll_craft_cost(r) for r in expected}
    check("scroll ladder is value-derived", got == expected, f"got {got}")

    # ── Market index (Phase 3) ───────────────────────────────────────────
    for lvl, expected_k in ((3, 1.0), (5, 1.0), (10, 2.5), (20, 4.5),
                            (30, 6.0), (42, 8.4), (80, 8.5)):
        check(f"market index L{lvl} = {expected_k}",
              abs(market_index(lvl) - expected_k) < 1e-9,
              f"got {market_index(lvl):.4f}")

    check("anchor uses max(level, floor)",
          market_anchor_level({"level": 10, "max_floor": 30, "city_floors": {}}) == 30)
    check("anchor uses max(level, floor) 2",
          market_anchor_level({"level": 40, "max_floor": 20, "city_floors": {}}) == 40)

    for lvl, expected_offset in ((5, 0), (10, 10), (20, 26), (30, 46), (42, 73)):
        check(f"kill-gold offset L{lvl} = {expected_offset}",
              kill_gold_offset(lvl) == expected_offset,
              f"got {kill_gold_offset(lvl)}")

    weapon_key = next(k for k, v in ITEMS.items()
                      if v.get("type") == "equipment" and v.get("base_form")
                      and v.get("slot") == "weapon")
    sample = build_item(weapon_key, "legendary")
    expected_mv = int(round(item_value(sample) * market_index(42)))
    check("market_value = item_value x k",
          market_value(sample, 42) == expected_mv,
          f"got {market_value(sample, 42)} vs {expected_mv}")

    enemy_key = min(ENEMIES, key=lambda k: abs(ENEMIES[k]["level"] - 42))
    random.seed(123)
    plain = [roll_gold_drop(enemy_key) for _ in range(50)]
    random.seed(123)
    offset_rolls = [roll_gold_drop(enemy_key, player={"level": 42, "max_floor": 42})
                    for _ in range(50)]
    check("kill gold offset applied after bonus",
          all(a - b == kill_gold_offset(42) for a, b in zip(plain, offset_rolls)),
          f"got {plain[0] - offset_rolls[0]}")

    print("\nMarket index phase table (normal drops, 20k kills):")
    for level in (5, 20, 42):
        loot = sim_loot(level)
        old_kill = 1.15 * (8 * level + 10)
        new_kill = old_kill - kill_gold_offset(level)
        new_loot = loot * market_index(level)
        old_share = 100 * loot / (old_kill + loot)
        new_share = 100 * new_loot / (new_kill + new_loot)
        print(f"  L{level:<2}  old kill {old_kill:6.1f}  loot {loot:5.1f}  "
              f"share {old_share:4.1f}%  |  new kill {new_kill:6.1f}  "
              f"loot {new_loot:6.1f}  share {new_share:4.1f}%")

    print("\nHouse income/day by level (Tidebreak x1.5, F40):")
    for lvl, data in HOUSE_LEVELS.items():
        print(f"  Lv{lvl} {data['name']:<10} {_daily_income(p40, 'tidebreak', lvl):>5}")

    print("\nSanctuary floor scaling (Tidebreak x1.5):")
    for label, floor in (("Early", 5), ("Mid", 20), ("Late", 40), ("Endgame", 60)):
        pp = make_player(floor=floor)
        print(f"  {label:<8} F{floor:<2}  {_daily_income(pp, 'tidebreak', 8):>6}/day")

    print("\nF40 Sanctuary summary:")
    print(f"  Income/day      : {income:,}")
    print(f"  {MAX_INCOME_DAYS}-day bank     : {income * MAX_INCOME_DAYS:,}")
    print(f"  Legendary scroll: {_scroll_craft_cost('legendary'):,}g")

    if not ok:
        sys.exit(1)
    print("\ngold economy diagnostics OK")


if __name__ == "__main__":
    main()
