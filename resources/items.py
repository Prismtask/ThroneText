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

    # === Weapons ===
    "short_sword":  {"name": "Short Sword", "type": "equipment", "slot": "weapon", "base_mods": {"Strength": 2}},
    "long_sword":   {"name": "Long Sword",  "type": "equipment", "slot": "weapon", "base_mods": {"Strength": 3}},
    "battle_axe":   {"name": "Battle Axe",  "type": "equipment", "slot": "weapon", "base_mods": {"Strength": 4}},
    "greatsword":   {"name": "Greatsword",  "type": "equipment", "slot": "weapon", "base_mods": {"Strength": 5}},
    "dagger":       {"name": "Dagger",      "type": "equipment", "slot": "weapon", "base_mods": {"Dexterity": 3}},
    "war_bow":      {"name": "War Bow",     "type": "equipment", "slot": "weapon", "base_mods": {"Dexterity": 4}},
    "arcane_staff": {"name": "Arcane Staff","type": "equipment", "slot": "weapon", "base_mods": {"Learning": 4}},
    "mace":         {"name": "Mace",        "type": "equipment", "slot": "weapon", "base_mods": {"Strength": 2, "Wisdom": 1}},

    # === Armor ===
    "padded_armor": {"name": "Padded Armor","type": "equipment","slot": "armor","base_mods": {"Constitution": 2}},
    "leather_armor":{"name": "Leather Armor","type": "equipment","slot": "armor","base_mods": {"Dexterity": 2, "Constitution": 1}},
    "chainmail":    {"name": "Chainmail",   "type": "equipment","slot": "armor","base_mods": {"Constitution": 3}},
    "plate_armor":  {"name": "Plate Armor", "type": "equipment","slot": "armor","base_mods": {"Constitution": 5, "Dexterity": -1}},
    "dragonhide":   {"name": "Dragonhide Armor", "type": "equipment","slot": "armor","base_mods": {"Constitution": 4, "Dexterity": 2}},

    # === Accessories ===
    "ring_of_power":  {"name": "Ring of Power", "type": "equipment","slot": "accessory","base_mods": {"Strength": 2}},
    "ring_of_grace":  {"name": "Ring of Grace","type": "equipment","slot": "accessory","base_mods": {"Dexterity": 2}},
    "amulet_of_vigor":{"name": "Amulet of Vigor","type": "equipment","slot": "accessory","base_mods": {"Constitution": 3}},
    "tome_of_knowledge":{"name": "Tome of Knowledge","type": "equipment","slot": "accessory","base_mods": {"Learning": 3}},
    "cloak_of_shadows":{"name": "Cloak of Shadows","type": "equipment","slot": "accessory","base_mods": {"Dexterity": 2, "Charisma": 1}},
    "talisman_of_warding":{"name": "Talisman of Warding","type": "equipment","slot": "accessory","base_mods": {"Constitution": 2, "Wisdom": 1}},

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
    "poison_flask":      {"name": "Poison Flask",      "type": "utility",    "base_power": 18, "damage_over_time": 8, "duration": 3},
    "stun_bomb":         {"name": "Stun Bomb",         "type": "utility",    "stun_chance": 0.6, "base_power": 12},
    "flash_powder":      {"name": "Flash Powder",      "type": "utility",    "escape_bonus": 12, "blind_enemy": True},
    "throwing_knife":    {"name": "Throwing Knife",    "type": "utility",    "base_power": 22, "armor_pierce": 2},
    "curse_cleansing_scroll": {"name": "Scroll of Cleansing", "type": "consumable", "cure_curse": True},

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
    elif base["type"] == "consumable":
        # Safely use .get() so items without upfront power (like scrolls or armor buffs) don't crash
        item["power"] = int(base.get("base_power", 0) * r["stat_mult"])
        
        # Ensure all unique consumable mechanics carry over into the active item
        for k in ["temp_stat", "duration", "heal_over_time", "defense_buff", "cure_curse"]:
            if k in base:
                item[k] = base[k]
                
    elif base["type"] == "utility":
        item["power"] = int(base.get("base_power", 0) * r["stat_mult"])
        
        # Ensure all unique utility/combat mechanics carry over into the active item
        for k in ["status", "bonus_vs", "escape_bonus", "damage_over_time", "duration", "stun_chance", "blind_enemy", "armor_pierce"]:
            if k in base:
                item[k] = base[k]
                
    elif base["type"] == "scroll":
        item["target_rarity"] = rarity
        
    return item

def random_equipment(rarity=None):
    """Generate a random equipment item (weapon, armor, or accessory)."""
    if rarity is None:
        rarity = random.choices(
            ["common", "uncommon", "rare", "epic", "legendary"],
            weights=[50, 30, 15, 4, 1]
        )[0]
    # Filter equipment items (those with a 'slot' key)
    equip_ids = [item_id for item_id, data in ITEMS.items() if data.get("slot")]
    if not equip_ids:
        # Fallback: create a generic placeholder
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