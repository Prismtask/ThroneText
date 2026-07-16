# Wonderland Superboss — Mary Sue (Floor 50)

## Overview

| Attribute | Value |
|---|---|
| **Floor** | 50 |
| **Name** | Mary Sue — The Author |
| **Race** | Storybook (pure — **no secondary race**) |
| **Level** | 51 |
| **HP** | Highest in the game (5 phases) |
| **Phases** | 5 (Once Upon a Time → Queen's Shadow → Wolf's Shadow → Jabberwock's Shadow → Happily Ever After) |
| **Core Mechanic** | Plot Armor + Shadow Gauntlet (summons shadows of Queen of Hearts, Big Bad Wolf, and Jabberwock) |
| **Thematic Role** | Final superboss & tragic antagonist — the unconscious author of Wonderland |
| **Heroine Link** | All three (Alice, Red Hood, Dorothy) — special dialogue, tactical bonuses, triple-permanent unlock after victory |
| **Defeat Flag** | `player["wl_boss_defeated_mary_sue"] = True` |
| **Prerequisite** | `frabjous_page` (from Jabberwock F40) + `witchs_broom` (from Wicked Witch F30) required to access |

## Combat Module

```
combat/mary_sue.py           →   combat_mary_sue(player)
combat/mary_sue_shadows.py   →   create_shadow_queen_of_hearts()
                                  create_shadow_big_bad_wolf()
                                  create_shadow_jabberwock()
```

## Thematic Role

Mary Sue is the archetype made flesh. She is the unconscious author of
Wonderland — every character, every monster, every whimsical horror was
written by her without her even knowing she was doing it. She is the
"perfect character": flawless, beloved, and utterly alone.

She doesn't see herself as a villain. When the player attacks her, she's
genuinely confused and hurt: *"But I'm the hero of this story!"*

After her defeat, she understands what she is and surrenders her pen,
freeing Wonderland from her unconscious control. She is not killed —
she is liberated.

## Opening Narration

```
══════════════════════════════════════════════════════════════
The final page turns.

You stand in a room that has no walls — only words. Sentences
scrawl themselves across empty space, forming and reforming
like breath on glass. The floor is parchment. The ceiling is
a title page with no title.

At the center of it all, at a desk made of stacked manuscripts,
sits a young woman. She's writing. She doesn't look up.

"You're not supposed to be here," she says, still writing.
"This is the author's study. Characters aren't allowed."

She pauses. Looks at you. Her eyes are ink-blue and slightly
unfocused — the eyes of someone who's been reading too long.

"Oh. You're not one of mine, are you? You're... different.
Unwritten. How interesting."

She sets down her pen. It keeps writing without her.

"Tell me your story. I'd love to read it."
══════════════════════════════════════════════════════════════
```

---

## Core Mechanic: Plot Armor

Mary Sue has **Plot Armor** — a stacking damage reduction shield that
must be stripped before she can be meaningfully damaged.

### Rules

- Starts combat with **5 stacks** of Plot Armor
- Each stack reduces **incoming damage by 12%** (max **60%** at 5 stacks)
- A stack is removed each time Mary Sue takes damage from a **damage type
  she hasn't been hit by yet this phase**:
  - Physical, Fire, Water, Thunder, Wind, Earth, Light, Dark
- The 8 damage types mean you can strip up to 8 stacks — but she caps at 5
- Stacks **regenerate** during Shadow Phases (+1 per turn while a shadow is alive)
- During Phase 5, Plot Armor does NOT regenerate

### Visual Feedback

```
┌─────────────────────────────────────────────┐
│  Mary Sue's Plot Armor                       │
│  ██████████ (5 stacks — 60% DR)              │
│  Damage types used: [none]                   │
│  Next type to strip: any                     │
└─────────────────────────────────────────────┘

→ After Fire damage:
┌─────────────────────────────────────────────┐
│  Mary Sue's Plot Armor                       │
│  ████████░░ (4 stacks — 48% DR)              │
│  Damage types used: [Fire]                   │
│  Next type to strip: Physical, Water, etc.   │
└─────────────────────────────────────────────┘
```

When a stack breaks:
```
"A crack appears in Mary Sue's narrative armor!"
```

### Design Intent

Plot Armor forces build diversity. A player who deals only physical damage
can strip only 1 stack (12% DR removed) — they'll face 48% DR for the
entire fight. A player with a weapon that deals physical + fire, an ally
with thunder skills, and consumables for earth/water damage can strip
all 5 stacks quickly.

---

## Phase 1: "Once Upon a Time" (100% – 80% HP)

Mary Sue is not fighting seriously. She's *curious* about you — you're a
character she didn't write, and that fascinates her.

### Dialogue

> *"You're not from any of my stories. I'd remember. Let me get to know you."*

### Mechanics

#### "Tell me about yourself" (every other turn)
Mary Sue asks a question. This is a non-damaging "attack" that reveals one
of the player's **base stats** to her:

| Question | Stat Learned | Adaptation |
|---|---|---|
| *"Show me your strength."* | Strength | Next physical attack: +30% damage |
| *"How fast are you, really?"* | Dexterity | Next turn: she attacks first regardless of initiative |
| *"Have you ever been truly hurt?"* | Constitution | Next attack: ignores 30% CON |
| *"What do you know about this world?"* | Learning | Next turn: she reduces one skill cooldown (self-buff) |
| *"Do you believe in fate?"* | Wisdom | Next turn: she predicts your action (50% chance to counter with a debuff) |
| *"Are you loved?"* | Charisma | Next turn: she charms one ally (can't target her, 1 turn) |

She can ask up to 3 questions in Phase 1. Once a stat is learned, she
won't ask about it again.

#### Gentle Rebuke
Light single-target damage (~15–25). Mary Sue is pulling her punches.
She's writing a fight scene, not trying to kill you.

#### Author's Favor (at 90% HP, once)

```
"I like the quiet one. They have protagonist energy."

Mary Sue smiles and points her pen at one of your allies.
A faint golden glow surrounds them.
```

- Random ally receives **+3 all stats** for the rest of Phase 1.
- The buff is genuine — but Mary Sue will remove it in Phase 2 as a
  psychological tactic (*"That was just a draft. Let me revise."*).

### Heroine Reactions

**Alice:**
> *"She's... critiquing us. Like we're first drafts. I've had nightmares
>  like this."*

**Red Hood:**
> *"I've met wolves with better manners. At least they're honest about
>  wanting to eat you."*

### Phase Transition (80% HP)

```
Mary Sue frowns at her manuscript. "That's... not right. You're not
supposed to be winning. Let me check my outline."

She flips back a few pages. Her expression darkens.

"Oh. I see the problem. There's no villain yet. Every good story
needs a villain."

She picks up her pen. It glows.

"Let me write one in."
```

---

## Phase 2: "The Villain's Shadow — Queen of Hearts" (80% – 60% HP)

Mary Sue steps back. She is **untargetable** during this phase — she's
"narrating" from outside the scene. A shadow-copy of the **Queen of Hearts**
manifests from her pen.

### Dialogue

> *"The Queen was my first try. I was seven. She's a bit... one-dimensional.
>  But she scared me when I was little, so I kept her around."*

### Shadow Queen of Hearts

See `wonderland_superboss_queen_of_hearts.md` for the full boss. The shadow:

| Aspect | Original | Shadow |
|---|---|---|
| HP | 180 | 72 (40%) |
| Card Soldiers | 2, respawn once | 1, no respawn |
| Royal Decrees | 3, full power | 3, 70% power |
| Temper Tantrum | Yes (at 30%) | No |
| Mercy Rule | Yes (at 5%) | No — must kill |

### Mary Sue During This Phase

- **Untargetable**: Cannot be damaged, debuffed, or targeted
- **Narrating**: At the start of each turn, Mary Sue comments on the fight:
  - *"No, no — the Queen should feint left here. Like this."* → Shadow gains +10% dodge for 1 turn
  - *"More drama! The audience is getting bored!"* → Shadow's next attack deals +20% damage
- **Plot Armor regeneration**: +1 stack per turn

### Phase End

When the shadow is defeated:
- Mary Sue becomes targetable again
- **-2 stacks** of Plot Armor removed (the narrative strain weakens her)

```
Mary Sue: "Oh. You killed her. Again. That's... actually a bit sad.
          She was my first villain. But I suppose you're right —
          she was rather flat. All yelling, no depth."

She flips to a new page.

"Let me try a better one. I've been practicing."
```

---

## Phase 3: "The Hunter's Shadow — Big Bad Wolf" (60% – 40% HP)

Mary Sue writes a shadow-copy of the **Big Bad Wolf**. She is again
untargetable while the shadow fights.

### Dialogue

> *"The Wolf was scarier. I was older when I wrote him — thirteen, maybe.
>  I'd learned that the scariest monsters aren't the ones that roar.
>  They're the ones that smile and say 'grandmother.'"*

### Shadow Big Bad Wolf

See `wonderland_superboss_big_bad_wolf.md`. The shadow:

| Aspect | Original | Shadow |
|---|---|---|
| HP | 380 | 133 (35%) |
| Phases | 3 | 1 (no transitions) |
| Gnashing Jaws | Bleed stacks | Single bleed, no stacking |
| Swallow Whole | 2-turn banish, damage | "Narrative Exclusion": 1-turn banish, no damage |
| Huff & Puff | Escalating damage, buff removal | Fixed 15 damage, no buff removal |
| Enrage | At 35% | At 15% (+40% dmg, 2 attacks) |

### Mary Sue During This Phase

- **Untargetable**
- Plot Armor: **+1 stack per turn**

### Red Hood Interaction

If Red Hood is in the party:

> *"You wrote him. YOU wrote him. Do you have any idea what he DID? What
>  he took from me?"*
>
> Red Hood gains **Righteous Fury**: +30% damage vs the shadow Wolf.

After the shadow is defeated:

> *Red Hood is breathing hard.*
> *"That wasn't the real one. But it felt good anyway."*

### Phase End

- **-3 stacks** of Plot Armor removed

```
Mary Sue: "The Wolf falls. I always knew he would — he was the villain.
          Villains always lose. That's how stories work."

She hesitates.

"...Right?"
```

---

## Phase 4: "The Beast's Shadow — Jabberwock" (40% – 20% HP)

Mary Sue writes her masterpiece — a shadow of the **Jabberwock**.
She is untargetable.

### Dialogue

> *"The Jabberwock... was different. I didn't mean to write it. It just...
>  appeared on the page one night. I was sixteen. I'd been having nightmares.
>  When I woke up, it was there — already written, already real, already
>  hungry."*
>
> *"I've been afraid of it ever since. I think... I think it wrote itself."*

### Shadow Jabberwock

See `wonderland_superboss_jabberwock.md`. The shadow:

| Aspect | Original | Shadow |
|---|---|---|
| HP | 520 | 156 (30%) |
| Phases | 4 | 1 (no transitions) |
| Claws That Catch | Dual attack, 50% CON pierce | Dual attack, no CON pierce |
| Jaws That Bite | Uncleanseable bleed | Cleanseable bleed |
| Vorpal Beam | 40+ damage to interrupt, 60–90 AoE | 30+ to interrupt, 40–60 AoE |
| Whiffling | +40% dodge | Not present |
| Narrative Rewrite | Yes | No |
| Page Storm | Yes | No |
| Final Vorpal Strike | 80–120 damage, Defend saves at 1 HP | Same |

### Mary Sue During This Phase

- **Untargetable**
- Plot Armor: **+1 stack per turn**

### Alice Interaction

> *"You wrote the Jabberwock? You... that thing has haunted my nightmares
>  since I fell into this place! Every shadow. Every pun. Every page that
>  tore itself out of my story — it was YOU?"*
>
> Alice gains **Vorpal Clarity**: all her attacks count as Vorpal vs the
> shadow (2× damage).

After the shadow is defeated:

> *Alice is trembling — not from fear.*
> *"It's a copy. Just a copy. But... that felt real. That felt like closure."*

### Phase End

- **-4 stacks** of Plot Armor removed (if any remain after regeneration)

```
Mary Sue stares at the dissolving shadow. Her pen is shaking.

"Even the Jabberwock... falls. I don't understand. You're not supposed
 to win. The monsters are supposed to be unbeatable — that's what makes
 the heroes brave for trying!"

Her voice cracks.

"If the monsters can die... what's the point of being afraid?"
```

---

## Phase 5: "Happily Ever After" (20% – 0% HP)

All shadows are defeated. Mary Sue stands alone. Her Plot Armor is stripped
(or nearly so). For the first time, she is truly vulnerable — and she is
**furious**.

### Dialogue

```
"NO. This isn't how it goes. I'M the hero. I'M the one who saves the day.
 I'M the one everyone loves. That's how I WROTE it!"

She raises her pen. It's glowing — not the warm glow of creation, but
the cold, desperate light of someone trying to rewrite a story that's
already slipped out of their control.

"If you won't follow the story I wrote... then I'll write a NEW one.
 One where YOU'RE the villain!"
```

### Mechanics

#### Author's Wrath
Mary Sue attacks **3 times per turn**. Each attack is a different
damage type in a fixed cycle:

| Attack # | Name | Type | Effect |
|---|---|---|---|
| 1 | *"Your strength is a cliché!"* | Physical | Standard damage + debuff: -2 STR (1 turn) |
| 2 | *"Your magic is derivative!"* | Random elemental | Fire/Water/Thunder/Wind/Earth, cycles. Applies matching elemental debuff. |
| 3 | *"Your story is TIRED!"* | Dark | Heavy damage, ignores 20% CON |

The cycle is the counterplay: if Plot Armor stacks remain, the variety of
damage types will naturally strip them. But you'll also take heavy damage
in the process.

#### Rewrite (every 4 turns)

```
Mary Sue scribbles furiously. "Let me fix that. There. Much better."
```

**Effects:**
1. All damage Mary Sue took in the **previous round** is **reversed**
   (she heals that amount)
2. One positive buff on a random party member is **converted to a debuff**
   (same magnitude, negative)
3. Mary Sue heals an additional **10% of her max HP**

**Counterplay**: Focus damage on Rewrite turns to minimize the reversal.
If she took 200 damage last round, Rewrite heals 200. If she took 40,
Rewrite heals 40 + 10%.

#### Mary Sue Stu (at 10% HP, once)

```
Mary Sue closes her eyes. The pen floats from her hand. Words stream
from its tip — not sentences, but raw, desperate intent:

"And then... she won. Because she was the hero. Because she deserved to.
Because the author said so. The. End."

⚡ MARY SUE STU: Rewriting the ending...!
```

**1-turn cast.** If it completes:
- Mary Sue heals to **40% HP**
- Regains **3 stacks of Plot Armor**
- The fight essentially resets to mid-Phase 5

**Must be interrupted**: Deal **50+ total damage** in a single turn to
shatter the cast.

```
"The pen wavers! The words shatter — 'hero,' 'deserved,' 'end' — they
fall to the floor like broken glass!"

INTERRUPTED!
```

### Victory

```
Mary Sue falls to her knees. The pen rolls from her fingers. For the
first time, it stops glowing.

"I... I lost? But I'm the... the main character..."

She looks at her hands. They're just hands now. No glow. No plot armor.
No narrative protection. Just a young woman's hands, ink-stained and
shaking.

"...Oh."

The word is small. Fragile. The first honest thing she's ever said.

"I'm not, am I? I never was. I was just... writing myself that way."

She looks up at you. Her eyes aren't narrating anymore. They're just
seeing. Seeing you. Seeing herself. Seeing the world without the
filter of her own story.

"Thank you. For not following the script."

She smiles — a real smile, not a written one — and hands you the pen.

"Here. It's yours now. Write something good with it. Something...
 honest."

The room of words dissolves. The pages settle. Wonderland breathes —
free, for the first time, from its author's unconscious grip.
```

---

## Post-Combat

### Rewards

```python
player["wl_boss_defeated_mary_sue"] = True

# Author's Pen
author_pen = build_item("authors_pen", rarity="legendary")
player["inventory"].append(author_pen)

# Wonderland Key — permanent access, no book needed
wonderland_key = build_item("wonderland_key")
player["inventory"].append(wonderland_key)
```

### The Author's Pen

| Attribute | Value |
|---|---|
| Type | Accessory (Legendary) |
| Slot | Accessory 1 or 2 |
| Passive | **+4 to all stats** while in Wonderland |
| Active | **Rewrite** (5 cd): restore all damage and convert it to the party original hp in the last combat round. Does not revive fallen allies. |
| Flavour | *"A pen that once wrote a world into existence. Now it only writes the truth."* |

### Heroine Resolution

```python
def _mary_sue_victory_heroine_check(player):
    """After Mary Sue is defeated, finalize heroine arcs."""

    # Alice — permanent if Jabberwock was also defeated
    if player.get("wl_boss_defeated_jabberwock"):
        player["wonderland_heroine_alice_permanent"] = True
        # Narration:
        # "Alice closes her eyes. When she opens them, they're clearer."
        # '"The Jabberwock. The Queen. Even the author herself."'
        # '"I think... I think my story is finally my own now."'

    # Red Hood — permanent if Big Bad Wolf was also defeated
    if player.get("wl_boss_defeated_big_bad_wolf"):
        player["wonderland_heroine_redhood_permanent"] = True
        # Narration:
        # "Red Hood sheathes her axe. The crimson hood falls back."
        # '"The Wolf. The one who wrote the Wolf. They're both gone."'
        # '"Grandmother can rest now. So can I."'
    # Dorothy — permanent if Wicked Witch was also defeated
    if player.get("wl_boss_defeated_wicked_witch"):
        player["wonderland_heroine_dorothy_permanent"] = True
        # Narration:
        # "Dorothy looks at the ruby slippers on her feet. They're glowing softly."
        # '"The Witch. The one who wrote her. They can\'t keep me here anymore."'
        # "She clicks her heels once. The sound echoes — not in the room, but somewhere far away."
        # '"Kansas can wait. You still need me here."'
    # If Mary Sue defeated but personal boss wasn't:
    # The heroine acknowledges partial closure. They remain temporary
    # until their personal boss is defeated.
```

### Drops Summary

| Item | Type | Rarity | Notes |
|---|---|---|---|
| `authors_pen` | Accessory | Legendary | See above |
| `mary_sue_teardrop` | Crafting Mat | Legendary | Forge "Flawed Hero" weapon |
| `plot_hole_scrap` | Consumable | Epic | Skip 1 dungeon room |
| `wonderland_key` | Key Item | — | Permanent Wonderland access |
| Gold: 2500–3500 | — | — | — |
| XP: 3000 | — | — | — |

---

## Phase Summary Table

| Phase | HP Range | Mary Sue Status | Shadow Boss | Plot Armor Change | Heroine Interactions |
|---|---|---|---|---|---|
| 1 | 100–80% | Active (curious) | None | Stacks: 5 → strip via damage types | Alice: critique unease. Red Hood: wolf comparison. Dorothy: Wizard parallel. |
| 2 | 80–60% | Untargetable (narrating) | Shadow Queen of Hearts (40% HP) | Regens +1/turn. -2 on shadow defeat. | Alice: "You kept HER?!" Red Hood: "At least my villain had teeth." Dorothy: "At least my witch was honest about being evil." |
| 3 | 60–40% | Untargetable (narrating) | Shadow Big Bad Wolf (35% HP) | Regens +1/turn. -3 on shadow defeat. | Red Hood: Righteous Fury (+30% dmg) |
| 4 | 40–20% | Untargetable (narrating) | Shadow Jabberwock (30% HP) | Regens +1/turn. -4 on shadow defeat. | Alice: Vorpal Clarity (2× vorpal damage) |
| 5 | 20–0% | Active (enraged) | None | No regen. Strip remaining via Author's Wrath. | Resolve all three arcs after victory. |

---

## AI Priority

| Phase | Priority |
|---|---|
| Phase 1 | "Tell me about yourself" on each new stat → Gentle Rebuke → Author's Favor at 90% (once) |
| Phase 2 | Shadow AI (see Queen of Hearts doc) → Mary Sue narration buffs on shadow |
| Phase 3 | Shadow AI (see Big Bad Wolf doc) → Mary Sue narration buffs |
| Phase 4 | Shadow AI (see Jabberwock doc) → Mary Sue narration buffs |
| Phase 5 | Author's Wrath (3-attack cycle) → Rewrite every 4 turns → Mary Sue Stu at 10% |

## Strategy Notes

### Build Requirements

- **Damage type diversity is mandatory.** A pure-physical build faces 48% DR
  (only strips 1 stack). Bring:
  - Weapon with secondary elemental damage
  - Allies with different elemental skills
  - Elemental consumables (fire bombs, thunder scrolls, etc.)
  - At minimum: physical + 2 elemental types to strip 3 stacks (36% → 24% DR)

### Phase-by-Phase

- **Phase 1**: Low-pressure. Use this phase to identify which damage types
  you have available and plan your Plot Armor stripping order.
- **Phases 2–4**: Mary Sue regens Plot Armor while shadows are alive. Kill
  shadows FAST to minimize regen. The shadows are simplified (35–40% HP,
  fewer mechanics) — treat them as DPS races.
- **Phase 5**: The real fight. Rewrite every 4 turns heals her — burst on
  non-Rewrite turns, hold cooldowns on Rewrite turns. Mary Sue Stu at 10%
  is a hard DPS check: save your biggest burst for this moment.
- **Heroines are force multipliers**: Alice's Vorpal Clarity in Phase 4
  and Red Hood's Righteous Fury in Phase 3 significantly speed up the
  shadow phases. Bring both if possible.

### Difficulty

This is the hardest fight in the game. A player at floor 50 should have:
- Level ~38–42
- At least 2 permanent allies (ideally Alice + Red Hood + Dorothy)
- Crafted or legendary equipment in most slots
- Vorpal Blade (optional but highly recommended for Phase 4)

---

## Enemy YAML Template

```yaml
wl_mary_sue:
  name: Mary Sue
  race: Storybook
  # No secondary_race — she is the archetype
  level: 51
  base_hp: 780
  mods:
    Strength: 2
    Constitution: 2
    Dexterity: 3
    Wisdom: 5
    Learning: 5
    Charisma: 8
  boss: true
  super_boss: true
  elemental_res:
    light: 1.3
    dark: 0.6
    thunder: 1.1
  elemental_dmg:
    light: 1.3
    dark: 1.2
  dialogue:
    phase1: "Oh! A new character! Tell me your story!"
    phase2: "Every good story needs a villain."
    phase3: "I was older when I wrote him. He was scarier."
    phase4: "I didn't mean to write it. It wrote itself."
    phase5: "I'LL WRITE A NEW STORY WHERE YOU'RE THE VILLAIN!"
    surrender: "Thank you. For not following the script."
```

## Shadow Boss Factory

```python
# combat/mary_sue_shadows.py

def create_shadow_queen_of_hearts(player):
    """Simplified shadow of the Floor 10 boss."""
    boss = enemy_stats("wl_queen_of_hearts_shadow", player)
    boss["max_hp"] = boss["hp"]
    boss["_shadow_of"] = "queen_of_hearts"
    return boss

def create_shadow_big_bad_wolf(player):
    """Simplified shadow of the Floor 20 boss."""
    boss = enemy_stats("wl_big_bad_wolf_shadow", player)
    boss["max_hp"] = boss["hp"]
    boss["_shadow_of"] = "big_bad_wolf"
    return boss

def create_shadow_jabberwock(player):
    """Simplified shadow of the Floor 30 boss."""
    boss = enemy_stats("wl_jabberwock_shadow", player)
    boss["max_hp"] = boss["hp"]
    boss["_shadow_of"] = "jabberwock"
    return boss
```

---

## Design Notes

1. **Pure Storybook race is deliberate.** Mary Sue is the only enemy in the
   entire game with no secondary race. She IS the Storybook archetype — not
   a creature from a story, but the story itself. This is the thematic
   payoff of the dual-race system.

2. **She is sympathetic.** Unlike Black Silence (tragic warrior), Broodmother
   (primal horror), or Yinglong (cosmic force), Mary Sue is a lonely young
   woman who didn't know she was writing reality. The player should feel a
   twinge of guilt defeating her. The victory is a mercy.

3. **Plot Armor rewards mastery.** A knowledgeable player who understands
   elemental types can strip all 5 stacks quickly. A new player faces a
   brutal 60% DR and must learn on the fly. The mechanic is transparent
   (visual bar, clear feedback) so the learning curve is fair.

4. **Shadow phases as victory lap.** If the player already defeated those
   superbosses, the shadows feel like a "greatest hits" at faster pace —
   familiar but satisfying. If they somehow reached F50 without clearing
   those floors, the shadows are a preview of what they missed.

5. **The pen drop is symbolic.** Mary Sue doesn't die — she surrenders her
   pen. The Author's Pen item is both a powerful reward and a thematic
   statement: the power to write reality is now yours. Use it wisely.
