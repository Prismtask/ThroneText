from combat.combat_io import c_print, c_input
# combat/capture.py
import random

import karma
from combat.stats import get_effective_attribute
from inventory import remove_item_by_reference

def is_monster_girl(enemy):
    """Check the explicit monster_girl flag set in monster_girls.yaml."""
    return bool(enemy.get("monster_girl"))


def is_capturable(enemy):
    """Check if an enemy is a capturable monster girl.

    Heroines (those with _heroine set) are monster girls but are recruited
    through quests, not captured via nets.
    """
    return is_monster_girl(enemy) and not enemy.get("_heroine")


# ── Status-based capture bonuses ─────────────────────────────────────────
# A girl who cannot move or fight back is far easier to net. Values are
# percentage points added to the final capture chance. The total is capped
# so stacked debuffs cannot make every capture automatic.
#
# ``staggered`` is a leftover stun state: a Stun Bomb stuns for one enemy
# action, which would normally be consumed before the player's next turn.
# ``enemy_ai`` leaves ``capture_stagger`` behind so the window survives
# until the net can actually be thrown.
CAPTURE_STATUS_BONUSES = {
    "stunned": 35,
    "staggered": 35,
    "paralyzed": 35,
    "asleep": 30,
    "frozen": 25,
    "entombed": 20,
    "slowed": 10,
    "blinded": 10,
    "confused": 10,
    "weakened": 5,
}
CAPTURE_STATUS_BONUS_CAP = 50


def get_capture_status_bonus(target):
    """Return ``(bonus, labels)`` for conditions that hinder a capture target.

    Bonuses are percentage points. ``labels`` are player-facing adjectives
    ("stunned", "off-balance", ...) used by the combat log.
    """
    bonus = 0
    labels = []

    def add(key, label):
        nonlocal bonus
        bonus += CAPTURE_STATUS_BONUSES[key]
        labels.append(label)

    # Stun itself is consumed when the enemy loses a turn, so also accept
    # the stagger marker it leaves behind (see enemy_ai.begin_enemy_turn).
    if target.get("stunned"):
        add("stunned", "stunned")
    elif int(target.get("capture_stagger", 0) or 0) > 0:
        add("staggered", "off-balance")

    if target.get("paralyzed"):
        add("paralyzed", "paralyzed")
    if target.get("asleep"):
        add("asleep", "asleep")
    if target.get("frozen"):
        add("frozen", "frozen")
    if target.get("entombed"):
        add("entombed", "entombed")
    if target.get("slowed"):
        add("slowed", "slowed")
    if target.get("blinded"):
        add("blinded", "blinded")
    if target.get("confused"):
        add("confused", "confused")
    if any(d.get("type") == "weaken" for d in target.get("active_debuffs", [])):
        add("weakened", "weakened")

    return min(CAPTURE_STATUS_BONUS_CAP, bonus), labels


def get_capture_chance(player, target, net):
    """Return the final capture chance (5–95) for ``net`` against ``target``.

    Shared by the actual roll and the target-selection previews so the number
    the player sees is exactly the number that gets rolled. Guaranteed nets
    return 100; level-gated nets return 0 for out-of-range targets.
    """
    net = net or {}
    if not net_can_capture(net, target):
        return 0
    if net.get("guaranteed_capture"):
        return 100

    cha = get_effective_attribute(player, "Charisma")
    dex = get_effective_attribute(player, "Dexterity")
    rarity_mult_bonus = net.get("rarity_mult_bonus", 25)

    max_hp = target.get("max_hp") or target.get("hp") or 1
    hp_percent = target.get("hp", 0) / max_hp
    difficulty = target.get("level", 1) * 1.2 + (1 - hp_percent) * 40

    chance = (cha + dex) * 0.8 + rarity_mult_bonus - difficulty
    from combat.stat_milestones import get_charisma_bonus
    from combat.weapon.wedding_specials import apply_wedding_capture_bonus
    chance += get_charisma_bonus(player) + apply_wedding_capture_bonus(player)
    chance = max(5, min(95, chance))

    # Daily events: Monster Girl Season (+15) / Wary Prey (-10)
    chance += player.get("daily_effects", {}).get("capture_bonus", 0)
    chance = max(5, min(95, chance))

    # Deed titles: small capture-chance bonus (capped in titles.mod).
    from titles import mod as _title_mod
    chance += _title_mod(player, "capture_pct") * 100
    chance = max(5, min(95, chance))

    # Disabling status effects (stun, sleep, paralysis, ...).
    chance += get_capture_status_bonus(target)[0]

    return max(5, min(95, chance))


def get_capture_message(enemy, player):
    """Personalized capture message from the enemy's dialogue block."""
    dialogue = enemy.get("dialogue", {})
    template = dialogue.get("capture")

    if template:
        return template.format(
            name=enemy.get("name", "the girl"),
            player=player.get("name", "Adventurer")
        )

    # Fallback
    return f"{enemy.get('name', 'The creature')} is captured and gently bound by your net!"


def net_capture_level_cap(net):
    """Exclusive enemy-level ceiling for a net, or None when it has no limit.

    The Stellar Field Kit sets ``capture_level_cap`` to 8, so it can only
    hold monster girls of level 1-7.
    """
    if not net:
        return None
    try:
        cap = int(net.get("capture_level_cap") or 0)
    except (TypeError, ValueError):
        return None
    return cap if cap > 0 else None


def net_can_capture(net, target):
    """True if `net` may be thrown at `target` (level-gated nets only)."""
    cap = net_capture_level_cap(net)
    if cap is None:
        return True
    try:
        level = int(target.get("level", 1) or 1)
    except (TypeError, ValueError):
        level = 1
    return level < cap


def net_level_gate_message(net, target):
    """Player-facing reason a level-gated net refused a target."""
    cap = net_capture_level_cap(net) or 0
    name = (net or {}).get("name", "That net")
    return (f"The {name} only holds monster girls below level {cap} — "
            f"{target.get('name', 'she')} is level {target.get('level', '?')}.")


def _mark_stellar_kit_used(player, net):
    """Mark Voss's loan as spent so the Star Tower can reissue one."""
    if (net or {}).get("id") != "stellar_field_kit":
        return
    from quests import ensure_quest_state
    flags = ensure_quest_state(player)["flags"]
    flags["stellar_field_kit"] = True
    flags["stellar_field_kit_used"] = int(flags.get("stellar_field_kit_used", 0) or 0) + 1


def attempt_capture(player, target, net=None):
    """Main capture logic using the monster_girl flag.

    This function owns net consumption — callers must NOT remove the net
    themselves:
    - a level-gated net (Stellar Field Kit) refuses out-of-range targets and
      is NOT spent;
    - otherwise the net is spent on the throw, even if the player has no
      house to keep the girl in;
    - guaranteed nets (Stellar Field Kit) always catch inside their cap.
    """
    if not is_capturable(target):
        if target.get("_heroine"):
            c_print("This heroine cannot be captured — she must be recruited through her quest.")
        else:
            c_print("This enemy cannot be captured.")
        return False

    if net is None:
        # Find capture net in inventory
        net = next((item for item in player.get("inventory", [])
                    if item.get("capture_net")), None)
        if not net:
            c_print("You need a Capture Net to attempt this!")
            return False

    if not net_can_capture(net, target):
        c_print(net_level_gate_message(net, target))
        return False

    # The net is spent the moment it is thrown.
    remove_item_by_reference(player, net)
    _mark_stellar_kit_used(player, net)

    # Success calculation
    guaranteed = bool(net.get("guaranteed_capture"))
    success = guaranteed
    if not success:
        success_chance = get_capture_chance(player, target, net)
        status_bonus, status_labels = get_capture_status_bonus(target)
        status_note = ""
        if status_bonus > 0:
            status_note = (f" - she is {', '.join(status_labels)}, "
                           f"+{status_bonus}%")
        c_print(f"(Capture chance: {success_chance:.0f}%{status_note})")

        success = random.uniform(0, 100) < success_chance

    if success:
        # No emoji border — capture text is surfaced as a combat notice and
        # long decorated lines overflowed the 3-line combat feed.
        c_print("\n" + get_capture_message(target, player))
        if guaranteed:
            c_print("(The Stellar Field Kit's weave closes.)")

        stored = store_captured_girl(player, target)
        target["captured"] = True

        # Bestiary: a successful capture fills the entry even if the house
        # was full / she was released as a duplicate.
        from bestiary import record_capture
        record_capture(player, target)

        # Quest hook: only counts when she actually joined the household
        if stored:
            from quests import update_quests
            for msg in update_quests(player, "capture_girl", "any"):
                c_print(msg)
        return True
    else:
        c_print(f"The {target.get('name')} slips through your net and escapes!")
        return False


from facilities.house import HOUSE_MONSTER_GIRL_LIMITS

def store_captured_girl(player, mg):
    """Store captured monster girl in the player's house."""
    houses = player.get("houses", {})
    if not houses:
        c_print("You need a house to keep her!")
        return False

    # Only one house allowed — use the player's home regardless of location
    house_city, house = next(iter(houses.items()))

    # ── Duplicate check ──────────────────────────────────────────────────────
    mg_key = mg.get("key", "")
    existing = None
    for girl in house.get("monster_girls", []):
        if girl.get("key") == mg_key:
            existing = girl
            break
    if not existing:
        for ally in player.get("allies", []):
            if ally.get("key") == mg_key:
                existing = ally
                break

    if existing:
        c_print(f"\nYou already have {mg.get('name', 'a girl')} in your household!")
        standard = mg.get("level", 1) * 50 + 100
        slaver = int(round(standard * 1.6))
        karma_on = karma.is_enabled(player)
        if karma_on:
            c_print(f"1. Sell her to a licensed broker — {standard} gold")
            c_print(f"2. Sell her to a slaver — {slaver} gold (-5 Karma)")
            c_print(f"3. Release her back to the wild (+1 Karma)")
            c_print(f"4. Let her bond with your existing {existing.get('name', 'girl')} (+20 affection)")
        else:
            c_print(f"1. Sell her to a licensed broker — {standard} gold")
            c_print(f"2. Release her back to the wild")
            c_print(f"3. Let her bond with your existing {existing.get('name', 'girl')} (+20 affection)")
        dup_choice = c_input("CAPTURE_DUPLICATE_CHOICE:").strip()

        if karma_on:
            broker_key, slaver_key, release_key, bond_key = "1", "2", "3", "4"
        else:
            broker_key, slaver_key, release_key, bond_key = "1", None, "2", "3"

        if dup_choice == broker_key:
            player["gold"] = player.get("gold", 0) + standard
            c_print(f"Sold the captured {mg.get('name', 'girl')} to a licensed broker for {standard} gold.")
            c_print(f"  Gold: {player['gold']}")
            return False
        elif slaver_key and dup_choice == slaver_key:
            player["gold"] = player.get("gold", 0) + slaver
            applied = karma.change_karma(player, -5, "Sold a captured girl to a slaver")
            c_print(f"Sold the captured {mg.get('name', 'girl')} to a slaver for {slaver} gold.")
            if applied:
                tier = karma.get_karma_tier(player)
                c_print(f"  Karma {applied:+d} ({tier['label']} {karma.get_karma(player):+d})")
            c_print(f"  Gold: {player['gold']}")
            return False
        elif dup_choice == bond_key:
            aff_cap = existing.get("affection_cap", 200)
            existing["affection"] = min(aff_cap, existing.get("affection", 30) + 20)
            c_print(f"Your {existing.get('name', 'girl')} bonded with the newcomer!")
            c_print(f"  Affection +20 (now {existing['affection']}/{aff_cap})")
            return False
        else:
            applied = karma.change_karma(player, 1, "Released a captured girl")
            c_print(f"You release the captured {mg.get('name', 'girl')} back to the wild.")
            if applied:
                tier = karma.get_karma_tier(player)
                c_print(f"  Karma {applied:+d} ({tier['label']} {karma.get_karma(player):+d})")
            return False

    max_girls = HOUSE_MONSTER_GIRL_LIMITS.get(house.get("level", 1), 2)
    total_girls = len(house.get("monster_girls", [])) + len(player.get("allies", []))
    if total_girls >= max_girls:
        c_print(f"Your house is already full (max {max_girls} monster girls).")
        standard = mg.get("level", 1) * 50 + 100
        slaver = int(round(standard * 1.6))
        karma_on = karma.is_enabled(player)
        if karma_on:
            c_print(f"1. Sell her to a licensed broker — {standard} gold")
            c_print(f"2. Sell her to a slaver — {slaver} gold (-5 Karma)")
            c_print(f"3. Release her back to the wild (+1 Karma)")
        else:
            c_print(f"1. Sell her to a licensed broker — {standard} gold")
            c_print(f"2. Release her back to the wild")
        full_choice = c_input("CAPTURE_FULL_CHOICE:").strip()
        if full_choice == "1":
            player["gold"] = player.get("gold", 0) + standard
            c_print(f"Sold the captured {mg.get('name', 'girl')} for {standard} gold.")
            return False
        if karma_on and full_choice == "2":
            player["gold"] = player.get("gold", 0) + slaver
            applied = karma.change_karma(player, -5, "Sold a captured girl to a slaver")
            c_print(f"Sold the captured {mg.get('name', 'girl')} to a slaver for {slaver} gold.")
            if applied:
                tier = karma.get_karma_tier(player)
                c_print(f"  Karma {applied:+d} ({tier['label']} {karma.get_karma(player):+d})")
            return False
        applied = karma.change_karma(player, 1, "Released a captured girl")
        c_print(f"You release the captured {mg.get('name', 'girl')} back to the wild.")
        if applied:
            tier = karma.get_karma_tier(player)
            c_print(f"  Karma {applied:+d} ({tier['label']} {karma.get_karma(player):+d})")
        return False

    from combat.weapon.wedding_specials import apply_wedding_capture_affection_bonus
    base_affection = 20 + apply_wedding_capture_affection_bonus(player)

    captured_level = mg.get("level", 1)
    house.setdefault("monster_girls", []).append({
        "key": mg.get("key"),
        "name": mg.get("name"),
        "level": captured_level,
        "affection": base_affection,
        "affection_cap": 200,
        "captured_on": player.get("day", 1),
        "exp": 0,
        "level_hp_bonus": max(0, (captured_level - 1) * 4),
        "level_cap": 10,
        "growth_applied": 0,
        # Family system defaults (docs/family_system_design.md)
        "pregnant": False,
        "conceived_day": 0,
        "due_day": 0,
        "next_conception_day": 0,
        "pregnancy_pity": 0,
        "is_trueborn": False,
        "no_romance": False,
    })
    c_print(f"💕 {mg.get('name')} has been added to your house in {house_city}!")
    if base_affection > 20:
        c_print(f"  (Regal Presence — she starts with {base_affection} affection!)")
    return True