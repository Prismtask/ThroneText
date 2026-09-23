# facilities/travel.py

from resources.cities import CITIES
from utils import advance_time
from character import player_max_hp
from gui.terminal import term


def _show_wonderland_cheshire_cat():
    """Show Cheshire Cat art + quote when trying to travel in Wonderland."""
    cat_art = r"""
                              .'\   /`.
                            .'.-.`-'.-.`.
                        ..._:   .-. .-.   :_...
                    .'    '-.(o ) (o ).-'    `.
                    :  _    _ _`~(_)~`_ _    _  :
                    :  /:   ' .-=_   _=-. `   ;\  :
                    :   :|-.._  '     `  _..-|:   :
                    :   `:| |`:-:-.-:-:'| |:'   :
                    `.   `.| | | | | | |.'   .'
                        `.   `-:_| | |_:-'   .'
                         `-._   ````    _.-'
                            ``-------''
"""
    term.print(cat_art)
    term.print(
        '\n"Oh, you\'re looking for a map? How delightfully linear of you.\n'
        ' There is no map. There is no \'north.\' There is only where you are,\n'
        ' and where you aren\'t, and the difference is mostly academic.\n'
        '\n'
        ' But if you must go somewhere... try the book. It\'s how you came in.\n'
        ' It\'s how you\'ll leave. Everything else is just scenery."'
    )
    term.print('\n                    \u2014 The Cheshire Cat')
    term.pause()


def _danger_tag(travel_time):
    """Return a short danger hint based on journey length."""
    if travel_time >= 200:
        return "  [⚠ Long — high encounter risk]"
    if travel_time >= 120:
        return "  [~ Moderate distance]"
    return ""


def _effective_travel_time(player, raw_time):
    """Apply mount time reduction and daily event modifiers (e.g. Heavy Rain)."""
    effective = raw_time
    mount_id = player.get("mount_id")
    if mount_id:
        from resources.mounts import get_mount
        mount = get_mount(mount_id)
        if mount:
            reduction = mount.get("time_reduction", 0)
            effective = int(raw_time * (1 - reduction))
    # Daily events: Heavy Rain makes travel take longer
    daily_mult = player.get("daily_effects", {}).get("travel_time_mult", 1.0)
    if daily_mult != 1.0:
        effective = int(effective * daily_mult)
    return effective


def travel_to_city(player, current_city_id):
    """
    Overland travel between cities (terminal mode).

    Returns
    -------
    "dead"  – player died during a travel encounter
    None    – player arrived safely (or cancelled)
    """
    from facilities.travel_events import run_travel_events

    # ── Wonderland: Cheshire Cat replaces travel ─────────────────────────
    if player.get("wonderland_active"):
        _show_wonderland_cheshire_cat()
        return

    city            = CITIES.get(current_city_id, CITIES["solmere"])
    all_connections = city.get("travel", {}).get("connections", [])
    land_routes     = [c for c in all_connections if c.get("type", "land") == "land"]

    if not land_routes:
        term.print("\nThere are no overland roads leading out of this city.")
        term.pause()
        return

    # Show mount status if any
    mount_id = player.get("mount_id")
    if mount_id:
        from resources.mounts import get_mount
        mount = get_mount(mount_id)
        if mount:
            term.print(f"\n[Your {mount['name']} is ready. "
                  f"{int(mount['time_reduction']*100)}% faster, "
                  f"{int(mount['event_mitigation']*100)}% safer]")

    options = []
    for conn in land_routes:
        dest_name = CITIES.get(conn["dest"], {}).get("name", conn["dest"])
        actual_time = _effective_travel_time(player, conn["travel_time"])
        tag       = _danger_tag(actual_time)
        options.append(f"{dest_name}  ({actual_time} min){tag}")

    choice = term.menu(options, prompt=f"=== OVERLAND TRAVEL from {city['name']} ===")

    if choice < 0 or choice >= len(land_routes):
        return

    chosen      = land_routes[choice]
    dest_id     = chosen["dest"]
    dest_name   = CITIES.get(dest_id, {}).get("name", dest_id)
    raw_time    = chosen["travel_time"]
    travel_time = _effective_travel_time(player, raw_time)

    # Use origin city biome for thematic enemy selection on this road
    origin_biome = city.get("biome", "temperate")

    return embark_journey(player, dest_id, dest_name, travel_time, origin_biome)


def embark_journey(player, dest_id, dest_name, travel_time, origin_biome="temperate",
                   combat_override=None):
    """
    Execute the actual journey (GUI-based travel events).

    Designed to be called both from the terminal travel_to_city() and from
    the GUI World Map (via FacilityScreen I/O redirection).

    Args:
        player: Player state dict.
        dest_id: Destination city key (e.g. "solmere").
        dest_name: Display name of the destination.
        travel_time: Effective travel time in minutes (after mount reduction).
        origin_biome: Biome of the origin city for thematic enemy selection.
        combat_override: Optional function(player, enemy_keys, **kwargs) -> str
            If provided, called instead of combat() for travel encounters.
            Used by the GUI to show CombatScreen as an overlay.

    Returns
    -------
    "dead"  – player died during a travel encounter
    None    – player arrived safely
    """
    from facilities.travel_events import run_travel_events

    term.print(f"\nYou shoulder your pack and step onto the road to {dest_name}.")
    term.print(f"Estimated journey: {travel_time} minutes. Keep your eyes open.")
    term.pause("Press Continue to set out...")

    # ── Travel events ────────────────────────────────────────────────────────
    outcome = run_travel_events(
        player,
        travel_time,
        travel_type="land",
        region=origin_biome,
        combat_override=combat_override,
    )

    if outcome == "dead":
        term.print("\n  You have perished on the road. Your journey ends here...")
        player["current_hp"] = 0
        term.pause()
        return "dead"

    # ── Safe arrival ─────────────────────────────────────────────────────────
    advance_time(player, travel_time)
    player["location"] = dest_id

    term.print(f"\n{'─' * 52}")
    term.print(f"  You arrive in {dest_name}.")
    term.print(f"  HP: {player.get('current_hp', '?')}/{player_max_hp(player)}"
          f"  |  Gold: {player.get('gold', 0)}")
    term.pause("  Press Continue to enter the city...")


def embark_multi_leg_journey(player, segments, combat_override=None):
    """
    Execute a multi-leg journey composed of pre-computed path segments.

    Designed to be called from WorldMapScreen after pathfinding has computed
    the route. Each segment is processed sequentially:

        1. Print leg narration (City A → City B, distance, type)
        2. If sea segment & no ship → deduct ferry cost from player gold
        3. Run travel events for the segment
        4. If player dies mid-journey → return "dead" immediately
        5. Advance time for the segment
        6. Brief stopover narration (skipped on final leg)

    Args:
        player: Player state dict.
        segments: List of segment dicts from find_shortest_path():
            {"from", "to", "type", "raw_time", "effective_time", "biome", "cost"}
        combat_override: Optional function(player, enemy_keys, **kwargs) -> str
            If provided, called instead of combat() for travel encounters.

    Returns
    -------
    "dead"  – player died during a segment encounter
    None    – player completed the full journey safely
    """
    from facilities.travel_events import run_travel_events

    total_segments = len(segments)

    for i, seg in enumerate(segments):
        is_final = (i == total_segments - 1)
        from_name = CITIES.get(seg["from"], {}).get("name", seg["from"])
        to_name = CITIES.get(seg["to"], {}).get("name", seg["to"])

        # ── Leg narration ─────────────────────────────────────────────────
        if seg["type"] == "sea":
            has_ship = player.get("has_ship", False)
            if has_ship:
                term.print(f"\n  ⛵ {from_name} → {to_name}: "
                           f"{seg['effective_time']} min at sea "
                           f"({seg['raw_time']} min base, ship bonus applied)")
            else:
                term.print(f"\n  ⛵ {from_name} → {to_name}: "
                           f"{seg['effective_time']} min ferry crossing "
                           f"(ticket: {seg['cost']}g)")
        else:
            term.print(f"\n  🦶 {from_name} → {to_name}: "
                       f"{seg['effective_time']} min overland "
                       f"({seg['raw_time']} min base)")

        # ── Deduct ferry cost ─────────────────────────────────────────────
        if seg["type"] == "sea" and seg["cost"] > 0:
            player["gold"] = player.get("gold", 0) - seg["cost"]

        # ── Travel events ─────────────────────────────────────────────────
        outcome = run_travel_events(
            player,
            seg["effective_time"],
            travel_type=seg["type"],
            region=seg["biome"],
            combat_override=combat_override,
        )

        if outcome == "dead":
            term.print(f"\n  You have perished en route to {to_name}. "
                       "Your journey ends here...")
            player["current_hp"] = 0
            term.pause()
            return "dead"

        # ── Advance time ──────────────────────────────────────────────────
        advance_time(player, seg["effective_time"])

        # ── Stopover narration ────────────────────────────────────────────
        if not is_final:
            term.print(f"\n  You pause briefly in {to_name} before continuing "
                       "your journey...")
        else:
            # Final arrival
            player["location"] = seg["to"]
            term.print(f"\n{'─' * 52}")
            term.print(f"  You arrive in {to_name}.")
            term.print(f"  HP: {player.get('current_hp', '?')}/{player_max_hp(player)}"
                       f"  |  Gold: {player.get('gold', 0)}")
            term.pause("  Press Continue to enter the city...")

    return None
