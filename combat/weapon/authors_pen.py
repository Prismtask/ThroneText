# combat/authors_pen.py
"""Author's Pen accessory mechanics — passive + active (Rewrite) from Mary Sue drop.

Passive: +4 to all stats while in Wonderland.
Active: Rewrite (5 CD) — heal the party for all damage taken in the previous combat round.
        Does not revive fallen allies.
"""

from combat.combat_io import c_print, c_input


# ─── Equipped Check ───────────────────────────────────────────────────────

def _actor_has_authors_pen(actor):
    """Return the Author's Pen item dict if equipped in any accessory slot, else None."""
    equipment = actor.get("equipped", {})
    if isinstance(equipment, dict):
        for slot in ("accessory1", "accessory2", "accessory"):
            acc = equipment.get(slot)
            if acc and acc.get("special") == "authors_pen":
                return acc
    return None


def _is_in_wonderland(actor):
    """Return True if the actor is currently in the Wonderland dungeon.

    Allies mirror the player's dungeon_region at combat start, so this
    works for both players and allies.
    """
    return actor.get("dungeon_region") == "wonderland"


def _owner_name(actor):
    """Return a display name for the pen's wielder."""
    if actor.get("is_ally"):
        return actor.get("name", "The wielder")
    return "You"


# ─── Passive: +4 all stats in Wonderland ─────────────────────────────────

def get_authors_pen_stat_bonus(actor, attr_name):
    """Return the passive stat bonus from Author's Pen for a given attribute.

    +4 to ALL stats while in Wonderland. Returns 0 otherwise.
    """
    if not _is_in_wonderland(actor):
        return 0
    if not _actor_has_authors_pen(actor):
        return 0
    return 4


# ─── Availability / UI Helpers ──────────────────────────────────────────

def is_authors_pen_available(actor):
    """Return True if Author's Pen is equipped on actor and Rewrite is off cooldown."""
    if not _actor_has_authors_pen(actor):
        return False
    return actor.get("authors_pen_cooldown", 0) <= 0


def get_authors_pen_cooldown_display(actor):
    """Return cooldown display string for the combat UI, or empty string."""
    if not _actor_has_authors_pen(actor):
        return ""
    cd = actor.get("authors_pen_cooldown", 0)
    if cd > 0:
        return f"(Rewrite recharging: {cd} turn(s))"
    return ""


# ─── Round Lifecycle: Damage Tracking ────────────────────────────────────

def snapshot_party_hp(player):
    """Record the current HP of all alive party members at the start of a round.

    Stored as player["_authors_pen_hp_snapshot"] = {ref_id: hp, ...}
    where ref_id is 0 for the player or the ally's name for allies.
    """
    snapshot = {}
    # Player
    snapshot[0] = player.get("current_hp", 0)
    # Active (front-row) allies
    from combat.ally import get_active_allies
    for ally in get_active_allies(player):
        # Use the ally dict's id() as a tracking key
        snapshot[id(ally)] = {
            "name": ally.get("name", "Ally"),
            "hp": ally.get("current_hp", 0),
        }
    player["_authors_pen_hp_snapshot"] = snapshot


def compute_last_round_damage(player):
    """At end of round, compare current HP to the snapshot and store the
    per-member damage taken as player["_authors_pen_last_round_damage"].

    Format: {0: player_dmg, id(ally): {"name": ..., "damage": ...}, ...}
    Damage is counted even for members who died (healing won't revive them).
    """
    snapshot = player.pop("_authors_pen_hp_snapshot", None)
    if snapshot is None:
        player["_authors_pen_last_round_damage"] = {}
        return {}

    damage_map = {}
    # Build a lookup of current HP for all entities
    current_hp_map = {0: player.get("current_hp", 0)}
    from combat.ally import get_active_allies
    for ally in get_active_allies(player):
        current_hp_map[id(ally)] = ally.get("current_hp", 0)

    # Iterate over snapshot entries to capture damage for ALL members
    # (including those who died during the round and are no longer active)
    for key, prev_data in snapshot.items():
        if key == 0:
            prev_hp = prev_data  # player snapshot is just an int
            cur_hp = current_hp_map.get(0, 0)
            dmg = max(0, prev_hp - cur_hp)
            if dmg > 0:
                damage_map[0] = dmg
        else:
            prev_hp = prev_data["hp"]
            cur_hp = current_hp_map.get(key, 0)
            dmg = max(0, prev_hp - cur_hp)
            if dmg > 0:
                damage_map[key] = {
                    "name": prev_data.get("name", "Ally"),
                    "damage": dmg,
                }

    player["_authors_pen_last_round_damage"] = damage_map
    return damage_map


# ─── Cooldown Management ─────────────────────────────────────────────────

def tick_authors_pen_cooldown(actor, prefix="  "):
    """Decrement Author's Pen Rewrite cooldown at end of round.

    Returns True if cooldown just reached 0.
    """
    if actor.get("authors_pen_cooldown", 0) > 0:
        actor["authors_pen_cooldown"] -= 1
        if actor["authors_pen_cooldown"] == 0:
            owner = _owner_name(actor)
            c_print(f"{prefix}~*~ {owner}'s Author's Pen glows softly -- Rewrite is ready." if actor.get("is_ally") else f"{prefix}~*~ The Author's Pen glows softly -- Rewrite is ready.")
            return True
    return False


def clear_authors_pen_state(actor):
    """Clear all Author's Pen combat state for any actor."""
    actor.pop("authors_pen_cooldown", None)
    actor.pop("_authors_pen_hp_snapshot", None)
    actor.pop("_authors_pen_last_round_damage", None)


# ─── Active: Rewrite ─────────────────────────────────────────────────────

def use_rewrite(player):
    """Handle the 'Rewrite' action for the player. (backward-compat wrapper)"""
    return _use_rewrite_actor(player, player=player, is_player=True)


def _use_rewrite_actor(actor, player=None, is_player=True):
    """Handle the 'Rewrite' action for any actor (player or ally).

    Heals each party member for the damage they personally took in the
    PREVIOUS combat round. Does not revive fallen allies. 5-turn cooldown.

    Party damage tracking is stored on the player dict by
    snapshot_party_hp()/compute_last_round_damage(), so ally wielders
    read the same map. The cooldown is tracked per-wielder on the actor.

    Returns (result, defending) tuple.
    """
    pen = _actor_has_authors_pen(actor)
    if not pen:
        if is_player:
            c_print("You don't have the Author's Pen equipped.")
        else:
            c_print(f"{actor['name']} doesn't have the Author's Pen equipped.")
        return "retry", False

    cd = actor.get("authors_pen_cooldown", 0)
    if cd > 0:
        c_print(f"Rewrite is still recharging. ({cd} turn(s) remaining)")
        return "retry", False

    # Damage map lives on the player dict (party-wide tracking)
    tracker = player if player is not None else actor
    damage_map = tracker.get("_authors_pen_last_round_damage", {})
    if not damage_map:
        if is_player:
            c_print("\n  ~*~ You raise the Author's Pen, but there is nothing to rewrite --")
            c_print("  ~*~ no damage was taken in the last round.")
        else:
            c_print(f"\n  ~*~ {actor['name']} raises the Author's Pen, but there is nothing to rewrite --")
            c_print("  ~*~ no damage was taken in the last round.")
        return "retry", False

    total_healed = 0
    owner = _owner_name(actor)

    c_print("\n  " + "~*~ " * 18)
    c_print(f"  {owner} raise{'s' if not is_player else ''} the Author's Pen. Ink flows backward through the air.")
    c_print('  "That didn\'t happen. Let me try again."')
    c_print("  " + "~*~ " * 18)

    # Heal the actual player
    player_dmg = damage_map.get(0, 0)
    if player_dmg > 0 and tracker.get("current_hp", 0) > 0:
        p_max = tracker.get("max_hp", tracker.get("current_hp", 1))
        p_cur = tracker.get("current_hp", 0)
        heal = min(player_dmg, p_max - p_cur)
        if heal > 0:
            tracker["current_hp"] = p_cur + heal
            total_healed += heal
            c_print(f"  ~*~ You: +{heal} HP -> {tracker['current_hp']}/{p_max} HP")

    # Heal active allies
    from combat.ally import get_active_allies
    for ally in get_active_allies(tracker):
        ally_key = id(ally)
        ally_data = damage_map.get(ally_key)
        if ally_data is None:
            continue
        ally_dmg = ally_data["damage"] if isinstance(ally_data, dict) else ally_data
        if ally_dmg > 0 and ally.get("current_hp", 0) > 0:
            a_max = ally.get("max_hp", ally.get("current_hp", 1))
            a_cur = ally.get("current_hp", 0)
            heal = min(ally_dmg, a_max - a_cur)
            if heal > 0:
                ally["current_hp"] = a_cur + heal
                total_healed += heal
                c_print(f"  ~*~ {ally.get('name', 'Ally')}: +{heal} HP -> {ally['current_hp']}/{a_max} HP")

    c_print(f"\n  ~*~ The pen rewrites the last round -- {total_healed} HP restored!")

    # Set cooldown on the wielder
    actor["authors_pen_cooldown"] = 5
    c_print("  ~*~ Rewrite will be ready again in 5 turns.")

    return "continue", False
