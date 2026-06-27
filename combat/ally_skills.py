# combat/ally_skills.py - Ally skill system: passive, innate, and learnable skills
import os
import yaml

from resources.skill_loader import PASSIVE_SKILLS, CLASS_SKILLS


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
    """Return the skill definition for a learnable skill."""
    for category in LEARNABLE_SKILLS.values():
        if skill_id in category:
            return category[skill_id]
    return None


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
    """
    skill_def = get_learnable_skill_def(skill_id)
    if not skill_def:
        return False
    
    # Can't re-learn already learned skills
    if skill_id in ally.get("learned_skills", []):
        return False
    
    # Start learning this skill
    exp_needed = 300  # Base exp needed to learn a skill
    ally["learning"] = {
        "skill_id": skill_id,
        "exp": 0,
        "exp_needed": exp_needed
    }
    return True


def gain_skill_learning_exp(ally, amount):
    """Add experience to the skill currently being learned."""
    if not ally.get("learning"):
        return None  # Not learning anything
    
    learning_info = ally["learning"]
    learning_info["exp"] += amount
    
    # Check if skill is learned
    if learning_info["exp"] >= learning_info["exp_needed"]:
        skill_id = learning_info["skill_id"]
        # Move to learned skills
        ally.setdefault("learned_skills", []).append(skill_id)
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


def execute_ally_skill(ally, player, skill_id, skill_def, enemies, allies):
    """
    Execute an ally's innate or learned skill in combat.

    Returns: (result_message, victory)
    victory is True if all enemies were defeated.
    """
    import random
    from combat.ally import compute_ally_stats
    from combat.skills import get_mastery_bonuses
    from combat.status_effects import apply_poison, apply_burn
    from character import player_max_hp

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

    # ── Target Selection Helpers ──
    def _pick_enemy_target():
        live = [e for e in enemies if e["hp"] > 0]
        if not live:
            return None
        if len(live) == 1:
            return live[0]
        print(f"  Select target for {skill_def['name']}:")
        for i, e in enumerate(live):
            print(f"    {i+1}. {e['name']} (HP: {e['hp']}/{e['max_hp']})")
        try:
            choice = int(input("  Choice: ")) - 1
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
        print("  Select target:")
        for i, m in enumerate(party):
            name = m.get("name", "You") if m is player else m.get("name", "Ally")
            hp = m.get("current_hp", 0)
            max_hp = m.get("max_hp", 1)
            status = " [FALLEN]" if m.get("current_hp", 1) <= 0 else ""
            print(f"    {i+1}. {name} ({hp}/{max_hp}){status}")
        try:
            choice = int(input("  Choice: ")) - 1
            if 0 <= choice < len(party):
                return party[choice]
        except ValueError:
            pass
        return None

    def _calc_dmg(target, power, ignore_armor=False):
        armor = 0 if ignore_armor else target.get("con_mod", 0)
        for debuff in target.get("active_debuffs", []):
            if debuff.get("type") == "sunder":
                armor = max(0, armor - debuff.get("value", 0))
        return max(1, power - armor)

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
            flat_val = int(value * 10) if isinstance(value, float) and value < 1 else value
            recipients = [target] if target else [ally]
            if target_type == "all_allies":
                recipients = [player] + allies
            for r in recipients:
                r.setdefault("active_buffs", []).append({
                    "type": "defense", "value": flat_val, "remaining": duration
                })
            msg_parts.append(f"{ally['name']}'s defense increases for {duration} turns!")

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
            regen_val = int(target.get("max_hp", 100) * value) if isinstance(value, float) and value < 1 else value
            recipients = [target] if target else [ally]
            if target_type == "all_allies":
                recipients = [player] + allies
            for r in recipients:
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
            msg_parts.append(f"{ally['name']} reduces skill cooldowns!")

        elif effect_type == "reflection":
            recipients = [target] if target else [ally]
            for r in recipients:
                r.setdefault("active_buffs", []).append({
                    "type": "reflection", "value": value, "remaining": duration
                })
            msg_parts.append(f"{ally['name']} will reflect damage!")

        elif effect_type == "confusion":
            live = [e for e in enemies if e["hp"] > 0]
            for e in live:
                e.setdefault("active_debuffs", []).append({
                    "type": "confusion", "value": value, "remaining": duration
                })
            msg_parts.append(f"{ally['name']} confuses the enemies!")

        elif effect_type == "life_steal":
            # Handled during damage calculation below; mark for post-damage heal
            pass

        # If this skill has no damage component and only an effect, finish here
        if base_power == 0 and not any(k in skill_def for k in (
            "poison_damage", "burn_damage", "stun_chance", "guaranteed_crit",
            "ignore_armor", "apply_slow", "apply_weaken"
        )):
            cooldown = skill_def.get("cooldown", 1)
            ally.setdefault("skill_cooldowns", {})[skill_id] = max(0, cooldown - cd_reduction)
            add_ally_skill_mastery_xp(ally, skill_id)
            return " ".join(msg_parts), False

    # ── Damage / Heal Calculation ──
    power = int((base_power + scaling) * power_mult)
    if skill_def.get("guaranteed_crit"):
        power *= 2
        msg_parts.append("Critical hit!")

    # Multi-target enemy damage
    if target_type == "enemies":
        live = [e for e in enemies if e["hp"] > 0]
        total_dmg = 0
        for e in live:
            dmg = _calc_dmg(e, power, skill_def.get("ignore_armor", False))
            e["hp"] -= dmg
            msg_parts.append(f"{skill_def['name']} hits {e['name']} for {dmg} damage!")
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
                apply_burn(e, b_dmg, skill_def.get("burn_duration", 3))
                msg_parts.append(f"{e['name']} is burning!")
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

    # Single-target enemy damage
    elif target_type == "enemy" and target:
        dmg = _calc_dmg(target, power, skill_def.get("ignore_armor", False))
        target["hp"] -= dmg
        msg_parts.append(f"{skill_def['name']} deals {dmg} damage to {target['name']}!")
        if target["hp"] <= 0:
            msg_parts.append(f"{target['name']} is defeated!")
            victory = True
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
            apply_burn(target, b_dmg, skill_def.get("burn_duration", 3))
            msg_parts.append(f"{target['name']} is burning!")
        if skill_def.get("stun_chance") and random.random() < skill_def["stun_chance"]:
            target["stunned"] = True
            target.setdefault("active_debuffs", []).append({"type": "stun", "remaining": 3})
            msg_parts.append(f"{target['name']} is stunned!")
        # Life steal
        if effect and effect.get("type") == "life_steal" and dmg > 0:
            ls = effect.get("value", 0)
            heal = int(dmg * ls)
            old_hp = ally["current_hp"]
            ally["current_hp"] = min(old_hp + heal, ally["max_hp"])
            actual = ally["current_hp"] - old_hp
            if actual > 0:
                msg_parts.append(f"{ally['name']} recovers {actual} HP!")

    # Healing skills
    elif target_type in ("self", "ally_or_self", "all_allies", "dead_ally"):
        if target_type == "all_allies":
            party = [player] + allies
            total_heal = 0
            for member in party:
                if member.get("current_hp", 0) <= 0:
                    continue
                heal = int((base_power + scaling) * power_mult)
                old_hp = member.get("current_hp", 0)
                max_hp = player_max_hp(member) if member is player else member.get("max_hp", old_hp)
                member["current_hp"] = min(old_hp + heal, max_hp)
                total_heal += member["current_hp"] - old_hp
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
                heal = int((base_power + scaling) * power_mult)
                old_hp = target.get("current_hp", 0)
                max_hp = player_max_hp(target) if target is player else target.get("max_hp", old_hp)
                target["current_hp"] = min(old_hp + heal, max_hp)
                actual = target["current_hp"] - old_hp
                name = target.get("name", ally["name"])
                msg_parts.append(f"{name} is healed for {actual} HP!")

    # ── Cooldown & Mastery ──
    cooldown = skill_def.get("cooldown", 1)
    ally.setdefault("skill_cooldowns", {})[skill_id] = max(0, cooldown - cd_reduction)

    mastery_upgrade = add_ally_skill_mastery_xp(ally, skill_id)
    if mastery_upgrade:
        msg_parts.append("Skill Mastery increased! ★")

    # Safety check
    if victory and [e for e in enemies if e["hp"] > 0]:
        victory = False

    return " ".join(msg_parts), victory
