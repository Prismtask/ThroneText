# Celestia — Northern Celestial City

**Status:** Implemented 2026-11-04.
**Purpose:** Promote the previously stale `celestial` biome (only present in
`BIOME_RACES` + bestiary labels) into a real mid-game city and dungeon.

---

## 1. Placement & access

- City: **Celestia**, biome `celestial`, world-map position `(250, 30)` in the
  **North** region (above Solmere, beside Stormhold/Thornwall).
- Road connections: Stormhold (120 min) and Thornwall (90 min), bidirectional.
- **Visible from the start** — this is not an endgame lock like Pandemonium.
- Travel is blocked until the player carries the **Celestial Sigil**
  (`entry_item` on the city data). The world-map travel panel shows
  `Sealed — requires Celestial Sigil`; attempting travel shows a clear dialog.
- Sigil source: granted once when the player first reaches **Floor 30** of any
  city dungeon (`_grant_celestial_sigil`). Old saves with `max_floor >= 30`
  receive it on load via `ensure_player_fields()`.

## 2. Dungeon

- Entrance starts at **Floor 30** (`dungeon_start_floor: 30`), so the city is a
  mid-game destination rather than a replay of Floors 1–29.
- The floor-selection dialog starts its grid at the city's `dungeon_start_floor`.
- Standard city-dungeon loop; region is `celestial`, so `BIOME_RACES["celestial"]`
  (Angel/Fey/Construct/Dragonkin/Elemental/Clockwork) drives spawns.
- Counts as a unique biome for ascension, Wonderland's 2-biome gate (once its
  record reaches the relevant depth), and Pandemonium's 4-biome unlock.
- **Confirmed intended (2026-11-04):** entering the Celestial Stair seeds the
  celestial record at `max_floor = 30`, so it immediately counts as a biome at
  cap 30 — and at lower caps 10/20 — without clearing a Celestial floor first.
  It does **not** count at cap 40 or for Pandemonium's 4-biome-at-40 gate.

## 3. Identity & content

- Services: Shop, Inn, Temple, Gift Shop (all existing handlers).
- ASCII city map + clickable service positions added to `resources/city_maps.py`.
- Dialogue pool: `resources/dialogues/celestia.py` (receptionist, shop, inn,
  temple, gift shop); wired through `resources/cities.py` and `city_dialogue.py`.
- Loot identity: `FORM_WEIGHTS_BY_BIOME["celestial"]` favors staff/greatstaff/
  grimoire/crown/regalia/vestments/robes/monocle; `ELEMENT_WEIGHTS_BY_BIOME`
  favors light, then wind/magical/thunder.
- `WILD_DUNGEON_THEMES["celestial"]` added so wild ruins spawned near Celestia
  have a heavenly name pool.
- **Wild-dungeon integration:** Celestia is excluded from the weekly wild-ruin
  seed pool until the player owns the Celestial Sigil. Once accessible,
  celestial ruins can spawn near it (theme + loot weights apply). Any active
  ruin whose `seed_city` or `nearest_city` is still item-locked is hidden from
  the map and cannot be entered.

## 4. Implementation map

| File | Change |
|---|---|
| `resources/cities.py` | Celestia entry, `entry_item`, `dungeon_start_floor`, connections, dialogue imports |
| `resources/dialogues/celestia.py`, `resources/dialogues/__init__.py`, `city_dialogue.py` | dialogue pool + registry |
| `resources/world_layout.py` | `CITY_POSITIONS["celestia"]`, North region |
| `resources/city_maps.py` | ASCII map + service positions |
| `resources/items.py` | `celestial_sigil` key item |
| `resources/item_generation.py` | celestial form + element weights |
| `resources/wild_dungeon_themes.py` | celestial wild theme |
| `dungeon.py` | `_city_start_floor`, `_ensure_city_floors` Floor-30 seed, sigil grant |
| `character.py` | old-save sigil grant at `max_floor >= 30` |
| `gui/screens/city_screen.py` | floor grid honors `dungeon_start_floor` |
| `gui/screens/world_map_screen.py` | celestial biome color + `entry_item` gate/panel |

## 5. Verification

- `tests/test_celestia_city.py` (19 tests): city/map/connections, Floor-30
  seeding, sigil idempotence, threshold grant, ascension display, wild-dungeon
  gating, loot/theme tables.
- Full suite: `pytest tests/ --ignore=tests/test_phase0.py
  --ignore=tests/test_phase1.py`.
- `tests/_diag_biome_depth.py` still validates shared-depth migration.
