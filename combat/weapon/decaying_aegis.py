# combat/weapon/decaying_aegis.py
"""Decaying Aegis — Sylvana's unique armour.

Fully actor-based so it works for the player and allies.

Effect:
  - At the start of each round, while no Aegis shield is active and the
    cooldown is ready, raise a barrier equal to 15% of the wearer's max HP.
  - The shield decays by 4% of max HP per round.
  - When the shield breaks (absorbed or decayed), it cannot be raised again
    for 5 rounds.

State keys on the actor dict:
    decaying_aegis_cd: int — rounds until the shield can be raised again
"""

from combat.combat_io import c_print

SHIELD_PCT = 0.15
DECAY_PCT = 0.04
COOLDOWN_ROUNDS = 5


def _actor_has_decaying_aegis(actor):
    equipment = actor.get("equipped", {})
    if isinstance(equipment, dict):
        armor = equipment.get("armor")
        if armor and armor.get("special") == "decaying_aegis":
            return True
    return False


def _actor_max_hp(actor):
    if actor.get("is_ally"):
        return max(1, int(actor.get("max_hp", actor.get("current_hp", 1)) or 1))
    from character import player_max_hp
    return max(1, int(player_max_hp(actor)))


def _owner_name(actor):
    if actor.get("is_ally"):
        return actor.get("name", "The wearer")
    return "You"


def _active_aegis_buff(actor):
    for buff in actor.get("active_buffs", []):
        if buff.get("source") == "decaying_aegis":
            return buff
    return None


def begin_decaying_aegis_combat(actor):
    """Scrub stale Aegis state at combat start."""
    actor.pop("decaying_aegis_cd", None)
    buffs = actor.get("active_buffs")
    if buffs:
        actor["active_buffs"] = [
            b for b in buffs if b.get("source") != "decaying_aegis"
        ]


def clear_decaying_aegis_state(actor):
    """Remove battle-scoped Aegis state (combat end)."""
    begin_decaying_aegis_combat(actor)


def apply_decaying_aegis_turn_start(actor):
    """Tick the shield: decay it, or raise it when off cooldown."""
    if not _actor_has_decaying_aegis(actor):
        return
    if actor.get("current_hp", 0) <= 0:
        return

    max_hp = _actor_max_hp(actor)
    buff = _active_aegis_buff(actor)

    if buff is not None:
        decay = max(1, int(max_hp * DECAY_PCT))
        buff["value"] = max(0, int(buff.get("value", 0)) - decay)
        if buff["value"] <= 0:
            actor["active_buffs"].remove(buff)
            actor["decaying_aegis_cd"] = COOLDOWN_ROUNDS
            c_print(
                f"  [Mirror] {_owner_name(actor)}'s Decaying Aegis shatters - "
                f"it will re-form in {COOLDOWN_ROUNDS} rounds."
            )
        else:
            c_print(
                f"  [Mirror] {_owner_name(actor)}'s Decaying Aegis cracks and thins "
                f"({buff['value']} absorb left)."
            )
        return

    cd = int(actor.get("decaying_aegis_cd", 0) or 0)
    if cd > 0:
        actor["decaying_aegis_cd"] = cd - 1
        return

    shield = max(1, int(max_hp * SHIELD_PCT))
    actor.setdefault("active_buffs", []).append({
        "type": "barrier",
        "value": shield,
        "remaining": 99,
        "source": "decaying_aegis",
    })
    c_print(
        f"  [Mirror] {_owner_name(actor)}'s Decaying Aegis raises a mirrored shield "
        f"({shield} absorb)."
    )
