# Gold Economy & Pacing — Design (for review)

> **Status:** ✅ **Phases 1–3 shipped (v0.1.9.7–v0.1.9.9).** Phase 1 = house/scroll pacing; Phase 2 = reforge; Phase 3 = market index. D9–D12 shipped. Playtest tuning ongoing.
> **Related:** [`item_economy_tuning_design.md`](./item_economy_tuning_design.md) (item-level prices/rarity), [`improvement_planning_guide.md`](./improvement_planning_guide.md) (process), [`time_system_design.md`](./time_system_design.md) (day/block math), [`Pandemonium_Open_Improvements.md`](./Pandemonium_Open_Improvements.md) (backlog).
> **Supersedes in part:** `item_economy_tuning_design.md` §3.6 craft-cost ladder is replaced by a value-derived ladder (shipped v0.1.9.7). The §3.5 cost curve is reviewed and kept (with an optional +10 capstone). The value formula (§3.1), the multiplicative stat model (D2), and the value-delta fusion fee (D6) stay unchanged.
> **Trigger:** 2026-11-03 playtest observation — *"enemy drops 10–40g early where items cost 200–450, which is fair; but at endgame the main income comes from the player house, and the main gold sinks are scroll crafting and legendary enhancement."*

---

## 1. Verdict

| Phase | Grade | Why |
|---|---|---|
| Early (F1–10) | **8.5/10** | Kill gold vs item prices is well matched; shop gating and drop curves work. Keep this as the reference curve. |
| Mid (F11–25) | **7.5/10** | Multiple faucets; the house is still small; first epic/legendary sinks appear. |
| Late/Endgame (F26+) | **5/10** | Passive income grows to ~35–40% of a farming day; the only large sinks are one-time (scroll + enhance) and stop existing at gear cap; price scales diverge. |
| **Overall** | **7/10** | The item-level economy is sound. This pass fixes the gold-level pacing. |

**Diagnosis:** faucets grow with floor and house level; drains are finite and mostly one-time; the house's progress multiplier was uncapped. The fix is **not** "make the house worthless." It is to restore **active play as the primary faucet**, give **passive income a small, capped share**, and add **one repeatable endgame drain**.

**Mapping to the 2026-11-03 observation**

| Observation | Root cause | Fix |
|---|---|---|
| Early drops vs item prices feel fair | — | Keep unchanged (reference curve). |
| Endgame main income is the player house | House income scales 60× across upgrades and the floor multiplier was uncapped (P1/P7) | Cap the floor multiplier and the income bank (5 days); no hidden upkeep. |
| Main gold sinks are scrolls + legendary enchant | Both are one-time and stop at cap; scroll uses a second price scale; enhance has a value cliff (P2/P3/P4) | Value-priced scrolls, repeatable reforge, +10 capstone. |
| Selling/gear feels irrelevant at endgame | Item value does not scale with level; kill gold does (P9) | Level-scaled market index `k(level)` applied at the pricing layer. |

---

## 2. Verified current numbers

### 2.1 Faucets

| Source | Formula (code) | Notes |
|---|---|---|
| Kill gold | `level*8 + rand(5,15)`; boss ×2.5 + rand(20,40); Pandemonium ×2.5 + rand(30,60); 25% chance ×1.6 (`dungeon.py:roll_gold_drop`) | ~+15% EV from the bonus roll |
| Floor payout | ~22–25 enemies/floor; `advance_time(60)` per room → 10 h/floor; 24 blocks/day → **2.4 floors/day** | Boss floors add 1,400–2,500 |
| Item selling | `2.5 × item_value × CHARISMA` (`facilities/shop.py:_sell_price`) | ~2% of endgame daily income |
| House | `income_per_day × city_mult × max(1.0, max_floor/3)`; banked 10 days (`facilities/house.py:_pending_income`) | 8→480/day base; city 0.7–1.6× |
| Bounties | `kills × level × rand(8,12) × karma × tightness` (`facilities/guild.py`) | ~doubles kill gold while active |
| Dispatch | `25+10×top` … `40+14×top` per 18–36 h mission (`facilities/dispatch.py`) | Hundreds/day |
| Wild completion | `level × floors × 25` (`dungeon.py:_wild_victory`) | One-time per ruin |
| Event Horizon | `Σ(10+2r)` × entropy weight (`event_horizon.py:compute_payout`) | ~1–2k/run; relic faucet, not gold |
| Quests | 80–1,000 per quest (`resources/quests.py`) | One-time |

### 2.2 Drains

| Sink | Cost | Repeatable? |
|---|---|---|
| Enhance | `50 × price_mult × 1.5^n`; cumulative common +5 ≈ 990 · rare +7 ≈ 5,300 · epic +8 ≈ 14,800 · legendary +10 ≈ **68,000** | No — caps by rarity (+5 … +10) |
| Scroll craft | **2,000 / 5,000 / 12,000 / 30,000 / 80,000** + 4 same-rarity items (`facilities/arcane_tower.py:_scroll_craft_cost`) | No — one-time per item |
| Fusion fee | `max(150, 50 × Δvalue)` (`resources/items.py:fusion_fee`); common→legendary +0 ≈ 2,100; +10 ≈ 5,600 | One-time per item |
| House | 600→50,000 per level; **~98,100 total** + 500 deed | No — caps at Sanctuary |
| Arcane blessings | 250–25,000 (`facilities/arcane_tower.py`) | Yes, but small |
| Ships/mounts | 100–4,000 + 20–100/month upkeep (`resources/ships.py`, `resources/mounts.py`, `facilities/monthly_billing.py`) | One-time + tiny recurring |
| Inn/potions/temple | Tens to hundreds | Yes, but trivial at endgame |

### 2.3 The scale mismatch

A **legendary Inferno Greatsword +10** (intrinsic 6, value 128):

| Channel | Price |
|---|---|
| Sell to shop | **320g** |
| Shop buy (city_base 70) | **2,240g** |
| Black-market relic (`450 × value / 4`) | **14,400g** |
| Enhance +0→+10 | **68,000g** |
| Scroll craft to *make* it legendary | **80,000g** + 4 legendary items |

The same object is 320g, 2,240g, 14,400g, 68,000g, and 80,000g depending on which system asked. The item pass fixed the first three; the last two were explicitly kept.

### 2.4 Income share by phase (house fully upgraded for the floor)

| Floor | Active gold/day | House gold/day | House share |
|---|---|---|---|
| F10 | ~8k | 175 (Manor) | 2% |
| F20 | ~13k | 650 (Villa) | 5% |
| F30 | ~19k | 3,000 (Palace) | 16% |
| F40 | ~25k | 9,600 (Sanctuary) | **39%** |
| F50 | ~30k | 12,000 (Sanctuary) | **40%** |

The house share rises because housing income grows 60× across the upgrade track (8→480) while dungeon gold grows ~4× over the same floors. That is the "endgame income is the house" feeling, exactly.

---

## 3. Target model

**Principles**

1. **Active play is the primary faucet.** In an active day, ≥70% of gold earned should come from things the player did.
2. **Passive income is a dividend, not a salary.** Passive income ≤15% of an active day's income at every phase.
3. **Every phase has a repeatable drain.** Gold must never become a score.
4. **One value system.** Anything that prices an item **for sale** uses `market_value()` (intrinsic value × `k(level)`); power-based services (fusion, reforge, scroll, enhance) use `item_value()` or flat costs. No third scale.
5. **No hidden taxes.** The displayed daily rate is the amount paid; the multiplier cap is the balance lever.

**Budget table**

| Phase | Floor | Active gold/day | Passive income target | Primary sinks |
|---|---|---|---|---|
| Early | 1–10 | 2–8k | ≤500 (≤8%) | rare gear, house T1–3, consumables |
| Mid | 11–25 | 8–18k | ≤1.5k (≤10%) | epic gear, house T4–6, blessings |
| Late | 26–40 | 19–25k | ≤2.5k (≤12%) | legendary enhance, scrolls, house T7–8 |
| Endgame | 41+ | 25–35k | ≤3k (≤12%) | **reforge**, cosmetics, maxed gear |

**Payback rules**

- **House upgrade:** ≥20 active days of income (storage/girls/rest are separate value).
- **Gear sink:** 2–6 active days per item at the tier where it unlocks.
- **Repeatable reforge:** 0.2–0.5 active days per roll (2–5 rolls/day at endgame).

### 3.1 Item market index `k(level)` — agreed 2026-11-03

Measured loot share falls from ~14% at L3 to ~2.4% at L42 because kill gold scales linearly while item value barely moves. The fix is not a global currency cut; it is a **level-scaled market index** on item prices.

**Anchor (D9, locked):** `anchor_level = max(player level, highest max_floor across cities)`. Enemy level is **not** used — random high-level spawns must not move the market index.

**Combined per-kill budget:** `T(level) = kill_gold(level) + loot_sell(level)`. Hold the early share (~14% at L3) and rise to 20% at L42, then:

```
anchor_level   = max(player level, highest max_floor)
k(anchor)      = clamp(target_share(anchor) / measured_loot_share(anchor), 1.0, 8.5)
market_value   = item_value(item) × k(anchor)
buy_price      = city_base × market_value / 4
sell_price     = 2.5 × market_value × CHARISMA
kill_gold_new  = kill_gold_old − (k(anchor) − 1) × loot_sell_per_kill(anchor)
```

**Implementation table** (linear interpolation between bands):

| Level | ≤5 | 10 | 20 | 30 | 42+ |
|---|---:|---:|---:|---:|---:|
| `k` | 1.0 | 2.5 | 4.5 | 6.0 | 8.4 (cap 8.5) |
| Loot/kill (measured) | 6.3 | 6.8 | 7.5 | 9.2 | 9.8 |
| Kill-gold offset | 0 | −10 | −26 | −46 | −73 |

- **Pricing layer only.** `intrinsic_value()` / `item_value()` keep their current meaning for rarity caps and drop logic. `market_value` is a separate helper.
- **Buy and sell use the same `k`.** Otherwise buy-resell arbitrage opens up; `sell/buy` stays ~0.14–0.29 at every level.
- **Subtract the offset after the 25% bonus roll** (before the min-8 floor), so the expected total stays constant. Boss/Pandemonium multipliers must not amplify it.
- **Early game untouched:** `k = 1.0` for level ≤5; the ramp starts at L5 (D12, locked).
- **Pricing-only (D10, locked).** `market_value` applies to shop buy/sell and black-market pricing. Fusion, reforge, scroll and enhancement stay on `item_value()` or flat costs — Phase 1/2 already tuned them in absolute gold, and a literal ×k would make legendary reforge 16k, scroll 134k and enhancement 571k at L42. Services become relatively cheaper as loot income rises, which is the intended gentle direction.
- **Pandemonium** has 2.5× kill gold but only ~1.9× loot; its post-`k` share is lower (~13% vs 20%). **Accepted (D11, locked).**

**Verification:** the kill-gold offset must be derived from a 200k-kill sim per band and re-derived whenever drop tables change. `tests/_diag_gold_economy.py` prints the table.

---

## 4. Problems & fixes

### P1 — House income dominates non-farming days and ~40% of a farming day

**Evidence:** `facilities/house.py:_pending_income` uses `floor_mult = max(1.0, highest_floor / 3.0)`, uncapped. At F40, Sanctuary in Tidebreak (1.5×) pays `480 × 1.5 × 13.33 = 9,600/day`; a 10-day bank is 96,000g. The Sanctuary upgrade (50,000g) pays back in ~5 days. Meanwhile the whole house chain (98,100g) also grants storage, girl capacity, and rest buffs.

**Why it matters:** the house is the best gold purchase in the game and the only income with zero opportunity cost. During family/house/city days it is 100% of income — the observed "main income" feeling.

**Options**

- **A (recommended):** replace the multiplier with `1.0 + min(3.0, highest_floor / 15.0)` → 1.67× at F10, 2.33× at F20, 3.0× at F30, 3.67× at F40, 4.0× at F45+. At F40 income becomes 2,640/day (**10%** of an active day, down from 39%).
- **B:** keep the current multiplier and cut the base `income_per_day` values by ~60–65%. Same flat shape, but the table loses the "bigger house = bigger dividend" feel.
- **C:** remove the floor multiplier entirely (`480 × city_mult`). Cleanest, but the house then contributes ~3% and the upgrade table's income column is decorative.

**Recommendation:** A. The house remains worth upgrading for storage/girls/rest; income becomes a dividend. Show a single **daily figure** in the house screen; it is the exact amount collected. Update the README table.

**Touch points:** `facilities/house.py` (`_pending_income`, `_house_collect_income`, upgrade screen), `README.md`, wiki if regenerated. No new save fields.

---

### P2 — The endgame has no repeatable sink — ✅ implemented v0.1.9.8

**Evidence:** the two large sinks are enhancement (caps at +10) and scroll craft (one-time per item). Once the party's gear is maxed, the remaining drains are inns, potions, temple services, and 20–100g/month ship/mount upkeep — rounding errors against ~25k/day.

**Why it matters:** this is the direct cause of "the only sinks are scrolls and legendary enchant." The player is right: those are the only things big enough to matter, and they both stop.

**Options**

- **A (recommended): Reforge service (Blacksmith).** Pay `40 × item_value(item)` to re-roll the item's elemental infusion (or one affix once the affix system ships), with a keep-or-replace choice. Costs: legendary +0 ≈ 1,920g; legendary +10 ≈ 5,120g; epic +8 ≈ 2,240g. At endgame that is 2–5 rolls/day while still saving — a permanent gold-to-power conversion that scales with item power, not player wealth.
- **B: Base-tier promotion.** Pay to raise an item's `intrinsic_value` by +1 (capped by grade). Powerful, but touches drop caps and the form system; postpone.
- **C: Cosmetics / house decor / titles.** Good long-term sink, content-heavy; ship as a Phase 3 layer.

**Recommendation:** A shipped in Phase 2; C remains a later cosmetic layer. Reforge uses `item_value()` so it stays consistent with D1.

**Status:** ✅ Shipped v0.1.9.8 — "Reforge Element (Re-roll)" in `facilities/blacksmith.py`; `reforge_cost()` in `resources/items.py`; pure `roll_reforge_element()` / `apply_reforge_element()` helpers in `resources/item_generation.py`. The fee is paid before the roll; keeping the old element does not refund it. The fee stays on `item_value` (D10 pricing-only).

**Replaced 2026-11-10:** the re-roll was retired for **Strip Element (Recover Flowers, 3:1)** — the smith removes one flower slot entirely and returns one flower per three infused, with no gold fee. `reforge_cost()` was deleted.

**Touch points:** `facilities/blacksmith.py` (new service + menu), `inventory.py` / `resources/item_generation.py` (re-roll helper), tests. Item-based, so player/ally parity is automatic.

---

### P3 — Scroll costs use a second price scale

**Evidence:** the craft ladder is 2,000/5,000/12,000/30,000/80,000, while the same legendary item is worth 320g (sell), 2,240g (shop), 14,400g (black market). The cost of *creating* a legendary is 5–250× the cost of *buying* one. `_scroll_craft_cost` never calls `item_value()`.

**Why it matters:** it makes the scroll the only "real" sink and makes item values feel fake. It also makes targeted legendaries a week-long grind while random legendaries drop every ~20 kills in Pandemonium.

**Options**

- **A (recommended):** derive the gold cost from the rarity factor: `2,000 × price_mult(rarity)` → 2,000 / 2,800 / 4,400 / 8,000 / **16,000**. Keep the 4-item requirement and the value-delta apply fee. The fodder (4 legendary items) is the real gate; gold is the convenience fee.
- **B:** keep the 80k ladder as a prestige sink, but only if P2 ships (otherwise gold still has nowhere to go after gear cap).
- **C:** derive from `Δvalue` at a reference intrinsic (`6 × (price_mult − 1) × k`); equivalent to A with different constants.

**Recommendation:** A. If playtest shows legendary scrolls are now too easy, raise the constant (e.g. `3,000 × price_mult` → 24k) before touching the fodder rule.

**Touch points:** `facilities/arcane_tower.py:_scroll_craft_cost`; craft UI already displays the cost; tests; README/wiki.

> The scroll ladder stays **flat** (not multiplied by `k`). It becomes relatively cheaper as item values rise, which is intentional: the reforge (D2) is the repeatable endgame drain.

---

### P4 — Enhancement has a value cliff, not a cost problem

**Evidence:** the last legendary step (+9→+10) costs `50 × 8 × 1.5^10 = 23,000g` for +1 stat. The cumulative +10 is ~68k. Most players rationally stop at +5–8. The cap is a soft wall, not a sink.

**Why it matters:** the sink isn't "too cheap" or "too expensive"; it stops being *worth it* before it stops being *available*.

**Options**

- **A (recommended):** keep the 1.5 cost curve (early game untouched) and add a **+10 capstone**: the item gains a `Masterwork` prefix, +10% sell value, and one small utility perk (e.g. reforge cost −20% for that item). Power-neutral, so no combat/ally parity work.
- **B:** flatten the exponent to 1.4 (legendary +10 ≈ 39,100). Cheaper, but it changes the early common +5 cost (989→766) and doesn't fix the cliff by itself.
- **C:** add combat perks at +8/+10 (elemental proc, crit). Strongest, but requires actor-based wiring in both `combat/player_actions.py` and `combat/ally.py` — higher risk.

**Recommendation:** A now; revisit B/C only if playtest shows nobody enhances past +8.

**Touch points:** `facilities/blacksmith.py` (name/flag), `resources/items.py` (`item_value` bonus), sell price display, tests.

---

### P5 — House upkeep was hidden math (closed 2026-11-04)

**Evidence:** the first Phase 1 build deducted 15% at collection. That forced the UI to either show gross/net (clutter) or hide a tax (bad UX). Neither is acceptable.

**Decision:** **no house upkeep.** The displayed daily income is the exact amount collected. The multiplier cap (P1) is the balance lever; ships/mounts keep their existing visible monthly bills. Per-girl food remains a future dial only.

---

### P6 — Ancillary faucets have no defined role

**Evidence:** bounties (~doubles kill gold), dispatch (hundreds/day), cargo (hundreds/trip), wild completion (one-time `level × floors × 25`), Event Horizon (~1–2k/run), quests (80–1,000). None can rival dungeons or the house; several overlap with kill gold.

**Why it matters:** without a role statement, future content may accidentally add a second house-scale faucet, and players cannot tell which loop is "the" money loop.

**Recommendation (documentation, no numbers):**

| Activity | Role |
|---|---|
| Dungeon / Pandemonium | **Primary active faucet.** Pandemonium's 2.5× is the endgame risk premium. |
| Bounties | Directed farming; keep as a kill-gold multiplier. |
| Item selling | Loot liquidation (~2% of income, measured); not a primary faucet. |
| House | Small passive dividend (≤12%). |
| Dispatch | Passive supplemental (≤5% of daily). |
| Cargo | Strategic trade flavour; not a primary faucet. |
| Event Horizon | Power/relic progression; gold payout is a consolation, not the reward. |
| Quests | One-time story rewards. |

**Measured loot income (F42, 200k-kill sim):** 0.264 equipment drops/kill, average sell 33g, plus consumables → **9.9g/kill** ≈ 593g/day (2.3% of a 25.9k dungeon day); Pandemonium ≈ **18.5g/kill** ≈ 1.6% of its day. Selling is inventory hygiene, not a faucet. If it should matter, use the P9 market index (or add salvage materials) — not a raw kill-gold cut.

---

### P7 — The 10-day income bank creates lump-sum spikes

**Evidence:** `MAX_INCOME_DAYS = 10`; at F40 the current house banks 96k per collection. One collection dwarfs a dungeon run and hides the daily rate.

**Options:** reduce to 3–5 days (recommended: **5**), or keep 10 but show `per day` on the collection screen. The rate is the balance lever; the cap is perception.

**Recommendation:** 5 days + a single `Daily income` line.

---

### P8 — No gold-flow diagnostic

**Evidence:** item-level tests exist (`tests/_diag_item_economy.py`), but no script models income vs drains per phase. Balance changes are verified by playtest only.

**Recommendation:** add `tests/_diag_gold_economy.py` that imports the real constants (`HOUSE_LEVELS`, `CITY_INCOME_MULT`, `_pending_income`, `roll_gold_drop`, `_scroll_craft_cost`, enhance cost) and prints the per-phase table. Re-run it after every tuning change.

---

### P9 — Item value does not scale with level

**Evidence:** measured loot share: L3 13.8%, L10 6.1%, L20 3.7%, L30 3.1%, L42 **2.4%**. Kill gold grows 10× from L3 to L42; average equipment sell grows only 16.7g → 33.1g (~2×). A legendary good base's price/kill ratio is 14–22 at L3 but only **1.4–2.1 at L42** (early shops don't stock them, but the inversion is the point) — gear gets cheaper as the player levels, while the only meaningful sinks are flat 68k/80k costs.

**Why it matters:** this is the arithmetic behind "selling contributes almost nothing" and "the only sinks are scrolls and enchant." The shop is a 1–2 kill trivia purchase at endgame, so gold has no gear sink; the flat sinks are the only things big enough to matter.

**Fix (agreed direction):** the §3.1 `k(level)` market index. It holds the loot share near the early-game standard (~14–20%) and holds a legendary at ~14–22 kills at every level. Total per-kill income is unchanged; only the mix shifts from kill gold to loot.

**Locked (2026-11-04):** D9 anchor = `max(player level, highest max_floor)`; D10 pricing-only; D11 accept Pandemonium's ~13%; D12 ramp at L5. Phase 3 applies `k` to shop buy/sell + black market; blacksmith services stay power-based.

---

## 5. Decisions (D1–D8 proposed; D9–D12 locked 2026-11-04)

| # | Decision | Options | Recommendation |
|---|---|---|---|
| D1 | House income curve | A: `1 + min(3, floor/15)` · B: current curve, base income −60–65% · C: flat per level | **A** |
| D2 | Repeatable endgame sink | A: reforge at `40 × item_value` · B: base promotion · C: cosmetics only | **✅ A shipped v0.1.9.8**; stays on `item_value`; C later |
| D3 | Scroll craft cost | A: `2,000 × price_mult` · B: keep 80k · C: value-delta at reference intrinsic | **✅ A shipped v0.1.9.7**; stays flat |
| D4 | Enhancement | A: keep cost + +10 capstone · B: 1.4 exponent · C: +8/+10 combat perks | **A**; stays flat |
| D5 | House upkeep | A: none (displayed rate is final) · B: per-girl food · C: monthly bill | **A — none** |
| D6 | Ancillary faucet roles | document only | **As P6** |
| D7 | Income bank cap | 10 · 5 · 3 days | **5** |
| D8 | Diagnostics | script + UI breakdown | **Yes** |
| D9 | `k` index anchor | player level · max_floor · enemy level at drop | **🔒 `max(player level, highest max_floor)`** — enemy level excluded |
| D10 | `k` index scope | shop buy/sell + black market · also fusion/reforge/scroll/enhance · sell only | **🔒 Pricing-only** — shop buy/sell + black market; blacksmith services stay power-based |
| D11 | Pandemonium loot share | accept ~13% · cut its kill multiplier · loot multiplier | **🔒 Accept ~13%** |
| D12 | `k` ramp start | L3 · L5 · L10 | **🔒 L5** |

---

## 6. Implementation plan

**Phase 1 — tuning only (no new systems) — ✅ shipped v0.1.9.7**
- `facilities/house.py`: new floor multiplier; no upkeep; UI shows the exact daily rate; `MAX_INCOME_DAYS = 5`; docstring.
- `facilities/arcane_tower.py`: `_scroll_craft_cost` → `2_000 * price_mult` (import from `resources.items`).
- `README.md`: house table and passive-income note.
- `tests/_diag_gold_economy.py` (new) + unit checks for the three formulas.
- No new save fields; old saves load unchanged. Banked income is recomputed by the new formula on collection (no migration). Players with more than 5 banked days lose the excess once — note this in the changelog.

**Phase 2 — repeatable sink — ✅ shipped v0.1.9.8**
- `facilities/blacksmith.py`: "Reforge Element (Re-roll)" service; fee `reforge_cost(item)`; paid before the roll; keep-or-replace.
- `resources/items.py`: `reforge_cost()` (40 × `item_value`).
- `resources/item_generation.py`: `roll_reforge_element()` (pure) + `apply_reforge_element()`.
- Tests: `tests/_diag_reforge.py` — cost, pure roll, apply, value/tier preservation, unique exclusion.
- Changelog v0.1.9.8.
- **Replaced 2026-11-10:** `strip_element()` in `facilities/blacksmith.py`; `infusion_flowers_invested()` + `strip_infusion_slot()` in `resources/item_generation.py`; no gold fee, 3:1 flower refund. `tests/_diag_reforge.py` now covers stripping.

**Phase 3 — k-scaling (D9–D12) — ✅ shipped v0.1.9.9**
- `resources/items.py`: `market_anchor_level()`, `market_index()`, `market_value()`, `kill_gold_offset()`.
- Applied to shop buy/sell, road merchants and black-market pricing; stock cache key is now `shop_stock4`.
- Kill-gold offset is applied in `roll_gold_drop()` **after** the 25% bonus (before min-8), so the expected total stays flat. `add_gold_drop()` passes the player.
- Blacksmith services stay on `item_value`/flat costs (D10 pricing-only).
- `tests/_diag_gold_economy.py` checks the index/anchor/offset and prints the L5/L20/L42 loot-share table.
- Optional: +10 capstone, post-run breakdown.

---

## 7. Playtest checklist

- [ ] Early game unchanged: kill gold vs item prices still feels fair; common scroll still 2k.
- [ ] F20: house dividend < 10% of an active day; upgrade still feels worth it for storage/girls.
- [ ] F40: house income ≤ 12% of an active day; 5-day bank is no longer a session-defining lump sum.
- [ ] Mid-game scrolls: rare/epic scrolls are attainable without trivializing legendary drops.
- [ ] Legendary scroll: 4-item fodder remains the gate; gold cost is a convenience fee.
- [ ] Reforge: 2–5 rolls/day at endgame; a desired roll takes a meaningful (not infinite) number of attempts.
- [ ] No dead gold after +10 gear: reforge/cosmetics still absorb income.
- [ ] House screen shows one daily figure; no hidden upkeep; no negative-gold surprise.
- [ ] Old save loads; no new required fields; item values unchanged.
- [ ] `tests/_diag_gold_economy.py` matches the doc tables.
- [ ] k-index: early game (L≤5) is byte-identical; L20 loot share ~15–17%; L40 ~20%.
- [ ] k-index: a legendary costs 14–22 kills at L5/L20/L40 (no inversion).
- [ ] k-index: cannot buy from a shop and resell at a profit at any Charisma/Karma.
- [ ] Pandemonium loot share is acceptable (~13%) or its kill multiplier is tuned.

---

## 8. Explicitly NOT changing

- Early kill gold (`level*8+...`) — the early curve is the reference. The k-index kill-gold offset only applies from L5 upward.
- Pandemonium ×2.5 and boss bonuses, except D11 may tune Pandemonium's kill multiplier if its post-`k` loot share is too low.
- `item_value()` / `intrinsic_value()` and the rarity ladder. The `k` index is a **pricing-layer multiplier**, not a change to either function.
- Drop rates, rarity caps, treasure-room tables.
- One-house rule, house storage/girl/rest benefits, deed cost.
- Unique items, wedding accessories, fusion's no-downgrade rule, apply fee.
- Consumable pricing, Potion Sickness, inn/temple prices.
- Death penalty (20%), cargo pricing, quest/bounty formulas.

---

## 9. Implementation readiness

| Workstream | Ready? | Blockers |
|---|---|---|
| Phase 1: house curve + 5-day bank (no upkeep) | ✅ Shipped v0.1.9.7 | No new save fields; >5 banked days are capped once. |
| Phase 1: scroll ladder 2k→16k | ✅ Shipped v0.1.9.7 | One function + tests. |
| Phase 1: `_diag_gold_economy.py` | ✅ Shipped v0.1.9.7 | Passes (`gold economy diagnostics OK`). |
| Phase 2: reforge | ✅ Shipped v0.1.9.8 | `tests/_diag_reforge.py` passes. |
| P9 `k` index: pricing layer | ✅ Shipped v0.1.9.9 | Shop/sell/road/black market; stock key `shop_stock4`. |
| P9 `k` index: kill-gold offset | ✅ Shipped v0.1.9.9 | Applied after the 25% bonus; diag passes. |
| Full doc | ✅ Shipped v0.1.9.9 | Playtest tuning only. |

**Verdict:** Phases 1–3 are shipped. The remaining work is playtest tuning (D1/D2/D3 constants and the `k` bands).

**Recommended order:** playtest the full loop → tune the D1/D2/D3 dials and `k` bands.

---

## 10. Early / Mid / Late comparison (old vs new)

**Assumptions:** early = L5, mid = L20, late = L40. House is the max level for the phase (Hovel / Villa / Sanctuary); city multiplier 1.0 / 1.5 / 1.5. "New" = D1/D5/D7 for the house, D3/D4 for sinks, and P9 `k` for item prices. Bounties, dispatch and item sales outside the loot line are excluded. All values approximate.

### 10.1 Per-kill budget

| Phase | Old kill | Old loot | Old total | Old loot % | `k` | New kill | New loot | New total | New loot % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Early L5 | 58 | 6.5 | 64 | 10% | 1.0 | 58 | 6.5 | 64 | 10% |
| Mid L20 | 196 | 7.5 | 203 | 3.7% | 4.5 | 169 | 34 | 203 | 17% |
| Late L40 | 380 | 9.7 | 389 | 2.5% | 8.0 | 312 | 78 | 389 | 20% |

### 10.2 Reference shop price (legendary, intrinsic 6, city_base 45–70)

| Phase | Old price | Old kills | New price | New kills |
|---|---:|---:|---:|---:|
| Early L5 | 540–840 | 9–15 | 540–840 | 9–15 |
| Mid L20 | 540–840 | 2.8–4.3 | 2,430–3,780 | 14–22 |
| Late L40 | 540–840 | 1.4–2.2 | 4,320–6,720 | 14–22 |

### 10.3 House income/day

| Phase | Old | New |
|---|---:|---:|
| Early F5 (Hovel, ×1.0) | 13 | 11 |
| Mid F20 (Villa, ×1.5) | 650 | 228 |
| Late F40 (Sanctuary, ×1.5) | 9,600 | 2,640 |

### 10.4 Legendary max-out (gold only; fodder excluded)

> Phase 1/2 constants; blacksmith services stay on `item_value` (D10 pricing-only).

| Phase | Old (150k) | Old kills | New (86k) | New kills |
|---|---:|---:|---:|---:|
| Early L5 | 150,000 | 2,344 | 86,000 | 1,344 |
| Mid L20 | 150,000 | 739 | 86,000 | 424 |
| Late L40 | 150,000 | 386 | 86,000 | 221 |

### 10.5 What changes

- **Early:** unchanged (`k = 1.0`, house is tiny).
- **Mid:** loot share 3.7% → **17%**; a legendary goes from 3–4 kills to **14–22**; house 650 → **228/day**. The mid game becomes loot-driven and less passive.
- **Late:** loot share 2.5% → **20%**; a legendary goes from 1.4–2.2 kills to **14–22**; house 9,600 → **2,640/day**. The endgame becomes a loot economy; the max-out sink is 43% cheaper in kills, and the reforge is the repeatable drain.
- **Total per-kill income is unchanged in every phase** — this is relative price normalization, not inflation.

---

## Appendix A — Worked examples

**House at F40 (Sanctuary, Tidebreak 1.5×)**

| | Today | Proposed |
|---|---|---|
| Floor multiplier | 40/3 = 13.33 | 1 + min(3, 40/15) = 3.67 |
| Income/day | 9,600 | **2,640** |
| Share of active day (~25k) | 39% | **10%** |
| 5-day bank | 48,000 (10-day = 96,000) | 13,200 |

> The displayed daily rate is the amount collected; there is no upkeep deduction.

**Scroll**

| Rarity | Today | Proposed |
|---|---|---|
| common | 2,000 | 2,000 |
| uncommon | 5,000 | 2,800 |
| rare | 12,000 | 4,400 |
| epic | 30,000 | 8,000 |
| legendary | **80,000** | **16,000** |

(Plus 4 same-rarity items; apply fee `max(150, 50 × Δvalue)` unchanged.)

> Pre-k-index baseline; the scroll ladder stays flat (D10 pricing-only).

**Enhancement (cost unchanged; +10 capstone)**

- Legendary +10 total: ~68,000 + `Masterwork` (name, +10% sell value, −20% reforge cost).
- Alternative if never used: exponent 1.4 → ~39,100.

**Endgame day budget (F40, regular dungeon)**

| Line | Gold/day |
|---|---|
| Active dungeon | ~25,000 |
| House income | ~2,640 (10%) |
| Item selling | ~500 (2%) |
| Bounties/dispatch | ~1,000–2,000 (4–8%) |
| Reforge (1–3 rolls) | ~2,000–15,000 |
| Consumables/inn | ~500 |
| **Net** | still positive, but gold has a purpose every day |

---

## Appendix B — Open dials (playtest only)

| Dial | Default | If too strong | If too weak |
|---|---|---|---|
| House floor cap (D1) | `1 + min(3, floor/15)` | cap 2.0, divisor 20 | cap 4.0, divisor 12 |
| Scroll constant (D3) | 2,000 | 3,000 | 1,500 |
| Reforge multiplier (D2) | 40× value | 60× | 25× |
| Income bank (D7) | 5 days | 3 days | 10 days |
