# TerminalRPG — New Superboss Design Document

## Overview

This document details three new superbosses designed for the TerminalRPG milestone combat system. Each boss introduces a unique mechanical gimmick that tests different player skills: resource management, tactical target priority, and burst-timing. All stats are balanced against the existing superboss roster (Lv 20–25 range, ~30–35 total attribute mods, 400–500 HP).

---

## 1. Malphas, the Hollow Choirmaster

**Tier:** 6 (new, extends pool to `[0…6]`)
**Level:** 22
**Race:** Undead / Fey
**Theme:** Sound, resonance, and crescendo mechanics. The battlefield is a concert hall where every action feeds an invisible choir.

### Stat Block (YAML)

```yaml
malphas_hollow_choirmaster:
  name: Malphas, the Hollow Choirmaster
  race: Undead
  level: 22
  base_hp: 420
  mods:
    Strength: 5
    Constitution: 6
    Dexterity: 7
    Wisdom: 8
    Learning: 4
    Charisma: 6
  boss: true
  super_boss: true

hollow_echo:
  name: Hollow Echo
  race: Fey
  level: 18
  base_hp: 80
  mods:
    Strength: 4
    Constitution: 3
    Dexterity: 8
    Wisdom: 4
    Learning: 3
    Charisma: 2
  boss: false
  super_boss: false
  minion_only: true
```

### Gimmick: Resonance & Crescendo

| Mechanic | Description |
|----------|-------------|
| **Resonance** | Every action taken by **any** combatant (player attack, ally skill, enemy attack, Malphas action) adds **+1 Resonance** to a shared counter. |
| **Dampen** | When the player chooses **Defend** (`D`), they "Dampen" the field: **-2 Resonance** (minimum 0) and no Resonance is gained on that turn. |
| **Crescendo** (at 10 Resonance) | Malphas unleashes a sonic blast. **All** party members (player + allies) take `Resonance × 2 + 10` unblockable damage. Counter resets to 0. |
| **Dissonant Scream** (at 15 Resonance) | If the player lets Resonance reach 15, they are **Silenced** for 2 turns (cannot use skills or items). Resonance still resets to 0 after Crescendo. |
| **HUD Display** | `Resonance: 7/10 ⚠` (turns red at 8+) |

### Phase 2: Grand Finale (≤ 50% HP)

- Triggered once when Malphas drops to 50% HP.
- **Echo Fracture:** Spawns **2 Hollow Echoes** immediately.
- **Accelerated Tempo:** Every action now adds **+2 Resonance** instead of +1.
- **Crescendo threshold drops to 7.**
- **Malphas gains double actions** for the remainder of the fight.
- **Hollow Echoes:** Each echo deals 50% of Malphas's calculated damage and also adds to Resonance. They are 1-hit illusions (any damage destroys them), but they respawn every 3 rounds if the player kills them.

### Player Counterplay

1. **Defend proactively** to manage the Resonance gauge.
2. **Kill Echoes** the moment they spawn — each one effectively doubles the Resonance build rate.
3. **Save big skills** for after Crescendo (when Resonance is 0) so you don't accidentally trigger it mid-combo.
4. **Burst Malphas** once he hits Phase 2; the longer the fight lasts, the faster the gauge fills.

### Implementation Notes

- **`pre_player_hook`**: Increment Resonance by 1 (or 2 in Phase 2). Check if Resonance ≥ 10 → trigger Crescendo damage, reset. Check if ≥ 15 → apply Silence. Check HP threshold for Phase 2 trigger (spawn echoes, set flag).
- **`enemy_turn_hook`**: Each Malphas attack also adds +1 Resonance (handled in pre_player, but echo attacks need to add too). Echoes get `actions=1` with low damage and die in 1 hit (can use a custom `IllusionDict` subclass like Sylvana's mirrors, or just set their HP to 1 and make them fragile).
- **`post_round_hook`**: Respawn echoes if Phase 2 and it's been 3 rounds since last spawn. Echo respawn turn counter.
- **`custom_hud_hook`**: Display Resonance gauge and Phase 2 warning.
- **`player_action_override`**: If action is `d`, decrement Resonance by 2 and skip the auto-increment for that turn.

---

## 2. Vorath, the Bone Gardener

**Tier:** 7 (new, extends pool to `[0…7]`)
**Level:** 23
**Race:** Undead
**Theme:** Necromancy and battlefield resource management. The arena is a garden of bones that grow stronger with every drop of blood spilled.

### Stat Block (YAML)

```yaml
vorath_bone_gardener:
  name: Vorath, the Bone Gardener
  race: Undead
  level: 23
  base_hp: 480
  mods:
    Strength: 7
    Constitution: 8
    Dexterity: 5
    Wisdom: 6
    Learning: 4
    Charisma: 5
  boss: true
  super_boss: true

skeletal_hound:
  name: Skeletal Hound
  race: Undead
  level: 18
  base_hp: 100
  mods:
    Strength: 6
    Constitution: 3
    Dexterity: 9
    Wisdom: 2
    Learning: 2
    Charisma: 1
  boss: false
  super_boss: false
  minion_only: true
```

### Gimmick: The Bone Garden

Vorath begins the fight with **3 Bone Seeds** on the field. Seeds are not enemies; they are environmental objects tracked in `ctx`.

| Mechanic | Description |
|----------|-------------|
| **Fertilize** | At the **start of each round**, every living seed gains **+1 Fertilizer stack**. |
| **Consume** | On Vorath's turn, if a seed has ≥ 3 stacks, he may **consume** one seed (random priority) to: <br>• **Heal** 15% max HP per stack. <br>• **Summon** a Skeletal Hound (costs 2 stacks; consumes the seed). <br>• **Buff** +3 STR for 2 turns per stack (if no seed has ≥ 3, he attacks normally). |
| **First Harvest** (≤ 60% HP) | Triggered once. Vorath **instantly consumes all remaining seeds**, healing for **10% max HP × total stacks** and gaining **+5 STR for 3 turns**. All seeds are destroyed. |
| **Grave Bloom** (≤ 40% HP) | Triggered once. Vorath enters his final form: <br>• A new seed respawns every **2 rounds** (max 3). <br>• Seeds generate **double stacks** (+2 per round). <br>• Vorath gains **30% lifesteal** (heals 30% of damage dealt). <br>• Existing Skeletal Hounds gain **+2 STR**. <br>• If fewer than 2 hounds are alive, a seed auto-consumes at the start of the round to summon one. |

### Player Counterplay

1. **Kill Skeletal Hounds immediately** — they are fast (DEX 9) and hurt, and they prevent Vorath from needing to consume seeds to summon them.
2. **Burst Vorath** before he hits 40% HP. Grave Bloom turns a manageable fight into a war of attrition.
3. **Track the seed stacks** in the HUD. If a seed is at 3 stacks, expect a summon or a big heal next turn.
4. **Defend when a seed is at 4+ stacks** — Vorath's heal or buff will likely come this turn, so mitigating his normal attack is secondary to surviving the spike.

### Implementation Notes

- **`context` seeds**: `seeds = [{"stacks": 0}, {"stacks": 0}, {"stacks": 0}]` with `first_harvest_triggered`, `grave_bloom_triggered`, `hounds_alive`.
- **`pre_player_hook`**: 
  - Fertilize all seeds (+1, or +2 in Grave Bloom).
  - Auto-summon hound if Grave Bloom and < 2 hounds alive.
  - Check HP thresholds for phase transitions.
- **`enemy_turn_hook`**: 
  - If a seed has ≥ 3 stacks and no hound needs summoning, Vorath consumes the highest-stack seed: heal, buff, or summon (priority: summon if < 2 hounds, else heal if < 50% HP, else buff).
  - If a seed was consumed, it is removed from `ctx["seeds"]`.
  - Normal attack if no seed qualifies.
- **`custom_hud_hook`**: Display seed stacks as `Seed 1 [3] | Seed 2 [1] | Seed 3 [0]`. Highlight seeds at 3+ in red.
- **`on_kill_hook`**: If a Skeletal Hound dies, decrement `hounds_alive`.

---

## 3. Astron, the Forgotten Warden

**Tier:** 8 (new, extends pool to `[0…8]`)
**Level:** 24
**Race:** Construct
**Theme:** Time manipulation, stasis, and temporal rewind. A guardian left alone so long that time itself has become its weapon.

### Stat Block (YAML)

```yaml
astron_forgotten_warden:
  name: Astron, the Forgotten Warden
  race: Construct
  level: 24
  base_hp: 450
  mods:
    Strength: 8
    Constitution: 7
    Dexterity: 6
    Wisdom: 9
    Learning: 5
    Charisma: 3
  boss: true
  super_boss: true
  elemental_dmg:
    light: 1.3
  elemental_res:
    light: 0.6
    dark: 1.2

stasis_orb:
  name: Stasis Orb
  race: Construct
  level: 20
  base_hp: 1      # 1-hit destruction, like Sylvana Mirror / Yinglong Wedge
  mods:
    Strength: 0
    Constitution: 0
    Dexterity: -20
    Wisdom: 0
    Learning: 0
    Charisma: 0
  boss: false
  super_boss: false
  minion_only: true
```

### Gimmick: Timeline Anchor & Stasis Orbs

| Mechanic | Description |
|----------|-------------|
| **Timeline Anchor** | Every **3 rounds**, Astron records a snapshot of **his own HP**. The snapshot is stored in `ctx["anchor_hp"]` and the round counter resets. |
| **Rewind** | At the **start of the next Anchor cycle** (round 4, or round 3 in Phase 2), if Astron's current HP is **lower** than the snapshot, he **Rewinds**: restores HP to the snapshot value and deals **unblockable Temporal Damage** to the player equal to `(snapshot_hp - current_hp) ÷ 3`. |
| **Anchor Fracture** | If the player deals **≥ 60 damage in a single turn** (across all actions including Abyss Tempo extras), the Timeline Anchor **fractures**. The Rewind is delayed by 1 round. This can be done once per cycle. |
| **Stasis Orbs** | Astron begins with **2 Stasis Orbs** on the field. Each orb **absorbs the next instance of damage** directed at Astron (the orb is destroyed, Astron takes 0). Orbs are 1-hit objects (use `OneHitWedgeDict` / `IllusionDict` pattern). |
| **Orb Respawn** | If both orbs are destroyed, they respawn at the **start of round 3** (or round 2 in Phase 2). |

### Phase 2: Temporal Collapse (≤ 50% HP)

- Triggered once when Astron drops to 50% HP.
- **Anchor cycle shortens** from 3 rounds → **2 rounds**.
- **Rewind becomes unavoidable** (Anchor Fracture no longer works).
- **Astron gains +1 action per turn** (double actions).
- **Stasis Orbs respawn every round** if both are destroyed, instead of every 3 rounds.
- **Temporal Damage multiplier increases**: Rewind now deals `(snapshot_hp - current_hp) ÷ 2` instead of ÷ 3.

### Player Counterplay

1. **Destroy both Stasis Orbs immediately** at the start of each cycle. Orbs must die before you can pressure Astron's HP.
2. **Time your burst.** Deal as much damage as possible in the first 2 rounds of a cycle, then **fracture the anchor** with a big 60+ damage turn to buy a round.
3. **Don't over-invest in the 3rd round.** The rewind will undo damage done in round 3 anyway. Use round 3 to heal, buff, or defend.
4. **Push hard before 50% HP.** Phase 2 removes your ability to delay Rewind and makes orb management exhausting.

### Implementation Notes

- **`context`**: `{"anchor_hp": None, "anchor_round": 0, "cycle_length": 3, "fractured": False, "phase_2": False, "orbs": [orb1, orb2], ...}`
- **`pre_player_hook`**: 
  - Check if it's the recording round (`anchor_round == 1`). Record `anchor_hp`.
  - Check if it's the rewind round (`anchor_round > cycle_length`). If `current_hp < anchor_hp`, heal to `anchor_hp`, deal temporal damage to player. Reset `anchor_round = 1` and record new `anchor_hp`.
  - Check Anchor Fracture condition: if player dealt ≥ 60 damage last turn, set `fractured = True`, delay rewind by 1 round.
  - Respawn orbs if needed (check round count since last orb death).
  - Check HP threshold for Phase 2.
- **`on_player_hit_hook`**: 
  - Accumulate damage dealt this turn into `ctx["damage_this_turn"]`.
  - If target is an orb, check if it should shatter (any damage → 0 HP).
  - If target is Astron and orbs are alive, redirect the hit to an orb (or absorb it). The simplest way: when orbs exist, modify Astron's `con_mod` to 9999 (like Yinglong's immortality) but only for the player hit hook. Actually, better: on_player_hit_hook intercepts hits on Astron while orbs exist, negates damage, and destroys one orb.
- **`enemy_turn_hook`**: 
  - Normal attacks in Phase 1. 
  - Double actions in Phase 2 (`actions = 2`).
  - Temporal Damage bonus: if Rewind happened this round, add a temporary damage bonus to Astron's next attack based on the HP gap healed.
- **`custom_hud_hook`**: 
  - Display: `Timeline Anchor: Recording...` / `Rewind in 2 rounds` / `⚠ REWIND IMMINENT`.
  - Display orbs: `Stasis Orbs: [●] [○]` (filled = alive, empty = destroyed).
  - Display Phase 2 warning if active.

---

## Balancing Comparison Table

| Boss | Level | HP | Total Mods | Defensive Quirk | Offensive Quirk | Player Skill Tested |
|------|-------|-----|------------|-------------------|-------------------|---------------------|
| Broodmother Vileheart | 20 | 350 | 28 | Minion phase retreat | Enraged double actions | Minion clear speed |
| Dream-Devouring Slitcurrent | 21 | 420 | 29 | Floatsam spawn | Devour empowerment | Focus-fire management |
| Ignis | 21 | 400 | 30 | Heat = defense drop | Slag purge, self-bleed | Heat gauge control |
| Sylvana | 21 | 380 | 29 | Mirror copies (1-hit), veil defense | Null buffs, silence | Pattern recognition |
| Yinglong | 25 | 400 | 40 | Divine scales (-60%), immortal | Inner dragon, wedge | Multi-phase endurance |
| Rientrante | 25 | 420 | 33 | Frost resist | Frost shards, frozen arms | Positioning / RNG |
| **Malphas** | **22** | **420** | **30** | Echoes (1-hit), dampen | Crescendo AoE, silence | **Resource pacing / gauge** |
| **Vorath** | **23** | **480** | **34** | Seed consumption heal | Grave Bloom lifesteal | **Target priority / burst** |
| **Astron** | **24** | **450** | **38** | Stasis Orbs, rewind | Temporal damage | **Damage windows / timing** |

---

## Wiring Checklist (if implementing)

To add these bosses to the live game, the following changes are required:

1. **YAML Data**: Append entries to `resources/enemies/enemies_data/superbosses.yaml` (including `minion_only: true` for Hollow Echo, Skeletal Hound, and Stasis Orb).
2. **Python Modules**: Create `combat/malphas.py`, `combat/vorath.py`, `combat/astron.py` with `combat_malphas()`, `combat_vorath()`, `combat_astron()` entry points.
3. **Dungeon Integration**: 
   - Import the new functions in `dungeon.py`.
   - Extend `player["superboss_pool"]` initialization from `[0…5]` to `[0…8]`.
   - Add `elif tier == 6/7/8` branches in the milestone combat loop.
4. **Save Compatibility**: No new player fields are needed (all state is local to `context`), so `ensure_player_fields()` does not require updates.
5. **Hook Signature Compliance**: All `enemy_turn_hook` implementations must return exactly `(actions, skip_atk, extra_logic, armor_mult, temp_str)`. No extra kwargs.
6. **Minion Safety**: All minion entities (`hollow_echo`, `skeletal_hound`, `stasis_orb`) must have `minion_only: true` to prevent random spawns in normal rooms.

---

*Document generated for TerminalRPG superboss expansion. Stats and gimmicks are designed to fit the existing `superboss_combat_loop` hook architecture without requiring engine refactors.*
