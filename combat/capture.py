from combat.combat_io import c_print, c_input
# combat/capture.py
import random
from combat.stats import get_effective_attribute
from inventory import remove_item_by_reference

def is_monster_girl(enemy):
    """Check the explicit monster_girl flag set in monster_girls.yaml."""
    return bool(enemy.get("monster_girl"))


def is_capturable(enemy):
    """Check if an enemy is a capturable monster girl.

    Heroines (those with _heroine set) are monster girls but are recruited
    through quests, not captured via nets.
    """
    return is_monster_girl(enemy) and not enemy.get("_heroine")


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
    if not is_capturable(target):
        if target.get("_heroine"):
            c_print("This heroine cannot be captured — she must be recruited through her quest.")
        else:
            c_print("This enemy cannot be captured.")
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
            c_print("You need a Capture Net to attempt this!")
            return False
        # Consume net from inventory
        remove_item_by_reference(player, net)
    # else: net was already provided/consumed by caller (e.g., battle item use)

    # Success calculation
    cha = get_effective_attribute(player, "Charisma")
    dex = get_effective_attribute(player, "Dexterity")
    rarity_mult_bonus = net.get("rarity_mult_bonus", 25)

    hp_percent = target["hp"] / target.get("max_hp", target["hp"] or 1)
    difficulty = target.get("level", 1) * 1.2 + (1 - hp_percent) * 40

    roll = (cha + dex) * 0.8 + rarity_mult_bonus - difficulty
    from combat.stat_milestones import get_charisma_bonus
    from combat.weapon.wedding_specials import apply_wedding_capture_bonus
    success_chance = max(5, min(95, roll + get_charisma_bonus(player) + apply_wedding_capture_bonus(player)))

    if random.uniform(0, 100) < success_chance:
        c_print("\n" + "✨" * 20)
        c_print(get_capture_message(target, player))
        c_print("✨" * 20)

        store_captured_girl(player, target)
        target["captured"] = True
        return True
    else:
        c_print(f"The {target.get('name')} slips through your net and escapes!")
        return False


from facilities.house import HOUSE_MONSTER_GIRL_LIMITS

def store_captured_girl(player, mg):
    """Store captured monster girl in the player's house."""
    houses = player.get("houses", {})
    if not houses:
        c_print("You need a house to keep her!")
        return False

    # Only one house allowed — use the player's home regardless of location
    house_city, house = next(iter(houses.items()))

    # ── Duplicate check ──────────────────────────────────────────────────────
    mg_key = mg.get("key", "")
    existing = None
    for girl in house.get("monster_girls", []):
        if girl.get("key") == mg_key:
            existing = girl
            break
    if not existing:
        for ally in player.get("allies", []):
            if ally.get("key") == mg_key:
                existing = ally
                break

    if existing:
        c_print(f"\nYou already have {mg.get('name', 'a girl')} in your household!")
        sell_price = mg.get("level", 1) * 50 + 100
        c_print(f"1. Sell her for {sell_price} gold")
        c_print(f"2. Release her back to the wild")
        c_print(f"3. Let her bond with your existing {existing.get('name', 'girl')} (+20 affection)")
        dup_choice = c_input("CAPTURE_DUPLICATE_CHOICE:").strip()
        if dup_choice == "1":
            player["gold"] = player.get("gold", 0) + sell_price
            c_print(f"Sold the captured {mg.get('name', 'girl')} for {sell_price} gold.")
            c_print(f"  Gold: {player['gold']}")
            return False
        elif dup_choice == "3":
            aff_cap = existing.get("affection_cap", 100)
            existing["affection"] = min(aff_cap, existing.get("affection", 30) + 20)
            c_print(f"Your {existing.get('name', 'girl')} bonded with the newcomer!")
            c_print(f"  Affection +20 (now {existing['affection']}/{aff_cap})")
            return False
        else:
            c_print(f"You release the captured {mg.get('name', 'girl')} back to the wild.")
            return False

    max_girls = HOUSE_MONSTER_GIRL_LIMITS.get(house.get("level", 1), 2)
    total_girls = len(house.get("monster_girls", [])) + len(player.get("allies", []))
    if total_girls >= max_girls:
        c_print(f"Your house is already full (max {max_girls} monster girls).")
        return False

    from combat.weapon.wedding_specials import apply_wedding_capture_affection_bonus
    base_affection = 20 + apply_wedding_capture_affection_bonus(player)

    captured_level = mg.get("level", 1)
    house.setdefault("monster_girls", []).append({
        "key": mg.get("key"),
        "name": mg.get("name"),
        "level": captured_level,
        "affection": base_affection,
        "captured_on": player.get("day", 1),
        "exp": 0,
        "level_hp_bonus": max(0, (captured_level - 1) * 4),
        "level_cap": 10,
    })
    c_print(f"💕 {mg.get('name')} has been added to your house in {house_city}!")
    if base_affection > 20:
        c_print(f"  (Regal Presence — she starts with {base_affection} affection!)")
    return True