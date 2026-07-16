# Dungeon Systems & GUI Migration

## Wonderland (50 Floors)
- **Quirks:** Beneficial whimsical effects, 4 tiers. Applied per floor.
- **Floor Bosses:** F2–F48 even floors.
- **Shadows:** F40+ persist through floors and feed into Mary Sue fight.
- **Mary Sue (F50):** 5-phase boss fight.
  - Plot Armor: 8 damage types, each strips one stack max per hit.
  - Shadow Gauntlet mechanic.

## Pandemonium (40 Floors)
- **Stat Multiplier:** 1.7× enemy stats globally.
- **Curses:** 10 curse types, applied per floor.
- **Corruption Tiers:** 1.0× → 2.5× scaling.
- **Chrysalis (F20):** 3 Temporal Aspects, Paradox Fracture mechanic.
  - Set HP via `enemy["hp"] = new_value` for Paradox Fracture to apply correctly.

## Superboss Tier System
- **7 tiers** `[0..6]`, shuffled per floor.
- Wonderland has its own schedule (F10=QoH, F20=Wolf, F30=Witch, F40=Jabberwock, F50=MarySue).
- Pandemonium F20=Chrysalis.
- Abyss Fang: Multi-phase superboss with Abyssal Tempo stacking mechanic. State tracked in player fields, cleared via `clear_abyss_fang_state()`.
- Captain Cutlass: High Tide stacks, Rally, Riposte counters. 5 persistent player state fields.
- Use `superboss_common.py` for shared combat loop, buff ticking, and ally cooldown management.

## Wonderland Boss Schedule
| Floor | Boss | File |
|---|---|---|
| F10 | Queen of Hearts | `./combat/queen_of_hearts.py` |
| F20 | Wolf | `./combat/wl_floor_bosses.py` |
| F30 | Wicked Witch | `./combat/wicked_witch.py` |
| F40 | Jabberwock | `./combat/jabberwock.py` |
| F50 | Mary Sue | `./combat/mary_sue.py` |

## Dungeon Rooms
- 10 rooms/floor, 10% non-combat chance.
- Non-combat rooms: fountain, merchant, trap, treasure, stat-check.
- Mid-floor progress saved between rooms.

## GUI Migration Status
- **Phases 0–2:** Complete
- **Phase 3:** In progress
- **Phase 4:** In progress
- **Architecture:** Screen-based (`BaseScreen` → subclasses), `ScreenManager` with back-stack.
- **Theme:** Dark theme (`#1a1a2e` bg, `#e94560` accent), monospace font mandatory.
- **Save Format:** JSON save files in `./savefile/`.
- **Facility I/O:** Via `./gui/terminal.py` bridge.
- **Widgets:** Under `./gui/widgets/` — `city_map`, `confirm_dialog`, `hp_bar`, `item_card`, `log_window`, `notification_toast`, `stat_display`.
- **Combat Rendering:** ASCII combat HUD in tkinter text widget via `./gui/combat/combat_renderer.py`. Action buttons via `./gui/combat/action_panel.py`.
- **Launcher:** `./launcher.py` is the PyInstaller entry point; sets up thread exception hooks, calls `gui.app.run_gui()`.
