"""Moonlight Greatsword — unique greatsword.

The blade's basic attacks are **physical**. Its weapon skill, **Moonlight**
(combat action, 5-turn cooldown), wraps the steel in lunar light for 3 of the
wielder's turns: every basic attack then becomes a **magical** wave that
strikes **all enemies** at 75% power.

Actor-based per the unique-equipment convention — works for the player and
allies alike. State lives on the actor:

  moonlight_turns     — remaining empowered rounds (0 = inactive)
  moonlight_cooldown  — remaining cooldown before Moonlight can be used again

Lifecycle is wired in ``combat/combat_engine.py`` (``_combat_inner``,
``_tick_all_state``, ``clear_battle_scoped_state``) and mirrored in
``combat/superboss_common.py``.
"""

import random

from combat.combat_io import c_print

MOONLIGHT_DURATION = 3
MOONLIGHT_COOLDOWN = 5
MOONLIGHT_AOE_MULT = 0.75
MOONLIGHT_ELEMENT = "magical"


# ─── Equipped Check ───────────────────────────────────────────────────────

def _actor_has_moonlight_greatsword(actor):
    """Return the Moonlight Greatsword weapon dict if equipped, else None."""
    equipment = actor.get("equipped", {})
    if isinstance(equipment, dict):
        weapon = equipment.get("weapon")
        if weapon and weapon.get("special") == "moonlight_greatsword":
            return weapon
    return None


# ─── Availability / State Helpers ─────────────────────────────────────────

def is_moonlight_available(actor):
    """True if the sword is equipped and Moonlight is ready to activate."""
    if not _actor_has_moonlight_greatsword(actor):
        return False
    return (actor.get("moonlight_cooldown", 0) <= 0
            and actor.get("moonlight_turns", 0) <= 0
            and actor.get("moonlight_pending", 0) <= 0)


def is_moonlight_active(actor):
    """True while basic attacks are empowered by Moonlight."""
    if not _actor_has_moonlight_greatsword(actor):
        return False
    return actor.get("moonlight_turns", 0) > 0


def get_moonlight_status_display(actor):
    """Active/cooldown display string for the combat UI, or empty string."""
    if not _actor_has_moonlight_greatsword(actor):
        return ""
    turns = actor.get("moonlight_turns", 0)
    if turns > 0:
        return f"(Moonlight active: {turns} turn(s))"
    if actor.get("moonlight_pending", 0) > 0:
        return "(Moonlight gathering — next round)"
    cd = actor.get("moonlight_cooldown", 0)
    if cd > 0:
        return f"(Moonlight recharging: {cd} turn(s))"
    return ""


# ─── Round Lifecycle ──────────────────────────────────────────────────────

def apply_moonlight_round_start(actor, prefix="  "):
    """Convert the activation round's pending light into active turns.

    Activation consumes a turn, so the empowered window begins next round —
    otherwise the first of the advertised 3 turns would be eaten by the
    action itself. Mirrors Abyss Fang's tempo-pending pattern.
    """
    pending = actor.get("moonlight_pending", 0)
    if pending > 0:
        actor.pop("moonlight_pending")
        actor["moonlight_turns"] = pending
        c_print(f"{prefix}🌙 Moonlight settles over the blade — empowered strikes begin!")
        return True
    return False


def tick_moonlight(actor, prefix="  "):
    """Tick empowered rounds and cooldown at end of round."""
    if actor.get("moonlight_turns", 0) > 0:
        actor["moonlight_turns"] -= 1
        if actor["moonlight_turns"] == 0:
            c_print(f"{prefix}🌙 The moonlight gutters out — the greatsword falls quiet.")
    if actor.get("moonlight_cooldown", 0) > 0:
        actor["moonlight_cooldown"] -= 1
        if actor["moonlight_cooldown"] == 0:
            c_print(f"{prefix}🌙 The Moonlight Greatsword stirs — Moonlight is ready.")


def clear_moonlight_state(actor):
    """Clear all Moonlight combat state (battle-scoped)."""
    actor["moonlight_turns"] = 0
    actor["moonlight_cooldown"] = 0
    actor.pop("moonlight_pending", None)


# ─── Action ───────────────────────────────────────────────────────────────

def use_moonlight(player):
    """Handle the 'Moonlight' action for the player."""
    return _use_moonlight_actor(player, is_player=True)


def _use_moonlight_actor(actor, is_player=False):
    """Handle the 'Moonlight' action for any actor (player or ally).

    Returns (result, defending) tuple.
    """
    weapon = _actor_has_moonlight_greatsword(actor)
    if not weapon:
        if is_player:
            c_print("You have no blade that answers the moon.")
        else:
            c_print(f"{actor.get('name', 'They')} has no blade that answers the moon.")
        return "retry", False

    if actor.get("moonlight_turns", 0) > 0:
        c_print("The moonlight is already in your hands.")
        return "retry", False

    cd = actor.get("moonlight_cooldown", 0)
    if cd > 0:
        c_print(f"The Moonlight Greatsword is still gathering light. "
                f"({cd} turn(s) remaining)")
        return "retry", False

    actor["moonlight_pending"] = MOONLIGHT_DURATION
    actor["moonlight_cooldown"] = MOONLIGHT_COOLDOWN

    c_print("\n" + "≈" * 55)
    if is_player:
        c_print("You raise the Moonlight Greatsword. Pale light beads along the")
        c_print("blade, then spills over the edge like water that forgot how to")
        c_print("fall. The air smells of cold stone and distant tides.")
    else:
        name = actor.get("name", "They")
        c_print(f"{name} raises the Moonlight Greatsword. Pale light beads along")
        c_print("the blade, then spills over the edge like water that forgot how")
        c_print("to fall. The air smells of cold stone and distant tides.")
    c_print(f"For {MOONLIGHT_DURATION} turns, every strike will break as a wave of moonlight.")
    c_print("The light gathers... it will answer from the next round.")
    c_print("≈" * 55 + "\n")
    return "continue", False


# ─── Empowered Basic Attack ───────────────────────────────────────────────

def execute_moonlight_aoe_attack(actor, player_ref, enemies, stats,
                                 is_player=False, on_kill=None, on_hit=None):
    """Replace the basic attack with a magical wave that strikes every enemy.

    ``stats`` is the actor's (Strength, Constitution, Dexterity, Learning,
    Wisdom, Charisma) tuple, matching the values already computed by the
    calling turn handler.
    """
    weapon = _actor_has_moonlight_greatsword(actor)
    if not weapon:
        return

    p_str, p_con, p_dex, p_ler, p_wis, p_cha = stats
    raw_scaling = weapon.get("scaling_stat", ["Strength"])
    scaling_stats = raw_scaling if isinstance(raw_scaling, list) else [raw_scaling]
    stat_values = {
        "Strength": p_str, "Constitution": p_con, "Dexterity": p_dex,
        "Learning": p_ler, "Wisdom": p_wis, "Charisma": p_cha,
    }
    scaling_val = 0
    for stat in scaling_stats:
        if stat in stat_values:
            scaling_val += stat_values[stat]
        else:
            try:
                if is_player:
                    from combat.stats import get_effective_attribute
                    scaling_val += get_effective_attribute(actor, stat)
                else:
                    from combat.ally import get_ally_effective_attribute
                    scaling_val += get_ally_effective_attribute(actor, stat)
            except Exception:
                pass
    if weapon.get("scaling_mult"):
        scaling_val = int(scaling_val * weapon["scaling_mult"])

    from combat.stat_milestones import get_strength_bonus
    dice = (4, 10) if is_player else (3, 8)
    dmg = random.randint(*dice) + scaling_val + get_strength_bonus(actor)

    # ── Percentage damage buffs stack additively (power_buff + damage_boost);
    # one power_buff empowers the whole volley ──
    from combat.status_effects import get_damage_buff_multiplier
    _buff_msgs = []
    _damage_buff_mult = get_damage_buff_multiplier(
        actor, consume_power_buff=True, messages=_buff_msgs
    )
    for _buff_msg in _buff_msgs:
        c_print(f"  ⚡ {_buff_msg}")
    if _damage_buff_mult != 1.0:
        dmg = int(dmg * _damage_buff_mult)

    # Profession passive: bonus damage below a HP threshold (player only)
    if is_player:
        from combat.skills import get_player_passive_low_hp_mult
        lp_mult = get_player_passive_low_hp_mult(actor)
        if lp_mult != 1.0:
            dmg = int(dmg * lp_mult)

    # Event Horizon: The Hierophant — basic attacks ×0.75
    from event_horizon import joker_damage_multiplier, joker_crit_modifier
    dmg = int(dmg * joker_damage_multiplier(actor, "basic"))

    # Deed titles (player only)
    if is_player:
        from titles import mod as _title_mod
        title_dmg = _title_mod(actor, "damage_pct")
        if title_dmg:
            dmg = int(dmg * (1.0 + title_dmg))

    from combat.form_perks import (get_outgoing_damage_multiplier,
                                   get_armor_pen_multiplier)
    dmg = int(dmg * get_outgoing_damage_multiplier(actor))
    pen_mult = get_armor_pen_multiplier(actor)

    # ── Critical hit: one roll shared by the whole wave ──
    from combat.stats import (roll_critical_hit, apply_critical_damage,
                              format_critical_tag, CRIT_MULTIPLIER, roll_dodge)
    is_crit, _, overflow_crit = roll_critical_hit(
        actor, "player" if is_player else "ally", dex=p_dex, lrn=p_ler)
    crit_tag = format_critical_tag(is_crit)

    from combat.elemental import calculate_elemental_damage
    from combat.helpers import format_damage_msg
    from combat.status_effects import get_damage_taken_multiplier, apply_healing
    from combat.weapon.chance_and_choice import apply_chance_and_choice
    from combat.weapon.dopo_robe import get_robe_multiplier

    source = actor.get("name") or "You"
    c_print("🌙 Moonlight spills from the blade — waves of pale fire sweep the battlefield!")

    dealt = 0
    cac_state = {}  # Chance and Choice: one coin per action
    for enemy in [e for e in enemies if e.get("hp", 0) > 0 and not e.get("captured")]:
        extra = enemy.get("ally_accuracy_penalty", 0.0) if not is_player else 0.0
        is_dodged, _ = roll_dodge(enemy, actor, extra_chance=extra)
        if is_dodged:
            c_print(f"  The {enemy['name']} slips through the moonlight!")
            continue

        armor = int(enemy.get("con_mod", 0) * pen_mult)
        hit = max(0, dmg - armor)
        hit = int(hit * MOONLIGHT_AOE_MULT)
        hit = apply_critical_damage(hit, is_crit,
                                    multiplier=CRIT_MULTIPLIER + overflow_crit)
        hit = joker_crit_modifier(actor, is_crit, hit)
        hit = int(hit * get_robe_multiplier(actor, player_ref))
        hit = apply_chance_and_choice(actor, hit, cac_state)

        # Hunter's Mark damage bonus (Hawk's Eye buff boosts the mark)
        if enemy.get("hunters_mark"):
            bonus = enemy.get("hunters_mark_bonus", 0.50)
            for buff in actor.get("active_buffs", []):
                if buff.get("type") == "mark_damage_bonus":
                    bonus += buff.get("value", 0)
            hit = int(hit * (1 + bonus))

        # Damage-taken amplification (e.g. Aura of Despair)
        dt_mult = get_damage_taken_multiplier(enemy)
        if dt_mult != 1.0:
            hit = int(hit * dt_mult)

        # Pandemonium: Weakened Resolve curse — the party deals less damage
        if player_ref.get("pandemonium_curse"):
            from pandemonium_curses import apply_damage_dealt_multiplier
            hit = apply_damage_dealt_multiplier(player_ref, hit)

        # Wonderland: Jabberwock's Bane — bonus damage vs boss enemies
        if enemy.get("boss"):
            from wonderland_curses import get_jabberwock_bane_multiplier
            bane_mult = get_jabberwock_bane_multiplier(player_ref)
            if bane_mult > 0:
                hit += int(hit * bane_mult)

        final_dmg = calculate_elemental_damage(hit, actor, enemy,
                                               MOONLIGHT_ELEMENT)
        if on_hit:
            on_hit(enemy, enemies)
        enemy["hp"] -= final_dmg
        dealt += final_dmg
        c_print("  " + format_damage_msg(source, enemy["name"], final_dmg,
                                         element=MOONLIGHT_ELEMENT,
                                         crit=bool(crit_tag)))
        # ── Sky Piercer: execute non-superboss enemies left at/below threshold ──
        from combat.weapon.sky_piercer import check_sky_piercer_execute
        check_sky_piercer_execute(actor, enemy, final_dmg)
        if enemy["hp"] <= 0:
            c_print(f"  {enemy['name']} is overwhelmed by the moonlight!")
            if on_kill:
                on_kill(enemy, enemies)

    # ── Lifesteal applies once to the wave's total (basic-attack parity) ──
    if dealt <= 0:
        return
    if is_player:
        from combat.skills import get_passive_life_steal
        ls = get_passive_life_steal(actor)
        if ls > 0:
            heal = int(dealt * ls)
            if heal > 0:
                actual = apply_healing(actor, heal, source=actor)
                if actual < 0:
                    c_print(f"  [Soul Siphon] The void twists the healing! You take {-actual} damage!")
                elif actual > 0:
                    c_print(f"  [Soul Siphon] You recover {actual} HP.")
    else:
        from combat.ally_skills import get_race_lifesteal, get_race_passive
        rp_ls = get_race_lifesteal(actor)
        if get_race_passive(actor.get("race")) and rp_ls > 0:
            heal = int(dealt * rp_ls)
            if heal > 0:
                actual = apply_healing(actor, heal, source=actor)
                if actual > 0:
                    c_print(f"  {source} recovers {actual} HP.")
    eh_ls = actor.get("_eh_joker_lifesteal", 0) or 0
    if eh_ls > 0:
        heal = int(dealt * eh_ls)
        if heal > 0:
            actual = apply_healing(actor, heal, source=actor)
            if actual > 0:
                c_print(f"  [Death] {source} drains {actual} HP from the wound.")
