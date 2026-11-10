"""Wonderland guest pacing and late arcs.

Strict order: Red Hood -> Dorothy -> Alice.

The Hatter's tea party is empty until the Queen of Hearts falls. Entering the
inn after that reveals the three-guest scene and invites Red Hood. Dorothy
arrives after the Wolf, Alice after the Witch. A heroine accepted before her
boss arms that boss's variant; a heroine skipped before her boss becomes a
late arc instead.

Guest states
────────────
    away       not in Wonderland yet
    invited    waiting at the tea party
    accepted   traveling with the player (temp ally; boss variant armed)
    late       her boss died without her; a short closure arc is available
    resolved   permanent ally; arc complete

The module is deliberately I/O-free. The inn prints the scene text; quests and
combat only read the guest state.
"""

GUEST_ORDER = ("red_hood", "dorothy", "alice")

GUEST_NAMES = {
    "red_hood": "Red Hood",
    "dorothy":  "Dorothy",
    "alice":    "Alice",
}

# Heroine state keys (mirror combat/ally.py).
_HEROINE_STATE_KEYS = {
    "red_hood": "wl_redhood_state",
    "dorothy":  "wl_dorothy_state",
    "alice":    "wl_alice_state",
}
_HEROINE_PERM_FLAGS = {
    "red_hood": "wonderland_heroine_redhood_permanent",
    "dorothy":  "wonderland_heroine_dorothy_permanent",
    "alice":    "wonderland_heroine_alice_permanent",
}
# Boss flag that ends each heroine's chapter.
_HEROINE_BOSS_FLAGS = {
    "red_hood": "wl_boss_defeated_big_bad_wolf",
    "dorothy":  "wl_boss_defeated_wicked_witch",
    "alice":    "wl_boss_defeated_jabberwock",
}
_BOSS_TO_HEROINE = {flag: key for key, flag in _HEROINE_BOSS_FLAGS.items()}

# Floor that gates each heroine's arrival (the *preceding* boss).
ARRIVAL_BOSS_FLAGS = {
    "red_hood": "wl_boss_defeated_queen_of_hearts",
    "dorothy":  "wl_boss_defeated_big_bad_wolf",
    "alice":    "wl_boss_defeated_wicked_witch",
}
HEROINE_BOSS_FLOORS = {"red_hood": 20, "dorothy": 30, "alice": 40}

# House records use the enemy template key; `create_ally_from_girl` restores
# `_heroine_key` and permanent status from these.
_HEROINE_HOUSE_KEYS = {
    "red_hood": "wonderland_red_hood",
    "dorothy":  "wonderland_dorothy",
    "alice":    "wonderland_alice",
}

VALID_STATES = ("away", "invited", "accepted", "late", "resolved")


# ── State helpers ────────────────────────────────────────────────────────────

def _heroine_ally(player, heroine_key):
    for ally in player.get("allies", []):
        if ally.get("_heroine_key") == heroine_key:
            return ally
    return None


def _heroine_permanent(player, heroine_key):
    if player.get(_HEROINE_PERM_FLAGS.get(heroine_key, "")):
        return True
    if player.get(_HEROINE_STATE_KEYS.get(heroine_key, "")) == "permanent":
        return True
    ally = _heroine_ally(player, heroine_key)
    if ally and not ally.get("_wonderland_temp", True):
        return True
    # A heroine living in the house is still permanent — do not spawn a
    # duplicate late-arc copy for her.
    house_key = _HEROINE_HOUSE_KEYS.get(heroine_key)
    if house_key:
        for house in (player.get("houses") or {}).values():
            for girl in house.get("monster_girls", []):
                if girl.get("key") == house_key:
                    return True
    return False


def _wonderland_max_floor(player):
    prog = (player.get("city_floors") or {}).get("wonderland") or {}
    try:
        return int(prog.get("max_floor", 1))
    except (TypeError, ValueError):
        return 1


def _has_past_tea_party(player):
    """True when a save already progressed beyond the first Hatter scene."""
    if _wonderland_max_floor(player) >= 20:
        return True
    for key in GUEST_ORDER:
        flag = _HEROINE_BOSS_FLAGS[key]
        if player.get(flag):
            return True
        if _heroine_permanent(player, key):
            return True
        state = player.get(_HEROINE_STATE_KEYS.get(key, ""), "unmet")
        if state not in ("", "unmet", None):
            return True
    return False


def _infer_guest_state(player, heroine_key):
    """Migration default for saves without a guest-state entry."""
    if _heroine_permanent(player, heroine_key):
        return "resolved"
    if player.get(_HEROINE_BOSS_FLAGS.get(heroine_key, "")):
        return "late"
    if _heroine_ally(player, heroine_key) is not None:
        return "accepted"
    if player.get(_HEROINE_STATE_KEYS.get(heroine_key, "")) == "temp":
        return "accepted"
    if any(a.get("_heroine_key") == heroine_key
           for a in player.get("wonderland_saved_temp_heroines", [])):
        return "accepted"
    if player.get(_HEROINE_STATE_KEYS.get(heroine_key, "")) in ("intro", "declined"):
        return "invited"
    return "away"


def ensure_guest_state(player):
    """Seed/migrate the ``wonderland_guests`` block. Idempotent."""
    guests = player.setdefault("wonderland_guests", {})
    for key in GUEST_ORDER:
        if key not in guests or guests[key] not in VALID_STATES:
            guests[key] = _infer_guest_state(player, key)
        # Permanent heroines always win over a stale late/accepted state.
        if guests[key] != "resolved" and _heroine_permanent(player, key):
            guests[key] = "resolved"
    player.setdefault("wl_hatter_three_guests_seen", False)
    if not player["wl_hatter_three_guests_seen"] and _has_past_tea_party(player):
        player["wl_hatter_three_guests_seen"] = True
    return guests


def get_guest_state(player, heroine_key):
    return ensure_guest_state(player).get(heroine_key, "away")


def set_guest_state(player, heroine_key, state):
    if state not in VALID_STATES:
        raise ValueError(f"unknown Wonderland guest state: {state}")
    ensure_guest_state(player)[heroine_key] = state


def is_variant_active(player, heroine_key):
    """True when the heroine was accepted and is alive in the party."""
    if get_guest_state(player, heroine_key) != "accepted":
        return False
    ally = _heroine_ally(player, heroine_key)
    return bool(ally and ally.get("current_hp", 0) > 0)


# ── Inn flow ─────────────────────────────────────────────────────────────────

def _invite(player, heroine_key):
    # Leave the existing heroine state alone: the guest is present, but the
    # full first-meeting dialogue still belongs to the next conversation.
    set_guest_state(player, heroine_key, "invited")


def on_inn_enter(player):
    """Advance guest arrivals after Floor 10/20/30.

    Returns scene ids for the inn to print:
      ``three_guests``, ``red_hood_arrives``, ``dorothy_arrives``,
      ``alice_arrives``.
    """
    guests = ensure_guest_state(player)
    scenes = []

    # Late transitions first: a boss flag without a permanent heroine means
    # her chapter closed without her.
    for key in GUEST_ORDER:
        if (player.get(_HEROINE_BOSS_FLAGS.get(key, ""))
                and not _heroine_permanent(player, key)
                and guests[key] not in ("late", "resolved")):
            guests[key] = "late"

    unresolved = any(guests[key] != "resolved" for key in GUEST_ORDER)
    if (player.get("wl_boss_defeated_queen_of_hearts") and unresolved
            and not player.get("wl_hatter_three_guests_seen")):
        player["wl_hatter_three_guests_seen"] = True
        scenes.append("three_guests")

    # Strict order: only the next guest is newly invited.
    if player.get(ARRIVAL_BOSS_FLAGS["red_hood"]) and guests["red_hood"] == "away":
        _invite(player, "red_hood")
        if "three_guests" not in scenes:
            scenes.append("red_hood_arrives")

    if (player.get(ARRIVAL_BOSS_FLAGS["dorothy"])
            and guests["red_hood"] in ("resolved", "late")
            and guests["dorothy"] == "away"):
        _invite(player, "dorothy")
        scenes.append("dorothy_arrives")

    if (player.get(ARRIVAL_BOSS_FLAGS["alice"])
            and guests["dorothy"] in ("resolved", "late")
            and guests["alice"] == "away"):
        _invite(player, "alice")
        scenes.append("alice_arrives")

    # Deed titles read guest/boss state; check as soon as a scene lands.
    if scenes:
        from titles import check_unlock
        check_unlock(player)

    return scenes


def menu_keys(player):
    """Heroine keys that should appear at the tea party right now."""
    guests = ensure_guest_state(player)
    keys = []
    for key in GUEST_ORDER:
        state = guests.get(key, "away")
        if state in ("invited", "late") or _heroine_ally(player, key) is not None:
            keys.append(key)
        elif _heroine_permanent(player, key):
            keys.append(key)
    return keys


def on_boss_defeated(player, boss_target):
    """Close or open a guest arc after a Wonderland superboss victory."""
    guests = ensure_guest_state(player)
    if boss_target == "mary_sue":
        for key in GUEST_ORDER:
            if _heroine_permanent(player, key):
                guests[key] = "resolved"
            elif guests[key] != "resolved":
                guests[key] = "late"
        return

    key = _BOSS_TO_HEROINE.get(boss_target)
    if key is None:
        return
    if _heroine_permanent(player, key):
        guests[key] = "resolved"
    elif guests[key] in ("away", "invited", "accepted"):
        guests[key] = "late"


def late_arc_available(player, heroine_key):
    return get_guest_state(player, heroine_key) == "late"


def resolve_late_arc(player, heroine_key):
    """Close a late arc, promoting the heroine to permanent.

    Returns (ok, message). Signature-weapon facilities are untouched, so the
    full upgrade path remains available after a late resolution.
    """
    if get_guest_state(player, heroine_key) != "late":
        return False, "There is no unfinished story to close right now."

    # A permanent/house heroine already has closure; never create a duplicate.
    if _heroine_permanent(player, heroine_key):
        set_guest_state(player, heroine_key, "resolved")
        return True, f"{GUEST_NAMES[heroine_key]}'s story is already settled."

    from combat.ally import (
        create_heroine_ally, ensure_party_order, get_ally_capacity,
        get_heroine_in_party, promote_heroine_to_permanent, set_heroine_state,
    )

    ally = get_heroine_in_party(player, heroine_key)
    if ally is None:
        roster = player.get("allies", [])
        capacity = get_ally_capacity(player)
        if len(roster) >= capacity:
            return False, (f"Your party is full ({len(roster)}/{capacity}) — "
                           "make room, then speak with her again.")
        ally = create_heroine_ally(player, heroine_key,
                                   floor=player.get("saved_dungeon_floor", 1))
        if ally is None:
            return False, "Something is missing from the story. Try again later."
        player.setdefault("allies", []).append(ally)
        ensure_party_order(player)

    promote_heroine_to_permanent(player, ally,
                                 ally.get("level", player.get("level", 1)))
    set_heroine_state(player, heroine_key, "permanent")
    set_guest_state(player, heroine_key, "resolved")
    return True, f"{GUEST_NAMES[heroine_key]} becomes a PERMANENT ally."


def hatter_hint(player):
    """One or two Hatter lines naming the next guest trigger."""
    guests = ensure_guest_state(player)
    if not player.get("wl_boss_defeated_queen_of_hearts"):
        return ["No guests have asked for you yet. The Queen's chapter comes first."]

    red = guests["red_hood"]
    if red == "invited":
        return ["The huntress in red is by the fireplace.",
                f"The Wolf is her chapter. Take her with you to Floor {HEROINE_BOSS_FLOORS['red_hood']}."]
    if red == "accepted":
        return [f"Red Hood travels with you. The Wolf waits on Floor {HEROINE_BOSS_FLOORS['red_hood']}."]
    if red == "late":
        return ["Red Hood came back after the Wolf fell.",
                "She has something to finish. Speak with her."]
    if red != "resolved":
        return ["The huntress in red will return when the next chapter turns."]

    if not player.get("wl_boss_defeated_big_bad_wolf"):
        return ["The next guest will arrive after the Wolf's chapter closes."]

    dorothy = guests["dorothy"]
    if dorothy == "invited":
        return ["The girl with the silver shoes is by the window.",
                f"The Witch is her chapter. Take her with you to Floor {HEROINE_BOSS_FLOORS['dorothy']}."]
    if dorothy == "accepted":
        return [f"Dorothy travels with you. The Witch waits on Floor {HEROINE_BOSS_FLOORS['dorothy']}."]
    if dorothy == "late":
        return ["Dorothy returned after the Witch melted.",
                "She has something to finish. Speak with her."]
    if dorothy != "resolved":
        return ["The next guest will arrive when the next chapter turns."]

    if not player.get("wl_boss_defeated_wicked_witch"):
        return ["The last guest will arrive after the Witch's chapter closes."]

    alice = guests["alice"]
    if alice == "invited":
        return ["The dreamer in blue is counting sugar cubes at the far end.",
                f"The Jabberwock is her chapter. Take her with you to Floor {HEROINE_BOSS_FLOORS['alice']}."]
    if alice == "accepted":
        return [f"Alice travels with you. The Jabberwock waits on Floor {HEROINE_BOSS_FLOORS['alice']}."]
    if alice == "late":
        return ["Alice came back after the Jabberwock fell.",
                "She has something to finish. Speak with her."]
    if alice != "resolved":
        return ["The dreamer in blue will return when the last chapter turns."]

    return ["The tea party is quiet. Three stories have found their endings."]
