# TerminalRPG GUI Migration — Phase 0 & 1 Change Log

## Overview

This document records all changes made during **Phase 0** (Architecture & Foundation) and **Phase 1** (Main Menu, Character Creation, City Hub) of the GUI migration.

- **Terminal mode is fully preserved** — `python launcher.py --terminal` works identically to before.
- **GUI mode is now the default** — `python launcher.py` opens the tkinter interface.
- **No save file format changes** — existing saves load in both modes.

---

## Phase 0: Architecture & Foundation

### New Directories Created

```
gui/                          # Root GUI package
├── combat/                   # Combat HUD components (placeholder for Phase 2)
├── screens/                  # Screen controllers
│   └── facilities/           # Facility screens (placeholder for Phase 3)
└── widgets/                  # Reusable UI widgets
```

### New Files Created (14 files)

| # | File | Purpose |
|---|------|---------|
| 1 | `launcher.py` | **New entry point**. `launcher.py` → GUI mode (default). `launcher.py --terminal` → legacy terminal mode. Replaces `main.py` as the PyInstaller entry point. |
| 2 | `gui/__init__.py` | Package marker for the GUI layer. |
| 3 | `gui/theme.py` | Dark theme constants: colors (`#1a1a2e` bg, `#e94560` accent), monospace font selection (Consolas/Menlo/DejaVu Sans Mono), rarity colors, window defaults (900x700). |
| 4 | `gui/screen_manager.py` | `ScreenManager` class — handles screen transitions, back-stack navigation, persistent top status bar, bottom log panel, and shared game state. |
| 5 | `gui/notification_queue.py` | `NotificationQueue` — queued alert/toast system for events that need deferring (e.g. day-rollover while in dungeon). |
| 6 | `gui/io_redirector.py` | `GUIRedirector` — optional stdout capture that forwards stray `print()` calls into the GUI log panel during gradual migration. |
| 7 | `gui/app.py` | `TerminalRPGApp` — main tkinter application class. Creates root window, instantiates `ScreenManager`, launches `MainMenuScreen`. |
| 8 | `gui/screens/__init__.py` | Package marker. |
| 9 | `gui/screens/base_screen.py` | `BaseScreen` — abstract base class (ABC) that all screens inherit from. Provides `styled_button()`, `styled_label()`, `styled_frame()`, and `log()` helpers. |
| 10 | `gui/combat/__init__.py` | Package marker (Phase 2). |
| 11 | `gui/widgets/__init__.py` | Package marker. |
| 12 | `gui/widgets/hp_bar.py` | `HPBar` — custom Canvas-based progress bar for HP/MP/XP with percentage text overlay. |
| 13 | `gui/widgets/stat_display.py` | `StatDisplay` — attribute line widget: `STR: 8 + 2(eq) + 1(buff) = 11`. |
| 14 | `gui/widgets/item_card.py` | `ItemCard` — clickable card with rarity-colored name, slot, stats, and description. |
| 15 | `gui/widgets/confirm_dialog.py` | `confirm_dialog()` and `ok_dialog()` — true modal Toplevel dialogs (Yes/No, OK). |

### Modified Files

| File | Changes |
|------|---------|
| `make_exe.py` | **Entry point** changed from `main.py` to `launcher.py`. Added `gui/` directory to `--add-data` bundles. Added tkinter hidden imports (`tkinter`, `tkinter.ttk`, `tkinter.font`, `tkinter.messagebox`). |

### Test Files Created

| File | Purpose |
|------|---------|
| `tests/test_phase0.py` | Import/instantiation verification for all Phase 0 modules. |

---

## Phase 1: Main Menu, Character Creation, City Hub

### New Files Created (3 screens + 1 test)

| # | File | Purpose |
|---|------|---------|
| 1 | `gui/screens/main_menu_screen.py` | **MainMenuScreen** — Full GUI main menu with four buttons: **New Game** → CharCreateScreen, **Continue** → load dialog (slot selection radio buttons), **Delete Save** → delete dialog (with overwrite confirmation), **Quit** → confirmation dialog. |
| 2 | `gui/screens/char_create_screen.py` | **CharCreateScreen** — 4-step wizard: (1) Race selection — 8 clickable cards with mod summaries, (2) Class selection — 8 clickable cards, (3) Point allocation — +/- buttons per attribute with live remaining-points counter, (4) Name & Save Slot — Entry widget + Combobox. Calls extracted `build_character()` pure function. Validates each step with `ok_dialog()` popups. |
| 3 | `gui/screens/city_screen.py` | **CityScreen** — Dynamic city hub. Reads `CITIES` data to render service buttons in a grid. Conditional **House** button with pending income display. Bottom action bar: Inventory, Skill Book, Travel, Dungeon (Phase 2 placeholder), Save & Quit. Persistent top bar shows name, city, floor, date, time, gold. |
| 4 | `tests/test_phase1.py` | Import/instantiation verification + `build_character()` logic test. |

### Modified Files

| File | Changes |
|------|---------|
| `character.py` | **Extracted `build_character(race_key, class_key, final_attrs, name, slot)`** as a pure function (no I/O). This function creates the complete player dict with all default fields, elemental resistances, etc. `create_character()` now calls `build_character()` at the end — terminal mode behavior is **unchanged**. `allocate_points()` now accepts optional `remaining` parameter for GUI mode. |
| `gui/app.py` | Replaced Phase 0 placeholder screen. Now launches `MainMenuScreen` directly via `screen_manager.switch_to(MainMenuScreen, push_history=False)`. |

---

## Complete File Inventory

### Files Created (by this migration)

```
launcher.py
gui/__init__.py
gui/theme.py
gui/screen_manager.py
gui/notification_queue.py
gui/io_redirector.py
gui/app.py
gui/screens/__init__.py
gui/screens/base_screen.py
gui/screens/main_menu_screen.py
gui/screens/char_create_screen.py
gui/screens/city_screen.py
gui/combat/__init__.py
gui/widgets/__init__.py
gui/widgets/hp_bar.py
gui/widgets/stat_display.py
gui/widgets/item_card.py
gui/widgets/confirm_dialog.py
tests/test_phase0.py
tests/test_phase1.py
```

### Files Modified (by this migration)

```
character.py          # Extracted build_character() pure function
make_exe.py           # Entry point = launcher.py, added gui/ bundling
gui/app.py            # Now launches MainMenuScreen
```

### Files Untouched (terminal mode still works)

```
main.py               # Still the terminal entry point
city.py               # Still used by terminal mode
save_load.py          # No changes — pickle format identical
dungeon.py            # Untouched — Phase 2 will add GUI screen
combat/*.py           # Untouched — Phase 2 will add GUI renderer
facilities/*.py       # Untouched — Phase 3 will add GUI screens
inventory_ui.py       # Untouched — Phase 3 will add GUI screen
leveling.py           # Untouched — pure logic
events.py             # Untouched — pure logic
utils.py              # Untouched — used by both modes
resources/            # Untouched — data files
```

---

## Screen Transition Flow

```
[MainMenuScreen]
    ├── New Game ───────────→ [CharCreateScreen] ──Step 4──→ [CityScreen]
    ├── Continue ───Load Dialog──→ [CityScreen]
    └── Quit

[CityScreen]
    ├── Services ──→ calls facility handlers (terminal console for now)
    ├── House ─────→ calls house_menu (terminal console for now)
    ├── Inventory / Skill Book ──→ terminal console (Phase 3)
    ├── Travel ────→ calls travel_to_city() ──→ refreshes to new city
    ├── Dungeon ───→ "Coming in Phase 2" dialog (placeholder)
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
The built `TerminalRPG.exe` will default to GUI mode. Pass `--terminal` for legacy mode.

---

## Test Results

```
Phase 0 verification PASSED - all modules import and instantiate correctly.
Phase 1 verification PASSED - all modules import and build_character works.
main.py OK (terminal mode preserved)
```

---

## Phase 2, 3, and 4

See the following detailed documents:

| Phase | Document | Summary |
|-------|----------|---------|
| **Phase 2** | `unrelated for coding/PHASE2_CHANGES.md` | Combat GUI: renderer, action panel, thread-based I/O bridge, superboss integration |
| **Phase 3** | `unrelated for coding/PHASE3_CHANGES.md` | Inventory (tabbed), FacilityScreen wrapper, DungeonScreen with ASCII map |
| **Phase 4** | `unrelated for coding/PHASE4_CHANGES.md` | Settings persistence, keyboard shortcuts, escape handling, death/post-floor/splash screens, notification toasts, log window, bug fixes |

## Quick Reference: All Phases Complete

| Phase | Status | Key Deliverable |
|-------|--------|-----------------|
| **Phase 0** | ✅ | Architecture, `launcher.py`, theme, screen manager, widgets |
| **Phase 1** | ✅ | Main menu, character creation, city hub |
| **Phase 2** | ✅ | Combat HUD, action buttons, thread-based I/O, enemy click-targeting |
| **Phase 3** | ✅ | Tabbed inventory, FacilityScreen wrapper, DungeonScreen with map |
| **Phase 4** | ✅ | Settings, keyboard shortcuts, escape handling, death screen, splash, toasts, log window |
