from combat.combat_io import c_print, c_input
# combat/ally_skills.py - Ally skill system: passive, innate, and learnable skills
import os
import yaml

from combat.helpers import format_damage_msg

# Maximum number of learnable skills an ally can have at once
MAX_LEARNED_SKILLS = 3


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
RACE_PASSIVES = _LEARNABLE_DATA.get("race_passives", {})
LEARNABLE_SKILLS = _LEARNABLE_DATA.get("learnable_skills", {})
HEROINE_PASSIVES = _LEARNABLE_DATA.get("heroine_passives", {})


def initialize_ally_skills(ally, enemy_key, race):
    """Initialize skill system for a newly created ally.
    
    Sets up:
    - passive_skill (race-based)
    - innate_skills (2 unique skills per monster girl)
    - learned_skills (starts empty)
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
    
    # Set innate skills (2 skills unique to this monster girl)
    if enemy_key in INNATE_SKILLS_MAP:
        ally["innate_skills"] = INNATE_SKILLS_MAP[enemy_key]
    else:
        ally["innate_skills"] = []
    
    # Initialize learnable skill system
    ally["learned_skills"] = ally.get("learned_skills", [])
    ally["learning"] = ally.get("learning", None)
    ally["skill_cooldowns"] = ally.get("skill_cooldowns", {})
    ally["skill_mastery"] = ally.get("skill_mastery", {})


def get_race_passive(race):
    """Return the passive skill definition for a race."""
    if race in RACE_PASSIVES:
        return RACE_PASSIVES[race]
    return None


def get_innate_skill_def(skill_id):
    """Return the skill definition for an innate skill."""
    return INNATE_SKILL_DEFS.get(skill_id, None)


def get_learnable_skill_def(skill_id):
    """Return the skill definition for a learnable skill.

    Falls back to innate skill definitions so that skills granted to
    learned_skills via special means (e.g. vorpal weapon upgrades like
    Frabjous Day, Through the Forest, Emerald City's Light) are still
    findable even though they're defined in innate_skills.yaml.
    """
    for category in LEARNABLE_SKILLS.values():
        if skill_id in category:
            return category[skill_id]
    # Fallback: check innate skill defs (covers vorpal upgrade skills)
    return INNATE_SKILL_DEFS.get(skill_id, None)


def get_all_available_skills(ally):
    """Return a list of all skills the ally can use (passive, innate, learned)."""
    skills = {
        "passive": get_race_passive(ally.get("race")) if ally.get("passive_skill") else None,
        "innate": [get_innate_skill_def(sid) for sid in ally.get("innate_skills", [])],
        "learned": [get_learnable_skill_def(sid) for sid in ally.get("learned_skills", [])]
    }
    return skills


def get_usable_skills_in_combat(ally):
    """Return list of skills the ally can actually use in combat (innate + learned, not on cooldown)."""
    cooldowns = ally.get("skill_cooldowns", {})
    usable = []
    
    # Innate skills
    for skill_id in ally.get("innate_skills", []):
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


def teach_ally_skill(ally, skill_id):
    """Start teaching an ally a new learnable skill.
    
    Can only learn one skill at a time. Replaces any current learning.
    Does NOT enforce the MAX_LEARNED_SKILLS cap — callers should check
    beforehand and use replace_ally_learned_skill() if at the cap.
    """
    skill_def = get_learnable_skill_def(skill_id)
    if not skill_def:
        return False
    
    # Can't re-learn already learned skills
    if skill_id in ally.get("learned_skills", []):
        return False
    
    # Check level requirement
    ally_level = ally.get("level", 1)
    required_level = skill_def.get("required_level", 1)
    if ally_level < required_level:
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
    """Return mastery level (0-3) for a skill based on uses."""
    mastery_exp = ally.get("skill_mastery", {}).get(skill_id, 0)
    if mastery_exp >= 50:
        return 3
    elif mastery_exp >= 25:
        return 2
    elif mastery_exp >= 10:
        return 1
    return 0


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
    """Return all innate + learned skills with definitions (including those on cooldown)."""
    skills = []
    for sid in ally.get("innate_skills", []):
        sdef = get_innate_skill_def(sid)
        if sdef:
            skills.append((sid, sdef))
    for sid in ally.get("learned_skills", []):
        sdef = get_learnable_skill_def(sid)
        if sdef:
            skills.append((sid, sdef))
    return skills

def format_ally_mastery_label(skill_id, ally):
    """Return a mastery label string for display."""
    level = get_ally_skill_mastery_level(ally, skill_id)
    labels = ["", "★", "★★", "★★★"]
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


def execute_ally_skill(ally, player, skill_id, skill_def, enemies, allies):
    """
    Execute an ally's innate or learned skill in combat.

    Returns: (result_message, victory)
    victory is True if all enemies were defeated.
    """
    import random
    from combat.ally import compute_ally_stats
    from combat.skills import get_mastery_bonuses
    from combat.status_effects import apply_poison, apply_burn, apply_shock, apply_barrier, apply_sleep, apply_haste, apply_paralyze, apply_regen, apply_entomb, apply_void_touched, apply_bleed, absorb_damage, wake_on_damage, apply_healing
    from character import player_max_hp

    # ── Palette heroine: custom kit (degraded boss moves) ──
    from combat.palette_ally import is_palette_ally
    if is_palette_ally(ally):
        if skill_id == "palette_signature":
            from combat.palette_ally import start_palette_signature
            ally.setdefault("skill_cooldowns", {})[skill_id] = skill_def.get("cooldown", 4)
            add_ally_skill_mastery_xp(ally, skill_id)
            return start_palette_signature(ally), False
        if skill_id == "palette_spectrum":
            from combat.palette_ally import palette_spectrum_attack
            ally.setdefault("skill_cooldowns", {})[skill_id] = skill_def.get("cooldown", 3)
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

    def _pick_party_target(allow_dead=False):
        party = [player] + allies
        if not allow_dead:
            party = [m for m in party if m.get("current_hp", 0) > 0]
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

    def _calc_dmg(target, power, ignore_armor=False, guaranteed_crit=False):
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
        if not guaranteed_crit:
            from combat.stats import roll_critical_hit, apply_critical_damage
            is_crit, _ = roll_critical_hit(ally, "ally", dex=a_dex, lrn=a_ler)
            if is_crit:
                power = apply_critical_damage(power, is_crit)
                msg_parts.append("Critical hit!")
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
        return dmg

    # ── Determine Target ──
    target = None
    if target_type == "enemy":
        target = _pick_enemy_target()
        if not target:
            return "No valid target.", False
    elif target_type == "self":
        target = ally
    elif target_type in ("ally_or_self", "dead_ally"):
        target = _pick_party_target(allow_dead=(target_type == "dead_ally"))
        if not target:
            return "No valid target.", False
    elif target_type in ("enemies", "all_allies"):
        target = None
    else:
        target = _pick_enemy_target()
        if not target:
            return "No valid target.", False

    # ── Effect-based Skills (non-damage) ──
    effect = skill_def.get("effect")
    if effect:
        effect_type = effect.get("type")
        duration = effect.get("duration", 3)
        value = effect.get("value", 0)

        if effect_type == "damage_reduction":
            pct_val = value if isinstance(value, float) and value <= 1 else value / 100.0
            recipients = [target] if target else [ally]
            if target_type == "all_allies":
                recipients = [player] + allies
            for r in recipients:
                r.setdefault("active_buffs", []).append({
                    "type": "defense_pct", "value": pct_val, "remaining": duration
                })
            pct_display = int(pct_val * 100)
            msg_parts.append(f"{ally['name']} takes {pct_display}% less damage for {duration} turns!")

        elif effect_type == "evasion":
            recipients = [target] if target else [ally]
            for r in recipients:
                r.setdefault("active_buffs", []).append({
                    "type": "evasion", "value": value, "remaining": duration
                })
            msg_parts.append(f"{ally['name']} gains evasion for {duration} turns!")

        elif effect_type == "power_buff":
            recipients = [target] if target else [ally]
            for r in recipients:
                r.setdefault("active_buffs", []).append({
                    "type": "power_buff", "value": value, "remaining": duration
                })
            msg_parts.append(f"{r.get('name', 'ally')}'s next action is empowered!")

        elif effect_type == "slow":
            live = [e for e in enemies if e["hp"] > 0]
            for e in live:
                e["slowed"] = True
                e.setdefault("active_debuffs", []).append({
                    "type": "slow", "remaining": duration
                })
            msg_parts.append(f"{ally['name']} slows all enemies!")

        elif effect_type == "blind":
            live = [e for e in enemies if e["hp"] > 0]
            for e in live:
                e["blinded"] = True
                e.setdefault("active_debuffs", []).append({
                    "type": "blind", "remaining": duration
                })
            msg_parts.append(f"{ally['name']} blinds the enemies!")

        elif effect_type == "stun":
            if target_type == "enemy" and target:
                target["stunned"] = True
                target.setdefault("active_debuffs", []).append({
                    "type": "stun", "remaining": duration
                })
                msg_parts.append(f"{target['name']} is stunned!")
            else:
                live = [e for e in enemies if e["hp"] > 0]
                for e in live:
                    e["stunned"] = True
                    e.setdefault("active_debuffs", []).append({
                        "type": "stun", "remaining": duration
                    })
                msg_parts.append(f"{ally['name']} stuns all enemies!")

        elif effect_type == "stat_debuff":
            stat = effect.get("stat", "Strength")
            if target_type == "enemy" and target:
                target.setdefault("active_debuffs", []).append({
                    "type": "curse", "penalty": value,
                    "remaining": duration, "stats": [stat]
                })
                msg_parts.append(f"{target['name']}'s {stat} is reduced by {value}!")
            else:
                live = [e for e in enemies if e["hp"] > 0]
                for e in live:
                    e.setdefault("active_debuffs", []).append({
                        "type": "curse", "penalty": value,
                        "remaining": duration, "stats": [stat]
                    })
                msg_parts.append(f"{ally['name']} reduces all enemies' {stat}!")

        elif effect_type == "regen":
            recipients = [target] if target else [ally]
            if target_type == "all_allies":
                recipients = [player] + allies
            for r in recipients:
                if isinstance(value, float) and value < 1:
                    regen_val = int(r.get("max_hp", 100) * value)
                else:
                    regen_val = value
                r.setdefault("active_buffs", []).append({
                    "type": "hot", "value": regen_val, "remaining": duration
                })
            msg_parts.append(f"{ally['name']} grants regeneration for {duration} turns!")

        elif effect_type == "stat_buff":
            stat = effect.get("stat", "Strength")
            recipients = [target] if target else [ally]
            if target_type == "all_allies":
                recipients = [player] + allies
            for r in recipients:
                r.setdefault("active_buffs", []).append({
                    "stat": stat, "value": value, "remaining": duration
                })
            msg_parts.append(f"{ally['name']} raises {stat} for {duration} turns!")

        elif effect_type == "cooldown_reduction":
            recipients = [target] if target else [ally]
            for r in recipients:
                r.setdefault("active_buffs", []).append({
                    "type": "cooldown_reduction", "value": value, "remaining": duration
                })
            target_name = target.get("name", "Ally") if target else ally["name"]
            msg_parts.append(f"{target_name}'s next skill cooldown reduced by {value}!")

        elif effect_type == "reflection":
            recipients = [target] if target else [ally]
            for r in recipients:
                r.setdefault("active_buffs", []).append({
                    "type": "reflection", "value": value, "remaining": duration
                })
            msg_parts.append(f"{ally['name']} will reflect damage!")

        elif effect_type == "perfect_guard":
            recipients = [target] if target else [ally]
            if target_type == "all_allies":
                recipients = [player] + allies
            pct_val = value if isinstance(value, float) and value <= 1 else value / 100.0
            for r in recipients:
                r.setdefault("active_buffs", []).append({
                    "type": "defense_pct", "value": pct_val, "remaining": duration
                })
                r.setdefault("active_buffs", []).append({
                    "type": "reflection", "value": effect.get("reflect_value", 0.3), "remaining": duration
                })
            pct_display = int(pct_val * 100)
            msg_parts.append(f"{ally['name']} raises a perfect guard! ({pct_display}% less damage)")

        elif effect_type == "phantom_dodge":
            recipients = [target] if target else [ally]
            for r in recipients:
                r.setdefault("active_buffs", []).append({
                    "type": "evasion", "value": value, "remaining": duration
                })
                r.setdefault("active_buffs", []).append({
                    "stat": "Dexterity", "value": effect.get("dex_bonus", 3), "remaining": duration
                })
            msg_parts.append(f"{ally['name']} becomes a phantom!")

        elif effect_type == "confusion":
            live = [e for e in enemies if e["hp"] > 0]
            for e in live:
                e["confused"] = True
                e.setdefault("active_debuffs", []).append({
                    "type": "confusion", "value": value, "remaining": duration
                })
            msg_parts.append(f"{ally['name']} confuses the enemies!")

        elif effect_type == "shock":
            if target and target_type == "enemy":
                apply_shock(target, value, duration)
                msg_parts.append(f"{target['name']} is shocked!")
            else:
                live = [e for e in enemies if e["hp"] > 0]
                for e in live:
                    apply_shock(e, value, duration)
                msg_parts.append(f"{ally['name']} shocks all enemies!")

        elif effect_type == "barrier":
            recipients = [target] if target else [ally]
            if target_type == "all_allies":
                recipients = [player] + allies
            for r in recipients:
                apply_barrier(r, value, duration)
            msg_parts.append(f"{ally['name']} grants a barrier for {duration} turns!")

        elif effect_type == "haste":
            recipients = [target] if target else [ally]
            if target_type == "all_allies":
                recipients = [player] + allies
            for r in recipients:
                apply_haste(r, duration, effect.get("init_bonus", 3), effect.get("cd_reduction", 1))
            msg_parts.append(f"{ally['name']} grants haste for {duration} turns!")

        elif effect_type == "sleep":
            if target and target_type == "enemy":
                apply_sleep(target, duration)
                msg_parts.append(f"{target['name']} falls asleep!")
            else:
                live = [e for e in enemies if e["hp"] > 0]
                for e in live:
                    apply_sleep(e, duration)
                msg_parts.append(f"{ally['name']} lulls all enemies to sleep!")

        elif effect_type == "paralyze":
            if target and target_type == "enemy":
                apply_paralyze(target, duration)
                msg_parts.append(f"{target['name']} is paralyzed!")
            else:
                live = [e for e in enemies if e["hp"] > 0]
                for e in live:
                    apply_paralyze(e, duration)
                msg_parts.append(f"{ally['name']} paralyzes all enemies!")

        elif effect_type == "regen":
            recipients = [target] if target else [ally]
            if target_type == "all_allies":
                recipients = [player] + allies
            for r in recipients:
                apply_regen(r, value, duration)
            msg_parts.append(f"{ally['name']} grants regeneration for {duration} turns!")

        elif effect_type == "entomb":
            if target and target_type == "enemy":
                apply_entomb(target, duration)
                msg_parts.append(f"{target['name']} is entombed in stone!")
            else:
                live = [e for e in enemies if e["hp"] > 0]
                for e in live:
                    apply_entomb(e, duration)
                msg_parts.append(f"{ally['name']} entombs all enemies in stone!")

        elif effect_type == "void_touched":
            if target and target_type == "enemy":
                apply_void_touched(target, duration)
                msg_parts.append(f"{target['name']} is void-touched!")
            else:
                live = [e for e in enemies if e["hp"] > 0]
                for e in live:
                    apply_void_touched(e, duration)
                msg_parts.append(f"{ally['name']} curses all enemies with void touch!")

        elif effect_type == "life_steal":
            # Handled during damage calculation below; mark for post-damage heal
            pass

        elif effect_type == "random_buff":
            options = effect.get("options", [])
            if options:
                chosen = random.choice(options)
                opt_type = chosen.get("type")
                opt_value = chosen.get("value", 0)
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
            for r in recipients:
                r.setdefault("active_buffs", []).append({
                    "type": "damage_boost", "value": value, "remaining": duration
                })
            msg_parts.append(f"{ally['name']} grants +{int(value * 100)}% damage for {duration} turns!")

        elif effect_type == "elemental_weakness":
            if target_type == "enemy" and target:
                target.setdefault("active_debuffs", []).append({
                    "type": "elemental_weakness", "value": value, "remaining": duration
                })
                msg_parts.append(f"{target['name']}'s elemental resistances are lowered — +{int(value * 100)}% weakness!")
                # Also apply stat debuff if specified
                stat_debuff = effect.get("stat_debuff")
                stat_value = effect.get("stat_value")
                if stat_debuff and stat_value:
                    target.setdefault("active_debuffs", []).append({
                        "type": "curse", "penalty": stat_value,
                        "remaining": duration, "stats": [stat_debuff]
                    })
                    msg_parts.append(f"{target['name']}'s {stat_debuff} reduced by {abs(stat_value)}!")
            else:
                live = [e for e in enemies if e["hp"] > 0]
                for e in live:
                    e.setdefault("active_debuffs", []).append({
                        "type": "elemental_weakness", "value": value, "remaining": duration
                    })
                msg_parts.append(f"All enemies' elemental resistances lowered!")

        elif effect_type == "marked":
            if target_type == "enemy" and target:
                target["hunters_mark"] = True
                target["hunters_mark_bonus"] = value
                target["hunters_mark_source"] = ally.get("name", "Ally")
                target["hunters_mark_turns"] = duration
                msg_parts.append(f"{ally['name']} marks {target['name']}! +{int(value * 100)}% damage taken for {duration} turns!")

        elif effect_type == "multi":
            # Handle nested effects (e.g. Through the Forest: crit_boost + fear_immunity)
            nested = effect.get("effects", [])
            recipients = [target] if target else [ally]
            if target_type == "all_allies":
                recipients = [player] + allies
            for sub in nested:
                sub_type = sub.get("type")
                sub_value = sub.get("value", 0)
                sub_duration = sub.get("duration", duration)
                if sub_type == "crit_boost":
                    for r in recipients:
                        r.setdefault("active_buffs", []).append({
                            "type": "crit_chance", "value": sub_value, "remaining": sub_duration
                        })
                    msg_parts.append(f"{ally['name']} grants +{int(sub_value * 100)}% crit chance for {sub_duration} turns!")
                elif sub_type == "fear_immunity":
                    for r in recipients:
                        r.setdefault("active_buffs", []).append({
                            "type": "fear_immunity", "remaining": sub_duration
                        })
                    msg_parts.append(f"{ally['name']} grants Fear immunity for {sub_duration} turns!")
                elif sub_type == "stat_buff":
                    stat = sub.get("stat", "Strength")
                    for r in recipients:
                        r.setdefault("active_buffs", []).append({
                            "stat": stat, "value": sub_value, "remaining": sub_duration
                        })

        # If this skill has no damage component and only an effect, finish here
        if base_power == 0 and not any(k in skill_def for k in (
            "poison_damage", "burn_damage", "bleed_damage", "stun_chance", "guaranteed_crit",
            "ignore_armor", "apply_slow", "apply_weaken", "crit_bonus",
            "ignore_armor_pct", "bonus_vs_races", "push_initiative",
            "shock_damage", "apply_sleep", "apply_paralyze", "apply_entomb",
            "apply_void_touched"
        )):
            cooldown = skill_def.get("cooldown", 1)
            ally.setdefault("skill_cooldowns", {})[skill_id] = max(0, cooldown - cd_reduction)
            add_ally_skill_mastery_xp(ally, skill_id)
            return " ".join(msg_parts), False

    # ── Damage / Heal Calculation ──
    power = int((base_power + scaling) * power_mult)

    # Consume power_buff if present (empowers next action)
    for buff in ally.get("active_buffs", [])[:]:
        if buff.get("type") == "power_buff":
            power = int(power * (1 + buff.get("value", 0)))
            msg_parts.append(f"Empowered! Damage increased by {int(buff.get('value', 0) * 100)}%!")
            ally["active_buffs"].remove(buff)
            break

    guaranteed = skill_def.get("guaranteed_crit", False)
    crit_bonus = skill_def.get("crit_bonus", 0)
    if guaranteed:
        power *= 2
        msg_parts.append("Critical hit!")
    elif crit_bonus > 0 and random.random() < crit_bonus:
        power *= 2
        msg_parts.append("Critical hit!")

    # Multi-target enemy damage
    if target_type == "enemies":
        live = [e for e in enemies if e["hp"] > 0]
        total_dmg = 0
        for e in live:
            dmg = _calc_dmg(e, power, skill_def.get("ignore_armor", False), guaranteed_crit=guaranteed)
            e["hp"] -= dmg
            msg_parts.append(format_damage_msg(ally['name'], e['name'], dmg, element=skill_def.get("elemental"), skill_name=skill_def['name']))
            total_dmg += dmg
            if e["hp"] <= 0:
                msg_parts.append(f"{e['name']} is defeated!")
            # Status effects
            if skill_def.get("poison_damage"):
                p_dmg = skill_def["poison_damage"]
                if extra_effect:
                    p_dmg = int(p_dmg * 1.5)
                apply_poison(e, p_dmg, skill_def.get("poison_duration", 3))
                msg_parts.append(f"{e['name']} is poisoned!")
            if skill_def.get("burn_damage"):
                b_dmg = skill_def["burn_damage"]
                if extra_effect:
                    b_dmg = int(b_dmg * 1.5)
                from combat.status_effects import damage_to_burn_tier
                b_tier = damage_to_burn_tier(b_dmg)
                apply_burn(e, b_tier, skill_def.get("burn_duration", 3))
                msg_parts.append(f"{e['name']} is burning!")
            if skill_def.get("bleed_damage"):
                bl_dmg = skill_def["bleed_damage"]
                if extra_effect:
                    bl_dmg = int(bl_dmg * 1.5)
                apply_bleed(e, bl_dmg, skill_def.get("bleed_duration", 4))
                msg_parts.append(f"{e['name']} is bleeding!")
            if skill_def.get("stun_chance") and random.random() < skill_def["stun_chance"]:
                e["stunned"] = True
                e.setdefault("active_debuffs", []).append({"type": "stun", "remaining": 3})
                msg_parts.append(f"{e['name']} is stunned!")
            if skill_def.get("apply_slow"):
                e["slowed"] = True
                e.setdefault("active_debuffs", []).append({"type": "slow", "remaining": 3})
                msg_parts.append(f"{e['name']} is slowed!")
            if skill_def.get("apply_weaken"):
                e.setdefault("active_debuffs", []).append({
                    "type": "weaken", "value": 2, "remaining": 3
                })
                msg_parts.append(f"{e['name']} is weakened!")
            if skill_def.get("shock_damage"):
                apply_shock(e, skill_def["shock_damage"], skill_def.get("shock_duration", 3))
                msg_parts.append(f"{e['name']} is shocked!")
            if skill_def.get("apply_sleep"):
                apply_sleep(e, skill_def.get("sleep_duration", 3))
                msg_parts.append(f"{e['name']} falls asleep!")
            if skill_def.get("apply_paralyze"):
                apply_paralyze(e, skill_def.get("paralyze_duration", 2))
                msg_parts.append(f"{e['name']} is paralyzed!")
            if skill_def.get("apply_entomb"):
                apply_entomb(e, skill_def.get("entomb_duration", 3))
                msg_parts.append(f"{e['name']} is entombed!")
            if skill_def.get("apply_void_touched"):
                apply_void_touched(e, skill_def.get("void_touched_duration", 2))
                msg_parts.append(f"{e['name']} is void-touched!")
        # Push initiative: push enemies to bottom of initiative order
        if skill_def.get("push_initiative"):
            msg_parts.append(f"{ally['name']} pushes enemies to the bottom of initiative!")
            # Signal to combat engine to move enemies to end of turn order
            ally["_push_initiative_flag"] = True

        if not [e for e in enemies if e["hp"] > 0]:
            victory = True
        # Life steal
        if effect and effect.get("type") == "life_steal" and total_dmg > 0:
            ls = effect.get("value", 0)
            heal = int(total_dmg * ls)
            old_hp = ally["current_hp"]
            ally["current_hp"] = min(old_hp + heal, ally["max_hp"])
            actual = ally["current_hp"] - old_hp
            if actual > 0:
                msg_parts.append(f"{ally['name']} recovers {actual} HP!")
        # Race passive life steal
        race_passive = get_race_passive(ally.get("race"))
        if race_passive:
            rp_effect = race_passive.get("effect", {})
            if rp_effect.get("type") == "life_steal" and total_dmg > 0:
                ls = rp_effect.get("value", 0)
                heal = int(total_dmg * ls)
                old_hp = ally["current_hp"]
                ally["current_hp"] = min(old_hp + heal, ally["max_hp"])
                actual = ally["current_hp"] - old_hp
                if actual > 0:
                    msg_parts.append(f"[{race_passive['name']}] {ally['name']} recovers {actual} HP!")

    # Single-target enemy damage
    elif target_type == "enemy" and target:
        hits = skill_def.get("hits", 1)
        for _ in range(hits):
            dmg = _calc_dmg(target, power, skill_def.get("ignore_armor", False), guaranteed_crit=guaranteed)
            target["hp"] -= dmg
            msg_parts.append(format_damage_msg(ally['name'], target['name'], dmg, element=skill_def.get("elemental"), skill_name=skill_def['name']))
            # Wake sleeping enemy on damage
            wake_msg = wake_on_damage(target)
            if wake_msg:
                msg_parts.append(wake_msg)
            if target["hp"] <= 0:
                msg_parts.append(f"{target['name']} is defeated!")
                victory = True
                break
            # Status effects
            if skill_def.get("poison_damage"):
                p_dmg = skill_def["poison_damage"]
                if extra_effect:
                    p_dmg = int(p_dmg * 1.5)
                apply_poison(target, p_dmg, skill_def.get("poison_duration", 3))
                msg_parts.append(f"{target['name']} is poisoned!")
            if skill_def.get("burn_damage"):
                b_dmg = skill_def["burn_damage"]
                if extra_effect:
                    b_dmg = int(b_dmg * 1.5)
                from combat.status_effects import damage_to_burn_tier
                b_tier = damage_to_burn_tier(b_dmg)
                apply_burn(target, b_tier, skill_def.get("burn_duration", 3))
                msg_parts.append(f"{target['name']} is burning!")
            if skill_def.get("bleed_damage"):
                bl_dmg = skill_def["bleed_damage"]
                if extra_effect:
                    bl_dmg = int(bl_dmg * 1.5)
                apply_bleed(target, bl_dmg, skill_def.get("bleed_duration", 4))
                msg_parts.append(f"{target['name']} is bleeding!")
            if skill_def.get("stun_chance") and random.random() < skill_def["stun_chance"]:
                target["stunned"] = True
                target.setdefault("active_debuffs", []).append({"type": "stun", "remaining": 3})
                msg_parts.append(f"{target['name']} is stunned!")
            if skill_def.get("apply_slow"):
                target["slowed"] = True
                target.setdefault("active_debuffs", []).append({"type": "slow", "remaining": 3})
                msg_parts.append(f"{target['name']} is slowed!")
            if skill_def.get("apply_weaken"):
                target.setdefault("active_debuffs", []).append({
                    "type": "weaken", "value": 2, "remaining": 3
                })
                msg_parts.append(f"{target['name']} is weakened!")
            if skill_def.get("shock_damage"):
                apply_shock(target, skill_def["shock_damage"], skill_def.get("shock_duration", 3))
                msg_parts.append(f"{target['name']} is shocked!")
            if skill_def.get("apply_sleep"):
                apply_sleep(target, skill_def.get("sleep_duration", 3))
                msg_parts.append(f"{target['name']} falls asleep!")
            if skill_def.get("apply_paralyze"):
                apply_paralyze(target, skill_def.get("paralyze_duration", 2))
                msg_parts.append(f"{target['name']} is paralyzed!")
            if skill_def.get("apply_entomb"):
                apply_entomb(target, skill_def.get("entomb_duration", 3))
                msg_parts.append(f"{target['name']} is entombed!")
            if skill_def.get("apply_void_touched"):
                apply_void_touched(target, skill_def.get("void_touched_duration", 2))
                msg_parts.append(f"{target['name']} is void-touched!")
        # Push initiative: push enemies to bottom of initiative order
        if skill_def.get("push_initiative"):
            msg_parts.append(f"{ally['name']} pushes enemies to the bottom of initiative!")
            ally["_push_initiative_flag"] = True
            # Life steal
            if effect and effect.get("type") == "life_steal" and dmg > 0:
                ls = effect.get("value", 0)
                heal = int(dmg * ls)
                old_hp = ally["current_hp"]
                ally["current_hp"] = min(old_hp + heal, ally["max_hp"])
                actual = ally["current_hp"] - old_hp
                if actual > 0:
                    msg_parts.append(f"{ally['name']} recovers {actual} HP!")
            # Race passive life steal
            race_passive = get_race_passive(ally.get("race"))
            if race_passive:
                rp_effect = race_passive.get("effect", {})
                if rp_effect.get("type") == "life_steal" and dmg > 0:
                    ls = rp_effect.get("value", 0)
                    heal = int(dmg * ls)
                    old_hp = ally["current_hp"]
                    ally["current_hp"] = min(old_hp + heal, ally["max_hp"])
                    actual = ally["current_hp"] - old_hp
                    if actual > 0:
                        msg_parts.append(f"[{race_passive['name']}] {ally['name']} recovers {actual} HP!")

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
                healed = apply_healing(member, heal)
                if healed < 0:
                    msg_parts.append(f"The void twists the healing! {member.get('name', 'Ally')} takes {-healed} damage instead!")
                total_heal += max(0, healed)
                # Cleanse all debuffs if skill has cleanse_all_debuffs
                if skill_def.get("cleanse_all_debuffs") and member.get("active_debuffs"):
                    for d in list(member.get("active_debuffs", [])):
                        _clear_flat_debuff_flag(member, d.get("type"))
                    member["active_debuffs"] = []
                    name = "You" if member is player else member.get("name", "Ally")
                    msg_parts.append(f"{name}'s debuffs are all cleansed!")
                # Cleanse one debuff per ally if skill has cleanse_one_debuff
                elif skill_def.get("cleanse_one_debuff") and member.get("active_debuffs"):
                    removed = member["active_debuffs"].pop(0)
                    _clear_flat_debuff_flag(member, removed.get("type"))
                    name = "You" if member is player else member.get("name", "Ally")
                    msg_parts.append(f"{name}'s {removed.get('type', 'debuff')} cleansed!")
            if total_heal > 0:
                msg_parts.append(f"Total healing: {total_heal} HP!")
        elif target_type == "dead_ally":
            if target:
                max_hp = player_max_hp(target) if target is player else target.get("max_hp", 1)
                revive_hp = int(max_hp * skill_def.get("revive_percent", 0.50))
                target["current_hp"] = revive_hp
                name = target.get("name", "Ally")
                msg_parts.append(f"{name} is resurrected with {revive_hp} HP!")
        else:
            if target:
                max_hp = player_max_hp(target) if target is player else target.get("max_hp", target.get("current_hp", 1))
                if heal_percent:
                    heal = int(max_hp * heal_percent)
                else:
                    from combat.stat_milestones import get_wisdom_bonus
                    heal = int((base_power + scaling) * power_mult) + get_wisdom_bonus(ally)
                old_hp = target.get("current_hp", 0)
                actual = apply_healing(target, heal)
                name = target.get("name", ally["name"])
                if actual < 0:
                    msg_parts.append(f"The void twists the healing! {name} takes {-actual} damage instead!")
                else:
                    msg_parts.append(f"{name} is healed for {actual} HP!")
                # Cleanse all debuffs if applicable
                if skill_def.get("cleanse_all_debuffs") and target.get("active_debuffs"):
                    for d in list(target.get("active_debuffs", [])):
                        _clear_flat_debuff_flag(target, d.get("type"))
                    target["active_debuffs"] = []
                    msg_parts.append(f"{name}'s debuffs are all cleansed!")
                # Cleanse one debuff if applicable
                elif skill_def.get("cleanse_one_debuff") and target.get("active_debuffs"):
                    removed = target["active_debuffs"].pop(0)
                    _clear_flat_debuff_flag(target, removed.get("type"))
                    msg_parts.append(f"{name}'s {removed.get('type', 'debuff')} cleansed!")

    # ── Cooldown & Mastery ──
    cooldown = skill_def.get("cooldown", 1)

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
_VORPAL_UPGRADE_SKILL = "frabjous_day"
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
    
    Also removes the upgraded Frabjous Day skill if present.
    """
    if ally.get("_heroine_key") != "alice":
        return

    if not ally.get("_alice_vorpal_skills"):
        return

    original = ally.get("_alice_original_innate", _ALICE_NORMAL_INNATE)
    ally["innate_skills"] = list(original)
    ally["_alice_vorpal_skills"] = False
    ally.pop("_alice_original_innate", None)

    # Remove Frabjous Day from learned skills if present
    if _VORPAL_UPGRADE_SKILL in ally.get("learned_skills", []):
        ally["learned_skills"].remove(_VORPAL_UPGRADE_SKILL)
    ally.pop("_alice_vorpal_upgraded", None)

    # Clear cooldowns on skill swap
    ally["skill_cooldowns"] = {}


def grant_vorpal_upgrade_skill(ally):
    """Grant Frabjous Day to Alice after Vorpal Blade upgrade.
    
    Adds it as a learned skill so it persists through save/load.
    Only effective if Alice already has vorpal skills active.
    """
    if ally.get("_heroine_key") != "alice":
        return

    if not ally.get("_alice_vorpal_skills"):
        return

    if _VORPAL_UPGRADE_SKILL not in ally.get("learned_skills", []):
        ally.setdefault("learned_skills", []).append(_VORPAL_UPGRADE_SKILL)

    ally["_alice_vorpal_upgraded"] = True


# ══════════════════════════════════════════════════════════════════════════════
# Grandmother's Axe — Red Hood Skill Swap System
# ══════════════════════════════════════════════════════════════════════════════

_REDHOOD_VORPAL_INNATE = ["what_big_teeth", "fell_the_wolf"]
_REDHOOD_UPGRADE_SKILL = "through_the_forest"
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
    """Restore Red Hood's original innate skills."""
    if ally.get("_heroine_key") != "red_hood":
        return
    if not ally.get("_redhood_vorpal_skills"):
        return
    original = ally.get("_redhood_original_innate", _REDHOOD_NORMAL_INNATE)
    ally["innate_skills"] = list(original)
    ally["_redhood_vorpal_skills"] = False
    ally.pop("_redhood_original_innate", None)
    if _REDHOOD_UPGRADE_SKILL in ally.get("learned_skills", []):
        ally["learned_skills"].remove(_REDHOOD_UPGRADE_SKILL)
    ally.pop("_redhood_vorpal_upgraded", None)
    ally["skill_cooldowns"] = {}


def grant_redhood_upgrade_skill(ally):
    """Grant Through the Forest to Red Hood after Grandmother's Axe upgrade."""
    if ally.get("_heroine_key") != "red_hood":
        return
    if not ally.get("_redhood_vorpal_skills"):
        return
    if _REDHOOD_UPGRADE_SKILL not in ally.get("learned_skills", []):
        ally.setdefault("learned_skills", []).append(_REDHOOD_UPGRADE_SKILL)
    ally["_redhood_vorpal_upgraded"] = True


# ══════════════════════════════════════════════════════════════════════════════
# Silver/Ruby Slippers — Dorothy Skill Swap System
# ══════════════════════════════════════════════════════════════════════════════

_DOROTHY_VORPAL_INNATE = ["cyclones_call", "heart_of_tin"]
_DOROTHY_UPGRADE_SKILL = "emerald_citys_light"
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
    """Restore Dorothy's original innate skills."""
    if ally.get("_heroine_key") != "dorothy":
        return
    if not ally.get("_dorothy_vorpal_skills"):
        return
    original = ally.get("_dorothy_original_innate", _DOROTHY_NORMAL_INNATE)
    ally["innate_skills"] = list(original)
    ally["_dorothy_vorpal_skills"] = False
    ally.pop("_dorothy_original_innate", None)
    if _DOROTHY_UPGRADE_SKILL in ally.get("learned_skills", []):
        ally["learned_skills"].remove(_DOROTHY_UPGRADE_SKILL)
    ally.pop("_dorothy_vorpal_upgraded", None)
    ally["skill_cooldowns"] = {}


def grant_dorothy_upgrade_skill(ally):
    """Grant Emerald City's Light to Dorothy after Ruby Slippers upgrade."""
    if ally.get("_heroine_key") != "dorothy":
        return
    if not ally.get("_dorothy_vorpal_skills"):
        return
    if _DOROTHY_UPGRADE_SKILL not in ally.get("learned_skills", []):
        ally.setdefault("learned_skills", []).append(_DOROTHY_UPGRADE_SKILL)
    ally["_dorothy_vorpal_upgraded"] = True
