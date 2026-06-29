# enemy_ai.py – enemy turn logic and racial status effects
import random
from combat.status_effects import (
    apply_bleed, apply_curse, apply_dread, apply_weaken,
    apply_drain, apply_silence, tick_enemy_debuffs
)
from resources.enemies import ENEMIES
from combat.wedding_specials import (
    apply_wedding_dodge_bonus,
    apply_wedding_on_dodge,
    apply_wedding_damage_reduction,
    apply_wedding_fatal_blow_survival,
    apply_wedding_on_damage_taken,
    apply_wedding_enemy_accuracy_penalty,
    apply_wedding_enemy_attack_pre_damage,
)
 

def enemy_attack(enemy, player, p_con, defending, extra_logic=None, armor_mult=1.0, temp_str_bonus=0):
    # --- Check fear BEFORE ticking (so it applies this full turn) ---
    fear_mult = 1.0
    for debuff in enemy.get("active_debuffs", []):
        if debuff.get("type") == "fear":
            fear_mult = max(0.0, 1.0 - debuff.get("value", 0))
            break

    # Tick enemy debuffs (poison, burn, blind, fear, etc.)
    msgs, died = tick_enemy_debuffs(enemy)
    for m in msgs:
        print(m)
    if died:
        return "died"

    if enemy.get("stunned"):
        print(f"The {enemy['name']} is stunned and cannot act!")
        enemy["stunned"] = False
        return "stunned"

    if enemy.get("frozen"):
        print(f"The {enemy['name']} is frozen solid and cannot act!")
        return "stunned"

    # --- DODGE CHECK ---
    from combat.stat_milestones import get_dexterity_bonus
    dodge_chance = get_dexterity_bonus(player)
    # Add evasion buffs
    for buff in player.get("active_buffs", []):
        if buff.get("type") == "evasion":
            dodge_chance += buff.get("value", 0)
    # Wedding dodge bonuses + enemy accuracy penalty
    dodge_chance += apply_wedding_dodge_bonus(player)
    dodge_chance += apply_wedding_enemy_accuracy_penalty(player)
    # Cap dodge at 80% to prevent absolute immunity
    dodge_chance = min(dodge_chance, 0.80)
    if dodge_chance > 0 and random.random() < dodge_chance:
        print(f"The {enemy['name']} lunges at {player['name']} — but {player['name']} dodges out of the way!")
        apply_wedding_on_dodge(player, enemy)
        return "dodged"

    # --- PRE-DAMAGE WEDDING EFFECTS (foxfire trick, etc.) ---
    if apply_wedding_enemy_attack_pre_damage(player, enemy):
        return "missed"

    # --- DIVINE SHIELD CHECK ---
    divine_shield = any(
        b.get("type") == "divine_shield" and b.get("remaining", 0) > 0
        for b in player.get("active_buffs", [])
    )
    if divine_shield:
        print(f"The {enemy['name']}'s attack glances off {player['name']}'s divine shield!")
        return "blocked"

    # --- BASE DAMAGE ---
    block = p_con + (5 if defending else 0)
    block = int(block * armor_mult)

    raw_dmg = random.randint(2, 7) + enemy["str_mod"] + temp_str_bonus

    # Critical hit check
    from combat.stats import roll_critical_hit, apply_critical_damage, format_critical_tag
    is_crit, _ = roll_critical_hit(enemy, "enemy")
    raw_dmg = apply_critical_damage(raw_dmg, is_crit)
    crit_tag = format_critical_tag(is_crit)

    raw_dmg = int(raw_dmg * fear_mult)
    base_dmg = raw_dmg - block
    base_dmg = max(0, base_dmg)

    # --- VULNERABLE CHECK ---
    vulnerable_mult = 1.0
    for debuff in player.get("active_debuffs", []):
        if debuff.get("type") == "vulnerable":
            vulnerable_mult = 1.0 + debuff.get("value", 0)
            break
    base_dmg = int(base_dmg * vulnerable_mult)

    # Apply elemental damage based on enemy's elemental profile
    from combat.elemental import calculate_elemental_damage, ELEMENTS
    enemy_dmg = base_dmg
    element = None
    if base_dmg > 0:
        e_dmg_profile = enemy.get("elemental_dmg", {})
        best_el = None
        best_val = 1.0
        for el in ELEMENTS:
            val = e_dmg_profile.get(el, 1.0)
            if val > best_val:
                best_val = val
                best_el = el
        if best_el:
            element = best_el
            enemy_dmg = calculate_elemental_damage(base_dmg, enemy, player, element)
        else:
            enemy_dmg = base_dmg

    # --- DEFENSE BUFFS (flat reduction) ---
    defense_reduction = 0
    for buff in player.get("active_buffs", []):
        if buff.get("type") == "defense":
            defense_reduction += buff.get("value", 0)
    if defense_reduction > 0:
        enemy_dmg = max(0, enemy_dmg - defense_reduction)

    # Apply Constitution milestone damage reduction
    from combat.stat_milestones import get_constitution_bonus
    con_reduction = get_constitution_bonus(player)
    if con_reduction > 0 and enemy_dmg > 0:
        enemy_dmg = max(0, enemy_dmg - con_reduction)

    # Apply Barbarian passive damage reduction
    from combat.skills import apply_passive_to_damage_taken
    enemy_dmg = apply_passive_to_damage_taken(player, enemy_dmg)

    # Wedding damage reduction (slime_absorb, stone_endurance, etc.)
    is_elemental = element is not None
    enemy_dmg = apply_wedding_damage_reduction(player, enemy_dmg, is_elemental=is_elemental, element=element)

    # Wedding fatal blow survival (bark_shield)
    enemy_dmg = apply_wedding_fatal_blow_survival(player, enemy_dmg)

    # Final floor
    enemy_dmg = max(0, enemy_dmg)
    player["current_hp"] -= enemy_dmg

    elemental_tags = {"fire": "[FIRE]", "water": "[ICE]", "thunder": "[THUNDER]",
                      "wind": "[WIND]", "earth": "[EARTH]", "light": "[LIGHT]", "dark": "[DARK]"}
    tag = elemental_tags.get(element, "")

    if enemy_dmg > 0:
        if tag:
            print(f"The {enemy['name']} hits {player['name']} for {enemy_dmg} damage!{crit_tag} {tag}")
        else:
            print(f"The {enemy['name']} hits {player['name']} for {enemy_dmg} damage!{crit_tag}")
        # Wedding retribution effects (pharaohs_curse, infernal_crown, keening_wail)
        apply_wedding_on_damage_taken(player, enemy, enemy_dmg, "hit")
    else:
        print(f"The {enemy['name']} attacks but {player['name']} blocks all incoming damage!")

    if extra_logic:
        msg = extra_logic(enemy, player, enemy_dmg)
        if msg:
            print(msg)

    if player["current_hp"] <= 0:
        return "dead"
    return "hit"


def get_race_extra_logic(enemy):
    race = ENEMIES[enemy["key"]]["race"]

    if race == "Beast":
        def beast_bleed(e, player, dmg):
            if dmg > 0 and random.random() < 0.35:
                bleed_dmg = max(2, dmg // 3)
                result = apply_bleed(player, damage=bleed_dmg, duration=4)
                if result == "applied":
                    return f"The {e['name']}'s claws open a wound! {player['name']} bleed for {bleed_dmg}/round."
                elif result == "refreshed":
                    return f"The {e['name']} tears {player['name']}'s wound wider! ({bleed_dmg}/round)"
            return None
        return beast_bleed

    if race == "Undead":
        def undead_curse(e, player, dmg):
            if dmg > 0 and random.random() < 0.20:
                result = apply_curse(player)
                if result == "applied":
                    return f"The {e['name']}'s touch carries a dark curse! All attributes reduced."
                elif result == "already_cursed":
                    return f"The {e['name']}'s curse washes over {player['name']}, but already afflicted."
            return None
        return undead_curse

    if race == "Shadow":
        def shadow_dread(e, player, dmg):
            if dmg > 0 and random.random() < 0.30:
                result = apply_dread(player, duration=2)
                if result == "applied":
                    return f"The {e['name']}'s darkness fills {player['name']} with supernatural dread!"
            return None
        return shadow_dread

    if race == "Demon":
        def demon_weaken(e, player, dmg):
            if dmg > 0 and random.random() < 0.25:
                result = apply_weaken(player, str_penalty=2, duration=3)
                if result == "applied":
                    return f"The {e['name']}'s hellfire saps {player['name']}'s strength! STR reduced for 3 turns."
                elif result == "refreshed":
                    return f"{player['name']}'s weakness deepens under the {e['name']}'s assault!"
            return None
        return demon_weaken

    if race == "Vampire":
        def vampire_drain(e, player, dmg):
            if dmg > 0:
                drained = apply_drain(player, e, drain_amount=max(1, dmg // 2))
                if drained > 0:
                    return f"The {e['name']} drains {drained} HP from {player['name']}'s life force!"
            return None
        return vampire_drain

    if race == "Fey":
        def fey_silence(e, player, dmg):
            if dmg > 0 and random.random() < 0.25:
                result = apply_silence(player, duration=2)
                if result == "applied":
                    return f"The {e['name']}'s enchantment seals your pack shut for 2 turns!"
            return None
        return fey_silence

    if race == "Abomination":
        def abomination_weaken(e, player, dmg):
            if dmg > 0 and random.random() < 0.35:
                result = apply_weaken(player, str_penalty=3, duration=3)
                if result == "applied":
                    return f"The {e['name']}'s corrosive flesh weakens {player['name']}'s muscles! STR -3 for 3 turns."
                elif result == "refreshed":
                    return f"The corruption deepens — {player['name']}'s strength ebbs further!"
            return None
        return abomination_weaken

    if race == "Giant":
        def giant_weaken(e, player, dmg):
            if dmg > 0 and random.random() < 0.30:
                result = apply_weaken(player, str_penalty=4, duration=2)
                if result == "applied":
                    return f"The {e['name']}'s crushing blow leaves {player['name']} arms numb! STR -4 for 2 turns."
                elif result == "refreshed":
                    return f"Another bone-crushing hit — {player['name']}'s strength fails!"
            return None
        return giant_weaken

    if race == "Gnome":
        def gnome_silence(e, player, dmg):
            if dmg > 0 and random.random() < 0.20:
                result = apply_silence(player, duration=2)
                if result == "applied":
                    return f"The {e['name']}'s arcane static disrupts {player['name']}'s concentration!"
            return None
        return gnome_silence

    if race == "Elemental":
        def elemental_blind(e, player, dmg):
            if dmg > 0 and random.random() < 0.30:
                from combat.status_effects import apply_blind
                result = apply_blind(player, duration=2)
                if result == "applied":
                    return f"A burst of searing light from the {e['name']} blinds {player['name']}!"
                elif result == "refreshed":
                    return f"The {e['name']}'s radiance deepens {player['name']}'s blindness!"
            return None
        return elemental_blind

    return None