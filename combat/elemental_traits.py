# combat/elemental_traits.py
"""Elemental trait system — passive combat effects tied to weapon element.

Each element has a trait that triggers on-hit, on-kill, or conditionally.
Traits are per-weapon, determined by the weapon's ``primary_element`` field.
Rarity amplifies trait effects (higher rarity = stronger trait).
"""

import random
from combat.combat_io import c_print
from combat.status_effects import apply_burn
from character import player_max_hp

# ── Core Trait Definitions ────────────────────────────────────────────────────

ELEMENTAL_TRAITS = {
    "physical": {
        "name": "Sunder",
        "desc": "+{pct}% armor penetration on this attack",
        "on_hit_armor_pen": 0.15,  # base 15%
        "rarity_bonus": 0.0,       # static — no scaling
    },
    "fire": {
        "name": "Ignite",
        "desc": "Applies a burn tier based on rarity",
        "on_hit_burn_tier": 2,   # base tier: Burn (6/turn) at common
        "rarity_bonus": 1,       # +1 tier per rarity above common
    },
    "water": {
        "name": "Douse",
        "desc": "On kill: reduce {n} random skill cooldown(s) by 1",
        "on_kill_cd_reduce": 1,
        "rarity_bonus": 0,         # becomes 2 at epic+
    },
    "thunder": {
        "name": "Chain",
        "desc": "{pct}% chance: 40% splash damage to 1 adjacent enemy",
        "on_hit_chain_chance": 0.15,
        "on_hit_chain_pct": 0.40,
        "rarity_bonus": 0.05,      # +5% chance per tier
    },
    "wind": {
        "name": "Swift",
        "desc": "+{n} initiative for 1 turn after attacking (stacks 2×)",
        "on_hit_init_bonus": 2,
        "rarity_bonus": 1,         # +1 init per tier
    },
    "earth": {
        "name": "Bulwark",
        "desc": "+{pct}% damage reduction for 1 turn after attacking",
        "on_hit_def_bonus": 0.08,  # 8% DR
        "rarity_bonus": 0.02,      # +2% per tier
    },
    "light": {
        "name": "Purge",
        "desc": "On kill: remove {n} debuff(s) from self",
        "on_kill_cleanse": 1,
        "rarity_bonus": 0,         # becomes 2 at rare+
    },
    "dark": {
        "name": "Leech",
        "desc": "Heal for {pct}% of damage dealt",
        "on_hit_leech_pct": 0.08,
        "rarity_bonus": 0.02,      # +2% per tier
    },
    "magical": {
        "name": "Pierce",
        "desc": "Ignores {pct}% of target elemental resistance",
        "on_hit_res_ignore": 0.25,
        "rarity_bonus": 0.05,      # +5% per tier
    },
}

# ── Rarity Tier Lookup (for trait scaling) ────────────────────────────────────

RARITY_TIER = {"common": 0, "uncommon": 1, "rare": 2, "epic": 3, "legendary": 4}


# ── Helper Functions ──────────────────────────────────────────────────────────

def get_primary_element(weapon: dict) -> str | None:
    """Return the primary element of a weapon (explicit field), or None."""
    if weapon is None:
        return None
    return weapon.get("primary_element")


def get_trait_for_weapon(weapon: dict, rarity: str) -> dict | None:
    """Return the resolved trait dict for a weapon, with rarity bonuses applied.

    Args:
        weapon: The weapon dict (must have ``primary_element`` field).
        rarity: Rarity string (e.g. ``"rare"``).

    Returns:
        A dict with resolved trait values, or None if no trait applies.
    """
    element = get_primary_element(weapon)
    if element is None:
        return None
    trait = ELEMENTAL_TRAITS.get(element)
    if trait is None:
        return None

    tier = RARITY_TIER.get(rarity, 0)
    bonus = trait.get("rarity_bonus", 0)

    # Clone and apply scaling bonuses
    resolved = dict(trait)
    scalar_keys = (
        "on_hit_chain_chance", "on_hit_leech_pct",
        "on_hit_res_ignore", "on_hit_def_bonus", "on_hit_init_bonus",
    )
    for key in scalar_keys:
        if key in resolved:
            resolved[key] = resolved[key] + bonus * tier

    # Integer-scaling keys (tiers, etc.)
    int_keys = ("on_hit_burn_tier",)
    for key in int_keys:
        if key in resolved:
            resolved[key] = min(5, resolved[key] + bonus * tier)

    # Special non-linear cases
    if element == "water" and tier >= 3:   # epic+
        resolved["on_kill_cd_reduce"] = 2
    if element == "light" and tier >= 2:   # rare+
        resolved["on_kill_cleanse"] = 2

    return resolved


def apply_trait(trait: dict, player: dict, target: dict, enemies: list,
                damage: int):
    """Apply an elemental trait's effects after a successful hit.

    Called from the attack resolution path in ``player_actions.py``.

    Args:
        trait: Resolved trait dict from ``get_trait_for_weapon``.
        player: The attacker's dict.
        target: The defender's dict.
        enemies: List of all enemy dicts (for Chain splash).
        damage: Final damage dealt to the target.
    """
    # ── Fire: Ignite (Burn DoT) ──
    if "on_hit_burn_tier" in trait:
        burn_tier = trait["on_hit_burn_tier"]
        from combat.status_effects import BURN_TIERS
        tier_info = BURN_TIERS.get(burn_tier, BURN_TIERS[2])
        result = apply_burn(target, burn_tier, 3)
        if result == "applied":
            c_print(f"  🔥 Ignite! {target['name']} is {tier_info['name']}d ({tier_info['damage']}/turn, 3 turns).")
        elif result == "upgraded":
            c_print(f"  🔥 Ignite leaps to {tier_info['name']}! {target['name']} burns for {tier_info['damage']}/turn.")
        elif result == "intensified":
            burn_d = next((d for d in target.get("active_debuffs", []) if d["type"] == "burn"), None)
            new_tier = burn_d["tier"] if burn_d else burn_tier + 1
            new_info = BURN_TIERS.get(new_tier, BURN_TIERS[2])
            c_print(f"  🔥 The flames intensify to {new_info['name']}! {target['name']} burns for {new_info['damage']}/turn.")
        elif result == "refreshed":
            c_print(f"  🔥 Ignite refreshed! {target['name']} keeps burning.")

    # ── Thunder: Chain (splash to adjacent enemy) ──
    if "on_hit_chain_chance" in trait:
        if random.random() < trait["on_hit_chain_chance"]:
            others = [e for e in enemies
                      if e is not target and e.get("hp", 0) > 0]
            if others:
                splash_target = random.choice(others)
                splash_dmg = int(damage * trait.get("on_hit_chain_pct", 0.40))
                splash_target["hp"] = max(0, splash_target["hp"] - splash_dmg)
                c_print(f"  ⚡ Chain! {splash_dmg} splash damage to {splash_target['name']}.")

    # ── Dark: Leech (lifesteal) ──
    if "on_hit_leech_pct" in trait:
        heal = int(damage * trait["on_hit_leech_pct"])
        if heal > 0:
            max_hp = player_max_hp(player)
            old = player.get("current_hp", 0)
            player["current_hp"] = min(old + heal, max_hp)
            actual = player["current_hp"] - old
            if actual > 0:
                c_print(f"  🩸 Leech! You recover {actual} HP.")

    # ── Wind: Swift (initiative buff) ──
    if "on_hit_init_bonus" in trait:
        bonus = trait["on_hit_init_bonus"]
        player.setdefault("active_buffs", []).append({
            "type": "initiative",
            "value": bonus,
            "remaining": 1,
            "source": "wind_trait",
        })
        c_print(f"  💨 Swift! +{bonus} initiative for 1 turn.")

    # ── Earth: Bulwark (damage reduction) ──
    if "on_hit_def_bonus" in trait:
        pct = trait["on_hit_def_bonus"]
        player.setdefault("active_buffs", []).append({
            "type": "defense",
            "value": pct,
            "remaining": 1,
            "source": "earth_trait",
        })
        c_print(f"  🛡️ Bulwark! {int(pct*100)}% damage reduction for 1 turn.")


def apply_trait_pre_damage(trait: dict, target: dict) -> dict:
    """Apply pre-damage trait modifiers (Sunder, Pierce).

    Called BEFORE damage calculation.

    Returns a dict with keys that the damage calc should use:
        - ``armor_pen``: armor reduction factor (1.0 = no pen)
        - ``res_ignore``: resistance ignore factor (0.0 = no ignore)
    """
    result = {"armor_pen": 1.0, "res_ignore": 0.0}

    if trait and "on_hit_armor_pen" in trait:
        result["armor_pen"] = 1.0 - trait["on_hit_armor_pen"]

    if trait and "on_hit_res_ignore" in trait:
        result["res_ignore"] = trait["on_hit_res_ignore"]

    return result


def apply_trait_on_kill(trait: dict, player: dict, target: dict, enemies: list):
    """Apply on-kill trait effects (Douse, Purge).

    Called from the kill resolution path in ``player_actions.py``.

    Args:
        trait: Resolved trait dict from ``get_trait_for_weapon``.
        player: The attacker's dict.
        target: The defeated enemy dict.
        enemies: List of all enemy dicts.
    """
    # ── Water: Douse (reduce skill cooldowns on kill) ──
    if "on_kill_cd_reduce" in trait:
        n = trait["on_kill_cd_reduce"]
        cooldowns = player.get("skill_cooldowns", {})
        on_cd = [(sid, cd) for sid, cd in cooldowns.items() if cd > 0]
        if on_cd:
            # Shuffle and pick up to n skills
            random.shuffle(on_cd)
            reduced = 0
            for skill_id, _ in on_cd[:n]:
                cooldowns[skill_id] = max(0, cooldowns[skill_id] - 1)
                reduced += 1
            if reduced > 0:
                c_print(f"  💧 Douse! {reduced} skill cooldown(s) reduced by 1.")

    # ── Light: Purge (remove debuffs on kill) ──
    if "on_kill_cleanse" in trait:
        n = trait["on_kill_cleanse"]
        debuffs = player.get("active_debuffs", [])
        if debuffs:
            removed = 0
            for _ in range(min(n, len(debuffs))):
                if debuffs:
                    removed_debuff = random.choice(debuffs)
                    player["active_debuffs"].remove(removed_debuff)
                    removed += 1
            if removed > 0:
                c_print(f"  ✨ Purge! {removed} debuff(s) cleansed.")
