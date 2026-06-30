# TerminalRPG — Improvement & Addition Opportunities

Based on a thorough review of the codebase, here is a comprehensive list of **upgradeable existing systems** and **new features** that can be added.

---

## 1. Combat System (Core Upgrades)

| Priority | Idea | Description |
|----------|------|-------------|
| **High** | **Combat Log / History** | Persist a scrollable log of the last N combat actions for review. |
| **High** | **Critical Hit System** | Add base crit chance (e.g., +DEX-based), crit damage multiplier, and visual feedback. |
| **High** | **Enemy AI Behaviors** | Enemies currently attack randomly. Add roles: healers target wounded allies, casters use spells, berserkers focus low-HP targets. |
| **Medium** | **Party Formations** | Front row / back row positioning. Front row takes more damage but deals more; back row is safer but deals less. |
| **Medium** | **Environmental Hazards** | Dungeon floors apply modifiers: "Flame Floor" (+fire dmg), "Frost Floor" (chance to freeze), "Toxic Mist" (poison each round). |
| **Medium** | **Stealth System** | Rogues can enter stealth before combat for guaranteed first-strike/backstab bonuses. |
| **Medium** | **Taunt/Provoke Mechanic** | Skills or items that force enemies to target specific party members. |
| **Medium** | **Escape Rework** | Scale flee chance with DEX and enemy count; add "smoke bomb" as guaranteed escape. |
| **Low** | **Combo System** | Multi-class parties unlock combo attacks (e.g., Mage freezes → Warrior shatters). |
| **Low** | **Counter-Attack** | High-DEX characters have a chance to counter when attacked. |

---

## 2. Dungeon Crawling (Expansion)

| Priority | Idea | Description |
|----------|------|-------------|
| **High** | **Non-Combat Rooms** | Add treasure rooms, rest shrines, puzzle rooms, and merchant encounters between combat rooms. |
| **High** | **Trap System** | Random traps on floors (spike traps, poison gas, curse glyphs). DEX-based detection/disarm. |
| **High** | **Treasure Chests** | Random chests in rooms with loot tables scaled by floor and rarity. Mimic enemies! |
| **Medium** | **Floor Modifiers** | Each floor rolls a random modifier: "Rich" (more gold), "Cursed" (enemies have hex), "Overgrown" (plant enemies only). |
| **Medium** | **Secret Floors** | Hidden stairs to bonus floors with unique enemies and better loot. |
| **Medium** | **Dungeon Map** | ASCII minimap showing explored rooms, current room, and exit. |
| **Medium** | **Floor-Specific Loot** | Biomes affect drop tables (volcanic = fire items, swamp = poison items). |
| **Low** | **Dungeon Events** | Random narrative events: "You find a wounded adventurer" (help/rob/ignore). |
| **Low** | **Torches / Light System** | Dark floors reduce accuracy unless you have light sources. |
| **Low** | **Exploration Score** | Track % explored per floor; reward completionists. |

---

## 3. Character Progression (Deepening)

| Priority | Idea | Description |
|----------|------|-------------|
| **High** | **Talent Trees** | Each class gets branching talent trees (e.g., Warrior → Berserker or Tank branch). |
| **High** | **Weapon/Armor Proficiency** | Using a weapon type repeatedly grants bonuses (sword mastery, bow mastery). |
| **Medium** | **Title System** | Earn titles from achievements: "Dragon Slayer", "Pacifist", "Dungeon Diver". Titles grant small passive bonuses. |
| **Medium** | **Stat Milestones** | Reaching 20 in a stat unlocks a unique passive (e.g., 20 STR = "Mighty Blow" +10% melee damage). |
| **Medium** | **Class-Specific Quests** | Paladin smite undead, Rogue steal a relic, etc. — rewards unique skills. |
| **Medium** | **Paragon/Ascension** | After level cap, reset to level 1 for permanent account-wide bonuses. |
| **Low** | **Multiclassing** | At level 20, choose a secondary class for hybrid skills. |
| **Low** | **Reputation/Factions** | Align with factions (Temple, Thieves' Guild, etc.) for exclusive rewards. |

---

## 4. Monster Girl & Ally System (Expansion)

| Priority | Idea | Description |
|----------|------|-------------|
| **High** | **Monster Girl Skills** | Each girl gets 2 unique innate skills + skill learning system. Framework exists (`ally_skills.py`) but can be expanded with more skills. |
| **High** | **Affection Decay** | If not visited in N days, affection slowly drops. Adds a reason to return home. |
| **High** | **Monster Girl Roles** | Assign roles: Tank (protects player), Healer (uses support skills), DPS (damage focus). |
| **Medium** | **Evolution System** | At high affection + level, girls can "evolve" into stronger forms with new skills/appearance. |
| **Medium** | **Gift Crafting** | Use dungeon materials to craft personalized gifts for specific girl types. |
| **Medium** | **Romance Progression** | Beyond 100 affection — unlock unique scenes, powerful duo skills, or stat bonds. |
| **Medium** | **Monster Girl Side Quests** | Individual girls give personal quests that unlock their backstory and unique rewards. |
| **Low** | **Fusion System** | Combine two girls into a hybrid with traits from both. |
| **Low** | **Breeding System** | Raise affection to max, unlock offspring with inherited traits. |
| **Low** | **Mood System** | Girls have daily moods affecting combat performance and dialogue. |

---

## 5. Equipment & Items (Major Expansion)

| Priority | Idea | Description |
|----------|------|-------------|
| **High** | **Equipment Set Bonuses** | Wearing 2/4/6 pieces of a named set grants powerful bonuses (e.g., "Dragon Slayer Set" = +fire res, +crit vs dragons). |
| **High** | **Item Crafting / Alchemy** | Use gathered materials to craft potions, bombs, and gear. Herbalist + dungeon gathering. |
| **High** | **Random Enchantments / Affixes** | Epic+ items roll 1-3 random affixes (e.g., "of the Bear" = +CON, "of Fire" = +fire dmg). |
| **Medium** | **Item Sockets & Gems** | Add socketable gems to equipment for customizable stats. |
| **Medium** | **Item Comparison** | When viewing a new item, show side-by-side vs currently equipped. |
| **Medium** | **Legendary Quest Items** | Some legendaries only drop from specific boss quests or crafted from rare components. |
| **Medium** | **Dual Wielding** | Rogues/Barbarians can equip two weapons at once (lower damage each, higher total). |
| **Medium** | **Off-Hand / Shield Slot** | Add shields and off-hand items (orbs, tomes) for more build variety. |
| **Medium** | **Equipment Presets** | Save/load gear sets for quick swapping between "dungeon DPS" and "city social" builds. |
| **Low** | **Item Durability** | Weapons degrade with use; blacksmith repairs for gold. |
| **Low** | **Item Transmogrification** | Change appearance of gear while keeping stats. |
| **Low** | **Unidentified Magic Items** | Items drop as "Unidentified Sword" — identify at arcane tower or with scroll. |

---

## 6. Facilities & City Services (New Additions)

| Priority | Idea | Description |
|----------|------|-------------|
| **High** | **Quest Board** | Non-bounty quests: fetch items, escort NPCs, deliver messages. Different from guild bounties. |
| **High** | **Bestiary / Library** | Log encountered enemies with stats, weaknesses, and lore. Fill it by defeating enemies. |
| **High** | **Training Dummy** | Test damage output against a target dummy in barracks. |
| **Medium** | **Bank / Storage** | Deposit gold across cities to avoid death loss. Already have house storage, but a bank is safer. |
| **Medium** | **Arena / Colosseum** | Fight waves of enemies or boss rush for prizes. No death penalty (knockout). |
| **Medium** | **Casino / Mini-Games** | Simple dice/guessing games for gold. High risk, high reward. |
| **Medium** | **Trophy Hall / Museum** | Display defeated superboss trophies in your house for passive bonuses. |
| **Medium** | **Stables / Mount System** | Buy mounts to reduce travel time between cities. |
| **Medium** | **Hire Mercenaries** | Temporary allies for one dungeon run (not monster girls, generic fighters). |
| **Low** | **Day/Night Services** | Black market only open at night, temple blessings stronger at dawn. |
| **Low** | **Auction House** | Sell items to other players' saves (if multiplayer ever added). |
| **Low** | **Weather-Dependent Events** | Storms boost thunder mages, rain makes travel slower, etc. |

---

## 7. World & Travel (Expansion)

| Priority | Idea | Description |
|----------|------|-------------|
| **High** | **Weather System** | Per-biome weather: rain, snow, sandstorms, magical auroras. Affects combat and travel. |
| **High** | **Naval Combat** | Sea routes have random naval encounters (pirate ships, sea monsters). |
| **Medium** | **Caravan Escort Missions** | Travel with a merchant caravan; defend them from bandits. |
| **Medium** | **Airship / Fast Travel** | Unlock late-game fast travel between discovered cities for a fee. |
| **Medium** | **Landmark Discovery** | Discover landmarks on roads for small permanent bonuses (e.g., "Found the Ancient Obelisk" +1 WIS). |
| **Medium** | **World Map with Fog of War** | ASCII map that reveals as you visit cities and dungeons. |
| **Low** | **Seasonal Events** | Halloween dungeon, winter festival, summer solstice buffs. |
| **Low** | **Random World Events** | "A dragon has been spotted near Elderfen!" — temporary special dungeons. |
| **Low** | **City-Specific Festivals** | Buffs, special shops, and unique enemies during festival days. |
| **Low** | **Crime/Bounty System** | Stealing from shops increases a "wanted" level; guards attack on sight. |

---

## 8. Economy & Gold (Deepening)

| Priority | Idea | Description |
|----------|------|-------------|
| **High** | **Multiple Currencies** | Dungeon tokens (from guild), sea doubloons (from ports), arcane crystals (from towers). |
| **High** | **Price Fluctuation** | Supply/demand: if many players sell iron swords, price drops. |
| **Medium** | **Investment System** | Invest gold in city businesses for daily returns (risk-based). |
| **Medium** | **Merchant Caravans** | Traveling merchants with rotating exotic stock visit cities periodically. |
| **Medium** | **Crafting for Profit** | Crafted items sell for more than raw materials. |
| **Low** | **Loan / Debt System** | Borrow gold from a shady lender; fail to pay back and face debt collectors. |
| **Low** | **Item Insurance** | Pay a fee to recover equipped items on death. |
| **Low** | **Property Expansion** | Buy houses in multiple cities; each generates income and has unique perks. |

---

## 9. Narrative & Lore (New Systems)

| Priority | Idea | Description |
|----------|------|-------------|
| **High** | **Main Questline** | A central story thread that progresses through dungeon milestones and city visits. |
| **High** | **Journal / Quest Log** | Track active quests, completed quests, and discovered lore. |
| **Medium** | **Lore Books / Codex** | Scattered books in dungeons that unlock lore entries about the world. |
| **Medium** | **NPC Relationships** | Track rapport with key NPCs; high rapport unlocks discounts and unique dialogue. |
| **Medium** | **Random Encounters** | Narrative events during travel and dungeon exploration. |
| **Low** | **Legendary Tales** | Procedurally generated stories about past heroes based on your own save data. |
| **Low** | **Epilogue System** | After "beating" the game, generate a text epilogue based on your choices. |

---

## 10. Quality of Life (Polish)

| Priority | Idea | Description |
|----------|------|-------------|
| **High** | **Inventory Sorting & Filtering** | Sort by type, rarity, stat. Filter by slot. |
| **High** | **Item Comparison in Shops** | Show "Currently Equipped" stat line next to shop items. |
| **Medium** | **Auto-Save** | Optional auto-save after every floor clear. |
| **Medium** | **Settings Menu** | Difficulty slider, text speed, UI color themes, ASCII art toggle. |
| **Medium** | **Keyboard Shortcuts** | Quick keys for common actions (e.g., 'A' for attack, 'S' for skills). |
| **Medium** | **Game Statistics Tracker** | Total kills, gold earned, floors cleared, deaths, favorite skill. |
| **Low** | **Undo for Character Creation** | One free re-roll after seeing starting stats. |
| **Low** | **Export Character Sheet** | Generate a text/markdown summary of your character. |
| **Low** | **Sound Effects** | Text-based audio cues (beep on crit, chime on level up). |
| **Low** | **Color Themes** | Customizable ANSI color schemes for the UI. |

---

## 11. Enemy & Boss Design (Expansion)

| Priority | Idea | Description |
|----------|------|-------------|
| **High** | **Boss Loot Tables** | Each boss has unique drops; superbosses have guaranteed unique items. |
| **High** | **Elite Enemy Variants** | Rare spawns with prefixes: "Elite", "Corrupted", "Ancient" — stronger, better loot. |
| **Medium** | **Boss Phases** | Bosses change tactics at 50% HP (e.g., summon minions, enrage, flee). |
| **Medium** | **Enemy Factions** | Some enemy types fight each other; player can exploit this. |
| **Medium** | **Enemy Weakness System** | Undead weak to Holy, beasts weak to Fire, etc. — shown in bestiary. |
| **Medium** | **Boss Cutscenes** | Short ASCII art intros for superbosses and milestone bosses. |
| **Low** | **Enemy Retreat** | Low-HP enemies have a chance to flee, denying full XP. |
| **Low** | **Summoner Archetype** | Enemies that spawn adds until killed. |
| **Low** | **Boss Rerun** | Re-fight defeated superbosses for practice (no rewards, or reduced). |

---

## 12. Technical & Engine (Under the Hood)

| Priority | Idea | Description |
|----------|------|-------------|
| **High** | **Unit Tests for Combat Balance** | Ensure no class is brokenly OP; verify damage formulas. |
| **High** | **YAML/JSON Config for Enemies** | Move more data out of Python into editable files (already partially done). |
| **Medium** | **Modding Support** | Load custom races, classes, enemies, and items from a `mods/` folder. |
| **Medium** | **Localization Framework** | All strings externalized for translation (i18n). |
| **Medium** | **Better Error Handling** | Graceful failures when enemy data is missing or corrupted. |
| **Low** | **Save File Migration Tool** | Automated script to upgrade old save formats to newest version. |
| **Low** | **Leaderboard** | Export floor-clear records to a local leaderboard file. |
| **Low** | **Weekly Challenge Seeds** | Fixed RNG seeds for community "challenge weeks." |

---

## Summary: Top 10 Recommended Next Steps

If you want to pick the **highest-impact** improvements to implement next, here are the top 10:

1. **Combat Log** — Immediate quality-of-life improvement for understanding fights.
2. **Critical Hit System** — Adds excitement and depth to every attack.
3. **Non-Combat Rooms** — Makes dungeon crawling feel less repetitive (treasure, puzzles, rest shrines).
4. **Trap System** — Adds tension and rewards high-DEX builds.
5. **Talent Trees** — Huge replayability boost; every class playthrough feels different.
6. **Equipment Set Bonuses** — Encourages strategic loadout building instead of just "best stat."
7. **Monster Girl Skill Expansion** — Makes allies feel unique and not just "weaker players."
8. **Bestiary** — Adds completionist motivation and tactical depth.
9. **Main Questline** — Gives players a reason to keep pushing floors beyond "just because."
10. **Weather / Floor Modifiers** — Adds variety to every dungeon run.

---

*This document covers 80+ improvement ideas across 12 categories. Let me know which area you'd like to tackle first, and I can help design and implement it!*
