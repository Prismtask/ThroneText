# combat/black_silence_gloves.py
"""Certain Someone Black Gloves — item logic for the Black Silence superboss drop.

Replaces ALL class skills with 9 one-use-per-cycle workshop attacks + Furioso.

State keys on player dict:
    gloves_workshop_used: set[int]     — indices 1-9 used this cycle
    gloves_furioso_available: bool     — whether Furioso can be activated
    gloves_first_strike_active: bool   — +15% damage for acting first this round
"""

import random
from combat.combat_io import c_print, c_input
from combat.helpers import format_damage_msg, ELEMENT_TAGS
from combat.status_effects import apply_bleed

# ═══════════════════════════════════════════════════════════════════
# WORKSHOP DEFINITIONS
# ═══════════════════════════════════════════════════════════════════
# Each entry: (name, scaling_stat, target_mode, dmg_mult, effect_fn)

WORKSHOPS = {
    1: {"name": "Allas Workshop",       "stat": "Strength",     "target": "single", "mult": 1.40,
         "desc": "Ignore 20% of target's CON (DEF piercing)"},
    2: {"name": "Wheels Industry",      "stat": "Strength",     "target": "aoe",    "mult": 0.90,
         "desc": "30% chance to Stun each target for 1 turn"},
    3: {"name": "Zelkova Workshop",     "stat": "Dexterity",    "target": "single", "mult": 1.00,
         "desc": "Hit TWICE (each at 1.20x, total 2.40x)"},
    4: {"name": "Old Boys Workshop",    "stat": "Strength",     "target": "single", "mult": 1.20,
         "desc": "65% chance to Stun for 1 turn"},
    5: {"name": "Mook Workshop",        "stat": "Wisdom",       "target": "aoe",    "mult": 0.80,
         "desc": "Lifesteal: heal 50% of total damage dealt"},
    6: {"name": "Ranga Workshop",       "stat": "Dexterity",    "target": "single", "mult": 1.20,
         "desc": "70% chance to apply Bleed (6 dmg x 3 turns)"},
    7: {"name": "Crystal Atelier",      "stat": "Dexterity",    "target": "single", "mult": 1.10,
         "desc": "Grant self +20% dodge for 2 turns"},
    8: {"name": "Atelier Logic",        "stat": "Wisdom",       "target": "single", "mult": 2.90,
         "desc": "massive single-target damage"},
    9: {"name": "Durandal",             "stat": "Learning",     "target": "random3", "mult": 1.10,
         "desc": "3 random hits; if 1 enemy alive, all 3 hit that enemy"},
}

# Durandal hit count
DURANDAL_HITS = 3


# ═══════════════════════════════════════════════════════════════════
# STATE MANAGEMENT
# ═══════════════════════════════════════════════════════════════════

def _actor_has_black_silence_gloves(actor):
    """Check if an actor has Black Silence gloves equipped in weapon slot."""
    equipped = actor.get("equipped", {})
    if isinstance(equipped, dict):
        weapon = equipped.get("weapon")
        if weapon and weapon.get("id") == "certain_someone_black_gloves":
            return True
    return False

def _player_has_black_silence_gloves(player):
    """Check if the player has Black Silence gloves equipped in weapon slot."""
    return _actor_has_black_silence_gloves(player)


def init_gloves_state(actor):
    """Called at combat start to set up gloves state on an actor."""
    actor["gloves_workshop_used"] = set()
    actor["gloves_furioso_available"] = False
    actor["gloves_first_strike_active"] = False


def clear_gloves_state(actor):
    """Called at combat end to clean up gloves state."""
    actor.pop("gloves_workshop_used", None)
    actor.pop("gloves_furioso_available", None)
    actor.pop("gloves_first_strike_active", None)


def get_gloves_initiative_bonus(actor):
    """Return +3 initiative if gloves are equipped."""
    if _actor_has_black_silence_gloves(actor):
        return 3
    return 0


def get_gloves_dodge_bonus(actor):
    """Return +8% dodge (0.08) if gloves are equipped."""
    if _actor_has_black_silence_gloves(actor):
        return 0.08
    return 0.0


def get_gloves_first_strike_damage_bonus(actor):
    """Return +15% (0.15) multiplicative damage bonus if first strike is active."""
    if actor.get("gloves_first_strike_active"):
        return 0.15
    return 0.0


def set_first_strike(actor, is_first):
    """Set first strike state for the round."""
    if _actor_has_black_silence_gloves(actor):
        actor["gloves_first_strike_active"] = is_first


# ═══════════════════════════════════════════════════════════════════
# DAMAGE CALCULATION
# ═══════════════════════════════════════════════════════════════════

def _compute_scaling_stat(player, workshop_id):
    """Get the player's effective attribute value for a workshop."""
    ws = WORKSHOPS[workshop_id]
    stat_name = ws["stat"]
    attr_map = {
        "Strength": "p_str", "Dexterity": "p_dex", "Constitution": "p_con",
        "Wisdom": "p_wis", "Learning": "p_ler", "Charisma": "p_cha",
    }
    # The caller passes these as kwargs
    return stat_name


def _roll_base_damage(scaling_val):
    """Roll the base damage die: d4-10 + scaling."""
    return random.randint(4, 10) + scaling_val


def _apply_workshop_damage(attacker_name, target, base_dmg, mult, element="dark",
                           ignore_con_pct=0.0, is_crit=False):
    """Apply damage to target with the workshop multiplier and CON reduction.
    CON is scaled by the multiplier so low-mult attacks aren't double-penalized."""
    if ignore_con_pct > 0:
        effective_con = int(target.get("con_mod", 0) * (1.0 - ignore_con_pct))
    else:
        effective_con = target.get("con_mod", 0)
    final_dmg = max(0, int((base_dmg - effective_con) * mult))

    # Apply first strike bonus
    # (handled by caller)

    target["hp"] = max(0, target["hp"] - final_dmg)
    return final_dmg


# ═══════════════════════════════════════════════════════════════════
# WORKSHOP EXECUTION
# ═══════════════════════════════════════════════════════════════════

def execute_workshop(player, enemies, workshop_id,
                     p_str, p_con, p_dex, p_ler, p_wis, p_cha,
                     allies=None, defending=False):
    """Execute a single workshop attack (player-initiated).
    
    Returns: (msg_string, victory_bool)
    """
    return _execute_workshop_actor(player, enemies, workshop_id,
                                   p_str, p_con, p_dex, p_ler, p_wis, p_cha,
                                   allies=allies, defending=defending, is_player=True)


def _execute_workshop_actor(actor, enemies, workshop_id,
                            p_str, p_con, p_dex, p_ler, p_wis, p_cha,
                            allies=None, defending=False, is_player=True):
    ws = WORKSHOPS[workshop_id]
    stat_map = {
        "Strength": p_str, "Dexterity": p_dex, "Constitution": p_con,
        "Wisdom": p_wis, "Learning": p_ler, "Charisma": p_cha,
    }
    scaling_val = stat_map[ws["stat"]]

    from combat.stat_milestones import get_strength_bonus
    str_bonus = get_strength_bonus(actor) if ws["stat"] == "Strength" else 0

    messages = []
    total_heal = 0
    victory = False

    # First strike bonus
    first_strike_mult = 1.0 + get_gloves_first_strike_damage_bonus(actor)

    if ws["target"] == "single":
        # Single target selection
        if len(enemies) > 1:
            try:
                choice = int(c_input(f"Select target for {ws['name']}: ")) - 1
                if choice < 0 or choice >= len(enemies):
                    c_print("Invalid target selection.")
                    return "Invalid target.", False
                target = enemies[choice]
            except ValueError:
                c_print("Please enter a valid number.")
                return "Invalid input.", False
        else:
            target = enemies[0]

        base_dmg = _roll_base_damage(scaling_val + str_bonus)

        # Special handling per workshop
        if workshop_id == 1:  # Allas — 20% CON ignore
            ignore_pct = 0.20
            effective_con = int(target.get("con_mod", 0) * (1.0 - ignore_pct))
            dmg = max(0, int((base_dmg - effective_con) * ws["mult"]))
            dmg = int(dmg * first_strike_mult)
            dmg = max(0, dmg)
            target["hp"] = max(0, target["hp"] - dmg)
            messages.append(format_damage_msg(actor["name"], target["name"], dmg, element="dark", skill_name="Allas (DEF pierce)"))

        elif workshop_id == 3:  # Zelkova — double hit
            for hit_num in range(2):
                roll = _roll_base_damage(scaling_val)
                dmg = max(0, int((roll - target.get("con_mod", 0)) * ws["mult"]))
                dmg = int(dmg * first_strike_mult)
                dmg = max(0, dmg)
                target["hp"] = max(0, target["hp"] - dmg)
                hit_label = f"Zelkova ({hit_num + 1}/2)"
                messages.append(format_damage_msg(actor["name"], target["name"], dmg, element="dark", skill_name=hit_label))
                if target["hp"] <= 0:
                    break

        elif workshop_id == 4:  # Old Boys — 65% stun
            dmg = max(0, int((base_dmg - target.get("con_mod", 0)) * ws["mult"]))
            dmg = int(dmg * first_strike_mult)
            dmg = max(0, dmg)
            target["hp"] = max(0, target["hp"] - dmg)
            messages.append(format_damage_msg(actor["name"], target["name"], dmg, element="dark", skill_name="Old Boys"))
            if random.random() < 0.65:
                target["stunned"] = True
                messages.append(f"  💥 {target['name']} is STUNNED!")

        elif workshop_id == 6:  # Ranga — 70% bleed
            dmg = max(0, int((base_dmg - target.get("con_mod", 0)) * ws["mult"]))
            dmg = int(dmg * first_strike_mult)
            dmg = max(0, dmg)
            target["hp"] = max(0, target["hp"] - dmg)
            messages.append(format_damage_msg(actor["name"], target["name"], dmg, element="dark", skill_name="Ranga"))
            if random.random() < 0.70:
                apply_bleed(target, 6, 3)
                messages.append(f"  🩸 {target['name']} is BLEEDING! (6 dmg x 3 turns)")

        elif workshop_id == 7:  # Crystal Atelier — +20% dodge
            dmg = max(0, int((base_dmg - target.get("con_mod", 0)) * ws["mult"]))
            dmg = int(dmg * first_strike_mult)
            dmg = max(0, dmg)
            target["hp"] = max(0, target["hp"] - dmg)
            messages.append(format_damage_msg(actor["name"], target["name"], dmg, element="dark", skill_name="Crystal Atelier"))
            # Add dodge buff to actor
            actor.setdefault("active_buffs", []).append({
                "type": "evasion",
                "source": "crystal_atelier",
                "value": 0.20,
                "remaining": 2,
            })
            messages.append("  💎 Crystal Atelier: +20% Dodge for 2 turns!")

        elif workshop_id == 8:  # Atelier Logic — 2.0x once per cycle
            dmg = max(0, int((base_dmg - target.get("con_mod", 0)) * ws["mult"]))
            dmg = int(dmg * first_strike_mult)
            dmg = max(0, dmg)
            target["hp"] = max(0, target["hp"] - dmg)
            messages.append(format_damage_msg(actor["name"], target["name"], dmg, element="dark", skill_name="Atelier Logic"))

        else:
            # Generic single-target
            dmg = max(0, int((base_dmg - target.get("con_mod", 0)) * ws["mult"]))
            dmg = int(dmg * first_strike_mult)
            dmg = max(0, dmg)
            target["hp"] = max(0, target["hp"] - dmg)
            messages.append(format_damage_msg(actor["name"], target["name"], dmg, element="dark", skill_name=ws["name"]))

        if target["hp"] <= 0:
            messages.append(f"{actor['name']} defeated {target['name']}!")
            enemies[:] = [e for e in enemies if e["hp"] > 0 and not e.get("captured")]
            if not enemies:
                victory = True

    elif ws["target"] == "aoe":
        # AoE — Wheels Industry (2) or Mook Workshop (5)
        total_aoe_dmg = 0
        for target in list(enemies):
            base_dmg = _roll_base_damage(scaling_val + str_bonus)
            dmg = max(0, int((base_dmg - target.get("con_mod", 0)) * ws["mult"]))
            dmg = int(dmg * first_strike_mult)
            dmg = max(0, dmg)
            target["hp"] = max(0, target["hp"] - dmg)
            total_aoe_dmg += dmg
            messages.append(format_damage_msg(actor["name"], target["name"], dmg, element="dark", skill_name=ws["name"]))

            # Wheels Industry (2): 30% stun per target
            if workshop_id == 2 and target["hp"] > 0:
                if random.random() < 0.30:
                    target["stunned"] = True
                    messages.append(f"  ⚡ {target['name']} is STUNNED!")

        # Mook Workshop (5): 50% lifesteal
        if workshop_id == 5:
            heal = int(total_aoe_dmg * 0.50)
            if heal > 0:
                from character import player_max_hp
                old_hp = actor["current_hp"]
                max_hp = player_max_hp(actor)
                actor["current_hp"] = min(old_hp + heal, max_hp)
                actual_heal = actor["current_hp"] - old_hp
                messages.append(f"  🩸 Mook lifesteal: recovered {actual_heal} HP!")

        enemies[:] = [e for e in enemies if e["hp"] > 0 and not e.get("captured")]
        if not enemies:
            victory = True

    elif ws["target"] == "random3":
        # Durandal (9): 3 random hits
        alive = [e for e in enemies if e["hp"] > 0]
        if not alive:
            return "No enemies to target.", False

        for hit_num in range(DURANDAL_HITS):
            if not alive:
                break
            target = random.choice(alive)
            base_dmg = _roll_base_damage(scaling_val)
            dmg = max(0, int((base_dmg - target.get("con_mod", 0)) * ws["mult"]))
            dmg = int(dmg * first_strike_mult)
            dmg = max(0, dmg)
            target["hp"] = max(0, target["hp"] - dmg)
            hit_label = f"Durandal ({hit_num + 1}/{DURANDAL_HITS})"
            messages.append(format_damage_msg(actor["name"], target["name"], dmg, element="dark", skill_name=hit_label))
            if target["hp"] <= 0:
                messages.append(f"  {target['name']} falls!")
                alive = [e for e in enemies if e["hp"] > 0]

        enemies[:] = [e for e in enemies if e["hp"] > 0 and not e.get("captured")]
        if not enemies:
            victory = True

    # Mark workshop as used
    actor.setdefault("gloves_workshop_used", set()).add(workshop_id)
    if len(actor["gloves_workshop_used"]) >= 9:
        actor["gloves_furioso_available"] = True

    msg = "\n".join(messages) if messages else f"{ws['name']}: no effect."
    return msg, victory


def execute_furioso(player, enemies, p_str, p_con, p_dex, p_ler, p_wis, p_cha,
                    allies=None):
    """Execute Furioso for the player (backward-compat)."""
    return _execute_furioso_actor(player, enemies, p_str, p_con, p_dex, p_ler, p_wis, p_cha,
                                  allies=allies, is_player=True)


def _execute_furioso_actor(actor, enemies, p_str, p_con, p_dex, p_ler, p_wis, p_cha,
                            allies=None, is_player=True):
    stat_map = {
        "Strength": p_str, "Dexterity": p_dex, "Constitution": p_con,
        "Wisdom": p_wis, "Learning": p_ler, "Charisma": p_cha,
    }
    from combat.stat_milestones import get_strength_bonus

    messages = ["\n" + "=" * 50]
    messages.append("⚔️  FURIOSO  ⚔️")
    messages.append("The gloves hum in unison. Nine voices become one.")
    messages.append("=" * 50)

    alive = [e for e in enemies if e["hp"] > 0]
    if not alive:
        return "No enemies to target.", False

    target_idx = 0
    total_dmg = 0  # Accumulate total damage dealt
    furioso_mult = 1.45  # Damage multiplier during Furioso
    effect_potency = 0.50  # Effect potency halved

    # Build randomized Furioso order: shuffle 1-8, Durandal (9) always last
    furioso_order = list(range(1, 9))
    random.shuffle(furioso_order)
    furioso_order.append(9)

    for workshop_id in furioso_order:
        if not alive:
            break

        ws = WORKSHOPS[workshop_id]
        stat_name = ws["stat"]
        scaling_val = stat_map[stat_name]
        str_bonus = get_strength_bonus(actor) if stat_name == "Strength" else 0

        # Round-robin target selection
        target = alive[target_idx % len(alive)]
        target_idx += 1

        base_dmg = random.randint(4, 10) + scaling_val + str_bonus

        if workshop_id == 1:  # Allas — 10% CON ignore (halved from 20%)
            ignore_pct = 0.10
            eff_con = int(target.get("con_mod", 0) * (1.0 - ignore_pct))
            dmg = max(0, int((base_dmg - eff_con) * ws["mult"] * furioso_mult))
            dmg = max(0, dmg)
            target["hp"] = max(0, target["hp"] - dmg)
            total_dmg += dmg
            messages.append(format_damage_msg(actor["name"], target["name"], dmg, element="dark", skill_name="Furioso: Allas"))

        elif workshop_id == 2:  # Wheels Industry — AoE (but in Furioso, single-target round-robin) 15% stun
            dmg = max(0, int((base_dmg - target.get("con_mod", 0)) * ws["mult"] * furioso_mult))
            dmg = max(0, dmg)
            target["hp"] = max(0, target["hp"] - dmg)
            total_dmg += dmg
            messages.append(format_damage_msg(actor["name"], target["name"], dmg, element="dark", skill_name="Furioso: Wheels"))
            if target["hp"] > 0 and random.random() < 0.15:
                target["stunned"] = True
                messages.append(f"  ⚡ {target['name']} is STUNNED!")

        elif workshop_id == 3:  # Zelkova — double hit (each at 0.70 * 0.75)
            for hit_num in range(2):
                roll = random.randint(4, 10) + scaling_val
                dmg = max(0, int((roll - target.get("con_mod", 0)) * ws["mult"] * furioso_mult))
                dmg = max(0, dmg)
                target["hp"] = max(0, target["hp"] - dmg)
                total_dmg += dmg
                hit_label = f"Furioso: Zelkova ({hit_num + 1}/2)"
                messages.append(format_damage_msg(actor["name"], target["name"], dmg, element="dark", skill_name=hit_label))
                if target["hp"] <= 0:
                    break

        elif workshop_id == 4:  # Old Boys — 32.5% stun
            dmg = max(0, int((base_dmg - target.get("con_mod", 0)) * ws["mult"] * furioso_mult))
            dmg = max(0, dmg)
            target["hp"] = max(0, target["hp"] - dmg)
            total_dmg += dmg
            messages.append(format_damage_msg(actor["name"], target["name"], dmg, element="dark", skill_name="Furioso: Old Boys"))
            if target["hp"] > 0 and random.random() < 0.325:
                target["stunned"] = True
                messages.append(f"  💥 {target['name']} is STUNNED!")

        elif workshop_id == 5:  # Mook — AoE lifesteal 25% (halved)
            dmg = max(0, int((base_dmg - target.get("con_mod", 0)) * ws["mult"] * furioso_mult))
            dmg = max(0, dmg)
            target["hp"] = max(0, target["hp"] - dmg)
            total_dmg += dmg
            messages.append(format_damage_msg(actor["name"], target["name"], dmg, element="dark", skill_name="Furioso: Mook"))
            heal = int(dmg * 0.25)
            if heal > 0:
                from character import player_max_hp
                old_hp = actor["current_hp"]
                max_hp = player_max_hp(actor)
                actor["current_hp"] = min(old_hp + heal, max_hp)
                actual = actor["current_hp"] - old_hp
                if actual > 0:
                    messages.append(f"  🩸 Mook lifesteal: recovered {actual} HP!")

        elif workshop_id == 6:  # Ranga — 35% bleed
            dmg = max(0, int((base_dmg - target.get("con_mod", 0)) * ws["mult"] * furioso_mult))
            dmg = max(0, dmg)
            target["hp"] = max(0, target["hp"] - dmg)
            total_dmg += dmg
            messages.append(format_damage_msg(actor["name"], target["name"], dmg, element="dark", skill_name="Furioso: Ranga"))
            if target["hp"] > 0 and random.random() < 0.35:
                apply_bleed(target, 6, 3)
                messages.append(f"  🩸 {target['name']} is BLEEDING!")

        elif workshop_id == 7:  # Crystal Atelier — +10% dodge
            dmg = max(0, int((base_dmg - target.get("con_mod", 0)) * ws["mult"] * furioso_mult))
            dmg = max(0, dmg)
            target["hp"] = max(0, target["hp"] - dmg)
            total_dmg += dmg
            messages.append(format_damage_msg(actor["name"], target["name"], dmg, element="dark", skill_name="Furioso: Crystal"))
            actor.setdefault("active_buffs", []).append({
                "type": "evasion",
                "source": "crystal_atelier",
                "value": 0.10,
                "remaining": 2,
            })
            messages.append("  💎 Crystal Atelier: +10% Dodge for 2 turns!")

        elif workshop_id == 8:  # Atelier Logic — 1.50x (2.00 * 0.75)
            dmg = max(0, int((base_dmg - target.get("con_mod", 0)) * ws["mult"] * furioso_mult))
            dmg = max(0, dmg)
            target["hp"] = max(0, target["hp"] - dmg)
            total_dmg += dmg
            messages.append(format_damage_msg(actor["name"], target["name"], dmg, element="dark", skill_name="Furioso: Logic"))

        elif workshop_id == 9:  # Durandal — 3 hits at 0.45x (0.60 * 0.75)
            for hit_num in range(DURANDAL_HITS):
                # Refresh alive list before each hit so we don't target dead enemies
                alive = [e for e in enemies if e["hp"] > 0]
                if not alive:
                    break
                if target["hp"] <= 0:
                    target = random.choice(alive)
                roll = random.randint(4, 10) + scaling_val
                dmg = max(0, int((roll - target.get("con_mod", 0)) * ws["mult"] * furioso_mult))
                dmg = max(0, dmg)
                target["hp"] = max(0, target["hp"] - dmg)
                total_dmg += dmg
                hit_label = f"Furioso: Durandal ({hit_num + 1}/{DURANDAL_HITS})"
                messages.append(format_damage_msg(actor["name"], target["name"], dmg, element="dark", skill_name=hit_label))

        # Refresh alive list
        alive = [e for e in enemies if e["hp"] > 0]
        if target["hp"] <= 0:
            messages.append(f"  {target['name']} falls to the Furioso!")

    enemies[:] = [e for e in enemies if e["hp"] > 0 and not e.get("captured")]

    # Reset cycle
    actor["gloves_workshop_used"] = set()
    actor["gloves_furioso_available"] = False
    messages.append(f"\n  ⚡ Total Furioso damage: {total_dmg}")
    messages.append("\n" + "=" * 50)
    messages.append("The gloves fall silent. The cycle begins anew.")
    messages.append("=" * 50)

    victory = len(enemies) == 0
    return "\n".join(messages), victory


def get_gloves_action_menu(player, enemies):
    """Build the action menu when Black Silence gloves are equipped.
    
    Returns: (menu_string, valid_keys_list)
    """
    from combat.capture import is_monster_girl, is_capturable
    from combat.status_effects import is_silenced

    actions = []

    # Capture
    if any(is_capturable(e) for e in enemies):
        actions.append(('c', 'Capture'))

    # Core actions (no Attack — gloves replace it)
    actions.append(('d', 'Defend'))
    actions.append(('f', 'Flee'))

    # Use item (blocked if silenced)
    if not is_silenced(player):
        actions.append(('u', 'Use item'))

    # Workshop attacks 1-9
    workshop_state = player.get("gloves_workshop_used", set())
    if not isinstance(workshop_state, (set, list)):
        workshop_state = set()
    workshop_menu = [
        ('1', 'Allas Workshop [STR]'),
        ('2', 'Wheels Industry [STR]'),
        ('3', 'Zelkova Workshop [DEX]'),
        ('4', 'Old Boys Workshop [STR]'),
        ('5', 'Mook Workshop [WIS]'),
        ('6', 'Ranga Workshop [DEX]'),
        ('7', 'Crystal Atelier [DEX]'),
        ('8', 'Atelier Logic [WIS]'),
        ('9', 'Durandal [LEA]'),
    ]
    for key, label in workshop_menu:
        if int(key) not in workshop_state:
            actions.append((key, label))
        else:
            actions.append((key, f'{label} [USED]'))

    # Furioso — only if all 9 used
    if player.get("gloves_furioso_available"):
        actions.append(('0', 'FURIOSO'))

    menu_str = '  '.join(f'[{key.upper()}]{label}' for key, label in actions)
    valid_keys = [key for key, _ in actions]

    return menu_str, valid_keys
