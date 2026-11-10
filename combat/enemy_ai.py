from combat.combat_io import c_print
# enemy_ai.py – enemy turn logic and racial status effects
import random
from combat.status_effects import (
    apply_bleed, apply_curse, apply_dread, apply_weaken,
    apply_drain, apply_silence, tick_enemy_debuffs, get_weaken_pct,
    get_bleed_feast_multiplier
)
from resources.enemies import ENEMIES
from combat.weapon.wedding_specials import (
    apply_wedding_dodge_bonus,
    apply_wedding_on_dodge,
    apply_wedding_damage_reduction,
    apply_wedding_fatal_blow_survival,
    apply_wedding_on_damage_taken,
    apply_wedding_enemy_accuracy_penalty,
    apply_wedding_enemy_attack_pre_damage,
)
from combat.helpers import _player_has_tarnished_jade
 

def _get_fear_multiplier(enemy):
    """Fear suppresses damage for the whole turn; read it before debuff ticks."""
    for debuff in enemy.get("active_debuffs", []):
        if debuff.get("type") == "fear":
            return max(0.0, 1.0 - debuff.get("value", 0))
    return 1.0


def begin_enemy_turn(enemy, all_enemies=None):
    """Run start-of-turn upkeep and action gates for an enemy.

    Extracted from :func:`enemy_attack` so the generic enemy AI
    (``combat/enemy_skills.py``) can resolve the status gates once and then
    execute any action — basic attack, skill, AoE, heal — without ticking
    debuffs once per target.

    Returns ``(outcome, fear_mult)``. ``outcome`` is ``None`` when the enemy
    can act, otherwise one of the historical enemy_attack return strings:
    ``"died"``, ``"asleep"``, ``"paralyzed"``, ``"stunned"``, ``"missed"``,
    ``"confused"``.
    """
    from combat.helpers import format_damage_msg

    # --- Check fear BEFORE ticking (so it applies this full turn) ---
    fear_mult = _get_fear_multiplier(enemy)

    # Tick enemy debuffs (poison, burn, blind, fear, etc.)
    msgs, died = tick_enemy_debuffs(enemy)
    for m in msgs:
        c_print(m)
    if died:
        return "died", fear_mult

    # Event Horizon: Mending Roil — enemies regenerate on their turn
    _rift_regen = enemy.get("rift_regen_pct", 0.0)
    if _rift_regen > 0 and enemy.get("max_hp", 0) > 0 and enemy.get("hp", 0) < enemy["max_hp"]:
        _heal = max(1, int(enemy["max_hp"] * _rift_regen))
        enemy["hp"] = min(enemy["max_hp"], enemy["hp"] + _heal)
        c_print(f"  🌀 {enemy['name']} mends its wounds (+{_heal} HP).")

    if enemy.get("asleep"):
        c_print(f"The {enemy['name']} is fast asleep...")
        return "asleep", fear_mult

    if enemy.get("paralyzed"):
        c_print(f"The {enemy['name']} is paralyzed and cannot move!")
        return "paralyzed", fear_mult

    if enemy.get("stunned"):
        c_print(f"The {enemy['name']} is stunned and cannot act!")
        enemy["stunned"] = False
        # A stunned monster girl stays off-balance until her next turn, so
        # the player still gets the +35% capture window when the net is
        # thrown (combat/capture.py). Ticked in tick_enemy_debuffs.
        if enemy.get("monster_girl"):
            enemy["capture_stagger"] = max(
                int(enemy.get("capture_stagger", 0) or 0), 1
            )
        return "stunned", fear_mult

    if enemy.get("frozen"):
        c_print(f"The {enemy['name']} is frozen solid and cannot act!")
        return "stunned", fear_mult

    # --- BLIND CHECK ---
    if enemy.get("blinded"):
        blind_chance = 0.40
        for debuff in enemy.get("active_debuffs", []):
            if debuff.get("type") == "blind":
                blind_chance = debuff.get("value", 0.40)
                break
        if random.random() < blind_chance:
            c_print(f"The {enemy['name']} is blinded and flails wildly — it misses!")
            return "missed", fear_mult

    # --- CONFUSION CHECK ---
    if enemy.get("confused"):
        confusion_chance = 0.30
        for debuff in enemy.get("active_debuffs", []):
            if debuff.get("type") == "confusion":
                confusion_chance = debuff.get("value", 0.30)
                break
        if random.random() < confusion_chance:
            if all_enemies and len(all_enemies) > 1:
                other_enemies = [e for e in all_enemies if e is not enemy and e["hp"] > 0]
                if other_enemies:
                    victim = random.choice(other_enemies)
                    c_print(f"The {enemy['name']} is confused and attacks {victim['name']} instead!")
                    raw_dmg = random.randint(2, 7) + enemy.get("str_mod", 0)
                    victim["hp"] -= raw_dmg
                    c_print("  " + format_damage_msg(enemy['name'], victim['name'], raw_dmg, skill_name="Confused"))
                    if victim["hp"] <= 0:
                        c_print(f"  {victim['name']} is defeated by friendly fire!")
                    return "confused", fear_mult
            c_print(f"The {enemy['name']} is confused and stumbles — it misses!")
            return "missed", fear_mult

    return None, fear_mult


def _try_enemy_attack_dodge(enemy, player, skill_name=None):
    """Resolve the target's dodge roll and any on-dodge effects.

    Returns True when the attack is dodged. Extracted so AoE abilities can
    skip the roll without duplicating the wedding / Duskfall Veil logic.
    """
    from combat.helpers import format_damage_msg
    from combat.stats import get_dodge_chance

    dodge_chance = get_dodge_chance(player, enemy)
    # Wedding dodge bonuses + enemy accuracy penalty (player only)
    dodge_chance += apply_wedding_dodge_bonus(player)
    dodge_chance += apply_wedding_enemy_accuracy_penalty(player)
    # Cap dodge at 80% to prevent absolute immunity
    dodge_chance = min(dodge_chance, 0.80)
    if dodge_chance <= 0 or random.random() >= dodge_chance:
        return False

    if skill_name:
        c_print(f"{player['name']} evades the {enemy['name']}'s {skill_name}!")
    else:
        c_print(f"The {enemy['name']} lunges at {player['name']} — but {player['name']} dodges out of the way!")
    apply_wedding_on_dodge(player, enemy)
    # Duskfall Veil: the veil answers every dodge with a counter-strike
    for buff in player.get("active_buffs", []):
        if buff.get("type") == "dodge_counter" and buff.get("remaining", 0) > 0:
            if player.get("is_ally"):
                from combat.ally import get_ally_effective_attribute
                counter_stat = get_ally_effective_attribute(player, "Dexterity")
            else:
                from combat.stats import get_effective_attribute
                counter_stat = get_effective_attribute(player, "Dexterity")
            counter_dmg = max(1, int(counter_stat * buff.get("value", 0.5) / 2) + random.randint(1, 3))
            enemy["hp"] -= counter_dmg
            c_print("  " + format_damage_msg(player['name'], enemy['name'], counter_dmg, skill_name="Dusk Counter"))
            if enemy["hp"] <= 0:
                c_print(f"  The {enemy['name']} is cut down by the counter!")
            break
    return True


def enemy_attack(enemy, player, p_con, defending, extra_logic=None, armor_mult=1.0,
                 temp_str_bonus=0, all_enemies=None, actual_player=None, *,
                 power_mult=1.0, flat_bonus=0, skill_name=None,
                 element_override=None, skip_turn_start=False, allow_dodge=True):
    """Resolve one enemy strike against a single party member.

    Keyword-only parameters are used by the regular-enemy ability kits
    (``combat/enemy_skills.py``):

    ``power_mult`` / ``flat_bonus`` — scale the raw strike (skills).
    ``skill_name`` — shown in the damage log; also tags dodge messages.
    ``element_override`` — force the strike's element (e.g. a fire breath).
    ``skip_turn_start`` — caller already ran :func:`begin_enemy_turn`.
    ``allow_dodge`` — False for AoE skills that should not be evaded.
    """
    # Imported once here so the name is always bound. It used to be imported
    # inside the confusion/friendly-fire branch only, which crashed with
    # UnboundLocalError in the reflection-damage section when that branch
    # hadn't run (e.g. the first attack that triggers reflection damage).
    from combat.helpers import format_damage_msg

    # Reset the per-strike damage marker read by the ability AI. It is set
    # once damage lands so on-hit statuses never proc on a fully blocked hit.
    enemy["_last_attack_damage"] = 0

    if skip_turn_start:
        fear_mult = _get_fear_multiplier(enemy)
    else:
        turn_outcome, fear_mult = begin_enemy_turn(enemy, all_enemies=all_enemies)
        if turn_outcome:
            return turn_outcome

    # Event Horizon: Piece of Relationship (+7 tier) — mark attackers that
    # target an ally (regardless of whether the blow lands).
    from combat.weapon.piece_of_relationship import maybe_mark_attacker
    maybe_mark_attacker(enemy, player, actual_player)

    # --- DODGE CHECK ---
    if allow_dodge and _try_enemy_attack_dodge(enemy, player, skill_name):
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
        c_print(f"The {enemy['name']}'s attack glances off {player['name']}'s divine shield!")
        return "blocked"

    # --- BASE DAMAGE ---
    block = p_con // 2 + (5 if defending else 0)
    block = int(block * armor_mult)
    # Per-target armor scaling (e.g. White Knight Expose: ignores CON per stack)
    _armor_scale = player.get("enemy_attack_armor_mult", 1.0)
    try:
        _armor_scale = max(0.0, min(1.0, float(_armor_scale)))
    except (TypeError, ValueError):
        _armor_scale = 1.0
    if _armor_scale != 1.0:
        block = int(block * _armor_scale)

    # Apply weaken/curse penalties to enemy attack damage
    effective_str = enemy.get("str_mod", 0)
    weaken_pct = get_weaken_pct(enemy)
    for debuff in enemy.get("active_debuffs", []):
        if debuff.get("type") == "curse" and "Strength" in debuff.get("stats", []):
            effective_str = max(0, effective_str - debuff.get("penalty", 0))
    if weaken_pct > 0:
        effective_str = int(effective_str * (1.0 - weaken_pct))
    
    raw_dmg = random.randint(2, 7) + effective_str + temp_str_bonus

    # Critical hit check
    from combat.stats import roll_critical_hit, apply_critical_damage, format_critical_tag
    is_crit, _, _ = roll_critical_hit(enemy, "enemy")  # enemies: capped, no overflow
    raw_dmg = apply_critical_damage(raw_dmg, is_crit)
    crit_tag = format_critical_tag(is_crit)

    # Skill power (regular-enemy ability kits). Multiplied before armor so
    # heavy CON still matters; flat_bonus lands after the multiplier.
    if power_mult != 1.0:
        raw_dmg = int(raw_dmg * max(0.0, power_mult))
    if flat_bonus:
        raw_dmg += int(flat_bonus)

    raw_dmg = int(raw_dmg * fear_mult)
    base_dmg = raw_dmg - block
    base_dmg = max(0, base_dmg)

    # Apply the enemy's own percentage damage buffs (e.g. Big Bad Wolf enrage/
    # howl, Wicked Witch power surges). Sources stack additively.
    from combat.status_effects import get_damage_buff_multiplier
    _damage_buff_mult = get_damage_buff_multiplier(enemy)
    if _damage_buff_mult != 1.0:
        base_dmg = int(base_dmg * _damage_buff_mult)

    # --- VULNERABLE CHECK ---
    vulnerable_mult = 1.0
    for debuff in player.get("active_debuffs", []):
        if debuff.get("type") == "vulnerable":
            vulnerable_mult = 1.0 + debuff.get("value", 0)
            break
    base_dmg = int(base_dmg * vulnerable_mult)

    # Apply elemental damage based on enemy's elemental profile
    from combat.elemental import calculate_elemental_damage, get_damage_element
    enemy_dmg = base_dmg
    element = None
    if base_dmg > 0:
        element = element_override or get_damage_element(enemy.get("elemental_dmg", {}))
        if element:
            enemy_dmg = calculate_elemental_damage(base_dmg, enemy, player, element)
        else:
            enemy_dmg = base_dmg

    # --- DEFENSE BUFFS (flat reduction) ---
    defense_reduction = 0
    for buff in player.get("active_buffs", []):
        if buff.get("type") in ("defense", "arcane_ward"):
            defense_reduction += buff.get("value", 0)
    if defense_reduction > 0:
        enemy_dmg = max(0, enemy_dmg - defense_reduction)

    # --- PERCENTAGE DEFENSE BUFFS (multiplicative reduction) ---
    defense_pct = 0.0
    for buff in player.get("active_buffs", []):
        if buff.get("type") in ("defense_pct", "arcane_ward"):
            # arcane_ward may also have a percentage component
            if buff.get("type") == "arcane_ward":
                continue  # arcane_ward is flat only
            defense_pct += buff.get("value", 0)
    if defense_pct > 0 and enemy_dmg > 0:
        defense_pct = min(defense_pct, 0.8)  # Cap at 80% total reduction
        enemy_dmg = int(enemy_dmg * (1 - defense_pct))

    # Apply Constitution milestone damage reduction
    from combat.stat_milestones import get_constitution_bonus
    con_reduction = get_constitution_bonus(player)
    if con_reduction > 0 and enemy_dmg > 0:
        enemy_dmg = max(0, enemy_dmg - con_reduction)

    # Constitution weapon defense: +Con//2 flat damage reduction when wielding a con_defense weapon
    equipped_weapon = player.get("equipped", {}).get("weapon")
    if equipped_weapon and equipped_weapon.get("con_defense") and enemy_dmg > 0:
        con_val = player.get("attributes", {}).get("Constitution", 0)
        if player.get("is_ally"):
            from combat.ally import get_ally_effective_attribute
            con_val = get_ally_effective_attribute(player, "Constitution")
        else:
            from combat.stats import get_effective_attribute
            con_val = get_effective_attribute(player, "Constitution")
        con_def = con_val // 2
        if con_def > 0:
            enemy_dmg = max(0, enemy_dmg - con_def)

    # Apply Barbarian passive damage reduction
    from combat.skills import apply_passive_to_damage_taken
    enemy_dmg = apply_passive_to_damage_taken(player, enemy_dmg)

    # Apply ally race passive damage reduction (Abomination, Giant, etc.)
    if player.get("is_ally"):
        from combat.ally_skills import get_race_damage_reduction
        reduction = get_race_damage_reduction(player)
        if reduction > 0:
            enemy_dmg = int(enemy_dmg * (1 - reduction))

    # Form tradition damage reduction (Guarded — every equipped slot)
    from combat.form_perks import get_form_damage_reduction
    form_dr = get_form_damage_reduction(player)
    if form_dr > 0 and enemy_dmg > 0:
        enemy_dmg = int(enemy_dmg * (1 - form_dr))

    # Palette's Brush: Umber aura damage reduction (player or ally wielder)
    from combat.weapon.palette_brush import get_brush_damage_reduction
    brush_dr = get_brush_damage_reduction(player)
    if brush_dr > 0 and enemy_dmg > 0:
        enemy_dmg = int(enemy_dmg * (1 - brush_dr))

    # Wedding damage reduction (slime_absorb, stone_endurance, etc.)
    is_elemental = element is not None
    enemy_dmg = apply_wedding_damage_reduction(player, enemy_dmg, is_elemental=is_elemental, element=element)

    # Captain's Cutlass: High Tide vulnerability + Rally damage reduction (player or ally wielder)
    if actual_player:
        from combat.weapon.captain_cutlass import apply_high_tide_vulnerability, apply_rally_damage_reduction
        enemy_dmg = apply_high_tide_vulnerability(player, enemy_dmg)
        enemy_dmg = apply_rally_damage_reduction(player, enemy_dmg)

    # Chronoweave Mantle: once-per-floor fatal survival (player or ally wielder)
    from combat.weapon.chronoweave import check_chronoweave_fatal_survival
    enemy_dmg, _ = check_chronoweave_fatal_survival(player, enemy_dmg)

    # Wedding fatal blow survival (bark_shield)
    enemy_dmg = apply_wedding_fatal_blow_survival(player, enemy_dmg)

    # --- Tarnished Jade trigger check (before applying damage) ---
    if actual_player and _player_has_tarnished_jade(player) and all_enemies:
        from combat.weapon.tarnished_jade import check_tarnished_jade_trigger
        should_apply, _ = check_tarnished_jade_trigger(
            player, enemy_dmg, all_enemies, enemy, "enemy_attack",
            is_player=(player is actual_player),
        )
        if not should_apply:
            c_print(f"  The {enemy['name']}'s attack is REPULSED by the Tarnished Jade!")
            c_print(f"  {player['name']} takes 0 damage! [Divine Intervention]")
            if extra_logic:
                msg = extra_logic(enemy, player, 0)
                if msg:
                    c_print(msg)
            return "hit"

    # Final floor
    enemy_dmg = max(0, enemy_dmg)

    # Wonderland: Cheshire Cat's Favor — enemies may miss entirely
    if actual_player:
        from wonderland_curses import get_cheshire_dodge_chance
        dodge_chance = get_cheshire_dodge_chance(actual_player)
        if dodge_chance > 0 and random.random() < dodge_chance:
            c_print(f"  😸 The Cheshire Cat's grin flickers — the {enemy['name']} swings at empty air!")
            return "hit"  # no damage dealt, but still counts as a "hit" for combat flow

    # Pandemonium: Crystal Fragility curse — player & allies take more damage
    if actual_player and actual_player.get("pandemonium_curse"):
        from pandemonium_curses import apply_damage_taken_multiplier
        enemy_dmg = apply_damage_taken_multiplier(actual_player, enemy_dmg)

    # Wonderland Shadow: Off With Their Heads — player takes more damage
    if actual_player:
        from wonderland_curses import get_shadow_damage_taken_multiplier
        shadow_dmg_mult = get_shadow_damage_taken_multiplier(actual_player)
        if shadow_dmg_mult > 0:
            enemy_dmg = int(enemy_dmg * (1.0 + shadow_dmg_mult))

    # --- DAMAGE ABSORPTION (Slime Absorption / Adaptive Membrane) ---
    # While active, a share of incoming damage is converted into healing.
    absorption_pct = 0.0
    for buff in player.get("active_buffs", []):
        if buff.get("type") == "damage_absorption" and buff.get("remaining", 0) > 0:
            absorption_pct += buff.get("value", 0)
    if absorption_pct > 0 and enemy_dmg > 0:
        absorbed = int(enemy_dmg * min(absorption_pct, 0.9))
        if absorbed > 0:
            enemy_dmg -= absorbed
            if player.get("is_ally"):
                abs_max_hp = player.get("max_hp", 100)
            else:
                from character import player_max_hp
                abs_max_hp = player_max_hp(player)
            old_hp = player["current_hp"]
            player["current_hp"] = min(old_hp + absorbed, abs_max_hp)
            healed = player["current_hp"] - old_hp
            c_print(f"  {player['name']} absorbs {absorbed} damage! (+{healed} HP)")

    # --- BARRIER ABSORPTION ---
    from combat.status_effects import absorb_damage
    enemy_dmg, barrier_absorbed = absorb_damage(player, enemy_dmg)
    if barrier_absorbed > 0:
        c_print(f"  Your barrier absorbs {barrier_absorbed} damage!")

    player["current_hp"] -= enemy_dmg
    enemy["_last_attack_damage"] = int(enemy_dmg)

    # --- MIRROR GUARD THORNS ---
    # Sylvana's Mirror Guard turns the shield itself into a weapon. The
    # attacker takes fixed pure damage whenever it connects with her (even
    # if the barrier ate the whole blow).
    if enemy_dmg > 0 or barrier_absorbed > 0:
        for buff in player.get("active_buffs", []):
            if buff.get("type") == "mirror_thorns" and buff.get("remaining", 0) > 0:
                thorns = int(buff.get("value", 0) or 0)
                if thorns > 0:
                    enemy["hp"] -= thorns
                    c_print(
                        f"  [Mirror Guard] {enemy['name']} takes {thorns} "
                        f"pure damage from the reflection!"
                    )
                    if enemy["hp"] <= 0:
                        c_print(f"  The {enemy['name']} is shattered by the backlash!")
                break

    # Track the last elemental source that struck this unit (Perfect Mimicry)
    if element and enemy_dmg > 0:
        player["_last_element_hit"] = element

    # --- REFLECTION DAMAGE ---
    if enemy_dmg > 0:
        total_reflect = 0.0
        for buff in player.get("active_buffs", []):
            if buff.get("type") == "reflection" and buff.get("remaining", 0) > 0:
                total_reflect += buff.get("value", 0)
        if total_reflect > 0:
            reflect_dmg = int(enemy_dmg * total_reflect)
            if reflect_dmg > 0:
                enemy["hp"] -= reflect_dmg
                c_print("  " + format_damage_msg(player['name'], enemy['name'], reflect_dmg, skill_name="Reflect"))
                if enemy["hp"] <= 0:
                    c_print(f"  The {enemy['name']} is shattered by the backlash!")

    # Tarnished Jade: pin on taking damage (player or ally wielder)
    if _player_has_tarnished_jade(player):
        from combat.weapon.tarnished_jade import add_tarnished_jade_pin
        add_tarnished_jade_pin(player)
        pins = player.get("tarnished_jade_pins", 0)
        owner = "Your" if (actual_player is None or player is actual_player) else f"{player['name']}'s"
        c_print(f"  📌 {owner} Tarnished Jade embeds a pin! ({pins}/10)")

    elemental_tags = {"fire": "[FIRE]", "water": "[WATER]", "thunder": "[THUNDER]",
                      "wind": "[WIND]", "earth": "[EARTH]", "light": "[LIGHT]", "dark": "[DARK]"}
    tag = elemental_tags.get(element, "")

    if enemy_dmg > 0:
        c_print(format_damage_msg(enemy['name'], player['name'], enemy_dmg,
                                  element=element, crit=bool(crit_tag), skill_name=skill_name))
        # Wedding retribution effects (pharaohs_curse, infernal_crown, keening_wail)
        apply_wedding_on_damage_taken(player, enemy, enemy_dmg, "hit")
        # Captain's Cutlass: Captain's Authority riposte (player or ally)
        from combat.weapon.captain_cutlass import trigger_captain_riposte
        if actual_player and player is actual_player:
            trigger_captain_riposte(actual_player, enemy)
        elif player is not actual_player and player is not None:
            # Target is an ally — check if ally has Cutlass
            trigger_captain_riposte(player, enemy, is_player=False)
    elif skill_name:
        c_print(f"The {enemy['name']}'s {skill_name} is fully blocked by {player['name']}!")
    else:
        c_print(f"The {enemy['name']} attacks but {player['name']} blocks all incoming damage!")

    if extra_logic:
        msg = extra_logic(enemy, player, enemy_dmg)
        if msg:
            c_print(msg)

    # ── Elemental Profile Debuff (secondary channel) ──
    if enemy_dmg > 0:
        from combat.elemental_debuffs import try_apply_elemental_debuff
        elem_msg = try_apply_elemental_debuff(enemy, player, enemy_dmg)
        if elem_msg:
            c_print(elem_msg)

    if player["current_hp"] <= 0:
        return "dead"
    return "hit"


def get_race_extra_logic(enemy):
    key = enemy.get("key")
    if not key or key not in ENEMIES:
        return None

    # ── Wonderland floor boss AI (Phase 19) ───────────────────────
    try:
        from combat.wl_floor_bosses import WL_FLOOR_BOSS_MAP
        for floor, (boss_name, boss_key, ai_fn) in WL_FLOOR_BOSS_MAP.items():
            if key == boss_key:
                # Return the boss-specific AI wrapped for extra_logic signature
                def wl_boss_wrapper(e, player, dmg, _ai=ai_fn):
                    return _ai(e, player, dmg)
                return wl_boss_wrapper
    except ImportError:
        pass

    race = ENEMIES[key]["race"]

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
                result = apply_weaken(player, penalty_pct=0.20, duration=3)
                if result == "applied":
                    return f"The {e['name']}'s hellfire saps {player['name']}'s strength! STR reduced for 3 turns."
                elif result == "refreshed":
                    return f"{player['name']}'s weakness deepens under the {e['name']}'s assault!"
            return None
        return demon_weaken

    if race == "Vampire":
        def vampire_drain(e, player, dmg):
            if dmg > 0:
                # Feeds on open wounds — lifesteal doubled while the target bleeds
                mult = get_bleed_feast_multiplier(player)
                drain_amount = max(1, int(dmg * mult / 2))
                drained = apply_drain(player, e, drain_amount=drain_amount)
                if drained > 0:
                    if mult > 1.0:
                        return f"The {e['name']} latches onto the open wound — drains {drained} HP from {player['name']}!"
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
                result = apply_weaken(player, penalty_pct=0.25, duration=3)
                if result == "applied":
                    return f"The {e['name']}'s corrosive flesh weakens {player['name']}'s muscles! STR −25% for 3 turns."
                elif result == "refreshed":
                    return f"The corruption deepens — {player['name']}'s strength ebbs further!"
            return None
        return abomination_weaken

    if race == "Giant":
        def giant_weaken(e, player, dmg):
            if dmg > 0 and random.random() < 0.30:
                result = apply_weaken(player, penalty_pct=0.30, duration=2)
                if result == "applied":
                    return f"The {e['name']}'s crushing blow leaves {player['name']} arms numb! STR −30% for 2 turns."
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

    # ── Storybook (Wonderland) ──────────────────────────────────────
    if race == "Storybook":
        def storybook_twist(e, player, dmg):
            """Storybook enemies can rewrite their own narrative."""
            hp_pct = e["hp"] / e["max_hp"]
            roll = random.random()

            # Narrative Rewrite: heal + buff at low HP
            if hp_pct < 0.35 and roll < 0.25:
                heal = random.randint(4, 10)
                e["hp"] = min(e["max_hp"], e["hp"] + heal)
                return (f"The {e['name']}'s story rewrites itself — "
                        f"it recovers {heal} HP! (A new chapter begins...)")

            # Plot Twist: random debuff on player
            if dmg > 0 and roll < 0.22:
                twist = random.choice(["confusion", "dread", "silence"])
                if twist == "confusion":
                    from combat.status_effects import apply_confusion
                    result = apply_confusion(player, duration=2)
                    if result == "applied":
                        return (f"The {e['name']} warps the narrative — "
                                f"{player['name']} is confused for 2 turns!")
                elif twist == "dread":
                    from combat.status_effects import apply_dread
                    result = apply_dread(player, duration=2)
                    if result == "applied":
                        return (f"Reality bends around the {e['name']} — "
                                f"{player['name']} is filled with dread!")
                elif twist == "silence":
                    from combat.status_effects import apply_silence
                    result = apply_silence(player, duration=2)
                    if result == "applied":
                        return (f"The {e['name']} closes the book on your voice — "
                                f"{player['name']} is silenced!")

            # Happily Ever After: self-buff when winning
            if hp_pct > 0.60 and roll < 0.15:
                e["str_mod"] = e.get("str_mod", 0) + 1
                return (f"The {e['name']} believes in its happy ending — "
                        f"its strength grows!")
            return None
        return storybook_twist

    return None