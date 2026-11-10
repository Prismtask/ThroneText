# Barracks Tiers V–VI — Skill Proposal (for review)

**Status:** ✅ **Implemented in v0.1.8.0** (revive bug patched first, as requested)
**Date:** 2026-10-01 · **Context:** audit §5.3 in `docs/barracks_skills_audit.md` (Option C)

This document proposes the endgame tier expansion. Current pool: 31 skills (Tiers I–IV).
Proposed additions: **16 skills** (8 per tier) → 47 total.

**Review decisions incorporated (2026-10-01):** expand to 16 · Tier V revive kept but weakened (30%), Tier VI gets an upgraded revive **and** a death-prevention skill · barriers are a fixed % of the **caster's max HP** at cast time · names kept.

---

## 1. Proposed gates

| Tier | Name | Required Level | Required Cap | EXP to Learn | Ascension required |
|------|------|---------------:|-------------:|-------------:|--------------------|
| V | Elite | 35 | 40 | 10,000 | 3rd ascension — Stone III territory (floor 30+) |
| VI | Legend | 45 | 50 | 20,000 | 4th ascension — Stone IV territory (floor 40+) |

- Cap gates follow the same rule added in v0.1.8.0: captures must be ascended at the House Lounge.
- Stone gold cost at these steps is ~6,000g (cap 30→40) and ~12,000g (cap 40→50) before discounts.
- 20,000 EXP ≈ a multi-run project at level-40-ish enemy payouts.

## 2. Design rules used

1. **Mechanics over numbers.** At endgame the flat `stat + Learning//2` term dominates, so base_power inflation is invisible (audit §3). Every T5/T6 skill must add a *capability*: barrier, revive, cleanse, party mitigation/tempo, shock/bleed, armor pierce, element coverage.
2. **Element gaps get filled:** learnable attacks currently have no thunder, earth, or light options (audit finding #7).
3. **Cooldowns 6–8** — ultimate-button pacing, not spam.
4. Everything is **YAML-first**; engine status is marked per skill.

## 3. Tier V — Elite (Lv 35 · Cap 40 · 10,000 EXP)

| # | Skill | Category | Target | Element | Numbers / Effect | CD | Engine |
|---|-------|----------|--------|---------|------------------|----|--------|
| 1 | **Thunderfall** | Offensive | all enemies | Thunder | base 20 (LER) · `shock_damage: 12`, `shock_duration: 3` | 6 | ✅ ready |
| 2 | **Rend** | Offensive | single enemy | Physical | base 10 (DEX) × **3 hits** · `bleed_damage: 12`, `bleed_duration: 4` | 6 | ✅ ready |
| 3 | **Glacial Requiem** ⭐ | Offensive | all enemies | Water | base 18 (LER) · applies **Slow** 3 turns (−25% DEX) | 6 | ✅ ready |
| 4 | **Aegis Shell** | Defensive | self or ally | Magical | barrier absorbs **30% of the caster's max HP**, 3 turns | 6 | ⚠ barrier value computed from caster HP (small engine add) |
| 5 | **Bulwark** | Defensive | whole party | Earth | 30% damage reduction, 2 turns | 6 | ✅ ready |
| 6 | **Phoenix Call** | Support | fallen ally | Light | revive at **30% HP** (weakened per review) | 8 | ⚠ revive must clear `defeated` (see §6) |
| 7 | **Cleansing Chorus** | Support | whole party | Light | heal base 12 (WIS) + cleanse all debuffs | 6 | ✅ ready |
| 8 | **Benediction** ⭐ | Support | self or ally | Light | big single-target heal, base 30 (WIS) | 5 | ✅ ready |

⭐ = new since the first review draft.

**Why these:**
- *Thunderfall* fills the thunder attack gap; shock gives it an identity beyond damage.
- *Rend* is boss sustain — bleed keeps ticking through long superboss fights.
- *Glacial Requiem* fills the water AoE/control slot; Slow (−25% DEX) is a real endgame debuff.
- *Aegis Shell* is the only ally-usable absorb pool, sized off the caster's own HP so it scales with her build, not her level.
- *Bulwark* is the first **party-wide** mitigation (Perfect Guard is self-only).
- *Phoenix Call* is the entry revive — deliberately weak (30%) so it's a recovery tool, not a reset.
- *Cleansing Chorus* answers the debuff-heavy endgame (fear, silence, burns, void).
- *Benediction* fills the burst-single-heal gap between Heal (T1) and the party healers.

## 4. Tier VI — Legend (Lv 45 · Cap 50 · 20,000 EXP)

| # | Skill | Category | Target | Element | Numbers / Effect | CD | Engine |
|---|-------|----------|--------|---------|------------------|----|--------|
| 1 | **Worldbreaker** | Offensive | single enemy | Earth | base 24 (STR) × 2 hits · `ignore_armor_pct: 0.5` | 7 | ✅ ready |
| 2 | **Judgment** | Offensive | all enemies | Light | base 22 (LER) · `bonus_vs_races: [Undead, Abomination]` (+30%) | 7 | ✅ ready |
| 3 | **Indomitable** | Defensive | self | Light | 80% damage reduction, 2 turns | 7 | ✅ ready |
| 4 | **Guardian's Vow** | Defensive | whole party | Earth | 40% damage reduction, 3 turns | 8 | ✅ ready |
| 5 | **Undying Vow** ⭐ | Defensive | whole party | Light | 3 turns: the first lethal blow each ally takes instead leaves them at **1 HP** (consumed per ally) | 9 | ⚠ needs `try_survive_lethal()` helper + death-path wiring (see §6) |
| 6 | **Radiant Rebirth** ⭐ | Support | fallen ally | Light | revive at **75% HP** + barrier of **15% of caster's max HP** (2 turns) | 9 | ⚠ revive `defeated` clear + barrier-from-caster-HP add |
| 7 | **Fate's Favor** | Support | whole party | Fire | +15% damage dealt (`damage_boost`), 3 turns | 7 | ✅ ready |
| 8 | **Astral Haste** | Support | whole party | Thunder | haste: +3 initiative, next-skill cooldown −1, 3 turns | 8 | ✅ ready |

⭐ = new since the first review draft.

**Why these:**
- *Worldbreaker* covers the earth attack gap and is the anti-armor finisher (paired with Rend's sustain).
- *Judgment* covers the light attack gap and gives endgame undead/abomination hunts a dedicated answer.
- *Indomitable* is the panic button; *Guardian's Vow* the sustained party version.
- *Undying Vow* is the requested **death prevention** — it turns a losing round into a recoverable one without a full revive reset, and layers with the revives as the fallback plan.
- *Radiant Rebirth* is the "better effect" Tier VI revive: 75% HP plus an absorb shield so the revived ally survives the round they return in.
- *Fate's Favor* and *Astral Haste* multiply the whole party — the kind of utility that ages well (like Aura of Despair).

## 5. Example YAML shape (Thunderfall)

```yaml
    thunderfall:
      name: Thunderfall
      description: Call down a storm of lightning that shocks all enemies.
      tier: 5
      exp_cost: 10000
      required_level: 35
      required_cap: 40
      category: offensive
      cooldown: 6
      target: enemies
      power_type: ler
      base_power: 20
      shock_damage: 12
      shock_duration: 3
      elemental: thunder
      mastery_thresholds:
      - 25
      - 50
      - 100
```

## 6. Implementation checklist (all shipped)

- [x] `skill_list.yaml`: 16 blocks + tier 5/6 gates (`required_level` 35/45, `required_cap` 40/50, costs 10,000/20,000).
- [x] `combat/ally_skills.py`:
  - [x] barrier branch: `value_from_caster_hp` (fixed % of the caster's max HP at cast time) — powers Aegis Shell and Radiant Rebirth's shield.
  - [x] revive branch: clears `defeated` so the ally rejoins combat — **fixed ahead of the build**, including the Cleric Resurrection path (Raise Dead shared the gap).
  - [x] death prevention: `apply_death_ward()` / `try_consume_death_ward()` in `status_effects.py`, wired into both engines' enemy-attack and DoT death paths (allies + player). Not wired: the Big Bad Wolf's scripted swallow (special mechanic).
- [x] Tier label maps extended to six tiers: `facilities/barracks.py`, `facilities/skill_book.py`, `tests/_temp_gen_skills_wiki.py`.
- [x] Wiki generator: renders `barrier`, `death_ward`, `haste`, `revive_barrier_pct`; wiki regenerated (47 learnable skills).
- [x] Changelog entry + audit update.
- [ ] Balance pass after playtest (numbers are first-pass).

## 7. Review log

**Resolved (2026-10-01 review):**
1. **Count:** expanded to **16** (8 per tier) — added Glacial Requiem, Benediction, Undying Vow, Radiant Rebirth.
2. **Revive:** Tier V Phoenix Call weakened to **30% HP**; Tier VI gets Radiant Rebirth (**75% + shield**) **and** the death-prevention skill Undying Vow.
3. **Barrier:** fixed at cast time from the **caster's max HP** (30% for Aegis Shell, 15% for Radiant Rebirth's shield) — not level-scaled.
4. **Names:** kept.

**Resolved (2026-10-01, final):**
- Undying Vow numbers confirmed: 3 turns / CD 9 / one save per ally per cast.
- Support menu size (18 options) accepted.
- Build approved and shipped — see §6.
