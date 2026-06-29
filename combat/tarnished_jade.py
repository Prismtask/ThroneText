import random
from character import player_max_hp


def _player_has_tarnished_jade(player):
    """Return True if player has Tarnished Jade equipped as armor."""
    equipment = player.get("equipped", {})
    if isinstance(equipment, dict):
        armor = equipment.get("armor")
        if armor and armor.get("id") == "tarnished_jade":
            return True
    return False


def add_tarnished_jade_pin(player, amount=1):
    """Add pin stacks to Tarnished Jade, up to max 10."""
    if not _player_has_tarnished_jade(player):
        return
    current = player.get("tarnished_jade_pins", 0)
    player["tarnished_jade_pins"] = min(10, current + amount)


def get_tarnished_jade_str_bonus(player):
    """Return STR bonus from pin stacks: +1 per 2 stacks."""
    if not _player_has_tarnished_jade(player):
        return 0
    return player.get("tarnished_jade_pins", 0) // 2


def get_tarnished_jade_wis_bonus(player):
    """Return WIS bonus from pin stacks: +1 per 2 stacks."""
    if not _player_has_tarnished_jade(player):
        return 0
    return player.get("tarnished_jade_pins", 0) // 2


def is_tarnished_jade_weakened(player):
    """Return True if Wedge Backlash permanent debuff is active."""
    return player.get("tarnished_jade_weakened", False)


def _compute_divine_lament_damage(player, pins):
    """Compute Divine Lament damage based on pin stacks and player stats."""
    from combat.stats import compute_player_stats
    p_str, p_con, p_dex, p_ler, p_wis, p_cha = compute_player_stats(player)
    return pins * (p_str + p_wis) // 2


def _compute_wedge_backlash_damage(player, pins):
    """Compute Wedge Backlash damage (reduced)."""
    return _compute_divine_lament_damage(player, pins) // 2


def trigger_divine_lament(player, enemies, source):
    """Trigger Divine Lament: deal damage to all enemies, heal player, remove pins."""
    pins = player.get("tarnished_jade_pins", 0)
    if pins == 0:
        return

    dmg = _compute_divine_lament_damage(player, pins)

    print("\n" + "✦" * 55)
    print("  ☁ DIVINE LAMENT ☁")
    print("  The Tarnished Jade PINS shatter in unison!")
    print("  Heaven's sorrow erupts through your wounds —")
    print("  all enemies feel the dragon's grief!")
    print("✦" * 55)

    for enemy in enemies:
        if enemy.get("hp", 0) > 0:
            enemy["hp"] -= dmg
            print(f"  {enemy['name']} takes {dmg} pure damage from the shattered pins!")
            if enemy["hp"] <= 0:
                print(f"  {enemy['name']} is struck down by divine sorrow!")

    # Heal player: 5% per pin stack
    max_hp = player_max_hp(player)
    heal = int(max_hp * 0.05 * pins)
    player["current_hp"] = min(max_hp, player["current_hp"] + heal)
    print(f"  ✨ You heal {heal} HP from the shattered pins! ({player['current_hp']}/{max_hp})")

    # Remove all pins
    player["tarnished_jade_pins"] = 0
    print("  ✦ All pin stacks consumed. The Jade grows silent.")


def trigger_wedge_backlash(player, enemies, attacker=None, source=""):
    """Trigger Wedge Backlash: reduced damage to single target, heal, debuff, remove pins."""
    pins = player.get("tarnished_jade_pins", 0)
    if pins == 0:
        return

    dmg = _compute_wedge_backlash_damage(player, pins)

    # Determine target
    target = attacker
    if target is None and enemies:
        alive = [e for e in enemies if e.get("hp", 0) > 0]
        if alive:
            target = max(alive, key=lambda e: e["hp"])

    print("\n" + "!" * 55)
    print("  ☠ WEDGE BACKLASH ☠")
    print("  The Tarnished Jade's pins shatter too early!")
    print("  A feeble divine spark lashes out —")
    print("  but the heavens punish your weakness!")
    print("!" * 55)

    if target and target.get("hp", 0) > 0:
        target["hp"] -= dmg
        print(f"  {target['name']} takes {dmg} reduced pure damage!")
        if target["hp"] <= 0:
            print(f"  {target['name']} is struck down by the backlash!")

    # Heal: 5% per pin stack / 2
    max_hp = player_max_hp(player)
    heal = int(max_hp * 0.05 * (pins / 2))
    player["current_hp"] = min(max_hp, player["current_hp"] + heal)
    print(f"  ✨ You heal {heal} HP from the broken pins. ({player['current_hp']}/{max_hp})")

    # Apply permanent 50% stat debuff
    player["tarnished_jade_weakened"] = True
    print("  ⚠ The Jade's curse settles deep — all your stats are halved for this battle!")

    # Remove all pins
    player["tarnished_jade_pins"] = 0


def check_tarnished_jade_trigger(player, incoming_damage, enemies, attacker=None, source=""):
    """
    Check if incoming damage would trigger Divine Lament or Wedge Backlash.
    Returns (should_apply_damage, None).
    If triggered, handles the effect internally and returns (False, None).
    """
    if not _player_has_tarnished_jade(player):
        return True, None

    max_hp = player_max_hp(player)
    threshold = int(max_hp * 0.20)
    current_hp = player["current_hp"]
    pins = player.get("tarnished_jade_pins", 0)

    # Check if damage would bring HP to <= 20% (Divine Lament) or < 20% (Wedge Backlash)
    projected_hp = current_hp - incoming_damage

    # Divine Lament: HP <= 20% AND pins >= 6
    if projected_hp <= threshold and pins >= 6:
        trigger_divine_lament(player, enemies, source)
        return False, None

    # Wedge Backlash: HP < 20% AND pins < 6
    if projected_hp < threshold and pins < 6:
        trigger_wedge_backlash(player, enemies, attacker, source)
        return False, None

    return True, None


def apply_tarnished_jade_turn_start(player, enemies):
    """
    Apply turn-start pin damage and check for triggers.
    Returns True if Divine Lament or Wedge Backlash triggered.
    """
    if not _player_has_tarnished_jade(player):
        return False

    pins = player.get("tarnished_jade_pins", 0)
    if pins <= 0:
        return False

    max_hp = player_max_hp(player)
    threshold = int(max_hp * 0.20)
    pin_damage = int(max_hp * 0.05 * pins)
    projected_hp = player["current_hp"] - pin_damage

    # Check Divine Lament trigger (projected HP <= 20% AND pins >= 6)
    if projected_hp <= threshold and pins >= 6:
        print(f"\n  ⚡ The Tarnished Jade's {pins} pins pulse with divine agony...")
        print(f"  Your body buckles under the weight of heaven — but the pins SHATTER!")
        trigger_divine_lament(player, enemies, "turn_start")
        return True

    # Check Wedge Backlash trigger (projected HP < 20% AND pins < 6)
    if projected_hp < threshold and pins < 6:
        print(f"\n  ⚡ The Tarnished Jade's {pins} pins pulse weakly...")
        print(f"  Your body buckles — the pins shatter too soon!")
        trigger_wedge_backlash(player, enemies, None, "turn_start")
        return True

    # Normal pin damage
    player["current_hp"] -= pin_damage
    print(f"\n  ⚡ The Tarnished Jade's {pins} pins dig deeper — {pin_damage} damage!")
    print(f"  (+{pins // 2} STR, +{pins // 2} WIS from the embedded pins)")

    return False
