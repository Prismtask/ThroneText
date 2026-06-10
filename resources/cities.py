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

    # Greyharbor
    GREYHARBOR_RECEPTIONIST_DIALOGUE,
    GREYHARBOR_SHOPKEEPER_DIALOGUE,
    GREYHARBOR_INNKEEPER_DIALOGUE,
    GREYHARBOR_PORTMASTER_DIALOGUE,
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

    # Ashkara
    ASHKARA_RECEPTIONIST_DIALOGUE,
    ASHKARA_SHOPKEEPER_DIALOGUE,
    ASHKARA_INNKEEPER_DIALOGUE,
    ASHKARA_BLACK_MARKET_DIALOGUE,
    ASHKARA_BLACKSMITH_DIALOGUE,

    # Sunreach
    SUNREACH_RECEPTIONIST_DIALOGUE,
    SUNREACH_SHOPKEEPER_DIALOGUE,
    SUNREACH_INNKEEPER_DIALOGUE,
    SUNREACH_PORTMASTER_DIALOGUE,
    SUNREACH_TEMPLE_DIALOGUE,

    # Thornwall
    THORNWALL_RECEPTIONIST_DIALOGUE,
    THORNWALL_SHOPKEEPER_DIALOGUE,
    THORNWALL_INNKEEPER_DIALOGUE,
    THORNWALL_BARRACKS_DIALOGUE,

    # Dunemar
    DUNEMAR_RECEPTIONIST_DIALOGUE,
    DUNEMAR_SHOPKEEPER_DIALOGUE,
    DUNEMAR_INNKEEPER_DIALOGUE,
    DUNEMAR_PORTMASTER_DIALOGUE,
    DUNEMAR_TRADE_HALL_DIALOGUE,
    DUNEMAR_BLACK_MARKET_DIALOGUE,

    # Tidebreak
    TIDEBREAK_RECEPTIONIST_DIALOGUE,
    TIDEBREAK_SHOPKEEPER_DIALOGUE,
    TIDEBREAK_INNKEEPER_DIALOGUE,
    TIDEBREAK_PORTMASTER_DIALOGUE,
    TIDEBREAK_SHIPYARD_DIALOGUE,
    TIDEBREAK_TRADE_HALL_DIALOGUE,

    # Stormhold
    STORMHOLD_RECEPTIONIST_DIALOGUE,
    STORMHOLD_SHOPKEEPER_DIALOGUE,
    STORMHOLD_PORTMASTER_DIALOGUE,
    STORMHOLD_SHIPYARD_DIALOGUE,
    STORMHOLD_BARRACKS_DIALOGUE,

    # Coralhaven
    CORALHAVEN_RECEPTIONIST_DIALOGUE,
    CORALHAVEN_SHOPKEEPER_DIALOGUE,
    CORALHAVEN_INNKEEPER_DIALOGUE,
    CORALHAVEN_PORTMASTER_DIALOGUE,
    CORALHAVEN_HERBALIST_DIALOGUE,
    CORALHAVEN_TEMPLE_DIALOGUE,

    # Blackwake
    BLACKWAKE_RECEPTIONIST_DIALOGUE,
    BLACKWAKE_INNKEEPER_DIALOGUE,
    BLACKWAKE_PORTMASTER_DIALOGUE,
    BLACKWAKE_BLACK_MARKET_DIALOGUE,

    # Isle of Glass
    ISLE_OF_GLASS_ARCANE_TOWER_DIALOGUE,
)

CITIES = {
    "solmere": {
        "name": "Solmere",
        "biome": "temperate",
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
                {"dest": "brinewatch", "type": "land", "travel_time": 120},
                {"dest": "greyharbor", "type": "land", "travel_time": 110},
                {"dest": "elderfen", "type": "land", "travel_time": 150},
                {"dest": "irondeep", "type": "land", "travel_time": 130},
                {"dest": "skylume", "type": "land", "travel_time": 180},
                {"dest": "sunreach", "type": "land", "travel_time": 140},
                {"dest": "thornwall", "type": "land", "travel_time": 100},
            ],
        },
        "shop": {"stock_size": 8, "base_price_consumable": 15, "base_price_other": 45, "rarity_bias": "normal"},
        "inn": {"rest_cost": 0, "sleep_after_hour": 18}
    },
    "brinewatch": {
        "name": "Brinewatch",
        "biome": "coastal",
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
                {"dest": "solmere", "type": "land", "travel_time": 120},
                {"dest": "ashkara", "type": "land", "travel_time": 200},
                {"dest": "tidebreak", "type": "sea", "travel_time": 90},
                {"dest": "blackwake", "type": "sea", "travel_time": 80},
            ],
        },
        "shop": {"stock_size": 10, "base_price_consumable": 18, "base_price_other": 55, "rarity_bias": "normal"},
        "inn": {"rest_cost": 8, "sleep_after_hour": 19}
    },
    "greyharbor": {
        "name": "Greyharbor",
        "biome": "coastal",
        "services": ["shop", "inn", "port", "trade_hall"],
        "dialogues": {
            "receptionist": GREYHARBOR_RECEPTIONIST_DIALOGUE,
            "shop": GREYHARBOR_SHOPKEEPER_DIALOGUE,
            "inn": GREYHARBOR_INNKEEPER_DIALOGUE,
            "port": GREYHARBOR_PORTMASTER_DIALOGUE,
            "trade_hall": GREYHARBOR_TRADE_HALL_DIALOGUE,
        },
        "travel": {
            "connections": [
                {"dest": "solmere", "type": "land", "travel_time": 110},
                {"dest": "stormhold", "type": "sea", "travel_time": 130},
            ],
        },
        "shop": {"stock_size": 7, "base_price_consumable": 14, "base_price_other": 42, "rarity_bias": "normal"},
        "inn": {"rest_cost": 5, "sleep_after_hour": 18}
    },
    "elderfen": {
        "name": "Elderfen",
        "biome": "swamp",
        "services": ["shop", "inn", "herbalist"],
        "dialogues": {
            "receptionist": ELDERFEN_RECEPTIONIST_DIALOGUE,
            "shop": ELDERFEN_SHOPKEEPER_DIALOGUE,
            "inn": ELDERFEN_INNKEEPER_DIALOGUE,
            "herbalist": ELDERFEN_HERBALIST_DIALOGUE,
        },
        "travel": {
            "connections": [
                {"dest": "solmere", "type": "land", "travel_time": 150},
            ],
        },
        "shop": {"stock_size": 6, "base_price_consumable": 12, "base_price_other": 40, "rarity_bias": "normal"},
        "inn": {"rest_cost": 6, "sleep_after_hour": 17}
    },
    "irondeep": {
        "name": "Irondeep",
        "biome": "mountain",
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
                {"dest": "solmere", "type": "land", "travel_time": 130},
            ],
        },
        "shop": {"stock_size": 8, "base_price_consumable": 16, "base_price_other": 50, "rarity_bias": "higher"},
        "inn": {"rest_cost": 7, "sleep_after_hour": 19}
    },
    "skylume": {
        "name": "Skylume",
        "biome": "magical",
        "services": ["shop", "inn", "arcane_tower"],
        "dialogues": {
            "receptionist": SKYLUME_RECEPTIONIST_DIALOGUE,
            "shop": SKYLUME_SHOPKEEPER_DIALOGUE,
            "inn": SKYLUME_INNKEEPER_DIALOGUE,
            "arcane_tower": SKYLUME_ARCANE_TOWER_DIALOGUE,
        },
        "travel": {
            "connections": [
                {"dest": "solmere", "type": "land", "travel_time": 180},
                {"dest": "isle_of_glass", "type": "land", "travel_time": 240},
            ],
        },
        "shop": {"stock_size": 9, "base_price_consumable": 20, "base_price_other": 60, "rarity_bias": "higher"},
        "inn": {"rest_cost": 12, "sleep_after_hour": 20}
    },
    "ashkara": {
        "name": "Ashkara",
        "biome": "desert",
        "services": ["shop", "inn", "black_market", "guild"],
        "dialogues": {
            "receptionist": ASHKARA_RECEPTIONIST_DIALOGUE,
            "shop": ASHKARA_SHOPKEEPER_DIALOGUE,
            "inn": ASHKARA_INNKEEPER_DIALOGUE,
            "black_market": ASHKARA_BLACK_MARKET_DIALOGUE,
        },
        "travel": {
            "connections": [
                {"dest": "brinewatch", "type": "land", "travel_time": 200},
            ],
        },
        "shop": {"stock_size": 7, "base_price_consumable": 22, "base_price_other": 65, "rarity_bias": "higher"},
        "inn": {"rest_cost": 15, "sleep_after_hour": 21}
    },
    "sunreach": {
        "name": "Sunreach",
        "biome": "coastal",
        "services": ["shop", "inn", "port", "temple"],
        "dialogues": {
            "receptionist": SUNREACH_RECEPTIONIST_DIALOGUE,
            "shop": SUNREACH_SHOPKEEPER_DIALOGUE,
            "inn": SUNREACH_INNKEEPER_DIALOGUE,
            "port": SUNREACH_PORTMASTER_DIALOGUE,
            "temple": SUNREACH_TEMPLE_DIALOGUE,
        },
        "travel": {
            "connections": [
                {"dest": "solmere", "type": "land", "travel_time": 140},
                {"dest": "dunemar", "type": "sea", "travel_time": 100},
                {"dest": "coralhaven", "type": "sea", "travel_time": 120},
            ],
        },
        "shop": {"stock_size": 8, "base_price_consumable": 16, "base_price_other": 48, "rarity_bias": "normal"},
        "inn": {"rest_cost": 7, "sleep_after_hour": 18}
    },
    "thornwall": {
        "name": "Thornwall",
        "biome": "temperate",
        "services": ["shop", "inn", "barracks"],
        "dialogues": {
            "receptionist": THORNWALL_RECEPTIONIST_DIALOGUE,
            "shop": THORNWALL_SHOPKEEPER_DIALOGUE,
            "inn": THORNWALL_INNKEEPER_DIALOGUE,
            "barracks": THORNWALL_BARRACKS_DIALOGUE,
        },
        "travel": {
            "connections": [
                {"dest": "solmere", "type": "land", "travel_time": 100},
            ],
        },
        "shop": {"stock_size": 6, "base_price_consumable": 13, "base_price_other": 38, "rarity_bias": "normal"},
        "inn": {"rest_cost": 4, "sleep_after_hour": 19}
    },
    "dunemar": {
        "name": "Dunemar",
        "biome": "desert",
        "services": ["shop", "inn", "port", "trade_hall", "black_market"],
        "dialogues": {
            "receptionist": DUNEMAR_RECEPTIONIST_DIALOGUE,
            "shop": DUNEMAR_SHOPKEEPER_DIALOGUE,
            "inn": DUNEMAR_INNKEEPER_DIALOGUE,
            "port": DUNEMAR_PORTMASTER_DIALOGUE,
            "trade_hall": DUNEMAR_TRADE_HALL_DIALOGUE,
            "black_market": DUNEMAR_BLACK_MARKET_DIALOGUE,
        },
        "travel": {
            "connections": [
                {"dest": "sunreach", "type": "sea", "travel_time": 100},
                {"dest": "tidebreak", "type": "sea", "travel_time": 110},
            ],
        },
        "shop": {"stock_size": 9, "base_price_consumable": 17, "base_price_other": 52, "rarity_bias": "normal"},
        "inn": {"rest_cost": 9, "sleep_after_hour": 18}
    },
    "tidebreak": {
        "name": "Tidebreak",
        "biome": "coastal",
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
                {"dest": "brinewatch", "type": "sea", "travel_time": 90},
                {"dest": "dunemar", "type": "sea", "travel_time": 110},
                {"dest": "coralhaven", "type": "sea", "travel_time": 70},
                {"dest": "stormhold", "type": "sea", "travel_time": 80},
            ],
        },
        "shop": {"stock_size": 10, "base_price_consumable": 19, "base_price_other": 58, "rarity_bias": "normal"},
        "inn": {"rest_cost": 10, "sleep_after_hour": 19}
    },
    "stormhold": {
        "name": "Stormhold",
        "biome": "coastal",
        "services": ["shop", "port", "shipyard", "barracks"],
        "dialogues": {
            "receptionist": STORMHOLD_RECEPTIONIST_DIALOGUE,
            "shop": STORMHOLD_SHOPKEEPER_DIALOGUE,
            "port": STORMHOLD_PORTMASTER_DIALOGUE,
            "shipyard": STORMHOLD_SHIPYARD_DIALOGUE,
            "barracks": STORMHOLD_BARRACKS_DIALOGUE,
        },
        "travel": {
            "connections": [
                {"dest": "greyharbor", "type": "sea", "travel_time": 130},
                {"dest": "tidebreak", "type": "sea", "travel_time": 80},
            ],
        },
        "shop": {"stock_size": 7, "base_price_consumable": 15, "base_price_other": 45, "rarity_bias": "normal"}
    },
    "coralhaven": {
        "name": "Coralhaven",
        "biome": "coastal",
        "services": ["shop", "inn", "port", "herbalist", "temple", "guild"],
        "dialogues": {
            "receptionist": CORALHAVEN_RECEPTIONIST_DIALOGUE,
            "shop": CORALHAVEN_SHOPKEEPER_DIALOGUE,
            "inn": CORALHAVEN_INNKEEPER_DIALOGUE,
            "port": CORALHAVEN_PORTMASTER_DIALOGUE,
            "herbalist": CORALHAVEN_HERBALIST_DIALOGUE,
            "temple": CORALHAVEN_TEMPLE_DIALOGUE,
        },
        "travel": {
            "connections": [
                {"dest": "sunreach", "type": "sea", "travel_time": 120},
                {"dest": "tidebreak", "type": "sea", "travel_time": 70},
            ],
        },
        "shop": {"stock_size": 8, "base_price_consumable": 16, "base_price_other": 50, "rarity_bias": "normal"},
        "inn": {"rest_cost": 8, "sleep_after_hour": 18}
    },
    "blackwake": {
        "name": "Blackwake",
        "biome": "coastal",
        "services": ["inn", "port", "black_market"],
        "dialogues": {
            "receptionist": BLACKWAKE_RECEPTIONIST_DIALOGUE,
            "inn": BLACKWAKE_INNKEEPER_DIALOGUE,
            "port": BLACKWAKE_PORTMASTER_DIALOGUE,
            "black_market": BLACKWAKE_BLACK_MARKET_DIALOGUE,
        },
        "travel": {
            "connections": [
                {"dest": "brinewatch", "type": "sea", "travel_time": 80},
            ],
        },
        "inn": {"rest_cost": 6, "sleep_after_hour": 20}
    },
    "isle_of_glass": {
        "name": "Isle of Glass",
        "biome": "magical",
        "services": ["arcane_tower"],
        "dialogues": {
            "arcane_tower": ISLE_OF_GLASS_ARCANE_TOWER_DIALOGUE,
        },
        "travel": {
            "connections": [
                {"dest": "skylume", "type": "land", "travel_time": 240},
            ],
        },
    },
}