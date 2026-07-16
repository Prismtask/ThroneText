# Phase 2 Changes — Combat GUI Integration

## Overview
This document records all changes made during **Phase 2** of the GUI migration:
integrating the tkinter combat screen (`CombatScreen`) with the existing terminal-based
combat engine. The combat engine now runs in a background thread, bridged to the GUI
via a thread-safe I/O abstraction layer.

---

## New Files (8)

### 1. `combat/combat_io.py`
**Thread-safe I/O redirection layer.**

- `BaseCombatIO` — abstract base with `print()`, `input()`, `clear()`, `show_hud()`
- `TerminalIO` — default implementation using `builtins.print` / `builtins.input`
- `get_io()` / `set_io()` / `reset_io()` — thread-local storage via `threading.local()`
- `c_print()` / `c_input()` / `c_clear()` — convenience aliases used by all combat modules

### 2. `gui/combat/combat_renderer.py`
**HUD renderer — party vs enemies layout.**

- Left column: party members (player + allies) with HP bars and buff tags
- Right column: enemies with HP bars, index numbers, monster-girl symbol (♀)
- Active-turn indicator (`>`)
- HP bar colors: green >50%, orange 25-50%, red <25%
- `highlight_enemy()` / `clear_target_highlight()` for target selection mode

### 3. `gui/combat/action_panel.py`
**Dynamic action button bar.**

- Builds buttons from `combat/action_menu.py` (Attack, Defend, Skills, Items, Flee, Capture)
- `set_actions()` — rebuilds buttons for current combatant
- `set_target_mode()` — disables non-target actions, shows selection prompt
- `enable_all()` / `disable_all()` — for enemy turns / loading states

### 4. `gui/screens/combat_screen.py`
**Main combat screen (the GUI integration hub).**

- Constructor accepts: `enemy_keys`, `floor`, `room_num`, `total_rooms`, `on_result`
- Pre-creates enemy instances so GUI shares state with combat thread
- `GUICombatIO` — queue-based I/O bridge (`input_queue` / `output_queue`)
- Runs `combat()` in a `daemon=True` background thread
- Polls output queue every 100ms, refreshes HUD every 200ms
- Handles all input modes: action, enemy_target, capture_target, item, continue
- Log widget for combat text output
- Continue button for "Press Enter to continue..." prompts
- Item selection Listbox for consumable/utility items
- Click-to-select enemy targets (bound to enemy frame widgets)

### 5. `gui/combat/__init__.py`
Empty init file for the `gui.combat` package.

### 6–8. `tests/test_phase2.py`
**8 test cases:**
1. `test_thread_local_io` — verifies independent IO per thread
2. `test_terminal_io_defaults` — default IO is `TerminalIO`
3. `test_format_combat_hud_data_structure` — HUD data dict has expected keys
4. `test_combat_engine_with_mock_io` — combat runs without real stdin/stdout
5. `test_gui_combat_io_bridge` — queue-based I/O works correctly
6. `test_combat_renderer_instantiation` — renderer creates without tk errors
7. `test_action_panel_instantiation` — action buttons build from menu
8. `test_dungeon_combat_override` — `explore_dungeon` accepts `combat_override`

---

## Modified Files (20+)

### Core Combat Engine

#### `combat/combat_engine.py`
- All `print()` → `c_print()`, `input()` → `c_input()`, `clear_screen()` → `c_clear()`
- Added `from combat.combat_io import c_print, c_input, c_clear`
- `combat()` and `_combat_inner()` now accept optional `enemies=None` parameter:
  - If `enemies` is provided, combat uses those instances directly (GUI shares state)
  - If `None`, creates fresh enemy instances from `enemy_keys` (terminal mode)

#### `combat/combat_ui.py`
- Added `from combat.combat_io import c_print, c_input, c_clear`
- All `print()` calls inside HUD functions changed to `c_print()`
- **New function:** `format_combat_hud_data(player, enemies, active_ally=None, header="")`
  - Returns structured dict with `party`, `enemies`, `header`, `action_menu`, `cooldowns`, `active_ally`
  - Used by both `print_combat_hud()` (terminal) and `CombatRenderer` (GUI)

#### `combat/player_actions.py`
- All `print()` → `c_print()`, `input()` → `c_input()`
- Added `from combat.combat_io import c_print, c_input, c_clear`

#### `combat/ally.py`
- All `print()` → `c_print()`, `input()` → `c_input()`
- Added `from combat.combat_io import c_print, c_input, c_clear`

#### `combat/enemy_ai.py`
- All `print()` → `c_print()`
- Added `from combat.combat_io import c_print, c_input, c_clear`

#### `combat/skills.py`
- All `print()` → `c_print()`, `input()` → `c_input()`
- Added `from combat.combat_io import c_print, c_input, c_clear`

### Superboss Files

All superboss combat files updated with `from combat.combat_io import c_print, c_input, c_clear` and replaced bare `print()`/`input()` calls:

| File | Changes |
|---|---|
| `combat/superboss_common.py` | `print()` → `c_print()`, `input()` → `c_input()` |
| `combat/broodmother.py` | Same |
| `combat/slitcurrent.py` | Same + syntax fix (removed duplicate imports) |
| `combat/ignis.py` | Same |
| `combat/sylvana.py` | Same + syntax fix (removed duplicate imports) |
| `combat/rientrante.py` | Same |
| `combat/everlong_ship.py` | Same + syntax fix (removed duplicate imports) |
| `combat/yinglong.py` | Same + syntax fix (removed duplicate imports) |

### Other Combat Files

| File | Changes |
|---|---|
| `combat/abyss_fang.py` | `print()` → `c_print()`, `input()` → `c_input()` |
| `combat/ally_skills.py` | Same |
| `combat/capture.py` | Same |
| `combat/captain_cutlass.py` | Same |
| `combat/tarnished_jade.py` | Same |
| `combat/wedding_specials.py` | Same |
| `combat/__init__.py` | Added `from . import combat_io` |

### Dungeon Integration

#### `dungeon.py`
- `explore_dungeon()` signature changed to accept `combat_override=None`
- Docstring added explaining the callback signature: `function(player, enemy_keys, **kwargs) -> str`
- In the `combat` room handler, checks `if combat_override:` before calling `combat()`:
  ```python
  if combat_override:
      result = combat_override(player, room["enemies"], floor=floor, room_num=i+1, total_rooms=total_rooms)
  else:
      result = combat(player, room["enemies"], floor=floor, room_num=i+1, total_rooms=total_rooms)
  ```

#### `gui/screens/city_screen.py`
- `_enter_dungeon()` completely rewritten:
  - Launches dungeon in a `daemon=True` background thread
  - Defines `gui_combat()` callback that schedules `CombatScreen` on the main thread via `self.sm.root.after(0, ...)`
  - Uses a `queue.Queue()` to block the dungeon thread until combat completes
  - `_return_from_dungeon()` handles results: death, flee, save_exit, success

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Main Thread (tkinter)                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │CombatRenderer│    │ ActionPanel  │    │  Log Widget  │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│         ▲                   ▲                   ▲          │
│         │                   │                   │          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              CombatScreen (polls queues)              │  │
│  │  • after(100, _poll) — processes output_queue       │  │
│  │  • after(200, _refresh_hud) — reads player/enemies  │  │
│  └──────────────────────────────────────────────────────┘  │
│         │ input_queue                │ output_queue        │
└─────────┼────────────────────────────┼─────────────────────┘
          │                            │
          ▼                            ▼
┌─────────────────────────────────────────────────────────────┐
│               Combat Thread (daemon=True)                    │
│  ┌──────────────┐    ┌────────────────────────────────────┐ │
│  │  GUICombatIO │◄───│  combat.combat_engine.combat()   │ │
│  │  • input()   │     │  • Uses c_print() / c_input()    │ │
│  │  • print()   │     │  • Modifies shared enemy dicts   │ │
│  └──────────────┘    └────────────────────────────────────┘ │
│         │                                                    │
│         └── set_io(GUICombatIO) before combat starts         │
└─────────────────────────────────────────────────────────────┘
```

---

## Backwards Compatibility

- **Terminal mode is fully preserved.** When no custom IO is set, `get_io()` returns `TerminalIO` which uses `builtins.print` and `builtins.input`.
- `launcher.py` and CLI workflows are unchanged — no changes were made to `launcher.py`.
- The `combat_override` parameter in `explore_dungeon()` defaults to `None`, so existing dungeon callers work without modification.

---

## Test Results

```
PASS: test_thread_local_io
PASS: test_terminal_io_defaults
PASS: test_format_combat_hud_data_structure
PASS: test_combat_engine_with_mock_io
PASS: test_gui_combat_io_bridge
PASS: test_combat_renderer_instantiation
PASS: test_action_panel_instantiation
PASS: test_dungeon_combat_override

All Phase 2 tests passed!
```

All 30+ modified files pass `python -m py_compile` syntax checks.
