# status_effects.py
# Pure functions for applying, ticking, and cleaning up status effects.
# All functions return a list of message strings and mutate the entity dict in place.
# Import and call these in combat.py and superboss_combat.py instead of copy-pasting loops.

import random
from character import player_max_hp


# ===========================================================================
# BURN TIER SYSTEM
# ===========================================================================

# Each tier has a unique name, flat damage/turn, and status tag for the HUD.
# Higher tier = more intense burn.  Applying a higher tier upgrades the debuff;
# same/lower tier refreshes duration without downgrading damage.
BURN_TIERS = {
    1: {"name": "Singe",         "damage": 3,  "tag": "SNG", "icon": "🔥"},
    2: {"name": "Burn",          "damage": 6,  "tag": "BRN", "icon": "🔥"},
    3: {"name": "Blaze",         "damage": 10, "tag": "BLZ", "icon": "💥"},
    4: {"name": "Inferno",       "damage": 18, "tag": "INF", "icon": "💥"},
    5: {"name": "Conflagration", "damage": 30, "tag": "CFL", "icon": "☀️"},
}


def damage_to_burn_tier(damage: int) -> int:
    """Map a legacy flat burn_damage value to the closest burn tier.

    Used to convert old skill/effect burn values into the tier system.
    """
    if damage <= 3:
        return 1
    if damage <= 6:
        return 2
    if damage <= 10:
        return 3
    if damage <= 18:
        return 4
    return 5


def get_burn_tier_name(tier: int) -> str:
    """Return the display name for a burn tier (e.g. 'Blaze')."""
    return BURN_TIERS.get(tier, BURN_TIERS[2])["name"]


def get_burn_tier_tag(tier: int) -> str:
    """Return the short HUD tag for a burn tier (e.g. 'BLZ')."""
    return BURN_TIERS.get(tier, BURN_TIERS[2])["tag"]


# ===========================================================================
# APPLYING EFFECTS
# ===========================================================================

# ---------------------------------------------------------------------------
# EXISTING EFFECTS (unchanged API)
# ---------------------------------------------------------------------------

def apply_poison(target, damage, duration):
    """Apply or refresh poison on a target (player or enemy dict).

    Returns 'applied' or 'refreshed'.
    """
    from combat.weapon.blank_canvas_shawl import try_consume_afterimage
    if try_consume_afterimage(target):
        return None
    existing = next(
        (d for d in target.get("active_debuffs", []) if d["type"] == "poison"),
        None,
    )
    if existing:
        existing["remaining"] = duration
        existing["damage"] = damage
        return "refreshed"
    target.setdefault("active_debuffs", []).append(
        {"type": "poison", "damage": damage, "remaining": duration}
    )
    return "applied"


def apply_curse(player, enemy_level=None):
    from combat.weapon.blank_canvas_shawl import try_consume_afterimage
    if try_consume_afterimage(player):
        return None
    if player.get("cursed"):
        return "already_cursed"
    penalty = max(2, player.get("level", 1) // 3)   # dynamic
    player["cursed"] = True
    player.setdefault("active_debuffs", []).append({
        "type": "curse",
        "remaining": -1,
        "penalty": penalty
    })
    return "applied"


# ---------------------------------------------------------------------------
# NEW ENEMY DEBUFFS  (applied to enemy dicts)
# ---------------------------------------------------------------------------

def apply_burn(target, tier=None, duration=3, damage=None):
    """Apply a burn of the given tier to a target (enemy OR player dict).

    Tier system:
    - Higher tier source -> upgrades directly to that tier.
    - Same tier source -> intensifies the burn by +1 tier (repeated application).
    - Lower tier source -> refreshes duration without changing damage.
    - Capped at tier 5 (Conflagration).

    For enemies: also reduces con_mod by 1 on first application.

    Call as ``apply_burn(target, tier=3)`` (new) or ``apply_burn(target, damage=7)`` (legacy).
    If both are passed, *tier* takes precedence.

    Returns 'applied', 'upgraded', 'intensified', or 'refreshed'.
    """
    # Backward compatibility: old-style damage= keyword auto-converts to tier
    if tier is None:
        if damage is not None:
            tier = damage_to_burn_tier(damage)
        else:
            tier = 2  # default

    from combat.weapon.blank_canvas_shawl import try_consume_afterimage
    if try_consume_afterimage(target):
        return None

    tier_info = BURN_TIERS.get(tier, BURN_TIERS[2])
    damage_val = tier_info["damage"]

    existing = next((d for d in target.get("active_debuffs", []) if d["type"] == "burn"), None)
    if existing:
        old_tier = existing.get("tier", 2)
        if tier > old_tier:
            # Higher tier source: upgrade directly to that tier
            existing["tier"] = tier
            existing["damage"] = damage_val
            existing["remaining"] = duration
            return "upgraded"
        elif tier == old_tier and old_tier < 5:
            # Same tier: repeated application intensifies the burn by 1 tier
            new_tier = old_tier + 1
            new_info = BURN_TIERS[new_tier]
            existing["tier"] = new_tier
            existing["damage"] = new_info["damage"]
            existing["remaining"] = duration
            return "intensified"
        else:
            # Lower tier, or already at cap: just refresh duration
            existing["remaining"] = duration
            return "refreshed"

    # New application
    # For enemies, reduce CON
    if "con_mod" in target:
        target.setdefault("burn_original_con", target["con_mod"])
        target["con_mod"] = max(0, target["con_mod"] - 1)
    target.setdefault("active_debuffs", []).append(
        {"type": "burn", "tier": tier, "damage": damage_val, "remaining": duration}
    )
    return "applied"


def apply_burn_to_player(player, tier=None, duration=3, damage=None):
    """Apply a burn to a player dict (no CON reduction).

    Tier system:
    - Higher tier source -> upgrades directly to that tier.
    - Same tier source -> intensifies the burn by +1 tier (repeated application).
    - Lower tier source -> refreshes duration without changing damage.
    - Capped at tier 5 (Conflagration).

    Call as ``apply_burn_to_player(player, tier=2)`` (new) or
    ``apply_burn_to_player(player, damage=3)`` (legacy).
    If both are passed, *tier* takes precedence.
    """
    # Backward compatibility: old-style damage= keyword auto-converts to tier
    if tier is None:
        if damage is not None:
            tier = damage_to_burn_tier(damage)
        else:
            tier = 1  # default

    from combat.weapon.blank_canvas_shawl import try_consume_afterimage
    if try_consume_afterimage(player):
        return None

    tier_info = BURN_TIERS.get(tier, BURN_TIERS[1])
    damage_val = tier_info["damage"]

    existing = next(
        (d for d in player.get("active_debuffs", []) if d["type"] == "burn"),
        None,
    )
    if existing:
        old_tier = existing.get("tier", 1)
        if tier > old_tier:
            existing["tier"] = tier
            existing["damage"] = damage_val
            existing["remaining"] = duration
            return "upgraded"
        elif tier == old_tier and old_tier < 5:
            new_tier = old_tier + 1
            new_info = BURN_TIERS[new_tier]
            existing["tier"] = new_tier
            existing["damage"] = new_info["damage"]
            existing["remaining"] = duration
            return "intensified"
        else:
            existing["remaining"] = duration
            return "refreshed"
    player.setdefault("active_debuffs", []).append(
        {"type": "burn", "tier": tier, "damage": damage_val, "remaining": duration}
    )
    return "applied"


def apply_freeze(enemy, duration=2):
    """Freeze an enemy solid.

    Frozen enemies:
    - Skip their next attack (like stun) AND
    - Gain the 'slowed' flag after thawing for 1 round.

    Returns 'applied' or 'already_frozen'.
    """
    if enemy.get("frozen"):
        return "already_frozen"
    enemy["frozen"] = True
    enemy["freeze_duration"] = duration
    return "applied"


def apply_expose(enemy, armor_reduction=2):
    """Shatter an enemy's armour plating.

    Permanently reduces con_mod for this fight.  Cannot reduce below 0.
    Multiple applications stack up to a cap of 5 total reduction.

    Returns ('applied', new_con) or ('capped', current_con).
    """
    total_reduction = enemy.get("expose_stacks", 0) + armor_reduction
    if total_reduction > 5:
        armor_reduction = 5 - enemy.get("expose_stacks", 0)
        if armor_reduction <= 0:
            return "capped", enemy.get("con_mod", 0)
    enemy["expose_stacks"] = enemy.get("expose_stacks", 0) + armor_reduction
    enemy["con_mod"] = max(0, enemy.get("con_mod", 0) - armor_reduction)
    return "applied", enemy["con_mod"]


# ---------------------------------------------------------------------------
# NEW PLAYER DEBUFFS  (applied to player dicts)
# ---------------------------------------------------------------------------

def apply_weaken(player, str_penalty=2, duration=3):
    """Apply a Weakened condition to the player.

    Reduces effective Strength for damage rolls.  Tracked via active_debuffs
    so get_effective_attribute() must read it (see integration notes below).

    Returns 'applied' or 'refreshed'.
    """
    from combat.weapon.blank_canvas_shawl import try_consume_afterimage
    if try_consume_afterimage(player):
        return None
    existing = next(
        (d for d in player.get("active_debuffs", []) if d["type"] == "weaken"),
        None,
    )
    if existing:
        existing["remaining"] = duration
        existing["penalty"] = max(existing.get("penalty", 0), str_penalty)
        return "refreshed"
    player.setdefault("active_debuffs", []).append({
        "type": "weaken",
        "penalty": str_penalty,
        "remaining": duration,
    })
    return "applied"


def apply_bleed(target, damage, duration=4):
    """Apply a Bleed wound to a target (player or enemy dict).

    Bleed deals damage each round.  Unlike poison it does NOT stack — a
    heavier bleed (higher damage) overwrites a lighter one.

    Returns 'applied', 'refreshed', or 'no_change' (existing bleed is worse).
    """
    from combat.weapon.blank_canvas_shawl import try_consume_afterimage
    if try_consume_afterimage(target):
        return None
    existing = next(
        (d for d in target.get("active_debuffs", []) if d["type"] == "bleed"),
        None,
    )
    if existing:
        if damage > existing["damage"]:
            existing["damage"] = damage
            existing["remaining"] = duration
            return "refreshed"
        return "no_change"
    target.setdefault("active_debuffs", []).append({
        "type": "bleed",
        "damage": damage,
        "remaining": duration,
    })
    return "applied"


def apply_silence(player, duration=2):
    """Silence the player, preventing item use for N turns.

    Returns 'applied' or 'already_silenced'.
    """
    from combat.weapon.blank_canvas_shawl import try_consume_afterimage
    if try_consume_afterimage(player):
        return None
    if player.get("silenced"):
        return "already_silenced"
    player["silenced"] = True
    player.setdefault("active_debuffs", []).append({
        "type": "silence",
        "remaining": duration,
    })
    return "applied"

def apply_blind(player, duration=2):
    """Blind the player – 25% miss chance, -2 Dex for flee."""
    from combat.weapon.blank_canvas_shawl import try_consume_afterimage
    if try_consume_afterimage(player):
        return None
    existing = next((d for d in player.get("active_debuffs", []) if d["type"] == "blind"), None)
    if existing:
        existing["remaining"] = max(existing["remaining"], duration)
        return "refreshed"
    player.setdefault("active_debuffs", []).append({
        "type": "blind",
        "remaining": duration,
    })
    player["blinded"] = True
    return "applied"

def apply_drain(player, enemy, drain_amount):
    """Vampire drain: steals HP from player and heals the enemy.

    Caps the heal so the enemy cannot exceed its max_hp.
    Mutates both dicts in place.

    Returns actual amount drained (may be less than drain_amount if player
    would die — caller decides whether to clamp at 1).
    """
    from combat.weapon.blank_canvas_shawl import try_consume_afterimage
    if try_consume_afterimage(player):
        return 0
    actual = min(drain_amount, player["current_hp"] - 1)   # leave player at 1
    actual = max(0, actual)
    player["current_hp"] -= actual
    enemy["hp"] = min(enemy["hp"] + actual, enemy.get("max_hp", enemy["hp"]))
    return actual


def apply_dread(player, duration=2):
    """Fill the player with supernatural dread.

    While dreaded:
    - 40 % chance each attack action misses entirely (rolled in combat).
    - Flee difficulty increases by 4 (applied in flee roll).

    Returns 'applied' or 'already_dreaded'.
    """
    from combat.weapon.blank_canvas_shawl import try_consume_afterimage
    if try_consume_afterimage(player):
        return None
    if player.get("dreaded"):
        return "already_dreaded"
    player["dreaded"] = True
    player.setdefault("active_debuffs", []).append({
        "type": "dread",
        "remaining": duration,
    })
    return "applied"


# ===========================================================================
# NEW STATUS EFFECTS — Phase 8 Additions
# ===========================================================================

# ---------------------------------------------------------------------------
# 1. SHOCKED (Thunder DoT + Stun Proc)
# ---------------------------------------------------------------------------

def apply_shock(enemy, damage, duration=3):
    """Apply Shocked to an enemy — thunder DoT with stun chance per tick."""
    existing = next(
        (d for d in enemy.get("active_debuffs", []) if d["type"] == "shock"), None
    )
    if existing:
        existing["remaining"] = duration
        existing["damage"] = max(existing["damage"], damage)
        return "refreshed"
    enemy.setdefault("active_debuffs", []).append({
        "type": "shock",
        "damage": damage,
        "remaining": duration,
    })
    return "applied"


def apply_shock_to_player(player, damage, duration=3):
    """Apply Shocked to a player — thunder DoT with 25% stun proc per tick."""
    from combat.weapon.blank_canvas_shawl import try_consume_afterimage
    if try_consume_afterimage(player):
        return None
    existing = next(
        (d for d in player.get("active_debuffs", []) if d["type"] == "shock"), None
    )
    if existing:
        existing["remaining"] = duration
        existing["damage"] = max(existing["damage"], damage)
        return "refreshed"
    player.setdefault("active_debuffs", []).append({
        "type": "shock",
        "damage": damage,
        "remaining": duration,
    })
    return "applied"


def apply_slow_to_player(player, duration=2):
    """Apply a timed Slow debuff to the player (-3 DEX, initiative penalty)."""
    from combat.weapon.blank_canvas_shawl import try_consume_afterimage
    if try_consume_afterimage(player):
        return None
    existing = next(
        (d for d in player.get("active_debuffs", []) if d["type"] == "slow"), None
    )
    if existing:
        existing["remaining"] = max(existing["remaining"], duration)
        return "refreshed"
    player.setdefault("active_debuffs", []).append({
        "type": "slow",
        "remaining": duration,
    })
    return "applied"


def apply_confusion_to_player(player, duration=2):
    """Apply Confusion to a player — 30% chance to hit own ally or miss."""
    from combat.weapon.blank_canvas_shawl import try_consume_afterimage
    if try_consume_afterimage(player):
        return None
    existing = next(
        (d for d in player.get("active_debuffs", []) if d["type"] == "confusion"), None
    )
    if existing:
        existing["remaining"] = max(existing.get("remaining", 0), duration)
        return "refreshed"
    player.setdefault("active_debuffs", []).append({
        "type": "confusion",
        "value": 0.30,
        "remaining": duration,
    })
    return "applied"


# Backward-compatible aliases for code that imports from status_effects
apply_confusion = apply_confusion_to_player
apply_slow = apply_slow_to_player


# ---------------------------------------------------------------------------
# 2. BARRIER / WARD (Damage-Absorb Shield)
# ---------------------------------------------------------------------------

def apply_barrier(target, amount, duration=3):
    """Grant a damage-absorbing barrier to target (player or ally).

    Barrier absorbs incoming damage before HP is reduced.
    Stacks by adding to remaining absorb, not overwriting.
    """
    existing = next(
        (b for b in target.get("active_buffs", []) if b.get("type") == "barrier"), None
    )
    if existing:
        existing["value"] += amount
        existing["remaining"] = max(existing["remaining"], duration)
        return "reinforced"
    target.setdefault("active_buffs", []).append({
        "type": "barrier",
        "value": amount,
        "remaining": duration,
    })
    return "applied"


def absorb_damage(target, incoming_damage):
    """Apply barrier absorption to incoming damage. Call BEFORE dealing damage.

    Returns (actual_damage, absorbed_amount).
    Mutates barrier buff in place (reduces value or removes).
    """
    for buff in target.get("active_buffs", [])[:]:
        if buff.get("type") == "barrier" and buff.get("value", 0) > 0:
            absorbed = min(buff["value"], incoming_damage)
            buff["value"] -= absorbed
            if buff["value"] <= 0:
                target["active_buffs"].remove(buff)
            return incoming_damage - absorbed, absorbed
    return incoming_damage, 0


def get_barrier_remaining(target):
    """Return total barrier absorb remaining (0 if none)."""
    return sum(b.get("value", 0) for b in target.get("active_buffs", [])
               if b.get("type") == "barrier")


# ---------------------------------------------------------------------------
# 3. SLEEP (Action Lock, Breaks on Damage)
# ---------------------------------------------------------------------------

def apply_sleep(enemy, duration=3):
    """Put an enemy to sleep. Slept enemies skip turns until damaged."""
    if enemy.get("asleep"):
        return "already_asleep"
    enemy["asleep"] = True
    enemy.setdefault("active_debuffs", []).append({
        "type": "sleep",
        "remaining": duration,
    })
    return "applied"


def wake_on_damage(enemy):
    """Call after dealing damage to a sleeping enemy. Returns message or None."""
    if enemy.get("asleep"):
        enemy["asleep"] = False
        enemy["active_debuffs"] = [
            d for d in enemy.get("active_debuffs", []) if d.get("type") != "sleep"
        ]
        return f"The {enemy['name']} jolts awake!"
    return None


def is_asleep(enemy):
    """True if the enemy is currently asleep."""
    return bool(enemy.get("asleep"))


# ---------------------------------------------------------------------------
# 4. HASTE (Speed & Action Buff)
# ---------------------------------------------------------------------------

def apply_haste(target, duration=3, init_bonus=3, cd_reduction=1):
    """Haste the target — they act faster and skills recover quicker."""
    existing = next(
        (b for b in target.get("active_buffs", []) if b.get("type") == "haste"), None
    )
    if existing:
        existing["remaining"] = max(existing["remaining"], duration)
        existing["value"] = max(existing.get("value", 0), init_bonus)
        existing["cd_reduction"] = max(existing.get("cd_reduction", 0), cd_reduction)
        return "refreshed"
    target.setdefault("active_buffs", []).append({
        "type": "haste",
        "value": init_bonus,        # initiative bonus
        "cd_reduction": cd_reduction,
        "remaining": duration,
    })
    return "applied"


def get_haste_initiative_bonus(target):
    """Return the initiative bonus from Haste (0 if none)."""
    for b in target.get("active_buffs", []):
        if b.get("type") == "haste":
            return b.get("value", 0)
    return 0


def consume_haste_cd_reduction(target):
    """Consume one Haste CD reduction charge. Returns the reduction value (0 if none)."""
    for buff in target.get("active_buffs", []):
        if buff.get("type") == "haste" and buff.get("cd_reduction", 0) > 0:
            reduction = buff["cd_reduction"]
            buff["cd_reduction"] = 0
            return reduction
    return 0


# ---------------------------------------------------------------------------
# 5. PARALYZE (Stronger Stun — Multi-Turn, No Auto-Break)
# ---------------------------------------------------------------------------

def apply_paralyze(enemy, duration=2):
    """Paralyze an enemy — skip all actions for N turns. Stronger than stun."""
    if enemy.get("paralyzed"):
        return "already_paralyzed"
    enemy["paralyzed"] = True
    enemy.setdefault("active_debuffs", []).append({
        "type": "paralyze",
        "remaining": duration,
    })
    return "applied"


def is_paralyzed(enemy):
    """True if the enemy is currently paralyzed."""
    return bool(enemy.get("paralyzed"))


# ---------------------------------------------------------------------------
# 6. REGENERATION (Long-Duration HoT)
# ---------------------------------------------------------------------------

def apply_regen(target, heal_per_tick, duration=5):
    """Grant long-duration regeneration. Heals a small amount each round."""
    existing = next(
        (b for b in target.get("active_buffs", []) if b.get("type") == "regen"), None
    )
    if existing:
        existing["value"] = max(existing["value"], heal_per_tick)
        existing["remaining"] = max(existing["remaining"], duration)
        return "refreshed"
    target.setdefault("active_buffs", []).append({
        "type": "regen",
        "value": heal_per_tick,
        "remaining": duration,
    })
    return "applied"


# ---------------------------------------------------------------------------
# 7. ENTOMBED (Earth — Flee Lock + Healing Reduction)
# ---------------------------------------------------------------------------

def apply_entomb(enemy, duration=3):
    """Entomb an enemy in stone. Cannot flee. Healing received is halved."""
    existing = next(
        (d for d in enemy.get("active_debuffs", []) if d["type"] == "entomb"), None
    )
    if existing:
        existing["remaining"] = max(existing["remaining"], duration)
        return "refreshed"
    enemy.setdefault("active_debuffs", []).append({
        "type": "entomb",
        "remaining": duration,
    })
    enemy["entombed"] = True
    return "applied"


def is_entombed(enemy):
    """Check if an enemy is entombed (for healing reduction)."""
    return bool(enemy.get("entombed"))


def get_healing_multiplier(target):
    """Return healing multiplier (0.5 if entombed, 1.0 otherwise)."""
    return 0.5 if target.get("entombed") else 1.0


# ---------------------------------------------------------------------------
# 8. VOID-TOUCHED (Dark — Healing Becomes Damage)
# ---------------------------------------------------------------------------

def apply_void_touched(target, duration=2):
    """Curse target with void — healing received becomes damage."""
    from combat.weapon.blank_canvas_shawl import try_consume_afterimage
    if try_consume_afterimage(target):
        return None
    if target.get("void_touched"):
        return "already_void_touched"
    target["void_touched"] = True
    target.setdefault("active_debuffs", []).append({
        "type": "void_touched",
        "remaining": duration,
    })
    return "applied"


def is_void_touched(target):
    """True if the target is void-touched."""
    return bool(target.get("void_touched"))


def apply_healing(target, amount):
    """Apply healing to a target, respecting void_touched and entomb.

    Returns the actual HP change (positive = healed, negative = damage dealt).
    Mutates target['current_hp'] or target['hp'] in place.
    """
    hp_key = "current_hp" if "current_hp" in target else "hp"
    max_key = "max_hp" if "current_hp" in target else "max_hp"

    # Compute max HP: use stored key if present, otherwise compute dynamically
    # (the player dict doesn't store max_hp — it's computed via player_max_hp())
    if max_key in target:
        max_hp = target[max_key]
    elif "attributes" in target:
        from character import player_max_hp
        max_hp = player_max_hp(target)
    else:
        max_hp = target.get(hp_key, 100)

    # Void-touched: healing becomes damage
    if target.get("void_touched"):
        target[hp_key] -= amount
        return -amount  # negative = damage dealt

    # Entomb: healing halved (enemy only)
    if target.get("entombed"):
        amount = max(1, amount // 2)

    old_hp = target[hp_key]
    target[hp_key] = min(old_hp + amount, max_hp)
    return target[hp_key] - old_hp


# ===========================================================================
# TICKING DEBUFFS  (called once per round)
# ===========================================================================

def tick_enemy_debuffs(enemy):
    """Tick dot/burn/blind/freeze debuffs on an enemy dict.

    Returns (messages, died).
    """
    messages = []
    if not enemy.get("active_debuffs"):
        # Still need to handle freeze separately (stored as flat flag)
        messages, died = _tick_enemy_freeze(enemy, messages)
        return messages, died

    for debuff in enemy["active_debuffs"][:]:

        if debuff["type"] == "poison":
            dmg = debuff["damage"]
            enemy["hp"] -= dmg
            messages.append(f"The {enemy['name']} takes {dmg} poison damage!")
            debuff["remaining"] -= 1
            if debuff["remaining"] <= 0:
                enemy["active_debuffs"].remove(debuff)

        elif debuff["type"] == "bleed":
            dmg = debuff["damage"]
            enemy["hp"] -= dmg
            messages.append(f"The {enemy['name']} bleeds for {dmg} damage!")
            debuff["remaining"] -= 1
            if debuff["remaining"] <= 0:
                enemy["active_debuffs"].remove(debuff)
                messages.append(f"The {enemy['name']}'s wounds finally clot.")

        elif debuff["type"] == "burn":
            dmg = debuff["damage"]
            tier = debuff.get("tier", 2)
            tier_name = BURN_TIERS.get(tier, BURN_TIERS[2])["name"]
            enemy["hp"] -= dmg
            messages.append(f"The {enemy['name']} suffers {dmg} {tier_name} damage!")
            debuff["remaining"] -= 1
            if debuff["remaining"] <= 0:
        # Restore original CON
                if "burn_original_con" in enemy:
                    enemy["con_mod"] = enemy["burn_original_con"]
                    del enemy["burn_original_con"]
                enemy["active_debuffs"].remove(debuff)
                messages.append(f"The {tier_name} on {enemy['name']} dies out.")

        elif debuff["type"] == "blind":
            debuff["remaining"] -= 1
            if debuff["remaining"] <= 0:
                enemy["blinded"] = False
                enemy["active_debuffs"].remove(debuff)
                messages.append(f"The {enemy['name']} recovers their vision.")
        elif debuff["type"] == "fear":
            debuff["remaining"] -= 1
            if debuff["remaining"] <= 0:
                enemy["active_debuffs"].remove(debuff)
                messages.append(f"The {enemy['name']} shakes off the fear!")

        elif debuff["type"] == "slow":
            debuff["remaining"] -= 1
            if debuff["remaining"] <= 0:
                enemy["slowed"] = False
                enemy["active_debuffs"].remove(debuff)
                messages.append(f"The {enemy['name']} is no longer slowed.")

        elif debuff["type"] == "confusion":
            debuff["remaining"] -= 1
            if debuff["remaining"] <= 0:
                enemy["confused"] = False
                enemy["active_debuffs"].remove(debuff)
                messages.append(f"The {enemy['name']} shakes off the confusion!")

        elif debuff["type"] == "stun":
            debuff["remaining"] -= 1
            if debuff["remaining"] <= 0:
                enemy["active_debuffs"].remove(debuff)

        elif debuff["type"] == "weaken":
            debuff["remaining"] -= 1
            if debuff["remaining"] <= 0:
                enemy["active_debuffs"].remove(debuff)

        elif debuff["type"] == "curse":
            debuff["remaining"] -= 1
            if debuff["remaining"] <= 0:
                enemy["active_debuffs"].remove(debuff)

        elif debuff["type"] == "elemental_weakness":
            debuff["remaining"] -= 1
            if debuff["remaining"] <= 0:
                enemy["active_debuffs"].remove(debuff)
                messages.append(f"The {enemy['name']}'s elemental weakness fades.")

        elif debuff["type"] == "shock":
            dmg = debuff["damage"]
            enemy["hp"] -= dmg
            messages.append(f"The {enemy['name']} is jolted for {dmg} thunder damage!")
            # 25% chance to stun on each tick
            if random.random() < 0.25:
                enemy["stunned"] = True
                messages.append(f"The {enemy['name']} is paralyzed by the shock!")
            debuff["remaining"] -= 1
            if debuff["remaining"] <= 0:
                enemy["active_debuffs"].remove(debuff)
                messages.append(f"The sparks fade from {enemy['name']}.")

        elif debuff["type"] == "sleep":
            debuff["remaining"] -= 1
            if debuff["remaining"] <= 0:
                enemy["asleep"] = False
                enemy["active_debuffs"].remove(debuff)
                messages.append(f"The {enemy['name']} stirs awake naturally.")

        elif debuff["type"] == "paralyze":
            debuff["remaining"] -= 1
            if debuff["remaining"] <= 0:
                enemy["paralyzed"] = False
                enemy["active_debuffs"].remove(debuff)
                messages.append(f"The {enemy['name']} breaks free from paralysis!")

        elif debuff["type"] == "entomb":
            debuff["remaining"] -= 1
            if debuff["remaining"] <= 0:
                enemy["entombed"] = False
                enemy["active_debuffs"].remove(debuff)
                messages.append(f"The stone crumbles from {enemy['name']}.")

        elif debuff["type"] == "void_touched":
            debuff["remaining"] -= 1
            if debuff["remaining"] <= 0:
                enemy["void_touched"] = False
                enemy["active_debuffs"].remove(debuff)
                messages.append(f"The void's grip on the {enemy['name']} releases.")

    # Handle Hunter's Mark expiration (stored as flat flag + counter)
    if enemy.get("hunters_mark"):
        enemy["hunters_mark_turns"] = enemy.get("hunters_mark_turns", 1) - 1
        if enemy["hunters_mark_turns"] <= 0:
            enemy["hunters_mark"] = False
            messages.append(f"The mark on {enemy['name']} fades.")

    # Handle freeze (stored as flat flag + counter, not in active_debuffs list)
    messages, died_from_freeze = _tick_enemy_freeze(enemy, messages)

    died = enemy["hp"] <= 0
    if died:
        messages.append(f"The {enemy['name']} has succumbed to status damage!")
    return messages, died or died_from_freeze


def _tick_enemy_freeze(enemy, messages):
    """Internal helper: count down freeze and apply slow on thaw."""
    died = False
    if enemy.get("frozen"):
        enemy["freeze_duration"] = enemy.get("freeze_duration", 1) - 1
        if enemy["freeze_duration"] <= 0:
            enemy["frozen"] = False
            enemy["slowed"] = True
            enemy.setdefault("active_debuffs", []).append({
                "type": "slow", "remaining": 1
            })
            messages.append(f"The {enemy['name']} thaws — but is still sluggish!")
    return messages, died


def tick_player_debuffs(player):
    """Tick poison/bleed/slow/weaken/silence/dread/curse debuffs on the player.

    Returns (messages, died).
    """
    messages = []
    if not player.get("active_debuffs"):
        return messages, False

    for debuff in player["active_debuffs"][:]:
        dtype = debuff["type"]

        if dtype == "poison":
            dmg = debuff["damage"]
            player["current_hp"] -= dmg
            messages.append(f"You suffer {dmg} poison damage!")
            debuff["remaining"] -= 1
            if debuff["remaining"] <= 0:
                player["active_debuffs"].remove(debuff)
                messages.append("The poison fades from your system.")

        elif dtype == "bleed":
            dmg = debuff["damage"]
            player["current_hp"] -= dmg
            messages.append(f"Your wounds bleed for {dmg} damage!")
            debuff["remaining"] -= 1
            if debuff["remaining"] <= 0:
                player["active_debuffs"].remove(debuff)
                messages.append("Your wounds finally clot.")

        elif dtype == "slow":
            debuff["remaining"] -= 1
            if debuff["remaining"] <= 0:
                player["active_debuffs"].remove(debuff)
                messages.append("You are no longer slowed.")

        elif dtype == "weaken":
            debuff["remaining"] -= 1
            if debuff["remaining"] <= 0:
                player["active_debuffs"].remove(debuff)
                player_name = player.get("name", "You")
                messages.append(f"Your strength returns — the weakening fades.")

        elif dtype == "silence":
            debuff["remaining"] -= 1
            if debuff["remaining"] <= 0:
                player["silenced"] = False
                player["active_debuffs"].remove(debuff)
                messages.append("You can reach your pack again — silence lifts.")

        elif dtype == "dread":
            debuff["remaining"] -= 1
            if debuff["remaining"] <= 0:
                player["dreaded"] = False
                player["active_debuffs"].remove(debuff)
                messages.append("The supernatural dread recedes from your mind.")

        elif dtype == "blind":
            debuff["remaining"] -= 1
            if debuff["remaining"] <= 0:
                player["blinded"] = False
                player["active_debuffs"].remove(debuff)
                messages.append("Your vision clears – the blindness fades.")

        elif dtype == "vulnerable":
            debuff["remaining"] -= 1
            if debuff["remaining"] <= 0:
                player["active_debuffs"].remove(debuff)
                messages.append("Your vulnerability fades — the rage subsides.")

        elif dtype == "healing_down":
            debuff["remaining"] -= 1
            if debuff["remaining"] <= 0:
                player["active_debuffs"].remove(debuff)
                messages.append("Your healing returns to normal.")

        elif dtype == "burn":
            dmg = debuff["damage"]
            tier = debuff.get("tier", 1)
            tier_name = BURN_TIERS.get(tier, BURN_TIERS[1])["name"]
            player["current_hp"] -= dmg
            messages.append(f"You suffer {dmg} {tier_name} damage!")
            debuff["remaining"] -= 1
            if debuff["remaining"] <= 0:
                player["active_debuffs"].remove(debuff)
                messages.append(f"The {tier_name} on you dies out.")

        elif dtype == "curse":
            # Indefinite — only removed by cure_curse()
            continue

        elif dtype == "void_touched":
            debuff["remaining"] -= 1
            if debuff["remaining"] <= 0:
                player["void_touched"] = False
                player["active_debuffs"].remove(debuff)
                messages.append("The void's grip on you releases.")

        elif dtype == "shock":
            dmg = debuff["damage"]
            player["current_hp"] -= dmg
            messages.append(f"Electricity courses through you — {dmg} thunder damage!")
            # 25% chance to stun (skip next action) on each tick
            if random.random() < 0.25:
                player["stunned"] = True
                player.setdefault("active_debuffs", []).append({
                    "type": "stun", "remaining": 1
                })
                messages.append("The shock paralyzes you — you lose your next action!")
            debuff["remaining"] -= 1
            if debuff["remaining"] <= 0:
                player["active_debuffs"].remove(debuff)
                messages.append("The sparks fade from your body.")

        elif dtype == "confusion":
            debuff["remaining"] -= 1
            if debuff["remaining"] <= 0:
                player["active_debuffs"].remove(debuff)
                messages.append("Your mind clears — the confusion lifts.")

    died = player["current_hp"] <= 0
    return messages, died


# ===========================================================================
# TICKING BUFFS
# ===========================================================================

def tick_player_buffs(player):
    """Tick HoT, stat buffs, and other timed buffs on the player dict.

    Fixed the double-decrement bug present in the original code.
    Returns a list of message strings.
    """
    messages = []
    if not player.get("active_buffs"):
        return messages

    for buff in player["active_buffs"][:]:
        btype = buff.get("type")

        if btype == "hot":
            old_hp = player["current_hp"]
            from combat.stat_milestones import get_wisdom_bonus
            heal = buff["value"] + get_wisdom_bonus(player)
            new_hp = min(old_hp + heal, player_max_hp(player))
            healed = new_hp - old_hp
            player["current_hp"] = new_hp
            if healed > 0:
                messages.append(f"You regenerate {healed} HP from your healing salve.")
            buff["remaining"] -= 1
            if buff["remaining"] <= 0:
                player["active_buffs"].remove(buff)
                messages.append("Your healing salve's effect has worn off.")

        elif btype in ("blessing", "well_rested", "floor_buff"):
            # Permanent / floor-based — never expires through round ticking
            continue

        elif btype == "divine_shield":
            buff["remaining"] -= 1
            if buff["remaining"] <= 0:
                player["active_buffs"].remove(buff)
                messages.append("Your divine shield fades.")

        elif btype == "barrier":
            buff["remaining"] -= 1
            if buff["remaining"] <= 0:
                player["active_buffs"].remove(buff)
                messages.append("Your barrier shimmers and fades.")
            elif buff.get("value", 0) > 0:
                messages.append(f"Barrier: {buff['value']} absorb remaining.")

        elif btype == "haste":
            buff["remaining"] -= 1
            if buff["remaining"] <= 0:
                player["active_buffs"].remove(buff)
                messages.append("Your movements return to normal — haste fades.")

        elif btype == "regen":
            old_hp = player["current_hp"]
            from combat.stat_milestones import get_wisdom_bonus
            heal = buff["value"] + get_wisdom_bonus(player)
            new_hp = min(old_hp + heal, player_max_hp(player))
            healed = new_hp - old_hp
            player["current_hp"] = new_hp
            if healed > 0:
                messages.append(f"Regeneration restores {healed} HP.")
            buff["remaining"] -= 1
            if buff["remaining"] <= 0:
                player["active_buffs"].remove(buff)
                messages.append("Your regeneration fades.")

        else:
            # Generic timed buff (stat boost, defense buff, etc.)
            buff["remaining"] -= 1
            if buff["remaining"] <= 0:
                player["active_buffs"].remove(buff)
                if "stat" in buff:
                    messages.append(f"Your {buff['stat']} buff wears off.")

    # Blank Canvas Shawl: Afterimage countdown
    from combat.weapon.blank_canvas_shawl import tick_afterimage
    messages.extend(tick_afterimage(player))

    # Palette's Brush: Palette heroine passives (Azure heal / Alabaster cleanse)
    from combat.weapon.palette_brush import tick_palette_brush_passives
    messages.extend(tick_palette_brush_passives(player))

    return messages


# ===========================================================================
# REMOVING EFFECTS  (triggered by items, abilities, scripted events)
# ===========================================================================

def cure_curse(player):
    """Remove a curse from the player. Returns 'cured' or 'not_cursed'."""
    if not player.get("cursed"):
        return "not_cursed"
    player["cursed"] = False
    player["active_debuffs"] = [
        d for d in player.get("active_debuffs", []) if d.get("type") != "curse"
    ]
    return "cured"


def cure_bleed(player):
    """Stop a bleed on the player. Returns 'cured' or 'not_bleeding'."""
    bleeding = any(d["type"] == "bleed" for d in player.get("active_debuffs", []))
    if not bleeding:
        return "not_bleeding"
    player["active_debuffs"] = [
        d for d in player.get("active_debuffs", []) if d.get("type") != "bleed"
    ]
    return "cured"


def cure_silence(player):
    """Lift silence from the player. Returns 'cured' or 'not_silenced'."""
    if not player.get("silenced"):
        return "not_silenced"
    player["silenced"] = False
    player["active_debuffs"] = [
        d for d in player.get("active_debuffs", []) if d.get("type") != "silence"
    ]
    return "cured"


def dispel_dread(player):
    """Dispel dread from the player. Returns 'dispelled' or 'not_dreaded'."""
    if not player.get("dreaded"):
        return "not_dreaded"
    player["dreaded"] = False
    player["active_debuffs"] = [
        d for d in player.get("active_debuffs", []) if d.get("type") != "dread"
    ]
    return "dispelled"


# ===========================================================================
# QUERY HELPERS  (read-only; used by combat to apply effect-based modifiers)
# ===========================================================================

def get_weaken_penalty(player):
    """Return the current Strength penalty from Weaken (0 if none)."""
    for d in player.get("active_debuffs", []):
        if d["type"] == "weaken":
            return d.get("penalty", 0)
    return 0


def is_silenced(player):
    """True if the player is currently silenced."""
    return bool(player.get("silenced"))


def is_dreaded(player):
    """True if the player is currently dreaded."""
    return bool(player.get("dreaded"))


def is_frozen(enemy):
    """True if the enemy is currently frozen solid."""
    return bool(enemy.get("frozen"))


# ===========================================================================
# STATUS DISPLAY  (for HUD / player info panels)
# ===========================================================================

def get_player_status_tags(player):
    """Return a list of short status strings for the player HUD.

    Example return: ['Poisoned', 'Weakened', 'Silenced']
    """
    tags = []
    type_labels = {
        "poison":  "Poisoned",
        "bleed":   "Bleeding",
        "slow":    "Slowed",
        "weaken":  "Weakened",
        "silence": "Silenced",
        "dread":   "Dreaded",
        "curse":   "Cursed",
        "blind":   "Blinded",
        "vulnerable": "Vulnerable",
        "shock":   "Shocked",
        "void_touched": "Void-Touched",
        "paint":   "Painted",
    }
    buff_labels = {
        "haste":   "Hasted",
        "regen":   "Regenerating",
        "barrier": "Barrier",
    }
    for d in player.get("active_debuffs", []):
        if d["type"] == "burn":
            label = get_burn_tier_name(d.get("tier", 1))
        else:
            label = type_labels.get(d["type"])
        if label and label not in tags:
            tags.append(label)
    # Buff labels
    for b in player.get("active_buffs", []):
        label = buff_labels.get(b.get("type"))
        if label and label not in tags:
            tags.append(label)
    # Momentum buff
    for b in player.get("active_buffs", []):
        if b.get("type") == "momentum":
            tags.append(f"Momentum({b['value']})")
    return tags


def format_player_status_line(player):
    """Return a compact status string for inline display, e.g. '[Poisoned, Bleeding]'."""
    tags = get_player_status_tags(player)
    return f"[{', '.join(tags)}]" if tags else ""


# ===========================================================================
# MOMENTUM — Chrysalis / Chronoweave Mantle buff
# ===========================================================================

def apply_momentum(target, stacks=1, cap=20):
    """Grant Momentum stacks — each stack gives +3% damage dealt.

    Permanent (remaining=-1) until manually cleared by clear_momentum().
    Used by Chrysalis (Present Aspect) and Chronoweave Mantle (player loot).

    Returns 'applied', 'reinforced', or 'capped'.
    """
    existing = next(
        (b for b in target.get("active_buffs", []) if b.get("type") == "momentum"),
        None
    )
    current = existing["value"] if existing else 0
    new_total = min(cap, current + stacks)
    if new_total == current and current >= cap:
        return "capped"
    if existing:
        existing["value"] = new_total
        return "reinforced"
    target.setdefault("active_buffs", []).append({
        "type": "momentum",
        "value": new_total,
        "remaining": -1,  # permanent
    })
    return "applied"


def clear_momentum(target):
    """Remove all Momentum stacks from target. Called on Aspect switch."""
    target["active_buffs"] = [
        b for b in target.get("active_buffs", []) if b.get("type") != "momentum"
    ]


def get_momentum_stacks(target):
    """Return current Momentum stack count (0 if none)."""
    for b in target.get("active_buffs", []):
        if b.get("type") == "momentum":
            return b.get("value", 0)
    return 0


# ===========================================================================
# DETONATE — Chrysalis burn/bleed burst mechanics
# ===========================================================================

def detonate_burn(target, all_party=None):
    """Remove burn from target, deal 3x its damage instantly, spread 1 burn to others.

    Args:
        target: dict with active_debuffs (player or enemy)
        all_party: optional list of all party members for flame spread

    Returns (damage_dealt, messages).
    If target has no burn, returns (0, []) — caller should use fallback.
    """
    messages = []
    for d in target.get("active_debuffs", [])[:]:
        if d["type"] == "burn":
            dmg = d["damage"] * 3
            target_name = target.get("name", "Target")
            # Apply damage
            if "current_hp" in target:
                target["current_hp"] = max(0, target["current_hp"] - dmg)
            else:
                target["hp"] = max(0, target["hp"] - dmg)
            messages.append(f"🔥 BURN DETONATION! {target_name} takes {dmg} fire damage!")
            target["active_debuffs"].remove(d)

            # Restore CON if burn was reducing it (enemy only)
            if "burn_original_con" in target:
                target["con_mod"] = target["burn_original_con"]
                del target["burn_original_con"]

            # Spread 1 burn to all OTHER party members
            if all_party:
                for other in all_party:
                    if other is not target:
                        hp_key = "current_hp" if "current_hp" in other else "hp"
                        if other.get(hp_key, 0) > 0:
                            apply_burn_to_player(other, damage=2, duration=3)
                            other_name = other.get("name", "Ally")
                            messages.append(f"  🔥 Flames spread! {other_name} is burned.")
            return dmg, messages
    return 0, messages


def detonate_bleed(target):
    """Remove bleed from target, deal 3x its damage instantly.

    Returns (damage_dealt, messages).
    Caller handles healing for Chrysalis.
    If target has no bleed, returns (0, []) — caller should use fallback.
    """
    messages = []
    for d in target.get("active_debuffs", [])[:]:
        if d["type"] == "bleed":
            dmg = d["damage"] * 3
            target_name = target.get("name", "Target")
            if "current_hp" in target:
                target["current_hp"] = max(0, target["current_hp"] - dmg)
            else:
                target["hp"] = max(0, target["hp"] - dmg)
            messages.append(f"🩸 BLEED DETONATION! {target_name} takes {dmg} damage!")
            target["active_debuffs"].remove(d)
            return dmg, messages
    return 0, messages