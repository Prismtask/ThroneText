# Ally Potential & Awakening — Design Proposal

**Status:** ✅ Design approved (2026-10-05) · **Parts A (Growth) + B (Race passives) + C (Awakening) implemented 2026-10-05**
**Date:** 2026-10-05 · **Patch context:** v0.1.8.0
**Related docs:** `docs/barracks_skills_audit.md` · `docs/mastery_extension_design.md` · `docs/barracks_tier_5_6_proposal.md` · `unrelated for coding/ALLY_TIER_LISTS.md` · `docs/monster_girls_skills_wiki.md` · `docs/dispatch_system_design.md`
**Scope:** three companion systems for underutilized monster girls — **(A) late-bloomer Growth**, **(B) race passive completion**, **(C) Awakening**.

**Review decisions (2026-10-05):** ALL LOCKED — TARGET_SUM 42 · distribution = auto-highest → **player-chosen (changed 2026-11-06)** · race passives finalized (Gnome/Clockwork approved) · 5 sigils/save · **1 Sigil = full awakening (both skills)** · mastery carry-over · per-girl dialogue + names + special scene · affection gate 150 · secondary skills approved. Full log in Appendix B.

---

## 0. Context — the stat gap is structural

### 0.1 History (verified via git)

| Commit | Formula | Effect |
|---|---|---|
| `a84630b` (original ally system) | `0.75 × base`, **no level scaling** | Early-caught girls (manual +1/level) dominated; late captures were blank slates |
| `82ddb66` | `0.8 × base + 0.15/attr/level` | The "ramp up later allies" fix |
| `cabf1f5` (current) | `0.85 × base + 0.18/attr/level` | Current balance — now inverted: late captures dominate |

### 0.2 Current numbers

- Capture attributes: `base × 0.85 + (level − 1) × 0.18` per attribute (`combat/ally.py::compute_girl_attributes`).
- Level-ups (party + dispatch): `+1 to one chosen attribute` (`leveling.py::gain_exp_ally`).
- Base sums (`race mods + personal mods`) span **10 (Goblin Girl) → 55 (Seraph Ascendant)** and correlate with capture level.

| Girl (capture Lv) | At capture | By Lv 50 (fully leveled) |
|---|---:|---:|
| Goblin Girl (Lv 2) | 10 pts | 10 + 48 manual = **58** |
| Lich Queen (Lv 35) | 69 pts | 69 + 15 manual = **84** |
| Arachne Brood Queen (Lv 38) | 77 pts | 77 + 12 manual = **89** |

- **The ramp asymmetry is small:** auto-scaling is `0.18 × 6 = 1.08` pts/level vs `1.0` manual ≈ **4 pts** at Lv 50.
- **The base × 0.85 gap is the problem:** a permanent **~26–31 point** deficit for low-base girls. Plus kit quality (C/B vs S), HP (CON base), `Learning//2` damage, and the dead-weight window (Lv 2→50 ≈ 463k XP vs 228k for a Lv 38→50 capture).

### 0.3 Design target

> **Acquisition = instant power. Investment = the highest ceiling.**
> Investment buys *parity*, not superiority: a fully-raised Goblin should end ~equal in stats to a same-level Lich — with TARGET_SUM = 42 she ends exactly even (84 vs 84) — with kits remaining the differentiator. "Mechanics over numbers" (barracks audit §3).

---

## Part A — Late-bloomer Growth

### A.1 Formula

```
base_sum = race mods + personal mods (compute_enemy_attributes)
growth   = clamp((TARGET_SUM − base_sum) × 0.85 / 50, 0.0, 0.6)      # points per level
TARGET_SUM = 42  (approved 2026-10-05 — exact Lich Queen parity)
```

- Low-base girls grow faster per level; top-base girls get 0.
- Optional per-girl YAML override (`growth: 0.4`) for hand-tuning, with the derived value as default.
- No data entry needed for the initial 56 — the formula covers everyone.

### A.2 Credit & application rules

- **Total credit at level L** = `floor((L − 1) × growth)`.
- **Applied incrementally on each level-up:** `delta = floor((L − 1) × growth) − growth_applied`; grant `delta` points; update the `growth_applied` counter (persisted on the ally/house record). Idempotent, dismiss/re-recruit safe.
  - This grants minor retro credit for pre-recruit levels (≤ ~2–3 pts for the girls it affects, all early captures). Acceptable simplification; the exact investment-only variant is to store `growth_from_level` at first recruit and subtract `floor((growth_from_level − 1) × growth)` — not recommended for v1 (extra field, negligible difference).
- **Distribution (changed 2026-11-06):** each granted point is **chosen by the player through the level-up picker** — a "Late Bloomer bonus" prompt appears right after the manual +1, so the point is an extra level-up choice rather than an automatic highest-stat bump. If the picker is unavailable, the point falls back to the girl's highest current attribute (tie-break: `ATTRIBUTES` order).
- **Display:** one line in the level-up results — `[Late Bloomer] {name}: +1 STR (growth)`.
- **Dispatch:** works automatically (dispatch collect runs `gain_exp_ally`) — benched girls grow while away.
- **Exclusions:** heroines (own formula: `base + (player_level−1) × 0.22`, cap 99, no ×0.85) — untouched.
- **Old saves:** no retroactive grant on patch; affected girls start growing from their current level. (The target audience — underutilized low-level girls — loses nothing meaningful.)

### A.3 Parity examples (TARGET_SUM = 42)

| | Attributes at capture | Manual | Growth | Lv 50 total |
|---|---:|---:|---:|---:|
| Goblin Girl | 10 | +48 | +26 | **84** |
| Lich Queen | 69 | +15 | +0 | **84** |
| Brood Queen | 77 | +12 | +0 | **89** |

With `TARGET_SUM = 46`: Goblin growth caps at 0.6 → +29 → **87**, essentially Brood parity.

### A.4 Display bands

| Band | Rate | Intent |
|---|---|---|
| **High** | ≥ 0.35 | "Late bloomer" label in lounge/wiki — the Goblin/Harpy/Alraune group |
| **Medium** | 0.15–0.34 | Mid girls — grows into her kit |
| **Low** | 0.01–0.14 | Small top-up |
| **—** | 0 / no point by Lv 50 | Top-base girls (Lich, Brood, Seraph, …) · base-41 girls at 0.017 round to 0 |

Show on the lounge girl page + skill book ("Growth: High") and in the wiki (new column).

### A.5 Implementation checklist (Part A)

- [x] `combat/ally.py`: `get_growth_rate(ally_or_girl)` (template lookup + derived formula + YAML override), `get_growth_label()`, `apply_ally_growth(ally)` helper.
- [x] Persistence: `growth_applied` in `_ally_to_house_record`, `create_ally_from_girl` (both paths), `store_captured_girl`, `character.py::ensure_player_fields`; dispatch write-back verified (`ensure_girl_combat_fields`).
- [x] `leveling.py::gain_exp_ally`: `apply_ally_growth` runs after the manual `+1` (inside the level-up loop, before HP recalculation).
- [x] Level-up UI: growth line appended to the `milestones` list so both the GUI dialog and terminal path show it.
- [x] Display: lounge girl page (`Growth: High (late bloomer)`), skill book (`[Growth] …`), wiki generator + regenerated wiki (Growth column).
- [x] Tests: `tests/_temp_growth_check.py` — 10 sections (formula, parity, delta math, idempotency, highest-stat distribution, tie-break, house round-trip, exclusions, legacy save, `gain_exp_ally` integration). All pass; rename smoke test still passes.

*Implemented 2026-10-05. Parts B & C pending.*

---

## Part B — Race passive completion (approved 2026-10-05)

### B.1 Final race passive kits

Every race except Human gets its **full fitting passive** — missing halves implemented, with the balance adjustments from review. Descriptions must match effects exactly (`resources/skill_book/skill_list.yaml::race_passives`).

| Race | Final passive | Change |
|---|---|---|
| Human | +1 to all attributes | Approved (baseline exception) |
| Beast | **+2 STR, +3 DEX** | Approved |
| Goblin | +2 DEX, **+20% dodge** | Approved |
| Orc | **+2 STR, +10% stun chance on basic attacks** | Approved — stun added on top of +2 STR |
| Undead | **Regenerate 5% max HP/turn; allied heals blocked (self-heals allowed)** | Approved — remove +2 WIS |
| Dragonkin | +2 STR, **+8% elemental damage** | Adjusted (8%) |
| Demon | **+15% fire & dark damage** | Approved — remove +2 CHA |
| Giant | +3 STR, **−10% damage taken** | Adjusted — add DR |
| Shadow | +2 DEX, **15% evade** | Approved |
| Elemental | **+10% elemental damage, +10% elemental resistance (all)** | Approved — remove +2 CON |
| Lizardfolk | **+2 STR, +1 CON** | Approved |
| Abomination | **+1 STR / +1 DEX / +1 WIS**, −10% damage taken | Approved — keep DR alongside the spread |
| Construct | +3 CON, **poison & bleed immunity** | Approved |
| Vampire | 25% lifesteal (×2 vs bleeding), **+1 CHA** | Approved |
| Fey | Regen 10% max HP/turn | Approved |
| Gnome | **+2 Learning, +15% thunder damage** | Approved |
| Angel | +1 WIS, +1 CHA, **+5% damage vs Demons** | Adjusted — add vs-Demon |
| Clockwork | **+2 CON, +10% damage vs shocked enemies** | Approved |

### B.2 Implementation notes

- **Per-stat values:** Beast (+2/+3) and Lizardfolk (+2/+1) need the small effect-format extension — `stat: multi` with per-stat values — read alongside the existing `stat` / `stat: all` forms in `get_effective_attribute()`. Abomination's +1/+1/+1 uses the existing `stat: all` form.
- **Orc — stun on basic attack (in addition to +2 STR):** add a 10% stun roll to the basic-attack resolution paths (player + ally) gated on the race passive; verify multi-hit/basic-attack rider interactions. ⚠ small.
- **Dodge/evade:** add a race-passive `evasion` check in `combat/stats.py::get_dodge_chance()` (mirrors stat passives). ✅ small.
- **Construct immunity:** check at all poison/bleed application sites (`combat/status_effects.py` + direct DoT injections in superboss modules) and log an "immune" line. ⚠ verify every injection site.
- **Undead (approved):** 5% max-HP regen at end of round (extend the Fey hook in `combat_engine.py`); **allied heals blocked, self-heals allowed** — audit heal destinations (party heals, potions/items) to block external healing, and confirm own skills / lifesteal-style effects still function. ⚠
- **Elemental dmg/res (Dragonkin 8%, Demon, Elemental, Gnome thunder, Angel vs-Demon):** apply via `compute_ally_elemental` / combat-start profile edit for elemental %, and a `bonus_vs_race` passive hook for Angel (Snicker-Snack-style bonus precedent). ⚠
- **Clockwork (approved):** "+10% damage vs shocked enemies" needs a shocked-status check in the damage calc (fallback if the hook proves messy: "+15% shock damage"). ⚠
- **Existing saves:** passives key off `ally["race"]`, so all current allies pick up the changes automatically. Player characters are unaffected (the shared combat paths scope race passives to allies — `is_ally` gates).

### B.3 Implementation status (2026-10-05)

- [x] All 18 race kits rewritten in `skill_list.yaml` (multi-effect format; descriptions now match effects).
- [x] `combat/ally_skills.py`: `get_race_passive_effects` (multi-aware) + typed helpers — `get_race_lifesteal`, `get_race_damage_reduction`, `get_race_regen`, `get_race_evasion`, `get_race_damage_multiplier`, `has_status_immunity`, `is_heal_blocked`, `maybe_stun_on_basic`.
- [x] Stat reads: `get_ally_effective_attribute` supports `stat: multi`; all three Vampire lifesteal sites use the helper (bleed-feast doubling kept).
- [x] Combat hooks: Goblin/Shadow evasion (`get_dodge_chance`), Orc stun (ally basic attack, in addition to +2 STR), Giant/Abomination DR (`enemy_ai` — shared by normal + superboss attacks), Fey/Undead regen (`combat_engine` end-of-round), Construct poison/bleed immunity (`apply_poison`/`apply_bleed` return `"immune"`), Undead heal block (`apply_healing(source=...)`; ally party/single heals + Cleric heals show the rejection line; self-heals allowed), elemental dmg/res (`compute_ally_elemental`), Angel/Clockwork damage bonuses (ally basic attacks + `_calc_dmg`).
- [x] Tests: `tests/_temp_race_passives_check.py` (9 sections) passes. Regressions also pass: growth check, status-res diag, bleed unify, vampire bleed drain, rename smoke.

---

## Part C — Awakening

### C.1 Concept & guardrails

- One-time, permanent awakening of a girl's **entire innate kit — both skills upgrade together** — at a bond milestone.
- **Sidegrade rule:** each awakened skill adds a *capability* (AoE, CC, reflection, cooldown, guardian save) — never raw power inflation on a top kit.
- **Max 5 awakened girls per save** (scarcity caps the ceiling, regardless of roster size).
- **Top 6 S-kits excluded:** Grave Queen, Dragon Goddess, Lich Queen, Cosmic Slime Empress, Infernal Bride, Seraph Ascendant.
- No stat changes (that's the Growth system's job), no passive/wedding-accessory changes.

### C.2 Currency — Awakening Sigils

| Source | Reward | Count |
|---|---|---:|
| **First superboss ever defeated** (milestone, one-time message) | 1 × Sigil | 1 |
| **8 global-pool superbosses** (20th-floor rotation) | 1 × Sigil Shard each, first kill | 8 |
| **4 Wonderland superbosses** (Floors 10/20/30/40) | 1 × Sigil Shard each, first kill | 4 |
| **Mary Sue** (Floor 50) | 1 × Sigil — "the author grants a rewrite" | 1 |
| **Arcane Tower — Awakening Research** | 4 Shards + 25,000g → 1 Sigil (craftable 3× of the 12 shards) | 3 |

**Net: 5 Sigils per save** — **1 Sigil = full awakening of one girl** (both skills + name change + special scene) → up to 5 of the 12 candidates per save. Pandemonium-only specialists (Chrysalis, White Knight) drop no shards in wave 1 (see Appendix B).

- **Grant guards:** per-boss credited list stored on the player (`awakening_shard_sources`), mirroring `wl_floor_looted_*` idempotency.
- **Migration:** on first load after the patch, scan `defeated_superbosses` + Wonderland flags and retro-grant the milestone Sigil, shards, and Mary Sue Sigil so existing saves are not punished.

### C.3 Prerequisites, location, ceremony

**Per girl — all required:**

| Requirement | Value | Why |
|---|---|---|
| Level | **40+** | Mirrors the Tier V gate |
| Level cap | **≥ 40** | 3rd ascension done — stones invested, not just carried |
| Affection | **≥ 150** | Past engagement (100), short of the wedding gift (200) — a bond, not a purchase |
| Currency | 1 Awakening Sigil, not already awakened | The scarce choice |

- **Location:** House Lounge → new **"Awaken"** action (visible only when eligible). Reuses the ascension ceremony pattern.
- **Dialogue (per girl, approved):** `awakening_pre_ceremony` / `awakening_post_ceremony`, a one-time **`awakening_scene`** (multi-beat special scene), and a replaced daily-talk set (`awakened_talk_low/mid/high/max`) that overrides `house_talk_*` once the girl is awakened — written for the 12 wave-1 girls. Only reachable on high-affection favorites, which justifies the bespoke writing.
- **Name change (approved):** the girl's *displayed* name changes on awakening (e.g., Goblin Girl → Goblin Deadeye).
  - **Do not rename `name`** — per the ally-nickname conventions, the species name is the identity used by `_girl_unique_id` (daily talk/gift tracking), recruit/dismiss/house matching, and save compat.
  - New field `awakened_name`; `utils.display_name()` resolves **nickname → awakened_name → name**; `display_name_with_species()` renders "Nick (Awakened Name)".
  - Awakened names (approved): Goblin Deadeye · Harpy Stormcaller · Moth Girl Moonweaver · Mirror Slime · Automata Prime · Centaur Warlord · Gorgon Basilisk · Grand Mimic · Gear Artificer · Nightweaver · Demon Overseer · Dullahan Sentinel.
- **Persisted fields:** `awakened: true` (ceremony/name state) + `awakened_skills` (both upgraded ids, recorded at the ceremony); swap handling at `initialize_ally_skills` / `create_ally_from_girl` (precedent: Vorpal skill swap for Alice).
- **Skill swap:** the mapping lives in `innate_skills.yaml` under an `awakenings:` block; upgraded defs replace the base ids in `ally["innate_skills"]`.

**One skill or both? (resolved 2026-10-05)** — **1 Sigil awakens the girl fully: both innate skills upgrade together**, followed by the name change and the one-time special scene. The earlier 1-Sigil-per-skill idea was dropped: it split a single identity moment, and the name change only makes sense at full awakening. Consequences:
- Wave 1 must ship **both** upgrade sets (12 primary + 12 secondary = 24 skill defs) — secondary drafts are in C.4.
- 5 Sigils/save = up to **5 fully awakened girls** of the 12 candidates.
- If playtest wants more awakenings per save, the clean extension is extra shard sources (e.g., Pandemonium specialists) — held as an open question, not part of wave 1.

Example YAML shape:

```yaml
# innate_skills.yaml
awakenings:
  goblin_girl:
    replaces: goblin_dart
    grants: lucky_volley
  harpy_scout:
    replaces: harpy_cry
    grants: tempest_screech
  # ...

innate_skill_defs:
  lucky_volley:
    name: Lucky Volley
    description: A fistful of lucky darts peppers every enemy with poison.
    category: offensive
    cooldown: 3
    target: enemies
    power_type: dex
    base_power: 8
    poison_damage: 2
    poison_duration: 3
    elemental: water
    awakened_from: goblin_dart
```

### C.4 Awakened skills — wave 1 (12 girls)

**Rescue line (B/C kits — the underutilized set):**

| Girl | Base skill (CD, target) | → Awakened skill | What changes | Engine |
|---|---|---|---|---|
| Goblin Girl | Goblin Dart (2, enemy, DEX 6, poison) | **Lucky Volley** (3, all enemies, DEX 8, poison per enemy) | First AoE + mass poison — a real role | ✅ |
| Harpy Scout | Harpy Cry (3, enemies, CHA 8) | **Tempest Screech** (4, enemies, **DEX** 10, push_initiative) | Scaling fixed (CHA→DEX) + tempo control | ✅ |
| Moth Girl | Dust Cloud (3, enemies, blind 50%/2) | **Moonveil Dust** (4, enemies, blind 75%/3 + Marked +10%/3) | Blind finally pays off for the team | ⚠ AoE mark |
| Slime Girl | Slime Absorption (4, self, absorb 40%/2) | **Adaptive Membrane** (5, self, absorb 40% + reflect 30%/2) | Tank button becomes punishment | ⚠ combine effects |
| Automata Doll | Emergency Repair (4, self, regen 20%×2) | **Reboot Protocol** (5, self, 3 turns: first lethal blow → revive at 30%, once) | Self-repair bot that means it | ⚠ death-ward variant |

**Potential line (high-level, strong-but-not-top kits — role refinements):**

| Girl | Base skill (CD, target) | → Awakened skill | What changes | Engine |
|---|---|---|---|---|
| Centaur Champion | Stampede (4, enemies, STR 11) | **Rolling Thunder** (5, enemies, STR 12 + **Expose −2 armor/3**) | New AoE armor-shred niche | ⚠ |
| Gorgon Petrifier | Petrifying Gaze (4, enemy, stun 2) | **Medusa's Verdict** (5, enemy, stun 2 + **35% entomb 2**) | CC queen, RNG-gated (no guaranteed lockdown) | ⚠ |
| Mimic Girl | Mimic Form (4, self, DR 30%/2) | **Perfect Mimicry** (5, self: adapt last element — **+50% res, +25% dmg** of it, 3) | Element adaptation; punishes elemental bosses | 🔧 last-element tracking |
| Gear Maiden | Overclock (4, ally, +40% next action) | **System Overdrive** (5, ally, +40% + **−1 CD on all their skills**) | Premier cooldown support | ✅/⚠ (Astral Haste precedent) |
| Dusk Weaver | Veil of Dusk (3, ally, evasion 35%/2) | **Duskfall Veil** (4, ally, evasion 35%/3 + **dodge counter 50%**) | Evasion build enabler | 🔧 ally counter |
| Demon Whip Master | Dominating Presence (4, enemies, −2 STR/3) | **Absolute Dominion** (5, enemies, −2 STR + **Fear 30%/2**) | Domination that dominates | ⚠ |
| Dullahan Knight | Spectral Guard (3, ally, DR 35%/2) | **Death's Vigil** (4, ally, DR 35% + **death ward 3 turns**) | Targeted mini-Undying Vow — guardian identity | ⚠ |

*Legend: ✅ primitives ready · ⚠ small engine add · 🔧 new mechanic (moderate).*

**Secondary skills (approved — awakening upgrades both skills, so these ship with wave 1):**

| Girl | Secondary base skill (CD, target) | → Awakened | Change | Engine |
|---|---|---|---|---|
| Goblin Girl | Goblin Evasion (3, self, dodge 60%/2) | **Fortune's Veil** (4, self + allies) | Self dodge 60%/2 + party +15% dodge/2 | ⚠ party evasion |
| Harpy Scout | Harpy Swoop (2, enemy, DEX 10) | **Skydive Strike** (3, enemy) | DEX 12 + 25% stun (dive knockdown) | ✅ |
| Moth Girl | Flutter Strike (2, enemy, DEX 8) | **Moonlit Flurry** (3, enemy) | 2×7 DEX hits + Blind 30%/2 | ✅ |
| Slime Girl | Acidic Blob (2, enemy, CON 8) | **Corrosive Deluge** (3, enemy) | CON 10 + poison 3×3 + Expose (−1 armor) | ✅ |
| Automata Doll | Clockwork Blade (2, enemy, DEX 12, shock 4×3) | **Overclocked Edge** (3, enemy) | 2×9 DEX hits, shock 4×3 on each | ✅ |
| Centaur Champion | Champion's Charge (3, enemy, STR 14, ignore armor) | **Lance of the Gale** (4, enemy) | STR 15, ignore armor, +15% crit | ✅ |
| Gorgon Petrifier | Serpent Fang (2, enemy, DEX 10, poison 4×4) | **Basilisk Fang** (3, enemy) | DEX 11, poison 6×4, applies Slow | ✅ |
| Mimic Girl | Surprise Strike (2, enemy, STR 11, guaranteed crit) | **Perfect Ambush** (3, enemy) | STR 12, guaranteed crit; +30% dmg vs targets above 80% HP | ⚠ high-HP bonus |
| Gear Maiden | Cog Storm (3, enemy, LER 13, 25% stun) | **Cog Blizzard** (4, all enemies) | LER 10 AoE + 15% stun each | ✅ |
| Dusk Weaver | Twilight Lash (2, enemy, DEX 12, bleed 3×3) | **Eclipse Lash** (3, enemy) | DEX 12, bleed 5×4; +25% dmg vs bleeding targets | ⚠ bleeding bonus |
| Demon Whip Master | Whip Lash (2, enemy, DEX 10, weaken) | **Cruel Crack** (3, enemy) | DEX 11 + Weaken + bleed 4×3 | ✅ |
| Dullahan Knight | Headless Charge (3, enemy, STR 13, ignore armor) | **Headless Pursuit** (4, enemy) | STR 13, ignore armor + Fear 30%/2 | ⚠ |

**Mastery carry-over (approved):** when a base skill is replaced, transfer `skill_mastery[base]` and any `skill_cooldowns[base]` to the awakened id — investment should not be punished by the upgrade.

### C.5 Why this doesn't create a new scaling problem

- 5 Sigils/save, each behind Lv40 + cap40 + affection150 → bounded awakened power per save (max 5 fully awakened girls).
- Every upgrade adds a capability; none boosts an already-top kit's raw numbers.
- Rescue upgrades lift the floor; potential upgrades refine roles. The top 6 S-kits never enter the pool.
- Full-kit awakening (both skills) is the single identity moment — name change + special scene trigger here, not at a half-upgrade.

### C.6 Implementation checklist (Part C)

- [x] `resources/skill_book/innate_skills.yaml`: **24 awakened skill defs** (12 primary + 12 secondary) + `awakenings:` map; `get_innate_skill_def` finds them (same lookup path).
- [x] `combat/ally_skills.py`: swap-aware `initialize_ally_skills` (awakened flag), mastery/cooldown carry-over (`apply_awakening_skills`).
- [x] `facilities/house.py`: lounge "Awaken" action + eligibility display + per-girl ceremony dialogue + `awakening_scene` + `awakened_talk_*` override + consume Sigil + persist `awakened` / `awakened_skills` / `awakened_name`.
- [x] `resources/enemies/enemies_data/monster_girls.yaml`: per-girl `awakened_name` + `awakening_pre_ceremony` / `awakening_scene` / `awakening_post_ceremony` + 4 awakened talk lines × 12 girls.
- [x] `utils.py`: `display_name` resolution nickname → `awakened_name` → name; `display_name_with_species` update; house matching / `_girl_unique_id` still key off `name` (unchanged).
- [x] `facilities/arcane_tower.py`: "Awakening Research" forge (4 shards + 25,000g → 1 Sigil) + menu/dialogue.
- [x] `dungeon.py` / superboss paths: shard grants (global pool + 4 Wonderland floors), Mary Sue Sigil, first-superboss milestone; idempotent guards + migration scan (`character.py::_migrate_awakening_rewards`).
- [x] `character.py`: `ensure_player_fields()` — `awakening_sigils`, `awakening_shards`, `awakening_shard_sources`, `awakening_intro_granted` + awakened-skill reconciliation for allies/house girls.
- [x] GUI parity: house lounge + arcane tower run through the shared terminal layer (both modes); all lines use `term.print` / `_tprint`.
- [x] Wiki generator + changelog (v0.1.8.0) + README section.
- [x] Tests: forge math, prereq gating, swap + mastery carry-over, idempotent grants, migration from a superboss-cleared save (`tests/_temp_awakening_check.py`).

### C.7 Implementation notes (2026-10-05)

- **One extra shard source:** the global pool currently holds **9** tiered superbosses (tiers 0–8), so a fully-cleared save can collect 9 pool shards + 4 Wonderland shards = 13. The forge still consumes 4 per Sigil → **max 3 forged Sigils**, so the 5-Sigils-per-save ceiling is unchanged.
- **Engine additions the awakened kits required:** `damage_absorption` is now a real buff (was defined but inert — Slime Absorption now works); the `multi` effect handler dispatches absorb/reflect/DR/death-ward/evasion/blind/marked/fear/stun/entomb/stat-debuff/cd-refund/power-buff subs; death wards accept `hp_pct` (Reboot Protocol revives at 30%); `marked` works AoE; ally skills support `expose_armor`, `blind_value`, `apply_fear`, `bonus_vs_high_hp`, `bonus_vs_bleeding`; `enemy_ai` tracks `_last_element_hit` and honors `dodge_counter` (Duskfall Veil) and `damage_absorption` conversion.
- **Scope note:** race passives remain ally-only (`is_ally` gates), consistent with Part B.

---

## Appendix A — Full growth table (derived, TARGET_SUM = 42)

`+Pts @50` = `floor(49 × growth)` — total growth points if raised from her native level to Lv 50. Band "—" = no point by Lv 50.

| Girl | Lv | Base sum | Growth | +Pts @50 | Band |
|---|---:|---:|---:|---:|---|
| Goblin Girl | 2 | 10 | 0.544 | +26 | High |
| Harpy Scout | 5 | 13 | 0.493 | +24 | High |
| Alraune Fledger | 7 | 18 | 0.408 | +19 | High |
| Centaur Scout | 11 | 19 | 0.391 | +19 | High |
| Ghost Maid | 10 | 19 | 0.391 | +19 | High |
| Kobold Tinkerer | 8 | 19 | 0.391 | +19 | High |
| Dryad Protector | 9 | 20 | 0.374 | +18 | High |
| Mimic Girl | 14 | 22 | 0.340 | +16 | Medium |
| Holstaur Brawler | 15 | 23 | 0.323 | +15 | Medium |
| Lamia Constrictor | 13 | 23 | 0.323 | +15 | Medium |
| Moth Girl Flutterer | 12 | 23 | 0.323 | +15 | Medium |
| Umbral Weaver | 14 | 23 | 0.323 | +15 | Medium |
| Banshee Wailer | 18 | 24 | 0.306 | +14 | Medium |
| Lizard Queen | 14 | 24 | 0.306 | +14 | Medium |
| Slime Girl | 12 | 24 | 0.306 | +14 | Medium |
| Gargoyle Watcher | 16 | 25 | 0.289 | +14 | Medium |
| Mummy Princess | 19 | 25 | 0.289 | +14 | Medium |
| Winter Fairy | 14 | 25 | 0.289 | +14 | Medium |
| Amazon Warrior | 18 | 26 | 0.272 | +13 | Medium |
| Neko Ninja | 18 | 26 | 0.272 | +13 | Medium |
| Arachne Weaver | 19 | 27 | 0.255 | +12 | Medium |
| Dullahan Knight | 22 | 28 | 0.238 | +11 | Medium |
| Vampire Seductress | 16 | 29 | 0.221 | +10 | Medium |
| Yuki-onna | 17 | 29 | 0.221 | +10 | Medium |
| Kitsune Miko | 22 | 30 | 0.204 | +9 | Medium |
| Gear Maiden | 23 | 31 | 0.187 | +9 | Medium |
| Oni Bruiser | 20 | 31 | 0.187 | +9 | Medium |
| War Sister | 25 | 32 | 0.170 | +8 | Medium |
| Succubus Seductress | 21 | 32 | 0.170 | +8 | Medium |
| Salamander Dancer | 21 | 33 | 0.153 | +7 | Medium |
| Centaur Champion | 26 | 34 | 0.136 | +6 | Low |
| Scylla Wrecker | 26 | 34 | 0.136 | +6 | Low |
| Siren Empress | 23 | 34 | 0.136 | +6 | Low |
| Automata Doll | 29 | 35 | 0.119 | +5 | Low |
| Demon Whip Master | 24 | 35 | 0.119 | +5 | Low |
| Minotaur Gladiator | 24 | 35 | 0.119 | +5 | Low |
| Crimson Countess | 24 | 37 | 0.085 | +4 | Low |
| Infernal Empress | 26 | 37 | 0.085 | +4 | Low |
| Dusk Weaver | 27 | 37 | 0.085 | +4 | Low |
| Gorgon Petrifier | 28 | 38 | 0.068 | +3 | Low |
| Ninetales Fox | 30 | 38 | 0.068 | +3 | Low |
| Vampire Matriarch | 25 | 38 | 0.068 | +3 | Low |
| Maiden of Stone | 32 | 41 | 0.017 | +0 | — |
| Lich Queen Avatar | 35 | 41 | 0.017 | +0 | — |
| Mermaid Siren Queen | 31 | 42 | 0 | +0 | — |
| Sphinx Riddler | 34 | 42 | 0 | +0 | — |
| Draconic Valkyrie | 33 | 44 | 0 | +0 | — |
| Valkyrie Commander | 36 | 44 | 0 | +0 | — |
| Arachne Brood Queen | 38 | 46 | 0 | +0 | — |
| Dragon Goddess Avatar | 37 | 48 | 0 | +0 | — |
| Flame Heart | 39 | 48 | 0 | +0 | — |
| Star Court Dancer | 44 | 50 | 0 | +0 | — |
| Grave Queen | 50 | 50 | 0 | +0 | — |
| Cosmic Slime Empress | 40 | 52 | 0 | +0 | — |
| Infernal Bride | 47 | 53 | 0 | +0 | — |
| Seraph Ascendant | 42 | 55 | 0 | +0 | — |

---

## Appendix B — Review log

### Decisions (2026-10-05 review)

1. **Growth target: `TARGET_SUM = 42`** — exact Lich parity (Goblin 84 = 84).
2. **Growth distribution: auto-highest attribute** (tie-break `ATTRIBUTES` order) — monitor one-stat spikes in playtest.
3. **Growth bands as proposed** (High/Medium/Low; "—" when no point by Lv 50).
4. **Race passives finalized** (full table in Part B): Goblin dodge · Beast +2 STR/+3 DEX · Orc +2 STR + stun-on-basic · Undead 5% regen + allied-heal block (self-heals allowed) · Dragonkin +8% elemental · Demon no CHA/+15% fire&dark · Giant +3 STR/−10% taken · Shadow evade · Elemental no CON/+10% dmg&res · Lizardfolk +2/+1 · Abomination +1 STR/DEX/WIS + DR · Construct immunity · Vampire +1 CHA · Fey approved · Gnome +2 LER/+15% thunder · Angel +5% vs Demons · Clockwork +2 CON/+10% vs shocked.
5. **Sigils: 5 per save (confirmed)** — **1 Sigil = full awakening** (both skills + name + scene).
6. **Mastery carry-over: yes.**
7. **Per-girl dialogue + awakened names + special scene** — `awakened_name` display-only; 12 names agreed; `awakening_scene` one-time.
8. **Wave 2 candidates held.**
9. **One skill vs both — resolved: both at once** (dropped the 1-Sigil-per-skill split).
10. **Affection gate: 150 confirmed.**
11. **Gnome (+2 Learning/+15% thunder) and Clockwork (+2 CON/+10% vs shocked) approved as proposed.**
12. **Abomination: keep −10% damage taken alongside +1 STR/DEX/WIS.**
13. **Secondary skill drafts approved** — ship together with the primaries.
14. **Undead: self-heals remain allowed** (only allied/external healing is blocked).
15. **Orc: stun is in addition to +2 STR.**

### Remaining open questions

*None — all review items resolved (2026-10-05). Post-playtest tuning knobs only: growth TARGET_SUM, growth distribution if specialists spike, and (only if desired) extra shard sources from Pandemonium specialists (16 shards → 7 sigils).*

### Review log

- **2026-10-05 — Part A (Growth) implemented:** parity tweak (`ALLY_LEVEL_STAT_BONUS = 1/6`) + growth system (`growth_applied`, highest-stat distribution, level-up lines, lounge/skill-book/wiki display). `tests/_temp_growth_check.py` passes (10 sections); wiki regenerated. Parts B & C pending.
- **2026-10-05 — Part B (Race passives) implemented:** all 18 kits finalized (multi-effect YAML), hooks wired through stats/dodge/elemental/DR/regen/lifesteal/immunity/heal-block/stun/damage bonuses. `tests/_temp_race_passives_check.py` passes (9 sections); regressions green. Part C pending.
- **2026-10-05 — Part C (Awakening) implemented:** 24 awakened skills + `awakenings:` map; swap-aware init + mastery carry-over; Lounge Awaken ceremony with per-girl dialogue/names/scene; Sigil/Shard economy (first-superboss, Wonderland 10–40, Mary Sue, Arcane Tower forge) with migration for old saves; engine support (absorb/reflect/adapt/counter/expose/fear/blind/entomb/CD-refund). Tests: `tests/_temp_awakening_check.py`. See C.7 for implementation notes.
- *(add decisions as they are made — matches the barracks proposal workflow)*
