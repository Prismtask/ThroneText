"""facilities/dispatch.py — Dispatch board (Phase 1).

Send housed monster girls on time-based missions: dungeon sweeps over floors
the player has already cleared, or errands (foraging / courier / escort /
scouting / survey). Missions resolve inside ``utils.advance_time``; rewards
are collected back at the house.

Phase 1 scope: data + offers + procedural names + stress/mood + HP tracking
(injuries, Downed state, nightly recovery) + launch / resolution / collection.

Design: docs/dispatch_system_design.md (locked 2026-10-05).
"""
import random

from resources.cities import CITIES
from resources.items import ITEMS
from resources.wild_dungeon_themes import get_theme
from utils import display_name

REFRESH_DAYS = 3
REPORT_CAP = 10

# ── Name pools (wild-dungeon style: "{adjective} {noun} {suffix}") ──────────

STAR_ADJECTIVES = {
    1: ["Quiet", "Sunlit", "Routine", "Dusty", "Green", "Mild"],
    2: ["Watchful", "Wandering", "Dim", "Earnest", "Dusk", "Wind-Cut"],
    3: ["Bitter", "Brooding", "Rough", "Sundered", "Hollow", "Storm-Watched"],
    4: ["Dire", "Feral", "Reaving", "Grave-Bound", "Thunderous", "Sanguine"],
    5: ["Calamitous", "Abyssal", "Ruinous", "Fated", "Heaven-Scorned", "Dragon-Glass"],
    6: ["Aeon-Breaking", "Heaven-Rent", "Void-Wrought", "Sun-Eclipsed", "World-Wound", "Final"],
}

SWEEP_SUFFIXES = {
    1: ["Sweep", "Push", "Patrol"],
    2: ["Sweep", "Push", "Descent"],
    3: ["Descent", "Clearing", "Assault"],
    4: ["Breach", "Onslaught", "Clearing"],
    5: ["Breach", "Onslaught", "Reckoning"],
    6: ["Cataclysm", "Finality", "Apotheosis"],
}

ERRAND_NAME_PARTS = {
    "herb_gathering": {"nouns": ["Bloom", "Root", "Thicket", "Grove", "Garden"],
                       "suffixes": ["Foraging", "Harvest", "Gathering"]},
    "courier_run":    {"nouns": ["Parcel", "Letters", "Ledger", "Dispatch"],
                       "suffixes": ["Run", "Delivery", "Courier"]},
    "caravan_escort": {"nouns": ["Wagons", "Pilgrims", "Convoy", "Merchant Train"],
                       "suffixes": ["Escort", "Guard", "Watch"]},
    "scout_ruins":    {"nouns": ["Trail", "Horizon", "Ruins", "Signs"],
                       "suffixes": ["Recon", "Scouting", "Patrol"]},
    "monster_survey": {"nouns": ["Readings", "Anomaly", "Ley-Lines", "Wildlife"],
                       "suffixes": ["Survey", "Census", "Study"]},
}

# ── Mission templates ───────────────────────────────────────────────────────

ERRAND_TEMPLATES = {
    "herb_gathering": {
        "label": "foraging", "tag": "wis", "base_power": 12, "hours": (8, 12),
        "risk": 0, "gold": (25, 45), "exp": 18,
        "loot_pool": ["minor_healing_potion", "healing_salve", "antidote"],
    },
    "courier_run": {
        "label": "courier", "tag": "dex", "base_power": 14, "hours": (8, 14),
        "risk": 0, "gold": (30, 55), "exp": 20,
        "loot_pool": ["smoke_bomb", "flash_powder"],
    },
    "caravan_escort": {
        "label": "escort", "tag": "str", "base_power": 18, "hours": (12, 16),
        "risk": 1, "gold": (50, 80), "exp": 30,
        "loot_pool": ["healing_potion", "battle_drink"],
    },
    "scout_ruins": {
        "label": "scouting", "tag": "dex", "base_power": 20, "hours": (10, 16),
        "risk": 1, "gold": (45, 75), "exp": 28,
        "loot_pool": ["throwing_knife", "flash_powder"],
    },
    "monster_survey": {
        "label": "survey", "tag": "lrn", "base_power": 16, "hours": (10, 14),
        "risk": 1, "gold": (40, 65), "exp": 25,
        "loot_pool": ["mana_philter", "shadow_essence"],
    },
}

SWEEP_LOOT = {
    1: ["minor_healing_potion", "healing_salve", "antidote"],
    2: ["healing_potion", "iron_skin_potion", "battle_drink", "fire_bomb"],
    3: ["greater_healing_potion", "holy_water", "thunder_bomb", "acid_flask"],
    4: ["superior_healing_potion", "blessed_water", "mana_philter"],
    5: ["superior_healing_potion", "blessed_water", "mana_philter"],
    6: ["superior_healing_potion", "blessed_water", "mana_philter"],
}


def _only_existing(ids):
    """Filter a loot pool to item ids that actually exist in the ITEMS table."""
    return [i for i in ids if i in ITEMS]


ERRAND_TEMPLATES = {
    k: {**v, "loot_pool": _only_existing(v["loot_pool"])}
    for k, v in ERRAND_TEMPLATES.items()
}
SWEEP_LOOT = {k: _only_existing(v) for k, v in SWEEP_LOOT.items()}

# ── Outcome tables ──────────────────────────────────────────────────────────

OUTCOME_LABELS = {
    "great":    "Great Success",
    "success":  "Success",
    "partial":  "Partial Success",
    "failure":  "Failure",
    "disaster": "Disaster",
}

_OUTCOME_STRESS = {"great": -2, "success": 0, "partial": 3, "failure": 6, "disaster": 14}
_REWARD_MULT = {"great": 1.5, "success": 1.0, "partial": 0.5, "failure": 0.15, "disaster": 0.0}
_ITEM_ROLLS = {"great": (2, 3), "success": (1, 2), "partial": (0, 1), "failure": (0, 0), "disaster": (0, 0)}
_DAMAGE_PCT = {"great": (3, 10), "success": (8, 20), "partial": (18, 35),
               "failure": (30, 50), "disaster": (50, 75)}
_OUTCOME_LINES = {
    "great":    "A flawless run — they return early, barely dusty.",
    "success":  "The job is done. They come home tired but whole.",
    "partial":  "Half the job, all of the walk. They return with less to show.",
    "failure":  "It goes wrong out there. They limp home empty-handed.",
    "disaster": "It goes badly wrong. The walk home is a long one.",
}

# ── Level-based curves (locked design §3.12–3.15) ───────────────────────────

def star_for_power(power):
    if power <= 15:
        return 1
    if power <= 30:
        return 2
    if power <= 55:
        return 3
    if power <= 85:
        return 4
    if power <= 120:
        return 5
    return 6


def star_cap(house_level):
    """Max mission stars this house can administer (3/4/5/6 by band)."""
    return min(6, 3 + max(0, house_level - 1) // 2)


def slot_cap(house_level):
    """Concurrent dispatch slots: 1/2/2/3 across the house bands."""
    return 1 + (1 if house_level >= 3 else 0) + (1 if house_level >= 7 else 0)


def team_cap(house_level):
    """Max girls per mission: 2/3/4 across the house bands (min is 1)."""
    if house_level <= 2:
        return 2
    if house_level <= 6:
        return 3
    return 4


def offer_count(house_level):
    """Offers per refresh: 4/5/6/7 across the house bands."""
    return 4 + (house_level - 1) // 2


def offer_cycle(day):
    return (day - 1) // REFRESH_DAYS


def refresh_day(day):
    """Day the current offer cycle's board refreshes next."""
    return offer_cycle(day) * REFRESH_DAYS + REFRESH_DAYS + 1


# ── Stress / mood ───────────────────────────────────────────────────────────

def stress_band(stress):
    stress = int(stress)
    if stress >= 90:
        return "Burned Out"
    if stress >= 75:
        return "Frayed"
    if stress >= 50:
        return "Weary"
    if stress >= 25:
        return "Wound-Up"
    return "Calm"


def mood_of(girl, day):
    """Derived mood: (label, success modifier, refuses_dispatch)."""
    stress = int(girl.get("stress", 0))
    aff = int(girl.get("affection", 30))
    last = girl.get("last_dispatch") or {}
    recent = bool(last) and (day - int(last.get("day", 0))) <= 3

    if stress >= 90:
        return ("Burned Out", -15, True)
    if recent and last.get("outcome") == "disaster":
        return ("Discouraged", -12, False)
    if stress >= 75:
        return ("Weary", -9, False)
    if recent and last.get("outcome") == "great":
        return ("Inspired", 8, False)
    if stress >= 50:
        return ("Tired", -4, False)
    if aff >= 60:
        return ("Spirited", 5, False)
    return ("Steady", 0, False)


def adjust_stress(girl, delta):
    """Apply a stress change (clamped 0–100). Returns the new value."""
    new = max(0, min(100, int(girl.get("stress", 0)) + int(delta)))
    girl["stress"] = new
    return new


def affection_mod(girl):
    aff = int(girl.get("affection", 30))
    if girl.get("married"):
        return 8
    if aff >= 80:
        return 6
    if aff >= 60:
        return 4
    if aff >= 30:
        return 2
    return 0


# ── Girl record helpers ─────────────────────────────────────────────────────

def _girl_uid(girl):
    """Stable girl identity — must match house._girl_unique_id format."""
    return f"{girl.get('key', '')}:{girl.get('name', '')}"


def ensure_girl_combat_fields(girl):
    """Materialize the fields gain_exp_ally / ally_max_hp expect on a girl."""
    from combat.ally import compute_girl_attributes, _fix_level_hp_bonus
    girl["attributes"] = compute_girl_attributes(girl)
    girl["level_hp_bonus"] = _fix_level_hp_bonus(girl)
    girl.setdefault("level_cap", 10)
    girl.setdefault("exp", 0)
    girl.setdefault("learned_skills", [])
    girl.setdefault("upgrade_skills", [])
    girl.setdefault("skill_cooldowns", {})
    girl.setdefault("skill_mastery", {})


def girl_max_hp(girl):
    if girl.get("max_hp"):
        return int(girl["max_hp"])
    ensure_girl_combat_fields(girl)
    from combat.ally import ally_max_hp
    return ally_max_hp(girl)


def girl_hp(girl):
    hp = girl.get("current_hp")
    if hp is None:
        return girl_max_hp(girl)
    return max(1, int(hp))


def girl_status_line(girl, day):
    """One-line status used in the lounge and team select screens."""
    stress = int(girl.get("stress", 0))
    label, _mod, refuses = mood_of(girl, day)
    line = (f"HP {girl_hp(girl)}/{girl_max_hp(girl)} · "
            f"Stress {stress} ({stress_band(stress)}) · Mood: {label}")
    if refuses:
        line += " — refusing work"
    return line


def dispatch_return_text(player, girl):
    """'Away — returns Day X, HH:MM' when the girl is on a mission, else None."""
    mid = girl.get("dispatch_mission")
    if not mid:
        return None
    for inst in get_dispatch_state(player).get("active", []):
        if inst.get("instance_id") == mid:
            day, mins = divmod(int(inst.get("return_abs", 0)), 1440)
            return f"Away — returns Day {day}, {mins // 60:02d}:{mins % 60:02d}"
    return "Away on a dispatch"


def injured_text(girl, day):
    until = int(girl.get("injured_until", 0) or 0)
    if until > day:
        return f"Injured — recovering until Day {until}"
    return None


def eligible_girls(player, house):
    """Girls who can be sent out right now (home, healthy, not burned out)."""
    day = player.get("day", 1)
    out = []
    for g in house.get("monster_girls", []):
        if g.get("dispatch_mission"):
            continue
        if int(g.get("injured_until", 0) or 0) > day:
            continue
        if int(g.get("stress", 0)) >= 90:
            continue
        out.append(g)
    return out


def _find_girl(player, uid):
    for house in (player.get("houses") or {}).values():
        for g in house.get("monster_girls", []):
            if _girl_uid(g) == uid:
                return g
    for a in player.get("allies", []):
        if _girl_uid(a) == uid:
            return a
    return None


def get_dispatch_state(player):
    """Return (and repair) the player's dispatch state dict."""
    d = player.get("dispatch")
    if not isinstance(d, dict):
        d = {}
        player["dispatch"] = d
    d.setdefault("active", [])
    d.setdefault("reports", [])
    d.setdefault("completed", 0)
    d.setdefault("offers", [])
    d.setdefault("offers_cycle", -1)
    return d


def sanitize_flags(player, house=None):
    """Clear stale busy flags whose mission is no longer tracked."""
    known = {i.get("instance_id") for i in get_dispatch_state(player).get("active", [])}
    houses = [house] if house else list((player.get("houses") or {}).values())
    for h in houses:
        if not h:
            continue
        for g in h.get("monster_girls", []):
            mid = g.get("dispatch_mission")
            if mid and mid not in known:
                g.pop("dispatch_mission", None)


def board_label(player):
    d = get_dispatch_state(player)
    act = len(d.get("active", []))
    rep = len(d.get("reports", []))
    parts = []
    if act:
        parts.append(f"{act} away")
    if rep:
        parts.append(f"{rep} report" + ("s" if rep != 1 else ""))
    return "Dispatch board" + (f" ({', '.join(parts)})" if parts else "")


# ── Offers ──────────────────────────────────────────────────────────────────

def _global_max_floor(player):
    best = int(player.get("max_floor", 1) or 1)
    for cf in (player.get("city_floors") or {}).values():
        best = max(best, int(cf.get("max_floor", 1) or 1))
    return best


def _roll_sweep_name(biome, stars):
    adj = random.choice(STAR_ADJECTIVES[stars])
    noun = random.choice(get_theme(biome)["ruins"])
    suffix = random.choice(SWEEP_SUFFIXES[stars])
    return f"{adj} {noun} {suffix}"


def _roll_errand_name(subtype, stars):
    parts = ERRAND_NAME_PARTS[subtype]
    adj = random.choice(STAR_ADJECTIVES[stars])
    noun = random.choice(parts["nouns"])
    suffix = random.choice(parts["suffixes"])
    return f"{adj} {noun} {suffix}"


def _make_errand(player, subtype, global_max, day, idx, home_city):
    base = ERRAND_TEMPLATES[subtype]
    scale = 1 + 0.15 * max(0, global_max - 10)
    power = int(round(base["base_power"] * scale))
    stars = star_for_power(power)
    gmin, gmax = base["gold"]
    return {
        "id": f"errand_{subtype}_{home_city}_{day}_{idx}",
        "kind": "errand",
        "subtype": subtype,
        "name": _roll_errand_name(subtype, stars),
        "stars": stars,
        "power": power,
        "risk": base["risk"],
        "tag": base["tag"],
        "hours": random.randint(*base["hours"]),
        "gold_min": int(gmin * scale),
        "gold_max": int(gmax * scale),
        "exp": int(base["exp"] * scale),
        "loot_pool": list(base["loot_pool"]),
        "floors": None,
        "label": base["label"],
    }


def _make_sweep(top, biome, day, idx, home_city):
    power = int(6 + 2.2 * top)
    stars = star_for_power(power)
    risk = 1 if top < 10 else 2 if top < 25 else 3
    return {
        "id": f"sweep_{home_city}_{top}_{day}_{idx}",
        "kind": "sweep",
        "subtype": None,
        "name": _roll_sweep_name(biome, stars),
        "stars": stars,
        "power": power,
        "risk": risk,
        "tag": "str",
        "hours": random.randint(18, 36),
        "gold_min": 25 + 10 * top,
        "gold_max": 40 + 14 * top,
        "exp": 10 + 4 * top,
        "loot_pool": list(SWEEP_LOOT.get(min(6, max(1, stars)), [])),
        "floors": (max(1, top - 3), top),
        "label": "sweep",
    }


def generate_offers(player, home_city, house):
    """Roll a fresh board for the current 3-day cycle."""
    day = player.get("day", 1)
    level = house.get("level", 1) if house else 1
    count = offer_count(level)
    cap = star_cap(level)
    global_max = _global_max_floor(player)
    biome = CITIES.get(home_city, {}).get("biome", "temperate")

    offers = []

    # 2 errands are guaranteed (the safe options).
    for idx, subtype in enumerate(random.sample(list(ERRAND_TEMPLATES), 2)):
        offers.append(_make_errand(player, subtype, global_max, day, idx, home_city))

    # The rest are sweeps from cleared floor bands, capped by the house limit.
    max_floor = int((player.get("city_floors") or {}).get(home_city, {}).get(
        "max_floor", player.get("max_floor", 1)) or 1)
    used_tops = set()
    for idx in range(count - 2):
        top = max(1, max_floor - 4 * idx)
        while top > 1 and star_for_power(int(6 + 2.2 * top)) > cap:
            top = max(1, top - 4)
        stars = star_for_power(int(6 + 2.2 * top))
        if stars > cap or top in used_tops:
            # No sweep fits the house cap — offer another errand instead.
            offers.append(_make_errand(player, random.choice(list(ERRAND_TEMPLATES)),
                                       global_max, day, idx + 10, home_city))
            continue
        used_tops.add(top)
        offers.append(_make_sweep(top, biome, day, idx, home_city))

    return offers


def ensure_offers(player, home_city, house):
    """Return this cycle's offers, regenerating when the cycle rolls over."""
    d = get_dispatch_state(player)
    cycle = offer_cycle(player.get("day", 1))
    # An empty list is a valid state (board cleared out) — regenerate only
    # when the 3-day cycle rolls over, never because the offers ran out.
    if isinstance(d.get("offers"), list) and d.get("offers_cycle") == cycle:
        return d["offers"]
    d["offers"] = generate_offers(player, home_city, house)
    d["offers_cycle"] = cycle
    return d["offers"]


# ── Success math ────────────────────────────────────────────────────────────

def _mission_power(girl, tag):
    ensure_girl_combat_fields(girl)
    attrs = girl.get("attributes", {})
    top = max(attrs, key=attrs.get) if attrs else None
    mult = 1.15 if top == tag else 1.0
    return int(girl.get("level", 1)) * mult


def success_chance_for(offer, girls, day):
    """Projected success chance (10–95) for a team and mission."""
    if not girls:
        return 10
    team_power = sum(_mission_power(g, offer.get("tag")) for g in girls)
    ratio = team_power / max(1, int(offer.get("power", 1)))
    base = 50 + 55 * (ratio - 1)
    mood = sum(mood_of(g, day)[1] for g in girls) / len(girls)
    aff = sum(affection_mod(g) for g in girls) / len(girls)
    leader = 3 if max(int(g.get("level", 1)) for g in girls) >= 0.6 * int(offer.get("power", 1)) else 0
    consec = min(6, sum(2 for g in girls if int(g.get("consecutive_dispatch", 0)) >= 2))
    chance = base + mood + aff + leader - consec - 2 * int(offer.get("risk", 0))
    return int(max(10, min(95, round(chance))))


def _roll_outcome(roll, chance, risk):
    if roll <= chance - 25:
        return "great"
    if roll <= chance:
        return "success"
    if roll <= chance + 15:
        return "partial"
    if (roll > chance + 25) or (roll >= 97 and risk >= 2):
        return "disaster"
    return "failure"


# ── Launch ──────────────────────────────────────────────────────────────────

def _now_abs(player):
    return int(player.get("day", 1)) * 1440 + int(player.get("time_minutes", 0))


def _journal(player, name, desc):
    from events import ensure_journal
    ensure_journal(player)
    player["journal"]["events"].append({
        "day": player.get("day", 1),
        "name": name,
        "desc": desc,
        "tag": "[DISPATCH]",
        "fixed": False,
    })


def create_instance(player, home_city, house, offer, girls):
    """Launch a mission. Returns (instance, message) or (None, error)."""
    d = get_dispatch_state(player)
    level = house.get("level", 1) if house else 1
    day = player.get("day", 1)

    if len(d["active"]) >= slot_cap(level):
        return None, "All dispatch slots are in use — wait for a team to return."
    if not (1 <= len(girls) <= team_cap(level)):
        return None, f"Pick between 1 and {team_cap(level)} girls for this mission."
    for g in girls:
        if g.get("dispatch_mission"):
            return None, f"{display_name(g)} is already away on a dispatch."
        if int(g.get("injured_until", 0) or 0) > day:
            return None, f"{display_name(g)} is injured and can't go."
        if int(g.get("stress", 0)) >= 90:
            return None, f"{display_name(g)} is burned out and refuses to go."

    inst_id = f"{offer['id']}#{random.randint(1000, 9999)}"
    for g in girls:
        ensure_girl_combat_fields(g)
        last_day = int(g.get("last_dispatch_day", 0) or 0)
        if last_day and (day - last_day) <= 1:
            g["consecutive_dispatch"] = int(g.get("consecutive_dispatch", 0)) + 1
        else:
            g["consecutive_dispatch"] = 1
        g["dispatch_mission"] = inst_id

    now = _now_abs(player)
    inst = {
        "instance_id": inst_id,
        "template_id": offer["id"],
        "name": offer["name"],
        "kind": offer["kind"],
        "subtype": offer.get("subtype"),
        "city_id": home_city,
        "girls": [_girl_uid(g) for g in girls],
        "girl_names": [display_name(g) for g in girls],
        "start_abs": now,
        "return_abs": now + int(offer["hours"]) * 60,
        "power": int(offer["power"]),
        "risk": int(offer["risk"]),
        "tag": offer.get("tag"),
        "stars": int(offer.get("stars", 1)),
        "gold_min": int(offer.get("gold_min", 0)),
        "gold_max": int(offer.get("gold_max", 0)),
        "exp": int(offer.get("exp", 0)),
        "loot_pool": list(offer.get("loot_pool", [])),
        "resolved": False,
    }
    d["active"].append(inst)

    # Consume the offer: a launched mission leaves the board until the next
    # 3-day refresh, so the same listing can't be run infinitely.
    d["offers"] = [o for o in d.get("offers", []) if o.get("id") != offer.get("id")]

    ret_day, ret_mins = divmod(inst["return_abs"], 1440)
    _journal(player, f"Dispatch launched: {inst['name']}",
             f"{', '.join(inst['girl_names'])} set out — expected back Day {ret_day}, "
             f"{ret_mins // 60:02d}:{ret_mins % 60:02d}.")
    return inst, f"{', '.join(inst['girl_names'])} set out on \"{inst['name']}\"."


# ── Time progression (hooked from utils.advance_time) ───────────────────────

def _night_tick(player, days):
    """Nightly recovery for housed, off-duty girls (one tick per day passed)."""
    houses = list((player.get("houses") or {}).values())
    for _ in range(max(0, int(days))):
        for house in houses:
            level = int(house.get("level", 1))
            decay = 5 + min(level, 6) + 2  # base nightly rest + full idle day
            for g in house.get("monster_girls", []):
                if g.get("dispatch_mission"):
                    continue  # away on duty — no rest
                adjust_stress(g, -decay)
                g["consecutive_dispatch"] = 0
                hp = g.get("current_hp")
                if hp is not None:
                    max_hp = girl_max_hp(g)
                    if int(hp) < max_hp:
                        g["current_hp"] = min(max_hp, int(hp) + max(1, max_hp // 4))


def process_dispatch_progress(player, days_passed=0):
    """Resolve returned missions and tick nightly recovery.

    Called from ``utils.advance_time`` on every advance (resolution is
    hour-precise); recovery ticks only for full days that passed.
    """
    d = player.get("dispatch")
    if not isinstance(d, dict):
        return

    if days_passed:
        _night_tick(player, days_passed)

    actives = d.get("active") or []
    if not actives:
        return

    now = _now_abs(player)
    done = [i for i in actives if not i.get("resolved") and now >= int(i.get("return_abs", 0))]
    if not done:
        return

    for inst in done:
        _resolve(player, inst)
        inst["resolved"] = True
    d["active"] = [i for i in actives if not i.get("resolved")]


def _resolve(player, inst):
    """Roll the outcome, apply stress/HP damage, and file a report."""
    d = get_dispatch_state(player)
    day = player.get("day", 1)
    girls = [g for g in (_find_girl(player, uid) for uid in inst.get("girls", [])) if g]

    chance = success_chance_for(inst, girls, day) if girls else 20
    roll = random.randint(1, 100)
    outcome = _roll_outcome(roll, chance, int(inst.get("risk", 0)))

    base_stress = 2 if inst.get("kind") == "errand" else 3 + 2 * int(inst.get("risk", 0))
    stress_delta = base_stress + _OUTCOME_STRESS[outcome]
    mult = _REWARD_MULT[outcome]

    gold = int(random.randint(int(inst.get("gold_min", 0)), int(inst.get("gold_max", 0))) * mult)
    favor = {"great": 2, "success": 1}.get(outcome, 0) if inst.get("kind") == "sweep" else 0

    item_ids = []
    rolls = _ITEM_ROLLS[outcome]
    if rolls[1] > 0 and inst.get("loot_pool"):
        for _ in range(random.randint(*rolls)):
            item_ids.append(random.choice(inst["loot_pool"]))

    girl_results = []
    exp_entries = []
    for g in girls:
        ensure_girl_combat_fields(g)
        max_hp = girl_max_hp(g)
        lo, hi = _DAMAGE_PCT[outcome]
        pct = random.uniform(lo, hi) / 100.0
        if inst.get("kind") == "errand":
            pct *= 0.4
        pct *= 1 + 0.1 * int(inst.get("risk", 0))
        pct *= 1 + int(g.get("stress", 0)) / 150.0
        dmg = max(1, int(max_hp * pct))

        hp = girl_hp(g)
        downed = False
        if hp - dmg <= 0:
            new_hp = 1
            downed = True
            g["injured_until"] = day + 2
            adjust_stress(g, 20)
        else:
            new_hp = hp - dmg
        g["current_hp"] = new_hp
        adjust_stress(g, stress_delta)
        g["last_dispatch"] = {"outcome": outcome, "day": day}
        g["last_dispatch_day"] = day
        g.pop("dispatch_mission", None)

        exp_amount = int(int(inst.get("exp", 0)) * mult)
        if exp_amount > 0:
            exp_entries.append({"uid": _girl_uid(g), "amount": exp_amount})

        girl_results.append({
            "uid": _girl_uid(g), "name": display_name(g),
            "hp_lost": dmg, "downed": downed,
            "stress_after": int(g.get("stress", 0)),
        })

    lines = [f"{', '.join(inst.get('girl_names', []))} — {_OUTCOME_LINES[outcome]}"]
    for r in girl_results:
        if r["downed"]:
            lines.append(f"{r['name']} was carried home — Downed, recovering until Day {day + 2}.")
        elif r["hp_lost"] > 0:
            lines.append(f"{r['name']} is hurt (−{r['hp_lost']} HP).")

    report = {
        "instance_id": inst["instance_id"],
        "name": inst["name"],
        "kind": inst.get("kind"),
        "stars": int(inst.get("stars", 1)),
        "city_id": inst.get("city_id"),
        "outcome": outcome,
        "day": day,
        "gold": gold,
        "favor": favor,
        "items": item_ids,
        "exp": exp_entries,
        "girls": girl_results,
        "lines": lines,
    }
    reports = d.setdefault("reports", [])
    reports.append(report)
    while len(reports) > REPORT_CAP:
        reports.pop(0)
    d["completed"] = int(d.get("completed", 0)) + 1

    _journal(player, f"Dispatch returned: {inst['name']}",
             f"{', '.join(inst.get('girl_names', []))} — {OUTCOME_LABELS[outcome]}. "
             "Collect the report at the dispatch board.")


# ── Collection (house UI) ───────────────────────────────────────────────────

def collect_reports(player, home_city, house):
    """Grant all report rewards: gold, favor, items, and per-girl EXP."""
    from gui.terminal import term

    d = get_dispatch_state(player)
    reports = d.get("reports") or []
    if not reports:
        term.print("No dispatch reports to collect.")
        term.pause()
        return

    for rep in reports:
        term.print("─" * 46)
        term.print(f"{'★' * int(rep.get('stars', 1))} {rep['name']} — {OUTCOME_LABELS.get(rep.get('outcome'), '?')}")
        for line in rep.get("lines", []):
            term.print("  " + line)

        gold = int(rep.get("gold", 0))
        if gold:
            player["gold"] = player.get("gold", 0) + gold
            term.print(f"  +{gold} gold")

        favor = int(rep.get("favor", 0))
        if favor:
            player.setdefault("favor", {})
            player["favor"][home_city] = player["favor"].get(home_city, 0) + favor
            city_name = CITIES.get(home_city, {}).get("name", home_city)
            term.print(f"  +{favor} {city_name} Favor")

        for iid in rep.get("items", []):
            from resources.items import build_item
            from inventory import add_item_to_inventory
            item = build_item(iid)
            if add_item_to_inventory(player, item):
                term.print(f"  + {item['name']}")
            else:
                from facilities.house import _house_level_data
                storage = house.setdefault("storage", [])
                cap = _house_level_data(house)["storage_cap"]
                if len(storage) < cap:
                    storage.append(item)
                    term.print(f"  + {item['name']} (bag full — stored in the house chest)")
                else:
                    term.print(f"  ! {item['name']} left behind — no space")

        for entry in rep.get("exp", []):
            girl = _find_girl(player, entry["uid"])
            if not girl:
                continue
            ensure_girl_combat_fields(girl)
            from leveling import gain_exp_ally
            leveled = gain_exp_ally(girl, entry["amount"])
            suffix = " — level up!" if leveled else ""
            term.print(f"  {display_name(girl)} gains {entry['amount']} EXP{suffix}")

    d["reports"] = []
    term.pause()
