import random
from character import player_max_hp
from resources.items import build_item, ITEMS, ITEM_RARITY

# ── GUI terminal detection (safe import for terminal mode) ──────────
try:
    from gui.terminal import get_terminal as _get_gui_terminal
except ImportError:
    _get_gui_terminal = lambda: None


def _term():
    """Return the GUI Terminal if running in GUI mode, else None."""
    return _get_gui_terminal()


def _tprint(*args, sep=" "):
    """Print to GUI if available, else to terminal."""
    t = _term()
    text = sep.join(str(a) for a in args)
    if t:
        t.print(text)
    else:
        print(text)

RARITY_ORDER = {
    "common": 0,
    "uncommon": 1,
    "rare": 2,
    "epic": 3,
    "legendary": 4,
    "unique": 5,
}

def _items_stackable(a, b):
    """Check if two non-equipment items can stack."""
    if a.get("type") == "equipment" or b.get("type") == "equipment":
        return False
    a_key = a.get("id") or a.get("name")
    b_key = b.get("id") or b.get("name")
    if a_key != b_key:
        return False
    if a.get("rarity") != b.get("rarity"):
        return False
    if a.get("enhance", 0) != b.get("enhance", 0):
        return False
    if a.get("gift_type") != b.get("gift_type"):
        return False
    return True

def _ensure_count(item):
    if "count" not in item:
        item["count"] = 1

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
    # Key items and crafting materials don't take up bag space
    other_count = sum(1 for i in inv if i.get("type") not in ("equipment", "key_item", "crafting_material"))
    return equip_count, other_count

def add_item_to_inventory(player, item):
    """Add item to inventory if there's space. Returns True if added, False if full.
    Key items and crafting materials bypass capacity checks."""
    _ensure_count(item)
    # Key items and crafting materials don't take up bag space — always add
    if item.get("type") in ("key_item", "crafting_material"):
        inv = player.setdefault("inventory", [])
        for existing in inv:
            if _items_stackable(existing, item):
                existing["count"] = existing.get("count", 1) + item["count"]
                return True
        inv.append(item)
        return True
    equip_cap, other_cap = get_inventory_caps(player)
    equip_count, other_count = count_inventory(player)
    if item.get("type") == "equipment":
        if equip_count >= equip_cap:
            return False
        player.setdefault("inventory", []).append(item)
        return True
    else:
        inv = player.setdefault("inventory", [])
        for existing in inv:
            if _items_stackable(existing, item):
                existing["count"] = existing.get("count", 1) + item["count"]
                return True
        if other_count >= other_cap:
            return False
        inv.append(item)
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
    """Return non-equipment, non-key items sorted by rarity descending, then by name."""
    inv = player.get("inventory", [])
    items = [i for i in inv if i.get("type") not in ("equipment", "key_item", "crafting_material")]
    items.sort(key=lambda x: (
        -RARITY_ORDER.get(x.get("rarity", "common"), 0),
        x.get("name", "")
    ))
    return items

def get_key_items(player):
    """Return key items and crafting materials from inventory."""
    inv = player.get("inventory", [])
    key_items = [i for i in inv if i.get("type") in ("key_item", "crafting_material")]
    key_items.sort(key=lambda x: (
        -RARITY_ORDER.get(x.get("rarity", "common"), 0),
        x.get("name", "")
    ))
    return key_items

def remove_item_from_inventory(player, index):
    """Remove item from inventory by index, decrementing count if stacked."""
    inv = player.get("inventory", [])
    if 0 <= index < len(inv):
        item = inv[index]
        count = item.get("count", 1)
        if count > 1:
            item["count"] = count - 1
            return item
        return inv.pop(index)
    return None

def remove_item_by_reference(player, item, amount=1):
    """Remove amount from a specific item stack in inventory. Returns True if successful."""
    inv = player.get("inventory", [])
    for idx, itm in enumerate(inv):
        if itm is item:
            count = itm.get("count", 1)
            if count > amount:
                itm["count"] = count - amount
            else:
                inv.pop(idx)
            return True
    return False

def consume_stackable_items(player, predicate, amount_needed):
    """Consume amount_needed items matching predicate from stacked inventory.
    Returns list of (item_ref, amount_consumed) tuples.
    """
    inv = player.get("inventory", [])
    consumed = []
    remaining = amount_needed
    i = 0
    while i < len(inv) and remaining > 0:
        item = inv[i]
        if predicate(item):
            count = item.get("count", 1)
            if count > remaining:
                item["count"] = count - remaining
                consumed.append((item, remaining))
                remaining = 0
                break
            else:
                consumed.append((item, count))
                remaining -= count
                inv.pop(i)
                continue
        i += 1
    return consumed

def equip_item(player, item, target_slot=None):
    item_slot = item["slot"]
    # Resolve dual accessory slots
    if item_slot == "accessory":
        if target_slot in ("accessory1", "accessory2"):
            pass  # use caller-specified slot
        elif player.get("equipped", {}).get("accessory1") is None:
            target_slot = "accessory1"
        elif player.get("equipped", {}).get("accessory2") is None:
            target_slot = "accessory2"
        else:
            target_slot = "accessory1"
    else:
        target_slot = item_slot
        if target_slot not in player["equipped"]:
            player["equipped"][target_slot] = None

    old = player["equipped"][target_slot]
    if old:
        if not add_item_to_inventory(player, old):
            _tprint(f"Cannot equip {item['name']} — inventory is full. Unequip something first.")
            return False
    player["equipped"][target_slot] = item
    _tprint(f"Equipped {item['name']}.")
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
            _tprint(f"Unequipped {item['name']}.")
            # Recalculate elemental profile
            from combat.elemental import compute_player_elemental
            res, dmg = compute_player_elemental(player)
            player["elemental_res"] = res
            player["elemental_dmg"] = dmg
        else:
            _tprint(f"Cannot unequip {item['name']} — your inventory is full!")
    else:
        _tprint("Nothing equipped in that slot.")

def get_total_equipment_mods(player):
    total = {}
    for slot, item in player.get("equipped", {}).items():
        if item and "mods" in item:
            for stat, val in item["mods"].items():
                total[stat] = total.get(stat, 0) + val
    return total


def is_combat_only_item(item):
    """Return True if this item requires an enemy target and can only be used in combat.
    
    Items like flasks, bombs, and throwing weapons that deal damage or apply
    debuffs to enemies have no valid target outside of combat.
    Escape/flee items are NOT combat-only — they can be used freely.
    """
    if item.get("type") != "utility":
        return False
    # Escape / flee items work without a specific enemy target
    if item.get("escape_bonus") or item.get("fixed_flee"):
        return False
    # Capture nets need a capturable enemy present
    if item.get("capture_net"):
        return True
    # Items that apply debuffs or status effects to an enemy
    if any(k in item for k in ["status", "blind_enemy", "damage_over_time",
                                "poison_damage", "stun_chance", "expose_armor",
                                "burn_tier", "shock_damage"]):
        return True
    # Utility items with damage power (throwing knives, etc.)
    if item.get("power", item.get("base_power", 0)) > 0:
        return True
    return False


def use_consumable(player, item, combat_state=None):
    """Use consumable or utility item.
    
    Returns a message string describing the result.
    Callers should check is_combat_only_item() before calling this
    outside of combat — those items have no valid target.
    """
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
            from combat.stat_milestones import get_dexterity_damage_bonus
            dmg = item["power"] + get_dexterity_damage_bonus(player)
            msg = f"{item['name']} burns the enemy for {dmg} damage!"
            if combat_state:
                combat_state["enemy_hp"] -= dmg
        elif "status" in item:
            if combat_state:
                combat_state["enemy_slowed"] = True
            msg = f"You throw {item['name']}. Enemy is slowed!"
        else:
            from combat.stat_milestones import get_dexterity_damage_bonus
            dmg = item["power"] + get_dexterity_damage_bonus(player)
            if combat_state:
                combat_state["enemy_hp"] -= dmg
            msg = f"You throw {item['name']}, dealing {dmg} damage!"
        return msg

    return "Cannot use that item."

# Rarity tier ordering (lower index = lower rarity)
_RARITY_TIER = ["common", "uncommon", "rare", "epic", "legendary", "unique"]

def apply_scroll_to_item(item, scroll):
    """Apply a rarity scroll to an equipment item. Returns True if success.
    
    Prevents degrading rarity to block the exploit where players
    downgrade an item, enchant it cheaply at low rarity, then upgrade back.
    Unique items cannot be fused with scrolls.
    """
    if item["type"] != "equipment":
        return False
    # Unique items cannot be fused — their essence is immutable
    if item.get("unique"):
        return False
    new_rarity = scroll["target_rarity"]
    old_rarity = item["rarity"]
    if new_rarity == old_rarity:
        return False
    
    # Prevent rarity degradation to close the cheap-enchant exploit
    old_tier = _RARITY_TIER.index(old_rarity) if old_rarity in _RARITY_TIER else -1
    new_tier = _RARITY_TIER.index(new_rarity) if new_rarity in _RARITY_TIER else -1
    if old_tier >= 0 and new_tier >= 0 and new_tier < old_tier:
        return False  # Cannot degrade rarity via scroll fusion
    
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