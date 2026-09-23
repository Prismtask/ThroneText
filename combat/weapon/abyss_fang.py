from combat.combat_io import c_print, c_input
"""Abyss Fang weapon mechanics and combat state management."""


# ─── Equipped Check ───────────────────────────────────────────────────────

def _actor_has_abyss_fang(actor):
    """Return the Abyss Fang weapon dict if equipped on any actor, else None."""
    equipment = actor.get("equipped", {})
    if isinstance(equipment, dict):
        weapon = equipment.get("weapon")
        if weapon and weapon.get("special") == "dream_devour":
            return weapon
    return None

def _player_has_abyss_fang(player):
    """Return the Abyss Fang weapon dict if equipped, else None."""
    return _actor_has_abyss_fang(player)


# ─── Availability / UI Helpers ──────────────────────────────────────────

def is_abyss_fang_available(actor):
    """Return True if Abyss Fang is equipped on actor and off cooldown."""
    if not _actor_has_abyss_fang(actor):
        return False
    return actor.get("abyss_fang_cooldown", 0) <= 0


def get_abyss_fang_cooldown_display(actor):
    """Return cooldown display string for the combat UI, or empty string."""
    if not _actor_has_abyss_fang(actor):
        return ""
    cd = actor.get("abyss_fang_cooldown", 0)
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
        c_print(f"⚔️  The Abyss awakens! Triple actions for {pending} turns!")
        return True
    return False


def tick_abyss_fang_cooldown(player, prefix="  "):
    """Decrement Abyss Fang cooldown at end of round.

    Returns True if cooldown just reached 0.
    """
    if player.get("abyss_fang_cooldown", 0) > 0:
        player["abyss_fang_cooldown"] -= 1
        if player["abyss_fang_cooldown"] == 0:
            c_print(f"{prefix}⚔️  The Abyss Fang hums — its hunger is renewed.")
            return True
    return False


def tick_abyssal_tempo(player, prefix="  "):
    """Decrement abyss triple actions and print fade message if it reaches 0.

    Returns True if tempo just faded.
    """
    if player.get("abyss_triple_actions", 0) > 0:
        player["abyss_triple_actions"] -= 1
        if player["abyss_triple_actions"] == 0:
            c_print(f"{prefix}⚔️  Nightmare Tempo fades. The triple-action fury ends.")
            return True
    return False


def clear_abyss_fang_state(player):
    """Clear all Abyss Fang combat state (triple actions, tempo pending)."""
    player["abyss_triple_actions"] = 0
    player.pop("abyss_tempo_pending", None)


# ─── Player Action ────────────────────────────────────────────────────────

def wield_abyss_fang(player):
    """Handle the 'Wield the Abyss' action for the player.

    Returns (result, defending) tuple.
    """
    return _wield_abyss_fang_actor(player, is_player=True)


def _wield_abyss_fang_actor(actor, is_player=False):
    """Handle the 'Wield the Abyss' action for any actor (player or ally).

    Returns (result, defending) tuple.
    """
    abyss_fang = _actor_has_abyss_fang(actor)
    if not abyss_fang:
        if is_player:
            c_print("You have no weapon that responds to that command.")
        else:
            c_print(f"{actor['name']} has no weapon that responds to that command.")
        return "retry", False

    abyss_cd = actor.get("abyss_fang_cooldown", 0)
    if abyss_cd > 0:
        c_print(f"The Abyss Fang is still recharging. ({abyss_cd} turn(s) remaining)")
        return "retry", False

    name = "You" if is_player else actor['name']
    pronoun = "your" if is_player else "their"
    lose_verb = "you lose" if is_player else f"{actor['name']} loses"

    c_print("\n" + "≈" * 55)
    c_print(f"The Abyss Fang SCREAMS. A void tears open across {pronoun}")
    c_print(f"vision — stolen faces from the Slitcurrent's body flash")
    c_print(f"across the blade, mouthing silent warnings. {name} grip it")
    c_print(f"anyway. Reality peels back. {name} {'are' if is_player else 'is'} the wound now.")
    c_print("≈" * 55)
    c_input("Press Enter to unleash it...")

    max_hp = actor.get("max_hp", actor.get("current_hp", 1))
    hp_cost = int(max_hp * 0.40)
    actor["current_hp"] = max(1, actor["current_hp"] - hp_cost)
    c_print(f"\nThe blade drinks deep — {lose_verb} {hp_cost} HP ({actor['current_hp']}/{max_hp} remaining).")

    str_bonus = 8
    actor.setdefault("active_buffs", []).append({
        "stat": "Strength",
        "value": str_bonus,
        "remaining": 4,
        "source": "abyss_fang",
    })
    c_print(f"⚔️  Abyss-Tempered: Strength +{str_bonus} for 4 turns!")

    actor["abyss_tempo_pending"] = 4
    c_print("⚔️  The Abyss stirs... its full fury will awaken next round!")

    actor["abyss_fang_cooldown"] = 6
    c_print("(The blade will recharge in 6 turns.)\n")
    return "continue", False
