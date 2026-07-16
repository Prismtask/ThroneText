# Phase 3 Changes — Inventory, Facilities & Dungeon GUI

## Overview
This document records all changes made during **Phase 3** of the GUI migration:
integrating inventory management, facility screens, and dungeon crawling into the
tkinter GUI layer.

- **Terminal mode is fully preserved** — `python launcher.py --terminal` works identically.
- **GUI mode is the default** — `python launcher.py` opens the tkinter interface.
- **No save file format changes** — existing saves load in both modes.
- **No facility files were modified** — all existing facility code remains untouched.

---

## Architecture

Phase 3 introduces three new screen types and a shared I/O redirection layer:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CityScreen                                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │  Inventory  │  │  Dungeon    │  │  Services   │  │   Skill Book    │ │
│  │   Button    │  │   Button    │  │   Buttons   │  │     Button      │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └────────┬────────┘ │
│         │                │                │                  │          │
│         ▼                ▼                ▼                  ▼          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────────┐  │
│  │InventoryScreen│  │DungeonScreen │  │      FacilityScreen          │  │
│  │  (tabbed)    │  │ (thread+IO)  │  │  (generic wrapper)           │  │
│  │              │  │              │  │  • shop, inn, blacksmith     │  │
│  │ Tabs:        │  │              │  │  • temple, guild, barracks   │  │
│  │ • Stats      │  │ Map panel    │  │  • house, travel, etc.       │  │
│  │ • Bag        │  │ Output log   │  │                              │  │
│  │ • Skills     │  │ Input entry  │  │  Runs facility function in   │  │
│  │ • Allies     │  │              │  │  background thread with I/O  │  │
│  │ • Bounties   │  │ Combat →     │  │  redirected to GUI Text      │  │
│  │              │  │ CombatScreen │  │  widget.                     │  │
│  └──────────────┘  └──────────────┘  └──────────────────────────────┘  │
│         │                │                            │                 │
│         └────────────────┴────────────────────────────┘                 │
│                              │                                          │
│                              ▼                                          │
│                    Returns to CityScreen                                │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## New Files Created (4)

### 1. `gui/screens/facility_screen.py`
**Generic terminal-to-GUI wrapper for all facility functions.**

- `FacilityScreen` — runs any facility function in a `daemon=True` background thread
- Thread-safe I/O redirection via monkey-patched `builtins.print` and `builtins.input`
- Only redirects I/O when the calling thread is the facility thread (safe for tkinter main loop)
- Features:
  - Scrollable output Text widget (monospace font)
  - Input Entry widget with Enter key binding
  - Continue button for "Press Enter to continue..." prompts
  - Back button with running-thread confirmation
  - `_after_facility()` callback refreshes city UI on return

### 2. `gui/screens/inventory_screen.py`
**Full tabbed GUI replacing `inventory_ui.py`.**

- Uses `ttk.Notebook` with custom dark theme styling (`Inv.TNotebook`)
- **Tab 1 — Stats & Equipment:**
  - Player name, level, HP, gold
  - Attributes with breakdown (base + equipment + buffs)
  - Milestone labels
  - Equipment slots with rarity-colored names and Unequip buttons
  - Passive skill display
  - Milestone bonuses
- **Tab 2 — Bag:**
  - Inventory cap counters
  - Equipment list with Equip/Drop buttons
  - Item list (consumables/utility) with Use/Drop buttons
  - Rarity-colored item names
- **Tab 3 — Skills:**
  - Unlocked skills (green) with cooldown and mastery
  - Locked skills (gray)
- **Tab 4 — Allies:**
  - Ally cards with HP, equipment, skills
  - Equip/Unequip buttons for each ally
  - Accessory slot selection dialog when both slots occupied
- **Tab 5 — Bounties:**
  - Progress tracking with completion highlighting
  - Days remaining
- **Actions:** Equip, Unequip, Use, Drop with automatic UI refresh
- **Accessory handling:** Dialog prompts when both accessory slots are occupied

### 3. `gui/screens/dungeon_screen.py`
**Dungeon crawl GUI extending FacilityScreen.**

- Runs `explore_dungeon()` in a background thread with I/O redirected to GUI
- **Left panel:** ASCII map display (Text widget, monospace)
- **Right panel:** Dungeon log output (scrollable Text widget)
- **Bottom:** Input area + Flee button
- **Combat integration:** Uses existing `combat_override` mechanism to launch `CombatScreen`
- Returns to `CityScreen` with result handling (dead/fled/save_exit/success)

### 4. `tests/test_phase3.py`
**12 test cases:**

| # | Test | Description |
|---|------|-------------|
| 1 | `test_facility_screen_import` | FacilityScreen imports cleanly |
| 2 | `test_inventory_screen_import` | InventoryScreen imports cleanly |
| 3 | `test_dungeon_screen_import` | DungeonScreen imports cleanly |
| 4 | `test_city_screen_import` | CityScreen imports cleanly |
| 5 | `test_inventory_ui_unchanged` | inventory_ui.py still imports (no breaking changes) |
| 6 | `test_facility_screen_instantiation` | FacilityScreen creates without tk errors |
| 7 | `test_inventory_screen_instantiation` | InventoryScreen creates without tk errors |
| 8 | `test_dungeon_screen_instantiation` | DungeonScreen creates without tk errors |
| 9 | `test_city_screen_instantiation` | CityScreen creates without tk errors |
| 10 | `test_io_redirection_helpers` | I/O redirection functions exist |
| 11 | `test_dungeon_combat_override_still_exists` | explore_dungeon accepts combat_override |
| 12 | `test_inventory_ui_data_functions_exist` | Terminal inventory functions still exist |

---

## Modified Files (1)

### `gui/screens/city_screen.py`
**Wired all Phase 3 screens into the city hub.**

| Method | Before (Phase 2) | After (Phase 3) |
|--------|------------------|-----------------|
| `_open_service()` | Called handler directly in terminal | Switches to `FacilityScreen` wrapper |
| `_open_house()` | Called `house_menu()` in terminal | Switches to `FacilityScreen` wrapper |
| `_open_inventory()` | Called `manage_inventory_menu()` in terminal | Switches to `InventoryScreen` |
| `_open_skill_book()` | Called `skill_book_menu()` in terminal | Switches to `FacilityScreen` wrapper |
| `_enter_dungeon()` | Ran dungeon in raw thread with combat_override | Switches to `DungeonScreen` |
| `_after_facility()` | *new* | Shared callback to refresh UI after any facility |

---

## Files Untouched (terminal mode still works)

```
main.py                 # Still the terminal entry point
inventory_ui.py         # Still used by terminal mode
facilities/*.py         # All 16 facility files unchanged
dungeon.py              # Unchanged — combat_override still works
dungeon_rooms.py        # Unchanged
combat/*.py             # Unchanged from Phase 2
save_load.py            # No changes
leveling.py             # No changes
events.py               # No changes
utils.py                # No changes
resources/              # No changes
```

---

## Screen Transition Flow (Phase 3)

```
[MainMenuScreen]
    ├── New Game ───────────→ [CharCreateScreen] ──Step 4──→ [CityScreen]
    ├── Continue ───Load Dialog──→ [CityScreen]
    └── Quit

[CityScreen]
    ├── Services ──→ [FacilityScreen] ──→ [CityScreen]
    ├── House ─────→ [FacilityScreen] ──→ [CityScreen]
    ├── Inventory ─→ [InventoryScreen] ──→ [CityScreen]
    ├── Skill Book ─→ [FacilityScreen] ──→ [CityScreen]
    ├── Travel ────→ calls travel_to_city() ──→ refreshes [CityScreen]
    ├── Dungeon ───→ [DungeonScreen]
    │                  ├── Combat Room ──→ [CombatScreen] ──→ [DungeonScreen]
    │                  └── Floor Clear ──────────────────────→ [CityScreen]
    └── Save & Quit ──→ save_game() ──→ [MainMenuScreen]
```

---

## How to Run

### GUI Mode (default)
```bash
cd C:\Code\TerminalRPG
.venv\Scripts\python.exe launcher.py
```

### Terminal Mode (legacy)
```bash
cd C:\Code\TerminalRPG
.venv\Scripts\python.exe launcher.py --terminal
```

### Build EXE
```bash
cd C:\Code\TerminalRPG
.venv\Scripts\python.exe make_exe.py
```

### Run Phase 3 Tests
```bash
cd C:\Code\TerminalRPG
.venv\Scripts\python.exe -m unittest tests.test_phase3 -v
```

---

## Test Results

```
PASS: test_facility_screen_import
PASS: test_inventory_screen_import
PASS: test_dungeon_screen_import
PASS: test_city_screen_import
PASS: test_inventory_ui_unchanged
PASS: test_facility_screen_instantiation
PASS: test_inventory_screen_instantiation
PASS: test_dungeon_screen_instantiation
PASS: test_city_screen_instantiation
PASS: test_io_redirection_helpers
PASS: test_dungeon_combat_override_still_exists
PASS: test_inventory_ui_data_functions_exist

All 12 Phase 3 tests passed!
```

All new and modified files pass `python -m py_compile` syntax checks.
All existing Phase 0/1/2 tests still pass.

---

## Design Decisions

### Why FacilityScreen uses monkey-patched builtins
The 16 facility files (`facilities/shop.py`, `inn.py`, `house.py`, etc.) collectively
contain ~300+ `print()` and `input()` calls. Refactoring all of them to use an
I/O adapter (like Phase 2's `c_print`/`c_input`) would require touching every
facility file and risk introducing bugs. Instead, `FacilityScreen` temporarily
redirects `builtins.print` and `builtins.input` **only for the facility thread**,
using a thread-identity check to avoid affecting the tkinter main loop.

This approach:
- Requires **zero changes** to existing facility files
- Preserves **100% backwards compatibility** with terminal mode
- Adds only ~150 lines of generic wrapper code

### Why DungeonScreen extends FacilityScreen
The dungeon flow (`explore_dungeon()`) contains terminal I/O for room
descriptions, ASCII maps, post-room menus, and save prompts. Rather than
refactoring the entire dungeon engine, `DungeonScreen` reuses the same
thread+I/O redirection pattern as `FacilityScreen` but adds:
- An ASCII map panel
- Dungeon-specific branding
- Integration with the existing `combat_override` → `CombatScreen` flow

Future phases could replace this with a fully-native dungeon GUI.

### InventoryScreen is a proper native GUI
Inventory is the most frequently used non-combat screen, so it received a
full native GUI implementation with:
- Real-time equip/unequip with stat updates
- Tabbed organization
- Rarity-colored item display
- Ally management with equipment dialogs

---

## Next: Phase 4 (Polish & Release)

Planned files:
- `gui/screens/settings_screen.py` — Sound toggle, font size, color theme
- `gui/widgets/damage_popup.py` — Floating damage numbers
- `gui/combat/initiative_bar.py` — Visual turn order strip
- Keyboard shortcuts (1-9 for skills, A for attack, I for inventory, etc.)
- Splash screen / title art
- Full playthrough testing
- Update `make_exe.py` and build release
