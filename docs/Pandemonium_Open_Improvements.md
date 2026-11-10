# Pandemonium — Open Improvements & Ideas (Living Backlog)

> **Living document** — unlike [`TerminalRPG_Improvement_Opportunities.md`](./TerminalRPG_Improvement_Opportunities.md) (kept as a historical record), this list is meant to be **updated as items ship**. Cross out / remove finished entries; add new ones freely.
>
> **Before implementing anything here, follow [`improvement_planning_guide.md`](./improvement_planning_guide.md):** verify it doesn't already exist → classify & evaluate → design doc → pre-flight checklist. Priority below is gut-feel triage only.

**Status key:** Priority = High / Medium / Low (impact×effort×risk, rough). "Builds on" = the existing systems the idea should extend instead of replacing.

---

## 0. Already proposed / in flight — read before proposing these

| Work | Status |
|------|--------|
| **Rarity / Grade / Enchantment rework (B+C)** | ✅ Implemented 2026-10-20 — grade/tempering retired; base forms + flower infusion (3 weapon slots, trait ladders, res tiers); rarity/enhance stats-only; v4 migration. `rarity_grade_flower_audit.md` §12.10. |
| **Item Economy Tuning** | ✅ Implemented (2026-10-18) — Phase 3 playtest tuning ongoing |
| **Compositional Weapons (Form × Element × Grade)** | ✅ Implemented 2026-10-18 |
| **Compositional Armor & Accessories** | ✅ Implemented 2026-10-19 (grid; perks deferred) |
| **Equipment Form Perks (D-G / D-J)** | ✅ Implemented 2026-10-19 — 10 static archetypes, all equipped slots (4, or 5 with the Beating Root), uniques included via form tags. Test: `tests/_diag_form_perks.py`. |
| **Generic Catalog Retirement (D-L)** | ✅ Implemented 2026-10-19 — all non-unique gear generated; 12 non-coordinate nouns kept in `LEGACY_ITEMS`; owned gear migrated (formula v3) |
| **Tempering & Flowers (D-K)** | ❌ Superseded 2026-10-20 by the flower infusion rework — tempering retired; flowers now set elements/traits. See `rarity_grade_flower_audit.md` §12. |
| **Scroll ↔ Grade Ceiling (D-M)** | ❌ Superseded 2026-10-19 by D-N — scrolls are uncapped; soft grade ceiling + shop floor + Forge Commission shipped (`rarity_grade_flower_audit.md` §11) |
| **Dungeon Form Identity** | 📝 Proposal in `compositional_equipment_design.md` §10 — biome-weighted form pools, not implemented |
| **D-RES: resistance convention inversion (bug)** | ✅ Fixed 2026-10-18 (runtime rating inversion) |
| **The Thumb** (human syndicate faction) | Design only, decisions open — `docs/thumb_faction_design.md` |
| **The Father of Thirst** (vampire questline) | Proposal / for review, no code — `docs/father_of_thirst_questline.md` |
| **Items Overhaul Blueprint** | ✅ Implemented (verified 2026-10-16) — was listed here by mistake from a stale doc header; only ongoing balance tuning remains |
| **Wonderland heroine quests** | ✅ Implemented 2026-10-27 — seven Journal side quests (way-in guide, entry arc, floor/finale arc, Alice/Red Hood/Dorothy arcs); ✅ staged guest pacing + baseline boss variants shipped 2026-11-08 — see `docs/wonderland_heroine_rework.md`. Playtest/balance tuning remains. |
| **Fireside Tales (house storybook)** | ✅ Implemented 2026-10-27 — 8 multi-part arcs; gates on girls/affection/designated allies/marriage/house level/flags/defeated superbosses; Skylume city-triggered arc; see `docs/house_stories_design.md` |
| **Family System (bed events, pregnancy, true-born children)** | ✅ **Phases 1–4 implemented 2026-10-30 (v0.1.9.1)** — Attunement Shared Night, full per-girl night lines for all 56 capturable girls + heroines, pregnancy/birth, 15/40/60 growth, daughter bond UI with race/mother pools, no-romance guards, dispatch/ascension/awakening gates, Father's Legacy combat passives, Voss & Lumen “The First Page” epilogue, written-mode prose variants, README/wiki/changelog. `tests/_diag_family.py` passes; manual playtest pending. Docs: `docs/family_system_design.md`; codex amended |
| **Dream Events (sleep boons / burdens / choices / story)** | 📝 Proposal for review — `docs/dream_events_design.md` (2026-10-29); decisions D1–D8 open; registry-driven, reuses StoryScreen/facility UI |
| **Casino / tavern games** | ✅ Phases 1–3 implemented 2026-11-06 — inn tables + Black Market back room + cheating/blacklist in both games + suited cards + casino titles/record lines; `tests/_diag_casino.py` passes. Optional third game/TAVERN tiles/README/wiki remain. `docs/casino_games_design.md` |
| **Karma & moral choices (single standing score)** | 🚧 Phase 0–3 implemented 2026-10-29 (v0.1.8.7); **City Favor removed in v0.1.8.8** — `karma.py`, final Game Rules toggle, Karma-only shop/bills/Tax Day, Karma-scaled guild bounties, Black Market inverse + outlaw crate, event choices + Forgotten Shrine, 4-way capture + house-full, city top-bar Karma, Prescript Debt rename, city gates/guards/jail, temple contrition, guild atonement contracts, hallucination shift, Karma-tier dialogue, travel moral event, Blackwake smuggler fare, inventory Karma section, README/wiki. Wonderland-specific Karma content deferred. Playtest pending. `docs/karma_system_design.md` |
| **Titles & deeds** | ✅ Phases 1–3 + casino titles implemented 2026-11-06 — `docs/titles_design.md`. Twenty-two T1–T4 titles: shop, travel, XP, capture, dungeon gold, bounty gold, upkeep, Black Market, player-only combat stat/damage, and the three casino titles (The Gambler / Sleight-Hand / Marked with shared record lines); endgame Stormbreaker/Abyss Walker/Collector/Worldbreaker/First Page; Journal → Titles tab, `Name the [Title]` display, locked `???` + hint/progress, visible drawbacks, free swaps at safe points (incl. dungeon rest), HUD compact names, title-aware service greetings, old-save backfill, `tests/_diag_titles.py` passes. Optional Phase 4 (trials/trophy hall/ally titles) pending. |
| **The Joker** (Event Horizon arcana) | Implemented 2026-10-09 — playtest pending |

## 1. Combat Depth

| Priority | Idea | Description |
|----------|------|-------------|
| Medium | **Elemental reaction matrix** | Codify reactions between existing elemental debuffs (e.g. Frozen + heavy physical = shatter bonus). Builds on `combat/elemental_debuffs.py`. |
| Medium | **Battle objectives** | Optional per-room goals (survive N rounds, protect a guest, no consumables) for bonus loot. Builds on `dungeon_rooms.py` room pattern. |
| Medium | **Generic counter/riposte** | High-DEX counterattacks for all actors, beyond Captain Cutlass's crew riposte. Builds on stat milestones + evasion. |
| Low | **Stealth approaches** | Enter dungeon rooms in stealth to avoid or ambush encounters. Builds on trap/stat-check room checks. |

## 2. Dungeon & Exploration

| Priority | Idea | Description |
|----------|------|-------------|
| High | **Floor / run modifiers** | Rolled per-run modifiers ("Rich", "Cursed", "Overgrown"…) that change enemies, loot, and hazards. Builds on wild dungeon themes + difficulty multipliers. |
| Medium | **Secret floors** | Chance-based hidden stairs to bonus floors with unique enemies and loot. |
| Medium | **Mimics** | Rare treasure rooms that fight back. Builds on existing treasure rooms. |
| Medium | **Floor completion tracking** | % explored per floor with completion rewards. The ASCII exploration map already tracks visited rooms. |
| Low | **Light / torch resource** | Dark floors that reduce accuracy/ambush you unless light sources are used. Interacts with shops + item slots. |
| Low | **Lore fragments** | Findable documents feeding the codex (see Bestiary below). |

## 3. Progression & Advancement

| Priority | Idea | Description |
|----------|------|-------------|
| High | **Class specialization branches** | Branching paths per class at a milestone (e.g. Ranger → Deadeye / Beastmaster) with exclusive skills. Distinct from masteries and barracks tiers; builds on the class skill system. |
| ✅ Phases 1–3 | **Titles & deeds** | Deed-based titles granting small passives + a `Name the [Title]` honourific, one equipped at a time. **Phases 1–3 + casino titles shipped 2026-11-06** — `docs/titles_design.md`; optional Phase 4 expansion remains. Builds on bestiary, guild contracts, superboss flags, quests, house/family state, and casino records. |
| Medium | **Class trial quests** | Quest-runtime trials that unlock specialization/ultimate skills. Reuses `quests.py` hooks. |
| Medium | **Secondary class kit** | Multiclass-lite: later unlock of a subset of another class's skills. Balance via cooldowns/slots. |
| Low | **Prestige / rebirth** | Post-cap reset for permanent perks. Mind the naming clash — "Ascension" already means level-cap raises; also interacts with the awakening economy. |

## 4. Allies, House & Romance

| Priority | Idea | Description |
|----------|------|-------------|
| ✅ Shipped | **House storybook (Fireside Tales)** | Multi-part romance/lore arcs read at home, gated by household size, affection, marriage, house level or quest flags; some trigger in cities instead. `docs/house_stories_design.md` |
| High | **Heroine quest continuation** | More heroine-quest chapters beyond the shipped Wonderland arcs (Alice, Red Hood, Dorothy). Quest runtime + hooks are ready. |
| Medium | **Affection upkeep** | Gentle neglect/decay loop to keep the house relevant between visits — with guardrails (caps, opt-in, no punishing spiral). Nothing exists today. |
| Medium | **Combat moods** | Dispatch already has moods; extend to combat (small buffs/debuffs + chat lines per mood). |
| Medium | **Gift crafting** | Craft personalized gifts from dungeon materials instead of only buying them. Builds on Herbalist/gift shop + crafting materials. |
| Medium | **Duo skills** | Paired finishers with a bonded/married girl when both are in the party. Resonance-adjacent. |
| Low | **House decor** | Furnish the house with decorations and trophies (see Trophy Hall in §6). |

## 5. Equipment & Items

| Priority | Idea | Description |
|----------|------|-------------|
| High | **Equipment set bonuses** | Named sets with 2/4/6-piece thresholds. Must be designed around the fusion/enchant economy (see blacksmith anti-exploit rules). |
| High | **Random affixes** | High-rarity drops roll 1–3 affixes ("of the Bear", "of Embers"). Interacts with the open Items Overhaul Blueprint. |
| Medium | **Sockets & gems** | Socketable gems for customizable stats; Arcane Tower forge adjacency. |
| Medium | **Loadout presets** | Save/equip gear sets ("dungeon DPS", "city social") with one action. |
| Medium | **Shop item comparison** | Show equipped-vs-new stat line next to shop items (none exists today). |
| Medium | **Alchemy bench** | Brew potions/elixirs from herbs + materials; extends Herbalist. Respect potion-sickness balance. |
| Low | **Off-hand slot / dual wield** | New weapon slot(s) with a full balance pass. |
| Low | **Unidentified loot** | Drops roll "Unidentified"; reveal at the Arcane Tower or via scrolls. The README already advertises an identify service — no code path exists today. |
| Low | **Transmog** | Appearance overrides while keeping stats. |

## 6. City Facilities & Services

| Priority | Idea | Description |
|----------|------|-------------|
| High | **Bank / treasury** | Deposit gold to protect it, city-to-city representation. Builds on the existing house chest precedent. |
| Medium | **Arena / colosseum** | Repeatable wave & boss-rush mode for the mid-game with a time-of-day schedule. Reuses barracks sparring + EH boss-rush patterns. |
| Medium | **Tavern hirelings** | Temporary generic adventurers for one run — distinct from monster girls. Must respect the resonance party-cap system. |
| Medium | **Stable & mount progression** | Expand mounts beyond Trade Hall purchases: care, training, rare mounts, traits. |
| ✅ Phases 1–3 | **Casino / tavern games** | Inn tavern tables + Black Market back room + cheating/blacklist in both games (blackjack removes the latest card) + suited cards + The Gambler / Sleight-Hand / Marked titles with record lines implemented; EV-negative by design; pot/net caps + 12 hands/day + 1 block/hand. Optional third game/TAVERN tiles/README/wiki remain. [casino_games_design.md](./casino_games_design.md) (2026-11-06). |
| Low | **Trophy hall** | Display superboss trophies in the house for tiny collection perks. |
| Low | **Auction house** | Rotating consignment stock (single-player, save-based). |

## 7. World, Travel & Events

| Priority | Idea | Description |
|----------|------|-------------|
| High | **Weather system** | Per-biome, per-day weather affecting travel (speed/risk) and combat (elemental shifts). Hooks into daily events, time blocks, and travel events. |
| Medium | **Naval encounters expansion** | Ships already exist and pirates are travel events — expand into sea-monster/pirate battles and ship upgrades. Blackwake adjacency. |
| Medium | **Landmarks & discovery** | Discoverable world-map points granting small permanent bonuses. The world-map canvas exists. |
| Medium | **Seasonal festivals** | Multi-day scheduled festivals with unique shops/enemies/buffs. Builds on the daily event system. |
| Low | **World event layer** | "A dragon has been spotted near Elderfen" → temporary special dungeon or roaming world boss. |
| 📝 Proposed | **Crime & guards** | Expanded into the Karma system: crimes lower global Karma; low Karma triggers gate fees, guard confrontations, and jail; high Karma lowers prices and taxes. See `docs/karma_system_design.md` (2026-10-29). |

## 8. Economy & Trade

| Priority | Idea | Description |
|----------|------|-------------|
| ✅ Phases 1–3 | **Gold economy pacing** | Shipped: Phase 1 (house cap + 5-day bank; value-derived scrolls, v0.1.9.7), Phase 2 (Blacksmith reforge, v0.1.9.8), Phase 3 (market index `k`, v0.1.9.9). Playtest tuning remains. See `docs/gold_economy_pacing_design.md` (2026-11-03). |
| Medium | **City demand cycles** | Supply/demand modifiers for the cargo trade (buy-low/sell-high exists; add elasticity + event-driven spikes). |
| Medium | **Investments** | Stake gold in city businesses for periodic returns with risk. Trade Hall adjacency. |
| Medium | **Loans & debt** | Borrow from a shady lender; failure spawns debt-collector encounters. Black Market adjacency. |
| Low | **Item insurance** | Pay to recover equipment after a defeat. |
| Low | **Additional properties** | Own more than one house/property; income and perks per city (deeds are one-per-player today). |
| Low | **Crafting for resale** | Crafted goods fetch a premium (ties into alchemy + Trade Hall). |

## 9. Narrative, Codex & Completion

| Priority | Idea | Description |
|----------|------|-------------|
| High | **Bestiary & codex** | Log encountered enemies → stats, weaknesses (elemental system exists), lore. Journal infrastructure + enemy YAML are ready. |
| Medium | **NPC rapport** | Track relationships with key NPCs for discounts and new dialogue. Builds on `city_dialogue.py`. |
| Medium | **Lore library** | Collectible books/fragments unlock codex entries; worldbuilding docs already exist. |
| Low | **Epilogue / legacy recap** | Post-main-story summary generated from your save (choices, allies, records). |

## 10. Quality of Life

| Priority | Idea | Description |
|----------|------|-------------|
| High | **Auto-save** | Optional saves after floor clears / city changes / travel. Save browser exists; use the existing atomic-write pattern. |
| Medium | **Statistics & records** | Total kills, gold earned, floors cleared, deaths, favorite skill — a "Records" view. Nothing tracked today. |
| Medium | **Inventory sort & filter controls** | User-selectable keys (rarity/slot/stat) + search over the existing grouped lists. |
| Medium | **Accessibility pack** | Text scaling, colorblind palettes, reduced motion/flashing. Settings screen exists. |
| Medium | **Training dummy analytics** | Per-skill/ally DPS report extending the dummy + sim harness. |
| Low | **Character sheet export** | Markdown/HTML character summary (wiki generator adjacency). |

## 11. Enemies & Bosses

| Priority | Idea | Description |
|----------|------|-------------|
| ✅ Shipped | **Enemy AI behaviors (regular enemies)** | Non-superboss enemies now choose between basic attacks, single-target skills, AoE skills, heals and AoE heals. Kits come from race + level, with healer name keywords and per-enemy YAML overrides; behavior escalates by level tier. Enemies also have attacker/supporter roles, and dungeon/Event Horizon spawns mix those roles by depth (max 2 supporters, always ≥1 attacker, no lone healers). See `docs/enemy_ai_behaviors_design.md`. |
| High | **Elite spawn prefixes** | Generalize elite variants ("Elite", "Corrupted", "Ancient") with scaled rewards. Pairs naturally with floor modifiers. |
| Medium | **Boss practice & refight** | Refight defeated bosses for reduced/no rewards. EH boss rush covers the endgame; this targets the rest. |
| Low | **Enemy ecology events** | Select rooms where two enemy groups fight each other and can be exploited. |
| Low | **Regular-enemy summoners** | Spawning archetype outside boss kits (Broodmother-style, generalized). |

## 12. Technical & Content Pipeline

| Priority | Idea | Description |
|----------|------|-------------|
| Medium | **Mod support** | Load custom enemies/items/races from a `mods/` folder. Data is already YAML; needs schema validation + load order. |
| Medium | **Balance regression suite** | Grow the `tests/_temp_*_check.py` scripts into a maintained per-system suite run before releases. |
| Low | **Localization scaffolding** | Externalize strings (large effort — phase it if ever pursued). |
| Low | **Challenge seeds & local leaderboard** | Weekly fixed-seed runs with local records. |
| Low | **Save-format versioning doc** | Document the save schema + migration conventions (migrations exist in code, undocumented). |

---

## Top 10 shortlist

If picking the highest-impact next steps:

1. **Bestiary & codex** — maximum completion value for low content cost (Journal + YAML already exist).
2. **Floor / run modifiers** — biggest variety-per-effort gain for dungeons.
3. **Class specialization branches** — replayability; the skill systems are ready to build on.
4. **Equipment set bonuses** — build variety; makes loot decisions interesting again.
5. **Auto-save** — cheap, high-value safety net.
6. **Elite spawn prefixes** — multiplies existing enemy content with one system.
7. **Weather system** — ties travel, combat, and daily events together.
8. **Random affixes** — loot excitement; design around the enchant/fusion economy.
9. **Bank** — economy QoL with an existing pattern (house chest) to extend.
10. **Heroine quest continuation** — content pipeline the quest runtime already supports.

---

*To promote an idea: run it through `docs/improvement_planning_guide.md` §1–3, write/lock a design doc if non-trivial, then implement in phases and update this list when it ships.*
