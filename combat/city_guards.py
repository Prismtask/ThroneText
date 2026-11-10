"""Non-lethal city guard encounters (Karma Phase 2).

Guards are a consequence, not a farm:
- no XP, loot, bestiary entries, capture, or quest credit
- defeat or submission sends the party to jail, never the death screen
- victory, paying, or talking down only sets a city-gate cooldown
"""

import karma

_ROMAN = ("", " II", " III", " IV", " V")


def _guard_spec(tier):
    if tier == "outlaw":
        return (("city_guard_elite", 2, True), ("city_guard", 2, False))
    return (("city_guard", 3, False),)


def _make_guard(player, key, elite, index):
    from combat.stats import compute_enemy_attributes, enemy_stats
    from resources.enemies import ENEMIES

    template = ENEMIES[key]
    player_level = max(1, int(player.get("level", 1) or 1))
    level = player_level + (3 if elite else 0)
    factor = 1.0 + (0.09 if elite else 0.06) * level
    attrs = compute_enemy_attributes(key)

    guard = enemy_stats(key, player)
    guard["level"] = level
    guard["max_hp"] = max(1, int(template.get("base_hp", 60) * factor))
    guard["hp"] = guard["max_hp"]
    guard["str_mod"] = max(1, int(attrs["Strength"] * factor))
    guard["con_mod"] = max(1, int(attrs["Constitution"] * factor))
    guard["dex_mod"] = max(1, int(attrs["Dexterity"] * factor))
    guard["name"] = template["name"] + _ROMAN[min(index, len(_ROMAN) - 1)]

    # Engine / UI flags. City guards are people, not monsters.
    guard["nonlethal"] = True
    guard["no_bestiary"] = True
    guard["no_loot"] = True
    guard["no_xp"] = True
    guard["guard"] = True
    guard["monster_girl"] = False
    guard["capturable"] = False
    return guard


def spawn_city_guards(player, tier):
    """Build the guard squad for a Wanted/Outlaw gate confrontation."""
    enemies = []
    counters = {}
    for key, count, elite in _guard_spec(tier):
        for _ in range(count):
            index = counters.get(key, 0)
            counters[key] = index + 1
            enemies.append(_make_guard(player, key, elite, index))
    return enemies


def resolve_gate(player, city_id, days=3, warning=False):
    """Quiet this city's gate for ``days`` and clear the arrival check."""
    karma.ensure_state(player)
    gate = player["karma_gate"]
    day = int(player.get("day", 1) or 1)
    gate["cooldown"][city_id] = day + max(1, int(days))
    gate["check_pending"] = False
    if warning:
        gate["warning_seen"] = True


def _heal_party_to_half(player):
    from character import player_max_hp

    max_hp = player_max_hp(player)
    half = max(1, int(max_hp * 0.5))
    player["current_hp"] = max(half, int(player.get("current_hp", 0) or 0))

    for ally in player.get("allies", []):
        ally_max = max(1, int(ally.get("max_hp", 1) or 1))
        ally_half = max(1, int(ally_max * 0.5))
        ally["current_hp"] = max(ally_half, int(ally.get("current_hp", 0) or 0))
        ally["defeated"] = False
        ally.pop("dead", None)


def city_guard_victory(player, city_id):
    """The guards yield. Enter the city under watch; no Karma change."""
    karma.ensure_state(player)
    resolve_gate(player, city_id, days=3)
    player["karma_gate"]["watched_until"] = int(player.get("day", 1) or 1) + 2
    karma.add_journal(
        player,
        "The gate yields",
        "The guards lower their weapons. You are allowed through under watch.",
    )


def city_guard_flee(player, city_id):
    """Fleeing the gate quiets it for one day; no Karma change."""
    resolve_gate(player, city_id, days=1)


def city_guard_jail(player, city_id):
    """Non-lethal defeat/submission: fine, jail, morning, and slow atonement."""
    karma.ensure_state(player)
    gate = player["karma_gate"]
    day = int(player.get("day", 1) or 1)
    level = max(1, int(player.get("level", 1) or 1))
    gold = max(0, int(player.get("gold", 0) or 0))
    fine = min(gold, max(100, level * 15))
    player["gold"] = gold - fine

    _heal_party_to_half(player)
    resolve_gate(player, city_id, days=3)
    gate["watched_until"] = day + 2

    applied = 0
    if (karma.get_karma(player) < 0
            and day >= int(gate.get("jail_karma_day", -99) or -99)
            + karma.JAIL_KARMA_COOLDOWN_DAYS):
        applied = karma.change_karma_toward_zero(
            player, karma.JAIL_KARMA_GAIN, "Served your sentence"
        )
        if applied:
            gate["jail_karma_day"] = day

    karma.add_journal(
        player,
        "A night in the cells",
        f"You spent the night in a cell. The fine was {fine} gold; the city "
        f"will be watching.",
    )
    if applied:
        karma.add_journal(
            player,
            f"Time served: Karma {applied:+d}",
            "The quiet of the cell gives you time to think.",
        )

    from time_blocks import end_day
    end_day(player, slept=True)
    return {
        "fine": fine,
        "karma": applied,
        "day": player.get("day", day + 1),
    }
