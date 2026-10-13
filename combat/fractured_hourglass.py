"""Fractured Hourglass — reusable temporal consumable (Chrysalis superboss drop).

Intended behavior (previously it was consumed with no effect at all):
  * Works for any actor (player or ally) — actor-based convention.
  * FREE ACTION: using it does not consume the actor's turn (the action
    handlers return "retry" so the actor can still act).
  * Reduces ALL of the user's skill cooldowns by 1.
  * The item is NOT consumed. Instead the user's hourglass goes on cooldown
    (actor["hourglass_cooldown"]), ticked at end of round in
    combat_engine._tick_all_state() and the superboss round-end loop.

Combat-only: blocked outside battle via inventory.is_combat_only_item() —
its temporal energy only bends skill cooldowns, which exist in combat.
"""
from combat.combat_io import c_print
from combat.skills import reduce_all_cooldowns

HOURGLASS_SPECIAL = "cooldown_reset"
HOURGLASS_ITEM_ID = "fractured_hourglass"
HOURGLASS_COOLDOWN_TURNS = 3  # turns before it can bend time again
HOURGLASS_REDUCTION = 1       # how much every cooldown is reduced by


def is_fractured_hourglass(item):
    """Return True if this item instance is the Fractured Hourglass."""
    if not isinstance(item, dict):
        return False
    return (
        item.get("special") == HOURGLASS_SPECIAL
        or item.get("id") == HOURGLASS_ITEM_ID
    )


def get_hourglass_cooldown(actor):
    """Return the actor's remaining hourglass cooldown (0 = ready)."""
    return actor.get("hourglass_cooldown", 0)


def use_fractured_hourglass(actor, is_player=False):
    """Use the hourglass as a free action.

    Returns True if it was used (cooldowns reduced + cooldown started).
    Returns False if refused (still recharging / nothing on cooldown).
    Callers should NOT remove the item and should return "retry" so the
    actor keeps their turn either way.
    """
    indent = "" if is_player else "  "
    who = "You" if is_player else actor.get("name", "The ally")
    pronoun = "your" if is_player else "their"

    cd = get_hourglass_cooldown(actor)
    if cd > 0:
        c_print(f"{indent}⏳ The Fractured Hourglass is still recharging — {cd} turn(s) remaining.")
        return False

    active = [
        sid for sid, value in actor.get("skill_cooldowns", {}).items()
        if value > 0
    ]
    if not active:
        c_print(f"{indent}⏳ All of {pronoun} skills are already ready — "
                "the hourglass's sands stay still.")
        return False

    reduce_all_cooldowns(actor, HOURGLASS_REDUCTION)
    actor["hourglass_cooldown"] = HOURGLASS_COOLDOWN_TURNS
    turn_word = "turn" if is_player else "turns"
    c_print(f"{indent}⏳ {who} {turn_word} the Fractured Hourglass — time shudders. "
            f"All of {pronoun} cooldowns are reduced by {HOURGLASS_REDUCTION}!")
    c_print(f"{indent}   The hourglass begins recharging ({HOURGLASS_COOLDOWN_TURNS} turns).")
    return True


def tick_hourglass_cooldown(actor, prefix="  "):
    """Decrement the hourglass cooldown at end of round.

    Returns True if it just became ready again.
    """
    if actor.get("hourglass_cooldown", 0) > 0:
        actor["hourglass_cooldown"] -= 1
        if actor["hourglass_cooldown"] == 0:
            name = actor.get("name", "The wielder")
            c_print(f"{prefix}⏳ The Fractured Hourglass is ready again for {name}.")
            return True
    return False
