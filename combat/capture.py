# combat/capture.py
import random
from resources.items import ITEM_RARITY
from combat.stats import get_effective_attribute

def is_monster_girl(enemy):
    """Check the explicit monster_girl flag set in monster_girls.yaml."""
    return bool(enemy.get("monster_girl"))


def get_capture_message(enemy, player):
    """Personalized capture message from the enemy's dialogue block."""
    dialogue = enemy.get("dialogue", {})
    template = dialogue.get("capture")

    if template:
        return template.format(
            name=enemy.get("name", "the girl"),
            player=player.get("name", "Adventurer")
        )

    # Fallback
    return f"{enemy.get('name', 'The creature')} is captured and gently bound by your net!"


def attempt_capture(player, target, net=None):
    """Main capture logic using the monster_girl flag."""
    if not is_monster_girl(target):
        print("This enemy cannot be captured.")
        return False

    if net is None:
        # Find capture net in inventory
        net_idx = None
        for i, item in enumerate(player.get("inventory", [])):
            if item.get("capture_net"):
                net_idx = i
                net = item
                break

        if not net:
            print("You need a Capture Net to attempt this!")
            return False
        # Consume net from inventory
        player["inventory"].pop(net_idx)
    # else: net was already provided/consumed by caller (e.g., battle item use)

    # Success calculation
    cha = get_effective_attribute(player, "Charisma")
    dex = get_effective_attribute(player, "Dexterity")
    rarity_mult = ITEM_RARITY.get(net.get("rarity", "common"))["stat_mult"]

    hp_percent = target["hp"] / target.get("max_hp", target["hp"] or 1)
    difficulty = target.get("level", 1) * 1.2 + (1 - hp_percent) * 40

    roll = (cha + dex) * 0.8 + (rarity_mult * 25) - difficulty
    from combat.stat_milestones import get_charisma_bonus
    from combat.wedding_specials import apply_wedding_capture_bonus
    success_chance = max(5, min(95, roll + get_charisma_bonus(player) + apply_wedding_capture_bonus(player)))

    if random.uniform(0, 100) < success_chance:
        print("\n" + "✨" * 20)
        print(get_capture_message(target, player))
        print("✨" * 20)

        store_captured_girl(player, target)
        target["captured"] = True
        return True
    else:
        print(f"The {target.get('name')} slips through your net and escapes!")
        return False


from facilities.house import HOUSE_MONSTER_GIRL_LIMITS

def store_captured_girl(player, mg):
    """Store captured monster girl in the player's house."""
    houses = player.get("houses", {})
    if not houses:
        print("You need a house to keep her!")
        return False

    # Only one house allowed — use the player's home regardless of location
    house_city, house = next(iter(houses.items()))

    max_girls = HOUSE_MONSTER_GIRL_LIMITS.get(house.get("level", 1), 2)
    total_girls = len(house.get("monster_girls", [])) + len(player.get("allies", []))
    if total_girls >= max_girls:
        print(f"Your house is already full (max {max_girls} monster girls).")
        return False

    from combat.wedding_specials import apply_wedding_capture_affection_bonus
    base_affection = 20 + apply_wedding_capture_affection_bonus(player)

    house.setdefault("monster_girls", []).append({
        "key": mg.get("key"),
        "name": mg.get("name"),
        "level": mg.get("level"),
        "affection": base_affection,
        "captured_on": player.get("day", 1),
        "exp": 0,
        "level_hp_bonus": 0,
        "level_cap": 10,
    })
    print(f"💕 {mg.get('name')} has been added to your house in {house_city}!")
    if base_affection > 20:
        print(f"  (Regal Presence — she starts with {base_affection} affection!)")
    return True