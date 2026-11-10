# Biome-Shared Dungeon Depth — Design

**Status:** Implemented 2026-11-04 (Phase 1).
**Decision:** Same-biome city dungeons share one unlocked depth; each city
remains a separate entrance with its own floor cursor.

---

## 1. Problem

Every city had an independent `city_floors[city_id]` ladder. Dungeon content is
already biome-keyed — enemy pools (`BIOME_RACES`), loot and flower weights
(`dungeon_biome()`), and the biome craft hint all use the city's biome — so
same-biome cities were mechanically identical ladders differing only by label.

Duplicated ladders: temperate ×3 (Thornwall/Solmere/Greyharbor), coastal ×3
(Brinewatch/Saltmarsh/Tidebreak), swamp ×2 (Elderfen/Mirefall), desert ×2
(Ashkara/Dunemar). 19 city dungeons → 13 biome dungeons (Wonderland separate).

## 2. Model (locked)

`city_floors[city_id] = {"floor": N, "max_floor": M}` is retained.

- **`max_floor` is shared per biome.** Every existing record whose city has the
  same `CITIES[city_id]["biome"]` is raised to the group maximum.
- **`floor` stays city-local.** It is the entrance cursor used by floor
  selection and resume; it is never copied between cities.
- Unvisited cities have no record, so they are not mistaken for "visited" by
  other systems. On first entry, `_ensure_city_floors()` creates the record at
  `floor = 1` and seeds `max_floor` from the biome's existing depth.
- `player["max_floor"]` (legacy global) stays monotonic: max of every record.
- Unknown city ids never join the temperate group; they sync alone.

## 3. Implementation

| Location | Change |
|---|---|
| `leveling.py` | `cities_in_biome`, `get_shared_biome_max_floor`, `sync_biome_dungeon_depth` |
| `dungeon.py` | `_ensure_city_floors` seeds shared depth; `_advance_city_floor` writes cursor + shared depth; all 5 floor-advance sites use it |
| `character.ensure_player_fields()` | calls `sync_biome_dungeon_depth()` on load (old-save migration) |
| `events.py` / `facilities/arcane_tower.py` / `facilities/black_market.py` | Wonderland gate counts **unique biomes** at Floor 20+ (was city records) |
| `titles.py` | `_floors_cleared` sums each biome once |

## 4. Deliberate consequences

- Entering a second city of a cleared biome exposes the shared depth
  immediately; it does not replay Floors 1–N.
- Floor selection/cursors remain per entrance, so a run resumed from a different
  city starts from that city's cursor.
- Wonderland unlock remains **2 different biomes** at Floor 20+ (same semantic
  as before, now enforced explicitly).
- Pandemonium unlock was already biome-based (`is_pandemonium_unlocked`) and is
  unchanged.
- Arcane teleport's `max_floor > 1` heuristic is unchanged: it only looks at
  records that exist, i.e. cities whose dungeon was actually entered.

## 5. Verification

- `tests/test_biome_dungeon_depth.py` (14 tests): grouping, sync/migration,
  entrance seeding, cursor isolation, title/leveling/gate counting.
- `tests/_diag_biome_depth.py`: read-only real-save smoke test; asserts no depth
  is lowered, cursors are untouched, same-biome groups share one depth.
- Full suite: `pytest tests/ --ignore=tests/test_phase0.py
  --ignore=tests/test_phase1.py`.
