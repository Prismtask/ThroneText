"""Captain's Cutlass weapon mechanics and combat state management."""
import random
from combat.ally import get_alive_allies


# ─── Equipped Check ───────────────────────────────────────────────────────

def _player_has_captain_cutlass(player):
    """Return the Cutlass weapon dict if equipped, else None."""
    equipment = player.get("equipped", {})
    if isinstance(equipment, dict):
        weapon = equipment.get("weapon")
        if weapon and weapon.get("special") == "captain_cutlass":
            return weapon
    return None


# ─── Availability / UI Helpers ──────────────────────────────────────────

def is_captain_cutlass_available(player):
    """Return True if Cutlass is equipped and Crew Rally is off cooldown."""
    if not _player_has_captain_cutlass(player):
        return False
    return player.get("cutlass_rally_cooldown", 0) <= 0


def get_captain_cutlass_cooldown_display(player):
    """Return cooldown display string for the combat UI, or empty string."""
    if not _player_has_captain_cutlass(player):
        return ""
    cd = player.get("cutlass_rally_cooldown", 0)
    if cd > 0:
        return f"(Crew Rally recharging: {cd} turn(s))"
    return ""


# ─── Combat State Lifecycle ─────────────────────────────────────────────

def clear_captain_cutlass_state(player):
    """Clear all Captain's Cutlass combat state (rally, riposte count)."""
    player["cutlass_riposte_count"] = 0
    player["cutlass_rally_active"] = False
    player["cutlass_rally_turns"] = 0
    player.pop("cutlass_rally_dr", None)
    player.pop("cutlass_rally_attack_mult", None)
    player.pop("cutlass_rally_ignore_high_tide", None)
    # Remove rally buffs from player and allies
    for buff in player.get("active_buffs", [])[:]:
        if buff.get("source") == "captain_rally":
            player["active_buffs"].remove(buff)
    for ally in get_alive_allies(player):
        for buff in ally.get("active_buffs", [])[:]:
            if buff.get("source") == "captain_rally":
                ally["active_buffs"].remove(buff)


def tick_captain_cutlass(player, prefix="  "):
    """Tick Captain's Cutlass cooldown and rally duration at end of round.

    Returns True if rally just ended.
    """
    # Reset per-turn riposte counter
    player["cutlass_riposte_count"] = 0

    # Cooldown tick
    if player.get("cutlass_rally_cooldown", 0) > 0:
        player["cutlass_rally_cooldown"] -= 1
        if player["cutlass_rally_cooldown"] == 0:
            print(f"{prefix}⚓ The Captain's Cutlass hums — Crew Rally is ready!")

    # Rally duration tick
    if player.get("cutlass_rally_active"):
        player["cutlass_rally_turns"] -= 1
        if player["cutlass_rally_turns"] == 0:
            print(f"{prefix}⚓ The rally ends. The spectral wind fades.")
            player["cutlass_rally_active"] = False
            player["cutlass_rally_ignore_high_tide"] = False
            player.pop("cutlass_rally_dr", None)
            player.pop("cutlass_rally_attack_mult", None)
            # Remove rally buffs
            for buff in player.get("active_buffs", [])[:]:
                if buff.get("source") == "captain_rally":
                    player["active_buffs"].remove(buff)
            for ally in get_alive_allies(player):
                for buff in ally.get("active_buffs", [])[:]:
                    if buff.get("source") == "captain_rally":
                        ally["active_buffs"].remove(buff)
            return True
        elif player["cutlass_rally_turns"] == 1:
            # Second turn: ramp to 30%
            player["cutlass_rally_attack_mult"] = 0.30
            print(f"{prefix}⚓ The rally intensifies! Attack power +30%!")
    return False


# ─── Player Action: Crew Rally ───────────────────────────────────────────

def use_crew_rally(player):
    """Handle the 'Crew Rally' action.

    Returns (result, defending) tuple.
    """
    cutlass = _player_has_captain_cutlass(player)
    if not cutlass:
        print("You have no weapon that responds to that command.")
        return "retry", False

    rally_cd = player.get("cutlass_rally_cooldown", 0)
    if rally_cd > 0:
        print(f"Crew Rally is still recharging. ({rally_cd} turn(s) remaining)")
        return "retry", False

    print("\n" + "⚓" * 55)
    print("You raise the Captain's Cutlass high!")
    print("'Stand fast, crew! For the Everlong!'")
    print("A spectral wind fills the battlefield — the crew rallies!")
    print("⚓" * 55)
    input("Press Enter to rally the crew...")

    player["cutlass_rally_active"] = True
    player["cutlass_rally_turns"] = 2
    player["cutlass_rally_cooldown"] = 5
    player["cutlass_rally_ignore_high_tide"] = True

    # Initiative boost: DEX +3 to all party members
    party = [player] + get_alive_allies(player)
    for member in party:
        member.setdefault("active_buffs", []).append({
            "stat": "Dexterity",
            "value": 3,
            "remaining": 2,
            "source": "captain_rally",
        })

    # Damage reduction percentage based on party size
    dr = min(0.20, len(party) * 0.05)
    player["cutlass_rally_dr"] = dr
    print(f"\n  ⚓ Damage reduced by {int(dr*100)}% for 2 turns!")

    # Attack bonus starts at 20%
    player["cutlass_rally_attack_mult"] = 0.20
    print("  ⚓ Attack power increased by 20% for the first turn!")

    # Suppress High Tide vulnerability during rally
    stacks = player.get("cutlass_high_tide_stacks", 0)
    if stacks > 0:
        print("  ⚓ The High Tide's curse is held at bay during the rally!")

    return "continue", False


# ─── Riposte: Captain's Authority ───────────────────────────────────────

def trigger_captain_riposte(player, enemy):
    """Trigger riposte when the player is attacked while equipped with the Cutlass.

    Max 2 ripostes per turn.
    """
    if not _player_has_captain_cutlass(player):
        return

    current = player.get("cutlass_riposte_count", 0)
    if current >= 2:
        return

    player["cutlass_riposte_count"] = current + 1

    from combat.stats import compute_player_stats
    p_str, p_con, p_dex, p_ler, p_wis, p_cha = compute_player_stats(player)
    riposte_dmg = max(1, p_str // 2 + 3 + random.randint(1, 4))
    enemy["hp"] -= riposte_dmg
    print(f"  ⚔ [CAPTAIN'S AUTHORITY] Your cutlass ripostes! The {enemy['name']} takes {riposte_dmg} damage!")
    if enemy["hp"] <= 0:
        print(f"  The {enemy['name']} is struck down by your riposte!")
        # Trigger high tide stack for riposte kills too
        check_high_tide_kill(player, enemy)


# ─── High Tide Battle ────────────────────────────────────────────────────

def check_high_tide_kill(player, target):
    """Check if an enemy death should add a High Tide stack.

    Stacks are floor-persistent (reset when leaving dungeon or entering next floor).
    """
    if not _player_has_captain_cutlass(player):
        return

    floor = player.get("floor")
    if floor is not None and player.get("cutlass_high_tide_floor") != floor:
        player["cutlass_high_tide_floor"] = floor
        player["cutlass_high_tide_stacks"] = 0

    current = player.get("cutlass_high_tide_stacks", 0)
    if current < 5:
        player["cutlass_high_tide_stacks"] = current + 1
        print(f"  [HIGH TIDE] The Cutlass thirsts! Stack {current + 1}/5! (+5% attack, +10% incoming damage)")
    else:
        print(f"  [HIGH TIDE] The Cutlass is at maximum tide! (5/5)")


def get_high_tide_attack_bonus(player, base_dmg):
    """Return bonus damage from High Tide stacks."""
    if not _player_has_captain_cutlass(player):
        return 0
    stacks = player.get("cutlass_high_tide_stacks", 0)
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
        print(f"  [HIGH TIDE] The curse of the sea deepens — +{extra} damage from the tide!")
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
        print(f"  [RALLY] The spectral crew shields you! (-{incoming_dmg - reduced} damage)")
    return reduced


def get_rally_attack_bonus(player, base_dmg):
    """Return bonus damage from Crew Rally attack multiplier."""
    if not player.get("cutlass_rally_active"):
        return 0
    mult = player.get("cutlass_rally_attack_mult", 0)
    if mult <= 0:
        return 0
    return int(base_dmg * mult)
