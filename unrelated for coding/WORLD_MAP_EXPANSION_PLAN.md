# World Map Expansion Plan

## Goal

Replace the current single-hop travel system with a full world map where players can select **any city directly**, with travel time accumulating across the shortest path. Show facility previews before confirming the journey.

---

## Current State

### Data Layer ✅ (No Changes Needed)

`resources/cities.py` already contains a complete graph:

- **19 cities** with `biome`, `description`, `services[]`, `dialogues`
- **~40 bidirectional connections** with `dest`, `type` (land/sea), `travel_time`
- **7 regions**: North, Central, East, South, Far Reaches & Islands

### Current Travel Flow

```
CityScreen → [T] Travel → TravelScreen → shows ADJACENT land routes only
                                              ↓
                                         embark_journey() → TravelEvents → arrival

CityScreen → Port facility → port_service() → shows ADJACENT sea routes only
```

**The gap:** Player can only travel 1 hop at a time. Sea and land travel are separate UI flows.

---

## Architecture Changes

### New Files

| File | Purpose |
|---|---|
| `facilities/pathfinding.py` | BFS shortest-path over the city graph |
| `gui/screens/world_map_screen.py` | Canvas-based interactive world map |

### Modified Files

| File | Change |
|---|---|
| `facilities/travel.py` | Add `embark_multi_leg_journey()` for chained segments |
| `gui/screens/city_screen.py` | Add `[M] World Map` action button |

---

## Phase A — Pathfinding Engine

`facilities/pathfinding.py`

### Algorithm

Simple **BFS** over an undirected graph (19 nodes, ~40 edges — Dijkstra is overkill):

```python
def find_shortest_path(player, origin_id: str, dest_id: str) -> dict:
    """
    Returns:
        {
            "path": ["solmere", "sunreach", "brinewatch", ...],
            "total_time": 490,
            "segments": [
                {"from": "solmere", "to": "sunreach", "type": "land",
                 "raw_time": 140, "effective_time": 112, "biome": "temperate"},
                {"from": "brinewatch", "to": "tidebreak", "type": "sea",
                 "raw_time": 110, "effective_time": 77, "cost": 100},
                ...
            ],
            "total_cost": 200,
            "ferry_segments": 2,
        }
    """
```

### Rules

| Rule | Detail |
|---|---|
| **Graph traversal** | All connections are bidirectional — traverse the graph undirected |
| **Land time reduction** | Apply mount `time_reduction` (e.g. 20% for horse) to land segments |
| **Sea time reduction** | Apply 30% reduction if `player.has_ship == True` |
| **Sea cost** | 100g per sea segment if player has no ship; 0g if they own one |
| **Biome tracking** | Use origin city's biome for each segment's travel events |

---

## Phase B — Multi-Leg Journey

`facilities/travel.py` — new function `embark_multi_leg_journey()`

### Flow

```
For each segment in path:
    1. Print leg narration (City A → City B, distance, type)
    2. If sea segment & no ship → deduct 100g ferry cost
    3. run_travel_events(player, effective_time, travel_type, biome, combat_override)
    4. If outcome == "dead" → return "dead" (player died mid-journey)
    5. advance_time(player, effective_time)
    6. Brief stopover narration (optional, skip on final leg)

On completion:
    player["location"] = dest_id
    return None
```

### Combat Override

Must support the GUI `combat_override` callback (same pattern as current `embark_journey`) so travel combat uses `CombatScreen` overlay rather than terminal I/O.

---

## Phase C — WorldMapScreen (Canvas)

`gui/screens/world_map_screen.py`

### Layout

```
┌─────────────────────────────────────────────┐
│  Top Bar: "World Map — Current: Solmere"    │
├─────────────────────────────────────────────┤
│                                             │
│   ┌─ North ─────────────────────┐           │
│   │  Stormhold ── Thornwall     │  Legend   │
│   └─────────────────────────────┘           │
│                                             │
│   ┌─ Central ───────────────────┐           │
│   │  Greyharbor ── Solmere ★    │           │
│   │              ── Elderfen     │           │
│   └─────────────────────────────┘           │
│                                             │
│   ┌─ East ──────────────────────┐           │
│   │  Irondeep ── Skylume        │           │
│   │          ── Cinderpeak      │           │
│   │          ── Veilholt        │           │
│   └─────────────────────────────┘           │
│                                             │
│   ┌─ South / Far Reaches ───────┐           │
│   │  Sunreach ── Brinewatch ⚓   │           │
│   │  Ashkara ── Dunemar         │           │
│   │  ⛵ Tidebreak ⚓ ── ⛵ Coralhaven ⚓      │
│   │  Blackwake ── ⛵ Isle of Glass          │
│   └─────────────────────────────┘           │
│                                             │
├─────────────────────────────────────────────┤
│  Bottom: [Cancel]         [Show Legend]     │
└─────────────────────────────────────────────┘
```

### Canvas Elements

| Element | Rendering |
|---|---|
| **Region backgrounds** | Rounded rectangles with subtle border, region label in corner |
| **City nodes** | Rounded rectangles colored by biome, city name + biome label inside |
| **Current city** | Bold border + ★ star indicator |
| **Land routes** | Solid lines (`stroke-width: 1.2`) |
| **Sea routes** | Dashed lines (`dash=(5,4)`) |
| **Port cities** | ⚓ anchor icon next to name |
| **Selected destination** | Highlighted border (accent color, thicker stroke) |
| **Path highlight** | Gold/thick line along the computed shortest path |

### Interactions

1. **Hover over city** → cursor change, subtle brightness boost
2. **Click city** → compute shortest path → highlight route → show info panel
3. **Click same city again** or **press Escape** → deselect
4. **Click Cancel** or **Escape with nothing selected** → return to `CityScreen`

---

## Phase D — Route Highlighting

After pathfinding returns the path, draw each segment on the canvas:

- Solid gold line for land segments
- Dashed gold line for sea segments
- Small arrow markers showing direction along each edge
- Segment time labels along each edge (e.g. "140m")

---

## Phase E — Destination Info Panel

When a destination city is selected, show a side panel (or overlay card):

```
┌────────────────────────────────┐
│  CORALHAVEN       tropical     │
│                                │
│  "A jewel of the southern      │
│   seas built across a reef     │
│   archipelago..."              │
│                                │
│  ═══ ROUTE ═══════════════     │
│  Solmere                        │
│    └─🦶 140m → Sunreach         │
│                └─🦶 120m →      │
│                   Brinewatch    │
│                   └─⛵ 77m →    │
│                      Tidebreak  │
│                      └─⛵ 56m → │
│                         Coralhaven
│                                │
│  Total: 393 min                │
│  Ferry cost: 200g              │
│  Encounters: ~4 land, 2 sea    │
│                                │
│  ═══ FACILITIES ═══════════    │
│  🛒 Shop   🛏️ Inn   ⚓ Port     │
│  🌿 Herbalist  🏛️ Temple       │
│  🏰 Guild  🎁 Gift Shop        │
│                                │
│  [Confirm Journey]  [Cancel]   │
└────────────────────────────────┘
```

### Facility Icon Mapping

| Service | Icon | CSS Class (from HTML) |
|---|---|---|
| shop | 🛒 | `fac-shop` |
| inn | 🛏️ | `fac-inn` |
| blacksmith | 🔨 | `fac-blacksmith` |
| trade_hall | 🏪 | `fac-trade_hall` |
| temple | 🏛️ | `fac-temple` |
| port | ⚓ | `fac-port` |
| shipyard | 🚢 | `fac-shipyard` |
| herbalist | 🌿 | `fac-herbalist` |
| barracks | 🛡️ | `fac-barracks` |
| black_market | 👁️ | `fac-black_market` |
| arcane_tower | 🪄 | `fac-arcane_tower` |
| gift_shop | 🎁 | `fac-gift_shop` |
| guild | 👥 | `fac-guild` |

---

## Phase F — CityScreen Integration

`gui/screens/city_screen.py`

Add a new `[M] World Map` action alongside the existing `[T] Travel` button:

```python
# Keep [T] Travel for quick adjacent travel
# Add [M] World Map for full map with any-city selection

("[M] World Map", self._open_world_map),
```

Keyboard shortcut: press `M` in the city to open the world map.

The existing `TravelScreen` is preserved as a lighter-weight alternative for adjacent hops.

---

## Complexity Estimate

| Component | Lines | Effort |
|---|---|---|
| `pathfinding.py` | ~60-80 | Low |
| `travel.py` (multi-leg) | ~80-120 | Medium |
| `world_map_screen.py` | ~400-600 | High |
| `city_screen.py` (integration) | ~20-30 | Low |
| **Total** | **~560-830** | ~3-5 sessions |

---

## Risk Assessment

| Risk | Mitigation |
|---|---|
| Pathfinding infinite loops | Standard BFS with `visited` set — trivial to get right |
| Canvas click coordinates off | Use `canvas.find_closest()` or hit-testing on city node rects |
| Multi-leg journey too long (death likely) | Show encounter estimate in info panel; player can abort |
| Sea segments without ship too expensive | Show cost breakdown before confirming |
| Screen manager back-stack depth | `WorldMapScreen` navigates back to `CityScreen` after journey or cancel |
| Mount bonuses applying to sea | Only apply mount reduction to `type == "land"` segments |

---

## Future Enhancements (Out of Scope for Now)

- **Fast travel waypoints** — unlockable teleport shrines between major cities
- **Danger heatmap overlay** — color routes by encounter difficulty
- **Unlockable/secret cities** — initially hidden nodes that appear after story events
- **Travel animations** — dotted line animating along the path in real-time
- **Tooltip on hover** — quick city summary without clicking
