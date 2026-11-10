# Player Stress — Design (locked & implemented 2026-10-30)

**Scope:** a player-side stress meter that sits *in front of* the existing fatigue stacks, so a skipped night is a warning and real exhaustion has to be earned.
**Related:** `time_blocks.py` (engine) · `combat/hallucination.py` (rattled tier) · `docs/dream_events_design.md` (burden dreams feed the meter) · `docs/family_system_design.md` (companion stress, same 0–100 scale)

> **Design goal:** make sleep loss legible. Fatigue was a blunt "+1 per unslept day"; stress gives the player a visible meter, a warning band, and a bridge to companion stress, without turning sleep into a punishment spiral.

---

## 1. Rules (locked)

| Item | Value |
|---|---|
| Meter | `player["stress"]`, integer **0–100** (same scale as companion stress) |
| Accrual | **+50 per unslept day rollover** (`time_blocks.STRESS_PER_UNSLEPT_DAY`) |
| Conversion | every full **100** → **+1 fatigue stack** (cap `MAX_FATIGUE = 3`); the leftover stays in the meter |
| Overflow at the fatigue cap | the converted 100 is **dropped** — never banked for later |
| Bands | **calm** < 34 · **worn** 34–66 · **rattled** ≥ 67 |
| Clears | **only a real sleep** (house bed / inn Sleep / camp) — clears stress *and* fatigue |
| Suppression | Wonderland (time pocket) and Event Horizon (frozen clock) accrue nothing; Pandemonium accrues (rev 3.5 rule) |
| HUD | every top bar: `· STRESS 50`, with the 👁 marker at rattled (`· 👁 STRESS 84`) |

**What stress does before it converts:**
- It is a warning meter and a dream/flavor hook (no direct stat penalty — fatigue owns that).
- **Rattled (≥ 67):** `hallucination_tier = fatigue + karma shift + 1`, floored at tier 2. A rattled mind hallucinates *without* exhaustion — this is how a Nightmare follows you into the next night.

**What fatigue still does:** −1 to every attribute per stack (`combat/stats.py`, Event Horizon suppressed), HUD `FATIGUE I/II/III`, and hallucinations from stack II.

---

## 1a. Sources (locked 2026-10-30)

| Source | Player | Companions |
|---|---|---|
| Unslept day rollover | **+50** | — |
| Nightmare dream | +34 | party **+8** |
| Restless dream | +20 | party **+4** |
| **Companion falls in combat** | **+34 per fall** | fallen **+34**, every other living companion **+20 per fall** |
| Real sleep | clears to 0 | **−10** each |

No stress is charged in Wonderland or Event Horizon (both the player meter and the companion charges are suppressed).

### Companion stress — what it does (no fatigue ladder)

Companions use the same 0–100 meter but never convert into fatigue; they wear down instead:

| Band | Threshold | Effect |
|---|---|---|
| Calm | < 50 | — |
| **Weary** | ≥ 50 | −1 all attributes in combat · HUD `WEA` |
| **Frayed** | ≥ 75 | −2 all attributes in combat · HUD `FRY` |
| **Burned Out** | ≥ 90 | −3 all attributes · HUD `EXH` · **refuses the encounter** |

The bands mirror `facilities/dispatch.stress_band()` (Calm / Wound-Up / Tired / Weary / Burned Out) — combat adds the Weary/Frayed/Burned Out penalties and the refusal; dispatch keeps its own mood/success/refusal rules.

**Refusal:** at encounter start a Burned Out companion in the **front row** refuses to fight and sits the fight out (excluded from front row, bench, living-allies lists and the party HUD); bench companions are not asked, so they stay quiet until deployed. She recovers normally afterwards. Refusal lines come from `combat/party_stress.REFUSAL_LINES`, and a template can override with `ENEMIES[key]["dialogue"]["stress_refusal"]` (`{name}` substituted).

**Fall detection:** no knockout site is patched. `begin_encounter()` marks every living companion with `_combat_started_alive`; `settle_pending_falls()` charges stress for anyone who ends the fight still down. The marker is popped, so settlement is idempotent; a superboss loop that exits without settling is caught by the next `begin_encounter()` or by the next real sleep (`on_party_sleep()`).

---

## 2. Why this shape

- **Two skipped nights → one fatigue stack** keeps the old cadence for the *first* consequence (night 2 instead of night 1 per stack) while making the first night recoverable and visible.
- Stress can be **fed by other systems** (dreams today; family/dungeon/combat later) without touching the fatigue ladder.
- The 0–100 scale matches companion stress (`facilities/dispatch.py` mood bands), so future UI and text can treat the two consistently.
- No new time costs: stress rides on the existing `end_day(slept=False)` boundaries (block overflow, Wait-a-While from Night, unslept travel).

---

## 3. Interactions

| System | Behavior |
|---|---|
| Block overflow / Wait | every unslept rollover adds +50 stress |
| Camp | counts as real sleep → clears stress (both camp options) |
| Inn "Rest" (1 block, full heal) | **no stress change** (locked decision) |
| Hallucination victory | existing rule unchanged (stack II → I; stack III sleep-only) |
| Burden dreams | Nightmare **+34**, Restless **+20** player stress (applied after the sleep reset, so the new day starts tense) |
| Companion falls | +34 player, +34 fallen, +20 witnesses — charged at fight end (or at the next encounter/sleep for superboss loops) |
| Burned Out companions | −3 all attributes and refuse the encounter (see §1a) |
| Sleep | player clears to 0; companions −10 each |
| Wonderland / EH | no accrual, no conversion (companion charges suppressed too) |

---

## 4. Files

- `time_blocks.py` — constants (`STRESS_MAX`, `STRESS_PER_UNSLEPT_DAY`, `STRESS_WORN_MIN`, `STRESS_RATTLED_MIN`), helpers `get_stress`, `stress_band`, `is_rattled`, `add_stress`, HUD line in `format_block_track`, `end_day` reset/conversion.
- `combat/party_stress.py` — companion meter, fall settlement, refusal, banded penalty/tag, sleep recovery; `REFUSAL_LINES` + template override.
- `combat/hallucination.py` — rattled tier bump, rattled-only trigger.
- `combat/ally.py` — stress penalty in `get_ally_effective_attribute`; `_stress_sit_out` filters on the party-selection helpers; `combat/combat_ui.py` HUD tags.
- `combat/combat_engine.py` / `combat/superboss_common.py` — `begin_encounter` at fight start, `settle_pending_falls` at fight end.
- `facilities/house.py`, `facilities/inn.py`, `facilities/camp.py` — `on_party_sleep` at real sleep.
- `character.py` — `stress` seeded in `ensure_player_fields()` and `build_character()`.
- `dreams.py` / `resources/dreams.py` — `player_stress` dream effect.
- Diagnostics: `tests/_diag_stress.py` (35 checks), `tests/_diag_party_stress.py` (39 checks), updated `tests/_diag_block_time.py` and `tests/_diag_dungeon_fatigue.py`.

---

## 5. Future hooks (not implemented)

- Stress sources beyond sleeping, dreams and falls (fleeing, defeat, dungeon depth, vampiric hunger).
- Stress relief beyond sleep (temple Day of Respite, herbal baths) — mirror the companion tools for the player.
- Dream weighting from player stress (currently impossible: sleep clears the meter before the roll).
- Companion refusal dialogue does not have per-girl lines yet (template override + generic pool only).
