# Pandemonium — Karma System (Favor → Karma) Design

**Status:** 📝 Design fully locked 2026-10-29 (D1–D15; D1 revised the same day to full replacement). **Phase 0 + Phase 1 core implemented 2026-10-29 (v0.1.8.5); Phase 2 implemented 2026-10-29 (v0.1.8.6); Phase 3 implemented 2026-10-29 (v0.1.8.7); City Favor removed 2026-10-29 (v0.1.8.8)** — playtest pending. Wonderland-specific Karma content is deliberately deferred. Karma is a per-save character-creation rule and is final for that save.
**Scope:** A global moral axis (**Karma**) that replaces per-city **City Favor** entirely, adds explicit moral choices to existing dungeon events and capture sales, gives high Karma meaningful economic benefits, and makes low Karma produce city-gate confrontations with guards. A lawless pirate haven (**Blackwake**) inverts Karma instead of enforcing it. The rule is chosen at character creation; new characters default ON, old saves stay OFF.
**Related docs:** [`improvement_planning_guide.md`](./improvement_planning_guide.md) · [`Pandemonium_Open_Improvements.md`](./Pandemonium_Open_Improvements.md) · [`karma_playtest_checklist.md`](./karma_playtest_checklist.md) · [`item_economy_tuning_design.md`](./item_economy_tuning_design.md) · [`time_system_design.md`](./time_system_design.md) · [`quest_system_design.md`](./quest_system_design.md) · [`prescript_ledger_design.md`](./prescript_ledger_design.md)
**Process:** follows the improvement plan: verify current systems → classify/evaluate → design doc with locked decisions → pre-flight checklist → implement → verify → record.

---

## 0. Verdict

**Yes — build it, always on, with three corrections and one new city rule.**

1. **Remove City Favor entirely and replace it with Karma.** Your observation is correct: favor was only earned and consumed in cities with a guild, even though the score was presented as a general city stat. Rather than keep a dormant per-city score, delete favor from the live economy and use the single global **Karma** score everywhere:
   - **Karma** (global, −100…+100): who you are. Drives shop prices, taxes, guild bounty scaling, guard reactions, event options, dialogue, and hallucination pressure.
   - **City Favor** (per city): **removed.** Legacy `player["favor"]` data in old saves is preserved but no longer read or written. There is no guild-city-only standing score.
2. **Make low-karma consequences non-lethal and recoverable.** Guards can beat you, but they should not send you to the death screen. Losing a gate fight means **jail** (fine + time), not a run wipe. Jail also grants a small atonement (**+3 Karma**, once per 3 days, shared with the daily cap). There must always be a way into the city ("submit to judgment") and at least two ways to climb back (temple contrition, guild atonement contracts, good deeds). Otherwise a −100 save is a soft lock.
3. **Resolve the existing Karma name collision.** The Prescript Ledger already calls its combat-local debt **Karma** (`prescript_karma_stacks`, displayed as `KRM×N`, described in the item text and changelog). Two unrelated Karma systems will confuse players and future code. **Locked:** keep the new global system named **Karma**, and rename the Ledger's *display* to **Prescript Debt** ("Debt×N") while keeping its internal field names unchanged for save compatibility.
4. **Give the criminal path a home — Blackwake.** **Locked:** the hidden pirate cove is the lawless city: no gate, no guards, no jail, no guild. But "Karma means nothing" is less interesting than **"low Karma is respected"**: invert the inn and Black Market prices so outlaws get the better deal and saints pay a "saint tax." Brinewatch is a lawful working port; Ashkara has a guild, so it is dangerous commerce, not a no-man's-land.
5. **Make it a new-character choice.** **Locked (D15):** Karma is selected in the shared **Game Rules** step at character creation (default ON), alongside the family system and future difficulty/drastic-system rules. The choice is final for the save: there is no mid-game enable or disable path, and old saves stay OFF.

**Why the idea is good:** the game already has the exact economic lever (the old favor discount, now retired in favor of Karma), the exact content hooks (wounded adventurer, corpse, monster encounter, duplicate captures), and an explicit future hook in `combat/hallucination.py` ("Karma (future design) plugs into `hallucination_tier()`"). The proposal turns a passive number into a series of visible, meaningful choices — which is the stated goal.

**Why Karma is not just a renamed favor:** City Favor was awarded by repeatable systems (bounties, dispatch, event rewards), so it measured *service*, not *morality*. Karma comes from **choices**, not routine play. Guild bounties now read Karma for scaling but do not award it.

### 0.1 Player-facing pitch (for a future README/wiki update)

> Every kindness and every cruelty is remembered. Help the wounded and the cities open their gates and lower their prices. Rob them and the guards will be waiting. Sell a captured girl to a slaver and you will feel the weight of the gold — and the door closing behind you.

### 0.2 What ships

- One global standing score: **City Favor is removed**, and every city reads the same Karma.
- A visible Karma score with nine tiers and precise deltas on choices.
- Moral choices in existing dungeon events: help vs. rob vs. leave; bury vs. loot; calm vs. ambush.
- A new **Forgotten Shrine** event: offer gold for a blessing, or steal the offerings.
- A four-way duplicate-capture sale: licensed broker / slaver / release / bond — and a sale path when the house is full.
- Karma-driven shop and blacksmith prices, monthly-bill adjustments, Tax Day interaction, and temple benefits at high Karma.
- City-gate confrontations at −25 / −50 / −75 karma with fines, talk-down checks, non-lethal guard fights, and jail.
- A lawless pirate haven (**Blackwake**): no Karma gate, no jail; low Karma is respected through inverse inn and Black Market pricing.
- Atonement: temple contrition, guild atonement contracts, good deeds, and time served in jail.
- Hallucination pressure hook (low karma worsens it, high karma softens it).
- A **Game Rules** step at character creation: Karma ON/OFF (default ON), with slots for the family system, difficulty, and future drastic systems.
- Journal/log feedback and a Karma history.

### 0.3 What does **not** change

- Routine combat, bounty turn-ins, floor clears, and dispatch do **not** change Karma. Only moral choices do.
- Monster girls are still never narrated as killed; the capture pipeline is untouched except for the sale choice.
- The 70% maximum shop discount stays.
- Guild bounty boards stay, but scale from global Karma instead of per-city favor.
- Dispatch still grants gold, items, and EXP; it no longer grants favor.
- Legacy `player["favor"]` data in old saves is preserved but ignored (no migration).
- No new UI screen; Karma is a line in existing headers + choice labels + Journal.
- No mid-game Karma switch. The rule is chosen at character creation and is final for the save; old saves stay OFF (D15).

---

## 1. Current state (verified 2026-10-29)

| System | Current behavior |
|---|---|
| City Favor (removed) | Old saves may still contain `player["favor"][city_id]`. After v0.1.8.8 no live gameplay code reads or writes it. |
| Former favor gains | Bounties, dispatch sweeps, `heal_wounded`, and New Moon Festival. Removed or converted: bounties pay gold only, dispatch pays gold/items/EXP, and New Moon gives +25% bounty gold. |
| Former favor spending | Shop/blacksmith discount. Replaced by the Karma tier; the formula is now Charisma + Karma only. |
| Former favor scaling | `facilities/guild.py::generate_bounties` now uses global Karma for level offset, bounty count, kills required, deadline, and reward gold. |
| Former favor scope | Only six cities had guilds. That special case is gone: Karma applies in every city. |
| Karma replacement | Global Karma is the single standing score and drives the former favor surfaces (shop, guild bounty scaling) plus gates, dialogue, and events. |
| Lawless city | **Blackwake** is the hidden pirate cove (sea-only; `inn`, `port`, `black_market`; dialogue: "Welcome to the pirate port"). Brinewatch is a lawful working port; Ashkara has a guild, so its black market is dangerous commerce, not lawlessness. |
| Missing | No global morality, no wanted/heat level, no guard encounters, no capture-sale consequence. |
| Existing hooks | `combat/hallucination.py::hallucination_tier` explicitly reserves a Karma input. `docs/Pandemonium_Open_Improvements.md` lists "Crime & guards" as a Low idea. |
| Name collision | `combat/weapon/prescript_ledger.py` uses **Karma** for combat-local debt (`KARMA_DT_PER`, `Karmic Retribution`, `KRM×N`). |

**Conclusion:** this is a system extension, not a brand-new system. Reuse the guild hooks, event handler, and capture flow; add one core module (`karma.py`) and one combat helper (`combat/city_guards.py`). Remove favor from shop, guild, dispatch, events, and UI.

---

## 2. Locked decisions (user, 2026-10-29)

| # | Decision | Locked answer |
|---|---|---|
| D1 | Favor vs Karma | **Full replacement (revised 2026-10-29).** Global Karma is the only standing score. City Favor is removed from all live systems (shop, guild, dispatch, events, UI); legacy save data is ignored. |
| D2 | Karma range | **−100…+100**, integer, starts at 0. Nine tiers (§3.2). |
| D3 | When Karma changes | Only on an **explicitly labeled choice**, applied when the choice is **committed** (before the roll), not on success. This prevents save-scumming and makes intent the moral unit. **Casino exception (2026-11-05):** hidden back-room cheating applies its Karma penalty only when caught; see `casino_games_design.md`. |
| D4 | Gain limits | Positive Karma from **all repeatable sources** (good deeds, contrition, atonement contracts, jail) is capped at **+8/day**; negative Karma is uncapped. One-time quest/story rewards bypass. **No automatic drift.** |
| D5 | Shop formula | `Charisma (≤40%) + Karma (−20…+20)`, total clamped to **−20%…70%**. No City Favor term; the practical Charisma+Karma maximum is 60%, with the 70% cap retained for headroom. |
| D6 | Taxes & high-Karma services | Monthly bills reduced by up to 30% at high Karma / increased by up to 20% at low Karma; Tax Day surcharge waived at Virtuous+, doubled at Wanted/Outlaw. High-Karma benefits are **shop / tax / temple only** — no inn discounts. |
| D7 | Capture sale | Four options: licensed broker (standard gold, 0 Karma), **slaver (+60% gold, −5 Karma)**, release (+1 Karma), bond (+20 affection). **Slaver available everywhere.** House-full captures also offer broker/slaver/release instead of silently vanishing. |
| D8 | City gate | One-shot per travel/menu arrival. First low-Karma entry is a one-time warning. Then: **Suspect (−25…−49) = gate fee** (pay / turn away); **Wanted (−50…−74) = confrontation**; **Outlaw (−75…−100) = elite confrontation**. Wanted/Outlaw always offer pay / talk down / submit / fight / leave; Suspect is a soft squeeze with no fight. |
| D9 | Guard combat & jail | Non-lethal. Guards scale to player level, max 5 enemies, **no XP / loot / bestiary / capture / quest credit**. Victory = entry + cooldown. Defeat or submit = **jail** (fine + advance to next morning + wake at 50% HP), never the death screen. **Jail also grants +3 Karma** toward 0, once per 3 days globally; it shares the +8/day cap. |
| D10 | Atonement | Temple "Act of Contrition" restores **1 Karma per 50g**, up to the **same +8/day cap** (not a separate +10), only toward 0. Guild adds **atonement contracts** (+5 Karma, also counted toward the cap) at negative Karma. Good deeds and jail time are the other paths. |
| D11 | Naming | **Locked:** keep the new axis named **Karma**; rename the Prescript Ledger's display to **Prescript Debt** (internal `prescript_karma_stacks` unchanged). |
| D12 | Old saves | **Locked:** old saves default `karma_enabled=False` and stay OFF — there is no in-game enable path. `enable_karma()` remains tooling only and no longer seeds from favor. New characters start at 0 with `karma_enabled=True` by default. |
| D13 | Blackwake | **Locked:** Blackwake is lawless — no Karma gate, no guards, no jail, no guild. Low Karma is **respected**, not ignored: inverse inn pricing (negative Karma up to 20% off, positive Karma up to +20% "saint tax"); the Black Market keeps its inverse Karma discount. |
| D14 | Ashkara / Brinewatch | **Locked:** no special Karma rule. Brinewatch is a lawful working port; Ashkara has a guild and therefore law. Only Blackwake is the no-man's-land. |
| D15 | Toggle vs base game | **Locked:** per-save **character-creation toggle** in the shared Game Rules step. New characters default ON; old saves default OFF and cannot switch on later. The choice is final for the save. If playtesting shows the consequences are too harsh, a `full`/`merciful` intensity dial can be added later; it never turns Karma off. |

D1–D15 are locked. The design is fully locked for implementation.

---

## 3. Karma model

### 3.1 Data model

Add to `character.py::ensure_player_fields`:

```python
player.setdefault("karma_enabled", False)          # old saves; new characters choose in Game Rules
player.setdefault("karma_migrated", False)         # legacy marker (tooling only)
player.setdefault("family_enabled", False)         # Game Rules (family design)
player.setdefault("difficulty", "normal")           # Game Rules (effects later)
player.setdefault("game_rules_version", 1)

player.setdefault("karma", 0)                       # int, -100..+100
player.setdefault("karma_log", [])                  # last 50 {day, delta, reason, total}
player.setdefault("karma_daily", {"day": 0, "gained": 0})
player.setdefault("karma_gate", {
    "cooldown": {},          # city_id -> day the gate is quiet again
    "warning_seen": False,   # one-time first low-karma warning
    "watched_until": 0,      # "watched" flavor after jail/submission
    "jail_karma_day": -99,   # last day jail atonement was granted (3-day cooldown)
    "check_pending": False,  # one-shot arrival check (travel/menu load)
    "atonement_day": -99,    # last guild atonement contract generation
})
```

New root module **`karma.py`** is the single source of truth:

```python
KARMA_MIN, KARMA_MAX = -100, 100
KARMA_DAILY_CAP = 8
KARMA_TIERS = (
    # min, label, buy_pct, bills_pct
    ( 80, "Paragon",   +20, -30),
    ( 50, "Virtuous",  +15, -20),
    ( 25, "Respected", +10, -10),
    ( 10, "Good",       +5,  -5),
    ( -9, "Neutral",     0,   0),
    (-24, "Shady",      -5,  +5),
    (-49, "Suspect",   -10, +10),
    (-74, "Wanted",    -15, +15),
    (-100,"Outlaw",    -20, +20),
)

def get_karma(player): ...
def get_karma_tier(player): ...          # -> dict(min, label, buy_pct, bills_pct)
def change_karma(player, delta, reason, bypass_cap=False): ...
def get_shop_karma_pct(player): ...
def get_bills_mult(player): ...
def get_gate_response(player, city_id): ...
```

Rules:
- `change_karma` clamps to `KARMA_MIN..KARMA_MAX`.
- Positive deltas consume the daily cap. Only one-time quest/story rewards may pass `bypass_cap=True`; contrition, atonement contracts, jail, and good deeds all share the cap. When capped, log "Your conscience can only grow so much in a day." and apply 0.
- Append to `karma_log` (cap 50) and, on a **tier change**, write a Journal event and a session-log line.
- Never show a hidden alignment change. Every choice label carries its delta.

### 3.2 Tiers

| Tier | Karma | Label | Karma discount (`buy_pct`) | Monthly bills (`bills_pct`) | Gate response |
|---|---|---:|---:|---:|---|
| 4 | +80…+100 | **Paragon** | +20% | −30% | Saluted; Tax Day waived; free temple cure 1/day |
| 3 | +50…+79 | **Virtuous** | +15% | −20% | Saluted; Tax Day waived; temple blessing 50% off |
| 2 | +25…+49 | **Respected** | +10% | −10% | Normal; temple blessing 25% off; +1 bounty slot (optional) |
| 1 | +10…+24 | **Good** | +5% | −5% | Normal |
| 0 | −9…+9 | **Neutral** | 0 | 0 | Normal |
| −1 | −10…−24 | **Shady** | −5% | +5% | Suspicious dialogue only |
| −2 | −25…−49 | **Suspect** | −10% | +10% | **Gate fee** |
| −3 | −50…−74 | **Wanted** | −15% | +15% | **Confrontation** |
| −4 | −75…−100 | **Outlaw** | −20% | +20% | **Elite confrontation** |

`buy_pct` is added to the shop discount (positive = cheaper, negative = surcharge). `bills_pct` is added to the monthly-bill multiplier (negative = cheaper, positive = more expensive). The table values match `KARMA_TIERS` in §3.1. In **Blackwake**, the gate column does not apply — there is no gate; the inn/Black Market invert Karma instead (§6.6).

### 3.3 Change rules

- **Karma is a record, not a mood.** No daily drift, no passive decay. Only explicit choices and atonement change it.
- **Commitment, not success.** Choosing "Rob them" applies −4 immediately, even if the DEX check fails. Choosing "Help them" applies +2 even if the WIS check fails. Stats decide the *reward*, not the *moral record*. This is deliberate: it prevents rerolling for alignment and matches the fiction ("you tried").
- **Hidden acts are the one exception.** Back-room cheating is attempted before the outcome is known; its Karma penalty applies only when the player is caught. The choice label says "Karma only if caught." The ledger records what is witnessed, not private intent.
- **Routine play is neutral.** Bounties, dungeon clears, dispatch sweeps, and normal combat do not move Karma. This keeps the axis about choices, not farming.
- **Positive cap:** +8/day from **all repeatable positive sources** — good deeds, temple contrition, atonement contracts, and jail time. One-time quest/story rewards bypass the cap.
- **Negative uncapped:** the player can dig as deep as they like; the consequences are economic and legal, not a hidden wall.
- **No soft lock:** even at −100, the city gate always offers "submit to judgment", and atonement is always available. In **Blackwake** there is no gate at all; Karma is respected there, not enforced (§6.6). Karma still changes normally while you are there — the city simply refuses to police it.

### 3.4 Feedback

- Every change: session-log line `Karma −4 (Suspect −33) — Robbed the wounded adventurer.`
- Tier change: Journal event with the tier label, a one-line explanation, and the current benefits/penalties.
- `karma_log` powers a future "Reputation" section in the character/inventory screen; no new full screen in Phase 1.
- Colors: green for positive, amber for Shady/Suspect, red for Wanted/Outlaw. Always pair color with text.

### 3.5 New-character toggle — not a mid-game switch

**Locked (D15):** Karma is chosen in the shared **Game Rules** step at character creation. It is a per-save rule, not a global always-on flag and not a mid-game switch.

- **New characters:** Karma ON by default; the player can turn it OFF before creating the character.
- **Old saves:** Karma defaults OFF to avoid changing an in-progress game, and stays OFF. There is no in-game enable action.
- **No mid-game switch:** turning it off after earning Karma would freeze or delete the moral record; turning it on later would silently change an in-progress run. The choice is final for the save.
- **Family and difficulty** use the same step: the family system already plans a per-save yes/no at creation; a difficulty selector and future drastic-system toggles plug into the same registry.

Why this is the right compromise:
1. **Player control at the right moment.** Character creation is the consent point for rules that change the whole run.
2. **No balance fork mid-run.** The save is either classic or Karma-aware from the start; prices, gates, events, and Blackwake are consistent for the whole run.
3. **No save hazards.** There is no OFF↔ON transition after creation.
4. **No content branching inside one run.** Karma-off hides the Karma-only choices (rob/loot/steal/slaver) and uses a Charisma-only economy; Karma-on uses the full system. Each save sees one coherent ruleset.
5. **Extensible.** The Game Rules step is registry-driven; adding a new drastic system is a registry entry + `ensure_player_fields` default + hook checks, not a UI rewrite.

**Karma OFF — classic mode:**

| Surface | Behavior with `karma_enabled=False` |
|---|---|
| Karma UI | Hidden (top bar, shop header, character sheet, Journal tier entries). |
| Shop/blacksmith | Charisma ≤40% only; no Karma or City Favor component. |
| Event choices | Karma-only choices hidden; original help/bury/calm behavior remains. |
| Capture sale | Broker/release/bond only; slaver option hidden. |
| City gates | No Karma gate, no guards, no jail. |
| Blackwake | Normal inn/Black Market prices; no inverse Karma. |
| Atonement | Temple contrition, atonement contracts, jail atonement disabled. |
| Hallucination | No Karma shift. |
| Save fields | `karma` stays 0/dormant; `karma_enabled=False`. |

**If a dial is ever needed:** add a `full`/`merciful` **consequences intensity** preference later — `merciful` disables guard fights, halves Karma price modifiers, and removes the hallucination shift. It never turns Karma off. This is a Phase 3+ playtest decision, not v1.

---

## 4. Economy

### 4.1 Shop and blacksmith formula

`facilities/shop.py::get_discounted_price` becomes:

```python
charisma_discount = min(40, max(0, (CHA - 8) * 0.5))
karma_bonus       = get_karma_tier(player)["buy_pct"]  # +20 .. -20
total_discount    = max(-20, min(70, charisma_discount + karma_bonus))
price = max(1, int(base * (100 - total_discount) / 100))
# then the existing daily-event shop_discount / shop_surcharge
```

Karma is the only standing score, so there is no City Favor term and no guild-city special case; the formula is identical in every city. `facilities/blacksmith.py` calls `get_discounted_price`, so it inherits the change automatically (enhancement, commission, fusion fees).

The practical Charisma+Karma maximum is **60%** (40% Charisma + 20% Paragon); the **70%** cap is retained as headroom. City Favor was removed in v0.1.8.8.

Display in the shop header:
`Charisma 24% | Karma Respected (+34) 10% → 66% of base price (max 70% off)`

### 4.2 Black Market — inverse Karma

The Black Market is where a bad reputation is an asset:

```python
outlaw_discount = min(20, max(0, -karma * 0.2))   # 0 at karma >= 0, 20% at -100
price = base * (1 - outlaw_discount / 100)
```

- Positive Karma gets no black-market discount (the dealers do not trust a saint).
- Negative Karma gets up to 20% off.
- This is the criminal path's economic upside; it keeps the moral choice from being strictly "good is always better".
- **Blackwake:** the pirate haven has no law and no gate. Its inn uses the same inverse logic (negative Karma up to 20% off, positive Karma up to +20% "saint tax"). See §6.6.
- Phase 2: add a "Sell a captured girl" option at the Black Market as an additional route for house-full captures (the slaver is already available everywhere via §5.5).

### 4.3 Monthly bills and Tax Day

`facilities/monthly_billing.py`:

```python
mult = 1 + get_karma_tier(player)["bills_pct"] / 100   # 0.70 Paragon .. 1.20 Outlaw
total = int(round(sum(bills) * mult))
```

- Bills remain 20–180g/month (ship + high-tier mount upkeep); the percentage is modest, so this is a flavor/steady-state benefit, not the main Karma reward.
- `Tax Day` daily event: at Karma ≥ +50 the 15% shop surcharge is **waived**; at Karma ≤ −50 it becomes **30%**. This makes the high-karma reputation tangible on event days.
- Blackwake has no tax authority; monthly bills are global upkeep, not a city tax. The Karma modifier still applies as a general cost-of-living effect, but Blackwake's local expression is the inverse inn/Black Market (§6.6).
- Do not add a new sales tax. The existing economy does not need another hidden sink.

### 4.4 Temple (locked high-Karma service)

- Respected+ (≥ +25): temple blessing costs 25% less (50g → 37g; round to 37 or 38).
- Virtuous+ (≥ +50): temple blessing costs 50% less.
- Paragon (≥ +80): one free temple curse cure per day.
- **No inn discounts** (locked): inns are neutral. Blackwake's inn is the exception — it inverts Karma pricing (§6.6), not a high-Karma benefit.
- These are deliberately smaller than the shop/tax benefits; the temple is the "moral" reward mirror.

### 4.5 Guild

- Global **Karma** is the primary bounty scaler. There is no per-city favor and no guild-city-only bonus.
- Bounty generation uses Karma directly:
  - `level_offset = clamp(1…5, 2 + Karma // 30)`;
  - `num_bounties = clamp(2…7, 2 + Karma // 20)`;
  - kills and deadlines use `max(0, Karma)`;
  - `reward_gold` is multiplied by `1 + Karma / 200` (0.5× at −100, 1.5× at +100).
- Karma-off saves use the same board with a 0 Karma score: level-scaled contracts, no standing bonus.
- ⏳ Optional future: Virtuous+ adds +5% bounty gold, Paragon +10%; Respected+ adds +1 bounty slot (cap 7).
- Negative Karma adds **atonement contracts** (§7.2) without removing normal bounties. An outlaw should still be able to work; the guild just offers a way back. Atonement Karma counts toward the +8/day cap.
- Blackwake has no guild and no bounty board; Karma still applies globally elsewhere, and its economy is the Black Market and the inn.

### 4.6 Balance walkthrough

Charisma discount is `(CHA − 8) × 0.5`, capped at 40% — so CHA 20 = 6%, CHA 40 = 16%, CHA 88 = 40%. Karma adds +20…−20. There is no favor component.

| Situation | Numbers | Result |
|---|---|---|
| CHA 20, Neutral | 6% + 0 = 6% off | Charisma only; the old favor discount is gone. |
| CHA 40, Paragon | 16% + 20% = 36% off | Strong, but not the cap. |
| CHA 40, Outlaw | 16% − 20% = −4% | A small surcharge; infamy eats the Charisma discount. |
| CHA 8, Outlaw | 0 − 20% = −20% | 20% surcharge — the price of infamy. |
| CHA 88, Paragon | 40% + 20% = 60% off | Practical maximum; the 70% cap remains as headroom. |
| CHA 88, Outlaw | 40% − 20% = 20% off | High Charisma still helps, but infamy eats most of the top-end discount. |
| Slaver sale, level 10 duplicate | 600g → 960g, −5 Karma | +360g now; 5 points of contrition cost 250g. Net +110g plus gate risk. |
| Slaver sale, level 20 duplicate | 1,100g → 1,760g, −5 Karma | +660g now; contrition 250g. Net +410g plus gate risk. |

The intent: crime is **profitable now**, but the atonement price and the risk of gate/price penalties make it a real trade, not free money. Tune `slaver premium` and `contrition cost` together in playtest.

In Blackwake the shop formula does not apply (there is no shop); the inn and Black Market use inverse Karma instead (§6.6).

---

## 5. Choices in existing content

### 5.1 Design rules

1. **Visible before commitment.** Every choice label shows the stat, DC, gold/loot, and Karma delta. No surprise alignment.
2. **No double-dipping.** The old `heal_wounded` karma block is removed; the choice system becomes the single source.
3. **Stat checks use existing helpers.** Reuse `_select_party_member`, `_roll_stat_check`, and `get_effective_attribute` so party members, buffs, and curses work exactly as they do now.
4. **Failure is not a dead end.** Failed theft gives no loot and still applies the Karma delta (the attempt was the choice); failed help still applies +2 (you tried) and follows the existing failure consequence.
5. **One moral axis per event.** No hidden second currency and no local favor changes on top of Karma.

### 5.2 New choice step in stat-check rooms

`dungeon_rooms.py::handle_stat_check_room` currently prints the event, selects a party member, rolls, and branches. Add a choice step before member selection:

```python
event = STAT_CHECK_EVENTS.get(event_key) or WL_STAT_CHECK_EVENTS.get(event_key)
choice = None
if event.get("choices"):
    choice = _prompt_event_choice(event)   # numbered menu; "leave" returns None
    if choice is None:
        return "continue"
    change_karma(player, choice["karma"], choice["reason"])
    # choice may override the stat/DC
    stat_name = choice.get("stat", event["stat"])
    dc_delta = choice.get("dc_delta", 0)
else:
    stat_name = event["stat"]
    dc_delta = 0
```

- `choice["karma"]` is applied once, at commit time.
- `choice["outcome"]` selects the branch (`help`, `rob`, `loot`, etc.).
- Existing events without `choices` behave exactly as today, including all Wonderland events.
- The choice prompt is rendered with `_tmenu`; the existing terminal/GUI I/O path already supports it.

### 5.3 Event-by-event deltas

| Event | Choice | Stat / DC | Karma | Reward / consequence |
|---|---|---|---:|---|
| **Wounded Adventurer** | Help them | WIS (existing DC) | **+2** | Existing gold on success; existing death on failure. |
| | Rob them | DEX (DC 12 + floor×0.7) | **−4** | Success: `30 + floor×6 + rand(10,30)` gold. Failure: no gold, the adventurer dies/vanishes, −4 still. |
| | Walk away | — | 0 | No change. |
| **Ancient Corpse** | Bury them | STR (existing DC) | **+2** | Existing blessing on success; existing spirit damage on failure. |
| | Loot the remains | DEX (DC 10 + floor×0.8) | **−3** | Success: `25 + floor×4` gold + 30% item chance. Failure: spirit damage + curse, −3 still. |
| | Leave | — | 0 | No change. |
| **Monster Approaching** | Calm it | CHA (existing DC) | **+1** | Existing XP on success; forced fight on failure. |
| | Ambush it | — (starts combat) | **−2** | Normal combat rewards (XP/gold/drop). |
| | Leave | — | 0 | No change. |
| **Forgotten Shrine** (new) | Offer 50g | — | **+2** | Blessing (+2 all stats, 2 floors). |
| | Steal the offerings | DEX (DC 12 + floor×0.7) | **−3** | Success: `80 + floor×8` gold. Failure: curse (−2 all stats, 2 floors), −3 still. |
| | Leave | — | 0 | No change. |

Notes:
- The "rob" and "loot" amounts scale with floor so late-game theft stays tempting. The daily cap does not apply to negative Karma.
- The Forgotten Shrine is a new entry in `STAT_CHECK_EVENTS`; `dungeon.py` already picks event keys randomly from `get_stat_check_events(region)`, so it joins the pool without a new room type.
- Wonderland events are untouched; their dream-logic morality remains deferred (no Wonderland Karma dialogue/events in Phase 3).

### 5.4 New Forgotten Shrine event (copy)

```text
📜  Forgotten Shrine
A moss-eaten altar stands in a pocket of still air. Coins and faded
offerings are heaped at its base. The carved face has worn smooth,
but the air still feels watched.

1. Leave 50 gold and pray  — +2 Karma, blessing
2. Take the offerings      — DEX check (DC scales with floor), +gold, −3 Karma
3. Walk away
```

The exact prose can be tuned; the key is the visible trade.

### 5.5 Capture duplicate sale

`combat/capture.py::store_captured_girl` currently offers Sell / Release / Bond for duplicates. Replace with four options:

| # | Option | Gold | Karma | Notes |
|---|---|---|---:|---|
| 1 | **Sell to a licensed broker** | Standard `level×50 + 100` | 0 | The safe, respectable sale. |
| 2 | **Sell to a slaver** | `int(1.6 × standard)` | **−5** | The "more gain for reputation" choice. Confirm dialog with the name and exact numbers. |
| 3 | **Release to the wild** | 0 | **+1** | Mercy; the capture is lost. |
| 4 | **Bond with your existing girl** | 0 | 0 | +20 affection to the duplicate's existing counterpart. |

- Terminal path: `c_input("CAPTURE_DUPLICATE_CHOICE:")` accepts `1–4`; print the prices and Karma in the menu.
- GUI path: `gui/combat/action_panel.py::set_capture_choice_actions` grows to four buttons; `gui/screens/combat_screen.py` already routes the digit to the engine. Update the comment "Sell / Release / Bond" to "Broker / Slaver / Release / Bond".
- Use `karma.change_karma(player, -5, "Sold a captured girl to a slaver")` and the same function for +1 release.
- **Locked: the slaver option is available everywhere**, not only in cities with a Black Market. The Black Market can later offer a second route, but the duplicate-capture flow always has it.
- No local favor exists; the sale is underground. The bestiary entry stays (you did capture her).
- Narration: restrained, non-explicit, and never celebratory. The game's content direction already includes black-market slavery; this is the mechanical expression of it, not a new content level.

### 5.6 House-full capture

Current behavior: if the house is full, the captured girl is silently lost (`return False`). That is a missed choice and a bad player experience. Change to offer:

1. Sell to a licensed broker (standard gold, 0 Karma).
2. Sell to a slaver (+60% gold, −5 Karma).
3. Release (+1 Karma).

Bond is not offered when there is no existing duplicate to bond with. This makes the house-full state a real moral decision instead of a lost capture.

### 5.7 Choice sites (Phase 3)

- ✅ **Travel events**: a stranded traveler/castaway — help (+2 Karma), rob (+gold, −3 Karma), or walk away. Shown in world-map and legacy travel; hidden when Karma is off.
- ⏳ **Merchant room**: "Rob the merchant" (DEX or combat) as a high-risk crime; optional future work.
- ⏳ **Wonderland**: dream-logic choices remain deferred by request.
- ✅ **Bounty board**: atonement contracts (Phase 2). "Protect the caravan" vs "take the cargo" remains optional future work.

---

## 6. City entry and guards

### 6.1 Trigger and exclusions

Run the gate check from `gui/screens/city_screen.py`, **before** `_check_story_beats` and the Event Horizon intro:

- Trigger only when `karma <= -25`.
- Trigger on **travel/world-map arrival** and **menu load**, as a **one-shot check per arrival** (consume `karma_gate["check_pending"]`). Set the flag in the travel/world-map arrival path and in the load-game path; `CityScreen` clears it after the check. Do **not** trigger on dungeon returns, post-floor returns, or facility closes — a wounded party should not be ambushed at the gate after clearing a floor.
- Exclude `wonderland` (no city watch), **`blackwake`** (lawless pirate haven — no gate, no guards, no jail; §6.6), and any Event Horizon run. `isle_of_glass` can be included; it is a normal CityScreen.
- First low-karma entry: one-time **warning** (a 50g "processing fee" and a clear explanation). Set `karma_gate["warning_seen"] = True` and a **1-day** cooldown; the normal tier response starts on the next visit.
- After a real resolution (pay, talk down, submit, fight), set `karma_gate["cooldown"][city_id] = day + 3`. Flee sets a **1-day** cooldown. If Karma is still low, the next confrontation comes after the cooldown, not on every entry.
- **Turning away is not a resolution.** It sets no cooldown; if you come back, the gate is still there. This closes the "leave and re-enter to skip the gate" loophole without trapping the player.
- While the gate is unresolved, suppress `_check_story_beats` and the Event Horizon intro; resume them after paying, talking down, submitting, winning, or being jailed. Never stack a gate dialog and a story overlay.
- Gate checks are main-thread UI. The guard fight runs through `CombatScreen` (background thread + queues), exactly like other combats.

### 6.2 Gate response by tier

| Tier | Karma | Response |
|---|---:|---|
| Suspect | −25…−49 | **Gate fee**: `max(50, level × 10)` gold. Options: pay / turn away. No fight at this tier — the guards are squeezing you, not arresting you yet. |
| Wanted | −50…−74 | **Confrontation**: pay `max(100, level × 20)`, talk down (CHA check), submit to judgment, or fight **3 city guards**. |
| Outlaw | −75…−100 | **Elite confrontation**: pay `max(200, level × 30)`, talk down (harder check), submit, or fight **2 elite guards + 2 guards**. |

Talk-down check:
- Player's effective Charisma (the player is the one speaking), d20 + CHA vs `DC = 16 + (|karma| // 10)`, capped at 30.
- Success: pay **50%** of the fee and enter.
- Failure: guards attack (same as refusing).
- This gives a high-Charisma character a non-combat way through, consistent with the shop discount fantasy.

Submit to judgment:
- Always available, always the safety valve.
- Fine: `min(gold, max(100, level × 15))`.
- Heal the whole party to 50% HP (never below 1).
- Advance to the next morning via `time_blocks.end_day(player, slept=True)`.
- Set `karma_gate["watched_until"] = day + 2` (flavor: guards watch you in the city).
- Enter the city; jail grants the +3 atonement described in §6.4 (the only gate outcome that changes Karma).
- Journal entry: "You spent the night in a cell. The fine was paid; the city will be watching."

Leave / turn away:
- Return to the world map (or the previous screen) without entering.
- No Karma change, no cooldown (you can come back and choose differently).
- The player is never hard-locked out of the world map.

### 6.3 Guard combat rules

New helper **`combat/city_guards.py`**:

```python
def spawn_city_guards(player, tier):
    # tier: "wanted" -> 3 guards; "outlaw" -> 2 elites + 2 guards
    # Returns enemy dicts ready for CombatScreen(enemies=...)
```

- Add two YAML entries in `resources/enemies/enemies_data/all_enemies.yaml`:
  - `city_guard` — Human, base HP ~60, balanced mods.
  - `city_guard_elite` — Human, base HP ~90, heavier STR/CON.
- Runtime scaling: use `enemy_stats(key, player)` then scale `level`, `max_hp`, `hp`, `str_mod`, `con_mod`, `dex_mod` to the player's level:
  - Guard: level = player level; HP/mods × `1.0 + 0.06 × level` (tune).
  - Elite: level = player level + 3; HP/mods × `1.0 + 0.09 × level`.
- Flags on every guard enemy:
  ```python
  enemy["nonlethal"] = True
  enemy["no_bestiary"] = True
  enemy["no_loot"] = True
  enemy["no_xp"] = True
  enemy["guard"] = True
  ```
- `combat/combat_engine.py::prune_dead` and `_bestiary_kill` must skip `enemy.get("no_bestiary")`. This is the only engine change required.
- No gold/XP/item rewards: the gate flow does not call `add_gold_drop` or `gain_exp`. Guard fights are a consequence, not a farm.
- Capture: guards are not monster girls, so `net_can_capture` already rejects them; ensure the capture action does not list them (it filters `enemy.get("monster_girl")`).
- Victory: guards yield (no kill narration). Enter the city, set the cooldown, log "The guards lower their weapons. You are allowed through — under watch." No Karma change.
- Flee: return to the world map; set a 1-day cooldown; no Karma change.
- Defeat: **jail**, not death. The CityScreen `CombatScreen.on_result("dead")` callback intercepts and calls `city_guard_jail(player, city_id)` instead of switching to `DeathScreen`. This mirrors how the training-dummy flow intercepts results and switches back to the city.
- Party members: standard combat; no special hooks. Allies can be defeated and revived by the normal rules. The jail outcome heals everyone to 50%.

### 6.4 Jail outcome

```python
def city_guard_jail(player, city_id):
    day = player.get("day", 1)
    fine = min(player.get("gold", 0), max(100, player.get("level", 1) * 15))
    player["gold"] = player.get("gold", 0) - fine
    # heal party to 50%
    ...
    time_blocks.end_day(player, slept=True)
    player["karma_gate"]["cooldown"][city_id] = day + 3
    player["karma_gate"]["watched_until"] = day + 2
    # Served time = small atonement, once per 3 days, shared with the +8/day cap.
    if player.get("karma", 0) < 0 and day >= player["karma_gate"].get("jail_karma_day", -99) + 3:
        change_karma(player, +3, "Served your sentence")
        player["karma_gate"]["jail_karma_day"] = day
    # journal entry, session log, then CityScreen
```

- Gold may go to 0 but not negative for a jail fine (unlike monthly debt).
- **Jail is the only gate outcome that changes Karma**: +3 toward 0, once per 3 days globally, shared with the +8/day cap. This makes "submit/serve time" a genuine but slow atonement path.
- Paying, talking down, winning, or fleeing does **not** change Karma (locked O11). The gate is a consequence of Karma, not a second source; no death spiral.
- If the player has 0 gold, jail costs time only; they can still recover.

### 6.5 Why non-lethal

- A death screen for a reputation check is disproportionate and punishes experimentation.
- Jail is thematically apt for city guards and keeps the economy/choice tension.
- It guarantees no soft lock: even at −100, "submit" always works, and the temple/guild paths remain reachable.
- **Locked:** non-lethal jail; lethal guard fights are not planned. Jail atonement makes losing a gate fight less purely punitive and gives the player a reason to submit rather than reload.

### 6.6 Blackwake — the lawless city (Karma respected, not ignored)

Blackwake is the hidden pirate cove (sea-only; services: `inn`, `port`, `black_market`). It has no guild, no shop, no temple, no blacksmith, and no city watch.

- **No Karma gate.** `get_gate_response()` returns `None` for `city_id == "blackwake"`; no fines, guards, or jail.
- **Low Karma is respected.** The city does not ignore Karma; it inverts it:
  - **Inn:** negative Karma up to 20% off; positive Karma up to +20% ("saint tax").
  - **Black Market:** existing inverse Karma discount (up to 20% off at Outlaw).
  - **Port:** neutral travel, but outlaws get a 50-gold smuggler's ferry berth (Phase 3).
- **High Karma is not attacked**, just less favored: no gate, but the inn/black-market prices are worse. This keeps Blackwake a safe haven for outlaws without making it a free paradise for saints.
- **No guild standing.** Blackwake has no guild or bounty board; Karma still follows the player in from the wider world.
- **No jail atonement.** With no guards there is no jail, so Blackwake cannot be used to farm the +3 jail Karma.
- **Why Blackwake, not Brinewatch or Ashkara:** Brinewatch is a lawful working port (shipyard, trade hall, naval conscripts); its pirates are travel encounters. Ashkara has a guild and a black market, but the guild means contracts and law. Blackwake's own dialogue calls it "the pirate port" and says "the black market is the only market."
- **What this does for the design:** the criminal path gets a home base and a reason to exist; the lawful path still gets the best shops/temples/guilds. It also makes the world feel less monolithic.
- **Karma still changes in Blackwake** — dungeon choices, slaver sales, etc. still move the score. The city simply refuses to enforce it.

---

## 7. Atonement and recovery

### 7.1 Temple — Act of Contrition

Add to `facilities/temple.py::temple_menu` (all temple cities — Solmere, Sunreach, Coralhaven, Wonderland):

- **Act of Contrition** — restores negative Karma toward 0.
- Cost: **50g per Karma point**, up to the **same +8/day cap** as good deeds (no separate +10 allowance).
- Cannot raise Karma above 0 (virtue is earned, not bought).
- Cannot be used at positive Karma (nothing to atone).
- Journal entry + log: `Contrition: Karma +8 (−42 → −34). Cost: 400g.`
- This is the main gold sink for a criminal run. It turns "crime now" into "pay later", which is the intended tension; the shared cap prevents it from outrunning the rest of the recovery paths.

### 7.2 Guild — atonement contracts

At Karma ≤ −25, `facilities/guild.py` adds one **Atonement** contract per 7-day board refresh:

- Example: "Recover stolen relics from the marsh bandits", "Escort a caravan through the Ashfen", "Clear the shrine of the thing that moved in".
- Reward: **+5 Karma** (counts toward the +8/day cap), low gold, no monster-girl sale.
- The contract is a normal bounty-shaped entry so it reuses the existing board UI and turn-in flow.
- This is the portable recovery path for players who cannot reach a temple or are broke.

### 7.3 Good deeds

- The event choices in §5.3 and the shrine offering.
- Daily cap +8 from **all repeatable positive sources** (deeds, contrition, atonement contracts, jail); one-time quest/story rewards bypass.
- No automatic drift; the player's record is theirs.

### 7.4 What recovery is **not**

- Not a free reset. Contrition costs gold; atonement costs time; good deeds cost opportunity.
- Not hidden. The temple and guild explain the paths; the Journal records them.
- Not a Blackwake shortcut. The pirate haven has no temple or guild; it is a place to live with your reputation, not to erase it.
- Not required to "win". A player can stay an outlaw forever; they just pay different prices.

---

## 8. High-karma and low-karma benefits

### 8.1 High Karma (the "reputation dividend")

- Shop and blacksmith discount up to +20 points (the retired City Favor discount, now earned by choices).
- Monthly bills down to −30%.
- Tax Day surcharge waived at Virtuous+.
- Temple: blessing 25% off at Respected+, 50% off at Virtuous+, free curse cure 1/day at Paragon.
- **No inn discounts** (locked); inns are neutral except Blackwake's inverse pricing (§6.6).
- ⏳ Optional future: +1 bounty slot at Respected+, +5/10% bounty gold at Virtuous/Paragon.
- Dialogue: receptionists, shopkeepers, and guards recognize you. No new dialogue rewrite in Phase 1; a tier line can be added to existing dialogue dictionaries later.

### 8.2 Low Karma (the "gain now" path)

- Slaver sale +60% gold (available everywhere).
- Theft/robbery gold from events.
- Black Market discount up to 20% at Outlaw.
- **Blackwake safe haven:** no gate, no guards, no jail; the inn inverts Karma (negative up to 20% off, positive up to +20% saint tax). Low Karma is respected there.
- ✅ Phase 3: exclusive outlaw stock, Blackwake smuggler fare, and Karma-tier dialogue. Deeper shady quests remain optional future work.
- The cost: shop surcharge, higher bills, Tax Day doubled, gate confrontations in lawful cities, hallucination pressure.
- Do **not** make low Karma strictly worse. The whole point is "more gain in exchange for your reputation", so the immediate payout must be real.

### 8.3 Hallucination hook

`combat/hallucination.py` already reserves the input:

```python
def hallucination_tier(player):
    stacks = time_blocks.get_fatigue_stacks(player)
    shift = -1 if get_karma(player) >= 50 else (1 if get_karma(player) <= -50 else 0)
    return max(0, min(3, stacks + shift))
```

- Low Karma (≤ −50) raises the effective instability tier by 1 when a hallucination triggers; high Karma (≥ +50) lowers it by 1.
- `should_trigger` still requires fatigue stacks ≥ 2; Karma never *forces* a hallucination, it changes how bad it is.
- ✅ Phase 3 implemented in `combat/hallucination.py`; the tier is clamped to 0–3 and `should_trigger` still requires fatigue stack II. Wonderland and Karma-off saves never shift.

### 8.4 Prescript Ledger naming collision

**Implemented 2026-10-29 (v0.1.8.5):** the Ledger's combat-local display is now **Prescript Debt** (`DBT×N`). Internal `prescript_karma_stacks` names are unchanged for save compatibility.

- The Ledger's `prescript_karma_stacks` is a **combat-local debt** for ignoring a Prescript. It is not the player's moral record.
- Rename the player-facing display to **Prescript Debt**:
  - `combat/combat_ui.py`: `KRM×N` → `DBT×N`.
  - `combat/weapon/prescript_ledger.py` messages: "Karma" → "Debt", "Karmic Retribution" → "Debt Collected" (or keep the skill name, but describe it as Debt).
  - `resources/unique_effects.py` description: "adds Karma" → "adds Prescript Debt".
  - `facilities/guild.py` dialogue line "Karma comes due" → "the debt comes due".
  - Do not edit old changelog headers; add the rename note in the new version's changelog.
- Keep internal field names (`prescript_karma_stacks`) for save compatibility. A future cleanup can rename them with a migration if desired.
- **Locked (O2):** the new axis is **Karma**; the Ledger becomes **Prescript Debt**. The alternative "Renown" name is rejected.

---

## 9. UI/UX

### 9.1 Top bar and character sheet

- `CityScreen._update_top_bar` appends `Karma: Respected (+34)` (colored, text-first).
- In **Blackwake**, append `Karma: Outlaw (−82) — respected here` (or `— saint tax` for positive Karma) so the inversion is discoverable.
- `InventoryScreen`/character panel shows `Karma: Respected (+34) — +10% shop discount, −10% bills` with a short tier description.
- Do not add a new full screen. Karma belongs in existing surfaces.

### 9.2 Shop header

`facilities/shop.py::show_shop`:

```text
Charisma 24% | Karma Respected (+34) 10% → 66% of base price (max 70%)
```

- There is no City Favor segment; the same Charisma + Karma breakdown appears in every city.
- Show the final multiplier, not just the components, so the player can verify the math.
- If a daily event applies, show it on the next line as today.
- Blackwake has no shop; its inn shows `Outlaw rate: 20% off` / `Saint tax: +20%` instead.

### 9.3 Event choices

- Numbered menu with the exact delta:
  ```text
  1. Help the wounded adventurer (WIS DC 14) — +2 Karma
  2. Take their purse (DEX DC 15) — +120g, −4 Karma
  3. Walk away
  ```
- After the choice, print the Karma line immediately, before the roll, so the player sees the moral record update.
- On failure, print the consequence and repeat the Karma line if it was already applied.

### 9.4 Capture menu

```text
⌖ Duplicate Monster Girl Captured — Choose Action
[1] Sell to a broker — 600g
[2] Sell to a slaver — 960g, −5 Karma
[3] Release — +1 Karma
[4] Bond — +20 Affection
```

- Four buttons in the GUI panel; the existing digit input path accepts 1–4.
- A confirm dialog for option 2: "Sell [name] to a slaver for 960g? This will cost 5 Karma." This is the one irreversible choice that deserves a confirmation.

### 9.5 City gate dialog

- New reusable widget `gui/widgets/choice_dialog.py`:
  ```python
  choice_dialog(parent, title, message, options=[(label, callback), ...], focus_index=0)
  ```
  Main-thread only, modal, keyboard 1–N + Esc = leave.
- Used for the gate (and later for other multi-option modals).
- The gate message names the tier, the fee, and the alternatives in plain language. No lore-only hints.
- The gate dialog never appears in Blackwake (no gate). The inn/Black Market inversion is explained in their headers instead.

### 9.6 Notifications

- Session log + Journal only, per the project convention.
- No toasts from facility threads.
- Tier changes are the only Karma events that get a Journal entry; point changes go to `karma_log` and the session log.
- `karma_log` entries are capped at 50 to keep saves small.

---

## 10. Save compatibility and migration

### 10.1 New fields

Registered via `character.py::ensure_player_fields` (`.setdefault`), so old saves load cleanly:

```python
player.setdefault("karma_enabled", False)
player.setdefault("karma_migrated", False)
player.setdefault("family_enabled", False)
player.setdefault("difficulty", "normal")
player.setdefault("game_rules_version", 1)

player.setdefault("karma", 0)
player.setdefault("karma_log", [])
player.setdefault("karma_daily", {"day": 0, "gained": 0})
player.setdefault("karma_gate", {
    "cooldown": {}, "warning_seen": False, "watched_until": 0,
    "jail_karma_day": -99, "check_pending": False, "atonement_day": -99,
})
```

### 10.2 Legacy City Favor data (ignored)

City Favor is removed. Old saves may still contain `player["favor"]`; no live system reads or writes it. **D15 was revised on 2026-10-29:** Karma is final at character creation, so there is no in-game enable path. `enable_karma()` remains in `karma.py` for save tooling and diagnostics only; it no longer seeds from favor.

- New character, Karma ON: `karma = 0` (Neutral).
- New character, Karma OFF: Karma stays dormant at 0.
- Old save: `karma_enabled = False` and stays OFF.
- Normal play never reads City Favor, and no code seeds Karma from it.

### 10.3 Idempotency

- `ensure_player_fields` runs on every load; it never overwrites a player's current Karma or rule choice.
- Field defaults are additive and safe for old saves.
- `karma_log` is trimmed to 50 on write.
- **No mid-game switch:** `karma_enabled` does not change after character creation.
- No ally or house-girl fields are needed.

---

## 11. Integration map

| File | Change |
|---|---|
| **`karma.py`** (new) | Constants, tier table, `is_enabled`, `ensure_state`, `get_karma`, `change_karma`, `change_karma_toward_zero`, `get_daily_positive_remaining`, `get_karma_tier`, `get_shop_karma_pct`, `get_bills_mult`, `get_gate_response`, `get_gate_talkdown_dc`, `is_lawless_city`, `add_journal`; legacy `enable_karma` is tooling-only and does not seed from favor. Single source of truth. |
| `character.py` | `GAME_RULES` / `default_game_rules`; Game Rules defaults in `ensure_player_fields` (old saves `karma_enabled=False`); `build_character(..., game_rules=...)`; no auto-seed. |
| `gui/screens/char_create_screen.py` | ✅ **Step 4: Game Rules** (Karma ON/OFF, family/difficulty placeholders); choice is final; passes `game_rules` to `build_character`; Name & Save is Step 5. |
| `facilities/shop.py` | ✅ Karma-only price formula; header shows Charisma + Karma; no City Favor term or guild-city special case; Karma-tier shopkeeper line. |
| `facilities/blacksmith.py` | ✅ Inherits the Karma price via `get_discounted_price`; Karma-tier blacksmith line. |
| `facilities/black_market.py` | ✅ Inverse Karma discount; outlaw-only sealed crate at Karma ≤ −25 (not in Wonderland); Karma-tier dealer line. |
| `facilities/monthly_billing.py` | Apply `get_bills_mult` to the total; `1.0` when Karma is off. |
| `facilities/guild.py` | ✅ Karma-scaled bounty board (level offset, count, kills, deadline, gold); ✅ one weekly Atonement contract at Karma ≤ −25; +5 Karma on turn-in, shared daily cap; ✅ Karma-tier guild clerk line. No City Favor reads or writes. |
| `facilities/temple.py` | ✅ Phase 2 — Act of Contrition (50g/point, +8/day shared cap, never above 0). High-Karma blessing discount/free cure remains optional future polish. |
| `facilities/inn.py` | ✅ Blackwake Karma dialogue for the innkeeper; all other inns stay neutral. ⏳ Blackwake inverse Karma pricing (negative 0…20% off, positive 0…20% saint tax) is deferred because the inn currently has no gold cost (`rest_cost` is unused). |
| `dungeon_rooms.py` | Choice step in `handle_stat_check_room`; choice data for 3 events; new Forgotten Shrine event; remove the old `heal_wounded` karma block; hide Karma-only choices when off. |
| `combat/capture.py` | 4-way duplicate menu + house-full broker/slaver/release; Karma calls; hide the slaver when off. |
| `gui/combat/action_panel.py` | 4 buttons in `set_capture_choice_actions`; labels with prices/Karma. |
| `gui/screens/combat_screen.py` | ✅ Capture-choice input 1–4; `city_guard` top-bar context. The CityScreen `on_result` callback performs the jail/return routing. |
| `gui/screens/city_screen.py` | ✅ `_begin_arrival` / `_start_karma_gate` run before story beats; warning/fee/talk/submit/fight/turn-away dialogs; jail and guard-result wiring; top-bar Karma and Watched tag; skip in Blackwake/Wonderland/EH. |
| `gui/screens/world_map_screen.py`, `gui/screens/main_menu_screen.py` | ✅ Set the one-shot `karma_gate["check_pending"]` flag on city travel arrival and save load. |
| `gui/widgets/confirm_dialog.py` | ✅ Reuses the existing `choice_dialog()` multi-option modal; no new widget file needed. |
| `combat/city_guards.py` (new) | ✅ Guard spawning/scaling, non-lethal flags, gate cooldowns, jail outcome (+3 Karma), party heal, Blackwake exclusion. |
| `resources/cities.py` | No data change; `city_id == "blackwake"` remains the lawless exception. Guild-city checks are no longer needed for favor scope. |
| `combat/combat_engine.py` | ✅ `prune_dead` / `_bestiary_kill` skip `no_bestiary`. |
| `bestiary.py` | ✅ `get_total_enemy_count` skips `city_only` guards, so the bestiary can still reach 100%. |
| `resources/enemies/enemies_data/all_enemies.yaml` | ✅ `city_guard`, `city_guard_elite` entries flagged `city_only: true`. `dungeon`, `facilities/travel_events`, and `facilities/guild` skip `city_only` so guards never appear in dungeon/travel/bounty pools. |
| `combat/hallucination.py` | ✅ Karma shift in `hallucination_tier` (−1 at +50, +1 at −50); no shift when off; Wonderland excluded; `should_trigger` still requires fatigue stack II. |
| `combat/combat_ui.py`, `combat/weapon/prescript_ledger.py`, `resources/unique_effects.py` | ✅ Done 2026-10-29 — Ledger display renamed to Prescript Debt (`DBT`); internal field unchanged. |
| `event_horizon.py` / `wonderland_curses.py` | No change; excluded from the gate. |
| **`karma_dialogue.py`** (new) | ✅ Karma-tier lines for receptionists, shops, blacksmiths, guilds, Black Markets, ports, guards, and Blackwake inns; Blackwake has outlaw/saint variants; Wonderland and non-Blackwake inns return None. |
| `facilities/travel_events.py` | ✅ Land/sea moral event (help / rob / walk away); Karma-only, filtered out when Karma is off; `_event_pool()` centralizes the filter. |
| `facilities/port.py`, `facilities/travel.py` | ✅ Mark arrivals for the gate check; Blackwake outlaws get a 50g smuggler ferry berth. |
| `gui/screens/inventory_screen.py` | ✅ Stats & Equipment tab shows Karma tier, shop/bill effects, and the last three Karma changes. |
| `tests/_diag_karma.py` (new) | Tier boundaries, Karma-only price/tax math, daily cap, legacy helper ignoring City Favor, gate response, Blackwake inversion, jail atonement, toggle-off Charisma-only mode, Game Rules plumbing. |
| `tests/_diag_karma_phase2.py` (new) | Gate tiers/cooldowns/menu options, guard squads/flags, no-bestiary pruning, jail fine/heal/Karma cooldown, temple contrition, guild atonement generation/turn-in, pending-flag consumption, gate action wiring. |
| `tests/_diag_karma_phase3.py` (new) | Hallucination shift/stack-II guard, Karma dialogue (including Wonderland exclusion), travel moral event + world-map dialog, outlaw stock, smuggler fare, arrival helper. |
| `README.md`, `wiki/index.html`, `gui/screens/changelog_screen.py` | ✅ Updated for Karma Phase 3 (Wonderland-specific content deferred). |

---

## 12. Balance constants (initial tuning)

| Constant | Initial value | Notes |
|---|---:|---|
| `KARMA_MIN/MAX` | −100 / +100 | Hard clamp. |
| Tier thresholds | ±10, ±25, ±50, +80 | See §3.2. |
| `KARMA_DAILY_CAP` | +8 | All repeatable positive sources (deeds, contrition, atonement, jail). |
| Shop Karma component | −20…+20 | Added to Charisma only; practical max 60%, total cap 70% / floor −20%. |
| Black Market inverse | 0…20% | `min(20, -karma × 0.2)`; Blackwake inn uses the same rule once `rest_cost` is wired. |
| Bills multiplier | 0.70…1.20 | Paragon…Outlaw. |
| Tax Day | waived at +50; ×2 at −50 | Daily event only. |
| Gate thresholds | −25 / −50 / −75 | Suspect / Wanted / Outlaw. |
| Gate fees | 10 / 20 / 30 × level (min 50/100/200) | Pay or talk down (50% on success). |
| Talk-down DC | `16 + |karma| // 10`, cap 30 | Player's effective Charisma. |
| Jail fine | `min(gold, max(100, level × 15))` | No negative gold. |
| Jail atonement | +3 Karma, once per 3 days | Only toward 0; counts toward the cap; no jail in Blackwake. |
| Gate cooldown | 3 days per city | Flee = 1 day. |
| Contrition | 50g per point, +8/day | Shared cap; only toward 0. |
| Atonement contract | +5 Karma | Counts toward the cap; one per 7-day board refresh. |
| Blackwake | no gate/jail | Low Karma respected; inn inverse 0…20%; no guild/temple. |
| Slaver premium | +60% of standard sale | Current standard `level×50+100`. |
| Release | +1 Karma | Loses the capture. |
| Guard counts | Wanted 3; Outlaw 2 elite + 2 guard | Max 5, matches combat cap. |
| Guard scaling | player level; elite +3 | HP/mods × level factor; tune with a sim. |

**Balance checks to run before shipping:**
- A player at Charisma 88 / Paragon reaches 60% off, below the 70% cap.
- A player at Charisma 8 / Outlaw pays a 20% surcharge, not more.
- The same Charisma + Karma price applies in every city; no favor or guild-city special case remains.
- Three slaver sales (−15 Karma, ~+1,080g at level 10) do not trivialize the early economy; contrition for those 15 points costs 750g, leaving ~330g net plus gate risk.
- A full crime spree to −75 cannot happen in the first two dungeon floors without deliberate choices.
- Jail can never reduce gold below 0 or kill a party member.
- Jail atonement cannot be farmed faster than +3 per 3 days; Blackwake has no jail at all.
- No guard fight can be farmed for XP/loot/bestiary.

---

## 13. Phases

### Phase 0 — Foundation ✅ Implemented 2026-10-29

- Add `karma.py`, player fields (`karma_enabled` included), legacy-data handling, tier helpers.
- Add the Ledger display rename (Prescript Debt) to avoid the collision before the new Karma UI appears.
- Add `tests/_diag_karma.py` for tier boundaries, clamp, daily cap, price/bill math, legacy-data handling, and toggle behavior.
- Add the Karma line to the city top bar and shop header **only when `karma_enabled`** (at Neutral it reads `Karma: Neutral (0)`).
- **Exit criteria:** old saves load cleanly with `karma_enabled=False`; new characters default ON; legacy data handling is idempotent; all diagnostics pass; no mid-game switch.

### Phase 1 — Choices and economy ✅ Implemented 2026-10-29

**Implemented in this pass:** `karma.py`; Game Rules step; shop/blacksmith pricing, monthly bills, Tax Day, Black Market inverse; event choices + Forgotten Shrine; 4-way capture + house-full disposition; city top-bar Karma; `tests/_diag_karma.py`.

- Shared **Game Rules** step at character creation (Karma ON/OFF; family/difficulty entries reserved in the registry).
- `build_character(..., game_rules=...)` and `ensure_player_fields` defaults.
- Choice step in `handle_stat_check_room`; deltas for Wounded Adventurer, Ancient Corpse, Monster Approaching.
- New Forgotten Shrine event (hidden when Karma is off).
- 4-way duplicate capture sale + house-full sale (slaver hidden when Karma is off).
- Karma shop/blacksmith pricing, black market inverse, monthly bills, Tax Day.
- City Favor was temporarily scoped to guild cities, then removed entirely in v0.1.8.8.
- `karma_enabled` gating across shop, events, capture, Blackwake, and temple.
- Blackwake inverse Black Market pricing (no gate yet; Karma-off keeps normal prices). Inn inversion is deferred until the inn charges gold (`rest_cost` is currently unused).
- Journal/log feedback; event choice labels with exact deltas.
- **Exit criteria:** a full good playthrough can reach Respected; a deliberate crime run can reach Wanted; prices/taxes match the table; no double-counted karma; old Wonderland events unchanged; Karma-off saves use Charisma-only pricing and never see Karma-only choices.

### Phase 2 — Consequences and recovery ✅ Implemented 2026-10-29 (v0.1.8.6)

- City gate detection + existing `choice_dialog` (only when `karma_enabled`), one-shot per travel/menu arrival.
- `combat/city_guards.py`, guard YAML entries, non-lethal combat, jail outcome.
- Jail +3 Karma atonement (once per 3 days, shared cap).
- Blackwake / Wonderland / Event Horizon excluded from the gate.
- No in-game Karma enable for old saves (D15 revised); the character-creation choice is final.
- Temple contrition; guild atonement contracts.
- Gate cooldown, first warning, watched status.
- **Exit criteria:** no soft lock at −100; jail never shows the death screen; guard fights give no XP/loot/bestiary; submitting always enters the city; atonement works from a real save; Blackwake has no gate and no jail; Karma-off saves never trigger the gate; old saves stay OFF.

### Phase 3 — Polish and breadth ✅ Implemented 2026-10-29 (v0.1.8.7)

- ✅ Hallucination Karma shift (−1 tier at +50, +1 at −50; still requires fatigue stack II).
- ✅ Karma-tier dialogue lines for receptionists, shopkeepers, blacksmiths, guild clerks, portmasters, guards, and Blackwake innkeepers via `karma_dialogue.py`.
- ✅ Blackwake dialogue + 50-gold smuggler ferry berth for negative Karma.
- ✅ Travel-event moral choice (help / rob / walk away); hidden when Karma is off. World-map journeys and legacy travel both use it.
- ✅ Black Market outlaw crate at Karma ≤ −25.
- ⏳ Wonderland-specific Karma content (dialogue, events, hallucination interactions) is deferred by request. Wonderland remains excluded from Karma gates and Karma dialogue.
- ⏳ Optional bounty bonuses and the `karma_consequences` comfort dial remain optional future work.
- ✅ README/changelog updates; Stats & Equipment tab now shows a Karma section with recent history.
- **Exit criteria:** content is discoverable, no hidden alignment, documentation matches implementation.

### Phase 3.5 — City Favor removal ✅ Implemented 2026-10-29 (v0.1.8.8)

- ✅ Removed City Favor from shop/blacksmith pricing, guild bounty scaling, dispatch rewards, `heal_wounded`, New Moon Festival, and all UI.
- ✅ Guild bounty level offset, count, kills, deadlines, and gold now read global Karma; no per-city standing score remains.
- ✅ New Moon Festival now grants **+25% bounty gold** instead of favor; dispatch reports grant gold/items/EXP only.
- ✅ Karma-off saves use Charisma-only shop pricing and level-scaled guild contracts.
- ✅ Legacy `player["favor"]` data is ignored; no migration and no seed path.
- **Exit criteria:** no live code reads `player["favor"]`; every city uses the same Karma score; tests and docs no longer describe City Favor as current behavior.

**Why this order:** Phase 0 is low-risk infrastructure; Phase 1 delivers the player-facing loop the request is about; Phase 2 adds the riskiest combat/screen-lifecycle work after the economy is proven; Phase 3 is content polish. Guards are not skipped — they are Phase 2, and the design is complete here.

---

## 14. Testing and verification

### 14.0 Current verification (2026-10-29, v0.1.8.8)

- `tests/_diag_karma.py` passes (tiers, toggle, cap, Karma-only shop/Tax Day, bills, Black Market, gates, Game Rules plumbing, legacy favor ignored).
- `tests/_diag_karma_phase2.py` passes (gate tiers/menus/cooldowns, guard squads/flags, no-bestiary pruning, jail fine/heal/Karma cooldown, temple contrition, Karma-scaled guild bounties, atonement, pending flag, gate action wiring).
- `tests/_diag_karma_phase3.py` passes (hallucination shift and stack-II guard, Karma dialogue + Wonderland exclusion, travel moral event and world-map dialog, outlaw stock, smuggler fare, arrival helper).
- `tests/_diag_item_economy.py`, `tests/_diag_prescript_ledger.py`, `tests/_diag_quests.py`, and `tests/_diag_dispatch.py` pass.
- `py_compile` is clean for all touched files.
- `tests/_diag_local_imports.py` reports a **pre-existing** `combat/status_effects.py` warning unrelated to Karma.

### 14.1 New diagnostic `tests/_diag_karma.py`

- Tier boundaries: −100, −75, −74, −50, −49, −25, −24, −10, −9, 0, +9, +10, +24, +25, +49, +50, +79, +80, +100.
- `change_karma`: clamp, daily cap across **all** positive sources, log trim, tier-change journal, one-time quest bypass only.
- Toggle check: new characters default `karma_enabled=True`; old saves default `False`; the choice is final for the save.
- `get_discounted_price`: CHA 8/20/40/88 × Karma −100/−50/0/50/100 in both guild and non-guild cities; with no daily events, assert `1 ≤ price ≤ base × 1.20`, and the same formula applies everywhere. With `karma_enabled=False`, assert Charisma-only pricing and no Karma term.
- `get_bills_mult`: Paragon 0.70, Outlaw 1.20; `1.0` when disabled; bills never negative.
- `get_gate_response`: None above −25; Suspect/Wanted/Outlaw at boundaries; excluded cities (`wonderland`, `blackwake`); cooldown; **None everywhere when `karma_enabled=False`**.
- Inn inversion: **deferred** until the inn charges gold; Black Market inversion is covered instead (Karma −100 → 20% off, +100 → full price).
- Jail: +3 Karma, 3-day cooldown, shared cap, never above 0; Blackwake has no jail.
- Contrition: +8/day shared cap; atonement contracts +5 count toward the cap.
- Legacy data: a stray `player["favor"]` value is ignored; `enable_karma()` does not seed from it; new game starts at 0.

### 14.2 Event/capture checks

- `tests/_temp_karma_events_check.py` (temporary, delete after): simulate each choice, verify the Karma delta is applied once, before the roll; failure still applies the delta; "leave" applies 0.
- Karma-off: rob/loot/steal/ambush choices hidden; Forgotten Shrine absent; slaver option hidden; original help/bury/calm branches unchanged.
- Capture: broker / slaver / release / bond prices and deltas; house-full path offers the sale; duplicate path unchanged for bond.
- Verify the old `heal_wounded` karma block is gone (no double gain).

### 14.3 Combat checks

- Guard spawn: 3 guards at Wanted; 2 elites + 2 guards at Outlaw; never more than 5.
- `prune_dead` skips `no_bestiary`; bestiary count does not increase after a guard fight.
- No XP/gold/items after a guard fight.
- Player defeat in a guard fight → jail, not DeathScreen; HP restored to 50%; time advanced; fine clamped; +3 Karma if eligible.
- Flee → world map, cooldown, no death.
- Capture action does not list guards.
- Blackwake: `get_gate_response` returns None; no guard spawn path; Black Market inversion applies (inn inversion deferred until `rest_cost` is wired).
- Optional: `tests/_sim_karma_guards.py` to check win rates at level 10/20/40; tune HP/mods.

### 14.4 GUI/manual checks

The full player-facing pass lives in
[`karma_playtest_checklist.md`](./karma_playtest_checklist.md). At minimum:

- New character flow: the Game Rules step appears before Name & Save; Karma defaults ON; an OFF choice persists to the save.
- The Game Rules step states that the choice is final; there is no "enable later" text or action.
- Old save: Karma defaults OFF and stays OFF; no Karma UI, gate, or atonement appears.
- Gate dialog appears before story beats and does not stack with them.
- Gate does not trigger on dungeon return or facility close.
- Story beats still play after paying/submitting.
- Shop header math matches the actual price, and no shop/guild/blacksmith surface shows City Favor.
- Event choice labels fit the terminal/GUI log; no raw `print()`/`input()`.
- No tkinter widget creation from a background thread.
- Problems panel clean for touched files.
- `tests/_diag_local_imports.py` passes (no new local-import traps).

### 14.5 Save checks

- Copy a real save, load it read-only, verify no unexpected mutations before save.
- Save/load round-trip preserves `karma`, `karma_log`, `karma_gate`.
- Old saves load with `karma_enabled=False` and Karma 0; any legacy `favor` data is ignored and not displayed.
- A save at −100 can still enter a lawful city via submit; a save at +100 can shop at the cap.
- A save at −100 enters Blackwake freely and sees inverse Black Market prices; a save at +100 pays normal Black Market prices (inn inversion is deferred).
- A Karma-off save never shows Karma UI or gates and uses Charisma-only pricing.

### 14.6 Phase 3 checks

- Hallucination tier shifts at ±50, never below 0 or above 3, and cannot trigger from fatigue stack I.
- Karma dialogue appears for high/low tiers, includes Blackwake outlaw/saint variants, and returns None in Wonderland.
- Travel moral event appears in both world-map and legacy travel; hidden when Karma is off; help/rob deltas respect the daily cap.
- Black Market outlaw crate is visible only at Karma ≤ −25 and not in Wonderland.
- Blackwake smuggler fare is 50g only for negative Karma; other ports/cities stay at 100g.
- Stats & Equipment shows Karma tier, shop/bill effects, and recent history.
- Guild bounties scale from Karma, and no screen displays City Favor.
- README/wiki match the implemented behavior; Wonderland-specific Karma content remains deferred.

---

## 15. Decision status

| # | Decision | Status |
|---|---|---|
| O1 | Dual-axis vs full replacement | 🔒 **Revised 2026-10-29 — full replacement.** Karma is the only standing score; City Favor is removed. |
| O2 | Prescript Debt vs Renown | 🔒 **Locked** — Prescript Debt. |
| O3 | Gate trigger frequency | 🔒 **Locked** — one-shot per travel/menu arrival; 3-day cooldown after resolution. |
| O4 | Non-lethal jail vs death | 🔒 **Locked** — non-lethal jail; +3 Karma atonement. |
| O5 | Slaver location | 🔒 **Locked** — everywhere. |
| O6 | Positive cap | 🔒 **Locked** — +8/day; negative uncapped. |
| O7 | Contrition +10/day | 🔒 **Resolved** — +8/day shared cap; no conflict with O6. |
| O8 | Old-save seed | 🔒 **Superseded 2026-10-29** — no in-game enable/seed; legacy helper only. |
| O9 | High-Karma services | 🔒 **Locked** — shop / tax / temple; no inn. |
| O10 | Hallucination | 🔒 **Locked / implemented** — yes, Phase 3; Wonderland and Karma-off saves do not shift. |
| O11 | Gate Karma change | 🔒 **Locked** — no, except jail's +3 atonement. |
| O12 | Road merchants | 🔒 **Locked** — no. |
| O13 | Blackwake lawless city | 🔒 **Locked** — low Karma respected; no gate/jail; inverse inn/Black Market. |
| O14 | Ashkara/Brinewatch special rules | 🔒 **Locked** — none; only Blackwake is lawless. |
| O15 | Toggle vs base game | 🔒 **Locked** — per-save character-creation toggle; new characters default ON; old saves default OFF; the choice is final. |

All decisions are locked. Phase 0, Phase 1, Phase 2, Phase 3, and the City Favor removal are implemented; Wonderland-specific Karma content is intentionally deferred.

---

## 16. Documentation, changelog, and backlog plan

### At implementation

- ✅ Done 2026-10-29: bumped to **v0.1.8.5**, **v0.1.8.6**, **v0.1.8.7**, and **v0.1.8.8** with the Phase 1/2/3 and City Favor removal changelog blocks. Version consistency passes.
- ✅ v0.1.8.8: updated `README.md` to present **Karma** as the single standing score; removed the City Favor section.
- ✅ Phase 3: regenerated `wiki/index.html` from the updated README/wiki source (city-only guards excluded from the enemy database).
- Mark Phase 0–3 progress in this doc; do not delete the plan.
- ✅ Updated `.github/skills/pandemoniumhelper/references/architecture.md` with `karma.py` and `combat/city_guards.py`.
- ✅ `/memories/repo/karma-system.md` records the locked decisions and pitfalls.
- Document the **Game Rules** step (Karma ON/OFF) as a final per-save choice. Do **not** add a mid-game switch; a `karma_consequences` intensity dial can be added later as a comfort/difficulty preference.

### Backlog

- Move `Crime & guards` from §7 (Low) to the "in flight" table in §0, linked to this doc.
- Keep `Karma` as the canonical name; note the Prescript Debt rename.

---

## 17. New-game Game Rules step (shared framework)

**Purpose:** one character-creation step for systems that drastically change a run — Karma, the family system, difficulty, and future rules.

### 17.1 Wizard placement

Current wizard (`gui/screens/char_create_screen.py`): 1 Race, 2 Class, 3 Allocate, 4 Name & Save Slot.

New: 1 Race, 2 Class, 3 Allocate, **4 Game Rules**, 5 Name & Save Slot.

The step is a scrollable list of rule cards with a one-line "what changes" and a "recommended" marker. It is main-thread UI; no facility/combat thread involvement.

### 17.2 Rule registry

Add `GAME_RULES` (in `character.py`, imported by the creation screen) as the single registry:

| Field | Type | New-character default | Old-save default | Status |
|---|---|---|---|---|
| `karma_enabled` | bool | **True** | **False** | Phase 1 |
| `family_enabled` | bool | **False** | **False** | Family design — stored now, effects when the family system ships |
| `difficulty` | choice (`story`/`normal`/`hard`) | `normal` | `normal` | Framework only; effects need a separate difficulty design |
| `game_rules_version` | int | 1 | 1 | Migration/format version |

Each entry carries `id`, `label`, `description`, `type`, `options`, `default_new`, `default_old`, `implemented`, and `locked_after_creation`.

### 17.3 UI copy

- **Karma** (default ON): "Choices change prices, taxes, guild contracts, city gates, Blackwake, and atonement. Off disables Karma choices and gates; Charisma alone sets prices and guild contracts scale by level only."
- **Family system** (default OFF): "Mature family content. This choice is stored now; the system activates when it ships."
- **Difficulty** (default Normal): "Normal for now. Story/Hard options arrive with the difficulty system." Show the row disabled until the effects exist.
- Intro: "Choose the rules for this save. These choices last for the whole save." No footer promising a later enable.

### 17.4 Storage and migration

- Top-level fields in the player dict: `karma_enabled`, `family_enabled`, `difficulty`, `game_rules_version`.
- `build_character(..., game_rules=None)` writes the selected values; new characters default Karma ON.
- `ensure_player_fields` defaults old saves to `karma_enabled=False`, `family_enabled=False`, `difficulty="normal"`, `game_rules_version=1`.
- The rule set is final: no in-game enable/disable path. `karma.enable_karma()` is legacy tooling only and is not called by any screen.
- A rule that is not implemented yet is stored but inert; hooks check `is_enabled`/the rule field, not the UI state.

### 17.5 Hooks that must read `karma_enabled`

- `karma.is_enabled(player)` is the single gate.
- Shop/blacksmith: Charisma-only pricing when off.
- `dungeon_rooms.py`: hide Karma-only choices and the Forgotten Shrine.
- `combat/capture.py` / GUI action panel: hide the slaver option.
- `gui/screens/city_screen.py`: skip the gate and Karma top-bar line.
- `facilities/black_market.py`: no inverse Karma in Blackwake. Inn inversion is deferred until `rest_cost` is wired.
- `facilities/temple.py`, `facilities/guild.py`: no contrition/atonement contracts.
- `combat/hallucination.py`: no Karma shift.
- `facilities/monthly_billing.py`: `get_bills_mult` returns 1.0.

### 17.6 Implementation order

- **Phase 1:** Game Rules step skeleton, Karma ON/OFF, `build_character` plumbing, shop gating, diagnostic.
- **Family:** add the real `family_enabled` behavior when `family_system_design.md` ships; the toggle already exists in the step.
- **Difficulty:** separate design; add the selector once its effects exist (do not ship an inert difficulty choice; show the row disabled meanwhile).
- **Future drastic systems:** add a registry entry + `ensure_player_fields` default + hook checks; no UI rewrite.

---

## Appendix A — Choice copy bank

**Wounded Adventurer**
- `Help them (WIS check, DC scales with floor) — +2 Karma`
- `Take their purse (DEX check, DC scales with floor) — +gold, −4 Karma`
- `Walk away`

**Ancient Corpse**
- `Bury them with proper rites (STR check, DC scales with floor) — +2 Karma`
- `Loot the remains (DEX check, DC scales with floor) — +gold/item, −3 Karma`
- `Leave them be`

**Monster Approaching**
- `Calm it (CHA check, DC scales with floor) — +1 Karma, XP`
- `Ambush it — combat loot, −2 Karma`
- `Back away`

**Forgotten Shrine**
- `Offer 50 gold — +2 Karma, blessing`
- `Take the offerings (DEX check, DC scales with floor) — +gold, −3 Karma`
- `Leave`

**Slaver confirmation**
> Sell **[name]** to a slaver for **960g**? This will cost **5 Karma**. The runner does not ask where she came from.

**Jail**
> You wake in a stone cell with a splitting headache. The fine was **300g**. You served your time.
> **+3 Karma** (shared with the daily cap).

**Blackwake gate**
> "Welcome to the pirate port. Your name is worth something here — the worse it is, the better."

**Tier-up**
> **Karma: Respected (+25)** — Shopkeepers greet you warmly. Prices fall; the guild posts one more contract.

**Tier-down**
> **Karma: Wanted (−50)** — The gate captain spits. "You have nerve showing up here." The guards are already moving.

---

## Appendix B — Karma quick reference

```text
+80 … +100  Paragon   +20% discount   −30% bills   Saluted; Tax Day waived; free temple cure 1/day
+50 …  +79  Virtuous  +15% discount   −20% bills   Saluted; Tax Day waived; temple blessing 50% off
+25 …  +49  Respected +10% discount   −10% bills   Temple blessing 25% off; +1 bounty slot (optional)
+10 …  +24  Good       +5% discount    −5% bills   Flavor only
−9  …   +9  Neutral         0%            0%        Normal
−10 …  −24  Shady      −5% discount    +5% bills   Suspicious dialogue
−25 …  −49  Suspect   −10% discount   +10% bills   Gate fee
−50 …  −74  Wanted    −15% discount   +15% bills   Confrontation
−75 … −100  Outlaw    −20% discount   +20% bills   Elite confrontation

Blackwake: no gate/jail; low Karma respected (inn/Black Market inverse; positive Karma pays saint tax).
```

> **Remember:** Karma changes on **choices**, not on success, not on routine combat, and not on bounty turn-ins. The city remembers what you did — not how many rats you killed. In Blackwake, the city respects the outlaw and charges the saint extra.
