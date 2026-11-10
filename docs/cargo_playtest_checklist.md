# Cargo System Playtest Checklist — Phase A + B verification

Run through this before starting Phase C. Expected values are from the
implemented constants (`resources/trade_goods.py`, `resources/ships.py`,
`resources/mounts.py`). A "❌" anywhere = bug to report.

## Setup

- [x] Have ≥ 3,000g available (use an existing save or grind).
- [x] Buy the Trade Permit at a trade hall (e.g. Solmere, 200g). Label should
      read "Buy trade permit (200 gold) — unlocks cargo markets".

---

## Phase A — Cargo market & weight

### A1. Access gating

- [x] **No permit:** any city shop shows "??? — Requires Trade Permit";
      selecting it prints the clerk's refusal.
- [x] **With permit:** shop menu shows "Cargo Market".

### A2. Buying

- [x] Cargo Market header shows Gold + `Load: x/y wt (overload cap z)`.
- [x] **No mount:** buying is refused ("no mount" hint, Load `0/0`).
- [x] Buy a Mule (100g) at the Trade Hall → Load reads `0/30`.
- [x] Buy prices match: `base × 0.6 × (1 − cha_disc)`. Examples at 8 Charisma:
      Spices 45g (base 75), Saltfish 24g (base 40), Ingots 51g (base 85).
- [x] Higher Charisma lowers the price (25% soft cap) — check with a
      high-Charisma build/ally buff.
- [x] Stock is 2–3 distinct goods × 5 units each; depletes per purchase.
- [x] When a good hits 0: "Nothing left in stock today."
- [x] Buying that would exceed **1.8× capacity** is rejected (Mule: reject
      past 54 wt). Buying between 30–54 wt is allowed (travel penalty range).
- [x] Stock restocks after the in-game day changes (sleep at the inn or travel
      enough minutes past 1440).

### A3. Selling

- [x] Selling in the **origin city** = loss: Spices in Dunemar → 52g (0.7×).
- [x] Selling in a high-demand city: Spices in Stormhold → 112g (1.5×).
- [x] Ore (mountain theme) sells high at ports: Cinderpeak Ore in Coralhaven
      ≈ 77g vs 0.8× in Irondeep ≈ 56g.
- [x] Selling removes the item and updates the Load line.

### A4. Inventory

- [ ] Cargo items appear in the bag labeled `(Cargo)`.
- [ ] Cargo does **not** consume bag space (`x/20 items` unchanged).
- [ ] Cargo never appears in the shop's normal "Sell" list.

### A5. Travel weight (land)

- [x] Load ≤ capacity → no travel-time penalty (Mule still gives its 15%
      reduction).
- [x] Load between capacity and 1.8× → ETA grows; at the 1.8× cap the penalty
      is +25% (terminal and world map must agree).
- [x] Load > 1.8× capacity → terminal `travel_to_city` prints the overload
      message; world map shows the "Overloaded" dialog listing the blocked legs.
- [x] **No mount** with cargo → travel allowed but +25% time; on-foot warning
      line shows.
- [x] Sell the mount while loaded (Trade Hall) → max penalty (+25%) until the
      cargo is sold off or stashed in house storage.

### A6. GUI/terminal parity

- [ ] World map route ETA includes the load penalty.
- [ ] Trade Hall mount status line shows `Cargo load: x/y wt` when carrying.
- [x] Cargo Market menus render correctly in GUI mode (background thread /
      facility screen).

---

## Phase B — Merchants, ships, monthly bills

### B1. Road merchant (travel events)

- [x] ~30% of road-merchant stock slots are cargo goods, priced at 75–90% of
      the market buy price (e.g. Spices ~34–40g).
- [x] Selling cargo to the road merchant pays the flat road rate: Spices 56g.
- [x] Normal items still sell at normal road rates (no errors).

### B2. Discoveries

- [x] Land: "abandoned wagon" outcome grants 1–3 units of a random cargo good.
- [x] Sea: "drifting cargo crate" outcome grants 1–3 units.
- [x] Pickup is always accepted (even past 1.8×). If it pushes the load past
      1.8×, travel is blocked until you sell/stash — confirm this state.

### B3. Dungeon merchant

- [x] Merchant rooms occasionally stock cargo (~30% per slot).
- [x] Selling cargo there pays the flat road rate (Spices 56g).

### B4. Guild Market Day merchant

- [x] When the Traveling Merchant daily event is active, the stall may stock
      cargo weighted toward the city's origin goods.
- [x] Selling cargo to him uses **city demand** (Spices in Solmere → 67g vs
      56g on the road).

### B5. Ships

- [x] Shipyard (Brinewatch/Tidebreak): no ship → buy list shows all three
      tiers (Sloop 500g, Frigate 1500g, Galleon 4000g) with stats.
- [x] Owned ship → menu shows Upgrade / Downgrade / Sell. Upgrade costs the
      difference (Sloop→Frigate 1000g, Frigate→Galleon 2500g); downgrade
      refunds half the difference; sell refunds half the cost.
- [x] **Old-save migration:** a save with `has_ship`/`ship_type` loads with
      the correct `ship_id` (sloop/frigate) and the old fields gone.
- [x] Port: with a ship → no ticket and voyage time reduced by the ship's
      percentage (Sloop 30%, Frigate 35%, Galleon 40%). Without a ship → 100g
      ferry ticket, full time.
- [x] Sea cargo: load compares against the **ship's** capacity (Sloop 40 wt,
      Galleon 180 wt). Over 1.8× the ship's cap → sailing blocked with a
      message; between cap and 1.8× → ETA penalty.
- [x] Ferry with cargo → max penalty but never blocked (no ship = capacity 0).
- [x] Frigate should visibly reduce sea events vs the Galleon (30% vs 15%
      mitigation).
- [x] World map: sea prompt shows the ship's name; mixed land+sea routes apply
      each leg's own vehicle capacity to that leg's ETA.

### B6. Monthly maintenance bills

- [x] Own a Sloop + a Caravan, note your gold, then advance time past a month
      boundary (day 1, 31, 61…).
- [x] On the 1st: bill = Sloop 20g + Caravan 80g = 100g deducted immediately;
      terminal prints the breakdown; GUI shows the Event Notice popup on city
      return + a journal entry.
- [x] Debt: with less gold than the bill, gold goes **negative**. While
      negative, shops/merchants refuse purchases until repaid.
- [x] No ship and no high-tier mount (War Horse/Caravan) → no bill at all.
- [x] A multi-day jump crossing a month end bills once per month crossed.

### B7. Save / load

- [x] Save mid-test with cargo, ship, and negative gold → reload → all persist.
- [x] A pre-cargo save loads cleanly (empty cargo market state, no ship errors).

---

## Regression checks

- [x] Shop main menu indices still work (Buy / Sell / Backpack / Stats /
      Cargo Market / Back).
- [x] Selling normal items at every merchant works (no crashes from the
      sell-list refactor).
- [x] World map travel animation + ferry prompt work end-to-end.
- [x] A normal dungeon run is unaffected.

## Known tunables if something feels off

| Symptom | Knob |
|---|---|
| Cargo too profitable | lower `CITY_DEMAND` high values / raise `BUY_MULT` |
| Cargo never worth it | raise demand values / lower weights |
| Overload too lenient | lower `OVERLOAD_CAP` (1.8) |
| Bills too punishing | lower `monthly_fee` on ships / mounts |
