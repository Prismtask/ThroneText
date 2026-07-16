# Wonderland Superboss — The Jabberwock (Floor 40)

## Overview

| Attribute | Value |
|---|---|
| **Floor** | 40 |
| **Name** | The Jabberwock |
| **Race** | Dragonkin / Storybook (dual) |
| **Level** | 41 |
| **HP** | Very High (4 phases) |
| **Phases** | 4 (Bewilderbeast → Manxome → Frabjous → Narrative Collapse) |
| **Minions** | Bandersnatch (summoned once in Phase 1) |
| **Core Weakness** | Vorpal — takes 2× damage from Vorpal-tagged weapons/skills |
| **Thematic Role** | Penultimate superboss; Alice's personal nemesis |
| **Heroine Link** | Alice — tactical insight, vorpal damage bonus, closure dialogue |
| **Defeat Flag** | `player["wl_boss_defeated_jabberwock"] = True` |
| **Key Drop** | `frabjous_page` (required to access Floor 50 / Mary Sue) |

## Combat Module

```
combat/jabberwock.py   →   combat_jabberwock(player)
```

## Thematic Role

The Jabberwock is Mary Sue's masterpiece — the monster she wrote when she was
old enough to understand true fear. It doesn't just exist in the story; it
*writes over* stories, consuming narrative threads and replacing them with its
own. It is wrong in a way that defies genre — not just scary, but ontologically
incorrect.

Defeating it is Alice's personal quest. She fell into Wonderland running from
it. Now she's ready to face it — if you'll help her.

## Opening Narration

```
══════════════════════════════════════════════════════════════
The tulgey wood closes around you. Trees with bark like
bookbindings. Leaves that rustle in reverse — from brown
to green, from death to birth.

A sound reaches you before it should. Galumphing. A heavy,
lurching gait that arrives at your ears seconds before its
source rounds the corner.

The Jabberwock is hard to look at. Your eyes keep sliding
off — not from fear, but because the thing is written in a
language your brain refuses to parse. It has the body of a
dragon. The wings of a tattered manuscript. Eyes that are
inkwells, dripping with someone else's nightmares.

It opens its jaws. Words spill out — nonsense words, puns
so bad they physically hurt, plot holes that bend the air.

The Jabberwock has noticed you.

'Beware,' it doesn't quite say. 'The jaws that bite...'
══════════════════════════════════════════════════════════════
```

---

## Phase 1: "Bewilderbeast" (100% – 75% HP)

The Jabberwock is barely a physical creature — it's a shape of whirling
confusion and nonsense words that hurt to perceive. Attacks are more
conceptual than physical.

### Mechanics

#### Burble
AoE confusion gas. Targets all party members. 40% chance per target to
inflict **Bewildered** (2 turns):

- **Bewildered**: 50% chance that attacks target a random combatant
  (enemy or ally) instead of the intended target.
- Attacks that miss due to Bewildered deal half damage to the random target.

#### Galumphing Charge
Physical trample on a single target. Moderate damage. Additionally,
**pushes the target to the bottom of the initiative order** —
they act last next round.

#### "The frumious Bandersnatch!" (at 85% HP)

```
The Jabberwock howls — and the howl takes shape. A smaller creature
tears itself free from the Jabberwock's shadow: all angles and fury,
a beast made of adjectives.
```

Summons a **Bandersnatch** minion:
- Low HP (~60), very high dodge (+30%)
- Attacks: Frumious Swipe (moderate damage, can crit)
- The Bandersnatch does not respawn when killed
- While the Bandersnatch is alive, the Jabberwock uses fewer Burble attacks

**Alice Interaction:**
> *"It's speaking in puns. Terrible, terrible puns. That's how it hunts —
>  it confuses you until you don't know which way is forward."*
> Alice gains **+15% dodge** against Burble.

### Phase Transition (75% HP)

```
The Jabberwock roars — and the nonsense condenses. The bewildering
shapes solidify into something you can finally see clearly.

And you wish you couldn't.

It has the body of a dragon. The wings of a tattered manuscript.
Eyes that are inkwells — and they are fixed on you.

The Jabberwock has stopped playing with its food.
```

---

## Phase 2: "Manxome" (75% – 45% HP)

The Jabberwock has solidified. Its form is terrible and unambiguous.
This is the monster Alice has been running from.

### Mechanics

#### Claws That Catch
Dual strike. The Jabberwock attacks **twice per turn**. The first attack
is a standard physical hit. The second attack **ignores 50% of the target's
CON** for damage calculation. Targets can be different or the same.

#### Jaws That Bite
Heavy single-target physical attack. Applies **Vorpal Wound**:

- Vorpal Wound: Bleed variant. **10 damage × 4 turns. Cannot be cleansed**
  by any means (Temple, items, skills). Must run its full duration.
- The wound is telegraphed: *"The jaws that bite, the claws that catch!"*
- The Jabberwock uses this on the same target every 3 turns, refreshing
  the duration each time.

#### Whiffling (every 5 turns)

```
"The Jabberwock begins to whiffle through the tulgey wood..."
```

- Self-buff: **+40% dodge** for 1 turn.
- The Jabberwock does not attack the turn it Whiffles.
- The turn **after** Whiffling: **-30% dodge** (exhaustion).

**Alice Interaction:**
> *"When it whiffles, don't attack — it'll just dance away. Wait. Then
>  strike when it's catching its breath."*
> The player is informed of the -30% dodge window.

### Phase Transition (45% HP)

```
The Jabberwock's wings unfurl — not outward, but upward. They spread
across the arena like pages torn from a book and thrown into a storm.

The ceiling vanishes. Above you: a vortex of ink, paper, and
half-finished sentences. The Jabberwock ascends into it, and the
vortex descends onto you.

"Callooh! Callay!" it chortles. The sound is the opposite of joy.
```

---

## Phase 3: "Frabjous" (45% – 20% HP)

The Jabberwock has merged with its own narrative — the fight is now
taking place inside the story it's writing in real time.

### Mechanics

#### Vorpal Beam (every 3 turns)
**1-turn windup** → massive line-AoE.

**Windup turn:**
```
"The Jabberwock's eyes glow with vorpal light. The air crystallizes..."

⚡ CHARGING: Vorpal Beam — next turn!
```

**Execution turn:** 60–90 thunder damage to all party members.

**Interrupt**: If the party deals **40+ total damage** to the Jabberwock
during the windup turn, the beam is disrupted:
```
"The vorpal light sputters! The Jabberwock shrieks in frustration!"
```
The beam does not fire, and the Jabberwock loses its next attack.

**Alice Interaction:** During windup:
> *"The eyes! Aim for the eyes — that's where it keeps its plot holes!"*
> Alice's attacks deal **+50% damage** during the windup turn.

#### Narrative Rewrite (every 2 turns)
Erases the **last positive buff** applied to any party member. The Jabberwock
is editing the story — if you got stronger last round, that didn't happen.

#### Page Storm (passive, every turn)
At the end of each round, one random party member's skill cooldown is
**increased by +1** as *"their page is torn."* The target and affected
skill are shown:
```
"A page tears from Alice's storybook: 'Drink Me' gains +1 cooldown!"
```

### Phase Transition (20% HP)

```
The Jabberwock screams. The vortex begins to collapse — not upward,
but inward. Pages are flying in reverse, words unscrambling, ink
flowing back into its wounds.

It's dying. And it's taking this chapter with it.
```

---

## Phase 4: "Narrative Collapse" (20% – 0% HP)

The arena is collapsing. The Jabberwock's body is unraveling — ink and
paper and half-formed ideas spilling everywhere. Every round, the
environment deals damage. It's a race to kill before the collapse
kills you.

### Mechanics

#### Death Throes (passive, every turn)
At the start of every round, **all party members take 15 unavoidable
environmental damage**. This is the dungeon collapsing, not the Jabberwock
attacking — it cannot be mitigated.

#### Final Vorpal Strike (at 5% HP)

```
"The Jabberwock gathers every word it has left. Every claw, every
jaw, every burble and galumph. It shapes them into one final
attack — a sentence with no period, no mercy, no ending except yours."
```

- **Target**: Randomly chosen from all party members
- **Damage**: 80–120 physical damage (can be lethal)
- **Counterplay**: If the target **Defends**, they survive with 1 HP
  (the narrative equivalent of "and then they woke up")
- The Jabberwock is then defenseless — the next hit kills it

### Victory

```
The Jabberwock's body dissolves into ink. The vortex calms.

Pages drift down around you like snow. Each one has a single
word on it — the Jabberwock's vocabulary, scattered and spent.

The ink pools on the floor. It spells one word across the stones:

FIN.

Then the word itself evaporates.

Silence. Real silence. The kind that comes after a story ends.
```

**Alice in party:**
> *Alice stands very still. The teacup she's been holding this entire
>  time — you're not sure when she picked it up — has a crack in it.*
>
> *"It's over. It's really over."*
>
> *She reads the vanishing ink on the floor. Her expression flickers.*
>
> *"It says... 'To be continued.'"*
> *She looks at you.*
> *"That's not ominous at all."*
>
> *Alice becomes a permanent ally.*

A **Frabjous Page** drops — this is the key item needed to challenge
Mary Sue at Floor 50.

## AI Priority

| Phase | Priority |
|---|---|
| Phase 1 | Burble every 3 turns → Galumphing Charge on highest-DEX → basic attack → summon Bandersnatch at 85% |
| Phase 2 | Jaws That Bite on cooldown → Claws That Catch → Whiffle on cooldown |
| Phase 3 | Vorpal Beam on cooldown → Narrative Rewrite → basic attack → Page Storm (passive) |
| Phase 4 | Death Throes (passive) → basic attack → Final Vorpal Strike at 5% |

## Strategy Notes

- **Vorpal weapons are key.** If you have the Vorpal Blade (crafted), this
  fight is significantly easier. Without it, bring Alice for her vorpal
  damage bonus during Phase 3 windups.
- **Phase 2 Whiffling**: Do NOT attack during Whiffle turns. Use the turn
  to heal, buff, Defend, or use items. Attack the following turn when the
  Jabberwock has -30% dodge.
- **Phase 3 Vorpal Beam**: This is the hardest DPS check in the fight.
  Save burst cooldowns. Alice's +50% during windup is crucial — always
  have her attack during the beam charge.
- **Phase 4 Death Throes**: 15 damage/turn to all means you have about
  5–6 turns to finish the fight. Prioritize damage over healing here.
- **Final Vorpal Strike**: When the Jabberwock hits 5%, EVERYONE should
  Defend. The target is random and the damage can one-shot an unguarded
  ally. Defending guarantees survival at 1 HP.

## Drops

| Item | Type | Rarity | Effect |
|---|---|---|---|
| `vorpal_blade_fragment` | Crafting Mat | Legendary | Combine with `looking_glass_shard` at Wonderland Black Market to forge the Vorpal Blade |
| `jabberwock_scale` | Accessory Mat | Epic | Craft "Vorpal Ward" accessory (+15% thunder resist, immune to Bewildered) |
| `frabjous_page` | Key Item | — | **Required** to access Floor 50 (Mary Sue). *"A page that writes itself. It reads: 'And then, the author appeared.'"* |
| `curiouser_inscription` | Skill Tome | — | **Only if Alice in party.** Teaches her a new skill. |
| Gold: 1200–1800 | — | — | — |
| XP: 2100 | — | — | — |

## Enemy YAML Template

```yaml
wl_jabberwock:
  name: The Jabberwock
  race: Storybook
  secondary_race: Dragonkin
  level: 41
  base_hp: 580
  mods:
    Strength: 5
    Constitution: 5
    Dexterity: 2
    Wisdom: 3
    Learning: 1
    Charisma: -3
  boss: true
  super_boss: true
  elemental_res:
    thunder: 0.8
    dark: 1.3
    light: 0.6
  dialogue:
    phase1: "Beware... the Jabberwock, my son! The jaws that bite, the claws that catch!"
    phase2: "..."
    phase3: "Callooh! Callay!"
    phase4: "...!"
    death: "...FIN."
```

## Shadow Variant (for Mary Sue Phase 4)

```yaml
wl_jabberwock_shadow:
  name: Shadow Jabberwock
  race: Storybook
  secondary_race: Dragonkin
  level: 41
  base_hp: 174           # 30% of original
  mods:
    Strength: 4
    Constitution: 4
    Dexterity: 2
    Wisdom: 2
    Learning: 1
    Charisma: -3
  boss: false
  super_boss: false
  _shadow: true
  _shadow_of: jabberwock
```

Shadow variant differences:
- Claws That Catch (dual attack, but no 50% CON pierce)
- Jaws That Bite (bleed can be cleansed on shadow version)
- Vorpal Beam (30+ damage to interrupt instead of 40+)
- No Whiffling, no Narrative Rewrite, no Page Storm
- Final Vorpal Strike at 5% (same as original)
- No phase transitions
