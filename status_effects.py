# status_effects.py
# Pure functions for applying, ticking, and cleaning up status effects.
# All functions return a list of message strings and mutate the entity dict in place.
# Import and call these in combat.py and superboss_combat.py instead of copy-pasting loops.

from character import player_max_hp


# ---------------------------------------------------------------------------
# APPLYING EFFECTS
# ---------------------------------------------------------------------------

def apply_poison(target, damage, duration):
    """Apply or refresh poison on a target (player or enemy dict).

    Returns 'applied' or 'refreshed'. Does NOT print – caller prints using
    the returned status so each combat file can word the message differently.
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


def apply_curse(target):
    """Apply a permanent curse debuff (remaining = -1 means indefinite).

    Returns 'applied' or 'already_cursed'.
    """
    if target.get("cursed"):
        return "already_cursed"
    target["cursed"] = True
    target.setdefault("active_debuffs", []).append(
        {"type": "curse", "remaining": -1}
    )
    return "applied"


# ---------------------------------------------------------------------------
# TICKING DEBUFFS  (called once per round for each entity that can be debuffed)
# ---------------------------------------------------------------------------

def tick_enemy_debuffs(enemy):
    """Tick dot/blind debuffs on an enemy dict.

    Mutates enemy["hp"] and enemy["blinded"] where appropriate.
    Returns (messages, died) where died=True if hp dropped to 0 or below.
    """
    messages = []
    if not enemy.get("active_debuffs"):
        return messages, False

    for debuff in enemy["active_debuffs"][:]:
        if debuff["type"] == "dot":
            dmg = debuff["damage"]
            enemy["hp"] -= dmg
            messages.append(f"The {enemy['name']} takes {dmg} status damage!")
            debuff["remaining"] -= 1
            if debuff["remaining"] <= 0:
                enemy["active_debuffs"].remove(debuff)

        elif debuff["type"] == "blind":
            debuff["remaining"] -= 1
            if debuff["remaining"] <= 0:
                enemy["blinded"] = False
                enemy["active_debuffs"].remove(debuff)
                messages.append(f"The {enemy['name']} recovers their vision.")

    died = enemy["hp"] <= 0
    if died:
        messages.append(f"The {enemy['name']} has succumbed to status damage!")
    return messages, died


def tick_player_debuffs(player):
    """Tick poison/slow/curse debuffs on the player dict.

    - poison  : deals damage and counts down; removed at 0.
    - slow    : counts down silently; removal message included.
    - curse   : remaining == -1 means indefinite – never ticked off here;
                use cure_curse() to remove it explicitly.

    Returns (messages, died).
    """
    messages = []
    if not player.get("active_debuffs"):
        return messages, False

    for debuff in player["active_debuffs"][:]:
        if debuff["type"] == "poison":
            dmg = debuff["damage"]
            player["current_hp"] -= dmg
            messages.append(f"You suffer {dmg} poison damage!")
            debuff["remaining"] -= 1
            if debuff["remaining"] <= 0:
                player["active_debuffs"].remove(debuff)
                messages.append("The poison fades from your system.")

        elif debuff["type"] == "slow":
            debuff["remaining"] -= 1
            if debuff["remaining"] <= 0:
                player["active_debuffs"].remove(debuff)
                messages.append("You are no longer slowed.")

        elif debuff["type"] == "curse":
            # Indefinite – only removed by cure_curse(); skip tick
            continue

    died = player["current_hp"] <= 0
    return messages, died


# ---------------------------------------------------------------------------
# TICKING BUFFS  (called once per round for each entity that can be buffed)
# ---------------------------------------------------------------------------

def tick_player_buffs(player):
    """Tick HoT, stat buffs, and other timed buffs on the player dict.

    Handles:
    - "hot"      : heals each round, then expires.
    - "blessing" : permanent, never ticked.
    - anything else with "remaining": counts down; prints expiry if it had a "stat".

    NOTE: The original code had a double-decrement bug for non-hot/non-blessing buffs
    (it decremented inside the hot block AND again in the outer loop). This function
    fixes that – each buff is decremented exactly once per call.

    Returns a list of message strings.
    """
    messages = []
    if not player.get("active_buffs"):
        return messages

    for buff in player["active_buffs"][:]:
        btype = buff.get("type")

        if btype == "hot":
            old_hp = player["current_hp"]
            heal = buff["value"]
            new_hp = min(old_hp + heal, player_max_hp(player))
            healed = new_hp - old_hp
            player["current_hp"] = new_hp
            if healed > 0:
                messages.append(f"You regenerate {healed} HP from your healing salve.")
            buff["remaining"] -= 1
            if buff["remaining"] <= 0:
                player["active_buffs"].remove(buff)
                messages.append("Your healing salve's effect has worn off.")

        elif btype == "blessing":
            # Permanent – never expires through ticking
            continue

        else:
            # Generic timed buff (stat boost, defense buff, etc.)
            buff["remaining"] -= 1
            if buff["remaining"] <= 0:
                player["active_buffs"].remove(buff)
                if "stat" in buff:
                    messages.append(f"Your {buff['stat']} buff wears off.")

    return messages


# ---------------------------------------------------------------------------
# REMOVING EFFECTS  (triggered by items, abilities, scripted events)
# ---------------------------------------------------------------------------

def cure_curse(player):
    """Remove a curse from the player.

    Returns 'cured' or 'not_cursed'.
    """
    if not player.get("cursed"):
        return "not_cursed"
    player["cursed"] = False
    player["active_debuffs"] = [
        d for d in player.get("active_debuffs", []) if d.get("type") != "curse"
    ]
    return "cured"