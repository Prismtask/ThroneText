# Rarity × Grade × Flowers — Audit & Patch Plan (for review)

> **Status:** ✅ **Implemented 2026-10-19** — P1–P7 shipped and verified against the repo. Corrections to the original proposal (the §2.6 diagnosis, the cache-key name, site counts) are recorded in §11.
> **Date:** 2026-10-19
> **Trigger:** the grid (Form × Element × Grade) diluted the chance of finding a *specific* item; flowers were added as the alternative route, but the grade↔rarity cap and the flower role no longer fit together.
> **Rev 2 (2026-10-19):** `travel_events.py`, `inventory.py` and `status_effects.py` reviewed — §2.3 (Ignite saturation), §2.9 (leaks confirmed), P5/P6 (exact edits), new P10, §10 updated.
> **Reviewed:** `item_generation.py`, `items.py`, `dungeon.py`, `dungeon_rooms.py`, `shop.py`, `blacksmith.py`, `elemental_traits.py`, `elemental.py`, `travel_events.py`, `inventory.py`, `status_effects.py`, plus the three design docs.
> **Not reviewed:** Arcane Tower scroll crafting, `city.py`, `leveling.get_current_city_id`, `guild.py`, `world_map_screen.py`, `enemies.py` (see §10).
> **Companions:** `compositional_equipment_design.md` · `compositional_armor_design.md` · `item_economy_tuning_design.md`

---

## 1. TL;DR

1. **Two problems got tangled.** (A) *Dilution* — the grid made your exact form + element rare. (B) *Ceiling* — the cap made high rarity impossible on low grades, so a g3 legendary became the only legendary. Flowers were built to patch (B). Nothing patches (A).
2. **The cap is the root of (B), and it is a clamp, not a reroll.** It quietly moves probability mass down instead of making anything scarcer, and the treasure tables at floor ≤10 are effectively decorative.
3. **Grade and rarity are not independent in the pipeline.** Both are derived from the same number (`enemy_level` / `floor`). That is why the design feels like one axis counted twice.
4. **Rarity already has its own job in code: traits — but it is uneven.** Elemental traits scale with rarity only, never grade. Chain, Swift, Bulwark, Leech and Pierce scale linearly; **Ignite saturates at epic** (§2.3) and Physical's Sunder does not scale at all. So a g1 legendary is a real trade-off for most elements, but mostly a fodder/jackpot item for fire and physical. Removing the cap is still the right direction — but *only with soft scarcity*, otherwise Pandemonium floods with legendaries (§2.2).
5. **Flowers should stop being "the alternative to luck for grade" and become the answer to dilution** (a forge commission keyed to the flower's element), while still working as the grade sink for tempering.
6. **Several smaller bugs/leaks are real** (biome plumbing, un-gated drop sites, shop legendary fodder). Ordered patches are in §5.

### Corrections to my earlier chat messages

| What I said | What the code shows |
|---|---|
| "9 flowers is roughly 150 kills" | That was *any* flower. Tempering needs 9 of **one element**. At 11% element share that is ~150 kills **per flower** (~1,350 for 9); in the best biome (25% share) ~67 per flower (~600 for 9). Flowers are a real grind, not a token. |
| "Grade comes from the floor, so every drop in a dungeon shares it" | Grade comes from **enemy level** (`pick_equipment_id(enemy_level)`), and enemy levels span `floor−(6+floor//10)` … `floor+min(floor,3)`. A floor-10 dungeon yields g1 *and* g2 drops. |
| "I can't tell whether a Legendary Ember is worth anything" | Traits scale by rarity only (§2.3) — so it keeps the full legendary trait on a g1 base. The trade-off is real. |

---

## 2. Verified findings

### 2.1 Grade and rarity share one input

`dungeon._roll_equipment_drop(enemy_level, …)`:
- grade → `pick_equipment_id(enemy_level)` → `grade_for_level` (≤10 → g1 · 11–25 → g2 · 26+ → g3)
- rarity weights → `if enemy_level <= 5 / 10 / 20 / 30 …`

Both are step functions of the same variable, so they are perfectly correlated. The cap then *links* them a second time. Treasure rooms do the same with `floor`.

### 2.2 The cap is a clamp (probability mass moves, nothing gets rarer)

`rarity = cap_rarity_for_item(item_id, rarity)` runs **after** the roll. A g1 item that rolled epic/legendary becomes rare. Effective distributions today (normal drops):

| Enemy-level band | Grade | Rolled weights `[C,U,R,E,L]` | Mass the clamp moves |
|---|---|---|---|
| ≤5 | g1 | .50 .34 .14 .02 .00 | 2% epic → rare (rare = 16%) |
| 6–10 | g1 | .36 .36 .21 .06 .01 | 7% → rare (rare = 28%) |
| 11–20 | g2 | .24 .31 .29 .13 .03 | 3% legendary → epic (epic = 16%) |
| 21–25 | g2 | .15 .25 .33 .21 .06 | 6% legendary → epic (epic = 27%) |
| 26–30 | g3 | .15 .25 .33 .21 .06 | none |
| 30+ | g3 | .11 .22 .34 .28 .05 | none |

**Treasure rooms** (`handle_treasure_room`): floor ≤10 rolls `[.65 rare, .33 epic, .02 legendary]` but the item is g1 (cap = rare) → **100% rare**. Floors 11–25 → 45% rare / 55% epic. The authored weights for the low bands are decorative.

**Why you cannot simply set the cap to "legendary".** Legendary weights are keyed to enemy level, not grade. Uncapped, the existing tables give (per kill; equipment drop chance = 0.50 × 0.88 × 0.60 = 26.4% normal, 0.70 × 0.88 × 0.60 = 37.0% Pandemonium):

| Context | Legendary / kill today | Legendary / kill with cap simply removed |
|---|---|---|
| Normal, Lv 6–10 | 0 | 0.26% (≈1 per 380) |
| Normal, Lv 11–20 | 0 | 0.79% (≈1 per 126) |
| Normal, Lv 21–25 | 0 | **1.58% (≈1 per 63) — same as g3** |
| Normal, Lv 26–30 | 1.58% (≈1 per 63) | unchanged |
| Pandemonium, Lv ≤5 | 0 | 2.2% (≈1 per 45) |
| Pandemonium, Lv 6–25 | 0 | **3.0–3.7% (≈1 per 27–34)** |
| Pandemonium, Lv 26+ | 3.7% (≈1 per 27) | unchanged |

Plain cap removal makes low-level Pandemonium a legendary fountain and erases the difference between g2 and g3 at Lv 21–25. The economy doc's playtest goal ("legendary is a chase") is violated.

Minor: the 30+ row has legendary **5%** while ≤30 has **6%** — non-monotonic. Probably intentional (mass shifted to epic) but worth a conscious decision.

### 2.3 Traits scale with rarity only — grade is irrelevant to them

`elemental_traits.get_trait_for_weapon(weapon, rarity)` uses `RARITY_TIER` only.

| Element | Trait | Common | Legendary |
|---|---|---|---|
| Physical | Sunder | 15% armor pen | **15% (no scaling)** |
| Fire | Ignite | tier 2 (Burn) | tier 5 (Conflagration) |
| Water | Douse | −1 CD on kill | −2 (epic+) |
| Thunder | Chain | 15% | 35% |
| Wind | Swift | +2 init | +6 |
| Earth | Bulwark | 8% DR | 16% |
| Light | Purge | 1 debuff | 2 (rare+) |
| Dark | Leech | 8% | 16% |
| Magical | Pierce | 25% | 45% |

**Consequences**
- A g1 legendary has the **full legendary trait** on a weak base. That is a genuine trade-off against a high-grade low-rarity item — the "Legendary Ember vs Common Inferno" choice I said was missing. Rarity = trait/identity; grade = raw power.
- **Physical weapons gain nothing from rarity trait-wise** (Sunder is static). A Legendary Iron Sword is stats + prestige only. Optional fix in §5 (P9).
- **Ignite saturates (verified in `status_effects.apply_burn`).** Burn tiers deal flat per-tick damage — Singe 3 · Burn 6 · Blaze 10 · Inferno 18 · Conflagration 30 — for 3 ticks per application. A repeat hit from a weapon of the *same* tier as the existing burn intensifies it by +1 tier; a lower-tier hit only refreshes. Sustained fights therefore converge on **weapon tier + 1** (capped at 5):

  | Rarity | Ignite tier (first hit) | After a second hit | Sustained dmg/tick |
  |---|---|---|---|
  | Common | 2 (Burn) | 3 (Blaze) | 10 |
  | Uncommon / Rare | 3 (Blaze) | 4 (Inferno) | 18 |
  | Epic | 4 (Inferno) | 5 (Conflagration) | 30 |
  | Legendary | 5 (Conflagration) | 5 (already capped) | 30 |

  Epic and legendary fire weapons are **identical after two hits**; legendary only wins the first application. Fire is the one trait where rarity stops mattering above epic, so a g1 legendary fire weapon (STR 7, fire 1.19) is mostly dominated by a g3 epic. Chain, Swift, Bulwark, Leech and Pierce scale linearly with tier and do not have this problem. Whether flat 3–30 ticks matter at endgame hit sizes depends on enemy HP (`enemies.py`, not reviewed); status-resistant bosses (`status_res`) can also resist Ignite outright. See P10.

### 2.4 Power / value comparison (Greatsword, fire, +0)

| Item | STR | Fire mult | Ignite | `item_value` |
|---|---|---|---|---|
| Common Ember (g1) | 4 | 1.10 | Burn (2) | 5 |
| Common Inferno (g3) | 8 | 1.50 | Burn (2) | 14 |
| Epic Blaze (g2) | 9 | 1.48 | Inferno (4) | 36 |
| Rare Inferno (g3) | 10 | 1.68 | Blaze (3) | 31 |
| **Legendary Ember (g1)** | 7 | 1.19 | **Conflagration (5)** | 40 |
| Legendary Inferno (g3) | 15 | 1.95 | Conflagration (5) | 112 |

`intrinsic_value` is stats + element bonus + grade premium, then `price_mult` multiplies the **whole** stack. A Legendary Ember (40) is "worth" more than a Rare Inferno (31) while having lower stats and element — its price is justified only by the trait. That is acceptable if the trait is worth it; it is a **pricing statement about rarity**, not a bug.

(Basic attacks resolve only the weapon's `primary_element` multiplier — `get_attack_element` — so the secondary `physical 1.2` entry does not contribute to basic-attack damage.)

### 2.5 Flower rates (per kill) — verified from `roll_drop` + `ELEMENT_WEIGHTS_BY_BIOME`

Any flower: 50% drop × 12% flower branch = **6.0% / kill** (Pandemonium 8.4%). A *specific* element's share is `weight / Σweights` (unlisted elements default to 1):

| Situation | Element share | Kills per flower | Kills for 9 (g1→g3) |
|---|---|---|---|
| Uniform biome (temperate / unknown) | 11% | ~150 | ~1,350 |
| Themed biome, weight 3 (e.g. fire in volcanic: 3 of 12) | 25% | ~67 | ~600 |
| Themed biome, weight 1 (e.g. light in volcanic) | 8% | ~200 | ~1,800 |

Treasure rooms add one flower each (same element weights). For reference, a *natural* g3 legendary is ~1 per 63 kills but **not your form/element** — a specific one (form 1/29 × element 25% × weapon family 48% = 0.41% of equipment drops ≈ 1 per ~920 kills, any rarity) is far worse. Tempering is therefore the realistic route to a specific g3 — but it still only fixes *grade*.

Because tempering lets you start from g1, the search space you actually need is **form × element (261 weapons)**, not × grade (783). Dilution (A) remains 1-in-261 at best.

### 2.6 Biome plumbing — likely dead data

- `add_drop_to_inventory` and both room handlers pass `player_biome(player)`, which reads **the city's** `biome`.
- Enemies in the same dungeon use `player["dungeon_region"]` (`generate_floor(…, region=region)`).
- `roll_drop(…, pandemonium, biome)` receives `pandemonium` as a bool and nothing maps it to the `"pandemonium"` weights table.
- Wild dungeons set `player["dungeon_region"] = region` and call `_wild_room_victory_rewards` → `add_drop_to_inventory` → city biome again.

So, unless a city is literally configured with `biome: "pandemonium"` / `"wonderland"`, the **pandemonium and wonderland weight rows (elements and flowers) are never reached**, and wild-dungeon ruin themes do not influence their own drops. Docs §4.2 (flower table) claims otherwise. *Verify with a one-line print of the biome at drop time in a Pandemonium run.*

### 2.7 Shops

- Grade (`roll_shop_grade`) and rarity (`SHOP_TIER_WEIGHTS`) are rolled independently; `_player_rarity_cap` only gates by level (legendary needs Lv 20).
- Value pricing: `price = city_base × item_value / 4`. Legendary Ember Greatsword (value 40) at city base 45 ≈ **450g** (≈135g after max discounts); sells for 100g.
- With the cap removed, a late shop could stock g1/g2 legendaries (~7–12% chance per day per late city) as ~hundreds-of-gold fodder. The scroll's "sacrifice 4 legendaries" requirement then costs ~2–3k instead of being a real gate (the 80k craft fee stays the main gate regardless).

### 2.8 Tempering & scroll plumbing

- Tempering gold is **flat** (1,200 / 3,000) and preserves rarity + enhance. A **legendary** g1 → g3 costs the same 4,200g + 9 flowers as a **common** one, though the value gained is 72 vs 9. Value-delta pricing (50g/pt, as in `fusion_fee`) would make legendary ≈ 3,600g — i.e. roughly the current flat price — so *pure* value-delta does not tighten it; a rarity multiplier does.
- `make_tempered_item` clamps rarity to the **target** grade's cap. For a pre-D-M grandfathered over-cap item (e.g. legendary g1), tempering to g2 would **demote** it to epic. Moot once the cap is removed.
- `blacksmith.fuse_scroll_with_item` refuses with "Temper it to a higher grade first." (D-M). Needs removal with the cap. **Confirmed:** `inventory.apply_scroll_to_item` carries the matching check (`if cap_rarity_for_item(item, new_rarity) != new_rarity: return False`), so both places must change or the scroll silently fails after the blacksmith has already shown the fee. The no-downgrade and same-rarity guards in that function are independent and stay.

### 2.9 Roll sites that bypass the pipeline

In `dungeon_rooms.py`, four sites call `_random_item_id()` and `build_item(item_id, rarity)` with **no grade gating and no `cap_rarity_for_item`**: trap-room bonus item (30%, up to rare), `monster_approaching` drop (40%, up to rare), `wl_paint_roses` (guaranteed, up to **epic**), `wl_cat_riddle` drop (40%, up to rare).

**Confirmed in `travel_events.py`:** `_random_item_id()` samples uniformly from every key in `ITEMS` that is not unique / scroll / ascension / key_item / wonderland-only / black-market-only. After the grid install that is ~1,670 composed equipment ids **across all three grades** (≈97% of the pool), plus a few dozen consumables/utilities and the nine flowers (`crafting_material` is not skipped). Consequences:
- A floor-1 trap room has roughly a 1-in-3 chance to hand out a **grade-3** piece; the floor-based grade bands do not apply.
- `wl_paint_roses` can produce epic g1/g2 items, violating the stated ceiling (no cap call).
- ~2% of rolls are consumables/flowers. A flower rolled this way carries a random rarity (e.g. "rare"), so it will not stack with normal common flowers (`_items_stackable` compares rarity). Tempering still works (it matches by id), but the stack is split.

The four **travel** sites are fine structurally — they use `pick_equipment_id` (grade-gated) and `cap_rarity_for_item`:
- `_handle_combat` — 40% per enemy, always equipment; rarity from `_combat_drop_rarity` (legendary 4% at enemy level ≥10).
- `_handle_discovery` (sea and land branches) — rarity from `_discovery_rarity` (legendary 3% at floor ≥10).
- `_handle_merchant` — rarity from `_merchant_stock_rarity`, **capped at epic**, so road merchants (and the dungeon merchant room, which imports the same helper) never sell legendary. The shop-fodder concern in §2.7 applies to **city shops only**.
- Travel never drops flowers.

---

## 3. Diagnosis — what feels wrong, in words

- **Grade and rarity were both "how strong is the base".** One came from depth, the other from luck, and the cap tied them together. A player never sees a real choice between them.
- **They should have different jobs.**
  - **Grade = base power** (stats + element + value). Depth gives it; gold + flowers can buy it (tempering).
  - **Rarity = trait strength + multiplier.** Luck gives it; only a scroll (80k + 4 same-rarity items) can buy it.
- **Flowers answered the wrong question.** They let you buy *grade* so you don't depend on a g3 legendary — a need that exists only because of the cap. Your original instinct ("the exact item is rare, so give an alternative route") is about *getting the base item*, and flowers do not do that.
- **Once axes are independent, the scarce axis is rarity.** Tempering/enhance are gold+grind (deterministic); rarity is luck + 80k. That is a coherent economy — as long as legendary supply is a deliberate dial instead of a side-effect of the cap.

---

## 4. Recommended model

| Axis | Job | Source of supply | Purchasable? |
|---|---|---|---|
| **Form × Element** | Your build identity | Drops (1-in-261 at best) · **Forge Commission (new)** | Yes — commission (1 flower + gold) |
| **Grade** | Base power | Depth (enemy level) | Yes — tempering (gold + flowers) |
| **Rarity** | Trait tier + ×stats | Luck, **soft-scarce below g3** | Only via scroll (80k + 4 same-rarity) |
| **Enhance** | Investment | Gold | Yes |

Rules:
1. **No hard rarity cap.** Replace it with a **soft ceiling**: a rolled rarity at a low grade survives with probability `p`, otherwise it demotes one step (and is re-checked). g3 is unrestricted.
2. Scrolls and tempering never consult grade ceilings.
3. Shops never sell legendary below g3.
4. Every drop site goes through the same pipeline and the same biome source.
5. Flowers stay the grade sink **and** become the element token for commissions.

---

## 5. Patches (ordered)

### P1 — Soft ceiling replaces the hard cap *(core, small)*

`resources/item_generation.py`
```python
GRADE_RARITY_CAP = {1: "legendary", 2: "legendary", 3: "legendary"}   # hard cap removed
# Chance a rolled rarity SURVIVES at this grade; otherwise it demotes one step and is re-checked.
GRADE_RARITY_PASS = {
    1: {"epic": 0.60, "legendary": 0.15},
    2: {"legendary": 0.40},
    3: {},
}
```
`resources/items.py`
```python
def soften_rarity(item_or_def, rarity, rng=random):
    """Rolled rarity -> possibly demoted by the item's grade (soft ceiling)."""
    from resources.item_generation import GRADE_RARITY_PASS
    grade = _resolve_item_def(item_or_def).get("grade")
    table = GRADE_RARITY_PASS.get(grade, {})
    idx = RARITY_LADDER.index(rarity) if rarity in RARITY_LADDER else 0
    while idx > 0 and rng.random() >= table.get(RARITY_LADDER[idx], 1.0):
        idx -= 1
    return RARITY_LADDER[idx]
```
Swap **rolled** sites from `cap_rarity_for_item` → `soften_rarity`:
- `dungeon._roll_equipment_drop`
- `dungeon_rooms.handle_merchant_room`, `handle_treasure_room`
- `shop.city_shop` (together with P2)
- `travel_events._handle_combat`, `_handle_discovery` (sea + land branches), `_handle_merchant` (4 sites; the merchant one is epic-capped already, so it only needs the swap for consistency)
- `guild.py` / `world_map_screen.py` (not reviewed — grep for `cap_rarity_for_item`; per the economy doc they reuse the travel helpers)

Keep `cap_rarity_for_item` only for ungraded legacy items (value caps). `make_tempered_item` no longer needs to clamp.

Risk: low. Dials: the four pass probabilities. No migration (grandfathered items are untouched).

### P2 — Shop legendary floor

`facilities/shop.py` (equipment branch, after `soften_rarity`):
```python
SHOP_LEGENDARY_MIN_GRADE = 3
if rarity == "legendary" and ITEMS[item_id].get("grade", 3) < SHOP_LEGENDARY_MIN_GRADE:
    rarity = "epic"
```
Keeps legendary fodder a drop-side resource. Road and dungeon merchants need no change — `_merchant_stock_rarity` already caps at epic. Bump the stock cache key (`shop_stock3_{city}`) so the change shows immediately.

### P3 — Tempering scales with rarity

`facilities/blacksmith.py`
```python
TEMPER_RARITY_GOLD_MULT = {"common": 1.0, "uncommon": 1.0, "rare": 1.5, "epic": 2.5, "legendary": 4.0}
req_gold = int(req["gold"] * TEMPER_RARITY_GOLD_MULT.get(item.get("rarity", "common"), 1.0))
cost = get_discounted_price(req_gold, player, city_id)
```
Legendary g1 → g3 becomes 16,800g + 9 flowers; common stays 4,200g + 9. Remove the grade-ceiling rarity clamp in `make_tempered_item`.

Trade-off to be aware of: any rarity-scaled cost makes the cheapest order *temper → scroll → enhance*. That is now a cost optimum, not a hard rule. If you want zero order pressure, skip P3 and accept that tempering a legendary is cheap.

### P4 — One biome source for dungeon drops *(bug fix)*

`resources/item_generation.py`
```python
def dungeon_biome(player):
    """Biome for loot rolled INSIDE a dungeon run."""
    if player.get("pandemonium_mode"):
        return "pandemonium"
    return player.get("dungeon_region") or player_biome(player)
```
Use in: `dungeon.add_drop_to_inventory`, `dungeon_rooms.handle_treasure_room` (item **and** flower), `handle_merchant_room`. Outside dungeons (travel, shops) keep `player_biome`. This revives the pandemonium/wonderland rows and makes wild ruins drop their own theme.

### P5 — Close the un-gated roll sites

In `dungeon_rooms.py`, replace the four `_random_item_id()` + `build_item(...)` sites (trap bonus, `monster_approaching`, `wl_paint_roses`, `wl_cat_riddle`) with:
```python
item_id = pick_equipment_id(floor, dungeon_biome(player))
rarity = soften_rarity(item_id, rarity)
```
`_random_item_id()` also yields consumables/flowers (~2% of rolls); losing those is harmless. If you want consumable variety at these sites, add an explicit small branch via `dungeon._roll_consumable_drop(level)` instead of relying on the uniform pool. Once `guild.py` / `world_map_screen.py` are grepped for other users, `_random_item_id` can be deleted.

### P6 — Remove the scroll grade ceiling

- `blacksmith.fuse_scroll_with_item`: delete the `capped != target_rarity` block (message "Temper it to a higher grade first").
- `inventory.apply_scroll_to_item`: delete the block commented "Grade ceilings: a scroll may finish a grade's rarity cap but never exceed it…" (the `if cap_rarity_for_item(item, new_rarity) != new_rarity: return False` check) and drop `cap_rarity_for_item` from that file's import list. Both edits must ship together.
- Fusion fee stays value-delta based (`fusion_fee`).

### P7 — Forge Commission *(recommended; answers dilution)*

New blacksmith entry **"Commission (Order a Base)"**: pick form → pick element → pay **1 flower of that element + gold** → receive a **common, g1, +0** item of exactly that form and element.
```python
COMMISSION = {"flowers": 1, "gold": 600}          # dials
item_id = f"{ELEMENT_PREFIXES[element][0].lower()}_{form_key}"   # g1 composed id always exists
item = build_item(item_id, "common")
```
- Flowers become the **element selector**, matching "one flower per element".
- Commission never yields rarity or grade — those stay luck-/gold-gated, so legendary scarcity is untouched and drops remain valuable (they carry the rolls you can't commission).
- The whole build chain becomes deterministic: **commission → temper → scroll → enhance**; drops are the shortcut, not the requirement.
- Flower demand rises by 1 per build (10 per chain with tempering) — see §2.5 for kill costs.

### P8 — Optional alternatives for dilution *(pick at most one with P7)*

- **Element boost:** consume a flower at dungeon entry; `_element_weights(biome, boost)` multiplies that element ×4 for the run. Lighter, but only shifts odds.
- **Form bias (weapons doc §10):** `FORM_WEIGHTS_BY_BIOME` ×3. Needs a form lookup in the pools (`_FORM_OF[item_id] = form_key`, filled in `install_grid`) and `rng.choices(pool, weights=…)` in `_pick_from_pools`. Raises a preferred form from ~3.4% to ~8% in its biome — useful, but it will not make a specific item reliable on its own.

### P9 — Optional: give Physical a rarity scaling

Two changes, not one: set `ELEMENTAL_TRAITS["physical"]["rarity_bonus"] = 0.03` **and** add `"on_hit_armor_pen"` to `scalar_keys` in `get_trait_for_weapon` — Sunder's key is not in that list today, so the bonus alone would do nothing. Legendary Sunder ≈ 27%. Without this, rarity is only a stat multiplier on physical weapons.

### P10 — Optional: fix Ignite saturation *(balance change — playtest)*

Because repeat hits intensify the burn by +1 tier, rarity stops mattering above epic for fire (§2.3). Options:

| Option | Sustained dmg/tick (C / U,R / E / L) | Effect |
|---|---|---|
| Leave as is | 10 / 18 / 30 / 30 | Epic = legendary after two hits |
| Shift table down one tier: `{"common": 1, "uncommon": 2, "rare": 2, "epic": 3, "legendary": 4}` | 6 / 10 / 18 / 30 | Every rarity distinct; **nerfs common–epic fire** |
| Add `intensify=False` to `apply_burn` for Ignite only | 6 / 10 / 18 / 30 | Same sustained result, first-hit values unchanged; small code change |
| Add a tier 6 above Conflagration (new HUD tag, e.g. 45/tick) | 10 / 18 / 30 / 45 | Keeps current values, gives legendary a real edge; new status tier to display |

Pick after checking enemy HP / hit sizes (`enemies.py`): flat 3–30 ticks may already be minor at endgame, in which case leave it.

---

## 6. Resulting rates after P1–P2 (approx., equipment drops only)

Pass table: g1 `epic 0.60 / legendary 0.15`, g2 `legendary 0.40`.

| Context | Legendary / kill | ≈ kills per legendary |
|---|---|---|
| Normal g1, Lv 6–10 | 0.04% | ~2,500 (jackpot) |
| Normal g2, Lv 11–20 | 0.32% | ~315 |
| Normal g2, Lv 21–25 | 0.63% | ~160 |
| Normal g3, Lv 26–30 / 30+ | 1.58% / 1.32% | ~63 / ~76 (unchanged) |
| Pandemonium g1, Lv ≤10 | 0.33–0.44% | ~225–300 |
| Pandemonium g2 | 1.5% | ~68 |
| Pandemonium g3 | 3.7% | ~27 (unchanged) |

- Four same-rarity items for one legendary scroll ≈ **~270 kills** in Pandemonium g2 or ~630 in normal g2 Lv 21–25 — a dial, not a wall.
- Epic share at g1 stays modest (e.g. Lv 6–10: ~4%); g2/g3 epic unaffected.
- If g1 fodder should be less of a jackpot, raise `GRADE_RARITY_PASS[1]["legendary"]` to 0.30.
- **Travel drops** (`_handle_combat`: 40% per enemy, always equipment, legendary 4% at enemy level ≥10): at g2 the soft ceiling gives ≈ 0.64% legendary per enemy killed — about **2× the dungeon rate per kill** (0.32–0.63%), because travel drops are always equipment while only ~26% of dungeon drop rolls are. Travel is therefore a real fodder source, bounded by travel time and mount/ship event mitigation rather than kill count.

---

## 7. Decisions

| # | Decision | Options | Recommendation |
|---|---|---|---|
| D-N | Rarity ceiling | keep hard cap · remove entirely · **soft ceiling (pass table)** | **Soft ceiling** (P1); entire removal floods Pandemonium (§2.2) |
| D-O | Shop legendary | any grade · **g3 only** · none | **g3 only** (P2) |
| D-P | Tempering price | flat · **× rarity multiplier** · value-delta | Rarity multiplier (P3); flat is fine if you accept cheap legendary grade |
| D-Q | Flower role | grade sink only · **+ commission (P7)** · + element boost (P8) | Commission; do not stack with boost |
| D-R | Biome source | city biome · **`dungeon_biome()`** | Bug fix — no decision needed beyond verifying §2.6 |
| D-S | Un-gated roll sites | leave · **route via `pick_equipment_id` + soften** | Route (P5) |
| D-T | Physical trait scaling | static · small rarity bonus | Optional (P9) — needs the `scalar_keys` fix too |
| D-U | Ignite saturation | leave · shift table · `intensify=False` · add tier 6 | Leave unless fire feels flat; if changed, test every fire build (P10) |

---

## 8. Tests

- **Rarity sampling:** for each (grade, enemy-level band, normal/Pandemonium) roll 200k and assert legendary/epic rates within ±15% of §6; assert g3 identical to today.
- **Soft ceiling:** `soften_rarity` never returns above the input; g3 is the identity; g1 epic/legendary survive at the table rates.
- **Scroll:** legendary scroll applies to a g1 item without refusal; item equals a natural drop (stat line) at that grade/rarity.
- **Tempering:** preserves rarity (including g1 legendary → g2, no demotion); gold follows `TEMPER_RARITY_GOLD_MULT`.
- **Shop:** 20k stock generations → zero legendary below g3.
- **Biome:** pandemonium run passes `"pandemonium"`; wild ruin passes its `dungeon_region`; city/travel still use the city biome.
- **Flowers:** sampled per-element rates match §2.5 in volcanic vs temperate.
- **Commission:** every (form, element) produces the expected id, common, g1, +0; refuses without the matching flower.
- **Leaks:** no un-gated roll site returns a grade above the floor's band after P5.

## 9. Doc updates when this ships

- Weapons doc: §4 (grade gating note: *enemy level*, not floor), §4.1 (rarity paragraph), §5.1 (cost stack/order), D-E, D-M (superseded by D-N), flower table (§4.2) once §2.6 is verified.
- Armor doc: D-AG.
- Economy doc: §3.4 base-tier caps → soft ceiling; legendary cadence targets restated per §6.
- Not changing: consumables, enhance costs, fusion no-downgrade, uniques, drop chance (50% / 70%), flower drop branch (12%).

## 10. Verification status (rev 2)

**Resolved by the files received**
- `travel_events.py` — `_random_item_id` samples all grades uniformly (§2.9); the four travel roll sites use the grade-gated pipeline and are listed under P1; road merchants are epic-capped.
- `inventory.py` — the scroll grade check is confirmed and must be removed together with the blacksmith pre-check (P6).
- `status_effects.py` — burn tier values and the intensify rule confirmed; Ignite saturates at epic (§2.3, P10).

**Still not seen**
- Arcane Tower — `_scroll_craft_cost()` and the "4 same-rarity" requirement (the 80k / 4-legendary figures come from the weapons doc only).
- `city.py` / `leveling.get_current_city_id` — how `dungeon_region` is set and what `player_biome` returns during a run. **§2.6 stays "likely" until this is checked** (one print of the biome passed at drop time in a Pandemonium run settles it).
- `guild.py`, `world_map_screen.py` — other roll sites (grep for `cap_rarity_for_item` and `_random_item_id`).
- `enemies.py` / endgame damage numbers — whether flat 3–30 burn ticks matter (P10).
- The combat hook in `player_actions.py` that calls `get_trait_for_weapon` — to confirm it passes the item's `rarity` (the trait table assumes it does).

---

## 11. Implementation record (2026-10-19)

**Shipped:** P1, P2, P3, P4, P5, P6, P7 (P8–P10 skipped by decision).

- **P1 — soft ceiling.** `GRADE_RARITY_PASS` + `items.soften_rarity()` replace the hard cap; `GRADE_RARITY_CAP` is now `legendary` for every grade (legacy-safe). Swapped at every rolled site: `dungeon._roll_equipment_drop`, `dungeon_rooms` (merchant, treasure, trap, monster, paint-roses, cat-riddle), `shop.city_shop`, `travel_events` (combat, discovery ×2, merchant), `guild._traveling_merchant`, `world_map_screen` ×4, and `random_equipment()` (black-market relics). `cap_rarity_for_item` survives only as a legacy helper.
- **P2 — shop legendary floor.** `SHOP_LEGENDARY_MIN_GRADE = 3` demotes any sub-g3 legendary roll to epic. **Correction:** the old stock key was `shop_stock2_{city_id}` (the proposal said `shop_stock3`); the bump is now `shop_stock3_{city_id}`, so existing players receive fresh stock once.
- **P3 — tempering price.** `TEMPER_RARITY_GOLD_MULT` (×1.5 rare · ×2.5 epic · ×4 legendary) applied before city discounts; `make_tempered_item` no longer clamps rarity (a legendary g1 → g2 stays legendary).
- **P4 — biome source.** `item_generation.dungeon_biome()` (pandemonium flag → `dungeon_region` → city biome) is used by `dungeon.add_drop_to_inventory`, `dungeon_rooms.handle_merchant_room`, and both the item and flower in `handle_treasure_room`. **Correction to §2.6:** `isle_of_glass` is configured with `biome: "pandemonium"` and `wonderland` with `biome: "wonderland"` (`resources/cities.py`), and `get_current_city_id` returns `origin_city` inside dungeons — so the pandemonium/wonderland weight rows were already live for city-floor runs. The actual bug was narrower: wild dungeons and world-map ruins used the origin city's biome instead of their own. P4 fixes that.
- **P5 — leaks closed.** The four `dungeon_rooms` sites now use `pick_equipment_id(level, dungeon_biome(player))` + `soften_rarity`; `_random_item_id` was deleted (its `guild`/`world_map_screen` imports were unused).
- **P6 — scrolls uncapped.** Both the blacksmith pre-check and the `inventory.apply_scroll_to_item` grade-ceiling check were removed; downgrade and same-rarity guards remain.
- **P7 — Forge Commission.** Blacksmith menu entry “Commission (Order a Base)”: family → form → element, cost 1 matching flower + 600 g (discounts apply). Builds the common g1 coordinate; refuses on missing flower, gold, or equipment-bag space.
- **Tests:** `_diag_weapon_grid.py` / `_diag_armor_grid.py` (soft-ceiling distributions), `_diag_scroll_caps.py` (rewritten: scrolls uncapped), `_diag_retirement_temper.py` (rarity pricing, no demotion, every commission coordinate exists), `_diag_item_economy.py` (hard cap removed). All pass; `_diag_form_tags.py`, `_diag_form_perks.py`, `_diag_version_consistency.py` pass unchanged.

---

## 12. Follow-up rework — grade vs flower (proposal, TOP PRIORITY)

> **Status:** ✅ **Implemented 2026-10-20** — base-form catalog, rarity compression, three-slot weapon infusion, trait ladders and v4 migration are live. 3:1 transmutation shipped 2026-10-19.

### 12.1 What's still wrong

Grade currently does two jobs (base power: stats + elemental ladder + value premium; and prefix identity). Rarity is the only luck axis **and** the only elemental-trait axis. Flowers only buy grade. The stack stays multiplicative, so a g3 legendary +10 is still ~8× a g1 common of the same form.

### 12.2 Options on the table (user proposals, evaluated)

| # | Proposal | Verdict |
|---|---|---|
| **A** | Grade becomes the **enhancement cap**; drop the per-grade elemental ladder | ❌ **Rejected.** A g1 and g3 drop would be identical at +0 — grade becomes a coupon for gold, not loot. The user's own objection is decisive: a found max-grade weapon means tempering only fixes bad luck, so the loot moment disappears and all progression collapses into an enhance-gold grind. |
| **B** | **Remove grade**; flowers apply the element to a **base form**; rarity stays as power | ✅ **Recommended.** Removes the grade×rarity×enhance stack by construction and fixes dilution at the root: the hunt becomes form-only (1 in 29/16/17), not form × element × grade. |
| **C** | **Elemental trait tier moves from rarity to flowers** (each flower infusion upgrades the effect) | ✅ **Recommended, together with B.** Decouples trait power from stat power, fixes the audit's trait anomalies (static Sunder, Ignite saturation at epic, full legendary trait on a g1 base), and gives flowers a permanent power sink. |

### 12.3 Recommended model (B + C)

- An item exists as **Form × Rarity × Enhance**. A weapon carries up to **three flower elements**: primary (1.10 → +0.05/infusion → 1.48, owns the trait), secondary (cap 1.20) and tertiary (cap 1.15) — §12.8. Armor/accessories hold up to **three resistance elements** on the same three-slot rule (resistance track only; the first slot owns the form drawback).
- **Rarity = stat multiplier + value** only (trait tier no longer follows rarity).
- **Trait tier = flower infusions** (weapon unlocks at the 4th / 6th / 8th infusion; armor/accessory res tiers cap at 3 infusions — see §12.7/§12.8). Trait upgrades enter `intrinsic_value` so pricing stays truthful.
- **Grade, tempering, and the 1,673-coordinate grid retire.** The catalog falls to ~558 base-form items; `{prefix}_{form}` ids migrate to base form + element token (`item_formula_version = 4`).
- **Stack compression happens here:** `stat = (form base + enhance) × rarity`, rarity range retuned to ≤1.4×, enhance cap tied to rarity (e.g. +5 common → +10 legendary) or left flat. Target ≤3× worst-to-best within one form.
- Flower sinks: element infusion (1), trait upgrades (1 each), commission/temper replaced by infusion. Enhancement stays gold.
- **3:1 transmutation stays** — any flower farm converts into the one a build needs.

### 12.4 Migration sketch (when approved)

1. `install_grid()` installs base forms only; element becomes an instance field (`weapon["element"]`), not part of the id.
2. v4 migration: parse `{prefix}_{form}` → base form + element; keep rarity/enhance; re-stat via the compressed formula; traits re-derived from the instance element.
3. `ELEMENT_PREFIXES` retires (names become `<Element> <Form>` from the instance, e.g. "Inferno Greatsword" built at display time).
4. Balance pass + playtest before removing the old grid from `ITEMS` (keep legacy ids for one chapter).

### 12.5 Implemented now (2026-10-19)

- **Flower transmutation 3:1** — blacksmith “Transmute Flowers (3:1)”: consume 3 blooms of one element → 1 of another, no gold fee. `TRANSMUTE_RATIO`, pure `transmute_flower()`, menu wrapper `transmute_flowers()`. Test: `_diag_retirement_temper.py` (conversion, insufficient stock, same-element refusal). This is the only piece of §12 shipped in the current chapter; B+C remain design-only until approved.

### 12.6 Sequencing — dungeon form identity (§10) waits

**Decision: do not implement §10's form weighting on the current grid; fold it into this rework.**

- Under B the pool shrinks from 1,673 coordinates to ~558 base forms and element dilution disappears — the hunt becomes 1 in 29 (weapon forms), not 1 in 261 (form × element). Form weighting stops being a fix and becomes flavor.
- `_pick_from_pools` is replaced by the rework anyway; weights built now are throwaway work.
- No player-facing emergency: Forge Commission already returns any form deterministically for 1 flower + 600g.
- When the rework ships, `FORM_WEIGHTS_BY_BIOME` ×3 lands in `_pick_from_pools` over base forms in the same pass.

### 12.7 Element ladders — all nine traits need infusion tiers

**Verified against `combat/elemental_traits.py`:** only **fire** has a real tier ladder (Burn → Blaze → … → Conflagration). Water and Light have one hard step, Thunder/Wind/Earth/Dark/Magical scale linearly with rarity, and Physical is static (Sunder never scales, and `on_hit_armor_pen` is missing from `scalar_keys` anyway). In B+C, rarity no longer touches traits, so every element needs three readable infusion tiers. **Infusion tiers also own the weapon's elemental damage multiplier** (+0.05 per infusion, cap 1.48, traits unlocking at 1.25 / 1.35 / 1.48 — primary slot only; §12.8), replacing grade's old 1.10 / 1.30 / 1.50 ladder × rarity scaling. Current legendary values become trait tier III:

| Element | Trait | Tier I | Tier II | Tier III |
|---|---|---|---|---|
| physical | Sunder | 15% armor pen | 22% | 30% |
| fire | Ignite | Burn (6/tick) | Inferno (18/tick) | Conflagration (30/tick) |
| water | Douse | −1 cooldown on kill | −2 | −3 |
| thunder | Chain | 15% chance · 40% splash | 25% | 35% |
| wind | Swift | +2 initiative | +4 | +6 |
| earth | Bulwark | 8% DR | 12% | 16% |
| light | Purge | 1 debuff | 2 | 3 |
| dark | Leech | 8% heal | 12% | 16% |
| magical | Pierce | 25% res ignore | 35% | 45% |

- Fire's 5-step burn ladder stays the **status effect's** internal scale; infusion tiers pick the entry point (2 / 4 / 5). The same-tier intensify rule still pushes sustained burn one step higher, capped at Conflagration.
- Armor/accessory infusion tiers reuse the existing resistance numbers: armor primary 1.15 / 1.25 / 1.35 and accessory 1.05 / 1.10 / 1.15 at tiers I / II / III — grade's resistance job transfers to the flower with no rebalance.
- `rarity_bonus`, `RARITY_TIER` and `IGNITE_TIER_BY_RARITY` retire when the rework ships; trait resolution reads the instance's infusion tier instead.
- Trait tier enters `intrinsic_value` (value = stats + element entries + trait tier) so merchant pricing stays truthful.

### 12.8 Infusion rules — three element slots (weapon), upgrade or fill

- **Up to three element entries on a weapon.** The primary drives basic attacks and the trait (`get_attack_element`); secondary and tertiary never proc traits — they strengthen off-element **skills**, because `calculate_elemental_damage` reads the merged `attacker["elemental_dmg"]` profile for the skill's element. One proc layer, three damage layers. Armor/accessories use the same three-slot rule, but every slot is resistance-only: primaries from all slots, the first slot's drawback, and each slot's secondary — max-merged so a slotted element can cover the drawback.
- **Slot caps (weapon):** primary starts 1.10, +0.05 per infusion, cap **1.48**, traits at 1.25 / 1.35 / 1.48 · secondary starts 1.10, cap **1.20** · tertiary starts 1.10, cap **1.15**.
- **One flower per element, repeatable — no tiered flower items.** The item's tier is its infusion count (I → II → III = 1–3 flowers of the same element). Tiered flowers (Emberbloom → Blazebloom → Inferno Bloom) would recreate the grade ladder that B removes and triple the material count from 9 to 27, with a third conversion matrix to maintain. Depth comes from the item's tier, not from the flower's quality.
- **Same flower, same element:** upgrades that element's slot by +0.05, respecting the slot cap. Primary-slot traits unlock at **1.25 / 1.35 / 1.48**.

  | Flowers infused | Weapon elemental multiplier | Unlocks |
  |---|---|---|
  | 1 | 1.10× | element set |
  | 2 | 1.15× | — |
  | 3 | 1.20× | — |
  | 4 | 1.25× | **trait I** |
  | 5 | 1.30× | — |
  | 6 | 1.35× | **trait II** |
  | 7 | 1.40× | — |
  | 8 | 1.48× (cap; last step +0.08) | **trait III** |

  Armor/accessories use a shorter resistance-only track: tiers I / II / III at 1–3 infusions per slot (armor primary 1.15 / 1.25 / 1.35 · accessory 1.05 / 1.10 / 1.15) — no damage multiplier. Up to three slots; the first slot's drawback can be covered by slotting that element in another slot. Multipliers are a playtest dial; the track shape is the decision. **Consequence to confirm:** under this track the first three flowers raise damage only — trait I arrives on the 4th flower. If the first infusion should grant trait I, move threshold I to 1.10 and keep 1.35 / 1.48 for II / III.
- **Secondary identity is capped at 1.20×.** Form-owned secondary damage entries (e.g. a blade's innate physical) never grow with infusions and can never exceed 1.20 — one weapon, one primary, one modest secondary.
- **Rarity and enhancement no longer touch the elemental multiplier.** Element power = flower track only; enhance = stats only. This retires the old `1.0 + (grade + 0.02×enhance − 1.0) × rarity` stack (top end ~3.2× today → 1.48×) and removes the “Ember +10 = Blaze +0” naming collision for good.
- **Different flower:** fills the next empty slot (secondary, then tertiary), each starting at 1.10. When all three slots are filled, a new distinct element **replaces the tertiary slot** (resets to 1.10) — the primary and secondary are never destroyed. Switching the primary entirely = commission a new base (1 flower + 600g) or a future respec service.
- **No overflow sink:** the primary cap is 1.48× (8 infusions); secondary/tertiary cap at 1.20×/1.15×. Extra flowers keep other uses (3:1 transmutation, commission, future sinks); unbounded multiplier stacking would just move the grind wall.
- Cost: **1 flower per infusion**, no gold. The 3:1 transmutation covers wrong-element farming.

### 12.9 Uninfused base items

- **Weapon:** defaults to the form's base axis — martial forms physical (Sunder I), caster forms magical (Pierce I). This is already per-form data (`WEAPON_FORMS[..., "base"]`), so plain drops keep behaving like today and the first flower is a *choice*, not a prerequisite. The first flower of a **different** element replaces that default primary; the same element simply upgrades it.
- **Armor/accessory:** default to the physical resistance triangle at tier I (matches the current filler order, physical first).
- No “elementless” items exist in combat math — `get_attack_element` / `calculate_elemental_damage` always receive a valid element.
### 12.10 Implementation record (2026-10-20)

- **Catalog:** `install_base_forms()` installs 62 base forms (29 weapons / 16 armor / 17 accessories). The 1,673-coordinate grid stays as **dormant legacy defs for one chapter** (old ids still resolve; nothing drops them). Pickers return base forms and ignore grade/biome args.
- **Rarity:** stat multipliers compressed to 1.00 / 1.10 / 1.20 / 1.30 / 1.40; `compute_elemental_dmg` / `compute_elemental_res` no longer scale with rarity or enhancement (enhance = stats only). City shops cap at epic; legendary is drop/scroll-only.
- **Infusion:** `apply_infusion()` + `refresh_infused_instance()` in `item_generation.py`; exact ladders primary (1.10 → 0.05 steps → 1.48, 8 infusions), secondary (1.10 / 1.15 / 1.20), tertiary (1.10 / 1.15). Primary traits unlock at 1.25 / 1.35 / 1.48; uninfused gear keeps its innate trait I. Armor/accessories hold up to three resistance elements with 1.15 / 1.25 / 1.35 (armor) or 1.05 / 1.10 / 1.15 (accessory) tiers per slot; the first slot owns the form drawback, later slots add coverage (max merge), and accessories keep their form stat affinity — flowers only add resistance.
- **Traits:** `INFUSION_LADDERS` resolves from the instance's `trait_tier`; the old rarity curve remains only as a fallback for uniques/legacy.
- **Services:** blacksmith “Temper” is replaced by “Infuse Element”; Commission forges the base form + first infusion; 3:1 transmutation unchanged.
- **Value:** `intrinsic_value` reads instance element profiles and adds the trait tier (+1/+2/+3); `item_value` passes instances through so infused gear prices truthfully.
- **Naming:** the element prefix is now the flower-tier word. Weapons use the primary value: word II from **1.30** (the old grade-2 element value) and word III from **1.40** (7th infusion); 1.10–1.25 reads as word I (fire: Ember → Blaze → Inferno); armor/accessories use the first infusion slot's stored tier (0–2) directly — later slots do not rename the piece. Uninfused drops carry no prefix. `character._refresh_base_form_name` re-derives names on every load, so saves migrated by earlier v4 builds pick up the current words. **Uniques are exempt** — their hand-authored names never take a tier word; the Examine popup states the element instead (“This weapon causes Dark damage (×1.35 | Leech II)” style, from `InventoryScreen._weapon_element_line`).
- **Flower drop element (2026-10-22):** `pick_flower_id(biome, enemy_element=…)` gives the defeated enemy's attack element **60%** of the time and falls back to `ELEMENT_WEIGHTS_BY_BIOME` for the other 40%. `dungeon.add_drop_to_inventory` passes `_enemy_attack_element(enemy_key)`; neutral enemies and room caches (rose-painting cache, wild reward pools) pass no element and stay biome-only.
- **Migration:** `item_formula_version = 4` maps `{prefix}_{form}` → base form + infusion (old grade → 1.10 / 1.25 / 1.48, old secondary axis → slot 2) while keeping rarity/enhance; legacy trophies are untouched.
- **Tests:** new `tests/_diag_infusion.py`; weapon/armor/economy/rarity/scroll/retirement diags updated. All equipment diagnostics pass.

### 12.11 Remaining work (status 2026-10-20)

1. **Unique rebalance** — ✅ **Implemented 2026-10-20:** every unique weapon now carries one primary element at infusion tier II (`elemental_dmg = {primary: 1.35}`, `trait_tier = 2`, explicit map first then highest value), and stat totals are normalized to slot budgets at +5: **weapon 32 · armor 33 · accessory 26** (base mods = budget − 5×stat_count; the hidden `UNIQUE_BASE_BONUS` was removed). **Superseded 2026-11-09:** all unique equipment (weapons, armor, accessories) is now collapsed to **one primary element** by `item_generation.normalize_unique_elements()`; flowers fill two remaining profile slots via `apply_infusion` (primary locked). See §12.12.
2. **Power/enemy curve** — the top end is roughly halved vs the old grid; re-verify enemy HP/damage, dummy TTK and boss fights. Burn ticks (3–30) are a larger share of weapon power now.
3. **Enhancement dominance** — ✅ **Implemented 2026-10-20:** `ENHANCE_CAP_BY_RARITY` caps enhancement at +5 common · +6 uncommon · +7 rare · +8 epic · +10 legendary (uniques stay +5). Grandfathered over-cap items keep their level but cannot enhance further.
4. **Economy pass** — price multipliers are still 1/1.4/2.2/4/8 while stats cap at ×1.4, and `intrinsic_value` counts element *entries*, not infusion magnitude. Re-tune shop/sell prices and fusion fees on the new values. **(Deferred to final playtest.)**
5. **Infusion UI** — inventory cards/examine and merchant lines do not show infusion values or trait tier yet (`_item_stat_line` shows mods + form perk only). Flowers now have a dedicated Bag tab with live counts and the Bag refreshes on tab switch; gear cards still need exact infusion/tier text. **(Partially done.)**
6. **Real-save migration check** — user will verify with savefile 1 “prism” and run a fresh save for the full playtest.
7. **Doc sweep** — ✅ **Swept 2026-10-20:** both grade-era design docs now carry a “GRADE MODEL RETIRED” banner and the grade rows are marked historical.
8. **Playtest dials** — flower supply vs a 22–25 flower full kit; 3:1 conversion; trait thresholds (1.25/1.35/1.48); primary length (8 infusions); form-perk magnitudes. **(Deferred to final playtest — checklist: `docs/flower_rework_playtest_checklist.md`.)**
9. **Enemy damage profile normalization** — ✅ **Implemented 2026-10-20:** `compute_enemy_elemental` now collapses `elemental_dmg` to the single element returned by the shared `get_damage_element()` picker, which `enemy_ai` and `elemental_debuffs` both use (identical `ELEMENTS` tie-break), so 399 multi-element enemies stop carrying damage entries that never applied; resistances stay multi. `event_horizon.scale_enemy_elemental` only multiplies entries > 1.0, fixing neutral enemies gaining a phantom fire element under enemy-elemental trial cards. Test: `tests/_diag_enemy_elemental.py`.

### 12.12 Unique equipment — one primary + two flower slots (2026-11-09)

- **One primary element.** `install_grid()` calls `item_generation.normalize_unique_elements()`, which collapses every unique equipment definition to a single `primary_element`. `unique_primary_element()` resolves explicit `UNIQUE_PRIMARY_ELEMENTS` first, then the highest `elemental_dmg`, then the highest `elemental_res`; ties use the canonical `ELEMENTS` order. Unique armor/accessories keep only their authored primary damage/resistance values (dual-profile pieces keep both axes for that one element).
- **Primary is locked; flowers fill two slots.** `blacksmith._infusable()` now accepts uniques. `apply_infusion()` → `_apply_unique_infusion()` refuses the primary element and accepts up to two distinct flower elements. Weapons use the secondary/tertiary damage ladders (1.20 / 1.15 caps); armor uses the armor resistance tiers; accessories extend whichever profiles they authored (damage-only → damage, resistance-only → resistance, dual → both). A full third element replaces the second flower slot, never the primary.
- **Names stay hand-authored.** `infused_item_name()` short-circuits for uniques, so flowers never add a tier word. Examine still shows the primary damage line, trait tier, flower-boosted skill elements, and the resistance profile.
- **Elementless flavour uniques** (`chance_and_choice`, `piece_of_relationship`, `prescript_ledger`) start with no primary; their first flower claims the primary slot and adds tier-I resistance.
- **Old saves:** `character._refresh_unique_instance()` runs on every load, collapsing legacy multi-element unique profiles to the primary while preserving flower slots and authored stats/specials.
- **Tests:** `tests/_diag_infusion.py` (unique section), `tests/_diag_reforge.py` (unique flower-slot reforge).

---

## 13. Reference — weapon base forms, flowers & sources (2026-10-20)

> Snapshotted from `resources/item_generation.py` and `resources/items.py` after the v4 base-form rework (§12.10). Grade/tempering is retired: a dropped item is an **uninfused base form**, flowers supply its elements, and rarity supplies stats/traits.

### 13.1 Weapon base forms (29)

Drops pick a base form, not a form × element × grade coordinate. `Family` is `weapon_type` — the key used by weapon-synergy effects (the Old Dopo Robe requires `blade`). `Biome bias` = 3× draw weight in that biome (`FORM_WEIGHTS_BY_BIOME`); `—` = uniform everywhere.

| Form | Family | Scaling | Base stats | Damage | Biome bias (3×) | Notes |
|---|---|---|---|---|---|---|
| Sword (`sword`) | sword | Strength | STR +2 | Physical | temperate | — |
| Greatsword (`greatsword`) | greatsword | Strength | STR +4 | Physical | temperate, volcanic | — |
| Axe (`axe`) | axe | Strength | STR +4 | Physical | volcanic, savanna, desert, pandemonium | — |
| Flail (`flail`) | flail | Strength | STR +3 · CON +1 | Physical | volcanic, pandemonium | — |
| Hammer (`hammer`) | hammer | Strength | STR +4 | Physical | mountain, volcanic | — |
| Mace (`mace`) | mace | Strength | STR +3 · WIS +1 | Physical | swamp | — |
| Maul (`maul`) | maul | Strength | STR +4 · CON +1 | Physical | mountain | — |
| Spear (`spear`) | spear | Strength | STR +3 · DEX +1 | Physical | tundra, forest, savanna, desert, sea_caves | — |
| Halberd (`halberd`) | halberd | Strength | STR +4 · DEX +1 | Physical | mountain | — |
| Shield (`shield`) | shield | Constitution | CON +3 | Physical | temperate, mountain | CON weapon: half damage; DR = CON÷2 |
| Gauntlets (`gauntlets`) | gauntlets | Constitution | CON +2 · STR +1 | Physical | — | CON weapon: half damage; DR = CON÷2 |
| Dagger (`dagger`) | dagger | Dexterity | DEX +3 | Physical | swamp, forest, tropical, sea_caves | — |
| Tongue Dagger (`tongue_dagger`) | dagger | Charisma | CHA +3 · DEX +2 | Physical | swamp, pandemonium | — |
| Blade (`blade`) | blade | Strength | STR +4 · DEX +2 | Physical | — | — |
| Spellblade (`spellblade`) | blade | Learning | LER +3 · WIS +2 | Magical | — | — |
| Rapier (`rapier`) | rapier | Dexterity | DEX +4 · CHA +1 | Physical | savanna, coastal, wonderland | — |
| Bow (`bow`) | bow | Dexterity | DEX +4 | Physical | temperate, forest, tropical | — |
| Crossbow (`crossbow`) | crossbow | Dexterity | DEX +3 · LER +1 | Physical | tundra, coastal | — |
| Chakram (`chakram`) | chakram | Dexterity | DEX +3 · STR +1 | Physical | savanna, desert, tropical | — |
| Staff (`staff`) | staff | Wisdom | WIS +4 | Magical | magical | — |
| Greatstaff (`greatstaff`) | staff | Learning | LER +4 | Magical | tundra, magical | — |
| Wand (`wand`) | wand | Learning | LER +2 · WIS +1 | Magical | desert, sea_caves, wonderland | — |
| Orb (`orb`) | orb | Learning | LER +3 · CHA +1 | Magical | swamp, magical, coastal, sea_caves | — |
| Focus Orb (`focus_orb`) | orb | Wisdom | WIS +3 · LER +1 | Magical | — | — |
| Scepter (`scepter`) | scepter | Wisdom | WIS +3 · CHA +2 | Magical | — | — |
| Grimoire (`grimoire`) | grimoire | Learning | LER +4 | Magical | magical, pandemonium | — |
| Lute (`lute`) | lute | Charisma | CHA +4 · LER +1 | Magical | forest, wonderland | — |
| Harp (`harp`) | harp | Charisma | CHA +3 · DEX +2 | Magical | tundra, coastal | — |
| Bell (`bell`) | bell | Charisma | CHA +3 · LER +2 | Magical | tropical, wonderland | — |

**Form defaults on drop:** uninfused weapons keep the form's innate damage axis — martial forms are Physical (Sunder I), caster forms Magical (Pierce I). The first flower can replace that default primary; the same element upgrades it.

### 13.2 Flowers (9)

One flower per element. All are `crafting_material` with `no_random_stock: true` — **never sold in shops**. `Favoured biomes` are the `ELEMENT_WEIGHTS_BY_BIOME` entries above the default weight 1 (temperate is all-1; any unlisted biome also uses 1, so an unknown biome is a uniform 1/9).

| Flower | Element | Item id | Favoured biomes (weight) |
|---|---|---|---|
| Ironbriar | Physical | `ironbriar` | mountain ×2 |
| Emberbloom | Fire | `emberbloom` | volcanic ×3, desert ×3, savanna ×2, pandemonium ×2 |
| Frostlotus | Water | `frostlotus` | tundra ×3, swamp ×3, coastal ×3, sea_caves ×3, tropical ×2 |
| Stormlily | Thunder | `stormlily` | coastal ×2, sea_caves ×2 |
| Galeorchid | Wind | `galeorchid` | tundra ×2, forest ×2, savanna ×2, coastal ×2 |
| Stonebloom | Earth | `stonebloom` | mountain ×3, swamp ×2, volcanic ×2, forest ×2, savanna ×2, desert ×2, tropical ×2 |
| Sunpetal | Light | `sunpetal` | wonderland ×2 |
| Nightbloom | Dark | `nightbloom` | pandemonium ×3, swamp ×2, wonderland ×2 |
| Manabloom | Magical | `manabloom` | magical ×3, pandemonium ×2, wonderland ×2 |

Flowers are consumed by blacksmith services: **1 per infusion**, **1 per Forge Commission**, and **3 → 1** element transmutation.

### 13.3 Sources

| Source | Base forms | Flowers | Notes |
|---|---|---|---|
| Dungeon enemy kill (`roll_drop`) | Yes — 60% of successful drop rolls | Yes — 12% of successful drop rolls | Roll succeeds 50% normal / 70% Pandemonium → **flowers 6.0% / 8.4% per kill**. Element is biome-weighted via `dungeon_biome(player)` (Pandemonium → `pandemonium`; wild dungeons → own region; else city biome). |
| Treasure room (`handle_treasure_room`) | Yes — 1 random item | **Yes — 1 guaranteed** | Biome-weighted; the reliable flower-farming spot. |
| City shop | Yes — base-form stock | **No** — `no_random_stock` | Shop rarity caps at epic (§12.10). |
| Travel combat / discovery / merchant | Yes | No | Uses `pick_equipment_id` + rarity helpers; merchant stock caps at epic (§2.9). |
| Trap bonus / `monster_approaching` / Wonderland paint-roses & cat riddle | Yes | Incidental — consumables/flowers make up ≈2% of `_random_item_id` rolls | Bypasses form weighting — cleanup tracked in §2.9. |
| **Forge Commission** (blacksmith) | **Yes — any form, chosen** | Consumes 1 matching flower | 600g before discounts → common item + first infusion. The deterministic form + element source. |
| Infuse Element (blacksmith) | — | Consumes 1 per infusion | Same element upgrades the slot; a new element fills the next (caps 1.48 / 1.20 / 1.15). |
| Transmute Flowers (blacksmith) | — | 3 → 1 of another element | No gold fee; fixes element-locked farming streaks. |

**Rate summary:** a specific flower's share is `weight / Σweights` — 1/9 ≈ 11% in temperate or an unknown biome, up to 3/12 = 25% in a themed biome. At 6.0% flower drops that is ≈ 67 kills per themed flower and ≈ 150 for an unweighted one (§2.5). Forge Commission removes the form × element hunt; flowers then gate infusion count (up to 8 per weapon primary) while rarity remains the chase.