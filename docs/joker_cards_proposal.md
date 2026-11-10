# The Joker — Pool Expansion Proposal (for review)

**Status:** ✅ IMPLEMENTED (2026-10-09) — core hand model + **all 22 Major Arcana live** (`ready=True`, fully dealable). Priestess / Justice / Judgement redesigned same day (Rev 8; Justice finalised in Rev 9). Playtest pending.
**Date:** 2026-10-08 · **Context:** `docs/event_horizon_design.md` §4.3 (the 3-card pool locked 2026-10-07); user: "i wanted more joker cards variation, but it needs to be designed first"
**Rev 2 (2026-10-08):** Tarot naming — **the Joker deals the Arcana**; burden vocabulary widened — drawbacks are no longer limited to +damage taken / −damage dealt (economic + battle-start gamble classes added per user feedback). Decision still unlocked.
**Rev 3 (2026-10-08):** drawbacks must be **bold/structural** — user benchmark: **The Tower** (flasks grant ×2, but every 5 flasks an actor has drunk cost 2% max HP per turn). The Tower added; full roster bold pass below. Decision still unlocked.
**Rev 4 (2026-10-08):** review round — Tower details confirmed; Hermit → option B; Magician → **+50% elemental** + **weakness gate** (25% rec); Moon **+Burn**; Devil **+20%** (not ×2); offering **persists** — 1 card per encounter, duplicates allowed, no exhaustion rule.
**Rev 5 (2026-10-08):** hand & deal model — the pool frame is the **22 Major Arcana** (this wave ships 11); a run holds a **capped hand (5 or 7)** that is **replaceable** — a thrown card **returns to the deck** and can be dealt again; the Joker **deals 2 faces per encounter**.
**Rev 6 (2026-10-08):** hand cap **7** · **keep one** of two dealt · **full spread — all 22 Major Arcana designed and shipping together** (maintenance call; wave-2 roster drafted below for review; hook-dependent faces get fallbacks, no deferrals).
**Rev 7 (2026-10-08):** **Justice** takes the kill-price drawback — *every kill an actor lands costs that actor 15% max HP* (stacks on multi-kills; never below 1 HP) — replacing "cannot crit"; **Judgement** keeps the renewal heal. **The World** redesigned: it strips the **drawbacks of every other owned arcana**, but the hand is frozen — *no more throws, no more offers for the run*.
**Rev 8 (2026-10-09):** three faces redesigned before playtest — **Priestess**: skill cooldowns **−2 turns** · basic attacks **×0.5**; **Justice**: attacks **ignore every enemy defense (×2.0 dealt, default)** · the party takes **×1.5 damage** (Justice and Judgement never shared effects — both hung off one on-kill hook, which is now retired); **Judgement**: at the **start of every round** all enemies lose **20% max HP (pure)** — **from round 3 the party suffers the same** (≥1 HP clamp; The World lifts it).
**Rev 9 (2026-10-09, FINAL — supersedes the Rev 8 Justice):** **Justice** is a **debuff mirror** — every debuff an enemy inflicts is inflicted back on that enemy; the party's own debuffs likewise bounce back onto whoever inflicted them (the drawback; The World lifts the party side). **Once per debuff type per action** — an ally's AoE burn mires the caster once, not once per victim or the whole team. Standard appliers are used, so immunities and status resistance still apply. The ×2.0-dealt / ×1.5-taken draft is retired.

---

## 1. Where the Joker stands today

- **3 faces:** Edge (+10% dealt / +5% taken) · Warden (−10% taken / −5% dealt) ·
  Gambler (+10% crit / +5% taken) — proposed Tarot renames in §3. Every face
  is a 2:1 bargain.
- Offered **every rn+25** (after milestone events), **skippable**, **off-deck**
  (no Entropy, no payout weight), **party-wide**, **run-long**.
- Stored in `state["joker_cards"]`; strip/restore with the run; boosts merge
  into the stacked HUD totals, drawbacks show as `DT+5%` (or negative DMG%).
- **Hand model (2026-10-08):** every rn+25 the Joker **deals 2 faces**
  (from the unowned pool); the player keeps at most one — or refuses both.
  A run holds a capped **hand of 5 or 7 arcana** (lock at review); at cap,
  keeping means *throwing* an owned arcana — and **a thrown card returns to
  the deck, dealable again**.

## 2. Design rules for new faces

1. **Every Joker is a bargain — and the burden must be bold.** A drawback
   should be something you *decide around*, not a tax you forget. Benchmark
   (user, 2026-10-08): **The Tower** — flasks grant ×2, but every 5 flasks
   an actor has drunk cost them 2% max HP per turn.
2. **Each face gets a distinct axis AND a distinct burden.** Axes: damage ·
   mitigation · crit · elemental · attributes · sustain · economy · tempo ·
   control · bond · risk. Two faces may not share the same burden language —
   after the bold pass the pool reads as different *kinds* of bargains.
   Plain numeric burdens (−15% dealt) may recur when the boost axis is
   unique; **bold/structural burdens stay one-of-a-kind**.
3. **Magnitude band:** boosts 10–30% — an outlier (The Magician's +50%) must
   be priced by a severe gate; plain numeric burdens 5–20%.
   Structural/ongoing burdens are exempt from the % band — bounded by
   legibility instead: (a) one line in the offer, (b) they bite the very
   strategy the boost rewards, (c) they cannot instantly void a run — the
   Tower's drain scales with the same flasks its boost doubles, so greed
   prices itself in blood rather than in a coin-flip.
4. **Burden vocabulary:** a drawback may come from any class:
   - **Combat:** +damage taken · −damage dealt.
   - **Economic (drawbacks only — they do not feed the Horizon):** EH shop
     prices up (The Devil: +20%) · mote gains cut. Economic *benefits* stay
     banned.
   - **Battle-start gamble:** gain N random buffs *and* suffer M random
     debuffs at each battle start.
   - **Ongoing cost (new, bold):** recurring drains/taxes scaled by a
     tracked count (The Tower).
   - **Option-closing (new, bold):** a system simply stops working for you
     (flasks, healing — Hermit/Death drafts).
   Still held: max-HP *edits* stay banned (drains based on max HP are fine);
   room-conditional effects need new tickers — they wait.
5. **Feasibility tags:** ✅ = works with the existing effect vocabulary via
   `_apply_joker_to_roster` as-is · 🔧 = needs a small hook (site named).

## 3. Proposed roster — the Joker deals the Arcana

Naming rule: the **faces are the 22 Major Arcana**; the **Joker stays the
dealer**. All **22 arcana are designed** and ship together (waves below) —
a complete spread keeps the system honest and maintainable. Renaming is
**save-safe**: already-played records re-apply from their stored
`effects`/`drawback`, so only the display name of cards played in an open
run changes.

### The hand & the deal (2026-10-08)

- **Pool:** the full **22 Major Arcana**; draws come from the *unowned*
  pool. The hand holds **distinct** arcana (no duplicates).
- **Cap: 7** — a run holds at most seven arcana (a classic spread).
- **The deal:** every rn+25 the Joker **deals 2 faces** — two distinct
  arcana not currently in the hand. Keep at most one — or refuse both.
- **Replace:** at cap, keeping a face means **throwing** an owned arcana.
  The thrown card **returns to the deck** and can be dealt again later.
- In a r275 run that's 11 deals — with 22 arcana, the hand is a living
  spread you curate, not a checklist you complete.

### The bold benchmark — The Tower (XVI)

**Boost:** every flask consumed *after* The Tower takes effect grants
**double its value** (not retroactive). **Drawback:** per actor, **every 5
flasks that actor has consumed — all-time, pre- and post-Tower — they lose
2% of max HP per turn** (each battle round).

**Confirmed 2026-10-08:** post-acquisition doubling; the drain counts the
consumed total (pre- + post-Tower); ticks every battle round.

This is the tone: the boost pays the greedy funnel, the burden prices it — in
the same currency (flasks), so the greedier you get, the harder it bites.

### Renames of the locked 3 — bold pass (adopted)

| id | Arcana | Boost | Bold drawback *(was)* |
|----|--------|-------|----------------------|
| `joker_strength` | **Strength** (XI) | +20% damage dealt | **always act last in battle** (permanent Slow) *(was +5% taken)* |
| `joker_temperance` | **Temperance** (XIV) | −20% damage taken | **−15% damage dealt · −25% Horizon Mote gain** *(was −5% dealt)* |
| `joker_wheel` | **Wheel of Fortune** (X) | +20% crit chance | **enemies' crit cap doubles (12% → 24%)** — luck cuts both ways *(was +5% taken)* |

The original gentle numbers (Edge +10/+5, Warden −10/−5, Gambler +10/+5) are
superseded by the bold versions above.

### New faces

| id | Arcana | Boost | Drawback | Burden class |
|----|--------|-------|----------|--------------|
| `joker_magician` | **The Magician** (I) | **+50% elemental damage** | **weakness gate:** hits that are not the enemy's weakness element deal only **25% of their damage** (immunity variant held — can void runs); enemies with **no** weakness element take normal damage (×1.0) | elemental oath |
| `joker_hermit` | **The Hermit** (IX) | +6 all attributes | **−50% gold & mote gains** *(option B — confirmed)* | economic |
| `joker_empress` | **The Empress** (III) | +2.5% max HP per round | −15% damage dealt | combat |
| `joker_chariot` | **The Chariot** (VII) | +30% damage dealt | +20% damage taken | combat (all-in) |
| `joker_devil` | **The Devil** (XV) | +25% damage dealt | **EH shop prices +20%** | economic (bold) |
| `joker_moon` | **The Moon** (XVIII) | battle start: 2 random buffs | battle start: **2 random debuffs** | battle-start gamble |
| `joker_tower` | **The Tower** (XVI) | flasks consumed after acquisition grant **×2** | **2% max HP lost per battle round per 5 flasks the actor has consumed** | ongoing cost |
| `joker_death` | **Death** (XIII) | attacks heal 10% of damage dealt | **all other healing received −50%** *(Wave B audit)* | option-closing |

The Moon pools: **Buffs** Haste (1t) · +10% damage dealt (3t) · −15% damage
taken (3t) · +2% max HP regen (3t). **Debuffs** Weaken · Slow · Blind ·
Poison (4×3t) · **Burn (3t, rising)** — buffs drawn without replacement so
the two differ. *(Burn added 2026-10-08.)*

Notes:
- Boosts merge into the stacked HUD types; burdens route through
  record-driven hooks (sites in §5) — none are plain actor buffs except
  where noted.

**Why these:** every burden is a different *kind* of decision — Strength
buys power with tempo, Temperance and the Hermit pay in coin and options,
the Moon pays in chaos, Death pays in sustain — and The Tower is the
anti-funnel face: it pays the flask greed double and then taxes the pile in
blood.

### Wave 2 — the remaining arcana (completes all 22)

| id | Arcana | Boost | Drawback | Burden class | Hook |
|----|--------|-------|----------|--------------|------|
| `joker_fool` | **The Fool** (0) | +2 initiative · +10% dodge | attacks have a **10% miss chance** | luck (both ways) | initiative/dodge exist; miss roll at attack sites — audit |
| `joker_priestess` | **The High Priestess** (II) | **+25% status effect chance** | −15% damage dealt | control | status-application audit (fallback: −25% cooldowns) |
| `joker_emperor` | **The Emperor** (IV) | **once per battle: survive a lethal hit at 1 HP** | the saved actor is **silenced 2 rounds** | endurance (attached cost) | ✅ live — `try_emperor_save` via `try_consume_death_ward` fallthrough (all death paths) |
| `joker_hierophant` | **The Hierophant** (V) | **+25% skill damage** | basic attacks deal **−25%** | skill-vs-strike split | damage-site split — audit |
| `joker_lovers` | **The Lovers** (VI) | **allies: +25% dealt · −15% taken** | the MC deals **−15%** | bond split | near-ready (role-split application) |
| `joker_justice` | **Justice** (VIII) | **reflect 20% of damage taken** | **every kill an actor lands costs that actor 15% max HP** — stacks per kill in one action (an AoE wipe bills the whole tally; never below 1 HP) | reciprocity (all force is repaid) | reflection status + on-kill detection — audit |
| `joker_hanged_man` | **The Hanged Man** (XII) | **+30% damage dealt** | **cannot act in round 1** of every battle | sacrifice (tempo) | turn-logic skip — audit |
| `joker_star` | **The Star** (XVII) | **debuffs on the party last 1 turn less** | −15% damage dealt | cleansing | duration tweak at application — audit |
| `joker_sun` | **The Sun** (XIX) | **crits deal +30% more** | non-crit hits deal **−15%** | crit-damage split | multiplier bonus at crit call sites — audit |
| `joker_judgement` | **Judgement** (XX) | **each kill heals the party 4% max HP** | −10% damage dealt | reckoning (sustain) | on-kill detection — audit |
| `joker_world` | **The World** (XXI) | **every other owned arcana loses its drawback** | the deal ends — **no further offers for the run, and cards can no longer be thrown** | completion (everything, once) | drawback suppression in apply/restore paths + retroactive sweep; offer gate |

Notes:
- **Justice or Judgement?** The kill-price lives on **Justice** — reciprocity
  is its whole idiom: what is taken is repaid, from any direction (reflect
  for incoming, the blood bill for outgoing). Judgement keeps the renewal
  side (kills heal the party). Holding both is legal and produces a natural
  tension: every kill pays blood *and* returns life.
- **The World** is the capstone: it turns the whole hand into pure blessing
  — every burden lifted — paid for by *closing the deal*: no further offers,
  no more throws; the hand is final. It self-balances by timing: taken early
  it freezes a small hand forever; taken late it crowns a curated one.
- **The Lovers** is the first role-split face (allies up, the MC pays) — it runs
  crosswise to the flask-funnel lesson: value spread beats value stacked.

## 4. Decisions — review record (2026-10-08)

Boxes ticked in review; chat answers folded in below.

- ✅ **Naming:** Tarot arcana + Joker-as-dealer (save-safe) — confirmed.
- ✅ **The Tower:** post-acquisition doubling; drain counts the consumed
  total (pre- + post-Tower); ticks each battle round.
- ✅ **The Hermit:** option B — −50% gold & mote gains.
- ✅ **The Magician:** +50% elemental adopted; weakness gate ships at
  **25% damage** — the pure-immunity variant is parked (full immunity can
  void runs: EH flee is disabled and a mixed-race pack can strand an
  unkillable enemy). Reopen if desired.
- ✅ **The Moon:** +2 buffs / +2 debuffs each battle; **Burn** joins the
  debuff pool.
- ✅ **The Devil:** shop prices **+20%** (not doubled).
- ✅ **The deal:** the Joker persists and **deals 2 faces per encounter**;
  refuse-both stays available (reject is always the player's control).
- ✅ **Hand:** cap **7**, distinct arcana, **replaceable**; the **thrown card
  returns to the deck** and can be dealt again.
- ✅ **Deal flow:** keep **one** of the two dealt faces (or refuse both).
- ✅ **Full spread:** all **22 Major Arcana** designed and shipping together
  (maintenance call) — wave 2 above completes the roster.
- ✅ **Coverage:** every face ships; hook-dependent faces land with their
  hooks — audit failures get fallbacks, not deferrals.
- ✅ **Justice / Judgement (Rev 7):** the kill-price (15% max HP per kill,
  stacking, clamped at 1 HP) sits on **Justice**; Judgement keeps the
  renewal side (kill heals the party).
- ✅ **The World (Rev 7):** strips **every other owned arcana's drawback**;
  the hand freezes — no more throws, no more offers for the run.
- ✅ **Bold pass:** adopt the bold drawbacks — new faces ship bold; the
  locked 3 bolden (Strength / Temperance / Wheel) per the table above.
- ✅ **Entropy exception:** hold (payout coupling) — nothing pays in Entropy.

## 5. Implementation checklist (once approved)

**Status 2026-10-09:** DONE — **all 22 Major Arcana live** (`ready=True`).
Shipped: hand/deal/throw core (`EH_JOKER_HAND_CAP=7`, `deal_joker_faces`,
keep-one flow in `offer_joker`, throw picker), `discard_joker`, World
suppression + deal gates, full 22-face data, and every hook — Tower flask ×2
+ drain, Magician gate, Wheel crit cap, Temperance/Hermit economy, Devil
shop ×1.2, Moon battle-start, Lovers role-split, Emperor cheat-death,
Weakness gate; batch 2: Death lifesteal (+healing-received ×0.5), Fool miss
10% + initiative +2, Priestess cooldowns −2 turns / basic ×0.5,
Hierophant skill ×1.25 / basic ×0.75, Justice debuff mirror (Rev 9),
Hanged Man round-1 skip, Star debuff −1/turn, Sun crit +30% /
non-crit −15%, Judgement round-start pulse (20% pure; round 3+ the party
too). The on-kill hook (kill-price / kill-heal / reflect) is retired (Rev 8).

**Priestess (Rev 8):** the original status-*application* chance had no
clean chokepoint; after the −25% cooldown fallback the face was redesigned
— flat **−2 turn** cooldowns (`set_skill_cooldown`) with **basic attacks
×0.5**.

Tests: EH file **94** (+29 subtests), map diag 79/79, run diag ✅, phase1 ✅,
phase4 19/19, suite **215 passed / 89 subtests**.

- `event_horizon.py`: extend `JOKER_CARDS` to the full **22 Major Arcana**
  (multi-effect lists already supported; a face may carry several `effects`
  entries).
- **Hand & deal mechanics (new, Rev 5):**
  - `offer_joker`: deal **2 faces** from the unowned pool; keep-one (or
    refuse both); if at the hand cap, the keep opens a "throw which
    arcana?" picker. Cap constant `EH_JOKER_HAND_CAP` = **7**.
  - **Throw:** remove the record from `state["joker_cards"]` + selectively
    strip its labeled EH entries from every actor (new `discard_joker`
    helper — existing strip functions remove ALL EH effects, so it must
    match by record label). The thrown id simply re-enters the unowned
    pool — no extra state.
  - Tests: cap enforcement, throw → re-deal round-trip, distinct-hand rule,
    keep-one deal, strip/restore with a thrown card.
- **Bold-burden hooks (all EH-local unless noted):**
  - **The Tower** — `apply_flask` ×2 multiplier for post-acquisition drinks
    (record keeps the effective value; label gains a "×2" suffix); per battle
    round drain: `2% max HP × floor(total flasks that actor has consumed / 5)`
    (counts pre- + post-Tower).
  - **The Magician** — weakness gate inside `calculate_elemental_damage`
    (player: `combat/elemental.py`; ally: `combat/ally.py` ~L1474): if the
    target has any weakness element (`elemental_res[el] < 1.0`) and the
    attack's element is not one of them → damage ×0.25. Neutral (no-element)
    hits fail the gate when the target has weaknesses; targets with no
    weakness take normal damage (×1.0).
  - **The Devil** — `_shop_flask_price` ×1.2.
  - **Wheel of Fortune** — `apply_enemy_scaling` stamps
    `enemy["_eh_crit_cap"]`; `resolve_critical_chance` reads the override
    (one engine line).
  - **Strength** — permanent `slow` entry (audit that battle-state scrubs
    keep permanent entries).
  - **Temperance** — mote award sites ×0.75.
  - **The Hermit** (B) — gold & mote award sites ×0.5 (audit sites; includes
    the run payout).
  - **The Moon** — new `apply_joker_battle_start` + pools (Burn included).
  - **Death** — generic lifesteal read + healing-received hook (audit).
- **Wave-2 hooks (all landed 2026-10-09):**
  - **The Fool** — initiative/dodge buffs + a miss roll at attack sites.
  - **The High Priestess** — **−2-turn cooldowns** at `set_skill_cooldown`
    (`_eh_joker_priestess` flag); basic attacks ×0.5 (Rev 8).
  - **The Emperor** — cheat-death once per battle (barracks T6 pattern) +
    silence-on-save.
  - **The Hierophant** — skill-vs-basic damage split at the damage sites.
  - **The Lovers** — near-ready: role-split application (allies vs MC).
  - **Justice** — **debuff mirror** (Rev 9): `debuff_signature` diff per
    action in the engine's player/ally/enemy turn blocks →
    `joker_mirror_debuffs` re-inflicts each newly-applied debuff type on
    the inflictor (once per type per action; verified against
    refreshes — count or duration must grow). Standard appliers, so
    immunities and status resistance still apply. The party's own
    infliction is the drawback (World lifts it).
  - **The Hanged Man** — skip-round-1 in the party turn logic.
  - **The Star** — debuff duration −1 at application.
  - **The Sun** — crit-multiplier bonus at the crit call sites.
  - **Judgement** — round-start **pure pulse** (`joker_judgement_pulse`,
    engine round loop): 20% max HP to all enemies; from round 3 the party
    takes the same (Rev 8).
  - **The World** — **drawback suppression**: when World is owned, every
    *other* joker's drawback is skipped in `_apply_joker_to_roster` and on
    the restore path; taking World runs a retroactive sweep that strips the
    other jokers' labeled drawback entries from every actor. The deal/throw
    locks are behavioral (offer gate + no throws possible, since throws only
    occur while keeping a card — and no cards are ever dealt again).
    World itself carries no actor-entry drawback.
- Tests: TestJoker iterates **all 22** (apply + strip/restore for every
  variant); `_diag_eh_run` joker scenario **updated for the 2-face deal +
  keep/throw flow** (menu script indices shift); `_diag_eh_map` pool check
  updated to the new roster.
- Changelog bullet + `docs/event_horizon_design.md` §4.3 rewrite **when
  locked** (this proposal supersedes nothing until then).

## 6. Held / rejected ideas (for the record)

- Numeric-only burdens are no longer the default voice of the pool (rev 3
  bold pass); a face must be a different *kind* of bargain.
- Economic **benefit** Jokers (motes/gold/payout +) — violates "off-deck,
  no payout". Economic **drawbacks** are allowed and can be bold.
- Max-HP **edits** — messy to detach/restore (drains computed from max HP
  are fine; The Tower uses one).
- Room-conditional Jokers ("stronger past r100") — needs tickers per room;
  against the instant/permanent profile.
- One-shot Jokers (heal/cleanse on pick) — not a run-long identity.
- Healing-received and physical/elemental split modifiers need their audits
  before Death / Magician ship.
- The Magician **immunity** variant — held: full immunity can void runs
  (EH flee is disabled; mixed-race packs can strand an unkillable enemy);
  ship the 25% gate instead.
- The Hermit option A (flasks no longer affect you) — held; user chose B.
- No-repeat / exhaustion offering rule — superseded by the hand model
  (2-face deals, capped hand, replaceable; thrown cards re-dealable).
- Duplicate arcana in a hand — held: the hand holds distinct faces.
- Rev-1 faces parked: Unfound (anti-Entropy boost), Harbinger (haste),
  Viper (status), Aegis/Sleight/Zealot (magnitude twins).
