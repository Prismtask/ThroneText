# Pandemonium

A rich, story-driven text-based dungeon crawler RPG built in Python with an optional tkinter GUI.

---

## Overview

**Pandemonium** is a deep, classic-style text RPG where you explore dangerous dungeons, manage a growing adventuring party, build relationships with cities, and face increasingly powerful foes — including 14 epic superbosses that change the battlefield with unique mechanics. Beyond the standard world lies the hidden **Wonderland** — a storybook-themed 50-floor dungeon with its own superbosses, heroine quests, and a six-phase final boss. The ultimate endgame challenge awaits in the **Pandemonium** dungeon itself: a 50-floor crystalline hell where every floor curses you with escalating corruption.

You start as a fresh adventurer in the city of **Solmere** and gradually unlock more cities, better gear, a house, monster-girl companions, and powerful abilities. Time passes realistically, affecting travel danger, encounter rates, and inn prices. Every choice matters.

---

## Table of Contents

- [How to Play](#how-to-play)
- [Core Game Loop](#core-game-loop)
- [Character Creation](#character-creation)
- [World & Cities](#world--cities)
- [City Services](#city-services)
- [Dungeon System](#dungeon-system)
- [Superboss System](#superboss-system)
- [Pandemonium Dungeon (Endgame)](#pandemonium-dungeon-endgame)
- [Wonderland System](#wonderland-system)
- [Combat System](#combat-system)
- [Legendary Weapons & Unique Gear](#legendary-weapons--unique-gear)
- [Stat Milestones](#stat-milestones)
- [Monster Girl & Ally System](#monster-girl--ally-system)
- [Engagement & Marriage](#engagement--marriage)
- [Heroine Quest System](#heroine-quest-system)
- [Player Housing](#player-housing)
- [Progression & Leveling](#progression--leveling)
- [Travel & Exploration](#travel--exploration)
- [Your First Adventure](#your-first-adventure)
- [Skill System](#skill-system)
- [Controls](#controls)
- [GUI Mode](#gui-mode)
- [Technical Info](#technical-info)
- [FAQ](#faq)
- [Keybind Quick Reference](#keybind-quick-reference)

---

## Your First Adventure

New to Pandemonium? Here's a step-by-step walkthrough of your first session — from character creation to your first dungeon clear.

### Step 1 — Create Your Character

1. Run `python main.py` (or `Pandemonium.exe`) and choose **New Game**.
2. Pick a **race** and **class**. If you're unsure, **Human Warrior** is the most forgiving combo:
   - Human has no stat penalties and gets +1 to all attributes from Jack of All Trades.
   - Warrior boosts Strength and Constitution — more damage, more HP.
3. Allocate your **15 attribute points**. A balanced spread like `STR 5 / CON 4 / DEX 3 / WIS 2 / LRN 1` works well for a first playthrough.
4. Name your character and pick a **save slot**. The game supports multiple save slots — you can keep separate characters or backup saves.

### Step 2 — Get Your Bearings in Solmere

You begin in **Solmere**, the central hub city. The city menu lists all available services. Here's what to do first:

1. **Open your Inventory** (`[V]iew Stats / Inventory`) — check your starting weapon and armor. Equip anything that isn't already equipped.
2. **Visit the Shop** — spend your starting gold on **3–5 Healing Potions** and optionally a capture net. Don't blow all your gold on equipment yet; dungeon drops will outclass shop gear quickly.
3. **Visit the Guild** (optional) — grab a bounty if one is available. Bounties give bonus gold and city favor for killing specific enemies in that city's dungeon.
4. **Check the Skill Book** — see what skills your class unlocks at Levels 3, 5, 8, 10, and 15 so you know what to look forward to.

### Step 3 — Enter the Dungeon

Choose **Enter Dungeon** from the city menu. You'll start at **Floor 1**.

- Each floor has **10 rooms**. The 10th room is always a **boss**.
- Combat is turn-based. Use `a` to attack, `d` to defend when low on HP, and `u` to use potions.
- After each fight you can `[S]ave` or `[I]nventory` manage your loot.
- **Non-combat rooms** (fountains, merchants, treasure caches) appear occasionally — they're always beneficial.

> 💡 **Tip:** Don't be afraid to flee (`f`) if a fight looks bad. You'll keep your loot and progress up to that room.

### Step 4 — Return & Rest

After clearing Floor 1 (or if your HP gets dangerously low), head back to the city:

1. **Visit the Inn** to rest and fully restore HP.
2. **Save** your game from the city menu.
3. Check your **level progress** — you likely gained a level! Assign your new attribute point.

### What Next?

- **Keep pushing deeper** — Floor 5 has your first true boss. Floor 20 has your first superboss.
- **Travel to new cities** — once you have some levels and gold, head to **Greyharbor** or **Elderfen** to see different biomes and services.
- **Buy a house** — save up 300g and visit a Trade Hall (Greyharbor has one) to buy a Hovel deed. Houses give passive income and storage.
- **Raise your level cap** — once you hit Level 10, clear Floor 10 in a second biome's dungeon, then Ascend at any Guild.
- **Discover Wonderland** — visit Veilholt's Arcane Tower once you're strong enough. A 50-floor storybook dungeon awaits with unique superbosses, heroine companions, and legendary Vorpal weapons.
- **Challenge Pandemonium** — after clearing Floor 40 in 4 biomes, the ultimate 50-floor endgame dungeon unlocks beneath the Isle of Glass.

---

## How to Play

1. **Run the game:** `python main.py` (or run `Pandemonium.exe` if using the built release)
2. **Create a new character** or load an existing save from multiple slots.
3. You begin in your origin city. Use the city menu to rest, shop, gear up, or take bounties.
4. When ready, **enter the dungeon** and descend floor by floor.
5. Survive, grow stronger, and uncover the secrets of the world.

> **Tip:** You can always `[S]ave` after clearing a floor or from any city menu. You can also delete old saves from the main menu.

---

## Core Game Loop

1. **Visit Cities** — Rest, shop, train, upgrade your house, take bounties, or buy ships and mounts.
2. **Descend into Dungeons** — Clear floors filled with enemies and bosses. Each city has its own themed dungeon with biome-appropriate foes.
3. **Grow Stronger** — Level up, enhance gear, collect rare items, capture monster girls, recruit allies, and raise your level cap by clearing biomes.
4. **Travel the World** — Journey between cities by land or sea. Random encounters and events keep every trip exciting.

---

## Character Creation

When starting a new game, you will:

- **Choose a Race** (8 options):
  - *Human, Elf, Dwarf, Halfling, Orc, Gnome, Tiefling, Dragonborn*
  - Each race provides attribute modifiers and elemental affinities.

- **Choose a Class** (8 options):
  - *Warrior, Mage, Rogue, Cleric, Ranger, Paladin, Warlock, Barbarian*
  - Each class provides unique passive skills, active skills, and elemental profiles.

- **Allocate 15 Attribute Points** across six attributes. For every 5 points in a single attribute you unlock a passive milestone bonus:
  - **Strength** — Melee damage, physical attacks, carry weight
  - **Constitution** — HP and durability
  - **Dexterity** — Speed, initiative, dodge
  - **Wisdom** — Healing, perception
  - **Learning** — Magic damage, skill effectiveness
  - **Charisma** — Prices, discounts, persuasion

- **Name your character** and pick a **save slot** (1+).

---

## World & Cities

The world is divided into **five regions** with **20 unique cities** (including a hidden 20th), each with its own biome, services, dialogue NPCs, and dungeon theme.

### North Region
| City | Biome | Notable Features |
|------|-------|------------------|
| **Stormhold** | Tundra | Fortress city; Barracks, Gift Shop |
| **Thornwall** | Temperate | Garrison town; Barracks training |

### Central Region
| City | Biome | Notable Features |
|------|-------|------------------|
| **Solmere** | Temperate | *Starting hub*; most services including Guild & Blacksmith |
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
| **Brinewatch** | Coastal | Major western port; Port, Shipyard, Trade Hall, Blacksmith |
| **Mirefall** | Swamp | Deep swamp town; Herbalist, Black Market |
| **Ashkara** | Desert | Desert oasis; Black Market, Blacksmith, Guild |
| **Dunemar** | Desert | Trade post; Trade Hall, Black Market, sea route to Coralhaven |
| **Saltmarsh** | Coastal | Fishing village; minor port, sea routes to Blackwake & Tidebreak |

### Far Reaches / Islands
| City | Biome | Notable Features |
|------|-------|------------------|
| **Tidebreak** | Coastal | Great southern port hub; Port, Shipyard, Trade Hall |
| **Coralhaven** | Tropical | Island paradise; Port, Temple, Herbalist, Guild, Gift Shop |
| **Blackwake** | Coastal | *Hidden pirate cove*; sea-only, Inn, Port, Black Market |
| **Isle of Glass** | Magical | *Hidden island*; sea-only; Arcane Tower, Port |
| **Wonderland** 🌟 | Wonderland | *Secret 20th city*; book-only via Veilholt Arcane Tower; 50-floor dungeon, unique superbosses, heroine quests |

> **Sea-only cities** (Coralhaven, Blackwake, Isle of Glass) can only be reached by ship from port cities. Blackwake and Isle of Glass lack regular shops.
> 
> 🌟 **Wonderland** is a hidden city with no map connections — discover it through the Arcane Tower in Veilholt. See the [Wonderland System](#wonderland-system) section.

---

## City Services

Each city offers a subset of the following services:

| Service | What It Does |
|---------|-------------|
| **Shop** | Buy consumables, equipment, and supplies. Stock size and prices vary by city. |
| **Inn** | Rest to restore HP. Cost varies by city; free after a certain hour in some places. |
| **Blacksmith** | Enhance equipment (+1 to +N) using gold, or **fuse Scrolls** onto equipment to set its rarity. Prices scale with enhancement level. Charisma and city favor reduce costs. |
| **Temple** | Receive blessings that buff all attributes (+1 to +3) for 2–5 floors depending on donation tier. Cures curses. |
| **Guild** | Pick up **bounties** (hunt contracts) and **Ascend** to raise your level cap. Bounties scale with your level and city **favor**. Higher favor = harder contracts, better rewards. Ranked Bronze → Silver → Gold → Platinum, with a 1–5 star difficulty. View floor-by-floor enemy intelligence for any city's dungeon. |
| **Trade Hall** | Buy a **House Deed** (one per player), buy and sell goods, and acquire **mounts** that reduce travel time and encounter danger. |
| **Port** | Pay for sea voyages to distant destinations. Requires a port city. If you own a ship, voyages are faster and free. |
| **Shipyard** | Purchase ships (Merchant Sloop or War Frigate) that unlock sea routes and grant travel bonuses. |
| **Barracks** | Train to gain temporary attribute buffs for your next dungeon run. |
| **Herbalist** | Buy natural remedies, antidotes, and unique potions. |
| **Arcane Tower** | Magical services: identify items, arcane training. In Veilholt, also the gateway to **Wonderland**. |
| **Black Market** | Rare and dangerous goods. Sells items not found in normal shops. Higher prices, unique stock. |
| **Gift Shop** | Buy affection gifts and **engagement rings** (Ruby, Sapphire, Emerald, Topaz, Amethyst, Diamond) for monster girls. |
| **Skill Book** | View and manage your unlocked class skills and their mastery levels. |
| **Your House** | *(Only if you own one)* Manage storage, collect passive income, rest with bed buffs, and house monster girls. |
| **View Stats / Inventory** | Inspect your character, allies, equipment, and manage items. |
| **Travel** | Journey to connected cities by land. |
| **Enter Dungeon** | Descend into that city's themed dungeon. You can choose any unlocked floor. |
| **Save & Return** | Save your game and return to the main menu. |

> 🔮 **Secret Facility — Godmother**: Hidden in Wonderland's Temple, the Fairy Godmother upgrades heroine weapons after you defeat their linked superboss. See [Heroine Quest System](#heroine-quest-system).

### City Favor
- Each city tracks a **favor** score that increases by completing bounties and clearing dungeon floors.
- Higher favor unlocks harder (better-paying) bounties, increases bounty rewards, and grants shop/blacksmith discounts.
- Favor also affects bounty deadlines and the number of bounties available.

### Global Events
- Random **world events** occur each day: bounty bonuses, shop sales, festival discounts, dangerous nights, and more.
- Events are displayed on the city status screen alongside the current date and time.

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
  - **Trap** — Avoidable hazard (DEX + WIS check to disarm)

### Boss Floors
- Every **5th floor** is a **true boss fight** with a powerful enemy.
- Every **20th floor** is a **superboss fight** — mechanically unique, multi-phase battles (see [Superboss System](#superboss-system)).
- In Pandemonium, the 20th and 40th floors trigger superboss encounters with unique arena flavor text.

### Progression
- **Per-city floor tracking**: each city remembers its own current floor and maximum cleared floor.
- You can **descend to any unlocked floor** — no need to replay from Floor 1.
- Mid-floor progress is saved: if you quit during a run, you resume in the same room.
- **Guild Intelligence**: visit any Guild to view a floor-by-floor breakdown of what enemies can spawn in that city's dungeon, including active bounty targets.

### Loot
- **50% drop chance** from regular enemies; **70%** in Pandemonium.
- Rarity weights shift dramatically with enemy level — higher floors drop Epic and Legendary gear more often.
- Bosses and superbosses grant significantly more gold and EXP.
- Pandemonium doubles gold drops and shifts rarity toward Epic/Legendary.

### Difficulty
- Enemy level scales with floor number (roughly ±6 to +3 range).
- Time of day affects enemy strength and travel danger.
- Biome filtering ensures desert dungeons feature desert races, coastal dungeons feature coastal creatures, etc.
- **Death Penalty**: dying in a dungeon costs you 20% of your gold (minimum 10 gold). You return to your last city.

---

## Superboss System

Pandemonium features **14 mechanically unique superbosses** across three encounter pools. Every superboss is a multi-phase fight with signature gimmicks, custom HUD effects, and unique legendary drops.

### Global Pool (8 Superbosses)

Every **20th floor** in standard dungeons pits you against one of 8 superbosses drawn from a shuffled pool:

| # | Superboss | Theme | Signature Mechanic | Legendary Drop |
|---|-----------|-------|--------------------|----------------|
| 1 | **Broodmother Vileheart** | Toxic lair | Spawns swarms of spiderlings; applies poison & web | Vileheart Pendant (poison-on-hit accessory) |
| 2 | **Dream-Devouring Slitcurrent** | Dream distortion | Phases between Dream and Nightmare forms | **Abyss Fang** (dark damage weapon) |
| 3 | **Sylvana** | Mirror dimension | Creates mirror clones of your party; reflective damage | — |
| 4 | **Ignis** | Molten forge | Alternates between Heat Shield and Overheat phases; fire-elemental colossus | — |
| 5 | **Yinglong** | Celestial dragon | Multi-element dragon with storm, wind, and light attacks; pin-stacking mechanic | **Tarnished Jade** (pin-stack armor) |
| 6 | **Rientrante** | Reality glitch | Breaks the fourth wall; distorts the combat HUD; "Frostbound" / "Truth Unveiled" phases | — |
| 7 | **The Everlong Ship** | Ghostly vessel | Spectral pirate crew; phases between spectral and corporeal | **Captain's Cutlass** (water damage weapon) |
| 8 | **The Black Silence** | Silent workshop | Three-phase fight; 9 workshop attack patterns; Furioso ultimate; revives at 55% HP | **Certain Someone Black Gloves** (replaces all class skills) + Perception-Blocking Mask |

### Pool Mechanics
- Superbosses are drawn from a **shuffled pool** of all 8 so each one appears once before repeating.
- The pool is seeded per character to ensure consistency across runs.
- Superboss EXP reward: **500 + (floor × 50)**.
- You **cannot flee** from superboss encounters.

### Pandemonium Exclusive
- **Chrysalis, the Entangled One** — appears on Pandemonium Floor 20.
- Three Temporal Aspects (Past/Present/Future) share an immortal health pool. Only the Present Aspect can be damaged — and only during **Paradox Fracture** windows.
- Drops **Chronoweave Mantle** (temporal defense armor) and **Fractured Hourglass** (full cooldown reset consumable).

### Wonderland Superbosses

Every **10th floor** in the Wonderland dungeon features its own unique superboss:

| Floor | Superboss | Theme | Legendary Drop |
|-------|-----------|-------|----------------|
| 10 | **Queen of Hearts** | Royal Decrees, Card Soldiers, Temper Tantrum, Mercy Rule | Rose-Tinted Crown |
| 20 | **Big Bad Wolf** | Swallow mechanic (removes allies), Huff and Puff AoE, 15% Enrage | Woodcutter's Broken Axe |
| 30 | **Wicked Witch of the West** | 3-phase (Emerald Flame → Flying Fury with Monkeys → I'm Melting!), 2× water weakness | Wicked Witch's Hat, Broomstick |
| 40 | **The Jabberwock** | 4-phase (Bewilderbeast → Manxome → Frabjous → Narrative Collapse), Alice-linked quest | Vorpal Blade Fragment |
| 50 | **Mary Sue** | **Six-phase final boss** with Plot Armor (5 stacks stripped by damage variety), summons 4 shadow superbosses, Author's Wrath | **The Author's Pen** (+4 all stats in Wonderland) |

---

## Pandemonium Dungeon (Endgame)

Hidden beneath the **Isle of Glass**, Pandemonium is the ultimate endgame challenge — a 50-floor crystalline dungeon accessible only after proving your mastery across the world.

### Unlock Requirement
- Clear **Floor 40** in dungeons across at least **4 unique biomes**.

### Pandemonium Curse System
Every floor in Pandemonium rolls a **random curse** that persists for the entire floor. Curses scale with **Corruption Tiers** every 10 floors:

| Tier | Floors | Multiplier | Name |
|------|--------|------------|------|
| 1 | 1–10 | 1.0× | Whispering Corruption |
| 2 | 11–20 | 1.5× | Seething Corruption |
| 3 | 21–30 | 2.0× | Howling Corruption |
| 4 | 31–40+ | 2.5× | Apocalyptic Corruption |

#### Curse Types (10 total)
| Curse | Effect |
|-------|--------|
| **Crystal Fragility** 💔 | Take more damage from all sources |
| **Weakened Resolve** 🔻 | Deal less damage with all attacks |
| **Sapping Aura** 💀 | Lose HP at the start of every room |
| **Blighted Recovery** 🩸 | All healing reduced |
| **Corrupted Loot** 🪙 | Gold drops reduced |
| **Crystalline Prison** 🔒 | Fleeing disabled |
| **Mirrored Mind** 🪞 | WIS stat check DCs increased |
| **Unstable Ground** 💥 | DEX stat check DCs increased |
| **Time Dilation** ⏳ | Enemies gain initiative bonus |
| **Echoing Madness** 🌀 | Chance to lose your turn each round |
| **Mana Drain** 🔮 | Skill cooldowns extended |

### Pandemonium-Specific Features
- **Enhanced loot**: 70% drop rate, rarity heavily skewed toward Epic/Legendary.
- **2.5× gold multiplier** plus guaranteed bonus gold.
- Bosses on floors 5, 10, 15, 25, 30, 35, 45, 50.
- **Floor 20**: Chrysalis, the Entangled One — Pandemonium's exclusive superboss (see [Pandemonium Exclusive](#pandemonium-exclusive)).
- **Floor 40**: A global-pool superboss encounter.
- Pandemonium enemies deal **1.7× damage**.

---

## Wonderland System

Hidden beyond the veil of reality, **Wonderland** is a secret 20th city and the game's most ambitious dungeon — a 50-floor storybook nightmare with its own superboss cadence, whimsical quirks, and a six-phase final boss.

### Discovery
- Wonderland is only accessible through the **Arcane Tower in Veilholt** — look for a mysterious book.
- It has no land or sea connections. Entry and exit are via the book alone.
- Wonderland features its own unique NPCs: the White Rabbit, Caterpillar, Mad Hatter, Rose Gardener, Cheshire Cat, Captain Hook, the Fairy Godmother, and Tweedledee & Tweedledum.
- Services include: shop, inn, herbalist, arcane tower, black market, temple, and gift shop.

### Wonderland Quirk System

Unlike Pandemonium's punishing curses, Wonderland has **10 whimsical quirks** — mostly beneficial floor effects that scale with depth across 4 tiers:

| Quirk | Effect |
|-------|--------|
| 🍄 **Curiouser and Curiouser** | Random party member gains +stat per room |
| 🫖 **Mad Hatter's Tea Party** | Post-combat healing increased |
| 😸 **Cheshire Cat's Favor** | Enemies have miss chance |
| 👑 **Queen's Decree** | Gold drops increased |
| 🐇 **White Rabbit's Haste** | Skill cooldowns reduced |
| 🐛 **Caterpillar's Insight** | Stat check DCs reduced |
| ⚔️ **Jabberwock's Bane** | Bonus damage vs. bosses |
| 🪞 **Looking Glass** | Loot reroll chance |
| 🌹 **Painting the Roses Red** | Enemy damage reduction |
| 🎩 **Mad Hatter's Drop** | Bonus item from boss kills |

### Wonderland Shadow System (Floors 40+)

At Floor 40 and Floor 46, you must choose **1 persistent negative Shadow** that affects all subsequent floors:

| Shadow | Effect |
|--------|--------|
| **Author's Will** | Reduced damage dealt |
| **Off With Their Heads** | Chance to lose turn each round |
| **Down the Rabbit Hole** | Room entry damage |
| **Jabberwock's Wrath** | Increased damage taken |
| **Madness Contagion** | Healing reduced |
| **Looking Glass Shatter** | Accuracy penalties |
| **Caterpillar's Smoke** | Stat check DCs increased |
| **Rose Wilt** | Bleed & poison duration extended |
| **White Rabbit Panic** | Enemy initiative bonus |
| **Cheshire Absence** | Gold drops reduced |

Accumulated shadows **alter Mary Sue's behavior** on Floor 50, granting her unique passives based on your choices. Choose carefully — each shadow makes the final battle more complex.

### Wonderland Dungeon Structure
- **50 floors** of Storybook-race enemies (living fairy tales gone wrong).
- **20 unique floor bosses** on even-numbered non-superboss floors, including: White Rabbit, Cheshire Cat, Peter Pan, Captain Hook, Tick-Tock Crocodile, Mr. Hyde, Professor Moriarty, Dracula's Bride, Phantom of the Opera, the Headless Horseman, the Scarecrow King, the Snow Queen, and more.
- Superbosses every **10 floors** (see [Wonderland Superbosses](#wonderland-superbosses)).
- Unique consumables: Drink Me Potion, Eat Me Cake, Pixie Dust Vial, Plot Hole Scrap.
- Crafting materials drop from superbosses: Wolf's Tooth, Crimson Hood Scrap, Vorpal Blade Fragment, Emerald Flame Crystal, Monkey Wing, Mary Sue's Teardrop.
- Key items found throughout: Wonderland Key, Frabjous Page, Looking Glass Shard, Glass Anchor, Witch's Broom.

---

## Skill System

Skills are the core of combat progression. Every class has its own skill tree, and mastering your skills is key to surviving higher floors.

### How Skills Work

- **Class skills** unlock automatically at specific levels (3, 5, 8, 10, 15).
- Each class has **5 active skills** and **1 passive skill**. Passives are always active once unlocked.
- Skills have **cooldowns** measured in combat rounds. After using a skill, you must wait the listed number of rounds before using it again. Cooldowns tick down by 1 at the end of each round.
- Skills scale with your **primary attribute + Learning**, making them stronger than basic attacks as you invest in those stats.
- **Silence** status prevents all skill usage — keep an eye out for enemies that can silence you.

### Skill Book

Accessible from any city menu, the **Skill Book** shows:

- Your **class passive** — always active, no input needed.
- Every **active skill** in your class tree, sorted by tier:
  - **Tier 1 (Level 3–8):** Your first 3 skills.
  - **Tier 2 (Level 10–15):** Your advanced 2 skills.
- Each skill's **unlock level**, **cooldown**, and description.
- Locked skills show `[LOCKED]`; skills on cooldown show `[CD: N]`.
- **Ally skills** — every recruited monster girl's passive, innate skills, and learnable skills are also displayed.

### Skill Mastery

Every time you use a skill in combat, its **mastery** increases by 1. Mastery provides cumulative bonuses at thresholds:

| Mastery Level | Uses Required | Bonus |
|---------------|---------------|-------|
| ★ (Lv.1) | 10 | Minor power increase |
| ★★ (Lv.2) | 40 | Power increase + cooldown reduction (-1 turn) |
| ★★★ (Lv.3) | 100 | Maximum power + unique bonus effect |

Mastery progress and bonuses are displayed in the Skill Book. The more you use a skill, the deadlier it becomes.

### Ally Learnable Skills

Allies can study **learnable skills** from three categories:

| Category | Focus |
|----------|-------|
| **Offensive** | Damage-dealing and debuff abilities |
| **Defensive** | Damage reduction, taunts, and self-heals |
| **Support** | Party buffs, healing, and utility |

- One skill can be studied at a time; learning progresses by earning combat EXP with that ally.
- Once learned, ally skills also have their own mastery track.

### In Combat

- Your available skills appear as numbered options `[1]` through `[9]` in the action menu.
- Skills on cooldown are hidden from the menu until they recharge.
- The Skill Book cannot be opened during combat — plan your loadout before entering the dungeon.

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
| Action | Key | Description |
|--------|-----|-------------|
| **Attack** | `a` | Basic attack. Target any enemy. Weapon scaling stat (STR, DEX, LRN, WIS, CHA, or CON) determines damage. |
| **Skills** | `1`–`9` | Use unlocked class skills. Skills have cooldowns, mastery levels, and scale with your primary attribute + Learning. |
| **Defend** | `d` | Reduce incoming damage for the round. |
| **Use Item** | `u` | Consume potions, elixirs, or throwables from inventory. |
| **Capture** | `c` | Throw a capture net at a weakened monster girl to add her to your house. |
| **Flee** | `f` | Attempt to escape. Success chance based on DEX and enemy strength. Cannot flee from superbosses. |
| **Wield the Abyss** | `w` | *(Abyss Fang equipped)* Triggers Dream Devour — massive dark damage, heals the user, and may grant Abyssal Tempo (triple actions). 10-turn cooldown. |
| **Crew Rally** | `r` | *(Captain's Cutlass equipped)* Rallies the party for 3 turns: +20% damage (ramping to +30%), +25% damage reduction, and 1 riposte per turn per ally. 8-turn cooldown. |

### Ally Turns
- All allies are **controlled by the player** — you choose their actions each turn.
- Allies can attack, use innate skills, use items, or defend. They cannot capture or wield the Abyss.
- Allies have their own **equipment slots** (weapon, armor, accessory1, accessory2) and can be geared up independently.

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
- Two damage types: **Physical** (melee/weapon-based) and **Magical** (spell/arcane-based)
- Every entity has **elemental/type resistance** (`<1.0` = resistant, `>1.0` = weak) and **elemental/type damage** modifiers.
- Race, class, and equipment all contribute to your elemental/type profile.
- **Keyword-based specialization**: enemy names containing keywords (e.g., "Lightning", "Frost", "Abyssal", "Arcane", "Brute") automatically gain elemental/type damage and resistance overrides on top of their racial profile.
- Equipment can have elemental/type damage bonuses (weapons) or resistances (armor).

### Weapon Scaling
- Weapons scale with one of six attributes: **STR, DEX, LRN, WIS, CHA, or CON**.
- **Constitution weapons** (Tower Shield, Iron Gauntlets, Bulwark Mace, Thorned Plate) deal half damage but grant damage reduction equal to CON÷2 when equipped.
- The legendary **Abyss Fang** dual-scales with both STR and DEX.

---

## Legendary Weapons & Unique Gear

Superbosses and special quests drop legendary equipment with powerful active abilities and unique passives:

### Legendary Weapons

#### Abyss Fang
- **Source**: Dropped by the Dream-Devouring Slitcurrent (superboss).
- **Stats**: +6 STR, +3 DEX; 1.5× dark damage.
- **Special — Dream Devour** (`w`): Deals massive dark damage to one enemy, heals the user for 35% of damage dealt. If the target is at ≤30% HP, grants **Abyssal Tempo**: 2 turns of triple actions. 10-turn cooldown.

#### Captain's Cutlass
- **Source**: Dropped by The Everlong Ship (superboss).
- **Stats**: +5 STR, +3 CHA, +2 DEX; 1.3× water damage.
- **Special — Crew Rally** (`r`): Buffs the entire party for 3 turns: +20% attack damage (ramps to +30% on turn 2), +25% damage reduction. Each ally (and the captain) gets 1 free riposte per turn — counterattacking when struck. 8-turn cooldown.
- **High Tide**: Gains persistent stacking bonuses as you clear floors while equipped.
- **Riposte**: When a rallied party member is attacked, they automatically counter for 40% of their normal attack damage (once per turn each).

#### Certain Someone Black Gloves
- **Source**: Dropped by The Black Silence (superboss).
- **Stats**: +7 STR, +4 DEX.
- **Special**: Replaces **all** class skills with 9 unique workshop attack patterns. Build up to **Furioso** — a devastating ultimate attack. Changes the entire way you play in combat.

### Legendary Armor

#### Tarnished Jade
- **Source**: Dropped by Yinglong (superboss).
- **Pin Stacking**: Landing attacks builds Pin stacks (up to 10). At max stacks, unleash **Divine Lament** — a massive nuke that consumes all pins. Risk: **Wedge Backlash** may trigger if pins are stacked recklessly.

#### Chronoweave Mantle
- **Source**: Dropped by Chrysalis, the Entangled One (Pandemonium Floor 20).
- **Temporal Defense**: Reduces damage taken from enemies that haven't acted yet in the round.

### Legendary Accessories

#### Vileheart Pendant
- **Source**: Dropped by Broodmother Vileheart (superboss).
- **Effect**: 25% chance to apply poison on hit (50% if the target is already poisoned).

#### The Author's Pen
- **Source**: Dropped by Mary Sue (Wonderland Floor 50).
- **Effect**: +4 to all attributes while in Wonderland. **Rewrite**: powerful self-heal ability.
- The ultimate trophy from the hardest fight in the game.

#### Perception-Blocking Mask
- **Source**: Dropped by The Black Silence (superboss).
- **Effect**: Grants **Silent Visage** — enemies have a chance to ignore you, focusing on allies instead.

#### Wedding Accessories
Over 40 unique soulbound accessories obtained through [marriage](#engagement--marriage). Effects are **amplified (Bonded)** when the married monster girl is in your active party. See the [Engagement & Marriage](#engagement--marriage) section for details.

### Vorpal Weapons (Heroine Quests)
Story-linked upgradeable weapons earned through the [Heroine Quest System](#heroine-quest-system):
- **Vorpal Blade** (Alice) — upgraded from ??? Blade; special: Frabjous Day
- **Grandmother's Axe** (Red Hood) — upgraded from Woodcutter's Broken Axe; special: Through the Forest
- **Ruby Slippers** (Dorothy) — upgraded from Silver Slippers; special: Emerald City's Light

---

## Stat Milestones

Every **5 points** in a base attribute grants a permanent passive bonus. These are calculated from your **base** attributes (before equipment and buffs):

| Stat | Milestone Bonus (per 5 points) |
|------|-------------------------------|
| **Strength** | +1 flat damage to all attacks and skills |
| **Constitution** | -1 damage taken from all sources (flat reduction, min 0) |
| **Dexterity** | +4% dodge chance; +1 damage to thrown/utility items |
| **Wisdom** | +1 HP healed from all healing sources; +1 initiative bonus |
| **Learning** | +6% bonus EXP from all sources |
| **Charisma** | +5% capture success chance; +4% shop discount |

---

## Monster Girl & Ally System

### Capture
- During combat, if a **monster girl** enemy is weakened (low HP), the **Capture** action becomes available.
- Use capture nets (bought from shops or found) to attempt capture.
- Success chance increases as HP drops.

### Housing & Affection
- Captured monster girls are stored in your **House**.
- Raise their **affection** by giving gifts (from Gift Shops) or through dungeon victories.
- Each girl has a preferred gift type that grants bonus affection.
- Daily interaction limits apply: you can talk to and gift each girl once per day, encouraging you to spread attention across your roster.

### Recruitment
- Once a monster girl's affection reaches **50+**, you can **recruit** her as an active **ally**.
- Allies join your combat party (max 3 active at a time).
- Allies gain EXP from battles, level up, and have their own level cap (starts at 10).

### Ally Skills
- **Race Passive**: Each ally inherits a passive skill based on their monster girl race.
- **2 Innate Skills**: Every monster girl has two unique innate combat skills.
- **Learnable Skills**: Allies can learn additional skills from three categories — Offensive, Defensive, and Support. One skill can be studied at a time; learning progresses via combat EXP.
- **Skill Mastery**: As allies use their skills, their mastery improves, increasing effectiveness.
- **Ally Equipment**: Allies have full equipment slots (weapon, armor, accessory1, accessory2) and benefit from enhancement and elemental bonuses.

> 💍 **Marriage**: Once a girl reaches 100 affection, you can propose with an engagement ring. At 200 affection, she gifts you a legendary Wedding Accessory. See the full [Engagement & Marriage](#engagement--marriage) section.

### Ally Management
- Allies have their own stats, equipment slots, HP, and level cap.
- In combat, you control every ally turn directly — they can attack, use skills, use items, or defend.
- You can swap active allies at your House.
- **Party Swap in Combat**: when an ally falls, you can swap in a reserve ally between rooms.
- House level determines how many monster girls you can store (2 → 4 → 8 → 14 → 24 → 50 → 75 → 100).

---

## Engagement & Marriage

Once a monster girl's affection reaches **100**, you can propose with an engagement ring. Marriage deepens the bond and unlocks powerful combat rewards.

### Engagement
- **6 ring types**: Ruby, Sapphire, Emerald, Topaz, Amethyst, and Diamond — purchased from Gift Shops.
- Proposal requires 100 affection. Upon acceptance, the girl becomes **engaged**.
- Affection cap rises to **200** after engagement.

### Wedding Accessories
- At **200 affection**, the married girl gifts you a **Legendary Wedding Accessory** — a unique soulbound item with powerful combat effects.
- Each monster girl has a **distinct accessory** with its own special ability. Over 40 unique wedding accessories exist.
- **Bonded Mechanic**: If the married girl is in your active combat party, the accessory's effects are **amplified**.

### Sample Wedding Accessories

| Accessory | Effect |
|-----------|--------|
| **Bark Shield** | Damage reduction; amplified when Bonded |
| **Shadow Cloak** | Dodge chance and dark damage bonus |
| **Cosmic Gravity** | Enemy slow and gravity damage |
| **Crimson Feast** | Lifesteal on attacks |
| **Flame Dance** | Fire damage and burn application |
| **Siren Song** | Enemy confusion chance |
| **Valkyrie Ride** | Bonus initiative and light damage |
| **Dragon Judgment** | Bonus damage vs. high-HP enemies |
| **Starfire Breath** | AoE light/fire hybrid damage |
| …and 30+ more | Each unique to a specific monster girl |

> Wedding accessories cannot be obtained from random drops — they are exclusively earned through marriage.

---

## Heroine Quest System

Three story-linked heroines await in Wonderland, each with a weapon upgrade questline:

| Heroine | Rusted Weapon | Upgraded Weapon | Special Ability |
|---------|--------------|-----------------|-----------------|
| **Alice** | ??? Blade | **Vorpal Blade** | Frabjous Day — massive light/dark hybrid attack |
| **Red Hood** | Woodcutter's Broken Axe | **Grandmother's Axe** | Through the Forest — cleave attack |
| **Dorothy** | Silver Slippers | **Ruby Slippers** | Emerald City's Light — party-wide heal & buff |

### Quest Flow
1. **Meet the Heroine** — encountered during your Wonderland journey.
2. **Defeat their nemesis** — each heroine is linked to a specific Wonderland superboss:
   - Alice → The Jabberwock (Floor 40)
   - Red Hood → Big Bad Wolf (Floor 20)
   - Dorothy → Wicked Witch of the West (Floor 30)
3. **Visit the Godmother** — a hidden NPC in Wonderland's Temple who upgrades the rusted weapon into its legendary form.
4. Each upgrade requires a **crafting material** dropped by the corresponding superboss (Vorpal Blade Fragment, Crimson Hood Scrap, or Emerald Flame Crystal).

---

## Player Housing

You may own **one house globally** (placed in any city except Blackwake and Isle of Glass). Buy a deed at any Trade Hall to place it.

Owning a house gives you:

| Feature | Benefit |
|---------|---------|
| **Storage** | Store items outside your inventory (10 / 20 / 35 slots). |
| **Passive Income** | Collect daily gold based on house level and city wealth (capped at 10 days). |
| **Rest Buff** | Sleep in your own bed for a blessing that lasts 1–3 floors (+1 / +2 / +3 all attributes). |
| **Monster Girl Housing** | Store captured girls (2 → 4 → 8 → 14 → 24 → 50 → 75 → 100 capacity based on house level). |
| **Faster Rest** | Rest time is shorter than inns (90 / 70 / 50 minutes). |

### House Levels
| Level | Name | Upgrade Cost | Storage | Income/Day | Girl Cap | Bed Buff | Rest Time |
|-------|------|-------------|---------|------------|----------|----------|-----------|
| 1 | Hovel | 300g | 10 | 8g | 2 | — | 30 min |
| 2 | Cottage | 600g | 20 | 18g | 4 | — | 25 min |
| 3 | Manor | 1,500g | 35 | 35g | 8 | +1 all, 3 floors | 20 min |
| 4 | Villa | 3,000g | 55 | 65g | 14 | +1 all, 4 floors | 15 min |
| 5 | Estate | 6,000g | 80 | 110g | 24 | +2 all, 5 floors | 10 min |
| 6 | Palace | 12,000g | 120 | 200g | 50 | +2 all, 6 floors | 10 min |
| 7 | Citadel | 25,000g | 170 | 320g | 75 | +2 all, 7 floors | 5 min |
| 8 | Sanctuary | 50,000g | 230 | 480g | 100 | +3 all, 8 floors | 5 min |

> Passive income also scales with your highest dungeon floor cleared globally, keeping it relevant in late game. Income is capped at 10 accumulated days.

> Wealthier cities (Skylume, Tidebreak, Isle of Glass) yield higher passive income. You can move your house by buying a new deed, but you can only ever have one.

---

## Progression & Leveling

### Leveling Up
- Gain **EXP** from defeating enemies and completing bounties.
- **Learning milestone** (+6% EXP per 5 Learning) increases all EXP gains.
- Level up grants:
  - **+4 HP** (Constitution-based formula with a flat level bonus)
  - **+1 Attribute Point** to allocate freely
  - **New class skills** unlocked at specific levels
  - **Stat milestone notifications** when thresholds are crossed

### Level Cap & Ascension
- Your **level cap** starts at **10**.
- To raise it, you must clear **unique biome dungeons** to the current cap:
  - 10 → 20: 1 biome cleared to Floor 10
  - 20 → 30: 2 biomes cleared to Floor 20
  - 30 → 40: 3 biomes cleared to Floor 30
  - 40 → 50: 4 biomes cleared to Floor 40
  - 50 → 60: 5 biomes cleared to Floor 50
- Once the biome requirement is met, visit any **Guild** to **Ascend** and raise your cap.
- This encourages exploring the world rather than grinding a single dungeon.

### Race Passives
Each race also has a unique passive skill (separate from class passives) that unlocks at creation:
- **Human**: Jack of All Trades — +1 to all attributes
- **Elf**: Elven Grace — +10% dodge chance
- **Dwarf**: Dwarven Resilience — +15% max HP
- **Halfling**: Lucky — +10% crit chance
- **Orc**: Blood Fury — +15% damage when below 50% HP
- **Gnome**: Tinkerer — +10% item effectiveness
- **Tiefling**: Infernal Legacy — +15% fire & dark damage
- **Dragonborn**: Draconic Ancestry — +10% all elemental damage

> See the [Skill System](#skill-system) section above for a full breakdown of skills, mastery, cooldowns, the Skill Book, and ally learnable skills.

### Equipment & Items
- **Rarity tiers**: Common → Uncommon → Rare → Epic → Legendary (5 tiers)
- **Rarity multipliers**: Uncommon 1.3×, Rare 1.7×, Epic 2.4×, Legendary 3.5× stat scaling.
- **Weapons** scale with STR, DEX, Learning, Wisdom, Charisma, or Constitution depending on type. Over 30 weapon types available.
- **Armor** provides CON and elemental resistances.
- **Accessories** — you have **2 slots** (`accessory1` and `accessory2`), allowing you to equip two accessories simultaneously. Wedding accessories, Vileheart Pendant, Perception-Blocking Mask, and The Author's Pen all compete for these slots.
- **Enhancement**: Blacksmiths can upgrade equipment up to +10. Cost scales with enhancement level × rarity multiplier. Charisma and city favor reduce prices.
- **Scroll Fusion**: Use Fusion Scrolls at the blacksmith to force an item's rarity to a specific tier (Common through Legendary).
- **Unique items** (Abyss Fang, Captain's Cutlass, Black Silence Gloves, wedding accessories, Vorpal weapons) cannot be obtained from random drops.
- **Crafting Materials**: Superbosses drop materials (Wolf's Tooth, Crimson Hood Scrap, Vorpal Blade Fragment, Emerald Flame Crystal, Monkey Wing, Mary Sue's Teardrop) used in heroine weapon upgrades.
- **Key Items**: Special items like Wonderland Key, Frabjous Page, Looking Glass Shard, Glass Anchor, and Witch's Broom unlock story progression in Wonderland.
- **Potion Sickness**: Using consumables applies a brief cooldown before you can use another item — you can't chug potions indefinitely.

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

### Mounts
| Tier | Mount | Cost | Time Reduction | Encounter Safety |
|------|-------|------|----------------|------------------|
| 1 | Mule | 100g | 15% faster | 10% safer |
| 2 | Horse | 300g | 25% faster | 20% safer |
| 3 | War Horse | 800g | 35% faster | 30% safer |
| 4 | Caravan | 2,000g | 45% faster | 40% safer |

> Upgrading a mount only costs the difference between tiers. Downgrading refunds half the difference.

### Sea Travel
- Only available from **Port** cities (Brinewatch, Saltmarsh, Tidebreak, Coralhaven, Blackwake, Isle of Glass, Dunemar).
- Pay a fee for passage (100g per voyage). Some destinations require owning a ship from the **Shipyard**.
- Island cities (Coralhaven, Blackwake, Isle of Glass) are **only reachable by sea**.
- Owning a ship (Sloop or Frigate) makes sea voyages **free and 30% faster**.

### Ships
| Ship | Cost | Benefits |
|------|------|----------|
| Merchant Sloop | 500g | Fast travel, unlocks ocean trading routes |
| War Frigate | 1,500g | Safest voyages, immune to pirate encounters |

> Ships make all sea voyages free and 30% faster. You can only own one ship at a time.

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
d     Defend (brace)
f     Flee (disabled vs superbosses, Crystalline Prison curse)
u     Use item (potions, elixirs, nets, scrolls)
c     Capture (monster girls only, when enemy is weakened)
w     Wield the Abyss (requires Abyss Fang equipped, 10-turn cooldown)
r     Crew Rally (requires Captain's Cutlass equipped, 8-turn cooldown)
s     Swap party member (when an ally has fallen)
```

### General
- `[I]`nventory and `[S]ave` are available after most room victories and from city menus.
- Press **Enter** to confirm most prompts.
- **0** usually means Cancel / Go Back.

---

## GUI Mode

Pandemonium includes an optional **tkinter-based graphical interface** alongside the terminal mode:

- **Launch**: `python launcher.py` and select "GUI Mode".
- **Features**:
  - Dark fantasy themed UI with custom color palette
  - Real-time scrolling terminal output panel
  - Interactive menus, confirmations, and input prompts
  - Splash screen and main menu with save management
  - City screen with service buttons and dungeon map
  - Combat screen with HUD, action buttons, and status display
  - Inventory/equipment management with drag-and-drop style interface
  - Settings persistence (font size, theme preferences)
- **Fallback**: GUI mode wraps the same game logic — save files are fully compatible between terminal and GUI modes.
- The GUI is built as a layered system: `gui/app.py` (main window) → `gui/screens/` (screen controllers) → `gui/widgets/` (reusable components).

---

## Technical Info

- **Language:** Python 3 (core game has no external dependencies; GUI mode requires tkinter, which is bundled with Python).
- **Entry Points:** `main.py` (terminal) or `launcher.py` (mode selector). Build to `.exe` with `make_exe.py` (uses PyInstaller).
- **Saves:** Stored in the `savefile/` folder as JSON. Multiple save slots supported; delete option available from main menu.
- **Data:** Enemy and skill data are loaded from YAML files in `resources/` for easy modding.
- **Modular Design:** Easy to extend with new cities, enemies, items, superbosses, skills, or facilities.
- **Save Compatibility:** New fields are automatically added to old save files when loaded with `character.py` migration.
- **Project Structure:**
  - `combat/` — Combat engine, AI, player actions, UI, stats, allies, superbosses (14 total), legendary weapons
  - `facilities/` — All city services (shop, inn, guild, blacksmith, temple, Godmother, etc.)
  - `gui/` — tkinter GUI with screens (15), widgets (8), theme, terminal emulation
  - `resources/` — Game data (enemies, items, skills, cities, dialogues)
  - `wonderland_curses.py` — Wonderland quirk & shadow system
  - `savefile/` — JSON save files (multiple slots)

---

## FAQ

### "Why can't I level past 10?"
Your **level cap** starts at 10. To raise it, you must clear your current cap floor in dungeons across multiple unique biomes, then **Ascend** at any Guild. See [Level Cap & Ascension](#level-cap--ascension) for the full breakdown.

### "How do I reach Coralhaven / Blackwake / Isle of Glass?"
These are **sea-only island cities**. Travel to a port city (Brinewatch, Saltmarsh, Tidebreak, or Dunemar), then use the **Port** service. Some destinations require owning a ship — buy a Merchant Sloop (500g) at any Shipyard. Once you own a ship, all sea voyages become free and faster.

### "What happens when I die in a dungeon?"
You lose **20% of your gold** (minimum 10g) and wake up in your last visited city with 1 HP. You keep all items, equipment, EXP, and floor progress. Mid-floor progress (current room) is preserved.

### "How do I capture monster girls?"
1. Buy **capture nets** from shops.
2. In combat, weaken a monster girl enemy (marked with `♀`) to low HP.
3. Use the `[C]apture` action.
4. Success chance increases as the target's HP drops and with your CHA milestone bonus. Captured girls are sent to your house.

### "My skill won't activate — it's greyed out!"
Check for:
- **Cooldown** — skills need N rounds to recharge after use. The Skill Book shows current cooldowns.
- **Silence** status — you cannot use any skills while Silenced.
- **Level requirement** — you may have previewed a skill not yet unlocked for your level.

### "How do I get the legendary weapons?"
Legendary weapons and gear drop from specific superbosses:

| Item | Source | Type |
|------|--------|------|
| **Abyss Fang** | Slitcurrent (global pool, 20th floors) | Dark damage weapon |
| **Captain's Cutlass** | The Everlong Ship (global pool, 20th floors) | Water damage weapon |
| **Certain Someone Black Gloves** | The Black Silence (global pool, 20th floors) | Workshop skill weapon |
| **Tarnished Jade** | Yinglong (global pool, 20th floors) | Pin-stack armor |
| **Vileheart Pendant** | Broodmother Vileheart (global pool, 20th floors) | Poison accessory |
| **Chronoweave Mantle** | Chrysalis (Pandemonium Floor 20 only) | Temporal armor |
| **The Author's Pen** | Mary Sue (Wonderland Floor 50) | +4 all stats accessory |

Superbosses are drawn from a shuffled pool of 8 — you'll face each one eventually as you clear more 20th floors across different cities. See the [Superboss System](#superboss-system) for the full roster.

### "How do I unlock the Pandemonium dungeon?"
Clear **Floor 40** in dungeons across at least **4 unique biomes** (e.g., Temperate, Swamp, Desert, Mountain). Once unlocked, travel to the **Isle of Glass** and enter Pandemonium from there.

### "How do I find Wonderland?"
Visit the **Arcane Tower in Veilholt** and look for a mysterious book. Wonderland is a hidden 20th city with its own 50-floor dungeon, unique superbosses, heroine quests, and the game's hardest boss — Mary Sue. See the [Wonderland System](#wonderland-system) section.

### "How do I marry a monster girl?"
1. Raise a monster girl's affection to **100** through gifts and dungeon victories.
2. Buy an **engagement ring** from any Gift Shop (Ruby, Sapphire, Emerald, Topaz, Amethyst, or Diamond).
3. Propose! Once engaged, raise affection to **200**.
4. At 200 affection, she gifts you a **legendary Wedding Accessory** with unique combat effects that are amplified when she's in your party.
See [Engagement & Marriage](#engagement--marriage) for full details.

### "What do the Black Silence Gloves do?"
They **replace all your class skills** with 9 unique workshop attack patterns. You build up to **Furioso** — a devastating ultimate. They fundamentally change how you play in combat. Dropped by The Black Silence superboss.

### "Can I respec my attribute points?"
Not currently. Attribute allocations are permanent, so choose carefully! That said, equipment, blessings, barracks training, and stat milestones all add substantial bonuses on top of your base stats.

### "How do I save my game?"
You can save from any city menu (`[S]ave & Return`) or after clearing a dungeon room. There are **multiple save slots** — you can keep separate characters or backup saves. Saves are stored as JSON in the `savefile/` folder and are fully compatible between terminal and GUI modes.

### "What's the difference between terminal mode and GUI mode?"
Both modes play the exact same game with the same save files. **Terminal mode** (`python main.py`) runs in your console/command prompt. **GUI mode** (`python launcher.py` → GUI) uses a tkinter window with clickable buttons, themed panels, and scrollable text output. Choose whichever you prefer — you can switch anytime.

---

## Keybind Quick Reference

### Main Menu / City

| Key | Action |
|-----|--------|
| `1`–`9` | Select numbered menu option |
| `0` | Cancel / Go back |
| `Enter` | Confirm prompt |
| `s` | Save game (from city menu) |
| `i` | Open inventory (after room clears) |

### Combat

| Key | Action | Condition |
|-----|--------|-----------|
| `a` | **Attack** | Always available |
| `d` | **Defend** (brace, -50% damage taken) | Always available |
| `1`–`9` | **Use skill** (numbered by skill list) | Skill unlocked & not on cooldown |
| `u` | **Use item** (potions, elixirs, nets) | Not silenced |
| `c` | **Capture** monster girl | Monster girl enemy present & weakened |
| `f` | **Flee** from combat | Not in superboss fight or Crystalline Prison curse |
| `w` | **Wield the Abyss** (Dream Devour) | Abyss Fang equipped, 10-turn cooldown |
| `r` | **Crew Rally** (party-wide buff) | Captain's Cutlass equipped, 8-turn cooldown |
| `s` | **Swap** fallen ally for reserve | Ally has fallen in combat |

---

## Welcome to the World of Pandemonium

May your blade stay sharp, your wits sharper, and your house always warm.

**Enjoy the adventure!**
