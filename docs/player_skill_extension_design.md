# Player Skill Extension — Second Wave · Capstones · Profession Branching

**Status:** ✅ All phases shipped 2026-10-15 — wave 2 + capstones + Battle Loadout + professions live in-game; playtest pending — **Date:** 2026-10-15
**Scope:** `resources/skill_book/skill_list.yaml` (`class_skills` + new `professions`), `combat/skills.py`, `combat/action_menu.py`, `facilities/guild.py`, `facilities/skill_book.py`, `gui/screens/inventory_screen.py`, wiki generator
**Related:** [`barracks_skills_audit.md`](./barracks_skills_audit.md) (§2: the campaign has outgrown the 3–15 ladder) · [`mastery_extension_design.md`](./mastery_extension_design.md) · [`barracks_tier_5_6_proposal.md`](./barracks_tier_5_6_proposal.md)

**Summary:** adds ~80 new player actives + 16 upgraded passives across three phases — a second class-skill wave (Lv 20/26/32), one capstone per class (Lv 40, CD 9), and an exclusive **profession branch** chosen after the capstone (signature skill + upgraded class passive on choice, Lv 50/60 skills, permanently locking the other branch). Adds a **9-skill Battle Loadout** cap to keep the growing pool menu-manageable. Fixes the "full kit by level 15 in a level-60 campaign" problem without touching the early-game ladder.

---

## 1. Problem (as-built facts)

| Fact | Value |
|---|---|
| Class actives | 6 per class (48 total) at Lv **3 / 5 / 8 / 10 / 12 / 15** + 1 passive |
| Player's entire active kit source | `class_skills` YAML only — nothing else feeds `player["skills"]` |
| Campaign length | Player cap **60**, enemy level up to **57**, 40–60+ floor dungeons, Wonderland 48 floors |
| Post-15 skill progression | Mastery (★✦✦) only — same 6 buttons, bigger numbers |
| Ally comparison | 2 innate + race passive + up to 3 learned (47-skill pool, 6 tiers to Lv45/Cap50) + heroine upgrades + awakening |

- The last class skill unlocks **one level after the first ascension** (10→20). Everything after that is mastery.
- XP to Lv 15 is roughly **~23k of ~700k** XP to cap 60 — the kit completes at ~3% of the journey.
- `docs/barracks_skills_audit.md` §2 already names the cause: the 3–15 ladder is launch-era pacing the campaign has outgrown.

**Goal:** the ladder should deliver a new decision at regular intervals from Lv 20 to 60, ending in a build-defining, exclusive choice.

## 2. Agreed direction (locked 2026-10-15)

1. **Wave 2** — three new class actives at Lv 20/26/32 (all classes, no choice).
2. **Capstone** — one class-defining ultimate at Lv 40 (behind the cap-40 ascension), cooldown 9.
3. **Profession branch** — *after the capstone*, a one-time **permanent** choice of 2 professions per class; grants 3 exclusive actives **plus an upgraded class passive**, and locks out the other branch forever.
4. **Battle Loadout** — at most **9 skills equipped** per fight (answers menu growth with a design lever; full rules in §7).
5. **Ceremony** — plain Guild ceremony (class-specific quest chains deferred).

## 3. The proposed ladder (final target)

| Level | Content | Gate |
|---|---|---|
| 1 | Class passive | — |
| 3–15 | Existing six actives | — |
| 20 / 26 / 32 | **Wave 2** (3 actives) | Lv 20 needs cap-20 ascension (1 biome @ floor 10) |
| 40 | **Capstone** (1 class ultimate) | Cap-40 ascension (3 biomes @ floor 30) |
| 40+ | **Profession ceremony** (Guild) → **signature skill + upgraded class passive** granted immediately | Capstone known |
| 50 / 60 | 2 more profession skills | Cap-50 ascension (4 biomes @ floor 40) / cap-60 (5 biomes @ floor 50) |

Endgame kit: 6 + 3 + 1 + 3 = **13 actives**, of which **9 can be equipped** at once (§7 Battle Loadout). Spacing confirmed: 20/26/32 · 40 · 50/60.

## 4. Phase 1 — Wave 2 (Lv 20/26/32, 24 skills)

Extends each class's existing identity. All listed effects use primitives the player engine **already supports** (DoTs, buffs, stuns, drains, marks, stat debuffs).

| Class | Lv 20 | Lv 26 | Lv 32 |
|---|---|---|---|
| Warrior | *Reckless Charge* — heavy hit, self vulnerable 1 turn | *War Banner* — party STR buff + minor regen | *Titan's Swing* — armor-ignoring heavy single hit |
| Mage | *Elemental Focus* — +elemental damage self buff | *Glacial Prison* — single-target freeze (stun + water) | *Arcane Singularity* — AoE magical + slow |
| Rogue | *Caltrops* — AoE bleed + slow | *Nightshade* — toxic hit + strong poison | *Perfect Opening* — +crit chance / crit damage buff |
| Cleric | *Prayer of Mending* — ally regen (HoT) | *Blessed Aegis* — ally barrier ⚠️ port | *Wrath of Heaven* — AoE light damage |
| Ranger | *Camouflage* — self evasion + crit buff | *Blast Arrow* — AoE fire burst | *Hawk's Eye* — crit buff w/ mark synergy |
| Paladin | *Blessing of the Faithful* — ally DR + small heal | *Censure* — damage + weaken | *Dawnbreaker* — heavy holy + blind |
| Warlock | *Grasp of the Void* — dark dmg + slow + DoT | *Blood Pact* — pay HP for a power buff | *Siphon Soul* — big drain + self heal |
| Barbarian | *Battle Trance* — +STR / crit self buff | *Reckless Abandon* — +crit dmg, self vulnerable | *Skullbreaker* — heavy hit + stun |

⚠️ = needs an engine port from the ally side (see §6.7). True effects are preferred over substitutions (decided — never water a skill down to ship it early). ✓ *Blessed Aegis* shipped with the **real barrier** — `status_effects.apply_barrier` + `enemy_ai` absorption already covered player and allies; only the casting branch was missing.

## 5. Phase 2 — Capstones (Lv 40, 8 skills) — ✅ shipped 2026-10-15

One per class; cooldown **9** (decided — above the current 5–7 ultimates). Each has a condition/payoff loop, not just bigger numbers.

| Class | Capstone | Concept |
|---|---|---|
| Warrior | *Onslaught* | 5-hit flurry on random enemies; final blow executes below 30% |
| Mage | *Cataclysm* | Massive AoE + burn |
| Rogue | *Death's Embrace* | Execute below 35%; a kill refunds the cooldown |
| Cleric | *Providence* | Full-party heal + revive one fallen ally with a shield |
| Ranger | *Skyfall Volley* | AoE multi-hit + slow |
| Paladin | *Heaven's Sword* | Massive single-target holy; party heals for damage dealt |
| Warlock | *Dark Apotheosis* | Self empower + AoE drain |
| Barbarian | *Wrath Incarnate* | AoE crush + stun chance + self heal |

The capstone being known is the **prerequisite for the profession ceremony**.

## 6. Phase 3 — Profession branching (exclusive) — ✅ shipped 2026-10-15

### 6.1 Rules

1. **One-time choice** at the Guild, available once the class capstone is unlocked (Lv 40). Two professions per class.
2. **Per profession: 3 exclusive actives** — signature granted immediately on choosing; one at Lv 50; one at Lv 60.
3. **Per profession: an upgraded class passive** — replaces the base passive on choosing (designs in §6.3).
4. **Permanent** — no respec (decided 2026-10-15). The ceremony confirm states it explicitly.
5. **Identity surfaces:** character screen ("Warrior — Warlord"), skill book / wiki show both branches with the chosen one active and the other labelled *Locked — chose Warlord*. Guild ceremony shows an explicit two-step confirm ("This choice is permanent").
6. Mastery, cooldowns, and Arcane Tower research apply to profession skills automatically (they are skill-agnostic systems).

### 6.2 Profession roster (8 × 2, 48 actives)

**Signature (on choice) · Lv 50 · Lv 60**

| Class | Profession A | Profession B |
|---|---|---|
| **Warrior** | **Warlord** (command offense) — *Iron Command* party power buff, clears fear · *Decimation* AoE + sunder · *Warlord's Reign* mark all; party deals +dmg | **Sentinel** (defense) — *Guardian Stance* self DR + counter stance · *Living Fortress* party DR · *Unbreakable* survive-lethal ward |
| **Mage** | **Evoker** (elemental destruction) — *Overchannel* +spell power, recoil · *Prismatic Ray* big random-element hit · *Arcane Ascension* AoE + self empower | **Chronomancer** (time) — *Temporal Acceleration* party cooldown refund · *Time Stop* stun/slow all · *Rewind* restore HP + heavy self cooldown refund |
| **Rogue** | **Assassin** (execution) — *Mark for Death* +dmg taken · *Mortal Blow* execute · *Thousand Cuts* multi-hit single target | **Shadowdancer** (evasion/affliction) — *Veil of Shadows* party evasion · *Nightmare Requiem* AoE fear + dark DoT · *Shadowfall* AoE dark + bleed |
| **Cleric** | **Hierophant** (restoration) — *Sanctuary* party regen + cleanse · *Greater Resurrection* revive 100% + shield · *Eternal Light* party heal + death ward | **Inquisitor** (holy offense) — *Verdict* heavy holy + vulnerable · *Chains of Faith* stun + light DoT · *Day of Reckoning* AoE light, bonus vs debuffed |
| **Ranger** | **Sharpshooter** (crit) — *Steady Aim* +crit buff · *Killshot* execute · *Perfect Fusillade* crit multi-hit | **Warden** (nature) — *Bramble Grasp* AoE slow + bleed · *Toxic Bloom* AoE poison · *Nature's Wrath* AoE earth + entangle |
| **Paladin** | **Crusader** (offense) — *Condemn* stun + vulnerable · *Avenging Crusade* dmg scales w/ missing HP · *Final Judgment* massive single + party heal | **Templar** (protection) — *Aegis* party barrier · *Unbreakable Oath* death ward on ally · *Bastion Eternal* party DR + regen |
| **Warlock** | **Nethermancer** (affliction) — *Wither* heavy DoT · *Feast of Shadows* AoE drain, self heal · *Dominion of Dread* AoE fear + vulnerable + DoT | **Infernalist** (fire/sacrifice) — *Hellfire* AoE fire + burn · *Searing Chains* single fire + burn/root · *Infernal Avatar* +fire dmg + fire nova |
| **Barbarian** | **Berserker** (rage) — *Bloodrage* lifesteal + crit · *Rampage* multi-hit random · *Undying Rage* survive-lethal | **Juggernaut** (endurance) — *Unyielding* self DR + debuff resist · *Seismic Roar* AoE stun + sunder · *Mountain Breaker* massive single earth + self heal |

Naming notes: avoided **Archmage** and **High Priest** (Arcane Tower NPC title / Event Horizon boss name) — replaced with *Evoker* and *Hierophant*. *Sentinel* / *Warden* / *Juggernaut* overlap with mob names but remain clear in player-facing screens; skill **IDs** stay unique regardless.

### 6.3 Profession passive upgrades (upgraded class passive)

Choosing a profession **upgrades the class passive**: same passive slot, stronger original effect plus one new effect. 16 upgrades (8 classes × 2), using the player engine's existing effect vocabulary wherever possible.

| Class (base passive) | Profession A upgrade | Profession B upgrade |
|---|---|---|
| Warrior (Iron Will: CON +2) | **Warlord — Commanding Presence**: STR +2, CON +2 | **Sentinel — Living Bulwark**: CON +4, 10% damage reduction |
| Mage (Arcane Intellect: LER +2) | **Evoker — Elemental Mastery**: LER +3, +10% elemental damage [E] | **Chronomancer — Temporal Insight**: LER +2, all skills start combat with −1 cooldown [T] |
| Rogue (Sneak Attack: +25% vs impaired) | **Assassin — Lethality**: +40% vs impaired, +8% crit chance [C] | **Shadowdancer — Umbral Step**: +25% vs impaired, 8% evasion vs enemy attacks [V] |
| Cleric (Holy Favor: heal +20%) | **Hierophant — Blessed Hands**: heal +30%, 3% max-HP regen per turn [R] | **Inquisitor — Zealous Light**: heal +20%, +8% crit chance [C] |
| Ranger (Keen Eye: DEX +2) | **Sharpshooter — Deadeye**: DEX +3, +8% crit chance [C] | **Warden — Verdant Vigor**: DEX +2, 3% max-HP regen per turn [R] |
| Paladin (Aura of Courage: STR/CHA +1) | **Crusader — Zeal of Battle**: STR +2, CHA +1, +8% crit chance [C] | **Templar — Aegis Aura**: STR +1, CHA +2, 10% damage reduction |
| Warlock (Soul Siphon: 10% lifesteal) | **Nethermancer — Soul Feast**: 15% lifesteal, 8% damage reduction | **Infernalist — Infernal Vitality**: 10% lifesteal, +10% fire & dark damage [E] |
| Barbarian (Thick Skin: 15% DR) | **Berserker — Pain Fury**: 15% DR, +10% damage below 50% HP [L] | **Juggernaut — Unstoppable Hide**: 20% DR, CON +2 |

Hook legend: [E] elemental bonus · [T] combat-start cooldown · [C] crit chance · [V] evasion · [R] regen per turn · [L] low-HP damage. Unmarked entries use supported types (`stat`, `damage_reduction`, `heal_bonus`, `life_steal`, `vulnerable_bonus`).

**Engine notes**
- **Composite passives (required):** player passive reads currently assume one effect. Add `get_player_passive_effects(player)` (returns a list, mirrors the ally `multi` pattern in `get_race_passive_effects`) and iterate at the ~8 call sites (`combat/stats.py` ×1, `combat/skills.py` ~5, `combat/player_actions.py` ×2, `combat/enemy_ai.py` ×1).
- **New effect hooks (6 small):** crit chance → `get_raw_critical_chance`; elemental → `compute_player_elemental`; combat-start cooldown → both combat loops' start; evasion → enemy→player hit path; regen % → round-start tick (**both** loops: `combat_engine` + `superboss_common`); low-HP damage → player damage calc. **All six ship as true implementations** (decided 2026-10-15 — fidelity over cost; no substitution fallback).
- YAML shape: `professions.<Class>.<prof>.passive` with `name`, `description`, `effect`/`effects`. `get_passive_skill(player)` returns the profession version when chosen — skill book, inventory, and wiki displays update through the existing helper.

### 6.4 Why 2 professions, not 3

Binary choice reads instantly, halves the authoring (48 vs 72 skills), and the YAML schema stays extensible if a third branch is ever added.

### 6.5 Lockout — what it does *not* touch

- The player keeps every base/wave-2/capstone skill and all mastery progress.
- Cooldowns, skill book entries, and tower research for the chosen branch work like any skill.
- The lockout is enforced **at the class-map level** (§6.6), so even a hand-edited save cannot surface the other branch's skills.

### 6.6 Engineering

**YAML**
- Wave 2 + capstone are plain `class_skills` entries: `unlock_level: 20/26/32/40`; capstones add `capstone: true` (drives ceremony availability + wiki badge).
- New top-level block:

```yaml
professions:
  Warrior:
    warlord:
      name: Warlord
      tagline: "Command the field."
      skills:
        war_wl_iron_command: { name: Iron Command, ... }
        ...
    sentinel: { ... }
```

- ID conventions: wave 2 `war_*` (existing pattern), capstone `war_cap_*`, professions `war_wl_*` / `war_sent_*`.

**Code — one choke point**
- `get_class_skill_map(player)` becomes the single merge point: base class map + (if `player.get("profession")`) the chosen profession's skills. Downstream consumers update for free (verified callers): `unlock_skills_for_level`, `get_available_skills`, `get_all_unlocked_skills` (↳ action menu, Arcane Tower, skill book, inventory skills tab), `set_skill_cooldown`.
- **Lockout is automatic:** unchosen branches are simply absent from the merged map, so they can never unlock or appear.
- `unlock_skills_for_level` needs no changes.

**Save data**
- `player.setdefault("profession", None)` in `character.py` `ensure_player_fields()` (next to `level_cap`).
- Ceremony sets `player["profession"]`, then calls `unlock_skills_for_level(player)` so any already-eligible profession skills (a maxed save choosing at 60) arrive immediately.
- **Load catch-up already exists:** `ensure_player_fields()` calls `unlock_skills_for_level()` — existing high-level saves receive wave-2/capstone skills on first load after the update. No migration script needed.
- **Loadout init:** `skill_loadout` absent = "all unlocked equipped" (back-compat); see §7.

**Guild ceremony**
- New menu option "Choose Profession" in `facilities/guild.py` — visible when capstone skill is unlocked and `profession` is `None`. Two-step confirm with explicit permanence warning (the `term` abstraction covers both terminal and GUI facility modes).
- Failure/edge cases: profession already chosen → option hidden; capstone not known → option hidden (no dead UI).

**UI workstreams (per phase)**
- `facilities/skill_book.py`: `_display_player_skill_book` has **hardcoded tiers** ("Tier 1 (Level 3-8)" / "Tier 2 (Level 10-15)") — regroup by level band and add a profession section showing both branches (chosen active / other locked).
- `gui/screens/inventory_screen.py`: skills tab gets a profession header row; the rest follows the merged map.
- `combat/action_menu.py` + `gui/combat/action_panel.py`: the **Battle Loadout cap of 9** (§7) bounds the menu to 9 numbered skills — no submenu needed. Verify the GUI panel's 2-row reservation still holds at 9 skills + utility buttons; adjust `MIN_ROWS` if not.
- Wiki generator (`tests/_temp_gen_skills_wiki.py` / `gen_wiki_html.py`): class ladder table update, capstone badge, profession sections with lockout labels. Generator needs explicit branches for new keys (known pitfall — see repo notes).

**6.7 Engine ports needed (verified gap)**

The ally engine (`combat/ally_skills.py`) supports primitives the player engine (`combat/skills.py`) does not. Affected skills:

| Primitive | Used by | Notes |
|---|---|---|
| `barrier` | Blessed Aegis, Aegis, Living Fortress | Port absorb-pool + consumption sites for player |
| `death_ward` / survive-lethal | Unbreakable, Unbreakable Oath, Undying Rage, Eternal Light | Port from ally engine |
| `cleanse_one/all` | Sanctuary, Unyielding | Port from ally engine |
| Party-wide `evasion` buff | Veil of Shadows | Ally pattern exists; player buffs party via `pal_bastion`-style loop |
| Party-wide cooldown refund | Temporal Acceleration | `reduce_all_cooldowns` exists for self; party targeting is new |
| Counter/reflection stance | Guardian Stance | Cutlass riposte precedent; **not** wired as a generic stance for the player |

Everything else in §4–§6 uses existing player primitives. Ports can be scheduled freely, but ship as **true implementations** rather than substitutes (true-effect policy — see §11 #10).

**As built (2026-10-15):** the ports turned out to be almost entirely unnecessary — `apply_death_ward` (player consumption already wired), `is_cleansable`-based cleansing, `reflection` (read by `enemy_ai`), `apply_barrier`, per-member `evasion` buffs, and a small `_reduce_cooldowns_for` helper covered all 48 skills. Only new primitive: the `elemental_dmg_elem` single-element buff (Infernal Avatar).

**Tests**
- New `tests/_temp_player_skill_extension_check.py`: merge behavior, profession lockout (unchosen branch never unlocks even with stale save data), unlock gating at each level, ceremony one-time-only, save-sim (profession set → load → skills consistent), maxed-save choice grants 50/60 skills immediately.
- Keep `tests/_temp_barracks_patch_check.py` green (shared `get_mastery_bonuses`, thresholds).

## 7. Battle Loadout (max 9 skills per fight) — decided

**Rule:** the player equips up to **9 skills** for combat. Unlocked-but-unequipped skills cannot be used in battle; they stay fully visible in the skill book, and Arcane Tower research is unaffected.

- **Why 9:** matches the existing 1–9 numbered skill keys (no submenu, no new muscle memory), and creates a real decision only when the pool outgrows it: 6 → 9 with wave 2 (fits exactly), 10 with the capstone (first cut), 13 with the profession (4 cuts).
- **Data:** `player["skill_loadout"]` — ordered list of skill ids. Missing key (old saves) = "all unlocked equipped" back-compat. `unlock_skills_for_level` auto-appends while under cap and notifies "Loadout full — manage it at the Skill Book" when at cap.
- **Filter point:** a single helper `get_equipped_skill_ids(player)` consumed by `get_available_skills` and `is_skill_available` — the combat menu, HUD cooldown list, and target flow all follow automatically. `get_all_unlocked_skills` stays unfiltered (skill book, Arcane Tower).
- **Management UI:** Skill Book — a "Battle Loadout" section (equip/unequip, shows "Equipped X/9"); Inventory skills tab — equipped markers + counter. Both write the same field; swaps allowed **anywhere out of combat** (decided 2026-10-15).
- **Interactions:** gloves/brush kits replace the action menu entirely (unaffected); profession lockout and loadout compose (the locked branch is never in the pool; the loadout trims what remains).
- **As built (2026-10-15):** `MAX_SKILL_LOADOUT = 9` in `combat/skills.py`; `get_equipped_skill_ids` (missing key = all unlocked); `get_available_skills` + `is_skill_available` filter; `unlock_skills_for_level` auto-appends under cap, materialises the list at overflow, and marks queued skills "(battle loadout full — equip it at the Skill Book)". Management lives in the Skill Book menu ("Manage Battle Loadout"); the inventory skills tab shows ✓/– markers + counter. `get_all_unlocked_skills` deliberately stays unfiltered.

## 8. Balance guardrails

- **Mechanics over numbers** (audit §3): endgame flat scaling dominates, so capstones/profession skills buy conditions, statuses, and tempo — not base-power inflation.
- **Mastery interaction:** ✦✦ doubles status potency (`status_mult` 2.0). Set new debuff values with doubled endgame values in mind.
- **Cooldown budget:** capstone 9; profession 60s 6–8; keep one-tap AoE ultimates from stacking with Haste/Time Warp into every-turn casts.
- **Element coverage:** wave 2 / professions fill per-class fantasy; avoid duplicating an element a class already owns.
- **No parity ships:** don't release a skill that relies on an unported primitive (see §6.7).
- **Loadout pressure is the pacing tool:** the 9-slot cap (not cooldowns alone) is what makes capstone/profession picks trade off against the launch kit.

## 9. Save compatibility

- **Additive only** — nothing removed, no re-paced existing unlocks (avoids old-save/new-save divergence).
- `profession: None` default; branchless saves work identically until they choose.
- Existing saves receive wave-2/capstone skills **on load** via the existing `ensure_player_fields()` → `unlock_skills_for_level()` call.
- **Loadout:** absent key = all unlocked equipped (old saves unchanged until they open the new UI). Stored as plain ids, so future skill additions are safe.
- A save at cap 60 choosing a profession gets the signature + 50/60 skills at once (they've already earned the levels), and the upgraded passive applies immediately.

## 10. Phasing

| Phase | Deliverable | Code touch | Authoring |
|---|---|---|---|
| **1** | Wave 2 + skill book regroup | minimal (skill book tier labels) | 24 YAML skills + wiki |
| **2** ✅ | Capstones + **Battle Loadout** | SHIPPED 2026-10-15 — loadout filter/auto-equip + Skill Book management; panel height re-verified | 8 YAML + wiki |
| **3a** ✅ | Profession model + ceremony + passive framework | SHIPPED — merge + lockout in `get_class_skill_map`, `profession` save field, Guild ceremony (menu restructured), composite passive helper | — |
| **3b** ✅ | Profession skills + passive upgrades | SHIPPED — 48 skills (33 bespoke branches, 15 generic), 16 passives, 6 hooks (crit / elemental / start-CD / evasion / regen / low-HP) | 48 YAML + 16 passives + wiki |
| **3c** ✅ | UI polish | SHIPPED — Skill Book profession + locked-branch display, inventory line, wiki sections | wiki lockout badges |

Each phase ships standalone; playtest gates between phases.

## 11. Decisions (all locked 2026-10-15)

| # | Question | Decision |
|---|---|---|
| 1 | Respec | **Permanent** — no respec |
| 2 | Professions per class | **2** |
| 3 | Spacing | **20/26/32 · 40 · 50/60** ✓ |
| 4 | Profession passive | **Upgrade the original class passive** — 16 designs in §6.3 |
| 5 | Menu overflow | **Battle Loadout cap** (§7) instead of a submenu |
| 6 | Ceremony | **Plain Guild ceremony** |
| 7 | Capstone cooldown | **9** |
| 8 | Loadout cap | **9** — approved |
| 9 | Loadout swap location | **Anywhere out of combat** |
| 10 | Effect fidelity | **True effects over substitutes, even if costly** — all 6 passive hooks and all §6.7 ports are real implementations; substitution only if genuinely impossible |

No open items — ready for Phase 1 (§10).

## 12. Patch log

- **2026-10-15 — Phase 1 shipped (wave 2).**
  - 24 skills added to `skill_list.yaml` (9 actives per class; Lv 20/26/32), no new ids colliding with the learnable pool.
  - Engine (`combat/skills.py`): 11 new non-damage branches (War Banner, Elemental Focus, Perfect Opening, Prayer of Mending, Blessed Aegis, Camouflage, Hawk's Eye, Blessing, Blood Pact, Battle Trance, Reckless Abandon); generic single-target fallback now applies YAML statuses (`apply_slow`, `stun_chance`, `apply_weaken`, `burn/poison/bleed`, `apply_sunder`, `apply_blind`, `self_vulnerable`); AoE path gained bleed; Siphon Soul drain branch.
  - Hooks: `crit_damage` buffs in `resolve_critical_chance` (stats.py); generic `elemental_dmg` buffs in `calculate_elemental_damage` (elemental.py); `mark_damage_bonus` read by both mark sites (skills.py + player_actions.py); HUD tags for the four new buff types (combat_ui.py).
  - Barrier/regen/evasion needed **no port** — `apply_barrier`/`regen_pct`/`evasion` consumption already existed for player + allies (verified in `status_effects`/`enemy_ai`/`get_dodge_chance`).
  - UI: Skill Book regrouped into bands incl. Tier 3 (Level 20-32); action panel `MIN_ROWS` 2 → 3 (9 skills + utility = 3 rows; constant height re-verified at 15/16 buttons).
  - Docs/wiki: README skill section updated; skills wiki + web wiki regenerated (all 24 render); changelog section added under v0.1.8.1.
  - Tests: `tests/_temp_player_skill_extension_check.py` (22 checks, all pass); barracks patch check + local-import diag + action panel + HUD layout all green.
- **2026-10-15 — Phase 2 shipped (capstones + Battle Loadout).**
  - 8 capstones at Lv 40 (CD 9, `capstone: true`): Onslaught, Cataclysm, Death's Embrace, Providence, Skyfall Volley, Heaven's Sword, Dark Apotheosis, Wrath Incarnate — 7 bespoke branches (Cataclysm rides the generic AoE + burn path).
  - Battle Loadout: `MAX_SKILL_LOADOUT = 9`; `get_equipped_skill_ids` (missing key = everything equipped); combat menu + `is_skill_available` filter by loadout; auto-equip under cap; overflow queue notification; Skill Book "Manage Battle Loadout" screen; inventory ✓/– markers + counter.
  - Cooldown refund hook: `player["refund_cooldown_skill"]` consumed by `set_skill_cooldown` (Death's Embrace kill refunds its CD).
  - Bug fixes shipped alongside: support skills (heals/buffs/barriers) now earn mastery XP — `execute_skill` is a thin wrapper around `_execute_skill_core`; Frost Nova's slow was missing (`apply_slow` never set) and is restored.
  - Wiki/README/changelog updated; check test extended to **35 checks** (all pass); barracks/panel/HUD/version diags green.
- **2026-10-15 — Phase 3 shipped (professions).**
  - Model: `professions:` YAML block (8 classes × 2 branches × 3 skills + upgraded passives); `get_class_skill_map` merges the chosen branch — lockout is structural (the unchosen branch never enters the map). `get_class_capstone_id` + `can_choose_profession`; `profession` save field via `ensure_player_fields`.
  - Ceremony: Guild menu restructured to an action-key dispatch; new `_choose_profession` (branch pick → detail + explicit permanence → confirm → sets `profession`, calls `unlock_skills_for_level`).
  - Passives: `get_player_passive_effects` composite helper replaces the class passive when a profession is chosen; 6 hooks live — crit (`get_raw_critical_chance`), elemental (`calculate_elemental_damage`), evasion (`get_dodge_chance`), combat-start CD + regen (`apply_profession_battle_start`, called in both battle loops), low-HP damage (`_calc_dmg` + basic attacks).
  - Skills: 48 new (33 bespoke branches incl. party buffs, wards, cooldown unwinds, executes, novas; 15 ride the generic AoE/fallback paths — new generic keys `apply_damage_taken_up`, `self_heal_percent`, `elemental_dmg_elem`).
  - UI: Skill Book shows profession + upgraded passive + locked branch; inventory tab shows the profession line; wiki gained a full **Player Professions** section (regenerated).
  - Check test now at **46 checks** (all pass); full regression sweep green.
