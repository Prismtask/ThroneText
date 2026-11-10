# Wild Dungeons — Design & Implementation Plan

Status: **COMPLETE — Phases 1–5 done and fully playtest-verified 2026-10-13.**
Locked decisions below.

**Playtest verification (user, live play):**
- 2026-10-07: despawn/expiry, reward granting, death flow.
- 2026-10-13: flee→nearest-city return, retry-after-flee, save-and-quit
  mid-run resume, weekly spawn cadence over multiple cycles, and level-band
  feel across the 1–80 range.

Journal coverage: weekly spawns record a "Strange Ruins Surfaced" event;
each conquest records a "Conquered: <name>" [WILD] entry with level, floor
count, and spoils (the Journal renders the date from the entry's day field).
Direct append (no dedupe) so two conquests on one day both appear.
Changelog entry lives under v0.1.8.0 "The Distant Journey" → section
"Wild Dungeons" (gui/screens/changelog_screen.py).

Scope: One-time wild dungeons that surface on the world map, travelable under
existing travel rules, playable through the existing dungeon UI, with a
previewable reward pool.

**Phase 1 (done):** `wild_dungeons.py` runtime, `resources/world_layout.py`,
`resources/wild_dungeon_themes.py`, `events.process_day_rollover` hook,
`character.build_character` state init, `tests/test_wild_dungeons.py` (18 tests).

**Phase 2 (done):** world map markers (`☠ Lv N`, purple), click selection +
hit-testing, info panel with details + rarity-colored reward pool preview,
spawn/expiry refresh on map open, legend/placeholder updates.

**Phase 3 (done):** off-road segment + journey builder (`wild_dungeons.py`),
wild support in `embark_multi_leg_journey` + `embark_wild_dungeon_journey`
(terminal), "Travel to Dungeon" button, animated off-road leg with `wild:`
endpoint resolution, arrival → entry fields (`wild_dungeon_id`, `origin_city`
= nearest, `dungeon_region`, `location="dungeon"`) → DungeonScreen, expiry
grace mid-journey → nearest city, wild run results routed (fled→city,
dead→DeathScreen dungeon type).

**Phase 4 (done):** real `_explore_wild_dungeon` loop in `dungeon.py`
(dungeon-level floors, shared room handlers, wild-scoped resume keys
`saved_wild_*`, no superboss/wonderland/pandemonium, mid-run crumble guard);
victory grants the previewed pool + gold (`lv×floors×25`) + XP (`lv×floors×40`),
records completion, stores `player["_wild_completion"]` summary, exits to
nearest city as `"wild_complete"`; flee keeps the ruin retryable (attempted
flag); death returns `"dead"` with run state cleaned; `complete_wild_dungeon`
idempotent (post-expiry completions recorded). **Progress integrity:** wild
runs never touch `player["max_floor"]` or `city_floors` (all of the game's
`max_floor` writers live in the city-path floor-clear/superboss blocks that
run after the wild branch returns); the transient `player["floor"]` cursor is
snapshotted to `_wild_prev_floor` at entry and restored on every exit (flee /
death / interrupt / crumble / save-exit / victory) so the ruin's level never
pollutes later travel scaling. DungeonScreen wild branding
(name/floor/top-bar tick). `_on_wild_result` handles
wild_complete (reward dialog) / save_exit (menu) / fled-timeout-None
(defensive scrub for button-flees). `city_screen._launch_dungeon` and
`apply_death_penalty` defensively wipe wild state so it can never hijack
city runs.
Smoke tests: `tests/_diag_wild_map.py` (11 scenarios) and
`tests/_diag_wild_run.py` (5 scenarios — victory/flee/death/crumble/missing),
both manual, UTF-8 safe when piped.

---

## 0. Decision log (locked 2026-10-02)

1. **Spawn model:** auto-spawn on the **world map on a weekly roll** (checked on
   day rollover when `player["day"] % 7 == 0`). Each cycle spawns a random
   **3–7 dungeons** (`random.randint(3, 7)`, never fewer than 3, never more
   than 7). Markers are always visible — no hidden discovery mechanic.
2. **Level:** dungeon level ranges from `max_floor − 8` to `max_floor + up`,
   **clamped 1–80**, where the upward offset `up` scales with progress:
   `up = min(8, 2 + max_floor // 3)`. Full ±8 at depth (+8 reached at floor
   18), but low floors are protected — a floor-1 player faces at most level-3
   ruins (matching the game's core convention of floor+3 caps). Never truly
   random — always fair-to-challenging relative to the player. Fixed
   2026-10-02: the original flat ±8 unfairly burdened early players (spotted
   via savefile-1 bias during playtest of a late-game character).
3. **Floors:** 2–6 floors (rolled at spawn). Final floor is a boss floor.
4. **Retry:** fleeing does **not** consume the dungeon. It stays on the map
   until its **expiry day** (spawn day + 3–5 days). Expired dungeons despawn.
5. **Flee outcome:** player is returned to the **nearest city** to the dungeon.
6. **Death outcome:** identical to all other deaths (`apply_death_penalty`).
7. **Success outcome:** grants the **previewed reward pool** + gold/XP scaled
   to dungeon level. The pool is generated **at spawn time** and visible in
   the map info panel before traveling.
8. **One-time:** a cleared dungeon is removed forever (recorded in a
   `completed` list for stats/flavor only).

---

## 1. Data model

### 1.1 State block — `player["wild_dungeons"]`

```python
{
    "active":    [],      # [dungeon dict, ...] — spawned, not yet cleared/expired
    "completed": [],      # [dungeon_id, ...] — permanent record
    "next_id":   1,       # monotonically increasing dungeon id counter
    "last_spawn_day": 0,  # throttle for the weekly roll
}
```

Managed exclusively by `wild_dungeons.ensure_wild_dungeon_state(player)`
(mirrors `quests.ensure_quest_state`). Called from `character.build_character`
and defensively at every access point, so old saves migrate with zero work —
the save system already round-trips arbitrary JSON-safe keys.

### 1.2 Dungeon dict (single element of `active`)

```python
{
    "id":        "wild_3",              # monotonically increasing counter
    "name":      "Forgotten Crypt",     # generated from theme tables
    "biome":     "swamp",               # from nearest city's biome
    "level":     18,                    # clamp(max_floor ± 8, 1, 80)
    "total_floors": 4,                  # 2–6
    "highest_floor_cleared": 0,         # progress across retries
    "position":  [320, 180],            # world-map canvas coords (ring around seed_city)
    "spawn_day":  21,
    "expire_day": 26,
    "seed_city": "mirefall",             # biome source + placement anchor
    "nearest_city": "elderfen",          # flee destination (derived from position)
    "attempted":  False,                # flavor only
    "reward_pool": [                    # PREVIEWABLE — generated at spawn
        {"item_id": "iron_sword", "rarity": "epic"},
        {"item_id": "greater_healing_potion", "rarity": "common"},
        ...
    ],
}
```

### 1.3 Reward pool generation (at spawn)

- Size: `total_floors + 2` entries.
- **Top item forced to rarity ≥ epic** at levels 25+, ≥ rare below — reusing
  `dungeon._roll_equipment_drop`'s level bands as the rarity weight source.
- Remaining entries: standard `roll_drop(level)`-style rolls (equipment w/
  rarity, consumables w/o).
- Only item IDs + rarities are stored — **stats are rolled on acquisition**
  via `build_item()`, so the preview shows names/rarities but not exact mods.

### 1.4 Name themes — `resources/wild_dungeon_themes.py`

Pure-data module (same pattern as `resources/quests.py`): per-biome adjective
+ ruin-type tables, e.g. `temperate → ("Forgotten", "Sunken", "Verdant") ×
("Crypt", "Hollow", "Barrens")`. No game imports.

---

## 2. Spawn system

- Hook: inside `events.process_day_rollover` (after the per-day loop), call
  `wild_dungeons.spawn_cycle(player)` when `player["day"] % 7 == 0` and
  `day - last_spawn_day >= 7`.
- `spawn_cycle(player)`:
  1. Expire anything past `expire_day` first (keeps the active list from
     growing unboundedly — old dungeons age out as new ones arrive).
  2. Roll `count = random.randint(3, 7)` — the cycle always spawns 3–7.
  3. For each of the `count` dungeons, pick a distinct random city seed;
     biome = that city's biome; position = random point on a **90–260 px ring
     around the seed city's node center** (clamped to canvas bounds), clear of
     every city node and of other dungeons spawned this cycle. The flee
     destination (`nearest_city`) is derived from the final position.
  4. Generate level (scaled band `min(8, 2 + base // 3)` up-side, −8 down,
     clamp 1–80), floors (2–6), reward pool, expiry (3–5 days).
  5. Journal entry + session log: "Strange ruins have surfaced across the
     land..." (reuses `events.record_event` — no toasts, matching quest
     convention).
- Idempotent: also called on world-map open, so a save loaded mid-week is
  immediately consistent (a cycle already rolled this week does not roll
  again).

---

## 3. World map integration — `gui/screens/world_map_screen.py`

1. **Prerequisite refactor:** move `_CITY_POSITIONS` (and `_REGIONS` bounds
   used for canvas limits) into a new `resources/world_layout.py`. This lets
   runtime code (spawner) place markers without importing tkinter/GUI modules.
2. `_draw_wild_dungeons()`: skull/cave glyph marker at `position`, distinct
   from city rectangles.
3. Click detection: extend `_on_canvas_click` with `_find_wild_at(ex, ey)`.
4. `_build_wild_info_panel(dungeon)` — right panel shows:
   - name, biome, **level**, **floors**, days until despawn
   - **reward pool preview**: item names colored by rarity
   - nearest city (where you'll wake up if you flee)
   - **"Travel to Dungeon"** button
5. `_on_travel_to_dungeon(dungeon)`:
   - Route = `find_shortest_path(cur_city, nearest_city)` + synthetic final
     segment `{from: nearest, to: dungeon.id, type: "land",
     raw_time: 60–90}`; apply mount reduction to the synthetic leg (mirrors
     `pathfinding` math).
   - Reuse the existing cargo/ferry checks; the final leg is land-only.
   - Existing segment interpolation already animates between arbitrary
     coordinates — the final leg's endpoint is `dungeon["position"]`.
6. `_on_arrival` wild variant: set `player["wild_dungeon_id"]`,
   `player["location"] = "dungeon"`, `player["origin_city"] = nearest_city`,
   then `switch_to(DungeonScreen)` instead of `CityScreen`.
7. Expiry guard: check `day <= expire_day` at Travel-button time and again on
   arrival (grace: if it expired mid-journey, drop into nearest city with a
   "the ruin has crumbled" message).

---

## 4. Dungeon integration — `dungeon.py`

### 4.1 Branch

At the top of `explore_dungeon`:

```python
if player.get("wild_dungeon_id"):
    return _explore_wild_dungeon(player, combat_override, superboss_override)
```

`_explore_wild_dungeon` is a **separate function** (~250 lines), not
conditionals threaded through the existing 1300-line loop. It reuses the
same room handlers (`handle_fountain_room`, `handle_merchant_room`,
`handle_trap_room`, `handle_stat_check_room`, combat via `combat_override`),
the same `generate_floor()`, and the same `_tprint/_tpause/_term` helpers.

### 4.2 Key trick — free flee/death routing

Before entry (done at travel arrival), set:

```python
player["origin_city"] = dungeon["nearest_city"]
```

Every existing exit path — flee, death, timeout — already sends the player to
`origin_city` (`apply_death_penalty`, `_cleanup_dungeon_exit`,
`_return_from_dungeon`). **No changes needed** to death/flee plumbing;
"nearest city on flee" falls out for free.

### 4.3 What `_explore_wild_dungeon` does differently

- Floor number = `dungeon["level"]` (passed to `generate_floor`), NOT
  `city_floors` progress.
- Region = `dungeon["biome"]`.
- **Skips:** superboss dispatch (20-floor), Wonderland dispatch/quirks/
  shadows, Pandemonium curses, level-cap milestone checks.
- Resume state uses **wild-scoped keys** (`saved_wild_floor`,
  `saved_wild_rooms`, `saved_wild_room_index`) so it never collides with city
  dungeon saves.
- Floor clear: `highest_floor_cleared += 1`; on the **final floor**, run the
  victory sequence (below) and return `"wild_complete"`.
- Flee: existing message + return `"fled"` (dungeon stays active; retryable).
- Death: return `"dead"` (normal penalty path).

### 4.4 Victory sequence

- Grant every `reward_pool` entry via `build_item` + `add_item_to_inventory`.
- Gold: `level × total_floors × ~25`; XP: `level × total_floors × ~40`
  (player + living allies), both through the daily-bonus multiplier for
  consistency with other rewards.
- Mark completed: move dungeon dict into `completed`, drop `active`,
  `player.pop("wild_dungeon_id")`.

### 4.5 DungeonScreen branding — `gui/screens/dungeon_screen.py`

~10-line change in `build_ui`: when `player.get("wild_dungeon_id")`, derive
name from the active dungeon dict and floor/max from
`highest_floor_cleared + 1` / `total_floors` instead of `city_floors`.

### 4.6 Return handling — `gui/screens/city_screen.py`

`_return_from_dungeon` gains one branch: `result == "wild_complete"` → custom
reward-summary dialog (bypasses `_show_post_floor_menu`, which reads
`city_floors`) → `CityScreen` at the nearest city.

---

## 5. Travel runtime — `facilities/travel.py`

- New `embark_wild_dungeon_journey(player, dungeon, combat_override)` for
  terminal mode: runs the city-route legs via existing helpers, then the
  off-road leg via `run_travel_events`, then sets the wild-dungeon entry
  fields.
- GUI mode bypasses this (WorldMapScreen animates travel itself, as today) —
  the function exists for terminal parity and as the shared logic home for
  the synthetic-segment construction.

---

## 6. Save migration & old saves

- `ensure_wild_dungeon_state` called from `character.build_character` and
  defensively inside `maybe_spawn` / world-map read paths.
- Old saves: first week roll after loading initializes the block. No version
  bump, no migration script (matches quest-state rollout).

---

## 7. Tests — `tests/test_wild_dungeons.py`

- Seeded spawn: level clamp (±8 of max_floor, 1–80), floors 2–6, and each
  cycle spawns exactly `randint(3, 7)` dungeons (never < 3, never > 7).
- Reward pool: size `floors + 2`, top rarity ≥ epic at level ≥ 25.
- Expiry: despawn past `expire_day`; retryable before; active list stays
  bounded by expiry since 3–7 enter and old ones age out each cycle.
- Flee → `player["location"] == nearest_city`, dungeon still active.
- Death → `apply_death_penalty` lands at nearest city (via origin trick).
- Victory → pool items in inventory, dungeon in `completed`, id flag cleared.
- Save/load roundtrip of the `wild_dungeons` block.
- `find_nearest_city` / position spacing from city nodes.

---

## 8. Implementation order (phases)

| Phase | Work | Files | Effort |
|---|---|---|---|
| 1 | Layout refactor (`resources/world_layout.py`), `wild_dungeons.py` runtime + themes, state migration, spawn/expiry, nearest-city, reward-pool gen | `resources/world_layout.py`, `resources/wild_dungeon_themes.py`, `wild_dungeons.py`, `character.py`, `events.py` | S–M |
| 2 | World map read-only: markers, info panel w/ reward preview | `gui/screens/world_map_screen.py` | M |
| 3 | Travel: synthetic off-road segment, animation, arrival → DungeonScreen | `world_map_screen.py`, `facilities/travel.py` | M |
| 4 | Dungeon loop: `_explore_wild_dungeon`, DungeonScreen branding, CityScreen `wild_complete` | `dungeon.py`, `gui/screens/dungeon_screen.py`, `gui/screens/city_screen.py` | M |
| 5 | Polish: expiry grace, journal/flavor, balance pass, tests | `tests/test_wild_dungeons.py`, docs | S |

**Total estimate: ~1,200–1,400 LOC across ~10 files, roughly 1 medium
work-session per phase.**

---

## 9. Risks

1. **`explore_dungeon` coupling** — mitigated by the branch-to-separate-
   function approach (4.1); the shared room handlers keep the fork thin.
2. **Canvas layout in GUI module** — fixed up-front in Phase 1 (shared
   `world_layout` module).
3. **Pathfinding is city-ID-based** — handled with a synthetic final segment;
   `embark_multi_leg_journey` needs a guard so a `wild:*` destination never
   hits the `CITIES` lookup / quest-arrival path (terminal mode only; GUI
   animates independently).
4. **Party-size scaling** in `generate_floor` reads ally state normally —
   wild runs pass the real player dict, so no special handling.
5. **Balance of the level band** — the upward side now scales in at low
   floors (`2 + base // 3`, cap +8) so early players aren't burdened; still
   tune the full-band depth (floor 18+), spawn count, and expiry window in
   the Phase 5 playtest. With 3–7 spawns per week, a low-level player should
   see mostly near-floor spawns — playtest the spread across 1–80.
