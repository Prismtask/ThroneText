# resources/trade_goods.py
"""
Cargo trading system — goods, demand, and weight helpers.

Cargo is an inventory item type (`"type": "cargo"`) that bypasses bag capacity
but counts against the player's mount cargo capacity and slows travel.
Full design: docs/cargo_trade_design.md
"""

from inventory import get_cargo_items

# ── Themes: what kind of market a good appeals to ──────────────────────────
THEMES = ("mountain", "sea", "exotic", "luxury", "common")

# ── Goods table ────────────────────────────────────────────────────────────
# Each good: name, theme, weight (unit measurement), base_price, origin city.
TRADE_GOODS = {
    # Common
    "stormhold_furs":      {"name": "Stormhold Furs",       "theme": "common",   "weight": 10, "base_price": 50, "origin": "stormhold"},
    "mirefall_peat":       {"name": "Mirefall Peat",        "theme": "common",   "weight": 20, "base_price": 35, "origin": "mirefall"},
    # Mountain
    "cinderpeak_ore":      {"name": "Cinderpeak Ore",       "theme": "mountain", "weight": 20, "base_price": 70, "origin": "cinderpeak"},
    "irondeep_ingots":     {"name": "Irondeep Ingots",      "theme": "mountain", "weight": 25, "base_price": 85, "origin": "irondeep"},
    "sunreach_steel":      {"name": "Sun-Steel Ingots",     "theme": "mountain", "weight": 20, "base_price": 90, "origin": "sunreach"},
    # Sea
    "greyharbor_pearls":   {"name": "Greyharbor Pearls",    "theme": "sea",      "weight": 5,  "base_price": 80, "origin": "greyharbor"},
    "brinewatch_saltfish": {"name": "Brinewatch Saltfish",  "theme": "sea",      "weight": 10, "base_price": 40, "origin": "brinewatch"},
    "saltmarsh_salt":      {"name": "Saltmarsh Salt",       "theme": "sea",      "weight": 15, "base_price": 45, "origin": "saltmarsh"},
    "coralhaven_coral":    {"name": "Coralhaven Coral",     "theme": "sea",      "weight": 10, "base_price": 60, "origin": "coralhaven"},
    "tidebreak_whaleoil":  {"name": "Tidebreak Whale Oil",  "theme": "sea",      "weight": 20, "base_price": 95, "origin": "tidebreak"},
    # Exotic
    "dunemar_spices":      {"name": "Dunemar Spices",       "theme": "exotic",   "weight": 5,  "base_price": 75, "origin": "dunemar"},
    "elderfen_herbs":      {"name": "Elderfen Herbs",       "theme": "exotic",   "weight": 5,  "base_price": 55, "origin": "elderfen"},
    # Luxury
    "solmere_porcelain":   {"name": "Solmere Porcelain",    "theme": "luxury",   "weight": 10, "base_price": 60, "origin": "solmere"},
    "sunreach_silk":       {"name": "Sunreach Silk",        "theme": "luxury",   "weight": 5,  "base_price": 70, "origin": "sunreach"},
    "skylume_crystals":    {"name": "Skylume Crystals",     "theme": "luxury",   "weight": 10, "base_price": 85, "origin": "skylume"},
}

# ── Static per-city demand by theme (default 1.0) ──────────────────────────
# Higher = better sell price. Themed: mountain goods fetch top gold at beach
# cities, sea goods inland, etc.
CITY_DEMAND = {
    "stormhold":    {"mountain": 1.1, "sea": 1.4, "exotic": 1.5, "luxury": 1.3, "common": 0.9},
    "thornwall":    {"mountain": 1.2, "sea": 1.3, "exotic": 1.0, "luxury": 0.9, "common": 1.1},
    "solmere":      {"mountain": 1.0, "sea": 1.1, "exotic": 1.2, "luxury": 1.5, "common": 1.0},
    "greyharbor":   {"mountain": 1.3, "sea": 0.9, "exotic": 1.1, "luxury": 1.2, "common": 1.1},
    "elderfen":     {"mountain": 1.2, "sea": 0.9, "exotic": 1.2, "luxury": 0.8, "common": 1.0},
    "irondeep":     {"mountain": 0.8, "sea": 1.4, "exotic": 1.3, "luxury": 1.1, "common": 1.2},
    "skylume":      {"mountain": 0.9, "sea": 1.1, "exotic": 1.2, "luxury": 1.5, "common": 1.0},
    "cinderpeak":   {"mountain": 0.8, "sea": 1.3, "exotic": 1.1, "luxury": 1.2, "common": 1.0},
    "veilholt":     {"mountain": 1.0, "sea": 1.0, "exotic": 1.3, "luxury": 1.1, "common": 1.1},
    "sunreach":     {"mountain": 1.1, "sea": 1.5, "exotic": 1.0, "luxury": 1.2, "common": 1.4},
    "brinewatch":   {"mountain": 1.5, "sea": 0.8, "exotic": 1.2, "luxury": 1.3, "common": 1.2},
    "mirefall":     {"mountain": 1.3, "sea": 1.1, "exotic": 1.1, "luxury": 0.8, "common": 0.9},
    "ashkara":      {"mountain": 1.2, "sea": 1.4, "exotic": 1.1, "luxury": 1.2, "common": 1.1},
    "dunemar":      {"mountain": 1.2, "sea": 1.3, "exotic": 0.9, "luxury": 1.4, "common": 1.2},
    "saltmarsh":    {"mountain": 1.5, "sea": 0.8, "exotic": 1.2, "luxury": 1.2, "common": 1.1},
    "tidebreak":    {"mountain": 1.4, "sea": 0.9, "exotic": 1.1, "luxury": 1.3, "common": 1.1},
    "coralhaven":   {"mountain": 1.1, "sea": 0.8, "exotic": 1.3, "luxury": 1.6, "common": 1.2},
    "blackwake":    {"mountain": 1.1, "sea": 1.0, "exotic": 1.2, "luxury": 1.2, "common": 1.2},
    "isle_of_glass": {"mountain": 1.2, "sea": 1.1, "exotic": 1.1, "luxury": 1.1, "common": 1.1},
    "wonderland":   {"mountain": 1.2, "sea": 1.2, "exotic": 1.2, "luxury": 1.2, "common": 1.2},
}

# ── Balance constants ──────────────────────────────────────────────────────
BUY_MULT          = 0.6    # buy at 60% of base price
ORIGIN_SELL_MULT  = 0.7    # selling in the origin city loses money
OVERLOAD_CAP      = 1.8    # hard overload cap (× capacity)
MAX_LOAD_PENALTY  = 0.25   # +25% travel time at the overload cap
DAILY_RESTOCK     = 5      # units per good per city per day
ORIGIN_WEIGHT     = 5      # stock spawn weight for origin-city goods (others: 1)


def build_cargo(good_id):
    """Build a cargo inventory item dict from the goods table."""
    g = TRADE_GOODS[good_id]
    return {
        "id": good_id,
        "name": g["name"],
        "type": "cargo",
        "rarity": "common",
        "count": 1,
        "weight": g["weight"],
        "theme": g["theme"],
        "origin": g["origin"],
        "base_price": g["base_price"],
    }


def cargo_total_weight(player):
    """Total cargo weight in the player's inventory (unit measurement)."""
    return sum(
        i.get("weight", 0) * i.get("count", 1)
        for i in get_cargo_items(player)
    )


def cargo_capacity(player):
    """Mount cargo capacity in weight units, 0 with no mount."""
    mid = player.get("mount_id")
    if not mid:
        return 0
    from resources.mounts import get_mount
    mount = get_mount(mid)
    return mount.get("cargo_capacity", 0) if mount else 0


def cargo_overload_limit(player):
    """Hard cap = 1.8× capacity. Purchases past this are rejected."""
    return int(OVERLOAD_CAP * cargo_capacity(player))


def cargo_travel_penalty(player, capacity=None):
    """
    Return the travel-time penalty fraction (0.0 – MAX_LOAD_PENALTY).
    Ramps linearly from 0% at full load to MAX_LOAD_PENALTY at the overload
    cap. capacity=None uses the mount; pass a ship capacity for sea legs.
    No capacity + cargo = max penalty (mount sold while loaded).
    """
    if capacity is None:
        capacity = cargo_capacity(player)
    weight = cargo_total_weight(player)
    if weight <= 0:
        return 0.0
    if capacity <= 0:
        return MAX_LOAD_PENALTY
    limit = OVERLOAD_CAP * capacity
    if weight <= capacity:
        return 0.0
    ratio = min(1.0, (weight - capacity) / ((limit - capacity) or 1))
    return MAX_LOAD_PENALTY * max(0.0, ratio)


def cargo_overloaded_for_travel(player, capacity=None):
    """True when load exceeds the 1.8× hard cap of the given vehicle.

    capacity=None uses the mount. A capacity of 0 (no vehicle) is NOT
    blocked — that case gets the max travel penalty instead (decision #3).
    """
    if capacity is None:
        capacity = cargo_capacity(player)
    weight = cargo_total_weight(player)
    if weight <= 0:
        return False
    if capacity <= 0:
        return False
    return weight > OVERLOAD_CAP * capacity


def _cargo_charisma_discount(player):
    """Soft Charisma discount on cargo purchases (25% cap, road-merchant rule)."""
    from combat.stats import get_effective_attribute
    cha = get_effective_attribute(player, "Charisma")
    return min(25, max(0, (cha - 8) * 0.4)) / 100.0


def cargo_buy_price(good_id, player):
    """Price to buy one unit of a good (0.6× base, soft Charisma discount)."""
    g = TRADE_GOODS[good_id]
    disc = _cargo_charisma_discount(player)
    return max(1, int(g["base_price"] * BUY_MULT * (1 - disc)))


def cargo_demand(city_id, theme):
    """Static per-city demand multiplier for a theme (default 1.0)."""
    return CITY_DEMAND.get(city_id, {}).get(theme, 1.0)


def cargo_sell_price(cargo_item, player, city_id):
    """Sell price for one unit of a cargo item in a city."""
    if cargo_item.get("origin") == city_id:
        return max(1, int(cargo_item["base_price"] * ORIGIN_SELL_MULT))
    mult = cargo_demand(city_id, cargo_item.get("theme"))
    return max(1, int(cargo_item["base_price"] * mult))


def roll_daily_cargo_stock(city_id, count):
    """
    Pick `count` distinct goods for today's cargo market stock.
    Any good can appear; origin-city goods are ORIGIN_WEIGHT× more likely.
    """
    import random
    pool = list(TRADE_GOODS)
    weights = [
        ORIGIN_WEIGHT if TRADE_GOODS[gid]["origin"] == city_id else 1
        for gid in pool
    ]
    chosen = []
    for _ in range(count):
        if not pool:
            break
        pick = random.choices(pool, weights=weights, k=1)[0]
        chosen.append(pick)
        idx = pool.index(pick)
        pool.pop(idx)
        weights.pop(idx)
    return chosen


def roll_cargo_good(city_id=None):
    """
    Pick a single random cargo good. Any good can spawn anywhere; when a
    city is given, its origin goods are ORIGIN_WEIGHT× more likely.
    """
    import random
    if city_id is None:
        return random.choice(list(TRADE_GOODS))
    return roll_daily_cargo_stock(city_id, 1)[0]


def cargo_merchant_stock_price(good_id, player):
    """
    Road/dungeon/guild merchant sale price for one unit of a cargo good:
    the market buy price with a 75–90% road markdown, like normal wares.
    Returns (your_price, road_price).
    """
    import random
    road_price = cargo_buy_price(good_id, player)
    your_price = max(1, int(road_price * random.uniform(0.75, 0.90)))
    return your_price, road_price


def cargo_merchant_sell_price(item, city_id=None):
    """
    What a merchant pays for one unit of the player's cargo: 75% of the
    shop demand sell price. city_id=None → flat road rate (demand 1.0);
    guild merchants pass their city for the local demand.
    """
    if city_id and item.get("origin") == city_id:
        mult = ORIGIN_SELL_MULT
    else:
        mult = cargo_demand(city_id, item.get("theme")) if city_id else 1.0
    return max(1, int(item["base_price"] * mult * 0.75))
