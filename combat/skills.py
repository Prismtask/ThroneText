from combat.combat_io import c_print, c_input
# combat/skills.py – Class Skill Definitions, Mastery & Execution
import random

from resources.skill_loader import PASSIVE_SKILLS, CLASS_SKILLS
from combat.helpers import format_damage_msg


# ── Skill Queries ──────────────────────────────────────────────────────────

def get_class_skill_map(player):
    """Return the skill definition dict for the player's class."""
    return CLASS_SKILLS.get(player.get("class"), {})


def get_available_skills(player):
    """Return list of (skill_id, skill_def) that the player has unlocked and is not on cooldown."""
    skill_map = get_class_skill_map(player)
    cooldowns = player.get("skill_cooldowns", {})
    level = player.get("level", 1)
    unlocked = player.get("skills", [])
    available = []
    for sid, sdef in skill_map.items():
        if sid in unlocked and level >= sdef["unlock_level"] and cooldowns.get(sid, 0) <= 0:
            available.append((sid, sdef))
    return available


def get_all_unlocked_skills(player):
    """Return all unlocked skills (including those on cooldown)."""
    skill_map = get_class_skill_map(player)
    unlocked = player.get("skills", [])
    return [(sid, skill_map[sid]) for sid in unlocked if sid in skill_map]


def is_skill_available(player, skill_id):
    """Check if a specific skill is ready to use."""
    unlocked = player.get("skills", [])
    if skill_id not in unlocked:
        return False
    cooldowns = player.get("skill_cooldowns", {})
    return cooldowns.get(skill_id, 0) <= 0


# ── Skill Unlocking ─────────────────────────────────────────────────────────

def unlock_skills_for_level(player):
    """Check if new skills should be unlocked based on current level."""
    skill_map = get_class_skill_map(player)
    level = player.get("level", 1)
    unlocked = set(player.get("skills", []))
    newly_unlocked = []
    for sid, sdef in skill_map.items():
        if sid not in unlocked and level >= sdef["unlock_level"]:
            unlocked.add(sid)
            newly_unlocked.append(sdef["name"])
    if newly_unlocked:
        player["skills"] = list(unlocked)
    return newly_unlocked


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

def get_skill_mastery_level(player, skill_id):
    """Return the mastery level of a skill (0-3)."""
    mastery = player.get("skill_mastery", {})
    uses = mastery.get(skill_id, 0)
    if uses >= 50:
        return 3
    elif uses >= 25:
        return 2
    elif uses >= 10:
        return 1
    return 0


def get_mastery_bonuses(skill_id, mastery_level):
    """Return bonus multipliers based on mastery level."""
    bonuses = {"power_mult": 1.0, "cooldown_reduction": 0, "extra_effect": False}
    if mastery_level >= 1:
        bonuses["power_mult"] = 1.15
    if mastery_level >= 2:
        bonuses["cooldown_reduction"] = 1
    if mastery_level >= 3:
        bonuses["power_mult"] = 1.30
        bonuses["extra_effect"] = True
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
    """Return a mastery label string for display."""
    level = get_skill_mastery_level(player, skill_id)
    labels = ["", "★", "★★", "★★★"]
    return labels[level]


# ── Passive Skill Application ─────────────────────────────────────────────

def get_passive_skill(player):
    """Return the passive skill dict for the player's class, or None."""
    if not player.get("passive_unlocked", True):
        return None
    return PASSIVE_SKILLS.get(player.get("class"))


def apply_passive_to_damage_taken(player, damage):
    """Apply passive damage reduction. Returns reduced damage."""
    passive = get_passive_skill(player)
    if not passive:
        return damage
    effect = passive.get("effect", {})
    if effect.get("type") == "damage_reduction":
        reduction = effect.get("value", 0)
        return int(damage * (1 - reduction))
    return damage


def get_passive_heal_bonus(player):
    """Return heal multiplier from passive."""
    passive = get_passive_skill(player)
    if not passive:
        return 1.0
    effect = passive.get("effect", {})
    if effect.get("type") == "heal_bonus":
        return 1.0 + effect.get("value", 0)
    return 1.0


def get_passive_life_steal(player):
    """Return life steal percentage from passive and temporary effects."""
    # Bloodlust (Barbarian skill) - 50% life steal
    if player.get("bloodlust_turns", 0) > 0:
        return 0.50
    passive = get_passive_skill(player)
    if not passive:
        return 0.0
    effect = passive.get("effect", {})
    if effect.get("type") == "life_steal":
        return effect.get("value", 0)
    return 0.0


# ── Skill Execution ───────────────────────────────────────────────────────

def execute_skill(player, skill_id, enemies, p_str, p_con, p_dex, p_ler, p_wis, p_cha, allies=None):
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
    def _calc_dmg(target, power, ignore_armor=False, element=None, guaranteed_crit=False):
        armor = 0 if ignore_armor else target.get("con_mod", 0)
        # Apply sunder debuff reduction to armor
        for debuff in target.get("active_debuffs", []):
            if debuff.get("type") == "sunder":
                armor = max(0, armor - debuff.get("value", 0))
            elif debuff.get("type") == "curse" and "Constitution" in debuff.get("stats", []):
                armor = max(0, armor - debuff.get("penalty", 0))
        # Apply Strength milestone bonus
        from combat.stat_milestones import get_strength_bonus
        power = power + get_strength_bonus(player)
        # Random critical hit (skip if skill already guarantees a crit)
        if not guaranteed_crit:
            from combat.stats import roll_critical_hit, apply_critical_damage
            is_crit, _ = roll_critical_hit(player, "player")
            if is_crit:
                power = apply_critical_damage(power, is_crit)
                msg_parts.append("Critical hit!")
        dmg = max(1, power - armor)
        # Apply elemental damage — read from YAML skill definition
        if element is None:
            element = skill.get("elemental")
        if element:
            from combat.elemental import calculate_elemental_damage
            dmg = calculate_elemental_damage(dmg, player, target, element)
        # Apply Hunter's Mark damage bonus
        if target.get("hunters_mark"):
            bonus = target.get("hunters_mark_bonus", 0.50)
            dmg = int(dmg * (1 + bonus))
        return dmg

    # ── Life Steal Helper ──
    def _apply_life_steal(damage_dealt):
        ls = get_passive_life_steal(player)
        if ls > 0 and damage_dealt > 0:
            heal = int(damage_dealt * ls)
            if heal > 0:
                from combat.status_effects import apply_healing
                actual = apply_healing(player, heal)
                if actual < 0:
                    msg_parts.append(f"[Soul Siphon] The void twists the healing! You take {-actual} damage!")
                elif actual > 0:
                    msg_parts.append(f"[Soul Siphon] You recover {actual} HP.")

    # ── Special Skills (non-damage) ──

    # Smoke Bomb
    if skill_id == "rog_smoke":
        for e in enemies:
            e["blinded"] = True
            e.setdefault("active_debuffs", []).append({
                "type": "blind", "remaining": 3
            })
        player["smoke_bomb_flee"] = True
        return "You vanish in a cloud of smoke! Enemies are blinded, and your next escape is guaranteed.", False

    # Battle Cry
    if skill_id == "war_battlecry":
        val = 3 if extra_effect else 2
        player.setdefault("active_buffs", []).append({
            "stat": "Strength", "value": val, "remaining": 3, "source": "battle_cry"
        })
        player.setdefault("active_buffs", []).append({
            "stat": "Constitution", "value": val, "remaining": 3, "source": "battle_cry"
        })
        return f"You let out a thunderous battle cry! Strength +{val}, Constitution +{val} for 3 turns!", False

    # Divine Shield
    if skill_id == "clr_shield":
        duration = 3 if extra_effect else 2
        player.setdefault("active_buffs", []).append({
            "type": "divine_shield", "remaining": duration, "source": "divine_shield"
        })
        return f"A radiant shield envelops you! You are immune to damage for {duration} turns.", False

    # Feral Rage
    if skill_id == "bar_rage":
        val = 4 if extra_effect else 3
        player.setdefault("active_buffs", []).append({
            "stat": "Strength", "value": val, "remaining": 3, "source": "feral_rage"
        })
        player.setdefault("active_debuffs", []).append({
            "type": "vulnerable", "value": 0.20, "remaining": 3, "source": "feral_rage"
        })
        return f"You enter a feral rage! Strength +{val}, but you take 20% more damage for 3 turns.", False

    # Berserk
    if skill_id == "bar_berserk":
        player["berserk_turns"] = 3
        return "You go berserk! You will attack twice per turn for 3 turns!", False

    # Dark Curse
    if skill_id == "lck_curse":
        target = _pick_enemy_target()
        if not target:
            return "No valid target.", False
        penalty = 3 if extra_effect else 2
        target.setdefault("active_debuffs", []).append({
            "type": "curse", "penalty": penalty, "remaining": 3, "stats": ["Strength", "Constitution"]
        })
        return f"You curse the {target['name']}! Its Strength and Constitution are reduced by {penalty} for 3 turns.", False

    # Hunter's Mark
    if skill_id == "rng_mark":
        target = _pick_enemy_target()
        if not target:
            return "No valid target.", False
        bonus = 0.75 if extra_effect else 0.50
        target["hunters_mark"] = True
        target["hunters_mark_bonus"] = bonus
        target["hunters_mark_source"] = player.get("name", "Ranger")
        target["hunters_mark_turns"] = 3
        return f"You mark the {target['name']}! Your attacks against it deal +{int(bonus*100)}% damage for 3 turns.", False

    # Heal
    if skill_id == "clr_heal":
        target = _pick_ally_target()
        if not target:
            return "No valid target.", False
        from combat.stat_milestones import get_wisdom_bonus
        heal = int((base_power + scaling) * power_mult * get_passive_heal_bonus(player)) + get_wisdom_bonus(player)
        from combat.status_effects import apply_healing
        actual = apply_healing(target, heal)
        name = "You" if target is player else target.get("name", "Ally")
        mastery_msg = f" [{format_mastery_label(skill_id, player)}]" if mastery > 0 else ""
        if actual < 0:
            return f"The void twists the healing! {name} takes {-actual} damage instead!{mastery_msg}", False
        return f"{name} is healed for {actual} HP!{mastery_msg}", False

    # Lay on Hands
    if skill_id == "pal_layhands":
        target = _pick_ally_target()
        if not target:
            return "No valid target.", False
        max_hp = player_max_hp(target) if target is player else target.get("max_hp", target.get("current_hp", 1))
        old_hp = target.get("current_hp", 0)
        target["current_hp"] = max_hp
        name = "You" if target is player else target.get("name", "Ally")
        return f"{name} is fully restored to {max_hp} HP!", False

    # Mass Heal
    if skill_id == "clr_mass_heal":
        party = [player] + (allies or [])
        from combat.stat_milestones import get_wisdom_bonus
        heal = int((base_power + scaling) * power_mult * get_passive_heal_bonus(player)) + get_wisdom_bonus(player)
        from combat.status_effects import apply_healing
        total_healed = 0
        for member in party:
            if member.get("current_hp", 0) <= 0:
                continue
            actual = apply_healing(member, heal)
            total_healed += max(0, actual)
        return f"Divine light washes over the party! Total healing: {total_healed} HP.", False

    # Resurrection
    if skill_id == "clr_resurrection":
        target = _pick_dead_ally()
        if not target:
            return "No fallen allies to revive.", False
        max_hp = player_max_hp(target) if target is player else target.get("max_hp", 1)
        revive_hp = int(max_hp * skill.get("revive_percent", 0.50))
        target["current_hp"] = revive_hp
        name = "You" if target is player else target.get("name", "Ally")
        return f"{name} is resurrected with {revive_hp} HP!", False

    # Second Wind
    if skill_id == "war_second_wind":
        max_hp = player_max_hp(player)
        heal = int(max_hp * skill.get("heal_percent", 0.25))
        from combat.stat_milestones import get_wisdom_bonus
        heal = heal + get_wisdom_bonus(player)
        from combat.status_effects import apply_healing
        actual = apply_healing(player, heal)
        if actual < 0:
            return f"The void twists your second wind! You take {-actual} damage instead!", False
        return f"You catch your second wind, recovering {actual} HP!", False

    # Time Warp
    if skill_id == "mage_timewarp":
        reduce_all_cooldowns(player, skill.get("cooldown_reduction", 2))
        return "Time bends around you! All skill cooldowns reduced by 2 turns.", False

    # Haste — grant an ally cooldown reduction on their next skill use
    if skill_id == "haste":
        target = _pick_ally_target()
        if not target:
            return "No valid target.", False
        effect = skill.get("effect", {})
        cd_val = effect.get("value", 2)
        duration = effect.get("duration", 2)
        target.setdefault("active_buffs", []).append({
            "type": "cooldown_reduction", "value": cd_val, "remaining": duration
        })
        target_name = "You" if target is player else target.get("name", "Ally")
        mastery_msg = f" [{format_mastery_label(skill_id, player)}]" if mastery > 0 else ""
        return f"{target_name} is hastened! Next skill cooldown reduced by {cd_val} for {duration} turns.{mastery_msg}", False

    # Dark Empowerment
    if skill_id == "lck_empower":
        val = 4 if extra_effect else 3
        player.setdefault("active_buffs", []).append({
            "stat": "Learning", "value": val, "remaining": 3, "source": "dark_empowerment"
        })
        player.setdefault("active_buffs", []).append({
            "stat": "Charisma", "value": val, "remaining": 3, "source": "dark_empowerment"
        })
        return f"Dark energies surge through you! Learning +{val}, Charisma +{val} for 3 turns!", False

    # Bloodlust
    if skill_id == "bar_bloodlust":
        player["bloodlust_turns"] = skill.get("bloodlust_duration", 3)
        return "You thirst for blood! You will heal for 50% of damage dealt for 3 turns!", False

    # Bastion of Light
    if skill_id == "pal_bastion":
        party = [player] + (allies or [])
        for member in party:
            member.setdefault("active_buffs", []).append({
                "type": "defense",
                "value": skill.get("defense_buff", 3),
                "remaining": skill.get("buff_duration", 3)
            })
        return "A bastion of light shields the entire party! Defense buff for 3 turns.", False

    # Soul Fear
    if skill_id == "lck_fear":
        for e in enemies:
            e.setdefault("active_debuffs", []).append({
                "type": "fear",
                "value": skill.get("fear_value", 0.20),
                "remaining": skill.get("fear_duration", 3)
            })
        return "You unleash a wave of terror! All enemies deal 20% less damage for 3 turns.", False

    # ── Damage-dealing skills ──

    # Multi-target (enemies)
    if target_type == "enemies":
        total_hits = skill.get("hits", 1)
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
                    # Apply rogue sneak attack bonus
                    passive = get_passive_skill(player)
                    if passive and passive.get("effect", {}).get("type") == "vulnerable_bonus":
                        if target.get("slowed") or target.get("stunned"):
                            power = int(power * (1 + passive["effect"]["value"]))
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
                        target["slowed"] = True
                        target.setdefault("active_debuffs", []).append({
                            "type": "slow", "remaining": 3
                        })
                    # Apply stun
                    if skill.get("stun_chance") and random.random() < skill["stun_chance"]:
                        target["stunned"] = True
                        msg_parts.append(f"{target['name']} is stunned!")
                    # Apply weaken
                    if skill.get("apply_weaken"):
                        target.setdefault("active_debuffs", []).append({
                            "type": "weaken", "value": 2, "remaining": 3
                        })
                        msg_parts.append(f"{target['name']} is weakened!")
                    # Apply burn
                    if skill.get("burn_damage"):
                        from combat.status_effects import apply_burn, damage_to_burn_tier, get_burn_tier_name
                        b_tier = damage_to_burn_tier(skill["burn_damage"])
                        apply_burn(target, b_tier, skill.get("burn_duration", 3))
                        msg_parts.append(f"{target['name']} is set ablaze!")
                    # Apply poison
                    if skill.get("poison_damage"):
                        apply_poison(target, skill["poison_damage"], skill.get("poison_duration", 3))
                        msg_parts.append(f"{target['name']} is poisoned!")
                    # Apply sunder
                    if skill.get("apply_sunder"):
                        target.setdefault("active_debuffs", []).append({
                            "type": "sunder", "value": skill.get("sunder_value", 3),
                            "remaining": skill.get("sunder_duration", 3)
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
            return "No valid target.", False

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
            healed = apply_healing(player, heal)
            if healed < 0:
                msg_parts.append(format_damage_msg(player['name'], target['name'], dmg, element=skill.get('elemental'), skill_name=skill['name']) + f" (Void Drain: {-healed} damage!)")
            else:
                msg_parts.append(format_damage_msg(player['name'], target['name'], dmg, element=skill.get('elemental'), skill_name=skill['name']) + f" (Drain: +{healed} HP)")
            if target["hp"] <= 0:
                msg_parts.append(f"{target['name']} is defeated!")
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
            actual_heal = apply_healing(player, heal)
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
                e["slowed"] = True
                e.setdefault("active_debuffs", []).append({
                    "type": "slow", "remaining": 3
                })
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
            if extra_effect:
                poison_dmg = int(poison_dmg * 1.5)
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
                e.setdefault("active_debuffs", []).append({
                    "type": "weaken", "value": 2, "remaining": 3
                })
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
            burn_dmg = skill.get("burn_damage", 6)
            if extra_effect:
                burn_dmg = int(burn_dmg * 1.5)
            b_tier = damage_to_burn_tier(burn_dmg)
            apply_burn(target, b_tier, skill.get("burn_duration", 3))
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
            sunder_val = skill.get("sunder_value", 3)
            if extra_effect:
                sunder_val += 2
            target.setdefault("active_debuffs", []).append({
                "type": "sunder", "value": sunder_val,
                "remaining": skill.get("sunder_duration", 3)
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
                e["slowed"] = True
                e.setdefault("active_debuffs", []).append({
                    "type": "slow", "remaining": 3
                })
                msg_parts.append(format_damage_msg(player['name'], e['name'], dmg, element=skill.get('elemental'), skill_name=skill['name']) + " +Slowed")
                if e["hp"] <= 0:
                    msg_parts.append(f"{e['name']} is strangled!")
            if not [e for e in enemies if e["hp"] > 0]:
                victory = True

        # Generic fallback
        else:
            if target_type == "ally_or_self" and target:
                heal = int((base_power + scaling) * power_mult * get_passive_heal_bonus(player))
                old_hp = target.get("current_hp", 0)
                max_hp = player_max_hp(target) if target is player else target.get("max_hp", old_hp)
                target["current_hp"] = min(old_hp + heal, max_hp)
                actual = target["current_hp"] - old_hp
                name = "You" if target is player else target.get("name", "Ally")
                msg_parts.append(f"{name} is healed for {actual} HP!")
            elif target:
                power = int((base_power + scaling) * power_mult)
                dmg = _calc_dmg(target, power, skill.get("ignore_armor", False))
                target["hp"] -= dmg
                msg_parts.append(format_damage_msg(player['name'], target['name'], dmg, element=skill.get('elemental'), skill_name=skill.get('name', 'Skill')))
                if target["hp"] <= 0:
                    msg_parts.append(f"{target['name']} is defeated!")
                    victory = True
                _apply_life_steal(dmg)

    mastery_upgrade = add_skill_mastery_xp(player, skill_id)
    if mastery_upgrade:
        msg_parts.append(f"Skill Mastery increased to Level {mastery_upgrade}! ★")

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
