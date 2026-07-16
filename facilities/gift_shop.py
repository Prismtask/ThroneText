# facilities/gift_shop.py
import random
from utils import advance_time
from inventory import add_item_to_inventory
from city_dialogue import service_dialogue
from gui.terminal import term

GIFT_TYPES = ["flowers", "jewelry", "weapon", "candy", "book"]

ENGAGEMENT_RINGS = [
    ("ruby_engagement_ring", "Ruby Engagement Ring", "Strength", 600),
    ("sapphire_engagement_ring", "Sapphire Engagement Ring", "Wisdom", 600),
    ("emerald_engagement_ring", "Emerald Engagement Ring", "Dexterity", 600),
    ("topaz_engagement_ring", "Topaz Engagement Ring", "Learning", 600),
    ("amethyst_engagement_ring", "Amethyst Engagement Ring", "Charisma", 600),
    ("diamond_engagement_ring", "Diamond Engagement Ring", "Constitution", 600),
]

def _show_engagement_rings(player, city_id):
    term.print("\n=== Engagement Rings ===")
    term.print("A token of commitment. Propose to a girl at 100 affection.")
    term.print("Each ring grants a permanent flat stat bonus while equipped.")
    
    options = [f"{name} (+3 {stat}) — {cost} gold" for (item_id, name, stat, cost) in ENGAGEMENT_RINGS]
    choice = term.menu(options, prompt="Choose a ring:", allow_cancel=True)
    
    if choice < 0:
        return
    
    item_id, name, stat, cost = ENGAGEMENT_RINGS[choice]
    if player.get("gold", 0) < cost:
        term.print("Not enough gold.")
        return

    # Guard: prevent buying duplicate engagement rings
    already_has = any(it.get("id") == item_id for it in player.get("inventory", []))
    for ally in player.get("allies", []):
        if ally.get("equipped", {}).get("accessory", {}).get("id") == item_id:
            already_has = True
            break
    if already_has:
        term.print(f"You already own a {name}. No need for another.")
        term.pause()
        return

    from resources.items import build_item
    item = build_item(item_id, "unique")
    if add_item_to_inventory(player, item):
        player["gold"] -= cost
        term.print(f"You bought the {name}!")
        service_dialogue(city_id, "gift_shop", "success")
    else:
        term.print("Your bag is full! Cannot carry the ring.")


def gift_shop_service(player, city_id):
    service_dialogue(city_id, "gift_shop", "enter")
    term.print("=== GIFT SHOP ===")
    term.print("Special gifts for your companions.\n")

    options = [f"{gtype.title()} (30 gold)" for gtype in GIFT_TYPES]
    options.append("Engagement Rings")
    options.append("Leave")
    
    choice = term.menu(options, prompt="Available Gifts:")
    
    if choice == len(options) - 1 or choice == -1:  # Leave
        service_dialogue(city_id, "gift_shop", "leave")
        advance_time(player, 20)
        return
    if choice == len(options) - 2:  # Engagement Rings
        _show_engagement_rings(player, city_id)
        advance_time(player, 25)
        term.pause()
        return

    if 0 <= choice < len(GIFT_TYPES):
        gift_type = GIFT_TYPES[choice]
        cost = 30

        if player.get("gold", 0) < cost:
            term.print("Not enough gold.")
            advance_time(player, 10)
            return

        player["gold"] -= cost
        gift_item = {
            "name": f"Romantic {gift_type.title()}",
            "type": "gift",
            "gift_type": gift_type,
            "value": 1,
            "count": 1
        }
        if add_item_to_inventory(player, gift_item):
            term.print(f"You bought a {gift_type.title()} gift!")
            service_dialogue(city_id, "gift_shop", "buy")
        else:
            term.print("Your bag is full! Cannot carry the gift.")
            player["gold"] += cost  # refund

    advance_time(player, 25)
    term.pause()