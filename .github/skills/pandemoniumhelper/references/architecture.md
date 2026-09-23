# Architecture Reference

## Entry Points

| File | Role |
|---|---|
| `./launcher.py` | **Entry point** (PyInstaller target). Sets up threading exception hook, calls `gui.app.run_gui()`. |
| `./Pandemonium.spec` | PyInstaller build spec for GUI executable. |
| `./make_exe.py` | PyInstaller build script. |

## Core Files

| File | Role |
|---|---|
| `./character.py` | Creation, `ensure_player_fields()`, `player_max_hp()` |
| `./leveling.py` | XP, level-up rewards |
| `./dungeon.py` | Dungeon crawl, floor gen, combat triggers, superboss milestones |
| `./inventory.py` / `./inventory_ui.py` | Inventory & equipment |
| `./save_load.py` | Save/load |
| `./city.py` / `./city_dialogue.py` | City hub, NPC dialogue |
| `./events.py` | Date-based event system, time tracking |
| `./utils.py` | `_tprint`/`_tpause`/`_tinput`, `advance_time()`, `apply_death_penalty()`, `handle_player_death()`, `clear_screen()`, `format_time()`, `get_time_period()`, `get_difficulty_multiplier_from_time()`, `strip_ansi()` |

## Combat Module

| File | Role |
|---|---|
| `./combat/combat_engine.py` | Combat loop, initiative, turn order |
| `./combat/combat_ui.py` | ASCII combat HUD (68-char width, 2-row entity layout) |
| `./combat/player_actions.py` | Player turn: attack, skills, items, flee, capture |
| `./combat/ally.py` | Ally creation, turn actions |
| `./combat/skills.py` | Class skills: definitions, cooldowns, mastery |
| `./combat/ally_skills.py` | Ally innate/learnable skill execution |
| `./combat/superboss_common.py` | Shared superboss combat loop |
| `./combat/capture.py` | Monster-girl capture |
| `./combat/stats.py` | Effective stats (base+eq+buffs), 1.7× Pandemonium multiplier |
| `./combat/status_effects.py` | Poison, burn, bleed, curse, dread, silence, fear, etc. |
| `./combat/stat_milestones.py` | Every 5 base-attr: STR→+dmg, CON→-dmg, DEX→dodge%, WIS→init/flee+heal%, CHA→capture%, LRN→skill% |
| `./combat/elemental.py` | 8-element damage/resist system |
| `./combat/enemy_ai.py` | Enemy attacks, mitigation (def buffs, divine shield, dodge, passives) |
| `./combat/combat_io.py` | Thread-safe I/O: `c_print`/`c_input`/`c_clear` |
| `./combat/action_menu.py` | Conditional action menus (ally menus differ from player) |
| `./combat/wedding_specials.py` | Bonded effects, soulbound, post-combat rewards |
| `./combat/elemental_debuffs.py` | Elemental debuff application: `try_apply_elemental_debuff()`, proc chance calc |
| `./combat/elemental_traits.py` | Weapon elemental traits: `get_primary_element()`, `apply_trait()`, on-kill procs |
| `./combat/helpers.py` | Formatting helpers: `format_damage_msg()`, `_player_has_tarnished_jade()` |
| `./combat/vileheart_venom.py` | Vileheart Venom pendant proc system |

## Superboss Files

| File | Boss |
|---|---|
| `./combat/abyss_fang.py` | Abyss Fang (multi-phase superboss), Abyssal Tempo stacks |
| `./combat/black_silence.py` | Black Silence |
| `./combat/black_silence_gloves.py` | Black Silence Gloves |
| `./combat/broodmother.py` | Broodmother |
| `./combat/captain_cutlass.py` | Captain Cutlass (high tide, rally, riposte) |
| `./combat/entangled_chrysalis.py` | Entangled Chrysalis (Pandemonium F20, 3 Temporal Aspects, Paradox Fracture) |
| `./combat/everlong_ship.py` | Everlong Ship |
| `./combat/ignis.py` | Ignis |
| `./combat/jabberwock.py` | Jabberwock (Wonderland F40) |
| `./combat/mary_sue.py` / `./combat/mary_sue_shadows.py` | Mary Sue (Wonderland F50, 5-phase, Plot Armor) |
| `./combat/queen_of_hearts.py` | Queen of Hearts (Wonderland F10) |
| `./combat/rientrante.py` | Rientrante |
| `./combat/slitcurrent.py` | Slitcurrent |
| `./combat/sylvana.py` | Sylvana |
| `./combat/tarnished_jade.py` | Tarnished Jade |
| `./combat/wicked_witch.py` | Wicked Witch (Wonderland F30) |
| `./combat/wl_floor_bosses.py` | Wonderland floor bosses |
| `./combat/yinglong.py` | Yinglong |
| `./combat/dummy.py` | Training dummy |

## Non-Combat

| File | Role |
|---|---|
| `./dungeon_rooms.py` | Non-combat rooms: fountain, merchant, trap, treasure, stat-check (10% chance) |
| `./pandemonium_curses.py` | Pandemonium curses: 10 types, 4 corruption tiers (1.0×–2.5×) |
| `./wonderland_curses.py` | Wonderland quirks + Shadow system (Floor 40+) |

## Facilities

| File | Role |
|---|---|
| `./facilities/house.py` | Monster girl housing, affection, recruitment |
| `./facilities/shop.py` | Item shop |
| `./facilities/inn.py` | Rest/HP recovery |
| `./facilities/blacksmith.py` | Equipment crafting/upgrading |
| `./facilities/temple.py` | Blessings, curse removal |
| `./facilities/guild.py` | Level cap increases, biome clearing |
| `./facilities/barracks.py` | Ally skill training (`learning` dict) |
| `./facilities/gift_shop.py` | Gifts, wedding rings |
| `./facilities/travel.py` / `./facilities/travel_events.py` | World travel + events |
| `./facilities/arcane_tower.py` | Arcane tower facility |
| `./facilities/black_market.py` | Black market |
| `./facilities/herbalist.py` | Herbalist |
| `./facilities/port.py` | Port facility |
| `./facilities/shipyard.py` | Shipyard |
| `./facilities/skill_book.py` | Skill book management |
| `./facilities/trade_hall.py` | Trading |
| `./facilities/pathfinding.py` | Pathfinding utility |

## Resources

### Top-Level Data Files
| File | Role |
|---|---|
| `./resources/__init__.py` | Package init |
| `./resources/cities.py` | City definitions/data |
| `./resources/city_maps.py` | City map layouts |
| `./resources/constants.py` | Game constants |
| `./resources/items.py` | Item definitions |
| `./resources/mounts.py` | Mount definitions |
| `./resources/races_classes.py` | Race/class data (RACES, CLASSES, ATTRIBUTES) |
| `./resources/skill_loader.py` | Skill loading from YAML |

### Enemy Data (`./resources/enemies/`)
| File | Role |
|---|---|
| `./resources/enemies/enemy_loader.py` | YAML enemy loading (old `enemies.py` removed) |
| `./resources/enemies/biome_races.py` | Biome-to-enemy-race mappings |
| `./resources/enemies/enemy_races.py` | Enemy race definitions |
| `./resources/enemies/enemies_data/` | 24 YAML files: `all_enemies.yaml`, `monster_girls.yaml`, `superbosses.yaml`, `wonderland.yaml`, + per-race files |

### Dialogues (`./resources/dialogues/`)
21 city dialogue files: `ashkara.py`, `blackwake.py`, `brinewatch.py`, `cinderpeak.py`, `coralhaven.py`, `dunemar.py`, `elderfen.py`, `greyharbor.py`, `irondeep.py`, `isle_of_glass.py`, `mirefall.py`, `saltmarsh.py`, `skylume.py`, `solmere.py`, `stormhold.py`, `sunreach.py`, `thornwall.py`, `tidebreak.py`, `veilholt.py`, `wonderland.py`

### Skill Book (`./resources/skill_book/`)
| File | Role |
|---|---|
| `./resources/skill_book/innate_skills.yaml` | Innate ally/monster-girl skill definitions |
| `./resources/skill_book/skill_list.yaml` | Master skill list with race passives |

## GUI Module

### Core GUI
| File | Role |
|---|---|
| `./gui/__init__.py` | Package init |
| `./gui/app.py` | tkinter main window, `PandemoniumApp`, `run_gui()` entry |
| `./gui/theme.py` | Dark theme: bg `#1a1a2e`, accent `#e94560`, monospace |
| `./gui/screen_manager.py` | Screen router, back-stack, game clock (1min/2s), top/bottom bars |
| `./gui/terminal.py` | Thread-safe facility I/O bridge |
| `./gui/io_redirector.py` | stdout/stderr redirect for tkinter |
| `./gui/notification_queue.py` | Notification queuing system |
| `./gui/settings.py` | GUI settings management |

### GUI Screens (`./gui/screens/`)
| File | Role |
|---|---|
| `base_screen.py` | Base screen class for all screens |
| `changelog_screen.py` | Changelog display |
| `char_create_screen.py` | Character creation screen |
| `city_screen.py` | City hub screen |
| `combat_screen.py` | Combat UI screen |
| `death_screen.py` | Death/game-over screen |
| `dungeon_screen.py` | Dungeon crawl screen |
| `facility_screen.py` | Facility interaction screen |
| `inventory_screen.py` | Inventory/equipment screen |
| `main_menu_screen.py` | Main menu screen |
| `post_floor_screen.py` | Post-floor rewards/choices |
| `settings_screen.py` | Settings screen |
| `splash_screen.py` | Splash/loading screen |
| `world_map_screen.py` | Unified world map / travel hub |

### GUI Widgets (`./gui/widgets/`)
| File | Role |
|---|---|
| `city_map.py` | City map widget |
| `confirm_dialog.py` | Confirmation dialog |
| `hp_bar.py` | HP bar display |
| `item_card.py` | Item card display |
| `log_window.py` | Log/message window |
| `notification_toast.py` | Toast notifications |
| `stat_display.py` | Stats display panel |

### GUI Combat (`./gui/combat/`)
| File | Role |
|---|---|
| `combat_renderer.py` | ASCII combat HUD in tkinter text widget |
| `action_panel.py` | Action button panel for combat |

### Savefile (`./savefile/`)
| File | Role |
|---|---|
| `gui_settings.json` | GUI settings persistence |
| `savegame_1.json` through `savegame_4.json` | Player save slots |

## Tests

| File | Role |
|---|---|
| `./tests/test_health_checks.py` | Health/sanity checks |
| `./tests/test_phase0.py` | Phase 0 validation |
| `./tests/test_phase1.py` | Phase 1 validation |
| `./tests/test_phase2.py` | Phase 2 validation |
| `./tests/test_phase3.py` | Phase 3 validation |
| `./tests/test_phase4.py` | Phase 4 validation |
| `./tests/test_phase19.py` | Phase 19 validation |

## Dev Utilities

| File | Role |
|---|---|
| `./clean_pycache.ps1` | Clear Python bytecode cache |
| `./verify_phase2.py` | Phase 2 verification/QA script |
| `./result.txt` | Output/log artifact |
