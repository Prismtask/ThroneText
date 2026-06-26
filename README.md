# Throne of Plaintext

A rich, story-driven text-based dungeon crawler RPG built in Python.

---

## Overview

**Throne of Plaintext** is a deep, classic-style text RPG where you explore dangerous dungeons, manage a growing adventuring party, build relationships with cities, and face increasingly powerful foes — including epic superbosses that change the battlefield with unique mechanics.

You start as a fresh adventurer in the city of **Solmere** and gradually unlock more cities, better gear, houses, monster-girl companions, and powerful abilities. Time passes realistically, affecting difficulty, shop stock, and bounty deadlines. Every choice matters.

---

## Table of Contents

- [How to Play](#how-to-play)
- [Core Game Loop](#core-game-loop)
- [Character Creation](#character-creation)
- [World & Cities](#world--cities)
- [City Services](#city-services)
- [Dungeon System](#dungeon-system)
- [Combat System](#combat-system)
- [Monster Girl & Ally System](#monster-girl--ally-system)
- [Player Housing](#player-housing)
- [Progression & Leveling](#progression--leveling)
- [Travel & Exploration](#travel--exploration)
- [Controls](#controls)
- [Technical Info](#technical-info)

---

## How to Play

1. **Run the game:**
   ```bash
   python main.py
   ```
2. **Create a new character** or load an existing save from multiple slots.
3. You begin in your origin city. Use the city menu to rest, shop, gear up, or take bounties.
4. When ready, **enter the dungeon** and descend floor by floor.
5. Survive, grow stronger, and uncover the secrets of the world.

> **Tip:** You can always `[S]ave` after clearing a floor or from any city menu.

---

## Core Game Loop

1. **Visit Cities** — Rest, shop, train, upgrade your house, take bounties, or buy ships.
2. **Descend into Dungeons** — Clear floors filled with enemies and bosses. Each city has its own themed dungeon with biome-appropriate foes.
3. **Grow Stronger** — Level up, craft/enhance gear, collect rare items, capture monster girls, and recruit allies.
4. **Travel the World** — Journey between cities by land or sea. Random encounters and events keep every trip exciting.

---

## Character Creation

When starting a new game, you will:

- **Choose a Race** (8 options):
  - *Human, Elf, Dwarf, Halfling, Orc, Gnome, Tiefling, Dragonborn*
  - Each race provides attribute modifiers and elemental affinities.

- **Choose a Class** (8 options):
  - *Warrior, Mage, Rogue, Cleric, Ranger, Paladin, Warlock, Barbarian*
  - Each class provides unique stat bonuses, skill trees, and elemental profiles.

- **Allocate 15 Attribute Points** across six attributes:
  - **Strength** — Melee damage, physical attacks
  - **Constitution** — HP and durability
  - **Dexterity** — Speed, initiative, dodge
  - **Wisdom** — Healing, perception
  - **Learning** — Magic damage, skill effectiveness
  - **Charisma** — Prices, discounts, persuasion

- **Name your character** and pick a **save slot** (1+).

---

## World & Cities

The world is divided into **five regions** with **18 unique cities**, each with its own biome, services, dialogue NPCs, and dungeon theme.

### North Region
| City | Biome | Notable Features |
|------|-------|------------------|
| **Stormhold** | Tundra | Fortress city; Barracks, Gift Shop |
| **Thornwall** | Temperate | Garrison town; Barracks training |

### Central Region
| City | Biome | Notable Features |
|------|-------|------------------|
| **Solmere** | Temperate | *Starting hub*; most services including Guild |
| **Greyharbor** | Temperate | River trade city; Trade Hall, Guild |
| **Elderfen** | Swamp | Herbalist hub; stilt-town atmosphere |

### East Region
| City | Biome | Notable Features |
|------|-------|------------------|
| **Irondeep** | Mountain | Dwarven forge; Blacksmith, Barracks, Guild |
| **Skylume** | Magical | Arcane city; Arcane Tower, Gift Shop |
| **Cinderpeak** | Volcanic | Volcanic outpost; Blacksmith, Arcane Tower |
| **Veilholt** | Forest | Elven forest city; Herbalist, Arcane Tower, Guild |

### South Region
| City | Biome | Notable Features |
|------|-------|------------------|
| **Sunreach** | Savanna | Temple city; great radiant temple |
| **Brinewatch** | Coastal | Major western port; Port, Shipyard, Trade Hall |
| **Mirefall** | Swamp | Deep swamp town; Herbalist, Black Market |
| **Ashkara** | Desert | Desert oasis; Black Market, Blacksmith, Guild |
| **Dunemar** | Desert | Trade post; Trade Hall, Black Market |
| **Saltmarsh** | Coastal | Fishing village; minor port |

### Far Reaches / Islands
| City | Biome | Notable Features |
|------|-------|------------------|
| **Tidebreak** | Coastal | Great southern port hub; Port, Shipyard |
| **Coralhaven** | Tropical | Island paradise; Port, Temple, Herbalist, Guild, Gift Shop |
| **Blackwake** | Coastal | *Hidden pirate cove*; sea-only; Black Market |
| **Isle of Glass** | Magical | *Hidden island*; sea-only; Arcane Tower |

> **Sea-only cities** (Coralhaven, Blackwake, Isle of Glass) can only be reached by ship from port cities.

---

## City Services

Each city offers a subset of the following services:

| Service | What It Does |
|---------|-------------|
| **Shop** | Buy consumables, equipment, and supplies. Stock size and prices vary by city. |
| **Inn** | Rest to restore HP. Cost varies by city; free after a certain hour in some places. |
| **Blacksmith** | Enhance equipment (+1 to +N) using gold. Prices scale with enhancement level. Charisma and city favor reduce costs. |
| **Temple** | Receive blessings that buff all attributes for several floors. Cures curses. |
| **Guild** | Pick up **bounties** (hunt contracts). Bounties scale with your level and city **favor**. Higher favor = harder contracts, better rewards. |
| **Trade Hall** | Buy and sell goods, acquire **mounts** that reduce travel time and encounter danger. |
| **Port** | Pay for sea voyages to distant destinations. Requires a port city. |
| **Shipyard** | Purchase ships that unlock certain sea routes permanently. |
| **Barracks** | Train to gain temporary attribute buffs for your next dungeon run. |
| **Herbalist** | Buy natural remedies, antidotes, and unique potions. |
| **Arcane Tower** | Magical services: identify items, imbue gear, arcane training. |
| **Black Market** | Rare and dangerous goods. Sells items not found in normal shops. Higher prices, unique stock. |
| **Gift Shop** | Buy affection gifts for monster girls. |
| **Skill Book** | View and manage your unlocked class skills and their mastery levels. |
| **Your House** | *(Only if you own one in this city)* Manage storage, collect passive income, rest with bed buffs, and house monster girls. |
| **View Stats / Inventory** | Inspect your character, allies, equipment, and manage items. |
| **Travel** | Journey to connected cities by land. |
| **Enter Dungeon** | Descend into that city's themed dungeon. You can choose any unlocked floor. |
| **Save & Return** | Save your game and return to the main menu. |

---

## Dungeon System

Each city has its own **themed dungeon** with biome-appropriate enemies.

### Floor Structure
- Every floor has **10 rooms**: 9 mixed rooms + 1 **boss room** at the end.
- **Non-combat rooms** have a base 10% chance to appear, increasing by 5% for each consecutive combat room. Types include:
  - **Fountain** — Healing and magical buffs
  - **Merchant** — Wandering shop with discounted goods
  - **Stat Check** — Narrative skill challenges (e.g., heal a wounded adventurer, scare off a beast)
  - **Treasure** — Guaranteed rare+ item cache
  5. **Trap** — Avoidable hazard (DEX + WIS check to disarm)

### Boss Floors
- Every **5th floor** is a **true boss fight** with a powerful enemy.
- Every **10th floor** is a **superboss fight** — mechanically unique, multi-phase battles:
  - *Broodmother, Slitcurrent, Sylvana, Ignis, Yinglong, Rientrante*, and more.
  - Superbosses are drawn from a tier pool and shuffled so each one appears once before repeating.

### Progression
- **Per-city floor tracking**: each city remembers its own current floor and maximum cleared floor.
- You can **descend to any unlocked floor** — no need to replay from Floor 1.
- Mid-floor progress is saved: if you quit during a run, you resume in the same room.
- Final non-boss rooms on non-milestone floors feature an **Empowered** enemy (buffed HP and stats).

### Difficulty
- Enemy level scales with floor number (roughly ±6 to +3 range).
- Time of day affects enemy strength and travel danger.
- Biome filtering ensures desert dungeons feature desert races, coastal dungeons feature coastal creatures, etc.

---

## Combat System

Combat is **turn-based** with an **initiative roll** each round.

### Party Size
- **You** (the player) + up to **3 allies**.
- Enemies: up to **5** per encounter.

### Combat HUD
- A fixed-width ASCII box shows the battlefield.
- **Left side**: Your party (player + allies) with HP bars and active buff/debuff tags.
- **Right side**: Enemies with HP and status tags.
- Tags include: `[+STR]`, `[BLD]`, `[PSN]`, `[DRD]`, `[CUR]`, `[SIL]`, etc.
- Monster girls are marked with the `♀` symbol.

### Player Actions
| Action | Description |
|--------|-------------|
| **Attack** | Basic attack. Target any enemy. Weapon scaling stat (STR, DEX, etc.) determines damage. |
| **Skills** | Use unlocked class skills (numbered 1–9). Skills have cooldowns, mastery levels, and scale with your primary attribute + Learning. |
| **Defend** | Reduce incoming damage for the round. |
| **Use Item** | Consume potions, elixirs, or throwables from inventory. |
| **Capture** | Throw a capture net at a weakened monster girl to add her to your house. |
| **Flee** | Attempt to escape. Success chance based on DEX and enemy strength. |
| **Wield the Abyss** | *(Legendary weapon action — only when Abyss Fang is equipped)* |

### Ally Turns
- All allies are **controlled by the player** — you choose their actions each turn.
- Allies can attack, use innate skills, use items, or defend. They cannot capture or wield the Abyss.

### Status Effects
- **Poison** — Damage over time
- **Burn** — Damage over time, reduced by fire resistance
- **Bleed** — Damage over time
- **Curse** — Reduced stats, curable at Temple
- **Dread** — Chance to miss attacks (40%)
- **Silence** — Cannot use skills
- **Blind** — Chance to miss (25%)
- **Slow** — Reduced initiative
- **Blessing** — Attribute buffs from Temple or bed rest

### Elemental System
- Seven elements: **Fire, Water, Thunder, Wind, Earth, Light, Dark**
- Every entity has **elemental resistance** (`<1.0` = resistant, `>1.0` = weak) and **elemental damage** modifiers.
- Race, class, and equipment all contribute to your elemental profile.
- Equipment can have elemental damage bonuses (weapons) or resistances (armor).

---

## Monster Girl & Ally System

### Capture
- During combat, if a **monster girl** enemy is weakened (low HP), the **Capture** action becomes available.
- Use capture nets (bought from shops or found) to attempt capture.
- Success chance increases as HP drops.

### Housing & Affection
- Captured monster girls are stored in your **House** (in whichever city you own one).
- Raise their **affection** by giving gifts (from Gift Shops) or through dungeon victories.
- Each girl has a preferred gift type that grants bonus affection.

### Recruitment
- Once a monster girl's affection reaches **50+**, you can **recruit** her as an active **ally**.
- Allies join your combat party (max 3 active at a time).
- Allies gain EXP from battles, level up, and unlock innate/learnable skills.

### Ally Management
- Allies have their own stats, equipment slots, and HP.
- In combat, you control every ally turn directly.
- You can swap active allies at your House.
- House level determines how many monster girls you can store (2 / 4 / 8).

---

## Player Housing

Buy a house in any city to gain:

| Feature | Benefit |
|---------|---------|
| **Storage** | Store items outside your inventory (10 / 20 / 35 slots). |
| **Passive Income** | Collect daily gold based on house level and city wealth (capped at 10 days). |
| **Rest Buff** | Sleep in your own bed for a blessing that lasts 1–3 floors (+1 / +2 / +3 all attributes). |
| **Monster Girl Housing** | Store captured girls (2 / 4 / 8 capacity). |
| **Faster Rest** | Rest time is shorter than inns (90 / 70 / 50 minutes). |

### House Levels
| Level | Name | Cost | Storage | Income/Day | Girl Cap |
|-------|------|------|---------|------------|----------|
| 1 | Hovel | 300g | 10 | 8g | 2 |
| 2 | Cottage | 600g | 20 | 18g | 4 |
| 3 | Manor | 1,500g | 35 | 35g | 8 |

> Wealthier cities (Skylume, Tidebreak, Isle of Glass) yield higher passive income.

---

## Progression & Leveling

### Leveling Up
- Gain **EXP** from defeating enemies and completing bounties.
- Level up grants:
  - **+HP** (Constitution-based formula)
  - **+1 Attribute Point** to allocate freely
  - **New class skills** unlocked at specific levels
  - **Level cap** starts at 10 and can be raised through ascension mechanics.

### Skill System
- Each class has a unique skill tree defined in YAML data files.
- Skills unlock at specific levels, have **cooldowns** (tracked in rounds), and a **mastery** system.
- Damage formulas combine the skill's primary attribute with **Learning**.
- Passives are always active once unlocked.

### Equipment & Items
- **Rarity tiers**: Common → Uncommon → Rare → Epic → Legendary
- **Weapons** scale with STR, DEX, Learning, Wisdom, or Charisma depending on type.
- **Armor** provides CON and elemental resistances.
- **Accessories** grant unique bonuses.
- **Enhancement**: Blacksmiths can upgrade equipment to +1, +2, etc., increasing stats.
- **Scrolls**: Apply permanent bonus stats to equipment.

### Inventory
- Base inventory size can be expanded with upgrades.
- Manage items from any city menu or after combat rooms.
- Equip, use, discard, or move items to house storage.

---

## Travel & Exploration

### Overland Travel
- From any city, choose **Travel to Another City** to see available **land routes**.
- Travel takes time (30–220 minutes). Longer journeys have higher encounter risk.
- **Mounts** reduce travel time and encounter danger. Bought at Trade Halls.

### Sea Travel
- Only available from **Port** cities (Brinewatch, Saltmarsh, Tidebreak, Coralhaven, Blackwake, Dunemar, Isle of Glass).
- Pay a fee for passage. Some destinations require owning a ship from the **Shipyard**.
- Island cities (Coralhaven, Blackwake, Isle of Glass) are **only reachable by sea**.

### Travel Events
- Random encounters during travel: merchants, ambushes, hazards, storms (at sea), and opportunities.
- Outcomes are influenced by your stats, mounts, and time of day.

---

## Controls

Most interactions use **numbered choices** (1, 2, 3, ...).

### Combat Menu
```
1-9   Use unlocked class skills
a     Attack
b     Defend (brace)
f     Flee
i     Use item
c     Capture (monster girls only, when available)
x     Wield the Abyss (requires Abyss Fang equipped)
```

### General
- `[I]`nventory and `[S]ave` are available after most room victories and from city menus.
- Press **Enter** to confirm most prompts.
- **0** usually means Cancel / Go Back.

---

## Technical Info

- **Language:** Pure Python 3 (no external dependencies required for the core game).
- **Entry Point:** `main.py`
- **Saves:** Stored in the `savefile/` folder. Multiple save slots supported.
- **Data:** Enemy and skill data are loaded from YAML files for easy modding.
- **Modular Design:** Easy to extend with new cities, enemies, items, superbosses, or skills.
- **Save Compatibility:** New fields are automatically added to old save files when loaded.

---

## Welcome to the World of Throne of Plaintext

May your blade stay sharp, your wits sharper, and your house always warm.

**Enjoy the adventure!**
