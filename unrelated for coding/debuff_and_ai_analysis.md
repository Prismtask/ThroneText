# Debuff & Buff Mechanics Analysis — Pandemonium

> **Date:** 2026-07-14  
> **Scope:** How enemies apply debuffs to players, how players apply debuffs to enemies, and whether the enemy AI should use weighted decision-making for buff/debuff application.

---

## 1. Overview of the Status Effect System

All status effects (buffs and debuffs) are managed through `combat/status_effects.py`. The system uses a **list-of-dicts** pattern stored under `entity["active_debuffs"]` and `entity["active_buffs"]`. Each entry has at minimum:

```python
{"type": "poison", "damage": 5, "remaining": 3}
```

Some effects also use **flat boolean flags** on the entity dict (e.g., `enemy["stunned"] = True`, `player["silenced"] = True`) alongside their `active_debuffs` entry for HUD display and tick logic.

### Debuff Types (Enemies & Players)

| Debuff | Key | Effect |
|---|---|---|
| **Poison** | `poison` | Flat DoT per round |
| **Bleed** | `bleed` | Flat DoT per round (higher damage overwrites) |
| **Burn** | `burn` | Tiered DoT (1-5), reduces enemy CON on first application |
| **Curse** | `curse` | Permanent stat penalty until cured (player only) |
| **Weaken** | `weaken` | Reduces STR for damage calculations |
| **Silence** | `silence` | Prevents item use |
| **Dread** | `dread` | 40% miss chance + harder flee |
| **Blind** | `blind` | 25-40% miss chance (player: 25%, enemy: 40%) |
| **Slow** | `slow` | -3 DEX for initiative, persisted after freeze thaws |
| **Stun** | `stun` | Skip next action (auto-clears after one skip) |
| **Freeze** | `frozen` | Skip actions + applies slow on thaw |
| **Paralyze** | `paralyze` | Multi-turn action skip (stronger than stun) |
| **Confusion** | `confusion` | 30% chance to hit own ally or miss |
| **Fear** | `fear` | Reduces outgoing damage by % (value field) |
| **Shock** | `shock` | Thunder DoT + 25% stun proc per tick |
| **Sleep** | `sleep` | Skip turns; breaks on damage |
| **Entomb** | `entomb` | Cannot flee; healing received is halved |
| **Void-Touched** | `void_touched` | Healing received becomes damage |
| **Vulnerable** | `vulnerable` | Takes increased damage (multiplier) |
| **Sunder** | `sunder` | Reduces enemy CON (armor) |
| **Expose** | `expose` | Permanently reduces CON (stacks up to -5) |
| **Elemental Weakness** | `elemental_weakness` | Reduces elemental resistance |

### Buff Types (Players & Allies)

| Buff | Key | Effect |
|---|---|---|
| **HoT (Heal over Time)** | `hot` | Flat HP regen per round |
| **Regeneration** | `regen` | Long-duration HoT |
| **Barrier** | `barrier` | Damage-absorb shield (stacks) |
| **Haste** | `haste` | +Initiative, cooldown reduction charges |
| **Divine Shield** | `divine_shield` | Blocks one attack entirely |
| **Defense** | `defense` | Flat damage reduction |
| **Defense%** | `defense_pct` | Percentage damage reduction |
| **Reflection** | `reflection` | % of damage taken reflected back |
| **Stat Buffs** | `stat` | Temporary attribute increase |
| **Dodge** | `dodge` | Guaranteed dodge on next attack |
| **Fire Resist** | `fire_resist` | Elemental resistance buff |

---

## 2. How Enemies Apply Debuffs to Players

### 2.1 The `enemy_attack()` Flow

File: `combat/enemy_ai.py`

The enemy attack pipeline runs in this order:

```
1. Tick fear debuff on enemy (if any) → reduces enemy's outgoing damage
2. Tick enemy's own debuffs (poison/burn/bleed/etc.) → if dies, return "died"
3. Check status locks: asleep? paralyzed? stunned? frozen? → skip turn
4. Blind check: 40% chance to miss
5. Confusion check: 30% chance to hit ally or miss
6. Player dodge check (capped at 80%)
7. Wedding pre-damage effects (foxfire trick, etc.)
8. Divine Shield check → block entirely
9. Calculate damage (STR + random + crit + fear multiplier − block)
10. Vulnerable multiplier on player
11. Elemental damage calculation
12. Defense buffs (flat + percentage)
13. CON milestone reduction
14. Barrier absorption
15. Apply damage to player HP
16. Reflection damage back to enemy
17. → **extra_logic(enemy, player, damage)** ← DEBUFF APPLICATION POINT
```

### 2.2 Racial `extra_logic` — The Core Debuff Mechanism

After damage is dealt, `get_race_extra_logic(enemy)` returns a callback function based on the enemy's **race**. This is the **only** systematic way enemies apply debuffs:

| Race | Debuff | Proc Chance | Details |
|---|---|---|---|
| **Beast** | Bleed | 35% | `damage // 3` bleed for 4 turns |
| **Undead** | Curse | 20% | All attributes reduced (permanent) |
| **Shadow** | Dread | 30% | 40% miss chance, harder flee |
| **Demon** | Weaken | 25% | STR -2 for 3 turns |
| **Vampire** | Drain | 100% (on dmg>0) | Steals `dmg//2` HP, heals self |
| **Fey** | Silence | 25% | Prevents items for 2 turns |
| **Abomination** | Weaken | 35% | STR -3 for 3 turns (stronger) |
| **Giant** | Weaken | 30% | STR -4 for 2 turns (strongest weaken) |
| **Gnome** | Silence | 20% | Prevents items for 2 turns |
| **Elemental** | Blind | 30% | -25% accuracy + -2 DEX for flee |
| **Storybook** | Confusion/Dread/Silence | 22% | Random plot twist; also self-heal (25% @ <35% HP) and self-buff (15% @ >60% HP) |

### 2.3 Wonderland Floor Bosses

File: `combat/wl_floor_bosses.py`

Floor bosses use bespoke AI functions (not the racial system). They are registered in `WL_FLOOR_BOSS_MAP` and have their own debuff logic, which may include:

- Unique status effects specific to the boss
- Multi-phase behavior changes
- Conditional debuff application based on boss state

### 2.4 Superbosses

Superbosses (Black Silence, Chrysalis, Mary Sue, etc.) have their own `enemy_turn_hook()` with custom debuff logic. These are handled outside the standard `enemy_attack()` pipeline via the `extra_logic` parameter.

### 2.5 Summary: Enemy Debuff Application Pattern

```
Enemy attacks → deals damage → race determines proc chance → one specific debuff applied
```

**Key observations:**
- Enemies do NOT choose between debuffs — each race has exactly ONE debuff type
- Storybook is the exception: it randomly picks from 3 debuffs + 2 self-effects
- There is no "should I debuff or buff?" decision — it's purely reactive
- Enemies cannot buff themselves (except Storybook's self-STR-buff)
- There is no consideration of: "does the player already have this debuff?", "is the player low on HP?", "would a different debuff be better?"

---

## 3. How Players Apply Debuffs to Enemies

Players have **four** distinct avenues for inflicting debuffs:

### 3.1 Class Skills

File: `combat/skills.py`

Skills are the primary debuff delivery mechanism. Examples:

| Skill | Class | Debuff | Notes |
|---|---|---|---|
| War Cry | Warrior | Fear (all enemies) | 20% damage reduction, 3 turns |
| Execute | Warrior | Stun | Single target |
| Shield Slam | Warrior | Stun | Proc chance |
| Sunder Armor | Barbarian | Sunder (armor reduction) | -3 CON, 3 turns |
| Earth Shatter | Barbarian | Stun (AoE) | Proc chance per enemy |
| Venomous Blade | Rogue | Poison | 5 damage/turn, 5 turns |
| Nature's Grasp | Ranger | Slow (all enemies) | -3 DEX |
| Consecrate | Paladin | Weaken (all enemies) | -2 STR, 3 turns |
| Soul Fire | Warlock | Burn | Tier-based DoT |

Skills also support **generic debuff flags** on any skill definition:
- `apply_slow` → slows target
- `stun_chance` → chance to stun
- `apply_weaken` → weakens target
- `burn_damage` → applies burn (auto-converted to tier)
- `poison_damage` → applies poison
- `apply_sunder` → reduces armor

### 3.2 Basic Attacks (Weapon Traits)

File: `combat/elemental_traits.py`

Weapons can have **elemental traits** that trigger on-hit:

| Trait | Effect | Trigger |
|---|---|---|
| **Ignite** | Applies burn | On hit |
| **Chain** | Hits additional enemies | On hit |
| **Sunder** | Armor penetration (ignores % of CON) | Pre-damage |
| **Pierce** | Ignores % of enemy elemental resistance | Pre-damage |
| **Leech** | Life steal | On hit |
| **Swift** | Bonus action/initiative | On hit |
| **Bulwark** | Self-defense buff | On hit |

### 3.3 Combat Items

File: `combat/player_actions.py` (use item section)

Items can carry debuff keys:
- `blind_enemy` → applies blind
- `poison_damage` → applies poison
- `stun_chance` → chance to stun
- `expose_armor` → reduces CON permanently
- `burn_tier` → applies tiered burn
- `shock_damage` → applies shock (DoT + stun proc)
- `damage_over_time` → generic DoT

### 3.4 Wedding Accessories & Superboss Weapons

- **Wedding accessories** (`combat/wedding_specials.py`): Pharaoh's Curse, Infernal Crown, Keening Wail — various retribution/proc effects
- **Captain's Cutlass** (`combat/captain_cutlass.py`): High Tide stacks, Rally buffs, Captain's Authority riposte
- **Abyss Fang** (`combat/abyss_fang.py`): Abyssal Tempo system
- **Tarnished Jade** (`combat/tarnished_jade.py`): Pin system → Divine Intervention

### 3.5 Vileheart Pendant

File: `combat/vileheart_venom.py`

Chance to poison on any physical hit.

### 3.6 Summary: Player Debuff Application Pattern

```
Player acts → skill/item/attack → debuff key checked → apply_X() called → active_debuffs list updated
```

Players have **intentional control** over debuffs:
- They choose which skill to use (tactical decision)
- They choose which target receives it
- They consider cooldowns and opportunity cost

---

## 4. The Tick System: How Debuffs Resolve

### 4.1 Enemy Debuff Ticking

`tick_enemy_debuffs(enemy)` is called at the **start** of every enemy's turn (before they act). This means:

- DoT effects (poison, bleed, burn, shock) deal damage BEFORE the enemy can attack
- An enemy can die to DoT before getting to act
- Status effects decrement duration at turn start

### 4.2 Player Debuff Ticking

`tick_player_debuffs(player)` is called once per **round** (in `_tick_all_state()` in `combat_engine.py`), not per enemy turn. Player debuffs tick at the beginning of each combat round.

### 4.3 Player Buff Ticking

`tick_player_buffs(player)` runs at the same time — once per round. This handles HoT, barrier decay, haste countdown, stat buff expiration.

---

## 5. Current AI Limitations & Weighted AI Proposal

### 5.1 Current State: No Strategic AI

The enemy AI currently operates on a **deterministic racial table**:

```python
if race == "Beast":
    # Always try bleed (35% chance)
elif race == "Undead":
    # Always try curse (20% chance)
# ... etc
```

**What's missing:**
1. **No conditional logic** — enemies don't check if a debuff is already active
2. **No tactical awareness** — enemies don't consider player HP, debuff stacking, or threat
3. **No buff self-awareness** — enemies (except Storybook) never buff themselves
4. **No multi-debuff choice** — each enemy race has exactly one debuff, no decision space
5. **No priority system** — no concept of "the player is low HP, I should use X instead of Y"

### 5.2 Should Enemies Have Weighted AI?

**Yes, for certain enemy tiers.** A weighted AI system would add tactical depth. Here's a proposed framework:

#### Tier 1: Standard Enemies (Keep Simple)
- Keep the current racial proc system
- Low proc chances (15-35%) are fine for trash mobs
- No strategic AI needed — simplicity is good here

#### Tier 2: Elite Enemies (Lightweight AI)
- **Condition checks**: "Is player already bleeding? If so, try a different debuff."
- **Priority weights**: e.g., if player is NOT silenced → 60% weight on silence; if already silenced → 10% weight
- **HP-aware**: if player is below 30% HP → prioritize direct damage over debuffs
- Each elite enemy could have 2-3 possible debuffs with weighted selection

#### Tier 3: Bosses & Superbosses (Full AI)
- **Multi-action turns**: Boss can attack AND apply a debuff in one turn
- **Phase-based behavior**: Different debuff priorities at <50% HP, <25% HP
- **Reactive AI**: If player buffed themselves → apply dispel/debuff to counter
- **Self-buffing**: Bosses should buff themselves at HP thresholds
- **Threat assessment**: Prioritize debuffing the highest-damage party member
- **Cooldown awareness**: Track which debuffs were recently applied and avoid spam

### 5.3 Weighted AI Example Pseudocode

```python
def enemy_choose_debuff(enemy, player, all_enemies):
    """Weighted debuff selection for elite+ enemies."""
    choices = []
    
    # Condition checks
    player_below_half = player["current_hp"] < player_max_hp(player) // 2
    player_is_buffed = len(player.get("active_buffs", [])) > 2
    player_has_bleed = any(d["type"] == "bleed" for d in player.get("active_debuffs", []))
    
    # Build weighted options
    choices.append(("direct_damage", 40))  # baseline
    
    if not player_has_bleed:
        choices.append(("apply_bleed", 25))
    
    if not player.get("silenced"):
        choices.append(("apply_silence", 20))
    
    if player_below_half:
        # Shift weights toward finishing the player
        choices = [(name, w * 1.5) for name, w in choices]
    
    if player_is_buffed:
        choices.append(("apply_dispel", 15))
    
    # Normalize and roll
    total = sum(w for _, w in choices)
    roll = random.uniform(0, total)
    cumulative = 0
    for name, weight in choices:
        cumulative += weight
        if roll <= cumulative:
            return name
    
    return "direct_damage"
```

### 5.4 Implementation Considerations

1. **Backward compatibility**: The racial `extra_logic` system must continue to work for standard enemies
2. **AI tier field**: Add `"ai_tier": "standard" | "elite" | "boss"` to enemy definitions in `resources/enemies/`
3. **Debuff pool per enemy**: Define `"debuff_pool"` on enemy dicts for elite+ enemies
4. **Memory/state tracking**: Enemies need to remember what they've applied (could use a simple dict `enemy["ai_memory"] = {}`)
5. **Performance**: Weighted random is cheap — no concern for turn-based combat
6. **Balance**: Start with small weights and playtest; overtuned AI feels unfair

### 5.5 Potential Debuff Pools by Enemy Archetype

| Archetype | Possible Debuffs | AI Priority |
|---|---|---|
| **Brute** (Beast/Giant) | Bleed, Weaken, Stun | Weaken first, then bleed |
| **Caster** (Fey/Gnome) | Silence, Dread, Confusion | Silence casters, dread melee |
| **Undead** | Curse, Drain, Fear | Curse early, drain when hurt |
| **Assassin** (Shadow/Demon) | Blind, Poison, Weaken | Blind → Poison → finish |
| **Elemental** | Burn, Freeze, Shock | Stack burn tiers, freeze when threatened |
| **Support/Buffer** | Self-buff, Ally heal, Dispel | Prioritize self-preservation |

---

## 6. Elemental Profile Debuff System (New Design)

> **Status:** Proposal — extends the 5.5 archetype table into a concrete implementation plan.  
> **Key insight:** Every enemy already has an `elemental_dmg` profile (from `resources/enemies/enemy_races.py`).  
> This section designs a system where that profile drives a **secondary debuff channel** for standard enemies, with proc chance scaling dynamically on round number and enemy level.

### 6.1 Rationale

Currently, enemy elemental profiles only affect **damage multipliers** — an Orc with `elemental_dmg: {"fire": 1.3}` just hits harder with fire. There is no *qualitative* difference between fighting a fire-aspected Orc vs a dark-aspected Shadow.

By attaching debuffs to elemental damage strength, every enemy gains a secondary tactical identity based on its elemental makeup, without needing per-enemy AI scripts.

### 6.2 Element → Debuff Mapping

Each element maps to a thematically appropriate debuff. Only elements where the enemy has `elemental_dmg[element] > 1.0` (i.e., "strong" in that element) can trigger the associated debuff.

| Element | Debuff | Effect | Thematic Rationale |
|---|---|---|---|
| **Fire** | Burn | Tiered DoT (1-5), -1 CON | Flames linger and sear armor |
| **Water** | Slow | -3 DEX, initiative penalty | Ice/frost numbs movement |
| **Thunder** | Shock | DoT + 25% stun proc per tick | Lightning jolts and paralyzes |
| **Wind** | Blind | 25% miss chance (player) | Gale-force winds obscure vision |
| **Earth** | Weaken | STR penalty for damage calc | Crushing force saps strength |
| **Light** | Silence | Prevents item use | Holy radiance seals mortal tools |
| **Dark** | Dread | 40% miss chance + harder flee | Shadow fills mind with terror |
| **Physical** | Bleed | Flat DoT per round | Raw wounds keep bleeding |
| **Magical** | Confusion | 30% self-hit or miss | Arcane feedback disorients |

**Design note:** This mapping intentionally overlaps with some racial debuffs. An enemy could apply BOTH its racial debuff AND its elemental debuff in the same attack — this is a feature, not a bug. It means a Fire-aspected Beast (e.g., a Hellhound) can proc Bleed (racial) AND Burn (elemental), making it feel genuinely different from a physical Beast.

### 6.3 Proc Chance Scaling Formula

The elemental debuff is rolled **independently** after the racial debuff. The base chance is tuned low so it's a bonus, not a guarantee.

```
P(proc) = BASE × round_factor × level_factor
```

Where:

| Parameter | Symbol | Range | Notes |
|---|---|---|---|
| **Base chance** | `BASE` | 0.08–0.15 | Per-element, see table below |
| **Round factor** | `round_factor` | 1.0–2.5 | Scales with combat length |
| **Level factor** | `level_factor` | 0.5–2.0 | Scales with enemy level |

#### 6.3.1 Base Chance by Element

Not all debuffs are equally impactful. The base chance reflects the debuff's potency:

| Element | Debuff | Base Chance | Reasoning |
|---|---|---|---|
| Fire | Burn | 12% | DoT that stacks in power — moderate base |
| Water | Slow | 10% | Soft CC, lower impact |
| Thunder | Shock | 8% | DoT + stun proc — very strong, keep rare |
| Wind | Blind | 10% | Moderate impact |
| Earth | Weaken | 12% | Reduces player output — significant |
| Light | Silence | 8% | Shuts down items — strong in certain fights |
| Dark | Dread | 10% | Miss chance — swingy RNG |
| Physical | Bleed | 15% | Simplest DoT — highest base because it's pure damage |
| Magical | Confusion | 8% | Can cause friendly fire — chaotic, keep low |

#### 6.3.2 Round Scaling (`round_factor`)

The longer combat drags on, the more dangerous enemies become. This prevents stall strategies and adds tension.

```
round_factor = 1.0 + (round_num - 1) × 0.08   # caps at 2.5 (round 20+)
```

| Round | Factor | Meaning |
|---|---|---|
| 1 | 1.00 | Baseline — enemy hasn't "warmed up" |
| 3 | 1.16 | Slight increase |
| 5 | 1.32 | Noticeable — ~4% higher absolute proc chance |
| 7 | 1.48 | Fight is getting serious |
| 10 | 1.72 | Drawn-out battle — enemies press advantage |
| 15 | 2.12 | Very dangerous |
| 20+ | 2.50 | Capped — ~2.5× base chance |

At the cap (round 20+), a Fire enemy with 12% base would have a 30% elemental proc chance. Combined with its racial proc, this makes very long fights increasingly lethal.

#### 6.3.3 Level Scaling (`level_factor`)

Higher-level enemies are more proficient with their elemental affinity. A level-1 Spark shouldn't proc Shock as often as a level-20 Thunder Dragon.

```
level_factor = 0.5 + (enemy_level / 40)   # caps at 2.0 (level 60+)
```

| Enemy Level | Factor | Meaning |
|---|---|---|
| 1 | 0.525 | Weak — barely a threat |
| 5 | 0.625 | Low-level zone |
| 10 | 0.75 | Mid-game |
| 20 | 1.00 | Baseline parity |
| 30 | 1.25 | Dangerous |
| 40 | 1.50 | Elite territory |
| 50 | 1.75 | Near cap |
| 60+ | 2.00 | Boss-level elemental mastery |

#### 6.3.4 Combined Example

A **level-25 Fire Elemental** (base fire chance 12%) at **round 6**:

```
round_factor  = 1.0 + (6 - 1) × 0.08 = 1.40
level_factor  = 0.5 + (25 / 40)       = 1.125
P(proc)       = 0.12 × 1.40 × 1.125  = 0.189 → ~19%
```

So this mid-game Fire Elemental has roughly a 1-in-5 chance per hit to also apply a Burn on top of its racial Blind (Elemental race). This makes it feel dangerous without being oppressive.

A **level-5 Fire Elemental** at **round 2**:

```
round_factor  = 1.0 + (2 - 1) × 0.08 = 1.08
level_factor  = 0.5 + (5 / 40)        = 0.625
P(proc)       = 0.12 × 1.08 × 0.625  = 0.081 → ~8%
```

Early-game, low-level enemies barely proc their elemental debuff. This is correct — new players shouldn't be overwhelmed.

### 6.4 Selecting Which Elemental Debuff to Apply

An enemy may have multiple elements where `elemental_dmg > 1.0` (e.g., Orc: fire=1.3, dark=1.1, physical=1.3). In this case, the system should pick the **strongest** element (highest `elemental_dmg` value):

```python
def get_elemental_debuff(enemy):
    """Return (debuff_type, base_chance) for enemy's strongest element, or None."""
    dmg_profile = enemy.get("elemental_dmg", {})
    if not dmg_profile:
        return None
    
    # Element → (debuff_type, base_chance) mapping
    ELEMENT_DEBUFF_MAP = {
        "fire":     ("burn",       0.12),
        "water":    ("slow",       0.10),
        "thunder":  ("shock",      0.08),
        "wind":     ("blind",      0.10),
        "earth":    ("weaken",     0.12),
        "light":    ("silence",    0.08),
        "dark":     ("dread",      0.10),
        "physical": ("bleed",      0.15),
        "magical":  ("confusion",  0.08),
    }
    
    # Find the element with the strongest damage affinity (>1.0)
    best_element = None
    best_value = 0.0
    for el, val in dmg_profile.items():
        if val > 1.0 and val > best_value:
            best_value = val
            best_element = el
    
    if best_element is None:
        return None
    
    return ELEMENT_DEBUFF_MAP.get(best_element)
```

**Design decision:** Picking the *strongest* rather than rolling among all elements keeps the system predictable. Players can inspect an enemy's elemental profile (or learn through experience) and know roughly what secondary debuff to expect.

**Alternative (for elite+):** Roll among all elements with `dmg > 1.0`, weighted by their strength. This adds variety but reduces predictability. Recommended for elite-tier enemies only.

### 6.5 Integration into `enemy_attack()`

The elemental debuff check would slot in right after the racial `extra_logic` call, at step 17 of the attack pipeline:

```python
# In enemy_attack(), after extra_logic:
if extra_logic:
    msg = extra_logic(enemy, player, enemy_dmg)
    if msg:
        c_print(msg)

# ── NEW: Elemental Profile Debuff ──
if enemy_dmg > 0:  # Only on successful hits
    elem_result = get_elemental_debuff(enemy)
    if elem_result:
        debuff_type, base_chance = elem_result
        
        # Get round_num from combat context (passed as new parameter)
        round_num = enemy.get("_combat_round", 1)
        enemy_level = enemy.get("level", 1)
        
        # Calculate scaled proc chance
        round_factor = min(2.5, 1.0 + (round_num - 1) * 0.08)
        level_factor = min(2.0, 0.5 + (enemy_level / 40))
        proc_chance = base_chance * round_factor * level_factor
        
        if random.random() < proc_chance:
            # Apply the debuff
            apply_func = DEBUFF_APPLY_MAP[debuff_type]
            result = apply_func(player, ...)  # duration/strength params
            c_print(f"  ✦ The {enemy['name']}'s elemental aura inflicts {debuff_type}!")
```

#### 6.5.1 Passing `round_num` to `enemy_attack()`

Currently `enemy_attack()` signature is:

```python
def enemy_attack(enemy, player, p_con, defending, extra_logic=None,
                 armor_mult=1.0, temp_str_bonus=0, all_enemies=None,
                 actual_player=None):
```

The simplest approach is to **attach `round_num` to the enemy dict** before calling `enemy_attack()` in the combat loop:

```python
# In combat_engine.py, before calling enemy_attack:
enemy["_combat_round"] = round_num
result = enemy_attack(enemy, player, p_con, defending, ...)
```

This avoids changing the function signature while making the round available.

#### 6.5.2 Duration & Strength Parameters

Each elemental debuff needs sensible default duration/strength:

| Debuff | Default Duration | Default Strength | Notes |
|---|---|---|---|
| Burn | 3 turns | Tier from `damage_to_burn_tier(enemy_level // 3 + 1)` | Higher level → higher burn tier (capped at tier 3 for non-boss) |
| Slow | 2 turns | -3 DEX | Standard slow |
| Shock | 3 turns | `max(2, enemy_level // 5)` damage/tick | Scales weakly with level |
| Blind | 2 turns | 25% miss (player) | Standard blind |
| Weaken | 3 turns | `max(1, enemy_level // 10)` STR penalty | Weak scaling |
| Silence | 2 turns | — | Binary effect |
| Dread | 2 turns | — | Binary effect |
| Bleed | 4 turns | `max(2, enemy_level // 4)` damage/tick | Scales with level |
| Confusion | 2 turns | 30% self-hit | Standard confusion |

### 6.6 Interaction with Racial Debuffs

The elemental debuff system is **additive**, not replacement. The order of operations:

```
enemy_attack() hits player
  ├── 1. Racial extra_logic (existing) — e.g., Beast → Bleed at 35%
  └── 2. Elemental profile check (NEW)  — e.g., Fire affinity → Burn at scaled %
```

Both can trigger on the same hit. This is intentional:
- A **Fire-aspected Beast** (e.g., a Hellhound) can inflict both Bleed (racial) and Burn (elemental) in one attack
- A **Fire-aspected Undead** (e.g., a Flame Wraith) can Curse (racial) AND Burn (elemental)
- A purely **Physical Beast** with no strong elemental affinity only procs its racial Bleed — no elemental debuff

This creates natural enemy variety without needing to define new enemy types per combination.

### 6.7 Player Counterplay

Since players can see enemy names (which often hint at element via `ELEMENTAL_KEYWORDS` in `combat/elemental.py`), they can:
1. **Identify threats**: "Flame Hound" = Beast racial (Bleed) + Fire elemental (Burn)
2. **Equip resistance gear**: Fire resist gear reduces fire damage AND the burn proc chance (since proc only triggers on damage > 0)
3. **Prioritize targets**: Kill the Thunder-aspected enemy first to avoid Shock stun procs
4. **Use cleanse items**: Anti-burn salves, curse-removal scrolls counter specific elemental debuffs

### 6.8 Implementation Steps

| Step | Effort | Files Touched |
|---|---|---|
| 1. Define `ELEMENT_DEBUFF_MAP` constant | Small | `combat/enemy_ai.py` (or new `combat/elemental_debuffs.py`) |
| 2. Implement `get_elemental_debuff(enemy)` | Small | Same file |
| 3. Add `_combat_round` passthrough in combat loop | Tiny | `combat/combat_engine.py` (~2 lines) |
| 4. Add elemental proc check in `enemy_attack()` | Medium | `combat/enemy_ai.py` (~30 lines) |
| 5. Add duration/strength lookup per debuff type | Small | Same as step 1-2 |
| 6. Add HUD indicator for elemental aura | Medium | `combat/combat_ui.py` — show element icon next to enemy name |
| 7. Balance pass: tune `BASE` values and scaling caps | Ongoing | Constants in step 1 |

### 6.9 Risks & Mitigations

| Risk | Mitigation |
|---|---|
| **Too many debuffs on player** — double-proccing (racial + elemental) could feel unfair | Cap max active debuffs on player at 3-4; if at cap, elemental proc downgrades to minor direct damage instead |
| **RNG frustration** — low proc chances feel inconsistent | Display elemental aura on HUD so player knows what *could* happen; add a "primed" state after 3 non-proc hits where next hit guarantees proc |
| **Balance with existing superboss mechanics** | Superbosses already use custom AI hooks; elemental debuff system only applies to standard enemies. Bosses can opt in by setting `enemy["use_elemental_debuff"] = True` |
| **Performance** | `get_elemental_debuff()` is O(#elements) = O(9) per enemy attack — negligible |

---

## 7. Recommendations

### Immediate (Low Effort)
1. **Document existing racial debuffs** in enemy YAML definitions for visibility
2. **Add `debuff_icon` field** to enemy HUD display so players can see what debuffs enemies carry
3. **Fix any edge cases** where debuff ticks at wrong time (start vs end of turn)

### Short-Term (Medium Effort)
4. **Add `ai_tier` and `debuff_pool` fields** to enemy data model
5. **Implement weighted debuff selection** for elite enemies
6. **Add self-buffing behavior** for elite+ enemies at HP thresholds
7. **Add dispel capability** for boss-tier enemies to counter player buff stacking

### Long-Term (High Effort)
8. **Full boss AI state machines** with phase transitions
9. **Party threat assessment**: enemies prioritize debuffing the most dangerous party member
10. **Adaptive AI**: enemies "learn" which debuffs the player is vulnerable to
11. **Synergy AI**: enemies coordinate debuffs (e.g., one slows, another applies vulnerable, third does bonus damage vs slowed)

---

## 8. File Reference Map

| Concern | File |
|---|---|
| All status effect functions | `combat/status_effects.py` |
| Enemy attack + racial debuff logic | `combat/enemy_ai.py` |
| Player turn + item debuff logic | `combat/player_actions.py` |
| Skill execution + skill debuffs | `combat/skills.py` |
| Combat round orchestration + tick loop | `combat/combat_engine.py` |
| Weapon elemental traits (on-hit effects) | `combat/elemental_traits.py` |
| Wedding accessory procs | `combat/wedding_specials.py` |
| Superboss weapons (Cutlass, Abyss Fang) | `combat/captain_cutlass.py`, `combat/abyss_fang.py` |
| Tarnished Jade pin system | `combat/tarnished_jade.py` |
| Vileheart Pendant poison proc | `combat/vileheart_venom.py` |
| Enemy definitions (race, stats) | `resources/enemies/` |
| Wonderland floor boss AI | `combat/wl_floor_bosses.py` |
| Pandemonium curses | `pandemonium_curses.py` |
| Wonderland curses | `wonderland_curses.py` |
