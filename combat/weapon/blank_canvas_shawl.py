# combat/weapon/blank_canvas_shawl.py
"""Blank Canvas Shawl — unique armor logic (actor-based, player AND allies).

Once per combat, a free action:
  - Cleanse ALL debuffs from the wearer (including Paint — unless Fixative
    locked it), heal 15% max HP, and gain Afterimage (blocks the next 2
    debuff applications for 2 turns).
  - Cost: also clears ALL of the wearer's buffs — a true blank canvas.

Recruited Palette wearing her own shawl upgrades it: the cleanse + heal
becomes party-wide (10% max HP per member); she keeps her Afterimage window.

Afterimage gates every debuff application via try_consume_afterimage(),
called from combat/status_effects.py apply_* functions and the Paint system.
"""

# ═══════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════

SHAWL_ITEM_ID = "blank_canvas_shawl"

AFTERIMAGE_TURNS = 2
AFTERIMAGE_CHARGES = 2


def _actor_has_blank_canvas_shawl(actor):
    """Check if an actor has the Blank Canvas Shawl equipped in the armor slot."""
    equipped = actor.get("equipped", {})
    if isinstance(equipped, dict):
        armor = equipped.get("armor")
        if armor and armor.get("id") == SHAWL_ITEM_ID:
            return True
    return False


def _max_hp_of(actor, is_player):
    if is_player:
        from character import player_max_hp
        return player_max_hp(actor)
    return actor.get("max_hp", 1)


def _cleanse_actor(actor):
    """Remove all debuffs (except Fixative-locked paint) + debuff flags."""
    actor["active_debuffs"] = [
        d for d in actor.get("active_debuffs", [])
        if d.get("type") == "paint" and d.get("fixed")
    ]
    for flag in ("stunned", "slowed", "blinded", "silenced", "dreaded",
                 "frozen", "confused", "cursed", "void_touched"):
        if flag in actor:
            actor[flag] = False


def _grant_afterimage(actor):
    actor["afterimage_turns"] = AFTERIMAGE_TURNS
    actor["afterimage_charges"] = AFTERIMAGE_CHARGES


def try_consume_afterimage(actor):
    """Block one incoming debuff application if Afterimage is active.

    Returns True if the debuff was absorbed (caller should skip applying it).
    """
    charges = actor.get("afterimage_charges", 0)
    turns = actor.get("afterimage_turns", 0)
    if charges <= 0 or turns <= 0:
        return False
    charges -= 1
    if charges <= 0:
        actor.pop("afterimage_charges", None)
    else:
        actor["afterimage_charges"] = charges
    return True


def tick_afterimage(actor):
    """Count down Afterimage at round end. Returns messages."""
    turns = actor.get("afterimage_turns", 0)
    if turns <= 0:
        return []
    turns -= 1
    if turns <= 0:
        actor.pop("afterimage_turns", None)
        actor.pop("afterimage_charges", None)
        return ["The afterimage fades — you are vulnerable to stains once more."]
    actor["afterimage_turns"] = turns
    return []


def clear_shawl_state(actor):
    """Called at combat end."""
    actor.pop("blank_canvas_used", None)
    actor.pop("afterimage_turns", None)
    actor.pop("afterimage_charges", None)


# ═══════════════════════════════════════════════════════════════════
# ACTIVATION
# ═══════════════════════════════════════════════════════════════════

def use_blank_canvas(actor, is_player, player):
    """Activate the shawl. Free action, once per combat.

    Returns a list of message strings.
    """
    from combat.combat_io import c_print

    if not _actor_has_blank_canvas_shawl(actor):
        return ["You are not wearing the Blank Canvas Shawl."]
    if actor.get("blank_canvas_used"):
        return ["The shawl is pristine but still — it has already been used this battle."]

    actor["blank_canvas_used"] = True
    msgs = []

    is_palette = actor.get("_heroine_key") == "palette"

    if is_palette:
        # ── Party-wide Blank Canvas (Palette heroine upgrade) ──
        from combat.ally import get_active_allies
        members = [player] + [a for a in get_active_allies(player) if a.get("current_hp", 0) > 0]
        for member in members:
            _cleanse_actor(member)
            heal = int(_max_hp_of(member, member is player) * 0.10)
            if heal > 0 and member.get("current_hp", 0) > 0:
                old_hp = member["current_hp"]
                max_hp = _max_hp_of(member, member is player)
                member["current_hp"] = min(old_hp + heal, max_hp)
                actual = member["current_hp"] - old_hp
                if actual > 0:
                    msgs.append(f"🩹 {member['name']} is healed for {actual} HP.")
        msgs.insert(0, f"🖼️  {actor['name']} sweeps the canvas clean — the whole party's "
                        "wounds and curses are wiped away!")
        _grant_afterimage(actor)
        msgs.append(f"👻 Afterimage: {actor['name']} will deflect the next 2 debuffs for 2 turns!")
    else:
        # ── Self cleanse ──
        _cleanse_actor(actor)
        msgs.append(f"🖼️  {actor['name']} wipes the canvas clean — every debuff is gone!")
        # ── Heal 15% ──
        heal = int(_max_hp_of(actor, is_player) * 0.15)
        if heal > 0 and actor.get("current_hp", 0) > 0:
            old_hp = actor["current_hp"]
            max_hp = _max_hp_of(actor, is_player)
            actor["current_hp"] = min(old_hp + heal, max_hp)
            actual = actor["current_hp"] - old_hp
            if actual > 0:
                msgs.append(f"🩹 {actor['name']} is healed for {actual} HP!")
        _grant_afterimage(actor)
        msgs.append("👻 Afterimage: the next 2 debuffs are deflected for 2 turns!")

    # ── The cost: a true blank canvas wipes the wearer's own buffs too ──
    actor["active_buffs"] = [
        b for b in actor.get("active_buffs", [])
        if b.get("type") in ("blessing", "well_rested", "floor_buff")
    ]
    msgs.append("⚪ The canvas takes its price — all of your own buffs are wiped away.")

    return msgs
