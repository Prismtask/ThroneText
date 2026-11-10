"""family.py — Family system state, switches, and pure helpers.

Implements docs/family_system_design.md Phases 1–4:
- per-save/per-girl field migration (`ensure_family_fields`)
- affection ladder v2 cap migration (§4.8); true-born bond cap 100
- content-level gating (§3.1)
- sleep-sharing eligibility + season/moon initiation chance (§4.3, §4.9)
- pregnancy period tracking, third-period lounge return, child growth
- conception outcomes, birth records, adult conversion
- no-romance sanitizing and Father's Legacy passive helpers

No scenes or UI live here; the house/sleep-sharing modules render them.
"""

# ── Constants (single tuning block) ────────────────────────────────────────
# Affection ladder v2 (§4.8)
BASE_AFFECTION_CAP = 200
ENGAGED_AFFECTION_CAP = 300
CHILD_BOND_CAP = 100          # true-born children: bond only, no romance
PLAYER_INITIATE_AFFECTION = 140
ALLY_INITIATE_AFFECTION = 160

# Pregnancy / growth (§5, §6.2)
PREGNANCY_DAYS = 30
PREGNANCY_PERIOD_DAYS = 10
POST_BIRTH_RECOVERY_DAYS = 7
CONCEPTION_COOLDOWN_DAYS = 30
GROWTH_INFANT_DAYS = 15
GROWTH_ADULT_DAYS = 40
GROWTH_PRIME_DAYS = 60
# Child stage spans days 15–40 (25 days); named for display/tuning.
GROWTH_CHILD_DAYS = GROWTH_ADULT_DAYS - GROWTH_INFANT_DAYS

# Ally-initiated night chance (§4.9)
INITIATE_BASE = 0.06
INITIATE_ENGAGED = 0.04
INITIATE_MARRIED = 0.08
INITIATE_MIN = 0.02
INITIATE_MAX = 0.25
SEASON_INITIATE_MODS = {
    "spring": 0.03,
    "summer": 0.01,
    "autumn": 0.00,
    "winter": 0.02,
}
FULL_MOON_INITIATE_MOD = 0.05
NEW_MOON_INITIATE_MOD = 0.02
MONSTER_GIRL_SEASON_INITIATE_MOD = 0.03
WARY_PREY_INITIATE_MOD = -0.03
BLESSED_WIND_INITIATE_MOD = 0.02

# Conception (§4.6)
CONCEPTION_BASE = 0.12
CONCEPTION_ENDING_MODS = {
    "together": 0.08,
    "warm": 0.04,
    "quiet": 0.00,
    "rest": None,          # no roll
}
CONCEPTION_ENGAGED = 0.05
CONCEPTION_MARRIED = 0.10
CONCEPTION_CAP = 0.35
PITY_START = 5
PITY_STEP = 0.10
PITY_GUARANTEE = 8

CONTENT_LEVELS = ("off", "fade-to-black", "written")
DEFAULT_CONTENT_LEVEL = "fade-to-black"

# Attribute order shared with the combat layer (avoid importing it at module load).
ATTRIBUTES = ("Strength", "Constitution", "Dexterity", "Wisdom", "Learning", "Charisma")

# Preferred-tone fallbacks by race (docs/family_system_design.md §4.4).
TONE_DEFAULTS = {
    "Demon": ("bold", "playful"),
    "Dragonkin": ("bold", "playful"),
    "Vampire": ("bold", "tender"),
    "Undead": ("shy", "tender"),
    "Shadow": ("shy", "tender"),
    "Construct": ("shy", "tender"),
    "Fey": ("playful", "tender"),
    "Elemental": ("playful", "tender"),
    "Beast": ("playful", "tender"),
    "Human": ("tender", "playful"),
    "Goblin": ("tender", "bold"),
    "Giant": ("tender", "bold"),
    "Orc": ("tender", "bold"),
    "Lizardfolk": ("tender", "shy"),
    "Abomination": ("shy", "playful"),
}

# Father's Legacy (O4a — weakened player-race passive table).
FATHER_LEGACY_TABLE = {
    "Human": {"type": "attributes", "count": 2, "value": 1,
              "label": "+1 to two attributes"},
    "Elf": {"type": "passive", "passive": "dodge", "value": 0.05,
            "label": "+5% dodge"},
    "Dwarf": {"type": "passive", "passive": "max_hp_pct", "value": 0.075,
              "label": "+7.5% max HP"},
    "Halfling": {"type": "passive", "passive": "crit", "value": 0.05,
                 "label": "+5% crit"},
    "Orc": {"type": "passive", "passive": "low_hp_damage", "value": 0.075,
            "label": "+7.5% damage below 50% HP"},
    "Gnome": {"type": "passive", "passive": "item_effectiveness", "value": 0.05,
              "label": "+5% item effectiveness"},
    "Tiefling": {"type": "passive", "passive": "fire_dark_damage", "value": 0.075,
                 "label": "+7.5% fire & dark damage"},
    "Dragonborn": {"type": "passive", "passive": "elemental_damage", "value": 0.05,
                   "label": "+5% all elemental damage"},
}

# Sleep buff families that merge instead of stacking.
SLEEP_BUFF_TYPES = ("well_rested", "shared_night", "dream_blessed")


# ── Small helpers ──────────────────────────────────────────────────────────

def _int(value, default=0):
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def _iter_girls(player):
    """Yield every owned girl record (active, benched, and housed)."""
    for ally in player.get("allies", []) or []:
        yield ally
    for ally in player.get("wonderland_benched_allies", []) or []:
        yield ally
    for house in (player.get("houses") or {}).values():
        for girl in house.get("monster_girls", []) or []:
            yield girl


def _first_house(player):
    houses = player.get("houses") or {}
    if not houses:
        return None
    origin = player.get("origin_city")
    if origin in houses:
        return houses[origin]
    return next(iter(houses.values()))


def is_trueborn(girl):
    """True for a child born through the family system."""
    return bool(girl.get("is_trueborn"))


def is_trueborn_minor(girl):
    """True while a true-born child is still infant/child (not adult)."""
    if not is_trueborn(girl):
        return False
    return girl.get("stage") in ("infant", "child")


# ── Content switch (§3.1) ──────────────────────────────────────────────────

def get_content_level(settings=None):
    """Return 'off' | 'fade-to-black' | 'written' (global display setting)."""
    if settings is None:
        try:
            from gui.settings import load_settings
            settings = load_settings()
        except Exception:
            settings = {}
    level = (settings or {}).get("content_level", DEFAULT_CONTENT_LEVEL)
    return level if level in CONTENT_LEVELS else DEFAULT_CONTENT_LEVEL


def intimacy_enabled(settings=None):
    """Sleep sharing exists whenever content level is not 'off'."""
    return get_content_level(settings) != "off"


def family_system_enabled(player):
    """Pregnancy/children only — Game Rules choice, final per save."""
    return bool(player.get("family_enabled"))


# ── State + migration ──────────────────────────────────────────────────────

def ensure_family_fields(player):
    """Seed family state and per-girl pregnancy fields. Idempotent."""
    player.setdefault("children", [])
    player.setdefault("family_enabled", False)
    player.setdefault("family_births_pending", [])

    for girl in _iter_girls(player):
        girl.setdefault("pregnant", False)
        girl.setdefault("conceived_day", 0)
        girl.setdefault("due_day", 0)
        girl.setdefault("next_conception_day", 0)
        girl.setdefault("recovery_until", 0)
        girl.setdefault("pregnancy_pity", 0)
        girl.setdefault("beloved_until_day", 0)
        girl.setdefault("is_trueborn", False)
        girl.setdefault("no_romance", False)
        if girl.get("is_trueborn"):
            girl["no_romance"] = True
        if girl.get("is_trueborn") or girl.get("no_romance"):
            # Hard no-romance invariant: children never carry engagement or
            # marriage state, and their affection is a 100-point bond.
            girl["engaged"] = False
            girl["married"] = False
            cap = _int(girl.get("affection_cap"), CHILD_BOND_CAP)
            if cap <= 0 or cap > CHILD_BOND_CAP:
                girl["affection_cap"] = CHILD_BOND_CAP
            girl["affection"] = min(_int(girl.get("affection"), 0),
                                     CHILD_BOND_CAP)

    # Remove stale engagement/marriage keys for children from the global lists.
    blocked_keys = {girl.get("key") for girl in _iter_girls(player)
                    if girl.get("is_trueborn") or girl.get("no_romance")}
    for field in ("engaged_girls", "married_girls"):
        if field in player:
            player[field] = [key for key in (player.get(field) or [])
                             if key not in blocked_keys]

    migrate_affection_caps(player)


def migrate_affection_caps(player):
    """Affection ladder v2: base cap 200; engaged/married cap 300.

    Only raises caps — existing affection is preserved and no cap is lowered
    (a hand-tuned or legacy cap above the new floor stays untouched).
    """
    for girl in _iter_girls(player):
        if girl.get("is_trueborn") or girl.get("no_romance"):
            required = CHILD_BOND_CAP
        elif girl.get("engaged") or girl.get("married"):
            required = ENGAGED_AFFECTION_CAP
        else:
            required = BASE_AFFECTION_CAP
        if _int(girl.get("affection_cap"), 0) < required:
            girl["affection_cap"] = required


# ── Sleep-sharing eligibility (§4.3) ───────────────────────────────────────

def share_night_eligibility(player, girl, initiated_by_player=True,
                            settings=None, day=None):
    """Return (ok, reason) for the night event (no scenes in Phase 1)."""
    if not intimacy_enabled(settings):
        return False, "Intimacy content is off."
    if girl.get("is_trueborn") or girl.get("no_romance"):
        return False, "Family content is not available for this companion."
    if girl.get("pregnant"):
        return False, "She is expecting."
    if girl.get("dispatch_mission"):
        return False, "She is away on a dispatch."
    day = _int(day if day is not None else player.get("day", 1), 1)
    if _int(girl.get("injured_until"), 0) > day:
        return False, "She is injured and recovering."
    if _int(girl.get("recovery_until"), 0) > day:
        return False, "She is still recovering after childbirth."
    threshold = (PLAYER_INITIATE_AFFECTION
                 if initiated_by_player else ALLY_INITIATE_AFFECTION)
    if _int(girl.get("affection"), 0) < threshold:
        return False, f"Requires {threshold} affection."
    return True, ""


# ── Season/moon initiation chance (§4.9) ───────────────────────────────────

def initiation_chance(player, girl, day=None, settings=None):
    """Ally-initiated night chance with season, moon, and daily-event mods."""
    if not intimacy_enabled(settings):
        return 0.0
    day = _int(day if day is not None else player.get("day", 1), 1)

    chance = INITIATE_BASE
    if girl.get("married"):
        chance += INITIATE_MARRIED
    elif girl.get("engaged"):
        chance += INITIATE_ENGAGED

    daily = player.get("daily_effects", {}) or {}
    dom = 0
    try:
        from events import get_season, get_month_day
        season_id, _ = get_season(day)
        _, dom = get_month_day(day)
        chance += SEASON_INITIATE_MODS.get(season_id, 0.0)
    except Exception:
        pass

    if daily.get("full_moon"):
        chance += FULL_MOON_INITIATE_MOD
    if dom == 1:
        chance += NEW_MOON_INITIATE_MOD

    capture_bonus = _int(daily.get("capture_bonus"), 0)
    if capture_bonus > 0:
        chance += MONSTER_GIRL_SEASON_INITIATE_MOD
    elif capture_bonus < 0:
        chance += WARY_PREY_INITIATE_MOD
    if _int(daily.get("all_stats"), 0) > 0:
        chance += BLESSED_WIND_INITIATE_MOD

    return max(INITIATE_MIN, min(INITIATE_MAX, chance))


# ── Pregnancy lifecycle helpers (§5) ───────────────────────────────────────

def _conceived_day(girl):
    conceived = _int(girl.get("conceived_day"), 0)
    if conceived > 0:
        return conceived
    due = _int(girl.get("due_day"), 0)
    if due > 0:
        return max(1, due - PREGNANCY_DAYS)
    return 0


def pregnancy_period(girl, day):
    """1, 2, or 3 while pregnant; None otherwise. Due pregnancies stay at 3."""
    if not girl.get("pregnant"):
        return None
    conceived = _conceived_day(girl)
    if conceived <= 0:
        return 1
    elapsed = max(0, _int(day, 1) - conceived)
    return min(3, elapsed // PREGNANCY_PERIOD_DAYS + 1)


def pregnancy_due(girl, day):
    if not girl.get("pregnant"):
        return False
    due = _int(girl.get("due_day"), 0)
    if due > 0:
        return _int(day, 1) >= due
    conceived = _conceived_day(girl)
    return conceived > 0 and _int(day, 1) >= conceived + PREGNANCY_DAYS


def start_pregnancy(girl, day):
    day = _int(day, 1)
    girl["pregnant"] = True
    girl["conceived_day"] = day
    girl["due_day"] = day + PREGNANCY_DAYS


def finish_pregnancy(girl, day):
    """Clear pregnancy state and start recovery/cooldown (child record is Phase 2)."""
    day = _int(day, 1)
    girl["pregnant"] = False
    girl["recovery_until"] = day + POST_BIRTH_RECOVERY_DAYS
    girl["next_conception_day"] = day + CONCEPTION_COOLDOWN_DAYS
    girl["conceived_day"] = 0
    girl["due_day"] = 0


def can_conceive(girl, day):
    """Conception cooldown gate (O15)."""
    return _int(day, 1) >= _int(girl.get("next_conception_day"), 0)


def conception_chance(player, girl, ending):
    """Conception roll chance after an intimate ending (Phase 2)."""
    if not family_system_enabled(player):
        return 0.0
    if ending not in CONCEPTION_ENDING_MODS:
        return 0.0
    ending_mod = CONCEPTION_ENDING_MODS[ending]
    if ending_mod is None:
        return 0.0

    attempts = _int(girl.get("pregnancy_pity"), 0)
    if attempts + 1 >= PITY_GUARANTEE:
        return 1.0

    chance = CONCEPTION_BASE + ending_mod
    if girl.get("married"):
        chance += CONCEPTION_MARRIED
    elif girl.get("engaged"):
        chance += CONCEPTION_ENGAGED
    if attempts >= PITY_START:
        chance += (attempts - PITY_START + 1) * PITY_STEP
    return min(CONCEPTION_CAP, chance)


def record_conception_attempt(girl, conceived):
    if conceived:
        girl["pregnancy_pity"] = 0
    else:
        girl["pregnancy_pity"] = _int(girl.get("pregnancy_pity"), 0) + 1


# ── Child growth (§6.2) ────────────────────────────────────────────────────

def _child_elapsed(child, day):
    born = _int(child.get("born_day"), 0)
    return max(0, _int(day, 1) - born) if born > 0 else 0


def growth_stage_for_child(child, day):
    elapsed = _child_elapsed(child, day)
    if elapsed >= GROWTH_ADULT_DAYS:
        return "adult"
    if elapsed >= GROWTH_INFANT_DAYS:
        return "child"
    return "infant"


def is_prime(child, day):
    """True once the child reaches the age where aging stops (60 days)."""
    return _child_elapsed(child, day) >= GROWTH_PRIME_DAYS


def growth_days_remaining(child, day):
    """Days until the next growth stage (0 when adult)."""
    stage = growth_stage_for_child(child, day)
    if stage == "adult":
        return 0
    elapsed = _child_elapsed(child, day)
    target = GROWTH_ADULT_DAYS if stage == "child" else GROWTH_INFANT_DAYS
    return max(0, target - elapsed)


def growth_days_to_prime(child, day):
    """Days until the prime milestone (0 once reached)."""
    return max(0, GROWTH_PRIME_DAYS - _child_elapsed(child, day))


# ── Phase 2: shared night, birth, and child records ────────────────────────

def journal_event(player, name, desc):
    """Append a [FAMILY] Journal event (Journal + log only — no toasts)."""
    try:
        from events import ensure_journal
        ensure_journal(player)
        player["journal"]["events"].append({
            "day": player.get("day", 1),
            "name": name,
            "desc": desc,
            "tag": "[FAMILY]",
            "fixed": False,
        })
    except Exception:
        pass


def get_preferred_tones(girl, template=None):
    """Return the girl's two preferred tones (persisting a derived default)."""
    tones = girl.get("preferred_tones")
    if tones:
        return tuple(tones)
    template = template or {}
    family_block = template.get("family") or {}
    tones = family_block.get("preferred_tones")
    if tones:
        girl["preferred_tones"] = list(tones)
        return tuple(tones)
    race = template.get("race") or girl.get("race")
    tones = TONE_DEFAULTS.get(race, ("tender", "playful"))
    try:
        girl["preferred_tones"] = list(tones)
    except Exception:
        pass
    return tuple(tones)


def primary_attribute(girl):
    """Best-effort primary attribute for the `beloved` buff."""
    attrs = girl.get("attributes") or {}
    if attrs:
        return max(ATTRIBUTES, key=lambda a: (attrs.get(a, 0), -ATTRIBUTES.index(a)))
    try:
        from resources.enemies import ENEMIES
        template = ENEMIES.get(girl.get("key"), {}) or {}
    except Exception:
        template = {}
    mods = template.get("mods") or {}
    if mods:
        return max(ATTRIBUTES, key=lambda a: (mods.get(a, 0), -ATTRIBUTES.index(a)))
    return "Strength"


def father_legacy(player):
    """O4a — weakened player-race passive carried by the child."""
    race = player.get("race", "Human")
    legacy = dict(FATHER_LEGACY_TABLE.get(race, FATHER_LEGACY_TABLE["Human"]))
    legacy["race"] = race
    if legacy.get("type") == "attributes":
        legacy["chosen"] = list(legacy.get("chosen") or [])
    return legacy


def _father_legacy_passive(actor):
    """Return the passive legacy block, or None for Human attribute legacy."""
    legacy = actor.get("father_legacy") or {}
    if legacy.get("type") != "passive":
        return None
    return legacy


def father_legacy_max_hp_mult(actor):
    """Dwarf legacy: +7.5% max HP."""
    legacy = _father_legacy_passive(actor)
    if legacy and legacy.get("passive") == "max_hp_pct":
        return 1.0 + float(legacy.get("value", 0) or 0)
    return 1.0


def father_legacy_evasion(actor):
    """Elf legacy: +5% dodge."""
    legacy = _father_legacy_passive(actor)
    if legacy and legacy.get("passive") == "dodge":
        return float(legacy.get("value", 0) or 0)
    return 0.0


def father_legacy_crit_chance(actor):
    """Halfling legacy: +5% crit chance."""
    legacy = _father_legacy_passive(actor)
    if legacy and legacy.get("passive") == "crit":
        return float(legacy.get("value", 0) or 0)
    return 0.0


def father_legacy_damage_mult(actor):
    """Orc legacy: +7.5% damage while below 50% HP."""
    legacy = _father_legacy_passive(actor)
    if legacy and legacy.get("passive") == "low_hp_damage":
        max_hp = _int(actor.get("max_hp"), 0)
        if max_hp > 0 and _int(actor.get("current_hp"), 0) <= max_hp * 0.5:
            return 1.0 + float(legacy.get("value", 0) or 0)
    return 1.0


def father_legacy_item_mult(actor):
    """Gnome legacy: +5% item effectiveness."""
    legacy = _father_legacy_passive(actor)
    if legacy and legacy.get("passive") == "item_effectiveness":
        return 1.0 + float(legacy.get("value", 0) or 0)
    return 1.0


def father_legacy_elemental_bonus(actor, element):
    """Tiefling/Dragonborn legacy elemental damage bonus for one element."""
    legacy = _father_legacy_passive(actor)
    if not legacy:
        return 0.0
    passive = legacy.get("passive")
    if passive == "fire_dark_damage" and element in ("fire", "dark"):
        return float(legacy.get("value", 0) or 0)
    if passive == "elemental_damage":
        return float(legacy.get("value", 0) or 0)
    return 0.0


def father_legacy_label(actor):
    """Short UI label for an actor's Father's Legacy."""
    legacy = actor.get("father_legacy") or {}
    label = legacy.get("label") or ""
    chosen = legacy.get("chosen") or []
    if label and isinstance(chosen, (list, tuple)) and chosen:
        label += f" ({', '.join(str(c) for c in chosen)})"
    return label


def grant_sleep_buff(actor, buff_type, value, remaining, stat="all"):
    """Add/merge a sleep buff. well_rested and shared_night never stack."""
    buffs = actor.setdefault("active_buffs", [])
    if buff_type in SLEEP_BUFF_TYPES:
        existing = next((b for b in buffs if b.get("type") in SLEEP_BUFF_TYPES), None)
    else:
        existing = next((b for b in buffs if b.get("type") == buff_type), None)

    if existing is not None:
        cur_value = _int(existing.get("value"), 0)
        cur_remaining = _int(existing.get("remaining"), 0)
        merged_value = max(cur_value, _int(value, 0))
        merged_remaining = max(cur_remaining, _int(remaining, 0))
        merged_type = buff_type if _int(value, 0) >= cur_value else existing.get("type")
        had_shared = (buff_type == "shared_night"
                      or existing.get("type") == "shared_night"
                      or bool(existing.get("shared_night")))
        existing.clear()
        existing.update({
            "type": merged_type,
            "stat": stat,
            "value": merged_value,
            "remaining": merged_remaining,
        })
        if had_shared:
            existing["shared_night"] = True
        return existing

    buff = {"type": buff_type, "stat": stat, "value": value, "remaining": remaining}
    if buff_type == "shared_night":
        buff["shared_night"] = True
    buffs.append(buff)
    return buff


def beloved_multiplier(girl, day):
    """+10% affection gain until the next sleep after a `beloved` night."""
    if _int(girl.get("beloved_until_day"), 0) >= _int(day, 1):
        return 1.1
    return 1.0


SLEEP_ENDINGS = {
    "together": {"affection": 4, "stress": -20, "shared": True,  "beloved": True},
    "warm":     {"affection": 3, "stress": -15, "shared": True,  "beloved": True},
    "quiet":    {"affection": 1, "stress": -10, "shared": True,  "beloved": False},
    "rest":     {"affection": 1, "stress": -5,  "shared": False, "beloved": False},
}


def apply_sleep_outcome(player, girl, ending, rng=None):
    """Apply a Shared Night ending: affection, stress, buffs, conception."""
    import random as _random
    rng = rng or _random
    day = _int(player.get("day", 1), 1)
    reward = SLEEP_ENDINGS.get(ending, SLEEP_ENDINGS["rest"])

    cap = _int(girl.get("affection_cap"), BASE_AFFECTION_CAP)
    girl["affection"] = min(cap, _int(girl.get("affection"), 30) + reward["affection"])
    girl["stress"] = max(0, min(100, _int(girl.get("stress"), 0) + reward["stress"]))

    if reward["shared"]:
        grant_sleep_buff(player, "shared_night", 1, 2)
        # Story-dream trigger (docs/dream_events_design.md §2.4): the first
        # shared night queues a warm, fade-to-black dream at the next sleep.
        player["had_shared_night"] = True
    if reward["beloved"]:
        grant_sleep_buff(girl, "beloved", 2, 2, stat=primary_attribute(girl))
        girl["beloved_until_day"] = day + 1

    conceived = False
    if ending in ("together", "warm", "quiet"):
        if (family_system_enabled(player) and not girl.get("pregnant")
                and can_conceive(girl, day)):
            chance = conception_chance(player, girl, ending)
            conceived = rng.random() < chance
            record_conception_attempt(girl, conceived)
            if conceived:
                start_pregnancy(girl, day)
                # Story-dream trigger (§2.4): an expectant-household dream.
                player["family_expecting"] = True
                from events import format_short_date
                journal_event(
                    player, "A new life",
                    f"{girl.get('name', 'Your companion')} is expecting "
                    f"(due {format_short_date(girl.get('due_day'))}).",
                )

    return {
        "ending": ending,
        "conceived": conceived,
        "affection": girl["affection"],
        "stress": girl["stress"],
    }


def sleep_night_candidates(player, house):
    """Active allies + the current house's girls, deduplicated."""
    seen = set()
    out = []
    for girl in list(player.get("allies", []) or []) + list((house or {}).get("monster_girls", []) or []):
        uid = (girl.get("key"), girl.get("name"))
        if uid in seen:
            continue
        seen.add(uid)
        out.append(girl)
    return out


def roll_sleep_initiation(player, house, rng=None):
    """Pick at most one ally-initiated partner for tonight (or None)."""
    import random as _random
    if not intimacy_enabled():
        return None
    rng = rng or _random
    best = None
    best_roll = -1.0
    for girl in sleep_night_candidates(player, house):
        ok, _ = share_night_eligibility(player, girl, initiated_by_player=False)
        if not ok:
            continue
        chance = initiation_chance(player, girl)
        roll = rng.random()
        if roll < chance and roll > best_roll:
            best = girl
            best_roll = roll
    return best


def _find_house_city(player, girl):
    for city, house in (player.get("houses") or {}).items():
        for candidate in house.get("monster_girls", []) or []:
            if (candidate is girl
                    or (candidate.get("key") == girl.get("key")
                        and candidate.get("name") == girl.get("name"))):
                return city
    return player.get("origin_city") or next(iter(player.get("houses") or {}), None)


def build_child_record(player, girl, day):
    """Create the true-born child record (birth is state-only; naming is UI)."""
    from resources.enemies import ENEMIES
    from combat.ally_skills import initialize_ally_skills

    mother_key = girl.get("key")
    template = ENEMIES.get(mother_key, {}) or {}
    race = template.get("race") or girl.get("race") or "Human"

    base_attrs = {}
    try:
        from combat.stats import compute_enemy_attributes
        if mother_key:
            base_attrs = compute_enemy_attributes(mother_key) or {}
    except Exception:
        base_attrs = {}
    if not base_attrs:
        base_attrs = template.get("mods") or {}
    attrs = {attr: max(1, int(base_attrs.get(attr, 1) * 0.9)) for attr in ATTRIBUTES}

    temp = {"key": mother_key, "race": race, "awakened": False, "awakened_skills": []}
    try:
        initialize_ally_skills(temp, mother_key, race)
    except Exception:
        pass
    innate = list(temp.get("innate_skills", []) or [])
    passive = temp.get("passive_skill")

    prefix = f"trueborn_{mother_key}_"
    count = sum(1 for c in player.get("children", []) or []
                if str(c.get("key", "")).startswith(prefix))
    for house in (player.get("houses") or {}).values():
        count += sum(1 for g in house.get("monster_girls", []) or []
                     if str(g.get("key", "")).startswith(prefix))

    return {
        "key": f"{prefix}{count + 1}",
        "mother_key": mother_key,
        "mother_name": girl.get("name"),
        "name": f"{girl.get('name', 'Companion')}'s child",
        "pending_name": True,
        "race": race,
        "father_race": player.get("race", "Human"),
        "legacy": father_legacy(player),
        "born_day": _int(day, 1),
        "stage": "infant",
        "affection": 30,
        "affection_cap": CHILD_BOND_CAP,
        "innate_skills": innate,
        "passive_skill": passive,
        "preferred_tones": list(get_preferred_tones(girl, template)),
        "attributes": attrs,
        "home_city": _find_house_city(player, girl),
        "is_trueborn": True,
        "no_romance": True,
    }


def birth_child(player, girl, day):
    """Create the child, finish the pregnancy, and queue the birth scene."""
    child = build_child_record(player, girl, day)
    player.setdefault("children", []).append(child)
    from titles import check_unlock as _check_title_unlock
    _check_title_unlock(player)
    finish_pregnancy(girl, day)
    journal_event(
        player, "A child is born",
        f"{girl.get('name', 'Your companion')} has given birth. The child is healthy.",
    )
    player.setdefault("family_births_pending", []).append({
        "child_key": child["key"],
        "mother": girl.get("name"),
        "day": _int(day, 1),
    })
    return child


def name_child(child, name):
    """Set a child's name and clear the pending-name flag."""
    name = " ".join((name or "").split())[:24]
    if name:
        child["name"] = name
        child["pending_name"] = False
        return True
    return False


def convert_child_to_house(player, child, day):
    """Adult conversion: children become true-born house girls (bond only)."""
    houses = player.get("houses") or {}
    if not houses:
        return None

    city = child.get("home_city")
    if city not in houses:
        city = next(iter(houses))
    house = houses[city]

    # Children count toward the house monster-girl cap (O6). If the house is
    # full, she waits in the nursery until room is freed.
    try:
        from facilities.house import HOUSE_MONSTER_GIRL_LIMITS
        limit = HOUSE_MONSTER_GIRL_LIMITS.get(house.get("level", 1), 2)
        total = len(house.get("monster_girls", []) or []) + len(player.get("allies", []) or [])
        if total >= limit:
            return None
    except Exception:
        pass

    attrs = dict(child.get("attributes") or {})
    legacy = dict(child.get("legacy") or {})
    if legacy.get("type") == "attributes":
        chosen = list(legacy.get("chosen") or [])
        if not chosen:
            chosen = sorted(ATTRIBUTES, key=lambda a: attrs.get(a, 0), reverse=True)[
                :int(legacy.get("count", 2))]
            legacy["chosen"] = chosen
        for attr in chosen:
            attrs[attr] = attrs.get(attr, 0) + int(legacy.get("value", 1))

    record = {
        "key": child["key"],
        "mother_key": child.get("mother_key"),
        "name": child.get("name", "True-born"),
        "level": 1,
        "affection": _int(child.get("affection"), 30),
        "affection_cap": CHILD_BOND_CAP,
        "captured_on": _int(day, 1),
        "exp": 0,
        "level_hp_bonus": 0,
        "level_cap": 10,
        "growth_applied": 0,
        "attributes": attrs,
        "innate_skills": list(child.get("innate_skills", []) or []),
        "passive_skill": child.get("passive_skill"),
        "race": child.get("race"),
        "preferred_tones": list(child.get("preferred_tones", []) or []),
        "father_legacy": legacy,
        "is_trueborn": True,
        "no_romance": True,
        "pregnant": False,
        "conceived_day": 0,
        "due_day": 0,
        "next_conception_day": 0,
        "pregnancy_pity": 0,
        "home_city": city,
        "stage": "adult",
        "prime": bool(child.get("prime")),
    }
    house.setdefault("monster_girls", []).append(record)
    journal_event(
        player, "A child comes of age",
        f"{record['name']} is grown and can now live in the house.",
    )
    return record


# ── Day-tick ───────────────────────────────────────────────────────────────

def family_tick(player, old_day=None):
    """Daily family state: pregnancy periods, births, and child growth."""
    # Event Horizon is a time pocket — family time does not advance there.
    try:
        from event_horizon import in_run
        if in_run(player):
            return
    except Exception:
        pass

    day = _int(player.get("day", 1), 1)

    # Third period: the girl leaves active combat and rests in the house.
    for ally in list(player.get("allies", []) or []):
        if not ally.get("pregnant"):
            continue
        if pregnancy_period(ally, day) < 3:
            continue
        house = _first_house(player)
        if house is None:
            continue
        from combat.ally import _return_ally_to_house
        _return_ally_to_house(player, ally, house)
        try:
            player["allies"].remove(ally)
        except ValueError:
            pass

    # Births (state-only; the birth scene/naming is handled at home sleep).
    for girl in list(_iter_girls(player)):
        if pregnancy_due(girl, day):
            birth_child(player, girl, day)

    # Children: update stages; adults move into the house roster.
    for child in list(player.get("children", []) or []):
        stage = growth_stage_for_child(child, day)
        child["stage"] = stage
        child["prime"] = is_prime(child, day) or bool(child.get("prime"))
        if stage == "adult":
            if convert_child_to_house(player, child, day) is not None:
                try:
                    player["children"].remove(child)
                except ValueError:
                    pass

