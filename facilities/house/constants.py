"""facilities/house/constants.py — static house data and tuning.

Pure data: no player state, no UI. Tiers, caps, income multipliers, and the
affection/engagement/awakening thresholds that the house screens enforce.
"""

RECRUIT_AFFECTION_THRESHOLD = 50  # Minimum affection needed to recruit a girl

# ── House tiers ──────────────────────────────────────────────────────────────

HOUSE_LEVELS = {
    1: {"name": "Hovel",     "storage_cap": 10,  "income_per_day": 8,   "rest_minutes": 30, "upgrade_cost": 600,   "bed_buff_value": 0, "bed_buff_floors": 1},
    2: {"name": "Cottage",   "storage_cap": 20,  "income_per_day": 18,  "rest_minutes": 25, "upgrade_cost": 1500,  "bed_buff_value": 0, "bed_buff_floors": 2},
    3: {"name": "Manor",     "storage_cap": 35,  "income_per_day": 35,  "rest_minutes": 20, "upgrade_cost": 3000,  "bed_buff_value": 1, "bed_buff_floors": 3},
    4: {"name": "Villa",     "storage_cap": 55,  "income_per_day": 65,  "rest_minutes": 15, "upgrade_cost": 6000,  "bed_buff_value": 1, "bed_buff_floors": 4},
    5: {"name": "Estate",    "storage_cap": 80,  "income_per_day": 110, "rest_minutes": 10, "upgrade_cost": 12000, "bed_buff_value": 2, "bed_buff_floors": 5},
    6: {"name": "Palace",    "storage_cap": 120, "income_per_day": 200, "rest_minutes": 10, "upgrade_cost": 25000, "bed_buff_value": 2, "bed_buff_floors": 6},
    7: {"name": "Citadel",   "storage_cap": 170, "income_per_day": 320, "rest_minutes": 5,  "upgrade_cost": 50000, "bed_buff_value": 2, "bed_buff_floors": 7},
    8: {"name": "Sanctuary", "storage_cap": 230, "income_per_day": 480, "rest_minutes": 5,  "upgrade_cost": None,  "bed_buff_value": 3, "bed_buff_floors": 8},
}

HOUSE_MONSTER_GIRL_LIMITS = {
    1: 2,    # Hovel
    2: 4,    # Cottage
    3: 8,    # Manor
    4: 14,   # Villa
    5: 24,   # Estate
    6: 50,   # Palace  (room for 48 current + future)
    7: 75,   # Citadel
    8: 100,  # Sanctuary
}

# Multiplier on income per day based on a city's wealth (derived from inn cost).
# Wealthier cities yield more passive income.
CITY_INCOME_MULT = {
    "solmere":     1.0,
    "greyharbor":  1.0,
    "elderfen":    0.8,
    "thornwall":   0.9,
    "stormhold":   0.9,
    "irondeep":    1.1,
    "skylume":     1.4,
    "cinderpeak":  1.2,
    "veilholt":    1.1,
    "sunreach":    1.0,
    "brinewatch":  1.2,
    "mirefall":    0.7,
    "ashkara":     1.3,
    "dunemar":     1.1,
    "saltmarsh":   0.8,
    "tidebreak":   1.5,
    "coralhaven":  1.3,
    "blackwake":   0.9,
    "isle_of_glass": 1.6,
}

MAX_INCOME_DAYS = 5  # Income caps after this many days (prevents idle exploit)
HOUSE_FLOOR_BONUS_CAP = 3.0  # floor multiplier = 1 + min(cap, highest_floor / divisor)
HOUSE_FLOOR_BONUS_DIVISOR = 15.0

# ── Engagement ───────────────────────────────────────────────────────────────

ENGAGEMENT_RING_IDS = {
    "ruby_engagement_ring", "sapphire_engagement_ring", "emerald_engagement_ring",
    "topaz_engagement_ring", "amethyst_engagement_ring", "diamond_engagement_ring",
}

# ── Awakening (docs/awakening_design.md Part C) ─────────────────────────────

AWAKEN_LEVEL_REQ = 40
AWAKEN_CAP_REQ = 40
AWAKEN_AFFECTION_REQ = 200
