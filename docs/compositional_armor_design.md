# Compositional Armor & Accessories — Form × Element × Grade (for review)

> **Status:** ✅ **Grid implemented 2026-10-19** — 16 armor × 9 × 3 and 17 accessory × 9 × 3 coordinates are live (851 generated pieces + curated overrides). **Form perks implemented 2026-10-19** (`combat/form_perks.py` — every equipment piece participates, 4 slots / 5 with the Beating Root). **D-RES resolved 2026-10-18. Rarity soft ceiling + commission ✅ 2026-10-19 (`rarity_grade_flower_audit.md`). Flower infusion rework ✅ 2026-10-20 — armor/accessories are base forms; 2026-10-27: up to three resistance elements per piece (formula v4).**
>
> **⚠ GRADE MODEL RETIRED (2026-10-20).** This document is kept as the historical design record for the 2026-10-19 grid. The current equipment model is base forms + flower infusion — see `docs/rarity_grade_flower_audit.md` §12. Do not implement grade mechanics from the sections below.
> **Companion:** `docs/compositional_equipment_design.md` (weapons) · `docs/item_economy_tuning_design.md` (economy pass — ships first).
> **Sequencing (user direction):** economy pass → weapon grid → armor/accessory grid. **D-RES (§7) fixed 2026-10-18**, ahead of the queue.
> **Direction (2026-10-18):** same machinery as weapons for armor & accessories; uniques untouched; design first.

---

## 1. Current state (verified against code, 2026-10-18)

- **17 armor + 26 accessory definitions**, all prebuilt one-offs (plus uniques/specials below). Same problem as weapons: the Ember/Blaze/Frost prefixes are cosmetic — Ember Ring (fire 1.1), Blaze Band (fire 1.1) and Blaze Gauntlets (fire 1.1) have identical elemental strength; no grade ladder exists.
- Stats: armor `base_mods` total 2–6; accessories 1–5. Res profiles: armor 2–5 entries at 1.05–1.3; accessories 1–4 entries at 1.05–1.2.
- Armor/accessories carry `primary_element`, but it is **unused in combat** — only weapons resolve elemental traits. Their element exists purely as a resistance profile.
- Armor forms are already implied by names (Padded/Chainmail/Scale/Banded/Plate/Leathers/…), accessories by nouns (Ring/Band/Amulet/Cloak/…). Accessory stat patterns already follow a hidden **element → stat affinity** rule (Ember Ring STR, Frost Ring CON/DEX, Gale Ring DEX, Shadow Ring CHA, Arcane Ring LRN, Astral Ring WIS…).

## 2. Model

**Armor instance = ArmorForm × Element × Grade** (+ Rarity, Enhance).
**Accessory instance = AccessoryForm × Element × Grade** (+ Rarity, Enhance).

| Axis | Armor owns | Accessory owns |
|---|---|---|
| Form | silhouette, stat template, res-entry count | noun, stat budget/shape |
| Element | defensive res profile only (§6) | **stat affinity** + res profile |
| Grade | +1 primary stat/grade · res magnitude/entries | +1 primary stat/grade · res magnitude/entries |
| Rarity | unchanged: ×stats, ×res scaling, caps by grade | same |
| Enhance | +1 stat/step (no res) | same |

Grid size: armor ~16 forms × 9 × 3 ≈ **430**; accessories ~17 × 9 × 3 ≈ **460** (vs 43 today).

## 3. Templates & formulas

### 3.1 Armor forms

| Form | Stat template | Res entries | Today's example |
|---|---|---|---|
| Padded Armor | CON 2 | 2 | Iron Padded Armor |
| Chainmail | CON 3 | 3 | Steel Chainmail |
| Scale Armor | CON 3, STR 1 | 3 | Steel Scale Armor |
| Banded Mail | CON 4, DEX −1 | 4 (incl. drawback) | Iron Banded Mail |
| Plate Armor | CON 5, DEX −1 | 4 (incl. drawback) | Bedrock Plate Armor |
| Leathers | DEX 2, CON 1 | 2 | Gale Leathers |
| Elven Mail | DEX 3, LRN 1 | 3 | Zephyr Elven Mail |
| Dragonhide | CON 4, DEX 2 | 3 | Ember Dragonhide |
| Battle Harness | STR 2, CON 2 | 3 | Blaze Battle Harness |
| Fur Mantle | CON 2, WIS 1 | 3 | Frost Fur Mantle |
| Robes | LRN 3, WIS 1 | 3 (incl. drawback) | Arcane Robes |
| Vestments | LRN 4, CON 1 | 3 | Arcane Vestments |
| Regalia | CHA 4, WIS 1 | 3 | Radiant Regalia |
| Silk Garb | CHA 3, DEX 1 | 2 | Shadow Silk Garb |
| Wraps | DEX 4, CHA 1 | 2 | Shadow Wraps |
| Runic Plate | CON 4, LRN 2 | 5 | Mystic Runic Plate |

### 3.2 Armor element profiles (defensive identity)

Each element gets a fixed triangle (primary resist · secondary · drawback). **Rating values are authored "higher = stronger" (data convention — see §7 / D-RES).**

| Element | Primary (g1/g2/g3) | Secondary (g1/g2/g3) | Drawback |
|---|---|---|---|
| Fire | fire 1.15 / 1.25 / 1.35 | earth 1.05 / 1.10 / 1.15 | water 0.85 |
| Water | water 1.15 / 1.25 / 1.35 | wind 1.05 / 1.10 / 1.15 | thunder 0.85 |
| Thunder | thunder 1.15 / 1.25 / 1.35 | wind 1.05 / 1.10 / 1.15 | earth 0.85 |
| Wind | wind 1.15 / 1.25 / 1.35 | thunder 1.05 / 1.10 / 1.15 | earth 0.85 |
| Earth | earth 1.15 / 1.25 / 1.35 | fire 1.05 / 1.10 / 1.15 | wind 0.85 |
| Light | light 1.15 / 1.25 / 1.35 | magical 1.05 / 1.10 / 1.15 | dark 0.85 |
| Dark | dark 1.15 / 1.25 / 1.35 | magical 1.05 / 1.10 / 1.15 | light 0.85 |
| Magical | magical 1.15 / 1.25 / 1.35 | dark 1.05 / 1.10 / 1.15 | physical 0.85 |
| Physical | physical 1.15 / 1.25 / 1.35 | fire 1.05 / 1.10 / 1.15 | magical 0.85 |

- Grade also raises stats: **+1 to the form's primary stat per grade** (armor budgets are smaller than weapons' +2).
- Rarity continues to scale res via the existing `build_item` formula `1.0 + (val − 1.0) × stat_mult` — correct only after D-RES is fixed.

### 3.3 Accessory forms

| Form | Shape | Today's example |
|---|---|---|
| Ring | 1 stat (budget 2–3) | Ember/Frost/Gale/Shadow/Void/Arcane/Astral Ring |
| Band | 2 stats (3–4) | Blaze Band |
| Signet | 1 stat (4) | Radiant Signet |
| Amulet | 1 stat (3) | Stone Amulet |
| Pendant | 2 stats (3–4) | Divine Pendant |
| Talisman | 2 stats (3–4) | Radiant Talisman |
| Cloak | 2 stats (3) | Void Cloak |
| Bracers | 1 stat (3) | Ember Bracers |
| Gloves | 2 stats (3) | Zephyr Gloves |
| Boots | 1 stat (3) | Gale Boots |
| Belt | 2 stats (5) | Stone Belt |
| Brooch | 2 stats (4) | Radiant Brooch |
| Crown | 2 stats (6) | Mystic Crown |
| Tome | 1 stat (3) | Arcane Tome |
| Earring | 2 stats (3) | Arcane Earring |
| Monocle | 2 stats (3) | Mystic Monocle |
| Eye | 2 stats (4) | Divine Eye |

**Accessory element → stat affinity** (codifies the existing pattern; exact numbers per form):

| Element | Primary | Secondary |
|---|---|---|
| Fire | STR | CON |
| Water | CON | DEX |
| Thunder | DEX | STR |
| Wind | DEX | CHA |
| Earth | CON | STR |
| Light | CHA | WIS |
| Dark | CHA | DEX |
| Magical | LRN | WIS |
| Physical | STR | CON |

- Accessory grade: **+1 primary stat/grade**; res primary `1.05 / 1.10 / 1.15`, secondary `1.00 / 1.05 / 1.10`; no drawbacks (matches today's accessories).
- Accessory res profile follows the same element triangle as armor (smaller magnitudes, one secondary, no drawback).

### 3.4 Value & economy

- `intrinsic_value` (economy §3.1) already counts stats + res entries → armor/accessories price correctly once values exist.
- Grade premium (added to intrinsic): **+0 / +1 / +3** (armor) · **+0 / +1 / +2** (accessories) — smaller than weapons' +0/+2/+5.
- Rarity is softened by grade (soft ceiling, D-N / supersedes D-AG): g1 epic 60% / legendary 15% · g2 legendary 40% · g3 unrestricted.
- Enhance: +1 stat/step, multiplicative with rarity (economy Option A); **no res gain from enhance** (grade owns res).

## 4. Generation & rolls

Same pipeline as weapons: roll **form → element → grade → rarity**, with the same
floor bands (g1 ≤10 · g2 11–25 · g3 26+), city-tier shop mixes, regional element
weights, and grade-capped rarity. Armor and accessory pools are separate from
the weapon pool (`_EQUIP_POOL` becomes per-slot-family pools). Treasure rooms
include armor/accessories as today.

## 5. Naming & IDs

Deterministic `{prefix}_{form}`, reusing the blueprint §3a prefixes:
`frost_padded_armor`, `inferno_dragonhide`, `abyssal_crown`, `void_cloak`…
Most existing ids already match this scheme; a mapping table will be produced at
implementation. Accessory names read naturally as element + noun (Ember Ring,
Gloom Pendant…).

## 6. Element identity on armor/accessories (decision D-AE)

- **Recommended: defensive-only.** Armor/accessory elements define only the res
  profile. Weapons remain the trait layer (Sunder/Ignite/…). This keeps the
  armor grid about survival trade-offs, not extra proc noise.
- Alternative: blueprint §3C (armor = half-strength weapon trait, accessory =
  utility trait). Bigger balance surface; revisit only if armor needs more flavor.
- Form perks (heavy = DR, light = evasion, rings = crit, etc.) are deferred to the
  same later phase as weapon form perks.

## 7. D-RES prerequisite — resistance convention inversion (FIXED 2026-10-18)

**Evidence:**

| Source | Convention |
|---|---|
| `combat/elemental.py` header + README §Elemental System | `res < 1.0` = resistant · `> 1.0` = weak |
| Runtime `calculate_elemental_damage` | `final = base × dmg_mult × res_mult` → **res > 1 takes MORE damage** (empirically verified: res 1.3 → 169 dmg; res 0.7 → 91 dmg on a 100 base) |
| **All resistance data** (RACES, CLASSES, ENEMY_RACES, keyword profiles, every armor/accessory) | authored as **higher = stronger**: Ember Dragonhide fire 1.3, Undead dark 1.3 / light 0.6, "flame" keyword fire 1.3, Iron Banded Mail physical 1.2 with wind 0.8 drawback |

**Consequence today:** fire armor makes you take *more* fire damage; "flame"
enemies are weak to fire; undead resist light and are weak to dark — the exact
opposite of the data's designed intent. This is also a likely reason elements
feel flat in play.

**Options (D-RES):**
- **A (recommended): invert at runtime.** Compute `res_mult = clamp(2.0 − res, 0, 2.0)` in `calculate_elemental_damage`; audit every site that adds/subtracts res (`elemental_weakness` debuff, adapt buffs, Event Horizon flask/boon res, traits); flip README/header wording and `format_elemental_short` semantics (display `+` = resistance). Data untouched; all future data keeps "higher = better".
- **B: invert all data** (`r → 2 − r` in races/classes/enemy races/keywords/enemy YAML/items). Runtime + docs stay; large mechanical migration and awkward future authoring.
- **C: leave as-is** — rejected (gear and enemy identities remain inverted).

**Implemented 2026-10-18 (Option A):** `resistance_multiplier()` in `combat/elemental.py` (2 − rating, clamped, rounded); `calculate_elemental_damage` now works in rating space; Pierce (player + ally), direct-damage boss attacks (Jabberwock, Mary Sue's shadow, White Knight, Wicked Witch), and the training-dummy/barracks config were updated; README/header wording flipped. Data untouched. Verified by `tests/_diag_elemental_res.py` (`_diag_status_res.py` still passes).

## 8. Uniques & specials — stats untouched, form-tagged (D-J)

Tarnished Jade, Sky Piercer, Prescript Ledger, wedding accessories, engagement
rings, heroine/quest/Wonderland gear, and the third accessory slot (`acc3`
unlock) are excluded from the grid, caps, composition, and grading. They keep
hand-tuned stats, red tier, and specials.

**Since 2026-10-19 every unique carries a `form` tag** (noun-based where the
name is clear, description-based where it isn't — Sky Piercer → talisman,
Prescript Ledger → tome, Witch's Hat → crown). They therefore inherit form
perks without being re-stat'ed or priced differently. Curated hand-written
gear is tagged as well (id-suffix inference, plus an explicit map for stray
nouns: locket → amulet, anklet → band, accessory gauntlets → gloves), so no
equipment piece is excluded from the perk layer. See
`docs/compositional_equipment_design.md` §6.1 / D-J.

## 9. Migration & tests

- Old save instances keep their full dicts; re-stat migration is optional (D-AH; recommend piggybacking the economy/weapon migration).
- Tests: grid sanity (each form×element×grade composes within budget), res-convention unit tests (after D-RES), weighted-roll distributions, grade caps, naming/id generation, migration idempotency.
- Sequencing: economy → weapons → D-RES + armor/accessories. D-RES may land earlier as a bug fix.

## 10. Decisions (LOCKED 2026-10-18 — as recommended)

| # | Decision | Options | Recommendation |
|---|---|---|---|
| D-RES | Resistance convention | A runtime `2 − res` · B data conversion · C leave | ✅ **A — implemented 2026-10-18** |
| D-AA | Armor form set (16 forms) | keep · consolidate | Keep |
| D-AB | Armor grade numbers | +1 primary stat/grade · res 1.15/1.25/1.35 · value +0/+1/+3 | As specced |
| D-AC | Accessory element→stat affinity | table in §3.3 | As specced |
| D-AD | Accessory grade numbers | res 1.05/1.10/1.15 · value +0/+1/+2 | As specced |
| D-AE | Armor/accessory traits | defensive-only · blueprint half-traits | Defensive-only now |
| D-AF | Res on enhance | none · small per-step | None |
| D-AG | Rarity caps | same as weapons (g1 rare / g2 epic / g3 any) | ❌ **Superseded 2026-10-19 by D-N** — soft ceiling: g1 epic 60% / legendary 15%, g2 legendary 40% |
| D-AH | Re-stat old armor/accessories | piggyback migration · leave instances | Piggyback |

---

## 11. Implementation record (2026-10-19)

- `resources/item_generation.py` composes armor and accessories at import time alongside weapons, into separate grade × element pools (`_ARMOR_POOLS`, `_ACCESSORY_POOLS`); `pick_family_id(family, grade, biome)` is now grade- and biome-aware and `pick_equipment_id` passes the floor's grade band.
- Armor: template + 1 primary stat/grade; res profile = element triangle (primary 1.15/1.25/1.35, secondary 1.05/1.10/1.15, drawback 0.85 fixed) padded to the form's entry count with 1.05 fillers (physical → earth → fire → magical → thunder → wind → water → light → dark); drawback entries only on Banded Mail, Plate Armor and Robes.
- Accessories: element→stat affinity (D-AC) with budget split on two-stat forms; +1 primary stat/grade; res primary 1.05/1.10/1.15 and secondary 1.00/1.05/1.10 — the secondary entry only appears from grade 2 (a 1.00 entry is a no-op).
- Value: `intrinsic_value` now honours a per-definition `grade_premium`, set by slot (+0/+2/+5 weapons, +0/+1/+3 armor, +0/+1/+2 accessories) at install time for generated **and** curated gear. Rarity caps are grade caps for every slot (D-AG; superseded 2026-10-19 by the soft ceiling, audit D-N).
- **Rarity/flower audit patch (2026-10-19):** hard grade caps → soft ceiling everywhere (armor/accessories included); tempering gold ×1.5/×2.5/×4 by rarity; scroll ceilings removed; shops never stock legendary below g3; Forge Commission added. See `docs/rarity_grade_flower_audit.md` §11.
- Curated armor/accessories keep their hand-tuned stats and receive inferred grades (prefix first, stat sum fallback) so caps/valuation work; they win id collisions, exactly like weapons. Uniques / Wonderland / black-market gear stay excluded from pools.
- Wired automatically everywhere `pick_equipment_id` / `pick_family_id` is used: city shops roll armor and accessories by city tier grade mix, dungeons/treasure/merchants/travel events/guild/world map use `pick_equipment_id`, wild dungeons pass their biome.
- **Curated armor/accessory definitions were retired alongside the weapons (2026-10-19):** every non-unique piece is generated; the hand-written nouns that are not grid coordinates moved to `LEGACY_ITEMS` for save compatibility and no longer drop or appear in shops. Owned gear is rescaled by `item_formula_version = 3`. See the weapons doc D-L.
- Tests: `tests/_diag_armor_grid.py` (every coordinate vs form template, res entry counts, affinity/budgets, premiums, caps, pickers, biome weighting, build path, pool exclusions).

---

*Implementation order: item economy ✅ → weapon grid ✅ → D-RES ✅ + armor/accessory grid ✅ → form perks (proposal awaiting approval).*
