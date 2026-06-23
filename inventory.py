import random
from character import player_max_hp
from resources.items import build_item, ITEMS, ITEM_RARITY

def add_item_to_inventory(player, item):
    player.setdefault("inventory", []).append(item)

def remove_item_from_inventory(player, index):
    return player["inventory"].pop(index)

def equip_item(player, item):
    slot = item["slot"]
    if slot not in player["equipped"]:
        player["equipped"][slot] = None
    old = player["equipped"][slot]
    player["equipped"][slot] = item
    if old:
        add_item_to_inventory(player, old)
    print(f"Equipped {item['name']}.")
    # Recalculate elemental profile
    from combat.elemental import compute_player_elemental
    res, dmg = compute_player_elemental(player)
    player["elemental_res"] = res
    player["elemental_dmg"] = dmg


def unequip_slot(player, slot):
    if slot in player["equipped"] and player["equipped"][slot]:
        item = player["equipped"][slot]
        player["equipped"][slot] = None
        add_item_to_inventory(player, item)
        print(f"Unequipped {item['name']}.")
        # Recalculate elemental profile
        from combat.elemental import compute_player_elemental
        res, dmg = compute_player_elemental(player)
        player["elemental_res"] = res
        player["elemental_dmg"] = dmg
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
            heal = item["power"]
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