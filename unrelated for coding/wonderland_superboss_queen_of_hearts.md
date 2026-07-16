# Wonderland Superboss — Queen of Hearts (Floor 10)

## Overview

| Attribute | Value |
|---|---|
| **Floor** | 10 |
| **Name** | Queen of Hearts |
| **Race** | Storybook / Demon (dual) |
| **Level** | 11 |
| **HP** | Moderate (single phase) |
| **Phases** | 1 phase |
| **Minions** | 2 Card Soldiers (respawn once) |
| **Thematic Role** | Gatekeeper — first test of whether you're a "real" character |
| **Heroine Link** | None |
| **Defeat Flag** | `player["wl_boss_defeated_queen_of_hearts"] = True` |

## Combat Module

```
combat/queen_of_hearts.py   →   combat_queen_of_hearts(player)
```

## Thematic Role

The Queen of Hearts guards the threshold between the whimsical upper floors
(1–6) and the darker depths of the Storybook Dungeon. She is the first villain
Mary Sue ever wrote — brash, loud, and one-dimensional. Defeating her proves
you're not just background flavour text.

## Opening Narration

```
══════════════════════════════════════════════════════════════
You push through a hedge of perfectly manicured roses —
half red, half white. The gardeners flee at your approach,
their paintbrushes clattering to the ground.

At the far end of the garden, on a throne of stacked playing
cards, sits a woman in a gown the colour of fresh-spilled
wine. Two Card Soldiers snap to attention at her sides.

"WHO DARES TRAMPLE MY ROSES?"
══════════════════════════════════════════════════════════════
```

## Combat Design

### Phase: "Off With Their Heads!" (100% – 0% HP)

Single phase with evolving mechanics based on HP thresholds.

#### Card Soldiers (Minions)

- **2 minions** spawn at combat start
- Low HP (~40 each at player level 10), moderate physical ATK
- **Sacrifice**: The Queen can spend her turn to kill one soldier and heal
  herself for 15% of her max HP. Telegraph: *"You! Take the fall for your Queen!"*
- **Respawn**: At 50% Queen HP, both soldiers respawn once.
  Telegraph: *"SUMMON THE RESERVES!"*

#### Royal Decree (every 3 turns)

The Queen rotates through three decrees in fixed order. The current decree
is telegraphed the turn before (she shouts it, then executes next turn):

| Turn | Decree | Effect |
|---|---|---|
| 1 | *"Off with their heads!"* | Heavy single-target physical damage. **Execute**: instantly kills target below 20% HP. Defending reduces threshold to 10%. |
| 2 | *"Painting the roses red!"* | AoE bleed: 3 damage × 3 turns to all party members. Unavoidable unless Defending (halved). |
| 3 | *"All ways are my ways!"* | Self-buff: +30% damage, +15% defense for 2 turns. Does not attack this turn. |

After the third decree, the cycle repeats.

#### Temper Tantrum (at 30% HP)

```
"THIS IS COMPLETELY UNACCEPTABLE!!!"
```

- All current buffs and debuffs on all combatants are **cleared**
- Card Soldiers **respawn** (if they weren't already alive)
- Queen gains **Haste**: 2 actions per turn for 3 turns
- During Haste, she still only decrees once per turn; the second action is
  a basic physical attack on a random target

#### Mercy Rule (at 5% HP)

The fight ends automatically:

```
The Queen throws her crown to the ground. Cards scatter everywhere.

"Enough! ENOUGH! I'll behave! Just... just don't write me out.
 Do you know what happens to characters who get written out?
 They don't even get to be FOOTNOTES!"

She sinks onto her throne, suddenly very small.
```

The player is not required to kill her. Flag is set. Victory.

## AI Priority

1. If a Card Soldier is alive and Queen HP < 40% → **Sacrifice** the soldier
2. Decrees always take priority over basic attacks
3. During Haste, second action targets lowest-HP party member
4. Queen will **not** sacrifice the last soldier if she's above 60% HP

## Strategy Notes

- **Kill soldiers quickly** to prevent sacrifice healing
- **Defend** during "Off with their heads!" if anyone is below 30% HP
- The Temper Tantrum at 30% clears all debuffs on the Queen — don't blow
  your best cooldowns just before this threshold
- Bleed from "Painting the roses red!" can be cleansed at the Temple or
  with consumables — bring cleansing items if you lack healing
- The Queen has low WIS; magic damage is effective

## Drops

| Item | Type | Rarity | Effect |
|---|---|---|---|
| `rose_tinted_crown` | Accessory | Epic | +2 Charisma. **Royal Decree** (active, 1/combat): issue a command buffing one ally (+20% damage, 2 turns). |
| Gold: 400–600 | — | — | — |
| XP: 900 | — | — | — |

### Rose-Tinted Crown Flavour Text

> *"A crown worn by a queen who ruled through volume rather than wisdom.
> It still carries a faint echo of her authority — but only if you
> shout loud enough."*

## Enemy YAML Template

```yaml
# In wonderland.yaml
wl_queen_of_hearts:
  name: Queen of Hearts
  race: Storybook
  secondary_race: Demon
  level: 11
  base_hp: 180
  mods:
    Strength: 3
    Charisma: 5
    Constitution: 2
    Dexterity: 1
    Wisdom: -2
    Learning: -1
  boss: true
  super_boss: true
  dialogue:
    encounter: "WHO DARES TRAMPLE MY ROSES?!"
    enrage: "THIS IS COMPLETELY UNACCEPTABLE!!!"
    surrender: "Enough! I'll behave! Just don't write me out..."

wl_card_soldier:
  name: Card Soldier
  race: Storybook
  secondary_race: Construct
  level: 10
  base_hp: 35
  mods:
    Strength: 2
    Constitution: 3
    Dexterity: 1
    Wisdom: -3
    Learning: -3
    Charisma: -4
  boss: false
  super_boss: false
  minion_only: true   # Only appears as Queen's minion, never random spawn
```

## Shadow Variant (for Mary Sue Phase 2)

See `wonderland_superboss_mary_sue.md` for context.

```yaml
wl_queen_of_hearts_shadow:
  name: Shadow of Hearts
  race: Storybook
  secondary_race: Demon
  level: 11
  base_hp: 72            # 40% of original
  mods:
    Strength: 2
    Charisma: 4
    Constitution: 1
    Dexterity: 1
    Wisdom: -2
    Learning: -1
  boss: false
  super_boss: false
  _shadow: true
  _shadow_of: queen_of_hearts
```

Shadow variant differences:
- No Card Soldiers (1 soldier on Mary Sue's phase, no respawn)
- Royal Decrees only — no Temper Tantrum, no Haste
- No Mercy Rule — must be killed
