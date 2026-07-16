# facilities/shipyard.py
from utils import advance_time
from city_dialogue import service_dialogue
from gui.terminal import term

def shipyard_service(player, city_id):
    """Shipyard: buy upgraded vessels and repair hull integrity."""
    service_dialogue(city_id, "shipyard", "enter")
    
    choice = term.menu([
        "Buy Merchant Sloop (500 gold) - Fast travel & unlocks ocean trading",
        "Buy War Frigate (1500 gold) - Safest voyages, immune to pirates",
        "Leave"
    ], prompt="Welcome to the Shipyard! Select a service:")
    
    if choice == 0:
        if player.get("gold", 0) >= 500:
            player["gold"] -= 500
            player["has_ship"] = True
            player["ship_type"] = "sloop"
            term.print("You are now the proud owner of a fast Merchant Sloop!")
            advance_time(player, 30)
        else:
            term.print("The shipwright laughs. 'Come back when you have real gold.'")
            advance_time(player, 15)
    elif choice == 1:
        if player.get("gold", 0) >= 1500:
            player["gold"] -= 1500
            player["has_ship"] = True
            player["ship_type"] = "frigate"
            term.print("You purchase a massive War Frigate. The sea is yours to command!")
            advance_time(player, 30)
        else:
            term.print("The shipwright scoffs. 'You can't even afford a sloop, let alone a frigate!'")
            advance_time(player, 15)
    else:
        service_dialogue(city_id, "shipyard", "leave")
        advance_time(player, 15)

    term.pause()
    advance_time(player, 30)