import random
from resources.enemies import ENEMIES, BIOME_RACES
from resources.items import build_item, ITEMS, ITEM_RARITY
from resources.cities import CITIES
from combat.combat_engine import combat
from combat.stats import player_con_mod
from combat.broodmother import combat_broodmother 
from combat.slitcurrent import combat_slitcurrent
from combat.sylvana import combat_sylvana
from combat.ignis import combat_ignis
from combat.yinglong import combat_yinglong
from combat.rientrante import combat_rientrante
from combat.everlong_ship import combat_everlong_ship
from combat.black_silence import combat_black_silence
from combat.palette_chromatic_artisan import combat_palette
from combat.entangled_chrysalis import combat_entangled_chrysalis
from combat.queen_of_hearts import combat_queen_of_hearts
from combat.big_bad_wolf import combat_big_bad_wolf
from combat.wicked_witch import combat_wicked_witch
from combat.jabberwock import combat_jabberwock
from combat.mary_sue import combat_mary_sue
from combat.wl_floor_bosses import get_wl_floor_boss, is_wl_boss_floor
from character import player_max_hp
from save_load import save_game
from utils import clear_screen, advance_time, get_difficulty_multiplier_from_time, format_time, _tprint, _tpause, _tclear, _tmenu, _term
from leveling import gain_exp, gain_exp_ally
import dungeon_rooms
from dungeon_rooms import (
    pick_non_combat_type,
    handle_fountain_room,
    handle_merchant_room,
    handle_treasure_room,
    handle_trap_room,
    handle_stat_check_room,
    ROOM_LABELS,
    STAT_CHECK_EVENTS,
    WL_ROOM_LABELS,
    WL_STAT_CHECK_EVENTS,
    get_stat_check_events,
    get_room_labels,
)
from pandemonium_curses import (
    apply_curse_on_floor_start,
    apply_room_entry_damage,
    apply_healing_reduction,
    apply_gold_reduction,
    is_flee_blocked,
    clear_curse,
    format_active_curse_line,
    get_curse,
)
from wonderland_curses import (
    apply_wonderland_quirk_on_floor_start,
    clear_wonderland_quirk,
    get_wl_quirk,
    format_active_quirk_line as format_active_wl_quirk_line,
    format_quirk_summary,
    apply_tea_party_regen,
    apply_queens_decree,
    get_curiosity_boost_value,
    get_mad_hatter_drop_chance,
    get_cheshire_dodge_chance,
    get_jabberwock_bane_multiplier,
    get_caterpillars_insight_reduction,
    get_white_rabbit_cooldown_reduction,
    get_looking_glass_reroll_chance,
    get_painting_roses_reduction,
    # ── Shadow system ──
    SHADOW_CHOICE_FLOORS,
    trigger_shadow_choice,
    format_active_shadows_line,
    clear_all_shadows,
    get_player_shadows,
    get_shadow_room_damage,
    get_shadow_stat_penalty,
    get_shadow_skip_chance,
    get_shadow_healing_reduction,
    get_shadow_gold_reduction,
    get_shadow_damage_taken_multiplier,
    get_shadow_accuracy_penalty,
    get_shadow_bleed_poison_extension,
    get_shadow_initiative_bonus,
    get_shadow_stat_check_dc_increase,
    format_mary_sue_shadow_intro,
    get_mary_sue_shadow_modifiers,
)

def get_random_enemy_key(floor, boss=False, region=None, player=None):
    """Pick a random enemy suitable for the current floor.
    
    If player is provided and has active bounties, bounty-target enemies
    in the pool receive extra weight (duplicated entries), making them
    more likely to spawn when the player is actively hunting them.
    """
    pool = []
    allowed_races = None
    if region and region in BIOME_RACES:
        allowed_races = set(BIOME_RACES[region])

    for key, data in ENEMIES.items():
        # Skip minion-only enemies in regular rooms
        if data.get("minion_only", False):
            continue
        # Skip shadow copies — internal combat helpers, not real enemies
        if data.get("_shadow", False):
            continue
        # Skip heroines — they are recruited via quests, not fought in dungeons
        if data.get("_heroine"):
            continue
        # Skip Wonderland-exclusive enemies outside Wonderland
        if data.get("secondary_race") == "Storybook" and region != "wonderland":
            continue
        # Skip superbosses — they are handled separately by the superboss
        # dispatch in explore_dungeon() and should never appear as regular enemies.
        if data.get("super_boss", False):
            continue
        if boss != data.get("boss", False):
            continue

        # Level constraints
        if boss:
            # Boss: 1–3 levels above current floor
            if not (data["level"] >= floor + 1 and data["level"] <= floor + 3):
                continue
        else:
            # Normal: progressively wider band as floor increases.
            # Lower bound starts at floor-6 and widens by 1 every 10 floors
            # (floor-10 at floor 40+), keeping the pool healthy at depth.
            upper_offset = min(floor, 3)
            lower_bound = max(1, floor - (6 + floor // 10))
            if not (data["level"] >= lower_bound and data["level"] <= floor + upper_offset):
                continue

        # Region filter — checks both primary race and secondary_race
        # (Wonderland enemies use secondary_race: Storybook while their
        #  primary race is Construct / Beast / Shadow / etc.)
        if allowed_races:
            enemy_race = data.get("race")
            secondary = data.get("secondary_race")
            if enemy_race not in allowed_races and secondary not in allowed_races:
                continue

        pool.append(key)

    # Fallback – ignore region but keep level and boss/superboss constraints
    if not pool:
        for key, data in ENEMIES.items():
            if data.get("minion_only", False):
                continue
            if data.get("_heroine"):
                continue
            if data.get("_shadow", False):
                continue
            if data.get("secondary_race") == "Storybook" and region != "wonderland":
                continue
            if data.get("super_boss", False):
                continue
            if boss != data.get("boss", False):
                continue
            if boss:
                if not (data["level"] >= floor + 1 and data["level"] <= floor + 3):
                    continue
            else:
                upper_offset = min(floor, 3)
                lower_bound = max(1, floor - (6 + floor // 10))
                if not (data["level"] >= lower_bound and data["level"] <= floor + upper_offset):
                    continue
            pool.append(key)

    if not pool:
        # Ultimate fallback – any enemy of the right boss type
        pool = [k for k, d in ENEMIES.items() if d.get("boss", False) == boss
                and not d.get("minion_only", False)
                and not d.get("_heroine")
                and not d.get("_shadow", False)
                and not d.get("super_boss", False)
                and not (d.get("secondary_race") == "Storybook" and region != "wonderland")]
    
    if not pool:
        # Emergency fallback – any enemy at all (keep sensible filters to avoid
        # superbosses / Wonderland enemies / heroines leaking into wrong contexts)
        pool = [k for k, d in ENEMIES.items() if not d.get("_heroine")
                and not d.get("_shadow", False)
                and not d.get("super_boss", False)
                and not (d.get("secondary_race") == "Storybook" and region != "wonderland")]
    
    if not pool:
        # Critical error – no enemies loaded
        raise RuntimeError(
            f"No enemies found! ENEMIES has {len(ENEMIES)} entries. "
            f"floor={floor}, boss={boss}, region={region}"
        )

    # ── Bounty weighting ────────────────────────────────────────────────
    # When the player has active bounties, duplicate bounty-target enemies
    # in the pool so they appear more often than other enemies.
    if player:
        active_bounties = player.get("active_bounties", [])
        if active_bounties:
            bounty_targets = {b["target_enemy"] for b in active_bounties}
            # Add 2 bonus copies of each bounty target already in the pool
            bonus = [key for key in pool if key in bounty_targets]
            if bonus:
                pool.extend(bonus * 2)  # 2 extra copies = 3x base weight

    return random.choice(pool)


def generate_floor(floor, region=None, player=None):
    """Generate a floor with 10 rooms: 9 mixed rooms + 1 boss room.
    
    Non-combat rooms have a base 10% chance to appear.
    For each consecutive combat room, the chance increases by 5%.
    When a non-combat room appears, the chance resets to 10%.
    
    If player is provided, bounty-target enemies receive extra spawn weight.
    """
    rooms = []
    max_enemies = min(5, floor)
    
    # Dynamic non-combat chance
    non_combat_chance = 0.10
    consecutive_combat = 0

    # ── Select region-appropriate stat check events ──────────────────
    region_events = get_stat_check_events(region)

    # Generate 9 rooms (index 0-8)
    for room_idx in range(9):
        if random.random() < non_combat_chance:
            # Non-combat room
            room_type = pick_non_combat_type()
            if room_type == "stat_check":
                event_key = random.choice(list(region_events.keys()))
                rooms.append({"type": "stat_check", "event": event_key})
            elif room_type == "trap":
                difficulty = int(10 + floor * 1.5)
                rooms.append({"type": "trap", "difficulty": difficulty})
            else:
                rooms.append({"type": room_type})
            # Reset chance after non-combat room
            non_combat_chance = 0.10
            consecutive_combat = 0
        else:
            # Combat room
            num_enemies = random.randint(1, max_enemies)
            # Daily events: Monster Surge — dungeon enemies are more numerous
            if player and player.get("daily_effects", {}).get("monster_surge"):
                num_enemies = min(5, num_enemies + 1)
            enemy_keys = [get_random_enemy_key(floor, boss=False, region=region, player=player)
                          for _ in range(num_enemies)]
            rooms.append({"type": "combat", "enemies": enemy_keys})
            consecutive_combat += 1
            non_combat_chance = min(0.10 + 0.05 * consecutive_combat, 0.80)
    
    # Room 10: Boss room (always combat)
    # ── Wonderland: every even floor that isn't a multiple of 10 is a boss floor ──
    if region == "wonderland" and is_wl_boss_floor(floor):
        is_true_boss_floor = True
        # Use the specific floor boss instead of a random one
        boss_info = get_wl_floor_boss(floor)
        if boss_info:
            _, boss_key, _ = boss_info
            boss_room = [boss_key]
        else:
            boss_room = [get_random_enemy_key(floor, boss=True, region=region, player=player)]
    else:
        is_true_boss_floor = (floor % 5 == 0)
        boss_room = [get_random_enemy_key(floor, boss=is_true_boss_floor, region=region, player=player)]
    
    num_minions = random.randint(0, min(4, floor - 1))
    for _ in range(num_minions):
        boss_room.append(get_random_enemy_key(floor, boss=False, region=region, player=player))
    rooms.append({"type": "combat", "enemies": boss_room, "is_boss": True})
    
    return rooms

# ── Equipment drop pool (exclude uniques, consumables, scrolls, ascension, wonderland-only) ──
_EQUIP_POOL = frozenset(
    k for k, v in ITEMS.items()
    if v.get("type") == "equipment"
    and not v.get("unique")
    and not v.get("wonderland_only")
    and not v.get("black_market_only")
)

# ── Consumable drop tiers (weighted by power/rarity tier) ──
_CONSUMABLE_TIERS = {
    1: ["minor_healing_potion", "antidote", "healing_salve"],
    2: ["healing_potion", "elixir_of_strength", "elixir_of_speed",
        "elixir_of_vitality", "elixir_of_mind", "battle_drink",
        "iron_skin_potion", "curse_cleansing_scroll", "fire_bomb",
        "ice_bomb", "smoke_bomb", "throwing_knife", "flash_powder",
        "poison_flask", "stun_bomb"],
    3: ["greater_healing_potion", "holy_water", "thunder_bomb",
        "acid_flask", "armor_shatter_flask"],
    4: ["superior_healing_potion", "recalled_scroll",
        "ember_draught", "frostward_tonic", "thunderbrew",
        "gale_cordial", "stoneblood_vial", "blessed_water",
        "shadow_essence", "mana_philter"],
}

# Filter tier pools to only items that actually exist in ITEMS dict
_CONSUMABLE_TIERS = {
    tier: [iid for iid in ids if iid in ITEMS]
    for tier, ids in _CONSUMABLE_TIERS.items()
}


def roll_drop(enemy_level, pandemonium=False):
    """Roll for an item drop. Returns (item_id, rarity) or None.

    Split: 60% equipment (with rarity), 40% consumable (no rarity — always 'common').
    """
    if pandemonium:
        if random.random() > 0.70:
            return None
    else:
        if random.random() > 0.50:
            return None

    # 60% equipment, 40% consumable
    if random.random() < 0.60:
        return _roll_equipment_drop(enemy_level, pandemonium)
    else:
        return _roll_consumable_drop(enemy_level)


def _roll_equipment_drop(enemy_level, pandemonium):
    """Roll for equipment with rarity using the new narrower weights."""
    rarities = ["common", "uncommon", "rare", "epic", "legendary"]

    if pandemonium:
        if enemy_level <= 5:
            weights = [0.18, 0.28, 0.28, 0.16, 0.10]
        elif enemy_level <= 10:
            weights = [0.10, 0.18, 0.30, 0.26, 0.16]
        elif enemy_level <= 20:
            weights = [0.05, 0.14, 0.26, 0.32, 0.23]
        elif enemy_level <= 30:
            weights = [0.03, 0.10, 0.20, 0.35, 0.32]
        else:
            weights = [0.02, 0.06, 0.16, 0.36, 0.40]
    else:
        if enemy_level <= 5:
            weights = [0.48, 0.32, 0.15, 0.05, 0.00]
        elif enemy_level <= 10:
            weights = [0.34, 0.34, 0.20, 0.10, 0.02]
        elif enemy_level <= 20:
            weights = [0.22, 0.30, 0.28, 0.15, 0.05]
        elif enemy_level <= 30:
            weights = [0.12, 0.24, 0.30, 0.22, 0.12]
        else:
            weights = [0.06, 0.18, 0.28, 0.28, 0.20]

    rarity = random.choices(rarities, weights=weights)[0]
    valid_ids = list(_EQUIP_POOL)
    item_id = random.choice(valid_ids) if valid_ids else "iron_sword"
    return (item_id, rarity)


def _roll_consumable_drop(enemy_level):
    """Roll for a consumable. No rarity — consumables are always 'common'."""
    # Determine which tier of consumables can drop based on enemy level
    if enemy_level <= 5:
        tier_pool = [1, 1, 1, 2]  # mostly tier 1, occasional tier 2
    elif enemy_level <= 10:
        tier_pool = [1, 2, 2, 2]
    elif enemy_level <= 20:
        tier_pool = [2, 2, 3, 3]
    elif enemy_level <= 30:
        tier_pool = [2, 3, 3, 4]
    else:
        tier_pool = [3, 3, 4, 4]

    tier = random.choice(tier_pool)
    pool = _CONSUMABLE_TIERS.get(tier, _CONSUMABLE_TIERS.get(1, ["minor_healing_potion"]))
    if not pool:
        pool = ["minor_healing_potion"]
    item_id = random.choice(pool)
    return (item_id, "common")

def roll_gold_drop(enemy_key, is_boss=False, pandemonium=False):
    """Roll gold drop from defeated enemy."""
    enemy_level = ENEMIES[enemy_key]["level"]
    
    # Base gold
    base_gold = enemy_level * 8 + random.randint(5, 15)
    
    if pandemonium:
        # Pandemonium: 2.5x gold multiplier + guaranteed bonus
        base_gold = int(base_gold * 2.5) + random.randint(30, 60)
    
    if is_boss:
        base_gold = int(base_gold * 2.5) + random.randint(20, 40)
    
    # Bonus gold chance (25% chance for big bonus)
    if random.random() < 0.25:
        base_gold = int(base_gold * 1.6)
    
    gold = max(8, base_gold)  # Minimum gold
    
    return gold


def add_drop_to_inventory(player, enemy_level, pandemonium=False):
    drop = roll_drop(enemy_level, pandemonium=pandemonium)
    if drop:
        item_id, rarity = drop
        item = build_item(item_id, rarity)
        _tprint(f"An enemy drops: {item['name']} [{rarity}]!")
        from inventory_ui import prompt_acquire_item
        if prompt_acquire_item(player, item):
            _tprint(f"You acquired the {item['name']}!")
        return True
    return False

def add_gold_drop(player, enemy_key, pandemonium=False):
    """Add gold from enemy to player and print message."""
    is_boss = ENEMIES[enemy_key].get("boss", False)
    gold = roll_gold_drop(enemy_key, is_boss, pandemonium=pandemonium)
    
    # Pandemonium: Corrupted Loot curse reduces gold
    gold = apply_gold_reduction(player, gold)
    # Wonderland: Queen's Decree quirk boosts gold
    gold = apply_queens_decree(player, gold)
    # Wonderland Shadow: White Rabbit's Panic reduces gold
    shadow_gold_reduce = get_shadow_gold_reduction(player)
    if shadow_gold_reduce > 0:
        gold = max(1, int(gold * (1.0 - shadow_gold_reduce)))
    
    # Daily events: Lucky Day / Full Moon gold bonus
    from events import get_daily_bonus_multiplier
    gold = int(gold * get_daily_bonus_multiplier(player, "gold_bonus"))

# Wonderland uses per‑10‑floor superbosses (unlike the global per‑20).
# Each entry maps floor → (boss_name, module_path, combat_function).
# Phases 13‑16 will populate floors 20‑50; only floor 10 is live now.
_WL_SUPERBOSS_MAP = {
    10: ("Queen of Hearts",            combat_queen_of_hearts),
    20: ("Big Bad Wolf",               combat_big_bad_wolf),
    30: ("Wicked Witch of the West",   combat_wicked_witch),   # Phase 14
    40: ("Jabberwock",                 combat_jabberwock),     # Phase 15
    50: ("Mary Sue",                   combat_mary_sue),       # Phase 16
}


def _record_superboss_defeat(player, boss_id):
    """Track distinct superboss kills (used by guild legacy rewards)."""
    kills = player.setdefault("defeated_superbosses", [])
    if boss_id not in kills:
        kills.append(boss_id)


def _wl_superboss_defeated(player, floor):
    """Return True if the Wonderland superboss for this floor was already defeated."""
    flag_map = {
        10: "wl_boss_defeated_queen_of_hearts",
        20: "wl_boss_defeated_big_bad_wolf",
        30: "wl_boss_defeated_wicked_witch",
        40: "wl_boss_defeated_jabberwock",
        50: "wl_boss_defeated_mary_sue",
    }
    flag = flag_map.get(floor)
    return bool(flag and player.get(flag))


def _wonderland_superboss_dispatch(player, floor, superboss_override):
    """Run a Wonderland‑specific superboss encounter.

    Args:
        player: player state dict
        floor: current dungeon floor
        superboss_override: Optional function(boss_name, floor) -> str
            injected by the GUI combat screen.

    Returns:
        "victory" | "dead" | "fled" (fled restarts the fight)
    """
    entry = _WL_SUPERBOSS_MAP.get(floor)
    if entry is None:
        _tprint(f"\n  ERROR: No Wonderland superboss defined for floor {floor}.")
        _tpause("Press Enter to continue...")
        return "victory"

    boss_name, combat_fn = entry

    _tprint("\n" + "=" * 60)
    _tprint(f"  WONDERLAND SUPERBOSS — FLOOR {floor}")
    _tprint(f"  {boss_name}")
    _tprint("=" * 60)
    _tpause("Press Enter to face the horror...")

    while True:
        advance_time(player, 60)
        if superboss_override:
            result = superboss_override(boss_name.lower().replace(" ", "_"), floor)
        else:
            result = combat_fn(player)

        if result == "victory":
            # Set defeat flag
            flag_map = {
                10: "wl_boss_defeated_queen_of_hearts",
                20: "wl_boss_defeated_big_bad_wolf",
                30: "wl_boss_defeated_wicked_witch",
                40: "wl_boss_defeated_jabberwock",
                50: "wl_boss_defeated_mary_sue",
            }
            flag = flag_map.get(floor)
            if flag:
                player[flag] = True

            _record_superboss_defeat(player, {
                10: "wl_queen_of_hearts",
                20: "wl_big_bad_wolf",
                30: "wl_wicked_witch",
                40: "wl_jabberwock",
                50: "wl_mary_sue",
            }.get(floor, f"wl_floor_{floor}"))

            # Rewards: exp = 300 + (floor * 60), gold = 200 + (floor * 40)
            super_boss_exp = 300 + (floor * 60)
            super_boss_gold = 200 + (floor * 40)
            if player.get("pandemonium_mode"):
                super_boss_gold = int(super_boss_gold * 2.5)
                super_boss_exp = int(super_boss_exp * 1.5)
                _tprint("\n  Pandemonium surges — the reward is amplified!")
            # Daily events: Lucky Day / Full Moon gold bonus
            from events import get_daily_bonus_multiplier
            super_boss_gold = int(super_boss_gold * get_daily_bonus_multiplier(player, "gold_bonus"))
            player["gold"] = player.get("gold", 0) + super_boss_gold
            _tprint(f"\n  {boss_name} defeated! Bonus: +{super_boss_gold} gold, +{super_boss_exp} XP!")
            gain_exp(player, super_boss_exp)
            for ally in player.get("allies", []):
                if ally.get("current_hp", 0) > 0:
                    gain_exp_ally(ally, super_boss_exp)

            # ── Unique item drops ────────────────────────────────────
            # Guard: only award loot once per save per floor
            loot_flag = f"wl_floor_looted_{floor}"
            if not player.get(loot_flag):
                wl_drop_map = {
                    10: "rose_tinted_crown",
                    20: "crimson_hood_scrap",
                    30: "witch_hat",
                    40: "vorpal_blade_fragment",
                    50: "authors_pen",
                }
                drop_id = wl_drop_map.get(floor)
                if drop_id:
                    from inventory import add_item_to_inventory
                    item = build_item(drop_id)
                    add_item_to_inventory(player, item)
                    _tprint(f"  🎁 Received unique reward: {item.get('name', drop_id)}!")

                # ── Secondary drops ────────────────────────────────────
                if floor == 20:
                    secondary = ["wolfs_tooth"]
                    # Only grant woodcutters_broken_axe if player doesn't already have one
                    has_axe = any(it.get("id") == "woodcutters_broken_axe" for it in player.get("inventory", []))
                    has_axe = has_axe or any(
                        ally.get("equipped", {}).get("weapon", {}).get("id") == "woodcutters_broken_axe"
                        for ally in player.get("allies", [])
                    )
                    if not has_axe:
                        secondary.append("woodcutters_broken_axe")
                    for _ in range(3):
                        secondary.append("wolfs_tooth")
                    for sid in secondary:
                        sitem = build_item(sid)
                        if sitem:
                            add_item_to_inventory(player, sitem)
                            _tprint(f"  🎁 Obtained: {sitem.get('name', sid)}!")

                if floor == 30:
                    secondary = ["broomstick", "emerald_flame_crystal"]
                    for _ in range(3):
                        secondary.append("monkey_wing")
                    for sid in secondary:
                        sitem = build_item(sid)
                        if sitem:
                            add_item_to_inventory(player, sitem)
                            _tprint(f"  🎁 Obtained: {sitem.get('name', sid)}!")

                if floor == 50:
                    secondary = ["mary_sue_teardrop", "plot_hole_scrap", "wonderland_key"]
                    for sid in secondary:
                        sitem = build_item(sid)
                        if sitem:
                            add_item_to_inventory(player, sitem)
                            _tprint(f"  🎁 Obtained: {sitem.get('name', sid)}!")

                # Mark this floor's loot as claimed
                player[loot_flag] = True

            # Advance floor
            # Clear Wonderland shadows after superboss victory
            clear_all_shadows(player)
            return "victory"

        elif result == "fled":
            _tprint("You cannot flee from a Wonderland Superboss!")
            _tpause("Press Enter to continue the fight...")
            continue

        elif result == "dead":
            return "dead"

        else:
            # error, timeout, or unknown — return safely without death penalty
            _tprint(f"\n  The fight was interrupted (result: {result}). Returning to safety...")
            _tpause("Press Enter to continue...")
            return "interrupted"


def _ensure_city_floors(player, city_id):
    """Guarantee city_floors[city_id] exists, migrating legacy saves if needed."""
    if "city_floors" not in player:
        player["city_floors"] = {}
    if city_id not in player["city_floors"]:
        if player["city_floors"]:
            # New city: dungeon is independent — always start at floor 1
            # with only floor 1 unlocked.  Inheriting other cities'
            # max_floor let players skip floors and instantly counted
            # new biomes toward ascension/Pandemonium milestones.
            player["city_floors"][city_id] = {"floor": 1, "max_floor": 1}
        else:
            # Legacy save migration: no per-city data exists yet, so
            # preserve the global max_floor for the first city so old
            # saves don't lose their unlocked floors.
            best_max = player.get("max_floor", 1)
            player["city_floors"][city_id] = {"floor": 1, "max_floor": max(1, best_max)}


def _grant_glass_anchor(player):
    """Grant the Glass Anchor key item if the player doesn't already have it."""
    inv = player.get("inventory", [])
    already_has = any(item.get("id") == "glass_anchor" for item in inv)
    if already_has:
        return

    from resources.items import build_item
    from inventory import add_item_to_inventory

    anchor = build_item("glass_anchor", rarity="legendary")
    added = add_item_to_inventory(player, anchor)
    if added:
        _tprint("\n" + "═" * 50)
        _tprint("  💎 KEY ITEM ACQUIRED: Glass Anchor")
        _tprint("  A crystalline shard torn from the heart of Pandemonium.")
        _tprint("  It resonates with the Isle's unstable magic —")
        _tprint("  arcane teleportation TO the Isle of Glass is now possible.")
        _tprint("═" * 50)
        _tpause("Press Enter to continue...")
    else:
        _tprint("\n  ⚠️ Could not receive Glass Anchor (inventory error).")
        _tpause("Press Enter to continue...")


def explore_dungeon(player, combat_override=None, superboss_override=None):
    """Main dungeon loop. Clears one floor. Returns False if player dies.

    Args:
        combat_override: Optional function(player, enemy_keys, **kwargs) -> str
            If provided, called instead of combat() for regular encounters.
            Allows the GUI to inject its own combat screen.
        superboss_override: Optional function(tier, floor) -> str
            If provided, called instead of direct superboss combat_*() calls.
            Allows the GUI to inject its own superboss combat screen.
    """
    # ── Resolve origin city and ensure per-city progress record exists ─────
    origin_city = player.get("origin_city", "solmere")
    _ensure_city_floors(player, origin_city)
    city_prog = player["city_floors"][origin_city]

    # player["floor"] is the transient cursor set by city.py before entry;
    # treat it as authoritative for this run.
    floor = city_prog["floor"]

    # ----- Determine current dungeon region -----
    region = player.get("dungeon_region", "temperate")
    dungeon_display = "PANDEMONIUM" if player.get("pandemonium_mode") else region.upper()

    # ── Wonderland Floor 50: shadow choice BEFORE Mary Sue ──────────────
    if region == "wonderland" and floor == 50 and not _wl_superboss_defeated(player, floor):
        clear_all_shadows(player)
        _tprint("\n  🌑 The Author's study awaits. Wonderland makes its final demand...")
        _tpause("Press Enter to face the growing darkness...")
        shadow_msg = trigger_shadow_choice(player, floor, term_func=_term, count=2)
        _tprint(shadow_msg)
        _tpause("Press Enter to continue...")

    # ----- WONDERLAND SUPERBOSS (per‑10‑floor, before global per‑20 check) -----
    if region == "wonderland" and floor % 10 == 0 and not _wl_superboss_defeated(player, floor):
        result = _wonderland_superboss_dispatch(player, floor, superboss_override)
        if result == "dead":
            player.pop("pandemonium_mode", None)
            return "dead"
        elif result == "interrupted":
            # Combat error — return player safely without death penalty
            save_game(player)
            return True
        elif result == "victory":
            # Advance floor progress
            next_floor = floor + 1
            old_max = city_prog["max_floor"]
            city_prog["floor"]     = next_floor
            city_prog["max_floor"] = max(old_max, next_floor)
            player["max_floor"]    = max(player.get("max_floor", 1), city_prog["max_floor"])
            player["floor"]        = next_floor
            if city_prog["max_floor"] > old_max:
                from leveling import check_level_cap_milestone
                check_level_cap_milestone(player, origin_city)
            player["current_hp"] = player_max_hp(player)
            save_game(player)
            return True

    # ----- SUPER BOSS ENCOUNTER (every 20th floor, first time only) -----
    if floor % 20 == 0 and city_prog["max_floor"] <= floor:

        # ── Pandemonium Floor 20: Chrysalis override ──────────────────
        if player.get("pandemonium_mode") and floor == 20:
            _tprint("\n" + "="*50)
            _tprint("The crystalline halls fall silent. The air grows heavy —")
            _tprint("not with menace, but with age. With the weight of moments.")
            _tprint("Three hourglasses shimmer into existence around you.")
            _tprint("A cocoon beats at the center. It has been waiting.")
            _tprint("="*50)
            _tpause("Press Enter to face the Entangled One...")

            while True:
                advance_time(player, 60)
                if superboss_override:
                    result = superboss_override("chrysalis", floor)
                else:
                    result = combat_entangled_chrysalis(player, floor)

                if result == "victory":
                    _record_superboss_defeat(player, "entangled_chrysalis")
                    super_boss_exp = 800 + (floor * 60)
                    super_boss_gold = 500 + (floor * 40)
                    if player.get("pandemonium_mode"):
                        super_boss_gold = int(super_boss_gold * 2.5)
                        super_boss_exp = int(super_boss_exp * 1.5)
                    # Daily events: Lucky Day / Full Moon gold bonus
                    from events import get_daily_bonus_multiplier
                    super_boss_gold = int(super_boss_gold * get_daily_bonus_multiplier(player, "gold_bonus"))
                    player["gold"] = player.get("gold", 0) + super_boss_gold
                    _tprint(f"\n Chrysalis defeated! Bonus: +{super_boss_gold} gold, +{super_boss_exp} XP!")
                    gain_exp(player, super_boss_exp)
                    for ally in player.get("allies", []):
                        if ally.get("current_hp", 0) > 0:
                            gain_exp_ally(ally, super_boss_exp)

                    next_floor = floor + 1
                    old_max = city_prog["max_floor"]
                    city_prog["floor"]     = next_floor
                    city_prog["max_floor"] = max(old_max, next_floor)
                    player["max_floor"]    = max(player.get("max_floor", 1), city_prog["max_floor"])
                    player["floor"]        = next_floor

                    if city_prog["max_floor"] > old_max:
                        from leveling import check_level_cap_milestone
                        check_level_cap_milestone(player, origin_city)

                    player["current_hp"] = player_max_hp(player)
                    save_game(player)
                    return True
                elif result == "fled":
                    _tprint("There is no fleeing from entangled time.")
                    _tpause("Press Enter to continue the fight...")
                    continue
                elif result == "dead":
                    player.pop("pandemonium_mode", None)
                    return "dead"
                else:
                    _tprint(f"\n[ERROR: Unexpected chrysalis combat result: {result!r}]")
                    _tpause("Press Enter to continue...")
                    player.pop("pandemonium_mode", None)
                    save_game(player)
                    return True

        # ── Normal superboss pool (tiers 0-7) ────────────────────────
        _tprint("\n" + "="*50)
        _tprint("⚠️  A dark, suffocating energy fills the air...")
        
        # 1. Initialize or refill the superboss pool if it's empty or missing
        if not player.get("superboss_pool"):
            pool = [0, 1, 2, 3, 4, 5, 6, 7, 8]
            # Use seed + floor to keep the shuffle consistent per run/floor 
            # but fall back to a random seed if missing to prevent crashes
            rng = random.Random(player.get("superboss_seed", random.randint(1, 99999)) + floor)
            rng.shuffle(pool)
            player["superboss_pool"] = pool
            
        # 2. Peek at the next boss in the pool (do not remove until defeated!)
        tier = player["superboss_pool"][0]
        
        if tier == 0:
            _tprint("The walls are covered in dense, toxic cobwebs.")
        elif tier == 1:
            _tprint("Reality itself frays... distorted dream fragments float everywhere.")
        elif tier == 2:
            _tprint("Every surface becomes a mirror. You see a thousand versions of yourself — all afraid.")
        elif tier == 3:
            _tprint("The air shimmers with heat haze. The stone floor has begun to glow.")
        elif tier == 4:
            _tprint("The sky above the dungeon cracks open. Something vast descends.")
        elif tier == 5:
            _tprint("The dungeon flickers. The walls pixelate at the edges.")
            _tprint("For a moment you see fluorescent lights behind them.")
            _tprint("A man steps through the distortion — not a monster, but a human.")
            _tprint("He looks at you with tired eyes and says: 'You shouldn't be here.'")
        elif tier == 6:
            _tprint("The scent of salt and rot fills the air. A ghostly fog rolls in.")
            _tprint("From the mist, a spectral vessel emerges — tattered sails, haunted hull.")
            _tprint("You hear the creak of timbers and a distant parrot's cry...")
        elif tier == 7:
            _tprint("The dungeon falls silent. Not the silence of emptiness,")
            _tprint("but the silence of a held breath — of a room that knows")
            _tprint("something terrible is about to happen.")
            _tprint("A figure in black stands in the center. They do not speak.")
            _tprint("Nine names are stitched into their gloves.")
        elif tier == 8:
            _tprint("The corridor ahead is unfinished — walls of raw gesso,")
            _tprint("a floor sketched in charcoal. From somewhere beyond,")
            _tprint("you hear the wet drag of a brush against canvas.")
        _tprint("You have stumbled directly into a SUPER BOSS ARENA!")
        _tprint("="*50)
        _tpause("Press Enter to face the horror...")

        # Combat loop – cannot flee (if flee, restart combat)
        while True:
            advance_time(player, 60)   # time passes
            if superboss_override:
                result = superboss_override(tier, floor)
            elif tier == 0:
                result = combat_broodmother(player)
            elif tier == 1:
                result = combat_slitcurrent(player)
            elif tier == 2:
                result = combat_sylvana(player)
            elif tier == 3:
                result = combat_ignis(player)
            elif tier == 4:
                result = combat_yinglong(player)
            elif tier == 5:
                result = combat_rientrante(player)
            elif tier == 6:
                result = combat_everlong_ship(player)
            elif tier == 7:
                result = combat_black_silence(player)
            elif tier == 8:
                result = combat_palette(player)
                
            if result == "victory":
                # 3. Remove the defeated boss from the pool so it won't spawn again until reshuffled
                player["superboss_pool"].pop(0)

                _record_superboss_defeat(player, {
                    0: "broodmother_vileheart",
                    1: "dream_devouring_slitcurrent",
                    2: "queen_of_mirrors_sylvana",
                    3: "melt_forge_golem_ignis",
                    4: "heaven_banished_dragon_yinglong",
                    5: "rientrante_frostbound",
                    6: "captain_everlong_ship",
                    7: "black_silence",
                    8: "chromatic_artisan",
                }.get(tier, f"superboss_tier_{tier}"))
                
                # Reward
                super_boss_exp = 500 + (floor * 50)
                super_boss_gold = 300 + (floor * 30)
                if player.get("pandemonium_mode"):
                    super_boss_gold = int(super_boss_gold * 2.5)
                    super_boss_exp = int(super_boss_exp * 1.5)
                    _tprint("\n  Pandemonium surges — the reward is amplified!")
                # Daily events: Lucky Day / Full Moon gold bonus
                from events import get_daily_bonus_multiplier
                super_boss_gold = int(super_boss_gold * get_daily_bonus_multiplier(player, "gold_bonus"))
                player["gold"] = player.get("gold", 0) + super_boss_gold
                _tprint(f"\n Super Boss Defeated! Bonus: +{super_boss_gold} gold, +{super_boss_exp} XP!")
                gain_exp(player, super_boss_exp)
                for ally in player.get("allies", []):
                    if ally.get("current_hp", 0) > 0:
                        gain_exp_ally(ally, super_boss_exp)

                # Sync per-city progress
                next_floor = floor + 1
                old_max = city_prog["max_floor"]
                city_prog["floor"]     = next_floor
                city_prog["max_floor"] = max(old_max, next_floor)
                player["max_floor"]    = max(player.get("max_floor", 1), city_prog["max_floor"])
                player["floor"]        = next_floor

                if city_prog["max_floor"] > old_max:
                    from leveling import check_level_cap_milestone
                    check_level_cap_milestone(player, origin_city)

                # Full heal and save
                player["current_hp"] = player_max_hp(player)
                save_game(player)
                return True   # floor cleared, outer loop will handle full heal
            elif result == "spared":
                # Rientrante spared you — remove from pool but no kill reward
                player["superboss_pool"].pop(0)
                _tprint("\n  Rientrante spared you. The encounter ends.")
                # Full heal and save
                player["current_hp"] = player_max_hp(player)
                save_game(player)
                return True
            elif result == "fled":
                _tprint("You cannot flee from a milestone Super Boss!")
                _tpause("Press Enter to continue the fight...")
                continue
            elif result == "dead":
                player.pop("pandemonium_mode", None)
                return "dead"
            else:
                # error, timeout, or unknown — return safely without death penalty
                _tprint(f"\n  The fight was interrupted (result: {result}). Returning to safety...")
                _tpause("Press Enter to continue...")
                player.pop("pandemonium_mode", None)
                save_game(player)
                return True

    # ----- NORMAL FLOORS (non‑milestone) -----
    # Set floor for downstream handlers
    player["floor"] = floor

    # Check for saved room progress on this floor
    saved_floor = player.get("saved_dungeon_floor")
    saved_rooms = player.get("saved_dungeon_rooms")
    saved_idx   = player.get("saved_dungeon_room_index", 0)

    # ── Validate the saved state before trusting it ──────────────────
    restore_ok = (
        saved_floor == floor
        and isinstance(saved_rooms, list)
        and len(saved_rooms) == 10  # every floor has exactly 10 rooms
        and isinstance(saved_idx, int)
        and 0 <= saved_idx < 10
    )
    if not restore_ok:
        # Wipe invalid saved state so it doesn't poison future runs
        for _key in ("saved_dungeon_floor", "saved_dungeon_rooms", "saved_dungeon_room_index"):
            player.pop(_key, None)

    if restore_ok:
        rooms = saved_rooms
        start_room = saved_idx
        if start_room > 0:
            _tprint("\n" + "─" * 50)
            _tprint(f"  RESUMING {dungeon_display} DUNGEON – FLOOR {floor}")
            _tprint(f"  Continuing from Room {start_room + 1}...")
            _tprint("─" * 50)
            _tpause("Press Enter to continue...")
    else:
        _tprint(f"\n=== DESCENDING INTO {dungeon_display} DUNGEON – FLOOR {floor} ===")
        _tpause("Press Enter to begin...")
        rooms = generate_floor(floor, region=region, player=player)
        start_room = 0
        player["_dungeon_log"] = []  # Clear dungeon log for new floor
        player["saved_dungeon_floor"] = floor
        player["saved_dungeon_rooms"] = rooms
        player["saved_dungeon_room_index"] = 0

    total_rooms = len(rooms)
    explored = set(range(start_room))

    # ── Pandemonium: roll / display floor curse ──────────────────────────
    if player.get("pandemonium_mode"):
        if start_room == 0:
            # New floor — roll a fresh curse
            curse_msg = apply_curse_on_floor_start(player, floor)
            _tprint(curse_msg)
            _tpause("Press Enter to acknowledge the curse...")
        else:
            # Resuming — show active curse
            curse_line = format_active_curse_line(player)
            if curse_line:
                _tprint(f"\n  Active Pandemonium Curse:")
                _tprint(curse_line)
                _tpause()
        # ── Push curse info to the GUI top bar ─────────────────────────
        curse = get_curse(player)
        if curse:
            t = _term()
            if t:
                t.set_curse_bar(floor, curse.get("name", ""),
                                curse.get("icon", "☠️"),
                                curse.get("tier_name", ""))

    # ── Wonderland: roll / display floor quirk ──────────────────────────
    if region == "wonderland":
        if start_room == 0:
            quirk_msg = apply_wonderland_quirk_on_floor_start(player, floor)
            _tprint(quirk_msg)
            _tpause("Press Enter to embrace the whimsy...")
        else:
            quirk_line = format_active_wl_quirk_line(player)
            if quirk_line:
                _tprint(f"\n  Active Wonderland Whimsy:")
                _tprint(quirk_line)
                _tpause()
        # ── Push quirk info to the GUI top bar ─────────────────────────
        quirk_summary = format_quirk_summary(player)
        t = _term()
        if t:
            t.set_quirk_bar(floor, quirk_summary, "Wonderland")

        # ── Wonderland Shadow choice (Floors 41-49) ─────────────────────
        if start_room == 0 and floor in SHADOW_CHOICE_FLOORS and floor != 50:
            if floor == 46 or floor == 50:
                # Floor 46 & 50: clear all shadows, then pick fresh
                clear_all_shadows(player)
                if floor == 46:
                    _tprint("\n  🌑 The slate is wiped clean. Wonderland's darkness deepens...")
                else:
                    _tprint("\n  🌑 The Author's study awaits. Wonderland makes its final demand...")
                _tpause("Press Enter to face the growing darkness...")
                shadow_msg = trigger_shadow_choice(player, floor, term_func=_term, count=2)
                _tprint(shadow_msg)
                _tpause("Press Enter to continue...")
            elif 41 <= floor <= 45:
                # Floors 41-45: pick 1 shadow per floor (stack)
                shadow_msg = trigger_shadow_choice(player, floor, term_func=_term, count=1)
                _tprint(shadow_msg)
                _tpause("Press Enter to continue...")
            elif 47 <= floor <= 49:
                # Floors 47-49: pick 2 shadows per floor (stack)
                shadow_msg = trigger_shadow_choice(player, floor, term_func=_term, count=2)
                _tprint(shadow_msg)
                _tpause("Press Enter to continue...")

        # ── Show active Shadows ──────────────────────────────────────────
        shadow_line = format_active_shadows_line(player)
        if shadow_line:
            _tprint("\n  🌑 ACTIVE SHADOWS:")
            _tprint(shadow_line)
            _tpause()
        # ── Push updated quirk+shadow info to the GUI top bar ──────────
        quirk_summary = format_quirk_summary(player)
        t = _term()
        if t:
            t.set_quirk_bar(floor, quirk_summary, "Wonderland")

    # ── Initial map render before the first room ─────────────────────────
    map_str = dungeon_rooms.render_ascii_map(rooms, explored, -1, floor, player=player)
    if not _term():
        _tprint(map_str)
    party_str = dungeon_rooms.render_party_status(player)
    if not _term():
        _tprint(party_str)
        _tpause()

    for i, room in enumerate(rooms[start_room:], start=start_room):
        room_type = room.get("type", "combat")

        # ── Room border ──────────────────────────────────────────────────
        _tprint("\n" + "═" * 50)
        if room.get("is_boss"):
            _tprint("  *** BOSS ROOM ***")
        else:
            room_label = get_room_labels(region).get(room_type, f"--- Room {i+1} ---")
            _tprint(f"  {room_label}")
        _tprint("═" * 50)
        _tpause("Press Enter to enter the room...")

        # ── Pandemonium: Sapping Aura room-entry damage ──────────────────
        if player.get("pandemonium_mode"):
            sap_dmg = apply_room_entry_damage(player)
            if sap_dmg > 0:
                _tprint(f"\n  💀 The Sapping Aura drains {sap_dmg} HP from your party!")
                if player["current_hp"] <= 1:
                    _tprint("  You collapse from the relentless corruption...")
                    player.pop("pandemonium_mode", None)
                    player["cutlass_high_tide_stacks"] = 0
                    player.pop("cutlass_high_tide_floor", None)
                    return "dead"

        # ── Wonderland: Curiosity Boost random stat buff ─────────────────
        if region == "wonderland":
            boost_val = get_curiosity_boost_value(player)
            if boost_val > 0:
                from resources.races_classes import ATTRIBUTES
                import random as _random
                pool = [player] + [a for a in player.get("allies", []) if a.get("current_hp", 0) > 0]
                if pool:
                    target = _random.choice(pool)
                    stat = _random.choice(list(ATTRIBUTES))
                    target.setdefault("active_buffs", []).append({
                        "stat": stat,
                        "value": int(boost_val),
                        "remaining": 1,
                        "type": "wonderland_curiosity",
                    })
                    _tprint(f"\n  🍄 Curiosity sweeps over {target['name']} — +{int(boost_val)} {stat} for this room!")

        # ── Wonderland Shadow: Jabberwock's Wrath room damage ────────────
        if region == "wonderland":
            wrath_dmg = get_shadow_room_damage(player)
            if wrath_dmg > 0:
                player["current_hp"] = max(1, player["current_hp"] - wrath_dmg)
                _tprint(f"\n  🔥 The Jabberwock's flames sear you for {wrath_dmg} damage!")
                if player["current_hp"] <= 1:
                    _tprint("  You collapse from the relentless flames...")
                    player.pop("pandemonium_mode", None)
                    player["cutlass_high_tide_stacks"] = 0
                    player.pop("cutlass_high_tide_floor", None)
                    return "dead"

        # ── Wonderland Shadow: Madness Contagion stat penalty ────────────
        if region == "wonderland":
            madness_penalty = get_shadow_stat_penalty(player)
            if madness_penalty > 0:
                from resources.races_classes import ATTRIBUTES
                pool = [player] + [a for a in player.get("allies", []) if a.get("current_hp", 0) > 0]
                if pool:
                    target = random.choice(pool)
                    stat = random.choice(list(ATTRIBUTES))
                    target.setdefault("active_debuffs", []).append({
                        "stat": stat,
                        "value": int(madness_penalty),
                        "remaining": 1,
                        "type": "wonderland_madness",
                    })
                    _tprint(f"\n  🎭 Madness clouds {target['name']}'s mind — -{int(madness_penalty)} {stat} for this room!")

        # ── Arcane Blessing room consumption ─────────────────────────────
        from facilities.arcane_tower import consume_arcane_blessing_room
        consume_arcane_blessing_room(player)

        # Advance time by 1 hour per room
        advance_time(player, 60)

        while True:

            if room_type == "combat":
                if combat_override:
                    result = combat_override(player, room["enemies"], floor=floor, room_num=i+1, total_rooms=total_rooms)
                else:
                    result = combat(player, room["enemies"], floor=floor, room_num=i+1, total_rooms=total_rooms)

                if result == "victory":
                    pandemonium = player.get("pandemonium_mode", False)
                    _tprint("\n--- Room Victory Rewards ---")
                    for enemy_key in room["enemies"]:
                        enemy_level = ENEMIES[enemy_key]["level"]
                        gain_exp(player, enemy_level * 12)
                        for ally in player.get("allies", []):
                            if ally.get("current_hp", 0) > 0:
                                gain_exp_ally(ally, enemy_level * 12)
                        add_drop_to_inventory(player, enemy_level, pandemonium=pandemonium)
                        add_gold_drop(player, enemy_key, pandemonium=pandemonium)
                        
                        # BOUNTY TRACKING:
                        if "active_bounties" in player:
                            for b in player["active_bounties"]:
                                if b["target_enemy"] == enemy_key and b["current"] < b["required"]:
                                    b["current"] += 1
                                    if b["current"] == b["required"]:
                                        _tprint(f"★ Bounty objective complete: Hunt {b['required']} {b['target_name']}!")

                    # ── Wonderland: Mad Hatter's Gift extra drop ─────────
                    hatter_chance = get_mad_hatter_drop_chance(player)
                    if hatter_chance > 0 and random.random() < hatter_chance:
                        avg_level = sum(ENEMIES[e]["level"] for e in room["enemies"]) // len(room["enemies"])
                        extra_drop = add_drop_to_inventory(player, avg_level, pandemonium=False)
                        if extra_drop:
                            _tprint("  🎁 The Mad Hatter left a most unbirthday-ish gift!")
                    # ───────────────────────────────────────────────────────

                    # Heal after victory
                    heal = random.randint(1, 5) + player_con_mod(player)
                    # Pandemonium: Blighted Recovery curse reduces healing
                    heal = apply_healing_reduction(player, heal)
                    # Wonderland: Tea Party Regen boosts healing
                    heal = apply_tea_party_regen(player, heal)
                    # Wonderland Shadow: Looking Glass Shatter reduces healing
                    shadow_heal_reduce = get_shadow_healing_reduction(player)
                    if shadow_heal_reduce > 0:
                        heal = max(1, int(heal * (1.0 - shadow_heal_reduce)))
                    player["current_hp"] = min(
                        player["current_hp"] + heal,
                        player_max_hp(player)
                    )
                    _tprint(f"\nYou catch your breath and recover {heal} HP.")

                    # Heal allies too
                    for ally in player.get("allies", []):
                        if ally.get("current_hp", 0) > 0:
                            ally_heal = random.randint(1, 3) + ally["attributes"].get("Constitution", 0)
                            ally_heal = apply_healing_reduction(player, ally_heal)
                            ally_heal = apply_tea_party_regen(player, ally_heal)
                            if shadow_heal_reduce > 0:
                                ally_heal = max(1, int(ally_heal * (1.0 - shadow_heal_reduce)))
                            ally["current_hp"] = min(ally["current_hp"] + ally_heal, ally["max_hp"])
                            _tprint(f"  {ally['name']} recovers {ally_heal} HP.")

                    # Wedding end-of-combat rewards
                    from combat.weapon.wedding_specials import apply_wedding_combat_end
                    apply_wedding_combat_end(player, victory=True)

                    break

                elif result == "fled":
                    _tprint("You flee from the dungeon and return to the city.")
                    # No input() wait in GUI mode; the flee message is auto-dismissed
                    if not _term():
                        input("Press Enter to continue...")
                    origin = player.get("origin_city", "solmere")
                    player["location"] = origin
                    player.pop("pandemonium_mode", None)
                    # Reset High Tide when leaving dungeon
                    player["cutlass_high_tide_stacks"] = 0
                    player.pop("cutlass_high_tide_floor", None)
                    # Clear Wonderland state
                    clear_wonderland_quirk(player)
                    clear_all_shadows(player)
                    return "fled"
                elif result == "dead":
                    _tprint("Your adventure ends here...")
                    player.pop("pandemonium_mode", None)
                    # Reset High Tide on death
                    player["cutlass_high_tide_stacks"] = 0
                    player.pop("cutlass_high_tide_floor", None)
                    # Clear Wonderland state
                    clear_wonderland_quirk(player)
                    clear_all_shadows(player)
                    return "dead"
                elif result == "timeout":
                    _tprint("\n[ERROR: Combat timed out — returning to city.]")
                    # Same cleanup as fleeing
                    if not _term():
                        input("Press Enter to continue...")
                    origin = player.get("origin_city", "solmere")
                    player["location"] = origin
                    player.pop("pandemonium_mode", None)
                    player["cutlass_high_tide_stacks"] = 0
                    player.pop("cutlass_high_tide_floor", None)
                    clear_wonderland_quirk(player)
                    clear_all_shadows(player)
                    return "timeout"

            else:
                # Non-combat room
                if room_type == "fountain":
                    result = handle_fountain_room(player, floor)
                elif room_type == "merchant":
                    result = handle_merchant_room(player, floor)
                elif room_type == "treasure":
                    result = handle_treasure_room(player, floor)
                elif room_type == "trap":
                    result = handle_trap_room(player, floor)
                elif room_type == "stat_check":
                    result = handle_stat_check_room(player, floor, room["event"], combat_override=combat_override)
                else:
                    result = "continue"

                if result == "dead":
                    player.pop("pandemonium_mode", None)
                    # Reset High Tide on death
                    player["cutlass_high_tide_stacks"] = 0
                    player.pop("cutlass_high_tide_floor", None)
                    # Clear Wonderland state
                    clear_wonderland_quirk(player)
                    clear_all_shadows(player)
                    return "dead"
                elif result == "fled":
                    _tprint("You flee from the dungeon and return to the city.")
                    if not _term():
                        input("Press Enter to continue...")
                    origin = player.get("origin_city", "solmere")
                    player["location"] = origin
                    player.pop("pandemonium_mode", None)
                    # Reset High Tide when leaving dungeon
                    player["cutlass_high_tide_stacks"] = 0
                    player.pop("cutlass_high_tide_floor", None)
                    # Clear Wonderland state
                    clear_wonderland_quirk(player)
                    clear_all_shadows(player)
                    return "fled"
                
                break

            # Increment wedding bark_shield room counter
            player["wedding_bark_shield_room_count"] = player.get("wedding_bark_shield_room_count", 0) + 1

        # Update saved progress so reloads resume from the next room
        player["saved_dungeon_room_index"] = i + 1

        # Post-room menu (combat and non-combat both get this)
        while True:
            t = _term()
            if t:
                # GUI mode: show buttons
                choice = t.menu(
                    ["Continue", "Inventory / Stats", "Save and quit"],
                    prompt="What would you like to do?",
                    allow_cancel=False,
                )
                if choice == 0:  # Continue
                    break
                elif choice == 1:  # Inventory/Stats
                    t.open_inventory()
                    continue
                elif choice == 2:  # Save and quit
                    # Clear run-only flags BEFORE saving so they never persist
                    # into the save file (they are re-set on dungeon entry).
                    player.pop("pandemonium_mode", None)
                    player["cutlass_high_tide_stacks"] = 0
                    player.pop("cutlass_high_tide_floor", None)
                    save_game(player)
                    _tprint("Game saved. Exiting to menu.")
                    # Clear Wonderland state — preserved shadows will restore on reload via save
                    clear_wonderland_quirk(player)
                    return "save_exit"
            else:
                # Terminal mode
                print("\n[Enter] to continue  [I]nventory/Stats  [S]ave and quit")
                cmd = input().strip().lower()
                if cmd == "":
                    break
                elif cmd == "i":
                    print("Inventory management is only available in GUI mode. Please use the launcher.")
                    continue
                elif cmd == "s":
                    # Clear run-only flags BEFORE saving so they never persist
                    # into the save file (they are re-set on dungeon entry).
                    player.pop("pandemonium_mode", None)
                    # Reset High Tide when leaving dungeon
                    player["cutlass_high_tide_stacks"] = 0
                    player.pop("cutlass_high_tide_floor", None)
                    save_game(player)
                    print("Game saved. Exiting to menu.")
                    return "save_exit"
                else:
                    continue

        # Mark room explored and show ASCII map
        explored.add(i)
        # Use qualified module reference so GUI patching works
        map_str = dungeon_rooms.render_ascii_map(rooms, explored, i, floor, player=player)
        if not _term():
            _tprint(map_str)
        party_str = dungeon_rooms.render_party_status(player)
        if not _term():
            _tprint(party_str)
            _tpause()

        # ── Tick room-based buffs (well_rested) after every room ─────────────────
        if player.get("active_buffs"):
            expired = []
            for buff in player.get("active_buffs", [])[:]:
                if buff.get("type") == "well_rested":
                    buff["remaining"] -= 1
                    if buff["remaining"] <= 0:
                        player["active_buffs"].remove(buff)
                        expired.append("well-rested buff")
            if expired:
                _tprint(f"\nYour {', '.join(expired)} wears off as you move deeper.")

        for ally in player.get("allies", []):
            if ally.get("active_buffs"):
                for buff in ally.get("active_buffs", [])[:]:
                    if buff.get("type") == "well_rested":
                        buff["remaining"] -= 1
                        if buff["remaining"] <= 0:
                            ally["active_buffs"].remove(buff)
                            _tprint(f"  {ally['name']}'s well-rested buff wears off.")

    # Floor cleared (normal)
    # Wipe saved dungeon state so the next floor starts fresh
    for _key in ("saved_dungeon_floor", "saved_dungeon_rooms", "saved_dungeon_room_index"):
        player.pop(_key, None)

    # ── Tick floor-based buffs (floor_buff only) ───────────────────────────────
    if player.get("active_buffs"):
        expired = []
        for buff in player.get("active_buffs", [])[:]:
            if buff.get("type") == "floor_buff":
                buff["remaining"] -= 1
                if buff["remaining"] <= 0:
                    player["active_buffs"].remove(buff)
                    stat = buff.get("stat", "all")
                    if stat == "all":
                        expired.append("floor buff")
                    else:
                        expired.append(f"{stat} buff")
        if expired:
            _tprint(f"\nYour {', '.join(expired)} wears off as you transition floors.")

    # Tick ally floor-based buffs
    for ally in player.get("allies", []):
        if ally.get("active_buffs"):
            for buff in ally.get("active_buffs", [])[:]:
                if buff.get("type") == "floor_buff":
                    buff["remaining"] -= 1
                    if buff["remaining"] <= 0:
                        ally["active_buffs"].remove(buff)
                        _tprint(f"  {ally['name']}'s {buff.get('stat', 'floor')} buff wears off.")

    # Remove blessings
    if player.get("active_buffs"):
        orig_len = len(player["active_buffs"])
        player["active_buffs"] = [b for b in player["active_buffs"] if b.get("type") != "blessing"]
        if len(player["active_buffs"]) < orig_len:
            _tprint("\nYour divine temple blessing has worn off as you transition floors.")
    if player.get("training_buff"):
        player["training_buff"]["expires_after"] -= 1
        if player["training_buff"]["expires_after"] <= 0:
            del player["training_buff"]
            _tprint("\nYour barracks training exhaustion catches up to you. The strength buff has worn off.")

    # ── Sync per-city floor progress ────────────────────────────────────────
    # Advance the city record to the next floor.  main.py will also do
    # player["floor"] += 1, but we mirror it here so city_prog stays in sync
    # whether control returns through main.py or any other path.
    next_floor = floor + 1
    old_max = city_prog["max_floor"]
    city_prog["floor"]     = next_floor
    city_prog["max_floor"] = max(old_max, next_floor)
    player["max_floor"]    = max(player.get("max_floor", 1), city_prog["max_floor"])
    player["floor"]        = next_floor

    if city_prog["max_floor"] > old_max:
        from leveling import check_level_cap_milestone
        check_level_cap_milestone(player, origin_city)

    # ── Isle of Glass Floor 10: guaranteed Glass Anchor key item ─────────
    if origin_city == "isle_of_glass" and floor == 10 and old_max <= 10:
        _grant_glass_anchor(player)

    # Advance time by 1 hour for floor completion
    current_time = advance_time(player, 60)

    # ── Pandemonium: include active curse in the floor-clear summary ─────
    curse = get_curse(player)
    if curse:
        _tprint(f"Current time: {current_time} | Gold: {player.get('gold', 0)} | {curse.get('icon', '☠️')} {curse.get('name', '')}")
    else:
        _tprint(f"Current time: {current_time} | Gold: {player.get('gold', 0)}")

    player["current_hp"] = player_max_hp(player)

    # Fully heal all allies on floor clear
    for ally in player.get("allies", []):
        ally["current_hp"] = ally["max_hp"]

    save_game(player)
    # NOTE: pandemonium_mode is intentionally NOT cleared here.
    # It persists across floors so curses continue to apply.
    # It is only cleared on death, flee, or save_exit.
    return True