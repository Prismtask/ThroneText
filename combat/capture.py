# combat/capture.py
import random
from resources.items import ITEM_RARITY
from combat.stats import get_effective_attribute
from resources.enemies import MONSTER_GIRL_MESSAGES

def is_monster_girl(enemy):
    """Check the explicit monster_girl flag set in monster_girls.yaml."""
    return bool(enemy.get("monster_girl"))


def get_capture_message(enemy, player):
    """Personalized capture message from monster_girls.yaml."""
    key = enemy.get("key")
    
    # Try to load from monster_girls.yaml capture_messages section
    try:
        if key in MONSTER_GIRL_MESSAGES:
            template = MONSTER_GIRL_MESSAGES[key]
            return template.format(
                name=enemy.get("name", "the girl"),
                player=player.get("name", "Adventurer")
            )
    except ImportError:
        pass

    # Fallback
    return f"{enemy.get('name', 'The creature')} is captured and gently bound by your net!"


def attempt_capture(player, target):
    """Main capture logic using the monster_girl flag."""
    if not is_monster_girl(target):
        print("This enemy cannot be captured.")
        return False

    # Find capture net
    net_idx = None
    net = None
    for i, item in enumerate(player.get("inventory", [])):
        if item.get("capture_net"):
            net_idx = i
            net = item
            break

    if not net:
        print("You need a Capture Net to attempt this!")
        return False

    # Success calculation
    cha = get_effective_attribute(player, "Charisma")
    dex = get_effective_attribute(player, "Dexterity")
    rarity_mult = ITEM_RARITY.get(net.get("rarity", "common"))["stat_mult"]

    hp_percent = target["hp"] / target.get("max_hp", target["hp"] or 1)
    difficulty = target.get("level", 1) * 1.2 + (1 - hp_percent) * 40

    roll = (cha + dex) * 0.8 + (rarity_mult * 25) - difficulty
    success_chance = max(5, min(95, roll))

    # Consume net
    player["inventory"].pop(net_idx)

    if random.uniform(0, 100) < success_chance:
        print("\n" + "✨" * 20)
        print(get_capture_message(target, player))
        print("✨" * 20)

        store_captured_girl(player, target)
        return True
    else:
        print(f"The {target.get('name')} slips through your net and escapes!")
        return False


def store_captured_girl(player, mg):
    """Store captured monster girl in house storage."""
    total_tamed = sum(len(h.get("monster_girls", [])) for h in player.get("houses", {}).values())
    if total_tamed >= 5:
        print("Your houses are already full (max 5 monster girls).")
        return False

    city_id = player.get("location") or player.get("origin_city", "solmere")
    if city_id not in player.setdefault("houses", {}):
        print(f"You need a house in {city_id} to keep her!")
        return False

    house = player["houses"][city_id]
    house.setdefault("monster_girls", []).append({
        "key": mg.get("key"),
        "name": mg.get("name"),
        "level": mg.get("level"),
        "affection": 30,
        "captured_on": player.get("day", 1)
    })
    print(f"💕 {mg.get('name')} has been added to your house in {city_id}!")
    return True