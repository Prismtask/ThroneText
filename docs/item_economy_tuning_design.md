# Item Economy & Rarity Tuning — Design (for review)

> **Status:** ✅ **Implemented (2026-10-18)** — decisions **D1–D7 locked** as recommended; Phases 1–2 shipped (value pricing, shop gating, drop curves, multiplicative enhance, fusion fee + elemental rescale, owned-item migration). Phase 3 = ongoing playtest tuning.
> **Related:** `docs/improvement_planning_guide.md` (process), `docs/ITEMS_OVERHAUL_BLUEPRINT.md` (shipped baseline), `docs/Pandemonium_Open_Improvements.md` (backlog).
> **Companion design:** `docs/compositional_equipment_design.md` (Form × Element × Grade — ships **after** this pass; user decision 2026-10-16).
> **Trigger:** player feedback (2026-10-16) — "new players can buy rares with starting money; legendary becomes a common drop in the endgame; enhancement/price/fusion all keyed to rarity has problems."
> **Rev 2 (2026-10-16):** value model revised using Elona as reference ([Equipment](https://elona.fandom.com/wiki/Equipment) / [Equipment/Technical](https://elona.fandom.com/wiki/Equipment/Technical)) — see Appendix A for what was adopted/adapted.
> **Rev 3 (2026-11-03):** the gold-level pacing pass ([`gold_economy_pacing_design.md`](./gold_economy_pacing_design.md)) replaced the scroll craft ladder (§3.6) with a value-derived ladder in v0.1.9.7; the enhance cost curve (§3.5) is kept (optional +10 capstone). The value formula (§3.1), multiplicative stat model (D2), and value-delta fusion fee (D6) are unchanged.
> **Rev 4 (2026-11-04):** sale prices now scale with the market index (`market_value = item_value × k(anchor)`, k 1.0–8.5) for shop, road-merchant and black-market pricing (v0.1.9.9). `item_value`, drops, and blacksmith services are unchanged.

---

## 1. Context — current numbers (verified against code)

| Lever | Today | Consequence |
|---|---|---|
| **Shop price** | `city_base (35–70) × price_mult (1.0/1.4/2.2/4.0/8.0)`; **item stats never enter the price** (`facilities/shop.py` stock gen) | Solmere: rare ≈ **99g, epic ≈ 180g, legendary ≈ 360g**. Start gold = 300 (100 base + 200 allowance) → rare day 1. A Legendary Iron Sword and a Legendary Inferno Greatsword cost the same. |
| **Shop stock rarity** | Normal bias `[30,32,22,12,4]`, higher `[15,25,28,20,12]`; **no progression gate** | ~28% chance of a legendary in an 8-slot daily stock; high-bias cities ~1.3 legendaries/day. |
| **Drops, endgame** | Lv30+ normal `[.06,.18,.28,.28,.20]`; Pandemonium `[.02,.06,.16,.36,.40]` (`dungeon.py _roll_equipment_drop`) | Normal ≈ 6% legendary **per kill**; Pandemonium ≈ **17% per kill**. Base item rolled uniformly from ~60 items → junk-base legendaries. |
| **Treasure rooms** | Floor 26+: `[.25,.50,.25]` rare/epic/legendary (`dungeon_rooms.py handle_treasure_room`) | Another legendary fountain; `_random_item_id()` uniform. |
| **Enhancement** | `+1 to every stat` per level (flat); cost `50 × price_mult × 1.5^n` (`facilities/blacksmith.py`) | Rarity's advantage erodes with enhance: legendary +10 = 19 STR vs common +10 = 15 STR (**1.27×**), while enhance costs 8×. Optimal play = enhance cheap bases. |
| **Fusion** | 4 same-rarity items + gold (2k/5k/12k/30k/80k) → scroll; apply fee flat **150g**; `apply_scroll_to_item` rebuilds `mods` but **not `elemental_dmg`/`elemental_res`** (`inventory.py`) | Fusion-upgraded items are permanently weaker than natural drops (trait scales with rarity, elementals don't). Outer loop bypasses per-step rarity enhance pricing. |
| **Sell price** | `12 × price_mult` flat (`facilities/shop.py`, 75% on the road) | Every legendary sells for 96g; identity worthless. |

**Root cause:** rarity is the only priced/rolled axis; item **base** (stats + element count) is invisible to prices, shops, drops, and fusion. The value curves disagree: price/upgrade cost ×1.4→×8, raw power ×1.0→×1.9, enhance flat.

## 2. Goals

1. Item base quality matters to **price, sell value, and stock/drop composition**.
2. Rarity keeps meaning across the whole curve: early rare = deliberate splurge, endgame legendary = chase (not a flood).
3. Enhancement stays the long-term gold sink but no longer erases rarity.
4. Fusion stays the endgame "put rarity on *my* base" loop, with consistent math.
5. No save breakage — the only migration is a one-time, idempotent recompute (Phase 2).

## 3. Proposed changes

### 3.1 Item value function (new, shared) — Elona-style multiplicative stack

Elona computes an item's worth as a multiplicative stack: *base value (per item type) × material value factor × quality, with enchantments adding value*. We adopt the same architecture, sized for our systems:

```
intrinsic_value(def) = Σ base_mods + max(0, element_count − 1) + special_premium
                       where element_count    = len(elemental_dmg) + len(elemental_res)
                             special_premium  = +1 per special property (con_defense, scaling_mult, …)  # tunable list

item_value(item)     = round( (intrinsic_value + enhance) × price_mult(rarity) )
                       price_mult = 1.0 / 1.4 / 2.2 / 4.0 / 8.0   # existing rarity ladder = our "value factor"
```

- **Everything the item *is* feeds its value:** base identity, enhance investment (Elona: enchantments add value — so ours no longer vanishes on resale), elemental profile, special properties. Rarity then multiplies the whole stack, the way Elona's material/quality factors do.
- Optional explicit override: a `"base_value"` field on an item definition (Elona's per-type Base Val) for designer-priced specials; when absent, the derived formula applies.
- Future affixes (see backlog) plug in as additional additive premiums — no formula redesign needed.
- Exposed as `intrinsic_value()` / `item_value()` in `resources/items.py` (single source for prices, sells, fusion fees, and base-tier caps).

| Example | intrinsic + enhance | rarity mult | item value |
|---|---|---|---|
| Iron Sword +0 (2 STR) | 2 | ×1.0 | **2** |
| Inferno Greatsword +0 (5 STR, 2 dmg → +1) | 6 | ×1.0 | **6** |
| Inferno Greatsword +10 | 16 | ×1.0 | **16** |
| Inferno Greatsword +0, legendary | 6 | ×8.0 | **48** |
| Inferno Greatsword +10, legendary | 16 | ×8.0 | **128** |
| Frost Blade +0 (6 stats, 2 dmg → +1), rare | 7 | ×2.2 | **≈15** |

### 3.2 Value-based pricing (buy + sell)

- **Buy:** `price = round(city_base × item_value / 4)` — `city_base` (35–70) stays the city dial; /4 keeps the average item near today's price level.
- **Sell (city):** `sell = round(2.5 × item_value × (1 + (cha − 8)/100))`; road = `1.9 × item_value × …` (preserves today's 12:9 city:road ratio). Selling now credits enhance + elemental richness, since they live inside `item_value`.

Worked examples (Solmere, city_base 45):

| Item | Common | Rare | Legendary | Legendary +10 |
|---|---|---|---|---|
| Iron Sword (value 2) | ≈23 | ≈45 | **≈180** | — |
| Inferno Greatsword (values 6/13/48/128) | ≈68 | ≈146 | **≈540** | **≈1440** |
| Sell price (Inferno Greatsword) | 15 | ≈33 | 120 | ≈320 |

Junk bases are cheap in every rarity; high-value bases cost real money in every rarity — and enhanced items are worth more than raw ones.

### 3.3 Shop stock rarity gating (progression)

Replace the two global weight sets with a **city tier** table (+ keep the existing `rarity_bias` for late cities):

| Tier | weighted [common, uncommon, rare, epic, legendary] | Applies to |
|---|---|---|
| Early | `[70, 26, 4, 0, 0]` | starter cities (Solmere, Elderfen, …) |
| Mid | `[45, 33, 18, 4, 0]` | mid-game cities |
| Late | `[25, 30, 28, 13, 4]` | late cities |
| Late (high bias) | `[12, 24, 30, 23, 11]` | cities currently flagged `rarity_bias: "higher"` |

- Implementation: add `shop_tier: "early"|"mid"|"late"` to city configs (`resources/cities.py`); keep `rarity_bias` as the late-city modifier.
- **D4 option:** additionally clamp by player progress (e.g. epic requires player level ≥ 12; legendary ≥ 20). Recommended: yes, soft clamp.
- **Cache:** bump the stock cache key (`shop_stock2_{city}`) so the first visit after the patch regenerates with new weights/values instead of waiting out the daily restock.

### 3.4 Drop curves — flatten legendary, shift to epic

**`dungeon.py _roll_equipment_drop` (normal):**

| Enemy level | weights |
|---|---|
| ≤5 | `[0.50, 0.34, 0.14, 0.02, 0.00]` |
| ≤10 | `[0.36, 0.36, 0.21, 0.06, 0.01]` |
| ≤20 | `[0.24, 0.31, 0.29, 0.13, 0.03]` |
| ≤30 | `[0.15, 0.25, 0.33, 0.21, 0.06]` |
| 30+ | `[0.11, 0.22, 0.34, 0.28, 0.05]` |

**Pandemonium** (keeps its generous identity, caps legendary at 10%): `≤5 [.18,.28,.30,.18,.06]` · `≤10 [.12,.22,.30,.28,.08]` · `≤20 [.07,.16,.29,.38,.10]` · `≤30 [.04,.11,.25,.50,.10]` · `30+ [.03,.08,.21,.58,.10]`.

**Travel mirrors** (`facilities/travel_events.py`, more conservative): `_combat_drop_rarity` → legendary max 4%; `_discovery_rarity` → legendary max 3%; `_merchant_stock_rarity` keeps its epic cap.

**Treasure rooms** (`dungeon_rooms.py`): `≤10 [.65,.33,.02]` · `≤25 [.45,.46,.09]` · `26+ [.30,.52,.18]`.

- **Base-tier caps (D3, recommended):** a base's `intrinsic_value` caps the rarity it can roll — `≤3 → max rare`, `4–5 → max epic`, `≥6 → full`. Applied to drops **and** shop stock **and** treasure rooms. This removes junk-base legendaries structurally and makes value pricing line up with what actually exists. (Trade-off: legendary fusion fodder now needs intrinsic ≥6 bases — re-check fusion pacing in playtest.) *Once the compositional system ships (later phase), these caps restate as grade caps: g1 → max rare, g2 → max epic, g3 → any.*

**Audit list of all roll sites:** `dungeon.py` (`roll_drop`, used by `wild_dungeons.py` too), `dungeon_rooms.py` (treasure + merchant stock), `travel_events.py` (`_combat_drop_rarity`, `_discovery_rarity`, `_merchant_stock_rarity`), `facilities/guild.py` (uses merchant stock rarity), `world_map_screen.py` (calls travel helpers). Black-market relic pricing (`450 × price_mult`) — align with value pricing in the same pass or defer, decision noted.

### 3.5 Enhancement — make it multiplicative (D2, recommended)

**Option A (recommended):** `stat = int((base_stat + enhance) × stat_mult)` — enhance *before* the rarity multiplier passes through. (Changed in `build_item`, `enhance_item`, `apply_scroll_to_item`.)

Inferno Greatsword (base 5 STR) examples:

| Rarity | +0 | +5 | +10 |
|---|---|---|---|
| Common (×1.0) | 5 | 10 | 15 |
| Rare (×1.35) | 6 | 13 | 20 |
| Legendary (×1.9) | 9 | 19 | **28** |

Costs unchanged (legendary +10 ≈ 68k vs common +10 ≈ 8.5k) → an 8× cost now buys a ~1.87× stat multiplier at every enhance level instead of converging to 1.27×.

**Migration:** one-time recompute of `mods` for all owned non-unique equipment (player equipped + inventory, allies, house storage/chest, wonderland bench) from `ITEMS[id].base_mods` + `enhance`; guard with `item_econ_migrated` flag; skip unknown ids defensively. Uniques untouched (they bypass the system).

**Option B (minimal-diff fallback):** keep flat `+1/stat`; flatten enhance cost to `50 × price_mult**0.5 × 1.5^n` (legendary +10 ≈ 24k vs common 8.5k) and accept convergence (19 vs 15). No migration. Recommended only if Option A playtests too strong.

### 3.6 Fusion & scrolls — consistency fixes

- **Elemental rescale (bug fix):** `apply_scroll_to_item` must rescale `elemental_dmg`/`elemental_res` with `1.0 + (val − 1.0) × stat_mult` (matching `build_item`), so a scrolled-up item equals a natural drop.
- **Apply fee = you pay for the value you're adding:** `fee = max(150, 50 × (new_value − old_value))` using §3.1 values, so enhance investment and elemental richness are automatically part of the delta — no separate enhance term to tune. Examples: common→rare Inferno Greatsword: Δ7 → 350g · common→legendary +10 Inferno Greatsword: Δ112 → 5,600g · common→legendary Iron Sword: Δ14 → 700g.
- Keep: no downgrade, uniques immutable, craft cost ladder (2k/5k/12k/30k/80k), "4 same-rarity" requirement.
- With §3.4 flattened, fusion becomes the *targeted* legendary route — expected but re-check pacing in playtest.

## 4. Decisions (LOCKED 2026-10-18 — implemented as recommended)

| # | Decision | Options | Recommendation |
|---|---|---|---|
| D1 | Value formula & constants | Elona-style stack: (intrinsic + enhance) × rarity value factor; explicit `base_value` override | As specced (§3.1) |
| D2 | Enhancement model | A: multiplicative + migration · B: flat + flatter cost | **A**, fall back to B if playtest shows power creep |
| D3 | Base-tier rarity caps | none · caps by `value` in drops+shops+treasure | **Yes**: ≤3 → rare, 4–5 → epic, ≥6 → all |
| D4 | Shop gating | tier-only · tier + player-level clamp | **Tier + clamp** (epic ≥ lv12, legendary ≥ lv20) |
| D5 | Drop caps | legendary 5% normal / 10% Pandemonium at 30+ | As specced (playtest dial) |
| D6 | Fusion fee & rescale | keep 150g flat + no rescale · value-delta fee + rescale + recompute existing scrolled items | **Value-delta fee + rescale + recompute** (same migration pass) |
| D7 | Sell constants | 2.5 city / 1.9 road (× item_value, which already includes rarity) | As specced (playtest dial) |

## 5. Implementation plan — shipped 2026-10-18

**Status:** Phase 1 ✅ · Phase 2 ✅ · Phase 3 = ongoing playtest tuning.
**Key helpers:** `intrinsic_value()` / `item_value()` / `cap_rarity_for_item()` / `fusion_fee()` in `resources/items.py`; shop stock cache is now `shop_stock2_{city}`; the one-time rescale is guarded by `item_econ_migrated`.

**Phase 1 — tuning (no migration):**
- `resources/items.py`: `intrinsic_value()` / `item_value()` (multiplicative stack incl. enhance/element/special premiums + optional `base_value` override).
- `facilities/shop.py`: value pricing (buy via stored base at stock gen), sell price, tier weights, cache-key bump.
- `resources/cities.py`: `shop_tier` per city.
- `dungeon.py`, `dungeon_rooms.py`, `travel_events.py`: weight tables + caps + treasure table.
- Tests: weight sums = 1.0; price/sell worked examples; early-city gating sample (10k rolls → zero epic/legendary); new-game affordability (cannot afford rare in early cities).

**Phase 2 — math + migration:**
- `resources/items.py` + `facilities/blacksmith.py` + `inventory.py`: Option A formula, fusion fee, elemental rescale.
- `character.py`: `item_econ_migrated` one-time recompute (mods + elementals for non-unique equipment, all storage locations).
- Tests: enhance table (§3.5), fuse fee examples, migration idempotency; read-only migration sim against `savefile/savegame_1.json` (pattern: `tests/_temp_upgrade_save_migration_sim.py`).

**Phase 3 — playtest & ship:**
- Playtest checklist (below); adjust dials; changelog bullets under the current version (bump per `version.py` procedure); update this doc's status to implemented.

## 6. Playtest checklist

- [x] New character: early shops show no epic/legendary; rare is a visible-but-unaffordable splurge.
- [x] Mid-game: first purchased rare feels earned; sell values feel fair for junk vs good bases.
- [x] Endgame normal: legendary cadence feels like a chase (~1 per 50–70 kills); epics are the workhorse.
- [x] Pandemonium: still generous, legendary ≈ 1 per 20–25 kills, not a slot machine flood.
- [x] Junk-base legendaries gone (or explicitly cheap) — no "Legendary Iron Sword" at full price.
- [x] Enhancement: legendary +10 feels clearly better than common +10 and worth its cost.
- [x] Fusion: target-a-base legendary route paced reasonably; scrolled item == natural drop (compare stat lines).
- [x] Selling an enhanced/legendary item returns a fair value-scaled price (no more flat 96g legendaries).
- [x] Fusion fees scale sanely with the upgrade bought (cheap junk hops, expensive legendary hops).
- [x] No save errors; sample old save loads with recomputed items.

## 7. Explicitly NOT changing

- Unique items (fully bypass rarity/economy), consumable pricing & Potion Sickness, the 60/40 equip/consumable drop split, drop *chance* (50% / 70% Pandemonium), fusion's no-downgrade rule, road merchants' epic cap, wonderland-only / black-market-only item handling.

---

## Appendix A — Elona reference notes (reviewed 2026-10-16)

Sources: Elona+ wiki [Equipment](https://elona.fandom.com/wiki/Equipment) and [Equipment/Technical](https://elona.fandom.com/wiki/Equipment/Technical).

### Adopted

- **Multiplicative value stack:** Elona item worth ≈ *base value (per item type) × material value factor × quality*, with enchantments adding value. → Our §3.1: `(intrinsic + enhance) × rarity value factor`, one number driving buy prices, sell prices, fusion fees, and base-tier caps.
- **Enchantments are part of value:** Elona's attributes (EncPow formulas for stats/resists/crit/etc.) contribute worth; our enhance investment + elemental profile now do too, so resale no longer ignores them.
- **Quality ⇒ attributes, not just bigger numbers:** Elona quality gates *how many/strong* random attributes an item receives. Our rarity already scales traits/elements; future affixes (backlog) should follow the same pattern.
- **Naming signals identity:** Elona material/quality adjectives ("glowing bronze sword") ≈ our elemental prefix convention (Ember/Blaze/Inferno — already shipped).
- **Value-derived vendor pricing:** Elona prices come from intrinsic item value and vendors stock by value tables — mirrored by our §3.2–3.3 (value-priced stock/sells).

### Adapted with care (deliberate divergences)

- Elona **quality is immutable** (only material changes via scrolls); our Scroll of Fusion changes rarity. We keep fusion but price it by **value delta** (§3.6) so it can't shortcut the economy.
- Elona's material system (DV/PV, damage dice, weight/value factors per material) is a much deeper stat architecture than ours. **Not adopting materials now** — base identity + element + rarity already cover the axes. Revisit only if a materials-layer feature is ever prioritized (the `base_value` override is the hook).

### Noted for possible future layers

- Unidentified loot with ID-on-carry / Sense Quality (Elona) ≈ our backlog's "Unidentified loot" idea.
- Alias/name re-rolling items (Elona's scroll of name).
- Explicit per-type base value tables (our `base_value` override covers specials; full tables only if needed).
