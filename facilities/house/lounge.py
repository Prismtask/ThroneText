"""facilities/house/lounge.py — the House Lounge.

The lounge owns every girl-interaction menu: the sortable roster, daily
talks/gifts, stress relief, blessings/kisses, proposals, ascension, and
awakening. Gift reactions come from the YAML affection tables.
"""

import random

from utils import _int_to_roman, display_name, display_name_with_species
from events import format_day_delta, format_days_left
from character import player_max_hp
from resources.enemies import AFFECTION_GIFTS, ENEMIES
from gui.terminal import term
from facilities.dispatch import (
    adjust_stress,
    dispatch_return_text,
    girl_status_line,
    injured_text,
)
from inventory import consume_stackable_items, remove_item_by_reference

from .constants import (
    AWAKEN_AFFECTION_REQ,
    AWAKEN_CAP_REQ,
    AWAKEN_LEVEL_REQ,
    HOUSE_MONSTER_GIRL_LIMITS,
    RECRUIT_AFFECTION_THRESHOLD,
)
from .core import (
    _affection_gain,
    _apply_ring_bonus_to_girl,
    _get_engagement_rings,
    _gifts_remaining,
    _girl_unique_id,
    _has_engagement_ring,
    _house_level_data,
    _reset_daily_limits,
    _talks_remaining,
)
from .rest import _house_sleep


def _get_ascension_requirements(current_cap):
    """
    Returns a list of (tier, count) tuples for ascending from current_cap.
    Formula: to ascend from cap C, need (C/10 - t + 1) stones of tier t
    for t = 1 .. C/10.
    Example: C=20 → [(1, 2), (2, 1)]  → 2 Stone I + 1 Stone II
             C=30 → [(1, 3), (2, 2), (3, 1)]
    """
    max_tier = current_cap // 10
    requirements = []
    for tier in range(1, max_tier + 1):
        count = max_tier - tier + 1
        requirements.append((tier, count))
    return requirements


def _can_ascend_ally(player, ally):
    """Check if ally is at their level cap and player has ALL required stones."""
    from family import is_trueborn_minor
    if ally.get("pregnant") or is_trueborn_minor(ally):
        return False
    if int(ally.get("recovery_until", 0) or 0) > player.get("day", 1):
        return False
    current_cap = ally.get("level_cap", 10)
    if ally["level"] < current_cap:
        return False
    requirements = _get_ascension_requirements(current_cap)
    # Count available stones per tier in inventory (stack-aware)
    available = {}
    for item in player.get("inventory", []):
        tier = item.get("ascension_tier")
        if tier:
            available[tier] = available.get(tier, 0) + item.get("count", 1)
    # Check all requirements
    for tier, count in requirements:
        if available.get(tier, 0) < count:
            return False
    return True


def can_awaken_girl(girl, day=None):
    """Return (eligible, reason) for the House Lounge Awaken action.

    Covers the girl-side gates only (candidate, level, cap, affection, not yet
    awakened); the Sigil cost is checked when the action is taken.
    """
    from combat.ally_skills import has_awakening
    from family import is_trueborn_minor
    if girl.get("awakened"):
        return False, "already awakened"
    if girl.get("pregnant"):
        return False, "expecting"
    if is_trueborn_minor(girl):
        return False, "too young"
    if day is not None and int(girl.get("recovery_until", 0) or 0) > day:
        return False, "recovering"
    # True-born children use their mother's awakening data (synthetic keys
    # have no YAML entry of their own).
    awakening_key = girl.get("mother_key") if girl.get("is_trueborn") else girl.get("key", "")
    if not has_awakening(awakening_key or ""):
        return False, "no awakening available"
    if girl.get("level", 1) < AWAKEN_LEVEL_REQ:
        return False, f"needs Lv {AWAKEN_LEVEL_REQ}"
    if girl.get("level_cap", 10) < AWAKEN_CAP_REQ:
        return False, f"needs level cap {AWAKEN_CAP_REQ}"
    if girl.get("affection", 0) < AWAKEN_AFFECTION_REQ:
        return False, f"needs affection {AWAKEN_AFFECTION_REQ}"
    return True, "ready"


def _fmt_dialogue(line, **tokens):
    """Replace {token} placeholders without str.format (dialogue-safe)."""
    for key, val in tokens.items():
        line = line.replace("{" + key + "}", str(val))
    return line


def _sort_girls(all_girls, sort_by, sort_dir):
    """Sort the combined girls list by the given criteria.

    Args:
        all_girls: list of (where, girl_dict) tuples
        sort_by: "capture_order", "level", or "affection"
        sort_dir: "asc" (top→bottom) or "desc" (bottom→top)

    Returns:
        Sorted list of (where, girl_dict) tuples
    """
    reverse = (sort_dir == "desc")

    if sort_by == "level":
        return sorted(all_girls, key=lambda x: x[1].get("level", 1), reverse=reverse)
    elif sort_by == "affection":
        return sorted(all_girls, key=lambda x: x[1].get("affection", 30), reverse=reverse)
    else:  # capture_order (default)
        # Sort by captured_on day (lower = caught earlier).
        # Active allies and girls without captured_on get a high sentinel value.
        def _cap_key(item):
            g = item[1]
            return g.get("captured_on", 9999)
        return sorted(all_girls, key=_cap_key, reverse=reverse)


def _house_lounge(player, city_id, house):
    # ── Filter / sort state (persists across re-displays) ──────────────────
    sort_by = "capture_order"   # "capture_order" | "level" | "affection"
    sort_dir = "asc"            # "asc" (top→bottom) | "desc" (bottom→top)

    SORT_LABELS = {
        "capture_order": "Capture Order",
        "level":         "Level",
        "affection":     "Affection",
    }
    DIR_LABEL = {"asc": "Top→Bottom", "desc": "Bottom→Top"}

    # ── Outer loop: re-display after filter changes ─────────────────────────
    while True:
        term.clear()
        lvl_data = _house_level_data(house)
        girls = house.get("monster_girls", [])
        max_girls = HOUSE_MONSTER_GIRL_LIMITS.get(house["level"], 2)
        allies = player.get("allies", [])
        total_girls = len(girls) + len(allies)

        term.print(f"=== {lvl_data['name'].upper()} LOUNGE ===")
        term.print(f"Monster Girls: {total_girls}/{max_girls}")
        if allies:
            from resources.quests import format_resonance_status
            tier = (player.get("quests") or {}).get("resonance_tier", 0)
            term.print(f"Active Party: {len(allies)} allies")
            term.print(format_resonance_status(tier))
        sigil_count = player.get("awakening_sigils", 0)
        shard_count = player.get("awakening_shards", 0)
        if sigil_count or shard_count:
            term.print(f"Awakening Sigils: {sigil_count}   ·   Sigil Shards: {shard_count}")

        # ── Filter / sort info bar ──────────────────────────────────────────
        term.print(f"Sort: [{SORT_LABELS[sort_by]}]  |  View: [{DIR_LABEL[sort_dir]}]")
        term.print()

        # Build combined list
        all_girls = []
        for girl in girls:
            all_girls.append(("lounge", girl))
        for ally in allies:
            all_girls.append(("active", ally))

        if not all_girls:
            term.print("The lounge is quiet... no companions yet.")
            term.pause()
            return

        # ── Apply sort ──────────────────────────────────────────────────────
        all_girls = _sort_girls(all_girls, sort_by, sort_dir)

        # ── Display girl list ───────────────────────────────────────────────
        for i, (where, g) in enumerate(all_girls):
            aff = g.get("affection", 30)
            aff_cap = g.get("affection_cap", 200)
            is_child = bool(g.get("is_trueborn"))
            if is_child:
                status = "👧"
            else:
                status = "💍" if g.get("married") else "💎" if g.get("engaged") else "💖" if aff >= 140 else "❤️" if aff >= 80 else "😐"
            ready = " ✓" if aff >= RECRUIT_AFFECTION_THRESHOLD else ""
            active_tag = " [ACTIVE]" if where == "active" else ""
            cap_tag = " [CAP]" if where == "active" and g["level"] >= g.get("level_cap", 10) else ""
            aff_str = f"{aff}/{aff_cap}"
            aff_label = "Bond" if is_child else "Affection"
            disp_full = display_name_with_species(g)
            if where == "active":
                if g.get("defeated") or g.get("current_hp", 0) <= 0:
                    hp_str = "[INCAPACITATED]"
                else:
                    hp_str = f"HP: {g['current_hp']}/{g['max_hp']}"
                term.print(f"  {i+1}. {disp_full} (Lv {g['level']}{cap_tag}){active_tag} — {hp_str} — {status} {aff_label}: {aff_str}{ready}")
            else:
                duty_tag = ""
                if g.get("dispatch_mission"):
                    duty_tag = " [AWAY]"
                elif int(g.get("injured_until", 0) or 0) > player.get("day", 1):
                    duty_tag = " [INJURED]"
                term.print(f"  {i+1}. {disp_full} (Lv {g['level']}){active_tag}{duty_tag} — {status} {aff_label}: {aff_str}{ready}")

        # ── Build menu: girl options + filter controls + back ───────────────
        girl_options = []
        girl_styles = []
        for where, g in all_girls:
            aff = g.get("affection", 30)
            active_tag = " [ACTIVE]" if where == "active" else ""
            aff_mark = f"Bond {aff}" if g.get("is_trueborn") else f"\u2665{aff}"
            girl_options.append(f"{display_name_with_species(g)} (Lv {g['level']}){active_tag} — {aff_mark}")
            girl_styles.append(None)  # default style

        # Pad to next full row so filters start on their own row (4-column grid)
        num_girls = len(all_girls)
        pad_count = (4 - (num_girls % 4)) % 4
        for _ in range(pad_count):
            girl_options.append("")
            girl_styles.append({"bg": "#1a1a2e", "fg": "#1a1a2e", "active_bg": "#1a1a2e", "active_fg": "#1a1a2e"})

        # Filter style: warm amber/gold to stand out from blue girl buttons
        FILTER_STYLE = {"bg": "#5a4a1a", "fg": "#f0d060", "active_bg": "#7a6a2a", "active_fg": "#ffe080"}

        # Append filter/sort toggles with distinct styling
        girl_options.append("\u2014 Sort by Capture Order \u2014")
        girl_styles.append(FILTER_STYLE)
        girl_options.append("\u2014 Sort by Level \u2014")
        girl_styles.append(FILTER_STYLE)
        girl_options.append("\u2014 Sort by Affection \u2014")
        girl_styles.append(FILTER_STYLE)
        girl_options.append(f"\u2014 Toggle View: {'Bottom\u2192Top' if sort_dir == 'asc' else 'Top\u2192Bottom'} \u2014")
        girl_styles.append(FILTER_STYLE)

        idx = term.menu(girl_options, prompt="Select companion or change sort:", allow_cancel=True, cancel_label="Back", styles=girl_styles)
        if idx < 0:
            return  # Back to house menu

        # ── Check if user picked a filter option ────────────────────────────
        filter_start = num_girls + pad_count
        if idx == filter_start:
            sort_by = "capture_order"
            continue  # re-display
        elif idx == filter_start + 1:
            sort_by = "level"
            continue  # re-display
        elif idx == filter_start + 2:
            sort_by = "affection"
            continue  # re-display
        elif idx == filter_start + 3:
            sort_dir = "desc" if sort_dir == "asc" else "asc"
            continue  # re-display

        # ── Handle clicks on invisible spacer buttons ───────────────────────
        if idx >= num_girls:
            continue  # clicked a spacer, re-display

        where, girl = all_girls[idx]
        girl_key = girl.get("key", "")
        template = ENEMIES.get(girl_key, {})
        dialogue = template.get("dialogue", {})
        aff = girl.get("affection", 30)

        # ── Sub-menu for this girl ──────────────────────────────────────────
        while True:
            term.clear()
            disp = display_name(girl)
            is_child = bool(girl.get("is_trueborn"))
            engaged = girl.get("engaged", False) and not is_child
            married = girl.get("married", False) and not is_child
            # Stale-cap heal: engaged/married girls belong at cap 300
            # (affection ladder v2 — base 200 / engaged 300).
            if (engaged or married) and girl.get("affection_cap", 100) < 300:
                girl["affection_cap"] = 300
            aff_cap = girl.get("affection_cap", 200)
            term.print(f"=== {disp} ===")
            if girl.get("nickname"):
                term.print(f"  Species: {girl['name']}")
            aff_label = "Bond" if is_child else "Affection"
            term.print(f"  {aff_label}: {aff}/{aff_cap}")
            if is_child:
                status_label = "Daughter"
            else:
                status_label = "Married" if married else "Engaged" if engaged else "Active" if where == "active" else "At home"
            term.print(f"  Status: {status_label}")
            if is_child:
                from family import father_legacy_label
                legacy_label = father_legacy_label(girl)
                term.print(f"  Father's Legacy: {legacy_label or '—'}")
            if girl.get("pregnant"):
                from family import pregnancy_period
                period = pregnancy_period(girl, player.get("day", 1))
                due_day = girl.get("due_day")
                due_text = format_day_delta(due_day, player.get("day", 1)) if due_day else "?"
                term.print(f"  Expecting — period {period}/3 · due {due_text}")
            term.print(f"  {girl_status_line(girl, player.get('day', 1))}")
            away_line = dispatch_return_text(player, girl)
            if away_line:
                term.print(f"  {away_line}")
            hurt_line = injured_text(girl, player.get("day", 1))
            if hurt_line:
                term.print(f"  {hurt_line}")
            ring_bonus = girl.get("ring_stat_bonus")
            if ring_bonus:
                bonus_lines = [f"{stat} +{val}" for stat, val in ring_bonus.items()]
                term.print(f"  Ring Blessing: {', '.join(bonus_lines)}")
            from combat.ally import get_growth_label
            growth_label = get_growth_label(girl)
            if growth_label != "—":
                term.print(f"  Growth: {growth_label} (late bloomer)")
            if girl.get("awakened"):
                term.print("  ✦ Awakened — her innate skills are empowered.")
            if where == "active":
                cap = girl.get("level_cap", 10)
                term.print(f"  Level: {girl['level']}/{cap}")
            term.print()

            talks_left = _talks_remaining(player, _girl_unique_id(girl))
            gift_ready = _gifts_remaining(player, _girl_unique_id(girl))
            can_propose = (aff >= 100 and not engaged and not married
                           and not girl.get("no_romance")
                           and _has_engagement_ring(player))

            can_ascend = where == "active" and _can_ascend_ally(player, girl)
            at_cap = where == "active" and girl["level"] >= girl.get("level_cap", 10)
            can_awaken, _awaken_reason = can_awaken_girl(girl, player.get("day", 1))

            # Build dynamic menu options
            menu_options = []
            menu_actions = []

            menu_options.append(f"Talk  ({talks_left} left today)")
            menu_actions.append("talk")

            menu_options.append(f"Give a gift  ({'ready' if gift_ready else 'already gifted today'})")
            menu_actions.append("gift")

            bath_item = next((it for it in player.get("inventory", [])
                              if it.get("id") == "herbal_bath_salts"), None)
            if bath_item and not girl.get("dispatch_mission") and int(girl.get("stress", 0)) > 0:
                menu_options.append(f"Draw a warm bath (Herbal Bath Salts ×{bath_item.get('count', 1)}, −20 stress)")
                menu_actions.append("bath")

            if aff >= 60 and not is_child:
                menu_options.append("Ask for blessing")
                menu_actions.append("blessing")

            if aff >= 80 and not girl.get("no_romance"):
                menu_options.append("Share a kiss")
                menu_actions.append("kiss")

            if can_propose and not girl.get("no_romance"):
                menu_options.append("Propose marriage")
                menu_actions.append("propose")

            # Shared Night (docs/family_system_design.md §4.3) — Night only.
            import time_blocks
            from family import share_night_eligibility
            if (time_blocks.get_day_phase(player) == "night"
                    and share_night_eligibility(player, girl, True)[0]):
                menu_options.append("Share the night")
                menu_actions.append("share_night")

            menu_options.append("Rename" if girl.get("nickname") else "Give a name")
            menu_actions.append("rename")

            if can_ascend:
                menu_options.append("Ascend (break level limit)")
                menu_actions.append("ascend")
            elif at_cap:
                requirements = _get_ascension_requirements(girl.get("level_cap", 10))
                needs = ", ".join(f"{count} Stone {_int_to_roman(tier)}" for tier, count in requirements)
                term.print(f"  [Ascend: needs {needs}]")

            if can_awaken:
                sigil_now = player.get("awakening_sigils", 0)
                menu_options.append(f"Awaken (1 Awakening Sigil) [{'ready' if sigil_now else 'no Sigil'}]")
                menu_actions.append("awaken")

            if where == "lounge":
                menu_options.append("Take her adventuring" if is_child else "Recruit to party")
                menu_actions.append("recruit")

            if where == "active":
                menu_options.append("Remove from party")
                menu_actions.append("dismiss")

            menu_options.append("Back")
            menu_actions.append("back")

            choice_idx = term.menu(menu_options, prompt=f"What to do with {disp}?")
            if choice_idx < 0:
                break
            action = menu_actions[choice_idx] if choice_idx < len(menu_actions) else "back"

            if action == "back":
                break

            elif action == "rename":
                # ── RENAME ──
                current_nick = girl.get("nickname", "")
                if current_nick:
                    prompt = (f"Current name: {current_nick} (originally {girl['name']})\n"
                              "Enter a new name, or leave blank to restore her original name:")
                else:
                    prompt = f"Enter a name for {girl['name']} (leave blank to cancel):"
                new_name = term.input(prompt).strip()
                # Single line only, and short enough for the combat HUD (12 chars shown).
                new_name = " ".join(new_name.split())[:16]
                if new_name:
                    girl["nickname"] = new_name
                    term.print(f"\n{girl['name']} will now answer to \"{new_name}\".")
                elif current_nick:
                    girl["nickname"] = ""
                    term.print(f"\nShe's back to being called {girl['name']}.")
                else:
                    term.print("\n(No change.)")
                term.pause()

            elif action == "talk":
                if talks_left <= 0:
                    term.print(f"\n{disp} seems tired of talking. Come back tomorrow.")
                    term.pause()
                    continue

                # Wedding gift check (300 affection, earned after engagement)
                if engaged and not married and aff >= 300 and not is_child:
                    special_line = dialogue.get("house_special_gift",
                        f"{disp} pulls out a beautifully wrapped box. 'This is for you, my love.'")
                    term.print("\n" + (special_line.format(name=disp) if "{name}" in special_line else special_line))
                    # Give wedding accessory
                    wedding_id = f"wedding_{girl_key}"
                    from resources.items import build_item, ITEMS
                    if wedding_id in ITEMS:
                        wedding_item = build_item(wedding_id, "unique")
                        from inventory import add_item_to_inventory
                        if add_item_to_inventory(player, wedding_item):
                            term.print(f"\n  *** You received: {wedding_item['name']} ***")
                        else:
                            term.print(f"\n  Your inventory is full! The {wedding_item['name']} was left on the table.")
                    else:
                        term.print(f"\n  (Wedding item '{wedding_id}' not found — this is a bug.)")
                    girl["married"] = True
                    player.setdefault("married_girls", [])
                    if girl_key not in player["married_girls"]:
                        player["married_girls"].append(girl_key)
                    # Remove from engaged list
                    player.setdefault("engaged_girls", [])
                    if girl_key in player["engaged_girls"]:
                        player["engaged_girls"].remove(girl_key)
                    term.print(f"\n  *** {disp} is now your wife! ***")
                    term.pause()
                    continue

                # Determine dialogue key
                if aff <= 60:
                    aff_tier = "low"
                elif aff <= 120:
                    aff_tier = "mid"
                elif aff <= 200:
                    aff_tier = "high"
                else:
                    aff_tier = "max"

                if is_child:
                    # Daughter voice — bond only, never the adult romance set.
                    from resources.family_scenes import child_talk_lines
                    mother_key = girl.get("mother_key") or girl_key
                    mother_template = ENEMIES.get(mother_key, {}) if mother_key else {}
                    child_dialogue = mother_template.get("dialogue", {}) or {}
                    line = (child_dialogue.get(f"child_talk_{aff_tier}")
                            or random.choice(child_talk_lines(
                                aff_tier, girl.get("race"), mother_key)))
                elif engaged and not married:
                    # Alternate between engaged_1 and engaged_2
                    if player.get("day", 1) % 2 == 0:
                        dialog_key = "house_talk_engaged_2"
                        default = f"{disp} leans against you, smiling. 'Every day with you feels like a dream. I can't wait for our wedding.'"
                    else:
                        dialog_key = "house_talk_engaged_1"
                        default = f"{disp} beams at you, her engagement ring catching the light. 'Can you believe it? We're going to be together forever!'"
                    line = dialogue.get(dialog_key, default)
                else:
                    if girl.get("awakened"):
                        # Awakened girls have their own daily-talk set
                        dialog_key = f"awakened_talk_{aff_tier}"
                        line = dialogue.get(dialog_key,
                            dialogue.get(f"house_talk_{aff_tier}", f"{disp} looks at you expectantly."))
                    else:
                        dialog_key = f"house_talk_{aff_tier}"
                        line = dialogue.get(dialog_key, f"{disp} looks at you expectantly.")

                line = line.format(name=disp) if "{name}" in line else line
                term.print("\n" + line)

                # Increase affection
                gain = _affection_gain(girl, random.randint(3, 7), player.get("day", 1))
                girl["affection"] = min(aff_cap, aff + gain)
                aff = girl["affection"]
                term.print(f"\nAffection +{gain} (now {aff}/{aff_cap})")

                # Track daily talk
                _reset_daily_limits(player)
                uid = _girl_unique_id(girl)
                player["girl_talk_today"][uid] = player["girl_talk_today"].get(uid, 0) + 1
                stress_now = adjust_stress(girl, -3)
                term.print(f"  The talk eases her mind — Stress −3 (now {stress_now}).")
                term.pause()

            elif action == "gift":
                if not gift_ready:
                    term.print(f"\n{disp} has already received a gift today.")
                    term.pause()
                    continue

                gifts = [it for it in player.get("inventory", []) if it.get("type") == "gift"]
                if not gifts:
                    term.print("You have no gifts.")
                    term.pause()
                    continue

                gift_names = [g['name'] for g in gifts]
                gift_names.append("Back")
                gidx = term.menu(gift_names, prompt="Choose gift:")
                if gidx < 0 or gidx >= len(gifts):
                    # Back or cancelled
                    continue
                gift = gifts[gidx]
                # Remove from inventory
                gift_type = gift.get("gift_type", "unknown")
                reaction = get_gift_reaction(girl_key, gift_type,
                                             is_trueborn=is_child)
                reaction = _affection_gain(girl, reaction, player.get("day", 1))
                remove_item_by_reference(player, gift)

                # Show love/hate dialogue
                if is_child:
                    from resources.family_scenes import child_gift_lines
                    mother_key = girl.get("mother_key") or girl_key
                    mother_template = ENEMIES.get(mother_key, {}) if mother_key else {}
                    child_dialogue = mother_template.get("dialogue", {}) or {}
                    child_line = child_dialogue.get(
                        "child_gift_love" if reaction > 0 else "child_gift_hate")
                    line = (child_line or random.choice(child_gift_lines(
                        reaction > 0, girl.get("race"), mother_key)))
                    term.print(line.format(name=disp) if "{name}" in line else line)
                elif reaction > 0:
                    love_line = dialogue.get("house_gift_love", f"{disp} beams with joy!")
                    term.print(love_line.format(name=disp) if "{name}" in love_line else love_line)
                elif reaction < 0:
                    hate_line = dialogue.get("house_gift_hate", f"{disp} sighs, disappointed.")
                    term.print(hate_line.format(name=disp) if "{name}" in hate_line else hate_line)
                else:
                    term.print(f"{disp} shrugs indifferently.")

                # Apply reaction
                girl["affection"] = max(0, min(aff_cap, aff + reaction))
                aff = girl["affection"]
                term.print(f"Reaction: {reaction:+} affection (now {aff}/{aff_cap})")

                # Track daily gift
                _reset_daily_limits(player)
                uid = _girl_unique_id(girl)
                player["girl_gift_today"][uid] = True
                stress_delta = -12 if reaction > 0 else (-6 if reaction == 0 else 4)
                stress_now = adjust_stress(girl, stress_delta)
                term.print(f"  Stress {stress_delta:+d} (now {stress_now}).")
                term.pause()

            elif action == "bath":
                remove_item_by_reference(player, bath_item)
                stress_now = adjust_stress(girl, -20)
                term.print(f"\nYou draw a warm bath for {disp}. She sinks in with a long sigh and comes out loose-limbed and calm.")
                term.print(f"  Stress −20 (now {stress_now}).")
                term.pause()

            elif action == "blessing":  # Blessing
                buff_line = dialogue.get("house_buff", f"{disp} grants you a blessing.")
                term.print(buff_line.format(name=disp) if "{name}" in buff_line else buff_line)
                # Apply a buff: +1 all stats for 1 floor
                player.setdefault("active_buffs", [])
                player["active_buffs"] = [b for b in player["active_buffs"] if b.get("type") != "girl_blessing"]
                player["active_buffs"].append({
                    "type": "girl_blessing",
                    "stat": "all",
                    "value": 1,
                    "remaining": 1,
                })
                term.print("You feel a warm glow – +1 to all stats for 1 floor.")
                term.pause()

            elif action == "kiss":  # Kiss
                if girl.get("no_romance"):
                    term.print(f"\n{disp} gives you a puzzled look. That is not the bond you share.")
                    term.pause()
                    continue
                kiss_line = dialogue.get("house_bond_kiss", f"{disp} kisses you tenderly.")
                term.print(kiss_line.format(name=disp) if "{name}" in kiss_line else kiss_line)
                # Heal and boost affection
                player["current_hp"] = min(player["current_hp"] + 20, player_max_hp(player))
                gain = _affection_gain(girl, random.randint(5, 10), player.get("day", 1))
                girl["affection"] = min(aff_cap, aff + gain)
                aff = girl["affection"]
                term.print(f"Affection +{gain} (now {aff}/{aff_cap}). You feel renewed (healed 20 HP).")
                stress_now = adjust_stress(girl, -4)
                term.print(f"  She looks a little lighter — Stress −4 (now {stress_now}).")
                term.pause()

            elif action == "share_night":
                _house_sleep(player, city_id, house, partner=girl)
                break

            elif action == "propose":
                # ── PROPOSE ──
                if girl.get("no_romance"):
                    term.print(f"\n{disp} steps back, confused. That is not the bond you share.")
                    term.pause()
                    continue
                # Let the player choose which ring to offer — its stats become
                # her permanent engagement bonus, so the choice matters.
                rings = _get_engagement_rings(player)
                if not rings:
                    term.print("You don't have an engagement ring.")
                    term.pause()
                    continue
                if len(rings) == 1:
                    ring = rings[0]
                else:
                    ring_labels = []
                    for r in rings:
                        mods = r.get("mods") or r.get("base_mods") or {}
                        mod_txt = ", ".join(f"+{v} {stat}" for stat, v in mods.items())
                        ring_labels.append(f"{r['name']} ({mod_txt})" if mod_txt else r["name"])
                    ridx = term.menu(ring_labels + ["Back"],
                                     prompt=f"Which ring will you offer to {disp}?")
                    if ridx < 0 or ridx >= len(rings):
                        continue
                    ring = rings[ridx]

                engaged_line = dialogue.get("house_engaged", f"{disp} gasps, her eyes sparkling with tears of joy. 'Yes! Yes, I will marry you!' She throws her arms around you.")
                term.print("\n" + (engaged_line.format(name=disp) if "{name}" in engaged_line else engaged_line))
                # Consume the chosen ring
                remove_item_by_reference(player, ring)

                # The ring's power becomes her permanent engagement bonus
                # (folded into her stored stats so it shows up everywhere).
                ring_bonus = _apply_ring_bonus_to_girl(girl, ring)
                if ring_bonus:
                    bonus_lines = [f"{stat} +{val}" for stat, val in ring_bonus.items()]
                    term.print(f"  The ring's power flows into {disp}: {', '.join(bonus_lines)}.")

                girl["engaged"] = True
                girl["affection_cap"] = 300
                player.setdefault("engaged_girls", [])
                if girl_key not in player["engaged_girls"]:
                    player["engaged_girls"].append(girl_key)
                term.print(f"\n  *** {disp} is now engaged to you! Affection cap raised to 300. ***")
                term.pause()
                continue

            elif action == "ascend":
                # ── ASCEND ──
                from family import is_trueborn_minor
                if (girl.get("pregnant") or is_trueborn_minor(girl)
                        or int(girl.get("recovery_until", 0) or 0) > player.get("day", 1)):
                    term.print(f"\n{disp} can't ascend right now.")
                    term.pause()
                    continue
                current_cap = girl.get("level_cap", 10)
                requirements = _get_ascension_requirements(current_cap)

                # Gather all required stones from inventory (stack-aware)
                inv = player.get("inventory", [])
                consumed_refs = []
                for tier, count in requirements:
                    tier_consumed = consume_stackable_items(player, lambda item: item.get("ascension_tier") == tier, count)
                    total_found = sum(amt for _, amt in tier_consumed)
                    if total_found < count:
                        term.print("You do not have enough Ascension Stones.")
                        term.pause()
                        continue
                    consumed_refs.extend(tier_consumed)

                # Build summary of consumed stones for display
                stone_summary = ", ".join(
                    f"{count} Stone {_int_to_roman(tier)}"
                    for tier, count in requirements
                )
                # Pick the highest-tier stone for dialogue reference
                highest_stone = next(
                    (item for item, _ in consumed_refs if item.get("ascension_tier") == current_cap // 10),
                    consumed_refs[0][0] if consumed_refs else None
                )

                # Capture old cap before the ceremony
                old_cap = girl["level_cap"]

                # Dialogue 1: Ally's reaction (from monster_girls.yaml)
                pre_line = dialogue.get("ascension_pre_ceremony",
                    f"{disp} kneels before you, her eyes closed in reverence.\n'I feel the chains upon my soul. Please... set me free.'")
                pre_line = pre_line.format(name=disp, stone=highest_stone['name'] if highest_stone else 'stone', old_cap=old_cap)
                term.print("\n" + pre_line)
                term.pause("Press Continue to begin the ceremony...")

                girl["level_cap"] = old_cap + 10

                # Dialogue 2: The ascension itself (from monster_girls.yaml)
                post_line = dialogue.get("ascension_post_ceremony",
                    f"The {highest_stone['name'] if highest_stone else 'stone'} shatters into motes of prismatic light!\nAncient power surges through {disp}.\nHer form shimmers, breaking the seal of Level {old_cap}.")
                post_line = post_line.format(name=disp, stone=highest_stone['name'] if highest_stone else 'stone', old_cap=old_cap)
                term.print(f"\n{'='*50}")
                term.print("  " + post_line.replace("\n", "\n  "))
                term.print(f"  Stones consumed: {stone_summary}")
                term.print(f"  *** LEVEL CAP INCREASED: {old_cap} → {girl['level_cap']} ***")
                term.print(f"{'='*50}")

                term.print(f"\n{disp} opens her eyes, renewed and stronger.")
                term.print("'I can feel it... the path ahead is open once more.'")
                term.pause()

            elif action == "awaken":
                # ── AWAKEN (docs/awakening_design.md Part C) ──
                from family import is_trueborn_minor
                if (girl.get("pregnant") or is_trueborn_minor(girl)
                        or int(girl.get("recovery_until", 0) or 0) > player.get("day", 1)):
                    term.print(f"\n{disp} can't awaken right now.")
                    term.pause()
                    continue
                if player.get("awakening_sigils", 0) < 1:
                    term.print("\nYou have no Awakening Sigils.")
                    term.print("Sigils come from your first-ever superboss kill, from Mary Sue,")
                    term.print("or from the Arcane Tower — Awakening Research")
                    term.print("(4 Sigil Shards + 25,000 gold). Shards drop from first-time superbosses.")
                    term.pause()
                    continue

                from combat.ally_skills import apply_awakening_skills, get_innate_skill_def
                awakening_key = (girl.get("mother_key") if girl.get("is_trueborn")
                                 else girl_key)
                template = ENEMIES.get(girl_key, {})
                awakened_name = template.get("awakened_name") or girl.get("name", disp)

                # Dialogue 1: her plea
                pre_line = dialogue.get("awakening_pre_ceremony",
                    f"{disp} takes your hands, her eyes shining. 'I can feel it — the person I was meant to be. Please... call me by my true name.'")
                term.print("\n" + _fmt_dialogue(pre_line, name=disp, new_name=awakened_name))
                term.pause("Press Continue to begin the awakening...")

                # Consume the Sigil and perform the awakening
                player["awakening_sigils"] = player.get("awakening_sigils", 0) - 1
                apply_awakening_skills(girl, awakening_key or girl_key)
                girl["awakened"] = True
                girl["awakened_name"] = awakened_name

                # The one-time special scene (multi-beat)
                scene = dialogue.get("awakening_scene",
                    f"Light gathers around {disp} like a rising tide.\nHer old name sloughs away like a shed skin.\nWhen the glow fades she stands taller — and smiles.\n'{awakened_name}... I like the sound of that. Yours, always.'")
                term.print(f"\n{'='*50}")
                term.print("  " + _fmt_dialogue(scene, name=disp, new_name=awakened_name).replace("\n", "\n  "))
                term.print(f"{'='*50}")

                # Dialogue 2: her vow, under the new name
                post_line = dialogue.get("awakening_post_ceremony",
                    f"{awakened_name} flexes her fingers, feeling the new strength in them. 'I'm ready. Whatever comes next — we face it together.'")
                term.print("\n" + _fmt_dialogue(post_line, name=awakened_name, new_name=awakened_name))

                # Show the upgraded kit
                term.print(f"\n  *** {disp} awakens as {awakened_name}! ***")
                for sid in girl.get("awakened_skills", []):
                    sdef = get_innate_skill_def(sid)
                    if sdef:
                        term.print(f"    ★ {sdef['name']} — {sdef.get('description', '')}")
                term.print(f"  (Awakening Sigils left: {player['awakening_sigils']})")
                term.pause()
                continue

            elif action == "recruit":
                # ── RECRUIT ──
                aff = girl.get("affection", 30)
                if aff < RECRUIT_AFFECTION_THRESHOLD:
                    denied_msg = dialogue.get("recruit_denied",
                        f"{disp} looks at you uncertainly. 'I don't know you well enough yet...'")
                    term.print(denied_msg.format(name=disp))
                    term.print(f"  (Need {RECRUIT_AFFECTION_THRESHOLD}+ affection. Currently: {aff}/{aff_cap})")
                    term.pause()
                else:
                    day_now = player.get("day", 1)
                    if girl.get("dispatch_mission"):
                        term.print(f"{disp} is away on a dispatch — she'll see you when she's back.")
                        term.pause()
                        continue
                    if int(girl.get("injured_until", 0) or 0) > day_now:
                        term.print(f"{disp} is injured ({format_days_left(girl['injured_until'], day_now)} "
                                   f"left to recover) and can't join the party yet.")
                        term.pause()
                        continue
                    accepted_msg = dialogue.get("recruit_accepted",
                        f"{disp} smiles warmly. 'I'll fight beside you!'")
                    term.print(accepted_msg.format(name=disp))
                    from combat.ally import recruit_ally_from_house
                    ally, msg = recruit_ally_from_house(player, girl, house)
                    term.print(msg)
                    if ally:
                        term.print(f"{display_name(ally)}'s stats:")
                        term.print(f"  HP: {ally['max_hp']}")
                        term.print(f"  STR: {ally['attributes']['Strength']}  CON: {ally['attributes']['Constitution']}  DEX: {ally['attributes']['Dexterity']}")
                    term.pause()
                    break  # after recruitment, return to girl list

            elif action == "dismiss":
                # ── DISMISS ──
                dismiss_msg = dialogue.get("dismiss",
                    f"{disp} nods quietly. 'I'll be here when you need me.'")
                term.print(dismiss_msg.format(name=disp) if "{name}" in dismiss_msg else dismiss_msg)
                from combat.ally import _return_ally_to_house
                _return_ally_to_house(player, girl, house)
                player["allies"] = [a for a in player.get("allies", []) if not (a.get("key") == girl.get("key") and a.get("name") == girl.get("name"))]
                term.print(f"{disp} has been returned to the lounge.")
                term.pause()
                break  # after dismissal, return to girl list

            else:
                term.print("Invalid option.")
                term.pause()


def get_gift_reaction(girl_key, gift_type, is_trueborn=False):
    """Load personalized gift reactions from monster_girls.yaml.

    True-born daughters use a small, reliably positive bond pool instead of
    the adult random reaction table.
    """
    if is_trueborn:
        return random.randint(8, 14)
    try:
        reactions = AFFECTION_GIFTS.get(girl_key, {})
        return reactions.get(gift_type, random.randint(-15, 25))
    except Exception:
        return random.randint(-10, 30)
