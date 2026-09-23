# Pandemonium Code Healthcheck Report

**Date:** 2026-07-28  
**Audited:** 75+ Python files across `./`, `combat/`, `facilities/`, `gui/`  
**Findings:** 87 issues across 6 categories

---

## 🔴 CRITICAL: Bug Found

| # | File | Line | Issue |
|---|------|------|-------|
| 1 | `wonderland_curses.py` | ~795 | `get_heroine_shadow_floor50_dialogue()` references `HEROINE_SHADOW_FLOOR50_DIALOGUE` — **this dict was never defined**. The function will throw `NameError` at runtime. |

---

## 🔴 HIGH: Duplicate Function Definitions (20 instances)

### Cross-Module Duplicates

| # | Function | Defined In | Copies |
|---|----------|-----------|:------:|
| 2 | `_tprint` / `_tpause` / `_tclear` / `_tmenu` / `_tinput` | `leveling.py`, `dungeon.py`, `dungeon_rooms.py`, `inventory.py`, `inventory_ui.py`, `utils.py` | **6** |
| 3 | `_get_wonderland_max_floor` | `facilities/arcane_tower.py`, `facilities/black_market.py`, `facilities/temple.py` | **3** |
| 4 | `_int_to_roman` | `facilities/temple.py`, `facilities/house.py` | **2** |
| 5 | `get_effective_charisma` | `facilities/blacksmith.py`, `facilities/shop.py` | **2** |
| 6 | `get_discounted_price` / `get_discounted_blacksmith_price` | `facilities/shop.py`, `facilities/blacksmith.py` | **2** *(identical bodies, different names)* |
| 7 | `_sell_price` | `facilities/shop.py`, `facilities/travel_events.py` | **2** *(**reversed parameter order** — bug risk!)* |
| 8 | `_danger_tag` | `facilities/travel.py`, `facilities/port.py` | **2** *(different thresholds, same concept)* |

### Combat Module Duplicates

| # | Function | Defined In | Copies |
|---|----------|-----------|:------:|
| 9 | `prune_dead` | `combat/combat_engine.py`, `combat/superboss_common.py` | **2** |
| 10 | `roll_initiative` | `combat/combat_engine.py`, `combat/superboss_common.py` | **2** *(superboss version is stripped-down — missing Wisdom milestone, curses, Haste)* |
| 11 | `_get_alive_party` | `combat/combat_engine.py`, `combat/broodmother.py`, `combat/big_bad_wolf.py`, `combat/entangled_chrysalis.py` | **4** |
| 12 | `_player_has_tarnished_jade` | `combat/helpers.py`, `combat/tarnished_jade.py` | **2** |
| 13 | `_player_has_black_silence_gloves` | `combat/action_menu.py`, `combat/black_silence_gloves.py` | **2** |
| 14 | `_get_boss` pattern | `combat/broodmother.py`, `combat/black_silence.py`, `combat/entangled_chrysalis.py` | **3** *(only `BOSS_KEY` differs)* |
| 15 | `ELEMENT_TAGS` / `elemental_tags` | `combat/helpers.py`, `combat/enemy_ai.py` | **2** |

### GUI Duplicates

| # | Function | Defined In | Copies |
|---|----------|-----------|:------:|
| 16 | `_update_top_bar` | `gui/screens/city_screen.py`, `combat_screen.py`, `dungeon_screen.py`, `facility_screen.py`, `world_map_screen.py` | **5** |
| 17 | `_build_wonderland_cheshire` | `gui/screens/world_map_screen.py` | **1** *(deduped — `travel_screen.py` removed)* |
| 18 | `styled_button` | `gui/screens/base_screen.py`, `gui/widgets/log_window.py` | **2** |

---

## 🟡 MEDIUM: Dead Code & Unused Functions

| # | File | Line | Function | Notes |
|---|------|------|----------|-------|
| 19 | `leveling.py` | 145 | `get_city_dungeon_progress()` | Never called anywhere |
| 20 | `leveling.py` | 186 | `get_incomplete_biomes()` | Never called anywhere |
| 21 | `inventory.py` | 137 | `consume_stackable_items()` | Never called anywhere |
| 22 | `inventory.py` | 213 | `get_total_equipment_mods()` | Never called anywhere |
| 23 | `pandemonium_curses.py` | 246 | `format_curse_header()` | Never called anywhere |
| 24 | `wonderland_curses.py` | 793 | `get_heroine_shadow_floor50_dialogue()` | Never called + **bug** (references undefined dict) |
| 25 | `combat/abyss_fang.py` | 16 | `_player_has_abyss_fang()` | Never called (only `_actor_has_abyss_fang` is used) |
| 26 | `combat/tarnished_jade.py` | 15 | `_player_has_tarnished_jade()` | Only called internally; external callers use `helpers.py` copy |
| 27 | `gui/widgets/item_card.py` | — | Entire `ItemCard` class | Never imported or used anywhere |
| 28 | `gui/widgets/stat_display.py` | — | Entire `StatDisplay` class | Never imported or used anywhere |
| 29 | `gui/screens/facilities/` | — | Empty directory | Contains only `__pycache__`, no Python files |
| 30 | `utils.py` | 80 | `handle_player_death()` | Terminal-mode wrapper, likely dead since GUI migration |
| 31 | `main.py` | — | Entire file | Stub — just prints deprecation message pointing to `launcher.py` |

---

## 🟡 MEDIUM: Unused Imports (25 instances)

### `c_clear` imported but never called (9 files)

| # | File |
|---|------|
| 32 | `combat/abyss_fang.py` |
| 33 | `combat/ally_skills.py` |
| 34 | `combat/capture.py` |
| 35 | `combat/skills.py` |
| 36 | `combat/enemy_ai.py` |
| 37 | `combat/broodmother.py` |
| 38 | `combat/ignis.py` |
| 39 | `combat/slitcurrent.py` |
| 40 | `combat/captain_cutlass.py` |

### `clear_screen` imported but never called (7 files)

All use `term.clear()` instead of `clear_screen()`.

| # | File |
|---|------|
| 41 | `facilities/blacksmith.py` |
| 42 | `facilities/guild.py` |
| 43 | `facilities/house.py` |
| 44 | `facilities/inn.py` |
| 45 | `facilities/shop.py` |
| 46 | `facilities/skill_book.py` |
| 47 | `facilities/temple.py` |

### Other Unused Imports

| # | File | Unused Import |
|---|------|---------------|
| 48 | `facilities/temple.py` | `import random` |
| 49 | `facilities/shop.py` | `get_total_equipment_mods` from `inventory` |
| 50 | `facilities/skill_book.py` | `player_max_hp` from `character` |
| 51 | `combat/action_menu.py` | `is_monster_girl` from `capture` |
| 52 | `combat/dummy.py` | `get_io`, `TerminalIO` from `combat_io` |
| 53 | `combat/ignis.py` | `superboss_triple_action_loop` |
| 54 | `combat/slitcurrent.py` | `superboss_triple_action_loop` |
| 55 | `combat/sylvana.py` | `superboss_triple_action_loop` |
| 56 | `gui/screens/main_menu_screen.py` | `from tkinter import ttk` |
| 57 | `gui/screens/facility_screen.py` | `from tkinter import scrolledtext` |
| 58 | `gui/screens/city_screen.py` | `service_dialogue` from `city_dialogue` |

---

## 🟡 MEDIUM: Repeated Code Patterns (DRY Violations)

### Patterns in Dungeon (`dungeon.py`)

| # | Pattern | Occurrences | Recommendation |
|---|---------|:-----------:|----------------|
| 59 | "Clear Wonderland state" block (`clear_wonderland_quirk` + `clear_all_shadows`) | **8** | Extract to `_cleanup_wonderland(player)` |
| 60 | "Reset High Tide" block (`cutlass_high_tide_stacks = 0` + `pop cutlass_high_tide_floor`) | **7** | Extract to `_reset_high_tide(player)` |
| 61 | Wonderland floor→flag mapping (module-level dict + 2 inline copies) | **3** | Use a single `_WL_SUPERBOSS_FLAG_MAP` |
| 62 | "Advance floor progress" block | **3** | Extract to `_advance_floor_progress(player, ...)` |
| 63 | Superboss reward calculation (XP + gold + scaling + ally XP) | **3** | Extract to `_award_superboss_rewards(player, floor)` |

### Patterns in Leveling (`leveling.py`)

| # | Pattern | Occurrences | Recommendation |
|---|---------|:-----------:|----------------|
| 64 | `gain_exp()` vs `gain_exp_ally()` — 80% identical logic | **2** | Unify into `_gain_exp_for_entity(entity, amount, ...)` |

### Patterns in Facilities

| # | Pattern | Occurrences | Recommendation |
|---|---------|:-----------:|----------------|
| 65 | "Heal player + all allies" block in `inn.py` and `house.py` | **6** | Extract to `_heal_full_party(player)` |
| 66 | Numeric item selection parser (`"1 3 5"`, `"1-4"`, `"all"`) in `house.py`, `shop.py` | **3** | Extract to `parse_item_selection(raw, max) -> list[int]` |
| 67 | "Build enhanceable pool" in `blacksmith.py` | **2** | Extract to `_build_enhanceable_pool(player)` |
| 68 | "Check for item in inventory" pattern in `arcane_tower.py`, `black_market.py`, `temple.py`, `inn.py` | **15+** | Use a `has_item(player, item_id)` helper in `inventory.py` |
| 69 | "Remove item by ID" pattern in `arcane_tower.py`, `black_market.py`, `temple.py` | **3** | Create `remove_item_by_id(player, item_id)` in `inventory.py` |

### Patterns in Combat

| # | Pattern | Occurrences | Recommendation |
|---|---------|:-----------:|----------------|
| 70 | `_actor_has_*` equipment-check boilerplate (`abyss_fang.py`, `authors_pen.py`, `black_silence_gloves.py`, `captain_cutlass.py`, `tarnished_jade.py`, `vileheart_venom.py`) | **6** | Generic `_actor_has_item(actor, slot, field, value)` in `helpers.py` |
| 71 | `_spawn_*` minion creation boilerplate (`broodmother.py`, `everlong_ship.py`, `jabberwock.py`, `queen_of_hearts.py`, `rientrante.py`, `wicked_witch.py`) | **6** | `spawn_minion(player, key, count=1)` factory in `superboss_common.py` |
| 72 | Boss file initialization boilerplate (check enemies, find/create boss, set max_hp, intro, context, hooks) | **14** | Shared initialization in `superboss_common.py` |

### Patterns in GUI

| # | Pattern | Occurrences | Recommendation |
|---|---------|:-----------:|----------------|
| 73 | Canvas+Scrollbar+Inner Frame boilerplate (`facility_screen.py`, `dungeon_screen.py`, `inventory_screen.py`) | **7+** | Create `ScrollableFrame` widget in `gui/widgets/` |
| 74 | City/time top-bar formatting across 5+ screens | **5+** | Standardize via `ScreenManager.refresh_top_bar()` |
| 75 | Race/Class card selection grid in `char_create_screen.py` | **2** | Extract `_build_card_grid(items_dict, selected_key, on_select)` |
| 76 | "Back to City" button creation | **4+** | Shared `_make_back_to_city_button()` method |

### Patterns in Inventory

| # | Pattern | Occurrences | Recommendation |
|---|---------|:-----------:|----------------|
| 77 | Elemental recalculation after equip/unequip (`inventory.py`) | **2** | Extract to `_recalc_elemental(player)` |
| 78 | `RARITY_ORDER` dict vs `_RARITY_TIER` list — redundant encoding of same ordering | **2** | Derive one from the other |

---

## 📊 Summary Statistics

| Severity | Category | Count |
|----------|----------|:-----:|
| 🔴 | Critical (runtime bug) | 1 |
| 🔴 | Duplicate function definitions | 20 |
| 🟡 | Dead code / unused functions | 13 |
| 🟡 | Unused imports | 27 |
| 🟡 | Repeated code patterns (DRY) | 20 |
| **Total** | | **87** |

---

## 🏆 Top 10 Most Impactful Fixes

| # | Fix | Impact |
|:-:|------|--------|
| 1 | **Fix `HEROINE_SHADOW_FLOOR50_DIALOGUE` missing dict** in `wonderland_curses.py` | Prevents `NameError` crash at runtime |
| 2 | **Centralize `_tprint`/`_tpause`/`_tclear`/`_tmenu`/`_tinput`** into `utils.py` | Eliminates 6 copy-pasted copies (~200 lines) |
| 3 | **Create `ScrollableFrame` widget** in `gui/widgets/` | Eliminates 8+ canvas+scrollbar boilerplate blocks (~200 lines) |
| 4 | **Extract repeated dungeon cleanup helpers** in `dungeon.py` | Eliminates 8× wonderland cleanup, 7× high tide reset, 3× floor advance |
| 5 | **Unify `_update_top_bar`** across 6 GUI screens | Eliminates 5 of 6 near-identical methods |
| 6 | **Create `spawn_minion()` factory** in `superboss_common.py` | Eliminates 6 `_spawn_*` functions |
| 7 | **Unify `_actor_has_*` into `_actor_has_item(actor, slot, field, value)`** in `helpers.py` | Eliminates 6 near-identical functions + their `_player_has_*` wrappers |
| 8 | **Extract `_get_wonderland_max_floor`**, `_int_to_roman`, `get_effective_charisma` to `utils.py` | Eliminates 7 duplicate definitions |
| 9 | **Remove 27 unused imports** | Cleaner code, faster module loading |
| 10 | **Remove dead code**: 7 dead functions + 2 dead widgets + empty directory + stub `main.py` | Reduces maintenance burden |

---

## Notes

- The codebase is **well-structured** overall with clear module boundaries and consistent naming conventions.
- The primary source of redundancy is **copy-paste across modules** — many helper functions were copied rather than imported from a shared location.
- The **superboss files** in `combat/` share a large amount of boilerplate (~30-50 lines each × 14 bosses) that could be refactored into `superboss_common.py`.
- The **GUI migration** left behind some terminal-mode artifacts (`handle_player_death()`, `main.py` stub, `clear_screen` imports) that could be cleaned up now that the terminal mode is retired.
