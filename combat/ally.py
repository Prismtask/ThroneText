# combat/ally.py
"""Ally system - companions recruited from house monster girls."""
from combat.combat_io import c_print, c_input, c_clear
import random
from combat.stats import compute_enemy_attributes
from resources.enemies import ENEMIES, ENEMY_RACES
from resources.races_classes import ATTRIBUTES
from inventory import get_total_equipment_mods, remove_item_by_reference
from resources.quests import get_resonance_grade
from utils import display_name
from combat.helpers import ACTION_CANCELLED_MSG

ALLY_STAT_MULTIPLIER = 0.85   # Allies are slightly stronger at base
ALLY_LEVEL_STAT_BONUS = 1.0 / 6.0  # Capture level scaling matches the manual +1/level total (parity)
ALLY_HP_MULTIPLIER = 0.75    # Allies have slightly more HP baseline

# ── Late-bloomer growth (docs/awakening_design.md Part A) ────────────────
# Low-base girls earn bonus attribute points while leveling in the party.
GROWTH_TARGET_SUM = 42   # base-stat-sum parity target (Lich Queen parity at Lv 50)
GROWTH_MAX_RATE = 0.6    # points-per-level cap

# ── Party size constants ──────────────────────────────────────────────────────
MAX_PARTY_SIZE = 8        # Total party slots (player + up to 7 allies)
MAX_ALLIES = 7            # Maximum allies in party (player + 7 = 8 total)

# Front-row and bench capacities are governed by the player's Command
# Resonance grade — see resources/quests.RESONANCE_GRADES and
# docs/quest_system_design.md. Tier 0 (Unattuned) = 2 front / 0 bench;
# tier 5 (Crescendo) = 4 front / 4 bench, the historical fixed caps.


def get_resonance_tier(player):
    """The player's Command Resonance tier (0 if quest state is missing)."""
    return int((player.get("quests") or {}).get("resonance_tier", 0))


def get_party_capacity(player):
    """Return (max_front_allies, max_bench_allies).

    The front count is ALLIES only — the player always occupies the first
    slot of the combat row. Bench count is the reserve pool.
    """
    grade = get_resonance_grade(get_resonance_tier(player))
    return max(1, grade["front"] - 1), max(0, grade["bench"])


def get_active_limit(player):
    """Max number of ALLIES allowed in the front (active) row."""
    return get_party_capacity(player)[0]


def get_bench_limit(player):
    """Max number of ALLIES allowed on the reserve bench."""
    return get_party_capacity(player)[1]


# ── Party order management ───────────────────────────────────────────────────

def ensure_party_order(player):
    """Initialize or repair the party_order list for the player.
    
    party_order is a list of indices into player['allies'], ordered by
    deployment priority:
      - First get_active_limit(player) entries are the FRONT row (in combat)
      - The next get_bench_limit(player) entries are the BENCH (switchable)
      - Remaining entries are inactive (beyond current command capacity)
    The player themselves is always active and not in this list.
    """
    allies = player.get("allies", [])
    n = len(allies)
    order = player.get("party_order", [])

    # Clean out stale indices
    order = [i for i in order if 0 <= i < n]

    # Add any new allies not yet in order
    existing = set(order)
    for i in range(n):
        if i not in existing:
            order.append(i)

    player["party_order"] = order


def get_active_allies(player):
    """Return allies in the FRONT row (active in combat)."""
    ensure_party_order(player)
    allies = player.get("allies", [])
    order = player.get("party_order", [])
    result = []
    for idx in order[:get_active_limit(player)]:
        if idx < len(allies):
            ally = allies[idx]
            if not ally.get("defeated") and ally.get("current_hp", 0) > 0:
                result.append(ally)
    return result


def get_reserve_allies(player):
    """Return allies on the BENCH (reserve — switchable, not deployed)."""
    ensure_party_order(player)
    allies = player.get("allies", [])
    order = player.get("party_order", [])
    active_limit = get_active_limit(player)
    bench_limit = get_bench_limit(player)
    result = []
    for idx in order[active_limit:active_limit + bench_limit]:
        if idx < len(allies):
            ally = allies[idx]
            if not ally.get("defeated") and ally.get("current_hp", 0) > 0:
                result.append(ally)
    return result


def get_all_active_allies_including_defeated(player):
    """Return all allies in the FRONT row (including defeated ones, for display)."""
    ensure_party_order(player)
    allies = player.get("allies", [])
    order = player.get("party_order", [])
    result = []
    for idx in order[:get_active_limit(player)]:
        if idx < len(allies):
            result.append(allies[idx])
    return result


def get_all_reserve_allies_including_defeated(player):
    """Return bench allies (including defeated ones, for display)."""
    ensure_party_order(player)
    allies = player.get("allies", [])
    order = player.get("party_order", [])
    active_limit = get_active_limit(player)
    bench_limit = get_bench_limit(player)
    result = []
    for idx in order[active_limit:active_limit + bench_limit]:
        if idx < len(allies):
            result.append(allies[idx])
    return result


def swap_party_member(player, ally_index):
    """Swap an ally between front and back rows by their absolute index in allies list.
    
    If the ally is in the front row, they swap with the first bench ally.
    Otherwise (bench or inactive) they swap with the first front-row ally.
    Returns (message, success_bool).
    """
    ensure_party_order(player)
    allies = player.get("allies", [])
    order = player.get("party_order", [])
    n = len(allies)

    if ally_index < 0 or ally_index >= n:
        return "Invalid ally selection.", False

    ally_name = allies[ally_index]["name"]
    active_limit = get_active_limit(player)
    bench_limit = get_bench_limit(player)

    if ally_index in order[:active_limit]:
        # Ally is in front — swap with first bench ally
        back_indices = order[active_limit:active_limit + bench_limit]
        if not back_indices:
            return (f"{ally_name} is already in the front row and there is no "
                    f"one on the bench to swap with.", False)
        target_idx = back_indices[0]
        # Swap positions in order
        pos_a = order.index(ally_index)
        pos_b = order.index(target_idx)
        order[pos_a], order[pos_b] = order[pos_b], order[pos_a]
        target_name = allies[target_idx]["name"]
        return f"{ally_name} moves to the back row. {target_name} steps forward!", True
    else:
        # Ally is on the bench (or inactive) — swap with first front-row ally
        front_indices = order[:active_limit]
        if not front_indices:
            return f"There are no front row allies to swap with.", False
        target_idx = front_indices[0]
        pos_a = order.index(ally_index)
        pos_b = order.index(target_idx)
        order[pos_a], order[pos_b] = order[pos_b], order[pos_a]
        target_name = allies[target_idx]["name"]
        return f"{ally_name} steps forward! {target_name} moves to the back row.", True


def do_ally_switch(player, front_ally_idx, reserve_ally_idx):
    """Swap two specific allies: a front-row ally with a reserve ally.
    
    Used when an ally uses the Switch action on their turn.
    Args:
        front_ally_idx: absolute index of the front ally (the one switching)
        reserve_ally_idx: absolute index of the reserve ally (the one coming in)
    Returns (message, success_bool).
    """
    ensure_party_order(player)
    allies = player.get("allies", [])
    order = player.get("party_order", [])
    n = len(allies)
    active_limit = get_active_limit(player)
    bench_limit = get_bench_limit(player)

    if front_ally_idx < 0 or front_ally_idx >= n:
        return "Invalid front ally selection.", False
    if reserve_ally_idx < 0 or reserve_ally_idx >= n:
        return "Invalid reserve ally selection.", False

    front_name = allies[front_ally_idx]["name"]
    reserve_name = allies[reserve_ally_idx]["name"]

    # Verify positions
    if front_ally_idx not in order[:active_limit]:
        return f"{front_name} is not in the front row.", False
    if reserve_ally_idx not in order[active_limit:active_limit + bench_limit]:
        return f"{reserve_name} is not on the bench.", False

    # Swap positions in order
    pos_a = order.index(front_ally_idx)
    pos_b = order.index(reserve_ally_idx)
    order[pos_a], order[pos_b] = order[pos_b], order[pos_a]

    return f"{reserve_name} steps forward! {front_name} retreats to the back row.", True


def can_switch(player):
    """Return True if the player has at least one reserve ally who could switch in."""
    reserve = get_reserve_allies(player)
    return len(reserve) > 0


def auto_fill_active_slots(player):
    """If there are fewer than get_active_limit(player) living front allies,
    pull from the bench to fill the slots. Call at combat start so the front
    row is fully populated. Returns list of messages about who moved."""
    ensure_party_order(player)
    allies = player.get("allies", [])
    order = player.get("party_order", [])
    active_limit = get_active_limit(player)
    bench_limit = get_bench_limit(player)
    msgs = []

    # Count currently alive active allies
    active_alive = sum(
        1 for idx in order[:active_limit]
        if idx < len(allies) and not allies[idx].get("defeated") and allies[idx].get("current_hp", 0) > 0
    )

    # If we already have enough, stop
    needed = active_limit - active_alive
    if needed <= 0:
        return msgs

    # Find alive bench allies to pull forward
    reserve_alive = []
    for idx in order[active_limit:active_limit + bench_limit]:
        if idx < len(allies) and not allies[idx].get("defeated") and allies[idx].get("current_hp", 0) > 0:
            reserve_alive.append(idx)

    # Also find defeated/inactive front allies to swap out
    inactive_front = []
    for idx in order[:active_limit]:
        if idx >= len(allies) or allies[idx].get("defeated") or allies[idx].get("current_hp", 0) <= 0:
            inactive_front.append(idx)

    swaps = min(len(inactive_front), len(reserve_alive), needed)
    for i in range(swaps):
        front_idx = inactive_front[i]
        back_idx = reserve_alive[i]
        pos_a = order.index(front_idx)
        pos_b = order.index(back_idx)
        order[pos_a], order[pos_b] = order[pos_b], order[pos_a]
        msgs.append(f"{allies[back_idx]['name']} moves to the front row!")
        if front_idx < len(allies):
            msgs.append(f"{allies[front_idx]['name']} moves to the back row.")

    return msgs


def reinforce_fallen_allies(player):
    """Replace fallen FRONT-row allies with the earliest living bench ally.

    Reinforcement rule (2026-10-12): the bench is a reinforcement line — at
    the start of every combat round, any front ally who fell is swapped out
    for the earliest (party_order) living reserve ally, so the front row is
    always staffed. The fallen retire to the bench (still revivable).

    "Fallen" = HP 0 only. An ally who is flagged ``defeated`` but still has
    HP (e.g. the Big Bad Wolf's SWALLOW) is NOT swapped — that condition is
    temporary and restored in place by its fight.

    Returns list of swap messages (empty when nothing changes).
    """
    ensure_party_order(player)
    allies = player.get("allies", [])
    order = player.get("party_order", [])
    active_limit = get_active_limit(player)
    bench_limit = get_bench_limit(player)
    msgs = []

    fallen = [
        idx for idx in order[:active_limit]
        if idx < len(allies) and allies[idx].get("current_hp", 0) <= 0
    ]
    reserves = [
        idx for idx in order[active_limit:active_limit + bench_limit]
        if idx < len(allies)
        and not allies[idx].get("defeated")
        and allies[idx].get("current_hp", 0) > 0
    ]

    for front_idx in fallen:
        if not reserves:
            break
        back_idx = reserves.pop(0)      # earliest bench ally first
        pos_a = order.index(front_idx)
        pos_b = order.index(back_idx)
        order[pos_a], order[pos_b] = order[pos_b], order[pos_a]
        msgs.append(f"{allies[back_idx]['name']} steps in for the fallen "
                    f"{allies[front_idx]['name']}!")
    return msgs


def _fix_level_hp_bonus(girl):
    """Compute or repair an ally's level_hp_bonus.

    Handles backwards compatibility: if a girl was captured at a high level
    before this fix, her stored level_hp_bonus will be 0. We detect this and
    compute the correct bonus from her level.
    """
    level = girl.get("level", 1)
    stored = girl.get("level_hp_bonus")
    expected = max(0, (level - 1) * 4)
    # If stored value is missing or suspiciously low for a high-level girl,
    # use the expected formula instead.
    if stored is None or (stored == 0 and level > 1):
        return expected
    return stored


def ally_max_hp(ally):
    """Compute ally max HP based on Constitution and level-up bonuses (same formula as player)."""
    con = ally["attributes"]["Constitution"]
    bonus = ally.get("level_hp_bonus", 0)
    return int(15 + con * 3 + bonus)


def compute_girl_attributes(girl):
    """Return the attribute dict for a housed girl record.

    Stored attributes win (they preserve manual level-up picks). Otherwise
    the values are computed from the enemy template + level scaling + any
    engagement-ring bonus. Shared by create_ally_from_girl() and the
    dispatch system (facilities/dispatch.py).
    """
    stored = girl.get("attributes")
    if stored and all(attr in stored for attr in ATTRIBUTES):
        return dict(stored)

    enemy_key = girl.get("key")
    template = ENEMIES.get(enemy_key) if enemy_key else None
    if not template:
        return {attr: 1 for attr in ATTRIBUTES}

    base_attrs = compute_enemy_attributes(enemy_key)
    level = girl.get("level", 1)
    scaled = {}
    for attr in ATTRIBUTES:
        base = base_attrs.get(attr, 0)
        level_bonus = (level - 1) * ALLY_LEVEL_STAT_BONUS
        scaled[attr] = max(1, int(base * ALLY_STAT_MULTIPLIER + level_bonus))

    ring_bonus = girl.get("ring_stat_bonus")
    if ring_bonus:
        for attr, val in ring_bonus.items():
            scaled[attr] = scaled.get(attr, 0) + val
    return scaled


def get_growth_rate(entity):
    """Late-bloomer growth rate (attribute points per level) for a monster girl.

    Derived from the girl's base-stat-sum deficit vs GROWTH_TARGET_SUM; a
    template `growth:` override in the enemy YAML wins. Heroines and
    non-monster-girls return 0 (see docs/awakening_design.md Part A).
    """
    if entity.get("_heroine_key") or entity.get("_wonderland_temp"):
        return 0.0
    key = entity.get("key")
    template = ENEMIES.get(key) if key else None
    if not template or not template.get("monster_girl") or template.get("_heroine"):
        return 0.0
    override = template.get("growth")
    if override is not None:
        try:
            return max(0.0, min(GROWTH_MAX_RATE, float(override)))
        except (TypeError, ValueError):
            pass
    base_attrs = compute_enemy_attributes(key)
    base_sum = sum(base_attrs.get(attr, 0) for attr in ATTRIBUTES)
    return max(0.0, min(GROWTH_MAX_RATE, (GROWTH_TARGET_SUM - base_sum) * 0.85 / 50.0))


def get_growth_label(entity):
    """Display band for the growth system ("High"/"Medium"/"Low"/"—")."""
    rate = get_growth_rate(entity)
    if rate <= 0 or int(49 * rate) <= 0:  # no growth point by Lv 50
        return "—"
    if rate >= 0.35:
        return "High"
    if rate >= 0.15:
        return "Medium"
    return "Low"


def apply_ally_growth(ally):
    """Apply late-bloomer growth points owed at the ally's current level.

    `growth_applied` (persisted on ally + house records) tracks points already
    granted, making this idempotent. New points go to the girl's highest
    current attribute (tie-break: ATTRIBUTES order). Returns display lines for
    anything granted. Call after the manual level-up point and before the HP
    recalculation so Constitution growth counts toward max HP.
    """
    if not ally.get("attributes"):
        return []
    rate = get_growth_rate(ally)
    if rate <= 0:
        return []
    level = int(ally.get("level", 1))
    target = int((level - 1) * rate)
    try:
        applied = int(ally.get("growth_applied", 0) or 0)
    except (TypeError, ValueError):
        applied = 0
    gain = target - applied
    if gain <= 0:
        return []
    attrs = ally["attributes"]
    counts = {}
    for _ in range(gain):
        best = max(ATTRIBUTES, key=lambda a: (attrs.get(a, 0), -ATTRIBUTES.index(a)))
        attrs[best] = attrs.get(best, 0) + 1
        counts[best] = counts.get(best, 0) + 1
    ally["growth_applied"] = max(applied, target)
    parts = ", ".join(f"+{n} {attr}" for attr, n in counts.items())
    return [f"[Late Bloomer] {display_name(ally)}: {parts} (growth)"]


def create_ally_from_girl(girl):
    """Convert a house monster girl dict into a combat-ready ally dict.

    girl format from house:
        {"key": "...", "name": "...", "level": N, "affection": N, "captured_on": N}
    """
    enemy_key = girl.get("key")
    template = ENEMIES.get(enemy_key)
    if not template:
        # Fallback for missing template — still preserves stored HP/stress.
        from combat.elemental import neutral_profile
        level = girl.get("level", 1)
        stored_hp = girl.get("current_hp")
        fallback_hp = 30 if stored_hp is None else max(1, min(int(stored_hp), 30))
        fallback = {
            "name": girl.get("name", "Companion"),
            "nickname": girl.get("nickname", ""),
            "key": enemy_key or "unknown",
            "level": level,
            "attributes": {attr: 1 for attr in ATTRIBUTES},
            "current_hp": fallback_hp,
            "max_hp": 30,
            "equipped": {"weapon": None, "armor": None, "accessory1": None, "accessory2": None},
            "active_buffs": [],
            "active_debuffs": [],
            "blinded": False,
            "slowed": False,
            "stunned": False,
            "frozen": False,
            "cursed": False,
            "dreaded": False,
            "silenced": False,
            "is_ally": True,
            "affection": girl.get("affection", 20),
            "exp": girl.get("exp", 0),
            "level_hp_bonus": _fix_level_hp_bonus(girl),
            "growth_applied": int(girl.get("growth_applied", 0) or 0),
            "stress": int(girl.get("stress", 0)),
            "consecutive_dispatch": int(girl.get("consecutive_dispatch", 0)),
            "last_dispatch": girl.get("last_dispatch"),
            "last_dispatch_day": int(girl.get("last_dispatch_day", 0) or 0),
            "injured_until": int(girl.get("injured_until", 0) or 0),
            "elemental_res": neutral_profile(),
            "elemental_dmg": neutral_profile(),
        }
        if girl.get("acc3_unlocked"):
            fallback["acc3_unlocked"] = True
            fallback["equipped"]["accessory3"] = None
        return fallback

    # Attributes: stored level-up picks win; otherwise computed from the
    # enemy template formula (+ engagement ring bonus) in a shared helper
    # that the dispatch system also uses for housed girls.
    scaled_attrs = compute_girl_attributes(girl)

    ally = {
        "name": girl.get("name", template["name"]),
        "nickname": girl.get("nickname", ""),
        "key": enemy_key,
        "level": girl.get("level", template["level"]),
        "attributes": scaled_attrs,
        "equipped": {"weapon": None, "armor": None, "accessory1": None, "accessory2": None},
        "active_buffs": [],
        "active_debuffs": [],
        "blinded": False,
        "slowed": False,
        "stunned": False,
        "frozen": False,
        "cursed": False,
        "dreaded": False,
        "silenced": False,
        "is_ally": True,
        "affection": girl.get("affection", 30),
        "affection_cap": girl.get("affection_cap", 100),
        "engaged": girl.get("engaged", False),
        "married": girl.get("married", False),
        "monster_girl": template.get("monster_girl", True),
        "exp": girl.get("exp", 0),
        "level_hp_bonus": _fix_level_hp_bonus(girl),
        "level_cap": girl.get("level_cap", 10),
        "growth_applied": int(girl.get("growth_applied", 0) or 0),
        "defeated": False,
        "stress": int(girl.get("stress", 0)),
        "consecutive_dispatch": int(girl.get("consecutive_dispatch", 0)),
        "last_dispatch": girl.get("last_dispatch"),
        "last_dispatch_day": int(girl.get("last_dispatch_day", 0) or 0),
        "injured_until": int(girl.get("injured_until", 0) or 0),
        # Awakening (docs/awakening_design.md Part C) — persisted so the
        # upgraded kit + displayed name survive the house round trip.
        "awakened": girl.get("awakened", False),
        "awakened_name": girl.get("awakened_name", ""),
        "awakened_skills": list(girl.get("awakened_skills", []) or []),
        # Skill system fields
        "passive_skill": girl.get("passive_skill", None),  # Race-based passive
        "innate_skills": girl.get("innate_skills", []),    # 2 innate skills unique to girl
        "learned_skills": girl.get("learned_skills", []),  # List of learned skill_ids
        "upgrade_skills": girl.get("upgrade_skills", []),  # Heroine facility upgrade skills (own category)
        "learning": girl.get("learning", None),             # Current skill being learned: {"skill_id": "...", "exp": 0, "exp_needed": 300}
        "skill_cooldowns": girl.get("skill_cooldowns", {}), # skill_id -> cooldown_remaining
        "skill_mastery": girl.get("skill_mastery", {}),     # skill_id -> exp_count (for mastery levels)
    }
    # Beating Root — the third accessory slot survives the house round-trip
    if girl.get("acc3_unlocked"):
        ally["acc3_unlocked"] = True
        ally["equipped"]["accessory3"] = None

    # Compute HP based on scaled Constitution + level. A stored current_hp on
    # the house record is preserved (dispatch injuries / prior state) instead
    # of always landing at full — the round-trip is written back on dismiss.
    ally["max_hp"] = ally_max_hp(ally)
    stored_hp = girl.get("current_hp")
    if stored_hp is None:
        ally["current_hp"] = ally["max_hp"]
    else:
        ally["current_hp"] = max(1, min(int(stored_hp), ally["max_hp"]))

    # Add elemental stats from race
    from combat.elemental import compute_ally_elemental
    e_res, e_dmg = compute_ally_elemental(ally)
    ally["elemental_res"] = e_res
    ally["elemental_dmg"] = e_dmg
    
    # Initialize skill system
    from combat.ally_skills import initialize_ally_skills
    initialize_ally_skills(ally, enemy_key, template.get("race"))

    # ── Wonderland heroine identity ──────────────────────────────────
    # House-recruited heroines must carry their heroine identity, otherwise
    # get_heroine_in_party() can't find them and the Wonderland inn creates
    # duplicate copies (which then lose their equipment when leaving).
    heroine_key = _HEROINE_TEMPLATE_KEYS_INVERSE.get(enemy_key)
    if heroine_key:
        ally["_heroine_key"] = heroine_key
        ally["_wonderland_temp"] = False  # house heroines are permanent
        if girl.get("_heroine_passive"):
            ally["_heroine_passive"] = girl["_heroine_passive"]
        if girl.get("_heroine_permanent_passive"):
            ally["_heroine_permanent_passive"] = girl["_heroine_permanent_passive"]
        # Restore equipment stashed on the house record (inventory was full
        # when she was sent home — her gear is preserved there, not destroyed).
        stashed = girl.get("equipped")
        if stashed:
            for slot in ("weapon", "armor", "accessory1", "accessory2",
                         "accessory3"):
                item = stashed.get(slot)
                if item:
                    ally["equipped"][slot] = item
            from combat.elemental import compute_ally_elemental
            e_res, e_dmg = compute_ally_elemental(ally)
            ally["elemental_res"] = e_res
            ally["elemental_dmg"] = e_dmg

    return ally


def get_ally_effective_attribute(ally, attr_name):
    """Return effective attribute after equipment and buffs."""
    base = ally["attributes"].get(attr_name, 0)
    equip_mods = get_total_equipment_mods(ally)
    total = base + equip_mods.get(attr_name, 0)

    for debuff in ally.get("active_debuffs", []):
        if debuff.get("type") == "curse":
            total -= debuff.get("penalty", 2)

    if attr_name == "Strength":
        from combat.status_effects import get_weaken_pct
        weaken_pct = get_weaken_pct(ally)
        if weaken_pct > 0:
            total = int(total * (1.0 - weaken_pct))

    for buff in ally.get("active_buffs", []):
        if buff.get("type") in ("blessing", "well_rested") or buff.get("stat") == "all":
            total += buff.get("value", 0)
        elif buff.get("stat") == attr_name:
            total += buff.get("value", 0)

    # Apply race passive stat bonuses (supports `type: multi` blocks)
    from combat.ally_skills import get_race_passive_effects
    for effect in get_race_passive_effects(ally.get("race")):
        if effect.get("type"):
            continue  # type-tagged effects are handled outside attribute math
        if effect.get("stat") == "all":
            if attr_name in effect.get("stats", []):
                total += effect.get("value", 0)
        elif effect.get("stat") == "multi":
            total += effect.get("stats", {}).get(attr_name, 0)
        elif effect.get("stat") == attr_name:
            total += effect.get("value", 0)

    # Tarnished Jade pin bonuses
    from combat.weapon.tarnished_jade import get_tarnished_jade_str_bonus, get_tarnished_jade_wis_bonus, is_tarnished_jade_weakened
    if attr_name == "Strength":
        total += get_tarnished_jade_str_bonus(ally)
    elif attr_name == "Wisdom":
        total += get_tarnished_jade_wis_bonus(ally)
    # Apply weaken debuff from Wedge Backlash
    if is_tarnished_jade_weakened(ally):
        total = total // 2

    # Author's Pen passive: +4 all stats while in Wonderland
    from combat.weapon.authors_pen import get_authors_pen_stat_bonus
    total += get_authors_pen_stat_bonus(ally, attr_name)

    # Event Horizon: Entropy (−% all attributes, run-scoped)
    for debuff in ally.get("active_debuffs", []):
        if debuff.get("type") == "eh_entropy":
            total = int(total * (1.0 - min(0.95, debuff.get("value", 0))))
            break

    return total


def compute_ally_stats(ally):
    """Return tuple of effective stats (str, con, dex, ler, wis, cha)."""
    a_str = get_ally_effective_attribute(ally, "Strength")
    a_con = get_ally_effective_attribute(ally, "Constitution")
    a_dex = get_ally_effective_attribute(ally, "Dexterity")
    a_ler = get_ally_effective_attribute(ally, "Learning")
    a_wis = get_ally_effective_attribute(ally, "Wisdom")
    a_cha = get_ally_effective_attribute(ally, "Charisma")
    return a_str, a_con, a_dex, a_ler, a_wis, a_cha


def format_ally_status_line(ally, idx=None, is_active=False):
    """Format a compact name/HP line for an ally."""
    prefix = f"[{idx}]" if idx is not None else "   "
    active_mark = " >" if is_active else ""
    mg_symbol = " ♀" if ally.get("monster_girl") else ""
    disp = display_name(ally)[:12]
    if ally.get("defeated") or ally.get("current_hp", 0) <= 0:
        return f"{prefix} {disp:<12} [INCAPACITATED]{mg_symbol}{active_mark}"
    return f"{prefix} {disp:<12} {ally['current_hp']:>3}/{ally['max_hp']:<3}{mg_symbol}{active_mark}"


def format_ally_buff_line(ally):
    """Format a compact buff/debuff tag line for an ally."""
    statuses = []
    if ally.get("stunned"):
        statuses.append("STN")
    if ally.get("slowed"):
        statuses.append("SLW")
    if ally.get("blinded"):
        statuses.append("BLD")
    if ally.get("frozen"):
        statuses.append("FRZ")
    if any(d["type"] == "poison" for d in ally.get("active_debuffs", [])):
        statuses.append("PSN")
    if any(d["type"] == "bleed" for d in ally.get("active_debuffs", [])):
        statuses.append("BLE")
    if any(d["type"] == "burn" for d in ally.get("active_debuffs", [])):
        statuses.append("BRN")
    return f" [{' '.join(statuses)}]" if statuses else ""


def _hp_bar(current, max_hp, width=10):
    """Return a simple ASCII HP bar."""
    if max_hp <= 0:
        return "[          ]"
    ratio = current / max_hp
    filled = int(ratio * width)
    filled = max(0, min(width, filled))
    empty = width - filled
    bar = "#" * filled + "." * empty
    return f"[{bar}]"


def get_alive_allies(player):
    """Return list of alive (non-defeated) allies from player."""
    return [a for a in player.get("allies", []) if not a.get("defeated") and a.get("current_hp", 0) > 0]


def get_all_party_members(player):
    """Return list of all alive party members: [player] + alive allies."""
    party = [player]
    party.extend(get_alive_allies(player))
    return party


def equip_ally_item(ally, item, player, target_slot=None):
    """Equip an item on an ally from the player's inventory."""
    from inventory import add_item_to_inventory

    # Block equipping temporary Wonderland heroines
    # EXCEPTION: vorpal_blade_rusted / vorpal_blade on Alice (heroine quest item)
    # EXCEPTION: woodcutters_broken_axe / grandmothers_axe on Red Hood
    # EXCEPTION: silver_slippers / ruby_slippers on Dorothy
    item_id = item.get("id", "")

    # Event Horizon / player-only items (e.g. Piece of Relationship) refuse
    # to be equipped by anyone but the MC.
    if item.get("player_only"):
        return (f"{item['name']} will only answer to "
                f"{player.get('name', 'its bearer')} — it cannot be worn by an ally.")

    is_vorpal_on_alice = (
        item_id in ("vorpal_blade_rusted", "vorpal_blade") and
        ally.get("_heroine_key") == "alice"
    )
    is_axe_on_redhood = (
        item_id in ("woodcutters_broken_axe", "grandmothers_axe") and
        ally.get("_heroine_key") == "red_hood"
    )
    is_slippers_on_dorothy = (
        item_id in ("silver_slippers", "ruby_slippers") and
        ally.get("_heroine_key") == "dorothy"
    )
    if ally.get("_wonderland_temp") and not is_vorpal_on_alice and not is_axe_on_redhood and not is_slippers_on_dorothy:
        return f"Cannot equip gear on {display_name(ally)} — they are not a permanent ally yet."

    item_slot = item["slot"]
    # Resolve dual accessory slots (+ unlocked third — Beating Root, docs §10.6)
    if item_slot == "accessory":
        acc3 = bool(ally.get("acc3_unlocked"))
        if target_slot in ("accessory1", "accessory2") or (
                target_slot == "accessory3" and acc3):
            pass  # use caller-specified slot
        elif ally.get("equipped", {}).get("accessory1") is None:
            target_slot = "accessory1"
        elif ally.get("equipped", {}).get("accessory2") is None:
            target_slot = "accessory2"
        elif acc3 and ally.get("equipped", {}).get("accessory3") is None:
            target_slot = "accessory3"
        else:
            target_slot = "accessory1"
    else:
        target_slot = item_slot

    old = ally.get("equipped", {}).get(target_slot)
    if old:
        # Return old item to player inventory
        if not add_item_to_inventory(player, old):
            return f"Cannot equip {item['name']} on {display_name(ally)} — your inventory is full."
    ally["equipped"][target_slot] = item
    # Remove item from player inventory
    if item in player.get("inventory", []):
        player["inventory"].remove(item)
    # Recalculate ally elemental profile
    from combat.elemental import compute_ally_elemental
    res, dmg = compute_ally_elemental(ally)
    ally["elemental_res"] = res
    ally["elemental_dmg"] = dmg

    # Vorpal Blade on Alice: trigger skill swap
    if is_vorpal_on_alice:
        from combat.ally_skills import swap_alice_to_vorpal_skills
        swap_alice_to_vorpal_skills(ally)

    # Grandmother's Axe on Red Hood: trigger skill swap
    if is_axe_on_redhood:
        from combat.ally_skills import swap_redhood_to_vorpal_skills
        swap_redhood_to_vorpal_skills(ally)

    # Silver/Ruby Slippers on Dorothy: trigger skill swap
    if is_slippers_on_dorothy:
        from combat.ally_skills import swap_dorothy_to_vorpal_skills
        swap_dorothy_to_vorpal_skills(ally)

    return f"Equipped {item['name']} on {display_name(ally)}."


def unequip_ally_slot(ally, slot, player):
    """Unequip an item from an ally and return to player's inventory."""
    from inventory import add_item_to_inventory

    # Block unequipping temporary Wonderland heroines
    # EXCEPTION: vorpal blade on Alice (heroine quest item)
    # EXCEPTION: woodcutter/grandmother axe on Red Hood
    # EXCEPTION: silver/ruby slippers on Dorothy
    equipped_item = ally.get("equipped", {}).get(slot, {}) or {}
    is_vorpal_on_alice = (
        equipped_item.get("id") in ("vorpal_blade_rusted", "vorpal_blade") and
        ally.get("_heroine_key") == "alice"
    )
    is_axe_on_redhood = (
        equipped_item.get("id") in ("woodcutters_broken_axe", "grandmothers_axe") and
        ally.get("_heroine_key") == "red_hood"
    )
    is_slippers_on_dorothy = (
        equipped_item.get("id") in ("silver_slippers", "ruby_slippers") and
        ally.get("_heroine_key") == "dorothy"
    )
    if ally.get("_wonderland_temp") and not is_vorpal_on_alice and not is_axe_on_redhood and not is_slippers_on_dorothy:
        return f"Cannot unequip from {display_name(ally)} — they are not a permanent ally yet."

    if slot in ally.get("equipped", {}) and ally["equipped"][slot]:
        item = ally["equipped"][slot]
        if add_item_to_inventory(player, item):
            ally["equipped"][slot] = None
            # Recalculate ally elemental profile
            from combat.elemental import compute_ally_elemental
            res, dmg = compute_ally_elemental(ally)
            ally["elemental_res"] = res
            ally["elemental_dmg"] = dmg

            # Vorpal Blade removed from Alice: revert skills
            if is_vorpal_on_alice:
                from combat.ally_skills import revert_alice_to_normal_skills
                revert_alice_to_normal_skills(ally)

            # Grandmother's Axe removed from Red Hood: revert skills
            if is_axe_on_redhood:
                from combat.ally_skills import revert_redhood_to_normal_skills
                revert_redhood_to_normal_skills(ally)

            # Silver/Ruby Slippers removed from Dorothy: revert skills
            if is_slippers_on_dorothy:
                from combat.ally_skills import revert_dorothy_to_normal_skills
                revert_dorothy_to_normal_skills(ally)

            return f"Unequipped {item['name']} from {display_name(ally)}."
        else:
            return f"Cannot unequip {item['name']} from {display_name(ally)} — your inventory is full!"
    return "Nothing equipped in that slot."


def _ally_to_house_record(ally, stashed_equipment):
    """Build the house record for an ally returning home.

    HP and dispatch state persist on the record (Phase 1 — dispatch injuries
    must survive the party round-trip). A defeated ally comes home at 1 HP
    with a stress bump; house rest / nightly regen handles recovery.
    """
    hp = int(ally.get("current_hp", 0))
    if ally.get("defeated") or hp <= 0:
        hp = 1
        ally["stress"] = min(100, int(ally.get("stress", 0)) + 10)
    record = {
        "key": ally.get("key"),
        "name": ally["name"],
        "nickname": ally.get("nickname", ""),
        "level": ally["level"],
        "affection": ally.get("affection", 30),
        "affection_cap": ally.get("affection_cap", 100),
        "engaged": ally.get("engaged", False),
        "married": ally.get("married", False),
        "exp": ally.get("exp", 0),
        "level_hp_bonus": ally.get("level_hp_bonus", 0),
        "level_cap": ally.get("level_cap", 10),
        "growth_applied": int(ally.get("growth_applied", 0) or 0),
        "attributes": dict(ally.get("attributes", {})),
        "current_hp": max(1, hp),
        "stress": int(ally.get("stress", 0)),
        "consecutive_dispatch": int(ally.get("consecutive_dispatch", 0)),
        "last_dispatch": ally.get("last_dispatch"),
        "last_dispatch_day": int(ally.get("last_dispatch_day", 0) or 0),
        "injured_until": int(ally.get("injured_until", 0) or 0),
        # Awakening — keeps the upgraded kit + displayed name on return home
        "awakened": ally.get("awakened", False),
        "awakened_name": ally.get("awakened_name", ""),
        "awakened_skills": list(ally.get("awakened_skills", []) or []),
        # Heroine facility upgrade skills (own category — not learned skills)
        "upgrade_skills": list(ally.get("upgrade_skills", []) or []),
        # Beating Root — the third accessory slot persists on the house record
        "acc3_unlocked": bool(ally.get("acc3_unlocked", False)),
    }
    if stashed_equipment:
        record["equipped"] = stashed_equipment
    return record


def dismiss_allies_back_to_house(player):
    """Return all active allies to the house's monster_girls list.

    Unequips all gear (returns to player inventory) and restores the girls to the house.
    """
    from inventory import add_item_to_inventory
    allies = player.pop("allies", [])
    if not allies:
        return

    houses = player.get("houses", {})
    if not houses:
        return

    house_city, house = next(iter(houses.items()))
    house.setdefault("monster_girls", [])

    for ally in allies:
        stashed_equipment = {}
        # Skip returning equipped items for temp heroines (their gear is innate)
        if not ally.get("_wonderland_temp"):
            # Return equipped items to player; if inventory is full, stash the
            # item on the house record instead of destroying it.
            for slot in ["weapon", "armor", "accessory1", "accessory2",
                         "accessory3"]:
                item = ally.get("equipped", {}).get(slot)
                if item:
                    if add_item_to_inventory(player, item):
                        ally["equipped"][slot] = None
                    else:
                        c_print(f"Your inventory is full! {item['name']} from {display_name(ally)} was kept in house storage.")
                        stashed_equipment[slot] = item
                        ally["equipped"][slot] = None

        # Add back to house (only if not already there). HP/stress persist.
        existing = [g for g in house["monster_girls"] if g.get("key") == ally["key"] and g.get("name") == ally["name"]]
        if not existing:
            house["monster_girls"].append(_ally_to_house_record(ally, stashed_equipment))


def _return_ally_to_house(player, ally, house):
    """Return a single ally to the house's monster_girls list."""
    from inventory import add_item_to_inventory

    stashed_equipment = {}
    # Skip returning equipped items for temp heroines (their gear is innate)
    if not ally.get("_wonderland_temp"):
        # Return equipped items to player; if inventory is full, stash the
        # item on the house record instead of destroying it.
        for slot in ["weapon", "armor", "accessory1", "accessory2",
                     "accessory3"]:
            item = ally.get("equipped", {}).get(slot)
            if item:
                if add_item_to_inventory(player, item):
                    ally["equipped"][slot] = None
                else:
                    c_print(f"Your inventory is full! {item['name']} from {display_name(ally)} was kept in house storage.")
                    stashed_equipment[slot] = item
                    ally["equipped"][slot] = None

    # Add back to house (only if not already there). HP/stress persist.
    existing = [g for g in house.get("monster_girls", []) if g.get("key") == ally.get("key") and g.get("name") == ally.get("name")]
    if not existing:
        house.setdefault("monster_girls", []).append(_ally_to_house_record(ally, stashed_equipment))


def recruit_ally_from_house(player, girl, house):
    """Recruit a monster girl from house to active party (max 7 allies, 8 total party)."""
    day = player.get("day", 1)
    if girl.get("dispatch_mission"):
        return None, f"{display_name(girl)} is away on a dispatch and can't join the party right now."
    if int(girl.get("injured_until", 0) or 0) > day:
        return None, (f"{display_name(girl)} is injured and recovering until Day "
                      f"{int(girl.get('injured_until', 0))} — she can't join the party yet.")
    allies = player.get("allies", [])
    if len(allies) >= MAX_ALLIES:
        # Party is full — ask who to replace
        ally_names = []
        for i, a in enumerate(allies):
            if a.get("defeated") or a.get("current_hp", 0) <= 0:
                status = "[INCAPACITATED]"
            else:
                status = f"HP {a['current_hp']}/{a['max_hp']}"
            ally_names.append(f"{display_name(a)} — {status}")
        ally_names.append("Cancel")
        from gui.terminal import term
        choice = term.menu(ally_names, prompt=f"Your party is full ({MAX_ALLIES}/{MAX_ALLIES}). Replace which ally?")
        if choice < 0 or choice >= len(allies):
            return None, "Recruitment cancelled."
        replaced = allies[choice]
        _return_ally_to_house(player, replaced, house)
        allies.pop(choice)

    ally = create_ally_from_girl(girl)
    player.setdefault("allies", []).append(ally)

    # Remove from house
    house["monster_girls"] = [g for g in house["monster_girls"]
                                if not (g.get("key") == girl.get("key") and g.get("name") == girl.get("name"))]

    msg = f"{display_name(ally)} has joined your party!"

    # Quest hook: recruitment milestones (Command Resonance backfill)
    from quests import update_quests
    quest_msgs = update_quests(player, "recruit_ally", "any")
    if quest_msgs:
        msg += "\n" + "\n".join(quest_msgs)

    return ally, msg


# ─────────────────────────────────────────────────────────────────────────────
# ALLY COMBAT ACTIONS
# ─────────────────────────────────────────────────────────────────────────────

def _ally_action_menu(ally, player, enemies):
    """Build action menu for an ally. Returns (menu_str, valid_keys, disabled_keys)."""
    actions = []
    disabled_keys = []

    # Check if Black Silence Gloves are equipped — replaces entire skill menu
    from combat.weapon.black_silence_gloves import _actor_has_black_silence_gloves
    has_gloves = _actor_has_black_silence_gloves(ally)
    
    if has_gloves:
        return _ally_gloves_menu(ally, player, enemies)

    # Palette's Brush — replaces class skills with the brush kit
    from combat.weapon.palette_brush import _actor_has_palette_brush, get_brush_action_menu
    if _actor_has_palette_brush(ally):
        return get_brush_action_menu(ally, player, enemies, False)

    actions.append(('a', 'Attack'))
    actions.append(('d', 'Defend'))

    # Abyss Fang – only if equipped and off cooldown
    from combat.weapon.abyss_fang import is_abyss_fang_available
    if is_abyss_fang_available(ally):
        actions.append(('w', 'Wield the Abyss'))

    # Captain's Cutlass – Crew Rally
    from combat.weapon.captain_cutlass import is_captain_cutlass_available
    if is_captain_cutlass_available(ally):
        actions.append(('r', 'Crew Rally'))

    # Author's Pen – Rewrite
    from combat.weapon.authors_pen import is_authors_pen_available
    if is_authors_pen_available(ally):
        actions.append(('e', 'Rewrite'))

    # Switch – only if there are reserve allies to swap with
    if can_switch(player):
        actions.append(('s', 'Switch'))

    # Skills – innate + learned, off cooldown
    from combat.ally_skills import get_usable_skills_in_combat
    usable_skills = get_usable_skills_in_combat(ally)
    for idx, (sid, sdef) in enumerate(usable_skills):
        actions.append((str(idx + 1), sdef['name']))

    # Use item - check if player has usable items
    combat_items = [
        item for item in player.get("inventory", [])
        if item.get("type") in ["consumable", "utility"]
    ]
    if combat_items:
        actions.append(('u', 'Use Item'))

    # Blank Canvas Shawl – free action, once per combat
    from combat.weapon.blank_canvas_shawl import _actor_has_blank_canvas_shawl
    if _actor_has_blank_canvas_shawl(ally) and not ally.get("blank_canvas_used"):
        actions.append(('b', 'Blank Canvas'))

    menu_str = '  '.join(f'[{key.upper()}]{label}' for key, label in actions)
    valid_keys = [key for key, _ in actions if key not in disabled_keys]
    return menu_str, valid_keys, disabled_keys


def _ally_gloves_menu(ally, player, enemies):
    """Build the action menu when an ally has Black Silence gloves equipped."""
    actions = []
    disabled_keys = []

    actions.append(('d', 'Defend'))

    # Switch
    if can_switch(player):
        actions.append(('s', 'Switch'))

    # Workshop attacks 1-9
    workshop_state = ally.get("gloves_workshop_used", set())
    if not isinstance(workshop_state, (set, list)):
        workshop_state = set()
    from combat.weapon.black_silence_gloves import WORKSHOPS
    for wid, ws in WORKSHOPS.items():
        key = str(wid)
        label = f'{ws["name"]} [{ws["stat"][:3].upper()}]'
        if wid in workshop_state:
            actions.append((key, f'{label} [USED]'))
            disabled_keys.append(key)
        else:
            actions.append((key, label))

    # Furioso
    if ally.get("gloves_furioso_available"):
        actions.append(('0', 'FURIOSO'))

    # Use item
    combat_items = [
        item for item in player.get("inventory", [])
        if item.get("type") in ["consumable", "utility"]
    ]
    if combat_items:
        actions.append(('u', 'Use Item'))

    # Blank Canvas Shawl – free action, once per combat
    from combat.weapon.blank_canvas_shawl import _actor_has_blank_canvas_shawl
    if _actor_has_blank_canvas_shawl(ally) and not ally.get("blank_canvas_used"):
        actions.append(('b', 'Blank Canvas'))

    menu_str = '  '.join(f'[{key.upper()}]{label}' for key, label in actions)
    valid_keys = [key for key, _ in actions if key not in disabled_keys]
    return menu_str, valid_keys, disabled_keys


def handle_ally_turn(ally, player, enemies, p_str, p_con, p_dex, p_ler, p_wis, p_cha, on_kill=None):
    """Handle an ally's turn in combat. Player chooses the ally's action.

    Returns: "continue", "victory", "dead", or "retry"
    """
    from combat.combat_ui import print_combat_hud
    from combat.status_effects import is_silenced
    from character import player_max_hp

    # Reset defending flag each turn so it only applies if they choose Defend THIS turn
    ally["defending_this_turn"] = False

    # Per-action status markers (White Knight skill dodge / accuracy penalty)
    for _e in enemies:
        _e.pop("_skill_dodge_used", None)
        _e.pop("_accuracy_penalty_used", None)

    # Palette's Brush: reset the once-per-turn stance flag
    from combat.weapon.palette_brush import begin_actor_turn
    begin_actor_turn(ally)

    # Prescript Ledger: the actor got a turn this round (waiver guard)
    from combat.weapon.prescript_ledger import mark_acted as mark_prescript_acted
    mark_prescript_acted(ally)

    # Palette heroine: color cycle each turn + deferred Signature strike
    from combat.palette_ally import (
        is_palette_ally, has_pending_signature,
        fire_palette_signature, advance_palette_ally_color,
    )
    from combat.weapon.palette_brush import _actor_has_palette_brush, COLOR_NAMES as _BRUSH_COLORS
    if is_palette_ally(ally) and not _actor_has_palette_brush(ally):
        color = advance_palette_ally_color(ally)
        c_print(f"  🎨 {display_name(ally)}'s brush settles on {_BRUSH_COLORS[color]}.")
        if has_pending_signature(ally):
            msg = fire_palette_signature(ally, player, enemies, on_kill)
            c_print(msg)
            return "continue"

    a_str, a_con, a_dex, a_ler, a_wis, a_cha = compute_ally_stats(ally)

    # Show HUD with this ally marked as active (this already renders the menu block)
    print_combat_hud(player, enemies, active_ally=ally)

    # Fetch the actions behind the scenes to keep the tracking list valid
    _, valid_actions, _disabled = _ally_action_menu(ally, player, enemies)

    # REMOVED: Redundant text headers and duplicate action list prints
    action = c_input(f"  ({display_name(ally)}) Choose action: ").strip().lower()
    while action not in valid_actions:
        c_print(f"  Invalid choice. Available: {', '.join(valid_actions)}")
        action = c_input("  Choose: ").strip().lower()

    # ----- SWITCH (ally swaps with a reserve ally, costs their turn) -----
    if action == "s":
        reserve = get_reserve_allies(player)
        if not reserve:
            c_print("  No allies in reserve to switch with.")
            return "retry"

        # Signal to GUI that we're in ally switch mode
        player["_ally_switch_mode"] = True
        player["_ally_switch_front"] = ally["name"]
        try:
            c_print(f"\n  {display_name(ally)} prepares to swap with a reserve ally...")
            c_print("\n  --- BACKUP PARTY (Back Row) ---")
            for i, r_ally in enumerate(reserve):
                c_print(f"  [{i+1}] {display_name(r_ally)} — HP: {r_ally['current_hp']}/{r_ally['max_hp']}")
            c_print("  [0] Cancel")

            try:
                choice = c_input(f"  Pick an ally to swap {display_name(ally)} with: ").strip()
                if choice == "0":
                    return "retry"
                idx = int(choice) - 1
                if idx < 0 or idx >= len(reserve):
                    c_print("  Invalid choice.")
                    return "retry"
                target_reserve = reserve[idx]
                allies_list = player.get("allies", [])
                reserve_abs_idx = allies_list.index(target_reserve)
                front_abs_idx = allies_list.index(ally)
                msg, ok = do_ally_switch(player, front_abs_idx, reserve_abs_idx)
                if ok:
                    c_print(f"  {msg}")
                    return "continue"
                else:
                    c_print(f"  {msg}")
                    return "retry"
            except (ValueError, IndexError):
                c_print("  Invalid choice.")
                return "retry"
        finally:
            player["_ally_switch_mode"] = False
            player.pop("_ally_switch_front", None)

    # ----- WIELD THE ABYSS (Abyss Fang weapon special) -----
    if action == "w":
        from combat.weapon.abyss_fang import _wield_abyss_fang_actor
        result, _def = _wield_abyss_fang_actor(ally, is_player=False)
        return result

    # ----- CREW RALLY (Captain's Cutlass weapon special) -----
    if action == "r":
        from combat.weapon.captain_cutlass import _use_crew_rally_actor
        result, _def = _use_crew_rally_actor(ally, is_player=False, player=player)
        return result

    # ----- REWRITE (Author's Pen accessory special) -----
    if action == "e":
        from combat.weapon.authors_pen import _use_rewrite_actor
        result, _def = _use_rewrite_actor(ally, player=player, is_player=False)
        return result

    # ----- BLANK CANVAS (shawl free action, once per combat) -----
    if action == "b":
        from combat.weapon.blank_canvas_shawl import use_blank_canvas
        for m in use_blank_canvas(ally, False, player):
            c_print(f"  {m}")
        return "retry"

    # ----- BRUSH STANCE (free action, once per turn) -----
    if action == "t":
        from combat.weapon.palette_brush import set_brush_stance
        c_print(set_brush_stance(ally))
        return "retry"

    # ----- BRUSH EXHIBITS (i/k/g) -----
    if action in ("i", "k", "g"):
        from combat.weapon.palette_brush import (
            _actor_has_palette_brush, execute_impasto_exhibit,
            execute_chiaroscuro_exhibit, execute_signature_exhibit,
            get_brush_exhibits,
        )
        if not _actor_has_palette_brush(ally):
            return "retry"
        key_map = {"i": "impasto", "k": "chiaroscuro", "g": "signature"}
        exhibit_key = key_map[action]
        if exhibit_key not in [k for k, _ in get_brush_exhibits(ally)]:
            c_print("  That exhibit is not available yet.")
            return "retry"
        stats = (a_str, a_con, a_dex, a_ler, a_wis, a_cha)
        alive_before = {id(e) for e in enemies if e["hp"] > 0}
        if exhibit_key == "impasto":
            msg, victory = execute_impasto_exhibit(ally, enemies, stats, False)
        elif exhibit_key == "chiaroscuro":
            msg, victory = execute_chiaroscuro_exhibit(ally, enemies, stats, False)
        else:
            msg, victory = execute_signature_exhibit(ally, enemies, stats, False)
        if msg == ACTION_CANCELLED_MSG:
            # Target selection canceled — do not consume the ally's turn.
            c_print(msg)
            return "retry"
        c_print(msg)
        killed = [e for e in enemies if e["hp"] <= 0 and id(e) in alive_before]
        if on_kill:
            for e in killed:
                on_kill(e, enemies)
        from combat.weapon.prescript_ledger import report_skill as report_prescript_skill
        report_prescript_skill(ally)
        if victory:
            return "victory"
        return "continue"

    # ----- SKILLS (numbered 1-9) or GLOVES WORKSHOPS -----
    if action.isdigit():
        # Check if Black Silence Gloves are equipped — workshop attacks replace skills
        from combat.weapon.black_silence_gloves import _actor_has_black_silence_gloves, _execute_workshop_actor, _execute_furioso_actor
        
        if _actor_has_black_silence_gloves(ally):
            if action == '0':
                # FURIOSO
                c_print("\n>>> FURIOSO: All nine workshops in sequence! <<<")
                enemies_before = [e for e in enemies if e["hp"] > 0]
                msg, victory = _execute_furioso_actor(
                    ally, enemies, a_str, a_con, a_dex, a_ler, a_wis, a_cha, is_player=False,
                )
                c_print(msg)
                # Fire on_kill for enemies actually killed by the attack (snapshot before side effects)
                if on_kill:
                    killed_by_attack = [e for e in enemies_before if e["hp"] <= 0]
                    for e in killed_by_attack:
                        on_kill(e, enemies)
                from combat.weapon.prescript_ledger import report_skill as report_prescript_skill
                report_prescript_skill(ally)
                if victory:
                    return "victory"
                return "continue"
            else:
                workshop_id = int(action)
                if workshop_id < 1 or workshop_id > 9:
                    c_print("  Invalid workshop choice.")
                    return "retry"
                ws_used = ally.get("gloves_workshop_used", set())
                if not isinstance(ws_used, (set, list)):
                    ws_used = set()
                if workshop_id in ws_used:
                    c_print("  That workshop has already been used this cycle!")
                    return "retry"
                from combat.weapon.black_silence_gloves import WORKSHOPS
                ws = WORKSHOPS.get(workshop_id, {})
                ws_name = ws.get("name", f"Workshop {workshop_id}")
                ws_desc = ws.get("desc", "")
                c_print(f"\n>>> {ws_name}: {ws_desc}")
                c_input("  Press Enter to use it...")
                enemies_before = [e for e in enemies if e["hp"] > 0]
                msg, victory = _execute_workshop_actor(
                    ally, enemies, workshop_id,
                    a_str, a_con, a_dex, a_ler, a_wis, a_cha, is_player=False,
                )
                if msg == ACTION_CANCELLED_MSG:
                    # Target selection canceled — do not consume the ally's turn.
                    c_print(msg)
                    return "retry"
                c_print(msg)
                # Fire on_kill for enemies actually killed by the attack (snapshot before side effects)
                if on_kill:
                    killed_by_attack = [e for e in enemies_before if e["hp"] <= 0]
                    for e in killed_by_attack:
                        on_kill(e, enemies)
                from combat.weapon.prescript_ledger import report_skill as report_prescript_skill
                report_prescript_skill(ally)
                if victory:
                    return "victory"
                return "continue"

        # Normal skills (no gloves)
        from combat.ally_skills import get_usable_skills_in_combat, execute_ally_skill, format_ally_mastery_label
        if is_silenced(ally):
            c_print(f"  {display_name(ally)} is silenced and cannot use skills!")
            return "retry"

        skill_idx = int(action) - 1
        usable_skills = get_usable_skills_in_combat(ally)
        if skill_idx < 0 or skill_idx >= len(usable_skills):
            c_print("  Invalid skill choice.")
            return "retry"

        skill_id, skill_def = usable_skills[skill_idx]
        from combat.combat_ui import format_skill_elemental_tag
        elem_tag = format_skill_elemental_tag(skill_def)
        c_print(f"\n  >> {skill_def['name']}{elem_tag}: {skill_def['description']}")
        mastery_label = format_ally_mastery_label(skill_id, ally)
        if mastery_label:
            c_print(f"      Mastery: {mastery_label}")
        c_input("  Press Enter to use it...")

        all_allies = player.get("allies", [])
        # Track alive enemies before skill so on_kill can fire for newly-dead ones.
        # Snapshot which enemies were actually killed by the skill BEFORE any
        # on_kill side effects (e.g. boss death destroying linked minions).
        alive_before = {id(e) for e in enemies if e["hp"] > 0}
        msg, victory = execute_ally_skill(ally, player, skill_id, skill_def, enemies, all_allies)
        if msg == ACTION_CANCELLED_MSG:
            # Target selection canceled — reopen the menu, no turn or cooldown cost.
            c_print(f"  {msg}")
            return "retry"
        c_print(f"  {msg}")
        # Determine enemies killed by the skill (before on_kill side effects)
        killed_by_skill = [e for e in enemies if e["hp"] <= 0 and id(e) in alive_before]
        if on_kill:
            for e in killed_by_skill:
                on_kill(e, enemies)
        from combat.weapon.prescript_ledger import report_skill as report_prescript_skill
        report_prescript_skill(ally)
        if victory:
            return "victory"
        return "continue"

    # ----- ATTACK -----
    if action == "a":
        if len(enemies) > 1:
            try:
                choice = int(c_input("  Select target number: ")) - 1
                if choice < 0 or choice >= len(enemies):
                    c_print("  Invalid target selection.")
                    return "retry"
                target = enemies[choice]
            except ValueError:
                c_print("  Please enter a valid number.")
                return "retry"
        else:
            target = enemies[0]

        # --- ENEMY DODGE CHECK ---
        from combat.stats import roll_dodge
        is_dodged, dodge_chance = roll_dodge(target, ally, extra_chance=target.get("ally_accuracy_penalty", 0.0))
        if is_dodged:
            c_print(f"  The {target['name']} dodges {display_name(ally)}'s attack!")
            return "continue"

        # ── Wonderland Shadow: Caterpillar's Smoke — accuracy penalty ──
        from wonderland_curses import get_shadow_accuracy_penalty
        smoke_penalty = get_shadow_accuracy_penalty(player)
        if smoke_penalty > 0 and random.random() < smoke_penalty:
            c_print(f"  💨 The smoke clouds {display_name(ally)}'s vision — the attack goes wide!")
            return "continue"

        # ── Event Horizon: The Fool — a 10% chance the attack simply fails ──
        from event_horizon import joker_attack_missed
        if joker_attack_missed(ally):
            return "continue"

        equipped_weapon = ally.get("equipped", {}).get("weapon")
        raw_scaling = equipped_weapon.get("scaling_stat", ["Strength"]) if equipped_weapon else ["Strength"]
        scaling_stats = raw_scaling if isinstance(raw_scaling, list) else [raw_scaling]

        scaling_val = 0
        for stat in scaling_stats:
            if stat == "Strength":
                scaling_val += a_str
            elif stat == "Dexterity":
                scaling_val += a_dex
            elif stat == "Constitution":
                scaling_val += a_con
            elif stat == "Learning":
                scaling_val += a_ler
            elif stat == "Wisdom":
                scaling_val += a_wis
            elif stat == "Charisma":
                scaling_val += a_cha
            else:
                from combat.stats import get_effective_attribute
                scaling_val += get_effective_attribute(ally, stat)

        # Apply weapon's scaling_mult (e.g. Constitution weapons use 0.5 for half scaling)
        if equipped_weapon and equipped_weapon.get("scaling_mult"):
            scaling_val = int(scaling_val * equipped_weapon["scaling_mult"])

        # ── Elemental Trait: pre-damage modifiers (Sunder, Pierce) ──
        from combat.elemental_traits import get_trait_for_weapon, apply_trait_pre_damage
        trait = get_trait_for_weapon(equipped_weapon, equipped_weapon.get("rarity", "common")) if equipped_weapon else None
        pre_dmg = apply_trait_pre_damage(trait, target) if trait else None

        from combat.stat_milestones import get_strength_bonus
        # ── Sunder (Physical trait): armor penetration ──
        effective_con_mod = target["con_mod"]
        if pre_dmg and pre_dmg.get("armor_pen", 1.0) < 1.0:
            effective_con_mod = int(target["con_mod"] * pre_dmg["armor_pen"])
            if effective_con_mod < target["con_mod"]:
                c_print(f"  ⚔️ Sunder! {target['name']}'s armor is reduced.")
        dmg = random.randint(3, 8) + scaling_val + get_strength_bonus(ally) - effective_con_mod
        dmg = max(0, dmg)

        # Consume power_buff (empowers this attack — e.g. Overclock from an ally)
        for buff in ally.get("active_buffs", [])[:]:
            if buff.get("type") == "power_buff":
                val = buff.get("value", 0)
                dmg = int(dmg * (1 + val))
                ally["active_buffs"].remove(buff)
                c_print(f"  ⚡ {display_name(ally)} is Empowered! Damage increased by {int(val * 100)}%!")
                break

        # Hunter's Mark: increased damage taken
        if target.get("hunters_mark"):
            mark_bonus = target.get("hunters_mark_bonus", 0.15)
            dmg = int(dmg * (1 + mark_bonus))

        # Damage-taken amplification (e.g. Aura of Despair)
        from combat.status_effects import get_damage_taken_multiplier
        dt_mult = get_damage_taken_multiplier(target)
        if dt_mult != 1.0:
            dmg = int(dmg * dt_mult)

        # Apply damage_boost buffs (multi-turn, non-consuming)
        for buff in ally.get("active_buffs", []):
            if buff.get("type") == "damage_boost":
                dmg = int(dmg * (1 + buff.get("value", 0)))

        # Event Horizon: The Hierophant — basic attacks ×0.75
        from event_horizon import joker_damage_multiplier
        dmg = int(dmg * joker_damage_multiplier(ally, "basic"))

        # Critical hit check (crit chance over the cap converts to crit damage)
        from combat.stats import (roll_critical_hit, apply_critical_damage,
                                  format_critical_tag, CRIT_MULTIPLIER)
        is_crit, _, overflow_crit = roll_critical_hit(ally, "ally", dex=a_dex, lrn=a_ler)
        dmg = apply_critical_damage(dmg, is_crit, multiplier=CRIT_MULTIPLIER + overflow_crit)

        # Event Horizon: The Sun — crits +30%, non-crits ×0.85
        from event_horizon import joker_crit_modifier
        dmg = joker_crit_modifier(ally, is_crit, dmg)

        # Apply elemental damage
        from combat.elemental import calculate_elemental_damage
        element = None
        if equipped_weapon and "elemental_dmg" in equipped_weapon:
            from combat.elemental import get_attack_element
            element = get_attack_element(ally, equipped_weapon)
        final_dmg = calculate_elemental_damage(dmg, ally, target, element)

        # Palette's Brush: stance damage multiplier
        from combat.weapon.palette_brush import get_brush_damage_mult
        final_dmg = int(final_dmg * get_brush_damage_mult(ally))

        # ── Pierce (Magical trait): ignore portion of enemy elemental resistance ──
        if pre_dmg and pre_dmg.get("res_ignore", 0) > 0 and element:
            target_res = target.get("elemental_res", {}).get(element, 1.0)
            if target_res < 1.0:
                attacker_dmg_mult = ally.get("elemental_dmg", {}).get(element, 1.0)
                mitigated_res = 1.0 + (target_res - 1.0) * (1.0 - pre_dmg["res_ignore"])
                final_dmg = int(dmg * attacker_dmg_mult * mitigated_res)
                final_dmg = max(0, final_dmg)
                c_print(f"  🔮 Pierce! {target['name']}'s {element} resistance is partially bypassed.")

        # Captain's Cutlass: High Tide + Rally attack bonuses
        from combat.weapon.captain_cutlass import get_high_tide_attack_bonus, get_rally_attack_bonus
        final_dmg += get_high_tide_attack_bonus(ally, final_dmg)
        final_dmg += get_rally_attack_bonus(ally, final_dmg)
        final_dmg = max(0, final_dmg)

        # Pandemonium: Weakened Resolve curse — allies deal less damage too
        from pandemonium_curses import apply_damage_dealt_multiplier
        final_dmg = apply_damage_dealt_multiplier(player, final_dmg)
        
        # Wonderland: Jabberwock's Bane — bonus damage vs boss enemies
        if target.get("boss"):
            from wonderland_curses import get_jabberwock_bane_multiplier
            bane_mult = get_jabberwock_bane_multiplier(player)
            if bane_mult > 0:
                bonus_dmg = int(final_dmg * bane_mult)
                final_dmg += bonus_dmg
                if bonus_dmg > 0:
                    c_print(f"  ⚔️ Vorpal blessing surges! +{bonus_dmg} bonus damage!")
        
        # Race passive damage bonuses (Angel vs Demons, Clockwork vs shocked)
        from combat.ally_skills import get_race_damage_multiplier
        _race_mult = get_race_damage_multiplier(ally, target)
        if _race_mult != 1.0:
            final_dmg = int(final_dmg * _race_mult)

        # Event Horizon trophies: Old Dopo Robe + Chance and Choice (single hit)
        from combat.weapon.dopo_robe import get_robe_multiplier
        final_dmg = int(final_dmg * get_robe_multiplier(ally, player))
        from combat.weapon.chance_and_choice import apply_chance_and_choice
        final_dmg = apply_chance_and_choice(ally, final_dmg)

        target["hp"] -= final_dmg
        # Event Horizon — Death: allies drain 10% of the damage dealt
        _eh_ls = ally.get("_eh_joker_lifesteal", 0) or 0
        if _eh_ls > 0 and final_dmg > 0:
            _eh_heal = int(final_dmg * _eh_ls)
            if _eh_heal > 0:
                from combat.status_effects import apply_healing as _eh_apply_heal
                _eh_actual = _eh_apply_heal(ally, _eh_heal, source=ally)
                if _eh_actual > 0:
                    c_print(f"  [Death] {display_name(ally)} drains {_eh_actual} HP.")
        # ── Sky Piercer: execute non-superboss enemies left at/below threshold ──
        from combat.weapon.sky_piercer import check_sky_piercer_execute
        check_sky_piercer_execute(ally, target, final_dmg)
        # Last Oath (unique rapier): basic attacks apply Expose
        from combat.weapon.last_oath import try_last_oath_expose
        _lo_msg = try_last_oath_expose(ally, target, is_crit)
        if _lo_msg:
            c_print(_lo_msg)
        # Palette's Brush: strokes, Pigment Explosion, aura procs
        from combat.weapon.palette_brush import _actor_has_palette_brush, on_brush_attack_hit
        if _actor_has_palette_brush(ally):
            for m in on_brush_attack_hit(ally, target, final_dmg, enemies):
                c_print(f"  {m}")
        # ── Elemental Trait: on-hit effects (Ignite, Chain, Leech, Swift, Bulwark) ──
        if trait:
            from combat.elemental_traits import apply_trait
            apply_trait(trait, ally, target, enemies, final_dmg)

        # Vileheart Pendant: chance to poison on physical hit
        from combat.vileheart_venom import try_vileheart_venom_proc
        if try_vileheart_venom_proc(ally, target):
            c_print(f"  🧪 Vileheart Pendant: {target['name']} is poisoned!")

        # ── Grandmother's Axe / Woodcutter's Broken Axe: bleed-pop passive ──
        if equipped_weapon and target["hp"] > 0:
            weapon_special = equipped_weapon.get("special", "")
            if weapon_special in ("grandmothers_axe", "woodcutter_broken"):
                # Check if target is bleeding
                bleed_debuff = None
                for d in target.get("active_debuffs", []):
                    if d.get("type") == "bleed":
                        bleed_debuff = d
                        break
                if bleed_debuff:
                    chance = 0.40 if weapon_special == "grandmothers_axe" else 0.20
                    if random.random() < chance:
                        from combat.status_effects import detonate_bleed
                        det_dmg, det_msgs = detonate_bleed(target)
                        for det_msg in det_msgs:
                            c_print(f"  {det_msg}")
                        # No heal — pure damage pop (unlike Chrysalis)
                        if target["hp"] <= 0:
                            if on_kill:
                                on_kill(target, enemies)
                            # ── Elemental Trait: on-kill effects (Douse, Purge) ──
                            if trait:
                                from combat.elemental_traits import apply_trait_on_kill
                                apply_trait_on_kill(trait, ally, target, enemies)
                            c_print(f"  {display_name(ally)} defeated {target['name']}!")

        # Apply race passive life steal (Vampire; doubled while the target bleeds)
        from combat.ally_skills import get_race_lifesteal, get_race_passive
        from combat.status_effects import get_bleed_feast_multiplier
        race_passive = get_race_passive(ally.get("race"))
        rp_ls = get_race_lifesteal(ally)
        if race_passive and rp_ls > 0 and final_dmg > 0:
            heal = int(final_dmg * rp_ls * get_bleed_feast_multiplier(target))
            old_hp = ally["current_hp"]
            ally["current_hp"] = min(old_hp + heal, ally["max_hp"])
            actual = ally["current_hp"] - old_hp
            if actual > 0:
                c_print(f"  [{race_passive['name']}] {display_name(ally)} recovers {actual} HP!")

        verb = "strikes"
        if "Dexterity" in scaling_stats:
            verb = "shoots" if "bow" in equipped_weapon.get("id", "") else "pierces"
        elif "Learning" in scaling_stats:
            verb = "blasts"

        crit_tag = format_critical_tag(is_crit)
        is_crit_bool = bool(crit_tag)
        from combat.helpers import format_damage_msg
        c_print("  " + format_damage_msg(display_name(ally), target['name'], final_dmg, element=element, crit=is_crit_bool))
        if target["hp"] <= 0:
            if on_kill:
                on_kill(target, enemies)
            # ── Elemental Trait: on-kill effects (Douse, Purge) ──
            if trait:
                from combat.elemental_traits import apply_trait_on_kill
                apply_trait_on_kill(trait, ally, target, enemies)
            c_print(f"  {display_name(ally)} defeated {target['name']}!")
            # Captain's Cutlass: High Tide stack on kill (player and ally wielders)
            from combat.weapon.captain_cutlass import check_high_tide_kill
            check_high_tide_kill(ally, target)
            check_high_tide_kill(player, target)
        else:
            # Orc race passive: chance to stun on a basic attack
            from combat.ally_skills import maybe_stun_on_basic
            _stun_msg = maybe_stun_on_basic(ally, target)
            if _stun_msg:
                c_print(f"  {_stun_msg}")
        return "continue"

    # ----- DEFEND -----
    elif action == "d":
        c_print(f"  {display_name(ally)} braces for impact, raising their guard.")
        ally["defending_this_turn"] = True
        from combat.weapon.prescript_ledger import report_defend as report_prescript_defend
        report_prescript_defend(ally)
        return "continue"

    # ----- USE ITEM -----
    elif action == "u":
        combat_items = [
            (idx, item) for idx, item in enumerate(player.get("inventory", []))
            if item.get("type") in ["consumable", "utility"]
        ]
        if not combat_items:
            c_print("  No usable items in the shared inventory.")
            return "retry"

        c_print("\n  Shared Battle Inventory:")
        for display_idx, (_, itm) in enumerate(combat_items):
            qty = itm.get("count", 1)
            qty_str = f" x{qty}" if qty > 1 else ""
            c_print(f"  {display_idx+1}. {itm['name']}{qty_str} ({itm['type']})")

        try:
            choice = int(c_input("  Use which item? (0 to cancel): ")) - 1
            if choice < 0 or choice >= len(combat_items):
                return "retry"
            true_idx, item = combat_items[choice]
            msg = ""
            target = None

            # ── Fractured Hourglass: reusable free-action cooldown reduction ──
            from combat.fractured_hourglass import is_fractured_hourglass, use_fractured_hourglass
            if is_fractured_hourglass(item):
                if use_fractured_hourglass(ally, is_player=False):
                    from combat.weapon.prescript_ledger import report_item as report_prescript_item
                    report_prescript_item(ally)
                # Free action — the ally's turn is not consumed either way.
                return "retry"

            # ── Potion Sickness: only blocks healing consumables (not buffs/utility items) ──
            is_healing_item = (
                item.get("type") == "consumable" and
                item.get("power", 0) > 0
            )
            if is_healing_item and ally.get("potion_sickness", 0) > 0:
                c_print(f"  {display_name(ally)} is still queasy from the last potion! ({ally['potion_sickness']} turn(s) remaining)")
                return "retry"

            # Items that need an enemy target: utility items with debuff/damage keys.
            # Consumables never need a target (they always affect the user).
            # Escape/flee/capture items handle their own target logic separately.
            affects_enemy = (
                any(k in item for k in ["status", "blind_enemy", "damage_over_time",
                                         "poison_damage", "stun_chance", "expose_armor",
                                         "burn_tier", "shock_damage"]) or
                (item.get("type") == "utility" and
                 item.get("power", item.get("base_power", 0)) > 0 and
                 "escape_bonus" not in item and
                 not item.get("fixed_flee") and
                 not item.get("capture_net"))
            )
            if affects_enemy:
                if len(enemies) > 1:
                    try:
                        t_choice = int(c_input(f"  Select target for {item['name']}: ")) - 1
                        if t_choice < 0 or t_choice >= len(enemies):
                            c_print("  Invalid target choice.")
                            return "retry"
                        target = enemies[t_choice]
                    except ValueError:
                        c_print("  Invalid input.")
                        return "retry"
                else:
                    target = enemies[0]

            # Healing items affect the ally using them
            if "power" in item and item.get("type") == "consumable":
                old_hp = ally["current_hp"]
                new_hp = min(old_hp + item["power"], ally["max_hp"])
                healed_amount = new_hp - old_hp
                ally["current_hp"] = new_hp
                msg += f"{display_name(ally)} recovers {healed_amount} HP. "

            if "heal_over_time" in item:
                ally.setdefault("active_buffs", []).append({
                    "type": "hot",
                    "value": item["heal_over_time"],
                    "remaining": item.get("duration", 3)
                })
                msg += f"{display_name(ally)} starts regenerating {item['heal_over_time']} HP each turn. "

            if "temp_stat" in item:
                stat = item["temp_stat"]
                val = item.get("base_power", 3)
                ally.setdefault("active_buffs", []).append({
                    "stat": stat,
                    "value": val,
                    "remaining": item.get("duration", 4)
                })
                msg += f"{display_name(ally)}'s {stat} increases by {val} for {item.get('duration',4)} turns. "

            if "defense_buff" in item:
                ally.setdefault("active_buffs", []).append({
                    "type": "defense",
                    "value": item["defense_buff"],
                    "remaining": item.get("duration", 3)
                })
                msg += f"Damage taken by {display_name(ally)} reduced by {item['defense_buff']} for {item.get('duration',3)} turns. "

            if item.get("cure_curse"):
                from combat.status_effects import cure_curse
                result = cure_curse(ally)
                if result == "cured":
                    msg += "The dark curse is lifted! "
                else:
                    msg += "Not cursed. "

            if item.get("cure_poison"):
                before = len([d for d in ally.get("active_debuffs", []) if d["type"] == "poison"])
                ally["active_debuffs"] = [d for d in ally.get("active_debuffs", []) if d["type"] != "poison"]
                after = len([d for d in ally.get("active_debuffs", []) if d["type"] == "poison"])
                if before > after:
                    msg += "The poison is cleansed. "
                else:
                    msg += "Not poisoned. "

            if item.get("expose_armor"):
                if target is None:
                    # Fallback: affects_enemy should have caught this; if not, pick first alive enemy
                    alive = [e for e in enemies if e["hp"] > 0]
                    if alive:
                        target = alive[0]
                    else:
                        c_print("  No valid target for armour shatter!")
                        return "retry"
                from combat.status_effects import apply_expose
                result, new_con = apply_expose(target, item["expose_armor"])
                if result == "applied":
                    msg += f"{target['name']}'s armour is shattered! Armour reduced to {new_con}. "
                elif result == "resisted":
                    msg += f"{target['name']} shrugs off the armour shatter! "
                else:
                    msg += f"{target['name']}'s armour is already fully exposed! "
            if item.get("burn_tier"):
                from combat.status_effects import apply_burn
                result = apply_burn(target, tier=item["burn_tier"], duration=item.get("burn_duration", 3))
                if result == "applied":
                    msg += f"{target['name']} catches fire! "
                elif result == "upgraded":
                    msg += f"The flames intensify on {target['name']}! "
                elif result == "intensified":
                    msg += f"The blaze grows stronger on {target['name']}! "
                elif result == "resisted":
                    msg += f"{target['name']} shrugs off the flames! "
                else:
                    msg += f"The burn on {target['name']} is refreshed. "
            if item.get("shock_damage"):
                from combat.status_effects import apply_shock
                result = apply_shock(target, item["shock_damage"], item.get("shock_duration", 3))
                if result == "applied":
                    msg += f"{target['name']} is jolted with electricity! "
                elif result == "resisted":
                    msg += f"{target['name']} shrugs off the shock! "
                else:
                    msg += f"The shock on {target['name']} is renewed! "
            if item.get("type") == "utility" and "damage_over_time" not in item and "stun_chance" not in item:
                item_power = item.get("power", item.get("base_power", 0))
                if item_power > 0:
                    from combat.stat_milestones import get_dexterity_damage_bonus_for_ally
                    dmg = item_power + get_dexterity_damage_bonus_for_ally(ally)
                    armor = target["con_mod"]
                    if "armor_pierce" in item:
                        armor = max(0, armor - item["armor_pierce"])
                        msg += f"(ignores {item['armor_pierce']} armor) "
                    final_dmg = max(1, dmg - armor)
                    target["hp"] -= final_dmg
                    # ── Sky Piercer: execute non-superboss enemies left at/below threshold ──
                    from combat.weapon.sky_piercer import check_sky_piercer_execute
                    check_sky_piercer_execute(ally, target, final_dmg)
                    from combat.helpers import format_damage_msg
                    msg += format_damage_msg(display_name(ally), target['name'], final_dmg, skill_name=item.get('name', 'Item')) + " "

            if "poison_damage" in item:
                from combat.status_effects import apply_poison
                if apply_poison(target, item["poison_damage"], item.get("poison_duration", 3)) != "resisted":
                    msg += f"{target['name']} is poisoned! "

            if "stun_chance" in item:
                if random.random() < item["stun_chance"]:
                    from combat.status_effects import check_status_resisted
                    if check_status_resisted(target):
                        msg += f"{target['name']} shrugs off the stun! "
                    else:
                        target["stunned"] = True
                        msg += f"{target['name']} is stunned! "
                else:
                    msg += "The stun attempt fails. "

            if item.get("status") == "slow":
                from combat.status_effects import apply_slow_to_enemy
                apply_slow_to_enemy(target, duration=item.get("slow_duration", 2))
                msg += f"{target['name']} is slowed. "

            if item.get("blind_enemy"):
                from combat.status_effects import check_status_resisted
                if check_status_resisted(target):
                    msg += f"{target['name']} shrugs off the blinding powder. "
                else:
                    target["blinded"] = True
                    target.setdefault("active_debuffs", []).append({
                        "type": "blind",
                        "remaining": 3
                    })
                    msg += f"{target['name']} is blinded. "

            c_print(f"  {msg}")
            remove_item_by_reference(player, item)
            from combat.weapon.prescript_ledger import report_item as report_prescript_item
            report_prescript_item(ally)
            if is_healing_item:
                ally["potion_sickness"] = 2

            if not [e for e in enemies if e["hp"] > 0]:
                return "victory"
            if ally["current_hp"] <= 0:
                return "dead"

        except (ValueError, IndexError):
            c_print("  Invalid choice.")
            return "retry"
        return "continue"

    return "retry"


# ══════════════════════════════════════════════════════════════════════════════
# Wonderland Heroine System (Phase 17 & 18)
# ══════════════════════════════════════════════════════════════════════════════

HEROINE_ALLY_STAT_PER_LEVEL = 0.22   # Heroines get +0.22 stats per level (vs 0.18 for regular)
HEROINE_ALLY_HP_PER_LEVEL = 4        # HP = base_hp + (level - 1) * 4

_HEROINE_TEMPLATE_KEYS = {
    "alice":     "wonderland_alice",
    "red_hood":  "wonderland_red_hood",
    "dorothy":   "wonderland_dorothy",
    "palette":   "wonderland_palette",
}

_HEROINE_TEMPLATE_KEYS_INVERSE = {v: k for k, v in _HEROINE_TEMPLATE_KEYS.items()}

_HEROINE_INTERNAL_KEYS = {
    "alice":     "wl_alice_state",
    "red_hood":  "wl_redhood_state",
    "dorothy":   "wl_dorothy_state",
    "palette":   "palette_state",
}

_HEROINE_PERMANENT_FLAGS = {
    "alice":     "wonderland_heroine_alice_permanent",
    "red_hood":  "wonderland_heroine_redhood_permanent",
    "dorothy":   "wonderland_heroine_dorothy_permanent",
    "palette":   "palette_heroine_permanent",
}

# ── Auto-equip builds for temp heroines (4 slots per heroine) ──────────
# Each tuple is (weapon_id, armor_id, accessory1_id, accessory2_id)
_HEROINE_EQUIPMENT_BUILDS = {
    "alice":    ("inferno_greatsword", "blaze_battle_harness", "stone_belt", "ember_bracers"),
    "red_hood": ("zephyr_bow", "shadow_wraps", "gale_boots", "cyclone_anklet"),
    "dorothy":  ("nether_grimoire", "arcane_vestments", "mystic_crown", "astral_ring"),
}

def _get_heroine_floor_rarity(floor):
    """Determine equipment rarity for a heroine based on the floor they join.
    
    Returns (rarity_str, enhance_level) tuple.
    """
    if floor <= 20:
        return "common", 5
    elif floor <= 35:
        return "uncommon", 5
    elif floor <= 45:
        return "rare", 5
    else:
        return "epic", 5


def _auto_equip_heroine(ally, heroine_key, floor):
    """Auto-equip a temp heroine with 4 pieces of gear based on floor tier.
    
    The gear is built directly onto the ally — it does NOT go through the
    player's inventory. This represents the heroine's own starting equipment.
    
    Args:
        ally: the heroine ally dict (mutated in-place)
        heroine_key: "alice", "red_hood", or "dorothy"
        floor: the dungeon floor at which they joined
    """
    from resources.items import build_item

    build = _HEROINE_EQUIPMENT_BUILDS.get(heroine_key)
    if not build:
        return

    rarity, enhance = _get_heroine_floor_rarity(floor)

    slot_map = ["weapon", "armor", "accessory1", "accessory2"]
    for item_id, slot in zip(build, slot_map):
        try:
            item = build_item(item_id, rarity=rarity, enhance=enhance)
            ally["equipped"][slot] = item
        except KeyError:
            # Skip if item_id doesn't exist (safety)
            pass

    # Recalculate elemental profile after equipping
    from combat.elemental import compute_ally_elemental
    e_res, e_dmg = compute_ally_elemental(ally)
    ally["elemental_res"] = e_res
    ally["elemental_dmg"] = e_dmg


def compute_heroine_temp_stats(base_mods, player_level):
    """Compute heroine stats at player level using heroine formula.
    
    Heroines use: stat = max(1, base_mod + (player_level - 1) * 0.22)
    No 0.85 multiplier — heroines are special characters.
    """
    from resources.races_classes import ATTRIBUTES
    scaled = {}
    for attr in ATTRIBUTES:
        base = base_mods.get(attr, 0)
        scaled[attr] = max(1, int(base + (player_level - 1) * HEROINE_ALLY_STAT_PER_LEVEL))
    return scaled


def create_heroine_ally(player, heroine_key, floor=None):
    """Create a combat-ready heroine ally scaled to player level.
    
    Args:
        player: player dict
        heroine_key: "alice", "red_hood", or "dorothy"
        floor: current dungeon floor (for auto-equip scaling); defaults to 1 if None
    
    Returns:
        ally dict ready for combat, or None if template not found
    """
    from resources.enemies import ENEMIES
    from combat.elemental import compute_ally_elemental
    from resources.races_classes import ATTRIBUTES

    template_key = _HEROINE_TEMPLATE_KEYS.get(heroine_key)
    if not template_key:
        return None

    template = ENEMIES.get(template_key)
    if not template:
        return None

    player_level = player.get("level", 1)

    # Compute stats using heroine formula
    base_mods = template.get("mods", {})
    scaled_attrs = compute_heroine_temp_stats(base_mods, player_level)

    # Compute HP: base_hp + (level - 1) * 4
    base_hp = template.get("base_hp", 20)
    hp = base_hp + (player_level - 1) * HEROINE_ALLY_HP_PER_LEVEL

    race = template.get("race", "Human")
    name = template.get("name", heroine_key.title())

    ally = {
        "name": name,
        "key": template_key,
        "level": player_level,           # Frozen at join level
        "attributes": scaled_attrs,
        "current_hp": hp,
        "max_hp": hp,
        "equipped": {"weapon": None, "armor": None, "accessory1": None, "accessory2": None},
        "active_buffs": [],
        "active_debuffs": [],
        "blinded": False,
        "slowed": False,
        "stunned": False,
        "frozen": False,
        "cursed": False,
        "dreaded": False,
        "silenced": False,
        "is_ally": True,
        "affection": 50,
        "affection_cap": 100,
        "engaged": False,
        "married": False,
        "monster_girl": False,
        "exp": 0,
        "level_hp_bonus": max(0, (player_level - 1) * 4),
        "level_cap": 10,
        "defeated": False,
        # Heroine-specific fields
        "_heroine_key": heroine_key,
        "_wonderland_temp": True,
        "_heroine_passive": template.get("_heroine_passive"),
        # Skill system
        "passive_skill": None,
        "innate_skills": [],
        "learned_skills": [],
        "upgrade_skills": [],
        "learning": None,
        "skill_cooldowns": {},
        "skill_mastery": {},
        "race": race,
    }

    # Add elemental stats
    e_res, e_dmg = compute_ally_elemental(ally)
    ally["elemental_res"] = e_res
    ally["elemental_dmg"] = e_dmg

    # Initialize skill system
    from combat.ally_skills import initialize_ally_skills
    initialize_ally_skills(ally, template_key, race)

    # Auto-equip based on floor tier and build (temp heroines only)
    effective_floor = floor if floor is not None else player.get("saved_dungeon_floor", 1)
    _auto_equip_heroine(ally, heroine_key, effective_floor)

    return ally


def promote_heroine_to_permanent(player, ally, join_level=None):
    """Promote a temp heroine to permanent status.
    
    Called when the heroine's associated superboss is defeated.
    
    - Freezes stats at current values
    - Sets exp to 0 so they can start gaining XP
    - Enables equipment slots
    - Sets high base affection
    - Marks _wonderland_temp = False
    
    Args:
        player: player dict
        ally: the heroine ally dict
        join_level: the level at which they joined (frozen level)
    """
    if join_level is None:
        join_level = ally.get("level", 1)

    ally["_wonderland_temp"] = False
    ally["level"] = join_level
    ally["level_hp_bonus"] = max(0, (join_level - 1) * 4)
    ally["exp"] = 0
    ally["affection"] = 60  # High base — they chose to stay
    ally["affection_cap"] = 100
    ally["level_cap"] = 99  # No cap for permanent heroines

    # Preserve ALL equipped items on promote (not just quest items)
    # This fixes the bug where auto-equip gear was being deleted when a
    # heroine became permanent.  Quest items (Vorpal Blade, Grandmother's
    # Axe, Ruby Slippers) are now preserved alongside any other gear the
    # heroine was wearing.
    old_equipped = ally.get("equipped", {})
    ally["equipped"] = {
        "weapon": old_equipped.get("weapon"),
        "armor": old_equipped.get("armor"),
        "accessory1": old_equipped.get("accessory1"),
        "accessory2": old_equipped.get("accessory2"),
    }

    # Strip wonderland_only flag from equipped items now that the heroine
    # is permanent — these items will exist outside Wonderland.
    for slot in ally["equipped"]:
        item = ally["equipped"].get(slot)
        if item and item.get("wonderland_only"):
            item.pop("wonderland_only", None)

    ally["monster_girl"] = False

    # Grant permanent unlock passive skill
    heroine_key = ally.get("_heroine_key")
    perm_passive_map = {
        "alice":    "vorpal_instinct",
        "red_hood": "grandmothers_lesson",
        "dorothy":  "somewhere_over_rainbow",
        "palette":  "living_pigment",
    }
    perm_passive = perm_passive_map.get(heroine_key)
    if perm_passive:
        ally["_heroine_permanent_passive"] = perm_passive

    return ally


def get_heroine_passive_def(passive_id):
    """Get the definition for a heroine passive skill."""
    from combat.ally_skills import _load_innate_and_learnable
    _, learnable_data = _load_innate_and_learnable()
    heroine_passives = learnable_data.get("heroine_passives", {})
    return heroine_passives.get(passive_id)


def get_heroine_in_party(player, heroine_key):
    """Find a heroine in the player's party by key ("alice", "red_hood", "dorothy")."""
    for ally in player.get("allies", []):
        if ally.get("_heroine_key") == heroine_key:
            return ally
    return None


def set_heroine_state(player, heroine_key, state):
    """Set the state of a heroine quest line.
    
    Args:
        player: player dict
        heroine_key: "alice", "red_hood", or "dorothy"
        state: "unmet", "intro", "temp", "permanent", or "declined"
    """
    state_key = _HEROINE_INTERNAL_KEYS.get(heroine_key)
    if state_key:
        player[state_key] = state

    if state == "permanent":
        perm_key = _HEROINE_PERMANENT_FLAGS.get(heroine_key)
        if perm_key:
            player[perm_key] = True


def get_heroine_state(player, heroine_key):
    """Get the current state of a heroine quest line."""
    state_key = _HEROINE_INTERNAL_KEYS.get(heroine_key)
    if state_key:
        return player.get(state_key, "unmet")
    return "unmet"


def apply_heroine_permanent_passive(ally):
    """Apply the permanent unlock passive to a heroine ally.
    
    Called after promote_heroine_to_permanent() to grant the special passive.
    """
    perm_passive_id = ally.get("_heroine_permanent_passive")
    if not perm_passive_id:
        return

    passive_def = get_heroine_passive_def(perm_passive_id)
    if not passive_def:
        return

    # Store the passive definition on the ally for combat checks
    ally["_heroine_perm_passive_def"] = passive_def


def trigger_heroine_permanent_unlock(player, heroine_key, boss_flag=None):
    """Standard handler for superboss defeat → heroine permanent unlock.
    
    Call this from superboss on_kill hooks to promote the associated heroine.
    
    Args:
        player: player dict
        heroine_key: "alice", "red_hood", or "dorothy"
        boss_flag: player flag to set (e.g., "wl_boss_defeated_jabberwock")
    
    Returns:
        ally dict if heroine was found and promoted, None otherwise
    """
    ally = get_heroine_in_party(player, heroine_key)
    if not ally:
        return None

    join_level = ally.get("level", player.get("level", 1))
    promote_heroine_to_permanent(player, ally, join_level)
    set_heroine_state(player, heroine_key, "permanent")

    if boss_flag:
        player[boss_flag] = True

    return ally
