# facilities/herbalist.py
from utils import advance_time
from inventory import add_item_to_inventory
from city_dialogue import service_dialogue
from resources.items import build_item  # <-- Import the unified builder
from gui.terminal import term

# ── Herbalist stock: (item_id, display_name, cost) ──
_HERBALIST_STOCK = [
    ("healing_potion",      "Healing Potion (55 HP)",                       40),
    ("antidote",            "Antidote (cures poison)",                      30),
    ("ember_draught",       "Ember Draught (40 HP + Fire Resist 2 turns)",  50),
    ("frostward_tonic",     "Frostward Tonic (40 HP + cleanses burn/poison)", 50),
    ("thunderbrew",         "Thunderbrew (30 HP + reduce cooldowns by 1)",  60),
    ("gale_cordial",        "Gale Cordial (35 HP + Initiative 3 turns)",    60),
    ("stoneblood_vial",     "Stoneblood Vial (30 HP + 15% DR 2 turns)",    50),
    ("blessed_water",       "Blessed Water (50 HP + remove curse/debuff)",  65),
    ("shadow_essence",      "Shadow Essence (25 HP + dodge next attack)",   55),
    ("mana_philter",        "Mana Philter (restore random skill cooldown)", 70),
]

def herbalist_service(player, city_id):
    """Herbalist: buy healing potions, antidotes, and elemental draughts."""
    service_dialogue(city_id, "herbalist", "enter")
    term.print("The herbalist displays jars of strange ingredients and bottled essences.")
    
    menu_items = [f"{name} ({cost} gold)" for _, name, cost in _HERBALIST_STOCK]
    menu_items.append("Leave")
    
    choice = term.menu(menu_items, prompt="What catches your eye?")
    
    if choice < 0 or choice >= len(_HERBALIST_STOCK):
        service_dialogue(city_id, "herbalist", "leave")
        term.pause()
        advance_time(player, 30)
        return
    
    item_id, item_name, cost = _HERBALIST_STOCK[choice]
    
    if player.get("gold", 0) < cost:
        term.print("Not enough gold.")
    else:
        player["gold"] -= cost
        # Consumables are always built with rarity="common" — no rarity scaling
        item = build_item(item_id, rarity="common")
        if add_item_to_inventory(player, item):
            term.print(f"You receive {item['name']}.")
            service_dialogue(city_id, "herbalist", "buy")
        else:
            term.print("Your bag is full! Cannot carry the item.")
            player["gold"] += cost  # refund
        
    term.pause()
    advance_time(player, 30)