# Dream Events — Design (locked)

**Status:** Phases 1–4 IMPLEMENTED (2026-10-30); mature variants intentionally deferred
**Scope:** A data-driven dream system for sleep: boon dreams, burden dreams, choice dreams, and scripted story dreams. Dreams reuse the existing **story/facility UI**, write to the Journal, and use shared reward/buff APIs.
**Related docs:** [`family_system_design.md`](./family_system_design.md) §4 (sleep sharing) · [`time_system_design.md`](./time_system_design.md) · [`house_stories_design.md`](./house_stories_design.md) · [`quest_system_design.md`](./quest_system_design.md) · [`karma_system_design.md`](./karma_system_design.md) (Game Rules)
**Reference:** Elona's sleep/dream system (random good/bad dreams with weighted chances, plus a rare choice dream) — **mechanics inspiration only**; all names, text, effects, and values here are original.

> **Design goal:** make sleep a narrative event, not a button. Dreams are short, atmospheric, occasionally useful, and occasionally unsettling — never a punishment spiral and never a second combat system.

---

## 0. Summary

- **One dream roll per sleep** (home / inn / camp) at a **20% base chance**, weighted by context.
- **Four categories:** boon, burden, choice, story.
- **Registry-driven:** `resources/dreams.py` holds dream definitions; `dreams.py` builds the eligible pool, rolls, applies effects, and journals the result.
- **UI:** short dreams render as facility-style text in the existing `StoryScreen` / `FacilityScreen` wrapper (`term.print` + `term.menu` for choices). No new UI system.
- **Persistence:** `player["dreams"] = {"seen": {}, "last_day": N, "streak": N}` via `ensure_player_fields()`.
- **Independent of the family system** — but family/content toggles gate mature dream variants (D5).
- **Locked scope (v1), see §9:** 20% base chance · home/inn/camp · Dream Journal in Phase 3 · no item/stat loss · base dreams always on · no Karma coupling · no Wonderland or Event Horizon dreams · new `dream_blessed` buff type.

---

## 1. Player experience

1. The player sleeps (house bed, inn, or camp).
2. After the day rolls (`end_day(slept=True)`), `maybe_offer_dream(player, context)` runs.
3. If a dream triggers, a short scene appears — 3–8 lines, occasionally a choice.
4. The dream applies its effect (or records a choice result), writes a `[DREAM]` Journal entry, and returns the player to the morning message.
5. Story dreams (once-only) can open a full `StoryScreen` and set flags.

**Dreams should be skippable.** Repeat dreams show a **Skip** option; story dreams are one-time.

---

## 2. Dream categories

### 2.1 Boon dreams (positive, minor)

| Dream type | Effect examples |
|---|---|
| **Inspired** | Small XP / learning progress for the player or an ally |
| **Restful** | Extra HP or stress recovery; short `dream_blessed` buff (§3.1) |
| **Omen** | Preview of the next dungeon room type or floor modifier |
| **Lucky** | Small temporary Luck/accuracy buff for N rooms |
| **Treasure** | Small item or crafting material (inventory-space safe) |
| **Memory** | Lore fragment; Journal entry; optional codex/collection progress |
| **Bond** | Small affection gain with a featured girl |

### 2.2 Burden dreams (negative, mild)

| Dream type | Effect examples |
|---|---|
| **Nightmare** | Player stress **+34** (rattled raises the hallucination tier) and party stress +8 |
| **Restless** | Party stress +4, player stress +20, +5 XP |
| **Thief** | Lose a small capped amount of gold (no more than 5% or 50g) |
| **Dread** | Next combat starts with the existing `dread` status (rare) |
| **Ominous** | Warning of the next floor's modifier (atmospheric, not harmful) |

**Guardrails (D4):** no permanent stat loss, no item destruction, no lost progression, no chains of burden dreams (see §4.4). Gold is the only stealable resource and never exceeds 5% of the purse or 50g, whichever is lower. **Phase 1 ships Nightmare, Restless, Thief and Ominous; Dread needs a Phase 2/4 pass** (a combat status applied at sleep needs its own persistence check).

### 2.3 Choice dreams (interactive — Phase 2, shipped)

Short 2–3 choice scenes with a trade-off, resolved via `term.menu`:

- *The Offered Hand* — take the hand (damage buff, +stress) vs refuse (XP).
- *The Accord Echo* (once) — listen to the clause (XP, +stress) vs cover your ears (Dream-Blessed).
- *The Mirror Self* — hold the reflection's gaze (XP, +stress) vs look away (+crit).
- *The Feast* — eat your fill (Dream-Blessed for the party) vs share the seat (affection).

Choices are **legible** (the trade-off is in the option text) and **consequence-light**. A repeatable dream whose choice has been seen before adds a **Skip** option (`Wake up. (let the dream go)`) that applies nothing and still counts as seen. `once` choices never offer Skip — they never repeat.

### 2.4 Story dreams (scripted, once-only — Phase 3, shipped)

Flag-gated, high-value narrative beats. Shipped beats:

| Dream | Trigger | Gate |
|---|---|---|
| **The First Night Not Alone** | `had_shared_night` (set by the first Shared Night) | `content_level ≠ off` |
| **The Lamp in the Unbuilt Room** | `family_expecting` (set on conception) | `family_enabled` + `content_level ≠ off` |
| **The Archive That Rains Upward** | `voss_epilogue_seen` | — |
| **The Counting in the Walls** | a living party member of race **Vampire** | — |

Story dreams are **queued beats**, delivered in the facility output (longer multi-line scenes), can set story flags (`flags_set`), and never repeat. They are never rolled.

**Not in v1 (D7):** Wonderland time-pocket dreams and Event Horizon / entropy dreams are **out of scope**. Neither location rolls or delivers dreams at all (§4.1); both can be added later as ordinary scripted story dreams without a data-model change.

### 2.5 Meta dreams (rare, optional)

Pandemonium already breaks the fourth wall (Mary Sue). A rare **meta dream** (a "dream choice" that knows it is a dream) can exist as a one-time flag-gated curiosity. Optional; content-gated.

---

## 3. Data model

`resources/dreams.py`:

```python
DREAMS = [
    {
        "id": "dream_accord_echo",
        "name": "The Accord Echo",
        "category": "choice",            # boon | burden | choice | story
        "weight": 3,
        "once": True,
        "content_level": None,           # None | "written" (mature variants)
        "conditions": {
            "location": ("home", "inn", "camp"),
            "phase": None,
            "min_day": 1,
            "flags": [],
            "not_flags": [],
            "party_min": 0,
            "stress_min": 0,
            "family": False,             # requires family_enabled (mature/story only)
        },
        "lines": [
            "You dream of a page turning in a language older than words.",
        ],
        "prompts": [                     # choice dreams only
            {"text": "Take the hand. (+10% damage · +20 stress)",
             "reply": "You wake with your fingers closed around nothing.",
             "effects": {"buff": {"type": "damage_boost", "value": 0.10,
                                   "rooms": 2, "target": "player"},
                         "player_stress": 20}},
            {"text": "Refuse, and walk on. (+15 XP)",
             "reply": "The hand folds away without offence.",
             "effects": {"xp": 15}},
        ],
        "effects": {"stress": -5},       # applied for non-choice dreams
    },
]
```

**Rules:**
- Effects use shared APIs only: `leveling.gain_exp` / `gain_exp_ally`, `resources.items.build_item` + `inventory.add_item_to_inventory`, `family.grant_sleep_buff` for `dream_blessed`, `player["stress"]`, affection helpers.
- Lines support token substitution (`{name}`, `{girl}`, `{location}`, `{day}`).
- `conditions` is evaluated against a small context dict (`location`, `day`, `phase`, flags, party, stress, `family_enabled`). **No `wonderland_active` key (D7).**
- **Base dreams are always in the pool (D5).** Only entries with `content_level` set, or `conditions.family = True`, check `get_content_level()` / `family_system_enabled()`.
- **Karma is never read by the dream system (D6).**
- No dream may delete items, remove gold beyond the D4 cap, reduce levels, or reduce maximum stats.

### 3.1 The `dream_blessed` buff (D8)

Dream boons use a **new buff type**, not `well_rested`:

```python
{"type": "dream_blessed", "stat": "all", "value": 1, "remaining": 2}
```

- **Never stacks with other sleep buffs.** Add `"dream_blessed"` to `family.SLEEP_BUFF_TYPES` so `grant_sleep_buff()` merges it with `well_rested` / `shared_night` (keep the stronger value + longer duration, keep the stronger entry's type name). A dream blessing on a manor bed must not double-dip.
- **Always grant through `family.grant_sleep_buff(player, "dream_blessed", value, rooms)`** (allies too) so the merge rule lives in one place.
- **Writing a buff alone does nothing** — every read/tick site must learn the type:

| Site | Change |
|---|---|
| `combat/stats.py` `get_total_attribute` | add `"dream_blessed"` to the `("blessing", "well_rested")` tuple |
| `combat/ally.py` ally stat total | same one-word addition |
| `dungeon.py` 3 per-room tick loops (city entry / standard floors / Pandemonium, player + allies) | add `"dream_blessed"` beside every `== "well_rested"` check |
| `combat/status_effects.py` status tag | add to `("blessing", "well_rested", "floor_buff")` |
| `combat/combat_ui.py` `_get_entity_buff_tags` | new `elif btype == "dream_blessed":` tag (e.g. `DRM+N`) |

- Value 1–2, duration 1–2 rooms (§7). Flavor: "You wake with the dream still sharp behind your eyes."

---

## 4. Trigger, weighting & anti-frustration

### 4.1 When dreams roll

- **Home / inn / camp sleep:** one roll per sleep, after `end_day(slept=True)`.
- **Shared nights:** a sleep-sharing event resolves first; the dream roll still happens afterward (dreams are independent of the family system).
- **Wonderland:** **no dreams at all (D7)** — time is frozen and the roll is suppressed; no story dream is queued.
- **Event Horizon:** **no dreams at all (D7)** — the outside day is untouched and the roll is suppressed, including on run end.
- **Death/collapse sleep?** No — death already has its own screen; no dream on the death path.

**Base chance (D1, locked):** `DREAM_CHANCE = 0.20` — one roll per sleep, plus the soft pity in §4.2. A no-dream night is normal and keeps dreams special.

### 4.2 Weighting & modifiers

| Modifier | Effect |
|---|---|
| High stress (≥ 60) | Burden dream weight ×2 |
| Fatigue stacks ≥ 2 | Burden dream weight ×1.5 |
| Pandemonium corruption tier ≥ 3 | Burden/eldritch dream weight ×1.5 *(n/a — dreams never roll inside Pandemonium)* |
| Married/engaged girl in party | Bond dream weight ×2 |
| Visiting a new city / first night after arriving | Memory/omen weight ×1.5 |
| No dream in last 5 sleeps | Dream chance +5% per night (soft pity) |
| Last dream was a burden | Next dream's burden weight ×0.5 (no spiral) |

**Karma has no influence (D6)** — no Karma gates, no Karma-weighted categories, no Karma changes from dream choices. Dreams are atmosphere, not morality.

**Base dreams always on (D5)** — `family_enabled` / `content_level` gate mature and story variants only; the boon/burden/choice pool never disappears because of a toggle.

### 4.3 Selection algorithm

1. Build the eligible pool from `DREAMS` (conditions + content gates).
2. Remove `once` dreams already in `player["dreams"]["seen"]`.
3. Apply repeat decay: `weight × 0.6^seen_count` (floor 0.2) for repeatable dreams.
4. Apply context modifiers (§4.2).
5. Weighted random pick with an **injected RNG** (testability).
6. Mark seen, apply effects/choices, write the Journal entry.

### 4.4 Anti-frustration rules

- Never two burden dreams in a row (last-dream check).
- Gold loss capped (5% or 50g, whichever is lower).
- No permanent losses; no lost items; no level/stat reductions.
- Every burden dream includes a flavor "small mercy" line and a recoverable effect.
- Story dreams are never blocked by RNG once their conditions are met — they are queued, not rolled (see §4.5).

### 4.5 Story-dream delivery

Story dreams are **queued beats**, not pool entries: when their flag/condition becomes true, the next sleep delivers them (before the random roll). This guarantees narrative beats land without fighting RNG.

---

## 5. UI & integration

### 5.1 Presentation

| Dream kind | UI |
|---|---|
| Boon/burden (non-interactive) | Short lines in the facility/story output panel + `term.pause`; 3–8 lines |
| Choice dream | `term.print` lines + `term.menu` options; applies the chosen effects; repeats add **Skip** |
| Story dream | Full `StoryScreen` scene (paused clock), like Fireside Tales |
| Repeat/skip | **Skip** button on repeatable dreams; story dreams are one-time |

**Rule:** dreams run in the **facility thread** (sleep flows already do) — `term` I/O only, no tkinter off-thread, no toasts. Journal + session log for persistence.

### 5.2 Hook points

| File | Hook |
|---|---|
| `facilities/house.py` | `_house_sleep()` — after `end_day(slept=True)`, before the morning message |
| `facilities/inn.py` | both `end_day(slept=True)` paths (night's rest) |
| `facilities/camp.py` | camping `end_day(slept=True)` |
| `time_blocks.py` | no change required if the hook is player-side (recommended); optionally a shared `post_sleep_hook(player, context)` for one call site |
| `character.py` | `ensure_player_fields()`: `player["dreams"] = {"seen": {}, "last_day": 0, "streak": 0}` |
| `gui/screens/changelog_screen.py` / README / wiki | player-facing summaries after ship |

### 5.3 Journal & collection

- Every dream writes a `[DREAM]` Journal event (title + one line).
- **Dream Journal page (Phase 3, shipped):** Inventory → **Journal → Dreams** lists every seen dream (name, category, full flavor text, times seen) with a "seen X of Y" header. Data comes from `dreams.journal_entries(player)` (registry order, `seen` counts).

---

## 6. Content & tone

- **Follow the world:** Accord fragments, the Deep Dark, vampire hunger, Mary Sue's meta nature. Wonderland and Event Horizon dream content is **deferred past v1 (D7)** — do not write it yet.
- Keep dreams short and impressionistic; they should feel like fragments, not chapters.
- **No fourth-wall** content unless explicitly flagged (`meta` story dream, once).
- Mature variants (family/romance) require `family_enabled` + `content_level: written`; default dreams are non-explicit (D5).
- Dream text should never contradict locked lore; if a dream is ambiguous, prefer "impression" over "revelation".

---

## 7. Balance

| Item | Guideline |
|---|---|
| Buffs | Small and short (1–2 rooms or 1 day); `dream_blessed` only (§3.1), merges with other sleep buffs |
| XP | ≤ one room's worth; never a level in one dream |
| Gold/items | Small; pity-safe; no unique/legendary items from dreams |
| Burden | Mild, recoverable, never permanent — no item or stat loss, gold loss capped (D4) |
| Frequency | ~1 dream per 5 sleeps at base (20%, plus soft pity); story dreams guaranteed when queued |
| Power creep | Dreams are flavor-first; any boon should be comparable to a good room event |

---

## 8. Phases

- **Phase 1 — Registry + boon/burden dreams:** `resources/dreams.py`, `dreams.py` (roll/pool/effects), Journal entries, hooks at house/inn/camp sleep. No choices. **✅ Shipped 2026-10-30.**
- **Phase 2 — Choice dreams:** `term.menu` scenes, effect resolution, once/story gating. **✅ Shipped 2026-10-30.**
- **Phase 3 — Story dreams + Dream Journal (D3):** scripted beats (family, Voss, Father of Thirst), Dream Journal collection page. **✅ Shipped 2026-10-30.**
- **Phase 4 — Content rollout:** per-context dream writing, wiki/README/changelog. **✅ Shipped 2026-10-30** (mature/`content_level`-gated variants deliberately **excluded** by the designer).

**§9 decisions are locked (2026-10-30).** Wonderland and Event Horizon dreams stay out of v1 (D7).

### Phase 2 implementation notes

- **Choice resolution:** `_run_choice()` prints the scene, shows `term.menu` (2 prompts, `allow_cancel=False`, 2 columns), substitutes tokens in the **option labels** (`{girl}`), prints the chosen option's `reply`, then applies that prompt's effects through the same `_apply_effects()` used by boons/burdens.
- **Skip (D-§1):** a repeatable choice dream seen at least once adds `Wake up. (let the dream go)`; skipping applies nothing, marks the sighting, and journals it as `(let it go)`. Once-dreams never offer it.
- **Choice trade-offs are stress-forward:** because dreams fire *after* the sleep reset, stress-relief options would be no-ops — accepting power costs stress instead, and the safe option usually grants a buff, XP or affection.
- **Story queue (§4.5) ready:** `dreams.queue_story_dream(player, dream_id)` + `player["dreams"]["queue"]`; the next sleep delivers a queued dream **before** the random roll and ignores `DREAM_CHANCE`. `category: "story"` entries are never rolled even if they sit in the registry. Phase 3 only needs content + the Dream Journal page.

### Phase 3 implementation notes

- **Automatic queueing:** `dreams.check_story_triggers(player, location)` runs at the start of every sleep; any story dream whose conditions hold (and which has not been seen or queued) joins the queue. No quest hooks needed — flags do the work.
- **Flag sources:** `family.apply_sleep_outcome()` sets `player["had_shared_night"]` (first shared ending) and `player["family_expecting"]` (on conception). Voss uses the existing `voss_epilogue_seen` quest flag; the vampire beat uses new condition `conditions.party_race`.
- **New condition keys:** `conditions.party_race` (a living party member of that race) and `content_level: "any"` (intimacy content is on — used by the two family beats).
- **Story flags:** `flags_set` on a dream writes the flag to the player dict **and** `player["quests"]["flags"]` (e.g. `dreamed_of_voss`, `dreamed_of_the_thirst`) for future quest hooks.
- **Presentation:** story beats are longer line sets printed in the facility output like Fireside Tales (there is no separate `StoryScreen` class); the sleep hook's own `term.pause()` ends the beat.
- **Dream Journal:** Inventory → Journal → **Dreams** tab (`inventory_screen._render_dream_subtab`) rendered from `dreams.journal_entries(player)`.

### Phase 4 implementation notes

- **Per-context dreams (4 new, 23 total):** `dream_hearth_song` (home only, Dream-Blessed), `dream_home_remembers` (home only, once, day 4+, XP), `dream_road_patience` (camp only, XP), `dream_rented_room` (inn only, companion stress). They use the existing `conditions.location` tuple — no new machinery.
- **Mature variants are OUT OF SCOPE.** No `content_level: "written"` dream variants and no explicit text were written; the two family story beats use `content_level: "any"` (intimacy on) with non-explicit text.
- **Wiki:** new `#/dreams` route in `tests/gen_wiki_html.py`, sourced from [`dreams_wiki.md`](./dreams_wiki.md) (mechanics, every dream, triggers, stress interplay, Dream Journal). Rebuild with `tests/gen_wiki_html.py`.
- **README:** new **Dreams** section (after Family & Children) and a new **Time, Sleep & Stress** section (before Travel & Exploration), plus the companion combat-stress bullet under Dispatch.

### Phase 1 implementation notes

- **Files:** `resources/dreams.py` (registry, 11 dreams) · `dreams.py` (state, chance, pool, weighting, effects, Journal) · hooks in `facilities/house.py` (`_house_sleep`), `facilities/inn.py` (normal inn only — the Wonderland inn is skipped), `facilities/camp.py` (`camp_event`) and `facilities/travel.py` (both terminal camp paths). State seeded in `character.ensure_player_fields()`.
- **Player stress (resolved 2026-10-30):** the player now has a real `stress` meter (0–100, see [`stress_system_design.md`](./stress_system_design.md)), so burden dreams feed it directly via the `player_stress` effect. Stress effects that target *companions* still use the party-girl records.
- **Deviation — corruption weighting:** §4.2's Pandemonium corruption modifier cannot apply — dreams only roll at home / inn / camp, never inside a dungeon.
- **Location tracking:** "first dream in a new place" is approximated with `player["dreams"]["last_location"]` (Memory/Omen dreams get ×1.5), not a per-city arrival ledger.
- **Journal:** entries use the `[DREAM]` tag. No toasts (`gui-log-system` convention).
- **Diagnostic:** `tests/_diag_dreams.py` — 53 checks (chance/pity, conditions, weighting, every effect, the `dream_blessed` merge rule, suppression, wiring guards).

---

## 9. Decisions (locked 2026-10-30)

| # | Decision | Locked answer | Where it lands |
|---|---|---|---|
| D1 | Base dream chance per sleep | **20%** | §4.1 `DREAM_CHANCE = 0.20`; §7 ≈ 1 dream / 5 sleeps |
| D2 | Dreams at inns and camps, or home only? | **All three** (home, inn, camp) | §1, §4.1; home is the story-dream delivery site |
| D3 | Dream Journal collection UI in scope? | **In scope — Phase 3** | §5.3, §8 |
| D4 | Burden severity ceiling | **No item loss, no stat loss**; gold capped at 5% / 50g | §2.2, §4.4 |
| D5 | Do `family_enabled` / `content_level` gate all dreams or only mature variants? | **Base dreams always on**; toggles gate mature/story variants only | §3, §4.2, §6 |
| D6 | Are dreams affected by Karma? | **No** | §4.2 |
| D7 | Scripted Wonderland/EH dreams in v1? | **No — out of scope for v1** | §2.4, §4.1, §6; no `wonderland` condition key |
| D8 | Dream buff type | **New `dream_blessed` type** | §3.1 (added to `SLEEP_BUFF_TYPES`, wired at every read/tick site) |
