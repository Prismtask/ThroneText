# Titles & Deeds — Design (locked v1)

**Status:** ✅ Phases 1–3 + casino titles (Phase 4) IMPLEMENTED 2026-11-06 — D1–D12 locked. Optional Phase 4 items (title trials, trophy hall, ally titles) remain.
**Date:** 2026-11-03
**Scope:** Unlockable deed titles, **one equipped at a time**, small passive effects (combat and out-of-combat), a `Name the [Title]` honorific, a Titles Journal tab, and swapping rules — including the "can I swap at a dungeon rest?" question.
**Related docs:** [`Pandemonium_Open_Improvements.md`](./Pandemonium_Open_Improvements.md) §3 · [`improvement_planning_guide.md`](./improvement_planning_guide.md) · [`karma_system_design.md`](./karma_system_design.md) (single standing score / discount precedent) · [`time_system_design.md`](./time_system_design.md) (travel blocks) · [`family_system_design.md`](./family_system_design.md) · [`quest_system_design.md`](./quest_system_design.md) · [`enemy_ai_behaviors_design.md`](./enemy_ai_behaviors_design.md)
**Reference:** classic RPG "deed title" systems (Elona/Fable-style honorifics) — **mechanics inspiration only**; every name, condition, and value here is original.

> **Design goal:** turn existing achievements into *identity choices*. A title is a small, legible bonus plus a line of flavour on the character sheet — never a second equipment grid, never a hidden mandatory power spike.

---

## 0. Summary

- **Deeds unlock titles permanently.** Titles are derived from things the player already does: bestiary defeats/captures, superboss kills, guild contracts, quests, house/family growth, Karma, Event Horizon clears, travel.
- **One title equipped at a time.** Unlocks are a collection; the equipped title is an identity/roleplay choice.
- **Name prefix:** `Aria the Dragon-Slayer` — computed for display only, **never** written into `player["name"]`.
- **Effects are small and budgeted:** mostly out-of-combat utility (discount, travel, upkeep, bounty pay, capture, XP), with tightly capped combat stats. Effects never stack — one title is active.
- **Free swapping at safe points** (city, house, camp, dungeon/Event Horizon post-room menu) — the same places Inventory is already open. Locked during combat.
- **No hidden effects on equippable titles.** Every locked title appears as `???` with a hint (and progress when countable); name and effect are revealed on unlock. A visible drawback is preferred over an invisible one.
- **Persistence:** `player["titles_unlocked"]`, `player["title_active"]`, `player["title_stats"]`, `player["titles_version"]` via `ensure_player_fields()`; old saves backfill from existing state.
- **UI:** Inventory → Journal → **Titles** sub-tab (6th), plus a title line on the character sheet and the party card.

---

## 1. Player experience

1. A deed completes (e.g. a 10th Dragonkin kill, a 50th honoured contract, a first Event Horizon clear).
2. `titles.check_unlock(player, event=...)` unlocks any matching title and writes a `[TITLE]` Journal entry (no toast — Journal + session log only, per project convention).
3. The player opens **Inventory → Journal → Titles**, sees the collection (Equipped / Unlocked / `???`), and equips one.
4. The character sheet and party card show `Aria the Dragon-Slayer`; the single equipped title's effects apply everywhere.
5. The player may swap freely at any safe point. Combat blocks swaps.

Terminal mode is not supported for title management — Inventory management is already GUI-only (same as equipment).

---

## 2. Design principles

1. **Legibility first.** Every equippable title states its effect; a reward the player cannot evaluate is a reward they cannot choose.
2. **Identity, not power.** A title is one small passive + flavour. If a title is mandatory for a build, it is too strong.
3. **Deed → title, never title → deed.** Titles do not gate quests, story, or content; they are the receipt for something already done.
4. **Monotonic progression.** Unlocks are permanent and never revoked by death, ascension, Karma drift, or a save migration.
5. **No invisible effects.** See §7 for the endgame-title answer.

---

## 3. Data model

### 3.1 Registry — `resources/titles.py`

```python
TITLES = [
    {
        "id": "roadwarden",
        "name": "Roadwarden",
        "epithet": "the Roadwarden",      # full-name suffix
        "compact": "Roadwarden",          # tight-width form
        "tier": 1,                        # 1..4 (budget, see §5)
        "category": "travel",
        "hint": "Walk the roads until they know your stride.",
        "requires_rule": None,            # e.g. "karma_enabled"
        "condition": {"all": [
            {"type": "deed_stat", "key": "travel_segments", "count": 25},
        ]},
        "effects": {"travel_time_pct": 0.05},
        "description": "The roads remember who walks them.",
    },
]
```

**Rules:**
- Data-only definitions; no callables in the registry (saves/mods/schema validation stay simple).
- `epithet` includes the article (`the Dragon-Slayer`) so titles that do not take one (e.g. `First Blood`) can omit it.
- **All locked titles render as `???`** with their hint — the registry needs no hidden flag; the reveal happens on unlock.
- `requires_rule` may name any Game Rules id from `character.GAME_RULES` (`karma_enabled`, `family_enabled`, future toggles). When that rule is off, the title shows "Unavailable — <rule> disabled", is skipped by unlock checks, and cannot be equipped.

### 3.2 Player state

Added in `character.py::ensure_player_fields()`:

```python
player.setdefault("titles_unlocked", {})     # {title_id: {"day": int, "seen": bool}}
player.setdefault("title_active", None)      # title_id | None
player.setdefault("title_stats", {           # monotonic deed counters only
    "gold_spent_shops": 0,
    "travel_segments": 0,
    # floors_cleared is derived from city_floors max_floor (no counter)
})
player.setdefault("titles_version", 1)
```

- **`player["name"]` is never modified.** Save-slot listing, dialogue token substitution, and ally matching keep working unchanged.
- `title_stats` exists only for deeds the game does not already track. Everything already tracked is read in place:
  - `player["bestiary"][key]` → `defeated`, `captured`, `regions` (`bestiary.py`)
  - `player["defeated_superbosses"]` (`dungeon.py::_record_superboss_defeat`)
  - `player["bounties_completed"]` / `player["high_bounties_completed"]` (`facilities/guild.py`)
  - `player["city_floors"]` (max floor per city), `player["quests"]` flags, `player["houses"]` levels, `player["children"]`
  - `player["karma"]` (when enabled)

### 3.3 Condition types

All conditions are **AND** within one dict; use `{"any": [...]}` for alternatives and `{"all": [...]}` for explicit grouping.

| Type | Fields | Reads |
|---|---|---|
| `flag` | `flag` | top-level story flag or `player["quests"]["flags"]` |
| `quest` | `quest_id` | `player["quests"]` completion state |
| `bestiary` | `race` \| `key`, `field` (`defeated`/`captured`), `count` | `player["bestiary"]` |
| `superboss` | `count` and/or `boss_id` | `player["defeated_superbosses"]` |
| `bounty` | `count`, `high` (bool) | `player["bounties_completed"]` / `high_bounties_completed` |
| `house_level` | `level` | max `player["houses"][*]["level"]` |
| `children` | `count` | `len(player["children"])` |
| `karma` | `at_least` / `at_most` | `karma.get_karma` (requires Karma enabled) |
| `level` | `level` | `player["level"]` |
| `eh_room` | `count` | `player["event_horizon"]["best_room"]` |
| `bestiary_fraction` | `fraction` | recorded Bestiary entries vs. `get_total_enemy_count()` |
| `deed_stat` | `key`, `count` | `player["title_stats"]` |
| `all` / `any` | list of conditions | composition |

### 3.4 Helpers — `titles.py`

| Helper | Purpose |
|---|---|
| `ensure_state(player)` | Idempotent field setup (called by `ensure_player_fields`) |
| `check_unlock(player, event=None)` | Evaluate registry conditions; unlock matches; write Journal entries |
| `reconcile(player)` | Backfill unlock every title whose condition already holds (login/load; guarded by `titles_version`) |
| `get_active(player)` | Return the equipped title dict or `None` |
| `can_swap(player)` | `False` in combat / scripted scenes; see §6 |
| `equip_title(player, title_id)` / `unequip_title(player)` | Validate unlock + swap rules; set `title_active` |
| `format_name(player, style="full")` | `"Aria the Dragon-Slayer"` / `"Aria (Dragon-Slayer)"` / `"Aria"` |
| `mod(player, key, default=0)` | Read one numeric effect from the active title |
| `format_effect_line(title)` | Shared display string for the Journal card and character sheet |

**Effect reads go through `mod()` only** — never read `title_active` and the registry inline at a hook site.

---

## 4. Name display

### 4.1 Display styles

| Style | Output | Use |
|---|---|---|
| `full` | `Aria the Dragon-Slayer` | character sheet, city hero card, Journal, dialogue tokens |
| `compact` | `Aria (Dragon-Slayer)` | party card, combat turn order, tight labels |
| `plain` | `Aria` | save browser, session log, damage lines, internal matching |

- `format_name()` returns the base name when no title is equipped, so every call site can adopt it unconditionally.
- **Never** edit `player["name"]`, save metadata, or dialogue token substitution logic. `dreams.py` / `house_stories.py` `{player}` tokens can call `format_name()` where prose wants the honourific (Phase 2).
- Width guard: the combat HUD party column is 31 chars and enemies 33. Titles use `compact` there; if the combined string exceeds the column, fall back to `plain` automatically inside `format_name(style="compact")` (same fallback discipline as ally names).

### 4.2 Display surfaces (Phase 1 vs later)

| Surface | File | Phase | Style |
|---|---|---|---|
| City hero card | `gui/screens/city_screen.py` (`members.append({"name": p["name"]})`, ~L498) | 1 | full |
| Dungeon party card | `gui/screens/dungeon_screen.py` (~L1205) | 1 | compact |
| Character sheet Title line | `gui/screens/inventory_screen.py` Stats tab | 1 | full |
| Combat turn order / flash label | `gui/screens/combat_screen.py` (~L592, ~L867, ~L1422) | 2 | compact |
| Combat HUD name row | `combat/combat_ui.py` (~L451) | 2 (or plain) | compact |
| Level-up messages | `leveling.py` (~L264, ~L285) | 2 | full |
| Tutorial / facility prose | `facilities/tutorial.py`, `facilities/house_stories.py` | 2 | full |
| Save browser | `save_load.py` `list_save_slots` | never | plain |

### 4.3 Settings toggle

`gui/settings.py` gets `"show_title_beside_name": True` (Settings → Display). When off, every style returns `plain`. This is the escape hatch for narrow windows / accessibility, and it also future-proofs localization width problems.

---

## 5. Effects & budget

### 5.1 Tier budgets

| Tier | Deed difficulty | Utility budget | Combat budget |
|---|---|---|---|
| **T1** | early / easy / first-time | ≤ 3% on one axis | none |
| **T2** | mid-game or a repeatable grind | ≤ 5% | +1 attribute **or** ≤ 2% damage |
| **T3** | hard (superbosses, deep floors, long quests) | ≤ 8% | +2 attribute **or** ≤ 4% damage |
| **T4** | endgame / completionist | ≤ 10% | +2 attribute **or** ≤ 4% + one utility effect (may carry a **visible** drawback) |

A title may spend its budget on one utility effect, one combat effect, or a small pair — never more.

### 5.2 Effect catalog & hook sites

| Effect key | Meaning | Hook site (single source) | Hard cap |
|---|---|---|---|
| `shop_discount_pct` | extra % off city shops / forge / temple | `facilities/shop.py::get_discounted_price` (add before the existing clamp) | +10% |
| `black_market_pct` | Black Market price shift | `facilities/black_market.py::_karma_price` | +10% |
| `travel_time_pct` | fewer travel blocks | `time_blocks.py::travel_blocks` (single source for block cost) | 10% |
| `bounty_gold_pct` | guild bounty payout | `facilities/guild.py` payout site | +10% |
| `upkeep_pct` | monthly bills | `facilities/monthly_billing.py` | −10% |
| `xp_pct` | XP gain | `leveling.py::gain_exp` | +5% |
| `capture_pct` | capture chance | `combat/capture.py` | +5% |
| `rest_heal_pct` | camp watch-shift healing | `facilities/camp.py` | +20% |
| `gold_find_pct` | room / dungeon gold | room reward payout (`dungeon.py` / `dungeon_rooms.py`) | +10% |
| `casino_payout_pct` | extra % of the stake added to winning casino payouts | `casino.py` payout site | +1% |
| `combat_stat` | +N to one attribute | `combat/stats.py::get_effective_attribute` (player only) | +2 |
| `damage_pct` | outgoing damage | basic attacks (`combat/player_actions.py`) + skills (`combat/skills.py`) | +4% |
| `crit_pct` | crit chance | stat/crit pipeline (`combat/stats.py`) | +3% (Phase 2) |

**Travel:** apply the title once in `time_blocks.travel_blocks()` to the **final block cost** — the documented single source of truth — not to raw minutes (a 2–3% minute cut rarely survives the 30-minute ceil). Journeys of 4+ blocks always save at least one block. Do **not** also inject it into `facilities/pathfinding.py`; mount/ship reductions already live there, and a second application would double-dip.

**Shop:** add the title term beside the Charisma + Karma terms inside `get_discounted_price()`, before its `min(70, ...)` clamp and before event discounts/surcharges. Charisma can already reach 40%, Karma ±20%; the title stays ≤10% and the shared clamp still wins.

**Combat:** `get_total_attribute` is shared by the player and ally pipelines — branch on the player identity (`actor is player` / the player dict), and never touch `combat/ally.py` totals in v1. All combat title effects are player-only (D8).

### 5.3 Stacking & anti-exploit rules

- Exactly one title is active; effects never stack with each other.
- Titles never grant: extra actions/turns, free captures, guaranteed flee, item duplication, quest/story flags, level-cap raises, or resurrection.
- Titles never bypass gates (city Karma gates, curse floors, Wonderland rules, Event Horizon rules).
- RNG-gated deeds give **flat, lower-tier** effects — never top-tier power behind a dice roll.
- Death, party wipes, ascension, and Karma drift never remove an unlock. A title whose condition is Karma-based stays unlocked permanently once earned (the effect is static, not condition-rechecked).
- No title may reduce a price below the existing `get_discounted_price` floor of 1 gold; clamps are applied at the hook, not in the registry.

---

## 6. Title swapping — the dungeon-rest question

### 6.1 Options considered

| Option | Verdict |
|---|---|
| **A. Swap anytime, anywhere (even mid-combat)** | ❌ Rejected — hidden mid-fight power changes; impossible to display honestly. |
| **B. Swap only at safe points** (city, house, camp, dungeon/EH post-room menu) | ✅ **Recommended** — matches equipment swapping exactly. |
| **C. Rest-only** (inn / house bed / camp — not the post-room menu) | ❌ Rejected — stricter than gear for no balance gain (see 6.2). |
| **D. Cost per swap** (gold fee / time block) | ❌ Rejected for v1 — friction with no exploit to close; Wonderland time is frozen, so a time cost would be inconsistent. |

### 6.2 Recommendation (D3, locked)

**Free, instant swapping at any safe point where Inventory is already open.**

- The dungeon post-room menu (`dungeon.py` "Continue / Inventory / Stats / Save and quit", wild dungeons, Event Horizon) and the camp (`facilities/camp.py`) already expose the full Inventory screen — players can currently swap weapons, armor, and accessories there for free. Titles are *less* impactful than gear (capped at +2 stats / 4% damage), so restricting titles while gear swaps freely would be inconsistent and player-hostile.
- "Dungeon rest" is therefore **allowed**. So is a boss-floor post-room menu: gear is already swappable there, and the player can only swap to a title they have already earned.
- No time-block cost: swapping is an identity change, not an action; charging time would make title experimentation feel like a tax and would behave differently in Wonderland (frozen time) than elsewhere.

### 6.3 Guardrails

- **Not during combat.** Inventory is not reachable from the combat screen; additionally, `titles.equip_title()` defensively refuses when `player.get("wedding_combat_active")` is true (the flag `begin_wedding_combat()` sets on every standard combat start in `combat_engine.py`). If a generic `player["combat_active"]` flag is introduced later, switch the guard to it.
- **Not during scripted scenes / multi-step facility flows** that temporarily hand control to the player mid-scene (same rule as other menu panels: the UI simply is not available).
- **No cost, no cooldown, no confirmation** for a normal swap; confirm only when replacing a title would visibly lower a stat (optional polish).
- Unequipping to "no title" is always allowed (clean look, no buff).
- The swap is logged in the session log (`Title equipped: Dragon-Slayer.`); no Journal entry for swaps (Journal is for unlocks).

---

## 7. Locked-title reveal policy (D5)

**Verdict: do not hide the effect of an equippable title.** It discourages more than it challenges.

Why:
- The player cannot evaluate the reward → they either ignore the system or look it up online, which spoils the mystery anyway.
- After a hard grind, a blind choice reads as the game withholding the payoff.
- "Challenge" is execution and decisions; hidden numbers remove decisions instead of adding difficulty.

What to do instead:
1. **Hide the hunt, not the payoff.** Every locked title shows as `???` with its hint and, when countable, progress (e.g. `Defeated 3 / 10`). On unlock, the name and effect are revealed in full. This applies to all titles, not just endgame ones (D5).
2. **Once unlocked, show the exact effect and numbers.** Vague wording is acceptable only in the locked card's hint; the unlocked card/tooltip must state the exact values.
3. **Use a visible drawback** for the endgame flex title: e.g. `Worldbreaker` — `+2 all attributes, −10% shop discount`. That creates a real choice without hiding information.
4. **Reserve true mystery for cosmetics/lore.** A `???` cosmetic title or a lore-puzzle title with clues in the Journal is fine; it never affects stats.
5. **Free respec makes experimentation cheap.** Because swapping is free (§6), players can test titles; hidden effects would still be bad, but visible tradeoffs become fun instead of punishing.

---

## 8. Title catalogue (design reference)

### Implemented titles (Phases 1–3 + casino + Wonderland — 31 total)

| # | Title | Tier | Deed | Effect | Phase |
|---|-------|------|------|--------|-------|
| 1 | **First Blood** | T1 | Defeat 10 enemies | +1% XP | 1 |
| 2 | **Trailblazer** | T1 | Complete 10 travel segments | −2% travel time | 1 |
| 3 | **Bargain Hunter** | T1 | Spend 2,500 gold in shops | +2% shop discount | 1 |
| 4 | **Pathfinder** | T1 | Clear 5 dungeon floors | +2% dungeon gold | 1 |
| 5 | **Delver** | T2 | Clear 25 dungeon floors | +3% dungeon gold | 1 |
| 6 | **Roadwarden** | T2 | Complete 25 travel segments | −3% travel time | 1 |
| 7 | **Haggler** | T2 | Spend 10,000 gold in shops | +3% shop discount | 1 |
| 8 | **Beast-Tamer** | T2 | Capture 25 monster girls | +3% capture chance | 1 |
| 9 | **The Hundred** | T2 | Defeat 100 enemies | +3% XP | 1 |
| 10 | **Dragon-Slayer** | T2 | Defeat 10 Dragonkin | +1 Strength | 2 |
| 11 | **Contracted** | T2 | Complete 50 guild bounties | +5% bounty gold | 2 |
| 12 | **Hearthkeeper** | T2 | House level 3 + a child (Family on) | −5% monthly bills | 2 |
| 13 | **Honest** | T2 | Reach 80 Karma (Karma on) | +5% shop discount | 2 |
| 14 | **Unrepentant** | T2 | Reach −75 Karma (Karma on) | +5% Black Market discount | 2 |
| 15 | **Stormbreaker** | T3 | Defeat 3 superbosses | +2 Strength | 3 |
| 16 | **Abyss Walker** | T3 | Reach Event Horizon room 50 | +6% XP | 3 |
| 17 | **Collector** | T4 | Record 80% of the Bestiary | +2 Learning, +5% XP | 3 |
| 18 | **Worldbreaker** | T4 | 9 superbosses + Event Horizon room 50 | +2 all attributes; **drawback:** −10% shop discount | 3 |
| 19 | **First Page** | T4 | See the Voss epilogue (`voss_epilogue_seen`) | +10% rest healing | 3 |
| 20 | **The Gambler** | T2 | Win 100 casino hands or record a 4,000g biggest win | +1% casino payouts | 4 |
| 21 | **Sleight-Hand** | T2 | 10 casino cheats never caught | +3% Black Market discount | 4 |
| 22 | **Marked** | T2 | 3 casino cheats caught | +5% Black Market discount; **drawback:** −5% shop discount | 4 |
| 23 | **Curiouser** | T1 | Enter Wonderland (`wonderland_visited`) | +1% XP | Wonderland |
| 24 | **Tea-Party Guest** | T1 | See the Hatter's three-guest scene after Floor 10 | +3% rest healing | Wonderland |
| 25 | **Shadow-Touched** | T2 | Accept a Wonderland Shadow (`wonderland_shadows_taken` ≥ 1) | +2% damage | Wonderland |
| 26 | **Heartsbane** | T2 | Defeat the Queen of Hearts (Floor 10) | +3% dungeon gold | Wonderland |
| 27 | **Wolf-Hunter** | T2 | Defeat the Big Bad Wolf (Floor 20) | +1 Strength | Wonderland |
| 28 | **Witch-Breaker** | T3 | Defeat the Wicked Witch (Floor 30) | +6% XP | Wonderland |
| 29 | **Vorpal Hand** | T3 | Defeat the Jabberwock (Floor 40) | +4% damage | Wonderland |
| 30 | **Author's Bane** | T4 | Defeat Mary Sue (Floor 50) | +2 Learning, +4% XP | Wonderland |
| 31 | **Happily Ever After** | T4 | Resolve all three Wonderland heroine arcs | +1 all attributes | Wonderland |

Notes on the Wonderland set:
- One title per story beat: entry, the tea party, the Floor 41 Shadow choice, each of the five floor bosses, and the three-heroine capstone.
- `Shadow-Touched` reads a lifetime `title_stats["wonderland_shadows_taken"]` counter (incremented in `wonderland_curses.trigger_shadow_choice`) because the active `wonderland_shadows` list resets between cycles. `titles.ensure_state()` backfills the counter from a save that is already carrying Shadows.
- **Happily Ever After** requires the three permanent-heroine flags (`wonderland_heroine_redhood_permanent`, `wonderland_heroine_dorothy_permanent`, `wonderland_heroine_alice_permanent`), so late arcs and normal arc resolutions both count.

### Future titles (not yet implemented)

| Title | Deed (condition) | Tier | Effect |
|---|---|---|---|
| **the Twice-Bound** | any quest chain fully completed (`quests` flags) | T2 | +2% XP |

Notes:
- The three casino titles are implemented (rows 20–22); Marked is the T2 criminal-reputation exception — it trades a shop-discount penalty for underworld standing.
- All three casino titles show the casino record line (hands won / biggest win / cheats unseen / caught) on locked and unlocked cards.
- Karma titles are skipped when Karma is off; they never appear as permanently locked (shown as "unavailable — rule disabled").
- Worldbreaker is the only T4 title with a **visible drawback**.
- Future titles must fit the §5 tier budgets; there is still no stacking beyond the single equipped title.

---

## 9. UI

### 9.1 Inventory → Journal → Titles (6th sub-tab)

- `gui/screens/inventory_screen.py::_refresh_journal_tab()` already builds a sub-notebook (Bounty / Main Quest / Side Quest / Event / Dreams). Add a **Titles** tab.
- The header also shows collection milestone tracking (5 / 10 / 15 titles) — UI only, no stat stacking.
- Each title card shows:
  - unlocked cards: name + epithet, tier badge, category icon, effect line via `format_effect_line()`, and **Equipped / Unlocked** state;
  - locked cards: `???`, tier badge, category icon, hint, and progress when countable (`Defeated 3 / 10`, `Honoured contracts 12 / 50`); name and effect stay hidden;
  - gambling titles may add a **record line** from the registry's `record` key (`Hands won: N · Cheats unseen: N · Caught: N`), shown locked or unlocked;
  - **Equip** (or **Unequip**) button; disabled in combat (`can_swap`).
- The equipped card is pinned at the top; the rest sorted by tier then name.
- Empty state: "No titles yet — deeds will find you."

### 9.2 Character sheet

Add a small **Title** LabelFrame in the Stats tab (above Attributes, beside the existing Profession line in Skills): active title name, effect line, and a hint that it can be changed in the Journal.

### 9.3 Unlock notification

- Journal entry: `{tag: "[TITLE]", name: "Title unlocked — the Dragon-Slayer", desc: effect + deed}` using the `player["journal"]["events"]` shape (`karma.add_journal` precedent); trim to 200 entries like Karma does.
- **No toast** (standing project decision for quest/dispatch-style flows). A session-log mirror is deferred: unlocks can happen inside combat/facility threads, where the Journal is the guaranteed surface.

### 9.4 Party card / combat

- City hero card and dungeon party card use `format_name(...)`.
- Combat HUD keeps fixed widths: `compact` with automatic `plain` fallback inside the 31-char player column.
- Enemy names, damage lines, and log parsing never include titles.

---

## 10. Unlock pipeline

### 10.1 Event hooks (call `titles.check_unlock(player)`)

| Event | Hook site |
|---|---|
| Enemy defeated | `bestiary.record_defeat` (already called by combat) |
| Enemy captured | `bestiary.record_capture` / `combat/capture.py` |
| Superboss defeated | `dungeon.py::_record_superboss_defeat` |
| Guild bounty turned in | `facilities/guild.py::_record_bounty_completion` |
| Quest completed | `quests.py` completion path |
| House upgraded / child born | `facilities/house.py`, `family.py` |
| Floor / run cleared | `dungeon.py` run completion (also increments `title_stats["floors_cleared"]`) |
| Travel segment completed | `time_blocks.spend_travel_segment` (increments `travel_segments`) |
| Shop purchase | `facilities/shop.py` purchase path (increments `gold_spent_shops`) |
| Karma tier crossed | `karma.change_karma` (Karma titles only) |
| Event Horizon clear | existing EH clear flag setter |
| Casino hand settled / cheat resolved | `casino.finish_hand` / `casino._record_cheat` (mirror counters, then `check_unlock`) |
| Wonderland entered | `facilities/arcane_tower.py::_enter_wonderland` |
| Tea-party / guest scene advanced | `wonderland_guests.on_inn_enter` |
| Wonderland Shadow accepted | `wonderland_curses.trigger_shadow_choice` (`note_deed`) |
| Wonderland heroine made permanent | `combat/ally.py::set_heroine_state` |
| Wonderland floor boss defeated | `dungeon.py::_record_superboss_defeat` (already covered) |

### 10.2 Backfill / reconcile

- `titles.reconcile(player)` runs **once per `titles_version`** at character load (`ensure_player_fields` or the load path) and in `check_unlock`.
- It evaluates every condition against existing state, unlocks matches, and writes Journal entries. This is how old saves get titles they already earned (`defeated_superbosses`, `bestiary`, `bounties_completed`, etc.).
- Reconcile is strictly additive and idempotent: no unlock is ever removed; `titles_version` only guards the backfill pass, not future event checks. Titles with a disabled `requires_rule` are skipped entirely (not unlocked, not shown as earnable).
- `title_stats` counters start at 0 for old saves; deeds that only have counters (shop spending, travel segments, floors cleared) backfill from available history where cheap (e.g. `city_floors` max floors) and otherwise start counting from the update — note this in the changelog. The four casino counters are backfilled from the existing lifetime `player["casino"]` stats.

### 10.3 Performance

- `check_unlock` evaluates only titles not yet unlocked; the registry is small (~31 entries). No per-frame work.
- Journal writes are capped/trimmed like Karma's event log.

---

## 11. Balance guardrails

- **One active title.** No set bonuses, no collection-wide passives in v1 (a small "collection milestones" layer can be a later phase; it must not stack with the equipped title's budget).
- **Hard caps** from §5.2 are enforced at the hook site, not just in the registry.
- **Player-only** in v1. Extending combat titles to allies later requires the actor-based convention (see skill: unique equipment pattern) and a separate budget review.
- **No snowball:** titles must not increase the rate at which other titles are earned (e.g. no "+% capture" stacked with "+% capture" — only one title anyway) and must not trivialize shop/economy loops (10% cap).
- **Difficulty fairness:** don't scale title power by the game's difficulty *setting* (it is display-only today: `character.py GAME_RULES`, `implemented: False`). Scale by the deed's tier. When the difficulty system ships, titles remain unaffected to avoid "farm titles on Story" exploits.
- **Save safety:** all fields are `.setdefault()`-safe; old saves load and reconcile without mutation of `name`, equipment, or existing ledgers.

---

## 12. Phases

### Phase 1 — Core loop ✅ IMPLEMENTED 2026-11-03 (v0.1.9.3)
- `resources/titles.py` registry (9 T1–T2 titles).
- `titles.py` helpers: state, conditions, `check_unlock`, `reconcile`, `mod`, `format_name`, `format_effect_line`.
- `character.ensure_player_fields()` fields + old-save backfill.
- Unlock hooks: bestiary defeat/capture, superboss, bounty, floor clear, travel segments, shop spending.
- Effects: `shop_discount_pct`, `travel_time_pct`, `xp_pct`, `capture_pct`, `gold_find_pct` (all player-side).
- UI: Journal → Titles tab; Stats-tab Title line; city hero card + dungeon party card names; settings toggle.
- `tests/_diag_titles.py` passes.
- Changelog + README/wiki; version bumped.

### Phase 2 — Combat & economy ✅ IMPLEMENTED 2026-11-03 (v0.1.9.4)
- Combat `combat_stat` / `damage_pct` integration (player-only) + HUD compact names.
- `bounty_gold_pct`, `upkeep_pct`, `rest_heal_pct`, Black Market hook.
- More titles (Dragon-Slayer, Contracted, Hearthkeeper, Honest, Unrepentant); `[TITLE]` Journal entries polished.
- Tuning pass against Charisma/Karma/mount caps.

### Phase 3 — Endgame & collection ✅ IMPLEMENTED 2026-11-03 (v0.1.9.5)
- T3–T4 titles: Stormbreaker, Abyss Walker, Collector, Worldbreaker (visible drawback), First Page.
- New conditions: Event Horizon depth, Bestiary completion fraction, and quest-flag reads.
- Title-aware NPC greeting variants (`karma_dialogue.title_line()`), shown when entering a city service.
- Collection milestone **tracking** (5 Acknowledged / 10 Renowned / 15 Legendary) shown in the Titles tab; intentionally no stat stacking.

### Phase 4 — Optional expansion
- Title trials/quests that unlock specific titles (reuses `quests.py` hooks).
- Trophy Hall / house display integration.
- Ally titles (separate budget + actor-based integration).
- ✅ Casino titles — **The Gambler**, **Sleight-Hand**, **Marked** — + record lines (implemented 2026-11-06; see `casino_games_design.md`).

---

## 13. Pre-flight checklist (per `improvement_planning_guide.md` §4)

- [ ] **Persistence:** `titles_unlocked`, `title_active`, `title_stats`, `titles_version` in `ensure_player_fields()`; old-save load + reconcile tested read-only first.
- [ ] **Notifications:** Journal + session log only; no toasts from facility/combat threads.
- [ ] **Threading:** Titles UI is main-thread (InventoryScreen); any facility-side unlock call uses `_tprint`-safe paths and does not touch tkinter.
- [ ] **Local imports:** no branch-local imports of names used elsewhere (`tests/_diag_local_imports.py`).
- [ ] **Combat parity:** combat effects player-only; no ally stat changes; no combat-loop state to clear. Name display respects HUD widths.
- [ ] **Rewards:** XP via `leveling.gain_exp`; no direct XP writes.
- [ ] **Display:** effect line formatter shared between Journal card and character sheet; `format_name` never mutates data.
- [ ] **Version/changelog:** bullet under the current version; bump only per `version.py`.

---

## 14. Verification

- `tests/_diag_titles.py`:
  - registry sanity (unique ids, valid tiers, effect keys known, caps within limits);
  - condition evaluation for every type against synthetic players;
  - `reconcile` idempotence and additive-only behavior;
  - `format_name` styles + width fallback;
  - effect clamps (shop total, travel floor, combat stat cap);
  - casino title backfill, unlocks, record lines, and Marked's visible drawback;
  - old-save load path (no `name` mutation, no crash on missing fields).
- Manual playtest:
  - unlock a title, see the Journal entry, equip it, verify the name on city/character sheet;
  - swap at city, camp, and dungeon post-room menu;
  - verify no Inventory/title access during combat;
  - save/reload; old save smoke test;
  - settings toggle off → names revert to plain.
- Run `tests/_diag_version_consistency.py` if the version is bumped.

---

## 15. Decisions

| ID | Decision | Status |
|---|---|---|
| **D1** | Exactly one equipped title. | ✅ Locked (request) |
| **D2** | Name honourific `Name the [Title]`, computed for display only; `player["name"]` never mutated. | ✅ Locked (request) |
| **D3** | Free, instant swapping at safe points (city/house/camp/dungeon post-room menu); no time/gold cost; combat locked. | ✅ Locked |
| **D4** | Effect caps: utility ≤10%, combat ≤+2 stats / 4%; one title only; no ally effects in v1. | ✅ Locked |
| **D5** | All locked titles show `???` with a hint (and countable progress); unlocked/equippable titles always show their full effect; visible drawbacks preferred over hidden effects. | ✅ Locked |
| **D6** | Unlocks are permanent per save (stored in the save file, never account-wide) and backfilled on load via reconcile. | ✅ Locked |
| **D7** | No Game Rules toggle for titles in v1 (effects are small and non-destructive). | ✅ Locked |
| **D8** | Combat title effects are player-only in v1. | ✅ Locked |
| **D9** | Titles UI lives in Inventory → Journal → Titles (6th tab), not a new city facility. | ✅ Locked |
| **D10** | Swap logging: session log only; Journal only for unlocks. | ✅ Locked |
| **D11** | `requires_rule` may reference any Game Rules toggle; titles whose rule is disabled show "unavailable — rule disabled", are skipped by unlock checks, and cannot be equipped. | ✅ Locked |
| **D12** | `title_stats` counters are the only new tracking; existing bestiary/bounty/superboss/house data is read in place. | ✅ Locked |

---

## 16. Answers to the two open questions (summary)

**"Can the player change titles anytime, even at dungeon rest?"**
Yes — at any safe point where Inventory is already open (city, house, camp, dungeon/Event Horizon post-room menu). It is free and instant, exactly like changing gear there. Combat and scripted scenes block it. Restricting it further adds friction without closing any exploit, because gear — which is stronger — is already freely swappable in those same menus.

**"Should endgame titles hide their effect for challenge?"**
No. Hidden effects discourage players (they cannot evaluate the reward, so they ignore it or spoil it online) and remove decisions instead of adding difficulty. Hide the *hunt* (`???` + hint before unlock), reveal the effect on unlock, and use **visible drawbacks** when an endgame title needs a trade-off.
