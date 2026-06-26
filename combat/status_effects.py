# status_effects.py
# Pure functions for applying, ticking, and cleaning up status effects.
# All functions return a list of message strings and mutate the entity dict in place.
# Import and call these in combat.py and superboss_combat.py instead of copy-pasting loops.

from character import player_max_hp


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

def apply_burn(enemy, damage, duration=3):
    existing = next((d for d in enemy.get("active_debuffs", []) if d["type"] == "burn"), None)
    if existing:
        existing["remaining"] = duration
        existing["damage"] = damage
        return "refreshed"
    # Store original CON before reducing
    enemy.setdefault("burn_original_con", enemy["con_mod"])
    enemy["con_mod"] = max(0, enemy["con_mod"] - 1)
    enemy.setdefault("active_debuffs", []).append(
        {"type": "burn", "damage": damage, "remaining": duration}
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


def apply_bleed(player, damage, duration=4):
    """Apply a Bleed wound to the player.

    Bleed deals damage each round.  Unlike poison it does NOT stack — a
    heavier bleed (higher damage) overwrites a lighter one.

    Returns 'applied', 'refreshed', or 'no_change' (existing bleed is worse).
    """
    existing = next(
        (d for d in player.get("active_debuffs", []) if d["type"] == "bleed"),
        None,
    )
    if existing:
        if damage > existing["damage"]:
            existing["damage"] = damage
            existing["remaining"] = duration
            return "refreshed"
        return "no_change"
    player.setdefault("active_debuffs", []).append({
        "type": "bleed",
        "damage": damage,
        "remaining": duration,
    })
    return "applied"


def apply_silence(player, duration=2):
    """Silence the player, preventing item use for N turns.

    Returns 'applied' or 'already_silenced'.
    """
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
    if player.get("dreaded"):
        return "already_dreaded"
    player["dreaded"] = True
    player.setdefault("active_debuffs", []).append({
        "type": "dread",
        "remaining": duration,
    })
    return "applied"


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
        elif debuff["type"] == "burn":
            dmg = debuff["damage"]
            enemy["hp"] -= dmg
            messages.append(f"The {enemy['name']} burns for {dmg} fire damage!")
            debuff["remaining"] -= 1
            if debuff["remaining"] <= 0:
        # Restore original CON
                if "burn_original_con" in enemy:
                    enemy["con_mod"] = enemy["burn_original_con"]
                    del enemy["burn_original_con"]
                enemy["active_debuffs"].remove(debuff)
                messages.append(f"The flames on {enemy['name']} die out.")

        elif debuff["type"] == "blind":
            debuff["remaining"] -= 1
            if debuff["remaining"] <= 0:
                enemy["blinded"] = False
                enemy["active_debuffs"].remove(debuff)
                messages.append(f"The {enemy['name']} recovers their vision.")

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
            enemy["slowed"] = True   # slow on thaw for 1 round
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

        elif dtype == "curse":
            # Indefinite — only removed by cure_curse()
            continue

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

        else:
            # Generic timed buff (stat boost, defense buff, etc.)
            buff["remaining"] -= 1
            if buff["remaining"] <= 0:
                player["active_buffs"].remove(buff)
                if "stat" in buff:
                    messages.append(f"Your {buff['stat']} buff wears off.")

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
    }
    for d in player.get("active_debuffs", []):
        label = type_labels.get(d["type"])
        if label and label not in tags:
            tags.append(label)
    return tags


def format_player_status_line(player):
    """Return a compact status string for inline display, e.g. '[Poisoned, Bleeding]'."""
    tags = get_player_status_tags(player)
    return f"[{', '.join(tags)}]" if tags else ""