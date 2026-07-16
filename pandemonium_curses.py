# pandemonium_curses.py — Floor curses & cumulative corruption for Pandemonium
"""
Pandemonium Curse System
─────────────────────────
Each floor in Pandemonium rolls a random curse that persists for the entire floor.
Curses scale with cumulative corruption, which increases every 10 floors.

Corruption Tiers:
  Tier 1 — Floors  1–10 — 1.0× base effect (mild)
  Tier 2 — Floors 11–20 — 1.5× base effect (moderate)
  Tier 3 — Floors 21–30 — 2.0× base effect (strong)
  Tier 4 — Floors 31–40 — 2.5× base effect (severe)

Curse effect types:
  damage_taken      — Player/allies take more damage from enemies
  damage_dealt      — Player/allies deal less damage to enemies
  room_damage       — Flat HP loss when entering each room
  healing_reduction — Post-combat healing is reduced
  gold_reduction    — Gold drops are reduced
  no_flee           — Fleeing is disabled
  stat_check_wis_dc — WIS-based stat check DCs are increased
  stat_check_dex_dc — DEX-based stat check DCs are increased
  enemy_speed       — Enemy initiative rolls get a bonus
  skip_chance       — Small chance for player to lose a turn
  cooldown_increase — Skill cooldowns are extended
"""

import random

# ═══════════════════════════════════════════════════════════════════════════════
# CURSE DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════════

PANDEMONIUM_CURSES = [
    {
        "key": "crystal_fragility",
        "name": "Crystal Fragility",
        "desc": "The crystalline walls pulse with malignant energy, weakening your defenses.",
        "desc_full": "You and your allies take {pct}% more damage from all sources.",
        "effect": "damage_taken",
        "base_value": 0.20,
        "icon": "💔",
    },
    {
        "key": "weakened_resolve",
        "name": "Weakened Resolve",
        "desc": "A psychic weight presses on your mind, deadening your strikes.",
        "desc_full": "You and your allies deal {pct}% less damage with all attacks.",
        "effect": "damage_dealt",
        "base_value": 0.15,
        "icon": "🔻",
    },
    {
        "key": "sapping_aura",
        "name": "Sapping Aura",
        "desc": "The air itself drains your vitality as you move through the halls.",
        "desc_full": "Lose {val} HP at the start of every room.",
        "effect": "room_damage",
        "base_value": 3,
        "icon": "💀",
    },
    {
        "key": "blighted_recovery",
        "name": "Blighted Recovery",
        "desc": "Corruption in the air stifles your body's natural healing.",
        "desc_full": "All sources of healing are reduced by {pct}%.",
        "effect": "healing_reduction",
        "base_value": 0.40,
        "icon": "🩸",
    },
    {
        "key": "corrupted_loot",
        "name": "Corrupted Loot",
        "desc": "Pandemonium's chaos twists material wealth into worthless shards.",
        "desc_full": "Gold drops are reduced by {pct}%.",
        "effect": "gold_reduction",
        "base_value": 0.30,
        "icon": "🪙",
    },
    {
        "key": "crystalline_prison",
        "name": "Crystalline Prison",
        "desc": "The dungeon walls seal behind you — there is no way back.",
        "desc_full": "Fleeing is impossible. You must clear this floor or die trying.",
        "effect": "no_flee",
        "base_value": 1,
        "icon": "🔒",
    },
    {
        "key": "mirrored_mind",
        "name": "Mirrored Mind",
        "desc": "A thousand reflections of your own fears assault your thoughts.",
        "desc_full": "Wisdom-based stat checks have their DC increased by {val}.",
        "effect": "stat_check_wis_dc",
        "base_value": 3,
        "icon": "🪞",
    },
    {
        "key": "unstable_ground",
        "name": "Unstable Ground",
        "desc": "The crystalline floor shifts and cracks unpredictably beneath you.",
        "desc_full": "Dexterity-based stat checks have their DC increased by {val}.",
        "effect": "stat_check_dex_dc",
        "base_value": 3,
        "icon": "💥",
    },
    {
        "key": "time_dilation",
        "name": "Time Dilation",
        "desc": "Time flows erratically — enemies move with unnatural swiftness.",
        "desc_full": "Enemies gain +{val} bonus to their initiative rolls.",
        "effect": "enemy_speed",
        "base_value": 2,
        "icon": "⏳",
    },
    {
        "key": "echoing_madness",
        "name": "Echoing Madness",
        "desc": "Whispers of Pandemonium's countless fallen distract and confuse you.",
        "desc_full": "{pct}% chance to lose your turn each round.",
        "effect": "skip_chance",
        "base_value": 0.08,
        "icon": "🌀",
    },
    {
        "key": "mana_drain",
        "name": "Mana Drain",
        "desc": "The ambient chaos interferes with magical and martial energies alike.",
        "desc_full": "All skill cooldowns are increased by {val} turn(s).",
        "effect": "cooldown_increase",
        "base_value": 1,
        "icon": "🔮",
    },
]

# ═══════════════════════════════════════════════════════════════════════════════
# CORRUPTION TIERS
# ═══════════════════════════════════════════════════════════════════════════════

CORRUPTION_TIERS = [
    # (floor_min, floor_max, multiplier, tier_name)
    (1, 10, 1.0, "Whispering Corruption"),
    (11, 20, 1.5, "Seething Corruption"),
    (21, 30, 2.0, "Howling Corruption"),
    (31, 40, 2.5, "Apocalyptic Corruption"),
]


def get_corruption_tier(floor):
    """Return (multiplier, tier_name) for the given floor."""
    for f_min, f_max, mult, name in CORRUPTION_TIERS:
        if f_min <= floor <= f_max:
            return mult, name
    # Fallback for floors beyond 40
    return 2.5, "Apocalyptic Corruption"


def roll_floor_curse(floor, previous_curse_key=None):
    """Roll a random curse for the current floor.
    
    Args:
        floor: Current floor number (used for corruption scaling)
        previous_curse_key: Key of the last floor's curse to avoid repeats
    
    Returns:
        dict with keys: key, name, desc_full, effect, value, tier_name, icon
    """
    mult, tier_name = get_corruption_tier(floor)
    
    # Build pool, excluding the previous floor's curse
    pool = PANDEMONIUM_CURSES[:]
    if previous_curse_key:
        pool = [c for c in pool if c["key"] != previous_curse_key]
    
    curse_def = random.choice(pool)
    
    # Scale the value
    scaled_value = curse_def["base_value"] * mult
    
    # Format description with scaled values
    if curse_def["effect"] in ("damage_taken", "damage_dealt", "healing_reduction", "gold_reduction", "skip_chance"):
        desc_full = curse_def["desc_full"].format(pct=int(scaled_value * 100))
    else:
        desc_full = curse_def["desc_full"].format(val=int(scaled_value))
    
    return {
        "key": curse_def["key"],
        "name": curse_def["name"],
        "desc_full": desc_full,
        "effect": curse_def["effect"],
        "value": scaled_value,
        "tier_name": tier_name,
        "tier_mult": mult,
        "icon": curse_def.get("icon", "☠️"),
    }


def apply_curse_on_floor_start(player, floor):
    """Roll and apply a Pandemonium floor curse. Call at the start of each floor.
    
    Curses are persisted per floor in player['pandemonium_floor_curses'].
    If the player already has a curse for this floor (e.g., after leaving
    and re-entering), the same curse is reused — preventing the player from
    re-rolling for a weaker curse by leaving and coming back.
    """
    # ── Check for existing curse on this floor (prevents leave/re-enter abuse) ─
    floor_curses = player.setdefault("pandemonium_floor_curses", {})
    floor_key = str(floor)
    if floor_key in floor_curses:
        # Re-use the existing curse for this floor
        curse = floor_curses[floor_key]
        player["pandemonium_curse"] = curse
    else:
        previous_key = None
        prev = player.get("pandemonium_curse")
        if prev:
            previous_key = prev.get("key")
        
        curse = roll_floor_curse(floor, previous_curse_key=previous_key)
        
        # ── Arcane Warding (from Isle of Glass Arcane Tower) ─────────────────
        if player.get("arcane_warding_active"):
            reduction_pct = player.get("arcane_warding_pct", 0.35)
            original_value = curse["value"]
            curse["value"] = curse["value"] * (1.0 - reduction_pct)
            curse["warded"] = True
            curse["ward_reduction"] = reduction_pct
            curse["ward_original_value"] = original_value
            
            # Re-format description with reduced values
            if curse["effect"] in ("damage_taken", "damage_dealt", "healing_reduction", "gold_reduction", "skip_chance"):
                curse["desc_full"] = curse["desc_full"].format(pct=int(curse["value"] * 100))
            else:
                curse["desc_full"] = curse["desc_full"].format(val=int(curse["value"]))
            
            # Consume the ward
            del player["arcane_warding_active"]
            del player["arcane_warding_pct"]
        
        # Persist the curse for this floor
        floor_curses[floor_key] = curse
        player["pandemonium_curse"] = curse
    
    # Build display message
    lines = []
    lines.append("")
    lines.append("╔" + "═" * 58 + "╗")
    if curse.get("warded"):
        lines.append(f"║  PANDEMONIUM CURSE — Floor {floor} — {curse['tier_name']}  [WARDED]".ljust(59) + "║")
    else:
        lines.append(f"║  PANDEMONIUM CURSE — Floor {floor} — {curse['tier_name']}".ljust(59) + "║")
    lines.append("╠" + "═" * 58 + "╣")
    lines.append(f"║  {curse['icon']}  {curse['name']}".ljust(59) + "║")
    if curse.get("warded"):
        pct = int(curse.get("ward_reduction", 0) * 100)
        orig = curse.get("ward_original_value", 0)
        lines.append(f"║  Arcane Ward reduced effect by {pct}%! (was {orig:.1f})".ljust(59) + "║")
    lines.append("║" + " " * 58 + "║")
    # Wrap description
    desc = curse["desc_full"]
    while len(desc) > 54:
        split = desc.rfind(" ", 0, 54)
        if split == -1:
            split = 54
        lines.append(f"║  {desc[:split]}".ljust(59) + "║")
        desc = desc[split:].strip()
    if desc:
        lines.append(f"║  {desc}".ljust(59) + "║")
    lines.append("╚" + "═" * 58 + "╝")
    
    return "\n".join(lines)


def clear_curse(player):
    """Remove the Pandemonium curse and all persisted floor curses from the player."""
    player.pop("pandemonium_curse", None)
    player.pop("pandemonium_floor_curses", None)


def format_curse_header(player):
    """Return a compact boxed header showing the active curse for room display.
    
    Returns a multi-line string with the curse name, icon, and effect,
    or an empty string if no curse is active.
    """
    curse = get_curse(player)
    if not curse:
        return ""
    
    floor = player.get("floor", "?")
    lines = []
    lines.append("╔" + "═" * 58 + "╗")
    header = f"  PANDEMONIUM CURSE — Floor {floor} — {curse.get('tier_name', '')}"
    lines.append("║" + header.ljust(58) + "║")
    lines.append("╠" + "═" * 58 + "╣")
    lines.append(f"║  {curse.get('icon', '☠️')}  {curse.get('name', 'Unknown Curse')}".ljust(59) + "║")
    lines.append("║" + " " * 58 + "║")
    desc = curse.get("desc_full", "")
    while len(desc) > 54:
        split = desc.rfind(" ", 0, 54)
        if split == -1:
            split = 54
        lines.append(f"║  {desc[:split]}".ljust(59) + "║")
        desc = desc[split:].strip()
    if desc:
        lines.append(f"║  {desc}".ljust(59) + "║")
    lines.append("╚" + "═" * 58 + "╝")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# CURSE EFFECT APPLICATION FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def get_curse(player):
    """Get the current curse dict, or None."""
    return player.get("pandemonium_curse")


def get_curse_value(player, effect_type):
    """Get the scaled value for a specific curse effect, or 0/None if not active."""
    curse = get_curse(player)
    if curse and curse.get("effect") == effect_type:
        return curse.get("value", 0)
    return 0


def apply_damage_taken_multiplier(player, damage):
    """Increase damage the player takes (Crystal Fragility). Returns modified damage."""
    mult = get_curse_value(player, "damage_taken")
    if mult > 0:
        return int(damage * (1 + mult))
    return damage


def apply_damage_dealt_multiplier(player, damage):
    """Decrease damage the player deals (Weakened Resolve). Returns modified damage."""
    mult = get_curse_value(player, "damage_dealt")
    if mult > 0:
        return max(1, int(damage * (1 - mult)))
    return damage


def apply_room_entry_damage(player):
    """Apply Sapping Aura damage on room entry. Returns damage taken, or 0."""
    dmg = get_curse_value(player, "room_damage")
    if dmg > 0:
        dmg = int(dmg)
        player["current_hp"] = max(1, player["current_hp"] - dmg)
        # Also damage allies
        for ally in player.get("allies", []):
            if ally.get("current_hp", 0) > 0:
                ally["current_hp"] = max(1, ally["current_hp"] - dmg)
        return dmg
    return 0


def apply_healing_reduction(player, heal_amount):
    """Reduce healing received (Blighted Recovery). Returns modified heal amount."""
    mult = get_curse_value(player, "healing_reduction")
    if mult > 0:
        return max(1, int(heal_amount * (1 - mult)))
    return heal_amount


def apply_gold_reduction(player, gold_amount):
    """Reduce gold drops (Corrupted Loot). Returns modified gold amount."""
    mult = get_curse_value(player, "gold_reduction")
    if mult > 0:
        return max(1, int(gold_amount * (1 - mult)))
    return gold_amount


def is_flee_blocked(player):
    """Check if fleeing is blocked (Crystalline Prison)."""
    return get_curse_value(player, "no_flee") > 0


def get_stat_check_dc_modifier(player, stat_name):
    """Get DC modifier for stat checks (Mirrored Mind / Unstable Ground)."""
    stat_lower = stat_name.lower()
    if stat_lower.startswith("wis"):
        return int(get_curse_value(player, "stat_check_wis_dc"))
    elif stat_lower.startswith("dex"):
        return int(get_curse_value(player, "stat_check_dex_dc"))
    return 0


def get_enemy_initiative_bonus(player):
    """Get enemy initiative bonus (Time Dilation)."""
    return int(get_curse_value(player, "enemy_speed"))


def roll_skip_turn(player):
    """Check if player should skip their turn (Echoing Madness). Returns True if skip."""
    chance = get_curse_value(player, "skip_chance")
    if chance > 0 and random.random() < chance:
        return True
    return False


def get_cooldown_increase(player):
    """Get additional cooldown turns (Mana Drain)."""
    return int(get_curse_value(player, "cooldown_increase"))


def format_active_curse_line(player):
    """Return a one-line summary of the active curse, or empty string."""
    curse = get_curse(player)
    if not curse:
        return ""
    return f"  {curse['icon']}  {curse['name']} [{curse['tier_name']}] — {curse['desc_full']}"
