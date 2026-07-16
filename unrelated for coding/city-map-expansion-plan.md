# City Map Expansion Plan (Method B — Manual Grid Overlay)

## Overview
Replace the city screen's service button grid with clickable ASCII art maps.
Services are scattered on the map by position; the bottom action bar (Inventory,
Skill Book, Travel, Dungeon, Save) stays as-is.

**Files to create:** 1  
**Files to modify:** 3  
**Total touched:** 4

---

## Phase 1 — Coordinate Data (`resources/city_maps.py`)

Add a `CITY_SERVICE_POSITIONS` dict after the maps. Each entry maps a service key
to `(line_number, start_col, end_col)` within that city's ASCII map string.

Line numbers are **0-based** relative to the map string (line 0 = first line of art).
Col numbers are character offsets on that line.

```python
CITY_SERVICE_POSITIONS: dict[str, dict[str, tuple[int, int, int]]] = {
    "stormhold": {
        "shop":       (8, 42, 48),
        "inn":        (8, 29, 34),
        "barracks":   (4, 23, 33),
        "gift_shop":  (10, 12, 22),
        "dungeon":    (13, 9, 23),
    },
    "thornwall": {
        "shop":       (12, 44, 52),
        "inn":        (12, 32, 40),
        "barracks":   (6, 10, 25),
        "dungeon":    (16, 9, 23),
    },
    "solmere": {
        "shop":       (17, 59, 71),
        "inn":        (16, 25, 34),
        "blacksmith": (16, 42, 58),
        "trade_hall": (11, 56, 67),
        "temple":     (8, 29, 40),
        "guild":      (6, 16, 26),
        "dungeon":    (20, 9, 23),
    },
    # ... repeat for all 19 cities
}
```

### Subtask 1.1: Map each city's service positions
Each ASCII map needs its services and dungeon located. Count lines in each map
(leading newline from `r"""` is line 0, strip it mentally).

Cities and their services (from `resources/cities.py` CITIES dict):
| City | Services | Approx map lines |
|------|----------|-----------------|
| stormhold | shop, inn, barracks, gift_shop | 14 |
| thornwall | shop, inn, barracks | 17 |
| solmere | shop, inn, blacksmith, trade_hall, temple, guild | 21 |
| greyharbor | shop, inn, trade_hall, guild | 22 |
| elderfen | shop, inn, herbalist | 27 |
| irondeep | shop, inn, blacksmith, barracks, guild | 23 |
| skylume | shop, inn, arcane_tower, gift_shop | 26 |
| cinderpeak | shop, inn, blacksmith, arcane_tower | 22 |
| veilholt | shop, inn, herbalist, arcane_tower, guild | 21 |
| sunreach | shop, inn, temple, trade_hall | 22 |
| brinewatch | shop, inn, blacksmith, trade_hall, port, shipyard, guild | 27 |
| mirefall | shop, inn, herbalist, black_market | 21 |
| ashkara | shop, inn, blacksmith, black_market, guild | 22 |
| dunemar | shop, inn, trade_hall, black_market | 22 |
| saltmarsh | shop, inn, port | 18 |
| tidebreak | shop, inn, trade_hall, port, shipyard, guild | 22 |
| coralhaven | shop, inn, temple, herbalist, gift_shop, port, guild | 21 |
| blackwake | inn, port, black_market | 22 |
| isle_of_glass | port, arcane_tower | 18 |

~76 coordinate entries × ~1 line each = ~80 lines of data.

---

## Phase 2 — New Widget (`gui/widgets/city_map.py`) **[NEW FILE]**

A reusable `tk.Text`-based widget that renders the ASCII city map and makes
service/dungeon regions clickable using tag bindings.

### Class: `CityMapWidget(tk.Text)`

```python
class CityMapWidget(tk.Text):
    """Renders a city ASCII map with clickable service regions."""

    def __init__(self, parent, city_id, city, positions, 
                 on_service_click=None, on_dungeon_click=None, **kwargs):
        ...
```

### Key methods:
- `__init__`: Configure Text widget (monospace, read-only, dark bg, no border, 
  fixed height based on map line count)
- `_render_map()`: Insert the ASCII map string, apply base styling
- `_apply_service_tags()`: For each position entry, create a tag, configure it
  (accent color, underline on hover), bind `<Button-1>`, `<Enter>`, `<Leave>`
- `_apply_dungeon_tag()`: Same for the dungeon marker at bottom of map
- `refresh(city_id, city, positions)`: Re-render for a different city

### Tag styling:
- **Normal**: `fg=Theme.TEXT`
- **Hover**: `fg=Theme.ACCENT, underline=True, cursor="hand2"`
- **Click**: calls `on_service_click(service_key)` or `on_dungeon_click()`

### Dimensions:
- Map is ~80 chars wide → at 10px font = ~800px wide, fits in current layout
- Map is 12-27 lines tall → set `height=map_lines` and `state="disabled"`

---

## Phase 3 — City Screen Integration (`gui/screens/city_screen.py`)

### Changes to `build_ui()`:

**Remove** (lines ~89-140):
- The `services_frame` LabelFrame
- The `self.service_btns` button grid loop
- The `self._service_refs` list
- The house button grid placement

**Replace with:**
```python
# ── City Map (clickable ASCII art) ───────────────────────────────────
from resources.city_maps import get_city_map, CITY_SERVICE_POSITIONS
from gui.widgets.city_map import CityMapWidget

map_art = get_city_map(self.city_id)
positions = CITY_SERVICE_POSITIONS.get(self.city_id, {})

map_frame = tk.Frame(self.content, bg=Theme.BG_DARK,
                     highlightthickness=1, highlightbackground=Theme.BORDER)
map_frame.pack(fill=tk.BOTH, expand=True, pady=8)

self.city_map = CityMapWidget(
    map_frame,
    city_id=self.city_id,
    city=self.city,
    positions=positions,
    on_service_click=self._open_service,
    on_dungeon_click=self._enter_dungeon,
)
self.city_map.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
```

### Changes to `_on_city_key()`:
Number keys still work but now cycle through `list(positions.keys())` instead of
`self._service_refs`. Keep the letter key mappings unchanged.

### House support:
If the player owns a house, add a small house button **below** the map or as a
tag on the map text itself (search for "HOUSE" in the map, or add a floating button).

### Bottom action bar:
**No changes.** The Inventory, Skill Book, Travel, Dungeon, Settings, Save & Quit
buttons stay exactly as-is. The `[D] Dungeon` button can coexist with the
clickable dungeon on the map — both call `_enter_dungeon()`.

### `_refresh_city_id()`:
Add a call to `self.city_map.refresh()` when the city changes.

---

## Phase 4 — Terminal Mode (`city.py`)

Minimal change — print the map before the service list.

In `visit_city()`, after `clear_screen()` and the header, add:
```python
from resources.city_maps import get_city_map
map_art = get_city_map(city_id)
if map_art:
    print(map_art)
    print()
```

Then continue with the existing numbered menu. No coordinate overlay needed in
terminal mode — the map is ambient art, navigation stays via numbered input.

Lines changed: ~5

---

## Phase 5 — Testing & Polish

### 5.1 Verify all 19 cities render without errors
Loop through all cities and check each map loads + positions dict has entries for
all services in that city's `CITIES[city]["services"]` list.

### 5.2 Window resize behavior
The Text widget should expand/shrink. Set `pack(fill=tk.BOTH, expand=True)`.
If the map font is too large for small windows, consider a smaller font size.

### 5.3 Focus management
After clicking a service on the map, focus must return to the CityScreen frame
so keyboard shortcuts work. Call `self.focus_set()` in click handlers.

### 5.4 House edge case
When the player owns a house but the map doesn't have a house marker, show a
button in the map_frame below the Text widget. When the map DOES have a house
marker (like Solmere), use a position entry with service key `"house"`.

---

## File Summary

| File | Action | Est. Lines Changed |
|------|--------|-------------------|
| `resources/city_maps.py` | Modify — add `CITY_SERVICE_POSITIONS` dict | +~100 |
| `gui/widgets/city_map.py` | **Create** — new CityMapWidget class | ~120 |
| `gui/screens/city_screen.py` | Modify — replace button grid with map widget | ~60 changed / ~40 removed |
| `city.py` | Modify — print map in terminal mode | +~5 |

**Total: 4 files, ~285 lines of new/changed code, ~40 lines removed.**

---

## Execution Order

1. **Phase 1** — Add `CITY_SERVICE_POSITIONS` to `city_maps.py` (data entry, can be done incrementally)
2. **Phase 2** — Create `gui/widgets/city_map.py` widget
3. **Phase 3** — Integrate into `city_screen.py` (the actual wiring)
4. **Phase 4** — Terminal mode print in `city.py`
5. **Phase 5** — Smoke test all 19 cities
