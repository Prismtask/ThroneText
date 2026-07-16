---
name: pandemoniumhelper
description: 'Iterative development helper for the Pandemonium Python text-based RPG. Use when: user mentions "Pandemonium", references files under this workspace, or asks about game features, combat, dungeons, GUI, or facilities. Covers architecture, UI conventions, and development workflows so the agent does not re-explore the codebase.'
---

# Pandemonium Development Helper

## Project Context
- **Path:** `./` (workspace root) | **Language:** Python 3 (tkinter GUI) | **Entry:** `./launcher.py`
- **Virtual env:** `./.venv` (no global packages)
- **Build:** `./make_exe.py` / `./Pandemonium.spec` (PyInstaller)

## When to Use
- Any task touching Pandemonium code (combat, dungeons, GUI, facilities, inventory, saves)
- User mentions game features, superbosses, monster girls, allies, skills, or items
- Adding new systems, enemies, or GUI screens
- Debugging combat, UI, threading, or save/load issues

## Core Workflow
1. **Jump to known file paths** — use the [architecture reference](./references/architecture.md) instead of re-exploring.
2. **Read player + ally files** if touching UI or stats display.
3. **New persistent fields** → patch `./character.py` `ensure_player_fields()` with `.setdefault()`.
4. **Verify** with `./.venv` interpreter.
5. **Allies can't** use Abyss Fang, Cutlass, capture, or player class skills.
6. **New superboss** → `./combat/<name>.py` + YAML entry + import in `./dungeon.py` + tier pool.
7. **End-of-combat**: `end_of_combat_cleanup()` must run on victory/flee/death to tick cooldowns, decrement buffs, clear weapon states. Must also call `clear_abyss_fang_state()` and `clear_captain_cutlass_state()`.

## Key Conventions (compact)

### Entry & Build
- **Launcher:** `./launcher.py` — sets up `threading.excepthook`, calls `gui.app.run_gui()`. PyInstaller target.

### UI & Display
- Player & ally displays must match identically (headers, stats, rarity).
- Combat HUD: fixed 68-char ASCII box. Party left (31 chars), enemies right (33 chars). 2 rows/entity.
- Stat display: `Attribute: base + N(eq) + N(buff) = total`
- Monster girls: ♀ symbol. Captured via nets → `./facilities/house.py`.

### Combat
- Max 1 player + 3 allies vs 5 enemies. Player controls all ally actions.
- Skills: class-based, unlock at levels, cooldowns in `player["skill_cooldowns"]`. Damage scales with primary attribute + Learning.
- HP calc: Player uses `player_max_hp(player)`, allies use `ally["max_hp"]`. Mixed lists must branch.
- Ally defending: Reset `defending_this_turn = False` at start of every ally turn.
- Ally cooldowns: `superboss_common.py` must tick ally cooldowns too.
- Superboss hooks: Signature `enemy_turn_hook(enemy, ctx, pl, p_con, defending)` must match across all modules.

### Elemental System
- 8 elements: Fire, Water, Ice, Lightning, Wind, Earth, Light, Dark.
- `./combat/elemental.py` — damage/resist calculation.
- `./combat/elemental_debuffs.py` — `try_apply_elemental_debuff()` procs on hit; chance scales with attack stat.
- `./combat/elemental_traits.py` — weapon primary element, trait application, on-kill procs.
- `./combat/vileheart_venom.py` — Vileheart Venom pendant proc system.

### Superboss State Management
- **Abyss Fang:** Abyssal Tempo stacks tick at round start (`tick_abyssal_tempo()`). State cleared via `clear_abyss_fang_state()`.
- **Captain Cutlass:** 5 persistent player fields (`cutlass_high_tide_stacks`, `cutlass_rally_cooldown`, `cutlass_riposte_count`, etc.). Cleared via `clear_captain_cutlass_state()`.
- **Chrysalis:** Set HP via `enemy["hp"] = new_value` for Paradox Fracture. 3 Temporal Aspects.

### Player Systems
- **Engagement/Wedding:** 100 affection → propose with ring → cap 200 → Legendary soulbound accessory at 200. Fields: `engaged_girls`, `married_girls`.
- **Mounts:** `player["mount_id"]` — travel speed + combat passives.
- **Potion sickness:** `player["potion_sickness"]` — turns of consumable cooldown.
- **Daily limits:** `girl_talk_today`, `girl_gift_today`, `girl_daily_last_day`.
- **Time-of-day:** `get_time_period()` + `get_difficulty_multiplier_from_time()` (1.0×–1.8×, night harder).
- **Elemental profiles:** `player["elemental_res"]` / `player["elemental_dmg"]` — per-element dicts.
- **Party order:** `player["party_order"]` — front/back row positioning.

### GUI Screens (16 screens in `./gui/screens/`)
`base_screen`, `changelog_screen`, `char_create_screen`, `city_screen`, `combat_screen`, `death_screen`, `dungeon_screen`, `facility_screen`, `inventory_screen`, `main_menu_screen`, `post_floor_screen`, `settings_screen`, `splash_screen`, `travel_screen`, `world_map_screen`

### GUI Widgets (7 widgets in `./gui/widgets/`)
`city_map`, `confirm_dialog`, `hp_bar`, `item_card`, `log_window`, `notification_toast`, `stat_display`

### Thread Safety (GUI)
- GUI runs facilities/combat in background threads.
- Use `_tprint`/`_tpause`/`_tinput` (from `./utils.py`) or `c_print`/`c_input` (from `./combat/combat_io.py`).
- **Never** raw `print()`/`input()`. **Never** tkinter from background thread → use `after()` or I/O queues.

## Reference Files
- [Architecture (key files and roles)](./references/architecture.md) — complete file/directory map
- [Full Conventions & Common Pitfalls](./references/conventions.md) — all rules + gotchas
- [Dungeon Systems & GUI Migration Status](./references/dungeon-systems.md) — dungeon mechanics, boss schedule, GUI progress
