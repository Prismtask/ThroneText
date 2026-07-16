# Certain Someone Black Gloves — Design Blueprint

> *"I have nothing but my sorrow and I want nothing more. It has been, it still is, faithful to me."*
>
> — The Black Silence, *Library of Ruina*

---

## Table of Contents

1. [Overview](#overview)
2. [Lore & Acquisition](#lore--acquisition)
3. [Equipment Definition](#equipment-definition)
4. [Passive Effects](#passive-effects)
5. [The Nine Workshops — Attack Definitions](#the-nine-workshops--attack-definitions)
6. [Furioso — The Ultimate](#furioso--the-ultimate)
7. [Skill Replacement Contract](#skill-replacement-contract)
8. [Combat Flow & State Machine](#combat-flow--state-machine)
9. [Action Menu Integration](#action-menu-integration)
10. [Player State Keys](#player-state-keys)
11. [Edge Cases & Rules](#edge-cases--rules)
12. [Allies Wearing the Gloves](#allies-wearing-the-gloves)
13. [Implementation Checklist](#implementation-checklist)
14. [Tuning Levers](#tuning-levers)

---

## Overview

| Property | Value |
|---|---|
| **Name** | Certain Someone Black Gloves |
| **Type** | Equipment → Weapon |
| **Slot** | `weapon` |
| **Rarity** | Legendary |
| **Unique** | Yes |
| **Source** | `black_silence` (superboss) |
| **Scaling Stats** | `Strength`, `Dexterity`, `Learning` |
| **Element** | `dark` (primary) |
| **Core Identity** | Replaces ALL class skills with 9 one-use-per-cycle workshop attacks + Furioso ultimate |

---

## Lore & Acquisition

> Dropped by **The Black Silence** — a wandering figure cloaked in sorrow, silent save for the whisper of leather and steel. Some say they were once a fixer of great renown; others claim they are nothing but a shade, bound to the gloves by an oath broken long ago.

**Acquisition**: Defeat the superboss `black_silence` (a new enemy to be designed separately). 100% drop rate. Can only drop once per save file.

**Flavor text on inspection**:
> *Black leather gloves, worn smooth by countless battles. Nine names are stitched into the lining, each in a different hand. They pulse faintly — eager, hungry, mourning.*

---

## Equipment Definition

```python
# resources/items.py
"certain_someone_black_gloves": {
    "name": "Certain Someone Black Gloves",
    "type": "equipment",
    "slot": "weapon",
    "unique": True,
    "base_mods": {"Strength": 4, "Dexterity": 4, "Learning": 3},
    "scaling_stat": ["Strength", "Dexterity", "Learning"],
    "elemental_dmg": {"dark": 1.5},
    "special": "black_silence_gloves",
    "drop_source": "black_silence",
    "drop_rarity": "legendary",
},
```

**Stat comparison to existing legendary weapons**:

| Weapon | Total Stat Bonus | Scaling |
|---|---|---|
| Abyss Fang | +9 (STR+6, DEX+3) | STR + DEX |
| Cutlass of the Captain | +8 (STR+5, DEX+3) | STR |
| **Black Gloves** | **+11** (STR+4, DEX+4, LER+3) | STR + DEX + LER |

The gloves give the highest total stat bonus but spread across 3 stats — harder to fully utilize unless you build hybrid.

---

## Passive Effects

Both passives are active **only while the gloves are equipped**.

### Passive 1: Mourning Advantage

> *The silence strikes first.*

- **+3 flat initiative** bonus (added to `roll_initiative()` speed roll)
- **+8% dodge chance** (additive, respects the 80% cap)
- **First Strike**: If you act first in a round (your initiative beats all enemies), gain **+15% damage** for that round only. Does not stack round-to-round.

```
Implementation note:
- Add 3 to player_speed in roll_initiative()
- Add 0.08 to dodge base in get_dodge_chance() before cap
- Track a combat_state key: "gloves_first_strike" = True/False, 
  checked in damage calculation for +15% multiplicative bonus
```

### Passive 2: Silent Pact

> *The gloves remember. Your old tricks will not avail you.*

- All class skills (and ally innate/learned skills if worn by ally) are **disabled**
- The action menu replaces skill slots 1–9 with workshop attacks
- Items, Defend, Flee, Capture remain available
- If another special weapon action would appear (Abyss Fang `[W]`, Cutlass `[R]`), they are also suppressed — the gloves tolerate no rivals

---

## The Nine Workshops — Attack Definitions

Each attack is **pseudo-locked**: usable once, then disabled until Furioso resets the cycle.

### Damage Formula (all workshops)

```
base_damage = random(4, 10) + (scaling_stat_value) + STR_milestone_bonus
final_damage = base_damage × workshop_damage_multiplier − enemy_con_mod
final_damage = max(0, final_damage)
then apply elemental mods, crit, first_strike bonus, etc.
```

The `scaling_stat_value` is the player's effective attribute for that workshop (see table below).

### Workshop Attack Table

| # | Workshop | Scaling | Target | Dmg Mult | Special Effect |
|---|---|---|---|---|---|
| 1 | **Allas Workshop** | STR | Single | 1.10× | Ignore 20% of target's CON (DEF piercing) |
| 2 | **Wheels Industry** | STR | AoE | 0.70× | 30% chance to Stun each target for 1 turn |
| 3 | **Zelkova Workshop** | DEX | Single | 0.70× | Hit **twice** (each at 0.70×, total 1.40×) |
| 4 | **Old Boys Workshop** | STR | Single | 1.00× | 65% chance to Stun for 1 turn |
| 5 | **Mook Workshop** | WIS | AoE | 0.70× | Lifesteal: heal 50% of total damage dealt |
| 6 | **Ranga Workshop** | DEX | Single | 1.00× | 70% chance to apply Bleed (6 dmg × 3 turns) |
| 7 | **Crystal Atelier** | DEX | Single | 0.90× | Grant self +20% dodge for 2 turns |
| 8 | **Atelier Logic** | WIS | Single | 2.00× | **Once per cycle** (cannot reuse until after Furioso) |
| 9 | **Durandal** | LER | 3 hits random | 0.60× | Hits 3 times; if only 1 enemy alive, all 3 hit that enemy |

### Detailed Workshop Behaviors

#### 1. Allas Workshop — *"The Workshop of Precision"*
```
Scaling: Strength
Target: Choose one enemy
Damage: (d4-10 + STR) × 1.10
Effect: Target's effective CON is reduced by 20% for this hit only.
        effective_con = int(target["con_mod"] * 0.80)
```

#### 2. Wheels Industry — *"The Workshop of Industry"*
```
Scaling: Strength
Target: ALL enemies
Damage: (d4-10 + STR) × 0.70  per enemy
Effect: Each enemy rolls separately: 30% chance → stunned for 1 turn.
        Stunned: skip next action, then clear.
```

#### 3. Zelkova Workshop — *"The Workshop of Swiftness"*
```
Scaling: Dexterity
Target: Choose one enemy
Damage: TWO hits, each at (d4-10 + DEX) × 0.70
        Roll dodge, crit, and CON reduction separately for each hit.
        Total expected: ~1.40× normal damage.
```

#### 4. Old Boys Workshop — *"The Workshop of Brute Force"*
```
Scaling: Strength
Target: Choose one enemy
Damage: (d4-10 + STR) × 1.00
Effect: 65% chance to Stun for 1 turn.
        High reliability control, but standard damage.
```

#### 5. Mook Workshop — *"The Workshop of Sustenance"*
```
Scaling: Wisdom
Target: ALL enemies
Damage: (d4-10 + WIS) × 0.70  per enemy
Effect: Sum all damage dealt across all enemies, 
        heal the wearer for 50% of that total.
        (e.g., deal 30 total across 3 enemies → heal 15 HP)
```

#### 6. Ranga Workshop — *"The Workshop of Bloodletting"*
```
Scaling: Dexterity
Target: Choose one enemy
Damage: (d4-10 + DEX) × 1.00
Effect: 70% chance to apply Bleed (6 damage × 3 turns).
        Bleed is non-stacking — stronger bleed overwrites weaker.
        Uses existing apply_bleed() system.
```

#### 7. Crystal Atelier — *"The Atelier of Crystal"*
```
Scaling: Dexterity
Target: Choose one enemy
Damage: (d4-10 + DEX) × 0.90
Effect: Grant wearer a +20% dodge buff for 2 turns.
        Buff type: "evasion", value: 0.20, remaining: 2.
        Stacks with existing dodge (capped at 80%).
```

#### 8. Atelier Logic — *"The Atelier of Logic"*
```
Scaling: Wisdom
Target: Choose one enemy
Damage: (d4-10 + WIS) × 2.00
Effect: Once per cycle. After use, it is locked.
        ONLY unlocks again after Furioso is used.
        This is your "big nuke" — save it for the right moment.
```

#### 9. Durandal — *"The Sword of Roland"*
```
Scaling: Learning
Target: Random enemies (3 hits)
Damage: Each hit at (d4-10 + LER) × 0.60
Effect: If ≥2 enemies alive: 3 hits distributed randomly across all alive enemies.
        If 1 enemy alive: all 3 hits go to that enemy.
        Each hit checks dodge/crit/CON independently.
        Total expected (single enemy): ~1.80× normal damage.
```

---

## Furioso — The Ultimate

### Unlock Condition

Furioso appears as action `[0]` on the menu **only when all 9 workshop attacks have been used at least once** in the current cycle.

### Behavior

> *The gloves hum in unison. Nine voices become one.*
> *"FURIOSO."*

```
Furioso executes ALL 9 workshop attacks in sequence:
- Allas → Wheels Industry → Zelkova → Old Boys → Mook → 
  Ranga → Crystal Atelier → Atelier Logic → Durandal

Each hit during Furioso:
- Deals damage at 0.75× of the normal workshop value
- Special effects operate at 50% potency:
  · Stun chance halved (Wheels: 15%, Old Boys: 32.5%)
  · Lifesteal halved (Mook: 25%)
  · Bleed chance halved (Ranga: 35%)
  · DEF pierce halved (Allas: ignore 10%)
  · Dodge buff halved (Crystal Atelier: +10%)
  · Atelier Logic uses 0.75× multiplier too (so 1.50× total vs normal 2.00×)
  · Durandal hits at 0.45× per hit (0.75 × 0.60)

Targeting during Furioso:
- After each hit, switch to the next alive enemy (round-robin).
- If an enemy dies mid-Furioso, skip to the next.
- If all enemies die before all 9 hits are done, Furioso stops early.

Total Furioso damage (all 9 hits, same target): ~6.75× base attack

After Furioso completes:
- ALL workshop attack locks are cleared
- Atelier Logic becomes available again
- The cycle resets — you're back to turn 1 of the new cycle
- Display: "The gloves fall silent. The cycle begins anew."
```

### Furioso Takes One Full Turn

Using Furioso consumes your action for the round. You cannot attack, defend, or use an item on the same turn.

---

## Skill Replacement Contract

When the gloves are equipped (checked in `get_action_menu()`):

```
BEFORE (normal):
  [C]Capture  [A]Attack  [D]Defend  [F]Flee  [U]Use item  [W]Wield Abyss  [1]Skill1  [2]Skill2 ...

AFTER (gloves equipped):
  [C]Capture  [D]Defend  [F]Flee  [U]Use item  
  [1]Allas  [2]Wheels  [3]Zelkova  [4]Old Boys  [5]Mook  
  [6]Ranga  [7]Crystal  [8]Logic  [9]Durandal  [0]FURIOSO
```

Key changes:
- `[A]Attack` is **removed** (basic attack not available)
- `[W]Wield Abyss`, `[R]Crew Rally` are **suppressed** (gloves override other special weapons)
- Skills 1–9 are **replaced** by workshop attacks 1–9
- `[0]Furioso` appears **only when all 9 are used**
- Items, Defend, Flee, Capture all remain available

---

## Combat Flow & State Machine

### Per-Combat Lifecycle

```
COMBAT START
  │
  ├─ clear_gloves_state(player)
  │    · gloves_workshop_used = set()        (empty)
  │    · gloves_furioso_available = False
  │    · gloves_first_strike_bonus = False
  │
  ▼
EACH ROUND ──► roll_initiative() ──► determine first strike bonus
  │
  ▼
PLAYER TURN ──► get_action_menu() shows workshops
  │
  ├─ Player picks [1]-[9]
  │    ├─ Execute workshop attack
  │    ├─ Add to gloves_workshop_used set
  │    ├─ If set size == 9 → gloves_furioso_available = True
  │    └─ return
  │
  ├─ Player picks [0] (Furioso)
  │    ├─ Execute all 9 in sequence
  │    ├─ clear_gloves_state(player)   (reset)
  │    └─ return
  │
  ▼
COMBAT END ──► clear_gloves_state(player)
```

### State Persistence

- Workshop usage state persists **within a single combat only**
- State is cleared on combat start and combat end
- State does NOT persist in save files (no save/load complexity needed)

---

## Action Menu Integration

### `get_action_menu()` pseudocode addition

```python
# combat/action_menu.py

def get_action_menu(player, enemies):
    actions = []
    
    # Check if Black Silence Gloves are equipped
    if _player_has_black_silence_gloves(player):
        # Suppress standard attack, special weapon actions, and skills
        if any(is_monster_girl(e) for e in enemies):
            actions.append(('c', 'Capture'))
        actions.append(('d', 'Defend'))
        actions.append(('f', 'Flee'))
        if not is_silenced(player):
            actions.append(('u', 'Use item'))
        
        # Add workshop attacks
        workshop_state = player.get("gloves_workshop_used", set())
        workshop_menu = [
            ('1', 'Allas Workshop'),
            ('2', 'Wheels Industry'),
            ('3', 'Zelkova Workshop'),
            ('4', 'Old Boys Workshop'),
            ('5', 'Mook Workshop'),
            ('6', 'Ranga Workshop'),
            ('7', 'Crystal Atelier'),
            ('8', 'Atelier Logic'),
            ('9', 'Durandal'),
        ]
        for key, label in workshop_menu:
            if key not in workshop_state:
                actions.append((key, label))
            else:
                actions.append((key, f'[{label} — USED]'))  # greyed out / strikethrough
        
        # Furioso — only if all 9 used
        if len(workshop_state) >= 9:
            actions.append(('0', 'FURIOSO'))
    else:
        # ... normal menu logic ...
        pass
    
    # ... build menu string ...
    return menu_str, valid_keys
```

### `handle_player_turn()` pseudocode addition

```python
# combat/player_actions.py — inside handle_player_turn()

if _player_has_black_silence_gloves(player) and action in [str(i) for i in range(1, 10)] + ['0']:
    if action == '0':
        return _execute_furioso(player, enemies, allies, ...)
    else:
        workshop_id = int(action)  # 1-9
        return _execute_workshop(player, enemies, workshop_id, p_str, p_con, p_dex, p_ler, p_wis, p_cha, ...)
```

---

## Player State Keys

Keys added to `player` dict at combat start, cleaned at combat end:

| Key | Type | Default | Description |
|---|---|---|---|
| `gloves_workshop_used` | `set[int]` | `set()` | Indices 1–9 of workshops used this cycle |
| `gloves_furioso_available` | `bool` | `False` | Whether Furioso can be activated |
| `gloves_first_strike_active` | `bool` | `False` | Set at round start if player acts first |

All three keys are **cleared** on combat end and on Furioso use.

---

## Edge Cases & Rules

### 1. Combat ends before Furioso
- State is cleared. No carryover to next combat. The cycle starts fresh each fight.

### 2. Enemy dies mid-Furioso
- Skip that attack, advance to next enemy. If no enemies remain, Furioso ends early. Remaining hits are lost.

### 3. Furioso with only 1 enemy alive
- All 9 hits go to that enemy. The "switch target" rule has nowhere to go.

### 4. Stunned during Furioso?
- Furioso happens on YOUR turn. You can only use it when it's your turn, so stun is irrelevant — if you're stunned, you skip your turn and can't activate Furioso.

### 5. Silenced while wearing gloves
- Item usage is blocked (standard silence behavior). Workshop attacks are NOT blocked — they're martial, not magical. This is intentional: the gloves give you a workaround for silence.

### 6. Weapon swap mid-combat
- If the player unequips the gloves mid-combat (via inventory), workshop state is cleared, normal menu returns. (Unlikely but handle gracefully.)

### 7. Multiple enemies and Durandal targeting
- Use `random.choice(alive_enemies)` for each of the 3 hits. Same enemy can be hit multiple times even with multiple enemies alive. This is intended RNG — sometimes Durandal spreads, sometimes it focuses.

### 8. Bleed from Ranga vs existing bleed
- Standard bleed rules: stronger bleed (higher damage) overwrites weaker. If enemy already has bleed 8 and Ranga would apply bleed 6, it's a no-op. If enemy has bleed 3, Ranga's bleed 6 overwrites it.

### 9. Lifesteal from Mook when at full HP
- Still works, but heals 0 (you're already at max). Overheal is lost. No temporary HP.

### 10. Defend action with gloves
- Still available. Defend still gives the normal damage reduction. This is your only defensive option besides Crystal Atelier's dodge buff and Mook's lifesteal.

---

## Allies Wearing the Gloves

If the gloves could be equipped by an ally (via inventory system):

- Ally's **innate skills** (2 skills) are disabled
- Ally's **learned skills** are disabled
- Ally's **race passive** remains active (passive is separate from skills)
- Ally gets the same 9 workshop attacks + Furioso
- Ally AI would need a decision tree for workshop selection (or controlled manually)

**Recommendation**: Initially make the gloves **player-only** (`slot: "weapon"` with a player-only equip flag). Ally support can be added later when the ally combat AI is mature enough to handle 9 distinct tactical options.

---

## Implementation Checklist

### Phase 1: Data Definition
- [ ] Add `"certain_someone_black_gloves"` to `resources/items.py`
- [ ] Add `black_silence` enemy template to `resources/enemies/`
- [ ] Add elemental keywords for "black" / "silence" if desired

### Phase 2: State Management
- [ ] Create `combat/black_silence_gloves.py` module
- [ ] Implement `_player_has_black_silence_gloves(player)` check
- [ ] Implement `clear_gloves_state(player)`
- [ ] Implement `init_gloves_state(player)` (called at combat start)

### Phase 3: Action Menu
- [ ] Modify `combat/action_menu.py` → `get_action_menu()` to detect gloves and replace menu
- [ ] Show "[USED]" for exhausted workshops
- [ ] Show "[0]FURIOSO" when all 9 used

### Phase 4: Workshop Execution
- [ ] Implement `execute_workshop(player, enemies, workshop_id, stats, ...)` in `black_silence_gloves.py`
- [ ] Allas: 20% DEF ignore
- [ ] Wheels Industry: 30% stun AoE
- [ ] Zelkova: double hit
- [ ] Old Boys: 65% stun single
- [ ] Mook: AoE lifesteal 50%
- [ ] Ranga: 70% bleed
- [ ] Crystal Atelier: +20% dodge self-buff
- [ ] Atelier Logic: 2.00× single, once per cycle
- [ ] Durandal: 3 random hits, LER scaling

### Phase 5: Furioso
- [ ] Implement `execute_furioso(player, enemies, allies, ...)`
- [ ] 9-hit sequence with reduced potency
- [ ] Round-robin targeting between hits
- [ ] State reset after completion

### Phase 6: Passives
- [ ] Modify `roll_initiative()` to add +3 when gloves equipped
- [ ] Add +8% dodge in `get_dodge_chance()` when gloves equipped
- [ ] Track first-strike bonus and apply +15% damage in damage calc

### Phase 7: Integration
- [ ] Wire into `handle_player_turn()` in `combat/player_actions.py`
- [ ] Call `clear_gloves_state()` at combat start and combat end in `combat_engine.py`
- [ ] Ensure silence doesn't block workshop attacks
- [ ] Ensure other special weapon actions (Abyss Fang, Cutlass) are suppressed

### Phase 8: Polish
- [ ] Flavor text for each workshop attack
- [ ] Furioso animation text (each hit with workshop name)
- [ ] Sound hooks or screen shake events (if GUI supports)
- [ ] Playtest damage numbers across all 9 workshops

---

## Tuning Levers

All values below are starting points. Adjust after playtesting.

| Parameter | Value | Notes |
|---|---|---|
| Base stat mods | STR+4, DEX+4, LER+3 | Total +11 |
| Initiative bonus | +3 | Flat, additive |
| Dodge bonus | +8% | Additive, capped at 80% |
| First strike damage | +15% | Multiplicative, one round only |
| Workshop base die | d(4–10) | Same as normal attack |
| Workshop damage multipliers | 0.60–2.00 | See table above |
| Furioso hit multiplier | 0.75× | Per hit during Furioso |
| Furioso effect potency | 50% | Halved stun/bleed/lifesteal/etc. |
| Wheels stun chance | 30% | Per enemy |
| Old Boys stun chance | 65% | Single target |
| Mook lifesteal ratio | 50% | Of total damage dealt |
| Ranga bleed damage | 6 | Per turn, 3 turns |
| Ranga bleed chance | 70% | — |
| Crystal dodge buff | +20% | 2 turn duration |
| Durandal hits | 3 | Random targeting |

### Quick Damage Comparison (midgame: ~12 in each stat)

| Attack | Expected Damage |
|---|---|
| Normal attack (greatsword, 12 STR) | ~19 |
| Allas Workshop | ~24 (piercing) |
| Zelkova Workshop (2 hits) | ~27 total |
| Old Boys Workshop | ~19 + 65% stun |
| Atelier Logic | ~38 (once per cycle) |
| Furioso (all 9, single target) | ~115 total |

---

*Blueprint last updated: 2026-07-10*
