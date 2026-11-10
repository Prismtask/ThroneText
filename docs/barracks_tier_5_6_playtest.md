# Barracks Tiers V–VI — Playtest Checklist

**Date:** 2026-10-01 · **Build:** v0.1.8.0 · **Scope:** Tier V–VI (16 skills), revive fixes, Undying Vow death prevention

Beyond "does the skill do what it says", this list targets the parts I **could not verify with scripts** —
turn-order rejoin, death paths across both engines, caster-vs-target math, and buff interactions.

---

## 0. Fast setup

- **Training Dummy** (Barracks → "Spar with Training Dummy") is the best lab: set HP, STR/CON/DEX mods, and per-element resistances freely, and flee any time.
- **To reach the gates:** Tier V needs Lv 35 + Cap 40, Tier VI Lv 45 + Cap 50. Fastest path: capture a high-level monster girl (Lv 30–40) and ascend her at the **House Lounge** (Stones I–IV), or test on a late save.
- New HUD tags to watch for: **BAR&lt;n&gt;** (barrier pool), **WARD** (undying vow), **HST** (haste) — added so you can see these tick.
- To force lethal hits: raise the dummy's STR mod, or go to a superboss.

---

## A. Gating & menus
- [x] Teach menu shows **Tier V (Elite)** and **Tier VI (Legend)** sections with locks like `Requires Lv.35 + Cap 40`.
- [x] A captured **Lv 40 girl with Cap 10**: both tiers LOCKED; selecting one explains `Required: Level Cap 40 | Current: Level Cap 10` + "Ascend her at the House Lounge first."
- [x] Ascend to Cap 40 → Tier V unlocks; Tier VI stays locked until Lv 45 + Cap 50.
- [x] Skill Book shows `[Tier V]`/`[Tier VI]` and `Cap: 40/50`.
- [x] Support menu with **18 options** renders/scrolls cleanly in the GUI.

## B. Revive fixes — **top priority** (this was the bug)
- [x] **Phoenix Call** on a fallen ally → revives at 30% max HP, shows alive in HUD, **and can act on her next turn**.
- [x] **Radiant Rebirth** → 75% revive + shield (see D).
- [x] Older paths give the same result: **Cleric Resurrection** and the **Raise Dead** innate.
- [x] With **no** fallen allies: revive is rejected ("Action canceled.") and returns to the menu — you can no longer target living allies.
- [x] With 2+ fallen: picker lists **only** the fallen.
- [ ] 🚩 Red flag: after a revive, the ally displays `[INCAPACITATED]`, is skipped in the turn order, or still can't act → the defeat-flag fix regressed.

## C. Undying Vow / death prevention — **riskiest feature**
- [x] Cast → every party member gets **WARD** (player included).
- [x] Enemy lands a lethal blow on an ally → log shows `Undying Vow holds — X survives at 1 HP!` and she stays up. **Her** ward is consumed; others keep theirs.
- [x] Same for the **player**: `Your Undying Vow flares — you survive at 1 HP!`
- [x] **DoT lethal** (bleed/poison ticking at round end) also triggers the save.
- [x] **Do this in a superboss fight too** — it runs a separate combat loop and has its own death paths.
- [x] After 3 turns: `Your Undying Vow fades.` and it no longer saves.
- [x] Recasting while active **refreshes** the duration (does not bank two saves).
- [x] Known non-coverage (expected): the **Big Bad Wolf's scripted swallow** still KOs allies.
- [ ] 🚩 Red flags: a lethal hit that should have been warded but wasn't (note source: normal enemy / superboss / DoT / scripted); an ally left at 0 HP but not marked defeated; any freeze.

## D. Barriers & shields
- [x] **Aegis Shell**: absorbed pool = **30% of the CASTER's max HP**, not the target's. Verify with two different max-HP values (equip/unequip gear on one of them).
- [x] Pool depletes per hit; `Barrier: N absorb remaining` ticks; **BAR&lt;n&gt;** tag counts down; expiry message appears.
- [x] Recast stacks the pool (intended).
- [x] **Radiant Rebirth shield** = 15% of the caster's max HP for 2 turns, sitting on the revived ally.

## E. New damage skills
- [x] **Thunderfall** — shock on ALL enemies; shock ticks; check direction vs resists (Jabberwock: thunder 0.8 = slightly weak; set dummy resists to be sure).
- [x] **Rend** — 3 hits; bleed applies and ticks ~4 turns. Watch repeated hits: does bleed refresh to something sane, or snowball?
- [x] **Glacial Requiem** — ALL enemies slowed (**SLW**); confirm the enemies visibly slow down.
- [x] **Worldbreaker** — 2 hits; compare vs a high-CON target (dummy CON mod up): piercing 50% armor should matter.
- [x] **Judgment** — `Bonus vs Undead/Abomination! +30%` on a Banshee/undead or Chrysalis (Abomination); NO bonus line on beasts etc.
- [x] Element direction sanity: weakness should read LOW `elemental_res` (e.g. Jabberwock light 0.6 → Judgment hits harder).

## F. Party support
- [x] **Cleansing Chorus** — heals each living member and strips their debuffs; uncleansable debuffs stay with the "some wounds resist" note; the fallen are not healed.
- [x] **Benediction** — big self/ally heal; number scales with WIS.
- [x] **Bulwark / Guardian's Vow** — whole party (player included) takes less damage. Combine with Protect/Perfect Guard and check mitigation doesn't reach absurd levels (~100% immunity would be a bug).
- [x] **Fate's Favor** — +15% damage also on **player attacks**, not just allies (this exact bug existed before).
- [x] **Astral Haste** — party acts earlier; using a skill afterwards shows the cooldown-reduction consumption message.

## G. Mastery, learning, cooldowns
- [x] Mastery counter climbs; thresholds are 25/50/100 (Tier V) and 30/60/120 (Tier VI); ★ shows in the Skill Book; mastery 2 → −1 cooldown.
- [x] Learning completes mid-combat with the "has mastered X!" message; the skill appears in the combat menu next fight.
- [x] 3-slot replacement with a Tier V/VI skill; the mastery-loss warning shows.

## H. Persistence & cross-combat
- [x] Save/load: learned Tier V/VI skills, in-progress learning, and mastery all persist.
- [x] **Buff carryover** (pre-existing behavior, confirm it's acceptable): cast Undying Vow/barrier, win fast — do they carry into the next fight with reduced turns? All timed combat buffs behave this way; flag it if it feels exploitable, and we'll decide whether wards should clear on combat end.

---

## 🚩 Stop-and-report list
1. Crash or soft-lock (especially revive + ward combos, superboss loops).
2. A revived ally that can't act (regression of the fixed bug).
3. Ward/barrier numbers that don't match the caster-based math.
4. Any lethal hit that should have triggered a ward but didn't — note the source.
5. Ally stuck at 0 HP, or alive with negative HP.
6. Elemental damage moving the wrong direction.

## Known limitations (not bugs)
- Big Bad Wolf swallow is not covered by the ward.
- The ward shows a tag but no turn-count number.
- All numbers are **first-pass** — report how they feel (too strong/weak) and I'll tune YAML values.
