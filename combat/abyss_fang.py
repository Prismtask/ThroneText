"""Abyss Fang weapon mechanics and combat state management."""


# ─── Equipped Check ───────────────────────────────────────────────────────

def _player_has_abyss_fang(player):
    """Return the Abyss Fang weapon dict if equipped, else None."""
    equipment = player.get("equipped", {})
    if isinstance(equipment, dict):
        weapon = equipment.get("weapon")
        if weapon and weapon.get("special") == "dream_devour":
            return weapon
    return None


# ─── Availability / UI Helpers ──────────────────────────────────────────

def is_abyss_fang_available(player):
    """Return True if Abyss Fang is equipped and off cooldown."""
    if not _player_has_abyss_fang(player):
        return False
    return player.get("abyss_fang_cooldown", 0) <= 0


def get_abyss_fang_cooldown_display(player):
    """Return cooldown display string for the combat UI, or empty string."""
    if not _player_has_abyss_fang(player):
        return ""
    cd = player.get("abyss_fang_cooldown", 0)
    if cd > 0:
        return f"(Abyss Fang recharging: {cd} turn(s))"
    return ""


def is_abyssal_tempo_active(player):
    """Return True if triple actions are currently active."""
    return player.get("abyss_triple_actions", 0) > 0


def get_abyssal_tempo_count(player):
    """Return the number of remaining triple-action turns."""
    return player.get("abyss_triple_actions", 0)


# ─── Round Lifecycle ────────────────────────────────────────────────────

def apply_abyss_tempo_round_start(player):
    """Convert pending tempo to active triple actions at round start.

    Returns True if tempo was activated.
    """
    pending = player.get("abyss_tempo_pending", 0)
    if pending > 0:
        player.pop("abyss_tempo_pending")
        player["abyss_triple_actions"] = pending
        print(f"⚔️  The Abyss awakens! Triple actions for {pending} turns!")
        return True
    return False


def tick_abyss_fang_cooldown(player, prefix="  "):
    """Decrement Abyss Fang cooldown at end of round.

    Returns True if cooldown just reached 0.
    """
    if player.get("abyss_fang_cooldown", 0) > 0:
        player["abyss_fang_cooldown"] -= 1
        if player["abyss_fang_cooldown"] == 0:
            print(f"{prefix}⚔️  The Abyss Fang hums — its hunger is renewed.")
            return True
    return False


def tick_abyssal_tempo(player, prefix="  "):
    """Decrement abyss triple actions and print fade message if it reaches 0.

    Returns True if tempo just faded.
    """
    if player.get("abyss_triple_actions", 0) > 0:
        player["abyss_triple_actions"] -= 1
        if player["abyss_triple_actions"] == 0:
            print(f"{prefix}⚔️  Nightmare Tempo fades. The triple-action fury ends.")
            return True
    return False


def clear_abyss_fang_state(player):
    """Clear all Abyss Fang combat state (triple actions, tempo pending)."""
    player["abyss_triple_actions"] = 0
    player.pop("abyss_tempo_pending", None)


# ─── Player Action ────────────────────────────────────────────────────────

def wield_abyss_fang(player):
    """Handle the 'Wield the Abyss' action.

    Returns (result, defending) tuple.
    """
    abyss_fang = _player_has_abyss_fang(player)
    if not abyss_fang:
        print("You have no weapon that responds to that command.")
        return "retry", False

    abyss_cd = player.get("abyss_fang_cooldown", 0)
    if abyss_cd > 0:
        print(f"The Abyss Fang is still recharging. ({abyss_cd} turn(s) remaining)")
        return "retry", False

    print("\n" + "≈" * 55)
    print("The Abyss Fang SCREAMS. A void tears open across your")
    print("vision — stolen faces from the Slitcurrent's body flash")
    print("across the blade, mouthing silent warnings. You grip it")
    print("anyway. Reality peels back. You are the wound now.")
    print("≈" * 55)
    input("Press Enter to unleash it...")

    from character import player_max_hp
    max_hp = player_max_hp(player)
    hp_cost = int(max_hp * 0.40)
    player["current_hp"] = max(1, player["current_hp"] - hp_cost)
    print(f"\nThe blade drinks deep — you lose {hp_cost} HP ({player['current_hp']}/{max_hp} remaining).")

    str_bonus = 8
    player.setdefault("active_buffs", []).append({
        "stat": "Strength",
        "value": str_bonus,
        "remaining": 4,
        "source": "abyss_fang",
    })
    print(f"⚔️  Abyss-Tempered: Strength +{str_bonus} for 4 turns!")

    player["abyss_tempo_pending"] = 4
    print("⚔️  The Abyss stirs... its full fury will awaken next round!")

    player["abyss_fang_cooldown"] = 6
    print("(The blade will recharge in 6 turns.)\n")
    return "continue", False
