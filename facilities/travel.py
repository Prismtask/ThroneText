# facilities/travel.py

import karma
from resources.cities import CITIES
from character import player_max_hp
from gui.terminal import term


def _set_wild_entry(player, dungeon):
    """Set the wild-dungeon entry fields on arrival.

    Points origin_city at the ruin's nearest city so every existing exit
    path (flee / death / timeout) routes the player there.
    """
    from wild_dungeons import ensure_wild_dungeon_state
    ensure_wild_dungeon_state(player)
    player["wild_dungeon_id"] = dungeon["id"]
    player["origin_city"] = dungeon.get("nearest_city", "solmere")
    player["dungeon_region"] = dungeon.get("biome", "temperate")
    player["location"] = "dungeon"


def embark_multi_leg_journey(player, segments, combat_override=None,
                             wild_dungeon=None):
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
        wild_dungeon: Optional wild dungeon dict. When provided, the final
            segment may target "wild:<id>"; on arrival the wild-dungeon
            entry fields are set instead of a city location.

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
        to_name = CITIES.get(seg["to"], {}).get("name")
        if to_name is None:
            if wild_dungeon is not None and str(seg["to"]).startswith("wild:"):
                to_name = wild_dungeon.get("name", seg["to"])
            else:
                to_name = seg["to"]

        # ── Leg narration (block-priced — §8) ────────────────────────────
        import time_blocks
        seg_blocks = time_blocks.travel_blocks(player, seg["effective_time"])
        blocks_label = f"{seg_blocks} block{'s' if seg_blocks != 1 else ''}"
        if seg["type"] == "sea":
            ship_id = player.get("ship_id")
            ship_name = None
            if ship_id:
                from resources.ships import get_ship
                ship = get_ship(ship_id)
                ship_name = ship["name"] if ship else None
            if ship_name:
                term.print(f"\n  ⛵ {from_name} → {to_name}: ≈{blocks_label} "
                           f"at sea aboard your {ship_name} (ship bonus applied)")
            else:
                term.print(f"\n  ⛵ {from_name} → {to_name}: ≈{blocks_label} "
                           f"ferry crossing (ticket: {seg['cost']}g)")
        else:
            term.print(f"\n  🦶 {from_name} → {to_name}: ≈{blocks_label} overland")

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

        # ── Time: the leg's cost in blocks (§8); boundary offers camp ────
        camp = False
        if (time_blocks.can_camp(player)
                and seg_blocks >= time_blocks.blocks_remaining(player)):
            camp = bool(term.confirm(
                "Night falls on the road — make camp for the night?"))
        time_blocks.spend_travel_segment(player, seg_blocks, camp=camp)
        if camp:
            from dreams import maybe_offer_dream
            maybe_offer_dream(player, "camp", term)

        # ── Stopover narration ────────────────────────────────────────────
        if not is_final:
            term.print(f"\n  You pause briefly in {to_name} before continuing "
                       "your journey...")
        else:
            # Final arrival
            if wild_dungeon is not None:
                _set_wild_entry(player, wild_dungeon)
                term.print(f"\n  You reach {wild_dungeon.get('name', 'the ruins')} "
                           f"(Lv {wild_dungeon.get('level', '?')}).")
                term.pause("  Press Continue to descend...")
                continue

            player["location"] = seg["to"]
            karma.mark_city_arrival(player)

            # Quests: arrival (visit_city objectives)
            from quests import update_quests
            for msg in update_quests(player, "visit_city", seg["to"]):
                term.print(msg)

            term.print(f"\n{'─' * 52}")
            term.print(f"  You arrive in {to_name}.")
            term.print(f"  HP: {player.get('current_hp', '?')}/{player_max_hp(player)}"
                       f"  |  Gold: {player.get('gold', 0)}")
            term.pause("  Press Continue to enter the city...")

    return None
