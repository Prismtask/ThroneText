# Wonderland Superboss — The Wicked Witch of the West (Floor 30)

## Overview

| Attribute | Value |
|---|---|
| **Floor** | 30 |
| **Name** | The Wicked Witch of the West |
| **Race** | Demon / Storybook (dual) |
| **Level** | 31 |
| **HP** | High (3 phases) |
| **Phases** | 3 (Emerald Flame → Flying Fury → I'm Melting!) |
| **Minions** | Flying Monkeys (summoned in Phase 2) |
| **Core Weakness** | Water — takes **2× damage** from water-element attacks |
| **Thematic Role** | Dorothy's nemesis. The villain Mary Sue wrote when she understood that true evil isn't loud — it's patient, calculating, and green with envy. |
| **Heroine Link** | **Dorothy** — special dialogue, water synergy, permanent unlock on defeat |
| **Defeat Flag** | `player["wl_boss_defeated_wicked_witch"] = True` |

## Combat Module

```
combat/wicked_witch.py   →   combat_wicked_witch(player)
```

## Thematic Role

The Wicked Witch of the West was Mary Sue's third villain. By the time she
wrote this one, she had learned subtlety. The Witch doesn't shout — she
schemes. She doesn't rage — she waits. She's been waiting for Dorothy to
come back for a very long time.

The Witch rules over a quarter of Wonderland's dungeon from her emerald-
tinted fortress. She knows Dorothy is coming. She's been preparing.

## Opening Narration

```
══════════════════════════════════════════════════════════════
The corridor opens into a vast chamber. The walls are green —
not painted, but glowing faintly, as though the stone itself
is sick with envy.

At the far end, silhouetted against an emerald flame, a figure
in black waits. Her hat is impossibly tall. Her skin is the
colour of jealousy. Her eyes are fixed on you — no, past you.

"I smell... Kansas."

The voice is dry as dead leaves. It comes from everywhere.

"The little girl came back. How... predictable. How...
delicious."

She turns. The emerald flame behind her gutters and flares.

"I've had SO long to prepare for this reunion, my pretty.
Let's not rush. Let's... savour it."
══════════════════════════════════════════════════════════════
```

---

## Core Mechanic: Water Weakness

The Witch's demonic/Storybook nature makes her **fatally vulnerable to water**:

- All water-element attacks deal **2× damage**
- Water-element debuffs (soak, drench) last **twice as long**
- If the Witch is hit by water while casting a fire spell, the spell **fizzles**
  and she loses her turn
- In Phase 3, water damage triggers the "I'm melting!" countdown

**Visual feedback:**
```
The Witch recoils! "WATER! FILTHY, HORRID WATER!"
→ 2× damage dealt!
```

### Dorothy's Water Synergy

If Dorothy is in the party, she provides tactical water support:

- **Passive — Kansas Rain**: Once per battle, Dorothy can convert any
  attack into water-element damage. She announces: *"Back in Kansas,
  we called this a twister."*
- Dorothy's `no_place_like_home` heal also applies **Soaked** (water
  debuff) to the Witch for 2 turns — doubling the Witch's water weakness
  duration
- Dorothy is immune to the Witch's Fear effects (*"I've faced worse
  than you in my own backyard."*)

---

## Phase 1: "Emerald Flame" (100% – 65% HP)

The Witch fights methodically from a distance. She's testing you, cataloguing
your weaknesses, preparing her countermeasures.

### Dialogue

> *"Let's see what you're made of, my pretty. Everyone has a melting point."*

### Mechanics

#### Fire Magic Arsenal
The Witch cycles through fire spells. She uses one per turn:

| Spell | Effect |
|---|---|
| **Ember Volley** | 3 small fire hits on random targets. Low damage each (8–12), but applies **Burning** (3 damage × 2 turns) per hit. |
| **Fireball** | Single-target heavy fire damage (30–45). 25% chance to destroy one consumable in the target's inventory ("Your potions! They're boiling!"). |
| **Wall of Flame** | Creates a fire wall. For 2 turns, any party member who attacks the Witch takes 10 fire reflect damage. The Witch does not attack the turn she casts this. |
| **Scrying Smoke** | Non-damaging. The Witch reads one party member's stats and equipment. Next turn, she exploits their lowest resistance. |

#### "How about a little fire, Scarecrow?"
At 85% HP, the Witch targets the party member with the lowest fire resistance:
> *"I've always hated your kind. Let's see if you burn as well as the last one."*
- Massive single-target fire attack (50–70 damage)
- If it kills: *"One down. They always burn."*
- If it doesn't kill: *"Stubborn. Like the Scarecrow. He burned anyway."*

#### Emerald Cackle (every 4 turns)
> *"HeheheheHAHAHAHA!"*
- AoE dark damage (15–25). 40% chance to apply **Fear** (1 turn: target flees
  to back of initiative, cannot act).
- The Witch's cackle echoes — for 1 turn after, all her fire damage is +15%.

**Dorothy Interaction:**
> *"Don't listen to her. She wants you to run. That's when she's most
>  dangerous."*
> Party members near Dorothy gain +25% Fear resistance.

### Phase Transition (65% HP)

```
The Witch stumbles. Her emerald flame gutters. For a moment —
just a moment — she looks afraid.

Then she laughs. It's not a cackle this time. It's cold. Precise.

"You're stronger than I expected. No matter. I didn't come alone."

She raises a gnarled hand. The shadows in the corners of the
chamber begin to writhe. Wings. Dozens of wings.

"FLY, MY PRETTIES! FLY!"
```

---

## Phase 2: "Flying Fury" (65% – 30% HP)

The Witch summons her Flying Monkeys. She takes to the air on her broomstick,
gaining a massive **evasion buff (+40% dodge)** — between the broom's magic
and her erratic flight, she's nearly impossible to pin down. The monkeys
swarm the party while the Witch rains fire from above.

However, hovering is draining. Every 3 turns, she must **land** to recover —
during the landing turn and the turn after, her dodge buff is removed and
she's fully vulnerable. This is your window.

### Dialogue

> *"You want to hurt me? You'll have to catch me first, my pretty!"*

### Mechanics

#### Flying Monkeys (Minions)

- **3 Flying Monkeys** spawn at phase start
- Low HP (~50 each), high dodge (+25% via evasion buff)
- Attack: Dive Bomb — moderate physical damage, 30% chance to steal one
  consumable from the target's inventory
- Monkeys do **not respawn** — but the Witch summons 1 replacement monkey
  every 3 turns while any are dead

#### The Witch (Airborne)

- **Broomstick Evasion**: Permanent +40% dodge buff (`active_buffs`, `type: "evasion"`).
  Combined with her DEX, she hovers near the 50% enemy dodge cap.
- **Landing Cycle**: Every 3 turns, the Witch **lands** to recover her magic.
  The dodge buff is removed for the landing turn AND the following turn
  (2 turns of full vulnerability). She announces this with a distinctive line.
- While airborne, she uses these attacks:

| Attack | Effect |
|---|---|
| **Broomstick Dive** | On landing turns. The Witch swoops down for a physical strike (20–35 damage). Since she's already on the ground, her dodge buff is off for this turn and the next. |
| **Fire From Above** | Fire AoE (20–30). Standard fire magic — dodge applies normally. |
| **"Here, my pretty!"** | The Witch marks one party member. All monkeys prioritize that target. Marked target takes +15% damage from all sources. Lasts 2 turns. |

#### "Seize them!"
Every 3 turns, if fewer than 2 monkeys are alive:
> *"More! I need MORE of you!"*
- Summons 2 Flying Monkeys

**Dorothy Interaction:**
> *"She always sends the monkeys first. She's afraid to get her hands
>  dirty — that's her weakness! When she lands to catch her breath,
>  her magic wavers. That's when you strike."*
> After this hint, the player learns: the Witch's dodge buff drops
> every 3 turns for a 2-turn window. Save burst damage for the landing.

**Implementation notes:**
- Use `enemy.setdefault("active_buffs", []).append({"type": "evasion", "value": 0.40, "remaining": 999, "source": "broomstick_evasion"})` on phase entry
- Track `ctx["wl_witch_landing_timer"]` starting at 3, decrement each enemy turn
- On timer=0: remove the evasion buff, set `ctx["wl_witch_vulnerable"] = 2` (turns remaining)
- On vulnerable>0: decrement each enemy turn. When it reaches 0, re-apply the evasion buff and reset timer to 3.
- The landing/Vulnerable state is checked in the dodge calculation — if `wl_witch_vulnerable > 0`, skip applying the broomstick evasion buff.
- Broomstick Dive only fires on landing turns (when timer hits 0).

### Phase Transition (30% HP)

```
A water strike catches the Witch mid-cackle. She shrieks — not in anger.
In pain. Real, genuine pain.

Her broomstick lurches. She crashes to the ground, robes smoking.
The emerald flame behind her SPUTTERS and DIES.

The Flying Monkeys shriek and scatter. Without their mistress's power,
they're just frightened animals.

The Witch rises slowly. Her hat is askew. Her green skin is... running?
Yes — where the water hit her, her skin is melting like candle wax.

"What have you DONE?! Do you know what water DOES to me?!"

She raises her hands. Black smoke pours from her fingertips — not fire
now, but raw, desperate, dying magic.

"I'LL TAKE YOU ALL WITH ME!"
```

---

## Phase 3: "I'm Melting!" (30% – 0% HP)

The Witch is grounded, wounded, and desperate. Water has breached her
defenses. She's literally melting — but she's never been more dangerous.

### Dialogue

> *"I'm melting! MELTING! But I won't go alone — I'll take the little
>  girl, and her little dog, and YOU, whoever you are!"*

### Mechanics

#### Melting Countdown

The Witch is actively dissolving. Every turn, she loses 3% of her **max HP**
from the melting effect. But her damage output **increases** as she gets lower:

| HP Range | Damage Bonus | Melting HP Loss/Turn |
|---|---|---|
| 30–20% | +20% | 3% |
| 20–10% | +40% | 3% |
| 10–0% | +60% | 3% |

The melting damage is **water-element** and **bypasses all resistances**.

#### Desperate Spellcasting

The Witch attacks **twice per turn** now. She alternates between:

- **Black Smoke** — AoE dark damage (20–35). Applies **Blinding** (50% miss
  chance, 1 turn) to all non-Dorothy targets.
- **Emerald Curse** — Single-target. Applies **Wicked Mark**: target takes
  15% bonus damage and cannot be healed for 2 turns.
- **Death Throes** — At 5% HP, a final room-wide fire AoE: 50–70 damage to
  ALL combatants (including herself — she's past caring).

#### Water Finisher

If the Witch is brought below 5% HP by a **water-element attack**:

> *"NO! Not water! NOT WAAAAATER—"*
>
> *The Witch dissolves into a puddle of green smoke and black fabric.
> Her hat floats for a moment, then sinks. The emerald flames die.
> All that remains is the hat — and silence.*

The Witch dies dramatically. All debuffs on the party are cleansed.
The fight ends.

If the Witch reaches 0% without a water finisher (e.g., from melting
damage or physical attacks), she simply collapses:
> *"You... haven't... seen the last... of me..."*
> *She crumbles to dust. But somehow, it's less satisfying.*

**Dorothy Killing Blow:**
> *Dorothy steps forward. The ruby slippers glow.*
>
> *"You kept me here for so long. You made me walk your road, fight your
>  battles, fear your shadow. But I'm not afraid anymore."*
>
> *She clicks her heels once. The sound is a thunderclap. Water pours
>  from nowhere — a Kansas rainstorm, summoned by sheer will.*
>
> *"There's no place like home. And you... you don't belong in anyone's."*
>
> *The Witch SCREAMS. The water takes her.*
>
> *Dorothy becomes a permanent ally.*

## Post-Combat

```python
player["wl_boss_defeated_wicked_witch"] = True
```

### Victory Narration

```
The chamber is silent. The emerald glow has faded to a soft,
sickly green that's already dimming to grey. The Witch's hat
lies in a puddle — the only thing that didn't melt.

Dorothy walks to the hat. Picks it up. Turns it over in her hands.

"She was wicked. Absolutely wicked. But... she was also the only
 one who never lied to me. The Wizard pretended to be a god. The
 Witch... she never pretended to be anything but what she was."

She sets the hat down gently — almost respectfully.

"I think that's why she scared me most of all."
```

## AI Priority

| Phase | Priority |
|---|---|
| Phase 1 | Scrying Smoke every 4 turns → "How about a little fire" at 85% → Emerald Cackle on cooldown → cycle Fireball / Ember Volley / Wall of Flame |
| Phase 2 | Broomstick Dive on landing turns → "Here, my pretty!" to mark → Fire From Above otherwise → summon monkeys if < 2 alive |
| Phase 3 | Emerald Curse on healer → Black Smoke on AoE → Death Throes at 5% |

## Strategy Notes

- **Bring water.** This cannot be overstated. Water-element weapons, water
  skills on allies, water consumables (bring extras — the monkeys steal them).
  A party without water damage faces a grueling fight; a party with water
  turns this into a tactical dismantling.
- **Dorothy is a force multiplier.** Her water conversion passive, Fear
  immunity, and Soaked application make the fight significantly easier.
  She's not optional — she's optimal.
- **Phase 2 is a game of patience.** The Witch has +40% dodge while airborne,
  making her extremely hard to hit. Every 3 turns she lands for a 2-turn
  vulnerability window — save your hardest-hitting abilities and water attacks
  for those windows. Don't waste big cooldowns while she's in the air.
- **Phase 3 is a DPS race that works in your favor.** She's melting (3% per
  turn), which means she has ~10 turns max. But her damage ramps hard —
  don't get complacent. Burst her from 10% to 0% to skip the Death Throes.
- **Protect your consumables.** The monkeys steal them, and the Witch's
  Fireball destroys them. Keep spares in inventory. Consider unequipping
  valuable consumables before the fight.

## Drops

| Item | Type | Rarity | Effect |
|---|---|---|---|
| `witch_hat` | Wicked Witch's Hat | Accessory (Epic) | +2 Learning, +1 Wisdom. **Active — "I'm Melting!"** (1/combat): imbue one attack with water element. |
| `broomstick` | Broomstick | Weapon (Epic) | +3 Dexterity, scaling stat: Dexterity. **Passive — "Fly, My Pretty!"**: +10% dodge. |
| `emerald_flame_crystal` | Crafting Mat | Legendary | Forge "Wicked Flame" accessory or "Emerald Curse" weapon. |
| `monkey_wing` | Crafting Mat | Rare | ×3 dropped. Craft "Monkey Paw" consumable (steal one item from an enemy). |
| Gold: 1500–2200 | — | — | — |
| XP: 2400 | — | — | — |

### Wicked Witch's Hat Flavour Text

> *"Still faintly damp. Still faintly wicked. When you put it on,
> you can hear a distant cackle — not threatening, just... amused.
> As though the Witch approves of you wearing her hat. As though
> she'd have done the same."*

---

## Enemy YAML Template

```yaml
wl_wicked_witch:
  name: The Wicked Witch of the West
  race: Storybook
  secondary_race: Demon
  level: 31
  base_hp: 480
  mods:
    Learning: 6
    Wisdom: 4
    Charisma: 3
    Constitution: 2
    Dexterity: 2
    Strength: 1
  boss: true
  super_boss: true
  elemental_res:
    fire: 1.3
    dark: 1.2
    water: 0.5     # 2× damage from water
    light: 0.8
  elemental_dmg:
    fire: 1.4
    dark: 1.2
  dialogue:
    phase1: "I smell... Kansas."
    phase2: "FLY, MY PRETTIES! FLY!"
    phase3: "I'm melting! MELTING!"
    death_water: "NOT WAAAAATER—"
    death_no_water: "You... haven't seen the last... of me..."

wl_flying_monkey:
  name: Flying Monkey
  race: Storybook
  secondary_race: Beast
  level: 40
  base_hp: 50
  mods:
    Dexterity: 5
    Strength: 2
    Constitution: 1
    Wisdom: -2
    Learning: -1
    Charisma: -1
  boss: false
  super_boss: false
  minion_only: true
  dialogue:
    summon: "Fly, my pretties! FLY!"
    steal: "Hehehe! Mine now!"
```

---

## Design Notes

1. **Water weakness is the defining mechanic.** Unlike the Jabberwock's
   Vorpal weakness (which requires a specific crafted weapon), water is
   accessible to everyone — basic water consumables, water-element weapons,
   ally skills. The challenge isn't *having* water; it's *protecting* it
   through Phase 2's monkey thieves.

2. **Dorothy's arc completes here.** The Witch is the reason Dorothy can't
   go home — not because the Witch trapped her, but because Dorothy needs
   to *choose* to face her. The ruby slippers always worked. Dorothy just
   wasn't ready. After this fight, she is.

3. **The Witch is tragic in her own way.** She's the only villain Mary Sue
   wrote who never pretended to be anything else. The Queen blusters about
   authority. The Wolf hides in grandmother's clothing. The Jabberwock is
   chaos incarnate. The Witch? She's just... wicked. Honestly, openly,
   unapologetically wicked. There's something almost admirable about it.

4. **Phase 3 melting is both mechanic and catharsis.** Watching the Witch
   literally dissolve while fighting desperately is the emotional payoff
   for the entire Yellow Brick Road arc. The water finisher is recommended
   but not required — it's the "canon" ending, but a physical kill is
   valid too.
