# combat.py – generic turn‑based combat (no super boss mechanics)

import random
from resources.enemies import ENEMIES, ENEMY_RACES
from resources.races_classes import ATTRIBUTES
from inventory import use_consumable, get_total_equipment_mods
from utils import get_difficulty_multiplier_from_time, clear_screen
from character import player_max_hp
from combat.status_effects import (
    apply_poison, apply_curse,
    apply_weaken, apply_bleed, apply_silence, apply_drain, apply_dread,
    tick_enemy_debuffs, tick_player_debuffs, tick_player_buffs,
    cure_curse,
    get_weaken_penalty, is_silenced, is_dreaded,
    format_player_status_line,
)

def compute_enemy_attributes(enemy_key):
    template = ENEMIES[enemy_key]
    race_name = template["race"]
    race_mods = ENEMY_RACES[race_name].get("mods", {})
    personal_mods = template.get("mods", {})

    base = {attr: 0 for attr in ATTRIBUTES}
    for attr, mod in race_mods.items():
        base[attr] += mod
    for attr, mod in personal_mods.items():
        base[attr] += mod
    return base

def enemy_stats(enemy_key, player=None):
    template = ENEMIES[enemy_key]
    attrs = compute_enemy_attributes(enemy_key)
    
    multiplier = get_difficulty_multiplier_from_time(player) if player else 1.0
    
    base_hp = template["base_hp"]
    str_mod = attrs["Strength"]
    con_mod = attrs["Constitution"]
    dex_mod = attrs["Dexterity"]

    scaled_hp = int(base_hp * multiplier)
    scaled_str = int(str_mod * (1 + (multiplier - 1) * 0.7))
    scaled_con = int(con_mod * (1 + (multiplier - 1) * 0.6))
    scaled_dex = int(dex_mod * (1 + (multiplier - 1) * 0.5))

    return {
        "key": enemy_key,
        "name": template["name"],
        "hp": scaled_hp,
        "max_hp": scaled_hp,
        "str_mod": scaled_str,
        "con_mod": scaled_con,
        "dex_mod": scaled_dex,
        "level": template["level"],
        "multiplier": round(multiplier, 2)
    }

def get_effective_attribute(player, attr_name):
    """Return effective attribute value after applying curse penalty.
    Works for Strength, Constitution, Dexterity, Charisma, Learning, Wisdom, etc.
    """
    # Base from attributes
    base = player["attributes"].get(attr_name, 0)
    # Equipment bonuses
    equip_mods = get_total_equipment_mods(player)
    total = base + equip_mods.get(attr_name, 0)
    
    # Apply curse penalty if present
    for debuff in player.get("active_debuffs", []):
        if debuff.get("type") == "curse":
            penalty = debuff.get("penalty", 2)
            total -= penalty

    # Apply weaken penalty to Strength only
    if attr_name == "Strength":
        total -= get_weaken_penalty(player)
    
    # Apply buffs (if any)
    for buff in player.get("active_buffs", []):
        if buff.get("type") == "blessing" or buff.get("stat") == "all":
            total += buff.get("value", 0)
        elif buff.get("stat") == attr_name:
            total += buff.get("value", 0)
    
    return total

def player_str_mod(player):
    return player["attributes"]["Strength"]


def player_con_mod(player):
    return player["attributes"]["Constitution"]


def player_dex_mod(player):
    return player["attributes"]["Dexterity"]


def compute_player_stats(player):
    p_str = get_effective_attribute(player, "Strength")
    p_con = get_effective_attribute(player, "Constitution")
    p_dex = get_effective_attribute(player, "Dexterity")
    if player.get("training_buff"):
        p_str += player["training_buff"].get("strength", 0)
    return p_str, p_con, p_dex


def format_enemy_status_line(enemy, extra=""):
    """Return one HUD line for a single enemy.

    Collects the standard status flags (slowed / stunned / blinded) into a
    parenthetical, then appends the caller-supplied ``extra`` string.  The
    caller is responsible for the leading ``[N]`` index prefix and the
    trailing newline.

    Examples
    --------
    Basic call (standard combat)::

        format_enemy_status_line(e)
        # "Vileheart Spiderling - HP: 34 (Slowed)"

    Boss call with extra data (superboss HUD)::

        format_enemy_status_line(boss, extra=" [Devour: 2/3]")
        # "Slitcurrent - HP: 88 (Stunned) [Devour: 2/3]"
    """
    statuses = []
    if enemy.get("slowed"):
        statuses.append("Slowed")
    if enemy.get("stunned"):
        statuses.append("Stunned")
    if enemy.get("blinded"):
        statuses.append("Blinded")
    if enemy.get("frozen"):
        statuses.append("Frozen")
    if any(d["type"] == "burn" for d in enemy.get("active_debuffs", [])):
        statuses.append("Burning")
    if enemy.get("expose_stacks", 0) > 0:
        statuses.append(f"Exposed×{enemy['expose_stacks']}")
    status_str = f" ({', '.join(statuses)})" if statuses else ""
    return f"{enemy['name']} - HP: {enemy['hp']}{status_str}{extra}"


def prune_dead(enemies):
    """Return a new list containing only enemies with hp > 0."""
    return [e for e in enemies if e["hp"] > 0]

def print_superboss_header(player, floor, boss_name, extra_gimmick_line=""):
    from utils import format_time
    time_str = format_time(player.get("time_minutes", 0))
    print(f"Dungeon Floor {floor} - Superboss: {boss_name} | Time: {time_str}")
    if extra_gimmick_line:
        print(extra_gimmick_line)
    status_line = format_player_status_line(player)
    print(f"\nYour HP: {player['current_hp']} {status_line}".rstrip())

def enemy_attack(enemy, player, p_con, defending, extra_logic=None):
    """Execute one standard attack action for a single enemy.

    Handles the shared logic that every enemy attack must go through:

    1. ``tick_enemy_debuffs`` — dot/blind tick; returns ``'died'`` immediately
       if the enemy's HP drops to zero from status damage.
    2. Stun check — clears the flag, prints the message, returns ``'stunned'``
       without issuing an attack.
    3. Damage roll, block calculation, player-HP mutation, hit/block message,
       and player-death check (returns ``'dead'`` if ``player['current_hp']``
       drops to zero).
    4. ``extra_logic`` hook — called only after a successful hit resolves.

    Parameters
    ----------
    enemy       : enemy dict, mutated in place (hp may change via debuff tick)
    player      : player dict, mutated in place (current_hp reduced on hit)
    p_con       : effective Constitution value used for the block calculation
    defending   : bool — True when the player chose [D]efend this round
    extra_logic : optional callable(enemy, player, enemy_dmg) -> str | None
                  Boss-specific side-effects (poison, curse, flavour text, …).
                  Return a non-empty string to have it printed; return None to
                  suppress output.

    Returns
    -------
    ``'died'``    enemy died from dot damage; caller should skip further logic
    ``'stunned'`` attack skipped; stun flag consumed
    ``'dead'``    attack resolved and player HP reached zero
    ``'hit'``     attack resolved normally; player may or may not have taken dmg
    """
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
        # tick_enemy_debuffs handles countdown and thaw — don't clear frozen here
        return "stunned"

    block = p_con + (5 if defending else 0)
    enemy_dmg = random.randint(2, 7) + enemy["str_mod"] - block
    enemy_dmg = max(0, enemy_dmg)
    player["current_hp"] -= enemy_dmg

    if enemy_dmg > 0:
        print(f"The {enemy['name']} hits you for {enemy_dmg} damage!")
    else:
        print(f"The {enemy['name']} attacks but you block all incoming damage!")

    if extra_logic:
        msg = extra_logic(enemy, player, enemy_dmg)
        if msg:
            print(msg)

    if player["current_hp"] <= 0:
        return "dead"
    return "hit"


def _player_has_abyss_fang(player):
    """Return the Abyss Fang item dict if it's in the player's inventory, else None."""
    for item in player.get("inventory", []):
        if item.get("id") == "abyss_fang" or item.get("special") == "dream_devour":
            return item
    return None


def handle_player_turn(player, enemies, p_str, p_con, p_dex, on_kill=None, _action_override=None):
    """
    Handle a single player turn: Attack, Defend, Use item, or Flee.

    Parameters
    ----------
    player   : player dict (mutated in place)
    enemies  : list of live enemy dicts (mutated in place)
    p_str/p_con/p_dex : effective player stats for this combat
    on_kill  : optional callable(target, enemies) called after a kill via [A]ttack.
               Lets superboss encounters hook in gimmick logic (e.g. floatsam stacks).
    _action_override : if the caller already read the action input (e.g. to render a
               custom HUD first), pass it here to skip the built-in prompt.

    Returns
    -------
    ('continue', defending)  – normal turn completed; defending=True if [D] was chosen
    ('fled',     False)      – player successfully fled or used an escape item
    ('victory',  False)      – all enemies dead after item use
    ('dead',     False)      – player died during item use
    ('retry',    False)      – invalid input; caller should re-prompt the same turn
    """
    if _action_override is None:
        status_str = format_player_status_line(player)
        print(f"\nYour HP: {player['current_hp']} {status_str}".rstrip())
        print("Enemies in the room:")
        for idx, e in enumerate(enemies):
            print(f"  [{idx + 1}] {format_enemy_status_line(e)}")
        # Show Abyss Fang option if the player carries it and it is not on cooldown
        abyss_fang = _player_has_abyss_fang(player)
        abyss_cd = player.get("abyss_fang_cooldown", 0)
        if abyss_fang and abyss_cd <= 0:
            print("[A]ttack  [D]efend  [F]lee  [U]se item  [W]ield the Abyss")
        elif abyss_fang and abyss_cd > 0:
            print(f"[A]ttack  [D]efend  [F]lee  [U]se item  (Abyss Fang recharging: {abyss_cd} turn(s))")
        else:
            print("[A]ttack  [D]efend  [F]lee  [U]se item")
        action = input("Choose: ").strip().lower()
    else:
        action = _action_override

    # ----- ATTACK -----
    if action == "a":
        # Dread: 40% chance the attack falters before target selection
        if is_dreaded(player) and random.random() < 0.40:
            print("Dread grips your weapon arm — your strike goes wide! (Miss)")
            return "continue", False
        if player.get("blinded") and random.random() < 0.25:
            print("You're blinded – your attack misses!")
            return "continue", False
    
        if len(enemies) > 1:
            try:
                choice = int(input("Select target number: ")) - 1
                if choice < 0 or choice >= len(enemies):
                    print("Invalid target selection.")
                    return "retry", False
                target = enemies[choice]
            except ValueError:
                print("Please enter a valid number.")
                return "retry", False
        else:
            target = enemies[0]

        dmg = random.randint(4, 10) + p_str - target["con_mod"]
        dmg = max(0, dmg)
        target["hp"] -= dmg
        print(f"You strike {target['name']} for {dmg} damage!")
        if target["hp"] <= 0:
            print(f"You defeated {target['name']}!")
            if on_kill:
                on_kill(target, enemies)
        return "continue", False

    # ----- DEFEND -----
    elif action == "d":
        print("You brace for impact, raising your guard.")
        return "continue", True

    # ----- USE ITEM -----
    elif action == "u":
        if is_silenced(player):
            print("You are silenced! Your hands cannot reach your pack.")
            return "retry", False
        combat_inventory = [
            (idx, item) for idx, item in enumerate(player.get("inventory", []))
            if item.get("type") in ["consumable", "utility"]
        ]
        if not combat_inventory:
            print("You have no items usable in combat.")
            return "retry", False

        print("\nYour Battle Inventory:")
        for display_idx, (_, itm) in enumerate(combat_inventory):
            print(f"{display_idx+1}. {itm['name']} ({itm['type']})")
        try:
            choice = int(input("Use which item? (0 to cancel): ")) - 1
            if choice < 0 or choice >= len(combat_inventory):
                return "retry", False
            true_idx, item = combat_inventory[choice]
            msg = ""
            target = None

            affects_enemy = any(k in item for k in ["status", "blind_enemy", "base_power", "damage_over_time", "stun_chance"])
            if affects_enemy:
                if len(enemies) > 1:
                    try:
                        t_choice = int(input(f"Select target for {item['name']}: ")) - 1
                        if t_choice < 0 or t_choice >= len(enemies):
                            print("Invalid target choice.")
                            return "retry", False
                        target = enemies[t_choice]
                    except ValueError:
                        print("Invalid input.")
                        return "retry", False
                else:
                    target = enemies[0]

            if "power" in item:
                old_hp = player["current_hp"]
                new_hp = min(old_hp + item["power"], player_max_hp(player))
                healed_amount = new_hp - old_hp
                player["current_hp"] = new_hp
                msg += f"You recover {healed_amount} HP. "
            if "heal_over_time" in item:
                player.setdefault("active_buffs", []).append({
                    "type": "hot",
                    "value": item["heal_over_time"],
                    "remaining": item.get("duration", 3)
                })
                msg += f"You start regenerating {item['heal_over_time']} HP each turn. "
            if "temp_stat" in item:
                stat = item["temp_stat"]
                val = item.get("base_power", 3)
                player.setdefault("active_buffs", []).append({
                    "stat": stat,
                    "value": val,
                    "remaining": item.get("duration", 4)
                })
                msg += f"Your {stat} increases by {val} for {item.get('duration',4)} turns. "
            if "defense_buff" in item:
                player.setdefault("active_buffs", []).append({
                    "type": "defense",
                    "value": item["defense_buff"],
                    "remaining": item.get("duration", 3)
                })
                msg += f"Damage taken reduced by {item['defense_buff']} for {item.get('duration',3)} turns. "
            if item.get("cure_curse"):
                result = cure_curse(player)
                if result == "cured":
                    msg += "The dark curse is lifted! "
                else:
                    msg += "You are not cursed. "
            if item.get("cure_poison"):
                # Remove poison debuff from player
                before = len([d for d in player.get("active_debuffs", []) if d["type"] == "poison"])
                player["active_debuffs"] = [d for d in player.get("active_debuffs", []) if d["type"] != "poison"]
                after = len([d for d in player.get("active_debuffs", []) if d["type"] == "poison"])
                if before > after:
                    msg += "The poison is cleansed from your body. "
                else:
                    msg += "You are not poisoned. "
            if "base_power" in item and "damage_over_time" not in item and "stun_chance" not in item:
                dmg = item["base_power"]
                armor = target["con_mod"]
                if "armor_pierce" in item:
                    armor = max(0, armor - item["armor_pierce"])
                    msg += f"(ignores {item['armor_pierce']} armor) "
                final_dmg = max(1, dmg - armor)
                target["hp"] -= final_dmg
                msg += f"You deal {final_dmg} damage to the {target['name']}! "
            if "poison_damage" in item:
                from combat.status_effects import apply_poison
                apply_poison(target, item["poison_damage"], item.get("poison_duration", 3))
                msg += f"The {target['name']} is poisoned! "
            if "stun_chance" in item:
                if random.random() < item["stun_chance"]:
                    target["stunned"] = True
                    msg += f"The {target['name']} is stunned and loses its next turn! "
                else:
                    msg += "The stun attempt fails. "
            if item.get("status") == "slow":
                target["slowed"] = True
                msg += f"The {target['name']} is slowed. "
            if item.get("blind_enemy"):
                target["blinded"] = True
                target.setdefault("active_debuffs", []).append({
                    "type": "blind",
                    "remaining": 3
                })
                msg += f"The {target['name']} is blinded (reduced dexterity). "
            if "escape_bonus" in item:
                print(msg)
                player["inventory"].pop(true_idx)
                return "fled", False

            print(msg)
            player["inventory"].pop(true_idx)

            enemies[:] = [e for e in enemies if e["hp"] > 0]
            if not enemies:
                return "victory", False
            if player["current_hp"] <= 0:
                return "dead", False

        except (ValueError, IndexError):
            print("Invalid choice.")
            return "retry", False

        return "continue", False

    # ----- WIELD THE ABYSS (Abyss Fang special) -----
    elif action == "w":
        abyss_fang = _player_has_abyss_fang(player)
        if not abyss_fang:
            print("You have no weapon that responds to that command.")
            return "retry", False
        abyss_cd = player.get("abyss_fang_cooldown", 0)
        if abyss_cd > 0:
            print(f"The Abyss Fang is still recharging. ({abyss_cd} turn(s) remaining)")
            return "retry", False

        # --- Flavor text ---
        print("\n" + "≈" * 55)
        print("The Abyss Fang SCREAMS. A void tears open across your")
        print("vision — stolen faces from the Slitcurrent's body flash")
        print("across the blade, mouthing silent warnings. You grip it")
        print("anyway. Reality peels back. You are the wound now.")
        print("≈" * 55)
        input("Press Enter to unleash it...")

        # --- Cost: lose 40% of max HP ---
        max_hp = player_max_hp(player)
        hp_cost = int(max_hp * 0.40)
        player["current_hp"] = max(1, player["current_hp"] - hp_cost)
        print(f"\nThe blade drinks deep — you lose {hp_cost} HP ({player['current_hp']}/{max_hp} remaining).")

        # --- Strength buff: +8 STR for 4 turns ---
        str_bonus = 8
        player.setdefault("active_buffs", []).append({
            "stat": "Strength",
            "value": str_bonus,
            "remaining": 4,
            "source": "abyss_fang",
        })
        print(f"⚔️  Abyss-Tempered: Strength +{str_bonus} for 4 turns!")

        # --- Triple action: 4 turns ---
        player["abyss_triple_actions"] = 4
        print("⚔️  Nightmare Tempo: You act THREE TIMES each turn for 4 turns!")

        # --- Cooldown: 6 turns ---
        player["abyss_fang_cooldown"] = 6
        print("(The blade will recharge in 6 turns.)\n")

        return "continue", False

    # ----- FLEE -----
    elif action == "f":
        effective_player_dex = p_dex
        for debuff in player.get("active_debuffs", []):
            if debuff["type"] == "slow":
                effective_player_dex -= 3

            if player.get("blinded"):
                effective_player_dex -= 2
                print("Your blindness makes escape harder!")
        max_enemy_dex = -999
        for e in enemies:
            eff_enemy_dex = e["dex_mod"]
            if e.get("slowed"):
                eff_enemy_dex -= 2
            if e.get("blinded"):
                eff_enemy_dex -= 3
            if eff_enemy_dex > max_enemy_dex:
                max_enemy_dex = eff_enemy_dex

        roll = random.randint(1, 20) + effective_player_dex
        difficulty = 10 + max_enemy_dex
        if is_dreaded(player):
            difficulty += 4   # dread makes it much harder to turn and run
        if roll >= difficulty:
            print("You successfully flee from battle!")
            return "fled", False
        else:
            print("You fail to escape and expose yourself!")
            return "continue", False

    return "retry", False


def get_race_extra_logic(enemy):
    """Return an extra_logic callable for this enemy based on its race, or None.

    Each function signature must match: extra_logic(enemy, player, dmg) -> str | None
    Only fires when dmg > 0 (the hit landed).
    """
    race = ENEMIES[enemy["key"]]["race"]

    # ----- Beast: Bleed on hit (35% chance) -----
    if race == "Beast":
        def beast_bleed(e, player, dmg):
            if dmg > 0 and random.random() < 0.35:
                bleed_dmg = max(2, dmg // 3)
                result = apply_bleed(player, damage=bleed_dmg, duration=4)
                if result == "applied":
                    return f"The {e['name']}'s claws open a wound! You bleed for {bleed_dmg}/round."
                elif result == "refreshed":
                    return f"The {e['name']} tears your wound wider! ({bleed_dmg}/round)"
            return None
        return beast_bleed

    # ----- Undead: Curse on hit (20% chance) — existing effect, now race-driven -----
    if race == "Undead":
        def undead_curse(e, player, dmg):
            if dmg > 0 and random.random() < 0.20:
                result = apply_curse(player)
                if result == "applied":
                    return f"The {e['name']}'s touch carries a dark curse! All attributes reduced."
                elif result == "already_cursed":
                    return f"The {e['name']}'s curse washes over you, but you are already afflicted."
            return None
        return undead_curse

    # ----- Shadow: Dread on hit (30% chance) -----
    if race == "Shadow":
        def shadow_dread(e, player, dmg):
            if dmg > 0 and random.random() < 0.30:
                result = apply_dread(player, duration=2)
                if result == "applied":
                    return f"The {e['name']}'s darkness fills you with supernatural dread!"
            return None
        return shadow_dread

    # ----- Demon: Weaken on hit (25% chance) -----
    if race == "Demon":
        def demon_weaken(e, player, dmg):
            if dmg > 0 and random.random() < 0.25:
                result = apply_weaken(player, str_penalty=2, duration=3)
                if result == "applied":
                    return f"The {e['name']}'s hellfire saps your strength! STR reduced for 3 turns."
                elif result == "refreshed":
                    return f"Your weakness deepens under the {e['name']}'s assault!"
            return None
        return demon_weaken

    # ----- Vampire: Drain on hit (always, steals dmg//2 HP) -----
    if race == "Vampire":
        def vampire_drain(e, player, dmg):
            if dmg > 0:
                drained = apply_drain(player, e, drain_amount=max(1, dmg // 2))
                if drained > 0:
                    return f"The {e['name']} drains {drained} HP from your life force!"
            return None
        return vampire_drain

    # ----- Fey: Silence on hit (25% chance) -----
    if race == "Fey":
        def fey_silence(e, player, dmg):
            if dmg > 0 and random.random() < 0.25:
                result = apply_silence(player, duration=2)
                if result == "applied":
                    return f"The {e['name']}'s enchantment seals your pack shut for 2 turns!"
            return None
        return fey_silence

    # ----- Abomination: Weaken on hit (35% chance, stronger penalty) -----
    if race == "Abomination":
        def abomination_weaken(e, player, dmg):
            if dmg > 0 and random.random() < 0.35:
                result = apply_weaken(player, str_penalty=3, duration=3)
                if result == "applied":
                    return f"The {e['name']}'s corrosive flesh weakens your muscles! STR -3 for 3 turns."
                elif result == "refreshed":
                    return f"The corruption deepens — your strength ebbs further!"
            return None
        return abomination_weaken

    # ----- Giant: Weaken on hit (30% chance, strongest penalty) -----
    if race == "Giant":
        def giant_weaken(e, player, dmg):
            if dmg > 0 and random.random() < 0.30:
                result = apply_weaken(player, str_penalty=4, duration=2)
                if result == "applied":
                    return f"The {e['name']}'s crushing blow leaves your arms numb! STR -4 for 2 turns."
                elif result == "refreshed":
                    return f"Another bone-crushing hit — your strength fails!"
            return None
        return giant_weaken

    # ----- Gnome (casters): Silence on hit (20% chance) -----
    if race == "Gnome":
        def gnome_silence(e, player, dmg):
            if dmg > 0 and random.random() < 0.20:
                result = apply_silence(player, duration=2)
                if result == "applied":
                    return f"The {e['name']}'s arcane static disrupts your concentration!"
            return None
        return gnome_silence
    
    if race == "Elemental":
        def elemental_blind(e, player, dmg):
            if dmg > 0 and random.random() < 0.30:
                from combat.status_effects import apply_blind
                result = apply_blind(player, duration=2)
                if result == "applied":
                    return f"A burst of searing light from the {e['name']} blinds you!"
                elif result == "refreshed":
                    return f"The {e['name']}'s radiance deepens your blindness!"
            return None
        return elemental_blind

    # No special debuff for this race
    return None


def combat(player, enemy_keys, floor=None, room_num=None, total_rooms=None):
    enemies = [enemy_stats(k, player) for k in enemy_keys]

    print("\nEnemies approach!")
    for e in enemies:
        print(f"- A {e['name']} appears! (HP: {e['hp']})")

    while True:
        # --- Print room header every turn if context is provided ---
        if floor is not None and room_num is not None and total_rooms is not None:
            from utils import format_time
            header = f"Dungeon Floor {floor} - Room {room_num}/{total_rooms} | Time: {format_time(player.get('time_minutes', 0))}"
            print(header)

        p_str, p_con, p_dex = compute_player_stats(player)
        enemies = prune_dead(enemies)
        if not enemies:
            print("All enemies have been defeated!")
            return "victor"

        result, defending = handle_player_turn(player, enemies, p_str, p_con, p_dex)
        if result == "retry":
            continue
        if result in ("fled", "victory", "dead"):
            return result

        # ----- ABYSS FANG TRIPLE ACTION -----
        triple_remaining = player.get("abyss_triple_actions", 0)
        if triple_remaining > 0 and result == "continue":
            extra_attacks = 2   # 3 total actions (1 already taken + 2 bonus)
            for attack_num in range(extra_attacks):
                enemies = prune_dead(enemies)
                if not enemies:
                    break
                print(f"\n⚔️  ABYSS TEMPO — extra action ({attack_num + 2}/3)!")
                sub_result, _ = handle_player_turn(player, enemies, p_str, p_con, p_dex)
                if sub_result in ("fled", "victory", "dead"):
                    return sub_result
            enemies = prune_dead(enemies)
            if not enemies:
                print("All enemies have been defeated!")
                return "victory"

        # ----- ENEMY TURN PHASE -----
        for enemy in enemies[:]:
            if enemy["hp"] <= 0:
                continue
            extra = get_race_extra_logic(enemy)
            outcome = enemy_attack(enemy, player, p_con, defending, extra_logic=extra)
            if outcome == "dead":
                print("You have been slain.")
                return "dead"
            
        input("\nPress Enter to continue...")
        clear_screen()    

        # ----- END OF ROUND MAINTENANCE -----
        enemies = prune_dead(enemies)
        if not enemies:
            print("All enemies have been defeated!")
            return "victory"

        # Tick Abyss Fang cooldown and triple-action counter
        if player.get("abyss_fang_cooldown", 0) > 0:
            player["abyss_fang_cooldown"] -= 1
            if player["abyss_fang_cooldown"] == 0:
                print("⚔️  The Abyss Fang hums — its hunger is renewed.")
        if player.get("abyss_triple_actions", 0) > 0:
            player["abyss_triple_actions"] -= 1
            if player["abyss_triple_actions"] == 0:
                print("⚔️  Nightmare Tempo fades. The triple-action fury ends.")

        msgs, died = tick_player_debuffs(player)
        for m in msgs:
            print(m)
        if died:
            print("You have been slain.")
            return "dead"

        for m in tick_player_buffs(player):
            print(m)