"""heroine_quests/sylvana_mirror.py — The Cracked Mirror (Sylvana).

Quest content lives with Sylvana's entry in
``resources/enemies/enemies_data/heroines.yaml``::

    sylvana:
      quest:
        id: sylvana_mirror
        title: The Cracked Mirror
        item: cracked_mirror
        repair_step: 5
        repair_blocks: 6
        milestone_lines:
          0: "…"

This module owns the rules and actions:

    is_available(player)   can the quest be offered at all?
    menu_label(player)     entry label for a house/city/dungeon menu
    progress(player)       current restoration percentage (0–100)
    can_mend(player)       eligibility to spend time mending
    mend(player)           spend time blocks and advance progress
    can_recruit(player)    eligibility to bring her through
    recruit(player, …)     party-full handling + recruit
    run_quest(player, …)   the interactive quest screen

Per-player progress lives in the save data (never YAML)::

    player["sylvana_mirror_repair"]  int, 0–100
    player["sylvana_mirror_fixed"]   bool, mirror fully restored
    player["sylvana_recruited"]      bool, she joined the party
    player["sylvana_mirror_obtained"] bool, key item first picked up
"""

from gui.terminal import term as _default_term
from utils import display_name

QUEST_ID = "sylvana_mirror"
HEROINE_KEY = "sylvana"
MIRROR_ITEM_ID = "cracked_mirror"
DEFAULT_TITLE = "The Cracked Mirror"
DEFAULT_REPAIR_STEP = 5
DEFAULT_REPAIR_BLOCKS = 6

# Milestone dialogue buckets (progress rounded down to this interval).
MILESTONE_INTERVAL = 5

# Fallback content if the YAML entry is missing (old saves / stripped data).
_DEFAULT_MILESTONE_LINES = {
    0: "A cracked mirror shard sits in the lounge. A woman watches you from behind the glass, saying nothing.",
    5: "A hairline crack closes. The woman in the glass blinks. '...You came back.'",
    10: "The glass warms under your hand. 'I had forgotten what warmth felt like,' she says.",
    15: "'You are wasting your time,' the reflection says — but she does not look away.",
    20: "'Most people leave the mirror in the dark,' she murmurs. 'You keep bringing light.'",
    25: "Two shards align. For an instant, two Sylvana eyes watch you instead of a thousand.",
    30: "'I copied whoever I needed to be,' she says. 'It was easier than being no one.'",
    35: "'Why do you keep looking at the cracks?' she asks. 'There is nothing beautiful in them.'",
    40: "'I do not remember my own face,' she admits. 'Only yours.'",
    45: "A long fracture fades. She stands a little straighter on the other side.",
    50: "'Half whole,' she says. 'Half a queen. Half a person. What is left of me worth keeping?'",
    55: "'You could stop,' she says. 'I would understand.' You do not stop.",
    60: "The surface steadies. For a moment, your reflections stand side by side.",
    65: "'When I am whole, I will owe you a debt I cannot repay,' she says.",
    70: "'Do not mistake gratitude for softness,' she warns, but her voice has gone gentle.",
    75: "She presses a hand to the inside of the glass. You press yours to the other side.",
    80: "'A thousand faces,' she says. 'None of them mine. This one is. I want to keep it.'",
    85: "Her reflection no longer lags behind her movements. She looks... present.",
    90: "'When the last crack closes,' she says, 'I will step out. If you will have me.'",
    95: "One crack remains. For the first time, the Queen of Mirrors looks nervous.",
    100: "The last crack closes. The glass turns to light — and Sylvana steps out, whole.",
}


# ── Quest content from YAML ─────────────────────────────────────────────────

def _quest_def():
    """Return Sylvana's ``quest`` mapping from heroines.yaml (or {})."""
    try:
        from resources.enemies import ENEMIES
        entry = ENEMIES.get(HEROINE_KEY) or {}
        quest = entry.get("quest") or {}
        if isinstance(quest, dict):
            return quest
    except Exception:
        pass
    return {}


def quest_title():
    return str(_quest_def().get("title") or DEFAULT_TITLE)


def mirror_item_id():
    return str(_quest_def().get("item") or MIRROR_ITEM_ID)


def repair_step():
    """Restoration percentage gained per mend."""
    try:
        return max(1, int(_quest_def().get("repair_step", DEFAULT_REPAIR_STEP)))
    except (TypeError, ValueError):
        return DEFAULT_REPAIR_STEP


def repair_blocks():
    """Time blocks spent per mend."""
    try:
        return max(0, int(_quest_def().get("repair_blocks", DEFAULT_REPAIR_BLOCKS)))
    except (TypeError, ValueError):
        return DEFAULT_REPAIR_BLOCKS


def _milestone_table():
    raw = _quest_def().get("milestone_lines")
    if not isinstance(raw, dict):
        return dict(_DEFAULT_MILESTONE_LINES)
    table = {}
    for key, line in raw.items():
        try:
            table[int(key)] = str(line)
        except (TypeError, ValueError):
            continue
    return table or dict(_DEFAULT_MILESTONE_LINES)


def milestone_line(progress_value):
    """Return Sylvana's response for the current restoration percentage."""
    try:
        progress_value = max(0, min(100, int(progress_value)))
    except (TypeError, ValueError):
        progress_value = 0
    key = (progress_value // MILESTONE_INTERVAL) * MILESTONE_INTERVAL
    table = _milestone_table()
    return table.get(key, table.get(0, _DEFAULT_MILESTONE_LINES[0]))


# ── Per-player save state ───────────────────────────────────────────────────

def ensure_state(player):
    """Ensure the quest's progress fields exist in the save."""
    player.setdefault("sylvana_mirror_repair", 0)
    player.setdefault("sylvana_mirror_fixed", False)
    player.setdefault("sylvana_recruited", False)
    player.setdefault("sylvana_mirror_obtained", False)


def progress(player):
    """Current restoration percentage, clamped to 0–100."""
    try:
        return max(0, min(100, int(player.get("sylvana_mirror_repair", 0) or 0)))
    except (TypeError, ValueError):
        return 0


def is_whole(player):
    return progress(player) >= 100 or bool(player.get("sylvana_mirror_fixed"))


def has_mirror(player):
    from inventory import has_item
    return has_item(player, mirror_item_id())


def is_available(player):
    """True when the house (or another hub) should offer the quest."""
    if player.get("sylvana_recruited"):
        return False
    return has_mirror(player) or bool(player.get("sylvana_mirror_fixed"))


def menu_label(player):
    """Menu label for the quest entry point."""
    if progress(player) >= 100:
        return "The Whole Mirror"
    return f"{quest_title()} ({progress(player)}% whole)"


# ── Rules / actions ─────────────────────────────────────────────────────────

def can_mend(player):
    """Return (eligible, reason) for spending time on the mirror."""
    if player.get("sylvana_recruited"):
        return False, "already recruited"
    if not is_available(player):
        return False, "no cracked mirror"
    if progress(player) >= 100:
        return False, "mirror is whole"
    return True, "ready"


def can_recruit(player):
    """Return (eligible, reason) for bringing Sylvana through."""
    if player.get("sylvana_recruited"):
        return False, "already recruited"
    if not is_whole(player):
        return False, "mirror is not whole"
    return True, "ready"


def mend(player):
    """Spend time and advance the restoration.

    Returns a dict::
        {"ok": bool, "reason": str, "progress": int, "complete": bool,
         "blocks": int, "step": int}
    """
    eligible, reason = can_mend(player)
    if not eligible:
        return {"ok": False, "reason": reason, "progress": progress(player),
                "complete": is_whole(player), "blocks": 0, "step": 0}

    import time_blocks
    blocks = repair_blocks()
    step = repair_step()
    time_blocks.wait_blocks(player, blocks)

    new_progress = min(100, progress(player) + step)
    player["sylvana_mirror_repair"] = new_progress
    if new_progress >= 100:
        player["sylvana_mirror_fixed"] = True
    return {"ok": True, "reason": "mended", "progress": new_progress,
            "complete": new_progress >= 100, "blocks": blocks, "step": step}


def _resolve_recruit_house(player, house):
    """Use the given house, else the player's effective home house."""
    if house is not None:
        return house
    try:
        from facilities.house.core import _resolve_house
        _, resolved = _resolve_house(player)
        return resolved
    except Exception:
        return None


def recruit(player, house=None, term=None):
    """Bring Sylvana through the whole mirror. Returns True on success."""
    t = term or _default_term
    ensure_state(player)

    from combat.ally import (
        get_ally_capacity, apply_heroine_permanent_passive, create_heroine_ally,
        ensure_party_order, get_heroine_in_party, promote_heroine_to_permanent,
        set_heroine_state, _return_ally_to_house,
    )

    existing = get_heroine_in_party(player, "sylvana")
    if existing:
        player["sylvana_recruited"] = True
        player["sylvana_mirror_fixed"] = True
        existing["affection"] = max(existing.get("affection", 0), 100)
        existing["affection_cap"] = max(existing.get("affection_cap", 100), 200)
        t.print(f"\n  {display_name(existing)} is already here, watching you from the glass.")
        t.pause()
        return True

    allies = player.setdefault("allies", [])
    capacity = get_ally_capacity(player)
    if len(allies) >= capacity:
        names = []
        for a in allies:
            hp = "[INCAPACITATED]" if a.get("current_hp", 0) <= 0 else f"HP {a.get('current_hp', 0)}/{a.get('max_hp', 1)}"
            names.append(f"{display_name(a)} — {hp}")
        names.append("Cancel")
        choice = t.menu(
            names,
            prompt=f"Your party is full ({len(allies)}/{capacity}). Who makes room for Sylvana?",
        )
        if choice < 0 or choice >= len(allies):
            t.print("\n  Sylvana waits at the mirror, patient as glass.")
            t.pause()
            return False
        resolved_house = _resolve_recruit_house(player, house)
        if resolved_house is None:
            t.print("\n  You have no home to send her back to — make room in the party first.")
            t.pause()
            return False
        replaced = allies[choice]
        _return_ally_to_house(player, replaced, resolved_house)
        allies.pop(choice)

    ally = create_heroine_ally(
        player, "sylvana", floor=player.get("saved_dungeon_floor", 1)
    )
    if ally is None:
        t.print("  (Sylvana's reflection will not hold — try again later.)")
        t.pause()
        return False

    promote_heroine_to_permanent(player, ally, ally.get("level", player.get("level", 1)))
    set_heroine_state(player, "sylvana", "permanent")
    ally["affection"] = 100
    ally["affection_cap"] = 200
    ally["no_romance"] = False

    # Her unique armour — the decaying mirror shield she carried as a boss.
    from resources.items import build_item
    from combat.elemental import compute_ally_elemental
    ally.setdefault("equipped", {})
    ally["equipped"]["armor"] = build_item("decaying_aegis", rarity="unique")
    res, dmg = compute_ally_elemental(ally)
    ally["elemental_res"] = res
    ally["elemental_dmg"] = dmg
    apply_heroine_permanent_passive(ally)

    allies.append(ally)
    ensure_party_order(player)
    player["sylvana_recruited"] = True
    player["sylvana_mirror_fixed"] = True

    # The key item becomes a keepsake; its id stays stable for old saves.
    for item in player.get("inventory", []):
        if item.get("id") == "cracked_mirror":
            item["name"] = "Sylvana's Looking Glass"
            item["description"] = (
                "A whole mirror, small enough to carry. Sylvana's reflection "
                "no longer lives behind it — but she still checks it when she "
                "thinks you are not looking."
            )
            break

    t.print("\n  The last crack closes. The glass turns to light.")
    t.print(f"  {display_name(ally)} steps out of the mirror — whole, and entirely her own person.")
    t.print(f"  She equips the Decaying Aegis and joins your party. Affection: 100/200.")
    t.pause()
    return True


def run_quest(player, house=None, term=None):
    """Interactive quest screen. Launchable from the house or any other hub."""
    t = term or _default_term
    ensure_state(player)

    if player.get("sylvana_recruited"):
        t.print("Sylvana is already with you.")
        t.pause()
        return
    if not has_mirror(player) and not player.get("sylvana_mirror_fixed"):
        t.print("You do not have the cracked mirror.")
        t.pause()
        return

    while True:
        prog = progress(player)
        step = repair_step()
        blocks = repair_blocks()
        filled = max(0, min(20, prog // MILESTONE_INTERVAL))
        bar = "#" * filled + "." * (20 - filled)
        title = quest_title()

        t.clear()
        t.print(f"=== {title.upper()} ===")
        t.print(f"  Restoration: {prog}%  [{bar}]")
        t.print()
        t.print(milestone_line(prog))
        t.print()

        if prog >= 100:
            options = ["Ask Sylvana to join you", "Back"]
        else:
            options = [f"Mend a crack (+{step}%, {blocks} time blocks)", "Back"]
        idx = t.menu(options, prompt="What will you do?")
        if idx != 0:
            return

        if prog >= 100:
            if recruit(player, house, term=t):
                return
            continue

        result = mend(player)
        if not result.get("ok"):
            # Eligibility changed between the menu and the action; redisplay.
            continue
        new_progress = result["progress"]

        t.clear()
        t.print(f"=== {title.upper()} ===")
        t.print(f"  Restoration: {new_progress}%")
        t.print()
        t.print(milestone_line(new_progress))
        if new_progress >= 100:
            t.print("\n  The mirror is whole. A woman stands on the other side, waiting.")
        t.pause()
        if new_progress >= 100:
            recruit(player, house, term=t)
            return
