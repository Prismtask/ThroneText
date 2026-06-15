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
    "short_sword":  {"name": "Short Sword", "type": "equipment", "slot": "weapon", "base_mods": {"Strength": 2}, "scaling_stat": "Strength"},
    "long_sword":   {"name": "Long Sword",  "type": "equipment", "slot": "weapon", "base_mods": {"Strength": 3}, "scaling_stat": "Strength"},
    "battle_axe":   {"name": "Battle Axe",  "type": "equipment", "slot": "weapon", "base_mods": {"Strength": 4}, "scaling_stat": "Strength"},
    "greatsword":   {"name": "Greatsword",  "type": "equipment", "slot": "weapon", "base_mods": {"Strength": 5}, "scaling_stat": "Strength"},
    "dagger":       {"name": "Dagger",      "type": "equipment", "slot": "weapon", "base_mods": {"Dexterity": 3}, "scaling_stat": "Dexterity"},
    "war_bow":      {"name": "War Bow",     "type": "equipment", "slot": "weapon", "base_mods": {"Dexterity": 4}, "scaling_stat": "Dexterity"},
    "arcane_staff": {"name": "Arcane Staff","type": "equipment", "slot": "weapon", "base_mods": {"Learning": 4}, "scaling_stat": "Learning"},
    "mace":         {"name": "Mace",        "type": "equipment", "slot": "weapon", "base_mods": {"Strength": 2, "Wisdom": 1}, "scaling_stat": "Strength"},

    # --- Strength Weapons ---
    "spear":        {"name": "Spear",         "type": "equipment", "slot": "weapon", "base_mods": {"Strength": 3, "Dexterity": 1},    "scaling_stat": "Strength"},
    "war_hammer":   {"name": "War Hammer",    "type": "equipment", "slot": "weapon", "base_mods": {"Strength": 5},                    "scaling_stat": "Strength"},
    "flail":        {"name": "Flail",         "type": "equipment", "slot": "weapon", "base_mods": {"Strength": 3, "Constitution": 1}, "scaling_stat": "Strength"},
    "silver_sword": {"name": "Silver Sword",  "type": "equipment", "slot": "weapon", "base_mods": {"Strength": 3, "Wisdom": 2},       "scaling_stat": "Strength"},
    "halberd":      {"name": "Halberd",       "type": "equipment", "slot": "weapon", "base_mods": {"Strength": 4, "Dexterity": 2},    "scaling_stat": "Strength"},

    # --- Dexterity Weapons ---
    "rapier":       {"name": "Rapier",        "type": "equipment", "slot": "weapon", "base_mods": {"Dexterity": 4, "Charisma": 1},   "scaling_stat": "Dexterity"},
    "crossbow":     {"name": "Crossbow",      "type": "equipment", "slot": "weapon", "base_mods": {"Dexterity": 3, "Learning": 1},   "scaling_stat": "Dexterity"},
    "elven_bow":    {"name": "Elven Bow",     "type": "equipment", "slot": "weapon", "base_mods": {"Dexterity": 5, "Learning": 1},   "scaling_stat": "Dexterity"},
    "chakram":      {"name": "Chakram",       "type": "equipment", "slot": "weapon", "base_mods": {"Dexterity": 3, "Strength": 1},   "scaling_stat": "Dexterity"},
    "runic_dagger": {"name": "Runic Dagger",  "type": "equipment", "slot": "weapon", "base_mods": {"Dexterity": 2, "Learning": 2},   "scaling_stat": "Dexterity"},
    "hand_crossbow":{"name": "Hand Crossbow", "type": "equipment", "slot": "weapon", "base_mods": {"Dexterity": 2},                  "scaling_stat": "Dexterity"},

    # --- Learning Weapons ---
    "tome_blade":   {"name": "Tome Blade",    "type": "equipment", "slot": "weapon", "base_mods": {"Learning": 3, "Wisdom": 2},      "scaling_stat": "Learning"},
    "wand":         {"name": "Wand",          "type": "equipment", "slot": "weapon", "base_mods": {"Learning": 2, "Wisdom": 1},      "scaling_stat": "Learning"},
    "grimoire":     {"name": "Grimoire",      "type": "equipment", "slot": "weapon", "base_mods": {"Learning": 5},                   "scaling_stat": "Learning"},
    "runic_orb":    {"name": "Runic Orb",     "type": "equipment", "slot": "weapon", "base_mods": {"Learning": 3, "Charisma": 1},    "scaling_stat": "Learning"},

    # --- Wisdom Weapons ---
    "holy_staff":   {"name": "Holy Staff",    "type": "equipment", "slot": "weapon", "base_mods": {"Wisdom": 4, "Constitution": 1},  "scaling_stat": "Wisdom"},
    "scepter":      {"name": "Scepter",       "type": "equipment", "slot": "weapon", "base_mods": {"Wisdom": 3, "Charisma": 2},      "scaling_stat": "Wisdom"},
    "sacred_mace":  {"name": "Sacred Mace",   "type": "equipment", "slot": "weapon", "base_mods": {"Wisdom": 4, "Strength": 1},      "scaling_stat": "Wisdom"},

    # --- Charisma Weapons ---
    "bards_lute":   {"name": "Bard's Lute",   "type": "equipment", "slot": "weapon", "base_mods": {"Charisma": 4, "Learning": 1},    "scaling_stat": "Charisma"},
    "silver_tongue_dagger": {"name": "Silver-Tongue Dagger", "type": "equipment", "slot": "weapon", "base_mods": {"Charisma": 3, "Dexterity": 2}, "scaling_stat": "Charisma"},

    "abyss_fang": {
        "name": "Abyss Fang",
        "type": "equipment",
        "slot": "weapon",
        "unique": True,
        "base_mods": {"Strength": 6, "Dexterity": 3},
        "special": "dream_devour",       # signals the combat system to show [W]ield the Abyss
        "drop_source": "dream_devouring_slitcurrent",
        "drop_rarity": "legendary",
        "scaling_stat": ["Strength", "Dexterity"],
    },

    # === Armor ===
    "padded_armor": {"name": "Padded Armor","type": "equipment","slot": "armor","base_mods": {"Constitution": 2}},
    "leather_armor":{"name": "Leather Armor","type": "equipment","slot": "armor","base_mods": {"Dexterity": 2, "Constitution": 1}},
    "chainmail":    {"name": "Chainmail",   "type": "equipment","slot": "armor","base_mods": {"Constitution": 3}},
    "plate_armor":  {"name": "Plate Armor", "type": "equipment","slot": "armor","base_mods": {"Constitution": 5, "Dexterity": -1}},
    "dragonhide":   {"name": "Dragonhide Armor", "type": "equipment","slot": "armor","base_mods": {"Constitution": 4, "Dexterity": 2}},

    # --- Strength/Constitution Armor ---
    "scale_armor":      {"name": "Scale Armor",      "type": "equipment", "slot": "armor", "base_mods": {"Constitution": 3, "Strength": 1}},
    "battle_harness":   {"name": "Battle Harness",   "type": "equipment", "slot": "armor", "base_mods": {"Strength": 2, "Constitution": 2}},
    "banded_mail":      {"name": "Banded Mail",      "type": "equipment", "slot": "armor", "base_mods": {"Constitution": 4, "Dexterity": -1}},
    "fur_mantle":       {"name": "Fur Mantle",       "type": "equipment", "slot": "armor", "base_mods": {"Constitution": 2, "Wisdom": 1}},

    # --- Dexterity Armor ---
    "elven_mail":       {"name": "Elven Mail",       "type": "equipment", "slot": "armor", "base_mods": {"Dexterity": 3, "Learning": 1}},
    "shadow_wraps":     {"name": "Shadow Wraps",     "type": "equipment", "slot": "armor", "base_mods": {"Dexterity": 4, "Charisma": 1}},

    # --- Learning / Wisdom Armor ---
    "robes":            {"name": "Robes",             "type": "equipment", "slot": "armor", "base_mods": {"Learning": 3, "Wisdom": 1}},
    "arcane_vestments": {"name": "Arcane Vestments",  "type": "equipment", "slot": "armor", "base_mods": {"Learning": 4, "Constitution": 1}},
    "blessed_vestments":{"name": "Blessed Vestments", "type": "equipment", "slot": "armor", "base_mods": {"Wisdom": 3, "Constitution": 2}},
    "runic_plate":      {"name": "Runic Plate",       "type": "equipment", "slot": "armor", "base_mods": {"Constitution": 4, "Learning": 2}},

    # --- Charisma Armor ---
    "silk_garb":        {"name": "Silk Garb",         "type": "equipment", "slot": "armor", "base_mods": {"Charisma": 3, "Dexterity": 1}},
    "noble_regalia":    {"name": "Noble Regalia",     "type": "equipment", "slot": "armor", "base_mods": {"Charisma": 4, "Wisdom": 1}},

    # === Accessories ===
    "ring_of_power":  {"name": "Ring of Power", "type": "equipment","slot": "accessory","base_mods": {"Strength": 2}},
    "ring_of_grace":  {"name": "Ring of Grace","type": "equipment","slot": "accessory","base_mods": {"Dexterity": 2}},
    "amulet_of_vigor":{"name": "Amulet of Vigor","type": "equipment","slot": "accessory","base_mods": {"Constitution": 3}},
    "tome_of_knowledge":{"name": "Tome of Knowledge","type": "equipment","slot": "accessory","base_mods": {"Learning": 3}},
    "cloak_of_shadows":{"name": "Cloak of Shadows","type": "equipment","slot": "accessory","base_mods": {"Dexterity": 2, "Charisma": 1}},
    "talisman_of_warding":{"name": "Talisman of Warding","type": "equipment","slot": "accessory","base_mods": {"Constitution": 2, "Wisdom": 1}},

    # --- Strength Accessories ---
    "bracers_of_strength":{"name": "Bracers of Strength",  "type": "equipment", "slot": "accessory", "base_mods": {"Strength": 3}},
    "belt_of_giants":     {"name": "Belt of Giants",       "type": "equipment", "slot": "accessory", "base_mods": {"Strength": 3, "Constitution": 2}},
    "gauntlets_of_power": {"name": "Gauntlets of Power",   "type": "equipment", "slot": "accessory", "base_mods": {"Strength": 2, "Dexterity": 1}},
    "war_band":           {"name": "War Band",             "type": "equipment", "slot": "accessory", "base_mods": {"Strength": 2, "Wisdom": 1}},

    # --- Dexterity Accessories ---
    "boots_of_swiftness": {"name": "Boots of Swiftness",   "type": "equipment", "slot": "accessory", "base_mods": {"Dexterity": 3}},
    "nimble_gloves":      {"name": "Nimble Gloves",        "type": "equipment", "slot": "accessory", "base_mods": {"Dexterity": 2, "Charisma": 1}},
    "wind_anklet":        {"name": "Wind Anklet",          "type": "equipment", "slot": "accessory", "base_mods": {"Dexterity": 3, "Constitution": 1}},

    # --- Constitution Accessories ---
    "iron_heart_locket":  {"name": "Iron Heart Locket",    "type": "equipment", "slot": "accessory", "base_mods": {"Constitution": 3, "Strength": 1}},
    "endurance_ring":     {"name": "Endurance Ring",       "type": "equipment", "slot": "accessory", "base_mods": {"Constitution": 2, "Dexterity": 1}},

    # --- Learning Accessories ---
    "ring_of_learning":   {"name": "Ring of Learning",     "type": "equipment", "slot": "accessory", "base_mods": {"Learning": 3}},
    "crown_of_intellect": {"name": "Crown of Intellect",   "type": "equipment", "slot": "accessory", "base_mods": {"Learning": 4, "Wisdom": 2}},
    "earring_of_insight": {"name": "Earring of Insight",   "type": "equipment", "slot": "accessory", "base_mods": {"Learning": 2, "Charisma": 1}},
    "scholars_monocle":   {"name": "Scholar's Monocle",    "type": "equipment", "slot": "accessory", "base_mods": {"Learning": 2, "Wisdom": 1}},

    # --- Wisdom Accessories ---
    "ring_of_wisdom":     {"name": "Ring of Wisdom",       "type": "equipment", "slot": "accessory", "base_mods": {"Wisdom": 3}},
    "pendant_of_wisdom":  {"name": "Pendant of Wisdom",    "type": "equipment", "slot": "accessory", "base_mods": {"Wisdom": 2, "Learning": 1}},
    "oracle_eye":         {"name": "Oracle Eye",           "type": "equipment", "slot": "accessory", "base_mods": {"Wisdom": 3, "Constitution": 1}},

    # --- Charisma Accessories ---
    "ring_of_charisma":   {"name": "Ring of Charisma",     "type": "equipment", "slot": "accessory", "base_mods": {"Charisma": 3}},
    "signet_of_authority":{"name": "Signet of Authority",  "type": "equipment", "slot": "accessory", "base_mods": {"Charisma": 4}},
    "silver_tongue_ring": {"name": "Silver Tongue Ring",   "type": "equipment", "slot": "accessory", "base_mods": {"Charisma": 2, "Wisdom": 1}},
    "brooch_of_valor":    {"name": "Brooch of Valor",      "type": "equipment", "slot": "accessory", "base_mods": {"Charisma": 2, "Strength": 2}},

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

    # === Scrolls ===
    "common_scroll":     {"name": "Scroll of Fusion", "type": "scroll", "target_rarity": "common"},
    "uncommon_scroll":   {"name": "Scroll of Fusion", "type": "scroll", "target_rarity": "uncommon"},
    "rare_scroll":       {"name": "Scroll of Fusion", "type": "scroll", "target_rarity": "rare"},
    "epic_scroll":       {"name": "Scroll of Fusion", "type": "scroll", "target_rarity": "epic"},
    "legendary_scroll":  {"name": "Scroll of Fusion", "type": "scroll", "target_rarity": "legendary"}
}

def build_item(item_id, rarity="common", enhance=0):
    base = ITEMS[item_id]
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
        
        # Carry over custom properties (Added "scaling_stat" to this checklist)
        for custom_key in ["special", "unique", "drop_source", "drop_rarity", "scaling_stat"]:
            if custom_key in base:
                item[custom_key] = base[custom_key]
    elif base["type"] == "consumable":
        item["power"] = int(base.get("base_power", 0) * r["stat_mult"])
        for k in ["temp_stat", "duration", "heal_over_time", "defense_buff", "cure_curse"]:
            if k in base:
                item[k] = base[k]
                
    elif base["type"] == "utility":
        item["power"] = int(base.get("base_power", 0) * r["stat_mult"])
        for k in ["status", "bonus_vs", "escape_bonus", "damage_over_time", "duration", "stun_chance", "blind_enemy", "armor_pierce"]:
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
    equip_ids = [item_id for item_id, data in ITEMS.items() if data.get("slot")]
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