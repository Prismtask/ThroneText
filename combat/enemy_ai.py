# enemy_ai.py – enemy turn logic and racial status effects
import random
from combat.status_effects import (
    apply_bleed, apply_curse, apply_dread, apply_weaken,
    apply_drain, apply_silence, tick_enemy_debuffs
)
from resources.enemies import ENEMIES


def enemy_attack(enemy, player, p_con, defending, extra_logic=None, armor_mult=1.0, temp_str_bonus=0):
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

    block = p_con + (5 if defending else 0)
    block = int(block * armor_mult)

    enemy_dmg = random.randint(2, 7) + enemy["str_mod"] + temp_str_bonus - block
    enemy_dmg = max(0, enemy_dmg)

    player["current_hp"] -= enemy_dmg

    if enemy_dmg > 0:
        print(f"The {enemy['name']} hits {player['name']} for {enemy_dmg} damage!")
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