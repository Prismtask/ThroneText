# dungeon_rooms.py — Non-combat room handlers and ASCII exploration map
"""
Room types:
    fountain    — Healing and buffing magical fountain
    merchant    — Wandering merchant (reuses travel merchant logic)
    stat_check  — Narrative skill challenge (player or ally can attempt)
    treasure    — Guaranteed rare+ item cache
    trap        — Avoidable hazard (DEX+WIS check)
"""

import random
from character import player_max_hp
from combat.stats import compute_player_stats
from utils import clear_screen, advance_time
from resources.items import ITEMS, ITEM_RARITY, build_item
from inventory import add_item_to_inventory
from leveling import gain_exp, gain_exp_ally
from combat.combat_engine import combat
from combat.ally import get_alive_allies

# Import merchant helpers from travel events
from facilities.travel_events import (
    _random_item_id, _item_stat_line, _charisma_discount,
    _merchant_price, _sell_price, _merchant_stock_rarity, _add_to_inv
)

# ── Room type weights ─────────────────────────────────────────────
ROOM_TYPE_WEIGHTS = {
    "fountain": 20,
    "merchant": 15,
    "stat_check": 25,
    "treasure": 20,
    "trap": 20,
}

# ── Stat check events ───────────────────────────────────────────────
STAT_CHECK_EVENTS = {
    "heal_wounded": {
        "name": "Wounded Adventurer",
        "desc": "A wounded adventurer lies against the wall, bleeding from a nasty gash. They look at you with pleading eyes.",
        "stat": "Wisdom",
        "base_dc": 12,
        "dc_floor_mult": 1 / 3,
    },
    "bury_corpse": {
        "name": "Ancient Corpse",
        "desc": "The skeletal remains of a long-dead explorer rest in the corner. Their equipment is rusted, but their spirit seems restless.",
        "stat": "Strength",
        "base_dc": 10,
        "dc_floor_mult": 1 / 4,
    },
    "monster_approaching": {
        "name": "Monster Approaching",
        "desc": "A low growl echoes from the shadows. A beast emerges from the darkness, sizing up your party.",
        "stat": "Charisma",
        "base_dc": 11,
        "dc_floor_mult": 1 / 3,
    },
}


ROOM_LABELS = {
    "combat": "--- Combat Chamber ---",
    "fountain": "✨  Fountain Chamber",
    "merchant": "🏺  Merchant's Corner",
    "stat_check": "📜  Mysterious Scene",
    "treasure": "💎  Treasure Vault",
    "trap": "⚠️   Suspicious Passage",
}


def pick_non_combat_type():
    """Pick a random non-combat room type using weighted selection."""
    types = list(ROOM_TYPE_WEIGHTS.keys())
    weights = list(ROOM_TYPE_WEIGHTS.values())
    return random.choices(types, weights=weights)[0]


# ═══════════════════════════════════════════════════════════════════
# PARTY MEMBER SELECTION
# ═══════════════════════════════════════════════════════════════════

def _select_party_member(player):
    """Show alive party members and let player choose who performs a check."""
    party = []
    if player.get("current_hp", 0) > 0:
        party.append(player)
    party.extend(get_alive_allies(player))
    if not party:
        return None

    print("\nWho will attempt this?")
    for idx, member in enumerate(party):
        if member is player:
            print(f"  {idx + 1}. {player['name']} (You) — HP: {player['current_hp']}/{player_max_hp(player)}")
        else:
            print(f"  {idx + 1}. {member['name']} — HP: {member['current_hp']}/{member['max_hp']}")
    print("  0. Leave it alone")

    try:
        choice = int(input("\nChoice: ").strip())
        if choice == 0:
            return None
        if 1 <= choice <= len(party):
            return party[choice - 1]
    except (ValueError, IndexError):
        pass
    return None


def _get_member_stat(member, stat_name, player):
    """Get the relevant stat for a party member."""
    if member is player:
        s, c, d, l, w, ch = compute_player_stats(member)
        return {
            "Strength": s,
            "Constitution": c,
            "Dexterity": d,
            "Learning": l,
            "Wisdom": w,
            "Charisma": ch,
        }.get(stat_name, 0)
    else:
        return member["attributes"].get(stat_name, 0)


def _roll_stat_check(member, stat_name, dc, player):
    """Roll a d20 + stat against DC. Returns (success, roll, total, stat)."""
    stat = _get_member_stat(member, stat_name, player)
    roll = random.randint(1, 20)
    total = roll + stat
    success = total >= dc
    return success, roll, total, stat


# ═══════════════════════════════════════════════════════════════════
# ASCII MAP
# ═══════════════════════════════════════════════════════════════════

def render_ascii_map(rooms, explored, current_room_idx, floor):
    """Render a 5×2 ASCII grid showing dungeon floor progress."""
    def get_symbol(idx):
        if idx == current_room_idx:
            return "P"
        if idx in explored:
            room_type = rooms[idx].get("type", "combat")
            if room_type == "combat":
                if rooms[idx].get("is_boss"):
                    return "B"
                return "C"
            return "N"
        return "?"

    clear_screen()
    print(f"=== FLOOR {floor} MAP ===")
    print()

    # 5×2 grid
    print("┌───┬───┬───┬───┬───┐")
    row1 = "│"
    for i in range(5):
        row1 += f" {get_symbol(i)} │"
    print(row1)
    
    nums1 = "│"
    for i in range(5):
        # Fix: Center the digit in exactly 3 characters
        nums1 += f"{i + 1:^3}│" 
    print(nums1)
    
    print("├───┼───┼───┼───┼───┤")
    
    row2 = "│"
    for i in range(5, 10):
        row2 += f" {get_symbol(i)} │"
    print(row2)
    
    nums2 = "│"
    for i in range(5, 10):
        # Fix: Center the digit in exactly 3 characters
        nums2 += f"{i + 1:^3}│" 
    print(nums2)
    
    print("└───┴───┴───┴───┴───┘")

    print("\n  [P] You  [C] Combat  [N] Special  [B] Boss  [?] Unexplored")
    print(f"\nCompleted: {len(explored)}/{len(rooms)} rooms")
    input("\nPress Enter to continue...")


# ═══════════════════════════════════════════════════════════════════
# ROOM HANDLERS
# ═══════════════════════════════════════════════════════════════════

def handle_fountain_room(player, floor):
    """Sparkling fountain with healing and buffing properties."""
    print("\n" + "=" * 50)
    print("✨  A sparkling fountain bubbles with magical energy!")
    print("The water glows faintly, shifting colors in the dim light.")
    print("=" * 50)

    max_hp = player_max_hp(player)

    while True:
        print("\nWhat do you do?")
        print("1. Drink — Restore 30% of your max HP")
        print("2. Immerse yourself — Gain a random stat buff")
        print("3. Splash water on allies — Heal allies for 15% HP")
        print("4. Leave it be")
        choice = input("\nChoice: ").strip()

        if choice == "1":
            old_hp = player["current_hp"]
            from combat.stat_milestones import get_wisdom_bonus
            heal = int(max_hp * 0.30) + get_wisdom_bonus(player)
            player["current_hp"] = min(old_hp + heal, max_hp)
            actual = player["current_hp"] - old_hp
            print(f"\nThe cool water revitalizes you! Healed {actual} HP.")
            print(f"HP: {player['current_hp']}/{max_hp}")
            input("Press Enter...")
            return "continue"

        elif choice == "2":
            stat = random.choice(["Strength", "Dexterity", "Constitution", "Wisdom", "Learning", "Charisma"])
            player.setdefault("active_buffs", []).append({
                "type": "floor_buff", "stat": stat, "value": 2, "remaining": 2, "source": "fountain"
            })
            print(f"\nMagical energy surges through you! +2 {stat} for 2 floors.")
            input("Press Enter...")
            return "continue"

        elif choice == "3":
            allies = get_alive_allies(player)
            if not allies:
                print("\nYou have no allies to heal.")
                continue
            for ally in allies:
                old_hp = ally["current_hp"]
                heal = int(ally["max_hp"] * 0.15)
                ally["current_hp"] = min(old_hp + heal, ally["max_hp"])
                actual = ally["current_hp"] - old_hp
                print(f"  {ally['name']} healed {actual} HP.")
            input("Press Enter...")
            return "continue"

        elif choice == "4":
            print("\nYou decide to leave the fountain untouched.")
            return "continue"
        else:
            print("Invalid choice.")


def handle_merchant_room(player, floor):
    """Wandering merchant in a dungeon chamber."""
    print("\n" + "=" * 50)
    print("🏺  A wandering merchant has set up a makeshift stall!")
    print('"Wares! Quality goods — fair price for a fellow crawler!"')
    print("=" * 50)

    # Build stock: 2–3 items, floor-influenced rarity
    stock = []
    for _ in range(random.randint(2, 3)):
        item_id = _random_item_id()
        rarity = _merchant_stock_rarity(player)
        item = build_item(item_id, rarity)
        your_price, road_price = _merchant_price(player, item)
        stock.append((item, your_price, road_price))

    cha_disc = _charisma_discount(player)
    print(f"\nYour gold: {player.get('gold', 0)}g", end="")
    if cha_disc > 0:
        print(f"  |  Charisma discount: {cha_disc:.0f}%")
    else:
        print()

    for i, (item, your_price, road_price) in enumerate(stock, 1):
        stat = _item_stat_line(item)
        if cha_disc > 0 and your_price < road_price:
            price_str = f"{your_price}g (road: {road_price}g)"
        else:
            price_str = f"{your_price}g"
        print(f"  {i}. {item['name']}  {stat}  —  {price_str}")

    sell_opt = len(stock) + 1
    leave_opt = len(stock) + 2
    print(f"  {sell_opt}. Sell an item")
    print(f"  {leave_opt}. Move on")

    while True:
        choice = input("\nChoice: ").strip()
        if choice == str(leave_opt) or choice == "":
            print('"Safe roads... or rather, safe dungeons!"')
            input("Press Enter...")
            return "continue"

        if choice == str(sell_opt):
            inv = player.get("inventory", [])
            if not inv:
                print('  "Nothing I want off you."')
                input("Press Enter...")
                return "continue"

            print("\nYour inventory:")
            for i, item in enumerate(inv):
                price = _sell_price(player, item)
                print(f"  {i+1}. {item['name']}  —  {price}g")
            print("  0. Never mind")

            try:
                idx = int(input("\nSell which item? ").strip()) - 1
                if 0 <= idx < len(inv):
                    item = inv.pop(idx)
                    gold = _sell_price(player, item)
                    player["gold"] = player.get("gold", 0) + gold
                    print(f'  Sold [{item["name"]}] for {gold}g.')
                else:
                    print("  Nothing sold.")
            except (ValueError, IndexError):
                print("  Nothing sold.")
            input("Press Enter...")
            return "continue"

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(stock):
                item, your_price, _ = stock[idx]
                if player.get("gold", 0) >= your_price:
                    player["gold"] -= your_price
                    if _add_to_inv(player, item.copy()):
                        print(f'  You purchase [{item["name"]}] for {your_price}g.')
                    else:
                        print('  Your bag is full — item dropped!')
                        player["gold"] += your_price
                else:
                    print(f'  "You\'re {your_price - player.get("gold", 0)}g short, friend."')
                input("Press Enter...")
                return "continue"
            else:
                print("Invalid choice.")
        except (ValueError, IndexError):
            print("Invalid choice.")


def handle_treasure_room(player, floor):
    """Treasure room with guaranteed rare+ item."""
    print("\n" + "=" * 50)
    print("💎  A forgotten hoard gleams in the torchlight!")
    print("Someone — or something — left these treasures here long ago.")
    print("=" * 50)

    # Guaranteed rare+ item
    rarities = ["rare", "epic", "legendary"]
    if floor <= 10:
        weights = [0.60, 0.35, 0.05]
    elif floor <= 25:
        weights = [0.40, 0.45, 0.15]
    else:
        weights = [0.25, 0.50, 0.25]

    rarity = random.choices(rarities, weights=weights)[0]
    item_id = _random_item_id()
    item = build_item(item_id, rarity)

    print(f"\nYou found: {item['name']}  {_item_stat_line(item)}")
    from inventory_ui import prompt_acquire_item
    prompt_acquire_item(player, item.copy())

    # Bonus gold
    gold = 20 + floor * 5 + random.randint(5, 15)
    player["gold"] = player.get("gold", 0) + gold
    print(f"You also found {gold} gold in a small chest!")

    input("\nPress Enter...")
    return "continue"


def handle_trap_room(player, floor):
    """Trap room that can be avoided with a DEX + WIS check."""
    print("\n" + "=" * 50)
    print("⚠️  The floor ahead looks suspicious...")
    print("Loose stones, scorch marks, and tiny needle holes dot the walls.")
    print("=" * 50)

    dc = int(10 + floor * 1.5)
    print(f"\nTrap Difficulty: {dc}")

    member = _select_party_member(player)
    if member is None:
        print("\nYou carefully back away and find another path around the trap.")
        return "continue"

    # Determine stat to use
    if member is player:
        _, _, dex, _, wis, _ = compute_player_stats(player)
    else:
        dex = member["attributes"].get("Dexterity", 0)
        wis = member["attributes"].get("Wisdom", 0)

    stat = (dex + wis) // 2
    roll = random.randint(1, 20)
    total = roll + stat
    success = total >= dc

    name = member.get("name", "You") if member is player else member["name"]
    print(f"\n{name} attempts to disarm the trap...")
    print(f"Roll: {roll} + {stat} (DEX+WIS) = {total} vs DC {dc}")

    if success:
        print(f"\n✅  Success! The trap is carefully disarmed.")
        # Hidden loot
        gold = 15 + floor * 4 + random.randint(3, 10)
        player["gold"] = player.get("gold", 0) + gold
        print(f"You find {gold} gold hidden in the trap mechanism!")

        # Small chance for extra item
        if random.random() < 0.30:
            rarity = random.choices(["common", "uncommon", "rare"], weights=[0.50, 0.35, 0.15])[0]
            item_id = _random_item_id()
            item = build_item(item_id, rarity)
            if not _add_to_inv(player, item.copy()):
                print(f"You also found: {item['name']}! (but your bag is full — dropped!)")
            else:
                print(f"You also found: {item['name']}!")
    else:
        max_hp = player_max_hp(player) if member is player else member.get("max_hp", 50)
        damage = max(3, int(max_hp * random.uniform(0.08, 0.15)))
        if member is player:
            player["current_hp"] = max(1, player["current_hp"] - damage)
            print(f"\n💥  The trap springs! You take {damage} damage.")
            print(f"HP: {player['current_hp']}/{max_hp}")
        else:
            member["current_hp"] = max(1, member["current_hp"] - damage)
            print(f"\n💥  The trap springs! {member['name']} takes {damage} damage.")
            print(f"HP: {member['current_hp']}/{member['max_hp']}")

        if member is player and player["current_hp"] <= max_hp * 0.25:
            print("⚠️  Critically wounded!")

    input("\nPress Enter...")
    return "continue"


def handle_stat_check_room(player, floor, event_key):
    """Stat check room with narrative choice and dice roll."""
    event = STAT_CHECK_EVENTS[event_key]
    print("\n" + "=" * 50)
    print(f"📜  {event['name']}")
    print(event["desc"])
    print("=" * 50)

    dc = int(event["base_dc"] + floor * event["dc_floor_mult"])
    print(f"\nRequired check: {event['stat']} (DC {dc})")

    member = _select_party_member(player)
    if member is None:
        print(f"\nYou ignore the {event['name'].lower()} and move on.")
        return "continue"

    success, roll, total, stat = _roll_stat_check(member, event["stat"], dc, player)

    name = member.get("name", "You") if member is player else member["name"]
    print(f"\n{name} attempts the task...")
    print(f"Roll: {roll} + {stat} ({event['stat']}) = {total} vs DC {dc}")

    if event_key == "heal_wounded":
        if success:
            gold = 15 + floor * 2
            print(f"\n✅  Success! You stabilize the wounded adventurer.")
            print(f"They reward you with {gold} gold and their eternal gratitude.")
            player["gold"] = player.get("gold", 0) + gold

            # Favor bonus in current city
            city_id = player.get("origin_city", "solmere")
            if "favor" not in player:
                player["favor"] = {}
            if city_id not in player["favor"]:
                player["favor"][city_id] = 0
            favor_gain = 3 + random.randint(1, 3)
            player["favor"][city_id] += favor_gain
            print(f"Gained {favor_gain} favor in {city_id.title()}!")
        else:
            print(f"\n❌  Failure! The wounds are too deep. The adventurer passes away.")
            city_id = player.get("origin_city", "solmere")
            if "favor" in player and city_id in player["favor"]:
                favor_loss = min(5, player["favor"][city_id])
                player["favor"][city_id] -= favor_loss
                print(f"Word spreads. You lose {favor_loss} favor in {city_id.title()}.")
            print("A heavy weight settles on your conscience.")

    elif event_key == "bury_corpse":
        if success:
            print(f"\n✅  Success! The remains are laid to rest with proper rites.")
            print("A gentle warmth fills the room — a blessing from the spirits.")
            player.setdefault("active_buffs", []).append({
                "type": "blessing", "stat": "all", "value": 2, "remaining": 2, "source": "corpse_blessing"
            })
            print("Gained +2 to all stats for this floor!")
        else:
            max_hp = player_max_hp(player)
            damage = max(5, int(max_hp * 0.10))
            player["current_hp"] = max(1, player["current_hp"] - damage)
            print(f"\n❌  Failure! Disturbed spirits lash out!")
            print(f"You take {damage} damage. HP: {player['current_hp']}/{max_hp}")

    elif event_key == "monster_approaching":
        if success:
            xp = floor * 15
            print(f"\n✅  Success! You calm the creature with soothing words.")
            print(f"It leaves peacefully, and you gain {xp} XP from the experience.")
            gain_exp(player, xp)
            for ally in player.get("allies", []):
                if ally.get("current_hp", 0) > 0:
                    gain_exp_ally(ally, xp)
        else:
            print(f"\n❌  Failure! The creature snarls and attacks!")
            # Spawn a single enemy of the floor's level
            # Local import to avoid circular dependency at module load
            from resources.enemies import ENEMIES
            from dungeon import get_random_enemy_key

            region = player.get("dungeon_region", "temperate")
            enemy_key = get_random_enemy_key(floor, boss=False, region=region)
            enemy_name = ENEMIES[enemy_key]["name"]
            print(f"\nA {enemy_name} attacks!")
            input("Press Enter to fight...")

            result = combat(player, [enemy_key], floor=floor)
            if result == "dead":
                return "dead"
            elif result == "fled":
                return "fled"
            elif result == "victory":
                # Award reduced XP for this forced fight
                enemy_level = ENEMIES[enemy_key]["level"]
                gain_exp(player, enemy_level * 8)
                for ally in player.get("allies", []):
                    if ally.get("current_hp", 0) > 0:
                        gain_exp_ally(ally, enemy_level * 8)
                # Chance for drop
                if random.random() < 0.40:
                    rarities = ["common", "uncommon", "rare"]
                    weights = [0.50, 0.35, 0.15]
                    rarity = random.choices(rarities, weights=weights)[0]
                    item_id = _random_item_id()
                    item = build_item(item_id, rarity)
                    if not _add_to_inv(player, item.copy()):
                        print(f"\nFound: {item['name']} (but your bag is full — dropped!)")
                    else:
                        print(f"\nFound: {item['name']}")
                # Small gold
                gold = enemy_level * 5 + random.randint(3, 10)
                player["gold"] = player.get("gold", 0) + gold
                print(f"Found {gold} gold.")
                input("Press Enter...")

    input("\nPress Enter...")
    return "continue"
