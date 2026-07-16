# GUI I/O Migration Audit — Old Terminal I/O Usage Report

**Date:** 2026-07-08  
**Scope:** Every function in the TerminalRPG codebase that still uses legacy terminal I/O  
(`input()`, `print()`, `os.system('cls')`) instead of the GUI clickable/keyboard-shortcut  
hybrid system in the GUI execution path.

---

## Architecture Overview

The project has two I/O abstraction layers for the GUI:

| Layer | Module | Pattern | Status |
|-------|--------|---------|--------|
| **Combat I/O Bridge** | `combat/combat_io.py` | `c_input()` / `c_print()` / `c_clear()` | ✅ All combat files migrated |
| **Facility I/O Bridge** | `gui/terminal.py` | `term.print()` / `term.input()` / `term.menu()` / `term.pause()` / `term.confirm()` | ✅ All facility files migrated |
| **Dungeon I/O Bridge** | `dungeon.py` (helpers) | `_tprint()` / `_tpause()` / `_tclear()` / `_tmenu()` | ⚠️ Partially migrated — helpers exist but sub-modules don't use them |

### GUI Execution Path (where old I/O matters):
```
launcher.py → gui/app.py → gui/screens/
  ├── main_menu_screen.py     (own GUI implementation)
  ├── char_create_screen.py   (own GUI implementation)
  ├── city_screen.py          (own GUI implementation, calls facility functions via term)
  ├── dungeon_screen.py       → calls dungeon.explore_dungeon() in background thread
  │   ├── → dungeon_rooms.handle_*()     ❌ RAW I/O
  │   ├── → inventory_ui.manage_*()      ❌ RAW I/O
  │   ├── → leveling.gain_exp()          ❌ RAW I/O
  │   └── → combat.* (via combat_override) ✅ c_input/c_print
  ├── combat_screen.py        (own GUI implementation)
  ├── inventory_screen.py     (own GUI implementation)
  ├── facility_screen.py      (wraps facility functions with term)
  └── ...
```

---

## 🔴 CRITICAL — In GUI Execution Path, No Abstraction

These files are called directly or indirectly from `explore_dungeon()` which runs in the  
GUI dungeon background thread. Their raw `input()` calls will **hang or crash** in GUI mode.

---

### 1. `dungeon_rooms.py` — **ALL room handlers use raw I/O**

Called from `dungeon.explore_dungeon()` → GUI dungeon thread.

| Function | Line(s) | Raw I/O Calls | Issue |
|----------|---------|---------------|-------|
| `_select_party_member()` | 101 | `int(input("\nChoice: ").strip())` | Raw input for party selection |
| `_select_party_member()` | 92–99 | `print(...)` (5 calls) | Raw print for party list |
| `render_ascii_map()` | 215 | `input("\nPress Enter to continue...")` | Raw input for map pause (terminal fallback, but `_is_gui()` check only guards print, not input) |
| `handle_fountain_room()` | 237 | `input("\nChoice: ").strip()` | Raw input for fountain choice |
| `handle_fountain_room()` | 247 | `input("Press Enter...")` | Raw input (drink) |
| `handle_fountain_room()` | 256 | `input("Press Enter...")` | Raw input (immerse) |
| `handle_fountain_room()` | 270 | `input("Press Enter...")` | Raw input (splash allies) |
| `handle_fountain_room()` | 220–273 | `print(...)` (15+ calls) | Raw print for all fountain UI |
| `handle_merchant_room()` | 317 | `input("\nChoice: ").strip()` | Raw input for merchant menu |
| `handle_merchant_room()` | 320 | `input("Press Enter...")` | Raw input (buy/leave) |
| `handle_merchant_room()` | 327 | `input("Press Enter...")` | Raw input (no items to sell) |
| `handle_merchant_room()` | 340 | `int(input("\nSell which item? ").strip())` | Raw input for selling |
| `handle_merchant_room()` | 351 | `input("Press Enter...")` | Raw input (after sell) |
| `handle_merchant_room()` | 367 | `input("Press Enter...")` | Raw input (after buy) |
| `handle_merchant_room()` | 290–370 | `print(...)` (25+ calls) | Raw print for merchant UI |
| `handle_treasure_room()` | 404 | `input("\nPress Enter...")` | Raw input after treasure |
| `handle_treasure_room()` | 380–405 | `print(...)` (8+ calls) | Raw print for treasure UI |
| `handle_trap_room()` | 470 | `input("\nPress Enter...")` | Raw input after trap |
| `handle_trap_room()` | 430–472 | `print(...)` (15+ calls) | Raw print for trap UI |
| `handle_stat_check_room()` | 556 | `input("Press Enter to fight...")` | Raw input before forced combat |
| `handle_stat_check_room()` | 590 | `input("Press Enter...")` | Raw input after forced combat |
| `handle_stat_check_room()` | 592 | `input("\nPress Enter...")` | Raw input at end |
| `handle_stat_check_room()` | 500–595 | `print(...)` (30+ calls) | Raw print for stat check UI |

**Total: ~15 raw `input()` calls, ~100+ raw `print()` calls**

---

### 2. `inventory_ui.py` — **ALL inventory management uses raw I/O**

Called from `dungeon.explore_dungeon()` (post-room menu) and `city.visit_city()`.

| Function | Line(s) | Raw I/O Calls | Issue |
|----------|---------|---------------|-------|
| `display_player_status()` | 37–110 | `print(...)` (40+ calls) | Raw print for status display |
| `display_inventory_menu_options()` | 252–257 | `print(...)` (5 calls) | Raw print for menu |
| `handle_inventory_choice()` | 261 | `input("Press Enter...")` | Raw input on invalid choice |
| `manage_inventory_menu()` | 270 | `input("Choice: ").strip()` | Raw input for main menu |
| `manage_equipment_submenu()` | 293 | `input("Choice: ")` | Raw input for equip submenu |
| `manage_equipment_submenu()` | 298 | `input("Press Enter...")` | Raw input (no equipment) |
| `manage_equipment_submenu()` | 304 | `int(input("Equip which? (0 cancel): "))` | Raw input for equip selection |
| `manage_equipment_submenu()` | 318 | `input("Which slot? (1/2): ").strip()` | Raw input for accessory slot |
| `manage_equipment_submenu()` | 325 | `input("Slot to unequip: ").strip().lower()` | Raw input for unequip |
| `manage_equipment_submenu()` | 330 | `input("Press Enter...")` | Raw input after unequip |
| `manage_equipment_submenu()` | 335 | `input("Press Enter...")` | Raw input (no allies) |
| `manage_equipment_submenu()` | 340 | `input("Press Enter...")` | Raw input (no equipment) |
| `manage_equipment_submenu()` | 347 | `int(input("Ally: "))` | Raw input for ally selection |
| `manage_equipment_submenu()` | 354 | `int(input("Equip which? (0 cancel): "))` | Raw input for ally equip |
| `manage_equipment_submenu()` | 366 | `input("Which slot? (1/2): ").strip()` | Raw input for ally acc slot |
| `manage_equipment_submenu()` | 371 | `input("Press Enter...")` | Raw input after ally equip |
| `manage_equipment_submenu()` | 376 | `input("Press Enter...")` | Raw input (no allies for unequip) |
| `manage_equipment_submenu()` | 383 | `int(input("Ally: "))` | Raw input for ally unequip select |
| `manage_equipment_submenu()` | 393 | `input("Slot to unequip: ").strip().lower()` | Raw input for ally slot unequip |
| `manage_equipment_submenu()` | 400 | `input("Press Enter...")` | Raw input after ally unequip |
| `manage_bag_submenu()` | 413 | `input("Press Enter...")` | Raw input (empty bag) |
| `manage_bag_submenu()` | 432 | `input("Choice: ").strip().lower()` | Raw input for bag actions |
| `manage_bag_submenu()` | 435 | `int(input("Item number: "))` | Raw input for item use |
| `manage_bag_submenu()` | 442 | `input("Press Enter...")` | Raw input after using item |
| `manage_bag_submenu()` | 445 | `input("Press Enter...")` | Raw input (can't use equipment) |
| `manage_bag_submenu()` | 450 | `int(input("Drop which? "))` | Raw input for drop selection |
| `manage_bag_submenu()` | 455 | `input("Press Enter...")` | Raw input after drop |
| `prompt_acquire_item()` | 499 | `input("Choice: ").strip().lower()` | Raw input for acquire/discard |
| `display_active_bounties()` | 236–243 | `print(...)` (4 calls) | Raw print for bounties |
| `_display_player_skills()` | 130–155 | `print(...)` (10+ calls) | Raw print for skills |
| `_display_ally_skills()` | 158–230 | `print(...)` (15+ calls) | Raw print for ally skills |

**Total: ~25 raw `input()` calls, ~80+ raw `print()` calls**

---

### 3. `leveling.py` — **Level-up I/O uses raw `input()`/`print()`**

Called from `dungeon.explore_dungeon()` → `gain_exp()` / `gain_exp_ally()`.

| Function | Line(s) | Raw I/O Calls | Issue |
|----------|---------|---------------|-------|
| `gain_exp()` | 145–176 | `print(...)` (level up, milestone, skill unlock messages) | Raw print for level-up feedback |
| `gain_exp()` | 165 | `int(input("Enter number: ").strip())` | Raw input for attribute selection on level-up |
| `gain_exp_ally()` | 210–231 | `print(...)` (level up messages) | Raw print for ally level-up |
| `gain_exp_ally()` | 231 | `int(input("Enter number: ").strip())` | Raw input for ally attribute selection |
| `check_level_cap_milestone()` | 115–123 | `print(...)` (5 calls) | Raw print for milestone notification |

**Total: ~3 raw `input()` calls, ~15+ raw `print()` calls**

---

### 4. `inventory.py` — **One raw `print()` call in logic**

| Function | Line | Raw I/O | Issue |
|----------|------|---------|-------|
| `equip_item()` | 159 | `print(f"Cannot equip {item['name']} — inventory is full...")` | Raw print for error; called from GUI inventory screen |

---

### 5. `utils.py` — **Death handler and clear screen**

| Function | Line(s) | Raw I/O | Issue |
|----------|---------|---------|-------|
| `handle_player_death()` | 71–84 | `print(...)` (10+ calls) + `input("\n  Choice: ").strip().lower()` | Raw I/O for death menu; called from `main.py`→`play_game()` |
| `clear_screen()` | 90 | `os.system('cls' if os.name == 'nt' else 'clear')` | Terminal-specific; called everywhere (harmless no-op in GUI but unnecessary) |

---

## 🟡 PARTIALLY MIGRATED — Has bridges but raw fallbacks remain

---

### 6. `dungeon.py` — **Has `_tprint()`/`_tpause()`/`_tmenu()` bridges**

The `explore_dungeon()` function itself uses GUI bridges correctly. However:

| Location | Line(s) | Raw I/O | Notes |
|----------|---------|---------|-------|
| `_tmenu()` fallback | 59, 83 | `input(prompt)` | Only fires when `_term()` is None (terminal mode) — **OK** |
| Flee message (combat) | 547 | `input("Press Enter to continue...")` | Guarded by `if not _term()` — **OK** |
| Flee message (non-combat) | 587 | `input("Press Enter to continue...")` | Guarded by `if not _term()` — **OK** |
| Post-room menu (terminal) | 629 | `cmd = input().strip().lower()` | Guarded by `else` (terminal mode) — **OK** |

**Verdict: The bridges themselves are correctly guarded. The problem is that sub-modules  
(`dungeon_rooms.py`, `inventory_ui.py`, `leveling.py`) called from `explore_dungeon()`  
do NOT use these bridges.**

---

### 7. `events.py` — **Has tkinter detection**

| Function | Line(s) | Raw I/O | Notes |
|----------|---------|---------|-------|
| `flush_event_queue()` | 247 | `input("\nPress Enter to continue...")` | Has `tk._default_root` check before using raw input — **OK** |
| `display_event_alert()` | 234 | `print(...)` | Only called from terminal path — **OK** |

---

## 🟢 TERMINAL-ONLY PATH — Not in GUI execution, but not yet cleaned up

These files are only used when launching with `python launcher.py --terminal`.  
They work correctly in terminal mode but could be confusing during maintenance.

---

### 8. `main.py` — **Terminal-only entry point**

| Function | Raw I/O Calls |
|----------|---------------|
| `main_menu()` | ~16 `input()` calls, ~25 `print()` calls |
| `play_game()` | ~8 `input()` calls, ~15 `print()` calls |

**Status: Expected — this is the terminal-mode launcher invoked by `launcher.py --terminal`.**

---

### 9. `city.py` — **Terminal-only city loop**

| Function | Raw I/O Calls |
|----------|---------------|
| `visit_city()` | ~5 `input()` calls, ~25 `print()` calls |

**Status: The GUI has its own `gui/screens/city_screen.py`. `city.py`'s `visit_city()` is  
only called from `main.py` (terminal mode). However, `SERVICE_HANDLERS` dict is imported  
by the GUI city screen (data only, no I/O).**

---

### 10. `character.py` — **Terminal-only character creation**

| Function | Raw I/O Calls |
|----------|---------------|
| `allocate_points()` | ~3 `input()` calls, ~5 `print()` calls |
| `create_character()` | ~9 `input()` calls, ~10 `print()` calls |

**Status: The GUI has its own `gui/screens/char_create_screen.py`. The pure functions  
`build_character()` and `ensure_player_fields()` (no I/O) are safely imported by the GUI.**

---

### 11. `city_dialogue.py` — **Terminal-only dialogue printer**

| Function | Raw I/O Calls |
|----------|---------------|
| `service_dialogue()` | 2 `print()` calls |

**Status: Only imported by `city.py` (terminal-only). Not used by any GUI screen.**

---

## ✅ ALREADY MIGRATED — No raw I/O

---

### 12. `combat/*` — **All combat files use I/O abstraction**

| File | I/O Method |
|------|-----------|
| `combat/combat_io.py` | Defines `c_input()`/`c_print()`/`c_clear()` bridge |
| `combat/combat_engine.py` | Uses `c_input()`/`c_print()` exclusively |
| `combat/player_actions.py` | Uses `c_input()` exclusively |
| `combat/skills.py` | Uses `c_input()` exclusively |
| `combat/ally.py` | Uses `c_input()` exclusively |
| `combat/ally_skills.py` | Uses `c_input()` exclusively |
| `combat/capture.py` | Uses `c_input()` exclusively |
| `combat/combat_ui.py` | Uses `c_print()`/`c_input()`/`c_clear()` exclusively |
| `combat/action_menu.py` | No I/O (pure logic) |
| `combat/enemy_ai.py` | No I/O (pure logic) |
| `combat/helpers.py` | No I/O (pure logic) |
| `combat/superboss_common.py` | Uses `c_input()` exclusively |
| `combat/abyss_fang.py` | Uses `c_input()` exclusively |
| `combat/broodmother.py` | Uses `c_input()` exclusively |
| `combat/captain_cutlass.py` | Uses `c_input()` exclusively |
| `combat/everlong_ship.py` | Uses `c_input()` exclusively |
| `combat/ignis.py` | Uses `c_input()` exclusively |
| `combat/rientrante.py` | Uses `c_input()` exclusively |
| `combat/slitcurrent.py` | Uses `c_input()` exclusively |
| `combat/sylvana.py` | Uses `c_input()` exclusively |
| `combat/yinglong.py` | Uses `c_input()` exclusively |
| `combat/wedding_specials.py` | No I/O (pure logic) |
| `combat/status_effects.py` | No I/O (pure logic) |
| `combat/stat_milestones.py` | No I/O (pure logic) |
| `combat/stats.py` | No I/O (pure logic) |
| `combat/elemental.py` | No I/O (pure logic) |

---

### 13. `facilities/*` — **All facility files use `term` abstraction**

| File | I/O Method |
|------|-----------|
| `facilities/arcane_tower.py` | `from gui.terminal import term` → `term.print()`/`term.menu()` |
| `facilities/barracks.py` | `from gui.terminal import term` |
| `facilities/black_market.py` | `from gui.terminal import term` |
| `facilities/blacksmith.py` | `from gui.terminal import term` |
| `facilities/gift_shop.py` | `from gui.terminal import term` |
| `facilities/guild.py` | `from gui.terminal import term` |
| `facilities/herbalist.py` | `from gui.terminal import term` |
| `facilities/house.py` | `from gui.terminal import term` |
| `facilities/inn.py` | `from gui.terminal import term` |
| `facilities/port.py` | `from gui.terminal import term` |
| `facilities/shipyard.py` | `from gui.terminal import term` |
| `facilities/shop.py` | `from gui.terminal import term` |
| `facilities/skill_book.py` | `from gui.terminal import term` |
| `facilities/temple.py` | `from gui.terminal import term` |
| `facilities/trade_hall.py` | `from gui.terminal import term` |
| `facilities/travel.py` | `from gui.terminal import term` |
| `facilities/travel_events.py` | `from gui.terminal import term` |

---

### 14. `gui/*` — **These ARE the new I/O system**

All files in `gui/` directory are the new GUI implementation.

---

## 📊 Summary Statistics

| Category | Files | Raw `input()` calls | Raw `print()` calls | `os.system('cls')` |
|----------|-------|---------------------|---------------------|-------------------|
| 🔴 Critical (GUI path) | 5 | ~45 | ~210+ | 0 |
| 🟡 Partial (bridged) | 2 | ~4 (guarded) | ~2 | 0 |
| 🟢 Terminal-only | 4 | ~38 | ~75 | 1 |
| ✅ Migrated | 33 | 0 | 0 | 0 |

---

## 🔧 Recommended Migration Priority

1. **`dungeon_rooms.py`** — Highest priority. These room handlers are the core dungeon  
   gameplay loop. Every room type needs `_tprint()`/`_tpause()`/`_tmenu()` wrappers  
   (following the pattern already in `dungeon.py`).

2. **`inventory_ui.py`** — Second priority. Called from the post-room menu in dungeons  
   and from city services. The GUI already has `gui/screens/inventory_screen.py` but  
   the dungeon post-room flow still calls the terminal version.

3. **`leveling.py`** — Third priority. Level-up attribute selection needs a GUI dialog.  
   The level-up messages could use `_tprint()` from `dungeon.py`.

4. **`utils.py`** — `handle_player_death()` needs a GUI death screen (the GUI already  
   has `gui/screens/death_screen.py` — ensure it's used instead). `clear_screen()` is  
   harmless but should be a no-op in GUI mode.

5. **`inventory.py`** — Single `print()` statement on line 159. Minor fix — either  
   raise an exception or return an error string.
