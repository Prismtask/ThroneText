# Combat Plan Phase — Design & Decisions

**Date:** 2026-10-04 · **Status:** decisions locked, **implementation NOT started** — the loop
change is gated on the superboss audit (§5). This document is the single source for the
plan-phase combat restructure; it supersedes the ad-hoc chat notes. The HUD work already
shipped (3-line feed, 📜 popup, acting/hit flashes) is the presentation kit this model
builds on — no new log surfaces are needed. **The pacer (§7) is ✅ implemented
2026-10-04** — separable from the gated loop change, and it doubles as the playback layer
the full model would need anyway.

The model itself is the classic JRPG batch-command flow (Dragon Quest / Persona family):
queue everyone's actions, then watch the round resolve.

---

## 0. The problem this solves

Today input and resolution are interleaved per actor. Because endgame allies out-speed
most enemies, every round resolves as *"your whole squad acts → the enemy squad acts"*:
enemy turns read as an epilogue, their actions constrain no decision, and the HUD
feedback has very little to dramatize.

Plan-first combat makes enemy actions the **consequences of a blind commitment** —
"will Red Hood survive to deliver the strike she queued?" — tension the current loop
cannot produce.

---

## 1. Decision log (locked)

| # | Decision | Notes |
|---|----------|-------|
| 1 | **Two-phase rounds.** *Planning:* queue the player + all allies — free input order, speed plays no part, snappy. *Resolution:* every queued action **and** every enemy action executes in **speed order**, no input. | Input freedom ≠ resolution freedom. |
| 2 | **Speed stays load-bearing.** Resolution order stays speed-based (d20 + DEX, as today). Strike-first / interrupt / push-initiative systems become *resolution-order modifiers*. | Kill-before-it-acts races must survive. |
| 3 | **ESC cancels one action at a time, in reverse.** Queuing runs 1→2→3→4; ESC steps back one actor and clears that actor's action (4→3→2→1). To change actor 2: step back to 2, re-choose, re-queue forward. The player (MC) is one of the actors. | "Resetting the whole action, but not entirely — one by one." |
| 4 | **Ally-targeted support is first-class.** Player and allies can target other allies with items/skills (heal, guard, buff, …) during planning. | Replaces reactive healing — support becomes prediction, not reaction. |
| 5 | **Enemy intent stays hidden.** No telegraphs, no announcements. | Deliberate tension source; ambush fairness is handled via aggro (§1.6), not via information. |
| 6 | **Aggro points.** Every combatant carries an aggro score; enemy targeting is driven by it (not unconditional weakest-unit ganking), and the player can influence aggro through their side's setup. | Sources & weights = open thread §4.1. |
| 7 | **Target-death redirect (silent).** If a queued action's target is dead at resolution, the action redirects to the **earliest-deployed living enemy** (for player-side actions). Applies to basic attacks **and** all skills. AoE unaffected; multi-hit re-picks naturally between hits. No announcer line. | "Fairest method" — deterministic and guessable. Enemy-side mirror = open thread §4.2. |
| 8 | **Actor death before resolve:** the queued action is lost. | Standard ruling; revisit if it feels bad in playtest. |
| 9 | **Capture unchanged.** Capture nets queue like any action and resolve at their speed slot; a duplicate-capture choice pauses playback until answered. | "Should be fine." |
| 10 | **Playback pacing (defaults, tunable).** ~0.6–0.8 s per actor beat, kicked off by the gold acting flash; ~0.1–0.2 s stagger for lines inside one action; ~0.8 s round-header beat. Speed setting: 0.5× / 1× / 2× / instant — **instant ≈ today's feel**. | Numbers are starting values; retune after the first full dungeon. Never hardcode. |
| 11 | **Presentation kit.** Playback narrates through the 3-line feed + HUD flashes/pulses; full history stays in the 📜 popup. | Already shipped. |

---

## 2. Rules detail

- **Planning order:** actors queue in deploy order (party order, front row first).
- **Targets are chosen at queue time.** All validation is deferred to resolution —
  dead actors lose their action (#8), dead targets redirect (#7).
- **Early round termination:** if the last enemy dies mid-playback, remaining queued
  actions are dropped. Flee/escape effects end combat the same way.
- **Reactions audit:** strike-first flags, counters, Furioso-style sequences, and boss
  phase transitions all need an explicit "when does this fire in the playback" answer
  before implementation (see §3).
- **Save/load:** combat is never saved mid-fight today; unchanged.

---

## 3. Integration landmines (work items, not decisions)

1. **Capture-choice prompt** must pause playback until answered (only mid-round dialog we know of).
2. **Reaction / choreography systems** — strike-first, interrupts, Black Silence's Furioso sequencing, boss phase-transition text — each needs a playback position.
3. **Superbosses (user-flagged ⚠):** gimmick-driven fights — Entangled Chrysalis, Black Silence phases, Wonderland floor bosses, Mary Sue — may depend on the interleaved input flow. **Audit required before any implementation** (see §5).
4. **Training dummy** is the first testbed; A/B one dungeon floor afterwards before committing.

---

## 4. Open threads (need decisions)

1. **Aggro sources & weights.** Candidates: class, row/position, equipment, guard/taunt
   actions, recent damage dealt/taken, skills. Also: is aggro visible anywhere (without
   an announcer), or fully opaque and learned by players?
2. **Enemy-side redirect.** Does an enemy whose target died mirror the rule
   (earliest-deployed living ally), or fall back to highest-aggro living ally?
3. **ESC nuance.** Stepping back clears each passed actor's action one-by-one (§1.3) —
   confirm that's the intent (vs. retaining later actions until overwritten).
4. **Mid-round conditions vs. queued actions.** If an actor is stunned/silenced *before*
   their queued action resolves — action lost (consistent with #8), or attempts-and-fails?
   (Losing it makes enemy CC genuinely heavy — likely desired, confirm.)
5. **Pacing final numbers** — after first playtest (current defaults in §1.10).

---

## 5. Superboss compatibility (implementation gate ⚠)

**No code may be written for the plan-phase loop until each special encounter is audited.**
Audit checklist per fight: mid-round input assumptions, choreographed sequences, add
spawns, timers keyed to actor turns, capture interactions, revival flows.

Known candidates: Entangled Chrysalis, Black Silence, Mary Sue, Wonderland floor bosses.

Handling options (not decided — pick after the audit):
- **(a) Adapt** the encounter scripts to the plan-phase loop.
- **(b) Per-encounter legacy flag** — special fights keep the classic interleaved flow.
- **(c) Hybrid** — plan-phase normal rounds, scripted interjections where needed.

---

## 6. Non-goals

- No changes to damage, skills, or status math.
- No enemy telegraph/intent system (decision #5).
- No new UI surfaces — the existing feed / popup / flashes carry the presentation.

---

## 7. Presentation pacing — "the pacer" (✅ implemented 2026-10-04)

Cheaper path, approved for specification: **keep the interleaved loop entirely** and give
every actor's action a readable beat. It solves *visibility/registration* (enemy turns
become watched beats instead of a scrolling burst) but **not** the commitment/stakes
problem (§0) — the full plan-phase model stays a separate, later decision. The pacer is
**not gated by the superboss audit** (§5): it changes presentation only. If the full model
is ever built, this pacer *is* its playback layer — not throwaway.

### 7.1 Architecture — pace the engine, not the GUI

- Pacing lives in **`GUICombatIO`** (`gui/screens/combat_screen.py`) — the bridge whose
  `print()` the combat thread already calls (`output_queue`). That thread simply sleeps
  between emissions.
- **Why**: engine state, text, HP bars, and flashes then stay in lockstep — the engine
  literally advances in paced real time. A GUI-side buffer was rejected because the HUD
  poller reads live engine state and would show bars moving *ahead* of the paced text.
- New module **`gui/combat_pacer.py`** — `CombatPacer` class, pure logic + injectable
  sleep function (headless-testable). `GUICombatIO.print()` calls `pacer.after_print(text)`;
  `GUICombatIO.input()` calls `pacer.before_input()` and clears skip state.
- GUI side: `CombatScreen._poll` interval 100 → **40 ms** while combat runs (keeps the
  ~130 ms staggers visible); skip signal wired from any click/key on the combat screen
  while the engine is **not** awaiting input.

### 7.2 Beat model

Each emitted chunk is classified by its highest-priority line; the wait happens **after**
the chunk is queued (header first → the gold flash shows during the hold):

| Class | Detection | Wait @ normal |
|---|---|---|
| Round header | `>> ROUND` | **0 ms** — redundant with the top bar; also no longer fed to the ticker (2026-10-04) |
| Turn header | `[n/m] Name's Turn:` | **400 ms enemy / 180 ms party** (name matched against party names, supplied by CombatScreen when the fight starts) |
| Combat event | `→ … dmg`, status/burn lines | 130 ms stagger after each event line |
| Menus, banners, descriptions | leading `>` (incl. `>>>` skill lines), prompts | **0 ms** — selection must stay snappy (2026-10-04) |
| Before `INPUT_NEEDED` | — | **0 ms** (settle removed — 2026-10-04) |
| First event after any input | RESOLVE_LEAD | **250 ms** — the confirm → delay → damage beat (2026-10-04) |

Reading: flash → hold → results stagger in → next actor's hold doubles as the settle.
Enemy beats get the full structure; party beats stay short (the player just acted).
The player's rhythm is: choose (instant) → confirm (instant) → beat → resolution lines.
The events feed **clears at each turn header** — every actor's beat owns the 3 lines —
and combat end wipes leftovers so the result line lands on a clean feed (2026-10-04).

### 7.3 Skip

- A `threading.Event`, set by the GUI when the player **clicks** during pacing
  (v1: clicks only via a recursive click bind; a key binding is a follow-up).
  Ignored while the engine awaits input (that click is a menu choice).
- The sleep helper waits in **25 ms slices**; a set event cuts the current beat's remaining
  waits and suppresses the rest of that beat.
- Suppression resets when the next turn/round header is paced, and unconditionally on
  `input()` and on `stop()`.
- **One input = one beat skipped.** Repeated clicks keep skipping; wholesale speed is the
  setting below, not spam.

### 7.4 Settings

- `gui/settings.py` `DEFAULT_SETTINGS` gains `"combat_pacing": "normal"`. Old settings
  files merge into the default automatically.
- Presets: **instant** (all waits 0 = today's feel) · **fast** (waits ×0.5) · **normal** (×1) ·
  **slow** (×2). Constants are named values in `gui/combat_pacer.py`.

### 7.5 Safety / edge cases

- Every sleep slice checks `io.is_active()` — a torn-down screen never leaves the engine
  thread sleeping (interacts with the `_CombatAborted` teardown path).
- Training dummy, superbosses, travel combat: all flow through the same IO — automatic,
  no per-encounter wiring.
- Long scripted sequences (Furioso chains, multi-hit/DoT cascades) pace line-by-line and
  remain skippable per beat.
- Combat end: no sleeps after `("RESULT", …)` is queued; Leave Battle flow unchanged.
- Don't set any wait below ~60 ms (below the drain granularity it renders as noise).

### 7.6 Test

- `tests/_diag_combat_pacer.py` (headless): classification table, party vs enemy hold
  selection, skip lifecycle (click → current beat suppressed; reset on next header; reset
  on input), instant = zero waits, multiplier mapping. Sleep function injected — tests
  assert computed durations without real sleeping.
- Playtest ladder: training dummy (fast cycle) → one full dungeon floor. Tune §7.7 from
  that, not from theory.

### 7.7 Open numbers (tune after playtest)

`HOLD_ENEMY 400` · `HOLD_PARTY 180` · `HOLD_ROUND 0` · `STAGGER 130` ·
`INPUT_SETTLE 0` · `RESOLVE_LEAD 250` ms at 1× — as revised after the first
playtest (2026-10-04); still tunable.
