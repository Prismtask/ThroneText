# Wonderland Superboss — The Big Bad Wolf (Floor 20)

## Overview

| Attribute | Value |
|---|---|
| **Floor** | 20 |
| **Name** | The Big Bad Wolf |
| **Race** | Beast / Abomination (dual) |
| **Level** | 21 |
| **HP** | High (3 phases) |
| **Phases** | 3 (Grandmother's House → What Big Teeth → Hunter's End) |
| **Minions** | None (solo boss) |
| **Thematic Role** | Mid-dungeon superboss; Red Hood's personal nemesis |
| **Heroine Link** | Red Hood — special dialogue, tactical advantage, killing-blow bonus |
| **Defeat Flag** | `player["wl_boss_defeated_big_bad_wolf"] = True` |

## Combat Module

```
combat/big_bad_wolf.py   →   combat_big_bad_wolf(player)
```

## Thematic Role

The Big Bad Wolf is a predator who has consumed so many stories that he's
become a patchwork of villain archetypes — the wolf from Little Red Riding
Hood, the beast from the Three Little Pigs, the thing that goes bump in
every forest-night story ever told. He is what Red Hood has been hunting
since she fell into Wonderland.

Mary Sue wrote him second. She was older, better at writing monsters.
He's smarter than the Queen — and far more dangerous.

## Opening Narration

```
══════════════════════════════════════════════════════════════
The forest clearing ahead is too quiet. No birds. No wind.
Just a cottage with smoke curling from its chimney — a
cottage that wasn't there when you looked a moment ago.

The door creaks open. An old woman in a nightgown beckons
you inside. But her eyes... her eyes are wrong. They're
yellow. And they don't blink.

"Come in, my dear. Grandmother's been expecting you."

The door slams shut behind you. The walls of the cottage
are made of words. Half-eaten sentences. Chewed-up endings.
══════════════════════════════════════════════════════════════
```

---

## Phase 1: "Grandmother's House" (100% – 70% HP)

The Wolf wears a grandmother's nightgown and cap — a grotesque, ill-fitting
disguise. The cottage interior shifts subtly: furniture rearranges when
you look away.

### Dialogue

> *"What big eyes you have, my dear."*
> *"All the better to... appreciate you with."*

### Mechanics

#### Deceptive Calm
The Wolf's attacks during Phase 1 use misdirection. When the UI displays
a target for his attack, there is a **30% chance** the actual target is
different. The game selects a different valid party member at random.

**Red Hood Interaction:** If Red Hood is in the party, she warns after the
first attack:
> *"Don't believe a word he says. Especially the polite ones. He's testing
>  who you'll try to protect."*
This permanently disables the deception for the rest of Phase 1 —
Red Hood's instincts see through the ruse.

#### "What big eyes you have..."
Gaze attack (single-target). Reveals the target's lowest stat to the Wolf
and applies a **permanent -3 debuff** to that stat for the rest of combat.
The Wolf will preferentially target that weakness in subsequent phases.

#### "What big ears you have..."
AoE sonic attack (thunder damage). 35% chance to apply **Silence** (1 turn)
to each party member.

### Phase Transition (70% HP)

```
The disguise tears. Not dramatically — it simply stops being convincing,
the way a story stops working when you notice the plot holes.

The old woman's form unravels like unspooled thread. Beneath it:
fur the colour of ink. Eyes the colour of endings. A jaw that
remembers every meal it has ever taken.

"Fine. Let's skip to the part where I eat you."
```

---

## Phase 2: "What Big Teeth You Have" (70% – 35% HP)

The Wolf reveals his true form. He is massive — fur matted with ink-stains,
teeth that are jagged fragments of torn pages, a tail that sweeps across
the room and erases whatever it touches.

### Mechanics

#### Gnashing Jaws
Primary attack. Heavy single-target physical damage. 40% chance to apply
**Bleed** (8 damage × 3 turns). Bleed from this attack **stacks** — each
application adds a fresh 3-turn duration and the damage values add together.

#### Swallow Whole (every 4 turns)

```
The Wolf's jaw unhinges — wider than should be possible. He lunges.
```

- **Target**: Random party member (player or ally).
- **Effect**: Target is **removed from combat** for 2 full turns. They are
  "inside the Wolf's stomach" — they take 8 damage per turn from digestive
  acid (bypasses CON). They cannot act, be targeted, or be healed.
- **Return**: After 2 turns, they are expelled with 50% of the HP they
  had when swallowed. They gain the **Digested** debuff: -3 all stats for
  3 turns.

**Red Hood Interaction:** When Swallow Whole targets Red Hood:
> *"Oh no you don't!"*
- 50% chance: She **resists entirely** (dodges the swallow).
- If swallowed: She takes **half** acid damage and escapes in **1 turn**
  instead of 2 (she's "hard to digest").

#### Huff & Puff
Wind AoE. Damage starts at 15 and **increases by +5 each use**.
**Destroys one positive buff** per party member (prioritizes non-permanent
buffs first).

### Phase Transition (35% HP)

```
The Wolf staggers. Blood — ink — pools beneath him. He's shrinking.
Not in size, but in narrative weight. The stories he consumed are
leaking out.

"No. NO. I won't go back to being just ONE story. I won't be just
the wolf in the woods that children laugh at!"

He bares his teeth. Every single one of them.
"IF I GO... I'M TAKING THE WHOLE STORY WITH ME!"
```

---

## Phase 3: "The Hunter's End" (35% – 0% HP)

The Wolf is cornered. He fights with nothing left to lose.

### Mechanics

#### Enrage (passive, permanent)
- **+50% damage** on all attacks
- **-20% defense** (incoming damage increased)
- His attacks now show desperation — no more trickery, just raw violence

#### Cornered Beast
The Wolf **attacks twice per turn**. Both attacks are Gnashing Jaws (with
independent bleed checks). If one target dies from the first attack, the
second attack retargets.

#### Final Howl (at 5% HP)

```
The Wolf tips his head back and HOWLS. It's not a sound — it's an erasure.
Every word he ever ate, every story he ever consumed, every ending he
stole — all of it pours out in one terrible, beautiful, dying note.
```

**Effect**: Massive AoE, **40–60 damage** to all party members (player + allies).
Unavoidable. Ignores DEF. This is a "do or die" moment — if you survive,
the Wolf is spent and the next hit kills him.

### Victory

```
The Wolf collapses. The howl still echoes — but it's fading, softening,
until it sounds almost like wind through leaves.

The ink-stains evaporate. The fur recedes. What's left is just a wolf.
A very old, very tired wolf.

"I ate so many stories," he whispers. "I just... forgot my own."

He closes his eyes. The cottage dissolves. You're standing in a
forest clearing. There are birds again. There is wind.
```

**Red Hood kills the Wolf:**
> *Red Hood steps forward. She's shaking — not from fear. From release.*
>
> *"That's for grandmother."*
> *She swings her axe.*
> *"And for every little girl who walked through the woods alone."*
>
> *The axe bites. The Wolf exhales. Stillness.*
>
> *Red Hood gains +1 permanent Strength (character development).*
> *Red Hood becomes a permanent ally.*

## AI Priority

| Phase | Priority |
|---|---|
| Phase 1 | "What big eyes" on highest-stat target → "What big ears" every 3 turns → basic attack on weakest |
| Phase 2 | Swallow Whole on cooldown → Gnashing Jaws on lowest-HP → Huff & Puff every 3 turns |
| Phase 3 | Gnashing Jaws × 2 on lowest-HP → Final Howl at 5% threshold |

## Strategy Notes

- **Phase 1**: Spread damage among party members so the stat debuff doesn't
  cripple your main damage dealer. If Red Hood is in party, she negates the
  deception mechanic entirely.
- **Phase 2**: Swallow Whole is the run-killer. Defend on the turn it's coming
  (it's on a fixed 4-turn cycle; track it). Bring cleanse items for the
  Digest debuff.
- **Phase 3**: The Final Howl at 5% is a hard DPS check. Save burst cooldowns
  and burst from ~10% to skip as much of the enrage phase as possible.
- Bleed from Gnashing Jaws stacks and hurts. Temple cleansing before this
  fight is recommended if you have low CON.

## Drops

| Item | Type | Rarity | Effect |
|---|---|---|---|
| `wolfs_tooth` | Crafting Mat | Legendary | Forge "Fenrir's Bite" dagger or "Grandmother's Vengeance" axe |
| `crimson_hood_scrap` | Accessory Mat | Epic | Craft "Hood of the Huntress" accessory |
| `grandmothers_recipe` | Skill Tome | — | **Only if Red Hood in party.** Teaches her a new skill. |
| Gold: 800–1200 | — | — | — |
| XP: 1500 | — | — | — |

## Enemy YAML Template

```yaml
wl_big_bad_wolf:
  name: The Big Bad Wolf
  race: Storybook
  secondary_race: Abomination
  level: 21
  base_hp: 380
  mods:
    Strength: 5
    Constitution: 3
    Dexterity: 2
    Wisdom: 2
    Learning: 1
    Charisma: 1
  boss: true
  super_boss: true
  dialogue:
    phase1: "Come in, my dear. Grandmother's been expecting you."
    phase2: "Fine. Let's skip to the part where I eat you."
    phase3: "IF I GO... I'M TAKING THE WHOLE STORY WITH ME!"
    death: "I ate so many stories... I just forgot my own."
```

## Shadow Variant (for Mary Sue Phase 3)

```yaml
wl_big_bad_wolf_shadow:
  name: Shadow of the Wolf
  race: Storybook
  secondary_race: Abomination
  level: 21
  base_hp: 133           # 35% of original
  mods:
    Strength: 4
    Constitution: 2
    Dexterity: 2
    Wisdom: 1
    Learning: 1
    Charisma: 1
  boss: false
  super_boss: false
  _shadow: true
  _shadow_of: big_bad_wolf
```

Shadow variant differences:
- Gnashing Jaws (no bleed stacking, single bleed application)
- Narrative Exclusion instead of Swallow Whole (banish for 1 turn, no damage)
- Huff & Puff (fixed 15 damage, no escalation)
- No phase transitions
- Enrages at 15% HP (+40% damage, 2 attacks)
- Must be killed (no dialogue phases)
