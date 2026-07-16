# Phase 4 Changes — Polish & Release

## Overview
This document records all changes made during **Phase 4** of the GUI migration:
settings persistence, keyboard shortcuts, escape key handling, notification toasts,
log window, death screen, post-floor screen, splash screen, and bug fixes.

- **Terminal mode is fully preserved** — `python launcher.py --terminal` works identically.
- **GUI mode is the default** — `python launcher.py` opens the tkinter interface with all Phase 4 features.
- **No save file format changes** — existing saves load in both modes.

---

## Architecture: Pre-Existing Phase 4 Files

Several Phase 4 files already existed in the codebase with complete implementations:

| File | Status | Purpose |
|------|--------|---------|
| `gui/settings.py` | ✅ Pre-existing | Load/save `gui_settings.json` with `DEFAULT_SETTINGS` dict |
| `gui/screens/settings_screen.py` | ✅ Pre-existing | Font size, window size, keyboard mode, splash toggle, audio placeholder |
| `gui/screens/death_screen.py` | ✅ Pre-existing | Death screen with Continue/Quit buttons |
| `gui/screens/post_floor_screen.py` | ✅ Pre-existing | Floor cleared rewards with Continue/Return/Save & Quit |
| `gui/screens/splash_screen.py` | ✅ Pre-existing | 2.5s title splash with click-to-skip |
| `gui/widgets/notification_toast.py` | ✅ Pre-existing | Auto-dismissing colored toast banners |
| `gui/widgets/log_window.py` | ✅ Pre-existing | Scrollable log history with category filter + search |
| `gui/theme.py` `set_font_size()` | ✅ Pre-existing | Dynamic font size rebuilder |

---

## Bug Fixes (Pre-existing Issues)

### 1. Duplicate `ScreenManager` class removed (`gui/screen_manager.py`)
**Problem:** The file had TWO `ScreenManager` class definitions. The OLD barebones version
(lines ~238-350) overwrote the NEW Phase 4 version (lines ~1-237), making all Phase 4
features (structured top bar, toasts, log window, persistent log, `refresh_top_bar`)
completely inaccessible.

**Fix:** Removed the duplicate OLD `ScreenManager` class. The NEW class is now the
only definition and includes:
- Structured top bar: `top_name`, `top_info`, `top_gold` widgets
- `refresh_top_bar(player)` — updates all top bar widgets from player dict
- `show_toast(message, category, duration_ms)` — slide-in toast notifications
- `_open_log_window()` / 📜 button — persistent scrollable log popup
- `_log_entries` list — session-persistent log storage (not cleared on screen switch)
- `switch_to()` now calls `focus_set()` on the new screen (required for keyboard binds)
- Settings dict integrated via constructor parameter

### 2. Corrupted `handle_escape()` in `base_screen.py`
**Problem:** The method had duplicate trailing code (`self.sm.log(message)` after the
`go_back()` call), causing it to be malformed.

**Fix:** Cleaned up to a single correct method:
```python
def handle_escape(self):
    if self.sm:
        self.sm.go_back()
```

### 3. Duplicate death handler code in `city_screen.py`
**Problem:** `_handle_death()` called `handle_player_death()` twice in sequence,
resulting in the death penalty being applied twice.

**Fix:** Replaced with a proper `DeathScreen` integration using `apply_death_penalty()`.

### 4. Duplicate code in `dungeon_screen.py` `_update_map()`
**Problem:** The method body had two identical `try/except` blocks stacked.

**Fix:** Removed the duplicate block.

---

## New Changes Made (Phase 4 Implementation)

### 5. `utils.py` — Added `apply_death_penalty()` pure function

**Problem:** `handle_player_death()` does terminal I/O (print/input). Calling it from
the GUI `DeathScreen` would try to read from stdin.

**Fix:** Extracted the penalty-application logic into a new pure function
`apply_death_penalty(player)` that applies gold loss, time advance, HP reset,
location reset, dungeon progress wipe, combat state cleanup, and auto-save
**without any I/O**. The original `handle_player_death()` now calls
`apply_death_penalty()` after its terminal UI, preserving terminal mode behavior.

Returns `penalty_gold` for display purposes.

### 6. `gui/app.py` — Full Phase 4 wiring

**Changes:**
- **Settings loading:** `load_settings()` called before window creation
- **Font size:** `set_font_size()` called before any widget creation
- **Window geometry:** Uses saved `window_size` and `window_position` from settings
- **Settings parameter:** Passed to `ScreenManager` constructor as `settings=` kwarg
- **Global keyboard shortcuts:**
  - `Escape` → delegates to current screen's `handle_escape()`
  - `I` → opens `InventoryScreen` from city/dungeon screens
  - `Ctrl+Q` → closes the application
- **Window close handler:** `WM_DELETE_WINDOW` captures current size/position and
  saves settings before destroying the window
- **Splash screen:** Shows `SplashScreen` for 2.5s before `MainMenuScreen` if
  `settings["show_splash"]` is True; skipped otherwise
- **Imports:** Added `load_settings`, `save_settings`, `set_font_size`

### 7. `gui/screens/main_menu_screen.py` — Polish

**Changes:**
- Removed "GUI Mode (Phase 1)" label — replaced with "v1.0.0 — GUI Edition"
- Added **Settings** button that switches to `SettingsScreen` (with history push)
- Added `_on_settings()` handler

### 8. `gui/screens/combat_screen.py` — Keyboard bindings

**Changes:**
- Added `_setup_key_binds()` method — binds `<KeyPress>` on the screen frame
- Added `_on_key(event)` handler with full keyboard mapping:

| Key | Action |
|-----|--------|
| `A` | Attack |
| `D` | Defend |
| `F` | Flee |
| `C` | Capture |
| `U` | Use Item |
| `1`–`9` | Skill slot (if available) |
| `0` | Cancel |
| `Enter` | Continue (when continue button visible) |
| `Esc` | Cancel target selection / Cancel action |

- Added `handle_escape()` override — cancels target selection mode, otherwise no-op
- Validates actions against `self.action_panel._buttons` before sending

### 9. `gui/screens/city_screen.py` — Death & Settings integration

**Changes:**
- Added **Settings** button to the bottom action bar
- Added `_open_settings()` method — switches to `SettingsScreen`
- Rewrote `_handle_death()` to use `DeathScreen` with proper callbacks:
  - Continue → `apply_death_penalty()` → fresh `CityScreen`
  - Quit → `MainMenuScreen`
- Added `handle_escape()` override — no-op (city has no modal state)
- Fixed duplicate death handler code (was calling `handle_player_death` twice)

### 10. `gui/screens/dungeon_screen.py` — Bug fixes

**Changes:**
- Fixed duplicate code in `_update_map()` method
- Added `handle_escape()` override — no-op (wraps FacilityScreen input handling)

### 11. `gui/screens/inventory_screen.py` — Escape support

**Changes:**
- Added `handle_escape()` override — calls `self.sm.go_back()` to return to
  previous screen (city or dungeon)

### 12. `gui/screens/facility_screen.py` — Escape guard

**Changes:**
- Added `handle_escape()` override — if input is active (`_input_mode` is True),
  Esc is silently ignored (prevents accidental exit during prompts). Otherwise,
  calls `_on_back()`.

### 13. `gui/screens/char_create_screen.py` — Step navigation

**Changes:**
- Updated `_prev_step()` — on step 1, goes back to main menu via `self.sm.go_back()`
- Added `handle_escape()` override — delegates to `_prev_step()`

### 14. `gui/screens/death_screen.py` — Use GUI-safe penalty

**Changes:**
- `_do_continue()` default now calls `apply_death_penalty()` instead of
  `handle_player_death()` to avoid terminal I/O

---

## Files Created (Phase 4)

All Phase 4 files were pre-existing in the codebase and required no creation:

```
gui/settings.py                       (pre-existing)
gui/screens/settings_screen.py        (pre-existing)
gui/screens/death_screen.py           (pre-existing)
gui/screens/post_floor_screen.py      (pre-existing)
gui/screens/splash_screen.py          (pre-existing)
gui/widgets/notification_toast.py     (pre-existing)
gui/widgets/log_window.py             (pre-existing)
```

## Files Modified (Phase 4)

| File | Nature of Change |
|------|-----------------|
| `gui/screen_manager.py` | Removed duplicate OLD `ScreenManager` class (was shadowing the NEW one) |
| `gui/screens/base_screen.py` | Fixed corrupted `handle_escape()` method |
| `gui/app.py` | Settings loading, font size, global keybinds, splash, window close save |
| `gui/screens/main_menu_screen.py` | Removed "Phase 1" label, added version + Settings button |
| `gui/screens/combat_screen.py` | Added keyboard bindings (A/D/F/C/U/1-9/Esc/Enter) + `handle_escape` |
| `gui/screens/city_screen.py` | Added Settings button, rewrote death handler, fixed duplicate code |
| `gui/screens/dungeon_screen.py` | Fixed duplicate code, added `handle_escape` |
| `gui/screens/inventory_screen.py` | Added `handle_escape` (returns to previous screen) |
| `gui/screens/facility_screen.py` | Added `handle_escape` (guards against accidental exit during input) |
| `gui/screens/char_create_screen.py` | Added `handle_escape` (goes to previous step or main menu) |
| `gui/screens/death_screen.py` | Uses `apply_death_penalty()` instead of `handle_player_death()` |
| `utils.py` | Added `apply_death_penalty()` pure function; refactored `handle_player_death()` |

## Files Untouched (terminal mode still works)

```
main.py                 # Terminal entry point
launcher.py             # Dual-mode entry (unchanged)
city.py                 # Terminal city loop
dungeon.py              # Terminal dungeon
combat/*.py             # Combat engine (unchanged from Phase 2)
facilities/*.py         # All facility files (unchanged from Phase 3)
inventory_ui.py         # Terminal inventory (unchanged)
save_load.py            # Save/load (unchanged)
leveling.py             # Pure logic (unchanged)
events.py               # Event system (unchanged)
resources/              # Data files (unchanged)
make_exe.py             # Build system (unchanged)
gui/combat/action_panel.py  # Already exposes ._buttons dict
gui/theme.py            # Already had set_font_size()
gui/settings.py         # Pre-existing
```

---

## Screen Transition Flow (Phase 4)

```
[SplashScreen (2.5s)] ──→ [MainMenuScreen]
    ├── New Game ───────────→ [CharCreateScreen] ──Step 4──→ [CityScreen]
    ├── Continue ───Load Dialog──→ [CityScreen]
    ├── Settings ──→ [SettingsScreen] ──→ [MainMenuScreen]
    └── Quit

[CityScreen]
    ├── Services ──→ [FacilityScreen] ──→ [CityScreen]
    ├── House ─────→ [FacilityScreen] ──→ [CityScreen]
    ├── Inventory ─→ [InventoryScreen] ──→ [CityScreen]
    ├── Skill Book ─→ [FacilityScreen] ──→ [CityScreen]
    ├── Travel ────→ calls travel_to_city() ──→ refreshes [CityScreen]
    ├── Dungeon ───→ [DungeonScreen]
    │                  ├── Combat Room ──→ [CombatScreen] ──→ [DungeonScreen]
    │                  ├── Death ──→ [DeathScreen] ──→ [CityScreen] or [MainMenuScreen]
    │                  └── Floor Clear ──────────────────────→ [CityScreen]
    ├── Settings ───→ [SettingsScreen] ──→ [CityScreen]
    └── Save & Quit ──→ save_game() ──→ [MainMenuScreen]

[Global Hotkeys]
    Esc ──→ screen.handle_escape()  (per-screen behavior)
    I   ──→ InventoryScreen         (from City or Dungeon)
    Ctrl+Q → Quit application
```

---

## Keyboard Shortcuts Reference

### Global (any screen)
| Key | Action |
|-----|--------|
| `Esc` | Back / Cancel (screen-dependent) |
| `I` | Open Inventory (from city or dungeon) |
| `Ctrl+Q` | Quit application |

### Combat
| Key | Action |
|-----|--------|
| `A` | Attack |
| `D` | Defend |
| `F` | Flee |
| `C` | Capture |
| `U` | Use Item |
| `1`–`9` | Skill slot |
| `0` | Cancel |
| `Enter` | Continue |
| `Esc` | Cancel target selection |

### Character Creation
| Key | Action |
|-----|--------|
| `Esc` | Previous step (or main menu on step 1) |

---

## Test Results

```
Phase 0 verification PASSED - all modules import and instantiate correctly.
Phase 1 verification PASSED - all modules import and build_character works.
Phase 3 tests: 12/12 PASSED
  - FacilityScreen, InventoryScreen, DungeonScreen, CityScreen imports
  - inventory_ui.py unchanged
  - All screen instantiation tests
  - I/O redirection helpers
  - Dungeon combat_override compatibility

All 18 modified/new files pass py_compile syntax checks.
Terminal mode entry points (main.py, launcher.py) import correctly.
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

---

## Settings File

GUI settings are saved to `savefile/gui_settings.json` independently of game saves:

```json
{
  "window_size": "900x700",
  "window_position": "+100+100",
  "font_size": 11,
  "theme": "dark",
  "sound_enabled": false,
  "keyboard_mode": true,
  "show_splash": true,
  "log_max_lines": 1000
}
```

Settings are saved automatically on window close and on "Apply & Close" in the Settings screen.

---

*End of Document*
