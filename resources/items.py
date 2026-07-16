# resources/items.py
import random

ITEM_RARITY = {
    "common":    {"stat_mult": 1.00, "price_mult": 1.0},
    "uncommon":  {"stat_mult": 1.15, "price_mult": 1.4},
    "rare":      {"stat_mult": 1.35, "price_mult": 2.2},
    "epic":      {"stat_mult": 1.60, "price_mult": 4.0},
    "legendary": {"stat_mult": 1.90, "price_mult": 8.0},
    "unique":    {"stat_mult": 1.00, "price_mult": 1.0},  # unused — uniques don't go through stat_mult scaling
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

    # === Elemental Consumables (Phase 3 — no rarity scaling, situational side-effects) ===
    "ember_draught":    {"name": "Ember Draught",    "type": "consumable", "base_power": 40, "buff_fire_resist": 0.20, "buff_duration": 2},
    "frostward_tonic":  {"name": "Frostward Tonic",  "type": "consumable", "base_power": 40, "cleanse_burn_poison": True},
    "thunderbrew":      {"name": "Thunderbrew",      "type": "consumable", "base_power": 30, "cooldown_reduce": 1},
    "gale_cordial":     {"name": "Gale Cordial",     "type": "consumable", "base_power": 35, "init_bonus": 3, "buff_duration": 3},
    "stoneblood_vial":  {"name": "Stoneblood Vial",  "type": "consumable", "base_power": 30, "defense_buff": 0.15, "buff_duration": 2},
    "blessed_water":    {"name": "Blessed Water",    "type": "consumable", "base_power": 50, "cleanse_curse_debuff": True},
    "shadow_essence":   {"name": "Shadow Essence",   "type": "consumable", "base_power": 25, "dodge_next": True},
    "mana_philter":     {"name": "Mana Philter",     "type": "consumable", "base_power": 0,  "restore_random_skill": True},

    # === Weapons === (Added "scaling_stat" + "primary_element" properties)
    # Elemental prefix naming: [ElementPrefix] + [WeaponType] — tells element at a glance.

    # --- Physical Weapons (STR / CON) ---
    "iron_sword":       {"name": "Iron Sword",       "type": "equipment", "slot": "weapon", "base_mods": {"Strength": 2},                     "scaling_stat": "Strength",    "primary_element": "physical", "elemental_dmg": {"physical": 1.2}},
    "steel_sword":      {"name": "Steel Sword",      "type": "equipment", "slot": "weapon", "base_mods": {"Strength": 3},                     "scaling_stat": "Strength",    "primary_element": "physical", "elemental_dmg": {"physical": 1.2}},

    # --- Fire Weapons (STR / DEX / LRN / CHA / CON) ---
    "ember_flail":      {"name": "Ember Flail",      "type": "equipment", "slot": "weapon", "base_mods": {"Strength": 3, "Constitution": 1},  "scaling_stat": "Strength",    "primary_element": "fire",      "elemental_dmg": {"physical": 1.2, "fire": 1.3}},
    "blaze_axe":        {"name": "Blaze Axe",        "type": "equipment", "slot": "weapon", "base_mods": {"Strength": 4},                     "scaling_stat": "Strength",    "primary_element": "fire",      "elemental_dmg": {"physical": 1.3, "fire": 1.3}},
    "inferno_greatsword":{"name": "Inferno Greatsword","type": "equipment","slot": "weapon", "base_mods": {"Strength": 5},                     "scaling_stat": "Strength",    "primary_element": "fire",      "elemental_dmg": {"physical": 1.3, "fire": 1.3}},
    "spark_hand_crossbow":{"name": "Spark Hand Crossbow","type": "equipment","slot": "weapon","base_mods": {"Dexterity": 2},                   "scaling_stat": "Dexterity",   "primary_element": "fire",      "elemental_dmg": {"physical": 1.1, "fire": 1.2}},
    "blaze_lute":       {"name": "Blaze Lute",       "type": "equipment", "slot": "weapon", "base_mods": {"Charisma": 4, "Learning": 1},      "scaling_stat": "Charisma",    "primary_element": "fire",      "elemental_dmg": {"magical": 1.1, "fire": 1.3, "wind": 1.1}},
    "magma_gauntlets":  {"name": "Magma Gauntlets",  "type": "equipment", "slot": "weapon", "base_mods": {"Constitution": 2, "Strength": 1},  "scaling_stat": "Constitution","scaling_mult": 0.5, "con_defense": True, "primary_element": "fire",      "elemental_dmg": {"physical": 1.2, "fire": 1.3}},

    # --- Water Weapons (STR / DEX / LRN / WIS) ---
    "frost_blade":      {"name": "Frost Blade",      "type": "equipment", "slot": "weapon", "base_mods": {"Strength": 4, "Dexterity": 2},     "scaling_stat": "Strength",    "primary_element": "water",     "elemental_dmg": {"physical": 1.2, "water": 1.3}},
    "rime_bow":         {"name": "Rime Bow",         "type": "equipment", "slot": "weapon", "base_mods": {"Dexterity": 4},                     "scaling_stat": "Dexterity",   "primary_element": "water",     "elemental_dmg": {"physical": 1.2, "water": 1.2}},
    "torrent_orb":      {"name": "Torrent Orb",      "type": "equipment", "slot": "weapon", "base_mods": {"Learning": 3, "Charisma": 1},       "scaling_stat": "Learning",    "primary_element": "water",     "elemental_dmg": {"magical": 1.3, "water": 1.3}},
    "glacier_scepter":  {"name": "Glacier Scepter",  "type": "equipment", "slot": "weapon", "base_mods": {"Wisdom": 3, "Charisma": 2},         "scaling_stat": "Wisdom",      "primary_element": "water",     "elemental_dmg": {"magical": 1.2, "water": 1.3}},

    # --- Thunder Weapons (STR / DEX / LRN) ---
    "storm_hammer":     {"name": "Storm Hammer",     "type": "equipment", "slot": "weapon", "base_mods": {"Strength": 5},                     "scaling_stat": "Strength",    "primary_element": "thunder",   "elemental_dmg": {"physical": 1.3, "thunder": 1.3}},
    "volt_chakram":     {"name": "Volt Chakram",     "type": "equipment", "slot": "weapon", "base_mods": {"Dexterity": 3, "Strength": 1},      "scaling_stat": "Dexterity",   "primary_element": "thunder",   "elemental_dmg": {"physical": 1.2, "thunder": 1.2}},
    "thunder_wand":     {"name": "Thunder Wand",     "type": "equipment", "slot": "weapon", "base_mods": {"Learning": 2, "Wisdom": 1},         "scaling_stat": "Learning",    "primary_element": "thunder",   "elemental_dmg": {"magical": 1.2, "thunder": 1.2}},

    # --- Wind Weapons (STR / DEX / CHA) ---
    "gale_spear":       {"name": "Gale Spear",       "type": "equipment", "slot": "weapon", "base_mods": {"Strength": 3, "Dexterity": 1},     "scaling_stat": "Strength",    "primary_element": "wind",      "elemental_dmg": {"physical": 1.2, "wind": 1.2, "earth": 1.1}},
    "zephyr_halberd":   {"name": "Zephyr Halberd",   "type": "equipment", "slot": "weapon", "base_mods": {"Strength": 4, "Dexterity": 2},     "scaling_stat": "Strength",    "primary_element": "wind",      "elemental_dmg": {"physical": 1.2, "wind": 1.2, "earth": 1.2}},
    "gale_bow":         {"name": "Gale Bow",         "type": "equipment", "slot": "weapon", "base_mods": {"Dexterity": 4},                     "scaling_stat": "Dexterity",   "primary_element": "wind",      "elemental_dmg": {"physical": 1.2, "wind": 1.2}},
    "zephyr_rapier":    {"name": "Zephyr Rapier",    "type": "equipment", "slot": "weapon", "base_mods": {"Dexterity": 4, "Charisma": 1},      "scaling_stat": "Dexterity",   "primary_element": "wind",      "elemental_dmg": {"physical": 1.2, "wind": 1.3}},
    "zephyr_bow":       {"name": "Zephyr Bow",       "type": "equipment", "slot": "weapon", "base_mods": {"Dexterity": 5, "Learning": 1},      "scaling_stat": "Dexterity",   "primary_element": "wind",      "elemental_dmg": {"physical": 1.2, "wind": 1.3, "light": 1.1}},
    "cyclone_crossbow": {"name": "Cyclone Crossbow", "type": "equipment", "slot": "weapon", "base_mods": {"Dexterity": 3, "Learning": 1},      "scaling_stat": "Dexterity",   "primary_element": "wind",      "elemental_dmg": {"physical": 1.2, "wind": 1.3}},
    "zephyr_harp":      {"name": "Zephyr Harp",      "type": "equipment", "slot": "weapon", "base_mods": {"Charisma": 3, "Dexterity": 2},      "scaling_stat": "Charisma",    "primary_element": "wind",      "elemental_dmg": {"magical": 1.1, "wind": 1.3, "light": 1.1}},

    # --- Earth Weapons (STR / CON) ---
    "stone_mace":       {"name": "Stone Mace",       "type": "equipment", "slot": "weapon", "base_mods": {"Strength": 2, "Wisdom": 1},         "scaling_stat": "Strength",    "primary_element": "earth",     "elemental_dmg": {"physical": 1.2, "earth": 1.2}},
    "grave_maul":       {"name": "Grave Maul",       "type": "equipment", "slot": "weapon", "base_mods": {"Strength": 4, "Constitution": 1},   "scaling_stat": "Strength",    "primary_element": "earth",     "elemental_dmg": {"physical": 1.3, "earth": 1.3}},
    "titan_shield":     {"name": "Titan Shield",     "type": "equipment", "slot": "weapon", "base_mods": {"Constitution": 3},                   "scaling_stat": "Constitution","scaling_mult": 0.5, "con_defense": True, "primary_element": "physical",  "elemental_dmg": {"physical": 1.1, "earth": 1.1}},
    "bedrock_mace":     {"name": "Bedrock Mace",     "type": "equipment", "slot": "weapon", "base_mods": {"Constitution": 3, "Strength": 1},     "scaling_stat": "Constitution","scaling_mult": 0.5, "con_defense": True, "primary_element": "earth",     "elemental_dmg": {"physical": 1.2, "earth": 1.2}},
    "stone_plate":      {"name": "Stone Plate",      "type": "equipment", "slot": "weapon", "base_mods": {"Constitution": 4},                   "scaling_stat": "Constitution","scaling_mult": 0.5, "con_defense": True, "primary_element": "earth",     "elemental_dmg": {"physical": 1.1, "earth": 1.1, "fire": 1.1}},

    # --- Light Weapons (STR / WIS / CHA) ---
    "radiant_sword":    {"name": "Radiant Sword",    "type": "equipment", "slot": "weapon", "base_mods": {"Strength": 3, "Wisdom": 2},          "scaling_stat": "Strength",    "primary_element": "light",     "elemental_dmg": {"physical": 1.2, "light": 1.3}},
    "divine_staff":     {"name": "Divine Staff",     "type": "equipment", "slot": "weapon", "base_mods": {"Wisdom": 4, "Constitution": 1},       "scaling_stat": "Wisdom",      "primary_element": "light",     "elemental_dmg": {"magical": 1.2, "light": 1.3}},
    "radiant_mace":     {"name": "Radiant Mace",     "type": "equipment", "slot": "weapon", "base_mods": {"Wisdom": 4, "Strength": 1},           "scaling_stat": "Wisdom",      "primary_element": "light",     "elemental_dmg": {"physical": 1.1, "magical": 1.1, "light": 1.2, "earth": 1.1}},
    "radiant_lute":     {"name": "Radiant Lute",     "type": "equipment", "slot": "weapon", "base_mods": {"Charisma": 4, "Learning": 1},         "scaling_stat": "Charisma",    "primary_element": "light",     "elemental_dmg": {"magical": 1.1, "light": 1.3, "wind": 1.1}},

    # --- Dark Weapons (STR / DEX / LRN / CHA) ---
    "void_blade":       {"name": "Void Blade",       "type": "equipment", "slot": "weapon", "base_mods": {"Strength": 5, "Dexterity": 3},      "scaling_stat": "Strength",    "primary_element": "dark",      "elemental_dmg": {"physical": 1.3, "dark": 1.3, "water": 1.2}},
    "shadow_dagger":    {"name": "Shadow Dagger",    "type": "equipment", "slot": "weapon", "base_mods": {"Dexterity": 3},                     "scaling_stat": "Dexterity",   "primary_element": "dark",      "elemental_dmg": {"physical": 1.1, "dark": 1.2}},
    "nether_blade":     {"name": "Nether Blade",     "type": "equipment", "slot": "weapon", "base_mods": {"Learning": 3, "Wisdom": 2},           "scaling_stat": "Learning",    "primary_element": "dark",      "elemental_dmg": {"magical": 1.2, "dark": 1.3}},
    "nether_grimoire":  {"name": "Nether Grimoire",  "type": "equipment", "slot": "weapon", "base_mods": {"Learning": 5},                       "scaling_stat": "Learning",    "primary_element": "dark",      "elemental_dmg": {"magical": 1.3, "dark": 1.3, "fire": 1.1}},
    "shadow_tongue_dagger":{"name": "Shadow Tongue Dagger","type": "equipment","slot": "weapon","base_mods": {"Charisma": 3, "Dexterity": 2},   "scaling_stat": "Charisma",    "primary_element": "dark",      "elemental_dmg": {"physical": 1.1, "dark": 1.2, "wind": 1.1}},

    # --- Magical Weapons (LRN / WIS / CHA) ---
    "arcane_staff":     {"name": "Arcane Staff",     "type": "equipment", "slot": "weapon", "base_mods": {"Learning": 4},                       "scaling_stat": "Learning",    "primary_element": "magical",   "elemental_dmg": {"magical": 1.2, "thunder": 1.2}},
    "mystic_dagger":    {"name": "Mystic Dagger",    "type": "equipment", "slot": "weapon", "base_mods": {"Dexterity": 2, "Learning": 2},        "scaling_stat": "Dexterity",   "primary_element": "magical",   "elemental_dmg": {"physical": 1.1, "magical": 1.2, "thunder": 1.2, "dark": 1.1}},
    "astral_orb":       {"name": "Astral Orb",       "type": "equipment", "slot": "weapon", "base_mods": {"Wisdom": 3, "Learning": 1},           "scaling_stat": "Wisdom",      "primary_element": "magical",   "elemental_dmg": {"magical": 1.3, "light": 1.3}},
    "mystic_bell":      {"name": "Mystic Bell",      "type": "equipment", "slot": "weapon", "base_mods": {"Charisma": 3, "Learning": 2},          "scaling_stat": "Charisma",    "primary_element": "magical",   "elemental_dmg": {"magical": 1.2, "thunder": 1.2}},

    # === Unique Weapons (keep existing IDs and names) ===

    "abyss_fang": {
        "name": "Abyss Fang",
        "type": "equipment",
        "slot": "weapon",
        "unique": True,
        "base_mods": {"Strength": 18, "Dexterity": 9},
        "special": "dream_devour",
        "drop_source": "dream_devouring_slitcurrent",
        "drop_rarity": "unique",
        "scaling_stat": ["Strength", "Dexterity"],
        "elemental_dmg": {"physical": 1.3, "dark": 1.5},
    },

    "tarnished_jade": {
        "name": "Tarnished Jade",
        "type": "equipment",
        "slot": "armor",
        "unique": True,
        "base_mods": {"Constitution": 15, "Wisdom": 12, "Strength": 9},
        "elemental_res": {"physical": 1.1, "magical": 1.1, "light": 1.3, "thunder": 1.2, "fire": 1.1},
        "special": "tarnished_jade",
        "drop_source": "heaven_banished_dragon_yinglong",
        "drop_rarity": "unique",
    },

    "cutlass_of_the_captain": {
        "name": "Cutlass of the Captain",
        "type": "equipment",
        "slot": "weapon",
        "unique": True,
        "base_mods": {"Strength": 15, "Dexterity": 9},
        "scaling_stat": "Strength",
        "elemental_dmg": {"physical": 1.3, "water": 1.3, "dark": 1.2},
        "special": "captain_cutlass",
        "drop_source": "captain_everlong_ship",
        "drop_rarity": "unique",
    },

    # === Armor === (Added "primary_element" for elemental trait support)
    # Physical armor
    "iron_padded_armor": {"name": "Iron Padded Armor","type": "equipment","slot": "armor","base_mods": {"Constitution": 2},                       "primary_element": "physical", "elemental_res": {"physical": 1.1, "earth": 1.1}},
    "steel_chainmail":   {"name": "Steel Chainmail",  "type": "equipment","slot": "armor","base_mods": {"Constitution": 3},                       "primary_element": "physical", "elemental_res": {"physical": 1.2, "fire": 1.2, "earth": 1.1}},
    "steel_scale_armor": {"name": "Steel Scale Armor", "type": "equipment","slot": "armor","base_mods": {"Constitution": 3, "Strength": 1},      "primary_element": "physical", "elemental_res": {"physical": 1.2, "fire": 1.2, "earth": 1.1}},
    "iron_banded_mail":  {"name": "Iron Banded Mail",  "type": "equipment","slot": "armor","base_mods": {"Constitution": 4, "Dexterity": -1},    "primary_element": "physical", "elemental_res": {"physical": 1.2, "fire": 1.2, "earth": 1.2, "wind": 0.8}},

    # Fire armor
    "ember_dragonhide":  {"name": "Ember Dragonhide",  "type": "equipment","slot": "armor","base_mods": {"Constitution": 4, "Dexterity": 2},    "primary_element": "fire",      "elemental_res": {"physical": 1.1, "fire": 1.3, "earth": 1.2}},
    "blaze_battle_harness":{"name": "Blaze Battle Harness","type": "equipment","slot": "armor","base_mods": {"Strength": 2, "Constitution": 2},"primary_element": "fire",      "elemental_res": {"physical": 1.2, "fire": 1.2, "earth": 1.1}},

    # Water armor
    "frost_fur_mantle":  {"name": "Frost Fur Mantle",   "type": "equipment","slot": "armor","base_mods": {"Constitution": 2, "Wisdom": 1},      "primary_element": "water",     "elemental_res": {"physical": 1.1, "wind": 1.2, "earth": 1.1, "water": 1.1}},

    # Wind armor
    "gale_leathers":     {"name": "Gale Leathers",      "type": "equipment","slot": "armor","base_mods": {"Dexterity": 2, "Constitution": 1},  "primary_element": "wind",      "elemental_res": {"physical": 1.1, "wind": 1.2, "thunder": 1.1}},
    "zephyr_elven_mail": {"name": "Zephyr Elven Mail",  "type": "equipment","slot": "armor","base_mods": {"Dexterity": 3, "Learning": 1},      "primary_element": "wind",      "elemental_res": {"physical": 1.1, "wind": 1.3, "light": 1.1}},

    # Earth armor
    "bedrock_plate_armor":{"name": "Bedrock Plate Armor","type": "equipment","slot": "armor","base_mods": {"Constitution": 5, "Dexterity": -1}, "primary_element": "earth",     "elemental_res": {"physical": 1.2, "fire": 1.2, "earth": 1.2, "wind": 0.8}},

    # Dark armor
    "shadow_wraps":      {"name": "Shadow Wraps",       "type": "equipment","slot": "armor","base_mods": {"Dexterity": 4, "Charisma": 1},      "primary_element": "dark",      "elemental_res": {"physical": 1.05, "dark": 1.3, "wind": 1.2}},
    "shadow_silk_garb":  {"name": "Shadow Silk Garb",   "type": "equipment","slot": "armor","base_mods": {"Charisma": 3, "Dexterity": 1},      "primary_element": "dark",      "elemental_res": {"magical": 1.1, "light": 1.2, "dark": 1.2}},

    # Light armor
    "divine_vestments":  {"name": "Divine Vestments",   "type": "equipment","slot": "armor","base_mods": {"Wisdom": 3, "Constitution": 2},     "primary_element": "light",     "elemental_res": {"magical": 1.1, "light": 1.3, "fire": 1.2}},
    "radiant_regalia":   {"name": "Radiant Regalia",    "type": "equipment","slot": "armor","base_mods": {"Charisma": 4, "Wisdom": 1},         "primary_element": "light",     "elemental_res": {"magical": 1.1, "light": 1.3, "dark": 1.2}},

    # Magical armor
    "arcane_robes":      {"name": "Arcane Robes",       "type": "equipment","slot": "armor","base_mods": {"Learning": 3, "Wisdom": 1},         "primary_element": "magical",   "elemental_res": {"magical": 1.2, "light": 1.2, "dark": 1.2, "earth": 0.8}},
    "arcane_vestments":  {"name": "Arcane Vestments",   "type": "equipment","slot": "armor","base_mods": {"Learning": 4, "Constitution": 1},  "primary_element": "magical",   "elemental_res": {"magical": 1.2, "light": 1.2, "dark": 1.2, "thunder": 1.1}},
    "mystic_runic_plate": {"name": "Mystic Runic Plate", "type": "equipment","slot": "armor","base_mods": {"Constitution": 4, "Learning": 2},"primary_element": "magical",   "elemental_res": {"physical": 1.1, "magical": 1.1, "thunder": 1.3, "earth": 1.2, "dark": 1.1}},

    # === Accessories === (Added "primary_element" for elemental trait support)
    # Fire accessories
    "ember_ring":         {"name": "Ember Ring",         "type": "equipment","slot": "accessory","base_mods": {"Strength": 2},                        "primary_element": "fire",    "elemental_res": {"physical": 1.1, "fire": 1.1}},
    "ember_bracers":      {"name": "Ember Bracers",      "type": "equipment","slot": "accessory","base_mods": {"Strength": 3},                        "primary_element": "fire",    "elemental_res": {"physical": 1.1, "fire": 1.1}},
    "blaze_gauntlets":    {"name": "Blaze Gauntlets",    "type": "equipment","slot": "accessory","base_mods": {"Strength": 2, "Dexterity": 1},        "primary_element": "fire",    "elemental_res": {"physical": 1.1, "fire": 1.1}},
    "blaze_band":         {"name": "Blaze Band",         "type": "equipment","slot": "accessory","base_mods": {"Strength": 2, "Wisdom": 1},           "primary_element": "fire",    "elemental_res": {"physical": 1.1, "fire": 1.1}},
    "magma_locket":       {"name": "Magma Locket",       "type": "equipment","slot": "accessory","base_mods": {"Constitution": 3, "Strength": 1},     "primary_element": "fire",    "elemental_res": {"physical": 1.2, "earth": 1.2}},

    # Water accessory
    "frost_ring":         {"name": "Frost Ring",         "type": "equipment","slot": "accessory","base_mods": {"Constitution": 2, "Dexterity": 1},    "primary_element": "water",   "elemental_res": {"physical": 1.1, "earth": 1.1, "water": 1.1}},

    # Wind accessories
    "gale_ring":          {"name": "Gale Ring",          "type": "equipment","slot": "accessory","base_mods": {"Dexterity": 2},                        "primary_element": "wind",    "elemental_res": {"physical": 1.05, "wind": 1.1}},
    "gale_boots":         {"name": "Gale Boots",         "type": "equipment","slot": "accessory","base_mods": {"Dexterity": 3},                        "primary_element": "wind",    "elemental_res": {"physical": 1.05, "wind": 1.2}},
    "zephyr_gloves":      {"name": "Zephyr Gloves",      "type": "equipment","slot": "accessory","base_mods": {"Dexterity": 2, "Charisma": 1},         "primary_element": "wind",    "elemental_res": {"physical": 1.05, "wind": 1.1}},
    "cyclone_anklet":     {"name": "Cyclone Anklet",     "type": "equipment","slot": "accessory","base_mods": {"Dexterity": 3, "Constitution": 1},     "primary_element": "wind",    "elemental_res": {"physical": 1.05, "wind": 1.2, "thunder": 1.1}},

    # Earth accessories
    "stone_amulet":       {"name": "Stone Amulet",       "type": "equipment","slot": "accessory","base_mods": {"Constitution": 3},                     "primary_element": "earth",   "elemental_res": {"physical": 1.1, "earth": 1.1}},
    "stone_belt":         {"name": "Stone Belt",         "type": "equipment","slot": "accessory","base_mods": {"Strength": 3, "Constitution": 2},       "primary_element": "earth",   "elemental_res": {"physical": 1.2, "earth": 1.2}},

    # Dark accessories
    "void_cloak":         {"name": "Void Cloak",         "type": "equipment","slot": "accessory","base_mods": {"Dexterity": 2, "Charisma": 1},         "primary_element": "dark",    "elemental_res": {"dark": 1.2}},
    "shadow_ring":        {"name": "Shadow Ring",        "type": "equipment","slot": "accessory","base_mods": {"Charisma": 3},                         "primary_element": "dark",    "elemental_res": {"magical": 1.1, "dark": 1.1}},
    "void_ring":          {"name": "Void Ring",          "type": "equipment","slot": "accessory","base_mods": {"Charisma": 2, "Wisdom": 1},            "primary_element": "dark",    "elemental_res": {"magical": 1.1, "dark": 1.1}},

    # Light accessories
    "radiant_talisman":   {"name": "Radiant Talisman",   "type": "equipment","slot": "accessory","base_mods": {"Constitution": 2, "Wisdom": 1},       "primary_element": "light",   "elemental_res": {"physical": 1.05, "magical": 1.05, "light": 1.1, "dark": 1.1}},
    "divine_pendant":     {"name": "Divine Pendant",     "type": "equipment","slot": "accessory","base_mods": {"Wisdom": 2, "Learning": 1},             "primary_element": "light",   "elemental_res": {"magical": 1.2, "light": 1.2}},
    "divine_eye":         {"name": "Divine Eye",         "type": "equipment","slot": "accessory","base_mods": {"Wisdom": 3, "Constitution": 1},          "primary_element": "light",   "elemental_res": {"magical": 1.1, "light": 1.2, "dark": 1.1}},
    "radiant_signet":     {"name": "Radiant Signet",     "type": "equipment","slot": "accessory","base_mods": {"Charisma": 4},                          "primary_element": "light",   "elemental_res": {"magical": 1.1, "light": 1.2}},
    "radiant_brooch":     {"name": "Radiant Brooch",     "type": "equipment","slot": "accessory","base_mods": {"Charisma": 2, "Strength": 2},           "primary_element": "light",   "elemental_res": {"physical": 1.05, "magical": 1.05, "light": 1.1, "fire": 1.1}},

    # Magical accessories
    "arcane_tome":        {"name": "Arcane Tome",        "type": "equipment","slot": "accessory","base_mods": {"Learning": 3},                          "primary_element": "magical", "elemental_res": {"magical": 1.1, "thunder": 1.1}},
    "arcane_ring":        {"name": "Arcane Ring",        "type": "equipment","slot": "accessory","base_mods": {"Learning": 3},                          "primary_element": "magical", "elemental_res": {"magical": 1.1, "thunder": 1.1}},
    "arcane_earring":     {"name": "Arcane Earring",     "type": "equipment","slot": "accessory","base_mods": {"Learning": 2, "Charisma": 1},           "primary_element": "magical", "elemental_res": {"magical": 1.1, "light": 1.1}},
    "mystic_crown":       {"name": "Mystic Crown",       "type": "equipment","slot": "accessory","base_mods": {"Learning": 4, "Wisdom": 2},              "primary_element": "magical", "elemental_res": {"magical": 1.2, "thunder": 1.2, "light": 1.1}},
    "mystic_monocle":     {"name": "Mystic Monocle",     "type": "equipment","slot": "accessory","base_mods": {"Learning": 2, "Wisdom": 1},              "primary_element": "magical", "elemental_res": {"magical": 1.1, "thunder": 1.1}},
    "astral_ring":        {"name": "Astral Ring",        "type": "equipment","slot": "accessory","base_mods": {"Wisdom": 3},                             "primary_element": "magical", "elemental_res": {"magical": 1.1, "light": 1.1}},

    # === Utility / Combat Items ===
    "fire_bomb":   {"name": "Fire Bomb",  "type": "utility", "base_power": 22, "burn_tier": 2},
    "ice_bomb":    {"name": "Ice Bomb",   "type": "utility", "base_power": 18, "status": "slow"},
    "holy_water":  {"name": "Holy Water", "type": "utility", "base_power": 25, "bonus_vs": "Undead"},
    "smoke_bomb":  {"name": "Smoke Bomb", "type": "utility", "escape_bonus": 8},
    "thunder_bomb": {"name": "Thunder Bomb", "type": "utility", "base_power": 28, "shock_damage": 5, "shock_duration": 3},
    "acid_flask":   {"name": "Acid Flask", "type": "utility", "base_power": 20, "expose_armor": 2},
    "healing_salve":     {"name": "Healing Salve",     "type": "consumable", "base_power": 40, "heal_over_time": 3, "duration": 3},
    "battle_drink":      {"name": "Battle Drink",      "type": "consumable", "temp_stat": "Strength", "base_power": 5, "duration": 3},
    "iron_skin_potion":  {"name": "Iron Skin Potion",  "type": "consumable", "defense_buff": 4, "duration": 3},
    "poison_flask":      {"name": "Poison Flask",      "type": "utility",    "base_power": 12, "poison_damage": 8, "duration": 3},
    "stun_bomb":         {"name": "Stun Bomb",         "type": "utility",    "stun_chance": 0.6, "base_power": 8},
    "flash_powder":      {"name": "Flash Powder",      "type": "utility",    "escape_bonus": 12, "blind_enemy": True},
    "throwing_knife":    {"name": "Throwing Knife",    "type": "utility",    "base_power": 14, "armor_pierce": 2},
    "curse_cleansing_scroll": {"name": "Scroll of Cleansing", "type": "consumable", "cure_curse": True},
    "antidote": {"name": "Antidote", "type": "consumable", "base_power": 0, "cure_poison": True},
    "armor_shatter_flask": { "name": "Armour Shatter Flask", "type": "utility", "base_power": 0, "expose_armor": 2,},
    "recalled_scroll": {"name": "Scroll of Recall", "type": "utility", "fixed_flee": True},
    # ── Capture Nets (Black Market only — no shop/dungeon/travel drops) ──
    # Per-tier purchase cap enforced in black_market.py
    "capture_net": {
        "name": "Capture Net",
        "type": "utility",
        "base_power": 0,
        "capture_net": True,
        "rarity_mult_bonus": 25,
        "black_market_only": True,
    },
    "reinforced_capture_net": {
        "name": "Reinforced Capture Net",
        "type": "utility",
        "base_power": 0,
        "capture_net": True,
        "rarity_mult_bonus": 37,
        "black_market_only": True,
    },
    "mythril_capture_net": {
        "name": "Mythril Capture Net",
        "type": "utility",
        "base_power": 0,
        "capture_net": True,
        "rarity_mult_bonus": 55,
        "black_market_only": True,
    },

    # Ascension Stones (sold at temples when dungeon floors are cleared)
    "ascension_stone_i":   {"name": "Ascension Stone I",   "type": "ascension", "ascension_tier": 1},
    "ascension_stone_ii":  {"name": "Ascension Stone II",  "type": "ascension", "ascension_tier": 2},
    "ascension_stone_iii": {"name": "Ascension Stone III", "type": "ascension", "ascension_tier": 3},
    "ascension_stone_iv":  {"name": "Ascension Stone IV",  "type": "ascension", "ascension_tier": 4},
    "ascension_stone_v":   {"name": "Ascension Stone V",   "type": "ascension", "ascension_tier": 5},
    "ascension_stone_vi":  {"name": "Ascension Stone VI",  "type": "ascension", "ascension_tier": 6},

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
        "base_mods": {"Strength": 9},
        "elemental_dmg": {"physical": 1.1, "fire": 1.1},
    },
    "sapphire_engagement_ring": {
        "name": "Sapphire Engagement Ring",
        "type": "equipment",
        "slot": "accessory",
        "unique": True,
        "base_mods": {"Wisdom": 9},
        "elemental_dmg": {"magical": 1.1, "water": 1.1},
    },
    "emerald_engagement_ring": {
        "name": "Emerald Engagement Ring",
        "type": "equipment",
        "slot": "accessory",
        "unique": True,
        "base_mods": {"Dexterity": 9},
        "elemental_dmg": {"physical": 1.05, "wind": 1.1},
    },
    "topaz_engagement_ring": {
        "name": "Topaz Engagement Ring",
        "type": "equipment",
        "slot": "accessory",
        "unique": True,
        "base_mods": {"Learning": 9},
        "elemental_dmg": {"magical": 1.1, "thunder": 1.1},
    },
    "amethyst_engagement_ring": {
        "name": "Amethyst Engagement Ring",
        "type": "equipment",
        "slot": "accessory",
        "unique": True,
        "base_mods": {"Charisma": 9},
        "elemental_dmg": {"magical": 1.1, "dark": 1.1},
    },
    "diamond_engagement_ring": {
        "name": "Diamond Engagement Ring",
        "type": "equipment",
        "slot": "accessory",
        "unique": True,
        "base_mods": {"Constitution": 9},
        "elemental_dmg": {"physical": 1.05, "magical": 1.05, "light": 1.1},
    },

    # === Wedding Accessories (Unique, Soulbound, One per girl) ===
    "wedding_goblin_girl":        {"name": "Lucky Copper Ring",       "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Charisma": 9, "Learning": 6}, "special": "goblin_luck", "elemental_dmg": {"physical": 1.05}},
    "wedding_harpy_scout":        {"name": "Windweaver Pinion",       "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Dexterity": 12, "Wisdom": 3}, "special": "tailwind", "elemental_res": {"physical": 1.05, "wind": 1.3}},
    "wedding_alraune_fledger":    {"name": "Pollenheart Locket",      "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Charisma": 9, "Constitution": 6}, "special": "bloom_regen", "elemental_res": {"magical": 1.1, "earth": 1.2}},
    "wedding_kobold_tinkerer":    {"name": "Clockwork Bond Ring",     "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Learning": 12, "Dexterity": 3}, "special": "tinkerers_inspiration", "elemental_res": {"magical": 1.1, "thunder": 1.2}},
    "wedding_dryad_protector":    {"name": "Barkskin Band",           "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Constitution": 12, "Wisdom": 3}, "special": "bark_shield", "elemental_res": {"physical": 1.2, "earth": 1.3, "fire": 1.1}},
    "wedding_ghost_maid":         {"name": "Ectoplasm Veil",          "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Dexterity": 9, "Charisma": 6}, "special": "spectral_dodge", "elemental_res": {"magical": 1.1, "dark": 1.3}},
    "wedding_centaur_scout":      {"name": "Thunderhoof Brooch",      "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Strength": 6, "Dexterity": 9}, "special": "stampede", "elemental_dmg": {"physical": 1.2, "wind": 1.2}},
    "wedding_moth_girl_flutterer":{"name": "Moondust Pendant",        "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Dexterity": 9, "Charisma": 6}, "special": "moth_dust", "elemental_dmg": {"magical": 1.1, "light": 1.2}},
    "wedding_slime_girl":         {"name": "Gelatinous Heart",        "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Constitution": 15, "Learning": 3}, "special": "slime_absorb", "elemental_res": {"physical": 1.1, "water": 1.2, "thunder": 1.2}},
    "wedding_lamia_constrictor":  {"name": "Coiled Serpent Ring",     "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Strength": 6, "Dexterity": 9}, "special": "coil_bind", "elemental_dmg": {"physical": 1.1, "earth": 1.2}},
    "wedding_lizard_queen":       {"name": "Crownscale Circlet",      "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Charisma": 9, "Constitution": 6}, "special": "regal_presence", "elemental_res": {"physical": 1.1, "fire": 1.2, "earth": 1.2}},
    "wedding_mimic_girl":         {"name": "Mimic's Tooth",           "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Strength": 9, "Dexterity": 6}, "special": "mimic_jackpot", "elemental_dmg": {"physical": 1.1, "dark": 1.2}},
    "wedding_umbral_weaver":      {"name": "Shadowthread Ring",       "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Dexterity": 9, "Wisdom": 6}, "special": "shadow_cloak", "elemental_res": {"magical": 1.1, "dark": 1.3}},
    "wedding_winter_fairy":       {"name": "Frostbloom Charm",        "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Dexterity": 9, "Charisma": 6}, "special": "frost_aura", "elemental_dmg": {"magical": 1.2, "water": 1.3}},
    "wedding_holstaur_brawler":   {"name": "Bullheart Signet",        "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Strength": 12, "Constitution": 6}, "special": "bull_rush", "elemental_dmg": {"earth": 1.3}},
    "wedding_gargoyle_watcher":   {"name": "Stonegaze Locket",        "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Constitution": 12, "Strength": 6}, "special": "stone_endurance", "elemental_res": {"earth": 1.3, "wind": 1.2}},
    "wedding_vampire_seductress": {"name": "Sanguine Kiss Ring",      "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Charisma": 12, "Dexterity": 6}, "special": "blood_drain", "elemental_dmg": {"dark": 1.3}},
    "wedding_yuki_onna":          {"name": "Blizzard Veil",           "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Charisma": 9, "Learning": 9}, "special": "blizzard_song", "elemental_dmg": {"water": 1.3, "wind": 1.2}},
    "wedding_amazon_warrior":     {"name": "Warband of the Sister",   "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Strength": 9, "Dexterity": 6, "Charisma": 3}, "special": "war_sister", "elemental_dmg": {"fire": 1.2, "wind": 1.1}},
    "wedding_banshee_wailer":     {"name": "Wailing Spirit Locket",   "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Charisma": 12, "Wisdom": 6}, "special": "keening_wail", "elemental_dmg": {"dark": 1.2, "wind": 1.2}},
    "wedding_neko_ninja":         {"name": "Nekomata Bell",           "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Dexterity": 15, "Strength": 3}, "special": "neko_shadow", "elemental_dmg": {"dark": 1.2, "wind": 1.1}},
    "wedding_arachne_weaver":     {"name": "Silkspinner Band",        "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Dexterity": 12, "Strength": 6}, "special": "silk_bind", "elemental_res": {"earth": 1.2, "dark": 1.2}},
    "wedding_mummy_princess":     {"name": "Pharaoh's Band",          "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Charisma": 12, "Constitution": 6, "Learning": 3}, "special": "pharaohs_curse", "elemental_res": {"dark": 1.2, "earth": 1.2}},
    "wedding_oni_bruiser":        {"name": "Oni Horn Ring",           "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Strength": 15, "Constitution": 6}, "special": "oni_rage", "elemental_dmg": {"fire": 1.3, "earth": 1.2}},
    "wedding_salamander_dancer":  {"name": "Emberwaltz Ring",         "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Dexterity": 9, "Charisma": 9}, "special": "flame_dance", "elemental_dmg": {"fire": 1.3}},
    "wedding_succubus_seductress":{"name": "Dreamcatcher Ring",       "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Charisma": 15, "Dexterity": 6}, "special": "dream_drain", "elemental_dmg": {"dark": 1.3}},
    "wedding_dullahan_knight":    {"name": "Headless Rider's Seal",   "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Strength": 12, "Constitution": 6, "Charisma": 3}, "special": "headless_oath", "elemental_res": {"dark": 1.2, "light": 1.1}},
    "wedding_kitsune_miko":       {"name": "Foxfire Band",            "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Wisdom": 12, "Charisma": 9}, "special": "foxfire_trick", "elemental_dmg": {"fire": 1.2, "light": 1.2}},
    "wedding_siren_empress":      {"name": "Coral Crown Ring",        "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Charisma": 15, "Dexterity": 6}, "special": "siren_song", "elemental_dmg": {"water": 1.3, "wind": 1.1}},
    "wedding_crimson_countess":   {"name": "Crimson Sigil",           "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Charisma": 15, "Dexterity": 6}, "special": "crimson_feast", "elemental_dmg": {"dark": 1.3, "water": 1.2}},
    "wedding_demon_whip_master":  {"name": "Whipmaster's Coil",       "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Dexterity": 12, "Charisma": 6}, "special": "whip_crack", "elemental_dmg": {"fire": 1.2, "dark": 1.2}},
    "wedding_minotaur_gladiator": {"name": "Arenaborn Signet",        "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Strength": 15, "Constitution": 6, "Dexterity": 3}, "special": "arena_glory", "elemental_dmg": {"earth": 1.3, "fire": 1.1}},
    "wedding_vampire_matriarch":  {"name": "Matriarch's Favor",       "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Charisma": 12, "Constitution": 9, "Wisdom": 6}, "special": "matriarchs_embrace", "elemental_res": {"dark": 1.3, "water": 1.2}},
    "wedding_centaur_champion":   {"name": "Champion's Mane Ring",    "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Strength": 9, "Dexterity": 9, "Charisma": 6}, "special": "champion_charge", "elemental_dmg": {"wind": 1.3, "light": 1.2}},
    "wedding_infernal_empress":   {"name": "Infernal Throne Seal",    "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Strength": 12, "Charisma": 12, "Constitution": 6}, "special": "infernal_crown", "elemental_dmg": {"fire": 1.4, "dark": 1.3}},
    "wedding_scylla_wrecker":     {"name": "Abyssal Coil",            "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Strength": 12, "Constitution": 9, "Dexterity": 3}, "special": "abyssal_grasp", "elemental_dmg": {"water": 1.4, "dark": 1.2}},
    "wedding_gorgon_petrifier":   {"name": "Gorgon's Veil Ring",      "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Dexterity": 9, "Charisma": 9, "Wisdom": 6}, "special": "stone_gaze", "elemental_dmg": {"earth": 1.3, "dark": 1.2}},
    "wedding_ninetales_fox":      {"name": "Sunfire Band",            "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Charisma": 15, "Wisdom": 9, "Learning": 6}, "special": "legendary_flame", "elemental_dmg": {"fire": 1.4, "light": 1.3}},
    "wedding_mermaid_siren_queen":{"name": "Tidecaller Ring",         "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Charisma": 15, "Wisdom": 9, "Learning": 6}, "special": "tidal_blessing", "elemental_dmg": {"water": 1.4, "wind": 1.2}},
    "wedding_draconic_valkyrie":  {"name": "Dragonwing Signet",       "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Strength": 12, "Constitution": 9, "Charisma": 6}, "special": "dragon_judgment", "elemental_dmg": {"fire": 1.3, "wind": 1.3}},
    "wedding_sphinx_riddler":     {"name": "Riddlelock Band",         "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Learning": 15, "Wisdom": 9, "Charisma": 6}, "special": "riddle_solved", "elemental_dmg": {"thunder": 1.3, "light": 1.2}},
    "wedding_lich_queen_avatar":  {"name": "Phylactery Bond",         "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Learning": 18, "Charisma": 9, "Wisdom": 6}, "special": "lich_grasp", "elemental_dmg": {"dark": 1.4, "thunder": 1.2}},
    "wedding_valkyrie_commander": {"name": "Commander's Ring",        "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Strength": 12, "Dexterity": 9, "Charisma": 9}, "special": "valkyrie_ride", "elemental_dmg": {"light": 1.3, "wind": 1.2}},
    "wedding_dragon_goddess_avatar":{"name": "Stardust Crown",        "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Strength": 15, "Constitution": 12, "Charisma": 9}, "special": "starfire_breath", "elemental_dmg": {"fire": 1.4, "light": 1.4, "thunder": 1.2}},
    "wedding_arachne_brood_queen":{"name": "Broodmother's Web",       "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Dexterity": 15, "Strength": 9, "Constitution": 6}, "special": "brood_swarm", "elemental_res": {"earth": 1.3, "dark": 1.3}},
    "wedding_cosmic_slime_empress":{"name": "Galaxy Heart",           "type": "equipment", "slot": "accessory", "unique": True, "base_mods": {"Constitution": 18, "Learning": 15, "Charisma": 12}, "special": "cosmic_gravity", "elemental_res": {"fire": 1.2, "water": 1.2, "thunder": 1.2, "wind": 1.2, "earth": 1.2, "light": 1.2, "dark": 1.2}},

    # === Broodmother Superboss Drop ===
    "vileheart_pendant": {
        "name": "Vileheart Pendant",
        "type": "equipment",
        "slot": "accessory",
        "unique": True,
        "base_mods": {"Dexterity": 9, "Strength": 6, "Constitution": 6},
        "elemental_dmg": {"dark": 1.15},
        "elemental_res": {"earth": 1.2, "dark": 1.2},
        "special": "vileheart_venom",
        "drop_source": "broodmother_vileheart",
        "drop_rarity": "unique",
    },

    # === Unique — Superboss Drop ===
    "certain_someone_black_gloves": {
        "name": "Certain Someone Black Gloves",
        "type": "equipment",
        "slot": "weapon",
        "unique": True,
        "base_mods": {"Strength": 12, "Dexterity": 12, "Learning": 9},
        "scaling_stat": ["Strength", "Dexterity", "Learning"],
        "elemental_dmg": {"dark": 1.5},
        "special": "black_silence_gloves",
        "drop_source": "black_silence",
        "drop_rarity": "unique",
    },
    "perception_blocking_mask": {
        "name": "Perception-Blocking Mask",
        "type": "equipment",
        "slot": "accessory",
        "unique": True,
        "base_mods": {"Dexterity": 6, "Learning": 3},
        "elemental_res": {"dark": 1.2},
        "special": "silent_visage",
        "drop_source": "black_silence",
        "drop_rarity": "unique",
    },

    # === Chrysalis Superboss Drops ===
    "chronoweave_mantle": {
        "name": "Chronoweave Mantle",
        "type": "equipment",
        "slot": "armor",
        "unique": True,
        "base_mods": {"Dexterity": 9, "Wisdom": 6, "Learning": 6},
        "elemental_res": {"fire": 1.2, "dark": 1.2, "light": 1.2, "physical": 1.1},
        "special": "chronoweave",
        "drop_source": "entangled_chrysalis",
        "drop_rarity": "unique",
    },
    "fractured_hourglass": {
        "name": "Fractured Hourglass",
        "type": "consumable",
        "base_power": 0,
        "special": "cooldown_reset",
        "drop_source": "entangled_chrysalis",
    },

    # === Wonderland Items ===
    "looking_glass_shard": {
        "name": "Looking Glass Shard",
        "type": "key_item",
        "rarity": "rare",
        "wonderland_only": True,
    },
    "vorpal_blade_rusted": {
        "name": "??? Blade",
        "type": "equipment",
        "slot": "weapon",
        "unique": True,
        "wonderland_only": True,
        "base_mods": {"Strength": 18, "Dexterity": 12},
        "scaling_stat": ["Strength", "Dexterity"],
        "elemental_dmg": {"physical": 1.3, "light": 1.4},
        "special": "vorpal_rusted",
        "drop_rarity": "unique",
    },
    "vorpal_blade": {
        "name": "Vorpal Blade",
        "type": "equipment",
        "slot": "weapon",
        "unique": True,
        "wonderland_only": True,
        "base_mods": {"Strength": 22, "Dexterity": 14},
        "scaling_stat": ["Strength", "Dexterity"],
        "elemental_dmg": {"physical": 1.4, "light": 1.5, "wind": 1.2},
        "special": "vorpal_blade",
        "drop_source": "jabberwock",
        "drop_rarity": "unique",
    },
    "woodcutters_broken_axe": {
        "name": "Woodcutter's Broken Axe",
        "type": "equipment",
        "slot": "weapon",
        "unique": True,
        "wonderland_only": True,
        "base_mods": {"Strength": 15, "Dexterity": 9},
        "scaling_stat": ["Strength", "Dexterity"],
        "elemental_dmg": {"physical": 1.2},
        "special": "woodcutter_broken",
        "drop_rarity": "unique",
    },
    "grandmothers_axe": {
        "name": "Grandmother's Axe",
        "type": "equipment",
        "slot": "weapon",
        "unique": True,
        "wonderland_only": True,
        "base_mods": {"Strength": 22, "Dexterity": 14},
        "scaling_stat": ["Strength", "Dexterity"],
        "elemental_dmg": {"physical": 1.4, "light": 1.3},
        "special": "grandmothers_axe",
        "drop_rarity": "unique",
    },
    "silver_slippers": {
        "name": "Silver Slippers",
        "type": "equipment",
        "slot": "accessory",
        "unique": True,
        "wonderland_only": True,
        "base_mods": {"Dexterity": 9, "Charisma": 6},
        "elemental_res": {"wind": 1.2, "thunder": 1.1},
        "special": "silver_slippers",
        "drop_rarity": "unique",
    },
    "drink_me_potion": {
        "name": "Drink Me Potion",
        "type": "consumable",
        "wonderland_only": True,
        "base_power": 0,
        "temp_stat": "Dexterity",
        "duration": 3,
        "special": "drink_me",
        "rarity": "uncommon",
    },
    "eat_me_cake": {
        "name": "Eat Me Cake",
        "type": "consumable",
        "wonderland_only": True,
        "base_power": 30,
        "temp_stat": "Constitution",
        "duration": 3,
        "rarity": "uncommon",
    },
    "pixie_dust_vial": {
        "name": "Pixie Dust Vial",
        "type": "consumable",
        "wonderland_only": True,
        "base_power": 0,
        "duration": 2,
        "special": "flight_buff",
        "rarity": "rare",
    },
    "pocket_watch": {
        "name": "White Rabbit's Pocket Watch",
        "type": "equipment",
        "slot": "accessory",
        "unique": True,
        "wonderland_only": True,
        "base_mods": {"Dexterity": 2, "Wisdom": 2},
        "elemental_res": {"thunder": 1.2},
        "special": "pocket_watch",
        "drop_rarity": "epic",
    },
    "hook_hand": {
        "name": "Captain's Hook",
        "type": "equipment",
        "slot": "weapon",
        "wonderland_only": True,
        "base_mods": {"Strength": 5, "Dexterity": 3},
        "scaling_stat": "Strength",
        "elemental_dmg": {"physical": 1.2, "dark": 1.3},
        "special": "hook_bleed",
        "drop_rarity": "epic",
    },
    "ruby_slippers": {
        "name": "Ruby Slippers",
        "type": "equipment",
        "slot": "accessory",
        "unique": True,
        "wonderland_only": True,
        "base_mods": {"Dexterity": 9, "Charisma": 9},
        "elemental_res": {"magical": 1.2, "light": 1.3},
        "special": "ruby_slippers",
        "drop_rarity": "unique",
    },
    "rose_tinted_crown": {
        "name": "Rose-Tinted Crown",
        "type": "equipment",
        "slot": "accessory",
        "unique": True,
        "wonderland_only": True,
        "base_mods": {"Charisma": 12, "Wisdom": 6},
        "elemental_res": {"light": 1.2, "dark": 1.1},
        "special": "rose_crown",
        "drop_source": "queen_of_hearts",
        "drop_rarity": "unique",
    },
    "witch_hat": {
        "name": "Wicked Witch's Hat",
        "type": "equipment",
        "slot": "accessory",
        "unique": True,
        "wonderland_only": True,
        "base_mods": {"Learning": 9, "Wisdom": 6},
        "elemental_res": {"dark": 1.2, "thunder": 1.1},
        "special": "im_melting",
        "drop_source": "wicked_witch",
        "drop_rarity": "unique",
    },
    "broomstick": {
        "name": "Broomstick",
        "type": "equipment",
        "slot": "weapon",
        "wonderland_only": True,
        "base_mods": {"Dexterity": 4, "Learning": 3},
        "scaling_stat": "Dexterity",
        "elemental_dmg": {"physical": 1.1, "wind": 1.3, "thunder": 1.2},
        "special": "broomstick_dodge",
        "drop_source": "wicked_witch",
        "drop_rarity": "epic",
    },
    "emerald_flame_crystal": {
        "name": "Emerald Flame Crystal",
        "type": "crafting_material",
        "rarity": "legendary",
        "wonderland_only": True,
        "drop_source": "wicked_witch",
    },
    "monkey_wing": {
        "name": "Monkey Wing",
        "type": "crafting_material",
        "rarity": "rare",
        "wonderland_only": True,
        "drop_source": "wicked_witch",
    },
    "wolfs_tooth": {
        "name": "Wolf's Tooth",
        "type": "crafting_material",
        "rarity": "legendary",
        "wonderland_only": True,
        "drop_source": "big_bad_wolf",
    },
    "crimson_hood_scrap": {
        "name": "Crimson Hood Scrap",
        "type": "crafting_material",
        "rarity": "epic",
        "wonderland_only": True,
        "drop_source": "big_bad_wolf",
    },
    "vorpal_blade_fragment": {
        "name": "Vorpal Blade Fragment",
        "type": "crafting_material",
        "rarity": "legendary",
        "wonderland_only": True,
        "drop_source": "jabberwock",
    },
    "frabjous_page": {
        "name": "Frabjous Page",
        "type": "key_item",
        "rarity": "legendary",
        "wonderland_only": True,
    },
    "witchs_broom": {
        "name": "Witch's Broom (Key)",
        "type": "key_item",
        "rarity": "legendary",
        "wonderland_only": True,
    },
    "authors_pen": {
        "name": "The Author's Pen",
        "type": "equipment",
        "slot": "accessory",
        "unique": True,
        "wonderland_only": True,
        "base_mods": {"Charisma": 15, "Learning": 12, "Wisdom": 9},
        "elemental_dmg": {"magical": 1.3, "light": 1.3, "dark": 1.3},
        "special": "authors_pen",
        "drop_source": "mary_sue",
        "drop_rarity": "unique",
    },
    "mary_sue_teardrop": {
        "name": "Mary Sue's Teardrop",
        "type": "crafting_material",
        "rarity": "legendary",
        "wonderland_only": True,
        "drop_source": "mary_sue",
    },
    "plot_hole_scrap": {
        "name": "Plot Hole Scrap",
        "type": "consumable",
        "wonderland_only": True,
        "base_power": 0,
        "special": "skip_room",
        "rarity": "epic",
        "drop_source": "mary_sue",
    },
    "wonderland_key": {
        "name": "Wonderland Key",
        "type": "key_item",
        "wonderland_only": True,
        "special": "wonderland_access",
        "rarity": "legendary",
    },

    # === Key Items ===
    "glass_anchor": {
        "name": "Glass Anchor",
        "type": "key_item",
        "rarity": "legendary",
        "description": (
            "A crystalline shard attuned to the Isle of Glass, torn from the heart "
            "of its deepest dungeon. It resonates with the island's unstable magic, "
            "allowing arcane teleportation to breach the Isle's wards from outside."
        ),
        "special": "glass_anchor",
        "drop_source": "isle_of_glass_floor_10",
    },

    "no_place_charm": {
        "name": "\"There's No Place\" Charm",
        "type": "equipment",
        "slot": "accessory",
        "unique": True,
        "wonderland_only": True,
        "base_mods": {"Wisdom": 6, "Dexterity": 6},
        "elemental_res": {"physical": 1.1, "magical": 1.1},
        "special": "no_place",
        "drop_rarity": "unique",
    },
}

def _build_unique_item(item_id, base, enhance=0):
    """Build a unique item with hand-tuned stats, bypassing rarity scaling.

    Unique items (Abyss Fang, Vorpal Blade, wedding accessories, etc.)
    do NOT go through the stat_mult system. Their base_mods are used
    directly, enhanced only by the enhance level. Elemental stats are
    also used as-is without rarity scaling.

    A flat +5 compensation is added to all stat mods because unique
    items are capped at +5 enhance (vs. +10 for normal items). This
    ensures a +5 unique has comparable raw stats to a +10 legendary.
    """
    # Unique items get +5 base stats to compensate for the +5 enhance cap
    UNIQUE_BASE_BONUS = 5

    item = {
        "id": item_id,
        "name": base["name"] if enhance <= 0 else f"{base['name']} +{enhance}",
        "type": base["type"],
        "rarity": "unique",
        "enhance": enhance,
    }

    if base["type"] == "equipment":
        item["slot"] = base["slot"]
        # Unique items use their base_mods AS-IS (no stat_mult multiplication)
        # +5 bonus compensates for the lower enhance cap (+5 vs +10)
        item["mods"] = {
            stat: int(val) + enhance + UNIQUE_BASE_BONUS
            for stat, val in base["base_mods"].items()
        }
        # Carry over special properties
        for key in ["special", "unique", "drop_source", "drop_rarity",
                     "scaling_stat", "scaling_mult", "con_defense",
                     "primary_element", "elemental_dmg", "elemental_res",
                     "wonderland_only"]:
            if key in base:
                item[key] = base[key]
    elif base["type"] in ("consumable", "utility", "key_item", "crafting_material"):
        item["count"] = 1
        for key in ["power", "base_power", "special", "drop_source",
                     "temp_stat", "duration", "heal_over_time",
                     "defense_buff", "cure_curse", "escape_bonus",
                     "status", "bonus_vs", "stun_chance", "blind_enemy",
                     "armor_pierce", "fixed_flee", "capture_net",
                     "rarity_mult_bonus", "poison_damage", "wonderland_only",
                     "black_market_only"]:
            if key in base:
                item[key] = base[key]

    return item


def build_item(item_id, rarity="common", enhance=0):
    base = ITEMS[item_id]

    # ── Unique items bypass the rarity scaling system entirely ──
    if base.get("unique") or rarity == "unique":
        return _build_unique_item(item_id, base, enhance)

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
        for custom_key in ["special", "unique", "drop_source", "drop_rarity",
                           "scaling_stat", "scaling_mult", "con_defense",
                           "primary_element", "elemental_dmg", "elemental_res"]:
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
    elif base["type"] in ("consumable", "utility", "scroll", "ascension"):
        item["count"] = 1
        if base["type"] == "consumable":
            # Consumables have NO rarity scaling — power is always base_power.
            # Strip rarity from name/rarity field so players aren't misled.
            item["name"] = base["name"]
            item["rarity"] = "common"
            item["power"] = base.get("base_power", 0)
            for k in ["temp_stat", "duration", "heal_over_time", "defense_buff", "cure_curse",
                       "cure_poison", "special", "drop_source",
                       "buff_fire_resist", "buff_duration", "cleanse_burn_poison", "cooldown_reduce",
                       "init_bonus", "cleanse_curse_debuff", "dodge_next",
                       "restore_random_skill"]:
                if k in base:
                    item[k] = base[k]
                    
        elif base["type"] == "utility":
            # Utilities also have NO rarity scaling — strip rarity from name
            item["name"] = base["name"]
            item["rarity"] = "common"
            item["power"] = base.get("base_power", 0)
            for k in ["status", "bonus_vs", "escape_bonus", "damage_over_time", "duration", "stun_chance", "blind_enemy", "armor_pierce", "fixed_flee", "capture_net", "rarity_mult_bonus", "expose_armor", "poison_damage", "burn_tier", "burn_duration", "shock_damage", "shock_duration", "black_market_only"]:
                if k in base:
                    item[k] = base[k]
                    
        elif base["type"] == "ascension":
            # Ascension stones have NO rarity — strip rarity from name
            item["name"] = base["name"]
            item["rarity"] = "common"
            for k in ["ascension_tier"]:
                if k in base:
                    item[k] = base[k]
                    
        elif base["type"] == "scroll":
            item["target_rarity"] = rarity

    elif base["type"] in ("key_item", "crafting_material"):
        item["count"] = 1
        for k in ["special", "drop_source"]:
            if k in base:
                item[k] = base[k]
        
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