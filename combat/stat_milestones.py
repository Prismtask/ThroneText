# combat/stat_milestones.py – passive bonuses earned at every 5 points in a stat

"""
Stat Milestone Passive Bonuses
================================
Every 5 points in a base attribute grants a small permanent passive bonus.
These bonuses are calculated from the player's *base* attributes (the values
stored in player["attributes"]), not effective/temporary values.

Milestone thresholds: 5, 10, 15, 20, 25, 30 ...
"""

from resources.races_classes import ATTRIBUTES

MILESTONE_STEP = 5


def _get_milestone_count(base_value):
    """Return how many milestones have been reached for a given base stat value."""
    return max(0, base_value // MILESTONE_STEP)


# ── Strength ────────────────────────────────────────────────────────────────

def get_strength_bonus(player):
    """+1 flat damage per 5 Strength (applied to all attacks and skills)."""
    base_str = player.get("attributes", {}).get("Strength", 0)
    return _get_milestone_count(base_str)


# ── Constitution ────────────────────────────────────────────────────────────

def get_constitution_bonus(player):
    """-1 damage taken per 5 Constitution (flat reduction, min 0)."""
    base_con = player.get("attributes", {}).get("Constitution", 0)
    return _get_milestone_count(base_con)


# ── Dexterity ───────────────────────────────────────────────────────────────

def get_dexterity_bonus(player):
    """+1 to flee/initiative rolls per 5 Dexterity."""
    base_dex = player.get("attributes", {}).get("Dexterity", 0)
    return _get_milestone_count(base_dex)


# ── Wisdom ──────────────────────────────────────────────────────────────────

def get_wisdom_bonus(player):
    """+1 HP healed from all healing sources per 5 Wisdom."""
    base_wis = player.get("attributes", {}).get("Wisdom", 0)
    return _get_milestone_count(base_wis)


# ── Learning ────────────────────────────────────────────────────────────────

def get_learning_bonus(player):
    """+1% XP gain per 5 Learning. Returns a multiplier (e.g. 1.02 for 2 milestones)."""
    base_ler = player.get("attributes", {}).get("Learning", 0)
    milestones = _get_milestone_count(base_ler)
    return 1.0 + (milestones * 0.01)


# ── Charisma ────────────────────────────────────────────────────────────────

def get_charisma_bonus(player):
    """+2% capture success chance per 5 Charisma."""
    base_cha = player.get("attributes", {}).get("Charisma", 0)
    return _get_milestone_count(base_cha) * 2  # returns flat percentage points


# ── Aggregate helpers ───────────────────────────────────────────────────────

def format_milestone_label(entity, attr):
    """Return a short inline label for a single attribute's milestone bonus, or empty string."""
    count = _get_milestone_count(entity.get("attributes", {}).get(attr, 0))
    if count <= 0:
        return ""
    if attr == "Strength":
        return f"+{count} dmg"
    elif attr == "Constitution":
        return f"-{count} dmg taken"
    elif attr == "Dexterity":
        return f"+{count} init/flee"
    elif attr == "Wisdom":
        return f"+{count} heal"
    elif attr == "Learning":
        return f"+{count}% XP"
    elif attr == "Charisma":
        return f"+{count * 2}% capture"
    return ""


def get_stat_milestones(player):
    """Return a dict of all active milestone bonuses for the player."""
    return {
        "Strength": get_strength_bonus(player),
        "Constitution": get_constitution_bonus(player),
        "Dexterity": get_dexterity_bonus(player),
        "Wisdom": get_wisdom_bonus(player),
        "Learning": get_learning_bonus(player),
        "Charisma": get_charisma_bonus(player),
    }


def format_milestone_bonuses(player):
    """Return a formatted multi-line string showing all milestone bonuses."""
    bonuses = get_stat_milestones(player)
    lines = ["--- Stat Milestone Bonuses ---"]
    for attr in ATTRIBUTES:
        val = bonuses[attr]
        if val == 0:
            continue
        if attr == "Strength":
            lines.append(f"  Strength:    +{val} flat damage")
        elif attr == "Constitution":
            lines.append(f"  Constitution: -{val} damage taken")
        elif attr == "Dexterity":
            lines.append(f"  Dexterity:   +{val} initiative/flee")
        elif attr == "Wisdom":
            lines.append(f"  Wisdom:      +{val} HP from healing")
        elif attr == "Learning":
            lines.append(f"  Learning:    +{int((val - 1.0) * 100)}% XP gain")
        elif attr == "Charisma":
            lines.append(f"  Charisma:    +{val}% capture chance")
    if len(lines) == 1:
        return ""  # No bonuses yet
    return "\n".join(lines)


def check_milestone_notification(player, old_attributes):
    """Check if any attribute crossed a milestone threshold and return a message."""
    messages = []
    for attr in ATTRIBUTES:
        old_val = old_attributes.get(attr, 0)
        new_val = player.get("attributes", {}).get(attr, 0)
        old_milestone = old_val // MILESTONE_STEP
        new_milestone = new_val // MILESTONE_STEP
        if new_milestone > old_milestone:
            messages.append(f"🌟 {attr} reached milestone {new_milestone * MILESTONE_STEP}! Passive bonus increased!")
    return messages
