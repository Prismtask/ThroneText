---
name: pandemonium
description: |
  Iterative development helper for the Pandemonium Python text-based game.
  Use when the user mentions "Pandemonium", references files under `C:\Code\Pandemonium`,
  or asks about game features such as skills, allies, monster girls, combat UI,
  dungeon crawling, inventory, leveling, character systems, or save-file compatibility.
  This skill captures the project's architecture, the user's UI/consistency preferences,
  and recurring workflows so the agent does not re-explore the codebase from scratch.
---

# Pandemonium Development Helper

## Project Context
- **Path:** `C:\Code\Pandemonium`
- **Language:** Python 3 (terminal / text-based RPG with tkinter GUI)
- **Entry point:** `launcher.py`
- **Virtual env:** `C:\Code\Pandemonium\.venv` (do not install packages globally)

## Architecture Overview
| Directory / File | Role |
|---|---|
| `character.py` | Character creation, `ensure_player_fields()`, `player_max_hp()` |
| `leveling.py` | XP gains, level-up rewards (HP + attribute + skill unlocks) |
| `dungeon.py` | Dungeon crawling, floor generation, combat triggers, superboss milestones |
| `inventory.py` / `inventory_ui.py` | Inventory, equipment, and item management |
| `save_load.py` | Save/load system |
| `city.py` / `city_dialogue.py` | Overworld city hub and NPC dialogue |
| `events.py` | Random + fixed date-based event system, day/month tracking, event handling during time skips |
| `combat/` | All combat-related code |
| `combat/combat_engine.py` | Combat loop, initiative, turn order (player + allies + enemies) |
| `combat/combat_ui.py` | Combat HUD: ASCII boxes, HP bars, buff/debuff tags |
| `combat/player_actions.py` | Player turn handler (attack, skills, items, flee, capture) |
| `combat/ally.py` | Ally creation from house girls, ally stats, ally turn actions |
| `combat/skills.py` | Class skill definitions, execution, cooldowns, mastery |
| `combat/ally_skills.py` | Ally innate/learnable skill execution engine |
| `combat/superboss_common.py` | Shared combat loop for milestone boss fights (avoids circular imports) |
| `combat/capture.py` | Monster-girl capture logic (nets, affection) |
| `combat/stats.py` | Effective attribute computation (base + equipment + buffs) |
| `combat/status_effects.py` | Poison, burn, bleed, curse, dread, silence, fear, vulnerable, etc. |
| `combat/stat_milestones.py` | Passive bonuses at every 5 base attribute points (STR, CON, DEX, WIS, CHA, LRN) |
| `combat/elemental.py` | Elemental damage/resistance profiles (fire/water/thunder/wind/earth/light/dark) |
| `combat/abyss_fang.py` | Abyss Fang weapon mechanics: tempo conversion, cooldown ticks, state cleanup, triple-action tracking |
| `combat/tarnished_jade.py` | Tarnished Jade armor pin-stack: turn-start HP drain, Divine Lament trigger, Wedge Backlash |
| `combat/captain_cutlass.py` | Cutlass of the Captain weapon mechanics: riposte counter, High Tide Battle stacking buff, Crew Rally active |
| `combat/everlong_ship.py` | Everlong Ship superboss: crew-replacement loop, untargetable parrot cannon marker, defend-to-dodge mechanic |
| `combat/entangled_chrysalis.py` | Chrysalis, the Entangled One: Pandemonium Floor 20 boss with three Temporal Aspects and Paradox Fracture mechanic |
| `combat/queen_of_hearts.py` | Wonderland Floor 10 superboss: Royal Decree cycling, Card Soldier minions, Temper Tantrum, Mercy Rule |
| `combat/wicked_witch.py` | Wonderland Floor 30 superboss: three-phase fight with Flying Monkeys, Emerald Flame, water weakness |
| `combat/jabberwock.py` | Wonderland Floor 40 superboss: four-phase narrative fight (Bewilderbeast → Manxome → Frabjous → Narrative Collapse), Alice-linked |
| `combat/mary_sue.py` | Wonderland Floor 50 final superboss: five-phase fight with Plot Armor system, Shadow Gauntlet, 8 damage-type stripping |
| `combat/mary_sue_shadows.py` | Shadow boss factory & AI for Mary Sue fight (Shadow Queen/Wolf/Jabberwock), ~30-40% scaled versions |
| `combat/black_silence.py` | Black Silence superboss: multi-weapon phase cycling, gloves mechanic via `black_silence_gloves.py` |
| `combat/wl_floor_bosses.py` | 20 unique Wonderland floor boss AI patterns (F2–F48 even floors, non-milestone), each with unique attack patterns |
| `combat/dummy.py` | Training dummy for barracks damage testing, configurable stats, passive target (0 damage, always fleeable) |
| `combat/combat_io.py` | Thread-safe I/O abstraction (`BaseCombatIO`, `TerminalIO`, `c_print`/`c_input`/`c_clear`). GUI sets custom IO before combat |
| `combat/enemy_ai.py` | Enemy attack logic, damage mitigation application (defense buffs, passives, dodge, divine shield) |
| `combat/wedding_specials.py` | Wedding accessory combat effects (Bonded bonuses, soulbound checks, post-combat rewards) |
| `combat/helpers.py` | Shared combat helpers (`format_damage_msg`, etc.) |
| `combat/action_menu.py` | Action menu builder for player/ally turns — conditional menus based on equipment, skills, target type |
| `dungeon_rooms.py` | Non-combat room generation (fountain, merchant, trap, treasure, stat-check), ASCII exploration map |
| `pandemonium_curses.py` | Pandemonium floor curses: 10 curse types, 4 corruption tiers (1.0×–2.5×), cumulative scaling per 10 floors |
| `wonderland_curses.py` | Wonderland floor quirks (mostly beneficial) + Shadow system (Floor 40+: persistent negative effects, Mary Sue alteration) |
| `facilities/` | City facilities (house, shop, inn, blacksmith, temple, guild, trade hall, gift shop) |
| `facilities/house.py` | Monster girl storage, recruiting, affection system, lounge with ally ascension menu, engagement/wedding |
| `facilities/temple.py` | Curse removal, blessings, and **Ascension Stone shop** (unlocks when any dungeon reaches n+10 floors) |
| `facilities/guild.py` | Bounty board and **Level Cap Ascension** (biome-threshold check) |
| `facilities/barracks.py` | Ally skill teaching menu (select ally → pick learnable skill → spend EXP to learn) |
| `facilities/blacksmith.py` | Equipment enhancement & scroll fusion (shows player + ally equipped items with owner tags) |
| `facilities/gift_shop.py` | Romantic gifts and **engagement rings** (exclusive source) |
| `facilities/travel.py` / `facilities/travel_events.py` | Overland/sea travel with event system, merchant encounters, `_item_stat_line()` for equipment display |
| `facilities/pathfinding.py` | BFS shortest-path engine for world map; supports mount time-reduction and ship speed bonus on sea segments |
| `facilities/arcane_tower.py` | Arcane Tower facility (magic-related upgrades) |
| `facilities/herbalist.py` | Herbalist facility (consumables, potions) |
| `facilities/black_market.py` | Black Market facility (rare/illicit items) |
| `facilities/port.py` | Port facility (sea travel hub) |
| `facilities/shipyard.py` | Shipyard facility (ship purchase/upgrade) |
| `resources/` | Static data: races, classes, enemies, items, dialogues, mounts |
| `resources/constants.py` | Game constants (EXP formula coefficients, etc.) |
| `resources/cities.py` | City definitions, dungeon listings, travel connections, biome mapping |
| `resources/city_maps.py` | ASCII city map data for GUI rendering |
| `utils.py` | Shared utilities: `_tprint`/`_tpause`/`_tinput` (GUI-aware I/O), `advance_time()`, `apply_death_penalty()`, `clear_screen()` |
| `events.py` | Random + fixed date-based event system, day/month tracking, event handling during time skips |
| `make_exe.py` | PyInstaller build script; bundles game + YAML data into `dist/Pandemonium/`, entry point = `launcher.py` |
| `stat_rebalance.py` | Standalone script that re-distributes enemy stat points across YAML files by level/race bias |
| `verify_phase2.py` | Phase 2 verification script: tests thread-local I/O independence, combat engine with mock IO, GUI widget imports |
| `resources/skill_loader.py` | YAML-based skill data loading |
| `resources/enemies/enemy_loader.py` | YAML-based enemy loading (replaces old `resources/enemies.py`) |
| `resources/mounts.py` | Mount definitions and trade-hall integration |
| `launcher.py` | GUI entry point (tkinter). PyInstaller target. |
| `gui/app.py` | Main `tk.Tk` window setup, `PandemoniumApp` class, `ScreenManager` wiring |
| `gui/screen_manager.py` | Screen transition router, back-stack navigation, persistent top status bar, bottom log panel |
| `gui/theme.py` | Dark theme constants (bg `#1a1a2e`, accent `#e94560`, monospace fonts, rarity colors, window defaults) |
| `gui/screens/base_screen.py` | Abstract `BaseScreen` (tk.Frame + ABC). Every major game state has its own screen subclass |
| `gui/screens/city_screen.py` | City hub with service buttons and action bar |
| `gui/widgets/hp_bar.py` | Custom `tk.Canvas` HP/MP/XP bar widget |
| `gui/widgets/confirm_dialog.py` | Modal confirm / OK dialogs |
| `gui/terminal.py` | Thread-safe GUI I/O for facility code: `Terminal` class with `print`/`menu`/`confirm`/`pause`/`input` via tkinter widgets |
| `gui/io_redirector.py` | Optional stdout capture for stray `print()` calls during migration, forwards to GUI log panel |
| `gui/notification_queue.py` | In-game toast/alert system: queue notifications during dungeon, show on city return |
| `gui/settings.py` | GUI-only preferences persistence (`gui_settings.json`): window size, theme, font, keyboard mode, log lines |
| `gui/screens/main_menu_screen.py` | Main menu with New Game / Load / Settings / Quit |
| `gui/screens/char_create_screen.py` | Character creation: race, class, name input |
| `gui/screens/city_screen.py` | City hub with service buttons, action bar, and real-time game clock tick |
| `gui/screens/dungeon_screen.py` | Dungeon floor exploration, room navigation, mini-map |
| `gui/screens/combat_screen.py` | Combat HUD screen (wraps terminal combat in GUI frame) |
| `gui/screens/inventory_screen.py` | Inventory management with equipment/consumable tabs, stat comparison |
| `gui/screens/facility_screen.py` | Generic facility wrapper: runs facility functions in background thread with Terminal I/O bridge |
| `gui/screens/travel_screen.py` | Overland/sea travel map with path visualization |
| `gui/screens/world_map_screen.py` | World map overview with city connections |
| `gui/screens/post_floor_screen.py` | Post-floor summary (rewards, stat gains, milestone checks) |
| `gui/screens/death_screen.py` | Death dialog: continue (penalty) or quit |
| `gui/screens/splash_screen.py` | Splash/loading screen on startup |
| `gui/screens/settings_screen.py` | GUI settings panel (theme, font, keyboard, window) |
| `gui/screens/changelog_screen.py` | Version changelog display |
| `gui/screens/facilities/` | Facility-specific screen overrides (currently empty — facilities use generic `FacilityScreen`) |
| `gui/combat/combat_renderer.py` | ASCII combat HUD rendered in monospace tkinter text widget |
| `gui/combat/action_panel.py` | Combat action button panel (Attack, Skills, Items, Defend, Flee, Capture) |
| `gui/widgets/city_map.py` | City map canvas widget |
| `gui/widgets/item_card.py` | Item display card with rarity coloring and stat lines |
| `gui/widgets/stat_display.py` | Player/ally stat breakdown widget |
| `gui/widgets/log_window.py` | Popup log window for combat/dungeon log scrollback |
| `gui/widgets/notification_toast.py` | Toast notification popup widget |

## User Preferences & Conventions
1. **UI Consistency:** Any display format for the player must be mirrored for allies. If the player UI shows a header (`=== Name (Level X) ===`), attribute breakdown, or equipment rarity, the ally version must match exactly.
2. **Combat HUD Layout:** Uses a fixed-width ASCII box (inner width = 68 chars). Left party column = 31 chars, right enemies column = 33 chars. Each entity occupies **2 rows**: row 1 = name/HP/♀ symbol; row 2 = active buff/debuff tags (e.g., `[+STR]`, `[BLD]`, `DRD`).
3. **Stat Display Format:** `Attribute: base + N(eq) + N(buff) = total`
4. **Monster Girls:** Marked with `♀` in UI. Captured via nets, stored in `house.py`, recruited when affection ≥ threshold. Allies are instantiated from house girls via `create_ally_from_girl()` in `combat/ally.py`.
5. **Combat Scale:** Maximum **1 player + 3 allies vs 5 enemies**. All ally actions are controlled by the player (no autonomous AI turns).
6. **Skill System:** Class-based skills unlock at specific levels, have cooldowns tracked in `player["skill_cooldowns"]`, and outgoing damage scales with the **corresponding attribute + Learning**.
7. **Dungeon Rooms:** Each floor has **10 rooms** with a **10% chance** for a non-combat room (fountain, merchant, trap, treasure, stat-check). The dungeon saves `saved_dungeon_floor`, `saved_dungeon_rooms`, and `saved_dungeon_room_index` so mid-floor progress persists across loads.
8. **Superboss Tier Pool:** `dungeon.py` milestone floors use a tier pool. Regular dungeons use `[0,1,2,3,4,5,6]` (7 tiers), shuffled per floor so each superboss appears once before refilling. New superbosses must be added to the pool and imported in `dungeon.py`. Existing superboss modules: `combat/broodmother.py`, `combat/slitcurrent.py`, `combat/sylvana.py`, `combat/ignis.py`, `combat/yinglong.py`, `combat/rientrante.py`, `combat/everlong_ship.py`, `combat/black_silence.py`, `combat/entangled_chrysalis.py`.
    - **Wonderland** has its own dedicated boss system: Floor 10 = Queen of Hearts, 20 = Big Bad Wolf, 30 = Wicked Witch, 40 = Jabberwock, 50 = Mary Sue. Every even non-milestone floor (F2–F48) has a unique floor boss via `combat/wl_floor_bosses.py`.
    - **Pandemonium** has `combat/entangled_chrysalis.py` on Floor 20 (three Temporal Aspects + Paradox Fracture). Other Pandemonium floors use the standard tier pool with the 1.7× stat multiplier.
9. **Save Compatibility:** When adding new fields to the player or ally dict, always update `ensure_player_fields()` in `character.py` to apply `.setdefault()` defaults so old save files load safely.
10. **Git Hygiene:** The project has a `.gitignore` at `C:\Code\Pandemonium\.gitignore` that excludes `__pycache__/`, `savefile/`, `.venv/`, IDE droppings, and OS files.
11. **Stat Milestones:** Every 5 points in a base attribute grants a passive bonus tracked in `combat/stat_milestones.py` (e.g., STR → +1 flat damage, CON → -1 damage taken, DEX → +1% dodge chance, WIS → +1 initiative/flee AND +1% healing potion efficacy, CHA → +1% capture chance, LRN → +1% skill damage). These are shown in `inventory_ui.py` and computed from base stats only. WIS now drives initiative/flee; DEX drives dodge.
12. **Level Cap System:** Player levels are capped at multiples of 10. The cap can only be raised after clearing enough **unique biomes** to the next multiple of 10. Required biomes = `(current_cap // 10) * 2 + 1`, capped at total biome count (e.g., 3 biomes at 10→20, 5 at 20→30, 7 at 30→40, etc.). The count is dynamic from `CITIES` biomes. When eligible, the player ascends the cap via the **Guild Hall** facility. Ally levels are also capped and can be broken with **Ascension Stones** sold at temples when any dungeon reaches n+10 floors.
13. **Experience at Cap:** When the player is already at their level cap, `gain_exp()` silently discards incoming XP (no accumulation, no message). This prevents a burst-level bug where stored XP would trigger multi-level jumps immediately after cap ascension.
14. **Inventory Cap System:** Base capacity is 10 equipment + 20 consumables. Upgradeable via a facility. Each ally adds +5 non-upgradeable slots. When full, the game prompts the player to choose what to discard rather than auto-dropping.
15. **Death Mechanic:** On death, the player is given a choice to continue (gold penalty, time passes, HP restored to 1) or quit. The original mechanic was returning directly to the main menu.
16. **Dual Accessory Slots:** Player and allies can equip **two accessories** (`accessory1` and `accessory2`). The old single `accessory` slot was migrated in `ensure_player_fields()`. Equipment loops across the codebase must iterate over both slots.
17. **Wedding / Engagement System:** At 100 affection, a monster girl can be proposed to with an engagement ring (bought exclusively at the gift shop). This raises the affection cap to 200. At 200 affection, talking to her triggers `house_special_gift` dialogue and awards a unique **Legendary wedding accessory** (46 total, one per girl). These are **soulbound** (cannot be sold/dropped) and have **Bonded** effects amplified when the married girl is in the active party.
18. **Daily Limits:** Talking to a girl is limited to **2-3 times per day**. Gifting works **once per day**. Track these via `daily_effects` or per-girl counters.
19. **Event System:** The game has random and fixed date-based events in `events.py`. Day/month display is on the **City HUD** (not the guild). Events must fire even when the player is in a dungeon or when time skips occur (death, sleeping, travel).
20. **Inventory Stacking:** Non-equipment items with identical `id`/`name`, `rarity`, `enhance`, and `gift_type` stack via `_items_stackable()` in `inventory.py`. The `count` field tracks quantity; `_ensure_count()` adds it if missing. When selling stacked items, revenue is multiplied by `count`. Equipment never stacks. `remove_item_by_reference()` decrements `count` before popping.
21. **Ally Skill Learning:** Allies learn skills through the **Barracks** facility (`teach_skill_menu()` → `teach_ally_skill()`). The `learning` field format is `{"skill_id": "...", "exp": 0, "exp_needed": 300}`. EXP is awarded via `gain_skill_learning_exp()` in `combat/ally_skills.py`, usually tied to dungeon/combat XP. Only one skill can be learned at a time; starting a new one replaces the old progress.
22. **Learnable Skill Tiers:** The `resources/skill_book/skill_list.yaml` defines `learnable_skills` by category (offensive, defensive, support). Each skill has a `tier` (1–4), `exp_cost`, and `required_level`. The Barracks UI displays skills grouped by category with tier and cost. Tier 4 skills require ally level 15+ and cost 2400 EXP. The skill system also supports `power_type` (str/dex/ler/cha), `base_power`, `cooldown`, `target` (enemy/enemies/all_allies/self), status effects (`poison_damage`, `burn_damage`, `stun_chance`, `apply_slow`, `apply_weaken`), and `mastery_thresholds`.
23. **Innate Skills & Race Passives:** All 46 monster girls have innate skills defined in `resources/skill_book/innate_skills.yaml`. Each girl has exactly 2 innate skills mapped under `innate_skills:`. Race passives (e.g., Beast → Feral Instinct, Demon → Infernal Blood, Giant → Colossal Might) are defined in `skill_list.yaml` under `race_passives:`. When adding a new monster girl, always add both her innate skill entries and, if she introduces a new race, a race passive. Without innate skills, allies are blank slates that must learn everything at the Barracks.
24. **Ally Skill Execution in Combat:** `combat/ally_skills.py` contains `execute_ally_skill()` which handles damage calculation, multi-target hits, status effect application (poison, burn, stun, slow, weaken), life steal, buff/debuff application, and mastery progression. Ally skills are selected during the ally's turn in `combat/ally.py` and displayed in the combat HUD via `combat/combat_ui.py`.
25. **House Tier Expansion:** House levels go beyond the original 3 tiers to accommodate up to 48+ monster girls. Higher tiers increase storage cap, income per day, and reduce rest time. Income scales with player level and house tier so late-game gold remains meaningful (e.g., a floor-20 player can have 20k+ gold). **Rest** only restores party HP; **Sleep** (available 20:00–04:00) advances time by 8 hours, similar to the inn.
26. **Duplicate Capture Handling:** When a captured monster girl already exists in the house, the player is offered: sell the duplicate for scaled gold (based on level), cancel the capture, or release the new one. This prevents exact duplicates from clogging storage.
27. **Wedding Ring Consumption:** Upon successful proposal, the engagement ring is consumed (removed from inventory). The girl still receives the ring's stat bonus permanently as a "gifted" buff stored in her dict. The ring item itself is gone.
28. **make_exe.py Build:** Run with `.venv\Scripts\python.exe make_exe.py`. It auto-collects `--add-data` entries for `resources/enemies/enemies_data`, `resources/skill_book`, `resources/dialogues`, and other YAML dirs. If new resource directories are added, they must be added to `collect_data_files()` or PyInstaller will miss them at runtime.
29. **Inventory Equipment Display:** When showing equipment in shop, inventory, or travel-event menus, stat mods should be rendered via `_item_stat_line()` (lives in `facilities/travel_events.py` and is imported by `facilities/shop.py`). Format: `[Slot | Stat +N, Stat +N]`. This ensures the player sees attribute bonuses before buying or equipping. Both shop stock and player inventory must show this line.
30. **End-of-Combat Cleanup:** When combat ends (victory, flee, or death), `combat/combat_engine.py` must call `end_of_combat_cleanup()` to tick player and ally skill cooldowns, decrement buff durations, and clear temporary combat state (e.g., Abyssal Tempo, Tarnished Jade pins). Without this, cooldowns/buffs from the final combat turn persist into the next fight. This is distinct from turn-start ticking that happens during active combat.
31. **Pandemonium Dungeon (Isle of Glass):** The endgame dungeon requires clearing 40 floors across 4 biomes to unlock. Once unlocked, it applies `pandemonium_mode` which multiplies all enemy stats by 1.7× via `combat/stats.py`. The dungeon is accessed separately from the regular city dungeon list. Check `biome` tag before applying the multiplier.
32. **Minion-Only Enemies:** Superboss summons (e.g., Dream Floatsam, Vileheart Spiderling, Sylvana Mirror, Rientrante shards) must be tagged with `minion_only: true` in their YAML definition. `dungeon.py`'s `get_random_enemy_key()` skips these entries so they never appear in regular dungeon rooms. Without this flag, superboss minions spawn as standalone random enemies.
33. **Superboss Re-Challenge Lock:** When a player re-challenges a milestone floor (n+20) that they already cleared, the superboss must NOT switch to a different one. The check is `city_prog["max_floor"] <= floor` in `dungeon.py` — only trigger superboss generation on first-ever clear of that floor. Otherwise the tier pool shuffle would replace the original boss.
34. **Combat Inventory Stack Display:** When displaying items in combat menus (bag, equip, use), non-equipment stack counts must render as `Item Name x{qty}`. The `count` field is the source of truth; use `item.get("count", 1)` everywhere. This applies to `combat/player_actions.py`, `combat/ally.py`, and any other combat UI that shows inventory.
35. **Design-First Workflow:** The user often requests "design only" first (e.g., superboss concepts, unique item ideas), then returns later with "implement it" or refinement requests. When designing, produce a Markdown design doc with clear mechanical identity, counterplay, and flavor text. When implementing, translate the design into Pandemonium-compatible mechanics before writing code.
36. **External Game Design References:** The user frequently references *Limbus Company* (E.G.O Gifts, Abnormality mechanics, Sinner identities) for design inspiration. When translating these into Pandemonium, map LC concepts to existing systems: Clash Power → initiative/skill scaling, Coin variance → crit/random damage, Sanity → SP/buffs, E.G.O cost → HP costs or cooldowns, and Abnormality gimmicks → boss phases or unique item passives.
37. **Thread Safety in GUI Mode:** Facility and combat code runs in background threads when in GUI mode. All I/O must use the appropriate abstraction: `combat/combat_io.py` for combat (`c_print`, `c_input`), `gui/terminal.py` for facilities (`term.print`, `term.menu`). Never call `print()` or `input()` directly in code that can run under GUI — use the `_tprint`/`_tpause`/`_tinput` pattern from `utils.py`.
38. **Dungeon Room Types:** Non-combat rooms (`dungeon_rooms.py`) include: fountain (healing + buff), merchant (wandering trader, reuses travel merchant logic), stat_check (narrative challenge — player or ally can attempt with stat-based DC), treasure (guaranteed rare+ item), trap (avoidable hazard, DEX+WIS check). Room generation uses 10% chance per room.
39. **Death Penalty Flow:** `utils.py` → `apply_death_penalty()`: 20% gold loss (min 10), 8-hour time advance, HP restored to 1 (player + allies), return to origin city, wipe dungeon progress, clear Abyss/Tarnished Jade combat state. This function is I/O-free so both terminal and GUI can use it directly.
40. **Training Dummy:** `combat/dummy.py` provides `create_dummy_enemy()` and `spar_with_dummy()`. Configurable HP, stat mods, elemental resists. Dummy always deals 0 damage and is always fleeable. Used in barracks for damage testing. In GUI mode, barracks sets `player['_pending_dummy_combat']` and city screen launches CombatScreen.

## Wonderland Dungeon
Wonderland is the second endgame dungeon (unlocked after clearing sufficient biomes). 50 floors with unique mechanics:

- **Quirk System** (`wonderland_curses.py`): Each floor rolls a random "quirk" — mostly beneficial whimsical effects. 4 tiers (1.0×–2.0×) based on floor depth. Effects include: `curiosity_boost` (random stat buff), `tea_party` (healing), etc.
- **Floor Bosses** (`combat/wl_floor_bosses.py`): Every even non-milestone floor (F2–F48) has a unique boss with custom AI. 20 bosses total ranging from White Rabbit to The Nothing. Each has unique attack patterns and status effects.
- **Milestone Superbosses**: Floor 10 = Queen of Hearts, Floor 20 = Big Bad Wolf, Floor 30 = Wicked Witch, Floor 40 = Jabberwock, Floor 50 = Mary Sue.
- **Shadow System** (Floor 40+): At Floor 40, player must choose 1 persistent Shadow (negative effect). At Floor 46, a 2nd Shadow is chosen from a refreshed list. 10 possible Shadows (e.g., `authors_will`, `off_with_heads`, `jabberwock_wrath`). Each Shadow alters Mary Sue's behavior on Floor 50, granting her unique passives.
- **Mary Sue Fight**: 5-phase battle with Plot Armor (5 stacks, 12% DR each, stripped by hitting with new damage types from 8-element pool), Shadow Gauntlet phases (Queen → Wolf → Jabberwock shadows, each at ~30-40% scale), Phase 5 Author's Wrath.

## Pandemonium Dungeon & Curse System
Pandemonium (Isle of Glass) is the pinnacle endgame dungeon requiring 40 floors across 4 biomes to unlock.

- **Curse System** (`pandemonium_curses.py`): Each floor rolls a random curse that persists for the entire floor. 10 curse types: `damage_taken`, `damage_dealt`, `room_damage`, `healing_reduction`, `gold_reduction`, `no_flee`, `stat_check_wis_dc`, `stat_check_dex_dc`, `enemy_speed`, `skip_chance`, `cooldown_increase`.
- **Corruption Tiers**: Tier 1 (F1–10) = 1.0×, Tier 2 (F11–20) = 1.5×, Tier 3 (F21–30) = 2.0×, Tier 4 (F31–40) = 2.5×. Cumulative corruption increases every 10 floors.
- **Stat Multiplier**: All enemies in Pandemonium get 1.7× stats via `combat/stats.py` when `pandemonium_mode` is active (checked via `biome` tag).
- **Chrysalis Boss** (Floor 20): Three Temporal Aspects (Past/Present/Future), three immortal linked shards, Paradox Fracture vulnerability mechanic. Uses a custom `_ParadoxFractureDict` wrapper to amplify HP damage based on Paradox Fracture stacks.

## Combat I/O System
`combat/combat_io.py` provides thread-safe I/O abstraction for combat code:

- `BaseCombatIO`: Abstract interface with `print()`, `input()`, `clear()`, `show_hud()`.
- `TerminalIO`: Default implementation using `builtins.print()`/`input()`.
- Thread-local storage via `threading.local()` — each thread gets its own IO object.
- Convenience aliases: `c_print()`, `c_input()`, `c_clear()` → route to current thread's IO.
- GUI mode: Before combat starts, the GUI sets a custom IO object via `set_io()`. Combat code calls `c_print()`/`c_input()` which route to GUI widgets.
- `verify_phase2.py` tests: default IO is TerminalIO, thread-local independence, combat engine with mock IO.

## Typical Workflow
1. The user often references files with `@C:\Code\Pandemonium\...` or pastes terminal output showing a bug/UI issue.
2. Read the relevant file(s) directly using the architecture table above instead of globbing the entire repo.
3. If the change touches UI, read both the player and ally versions to enforce consistency.
4. If the change adds new persistent fields, patch `ensure_player_fields()` in `character.py`.
5. After edits, verify syntax or run a quick import check. On Windows, `python` may not be in PATH; use the venv interpreter if needed.
6. When updating `combat/action_menu.py`, remember that allies should only see actions they can actually perform (e.g., no "Wield the Abyss" or "Wield the Cutlass" for allies, no capture for non-monster-girl enemies).
7. **External Design Doc Translation:** The user occasionally receives game-design documents (e.g., friend's superboss stat blocks as `.txt` files). Translate the design into Pandemonium-compatible mechanics first, then implement in a new `combat/<boss_name>.py` module, add the YAML entry to `resources/enemies/enemies_data/superbosses.yaml`, wire the import into `dungeon.py`, and extend the tier pool if needed.
8. **Wedding Accessory Wiring:** When adding a new wedding accessory, the item definition goes in `resources/items.py`, but its **combat effects** must be wired into `combat/wedding_specials.py` and hooked into `combat_engine.py`, `player_actions.py`, `enemy_ai.py`, `stats.py`, `capture.py`, `dungeon.py` (post-combat rewards), and shop/house systems (soulbound checks).

## GUI Migration (tkinter)
The project is actively migrating from a pure terminal UI (`print`/`input`) to a **tkinter GUI** while preserving full terminal compatibility.

- **Current State:** Phases 0–2 are complete. Phase 3 (facilities via `FacilityScreen` + `Terminal` bridge) is in progress. Phase 4 (polish, keyboard shortcuts) is planned.
- **Phased approach:** Phase 0 = architecture (`gui/` package, `launcher.py`, `theme.py`, `screen_manager.py`, `base_screen.py`, `app.py`). Phase 1 = main menu, character creation, city hub. Phase 2 = combat HUD, action buttons, initiative display, inventory screen. Phase 3 = facility screens, dungeon map, house UI. Phase 4 = polish, keyboard shortcuts, build updates.
- **Screen-based architecture:** Every major game state gets a screen class inheriting from `BaseScreen`. `ScreenManager` handles transitions, back-stack, and shared game state. Screens are swapped in-place inside the main window's content area. Overlay screens (combat, inventory, facilities) are pushed on top and dismissed with a callback.
- **Game Clock:** `ScreenManager` runs a real-time game clock: 1 in-game minute per 2 real seconds. Clock ticks only on "game" screens (City, Dungeon, WorldMap, Travel, PostFloor, Facility). Clock pauses when overlays (combat, inventory) are active.
- **Theme:** Dark palette (`#1a1a2e` bg, `#e94560` accent, `#16213e` top/bottom bars). Monospace font is mandatory for ASCII art preservation (Consolas / Menlo / DejaVu Sans Mono).
- **Save compatibility:** Zero changes to save file format. GUI and terminal share identical saves.
- **Build system:** `make_exe.py` bundles `gui/`, `resources/`, and sets `launcher.py` as the PyInstaller entry point. All `--add-data` entries for YAML resource directories must remain.
- **Keyboard shortcuts:** Planned mapping includes 1-9 for skills, A/D/F/C/U for core actions, I for inventory, Esc for back.
- **Hybrid Adapter pattern:** Terminal functions that call `print()`/`input()` are being refactored to use the `_tprint`/`_tpause`/`_tinput`/`_tmenu`/`_tclear` pattern from `utils.py` (or the module-local equivalents). These detect GUI mode and route to `gui/terminal.py` or `combat/combat_io.py` as appropriate.
- **Facility I/O Bridge:** `gui/terminal.py` `Terminal` class communicates with `FacilityScreen` via thread-safe queues. Facility functions run in background threads; all `print`/`menu`/`confirm`/`pause`/`input` calls are served by tkinter widgets on the main thread.
- **Widget library:** Reusable widgets live under `gui/widgets/` (HP bar, stat display, item card, confirm dialog, city map, log window, notification toast). Screens should reuse these rather than inline widget creation.
- **Combat HUD preservation:** The ASCII combat HUD (68-char inner width, 2-row entity layout) is rendered in `gui/combat/combat_renderer.py` using a monospace tkinter text widget so alignment survives the transition.
- **Notification System:** `gui/notification_queue.py` provides an in-game toast system. Notifications are queued during dungeon runs and displayed when returning to the city. Supports categories: info, warning, success, error, event.
- **GUI Settings:** `gui/settings.py` persists GUI-only preferences in `savefile/gui_settings.json` independently of game saves. Includes window size/position, font size, theme, keyboard mode, log max lines. Merges with defaults for backward compatibility.

## Pitfalls
- **Do not re-explore the entire codebase from scratch.** Use the known file paths to jump straight to the relevant module.
- **Ally action menus are not identical to player menus.** Allies cannot use the Abyss Fang, capture nets, or class skills that belong to the player class. Ally action menus must be conditionally built based on what the ally actually has equipped or unlocked.
- **HP calculations:** `player_max_hp()` and `ally_max_hp()` both use `15 + Constitution * 3 + level_hp_bonus`. Keep these in sync when modifying HP logic.
- **Dread / debuff display:** If an entity is affected by a status but it does not show in the HUD, the bug is usually in `combat/combat_ui.py` formatting functions (e.g., `_get_entity_buff_tags`), not in the effect application itself. Check both the `active_debuffs` list and the shorthand flags (e.g., `cursed`, `dreaded`).
- **Skill scaling:** The user prefers damage formulas that combine the skill's primary attribute (e.g., STR for Warrior) with the Learning attribute.
- **Enemy data source changed:** `resources/enemies.py` no longer exists. Enemy data is loaded from YAML files via `resources/enemies/enemy_loader.py`. The `resources/enemies/__init__.py` re-exports `ENEMIES`, `CAPTURE_MESSAGES`, `AFFECTION_GIFTS`, etc. Duplicate enemy IDs across YAML files trigger loader override warnings (non-fatal). Biomes are defined in `resources/enemies/biome_races.py`.
- **Windows bash PATH issues:** Bare `python` and `python3` often fail in Bash on Windows. Use `C:/Code/Pandemonium/.venv/Scripts/python.exe` or `python3` from the venv directory, or use `cd C:/Code/Pandemonium && .venv/Scripts/python.exe ...`.
- **Superboss circular imports:** New superboss modules should import shared logic from `combat/superboss_common.py` (initiative, HUD, combat loop) rather than duplicating or importing from each other. Avoid importing `dungeon.py` from combat modules.
- **Missing mitigation sources:** If the user asks why defense buffs, divine shield, or passive damage reduction "don't work," the functions likely exist but are **not called in `combat/enemy_ai.py`**. Check `enemy_attack()` for: defense buff lookup, divine shield check, passive damage reduction (`apply_passive_to_damage_taken`), dodge roll (`get_dexterity_bonus` as dodge chance), and vulnerable/fear multipliers.
- **Ally equipped items in blacksmith:** Ally equipped items are referenced directly (shared dicts). Enhancing an ally's gear modifies it in-place without unequipping. The blacksmith menu now tags items with `(Equipped by Player)` / `(Equipped by <ally_name>)`. The equipped_slots list includes `accessory1` and `accessory2`.
- **Ally cooldown display:** The combat HUD cooldown block was historically player-only (`if active_ally is None`). Ally turns now also render `(SkillName recharging: N turn(s))` below their action menu.
- **Wedding specials module:** `combat/wedding_specials.py` contains `begin_wedding_combat()` and `end_wedding_combat()` which must be called from `combat_engine.py` and `dungeon.py` to apply Bonded effects and post-combat rewards.
- **Event system day tracking:** The day/month counter is stored on the player dict and displayed in `city.py`. Events must be checked whenever `advance_time()` crosses a day boundary, including during dungeon crawling, sleep, death recovery, and travel.
- **Superboss hook signatures:** Every superboss module (`broodmother.py`, `ignis.py`, `rientrante.py`, `slitcurrent.py`, `sylvana.py`, `yinglong.py`) defines `enemy_turn_hook(enemy, ctx, pl, p_con, defending)` and optionally `inner_enemy_hook`. The signature must match exactly across all modules; adding extra kwargs to one but not others causes runtime `TypeError` when the combat loop calls them reflectively. If a new boss needs extra state, store it in `ctx` rather than changing the hook signature.
- **Barracks skill-teaching flow:** When debugging "ally didn't learn skill," check three places: (1) `facilities/barracks.py` passes the correct ally index, (2) `combat/ally_skills.py` sets `ally["learning"]` with the correct `exp_needed`, and (3) `gain_skill_learning_exp()` is actually called during dungeon/combat. If the ally's `learning` field is `None`, teaching never started; if `exp >= exp_needed` but no skill was added to `learned_skills`, the completion check is missing.
- **Player vs Ally max HP in UI:** Player max HP is computed dynamically via `player_max_hp(player)`; allies store it explicitly in `ally["max_hp"]`. Any UI that displays HP for a mixed list of targets (e.g., ally skill target selection, combat HUD) must branch: `m is player` → use `player_max_hp(m)`, else `m.get("max_hp", 1)`. Using `.get("max_hp", 1)` for the player returns `1` and shows `106/1`.
- **End-of-Combat state bleed:** If skill cooldowns, buffs, or temporary weapon states (Abyssal Tempo, Tarnished Jade pins) carry over between unrelated fights, the bug is missing `end_of_combat_cleanup()` in `combat_engine.py`. Search for `victory`, `flee`, and `player_death` handlers — all three must call the cleanup before returning to the dungeon/city loop.
- **Minion-only enemies in regular rooms:** If a superboss summon (e.g., Dream Floatsam, Sylvana Mirror) appears as a random room enemy, the YAML entry is missing `minion_only: true`. Also verify `dungeon.py` filters it: `if data.get("minion_only", False): continue` inside `get_random_enemy_key()`.
- **Ally defending flag stale state:** `ally["defending_this_turn"]` is set to `True` when an ally chooses Defend, but it must be **reset to `False` at the start of every ally turn** in `handle_ally_turn()` (`combat/ally.py`). Without this reset, a single Defend action on any previous turn will make the Wedge/parrot mechanics think the ally defended on the current turn, causing incorrect damage negation.
- **Ally skill cooldowns in superboss fights:** `superboss_common.py` historically only called `tick_skill_cooldowns(player)` at round end. It must also tick ally cooldowns: `for ally in get_alive_allies(player): tick_skill_cooldowns(ally)`. Without this, ally skills never cool down during superboss encounters.
- **Superboss death message visibility:** `superboss_common.py` calls `clear_screen()` at the start of each round before printing the HUD. If an enemy dies on the final turn of a round, its death message prints, then `clear_screen()` immediately erases it before the player can read it. Either delay `clear_screen()` until after a brief pause, or print a "round summary" block after initiative that re-lists any enemies who died last round.
- **stat_rebalance.py paths:** The rebalancing script expects to be run from the `C:\Code\Pandemonium` root. It looks for `resources/enemies/enemies_data/*.yaml` and writes back in-place. Running it from a different working directory causes `FileNotFoundError` on `all_enemies.yaml` or other files. Always run via `cd C:/Code/Pandemonium && python stat_rebalance.py`.
- **Wonderland boss keys:** Wonderland superboss/minion entities use `"wl_"` prefix keys (e.g., `wl_queen_of_hearts`, `wl_flying_monkey`). Wonderland floor bosses and shadows also use `wl_` prefix. This distinguishes them from main-dungeon entities. Always check the key prefix when debugging boss-specific issues.
- **Wonderland Shadow System:** At Floor 40, the player chooses a Shadow that persists across ALL subsequent floors. At Floor 46, a 2nd Shadow joins. Shadows are stored on the player dict. When Mary Sue is spawned on Floor 50, she reads the player's Shadow list to activate corresponding passives. If a Shadow is missing from the player dict, Mary Sue may be missing mechanics.
- **Pandemonium Curse Interaction:** Curses in `pandemonium_curses.py` are floor-specific (reset each floor). The `apply_curse_effect()` function scales the curse value by the current corruption tier multiplier. If a curse seems too weak/strong, check the corruption tier calculation in `get_corruption_tier()`.
- **GUI Thread Safety:** `ScreenManager` runs on the main (tkinter) thread. Facility and combat functions run in background `threading.Thread` instances. Never call tkinter widget methods directly from a background thread — always use `after()` or the Terminal/CombatIO queue system. Violating this causes silent tkinter crashes or garbled UI.
- **Chrysalis Paradox Fracture Dict:** The `_ParadoxFractureDict` wrapper in `combat/entangled_chrysalis.py` intercepts `__setitem__` for the `"hp"` key. If damage is applied via methods other than direct dict assignment (e.g., modifying a reference), the Fracture multiplier won't apply. Always set HP via `enemy["hp"] = new_value` in Chrysalis context.
- **Mary Sue Plot Armor:** Each damage type (Physical/Fire/Water/Thunder/Wind/Earth/Light/Dark) can only strip one Plot Armor stack. After all 8 types are used, no more stacks can be stripped. If Plot Armor isn't decreasing, verify the damage type tagging in the combat engine correctly labels each attack with an element type.
- **Wonderland Floor Boss AI signatures:** Each boss in `wl_floor_bosses.py` has a unique function. These are dispatched by floor number. If a boss function is missing for an even floor, the game may crash or fall back to a default. Always verify the floor-to-function mapping when adding/removing boss AI functions.
