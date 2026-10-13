"""Piece of Relationship — Event Horizon MC-only trophy accessory (docs §10.5).

Tiers are driven by how many owned allies (recruited, active + bench) sit at
200 affection; the count is re-checked at every battle start, so the item
grows as more allies marry. It is NOT an enhance chain.

    2–3 bonded allies  MC: +10% dmg                       allies: +5% dmg
    4–6 bonded allies  MC: +10% dmg, +2% dodge, +2% crit  allies: +10% dmg
    7+  bonded allies  MC: +20% dmg, +5% dodge, +5% crit  allies: +15% dmg,
                                                          +5% dodge, +5% crit
    tier +7 extra      when an ALLY is targeted by an enemy attack (hit or
                       miss), that attacker gains Hunter's Mark (+20%, 2t).

Battle-scoped: buffs are applied on round 1 and stripped by
``clear_battle_buffs`` from ``combat_engine._end_combat_with_result``.
"""

from combat.combat_io import c_print

AFFECTION_REQUIRED = 200
MARK_BONUS = 0.20
MARK_TURNS = 2
SOURCE = "piece_of_relationship"

_ITEM_ID = "piece_of_relationship"
_SPECIAL = "piece_of_relationship"

# (threshold, tier data) — checked high to low.
_TIERS = (
    (7, {"mc_dmg": 0.20, "mc_dodge": 0.05, "mc_crit": 0.05,
         "ally_dmg": 0.15, "ally_dodge": 0.05, "ally_crit": 0.05, "mark": True}),
    (4, {"mc_dmg": 0.10, "mc_dodge": 0.02, "mc_crit": 0.02,
         "ally_dmg": 0.10, "ally_dodge": 0.0, "ally_crit": 0.0, "mark": False}),
    (2, {"mc_dmg": 0.10, "mc_dodge": 0.0, "mc_crit": 0.0,
         "ally_dmg": 0.05, "ally_dodge": 0.0, "ally_crit": 0.0, "mark": False}),
)


def _has_por(actor):
    if not actor:
        return False
    for item in (actor.get("equipped", {}) or {}).values():
        if item and (item.get("special") == _SPECIAL or item.get("id") == _ITEM_ID):
            return True
    return False


def count_bonded_allies(player):
    return sum(
        1 for ally in player.get("allies", [])
        if ally.get("affection", 0) >= AFFECTION_REQUIRED
    )


def get_tier(count):
    """Return (threshold, tier_data) or (0, None)."""
    for threshold, data in _TIERS:
        if count >= threshold:
            return threshold, data
    return 0, None


def bonded_allies(player):
    return [a for a in player.get("allies", [])
            if a.get("affection", 0) >= AFFECTION_REQUIRED]


def _add_battle_buff(actor, btype, value):
    if value <= 0:
        return
    actor.setdefault("active_buffs", []).append({
        "type": btype,
        "value": value,
        "remaining": 9999,
        "battle_scoped": True,
        "source": SOURCE,
    })


def apply_battle_start(player):
    """Round-1 hook (combat_engine). Returns the active tier threshold."""
    clear_battle_buffs(player)  # idempotent re-apply
    if not _has_por(player):
        return 0
    count = count_bonded_allies(player)
    threshold, data = get_tier(count)
    if not data:
        return 0
    _add_battle_buff(player, "damage_boost", data["mc_dmg"])
    _add_battle_buff(player, "evasion", data["mc_dodge"])
    _add_battle_buff(player, "crit_chance", data["mc_crit"])
    for ally in bonded_allies(player):
        _add_battle_buff(ally, "damage_boost", data["ally_dmg"])
        _add_battle_buff(ally, "evasion", data["ally_dodge"])
        _add_battle_buff(ally, "crit_chance", data["ally_crit"])
    c_print(f"  ✥ Piece of Relationship resonates with {count} bonded allies (tier +{threshold}).")
    return threshold


def clear_battle_buffs(player):
    """Strip every Piece of Relationship battle buff from the whole roster."""
    for actor in [player] + list(player.get("allies", [])):
        buffs = actor.get("active_buffs")
        if buffs:
            actor["active_buffs"] = [b for b in buffs if b.get("source") != SOURCE]


# ── Tier +7: mark attackers that target an ally (enemy_ai hook) ─────────────

def maybe_mark_attacker(attacker, target, actual_player=None):
    """Called from enemy_ai before the dodge check (hit or miss both mark)."""
    if attacker is None or target is None or actual_player is None:
        return
    if not target.get("is_ally"):
        return
    if not _has_por(actual_player):
        return
    _, data = get_tier(count_bonded_allies(actual_player))
    if not data or not data.get("mark"):
        return
    newly_marked = not attacker.get("hunters_mark")
    attacker["hunters_mark"] = True
    attacker["hunters_mark_bonus"] = max(attacker.get("hunters_mark_bonus", 0.0), MARK_BONUS)
    attacker["hunters_mark_turns"] = max(attacker.get("hunters_mark_turns", 0), MARK_TURNS)
    attacker["hunters_mark_source"] = "Piece of Relationship"
    if newly_marked:
        c_print(f"  ✥ A mirror-shard flashes — {attacker['name']} is marked!")
