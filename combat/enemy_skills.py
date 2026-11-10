"""Generic ability kits and turn AI for non-superboss enemies.

Regular enemies used to only make basic attacks (plus their racial on-hit
procs). This module gives them a small, readable action menu:

    basic attack | single-target skill | AoE skill | heal | AoE heal

Kits are derived from the enemy's race and level. Support roles are added by
name keywords (Shaman / Priest / Witch / Oracle / Alchemist ...), so a
"Goblin Shaman" mends its allies while a "Goblin Knifer" sticks to blades.
Designers can override a single enemy's kit with an ``abilities:`` list in the
enemy YAML — see ``docs/enemy_ai_behaviors_design.md`` for the schema.

Deliberately untouched:
  * superbosses (they keep their scripted loops in ``combat/superboss_common``),
  * Wonderland floor bosses (``combat/wl_floor_bosses.py`` owns their AI),
  * hallucinations / dummies / any enemy with ``round_hook`` or
    ``ai_disabled`` set.

Every offensive action funnels through :func:`combat.enemy_ai.enemy_attack`,
so armor, dodge (single-target only), elemental resistance, wedding gear,
barriers, reflect, Tarnished Jade and every other defensive hook keep working.
"""
from __future__ import annotations

import random

from combat.combat_io import c_print
from combat.enemy_ai import begin_enemy_turn, enemy_attack
from resources.enemies import ENEMIES


# ── Tunables ────────────────────────────────────────────────────────────────

SELF_HEAL_CHANCE = 0.90
ALLY_HEAL_CHANCE = 0.60
AOE_HEAL_CHANCE = 0.55
AOE_HEAL_MIN_WOUNDED = 2
AOE_MIN_TARGETS = 2

# Roles: supporters prioritise healing; attackers prioritise damage.
ROLE_ATTACKER = "attacker"
ROLE_SUPPORTER = "supporter"
ROLE_VALUES = (ROLE_ATTACKER, ROLE_SUPPORTER)

# Supporters are not secret damage dealers — they fall back to basics unless
# their kit has a cheap spell, and only use damage AoE occasionally.
SUPPORTER_SKILL_MULT = 0.55
SUPPORTER_AOE_MULT = 0.25


# ── Level-based behaviour tiers ─────────────────────────────────────────────
# Enemies do not start knowing every trick. Instinctive enemies (level 1-4)
# only basic attack and heal; damage skills unlock at level 5, AoE at level
# 10, and higher tiers become progressively more deliberate. The AI never
# chooses which party member to hit — that stays with the engine's normal
# weighted targeting, so it can't focus-fire the weakest actor.

AI_TIERS = (
    {
        "name": "Instinctive", "min_level": 1,
        "skill_mult": 0.0, "aoe_mult": 0.0,
        "party_bonus": 0.0, "wounded_party_bonus": 0.0,
        "aoe_heal_bonus": 0.0, "ally_heal_bonus": 0.0,
        "self_heal_threshold": 0.35, "wounded_threshold": 0.60,
        "smart_heal": False,
    },
    {
        "name": "Trained", "min_level": 5,
        "skill_mult": 0.50, "aoe_mult": 0.0,
        "party_bonus": 0.0, "wounded_party_bonus": 0.0,
        "aoe_heal_bonus": 0.0, "ally_heal_bonus": 0.05,
        "self_heal_threshold": 0.38, "wounded_threshold": 0.62,
        "smart_heal": False,
    },
    {
        "name": "Coordinated", "min_level": 10,
        "skill_mult": 0.85, "aoe_mult": 0.55,
        "party_bonus": 0.05, "wounded_party_bonus": 0.0,
        "aoe_heal_bonus": 0.05, "ally_heal_bonus": 0.05,
        "self_heal_threshold": 0.40, "wounded_threshold": 0.65,
        "smart_heal": True,
    },
    {
        "name": "Tactical", "min_level": 20,
        "skill_mult": 1.0, "aoe_mult": 0.85,
        "party_bonus": 0.07, "wounded_party_bonus": 0.08,
        "aoe_heal_bonus": 0.10, "ally_heal_bonus": 0.08,
        "self_heal_threshold": 0.43, "wounded_threshold": 0.70,
        "smart_heal": True,
    },
    {
        "name": "Calculating", "min_level": 35,
        "skill_mult": 1.15, "aoe_mult": 1.10,
        "party_bonus": 0.10, "wounded_party_bonus": 0.12,
        "aoe_heal_bonus": 0.15, "ally_heal_bonus": 0.10,
        "self_heal_threshold": 0.45, "wounded_threshold": 0.75,
        "smart_heal": True,
    },
)


def get_ai_tier(level):
    """Return the behaviour tier for an enemy level."""
    try:
        level = int(level)
    except (TypeError, ValueError):
        level = 1
    tier = AI_TIERS[0]
    for candidate in AI_TIERS:
        if level >= candidate["min_level"]:
            tier = candidate
        else:
            break
    return tier


# ── Action builders ─────────────────────────────────────────────────────────

def _action(action_id, name, power=0.0, cooldown=3, min_level=1, element=None,
            chance=0.45, status=None, heal_pct=0.18, drain_pct=0.0):
    return {
        "id": action_id,
        "name": name,
        "power": power,
        "cooldown": cooldown,
        "min_level": min_level,
        "element": element,
        "chance": chance,
        "status": status,
        "heal_pct": heal_pct,
        "drain_pct": drain_pct,
    }


def _support_heal():
    return _action("mend_wounds", "Mend Wounds", cooldown=4, min_level=1,
                   heal_pct=0.20)


def _support_aoe_heal():
    return _action("soothing_chant", "Soothing Chant", cooldown=5, min_level=3,
                   heal_pct=0.12)


# ── Race kits ───────────────────────────────────────────────────────────────
# Per-action ``min_level`` is the kit-level gate. The AI tier gate also
# applies: no damage skills below level 5, no AoE below level 10. Low-level
# encounters therefore stay readable even though the kit tables list early
# skill unlocks for explicit YAML kits.

RACE_KITS = {
    "Human": {
        "skill": _action("power_strike", "Power Strike", 1.35, 3, 3,
                         element="physical"),
        "aoe": _action("whirlwind_slash", "Whirlwind Slash", 0.75, 5, 8,
                       element="physical", chance=0.30),
    },
    "Goblin": {
        "skill": _action("cheap_shot", "Cheap Shot", 1.30, 3, 2,
                         element="physical", chance=0.50,
                         status={"type": "bleed", "chance": 0.35, "duration": 3}),
        "aoe": _action("firebomb", "Firebomb", 0.70, 5, 7, element="fire",
                       chance=0.30,
                       status={"type": "burn", "chance": 0.35, "duration": 3,
                               "tier": 1}),
    },
    "Orc": {
        "skill": _action("brutal_smash", "Brutal Smash", 1.40, 3, 3,
                         element="physical", chance=0.50,
                         status={"type": "bleed", "chance": 0.40, "duration": 3}),
        "aoe": _action("cleave", "Cleave", 0.80, 5, 7, element="physical",
                       chance=0.32),
    },
    "Undead": {
        "skill": _action("grave_touch", "Grave Touch", 1.30, 3, 2,
                         element="dark", chance=0.45,
                         status={"type": "weaken", "chance": 0.35,
                                 "duration": 3, "penalty_pct": 0.20}),
        "aoe": _action("wail_of_the_dead", "Wail of the Dead", 0.70, 5, 7,
                       element="dark", chance=0.30,
                       status={"type": "dread", "chance": 0.30, "duration": 2}),
    },
    "Beast": {
        "skill": _action("feral_pounce", "Feral Pounce", 1.35, 3, 2,
                         element="physical", chance=0.50,
                         status={"type": "bleed", "chance": 0.45, "duration": 3}),
        "aoe": _action("howling_frenzy", "Howling Frenzy", 0.75, 5, 7,
                       element="physical", chance=0.30),
    },
    "Demon": {
        "skill": _action("hellfire_bolt", "Hellfire Bolt", 1.40, 3, 2,
                         element="fire", chance=0.50,
                         status={"type": "burn", "chance": 0.40, "duration": 3,
                                 "tier": 1}),
        "aoe": _action("infernal_conflagration", "Infernal Conflagration", 0.75,
                       5, 7, element="fire", chance=0.32,
                       status={"type": "burn", "chance": 0.30, "duration": 2,
                               "tier": 1}),
    },
    "Construct": {
        "skill": _action("gear_grind", "Gear Grind", 1.30, 3, 2,
                         element="earth", chance=0.45),
        "aoe": _action("steam_burst", "Steam Burst", 0.70, 5, 7,
                       element="fire", chance=0.30,
                       status={"type": "blind", "chance": 0.30, "duration": 2}),
    },
    "Dragonkin": {
        "skill": _action("rending_claw", "Rending Claw", 1.35, 3, 2,
                         element="physical", chance=0.48),
        "aoe": _action("breath_weapon", "Breath Weapon", 0.80, 5, 7,
                       element="fire", chance=0.35,
                       status={"type": "burn", "chance": 0.45, "duration": 3,
                               "tier": 2}),
    },
    "Fey": {
        "skill": _action("fey_hex", "Fey Hex", 1.25, 3, 2, element="light",
                         chance=0.45,
                         status={"type": "silence", "chance": 0.30,
                                 "duration": 2}),
        "aoe": _action("pixie_dust_storm", "Pixie Dust Storm", 0.70, 5, 8,
                       element="light", chance=0.30,
                       status={"type": "blind", "chance": 0.35, "duration": 2}),
    },
    "Elemental": {
        "skill": _action("elemental_surge", "Elemental Surge", 1.35, 3, 2,
                         element="auto", chance=0.48),
        "aoe": _action("elemental_burst", "Elemental Burst", 0.75, 5, 7,
                       element="auto", chance=0.32),
    },
    "Giant": {
        "skill": _action("crushing_blow", "Crushing Blow", 1.45, 3, 3,
                         element="earth", chance=0.50,
                         status={"type": "weaken", "chance": 0.35,
                                 "duration": 2, "penalty_pct": 0.25}),
        "aoe": _action("ground_quake", "Ground Quake", 0.80, 5, 6,
                       element="earth", chance=0.32,
                       status={"type": "slow", "chance": 0.30, "duration": 2}),
    },
    "Vampire": {
        "skill": _action("blood_drain", "Blood Drain", 1.30, 3, 2,
                         element="dark", chance=0.48,
                         drain_pct=0.30,
                         status={"type": "weaken", "chance": 0.30,
                                 "duration": 2, "penalty_pct": 0.20}),
        "aoe": _action("crimson_mist", "Crimson Mist", 0.65, 5, 8,
                       element="dark", chance=0.28,
                       status={"type": "weaken", "chance": 0.30,
                               "duration": 2, "penalty_pct": 0.15}),
    },
    "Lizardfolk": {
        "skill": _action("venom_fang", "Venom Fang", 1.30, 3, 2,
                         element="water", chance=0.48,
                         status={"type": "poison", "chance": 0.40,
                                 "duration": 3}),
        "aoe": _action("caustic_spray", "Caustic Spray", 0.70, 5, 7,
                       element="water", chance=0.30,
                       status={"type": "poison", "chance": 0.35,
                               "duration": 3}),
    },
    "Gnome": {
        "skill": _action("arcane_zap", "Arcane Zap", 1.35, 3, 2,
                         element="thunder", chance=0.48,
                         status={"type": "shock", "chance": 0.30,
                                 "duration": 2}),
        "aoe": _action("chain_lightning", "Chain Lightning", 0.75, 5, 7,
                       element="thunder", chance=0.32,
                       status={"type": "shock", "chance": 0.30,
                               "duration": 2}),
    },
    "Shadow": {
        "skill": _action("umbral_strike", "Umbral Strike", 1.35, 3, 2,
                         element="dark", chance=0.48,
                         status={"type": "blind", "chance": 0.30,
                                 "duration": 2}),
        "aoe": _action("shadow_sweep", "Shadow Sweep", 0.70, 5, 7,
                       element="dark", chance=0.30),
    },
    "Clockwork": {
        "skill": _action("piston_fist", "Piston Fist", 1.35, 3, 2,
                         element="thunder", chance=0.48),
        "aoe": _action("overload_pulse", "Overload Pulse", 0.75, 5, 7,
                       element="thunder", chance=0.32,
                       status={"type": "shock", "chance": 0.35,
                               "duration": 2}),
    },
    "Abomination": {
        "skill": _action("corrosive_claw", "Corrosive Claw", 1.35, 3, 2,
                         element="dark", chance=0.48,
                         status={"type": "weaken", "chance": 0.35,
                                 "duration": 3, "penalty_pct": 0.25}),
        "aoe": _action("flesh_rot_spray", "Flesh Rot Spray", 0.70, 5, 7,
                       element="dark", chance=0.30,
                       status={"type": "poison", "chance": 0.35,
                               "duration": 3}),
    },
    "Storybook": {
        "skill": _action("narrative_slash", "Narrative Slash", 1.30, 3, 2,
                         element="light", chance=0.45,
                         status={"type": "confusion", "chance": 0.25,
                                 "duration": 2}),
        "aoe": _action("plot_twist", "Plot Twist", 0.70, 5, 8,
                       element="light", chance=0.30,
                       status={"type": "confusion", "chance": 0.30,
                               "duration": 2}),
    },
    "Angel": {
        "skill": _action("radiant_lance", "Radiant Lance", 1.40, 3, 2,
                         element="light", chance=0.50,
                         status={"type": "blind", "chance": 0.30,
                                 "duration": 2}),
        "aoe": _action("choir_of_judgment", "Choir of Judgment", 0.75, 5, 7,
                       element="light", chance=0.32),
        "heal": _action("radiant_mend", "Radiant Mend", cooldown=4, min_level=1,
                        heal_pct=0.22),
        "aoe_heal": _action("choir_of_restoration", "Choir of Restoration",
                            cooldown=5, min_level=3, heal_pct=0.14),
    },
}


# Support roles are inferred from names so existing YAML does not need edits.
_HEAL_KEYWORDS = (
    "shaman", "priest", "priestess", "healer", "witch", "cultist", "acolyte",
    "oracle", "druid", "cleric", "medic", "mender", "alchemist", "potion",
)
_AOE_HEAL_KEYWORDS = (
    "high priest", "priest", "priestess", "oracle", "druid", "cleric",
    "shaman", "matriarch",
)


def get_enemy_role(entity):
    """Resolve an enemy's combat role: ``attacker`` or ``supporter``.

    Priority:
      1. Explicit YAML ``role:`` on the template.
      2. An explicit ``abilities:`` list — heal actions imply supporter,
         otherwise the designer made a damage kit.
      3. Name keywords (Shaman / Priest / Witch / Oracle / Alchemist ...).
      4. Angel race (its racial kit includes heals).
      5. Attacker by default.

    Used by both the turn AI and dungeon spawn composition, so the same
    template always agrees with itself.
    """
    if not isinstance(entity, dict):
        return ROLE_ATTACKER

    explicit = str(entity.get("role") or "").strip().lower()
    if explicit in ROLE_VALUES:
        return explicit

    raw = entity.get("abilities")
    if isinstance(raw, list) and raw:
        for entry in raw:
            if not isinstance(entry, dict):
                continue
            if str(entry.get("type", "")).lower() in ("heal", "aoe_heal"):
                return ROLE_SUPPORTER
        return ROLE_ATTACKER

    name = str(entity.get("name", "")).lower()
    if any(k in name for k in _HEAL_KEYWORDS):
        return ROLE_SUPPORTER
    if any(k in name for k in _AOE_HEAL_KEYWORDS):
        return ROLE_SUPPORTER
    if str(entity.get("race", "")) == "Angel":
        return ROLE_SUPPORTER
    return ROLE_ATTACKER

# Human templates are the broadest group (soldiers, mages, thieves). Give the
# obvious archetypes a fitting attack instead of every human using the same
# martial "Power Strike". Other races already have a strong elemental identity.
_HUMAN_CASTER_KEYWORDS = (
    "mage", "wizard", "sorcerer", "warlock", "arcanist", "binder",
    "illusionist", "enchanter", "oracle", "witch", "shaman", "priest",
    "priestess", "acolyte", "cultist", "druid", "cleric", "scribe",
    "artificer",
)
_HUMAN_ARCHER_KEYWORDS = ("archer", "sniper", "hunter", "ranger")
_HUMAN_ROGUE_KEYWORDS = ("assassin", "thief", "footpad", "rogue", "cutpurse")


def _apply_name_flavor(kit, race, name_lower):
    """Swap the generic Human kit for a fitting archetype when the name says so."""
    if race != "Human":
        return
    if any(k in name_lower for k in _HUMAN_CASTER_KEYWORDS):
        kit["skill"] = _action("arcane_bolt", "Arcane Bolt", 1.35, 3, 2,
                               element="magical", chance=0.48)
        kit["aoe"] = _action("arcane_wave", "Arcane Wave", 0.75, 5, 7,
                             element="magical", chance=0.30)
    elif any(k in name_lower for k in _HUMAN_ARCHER_KEYWORDS):
        kit["skill"] = _action("aimed_shot", "Aimed Shot", 1.35, 3, 2,
                               element="physical", chance=0.48)
        kit["aoe"] = _action("arrow_volley", "Arrow Volley", 0.72, 5, 8,
                             element="physical", chance=0.30)
    elif any(k in name_lower for k in _HUMAN_ROGUE_KEYWORDS):
        kit["skill"] = _action("backstab", "Backstab", 1.35, 3, 2,
                               element="physical", chance=0.50,
                               status={"type": "bleed", "chance": 0.35,
                                       "duration": 3})
        kit["aoe"] = _action("fan_of_knives", "Fan of Knives", 0.70, 5, 8,
                             element="physical", chance=0.28,
                             status={"type": "bleed", "chance": 0.25,
                                     "duration": 2})


_DEFAULT_NAMES = {
    "skill": "Special Attack",
    "aoe": "Sweeping Attack",
    "heal": "Mend Wounds",
    "aoe_heal": "Soothing Chant",
}


# ── Kit construction ────────────────────────────────────────────────────────

def _has_scripted_ai(enemy):
    """True for enemies whose turns are owned by bespoke content code."""
    if enemy.get("ai_disabled") or enemy.get("is_dummy"):
        return True
    if enemy.get("super_boss"):
        return True
    # Hallucination-style enemies run their own round hooks and should keep
    # exactly the behaviour their module authored.
    if enemy.get("round_hook"):
        return True
    key = enemy.get("key")
    if key:
        try:
            from combat.wl_floor_bosses import WL_FLOOR_BOSS_MAP
            if any(key == entry[1] for entry in WL_FLOOR_BOSS_MAP.values()):
                return True
        except ImportError:
            pass
    return False


def _normalize_explicit_abilities(raw):
    """Convert a YAML ``abilities:`` list into the internal kit dict."""
    kit = {}
    for idx, entry in enumerate(raw):
        if not isinstance(entry, dict):
            continue
        kind = str(entry.get("type", "")).lower()
        if kind not in _DEFAULT_NAMES:
            continue
        defaults = {
            "skill": {"power": 1.30, "cooldown": 3, "chance": 0.45},
            "aoe": {"power": 0.72, "cooldown": 5, "chance": 0.30},
            "heal": {"cooldown": 4, "chance": 1.0, "heal_pct": 0.18},
            "aoe_heal": {"cooldown": 5, "chance": 1.0, "heal_pct": 0.12},
        }[kind]
        kit.setdefault(kind, {
            "id": entry.get("id") or f"{kind}_{idx}",
            "name": entry.get("name") or _DEFAULT_NAMES[kind],
            "power": float(entry.get("power", defaults.get("power", 0.0))),
            "cooldown": int(entry.get("cooldown", defaults.get("cooldown", 3))),
            "min_level": int(entry.get("min_level", 1)),
            "element": entry.get("element"),
            "chance": float(entry.get("chance", defaults.get("chance", 0.4))),
            "status": entry.get("status"),
            "heal_pct": float(entry.get("heal_pct", defaults.get("heal_pct", 0.18))),
            "drain_pct": float(entry.get("drain_pct", 0.0)),
        })
    return kit


def get_enemy_kit(enemy):
    """Return the enemy's action kit (cached on the enemy dict).

    Returns ``None`` for scripted enemies (superbosses, Wonderland floor
    bosses, hallucinations, dummies) or templates with ``ai_disabled: true``.
    """
    if enemy.get("_enemy_ai_kit_resolved"):
        return enemy.get("_enemy_ai_kit")

    kit = None
    if not _has_scripted_ai(enemy):
        raw = enemy.get("abilities")
        if isinstance(raw, list) and raw:
            kit = _normalize_explicit_abilities(raw) or None
        else:
            race = enemy.get("race")
            if not race and enemy.get("key"):
                race = ENEMIES.get(enemy["key"], {}).get("race")
            base = RACE_KITS.get(race)
            if base:
                kit = {k: dict(v) for k, v in base.items() if isinstance(v, dict)}
                name_lower = str(enemy.get("name", "")).lower()
                _apply_name_flavor(kit, race, name_lower)
                if any(k in name_lower for k in _HEAL_KEYWORDS):
                    kit.setdefault("heal", _support_heal())
                if any(k in name_lower for k in _AOE_HEAL_KEYWORDS):
                    kit.setdefault("aoe_heal", _support_aoe_heal())
                # Monster girls are capture targets, not squad tactics —
                # keep their turns single-target so nets stay viable.
                if enemy.get("monster_girl"):
                    kit.pop("aoe", None)
                    kit.pop("aoe_heal", None)

    role = get_enemy_role(enemy)
    # A future race kit may add heals without a support keyword/race; infer
    # supporter from the kit unless the designer explicitly forced a role.
    if (str(enemy.get("role") or "").lower() not in ROLE_VALUES and kit
            and ("heal" in kit or "aoe_heal" in kit)):
        role = ROLE_SUPPORTER
    enemy["role"] = role

    enemy["_enemy_ai_kit"] = kit
    enemy["_enemy_ai_kit_resolved"] = True
    return kit


# ── Health helpers ──────────────────────────────────────────────────────────

def _enemy_alive(enemy):
    return enemy is not None and enemy.get("hp", 0) > 0 and not enemy.get("captured")


def _party_alive(member):
    if member is None:
        return False
    return member.get("current_hp", 0) > 0


def _hp_frac(enemy):
    max_hp = max(1, enemy.get("max_hp", 1))
    return max(0.0, min(1.0, enemy.get("hp", 0) / max_hp))


def _target_max_hp(target):
    if "max_hp" in target:
        return max(1, target["max_hp"])
    if "attributes" in target:
        from character import player_max_hp
        return max(1, player_max_hp(target))
    return max(1, target.get("current_hp", 100))


def _party_hp_frac(member):
    max_hp = _target_max_hp(member)
    return max(0.0, min(1.0, member.get("current_hp", 0) / max_hp))


# ── AI selection ────────────────────────────────────────────────────────────

def _usable(enemy, action):
    """True when the action exists and is off cooldown / level-gated."""
    if not action:
        return False
    if enemy.get("level", 1) < action.get("min_level", 1):
        return False
    cooldowns = enemy.get("_enemy_ai_cooldowns", {})
    return cooldowns.get(action["id"], 0) <= 0


def choose_enemy_action(enemy, kit, all_enemies=None, party_members=None):
    """Pick this turn's action.

    Returns ``(kind, action, heal_target)`` or ``None`` to use a basic attack.
    Healing is considered first (self preservation, group heal, then wounded
    allies), then AoE damage, then a single-target skill.

    The enemy's level tier controls how often damage skills and AoE are used;
    Instinctive enemies (level 1-4) never use damage skills. Party targeting
    is intentionally absent — ``target`` is still chosen by the combat engine.
    """
    if not kit:
        return None

    role = get_enemy_role(enemy)
    is_supporter = role == ROLE_SUPPORTER
    tier = get_ai_tier(enemy.get("level", 1))

    allies = [e for e in (all_enemies or []) if _enemy_alive(e)]
    if not any(e is enemy for e in allies):
        allies.append(enemy)
    wounded = sorted(
        (e for e in allies if _hp_frac(e) < tier["wounded_threshold"]),
        key=_hp_frac,
    )

    # Only supporters manage healing. An explicit ``role: attacker`` keeps
    # its heal actions unused even if a designer listed them.
    if is_supporter:
        heal = kit.get("heal")
        if _usable(enemy, heal):
            if (_hp_frac(enemy) <= tier["self_heal_threshold"]
                    and random.random() < SELF_HEAL_CHANCE):
                return ("heal", heal, enemy)

        # Two or more wounded allies make the group heal the better support
        # play, so it is checked before the single-target heal.
        aoe_heal = kit.get("aoe_heal")
        aoe_heal_chance = AOE_HEAL_CHANCE + tier["aoe_heal_bonus"]
        if (_usable(enemy, aoe_heal) and len(wounded) >= AOE_HEAL_MIN_WOUNDED
                and random.random() < aoe_heal_chance):
            return ("aoe_heal", aoe_heal, None)

        if _usable(enemy, heal) and wounded:
            # Low-tier healers pick any wounded ally; trained ones triage.
            heal_target = wounded[0] if tier["smart_heal"] else random.choice(wounded)
            if random.random() < ALLY_HEAL_CHANCE + tier["ally_heal_bonus"]:
                return ("heal", heal, heal_target)

    alive_party = [t for t in (party_members or []) if _party_alive(t)]
    aoe = kit.get("aoe")
    if (_usable(enemy, aoe) and tier["aoe_mult"] > 0
            and len(alive_party) >= AOE_MIN_TARGETS):
        chance = float(aoe.get("chance", 0.30)) * tier["aoe_mult"]
        chance += tier["party_bonus"] * max(0, len(alive_party) - AOE_MIN_TARGETS)
        # Tactical+ enemies notice when the whole party is already hurt and
        # lean into a sweep. This is group-state awareness, not target choice.
        wounded_party = sum(1 for t in alive_party if _party_hp_frac(t) < 0.50)
        if wounded_party >= 2:
            chance += tier["wounded_party_bonus"]
        if is_supporter:
            chance *= SUPPORTER_AOE_MULT
        chance = min(chance, 0.85)
        if random.random() < chance:
            return ("aoe", aoe, None)

    skill = kit.get("skill")
    skill_mult = tier["skill_mult"]
    if is_supporter:
        skill_mult *= SUPPORTER_SKILL_MULT
    if _usable(enemy, skill) and skill_mult > 0:
        chance = min(0.85, float(skill.get("chance", 0.45)) * skill_mult)
        if random.random() < chance:
            return ("skill", skill, None)
    return None


# ── Execution ───────────────────────────────────────────────────────────────

def _tick_cooldowns(enemy):
    cooldowns = enemy.get("_enemy_ai_cooldowns")
    if not cooldowns:
        return
    for action_id in list(cooldowns):
        cooldowns[action_id] = max(0, cooldowns[action_id] - 1)


def _start_cooldown(enemy, action):
    cooldowns = enemy.setdefault("_enemy_ai_cooldowns", {})
    cooldowns[action["id"]] = max(1, int(action.get("cooldown", 3)))


def _subject(enemy):
    """Return the enemy's name with a single leading article."""
    name = str(enemy.get("name", "the enemy"))
    return name if name.lower().startswith(("the ", "a ", "an ")) else f"The {name}"


def _announce(enemy, action):
    c_print(f"\n  {_subject(enemy)} uses {action['name']}!")


def _resolve_element(enemy, action):
    element = action.get("element")
    if element == "auto":
        from combat.elemental import get_damage_element
        return get_damage_element(enemy.get("elemental_dmg", {}))
    return element


def _target_con(target, fallback):
    """Constitution used for armor when an AoE hits a non-primary target."""
    if target.get("is_ally"):
        from combat.ally import compute_ally_stats
        return compute_ally_stats(target)[1]
    if "attributes" in target:
        from combat.stats import compute_player_stats
        return compute_player_stats(target)[1]
    return fallback


def _dot_damage(enemy, target, status):
    base = status.get("damage")
    if base is None:
        base = max(2, int(enemy.get("str_mod", 0) * 0.5))
    pct = status.get("damage_pct")
    if pct:
        base = max(base, int(_target_max_hp(target) * float(pct)))
    return max(1, int(base))


def _apply_skill_status(enemy, target, action):
    """Apply the skill's optional rider status; returns True if it landed."""
    status = action.get("status")
    if not status:
        return False
    if random.random() >= float(status.get("chance", 0.35)):
        return False

    from combat import status_effects as se

    kind = str(status.get("type", "")).lower()
    duration = int(status.get("duration", 2))
    result = None
    if kind == "burn":
        result = se.apply_burn_to_player(target, tier=int(status.get("tier", 1)),
                                         duration=duration)
    elif kind == "poison":
        result = se.apply_poison(target, damage=_dot_damage(enemy, target, status),
                                 duration=duration)
    elif kind == "bleed":
        result = se.apply_bleed(target, damage=_dot_damage(enemy, target, status),
                                duration=duration)
    elif kind == "shock":
        result = se.apply_shock_to_player(
            target, damage=_dot_damage(enemy, target, status), duration=duration)
    elif kind == "weaken":
        result = se.apply_weaken(target,
                                 penalty_pct=float(status.get("penalty_pct", 0.20)),
                                 duration=duration)
    elif kind == "silence":
        result = se.apply_silence(target, duration=duration)
    elif kind == "blind":
        result = se.apply_blind(target, duration=duration)
    elif kind == "confusion":
        result = se.apply_confusion_to_player(target, duration=duration)
    elif kind == "dread":
        result = se.apply_dread(target, duration=duration)
    elif kind == "slow":
        result = se.apply_slow_to_player(target, duration=duration)

    if result in ("applied", "refreshed", "upgraded", "intensified", "stacked"):
        label = {
            "burn": "is burning",
            "poison": "is poisoned",
            "bleed": "is bleeding",
            "shock": "is shocked",
            "weaken": "grows weaker",
            "silence": "is silenced",
            "blind": "is blinded",
            "confusion": "is confused",
            "dread": "is filled with dread",
            "slow": "is slowed",
        }.get(kind)
        if label:
            c_print(f"  {target['name']} {label}!")
        return True
    return False


def _apply_drain(enemy, action):
    """Vampire-style self-heal after a damaging skill connects."""
    drain_pct = float(action.get("drain_pct", 0.0))
    dealt = enemy.get("_last_attack_damage", 0)
    if drain_pct <= 0 or dealt <= 0 or enemy.get("hp", 0) <= 0:
        return
    from combat.status_effects import apply_healing
    healed = apply_healing(enemy, max(1, int(dealt * drain_pct)), source=enemy)
    if healed > 0:
        c_print(f"  {_subject(enemy)} drains {healed} HP!")


def _run_heal(enemy, action, target):
    _announce(enemy, action)
    _start_cooldown(enemy, action)
    from combat.status_effects import apply_healing
    amount = max(1, int(_target_max_hp(target) * float(action.get("heal_pct", 0.18))))
    healed = apply_healing(target, amount, source=enemy)
    if healed > 0:
        c_print(f"  {target['name']} recovers {healed} HP.")
    elif healed < 0:
        c_print(f"  {target['name']} is wracked by the void — the healing becomes damage!")
    else:
        c_print(f"  The healing has no effect on {target['name']}.")
    return "healed"


def _run_aoe_heal(enemy, action, all_enemies):
    _announce(enemy, action)
    _start_cooldown(enemy, action)
    from combat.status_effects import apply_healing
    targets = [e for e in (all_enemies or [enemy]) if _enemy_alive(e)]
    for target in targets:
        amount = max(1, int(_target_max_hp(target) * float(action.get("heal_pct", 0.12))))
        healed = apply_healing(target, amount, source=enemy)
        if healed > 0:
            c_print(f"  {target['name']} recovers {healed} HP.")
    return "healed"


def _run_skill(enemy, action, target, target_con, defending, extra_logic,
               all_enemies, actual_player):
    _announce(enemy, action)
    _start_cooldown(enemy, action)
    outcome = enemy_attack(
        enemy, target, target_con, defending,
        extra_logic=extra_logic, all_enemies=all_enemies,
        actual_player=actual_player, skip_turn_start=True,
        power_mult=float(action.get("power", 1.30)),
        skill_name=action["name"],
        element_override=_resolve_element(enemy, action),
    )
    if outcome == "hit" and enemy.get("hp", 0) > 0 and enemy.get("_last_attack_damage", 0) > 0:
        _apply_skill_status(enemy, target, action)
        _apply_drain(enemy, action)
    return outcome


def _announce_fall(target):
    if target.get("defeated"):
        return
    target["defeated"] = True
    c_print(f"  {target.get('name', 'An ally')} has fallen!")


def _run_aoe_skill(enemy, action, party_members, primary_target, target_con,
                   defending, all_enemies, actual_player):
    targets = [t for t in (party_members or []) if _party_alive(t)]
    if not targets:
        targets = [primary_target]
    player_ref = actual_player or primary_target

    _announce(enemy, action)
    _start_cooldown(enemy, action)

    element = _resolve_element(enemy, action)
    for target in targets:
        if not _party_alive(target):
            continue
        con = target_con if target is primary_target else _target_con(target, target_con)
        # Only the player can be defending; apply it even when the engine
        # picked an ally as the primary target of this enemy turn.
        is_defending = bool(defending) and target is player_ref
        outcome = enemy_attack(
            enemy, target, con, is_defending,
            extra_logic=None, all_enemies=all_enemies,
            actual_player=actual_player, skip_turn_start=True,
            power_mult=float(action.get("power", 0.72)),
            skill_name=action["name"],
            element_override=element,
            allow_dodge=False,
        )
        if outcome == "hit" and enemy.get("hp", 0) > 0 and enemy.get("_last_attack_damage", 0) > 0:
            _apply_skill_status(enemy, target, action)
            _apply_drain(enemy, action)
        if target is not player_ref and not _party_alive(target):
            _announce_fall(target)
        if not _party_alive(player_ref):
            return "dead"
        # Reflection / on-hit counters can kill the caster mid-sweep.
        if enemy.get("hp", 0) <= 0:
            break
    return "hit"


def enemy_take_turn(enemy, target, target_con, defending, *, extra_logic=None,
                    all_enemies=None, actual_player=None, party_members=None):
    """Run one regular-enemy turn: upkeep → choose ability → resolve.

    Drop-in replacement for the engine's direct ``enemy_attack`` call.
    ``party_members`` is the living party list (player + active allies) the
    engine already computed; it is used for AoE targeting.
    """
    _tick_cooldowns(enemy)

    outcome, _fear = begin_enemy_turn(enemy, all_enemies=all_enemies)
    if outcome:
        return outcome

    kit = get_enemy_kit(enemy)
    choice = choose_enemy_action(enemy, kit, all_enemies, party_members)

    if choice is None:
        return enemy_attack(
            enemy, target, target_con, defending,
            extra_logic=extra_logic, all_enemies=all_enemies,
            actual_player=actual_player, skip_turn_start=True,
        )

    kind, action, heal_target = choice
    if kind == "heal":
        return _run_heal(enemy, action, heal_target)
    if kind == "aoe_heal":
        return _run_aoe_heal(enemy, action, all_enemies)
    if kind == "aoe":
        return _run_aoe_skill(enemy, action, party_members, target, target_con,
                              defending, all_enemies, actual_player)
    return _run_skill(enemy, action, target, target_con, defending,
                      extra_logic, all_enemies, actual_player)
