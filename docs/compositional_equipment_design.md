# Compositional Weapons — Form × Element × Grade (for review)

> **Status:** ✅ **Implemented 2026-10-18** — the Form × Element × Grade grid is live. **Form perks ✅ 2026-10-19** (4 slots, 5 with the Beating Root). **Unique form tags ✅ 2026-10-19 (D-J). Curated generics retired + canonical migration v3 ✅ 2026-10-19. Tempering & flowers ✅ 2026-10-19. Rarity soft ceiling, shop floor & Forge Commission ✅ 2026-10-19 (`rarity_grade_flower_audit.md`). Flower infusion rework ✅ 2026-10-20 — grade/tempering retired, base forms + infusion tracks (formula v4).**
>
> **⚠ GRADE MODEL RETIRED (2026-10-20).** This document is kept as the historical design record for the 2026-10-18 grid. The current equipment model is base forms + flower infusion — see `docs/rarity_grade_flower_audit.md` §12. Do not implement grade mechanics from the sections below.
> **Sequencing (user decision 2026-10-16):** item economy pass first (`docs/item_economy_tuning_design.md`), then this grid — both shipped 2026-10-18.
> **Companion design:** `docs/item_economy_tuning_design.md` · **Related:** `docs/ITEMS_OVERHAUL_BLUEPRINT.md` §3a (the 9×3 prefix table — already designed, never used as tiers), `docs/Pandemonium_Open_Improvements.md`.
>
> **User direction (2026-10-16):** full grid + weighted rolls · widen the grade gaps · keep current weapon types as forms (mechanical perks = later phase) · rarity stays · uniques untouched · economy first.
> **Rev 2 (2026-10-18):** enhancement still upgrades **elemental damage**, but **grade renaming is dropped** — a tempered Ember item sharing a name with a found Blaze/Inferno item created name collisions with very different stats (user concern). See §5.

---

## 1. Problem (verified against code, 2026-10-16)

- **Prefixes are cosmetic.** Every fire item carries `fire: 1.3` regardless of Ember/Blaze/Inferno; the only same-form ladder in the catalog is Iron Sword → Steel Sword. Blueprint §3a designed 9 elements × 3 tiers of prefixes; the implementation shipped them as one-off flavors.
- **`weapon_type` does nothing.** It is consumed in exactly one place (`combat/weapon/dopo_robe.py`); otherwise a hammer and a dagger differ only in numbers.
- **Choice space is thin.** 40 generic weapons; per (stat + element) usually 1–2 options; stats span 2–5 points; element entries 1.1–1.3. Rarity + enhance carry all scaling.
- **Value formula mismatch.** Under the new economy formula, element-poor physical weapons get a value penalty relative to element-rich ones, yet nothing about them is "better" — structure doesn't express intent.

## 2. The model

**Weapon instance = Form × Element × Grade**, with **Rarity** and **Enhance** as the separate quality/investment axes.

| Axis | Owns | Values |
|---|---|---|
| **Form** | scaling stat, stat template, base damage entry, (future perk) | ~28 entries = (weapon_type, scaling) pairs, incl. a few established variants |
| **Element** | Trait + damage identity | 9 (physical included) |
| **Grade 1–3** | ~~Prefix family; stat bonus, element strength, value premium~~ — **retired 2026-10-20** | — |
| **Rarity** | Roll quality: ×stat, ×value, ×element, trait tier — **capped by grade** | 5 |
| **Enhance** | Investment: +stat, **+elemental damage**, grade-name evolution | +10 |

- Grid size: ~28 × 9 × 3 ≈ **750 variants** (vs 40 today). Names & IDs are deterministic: `{prefix}_{form}` — **the existing catalog is already a hand-picked subset of the grid** (`iron_sword` = sword/physical/1, `steel_sword` = sword/physical/2, `inferno_greatsword` = greatsword/fire/3).
- Prefixes: reuse the blueprint §3a table as-is (Physical Iron/Steel/Titan · Fire Ember/Blaze/Inferno · Water Frost/Glacier/Abyssal · Thunder Spark/Storm/Tempest · Wind Gale/Zephyr/Cyclone · Earth Stone/Grave/Bedrock · Light Radiant/Divine/Solar · Dark Shadow/Void/Nether · Magical Arcane/Mystic/Astral).

## 3. Templates & formulas (all numbers tunable)

```
grade_stat    = +2 × (grade − 1)                  # applied to the form's primary stat
grade_element = 1.10 / 1.30 / 1.50                # wider gap (user request)
value premium = +0 / +2 / +5                      # added to economy intrinsic_value

stat_final    = int( (form_stat + grade_stat + enhance) × rarity_mult )          # economy Option A
element_final = 1.0 + ( grade_element + 0.02 × enhance − 1.0 ) × rarity_mult     # enhancement upgrades element
```

**Form templates (draft — one scaling per form; variants marked):**

| Form | Scaling | Template (draft) | Today's example |
|---|---|---|---|
| sword | STR | STR 2 | Iron/Steel Sword |
| greatsword | STR | STR 4 | Inferno Greatsword |
| axe | STR | STR 4 | Blaze Axe |
| flail | STR | STR 3, CON 1 | Ember Flail |
| hammer | STR | STR 4 | Storm Hammer |
| mace | STR | STR 3, WIS 1 | Stone Mace |
| maul | STR | STR 4, CON 1 | Grave Maul |
| spear | STR | STR 3, DEX 1 | Gale Spear |
| halberd | STR | STR 4, DEX 1 | Zephyr Halberd |
| shield | CON | CON 3 · `scaling_mult 0.5` · `con_defense` | Titan Shield / Stone Plate |
| gauntlets | CON | CON 2, STR 1 · `scaling_mult 0.5` · `con_defense` | Magma Gauntlets |
| dagger (DEX) | DEX | DEX 3 | Shadow Dagger |
| dagger (CHA) ᵛ | CHA | CHA 3, DEX 2 | Shadow Tongue Dagger |
| blade (STR) | STR | STR 4, DEX 2 | Frost Blade / Void Blade |
| blade (LRN) ᵛ | LRN | LRN 3, WIS 2 | Nether Blade |
| rapier | DEX | DEX 4, CHA 1 | Zephyr Rapier |
| bow | DEX | DEX 4 | Rime/Gale Bow |
| crossbow | DEX | DEX 3, LRN 1 | Cyclone Crossbow |
| chakram | DEX | DEX 3, STR 1 | Volt Chakram |
| staff (WIS) | WIS | WIS 4 | Divine Staff |
| staff (LRN) ᵛ | LRN | LRN 4 | Arcane Staff |
| wand | LRN | LRN 2, WIS 1 | Thunder Wand |
| orb (LRN) | LRN | LRN 3, CHA 1 | Torrent Orb |
| orb (WIS) ᵛ | WIS | WIS 3, LRN 1 | Astral Orb |
| scepter | WIS | WIS 3, CHA 2 | Glacier Scepter |
| grimoire | LRN | LRN 4 | Nether Grimoire |
| lute | CHA | CHA 4, LRN 1 | Blaze/Radiant Lute |
| harp | CHA | CHA 3, DEX 2 | Zephyr Harp |
| bell | CHA | CHA 3, LRN 2 | Mystic Bell |

ᵛ = scaling variant (same noun, second scaling) — see D-A2. Unique-only shapes (fang, cutlass) stay outside the grid.

**Worked examples (Greatsword / STR 4, fire):**

| Item | STR | fire multiplier | Notes |
|---|---|---|---|
| Ember (g1) common +0 | 4 | 1.10 | starter tier |
| Inferno (g3) common +0 | 8 | 1.50 | grade gap: ×2 stats, ×1.36 element |
| Ember (g1) legendary +10 | int((4+0+10)×1.9) = **26** | 1.0+(0.10+0.20)×1.9 = **1.57** | tempered: +10 element = exactly one grade step (0.2); name stays "Ember" (§5) |
| Inferno (g3) legendary +10 | int((4+4+10)×1.9) = **34** | 1.0+(0.50+0.20)×1.9 = **2.33** | top of chain (vs 28 / 1.57 today — playtest dial) |

## 4. Generation & rolls

Roll order: **form → element → grade → rarity** (rarity softened by the grade's soft ceiling).

- **Grade gating (dungeons + wild dungeons):** floors ≤10 → grade 1 · 11–25 → grade 2 · 26+ → grade 3. (Mirrors the economy doc's treasure bands.)
- **Shops (extends economy §3.3 tiers):** early cities → g1 only · mid → g1 70 / g2 30 · late → g1 40 / g2 35 / g3 25.
- **Rarity soft ceiling (D-N, supersedes D-E):** g1 → epic survives 60%, legendary 15% · g2 → legendary 40% · g3 → any. A demoted rarity steps down one tier and is re-checked (`soften_rarity`).
- **Element weights:** weighted, not walled — regional themes bias (volcanic → fire/earth; coast → water/wind; etc., reusing `wild_dungeon_themes` biome identity); off-theme combos stay possible but rare.
- **Form weights:** near-uniform with light city/theme bias.
- **Code:** new `resources/item_generation.py` (`compose_item(form, element, grade, rarity, enhance)` + weighted rollers); replaces `dungeon.py` `_EQUIP_POOL`/`roll_drop` equipment path, `resources/items.random_equipment()`, shop/merchant stock rolls, treasure rooms.

### 4.1 Drop chances — grade vs rarity vs element (verified 2026-10-19)

- **Grade is not rolled per item.** Dungeons derive it from the floor: ≤10 → g1 · 11–25 → g2 · 26+ → g3. Shops roll the city-tier grade mix. Every item in a given dungeon therefore shares the same grade.
- **Rarity is rolled per item** from the same weights for every item of that grade, then softened by the grade's soft ceiling (D-N): on g1 an epic survives 60% of rolls and a legendary 15%; on g2 a legendary survives 40%; g3 is unrestricted. A demoted roll steps down one tier and is re-checked. A Legendary Ember or Legendary Blaze can therefore drop — rarely — and the old “only Inferno can be legendary” rule is gone.
- **Scroll fusion is not grade-capped (superseded 2026-10-19, audit D-N).** The old “Temper it to a higher grade first” refusal and the matching check in `inventory.apply_scroll_to_item` were both removed; a scroll can finish any rarity on any graded item. The intended loop is still **temper for grade → scroll for rarity → enhance for investment**, now as a cost preference rather than a hard rule (tempering gold scales ×1.5/×2.5/×4 by rarity).
- **Element is biome-weighted, form is uniform.** Within one grade, every element has the same rarity distribution; the biome decides how often fire vs water vs dark appears (volcanic → fire/earth, tundra → water/wind, pandemonium → dark/fire/magical…). Form is currently a flat pick across the whole grade pool.
- **Flowers use the same element weights**, so a volcanic dungeon is also the best place to farm Emberbloom for fire tempering.

### 4.2 Flower sourcing — how each core item is farmed (2026-10-19)

Flowers are `crafting_material` items: they stack, take no bag space, and are **never sold in shops**. Every element has one:

| Element | Flower | Best farming biomes (weight ≥ 2) |
|---|---|---|
| physical | Ironbriar | mountain (3× earth, 2× physical) |
| fire | Emberbloom | volcanic (3), desert (3), savanna (2), pandemonium (2) |
| water | Frostlotus | tundra, swamp, coastal, sea caves (3), tropical (2) |
| thunder | Stormlily | coastal (2), sea caves (2), everywhere else 1 |
| wind | Galeorchid | tundra, forest, savanna, coastal (2) |
| earth | Stonebloom | mountain (3), swamp/volcanic/forest/savanna/desert/tropical (2) |
| light | Sunpetal | wonderland (2), otherwise 1 |
| dark | Nightbloom | pandemonium (3), swamp/wonderland (2) |
| magical | Manabloom | magical (3), pandemonium/wonderland (2) |

Every biome gives every element at least weight 1, so **all nine flowers can drop anywhere** — the table only says where each is most likely.

**Sources (all implemented):**
- **Every enemy kill** in a dungeon or wild dungeon makes one drop roll: 50% nothing (30% in Pandemonium), then a 12% flower branch → **≈ 6% per kill** normally, **≈ 8.4%** in Pandemonium.
- **Treasure rooms** always contain one flower in addition to the guaranteed gear.
- **Wild-dungeon completion reward pools** re-roll drops, so flowers can appear as listed rewards.
- The **Mad Hatter** extra-drop roll can also yield a flower.
- Shops, travel events, guild discoveries and world-map encounters do **not** sell or drop flowers.


## 5. Enhancement ↔ Element (Rev 2 — no renaming)

- Each enhancement step: **+1 stat** (economy rule) **+0.02 elemental damage** (pre-rarity; +10 = exactly one grade step's worth of element).
- **The found grade prefix never changes.** An Ember Greatsword +10 stays "Ember Greatsword +10" even though its element now matches a found Blaze.
- Why the rename was dropped (user concern 2026-10-18): natural grade-3 weapons already spawn (§4), and a renamed tempered item collides with them **in name only** — a found Blaze +0 has STR 11 while a tempered Ember +10 has STR 26; found Inferno +10 reaches element 2.33 vs the tempered Ember's 1.57. Same name, very different power/value = unreadable and mispriced. Grade must remain a truthful found-tier label.
- **Tempering (implemented 2026-10-19):** the blacksmith raises a found grade by one step (g1 → g2 → g3) for gold + element flowers. **g2: 3 flowers + 1,200g · g3: 6 flowers + 3,000g** (city discounts apply); gold scales with rarity (×1.5 rare · ×2.5 epic · ×4 legendary). Enhancement and rarity are preserved. The form and element never change — a fire item can only become a stronger fire item; there is no service that converts elements. This is the intended fallback for players who cannot find a g3 legendary naturally. **Forge Commission (2026-10-19):** one matching flower + 600g buys a common g1 piece of any chosen form/element — the deterministic route to a *base*, leaving rarity and grade to luck/gold.
- Value rises automatically (economy `intrinsic + enhance`); element **magnitude** is not in the value formula — enhancement's element gain is a power gain, not a price gain (acceptable; revisit if desired).

### 5.1 Using flowers and scrolls together — the cost stack (2026-10-19)

**They are complementary, not alternatives:** flowers raise **grade** (and with the scroll change they no longer gate rarity), scrolls raise **rarity**, enhancement raises **stats and element**. Both can be used on one item in any order — the old grade-ceiling refusal is gone (D-N) — but tempering gold scales with rarity, so it is cheapest to temper a common base and scroll it afterwards.

Worked total for a **fresh grade-1 Ember Greatsword → grade-3 Legendary Inferno Greatsword +10**:

| Step | Cost |
|---|---|
| Temper g1 → g2 | 1,200g + 3× Emberbloom (rare → epic ceiling) |
| Temper g2 → g3 | 3,000g + 6× Emberbloom (epic → any ceiling) |
| Craft Legendary Scroll (Arcane Tower) | **80,000g + sacrifice 4 legendary items** (epic: 30,000g + 4 epics · rare: 12,000g + 4 rares) |
| Blacksmith fusion fee | 50 × value delta → **4,900g** at +0, **8,400g** at +10 |
| Enhance to +10 | ≈ **68,000g** (50 × 8.0 × 1.5ⁿ summed over n=1..10) |
| **Total** | ≈ **165,000g + 9 flowers + 4 legendaries** |

For comparison, the finished item's shop price is only ≈ 2,160g (value 192 × base 45 ÷ 4) and it sells for ≈ 480g. Items are cheap; **services are the gold sink** — that is the intended split, not an inconsistency.

**Why the fusion fee is *not* raised to match the scroll:** the fee prices the value added to the item (50 per value point), while the scroll's craft cost is the rarity gate. At 4,900–8,400g the fee is already 6–10% of an 80,000g legendary scroll; raising it would charge twice for the same rarity jump. If the whole path should cost less or more, the lever is `_scroll_craft_cost()` (2k / 5k / 12k / 30k / 80k) or the enhance curve — not the fee.

**Order is now a cost preference, not a legality rule:** the old cap made scroll-first on a g1 item stop at rare; since D-N a scroll may finish any rarity at any grade. Temper first anyway when planning ahead: tempering gold scales with rarity, so tempering a common base and scrolling it after is the cheapest sequence.

## 6. The four concerns, answered

1. **Should each form have an effect?** **Yes — implemented 2026-10-19.** With elements as the trait layer, forms would otherwise be just stat shapes.

### 6.1 Form perks — implemented v2 (2026-10-19)

**Separation of layers.** Elements own *procs* (Sunder / Ignite / Chain / Swift / Bulwark / Leech / Pierce…). Forms own **static, always-on modifiers**. No form perk adds a proc, a new status, or a boss-immunity rule.

**Vocabulary (all reuse existing primitives, verified in code):**

| Code | Effect | Existing primitive / hook |
|---|---|---|
| Keen | +X% critical chance | `crit_chance` buff type · `get_raw_critical_chance` |
| Brutal | +X critical damage (multiplier) | `crit_damage` buff type · `resolve_critical_chance` |
| Cleaving | +X% damage dealt | one multiplier in the shared damage pipeline |
| Sundering | +X% armour penetration | same field as the physical Sunder trait (additive) |
| Guarded | −X% damage taken | `damage_reduction` effect type · `get_race_damage_reduction` |
| Nimble | +X% dodge | `evasion` effect type · `get_dodge_chance` |
| Swift | +X initiative | flat bonus in `roll_initiative` (same pattern as gloves/brush) |
| Focused | +X% magical damage | damage-pipeline multiplier, magical axis only |
| Mending | +X% healing/regen | healing/regen amount hook |
| Steadfast | +X rating to the item's primary element | resistance rating space (higher = stronger) |

*Conditional perks (Opener / Executioner / Opportunist) were dropped on 2026-10-19 — they need uptime assumptions and cannot be priced predictably.*

**Weapon mapping (29 forms):**

| Form | Perk | Form | Perk |
|---|---|---|---|
| Sword | Keen +5% | Rapier | Keen +8% |
| Greatsword | Cleaving +10% | Bow | Keen +8% |
| Axe | Brutal +15% | Crossbow | Sundering +10% |
| Flail | Cleaving +8% | Chakram | Swift +2 |
| Hammer | Sundering +10% | Staff | Focused +8% |
| Mace | Sundering +10% | Greatstaff | Focused +10% |
| Maul | Cleaving +10% | Wand | Focused +6% |
| Spear | Swift +2 | Orb | Focused +8% |
| Halberd | Sundering +12% | Focus Orb | Mending +10% |
| Shield | Guarded −8% | Scepter | Mending +8% |
| Gauntlets | Guarded −6% | Grimoire | Focused +10% |
| Dagger | Keen +10% | Lute | Mending +10% |
| Tongue Dagger | Brutal +15% | Harp | Mending +8% |
| Blade | Cleaving +8% | Bell | Swift +2 |
| Spellblade | Focused +8% | | |

**Armor mapping (16 forms):** Guarded — Plate −6%, Banded −5%, Chainmail/Scale −4%, Battle Harness −3%, Runic Plate −5% · Nimble — Silk Garb +5%, Wraps +4%, Leathers/Elven Mail +4%, Padded +3% · Focused — Robes +6%, Regalia +4% · Mending — Vestments +6%, Fur Mantle +5% · Steadfast — Dragonhide (+0.05 rating).

**Accessory mapping (17 forms):** Keen — Ring +4%, Signet +4%, Gloves +4%, Monocle +4%, Eye +4% · Brutal — Band +6% · Nimble — Cloak +4%, Talisman +3% · Guarded — Belt +3%, Bracers +3% · Mending — Pendant +4%, Brooch +4% · Focused — Crown +4%, Tome +4% · Swift — Boots +1, Earring +1 · Steadfast — Amulet (+0.04 rating).

**Stacking & scope rules (revised 2026-10-19):**
- **All equipped slots activate.** Weapon, armor, accessory1 and accessory2 each contribute their form's perk — **4 active perks by default, 5 once the actor has consumed the Beating Root** (`acc3_unlocked`, the third accessory slot).
- Two pieces with the same archetype stack additively (e.g. a Keen weapon plus a Keen ring); different channels are independent.
- Actor-based: allies receive the perks of what they hold (the helpers already read the entity).
- **Uniques are form-tagged (D-J)** and participate normally — their hand-tuned stats and specials are untouched.
- **Every equipment piece is form-tagged, so every piece can carry a perk.** Composed grid items take the form from the loop; curated (hand-written) generics infer it from the id suffix (`ember_dragonhide` → Dragonhide) and fall back to an explicit table when the noun is not a form key — Magma Locket → Amulet, Cyclone Anklet → Band, Blaze Gauntlets → Gloves, Stone Plate → Shield, Captain's Hook → Dagger, Broomstick → Staff. Uniques use the D-J table (wedding lockets → Amulet, signets → Signet, veils → Cloak…). Nothing is left out.
- Magnitudes are playtest dials; the vocabulary and mapping are the thing to lock.

**Approval checklist (updated):** (1) vocabulary of 10 static archetypes, with conditionals removed · (2) the 29/16/17 mapping, including Greatsword → Cleaving, Axe → Brutal, Hammer → Sundering · (3) all-equipped stacking (4, or 5 with the Beating Root) · (4) magnitudes as a first pass.

**Implemented (2026-10-19).** `combat/form_perks.py` holds the data table and resolver; hooks: Keen/Brutal in `get_raw_critical_chance` / `resolve_critical_chance`, Nimble in `get_dodge_chance`, Guarded in `enemy_ai`'s damage application, Swift in `roll_initiative`, Steadfast in `calculate_elemental_damage`, Mending in `apply_healing`, and Cleaving/Focused/Sundering in the four damage pipelines (player basic, ally basic, player skills, ally skills). Examine and merchant/dropped-item lines show the tradition. Perks never scale with grade/rarity/enhance. Test: `tests/_diag_form_perks.py`.

2. **Is rarity kept?** **Yes.** Layering: *grade* = found base power tier (stats + element + value); *rarity* = roll quality multiplier (stat/value/element scaling + trait tier, unchanged); *enhance* = investment (stats + element + name). Grade caps which rarities can roll — junk-base legendaries die structurally.
3. **Uniques?** **Stats and specials untouched; they now carry form tags (D-J, 2026-10-19).** Excluded from the grid, caps, composition, and enhancement coupling; keep hand-tuned stats, red tier, specials. Every unique now has a `form` — noun-based where the name is clear (Vorpal Blade → blade, Tarnished Jade → runic_plate) and description-based where it isn't (Sky Piercer → talisman, Prescript Ledger → tome, Witch's Hat → crown). Heroine, wedding, quest and Wonderland gear are included, so uniques inherit form perks instead of being locked out of the layer.
4. **Progression?** Three visible, independent axes now:
   - **Grade = depth.** Early floors show Ember/Frost/Gale families; mid adds Blaze/Glacier/Zephyr; deep adds Inferno/Abyssal/Cyclone. Prefixes finally read as progression.
   - **Rarity = luck**, capped by grade (g1 can never be legendary).
   - **Enhance = investment**, now also raising elemental damage (name/grade unchanged — see §5).
   - Player loop: find your form+element at the best grade → chase its rarity ceiling → temper it; scroll fusion keeps working unchanged (rarity targeting on your chosen base).

## 7. Interactions & migration

- **IDs:** deterministic `{prefix}_{form}`. **Curated generics are retired (2026-10-19):** every non-unique equipment piece is now generated from its coordinate; the 12 hand-written nouns that are not coordinates (`magma_locket`, `cyclone_anklet`, `blaze_gauntlets`, `stone_plate`, `hook_hand`, `broomstick`, `rime_bow`, `volt_chakram`, `torrent_orb`, `thunder_wand`, `magma_gauntlets`, `spark_hand_crossbow`) live in `LEGACY_ITEMS` for save compatibility and no longer drop or appear in shops.
- **Re-stat decision (D-F) — implemented:** `item_formula_version = 3` rescales every owned non-unique item to the canonical grid formulas on load (name included). Legacy-only items are kept as trophies but cannot temper.
- **Economy doc cross-updates when this ships:** intrinsic gains the grade premium; base-tier caps restate as grade caps; drop/shop weight tables replaced by composition rolls. (`random_equipment()` and `dungeon._EQUIP_POOL` are now unused by the equipment economy.)
- **Unchanged:** consumables, enhancement costs, fusion rules, blacksmith, heroine/wedding/quest gear stats and specials (only form tags were added, D-J).
- **Deferred:** dungeon form identity (§10 — proposal) and any further tempering cost tuning.
- **Tests:** grid sanity (every form×element×grade composes; budgets in bounds), weighted-roll distribution sampling, rarity-cap enforcement, id/name generation, migration idempotency, balance sim vs today's top-end (flag: g3/legendary/+10 is ~21% above current top-end — tune dials in playtest).

## 8. Decisions (LOCKED 2026-10-18 — as recommended)

| # | Decision | Options | Recommendation (user-leaning marked) |
|---|---|---|---|
| D-A | Form set | keep ~28 (weapon_type, scaling) entries · consolidate nouns | **Keep** (user said yes); consolidation optional later |
| D-A2 | Scaling variants (same noun, 2nd scaling — dagger CHA, blade LRN, staff LRN, orb WIS) | allow · force one scaling per noun | Allow — already established by existing items |
| D-B | Grade numbers | stats +2/step · element 1.10/1.30/1.50 · value +0/+2/+5 | As specced (user: widen the gap) — playtest dial |
| D-C | Enhance ↔ element | A: +0.02 element/step, no rename (Rev 2) · B: element + explicit promotion ritual later · C: rename (dropped) | **A**; B as a later option |
| D-D | Grade gating | floors ≤10 / 11–25 / 26+; shop mixes above | As specced |
| D-E | Rarity caps | g1 rare · g2 epic · g3 any (restates economy D3) | ❌ **Superseded 2026-10-19 by D-N** — soft ceiling: g1 epic 60% / legendary 15%, g2 legendary 40% |
| D-F | Re-stat old generic items | migrate (piggyback economy pass) · leave instances | Migrate |
| D-G | Form perks | Phase 3, list in §6.1 | ✅ **Implemented 2026-10-19** — conditionals removed, all-equipped stacking (4/5 slots), 10 archetypes |
| D-H | Regional element weight table | draft from `wild_dungeon_themes` | Lock at implementation |
| D-I | Armor/accessories on same machinery | Phase 4 later · include now | Later |
| D-J | Unique form tags | name/noun only · description-based where ambiguous · none | ✅ **All 92 uniques tagged 2026-10-19** (description-based for ambiguous names) |
| D-K | Tempering service | grades g2/g3 · flower counts · element lock | ✅ **Implemented 2026-10-19** — 3 flowers + 1,200g for g2, 6 flowers + 3,000g for g3; element/form locked; enhancement+rarity preserved |
| D-L | Curated generic retirement | keep overrides · retire all non-uniques | ✅ **Retired 2026-10-19** — generated grid is canonical; 12 non-coordinate nouns kept in `LEGACY_ITEMS`; owned gear migrated (v3) |
| D-M | Scrolls vs grade ceilings | enforce cap · bypass cap | ❌ **Superseded 2026-10-19 by D-N** — scrolls are uncapped; both refusal sites removed |

---

## 9. Implementation record (2026-10-18)

- `resources/item_generation.py` builds the grid at import time: 29 forms × 9 elements × 3 grades, deterministic `{prefix}_{form}` ids, name `<Prefix> <Form>`. Colliding ids (`ember_flail`, `iron_sword`, …) are skipped — **curated items win** and are annotated with an inferred `grade` used only for caps/valuation.
- Grade math: +2 primary stat per step, element 1.10/1.30/1.50; value premium +0/+2/+5 (`intrinsic_value`); rarity caps g1→rare, g2→epic, g3→any (`cap_rarity_for_item`).
- Generation helpers: `pick_weapon_id(grade, biome)` / `pick_equipment_id(level, biome)`; `grade_for_level` bands ≤10 / 11–25 / 26+; `roll_shop_grade(tier)` mixes [100,0,0] → [70,30,0] → [40,35,25]; biome element weights for 14 regions.
- Wired into: city shops (58% equipment mix), dungeon drops, treasure/merchant rooms, travel events, guild discovery, and world-map encounters. `dungeon._EQUIP_POOL` is now unused (kept for reference).
- Enhancement adds +0.02 element/step through the shared `compute_elemental_dmg` (no rename); owned gear re-migrated via `item_formula_version = 2`.
- **D-F deviation:** curated weapons keep their hand-tuned stats rather than being re-stat'ed; the grid fills every missing coordinate. Re-statting would have invalidated playtested boss/quest rewards.
- Tests: `tests/_diag_weapon_grid.py` (grid, caps, pickers, enhancement), `tests/_diag_item_economy.py` (valuation, fees, migration).
- **Form tags (D-J, 2026-10-19):** every equipment definition (1,844 pieces) now carries `form` — composed items from the form loop; curated generics inferred from the id suffix (longest match, e.g. `shadow_tongue_dagger` → `tongue_dagger`) with `CURATED_FORM_TAGS` covering the six nouns the suffix cannot infer (Magma Locket → amulet, Cyclone Anklet → band, Blaze Gauntlets → gloves, Stone Plate → shield, Captain's Hook → dagger, Broomstick → staff); and all 92 uniques from `UNIQUE_FORM_TAGS` (ambiguous names mapped by description). `build_item` copies the tag onto instances. Tests: `tests/_diag_form_tags.py` (asserts zero untagged equipment).
- **Form perks (D-G, 2026-10-19):** `combat/form_perks.py` resolves perks from every equipped slot (weapon, armor, accessory1/2, plus accessory3 when `acc3_unlocked`), validating that an item's slot matches the channel. Hooks are listed in §6.1; perks are static (no grade/rarity/enhance scaling) and never enter `intrinsic_value`. Display via `describe_item_perk()` in examine popups and merchant lines. Test: `tests/_diag_form_perks.py`.
- **Retirement + canonical migration (D-L, 2026-10-19):** `install_grid()` moves all non-unique hand-written equipment out of `ITEMS`; coordinate ids are regenerated with canonical stats, the 12 non-coordinate nouns go to `LEGACY_ITEMS` (build/lookup fall back, forms preserved). `item_formula_version = 3` rescales owned gear and refreshes names. `intrinsic_value` falls back to an instance's `mods` for legacy pieces. Test: `tests/_diag_retirement_temper.py`.
- **Tempering + flowers (D-K, 2026-10-19):** nine `crafting_material` flowers (`FLOWER_ITEMS`, one per element) drop from enemy drops (12% of drop rolls, biome-weighted) and always from treasure rooms; never sold in shops. `facilities/blacksmith.py` — `temper_target_id()` derives the same-element next-grade id, `TEMPER_REQUIREMENTS` = 3 flowers/1,200g (g2) and 6/3,000g (g3), `make_tempered_item()` preserves rarity/enhancement, and the forge menu has a “Temper (Raise Grade)” entry. Element/form are locked by construction. Test: `tests/_diag_retirement_temper.py`.
- **Scroll grade ceilings (D-M, 2026-10-19):** `inventory.apply_scroll_to_item()` refuses any rarity above `cap_rarity_for_item(item, target)` and resolves definitions through `_lookup_item_def()` (legacy items included); the blacksmith pre-checks and explains the refusal before charging the fee. Test: `tests/_diag_scroll_caps.py`.
- **Rarity/flower audit patch (2026-10-19):** hard grade caps replaced by the soft ceiling (`GRADE_RARITY_PASS` / `soften_rarity`, D-N); shops never stock legendary below g3; tempering gold ×1.5/×2.5/×4 by rarity; dungeon loot uses `dungeon_biome` (fixes wild/world-map ruins); the four un-gated dungeon-room roll sites use the grade-gated pipeline and `_random_item_id` was deleted; both scroll ceiling checks removed; Forge Commission added (1 flower + 600g for a common g1 form/element base). Full record: `docs/rarity_grade_flower_audit.md` §11.
- **Flower infusion rework (2026-10-20, `rarity_grade_flower_audit.md` §12):** grade and tempering retired. Drops are 62 base forms; rarity is stats-only (×1.0–1.4) and enhance is stats-only. Flowers set elements in the blacksmith (“Infuse Element”): weapons hold primary (1.10→1.48, traits at 1.25/1.35/1.48), secondary (≤1.20) and tertiary (≤1.15); armor/accessories hold one element with 3 res tiers. All nine traits gained infusion ladders. `item_formula_version = 4` migrates owned grid gear to base form + infusions; grid defs remain dormant for one chapter. Test: `tests/_diag_infusion.py`.

## 10. Dungeon form identity — proposal (not implemented)

> **Sequencing (2026-10-20):** this ships **together with the B+C flower rework** (`rarity_grade_flower_audit.md` §12.6), not before it. The rework shrinks the drop pool to ~558 base forms, which makes form weighting flavor instead of a fix — building it on the current 1,673-coordinate grid would be throwaway work. Forge Commission covers the deterministic-base need until then.

**Goal:** make a dungeon's theme readable from its loot, so a player can farm a specific *form* instead of rolling the whole catalog. Today only the element is biome-weighted; form is a flat pick.

**Recommendation: weight, do not wall (option A).** A hard restriction (option B) can starve a build that needs a form the theme lacks, and turns “farm this form” into “wait for the right dungeon to spawn”. Option A keeps every form possible while making the themed ones ~3× more likely. Shops inherit the city's biome, so the same table gives cities a smithing identity too.

| Biome | Preferred weapon forms | Rationale |
|---|---|---|
| tundra | spear, crossbow, greatstaff, harp | reach and cold-weather gear |
| temperate | sword, greatsword, shield, bow | balanced frontier kit |
| swamp | dagger, tongue dagger, mace, orb | close, dirty fighting |
| mountain | hammer, maul, shield, halberd | weight and formation |
| magical | staff, greatstaff, grimoire, orb | arcanist country |
| volcanic | axe, hammer, flail, greatsword | forge-born heavy weapons |
| forest | bow, spear, dagger, lute | hunt and song |
| savanna | spear, chakram, axe, rapier | open-ground skirmish |
| coastal | rapier, crossbow, orb, harp | duelist and sailor kit |
| desert | axe, chakram, spear, wand | light travel gear |
| tropical | dagger, bow, chakram, bell | quick, mobile fighting |
| sea caves | spear, dagger, orb, wand | tight tunnels, damp magic |
| pandemonium | tongue dagger, axe, flail, grimoire | brutal and arcane |
| wonderland | rapier, wand, lute, bell | storybook elegance |

Armor and accessory forms can follow the same table (heavy silhouettes in mountain/volcanic, cloth in magical/forest, regalia in wonderland). Flowers already use the biome element weights, so form bias and flower farming would point the same direction.

**Implementation sketch (when approved):** `FORM_WEIGHTS_BY_BIOME` in `resources/item_generation.py`; `pick_weapon_id` / `pick_family_id` multiply the weight of listed forms by 3 and leave the rest at 1; shops inherit the city biome. Element weights stay unchanged.

---

*Implementation order: economy ✅ → grid ✅ → D-RES ✅ → armor/accessories ✅ → form tags ✅ → perks ✅ → retirement/tempering ✅ → rarity/flower audit ✅. Open: dungeon form identity (§10).*
