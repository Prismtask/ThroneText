# Barracks Skills Audit

**Date:** 2026-10-01 · **Patch version:** v0.1.8.0
**Scope:** `facilities/barracks.py`, `combat/ally_skills.py`, `resources/skill_book/skill_list.yaml` (`learnable_skills`)
**Related docs:** `docs/monster_girls_skills_wiki.md`, `docs/enemy_audit_report.md`
**Decisions:** tier gates rescaled (Option A, §5.1); level-cap gates on tiers III/IV (Option B, §5.1); **Tiers V–VI added (Option C, §5.3)**; house-stored girls intentionally cannot learn (only party members, §4 #10)

---

## 1. As-built summary

The Barracks teaches **47 learnable skills** for free (no gold), **1 in training at a time**, with a **maximum of 3 learned skills per ally** (the replacement flow exists and warns that the replaced skill's mastery is lost).

| Tier | Label | Required Ally Level | Required Level Cap | EXP to Learn | Offensive | Defensive | Support |
|------|-------|--------------------:|-------------------:|-------------:|----------:|----------:|--------:|
| I | Novice | 1 | — | 300 | 3 | 2 | 3 |
| II | Adept | 8 | — | 800 | 3 | 2 | 3 |
| III | Veteran | 16 | 20 | 2000 | 3 | **1** | 3 |
| IV | Master | 25 | 30 | 5000 | 3 | 2 | 3 |
| V | Elite | 35 | 40 | 10000 | 3 | 2 | 3 |
| VI | Legend | 45 | 50 | 20000 | 2 | 3 | 3 |

*(I–IV rescaled + cap-gated in v0.1.8.0; V–VI added in v0.1.8.0 per the approved `docs/barracks_tier_5_6_proposal.md`.)*

- **Learning EXP = combat XP.** `gain_exp_ally()` forwards the same amount to `gain_skill_learning_exp()` before level-cap checks, so learning always progresses even when an ally is stuck at their cap. Enemies pay `level × 8/10/12` XP each; a Tier IV skill (5000) is roughly 15–30 kills at Lv 20–30, and a Tier VI skill (20,000) is a multi-run project at Lv 40+.
- **Mastery** (global thresholds 10/25/50/90/150 uses, 5 levels — displayed ★ / ★★ / ★★★ / ✦ / ✦✦): ★ +15% power · ★★ −1 cooldown · ★★★ +30% power + bonus effect + ×1.5 status · ✦ +45% power, +1-turn effect durations, ×1.75 status · ✦✦ +60% power, −2 total cooldown, ×2.0 status.
- **Damage formula:** `power = (base_power + stat + Learning//2) × mastery_mult`, then `dmg = power + STR milestone bonus − target armor`, then elemental multipliers. The flat `stat + Learning//2` term dominates at higher levels.
- **Who can learn:** only recruited party allies (`get_current_house_allies()` returns `player["allies"]`). Combat XP flows to every living party/bench ally; girls stored in the house earn nothing, and since recruiting removes them from the house, the barracks' "house copy" update path is effectively unreachable.
- **Allies also have:** 2 innate skills each + 1 race passive, so the learnable pool is the customization layer on top of unique kits.

## 2. Progression context — the ladder vs. the campaign

- Allies start at **level cap 10**; each ascension adds +10 (Ascension Stone I unlocks at floor 10 for 600g; see `facilities/temple.py`, `facilities/house.py`).
- XP to level is `60·L^1.5 + 40·L`; L10→15 costs ≈15k, L20→25 ≈27k.
- **Before the rescale** (gates 1/5/10/15), Tier IV was reachable around floors 10–20 — early-to-mid content. The original gates mirrored the base game's player class-skill unlocks (3–15), which the campaign has long outgrown (player cap 60, enemy level 57, 40–60+ floor dungeons across ~5 biomes, Wonderland's 48 floors).
- **After the v0.1.8.0 rescale** (gates 1/8/16/25):
  - Tier II at Lv8 — reachable at the default cap 10.
  - Tier III at Lv16 — requires the first ascension (cap 20, Stone I from floor 10).
  - Tier IV at Lv25 — requires the cap-30 ascension (3×Stone I + 2×Stone II + 1×Stone III, unlocked from floor 20+).
- **Captures are now gated by both level and cap:** captured girls arrive at their YAML level (monster girls span Lv 2–40) with **cap 10**, but tiers III/IV now require `level_cap ≥ 20/30` (`required_cap` in YAML, enforced by `meets_skill_requirements()`). A Lv 25+ capture must be ascended at the House Lounge before she can learn Tier IV — the ladder-skip loophole is closed. Heroines (cap 99 once promoted) are unaffected.

**Verdict:** Master tier is now a floor-20+ investment for levelers and a stone-investment gate for captures; both paths must ascend before elite skills unlock.

## 3. Damage scaling — tiers flatten at high level

Because the flat `stat + Learning//2` term dominates, the vertical gap between tiers shrinks with level. At an endgame-ish scaling of ~65:

| Skill | Tier | Base | Endgame power (×1.30 mastery) |
|-------|------|-----:|------------------------------:|
| Slash | I | 8 | ≈95 |
| Power Strike | II | 12 | ≈100 |
| Annihilate | IV | 25 | ≈117 |

That is only a ~23% gap between the cheapest and most expensive single-target hit — for **2.5× the cooldown** (Slash CD 2 vs Annihilate CD 5). On sustained DPS, low tiers often beat high tiers; Tier IV's value is burst, statuses, multi-hits, and AoE, not raw numbers. Pure number inflation will not fix endgame relevance — mechanics will.

## 4. Findings

| # | Finding | Severity | Status |
|---|---------|----------|--------|
| 1 | **Regenerate / Mass Regenerate healed the player from a hard-coded 100 HP basis** (`r.get("max_hp", 100)`; the player dict has no `max_hp` key — canonical is `player_max_hp()`). Allies were correct. | Bug | ✅ Fixed in v0.1.8.0 |
| 2 | **Dead duplicate `regen` branch** in `execute_ally_skill` — the `hot` branch shadowed the `apply_regen` branch, so the latter never ran. | Cleanup | ✅ Fixed in v0.1.8.0 |
| 3 | **Dodge's advertised +2 Dexterity was never applied** — only the 50% evasion existed. | Bug | ✅ Fixed in v0.1.8.0 |
| 4 | **Slow and Blind silently hit every enemy** despite `target: enemy` and "an enemy" descriptions. (Slow is −25% DEX — a strong Tier I AoE as implemented.) | Inconsistency | ✅ Fixed in v0.1.8.0 |
| 5 | **Shield Wall's description overpromised** ("take reduced damage *and* protect an ally") — the effect grants 40% reduction to a single chosen target. | Text | ✅ Fixed in v0.1.8.0 |
| 6 | **Flat buffs don't scale:** Strength Buff +2, Wisdom Buff +2, Heroic Onslaught +3, Weakening Curse −2 are ~5% of endgame stats. | Balance | ✅ Fixed in v0.1.8.0 (level scaling) |
| 7 | **Element coverage holes:** learnable attacks cover physical/wind/fire/water/dark/magical — no thunder, earth, or light attacks. | Content gap | ✅ Fixed in v0.1.8.0 (Thunderfall, Worldbreaker, Judgment added) |
| 8 | **Defensive Tier III has exactly one option** (Counter) — a dead spot for Lv 10–14 builds. | Content gap | Open — partly mitigated (five new defensive skills at V/VI; T III still thin) |
| 9 | **Mastery III is dead for utility skills** — `extra_effect` only boosts poison/burn/bleed; non-damage skills get nothing at ★★★ (and nothing at ★ for pure buffs). | Design gap | ✅ Fixed in v0.1.8.0 (mastery now 5 levels, shown ★/★★/★★★/✦/✦✦ — ✦ adds +1-turn effect durations, ✦✦ adds ×2.0 status and −2 cooldown; duration/status hooks wired on both player and ally engines) |
| 10 | **House-stored girls can't learn** and never earn learning XP; the barracks "house copy" branch is unreachable. | Design limitation | By design — kept 2026-10-01 (only party members learn) |
| 11 | **Captures skip tier gates** (arrive at Lv 2–40; gates only checked raw level, not cap). | Design limitation | ✅ Fixed in v0.1.8.0 (gates rescaled + `required_cap` 20/30 for tiers III/IV) |
| 12 | **EXP costs were a soft gate** (2400 ≈ one run). | Balance | Addressed in v0.1.8.0 (costs now 300/800/2000/5000) |
| 13 | **Revive left the defeated flag set** — a revived ally restored HP but stayed benched (affected Raise Dead + Cleric Resurrection). | Bug | ✅ Fixed in v0.1.8.0 |

## 5. Proposed improvements

### 5.1 Tier ladder (question 1 — "too narrow?" — yes)

Options, cheapest first:

- **A. Rescale gates (no new content). — ✅ ADOPTED & IMPLEMENTED in v0.1.8.0.** Gates are now `1 / 8 / 16 / 25` and learning costs `300 / 800 / 2000 / 5000`. Master becomes a floor-20+ goal (cap-30 ascension). YAML-only change + wiki regen. Note: high-level captures (Lv 25+) still auto-qualify by raw level — Option B closes that if desired.
- **B. Gate by ascension, not only level. — ✅ ADOPTED & IMPLEMENTED in v0.1.8.0.** Tiers III/IV now require `level_cap ≥ 20/30` (`required_cap` in YAML, enforced by `meets_skill_requirements()`), so captured girls must be ascended before learning elite skills. Heroines with cap 99 are unaffected. (Originally proposed caps 30/40 — lowered to 20/30 to mirror the level gates and keep the stone economy fair.)
- **C. Add Tiers V–VI. — ✅ ADOPTED & IMPLEMENTED in v0.1.8.0.** Shipped as Lv 35/45, caps 40/50, costs 10k/20k, 16 skills — final list in `docs/barracks_tier_5_6_proposal.md`.

### 5.2 Skill variety (question 2 — "too small?" — catalog fine, choice thin)

The engine already implements most missing primitives (`cleanse_one_debuff`/`cleanse_all_debuffs`, `revive_percent`, `barrier`, sleep/paralyze/entomb/void, `shock_damage`, `bleed_damage`, `stun_chance`, `power_buff`), so additions are mostly YAML + wiki-generator work:

- **Defensive T3:** Barrier (absorb pool) — fills the one-option tier.
- **Support:** Cleanse (single/all debuffs); Revive (`dead_ally`, expensive cooldown).
- **Offensive utility:** Thunder/Earth/Light attack skills (element gap); a bleed or stun skill; a lower-tier armor-piercing opener.
- **Scaling buffs:** any remaining flat-valued effects should follow the new `scale_per_level` opt-in.

Keep the pool ≤ ~40–45 so category menus stay readable.

### 5.3 Endgame tiers & mastery (question 3 — "more tiers?" — yes, mechanical ones)

- **Tiers V–VI — ✅ IMPLEMENTED in v0.1.8.0.** 16 skills shipped as reviewed (`docs/barracks_tier_5_6_proposal.md`): revives (30% / 75% + shield), death prevention (Undying Vow), caster-HP barrier (Aegis Shell), party mitigation/tempo, and thunder/earth/light attack coverage. Revive plumbing bug fixed alongside (see §4 #13).
- **Mastery extension — ✅ IMPLEMENTED in v0.1.8.0** (`docs/mastery_extension_design.md`): five levels at 10/25/50/90/150 uses (★/★★/★★★/✦/✦✦); ✦ adds +1-turn effect durations, ✦✦ adds ×2.0 status potency and −2 total cooldown; Arcane Tower research extended to the ✦✦ cap (5k/15k/40k/80k/170k). Duration/status hooks are live on both engines (player class skills + ally skills).
- Do **not** pump base powers without touching the scaling formula — a Tier V at base 35 is only ~+10% over Tier IV at endgame.

## 6. Patch log — v0.1.8.0 (this pass)

**`resources/skill_book/skill_list.yaml`**
- **Tiers V–VI added:** 16 new skills (gates 35/45, caps 40/50, costs 10k/20k): Thunderfall, Rend, Glacial Requiem, Worldbreaker, Judgment, Aegis Shell, Bulwark, Indomitable, Guardian's Vow, Undying Vow, Phoenix Call, Cleansing Chorus, Benediction, Radiant Rebirth, Fate's Favor, Astral Haste.
- **Tier gates rescaled:** II `5→8` (cost `600→800`), III `10→16` (`1200→2000`), IV `15→25` (`2400→5000`); Tier I unchanged. All 23 affected skills updated.
- **Ascension gates added:** tiers III/IV gained `required_cap: 20 / 30` (all 15 skills).
- `dodge` effect gained `dex_bonus: 2` (the +2 DEX is now real).
- `shield_wall` description corrected to match its single-target effect.
- `strength_buff`, `wisdom_buff`, `heroic_onslaught` gained `scale_per_level: 0.15`; `weakening_curse` gained `scale_per_level: 0.10` — all with level-scaling descriptions.

**`combat/ally_skills.py`**
- New helper `meets_skill_requirements(ally, skill_def)` — enforces level + level-cap gates; `teach_ally_skill()` now uses it (replacement path inherits the check).
- New helper `_scale_effect_value(effect, caster_level)` — opt-in `scale_per_level` support for effect values.
- Barrier branch sizes off the caster's max HP (`value_from_caster_hp`); revive supports `revive_barrier_pct`; new `death_ward` effect type; dead-ally targeting now only offers fallen allies.
- `stat_buff` / `stat_debuff` branches use the scaled value.
- `evasion` branch applies the optional `dex_bonus`.
- `regen` branch computes %-of-max-HP against the correct max HP for the player (`player_max_hp()`), fixing Regenerate/Mass Regenerate.
- `slow` / `blind` branches now respect a single chosen target when the skill targets one enemy.
- Removed the dead duplicate `regen` branch and the now-unused `apply_regen` import.

**`combat/status_effects.py` / `combat/combat_engine.py` / `combat/superboss_common.py`**
- New `apply_death_ward()` / `try_consume_death_ward()` (Undying Vow); the save is wired into both engines' enemy-attack and DoT death paths for allies and the player.

**`combat/skills.py`**
- Cleric Resurrection now clears `defeated` on the revived ally (same fix as the ally revive path).

**`facilities/barracks.py` / `facilities/skill_book.py`**
- Skill listing locks/requirements now cover the level cap (`Requires Lv.X + Cap Y`); the teaching refusal explains to ascend at the House Lounge; the skill book shows `Cap: Y` on learned skills.

**`gui/screens/changelog_screen.py`**
- Added a "Barracks & Ally Skills" section documenting the fixes.

**`tests/_temp_gen_skills_wiki.py`**
- `fmt_effect` now renders Dodge's DEX bonus and "(scales)" for level-scaling stat buffs/debuffs; wiki regenerated.

## Appendix — scaling formula used

`_scale_effect_value`: `base + int((caster_level − 1) × scale_per_level)`
(buff skills use `0.15`, Weakening Curse uses `0.10`)

| Skill | Base | Lv 1 | Lv 15 | Lv 30 | Lv 40 | Lv 60 |
|-------|-----:|-----:|------:|------:|------:|------:|
| Strength Buff / Wisdom Buff | +2 | +2 | +4 | +6 | +7 | +10 |
| Heroic Onslaught | +3 | +3 | +5 | +7 | +8 | +11 |
| Weakening Curse | −2 | −2 | −3 | −4 | −5 | −7 |

Values are tunable per-skill via `scale_per_level` in the YAML with no code changes.
