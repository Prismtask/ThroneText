# Flower Infusion Rework — Playtest Checklist (2026-10-20)

> Covers everything shipped since the grade/tempering retirement (§12.10–12.11 of
> `rarity_grade_flower_audit.md`) plus the enemy-element normalization.
> Balance dials (enemy HP taper, deeper armor ladder, weapon tier 1.56) are
> **intentionally vaulted** — record measurements here, do not retune mid-run.

## 0. Prep

- [x] Back up `savefile/`.
- [x] Run the equipment diagnostics once before playing:
      `_diag_infusion.py`, `_diag_item_economy.py`, `_diag_unique_examine.py`,
      `_diag_weapon_grid.py`, `_diag_armor_grid.py`, `_diag_scroll_caps.py`,
      `_diag_retirement_temper.py`, `_diag_form_tags.py`, `_diag_form_perks.py`,
      `_diag_rarity_rates.py`, `_diag_enemy_elemental.py`.
- [x] Have save 1 “prism” (migration) + start a fresh save (new-game path).

---

## 1. Save migration (formula v4)

- [x] Save 1 loads without errors; inventory/equipment intact (no vanished gear).
- [x] Old grid gear became a base form + infusion: e.g. a “Inferno Greatsword”
      now reads as a Greatsword with fire ~1.48 (grade 3), ~1.25 (grade 2),
      ~1.10 (grade 1). Rarity and `+N` are preserved.
- [x] Old secondary element moved to slot 2 (value ≤ 1.20).
- [x] Legacy trophies / event items / wedding pieces are untouched (not converted).
- [x] Save, reload, load again — second load must change nothing (idempotent).
- [x] `item_formula_version: 4` present in the save JSON.
- [x] Fresh save: drops are base forms; no grade text anywhere in loot messages.

---

## 2. Loot, rarity & shops

- [ ] ~30 kills on a normal floor-10 dungeon: rarity mix looks like the band
      table (≈36/36/21/6/1 at Lv 6–10, softened), **no 100%-rare rooms**.
- [ ] Treasure room at floor ≤ 10 rolls a mix (pre-patch this was always rare).
- [ ] City shops never stock legendary (epic ceiling); stock refreshed once
      (`shop_stock3_` key bump) — visit 2–3 cities.
- [ ] Biome form bias: a volcanic run favours axes/hammers (≈3× weight);
      savanna favours the savanna list. Elements/flowers match the biome.
- [ ] Flower element blend: ~60% of flower drops are the defeated enemy's attack
      element, ~40% follow the biome — a tundra run against fire enemies should
      yield plenty of Emberbloom; neutral enemies drop biome-only.
- [ ] The dungeon header names the local craft ("Local crafts favour Axe, Hammer, …")
      in both the GUI and console runs; Event Horizon shows no hint (uniform loot).
- [ ] Bag → **Flowers (N)** tab lists each bloom with `xN` in element order; Key
      Items no longer contains flowers; the count updates after each run without
      pressing Refresh.
- [ ] Wild dungeons + world-map ruins roll **their own** biome (not the city's).
- [ ] Trap cache, wandering-monster drop, rose-painting cache, Cheshire gift:
      all produce valid base-form items with a legal rarity.
- [ ] Scrolls: apply one to an already-infused item → rarity changes, infusion
      values and `trait_tier` are preserved. No scroll is refused for “grade”.
- [ ] Guild / travel-event equipment rewards are base forms.

---

## 3. Blacksmith

### Enhance
- [ ] Caps: common +5, uncommon +6, rare +7, epic +8, legendary +10, unique +5.
- [ ] An item over the cap from an old save keeps its level but cannot enhance.
- [ ] Enhancing changes **stats only** — element values, infusion tiers and
      the trait do not move.

### Infuse Element (1 flower)
- [ ] Weapon primary ladder, same flower: 1.10 → 1.15 → 1.20 → 1.25 → 1.30 →
      1.35 → 1.40 → 1.48 (8 steps), then “slot at cap”.
- [ ] Trait unlocks at 1.25 (I), 1.35 (II), 1.48 (III); uninfused gear keeps
      the form's innate trait I.
- [ ] Second distinct flower starts slot 2 at 1.10, caps at 1.20.
- [ ] Third distinct flower starts slot 3 at 1.10, caps at 1.15.
- [ ] Fourth distinct flower **replaces** slot 3 (no error, no loss of the first two).
- [ ] Armor/accessory: same flower advances that slot's tier 1→3 (1.15/1.25/1.35 armor,
      1.05/1.10/1.15 accessory), then “cannot be strengthened further”.
- [ ] Armor/accessory also hold up to three elements: a new flower fills
      slot 2/3; a fourth distinct flower replaces slot 3 (first two kept).
- [ ] First slot is the piece's identity (name + form drawback); a later slot
      resisting the drawback element overrides it (max merge).
- [ ] Accessory stats keep their form affinity on infusion; flowers only add
      or merge elemental resistance.
- [ ] Item names move with the tier: Ember → Blaze (1.30) → Inferno (1.40);
      uninfused drops are plain (Common Greatsword).
- [ ] Uniques appear in the infusion list with their **primary locked**; flowers
        fill their two open slots (weapons: damage, armor: resistance, accessories:
        the profile(s) they authored).

### Commission (1 flower + 600 g)
- [ ] Family → form → element flow; result is a common item with the first
      infusion already applied; rarity is **not** included.
- [ ] Insufficient flower / gold / bag space / cancel paths behave.

### Transmute 3:1
- [ ] Exactly 3 of one flower become 1 of another, free; cancel changes nothing.

### Fuse
- [ ] Fee scales with rarity; unique premium is 12×; result rarity/level correct.

---

## 4. Elements in combat (post-normalization)

- [ ] Player basic attack logs/uses the weapon's **primary** element only.
- [ ] A skill of a different element picks up the weapon's matching secondary
      value (e.g. fire primary 1.48 + dark 1.20 → dark skills get 1.20).
- [ ] Same-element accessory: profile climbs toward the **2.0** clamp
      (fire weapon 1.35 + fire accessory 1.15 = 2.0). Confirm no overflow.
- [ ] Enemy HUD ⚔ tag shows one element; the elemental debuff it procs matches.
- [ ] Neutral enemies (e.g. `human_footpad`) deal no elemental damage and proc
      no elemental debuff.
- [ ] Enemy resistances still show multiple entries (weak/resist lines).
- [ ] EH run with an enemy-elemental trial card: neutral enemies do **not**
      suddenly deal fire (pre-fix bug).
- [ ] Resist convention: res > 1 takes less, res < 1 takes more; Steadfast form
      perk and Pierce trait still apply.

---

## 5. Traits (all nine)

Basic-attack-only (skills never proc traits). Check unlock at 1.25 / 1.35 / 1.48:

- [ ] Physical — Sunder armor pen 15 / 22 / 30%
- [ ] Fire — Ignite burn tier 2 / 4 / 5 (3 ticks; same-tier hits escalate +1)
- [ ] Water — Douse −1 / −2 / −3 cooldown on kill
- [ ] Thunder — Chain 15 / 25 / 35%
- [ ] Wind — Swift initiative +2 / +4 / +6
- [ ] Earth — Bulwark damage reduction 8 / 12 / 16%
- [ ] Light — Purge 1 / 2 / 3 debuffs
- [ ] Dark — Leech 8 / 12 / 16%
- [ ] Magical — Pierce 25 / 35 / 45% resistance bypass

---

## 6. Uniques

- [ ] Every unique weapon lists exactly one damage element at **1.35** and procs
        that element's **tier II** trait. Unique armor/accessories list exactly one
        primary damage/resistance element.
- [ ] Stat totals at +5: weapon **32**, armor **33**, accessory **26**.
- [ ] Enhancement caps at +5; flowers fill a unique's two open slots while its
        primary stays locked.
- [ ] Examine names the element a unique weapon strikes with and its trait tier
      (e.g. “This weapon causes Dark damage (×1.35 | Leech II).”); the unique's
      name itself is unchanged (no Ember/Blaze/Inferno word).
- [ ] Specials still fire: Vorpal (crit/execute), Abyss Fang (leech), Captain's
      Cutlass (High Tide/Rally), Black Silence gloves, Palette's Brush stances,
      Last Oath, Woodcutter/Grandmother axes.
- [ ] Unique examine panel shows correct mods/element/trait.

---

## 7. Allies

- [ ] Infusing an ally's weapon works via the blacksmith pool (equipped ally gear
      is listed).
- [ ] Ally basic attacks use their weapon's primary element; their skills use the
      skill's own element and read the ally's merged profile.
- [ ] Ally armor infusion raises their resistance in combat.
- [ ] Ally damage logs remain sane (no double-proc, no missing element).

---

## 8. Balance measurements (record, don't tune yet)

Fill these in before any dial is touched.

| Measurement | Where | Target | Actual |
|---|---|---|---|
| Hits to kill **End Bringer** (Lv 56, 820 HP) — legendary +10 weapon, primary 1.48, armor 1.35 | Endgame dungeon | 3–4 | |
| Hits to kill **Pit Sovereign** (EH) | EH run | fight 8–12 rounds | |
| % max HP lost per enemy hit at endgame | same fights | ≤ ~12% | |
| Midgame: hits to kill Lv 25–30 enemy (rare +7, primary ~1.30) | mid dungeon | 3–5 | |
| Early: hits to kill Lv 5 enemy (common +0) | starting area | 2–3 | |
| Burn share: total Ignite ticks vs direct hit at 1.48 fire | any fight | < 20% of hit | |
| Flowers per hour of normal farming | any biome | — | |
| Flowers for one full kit (weapon 13 + armor 3 + 3 accessories×3 = **25**) | — | 22–25 | |
| 3:1 transmute friction (how often it's needed) | — | occasionally | |

Vaulted dials (apply only after the table above):
- A. Enemy HP taper for Lv 30+ (`scaled_hp × 0.6` or `pandemonium_mult` 1.7 → 1.25).
- B. Deeper armor res ladder (add 1.45 / 1.55 / 1.65 tiers).
- C. Extra weapon tier (1.48 → 1.56).

---

## 9. Known gaps — do not report as bugs

- Inventory/examine cards don't show infusion values or trait tier numbers yet
  (the name word shows the tier; the blacksmith list shows exact values) —
  remaining work #5.
- Legendary drop rate is deliberately low; shops are epic-capped by design.
- Enemy HP / armor res depth are still grid-era targets — pending this playtest.

---

## 10. Regression smoke

- [ ] Combat: dummy TTK sim, a boss fight, an ally-heavy party fight.
- [ ] Shop buy/sell filters, sell prices for infused gear (no absurd values).
- [ ] Arcane Tower scroll crafting/application.
- [ ] Dungeon rooms: merchant, fountain, treasure, trap, wandering monster.
- [ ] Party swap, house, dispatch — quick sanity (items unchanged by this work).
