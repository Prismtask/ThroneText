"""Quest runtime — canonical state, journal sync, rewards, story beats.

Design: docs/quest_system_design.md

- Definitions live in ``resources/quests.py`` (pure data).
- Canonical progress lives in ``player["quests"]``. The Journal lists
  (``player["journal"]["main_quests"]`` / ``["side_quests"]``) are DISPLAY
  MIRRORS rebuilt by :func:`sync_journal` — never write them anywhere else.
- Game hooks call :func:`update_quests(player, obj_type, target)`
  fire-and-forget; the runtime no-ops when nothing matches.
- Every mutating function returns a list of plain-text messages. Callers
  display them via ``term.print`` (facilities) or the session log; quest
  updates are surfaced through the Journal — quest flows do not use toasts.
"""

from resources.quests import (
    QUESTS,
    format_orb_meter,
    get_grade_name,
    get_next_grade,
    get_orb_state,
    get_resonance_grade,
)


# ── State ─────────────────────────────────────────────────────────────────────

def _default_state():
    return {
        "active": {},               # quest_id -> {"objectives": {key: bool}, "started_day": int}
        "completed": [],            # [quest_id, ...] (permanent, in completion order)
        "completed_days": {},       # quest_id -> day completed (Journal display)
        "declined": [],             # [quest_id, ...] (side quests only)
        "flags": {},                # story flags set by quests
        "resonance_tier": 0,        # Command Resonance grade (resources/quests.RESONANCE_GRADES)
        "story_queue": [],          # [beat_id, ...] — opened as StoryScreens on city entry
        "seen_services": [],        # facility keys entered (for state-based objectives)
        "pending_items": [],        # reward items that didn't fit in the bag
    }


def ensure_quest_state(player):
    """Initialize/migrate the quest state block on a player dict."""
    state = player.setdefault("quests", _default_state())
    for key, value in _default_state().items():
        state.setdefault(key, value)
    return state


# ── Small helpers ─────────────────────────────────────────────────────────────

def _objective_key(obj_type, target):
    return f"{obj_type}:{target}"


def _quest_objectives(quest):
    """Flatten a quest's stages into one ordered list of objective dicts."""
    out = []
    for stage in quest.get("stages", []):
        out.extend(stage.get("objectives", []))
    return out


def _prereq_met(player, quest):
    prereq = quest.get("prereq")
    if not prereq:
        return True
    state = ensure_quest_state(player)
    if prereq in QUESTS:
        return prereq in state["completed"]
    return bool(state["flags"].get(prereq))


def _status(player, quest_id):
    """Derived status: 'active' | 'ready' | 'completed' | 'declined' | None."""
    state = ensure_quest_state(player)
    if quest_id in state["completed"]:
        return "completed"
    if quest_id in state["declined"]:
        return "declined"
    entry = state["active"].get(quest_id)
    if not entry:
        return None
    if all(entry["objectives"].values()):
        return "ready"
    return "active"


def _record_journal_event(player, name, desc):
    """Append a quest entry to the Journal's Event tab (deduped by day+name)."""
    journal = player.setdefault("journal", {})
    events = journal.setdefault("events", [])
    day = player.get("day", 1)
    for existing in events:
        if existing.get("day") == day and existing.get("name") == name:
            return
    events.append({
        "day": day,
        "name": name,
        "desc": desc,
        "tag": "[QUEST]",
        "fixed": False,
    })


# ── Queries ───────────────────────────────────────────────────────────────────

def quest_state(player, quest_id):
    """'active' | 'ready' | 'completed' | 'declined' | None."""
    return _status(player, quest_id)


def has_quest(player, quest_id):
    """True if the quest is active, ready, completed or declined."""
    return _status(player, quest_id) is not None


def get_resonance_tier(player):
    """The player's current Command Resonance tier (int)."""
    return ensure_quest_state(player).get("resonance_tier", 0)


def get_player_grade(player):
    """The player's current Command Resonance grade dict (name/front/bench)."""
    return get_resonance_grade(get_resonance_tier(player))


def _recruit_ally_keys(player):
    """Distinct species keys of recruited allies (Wonderland temps excluded)."""
    return {a.get("key") for a in player.get("allies", [])
            if a.get("key") and not a.get("_wonderland_temp")}


def _owned_girl_keys(player):
    """Distinct species keys owned: recruits + girls living in any house."""
    keys = set(_recruit_ally_keys(player))
    for house in (player.get("houses") or {}).values():
        keys.update(g.get("key") for g in house.get("monster_girls", [])
                    if g.get("key"))
    return keys


def compute_roster_tier(player):
    """The Command Resonance tier earned by the household (0-5).

    Milestones (see RESONANCE_GRADES / docs/quest_system_design.md):
      1  a home and a first captured girl
      2  a first recruited ally
      3  three distinct recruited allies
      4  six distinct girls owned, spanning 3+ races
      5  ten+ distinct girls, 5+ races, and a marriage
    """
    if not (player.get("houses") or {}):
        return 0

    owned_keys = _owned_girl_keys(player)
    if not owned_keys:
        return 0
    tier = 1

    recruit_keys = _recruit_ally_keys(player)
    if not recruit_keys:
        return tier
    tier = 2

    if len(recruit_keys) < 3:
        return tier
    tier = 3

    if len(owned_keys) < 6:
        return tier

    races = _owned_races(owned_keys)
    if len(races) < 3:
        return tier
    tier = 4

    if len(owned_keys) >= 10 and len(races) >= 5 and player.get("married_girls"):
        tier = 5
    return tier


def _owned_races(owned_keys):
    """Distinct primary races among owned girls (species key -> ENEMIES race)."""
    from resources.enemies import ENEMIES
    races = set()
    for key in owned_keys:
        entry = ENEMIES.get(key)
        if entry and entry.get("race"):
            races.add(entry["race"])
    return races


def sync_resonance_tier(player):
    """Monotonic backfill: keep the tier in step with the household.

    Capability follows the collection (the Field Study quests narrate it),
    so old saves are rated from their current roster the first time they
    sync, and milestones reached out of order still count.
    Returns display messages when the tier rises.
    """
    computed = compute_roster_tier(player)
    state = ensure_quest_state(player)
    if computed <= state.get("resonance_tier", 0):
        return []
    state["resonance_tier"] = computed
    _refresh_resonance_orb(player)
    message = f"📜 Command Resonance — new grade: {get_grade_name(computed)}"
    orb = _find_resonance_orb(player)
    if orb is not None:
        message += f" — the orb is now a {orb['name']}."
    return [message]


# ── Resonance Orb (Voss's resonance blank) ────────────────────────────────────

def _find_resonance_orb(player):
    for item in player.get("inventory", []):
        if item.get("id") == "resonance_orb":
            return item
    return None


def _refresh_resonance_orb(player):
    """Sync the orb's name/rarity/lore/fill-meter to the current tier."""
    orb = _find_resonance_orb(player)
    if orb is None:
        return None
    tier = get_resonance_tier(player)
    state = get_orb_state(tier)
    grade = get_resonance_grade(tier)

    orb["name"] = state["name"]
    orb["rarity"] = state["rarity"]
    orb["resonance_meter"] = format_orb_meter(tier)

    lines = [orb["resonance_meter"], "", state["lore"], "",
             f"Grade: {grade['name']} — {grade['front']} front / {grade['bench']} bench"]
    nxt = get_next_grade(tier)
    if nxt:
        _, nxt_grade, req = nxt
        lines.append(f"Next: {nxt_grade['name']} — {req}")
    else:
        lines.append("The orb is whole, and it sings.")
    orb["description"] = "\n".join(lines)
    return orb


def grant_resonance_orb(player):
    """Grant Voss's resonance blank (idempotent). Returns display lines."""
    orb = _find_resonance_orb(player)
    if orb is None:
        from resources.items import build_item
        from inventory import add_item_to_inventory
        orb = build_item("resonance_orb")
        add_item_to_inventory(player, orb)      # key items bypass bag limits
    orb = _refresh_resonance_orb(player) or orb
    return [f"🔮 Resonance blank received: {orb['name']}"]


def _sync_resonance_orb(player):
    """Grant (backfill old saves) and refresh the orb during sync passes."""
    state = ensure_quest_state(player)
    orb = _find_resonance_orb(player)
    if orb is not None:
        _refresh_resonance_orb(player)
        return []
    if not state["flags"].get("met_voss"):
        return []
    grant_resonance_orb(player)
    orb = _find_resonance_orb(player)
    if orb is None:
        return []
    return [f"📜 The resonance blank settles into your bag: {orb['name']}."]


# ── Starting / progressing / completing ──────────────────────────────────────

def start_quest(player, quest_id):
    """Begin a quest. Returns display messages."""
    quest = QUESTS.get(quest_id)
    if quest is None:
        return []                               # content not shipped yet
    state = ensure_quest_state(player)
    if quest_id in state["completed"] or quest_id in state["active"]:
        return []
    if not _prereq_met(player, quest):
        return []

    state["active"][quest_id] = {
        "objectives": {_objective_key(o["type"], o["target"]): False
                       for o in _quest_objectives(quest)},
        "started_day": player.get("day", 1),
    }
    state["declined"] = [q for q in state["declined"] if q != quest_id]

    # Objectives that are already true (old saves, weird ordering) resolve now.
    _sync_state_objectives(player)
    messages = _complete_ready_quests(player)
    messages.extend(sync_resonance_tier(player))
    sync_journal(player)

    kind = "Main Quest" if quest.get("type") == "main" else "Side Quest"
    _record_journal_event(player, f"Quest Started: {quest['name']}",
                          quest.get("journal_desc", ""))
    return [f"📜 New {kind}: {quest['name']}"] + messages


def notify_objective(player, obj_type, target):
    """Hook-friendly alias for update_quests(player, obj_type, target)."""
    return update_quests(player, obj_type, target)


def update_quests(player, obj_type=None, target=None):
    """Single entry point for quest hooks. Fire-and-forget safe.

    - Records visited services (``visit_service`` hooks).
    - Marks matching objectives done across all active quests.
    - Resolves state-based objectives and auto-completes finished quests.
    Returns display messages.
    """
    state = ensure_quest_state(player)
    messages = []

    if obj_type == "visit_service" and target:
        if target not in state["seen_services"]:
            state["seen_services"].append(target)

    if obj_type and target:
        key = _objective_key(obj_type, target)
        for quest_id, entry in state["active"].items():
            if key in entry["objectives"] and not entry["objectives"][key]:
                entry["objectives"][key] = True
                quest = QUESTS.get(quest_id)
                if (quest and quest.get("turn_in")
                        and all(entry["objectives"].values())):
                    messages.append(f"📜 {quest['name']} — ready to turn in.")

    _sync_state_objectives(player)
    messages.extend(_complete_ready_quests(player))
    messages.extend(_sync_quest_chain(player))
    messages.extend(_sync_resonance_orb(player))
    messages.extend(sync_resonance_tier(player))
    sync_journal(player)
    return messages


def _sync_quest_chain(player):
    """Start 'next' quests whose predecessor is already completed.

    Catches saves that finished a quest before its follow-up content existed
    (e.g. old saves that resolved past MQ2 before MQ3-MQ6 were registered).
    Returns display messages.
    """
    state = ensure_quest_state(player)
    messages = []
    for quest_id in list(state["completed"]):
        quest = QUESTS.get(quest_id)
        if not quest:
            continue
        next_id = (quest.get("rewards") or {}).get("next")
        if next_id and next_id not in state["completed"] and next_id not in state["active"]:
            messages.extend(start_quest(player, next_id))
    return messages


def complete_quest(player, quest_id):
    """Complete a quest (auto path or NPC turn-in). Returns display messages."""
    quest = QUESTS.get(quest_id)
    state = ensure_quest_state(player)
    if quest is None or quest_id not in state["active"]:
        return []

    day = player.get("day", 1)
    del state["active"][quest_id]
    state["completed"].append(quest_id)
    state["completed_days"][quest_id] = day

    messages = [f"📜 Quest complete: {quest['name']}"]
    messages.extend(_grant_rewards(player, quest))
    sync_journal(player)
    _record_journal_event(player, f"Quest Complete: {quest['name']}",
                          f"You completed \"{quest['name']}\".")

    next_id = (quest.get("rewards") or {}).get("next")
    if next_id:
        messages.extend(start_quest(player, next_id))
    return messages


def _grant_rewards(player, quest):
    """Grant a quest's rewards. Returns display messages."""
    rewards = quest.get("rewards") or {}
    messages = []

    xp = int(rewards.get("xp", 0))
    if xp > 0:
        from leveling import gain_exp
        gain_exp(player, xp)
        messages.append(f"   +{xp} XP")

    gold = int(rewards.get("gold", 0))
    if gold > 0:
        player["gold"] = player.get("gold", 0) + gold
        messages.append(f"   +{gold} gold")

    for item_spec in rewards.get("items", []):
        from resources.items import build_item
        from inventory import add_item_to_inventory
        item = build_item(item_spec["id"], rarity=item_spec.get("rarity", "common"))
        if add_item_to_inventory(player, item):
            messages.append(f"   Received: {item['name']}")
        else:
            ensure_quest_state(player)["pending_items"].append(item)
            messages.append(f"   {item['name']} (bag full — reward held for later)")

    for flag in rewards.get("flags", []):
        ensure_quest_state(player)["flags"][flag] = True

    tier = rewards.get("grade_unlock")
    if tier is not None:
        state = ensure_quest_state(player)
        if tier > state.get("resonance_tier", 0):
            state["resonance_tier"] = tier
            messages.append(
                f"   Command Resonance — new grade: {get_grade_name(tier)}"
            )
    return messages


def _complete_ready_quests(player):
    """Auto-complete quests (no turn-in NPC) whose objectives are all done."""
    state = ensure_quest_state(player)
    messages = []
    for quest_id in list(state["active"].keys()):
        quest = QUESTS.get(quest_id)
        if not quest or quest.get("turn_in"):
            continue
        entry = state["active"][quest_id]
        if all(entry["objectives"].values()):
            messages.extend(complete_quest(player, quest_id))
    return messages


# ── State-based objective checks ──────────────────────────────────────────────
# Objectives whose truth can be read directly from player state (safe for old
# saves and out-of-order play). Everything else needs an explicit hook call.

def _owned_girl_count(player):
    """Monster girls owned: recruited allies + girls living in any house."""
    count = len(player.get("allies", []))
    for house in player.get("houses", {}).values():
        count += len(house.get("monster_girls", []))
    return count


_STATE_CHECKS = {
    "visit_city":    lambda player, target: player.get("location") == target,
    "visit_service": lambda player, target: target in ensure_quest_state(player)["seen_services"],
    # Field Study checks — read straight from owned state (old-save friendly).
    "own_house":        lambda player, target: bool(player.get("houses")),
    "capture_girl":     lambda player, target: _owned_girl_count(player) >= 1,
    "recruit_count":    lambda player, target: len(_recruit_ally_keys(player)) >= int(target),
    "collection_count": lambda player, target: len(_owned_girl_keys(player)) >= int(target),
    "race_count":       lambda player, target: len(_owned_races(_owned_girl_keys(player))) >= int(target),
    "married":          lambda player, target: len(player.get("married_girls", [])) >= int(target),
}


def _sync_state_objectives(player):
    """Mark any state-satisfied objectives done (no messages)."""
    state = ensure_quest_state(player)
    for quest_id in list(state["active"].keys()):
        quest = QUESTS.get(quest_id)
        if not quest:
            continue
        entry = state["active"][quest_id]
        for obj in _quest_objectives(quest):
            key = _objective_key(obj["type"], obj["target"])
            if entry["objectives"].get(key):
                continue
            check = _STATE_CHECKS.get(obj["type"])
            if check and check(player, obj["target"]):
                entry["objectives"][key] = True


# ── Journal display mirror ────────────────────────────────────────────────────

def sync_journal(player):
    """Rebuild the Journal quest lists from canonical state.

    THIS IS THE ONLY FUNCTION allowed to write
    ``journal["main_quests"]`` / ``journal["side_quests"]``.
    """
    state = ensure_quest_state(player)
    journal = player.setdefault("journal", {})
    journal.setdefault("events", [])

    def _entry(quest_id, status):
        quest = QUESTS.get(quest_id)
        if quest is None:
            return None
        completed = status == "complete"
        active = state["active"].get(quest_id, {})
        objectives = []
        for obj in _quest_objectives(quest):
            key = _objective_key(obj["type"], obj["target"])
            done = active.get("objectives", {}).get(key, completed)
            objectives.append({
                "label": obj.get("label", key),
                "done": bool(done),
            })
        day = (state["completed_days"].get(quest_id)
               if completed else active.get("started_day", player.get("day", 1)))
        return {
            "id": quest_id,
            "name": quest["name"],
            "desc": quest.get("journal_desc", ""),
            "day": day or player.get("day", 1),
            "status": status,
            "objectives": objectives,
        }

    main, side = [], []
    for quest_id, entry in state["active"].items():
        quest = QUESTS.get(quest_id)
        if not quest:
            continue
        status = ("ready" if quest.get("turn_in")
                  and all(entry["objectives"].values()) else "active")
        item = _entry(quest_id, status)
        (main if quest["type"] == "main" else side).append(item)

    for quest_id in state["completed"]:
        quest = QUESTS.get(quest_id)
        if not quest:
            continue
        item = _entry(quest_id, "complete")
        (main if quest["type"] == "main" else side).append(item)

    journal["main_quests"] = [e for e in main if e]
    journal["side_quests"] = [e for e in side if e]


# ── Story beats (delivered as StoryScreens on city entry) ────────────────────

def queue_story(player, beat_id):
    """Queue a story beat for delivery the next time the player enters a city."""
    state = ensure_quest_state(player)
    if beat_id not in state["story_queue"]:
        state["story_queue"].append(beat_id)


def has_pending_story(player):
    return bool(ensure_quest_state(player)["story_queue"])


def pop_pending_story(player):
    """Pop the next queued story beat id, or None."""
    state = ensure_quest_state(player)
    return state["story_queue"].pop(0) if state["story_queue"] else None


# ── Side quest offers ─────────────────────────────────────────────────────────

def offer_side_quest(player, quest_id):
    """True if the quest can be offered to the player right now."""
    quest = QUESTS.get(quest_id)
    if quest is None or quest.get("type") != "side":
        return False
    if _status(player, quest_id) in ("active", "ready", "completed"):
        return False
    return _prereq_met(player, quest)


def decline_quest(player, quest_id):
    """Record a declined side quest offer (it can be re-offered later)."""
    state = ensure_quest_state(player)
    if quest_id not in state["declined"]:
        state["declined"].append(quest_id)
