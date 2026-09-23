"""
facilities/pathfinding.py — BFS shortest-path engine for the world map.

Finds the shortest route (by travel_time) between any two cities in the graph
defined by resources/cities.py.  Supports mount time-reduction on land segments
and ship speed bonus on sea segments.

Public API:
    find_shortest_path(player, origin_id, dest_id) -> dict | None
"""

from collections import deque

from resources.cities import CITIES


def _get_connections(city_id):
    """Return all bidirectional connections for a city."""
    city = CITIES.get(city_id)
    if not city:
        return []
    return city.get("travel", {}).get("connections", [])


def find_shortest_path(player, origin_id, dest_id):
    """
    BFS shortest-path over the undirected city graph.

    Parameters
    ----------
    player    : player state dict.
    origin_id : starting city key (e.g. "solmere").
    dest_id   : destination city key (e.g. "coralhaven").

    Returns
    -------
    dict with keys:
        "path"           : list of city IDs from origin to destination (inclusive).
        "total_time"     : int — effective travel time after all reductions.
        "total_cost"     : int — ferry costs (gold).
        "ferry_segments" : int — number of sea segments.
        "segments"       : list of dicts, each with:
            "from"            : origin city key of this segment.
            "to"              : destination city key of this segment.
            "type"            : "land" or "sea".
            "raw_time"        : base travel time from graph data.
            "effective_time"  : travel time after mount/ship reductions.
            "biome"           : biome of the origin city (for encounter theming).
            "cost"            : gold cost for this segment (sea without ship).
    or None if no path exists.
    """
    if origin_id not in CITIES or dest_id not in CITIES:
        return None
    if origin_id == dest_id:
        return {
            "path": [origin_id],
            "total_time": 0,
            "total_cost": 0,
            "ferry_segments": 0,
            "segments": [],
        }

    # ── Pre-compute reductions ────────────────────────────────────────────
    has_ship = bool(player.get("has_ship", False))
    mount_reduction = 0.0
    mount_id = player.get("mount_id")
    if mount_id:
        from resources.mounts import get_mount
        mount = get_mount(mount_id)
        if mount:
            mount_reduction = mount.get("time_reduction", 0)

    # Daily events: Heavy Rain makes travel take longer
    daily_time_mult = player.get("daily_effects", {}).get("travel_time_mult", 1.0)

    # ── BFS ───────────────────────────────────────────────────────────────
    # We store (current_node, path_list, total_time, total_cost, ferry_count,
    #          segments_list) in the queue.
    # BFS on an unweighted graph is fine here — weight differences between
    # edges are small and the graph is tiny (19 nodes, ~40 edges).

    queue = deque()
    queue.append((origin_id, [origin_id], 0, 0, 0, []))

    # visited[node] = best time to reach that node so far
    # (since edges have different costs, we may find a cheaper path later)
    visited = {origin_id: 0}

    best_path = None
    best_time = float("inf")

    while queue:
        current, path, total_time, total_cost, ferry_count, segments = queue.popleft()

        if current == dest_id:
            if total_time < best_time:
                best_time = total_time
                best_path = {
                    "path": path,
                    "total_time": total_time,
                    "total_cost": total_cost,
                    "ferry_segments": ferry_count,
                    "segments": segments,
                }
            continue

        for conn in _get_connections(current):
            neighbor = conn["dest"]
            if neighbor in path:  # prevent cycles
                continue

            seg_type = conn.get("type", "land")
            raw_time = conn.get("travel_time", 100)

            # Calculate effective time for this segment
            if seg_type == "sea":
                effective_time = int(raw_time * 0.7) if has_ship else raw_time
                seg_cost = 0 if has_ship else 100
            else:
                effective_time = int(raw_time * (1 - mount_reduction))
                seg_cost = 0
            if daily_time_mult != 1.0:
                effective_time = int(effective_time * daily_time_mult)

            new_time = total_time + effective_time
            new_cost = total_cost + seg_cost
            new_ferry = ferry_count + (1 if seg_type == "sea" else 0)

            # Prune: if we've reached this node before with a better time, skip
            if neighbor in visited and visited[neighbor] <= new_time:
                continue
            visited[neighbor] = new_time

            origin_biome = CITIES.get(current, {}).get("biome", "temperate")

            new_segments = segments + [{
                "from": current,
                "to": neighbor,
                "type": seg_type,
                "raw_time": raw_time,
                "effective_time": effective_time,
                "biome": origin_biome,
                "cost": seg_cost,
            }]

            queue.append((neighbor, path + [neighbor], new_time, new_cost,
                         new_ferry, new_segments))

    return best_path
