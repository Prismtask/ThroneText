from combat.combat_io import c_print, c_input, c_clear
import random
from character import player_max_hp


def _actor_has_tarnished_jade(actor):
    """Return True if actor has Tarnished Jade equipped as armor."""
    equipment = actor.get("equipped", {})
    if isinstance(equipment, dict):
        armor = equipment.get("armor")
        if armor and armor.get("id") == "tarnished_jade":
            return True
    return False

def _player_has_tarnished_jade(player):
    """Return True if player has Tarnished Jade equipped as armor."""
    return _actor_has_tarnished_jade(player)


def add_tarnished_jade_pin(actor, amount=1):
    """Add pin stacks to Tarnished Jade on the actor, up to max 10."""
    if not _actor_has_tarnished_jade(actor):
        return
    current = actor.get("tarnished_jade_pins", 0)
    actor["tarnished_jade_pins"] = min(10, current + amount)


def get_tarnished_jade_str_bonus(actor):
    """Return STR bonus from pin stacks: +1 per 2 stacks."""
    if not _actor_has_tarnished_jade(actor):
        return 0
    return actor.get("tarnished_jade_pins", 0) // 2


def get_tarnished_jade_wis_bonus(actor):
    """Return WIS bonus from pin stacks: +1 per 2 stacks."""
    if not _actor_has_tarnished_jade(actor):
        return 0
    return actor.get("tarnished_jade_pins", 0) // 2


def is_tarnished_jade_weakened(actor):
    """Return True if Wedge Backlash permanent debuff is active."""
    return actor.get("tarnished_jade_weakened", False)


def _compute_divine_lament_damage(actor, pins):
    """Compute Divine Lament damage based on pin stacks and actor stats."""
    from combat.stats import get_effective_attribute
    p_str = get_effective_attribute(actor, "Strength")
    p_wis = get_effective_attribute(actor, "Wisdom")
    return pins * (p_str + p_wis) // 2


def _compute_wedge_backlash_damage(actor, pins):
    """Compute Wedge Backlash damage (reduced)."""
    return _compute_divine_lament_damage(actor, pins) // 2


def _get_actor_max_hp(actor):
    """Get max HP for an actor. Uses player_max_hp for player, dict key for allies."""
    if actor.get("race"):  # Ally has race key, player doesn't
        return actor.get("max_hp", actor.get("current_hp", 1))
    return player_max_hp(actor)


def trigger_divine_lament(actor, enemies, source, is_player=True):
    """Trigger Divine Lament: deal damage to all enemies, heal actor, remove pins."""
    pins = actor.get("tarnished_jade_pins", 0)
    if pins == 0:
        return

    dmg = _compute_divine_lament_damage(actor, pins)

    c_print("\n" + "✦" * 55)
    c_print("  ☁ DIVINE LAMENT ☁")
    c_print("  The Tarnished Jade PINS shatter in unison!")
    c_print("  Heaven's sorrow erupts through the wounds —")
    c_print("  all enemies feel the dragon's grief!")
    c_print("✦" * 55)

    for enemy in enemies:
        if enemy.get("hp", 0) > 0:
            enemy["hp"] -= dmg
            c_print(f"  {enemy['name']} takes {dmg} pure damage from the shattered pins!")
            if enemy["hp"] <= 0:
                c_print(f"  {enemy['name']} is struck down by divine sorrow!")

    # Heal: 5% per pin stack
    max_hp = _get_actor_max_hp(actor)
    heal = int(max_hp * 0.05 * pins)
    actor["current_hp"] = min(max_hp, actor["current_hp"] + heal)
    name = "You" if is_player else actor.get("name", "The wielder")
    c_print(f"  ✨ {name} heal{'s' if not is_player else ''} {heal} HP from the shattered pins! ({actor['current_hp']}/{max_hp})")

    # Remove all pins
    actor["tarnished_jade_pins"] = 0
    c_print("  ✦ All pin stacks consumed. The Jade grows silent.")


def trigger_wedge_backlash(actor, enemies, attacker=None, source="", is_player=True):
    """Trigger Wedge Backlash: reduced damage to single target, heal, debuff, remove pins."""
    pins = actor.get("tarnished_jade_pins", 0)
    if pins == 0:
        return

    dmg = _compute_wedge_backlash_damage(actor, pins)

    # Determine target
    target = attacker
    if target is None and enemies:
        alive = [e for e in enemies if e.get("hp", 0) > 0]
        if alive:
            target = max(alive, key=lambda e: e["hp"])

    name = "You" if is_player else actor.get("name", "The wielder")
    c_print("\n" + "!" * 55)
    c_print("  ☠ WEDGE BACKLASH ☠")
    c_print(f"  {name}'s Tarnished Jade pins shatter too early!")
    c_print("  A feeble divine spark lashes out —")
    c_print("  but the heavens punish the weakness!")
    c_print("!" * 55)

    if target and target.get("hp", 0) > 0:
        target["hp"] -= dmg
        c_print(f"  {target['name']} takes {dmg} reduced pure damage!")
        if target["hp"] <= 0:
            c_print(f"  {target['name']} is struck down by the backlash!")

    # Heal: 5% per pin stack / 2
    max_hp = _get_actor_max_hp(actor)
    heal = int(max_hp * 0.05 * (pins / 2))
    actor["current_hp"] = min(max_hp, actor["current_hp"] + heal)
    s = '' if is_player else 's'
    c_print(f"  ✨ {name} heal{s} {heal} HP from the broken pins. ({actor['current_hp']}/{max_hp})")

    # Apply permanent 50% stat debuff
    actor["tarnished_jade_weakened"] = True
    c_print(f"  ⚠ The Jade's curse settles deep — all {name}'s stats are halved for this battle!")

    # Remove all pins
    actor["tarnished_jade_pins"] = 0


def check_tarnished_jade_trigger(actor, incoming_damage, enemies, attacker=None, source="", is_player=True):
    """
    Check if incoming damage would trigger Divine Lament or Wedge Backlash.
    Returns (should_apply_damage, None).
    If triggered, handles the effect internally and returns (False, None).
    """
    if not _actor_has_tarnished_jade(actor):
        return True, None

    max_hp = _get_actor_max_hp(actor)
    threshold = int(max_hp * 0.20)
    current_hp = actor["current_hp"]
    pins = actor.get("tarnished_jade_pins", 0)

    # Check if damage would bring HP to <= 20% (Divine Lament) or < 20% (Wedge Backlash)
    projected_hp = current_hp - incoming_damage

    # Divine Lament: HP <= 20% AND pins >= 6
    if projected_hp <= threshold and pins >= 6:
        trigger_divine_lament(actor, enemies, source, is_player)
        return False, None

    # Wedge Backlash: HP < 20% AND pins < 6
    if projected_hp < threshold and pins < 6:
        trigger_wedge_backlash(actor, enemies, attacker, source, is_player)
        return False, None

    return True, None


def apply_tarnished_jade_turn_start(actor, enemies, is_player=True):
    """
    Apply turn-start pin damage and check for triggers.
    Returns True if Divine Lament or Wedge Backlash triggered.
    """
    if not _actor_has_tarnished_jade(actor):
        return False

    pins = actor.get("tarnished_jade_pins", 0)
    if pins <= 0:
        return False

    max_hp = _get_actor_max_hp(actor)
    threshold = int(max_hp * 0.20)
    pin_damage = int(max_hp * 0.05 * pins)
    projected_hp = actor["current_hp"] - pin_damage
    name = "Your" if is_player else f"{actor.get('name', 'The wielder')}'s"

    # Check Divine Lament trigger (projected HP <= 20% AND pins >= 6)
    if projected_hp <= threshold and pins >= 6:
        c_print(f"\n  ⚡ {name} Tarnished Jade's {pins} pins pulse with divine agony...")
        c_print(f"  {name} body buckles under the weight of heaven — but the pins SHATTER!")
        trigger_divine_lament(actor, enemies, "turn_start", is_player)
        return True

    # Check Wedge Backlash trigger (projected HP < 20% AND pins < 6)
    if projected_hp < threshold and pins < 6:
        c_print(f"\n  ⚡ {name} Tarnished Jade's {pins} pins pulse weakly...")
        c_print(f"  {name} body buckles — the pins shatter too soon!")
        trigger_wedge_backlash(actor, enemies, None, "turn_start", is_player)
        return True

    # Normal pin damage
    actor["current_hp"] -= pin_damage
    c_print(f"\n  ⚡ {name} Tarnished Jade's {pins} pins dig deeper — {pin_damage} damage!")
    c_print(f"  (+{pins // 2} STR, +{pins // 2} WIS from the embedded pins)")

    return False
    return False
