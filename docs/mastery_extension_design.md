# Mastery Extension to ★★★★★ — Design Discussion

**Status:** ✅ Implemented in v0.1.8.0 (ally + player hooks) — display: ★ / ★★ / ★★★ / ✦ / ✦✦
**Date:** 2026-10-01 · **Question:** extend skill mastery from 3 to 5 levels — with what rewards, and what does it touch?

---

## 1. Current system (verified facts)

| Level | Threshold (uses) | Bonuses |
|-------|------------------|---------|
| ★ | 10 | +15% power |
| ★★ | 25 | (keeps +15%) · **−1 cooldown** |
| ★★★ | 50 | **+30% power** · "extra effect" |

- **Usage counting:** +1 per cast. Player: `add_skill_mastery_xp` at the end of `execute_skill` (all 48 class skills). Ally: `add_ally_skill_mastery_xp` at the end of `execute_ally_skill` (innate + learnable + heroine skills alike, incl. the effect-only early return).
- **Bonuses are shared:** `get_mastery_bonuses()` in `combat/skills.py` is used by BOTH engines. `skill_id` is currently ignored.
- **"Extra effect" (★★★) is not data-driven.** It's implemented ad hoc:
  - **Player side:** ~10 bespoke branches (Battle Cry +1, Divine Shield +1 turn, Feral Rage +1, Dark Curse +1, Hunter's Mark 0.50→0.75, execute threshold 0.15→0.20, plus three crit/status sites ~lines 855/980/997).
  - **Ally side:** 6 sites — poison/burn/bleed potency ×1.5. **Everything else gets nothing at ★★★** (audit finding #9: dead level for utility skills).
- **Thresholds are hardcoded in 4 places:** `combat/skills.py`, `combat/ally_skills.py`, `facilities/arcane_tower.py` (research costs + `_next_mastery_threshold`).
- **The YAML `mastery_thresholds` lists are documentation-only.** The wiki generator reads them; the game ignores them. So the wiki currently advertises per-skill pacing (e.g. 12/30/60) the game doesn't use — **a pre-existing inconsistency to fix in this pass.**
- **Arcane Tower research** sells instant progress to the next threshold: 5,000 / 15,000 / 40,000 gold for ★1/★2/★3, hard-capped at ★★★.
- **UI surfaces:** star arrays in `combat/skills.py` + `combat/ally_skills.py` (`["", "★", "★★", "★★★"]`), combat skill menus, Skill Book, Inventory stats screen, tower text.

## 2. What extending to ★★★★★ touches

| System | Tracked today? | Impact of extension |
|--------|----------------|---------------------|
| Player class skills (48) | Yes | Power steps apply free (damage/heals). L4/L5 utility value needs generic hooks or stays flat; bespoke ★★★ branches unaffected unless extended. |
| Ally learnable skills (47) | Yes | Fully generic path — cleanest, gets everything once the engine hooks exist. |
| Ally innate skills (~112) | Yes | Same generic path; exotic mechanics (summons, specials) may ignore power/CD — need the duration/status hooks to feel progress. |
| Heroine vorpal/upgrade skills | Yes | Same as innate. |
| Weapon specialties (Abyss Fang, Cutlass, Author's Pen, workshop attacks, Brush) | **No** | Not mastery-tracked; recommend leaving out. |
| Enemies / bosses | No | Unaffected. |
| Arcane Tower research | — | Caps, costs, "MAX" text, threshold helper must extend. |
| Combat HUD / menus / Skill Book / Inventory | — | 5-star labels; HUD width check (68-char box). |
| Wiki generator + `mastery_thresholds` YAML | — | Threshold legend + regenerate; reconcile with code. |
| Saves | — | Use-counts persist as-is; no migration if levels 1–3 keep their thresholds. |

## 3. Reward design — the three directions

**A. More damage (`power_mult` steps).** Simple and free for all tracked skills, but at endgame the flat `stat + Learning//2` scaling dominates (audit §3), so ×1.45/×1.60 over ×1.30 is barely felt — and it does *nothing* for buffs/debuffs/CC. Good baseline, bad solo answer.

**B. More cooldown reduction.** The only knob that matters to utility skills — and dangerous: cooldowns already floor at 0 (a CD-1 skill is spam-every-turn at ★★); stacking with Haste/Astral Haste/Time Warp/Arcane reductions could trivialize ultimates. If used, cap the total at −2 and keep the 0 floor.

**C. Duration / potency upgrades.** The real fix for utility: +1 turn on buffs/debuffs/DR/HoT/barrier/ward, and status potency beyond ×1.5. Centralized engine hooks make this cheap on the ally side; the player side needs a survey of ~20 bespoke effect branches.

**D. Per-skill capstones (a new "additional effect").** Most exciting, most expensive: ~200 skill defs to author, and the ad-hoc `extra_effect` logic would need to become data-driven first. Recommended as a later optional layer with per-skill overrides — not the first implementation.

### Recommended hybrid (no per-skill authoring)

| Level | Power | Cooldown | Effect duration | Status potency |
|-------|-------|----------|-----------------|----------------|
| ★ | ×1.15 | — | — | ×1.0 |
| ★★ | ×1.15 | −1 | — | ×1.0 |
| ★★★ | ×1.30 | −1 | — | ×1.5 |
| ✦ | ×1.45 | −1 | **+1 turn** | ×1.75 |
| ✦✦ | ×1.60 | **−2** | +1 turn | ×2.0 |

Implementation shape: extend `get_mastery_bonuses()` with two new keys — `duration_bonus` (added where effects read `duration`, one line in the ally effect block + survey of player branches) and `status_mult` (replaces the 1.5 literals at the 6 ally sites; ~3 player sites). Bonus levels flow to every tracked skill automatically. Optional per-skill overrides can later merge from YAML (and the unused `skill_id` parameter finally gets used).

## 4. Thresholds & plumbing

Options for ★4/★5 thresholds (levels 1–3 stay 10/25/50 for save compatibility):

1. **10 / 25 / 50 / 100 / 200** — clean doubling; ★5 is prestige (~200 casts).
2. **10 / 25 / 50 / 90 / 150** — softer; ★5 reasonably achievable per campaign.
3. **Per-skill from YAML** (recommended as the cleanup): make code read `mastery_thresholds` with a global fallback for entries that only have 3 values — fixes the doc/game mismatch, enables per-skill pacing, and the lists already exist in all ~200 defs. Backfill two numbers per def over time; fallback covers the rest.

Regardless of option: **centralize** thresholds in one helper used by `skills.py`, `ally_skills.py`, `arcane_tower.py`, and the wiki generator — currently four copies drift independently.

**Chosen:** global **10 / 25 / 50 / 90 / 150** (option 2). The per-skill YAML `mastery_thresholds` lists are now retired from gameplay — the wiki prints the global table instead. `MASTERY_THRESHOLDS` in `combat/skills.py` is the single source of truth; the tower and the wiki generator reference it.

## 5. Arcane Tower tie-in (a real endgame gold sink)

Extend research to ★4/★5: e.g. **100,000g** (→★4) and **250,000g** (→★5), keeping the same "pay for the next threshold" model. Update the MAX check, the bonuses summary text, and `_next_mastery_threshold`. This also gives players a no-grind path and gives late-game gold a purpose.

## 6. UI / UX notes

- Star arrays in two modules + "★★★" literals in tower text and Skill Book. Extend and unify.
- **HUD width:** solved by the chosen display — level 4/5 labels are ✦ / ✦✦ (2 chars max), so the 68-char combat box has plenty of room.
- Skill Book should list the full per-level bonus table instead of the single "Bonus effect at ★★★" line.

## 7. Risks & guardrails

- **CD floor:** keep total reduction capped at −2, floor 0. Decide whether CD-1 skills at 0 (already possible) stay as-is.
- **Stacking audit:** Haste + Astral Haste + Time Warp + Arcane cooldown reduction + mastery — verify a sensible floor together.
- **Power creep:** ×1.45/×1.60 measured against superboss HP; likely fine given the flat-scaling math, but playtest.
- **Support stacking (v2):** no caps added by design — maxed Mark (×2.0) + maxed Aura of Despair (×2.0) on one target ≈ ×2.6 damage taken; verify superboss TTK in playtest.
- **Exotic skills** (summons/specials) may still plateau — acceptable for v1; per-skill capstones solve it later.
- **Docs cleanup:** wiki regenerated with the real thresholds; audit finding #9 updated.

## 8. Decisions (2026-10-01, final) & implementation notes

1. **Reward model:** hybrid table accepted — shipped as ★1 ×1.15 · ★2 −1 CD · ★3 ×1.30 + bonus effect + ×1.5 status · ★4 ×1.45 +1-turn durations + ×1.75 status · ★5 ×1.60 −2 CD + ×2.0 status.
2. **Thresholds:** global **10/25/50/90/150** (levels 1–3 unchanged); YAML lists retired from gameplay.
3. **Cooldown:** −2 total at ★5, floor 0 as before.
4. **Tower:** research extended to ★5 at **80,000 / 170,000** gold for ★4/★5.
5. **Scope:** hooks shipped on both engines — `execute_ally_skill` (all effect branches + six DoT sites) and `execute_skill` (every timed player effect gets `duration_bonus`; burn/poison potency uses `status_mult`). Power/cooldown steps reach player class skills automatically via the shared table.
6. **Weapon specialties:** untracked, unchanged.
7. **Display:** chosen — levels 1–3 use ★, level 4 uses ✦, level 5 uses ✦✦, applied in every renderer (`format_mastery_label` / `format_ally_mastery_label`, Skill Book, Arcane Tower, Inventory, changelog, wiki).
8. **Support potency (v2, 2026-10-01):** `status_mult` now scales every support magnitude, not just DoT damage — single scaling channel, so the old ★3 `extra_effect` value bumps were converted into the multiplier (battle cry, feral rage, dark curse, hunter's mark, empowerment, sunder); soul fear, vulnerable and haste values also scale. Integers round half-up. Ally side: all value-based effect branches scale (damage reduction, evasion, stat buffs/debuffs, barrier, flat regen, cooldown reduction, reflection, power buff, damage boost, elemental weakness, mark, damage-taken amps, shock, lifesteal, haste init/cd). Flat heals stay unscaled (they already get ×power_mult); crit boosts left alone (cap-dominated). **Curse stays flat** — the number scales with mastery instead of converting to %, since flat is proportionally strong vs small enemy stats. Future idea: CRS+/CRS++ HUD severity for stacked/fatal curses.
9. **Burn tier ladder:** burn skills no longer multiply damage — they upgrade the burn tier: **+1 at ★3, +2 total at ✦✦** (cap tier 5 / Conflagration). Applies to both engines, all 4 burn sites.
10. **Revives (reworked):** mastery-scaled tables override YAML — Phoenix Call `20/20/20/25/25/35%`, Radiant Rebirth `45/45/45/50/50/70%`, Lich Queen's innate Raise Dead `30/30/30/35/35/50%` (m0–m5, plateau between the m1/m3/m5 anchors). Raise Dead keeps the highest ceiling so the Lich Queen stays the premium reviver versus the learnable Phoenix Call. Barrier portion unchanged.

**Wired in:** `combat/skills.py` (thresholds + bonus table + labels + `duration_bonus` on every timed effect + support magnitudes via `_scaled_value` + burn tier ladder), `combat/ally_skills.py` (`_scaled_mag` on every value-based effect branch, burn ladder, shock, haste, revive tables `REVIVE_MASTERY_PCT`), `facilities/arcane_tower.py` (research to ★5), `facilities/skill_book.py` (bonus lines, "Effect potency ×"), wiki generator, changelog, docs, and the smoke test (sections 17–19).
