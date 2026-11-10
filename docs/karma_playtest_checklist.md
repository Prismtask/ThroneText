# Karma Playtest Checklist — v0.1.8.8

> Scope: the **City Favor → Karma full replacement** shipped in v0.1.8.8, plus
> regression checks for the Phase 1–3 Karma systems. The critical question is:
> **does any current gameplay surface still read, write, or display City Favor?**
>
> Expected tuning values are listed in §8. Record any mismatch there rather than
> retuning mid-run.

## 0. Prep

- [x] Back up `savefile/`.
- [x] Run the automated pre-flight:
      `.venv\Scripts\python.exe tests\_diag_karma.py`
      `.venv\Scripts\python.exe tests\_diag_karma_phase2.py`
      `.venv\Scripts\python.exe tests\_diag_karma_phase3.py`
      `.venv\Scripts\python.exe tests\_diag_item_economy.py`
      `.venv\Scripts\python.exe tests\_diag_dispatch.py`
      `.venv\Scripts\python.exe tests\_diag_version_consistency.py`
- [x] Have three saves ready:
  - a fresh **Karma ON** character;
  - a fresh **Karma OFF** character;
  - an old save that still contains `favor` data in its JSON.
- [x] Have a high-Karma and low-Karma save available for the guild/shop spot checks,
      or be prepared to earn the thresholds through choices.

---

## 1. City Favor removal — critical

- [ ] Shop header contains **no** “City Favor” text.
- [ ] Blacksmith price line contains **no** “City Favor” text.
- [ ] Guild hall header contains **no** “Favor” value; it shows **Karma** when enabled.
- [ ] Active-bounty UI shows only the gold reward, not a favor reward.
- [ ] Dispatch report and collection log show no Favor line.
- [ ] `heal_wounded` success shows gold and Karma, never a favor gain.
- [ ] New Moon Festival mentions **bounty gold**, never favor.
- [ ] No current gameplay screen presents a per-city standing score.
- [ ] Old save with `player["favor"]` loads, saves, and reloads without errors.

---

## 2. Shop and blacksmith

- [ ] Shop header math matches the actual price.
- [ ] Karma ON header shows `Charisma … | Karma <tier> (<value>) … → <final>%`.
- [ ] No guild-city/non-guild-city price difference remains.
- [ ] Charisma 88 + Paragon reaches **60% off** (not 70%).
- [ ] Charisma 8 + Outlaw reaches the **−20% surcharge** floor.
- [ ] Tax Day is waived at high Karma and doubled at low Karma.
- [ ] Blacksmith enhancement/commission/fusion prices follow the same formula.
- [ ] **Karma OFF:** header is Charisma-only; no Karma or Favor segment.
- [ ] **Karma OFF:** Charisma 88 gives **40% off**; Charisma 8 gives no discount.

---

## 3. Guild bounties

- [ ] Neutral Karma board has **2** contracts.
- [ ] **+100 Karma** board has **7** contracts, higher target levels, and higher gold.
- [ ] **+80 Karma** board has **6** contracts.
- [ ] **−25 or lower Karma** board has **2 normal contracts + 1 Atonement contract**.
- [ ] Low-Karma normal bounties pay visibly less gold.
- [ ] No bounty entry, menu option, or turn-in line contains `reward_favor`/“Favor”.
- [ ] Normal bounty turn-in pays **gold only**; event bonuses add gold.
- [ ] Atonement turn-in grants **+5 Karma** and gold, with no Favor.
- [ ] **Karma OFF:** no Karma header, no Atonement contract, and level-scaled contracts only.
- [ ] **Karma OFF:** board is still **2** contracts at neutral.

---

## 4. Events, dispatch, and dungeon events

- [ ] New Moon Festival description says **+25% bounty gold**.
- [ ] New Moon increases bounty gold on turn-in.
- [ ] Bounty Rush description says **bounty gold +50%**.
- [ ] Bounty Rush increases bounty gold on turn-in.
- [ ] New Moon + Bounty Rush stack to **+75%** if both are active.
- [ ] Dispatch sweep report includes no Favor reward.
- [ ] Dispatch collection shows gold/items/EXP only.
- [ ] `heal_wounded` success grants gold and the normal **+2 Karma**; no Favor gain or loss.
- [ ] `heal_wounded` failure does not change favor (it no longer exists).

---

## 5. Karma regression

### Choices and caps
- [ ] Karma is applied when a choice is committed, before the stat roll.
- [ ] Positive repeatable Karma stops at **+8/day**.
- [ ] Negative Karma is uncapped.
- [ ] One-time quest/story rewards can bypass the daily cap.
- [ ] No automatic Karma drift from routine bounties or dispatch.

### Gates, guards, and jail
- [ ] Gate triggers once per travel/menu arrival at **−25** or lower.
- [ ] First low-Karma arrival is a warning.
- [ ] Suspect entry offers pay/turn away with no guard fight.
- [ ] Wanted/Outlaw entries offer pay, talk down, submit, fight, or leave.
- [ ] Guard fights are non-lethal and grant no XP/loot/bestiary/capture credit.
- [ ] Defeat or submission goes to jail, not the death screen.
- [ ] Jail clamps the fine, advances to morning, heals the party, and grants **+3 Karma** when eligible.
- [ ] Jail atonement respects the 3-day cooldown and shared daily cap.
- [ ] Blackwake/Wonderland/Event Horizon never gate.

### Atonement
- [ ] Temple Act of Contrition costs 50g/point and stops at 0.
- [ ] Contrition shares the **+8/day** cap.
- [ ] Guild Atonement contract appears at −25 or lower and grants **+5 Karma**.

### Blackwake
- [ ] No gate, guards, jail, guild, or bounty board.
- [ ] Negative Karma gets inverse Black Market pricing.
- [ ] Negative Karma gets the **50g smuggler ferry**; positive Karma pays normal fare.
- [ ] Blackwake innkeeper uses outlaw/saint dialogue lines.
- [ ] Positive Karma still forgoes the outlaw discount.

### Other Karma surfaces
- [ ] Outlaw crate appears only at **−25 Karma or lower** and not in Wonderland.
- [ ] Capture slaver gives +60% gold and **−5 Karma**; release gives **+1**.
- [ ] Hallucination tier shifts at **±50 Karma** and still requires fatigue stack II.
- [ ] Travel moral event: help **+2**, rob gold and **−3**, leave **0**.
- [ ] Inventory → Character → Personal Information shows Karma tier and recent history.
- [ ] Wonderland has no Karma gate, dialogue, or hallucination shift.

---

## 6. Karma OFF and old saves

- [ ] Fresh Karma-OFF character has no Karma top-bar line.
- [ ] No gate, guards, or jail.
- [ ] Shop/blacksmith use Charisma-only pricing.
- [ ] Guild board is level-scaled with no Karma or Atonement contract.
- [ ] Slaver capture option is hidden.
- [ ] Blackwake has normal prices, no inverse Karma.
- [ ] No Karma hallucination shift.
- [ ] Old save with `favor` data loads without a Favor UI; the JSON may keep the data.
- [ ] Save/load preserves `karma`, `karma_log`, and `karma_gate`.
- [ ] Re-saving an old save does not create new favor writes.

---

## 7. Text and stability

- [ ] Search current gameplay text for “City Favor” and “Favor”: only unrelated
      item/skill names (e.g. Cheshire Cat’s Favor, Fate’s Favor) may remain.
- [ ] No `reward_favor`, `favor_bonus`, or `player["favor"]` access appears in
      shop, guild, dispatch, dungeon-event, or inventory-bounty UI behavior.
- [ ] No traceback or console error in any checked flow.
- [ ] Save and reload once after each major section.

---

## 8. Expected values

### Guild board

| Karma | Normal contracts | Atonement | Reward multiplier | Level offset |
|---:|---:|---:|---:|---:|
| +100 / Paragon | 7 | — | ×1.50 | +5 |
| +80 / Paragon | 6 | — | ×1.40 | +4 |
| 0 / Neutral | 2 | — | ×1.00 | +2 |
| −50 / Wanted | 2 | 1 | ×0.75 | +1 |
| −100 / Outlaw | 2 | 1 | ×0.50 | +1 |

The Atonement contract is added only one per 7-day board refresh at Karma ≤ −25.

### Shop and blacksmith

| Case | Discount |
|---|---:|
| Charisma 88 + Paragon | **60% off** |
| Charisma 40 + Paragon | 36% off |
| Charisma 40 + Outlaw | 4% surcharge |
| Charisma 8 + Outlaw | 20% surcharge |
| Charisma 88, Karma OFF | 40% off |
| Charisma 8, Karma OFF | no discount |

### Bounty events

| Event | Bounty-gold effect |
|---|---:|
| New Moon Festival | +25% |
| Bounty Rush | +50% |
| Both active | +75% |

---

## 9. Pass criteria

- All critical §1 checks pass: **no current gameplay surface reads, writes, or displays City Favor**.
- Guild contracts and shop prices match §8.
- Karma OFF is fully playable with Charisma-only pricing and level-scaled contracts.
- Old saves preserve `favor` data but never use it.
- No traceback and no new diagnostic failures.

## 10. Notes / observations

```text
Date:
Save / character:
Karma value:
Observed board size:
Observed shop math:
Mismatches:
```
