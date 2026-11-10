# Family System — Bed Events, Pregnancy & True-Born Children

**Status:** ✅ **Phases 1–4 implemented 2026-10-30 (v0.1.9.1)** (Attunement mini-game, pregnancy/birth, 15/40/60 growth, full per-girl night lines, daughter bond UI, no-romance guards, dispatch/ascension/awakening gates, Father's Legacy combat wiring, Voss & Lumen epilogue, written-mode prose layer, README/wiki/changelog; automated diagnostics pass). Manual playtest pending.
**Scope:** A toggleable mature-content system: nightly bed-event mini-game → possible pregnancy → birth → a true-born child who grows up and can join the party, inheriting her mother's skills. Children have **no romance** — bond and gifting only.
**Related docs:** `unrelated_for_coding/WORLDBUILDING_CODEX.md` §4.1 / §4.2 / §4.7 · [`quest_system_design.md`](./quest_system_design.md) (Voss & Lumen) · [`awakening_design.md`](./awakening_design.md) · [`house_stories_design.md`](./house_stories_design.md) · [`time_system_design.md`](./time_system_design.md) · [`dream_events_design.md`](./dream_events_design.md) · [`karma_system_design.md`](./karma_system_design.md) §17 (shared Game Rules step)
**Process:** follows [`improvement_planning_guide.md`](./improvement_planning_guide.md) — verify → classify → design doc → pre-flight → implement.

> **Personal-project context:** no storefront/rating constraints apply (see `/memories/repo/content-direction.md`). The toggle exists for **experimentation, comfort, and save safety** — not compliance.

---

## 0. Summary

- **Bed events** are a repeatable **Attunement mini-game** (§4), not a fixed cutscene — because pregnancy is a chance roll, the same event repeating unchanged would become redundant. The event runs inside the existing **story/facility UI**, and a separate **dream system** lives in [`dream_events_design.md`](./dream_events_design.md).
- **Pregnancy** runs **30 days in three 10-day periods**; she can fight in periods 1–2 but is returned to the house lounge for the **third period**, then recovers 7 days after birth.
- **True-born children** grow through **15 / 40 / 60-day milestones** (infant → child at 15, adult at 40, prime at 60), inherit their mother's race + innate skills + **Father's Legacy**, and can join the party as normal allies at adulthood. Bond/gifting only — no romance, no marriage, no bed events.
- **Season & moon** feed the **ally-initiated** night chance (§4.9) — the first gameplay use of the new calendar.
- **Two independent switches** — `family_enabled` (per-save Game Rules: pregnancy + children) and `content_level` (global: `off` / `fade-to-black` / `written`). Sleep sharing belongs to the intimacy layer: it fires whenever `content_level` is not `off`, **even when the family system is off** — it then uses fade-to-black/scene text and simply never rolls conception (§3.1).
- **Lore** is amended in the codex (§4.1/§4.2, new §4.7) and dramatized by a new **Voss & Lumen ending**.

---

## 1. Locked decisions (user, 2026-10-27)

| # | Decision |
|---|---|
| L1 | The family system is **in scope** for the game. |
| L2 | Implementation is **toggle-based**, not forced/permanent. |
| L3 | Monster girls get a codex-level **complete biological system** capable of reproduction. |
| L4 | Bed events are a **mini-game** (repeatable, varied), since pregnancy is probabilistic. |
| L5 | Children are **bond + gifting only** — no romance path. |
| L6 | Grown children can **join the party** and use the **same skills as their mother**. |
| L7 | The Voss story gets an **ending with Lumen** supporting the lore change. |
| L8 | **Documentation first** — no implementation until this doc's open decisions are locked. |

---

## 2. Lore amendment

### 2.1 Codex changes (applied 2026-10-27)

`unrelated_for_coding/WORLDBUILDING_CODEX.md` was amended (provisional, marked as amendment):

- **§4.1 "Biologically real" bullet** — now states that the Accord-fragment sustains a *complete living biology*, including a functional reproductive system.
- **§4.2 Reproduction row** — changed from "Cannot reproduce" to: complete biological system sustained by the Accord-fragment; can conceive with a bonded mortal; true-born children are exceedingly rare (see §4.7).
- **New §4.7 "True-Born Children"** — defines them: inherit mother's race + innate gifts; do not carry the mother's Accord-clause; the mother remains the unique manifestation.

**Unchanged:** monster girls themselves still **do not age**; each remains the unique, irreplaceable manifestation of her clause. **Resolved (O1, 2026-10-30):** true-born children age to adulthood, then stop at prime — recorded in codex §4.7.

### 2.2 Voss & Lumen ending (implemented Phase 4)

**Placement:** a post-MQ6 epilogue — after **"Grand Resonance"** (`mq_archivist_06`) and the Fireside Tales arc **"A Moth at the Window"** is complete. This respects the locked pacing decision in `quest_system_design.md` §5 ("don't rush their story").

**Format:** a `StoryScreen` beat triggered by star-moth on city entry (reuse `facilities/story_beats.py` + `claim_city_trigger`), ending at the Star Tower. New flag `voss_epilogue_seen` (one-time, save-locked). **Implemented in Phase 4** as `facilities/star_tower.py::voss_epilogue`, registered in `STORY_BEATS`, and queued by `ensure_city_story_triggers()` on entering Skylume after MQ6 + the Moth arc.

**Outline (prose to be written in Phase 4; no explicit content):**

1. A last star-moth letter: the Archive has a **final entry** to read, in person.
2. At the tower, Voss and Lumen's shared history is finally told — the name **Lumen Quillan** (why she took it, how she came to the tower, why she "always seems grateful").
3. The reveal: the Archive's first **true-born** entry — **Lumen is expecting** (locked O2).
4. Voss closes the ledger: the Archive has recorded a century of bonds; this is the first entry about *what a bond can grow into*. The player's own household can now walk the same road.
5. Rewards: Journal entry + a small memento (optional unique keepsake), no combat power.

**Design intent:** the epilogue is the **in-fiction proof** of the amended lore — the player learns the phenomenon exists before/while using it, without gating their own family system on NPC story progress.

**Alternative (lighter):** add a 4th part to the *"A Moth at the Window"* house story instead. The Star Tower epilogue is recommended because it's the **Voss story's** ending, not the house arc's.

### 2.3 Resolved lore decisions (2026-10-29)

- **O1 ✅** True-born children **age to adulthood, then stop at prime**.
- **O3 ✅** Reproduction is **world-wide but rare**; Voss & Lumen are the first recorded case.
- **O4 ✅** The child is still the player's child: she takes the **mother's race/type** and also receives a **Father's Legacy** from the player (weakened player-race passive + family name) — see §6.3b. **O4a ✅:** the per-race values in §6.3b are locked.

---

## 3. Toggle model — where the switches live

### 3.1 Two switches, three content states

| Switch | Scope | Storage | Controls |
|---|---|---|---|
| `family_enabled` | **Per save** | Game Rules (character creation; final) | **Pregnancy + children only** |
| `content_level` | **Global** | `gui_settings.json` (`gui/settings.py`) | `off` / `fade-to-black` (default) / `written` — whether sleep sharing exists and how it renders |

**Interaction matrix (O10 clarification):**

| `content_level` | `family_enabled` | Sleep sharing | Explicit text | Pregnancy / children |
|---|---|---|---|---|
| `off` | any | ❌ | — | ❌ |
| `fade-to-black` (default) | off | ✅ | ❌ (fade to black) | ❌ |
| `fade-to-black` | on | ✅ | ❌ (fade to black) | ✅ |
| `written` | off | ✅ | ✅ | ❌ |
| `written` | on | ✅ | ✅ | ✅ |

- **Sleep sharing is independent of the family system.** With `family_enabled` off, the event still fires (when `content_level != off`) and still grants affection/stress/buffs — it simply skips the conception roll and never creates children.
- **`content_level: off` disables sleep sharing entirely**, which also means the family system cannot produce children even if `family_enabled` is on. The display preference is the stronger gate.

Why split them: explicitness is a **display preference** (read at render time only); the family system creates **persistent state** (pregnancies, children) and therefore must be a per-save decision.

### 3.2 New-game choice vs settings — recommendation

**New-game choice for the family system; settings for display only:**

- **New Game:** add the **Family system** yes/no to the shared **Game Rules** step at character creation (see [`karma_system_design.md`](./karma_system_design.md) §17), alongside Karma and future difficulty/drastic-system rules. The step also records *content level* if that setting is exposed there. This is the cleanest consent point and avoids surprise content in a new save.
- **Settings:** `content_level` is freely changeable at any time (render-only). `family_enabled` is final at character creation and is not exposed as a settings toggle.

**Why not settings-only?** The user's crash concern is about **mid-state toggling**, not the setting itself. A render-only switch cannot crash; the stateful switch can only be unsafe if it deletes or abandons pregnancies/children. Removing the mid-game state toggle entirely is the simplest safe policy and matches the shared Game Rules step.

### 3.3 Crash-safety rules (locked design constraints for implementation)

1. `content_level` is read at **trigger and render time**; it never mutates game state. Toggling it mid-game is always safe.
2. `family_enabled` is final per save (Game Rules). It gates **conception, birth, and child growth** — never sleep sharing.
3. Sleep sharing fires whenever `content_level != "off"`, regardless of `family_enabled`.
4. No conception roll, birth, or growth tick runs while `family_enabled` is False.
5. The switches are never read mid-scene — only at trigger time and reward resolution.

### 3.4 Old saves

- On migration (`ensure_player_fields`): `family_enabled` is **absent** → defaults to `False`; there is no mid-game opt-in, so old saves stay OFF.
- `content_level` is a new global setting; it defaults to **`fade-to-black`**, so old saves get sleep sharing (when the affection gate is met) but never family content.
- Affection caps migrate with the new ladder (§4.8): base **100 → 200**, engaged/married **200 → 300**. Existing affection values are preserved; married girls keep their already-granted wedding accessories.
- No modal on load; no surprise.

---

## 4. Sleep-sharing mini-game — "Shared Night" (Attunement)

### 4.1 Design principles (revised from the dual-meter draft)

The first draft copied Elona's **dual composure meters** (0–100 each). Playtest feedback (2026-10-30) was that the MC's meter was opaque and reaching 100 felt arbitrary. The mechanic was rebuilt as **Attunement**: the player reads the companion's visible mood and answers with a matching tone. There is no second meter — the only number is the couple's Attunement, so the goal is always legible.

**Rules:**
- Three rounds, one mood shown per round.
- Four tone actions: **tender** / **playful** / **bold** / **shy**. Each mood and action belongs to a two-tone "energy family" (`soft`: tender/shy; `energetic`: playful/bold).
- Exact mood match **+2** Attunement; same energy family **+1**; opposite family **+0**.
- Maximum 6. The night resolves at `together` (5–6), `warm` (3–4), or `quiet` (0–2). **End the night** early gives `rest`.
- Her mood is drawn 75% from her preferred tones, so each girl plays differently without hidden math.
- Pregnancy is rolled **after** an intimate ending, with the ending tier as a modifier (not tied to an item drop).
- Tone stays warm and **fade-to-black**; `content_level: written` can add explicit variants later.

### 4.2 UI wrapper — reuse existing screens

| Option | Fit | Recommendation |
|---|---|---|
| **Story/facility UI** (`StoryScreen` / `FacilityScreen`; `term.print` + `term.menu` + `term.pause`) | Same wrapper as Fireside Tales, house menus, and story beats; runs naturally inside the house facility thread | ✅ **Primary** — no new UI system; the Attunement bar renders as text, actions as buttons |
| **Combat UI** (`gui/screens/combat_screen.py`) | The loop is combat-shaped (action menu + log + meters), but the screen expects HP/enemies/targeting | ❌ Not for v1 — would require fake combat actors; keep the logic pure so a combat-style renderer can be added later without rewriting the event |

**Architecture rule:** the mini-game logic is **pure** (`facilities/sleep_sharing.py` — no I/O, RNG injected). The UI layer (`facilities/house.py` or a thin `sleep_sharing_ui.py`) drives it with `term`. This is what makes "wrap it in existing UI" cheap and testable.

**Trigger point:** `_house_sleep()` in `facilities/house.py` already runs in the house `FacilityScreen` thread and calls `end_day(slept=True)`. The event runs inline *before* the day rolls, so the morning message and buffs apply correctly.

### 4.3 Triggers & eligibility

**Eligible girl (locked O5/O8):**
- Owned (active party **or** house lounge), and `not is_child` / `not is_trueborn`.
- **All capturable girls and all heroines are eligible** (O5). Unique story NPCs are not allies and never enter this system.
- **Player-initiated:** `affection >= 140`.
- **Girl-initiated:** `affection >= 160`.
- Not pregnant, not away on dispatch, not injured.
- `content_level != "off"` (global display setting). `family_enabled` is **not** required for sleep sharing — only for conception.

**Two entry paths:**
1. **Player-initiated** — house lounge submenu action **"Share the night"** (per-girl, 140+), once per night (global daily limit, mirroring `girl_talk_today` / `girl_gift_today`).
2. **Girl-initiated** — on **Sleep at home** (Night phase), each eligible girl (160+) rolls `INITIATE_CHANCE` (6% base; engaged +4%, married +8%), **modified by season and moon (§4.9)**. At most **one** shared night per night; the highest roll wins.

**Cost:** none beyond the sleep itself (the night is already ending). Home only — inns and camps do not trigger sleep sharing (dreams may still occur; see the dreams doc).

### 4.4 Loop — read her mood, answer in kind

Each round shows the companion's mood and a short line. The player picks one of four tones (or ends the night). The UI displays Attunement as `◆◆◇◇◇◇`:

| Action | Tone family | Exact mood | Same family | Opposite family |
|---|---|---|---|---|
| **Tender** | soft | +2 | +1 | +0 |
| **Playful** | energetic | +2 | +1 | +0 |
| **Bold** | energetic | +2 | +1 | +0 |
| **Shy** | soft | +2 | +1 | +0 |
| **End the night** | — | — | — | exits with `rest` |

- **Three rounds.** After round 3 the night resolves automatically: Attunement **5–6 → Together**, **3–4 → Warm**, **0–2 → Quiet**.
- **Mood generation:** each round she is in one of the four tone-moods (`tender` / `playful` / `bold` / `shy`). 75% of the time it is drawn from her two preferred tones; otherwise from the full set.
- **Random beat (20%/round):** flavor only — a small gesture, a sound, a shift in the dark. No stat changes, so the puzzle stays readable.
- **Personal voice:** every capturable monster girl and the three Wonderland heroines has a signature line for each tone, merged over the generic pool; every girl also gets a personal closing line from her own `house_night_ending` (or `house_bond_kiss`) dialogue key.
- **Readable choices:** the UI shows only her mood line and natural-language action prompts ("Hold her close — slow and warm", "Play along — tease her, make her laugh"). It does not print tone names or "(Tender · soft)" labels, so the player reads the scene rather than matching labels.
- **Content source:** all pools live in `resources/family_scenes.yaml`; `resources/family_scenes.py` is a thin loader, so dialogue can be tuned without editing Python.
- `End the night` is always available (consent + quick exit) and never punishes the player.

### 4.5 Endings

| Ending | Condition | Affection | Stress | Buff | Conception roll? |
|---|---|---|---|---|---|
| **Together** | Attunement 5–6 after 3 rounds | +4 | −20 | `shared_night` + `beloved` | ✅ +8% |
| **Warm** | Attunement 3–4 | +3 | −15 | `shared_night` + `beloved` | ✅ +4% |
| **Quiet** | Attunement 0–2 | +1 | −10 | `shared_night` | ✅ +0% (still rolled, O12) |
| **Rest** | player ends early | +1 | −5 | — | ❌ |

- Affection respects `affection_cap`.
- Ending line comes from the scene pool. `content_level: written` adds a more intimate, non-graphic prose layer to actions and endings; it still closes before explicit detail.

**Buff model (O13):**
- House sleep grants the existing **house buff** (`well_rested`) to the player and active party, as today. If the house tier's bed buff is 0 (small houses), `shared_night` still applies from the shared night itself.
- A shared night additionally grants:
  - **MC — `shared_night`:** +1 to all attributes for 2 dungeon rooms.
  - **The girl — `beloved`:** +2 to her primary attribute for 2 rooms, and +10% affection gain until the next sleep.
  - Other party members: `well_rested` only.
- **Merge rule:** `shared_night` and `well_rested` do **not** stack — keep the stronger value/duration. The girl's `beloved` is a separate effect and may coexist with `well_rested`.
- **Duration:** `shared_night` and `beloved` are skipped by combat-round buff ticking and decremented by the three dungeon room loops, so “2 rooms” means two dungeon rooms, not two combat rounds. `well_rested` keeps its existing behavior.
- **HUD labels:** merged Shared Night shows **SHR**, beloved shows **BLV**, and ordinary bed rest keeps **RST**. The merged buff carries a `shared_night` marker so a stronger `well_rested` value does not hide the Shared Night origin.

### 4.6 Pregnancy roll

Rolled **after** an intimate ending, only if eligible (not already pregnant, `family_enabled`):

```
chance = BASE (12%)
       + ending bonus (Together +8%, Warm +4%, Quiet +0% — still rolled)
       + engaged +5% | married +10%
       + fertility item/blessing (future hook, 0 by default)
cap = 35%
```

- **Family gate:** the roll runs only when `family_enabled` is True. Sleep sharing with the family system off never conceives.

- **Pity system:** after `PITY_START` (5) consecutive shared nights without conception (per girl), each further night adds `+10%`; guaranteed at `GUARANTEE` (8). Counters reset on conception. All constants in one block for tuning.
- No raw odds are shown to the player; flavor feedback only ("Tonight felt… hopeful."). Odds are exposed in the diag script.

### 4.7 Anti-redundancy checklist

- [x] Visible mood each round (no hidden composure meter)
- [x] Three-round score with a legible 0–6 Attunement bar
- [x] Preferred tones per girl (75% mood bias; optimal play differs by personality)
- [x] Per-girl action-line overrides + a personal closing line
- [x] Random beats (20%/round), flavor only
- [x] Four endings with distinct rewards
- [x] Player-initiated vs girl-initiated framing differs
- [x] `End the night` early exit for quick repeats

### 4.8 Affection ladder v2 (required by the 140/160 gates)

Widening the max and raising the sleep-sharing gates requires rescaling the existing affection features (locked intent: "widen affection max and change existing feature gates to accommodate"). Proposed ladder:

| Milestone / gate | Old | New |
|---|---:|---:|
| Base cap (pre-engagement) | 100 | **200** |
| Kiss | 80 | **80 (unchanged)** |
| Player-initiated sleep sharing | — | **140** |
| Proposal | 100 | **100 (unchanged)** |
| Engaged cap | 200 | **300** |
| Ally-initiated sleep sharing | — | **160** |
| Marriage gift (unique wedding accessory) | 200 | **300** |
| Awakening affection gate | 150 | **200** |
| Talk-tier thresholds (low / mid / high / max) | ≤30 / ≤60 / ≤80 / >80 | **≤60 / ≤120 / ≤200 / >200** |
| Status icons (❤️ / 💖) | 50 / 80 | **80 / 140** |
| Dispatch "Spirited" / affection_mod tiers | 60 / 30·60·80 | **120 / 60·120·160** |
| Piece of Relationship / "bonded" threshold | 200 | **200 (kept — no retroactive nerf)** |

Load-bearing rules:
- Raising the **base cap** to 200 lets a girl reach the 140/160 sleep-sharing gates without being engaged; proposal at 100 and marriage at 300 bracket the intimacy ladder.
- **Migration:** existing saves get caps raised in `ensure_player_fields` (base 100→200, engaged/married 200→300). No affection is lost; married girls keep accessories already granted.
- **Existing feature gates to update:** kiss/propose checks, stale-cap heal (200→300), engage cap grant (200→300), marriage gift check (200→300), awakening gate (150→200), talk-tier selection, status icons, dispatch mood/mod tiers, tutorial/gift-shop/README/wiki text.
- **Not rescaled:** Fireside Tales early-story gates (40/45/50/100) stay as early-relationship beats; `RECRUIT_AFFECTION_THRESHOLD` stays 50.

### 4.9 Season & moon modulation (girl-initiated chance)

The new season system (`events.py`: four **30-day** seasons cycling with the months) and the fixed moon days give the initiation roll a calendar identity. The same pure helper handles it:

```
initiate = BASE 6%
         + engaged +4% | married +8%
         + season: Spring +3% · Summer +1% · Autumn +0% · Winter +2%
         + moon: Full Moon (day 15) +5% · New Moon (day 1) +2%
         + daily events: Monster Girl Season +3% · Wary Prey −3% · Blessed Wind +2%
clamp = 2% … 25%
```

- **Sources:** `events.get_season(player)` for the season; `events.get_month_day(player["day"])` for the moon days; `player["daily_effects"]` for `full_moon` (day 15), `capture_bonus` (Monster Girl Season / Wary Prey), and `all_stats` (Blessed Wind).
- **Flavor:** when a modifier applies, the initiation line mentions it ("The spring air makes her linger at the door"; "The full moon is doing most of the talking").
- **Scope:** this would be the **first gameplay effect of seasons** — `events.py::get_season` currently documents seasons as flavor/weather-only. Update that docstring when implementing; no combat/gold/XP multipliers are added.
- **Optional future hook (not v1):** the same coefficients can feed the conception roll; conception stays independent for now.

---

## 5. Pregnancy lifecycle

**Timings (O15 revision, 2026-10-30):** pregnancy is **30 in-game days**, split into **3 periods of 10 days** — longer than the original 14-day proposal and aligned with the 30-day month/season calendar.

1. **Conception** → `pregnant = True`, `conceived_day = day`, `due_day = day + 30`, Journal event, immediate status change. The active **period** is derived: `(day - conceived_day) // 10 + 1`.
2. **Periods:**
   - **First period (days 1–10):** remains in the active party; normal combat allowed. Status: *"Expecting — first period (Day N/30)."*
   - **Second period (days 11–20):** remains in the active party; normal combat allowed. Status: *"Expecting — second period."*
   - **Third period (days 21–30):** **no combat.** At the start of the period she is returned to the house lounge via `_return_ally_to_house()` and cannot be recruited until birth + recovery. Status: *"Expecting — third period — resting at home."*
3. **Available during pregnancy:** talk, gifts, bath (existing stress action), Fireside Tales effects. **Blocked:** dispatch, ascension, awakening, sleep sharing, and (third period only) combat/recruitment.
4. **Nesting:** house stress recovery bonus while any girl is expecting (propose +2/day, tunable; optionally +1/+2/+3 by period).
5. **Birth** triggers on `_apply_day_rollover()` when `day >= due_day`:
   - Scene via `term`/`StoryScreen`; child record created; player names the child (reuse rename flow).
   - Mother: `pregnant = False`, `recovery_until = day + 7`, then recruitable again.
6. **Conception cooldown (O15):** `next_conception_day = day + 30`; sleep sharing can resume after recovery, but conception is not rolled until the cooldown ends.
7. **No complications** — no miscarriage/risk events. Keep the system warm; revisit only if requested later.

**Time pockets:** pregnancy and growth **do not tick** in Wonderland / Event Horizon (frozen-time rule in `time_blocks.py`). Confirm exact guards during implementation.

---

## 6. True-born children

### 6.1 Record model

Pre-adult children live in a new `player["children"]` list (not mixed into house `monster_girls`):

```python
{
  "key": "trueborn_<mother_key>_<n>",   # unique, stable
  "mother_key": ..., "mother_name": ...,
  "name": "<player-chosen>",
  "race": "<mother's race>",
  "father_race": "<player's race>",
  "legacy": {...},                       # Father's Legacy (§6.3b)
  "born_day": N, "stage": "infant" | "child" | "adult",
  "affection": 30, "affection_cap": 100,   # bond meter (reused feel)
  "innate_skills": [...], "passive_skill": ...,
  "preferred_tones": [...],
  "no_romance": True, "is_trueborn": True,
  "home_city": ..., "home_house": ...
}
```

At adulthood she is converted into a **normal house girl record** with `is_trueborn: True` / `no_romance: True` and can use the standard `recruit_ally_from_house()` flow. This keeps party/equipment/leveling code untouched.

- **House cap (O6):** children count toward the house's monster-girl capacity; there is **no separate cap on children**. **O15 ✅:** a mother may have multiple children, with a **30-day conception cooldown** after each birth (see §5).

### 6.2 Growth stages

| Stage | Age (days since birth) | Interactions | Combat |
|---|---|---|---|
| Infant | 0–14 (15 days) | Flavor line in house; no talk/gift | No |
| Child | 15–39 (25 days) | Talk + gift (bond), small house flavor | No |
| Adult | 40+ | Full talk/gift; recruitable | Yes |
| Prime | 60+ | Cosmetic milestone; aging stops | Yes |

The three user-facing milestones are **15 / 40 / 60 days** — total age from birth, not additive durations: infant → child at 15, child → adult at 40, prime at 60. The days between milestones fall out of those numbers (child stage is 25 days). All four values live in one constants block (`GROWTH_INFANT_DAYS`, `GROWTH_ADULT_DAYS`, `GROWTH_PRIME_DAYS`, derived `GROWTH_CHILD_DAYS`) for tuning. Growth ticks on `_apply_day_rollover()` only (same frozen-time rule); the Family menu shows the countdown to the next stage and to prime.

### 6.3 Skills & stats inheritance

- **Innate skills:** copy the mother's **base** `innate_skills` (both). This is the "same skills as their mother" requirement.
- **Passive:** from the inherited race (Part B race passives), not copied from the mother's record.
- **Learned/upgrade/awakened skills:** **not** inherited. Children learn normally as allies (`learning` field) after adulthood.
- **Stats:** base = mother template attributes × 0.9, level 1, `level_cap` 10, growth band from the existing late-bloomer formula (`awakening_design.md` Part A), plus Father's Legacy (§6.3b).
- **HP:** standard `ally_max_hp()`.

### 6.3b Father's Legacy (O4 ✅)

The child is the player's child too. She inherits the mother's race and gifts, and from the **father** she receives:

1. **A weakened version of the player's race passive** (roughly half strength) — a permanent, build-aware benefit.
2. **The player's family name** (cosmetic; the player names the child at birth).

| Player race | Player passive | Child's Father's Legacy (weakened) |
|---|---|---|
| Human | +1 to all attributes | +1 to two attributes chosen at birth |
| Elf | +10% dodge | +5% dodge |
| Dwarf | +15% max HP | +7.5% max HP |
| Halfling | +10% crit | +5% crit |
| Orc | +15% damage below 50% HP | +7.5% damage below 50% HP |
| Gnome | +10% item effectiveness | +5% item effectiveness |
| Tiefling | +15% fire & dark damage | +7.5% fire & dark damage |
| Dragonborn | +10% all elemental damage | +5% all elemental damage |

- The legacy **stacks with the mother's race passive** (different sources).
- It is fixed at birth from the player's race; gear changes later do not alter it.
- **No class-skill inheritance:** allies cannot use the player's class skills (standing convention), so the legacy is passive/stat-based only.
- **O4a ✅ (2026-10-30):** use the weakened-passive table above. The attribute-echo alternative is **not adopted**.
- **Implementation note:** the Human attribute legacy is auto-applied to the child's two highest attributes at adulthood (the choice-at-birth prompt is deferred). Non-Human legacy passives are stored on the child (`father_legacy`) and wired into combat in **Phase 3** (2026-10-30): Dwarf max HP, Elf dodge, Halfling crit, Orc low-HP damage, Gnome item effectiveness, Tiefling fire/dark damage, Dragonborn all-element damage.

### 6.4 Bond & gifting (no romance)

- The house menu's romance actions (`kiss` at 80+, `propose`, `married` state, wedding accessories, bed events) are **hard-blocked** by `no_romance`. Phase 3 adds both menu hiding and action-time guards, plus save-load sanitizing: engagement/marriage flags are cleared, global `engaged_girls` / `married_girls` entries are removed, and the bond cap is clamped to **100**.
- Talk and gift reuse the existing daily-limit machinery (`girl_talk_today` / `girl_gift_today`). Phase 3 routes true-born daughters through child-specific generic pools (`child_talk_low/mid/high`, `child_gift_love/hate`) with positive bond reactions (+8–14) rather than the adult random gift table. Phase 4 adds **race pools** for all 19 races plus per-mother overrides for the starter girls; the starter girls also carry real `child_talk_*` / `child_gift_*` keys in `monster_girls.yaml`, and unknown races fall back to the generic pool.
- The lounge shows true-born adults as **👧 Daughter** with **Bond** instead of Affection, and hides the blessing/kiss/proposal/night actions. The sub-menu also shows her **Father's Legacy** label.
- Affection cap 100; no engagement/marriage path.

### 6.5 Party integration & restrictions

- Adult children join via the normal house recruitment flow and respect party caps / resonance tiers. **Phase 3:** recruitment explicitly rejects true-born minors (`stage` infant/child) even if a stale save/record puts one in the lounge; `stage` and `prime` survive party/house round-trips.
- Not capturable, not sellable, not releasable, not dispatchable before adulthood. Phase 3 dispatch validation rejects pregnant, post-birth-recovering, and true-born minor girls (see §8).
- Cannot equip gear before adulthood (proposal; revisit if a "training" kit is wanted).
- **Locked (O6):** children count toward the **house monster-girl cap** (house capacity is the only cap); no separate child cap. They count as distinct allies for collection/MQ counts. There is **no special child party slot** — Command Resonance and the normal ally cap govern the party.
- **O15 ✅:** multiple children per mother are allowed (30-day conception cooldown); the house cap remains the only cap.

---

## 7. Awakening inheritance

**Question:** if the mother is Awakened, is the child born Awakened or in the unawakened form?

**Locked (O7): the child is always born in the unawakened form and follows the normal awakening path as an adult** (Lv 40 + cap 40 + **affection 200** + 1 Sigil — per §4.8's revised ladder and `awakening_design.md` Part C).

Reasons:
1. Awakening is a **personal transformation** — per-girl dialogue, a new name, a special scene. Inheriting it skips the character moment entirely.
2. It preserves the **Sigil economy** (5 per save) and the meaning of the choice.
3. It avoids power inflation: awakened skills are upgraded versions; free inheritance would make children strictly superior to their mothers at the same investment.
4. Lore-compatible: the child inherits the mother's **clause-type and gifts**, not her personal recognition/trial.

**Alternatives considered (not adopted):**
- (a) Reduced gate — child still needs a Sigil but lower affection/level requirements.
- (b) Cosmetic inheritance — the child carries the awakened naming theme, no mechanical benefit.
- (c) Full inheritance — not recommended.

Regardless: the mother **keeps** her awakened state through pregnancy and after birth.

**Implementation (Phase 3):** true-born house records carry `mother_key`; the Awaken action looks up `AWAKENINGS[mother_key]` instead of the synthetic `trueborn_*` key, swaps the child's copied innate skills to the mother's awakened kit, and preserves `awakened` / `awakened_skills` through the ally fallback.

---

## 8. Integration points (implementation map)

| Area | File(s) | Change |
|---|---|---|
| State & migration | `character.py` | `family_enabled`, `children`, per-girl `pregnant` / `conceived_day` / `due_day` / `next_conception_day`, pity counters in `ensure_player_fields()` |
| Toggle UI | `gui/settings.py`, `gui/screens/settings_screen.py`, `gui/screens/char_create_screen.py` | `content_level` global (`off` / `fade-to-black` / `written`); `family_enabled` is a final new-game Game Rules choice (no mid-game toggle) |
| Affection ladder v2 | `facilities/house.py`, `character.py`, `combat/ally.py`, `combat/capture.py`, `facilities/dispatch.py` | Caps 100→200 / 200→300; marriage 200→300; awakening 150→200; talk tiers, status icons, dispatch tiers rescaled (§4.8) |
| Father's Legacy | `family.py`, `combat/ally.py`, `combat/stats.py`, `combat/elemental.py`, `combat/ally_skills.py` | Weakened player-race passive table (§6.3b); Phase 3 wires max HP, dodge, crit, low-HP damage, item effectiveness, fire/dark and all-element damage |
| House hub | `facilities/house.py` | "Share the night" action, pregnancy status, children section, Daughter/Bond labels, child talk/gift pools, `no_romance` menu + action guards, ascension/awakening gates, birth/name scene; calls the sleep-sharing UI from `_house_sleep` |
| Sleep-sharing logic | `facilities/sleep_sharing.py` (new) | Pure state machine: visible moods, 3-round Attunement scoring, endings, RNG-injectable; no I/O |
| Sleep-sharing UI | `facilities/sleep_sharing_ui.py` (new) | Story/facility loop via `term.print` / `term.menu` / `term.pause` |
| Birth/family UI | `facilities/family_ui.py` (new) | Birth scenes, pending-birth queue, child naming |
| Scene data | `resources/family_scenes.yaml` + `resources/family_scenes.py` (loader) | Tone/mood action lines, match/miss feedback, random beats, ending lines, per-girl overrides + personal closing line; generic child talk/gift pools; generic fallback pool |
| Day tick | `time_blocks.py` (`_apply_day_rollover`) | Due-date check, growth ticks, nesting buff upkeep; frozen-time guards |
| Dreams | `dreams.py` + `resources/dreams.py` (new) | Independent system — [`dream_events_design.md`](./dream_events_design.md); hooks after `end_day(slept=True)` |
| Ally conversion | `combat/ally.py` | Adult conversion to a true-born house record; missing-template fallback uses stored attributes/skills; family fields survive the round-trip |
| Dispatch | `facilities/dispatch.py` | `dispatch_block_reason()` excludes pregnant girls, post-birth recovery, and true-born minors from eligibility and launch |
| Voss ending | `facilities/story_beats.py` / `facilities/star_tower.py` / `gui/screens/city_screen.py` | **The First Page** epilogue beat + one-time flag + keepsake after MQ6 + Moth arc |
| Tests | `tests/_diag_family.py` (new) | State machine, chance math, growth ticks, round-trips, old-save smoke, Phase 3 gates + legacy combat checks |
| Docs | `README.md` / `wiki/index.html` / changelog / [`family_phase4_playtest_checklist.md`](./family_phase4_playtest_checklist.md) | Player-facing family section, v0.1.9.1 changelog, regenerated wiki, Phase 4 checklist (Phase 4) |

### Threading & notification conventions (from the planning guide)

- Scenes run in the **facility thread** → use `term` / `_tprint` I/O only; never tkinter off-thread.
- Quest/family progress notifications go to the **Journal + session log** — never toasts.
- Scenes resolve atomically; no save mid-scene.

---

## 9. Save compatibility

- All new fields via `ensure_player_fields()` `.setdefault()` — old saves load cleanly.
- `family_enabled` defaults to `False` on old saves and stays OFF (no mid-game opt-in).
- **Affection caps migrate** (base 100→200, engaged/married 200→300) with values preserved; married girls keep already-granted accessories.
- No existing field changes shape; children use a **new** list; pregnancy fields live on existing girl records (harmless when absent).
- Time-pocket saves (Wonderland/EH) cannot carry an in-progress family tick; ticks simply wait for the next normal day rollover.

---

## 10. Balance & risks

| Risk | Mitigation |
|---|---|
| Losing 1 of 3–4 active slots for pregnancy + recovery | 30-day pregnancy (combat loss only in the third period), 7-day recovery, nesting buff, bench reinforcement; tune after playtest |
| Child power creep | Level 1 start, no inherited learned/awakened skills, 0.9 stat factor, normal level caps |
| Frustration from a chance-based system | Pity counter (+10%/attempt after 5, guaranteed at 8); scene rewards are worthwhile even without conception |
| Party/house caps | Locked O6: children count toward the house monster-girl cap; no separate child cap (O15 covers multiple children per mother) |
| Affection rebalance | Caps/thresholds rescaled (§4.8); migration preserves values; Piece of Relationship stays at 200 to avoid retroactive nerfs |
| Old-save surprise | Family OFF by default, no mid-game opt-in; `content_level` defaults to fade-to-black; no modal on load |
| Toggle semantics | `content_level: off` disables sleep sharing; `family_enabled off` allows sleep sharing but never conception (§3.1) |
| Text volume | Generic scene pool first; per-girl writing is Phase 4 content debt — budget it |
| Testability | All durations/chances in one constants block; a diag script can override them in-memory |

---

## 11. Phases

- **Phase 0 — Documentation (this doc + codex amendment)** ✅ 2026-10-27
- **Phase 1 — State & switches (no scenes)** ✅ 2026-10-30:
  - `family.py` — constants, `ensure_family_fields`, affection-cap migration, content gating, sleep-sharing eligibility + season/moon chance, pregnancy/conception/growth helpers, `family_tick`.
  - `content_level` in `gui/settings.py` + Settings-screen control (`off` / `fade-to-black` / `written`).
  - Affection ladder v2 in `character.py`, `combat/ally.py`, `combat/capture.py`, `facilities/house.py`, `facilities/dispatch.py`, `facilities/house_stories.py`; tutorial/Arcane Tower text updated. Marriage 300, awakening 200, base cap 200, engaged cap 300; kiss/proposal unchanged.
  - Day-tick hook in `time_blocks._apply_day_rollover`; third-period lounge return is active, birth/child creation deferred to Phase 2.
  - `tests/_diag_family.py` — all checks pass.
  - **Deferred:** house "Share the night" menu entry + mini-game UI (Phase 2), birth/child creation (Phase 2), dispatch exclusions (Phase 3), README/wiki/changelog (Phase 4).
- **Phase 2 — Vertical slice** ✅ 2026-10-30 (Shared Night revised to **Attunement** after playtest):
  - `facilities/sleep_sharing.py` — pure 3-round mini-game: visible mood, exact/same-family/opposite tone scoring, together/warm/quiet/rest endings.
  - `resources/family_scenes.py` — tone and mood lines, match/miss feedback, random beats, ending lines, **per-girl action overrides** + helpers, birth/naming text (fade-to-black; explicit written variants deferred).
  - `facilities/sleep_sharing_ui.py` — Attunement bar, visible mood, tone menu, personal closing line from `house_night_ending` / `house_bond_kiss`; `facilities/family_ui.py` — birth scenes + naming.
  - `family.py` — conception outcomes for together/warm/quiet, `shared_night`/`beloved` buffs, father legacy, child records, **15/40/60 growth milestones** (`is_prime`, `growth_days_to_prime`), birth on day rollover, adult conversion to the house roster, Event Horizon guard.
  - House integration: "Share the night" action (140+), ally-initiated roll (160+, season/moon), buff merge, Family submenu (pregnancy/children/naming, stage + prime countdown).
  - Game Rules: `family_enabled` is now an **active** creation choice (default OFF, final per save); old saves stay OFF.
  - `combat/ally.py` — missing-template fallback now uses stored attributes/skills, so grown true-born children are playable.
  - `tests/_diag_family.py` extended; all checks pass (Attunement scoring/endings, conception, birth, naming, conversion, 15/40/60 growth, per-girl UI lines).
  - **Deferred:** dispatch/ascension exclusions for pregnant/children (Phase 3), non-Human legacy combat passives (Phase 3), per-girl scene writing + explicit variants (Phase 4), README/wiki/changelog (Phase 4).
- **Phase 3 — Integration & balance** ✅ 2026-10-30:
  - `family.py` — child helpers (`is_trueborn`, `is_trueborn_minor`), no-romance sanitizing (clears engagement/marriage, clamps bond cap 100), Father's Legacy passive helpers.
  - `facilities/house.py` — Daughter/Bond lounge labels, child talk/gift pools, hidden blessing/kiss/proposal/night actions, action-time romance guards, ascension/awakening block during pregnancy/recovery/minor status.
  - `facilities/dispatch.py` — shared `dispatch_block_reason()`; excludes pregnant, post-birth-recovering, and true-born minors from both eligibility and launch.
  - `combat/ally.py` / `combat/ally_skills.py` / `combat/stats.py` / `combat/elemental.py` — Father's Legacy wired: max HP, dodge, crit, low-HP damage, item effectiveness, fire/dark and all-element damage; stage/prime survive round-trips; minor recruitment blocked; true-born awakening uses `mother_key`.
  - `tests/_diag_family.py` — Phase 3 gates + legacy checks added; regression suite (dispatch, house girls/stories, growth, race passives, crit, dodge, elemental, save, routing) passes.
  - **Balance decision:** children use the normal house/party capacities (no special slot); 15/40/60 growth unchanged; legacy values remain the §6.3b weakened table.
- **Phase 4 — Content rollout** ✅ 2026-10-30:
  - `resources/family_scenes.yaml` + `resources/family_scenes.py` (loader) — one signature Attunement line per tone for all 56 capturable monster girls + Alice/Red Hood/Dorothy, merged with the generic pool; race-flavoured daughter talk/gift pools for all 19 races plus per-mother overrides and `child_talk_*` / `child_gift_*` YAML keys for the starter girls; `written` action/ending prose pools (non-graphic), selected by `content_level`.
  - `facilities/star_tower.py` + `facilities/story_beats.py` + `gui/screens/city_screen.py` — **The First Page** Voss & Lumen epilogue: city-entry trigger on Skylume after MQ6 + Moth arc, one-time flag, Journal entry, no-power keepsake.
  - `README.md`, `version.py`, `gui/screens/changelog_screen.py`, `wiki/index.html` — player-facing guide section, v0.1.9.0 changelog block, regenerated wiki.
  - `tests/_diag_family.py` — full roster coverage, child race/mother pools, epilogue trigger + scene checks.
  - **Manual playtest pending:** use [`family_phase4_playtest_checklist.md`](./family_phase4_playtest_checklist.md) to play through Shared Night, written mode, pregnancy/birth, child growth/recruitment, and the Voss epilogue on a real save.

**All decisions are locked (2026-10-30) — Phase 4 complete; manual playtest remains.**

---

## 12. Decisions

### All decisions locked (O1–O15, O4a) — 2026-10-30

| # | Decision | Locked answer |
|---|---|---|
| O1 | Child aging | Ages to adulthood, then stops at prime |
| O2 | Voss ending | Lumen is **expecting** |
| O3 | Reproduction scope | World-wide but rare |
| O4 | Father inheritance | Father's Legacy: weakened player-race passive + family name (§6.3b) |
| O4a | Father's Legacy values | **Use the §6.3b weakened-passive table** (attribute echo not adopted) |
| O5 | Eligibility | All capturable girls + all heroines |
| O6 | House/child caps | Children count toward the house cap; no separate child cap |
| O7 | Awakening inheritance | Children born unawakened; normal path |
| O8 | Sleep-sharing affection gates | Player-initiated **140**; ally-initiated **160**; ladder v2 (§4.8) |
| O9 | Timings & conception | Pregnancy **30 days, split 3×10**; third period no combat; birth recovery 7 days; growth milestones **15 (infant→child) / 40 (adult) / 60 (prime)**; conception 12% base + pity |
| O10 | Toggle semantics | Three-state `content_level` × `family_enabled` matrix (§3.1) |
| O11 | Mini-game actions | Tender / Playful / Bold / Shy / End (§4.4) |
| O12 | Lowest-tier conception | Allowed (base chance, no ending bonus: **Quiet**) |
| O13 | Buffs | House buff to party + `shared_night` (MC) + `beloved` (girl); merge, never stack (§4.5) |
| O14 | Initiation rates | 6% base, engaged +4%, married +8%, season/moon modifiers (§4.9), max 1/night |
| O15 | Multiple children per mother | **Yes**, with a **30-day conception cooldown** after birth; the house cap remains the only cap |
