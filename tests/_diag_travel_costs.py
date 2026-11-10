"""Diagnostic: travel block costs under the new design (docs/time_system_design.md §8).

Computes from `resources/cities.py`:
  1. Every direct route: raw minutes → block cost (§4 table).
  2. Journey cost = SUM of per-segment block costs (segments spend
     individually as they complete).
  3. A full A→B block-cost matrix (shortest-time path).
  4. Modifier sensitivity: which routes change block cost under the
     Caravan (-45%) / light weather (+1 block) / heavy weather (+2).

Run from repo root with:
    .venv\\Scripts\\python.exe tests\\_diag_travel_costs.py
"""
import sys
from collections import deque
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:  # piped consoles on Windows may default to a legacy codepage (cp932)
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass

import time_blocks as tb
from resources.cities import CITIES


def cname(cid):
    return CITIES.get(cid, {}).get("name", cid)


def graph():
    """Undirected adjacency {city: [(neighbor, minutes, type)]}."""
    g = {cid: [] for cid in CITIES}
    for cid, city in CITIES.items():
        for conn in city.get("travel", {}).get("connections", []):
            dest = conn["dest"]
            g.setdefault(cid, []).append((dest, conn["travel_time"], conn["type"]))
            g.setdefault(dest, []).append((cid, conn["travel_time"], conn["type"]))
    return g


def shortest_path(g, origin, dest):
    """Min-total-minutes path (mirrors pathfinding's BFS objective)."""
    if origin == dest:
        return []
    best = {origin: (0, [])}
    q = deque([(origin, 0, [])])
    best_time = None
    best_path = None
    while q:
        node, time_so_far, path = q.popleft()
        for nxt, minutes, typ in g.get(node, []):
            t = time_so_far + minutes
            if nxt in best and best[nxt][0] <= t:
                continue
            best[nxt] = (t, path + [(node, nxt, minutes, typ)])
            if nxt == dest and (best_time is None or t < best_time):
                best_time, best_path = t, path + [(node, nxt, minutes, typ)]
            q.append((nxt, t, path + [(node, nxt, minutes, typ)]))
    return best_path


def main():
    g = graph()
    cities = sorted([c for c in CITIES if CITIES[c].get("travel", {}).get("connections") or any(c in [n for n, _m, _t in g.get(o, [])] for o in g)], key=cname)

    # ── 1. Direct routes (deduped, keep the fastest direction) ──────────
    seen = {}
    for cid in cities:
        for dest, minutes, typ in g.get(cid, []):
            a, b = sorted((cid, dest))
            if (a, b) not in seen or minutes < seen[(a, b)][2]:
                seen[(a, b)] = (a, b, minutes, typ)

    print("=" * 96)
    print("  DIRECT ROUTES — travel blocks: ceil(min/30) + 2 supply · T2 mount -1 · T4 mount -2 · rain +1 · heavy +2")
    print("=" * 96)
    for (a, b, minutes, typ) in sorted(seen.values(), key=lambda x: (cname(x[0]), cname(x[1]))):
        base = tb.travel_blocks_for(minutes)
        t2 = tb.travel_blocks_for(minutes, mount_tier=2)
        t4 = tb.travel_blocks_for(minutes, mount_tier=4)
        rain = tb.travel_blocks_for(minutes, rain=1)
        heavy = tb.travel_blocks_for(minutes, rain=2)
        print(f"  {cname(a):>12} ↔ {cname(b):<12} {minutes:>4} min  {typ:<4} "
              f"base {base} | T2 {t2} | T4 {t4} | rain {rain} | heavy {heavy}")

    # ── 2. Full matrix (shortest-time path, sum of per-segment costs) ───
    codes = {c: "".join(w[0] for w in cname(c).split())[:3].upper() for c in cities}
    print()
    print("=" * 76)
    print("  A→B JOURNEY COST IN BLOCKS (shortest-time path; * = multi-segment)")
    print("  Columns:", " ".join(f"{codes[c]:>3}" for c in cities))
    print("=" * 76)
    for a in cities:
        row = []
        for b in cities:
            if a == b:
                row.append("  -")
                continue
            segs = shortest_path(g, a, b)
            cost = sum(tb.travel_blocks_for(m) for _f, _t, m, _ty in segs)
            star = "*" if len(segs) > 1 else " "
            row.append(f"{cost:>2}{star}")
        print(f"  {codes[a]:>3} {cname(a):<12}", " ".join(row))

    # ── 3. Sample long journeys, segment by segment ─────────────────────
    print()
    print("=" * 76)
    print("  WORKED EXAMPLES (per-segment spend)")
    print("=" * 76)
    for a, b in [("solmere", "stormhold"), ("solmere", "coralhaven"),
                 ("stormhold", "isle_of_glass"), ("skylume", "blackwake")]:
        if a not in CITIES or b not in CITIES:
            continue
        segs = shortest_path(g, a, b)
        parts = " + ".join(f"{cname(f)}→{cname(t)} {m}min({tb.travel_blocks_for(m)}b)"
                           for f, t, m, _ty in segs)
        total = sum(tb.travel_blocks_for(m) for _f, _t, m, _ty in segs)
        total_t4 = sum(tb.travel_blocks_for(m, mount_tier=4) for _f, _t, m, _ty in segs)
        total_h4 = sum(tb.travel_blocks_for(m, mount_tier=4, rain=2)
                       for _f, _t, m, _ty in segs)
        print(f"  {cname(a)} → {cname(b)}: {parts}")
        print(f"      = {total} blocks base · {total_t4} Caravan · {total_h4} Caravan + heavy rain")

    # ── 4. Rules recap + distribution ──────────────────────────────────
    print()
    print("=" * 96)
    print("  RULES: 1 block per started 30 min + 2 supply overhead (rev 3.2) · mount shave tier//2 (T2/T3 -1, T4 -2)")
    print("         rain +1 · heavy rain +2 · tier 3+ mounts: rain +0, heavy rain +1")
    print("=" * 96)
    counts, t4_counts, heavy_counts = {}, {}, {}
    for (_a, _b, minutes, _typ) in seen.values():
        for store, kw in ((counts, {}), (t4_counts, {"mount_tier": 4}),
                          (heavy_counts, {"rain": 2})):
            bb = tb.travel_blocks_for(minutes, **kw)
            store[bb] = store.get(bb, 0) + 1
    print("  Direct-route distribution: base", {f"{k}b": v for k, v in sorted(counts.items())},
          "· Caravan", {f"{k}b": v for k, v in sorted(t4_counts.items())},
          "· heavy rain", {f"{k}b": v for k, v in sorted(heavy_counts.items())})


if __name__ == "__main__":
    main()
