"""Prescript Ledger — unique guild legacy accessory (Index-style obedience engine).

Design doc: docs/prescript_ledger_design.md

Each combat round a Prescript is issued to every wearing party member. Fulfilling
it grants Grace of the Prescript — stacking damage / crit / regen (cap 9; no
further gain at cap). Ignoring a feasible Prescript adds Karmic Consequence
(+3% damage taken per stack); at 6 stacks the debt is collected as Karmic
Retribution (sure-hit blow; Defend halves).

Actor-based: works for the player and any ally who has it equipped.
All combat state is ephemeral — reset at combat start and end.
"""

import random

from combat.combat_io import c_print
from character import player_max_hp

_SLOTS = ("accessory1", "accessory2", "accessory3", "accessory")

# ── Tuning constants (playtest knobs) ─────────────────────────────────
GRACE_CAP = 9
GRACE_DMG_PER = 0.02        # damage_boost per Grace stack
GRACE_CRIT_PER = 0.015      # crit_chance per Grace stack
GRACE_REGEN_PCT = 0.015     # max-HP regen per Grace stack, per round
CLASH_TIERS = ((9, 0.30), (6, 0.20), (3, 0.10))  # (min Grace, skill damage bonus)
KARMA_DT_PER = 0.03         # +damage taken per Karma stack
KARMA_BURST_AT = 6          # Karmic Retribution threshold
KARMA_BURST_PCT = 0.08      # burst = 8% max HP ...
KARMA_BURST_FLAT = 20       # ... + 20, sure-hit (Defend halves)

_GRACE_DMG_SOURCE = "prescript_grace_dmg"
_GRACE_CRIT_SOURCE = "prescript_grace_crit"
_KARMA_SOURCE = "prescript_karma"


# ══════════════════════════════════════════════════════════════════════
# Equipment helpers
# ══════════════════════════════════════════════════════════════════════

def _get_equipped_prescript_ledger(actor):
    """Return the equipped Prescript Ledger item dicts, or []."""
    equipment = actor.get("equipped", {})
    if not isinstance(equipment, dict):
        return []
    out = []
    for slot in _SLOTS:
        acc = equipment.get(slot)
        if acc and acc.get("id") == "prescript_ledger":
            out.append(acc)
    return out


def _actor_has_prescript_ledger(actor):
    """Return True if actor has the Prescript Ledger equipped as an accessory."""
    return bool(_get_equipped_prescript_ledger(actor))


def get_wearers(player):
    """Every living party member wearing the Ledger, player first."""
    wearers = []
    if player.get("current_hp", 0) > 0 and _actor_has_prescript_ledger(player):
        wearers.append(player)
    for ally in player.get("allies", []):
        if ally.get("current_hp", 0) > 0 and _actor_has_prescript_ledger(ally):
            wearers.append(ally)
    return wearers


def _actor_max_hp(actor):
    if actor.get("is_ally"):
        return max(1, actor.get("max_hp", 1))
    return max(1, player_max_hp(actor))


def _label(actor):
    return actor.get("name", "???")


# ══════════════════════════════════════════════════════════════════════
# State lifecycle (combat start / end)
# ══════════════════════════════════════════════════════════════════════

def _strip_source_buffs(actor):
    """Remove all Ledger-applied buffs/debuffs from an actor."""
    buffs = actor.get("active_buffs", [])
    actor["active_buffs"] = [
        b for b in buffs
        if b.get("source") not in (_GRACE_DMG_SOURCE, _GRACE_CRIT_SOURCE)
    ]
    debuffs = actor.get("active_debuffs", [])
    actor["active_debuffs"] = [
        d for d in debuffs if d.get("source") != _KARMA_SOURCE
    ]


def reset_all_state(player):
    """Clear all Ledger state for the whole party (combat start and end).

    Also drops stale per-round fields so nothing leaks between fights.
    """
    for actor in [player] + list(player.get("allies", [])):
        _strip_source_buffs(actor)
        for key in ("prescript_grace_stacks", "prescript_karma_stacks",
                    "prescript_acted", "prescript_defended",
                    "prescript_current", "prescript_last"):
            actor.pop(key, None)


# ══════════════════════════════════════════════════════════════════════
# Derived auras (single source-tagged refresh — never append duplicates)
# ══════════════════════════════════════════════════════════════════════

def _refresh_grace_buffs(actor):
    """Refresh the damage/crit auras to match current Grace stacks."""
    stacks = actor.get("prescript_grace_stacks", 0)
    buffs = actor.setdefault("active_buffs", [])
    if stacks <= 0:
        actor["active_buffs"] = [
            b for b in buffs
            if b.get("source") not in (_GRACE_DMG_SOURCE, _GRACE_CRIT_SOURCE)
        ]
        return
    dmg = next((b for b in buffs if b.get("source") == _GRACE_DMG_SOURCE), None)
    crit = next((b for b in buffs if b.get("source") == _GRACE_CRIT_SOURCE), None)
    if dmg is None:
        dmg = {"type": "damage_boost", "source": _GRACE_DMG_SOURCE,
               "value": 0.0, "remaining": 999}
        buffs.append(dmg)
    if crit is None:
        crit = {"type": "crit_chance", "source": _GRACE_CRIT_SOURCE,
                "value": 0.0, "remaining": 999}
        buffs.append(crit)
    dmg["value"] = round(GRACE_DMG_PER * stacks, 4)
    crit["value"] = round(GRACE_CRIT_PER * stacks, 4)


def _refresh_karma_debuff(actor):
    """Refresh (or clear) the Karma damage-taken debuff."""
    stacks = actor.get("prescript_karma_stacks", 0)
    debuffs = actor.setdefault("active_debuffs", [])
    debuffs[:] = [d for d in debuffs if d.get("source") != _KARMA_SOURCE]
    if stacks > 0:
        debuffs.append({
            "type": "vulnerable",
            "source": _KARMA_SOURCE,
            "value": round(KARMA_DT_PER * stacks, 4),
            "remaining": 999,
        })


# ══════════════════════════════════════════════════════════════════════
# Fulfilment / punishment
# ══════════════════════════════════════════════════════════════════════

def _prescript_text(p):
    kind = p.get("kind")
    if kind == "target":
        tgt = p.get("target_name") or "the marked one"
        return f'"Shed blood upon {tgt}."'
    if kind == "skill":
        return '"Exercise the art."'
    if kind == "item":
        return '"Partake of your provisions."'
    return '"Endure."'


def _atonement(actor):
    """Cleanse 1 Karma via a fulfilled Prescript — works at any Grace level.

    Returns True if a Karma stack was removed.
    """
    if actor.get("prescript_karma_stacks", 0) > 0:
        actor["prescript_karma_stacks"] -= 1
        _refresh_karma_debuff(actor)
        return True
    return False


def _fulfill(actor):
    """Resolve a fulfilled Prescript: Grace +1 (below cap) and atonement."""
    p = actor.get("prescript_current")
    if not p or p.get("done"):
        return
    p["done"] = True
    name = _label(actor)
    stacks = actor.get("prescript_grace_stacks", 0)
    if stacks >= GRACE_CAP:
        # Cap rule: no further Grace — but atonement still cleanses Karma.
        msg = f"  📜 {name} fulfils the prescript — the ledger is already full (Grace ×{GRACE_CAP})."
        if _atonement(actor):
            msg += " Atonement eases the karmic debt (−1)."
        c_print(msg)
        return
    stacks += 1
    actor["prescript_grace_stacks"] = stacks
    _refresh_grace_buffs(actor)
    msg = f"  📜 {name} fulfils the prescript — Grace of the Prescript ×{stacks}."
    if _atonement(actor):
        msg += " Atonement eases the karmic debt (−1)."
    c_print(msg)


def _punish(actor):
    """Ignored-but-feasible Prescript: +1 Karma (and Retribution at the cap)."""
    stacks = actor.get("prescript_karma_stacks", 0) + 1
    actor["prescript_karma_stacks"] = stacks
    _refresh_karma_debuff(actor)
    c_print(f"  📜 {_label(actor)} lets the prescript slip — Karmic Consequence ×{stacks} "
            f"(+{int(KARMA_DT_PER * stacks * 100)}% damage taken).")
    if stacks >= KARMA_BURST_AT:
        _retribution(actor)


def _retribution(actor):
    """Karmic Retribution: consume all Karma and collect the debt."""
    actor["prescript_karma_stacks"] = 0
    _refresh_karma_debuff(actor)
    dmg = int(_actor_max_hp(actor) * KARMA_BURST_PCT) + KARMA_BURST_FLAT
    halved = bool(actor.get("prescript_defended"))
    if halved:
        dmg = max(1, dmg // 2)
    actor["current_hp"] = max(0, actor.get("current_hp", 0) - dmg)
    suffix = " (halved by their guard)" if halved else ""
    c_print(f"  📜 KARMIC RETRIBUTION — the ledger collects its due! "
            f"{_label(actor)} takes {dmg} damage{suffix}.")
    if actor.get("current_hp", 0) <= 0:
        from combat.status_effects import try_consume_death_ward
        if try_consume_death_ward(actor):
            if not actor.pop("_eh_emperor_saved", False):
                c_print(f"  {_label(actor)}'s Undying Vow flares — survival at 1 HP!")
        else:
            c_print(f"  {_label(actor)} collapses under the karmic weight!")


# ══════════════════════════════════════════════════════════════════════
# Action reporting (called from the action branches)
# ══════════════════════════════════════════════════════════════════════

def mark_acted(actor):
    """Mark that the actor got a turn this round (waiver guard for evaluation)."""
    if actor.get("prescript_current") and _actor_has_prescript_ledger(actor):
        actor["prescript_acted"] = True


def _report(actor, kind):
    if not _actor_has_prescript_ledger(actor):
        return
    p = actor.get("prescript_current")
    if p and not p.get("done") and p.get("kind") == kind:
        _fulfill(actor)


def report_skill(actor):
    """Wearer used a skill-class action (skill, workshop, Furioso, brush exhibit)."""
    _report(actor, "skill")


def report_item(actor):
    """Wearer used a consumable/utility item."""
    _report(actor, "item")


def report_defend(actor):
    """Wearer took the Defend action."""
    if _actor_has_prescript_ledger(actor):
        actor["prescript_defended"] = True
    _report(actor, "defend")


def report_damage(actor, target):
    """Wearer's action damaged `target` (any source, via HP-delta detection)."""
    if not _actor_has_prescript_ledger(actor):
        return
    p = actor.get("prescript_current")
    if p and not p.get("done") and p.get("kind") == "target" \
            and target.get("prescript_mark"):
        _fulfill(actor)


# ══════════════════════════════════════════════════════════════════════
# Clash empowerment (skill-class damage vs the Prescript's Target)
# ══════════════════════════════════════════════════════════════════════

def get_clash_bonus(actor, target):
    """Return the skill-class damage bonus vs the round's Target (0.0 if none)."""
    if not target or not target.get("prescript_mark"):
        return 0.0
    if not _actor_has_prescript_ledger(actor):
        return 0.0
    stacks = actor.get("prescript_grace_stacks", 0)
    for threshold, bonus in CLASH_TIERS:
        if stacks >= threshold:
            return bonus
    return 0.0


# ══════════════════════════════════════════════════════════════════════
# Round lifecycle
# ══════════════════════════════════════════════════════════════════════

def _has_skill_action(actor, is_player):
    """Feasibility gate: does the actor's current kit have a usable skill action?"""
    from combat.weapon.black_silence_gloves import _actor_has_black_silence_gloves
    from combat.weapon.palette_brush import _actor_has_palette_brush
    if _actor_has_black_silence_gloves(actor) or _actor_has_palette_brush(actor):
        return True
    if is_player:
        from combat.skills import get_available_skills
        return bool(get_available_skills(actor))
    from combat.ally_skills import get_usable_skills_in_combat
    return bool(get_usable_skills_in_combat(actor))


def _can_use_item(actor, player):
    """Feasibility gate: shared bag has a combat item and the actor can reach it."""
    from combat.status_effects import is_silenced
    if is_silenced(actor):
        return False
    return any(
        item.get("type") in ("consumable", "utility")
        for item in player.get("inventory", [])
    )


def issue_prescripts(player, enemies):
    """Round start: mark the Prescript's Target, then issue one Prescript per wearer."""
    wearers = get_wearers(player)
    if not wearers:
        return

    for e in enemies:
        e.pop("prescript_mark", None)
    alive = [e for e in enemies if e.get("hp", 0) > 0 and not e.get("captured")]
    marked = random.choice(alive) if alive else None
    if marked is not None:
        marked["prescript_mark"] = True

    for actor in wearers:
        is_player = actor is player
        actor["prescript_acted"] = False
        actor["prescript_defended"] = False

        pool = []
        if marked is not None:
            pool.append("target")
        if _has_skill_action(actor, is_player):
            pool.append("skill")
        if _can_use_item(actor, player):
            pool.append("item")
        pool.append("defend")

        last = actor.get("prescript_last")
        choices = [k for k in pool if k != last] or pool
        kind = random.choice(choices)
        actor["prescript_last"] = kind
        actor["prescript_current"] = {
            "kind": kind,
            "target_name": marked["name"] if (kind == "target" and marked) else None,
            "done": False,
        }
        c_print(f"  📜 Prescript for {_label(actor)}: "
                f"{_prescript_text(actor['prescript_current'])}")


def evaluate_round(player, enemies):
    """Round end: resolve Prescripts, apply Grace regen, clear round state.

    Returns "dead" if the player died to Karmic Retribution, else None.
    Evaluation must only run from the round-end block of a combat loop —
    never from `_tick_all_state` (which also runs at combat end).
    """
    wearers = get_wearers(player)
    if not wearers:
        return None

    for actor in wearers:
        if actor.get("current_hp", 0) <= 0:
            continue
        p = actor.get("prescript_current")
        if p and not p.get("done"):
            # Auto-credit: the marked Target fell before the wearer struck it.
            if p.get("kind") == "target":
                still_marked = next(
                    (e for e in enemies
                     if e.get("prescript_mark") and e.get("hp", 0) > 0
                     and not e.get("captured")),
                    None,
                )
                if still_marked is None:
                    _fulfill(actor)
            if p and not p.get("done") and actor.get("prescript_acted"):
                _punish(actor)

        # Grace sustain: mends every round for as long as Grace is held.
        stacks = actor.get("prescript_grace_stacks", 0)
        if stacks > 0 and actor.get("current_hp", 0) > 0:
            heal = int(_actor_max_hp(actor) * GRACE_REGEN_PCT * stacks)
            if heal > 0:
                actor["current_hp"] = min(
                    actor["current_hp"] + heal, _actor_max_hp(actor))
                c_print(f"  📜 Grace of the Prescript mends {heal} HP for {_label(actor)}.")

        actor["prescript_current"] = None
        actor["prescript_acted"] = False
        actor["prescript_defended"] = False

    for e in enemies:
        e.pop("prescript_mark", None)

    if player.get("current_hp", 0) <= 0:
        return "dead"
    return None
