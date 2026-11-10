"""facilities/house_stories.py — Fireside Tales (house story reader).

Stories live in ``resources/house_stories.py`` (pure data). This module owns
the runtime: roster evaluation, requirement gating, the house menu screen,
effects, Journal entries, and city-trigger delivery.

Design: docs/house_stories_design.md

Reading happens through ``term`` (FacilityScreen / StoryScreen), so it is
safe inside the house facility thread and inside a city StoryScreen overlay.
Progress lives in ``player["house_stories"]["seen"]`` (part id -> day).
"""

from resources.house_stories import (
    HOUSE_STORIES,
    SUPERBOSS_LABELS,
    ensure_state as ensure_house_story_state,
    get_part,
    iter_story_parts,
    merge_requirements,
    requirement_labels,
)
from resources.cities import CITIES
from gui.terminal import term
from utils import display_name


# ── Roster helpers ───────────────────────────────────────────────────────────

def _girl_uid(girl):
    return f"{girl.get('key', '')}:{girl.get('name', '')}"


def all_owned_girls(player):
    """Return {uid: live girl dict} across party, all houses and WL benches.

    Live references are important: affection/stress changes must land in the
    actual list the house and party menus read.
    """
    owned = {}
    collections = [
        player.get("allies", []),
        player.get("wonderland_benched_allies", []),
    ]
    for house in (player.get("houses") or {}).values():
        collections.append(house.get("monster_girls", []))

    for group in collections:
        for girl in group or []:
            if not isinstance(girl, dict):
                continue
            owned.setdefault(_girl_uid(girl), girl)
    return owned


def find_girl(player, key):
    """Return the live record for the first owned girl with ``key``."""
    if not key:
        return None
    for girl in all_owned_girls(player).values():
        if girl.get("key") == key:
            return girl
    return None


def _girl_affection(girl):
    return int(girl.get("affection", 30) or 0)


def _qualifying_girls(player, req):
    """Owned girls meeting the affection threshold (featured girl included)."""
    threshold = int(req.get("affection", 0) or 0)
    return [g for g in all_owned_girls(player).values()
            if _girl_affection(g) >= threshold]


def _max_house_level(player):
    levels = [int(h.get("level", 1) or 1)
              for h in (player.get("houses") or {}).values()]
    return max(levels) if levels else 0


def _married_count(player, girls):
    recorded = player.get("married_girls") or []
    if recorded:
        return len(recorded)
    return sum(1 for g in girls if g.get("married"))


def _quest_flags(player):
    return (player.get("quests") or {}).get("flags") or {}


def _has_flag(player, flag):
    """Check quest flags and top-level story flags (recruitment, boss kills)."""
    return bool(_quest_flags(player).get(flag) or player.get(flag))


# Some superbosses write a top-level defeat flag but may predate the shared
# ``defeated_superbosses`` ledger. Accept either source.
SUPERBOSS_FLAG_FALLBACKS = {
    "chromatic_artisan": "boss_defeated_palette",
    "white_knight": "boss_defeated_white_knight",
    "entangled_chrysalis": "boss_defeated_chrysalis",
    "wl_queen_of_hearts": "wl_boss_defeated_queen_of_hearts",
    "wl_big_bad_wolf": "wl_boss_defeated_big_bad_wolf",
    "wl_wicked_witch": "wl_boss_defeated_wicked_witch",
    "wl_jabberwock": "wl_boss_defeated_jabberwock",
    "wl_mary_sue": "wl_boss_defeated_mary_sue",
}


def _superboss_defeated(player, boss_id):
    if boss_id in (player.get("defeated_superbosses") or []):
        return True
    flag = SUPERBOSS_FLAG_FALLBACKS.get(boss_id)
    return bool(flag and _has_flag(player, flag))


def _phase_now(player):
    try:
        import time_blocks
        return time_blocks.get_day_phase(player)
    except Exception:
        return "morning"


# ── Requirement evaluation ───────────────────────────────────────────────────

def requirement_status(player, req):
    """Return (met, missing_lines) with progress numbers where useful."""
    missing = []

    featured_key = req.get("girl")
    qualifying = _qualifying_girls(player, req)
    girls_needed = int(req.get("girls", 0) or 0)
    affection = int(req.get("affection", 0) or 0)
    designated_keys = req.get("girl_keys") or []
    if isinstance(designated_keys, str):
        designated_keys = [designated_keys]

    checked_keys = set()
    if featured_key:
        checked_keys.add(featured_key)
        girl = find_girl(player, featured_key)
        if girl is None:
            missing.append(f"{featured_key.replace('_', ' ').title()} in your household")
        elif affection and _girl_affection(girl) < affection:
            missing.append(f"{display_name(girl)}'s affection "
                           f"{_girl_affection(girl)}/{affection}")

    # Designated allies (plural) must be owned; affection applies to each.
    for key in designated_keys:
        if key in checked_keys:
            continue
        checked_keys.add(key)
        girl = find_girl(player, key)
        if girl is None:
            missing.append(f"{key.replace('_', ' ').title()} in your household")
        elif affection and _girl_affection(girl) < affection:
            missing.append(f"{display_name(girl)}'s affection "
                           f"{_girl_affection(girl)}/{affection}")

    if girls_needed and len(qualifying) < girls_needed:
        if affection:
            missing.append(f"{len(qualifying)}/{girls_needed} companions at "
                           f"{affection}+ affection")
        else:
            missing.append(f"{len(qualifying)}/{girls_needed} companions in the house")
    elif affection and not featured_key and not designated_keys and not qualifying:
        missing.append(f"a companion at {affection}+ affection")

    married_needed = int(req.get("married", 0) or 0)
    if married_needed:
        married = _married_count(player, list(all_owned_girls(player).values()))
        if married < married_needed:
            missing.append(f"{married}/{married_needed} married companions")

    house_needed = int(req.get("house_level", 0) or 0)
    if house_needed and _max_house_level(player) < house_needed:
        missing.append(f"house level {_max_house_level(player)}/{house_needed}")

    for flag in req.get("flags") or []:
        if not _has_flag(player, flag):
            missing.append(requirement_labels({"flags": [flag]})[0])

    bosses = req.get("superbosses") or []
    if isinstance(bosses, str):
        bosses = [bosses]
    for boss in bosses:
        if not _superboss_defeated(player, boss):
            name = SUPERBOSS_LABELS.get(boss, boss.replace("_", " "))
            missing.append(f"having defeated {name}")

    return (not missing, missing)


def requirements_met(player, req):
    return requirement_status(player, req)[0]


# ── Story progression ────────────────────────────────────────────────────────

def _seen_parts(player):
    return ensure_house_story_state(player)["seen"]


def seen_part(player, part_id):
    return part_id in _seen_parts(player)


def next_part(player, story):
    """Return (number, part) for the first unseen part, or (0, None)."""
    seen = _seen_parts(player)
    for number, part in iter_story_parts(story):
        if part.get("id") not in seen:
            return number, part
    return 0, None


def story_status(player, story, city_id=None):
    """Evaluate one arc for the menu.

    state: "ready" | "locked" | "elsewhere" | "waiting" | "complete"
    """
    total = len(story.get("parts", []))
    seen_count = sum(1 for _, part in iter_story_parts(story)
                     if part.get("id") in _seen_parts(player))
    number, part = next_part(player, story)
    if part is None:
        return {"state": "complete", "seen": seen_count, "total": total,
                "next_part": None, "next_number": 0, "missing": []}

    req = merge_requirements(story, part)
    met, missing = requirement_status(player, req)
    info = {"state": "locked", "seen": seen_count, "total": total,
            "next_part": part, "next_number": number, "missing": missing}

    trigger = part.get("trigger") or {}
    if trigger.get("type") == "city":
        target = trigger.get("city")
        if target and target != "any" and city_id and target != city_id:
            info["state"] = "elsewhere"
            info["city_name"] = CITIES.get(target, {}).get("name", target.title())
            return info
        if target and target != "any" and not city_id:
            info["state"] = "elsewhere"
            info["city_name"] = CITIES.get(target, {}).get("name", target.title())
            return info
        phase = trigger.get("phase")
        if phase and _phase_now(player) != phase:
            info["state"] = "waiting"
            info["phase"] = phase
            return info

    if met:
        info["state"] = "ready"
    return info


def _trigger_matches_city(part, city_id, phase_now):
    trigger = part.get("trigger") or {}
    if trigger.get("type") != "city":
        return False
    target = trigger.get("city")
    if target and target != "any" and target != city_id:
        return False
    wanted_phase = trigger.get("phase")
    if wanted_phase and wanted_phase != phase_now:
        return False
    return True


def claim_city_trigger(player, city_id):
    """Return the next eligible city-triggered part, or None.

    Called on city entry. A part is eligible when it is the arc's next unseen
    part, its trigger matches this city (and phase), and its requirements pass.
    """
    if not city_id:
        return None
    phase_now = _phase_now(player)
    for story in HOUSE_STORIES.values():
        number, part = next_part(player, story)
        if part is None:
            continue
        if not _trigger_matches_city(part, city_id, phase_now):
            continue
        if requirements_met(player, merge_requirements(story, part)):
            return part
    return None


def available_ready_count(player, city_id=None):
    """Number of arcs whose next part can be read right now (house badge)."""
    return sum(1 for story in HOUSE_STORIES.values()
               if story_status(player, story, city_id)["state"] == "ready")


# ── Effects & Journal ────────────────────────────────────────────────────────

def _affection_cap(player, girl):
    cap = int(girl.get("affection_cap", 200) or 200)
    uid = _girl_uid(girl)
    engaged = player.get("engaged_girls") or []
    married = player.get("married_girls") or []
    if girl.get("engaged") or girl.get("married"):
        cap = max(cap, 200)
    for entry in engaged + married:
        if entry in (uid, girl.get("key"), f"{girl.get('key')}:{girl.get('nickname', '')}"):
            cap = max(cap, 200)
    return cap


def _add_affection(player, girl, amount):
    if not amount:
        return None
    cap = _affection_cap(player, girl)
    before = _girl_affection(girl)
    girl["affection"] = max(0, min(cap, before + int(amount)))
    return (f"{display_name(girl)}'s affection {int(amount):+d} "
            f"(now {girl['affection']}/{cap}).")


def _add_stress(girl, amount):
    if not amount:
        return None
    before = int(girl.get("stress", 0) or 0)
    girl["stress"] = max(0, min(100, before + int(amount)))
    return f"{display_name(girl)}'s stress {int(amount):+d} (now {girl['stress']})."


def _effect_targets(player, story, part, req):
    featured = story.get("girl") or req.get("girl")
    if featured:
        girl = find_girl(player, featured)
        return [girl] if girl else []

    keys = req.get("girl_keys") or []
    if isinstance(keys, str):
        keys = [keys]
    if keys:
        targets = []
        for key in keys:
            girl = find_girl(player, key)
            if girl is not None:
                targets.append(girl)
        return targets

    return _qualifying_girls(player, req)


def _bulk_affection(player, girls, amount):
    """Apply affection to many girls, returning how many actually changed."""
    changed = 0
    for girl in girls:
        before = _girl_affection(girl)
        _add_affection(player, girl, amount)
        if _girl_affection(girl) != before:
            changed += 1
    return changed


def _bulk_stress(girls, amount):
    """Apply stress to many girls, returning how many actually changed."""
    changed = 0
    for girl in girls:
        before = int(girl.get("stress", 0) or 0)
        _add_stress(girl, amount)
        if int(girl.get("stress", 0) or 0) != before:
            changed += 1
    return changed


def apply_effects(player, story, part):
    """Apply a part's effects; return player-facing messages."""
    effects = part.get("effects") or {}
    if not effects:
        return []

    req = merge_requirements(story, part)
    targets = _effect_targets(player, story, part, req)
    messages = []

    featured = story.get("girl") or req.get("girl")
    affection_targets = targets if not featured else targets[:1]

    # Featured/general affection: one message per girl when the target set is
    # a single companion (romance arcs), otherwise aggregate.
    single_affection = int(effects.get("affection", 0) or 0)
    if single_affection:
        if featured or len(affection_targets) == 1:
            for girl in affection_targets:
                msg = _add_affection(player, girl, single_affection)
                if msg:
                    messages.append(msg)
        else:
            changed = _bulk_affection(player, affection_targets, single_affection)
            if changed:
                messages.append(f"Household affection {single_affection:+d} "
                                f"({changed} companions).")

    # Ensemble affection: aggregate so a large household doesn't flood the log.
    all_targets = _qualifying_girls(player, req)
    bulk_affection = int(effects.get("affection_all", 0) or 0)
    if bulk_affection:
        changed = _bulk_affection(player, all_targets, bulk_affection)
        if changed:
            messages.append(f"Household affection {bulk_affection:+d} "
                            f"({changed} companions).")

    stress_amount = int(effects.get("stress", 0) or 0)
    if stress_amount:
        stress_targets = affection_targets
        if featured or len(stress_targets) == 1:
            for girl in stress_targets:
                msg = _add_stress(girl, stress_amount)
                if msg:
                    messages.append(msg)
        else:
            changed = _bulk_stress(stress_targets, stress_amount)
            if changed:
                messages.append(f"Household stress {stress_amount:+d} "
                                f"({changed} companions).")

    gold = int(effects.get("gold", 0) or 0)
    if gold:
        player["gold"] = int(player.get("gold", 0) or 0) + gold
        messages.append(f"You receive {gold} gold.")

    xp = int(effects.get("xp", 0) or 0)
    if xp:
        try:
            from leveling import gain_exp
            gain_exp(player, xp)
        except Exception:
            pass
        messages.append(f"You gain {xp} XP.")

    for entry in effects.get("items") or []:
        try:
            from resources.items import build_item
            from inventory import add_item_to_inventory
            item = build_item(entry["id"])
            item["count"] = int(entry.get("count", 1) or 1)
            if add_item_to_inventory(player, item):
                messages.append(f"Received {item.get('name', entry['id'])}.")
        except Exception:
            pass

    return messages


def _record_story_event(player, story, part):
    journal = player.setdefault("journal", {})
    events = journal.setdefault("events", [])
    day = player.get("day", 1)
    name = f"Story: {story.get('title')} — {part.get('title')}"
    for existing in events:
        if existing.get("day") == day and existing.get("name") == name:
            return
    events.append({
        "day": day,
        "name": name,
        "desc": story.get("summary", ""),
        "tag": "[STORY]",
        "fixed": False,
    })


# ── Rendering ────────────────────────────────────────────────────────────────

def _join_names(names):
    if not names:
        return "the household"
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f"{names[0]} and {names[1]}"
    return ", ".join(names[:3]) + ", and the others"


def _format_tokens(text, player, story, part):
    req = merge_requirements(story, part)
    targets = _effect_targets(player, story, part, req)
    names = [display_name(g) for g in targets]
    girl = names[0] if names else "she"
    return (text.replace("{player}", player.get("name", "you"))
                .replace("{girls}", _join_names(names))
                .replace("{girl}", girl))


def render_part(player, story, part, number):
    """Print a part's prose with Continue pauses between paragraphs."""
    term.clear()
    term.print("═" * 68)
    term.print(f"  {story.get('title', 'Story').upper()} — PART {number}")
    term.print(f"  {part.get('title', '')}")
    term.print("═" * 68)
    for paragraph in part.get("lines", []):
        term.print("")
        for line in paragraph.split("\n"):
            term.print(line)
        term.pause("Continue")


def play_part(player, part_id, replay=False, city_id=None):
    """Read one story part. Marks progress/effects once, then renders.

    Returns True when the part was found and readable.
    """
    story_id, story, number, part = get_part(part_id)
    if story is None:
        term.print("That story has gone quiet.")
        term.pause()
        return False

    req = merge_requirements(story, part)
    if not replay:
        met, missing = requirement_status(player, req)
        if not met:
            term.print("Not yet — this story is still waiting on:")
            for line in missing:
                term.print(f"  · {line}")
            term.pause()
            return False

        trigger = part.get("trigger") or {}
        if trigger.get("type") == "city":
            target = trigger.get("city")
            if target and target != "any" and city_id and target != city_id:
                term.print("This thread waits somewhere else.")
                term.pause()
                return False

        # Mark progress before rendering (early-close safe, like the
        # Archivist intro). Effects land once, with the progress mark.
        ensure_house_story_state(player)["seen"][part_id] = player.get("day", 1)
        messages = apply_effects(player, story, part)
        _record_story_event(player, story, part)
    else:
        messages = []

    render_part(player, story, part, number)

    if messages:
        term.print("")
        for message in messages:
            term.print(message)
        term.pause("Continue")

    if not replay:
        try:
            from save_load import save_game
            save_game(player)
        except Exception:
            pass  # never block a story on a save hiccup

    return True


# ── House menu screens ───────────────────────────────────────────────────────

def _story_option_label(story, info):
    title = story.get("title", "Story")
    state = info["state"]
    if state == "complete":
        return f"{title} — ✓ complete (re-read)"
    if state == "elsewhere":
        return f"{title} — 📍 waits in {info.get('city_name', 'another city')}"
    if state == "waiting":
        return f"{title} — 🕯 waits for {info.get('phase', 'the right time')}"
    if state == "ready":
        return (f"{title} — Part {info['next_number']}/{info['total']}: "
                f"{info['next_part'].get('title', '')}  ▶")
    missing = info.get("missing") or []
    return f"{title} — 🔒 {missing[0] if missing else 'requirements unmet'}"


def _story_detail(player, story, info):
    term.clear()
    term.print("═" * 68)
    term.print(f"  {story.get('title', 'Story')}")
    term.print("═" * 68)
    term.print(story.get("summary", ""))
    term.print("")
    term.print(f"Parts read: {info['seen']}/{info['total']}")
    if info["state"] == "complete":
        term.print("Every part of this story has been read. It is yours to keep.")
    elif info["state"] == "elsewhere":
        term.print(f"The next thread waits in {info.get('city_name', 'another city')}.")
    elif info["state"] == "waiting":
        term.print(f"The next thread waits for {info.get('phase', 'the right time')}.")
    else:
        term.print("Still locked. It needs:")
        for line in info.get("missing") or []:
            term.print(f"  · {line}")
    term.pause()


def _replay_menu(player, story):
    seen = _seen_parts(player)
    options = []
    part_ids = []
    for number, part in iter_story_parts(story):
        if part.get("id") in seen:
            options.append(f"Part {number}: {part.get('title', '')}")
            part_ids.append(part.get("id"))
    if not options:
        return
    options.append("Back")
    choice = term.menu(options, prompt="Re-read which part?",
                       allow_cancel=True, cancel_label="Back")
    if 0 <= choice < len(part_ids):
        play_part(player, part_ids[choice], replay=True)


def house_storybook(player, city_id):
    """Entry point from the house menu ("Fireside Tales")."""
    while True:
        term.clear()
        term.print("═" * 68)
        term.print("  FIRESIDE TALES")
        term.print("═" * 68)
        term.print("The house keeps its own stories. Some wait for company;")
        term.print("some wait for the right moment to find you.")
        term.print("")

        options = []
        actions = []
        for story in HOUSE_STORIES.values():
            info = story_status(player, story, city_id)
            options.append(_story_option_label(story, info))
            actions.append(("story", story, info))

        options.append("Back")
        actions.append(("back", None, None))

        choice = term.menu(options, prompt="Which story?",
                           allow_cancel=True, cancel_label="Back")
        if choice < 0 or choice >= len(actions):
            return

        kind, story, info = actions[choice]
        if kind == "back":
            return
        if info["state"] == "ready":
            play_part(player, info["next_part"]["id"], city_id=city_id)
        elif info["state"] == "complete":
            _replay_menu(player, story)
        else:
            _story_detail(player, story, info)
