# Pandemonium — Casino / Tavern Games Design

**Status:** ✅ Phases 1–3 implemented 2026-11-06 — inn tables, Black Market back room, cheating/blacklist in both games, suited cards, and the three casino deed titles with record lines; `tests/_diag_casino.py` passes. Optional Phase 3 polish (third game, TAVERN tiles, README/wiki) remains open.
**Scope:** Add optional dice/card gambling to the existing **inn** (tavern tables) and **Black Market** (a high-stakes back room). The back room pays better and accepts larger stakes, but requires negative Karma and is open only while the Black Market is (night).
**Builds on:** `facilities/inn.py`, `facilities/black_market.py`, `karma.py`, `time_blocks.py`, `titles.py`, `city_dialogue.py`.
**Related docs:** [`gold_economy_pacing_design.md`](./gold_economy_pacing_design.md) · [`karma_system_design.md`](./karma_system_design.md) · [`titles_design.md`](./titles_design.md) · [`improvement_planning_guide.md`](./improvement_planning_guide.md) · [`Pandemonium_Open_Improvements.md`](./Pandemonium_Open_Improvements.md)

---

## 0. Verdict

**Yes — but every game must be EV-negative.** "Higher reward" at the Black Market means **larger stakes, a higher payout ceiling, and a better return-to-player (RTP)**, not a positive expected value. A repeatable positive-EV game would be a gold faucet and would fight the economy targets in `gold_economy_pacing_design.md`.

Locked shape:

- **Inn = low-stakes tavern tables.** Flavor, a small voluntary sink, 1 block per hand.
- **Black Market = "The Back Room".** Higher stakes, RTP ≈96% vs ≈92%, pot cap 10,000 vs 1,000, gated behind negative Karma; stake tiers deepen with Karma.
- Both venues use the same two games and one rules engine.
- Caps + hand limits + time cost keep it a sink, not a farm.
- **Cheating (Phase 2, both games)** is the explicit moral choice: a DEX+CHA check, −2 Karma only if caught, and a 7-day blacklist risk — not a better bet. Under & Over pays 1.30×; Blackjack removes the latest card dealt to the player.

This is a content/flavor feature, not a primary gold sink. At the back room's ≈96% RTP the expected loss is ≈4% of every stake; it will not replace reforge/scroll/gear sinks.

---

## 1. Current state (verified 2026-11-05)

| Thing | Current behavior | Consequence |
|---|---|---|
| Inn | `inn_menu` has Rest/Sleep only; Wonderland uses a separate heroine menu. | Add one menu entry; no new screen. |
| Black Market | `black_market_service` sells relics, nets, the outlaw crate, the Looking Glass Shard, and the Woodcutter. Night-only. | Add one dynamic option + sub-menu; watch the index bookkeeping. |
| Time | `advance_time(player, ≤15)` is free; 16–90 min = 1 block. | A hand must cost ≥16 min to cost a block. Use 20 min. |
| Karma | `karma.is_enabled`, `get_karma`, `change_karma`; outlaw crate stock at ≤−25. Positive gains share the +8/day cap. | Gate the back room; do not drift Karma automatically. |
| Cities | 20 cities with inns; Black Markets in Veilholt, Wonderland, Mirefall, Ashkara, Dunemar, Blackwake. `black_market` hours = night only. | The back room is a night activity. |
| Maps | Brinewatch and Tidebreak already draw unused **TAVERN** tiles next to the INN. | Optional Phase 3: make those clickable. Phase 1 stays inside the inn menu. |
| Titles | `black_market_pct` exists on The Unrepentant; no gambling title. | Phase 3 casino titles + record lines. |

---

## 2. Player-facing pitch

> The inn keeps a table for travelers who want to lose a little coin. The Black Market keeps a table for people who can't afford to be seen winning. The dice and cards are the same. The odds are not.

---

## 3. Games

### 3.1 Under & Over (2d6)

Roll two dice. The player bets on one of:

- **Under 7** (sum 2–6) or **Over 7** (sum 8–12), or
- **Exactly 7**.

Distribution: 15 / 15 / 6 of 36.

| Venue | Under/Over pays | Exactly 7 pays | RTP |
|---|---|---|---|
| Inn | 2.20× total return | 5.50× | 91.67% (8.33% house edge) |
| Back Room | 2.30× | 5.75× | 95.83% (4.17% edge) |

**Payouts are total returns, stake included.** A winning 100g under bet returns 220g (net +120g). A losing bet returns 0.

Both bet types carry the same RTP at each venue, so the choice is about variance, not value.

**Pot-limit rule:** Exactly 7 is offered only when its maximum payout fits under the table's pot cap. Inn: 25g and 100g stakes; Back Room: 250g and 1,000g stakes. At the top stake the table offers Under/Over only, so both bet types keep the same RTP.

### 3.2 Blackjack (Hit or Stand)

A simplified blackjack table built for a terminal UI. One fresh 52-card deck per hand (no counting between hands); aces count 11 or 1; the dealer stands on all 17s.

- **Player actions:** Hit or Stand. No double, split, surrender, or insurance.
- **Regular win:** pays 1:1 (2.0× total return).
- **Natural 21:** a two-card 21 pays 6:5 (2.2× total return). A 21 made after hitting is just 21.
- **Resolution:** if the player busts, they lose immediately. Otherwise the dealer reveals the hole card and draws to 17. The higher total wins. A dealer natural beats a non-natural 21; two naturals tie.
- **Table display:** cards show rank and suit (`A♠`, `10♥`, `J♦`); the dealer's hole card shows as `?` until the player stands. Dealer hits are revealed one card at a time.
- **Cheat (back room):** the player may remove the latest card dealt to them (DEX+CHA check; see §4). The hand continues from the reverted total.

**Ties differ by venue:**

| Venue | Tie result | Estimated RTP |
|---|---|---|
| Inn | The house keeps half the stake (0.5× returned) | ~91–92% |
| Back Room | Push — the stake is returned (1.0×) | ~95–96.5% |

**Why the estimates sit where they do** (single-deck S17 reference ≈99.8% RTP with 3:2 and double/split):

| Rule change | RTP impact |
|---|---:|
| No double / split | −2.3 to −2.5% |
| Natural 21 pays 6:5 instead of 3:2 | −1.4% |
| Inn only: a tie returns half the stake | −4.2% |

The exact values depend on the player's Hit/Stand policy. `tests/_diag_casino.py` must simulate a fixed **Hit/Stand basic strategy** (hard 13–16 stands vs dealer 2–6, hard 12 stands vs 4–6, soft 18 stands vs dealer 2–8, otherwise hit) and verify each venue sits in its band. A casual player who hits too often returns less; that is acceptable.

Blackjack's tension is the Hit/Stand decision, so no press-your-luck mechanic is needed.

### 3.3 Table configuration

| | Inn tables | Back Room |
|---|---|---|
| Stakes | 25 / 100 / 250 (L1 / L5 / L10) | 250 / 1,000 / 2,500 (L5 / L15 / L25) |
| Karma gate | none | < 0 / ≤ −15 / ≤ −40 |
| Pot cap (max total return per hand) | 1,000 | 10,000 |
| Net-win cap per day | 1,000 | 5,000 |
| Hands per day | 12 shared across venues | 12 shared |
| Time per hand | 20 min (1 block) | 20 min (1 block) |
| Cheating | no | Yes — both games (2/day) |

**Pot-limit rule:** Exactly 7 is only offered where its maximum payout fits under the pot cap (inn: 25g/100g; back room: 250g/1,000g). At the top stake the table offers Under/Over only. This keeps the cap from turning the long shot into a bad bet; blackjack's 2.0× ceiling stays under both caps.

---

## 4. Karma integration

- **Entry:** when Karma is enabled, the back room requires `karma.get_karma(player) < 0`. At 0 or above the dealer refuses with a hint — never a silent dead end.
- **Stake tiers:** Karma < 0 (the 0 threshold) → 250g; ≤ −15 → 1,000g; ≤ −40 → 2,500g. Player-level gates (L5 / L15 / L25) apply on top.
- **Playing does not change Karma.** This respects the Karma design's D3 ("only explicit, labeled choices") and D4 ("no automatic drift"). The gate *is* the moral statement.
- **Cheat (Phase 2, back room, both games):** "Palm the bones" at the dice table; "Palm a card" at the blackjack table.
  - Success is a **DEX+CHA check**: `d20 + (DEX + CHA) // 2` using effective stats (gear included) vs a fixed DC 16 / 18 / 20 for the 250g / 1,000g / 2,500g table. Natural 1 fails, natural 20 succeeds; effective success is capped at **70%** to keep the bet EV-negative. The effective DC is `max(base DC, stat + 7)`, which enforces the cap through the check itself.
  - **Under & Over success:** returns 1.30× (net +0.30 stake).
  - **Blackjack success:** removes the latest card dealt to the player; the hand continues from the reverted total. No payout multiplier.
  - Failure (caught): lose the stake and a **7-day blacklist** from every back room. The catch also writes a `[CASINO]` Journal entry.
  - **−2 Karma only when caught** (failure). The menu labels it "Karma only if caught." This is a deliberate exception to Karma D3 for hidden acts — the ledger only records what is witnessed.
  - Under & Over EV ≈ −9% of stake at the 70% cap; low DEX/CHA makes it worse. Blackjack's cheat is a rescue/odds nudge — it removes a bad card but still carries the same caught-cheat loss, Karma, and blacklist risk. **Neither is a better bet.**
  - Max 2 attempts per day shared across games, tracked in `casino.cheats_today`.
  - Available when Karma is disabled; with no Karma, the blacklist is the only consequence.
- **Karma OFF** (old saves / rule disabled): the dealer "doesn't keep a ledger." The back room is open, stake tiers gate by level only, and the cheat remains available — a caught cheat still triggers the 7-day blacklist. A whole feature must never be dead because Karma is off.
- **The Unrepentant** already discounts the Black Market; no change needed. A caught cheat can push a player toward Outlaw and unlock it naturally.
- **Venues:** Blackwake is included (its Black Market is the natural crime hub); no special rule in Phase 1. **Wonderland is excluded** from the back room (Karma content there is deferred, and it is a time pocket).

---

## 5. Risk caps & anti-degeneracy

- **EV-negative by design.** Simulated RTP must stay in [0.89, 0.97] after pot caps.
- **Pot cap** per hand (1,000 inn / 10,000 back room).
- **Daily net-win cap** per venue (1,000 / 5,000). Once reached, that venue closes for the day. Losses count against the net, so a comeback is possible. A single capped payout may exceed the net cap; the payout stands and the table closes.
- **12 hands/day shared**, reset on day change. Twelve blocks is already half a day.
- **1 block per hand** (20 min) — a real opportunity cost against dungeon/travel.
- **No item, XP, quest, or Karma rewards** in Phase 1. Gold only.
- **No credit, loans, item stakes, or house storage.** Bets are clamped to carried gold; gold can never go negative.
- **Blacklist** (Phase 2) is the cheat's real cost: a caught cheat loses the stake and 7 days of back-room access (all cities).
- Save-scumming is mitigated, not solved, by time/caps. The game is single-player; do not over-engineer this.

**Why this is not a faucet:** at the back room's ≈96% RTP the expected loss is ≈4% of every stake. A 2,500g max bet loses ≈100g per hand in expectation. The caps bound lucky streaks; the time cost bounds volume.

---

## 6. Persistence

Add to `character.py::ensure_player_fields` (and heal nested shapes defensively, like `karma.ensure_state`):

```python
casino = player.setdefault("casino", {})
casino.setdefault("day", 0)
casino.setdefault("hands_today", 0)
casino.setdefault("net", {"inn": 0, "black_market": 0})
casino.setdefault("closed", {"inn": False, "black_market": False})
casino.setdefault("hands_played", 0)
casino.setdefault("hands_won", 0)
casino.setdefault("biggest_win", 0)
casino.setdefault("total_wagered", 0)
casino.setdefault("total_returned", 0)
casino.setdefault("cheats_today", 0)
casino.setdefault("cheats_unseen", 0)
casino.setdefault("cheats_caught", 0)
casino.setdefault("ban_until_day", 0)
```

All are monotonic lifetime stats or daily-reset state; no migration is needed. Old saves get defaults.

### 6.1 Titles & records (Phase 3) ✅ IMPLEMENTED 2026-11-06

The casino updates both its own lifetime stats and the matching `title_stats` counters:

| `casino` stat | `title_stats` key | Meaning |
|---|---|---|
| `hands_won` | `casino_hands_won` | Lifetime winning hands |
| `biggest_win` | `casino_biggest_win` | Largest single-hand **net** win |
| `cheats_unseen` | `casino_cheats_unseen` | Successful cheats never caught |
| `cheats_caught` | `casino_cheats_caught` | Cheats caught |

Three separate `gambling` titles track the three casino records:

| Title | Tier | Deed | Effect |
|---|---|---|---|
| **The Gambler** | T2 | 100 hands won **or** biggest win ≥4,000 | `casino_payout_pct: 0.01` (+1% table payouts) |
| **Sleight-Hand** | T2 | 10 cheats **unseen** | `black_market_pct: 0.03` (+3% Black Market discount) |
| **Marked** | T2 | 3 cheats **caught** | `black_market_pct: 0.05` (+5% Black Market discount); visible drawback `shop_discount_pct: 0.05` (−5% shop discount) |

All three show the same record line — `Hands won: N · Biggest win: N · Cheats unseen: N · Caught: N` — for both locked and unlocked states. The cheat counters are records, not prerequisites for The Gambler; each title unlocks independently from its own counter.

Implementation: the four keys are defaulted in `titles.ensure_state()`; `casino.ensure_state()` backfills them from the lifetime casino stats on load so old saves reconcile correctly. The `deed_stat` labels live in `titles._DEED_LABELS`; `resources/titles.py` carries the three entries with a `record: "casino"` key; `titles.list_titles()` builds the shared `record_line`; `inventory_screen._render_titles_subtab` renders it for locked and unlocked cards. The Gambler adds **1% of the stake** to winning payouts (minimum 1g, never on pushes/returns), then the pot cap applies; the diagnostic verifies the back-room RTP with The Gambler stays ≤0.97.

---

## 7. UI flow

**Inn** (standard cities; not Wonderland):

```
Rest (Full Heal - 1 block)
Sleep (Full Heal) - Night only
Play tavern games...
Back
```

Inside: choose game → choose stake → choose bet → result → "Play again / Leave." Show gold, hands left today, and the house limit. The house cuts a winner off at the daily net cap. At the back room, both games offer **Cheat** (Under & Over: 1.30× payout; Blackjack: remove the latest card) with a DEX+CHA check, success chance, and "Karma only if caught". The blackjack cheat option is offered during the hand, including after a bust.

**Black Market** (night only):

```
Buy mysterious relic...
Buy Capture Nets...
Gamble in the back room
...
```

The option is always visible; locked states explain themselves:

- Karma ≥ 0: "Ask about the back room" → dealer refusal + hint.
- Karma < 0 but level too low: "The dealer looks you over. Not yet."
- Blacklisted: "The back room (closed to you for N more days)."
- Open: "Step into the back room."

**Important integration pitfall:** `black_market_service` ends with `term.pause(); advance_time(player, 30)` for every branch. The back-room sub-menu charges time per hand, so its branch must `return` after the sub-menu to avoid double-charging a block. The inn loop has no trailing time charge, so it can call the sub-menu and continue.

---

## 8. File plan

| File | Change |
|---|---|
| `casino.py` (new, root) | Rules/config: dice and blackjack resolution (deck, hand totals, dealer policy), RTP tables, stake lists, caps, daily reset, Karma/level gating, title payout bonus. No I/O; takes an `rng` for tests. |
| `facilities/casino_ui.py` (new) | `tavern_games_menu(player)` and `back_room_menu(player, city_id)`; all `term` I/O, time advance, Karma calls, Journal entries. |
| `facilities/inn.py` | Add "Play tavern games..." to the standard loop; skip Wonderland. |
| `facilities/black_market.py` | Add the dynamic back-room option, fix the option-index bookkeeping, and `return` after the sub-menu. |
| `character.py` | `ensure_player_fields` casino state. |
| `resources/titles.py`, `titles.py` | The Gambler / Sleight-Hand / Marked titles, `casino_payout_pct` effect/cap, `deed_stat` labels, record line. |
| `gui/screens/inventory_screen.py` | Render the title's record line. |
| `karma.py` | No code change; call `change_karma` only when a cheat is caught. |
| `tests/_diag_casino.py` (new) | Simulation + gate/cap tests. |
| `docs/Pandemonium_Open_Improvements.md` | Update the §6 entry and §0 table. |
| `README.md`, `wiki/index.html`, `gui/screens/changelog_screen.py`, `version.py` | On ship only. |

No new GUI screen, no new threads, no new city service. The terminal `term` API handles FacilityScreen I/O.

---

## 9. Phases

**Phase 1 — Core (both venues, straight games) ✅ IMPLEMENTED 2026-11-05.**
- `casino.py` engine + caps + gating.
- Inn and back-room menus.
- Persistence.
- `tests/_diag_casino.py` passes (RTP: inn ≈92%, back room ≈96%).
- No cheating, no title.

**Phase 2 — The moral layer ✅ IMPLEMENTED 2026-11-05.**
- Cheat option (both games): DEX+CHA check, 7-day blacklist, Karma only if caught, `[CASINO]` Journal entry, 2 attempts/day.
- Under & Over: 1.30× payout. Blackjack: remove the latest card dealt to the player; the hand continues.
- Suited card display (`A♠`, `10♥`, `J♦`).
- Karma-tier dealer dialogue lines.
- Per-city dialogue keys (`games`, `back_room`) for Solmere / Ashkara / Blackwake, with generic and receptionist fallbacks.
- Karma-off fallback keeps the cheat available and applies the blacklist without a Karma change.
- Polish: locked-option hints, "dawn closes the table."

**Phase 3 — Collection & polish ✅ IMPLEMENTED 2026-11-06.**
- Casino titles — The Gambler, Sleight-Hand, Marked — + shared record lines (D8).
- Old-save backfill from the lifetime `casino` counters; unlocks are checked after every hand/cheat and on load.
- Permanent casino stats + the Journal record line; The Gambler's +1% keeps the back-room RTP ≤0.97.
- Optional third game / venue variant — not implemented.
- Promote the Brinewatch/Tidebreak TAVERN map tiles to a clickable service — optional, not implemented.
- README/wiki — deferred to release.

---

## 10. Verification

- `tests/_diag_casino.py`: 200,000 simulated hands per game/venue; assert effective RTP per venue band (inn 0.90–0.93; back room 0.94–0.97), back-room RTP > inn RTP for each game, pot caps, net caps, daily reset, stake gating (level + Karma < 0/≤−15/≤−40), Karma-off fallback, cheat check DC/cap, caught-only Karma, 7-day blacklist, gold never negative, and no mutation on an invalid bet. Blackjack uses the fixed Hit/Stand policy above. Phase 3 adds title backfill, unlock, effect-line, record-line, payout, and The Gambler RTP-cap checks.
- Old-save smoke test: load a real save read-only, confirm defaults appear after `ensure_player_fields`.
- GUI manual: inn tables, back room at night, dawn closure, ban, save/load mid-day.
- Run `tests/_diag_local_imports.py` if imports are added.
- On version bump: `tests/_diag_version_consistency.py`.

---

## 11. Locked decisions (user, 2026-11-05)

| # | Decision | Locked answer |
|---|---|---|
| D1 | Games | **Locked:** Under & Over + Blackjack. Additional minigames can be added later. |
| D2 | Back-room gate | **Locked:** Karma < 0 for entry/250g; ≤ −15 for 1,000g; ≤ −40 for 2,500g. Level gates L5/L15/L25 still apply. |
| D3 | Cheating | **Locked:** Phase 2, both games; DEX+CHA check (`d20 + (DEX+CHA)//2` vs base DC 16/18/20, effective DC `max(base, stat + 7)`); 70% success cap; Under & Over success pays 1.30×; Blackjack success removes the latest card dealt to the player; −2 Karma only if caught; 7-day blacklist when caught; max 2 attempts/day shared. |
| D4 | Karma drift from play | **Locked:** No drift from play; only a caught cheat changes Karma. No Karma change on commit. |
| D5 | Karma-off fallback | **Locked:** Back room open, level gates only; cheat available; a caught cheat triggers the 7-day blacklist with no Karma change. |
| D6 | Caps | **Locked:** 12 hands/day shared; 1 block/hand; net 1,000/5,000; pot 1,000/10,000. |
| D7 | Venue scope | **Locked:** All standard inns + all Black Markets except Wonderland; Blackwake included. |
| D8 | Gambling titles | **Locked:** three casino titles — **The Gambler** (100 hands won or biggest win ≥4,000; +1% casino payouts), **Sleight-Hand** (10 cheats unseen; +3% Black Market discount), and **Marked** (3 cheats caught; +5% Black Market discount, drawback −5% shop discount). All three show the casino record line (hands won / biggest win / cheats unseen / caught). |

---

## 12. Backlog / changelog

`Pandemonium_Open_Improvements.md` §6 and the §0 table now show **Phases 1–3 implemented**. Changelog bullets are under the current version; optional third-game/TAVERN-tile work and README/wiki remain open.
