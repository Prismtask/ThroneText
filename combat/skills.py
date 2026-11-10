from combat.combat_io import c_print, c_input, c_renders_menus
# combat/skills.py – Class Skill Definitions, Mastery & Execution
import random

from resources.skill_loader import PASSIVE_SKILLS, CLASS_SKILLS, PROFESSIONS
from combat.helpers import format_damage_msg, ACTION_CANCELLED_MSG, DamageResult
from utils import display_name


# ── Skill Queries ──────────────────────────────────────────────────────────

# Battle Loadout: max skills equipped for combat (the wave-2 ladder fills this
# at 9; the capstone is the first skill that must be swapped in).
MAX_SKILL_LOADOUT = 9


def get_class_skill_map(player):
    """Return the skill definition dict for the player's class.

    Includes the chosen profession's skills (Phase 3). Profession lockout is
    automatic: the unchosen branch is simply absent from this map, so it can
    never unlock, appear, or be used.
    """
    base = CLASS_SKILLS.get(player.get("class"), {})
    prof = player.get("profession")
    if not prof:
        return base
    prof_data = PROFESSIONS.get(player.get("class"), {}).get(prof)
    if not prof_data:
        return base
    merged = dict(base)
    merged.update(prof_data.get("skills", {}))
    return merged


def get_class_capstone_id(class_name):
    """Return the capstone skill id for a class (or None)."""
    for sid, sdef in CLASS_SKILLS.get(class_name, {}).items():
        if sdef.get("capstone"):
            return sid
    return None


def can_choose_profession(player):
    """True once the class capstone is known and no profession is chosen yet."""
    if player.get("profession"):
        return False
    cls = player.get("class")
    if cls not in PROFESSIONS:
        return False
    cap = get_class_capstone_id(cls)
    return bool(cap and cap in player.get("skills", []))


def get_equipped_skill_ids(player):
    """Return the skill ids currently equipped in the Battle Loadout.

    A missing `skill_loadout` key (legacy saves) means "everything unlocked";
    ids no longer unlocked are filtered out defensively.
    """
    unlocked = player.get("skills", [])
    loadout = player.get("skill_loadout")
    if loadout is None:
        return list(unlocked)
    return [sid for sid in loadout if sid in unlocked]


def get_available_skills(player):
    """Return list of (skill_id, skill_def) the player has unlocked, equipped
    in the Battle Loadout, and that is not on cooldown."""
    skill_map = get_class_skill_map(player)
    cooldowns = player.get("skill_cooldowns", {})
    level = player.get("level", 1)
    equipped = set(get_equipped_skill_ids(player))
    available = []
    for sid, sdef in skill_map.items():
        if sid in equipped and level >= sdef["unlock_level"] and cooldowns.get(sid, 0) <= 0:
            available.append((sid, sdef))
    return available


def get_all_unlocked_skills(player):
    """Return all unlocked skills (including those on cooldown).

    Deliberately NOT loadout-filtered — the Skill Book and Arcane Tower show
    every owned skill.
    """
    skill_map = get_class_skill_map(player)
    unlocked = player.get("skills", [])
    return [(sid, skill_map[sid]) for sid in unlocked if sid in skill_map]


def is_skill_available(player, skill_id):
    """Check if a specific skill is equipped and ready to use."""
    unlocked = player.get("skills", [])
    if skill_id not in unlocked:
        return False
    if skill_id not in get_equipped_skill_ids(player):
        return False
    cooldowns = player.get("skill_cooldowns", {})
    return cooldowns.get(skill_id, 0) <= 0


# ── Skill Unlocking ─────────────────────────────────────────────────────────

def unlock_skills_for_level(player):
    """Check if new skills should be unlocked based on current level.

    Also maintains the Battle Loadout: a missing loadout starts as "everything
    unlocked"; new skills auto-join while under the cap. When the cap is full,
    the skill still unlocks (Skill Book/mastery unaffected) but stays out of
    combat until equipped.
    """
    skill_map = get_class_skill_map(player)
    level = player.get("level", 1)
    unlocked = set(player.get("skills", []))
    newly_unlocked = []
    for sid, sdef in skill_map.items():
        if sid not in unlocked and level >= sdef["unlock_level"]:
            unlocked.add(sid)
            newly_unlocked.append(sid)
    if not newly_unlocked:
        return []
    player["skills"] = list(unlocked)

    # Battle Loadout auto-management (None = "all unlocked" back-compat)
    loadout = player.get("skill_loadout")
    if loadout is None:
        all_ids = [sid for sid in skill_map if sid in unlocked]
        if len(all_ids) > MAX_SKILL_LOADOUT:
            # Materialise: keep the assembled kit, queue later unlocks.
            loadout = all_ids[:MAX_SKILL_LOADOUT]
            player["skill_loadout"] = loadout
    if loadout is not None:
        loadout = [sid for sid in loadout if sid in unlocked]
        player["skill_loadout"] = loadout

    names = []
    for sid in newly_unlocked:
        name = skill_map[sid]["name"]
        if loadout is None or sid in loadout:
            names.append(name)
        elif len(loadout) < MAX_SKILL_LOADOUT:
            loadout.append(sid)
            names.append(name)
        else:
            names.append(f"{name} (battle loadout full — equip it at the Skill Book)")
    return names


def initialize_skills(player):
    """Set up skill-related fields on a new character."""
    player.setdefault("skills", [])
    player.setdefault("skill_cooldowns", {})
    player.setdefault("skill_mastery", {})
    player.setdefault("passive_unlocked", True)
    unlock_skills_for_level(player)


# ── Cooldown Management ───────────────────────────────────────────────────

def tick_skill_cooldowns(player):
    """Reduce all skill cooldowns by 1. Called each round end."""
    cooldowns = player.get("skill_cooldowns", {})
    for sid in list(cooldowns.keys()):
        cooldowns[sid] -= 1
        if cooldowns[sid] <= 0:
            del cooldowns[sid]


def set_skill_cooldown(player, skill_id):
    """Put a skill on cooldown after use.
    Returns an optional message if a cooldown_reduction buff was consumed."""
    # Death's Embrace — a kill marks the skill for a full cooldown refund.
    if player.pop("refund_cooldown_skill", None) == skill_id:
        return None
    from combat.weapon.wedding_specials import apply_wedding_skill_cooldown_skip
    if apply_wedding_skill_cooldown_skip(player, skill_id):
        return None
    skill_map = get_class_skill_map(player)
    if skill_id in skill_map:
        cooldown = skill_map[skill_id]["cooldown"]
        reduction_msg = None
        # Consume cooldown_reduction buff if present (e.g. from Haste)
        for buff in player.get("active_buffs", [])[:]:
            if buff.get("type") == "cooldown_reduction":
                reduction = buff.get("value", 0)
                cooldown = max(0, cooldown - reduction)
                player["active_buffs"].remove(buff)
                reduction_msg = f"Cooldown reduced by {reduction}!"
                break
        # Consume haste CD reduction
        from combat.status_effects import consume_haste_cd_reduction
        haste_cd = consume_haste_cd_reduction(player)
        if haste_cd > 0:
            cooldown = max(0, cooldown - haste_cd)
            if not reduction_msg:
                reduction_msg = f"Haste cooldown reduced by {haste_cd}!"
        # Pandemonium: Mana Drain curse increases cooldowns
        from pandemonium_curses import get_cooldown_increase
        cooldown += get_cooldown_increase(player)
        
        # Wonderland: White Rabbit's Haste reduces cooldowns
        from wonderland_curses import get_white_rabbit_cooldown_reduction
        cooldown = max(0, cooldown - get_white_rabbit_cooldown_reduction(player))
        
        # Arcane Blessing: Mana Attunement reduces cooldowns
        from facilities.arcane_tower import get_arcane_cooldown_reduction
        cooldown = max(0, cooldown - get_arcane_cooldown_reduction(player))
        
        # Event Horizon — The High Priestess: skill cooldowns −2 turns
        if player.get("_eh_joker_priestess"):
            cooldown = max(0, cooldown - 2)
            if not reduction_msg:
                reduction_msg = "The High Priestess hastens your recovery (−2 turns)."
        player.setdefault("skill_cooldowns", {})[skill_id] = cooldown
        return reduction_msg
    return None


def reduce_all_cooldowns(player, amount):
    """Reduce all skill cooldowns by a given amount."""
    cooldowns = player.get("skill_cooldowns", {})
    for sid in list(cooldowns.keys()):
        cooldowns[sid] -= amount
        if cooldowns[sid] <= 0:
            del cooldowns[sid]


# ── Skill Mastery ───────────────────────────────────────────────────────────

# Mastery thresholds (number of uses) for levels ★ / ★★ / ★★★ / ✦ / ✦✦.
# Levels ★-★★★ keep their original pacing for save compatibility.
MASTERY_THRESHOLDS = [10, 25, 50, 90, 150]
MASTERY_MAX_LEVEL = len(MASTERY_THRESHOLDS)


def get_skill_mastery_level(player, skill_id):
    """Return the mastery level of a skill (0-5)."""
    uses = player.get("skill_mastery", {}).get(skill_id, 0)
    level = 0
    for threshold in MASTERY_THRESHOLDS:
        if uses >= threshold:
            level += 1
    return level


def get_mastery_bonuses(skill_id, mastery_level):
    """Return bonus multipliers based on mastery level (0-5).

    ★★★  unlocks the per-skill "extra effect" flag and boosts status potency.
    ✦ (mastery 4) adds a +1-turn duration bonus to effect skills.
    ✦✦ (mastery 5) raises power/status again and brings total cooldown reduction to -2.
    """
    bonuses = {
        "power_mult": 1.0,
        "cooldown_reduction": 0,
        "extra_effect": False,
        "duration_bonus": 0,
        "status_mult": 1.0,
    }
    if mastery_level >= 1:
        bonuses["power_mult"] = 1.15
    if mastery_level >= 2:
        bonuses["cooldown_reduction"] = 1
    if mastery_level >= 3:
        bonuses["power_mult"] = 1.30
        bonuses["extra_effect"] = True
        bonuses["status_mult"] = 1.5
    if mastery_level >= 4:
        bonuses["power_mult"] = 1.45
        bonuses["duration_bonus"] = 1
        bonuses["status_mult"] = 1.75
    if mastery_level >= 5:
        bonuses["power_mult"] = 1.60
        bonuses["cooldown_reduction"] = 2
        bonuses["status_mult"] = 2.0
    return bonuses


def add_skill_mastery_xp(player, skill_id):
    """Increment skill use count for mastery progression."""
    player.setdefault("skill_mastery", {})
    old_level = get_skill_mastery_level(player, skill_id)
    player["skill_mastery"][skill_id] = player["skill_mastery"].get(skill_id, 0) + 1
    new_level = get_skill_mastery_level(player, skill_id)
    if new_level > old_level:
        return new_level
    return None


def format_mastery_label(skill_id, player):
    """Return a mastery label string for display.

    Display: ★ / ★★ / ★★★ for levels 1-3, then ✦ (4) and ✦✦ (5).
    """
    level = get_skill_mastery_level(player, skill_id)
    labels = ["", "★", "★★", "★★★", "✦", "✦✦"]
    return labels[level]


# ── Passive Skill Application ─────────────────────────────────────────────

def get_passive_skill(player):
    """Return the passive skill dict for the player, or None.

    A chosen profession replaces the class passive with its upgraded version.
    """
    if not player.get("passive_unlocked", True):
        return None
    prof = player.get("profession")
    if prof:
        prof_data = PROFESSIONS.get(player.get("class"), {}).get(prof)
        if prof_data and prof_data.get("passive"):
            return prof_data["passive"]
    return PASSIVE_SKILLS.get(player.get("class"))


def get_player_passive_effects(player):
    """Return the passive's effects as a list (upgraded passives have several)."""
    passive = get_passive_skill(player)
    if not passive:
        return []
    effects = passive.get("effects")
    if effects:
        return list(effects)
    effect = passive.get("effect")
    return [effect] if effect else []


def _sum_passive_effect(player, effect_type, key="value"):
    total = 0.0
    for effect in get_player_passive_effects(player):
        if effect.get("type") == effect_type:
            total += effect.get(key, 0)
    return total


def get_player_passive_crit_bonus(player):
    """Crit chance from the class/profession passive (0 when none)."""
    if player.get("is_ally") or not player.get("class"):
        return 0.0
    return _sum_passive_effect(player, "crit_chance")


def get_player_passive_evasion(player):
    """Evasion from the class/profession passive (0 when none)."""
    if player.get("is_ally") or not player.get("class"):
        return 0.0
    return _sum_passive_effect(player, "evasion")


def get_player_passive_elem_bonus(player, element):
    """Elemental damage bonus from the passive (all-element or element-listed)."""
    if player.get("is_ally") or not player.get("class"):
        return 0.0
    total = 0.0
    for effect in get_player_passive_effects(player):
        if effect.get("type") != "elemental":
            continue
        elements = effect.get("elements")
        if not elements or element in elements:
            total += effect.get("value", 0)
    return total


def get_player_passive_low_hp_mult(player):
    """Damage multiplier from low-HP passives (Berserker's Pain Fury)."""
    if player.get("is_ally") or not player.get("class"):
        return 1.0
    for effect in get_player_passive_effects(player):
        if effect.get("type") != "low_hp_damage":
            continue
        from character import player_max_hp
        max_hp = player_max_hp(player)
        if max_hp > 0 and player.get("current_hp", 0) <= max_hp * effect.get("threshold", 0.50):
            return 1.0 + effect.get("value", 0)
    return 1.0


def apply_profession_battle_start(player):
    """Apply once-per-battle profession passives (start-CD, regen)."""
    for effect in get_player_passive_effects(player):
        etype = effect.get("type")
        if etype == "combat_start_cd":
            reduce_all_cooldowns(player, effect.get("value", 1))
        elif etype == "regen_percent":
            player.setdefault("active_buffs", []).append({
                "type": "regen_pct", "value": effect.get("value", 0.03),
                "remaining": 999, "source": "profession_passive"
            })


def _reduce_cooldowns_for(actor, amount):
    """Reduce one actor's (player or ally) skill cooldowns by `amount`."""
    if actor is None or amount <= 0:
        return
    cooldowns = actor.get("skill_cooldowns", {})
    for key in list(cooldowns.keys()):
        cooldowns[key] = max(0, cooldowns[key] - amount)


def _cleanse_debuffs_for(entity):
    """Remove all cleansable debuffs from an entity (player or ally)."""
    from combat.status_effects import is_cleansable
    from combat.ally_skills import _clear_flat_debuff_flag
    debuffs = entity.get("active_debuffs", [])
    if not debuffs:
        return 0
    kept = [d for d in debuffs if not is_cleansable(d)]
    removed = len(debuffs) - len(kept)
    for d in debuffs:
        if is_cleansable(d):
            _clear_flat_debuff_flag(entity, d.get("type"))
    entity["active_debuffs"] = kept
    return removed


def apply_passive_to_damage_taken(player, damage):
    """Apply passive damage reduction (summed across effects; capped at 80%)."""
    reduction = _sum_passive_effect(player, "damage_reduction")
    if reduction <= 0:
        return damage
    return int(damage * (1 - min(reduction, 0.80)))


def get_passive_heal_bonus(player):
    """Return heal multiplier from passive."""
    return 1.0 + _sum_passive_effect(player, "heal_bonus")


def get_passive_life_steal(player):
    """Return life steal percentage from passive and temporary effects."""
    # Bloodlust (Barbarian skill) - 50% life steal
    if player.get("bloodlust_turns", 0) > 0:
        return 0.50
    return _sum_passive_effect(player, "life_steal")


# ── Skill Execution ───────────────────────────────────────────────────────

def execute_skill(player, skill_id, enemies, p_str, p_con, p_dex, p_ler, p_wis, p_cha, allies=None):
    """Execute a skill and return (result_message, victory).

    Wrapper around the core engine. Effect-only skills (heals, buffs,
    barriers, revives) early-return from the core, so mastery XP is awarded
    here for every successful cast rather than only on damage paths.
    """
    if skill_id not in get_class_skill_map(player):
        return "That skill does not exist.", False
    msg, victory = _execute_skill_core(
        player, skill_id, enemies, p_str, p_con, p_dex, p_ler, p_wis, p_cha, allies
    )
    if msg == ACTION_CANCELLED_MSG:
        return msg, victory
    mastery_upgrade = add_skill_mastery_xp(player, skill_id)
    if mastery_upgrade:
        msg = f"{msg} Skill Mastery increased to Level {mastery_upgrade}! ★"
    return msg, victory


def _execute_skill_core(player, skill_id, enemies, p_str, p_con, p_dex, p_ler, p_wis, p_cha, allies=None):
    """
    Execute a skill and return (result_message, victory).
    victory is True if all enemies were defeated.
    """
    from character import player_max_hp
    from combat.status_effects import apply_poison

    skill_map = get_class_skill_map(player)
    skill = skill_map.get(skill_id)
    if not skill:
        return "That skill does not exist.", False

    target_type = skill.get("target", "enemy")
    power_type = skill.get("power_type", "str")
    base_power = skill.get("base_power", 0)

    # Apply mastery bonuses
    mastery = get_skill_mastery_level(player, skill_id)
    bonuses = get_mastery_bonuses(skill_id, mastery)
    power_mult = bonuses["power_mult"]
    cd_reduction = bonuses["cooldown_reduction"]
    extra_effect = bonuses["extra_effect"]
    duration_bonus = bonuses["duration_bonus"]
    status_mult = bonuses["status_mult"]

    def _scaled_value(base):
        """Scale a support magnitude by the mastery status multiplier (ints round half-up)."""
        if isinstance(base, int):
            return int(base * status_mult + 0.5) if base >= 0 else int(base * status_mult - 0.5)
        return base * status_mult

    # Flat stat buffs scale with the holder's level plus a small baseline bonus.
    from combat.stats import scaled_stat_buff_value as _scale_stat_buff

    # Burn skills upgrade their burn TIER instead of multiplying damage:
    # +1 tier at ★3, +1 more at ✦✦ (capped at tier 5 / Conflagration).
    burn_tier_bonus = (1 if mastery >= 3 else 0) + (1 if mastery >= 5 else 0)

    # Map power type to stat value
    stat_map = {
        "str": p_str, "con": p_con, "dex": p_dex,
        "ler": p_ler, "wis": p_wis, "cha": p_cha,
        "Strength": p_str, "Constitution": p_con, "Dexterity": p_dex,
        "Learning": p_ler, "Wisdom": p_wis, "Charisma": p_cha,
    }
    scaling = stat_map.get(power_type, 0)
    # Add Learning as a secondary scaling to all outgoing skill damage
    scaling += p_ler // 2

    msg_parts = []
    victory = False
    # Snapshot enemy HP so Sky Piercer can detect which enemies this skill damaged
    pre_hp = [e["hp"] for e in enemies]

    # ── Target Selection Helpers ──
    def _pick_enemy_target():
        if len(enemies) == 1:
            return enemies[0]
        try:
            choice = int(c_input("Select target number: ")) - 1
            if 0 <= choice < len(enemies):
                return enemies[choice]
        except ValueError:
            pass
        return None

    def _pick_ally_target(allow_dead=False):
        party = [player] + (allies or [])
        if allow_dead:
            alive = party
        else:
            alive = [m for m in party if m.get("current_hp", 1) > 0]
        if len(alive) == 1:
            return alive[0]
        c_print("Select target:")
        # The header stays (the GUI uses it to detect ally targeting), but the
        # numbered roster is redundant — the HUD shows ally cards + badges.
        if not c_renders_menus():
            for i, m in enumerate(alive):
                name = m.get("name", "You") if m is player else m.get("name", "Ally")
                hp = m.get("current_hp", 0)
                max_hp = m.get("max_hp", player_max_hp(m) if m is player else m.get("max_hp", hp))
                status = " [FALLEN]" if m.get("current_hp", 1) <= 0 else ""
                c_print(f"  {i+1}. {name} ({hp}/{max_hp}){status}")
        try:
            choice = int(c_input("Choice: ")) - 1
            if 0 <= choice < len(alive):
                return alive[choice]
        except ValueError:
            pass
        return None

    def _pick_dead_ally():
        party = [player] + (allies or [])
        dead = [m for m in party if m.get("current_hp", 1) <= 0]
        if not dead:
            return None
        if len(dead) == 1:
            return dead[0]
        c_print("Select fallen ally to revive:")
        # Header kept ("select fallen" drives the GUI revive-target mode);
        # the roster is drawn as party cards with badges instead.
        if not c_renders_menus():
            for i, m in enumerate(dead):
                name = m.get("name", "You") if m is player else m.get("name", "Ally")
                max_hp = m.get("max_hp", player_max_hp(m) if m is player else m.get("max_hp", 1))
                c_print(f"  {i+1}. {name} (will revive at {int(max_hp * 0.5)} HP)")
        try:
            choice = int(c_input("Choice: ")) - 1
            if 0 <= choice < len(dead):
                return dead[choice]
        except ValueError:
            pass
        return None

    # ── Damage Helper ──
    # Percentage damage buffs stack additively: 1.00 + power_buff + every
    # damage_boost. The multiplier is captured once on the first damaging hit;
    # power_buff is consumed there and every hit of the action benefits.
    # Non-damaging skills never reach this helper, so the buff waits.
    _damage_buff_mult = 1.0
    _damage_buff_checked = False
    # Chance and Choice: one coin roll per action (all hits share it)
    _cac_state = {"rolled": False, "mult": 1.0}

    def _calc_dmg(target, power, ignore_armor=False, element=None, guaranteed_crit=False):
        nonlocal _damage_buff_mult, _damage_buff_checked
        from combat.stats import roll_skill_dodge
        if roll_skill_dodge(target):
            msg_parts.append(f"  💨 {target['name']} reads the strike and slips aside!")
            return DamageResult(0, False)
        # Event Horizon: The Fool — a 10% chance the skill simply fails
        from event_horizon import joker_attack_missed
        if joker_attack_missed(player):
            return DamageResult(0, False)
        if not _damage_buff_checked:
            _damage_buff_checked = True
            from combat.status_effects import get_damage_buff_multiplier
            _damage_buff_mult = get_damage_buff_multiplier(
                player, consume_power_buff=True, messages=msg_parts
            )
        armor = 0 if ignore_armor else target.get("con_mod", 0)
        # Apply sunder debuff reduction to armor
        for debuff in target.get("active_debuffs", []):
            if debuff.get("type") == "sunder":
                armor = max(0, armor - debuff.get("value", 0))
            elif debuff.get("type") == "curse" and "Constitution" in debuff.get("stats", []):
                armor = max(0, armor - debuff.get("penalty", 0))
        # Form tradition armour penetration (Sundering)
        if armor > 0:
            from combat.form_perks import get_armor_pen_multiplier
            armor = int(armor * get_armor_pen_multiplier(player))
        # Apply Strength milestone bonus
        from combat.stat_milestones import get_strength_bonus
        power = power + get_strength_bonus(player)
        # Percentage damage buffs (power_buff + damage_boost) stack additively.
        if _damage_buff_mult != 1.0:
            power = int(power * _damage_buff_mult)
        # Profession passive: bonus damage below a HP threshold (Berserker)
        lp_mult = get_player_passive_low_hp_mult(player)
        if lp_mult != 1.0:
            power = int(power * lp_mult)
        # Event Horizon: The Hierophant — skills deal +25%
        from event_horizon import joker_damage_multiplier
        power = int(power * joker_damage_multiplier(player, "skill"))
        # Random critical hit (skip if skill already guarantees a crit).
        # Skill crit_bonus feeds the roll; chance over the cap adds crit damage.
        if not guaranteed_crit:
            from combat.stats import roll_critical_hit, apply_critical_damage, CRIT_MULTIPLIER
            crit_bonus = skill.get("crit_bonus", 0)
            crit_mult = skill.get("crit_mult", CRIT_MULTIPLIER)
            is_crit, _, overflow_crit = roll_critical_hit(player, "player", bonus=crit_bonus)
            if is_crit:
                power = apply_critical_damage(power, True, multiplier=crit_mult + overflow_crit)
                msg_parts.append("Critical hit!")
        else:
            is_crit = True
        # Event Horizon: The Sun — crits +30%, non-crits ×0.85
        from event_horizon import joker_crit_modifier
        power = joker_crit_modifier(player, is_crit, power)
        dmg = max(1, power - armor)
        # Apply elemental damage — read from YAML skill definition
        if element is None:
            element = skill.get("elemental")
        if element:
            from combat.elemental import calculate_elemental_damage
            dmg = calculate_elemental_damage(dmg, player, target, element)
        # Apply Hunter's Mark damage bonus (Hawk's Eye buff boosts the mark)
        if target.get("hunters_mark"):
            bonus = target.get("hunters_mark_bonus", 0.50)
            for buff in player.get("active_buffs", []):
                if buff.get("type") == "mark_damage_bonus":
                    bonus += buff.get("value", 0)
            dmg = int(dmg * (1 + bonus))
        # Prescript Ledger — clash empowerment vs the Prescript's Target
        from combat.weapon.prescript_ledger import get_clash_bonus as get_prescript_clash_bonus
        prescript_clash = get_prescript_clash_bonus(player, target)
        if prescript_clash:
            dmg = int(dmg * (1 + prescript_clash))
        # Damage-taken amplification (e.g. Aura of Despair)
        from combat.status_effects import get_damage_taken_multiplier
        dt_mult = get_damage_taken_multiplier(target)
        if dt_mult != 1.0:
            dmg = int(dmg * dt_mult)
        # Wedding accessory attack bonuses + on-hit — skills count as attacks
        # (same hooks as the basic-attack path; 2026-10-04).
        from combat.weapon.wedding_specials import (apply_wedding_attack_bonus_procs,
                                                    apply_wedding_on_hit)
        is_first = not player.get("wedding_first_attack_done")
        dmg += apply_wedding_attack_bonus_procs(player, target, dmg, is_first)
        dmg = max(0, dmg)
        # Pandemonium: Weakened Resolve curse — skills deal less damage too
        from pandemonium_curses import apply_damage_dealt_multiplier
        dmg = apply_damage_dealt_multiplier(player, dmg)
        # Event Horizon trophies: Old Dopo Robe + Chance and Choice
        from combat.weapon.dopo_robe import get_robe_multiplier
        dmg = int(dmg * get_robe_multiplier(player, player))
        from combat.weapon.chance_and_choice import apply_chance_and_choice
        dmg = apply_chance_and_choice(player, dmg, _cac_state)
        # Form tradition (Cleaving / Focused)
        from combat.form_perks import get_outgoing_damage_multiplier
        dmg = int(dmg * get_outgoing_damage_multiplier(player))
        # Deed titles: small player-only outgoing-damage bonus.
        from titles import mod as _title_mod
        _title_dmg = _title_mod(player, "damage_pct")
        if _title_dmg:
            dmg = int(dmg * (1.0 + _title_dmg))
        apply_wedding_on_hit(player, target, enemies, dmg)
        player["wedding_first_attack_done"] = True
        return DamageResult(dmg, is_crit)

    # ── Life Steal Helper ──
    def _apply_life_steal(damage_dealt):
        ls = get_passive_life_steal(player)
        if ls > 0 and damage_dealt > 0:
            heal = int(damage_dealt * ls)
            if heal > 0:
                from combat.status_effects import apply_healing
                actual = apply_healing(player, heal, source=player)
                if actual < 0:
                    msg_parts.append(f"[Soul Siphon] The void twists the healing! You take {-actual} damage!")
                elif actual > 0:
                    msg_parts.append(f"[Soul Siphon] You recover {actual} HP.")
        _eh_ls = player.get("_eh_joker_lifesteal", 0) or 0
        if _eh_ls > 0 and damage_dealt > 0:
            heal = int(damage_dealt * _eh_ls)
            if heal > 0:
                from combat.status_effects import apply_healing as _eh_heal_fn
                actual = _eh_heal_fn(player, heal, source=player)
                if actual < 0:
                    msg_parts.append(f"[Death] The void twists the drain! You take {-actual} damage!")
                elif actual > 0:
                    msg_parts.append(f"[Death] You drain {actual} HP from the wound.")

    # ── Generic on-hit statuses (YAML-driven, for skills without a bespoke branch) ──
    def _apply_on_hit_effects(target):
        """Apply a skill's YAML status keys to a struck target."""
        from combat.status_effects import (
            apply_slow_to_enemy, check_status_resisted, apply_weaken,
            apply_burn, damage_to_burn_tier, apply_poison, apply_bleed,
            apply_damage_taken_up, apply_healing,
        )
        # Slow
        if skill.get("apply_slow"):
            if apply_slow_to_enemy(target, duration=3 + duration_bonus) != "resisted":
                msg_parts.append(f"{target['name']} is slowed!")
        # Stun
        if skill.get("stun_chance") and random.random() < skill["stun_chance"]:
            if check_status_resisted(target):
                msg_parts.append(f"{target['name']} shrugs off the stun!")
            else:
                target["stunned"] = True
                msg_parts.append(f"{target['name']} is stunned!")
        # Weaken
        if skill.get("apply_weaken"):
            if apply_weaken(target, duration=3 + duration_bonus) != "resisted":
                msg_parts.append(f"{target['name']} is weakened!")
        # Burn (mastery upgrades the tier: +1 at ★3, +1 more at ✦✦)
        if skill.get("burn_damage"):
            b_tier = min(5, damage_to_burn_tier(skill["burn_damage"]) + burn_tier_bonus)
            if apply_burn(target, b_tier, skill.get("burn_duration", 3)) != "resisted":
                msg_parts.append(f"{target['name']} is set ablaze!")
        # Poison
        if skill.get("poison_damage"):
            p_dmg = skill["poison_damage"]
            if status_mult > 1:
                p_dmg = int(p_dmg * status_mult)
            if apply_poison(target, p_dmg, skill.get("poison_duration", 3)) != "resisted":
                msg_parts.append(f"{target['name']} is poisoned!")
        # Bleed
        if skill.get("bleed_damage"):
            b_dmg = skill["bleed_damage"]
            if status_mult > 1:
                b_dmg = int(b_dmg * status_mult)
            result = apply_bleed(target, b_dmg, skill.get("bleed_duration", 4), source=skill_id)
            if result in ("applied", "refreshed", "stacked"):
                msg_parts.append(f"{target['name']} is bleeding!")
        # Sunder
        if skill.get("apply_sunder"):
            if check_status_resisted(target):
                msg_parts.append(f"{target['name']} shrugs off the armor break!")
            else:
                target.setdefault("active_debuffs", []).append({
                    "type": "sunder", "value": skill.get("sunder_value", 3),
                    "remaining": skill.get("sunder_duration", 3) + duration_bonus
                })
                msg_parts.append(f"{target['name']}'s armor is sundered!")
        # Blind
        if skill.get("apply_blind"):
            if check_status_resisted(target):
                msg_parts.append(f"{target['name']} shrugs off the blinding light!")
            else:
                target["blinded"] = True
                target.setdefault("active_debuffs", []).append({
                    "type": "blind", "value": 0.40,
                    "remaining": skill.get("blind_duration", 2) + duration_bonus
                })
                msg_parts.append(f"{target['name']} is blinded!")
        # Self vulnerability (Reckless Charge)
        if skill.get("self_vulnerable"):
            vuln_pct = skill["self_vulnerable"] * status_mult
            player.setdefault("active_debuffs", []).append({
                "type": "vulnerable", "value": vuln_pct,
                "remaining": skill.get("self_vulnerable_duration", 2) + duration_bonus,
                "source": skill_id
            })
            msg_parts.append(f"You leave yourself open! ({int(vuln_pct * 100)}% more damage taken.)")
        # Outgoing damage-taken debuff (Verdict, Condemn)
        if skill.get("apply_damage_taken_up"):
            val = skill["apply_damage_taken_up"] * status_mult
            if check_status_resisted(target):
                msg_parts.append(f"{target['name']} resists the brand!")
            else:
                apply_damage_taken_up(target, val, skill.get("damage_taken_up_duration", 3) + duration_bonus)
                msg_parts.append(f"{target['name']} is branded — it takes {int(val * 100)}% more damage!")
        # Self heal on hit (Juggernaut)
        if skill.get("self_heal_percent"):
            max_hp = player_max_hp(player)
            healed = apply_healing(player, int(max_hp * skill["self_heal_percent"]), source=player)
            if healed > 0:
                msg_parts.append(f"You steady yourself — {healed} HP recovered.")

    # ── Special Skills (non-damage) ──

    # Smoke Bomb
    if skill_id == "rog_smoke":
        from combat.status_effects import check_status_resisted
        resisted_names = []
        for e in enemies:
            if check_status_resisted(e):
                resisted_names.append(e["name"])
                continue
            e["blinded"] = True
            e.setdefault("active_debuffs", []).append({
                "type": "blind", "remaining": 3 + duration_bonus
            })
        player["smoke_bomb_flee"] = True
        smoke_msg = "You vanish in a cloud of smoke! Enemies are blinded, and your next escape is guaranteed."
        if resisted_names:
            smoke_msg += f" ({', '.join(resisted_names)} shrug off the smoke.)"
        return smoke_msg, False

    # Battle Cry
    if skill_id == "war_battlecry":
        val = _scaled_value(_scale_stat_buff(2, player))
        dur = 3 + duration_bonus
        player.setdefault("active_buffs", []).append({
            "stat": "Strength", "value": val, "remaining": dur, "source": "battle_cry"
        })
        player.setdefault("active_buffs", []).append({
            "stat": "Constitution", "value": val, "remaining": dur, "source": "battle_cry"
        })
        return f"You let out a thunderous battle cry! Strength +{val}, Constitution +{val} for {dur} turns!", False

    # Divine Shield
    if skill_id == "clr_shield":
        duration = (3 if extra_effect else 2) + duration_bonus
        player.setdefault("active_buffs", []).append({
            "type": "divine_shield", "remaining": duration, "source": "divine_shield"
        })
        return f"A radiant shield envelops you! You are immune to damage for {duration} turns.", False

    # Feral Rage
    if skill_id == "bar_rage":
        val = _scaled_value(_scale_stat_buff(3, player))
        dur = 3 + duration_bonus
        vuln_pct = 0.20 * status_mult
        player.setdefault("active_buffs", []).append({
            "stat": "Strength", "value": val, "remaining": dur, "source": "feral_rage"
        })
        player.setdefault("active_debuffs", []).append({
            "type": "vulnerable", "value": vuln_pct, "remaining": dur, "source": "feral_rage"
        })
        return f"You enter a feral rage! Strength +{val}, but you take {int(vuln_pct * 100)}% more damage for {dur} turns.", False

    # Berserk
    if skill_id == "bar_berserk":
        dur = 3 + duration_bonus
        player["berserk_turns"] = dur
        return f"You go berserk! You will attack twice per turn for {dur} turns!", False

    # Dark Curse
    if skill_id == "lck_curse":
        target = _pick_enemy_target()
        if not target:
            return ACTION_CANCELLED_MSG, False
        penalty = _scaled_value(2)
        dur = 3 + duration_bonus
        from combat.status_effects import check_status_resisted
        if check_status_resisted(target):
            return f"The {target['name']} shrugs off your curse!", False
        target.setdefault("active_debuffs", []).append({
            "type": "curse", "penalty": penalty, "remaining": dur, "stats": ["Strength", "Constitution"]
        })
        return f"You curse the {target['name']}! Its Strength and Constitution are reduced by {penalty} for {dur} turns.", False

    # Hunter's Mark
    if skill_id == "rng_mark":
        target = _pick_enemy_target()
        if not target:
            return ACTION_CANCELLED_MSG, False
        bonus = 0.50 * status_mult
        target["hunters_mark"] = True
        target["hunters_mark_bonus"] = bonus
        target["hunters_mark_source"] = player.get("name", "Ranger")
        dur = 3 + duration_bonus
        target["hunters_mark_turns"] = dur
        return f"You mark the {target['name']}! Your attacks against it deal +{int(bonus*100)}% damage for {dur} turns.", False

    # Heal
    if skill_id == "clr_heal":
        target = _pick_ally_target()
        if not target:
            return ACTION_CANCELLED_MSG, False
        from combat.stat_milestones import get_wisdom_bonus
        heal = int((base_power + scaling) * power_mult * get_passive_heal_bonus(player)) + get_wisdom_bonus(player)
        from combat.status_effects import apply_healing
        name = "You" if target is player else display_name(target)
        mastery_msg = f" [{format_mastery_label(skill_id, player)}]" if mastery > 0 else ""
        from combat.ally_skills import is_heal_blocked
        if is_heal_blocked(target, player):
            return f"{name}'s Unholy Resilience rejects allied healing!{mastery_msg}", False
        actual = apply_healing(target, heal, source=player)
        if actual < 0:
            return f"The void twists the healing! {name} takes {-actual} damage instead!{mastery_msg}", False
        return f"{name} is healed for {actual} HP!{mastery_msg}", False

    # Lay on Hands
    if skill_id == "pal_layhands":
        target = _pick_ally_target()
        if not target:
            return ACTION_CANCELLED_MSG, False
        max_hp = player_max_hp(target) if target is player else target.get("max_hp", target.get("current_hp", 1))
        old_hp = target.get("current_hp", 0)
        target["current_hp"] = max_hp
        name = "You" if target is player else display_name(target)
        return f"{name} is fully restored to {max_hp} HP!", False

    # Mass Heal
    if skill_id == "clr_mass_heal":
        party = [player] + (allies or [])
        from combat.stat_milestones import get_wisdom_bonus
        heal = int((base_power + scaling) * power_mult * get_passive_heal_bonus(player)) + get_wisdom_bonus(player)
        from combat.status_effects import apply_healing
        total_healed = 0
        from combat.ally_skills import is_heal_blocked
        for member in party:
            if member.get("current_hp", 0) <= 0:
                continue
            if is_heal_blocked(member, player):
                continue
            actual = apply_healing(member, heal, source=player)
            total_healed += max(0, actual)
        return f"Divine light washes over the party! Total healing: {total_healed} HP.", False

    # Resurrection
    if skill_id == "clr_resurrection":
        target = _pick_dead_ally()
        if not target:
            return ACTION_CANCELLED_MSG, False
        max_hp = player_max_hp(target) if target is player else target.get("max_hp", 1)
        revive_hp = int(max_hp * skill.get("revive_percent", 0.50))
        target["current_hp"] = revive_hp
        if target is not player:
            # Clear the defeated flag so the revived ally actually rejoins combat.
            target["defeated"] = False
        name = "You" if target is player else display_name(target)
        return f"{name} is resurrected with {revive_hp} HP!", False

    # Second Wind
    if skill_id == "war_second_wind":
        max_hp = player_max_hp(player)
        heal = int(max_hp * skill.get("heal_percent", 0.25))
        from combat.stat_milestones import get_wisdom_bonus
        heal = heal + get_wisdom_bonus(player)
        from combat.status_effects import apply_healing
        actual = apply_healing(player, heal, source=player)
        if actual < 0:
            return f"The void twists your second wind! You take {-actual} damage instead!", False
        return f"You catch your second wind, recovering {actual} HP!", False

    # Time Warp
    if skill_id == "mage_timewarp":
        amount = skill.get("cooldown_reduction", 2)
        reduce_all_cooldowns(player, amount)
        if skill.get("free_action"):
            player["_skill_free_action"] = True
        return f"Time bends around you! All skill cooldowns reduced by {amount} turns — you act again!", False

    # Haste — grant an ally cooldown reduction on their next skill use
    if skill_id == "haste":
        target = _pick_ally_target()
        if not target:
            return ACTION_CANCELLED_MSG, False
        effect = skill.get("effect", {})
        cd_val = _scaled_value(effect.get("value", 2))
        duration = effect.get("duration", 2) + duration_bonus
        target.setdefault("active_buffs", []).append({
            "type": "cooldown_reduction", "value": cd_val, "remaining": duration
        })
        target_name = "You" if target is player else display_name(target)
        mastery_msg = f" [{format_mastery_label(skill_id, player)}]" if mastery > 0 else ""
        return f"{target_name} is hastened! Next skill cooldown reduced by {cd_val} for {duration} turns.{mastery_msg}", False

    # Dark Empowerment
    if skill_id == "lck_empower":
        val = _scaled_value(_scale_stat_buff(3, player))
        dur = 3 + duration_bonus
        player.setdefault("active_buffs", []).append({
            "stat": "Learning", "value": val, "remaining": dur, "source": "dark_empowerment"
        })
        player.setdefault("active_buffs", []).append({
            "stat": "Charisma", "value": val, "remaining": dur, "source": "dark_empowerment"
        })
        return f"Dark energies surge through you! Learning +{val}, Charisma +{val} for {dur} turns!", False

    # Bloodlust
    if skill_id == "bar_bloodlust":
        dur = skill.get("bloodlust_duration", 3) + duration_bonus
        player["bloodlust_turns"] = dur
        return f"You thirst for blood! You will heal for 50% of damage dealt for {dur} turns!", False

    # Bastion of Light
    if skill_id == "pal_bastion":
        party = [player] + (allies or [])
        dur = skill.get("buff_duration", 3) + duration_bonus
        for member in party:
            member.setdefault("active_buffs", []).append({
                "type": "defense",
                "value": skill.get("defense_buff", 3),
                "remaining": dur
            })
        return f"A bastion of light shields the entire party! Defense buff for {dur} turns.", False

    # Soul Fear
    if skill_id == "lck_fear":
        from combat.status_effects import check_status_resisted
        dur = skill.get("fear_duration", 3) + duration_bonus
        fear_val = skill.get("fear_value", 0.20) * status_mult
        resisted_fear = 0
        for e in enemies:
            if check_status_resisted(e):
                resisted_fear += 1
                continue
            e.setdefault("active_debuffs", []).append({
                "type": "fear",
                "value": fear_val,
                "remaining": dur
            })
        fear_msg = f"You unleash a wave of terror! All enemies deal {int(fear_val * 100)}% less damage for {dur} turns."
        if resisted_fear:
            fear_msg += f" ({resisted_fear} resist{'s' if resisted_fear == 1 else ''} the terror.)"
        return fear_msg, False

    # ── Wave 2 skills (Lv 20/26/32) — non-damage ──

    # War Banner
    if skill_id == "war_banner":
        party = [player] + (allies or [])
        val = _scaled_value(_scale_stat_buff(2, player))
        regen_pct = 0.03 * status_mult
        dur = 3 + duration_bonus
        for member in party:
            if member.get("current_hp", 0) <= 0:
                continue
            member.setdefault("active_buffs", []).append({
                "stat": "Strength", "value": val, "remaining": dur, "source": "war_banner"
            })
            member.setdefault("active_buffs", []).append({
                "type": "regen_pct", "value": regen_pct, "remaining": dur, "source": "war_banner"
            })
        return f"You plant the war banner! Party Strength +{val} and {int(regen_pct * 100)}% HP regen for {dur} turns.", False

    # Elemental Focus
    if skill_id == "mage_elemental_focus":
        val = 0.15 * status_mult
        dur = 3 + duration_bonus
        player.setdefault("active_buffs", []).append({
            "type": "elemental_dmg", "value": val, "remaining": dur, "source": "elemental_focus"
        })
        return f"Elemental energies coalesce around you! +{int(val * 100)}% elemental damage for {dur} turns.", False

    # Perfect Opening
    if skill_id == "rog_perfect_opening":
        crit = 0.12 * status_mult
        crit_dmg = 0.25 * status_mult
        dur = 3 + duration_bonus
        player.setdefault("active_buffs", []).append({
            "type": "crit_chance", "value": crit, "remaining": dur, "source": "perfect_opening"
        })
        player.setdefault("active_buffs", []).append({
            "type": "crit_damage", "value": crit_dmg, "remaining": dur, "source": "perfect_opening"
        })
        return f"You spot the perfect opening! +{int(crit * 100)}% crit chance and +{int(crit_dmg * 100)}% crit damage for {dur} turns.", False

    # Prayer of Mending
    if skill_id == "clr_prayer_mending":
        target = _pick_ally_target()
        if not target:
            return ACTION_CANCELLED_MSG, False
        pct = 0.06 * status_mult
        dur = 4 + duration_bonus
        target.setdefault("active_buffs", []).append({
            "type": "regen_pct", "value": pct, "remaining": dur, "source": "prayer_mending"
        })
        name = "You" if target is player else display_name(target)
        return f"Mending light wraps {name} — {int(pct * 100)}% max HP restored each turn for {dur} turns.", False

    # Blessed Aegis
    if skill_id == "clr_blessed_aegis":
        target = _pick_ally_target()
        if not target:
            return ACTION_CANCELLED_MSG, False
        amount = int(player_max_hp(player) * 0.25 * status_mult)
        dur = 3 + duration_bonus
        from combat.status_effects import apply_barrier
        apply_barrier(target, amount, dur)
        name = "You" if target is player else display_name(target)
        return f"A blessed aegis surrounds {name}, absorbing up to {amount} damage for {dur} turns!", False

    # Camouflage
    if skill_id == "rng_camouflage":
        ev = 0.25 * status_mult
        crit = 0.10 * status_mult
        dur = 3 + duration_bonus
        player.setdefault("active_buffs", []).append({
            "type": "evasion", "value": ev, "remaining": dur, "source": "camouflage"
        })
        player.setdefault("active_buffs", []).append({
            "type": "crit_chance", "value": crit, "remaining": dur, "source": "camouflage"
        })
        return f"You melt into cover! +{int(ev * 100)}% evasion and +{int(crit * 100)}% crit chance for {dur} turns.", False

    # Hawk's Eye
    if skill_id == "rng_hawks_eye":
        crit = 0.15 * status_mult
        mark = 0.25 * status_mult
        dur = 3 + duration_bonus
        player.setdefault("active_buffs", []).append({
            "type": "crit_chance", "value": crit, "remaining": dur, "source": "hawks_eye"
        })
        player.setdefault("active_buffs", []).append({
            "type": "mark_damage_bonus", "value": mark, "remaining": dur, "source": "hawks_eye"
        })
        return f"You steady your aim! +{int(crit * 100)}% crit chance and +{int(mark * 100)}% Hunter's Mark bonus for {dur} turns.", False

    # Blessing of the Faithful
    if skill_id == "pal_blessing":
        target = _pick_ally_target()
        if not target:
            return ACTION_CANCELLED_MSG, False
        from combat.stat_milestones import get_wisdom_bonus
        from combat.status_effects import apply_healing
        from combat.ally_skills import is_heal_blocked
        name = "You" if target is player else display_name(target)
        if is_heal_blocked(target, player):
            return f"{name}'s Unholy Resilience rejects allied healing!", False
        heal = int((base_power + scaling) * power_mult * get_passive_heal_bonus(player)) + get_wisdom_bonus(player)
        actual = apply_healing(target, heal, source=player)
        if actual < 0:
            return f"The void twists the blessing! {name} takes {-actual} damage instead!", False
        def_val = _scaled_value(4)
        dur = 3 + duration_bonus
        target.setdefault("active_buffs", []).append({
            "type": "defense", "value": def_val, "remaining": dur, "source": "blessing"
        })
        return f"{name} is blessed — healed for {actual} HP and takes {def_val} less damage for {dur} turns!", False

    # Blood Pact
    if skill_id == "lck_blood_pact":
        max_hp = player_max_hp(player)
        hp_cost = int(max_hp * skill.get("hp_cost_percent", 0.15))
        player["current_hp"] = max(1, player["current_hp"] - hp_cost)
        val = _scaled_value(_scale_stat_buff(4, player))
        dur = 3 + duration_bonus
        player.setdefault("active_buffs", []).append({
            "stat": "Learning", "value": val, "remaining": dur, "source": "blood_pact"
        })
        player.setdefault("active_buffs", []).append({
            "stat": "Charisma", "value": val, "remaining": dur, "source": "blood_pact"
        })
        return f"You spill {hp_cost} HP as tribute! Learning +{val}, Charisma +{val} for {dur} turns.", False

    # Battle Trance
    if skill_id == "bar_battle_trance":
        val = _scaled_value(_scale_stat_buff(3, player))
        crit = 0.08 * status_mult
        dur = 3 + duration_bonus
        player.setdefault("active_buffs", []).append({
            "stat": "Strength", "value": val, "remaining": dur, "source": "battle_trance"
        })
        player.setdefault("active_buffs", []).append({
            "type": "crit_chance", "value": crit, "remaining": dur, "source": "battle_trance"
        })
        return f"You fall into a battle trance! Strength +{val} and +{int(crit * 100)}% crit chance for {dur} turns.", False

    # Reckless Abandon
    if skill_id == "bar_reckless_abandon":
        crit_dmg = 0.35 * status_mult
        vuln_pct = 0.12 * status_mult
        dur = 3 + duration_bonus
        player.setdefault("active_buffs", []).append({
            "type": "crit_damage", "value": crit_dmg, "remaining": dur, "source": "reckless_abandon"
        })
        player.setdefault("active_debuffs", []).append({
            "type": "vulnerable", "value": vuln_pct, "remaining": dur, "source": "reckless_abandon"
        })
        return f"You abandon all caution! +{int(crit_dmg * 100)}% crit damage, but you take {int(vuln_pct * 100)}% more damage for {dur} turns.", False

    # Providence (Cleric capstone)
    if skill_id == "clr_cap_providence":
        party = [player] + (allies or [])
        from combat.stat_milestones import get_wisdom_bonus
        from combat.status_effects import apply_healing, apply_barrier
        from combat.ally_skills import is_heal_blocked
        heal = int((base_power + scaling) * power_mult * get_passive_heal_bonus(player)) + get_wisdom_bonus(player)
        total_healed = 0
        for member in party:
            if member.get("current_hp", 0) <= 0 or is_heal_blocked(member, player):
                continue
            actual = apply_healing(member, heal, source=player)
            total_healed += max(0, actual)
        msg = f"Providence descends! The party recovers {total_healed} HP in total."
        dead = [m for m in party if m.get("current_hp", 0) <= 0]
        if dead:
            fallen = dead[0]
            max_hp = player_max_hp(fallen) if fallen is player else fallen.get("max_hp", 1)
            revive_hp = int(max_hp * skill.get("revive_percent", 0.50))
            fallen["current_hp"] = revive_hp
            if fallen is not player:
                fallen["defeated"] = False
            shield = int(player_max_hp(player) * skill.get("revive_barrier_pct", 0.15))
            apply_barrier(fallen, shield, 3)
            name = "You" if fallen is player else display_name(fallen)
            msg += f" {name} is pulled back from the brink with {revive_hp} HP and a {shield}-point ward!"
        return msg, False

    # ── Profession skills (Phase 3) — support / utility ──

    # Warlord — Iron Command
    if skill_id == "war_wl_iron_command":
        party = [player] + (allies or [])
        val = 0.15 * status_mult
        dur = 3 + duration_bonus
        for member in party:
            if member.get("current_hp", 0) <= 0:
                continue
            member.setdefault("active_buffs", []).append({
                "type": "damage_boost", "value": val, "remaining": dur, "source": "iron_command"
            })
            member.setdefault("active_buffs", []).append({
                "type": "fear_immunity", "remaining": dur, "source": "iron_command"
            })
        return f"Iron Command! The party deals +{int(val * 100)}% damage and stands immune to fear for {dur} turns.", False

    # Warlord — Warlord's Reign
    if skill_id == "war_wl_reign":
        bonus = 0.30 * status_mult
        dur = 4 + duration_bonus
        for e in enemies:
            if e["hp"] <= 0:
                continue
            e["hunters_mark"] = True
            e["hunters_mark_bonus"] = bonus
            e["hunters_mark_source"] = player.get("name", "Warlord")
            e["hunters_mark_turns"] = dur
        party = [player] + (allies or [])
        boost = 0.10 * status_mult
        for member in party:
            if member.get("current_hp", 0) <= 0:
                continue
            member.setdefault("active_buffs", []).append({
                "type": "damage_boost", "value": boost, "remaining": dur, "source": "warlords_reign"
            })
        return f"Warlord's Reign! All enemies are marked (+{int(bonus * 100)}% damage from every attack) for {dur} turns.", False

    # Sentinel — Guardian Stance
    if skill_id == "war_sent_guardian_stance":
        def_val = _scaled_value(6)
        reflect = 0.25 * status_mult
        dur = 3 + duration_bonus
        player.setdefault("active_buffs", []).append({
            "type": "defense", "value": def_val, "remaining": dur, "source": "guardian_stance"
        })
        player.setdefault("active_buffs", []).append({
            "type": "reflection", "value": reflect, "remaining": dur, "source": "guardian_stance"
        })
        return f"Guardian Stance! Damage taken -{def_val}, and attackers suffer {int(reflect * 100)}% backlash for {dur} turns.", False

    # Sentinel — Living Fortress
    if skill_id == "war_sent_living_fortress":
        party = [player] + (allies or [])
        def_val = _scaled_value(4)
        dur = 3 + duration_bonus
        for member in party:
            if member.get("current_hp", 0) <= 0:
                continue
            member.setdefault("active_buffs", []).append({
                "type": "defense", "value": def_val, "remaining": dur, "source": "living_fortress"
            })
        return f"Living Fortress! The party takes {def_val} less damage for {dur} turns.", False

    # Sentinel — Unbreakable
    if skill_id == "war_sent_unbreakable":
        from combat.status_effects import apply_death_ward
        apply_death_ward(player, 3 + duration_bonus)
        return "You plant your feet, unbreakable. The next lethal blow will leave you standing at 1 HP.", False

    # Evoker — Overchannel
    if skill_id == "mage_evo_overchannel":
        max_hp = player_max_hp(player)
        recoil = int(max_hp * skill.get("recoil_percent", 0.10))
        player["current_hp"] = max(1, player["current_hp"] - recoil)
        val = 0.30 * status_mult
        dur = 3 + duration_bonus
        player.setdefault("active_buffs", []).append({
            "type": "damage_boost", "value": val, "remaining": dur, "source": "overchannel"
        })
        return f"Overchannel! +{int(val * 100)}% damage for {dur} turns — at the cost of {recoil} HP.", False

    # Chronomancer — Temporal Acceleration
    if skill_id == "mage_chr_temporal_acceleration":
        amount = _scaled_value(2)
        _reduce_cooldowns_for(player, amount)
        for ally in (allies or []):
            if ally.get("current_hp", 0) > 0:
                _reduce_cooldowns_for(ally, amount)
        return f"Temporal Acceleration! Every party cooldown unwinds by {amount} turns.", False

    # Chronomancer — Time Stop
    if skill_id == "mage_chr_time_stop":
        stopped = 0
        from combat.status_effects import apply_slow_to_enemy
        for e in enemies:
            if e["hp"] <= 0:
                continue
            e["stunned"] = True
            apply_slow_to_enemy(e, duration=3 + duration_bonus)
            stopped += 1
        return f"Time Stop! {stopped} enem{'y' if stopped == 1 else 'ies'} freeze mid-motion — stunned and slowed.", False

    # Chronomancer — Rewind
    if skill_id == "mage_chr_rewind":
        max_hp = player_max_hp(player)
        heal = int(max_hp * skill.get("heal_percent", 0.40))
        from combat.status_effects import apply_healing
        healed = apply_healing(player, heal, source=player)
        _reduce_cooldowns_for(player, _scaled_value(4))
        if healed < 0:
            return f"The void twists the rewind! You take {-healed} damage — but your cooldowns still unwind by 4.", False
        return f"Rewind! Time folds back — {max(0, healed)} HP restored and your cooldowns unwind by 4.", False

    # Assassin — Mark for Death
    if skill_id == "rog_asm_mark_for_death":
        target = _pick_enemy_target()
        if not target:
            return ACTION_CANCELLED_MSG, False
        from combat.status_effects import apply_damage_taken_up, check_status_resisted
        val = 0.30 * status_mult
        dur = 4 + duration_bonus
        if check_status_resisted(target):
            return f"The {target['name']} resists your mark!", False
        apply_damage_taken_up(target, val, dur)
        return f"Mark for Death! The {target['name']} takes {int(val * 100)}% more damage for {dur} turns.", False

    # Shadowdancer — Veil of Shadows
    if skill_id == "rog_shd_veil_of_shadows":
        party = [player] + (allies or [])
        ev = 0.15 * status_mult
        dur = 3 + duration_bonus
        for member in party:
            if member.get("current_hp", 0) <= 0:
                continue
            member.setdefault("active_buffs", []).append({
                "type": "evasion", "value": ev, "remaining": dur, "source": "veil_of_shadows"
            })
        return f"Veil of Shadows! The party gains +{int(ev * 100)}% evasion for {dur} turns.", False

    # Hierophant — Sanctuary
    if skill_id == "clr_hie_sanctuary":
        party = [player] + (allies or [])
        pct = 0.05 * status_mult
        dur = 4 + duration_bonus
        cleansed = 0
        for member in party:
            if member.get("current_hp", 0) <= 0:
                continue
            member.setdefault("active_buffs", []).append({
                "type": "regen_pct", "value": pct, "remaining": dur, "source": "sanctuary"
            })
            cleansed += _cleanse_debuffs_for(member)
        return f"Sanctuary! {int(pct * 100)}% HP regen for {dur} turns — {cleansed} debuff(s) cleansed.", False

    # Hierophant — Greater Resurrection
    if skill_id == "clr_hie_greater_resurrection":
        target = _pick_dead_ally()
        if not target:
            return ACTION_CANCELLED_MSG, False
        max_hp = player_max_hp(target) if target is player else target.get("max_hp", 1)
        revive_hp = int(max_hp * skill.get("revive_percent", 0.75))
        target["current_hp"] = revive_hp
        if target is not player:
            target["defeated"] = False
        from combat.status_effects import apply_barrier
        shield = int(player_max_hp(player) * skill.get("revive_barrier_pct", 0.20))
        apply_barrier(target, shield, 3)
        name = "You" if target is player else display_name(target)
        return f"{name} rises again with {revive_hp} HP and a {shield}-point ward!", False

    # Hierophant — Eternal Light
    if skill_id == "clr_hie_eternal_light":
        party = [player] + (allies or [])
        from combat.stat_milestones import get_wisdom_bonus
        from combat.status_effects import apply_healing, apply_death_ward
        from combat.ally_skills import is_heal_blocked
        heal = int((base_power + scaling) * power_mult * get_passive_heal_bonus(player)) + get_wisdom_bonus(player)
        total = 0
        for member in party:
            if member.get("current_hp", 0) <= 0 or is_heal_blocked(member, player):
                continue
            total += max(0, apply_healing(member, heal, source=player))
            apply_death_ward(member, 2 + duration_bonus)
        return f"Eternal Light! {total} HP restored across the party, and death itself is held at bay (wards for 2 turns).", False

    # Sharpshooter — Steady Aim
    if skill_id == "rng_shp_steady_aim":
        crit = 0.20 * status_mult
        crit_dmg = 0.30 * status_mult
        dur = 3 + duration_bonus
        player.setdefault("active_buffs", []).append({
            "type": "crit_chance", "value": crit, "remaining": dur, "source": "steady_aim"
        })
        player.setdefault("active_buffs", []).append({
            "type": "crit_damage", "value": crit_dmg, "remaining": dur, "source": "steady_aim"
        })
        return f"Steady Aim! +{int(crit * 100)}% crit chance and +{int(crit_dmg * 100)}% crit damage for {dur} turns.", False

    # Templar — Aegis
    if skill_id == "pal_tmp_aegis":
        party = [player] + (allies or [])
        amount = int(player_max_hp(player) * skill.get("barrier_percent", 0.15) * status_mult)
        dur = 3 + duration_bonus
        from combat.status_effects import apply_barrier
        for member in party:
            if member.get("current_hp", 0) <= 0:
                continue
            apply_barrier(member, amount, dur)
        return f"Aegis! The party is shielded, each absorbing up to {amount} damage for {dur} turns.", False

    # Templar — Unbreakable Oath
    if skill_id == "pal_tmp_unbreakable_oath":
        target = _pick_ally_target()
        if not target:
            return ACTION_CANCELLED_MSG, False
        from combat.status_effects import apply_death_ward
        apply_death_ward(target, 4 + duration_bonus)
        name = "You" if target is player else display_name(target)
        return f"Unbreakable Oath! {name} cannot fall — the next lethal blow leaves them standing.", False

    # Templar — Bastion Eternal
    if skill_id == "pal_tmp_bastion_eternal":
        party = [player] + (allies or [])
        def_val = _scaled_value(5)
        regen = 0.04 * status_mult
        dur = 4 + duration_bonus
        for member in party:
            if member.get("current_hp", 0) <= 0:
                continue
            member.setdefault("active_buffs", []).append({
                "type": "defense", "value": def_val, "remaining": dur, "source": "bastion_eternal"
            })
            member.setdefault("active_buffs", []).append({
                "type": "regen_pct", "value": regen, "remaining": dur, "source": "bastion_eternal"
            })
        return f"Bastion Eternal! Party damage taken -{def_val} and {int(regen * 100)}% HP regen for {dur} turns.", False

    # Berserker — Bloodrage
    if skill_id == "bar_bsk_bloodrage":
        dur = 3 + duration_bonus
        player["bloodlust_turns"] = max(player.get("bloodlust_turns", 0), dur)
        crit = 0.10 * status_mult
        player.setdefault("active_buffs", []).append({
            "type": "crit_chance", "value": crit, "remaining": dur, "source": "bloodrage"
        })
        return f"Bloodrage! 50% lifesteal and +{int(crit * 100)}% crit chance for {dur} turns.", False

    # Berserker — Undying Rage
    if skill_id == "bar_bsk_undying_rage":
        from combat.status_effects import apply_death_ward
        apply_death_ward(player, 3 + duration_bonus)
        val = _scaled_value(_scale_stat_buff(3, player))
        player.setdefault("active_buffs", []).append({
            "stat": "Strength", "value": val, "remaining": 3 + duration_bonus, "source": "undying_rage"
        })
        return f"Undying Rage! Strength +{val}, and death will not take you — the next lethal blow leaves you at 1 HP.", False

    # Juggernaut — Unyielding
    if skill_id == "bar_jug_unyielding":
        def_val = _scaled_value(6)
        dur = 3 + duration_bonus
        cleansed = _cleanse_debuffs_for(player)
        player.setdefault("active_buffs", []).append({
            "type": "defense", "value": def_val, "remaining": dur, "source": "unyielding"
        })
        return f"Unyielding! Damage taken -{def_val} for {dur} turns ({cleansed} debuff(s) shaken off).", False

    # ── Damage-dealing skills ──

    # Multi-target (enemies)
    if target_type == "enemies":
        total_hits = skill.get("hits", 1)
        # ── Capstone AoE skills (bespoke; neutralise the generic loop) ──
        if skill_id == "war_cap_onslaught":
            total_hits = 0
            flurry = skill.get("hits", 5)
            for hit in range(flurry):
                live = [e for e in enemies if e["hp"] > 0]
                if not live:
                    break
                target = random.choice(live) if len(live) > 1 else live[0]
                if (hit == flurry - 1 and target["max_hp"] > 0
                        and target["hp"] / target["max_hp"] < 0.30):
                    target["hp"] = 0
                    msg_parts.append(f"ONSLAUGHT! The final blow executes the {target['name']}!")
                    continue
                power = int((base_power + scaling) * power_mult)
                dmg = _calc_dmg(target, power)
                target["hp"] -= dmg
                msg_parts.append(format_damage_msg(player['name'], target['name'], dmg, element=skill.get('elemental'), skill_name=skill['name']))
                if target["hp"] <= 0:
                    msg_parts.append(f"{target['name']} falls before the onslaught!")
                _apply_life_steal(dmg)
        elif skill_id == "rng_cap_skyfall_volley":
            total_hits = 0
            for e in list(enemies):
                if e["hp"] <= 0:
                    continue
                for _ in range(skill.get("hits", 2)):
                    if e["hp"] <= 0:
                        break
                    power = int((base_power + scaling) * power_mult)
                    dmg = _calc_dmg(e, power)
                    e["hp"] -= dmg
                    msg_parts.append(format_damage_msg(player['name'], e['name'], dmg, element=skill.get('elemental'), skill_name=skill['name']))
                    _apply_life_steal(dmg)
                if e["hp"] > 0:
                    from combat.status_effects import apply_slow_to_enemy
                    if apply_slow_to_enemy(e, duration=3 + duration_bonus) != "resisted":
                        msg_parts.append(f"{e['name']} is pinned by the volley!")
                else:
                    msg_parts.append(f"{e['name']} is buried under the skyfall!")
        elif skill_id == "bar_cap_wrath_incarnate":
            total_hits = 0
            for e in list(enemies):
                if e["hp"] <= 0:
                    continue
                power = int((base_power + scaling) * power_mult)
                dmg = _calc_dmg(e, power)
                e["hp"] -= dmg
                msg_parts.append(format_damage_msg(player['name'], e['name'], dmg, element=skill.get('elemental'), skill_name=skill['name']))
                if random.random() < skill.get("stun_chance", 0):
                    from combat.status_effects import check_status_resisted as _resisted_wrath
                    if _resisted_wrath(e):
                        msg_parts.append(f"{e['name']} shrugs off the tremor!")
                    else:
                        e["stunned"] = True
                        msg_parts.append(f"{e['name']} is stunned!")
                if e["hp"] <= 0:
                    msg_parts.append(f"{e['name']} is shattered!")
                _apply_life_steal(dmg)
            max_hp = player_max_hp(player)
            heal = int(max_hp * skill.get("self_heal_percent", 0.25))
            from combat.status_effects import apply_healing
            actual = apply_healing(player, heal, source=player)
            if actual < 0:
                msg_parts.append(f"The void twists the fury! You take {-actual} damage!")
            elif actual > 0:
                msg_parts.append(f"Wrath sustains you — you recover {actual} HP!")
        elif skill_id == "lck_cap_dark_apotheosis":
            total_hits = 0
            total_dmg = 0
            for e in list(enemies):
                if e["hp"] <= 0:
                    continue
                power = int((base_power + scaling) * power_mult)
                dmg = _calc_dmg(e, power)
                e["hp"] -= dmg
                total_dmg += dmg
                msg_parts.append(format_damage_msg(player['name'], e['name'], dmg, element=skill.get('elemental'), skill_name=skill['name']))
                if e["hp"] <= 0:
                    msg_parts.append(f"{e['name']}'s soul is devoured!")
            val = _scaled_value(_scale_stat_buff(4, player))
            dur = 4 + duration_bonus
            player.setdefault("active_buffs", []).append({
                "stat": "Learning", "value": val, "remaining": dur, "source": "dark_apotheosis"
            })
            player.setdefault("active_buffs", []).append({
                "stat": "Charisma", "value": val, "remaining": dur, "source": "dark_apotheosis"
            })
            msg_parts.append(f"Dark power surges through you! Learning +{val}, Charisma +{val} for {dur} turns.")
            if total_dmg > 0:
                from combat.status_effects import apply_healing
                healed = apply_healing(player, total_dmg, source=player)
                if healed > 0:
                    msg_parts.append(f"Dark Apotheosis! You devour {healed} HP from the fallen essence.")
        elif skill_id == "lck_net_feast_of_shadows":
            total_hits = 0
            total_dmg = 0
            for e in list(enemies):
                if e["hp"] <= 0:
                    continue
                power = int((base_power + scaling) * power_mult)
                dmg = _calc_dmg(e, power)
                e["hp"] -= dmg
                total_dmg += dmg
                msg_parts.append(format_damage_msg(player['name'], e['name'], dmg, element=skill.get('elemental'), skill_name=skill['name']))
                if e["hp"] <= 0:
                    msg_parts.append(f"{e['name']}'s shadow is consumed!")
            if total_dmg > 0:
                from combat.status_effects import apply_healing
                healed = apply_healing(player, total_dmg, source=player)
                if healed > 0:
                    msg_parts.append(f"You feast on the shadows (+{healed} HP).")
        elif skill_id == "lck_net_dominion_of_dread":
            total_hits = 0
            fear_val = 0.30 * status_mult
            dur = 4 + duration_bonus
            from combat.status_effects import apply_damage_taken_up, apply_poison, check_status_resisted
            for e in list(enemies):
                if e["hp"] <= 0 or check_status_resisted(e):
                    continue
                e.setdefault("active_debuffs", []).append({
                    "type": "fear", "value": fear_val, "remaining": dur
                })
                apply_damage_taken_up(e, 0.15 * status_mult, dur)
                apply_poison(e, int(6 * status_mult), 4)
            msg_parts.append(f"Dominion of Dread! Enemies cower (-{int(fear_val * 100)}% damage), branded and decaying for {dur} turns.")
        elif skill_id == "lck_inf_infernal_avatar":
            total_hits = 0
            val = 0.25 * status_mult
            dur = 3 + duration_bonus
            player.setdefault("active_buffs", []).append({
                "type": "elemental_dmg_elem", "element": "fire", "value": val,
                "remaining": dur, "source": "infernal_avatar"
            })
            for e in list(enemies):
                if e["hp"] <= 0:
                    continue
                power = int((base_power + scaling) * power_mult)
                dmg = _calc_dmg(e, power)
                e["hp"] -= dmg
                msg_parts.append(format_damage_msg(player['name'], e['name'], dmg, element=skill.get('elemental'), skill_name=skill['name']))
                if e["hp"] <= 0:
                    msg_parts.append(f"{e['name']} is consumed by the avatar's fire!")
            msg_parts.append(f"The Infernal Avatar rises! +{int(val * 100)}% fire damage for {dur} turns.")
        elif skill_id == "mage_cap_cataclysm":
            total_hits = 0
            msg_parts.append("CATACLYSM! Seven elements scour the field!")
            elements = skill.get("elements") or [
                "fire", "water", "thunder", "wind", "earth", "light", "dark"
            ]
            struck = set()
            for el in elements:
                live = [e for e in enemies if e["hp"] > 0]
                if not live:
                    break
                pool = [e for e in live if id(e) not in struck]
                if not pool:
                    # Every living enemy has been struck once — start a new cycle.
                    struck.clear()
                    pool = live
                target = random.choice(pool)
                struck.add(id(target))
                power = int((base_power + scaling) * power_mult)
                dmg = _calc_dmg(target, power, element=el)
                target["hp"] -= dmg
                msg_parts.append(format_damage_msg(
                    player['name'], target['name'], dmg, element=el, skill_name=skill['name']
                ))
                if el == "fire" and dmg > 0 and target["hp"] > 0 and skill.get("burn_damage"):
                    from combat.status_effects import apply_burn, damage_to_burn_tier
                    b_tier = min(5, damage_to_burn_tier(skill["burn_damage"]) + burn_tier_bonus)
                    if apply_burn(target, b_tier, skill.get("burn_duration", 4)) in (
                            "applied", "upgraded", "intensified", "refreshed"):
                        msg_parts.append(f"{target['name']} is set ablaze!")
                if target["hp"] <= 0:
                    msg_parts.append(f"{target['name']} is unmade by the cataclysm!")
                _apply_life_steal(dmg)
        elif skill_id == "mage_evo_ascension":
            total_hits = 0
            for e in list(enemies):
                if e["hp"] <= 0:
                    continue
                power = int((base_power + scaling) * power_mult)
                dmg = _calc_dmg(e, power)
                e["hp"] -= dmg
                msg_parts.append(format_damage_msg(player['name'], e['name'], dmg, element=skill.get('elemental'), skill_name=skill['name']))
                if e["hp"] <= 0:
                    msg_parts.append(f"{e['name']} is scoured from being!")
            val = 0.20 * status_mult
            dur = 3 + duration_bonus
            player.setdefault("active_buffs", []).append({
                "type": "damage_boost", "value": val, "remaining": dur, "source": "arcane_ascension"
            })
            player.setdefault("active_buffs", []).append({
                "type": "elemental_dmg", "value": 0.15 * status_mult, "remaining": dur, "source": "arcane_ascension"
            })
            msg_parts.append(f"Arcane Ascension! +{int(val * 100)}% damage and +15% elemental power for {dur} turns.")
        elif skill_id == "clr_inq_day_of_reckoning":
            total_hits = 0
            for e in list(enemies):
                if e["hp"] <= 0:
                    continue
                power = int((base_power + scaling) * power_mult)
                if e.get("active_debuffs"):
                    power = int(power * 1.30)
                dmg = _calc_dmg(e, power)
                e["hp"] -= dmg
                msg_parts.append(format_damage_msg(player['name'], e['name'], dmg, element=skill.get('elemental'), skill_name=skill['name']))
                if e["hp"] <= 0:
                    msg_parts.append(f"{e['name']} answers for its sins!")
        elif skill_id == "rog_shd_nightmare_requiem":
            total_hits = 0
            fear_val = 0.25 * status_mult
            dur = 3 + duration_bonus
            from combat.status_effects import apply_bleed, check_status_resisted
            for e in list(enemies):
                if e["hp"] <= 0:
                    continue
                if not check_status_resisted(e):
                    e.setdefault("active_debuffs", []).append({
                        "type": "fear", "value": fear_val, "remaining": dur
                    })
                if apply_bleed(e, int(5 * status_mult), 4, source=skill_id) in ("applied", "refreshed", "stacked"):
                    msg_parts.append(f"{e['name']} is bleeding!")
            msg_parts.append(f"Nightmare Requiem! Enemies relive their deaths (-{int(fear_val * 100)}% damage for {dur} turns).")
        for hit in range(total_hits):
            live = [e for e in enemies if e["hp"] > 0]
            if not live:
                break
            if total_hits > 1 and len(live) > 1:
                target = random.choice(live)
            else:
                # Single hit to all enemies
                for target in live:
                    power = int((base_power + scaling) * power_mult)
                    # Sneak-attack style bonus vs impaired targets (passive effects)
                    if target.get("slowed") or target.get("stunned"):
                        sneak = sum(e.get("value", 0) for e in get_player_passive_effects(player)
                                    if e.get("type") == "vulnerable_bonus")
                        if sneak:
                            power = int(power * (1 + sneak))
                    # Guaranteed crit
                    guaranteed = skill.get("guaranteed_crit", False)
                    if guaranteed:
                        power *= 2
                        msg_parts.append("Critical hit!")
                    dmg = _calc_dmg(target, power, skill.get("ignore_armor", False), guaranteed_crit=guaranteed)
                    target["hp"] -= dmg
                    msg_parts.append(format_damage_msg(player['name'], target['name'], dmg, element=skill.get("elemental"), crit=guaranteed, skill_name=skill['name']))
                    # Apply slow
                    if skill.get("apply_slow"):
                        from combat.status_effects import apply_slow_to_enemy
                        if apply_slow_to_enemy(target, duration=3 + duration_bonus) != "resisted":
                            msg_parts.append(f"{target['name']} is slowed!")
                    # Apply stun
                    if skill.get("stun_chance") and random.random() < skill["stun_chance"]:
                        from combat.status_effects import check_status_resisted as _resisted
                        if _resisted(target):
                            msg_parts.append(f"{target['name']} shrugs off the stun!")
                        else:
                            target["stunned"] = True
                            msg_parts.append(f"{target['name']} is stunned!")
                    # Apply weaken
                    if skill.get("apply_weaken"):
                        from combat.status_effects import apply_weaken
                        if apply_weaken(target, duration=3 + duration_bonus) != "resisted":
                            msg_parts.append(f"{target['name']} is weakened!")
                    # Apply burn (mastery upgrades the tier: +1 at ★3, +1 more at ✦✦)
                    if skill.get("burn_damage"):
                        from combat.status_effects import apply_burn, damage_to_burn_tier, get_burn_tier_name
                        b_tier = min(5, damage_to_burn_tier(skill["burn_damage"]) + burn_tier_bonus)
                        if apply_burn(target, b_tier, skill.get("burn_duration", 3)) != "resisted":
                            msg_parts.append(f"{target['name']} is set ablaze!")
                    # Apply poison
                    if skill.get("poison_damage"):
                        p_dmg = skill["poison_damage"]
                        if status_mult > 1:
                            p_dmg = int(p_dmg * status_mult)
                        if apply_poison(target, p_dmg, skill.get("poison_duration", 3)) != "resisted":
                            msg_parts.append(f"{target['name']} is poisoned!")
                    # Apply bleed
                    if skill.get("bleed_damage"):
                        from combat.status_effects import apply_bleed
                        b_dmg = skill["bleed_damage"]
                        if status_mult > 1:
                            b_dmg = int(b_dmg * status_mult)
                        if apply_bleed(target, b_dmg, skill.get("bleed_duration", 4), source=skill_id) in ("applied", "refreshed", "stacked"):
                            msg_parts.append(f"{target['name']} is bleeding!")
                    # Apply sunder
                    if skill.get("apply_sunder"):
                        from combat.status_effects import check_status_resisted as _resisted_sunder
                        if _resisted_sunder(target):
                            msg_parts.append(f"{target['name']} shrugs off the armor break!")
                        else:
                            target.setdefault("active_debuffs", []).append({
                                "type": "sunder", "value": skill.get("sunder_value", 3),
                                "remaining": skill.get("sunder_duration", 3) + duration_bonus
                            })
                            msg_parts.append(f"{target['name']}'s armor is sundered!")
                    if target["hp"] <= 0:
                        msg_parts.append(f"{target['name']} is defeated!")
                    _apply_life_steal(dmg)
                break
            if total_hits > 1:
                power = int((base_power + scaling) * power_mult)
                guaranteed = skill.get("guaranteed_crit", False)
                if guaranteed:
                    power *= 2
                dmg = _calc_dmg(target, power, skill.get("ignore_armor", False), guaranteed_crit=guaranteed)
                target["hp"] -= dmg
                msg_parts.append(format_damage_msg(player['name'], target['name'], dmg, element=skill.get("elemental"), crit=guaranteed, skill_name=skill['name']))
                if target["hp"] <= 0:
                    msg_parts.append(f"{target['name']} is defeated!")
                _apply_life_steal(dmg)
        if not [e for e in enemies if e["hp"] > 0]:
            victory = True

    # Single target
    elif target_type in ("enemy", "ally_or_self", "all_allies", "dead_ally"):
        if target_type == "enemy":
            target = _pick_enemy_target()
        elif target_type == "dead_ally":
            target = _pick_dead_ally()
        elif target_type == "all_allies":
            target = None  # Handled per-skill above
        else:
            target = _pick_ally_target()
        if not target and target_type not in ("all_allies",):
            return ACTION_CANCELLED_MSG, False

        # Execute
        if skill_id == "war_execute":
            hp_ratio = target["hp"] / target["max_hp"] if target["max_hp"] > 0 else 1
            power = int((base_power + scaling) * power_mult)
            if hp_ratio < 0.30:
                power *= 3
                msg_parts.append(f"EXECUTE! The {target['name']} is below 30% HP!")
            dmg = _calc_dmg(target, power)
            target["hp"] -= dmg
            msg_parts.append(format_damage_msg(player['name'], target['name'], dmg, element=skill.get('elemental'), skill_name=skill['name']))
            if target["hp"] <= 0:
                msg_parts.append(f"{target['name']} is defeated!")
                victory = True
            _apply_life_steal(dmg)

        # Backstab
        elif skill_id == "rog_backstab":
            power = int((base_power + scaling) * power_mult)
            if target.get("slowed") or target.get("stunned"):
                power *= 2
                msg_parts.append("Critical backstab! The target is vulnerable!")
            dmg = _calc_dmg(target, power)
            target["hp"] -= dmg
            msg_parts.append(format_damage_msg(player['name'], target['name'], dmg, element=skill.get('elemental'), skill_name=skill['name']))
            if target["hp"] <= 0:
                msg_parts.append(f"{target['name']} is defeated!")
                victory = True
            _apply_life_steal(dmg)

        # Assassinate
        elif skill_id == "rog_assassinate":
            hp_ratio = target["hp"] / target["max_hp"] if target["max_hp"] > 0 else 1
            threshold = 0.20 if extra_effect else 0.15
            if hp_ratio < threshold:
                target["hp"] = 0
                msg_parts.append(f"ASSASSINATE! You instantly slay the {target['name']}!")
                victory = True
            else:
                power = int((base_power + scaling) * power_mult)
                dmg = _calc_dmg(target, power)
                target["hp"] -= dmg
                msg_parts.append(format_damage_msg(player['name'], target['name'], dmg, element=skill.get('elemental'), skill_name=skill['name']))
                if target["hp"] <= 0:
                    msg_parts.append(f"{target['name']} is defeated!")
                    victory = True
            _apply_life_steal(dmg)

        # Holy Strike
        elif skill_id == "pal_strike":
            power = int((base_power + scaling) * power_mult)
            dmg = _calc_dmg(target, power)
            target["hp"] -= dmg
            msg_parts.append(format_damage_msg(player['name'], target['name'], dmg, element=skill.get('elemental'), skill_name=skill['name']))
            if random.random() < skill.get("stun_chance", 0):
                from combat.status_effects import check_status_resisted as _resisted
                if _resisted(target):
                    msg_parts.append(f"The {target['name']} shrugs off the holy light!")
                else:
                    target["stunned"] = True
                    msg_parts.append(f"The {target['name']} is stunned!")
            if target["hp"] <= 0:
                msg_parts.append(f"{target['name']} is defeated!")
                victory = True
            _apply_life_steal(dmg)

        # Divine Judgment
        elif skill_id == "pal_judgment":
            power = int((base_power + scaling) * power_mult)
            if target.get("stunned"):
                power *= 2
                msg_parts.append("Divine Judgment strikes a stunned foe!")
            dmg = _calc_dmg(target, power)
            target["hp"] -= dmg
            msg_parts.append(format_damage_msg(player['name'], target['name'], dmg, element=skill.get('elemental'), skill_name=skill['name']))
            if target["hp"] <= 0:
                msg_parts.append(f"{target['name']} is defeated!")
                victory = True
            _apply_life_steal(dmg)

        # Drain Life
        elif skill_id == "lck_drain":
            power = int((base_power + scaling) * power_mult)
            dmg = _calc_dmg(target, power)
            target["hp"] -= dmg
            from combat.stat_milestones import get_wisdom_bonus
            heal = dmg + get_wisdom_bonus(player)
            from combat.status_effects import apply_healing
            healed = apply_healing(player, heal, source=player)
            if healed < 0:
                msg_parts.append(format_damage_msg(player['name'], target['name'], dmg, element=skill.get('elemental'), skill_name=skill['name']) + f" (Void Drain: {-healed} damage!)")
            else:
                msg_parts.append(format_damage_msg(player['name'], target['name'], dmg, element=skill.get('elemental'), skill_name=skill['name']) + f" (Drain: +{healed} HP)")
            if target["hp"] <= 0:
                msg_parts.append(f"{target['name']} is defeated!")
                victory = True

        # Siphon Soul
        elif skill_id == "lck_siphon_soul":
            power = int((base_power + scaling) * power_mult)
            dmg = _calc_dmg(target, power)
            target["hp"] -= dmg
            from combat.stat_milestones import get_wisdom_bonus
            heal = dmg + get_wisdom_bonus(player)
            from combat.status_effects import apply_healing
            healed = apply_healing(player, heal, source=player)
            if healed < 0:
                msg_parts.append(format_damage_msg(player['name'], target['name'], dmg, element=skill.get('elemental'), skill_name=skill['name']) + f" (Void Siphon: {-healed} damage!)")
            else:
                msg_parts.append(format_damage_msg(player['name'], target['name'], dmg, element=skill.get('elemental'), skill_name=skill['name']) + f" (Siphon: +{healed} HP)")
            if target["hp"] <= 0:
                msg_parts.append(f"{target['name']}'s soul is consumed!")
                victory = True

        # Demonic Pact
        elif skill_id == "lck_pact":
            max_hp = player_max_hp(player)
            hp_cost = int(max_hp * 0.20)
            player["current_hp"] = max(1, player["current_hp"] - hp_cost)
            power = int((base_power + scaling) * power_mult)
            dmg = _calc_dmg(target, power)
            target["hp"] -= dmg
            msg_parts.append(f"Sacrificed {hp_cost} HP | " + format_damage_msg(player['name'], target['name'], dmg, element=skill.get('elemental'), skill_name=skill['name']))
            if target["hp"] <= 0:
                msg_parts.append(f"{target['name']} is defeated!")
                victory = True
            _apply_life_steal(dmg)

        # Holy Smite
        elif skill_id == "clr_smite":
            power = int((base_power + scaling) * power_mult)
            dmg = _calc_dmg(target, power)
            target["hp"] -= dmg
            from combat.stat_milestones import get_wisdom_bonus
            heal = int(dmg * 0.5 * get_passive_heal_bonus(player)) + get_wisdom_bonus(player)
            from combat.status_effects import apply_healing
            actual_heal = apply_healing(player, heal, source=player)
            if actual_heal < 0:
                msg_parts.append(format_damage_msg(player['name'], target['name'], dmg, element=skill.get('elemental'), skill_name=skill['name']) + f" (Void backlash: {-actual_heal} damage!)")
            else:
                msg_parts.append(format_damage_msg(player['name'], target['name'], dmg, element=skill.get('elemental'), skill_name=skill['name']) + f" (Heal: +{actual_heal} HP)")
            if target["hp"] <= 0:
                msg_parts.append(f"{target['name']} is defeated!")
                victory = True
            _apply_life_steal(dmg)

        # Fireball
        elif skill_id == "mage_fireball":
            power = int((base_power + scaling) * power_mult)
            dmg = _calc_dmg(target, power)
            target["hp"] -= dmg
            msg_parts.append(format_damage_msg(player['name'], target['name'], dmg, element=skill.get('elemental'), skill_name=skill['name']))
            if target["hp"] <= 0:
                msg_parts.append(f"{target['name']} is incinerated!")
                victory = True
            _apply_life_steal(dmg)

        # Frost Nova (already handles multi-target above, but check single target case)
        elif skill_id == "mage_frostnova":
            power = int((base_power + scaling) * power_mult)
            for e in enemies:
                dmg = _calc_dmg(e, power)
                e["hp"] -= dmg
                from combat.status_effects import apply_slow_to_enemy
                apply_slow_to_enemy(e, duration=3 + duration_bonus)
                msg_parts.append(format_damage_msg(player['name'], e['name'], dmg, element=skill.get('elemental'), skill_name=skill['name']) + " +Slowed")
                if e["hp"] <= 0:
                    msg_parts.append(f"{e['name']} freezes solid and shatters!")
            if not [e for e in enemies if e["hp"] > 0]:
                victory = True

        # Meteor
        elif skill_id == "mage_meteor":
            power = int((base_power + scaling) * power_mult)
            for e in enemies:
                dmg = _calc_dmg(e, power)
                e["hp"] -= dmg
                msg_parts.append(format_damage_msg(player['name'], e['name'], dmg, element=skill.get('elemental'), skill_name=skill['name']))
                if e["hp"] <= 0:
                    msg_parts.append(f"{e['name']} is vaporized!")
            if not [e for e in enemies if e["hp"] > 0]:
                victory = True

        # Mana Overload
        elif skill_id == "mage_overload":
            max_hp = player_max_hp(player)
            recoil = int(max_hp * skill.get("recoil_percent", 0.10))
            player["current_hp"] = max(1, player["current_hp"] - recoil)
            power = int((base_power + scaling) * power_mult)
            dmg = _calc_dmg(target, power)
            target["hp"] -= dmg
            msg_parts.append(format_damage_msg(player['name'], target['name'], dmg, element=skill.get('elemental'), skill_name=skill['name']) + f" (Recoil: -{recoil} HP)")
            if target["hp"] <= 0:
                msg_parts.append(f"{target['name']} is disintegrated!")
                victory = True
            _apply_life_steal(dmg)

        # Shadow Strike
        elif skill_id == "rog_shadow_strike":
            power = int((base_power + scaling) * power_mult) * 2
            dmg = _calc_dmg(target, power, skill.get("ignore_armor", False))
            target["hp"] -= dmg
            msg_parts.append(format_damage_msg(player['name'], target['name'], dmg, element=skill.get('elemental'), skill_name=skill['name']))
            if target["hp"] <= 0:
                msg_parts.append(f"{target['name']} is defeated!")
                victory = True
            _apply_life_steal(dmg)

        # Venomous Blade
        elif skill_id == "rog_venom":
            power = int((base_power + scaling) * power_mult)
            dmg = _calc_dmg(target, power)
            target["hp"] -= dmg
            msg_parts.append(format_damage_msg(player['name'], target['name'], dmg, element=skill.get('elemental'), skill_name=skill['name']))
            from combat.status_effects import apply_poison
            poison_dmg = skill.get("poison_damage", 5)
            if status_mult > 1:
                poison_dmg = int(poison_dmg * status_mult)
            apply_poison(target, poison_dmg, skill.get("poison_duration", 5))
            msg_parts.append(f"The {target['name']} is poisoned for {poison_dmg}/turn!")
            if target["hp"] <= 0:
                msg_parts.append(f"{target['name']} is defeated!")
                victory = True
            _apply_life_steal(dmg)

        # Piercing Shot
        elif skill_id == "rng_pierce":
            power = int((base_power + scaling) * power_mult)
            dmg = _calc_dmg(target, power, ignore_armor=True)
            target["hp"] -= dmg
            msg_parts.append(format_damage_msg(player['name'], target['name'], dmg, element=skill.get('elemental'), skill_name=skill['name']) + " [Ignores Armor]")
            if target["hp"] <= 0:
                msg_parts.append(f"{target['name']} is defeated!")
                victory = True
            _apply_life_steal(dmg)

        # Trueshot
        elif skill_id == "rng_trueshot":
            power = int((base_power + scaling) * power_mult) * 3
            dmg = _calc_dmg(target, power, ignore_armor=True)
            target["hp"] -= dmg
            msg_parts.append(format_damage_msg(player['name'], target['name'], dmg, element=skill.get('elemental'), skill_name=skill['name']) + " [Ignores Armor]")
            if target["hp"] <= 0:
                msg_parts.append(f"{target['name']} is defeated!")
                victory = True
            _apply_life_steal(dmg)

        # Rain of Arrows
        elif skill_id == "rng_rain":
            power = int((base_power + scaling) * power_mult)
            for e in enemies:
                dmg = _calc_dmg(e, power)
                e["hp"] -= dmg
                msg_parts.append(format_damage_msg(player['name'], e['name'], dmg, element=skill.get('elemental'), skill_name=skill['name']))
                if e["hp"] <= 0:
                    msg_parts.append(f"{e['name']} is defeated!")
            if not [e for e in enemies if e["hp"] > 0]:
                victory = True

        # Rapid Fire
        elif skill_id == "rng_rapid":
            power = int((base_power + scaling) * power_mult)
            for _ in range(skill.get("hits", 3)):
                if target["hp"] <= 0:
                    break
                dmg = _calc_dmg(target, power, skill.get("ignore_armor", False))
                target["hp"] -= dmg
                msg_parts.append(format_damage_msg(player['name'], target['name'], dmg, element=skill.get('elemental'), skill_name=skill['name']))
            if target["hp"] <= 0:
                msg_parts.append(f"{target['name']} is defeated!")
                victory = True
            _apply_life_steal(dmg)

        # Consecrate
        elif skill_id == "pal_consecrate":
            power = int((base_power + scaling) * power_mult)
            for e in enemies:
                dmg = _calc_dmg(e, power)
                e["hp"] -= dmg
                from combat.status_effects import apply_weaken
                apply_weaken(e, duration=3 + duration_bonus)
                msg_parts.append(format_damage_msg(player['name'], e['name'], dmg, element=skill.get('elemental'), skill_name=skill['name']))
                if e["hp"] <= 0:
                    msg_parts.append(f"{e['name']} is purified!")
            if not [e for e in enemies if e["hp"] > 0]:
                victory = True

        # Avenging Wrath
        elif skill_id == "pal_avenging":
            total_dmg = 0
            power = int((base_power + scaling) * power_mult)
            for e in enemies:
                dmg = _calc_dmg(e, power)
                e["hp"] -= dmg
                total_dmg += dmg
                msg_parts.append(format_damage_msg(player['name'], e['name'], dmg, element=skill.get('elemental'), skill_name=skill['name']))
                if e["hp"] <= 0:
                    msg_parts.append(f"{e['name']} is smited!")
            if not [e for e in enemies if e["hp"] > 0]:
                victory = True
            old_hp = player.get("current_hp", 0)
            max_hp = player_max_hp(player)
            from combat.stat_milestones import get_wisdom_bonus
            heal = min(total_dmg + get_wisdom_bonus(player), max_hp - old_hp)
            player["current_hp"] = old_hp + heal
            if heal > 0:
                msg_parts.append(f"You absorb the holy wrath, healing for {heal} HP!")
            _apply_life_steal(total_dmg)

        # Divine Wrath (Cleric)
        elif skill_id == "clr_divine_wrath":
            total_dmg = 0
            power = int((base_power + scaling) * power_mult)
            for e in enemies:
                dmg = _calc_dmg(e, power)
                e["hp"] -= dmg
                total_dmg += dmg
                msg_parts.append(format_damage_msg(player['name'], e['name'], dmg, element=skill.get('elemental'), skill_name=skill['name']))
                if e["hp"] <= 0:
                    msg_parts.append(f"{e['name']} is judged!")
            if not [e for e in enemies if e["hp"] > 0]:
                victory = True
            party = [player] + (allies or [])
            from combat.stat_milestones import get_wisdom_bonus
            heal_per = (total_dmg // max(1, len(party))) + get_wisdom_bonus(player)
            for member in party:
                if member.get("current_hp", 0) > 0:
                    old_hp = member.get("current_hp", 0)
                    max_hp = player_max_hp(member) if member is player else member.get("max_hp", old_hp)
                    member["current_hp"] = min(old_hp + heal_per, max_hp)
            if total_dmg > 0:
                msg_parts.append(f"The party shares {total_dmg} HP of divine healing!")

        # Soul Fire
        elif skill_id == "lck_soul_fire":
            power = int((base_power + scaling) * power_mult)
            dmg = _calc_dmg(target, power)
            target["hp"] -= dmg
            msg_parts.append(format_damage_msg(player['name'], target['name'], dmg, element=skill.get('elemental'), skill_name=skill['name']))
            from combat.status_effects import apply_burn, damage_to_burn_tier, get_burn_tier_name
            b_tier = min(5, damage_to_burn_tier(skill.get("burn_damage", 6)) + burn_tier_bonus)
            if apply_burn(target, b_tier, skill.get("burn_duration", 3)) != "resisted":
                msg_parts.append(f"{target['name']}'s soul is seared by {get_burn_tier_name(b_tier)}!")
            if target["hp"] <= 0:
                msg_parts.append(f"{target['name']} is consumed by the flames!")
                victory = True
            _apply_life_steal(dmg)

        # Sunder Armor
        elif skill_id == "bar_sunder":
            power = int((base_power + scaling) * power_mult)
            dmg = _calc_dmg(target, power)
            target["hp"] -= dmg
            msg_parts.append(format_damage_msg(player['name'], target['name'], dmg, element=skill.get('elemental'), skill_name=skill['name']))
            sunder_val = _scaled_value(skill.get("sunder_value", 3))
            from combat.status_effects import check_status_resisted as _resisted_sunder
            if _resisted_sunder(target):
                msg_parts.append(f"{target['name']} shrugs off the armor break!")
            else:
                target.setdefault("active_debuffs", []).append({
                    "type": "sunder", "value": sunder_val,
                    "remaining": skill.get("sunder_duration", 3) + duration_bonus
                })
                msg_parts.append(f"{target['name']}'s armor is sundered by {sunder_val}!")
            if target["hp"] <= 0:
                msg_parts.append(f"{target['name']} is defeated!")
                victory = True
            _apply_life_steal(dmg)

        # Earth Shatter
        elif skill_id == "bar_earth_shatter":
            power = int((base_power + scaling) * power_mult)
            for e in enemies:
                dmg = _calc_dmg(e, power)
                e["hp"] -= dmg
                msg_parts.append(format_damage_msg(player['name'], e['name'], dmg, element=skill.get('elemental'), skill_name=skill['name']))
                if random.random() < skill.get("stun_chance", 0):
                    from combat.status_effects import check_status_resisted as _resisted
                    if _resisted(e):
                        msg_parts.append(f"{e['name']} shrugs off the tremor!")
                    else:
                        e["stunned"] = True
                        msg_parts.append(f"{e['name']} is stunned!")
                if e["hp"] <= 0:
                    msg_parts.append(f"{e['name']} is buried!")
            if not [e for e in enemies if e["hp"] > 0]:
                victory = True

        # Cleave
        elif skill_id == "war_cleave":
            power = int((base_power + scaling) * power_mult)
            for e in enemies:
                dmg = _calc_dmg(e, power)
                e["hp"] -= dmg
                msg_parts.append(format_damage_msg(player['name'], e['name'], dmg, element=skill.get('elemental'), skill_name=skill['name']))
                if e["hp"] <= 0:
                    msg_parts.append(f"{e['name']} is defeated!")
            if not [e for e in enemies if e["hp"] > 0]:
                victory = True

        # Whirlwind
        elif skill_id == "bar_whirl":
            power = int((base_power + scaling) * power_mult)
            for e in enemies:
                dmg = _calc_dmg(e, power)
                e["hp"] -= dmg
                msg_parts.append(format_damage_msg(player['name'], e['name'], dmg, element=skill.get('elemental'), skill_name=skill['name']))
                if e["hp"] <= 0:
                    msg_parts.append(f"{e['name']} is defeated!")
            if not [e for e in enemies if e["hp"] > 0]:
                victory = True

        # Bladestorm
        elif skill_id == "war_bladestorm":
            for _ in range(skill.get("hits", 3)):
                live = [e for e in enemies if e["hp"] > 0]
                if not live:
                    break
                if len(live) > 1:
                    target = random.choice(live)
                else:
                    target = live[0]
                power = int((base_power + scaling) * power_mult)
                dmg = _calc_dmg(target, power)
                target["hp"] -= dmg
                msg_parts.append(format_damage_msg(player['name'], target['name'], dmg, element=skill.get('elemental'), skill_name=skill['name']))
                if target["hp"] <= 0:
                    msg_parts.append(f"{target['name']} is defeated!")
            if not [e for e in enemies if e["hp"] > 0]:
                victory = True

        # Shield Slam
        elif skill_id == "war_shield_slam":
            power = int((base_power + scaling) * power_mult)
            dmg = _calc_dmg(target, power)
            target["hp"] -= dmg
            msg_parts.append(format_damage_msg(player['name'], target['name'], dmg, element=skill.get('elemental'), skill_name=skill['name']))
            if random.random() < skill.get("stun_chance", 0):
                from combat.status_effects import check_status_resisted as _resisted
                if _resisted(target):
                    msg_parts.append(f"The {target['name']} shrugs off the impact!")
                else:
                    target["stunned"] = True
                    msg_parts.append(f"The {target['name']} is stunned!")
            if target["hp"] <= 0:
                msg_parts.append(f"{target['name']} is defeated!")
                victory = True
            _apply_life_steal(dmg)

        # Death Dance
        elif skill_id == "rog_death_dance":
            for _ in range(skill.get("hits", 3)):
                live = [e for e in enemies if e["hp"] > 0]
                if not live:
                    break
                if len(live) > 1:
                    target = random.choice(live)
                else:
                    target = live[0]
                power = int((base_power + scaling) * power_mult)
                dmg = _calc_dmg(target, power)
                target["hp"] -= dmg
                msg_parts.append(format_damage_msg(player['name'], target['name'], dmg, element=skill.get('elemental'), skill_name=skill['name']))
                if target["hp"] <= 0:
                    msg_parts.append(f"{target['name']} is defeated!")
                _apply_life_steal(dmg)
            if not [e for e in enemies if e["hp"] > 0]:
                victory = True

        # Nature's Grasp
        elif skill_id == "rng_nature":
            power = int((base_power + scaling) * power_mult)
            for e in enemies:
                dmg = _calc_dmg(e, power)
                e["hp"] -= dmg
                from combat.status_effects import apply_slow_to_enemy
                apply_slow_to_enemy(e, duration=3 + duration_bonus)
                msg_parts.append(format_damage_msg(player['name'], e['name'], dmg, element=skill.get('elemental'), skill_name=skill['name']) + " +Slowed")
                if e["hp"] <= 0:
                    msg_parts.append(f"{e['name']} is strangled!")
            if not [e for e in enemies if e["hp"] > 0]:
                victory = True

        # Death's Embrace
        elif skill_id == "rog_cap_deaths_embrace":
            hp_ratio = target["hp"] / target["max_hp"] if target["max_hp"] > 0 else 1
            if hp_ratio < 0.35:
                target["hp"] = 0
                msg_parts.append(f"DEATH'S EMBRACE! The {target['name']}'s life is claimed outright!")
                victory = True
            else:
                power = int((base_power + scaling) * power_mult)
                dmg = _calc_dmg(target, power)
                target["hp"] -= dmg
                msg_parts.append(format_damage_msg(player['name'], target['name'], dmg, element=skill.get('elemental'), skill_name=skill['name']))
                if target["hp"] <= 0:
                    msg_parts.append(f"{target['name']} is defeated!")
                    victory = True
                _apply_life_steal(dmg)
            if target["hp"] <= 0:
                player["refund_cooldown_skill"] = skill_id
                msg_parts.append("The kill fuels your momentum — Death's Embrace refreshes instantly!")

        # Heaven's Sword
        elif skill_id == "pal_cap_heavens_sword":
            power = int((base_power + scaling) * power_mult)
            dmg = _calc_dmg(target, power)
            target["hp"] -= dmg
            msg_parts.append(format_damage_msg(player['name'], target['name'], dmg, element=skill.get('elemental'), skill_name=skill['name']))
            if target["hp"] <= 0:
                msg_parts.append(f"{target['name']} is cleaved by heaven's light!")
                victory = True
            party = [player] + (allies or [])
            from combat.stat_milestones import get_wisdom_bonus
            heal_per = (dmg // max(1, len(party))) + get_wisdom_bonus(player)
            if heal_per > 0:
                for member in party:
                    if member.get("current_hp", 0) > 0:
                        old_hp = member.get("current_hp", 0)
                        max_hp = player_max_hp(member) if member is player else member.get("max_hp", old_hp)
                        member["current_hp"] = min(old_hp + heal_per, max_hp)
                msg_parts.append(f"Heaven's light washes over the party (+{heal_per} HP each).")
            _apply_life_steal(dmg)

        # Prismatic Ray (Evoker)
        elif skill_id == "mage_evo_prismatic_ray":
            from combat.elemental import ELEMENTS
            element = random.choice([el for el in ELEMENTS if el not in ("physical", "magical")])
            power = int((base_power + scaling) * power_mult)
            dmg = _calc_dmg(target, power, element=element)
            target["hp"] -= dmg
            msg_parts.append(format_damage_msg(player['name'], target['name'], dmg, element=element, skill_name=skill['name']))
            if target["hp"] <= 0:
                msg_parts.append(f"{target['name']} is unmade by prismatic light!")
                victory = True
            _apply_life_steal(dmg)

        # Mortal Blow (Assassin)
        elif skill_id == "rog_asm_mortal_blow":
            hp_ratio = target["hp"] / target["max_hp"] if target["max_hp"] > 0 else 1
            if hp_ratio < 0.25:
                target["hp"] = 0
                msg_parts.append(f"MORTAL BLOW! The {target['name']} is slain where it stands!")
                victory = True
            else:
                power = int((base_power + scaling) * power_mult)
                dmg = _calc_dmg(target, power, ignore_armor=True)
                target["hp"] -= dmg
                msg_parts.append(format_damage_msg(player['name'], target['name'], dmg, element=skill.get('elemental'), skill_name=skill['name']))
                if target["hp"] <= 0:
                    msg_parts.append(f"{target['name']} is defeated!")
                    victory = True
                _apply_life_steal(dmg)

        # Thousand Cuts (Assassin)
        elif skill_id == "rog_asm_thousand_cuts":
            power = int((base_power + scaling) * power_mult)
            for _ in range(skill.get("hits", 4)):
                if target["hp"] <= 0:
                    break
                dmg = _calc_dmg(target, power)
                target["hp"] -= dmg
                msg_parts.append(format_damage_msg(player['name'], target['name'], dmg, element=skill.get('elemental'), skill_name=skill['name']))
                _apply_life_steal(dmg)
            if target["hp"] <= 0:
                msg_parts.append(f"{target['name']} is reduced to ribbons!")
                victory = True

        # Killshot (Sharpshooter)
        elif skill_id == "rng_shp_killshot":
            hp_ratio = target["hp"] / target["max_hp"] if target["max_hp"] > 0 else 1
            if hp_ratio < 0.20:
                target["hp"] = 0
                msg_parts.append(f"KILLSHOT! The {target['name']} drops without a sound!")
                victory = True
            else:
                power = int((base_power + scaling) * power_mult)
                dmg = _calc_dmg(target, power, ignore_armor=True)
                target["hp"] -= dmg
                msg_parts.append(format_damage_msg(player['name'], target['name'], dmg, element=skill.get('elemental'), skill_name=skill['name']))
                if target["hp"] <= 0:
                    msg_parts.append(f"{target['name']} is defeated!")
                    victory = True
                _apply_life_steal(dmg)

        # Avenging Crusade (Crusader)
        elif skill_id == "pal_cru_avenging_crusade":
            max_hp = player_max_hp(player)
            missing = 0.0
            if max_hp > 0:
                missing = max(0.0, 1.0 - (player.get("current_hp", 0) / max_hp))
            power = int((base_power + scaling) * power_mult * (1 + missing))
            dmg = _calc_dmg(target, power)
            target["hp"] -= dmg
            msg_parts.append(format_damage_msg(player['name'], target['name'], dmg, element=skill.get('elemental'), skill_name=skill['name']))
            if missing > 0.2:
                msg_parts.append(f"Wounds fuel the crusade (+{int(missing * 100)}% damage)!")
            if target["hp"] <= 0:
                msg_parts.append(f"{target['name']} is vanquished!")
                victory = True
            _apply_life_steal(dmg)

        # Final Judgment (Crusader)
        elif skill_id == "pal_cru_final_judgment":
            power = int((base_power + scaling) * power_mult)
            dmg = _calc_dmg(target, power)
            target["hp"] -= dmg
            msg_parts.append(format_damage_msg(player['name'], target['name'], dmg, element=skill.get('elemental'), skill_name=skill['name']))
            if target["hp"] <= 0:
                msg_parts.append(f"{target['name']} is judged!")
                victory = True
            party = [player] + (allies or [])
            from combat.stat_milestones import get_wisdom_bonus
            heal_per = (dmg // max(1, len(party))) + get_wisdom_bonus(player)
            if heal_per > 0:
                for member in party:
                    if member.get("current_hp", 0) > 0:
                        old_hp = member.get("current_hp", 0)
                        max_hp = player_max_hp(member) if member is player else member.get("max_hp", old_hp)
                        member["current_hp"] = min(old_hp + heal_per, max_hp)
                msg_parts.append(f"The judgment mends the party (+{heal_per} HP each).")
            _apply_life_steal(dmg)

        # Generic fallback
        else:
            if target_type == "ally_or_self" and target:
                heal = int((base_power + scaling) * power_mult * get_passive_heal_bonus(player))
                old_hp = target.get("current_hp", 0)
                max_hp = player_max_hp(target) if target is player else target.get("max_hp", old_hp)
                target["current_hp"] = min(old_hp + heal, max_hp)
                actual = target["current_hp"] - old_hp
                name = "You" if target is player else display_name(target)
                msg_parts.append(f"{name} is healed for {actual} HP!")
            elif target:
                power = int((base_power + scaling) * power_mult)
                dmg = _calc_dmg(target, power, skill.get("ignore_armor", False))
                target["hp"] -= dmg
                msg_parts.append(format_damage_msg(player['name'], target['name'], dmg, element=skill.get('elemental'), skill_name=skill.get('name', 'Skill')))
                _apply_on_hit_effects(target)
                if target["hp"] <= 0:
                    msg_parts.append(f"{target['name']} is defeated!")
                    victory = True
                _apply_life_steal(dmg)

    # Adjust cooldown for mastery
    if cd_reduction > 0:
        cooldowns = player.get("skill_cooldowns", {})
        if skill_id in cooldowns:
            cooldowns[skill_id] = max(0, cooldowns[skill_id] - cd_reduction)
            if cooldowns[skill_id] <= 0:
                del cooldowns[skill_id]

    # ── Sky Piercer: execute non-superboss enemies left at/below threshold ──
    from combat.weapon.sky_piercer import check_sky_piercer_execute
    for i, e in enumerate(enemies):
        if i < len(pre_hp) and e["hp"] < pre_hp[i]:
            check_sky_piercer_execute(player, e, pre_hp[i] - e["hp"])
    # Victory is only valid if ALL enemies are defeated (covers executes too).
    victory = not any(e["hp"] > 0 for e in enemies)

    return " ".join(msg_parts), victory
