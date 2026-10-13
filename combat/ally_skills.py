from combat.combat_io import c_print, c_input
# combat/ally_skills.py - Ally skill system: passive, innate, and learnable skills
import os
import random
import yaml

from combat.helpers import format_damage_msg, ACTION_CANCELLED_MSG
from utils import display_name

# Maximum number of learnable skills an ally can have at once
MAX_LEARNED_SKILLS = 3

# Heroine "upgrade skills" — permanent rewards from facility weapon upgrades
# (docs call these "Upgrade skills"): Frabjous Day (Alice), Through the Forest
# (Red Hood), Emerald City's Light (Dorothy). They are their own skill
# category — they must NOT occupy one of the MAX_LEARNED_SKILLS slots and must
# never be teachable or replaceable at the Barracks.
HEROINE_UPGRADE_SKILLS = {
    "alice": "frabjous_day",
    "red_hood": "through_the_forest",
    "dorothy": "emerald_citys_light",
}
UPGRADE_SKILL_IDS = frozenset(HEROINE_UPGRADE_SKILLS.values())


def is_upgrade_skill(skill_id):
    """True for heroine facility-upgrade skills (own category — not learnable)."""
    return skill_id in UPGRADE_SKILL_IDS


def _load_innate_and_learnable():
    """Load innate and learnable skill definitions from YAML."""
    innate_path = os.path.join(os.path.dirname(__file__), "../resources/skill_book/innate_skills.yaml")
    learnable_path = os.path.join(os.path.dirname(__file__), "../resources/skill_book/skill_list.yaml")
    
    with open(innate_path, "r", encoding="utf-8") as f:
        innate_data = yaml.safe_load(f)
    with open(learnable_path, "r", encoding="utf-8") as f:
        learnable_data = yaml.safe_load(f)
    
    return innate_data, learnable_data


_INNATE_DATA, _LEARNABLE_DATA = _load_innate_and_learnable()

# Module-level accessors
INNATE_SKILLS_MAP = _INNATE_DATA.get("innate_skills", {})
INNATE_SKILL_DEFS = _INNATE_DATA.get("innate_skill_defs", {})
AWAKENINGS = _INNATE_DATA.get("awakenings", {})
RACE_PASSIVES = _LEARNABLE_DATA.get("race_passives", {})
LEARNABLE_SKILLS = _LEARNABLE_DATA.get("learnable_skills", {})
HEROINE_PASSIVES = _LEARNABLE_DATA.get("heroine_passives", {})

# Mastery-scaled revive percentages (override YAML revive_percent when present).
# Anchors per design: m1 / m3 / m5 values, plateau between, m0 = m1 value.
# Raise Dead (innate) keeps the highest ceiling so the Lich Queen stays the
# premium reviver versus the learnable Phoenix Call.
REVIVE_MASTERY_PCT = {
    "phoenix_call":    [0.20, 0.20, 0.20, 0.25, 0.25, 0.35],
    "radiant_rebirth": [0.45, 0.45, 0.45, 0.50, 0.50, 0.70],
    "raise_dead":      [0.30, 0.30, 0.30, 0.35, 0.35, 0.50],
}


def initialize_ally_skills(ally, enemy_key, race):
    """Initialize skill system for a newly created ally.
    
    Sets up:
    - passive_skill (race-based)
    - innate_skills (2 unique skills per monster girl)
    - learned_skills (starts empty)
    - upgrade_skills (starts empty — heroine facility rewards)
    - learning (starts None)
    - skill_cooldowns (starts empty)
    - skill_mastery (starts empty)
    """
    # Set race-based passive
    if race and race in RACE_PASSIVES:
        ally["passive_skill"] = RACE_PASSIVES[race].get("id", None)
    else:
        ally["passive_skill"] = None
    
    # Store race for UI lookups
    ally["race"] = race
    
    # Set innate skills (2 skills unique to this monster girl). Awakened girls
    # use their upgraded kit instead (docs/awakening_design.md Part C).
    mapping = AWAKENINGS.get(enemy_key)
    if ally.get("awakened") and mapping:
        stored = [sid for sid in ally.get("awakened_skills", []) if sid in mapping.values()]
        ally["innate_skills"] = stored if len(stored) == len(mapping) else list(mapping.values())
        ally["awakened_skills"] = list(ally["innate_skills"])
    elif enemy_key in INNATE_SKILLS_MAP:
        ally["innate_skills"] = list(INNATE_SKILLS_MAP[enemy_key])
    else:
        ally["innate_skills"] = []
    
    # Initialize learnable skill system
    ally["learned_skills"] = ally.get("learned_skills", [])
    ally["upgrade_skills"] = ally.get("upgrade_skills", [])
    ally["learning"] = ally.get("learning", None)
    ally["skill_cooldowns"] = ally.get("skill_cooldowns", {})
    ally["skill_mastery"] = ally.get("skill_mastery", {})


def has_awakening(enemy_key):
    """True if a monster girl has an Awakened kit defined."""
    return enemy_key in AWAKENINGS


def get_awakened_skill_ids(enemy_key):
    """Return a girl's awakened skill ids (empty list when she has none)."""
    mapping = AWAKENINGS.get(enemy_key)
    return list(mapping.values()) if mapping else []


def apply_awakening_skills(record, enemy_key):
    """Swap an awakened girl's innate kit to her upgraded skills (idempotent).

    Transfers mastery + cooldown progress from each base skill to its awakened
    counterpart first — investment should not be punished by the upgrade —
    then records the awakened ids. Works for active allies and house girl
    records alike (house records may not carry an innate_skills list).
    """
    mapping = AWAKENINGS.get(enemy_key)
    if not mapping:
        return False

    awakened_ids = list(mapping.values())

    # 1) Carry over mastery + cooldown progress
    mastery = record.setdefault("skill_mastery", {})
    cooldowns = record.setdefault("skill_cooldowns", {})
    for base_id, upgraded_id in mapping.items():
        if base_id in mastery:
            base_exp = mastery.pop(base_id)
            if base_exp > mastery.get(upgraded_id, 0):
                mastery[upgraded_id] = base_exp
        if base_id in cooldowns:
            base_cd = cooldowns.pop(base_id)
            if base_cd > cooldowns.get(upgraded_id, 0):
                cooldowns[upgraded_id] = base_cd

    # 2) Record the upgraded ids (persisted with the girl)
    record["awakened_skills"] = list(awakened_ids)

    # 3) Swap an active innate kit in place; rebuild it otherwise
    current = record.get("innate_skills") or []
    if current:
        swapped = [mapping.get(sid, sid) for sid in current]
        for upgraded_id in awakened_ids:
            if upgraded_id not in swapped:
                swapped.append(upgraded_id)
        record["innate_skills"] = swapped
    else:
        record["innate_skills"] = list(awakened_ids)
    return True


def get_race_passive(race):
    """Return the passive skill definition for a race."""
    if race in RACE_PASSIVES:
        return RACE_PASSIVES[race]
    return None


def get_race_passive_effects(race):
    """Return a race passive's effect blocks as a flat list.

    Supports the `type: multi` wrapper so races can combine several effects
    (stats + elemental + utility). See docs/awakening_design.md Part B.
    """
    passive = get_race_passive(race)
    if not passive:
        return []
    effect = passive.get("effect", {})
    if not effect:
        return []
    if effect.get("type") == "multi":
        return [e for e in effect.get("effects", []) if isinstance(e, dict)]
    return [effect]


def get_race_lifesteal(entity):
    """Total race-passive lifesteal fraction for an entity (0.0 if none)."""
    total = 0.0
    for effect in get_race_passive_effects(entity.get("race")):
        if effect.get("type") == "life_steal":
            total += effect.get("value", 0)
    return total


def get_race_damage_reduction(entity):
    """Total race-passive damage reduction fraction (0.0 if none)."""
    total = 0.0
    for effect in get_race_passive_effects(entity.get("race")):
        if effect.get("type") == "damage_reduction":
            total += effect.get("value", 0)
    return min(total, 0.9)


def get_race_regen(entity):
    """Total race-passive end-of-round regen fraction (0.0 if none)."""
    total = 0.0
    for effect in get_race_passive_effects(entity.get("race")):
        if effect.get("type") == "regen":
            total += effect.get("value", 0)
    return total


def get_race_evasion(entity):
    """Total race-passive evasion bonus (0.0 if none)."""
    total = 0.0
    for effect in get_race_passive_effects(entity.get("race")):
        if effect.get("type") == "evasion":
            total += effect.get("value", 0)
    return total


def _target_race(target):
    """Resolve a combat target's race (runtime field or enemy template)."""
    race = target.get("race")
    if race:
        return race
    key = target.get("key")
    if key:
        from resources.enemies import ENEMIES
        return ENEMIES.get(key, {}).get("race")
    return None


def _is_shocked(target):
    if target.get("shocked"):
        return True
    return any(d.get("type") == "shock" for d in target.get("active_debuffs", []))


def get_race_damage_multiplier(attacker, target):
    """Race-passive outgoing damage multiplier.

    Angel: +5% vs Demons. Clockwork: +10% vs shocked targets.
    """
    mult = 1.0
    for effect in get_race_passive_effects(attacker.get("race")):
        etype = effect.get("type")
        if etype == "damage_bonus_vs_race":
            if _target_race(target) in effect.get("races", []):
                mult += effect.get("value", 0)
        elif etype == "damage_bonus_vs_status":
            if _is_shocked(target):
                mult += effect.get("value", 0)
    return mult


def has_status_immunity(entity, status):
    """True if a race passive grants immunity to the given status (allies only)."""
    if not entity.get("is_ally"):
        return False
    for effect in get_race_passive_effects(entity.get("race")):
        if effect.get("type") == "status_immunity" and status in effect.get("statuses", []):
            return True
    return False


def is_heal_blocked(target, source):
    """True if the target's race passive blocks external healing.

    Undead: allied heals blocked, self-heals allowed. `source` is the healer
    entity; a None source means unknown origin and is allowed.
    """
    if source is None or source is target:
        return False
    if not target.get("is_ally"):
        return False
    for effect in get_race_passive_effects(target.get("race")):
        if effect.get("type") == "heal_block":
            return True
    return False


def maybe_stun_on_basic(attacker, target):
    """Orc race passive: chance to stun on a basic attack.

    Returns a message string when the stun lands, else None.
    """
    if target.get("hp", 0) <= 0:
        return None
    chance = 0.0
    for effect in get_race_passive_effects(attacker.get("race")):
        if effect.get("type") == "stun_on_basic":
            chance += effect.get("chance", 0.1)
    if chance <= 0 or random.random() >= chance:
        return None
    from combat.status_effects import check_status_resisted
    if check_status_resisted(target):
        return f"{target['name']} shrugs off the stun!"
    target["stunned"] = True
    target.setdefault("active_debuffs", []).append({"type": "stun", "remaining": 1})
    return f"{target['name']} is stunned! (Orc ferocity)"


def get_innate_skill_def(skill_id):
    """Return the skill definition for an innate skill."""
    return INNATE_SKILL_DEFS.get(skill_id, None)


def get_learnable_skill_def(skill_id):
    """Return the skill definition for a learnable skill.

    Falls back to innate skill definitions so legacy saves / stray records
    that still hold a heroine upgrade skill (Frabjous Day, Through the
    Forest, Emerald City's Light) can resolve its definition even though it
    is defined in innate_skills.yaml. Upgrade skills normally live in their
    own ``upgrade_skills`` category.
    """
    for category in LEARNABLE_SKILLS.values():
        if skill_id in category:
            return category[skill_id]
    # Fallback: check innate skill defs (covers vorpal upgrade skills)
    return INNATE_SKILL_DEFS.get(skill_id, None)


def get_all_available_skills(ally):
    """Return a list of all skills the ally can use (passive, innate, upgrade, learned)."""
    skills = {
        "passive": get_race_passive(ally.get("race")),
        "innate": [get_innate_skill_def(sid) for sid in ally.get("innate_skills", [])],
        "upgrade": [get_innate_skill_def(sid) for sid in ally.get("upgrade_skills", [])],
        "learned": [get_learnable_skill_def(sid) for sid in ally.get("learned_skills", [])]
    }
    return skills


def get_usable_skills_in_combat(ally):
    """Return list of skills the ally can actually use in combat (innate + upgrade + learned, not on cooldown)."""
    cooldowns = ally.get("skill_cooldowns", {})
    usable = []
    
    # Innate skills
    for skill_id in ally.get("innate_skills", []):
        if cooldowns.get(skill_id, 0) <= 0:
            skill_def = get_innate_skill_def(skill_id)
            if skill_def:
                usable.append((skill_id, skill_def))
    
    # Upgrade skills (heroine facility rewards — own category)
    for skill_id in ally.get("upgrade_skills", []):
        if cooldowns.get(skill_id, 0) <= 0:
            skill_def = get_innate_skill_def(skill_id)
            if skill_def:
                usable.append((skill_id, skill_def))
    
    # Learned skills
    for skill_id in ally.get("learned_skills", []):
        if cooldowns.get(skill_id, 0) <= 0:
            skill_def = get_learnable_skill_def(skill_id)
            if skill_def:
                usable.append((skill_id, skill_def))
    
    return usable


def meets_skill_requirements(ally, skill_def):
    """Return True if an ally meets a learnable skill's level and level-cap gates.

    Level gate: the ally's current level must be high enough.
    Cap gate: higher tiers may require a raised level_cap (ascension), so
    high-level captures can't skip the progression gates entirely.
    """
    if ally.get("level", 1) < skill_def.get("required_level", 1):
        return False
    required_cap = skill_def.get("required_cap", 0)
    if required_cap and ally.get("level_cap", 10) < required_cap:
        return False
    return True


def teach_ally_skill(ally, skill_id):
    """Start teaching an ally a new learnable skill.
    
    Can only learn one skill at a time. Replaces any current learning.
    Does NOT enforce the MAX_LEARNED_SKILLS cap — callers should check
    beforehand and use replace_ally_learned_skill() if at the cap.
    """
    # Upgrade skills are permanent facility rewards — never teachable
    if is_upgrade_skill(skill_id):
        return False

    skill_def = get_learnable_skill_def(skill_id)
    if not skill_def:
        return False
    
    # Can't re-learn already learned skills
    if skill_id in ally.get("learned_skills", []):
        return False
    
    # Check level + level-cap (ascension) requirements
    if not meets_skill_requirements(ally, skill_def):
        return False
    
    # Start learning this skill
    exp_needed = skill_def.get("exp_cost", 300)
    ally["learning"] = {
        "skill_id": skill_id,
        "exp": 0,
        "exp_needed": exp_needed
    }
    return True


def replace_ally_learned_skill(ally, old_skill_id, new_skill_id):
    """Replace an existing learned skill with a new skill to learn.
    
    Removes old_skill_id from learned_skills and skill_mastery, then
    starts learning new_skill_id. Returns True on success, False on failure.
    """
    learned = ally.get("learned_skills", [])
    if old_skill_id not in learned:
        return False

    # Facility upgrade skills are permanent — never replaceable
    if is_upgrade_skill(old_skill_id):
        return False
    
    # Remove old skill
    learned.remove(old_skill_id)
    ally.setdefault("skill_mastery", {}).pop(old_skill_id, None)
    
    # Start learning new skill
    return teach_ally_skill(ally, new_skill_id)


def gain_skill_learning_exp(ally, amount):
    """Add experience to the skill currently being learned."""
    if not ally.get("learning"):
        return None  # Not learning anything
    
    learning_info = ally["learning"]
    learning_info["exp"] += amount
    
    # Check if skill is learned
    if learning_info["exp"] >= learning_info["exp_needed"]:
        skill_id = learning_info["skill_id"]
        learned = ally.setdefault("learned_skills", [])
        
        # Safety cap: if already at max learned skills, replace the oldest one
        if len(learned) >= MAX_LEARNED_SKILLS:
            # Discard the oldest learned skill to make room
            oldest = learned.pop(0)
            ally.setdefault("skill_mastery", {}).pop(oldest, None)
        
        # Move to learned skills
        learned.append(skill_id)
        # Initialize mastery
        ally.setdefault("skill_mastery", {})[skill_id] = 0
        # Clear learning
        ally["learning"] = None
        return skill_id  # Return the newly learned skill_id
    
    return None


def get_ally_skill_mastery_level(ally, skill_id):
    """Return mastery level (0-5) for a skill based on uses."""
    from combat.skills import MASTERY_THRESHOLDS
    mastery_exp = ally.get("skill_mastery", {}).get(skill_id, 0)
    level = 0
    for threshold in MASTERY_THRESHOLDS:
        if mastery_exp >= threshold:
            level += 1
    return level


def add_ally_skill_mastery_xp(ally, skill_id):
    """Increment mastery exp for a skill after use."""
    ally.setdefault("skill_mastery", {})
    old_level = get_ally_skill_mastery_level(ally, skill_id)
    ally["skill_mastery"][skill_id] = ally["skill_mastery"].get(skill_id, 0) + 1
    new_level = get_ally_skill_mastery_level(ally, skill_id)
    
    if new_level > old_level:
        return True  # Mastery level increased
    return False


def get_learnable_skill_categories():
    """Return list of available learnable skill categories (offensive, defensive, support)."""
    return list(LEARNABLE_SKILLS.keys())


def get_learnable_skills_by_category(category):
    """Return dict of learnable skills in a category."""
    return LEARNABLE_SKILLS.get(category, {})


def get_all_learnable_skills():
    """Return all learnable skills as a flat dict."""
    all_skills = {}
    for category_skills in LEARNABLE_SKILLS.values():
        all_skills.update(category_skills)
    return all_skills


def get_passive_by_id(passive_id):
    """Look up a race passive definition by its ID string (for legacy save compatibility)."""
    for data in RACE_PASSIVES.values():
        if data.get("id") == passive_id:
            return data
    return None


def format_skill_learning_progress(ally):
    """Return a formatted string showing current learning progress."""
    if not ally.get("learning"):
        return "Not learning any skill"
    
    learning = ally["learning"]
    skill_id = learning["skill_id"]
    exp = learning["exp"]
    exp_needed = learning["exp_needed"]
    skill_def = get_learnable_skill_def(skill_id)
    skill_name = skill_def.get("name", skill_id) if skill_def else skill_id
    
    progress = (exp / exp_needed) * 100
    bar_len = 20
    filled = int((progress / 100) * bar_len)
    bar = "[" + "=" * filled + "-" * (bar_len - filled) + "]"
    
    return f"{skill_name}: {bar} {exp}/{exp_needed} ({progress:.1f}%)"


# ── Combat Skill Execution ──────────────────────────────────────────────────

def get_all_ally_skills(ally):
    """Return all innate + upgrade + learned skills with definitions (including those on cooldown)."""
    skills = []
    for sid in ally.get("innate_skills", []):
        sdef = get_innate_skill_def(sid)
        if sdef:
            skills.append((sid, sdef))
    for sid in ally.get("upgrade_skills", []):
        sdef = get_innate_skill_def(sid)
        if sdef:
            skills.append((sid, sdef))
    for sid in ally.get("learned_skills", []):
        sdef = get_learnable_skill_def(sid)
        if sdef:
            skills.append((sid, sdef))
    return skills

def format_ally_mastery_label(skill_id, ally):
    """Return a mastery label string for display.

    Display: ★ / ★★ / ★★★ for levels 1-3, then ✦ (4) and ✦✦ (5).
    """
    level = get_ally_skill_mastery_level(ally, skill_id)
    labels = ["", "★", "★★", "★★★", "✦", "✦✦"]
    return labels[level]


# Map debuff types to their corresponding flat entity flags that must also be cleared
_FLAT_DEBUFF_FLAGS = {
    "curse":      "cursed",
    "blind":      "blinded",
    "slow":       "slowed",
    "confusion":  "confused",
    "stun":       "stunned",
    "silence":    "silenced",
    "dread":      "dreaded",
    "fear":       "feared",
    "freeze":     "frozen",
    "sleep":      "asleep",
    "paralyze":   "paralyzed",
    "entomb":     "entombed",
    "void_touched": "void_touched",
}


def _clear_flat_debuff_flag(entity, debuff_type):
    """If the given debuff type has a corresponding flat flag on the entity, clear it."""
    flag = _FLAT_DEBUFF_FLAGS.get(debuff_type)
    if flag and entity.get(flag):
        entity[flag] = False


def _scale_effect_value(effect, caster_level):
    """Return an effect's value, optionally scaled with the caster's level.

    Skills opt in by adding `scale_per_level` to their effect dict — the
    caster's level (minus 1) times that fraction is added, rounded down.
    Example: value 2 with scale_per_level 0.15 → +2 at Lv1, +4 at Lv15,
    +7 at Lv40. Effects without the key keep their flat value.
    """
    base = effect.get("value", 0)
    per_level = effect.get("scale_per_level", 0)
    if per_level and caster_level > 1:
        base += int((caster_level - 1) * per_level)
    return base


def execute_ally_skill(ally, player, skill_id, skill_def, enemies, allies):
    """
    Execute an ally's innate or learned skill in combat.

    Returns: (result_message, victory)
    victory is True if all enemies were defeated.
    """
    import random
    from combat.ally import compute_ally_stats
    from combat.skills import get_mastery_bonuses
    from combat.status_effects import apply_poison, apply_burn, apply_shock, apply_barrier, apply_sleep, apply_haste, apply_paralyze, apply_entomb, apply_void_touched, apply_bleed, absorb_damage, wake_on_damage, apply_healing, apply_death_ward
    from character import player_max_hp

    # ── Palette heroine: custom kit (degraded boss moves) ──
    from combat.palette_ally import is_palette_ally
    if is_palette_ally(ally):
        if skill_id == "palette_signature":
            from combat.palette_ally import start_palette_signature
            from pandemonium_curses import get_cooldown_increase
            ally.setdefault("skill_cooldowns", {})[skill_id] = skill_def.get("cooldown", 4) + get_cooldown_increase(player)
            add_ally_skill_mastery_xp(ally, skill_id)
            return start_palette_signature(ally), False
        if skill_id == "palette_spectrum":
            from combat.palette_ally import palette_spectrum_attack
            from pandemonium_curses import get_cooldown_increase
            ally.setdefault("skill_cooldowns", {})[skill_id] = skill_def.get("cooldown", 3) + get_cooldown_increase(player)
            add_ally_skill_mastery_xp(ally, skill_id)
            return palette_spectrum_attack(ally, player, enemies)

    a_str, a_con, a_dex, a_ler, a_wis, a_cha = compute_ally_stats(ally)

    stat_map = {
        "str": a_str, "con": a_con, "dex": a_dex,
        "ler": a_ler, "wis": a_wis, "cha": a_cha,
        "Strength": a_str, "Constitution": a_con, "Dexterity": a_dex,
        "Learning": a_ler, "Wisdom": a_wis, "Charisma": a_cha,
    }

    target_type = skill_def.get("target", "enemy")
    power_type = skill_def.get("power_type", "str")
    base_power = skill_def.get("base_power", 0)

    mastery = get_ally_skill_mastery_level(ally, skill_id)
    bonuses = get_mastery_bonuses(skill_id, mastery)
    power_mult = bonuses["power_mult"]
    cd_reduction = bonuses["cooldown_reduction"]
    extra_effect = bonuses["extra_effect"]
    duration_bonus = bonuses["duration_bonus"]
    status_mult = bonuses["status_mult"]

    def _scaled_mag(val):
        """Scale a support magnitude by the mastery status multiplier (ints round half-up)."""
        if isinstance(val, int):
            return int(val * status_mult + 0.5) if val >= 0 else int(val * status_mult - 0.5)
        return val * status_mult

    # Burn skills upgrade their burn TIER instead of multiplying damage:
    # +1 tier at ★3, +1 more at ✦✦ (capped at tier 5 / Conflagration).
    burn_tier_bonus = (1 if mastery >= 3 else 0) + (1 if mastery >= 5 else 0)

    scaling = stat_map.get(power_type, 0)
    scaling += a_ler // 2

    msg_parts = []
    victory = False
    # Snapshot enemy HP so Sky Piercer can detect which enemies this skill damaged
    pre_hp = [e["hp"] for e in enemies]

    # ── Target Selection Helpers ──
    def _pick_enemy_target():
        live = [e for e in enemies if e["hp"] > 0]
        if not live:
            return None
        if len(live) == 1:
            return live[0]
        c_print(f"  Select target for {skill_def['name']}:")
        for i, e in enumerate(live):
            c_print(f"    {i+1}. {e['name']} (HP: {e['hp']}/{e['max_hp']})")
        try:
            choice = int(c_input("  Select target number: ")) - 1
            if 0 <= choice < len(live):
                return live[choice]
        except ValueError:
            pass
        return None

    def _pick_party_target(allow_dead=False, dead_only=False):
        party = [player] + allies
        if dead_only:
            party = [m for m in party if m.get("current_hp", 0) <= 0]
        elif not allow_dead:
            party = [m for m in party if m.get("current_hp", 0) > 0]
        if not party:
            return None
        if len(party) == 1:
            return party[0]
        c_print("  Select target:")
        for i, m in enumerate(party):
            name = m.get("name", "You") if m is player else m.get("name", "Ally")
            hp = m.get("current_hp", 0)
            max_hp = player_max_hp(m) if m is player else m.get("max_hp", 1)
            status = " [FALLEN]" if m.get("current_hp", 1) <= 0 else ""
            c_print(f"    {i+1}. {name} ({hp}/{max_hp}){status}")
        try:
            choice = int(c_input("  Choice: ")) - 1
            if 0 <= choice < len(party):
                return party[choice]
        except ValueError:
            pass
        return None

    # Chance and Choice: one coin roll per action (all hits share it)
    _cac_state = {"rolled": False, "mult": 1.0}

    def _calc_dmg(target, power, ignore_armor=False, guaranteed_crit=False):
        from combat.stats import roll_skill_dodge, roll_accuracy_penalty
        if roll_skill_dodge(target):
            msg_parts.append(f"  💨 {target['name']} reads the strike and slips aside!")
            return 0
        if roll_accuracy_penalty(target):
            msg_parts.append(f"  💨 {target['name']} deflects {display_name(ally)}'s attack!")
            return 0
        armor = 0 if ignore_armor else target.get("con_mod", 0)
        for debuff in target.get("active_debuffs", []):
            if debuff.get("type") == "sunder":
                armor = max(0, armor - debuff.get("value", 0))
            elif debuff.get("type") == "curse" and "Constitution" in debuff.get("stats", []):
                armor = max(0, armor - debuff.get("penalty", 0))
        # Ignore armor % (e.g. Fell the Wolf)
        ignore_armor_pct = skill_def.get("ignore_armor_pct", 0)
        if ignore_armor_pct > 0:
            armor = int(armor * (1 - ignore_armor_pct))
        # Hunter's Mark: increased damage taken
        if target.get("hunters_mark"):
            mark_bonus = target.get("hunters_mark_bonus", 0.15)
            power = int(power * (1 + mark_bonus))
            msg_parts.append(f"Hunter's Mark! +{int(mark_bonus * 100)}% damage!")
        # Awakened rider bonuses (Perfect Ambush / Eclipse Lash)
        bonus_high = skill_def.get("bonus_vs_high_hp")
        if bonus_high and target.get("max_hp") and target["hp"] / target["max_hp"] > 0.8:
            power = int(power * (1 + bonus_high))
            msg_parts.append(f"Ambush! +{int(bonus_high * 100)}% vs an untouched foe!")
        bonus_bleed = skill_def.get("bonus_vs_bleeding")
        if bonus_bleed:
            from combat.status_effects import is_bleeding
            if is_bleeding(target):
                power = int(power * (1 + bonus_bleed))
                msg_parts.append(f"The dark edge bites deep! +{int(bonus_bleed * 100)}% vs bleeding!")
        # Prescript Ledger — clash empowerment vs the Prescript's Target
        from combat.weapon.prescript_ledger import get_clash_bonus as get_prescript_clash_bonus
        prescript_clash = get_prescript_clash_bonus(ally, target)
        if prescript_clash:
            power = int(power * (1 + prescript_clash))
        # Damage-taken amplification (e.g. Aura of Despair)
        from combat.status_effects import get_damage_taken_multiplier
        dt_mult = get_damage_taken_multiplier(target)
        if dt_mult != 1.0:
            power = int(power * dt_mult)
        # Apply damage_boost buffs (multi-turn, non-consuming)
        for buff in ally.get("active_buffs", []):
            if buff.get("type") == "damage_boost":
                power = int(power * (1 + buff.get("value", 0)))
        # Bonus vs specific races (e.g. Snicker-Snack vs Dragonkin/Storybook)
        bonus_vs = skill_def.get("bonus_vs_races", [])
        if bonus_vs and target.get("race") in bonus_vs:
            bonus_val = skill_def.get("bonus_value", 0.30)
            power = int(power * (1 + bonus_val))
            msg_parts.append(f"Bonus vs {target['race']}! +{int(bonus_val * 100)}% damage!")
        # Random critical hit (skip if skill already guarantees a crit)
        did_crit = False
        if not guaranteed_crit:
            from combat.stats import roll_critical_hit, apply_critical_damage, CRIT_MULTIPLIER
            crit_bonus = skill_def.get("crit_bonus", 0)
            crit_mult = skill_def.get("crit_mult", CRIT_MULTIPLIER)
            is_crit, _, overflow_crit = roll_critical_hit(
                ally, "ally", dex=a_dex, lrn=a_ler, bonus=crit_bonus
            )
            if is_crit:
                power = apply_critical_damage(power, True, multiplier=crit_mult + overflow_crit)
                msg_parts.append("Critical hit!")
                did_crit = True
        else:
            did_crit = True
        # Apply Strength milestone bonus
        from combat.stat_milestones import get_strength_bonus
        dmg = max(1, power + get_strength_bonus(ally) - armor)
        # Apply elemental damage if skill has an elemental profile
        element = skill_def.get("elemental")
        if skill_def.get("palette_dynamic_element"):
            from combat.palette_ally import get_palette_ally_color_element
            element = get_palette_ally_color_element(ally)
        if element:
            from combat.elemental import calculate_elemental_damage
            dmg = calculate_elemental_damage(dmg, ally, target, element)
        # Race passive damage bonuses (Angel vs Demons, Clockwork vs shocked)
        dmg = int(dmg * get_race_damage_multiplier(ally, target))
        # Pandemonium: Weakened Resolve curse — allies deal less damage too
        from pandemonium_curses import apply_damage_dealt_multiplier
        dmg = apply_damage_dealt_multiplier(player, dmg)
        # Event Horizon trophies: Old Dopo Robe + Chance and Choice
        from combat.weapon.dopo_robe import get_robe_multiplier
        dmg = int(dmg * get_robe_multiplier(ally, player))
        from combat.weapon.chance_and_choice import apply_chance_and_choice
        dmg = apply_chance_and_choice(ally, dmg, _cac_state)
        return dmg, did_crit

    # ── Determine Target ──
    target = None
    if target_type == "enemy":
        target = _pick_enemy_target()
        if not target:
            return ACTION_CANCELLED_MSG, False
    elif target_type == "self":
        target = ally
    elif target_type in ("ally_or_self", "dead_ally"):
        target = _pick_party_target(dead_only=(target_type == "dead_ally"))
        if not target:
            return ACTION_CANCELLED_MSG, False
    elif target_type in ("enemies", "all_allies"):
        target = None
    else:
        target = _pick_enemy_target()
        if not target:
            return ACTION_CANCELLED_MSG, False

    # ── Effect-based Skills (non-damage) ──
    effect = skill_def.get("effect")
    if effect:
        effect_type = effect.get("type")
        duration = effect.get("duration", 3) + duration_bonus
        value = effect.get("value", 0)

        if effect_type == "damage_reduction":
            pct_val = value if isinstance(value, float) and value <= 1 else value / 100.0
            pct_val = pct_val * status_mult
            recipients = [target] if target else [ally]
            if target_type == "all_allies":
                recipients = [player] + allies
            for r in recipients:
                r.setdefault("active_buffs", []).append({
                    "type": "defense_pct", "value": pct_val, "remaining": duration
                })
            pct_display = int(pct_val * 100)
            msg_parts.append(f"{display_name(ally)} takes {pct_display}% less damage for {duration} turns!")

        elif effect_type == "evasion":
            recipients = [target] if target else [ally]
            ev_value = _scaled_mag(value)
            dex_bonus = _scaled_mag(effect.get("dex_bonus", 0))
            for r in recipients:
                r.setdefault("active_buffs", []).append({
                    "type": "evasion", "value": ev_value, "remaining": duration
                })
                if dex_bonus:
                    r.setdefault("active_buffs", []).append({
                        "stat": "Dexterity", "value": dex_bonus, "remaining": duration
                    })
            if dex_bonus:
                msg_parts.append(f"{display_name(ally)} gains evasion and +{dex_bonus} Dexterity for {duration} turns!")
            else:
                msg_parts.append(f"{display_name(ally)} gains evasion for {duration} turns!")

        elif effect_type == "power_buff":
            recipients = [target] if target else [ally]
            for r in recipients:
                r.setdefault("active_buffs", []).append({
                    "type": "power_buff", "value": _scaled_mag(value), "remaining": duration
                })
            msg_parts.append(f"{r.get('name', 'ally')}'s next action is empowered!")

        elif effect_type == "slow":
            from combat.status_effects import apply_slow_to_enemy
            if target_type == "enemy" and target:
                apply_slow_to_enemy(target, duration=duration)
                msg_parts.append(f"{target['name']} is slowed!")
            else:
                live = [e for e in enemies if e["hp"] > 0]
                for e in live:
                    apply_slow_to_enemy(e, duration=duration)
                msg_parts.append(f"{display_name(ally)} slows all enemies!")

        elif effect_type == "blind":
            from combat.status_effects import check_status_resisted
            if target_type == "enemy" and target:
                if check_status_resisted(target):
                    msg_parts.append(f"{target['name']} shrugs off the blinding light!")
                else:
                    target["blinded"] = True
                    target.setdefault("active_debuffs", []).append({
                        "type": "blind", "remaining": duration
                    })
                    msg_parts.append(f"{target['name']} is blinded!")
            else:
                for e in [e for e in enemies if e["hp"] > 0]:
                    if check_status_resisted(e):
                        continue
                    e["blinded"] = True
                    e.setdefault("active_debuffs", []).append({
                        "type": "blind", "remaining": duration
                    })
                msg_parts.append(f"{display_name(ally)} blinds the enemies!")

        elif effect_type == "stun":
            from combat.status_effects import check_status_resisted
            if target_type == "enemy" and target:
                if check_status_resisted(target):
                    msg_parts.append(f"{target['name']} shrugs off the stun!")
                else:
                    target["stunned"] = True
                    target.setdefault("active_debuffs", []).append({
                        "type": "stun", "remaining": duration
                    })
                    msg_parts.append(f"{target['name']} is stunned!")
            else:
                live = [e for e in enemies if e["hp"] > 0]
                for e in live:
                    if check_status_resisted(e):
                        continue
                    e["stunned"] = True
                    e.setdefault("active_debuffs", []).append({
                        "type": "stun", "remaining": duration
                    })
                msg_parts.append(f"{display_name(ally)} stuns all enemies!")

        elif effect_type == "stat_debuff":
            from combat.status_effects import check_status_resisted
            stat = effect.get("stat", "Strength")
            debuff_value = _scaled_mag(_scale_effect_value(effect, ally.get("level", 1)))
            if target_type == "enemy" and target:
                if check_status_resisted(target):
                    msg_parts.append(f"{target['name']} shrugs off the weakening hex!")
                else:
                    target.setdefault("active_debuffs", []).append({
                        "type": "curse", "penalty": debuff_value,
                        "remaining": duration, "stats": [stat]
                    })
                    msg_parts.append(f"{target['name']}'s {stat} is reduced by {debuff_value}!")
            else:
                live = [e for e in enemies if e["hp"] > 0]
                for e in live:
                    if check_status_resisted(e):
                        continue
                    e.setdefault("active_debuffs", []).append({
                        "type": "curse", "penalty": debuff_value,
                        "remaining": duration, "stats": [stat]
                    })
                msg_parts.append(f"{display_name(ally)} reduces all enemies' {stat} by {debuff_value}!")

        elif effect_type == "regen":
            recipients = [target] if target else [ally]
            if target_type == "all_allies":
                recipients = [player] + allies
            for r in recipients:
                if isinstance(value, float) and value < 1:
                    # Percent-of-max-HP regen — the player has no stored
                    # max_hp key, so use the canonical HP function for them.
                    r_max_hp = player_max_hp(r) if r is player else r.get("max_hp", 100)
                    regen_val = int(r_max_hp * value)
                else:
                    regen_val = _scaled_mag(value)
                r.setdefault("active_buffs", []).append({
                    "type": "hot", "value": regen_val, "remaining": duration
                })
            msg_parts.append(f"{display_name(ally)} grants regeneration for {duration} turns!")

        elif effect_type == "stat_buff":
            stat = effect.get("stat", "Strength")
            buff_value = _scaled_mag(_scale_effect_value(effect, ally.get("level", 1)))
            recipients = [target] if target else [ally]
            if target_type == "all_allies":
                recipients = [player] + allies
            for r in recipients:
                r.setdefault("active_buffs", []).append({
                    "stat": stat, "value": buff_value, "remaining": duration
                })
            msg_parts.append(f"{display_name(ally)} raises {stat} by {buff_value} for {duration} turns!")

        elif effect_type == "cooldown_reduction":
            recipients = [target] if target else [ally]
            cd_val = _scaled_mag(value)
            for r in recipients:
                r.setdefault("active_buffs", []).append({
                    "type": "cooldown_reduction", "value": cd_val, "remaining": duration
                })
            target_name = display_name(target) if target else display_name(ally)
            msg_parts.append(f"{target_name}'s next skill cooldown reduced by {cd_val}!")

        elif effect_type == "reflection":
            recipients = [target] if target else [ally]
            for r in recipients:
                r.setdefault("active_buffs", []).append({
                    "type": "reflection", "value": _scaled_mag(value), "remaining": duration
                })
            msg_parts.append(f"{display_name(ally)} will reflect damage!")

        elif effect_type == "damage_absorption":
            recipients = [target] if target else [ally]
            if target_type == "all_allies":
                recipients = [player] + allies
            absorb_val = value if isinstance(value, float) and value <= 1 else value / 100.0
            absorb_val = absorb_val * status_mult
            for r in recipients:
                r.setdefault("active_buffs", []).append({
                    "type": "damage_absorption", "value": absorb_val, "remaining": duration
                })
            msg_parts.append(f"{display_name(ally)}'s membrane absorbs {int(absorb_val * 100)}% of damage taken for {duration} turns!")

        elif effect_type == "elemental_adapt":
            # Perfect Mimicry: adapt to the last element that struck her
            el = ally.get("_last_element_hit")
            if not el:
                msg_parts.append(f"{display_name(ally)} has no recent element to mimic!")
            else:
                dmg_v = _scaled_mag(effect.get("dmg_value", 0.25))
                res_v = _scaled_mag(effect.get("res_value", 0.5))
                ally.setdefault("active_buffs", []).append({
                    "type": "elemental_adapt_dmg", "element": el, "value": dmg_v, "remaining": duration
                })
                ally.setdefault("active_buffs", []).append({
                    "type": "elemental_adapt_res", "element": el, "value": res_v, "remaining": duration
                })
                msg_parts.append(f"{display_name(ally)} mimics {el.capitalize()} — +{int(dmg_v * 100)}% damage, +{int(res_v * 100)}% resistance for {duration} turns!")

        elif effect_type == "perfect_guard":
            recipients = [target] if target else [ally]
            if target_type == "all_allies":
                recipients = [player] + allies
            pct_val = value if isinstance(value, float) and value <= 1 else value / 100.0
            pct_val = pct_val * status_mult
            reflect_val = _scaled_mag(effect.get("reflect_value", 0.3))
            for r in recipients:
                r.setdefault("active_buffs", []).append({
                    "type": "defense_pct", "value": pct_val, "remaining": duration
                })
                r.setdefault("active_buffs", []).append({
                    "type": "reflection", "value": reflect_val, "remaining": duration
                })
            pct_display = int(pct_val * 100)
            msg_parts.append(f"{display_name(ally)} raises a perfect guard! ({pct_display}% less damage)")

        elif effect_type == "phantom_dodge":
            recipients = [target] if target else [ally]
            ev_value = _scaled_mag(value)
            for r in recipients:
                r.setdefault("active_buffs", []).append({
                    "type": "evasion", "value": ev_value, "remaining": duration
                })
                r.setdefault("active_buffs", []).append({
                    "stat": "Dexterity", "value": _scaled_mag(effect.get("dex_bonus", 3)), "remaining": duration
                })
            msg_parts.append(f"{display_name(ally)} becomes a phantom!")

        elif effect_type == "confusion":
            from combat.status_effects import check_status_resisted
            live = [e for e in enemies if e["hp"] > 0]
            for e in live:
                if check_status_resisted(e):
                    continue
                e["confused"] = True
                e.setdefault("active_debuffs", []).append({
                    "type": "confusion", "value": _scaled_mag(value), "remaining": duration
                })
            msg_parts.append(f"{display_name(ally)} confuses the enemies!")

        elif effect_type == "shock":
            shock_dmg = _scaled_mag(value)
            if target and target_type == "enemy":
                apply_shock(target, shock_dmg, duration)
                msg_parts.append(f"{target['name']} is shocked!")
            else:
                live = [e for e in enemies if e["hp"] > 0]
                for e in live:
                    apply_shock(e, shock_dmg, duration)
                msg_parts.append(f"{display_name(ally)} shocks all enemies!")

        elif effect_type == "barrier":
            recipients = [target] if target else [ally]
            if target_type == "all_allies":
                recipients = [player] + allies
            # Optional: size the barrier off the caster's max HP (fixed at cast).
            caster_hp_pct = effect.get("value_from_caster_hp", 0)
            if caster_hp_pct:
                caster_max = player_max_hp(ally) if ally is player else ally.get("max_hp", 100)
                barrier_value = int(caster_max * caster_hp_pct * status_mult)
            else:
                barrier_value = _scaled_mag(value)
            for r in recipients:
                apply_barrier(r, barrier_value, duration)
            msg_parts.append(f"{display_name(ally)} raises a barrier absorbing up to {barrier_value} damage for {duration} turns!")

        elif effect_type == "death_ward":
            recipients = [target] if target else [ally]
            if target_type == "all_allies":
                recipients = [player] + allies
            for r in recipients:
                apply_death_ward(r, duration, hp_pct=effect.get("hp_pct", 0.0))
            msg_parts.append(f"{display_name(ally)} vows that none shall fall for {duration} turns!")

        elif effect_type == "haste":
            recipients = [target] if target else [ally]
            if target_type == "all_allies":
                recipients = [player] + allies
            init_bonus = _scaled_mag(effect.get("init_bonus", 3))
            cd_reduce = _scaled_mag(effect.get("cd_reduction", 1))
            for r in recipients:
                apply_haste(r, duration, init_bonus, cd_reduce)
            msg_parts.append(f"{display_name(ally)} grants haste for {duration} turns!")

        elif effect_type == "sleep":
            if target and target_type == "enemy":
                apply_sleep(target, duration)
                msg_parts.append(f"{target['name']} falls asleep!")
            else:
                live = [e for e in enemies if e["hp"] > 0]
                for e in live:
                    apply_sleep(e, duration)
                msg_parts.append(f"{display_name(ally)} lulls all enemies to sleep!")

        elif effect_type == "paralyze":
            if target and target_type == "enemy":
                apply_paralyze(target, duration)
                msg_parts.append(f"{target['name']} is paralyzed!")
            else:
                live = [e for e in enemies if e["hp"] > 0]
                for e in live:
                    apply_paralyze(e, duration)
                msg_parts.append(f"{display_name(ally)} paralyzes all enemies!")

        elif effect_type == "entomb":
            if target and target_type == "enemy":
                apply_entomb(target, duration)
                msg_parts.append(f"{target['name']} is entombed in stone!")
            else:
                live = [e for e in enemies if e["hp"] > 0]
                for e in live:
                    apply_entomb(e, duration)
                msg_parts.append(f"{display_name(ally)} entombs all enemies in stone!")

        elif effect_type == "void_touched":
            if target and target_type == "enemy":
                apply_void_touched(target, duration)
                msg_parts.append(f"{target['name']} is void-touched!")
            else:
                live = [e for e in enemies if e["hp"] > 0]
                for e in live:
                    apply_void_touched(e, duration)
                msg_parts.append(f"{display_name(ally)} curses all enemies with void touch!")

        elif effect_type == "life_steal":
            # Handled during damage calculation below; mark for post-damage heal
            pass

        elif effect_type == "random_buff":
            options = effect.get("options", [])
            if options:
                chosen = random.choice(options)
                opt_type = chosen.get("type")
                opt_value = _scaled_mag(chosen.get("value", 0))
                opt_duration = chosen.get("duration", 2)
                opt_label = chosen.get("label", "Random buff activated!")
                msg_parts.append(opt_label)
                if opt_type == "evasion":
                    ally.setdefault("active_buffs", []).append({
                        "type": "evasion", "value": opt_value, "remaining": opt_duration
                    })
                elif opt_type == "damage_boost":
                    ally.setdefault("active_buffs", []).append({
                        "type": "damage_boost", "value": opt_value, "remaining": opt_duration
                    })

        elif effect_type == "damage_boost":
            recipients = [target] if target else [ally]
            if target_type == "all_allies":
                recipients = [player] + allies
            boost_val = _scaled_mag(value)
            for r in recipients:
                r.setdefault("active_buffs", []).append({
                    "type": "damage_boost", "value": boost_val, "remaining": duration
                })
            msg_parts.append(f"{display_name(ally)} grants +{int(boost_val * 100)}% damage for {duration} turns!")

        elif effect_type == "elemental_weakness":
            from combat.status_effects import check_status_resisted
            weak_val = _scaled_mag(value)
            if target_type == "enemy" and target:
                if check_status_resisted(target):
                    msg_parts.append(f"{target['name']} shrugs off the elemental breach!")
                else:
                    target.setdefault("active_debuffs", []).append({
                        "type": "elemental_weakness", "value": weak_val, "remaining": duration
                    })
                    msg_parts.append(f"{target['name']}'s elemental resistances are lowered — +{int(weak_val * 100)}% weakness!")
                    # Also apply stat debuff if specified
                    stat_debuff = effect.get("stat_debuff")
                    stat_value = effect.get("stat_value")
                    if stat_debuff and stat_value:
                        stat_value = _scaled_mag(stat_value)
                        target.setdefault("active_debuffs", []).append({
                            "type": "curse", "penalty": stat_value,
                            "remaining": duration, "stats": [stat_debuff]
                        })
                        msg_parts.append(f"{target['name']}'s {stat_debuff} reduced by {abs(stat_value)}!")
            else:
                for e in [e for e in enemies if e["hp"] > 0]:
                    if check_status_resisted(e):
                        continue
                    e.setdefault("active_debuffs", []).append({
                        "type": "elemental_weakness", "value": weak_val, "remaining": duration
                    })
                msg_parts.append(f"All enemies' elemental resistances lowered!")

        elif effect_type == "marked":
            mark_val = _scaled_mag(value)
            if target_type == "enemy" and target:
                mark_targets = [target]
            else:
                mark_targets = [e for e in enemies if e["hp"] > 0]
            for tgt in mark_targets:
                tgt["hunters_mark"] = True
                tgt["hunters_mark_bonus"] = mark_val
                tgt["hunters_mark_source"] = ally.get("name", "Ally")
                tgt["hunters_mark_turns"] = duration
                msg_parts.append(f"{display_name(ally)} marks {tgt['name']}! +{int(mark_val * 100)}% damage taken for {duration} turns!")

        elif effect_type == "damage_taken_up":
            from combat.status_effects import apply_damage_taken_up
            dt_val = _scaled_mag(value)
            if target_type == "enemy" and target:
                apply_damage_taken_up(target, dt_val, duration)
                msg_parts.append(f"{target['name']}'s will is drained — takes +{int(dt_val * 100)}% damage for {duration} turns!")
            else:
                live = [e for e in enemies if e["hp"] > 0]
                for e in live:
                    apply_damage_taken_up(e, dt_val, duration)
                msg_parts.append(f"{display_name(ally)} drains the enemies' will — all take +{int(dt_val * 100)}% damage for {duration} turns!")

        elif effect_type == "multi":
            # Handle nested effects (e.g. Through the Forest: crit_boost +
            # fear_immunity; awakened kits: absorb + reflect, stun + entomb...)
            nested = effect.get("effects", [])
            recipients = [target] if target else [ally]
            if target_type == "all_allies":
                recipients = [player] + allies
            if target is not None and target is not player and not target.get("is_ally"):
                enemy_targets = [target]
            else:
                enemy_targets = [e for e in enemies if e["hp"] > 0]
            for sub in nested:
                sub_type = sub.get("type")
                sub_value = sub.get("value", 0)
                sub_duration = sub.get("duration", duration)
                if sub_type == "crit_boost":
                    for r in recipients:
                        r.setdefault("active_buffs", []).append({
                            "type": "crit_chance", "value": sub_value, "remaining": sub_duration
                        })
                    msg_parts.append(f"{display_name(ally)} grants +{int(sub_value * 100)}% crit chance for {sub_duration} turns!")
                elif sub_type == "fear_immunity":
                    for r in recipients:
                        r.setdefault("active_buffs", []).append({
                            "type": "fear_immunity", "remaining": sub_duration
                        })
                    msg_parts.append(f"{display_name(ally)} grants Fear immunity for {sub_duration} turns!")
                elif sub_type == "stat_buff":
                    stat = sub.get("stat", "Strength")
                    for r in recipients:
                        r.setdefault("active_buffs", []).append({
                            "stat": stat, "value": _scaled_mag(sub_value), "remaining": sub_duration
                        })
                elif sub_type == "evasion":
                    sub_recipients = recipients
                    if sub.get("self_only"):
                        sub_recipients = [ally]
                    elif sub.get("exclude_self"):
                        sub_recipients = [r for r in ([player] + allies) if r is not ally]
                    ev_value = _scaled_mag(sub_value)
                    for r in sub_recipients:
                        r.setdefault("active_buffs", []).append({
                            "type": "evasion", "value": ev_value, "remaining": sub_duration
                        })
                    if sub.get("exclude_self"):
                        msg_parts.append(f"The party gains +{int(ev_value * 100)}% dodge for {sub_duration} turns!")
                    elif sub.get("self_only"):
                        msg_parts.append(f"{display_name(ally)} gains +{int(ev_value * 100)}% dodge for {sub_duration} turns!")
                elif sub_type == "damage_reduction":
                    pct_val = sub_value if isinstance(sub_value, float) and sub_value <= 1 else sub_value / 100.0
                    pct_val = pct_val * status_mult
                    for r in recipients:
                        r.setdefault("active_buffs", []).append({
                            "type": "defense_pct", "value": pct_val, "remaining": sub_duration
                        })
                    msg_parts.append(f"{display_name(ally)} reduces damage taken by {int(pct_val * 100)}% for {sub_duration} turns!")
                elif sub_type == "reflection":
                    reflect_val = _scaled_mag(sub_value)
                    for r in recipients:
                        r.setdefault("active_buffs", []).append({
                            "type": "reflection", "value": reflect_val, "remaining": sub_duration
                        })
                    msg_parts.append(f"{display_name(ally)} will reflect {int(reflect_val * 100)}% of damage taken!")
                elif sub_type == "damage_absorption":
                    absorb_val = sub_value if isinstance(sub_value, float) and sub_value <= 1 else sub_value / 100.0
                    absorb_val = absorb_val * status_mult
                    for r in recipients:
                        r.setdefault("active_buffs", []).append({
                            "type": "damage_absorption", "value": absorb_val, "remaining": sub_duration
                        })
                    msg_parts.append(f"{display_name(ally)} will absorb {int(absorb_val * 100)}% of damage taken!")
                elif sub_type == "death_ward":
                    for r in recipients:
                        apply_death_ward(r, sub_duration, hp_pct=sub.get("hp_pct", 0.0))
                    msg_parts.append(f"{display_name(ally)} vows that none shall fall for {sub_duration} turns!")
                elif sub_type == "dodge_counter":
                    counter_val = _scaled_mag(sub_value)
                    for r in recipients:
                        r.setdefault("active_buffs", []).append({
                            "type": "dodge_counter", "value": counter_val, "remaining": sub_duration
                        })
                    msg_parts.append(f"Each dodge answers with a counter for {sub_duration} turns!")
                elif sub_type == "cd_refund":
                    refund = int(sub_value)
                    if refund > 0:
                        for r in recipients:
                            for cd_key in list(r.setdefault("skill_cooldowns", {}).keys()):
                                r["skill_cooldowns"][cd_key] = max(0, r["skill_cooldowns"][cd_key] - refund)
                        tgt_name = display_name(recipients[0]) if recipients else display_name(ally)
                        msg_parts.append(f"{tgt_name}'s active cooldowns reduced by {refund}!")
                elif sub_type == "power_buff":
                    for r in recipients:
                        r.setdefault("active_buffs", []).append({
                            "type": "power_buff", "value": _scaled_mag(sub_value), "remaining": sub_duration
                        })
                    tgt_name = display_name(recipients[0]) if recipients else display_name(ally)
                    msg_parts.append(f"{tgt_name}'s next action is empowered!")
                elif sub_type == "blind":
                    from combat.status_effects import check_status_resisted as _res
                    for e in enemy_targets:
                        if _res(e):
                            continue
                        e["blinded"] = True
                        e.setdefault("active_debuffs", []).append({
                            "type": "blind", "value": sub_value, "remaining": sub_duration
                        })
                    msg_parts.append(f"The enemies are blinded! ({int(sub_value * 100)}% miss, {sub_duration}t)")
                elif sub_type == "marked":
                    mark_val = _scaled_mag(sub_value)
                    for e in enemy_targets:
                        e["hunters_mark"] = True
                        e["hunters_mark_bonus"] = mark_val
                        e["hunters_mark_source"] = ally.get("name", "Ally")
                        e["hunters_mark_turns"] = sub_duration
                    msg_parts.append(f"The prey is marked! +{int(mark_val * 100)}% damage taken for {sub_duration} turns!")
                elif sub_type == "fear":
                    from combat.status_effects import check_status_resisted as _res
                    fear_val = _scaled_mag(sub_value)
                    for e in enemy_targets:
                        if _res(e):
                            continue
                        e.setdefault("active_debuffs", []).append({
                            "type": "fear", "value": fear_val, "remaining": sub_duration
                        })
                    msg_parts.append(f"Terror takes hold — enemies deal {int(fear_val * 100)}% less damage for {sub_duration} turns!")
                elif sub_type == "stun":
                    from combat.status_effects import check_status_resisted as _res
                    for e in enemy_targets:
                        if _res(e):
                            msg_parts.append(f"{e['name']} shrugs off the stun!")
                            continue
                        e["stunned"] = True
                        e.setdefault("active_debuffs", []).append({"type": "stun", "remaining": sub_duration})
                        msg_parts.append(f"{e['name']} is stunned!")
                elif sub_type == "entomb":
                    chance = sub.get("chance", 1.0)
                    for e in enemy_targets:
                        if random.random() >= chance:
                            continue
                        if apply_entomb(e, sub_duration) != "resisted":
                            msg_parts.append(f"{e['name']} is entombed in stone!")
                elif sub_type == "stat_debuff":
                    from combat.status_effects import check_status_resisted as _res
                    stat = sub.get("stat", "Strength")
                    debuff_value = _scaled_mag(_scale_effect_value(sub, ally.get("level", 1)))
                    for e in enemy_targets:
                        if _res(e):
                            continue
                        e.setdefault("active_debuffs", []).append({
                            "type": "curse", "penalty": debuff_value,
                            "remaining": sub_duration, "stats": [stat]
                        })
                    msg_parts.append(f"All enemies' {stat} reduced by {debuff_value}!")

        # If this skill has no damage component and only an effect, finish here
        if base_power == 0 and not any(k in skill_def for k in (
            "poison_damage", "burn_damage", "bleed_damage", "stun_chance", "guaranteed_crit",
            "ignore_armor", "apply_slow", "apply_weaken", "crit_bonus",
            "ignore_armor_pct", "bonus_vs_races", "push_initiative",
            "shock_damage", "apply_sleep", "apply_paralyze", "apply_entomb",
            "apply_void_touched", "heal_percent", "revive_percent",
            "cleanse_one_debuff", "cleanse_all_debuffs"
        )):
            from pandemonium_curses import get_cooldown_increase
            cooldown = skill_def.get("cooldown", 1) + get_cooldown_increase(player)
            ally.setdefault("skill_cooldowns", {})[skill_id] = max(0, cooldown - cd_reduction)
            add_ally_skill_mastery_xp(ally, skill_id)
            return " ".join(msg_parts), False

    # ── Damage / Heal Calculation ──
    power = int((base_power + scaling) * power_mult)

    # Consume power_buff if present (empowers the next damaging action).
    # Heal/support casts leave it in place for the next attack.
    if target_type in ("enemy", "enemies"):
        for buff in ally.get("active_buffs", [])[:]:
            if buff.get("type") == "power_buff":
                power = int(power * (1 + buff.get("value", 0)))
                msg_parts.append(f"Empowered! Damage increased by {int(buff.get('value', 0) * 100)}%!")
                ally["active_buffs"].remove(buff)
                break

    guaranteed = skill_def.get("guaranteed_crit", False)
    if guaranteed:
        power *= 2
        msg_parts.append("Critical hit!")

    # Multi-target enemy damage
    if target_type == "enemies":
        live = [e for e in enemies if e["hp"] > 0]
        total_dmg = 0
        bleed_feast_dmg = 0   # portion of total dealt to already-bleeding targets
        from combat.status_effects import is_bleeding
        for e in live:
            dmg, did_crit = _calc_dmg(e, power, skill_def.get("ignore_armor", False), guaranteed_crit=guaranteed)
            e["hp"] -= dmg
            msg_parts.append(format_damage_msg(display_name(ally), e['name'], dmg, element=skill_def.get("elemental"), crit=did_crit, skill_name=skill_def['name']))
            total_dmg += dmg
            if is_bleeding(e):
                bleed_feast_dmg += dmg
            if e["hp"] <= 0:
                msg_parts.append(f"{e['name']} is defeated!")
            # Status effects
            if skill_def.get("poison_damage"):
                p_dmg = skill_def["poison_damage"]
                if status_mult > 1:
                    p_dmg = int(p_dmg * status_mult)
                if apply_poison(e, p_dmg, skill_def.get("poison_duration", 3)) != "resisted":
                    msg_parts.append(f"{e['name']} is poisoned!")
            if skill_def.get("burn_damage"):
                from combat.status_effects import damage_to_burn_tier
                b_tier = min(5, damage_to_burn_tier(skill_def["burn_damage"]) + burn_tier_bonus)
                if apply_burn(e, b_tier, skill_def.get("burn_duration", 3)) != "resisted":
                    msg_parts.append(f"{e['name']} is burning!")
            if skill_def.get("bleed_damage"):
                bl_dmg = skill_def["bleed_damage"]
                if status_mult > 1:
                    bl_dmg = int(bl_dmg * status_mult)
                if apply_bleed(e, bl_dmg, skill_def.get("bleed_duration", 4)) != "resisted":
                    msg_parts.append(f"{e['name']} is bleeding!")
            if skill_def.get("stun_chance") and random.random() < skill_def["stun_chance"]:
                from combat.status_effects import check_status_resisted
                if check_status_resisted(e):
                    msg_parts.append(f"{e['name']} shrugs off the stun!")
                else:
                    e["stunned"] = True
                    e.setdefault("active_debuffs", []).append({"type": "stun", "remaining": 3})
                    msg_parts.append(f"{e['name']} is stunned!")
            if skill_def.get("apply_slow"):
                from combat.status_effects import apply_slow_to_enemy
                if apply_slow_to_enemy(e, duration=3) != "resisted":
                    msg_parts.append(f"{e['name']} is slowed!")
            if skill_def.get("apply_weaken"):
                from combat.status_effects import apply_weaken
                if apply_weaken(e, duration=3) != "resisted":
                    msg_parts.append(f"{e['name']} is weakened!")
            if skill_def.get("shock_damage"):
                if apply_shock(e, _scaled_mag(skill_def["shock_damage"]), skill_def.get("shock_duration", 3)) != "resisted":
                    msg_parts.append(f"{e['name']} is shocked!")
            if skill_def.get("apply_sleep"):
                if apply_sleep(e, skill_def.get("sleep_duration", 3)) != "resisted":
                    msg_parts.append(f"{e['name']} falls asleep!")
            if skill_def.get("apply_paralyze"):
                if apply_paralyze(e, skill_def.get("paralyze_duration", 2)) != "resisted":
                    msg_parts.append(f"{e['name']} is paralyzed!")
            if skill_def.get("apply_entomb"):
                if apply_entomb(e, skill_def.get("entomb_duration", 3)) != "resisted":
                    msg_parts.append(f"{e['name']} is entombed!")
            if skill_def.get("apply_void_touched"):
                if apply_void_touched(e, skill_def.get("void_touched_duration", 2)) != "resisted":
                    msg_parts.append(f"{e['name']} is void-touched!")
        # Expose (armour shred — Rolling Thunder)
        if skill_def.get("expose_armor"):
            from combat.status_effects import apply_expose
            for e in live:
                if e["hp"] > 0:
                    res, new_con = apply_expose(e, skill_def["expose_armor"])
                    if res == "applied":
                        msg_parts.append(f"{e['name']}'s armour shatters! (CON → {new_con})")
        # Push initiative: push enemies to bottom of initiative order
        if skill_def.get("push_initiative"):
            msg_parts.append(f"{display_name(ally)} pushes enemies to the bottom of initiative!")
            # Signal to combat engine to move enemies to end of turn order
            ally["_push_initiative_flag"] = True

        if not [e for e in enemies if e["hp"] > 0]:
            victory = True
        # Life steal
        if effect and effect.get("type") == "life_steal" and total_dmg > 0:
            ls = _scaled_mag(effect.get("value", 0))
            heal = int(total_dmg * ls)
            old_hp = ally["current_hp"]
            ally["current_hp"] = min(old_hp + heal, ally["max_hp"])
            actual = ally["current_hp"] - old_hp
            if actual > 0:
                msg_parts.append(f"{display_name(ally)} recovers {actual} HP!")
        # Race passive life steal (Vampire; doubled while the target bleeds)
        rp_ls = get_race_lifesteal(ally)
        race_passive = get_race_passive(ally.get("race"))
        if race_passive and rp_ls > 0 and total_dmg > 0:
            from combat.status_effects import BLEED_FEAST_MULT
            feast_dmg = total_dmg + bleed_feast_dmg * (BLEED_FEAST_MULT - 1.0)
            heal = int(feast_dmg * rp_ls)
            old_hp = ally["current_hp"]
            ally["current_hp"] = min(old_hp + heal, ally["max_hp"])
            actual = ally["current_hp"] - old_hp
            if actual > 0:
                msg_parts.append(f"[{race_passive['name']}] {display_name(ally)} recovers {actual} HP!")
        # Event Horizon — Death: allies drain 10% of the damage dealt
        _eh_ls = ally.get("_eh_joker_lifesteal", 0) or 0
        if _eh_ls > 0 and total_dmg > 0:
            heal = int(total_dmg * _eh_ls)
            if heal > 0:
                from combat.status_effects import apply_healing as _eh_heal_fn
                actual = _eh_heal_fn(ally, heal, source=ally)
                if actual > 0:
                    msg_parts.append(f"[Death] {display_name(ally)} drains {actual} HP.")

    # Single-target enemy damage
    elif target_type == "enemy" and target:
        hits = skill_def.get("hits", 1)
        for _ in range(hits):
            dmg, did_crit = _calc_dmg(target, power, skill_def.get("ignore_armor", False), guaranteed_crit=guaranteed)
            target["hp"] -= dmg
            msg_parts.append(format_damage_msg(display_name(ally), target['name'], dmg, element=skill_def.get("elemental"), crit=did_crit, skill_name=skill_def['name']))
            # Wake sleeping enemy on damage
            wake_msg = wake_on_damage(target)
            if wake_msg:
                msg_parts.append(wake_msg)
            if target["hp"] <= 0:
                msg_parts.append(f"{target['name']} is defeated!")
                victory = True
                break
            # Status effects
            from combat.status_effects import check_status_resisted as _status_resisted
            if skill_def.get("poison_damage"):
                p_dmg = skill_def["poison_damage"]
                if status_mult > 1:
                    p_dmg = int(p_dmg * status_mult)
                if apply_poison(target, p_dmg, skill_def.get("poison_duration", 3)) != "resisted":
                    msg_parts.append(f"{target['name']} is poisoned!")
            if skill_def.get("burn_damage"):
                from combat.status_effects import damage_to_burn_tier
                b_tier = min(5, damage_to_burn_tier(skill_def["burn_damage"]) + burn_tier_bonus)
                if apply_burn(target, b_tier, skill_def.get("burn_duration", 3)) != "resisted":
                    msg_parts.append(f"{target['name']} is burning!")
            if skill_def.get("bleed_damage"):
                bl_dmg = skill_def["bleed_damage"]
                if status_mult > 1:
                    bl_dmg = int(bl_dmg * status_mult)
                if apply_bleed(target, bl_dmg, skill_def.get("bleed_duration", 4)) != "resisted":
                    msg_parts.append(f"{target['name']} is bleeding!")
            if skill_def.get("stun_chance") and random.random() < skill_def["stun_chance"]:
                if _status_resisted(target):
                    msg_parts.append(f"{target['name']} shrugs off the stun!")
                else:
                    target["stunned"] = True
                    target.setdefault("active_debuffs", []).append({"type": "stun", "remaining": 3})
                    msg_parts.append(f"{target['name']} is stunned!")
            if skill_def.get("apply_slow"):
                from combat.status_effects import apply_slow_to_enemy
                if apply_slow_to_enemy(target, duration=3) != "resisted":
                    msg_parts.append(f"{target['name']} is slowed!")
            if skill_def.get("apply_weaken"):
                from combat.status_effects import apply_weaken
                if apply_weaken(target, duration=3) != "resisted":
                    msg_parts.append(f"{target['name']} is weakened!")
            if skill_def.get("shock_damage"):
                if apply_shock(target, _scaled_mag(skill_def["shock_damage"]), skill_def.get("shock_duration", 3)) != "resisted":
                    msg_parts.append(f"{target['name']} is shocked!")
            if skill_def.get("apply_sleep"):
                if apply_sleep(target, skill_def.get("sleep_duration", 3)) != "resisted":
                    msg_parts.append(f"{target['name']} falls asleep!")
            if skill_def.get("apply_paralyze"):
                if apply_paralyze(target, skill_def.get("paralyze_duration", 2)) != "resisted":
                    msg_parts.append(f"{target['name']} is paralyzed!")
            if skill_def.get("apply_entomb"):
                if apply_entomb(target, skill_def.get("entomb_duration", 3)) != "resisted":
                    msg_parts.append(f"{target['name']} is entombed!")
            if skill_def.get("apply_void_touched"):
                if apply_void_touched(target, skill_def.get("void_touched_duration", 2)) != "resisted":
                    msg_parts.append(f"{target['name']} is void-touched!")
            if skill_def.get("blind_value"):
                if _status_resisted(target):
                    msg_parts.append(f"{target['name']} shrugs off the clinging dust!")
                else:
                    target["blinded"] = True
                    target.setdefault("active_debuffs", []).append({
                        "type": "blind", "value": skill_def["blind_value"],
                        "remaining": skill_def.get("blind_duration", 2)
                    })
                    msg_parts.append(f"{target['name']} is blinded!")
            if skill_def.get("apply_fear"):
                if _status_resisted(target):
                    msg_parts.append(f"{target['name']} masters its fear!")
                else:
                    target.setdefault("active_debuffs", []).append({
                        "type": "fear", "value": skill_def.get("fear_value", 0.25),
                        "remaining": skill_def.get("fear_duration", 2)
                    })
                    msg_parts.append(f"{target['name']} is shaken with fear!")
        # Expose (armour shred — Corrosive Deluge / awakened kits)
        if skill_def.get("expose_armor") and target["hp"] > 0:
            from combat.status_effects import apply_expose
            res, new_con = apply_expose(target, skill_def["expose_armor"])
            if res == "applied":
                msg_parts.append(f"{target['name']}'s armour shatters! (CON → {new_con})")
            elif res == "resisted":
                msg_parts.append(f"{target['name']} shrugs off the armour shatter!")
        # Push initiative: push enemies to bottom of initiative order
        if skill_def.get("push_initiative"):
            msg_parts.append(f"{display_name(ally)} pushes enemies to the bottom of initiative!")
            ally["_push_initiative_flag"] = True
        # Life steal (fix: applies to every damaging single-target skill)
        if effect and effect.get("type") == "life_steal" and dmg > 0:
            ls = _scaled_mag(effect.get("value", 0))
            heal = int(dmg * ls)
            old_hp = ally["current_hp"]
            ally["current_hp"] = min(old_hp + heal, ally["max_hp"])
            actual = ally["current_hp"] - old_hp
            if actual > 0:
                msg_parts.append(f"{display_name(ally)} recovers {actual} HP!")
        # Race passive life steal (Vampire; doubled while the target bleeds)
        rp_ls = get_race_lifesteal(ally)
        race_passive = get_race_passive(ally.get("race"))
        if race_passive and rp_ls > 0 and dmg > 0:
            from combat.status_effects import get_bleed_feast_multiplier
            heal = int(dmg * rp_ls * get_bleed_feast_multiplier(target))
            old_hp = ally["current_hp"]
            ally["current_hp"] = min(old_hp + heal, ally["max_hp"])
            actual = ally["current_hp"] - old_hp
            if actual > 0:
                msg_parts.append(f"[{race_passive['name']}] {display_name(ally)} recovers {actual} HP!")
        # Event Horizon — Death: allies drain 10% of the damage dealt
        _eh_ls = ally.get("_eh_joker_lifesteal", 0) or 0
        if _eh_ls > 0 and dmg > 0:
            heal = int(dmg * _eh_ls)
            if heal > 0:
                from combat.status_effects import apply_healing as _eh_heal_fn
                actual = _eh_heal_fn(ally, heal, source=ally)
                if actual > 0:
                    msg_parts.append(f"[Death] {display_name(ally)} drains {actual} HP.")

    # Healing skills
    elif target_type in ("self", "ally_or_self", "all_allies", "dead_ally"):
        heal_percent = skill_def.get("heal_percent")
        if target_type == "all_allies":
            party = [player] + allies
            total_heal = 0
            for member in party:
                if member.get("current_hp", 0) <= 0:
                    continue
                max_hp = player_max_hp(member) if member is player else member.get("max_hp", member.get("current_hp", 1))
                if heal_percent:
                    heal = int(max_hp * heal_percent)
                else:
                    from combat.stat_milestones import get_wisdom_bonus
                    heal = int((base_power + scaling) * power_mult) + get_wisdom_bonus(ally)
                old_hp = member.get("current_hp", 0)
                if is_heal_blocked(member, ally):
                    name = "You" if member is player else member.get("name", "Ally")
                    msg_parts.append(f"{name}'s Unholy Resilience rejects allied healing!")
                    continue
                # Pandemonium: Blighted Recovery curse — allied heals reduced too
                from pandemonium_curses import apply_healing_reduction
                heal = apply_healing_reduction(player, heal)
                healed = apply_healing(member, heal, source=ally)
                if healed < 0:
                    msg_parts.append(f"The void twists the healing! {member.get('name', 'Ally')} takes {-healed} damage instead!")
                total_heal += max(0, healed)
                # Cleanse all debuffs if skill has cleanse_all_debuffs
                if skill_def.get("cleanse_all_debuffs") and member.get("active_debuffs"):
                    from combat.status_effects import is_cleansable
                    blocked = [d for d in member.get("active_debuffs", []) if not is_cleansable(d)]
                    for d in list(member.get("active_debuffs", [])):
                        if is_cleansable(d):
                            _clear_flat_debuff_flag(member, d.get("type"))
                    member["active_debuffs"] = blocked
                    name = "You" if member is player else member.get("name", "Ally")
                    if blocked:
                        msg_parts.append(f"{name}'s debuffs are cleansed — but some wounds resist!")
                    else:
                        msg_parts.append(f"{name}'s debuffs are all cleansed!")
                # Cleanse one debuff per ally if skill has cleanse_one_debuff
                elif skill_def.get("cleanse_one_debuff") and member.get("active_debuffs"):
                    from combat.status_effects import is_cleansable
                    idx = next((i for i, d in enumerate(member["active_debuffs"]) if is_cleansable(d)), None)
                    if idx is not None:
                        removed = member["active_debuffs"].pop(idx)
                        _clear_flat_debuff_flag(member, removed.get("type"))
                        name = "You" if member is player else member.get("name", "Ally")
                        msg_parts.append(f"{name}'s {removed.get('type', 'debuff')} cleansed!")
            if total_heal > 0:
                msg_parts.append(f"Total healing: {total_heal} HP!")
        elif target_type == "dead_ally":
            if target:
                max_hp = player_max_hp(target) if target is player else target.get("max_hp", 1)
                revive_pct = skill_def.get("revive_percent", 0.50)
                revive_table = REVIVE_MASTERY_PCT.get(skill_id)
                if revive_table:
                    revive_pct = revive_table[mastery]
                revive_hp = int(max_hp * revive_pct)
                target["current_hp"] = revive_hp
                if target is not player:
                    # A revived ally must rejoin the living — the defeated
                    # flag otherwise keeps them benched despite restored HP.
                    target["defeated"] = False
                name = display_name(target)
                msg_parts.append(f"{name} is resurrected with {revive_hp} HP!")
                shield_pct = skill_def.get("revive_barrier_pct", 0)
                if shield_pct:
                    caster_max = player_max_hp(ally) if ally is player else ally.get("max_hp", 100)
                    shield = int(caster_max * shield_pct)
                    apply_barrier(target, shield, skill_def.get("revive_barrier_duration", 2))
                    msg_parts.append(f"A {shield}-point barrier surrounds {name}!")
        else:
            if target:
                max_hp = player_max_hp(target) if target is player else target.get("max_hp", target.get("current_hp", 1))
                if heal_percent:
                    heal = int(max_hp * heal_percent)
                else:
                    from combat.stat_milestones import get_wisdom_bonus
                    heal = int((base_power + scaling) * power_mult) + get_wisdom_bonus(ally)
                old_hp = target.get("current_hp", 0)
                if is_heal_blocked(target, ally):
                    msg_parts.append(f"{display_name(target)}'s Unholy Resilience rejects allied healing!")
                else:
                    # Pandemonium: Blighted Recovery curse — allied heals reduced too
                    from pandemonium_curses import apply_healing_reduction
                    heal = apply_healing_reduction(player, heal)
                    actual = apply_healing(target, heal, source=ally)
                    name = display_name(target)
                    if actual < 0:
                        msg_parts.append(f"The void twists the healing! {name} takes {-actual} damage instead!")
                    else:
                        msg_parts.append(f"{name} is healed for {actual} HP!")
                # Cleanse all debuffs if applicable
                if skill_def.get("cleanse_all_debuffs") and target.get("active_debuffs"):
                    from combat.status_effects import is_cleansable
                    blocked = [d for d in target.get("active_debuffs", []) if not is_cleansable(d)]
                    for d in list(target.get("active_debuffs", [])):
                        if is_cleansable(d):
                            _clear_flat_debuff_flag(target, d.get("type"))
                    target["active_debuffs"] = blocked
                    if blocked:
                        msg_parts.append(f"{name}'s debuffs are cleansed — but some wounds resist!")
                    else:
                        msg_parts.append(f"{name}'s debuffs are all cleansed!")
                # Cleanse one debuff if applicable
                elif skill_def.get("cleanse_one_debuff") and target.get("active_debuffs"):
                    from combat.status_effects import is_cleansable
                    idx = next((i for i, d in enumerate(target["active_debuffs"]) if is_cleansable(d)), None)
                    if idx is not None:
                        removed = target["active_debuffs"].pop(idx)
                        _clear_flat_debuff_flag(target, removed.get("type"))
                        msg_parts.append(f"{name}'s {removed.get('type', 'debuff')} cleansed!")

    # ── Cooldown & Mastery ──
    from pandemonium_curses import get_cooldown_increase
    cooldown = skill_def.get("cooldown", 1) + get_cooldown_increase(player)

    # Consume cooldown_reduction buff if present
    for buff in ally.get("active_buffs", [])[:]:
        if buff.get("type") == "cooldown_reduction":
            reduction = buff.get("value", 0)
            cooldown = max(0, cooldown - reduction)
            msg_parts.append(f"Cooldown reduced by {reduction}!")
            ally["active_buffs"].remove(buff)
            break

    ally.setdefault("skill_cooldowns", {})[skill_id] = max(0, cooldown - cd_reduction)

    mastery_upgrade = add_ally_skill_mastery_xp(ally, skill_id)
    if mastery_upgrade:
        msg_parts.append("Skill Mastery increased! ★")

    # ── Sky Piercer: execute non-superboss enemies left at/below threshold ──
    from combat.weapon.sky_piercer import check_sky_piercer_execute
    for i, e in enumerate(enemies):
        if i < len(pre_hp) and e["hp"] < pre_hp[i]:
            check_sky_piercer_execute(ally, e, pre_hp[i] - e["hp"])
    # Victory is only valid if ALL enemies are defeated (covers executes too).
    victory = not any(e["hp"] > 0 for e in enemies)

    return " ".join(msg_parts), victory


# ══════════════════════════════════════════════════════════════════════════════
# Vorpal Blade — Alice Skill Swap System
# ══════════════════════════════════════════════════════════════════════════════

_VORPAL_INNATE_SKILLS = ["vorpal_edge", "snicker_snack"]
_VORPAL_UPGRADE_SKILL = HEROINE_UPGRADE_SKILLS["alice"]
_ALICE_NORMAL_INNATE = ["curious_inquiry", "try_me"]


def swap_alice_to_vorpal_skills(ally):
    """Replace Alice's innate skills with Vorpal Blade skills.
    
    Saves the original skills to _alice_original_innate so they can be restored.
    Safe to call multiple times — only swaps if not already vorpal.
    """
    if ally.get("_heroine_key") != "alice":
        return

    # Already swapped
    if ally.get("_alice_vorpal_skills"):
        return

    # Save original innate skills
    ally["_alice_original_innate"] = list(ally.get("innate_skills", []))
    ally["innate_skills"] = list(_VORPAL_INNATE_SKILLS)
    ally["_alice_vorpal_skills"] = True

    # Clear cooldowns on skill swap
    ally["skill_cooldowns"] = {}


def revert_alice_to_normal_skills(ally):
    """Restore Alice's original innate skills, removing Vorpal Blade skills.

    Frabjous Day (the facility-upgrade skill) stays — it is a permanent
    reward owned by the blade-upgrade flag, not by the weapon being equipped.
    """
    if ally.get("_heroine_key") != "alice":
        return

    if not ally.get("_alice_vorpal_skills"):
        return

    original = ally.get("_alice_original_innate", _ALICE_NORMAL_INNATE)
    ally["innate_skills"] = list(original)
    ally["_alice_vorpal_skills"] = False
    ally.pop("_alice_original_innate", None)

    # Clear cooldowns on skill swap
    ally["skill_cooldowns"] = {}


def grant_vorpal_upgrade_skill(ally):
    """Grant Frabjous Day to Alice after Vorpal Blade upgrade.

    Adds it to the ``upgrade_skills`` category (does NOT consume a learned
    skill slot) so it persists through save/load.
    Only effective if Alice already has vorpal skills active.
    """
    if ally.get("_heroine_key") != "alice":
        return

    if not ally.get("_alice_vorpal_skills"):
        return

    upgrades = ally.setdefault("upgrade_skills", [])
    if _VORPAL_UPGRADE_SKILL not in upgrades:
        upgrades.append(_VORPAL_UPGRADE_SKILL)
    # Legacy placement cleanup (upgrade skills used to live in learned_skills)
    if _VORPAL_UPGRADE_SKILL in ally.get("learned_skills", []):
        ally["learned_skills"].remove(_VORPAL_UPGRADE_SKILL)

    ally["_alice_vorpal_upgraded"] = True


# ══════════════════════════════════════════════════════════════════════════════
# Grandmother's Axe — Red Hood Skill Swap System
# ══════════════════════════════════════════════════════════════════════════════

_REDHOOD_VORPAL_INNATE = ["what_big_teeth", "fell_the_wolf"]
_REDHOOD_UPGRADE_SKILL = HEROINE_UPGRADE_SKILLS["red_hood"]
_REDHOOD_NORMAL_INNATE = ["hunters_mark", "whats_in_the_basket"]


def swap_redhood_to_vorpal_skills(ally):
    """Replace Red Hood's innate skills with Grandmother's Axe skills."""
    if ally.get("_heroine_key") != "red_hood":
        return
    if ally.get("_redhood_vorpal_skills"):
        return
    ally["_redhood_original_innate"] = list(ally.get("innate_skills", []))
    ally["innate_skills"] = list(_REDHOOD_VORPAL_INNATE)
    ally["_redhood_vorpal_skills"] = True
    ally["skill_cooldowns"] = {}


def revert_redhood_to_normal_skills(ally):
    """Restore Red Hood's original innate skills.

    Through the Forest (the facility-upgrade skill) stays — it is a
    permanent reward owned by the axe-upgrade flag.
    """
    if ally.get("_heroine_key") != "red_hood":
        return
    if not ally.get("_redhood_vorpal_skills"):
        return
    original = ally.get("_redhood_original_innate", _REDHOOD_NORMAL_INNATE)
    ally["innate_skills"] = list(original)
    ally["_redhood_vorpal_skills"] = False
    ally.pop("_redhood_original_innate", None)
    ally["skill_cooldowns"] = {}


def grant_redhood_upgrade_skill(ally):
    """Grant Through the Forest to Red Hood after Grandmother's Axe upgrade.

    Adds it to the ``upgrade_skills`` category (does NOT consume a learned
    skill slot).
    """
    if ally.get("_heroine_key") != "red_hood":
        return
    if not ally.get("_redhood_vorpal_skills"):
        return
    upgrades = ally.setdefault("upgrade_skills", [])
    if _REDHOOD_UPGRADE_SKILL not in upgrades:
        upgrades.append(_REDHOOD_UPGRADE_SKILL)
    # Legacy placement cleanup (upgrade skills used to live in learned_skills)
    if _REDHOOD_UPGRADE_SKILL in ally.get("learned_skills", []):
        ally["learned_skills"].remove(_REDHOOD_UPGRADE_SKILL)
    ally["_redhood_vorpal_upgraded"] = True


# ══════════════════════════════════════════════════════════════════════════════
# Silver/Ruby Slippers — Dorothy Skill Swap System
# ══════════════════════════════════════════════════════════════════════════════

_DOROTHY_VORPAL_INNATE = ["cyclones_call", "heart_of_tin"]
_DOROTHY_UPGRADE_SKILL = HEROINE_UPGRADE_SKILLS["dorothy"]
_DOROTHY_NORMAL_INNATE = ["no_place_like_home", "ruby_blink"]


def swap_dorothy_to_vorpal_skills(ally):
    """Replace Dorothy's innate skills with Slippers skills."""
    if ally.get("_heroine_key") != "dorothy":
        return
    if ally.get("_dorothy_vorpal_skills"):
        return
    ally["_dorothy_original_innate"] = list(ally.get("innate_skills", []))
    ally["innate_skills"] = list(_DOROTHY_VORPAL_INNATE)
    ally["_dorothy_vorpal_skills"] = True
    ally["skill_cooldowns"] = {}


def revert_dorothy_to_normal_skills(ally):
    """Restore Dorothy's original innate skills.

    Emerald City's Light (the facility-upgrade skill) stays — it is a
    permanent reward owned by the slippers-upgrade flag.
    """
    if ally.get("_heroine_key") != "dorothy":
        return
    if not ally.get("_dorothy_vorpal_skills"):
        return
    original = ally.get("_dorothy_original_innate", _DOROTHY_NORMAL_INNATE)
    ally["innate_skills"] = list(original)
    ally["_dorothy_vorpal_skills"] = False
    ally.pop("_dorothy_original_innate", None)
    ally["skill_cooldowns"] = {}


def grant_dorothy_upgrade_skill(ally):
    """Grant Emerald City's Light to Dorothy after Ruby Slippers upgrade.

    Adds it to the ``upgrade_skills`` category (does NOT consume a learned
    skill slot).
    """
    if ally.get("_heroine_key") != "dorothy":
        return
    if not ally.get("_dorothy_vorpal_skills"):
        return
    upgrades = ally.setdefault("upgrade_skills", [])
    if _DOROTHY_UPGRADE_SKILL not in upgrades:
        upgrades.append(_DOROTHY_UPGRADE_SKILL)
    # Legacy placement cleanup (upgrade skills used to live in learned_skills)
    if _DOROTHY_UPGRADE_SKILL in ally.get("learned_skills", []):
        ally["learned_skills"].remove(_DOROTHY_UPGRADE_SKILL)
    ally["_dorothy_vorpal_upgraded"] = True
