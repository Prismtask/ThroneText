# 🜁 Pandemonium — Comprehensive Enemy Audit Report

**Generated:** 2026-07-22  
**Total Enemies:** 523 | **Races:** 18 | **Level Range:** 1–57

---

## Executive Summary

523 enemies across 18 races spanning levels 1–57. The level curve is heavily front-loaded: **55% of all enemies are level 1–15**, while levels 41–50 have only **7 non-minion enemies**. Monster Girls (46) and Wonderland enemies (48) are well-represented but concentrated at lower/mid levels. A new **Angel** race is absent and urgently needed for more diversity.

### Key Numbers at a Glance

| Metric | Count |
|---|---|
| Total enemies | 523 |
| Monster Girls | 46 |
| Wonderland (Storybook secondary) | 48 |
| Superbosses | 14 |
| Bosses (non-super) | 76 |
| Minion-only | 18 |
| Races | 18 |

---

## Section 1 — Race Distribution & Level Coverage

| Race | Count | Level Range | High-Level Status |
|---|---|---|---|
| **Beast** | 64 | Lv 1–40 | Well-spread; stops at Lv 40 |
| **Undead** | 45 | Lv 1–44 | Good spread; WL boss at Lv 44 |
| **Abomination** | 39 | Lv 2–48 | Best high-end coverage |
| **Demon** | 38 | Lv 1–42 | Strong mid-high; WL bosses |
| **Construct** | 37 | Lv 1–45 | Minions at Lv 45 for Yinglong |
| **Human** | 34 | Lv 1–42 | WL bosses to Lv 42; tops out |
| **Elemental** | 34 | Lv 1–40 | MG at Lv 40; no 41+ |
| **Shadow** | 34 | Lv 1–29 | **Stops at Lv 29** ⚠️ |
| **Fey** | 33 | Lv 1–46 | WL Snow Queen at Lv 46 |
| **Dragonkin** | 27 | Lv 1–37 | MG at Lv 37; no 38+ |
| **Giant** | 26 | Lv 1–38 | Stops at Lv 38 |
| **Clockwork** | 24 | Lv 1–39 | Boss at Lv 39 |
| **Lizardfolk** | 22 | Lv 1–28 | **Stops at Lv 28** ⚠️ |
| **Vampire** | 21 | Lv 1–27 | **Stops at Lv 27** (WL Bride) ⚠️ |
| **Orc** | 18 | Lv 1–28 | **Stops at Lv 28** ⚠️ |
| **Gnome** | 16 | Lv 1–17 | **Stops at Lv 17** 🔴 Critical |
| **Goblin** | 8 | Lv 1–7 | **Stops at Lv 7** 🔴 Critical |
| **Storybook** | 3 | Lv 41–57 | Three superbosses only |

### Per-Race Level Gaps (2+ consecutive levels with no enemy)

| Race | Gaps |
|---|---|
| **Goblin** | Lv 8–31+ (no enemies above Lv 7) |
| **Gnome** | Lv 18–31+ (no enemies above Lv 17) |
| **Orc** | Lv 29–31+ (no enemies above Lv 28) |
| **Lizardfolk** | Lv 29–31+ (no enemies above Lv 28) |
| **Vampire** | Lv 28–31+ (no enemies above Lv 27) |
| **Shadow** | Lv 30–31+ (no enemies above Lv 29) |
| **Giant** | Lv 39–50+ |
| **Clockwork** | Lv 40–50+ |
| **Dragonkin** | Lv 38–50+ |
| **Elemental** | Lv 41–50+ |
| **Human** | Lv 43–50+ |
| **Beast** | Lv 41–50+ |
| **Demon** | Lv 43–50+ |
| **Fey** | Lv 47–50+ |
| **Construct** | Lv 46–50+ |
| **Undead** | Lv 45–50+ |

### Critical Race Gaps (races with no Lv 30+ enemies)

**Goblin, Gnome, Orc, Lizardfolk, Vampire, Shadow** — these races become completely irrelevant past level 30, limiting biome diversity in dungeons.

---

## Section 2 — Level Distribution & HP Scaling

| Bracket | Enemies | Trash | Bosses | Avg HP (Trash) | MG | WL | Verdict |
|---|---|---|---|---|---|---|---|
| **Lv 1–5** | 91 | 89 | 2 | 17 | 2 | 5 | Healthy over-supply |
| **Lv 6–10** | 104 | 93 | 11 | 39 | 3 | 4 | Dense; good variety |
| **Lv 11–15** | 102 | 85 | 17 | 77 | 8 | 3 | Peak density |
| **Lv 16–20** | 88 | 70 | 18 | 114 | 9 | 5 | Good coverage |
| **Lv 21–25** | 54 | 44 | 10 | 144 | 8 | 3 | Noticeable drop |
| **Lv 26–30** | 32 | 26 | 6 | 189 | 7 | 6 | Sparse but WL fills gaps |
| **Lv 31–35** | 24 | 15 | 9 | 249 | 6 | 5 | Boss-heavy; few trash |
| **Lv 36–40** | 17 | 9 | 8 | 320 | 4 | 2 | Very sparse trash |
| **Lv 41–45** | 7 | 3 | 2 | 369 | 0 | 3 | 🔴 **Critical: only 3 trash** |
| **Lv 46–50** | 3 | 1 | 2 | 370 | 0 | 2 | Near-empty |
| **Lv 51–60** | 1 | 0 | 0 | — | 0 | 0 | Only Mary Sue (Lv 57) |

### HP Scaling Analysis

Current organic HP formula approximates:

| Bracket | Observed Avg HP (Trash) | HP per Level |
|---|---|---|
| Lv 1–10 | ~28 | ~4.2/level |
| Lv 11–20 | ~96 | ~7.5/level |
| Lv 21–30 | ~167 | ~8.6/level |
| Lv 31–40 | ~285 | ~10.2/level |
| Lv 41–50 | ~369 | ~9.8/level |

**Issue:** HP scaling decelerates at Lv 41+ where it should accelerate. Bosses at Lv 40+ have wildly inconsistent HP (range: 120–1300).

### Player-Relevant Level Gaps (for dungeon spawning)

| Bracket | Trash Enemies | Bosses | Total Non-Minion |
|---|---|---|---|
| Lv 1–10 | 182 | 10 | 192 |
| Lv 11–20 | 141 | 38 | 179 |
| Lv 21–30 | 64 | 10 | 74 |
| Lv 31–40 | 25 | 14 | 39 |
| **Lv 41–50** | **3** | **4** | **7** 🔴 |

**Key finding:** Past Lv 35, enemies become almost exclusively bosses, superbosses, and minions. There are **zero ordinary trash enemies** at levels 41–50 across most races. This makes high-level dungeons impossible to populate with diverse random encounters.

---

## Section 3 — Race Resistance Profiles

Values >1.0 = resist (takes less damage), <1.0 = weakness (takes more damage).
Listed in format: `element:multiplier`.

| Race | Resistances (↑ good for enemy) | Weaknesses (↓ bad for enemy) | Design Note |
|---|---|---|---|
| **Human** | — | — | Blank slate; versatile baseline |
| **Goblin** | — | earth 0.8, light 0.9 | Fragile swarmers |
| **Orc** | dark 1.2, fire 1.1, physical 1.2 | magical 0.85 | Anti-mage physical bruiser |
| **Undead** | dark 1.3, physical 1.1 | **light 0.7**, fire 0.8 | Light = hard counter |
| **Beast** | earth 1.2, wind 1.1, physical 1.1 | — | Physically sturdy predator |
| **Demon** | dark 1.3, fire 1.2, magical 1.2 | **light 0.6**, water 0.7, physical 0.85 | Extreme light weakness; holy counter |
| **Construct** | earth 1.2, fire 1.2, physical 1.3 | **thunder 0.7**, magical 0.8 | Thunder = hard counter |
| **Dragonkin** | fire 1.2, thunder 1.2, water 1.1, physical 1.2 | — | Broad elemental tank |
| **Fey** | light 1.2, wind 1.1, magical 1.3 | dark 0.7, physical 0.8 | Magical glass cannon |
| **Elemental** | fire 1.1, water 1.1, thunder 1.1, wind 1.1, earth 1.1, magical 1.2 | physical 0.85 | Omni-elemental; weak to physical |
| **Giant** | earth 1.3, physical 1.2 | thunder 0.8, wind 0.7 | Vulnerable to wind/thunder |
| **Vampire** | dark 1.2, magical 1.1 | **light 0.6**, fire 0.7 | Light/fire = hard counter |
| **Lizardfolk** | water 1.2, earth 1.2, physical 1.1 | fire 0.8 | Cold-blooded; fire weakness |
| **Gnome** | earth 1.2, thunder 1.1, magical 1.1 | — | Magical tinkerer; resilient |
| **Shadow** | dark 1.3, physical 1.1 | **light 0.6** | Extreme light weakness |
| **Clockwork** | fire 1.2, physical 1.2 | **thunder 0.7**, magical 0.8 | Similar profile to Construct |
| **Abomination** | dark 1.2, fire 1.1, physical 1.2 | light 0.8, water 0.9 | Well-rounded horror |
| **Storybook** | light 1.2, thunder 1.1 | dark 0.7 | Fey-adjacent; narrative resilience |

### Enemy-Specific Resistance Overrides

Several enemies override their race resistances with custom `elemental_res` values. Notable examples:

| Enemy | Race | Override | Effect |
|---|---|---|---|
| Rientrante | Human | water 0.7, fire 1.2 | Frost-themed superboss |
| Black Silence | Human | dark 0.7, light 1.3, thunder 1.2 | Dark-vulnerable superboss |
| Chrysalis | Abomination | dark 0.8, fire 0.8, light 1.2, physical 0.9 | Inverts Abomination norm |
| Wicked Witch (WL) | Demon | water 2.0 | Extreme water immunity |
| Jabberwock (WL) | Storybook | light 0.6, dark 1.3, thunder 0.8 | Inverts Storybook norm |
| Temporal Shard: Pyre | Elemental | fire 0.5, water 1.3 | Fire-absorbing minion |
| Temporal Shard: Ruin | Shadow | dark 0.5, light 1.3 | Dark-absorbing minion |

---

## Section 4 — Monster Girl Roster

46 Monster Girls across levels 2–40, spanning 14 of 18 races.

### Full Monster Girl Roster

| Lv | Name | Race | HP | Key Resistances |
|---|---|---|---|---|
| 2 | Goblin Girl | Goblin | 14 | earth 0.8, light 0.9 |
| 5 | Harpy Scout | Beast | 27 | earth 1.2, wind 1.1, physical 1.1 |
| 7 | Alraune Fledger | Fey | 40 | light 1.2, wind 1.1, magical 1.3; dark 0.7, physical 0.8 |
| 8 | Kobold Tinkerer | Dragonkin | 45 | fire 1.2, thunder 1.2, water 1.1, physical 1.2 |
| 9 | Dryad Protector | Fey | 50 | light 1.2, wind 1.1, magical 1.3; dark 0.7, physical 0.8 |
| 10 | Ghost Maid | Shadow | 55 | dark 1.3, physical 1.1; light 0.6 |
| 11 | Centaur Scout | Beast | 64 | earth 1.2, wind 1.1, physical 1.1 |
| 12 | Moth Girl Flutterer | Fey | 65 | light 1.2, wind 1.1, magical 1.3; dark 0.7, physical 0.8 |
| 12 | Slime Girl | Elemental | 88 | all elemental 1.1, magical 1.2; physical 0.85 |
| 13 | Lamia Constrictor | Lizardfolk | 76 | water 1.2, earth 1.2, physical 1.1; fire 0.8 |
| 14 | Lizard Queen | Lizardfolk | 130 | water 1.2, earth 1.2, physical 1.1; fire 0.8 |
| 14 | Mimic Girl | Abomination | 95 | dark 1.2, fire 1.1, physical 1.2; light 0.8, water 0.9 |
| 14 | Umbral Weaver | Shadow | 85 | dark 1.3, physical 1.1; light 0.6 |
| 14 | Winter Fairy | Fey | 70 | light 1.2, wind 1.1, magical 1.3; dark 0.7, physical 0.8 |
| 15 | Holstaur Brawler | Beast | 115 | earth 1.2, wind 1.1, physical 1.1 |
| 16 | Gargoyle Watcher | Construct | 120 | earth 1.2, fire 1.2, physical 1.3; thunder 0.7, magical 0.8 |
| 16 | Vampire Seductress | Vampire | 100 | dark 1.2, magical 1.1; light 0.6, fire 0.7 |
| 17 | Yuki-onna | Elemental | 105 | all elemental 1.1, magical 1.2; physical 0.85 |
| 18 | Amazon Warrior | Human | 125 | none |
| 18 | Banshee Wailer | Undead | 110 | dark 1.3, physical 1.1; light 0.7, fire 0.8 |
| 18 | Neko Ninja | Beast | 92 | earth 1.2, wind 1.1, physical 1.1 |
| 19 | Arachne Weaver | Beast | 110 | earth 1.2, wind 1.1, physical 1.1 |
| 19 | Mummy Princess | Undead | 130 | dark 1.3, physical 1.1; light 0.7, fire 0.8 |
| 20 | Oni Bruiser | Demon | 160 | dark 1.3, fire 1.2, magical 1.2; light 0.6, water 0.7, physical 0.85 |
| 21 | Salamander Dancer | Elemental | 135 | all elemental 1.1, magical 1.2; physical 0.85 |
| 21 | Succubus Seductress | Demon | 120 | dark 1.3, fire 1.2, magical 1.2; light 0.6, water 0.7, physical 0.85 |
| 22 | Dullahan Knight | Undead | 150 | dark 1.3, physical 1.1; light 0.7, fire 0.8 |
| 22 | Kitsune Miko | Beast | 140 | earth 1.2, wind 1.1, physical 1.1 |
| 23 | Siren Empress | Fey | 220 | light 1.2, wind 1.1, magical 1.3; dark 0.7, physical 0.8 |
| 24 | Crimson Countess | Vampire | 230 | dark 1.2, magical 1.1; light 0.6, fire 0.7 |
| 24 | Demon Whip Master | Demon | 170 | dark 1.3, fire 1.2, magical 1.2; light 0.6, water 0.7, physical 0.85 |
| 24 | Minotaur Gladiator | Giant | 185 | earth 1.3, physical 1.2; thunder 0.8, wind 0.7 |
| 25 | Vampire Matriarch | Vampire | 140 | dark 1.2, magical 1.1; light 0.6, fire 0.7 |
| 26 | Centaur Champion | Beast | 195 | earth 1.2, wind 1.1, physical 1.1 |
| 26 | Infernal Empress | Demon | 290 | dark 1.3, fire 1.2, magical 1.2; light 0.6, water 0.7, physical 0.85 |
| 26 | Scylla Wrecker | Abomination | 180 | dark 1.2, fire 1.1, physical 1.2; light 0.8, water 0.9 |
| 28 | Gorgon Petrifier | Lizardfolk | 175 | water 1.2, earth 1.2, physical 1.1; fire 0.8 |
| 30 | Ninetales Fox | Beast | 220 | earth 1.2, wind 1.1, physical 1.1 |
| 31 | Mermaid Siren Queen | Fey | 200 | light 1.2, wind 1.1, magical 1.3; dark 0.7, physical 0.8 |
| 33 | Draconic Valkyrie | Dragonkin | 225 | fire 1.2, thunder 1.2, water 1.1, physical 1.2 |
| 34 | Sphinx Riddler | Beast | 210 | earth 1.2, wind 1.1, physical 1.1 |
| 35 | Lich Queen Avatar | Undead | 195 | dark 1.3, physical 1.1; light 0.7, fire 0.8 |
| 36 | Valkyrie Commander | Human | 260 | none |
| 37 | Dragon Goddess Avatar | Dragonkin | 440 | fire 1.2, thunder 1.2, water 1.1, physical 1.2 |
| 38 | Arachne Brood Queen | Beast | 310 | earth 1.2, wind 1.1, physical 1.1 |
| 40 | Cosmic Slime Empress | Elemental | 480 | all elemental 1.1, magical 1.2; physical 0.85 |

### Monster Girl Gaps

- **Level gaps** (no MG at these levels): 1, 3, 4, 6, 27, 29, 32, 39, 41+
- **Race gaps** (no MG of these races): Orc, Gnome, Goblin (beyond Lv 2), Clockwork, Storybook
- **Highest MG is Lv 40**. No MG above Lv 40.
- **No Angel MG** (race doesn't exist yet).

---

## Section 5 — Wonderland Enemy Roster

48 enemies with `secondary_race: Storybook`, spanning levels 1–48 across 4 dungeon floor ranges.

### Floor 1–8: Alice's Descent

| Lv | Name | Race | HP | Type |
|---|---|---|---|---|
| 1 | Card Soldier (Clubs) | Construct | 12 | Trash |
| 1 | Alice | Fey | 20 | WL Hero |
| 1 | Red Hood | Beast | 24 | WL Hero |
| 1 | Dorothy | Human | 22 | WL Hero |
| 3 | Card Soldier (Spades) | Construct | 22 | Trash |
| 4 | Panicked Rabbit | Beast | 30 | Trash |
| 5 | Dormouse | Beast | 30 | Trash |
| 6 | Grinning Shadow | Shadow | 34 | Trash |
| 7 | Card Knight | Construct | 65 | **Boss** |
| 8 | Dormouse Captain | Beast | 70 | **Boss** |

### Floor 9–16: Neverland's Lost

| Lv | Name | Race | HP | Type |
|---|---|---|---|---|
| 10 | Lost Boy | Human | 55 | Trash |
| 10 | Queen of Hearts | Demon | 235 | WL Boss |
| 10 | Card Soldier | Construct | 175 | WL Trash |
| 10 | Shadow Card Soldier | Construct | 164 | WL Trash |
| 11 | Spiteful Sprite | Fey | 65 | Trash |
| 12 | Peter Pan | Fey | 100 | **Boss** |
| 12 | Tick-Tock Hatchling | Beast | 75 | Trash |
| 13 | Pirate Shade | Undead | 78 | Trash |
| 14 | Tick-Tock Crocodile | Beast | 115 | **Boss** |
| 15 | Pirate Captain James | Undead | 145 | **Boss** |

### Floor 17–24: Yellow Brick Road & Gothic

| Lv | Name | Race | HP | Type |
|---|---|---|---|---|
| 17 | Munchkin Trickster | Gnome | 90 | Trash |
| 18 | Flying Monkey | Beast | 105 | Trash |
| 18 | Rusted Woodsman | Construct | 110 | Trash |
| 18 | Tin Woodsman Captain | Construct | 160 | **Boss** |
| 18 | Cowardly Beast | Beast | 105 | Trash |
| 21 | Mr. Hyde | Abomination | 120 | Trash |
| 22 | Mr. Hyde (Boss) | Abomination | 180 | **Boss** |
| 22 | Stitched Abomination | Abomination | 115 | Trash |
| 24 | Professor Moriarty | Human | 195 | **Boss** |
| 24 | Big Bad Wolf | Beast | 480 | WL Boss |

### Floor 25–32: Wonderland Revisited

| Lv | Name | Race | HP | Type |
|---|---|---|---|---|
| 26 | Bandersnatch | Beast | 140 | Trash |
| 27 | Jubjub Bird | Beast | 145 | Trash |
| 27 | Dracula's Bride | Vampire | 210 | **Boss** |
| 28 | Tweedledum | Human | 150 | Trash |
| 28 | Tweedledee | Human | 150 | Trash |
| 29 | Phantom of the Opera | Shadow | 225 | **Boss** |

### Floor 33–40: The Final Chapter

| Lv | Name | Race | HP | Type |
|---|---|---|---|---|
| 33 | Captain Hook | Human | 142 | **Boss** |
| 33 | Wicked Witch of the West | Demon | 765 | Superboss |
| 35 | The Red Queen | Demon | 270 | **Boss** |
| 35 | Shadow Queen of Hearts | Demon | 432 | WL Boss |
| 36 | The Scarecrow King | Construct | 280 | **Boss** |
| 38 | Bandersnatch Alpha | Beast | 295 | **Boss** |

### Floor 41–48: The Author's Draft

| Lv | Name | Race | HP | Type |
|---|---|---|---|---|
| 42 | The Wizard of Oz | Human | 325 | **Boss** |
| 42 | Shadow Wicked Witch | Demon | 650 | WL Boss |
| 44 | Headless Horseman | Undead | 340 | **Boss** |
| 45 | Shadow Big Bad Wolf | Beast | 754 | WL Boss |
| 46 | The Snow Queen | Fey | 360 | **Boss** |
| 48 | The Nothing | Abomination | 380 | **Boss** |

### Wonderland Analysis

- Strong coverage from Lv 1–48 with logical thematic progression
- **Gap at Lv 39–41**: One-level gap between Bandersnatch Alpha (38) and Wizard of Oz (42)
- Lv 48 is the highest WL enemy — no WL content at Lv 49+ despite superbosses going to Lv 57
- WL superbosses (Jabberwock at Lv 41, Mary Sue at Lv 57) span the highest levels but are standalone

---

## Section 6 — Superboss Inventory

| Lv | Name | Race | HP | Key Resistances |
|---|---|---|---|---|
| 21 | Dream-Devouring Slitcurrent | Abomination | 820 | Race defaults |
| 21 | Ignis, the Melt-Forge Golem | Construct | 840 | Race defaults |
| 21 | Queen of Mirrors Sylvana | Fey | 780 | Race defaults |
| 22 | Captain of the Everlong Ship | Undead | 880 | Race defaults |
| 24 | Broodmother Vileheart | Beast | 770 | Race defaults |
| 25 | Yinglong, Heaven-Banished Dragon | Dragonkin | 872 | Race defaults |
| 25 | Rientrante, the Administrator | Human | 820 | water 0.7, fire 1.2 (custom) |
| 28 | The Black Silence | Human | 920 | dark 0.7, light 1.3, thunder 1.2 (custom) |
| 33 | Wicked Witch of the West | Demon | 765 | water 2.0, fire 1.3 (custom) |
| 40 | Chrysalis, the Entangled One | Abomination | 1300 | dark 0.8, fire 0.8, light 1.2, physical 0.9 (custom) |
| 41 | The Jabberwock | Storybook | 1080 | light 0.6, dark 1.3, thunder 0.8 (custom) |
| 57 | Mary Sue | Storybook | 2030 | light 1.2, dark 0.7, thunder 1.1 (Storybook defaults) |

### Superboss Minions

| Minion | For Superboss | Lv | Race | HP |
|---|---|---|---|---|
| Vileheart Spiderling | Broodmother | 15 | Beast | 185 |
| Vileheart Venomweaver | Broodmother | 17 | Beast | 276 |
| Dream Floatsam | Slitcurrent | 16 | Construct | 55 |
| Frost Shard | Rientrante | 15 | Elemental | 235 |
| Eye of Truth | Rientrante | 20 | Fey | 230 |
| Frozen Arm | Rientrante | 18 | Construct | 200 |
| Seaman Everlong | Everlong Ship | 18 | Undead | 285 |
| Gunner Everlong | Everlong Ship | 19 | Undead | 230 |
| Brawler Everlong | Everlong Ship | 20 | Undead | 280 |
| Boatswain Everlong | Everlong Ship | 19 | Undead | 235 |
| Lookout Everlong | Everlong Ship | 18 | Undead | 230 |
| Heaven Pillar | Yinglong | 45 | Construct | 120 |
| Heaven Pinning Wedge | Yinglong | 45 | Construct | 30 |
| Temporal Shard: Pyre | Chrysalis | 25 | Elemental | 30 |
| Temporal Shard: Pulse | Chrysalis | 25 | Construct | 30 |
| Temporal Shard: Ruin | Chrysalis | 25 | Shadow | 30 |

---

## Section 7 — High-Level Enemy Inventory (Lv 30+)

Full listing of every enemy at level 30 or above, including all tags.

| Lv | Name | Race | HP | Tags |
|---|---|---|---|---|
| 30 | Ancient Wyrm | Beast | 170 | Trash |
| 30 | Lord of Ruin | Demon | 185 | Trash |
| 30 | Dread Lich | Undead | 170 | Trash |
| 30 | Epoch Engine | Clockwork | 185 | Trash |
| 30 | Doom of Worlds | Abomination | 220 | Trash |
| 30 | Elder Wyrm | Dragonkin | 185 | Trash |
| 30 | Ninetales Fox | Beast | 220 | MG |
| 31 | Undead Dread Emperor | Undead | 340 | Boss |
| 31 | Necro Titan | Abomination | 225 | Trash |
| 31 | Mermaid Siren Queen | Fey | 200 | Boss, MG |
| 32 | Sky Leviathan | Beast | 200 | Trash |
| 32 | Supreme Titan | Giant | 240 | Trash |
| 32 | Spectral Dragon | Undead | 190 | Trash |
| 32 | Clockwork Dragon | Clockwork | 290 | Trash |
| 32 | Planar Behemoth | Abomination | 240 | Trash |
| 32 | Primordial Golem | Construct | 210 | Trash |
| 32 | Abyssal Drake | Dragonkin | 180 | Trash |
| 33 | Soul Reaper | Undead | 185 | Trash |
| 33 | Draconic Valkyrie | Dragonkin | 225 | MG |
| 33 | Captain Hook | Human | 142 | Boss, WL |
| 33 | Wicked Witch of the West | Demon | 765 | Superboss, WL |
| 34 | Death Bringer | Undead | 360 | Boss |
| 34 | Genesis Device | Clockwork | 220 | Trash |
| 34 | God Serpent | Abomination | 250 | Trash |
| 34 | Sphinx Riddler | Beast | 210 | MG |
| 35 | Ancient Cyclops | Giant | 310 | Trash |
| 35 | Ancient Chronos Golem | Construct | 410 | Boss |
| 35 | Time Drake | Dragonkin | 240 | Trash |
| 35 | Lich Queen Avatar | Undead | 195 | MG |
| 35 | The Red Queen | Demon | 270 | Boss, WL |
| 35 | Shadow Queen of Hearts | Demon | 432 | WL |
| 36 | Earth Breaker | Beast | 240 | Trash |
| 36 | Elder Titan | Giant | 260 | Trash |
| 36 | Celestial Automaton | Construct | 250 | Trash |
| 36 | Valkyrie Commander | Human | 260 | Boss, MG |
| 36 | The Scarecrow King | Construct | 280 | Boss, WL |
| 37 | Primordial Chaos | Abomination | 290 | Trash |
| 37 | Dragon Goddess Avatar | Dragonkin | 440 | Boss, MG |
| 38 | World Carrier | Giant | 310 | Trash |
| 38 | Eternal Emperor | Undead | 230 | Trash |
| 38 | Cosmic Abomination | Abomination | 270 | Trash |
| 38 | Arachne Brood Queen | Beast | 310 | Boss, MG |
| 38 | Bandersnatch Alpha | Beast | 295 | Boss, WL |
| 39 | Omega Clockwork God | Clockwork | 490 | Boss |
| 40 | Doom of Elders | Abomination | 320 | Trash |
| 40 | Apocalypse Bringer | Abomination | 520 | Boss |
| 40 | Cosmic Slime Empress | Elemental | 480 | Boss, MG |
| 40 | Chrysalis, the Entangled One | Abomination | 1300 | Superboss |
| 41 | The Jabberwock | Storybook | 1080 | Superboss, WL |
| 42 | The Wizard of Oz | Human | 325 | Boss, WL |
| 42 | Shadow Wicked Witch | Demon | 650 | WL |
| 44 | Headless Horseman | Undead | 340 | Boss, WL |
| 45 | Heaven Pillar | Construct | 120 | Minion |
| 45 | Heaven Pinning Wedge | Construct | 30 | Minion |
| 45 | Shadow Big Bad Wolf | Beast | 754 | WL |
| 46 | The Snow Queen | Fey | 360 | Boss, WL |
| 48 | The Nothing | Abomination | 380 | Boss, WL |
| 48 | Shadow Jabberwock | Storybook | 874 | WL |
| 57 | Mary Sue | Storybook | 2030 | Superboss |

---

## Section 8 — Existing Enemy Naming/Level Audit

Before adding new enemies, several existing enemies have names that imply a higher power level than their actual level dictates. These must be fixed first to prevent confusing naming hierarchies when new high-level enemies are introduced.

### 8.1 Naming Conflicts — "Title Inflation at Low Levels"

The principle: **a name should match its level**. "Warlord", "Chieftain", "Whisperer" at levels 2–8 makes it impossible to introduce genuinely intimidating high-level variants without resorting to awkward prefixes like "Mega Warlord" or "Ultra Chieftain".

#### Orc Naming Fixes

| Current ID | Current Name | Lv | Issue | Action | New Name | New Lv |
|---|---|---|---|---|---|---|
| `orc_warlord` | Orc Warlord | 7 | "Warlord" at Lv7 is title inflation | **Rename** to `orc_war_captain` | Orc War Captain | 7 |
| `orc_chieftain` | Orc Chieftain | 8 | "Chieftain" at Lv8 is title inflation | **Rename** to `orc_elite_guard` | Orc Elite Guard | 8 |
| `orc_berserker_chief` | Berserker Chief | 12 | "Chief" is borderline at Lv12 | Keep — acceptable mid-tier title | Berserker Chief | 12 |
| `orc_blood_chieftain` | Blood Chieftain | 14 | Boss-tier; "Chieftain" fits here | Keep — boss status justifies title | Blood Chieftain | 14 |

**Rationale:** By freeing "Warlord" and "Chieftain", new high-level orcs can naturally use:
- **Orc Warlord** → reserved for a new Lv 35+ boss
- **Orc Chieftain** → reserved for a new Lv 33+ trash or boss
- **Orc Warbringer** (existing at Lv13) → fine, "Warbringer" is a distinct title

#### Goblin Naming Fixes

| Current ID | Current Name | Lv | Issue | Action | New Name | New Lv |
|---|---|---|---|---|---|---|
| `goblin_whisperer` | Goblin Whisperer | 2 | "Whisperer" implies mystical spy/assassin | **Rename** to `goblin_chatter` | Goblin Chatter | 2 |

**Rationale:** "Whisperer" is saved for a higher-level stealth goblin. At Lv2, "Chatter" (a fast-talking goblin with Charisma) fits better thematically. New high-level use: **Goblin Shadow Whisperer** at Lv 31.

#### Goblin Level Spread (Existing + Adjusted)

After the rename, the existing goblin level ladder is:

| Lv | ID | Name |
|---|---|---|
| 1 | `goblin_ratcatcher` | Goblin Ratcatcher |
| 1 | `goblin_scout` | Goblin Scout |
| 1 | `goblin_thief` | Goblin Thief |
| 2 | `goblin_archer` | Goblin Archer |
| 2 | `goblin_knifer` | Goblin Knifer |
| 2 | `goblin_shaman` | Goblin Shaman |
| 2 | `goblin_chatter` | Goblin Chatter *(renamed from whisperer)* |
| 2 | `goblin_girl` | Goblin Girl (MG) |

This is **extremely dense at Lv 1–2** with no spread. To alleviate this and create a ladder, shift:

| Current ID | Current Lv | New Lv | Reason |
|---|---|---|---|
| `goblin_shaman` | 2 | 3 | Shamans should outrank basic goblins |
| `goblin_archer` | 2 | 3 | Specialist above basic melee |
| `goblin_knifer` | 2 | 3 | Specialist above basic melee |

This gives: Lv1 (3 trash), Lv2 (2: chatter + MG), Lv3 (3: archer, knifer, shaman) — a better spread.

### 8.2 Valkyrie Naming Conflict

Two existing Monster Girls use "Valkyrie" in their name:

| ID | Name | Lv | Race |
|---|---|---|---|
| `draconic_valkyrie` | Draconic Valkyrie | 33 | Dragonkin |
| `valkyrie_commander` | Valkyrie Commander | 36 | Human |

A third "Valkyrie Ascendant" for the Angel MG would create confusion. **Resolution:** The Angel MG is renamed to avoid the valkyrie namespace entirely. Both existing valkyries remain untouched — they are well-established characters with unique identities (Draconic = dragon hybrid, Commander = human leader).

| Proposed Angel MG Name | Rationale |
|---|---|
| **Seraph Ascendant** | "Seraph" is the highest angelic choir; distinct from Norse "Valkyrie" |

---

## Section 9 — Revised Plan of Action (Expanded to Lv 60)

### Phase 0: Apply Naming Fixes 🔴 Prerequisite

Apply all renames and level shifts from Section 8.1 **before** creating any new enemies. This ensures the naming ladder is clean.

**Files to edit:** `all_enemies.yaml` (rename + level shifts), `monster_girls.yaml` (goblin_girl reference if needed), `resources/skill_book/innate_skills.yaml` (if goblin_whisperer has skills).

**Total changes: 3 renames + 3 level shifts = 6 edits.**

### Phase 1: Angel Race — Baseline Lv 20–55 (More Trash) 🔴 Priority: Highest

**Change from v1 report:** Angel baseline lowered from Lv 30 to Lv 20, with 18 enemies (13 trash, 3 bosses, 1 MG, 1 superboss minion). This provides a full ladder rather than a late-game spike.

#### 9.1.1 Angel Enemy Roster (18 enemies, Lv 20–55)

| ID | Name | Level | HP | Type | Role |
|---|---|---|---|---|---|
| `angel_lightwarden` | Light Warden | 20 | 210 | Trash | Entry angel; tests dark damage |
| `angel_radiant_acolyte` | Radiant Acolyte | 22 | 226 | Trash | Magic-focused caster; low HP |
| `angel_hallowed_lancer` | Hallowed Lancer | 25 | 250 | Trash | Physical-light hybrid melee |
| `angel_celestial_scribe` | Celestial Scribe | 27 | 266 | Trash | Buffer/healer support |
| `angel_divine_sentinel` | Divine Sentinel | 29 | 282 | Trash | High-Con tank guardian |
| `angel_solar_arbiter` | Solar Arbiter | 31 | 329 | Trash | Fast hybrid attacker |
| `angel_seraph_wing` | Seraph Wing | 33 | 347 | Trash | High-Dex flier; evasion focus |
| `angel_heaven_herald` | Heaven's Herald | 35 | 365 | Trash | AoE light caster |
| `angel_throne_warden` | Throne Warden | 37 | 383 | Trash | Elite melee guardian |
| `angel_divine_justicar` | Divine Justicar | 39 | 842 | Boss | Mid-boss gatekeeper |
| `angel_ophanim` | Ophanim | 41 | 480 | Trash | Wheel-of-fire construct-angel hybrid |
| `angel_dominion_lord` | Dominion Lord | 43 | 500 | Trash | Command-tier angel |
| `angel_heavenly_choir` | Heavenly Choir | 45 | 1350 | Boss | Multi-target light/Thunder AoE |
| `angel_virtue_incarnate` | Virtue Incarnate | 47 | 540 | Trash | High-Wis support/caster |
| `angel_power_manifest` | Power Manifest | 49 | 560 | Trash | High-Str melee bruiser |
| `angel_archon_of_truth` | Archon of Truth | 51 | 1530 | Boss | Pre-endgame boss |
| `angel_celestial_dragon` | Celestial Dragon | 53 | 736 | Trash | Dragon-angel hybrid; high all stats |
| `angel_metatron_voice` | Metatron's Voice | 55 | 1650 | Boss | Penultimate angel boss |

Plus one minion and one MG:

| ID | Name | Level | HP | Type |
|---|---|---|---|---|
| `angel_divine_puppet` | Divine Puppet | 30–55 | 80–200 | Minion (spawned by angel bosses) |
| `angel_seraph_ascendant` | Seraph Ascendant | 42 | 490 | MG *(renamed from Valkyrie Ascendant)* |

**Angel MG Note:** Named "Seraph Ascendant" to avoid conflict with existing `draconic_valkyrie` (Dragonkin) and `valkyrie_commander` (Human). Dialogue theme: a seraph who descends from heaven, torn between divine choir and mortal love. Recruitment: dark-element trials to prove the player can face what angels fear most.

#### 9.1.2 Angel Race Definition (unchanged from v1)

```python
"Angel": {
    "mods": {"Wisdom": 3, "Charisma": 3, "Learning": 1, "Constitution": -1},
    "elemental_res": {
        "light": 1.5, "dark": 0.4, "fire": 1.1,
        "magical": 1.2, "physical": 0.85, "thunder": 0.8
    },
    "elemental_dmg": {"light": 1.5, "wind": 1.2, "magical": 1.2}
}
```

#### 9.1.3 Biome Assignment

Add `"Angel"` to:
- `pandemonium` biome (endgame floors)
- `magical` biome (rare celestial incursions)
- New `celestial` biome (heaven-themed dungeon floors, Lv 30+)

**Subtotal: 20 Angel enemies (13 trash + 4 bosses + 1 MG + 1 minion + 1 superboss at Lv 57).**

### Phase 2: Fill Lv 20–40 Trash Gaps for Short Races 🟠 Priority: High

Using the cleaned-up naming ladder from Phase 0, extend races that stop before Lv 30.

#### Goblin Extension (currently stops at Lv 7 → extend to Lv 44)

| ID | Name | Level | HP | Type |
|---|---|---|---|---|
| `goblin_backstabber` | Goblin Backstabber | 20 | 130 | Trash |
| `goblin_bomb_chucker` | Goblin Bomb Chucker | 24 | 154 | Trash |
| `goblin_shadow_whisperer` | Goblin Shadow Whisperer | 31 | 225 | Trash *(uses freed "Whisperer" title)* |
| `goblin_war_chieftain` | Goblin War Chieftain | 37 | 383 | Boss |
| `goblin_demolition_squad` | Goblin Demolition Squad | 40 | 310 | Trash |
| `goblin_horde_captain` | Goblin Horde Captain | 44 | 500 | Boss |

#### Gnome Extension (currently stops at Lv 17 → extend to Lv 47)

| ID | Name | Level | HP | Type |
|---|---|---|---|---|
| `gnome_aether_mechanist` | Aether Mechanist | 23 | 156 | Trash |
| `gnome_chrono_tinker` | Chrono-Tinker | 28 | 182 | Trash |
| `gnome_arcane_artillerist` | Arcane Artillerist | 32 | 226 | Trash |
| `gnome_grand_artificer` | Grand Artificer | 36 | 382 | Boss |
| `gnome_mecha_overlord` | Mecha Overlord | 40 | 310 | Trash |
| `gnome_reality_engineer` | Reality Engineer | 43 | 500 | Trash |
| `gnome_omnissiah_prototype` | Omnissiah Prototype | 47 | 680 | Boss |

#### Orc Extension (currently stops at Lv 28 → extend to Lv 49)

| ID | Name | Level | HP | Type |
|---|---|---|---|---|
| `orc_warlord` | Orc Warlord | 33 | 270 | Boss *(uses freed title)* |
| `orc_chieftain` | Orc Chieftain | 31 | 225 | Trash *(uses freed title)* |
| `orc_bloodfist_champion` | Bloodfist Champion | 37 | 383 | Trash |
| `orc_apocalypse_rager` | Apocalypse Rager | 40 | 310 | Trash |
| `orc_warbringer_elite` | Warbringer Elite | 44 | 500 | Trash |
| `orc_doom_howler` | Doom Howler | 49 | 750 | Boss |

#### Lizardfolk Extension (currently stops at Lv 28 → extend to Lv 50)

| ID | Name | Level | HP | Type |
|---|---|---|---|---|
| `lizardfolk_serpentine_oracle` | Serpentine Oracle | 32 | 226 | Trash |
| `lizardfolk_dread_naga` | Dread Naga | 36 | 274 | Trash |
| `lizardfolk_primordial_serpent` | Primordial Serpent | 40 | 310 | Trash |
| `lizardfolk_scale_tyrant` | Scale Tyrant | 45 | 580 | Boss |
| `lizardfolk_world_fang` | World Fang | 50 | 410 | Trash |

#### Vampire Extension (currently stops at Lv 27 → extend to Lv 52)

| ID | Name | Level | HP | Type |
|---|---|---|---|---|
| `vampire_blood_baron` | Blood Baron | 33 | 270 | Trash |
| `vampire_nosferatu_ancient` | Nosferatu Ancient | 37 | 383 | Trash |
| `vampire_carmilla_handmaiden` | Carmilla's Handmaiden | 40 | 310 | Trash |
| `vampire_blood_sovereign` | Blood Sovereign | 44 | 500 | Boss |
| `vampire_eclipse_countess` | Eclipse Countess | 48 | 540 | Trash |
| `vampire_first_sire` | The First Sire | 52 | 850 | Boss |

#### Shadow Extension (currently stops at Lv 29 → extend to Lv 53)

| ID | Name | Level | HP | Type |
|---|---|---|---|---|
| `shadow_void_stalker` | Void Stalker | 33 | 270 | Trash |
| `shadow_penumbra_wraith` | Penumbra Wraith | 37 | 383 | Trash |
| `shadow_total_eclipse` | Total Eclipse | 40 | 310 | Trash |
| `shadow_umbral_sovereign` | Umbral Sovereign | 44 | 500 | Boss |
| `shadow_abyss_incarnate` | Abyss Incarnate | 48 | 540 | Trash |
| `shadow_primordial_dark` | Primordial Dark | 53 | 850 | Boss |

**Phase 2 Subtotal: 36 new enemies across 6 short races.**

### Phase 3: Populate Lv 41–50 Across Evergreen Races 🟠 Priority: High

Only 3 trash enemies currently exist in this bracket. Add 2 enemies per evergreen race.

| Race | ID | Name | Lv | HP | Type |
|---|---|---|---|---|---|
| Beast | `beast_apex_predator` | Apex Predator | 42 | 490 | Trash |
| Beast | `beast_world_serpent` | World Serpent | 46 | 550 | Trash |
| Undead | `undead_grave_colossus` | Grave Colossus | 41 | 480 | Trash |
| Undead | `undead_soul_harvester` | Soul Harvester | 45 | 540 | Trash |
| Demon | `demon_hellfire_archon` | Hellfire Archon | 41 | 480 | Trash |
| Demon | `demon_abyssal_sovereign` | Abyssal Sovereign | 47 | 580 | Trash |
| Construct | `construct_celestial_sentry` | Celestial Sentry | 43 | 500 | Trash |
| Construct | `construct_starforge_golem` | Starforge Golem | 48 | 620 | Trash |
| Dragonkin | `dragonkin_star_drake` | Star Drake | 44 | 520 | Trash |
| Dragonkin | `dragonkin_void_wyrm` | Void Wyrm | 49 | 630 | Trash |
| Fey | `fey_twilight_courtier` | Twilight Courtier | 42 | 490 | Trash |
| Fey | `fey_verdant_sovereign` | Verdant Sovereign | 46 | 550 | Trash |
| Elemental | `elemental_entropy_orb` | Entropy Orb | 41 | 480 | Trash |
| Elemental | `elemental_singularity` | Singularity | 49 | 630 | Trash |
| Abomination | `abomination_void_horror` | Void Horror | 43 | 500 | Trash |
| Abomination | `abomination_reality_tear` | Reality Tear | 48 | 620 | Trash |

**Phase 3 Subtotal: 16 new enemies.**

### Phase 4: Lv 51–60 Endgame 🟡 Priority: Medium

Currently only Mary Sue at Lv 57. Build out a full endgame ladder.

| ID | Name | Race | Lv | HP | Type |
|---|---|---|---|---|---|
| `dragonkin_eternal_drake` | Eternal Drake | Dragonkin | 51 | 710 | Trash |
| `demon_pit_sovereign` | Pit Sovereign | Demon | 52 | 730 | Trash |
| `undead_lich_eternal` | Lich Eternal | Undead | 53 | 750 | Trash |
| `construct_omega_golem` | Omega Golem | Construct | 54 | 780 | Trash |
| `beast_kaiju_alpha` | Kaiju Alpha | Beast | 55 | 800 | Trash |
| `abomination_end_bringer` | End Bringer | Abomination | 56 | 820 | Trash |
| `fey_timeless_court` | Timeless Court | Fey | 52 | 730 | Trash |
| `elemental_big_crunch` | Big Crunch | Elemental | 54 | 780 | Trash |
| `giant_ragnarok_jotunn` | Ragnarok Jotunn | Giant | 51 | 710 | Trash |
| `clockwork_heat_death` | Heat Death Engine | Clockwork | 53 | 750 | Trash |
| `angel_fallen_morningstar` | Fallen Morningstar | Angel | 57 | 2280 | **Superboss** |
| `dragonkin_apex_of_scales` | Apex of Scales | Dragonkin | 58 | 1800 | Boss |
| `abomination_first_horror` | The First Horror | Abomination | 59 | 1950 | Boss |
| `construct_world_engine` | World Engine | Construct | 60 | 2100 | Boss |
| `demon_lord_of_the_pit` | Lord of the Pit | Demon | 60 | 2200 | **Superboss** |

**Phase 4 Subtotal: 15 new enemies (8 trash + 4 bosses + 2 superbosses).**

### Phase 5: Monster Girl Expansion 🟢 Priority: Ongoing

Fill gaps and add new MGs, respecting the Valkyrie naming fix.

| Lv | ID | Name | Race | HP | Notes |
|---|---|---|---|---|---|
| 23 | `gnome_gear_maiden` | Gear Maiden | Gnome | 160 | First Gnome MG |
| 25 | `orc_war_sister` | War Sister | Orc | 180 | First Orc MG |
| 27 | `shadow_dusk_weaver` | Dusk Weaver | Shadow | 175 | Fills Lv 27 gap |
| 29 | `clockwork_automata_doll` | Automata Doll | Clockwork | 195 | First Clockwork MG |
| 32 | `giant_maiden_of_stone` | Maiden of Stone | Giant | 220 | Fills Lv 32 gap |
| 39 | `dragonkin_flame_heart` | Flame Heart | Dragonkin | 320 | Fills Lv 39 gap |
| 42 | `angel_seraph_ascendant` | Seraph Ascendant | Angel | 490 | *(from Phase 1)* |
| 44 | `fey_star_court_dancer` | Star Court Dancer | Fey | 360 | High-level Fey MG |
| 47 | `demon_infernal_bride` | Infernal Bride | Demon | 420 | High-level Demon MG |
| 50 | `undead_grave_queen` | Grave Queen | Undead | 500 | Caps MG roster at Lv 50 |

**Phase 5 Subtotal: 10 new MGs (8 fillers + 2 from new races).**

### Phase 6: Stat Standardization 🟢 Priority: Ongoing

| Bracket | Trash HP Formula | Boss Multiplier | Superboss HP |
|---|---|---|---|
| Lv 1–10 | $8 + \text{level} \times 6$ | ×2.0 | N/A |
| Lv 11–20 | $20 + \text{level} \times 7$ | ×2.2 | N/A |
| Lv 21–30 | $35 + \text{level} \times 8$ | ×2.5 | $\text{level} \times 30$ |
| Lv 31–40 | $50 + \text{level} \times 9$ | ×2.8 | $\text{level} \times 35$ |
| Lv 41–50 | $70 + \text{level} \times 10$ | ×3.0 | $\text{level} \times 40$ |
| Lv 51–60 | $100 + \text{level} \times 12$ | ×3.5 | $\text{level} \times 45$ |

Stat mods: $\text{level} \times 0.5$ distributed, race mods on top. Lv 41+ should have at least one attribute at 10+.

---

## Section 10 — Summary of Recommended Actions

| Priority | Phase | Action | Changes | New Enemies |
|---|---|---|---|---|
| **P0** | 0 | Apply 6 naming fixes + 3 level shifts to existing enemies | 9 edits to YAML | 0 |
| **P1** | 1 | Add Angel race + 20 enemies (Lv 20–55) + MG | 1 race + 20 YAML entries | 20 |
| **P2** | 2 | Extend Goblin, Gnome, Orc, Lizardfolk, Vampire, Shadow to ~Lv 50 | 36 YAML entries | 36 |
| **P3** | 3 | Add 16 trash enemies for evergreen races at Lv 41–50 | 16 YAML entries | 16 |
| **P4** | 4 | Add 15 enemies at Lv 51–60 including 2 superbosses | 15 YAML entries | 15 |
| **P5** | 5 | Add 10 MGs (fill level/race gaps) | 10 YAML entries + dialogue | 10 |
| **P6** | 6 | Standardize HP scaling (validation pass) | — | — |

| **Total** | | | **~90 YAML entries** | **97 new enemies** |

### Post-Expansion Projected Totals

| Metric | Before | After |
|---|---|---|
| Total enemies | 523 | ~620 |
| Races | 18 | 19 (+Angel) |
| Monster Girls | 46 | 56 |
| Level range | 1–57 | 1–60 |
| Lv 41–50 trash | 3 | ~25 |
| Lv 51–60 enemies | 1 | ~16 |
| Superbosses | 14 | 16 |

---

## Appendix A — All 19 Races at a Glance (Updated)

| # | Race | Count | Lv Range | Light | Dark | Fire | Water | Thunder | Wind | Earth | Physical | Magical |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Human | 34 | 1–42 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| 2 | Goblin | 8→14 | 1–7→44 | 0.9 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 0.8 | 1.0 | 1.0 |
| 3 | Orc | 18→24 | 1–28→49 | 1.0 | 1.2 | 1.1 | 1.0 | 1.0 | 1.0 | 1.0 | 1.2 | 0.85 |
| 4 | Undead | 45→49 | 1–44→53 | **0.7** | 1.3 | 0.8 | 1.0 | 1.0 | 1.0 | 1.0 | 1.1 | 1.0 |
| 5 | Beast | 64→69 | 1–40→55 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.1 | 1.2 | 1.1 | 1.0 |
| 6 | Demon | 38→44 | 1–42→60 | **0.6** | 1.3 | 1.2 | 0.7 | 1.0 | 1.0 | 1.0 | 0.85 | 1.2 |
| 7 | Construct | 37→43 | 1–45→60 | 1.0 | 1.0 | 1.2 | 1.0 | **0.7** | 1.0 | 1.2 | 1.3 | 0.8 |
| 8 | Dragonkin | 27→34 | 1–37→58 | 1.0 | 1.0 | 1.2 | 1.1 | 1.2 | 1.0 | 1.0 | 1.2 | 1.0 |
| 9 | Fey | 33→37 | 1–46→52 | 1.2 | 0.7 | 1.0 | 1.0 | 1.0 | 1.1 | 1.0 | 0.8 | 1.3 |
| 10 | Elemental | 34→38 | 1–40→54 | 1.0 | 1.0 | 1.1 | 1.1 | 1.1 | 1.1 | 1.1 | 0.85 | 1.2 |
| 11 | Giant | 26→28 | 1–38→51 | 1.0 | 1.0 | 1.0 | 1.0 | 0.8 | **0.7** | 1.3 | 1.2 | 1.0 |
| 12 | Vampire | 21→27 | 1–27→52 | **0.6** | 1.2 | 0.7 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.1 |
| 13 | Lizardfolk | 22→27 | 1–28→50 | 1.0 | 1.0 | 0.8 | 1.2 | 1.0 | 1.0 | 1.2 | 1.1 | 1.0 |
| 14 | Gnome | 16→23 | 1–17→47 | 1.0 | 1.0 | 1.0 | 1.0 | 1.1 | 1.0 | 1.2 | 1.0 | 1.1 |
| 15 | Shadow | 34→40 | 1–29→53 | **0.6** | 1.3 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.1 | 1.0 |
| 16 | Clockwork | 24→26 | 1–39→53 | 1.0 | 1.0 | 1.2 | 1.0 | **0.7** | 1.0 | 1.0 | 1.2 | 0.8 |
| 17 | Abomination | 39→46 | 2–48→59 | 0.8 | 1.2 | 1.1 | 0.9 | 1.0 | 1.0 | 1.0 | 1.2 | 1.0 |
| 18 | Storybook | 3 | 41–57 | 1.2 | 0.7 | 1.0 | 1.0 | 1.1 | 1.0 | 1.0 | 1.0 | 1.0 |
| ✨ | **Angel (NEW)** | 20 | 20–57 | **1.5** | **0.4** | 1.1 | 1.0 | 0.8 | 1.0 | 1.0 | 0.85 | 1.2 |

---

## Appendix B — Naming Fix Quick Reference

Apply these edits to `all_enemies.yaml` before creating new enemies:

```
# Line ~3821: orc_warlord → orc_war_captain
  orc_war_captain:
    name: Orc War Captain

# Line ~3835: orc_chieftain → orc_elite_guard  
  orc_elite_guard:
    name: Orc Elite Guard

# Line ~1405: goblin_whisperer → goblin_chatter
  goblin_chatter:
    name: Goblin Chatter

# Level shifts:
# goblin_shaman:   level 2 → level 3
# goblin_archer:   level 2 → level 3
# goblin_knifer:   level 2 → level 3
```

---

## Appendix C — Audit Script

Re-run after changes:

```bash
.\.venv\Scripts\python.exe tests\enemy_audit.py
```

---

*End of Report — Revised 2026-07-22 (Lv 60 expansion + naming audit + Angel baseline Lv 20)*
