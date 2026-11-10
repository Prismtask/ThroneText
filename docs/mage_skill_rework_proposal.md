# Mage Skill Rework — Time Warp & Cataclysm

**Status:** ✅ Implemented 2026-10-24 in v0.1.8.2 — playtest pending — **Date:** 2026-10-24
**Scope:** `resources/skill_book/skill_list.yaml`, `combat/skills.py`, `combat/player_actions.py`, `combat/combat_engine.py`, `combat/superboss_common.py`, `combat/combat_ui.py`, `tests/_temp_gen_skills_wiki.py`, `version.py`, changelog / wiki
**Related:** [`player_skill_extension_design.md`](./player_skill_extension_design.md) · [`mastery_extension_design.md`](./mastery_extension_design.md)

**Summary:** two Mage changes:

1. **Time Warp** keeps its cooldown reduction and additionally grants the player one immediate **free action**. This is too strong for the Tier 2 band, so **Time Warp and Elemental Focus swap acquisition levels** (Elemental Focus → Lv 12, Time Warp → Lv 20).
2. **Cataclysm** stops being a single massive Fire nuke. It becomes **seven elemental strikes** — one for each element (Fire, Water, Thunder, Wind, Earth, Light, Dark) — with **Inferno retained** on the Fire strike.

---

## 1. Current state

| Skill | Level | Tier band | CD | Current effect |
|---|---:|---|---:|---|
| Time Warp | 12 | Tier 2 (10–15) | 7 | Reduce all skill cooldowns by 2 turns |
| Elemental Focus | 20 | Tier 3 (20–32) | 6 | +15% elemental damage for 3 turns |
| Cataclysm | 40 | Tier 4 capstone | 9 | Massive Fire damage to all enemies + Inferno (18/turn, 4 turns) |

Tier bands are the Skill Book bands defined in `facilities/skill_book.py`:

- Tier 1 — Lv 3–8
- Tier 2 — Lv 10–15
- Tier 3 — Lv 20–32
- Tier 4 — Lv 40+ (capstone)

---

## 2. Time Warp

### 2.1 Proposed effect

> **Time Warp** — *Lv 20 · CD 7 · self · Magical* — Bend time: reduce all your skill cooldowns by 2 turns. Casting it is a **free action** — the action menu immediately reopens and you act again in the same turn.

The original cooldown reduction is unchanged. The new part follows the **Fractured Hourglass** pattern: the skill resolves, goes on cooldown, and does not consume the turn, so the player chooses another action immediately.

### 2.2 Tier verdict — move it to Tier 3

At Lv 12 the free action is too strong for Tier 2:

- It is effectively a **free spell every 7 turns** (~+14% action economy before cooldown acceleration).
- It also reduces every other cooldown by 2, so the real throughput gain is closer to +20–25%.
- Compare Tier 2 peers: Second Wind (30% self-heal), Venomous Blade (DoT), Meteor (one AoE hit). A free action is a capstone-grade tempo effect.

**Recommendation: swap levels.**

| Skill | Old level | New level | New tier band |
|---|---:|---:|---|
| Elemental Focus | 20 | **12** | Tier 2 |
| Time Warp | 12 | **20** | Tier 3 |

No other Mage skill changes level. Tier 3 then reads: **Time Warp (20) → Glacial Prison (26) → Arcane Singularity (32)**, which is a clean utility/control/damage progression.

### 2.3 Implementation notes

Time Warp should be a **free action in the same turn**, using the same mechanism as the Fractured Hourglass, Blank Canvas Shawl and Brush Stance: the handler performs the effect and returns `"retry"`, which reopens the action menu without consuming the turn. Do **not** insert an extra turn into `turn_order`.

1. **YAML:** add a generic key to `mage_timewarp`:
   ```yaml
   free_action: true
   ```
   Keeping it generic means future skills can reuse the mechanic without new hardcoded skill-id checks.

2. **`combat/skills.py` — Time Warp branch:**
   - Keep `reduce_all_cooldowns(player, skill.get("cooldown_reduction", 2))`.
   - Set a transient flag, e.g. `player["_skill_free_action"] = True`, when the definition has `free_action`.
   - Do **not** set the flag if the cast was cancelled.

3. **`combat/player_actions.py` — skill path:** after `execute_skill()`, firing `on_kill`, victory re-check and `set_skill_cooldown()`, clamp a free-action skill's own cooldown to at least 1 and pop the flag:
   ```python
   if skill_def.get("free_action"):
       player["skill_cooldowns"][skill_id] = max(1, player["skill_cooldowns"][skill_id])
   free_action = player.pop("_skill_free_action", False)
   ...
   if free_action:
       return "retry", False   # same turn continues — menu reopens
   ```
   The `while True` loop around `handle_player_turn()` already treats `"retry"` as "reopen the menu without consuming the turn", exactly like the Fractured Hourglass.

4. **Cooldown ordering / recast guard:** `set_skill_cooldown()` must run **before** the `"retry"` return, so Time Warp is on cooldown when the menu reopens. Clamp its cooldown to at least 1 (`player["skill_cooldowns"]["mage_timewarp"] = max(1, ...)`) so stacked reductions — or a wedding cooldown-skip proc — can never allow a same-turn loop.

5. **Cleanup:** `_skill_free_action` is transient combat state. Clear it in `combat/combat_engine.py` `clear_battle_scoped_state()` (and defensively at the start of a fresh player turn) so it cannot leak into a later action or save.

6. **Abyss Tempo helper:** `superboss_common.superboss_triple_action_loop()` now loops on `"retry"`, so a Time Warp cast during an Abyss Tempo extra action also keeps its free action instead of dropping it.

7. **GUI / turn order:** no changes. There is no extra turn entry and no new label; the existing action menu simply reappears. This is why the hourglass pattern is preferred over the Abyss Tempo/Berserk extra-turn approach.

### 2.4 Playtest levers

- If it overperforms at Lv 20: raise CD 7 → 8 first. Do not remove the free action — that is the point of the rework.
- If it underperforms: CD 7 → 6, or increase the cooldown reduction from 2 to 3.
- The free action is part of the same turn, so stun/skip checks already happened at turn start; do not add a second skip roll when the menu reopens.

---

## 3. Cataclysm

### 3.1 Proposed effect

> **Cataclysm** — *Lv 40 · CD 9 · all enemies · capstone* — The heavens split. **Seven elemental catastrophes** strike in sequence — Fire, Water, Thunder, Wind, Earth, Light and Dark. Each strike deals damage with its own element and resistance check. The Fire strike leaves its target in **Inferno**.

The single massive Fire hit is gone. Cataclysm becomes a **prismatic barrage** that exploits elemental weaknesses instead of stacking one resistance check.

### 3.2 The seven strikes

| Strike | Element | Extra effect |
|---:|---|---|
| 1 | Fire | Applies Inferno (18/turn, 4 turns) |
| 2 | Water | — |
| 3 | Thunder | — |
| 4 | Wind | — |
| 5 | Earth | — |
| 6 | Light | — |
| 7 | Dark | — |

**Why all seven:** the game has seven elements, and Cataclysm is the Mage's capstone — it should showcase the full elemental spectrum. The order matches `combat/elemental.py` `ELEMENTS`, so the skill reads naturally alongside the rest of the system. Only Fire carries an extra effect (Inferno); the other six are pure damage.

### 3.3 Damage budget

The existing damage formula is:

```
power per hit = int((base_power + scaling) * power_mult)
scaling       = Learning + Learning // 2   # primary + secondary Learning
```

Because **scaling is added to every hit**, a naïve 7-hit all-enemy AoE would deal roughly 7× the intended damage. The proposal therefore uses **one strike per enemy, spread round-robin**, not seven full AoE waves.

Recommended: **`base_power: 8` per strike**.

Sample at Lv 40 with Learning 40 (scaling 60) and neutral resistances:

| Scenario | Current Cataclysm | Proposed Cataclysm |
|---|---:|---:|
| 1 enemy | 90 direct + 72 burn = **162** | 7 × 68 + 72 burn = **548** |
| 5 enemies | 5 × 90 + 5 × 72 burn = **810** | 7 × 68 + 72 burn = **548** |

- Single-target damage rises sharply — seven hits is a true capstone barrage.
- Crowd damage falls, because the old version burned every enemy. That is the deliberate trade: Cataclysm becomes a **boss/weakness killer**, not a trash-clearer. Against five enemies the seven strikes still total 548, spread across the field.
- Elemental multipliers (Elemental Focus, Evoker passive, gear) can push individual strikes above the neutral sample, while resistant enemies reduce them. Expected value stays close to the table.

Tuning range: **6–10** base power. Start at 8; adjust after a Lv 40 playtest.

### 3.4 Targeting

- Each strike picks a random living enemy that has **not yet been struck this cast**.
- If every living enemy has been struck (fewer enemies than strikes), clear the list and start again.
- With one enemy, all seven strikes hit it.
- With five enemies, the first five strikes hit each enemy once; the remaining two begin a new cycle and hit random living enemies again.
- Elements are fixed in `ELEMENTS` order — Fire, Water, Thunder, Wind, Earth, Light, Dark — rather than randomly chosen.

This keeps the AoE feel and avoids 49 damage lines (7 strikes × 7 enemies).

### 3.5 Mastery

| Mastery | Upgrade |
|---|---|
| ★ / ★★ | Power scaling as usual |
| ★★★ | The Fire strike's Inferno upgrades to **Conflagration** via the existing `burn_tier_bonus` |
| ✦ / ✦✦ | Further power scaling; burn cap remains Conflagration |

Seven strikes is the hard cap — mastery does not add an eighth hit. The elemental spread is already complete at base, so mastery invests in damage and burn quality instead.

### 3.6 Implementation notes

1. **YAML** (`resources/skill_book/skill_list.yaml`):
   ```yaml
   mage_cap_cataclysm:
     name: Cataclysm
     description: Seven elemental catastrophes strike in sequence — Fire, Water,
       Thunder, Wind, Earth, Light and Dark. The Fire strike leaves its target
       in Inferno.
     unlock_level: 40
     cooldown: 9
     target: enemies
     power_type: ler
     base_power: 8
     elements: [fire, water, thunder, wind, earth, light, dark]
     burn_damage: 18
     burn_duration: 4
     capstone: true
   ```
   Keep `target: enemies` so the action menu and Skill Book still treat it as an AoE capstone.

2. **`combat/skills.py`:** add a bespoke branch in the `target_type == "enemies"` block, next to the other capstones:
   - Set `total_hits = 0` to neutralise the generic loop.
   - Build the strike list from `skill.get("elements", [...])` — all seven always, in `ELEMENTS` order.
   - For each strike: pick an unstruck living target, compute `power`, call `_calc_dmg(target, power, element=el)`, subtract HP, and log with `format_damage_msg(..., element=el, skill_name=skill["name"])`.
   - Apply Inferno only on the Fire strike (if the target survives), via `apply_burn(target, b_tier, skill.get("burn_duration", 4))` with the existing `damage_to_burn_tier` + `burn_tier_bonus` logic.
   - Call `_apply_life_steal(dmg)` per strike, same as other capstones.
   - After the loop, run the standard victory check and prune dead enemies.

3. **`combat/combat_ui.py`:** `format_skill_elemental_tag()` reads only `skill_def["elemental"]`. Extend it to detect `elements` and show a neutral `[MULTI]` tag; otherwise the skill shows no element tag at all. Per-hit log lines already get the correct element from `format_damage_msg()`.

4. **Description and docs:** update the YAML description, README Mage section, `wiki/index.html`, and the changelog bullet. `facilities/skill_book.py` tier bands update themselves from `unlock_level`.

### 3.7 Risks

- **Elemental profile mismatch:** a Fire-specialised mage may get less from non-Fire strikes. Elemental Focus and the Evoker passive (+% to all elements) are the intended answers; call this out in the description.
- **Proc multiplication:** seven `_calc_dmg()` calls mean seven crit rolls and seven on-hit triggers (wedding accessories, life steal, Prescript Ledger). This is already true of Onslaught and Skyfall Volley, but verify with the relevant uniques.
- **Log volume:** cap the output at one line per strike — seven lines maximum. Do not print a separate line per enemy per strike.
- **Overkill:** later strikes can hit an already-dead target if deaths are not pruned between strikes. Re-check `hp > 0` before each strike.

---

## 4. Final Mage ladder after both changes

| Level | Tier | Skill | Change |
|---:|---|---|---|
| 3 | 1 | Fireball | — |
| 5 | 1 | Frost Nova | — |
| 8 | 1 | Arcane Barrage | — |
| 10 | 2 | Meteor | — |
| 12 | 2 | **Elemental Focus** | Moved down from 20 |
| 15 | 2 | Mana Overload | — |
| 20 | 3 | **Time Warp** | Moved up from 12; gains a free action |
| 26 | 3 | Glacial Prison | — |
| 32 | 3 | Arcane Singularity | — |
| 40 | 4 | **Cataclysm** | Reworked into seven elemental strikes |

The Battle Loadout is unaffected: a new Mage still reaches the 9-skill cap at Lv 32, and Cataclysm still needs a manual swap at Lv 40.

---

## 5. Save compatibility

- `unlock_skills_for_level()` only **adds** skills; changing `unlock_level` never removes anything.
- Existing Mages who already learned Time Warp at Lv 12 **keep it**. This is intentional — skills are permanent unlocks, and retroactively removing one would feel like a bug.
- No new persistent player fields are needed. `_skill_free_action` is transient combat state; `clear_battle_scoped_state()` clears it defensively.
- New characters and characters below Lv 12 see the new order immediately.

If strict tier enforcement is ever required, it needs an explicit migration that removes `mage_timewarp` from `skills` and `skill_loadout` below Lv 20 — **not recommended** for a balance pass.

---

## 6. Testing checklist

- [x] Time Warp is a free action: the action menu reopens and the player can act again in the same turn.
- [x] Time Warp's own cooldown is set before the menu reopens; it cannot be recast in the same turn even with stacked cooldown reductions.
- [x] Cancelling Time Warp grants no free action and no cooldown (Time Warp has no target selection, so there is no cancel path).
- [x] Free action works in the standard `handle_player_turn` path; the superboss Abyss helper now also loops on `"retry"` (manual superboss playtest pending).
- [x] No extra turn entry appears in the turn order / GUI.
- [x] Cataclysm fires 7 strikes, one per element in `ELEMENTS` order; each uses the correct element and resistance check.
- [x] Fire strike applies Inferno; other strikes do not apply burn.
- [x] Cataclysm works with 1 and 5 living enemies; round-robin spread is correct; no dead-target hits; victory path uses the standard check.
- [x] Wiki shows Elemental Focus in Tier 2, Time Warp in Tier 3, and Cataclysm's multi-element tag; in-game Skill Book manual check pending.
- [x] Old save smoke test: `savegame_3` (Lv 12 Mage) loads cleanly, keeps the already-learned Time Warp, and load-time catch-up adds Elemental Focus.
- [x] `tests/_diag_local_imports.py` ran (one pre-existing warning in `combat/status_effects.py`, unrelated to this change); `tests/_temp_mage_skill_rework_check.py` passes.
- [x] Version bumped to 0.1.8.2 and changelog block prepended; `tests/_diag_version_consistency.py` passes.

### Verification log (2026-10-24)

- `tests/_temp_mage_skill_rework_check.py` — all checks passed (YAML, tags, free action, 7 hits, round-robin, Inferno, mastery burn).
- `tests/_diag_fractured_hourglass.py` — all checks passed (free-action regression).
- `tests/_temp_target_cancel_check.py` — all checks passed.
- `tests/_diag_prescript_ledger.py` — all checks passed.
- `tests/_diag_combat_ticker.py` — all checks passed.
- `tests/_diag_version_consistency.py` — `version consistency OK: v0.1.8.2 — The Distant Journey`.
- `tests/_temp_gen_skills_wiki.py` — regenerated `docs/monster_girls_skills_wiki.md` and `wiki/index.html`.
- Read-only old-save smoke test — `savegame_3` (Lv 12 Mage) loads; keeps Time Warp and gains Elemental Focus on `ensure_player_fields()`.

Remaining: manual in-game Skill Book / combat playtest.

---

## 7. Locked decisions (2026-10-24)

1. **Cataclysm hits:** seven hits total, one per element.
2. **Targeting:** round-robin across living enemies.
3. **Element set:** all seven elements at base — Fire, Water, Thunder, Wind, Earth, Light, Dark.
4. **Inferno:** retained on the Fire strike.
5. **Time Warp timing:** immediate free action in the same turn, following the Fractured Hourglass pattern.
6. **Tier swap:** confirmed — Elemental Focus → Lv 12, Time Warp → Lv 20.

No open decisions remain. Implemented in v0.1.8.2; remaining work is playtest and an old-save smoke test.
