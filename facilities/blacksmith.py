# facilities/blacksmith.py
import random
from resources.items import (
    ITEM_RARITY, ITEMS, fusion_fee, reforge_cost, build_item, enhance_cap_for,
    compute_equipment_mods, compute_elemental_dmg, compute_elemental_res,
)
from resources.dialogues import BLACKSMITH_DIALOGUES
from inventory import apply_scroll_to_item, remove_item_by_reference, add_item_to_inventory
from utils import advance_time, display_name
from gui.terminal import term
from gui.theme import Theme
from facilities.shop import get_discounted_price

# Unique gear enhancement price multiplier — premium over legendary (8.0)
# because uniques bypass the rarity stat_mult system entirely (see
# resources/items.py _build_unique_item).
UNIQUE_ENHANCE_PRICE_MULT = 12.0


def blacksmith_greeting(dialogues):
    term.print(random.choice(dialogues["greeting"]))

def blacksmith_farewell(dialogues):
    term.print(random.choice(dialogues["farewell"]))

def _rarity_style(item):
    """Return a button style dict for the given item based on its rarity."""
    rarity = item.get("rarity", "common")
    color = Theme.RARITY_COLORS.get(rarity, Theme.BUTTON_FG)
    darker = _darken_color(color)
    return {"fg": color, "active_fg": color, "bg": darker, "active_bg": darker}


def _darken_color(hex_color):
    """Darken a hex color slightly for button background."""
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    r, g, b = max(0, r - 60), max(0, g - 60), max(0, b - 60)
    return f"#{r:02x}{g:02x}{b:02x}"


def enhance_item(player, dialogues, city_id):
    # 1. Build a unified pool of items tracking where they live
    enhanceable_pool = []
    
    # Add player's equipped items first (Weapon, Armor, Accessories)
    equipped_slots = ["weapon", "armor", "accessory1", "accessory2",
                      "accessory3"]
    for slot in equipped_slots:
        equipped_item = player.get("equipped", {}).get(slot)
        if equipped_item:
            enhanceable_pool.append((True, "Player", equipped_item))
            
    # Add ally equipped items
    for ally in player.get("allies", []):
        for slot in equipped_slots:
            equipped_item = ally.get("equipped", {}).get(slot)
            if equipped_item:
                enhanceable_pool.append((True, display_name(ally), equipped_item))
            
    # Add unequipped equipment from inventory
    inv = player.get("inventory", [])
    for idx, item in enumerate(inv):
        if item.get("type") == "equipment":
            enhanceable_pool.append((False, None, item))
            
    if not enhanceable_pool:
        term.print(dialogues["no_equipment"])
        term.pause()
        return
        
    term.print("\n--- Enhance Equipment ---")
    options = []
    styles = []
    for i, (is_equipped, owner_name, item) in enumerate(enhanceable_pool):
        tag = f" (Equipped by {owner_name})" if is_equipped else ""
        # No numbered list: term.menu shows these as buttons below.
        options.append(f"{item['name']}{tag} (+{item.get('enhance', 0)})")
        styles.append(_rarity_style(item))
        
    choice = term.menu(options, prompt="Choose item to enhance:", allow_cancel=True, styles=styles)
    if choice < 0:
        return
            
    is_equipped, owner_name, item = enhanceable_pool[choice]
    
    current_enhance = item.get("enhance", 0)
    enhance_cap = enhance_cap_for(item)
    if current_enhance >= enhance_cap:
        term.print(dialogues["max_enhance"])
        term.pause()
        return

    # Unique items keep their own +5 cap (handled above by enhance_cap_for).
    new_enhance = current_enhance + 1
    rarity_mult = ITEM_RARITY[item["rarity"]]["price_mult"]

    # Unique gear is prestige smithing. Historically it fell through to the
    # common price_mult (1.0) and could be pushed to its +5 cap at bargain
    # prices — nonsense for the best items in the game and, since the Black
    # Silence Gloves now scale with their enhance level, an exploit too.
    # Charge a premium above legendary (8.0) instead.
    if item.get("unique"):
        rarity_mult = max(rarity_mult, UNIQUE_ENHANCE_PRICE_MULT)
    
    # Exponential cost scaling by enchant level: each +1 costs ~1.5× more than the last.
    # This closes the exploit where players could degrade rarity, enchant cheaply,
    # then upgrade rarity back — high-enchant items are always expensive regardless.
    base_cost = int(50 * rarity_mult * (1.5 ** new_enhance))
    cost = get_discounted_price(base_cost, player, city_id)
    term.print(f"Enhance to +{new_enhance} costs {cost} gold (Discounts applied).")

    if not term.confirm("Proceed?"):
        return
        
    if player.get("gold", 0) < cost:
        term.print(dialogues["not_enough_gold"])
        term.pause()
        return
            
    player["gold"] -= cost
    item["enhance"] = new_enhance

    # Enhancement is multiplicative with rarity (economy Option A) and adds
    # elemental damage per step for weapons (compositional D-C). Unique items
    # keep their hand-tuned additive progression (+5 compensation).
    base_def = ITEMS.get(item.get("id"))
    if item.get("unique"):
        if "mods" in item:
            for stat in item["mods"]:
                item["mods"][stat] += 1
    elif base_def and base_def.get("base_mods") and item.get("rarity") in ITEM_RARITY:
        if base_def.get("base_form"):
            # Preserve flower infusions: enhancement is stats-only.
            from resources.item_generation import refresh_infused_instance
            refresh_infused_instance(item, base_def)
        else:
            item["mods"] = compute_equipment_mods(base_def, item["rarity"], new_enhance)
            if "elemental_dmg" in base_def:
                item["elemental_dmg"] = compute_elemental_dmg(base_def, item["rarity"], new_enhance)
            if "elemental_res" in base_def:
                item["elemental_res"] = compute_elemental_res(base_def, item["rarity"], new_enhance)
    elif "mods" in item:
        for stat in item["mods"]:
            item["mods"][stat] += 1
            
    base_display_name = item["name"].split(" +")[0]
    item["name"] = f"{base_display_name} +{new_enhance}"
    
    term.print(dialogues["enhance_success"].format(item['name']))
        
    term.pause()

def fuse_scroll_with_item(player, dialogues, city_id):
    # Enforce standard item filtration matching index integrity updates
    inv = player.get("inventory", [])
    scrolls = [(idx, itm) for idx, itm in enumerate(inv) if itm["type"] == "scroll"]
    if not scrolls:
        term.print(dialogues["no_scrolls"])
        term.pause()
        return
    term.print("\n--- Available Scrolls ---")
    scroll_options = []
    for i, (idx, s) in enumerate(scrolls):
        scroll_options.append(f"{s['name']} (Target: {s.get('target_rarity','any')})")
    
    choice = term.menu(scroll_options, prompt="Choose scroll:", allow_cancel=True)
    if choice < 0:
        return
    scroll_idx, scroll = scrolls[choice]
    
    # Build combined pool of weapon slots for fusion targets
    enhanceable_pool = []
    equipped_slots = ["weapon", "armor", "accessory1", "accessory2",
                      "accessory3"]
    for slot in equipped_slots:
        equipped_item = player.get("equipped", {}).get(slot)
        if equipped_item:
            enhanceable_pool.append((True, "Player", equipped_item))
    for ally in player.get("allies", []):
        for slot in equipped_slots:
            equipped_item = ally.get("equipped", {}).get(slot)
            if equipped_item:
                enhanceable_pool.append((True, display_name(ally), equipped_item))
    for idx, item in enumerate(inv):
        if item.get("type") == "equipment":
            enhanceable_pool.append((False, None, item))
            
    if not enhanceable_pool:
        term.print(dialogues["no_equipment"])
        term.pause()
        return
        
    term.print("\n--- Choose Equipment for Scroll Fusion ---")
    eq_options = []
    eq_styles = []
    for i, (is_equipped, owner_name, item) in enumerate(enhanceable_pool):
        tag = f" (Equipped by {owner_name})" if is_equipped else ""
        eq_options.append(f"{item['name']}{tag}")
        eq_styles.append(_rarity_style(item))
        
    choice_eq = term.menu(eq_options, prompt="Choose equipment:", allow_cancel=True, styles=eq_styles)
    if choice_eq < 0:
        return
    is_equipped, owner_name, eq_item = enhanceable_pool[choice_eq]

    # Pay for the value being added (economy §3.6): cheap junk hops,
    # expensive legendary hops; enhance investment is inside the delta.
    base_cost = fusion_fee(eq_item, scroll["target_rarity"])
    cost = get_discounted_price(base_cost, player, city_id)
    term.print(f"Fusing {scroll['name']} into {eq_item['name']} costs {cost} gold.")

    if not term.confirm("Proceed?"):
        return

    if player.get("gold", 0) < cost:
        term.print(dialogues["not_enough_gold"])
        term.pause()
        return
        
    if apply_scroll_to_item(eq_item, scroll):
        player["gold"] -= cost
        # Extract scroll instance safely from total inventory tracking list
        remove_item_by_reference(player, scroll)
        term.print(dialogues["fusion_success"].format(eq_item['name'], scroll['target_rarity']))
    else:
        term.print(dialogues["fusion_failed"])
    term.pause()

# ── Flower infusion (docs/rarity_grade_flower_audit.md §12) ──────────────────
# Grade/tempering are retired. Same-element infusions upgrade a slot; a new
# distinct element fills the next empty slot (or replaces the third). Weapons
# hold three damage elements; armor/accessories hold up to three resistance
# elements, each with its own three-tier track.

COMMISSION = {"flowers": 1, "gold": 600}


def _count_item_id(player, item_id):
    return sum(int(it.get("count", 1))
               for it in player.get("inventory", []) if it.get("id") == item_id)


# Flower transmutation (2026-10-19): 3:1 exchange so an element-locked
# farming streak can never strand a build. All flower services live here.
TRANSMUTE_RATIO = 3


def transmute_flower(player, src_element, dst_element, ratio=TRANSMUTE_RATIO):
    """Move ``ratio`` source flowers into one destination flower (no UI).

    Returns True when the exchange happened. Same-element exchanges are
    refused. Element ids come from ``item_generation.FLOWER_ITEMS``.
    """
    from resources.item_generation import flower_for_element
    from inventory import consume_stackable_items

    src_id = flower_for_element(src_element)
    dst_id = flower_for_element(dst_element)
    if not src_id or not dst_id or src_id == dst_id:
        return False
    if _count_item_id(player, src_id) < ratio:
        return False
    consume_stackable_items(player, lambda it: it.get("id") == src_id, ratio)
    add_item_to_inventory(player, build_item(dst_id, "common"))
    return True


def _infusable(item):
    """True when an instance accepts flower essences.

    Base forms use the full three-slot track. Uniques accept flowers into
    their two open slots — their authored primary element is locked.
    """
    if not isinstance(item, dict) or item.get("type") != "equipment":
        return False
    base = ITEMS.get(item.get("id"), {})
    if item.get("unique") or base.get("unique"):
        # Elementless flavour uniques can still receive a first flower, which
        # claims their primary slot.
        return True
    return bool(base.get("base_form"))


def _infusable_pool(player, require_infusions=False):
    """Collect infusable items as (kind, owner, where, item) tuples."""
    pool = []
    slots = ["weapon", "armor", "accessory1", "accessory2", "accessory3"]
    for slot in slots:
        item = player.get("equipped", {}).get(slot)
        if _infusable(item) and (not require_infusions or item.get("infusions")):
            pool.append(("equipped", player, slot, item))
    for ally in player.get("allies", []):
        for slot in slots:
            item = ally.get("equipped", {}).get(slot)
            if _infusable(item) and (not require_infusions or item.get("infusions")):
                pool.append(("equipped", ally, slot, item))
    for idx, item in enumerate(player.get("inventory", [])):
        if _infusable(item) and (not require_infusions or item.get("infusions")):
            pool.append(("inventory", player, idx, item))
    return pool


def _res_slot_value(infusion, slot):
    """Resistance multiplier one armor/accessory infusion slot contributes.

    Armor and accessories list the value their slot adds (×1.05 … ×1.35)
    rather than a tier number, so each of the three elements reads as its
    own effect — the item name only reflects the first slot.
    """
    from resources.item_generation import (
        ACCESSORY_RES_PRIMARY_TIERS, ARMOR_RES_PRIMARY_TIERS,
    )
    tier = max(0, min(2, int(infusion.get("tier", 0))))
    ladder = (ACCESSORY_RES_PRIMARY_TIERS if slot == "accessory"
              else ARMOR_RES_PRIMARY_TIERS)
    return ladder[tier]


def _infusion_slot_text(item, infusion):
    """Readable effect of one flower slot (damage and/or resistance)."""
    parts = []
    if infusion.get("value") is not None:
        parts.append(f"{float(infusion['value']):.2f} damage")
    if infusion.get("tier") is not None:
        parts.append(f"×{_res_slot_value(infusion, item.get('slot')):.2f} resistance")
    return " · ".join(parts) or "effect"


def _infusion_summary(item):
    infusions = item.get("infusions") or []
    primary = item.get("primary_element") if item.get("unique") else None
    if not infusions and not primary:
        return "no element"
    parts = []
    if primary:
        parts.append(f"{primary.title()} (primary)")
    parts.extend(
        f"{inf['element'].title()} — {_infusion_slot_text(item, inf)}"
        for inf in infusions
    )
    return " / ".join(parts)


def infuse_item(player, dialogues, city_id):
    """Apply one flower infusion to a chosen piece of equipment."""
    from resources.item_generation import FLOWER_ITEMS, apply_infusion, flower_for_element
    from inventory import consume_stackable_items

    pool = []
    slots = ["weapon", "armor", "accessory1", "accessory2", "accessory3"]
    for slot in slots:
        item = player.get("equipped", {}).get(slot)
        if _infusable(item):
            pool.append(("equipped", player, slot, item))
    for ally in player.get("allies", []):
        for slot in slots:
            item = ally.get("equipped", {}).get(slot)
            if _infusable(item):
                pool.append(("equipped", ally, slot, item))
    for idx, item in enumerate(player.get("inventory", [])):
        if _infusable(item):
            pool.append(("inventory", player, idx, item))

    if not pool:
        term.print("\n--- Infuse Element ---")
        term.print("Nothing here can take an infusion. Base-form gear accepts three")
        term.print("flower slots; unique equipment accepts flowers into its two open")
        term.print("slots, with its primary element locked.")
        term.pause()
        return

    term.print("\n--- Infuse Element (Flower Essence) ---")
    term.print("A weapon holds up to three elements (primary 1.48 / secondary 1.20 /")
    term.print("tertiary 1.15). Armor and accessories hold up to three resistance")
    term.print("elements (three tiers each); each element shows the resistance × it")
    term.print("adds. Same flower upgrades its slot; a new flower fills the next")
    term.print("slot or replaces the third.")
    term.print("Uniques keep one fixed primary element (the first flower picks it")
    term.print("when the piece has none); later flowers extend whichever profile")
    term.print("the piece already carries (damage and/or resistance).")
    options = []
    styles = []
    for kind, owner, where, item in pool:
        where_tag = ""
        if kind == "equipped":
            where_tag = f" (equipped: {display_name(owner) if owner is not player else 'you'})"
        options.append(f"{item['name']}{where_tag} — {_infusion_summary(item)}")
        styles.append(_rarity_style(item))
        term.print(f"{len(options)}. {options[-1]}")

    choice = term.menu(options, prompt="Choose equipment:", allow_cancel=True, styles=styles)
    if choice < 0:
        return
    kind, owner, where, item = pool[choice]
    base_def = ITEMS.get(item.get("id"), {})

    elements = list(FLOWER_ITEMS)
    labels = []
    for element in elements:
        flower_id = flower_for_element(element)
        name = ITEMS.get(flower_id, {}).get("name", element)
        labels.append(f"{element.title()} — {name} (you have {_count_item_id(player, flower_id)}×)")
    el_choice = term.menu(labels, prompt="Choose the flower:", allow_cancel=True)
    if el_choice < 0:
        return
    element = elements[el_choice]
    flower_id = flower_for_element(element)
    if _count_item_id(player, flower_id) < 1:
        term.print(f"You have no {ITEMS.get(flower_id, {}).get('name', 'flower')} — "
                   f"harvest more from dungeon drops and treasure rooms.")
        term.pause()
        return

    ok, reason = apply_infusion(item, element, base_def)
    if not ok:
        term.print(f"That element cannot be strengthened further ({reason}).")
        term.pause()
        return

    # Equipped gear feeds the actor's cached elemental profile; an infusion
    # changes resistance/damage immediately, so rebuild it now instead of
    # waiting for the next equip/load.
    if kind == "equipped":
        from combat.elemental import compute_ally_elemental, compute_player_elemental
        if owner is player:
            res, dmg = compute_player_elemental(player)
        else:
            res, dmg = compute_ally_elemental(owner)
        owner["elemental_res"] = res
        owner["elemental_dmg"] = dmg

    consume_stackable_items(player, lambda it: it.get("id") == flower_id, 1)
    term.print(f"\nThe smith works the flower into the metal. The piece is now "
               f"{item['name']}!")
    term.pause()


def reforge_item(player, dialogues, city_id):
    """Re-roll one elemental infusion slot with a keep-or-replace choice.

    The fee is paid before the roll (docs/gold_economy_pacing_design.md D2),
    so a bad result still costs gold; keeping the old element does not refund.
    """
    from resources.item_generation import (
        roll_reforge_element, apply_reforge_element,
    )

    pool = _infusable_pool(player, require_infusions=True)
    if not pool:
        term.print("\n--- Reforge Element ---")
        term.print("Nothing here has an infusion to re-roll. Use 'Infuse Element'")
        term.print("first; a unique's primary element stays locked and cannot be")
        term.print("reforged, but its flower slots can.")
        term.pause()
        return

    term.print("\n--- Reforge Element (Re-roll) ---")
    term.print("The smith re-works one flower slot into another element, keeping")
    term.print("its damage value and/or resistance tier. The fee is paid whether")
    term.print("you keep the old element or accept the new one.")

    options = []
    styles = []
    for kind, owner, where, item in pool:
        where_tag = ""
        if kind == "equipped":
            where_tag = f" (equipped: {display_name(owner) if owner is not player else 'you'})"
        options.append(f"{item['name']}{where_tag} — {_infusion_summary(item)}")
        styles.append(_rarity_style(item))
        term.print(f"{len(options)}. {options[-1]}")

    choice = term.menu(options, prompt="Choose equipment:", allow_cancel=True, styles=styles)
    if choice < 0:
        return
    kind, owner, where, item = pool[choice]
    base_def = ITEMS.get(item.get("id"), {})
    if not base_def or not (base_def.get("base_form") or base_def.get("unique")):
        term.print("The smith cannot read that piece's form.")
        term.pause()
        return

    infusions = item.get("infusions") or []
    slot_labels = []
    for idx, inf in enumerate(infusions):
        slot_labels.append(f"{idx + 1}. {inf['element'].title()} — "
                           f"{_infusion_slot_text(item, inf)}")
    if len(slot_labels) > 1:
        slot_choice = term.menu(slot_labels, prompt="Which infusion slot?",
                                allow_cancel=True)
        if slot_choice < 0:
            return
        slot_index = slot_choice
    else:
        slot_index = 0

    current_element = infusions[slot_index].get("element")
    cost = get_discounted_price(reforge_cost(item), player, city_id)
    term.print(f"\nRe-forging {item['name']} costs {cost} gold (discounts applied).")
    if player.get("gold", 0) < cost:
        term.print(dialogues["not_enough_gold"])
        term.pause()
        return
    if not term.confirm("Pay the fee?"):
        return

    player["gold"] = player.get("gold", 0) - cost
    new_element = roll_reforge_element(item, slot_index)
    if new_element is None:
        player["gold"] += cost
        term.print("No other element is available for that slot. Your gold is returned.")
        term.pause()
        return

    term.print(f"\nThe smith quenches the metal: {current_element.title()} → "
               f"{new_element.title()}.")
    if not term.confirm(f"Replace {current_element.title()} with {new_element.title()}?"):
        term.print("You keep the current infusion. The fee is spent.")
        term.pause()
        return

    if not apply_reforge_element(item, base_def, slot_index, new_element):
        term.print("The reforge fails — the old infusion remains.")
        term.pause()
        return

    if kind == "equipped":
        from combat.elemental import compute_ally_elemental, compute_player_elemental
        if owner is player:
            res, dmg = compute_player_elemental(player)
        else:
            res, dmg = compute_ally_elemental(owner)
        owner["elemental_res"] = res
        owner["elemental_dmg"] = dmg

    term.print(f"The piece is now {item['name']}!")
    term.pause()


def _form_labels_by_slot():
    """Map slot -> [(form_key, noun)] from the grid form definitions."""
    from resources.item_generation import WEAPON_FORMS, ARMOR_FORMS, ACCESSORY_FORMS
    return {
        "weapon": [(f["key"], f["noun"]) for f in WEAPON_FORMS],
        "armor": [(f["key"], f["noun"]) for f in ARMOR_FORMS],
        "accessory": [(f["key"], f["noun"]) for f in ACCESSORY_FORMS],
    }


_COMMISSION_FAMILIES = [("weapon", "Weapon"), ("armor", "Armor"), ("accessory", "Accessory")]


def commission_item(player, dialogues, city_id):
    """Forge a common base-form item with its first infusion (audit P7).

    Flowers select the element; gold pays for the smith's work. Rarity is
    deliberately not included — that stays drop/scroll territory so loot
    keeps its value.
    """
    from resources.item_generation import FLOWER_ITEMS, apply_infusion, flower_for_element
    from inventory import consume_stackable_items, get_inventory_caps, count_inventory

    term.print("\n--- Forge Commission (Order a Base) ---")
    term.print("The smith forges a plain (common) piece in the form you choose")
    term.print("and works in one flower of the element you pick.")
    term.print("Rarity is not included — find or scroll that.")

    fam_choice = term.menu([label for _slot, label in _COMMISSION_FAMILIES],
                           prompt="What kind of piece?", allow_cancel=True)
    if fam_choice < 0:
        return None
    slot = _COMMISSION_FAMILIES[fam_choice][0]

    forms = _form_labels_by_slot()[slot]
    form_choice = term.menu([noun for _key, noun in forms],
                            prompt="Choose a form:", allow_cancel=True)
    if form_choice < 0:
        return None
    form_key = forms[form_choice][0]

    elements = list(FLOWER_ITEMS)
    el_choice = term.menu([el.title() for el in elements],
                          prompt="Choose an element:", allow_cancel=True)
    if el_choice < 0:
        return None
    element = elements[el_choice]

    if form_key not in ITEMS or not ITEMS[form_key].get("base_form"):
        term.print("The smith cannot forge that combination.")
        term.pause()
        return None

    flower_id = flower_for_element(element)
    flower_name = ITEMS.get(flower_id, {}).get("name", "flower")
    have = _count_item_id(player, flower_id)
    cost = get_discounted_price(COMMISSION["gold"], player, city_id)
    term.print(f"\n1× {flower_name} + {cost} gold "
               f"(you have {have}×, {player.get('gold', 0)} gold).")
    if have < COMMISSION["flowers"]:
        term.print(f"Not enough {flower_name} — harvest more from dungeon drops "
                   f"and treasure rooms.")
        term.pause()
        return None
    if player.get("gold", 0) < cost:
        term.print(dialogues["not_enough_gold"])
        term.pause()
        return None

    equip_cap, _other_cap = get_inventory_caps(player)
    equip_count, _other_count = count_inventory(player)
    if equip_count >= equip_cap:
        term.print("Your equipment bag is full.")
        term.pause()
        return None

    if not term.confirm("Proceed?"):
        return None

    consume_stackable_items(player, lambda it: it.get("id") == flower_id,
                            COMMISSION["flowers"])
    player["gold"] -= cost
    item = build_item(form_key, "common")
    apply_infusion(item, element, ITEMS[form_key])
    add_item_to_inventory(player, item)
    term.print(f"\nThe smith hammers out a {item['name']}!")
    term.pause()
    return item


def transmute_flowers(player, dialogues, city_id):
    """3:1 flower exchange menu (blacksmith)."""
    from resources.item_generation import FLOWER_ITEMS

    term.print("\n--- Transmute Flowers (3:1) ---")
    term.print("The smith grinds three blooms of one element into a single")
    term.print("bloom of another. No coin is taken for the work.")

    available = [el for el, fid in FLOWER_ITEMS.items()
                 if _count_item_id(player, fid) >= TRANSMUTE_RATIO]
    if not available:
        term.print(f"You need at least {TRANSMUTE_RATIO} flowers of one element.")
        term.pause()
        return

    src_labels = []
    for element in available:
        fid = FLOWER_ITEMS[element]
        name = ITEMS.get(fid, {}).get("name", fid)
        src_labels.append(f"{name} ×{_count_item_id(player, fid)}")
    src_choice = term.menu(src_labels, prompt="Transmute which flower?", allow_cancel=True)
    if src_choice < 0:
        return
    src_element = available[src_choice]

    targets = [el for el in FLOWER_ITEMS if el != src_element]
    dst_choice = term.menu([el.title() for el in targets],
                           prompt="Into which element?", allow_cancel=True)
    if dst_choice < 0:
        return
    dst_element = targets[dst_choice]

    src_name = ITEMS.get(FLOWER_ITEMS[src_element], {}).get("name", src_element)
    dst_name = ITEMS.get(FLOWER_ITEMS[dst_element], {}).get("name", dst_element)
    if not term.confirm(f"Consume {TRANSMUTE_RATIO}× {src_name} for 1× {dst_name}?"):
        return
    if transmute_flower(player, src_element, dst_element):
        term.print(f"\nThe {src_name}s crumble into essence — a fresh {dst_name} remains.")
    else:
        term.print("\nThe exchange fails — the flowers are not there.")
    term.pause()


def blacksmith_menu(player, city_id="solmere"):
    from karma_dialogue import service_line
    dialogues = BLACKSMITH_DIALOGUES.get(city_id, BLACKSMITH_DIALOGUES["solmere"])
    while True:
        term.clear()
        blacksmith_greeting(dialogues)
        smith_line = service_line(player, "blacksmith", city_id)
        if smith_line:
            term.print(f'  "{smith_line}"')
        term.print("=== BLACKSMITH FORGE === ")
        term.print(f"Gold: {player.get('gold', 0)}")
        
        choice = term.menu([
            "Enhance Equipment",
            "Infuse Element (Flower Essence)",
            "Reforge Element (Re-roll)",
            "Commission (Order a Base)",
            "Transmute Flowers (3:1)",
            "Fuse (Scroll + Equipment)",
            "Leave"
        ], prompt="What would you like to forge?")
        
        if choice == 0:
            enhance_item(player, dialogues, city_id)
            advance_time(player, 30)
        elif choice == 1:
            infuse_item(player, dialogues, city_id)
            advance_time(player, 30)
        elif choice == 2:
            reforge_item(player, dialogues, city_id)
            advance_time(player, 30)
        elif choice == 3:
            commission_item(player, dialogues, city_id)
            advance_time(player, 30)
        elif choice == 4:
            transmute_flowers(player, dialogues, city_id)
            advance_time(player, 30)
        elif choice == 5:
            fuse_scroll_with_item(player, dialogues, city_id)
            advance_time(player, 30)
        elif choice == 6 or choice == -1:
            blacksmith_farewell(dialogues)
            advance_time(player, 15)
            break
        else:
            term.print("Invalid Choice.")
            advance_time(player, 10)
            term.pause()