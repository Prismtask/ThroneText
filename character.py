from resources.races_classes import RACES, CLASSES, ATTRIBUTES, TOTAL_POINTS
from save_load import save_game, list_saves, get_next_free_slot
from utils import clear_screen
import random

# ══════════════════════════════════════════════════════════════════════════════
# Vorpal skill reconciliation — ensures heroine innate/learned skills stay in
# sync with the vorpal flags across save/load cycles.
# ══════════════════════════════════════════════════════════════════════════════

# Mapping: heroine_key → (vorpal_flag, innate_skills, original_innate_key,
#                         equipped_weapon_ids, upgrade_flag, upgrade_skill, upgraded_flag)
_VORPAL_RECONCILE_CONFIG = {
    "alice": {
        "vorpal_flag": "_alice_vorpal_skills",
        "vorpal_innate": ["vorpal_edge", "snicker_snack"],
        "original_innate_key": "_alice_original_innate",
        "weapon_ids": ("vorpal_blade_rusted", "vorpal_blade"),
        "upgrade_flag": "wl_godmother_blade_upgraded",
        "upgrade_skill": "frabjous_day",
        "upgraded_flag": "_alice_vorpal_upgraded",
    },
    "red_hood": {
        "vorpal_flag": "_redhood_vorpal_skills",
        "vorpal_innate": ["what_big_teeth", "fell_the_wolf"],
        "original_innate_key": "_redhood_original_innate",
        "weapon_ids": ("woodcutters_broken_axe", "grandmothers_axe"),
        "upgrade_flag": "wl_woodcutter_axe_upgraded",
        "upgrade_skill": "through_the_forest",
        "upgraded_flag": "_redhood_vorpal_upgraded",
    },
    "dorothy": {
        "vorpal_flag": "_dorothy_vorpal_skills",
        "vorpal_innate": ["cyclones_call", "heart_of_tin"],
        "original_innate_key": "_dorothy_original_innate",
        "weapon_ids": ("silver_slippers", "ruby_slippers"),
        "upgrade_flag": "wl_wizard_slippers_upgraded",
        "upgrade_skill": "emerald_citys_light",
        "upgraded_flag": "_dorothy_vorpal_upgraded",
    },
}


def _reconcile_heroine_vorpal_skills(ally, player):
    """Ensure a heroine's innate/learned skills match the vorpal swap state.

    Called from ensure_player_fields() on every game load.  Fixes three
    classes of inconsistency that can arise across save cycles:

    1.  Flag is true but innate_skills weren't swapped → force the swap.
    2.  Flag is false but vorpal weapon is equipped → trigger the swap.
    3.  Facility upgrade flag is true but the upgrade skill never made it
        into learned_skills → inject it now.
    """
    hk = ally.get("_heroine_key", "")
    cfg = _VORPAL_RECONCILE_CONFIG.get(hk)
    if cfg is None:
        return

    vorpal_flag = cfg["vorpal_flag"]
    vorpal_innate = cfg["vorpal_innate"]
    original_key = cfg["original_innate_key"]
    weapon_ids = cfg["weapon_ids"]
    upgrade_flag = cfg["upgrade_flag"]
    upgrade_skill = cfg["upgrade_skill"]
    upgraded_flag = cfg["upgraded_flag"]

    # Detect whether the vorpal weapon is equipped (any slot)
    weapon_equipped = any(
        slot_item and slot_item.get("id") in weapon_ids
        for slot_item in ally.get("equipped", {}).values()
        if slot_item
    )

    # ── Case 1 & 2: ensure innate_skills match the vorpal state ──────────
    if ally.get(vorpal_flag) or weapon_equipped:
        current_innate = ally.get("innate_skills", [])
        if current_innate != vorpal_innate:
            # Save the current innates as "original" so reverting the swap
            # later can restore them correctly.
            if not ally.get(original_key):
                ally[original_key] = list(current_innate)
            ally["innate_skills"] = list(vorpal_innate)
            ally["skill_cooldowns"] = {}
        ally[vorpal_flag] = True

    # ── Case 3: grant the facility-upgrade skill if missing ──────────────
    if player.get(upgrade_flag):
        learned = ally.setdefault("learned_skills", [])
        if upgrade_skill not in learned:
            learned.append(upgrade_skill)
        ally[upgraded_flag] = True


def ensure_player_fields(player):
    """Ensure loaded saves have all required fields for new systems."""
    player.setdefault("skills", [])
    player.setdefault("skill_cooldowns", {})
    player.setdefault("skill_mastery", {})
    player.setdefault("passive_unlocked", True)
    player.setdefault("berserk_turns", 0)
    player.setdefault("bloodlust_turns", 0)
    player.setdefault("mount_id", None)
    player.setdefault("level_cap", 10)
    player.setdefault("ascension_notified", {})
    player.setdefault("inventory_upgrade", 0)
    player.setdefault("party_order", [])  # Track front/back row order
    from combat.skills import unlock_skills_for_level
    unlock_skills_for_level(player)

    # Ensure elemental fields for new saves
    if "elemental_res" not in player or "elemental_dmg" not in player:
        from combat.elemental import compute_player_elemental
        res, dmg = compute_player_elemental(player)
        player["elemental_res"] = res
        player["elemental_dmg"] = dmg

    # Migrate old saves: ensure physical/magical keys exist in elemental profiles
    from combat.elemental import ELEMENTS
    for el in ELEMENTS:
        player.setdefault("elemental_res", {})[el] = player["elemental_res"].get(el, 1.0)
        player.setdefault("elemental_dmg", {})[el] = player["elemental_dmg"].get(el, 1.0)

    # Migrate old single-accessory slot to dual accessory slots
    equipped = player.get("equipped", {})
    if "accessory" in equipped:
        player["equipped"]["accessory1"] = equipped.pop("accessory")
        player["equipped"]["accessory2"] = None
    for slot in ["weapon", "armor", "accessory1", "accessory2"]:
        if slot not in player.get("equipped", {}):
            player.setdefault("equipped", {})[slot] = None

    player.setdefault("daily_effects", {})
    player.setdefault("event_queue", [])

    # Engagement / wedding system fields
    player.setdefault("girl_talk_today", {})
    player.setdefault("girl_gift_today", {})
    player.setdefault("girl_daily_last_day", 0)
    player.setdefault("engaged_girls", [])
    player.setdefault("married_girls", [])

    # Clean up leftover combat-only state that may be non-serializable
    for _key in ("gloves_workshop_used", "gloves_furioso_available", "gloves_first_strike_active"):
        player.pop(_key, None)

    # Captain's Cutlass state
    player.setdefault("cutlass_high_tide_stacks", 0)
    player.setdefault("cutlass_high_tide_floor", None)
    player.setdefault("cutlass_rally_cooldown", 0)
    player.setdefault("cutlass_rally_active", False)
    player.setdefault("cutlass_rally_turns", 0)
    player.setdefault("cutlass_riposte_count", 0)
    player.setdefault("potion_sickness", 0)  # turns remaining before another consumable can be used
    player.setdefault("wonderland_shadows", [])  # persistent Wonderland shadow choices (floor 41+)

    # Ensure ally and house girl fields for leveling system
    for ally in player.get("allies", []):
        # Clean up leftover combat-only state
        for _key in ("gloves_workshop_used", "gloves_furioso_available", "gloves_first_strike_active"):
            ally.pop(_key, None)
        ally.setdefault("exp", 0)
        ally.setdefault("level_hp_bonus", 0)
        ally.setdefault("level_cap", 10)
        ally.setdefault("defeated", False)
        ally.setdefault("cursed", False)
        ally.setdefault("dreaded", False)
        ally.setdefault("silenced", False)
        ally.setdefault("affection_cap", 100)
        ally.setdefault("engaged", False)
        ally.setdefault("married", False)
        ally.setdefault("learned_skills", [])
        ally.setdefault("learning", None)
        ally.setdefault("skill_cooldowns", {})
        ally.setdefault("skill_mastery", {})
        if "elemental_res" not in ally or "elemental_dmg" not in ally:
            from combat.elemental import compute_ally_elemental
            res, dmg = compute_ally_elemental(ally)
            ally["elemental_res"] = res
            ally["elemental_dmg"] = dmg
        # Migrate old saves: ensure physical/magical keys exist in ally profiles
        for el in ELEMENTS:
            ally.setdefault("elemental_res", {})[el] = ally["elemental_res"].get(el, 1.0)
            ally.setdefault("elemental_dmg", {})[el] = ally["elemental_dmg"].get(el, 1.0)
        # Migrate old ally accessory slot
        ally_equipped = ally.get("equipped", {})
        if "accessory" in ally_equipped:
            ally["equipped"]["accessory1"] = ally_equipped.pop("accessory")
            ally["equipped"]["accessory2"] = None
        for slot in ["weapon", "armor", "accessory1", "accessory2"]:
            if slot not in ally.get("equipped", {}):
                ally.setdefault("equipped", {})[slot] = None

        # ── Reconcile vorpal skill swaps for Wonderland heroines ──────────
        # Ensures innate_skills / learned_skills match the vorpal flags even if
        # a previous save cycle lost the swap (e.g. facility upgrade ran but
        # grant_*_upgrade_skill was never persisted).
        _reconcile_heroine_vorpal_skills(ally, player)

    # Also reconcile any benched Wonderland heroines
    for ally in player.get("wonderland_benched_allies", []):
        _reconcile_heroine_vorpal_skills(ally, player)

    for house in player.get("houses", {}).values():
        for girl in house.get("monster_girls", []):
            girl.setdefault("exp", 0)
            girl.setdefault("level_hp_bonus", 0)
            girl.setdefault("level_cap", 10)
            girl.setdefault("affection_cap", 100)
            girl.setdefault("engaged", False)
            girl.setdefault("married", False)
            girl.setdefault("learned_skills", [])
            girl.setdefault("learning", None)
            girl.setdefault("skill_cooldowns", {})
            girl.setdefault("skill_mastery", {})


def player_max_hp(player_or_attrs):
    """Improved HP formula."""
    if isinstance(player_or_attrs, dict) and "attributes" in player_or_attrs:
        attrs = player_or_attrs["attributes"]
        bonus = player_or_attrs.get("level_hp_bonus", 0)
        base = 15 + attrs["Constitution"] * 3 + bonus
        # Wedding max HP bonus (matriarchs_embrace)
        from combat.wedding_specials import apply_wedding_max_hp_bonus
        return base + apply_wedding_max_hp_bonus(player_or_attrs)
    else:
        attrs = player_or_attrs
        bonus = 0
        return 15 + attrs["Constitution"] * 3 + bonus


def allocate_points(base_attributes, remaining=None):
    """Fixed point allocation - handles negative base values and 0 remaining points."""
    temp = base_attributes.copy()
    remaining = TOTAL_POINTS if remaining is None else remaining

    while remaining > 0:
        print(f"\nYou have {remaining} points to distribute.")
        for attr in ATTRIBUTES:
            if remaining == 0:
                break
            while True:
                print(f"Remaining points: {remaining}")
                val = input(f"{attr} (current {temp[attr]}): ").strip()

                if val == "" or val.lower() == "skip":
                    if remaining == 0 or temp[attr] >= 0:
                        print(f"{attr} remains at {temp[attr]}.")
                        break
                    print(f"You must bring {attr} to at least 0.")
                    continue

                try:
                    pts = int(val)
                    if pts < 0:
                        print("Points cannot be negative.")
                        continue
                    if pts > remaining:
                        print(f"You only have {remaining} points left.")
                        continue

                    new_val = temp[attr] + pts
                    if new_val < 0:
                        print("Attribute cannot go below 0.")
                        continue

                    temp[attr] = new_val
                    remaining -= pts
                    break
                except ValueError:
                    print("Please enter an integer or press Enter to skip.")

    return temp


def build_character(race_key, class_key, final_attrs, name, slot):
    """
    Pure function: build a complete player dict from creation choices.
    No I/O — returns the player dict ready to be saved.
    """
    from combat.elemental import neutral_profile, merge_profiles

    race_res = merge_profiles(neutral_profile(), RACES[race_key].get("elemental_res", {}))
    race_dmg = merge_profiles(neutral_profile(), RACES[race_key].get("elemental_dmg", {}))
    class_res = merge_profiles(neutral_profile(), CLASSES[class_key].get("elemental_res", {}))
    class_dmg = merge_profiles(neutral_profile(), CLASSES[class_key].get("elemental_dmg", {}))

    base_res = {}
    base_dmg = {}
    from combat.elemental import ELEMENTS
    for el in ELEMENTS:
        base_res[el] = max(0.0, min(2.0, race_res[el] + class_res[el] - 1.0))
        base_dmg[el] = max(0.0, min(2.0, race_dmg[el] + class_dmg[el] - 1.0))

    player = {
        "name": name,
        "race": RACES[race_key]["name"],
        "class": CLASSES[class_key]["name"],
        "attributes": final_attrs,
        "city_floors": {
            "solmere": {"floor": 1, "max_floor": 1}
        },
        "current_hp": player_max_hp(final_attrs),
        "level": 1,
        "level_cap": 10,
        "exp": 0,
        "level_hp_bonus": 0,
        "inventory": [],
        "equipped": {"weapon": None, "armor": None, "accessory1": None, "accessory2": None},
        "active_buffs": [],
        "save_slot": slot,
        "dungeon_time": 0,
        "gold": 100,
        "time_minutes": 8 * 60,
        "location": "solmere",
        "superboss_seed": random.randint(1, 999999),
        "allies": [],
        "skills": [],
        "skill_cooldowns": {},
        "skill_mastery": {},
        "passive_unlocked": True,
        "ascension_notified": {},
        "elemental_res": base_res,
        "elemental_dmg": base_dmg,
        "mount_id": None,
        "inventory_upgrade": 0,
        "girl_talk_today": {},
        "girl_gift_today": {},
        "girl_daily_last_day": 0,
        "engaged_girls": [],
        "married_girls": [],
    }
    return player


def create_character():
    """Full new-game character creation (terminal interactive mode)."""
    clear_screen()
    print("=== New Game ===")

    # Race
    print("\nChoose your race:")
    for k, v in RACES.items():
        print(f"  {k}. {v['name']} - {v['desc']}")
    race_key = input("Enter number: ").strip()
    while race_key not in RACES:
        race_key = input("Invalid, choose again: ").strip()
    race_mods = RACES[race_key]["mods"]

    # Class
    print("\nChoose your class:")
    for k, v in CLASSES.items():
        print(f"  {k}. {v['name']} - {v['desc']}")
    class_key = input("Enter number: ").strip()
    while class_key not in CLASSES:
        class_key = input("Invalid, choose again: ").strip()
    class_mods = CLASSES[class_key]["mods"]

    # Base attributes
    base_attrs = {attr: 0 for attr in ATTRIBUTES}
    for attr, mod in race_mods.items():
        base_attrs[attr] += mod
    for attr, mod in class_mods.items():
        base_attrs[attr] += mod

    print("\nBase attributes after race & class:")
    for attr in ATTRIBUTES:
        print(f"{attr}: {base_attrs[attr]}")

    final_attrs = allocate_points(base_attrs)

    name = input("\nName your protagonist: ").strip()
    while not name:
        name = input("Name cannot be empty: ").strip()

    # Choose save slot
    print("\nSave slots available:")
    saves = list_saves()
    for slot, save_name in saves.items():
        print(f"  Slot {slot}: {save_name}")
    next_free = get_next_free_slot()
    print(f"  Slot {next_free}: (new)")

    while True:
        try:
            slot_str = input(f"Enter save slot number (new: {next_free}): ").strip()
            slot = int(slot_str) if slot_str else next_free
            if slot < 1:
                print("Slot must be a positive integer.")
                continue
            if slot in saves:
                overwrite = input(f"Slot {slot} already contains '{saves[slot]}'. Overwrite? (y/n): ").strip().lower()
                if overwrite != 'y':
                    continue
            break
        except ValueError:
            print("Please enter a number.")

    player = build_character(race_key, class_key, final_attrs, name, slot)
    save_game(player)
    print(f"\nCharacter '{name}' created and saved.")
    input("Press Enter to begin your dungeon adventure...")
    return player
