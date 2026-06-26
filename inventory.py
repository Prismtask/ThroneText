import random
from character import player_max_hp
from resources.items import build_item, ITEMS, ITEM_RARITY

RARITY_ORDER = {
    "common": 0,
    "uncommon": 1,
    "rare": 2,
    "epic": 3,
    "legendary": 4,
}

def get_inventory_caps(player):
    """Return (equipment_cap, other_cap) based on upgrades and allies."""
    upgrade = player.get("inventory_upgrade", 0)
    ally_count = len(player.get("allies", []))
    equip_cap = 10 + upgrade * 5
    other_cap = 20 + upgrade * 10 + ally_count * 5
    return equip_cap, other_cap

def count_inventory(player):
    inv = player.get("inventory", [])
    equip_count = sum(1 for i in inv if i.get("type") == "equipment")
    other_count = sum(1 for i in inv if i.get("type") != "equipment")
    return equip_count, other_count

def add_item_to_inventory(player, item):
    """Add item to inventory if there's space. Returns True if added, False if full."""
    equip_cap, other_cap = get_inventory_caps(player)
    equip_count, other_count = count_inventory(player)
    if item.get("type") == "equipment":
        if equip_count >= equip_cap:
            return False
    else:
        if other_count >= other_cap:
            return False
    player.setdefault("inventory", []).append(item)
    return True

def get_sorted_equipment(player):
    """Return inventory equipment sorted by slot then rarity descending."""
    inv = player.get("inventory", [])
    slot_order = {"weapon": 0, "armor": 1, "accessory": 2}
    equip = [i for i in inv if i.get("type") == "equipment"]
    equip.sort(key=lambda x: (
        slot_order.get(x.get("slot", ""), 99),
        -RARITY_ORDER.get(x.get("rarity", "common"), 0)
    ))
    return equip

def get_sorted_items(player):
    """Return non-equipment items sorted by rarity descending, then by name."""
    inv = player.get("inventory", [])
    items = [i for i in inv if i.get("type") != "equipment"]
    items.sort(key=lambda x: (
        -RARITY_ORDER.get(x.get("rarity", "common"), 0),
        x.get("name", "")
    ))
    return items

def remove_item_from_inventory(player, index):
    return player["inventory"].pop(index)

def equip_item(player, item):
    slot = item["slot"]
    if slot not in player["equipped"]:
        player["equipped"][slot] = None
    old = player["equipped"][slot]
    if old:
        if not add_item_to_inventory(player, old):
            print(f"Cannot equip {item['name']} — inventory is full. Unequip something first.")
            return False
    player["equipped"][slot] = item
    print(f"Equipped {item['name']}.")
    # Recalculate elemental profile
    from combat.elemental import compute_player_elemental
    res, dmg = compute_player_elemental(player)
    player["elemental_res"] = res
    player["elemental_dmg"] = dmg
    return True


def unequip_slot(player, slot):
    if slot in player["equipped"] and player["equipped"][slot]:
        item = player["equipped"][slot]
        if add_item_to_inventory(player, item):
            player["equipped"][slot] = None
            print(f"Unequipped {item['name']}.")
            # Recalculate elemental profile
            from combat.elemental import compute_player_elemental
            res, dmg = compute_player_elemental(player)
            player["elemental_res"] = res
            player["elemental_dmg"] = dmg
        else:
            print(f"Cannot unequip {item['name']} — your inventory is full!")
    else:
        print("Nothing equipped in that slot.")

def get_total_equipment_mods(player):
    total = {}
    for slot, item in player.get("equipped", {}).items():
        if item and "mods" in item:
            for stat, val in item["mods"].items():
                total[stat] = total.get(stat, 0) + val
    return total


def use_consumable(player, item, combat_state=None):
    """Use consumable or utility item."""
    if item["type"] == "consumable":
        if "temp_stat" in item:
            duration = item.get("duration", 3)
            stat = item["temp_stat"]
            power = item["power"]
            player.setdefault("active_buffs", []).append({
                "stat": stat,
                "value": power,
                "remaining": duration
            })
            msg = f"You drink {item['name']}. +{power} {stat} for {duration} turns."
        else:
            from combat.stat_milestones import get_wisdom_bonus
            heal = item["power"] + get_wisdom_bonus(player)
            max_hp = player_max_hp(player)
            old_hp = player["current_hp"]
            player["current_hp"] = min(old_hp + heal, max_hp)
            msg = f"You use {item['name']}. Healed {player['current_hp'] - old_hp} HP."
        return msg

    elif item["type"] == "utility":
        if "escape_bonus" in item:
            if combat_state:
                combat_state["forced_flee"] = True
            msg = f"You throw a {item['name']} and disappear in smoke!"
        elif "bonus_vs" in item and combat_state and combat_state.get("enemy_race") == item["bonus_vs"]:
            dmg = item["power"]
            msg = f"{item['name']} burns the enemy for {dmg} damage!"
            if combat_state:
                combat_state["enemy_hp"] -= dmg
        elif "status" in item:
            if combat_state:
                combat_state["enemy_slowed"] = True
            msg = f"You throw {item['name']}. Enemy is slowed!"
        else:
            dmg = item["power"]
            if combat_state:
                combat_state["enemy_hp"] -= dmg
            msg = f"You throw {item['name']}, dealing {dmg} damage!"
        return msg

    return "Cannot use that item."

def apply_scroll_to_item(item, scroll):
    """Apply a rarity scroll to an equipment item. Returns True if success."""
    if item["type"] != "equipment":
        return False
    new_rarity = scroll["target_rarity"]
    old_rarity = item["rarity"]
    if new_rarity == old_rarity:
        return False
    
    # Rebuild the item with new rarity, same enhance
    item["rarity"] = new_rarity
    base = ITEMS[item["id"]]
    r = ITEM_RARITY[new_rarity]
    enhance = item.get("enhance", 0)
    item["mods"] = {
        stat: int(val * r["stat_mult"]) + enhance
        for stat, val in base["base_mods"].items()
    }
    # Update name
    item["name"] = f"{new_rarity.title()} {base['name']}"
    if enhance > 0:
        item["name"] += f" +{enhance}"
    return True