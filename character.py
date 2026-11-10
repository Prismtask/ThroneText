from resources.races_classes import RACES, CLASSES
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


def _sync_unique_item_instances(player):
    """Re-apply the registry's unique identity to saved item instances.

    Older builds could store a unique template's instance before it was
    flagged unique — the Fractured Hourglass lived in old saves as a
    common consumable. Uniques are hand-authored, so restore the flag and
    the 'unique' rarity (the red label), and strip any rarity prefix baked
    into the saved name. Dynamic names never match the template and are
    left alone.
    """
    from resources.items import ITEMS

    lists = [player.get("inventory", [])]

    equipped_blocks = [player.get("equipped") or {}]
    for ally in (player.get("allies", [])
                 + player.get("wonderland_benched_allies", [])):
        equipped_blocks.append(ally.get("equipped") or {})
    for slots in equipped_blocks:
        for item in slots.values():
            if isinstance(item, dict):
                lists.append([item])

    for house in (player.get("houses") or {}).values():
        if isinstance(house, dict):
            lists.append(house.get("storage", []))
    lists.append((player.get("quests") or {}).get("pending_items", []))

    prefixes = ("Common ", "Uncommon ", "Rare ", "Epic ",
                "Legendary ", "Mythic ", "Unique ")

    for items in lists:
        for item in items or []:
            if not isinstance(item, dict):
                continue
            base = ITEMS.get(item.get("id"))
            if not base or not base.get("unique"):
                continue
            item["unique"] = True
            item["rarity"] = "unique"
            base_name = base.get("name")
            if not base_name:
                continue
            enhance = int(item.get("enhance", 0) or 0)
            expected = base_name + (f" +{enhance}" if enhance > 0 else "")
            name = item.get("name") or ""
            for prefix in prefixes:
                if name == f"{prefix}{expected}":
                    item["name"] = expected
                    break


def _rescale_item_instance(item):
    """Recompute a non-unique equipment instance under the current formulas (v4)."""
    if not isinstance(item, dict) or item.get("type") != "equipment" or item.get("unique"):
        return
    from resources.items import (
        _lookup_item_def, ITEM_RARITY,
        compute_equipment_mods, compute_elemental_dmg, compute_elemental_res,
    )
    base = _lookup_item_def(item.get("id"))
    if not base or "base_mods" not in base:
        return
    if base.get("base_form"):
        from resources.item_generation import refresh_infused_instance
        refresh_infused_instance(item, base)
        return
    rarity = item.get("rarity", "common")
    if rarity not in ITEM_RARITY:
        return
    enhance = int(item.get("enhance", 0))
    item["mods"] = compute_equipment_mods(base, rarity, enhance)
    if "elemental_dmg" in base:
        item["elemental_dmg"] = compute_elemental_dmg(base, rarity, enhance)
    if "elemental_res" in base:
        item["elemental_res"] = compute_elemental_res(base, rarity, enhance)
    if base.get("name"):
        suffix = f" +{enhance}" if enhance > 0 else ""
        item["name"] = f"{str(rarity).title()} {base['name']}{suffix}"


def _migrate_item_instance_v4(item):
    """Convert a v3 grid instance to a base form + flower infusions."""
    if not isinstance(item, dict) or item.get("type") != "equipment" or item.get("unique"):
        return
    from resources.items import _lookup_item_def, build_item
    from resources.item_generation import (
        INFUSION_START, WEAPON_SLOT_LADDERS,
        element_for_prefix, parse_grid_coordinate, refresh_infused_instance,
    )
    base = _lookup_item_def(item.get("id"))
    if not base or "base_mods" not in base:
        return
    if base.get("base_form"):
        refresh_infused_instance(item, base)
        return
    coord = parse_grid_coordinate(item.get("id"), base.get("slot"))
    if not coord:
        # Legacy trophy gear (magma locket etc.) keeps its instance stats.
        _rescale_item_instance(item)
        return
    prefix, form_key = coord
    target = _lookup_item_def(form_key)
    if not target or not target.get("base_form"):
        return
    element = element_for_prefix(prefix) or base.get("primary_element") or "physical"
    rarity = item.get("rarity", "common")
    enhance = int(item.get("enhance", 0))
    new_item = build_item(form_key, rarity, enhance)
    grade = int(base.get("grade", 1) or 1)
    if target.get("slot") == "weapon":
        steps = {1: 1, 2: 4, 3: 8}.get(grade, 1)
        ladder = WEAPON_SLOT_LADDERS[0]
        value = ladder[min(steps - 1, len(ladder) - 1)]
        infusions = [{"element": element, "value": value}]
        for el, val in (base.get("elemental_dmg") or {}).items():
            if el != element and val > 1.0 and len(infusions) < 3:
                infusions.append({"element": el, "value": INFUSION_START})
        new_item["infusions"] = infusions
    else:
        new_item["infusions"] = [{"element": element,
                                  "tier": max(0, min(2, grade - 1))}]
    refresh_infused_instance(new_item, target)
    item.clear()
    item.update(new_item)


def _refresh_unique_instance(item):
    """Keep a unique instance in sync with its one-primary element identity.

    Old saves can carry hand-tuned multi-element unique profiles. Refreshing
    on load collapses each piece to its authored primary and re-merges any
    flower infusions, so the new "primary + 2 flower slots" model reaches
    existing gear without touching its stats or specials.
    """
    if not isinstance(item, dict) or item.get("type") != "equipment":
        return
    from resources.items import _lookup_item_def
    from resources.item_generation import refresh_infused_instance
    base = _lookup_item_def(item.get("id"))
    if not base or not base.get("unique"):
        return
    refresh_infused_instance(item, base)


def _refresh_base_form_name(item):
    """Keep a base-form instance in sync with its current catalog template.

    Runs on every load so naming and catalog tuning reach saves migrated by
    an earlier build. Accessories additionally re-derive their stat mods and
    resistance profile: form affinities and the removal of innate accessory
    protection must apply to gear already sitting in old saves.
    """
    if not isinstance(item, dict) or item.get("type") != "equipment" or item.get("unique"):
        return
    from resources.items import (
        ITEM_RARITY, _lookup_item_def, compute_equipment_mods,
    )
    from resources.item_generation import infused_item_name, refresh_infused_instance
    base = _lookup_item_def(item.get("id"))
    if not base or not base.get("base_form"):
        return
    if base.get("slot") == "accessory":
        if item.get("infusions"):
            refresh_infused_instance(item, base)
        else:
            rarity = item.get("rarity", "common")
            if rarity in ITEM_RARITY:
                item["mods"] = compute_equipment_mods(
                    base, rarity, int(item.get("enhance", 0)))
            item["elemental_res"] = dict(base.get("elemental_res") or {})
    elif base.get("slot") == "armor" and item.get("infusions"):
        # Keep multi-slot resistance profiles in sync with the current merge.
        refresh_infused_instance(item, base)
    item["name"] = infused_item_name(item, base)


def _migrate_item_economy(player):
    """Migrate owned equipment to v4 and keep base-form names current."""
    migrate = player.get("item_formula_version", 1) < 4
    item_lists = [player.get("inventory", [])]
    for item in (player.get("equipped") or {}).values():
        if item:
            item_lists.append([item])
    for ally in player.get("allies", []) + player.get("wonderland_benched_allies", []):
        for item in (ally.get("equipped") or {}).values():
            if item:
                item_lists.append([item])
    for house in (player.get("houses") or {}).values():
        if isinstance(house, dict):
            item_lists.append(house.get("storage", []))
    for items in item_lists:
        for item in items or []:
            _refresh_unique_instance(item)
            if migrate:
                _migrate_item_instance_v4(item)
            else:
                _refresh_base_form_name(item)
    if migrate:
        player["item_econ_migrated"] = True
        player["item_formula_version"] = 4


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


def _backfill_bestiary(player):
    """Seed bestiary entries from progress that predates the journal.

    The ledger is written at fight/capture time, so older saves would show an
    empty bestiary despite holding captured girls and superboss kill flags.
    """
    player.setdefault("bestiary", {})
    from bestiary import record_defeat, record_capture
    for boss_id in list(player.get("defeated_superbosses", []) or []):
        record_defeat(player, boss_id, once=True, region=None)
    for house in (player.get("houses") or {}).values():
        for girl in (house.get("monster_girls") or []):
            key = girl.get("key")
            if key:
                record_capture(player, key, once=True, region=None)
    for ally in (player.get("allies", [])
                 + player.get("wonderland_benched_allies", [])):
        if ally.get("monster_girl") and not ally.get("_heroine_key"):
            record_capture(player, ally.get("key"), once=True, region=None)


def _backfill_superboss_ledger(player):
    """Retro-credit ``defeated_superbosses`` from durable per-boss evidence.

    The kill ledger is written at fight time only, so saves whose kills
    predate it (or predate Wonderland / White-Knight recording) miss entries
    — which starves the Event Horizon Boss Rush pool and the guild's Sky
    Piercer count. Rebuild from evidence that predates the ledger:
      * Wonderland defeat flags (explicit, one per boss)
      * ``boss_defeated_white_knight``
      * ``boss_defeated_palette`` (Chromatic Artisan)
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
        ("boss_defeated_palette", "chromatic_artisan"),
    ):
        if player.get(flag) and boss_id not in kills:
            kills.append(boss_id)
    for sid in list(player.get("awakening_shard_sources", []) or []):
        if isinstance(sid, str) and sid.startswith("pool:"):
            boss_id = sid.split(":", 1)[1]
            if boss_id and boss_id not in kills:
                kills.append(boss_id)


def _backfill_sylvana_mirror(player):
    """Give the Cracked Mirror to saves that already defeated Sylvana.

    The drop was added after the superboss shipped; without this, an old save
    could never open the house restoration arc. Key items bypass bag limits.
    """
    if player.get("sylvana_mirror_fixed") or player.get("sylvana_recruited"):
        return
    if "queen_of_mirrors_sylvana" not in (player.get("defeated_superbosses") or []):
        return
    if any(i.get("id") == "cracked_mirror"
           for i in player.get("inventory", [])):
        return
    from resources.items import build_item
    player.setdefault("inventory", []).append(
        build_item("cracked_mirror", rarity="unique")
    )
    player["sylvana_mirror_obtained"] = True


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
    player.setdefault("profession", None)  # chosen at the Guild after the Lv-40 capstone
    player.setdefault("inventory_upgrade", 0)
    player.setdefault("party_order", [])  # Track front/back row order
    # Shared dungeon depth per biome (2026-11-04): same-biome city entrances
    # share max_floor; each city keeps its own floor cursor. Old saves may
    # hold different depths per city — raise them monotonically on load.
    from leveling import sync_biome_dungeon_depth
    sync_biome_dungeon_depth(player)
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
    player.setdefault("stress", 0)          # player stress meter (0–100)
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

    # Fireside Tales (house stories) — part id -> day first read
    player.setdefault("house_stories", {"seen": {}})

    # Dream events (docs/dream_events_design.md) — old-save safe
    player.setdefault("dreams", {
        "seen": {},              # dream id -> times seen
        "last_day": 0,          # day the last dream fired
        "streak": 0,            # consecutive dreamless sleeps (soft pity)
        "last_category": None,  # boon/burden/choice — anti-spiral check
        "last_location": None,  # Memory/Omen dreams after a move
        "queue": [],            # queued story-dream ids (§4.5)
    })

    # Quest system (canonical state — see quests.py / docs/quest_system_design.md)
    from quests import ensure_quest_state, sync_resonance_tier
    ensure_quest_state(player)
    sync_resonance_tier(player)

    # Key-item naming migration (2026-09-28): strip the builder's rarity
    # prefix from keepsakes and materials in old saves.
    _strip_stale_rarity_prefixes(player)

    # Unique-item identity migration (2026-10-23): old saves may hold a
    # unique template's instance as a rolled rarity (e.g. Fractured Hourglass).
    _sync_unique_item_instances(player)

    # Item economy tuning (2026-10-18): rescale owned equipment once.
    _migrate_item_economy(player)

    # Celestial access (2026-11-04): the Sigil is earned at Floor 30.
    # Old saves that already reached that depth receive it on first load.
    try:
        if int(player.get("max_floor", 1) or 1) >= 30:
            from dungeon import _grant_celestial_sigil
            _grant_celestial_sigil(player, announce=False)
    except (TypeError, ValueError):
        pass

    # Rebuild cached elemental profiles from the current equipment. Item
    # migration/catalog refreshes (accessory resistances, infusion changes)
    # must reach the actor's defence/attack profile on load, not only after
    # the next equip action.
    from combat.elemental import compute_ally_elemental, compute_player_elemental
    res, dmg = compute_player_elemental(player)
    player["elemental_res"] = res
    player["elemental_dmg"] = dmg
    for ally in (player.get("allies", [])
                 + player.get("wonderland_benched_allies", [])):
        res, dmg = compute_ally_elemental(ally)
        ally["elemental_res"] = res
        ally["elemental_dmg"] = dmg

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

    # Karma / Game Rules (docs/karma_system_design.md) — old saves default OFF.
    # New characters get their rules from build_character(game_rules=...).
    from karma import ensure_state as _ensure_karma_state
    _ensure_karma_state(player)
    player.setdefault("karma_enabled", False)
    player.setdefault("karma_migrated", False)
    player.setdefault("family_enabled", False)
    player.setdefault("difficulty", "normal")
    player.setdefault("game_rules_version", 1)

    # Casino / tavern games (docs/casino_games_design.md) — old-save safe.
    from casino import ensure_state as _ensure_casino_state
    _ensure_casino_state(player)

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
    # Stepped through the book at least once. Older saves set
    # wonderland_unlocked when they entered, so that flag backfills it.
    player.setdefault("wonderland_visited", bool(player.get("wonderland_unlocked")))
    from wonderland_guests import ensure_guest_state
    ensure_guest_state(player)

    # Guild legacy rewards (Sky Piercer + Prescript Ledger)
    player.setdefault("defeated_superbosses", [])  # distinct superboss ids defeated
    # Sylvana's mirror restoration (heroine quest) — per-player progress, so
    # the quest state stays in the save (see heroine_quests/sylvana_mirror.py).
    from heroine_quests.sylvana_mirror import ensure_state as _ensure_sylvana_mirror_state
    _ensure_sylvana_mirror_state(player)
    player.setdefault("sky_piercer_claimed", False)
    player.setdefault("bounties_completed", 0)  # lifetime honored guild bounties
    player.setdefault("high_bounties_completed", 0)  # Level 20+ bounty completions (Prescript Ledger gate)
    player.setdefault("prescript_ledger_claimed", False)

    # Bestiary (Guild Hall discovery journal) — fills only on defeat/capture
    player.setdefault("bestiary", {})

    # Awakening system (docs/awakening_design.md Part C)
    player.setdefault("awakening_sigils", 0)
    player.setdefault("awakening_shards", 0)
    player.setdefault("awakening_shard_sources", [])
    player.setdefault("awakening_intro_granted", False)
    # Old saves: rebuild the kill ledger from per-boss flags before anything
    # reads it (Boss Rush pool, Sky Piercer count, awakening retro-grants).
    _backfill_superboss_ledger(player)
    _backfill_sylvana_mirror(player)
    _migrate_awakening_rewards(player)
    _backfill_bestiary(player)

    # Deed titles (docs/titles_design.md) — old-save safe. Reconcile after the
    # bestiary/superboss backfills so earned titles unlock on first load.
    from titles import ensure_state as _ensure_title_state, reconcile as _reconcile_titles
    _ensure_title_state(player)
    _reconcile_titles(player)

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
        ally.setdefault("affection_cap", 200)
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

    # Heroine auto-gear re-tier (2026-11-08): older builds equipped every inn
    # guest at common +5, which dominated heroine stats after the equipment
    # rework. Rebuild only the pieces still matching each heroine's build.
    # Runs after the ally slot normalisation above so temporary heroines have
    # a complete `equipped` dict.
    from combat.ally import migrate_heroine_auto_gear
    migrate_heroine_auto_gear(player)

    for house in player.get("houses", {}).values():
        for girl in house.get("monster_girls", []):
            girl.setdefault("exp", 0)
            girl.setdefault("level_hp_bonus", 0)
            girl.setdefault("level_cap", 10)
            girl.setdefault("affection_cap", 200)
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

    # Family system (docs/family_system_design.md) — pregnancy/child fields
    # plus affection ladder v2 cap migration (base 200 / engaged 300).
    from family import ensure_family_fields
    ensure_family_fields(player)


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


# New-game rules shown in the character-creation Game Rules step.
# Add a row here + a default in ensure_player_fields/build_character when a
# new drastic system ships. `implemented=False` rows are display-only.
GAME_RULES = (
    {
        "id": "karma_enabled",
        "label": "Karma",
        "type": "bool",
        "default_new": True,
        "default_old": False,
        "implemented": True,
        "locked_after_creation": True,
        "description": (
            "Choices change prices, taxes, city gates, Blackwake, and "
            "atonement. Off disables Karma choices and gates; Charisma alone "
            "sets prices and guild contracts scale by level only."
        ),
    },
    {
        "id": "family_enabled",
        "label": "Family system",
        "type": "bool",
        "default_new": False,
        "default_old": False,
        "implemented": True,
        "locked_after_creation": True,
        "description": (
            "Mature family content: shared nights, pregnancy, and true-born "
            "children. Off disables conception and children; intimacy scenes "
            "still follow the Content level setting."
        ),
    },
    {
        "id": "difficulty",
        "label": "Difficulty",
        "type": "choice",
        "options": ("story", "normal", "hard"),
        "default_new": "normal",
        "default_old": "normal",
        "implemented": False,
        "locked_after_creation": True,
        "description": (
            "Normal for now. Story/Hard options arrive with the difficulty "
            "system."
        ),
    },
)


def default_game_rules():
    """Return the default new-character Game Rules dict."""
    return {rule["id"]: rule["default_new"] for rule in GAME_RULES}


def build_character(race_key, class_key, final_attrs, name, slot, game_rules=None):
    """
    Pure function: build a complete player dict from creation choices.
    No I/O — returns the player dict ready to be saved.
    """
    rules = default_game_rules()
    rules.update(game_rules or {})
    karma_on = bool(rules.get("karma_enabled", True))
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
        "stress": 0,
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
        "wonderland_visited": False,
        "wonderland_guests": {"red_hood": "away", "dorothy": "away", "alice": "away"},
        "wl_hatter_three_guests_seen": False,
        "house_stories": {"seen": {}},
        # Deed titles (docs/titles_design.md) — new saves start empty
        "titles_unlocked": {},
        "title_active": None,
        "title_stats": {
            "gold_spent_shops": 0,
            "travel_segments": 0,
            "casino_hands_won": 0,
            "casino_biggest_win": 0,
            "casino_cheats_unseen": 0,
            "casino_cheats_caught": 0,
        },
        "titles_version": 1,
        # Game Rules / Karma (docs/karma_system_design.md)
        "karma_enabled": karma_on,
        "family_enabled": bool(rules.get("family_enabled", False)),
        "difficulty": rules.get("difficulty", "normal"),
        "game_rules_version": 1,
        "karma": 0,
        "karma_log": [],
        "karma_daily": {"day": 0, "gained": 0},
        "karma_gate": {
            "cooldown": {},
            "warning_seen": False,
            "watched_until": 0,
            "jail_karma_day": -99,
            "check_pending": False,
            "atonement_day": -99,
        },
        "karma_migrated": karma_on,
    }

    # Quest system state (see quests.py / docs/quest_system_design.md)
    from quests import ensure_quest_state, sync_resonance_tier
    ensure_quest_state(player)
    sync_resonance_tier(player)

    # Wonderland guest pacing (docs/wonderland_heroine_rework.md)
    from wonderland_guests import ensure_guest_state
    ensure_guest_state(player)

    # Wild dungeon state (see wild_dungeons.py / docs/wild_dungeon_design.md)
    from wild_dungeons import ensure_wild_dungeon_state
    ensure_wild_dungeon_state(player)
    return player
