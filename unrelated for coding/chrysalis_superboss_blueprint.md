# Chrysalis, the Entangled One — Superboss Blueprint

> *"I have lived this moment before. And this one. And this one.*
> *You are already caught in the weave."*
>
> — Chrysalis, the Entangled One (adapted from Butterfly of Entangled Lives, *Limbus Company*)

---

## Table of Contents

1. [Overview](#overview)
2. [Lore & Encounter](#lore--encounter)
3. [Enemy Definitions](#enemy-definitions)
4. [Core Mechanic: Temporal Aspects](#core-mechanic-temporal-aspects)
5. [The Momentum Buff](#the-momentum-buff)
6. [Temporal Shards — Minion Counter-Play](#temporal-shards--minion-counter-play)
7. [Paradox Fracture — The Risk/Reward Cycle](#paradox-fracture--the-riskreward-cycle)
8. [Phase Breakdown](#phase-breakdown)
9. [Skill Reference](#skill-reference)
10. [Combat Flow Diagram](#combat-flow-diagram)
11. [Hooks Implementation](#hooks-implementation)
12. [Context State Keys](#context-state-keys)
13. [Dialogue & Narration](#dialogue--narration)
14. [Loot & Post-Combat](#loot--post-combat)
15. [Edge Cases](#edge-cases)
16. [Engine Additions Required](#engine-additions-required)
17. [Tuning Levers](#tuning-levers)
18. [Implementation Checklist](#implementation-checklist)

---

## Overview

| Property | Value |
|---|---|
| **Name** | Chrysalis, the Entangled One |
| **Module** | `combat/entangled_chrysalis.py` |
| **Function** | `combat_entangled_chrysalis(player, floor=None, enemies=None)` |
| **Enemy Key** | `entangled_chrysalis` |
| **Rarity** | Pandemonium-exclusive (floor 20) |
| **Level** | 30 |
| **Location** | Pandemonium floor 20 milestone (replaces normal superboss spawn) |
| **Phases** | 3 (100%→67% / 66%→34% / 33%→0%) with HP gates to prevent one-shotting |
| **Core Gimmick** | Cycles between three Temporal Aspects (Past/Present/Future). Three immortal linked minions provide counter-play. Stance-switching builds a vulnerability meter (Paradox Fracture) that the player exploits for burst windows. |
| **Drop** | `chronoweave_mantle` (Legendary armor, 100%), + `fractured_hourglass` (consumable, resets 1 skill cooldown per floor) |
| **Source** | Inspired by Butterfly of Entangled Lives (Limbus Company), fully adapted to TerminalRPG mechanics |

---

## Lore & Encounter

### Setting

Pandemonium's crystalline halls are already a place where reality frays. On the 20th floor — the apex of Tier 2 corruption — time itself begins to unravel. The party stumbles into a vast chamber where three colossal hourglasses float in a triangle — one glowing amber (Past), one pulsing silver (Present), one bleeding violet (Future).

At the center, suspended in crystalline threads, hangs a cocoon. It beats like a heart.

**Spawn rule:** Chrysalis replaces the normal superboss spawn on Pandemonium floor 20. This is the ONLY place Chrysalis can be encountered. It is not part of the general superboss pool (tiers 0–7).

**Why floor 20?** Pandemonium Tier 2 (floors 11–20, 1.5× curse effects) culminates here. At this point the player has survived 20 floors of escalating curses and is ready for the game's most mechanically complex boss. Floor 20 is also a natural milestone — the last floor before Tier 3's 2.0× curses begin.

### Encounter Text

```
The chamber stretches beyond what geometry should allow. Three hourglasses
hover at its vertices — one dripping amber sand upward, one pulsing with 
silver light, one bleeding violet grains into an infinite abyss.

At the center, suspended by threads of crystallized time, a cocoon pulses.
It thrums with three heartbeats, each at a different tempo.

The threads snap.

What emerges is not a creature. It is a moment — stretched across
past, present, and future simultaneously. Wings of fractured glass.
Eyes that have seen every version of this fight. Every outcome.

It doesn't speak. It simply acknowledges that you are here.
It has always known you are here. It knows you will always be here. 
```

### Phase 2 Transition (66% HP)

```
The hourglasses shudder. Sand flows faster — upward, outward, inward.
The threads of time draw tighter around Chrysalis.

'You feel the weave tighten.'

The cocoon shards orbiting Chrysalis sharpen into blades. It moves faster now.
Two heartbeats at once.
```

### Phase 3 Transition (33% HP)

```
The chamber convulses. Cracks spider across the walls — not through stone,
but through the fabric of moments themselves. You glimpse alternate versions
of this fight: versions where you fell. Versions where you never arrived.

Chrysalis's form unravels and reforms in a single breath. The wings are 
no longer glass — they are the absence of glass.

'The cocoon breaks.'

The eyes see all of you at once. Every action you will take. Every defense you will try.

Nothing can be guarded against what has already happened.
```

### Victory Text

```
The three hourglasses crack simultaneously. Sand — amber, silver, violet —
spills across the chamber floor and evaporates into mist.

Chrysalis lowers its head. The wings fold. For a single, perfect moment,
all three heartbeats align.

'It has always known you would defeat it.'

The creature dissolves into threads of light. They weave themselves into
a mantle that settles gently across your shoulders. It is warm. It is 
heavy with all the moments that brought you here.

You feel, for just an instant, every version of yourself that made it
this far — and you understand that all of them fought for this.
```

### Defeat Text (Player Dies)

```
The hourglasses freeze. Not shatter — freeze. The chamber holds its breath.

Chrysalis watches you fall. There is no triumph in its gaze, only weariness.

'It has always known it would defeat you.'

The cocoon reforms around you. When you wake, you are at the dungeon entrance,
with no memory of how you arrived — only the certainty that this has happened 
before, and will happen again.
```

---

## Enemy Definitions

### Chrysalis, the Entangled One

```yaml
# resources/enemies/enemies_data/superbosses.yaml

entangled_chrysalis:
  name: Chrysalis, the Entangled One
  race: Abomination
  level: 40
  base_hp: 900
  mods:
    Strength: 5
    Constitution: 6
    Dexterity: 9
    Wisdom: 7
    Learning: 8
    Charisma: 5
  boss: true
  super_boss: true
  elemental_dmg:
    fire: 1.3
    dark: 1.3
    physical: 1.2        # for Momentum/Present physical attacks
  elemental_res:
    fire: 0.8
    dark: 0.8
    light: 1.2         # only weakness — light disrupts temporal coherence
    physical: 0.9
```

**Notes:**
- `base_hp: 900`, level 40 — a capstone Tier 2 Pandemonium boss. The player should be level 22–28 with solid gear.
- Chrysalis takes amplified light damage — tying into the game's existing holy/blessing items.
- The mixed resistances (0.8 fire/dark) counteract the burn/bleed focus.
- Pandemonium curses apply normally. `boss: true` and `super_boss: true` flags ensure curse-immunity logic for bosses is respected.

### Temporal Shards (Minions)

```yaml
temporal_shard_pyre:
  name: Temporal Shard: Pyre
  race: Elemental
  level: 25
  base_hp: 80
  mods:
    Strength: 3
    Constitution: 4
    Dexterity: 5
    Wisdom: 3
    Learning: 3
    Charisma: 2
  boss: false
  super_boss: false
  minion_only: true
  elemental_res:
    fire: 0.5           # strong fire resist (it IS fire)
    water: 1.3          # water weakness

temporal_shard_pulse:
  name: Temporal Shard: Pulse
  race: Construct
  level: 25
  base_hp: 80
  mods:
    Strength: 4
    Constitution: 5
    Dexterity: 4
    Wisdom: 3
    Learning: 3
    Charisma: 2
  boss: false
  super_boss: false
  minion_only: true
  elemental_res:
    physical: 0.7
    thunder: 1.3        # thunder weakness

temporal_shard_ruin:
  name: Temporal Shard: Ruin
  race: Shadow
  level: 25
  base_hp: 80
  mods:
    Strength: 3
    Constitution: 4
    Dexterity: 4
    Wisdom: 3
    Learning: 3
    Charisma: 3
  boss: false
  super_boss: false
  minion_only: true
  elemental_res:
    dark: 0.5            # strong dark resist
    light: 1.3           # light weakness
```

**Shard shared properties:**
- Speed fixed to 1 (always acts last in initiative)
- HP cannot drop below 1 (immortal — see [Edge Cases](#edge-cases))
- Do not attack — they exist purely as counter-play targets
- 50% of damage dealt to a shard is redirected to Chrysalis as true (unblockable) damage
- Display the current stack count of their linked Aspect in their name line

---

## Core Mechanic: Temporal Aspects

Chrysalis has **three stacking counters**, each capped at 30:

| Counter | Aspect | Element | DoT Specialty | Passive Theme |
|---|---|---|---|---|
| `past_stacks` | **Past** 🔥 | Fire | Burn | Retributive burn on being hit, healing reduction |
| `present_stacks` | **Present** ⚔️ | Physical | — (Momentum) | Self-buffing, ramping damage, armor penetration |
| `future_stacks` | **Future** 🩸 | Dark | Bleed | Lifesteal from bleed ticks, party-wide bleed acceleration |

### Determining the Active Aspect

At the start of each round (`pre_player_hook`):
1. Compare `past_stacks`, `present_stacks`, `future_stacks`
2. The **highest** becomes the active Aspect
3. If tied, the **currently active Aspect stays active** (no switch)
4. If the active Aspect changes → +1 Paradox Fracture (see [§7](#paradox-fracture--the-riskreward-cycle))

### Stack Scaling

Stacks affect Chrysalis's combat power at three thresholds:

| Stack Range | Effect |
|---|---|
| **0–10** | Base: skills apply 1 stack of DoT / gain 2 Momentum. No damage bonus. |
| **11–20** | Empowered: skills apply 2 stacks of DoT / gain 3 Momentum. +1 damage per hit. |
| **21–30** | Transcendent: skills apply 3 stacks of DoT / gain 4 Momentum. +2 damage per hit. Signature skills gain bonus effects. |

### Aspect Passives (always active when that Aspect is active)

#### Past 🔥 — "The Flame That Was"
```
When Chrysalis is hit by a party member (via on_player_hit_hook):
  → Inflict 1 burn (2 damage, 3 turns) on the attacker

Turn Start (pre_player_hook):
  → All party members with 10+ total (burn potency + burn remaining turns):
    Gain "HP Healing -50%" for 1 turn
    Gain "Wrath Fragility" — take +30% fire damage for 1 turn

When Chrysalis DETONATES burn (via skills):
  → Deals 3× the burn's damage value instantly
  → Removes the burn debuff from the target
  → Applies 1 burn to all OTHER party members (flames spread)

FALLBACK: If target has no burn to detonate, deal flat fire damage = (past_stacks × 2) instead.

Kalpāgni (signature skill) gains:
  → +2 flat damage on all hits
  → Final hit inflicts (past_stacks / 2) bonus damage as Curse (rounded down)
```

#### Present ⚔️ — "The Edge That Is"
```
Momentum persists (is never cleared) while Present is active.
Turn Start: gain (2 + number of living party members) Momentum stacks.

Momentum caps at 20 stacks in Phase 1–2, 30 stacks in Phase 3.

Bonus damage from Momentum is calculated per-skill in Chrysalis's
enemy_turn_hook (no engine changes needed).

When the player DEFENDS against a Present-aspect attack:
  → Only ⅓ of Momentum's bonus damage applies (the rest is absorbed by the guard).

When switching AWAY from Present: ALL Momentum stacks are cleared to 0.

Smite the Wicked (signature skill) gains:
  → +2 flat damage
  → Target takes +25% damage next turn (Stagger effect — applied as vulnerable debuff)
```

#### Future 🩸 — "The Wound That Will Be"
```
Turn Start (pre_player_hook):
  → All party members with an existing bleed debuff take 1 immediate bleed tick.
    Chrysalis heals for the total damage dealt this way.
    (If no party member is bleeding, nothing happens.)

Whenever Bleed naturally TICKS on ANY entity (handled by tick_player_debuffs
and tick_enemy_debuffs in the engine's post-round pipeline):
  → Chrysalis heals HP equal to the bleed damage dealt

When Chrysalis DETONATES bleed (via skills):
  → Deals 3× the bleed's damage value instantly
  → Removes the bleed debuff from the target
  → Chrysalis heals for 100% of the detonation damage

FALLBACK: If target has no bleed to detonate, deal flat dark damage = (future_stacks × 2) instead.
          Chrysalis still heals for this fallback damage.

Bloodflower (signature skill) gains:
  → +2 flat damage on all hits
  → Final hit heals Chrysalis for (future_stacks × 3) HP
```

---

## The Momentum Buff

TerminalRPG has no critical-hit (Poise) system, so we introduce **Momentum** as a simple stacking self-buff that grants +3% damage per stack. It is primarily used by Chrysalis (Present Aspect) but can also be granted to the player via loot.

### Definition

```python
# In combat/status_effects.py

def apply_momentum(target, stacks=1):
    """Grant Momentum stacks to target (player or enemy).
    
    Each stack gives +3% damage dealt. Simple, one-axis scaling.
    Primarily used by Chrysalis (Present Aspect).
    
    Returns 'applied' or 'reinforced'.
    """
    existing = next(
        (b for b in target.get("active_buffs", []) if b.get("type") == "momentum"),
        None
    )
    if existing:
        existing["value"] += stacks
        return "reinforced"
    target.setdefault("active_buffs", []).append({
        "type": "momentum",
        "value": stacks,       # damage bonus: +3% per stack
        "remaining": -1,       # permanent (does not tick down)
    })
    return "applied"
```

### Momentum Effects

| Stacks | Effect |
|---|---|
| **1+** | +3% damage per stack (applied per-skill in enemy_turn_hook). No engine-wide changes needed. |

Momentum caps at **20 stacks** (+60%) in Phases 1–2, and **30 stacks** (+90%) in Phase 3. This prevents Present from scaling out of control in early phases while still making Phase 3 threatening.

### Momentum Decay

Momentum is **permanent** (`remaining: -1`) and does not tick down naturally. However:

- **While Present Aspect is active:** Momentum persists and is never cleared.
- **When Chrysalis switches away from Present:** All Momentum stacks are **immediately cleared to 0**. This gives the boss a fresh start when returning to Present stance later.

This means Chrysalis must build Momentum from scratch each time it enters Present — rewarding the player for forcing Aspect switches before Momentum ramps too high.

### Momentum in Damage Formula

Momentum multiplier is applied inside each Chrysalis skill function via `_get_momentum_multiplier()`. For the player's Chronoweave Mantle, Momentum is read by the existing damage calculation path when checking `active_buffs`. See [Engine Additions §3](#3-damage-resolution--ignores-defend-dr) for the multiplier function.

---

## Temporal Shards — Minion Counter-Play

Three shard minions orbit Chrysalis. They are the **primary strategic lever** for the player.

### Shard Properties

| Property | Pyre (Past) | Pulse (Present) | Ruin (Future) |
|---|---|---|---|
| **Element** | Fire | Physical | Dark |
| **Attack?** | No | No | No |
| **Speed** | Fixed 1 | Fixed 1 | Fixed 1 |
| **Can die?** | No (HP floor = 1) | No (HP floor = 1) | No (HP floor = 1) |

### Shard Mechanics

#### 1. Damage Redirection (batched per-round)
At the start of each round, snapshot each shard's HP. At round end (in `pre_player_hook` for the next round), calculate how much HP each shard lost. Apply 50% of lost HP as true (unblockable) damage to Chrysalis.

```python
# In pre_player_hook, before shard regen:
for aspect, shard_key in SHARD_MAP.items():
    shard = _get_shard(elist, shard_key)
    if shard and "_hp_snapshot" in shard:
        lost = shard["_hp_snapshot"] - shard["hp"]
        if lost > 0:
            redirect = lost // 2
            if redirect > 0:
                boss["hp"] = max(0, boss["hp"] - redirect)
                c_print(f"  🦋 {shard['name']} transfers {redirect} damage to Chrysalis through the temporal bond.")
```

#### 2. Stack Drain (on shard reaching HP ≤ 0)
When a shard is "killed" — handled in `on_kill_hook`:
- Chrysalis loses **1 stack** of the corresponding Temporal Aspect (min 0)
- The attacking entity **heals 5 HP** (player or ally)
- The shard's HP is reset to 1 (immortal — it "shatters and reforms")
- The shard is marked as "hit this round" in context

#### 3. Stack Regeneration (if NOT hit)
At round start (`pre_player_hook`), for each shard that was **not** hit last round:
- Chrysalis gains **+3 stacks** of that Aspect (max 30)
- **Exception**: if Chrysalis is Stunned, this regeneration does not occur

#### 4. Death Behavior
When a shard's HP reaches ≤ 0 (via `on_kill_hook`):
- HP is reset to 1 — the shard "shatters and reforms"
- The shard is NOT removed from the enemy list (hook prevents `prune_dead` removal)
- Stack drain and heal effects trigger
- The redirected damage (50% of damage dealt this round) is applied separately in `pre_player_hook`

### Strategic Implication

The player must choose each round:
- **Hit the shard matching the active Aspect** → drain stacks, force stance switch, build Paradox Fracture
- **Hit a different shard** → prevent stack regeneration for a future Aspect
- **Ignore shards** → focus damage on Chrysalis but let all Aspects grow stronger

---

## Paradox Fracture — The Risk/Reward Cycle

Paradox Fracture is Chrysalis's vulnerability mechanic. It rewards the player for forcing stance switches.

### How It Works

1. Each time the active Temporal Aspect **changes**, Chrysalis gains **1 Paradox Fracture** stack
2. Each stack: Chrysalis takes **+(stack × 10)% damage** from all sources
3. Max stacks: **10** (+100% damage taken)
4. At **10 stacks**: Chrysalis becomes **Weakened** (-3 STR, -3 DEX) for 1 turn, then all stacks reset to 0

### Announcements

| Stacks | Message |
|---|---|
| 1–4 | *(silent — only visible on custom HUD)* |
| 5 | *"The timelines strain against each other..."* |
| 7 | *"Chrysalis's form wavers — paradox tears at its being!"* |
| 10 | *"PARADOX FRACTURE — The timelines collapse! Chrysalis is EXPOSED!"* |

### Damage Formula Integration

Paradox Fracture is applied **inside Chrysalis's skill functions** (since Chrysalis handles all its own damage via `enemy_turn_hook` with `skip_atk=True`, same as Black Silence). Before applying damage to the player, multiply by `(1.0 + paradox_fracture * 0.10)`. This means at 10 stacks, Chrysalis takes double damage from all sources — but since the boss self-inflicts damage (via shard redirect and Paradox Fracture), this is a vulnerability window the player exploits.

For player attacks against Chrysalis, Paradox Fracture is applied in the `on_player_hit_hook` or by modifying the boss's effective CON:

```python
# In on_player_hit_hook or pre-damage check:
def _get_paradox_multiplier(ctx):
    pf = ctx.get("paradox_fracture", 0)
    return 1.0 + (pf * 0.10)  # 1.0 → 2.0 at max stacks
```

The boss's actual HP dict is NOT subclassed. The multiplier is applied in the damage calculation path, not via dict interception.

---

## Phase Breakdown

### Phase 1: "The Weave Awakens" (100% – 67% HP)

| Property | Value |
|---|---|
| **Actions per turn** | 1 |
| **Skill cycle** | Standard 3-turn (see [§9](#skill-reference)) |
| **Shards** | All 3 present |
| **Ignores Defend?** | Only turn-3 signature skills ignore Defend DR |
| **Tone** | Introductory — learn the shard mechanic and Aspect cycling |

**Player goal in Phase 1:** Understand that hitting shards drains stacks and forces switches. Learn to recognize which Aspect is active by the HUD and attack patterns.

### Phase 2: "Threads Tighten" (66% – 34% HP)

Triggered when Chrysalis drops to or below 66% HP for the first time.

| Property | Value |
|---|---|
| **Actions per turn** | 2 |
| **Skill cycle** | Expanded — interleaves Aspect-specific mid-tier skills between shared skills |
| **Shards** | All 3 present |
| **Transition gift** | +15 to CURRENT active Aspect, +5 to the other two at start of next turn |
| **Ignores Defend?** | Turn-3 and mid-tier skills now have final hits that ignore Defend DR |

**Phase 2 cycle pattern (per Aspect, 3 turns):**

```
Past:    Temper and Cast → Fluttering Havoc → Immolation → Pulverization → Kalpāgni
Present: Anitya → Fluttering Havoc → Skypiercer → Pulverization → Smite the Wicked
Future:  Corrosive Disintegration → Fluttering Havoc → Rotting Annihilation → Pulverization → Bloodflower
```

### Phase 3: "The Cocoon Breaks" (33% – 0% HP)

Triggered when Chrysalis drops to or below 33% HP for the first time.

| Property | Value |
|---|---|
| **Actions per turn** | 2 (empowered — skills are upgraded, not more actions) |
| **Skill cycle** | Signature-heavy — double-detonations, bonus curse/bleed procs |
| **Shards** | All 3 present |
| **Transition gift** | +15 to CURRENT active Aspect, +5 to the other two at start of next turn |
| **Ignores Defend?** | **ALL attacks ignore Defend DR** |
| **Momentum cap** | Raised to 30 stacks |

**Phase 3 cycle pattern (per Aspect, 2-turn shortened cycle):**

```
Past:    Temper and Cast → Immolation (empowered: double-detonate) → Kalpāgni (empowered)
Present: Anitya → Skypiercer (empowered: all hits ignore Defend) → Smite the Wicked (empowered)
Future:  Corrosive Disint. → Rotting Annih. (empowered: double-detonate) → Bloodflower (empowered)
```

Phase 3 empowerment effects are described in each skill's entry below under "Phase 3."

---

## Skill Reference

> **How damage works:** Chrysalis handles all its own damage via `enemy_turn_hook` returning `skip_atk=True` (same pattern as Black Silence). Each skill function computes damage manually against the target's CON, the player's `defending` flag (+5 DR, 50% multiplier), and Momentum multiplier. Skills marked "ignores Defend DR" simply omit the +5 and 50% reduction.

### Shared Skills (used in all Aspects)

#### Fluttering Havoc
```
Type: Physical (2-hit)
Damage per hit: 4-10 + DEX_mod
Scaling: +1 damage per 8 (burn + bleed) stacks on target (max +3)
         × Momentum multiplier
Gain: 2 Momentum stacks
Hit 1: Inflict 1 burn (2 dmg, 3 turns)
Hit 2: +1 burn duration, +1 bleed duration
Phase 2+: Final hit ignores Defend DR
Phase 3: All hits ignore Defend DR
```

#### Pulverization
```
Type: Physical (2-hit)
Damage per hit: 4-10 + DEX_mod
Scaling: +1 damage per 8 (burn + bleed) stacks on target (max +3)
         × Momentum multiplier
Gain: 2 Momentum stacks
Hit 1: +1 burn duration, +1 bleed duration
Hit 2: Inflict 1 burn (2 dmg, 3 turns)
Phase 2+: Final hit ignores Defend DR
Phase 3: All hits ignore Defend DR
```

#### Chaotic Turmoil
```
Type: Dark (1-hit, ignores Defend DR)
Damage: 6-14 + LER_mod
Scaling: +1 damage per 6 (burn + bleed) stacks on target (max +6)
         +1 damage per 6 Momentum stacks on self (max +3)
Special: Repeats once for every 33% missing HP (max 2 extra uses):
  Above 67% HP: 1 use only
  34%–67% HP: 2 uses (the attack repeats once)
  Below 34% HP: 3 uses (the attack repeats twice)
On Hit: Inflict 1 burn, 1 bleed, gain 1 Momentum
```

### Past-Aspect Skills 🔥

#### Temper and Cast
```
Type: Fire (2-hit)
Damage per hit: 5-10 + WIS_mod
Scaling: +1 damage per 6 burn stacks on target (max +6)
Speed: This skill always acts first in initiative order (fixed speed = 99)
Hit 1: Inflict 1 burn, +1 burn duration
Hit 2: DETONATE burn (3× damage, removes burn, spreads 1 burn to other party members)
       FALLBACK (no burn): deal (past_stacks × 2) flat fire damage
Phase 2+: Second hit ignores Defend DR
Phase 3: Both hits ignore Defend DR
```

#### Immolation
```
Type: Fire (3-hit)
Damage per hit: 5-12 + WIS_mod
Scaling: +1 damage per 6 burn stacks on target (max +6)
         +(past_stacks × 2)% bonus damage (max +60%)
Hit 1: +2 burn duration
Hit 2: Inflict 3 burn (sets up the detonation on Hit 3)
Hit 3 (ignores Defend DR): DETONATE burn (3× damage, removes burn, spreads 1 burn)
       FALLBACK (no burn): deal (past_stacks × 3) flat fire damage
If player Defended: DETONATE a second time if burn is still present.
Phase 3: All hits ignore Defend DR. DETONATE burns twice regardless.
```

#### Kalpāgni (Past Signature)
```
Type: Fire (4-hit, ALL ignore Defend DR)
Damage per hit: 6-14 + WIS_mod
Scaling: +1 FINAL damage per 6 burn stacks on target (max +6)
         +(past_stacks × 4)% bonus damage (max +120%)
Hit 1: Inflict 1 burn, +1 burn duration
Hit 2: Inflict 1 burn, +1 burn duration
Hit 3: DETONATE burn (3× damage, removes burn, spreads 1 burn)
       FALLBACK: deal (past_stacks × 3) flat fire damage
Hit 4: Since burn was already detonated: deal (past_stacks / 2) Curse damage (rounded down)
       + Re-apply 1 burn to the target (fresh wound)
       If burn somehow survived Hit 3: DETONATE it instead
After skill resolves:
  If player Defended: Halve Past stacks (rounded down).
    Chrysalis gains Weaken (-2 STR) and Slow (2 turns).
  If player did NOT Defend: Gain +5 Past stacks.
Phase 3: After the skill, DETONATE any remaining burn once more.
```

### Present-Aspect Skills ⚔️

#### Anitya
```
Type: Physical (2-hit)
Damage per hit: 4-10 + DEX_mod
Scaling: +1 damage per 6 Momentum stacks on self (max +6)
         × Momentum multiplier
Before Attack: Gain 2 Momentum
Hit 1: Gain 1 Momentum
Hit 2: Deal (Momentum_stacks / 2) bonus Physical damage
If player Defended: Momentum multiplier reduced to ⅓ effectiveness.
Phase 2+: Second hit ignores Defend DR
Phase 3: Both hits ignore Defend DR. No Momentum penalty for Defend.
```

#### Skypiercer
```
Type: Physical (4-hit)
Damage per hit: 5-12 + DEX_mod
Scaling: +1 damage per 6 Momentum stacks on self (max +6)
         × Momentum multiplier
         +(present_stacks × 2)% bonus damage (max +60%)
Before Attack: Gain 3 Momentum
Hit 1: Gain 1 Momentum
Hit 2: Gain 2 Momentum
Hit 3 (ignores Defend DR): Deal +(Momentum_stacks)% bonus damage (max +50%)
Hit 4 (ignores Defend DR): Deal +(Momentum_stacks × 2)% bonus damage (max +100%)
If player Defended: Hits 3-4 bonus halved (max +25%/+50%).
Phase 3: All hits ignore Defend DR. No penalty for Defend.
```

#### Smite the Wicked (Present Signature)
```
Type: Physical (1-hit, ignores Defend DR)
Damage: 10-20 + DEX_mod
Scaling: +1 FINAL damage per 6 Momentum stacks on self (max +6)
         × Momentum multiplier (+20% damage per 6 Momentum, max +120%)
         +(present_stacks × 4)% bonus damage (max +120%)
Before Attack: 
  - Gain 4 Momentum
  - If 20+ Momentum stacks: consume up to 20 SURPLUS stacks
    → +(consumed × 5)% bonus damage (max +100%)
    - If player Defended, this consumption does NOT trigger
Physical Penetration: Ignores 50% of target's physical resistance
  (e.g., 0.5 resist → 0.75 effective)
After skill resolves:
  If player Defended: Halve Present stacks (rounded down).
    Chrysalis gains Weaken (-2 STR) and Slow (1 turn).
  If player did NOT Defend: Gain +5 Present stacks. Target gains Vulnerable (+25% damage taken, 1 turn).
Kill chain: If target is KILLED, REUSE this skill on highest-HP remaining target (once per turn).
Phase 3: If player Defended, deal +(50% of this hit's damage) as bonus Physical damage anyway.
```

### Future-Aspect Skills 🩸

#### Corrosive Disintegration
```
Type: Dark (2-hit)
Damage per hit: 4-10 + LER_mod
Scaling: +1 damage per 6 bleed stacks on target (max +6)
Hit 1: Inflict 1 bleed, +1 bleed duration
Hit 2: DETONATE bleed (3× damage, removes bleed, Chrysalis heals for damage dealt)
       FALLBACK (no bleed): deal (future_stacks × 2) flat dark damage, heal for that amount
Phase 2+: Second hit ignores Defend DR
Phase 3: Both hits ignore Defend DR
```

#### Rotting Annihilation
```
Type: Dark (2-hit)
Damage per hit: 5-12 + LER_mod
Scaling: +1 damage per 6 bleed stacks on target (max +6)
         +(future_stacks × 2)% bonus damage (max +60%)
Hit 1: Inflict 2 bleed, +2 bleed duration
Hit 2 (ignores Defend DR): DETONATE bleed (3× damage, removes bleed, Chrysalis heals)
       FALLBACK (no bleed): deal (future_stacks × 3) flat dark damage, heal for that amount
If player Defended: DETONATE a second time if bleed is still present.
Phase 3: All hits ignore Defend DR. DETONATE bleeds twice regardless.
```

#### Bloodflower (Future Signature)
```
Type: Dark (2-hit, ALL ignore Defend DR)
Speed: This skill always acts first in initiative order (fixed speed = 99)
Damage per hit: 6-16 + LER_mod
Scaling: +1 FINAL damage per 6 bleed on target (max +6)
         +(future_stacks × 4)% bonus damage (max +120%)
Hit 1: Inflict 1 bleed, +1 bleed duration
Hit 2: DETONATE bleed (3× damage, removes bleed, Chrysalis heals)
       FALLBACK: deal (future_stacks × 3) flat dark damage, heal for that amount
       + Inflict 2 burn, +3 burn duration (cross-Aspect contamination)
       + Heal Chrysalis for (future_stacks × 3) HP (signature bonus heal)
After skill resolves:
  If player Defended: Halve Future stacks (rounded down).
    Chrysalis gains Weaken (-2 STR) and Slow (2 turns).
  If player did NOT Defend: Gain +5 Future stacks.
Phase 3: After the skill, DETONATE any remaining bleed once more.
```

---

## Combat Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    COMBAT START                                  │
│  All 3 shards spawn. past=10, present=10, future=10             │
│  Active Aspect = Present (highest starts at tie, Present wins)  │
│  Phase = 1                                                      │
└──────────────────────┬──────────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ROUND START (pre_player_hook)                 │
│  1. Check HP → maybe trigger Phase 2 or 3 transition            │
│  2. Recalc active Aspect (highest stacks wins)                  │
│  3. If Aspect CHANGED → +1 Paradox Fracture, announce           │
│  4. If Paradox Fracture = 10 → Weaken boss, reset to 0          │
│  5. Check which shards were hit last round → +3 stacks for      │
│     unhit shards (unless boss stunned)                          │
│  6. Clear shards_hit_this_round                                 │
└──────────────────────┬──────────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ASPECT-SPECIFIC ROUND START                   │
│  PAST: apply burn retaliation passive                           │
│        apply healing-down + fire-fragility if burn >= 10        │
│  PRESENT: gain (2 + party_size) Momentum (capped at 20/30)     │
│           Momentum persists (not cleared while Present)        │
│  FUTURE: bleed lifesteal calculated in post_round_hook         │
└──────────────────────┬──────────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    INITIATIVE ROLL                              │
│  Player + allies + Chrysalis + 3 shards (speed=1)               │
│  Shards always act last                                         │
└──────────────────────┬──────────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ACTION PHASE (turn loop)                      │
│  ┌──────────┐  ┌──────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │ Player   │  │ Allies   │  │ Chrysalis   │  │ Shards      │  │
│  │ chooses  │  │ use AI   │  │ uses skill  │  │ (do nothing)│  │
│  │ target   │  │ or manual│  │ from cycle  │  │             │  │
│  └──────────┘  └──────────┘  └─────────────┘  └─────────────┘  │
│                                                                  │
│  If player hits a shard:                                        │
│    → Chrysalis loses 1 stack of that Aspect                     │
│    → Player heals 5 HP                                          │
│    → Shard marked "hit"                                         │
│    → 50% damage redirected to Chrysalis                         │
│                                                                  │
│  Chrysalis actions depend on:                                   │
│    - Active Aspect → which skill set                            │
│    - turn_in_cycle (0,1,2) → which skill in set                │
│    - Phase → how many actions (1/2/3)                          │
└──────────────────────┬──────────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ROUND END (post_round_hook)                   │
│  1. Tick all buffs/debuffs (burn, bleed, Momentum, etc.)        │
│  2. Future Aspect: Chrysalis heals from all bleed ticks         │
│  3. Tick Paradox Fracture if needed                             │
│  4. Check victory (Chrysalis HP <= 0)                           │
│  5. Repeat                                                     │
└─────────────────────────────────────────────────────────────────┘
```

### Decision Points for the Player

```
Each round, player faces this decision tree:

                    ┌─────────────────────────┐
                    │ Which target to attack?  │
                    └───────────┬─────────────┘
                                │
            ┌───────────────────┼───────────────────┐
            ▼                   ▼                   ▼
    ┌───────────────┐   ┌───────────────┐   ┌───────────────┐
    │ Hit Chrysalis  │   │ Hit active    │   │ Hit inactive  │
    │ directly       │   │ Aspect shard  │   │ Aspect shard  │
    └───────┬───────┘   └───────┬───────┘   └───────┬───────┘
            ▼                   ▼                   ▼
    ┌───────────────┐   ┌───────────────┐   ┌───────────────┐
    │ Max damage    │   │ Drain stacks  │   │ Prevent +3    │
    │ but all       │   │ → force Aspect│   │ stack regen   │
    │ Aspects grow  │   │ switch →      │   │ for future    │
    │ (no drain)    │   │ Paradox Fract.│   │ rounds        │
    │               │   │ + heal 5 HP   │   │ + heal 5 HP   │
    └───────────────┘   └───────────────┘   └───────────────┘

Optimal strategy: Alternate between hitting the active shard 
(to build Paradox Fracture) and hitting Chrysalis directly 
(to exploit the Fracture vulnerability window).
```

---

## Hooks Implementation

### Hook Summary

| Hook | Purpose |
|---|---|
| `pre_player_hook` | Phase transitions, Aspect switching, Paradox Fracture, shard regen check, Aspect passives |
| `enemy_turn_hook` | Skill selection based on Aspect + cycle + phase |
| `post_round_hook` | Bleed lifesteal (Future), tick Momentum, tick Paradox Fracture |
| `on_kill_hook` | Shard death prevention, stack drain, player heal |
| `on_player_hit_hook` | Past retaliatory burn on attacker |
| `custom_hud_hook` | Display Aspects, Momentum, Paradox Fracture, shard status |

### pre_player_hook

```python
def pre_player_hook(ctx, elist):
    boss = _get_boss(elist)
    if not boss:
        return None
    
    hp_pct = boss["hp"] / max(1, boss["max_hp"])
    active = ctx["active_aspect"]
    
    # ── Phase transitions ────────────────────────────────────
    if hp_pct <= 0.33 and ctx["phase"] < 3:
        ctx["phase"] = 3
        # +15 to current active, +5 to others (reinforces current stance)
        for asp in ["past", "present", "future"]:
            bonus = 15 if asp == active else 5
            ctx[f"{asp}_stacks"] = min(30, ctx[f"{asp}_stacks"] + bonus)
        c_print("\n[PHASE 3] 'THE COCOON BREAKS.' All attacks ignore Defend DR!")
    elif hp_pct <= 0.66 and ctx["phase"] < 2:
        ctx["phase"] = 2
        for asp in ["past", "present", "future"]:
            bonus = 15 if asp == active else 5
            ctx[f"{asp}_stacks"] = min(30, ctx[f"{asp}_stacks"] + bonus)
        c_print(f"\n[PHASE 2] 'THE WEAVE TIGHTENS.' {active.title()} Aspect surges +15!")
    
    # ── Determine active Aspect ──────────────────────────────
    stacks = {
        "past": ctx["past_stacks"],
        "present": ctx["present_stacks"],
        "future": ctx["future_stacks"],
    }
    max_aspect = max(stacks, key=stacks.get)
    max_val = stacks[max_aspect]
    
    # Count how many Aspects tie for max
    tied = [a for a, v in stacks.items() if v == max_val]
    
    if len(tied) > 1 and ctx["active_aspect"] in tied:
        # Currently active is among tied — stay
        pass
    elif max_aspect != ctx["active_aspect"]:
        # Switch!
        old = ctx["active_aspect"]
        ctx["active_aspect"] = max_aspect
        ctx["paradox_fracture"] = min(10, ctx["paradox_fracture"] + 1)
        c_print(f"\n⏳ TEMPORAL SHIFT: {old.upper()} → {max_aspect.upper()}!")
        c_print(f"   Paradox Fracture: {ctx['paradox_fracture']}/10 (+{ctx['paradox_fracture']*10}% damage taken)")
        
        # ── Clear Momentum if switching away from Present ────
        if old == "present":
            clear_momentum(boss)
            c_print("   ⚔️  Momentum dissipates as the Present slips away.")
        
        if ctx["paradox_fracture"] >= 5:
            _announce_paradox(ctx["paradox_fracture"])
        
        if ctx["paradox_fracture"] >= 10:
            c_print("💥 PARADOX FRACTURE MAX! The timelines collapse — Chrysalis is EXPOSED!")
            apply_weaken(boss, duration=1)  # -3 STR, -3 DEX
            # Also mark for HUD
            boss["_paradox_exposed"] = True
    
    # ── Shard regen (unhit shards give +3 stacks) ────────────
    if not boss.get("stunned"):
        for aspect in ["past", "present", "future"]:
            if aspect not in ctx["shards_hit_this_round"]:
                key = f"{aspect}_stacks"
                old_val = ctx[key]
                ctx[key] = min(30, ctx[key] + 3)
                if ctx[key] != old_val:
                    c_print(f"  🦋 The {aspect.title()} Shard pulses — Chrysalis gains +3 {aspect.title()} stacks. ({ctx[key]}/30)")
    
    ctx["shards_hit_this_round"].clear()
    
    # ── Aspect passives ─────────────────────────────────────
    if ctx["active_aspect"] == "past":
        _apply_past_passive(ctx, elist)
    elif ctx["active_aspect"] == "present":
        _apply_present_passive(ctx, boss)
    elif ctx["active_aspect"] == "future":
        _apply_future_passive(ctx, elist)
```

### enemy_turn_hook

```python
def enemy_turn_hook(enemy, ctx, pl, p_con, defending, **kwargs):
    """Custom turn logic for Chrysalis. Returns (actions, defending, extra_fn, armor_mult, temp_str)."""
    
    if enemy.get("key") != BOSS_KEY:
        # Shards do nothing
        return 1, False, None, 1.0, 0
    
    aspect = ctx["active_aspect"]
    cycle = ctx["turn_in_cycle"]
    phase = ctx["phase"]
    
    # Advance cycle for next call
    ctx["turn_in_cycle"] = (cycle + 1) % 3
    
    # Determine which skill to use
    skill_name, skill_fn = _get_skill_for_cycle(aspect, cycle, phase)
    
    # Execute the skill
    return _execute_skill(enemy, pl, ctx, skill_name, skill_fn, defending)
```

### post_round_hook

```python
def post_round_hook(ctx, elist):
    """Called AFTER actions but BEFORE the engine ticks debuffs/buffs.
    
    Future Aspect: calculate bleed lifesteal based on what WILL tick.
    The engine ticks bleeds immediately after this hook returns.
    """
    boss = _get_boss(elist)
    if not boss:
        return None
    
    # ── Future passive: pre-calculate bleed lifesteal ──────
    if ctx["active_aspect"] == "future":
        total_bleed_heal = 0
        # player is accessible via closure (same pattern as Yinglong)
        for entity in [player] + get_alive_allies(player):
            for d in entity.get("active_debuffs", []):
                if d["type"] == "bleed" and d.get("remaining", 0) > 0:
                    total_bleed_heal += d.get("damage", 0)
        if total_bleed_heal > 0:
            heal = min(total_bleed_heal, boss["max_hp"] - boss["hp"])
            boss["hp"] += heal
            c_print(f"  🩸 Future Aspect: Chrysalis drinks deep from wounds yet to open... +{heal} HP.")
    
    # ── Clear Paradox Exposed flag ──────────────────────────
    if boss.get("_paradox_exposed"):
        boss.pop("_paradox_exposed")
        ctx["paradox_fracture"] = 0
    
    # ── Momentum is permanent; no tick needed ───────────────
    # It is manually cleared on Aspect switch away from Present.
```

### on_kill_hook

```python
def on_kill_hook(target, elist, ctx):
    """Handle shard 'death' (HP reaching ≤ 0) — prevent removal, drain stacks."""
    
    shard_map = {
        "temporal_shard_pyre": "past",
        "temporal_shard_pulse": "present",
        "temporal_shard_ruin": "future",
    }
    
    aspect = shard_map.get(target.get("key"))
    if aspect:
        # Prevent death — reset HP to 1
        target["hp"] = 1
        
        # Drain 1 stack from the linked Aspect
        key = f"{aspect}_stacks"
        old = ctx[key]
        ctx[key] = max(0, ctx[key] - 1)
        
        # Mark as hit this round
        ctx["shards_hit_this_round"].add(aspect)
        
        c_print(f"  🦋 {target['name']} shatters and reforms!")
        c_print(f"     Chrysalis loses 1 {aspect.title()} stack. ({ctx[key]}/30)")
        
        # Heal the attacker (player — accessed via closure)
        player["current_hp"] = min(player["max_hp"], player["current_hp"] + 5)
        c_print("     You recover 5 HP from the temporal resonance.")
    
    elif target.get("key") == BOSS_KEY:
        # Chrysalis itself was killed
        pass  # Let the engine handle normal death
```

### custom_hud_hook

```python
def _chrysalis_hud(ctx, enemies):
    """Custom HUD showing Temporal Aspects, Paradox Fracture, and shard status."""
    boss = _get_boss(enemies)
    if not boss:
        return
    
    c_print("\n" + "═" * 60)
    c_print(f"  🦋 Chrysalis, the Entangled One  |  HP: {boss['hp']}/{boss['max_hp']}")
    c_print("═" * 60)
    
    # Aspect display
    active = ctx["active_aspect"]
    for aspect in ["past", "present", "future"]:
        stacks = ctx[f"{aspect}_stacks"]
        bar = _make_bar(stacks, 30, 20)
        marker = " ◀ ACTIVE" if aspect == active else ""
        icons = {"past": "🔥", "present": "⚔️", "future": "🩸"}
        c_print(f"  {icons[aspect]} {aspect.title():8s} [{bar}] {stacks:2d}/30{marker}")
    
    # Paradox Fracture
    pf = ctx["paradox_fracture"]
    pf_bar = _make_bar(pf, 10, 10)
    c_print(f"  💔 Paradox Fracture [{pf_bar}] {pf}/10 (+{pf*10}% damage taken)")
    
    # Phase
    phase_labels = {1: "The Weave Awakens", 2: "Threads Tighten", 3: "The Cocoon Breaks"}
    actions_text = {1: "1 action", 2: "2 actions (empowered)", 3: "2 actions (all ignore Defend)"}
    c_print(f"  📊 Phase {ctx['phase']}: {phase_labels[ctx['phase']]} ({actions_text[ctx['phase']]})")
    
    # Momentum (Present only)
    if active == "present":
        mom = 0
        for b in boss.get("active_buffs", []):
            if b.get("type") == "momentum":
                mom = b.get("value", 0)
        cap = 30 if ctx["phase"] >= 3 else 20
        c_print(f"  ⚔️  Momentum: {mom}/{cap} (+{mom*3}% damage)")
    
    # Shards
    for e in enemies:
        if e.get("key") in SHARD_KEYS.values():
            c_print(f"  🦋 {e['name']:30s} HP: {e['hp']}/{e['max_hp']}")
    
    c_print("═" * 60)
```

---

## Context State Keys

| Key | Type | Default | Description |
|---|---|---|---|
| `past_stacks` | int | 10 | Past Aspect stacks (0–30) |
| `present_stacks` | int | 10 | Present Aspect stacks (0–30) |
| `future_stacks` | int | 10 | Future Aspect stacks (0–30) |
| `active_aspect` | str | `"present"` | Which Aspect is currently active |
| `paradox_fracture` | int | 0 | Vulnerability stacks from stance switches (0–10) |
| `phase` | int | 1 | Current phase (1, 2, or 3) |
| `turn_in_cycle` | int | 0 | Position in skill cycle (0, 1, 2) |
| `shards_hit_this_round` | set | `set()` | Which Aspect shards were "killed" this round |
| `skip_player_turn` | bool | False | Standard stun flag (phase transitions) |

**Per-shard state** (stored on shard enemy dict, not in context):
| Key | Type | Description |
|---|---|---|
| `_hp_snapshot` | int | HP at start of round (for damage redirect calculation) |

---

## Dialogue & Narration

### Aspect Switch Announcements

| Switch | Message |
|---|---|
| → Past | *"The amber sand rises. Old wounds reopen."* |
| → Present | *"The silver light pulses. This moment sharpens to a razor's edge."* |
| → Future | *"The violet grains descend. Every wound that will be is already bleeding."* |

### Shard Hit Feedback

| Event | Message |
|---|---|
| Pyre hit | *"The amber shard cracks — Chrysalis's grip on the Past weakens."* |
| Pulse hit | *"The silver shard fractures — the Present moment wavers."* |
| Ruin hit | *"The violet shard splinters — the Future grows uncertain."* |

### Shard Regen Feedback

| Event | Message |
|---|---|
| Pyre regen | *"The Pyre shard pulses — amber threads weave tighter into the Past."* |
| Pulse regen | *"The Pulse shard glows — silver light anchors the Present."* |
| Ruin regen | *"The Ruin shard bleeds — violet threads sew wounds yet to come."* |

### Critical Boss HP Announcements

| Threshold | Message |
|---|---|
| 50% HP | *"Half of the threads have snapped. The other half are still pulling."* |
| 25% HP | *"The hourglasses begin to crack. Is this the timeline where you win?"* |
| 10% HP | *"Chrysalis's wings are in tatters. Each beat of the cocoon is weaker than the last."* |

---

## Loot & Post-Combat

### Guaranteed Drop: Chronoweave Mantle

```yaml
chronoweave_mantle:
  name: Chronoweave Mantle
  type: armor
  slot: armor
  rarity: legendary
  description: >
    A mantle woven from threads of crystallized time. It is warm
    with the weight of every moment that led to this one. When you
    wear it, you feel echoes of alternate selves — all of them
    fighting alongside you.
  effects:
    - "+3 DEX, +2 WIS, +2 LER"
    - "Turn Start: if HP < 50%, gain 1 Momentum stack (max 10)"
    - "Once per floor: when you would take fatal damage, instead
       survive with 1 HP and gain +50% dodge for 1 turn.
       (Does not stack with Dryad Protector wedding accessory)"
  flavor: >
    "All your selves, across all the timelines where you fell,
    hold you up now."
```

### Guaranteed Consumable: Fractured Hourglass

```yaml
fractured_hourglass:
  name: Fractured Hourglass
  type: consumable
  rarity: legendary
  description: >
    A miniature hourglass containing sand that flows in three
    directions simultaneously. Crushing it releases temporal
    energy that refreshes your body and mind.
  effect: >
    Resets the cooldown of one skill of your choice.
    Can be used once per dungeon floor. Refreshes on floor change.
  flavor: >
    "For a moment, you are in the past — the skill was never used.
    For a moment, you are in the future — the skill is ready again."
```

---

## Edge Cases

### 1. Shard Death Prevention
- Shards must never be removed from the enemy list
- `on_kill_hook` must reset `target["hp"] = 1` to prevent `prune_dead()` from removing them
- If a shard somehow ends up with HP < 1 after the hook, clamp to 1

### 2. All Shards Hit in Same Round
- All three shards are marked in `shards_hit_this_round` = `{"past", "present", "future"}`
- No shard regen occurs → Chrysalis gets no free stacks
- This is optimal player strategy; it should feel rewarding

### 3. No Shards Hit in a Round
- All three Aspects gain +3 stacks (unless boss is stunned)
- This is punishing — boss rapidly powers up
- Players must hit at least one shard per round

### 4. Stance Switch Timing
- Aspect is only recalculated in `pre_player_hook` (round start)
- Shard hits mid-round drain stacks but don't immediately switch Aspect
- The switch happens at the start of the NEXT round
- This gives the player one round of warning before the switch

### 5. Paradox Fracture Reset
- At 10 stacks: apply Weaken to Chrysalis, announce, reset to 0
- If Paradox Fracture is somehow pushed past 10 (shouldn't happen), clamp to 10

### 6. Momentum Reset on Aspect Switch
- When Chrysalis switches AWAY from Present Aspect, ALL Momentum stacks are cleared to 0
- Handled in the Aspect switch logic in `pre_player_hook`
- Chrysalis must rebuild Momentum from scratch when returning to Present

### 7. Bleed Lifesteal During Future Aspect
- Calculated in `post_round_hook` based on current bleed states (before engine ticks)
- Heal cannot exceed Chrysalis's max HP
- If all bleeds have been cleansed or expired, no heal

### 8. Detonate Fallbacks
- If burn/bleed was cleansed before detonation hits, use flat damage fallback
- Burn fallback: `past_stacks × 2` (or `× 3` depending on skill tier)
- Bleed fallback: `future_stacks × 2` (or `× 3` depending on skill tier)
- Future's bleed fallback also heals Chrysalis

### 9. Shard Damage Redirection Timing
- HP snapshots taken at start of each round (in `pre_player_hook`)
- Redirect calculated at start of NEXT round based on HP lost
- This is "batched redirect" — slightly different from per-hit but mechanically equivalent
- Redirect is true damage (bypasses all defenses)

### 10. GUI Mode Compatibility
- Must follow the `enemies=None` pattern for GUI state sharing
- Shard HP floor logic and damage redirect handled in hooks, not dict subclasses
- Custom HUD must work both in terminal mode and GUI mode

### 11. Ally Interactions
- Allies can target shards → same stack drain + heal effects
- If an ally "kills" (triggers HP≤0 on) a shard, the ally heals 5 HP (handled in on_kill_hook via `player` closure for now; extend to allies if needed)
- Past Aspect retaliatory burn (on_player_hit_hook) applies to allies as well as the player

### 12. Pandemonium Curse Interactions
- **Silence curse:** Signature skills (Kalpāgni, Smite the Wicked, Bloodflower) cannot be silenced. Shared skills like Fluttering Havoc ARE affected by silence.
- **Stun curse:** Shard regeneration is suppressed when Chrysalis is stunned. Chrysalis's turn is skipped normally via `skip_player_turn`.
- **Damage reduction curses:** Paradox Fracture's +X% damage taken is additive with curse modifiers, not multiplicative.
- **HP-drain curses:** Do not affect shards (shards are immortal at HP=1). Affect Chrysalis normally.
- **One-shot prevention:** Phase gates (66%, 33%) prevent curse-boosted damage from skipping phases.
- **Speed curses:** Shards have fixed speed=1 and are unaffected by speed modifiers.
- Chrysalis has `boss: true` and `super_boss: true` flags for existing curse-immunity logic.

### 13. Pandemonium Floor 20 Specifics
- Chrysalis only spawns on Pandemonium floor 20 — NOT in the general superboss pool
- The player will have an active Tier 2 curse (1.5× scaling) during this fight
- If the player dies, they return to town per normal Pandemonium rules
- Floor 20 curse is rolled BEFORE the encounter
- On victory, player continues to floor 21 (Tier 3, 2.0× curses)

---

## Engine Additions Required

### 1. `apply_momentum()` — Simple Stacking Damage Buff

File: `combat/status_effects.py`

```python
def apply_momentum(target, stacks=1, cap=20):
    """Grant Momentum stacks — each stack gives +3% damage dealt.
    
    Simple, one-axis buff. Permanent (remaining=-1) until manually cleared.
    Used by Chrysalis (Present Aspect) and Chronoweave Mantle (player loot).
    
    Returns 'applied', 'reinforced', or 'capped'.
    """
    existing = next(
        (b for b in target.get("active_buffs", []) if b.get("type") == "momentum"),
        None
    )
    current = existing["value"] if existing else 0
    new_total = min(cap, current + stacks)
    if new_total == current and current >= cap:
        return "capped"
    if existing:
        existing["value"] = new_total
        return "reinforced"
    target.setdefault("active_buffs", []).append({
        "type": "momentum",
        "value": new_total,
        "remaining": -1,  # permanent
    })
    return "applied"


def clear_momentum(target):
    """Remove all Momentum stacks from target. Called on Aspect switch."""
    target["active_buffs"] = [
        b for b in target.get("active_buffs", []) if b.get("type") != "momentum"
    ]
```

**Momentum is permanent** (`remaining: -1`) and manually cleared on Aspect switch. The cap is enforced in `apply_momentum()`.

### 2. `detonate_burn()` and `detonate_bleed()` — Remove Debuff, Deal 3× Damage

File: `combat/status_effects.py`

```python
def detonate_burn(target, enemies=None):
    """Remove burn from target, deal 3× its damage instantly, spread 1 burn to others.
    
    Returns (damage_dealt, messages).
    If target has no burn, returns (0, []) — caller should use fallback.
    """
    messages = []
    for d in target.get("active_debuffs", [])[:]:
        if d["type"] == "burn":
            dmg = d["damage"] * 3
            target["hp"] = max(0, target["hp"] - dmg)
            messages.append(f"🔥 BURN DETONATION! {target.get('name', 'Target')} takes {dmg} fire damage!")
            target["active_debuffs"].remove(d)
            
            # Restore CON if burn was reducing it
            if "burn_original_con" in target:
                target["con_mod"] = target["burn_original_con"]
                del target["burn_original_con"]
            
            # Spread 1 burn to all OTHER party members
            if enemies:
                for other in enemies:
                    if other is not target and other.get("hp", 0) > 0:
                        apply_burn(other, damage=2, duration=3)
                        messages.append(f"  🔥 Flames spread! {other.get('name', '?')} is burned.")
            return dmg, messages
    return 0, messages


def detonate_bleed(target):
    """Remove bleed from target, deal 3× its damage instantly.
    
    Returns (damage_dealt, messages). Caller handles healing.
    If target has no bleed, returns (0, []) — caller should use fallback.
    """
    messages = []
    for d in target.get("active_debuffs", [])[:]:
        if d["type"] == "bleed":
            dmg = d["damage"] * 3
            target["hp"] = max(0, target["hp"] - dmg)
            messages.append(f"🩸 BLEED DETONATION! {target.get('name', 'Target')} takes {dmg} dark damage!")
            target["active_debuffs"].remove(d)
            return dmg, messages
    return 0, messages
```

**Usage pattern in Chrysalis skills:**
```python
# Inside a skill function (e.g., Temper and Cast Hit 2):
dmg, msgs = detonate_burn(target, enemies=all_party_members)
if dmg == 0:
    # Fallback — target had no burn (cleansed/expired)
    dmg = past_stacks * 2
    target["hp"] = max(0, target["hp"] - dmg)
    msgs.append(f"🔥 No burn to detonate — Chrysalis inflicts {dmg} raw fire damage instead!")
for m in msgs:
    c_print(f"  {m}")
```

**Design note:** The detonate system is cleaner than the original "activate" design because:
1. **No duration tracking** — the debuff is simply removed. No need to track how many times it's been activated.
2. **Natural flow** — skills apply burn/bleed on early hits, detonate on later hits. If the player cleanses the debuff before detonation, Chrysalis loses the burst.
3. **Burn vs Bleed asymmetry** — burn spreads to other party members (Past's retributive theme), bleed heals Chrysalis (Future's vampiric theme). This gives each Aspect a distinct tactical feel.
4. **Single detonation per skill** — since the debuff is removed, there's no "DETONATE TWICE." Skills that previously had multiple activations now use the extra hits for other effects (Curse damage on Kalpāgni Hit 4, bonus heal on Bloodflower).

### 3. Damage Resolution — "Ignores Defend DR"

**No engine flag needed.** Chrysalis handles ALL its own damage via `enemy_turn_hook` returning `skip_atk=True` (same pattern as Black Silence). Each skill function computes damage manually:

```python
# Inside each Chrysalis skill function:
def _calc_damage(base_roll, stat_mod, target_con, defending, ignore_defend=False):
    raw = base_roll + stat_mod
    block = target_con // 2
    if defending and not ignore_defend:
        block += 5  # Normal Defend bonus: +5 DR
    dmg = max(0, raw - block)
    if defending and not ignore_defend:
        dmg = int(dmg * 0.5)  # Normal Defend bonus: 50% reduction
    return dmg
```

For "always goes first" skills (Temper and Cast, Bloodflower): set `fixed_speed = 99` in the shard/enemy dict for that turn, or insert the enemy at the front of the initiative order in `enemy_turn_hook`.

For Momentum multiplier:
```python
def _get_momentum_multiplier(boss, defending=False, aspect="present"):
    """Return damage multiplier from Momentum. Reduced to ⅓ if player Defended."""
    if aspect != "present":
        return 1.0
    for b in boss.get("active_buffs", []):
        if b.get("type") == "momentum":
            base = 1.0 + (b["value"] * 0.03)
            if defending:
                # Defending reduces Momentum bonus to ⅓
                return 1.0 + (base - 1.0) / 3
            return base
    return 1.0
```

### 4. Pandemonium Floor 20 — Chrysalis Spawn Trigger

Chrysalis is NOT part of the general superboss pool (tiers 0–7). Instead, it replaces the normal superboss spawn specifically on Pandemonium floor 20.

File: `dungeon.py`, in the `explore_dungeon` function, inside the milestone floor check (`if floor % 20 == 0`). The check goes BEFORE the normal superboss pool logic:

```python
# ── Pandemonium Floor 20: Chrysalis override ──────────────────
if player.get("pandemonium_mode") and floor == 20:
    _tprint("\n" + "="*50)
    _tprint("The crystalline halls fall silent. The air grows heavy —")
    _tprint("not with menace, but with age. With the weight of moments.")
    _tprint("Three hourglasses shimmer into existence around you.")
    _tprint("A cocoon beats at the center. It has been waiting.")
    _tprint("="*50)
    _tpause("Press Enter to face the Entangled One...")
    
    while True:
        advance_time(player, 60)
        result = combat_entangled_chrysalis(player, floor)
        if result == "victory":
            # Chrysalis does NOT consume a superboss pool slot
            super_boss_exp = 800 + (floor * 60)
            super_boss_gold = 500 + (floor * 40)
            player["gold"] = player.get("gold", 0) + super_boss_gold
            _tprint(f"\n Chrysalis defeated! Bonus: +{super_boss_gold} gold, +{super_boss_exp} XP!")
            gain_exp(player, super_boss_exp)
            for ally in player.get("allies", []):
                if ally.get("current_hp", 0) > 0:
                    gain_exp_ally(ally, super_boss_exp)
            # Standard floor-clear logic (heal, save, progress)
            return True
        elif result == "fled":
            _tprint("There is no fleeing from entangled time.")
            continue
        elif result == "dead":
            return "dead"
```

And add the import at the top of `dungeon.py`:
```python
from combat.entangled_chrysalis import combat_entangled_chrysalis
```

**Key differences from normal superboss spawn:**
- Does NOT consume a slot from `player["superboss_pool"]` — it's a fixed encounter
- The normal superboss pool stays at tiers 0–7 (8 bosses, shuffled)
- Rewards: 800 base XP + 60×floor (vs normal 500 + 50×floor) to match Pandemonium scaling
- The floor 20 check for Chrysalis runs BEFORE the normal superboss pool logic — if the player is in Pandemonium mode on floor 20, they fight Chrysalis instead of drawing from the pool

---

## Tuning Levers

| Parameter | Default | Effect of Increasing |
|---|---|---|
| `base_hp: 900` | 900 | Longer fight, more phase cycles |
| Shard HP: 80 | 80 | Harder to trigger stack drain (need more damage to "kill") |
| Shard redirect: 50% of HP lost | 50% | More damage transferred to boss per shard hit |
| Stack drain per shard "kill": 1 | 1 | Slower/faster stance switching |
| Stack regen per missed shard: 3 | 3 | Boss powers up faster if you ignore shards |
| Paradox Fracture damage: +10%/stack | 10% | Bigger burst windows |
| Phase thresholds: 66%, 33% | 66/33 | Earlier/later phase escalation |
| Phase transition gift: +15 active / +5 others | 15/5 | Stronger/longer current-stance lock-in |
| Momentum: +3% damage/stack | 3% | Stronger Present Aspect scaling |
| Momentum cap (Phase 1–2 / Phase 3): 20 / 30 | 20/30 | Limits or unleashes Present's peak damage |
| Past retaliatory burn: 1 stack | 1 | Punishes multi-hit attacks more/less |
| Future detonate heal: 100% | 100% | Boss sustain from bleed detonations |
| Future bleed lifesteal: 100% | 100% | Boss sustain from natural bleed ticks |
| Burn detonate fallback: past_stacks × 2 | ×2 | Minimum damage when burn is cleansed |
| Bleed detonate fallback: future_stacks × 2 | ×2 | Minimum damage when bleed is cleansed |
| Signature skill stack gain (+5 if not Defended) | +5 | Faster Aspect ramping |
| Signature skill stack loss (halve if Defended) | 50% | Punishment for defending signature skills |
| Phase 3 actions per turn: 2 (empowered) | 2 | Controls round length vs threat density |

---

## Implementation Checklist

### Phase 0 — Engine Additions
- [ ] Add `apply_momentum()` to `combat/status_effects.py`
- [ ] Add `clear_momentum()` to `combat/status_effects.py`
- [ ] Add `detonate_burn()` to `combat/status_effects.py`
- [ ] Add `detonate_bleed()` to `combat/status_effects.py`
- [ ] Add Momentum display to `get_player_status_tags` (for HUD / Chronoweave Mantle)

### Phase 1 — Enemy Definitions
- [ ] Add `entangled_chrysalis` to `resources/enemies/enemies_data/superbosses.yaml`
- [ ] Add `temporal_shard_pyre` to `resources/enemies/enemies_data/superbosses.yaml`
- [ ] Add `temporal_shard_pulse` to `resources/enemies/enemies_data/superbosses.yaml`
- [ ] Add `temporal_shard_ruin` to `resources/enemies/enemies_data/superbosses.yaml`

### Phase 2 — Combat Module
- [ ] Create `combat/entangled_chrysalis.py`
- [ ] Implement `_get_boss()`, `_get_shard()`, `_get_momentum_multiplier()` helpers
- [ ] Implement skill execution functions (Fluttering Havoc, Pulverization, Chaotic Turmoil, etc.)
- [ ] Implement Aspect-specific skill functions (Kalpāgni, Smite the Wicked, Bloodflower, etc.)
- [ ] Implement `combat_entangled_chrysalis()` main function
- [ ] Implement `pre_player_hook` (phase transitions, Aspect switching, Paradox Fracture, shard regen, Past/Future passives)
- [ ] Implement `enemy_turn_hook` (skill selection by Aspect + cycle + phase, damage calculation with Momentum multiplier + Defend checks + Paradox Fracture)
- [ ] Implement `post_round_hook` (Future bleed lifesteal calculation)
- [ ] Implement `on_kill_hook` (shard death prevention, stack drain, player heal)
- [ ] Implement `on_player_hit_hook` (Past retaliatory burn)
- [ ] Implement `custom_hud_hook` (_chrysalis_hud)

### Phase 3 — Integration
- [ ] Import `combat_entangled_chrysalis` in `dungeon.py`
- [ ] Add Pandemonium floor 20 check in `explore_dungeon()` (before normal superboss logic)
- [ ] Add Chrysalis-specific atmosphere text and encounter trigger
- [ ] Ensure Chrysalis does NOT consume a superboss pool slot
- [ ] Add Chrysalis to GUI superboss override (if applicable)
- [ ] Ensure normal superboss pool stays at tiers 0–7 (no tier 8)

### Phase 4 — Items
- [ ] Define `chronoweave_mantle` in `resources/items.py`
- [ ] Define `fractured_hourglass` in `resources/items.py`
- [ ] Implement `fractured_hourglass` use effect (skill cooldown reset)
- [ ] Add loot drop logic in `combat_entangled_chrysalis.py`

### Phase 5 — Testing
- [ ] Smoke test: boss spawns on Pandemonium floor 20, shards spawn, combat loop runs
- [ ] Verify Chrysalis does NOT appear in normal superboss pool (tiers 0–7)
- [ ] Test Aspect switching: hit each shard, verify stack drain on "kill"
- [ ] Test Paradox Fracture: force switches, verify damage multiplier
- [ ] Test Phase transitions: verify 2 actions with empowered skills in Phase 2, verify Phase 3 empowerment
- [ ] Test shard immortality: verify HP resets to 1, not removed from enemy list
- [ ] Test damage redirect: verify 50% of shard HP lost transfers to boss
- [ ] Test bleed detonation + lifesteal (Future Aspect)
- [ ] Test burn detonation + flame spread (Past Aspect)
- [ ] Test detonate fallbacks (cleanse burn/bleed before detonation)
- [ ] Test Momentum scaling (Present Aspect) — verify cap at 20/30
- [ ] Test retaliatory burn (Past Aspect)
- [ ] Test Defend interactions: verify ⅓ Momentum on Defend, signature skill penalties on Defend
- [ ] Test Pandemonium curse interactions (all curse types)
- [ ] Test with Tier 2 curse scaling (1.5×) active
- [ ] Test victory → loot drop → no pool slot consumed
- [ ] Test defeat → player death flow
- [ ] Test GUI mode compatibility
- [ ] Test with allies: shard targeting, retaliatory burn on allies, Momentum based on party size

---

*Blueprint generated for TerminalRPG Pandemonium expansion.*
*Inspired by Butterfly of Entangled Lives (Limbus Company / Project Moon).*
*All mechanics fully adapted to TerminalRPG's initiative-based combat system.*
