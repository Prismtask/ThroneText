"""Captain's Cutlass weapon mechanics and combat state management."""
import random
from combat.ally import get_alive_allies


# ─── Equipped Check ───────────────────────────────────────────────────────

def _actor_has_captain_cutlass(actor):
    """Return the Cutlass weapon dict if equipped on any actor, else None."""
    equipment = actor.get("equipped", {})
    if isinstance(equipment, dict):
        weapon = equipment.get("weapon")
        if weapon and weapon.get("special") == "captain_cutlass":
            return weapon
    return None

def _player_has_captain_cutlass(player):
    """Return the Cutlass weapon dict if equipped, else None."""
    return _actor_has_captain_cutlass(player)


# ─── Availability / UI Helpers ──────────────────────────────────────────

def is_captain_cutlass_available(actor):
    """Return True if Cutlass is equipped on actor and Crew Rally is off cooldown."""
    if not _actor_has_captain_cutlass(actor):
        return False
    return actor.get("cutlass_rally_cooldown", 0) <= 0


def get_captain_cutlass_cooldown_display(actor):
    """Return cooldown display string for the combat UI, or empty string."""
    if not _actor_has_captain_cutlass(actor):
        return ""
    cd = actor.get("cutlass_rally_cooldown", 0)
    if cd > 0:
        return f"(Crew Rally recharging: {cd} turn(s))"
    return ""


# ─── Combat State Lifecycle ─────────────────────────────────────────────

def clear_captain_cutlass_state(player):
    """Clear all Captain's Cutlass combat state for the player (backward-compat)."""
    _clear_captain_cutlass_state_actor(player, player)


def _clear_captain_cutlass_state_actor(actor, player_ref=None):
    """Clear all Captain's Cutlass combat state for any actor.

    player_ref is the player dict (needed to clean buffs from allies).
    """
    actor["cutlass_riposte_count"] = 0
    actor["cutlass_rally_active"] = False
    actor["cutlass_rally_turns"] = 0
    actor.pop("cutlass_rally_dr", None)
    actor.pop("cutlass_rally_attack_mult", None)
    actor.pop("cutlass_rally_ignore_high_tide", None)
    # Remove rally buffs from actor
    for buff in actor.get("active_buffs", [])[:]:
        if buff.get("source") == "captain_rally":
            actor["active_buffs"].remove(buff)
    # Remove rally buffs from allies (only if we have a player ref)
    if player_ref is not None:
        for ally in get_alive_allies(player_ref):
            for buff in ally.get("active_buffs", [])[:]:
                if buff.get("source") == "captain_rally":
                    ally["active_buffs"].remove(buff)
    # Also remove from player if actor is an ally
    if player_ref is not None and actor is not player_ref:
        for buff in player_ref.get("active_buffs", [])[:]:
            if buff.get("source") == "captain_rally":
                player_ref["active_buffs"].remove(buff)


def tick_captain_cutlass(player, prefix="  "):
    """Tick Captain's Cutlass cooldown for the player (backward-compat)."""
    return _tick_captain_cutlass_actor(player, player, prefix)


def _tick_captain_cutlass_actor(actor, player_ref=None, prefix="  "):
    """Tick Captain's Cutlass cooldown and rally duration for any actor.

    Returns True if rally just ended.
    """
    # Reset per-turn riposte counter
    actor["cutlass_riposte_count"] = 0

    # Cooldown tick
    if actor.get("cutlass_rally_cooldown", 0) > 0:
        actor["cutlass_rally_cooldown"] -= 1
        if actor["cutlass_rally_cooldown"] == 0:
            name = actor.get("name", "The wielder")
            c_print(f"{prefix}⚓ The Captain's Cutlass hums — Crew Rally is ready for {name}!")

    # Rally duration tick
    if actor.get("cutlass_rally_active"):
        actor["cutlass_rally_turns"] -= 1
        if actor["cutlass_rally_turns"] == 0:
            name = actor.get("name", "The wielder")
            c_print(f"{prefix}⚓ {name}'s rally ends. The spectral wind fades.")
            actor["cutlass_rally_active"] = False
            actor["cutlass_rally_ignore_high_tide"] = False
            actor.pop("cutlass_rally_dr", None)
            actor.pop("cutlass_rally_attack_mult", None)
            # Remove rally buffs from actor
            for buff in actor.get("active_buffs", [])[:]:
                if buff.get("source") == "captain_rally":
                    actor["active_buffs"].remove(buff)
            # Remove from allies/player
            if player_ref is not None:
                for ally in get_alive_allies(player_ref):
                    for buff in ally.get("active_buffs", [])[:]:
                        if buff.get("source") == "captain_rally":
                            ally["active_buffs"].remove(buff)
                if actor is not player_ref:
                    for buff in player_ref.get("active_buffs", [])[:]:
                        if buff.get("source") == "captain_rally":
                            player_ref["active_buffs"].remove(buff)
            return True
        elif actor["cutlass_rally_turns"] == 1:
            # Second turn: ramp to 30%
            actor["cutlass_rally_attack_mult"] = 0.30
            c_print(f"{prefix}⚓ The rally intensifies! Attack power +30%!")
    return False


# ─── Player Action: Crew Rally ───────────────────────────────────────────

def use_crew_rally(player):
    """Handle the 'Crew Rally' action for the player.

    Returns (result, defending) tuple.
    """
    return _use_crew_rally_actor(player, is_player=True)


def _use_crew_rally_actor(actor, is_player=False, player=None):
    """Handle the 'Crew Rally' action for any actor (player or ally).

    Returns (result, defending) tuple.
    player param is required for ally calls (to access party list).
    """
    cutlass = _actor_has_captain_cutlass(actor)
    if not cutlass:
        if is_player:
            c_print("You have no weapon that responds to that command.")
        else:
            c_print(f"{actor['name']} has no weapon that responds to that command.")
        return "retry", False

    rally_cd = actor.get("cutlass_rally_cooldown", 0)
    if rally_cd > 0:
        c_print(f"Crew Rally is still recharging. ({rally_cd} turn(s) remaining)")
        return "retry", False

    name = "You" if is_player else actor['name']
    c_print("\n" + "⚓" * 55)
    if is_player:
        c_print("You raise the Captain's Cutlass high!")
        c_print("'Stand fast, crew! For the Everlong!'")
    else:
        c_print(f"{actor['name']} raises the Captain's Cutlass high!")
        c_print(f"'{actor['name']} rallies the crew! For the Everlong!'")
    c_print("A spectral wind fills the battlefield — the crew rallies!")
    c_print("⚓" * 55)
    c_input("Press Enter to rally the crew...")

    actor["cutlass_rally_active"] = True
    actor["cutlass_rally_turns"] = 2
    actor["cutlass_rally_cooldown"] = 5
    actor["cutlass_rally_ignore_high_tide"] = True

    # Initiative boost: DEX +3 to all party members
    actual_player = player if player is not None else (actor if is_player else None)
    if actual_player:
        party = [actual_player] + get_alive_allies(actual_player)
    else:
        party = [actor]
    for member in party:
        member.setdefault("active_buffs", []).append({
            "stat": "Dexterity",
            "value": 3,
            "remaining": 2,
            "source": "captain_rally",
        })

    # Damage reduction percentage based on party size
    dr = min(0.20, len(party) * 0.05)
    actor["cutlass_rally_dr"] = dr
    c_print(f"\n  ⚓ Damage reduced by {int(dr*100)}% for 2 turns!")

    # Attack bonus starts at 20%
    actor["cutlass_rally_attack_mult"] = 0.20
    c_print("  ⚓ Attack power increased by 20% for the first turn!")

    # Suppress High Tide vulnerability during rally
    stacks = actor.get("cutlass_high_tide_stacks", 0)
    if stacks > 0:
        c_print("  ⚓ The High Tide's curse is held at bay during the rally!")

    return "continue", False


# ─── Riposte: Captain's Authority ───────────────────────────────────────

def trigger_captain_riposte(actor, enemy, is_player=True):
    """Trigger riposte when the actor is attacked while equipped with the Cutlass.

    Max 2 ripostes per turn.
    """
    if not _actor_has_captain_cutlass(actor):
        return

    current = actor.get("cutlass_riposte_count", 0)
    if current >= 2:
        return

    actor["cutlass_riposte_count"] = current + 1

    from combat.stats import get_effective_attribute
    p_str = get_effective_attribute(actor, "Strength")
    riposte_dmg = max(1, p_str // 2 + 3 + random.randint(1, 4))
    enemy["hp"] -= riposte_dmg
    from combat.helpers import format_damage_msg
    prefix = "[CAPTAIN'S AUTHORITY] "
    if is_player:
        c_print("  ⚔ " + prefix + format_damage_msg(actor['name'], enemy['name'], riposte_dmg, skill_name="Riposte"))
    else:
        c_print("  ⚔ " + prefix + format_damage_msg(actor['name'], enemy['name'], riposte_dmg, skill_name="Riposte"))
    if enemy["hp"] <= 0:
        c_print(f"  The {enemy['name']} is struck down by {actor['name']}'s riposte!")
        # Trigger high tide stack for riposte kills too
        check_high_tide_kill(actor, enemy)


# ─── High Tide Battle ────────────────────────────────────────────────────

def check_high_tide_kill(actor, target):
    """Check if an enemy death should add a High Tide stack.

    Stacks are floor-persistent (reset when leaving dungeon or entering next floor).
    """
    if not _actor_has_captain_cutlass(actor):
        return

    floor = actor.get("floor")
    if floor is not None and actor.get("cutlass_high_tide_floor") != floor:
        actor["cutlass_high_tide_floor"] = floor
        actor["cutlass_high_tide_stacks"] = 0

    current = actor.get("cutlass_high_tide_stacks", 0)
    if current < 5:
        actor["cutlass_high_tide_stacks"] = current + 1
        c_print(f"  [HIGH TIDE] The Cutlass thirsts! Stack {current + 1}/5! (+5% attack, +10% incoming damage)")
    else:
        c_print(f"  [HIGH TIDE] The Cutlass is at maximum tide! (5/5)")


def get_high_tide_attack_bonus(actor, base_dmg):
    """Return bonus damage from High Tide stacks."""
    if not _actor_has_captain_cutlass(actor):
        return 0
    stacks = actor.get("cutlass_high_tide_stacks", 0)
    if stacks <= 0:
        return 0
    return int(base_dmg * stacks * 0.05)


def apply_high_tide_vulnerability(player, incoming_dmg):
    """Increase incoming damage based on High Tide stacks.

    Rally suppresses this vulnerability while active.
    """
    if not _player_has_captain_cutlass(player):
        return incoming_dmg
    if player.get("cutlass_rally_ignore_high_tide"):
        return incoming_dmg
    stacks = player.get("cutlass_high_tide_stacks", 0)
    if stacks <= 0:
        return incoming_dmg
    extra = int(incoming_dmg * stacks * 0.10)
    if extra > 0:
        c_print(f"  [HIGH TIDE] The curse of the sea deepens — +{extra} damage from the tide!")
    return incoming_dmg + extra


def apply_rally_damage_reduction(player, incoming_dmg):
    """Apply percentage damage reduction from Crew Rally."""
    if not player.get("cutlass_rally_active"):
        return incoming_dmg
    dr = player.get("cutlass_rally_dr", 0)
    if dr <= 0:
        return incoming_dmg
    reduced = int(incoming_dmg * (1.0 - dr))
    if reduced < incoming_dmg:
        c_print(f"  [RALLY] The spectral crew shields you! (-{incoming_dmg - reduced} damage)")
    return reduced


from combat.combat_io import c_print, c_input, c_clear
def get_rally_attack_bonus(player, base_dmg):
    """Return bonus damage from Crew Rally attack multiplier."""
    if not player.get("cutlass_rally_active"):
        return 0
    mult = player.get("cutlass_rally_attack_mult", 0)
    if mult <= 0:
        return 0
    return int(base_dmg * mult)
