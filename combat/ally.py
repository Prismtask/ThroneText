# combat/ally.py
"""Ally system - companions recruited from house monster girls."""
import random
from combat.stats import compute_enemy_attributes
from resources.enemies import ENEMIES, ENEMY_RACES
from resources.races_classes import ATTRIBUTES
from inventory import get_total_equipment_mods, remove_item_by_reference

ALLY_STAT_MULTIPLIER = 0.8   # Allies are 80% as strong as original enemies (base)
ALLY_LEVEL_STAT_BONUS = 0.15 # Allies gain 0.15 stat per level above level 1
ALLY_HP_MULTIPLIER = 0.70    # Allies have 70% of original enemy HP


def ally_max_hp(ally):
    """Compute ally max HP based on Constitution and level-up bonuses (same formula as player)."""
    con = ally["attributes"]["Constitution"]
    bonus = ally.get("level_hp_bonus", 0)
    return int(15 + con * 3 + bonus)


def create_ally_from_girl(girl):
    """Convert a house monster girl dict into a combat-ready ally dict.

    girl format from house:
        {"key": "...", "name": "...", "level": N, "affection": N, "captured_on": N}
    """
    enemy_key = girl.get("key")
    template = ENEMIES.get(enemy_key)
    if not template:
        # Fallback for missing template
        from combat.elemental import neutral_profile
        level = girl.get("level", 1)
        return {
            "name": girl.get("name", "Companion"),
            "key": enemy_key or "unknown",
            "level": level,
            "attributes": {attr: 1 for attr in ATTRIBUTES},
            "current_hp": 30,
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
            "level_hp_bonus": girl.get("level_hp_bonus", max(0, (level - 1) * 4)),
            "elemental_res": neutral_profile(),
            "elemental_dmg": neutral_profile(),
        }

    attrs = compute_enemy_attributes(enemy_key)
    level = girl.get("level", 1)

    # Scale down attributes for balance with level-based scaling
    # Formula: base_stat * 0.8 + (level - 1) * 0.15, minimum 1
    scaled_attrs = {}
    for attr in ATTRIBUTES:
        base = attrs.get(attr, 0)
        level_bonus = (level - 1) * ALLY_LEVEL_STAT_BONUS
        scaled = max(1, int(base * ALLY_STAT_MULTIPLIER + level_bonus))
        scaled_attrs[attr] = scaled

    # Apply engagement ring stat bonus (from proposal)
    ring_bonus = girl.get("ring_stat_bonus")
    if ring_bonus:
        for attr, val in ring_bonus.items():
            scaled_attrs[attr] = scaled_attrs.get(attr, 0) + val

    ally = {
        "name": girl.get("name", template["name"]),
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
        "level_hp_bonus": girl.get("level_hp_bonus", max(0, (girl.get("level", 1) - 1) * 4)),
        "level_cap": girl.get("level_cap", 10),
        # Skill system fields
        "passive_skill": girl.get("passive_skill", None),  # Race-based passive
        "innate_skills": girl.get("innate_skills", []),    # 2 innate skills unique to girl
        "learned_skills": girl.get("learned_skills", []),  # List of learned skill_ids
        "learning": girl.get("learning", None),             # Current skill being learned: {"skill_id": "...", "exp": 0, "exp_needed": 300}
        "skill_cooldowns": girl.get("skill_cooldowns", {}), # skill_id -> cooldown_remaining
        "skill_mastery": girl.get("skill_mastery", {}),     # skill_id -> exp_count (for mastery levels)
    }

    # Compute HP based on scaled Constitution + level
    ally["max_hp"] = ally_max_hp(ally)
    ally["current_hp"] = ally["max_hp"]

    # Add elemental stats from race
    from combat.elemental import compute_ally_elemental
    e_res, e_dmg = compute_ally_elemental(ally)
    ally["elemental_res"] = e_res
    ally["elemental_dmg"] = e_dmg
    
    # Initialize skill system
    from combat.ally_skills import initialize_ally_skills
    initialize_ally_skills(ally, enemy_key, template.get("race"))

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
        from combat.status_effects import get_weaken_penalty
        total -= get_weaken_penalty(ally)

    for buff in ally.get("active_buffs", []):
        if buff.get("type") in ("blessing", "well_rested") or buff.get("stat") == "all":
            total += buff.get("value", 0)
        elif buff.get("stat") == attr_name:
            total += buff.get("value", 0)

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
    return f"{prefix} {ally['name'][:12]:<12} {ally['current_hp']:>3}/{ally['max_hp']:<3}{mg_symbol}{active_mark}"


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
    """Return list of alive allies from player."""
    return [a for a in player.get("allies", []) if a.get("current_hp", 0) > 0]


def get_all_party_members(player):
    """Return list of all alive party members: [player] + alive allies."""
    party = [player]
    party.extend(get_alive_allies(player))
    return party


def equip_ally_item(ally, item, player, target_slot=None):
    """Equip an item on an ally from the player's inventory."""
    from inventory import add_item_to_inventory
    item_slot = item["slot"]
    # Resolve dual accessory slots
    if item_slot == "accessory":
        if target_slot in ("accessory1", "accessory2"):
            pass  # use caller-specified slot
        elif ally.get("equipped", {}).get("accessory1") is None:
            target_slot = "accessory1"
        elif ally.get("equipped", {}).get("accessory2") is None:
            target_slot = "accessory2"
        else:
            target_slot = "accessory1"
    else:
        target_slot = item_slot

    old = ally.get("equipped", {}).get(target_slot)
    if old:
        # Return old item to player inventory
        if not add_item_to_inventory(player, old):
            return f"Cannot equip {item['name']} on {ally['name']} — your inventory is full."
    ally["equipped"][target_slot] = item
    # Remove item from player inventory
    if item in player.get("inventory", []):
        player["inventory"].remove(item)
    # Recalculate ally elemental profile
    from combat.elemental import compute_ally_elemental
    res, dmg = compute_ally_elemental(ally)
    ally["elemental_res"] = res
    ally["elemental_dmg"] = dmg
    return f"Equipped {item['name']} on {ally['name']}."


def unequip_ally_slot(ally, slot, player):
    """Unequip an item from an ally and return to player's inventory."""
    from inventory import add_item_to_inventory
    if slot in ally.get("equipped", {}) and ally["equipped"][slot]:
        item = ally["equipped"][slot]
        if add_item_to_inventory(player, item):
            ally["equipped"][slot] = None
            # Recalculate ally elemental profile
            from combat.elemental import compute_ally_elemental
            res, dmg = compute_ally_elemental(ally)
            ally["elemental_res"] = res
            ally["elemental_dmg"] = dmg
            return f"Unequipped {item['name']} from {ally['name']}."
        else:
            return f"Cannot unequip {item['name']} from {ally['name']} — your inventory is full!"
    return "Nothing equipped in that slot."


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
        # Return equipped items to player
        for slot in ["weapon", "armor", "accessory1", "accessory2"]:
            item = ally.get("equipped", {}).get(slot)
            if item:
                if not add_item_to_inventory(player, item):
                    print(f"Your inventory is full! {item['name']} from {ally['name']} was dropped.")
                ally["equipped"][slot] = None

        # Add back to house (only if not already there)
        existing = [g for g in house["monster_girls"] if g.get("key") == ally["key"] and g.get("name") == ally["name"]]
        if not existing:
            house["monster_girls"].append({
                "key": ally["key"],
                "name": ally["name"],
                "level": ally["level"],
                "affection": ally.get("affection", 30),
                "affection_cap": ally.get("affection_cap", 100),
                "engaged": ally.get("engaged", False),
                "married": ally.get("married", False),
                "exp": ally.get("exp", 0),
                "level_hp_bonus": ally.get("level_hp_bonus", 0),
                "level_cap": ally.get("level_cap", 10),
            })


def recruit_ally_from_house(player, girl, house):
    """Recruit a monster girl from house to active party."""
    if len(player.get("allies", [])) >= 3:
        return None, "Your party is full (max 3 allies)."

    ally = create_ally_from_girl(girl)
    player.setdefault("allies", []).append(ally)

    # Remove from house
    house["monster_girls"] = [g for g in house["monster_girls"]
                                if not (g.get("key") == girl.get("key") and g.get("name") == girl.get("name"))]

    return ally, f"{ally['name']} has joined your party!"


# ─────────────────────────────────────────────────────────────────────────────
# ALLY COMBAT ACTIONS
# ─────────────────────────────────────────────────────────────────────────────

def _ally_action_menu(ally, player, enemies):
    """Build action menu for an ally. Returns (menu_str, valid_keys)."""
    actions = []
    actions.append(('a', 'Attack'))
    actions.append(('d', 'Defend'))

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

    menu_str = '  '.join(f'[{key.upper()}]{label}' for key, label in actions)
    valid_keys = [key for key, _ in actions]
    return menu_str, valid_keys


def handle_ally_turn(ally, player, enemies, p_str, p_con, p_dex, p_ler, p_wis, p_cha, on_kill=None):
    """Handle an ally's turn in combat. Player chooses the ally's action.

    Returns: "continue", "victory", "dead", or "retry"
    """
    from combat.combat_ui import print_combat_hud
    from combat.status_effects import is_silenced, is_dreaded
    from character import player_max_hp

    # Reset defending flag each turn so it only applies if they choose Defend THIS turn
    ally["defending_this_turn"] = False

    a_str, a_con, a_dex, a_ler, a_wis, a_cha = compute_ally_stats(ally)

    # Show HUD with this ally marked as active (this already renders the menu block)
    print_combat_hud(player, enemies, active_ally=ally)

    # Fetch the actions behind the scenes to keep the tracking list valid
    _, valid_actions = _ally_action_menu(ally, player, enemies)

    # REMOVED: Redundant text headers and duplicate action list prints
    action = input(f"  ({ally['name']}) Choose action: ").strip().lower()
    while action not in valid_actions:
        print(f"  Invalid choice. Available: {', '.join(valid_actions)}")
        action = input("  Choose: ").strip().lower()

    # ----- SKILLS (numbered 1-9) -----
    if action.isdigit():
        from combat.ally_skills import get_usable_skills_in_combat, execute_ally_skill, format_ally_mastery_label
        if is_silenced(ally):
            print(f"  {ally['name']} is silenced and cannot use skills!")
            return "retry"

        skill_idx = int(action) - 1
        usable_skills = get_usable_skills_in_combat(ally)
        if skill_idx < 0 or skill_idx >= len(usable_skills):
            print("  Invalid skill choice.")
            return "retry"

        skill_id, skill_def = usable_skills[skill_idx]
        print(f"\n  >> {skill_def['name']}: {skill_def['description']}")
        mastery_label = format_ally_mastery_label(skill_id, ally)
        if mastery_label:
            print(f"      Mastery: {mastery_label}")
        input("  Press Enter to use it...")

        all_allies = player.get("allies", [])
        # Track alive enemies before skill so on_kill can fire for newly-dead ones
        alive_before = {id(e) for e in enemies if e["hp"] > 0}
        msg, victory = execute_ally_skill(ally, player, skill_id, skill_def, enemies, all_allies)
        print(f"  {msg}")
        # Trigger on_kill for any enemies that died during this skill use
        if on_kill:
            for e in enemies:
                if e["hp"] <= 0 and id(e) in alive_before:
                    on_kill(e, enemies)
        if victory:
            return "victory"
        return "continue"

    # ----- ATTACK -----
    if action == "a":
        if is_dreaded(ally) and random.random() < 0.40:
            print(f"  Dread grips {ally['name']}'s weapon arm — the strike goes wide! (Miss)")
            return "continue"
        if ally.get("blinded") and random.random() < 0.25:
            print(f"  {ally['name']} is blinded – the attack misses!")
            return "continue"

        if len(enemies) > 1:
            try:
                choice = int(input("  Select target number: ")) - 1
                if choice < 0 or choice >= len(enemies):
                    print("  Invalid target selection.")
                    return "retry"
                target = enemies[choice]
            except ValueError:
                print("  Please enter a valid number.")
                return "retry"
        else:
            target = enemies[0]

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

        dmg = random.randint(3, 8) + scaling_val - target["con_mod"]
        dmg = max(0, dmg)

        # Critical hit check
        from combat.stats import roll_critical_hit, apply_critical_damage, format_critical_tag
        is_crit, _ = roll_critical_hit(ally, "ally", dex=a_dex, lrn=a_ler)
        dmg = apply_critical_damage(dmg, is_crit)

        # Apply elemental damage
        from combat.elemental import calculate_elemental_damage
        element = None
        if equipped_weapon and "elemental_dmg" in equipped_weapon:
            from combat.elemental import get_attack_element
            element = get_attack_element(ally, equipped_weapon)
        final_dmg = calculate_elemental_damage(dmg, ally, target, element)
        target["hp"] -= final_dmg

        verb = "strikes"
        if "Dexterity" in scaling_stats:
            verb = "shoots" if "bow" in equipped_weapon.get("id", "") else "pierces"
        elif "Learning" in scaling_stats:
            verb = "blasts"

        # Elemental flavor text
        elemental_tags = {"fire": "[FIRE]", "water": "[ICE]", "thunder": "[THUNDER]",
                          "wind": "[WIND]", "earth": "[EARTH]", "light": "[LIGHT]", "dark": "[DARK]"}
        tag = elemental_tags.get(element, "")
        crit_tag = format_critical_tag(is_crit)
        if tag:
            print(f"  {ally['name']} {verb} {target['name']} for {final_dmg} damage!{crit_tag} {tag}")
        else:
            print(f"  {ally['name']} {verb} {target['name']} for {final_dmg} damage!{crit_tag}")
        if target["hp"] <= 0:
            if on_kill:
                on_kill(target, enemies)
            print(f"  {ally['name']} defeated {target['name']}!")
        return "continue"

    # ----- DEFEND -----
    elif action == "d":
        print(f"  {ally['name']} braces for impact, raising their guard.")
        ally["defending_this_turn"] = True
        return "continue"

    # ----- USE ITEM -----
    elif action == "u":
        combat_items = [
            (idx, item) for idx, item in enumerate(player.get("inventory", []))
            if item.get("type") in ["consumable", "utility"]
        ]
        if not combat_items:
            print("  No usable items in the shared inventory.")
            return "retry"

        print("\n  Shared Battle Inventory:")
        for display_idx, (_, itm) in enumerate(combat_items):
            qty = itm.get("count", 1)
            qty_str = f" x{qty}" if qty > 1 else ""
            print(f"  {display_idx+1}. {itm['name']}{qty_str} ({itm['type']})")

        try:
            choice = int(input("  Use which item? (0 to cancel): ")) - 1
            if choice < 0 or choice >= len(combat_items):
                return "retry"
            true_idx, item = combat_items[choice]
            msg = ""
            target = None

            # Determine if item affects an enemy
            affects_enemy = any(k in item for k in ["status", "blind_enemy", "base_power", "damage_over_time", "stun_chance"])
            if affects_enemy:
                if len(enemies) > 1:
                    try:
                        t_choice = int(input(f"  Select target for {item['name']}: ")) - 1
                        if t_choice < 0 or t_choice >= len(enemies):
                            print("  Invalid target choice.")
                            return "retry"
                        target = enemies[t_choice]
                    except ValueError:
                        print("  Invalid input.")
                        return "retry"
                else:
                    target = enemies[0]

            # Healing items affect the ally using them
            if "power" in item and item.get("type") == "consumable":
                old_hp = ally["current_hp"]
                new_hp = min(old_hp + item["power"], ally["max_hp"])
                healed_amount = new_hp - old_hp
                ally["current_hp"] = new_hp
                msg += f"{ally['name']} recovers {healed_amount} HP. "

            if "heal_over_time" in item:
                ally.setdefault("active_buffs", []).append({
                    "type": "hot",
                    "value": item["heal_over_time"],
                    "remaining": item.get("duration", 3)
                })
                msg += f"{ally['name']} starts regenerating {item['heal_over_time']} HP each turn. "

            if "temp_stat" in item:
                stat = item["temp_stat"]
                val = item.get("base_power", 3)
                ally.setdefault("active_buffs", []).append({
                    "stat": stat,
                    "value": val,
                    "remaining": item.get("duration", 4)
                })
                msg += f"{ally['name']}'s {stat} increases by {val} for {item.get('duration',4)} turns. "

            if "defense_buff" in item:
                ally.setdefault("active_buffs", []).append({
                    "type": "defense",
                    "value": item["defense_buff"],
                    "remaining": item.get("duration", 3)
                })
                msg += f"Damage taken by {ally['name']} reduced by {item['defense_buff']} for {item.get('duration',3)} turns. "

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

            if "base_power" in item and "damage_over_time" not in item and "stun_chance" not in item:
                dmg = item["base_power"]
                armor = target["con_mod"]
                if "armor_pierce" in item:
                    armor = max(0, armor - item["armor_pierce"])
                    msg += f"(ignores {item['armor_pierce']} armor) "
                final_dmg = max(1, dmg - armor)
                target["hp"] -= final_dmg
                msg += f"{ally['name']} deals {final_dmg} damage to {target['name']}! "

            if "poison_damage" in item:
                from combat.status_effects import apply_poison
                apply_poison(target, item["poison_damage"], item.get("poison_duration", 3))
                msg += f"{target['name']} is poisoned! "

            if "stun_chance" in item:
                if random.random() < item["stun_chance"]:
                    target["stunned"] = True
                    msg += f"{target['name']} is stunned! "
                else:
                    msg += "The stun attempt fails. "

            if item.get("status") == "slow":
                target["slowed"] = True
                msg += f"{target['name']} is slowed. "

            if item.get("blind_enemy"):
                target["blinded"] = True
                target.setdefault("active_debuffs", []).append({
                    "type": "blind",
                    "remaining": 3
                })
                msg += f"{target['name']} is blinded. "

            print(f"  {msg}")
            remove_item_by_reference(player, item)

            if not [e for e in enemies if e["hp"] > 0]:
                return "victory"
            if ally["current_hp"] <= 0:
                return "dead"

        except (ValueError, IndexError):
            print("  Invalid choice.")
            return "retry"
        return "continue"

    return "retry"
