# resources/items.py
import random

ITEM_RARITY = {
    "common":    {"stat_mult": 1.0,  "price_mult": 1.0},
    "uncommon":  {"stat_mult": 1.3,  "price_mult": 1.5},
    "rare":      {"stat_mult": 1.7,  "price_mult": 3.0},
    "epic":      {"stat_mult": 2.4,  "price_mult": 6.0},
    "legendary": {"stat_mult": 3.5,  "price_mult": 12.0},
}

ITEMS = {
    # === Consumables ===
    "minor_healing_potion": {"name": "Minor Healing Potion", "type": "consumable", "base_power": 25},
    "healing_potion":       {"name": "Healing Potion",      "type": "consumable", "base_power": 55},
    "greater_healing_potion":{"name": "Greater Healing Potion","type": "consumable","base_power": 110},
    "superior_healing_potion":{"name": "Superior Healing Potion","type": "consumable","base_power": 180},

    "elixir_of_strength":   {"name": "Elixir of Strength", "type": "consumable", "temp_stat": "Strength", "base_power": 3, "duration": 4},
    "elixir_of_speed":      {"name": "Elixir of Speed",    "type": "consumable", "temp_stat": "Dexterity","base_power": 3, "duration": 4},
    "elixir_of_vitality":   {"name": "Elixir of Vitality", "type": "consumable", "temp_stat": "Constitution","base_power": 3, "duration": 4},
    "elixir_of_mind":       {"name": "Elixir of Mind",     "type": "consumable", "temp_stat": "Learning","base_power": 3, "duration": 4},

    # === Weapons === (Added "scaling_stat" property)
    "short_sword":  {"name": "Short Sword", "type": "equipment", "slot": "weapon", "base_mods": {"Strength": 2}, "scaling_stat": "Strength", "elemental_dmg": {"fire": 1.2}},
    "long_sword":   {"name": "Long Sword",  "type": "equipment", "slot": "weapon", "base_mods": {"Strength": 3}, "scaling_stat": "Strength", "elemental_dmg": {"fire": 1.2}},
    "battle_axe":   {"name": "Battle Axe",  "type": "equipment", "slot": "weapon", "base_mods": {"Strength": 4}, "scaling_stat": "Strength", "elemental_dmg": {"fire": 1.3, "earth": 1.1}},
    "greatsword":   {"name": "Greatsword",  "type": "equipment", "slot": "weapon", "base_mods": {"Strength": 5}, "scaling_stat": "Strength", "elemental_dmg": {"fire": 1.3, "earth": 1.2}},
    "dagger":       {"name": "Dagger",      "type": "equipment", "slot": "weapon", "base_mods": {"Dexterity": 3}, "scaling_stat": "Dexterity", "elemental_dmg": {"dark": 1.2}},
    "war_bow":      {"name": "War Bow",     "type": "equipment", "slot": "weapon", "base_mods": {"Dexterity": 4}, "scaling_stat": "Dexterity", "elemental_dmg": {"wind": 1.2}},
    "arcane_staff": {"name": "Arcane Staff","type": "equipment", "slot": "weapon", "base_mods": {"Learning": 4}, "scaling_stat": "Learning", "elemental_dmg": {"thunder": 1.2}},
    "mace":         {"name": "Mace",        "type": "equipment", "slot": "weapon", "base_mods": {"Strength": 2, "Wisdom": 1}, "scaling_stat": "Strength", "elemental_dmg": {"earth": 1.2}},

    # --- Strength Weapons ---
    "spear":        {"name": "Spear",         "type": "equipment", "slot": "weapon", "base_mods": {"Strength": 3, "Dexterity": 1},    "scaling_stat": "Strength", "elemental_dmg": {"wind": 1.2, "earth": 1.1}},
    "war_hammer":   {"name": "War Hammer",    "type": "equipment", "slot": "weapon", "base_mods": {"Strength": 5},                    "scaling_stat": "Strength", "elemental_dmg": {"earth": 1.3}},
    "flail":        {"name": "Flail",         "type": "equipment", "slot": "weapon", "base_mods": {"Strength": 3, "Constitution": 1}, "scaling_stat": "Strength", "elemental_dmg": {"fire": 1.3}},
    "silver_sword": {"name": "Silver Sword",  "type": "equipment", "slot": "weapon", "base_mods": {"Strength": 3, "Wisdom": 2},       "scaling_stat": "Strength", "elemental_dmg": {"light": 1.3}},
    "halberd":      {"name": "Halberd",       "type": "equipment", "slot": "weapon", "base_mods": {"Strength": 4, "Dexterity": 2},    "scaling_stat": "Strength", "elemental_dmg": {"wind": 1.2, "earth": 1.2}},

    # --- Dexterity Weapons ---
    "rapier":       {"name": "Rapier",        "type": "equipment", "slot": "weapon", "base_mods": {"Dexterity": 4, "Charisma": 1},   "scaling_stat": "Dexterity", "elemental_dmg": {"wind": 1.3}},
    "crossbow":     {"name": "Crossbow",      "type": "equipment", "slot": "weapon", "base_mods": {"Dexterity": 3, "Learning": 1},   "scaling_stat": "Dexterity", "elemental_dmg": {"thunder": 1.2}},
    "elven_bow":    {"name": "Elven Bow",     "type": "equipment", "slot": "weapon", "base_mods": {"Dexterity": 5, "Learning": 1},   "scaling_stat": "Dexterity", "elemental_dmg": {"wind": 1.3, "light": 1.1}},
    "chakram":      {"name": "Chakram",       "type": "equipment", "slot": "weapon", "base_mods": {"Dexterity": 3, "Strength": 1},   "scaling_stat": "Dexterity", "elemental_dmg": {"wind": 1.2}},
    "runic_dagger": {"name": "Runic Dagger",  "type": "equipment", "slot": "weapon", "base_mods": {"Dexterity": 2, "Learning": 2},   "scaling_stat": "Dexterity", "elemental_dmg": {"thunder": 1.2, "dark": 1.1}},
    "hand_crossbow":{"name": "Hand Crossbow", "type": "equipment", "slot": "weapon", "base_mods": {"Dexterity": 2},                  "scaling_stat": "Dexterity", "elemental_dmg": {"wind": 1.2}},

    # --- Learning Weapons ---
    "tome_blade":   {"name": "Tome Blade",    "type": "equipment", "slot": "weapon", "base_mods": {"Learning": 3, "Wisdom": 2},      "scaling_stat": "Learning", "elemental_dmg": {"dark": 1.3}},
    "wand":         {"name": "Wand",          "type": "equipment", "slot": "weapon", "base_mods": {"Learning": 2, "Wisdom": 1},      "scaling_stat": "Learning", "elemental_dmg": {"thunder": 1.2}},
    "grimoire":     {"name": "Grimoire",      "type": "equipment", "slot": "weapon", "base_mods": {"Learning": 5},                   "scaling_stat": "Learning", "elemental_dmg": {"dark": 1.3, "fire": 1.1}},
    "runic_orb":    {"name": "Runic Orb",     "type": "equipment", "slot": "weapon", "base_mods": {"Learning": 3, "Charisma": 1},    "scaling_stat": "Learning", "elemental_dmg": {"thunder": 1.3}},

    # --- Wisdom Weapons ---
    "holy_staff":   {"name": "Holy Staff",    "type": "equipment", "slot": "weapon", "base_mods": {"Wisdom": 4, "Constitution": 1},  "scaling_stat": "Wisdom", "elemental_dmg": {"light": 1.3}},
    "scepter":      {"name": "Scepter",       "type": "equipment", "slot": "weapon", "base_mods": {"Wisdom": 3, "Charisma": 2},      "scaling_stat": "Wisdom", "elemental_dmg": {"light": 1.3}},
    "sacred_mace":  {"name": "Sacred Mace",   "type": "equipment", "slot": "weapon", "base_mods": {"Wisdom": 4, "Strength": 1},      "scaling_stat": "Wisdom", "elemental_dmg": {"light": 1.2, "earth": 1.1}},

    # --- Charisma Weapons ---
    "bards_lute":   {"name": "Bard's Lute",   "type": "equipment", "slot": "weapon", "base_mods": {"Charisma": 4, "Learning": 1},    "scaling_stat": "Charisma", "elemental_dmg": {"light": 1.2, "wind": 1.1}},
    "silver_tongue_dagger": {"name": "Silver-Tongue Dagger", "type": "equipment", "slot": "weapon", "base_mods": {"Charisma": 3, "Dexterity": 2}, "scaling_stat": "Charisma", "elemental_dmg": {"dark": 1.2, "wind": 1.1}},

    "abyss_fang": {
        "name": "Abyss Fang",
        "type": "equipment",
        "slot": "weapon",
        "unique": True,
        "base_mods": {"Strength": 6, "Dexterity": 3},
        "special": "dream_devour",
        "drop_source": "dream_devouring_slitcurrent",
        "drop_rarity": "legendary",
        "scaling_stat": ["Strength", "Dexterity"],
        "elemental_dmg": {"dark": 1.5},
    },

    # === Armor ===
    "padded_armor": {"name": "Padded Armor","type": "equipment","slot": "armor","base_mods": {"Constitution": 2}, "elemental_res": {"earth": 1.1}},
    "leather_armor":{"name": "Leather Armor","type": "equipment","slot": "armor","base_mods": {"Dexterity": 2, "Constitution": 1}, "elemental_res": {"wind": 1.2, "thunder": 1.1}},
    "chainmail":    {"name": "Chainmail",   "type": "equipment","slot": "armor","base_mods": {"Constitution": 3}, "elemental_res": {"fire": 1.2, "earth": 1.1}},
    "plate_armor":  {"name": "Plate Armor", "type": "equipment","slot": "armor","base_mods": {"Constitution": 5, "Dexterity": -1}, "elemental_res": {"fire": 1.2, "earth": 1.2, "wind": 0.8}},
    "dragonhide":   {"name": "Dragonhide Armor", "type": "equipment","slot": "armor","base_mods": {"Constitution": 4, "Dexterity": 2}, "elemental_res": {"fire": 1.3, "earth": 1.2}},

    # --- Strength/Constitution Armor ---
    "scale_armor":      {"name": "Scale Armor",      "type": "equipment", "slot": "armor", "base_mods": {"Constitution": 3, "Strength": 1}, "elemental_res": {"fire": 1.2, "earth": 1.1}},
    "battle_harness":   {"name": "Battle Harness",   "type": "equipment", "slot": "armor", "base_mods": {"Strength": 2, "Constitution": 2}, "elemental_res": {"fire": 1.2, "earth": 1.1}},
    "banded_mail":      {"name": "Banded Mail",      "type": "equipment", "slot": "armor", "base_mods": {"Constitution": 4, "Dexterity": -1}, "elemental_res": {"fire": 1.2, "earth": 1.2, "wind": 0.8}},
    "fur_mantle":       {"name": "Fur Mantle",       "type": "equipment", "slot": "armor", "base_mods": {"Constitution": 2, "Wisdom": 1}, "elemental_res": {"wind": 1.2, "earth": 1.1, "water": 1.1}},

    # --- Dexterity Armor ---
    "elven_mail":       {"name": "Elven Mail",       "type": "equipment", "slot": "armor", "base_mods": {"Dexterity": 3, "Learning": 1}, "elemental_res": {"wind": 1.3, "light": 1.1}},
    "shadow_wraps":     {"name": "Shadow Wraps",     "type": "equipment", "slot": "armor", "base_mods": {"Dexterity": 4, "Charisma": 1}, "elemental_res": {"dark": 1.3, "wind": 1.2}},

    # --- Learning / Wisdom Armor ---
    "robes":            {"name": "Robes",             "type": "equipment", "slot": "armor", "base_mods": {"Learning": 3, "Wisdom": 1}, "elemental_res": {"light": 1.2, "dark": 1.2, "earth": 0.8}},
    "arcane_vestments": {"name": "Arcane Vestments",  "type": "equipment", "slot": "armor", "base_mods": {"Learning": 4, "Constitution": 1}, "elemental_res": {"light": 1.2, "dark": 1.2, "thunder": 1.1}},
    "blessed_vestments":{"name": "Blessed Vestments", "type": "equipment", "slot": "armor", "base_mods": {"Wisdom": 3, "Constitution": 2}, "elemental_res": {"light": 1.3, "fire": 1.2}},
    "runic_plate":      {"name": "Runic Plate",       "type": "equipment", "slot": "armor", "base_mods": {"Constitution": 4, "Learning": 2}, "elemental_res": {"thunder": 1.3, "earth": 1.2, "dark": 1.1}},

    # --- Charisma Armor ---
    "silk_garb":        {"name": "Silk Garb",         "type": "equipment", "slot": "armor", "base_mods": {"Charisma": 3, "Dexterity": 1}, "elemental_res": {"light": 1.2, "dark": 1.2}},
    "noble_regalia":    {"name": "Noble Regalia",     "type": "equipment", "slot": "armor", "base_mods": {"Charisma": 4, "Wisdom": 1}, "elemental_res": {"light": 1.3, "dark": 1.2}},

    # === Accessories === (small res bonuses or neutral)
    "ring_of_power":  {"name": "Ring of Power", "type": "equipment","slot": "accessory","base_mods": {"Strength": 2}, "elemental_res": {"fire": 1.1}},
    "ring_of_grace":  {"name": "Ring of Grace","type": "equipment","slot": "accessory","base_mods": {"Dexterity": 2}, "elemental_res": {"wind": 1.1}},
    "amulet_of_vigor":{"name": "Amulet of Vigor","type": "equipment","slot": "accessory","base_mods": {"Constitution": 3}, "elemental_res": {"earth": 1.1}},
    "tome_of_knowledge":{"name": "Tome of Knowledge","type": "equipment","slot": "accessory","base_mods": {"Learning": 3}, "elemental_res": {"thunder": 1.1}},
    "cloak_of_shadows":{"name": "Cloak of Shadows","type": "equipment","slot": "accessory","base_mods": {"Dexterity": 2, "Charisma": 1}, "elemental_res": {"dark": 1.2}},
    "talisman_of_warding":{"name": "Talisman of Warding","type": "equipment","slot": "accessory","base_mods": {"Constitution": 2, "Wisdom": 1}, "elemental_res": {"light": 1.1, "dark": 1.1}},

    # --- Strength Accessories ---
    "bracers_of_strength":{"name": "Bracers of Strength",  "type": "equipment", "slot": "accessory", "base_mods": {"Strength": 3}, "elemental_res": {"fire": 1.1}},
    "belt_of_giants":     {"name": "Belt of Giants",       "type": "equipment", "slot": "accessory", "base_mods": {"Strength": 3, "Constitution": 2}, "elemental_res": {"earth": 1.2}},
    "gauntlets_of_power": {"name": "Gauntlets of Power",   "type": "equipment", "slot": "accessory", "base_mods": {"Strength": 2, "Dexterity": 1}, "elemental_res": {"fire": 1.1}},
    "war_band":           {"name": "War Band",             "type": "equipment", "slot": "accessory", "base_mods": {"Strength": 2, "Wisdom": 1}, "elemental_res": {"fire": 1.1}},

    # --- Dexterity Accessories ---
    "boots_of_swiftness": {"name": "Boots of Swiftness",   "type": "equipment", "slot": "accessory", "base_mods": {"Dexterity": 3}, "elemental_res": {"wind": 1.2}},
    "nimble_gloves":      {"name": "Nimble Gloves",        "type": "equipment", "slot": "accessory", "base_mods": {"Dexterity": 2, "Charisma": 1}, "elemental_res": {"wind": 1.1}},
    "wind_anklet":        {"name": "Wind Anklet",          "type": "equipment", "slot": "accessory", "base_mods": {"Dexterity": 3, "Constitution": 1}, "elemental_res": {"wind": 1.2, "thunder": 1.1}},

    # --- Constitution Accessories ---
    "iron_heart_locket":  {"name": "Iron Heart Locket",    "type": "equipment", "slot": "accessory", "base_mods": {"Constitution": 3, "Strength": 1}, "elemental_res": {"earth": 1.2}},
    "endurance_ring":     {"name": "Endurance Ring",       "type": "equipment", "slot": "accessory", "base_mods": {"Constitution": 2, "Dexterity": 1}, "elemental_res": {"earth": 1.1, "water": 1.1}},

    # --- Learning Accessories ---
    "ring_of_learning":   {"name": "Ring of Learning",     "type": "equipment", "slot": "accessory", "base_mods": {"Learning": 3}, "elemental_res": {"thunder": 1.1}},
    "crown_of_intellect": {"name": "Crown of Intellect",   "type": "equipment", "slot": "accessory", "base_mods": {"Learning": 4, "Wisdom": 2}, "elemental_res": {"thunder": 1.2, "light": 1.1}},
    "earring_of_insight": {"name": "Earring of Insight",   "type": "equipment", "slot": "accessory", "base_mods": {"Learning": 2, "Charisma": 1}, "elemental_res": {"light": 1.1}},
    "scholars_monocle":   {"name": "Scholar's Monocle",    "type": "equipment", "slot": "accessory", "base_mods": {"Learning": 2, "Wisdom": 1}, "elemental_res": {"thunder": 1.1}},

    # --- Wisdom Accessories ---
    "ring_of_wisdom":     {"name": "Ring of Wisdom",       "type": "equipment", "slot": "accessory", "base_mods": {"Wisdom": 3}, "elemental_res": {"light": 1.1}},
    "pendant_of_wisdom":  {"name": "Pendant of Wisdom",    "type": "equipment", "slot": "accessory", "base_mods": {"Wisdom": 2, "Learning": 1}, "elemental_res": {"light": 1.2}},
    "oracle_eye":         {"name": "Oracle Eye",           "type": "equipment", "slot": "accessory", "base_mods": {"Wisdom": 3, "Constitution": 1}, "elemental_res": {"light": 1.2, "dark": 1.1}},

    # --- Charisma Accessories ---
    "ring_of_charisma":   {"name": "Ring of Charisma",     "type": "equipment", "slot": "accessory", "base_mods": {"Charisma": 3}, "elemental_res": {"dark": 1.1}},
    "signet_of_authority":{"name": "Signet of Authority",  "type": "equipment", "slot": "accessory", "base_mods": {"Charisma": 4}, "elemental_res": {"light": 1.2}},
    "silver_tongue_ring": {"name": "Silver Tongue Ring",   "type": "equipment", "slot": "accessory", "base_mods": {"Charisma": 2, "Wisdom": 1}, "elemental_res": {"dark": 1.1}},
    "brooch_of_valor":    {"name": "Brooch of Valor",      "type": "equipment", "slot": "accessory", "base_mods": {"Charisma": 2, "Strength": 2}, "elemental_res": {"light": 1.1, "fire": 1.1}},

    # === Utility / Combat Items ===
    "fire_bomb":   {"name": "Fire Bomb",  "type": "utility", "base_power": 35},
    "ice_bomb":    {"name": "Ice Bomb",   "type": "utility", "base_power": 28, "status": "slow"},
    "holy_water":  {"name": "Holy Water", "type": "utility", "base_power": 40, "bonus_vs": "Undead"},
    "smoke_bomb":  {"name": "Smoke Bomb", "type": "utility", "escape_bonus": 8},
    "thunder_bomb": {"name": "Thunder Bomb", "type": "utility", "base_power": 45},
    "acid_flask":   {"name": "Acid Flask", "type": "utility", "base_power": 32},
    "healing_salve":     {"name": "Healing Salve",     "type": "consumable", "base_power": 40, "heal_over_time": 3, "duration": 3},
    "battle_drink":      {"name": "Battle Drink",      "type": "consumable", "temp_stat": "Strength", "base_power": 5, "duration": 3},
    "iron_skin_potion":  {"name": "Iron Skin Potion",  "type": "consumable", "defense_buff": 4, "duration": 3},
    "poison_flask":      {"name": "Poison Flask",      "type": "utility",    "base_power": 18, "poison_damage": 8, "duration": 3},
    "stun_bomb":         {"name": "Stun Bomb",         "type": "utility",    "stun_chance": 0.6, "base_power": 12},
    "flash_powder":      {"name": "Flash Powder",      "type": "utility",    "escape_bonus": 12, "blind_enemy": True},
    "throwing_knife":    {"name": "Throwing Knife",    "type": "utility",    "base_power": 22, "armor_pierce": 2},
    "curse_cleansing_scroll": {"name": "Scroll of Cleansing", "type": "consumable", "cure_curse": True},
    "antidote": {"name": "Antidote", "type": "consumable", "base_power": 0, "cure_poison": True},
    "armor_shatter_flask": { "name": "Armour Shatter Flask", "type": "utility", "base_power": 0, "expose_armor": 2,},
    "recalled_scroll": {"name": "Scroll of Recall", "type": "utility", "fixed_flee": True},
    "capture_net": {
    "name": "Capture Net",
    "type": "utility",
    "base_power": 0,
    "capture_net": True,
    "rarity_mult_bonus": 25
    },

    # === Ascension Stones (sold at temples when dungeon floors are cleared) ===
    "ascension_stone_i":   {"name": "Ascension Stone I",   "type": "utility", "ascension_tier": 1, "rarity": "rare"},
    "ascension_stone_ii":  {"name": "Ascension Stone II",  "type": "utility", "ascension_tier": 2, "rarity": "rare"},
    "ascension_stone_iii": {"name": "Ascension Stone III", "type": "utility", "ascension_tier": 3, "rarity": "rare"},
    "ascension_stone_iv":  {"name": "Ascension Stone IV",  "type": "utility", "ascension_tier": 4, "rarity": "rare"},
    "ascension_stone_v":   {"name": "Ascension Stone V",   "type": "utility", "ascension_tier": 5, "rarity": "rare"},
    "ascension_stone_vi":  {"name": "Ascension Stone VI",  "type": "utility", "ascension_tier": 6, "rarity": "rare"},

    # === Scrolls ===
    "common_scroll":     {"name": "Scroll of Fusion", "type": "scroll", "target_rarity": "common"},
    "uncommon_scroll":   {"name": "Scroll of Fusion", "type": "scroll", "target_rarity": "uncommon"},
    "rare_scroll":       {"name": "Scroll of Fusion", "type": "scroll", "target_rarity": "rare"},
    "epic_scroll":       {"name": "Scroll of Fusion", "type": "scroll", "target_rarity": "epic"},
    "legendary_scroll":  {"name": "Scroll of Fusion", "type": "scroll", "target_rarity": "legendary"},

    # === Engagement Rings (Gift Shop Only) ===
    "ruby_engagement_ring": {
        "name": "Ruby Engagement Ring",
        "type": "equipment",
        "slot": "accessory",
        "unique": True,
        "base_mods": {"Strength": 3},
        "elemental_dmg": {"fire": 1.1},
    },
    "sapphire_engagement_ring": {
        "name": "Sapphire Engagement Ring",
        "type": "equipment",
        "slot": "accessory",
        "unique": True,
        "base_mods": {"Wisdom": 3},
        "elemental_dmg": {"water": 1.1},
    },
    "emerald_engagement_ring": {
        "name": "Emerald Engagement Ring",
        "type": "equipment",
        "slot": "accessory",
        "unique": True,
        "base_mods": {"Dexterity": 3},
        "elemental_dmg": {"wind": 1.1},
    },
    "topaz_engagement_ring": {
        "name": "Topaz Engagement Ring",
        "type": "equipment",
        "slot": "accessory",
        "unique": True,
        "base_mods": {"Learning": 3},
        "elemental_dmg": {"thunder": 1.1},
    },
    "amethyst_engagement_ring": {
        "name": "Amethyst Engagement Ring",
        "type": "equipment",
        "slot": "accessory",
        "unique": True,
        "base_mods": {"Charisma": 3},
        "elemental_dmg": {"dark": 1.1},
    },
    "diamond_engagement_ring": {
        "name": "Diamond Engagement Ring",
        "type": "equipment",
        "slot": "accessory",
        "unique": True,
        "base_mods": {"Constitution": 3},
        "elemental_dmg": {"light": 1.1},
    },

    # === Wedding Accessories (Legendary, Soulbound, One per girl) ===
    "wedding_goblin_girl":        {"name": "Lucky Copper Ring",       "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Charisma": 3, "Learning": 2}, "special": "goblin_luck", "elemental_dmg": {}},
    "wedding_harpy_scout":        {"name": "Windweaver Pinion",       "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Dexterity": 4, "Wisdom": 1}, "special": "tailwind", "elemental_res": {"wind": 1.3}},
    "wedding_alraune_fledger":    {"name": "Pollenheart Locket",      "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Charisma": 3, "Constitution": 2}, "special": "bloom_regen", "elemental_res": {"earth": 1.2}},
    "wedding_kobold_tinkerer":    {"name": "Clockwork Bond Ring",     "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Learning": 4, "Dexterity": 1}, "special": "tinkerers_inspiration", "elemental_res": {"thunder": 1.2}},
    "wedding_dryad_protector":    {"name": "Barkskin Band",           "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Constitution": 4, "Wisdom": 1}, "special": "bark_shield", "elemental_res": {"earth": 1.3, "fire": 1.1}},
    "wedding_ghost_maid":         {"name": "Ectoplasm Veil",          "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Dexterity": 3, "Charisma": 2}, "special": "spectral_dodge", "elemental_res": {"dark": 1.3}},
    "wedding_centaur_scout":      {"name": "Thunderhoof Brooch",      "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Strength": 2, "Dexterity": 3}, "special": "stampede", "elemental_dmg": {"wind": 1.2}},
    "wedding_moth_girl_flutterer":{"name": "Moondust Pendant",        "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Dexterity": 3, "Charisma": 2}, "special": "moth_dust", "elemental_dmg": {"light": 1.2}},
    "wedding_slime_girl":         {"name": "Gelatinous Heart",        "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Constitution": 5, "Learning": 1}, "special": "slime_absorb", "elemental_res": {"water": 1.2, "thunder": 1.2}},
    "wedding_lamia_constrictor":  {"name": "Coiled Serpent Ring",     "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Strength": 2, "Dexterity": 3}, "special": "coil_bind", "elemental_dmg": {"earth": 1.2}},
    "wedding_lizard_queen":       {"name": "Crownscale Circlet",      "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Charisma": 3, "Constitution": 2}, "special": "regal_presence", "elemental_res": {"fire": 1.2, "earth": 1.2}},
    "wedding_mimic_girl":         {"name": "Mimic's Tooth",           "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Strength": 3, "Dexterity": 2}, "special": "mimic_jackpot", "elemental_dmg": {"dark": 1.2}},
    "wedding_umbral_weaver":      {"name": "Shadowthread Ring",       "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Dexterity": 3, "Wisdom": 2}, "special": "shadow_cloak", "elemental_res": {"dark": 1.3}},
    "wedding_winter_fairy":       {"name": "Frostbloom Charm",        "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Dexterity": 3, "Charisma": 2}, "special": "frost_aura", "elemental_dmg": {"water": 1.3}},
    "wedding_holstaur_brawler":   {"name": "Bullheart Signet",        "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Strength": 4, "Constitution": 2}, "special": "bull_rush", "elemental_dmg": {"earth": 1.3}},
    "wedding_gargoyle_watcher":   {"name": "Stonegaze Locket",        "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Constitution": 4, "Strength": 2}, "special": "stone_endurance", "elemental_res": {"earth": 1.3, "wind": 1.2}},
    "wedding_vampire_seductress": {"name": "Sanguine Kiss Ring",      "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Charisma": 4, "Dexterity": 2}, "special": "blood_drain", "elemental_dmg": {"dark": 1.3}},
    "wedding_yuki_onna":          {"name": "Blizzard Veil",           "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Charisma": 3, "Learning": 3}, "special": "blizzard_song", "elemental_dmg": {"water": 1.3, "wind": 1.2}},
    "wedding_amazon_warrior":     {"name": "Warband of the Sister",   "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Strength": 3, "Dexterity": 2, "Charisma": 1}, "special": "war_sister", "elemental_dmg": {"fire": 1.2, "wind": 1.1}},
    "wedding_banshee_wailer":     {"name": "Wailing Spirit Locket",   "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Charisma": 4, "Wisdom": 2}, "special": "keening_wail", "elemental_dmg": {"dark": 1.2, "wind": 1.2}},
    "wedding_neko_ninja":         {"name": "Nekomata Bell",           "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Dexterity": 5, "Strength": 1}, "special": "neko_shadow", "elemental_dmg": {"dark": 1.2, "wind": 1.1}},
    "wedding_arachne_weaver":     {"name": "Silkspinner Band",        "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Dexterity": 4, "Strength": 2}, "special": "silk_bind", "elemental_res": {"earth": 1.2, "dark": 1.2}},
    "wedding_mummy_princess":     {"name": "Pharaoh's Band",          "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Charisma": 4, "Constitution": 2, "Learning": 1}, "special": "pharaohs_curse", "elemental_res": {"dark": 1.2, "earth": 1.2}},
    "wedding_oni_bruiser":        {"name": "Oni Horn Ring",           "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Strength": 5, "Constitution": 2}, "special": "oni_rage", "elemental_dmg": {"fire": 1.3, "earth": 1.2}},
    "wedding_salamander_dancer":  {"name": "Emberwaltz Ring",         "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Dexterity": 3, "Charisma": 3}, "special": "flame_dance", "elemental_dmg": {"fire": 1.3}},
    "wedding_succubus_seductress":{"name": "Dreamcatcher Ring",       "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Charisma": 5, "Dexterity": 2}, "special": "dream_drain", "elemental_dmg": {"dark": 1.3}},
    "wedding_dullahan_knight":    {"name": "Headless Rider's Seal",   "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Strength": 4, "Constitution": 2, "Charisma": 1}, "special": "headless_oath", "elemental_res": {"dark": 1.2, "light": 1.1}},
    "wedding_kitsune_miko":       {"name": "Foxfire Band",            "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Wisdom": 4, "Charisma": 3}, "special": "foxfire_trick", "elemental_dmg": {"fire": 1.2, "light": 1.2}},
    "wedding_siren_empress":      {"name": "Coral Crown Ring",        "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Charisma": 5, "Dexterity": 2}, "special": "siren_song", "elemental_dmg": {"water": 1.3, "wind": 1.1}},
    "wedding_crimson_countess":   {"name": "Crimson Sigil",           "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Charisma": 5, "Dexterity": 2}, "special": "crimson_feast", "elemental_dmg": {"dark": 1.3, "water": 1.2}},
    "wedding_demon_whip_master":  {"name": "Whipmaster's Coil",       "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Dexterity": 4, "Charisma": 2}, "special": "whip_crack", "elemental_dmg": {"fire": 1.2, "dark": 1.2}},
    "wedding_minotaur_gladiator": {"name": "Arenaborn Signet",        "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Strength": 5, "Constitution": 2, "Dexterity": 1}, "special": "arena_glory", "elemental_dmg": {"earth": 1.3, "fire": 1.1}},
    "wedding_vampire_matriarch":  {"name": "Matriarch's Favor",       "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Charisma": 4, "Constitution": 3, "Wisdom": 2}, "special": "matriarchs_embrace", "elemental_res": {"dark": 1.3, "water": 1.2}},
    "wedding_centaur_champion":   {"name": "Champion's Mane Ring",    "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Strength": 3, "Dexterity": 3, "Charisma": 2}, "special": "champion_charge", "elemental_dmg": {"wind": 1.3, "light": 1.2}},
    "wedding_infernal_empress":   {"name": "Infernal Throne Seal",    "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Strength": 4, "Charisma": 4, "Constitution": 2}, "special": "infernal_crown", "elemental_dmg": {"fire": 1.4, "dark": 1.3}},
    "wedding_scylla_wrecker":     {"name": "Abyssal Coil",            "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Strength": 4, "Constitution": 3, "Dexterity": 1}, "special": "abyssal_grasp", "elemental_dmg": {"water": 1.4, "dark": 1.2}},
    "wedding_gorgon_petrifier":   {"name": "Gorgon's Veil Ring",      "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Dexterity": 3, "Charisma": 3, "Wisdom": 2}, "special": "stone_gaze", "elemental_dmg": {"earth": 1.3, "dark": 1.2}},
    "wedding_ninetales_fox":      {"name": "Sunfire Band",            "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Charisma": 5, "Wisdom": 3, "Learning": 2}, "special": "legendary_flame", "elemental_dmg": {"fire": 1.4, "light": 1.3}},
    "wedding_mermaid_siren_queen":{"name": "Tidecaller Ring",         "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Charisma": 5, "Wisdom": 3, "Learning": 2}, "special": "tidal_blessing", "elemental_dmg": {"water": 1.4, "wind": 1.2}},
    "wedding_draconic_valkyrie":  {"name": "Dragonwing Signet",       "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Strength": 4, "Constitution": 3, "Charisma": 2}, "special": "dragon_judgment", "elemental_dmg": {"fire": 1.3, "wind": 1.3}},
    "wedding_sphinx_riddler":     {"name": "Riddlelock Band",         "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Learning": 5, "Wisdom": 3, "Charisma": 2}, "special": "riddle_solved", "elemental_dmg": {"thunder": 1.3, "light": 1.2}},
    "wedding_lich_queen_avatar":  {"name": "Phylactery Bond",         "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Learning": 6, "Charisma": 3, "Wisdom": 2}, "special": "lich_grasp", "elemental_dmg": {"dark": 1.4, "thunder": 1.2}},
    "wedding_valkyrie_commander": {"name": "Commander's Ring",        "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Strength": 4, "Dexterity": 3, "Charisma": 3}, "special": "valkyrie_ride", "elemental_dmg": {"light": 1.3, "wind": 1.2}},
    "wedding_dragon_goddess_avatar":{"name": "Stardust Crown",        "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Strength": 5, "Constitution": 4, "Charisma": 3}, "special": "starfire_breath", "elemental_dmg": {"fire": 1.4, "light": 1.4, "thunder": 1.2}},
    "wedding_arachne_brood_queen":{"name": "Broodmother's Web",       "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Dexterity": 5, "Strength": 3, "Constitution": 2}, "special": "brood_swarm", "elemental_res": {"earth": 1.3, "dark": 1.3}},
    "wedding_cosmic_slime_empress":{"name": "Galaxy Heart",           "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Constitution": 6, "Learning": 5, "Charisma": 4}, "special": "cosmic_gravity", "elemental_res": {"fire": 1.2, "water": 1.2, "thunder": 1.2, "wind": 1.2, "earth": 1.2, "light": 1.2, "dark": 1.2}},
}

def build_item(item_id, rarity="common", enhance=0):
    base = ITEMS[item_id]
    # Some items (e.g. Ascension Stones) have a fixed rarity regardless of drop/shop roll
    if base.get("rarity"):
        rarity = base["rarity"]
    r = ITEM_RARITY[rarity]

    item = {
        "id": item_id,
        "name": f"{rarity.title()} {base['name']}",
        "type": base["type"],
        "rarity": rarity,
        "enhance": enhance,
    }

    if base["type"] == "equipment":
        item["slot"] = base["slot"]
        base_mods = base["base_mods"]
        item["mods"] = {
            stat: int(val * r["stat_mult"]) + enhance
            for stat, val in base_mods.items()
        }
        
        # Carry over custom properties (Added elemental support)
        for custom_key in ["special", "unique", "drop_source", "drop_rarity", "scaling_stat", "elemental_dmg", "elemental_res"]:
            if custom_key in base:
                item[custom_key] = base[custom_key]
        
        # Scale elemental stats by rarity (additive from neutral 1.0)
        if "elemental_dmg" in item:
            item["elemental_dmg"] = {
                el: round(1.0 + (val - 1.0) * r["stat_mult"], 2)
                for el, val in item["elemental_dmg"].items()
            }
        if "elemental_res" in item:
            item["elemental_res"] = {
                el: round(1.0 + (val - 1.0) * r["stat_mult"], 2)
                for el, val in item["elemental_res"].items()
            }
    elif base["type"] in ("consumable", "utility", "scroll"):
        item["count"] = 1
        if base["type"] == "consumable":
            item["power"] = int(base.get("base_power", 0) * r["stat_mult"])
            for k in ["temp_stat", "duration", "heal_over_time", "defense_buff", "cure_curse"]:
                if k in base:
                    item[k] = base[k]
                    
        elif base["type"] == "utility":
            item["power"] = int(base.get("base_power", 0) * r["stat_mult"])
            # ADDED "fixed_flee" to the list below:
            for k in ["status", "bonus_vs", "escape_bonus", "damage_over_time", "duration", "stun_chance", "blind_enemy", "armor_pierce", "fixed_flee", "capture_net", "rarity_mult_bonus", "ascension_tier"]:
                if k in base:
                    item[k] = base[k]
                    
        elif base["type"] == "scroll":
            item["target_rarity"] = rarity
        
    return item

def random_equipment(rarity=None):
    if rarity is None:
        rarity = random.choices(
            ["common", "uncommon", "rare", "epic", "legendary"],
            weights=[50, 30, 15, 4, 1]
        )[0]
    equip_ids = [item_id for item_id, data in ITEMS.items() if data.get("slot") and not data.get("unique")]
    if not equip_ids:
        return {
            "name": "Mysterious Relic",
            "type": "equipment",
            "rarity": rarity,
            "mods": {},
            "slot": "accessory"
        }
    item_id = random.choice(equip_ids)
    return build_item(item_id, rarity)

def upgrade_rarity(rarity: str) -> str:
    order = ["common", "uncommon", "rare", "epic", "legendary"]
    idx = order.index(rarity)
    return order[min(idx+1, len(order)-1)]