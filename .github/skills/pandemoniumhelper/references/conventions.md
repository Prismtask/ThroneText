# Full Conventions & Common Pitfalls

## Conventions

### UI Consistency
1. Player & ally displays must match identically (headers, stats, rarity).
2. Combat HUD: Fixed 68-char ASCII box. Party left (31 chars), enemies right (33 chars). 2 rows/entity: row1=name/HP/♀, row2=buff/debuff tags.
3. Stat Display: `Attribute: base + N(eq) + N(buff) = total`
4. Monster Girls: ♀ symbol. Captured via nets → `./facilities/house.py`. Recruited when affection ≥ threshold. Allies via `create_ally_from_girl()`.

### Combat Scale
5. Max 1 player + 3 allies vs 5 enemies. Player controls all ally actions.
6. Skills: Class-based, unlock at levels, cooldowns in `player["skill_cooldowns"]`. Damage scales with primary attribute + Learning.
7. Dungeon Rooms: 10 rooms/floor, 10% non-combat. Mid-floor progress saved.
8. Superboss Tier Pool: 7 tiers `[0..6]`, shuffled per floor. Wonderland has own system (F10=QoH, F20=Wolf, F30=Witch, F40=Jabberwock, F50=MarySue). Pandemonium F20=Chrysalis. Use `superboss_common.py` for shared logic.

### Save & Progression
9. Save Compat: New fields → add `.setdefault()` in `ensure_player_fields()`.
10. Level Cap: Multiples of 10, raised by clearing biomes via Guild Hall. Required biomes = `(cap//10)*2+1`. XP silently discarded at cap. Ally cap broken with Ascension Stones.
11. Inventory: Base 10 eq + 20 consumable. Allies +5 each. Non-eq stacks by id/name/rarity/enhance/gift_type with `count` field. Dual accessory slots (`accessory1`/`accessory2`).
12. Wedding: 100 affection → propose with ring (gift shop) → cap 200 → at 200 get Legendary soulbound wedding accessory (46 total, Bonded effects in party).
13. Death: `apply_death_penalty()`: 20% gold (min 10), +8h time, HP→1, return to city, wipe dungeon, clear Abyss/Jade state.

### Ally Systems
14. Ally Skills: Barracks teaches via `learning` dict `{skill_id, exp, exp_needed}`. Innate skills from YAML, 2 per girl. Race passives in `skill_list.yaml`.

### Elemental Systems
15. 8 Elements: Fire, Water, Ice, Lightning, Wind, Earth, Light, Dark. Each weapon has a primary element trait.
16. Elemental Debuffs: `elemental_debuffs.py` — `try_apply_elemental_debuff()` procs on hit; chance scales with attack stat. Each element has a unique debuff (burn, freeze, shock, etc.).
17. Elemental Traits: `elemental_traits.py` — `get_primary_element()`, `apply_trait()`, on-kill procs. Weapon traits are applied pre-damage.

### Engagement & Wedding System
18. 100 affection → propose with ring (from gift shop) → cap 200 → at 200 get Legendary soulbound wedding accessory (46 total, Bonded effects in party).
19. Fields: `engaged_girls`, `married_girls` in player save. `engaged`, `married` flags on each monster girl.

### Mount System
20. Player `mount_id` field. Mounts provide travel speed bonuses and combat passives.

### Daily Systems
21. Daily limits: `girl_talk_today`, `girl_gift_today`, `girl_daily_last_day` — reset each in-game day.
22. `daily_effects` / `event_queue` — date-based event system via `events.py`.

### Time-of-Day Difficulty
23. `get_time_period()` returns time period string. `get_difficulty_multiplier_from_time()` returns 1.0×–1.8× scaling based on in-game hour. Night is harder.

### Consumable Balance
24. `potion_sickness` — turns remaining on consumable cooldown, prevents potion spam.

### Thread Safety
25. GUI runs facilities/combat in background threads. Use `_tprint`/`_tpause`/`_tinput` or `c_print`/`c_input`. Never raw `print()`/`input()`.
26. End-of-Combat: `end_of_combat_cleanup()` must run on victory/flee/death to tick cooldowns, decrement buffs, clear weapon states. Also must call `clear_abyss_fang_state()` and `clear_captain_cutlass_state()`.

### Design Philosophy
27. Design-First: User may request design docs then later "implement it." Translate Limbus Company concepts: Clash→initiative, Coin→crit, Sanity→buffs, E.G.O→HP cost/cooldown.

## Common Pitfalls

- **HP calc:** Player uses `player_max_hp(player)`, allies use `ally["max_hp"]`. Mixed lists must branch.
- **Debuff display:** Bug usually in `./combat/combat_ui.py` `_get_entity_buff_tags`, not effect application.
- **Enemy data:** YAML only via `enemy_loader.py`. `minion_only: true` prevents superboss summons in random rooms.
- **Superboss hooks:** Signature `enemy_turn_hook(enemy, ctx, pl, p_con, defending)` must match across all modules. Extra state → `ctx`.
- **Ally defending:** Reset `defending_this_turn = False` at start of every ally turn.
- **Ally cooldowns:** `superboss_common.py` must tick ally cooldowns too.
- **GUI threading:** Never tkinter from background thread → use `after()` or I/O queues.
- **Wonderland:** `wl_` prefix for all Wonderland entities.
- **Chrysalis:** Set HP via `enemy["hp"] = new_value` for Paradox Fracture to apply.
- **Mary Sue Plot Armor:** 8 damage types each strip one stack max.
- **stat_rebalance.py:** Must run from workspace root.
- **Re-challenge lock:** `city_prog["max_floor"] <= floor` prevents superboss swap on re-clear.
- **Abyss Fang state:** Must clear via `clear_abyss_fang_state()` in `end_of_combat_cleanup()`. Abyssal Tempo stacks tick at round start via `tick_abyssal_tempo()`.
- **Captain Cutlass state:** 5 persistent fields in player (`cutlass_high_tide_stacks`, `cutlass_rally_cooldown`, `cutlass_riposte_count`, etc.). Must clear via `clear_captain_cutlass_state()`.
- **Elemental debuffs:** Check `elemental_debuffs.py` before adding new element interactions — proc chance scales with attack stat, not fixed.
- **Potion sickness:** Prevents consumable spam. Check `player["potion_sickness"]` before allowing potion use.
- **Time-of-day:** `get_difficulty_multiplier_from_time()` affects combat stats. Night encounters are 1.8× harder.
- **Save compatibility:** New fields MUST use `.setdefault()` in `ensure_player_fields()`. Test with old save files.

## Adding a Superboss (checklist)
1. Create `./combat/<name>.py` with `enemy_turn_hook(enemy, ctx, pl, p_con, defending)`
2. Add YAML entry in `./resources/enemies/`
3. Import in `./dungeon.py`
4. Add to tier pool in `./dungeon.py`
5. Use `./combat/superboss_common.py` for shared combat loop logic

## Adding a Persistent Field (checklist)
1. Add `.setdefault("field_name", default_value)` in `./character.py` `ensure_player_fields()`
2. Update any code that reads the field to handle the default gracefully
3. Test with both new and existing save files
