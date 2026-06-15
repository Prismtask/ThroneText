# facilities/travel_events.py
#
# Random travel encounter system.
#
# Called by:
#   facilities/travel.py  (land routes)
#   facilities/port.py    (sea routes)
#
# Public API:
#   run_travel_events(player, travel_time, travel_type, region) -> "safe" | "dead"
#
# Scaling summary:
#   • Encounter *slots*   → 1 for short trips, up to 4-5 for long ones; +1 at night/dusk.
#   • Trigger *chance*    → 25 % (short) … 45 % (long), multiplied by time-of-day factor.
#   • Enemy *strength*    → capped to player floor ± 2, biome-filtered for theme.
#   • Item *rarity*       → floor-scaled tables matching dungeon roll_drop logic.
#   • Merchant *prices*   → ITEM_RARITY price_mult × road markdown × Charisma discount.
#   • Hazard *damage*     → 8 % of max HP × difficulty multiplier.

import random
from utils import advance_time, get_difficulty_multiplier_from_time
from resources.enemies import ENEMIES, BIOME_RACES
from resources.items import ITEMS, ITEM_RARITY, build_item
from combat.generic import combat, get_effective_attribute
from leveling import gain_exp
from character import player_max_hp

# Prefer the proper inventory helper (handles capacity / stacking if implemented)
try:
    from inventory import add_item_to_inventory as _add_to_inv
except ImportError:
    def _add_to_inv(player, item):
        player.setdefault("inventory", []).append(item)


# ═══════════════════════════════════════════════════════════════
# EVENT TABLES
# ═══════════════════════════════════════════════════════════════

LAND_EVENTS = [
    {"type": "combat",    "weight": 50},
    {"type": "discovery", "weight": 20},
    {"type": "hazard",    "weight": 15},
    {"type": "merchant",  "weight": 15},
]

SEA_EVENTS = [
    {"type": "combat",    "weight": 50},
    {"type": "storm",     "weight": 20},
    {"type": "discovery", "weight": 20},
    {"type": "calm",      "weight": 10},
]

# Thematic enemy races for sea lanes
_SEA_RACES = set(BIOME_RACES.get("coastal", []))

# Keys excluded from all random item rolls: uniques (e.g. Abyss Fang) and Scrolls of Fusion
_SKIP_IDS = frozenset(
    k for k, v in ITEMS.items()
    if v.get("unique") or v.get("type") == "scroll"
)

# Superboss-minion keys — never appear in open travel encounter pools
_MINION_ONLY_KEYS = frozenset({"dream_floatsam", "sylvana_mirror_copy", "vileheart_spiderling"})

# Rarity order used by all weighted-choice tables below
_RARITIES = ["common", "uncommon", "rare", "epic", "legendary"]

# Base shop prices per type (mirrors city shop config; used to derive all travel prices)
_BASE_PRICE = {"consumable": 15, "utility": 20, "equipment": 45}


# ═══════════════════════════════════════════════════════════════
# ITEM HELPERS
# ═══════════════════════════════════════════════════════════════

def _random_item_id():
    """Pick a random, non-unique, non-scroll item key."""
    pool = [k for k in ITEMS if k not in _SKIP_IDS]
    return random.choice(pool) if pool else "minor_healing_potion"


def _discovery_rarity(player):
    """
    Floor-scaled rarity table for roadside finds.
    Slightly more conservative than the dungeon's roll_drop table —
    road finds are windfalls, not rewards.
    """
    floor = max(1, player.get("floor", 1))
    if floor <= 3:
        weights = [0.70, 0.25, 0.05, 0.00, 0.00]
    elif floor <= 6:
        weights = [0.50, 0.35, 0.12, 0.03, 0.00]
    elif floor <= 9:
        weights = [0.30, 0.40, 0.22, 0.07, 0.01]
    else:
        weights = [0.15, 0.32, 0.33, 0.15, 0.05]
    return random.choices(_RARITIES, weights=weights)[0]


def _combat_drop_rarity(enemy_level):
    """Enemy-level-scaled rarity for post-combat drops (mirrors dungeon logic)."""
    if enemy_level <= 3:
        weights = [0.55, 0.32, 0.10, 0.03, 0.00]
    elif enemy_level <= 6:
        weights = [0.40, 0.38, 0.16, 0.05, 0.01]
    elif enemy_level <= 9:
        weights = [0.25, 0.38, 0.26, 0.09, 0.02]
    else:
        weights = [0.12, 0.28, 0.35, 0.18, 0.07]
    return random.choices(_RARITIES, weights=weights)[0]


def _merchant_stock_rarity(player):
    """
    Floor-influenced rarity for merchant stock.
    Caps at epic — road merchants don't carry legendaries.
    Matches city shop's rarity_bias logic.
    """
    floor = max(1, player.get("floor", 1))
    if floor <= 5:
        weights = [40, 35, 20, 5]   # common … epic
    else:
        weights = [25, 35, 28, 12]
    return random.choices(["common", "uncommon", "rare", "epic"], weights=weights)[0]


def _item_base_price(item):
    """
    Derive a base price using ITEM_RARITY price_mult, matching city shop logic:
        base = _BASE_PRICE[type] * price_mult
    """
    rarity     = item.get("rarity", "common")
    price_mult = ITEM_RARITY.get(rarity, ITEM_RARITY["common"])["price_mult"]
    base       = _BASE_PRICE.get(item.get("type", "equipment"), 45)
    return int(base * price_mult)


def _charisma_discount(player):
    """
    Discount percentage from Charisma alone (no city favor on the road).
    Softer ceiling than the city shop (25 % vs 40 %).
    """
    cha = get_effective_attribute(player, "Charisma")
    return min(25, max(0, (cha - 8) * 0.4))


def _merchant_price(player, item):
    """
    Road merchant price:
        shop_base × road_markdown (0.75–0.90) × (1 − Charisma discount)

    Returns (your_price, road_price_before_cha) so the display can show
    both figures if a Charisma discount is active.
    """
    base        = _item_base_price(item)
    road_factor = random.uniform(0.75, 0.90)
    road_price  = int(base * road_factor)
    cha_disc    = _charisma_discount(player)
    your_price  = max(1, int(road_price * (100 - cha_disc) / 100))
    return your_price, road_price


def _sell_price(player, item):
    """
    Sell-to-merchant price: 75 % of city shop's sell rate, soft Charisma bonus.
    City shop uses: int(12 * price_mult) × (1 + (cha - 8) / 100)
    Road merchant:  int(9  * price_mult) × (1 + (cha - 8) / 150)
    """
    rarity_mult = ITEM_RARITY.get(item.get("rarity", "common"), ITEM_RARITY["common"])["price_mult"]
    cha         = get_effective_attribute(player, "Charisma")
    cha_bonus   = max(0, (cha - 8)) / 150
    return max(1, int(9 * rarity_mult * (1 + cha_bonus)))


def _item_stat_line(item):
    """One-line stat summary for display in merchant/discovery output."""
    itype = item.get("type", "")

    if itype == "equipment":
        slot  = item.get("slot", "?").title()
        mods  = item.get("mods", {})
        mod_s = ", ".join(
            f"{stat[:3]} {'+' if v >= 0 else ''}{v}"
            for stat, v in mods.items()
        )
        return f"[{slot}{(' | ' + mod_s) if mod_s else ''}]"

    if itype == "consumable":
        if item.get("cure_curse"):
            return "[Consumable | Removes Curse]"
        if item.get("cure_poison"):
            return "[Consumable | Cures Poison]"
        if item.get("temp_stat"):
            return (f"[Consumable | +{item.get('power','?')} {item['temp_stat']}, "
                    f"{item.get('duration','?')} turns]")
        if item.get("defense_buff"):
            return f"[Consumable | +{item['defense_buff']} Defense, {item.get('duration','?')} turns]"
        heal = item.get("power", 0)
        hot  = item.get("heal_over_time", 0)
        if hot:
            return f"[Consumable | {heal} HP + {hot}/turn × {item.get('duration','?')}]"
        return f"[Consumable | Heals {heal} HP]"

    if itype == "utility":
        parts = []
        if item.get("power"):       parts.append(f"{item['power']} dmg")
        if item.get("status"):      parts.append(item["status"].title())
        if item.get("stun_chance"): parts.append(f"{int(item['stun_chance']*100)}% Stun")
        if item.get("escape_bonus"):parts.append(f"+{item['escape_bonus']} Escape")
        if item.get("blind_enemy"): parts.append("Blinds")
        if item.get("armor_pierce"):parts.append(f"Pierce {item['armor_pierce']}")
        if item.get("expose_armor"):parts.append(f"Expose ×{item['expose_armor']}")
        return f"[Utility | {', '.join(parts)}]" if parts else "[Utility]"

    return f"[{itype.title()}]"


# ═══════════════════════════════════════════════════════════════
# ENEMY SELECTION  (unchanged from v1)
# ═══════════════════════════════════════════════════════════════

def _pick_travel_enemy(player, travel_type="land", region=None):
    """Return a random non-boss enemy key appropriate for the current journey."""
    floor = max(1, player.get("floor", 1))
    lo, hi = max(1, floor - 2), floor + 2

    allowed_races = _SEA_RACES if travel_type == "sea" else (
        set(BIOME_RACES[region]) if region and region in BIOME_RACES else None
    )

    def _build_pool(race_filter):
        return [
            k for k, d in ENEMIES.items()
            if k not in _MINION_ONLY_KEYS
            and not d.get("boss")
            and not d.get("super_boss")
            and lo <= d["level"] <= hi
            and (race_filter is None or d.get("race") in race_filter)
        ]

    pool = _build_pool(allowed_races)
    if not pool:
        pool = _build_pool(None)
    if not pool:
        pool = [k for k, d in ENEMIES.items()
                if k not in _MINION_ONLY_KEYS
                and not d.get("boss") and not d.get("super_boss")]

    return random.choice(pool) if pool else None


# ═══════════════════════════════════════════════════════════════
# ENCOUNTER SCALING  (unchanged from v1)
# ═══════════════════════════════════════════════════════════════

def _num_slots(travel_time, difficulty_mult):
    if travel_time <= 60:
        slots = 1
    elif travel_time <= 180:
        slots = 2
    elif travel_time <= 360:
        slots = 3
    else:
        slots = random.randint(3, 5)
    if difficulty_mult >= 1.6:
        slots += 1
    return slots


def _trigger_chance(travel_time, difficulty_mult):
    if travel_time <= 60:
        base = 0.25
    elif travel_time <= 180:
        base = 0.33
    else:
        base = 0.45
    return min(base * (difficulty_mult ** 0.6), 0.80)


def _weighted_choice(pool):
    total = sum(e["weight"] for e in pool)
    roll  = random.uniform(0, total)
    cum   = 0
    for entry in pool:
        cum += entry["weight"]
        if roll <= cum:
            return entry
    return pool[-1]


# ═══════════════════════════════════════════════════════════════
# EVENT HANDLERS
# ═══════════════════════════════════════════════════════════════

def _handle_combat(player, travel_type, region):
    """
    Spawn 1-3 enemies and run a full combat encounter.
    On victory: award gold, XP, and a 40 % per-enemy item drop (level-scaled rarity).
    On flee: inflict an HP penalty.
    """
    floor      = max(1, player.get("floor", 1))
    num        = random.randint(1, min(3, max(1, floor // 2 + 1)))
    enemy_keys = [k for k in
                  (_pick_travel_enemy(player, travel_type, region) for _ in range(num))
                  if k]

    if not enemy_keys:
        print("  A shadow crosses the road... and vanishes. Nothing to fight.")
        input("  Press Enter to continue...")
        return "skipped"

    result = combat(player, enemy_keys)   # no floor/room args → no dungeon header

    if result == "victory":
        print("\n  --- Road Encounter Rewards ---")

        # Gold and XP
        total_xp   = sum(ENEMIES[k]["level"] * 10 for k in enemy_keys)
        total_gold = sum(ENEMIES[k]["level"] * 5 + random.randint(3, 12)
                         for k in enemy_keys)
        player["gold"] = player.get("gold", 0) + total_gold
        gain_exp(player, total_xp)
        print(f"  +{total_gold} gold  |  +{total_xp} XP")

        # Per-enemy item drops (40 % chance each, level-scaled rarity)
        for key in enemy_keys:
            if random.random() < 0.40:
                enemy_level = ENEMIES[key]["level"]
                rarity      = _combat_drop_rarity(enemy_level)
                item_id     = _random_item_id()
                item        = build_item(item_id, rarity)
                _add_to_inv(player, item.copy())
                print(f"  Found: {item['name']}  {_item_stat_line(item)}")

        input("  Press Enter to continue your journey...")

    elif result == "fled":
        penalty = random.randint(8, 20)
        player["current_hp"] = max(1, player.get("current_hp", 1) - penalty)
        print(f"\n  You flee, but not cleanly — {penalty} damage taken in the scramble.")
        print(f"  HP: {player['current_hp']}/{player_max_hp(player)}")
        input("  Press Enter to keep moving...")

    return result   # "victory" | "fled" | "dead"


def _handle_discovery(player, travel_type):
    """
    Find abandoned gold or an item on the road / at sea.
    Rarity is scaled to the player's current dungeon floor.
    Items are filtered (no uniques, no scrolls) and added via add_item_to_inventory.
    """
    find_gold = random.random() < 0.55

    if travel_type == "sea":
        if find_gold:
            gold = random.randint(20, 80)
            player["gold"] = player.get("gold", 0) + gold
            print(f"\n  A barnacled crate bobs alongside. Inside: {gold} gold in waxed pouches!")
        else:
            rarity  = _discovery_rarity(player)
            item    = build_item(_random_item_id(), rarity)
            _add_to_inv(player, item.copy())
            print(f"\n  A waterlogged satchel surfaces from the deep. You haul it aboard.")
            print(f"  Found: {item['name']}  {_item_stat_line(item)}")
    else:
        if find_gold:
            gold = random.randint(10, 50)
            player["gold"] = player.get("gold", 0) + gold
            print(f"\n  A traveler's purse lies abandoned at the roadside. You pocket {gold} gold.")
        else:
            rarity  = _discovery_rarity(player)
            item    = build_item(_random_item_id(), rarity)
            _add_to_inv(player, item.copy())
            print(f"\n  A hollow tree stump — something's wedged inside.")
            print(f"  Found: {item['name']}  {_item_stat_line(item)}")

    input("  Press Enter to continue...")


def _sell_to_merchant(player):
    """Let the player offload items to the traveling merchant at 75 % of city sell rate."""
    inv = player.get("inventory", [])
    if not inv:
        print('  "Nothing I want off you — yet." The merchant shrugs.')
        input("  Press Enter...")
        return

    print("\n  The merchant eyes your pack with practiced interest.")
    print("  (Road sell rate: ~75 % of city shop value)\n")

    for i, item in enumerate(inv):
        price = _sell_price(player, item)
        print(f"  {i+1:>2}. {item['name']}  {_item_stat_line(item)}  —  {price}g")
    print("   0. Never mind")

    try:
        idx = int(input("\n  Sell which item? ").strip()) - 1
        if 0 <= idx < len(inv):
            item  = inv.pop(idx)
            gold  = _sell_price(player, item)
            player["gold"] = player.get("gold", 0) + gold
            print(f'  Sold [{item["name"]}] for {gold}g. "A fair deal for the road!"')
        else:
            print('  "Changing your mind is free."')
    except (ValueError, IndexError):
        print("  Nothing sold.")

    input("  Press Enter...")


def _handle_merchant(player):
    """
    Wandering merchant with 2-3 items priced via ITEM_RARITY price_mult,
    a road markdown (75-90 % of base), and a Charisma discount.
    Also offers to buy items from the player at 75 % of city sell rate.
    """
    print("\n  A road-worn merchant steps out from beside a laden cart.")
    print('  "Wares! Quality goods — fair price for a fellow traveler!"')

    # Build stock: filtered item pool, floor-influenced rarity
    stock = []
    for _ in range(random.randint(2, 3)):
        item_id     = _random_item_id()
        rarity      = _merchant_stock_rarity(player)
        item        = build_item(item_id, rarity)
        your_price, road_price = _merchant_price(player, item)
        stock.append((item, your_price, road_price))

    # Display
    cha_disc = _charisma_discount(player)
    print(f"\n  Your gold: {player.get('gold', 0)}g", end="")
    if cha_disc > 0:
        print(f"  |  Charisma discount: {cha_disc:.0f}%")
    else:
        print()

    print()
    for i, (item, your_price, road_price) in enumerate(stock, 1):
        stat = _item_stat_line(item)
        if cha_disc > 0 and your_price < road_price:
            price_str = f"{your_price}g  (road: {road_price}g)"
        else:
            price_str = f"{your_price}g"
        print(f"  {i}. {item['name']}  {stat}  —  {price_str}")

    sell_opt = len(stock) + 1
    leave_opt = len(stock) + 2
    print(f"  {sell_opt}. Sell an item")
    print(f"  {leave_opt}. Move on")

    while True:
        choice = input("\n  Choice: ").strip()

        if choice == str(sell_opt):
            _sell_to_merchant(player)
            break

        if choice == str(leave_opt) or choice == "":
            print('  "Safe roads, traveler!"')
            break

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(stock):
                item, your_price, _ = stock[idx]
                if player.get("gold", 0) >= your_price:
                    player["gold"] -= your_price
                    _add_to_inv(player, item.copy())
                    print(f'  You purchase [{item["name"]}] for {your_price}g.')
                    print('  "Pleasure doing business!" The merchant tips his hat.')
                else:
                    print(f'  "You\'re {your_price - player.get("gold", 0)}g short, friend."')
            else:
                print("  Invalid choice.")
                continue
        except (ValueError, IndexError):
            print("  Invalid choice.")
            continue
        break

    input("\n  Press Enter to continue...")


def _handle_hazard(player, travel_type, difficulty_mult):
    """Environmental hazard dealing damage scaled by time-of-day difficulty."""
    max_hp = player_max_hp(player)
    damage = max(3, int(max_hp * 0.08 * difficulty_mult))

    if travel_type == "sea":
        desc = random.choice([
            "Rogue waves crash over the deck — rigging snaps and splinters fly!",
            "A hidden reef grinds the hull. The impact sends you sprawling hard.",
            "A waterspout erupts fifty yards off the bow. You cling to the mast for your life.",
            "Poisonous jellyfish swarm the hull. Tentacles whip across the railing as you pass.",
        ])
    else:
        desc = random.choice([
            "The trail crumbles into a ravine edge. You slip and tumble down the slope.",
            "A concealed spike trap snaps shut — the spikes nick through your boot.",
            "Hailstones the size of coins hammer the exposed road. No shelter in sight.",
            "Thorned briar walls the overgrown path. You push through, paying in blood.",
            "Loose shale shifts underfoot on the mountain pass. The fall is brutal.",
        ])

    print(f"\n  ! {desc}")
    player["current_hp"] = max(1, player.get("current_hp", 1) - damage)
    print(f"  You take {damage} damage.  (HP: {player['current_hp']}/{max_hp})")

    if player["current_hp"] <= max_hp * 0.25:
        print("  ⚠  Critically wounded — consider resting before your next descent.")

    input("  Press Enter to continue...")


def _handle_storm(player, difficulty_mult):
    """Sea-only: storm that delays travel and may also deal HP damage."""
    max_hp = player_max_hp(player)
    print("\n  A black wall of clouds swallows the horizon — the storm hits fast.")

    if random.random() < 0.35 * difficulty_mult:
        damage = max(4, int(max_hp * 0.12 * difficulty_mult))
        player["current_hp"] = max(1, player.get("current_hp", 1) - damage)
        advance_time(player, 60)
        print(f"  Mountainous waves batter the hull for a full hour.")
        print(f"  You take {damage} damage and arrive one hour late.")
        print(f"  HP: {player['current_hp']}/{max_hp}")
    else:
        advance_time(player, 30)
        print("  You reef the sails and ride out the squall. Unharmed — but delayed 30 minutes.")

    input("  Press Enter to continue...")


def _handle_calm_seas(player):
    """Sea-only: peaceful stretch with minor HP recovery."""
    regen  = random.randint(5, 15)
    max_hp = player_max_hp(player)
    player["current_hp"] = min(player.get("current_hp", max_hp) + regen, max_hp)
    print(f"\n  The sea lies flat as polished obsidian. The crew rests.")
    print(f"  You recover {regen} HP.  (HP: {player['current_hp']}/{max_hp})")
    input("  Press Enter to continue...")


# ═══════════════════════════════════════════════════════════════
# PUBLIC ENTRY POINT
# ═══════════════════════════════════════════════════════════════

def run_travel_events(player, travel_time, travel_type="land", region=None):
    """
    Resolve all random events for a single journey.

    Parameters
    ----------
    player       : player dict (mutated in place)
    travel_time  : journey duration in minutes
    travel_type  : "land" or "sea"
    region       : biome string for enemy theming (ignored for sea; uses coastal pool)

    Returns
    -------
    "dead"  – player was killed during an encounter
    "safe"  – journey completed (incidents may have occurred)
    """
    difficulty_mult = get_difficulty_multiplier_from_time(player)
    slots           = _num_slots(travel_time, difficulty_mult)
    chance          = _trigger_chance(travel_time, difficulty_mult)
    event_pool      = SEA_EVENTS if travel_type == "sea" else LAND_EVENTS

    quiet_stretch = True

    for _ in range(slots):
        if random.random() > chance:
            continue

        quiet_stretch = False
        event_type    = _weighted_choice(event_pool)["type"]
        print("\n" + "─" * 52)

        if event_type == "combat":
            if travel_type == "sea":
                print("  A vessel flying no flag banks hard toward you — pirates!")
            else:
                print("  Movement in the treeline. Your hand reaches for your weapon.")
            result = _handle_combat(player, travel_type, region)
            if result == "dead":
                return "dead"

        elif event_type == "discovery":
            _handle_discovery(player, travel_type)

        elif event_type == "hazard":
            _handle_hazard(player, travel_type, difficulty_mult)

        elif event_type == "merchant":
            _handle_merchant(player)

        elif event_type == "storm":
            _handle_storm(player, difficulty_mult)

        elif event_type == "calm":
            _handle_calm_seas(player)

    if quiet_stretch:
        if travel_type == "sea":
            print("\n  The voyage passes without incident. Steady winds, clear skies.")
        else:
            print("\n  The road is quiet. You make good time without trouble.")

    return "safe"