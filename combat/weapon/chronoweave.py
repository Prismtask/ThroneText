# combat/weapon/chronoweave.py
"""Chronoweave Mantle armor mechanics — Entangled Chrysalis drop.

Fully actor-based so the mantle works identically for the player and allies:
  - Turn start: if HP < 50%, gain 1 Momentum stack (max 10).
    Momentum grants +3% damage per stack (applied in calculate_elemental_damage).
  - Once per floor: an otherwise fatal hit is survived at 1 HP and grants
    +50% dodge for 1 turn. (Does not stack with the Dryad Protector wedding
    accessory, which is player-only.)

State keys on the actor dict:
    chronoweave_survive_floor: int|None — floor where fatal survival was used
"""

from combat.combat_io import c_print

MOMENTUM_CAP = 10
FATAL_SURVIVE_DODGE = 0.50
FATAL_SURVIVE_DODGE_TURNS = 1


def _actor_has_chronoweave(actor):
    """Return True if the actor has the Chronoweave Mantle equipped as armor."""
    equipment = actor.get("equipped", {})
    if isinstance(equipment, dict):
        armor = equipment.get("armor")
        if armor and armor.get("special") == "chronoweave":
            return True
    return False


def _actor_max_hp(actor):
    """Return max HP for a player or ally actor."""
    if actor.get("race"):  # Allies carry a race key; the player does not
        return actor.get("max_hp", actor.get("current_hp", 1))
    from character import player_max_hp
    return player_max_hp(actor)


def _owner_name(actor):
    """Return a possessive display name for the mantle's wearer."""
    if actor.get("is_ally"):
        return f"{actor.get('name', 'The wielder')}'s"
    return "Your"


# ─── Turn-Start Momentum ─────────────────────────────────────────────────

def apply_chronoweave_turn_start(actor):
    """Turn start: if HP < 50%, gain 1 Momentum stack (max 10)."""
    if not _actor_has_chronoweave(actor):
        return
    cur_hp = actor.get("current_hp", 0)
    if cur_hp <= 0:
        return
    max_hp = _actor_max_hp(actor)
    if max_hp <= 0:
        return
    if cur_hp < int(max_hp * 0.5):
        from combat.status_effects import apply_momentum, get_momentum_stacks
        result = apply_momentum(actor, 1, cap=MOMENTUM_CAP)
        if result in ("applied", "reinforced"):
            c_print(f"  ⏳ {_owner_name(actor)} Chronoweave Mantle weaves a new thread — Momentum {get_momentum_stacks(actor)}/{MOMENTUM_CAP}!")


# ─── Once-Per-Floor Fatal Survival ───────────────────────────────────────

def check_chronoweave_fatal_survival(actor, incoming_dmg):
    """Once per floor: survive an otherwise fatal hit at 1 HP, gain +50% dodge for 1 turn.

    Returns (incoming_dmg_to_apply, survived_bool).
    """
    if not _actor_has_chronoweave(actor):
        return incoming_dmg, False

    cur = actor.get("current_hp", 0)
    if cur <= 0 or cur - incoming_dmg > 0:
        return incoming_dmg, False

    floor = actor.get("floor")
    if floor is None:
        # No floor context (e.g. scripted fights): fall back to once per combat
        floor = "combat"
    if actor.get("chronoweave_survive_floor") == floor:
        return incoming_dmg, False

    actor["chronoweave_survive_floor"] = floor
    actor.setdefault("active_buffs", []).append({
        "type": "evasion",
        "value": FATAL_SURVIVE_DODGE,
        "remaining": FATAL_SURVIVE_DODGE_TURNS,
        "source": "chronoweave",
    })

    name = actor.get("name", "You") if actor.get("is_ally") else "You"
    pronoun = "them" if actor.get("is_ally") else "you"
    c_print("  ⏳ " + "~*~ " * 14)
    c_print(f"  {_owner_name(actor)} Chronoweave Mantle flares — every timeline where the wearer fell,")
    c_print(f"  every self that never made it, reaches out and holds {pronoun} up!")
    c_print(f"  {name} survives at 1 HP and gains +50% dodge for 1 turn!")
    c_print("  ⏳ " + "~*~ " * 14)

    return max(0, cur - 1), True
