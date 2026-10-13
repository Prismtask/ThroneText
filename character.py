from resources.races_classes import RACES, CLASSES, ATTRIBUTES, TOTAL_POINTS
from save_load import save_game, list_saves, get_next_free_slot
from utils import clear_screen
import random

# ══════════════════════════════════════════════════════════════════════════════
# Vorpal skill reconciliation — ensures heroine innate/learned/upgrade skills
# stay in sync with the vorpal + facility-upgrade flags across save cycles.
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
        into upgrade_skills → inject it now. Legacy saves that stored it in
        learned_skills (where it occupied one of the 3 learned slots and
        showed up in the Barracks replacement menu) are migrated too.
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

    # ── Case 3: keep the facility-upgrade skill in its own category ──────
    # Upgrade skills are permanent facility rewards — they belong in
    # upgrade_skills, never in learned_skills (they must not consume one of
    # the 3 learned slots or appear in the Barracks replacement menu).
    from combat.ally_skills import is_upgrade_skill
    ally["learned_skills"] = [
        sid for sid in ally.get("learned_skills", []) if not is_upgrade_skill(sid)
    ]
    if player.get(upgrade_flag):
        upgrades = ally.setdefault("upgrade_skills", [])
        if upgrade_skill not in upgrades:
            upgrades.append(upgrade_skill)
        ally[upgraded_flag] = True


def _strip_stale_rarity_prefixes(player):
    """Old saves stored key items / crafting materials with the item builder's
    rarity prefix baked into the saved name ("Legendary Glass Anchor",
    "Rare Looking Glass Shard"). Strip it where the name exactly matches
    "{Rarity} {registry name}" — dynamic names (the resonance orb) never
    match and are left alone."""
    from resources.items import ITEMS
    containers = [player.get("inventory", [])]
    for house in (player.get("houses") or {}).values():
        if isinstance(house, dict):
            containers.append(house.get("storage", []))
    for container in containers:
        for item in container or []:
            if item.get("type") not in ("key_item", "crafting_material"):
                continue
            base = ITEMS.get(item.get("id"))
            if not base:
                continue
            rarity = str(item.get("rarity") or "common").title()
            if item.get("name") == f"{rarity} {base['name']}":
                item["name"] = base["name"]


# Global superboss pool ids that drop an Awakening Sigil Shard on first kill
# (docs/awakening_design.md Part C.2). Wonderland floors 10-40 grant shards via
# their own sources; Mary Sue (floor 50) grants a full Sigil instead.
AWAKENING_POOL_BOSS_IDS = [
    "broodmother_vileheart",
    "dream_devouring_slitcurrent",
    "queen_of_mirrors_sylvana",
    "melt_forge_golem_ignis",
    "heaven_banished_dragon_yinglong",
    "rientrante_frostbound",
    "captain_everlong_ship",
    "black_silence",
    "chromatic_artisan",
]


def _backfill_superboss_ledger(player):
    """Retro-credit ``defeated_superbosses`` from durable per-boss evidence.

    The kill ledger is written at fight time only, so saves whose kills
    predate it (or predate Wonderland / White-Knight recording) miss entries
    — which starves the Event Horizon Boss Rush pool and the guild's Sky
    Piercer count. Rebuild from evidence that predates the ledger:
      * Wonderland defeat flags (explicit, one per boss)
      * ``boss_defeated_white_knight``
      * ``awakening_shard_sources`` ``pool:<id>`` entries (shared ledger)
    Deliberately does NOT infer from ``superboss_pool`` (tier list is lossy
    across pool refills) and grants nothing itself — all currency grants are
    gated by their own source ledgers.
    """
    kills = player.setdefault("defeated_superbosses", [])
    for flag, boss_id in (
        ("wl_boss_defeated_queen_of_hearts", "wl_queen_of_hearts"),
        ("wl_boss_defeated_big_bad_wolf", "wl_big_bad_wolf"),
        ("wl_boss_defeated_wicked_witch", "wl_wicked_witch"),
        ("wl_boss_defeated_jabberwock", "wl_jabberwock"),
        ("wl_boss_defeated_mary_sue", "wl_mary_sue"),
        ("boss_defeated_white_knight", "white_knight"),
    ):
        if player.get(flag) and boss_id not in kills:
            kills.append(boss_id)
    for sid in list(player.get("awakening_shard_sources", []) or []):
        if isinstance(sid, str) and sid.startswith("pool:"):
            boss_id = sid.split(":", 1)[1]
            if boss_id and boss_id not in kills:
                kills.append(boss_id)


def _migrate_awakening_rewards(player):
    """Retro-grant Awakening currency for superbosses killed before the patch.

    Runs quietly on every load; the source ledger (awakening_shard_sources) is
    shared with the live kill grants in dungeon.py, so nothing double-grants.
    """
    kills = player.get("defeated_superbosses", [])
    if not kills:
        return
    sources = player.setdefault("awakening_shard_sources", [])

    # First superboss ever → one full Sigil (milestone)
    if not player.get("awakening_intro_granted"):
        player["awakening_intro_granted"] = True
        player["awakening_sigils"] = player.get("awakening_sigils", 0) + 1

    # Wonderland shards (floors 10-40) and the Mary Sue Sigil (floor 50)
    wl_flags = {
        "wl:10": "wl_boss_defeated_queen_of_hearts",
        "wl:20": "wl_boss_defeated_big_bad_wolf",
        "wl:30": "wl_boss_defeated_wicked_witch",
        "wl:40": "wl_boss_defeated_jabberwock",
    }
    for sid, flag in wl_flags.items():
        if player.get(flag) and sid not in sources:
            sources.append(sid)
            player["awakening_shards"] = player.get("awakening_shards", 0) + 1
    if player.get("wl_boss_defeated_mary_sue") and "wl:50" not in sources:
        sources.append("wl:50")
        player["awakening_sigils"] = player.get("awakening_sigils", 0) + 1

    # Global superboss pool → one shard per distinct kill
    for boss_id in AWAKENING_POOL_BOSS_IDS:
        sid = f"pool:{boss_id}"
        if boss_id in kills and sid not in sources:
            sources.append(sid)
            player["awakening_shards"] = player.get("awakening_shards", 0) + 1


def _reconcile_awakened_skills(record):
    """Ensure an awakened girl's innate kit matches her awakening state.

    Repairs saves where the flag was set but the swap never persisted
    (e.g. interrupted ceremony). No-op for non-awakened records.
    """
    if not record.get("awakened"):
        return
    key = record.get("key")
    if not key:
        return
    from combat.ally_skills import has_awakening, apply_awakening_skills
    if has_awakening(key):
        apply_awakening_skills(record, key)


def ensure_player_fields(player):
    """Ensure loaded saves have all required fields for new systems."""
    player.setdefault("skills", [])
    player.setdefault("skill_cooldowns", {})
    player.setdefault("skill_mastery", {})
    player.setdefault("passive_unlocked", True)
    player.setdefault("berserk_turns", 0)
    player.setdefault("bloodlust_turns", 0)
    player.setdefault("mount_id", None)
    player.setdefault("ship_id", None)
    # Migrate the legacy boolean ship system to tiered ships (Phase B)
    if player.get("has_ship") and not player.get("ship_id"):
        legacy = player.get("ship_type") or "sloop"
        player["ship_id"] = legacy if legacy in ("sloop", "frigate", "galleon") else "sloop"
    player.pop("has_ship", None)
    player.pop("ship_type", None)
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

    # Block time model (docs/time_system_design.md) — derive block fields
    # from the legacy minute clock once per save (no-op when migrated).
    player.setdefault("day_blocks", 0)
    player.setdefault("fatigue_stacks", 0)
    player.setdefault("time_blocks_migrated", False)
    from time_blocks import migrate_legacy_time_to_blocks
    migrate_legacy_time_to_blocks(player)

    # Event Horizon (docs/event_horizon_design.md)
    from event_horizon import ensure_eh_state
    ensure_eh_state(player)
    # Beating Root — per-actor third accessory slot (Phase 5)
    player.setdefault("acc3_unlocked", False)

    # Journal system (replaces console event display in GUI mode)
    player.setdefault("journal", {
        "events": [],
        "main_quests": [],
        "side_quests": [],
    })

    # Quest system (canonical state — see quests.py / docs/quest_system_design.md)
    from quests import ensure_quest_state, sync_resonance_tier
    ensure_quest_state(player)
    sync_resonance_tier(player)

    # Key-item naming migration (2026-09-28): strip the builder's rarity
    # prefix from keepsakes and materials in old saves.
    _strip_stale_rarity_prefixes(player)

    # Engagement / wedding system fields
    player.setdefault("girl_talk_today", {})
    player.setdefault("girl_gift_today", {})
    player.setdefault("girl_daily_last_day", 0)
    player.setdefault("engaged_girls", [])
    player.setdefault("married_girls", [])

    # Dispatch system (docs/dispatch_system_design.md) — Phase 1
    player.setdefault("dispatch", {
        "active": [],
        "reports": [],
        "completed": 0,
        "offers": [],
        "offers_cycle": -1,
    })

    # Tutorial tracking
    player.setdefault("tutorial_seen", False)
    player.setdefault("field_allowance_claimed", False)

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
    player.setdefault("hourglass_cooldown", 0)  # Fractured Hourglass recharge turns (combat state)
    player.setdefault("potion_sickness", 0)  # turns remaining before another consumable can be used
    player.setdefault("wonderland_shadows", [])  # persistent Wonderland shadow choices (floor 41+)

    # Guild legacy rewards (Sky Piercer + Prescript Ledger)
    player.setdefault("defeated_superbosses", [])  # distinct superboss ids defeated
    player.setdefault("sky_piercer_claimed", False)
    player.setdefault("bounties_completed", 0)  # lifetime honored guild bounties
    player.setdefault("high_bounties_completed", 0)  # Level 20+ bounty completions (Prescript Ledger gate)
    player.setdefault("prescript_ledger_claimed", False)

    # Awakening system (docs/awakening_design.md Part C)
    player.setdefault("awakening_sigils", 0)
    player.setdefault("awakening_shards", 0)
    player.setdefault("awakening_shard_sources", [])
    player.setdefault("awakening_intro_granted", False)
    # Old saves: rebuild the kill ledger from per-boss flags before anything
    # reads it (Boss Rush pool, Sky Piercer count, awakening retro-grants).
    _backfill_superboss_ledger(player)
    _migrate_awakening_rewards(player)

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
        ally.setdefault("nickname", "")
        ally.setdefault("learned_skills", [])
        ally.setdefault("upgrade_skills", [])
        ally.setdefault("learning", None)
        ally.setdefault("skill_cooldowns", {})
        ally.setdefault("skill_mastery", {})
        ally.setdefault("growth_applied", 0)
        ally.setdefault("awakened", False)
        ally.setdefault("awakened_name", "")
        ally.setdefault("awakened_skills", [])
        _reconcile_awakened_skills(ally)
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
        ally.setdefault("nickname", "")
        ally.setdefault("upgrade_skills", [])
        _reconcile_heroine_vorpal_skills(ally, player)

    for house in player.get("houses", {}).values():
        for girl in house.get("monster_girls", []):
            girl.setdefault("exp", 0)
            girl.setdefault("level_hp_bonus", 0)
            girl.setdefault("level_cap", 10)
            girl.setdefault("affection_cap", 100)
            girl.setdefault("engaged", False)
            girl.setdefault("married", False)
            girl.setdefault("nickname", "")
            girl.setdefault("learned_skills", [])
            girl.setdefault("upgrade_skills", [])
            girl.setdefault("learning", None)
            girl.setdefault("skill_cooldowns", {})
            girl.setdefault("skill_mastery", {})
            girl.setdefault("growth_applied", 0)
            girl.setdefault("awakened", False)
            girl.setdefault("awakened_name", "")
            girl.setdefault("awakened_skills", [])
            _reconcile_awakened_skills(girl)


def player_max_hp(player_or_attrs):
    """Improved HP formula."""
    if isinstance(player_or_attrs, dict) and "attributes" in player_or_attrs:
        attrs = player_or_attrs["attributes"]
        bonus = player_or_attrs.get("level_hp_bonus", 0)
        base = 15 + attrs["Constitution"] * 3 + bonus
        # Wedding max HP bonus (matriarchs_embrace)
        from combat.weapon.wedding_specials import apply_wedding_max_hp_bonus
        return base + apply_wedding_max_hp_bonus(player_or_attrs)
    else:
        attrs = player_or_attrs
        bonus = 0
        return 15 + attrs["Constitution"] * 3 + bonus


def allocate_points(base_attributes, remaining=None):
    """Fixed point allocation - handles negative base values and 0 remaining points.

    The player may finish early with points unspent: after each full pass
    through the attributes, they are asked whether to keep distributing.
    Answering 'n' (or 'done'/'quit') ends allocation early, preserving
    whatever has been spent so far.
    """
    temp = base_attributes.copy()
    remaining = TOTAL_POINTS if remaining is None else remaining

    first_pass = True
    while remaining > 0:
        if not first_pass:
            answer = input(
                f"\nYou still have {remaining} points left. "
                "Distribute more? (Enter = yes, n = finish): "
            ).strip().lower()
            if answer in ("n", "no", "done", "q", "quit", "finish"):
                print(f"Finishing with {remaining} points unspent.")
                break
        first_pass = False

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
        "time_minutes": 6 * 60,   # block 0 = 06:00 (Morning) — docs/time_system_design.md
        "day_blocks": 0,
        "fatigue_stacks": 0,
        "time_blocks_migrated": True,   # new games skip the legacy migration
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
        "tutorial_seen": False,
        "field_allowance_claimed": False,
    }

    # Quest system state (see quests.py / docs/quest_system_design.md)
    from quests import ensure_quest_state, sync_resonance_tier
    ensure_quest_state(player)
    sync_resonance_tier(player)

    # Wild dungeon state (see wild_dungeons.py / docs/wild_dungeon_design.md)
    from wild_dungeons import ensure_wild_dungeon_state
    ensure_wild_dungeon_state(player)
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
