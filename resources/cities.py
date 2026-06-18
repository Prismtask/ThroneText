from .dialogues import (
    # Solmere
    SOLMERE_RECEPTIONIST_DIALOGUE,
    SOLMERE_SHOPKEEPER_DIALOGUE,
    SOLMERE_INNKEEPER_DIALOGUE,
    SOLMERE_BLACKSMITH_DIALOGUE,
    SOLMERE_TRADE_HALL_DIALOGUE,
    SOLMERE_TEMPLE_DIALOGUE,

    # Brinewatch
    BRINEWATCH_RECEPTIONIST_DIALOGUE,
    BRINEWATCH_SHOPKEEPER_DIALOGUE,
    BRINEWATCH_INNKEEPER_DIALOGUE,
    BRINEWATCH_BLACKSMITH_DIALOGUE,
    BRINEWATCH_PORTMASTER_DIALOGUE,
    BRINEWATCH_SHIPYARD_DIALOGUE,
    BRINEWATCH_TRADE_HALL_DIALOGUE,

    # Greyharbor  (no longer has a port — inland river town)
    GREYHARBOR_RECEPTIONIST_DIALOGUE,
    GREYHARBOR_SHOPKEEPER_DIALOGUE,
    GREYHARBOR_INNKEEPER_DIALOGUE,
    GREYHARBOR_TRADE_HALL_DIALOGUE,

    # Elderfen
    ELDERFEN_RECEPTIONIST_DIALOGUE,
    ELDERFEN_SHOPKEEPER_DIALOGUE,
    ELDERFEN_INNKEEPER_DIALOGUE,
    ELDERFEN_HERBALIST_DIALOGUE,

    # Irondeep
    IRONDEEP_RECEPTIONIST_DIALOGUE,
    IRONDEEP_SHOPKEEPER_DIALOGUE,
    IRONDEEP_INNKEEPER_DIALOGUE,
    IRONDEEP_BLACKSMITH_DIALOGUE,
    IRONDEEP_BARRACKS_DIALOGUE,

    # Skylume
    SKYLUME_RECEPTIONIST_DIALOGUE,
    SKYLUME_SHOPKEEPER_DIALOGUE,
    SKYLUME_INNKEEPER_DIALOGUE,
    SKYLUME_ARCANE_TOWER_DIALOGUE,
    SKYLUME_GIFT_SHOP_DIALOGUE,

    # Ashkara
    ASHKARA_RECEPTIONIST_DIALOGUE,
    ASHKARA_SHOPKEEPER_DIALOGUE,
    ASHKARA_INNKEEPER_DIALOGUE,
    ASHKARA_BLACK_MARKET_DIALOGUE,
    ASHKARA_BLACKSMITH_DIALOGUE,

    # Sunreach  (no longer has a port — inland savanna city)
    SUNREACH_RECEPTIONIST_DIALOGUE,
    SUNREACH_SHOPKEEPER_DIALOGUE,
    SUNREACH_INNKEEPER_DIALOGUE,
    SUNREACH_TEMPLE_DIALOGUE,

    # Thornwall
    THORNWALL_RECEPTIONIST_DIALOGUE,
    THORNWALL_SHOPKEEPER_DIALOGUE,
    THORNWALL_INNKEEPER_DIALOGUE,
    THORNWALL_BARRACKS_DIALOGUE,

    # Dunemar  (no longer has a port — desert oasis city)
    DUNEMAR_RECEPTIONIST_DIALOGUE,
    DUNEMAR_SHOPKEEPER_DIALOGUE,
    DUNEMAR_INNKEEPER_DIALOGUE,
    DUNEMAR_TRADE_HALL_DIALOGUE,
    DUNEMAR_BLACK_MARKET_DIALOGUE,

    # Tidebreak  (major southern port hub)
    TIDEBREAK_RECEPTIONIST_DIALOGUE,
    TIDEBREAK_SHOPKEEPER_DIALOGUE,
    TIDEBREAK_INNKEEPER_DIALOGUE,
    TIDEBREAK_PORTMASTER_DIALOGUE,
    TIDEBREAK_SHIPYARD_DIALOGUE,
    TIDEBREAK_TRADE_HALL_DIALOGUE,

    # Stormhold  (northern fortress city — no port, land-locked)
    STORMHOLD_RECEPTIONIST_DIALOGUE,
    STORMHOLD_SHOPKEEPER_DIALOGUE,
    STORMHOLD_INNKEEPER_DIALOGUE,
    STORMHOLD_BARRACKS_DIALOGUE,
    STORMHOLD_GIFT_SHOP_DIALOGUE,

    # Coralhaven  (tropical island — sea access only)
    CORALHAVEN_RECEPTIONIST_DIALOGUE,
    CORALHAVEN_SHOPKEEPER_DIALOGUE,
    CORALHAVEN_INNKEEPER_DIALOGUE,
    CORALHAVEN_PORTMASTER_DIALOGUE,
    CORALHAVEN_HERBALIST_DIALOGUE,
    CORALHAVEN_TEMPLE_DIALOGUE,
    CORALHAVEN_GIFT_SHOP_DIALOGUE,

    # Blackwake  (hidden pirate cove — sea access only)
    BLACKWAKE_RECEPTIONIST_DIALOGUE,
    BLACKWAKE_INNKEEPER_DIALOGUE,
    BLACKWAKE_PORTMASTER_DIALOGUE,
    BLACKWAKE_BLACK_MARKET_DIALOGUE,

    # Isle of Glass  (magical island — sea access only)
    ISLE_OF_GLASS_ARCANE_TOWER_DIALOGUE,

    # Mirefall  (NEW — deep swamp town)
    MIREFALL_RECEPTIONIST_DIALOGUE,
    MIREFALL_SHOPKEEPER_DIALOGUE,
    MIREFALL_INNKEEPER_DIALOGUE,
    MIREFALL_HERBALIST_DIALOGUE,
    MIREFALL_BLACK_MARKET_DIALOGUE,

    # Saltmarsh  (NEW — small coastal fishing village, has port)
    SALTMARSH_RECEPTIONIST_DIALOGUE,
    SALTMARSH_SHOPKEEPER_DIALOGUE,
    SALTMARSH_INNKEEPER_DIALOGUE,
    SALTMARSH_PORTMASTER_DIALOGUE,

    # Cinderpeak  (NEW — volcanic mountain outpost)
    CINDERPEAK_RECEPTIONIST_DIALOGUE,
    CINDERPEAK_SHOPKEEPER_DIALOGUE,
    CINDERPEAK_INNKEEPER_DIALOGUE,
    CINDERPEAK_BLACKSMITH_DIALOGUE,
    CINDERPEAK_ARCANE_TOWER_DIALOGUE,

    # Veilholt  (NEW — ancient forest city)
    VEILHOLT_RECEPTIONIST_DIALOGUE,
    VEILHOLT_SHOPKEEPER_DIALOGUE,
    VEILHOLT_INNKEEPER_DIALOGUE,
    VEILHOLT_HERBALIST_DIALOGUE,
    VEILHOLT_ARCANE_TOWER_DIALOGUE,
    VEILHOLT_GUILD_DIALOGUE,
)

# ─────────────────────────────────────────────────────────────────────────────
#  WORLD MAP — connections summary
#  Port cities (sea routes): Brinewatch, Saltmarsh, Tidebreak, Coralhaven,
#                            Blackwake (pirate), Isle of Glass (destination).
#  Sea routes are only used where there is NO land path between nodes.
#  Coralhaven, Blackwake, and Isle of Glass are island/cove destinations:
#  sea is the only way in or out.
#
#  NORTH REGION:   Stormhold — Thornwall — (Solmere)
#  EAST REGION:    Irondeep — Skylume — Cinderpeak — Veilholt
#  CENTRAL:        Solmere (hub) — Greyharbor — Elderfen
#  SOUTH REGION:   Sunreach — Brinewatch — Mirefall — Ashkara — Dunemar — Saltmarsh
#  FAR REACHES:    Tidebreak — Coralhaven — Blackwake — Isle of Glass
# ─────────────────────────────────────────────────────────────────────────────

CITIES = {

    # ── NORTH REGION ──────────────────────────────────────────────────────────

    "stormhold": {
        "name": "Stormhold",
        "biome": "tundra",
        "description": "A bleak northern fortress carved into a glacier ridge. No harbour, no port — the sea here is frozen six months of the year.",
        "services": ["shop", "inn", "barracks", "gift_shop"],
        "dialogues": {
            "receptionist": STORMHOLD_RECEPTIONIST_DIALOGUE,
            "shop": STORMHOLD_SHOPKEEPER_DIALOGUE,
            "inn": STORMHOLD_INNKEEPER_DIALOGUE,
            "barracks": STORMHOLD_BARRACKS_DIALOGUE,
            "gift_shop": SKYLUME_GIFT_SHOP_DIALOGUE,
        },
        "travel": {
            "connections": [
                {"dest": "thornwall", "type": "land", "travel_time": 90},
                # Long southern road through the Ashfen marshes
                {"dest": "mirefall",  "type": "land", "travel_time": 220},
            ],
        },
        "shop": {"stock_size": 6, "base_price_consumable": 18, "base_price_other": 55, "rarity_bias": "higher"},
        "inn": {"rest_cost": 5, "sleep_after_hour": 20},
    },

    "thornwall": {
        "name": "Thornwall",
        "biome": "temperate",
        "description": "A walled garrison town on the northern road. Soldiers outnumber merchants three to one.",
        "services": ["shop", "inn", "barracks"],
        "dialogues": {
            "receptionist": THORNWALL_RECEPTIONIST_DIALOGUE,
            "shop": THORNWALL_SHOPKEEPER_DIALOGUE,
            "inn": THORNWALL_INNKEEPER_DIALOGUE,
            "barracks": THORNWALL_BARRACKS_DIALOGUE,
        },
        "travel": {
            "connections": [
                {"dest": "stormhold", "type": "land", "travel_time": 90},
                {"dest": "solmere",   "type": "land", "travel_time": 100},
                {"dest": "greyharbor","type": "land", "travel_time": 130},
            ],
        },
        "shop": {"stock_size": 6, "base_price_consumable": 13, "base_price_other": 38, "rarity_bias": "normal"},
        "inn": {"rest_cost": 4, "sleep_after_hour": 19},
    },

    # ── CENTRAL REGION ────────────────────────────────────────────────────────

    "solmere": {
        "name": "Solmere",
        "biome": "temperate",
        "description": "The crossroads of the known world. Merchants, sellswords, and pilgrims alike pass through its broad stone gates.",
        "services": ["shop", "inn", "blacksmith", "trade_hall", "temple", "guild"],
        "dialogues": {
            "receptionist": SOLMERE_RECEPTIONIST_DIALOGUE,
            "shop": SOLMERE_SHOPKEEPER_DIALOGUE,
            "inn": SOLMERE_INNKEEPER_DIALOGUE,
            "blacksmith": SOLMERE_BLACKSMITH_DIALOGUE,
            "trade_hall": SOLMERE_TRADE_HALL_DIALOGUE,
            "temple": SOLMERE_TEMPLE_DIALOGUE,
        },
        "travel": {
            "connections": [
                {"dest": "thornwall", "type": "land", "travel_time": 100},
                {"dest": "greyharbor","type": "land", "travel_time": 110},
                {"dest": "elderfen",  "type": "land", "travel_time": 150},
                {"dest": "irondeep",  "type": "land", "travel_time": 130},
                {"dest": "skylume",   "type": "land", "travel_time": 180},
                {"dest": "sunreach",  "type": "land", "travel_time": 140},
            ],
        },
        "shop": {"stock_size": 8, "base_price_consumable": 15, "base_price_other": 45, "rarity_bias": "normal"},
        "inn": {"rest_cost": 0, "sleep_after_hour": 18},
    },

    "greyharbor": {
        "name": "Greyharbor",
        "biome": "temperate",
        "description": "A prosperous river town where three tributaries meet. The 'harbour' is a network of canal docks — there is no sea access.",
        "services": ["shop", "inn", "trade_hall", "guild"],
        "dialogues": {
            "receptionist": GREYHARBOR_RECEPTIONIST_DIALOGUE,
            "shop": GREYHARBOR_SHOPKEEPER_DIALOGUE,
            "inn": GREYHARBOR_INNKEEPER_DIALOGUE,
            "trade_hall": GREYHARBOR_TRADE_HALL_DIALOGUE,
        },
        "travel": {
            "connections": [
                {"dest": "solmere",   "type": "land", "travel_time": 110},
                {"dest": "thornwall", "type": "land", "travel_time": 130},
                {"dest": "elderfen",  "type": "land", "travel_time": 120},
            ],
        },
        "shop": {"stock_size": 7, "base_price_consumable": 14, "base_price_other": 42, "rarity_bias": "normal"},
        "inn": {"rest_cost": 5, "sleep_after_hour": 18},
    },

    "elderfen": {
        "name": "Elderfen",
        "biome": "swamp",
        "description": "Half the buildings stand on stilts above brackish water. Herbalists and hedge-witches thrive here.",
        "services": ["shop", "inn", "herbalist"],
        "dialogues": {
            "receptionist": ELDERFEN_RECEPTIONIST_DIALOGUE,
            "shop": ELDERFEN_SHOPKEEPER_DIALOGUE,
            "inn": ELDERFEN_INNKEEPER_DIALOGUE,
            "herbalist": ELDERFEN_HERBALIST_DIALOGUE,
        },
        "travel": {
            "connections": [
                {"dest": "solmere",   "type": "land", "travel_time": 150},
                {"dest": "greyharbor","type": "land", "travel_time": 120},
                {"dest": "mirefall",  "type": "land", "travel_time": 110},
            ],
        },
        "shop": {"stock_size": 6, "base_price_consumable": 12, "base_price_other": 40, "rarity_bias": "normal"},
        "inn": {"rest_cost": 6, "sleep_after_hour": 17},
    },

    # ── EAST REGION ───────────────────────────────────────────────────────────

    "irondeep": {
        "name": "Irondeep",
        "biome": "mountain",
        "description": "A dwarven-founded mining city deep in the Iron Crags. The forges never go cold.",
        "services": ["shop", "inn", "blacksmith", "barracks", "guild"],
        "dialogues": {
            "receptionist": IRONDEEP_RECEPTIONIST_DIALOGUE,
            "shop": IRONDEEP_SHOPKEEPER_DIALOGUE,
            "inn": IRONDEEP_INNKEEPER_DIALOGUE,
            "blacksmith": IRONDEEP_BLACKSMITH_DIALOGUE,
            "barracks": IRONDEEP_BARRACKS_DIALOGUE,
        },
        "travel": {
            "connections": [
                {"dest": "solmere",   "type": "land", "travel_time": 130},
                {"dest": "skylume",   "type": "land", "travel_time": 90},
                {"dest": "cinderpeak","type": "land", "travel_time": 110},
            ],
        },
        "shop": {"stock_size": 8, "base_price_consumable": 16, "base_price_other": 50, "rarity_bias": "higher"},
        "inn": {"rest_cost": 7, "sleep_after_hour": 19},
    },

    "skylume": {
        "name": "Skylume",
        "biome": "magical",
        "description": "Towers of crystallised leyline energy pierce the clouds above this arcane city. Magic items trade for a premium.",
        "services": ["shop", "inn", "arcane_tower", "gift_shop"],
        "dialogues": {
            "receptionist": SKYLUME_RECEPTIONIST_DIALOGUE,
            "shop": SKYLUME_SHOPKEEPER_DIALOGUE,
            "inn": SKYLUME_INNKEEPER_DIALOGUE,
            "arcane_tower": SKYLUME_ARCANE_TOWER_DIALOGUE,
            "gift_shop": SKYLUME_GIFT_SHOP_DIALOGUE,
        },
        "travel": {
            "connections": [
                {"dest": "solmere",   "type": "land", "travel_time": 180},
                {"dest": "irondeep",  "type": "land", "travel_time": 90},
                {"dest": "veilholt",  "type": "land", "travel_time": 100},
            ],
        },
        "shop": {"stock_size": 9, "base_price_consumable": 20, "base_price_other": 65, "rarity_bias": "higher"},
        "inn": {"rest_cost": 12, "sleep_after_hour": 20},
    },

    "cinderpeak": {
        "name": "Cinderpeak",
        "biome": "volcanic",
        "description": "Built in the caldera of a dormant volcano. The air tastes of sulphur and opportunity — rare ores flow down from the crater rim.",
        "services": ["shop", "inn", "blacksmith", "arcane_tower"],
        "dialogues": {
            "receptionist": CINDERPEAK_RECEPTIONIST_DIALOGUE,
            "shop": CINDERPEAK_SHOPKEEPER_DIALOGUE,
            "inn": CINDERPEAK_INNKEEPER_DIALOGUE,
            "blacksmith": CINDERPEAK_BLACKSMITH_DIALOGUE,
            "arcane_tower": CINDERPEAK_ARCANE_TOWER_DIALOGUE,
        },
        "travel": {
            "connections": [
                {"dest": "irondeep",  "type": "land", "travel_time": 110},
                {"dest": "veilholt",  "type": "land", "travel_time": 80},
            ],
        },
        "shop": {"stock_size": 7, "base_price_consumable": 18, "base_price_other": 60, "rarity_bias": "higher"},
        "inn": {"rest_cost": 10, "sleep_after_hour": 21},
    },

    "veilholt": {
        "name": "Veilholt",
        "biome": "forest",
        "description": "An ancient city grown into and around the Forest of Veils. Elven architecture merges seamlessly with the canopy.",
        "services": ["shop", "inn", "herbalist", "arcane_tower", "guild"],
        "dialogues": {
            "receptionist": VEILHOLT_RECEPTIONIST_DIALOGUE,
            "shop": VEILHOLT_SHOPKEEPER_DIALOGUE,
            "inn": VEILHOLT_INNKEEPER_DIALOGUE,
            "herbalist": VEILHOLT_HERBALIST_DIALOGUE,
            "arcane_tower": VEILHOLT_ARCANE_TOWER_DIALOGUE,
            "guild": VEILHOLT_GUILD_DIALOGUE,
        },
        "travel": {
            "connections": [
                {"dest": "skylume",   "type": "land", "travel_time": 100},
                {"dest": "cinderpeak","type": "land", "travel_time": 80},
            ],
        },
        "shop": {"stock_size": 8, "base_price_consumable": 14, "base_price_other": 48, "rarity_bias": "normal"},
        "inn": {"rest_cost": 8, "sleep_after_hour": 18},
    },

    # ── SOUTH REGION ──────────────────────────────────────────────────────────

    "sunreach": {
        "name": "Sunreach",
        "biome": "savanna",
        "description": "A sun-baked trading city on the southern plains. The great temple here is said to channel the Radiant God's own light.",
        "services": ["shop", "inn", "temple", "trade_hall"],
        "dialogues": {
            "receptionist": SUNREACH_RECEPTIONIST_DIALOGUE,
            "shop": SUNREACH_SHOPKEEPER_DIALOGUE,
            "inn": SUNREACH_INNKEEPER_DIALOGUE,
            "temple": SUNREACH_TEMPLE_DIALOGUE,
        },
        "travel": {
            "connections": [
                {"dest": "solmere",   "type": "land", "travel_time": 140},
                {"dest": "brinewatch","type": "land", "travel_time": 120},
                {"dest": "ashkara",   "type": "land", "travel_time": 160},
            ],
        },
        "shop": {"stock_size": 8, "base_price_consumable": 16, "base_price_other": 48, "rarity_bias": "normal"},
        "inn": {"rest_cost": 7, "sleep_after_hour": 18},
    },

    "brinewatch": {
        "name": "Brinewatch",
        "biome": "coastal",
        "description": "The western seaport. A working harbour city of fishermen, merchants, and naval conscripts. Gateway to the Far Reaches.",
        "services": ["shop", "inn", "blacksmith", "port", "shipyard", "trade_hall"],
        "dialogues": {
            "receptionist": BRINEWATCH_RECEPTIONIST_DIALOGUE,
            "shop": BRINEWATCH_SHOPKEEPER_DIALOGUE,
            "inn": BRINEWATCH_INNKEEPER_DIALOGUE,
            "blacksmith": BRINEWATCH_BLACKSMITH_DIALOGUE,
            "port": BRINEWATCH_PORTMASTER_DIALOGUE,
            "shipyard": BRINEWATCH_SHIPYARD_DIALOGUE,
            "trade_hall": BRINEWATCH_TRADE_HALL_DIALOGUE,
        },
        "travel": {
            "connections": [
                {"dest": "sunreach",  "type": "land", "travel_time": 120},
                {"dest": "mirefall",  "type": "land", "travel_time": 100},
                # Sea routes — the two islands are not reachable by land
                {"dest": "tidebreak", "type": "sea",  "travel_time": 110},
                {"dest": "blackwake", "type": "sea",  "travel_time": 90},
            ],
        },
        "shop": {"stock_size": 10, "base_price_consumable": 18, "base_price_other": 55, "rarity_bias": "normal"},
        "inn": {"rest_cost": 8, "sleep_after_hour": 19},
    },

    "mirefall": {
        "name": "Mirefall",
        "biome": "swamp",
        "description": "A sunken settlement at the edge of the Ashen Mire. Its people are resilient — and deeply suspicious of outsiders.",
        "services": ["shop", "inn", "herbalist", "black_market"],
        "dialogues": {
            "receptionist": MIREFALL_RECEPTIONIST_DIALOGUE,
            "shop": MIREFALL_SHOPKEEPER_DIALOGUE,
            "inn": MIREFALL_INNKEEPER_DIALOGUE,
            "herbalist": MIREFALL_HERBALIST_DIALOGUE,
            "black_market": MIREFALL_BLACK_MARKET_DIALOGUE,
        },
        "travel": {
            "connections": [
                {"dest": "elderfen",  "type": "land", "travel_time": 110},
                {"dest": "brinewatch","type": "land", "travel_time": 100},
                {"dest": "stormhold", "type": "land", "travel_time": 220},
            ],
        },
        "shop": {"stock_size": 5, "base_price_consumable": 11, "base_price_other": 35, "rarity_bias": "normal"},
        "inn": {"rest_cost": 4, "sleep_after_hour": 17},
    },

    "ashkara": {
        "name": "Ashkara",
        "biome": "desert",
        "description": "A desert city built over a buried oasis. The black market here rivals the trade hall for volume — and far exceeds it for danger.",
        "services": ["shop", "inn", "black_market", "blacksmith", "guild"],
        "dialogues": {
            "receptionist": ASHKARA_RECEPTIONIST_DIALOGUE,
            "shop": ASHKARA_SHOPKEEPER_DIALOGUE,
            "inn": ASHKARA_INNKEEPER_DIALOGUE,
            "black_market": ASHKARA_BLACK_MARKET_DIALOGUE,
            "blacksmith": ASHKARA_BLACKSMITH_DIALOGUE,
        },
        "travel": {
            "connections": [
                {"dest": "sunreach",  "type": "land", "travel_time": 160},
                {"dest": "dunemar",   "type": "land", "travel_time": 140},
            ],
        },
        "shop": {"stock_size": 7, "base_price_consumable": 22, "base_price_other": 65, "rarity_bias": "higher"},
        "inn": {"rest_cost": 15, "sleep_after_hour": 21},
    },

    "dunemar": {
        "name": "Dunemar",
        "biome": "desert",
        "description": "A fortified desert trade post at the end of the Amber Road. Caravans converge here from three directions.",
        "services": ["shop", "inn", "trade_hall", "black_market"],
        "dialogues": {
            "receptionist": DUNEMAR_RECEPTIONIST_DIALOGUE,
            "shop": DUNEMAR_SHOPKEEPER_DIALOGUE,
            "inn": DUNEMAR_INNKEEPER_DIALOGUE,
            "trade_hall": DUNEMAR_TRADE_HALL_DIALOGUE,
            "black_market": DUNEMAR_BLACK_MARKET_DIALOGUE,
        },
        "travel": {
            "connections": [
                {"dest": "ashkara",   "type": "land", "travel_time": 140},
                # Coralhaven is island-only — only reachable by sea from here
                {"dest": "coralhaven","type": "sea",  "travel_time": 150},
            ],
        },
        "shop": {"stock_size": 9, "base_price_consumable": 17, "base_price_other": 52, "rarity_bias": "normal"},
        "inn": {"rest_cost": 9, "sleep_after_hour": 18},
    },

    "saltmarsh": {
        "name": "Saltmarsh",
        "biome": "coastal",
        "description": "A small fishing village turned minor port. The smell of brine and smoked fish is inescapable. Tidebreak lies a day's sail south.",
        "services": ["shop", "inn", "port"],
        "dialogues": {
            "receptionist": SALTMARSH_RECEPTIONIST_DIALOGUE,
            "shop": SALTMARSH_SHOPKEEPER_DIALOGUE,
            "inn": SALTMARSH_INNKEEPER_DIALOGUE,
            "port": SALTMARSH_PORTMASTER_DIALOGUE,
        },
        "travel": {
            "connections": [
                {"dest": "brinewatch","type": "land", "travel_time": 90},
                # Sea routes — Blackwake and Tidebreak cannot be reached overland
                {"dest": "blackwake", "type": "sea",  "travel_time": 70},
                {"dest": "tidebreak", "type": "sea",  "travel_time": 100},
            ],
        },
        "shop": {"stock_size": 5, "base_price_consumable": 12, "base_price_other": 36, "rarity_bias": "normal"},
        "inn": {"rest_cost": 4, "sleep_after_hour": 18},
    },

    # ── FAR REACHES / ISLANDS ─────────────────────────────────────────────────

    "tidebreak": {
        "name": "Tidebreak",
        "biome": "coastal",
        "description": "The great southern port. A sprawling city of three harbours and twice as many taverns. Centre of seaborne trade in the Far Reaches.",
        "services": ["shop", "inn", "port", "shipyard", "trade_hall"],
        "dialogues": {
            "receptionist": TIDEBREAK_RECEPTIONIST_DIALOGUE,
            "shop": TIDEBREAK_SHOPKEEPER_DIALOGUE,
            "inn": TIDEBREAK_INNKEEPER_DIALOGUE,
            "port": TIDEBREAK_PORTMASTER_DIALOGUE,
            "shipyard": TIDEBREAK_SHIPYARD_DIALOGUE,
            "trade_hall": TIDEBREAK_TRADE_HALL_DIALOGUE,
        },
        "travel": {
            "connections": [
                # All routes are sea — Tidebreak is on an island landmass
                {"dest": "brinewatch", "type": "sea", "travel_time": 110},
                {"dest": "saltmarsh",  "type": "sea", "travel_time": 100},
                {"dest": "coralhaven", "type": "sea", "travel_time": 80},
                {"dest": "blackwake",  "type": "sea", "travel_time": 60},
                {"dest": "isle_of_glass", "type": "sea", "travel_time": 130},
            ],
        },
        "shop": {"stock_size": 10, "base_price_consumable": 19, "base_price_other": 58, "rarity_bias": "normal"},
        "inn": {"rest_cost": 10, "sleep_after_hour": 19},
    },

    "coralhaven": {
        "name": "Coralhaven",
        "biome": "tropical",
        "description": "A jewel of the southern seas built across a reef archipelago. Reachable only by water. Blessed by three temples and surrounded by beauty.",
        "services": ["shop", "inn", "port", "herbalist", "temple", "guild", "gift_shop"],
        "dialogues": {
            "receptionist": CORALHAVEN_RECEPTIONIST_DIALOGUE,
            "shop": CORALHAVEN_SHOPKEEPER_DIALOGUE,
            "inn": CORALHAVEN_INNKEEPER_DIALOGUE,
            "port": CORALHAVEN_PORTMASTER_DIALOGUE,
            "herbalist": CORALHAVEN_HERBALIST_DIALOGUE,
            "temple": CORALHAVEN_TEMPLE_DIALOGUE,
            "gift_shop": CORALHAVEN_GIFT_SHOP_DIALOGUE,
        },
        "travel": {
            "connections": [
                # Sea-only — island city
                {"dest": "tidebreak", "type": "sea", "travel_time": 80},
                {"dest": "dunemar",   "type": "sea", "travel_time": 150},
                {"dest": "isle_of_glass", "type": "sea", "travel_time": 100},
            ],
        },
        "shop": {"stock_size": 8, "base_price_consumable": 16, "base_price_other": 50, "rarity_bias": "normal"},
        "inn": {"rest_cost": 8, "sleep_after_hour": 18},
    },

    "blackwake": {
        "name": "Blackwake",
        "biome": "coastal",
        "description": "A lawless sea-cove known only to sailors and criminals. No roads lead here — just unmarked sea lanes and whispered directions.",
        "services": ["inn", "port", "black_market"],
        "dialogues": {
            "receptionist": BLACKWAKE_RECEPTIONIST_DIALOGUE,
            "inn": BLACKWAKE_INNKEEPER_DIALOGUE,
            "port": BLACKWAKE_PORTMASTER_DIALOGUE,
            "black_market": BLACKWAKE_BLACK_MARKET_DIALOGUE,
        },
        "travel": {
            "connections": [
                # Sea-only — hidden coastal cove, no land routes
                {"dest": "brinewatch","type": "sea", "travel_time": 90},
                {"dest": "saltmarsh", "type": "sea", "travel_time": 70},
                {"dest": "tidebreak", "type": "sea", "travel_time": 60},
            ],
        },
        "inn": {"rest_cost": 6, "sleep_after_hour": 20},
    },

    "isle_of_glass": {
        "name": "Isle of Glass",
        "biome": "magical",
        "description": "A crystalline island that does not appear on any mundane map. Mages and scholars make pilgrimage here; most never leave.",
        "services": ["arcane_tower"],
        "dialogues": {
            "arcane_tower": ISLE_OF_GLASS_ARCANE_TOWER_DIALOGUE,
        },
        "travel": {
            "connections": [
                # Sea-only — magical island, no land access
                {"dest": "tidebreak", "type": "sea", "travel_time": 130},
                {"dest": "coralhaven","type": "sea", "travel_time": 100},
            ],
        },
    },
}