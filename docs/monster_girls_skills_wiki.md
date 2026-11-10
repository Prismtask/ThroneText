# Pandemonium — Skills Wiki

> Generated from `resources/skill_book/innate_skills.yaml`, `resources/skill_book/skill_list.yaml` and `resources/enemies/enemies_data/monster_girls.yaml`. Regenerate with `tests/_temp_gen_skills_wiki.py` — the same command refreshes the web wiki (`wiki/index.html`).

Covers player class skills, heroine skills, monster-girl innate & awakened skills, and ally learnable skills.

## Contents

1. [How Skills Work](#how-skills-work)
2. [Player Class Skills](#player-class-skills)
3. [Heroines — Innate & Enhanced Skills](#heroines--innate--enhanced-skills)
4. [Monster Girls — Innate Skill Roster](#monster-girls--innate-skill-roster)
5. [Awakened Skills (wave 1)](#awakened-skills-wave-1)
6. [Innate Skill Details (Dictionary)](#innate-skill-details-dictionary)
7. [Learnable Skills (Barracks)](#learnable-skills-barracks)

---

## How Skills Work

- Every **class** has **1 passive skill** (always active) and **10 active skills** unlocked at levels 3, 5, 8, 10, 12, 15, 20, 26, 32 and 40 — see [Player Class Skills](#player-class-skills).
- Every **monster girl** has **2 innate skills** unique to her. Capture her with a net (♀ icon) and she joins your party with both skills unlocked.
- Every **heroine** has 2 innate skills. Equipping her signature weapon **swaps them for 2 enhanced (vorpal) skills**; restoring/upgrading the weapon at the Arcane Tower grants a **third skill**.
- Skills scale with a primary attribute (`STR`, `DEX`, `WIS`, `LER`, `CHA`, `CON`) and have per-skill cooldowns tracked in `skill_cooldowns`.
- Elements: Fire, Water, Thunder, Wind, Earth, Light, Dark, Magical, Physical.
- Fire skills apply the **burn tier** system — **Singe** (3/turn) → **Burn** (6/turn) → **Blaze** (10/turn) → **Inferno** (18/turn) → **Conflagration** (30/turn). Tags name the tier each skill applies; higher tiers overwrite lower ones.
- Every monster girl and heroine also has a **race passive** (separate from innate skills).
- Some girls are **late bloomers** — low-base girls (Goblin Girl, Harpy Scout, …) gain bonus attribute points while leveling in your party (see the Growth column below).
- **Awakening** — twelve girls can be Awakened at the House Lounge (Lv 40 + level cap 40 + affection 150 + 1 Awakening Sigil). An awakening replaces both innate skills with upgraded versions, carries over mastery, and changes her displayed name — see [Awakened Skills (wave 1)](#awakened-skills-wave-1).
- **Learnable skills** are taught at the **Barracks** ('Teach Ally Skill'). Each ally can hold up to **3 learned skills** and learn **1 skill at a time** (earn EXP in combat to finish learning). They come in 4 tiers with level requirements and EXP costs — see [Learnable Skills (Barracks)](#learnable-skills-barracks).

---

## Player Class Skills

Every class has **1 passive skill** and **10 active skills**: the launch six unlock at levels 3, 5, 8, 10, 12 and 15, the **wave-2 skills** at 20, 26 and 32, and the class **capstone** at 40 — after which you choose a **profession** (see below). In combat your skills appear as numbered options (`1`–`9`) and you bring a **Battle Loadout** of up to 9 — the **Skill Book** in any city menu lists them with cooldowns and mastery.

### Warrior

- **Passive — Iron Will:** Your Constitution is permanently increased by 2.

- **Cleave** — *Level 3 · CD 3 · all enemies · power 6 (STR) · Physical* — Swing your weapon in a wide arc, damaging all enemies.
- **Battle Cry** — *Level 5 · CD 5 · self · Physical* — Roar with fury, gaining +2 Strength and +2 Constitution for 3 turns.
- **Execute** — *Level 8 · CD 4 · single enemy · power 10 (STR) · Physical* — Deal devastating damage to a weakened enemy. 3x damage if target is below 30% HP.
- **Shield Slam** — *Level 10 · CD 4 · single enemy · power 12 (CON) · Earth* — Slam your shield into an enemy, dealing damage and stunning it. — *75% stun chance*
- **Second Wind** — *Level 12 · CD 6 · self · Physical* — Recover 30% of your maximum HP instantly. — *heal 30% max HP*
- **Bladestorm** — *Level 15 · CD 6 · all enemies · power 6 (STR) · Wind* — Become a whirlwind of steel, striking all enemies 3 times. — *3 hits*
- **Reckless Charge** — *Level 20 · CD 4 · single enemy · power 18 (STR) · Physical* — Barrels into an enemy for heavy damage, leaving you open (+10% damage taken for 2 turns). — *you take +10% damage for 2 turns*
- **War Banner** — *Level 26 · CD 5 · whole party · Physical* — Plant a banner — the whole party gains +2 Strength and 3% max HP regen for 3 turns.
- **Titan's Swing** — *Level 32 · CD 4 · single enemy · power 24 (STR) · Physical* — A crushing overhead blow that ignores armor. — *ignores armor*
- **Onslaught** — *Level 40 · CD 9 · all enemies · power 14 (STR) · Physical* — Five blows rain across the field — the final blow executes any target left below 30% HP. — *5 hits · class capstone*

### Mage

- **Passive — Arcane Intellect:** Your Learning is permanently increased by 2.

- **Fireball** — *Level 3 · CD 3 · single enemy · power 16 (LER) · Fire* — Hurl a massive fireball at a single enemy.
- **Frost Nova** — *Level 5 · CD 5 · all enemies · power 10 (LER) · Water* — Unleash a blast of freezing energy that damages and slows all enemies. — *applies Slow*
- **Arcane Barrage** — *Level 8 · CD 4 · all enemies · power 8 (LER) · Magical* — Unleash 3 arcane missiles that strike random enemies. — *3 hits*
- **Meteor** — *Level 10 · CD 5 · all enemies · power 22 (LER) · Fire* — Call down a meteor that deals massive fire damage to all enemies.
- **Elemental Focus** — *Level 12 · CD 6 · self · Magical* — Channel raw elements — +15% elemental damage for 3 turns.
- **Mana Overload** — *Level 15 · CD 5 · single enemy · power 35 (LER) · Thunder* — Deal devastating damage to a single enemy. Take 10% max HP as recoil. — *recoil 10% max HP*
- **Time Warp** — *Level 20 · CD 7 · self · Magical* — Bend time to reduce all your skill cooldowns by 2 turns, then act again immediately. — *free action · all active cooldowns -2*
- **Glacial Prison** — *Level 26 · CD 4 · single enemy · power 16 (LER) · Water* — Encase an enemy in ice, dealing water damage with a 60% chance to stun. — *60% stun chance*
- **Arcane Singularity** — *Level 32 · CD 5 · all enemies · power 11 (LER) · Magical* — Tear open a singularity, damaging all enemies and slowing them. — *applies Slow*
- **Cataclysm** — *Level 40 · CD 9 · all enemies · power 8 (LER) · Multi-element* — Seven elemental catastrophes strike in sequence — Fire, Water, Thunder, Wind, Earth, Light and Dark. The Fire strike leaves its target in Inferno. — *Inferno (18/turn) x 4 turns · class capstone · 7 hits (one per element)*

### Rogue

- **Passive — Sneak Attack:** Deal +25% damage to slowed or stunned enemies.

- **Backstab** — *Level 3 · CD 2 · single enemy · power 10 (DEX) · Dark* — Strike a vital point. Double damage if the target is slowed or stunned.
- **Smoke Bomb** — *Level 5 · CD 5 · all enemies · Dark* — Blind all enemies and guarantee a successful escape on your next flee attempt.
- **Assassinate** — *Level 8 · CD 5 · single enemy · power 14 (DEX) · Dark* — Attempt to instantly kill a target below 15% HP. Otherwise deals heavy damage.
- **Shadow Strike** — *Level 10 · CD 4 · single enemy · power 10 (DEX) · Dark* — Strike from the shadows for guaranteed double damage. — *guaranteed crit*
- **Venomous Blade** — *Level 12 · CD 4 · single enemy · power 8 (DEX) · Water* — Coat your blade in poison. The target takes damage over 5 turns. — *Poison 5 dmg x 5 turns*
- **Death Dance** — *Level 15 · CD 5 · all enemies · power 12 (DEX) · Dark* — Unleash a flurry of strikes on 3 random enemies. — *3 hits*
- **Caltrops** — *Level 20 · CD 4 · all enemies · power 8 (DEX) · Physical* — Scatter caltrops — all enemies are slowed and bleed for 4 damage per turn for 4 turns. — *Bleed 4 dmg x 4 turns · applies Slow*
- **Nightshade** — *Level 26 · CD 4 · single enemy · power 14 (DEX) · Water* — A toxic strike that poisons the target for 8 damage per turn for 5 turns. — *Poison 8 dmg x 5 turns*
- **Perfect Opening** — *Level 32 · CD 5 · self · Dark* — Read the fight — +12% crit chance and +25% crit damage for 3 turns.
- **Death's Embrace** — *Level 40 · CD 9 · single enemy · power 30 (DEX) · Dark* — A killing art — execute a target below 35% HP outright. If the strike kills, the cooldown is refunded. — *class capstone*

### Cleric

- **Passive — Holy Favor:** All healing you perform is 20% more effective.

- **Heal** — *Level 3 · CD 3 · self or ally · power 28 (WIS) · Light* — Restore health to yourself or an ally.
- **Divine Shield** — *Level 5 · CD 6 · self · Light* — Become immune to all damage for 2 turns.
- **Holy Smite** — *Level 8 · CD 4 · single enemy · power 14 (WIS) · Light* — Smite an enemy with divine light and heal yourself for half the damage dealt.
- **Mass Heal** — *Level 10 · CD 5 · whole party · power 22 (WIS) · Light* — Restore health to all party members.
- **Resurrection** — *Level 12 · CD 8 · fallen ally · Light* — Revive a fallen ally with 50% of their max HP. — *revive at 50% HP*
- **Divine Wrath** — *Level 15 · CD 6 · all enemies · power 18 (WIS) · Light* — Smite all enemies with holy fire. Heal the party for total damage dealt. — *heals the party for damage dealt*
- **Prayer of Mending** — *Level 20 · CD 4 · self or ally · Light* — Wrap an ally in mending light, restoring 6% of their max HP each turn for 4 turns.
- **Blessed Aegis** — *Level 26 · CD 6 · self or ally · Light* — A protective ward absorbs up to 25% of your max HP in damage for 3 turns.
- **Wrath of Heaven** — *Level 32 · CD 5 · all enemies · power 13 (WIS) · Light* — Call down holy fire on all enemies.
- **Providence** — *Level 40 · CD 9 · whole party · power 40 (WIS) · Light* — Divine intervention — heal the whole party and revive one fallen ally at 50% HP with a protective ward. — *revive at 50% HP · revives with a 15% caster-HP barrier · class capstone*

### Ranger

- **Passive — Keen Eye:** Your Dexterity is permanently increased by 2.

- **Piercing Shot** — *Level 3 · CD 2 · single enemy · power 12 (DEX) · Wind* — Fire a shot that ignores enemy armor. — *ignores armor*
- **Hunter's Mark** — *Level 5 · CD 4 · single enemy · Wind* — Mark an enemy. All your attacks against it deal +50% damage for 3 turns.
- **Rain of Arrows** — *Level 8 · CD 4 · all enemies · power 10 (DEX) · Wind* — Fire a volley of arrows, damaging all enemies.
- **Rapid Fire** — *Level 10 · CD 3 · single enemy · power 8 (DEX) · Wind* — Fire 3 quick shots at a single target. — *3 hits*
- **Trueshot** — *Level 12 · CD 5 · single enemy · power 10 (DEX) · Physical* — A perfectly aimed shot that ignores armor and deals triple damage. — *guaranteed crit · ignores armor*
- **Nature's Grasp** — *Level 15 · CD 5 · all enemies · power 12 (WIS) · Earth* — Entangle all enemies in vines, damaging and slowing them for 3 turns. — *applies Slow*
- **Camouflage** — *Level 20 · CD 5 · self · Wind* — Blend into the terrain — +25% evasion and +10% crit chance for 3 turns.
- **Blast Arrow** — *Level 26 · CD 4 · all enemies · power 12 (DEX) · Fire* — Fire an explosive arrow that bursts on all enemies.
- **Hawk's Eye** — *Level 32 · CD 5 · self · Wind* — Steady your aim — +15% crit chance and +25% Hunter's Mark bonus for 3 turns.
- **Skyfall Volley** — *Level 40 · CD 9 · all enemies · power 13 (DEX) · Wind* — The sky answers — two waves of arrows strike every enemy and pin them in place. — *applies Slow · 2 hits · class capstone*

### Paladin

- **Passive — Aura of Courage:** Your Strength and Charisma are permanently increased by 1.

- **Holy Strike** — *Level 3 · CD 3 · single enemy · power 10 (STR) · Light* — Strike with divine power. 50% chance to stun the target. — *50% stun chance*
- **Lay on Hands** — *Level 5 · CD 6 · self or ally · Light* — Fully restore your own HP or an ally's HP.
- **Divine Judgment** — *Level 8 · CD 4 · single enemy · power 18 (STR) · Light* — Deal massive damage to an enemy. 2x damage if it is stunned.
- **Consecrate** — *Level 10 · CD 4 · all enemies · power 14 (STR) · Light* — Consecrate the ground, damaging all enemies and weakening them. — *applies Weaken*
- **Bastion of Light** — *Level 12 · CD 6 · whole party · Light* — You and all allies gain a defense buff for 3 turns. — *party damage reduction +3 (flat) for 3 turns*
- **Avenging Wrath** — *Level 15 · CD 6 · all enemies · power 16 (STR) · Light* — Deal holy damage to all enemies. Heal yourself for the total damage dealt. — *heals you for damage dealt*
- **Blessing of the Faithful** — *Level 20 · CD 5 · self or ally · power 20 (WIS) · Light* — Heal an ally and shield them — damage taken reduced by 4 for 3 turns.
- **Censure** — *Level 26 · CD 4 · single enemy · power 16 (STR) · Light* — A rebuking strike that damages an enemy and weakens it. — *applies Weaken*
- **Dawnbreaker** — *Level 32 · CD 5 · single enemy · power 24 (STR) · Light* — A searing flash of light — heavy holy damage with a 2-turn blind. — *Blind (40% miss) x 2 turns*
- **Heaven's Sword** — *Level 40 · CD 9 · single enemy · power 40 (STR) · Light* — A colossal blade of light — devastating single-target damage that heals the whole party. — *class capstone*

### Warlock

- **Passive — Soul Siphon:** Heal for 10% of all damage you deal.

- **Drain Life** — *Level 3 · CD 3 · single enemy · power 10 (LER) · Dark* — Drain life from an enemy, healing yourself for the damage dealt.
- **Dark Curse** — *Level 5 · CD 4 · single enemy · Dark* — Curse an enemy, reducing its Strength and Constitution by 2 for 3 turns.
- **Demonic Pact** — *Level 8 · CD 5 · single enemy · power 30 (CHA) · Fire* — Sacrifice 20% of your max HP to deal devastating damage to an enemy.
- **Soul Fear** — *Level 10 · CD 5 · all enemies · Dark* — Terrorize all enemies, reducing their damage by 20% for 3 turns. — *Fear (-20% damage) x 3 turns*
- **Dark Empowerment** — *Level 12 · CD 5 · self · Dark* — Gain +3 Learning and +3 Charisma for 3 turns.
- **Soul Fire** — *Level 15 · CD 5 · single enemy · power 25 (LER) · Fire* — Burn an enemy's soul for massive damage and apply a burning debuff. — *Burn (6/turn) x 3 turns*
- **Grasp of the Void** — *Level 20 · CD 4 · single enemy · power 12 (LER) · Dark* — Dark tendrils slow an enemy and leave it bleeding for 4 damage per turn for 4 turns. — *Bleed 4 dmg x 4 turns · applies Slow*
- **Blood Pact** — *Level 26 · CD 5 · self · Dark* — Sacrifice 15% of your max HP — Learning and Charisma +4 for 3 turns. — *costs 15% max HP*
- **Siphon Soul** — *Level 32 · CD 5 · single enemy · power 20 (LER) · Dark* — Tear at an enemy's soul, healing yourself for the damage dealt.
- **Dark Apotheosis** — *Level 40 · CD 9 · all enemies · power 20 (LER) · Dark* — Ascend for a moment — empower yourself and drain every enemy's essence to mend your wounds. — *class capstone*

### Barbarian

- **Passive — Thick Skin:** Take 15% less damage from all attacks.

- **Feral Rage** — *Level 3 · CD 4 · self · Fire* — Enter a rage. +3 Strength but take 20% more damage for 3 turns.
- **Whirlwind** — *Level 5 · CD 3 · all enemies · power 8 (STR) · Wind* — Spin wildly, striking all enemies around you.
- **Berserk** — *Level 8 · CD 6 · self · Fire* — Attack twice per turn for 3 turns. Take 1d6 damage after it ends.
- **Sunder Armor** — *Level 10 · CD 4 · single enemy · power 12 (STR) · Earth* — Smash an enemy's armor, dealing damage and reducing its defense for 3 turns. — *Sunder -3 armor for 3 turns*
- **Bloodlust** — *Level 12 · CD 5 · self · Physical* — Heal for 50% of damage dealt for 3 turns. — *heal 50% of damage dealt for 3 turns*
- **Earth Shatter** — *Level 15 · CD 6 · all enemies · power 18 (STR) · Earth* — Slam the ground, dealing massive damage to all enemies and stunning them. — *50% stun chance*
- **Battle Trance** — *Level 20 · CD 5 · self · Physical* — Enter a trance — Strength +3 and +8% crit chance for 3 turns.
- **Reckless Abandon** — *Level 26 · CD 6 · self · Fire* — Trade defense for devastation — +35% crit damage, but take +12% damage for 3 turns.
- **Skullbreaker** — *Level 32 · CD 5 · single enemy · power 22 (STR) · Physical* — A concussive blow with a 65% chance to stun. — *65% stun chance*
- **Wrath Incarnate** — *Level 40 · CD 9 · all enemies · power 24 (STR) · Physical* — Unchained fury — crush all enemies, stunning with 40% chance, and recover 25% max HP. — *40% stun chance · class capstone*

---

## Player Professions

After learning your class **capstone** (Level 40), choose **one of two professions** at any Guild — the choice is **permanent**. Your class passive is **upgraded**, your **signature skill** is granted immediately, and two more skills unlock at levels 50 and 60. The other branch is locked out for that save.

### Warrior

#### Warlord — *Command the field — the party fights harder under your banner.*

- **Upgraded passive — Commanding Presence:** Your Strength and Constitution are permanently increased by 2.

- **Iron Command** — *Level 40 · CD 6 · whole party · Physical* — The party deals +15% damage and stands immune to fear for 3 turns.
- **Decimation** — *Level 50 · CD 5 · all enemies · power 16 (STR) · Physical* — A ruinous sweep — heavy damage to all enemies, sundering their armor by 4. — *Sunder -4 armor for 3 turns*
- **Warlord's Reign** — *Level 60 · CD 8 · all enemies · Physical* — Mark every enemy — all of your party's attacks deal +30% damage to them for 4 turns.

#### Sentinel — *Become the wall the party stands behind.*

- **Upgraded passive — Living Bulwark:** Your Constitution is permanently increased by 4, and you take 10% less damage.

- **Guardian Stance** — *Level 40 · CD 6 · self · Physical* — Damage taken -6 and attackers suffer 25% backlash for 3 turns.
- **Living Fortress** — *Level 50 · CD 6 · whole party · Physical* — The whole party takes 4 less damage per hit for 3 turns.
- **Unbreakable** — *Level 60 · CD 8 · self · Physical* — The next lethal blow leaves you standing at 1 HP.

### Mage

#### Evoker — *Raw destruction — every element answers your call.*

- **Upgraded passive — Elemental Mastery:** Your Learning is permanently increased by 3, and you deal +10% elemental damage.

- **Overchannel** — *Level 40 · CD 7 · self · Magical* — Take 10% max HP as recoil — deal +30% damage for 3 turns. — *recoil 10% max HP*
- **Prismatic Ray** — *Level 50 · CD 5 · single enemy · power 30 (LER) · Magical* — A lance of raw light strikes with a random element for massive damage.
- **Arcane Ascension** — *Level 60 · CD 8 · all enemies · power 18 (LER) · Magical* — Scour all enemies, then surge — +20% damage and +15% elemental power for 3 turns.

#### Chronomancer — *Time is a resource — spend it.*

- **Upgraded passive — Temporal Insight:** Your Learning is permanently increased by 2, and every combat begins with all cooldowns 1 turn shorter.

- **Temporal Acceleration** — *Level 40 · CD 7 · self · Magical* — Every party cooldown unwinds by 2 turns.
- **Time Stop** — *Level 50 · CD 8 · all enemies · Magical* — Freeze time — all enemies are stunned and slowed.
- **Rewind** — *Level 60 · CD 9 · self · Magical* — Restore 40% of your max HP and unwind your cooldowns by 4 turns. — *heal 40% max HP*

### Rogue

#### Assassin — *One opening is all you need.*

- **Upgraded passive — Lethality:** Deal +40% damage to slowed or stunned enemies, and +8% crit chance.

- **Mark for Death** — *Level 40 · CD 5 · single enemy · Dark* — Brand an enemy — it takes +30% damage from everything for 4 turns.
- **Mortal Blow** — *Level 50 · CD 5 · single enemy · power 26 (DEX) · Dark* — Execute a target below 25% HP outright; otherwise a heavy armor-piercing strike.
- **Thousand Cuts** — *Level 60 · CD 7 · single enemy · power 10 (DEX) · Dark* — Four rapid strikes on a single target. — *4 hits*

#### Shadowdancer — *The battlefield never sees you coming.*

- **Upgraded passive — Umbral Step:** Deal +25% damage to slowed or stunned enemies, and gain +8% evasion.

- **Veil of Shadows** — *Level 40 · CD 6 · self · Dark* — The whole party gains +15% evasion for 3 turns.
- **Nightmare Requiem** — *Level 50 · CD 6 · all enemies · Dark* — Terrify all enemies (-25% damage) and leave them bleeding for 5 per turn.
- **Shadowfall** — *Level 60 · CD 7 · all enemies · power 20 (DEX) · Dark* — Dark blades fall on all enemies, leaving them bleeding for 6 per turn. — *Bleed 6 dmg x 4 turns*

### Cleric

#### Hierophant — *A beacon of restoration — wounds close where you stand.*

- **Upgraded passive — Blessed Hands:** All healing you perform is 30% more effective, and you regenerate 3% of your max HP each round.

- **Sanctuary** — *Level 40 · CD 6 · whole party · Light* — The party regenerates 5% max HP per round for 4 turns and all cleansable debuffs are removed.
- **Greater Resurrection** — *Level 50 · CD 9 · fallen ally · Light* — Revive a fallen ally at 75% HP with a ward absorbing 20% of your max HP. — *revive at 75% HP · revives with a 20% caster-HP barrier*
- **Eternal Light** — *Level 60 · CD 9 · whole party · power 45 (WIS) · Light* — Heal the whole party and ward every living member against the next lethal blow.

#### Inquisitor — *Judgment given form — light that burns the guilty.*

- **Upgraded passive — Zealous Light:** All healing you perform is 20% more effective, and you gain +8% crit chance.

- **Verdict** — *Level 40 · CD 5 · single enemy · power 22 (WIS) · Light* — Heavy holy damage — the target is branded, taking +15% damage for 3 turns.
- **Chains of Faith** — *Level 50 · CD 6 · single enemy · power 15 (WIS) · Light* — Bind an enemy — 85% stun chance and searing light for 6 per turn. — *Burn (6/turn) x 3 turns · 85% stun chance*
- **Day of Reckoning** — *Level 60 · CD 8 · all enemies · power 20 (WIS) · Light* — Holy judgment on all enemies — +30% damage against debuffed foes.

### Ranger

#### Sharpshooter — *Every shot finds its mark.*

- **Upgraded passive — Deadeye:** Your Dexterity is permanently increased by 3, and you gain +8% crit chance.

- **Steady Aim** — *Level 40 · CD 6 · self · Wind* — +20% crit chance and +30% crit damage for 3 turns.
- **Killshot** — *Level 50 · CD 5 · single enemy · power 28 (DEX) · Wind* — Execute a target below 20% HP outright; otherwise a heavy armor-piercing shot.
- **Perfect Fusillade** — *Level 60 · CD 7 · all enemies · power 12 (DEX) · Wind* — Three guaranteed critical shots spread across the enemy line. — *guaranteed crit · 3 hits*

#### Warden — *The wild itself fights beside you.*

- **Upgraded passive — Verdant Vigor:** Your Dexterity is permanently increased by 2, and you regenerate 3% of your max HP each round.

- **Bramble Grasp** — *Level 40 · CD 5 · all enemies · power 12 (DEX) · Earth* — Roots tear at all enemies — slowed and bleeding for 5 per turn. — *Bleed 5 dmg x 4 turns · applies Slow*
- **Toxic Bloom** — *Level 50 · CD 5 · all enemies · power 10 (DEX) · Earth* — A cloud of spores poisons all enemies for 10 per turn. — *Poison 10 dmg x 5 turns*
- **Nature's Wrath** — *Level 60 · CD 7 · all enemies · power 18 (WIS) · Earth* — The wild erupts — all enemies are slowed with a 50% chance to stun. — *50% stun chance · applies Slow*

### Paladin

#### Crusader — *Zeal sharpened into a blade.*

- **Upgraded passive — Zeal of Battle:** Your Strength is increased by 2 and Charisma by 1, and you gain +8% crit chance.

- **Condemn** — *Level 40 · CD 5 · single enemy · power 16 (STR) · Light* — Strike with holy force — 80% stun chance and +15% damage taken for 3 turns. — *80% stun chance*
- **Avenging Crusade** — *Level 50 · CD 5 · single enemy · power 22 (STR) · Light* — A holy strike that grows stronger as your wounds deepen (up to +100%).
- **Final Judgment** — *Level 60 · CD 8 · single enemy · power 38 (STR) · Light* — Colossal single-target holy damage that heals the whole party.

#### Templar — *The shield that does not break.*

- **Upgraded passive — Aegis Aura:** Your Strength is increased by 1 and Charisma by 2, and you take 10% less damage.

- **Aegis** — *Level 40 · CD 7 · whole party · Light* — The whole party is shielded, each absorbing up to 15% of your max HP.
- **Unbreakable Oath** — *Level 50 · CD 8 · self or ally · Light* — An ally cannot fall — the next lethal blow leaves them standing at 1 HP.
- **Bastion Eternal** — *Level 60 · CD 8 · whole party · Light* — Party damage taken -5 and 4% max-HP regen, for 4 turns.

### Warlock

#### Nethermancer — *Decay is a craft — perfect it.*

- **Upgraded passive — Soul Feast:** You heal for 15% of all damage you deal, and take 8% less damage.

- **Wither** — *Level 40 · CD 5 · single enemy · power 10 (LER) · Dark* — A wasting curse — the target rots for 12 damage per turn for 5 turns. — *Poison 12 dmg x 5 turns*
- **Feast of Shadows** — *Level 50 · CD 6 · all enemies · power 18 (LER) · Dark* — Tear at every enemy's shadow and heal for the total damage dealt.
- **Dominion of Dread** — *Level 60 · CD 8 · all enemies · Dark* — All enemies cower (-30% damage), taking +15% damage and decaying for 6 per turn.

#### Infernalist — *Feed the flame — it feeds you back.*

- **Upgraded passive — Infernal Vitality:** You heal for 10% of all damage you deal, and deal +10% fire and dark damage.

- **Hellfire** — *Level 40 · CD 5 · all enemies · power 16 (LER) · Fire* — Engulf all enemies in flame and leave them burning for 10 per turn. — *Blaze (10/turn) x 4 turns*
- **Searing Chains** — *Level 50 · CD 5 · single enemy · power 20 (LER) · Fire* — Bind an enemy in burning links — burning and slowed. — *Blaze (10/turn) x 4 turns · applies Slow*
- **Infernal Avatar** — *Level 60 · CD 8 · all enemies · power 16 (LER) · Fire* — Ascend in flame — +25% fire damage for 3 turns and a nova on all enemies.

### Barbarian

#### Berserker — *Pain is the only teacher you need.*

- **Upgraded passive — Pain Fury:** You take 15% less damage, and deal +10% damage while below half HP.

- **Bloodrage** — *Level 40 · CD 6 · self · Physical* — 50% lifesteal and +10% crit chance for 3 turns.
- **Rampage** — *Level 50 · CD 6 · all enemies · power 12 (STR) · Physical* — Five wild blows across random enemies. — *5 hits*
- **Undying Rage** — *Level 60 · CD 9 · self · Fire* — Strength +3, and the next lethal blow leaves you at 1 HP.

#### Juggernaut — *Slow, unstoppable, unbreakable.*

- **Upgraded passive — Unstoppable Hide:** You take 20% less damage, and your Constitution is increased by 2.

- **Unyielding** — *Level 40 · CD 6 · self · Physical* — Shake off every debuff and take 6 less damage for 3 turns.
- **Seismic Roar** — *Level 50 · CD 6 · all enemies · power 14 (STR) · Earth* — A ground-shaking roar — all enemies may be stunned and their armor sundered. — *60% stun chance · Sunder -3 armor for 3 turns*
- **Mountain Breaker** — *Level 60 · CD 7 · single enemy · power 34 (STR) · Earth* — A titanic single blow that mends 15% of your max HP.

---

## Heroines — Innate & Enhanced Skills

### Alice (Wonderland Heroine)

**Innate skills:**
- **Curious Inquiry** — *Offensive · CD 3 · single enemy · Magical* — Ask the wrong question. Increases enemy elemental weakness by 0.6 and reduces Wisdom by 3 for 3 turns. — *elemental weakness +0.6, Wisdom -3 for 3 turns*
- **Try Me** — *Defensive · CD 2 · self · Magical* — Drink or eat? Shrink (+30% dodge, 2 turns) or Grow (+30% damage, 2 turns). Random each use. — *Shrink! +30% dodge for 2 turns / Grow! +30% damage for 2 turns*

**Enhanced skills** — unlocked by equipping the *Vorpal Blade (Rusted → Restored)* (replaces the innate skills while equipped):
- **Vorpal Edge** — *Offensive · CD 2 · single enemy · power 12 (STR) · Light* — A swift, luminous slash. Deals physical+light damage with +30% crit chance. Critical hits deal 2.2x damage. — *+30% crit chance (2.2x damage)*
- **Snicker-Snack** — *Offensive · CD 4 · single enemy · power 18 (STR) · Light* — The blade sings its terrible song. Heavy damage, +50% damage vs Dragonkin and Storybook enemies. — *+50% dmg vs Dragonkin, Storybook*

**Upgrade skill** — granted by the Godmother's Blade facility upgrade:
- **Frabjous Day** — *Support · CD 5 · whole party · Light* — Callooh! Callay! The Vorpal Blade restored — party gains +25% damage for 2 turns. — *+25% damage for 2 turns*

---

### Red Hood (Wonderland Heroine)

**Innate skills:**
- **Hunter's Mark** — *Offensive · CD 3 · single enemy · Wind* — Mark your prey. Target takes +15% damage from all sources for 3 turns. — *target takes +15% damage for 3 turns*
- **What's in the Basket?** — *Support · CD 3 · self or ally · Earth* — Share provisions with an ally, restoring 25% of their max HP. — *heal 25% max HP*

**Enhanced skills** — unlocked by equipping the *Grandmother's Axe (Woodcutter's Broken Axe → Restored)* (replaces the innate skills while equipped):
- **What Big Teeth** — *Offensive · CD 3 · single enemy · power 10 (STR) · Dark* — The better to eat you with! +30% damage vs Beasts, applies Bleed (3 dmg x 3 turns). — *Bleed 3 dmg x 3 turns · +30% dmg vs Beast*
- **Fell the Wolf** — *Offensive · CD 4 · single enemy · power 14 (STR) · Physical* — A brutal overhead swing. +15% crit chance, ignores 20% of target's armor. — *+15% crit chance · ignores 20% armor*

**Upgrade skill** — granted by the Woodcutter's Axe facility upgrade:
- **Through the Forest** — *Support · CD 5 · whole party · Wind* — Grandmother's blessing shields the party. +20% crit chance and Fear immunity for 2 turns. — *+20% crit chance for 2 turns · Fear immunity for 2 turns*

---

### Dorothy (Wonderland Heroine)

**Innate skills:**
- **There's No Place Like Home** — *Support · CD 6 · whole party · Light* — Party-wide heal (25% max HP) + cleanse one debuff per ally. 6-turn cooldown. — *heal 25% max HP · cleanse 1 debuff*
- **Ruby Blink** — *Defensive · CD 3 · self · Magical* — Click your heels and vanish. +50% dodge for 1 turn. — *+50% dodge for 1 turn*

**Enhanced skills** — unlocked by equipping the *Silver Slippers → Ruby Slippers* (replaces the innate skills while equipped):
- **Cyclone's Call** — *Offensive · CD 4 · all enemies · power 10 (LER) · Wind* — Summon a twister! AoE wind damage and pushes enemies to bottom of initiative. — *enemies drop to initiative bottom*
- **Heart of Tin** — *Support · CD 3 · self or ally · Light* — A heart is not judged by how much you love. Heal 30% + cleanse 1 debuff on an ally. — *heal 30% max HP · cleanse 1 debuff*

**Upgrade skill** — granted by the Wizard's Slippers facility upgrade:
- **Emerald City's Light** — *Support · CD 6 · whole party · Light* — There's no place like home. Party cleanse ALL debuffs + heal 25%. — *heal 25% max HP · cleanse all debuffs*

---

### Palette (Chromatic Artisan)

**Innate skills:**
- **Brushstroke** — *Offensive · CD 0 · single enemy · power 5 (WIS)* — A stroke of her current color. (0.7x, current color's element) — *element matches Palette's current color*
- **Spectrum** — *Offensive · CD 3 · single enemy · power 0 (LER)* — Three splashes, each a random element. (3 x 0.3x) — *3 hits, each a random element*
- **Signature** — *Offensive · CD 4 · single enemy · power 0 (WIS)* — Begins painting the target's name — strikes NEXT turn for 2.5x, ignoring defense. (4-turn cooldown) — *strikes next turn for 2.5x, ignores defense*

> No skill swap — instead her Palette Brush grants elemental color stances.

---

## Monster Girls — Innate Skill Roster

| # | Monster Girl | Race | Level | Growth | Innate Skill 1 | Innate Skill 2 |
|---|--------------|------|-------|--------|----------------|----------------|
| 1 | Alraune Fledger ♀ | Fey | 7 | High | Root Strike | Nature's Embrace |
| 2 | Amazon Warrior ♀ | Human | 18 | Medium | Spear Thrust | Warrior Stance |
| 3 | Arachne Brood Queen ♀ | Beast | 38 | — | Brood Bite | Silk Shield |
| 4 | Arachne Weaver ♀ | Beast | 19 | Medium | Web Throw | Spider Dance |
| 5 | Automata Doll ♀ | Clockwork | 29 | Low | Clockwork Blade | Emergency Repair |
| 6 | Banshee Wailer ♀ | Undead | 18 | Medium | Wail of Sorrow | Death Shriek |
| 7 | Centaur Champion ♀ | Beast | 26 | Low | Champion's Charge | Stampede |
| 8 | Centaur Scout ♀ | Beast | 11 | High | Charge | Hoof Stomp |
| 9 | Cosmic Slime Empress ♀ | Elemental | 40 | — | Cosmic Blast | Gravity Well |
| 10 | Crimson Countess ♀ | Vampire | 24 | Low | Crimson Slash | Blood Ritual |
| 11 | Demon Whip Master ♀ | Demon | 24 | Low | Whip Lash | Dominating Presence |
| 12 | Draconic Valkyrie ♀ | Dragonkin | 33 | — | Dragon Breath | Valkyrie Strike |
| 13 | Dragon Goddess Avatar ♀ | Dragonkin | 37 | — | Starfire Breath | Divine Wings |
| 14 | Dryad Protector ♀ | Fey | 9 | High | Entangle | Forest Shield |
| 15 | Dullahan Knight ♀ | Undead | 22 | Medium | Headless Charge | Spectral Guard |
| 16 | Dusk Weaver ♀ | Shadow | 27 | Low | Twilight Lash | Veil of Dusk |
| 17 | Flame Heart ♀ | Dragonkin | 39 | — | Fireheart Eruption | Warmth of the Heart |
| 18 | Gargoyle Watcher ♀ | Construct | 16 | Medium | Stone Fist | Stone Skin |
| 19 | Gear Maiden ♀ | Gnome | 23 | Medium | Cog Storm | Overclock |
| 20 | Ghost Maid ♀ | Shadow | 10 | High | Spectral Strike | Phantom Barrier |
| 21 | Goblin Girl ♀ | Goblin | 2 | High | Goblin Dart | Goblin Evasion |
| 22 | Gorgon Petrifier ♀ | Lizardfolk | 28 | Low | Petrifying Gaze | Serpent Fang |
| 23 | Grave Queen ♀ | Undead | 50 | — | Grave Requiem | Soul Harvest |
| 24 | Harpy Scout ♀ | Beast | 5 | High | Harpy Swoop | Harpy Cry |
| 25 | Holstaur Brawler ♀ | Beast | 15 | Medium | Mighty Punch | Earthen Stomp |
| 26 | Infernal Bride ♀ | Demon | 47 | — | Hellfire Kiss | Dark Vows |
| 27 | Infernal Empress ♀ | Demon | 26 | Low | Infernal Flame | Empress Command |
| 28 | Kitsune Miko ♀ | Beast | 22 | Medium | Foxfire | Spirit Shield |
| 29 | Kobold Tinkerer ♀ | Dragonkin | 8 | High | Gadget Explosion | Tinker Enhancement |
| 30 | Lamia Constrictor ♀ | Lizardfolk | 13 | Medium | Constrict | Venom Fang |
| 31 | Lich Queen Avatar ♀ | Undead | 35 | — | Necrotic Bolt | Raise Dead |
| 32 | Lizard Queen ♀ | Lizardfolk | 14 | Medium | Royal Slash | Regenerate Scale |
| 33 | Maiden of Stone ♀ | Giant | 32 | — | Mountain Slam | Earthen Bulwark |
| 34 | Mermaid Siren Queen ♀ | Fey | 31 | — | Tidal Wave | Siren Lullaby |
| 35 | Mimic Girl ♀ | Abomination | 14 | Medium | Surprise Strike | Mimic Form |
| 36 | Minotaur Gladiator ♀ | Giant | 24 | Low | Colossal Slam | Gladiator Stance |
| 37 | Moth Girl Flutterer ♀ | Fey | 12 | Medium | Flutter Strike | Dust Cloud |
| 38 | Mummy Princess ♀ | Undead | 19 | Medium | Desert Curse | Pharaoh's Wrath |
| 39 | Neko Ninja ♀ | Beast | 18 | Medium | Shadow Clone | Ninja Strike |
| 40 | Ninetales Fox ♀ | Beast | 30 | Low | Sunfire Breath | Nine Tails Strike |
| 41 | Oni Bruiser ♀ | Demon | 20 | Medium | Oni Smash | Hellfire Roar |
| 42 | Salamander Dancer ♀ | Elemental | 21 | Medium | Flame Dance | Ember Shield |
| 43 | Scylla Wrecker ♀ | Abomination | 26 | Low | Tentacle Crush | Abyssal Pull |
| 44 | Seraph Ascendant ♀ | Angel | 42 | — | Holy Judgement | Celestial Hymn |
| 45 | Siren Empress ♀ | Fey | 23 | Low | Siren Call | Ocean Lullaby |
| 46 | Slime Girl ♀ | Elemental | 12 | Medium | Acidic Blob | Slime Absorption |
| 47 | Sphinx Riddler ♀ | Beast | 34 | — | Riddle Blast | Enigma Field |
| 48 | Star Court Dancer ♀ | Fey | 44 | — | Stardust Waltz | Star Court Ball |
| 49 | Succubus Seductress ♀ | Demon | 21 | Medium | Allure | Draining Kiss |
| 50 | Umbral Weaver ♀ | Shadow | 14 | Medium | Shadow Strike | Web Trap |
| 51 | Valkyrie Commander ♀ | Human | 36 | — | Commander's Slash | Rally |
| 52 | Vampire Matriarch ♀ | Vampire | 25 | Low | Matriarch's Bite | Dark Blessing |
| 53 | Vampire Seductress ♀ | Vampire | 16 | Medium | Blood Drain | Seductive Charm |
| 54 | War Sister ♀ | Orc | 25 | Medium | Bone Crusher | Bloodrage |
| 55 | Winter Fairy ♀ | Fey | 14 | Medium | Frost Bolt | Ice Shield |
| 56 | Yuki-onna ♀ | Elemental | 17 | Medium | Blizzard | Frozen Heart |

---

## Awakened Skills (wave 1)

Twelve girls can be **Awakened** at the House Lounge — **Lv 40**, **level cap 40**, **affection 150**, plus **1 Awakening Sigil** (max 5 Sigils per save). An awakening replaces both innate skills, carries over mastery/cooldown progress, and changes her displayed name (a chosen nickname still wins).

| Monster Girl | Awakened Name | Base kit → Awakened kit |
|---|---|---|
| Goblin Girl ♀ | Goblin Deadeye | Goblin Dart → **Lucky Volley** · Goblin Evasion → **Fortune's Veil** |
| Harpy Scout ♀ | Harpy Stormcaller | Harpy Cry → **Tempest Screech** · Harpy Swoop → **Skydive Strike** |
| Moth Girl Flutterer ♀ | Moth Girl Moonweaver | Dust Cloud → **Moonveil Dust** · Flutter Strike → **Moonlit Flurry** |
| Slime Girl ♀ | Mirror Slime | Slime Absorption → **Adaptive Membrane** · Acidic Blob → **Corrosive Deluge** |
| Automata Doll ♀ | Automata Prime | Emergency Repair → **Reboot Protocol** · Clockwork Blade → **Overclocked Edge** |
| Centaur Champion ♀ | Centaur Warlord | Stampede → **Rolling Thunder** · Champion's Charge → **Lance of the Gale** |
| Gorgon Petrifier ♀ | Gorgon Basilisk | Petrifying Gaze → **Medusa's Verdict** · Serpent Fang → **Basilisk Fang** |
| Mimic Girl ♀ | Grand Mimic | Mimic Form → **Perfect Mimicry** · Surprise Strike → **Perfect Ambush** |
| Gear Maiden ♀ | Gear Artificer | Overclock → **System Overdrive** · Cog Storm → **Cog Blizzard** |
| Dusk Weaver ♀ | Nightweaver | Veil of Dusk → **Duskfall Veil** · Twilight Lash → **Eclipse Lash** |
| Demon Whip Master ♀ | Demon Overseer | Dominating Presence → **Absolute Dominion** · Whip Lash → **Cruel Crack** |
| Dullahan Knight ♀ | Dullahan Sentinel | Spectral Guard → **Death's Vigil** · Headless Charge → **Headless Pursuit** |

**Awakened skill details:**

- **Lucky Volley** — *Offensive · CD 3 · all enemies · power 8 (DEX) · Water* — A fistful of lucky darts peppers every enemy with poison. — *Poison 2 dmg x 3 turns*
- **Fortune's Veil** — *Defensive · CD 4 · whole party · Wind* — A mantle of small fortunes — 60% dodge for herself, 15% for the party. — *+60% dodge for 2 turns · +15% dodge for 2 turns*
- **Tempest Screech** — *Offensive · CD 4 · all enemies · power 10 (DEX) · Wind* — A storm-borne scream that tears through every enemy and throws them off balance. — *enemies drop to initiative bottom*
- **Skydive Strike** — *Offensive · CD 3 · single enemy · power 12 (DEX) · Wind* — A plummeting dive that can knock a foe senseless. — *25% stun chance*
- **Moonveil Dust** — *Support · CD 4 · all enemies · Dark* — Lunar dust blinds every enemy (75% miss, 3t) and marks them for the hunt. — *Blind (75% miss) for 3 turns · target takes +10% damage for 3 turns*
- **Moonlit Flurry** — *Offensive · CD 3 · single enemy · power 7 (DEX) · Dark* — Two pale wingbeats that leave the target's eyes full of moonlight. — *2 hits · Blind (30% miss) x 2 turns*
- **Adaptive Membrane** — *Defensive · CD 5 · self · Water* — The membrane absorbs 40% of damage taken and reflects 30% of it back. — *absorbs 40% of damage for 2 turns · reflect 30% of damage back for 2 turns*
- **Corrosive Deluge** — *Offensive · CD 3 · single enemy · power 10 (CON) · Water* — A torrent of acid that poisons and eats away at armour. — *Poison 3 dmg x 3 turns · Expose -1 armor*
- **Reboot Protocol** — *Support · CD 5 · self · Magical* — A fatal blow triggers an emergency reboot — revive at 30% HP (once, 3t). — *survive lethal at 1 HP, once for 3 turns*
- **Overclocked Edge** — *Offensive · CD 3 · single enemy · power 9 (DEX) · Thunder* — Two arc-blade strikes, each discharging a shock. — *Shock 4 dmg x 3 turns · 2 hits*
- **Rolling Thunder** — *Offensive · CD 5 · all enemies · power 12 (STR) · Earth* — A thundering trample that shatters the armour of every foe. — *Expose -2 armor*
- **Lance of the Gale** — *Offensive · CD 4 · single enemy · power 15 (STR) · Wind* — A gale-driven lance thrust that ignores armour and bites deep. — *+15% crit chance · ignores armor*
- **Medusa's Verdict** — *Support · CD 5 · single enemy · Earth* — A petrifying stare — stuns, with a 35% chance to entomb the target in stone. — *Stun for 2 turns · Entomb for 2 turns*
- **Basilisk Fang** — *Offensive · CD 3 · single enemy · power 11 (DEX) · Water* — Venomous fangs that leave slowing venom in the wound. — *Poison 6 dmg x 4 turns · applies Slow*
- **Perfect Mimicry** — *Defensive · CD 5 · self · Dark* — Mimic the last element that struck her — +25% damage and +50% resistance to it. — *adapts to the last element that struck her (+dmg/+res)*
- **Perfect Ambush** — *Offensive · CD 3 · single enemy · power 12 (STR) · Dark* — A guaranteed critical strike that hits even harder against untouched foes. — *guaranteed crit · +30% dmg vs foes above 80% HP*
- **System Overdrive** — *Support · CD 5 · self or ally · Thunder* — Overdrive an ally — +40% next action and −1 turn on all their cooldowns. — *next action +40% power · all active cooldowns -1*
- **Cog Blizzard** — *Offensive · CD 4 · all enemies · power 10 (LER) · Thunder* — A blizzard of razor cogs tears across every enemy. — *15% stun chance*
- **Duskfall Veil** — *Defensive · CD 4 · self or ally · Dark* — A veil of dusk that turns aside blows — and answers each dodge with a counter. — *+35% dodge for 3 turns · counter-attacks after dodging (50%) for 3 turns*
- **Eclipse Lash** — *Offensive · CD 3 · single enemy · power 12 (DEX) · Dark* — A whip of eclipse-dark that opens deep wounds, striking harder into bleeding foes. — *Bleed 5 dmg x 4 turns · +25% dmg vs bleeding foes*
- **Absolute Dominion** — *Support · CD 5 · all enemies · Dark* — Crush the will of every foe — strength savaged and fear sown. — *Strength -2 for 3 turns · Fear (deals -30% damage) for 2 turns*
- **Cruel Crack** — *Offensive · CD 3 · single enemy · power 11 (DEX) · Fire* — A whip crack that weakens and leaves the wound bleeding. — *Bleed 4 dmg x 3 turns · applies Weaken*
- **Death's Vigil** — *Defensive · CD 4 · self or ally · Dark* — A guardian's oath — heavy damage reduction and a death ward for the watch. — *damage taken -35% for 2 turns · survive lethal at 1 HP, once for 3 turns*
- **Headless Pursuit** — *Offensive · CD 4 · single enemy · power 13 (STR) · Dark* — An unrelenting charge that ignores armour and fills the target with fear. — *ignores armor · Fear (-30% damage) x 2 turns*

---

## Innate Skill Details (Dictionary)

Alphabetical reference for every monster-girl innate skill in the roster above. Heroine skills are detailed in their own sections.

- **Abyssal Pull** — *Offensive · CD 4 · all enemies · power 11 (STR) · Water* — Drag all enemies into the crushing deep. — *25% stun chance*
- **Acidic Blob** — *Offensive · CD 2 · single enemy · power 8 (CON) · Water* — Throw acidic slime at an enemy.
- **Allure** — *Support · CD 3 · single enemy · Dark* — Bewitch an enemy, stunning them and reducing their will. — *Stun for 2 turns*
- **Blizzard** — *Offensive · CD 4 · all enemies · power 13 (LER) · Water* — Unleash a blizzard on all enemies.
- **Blood Drain** — *Offensive · CD 3 · single enemy · power 10 (WIS) · Dark* — Drain blood to heal yourself. — *heal 50% of damage dealt*
- **Blood Ritual** — *Support · CD 5 · whole party · power 10 (CHA) · Dark* — Sacrifice a sliver of health to heal the party.
- **Bloodrage** — *Defensive · CD 4 · self · Fire* — Enter a battle frenzy, gaining increased damage. — *+30% damage for 2 turns*
- **Bone Crusher** — *Offensive · CD 3 · single enemy · power 16 (STR) · Physical* — A bone-shattering blow that weakens the foe. — *applies Weaken*
- **Brood Bite** — *Offensive · CD 2 · single enemy · power 10 (DEX) · Water* — Bite an enemy with venomous brood fangs. — *Poison 5 dmg x 4 turns*
- **Celestial Hymn** — *Support · CD 5 · whole party · Light* — Sing a hymn that heals the party and cleanses a debuff from each ally. — *heal 20% max HP · cleanse 1 debuff*
- **Champion's Charge** — *Offensive · CD 3 · single enemy · power 14 (STR) · Wind* — Charge forward with the speed of a gale. — *ignores armor*
- **Charge** — *Offensive · CD 3 · single enemy · power 12 (STR) · Physical* — Rush forward and strike an enemy.
- **Clockwork Blade** — *Offensive · CD 2 · single enemy · power 12 (DEX) · Thunder* — Extend an arm-blade with clockwork precision, discharging a shock. — *Shock 4 dmg x 3 turns*
- **Cog Storm** — *Offensive · CD 3 · single enemy · power 13 (LER) · Thunder* — Hurl a vortex of razor-sharp cogs at an enemy. — *25% stun chance*
- **Colossal Slam** — *Offensive · CD 3 · single enemy · power 18 (STR) · Earth* — Bring down a massive strike that shakes the earth.
- **Commander's Slash** — *Offensive · CD 2 · single enemy · power 12 (STR) · Physical* — A precise slash befitting a commander.
- **Constrict** — *Support · CD 3 · single enemy · Physical* — Wrap around an enemy, immobilizing them. — *Stun for 2 turns*
- **Cosmic Blast** — *Offensive · CD 4 · all enemies · power 15 (LER) · Magical* — Unleash a blast of cosmic energy.
- **Crimson Slash** — *Offensive · CD 2 · single enemy · power 12 (DEX) · Dark* — A swift, bloody slash aimed at a vital point. — *guaranteed crit*
- **Dark Blessing** — *Support · CD 5 · whole party · Dark* — Bathe the party in vampiric vitality. — *regenerate 8% max HP for 4 turns*
- **Dark Vows** — *Support · CD 5 · whole party · Dark* — Bind the party with infernal vows of strength and passion. — *Strength +3 for 2 turns · Charisma +3 for 2 turns*
- **Death Shriek** — *Offensive · CD 4 · all enemies · power 13 (CHA) · Dark* — Unleash a shriek of death.
- **Desert Curse** — *Offensive · CD 4 · all enemies · power 10 (LER) · Earth* — Curse all enemies with ancient maledictions. — *Strength -2 for 3 turns*
- **Divine Wings** — *Defensive · CD 4 · self · Light* — Wrap yourself in divine wings of protection. — *+35% dodge for 3 turns*
- **Dominating Presence** — *Support · CD 4 · all enemies · Dark* — Assert dominance, weakening all foes. — *Strength -2 for 3 turns*
- **Dragon Breath** — *Offensive · CD 4 · all enemies · power 14 (STR) · Fire* — Exhale a gout of dragon flame. — *Burn (6/turn) x 3 turns*
- **Draining Kiss** — *Offensive · CD 3 · single enemy · power 12 (CHA) · Dark* — Steal life force with a kiss. — *heal 50% of damage dealt*
- **Dust Cloud** — *Support · CD 3 · all enemies · Earth* — Blind enemies with magical dust. — *Blind (50% miss) for 2 turns*
- **Earthen Bulwark** — *Defensive · CD 5 · whole party · Earth* — Raise walls of living stone to shield the party. — *damage taken -25% for 2 turns*
- **Earthen Stomp** — *Offensive · CD 3 · all enemies · power 10 (STR) · Earth* — Stomp with earthen power.
- **Ember Shield** — *Defensive · CD 3 · self · Fire* — Wreathe yourself in protective flames. — *damage taken -25% for 3 turns*
- **Emergency Repair** — *Support · CD 4 · self · Magical* — Activate self-repair protocols to restore health. — *regenerate 20% max HP for 2 turns*
- **Empress Command** — *Support · CD 4 · all enemies · Dark* — Command enemies to kneel, instilling fear and weakness. — *Strength -2 for 3 turns*
- **Enigma Field** — *Support · CD 4 · all enemies · Magical* — Confuse all enemies with riddles. — *Confusion (30%) for 2 turns*
- **Entangle** — *Support · CD 3 · all enemies · Earth* — Bind enemies in vines. — *Slow for 3 turns*
- **Fireheart Eruption** — *Offensive · CD 4 · single enemy · power 17 (STR) · Fire* — Unleash the flame of a dragon's heart upon one foe. — *Blaze (10/turn) x 3 turns*
- **Flame Dance** — *Offensive · CD 2 · single enemy · power 10 (DEX) · Fire* — Dance through the battlefield, leaving flames in your wake. — *Burn (6/turn) x 3 turns*
- **Flutter Strike** — *Offensive · CD 2 · single enemy · power 8 (DEX) · Wind* — Delicate yet damaging strike.
- **Forest Shield** — *Defensive · CD 4 · whole party · Earth* — Protect allies with nature's barrier. — *damage taken -20% for 2 turns*
- **Foxfire** — *Offensive · CD 2 · single enemy · power 11 (WIS) · Fire* — Launch a bolt of spiritual foxfire. — *Burn (6/turn) x 3 turns*
- **Frost Bolt** — *Offensive · CD 2 · single enemy · power 10 (LER) · Water* — Fire a bolt of freezing energy.
- **Frozen Heart** — *Defensive · CD 4 · self · Water* — Freeze your heart for power and protection. — *damage taken -35% for 3 turns*
- **Gadget Explosion** — *Offensive · CD 3 · single enemy · power 14 (LER) · Fire* — Detonate a gadget for massive damage to one target.
- **Gladiator Stance** — *Defensive · CD 4 · self · Physical* — Assume an unbreakable battle stance. — *damage taken -35% for 3 turns*
- **Goblin Dart** — *Offensive · CD 2 · single enemy · power 6 (DEX) · Water* — Quick dart attack with a 50% chance to apply poison. — *Poison 2 dmg x 3 turns*
- **Goblin Evasion** — *Defensive · CD 3 · self · Wind* — Dodge incoming attacks with Goblin agility. — *+60% dodge for 2 turns*
- **Grave Requiem** — *Offensive · CD 4 · all enemies · power 15 (CHA) · Dark* — A funeral dirge that drains the strength of the living. — *Strength -2 for 3 turns*
- **Gravity Well** — *Support · CD 4 · all enemies · Magical* — Create a gravity well that slows enemies. — *Slow for 3 turns*
- **Harpy Cry** — *Offensive · CD 3 · all enemies · power 8 (CHA) · Wind* — Screech loudly, damaging all enemies.
- **Harpy Swoop** — *Offensive · CD 2 · single enemy · power 10 (DEX) · Wind* — Dive down and strike an enemy.
- **Headless Charge** — *Offensive · CD 3 · single enemy · power 13 (STR) · Dark* — Charge at an enemy with reckless, armor-shattering force. — *ignores armor*
- **Hellfire Kiss** — *Offensive · CD 3 · single enemy · power 15 (CHA) · Fire* — A burning kiss that sears the soul and steals its fire. — *Blaze (10/turn) x 3 turns · heal 50% of damage dealt*
- **Hellfire Roar** — *Offensive · CD 4 · all enemies · power 12 (STR) · Fire* — Roar a wave of hellfire that scorches all enemies. — *Burn (6/turn) x 3 turns*
- **Holy Judgement** — *Offensive · CD 3 · single enemy · power 16 (CHA) · Light* — Smite a foe with divine wrath. — *guaranteed crit*
- **Hoof Stomp** — *Offensive · CD 3 · all enemies · power 9 (STR) · Earth* — Stomp the ground, hitting all enemies.
- **Ice Shield** — *Defensive · CD 3 · self · Water* — Create a shield of ice. — *damage taken -30% for 2 turns*
- **Infernal Flame** — *Offensive · CD 4 · all enemies · power 15 (STR) · Fire* — Unleash a torrent of infernal fire upon all foes. — *Blaze (10/turn) x 3 turns*
- **Matriarch's Bite** — *Offensive · CD 3 · single enemy · power 12 (CHA) · Dark* — Sink fangs deep and drain life while weakening the victim. — *applies Weaken · heal 50% of damage dealt*
- **Mighty Punch** — *Offensive · CD 2 · single enemy · power 14 (STR) · Physical* — A powerful physical punch.
- **Mimic Form** — *Defensive · CD 4 · self · Magical* — Temporarily mimic an ally's form for defense. — *damage taken -30% for 2 turns*
- **Mountain Slam** — *Offensive · CD 3 · single enemy · power 17 (STR) · Earth* — Crush a foe beneath the weight of a mountain. — *25% stun chance*
- **Nature's Embrace** — *Support · CD 4 · whole party · power 12 (WIS) · Earth* — Heal self and nearby allies moderately.
- **Necrotic Bolt** — *Offensive · CD 3 · single enemy · power 18 (LER) · Dark* — Hurl a bolt of pure necrotic energy.
- **Nine Tails Strike** — *Offensive · CD 3 · single enemy · power 8 (WIS) · Magical* — Strike with all nine tails at once. — *3 hits*
- **Ninja Strike** — *Offensive · CD 1 · single enemy · power 9 (DEX) · Wind* — A swift ninja strike.
- **Ocean Lullaby** — *Support · CD 3 · self or ally · power 18 (WIS) · Water* — Sing a soothing melody that heals an ally.
- **Oni Smash** — *Offensive · CD 3 · single enemy · power 16 (STR) · Fire* — Smash an enemy with demonic strength. — *guaranteed crit*
- **Overclock** — *Support · CD 4 · self or ally · Thunder* — Overclock an ally's next action for increased power. — *next action +40% power*
- **Petrifying Gaze** — *Support · CD 4 · single enemy · Earth* — Turn an enemy to stone with a single glance. — *Stun for 2 turns*
- **Phantom Barrier** — *Defensive · CD 3 · self or ally · Dark* — Create a protective barrier around an ally. — *damage taken -35% for 2 turns*
- **Pharaoh's Wrath** — *Offensive · CD 3 · single enemy · power 14 (WIS) · Dark* — Unleash the vengeance of a fallen dynasty upon one foe. — *ignores armor*
- **Raise Dead** — *Support · CD 6 · fallen ally · power 10 (WIS) · Dark* — Revive a fallen ally with unholy power — 30% of their HP, rising to 50% with mastery. — *revive at 35% HP*
- **Rally** — *Support · CD 5 · whole party · power 8 (STR) · Light* — Rally the party, raising their strength and healing them. — *Strength +2 for 3 turns*
- **Regenerate Scale** — *Support · CD 4 · self · Earth* — Restore health through scale regeneration. — *regenerate 15% max HP for 3 turns*
- **Riddle Blast** — *Offensive · CD 3 · single enemy · power 14 (LER) · Magical* — Unleash a blast of puzzling arcane energy.
- **Root Strike** — *Offensive · CD 2 · single enemy · power 9 (WIS) · Earth* — Attack with magical roots.
- **Royal Slash** — *Offensive · CD 2 · single enemy · power 13 (STR) · Physical* — A majestic and powerful slash.
- **Seductive Charm** — *Support · CD 4 · single enemy · Dark* — Charm an enemy to reduce their damage. — *Strength -3 for 2 turns*
- **Serpent Fang** — *Offensive · CD 2 · single enemy · power 10 (DEX) · Water* — Strike with venomous snake fangs. — *Poison 4 dmg x 4 turns*
- **Shadow Clone** — *Defensive · CD 4 · self · Dark* — Create a shadow clone to confuse enemies. — *+40% dodge for 2 turns*
- **Shadow Strike** — *Offensive · CD 2 · single enemy · power 10 (DEX) · Dark* — Strike from darkness. — *guaranteed crit*
- **Silk Shield** — *Defensive · CD 3 · self or ally · Earth* — Weave a shield of silk around an ally. — *damage taken -30% for 3 turns*
- **Siren Call** — *Offensive · CD 4 · all enemies · power 12 (CHA) · Water* — Lure enemies with a haunting song. — *25% stun chance*
- **Siren Lullaby** — *Support · CD 5 · whole party · power 12 (WIS) · Water* — Sing a soothing song that heals all allies.
- **Slime Absorption** — *Defensive · CD 4 · self · Water* — Absorb damage as health. — *absorbs 40% of damage for 2 turns*
- **Soul Harvest** — *Offensive · CD 3 · single enemy · power 17 (WIS) · Dark* — Tear the soul from a living foe, bypassing its defenses to feed the queen. — *ignores armor · heal 50% of damage dealt*
- **Spear Thrust** — *Offensive · CD 2 · single enemy · power 12 (STR) · Physical* — A precise spear thrust.
- **Spectral Guard** — *Defensive · CD 3 · self or ally · Dark* — Summon spectral protectors to shield an ally. — *damage taken -35% for 2 turns*
- **Spectral Strike** — *Offensive · CD 2 · single enemy · power 10 (WIS) · Dark* — Pass through defenses to strike an enemy. — *ignores armor*
- **Spider Dance** — *Support · CD 4 · all enemies · Dark* — Perform a hypnotic spider dance. — *Confusion (30%) for 2 turns*
- **Spirit Shield** — *Defensive · CD 4 · self · Light* — Call upon fox spirits to guard you. — *damage taken -30% for 3 turns*
- **Stampede** — *Offensive · CD 4 · all enemies · power 11 (STR) · Earth* — Trample the ground, striking all enemies.
- **Star Court Ball** — *Support · CD 5 · whole party · Magical* — Lead the party in a dance that sharpens their grace. — *Dexterity +3 for 3 turns*
- **Stardust Waltz** — *Offensive · CD 4 · all enemies · power 13 (DEX) · Magical* — Whirl through enemies in a storm of static stardust. — *Shock 6 dmg x 3 turns*
- **Starfire Breath** — *Offensive · CD 4 · all enemies · power 16 (STR) · Fire* — Exhale a torrent of starfire that burns all foes. — *Blaze (10/turn) x 3 turns*
- **Stone Fist** — *Offensive · CD 2 · single enemy · power 12 (STR) · Earth* — Strike with fists of stone.
- **Stone Skin** — *Defensive · CD 4 · self · Earth* — Harden your skin like stone. — *damage taken -40% for 2 turns*
- **Sunfire Breath** — *Offensive · CD 4 · all enemies · power 13 (WIS) · Fire* — Exhale a wave of burning sunfire. — *Blaze (10/turn) x 3 turns*
- **Surprise Strike** — *Offensive · CD 2 · single enemy · power 11 (STR) · Dark* — Strike when least expected. — *guaranteed crit*
- **Tentacle Crush** — *Offensive · CD 3 · single enemy · power 13 (STR) · Water* — Crush a foe with writhing tentacles. — *applies Slow*
- **Tidal Wave** — *Offensive · CD 4 · all enemies · power 14 (WIS) · Water* — Call forth a crushing wave upon all enemies.
- **Tinker Enhancement** — *Support · CD 4 · self or ally · Thunder* — Enhance an ally's next action for increased power. — *next action +25% power*
- **Twilight Lash** — *Offensive · CD 2 · single enemy · power 12 (DEX) · Dark* — Lash with threads of dusk that cut like wire. — *Bleed 3 dmg x 3 turns*
- **Valkyrie Strike** — *Offensive · CD 3 · single enemy · power 15 (STR) · Light* — A spear strike that pierces all defenses. — *ignores armor*
- **Veil of Dusk** — *Defensive · CD 3 · self or ally · Dark* — Weave dusk into a veil that hides an ally from harm. — *+35% dodge for 2 turns*
- **Venom Fang** — *Offensive · CD 2 · single enemy · power 9 (DEX) · Water* — Strike with venomous fangs. — *Poison 3 dmg x 4 turns*
- **Wail of Sorrow** — *Offensive · CD 3 · all enemies · power 11 (CHA) · Dark* — A mournful wail that damages all enemies.
- **Warmth of the Heart** — *Support · CD 4 · self or ally · Fire* — Share a dragon's inner fire, restoring an ally's health. — *heal 30% max HP*
- **Warrior Stance** — *Defensive · CD 3 · self · Physical* — Assume a defensive warrior stance. — *damage taken -25% for 3 turns*
- **Web Throw** — *Offensive · CD 2 · all enemies · power 7 (DEX) · Earth* — Throw webs at enemies.
- **Web Trap** — *Support · CD 3 · all enemies · Earth* — Trap enemies in webs. — *Slow for 3 turns*
- **Whip Lash** — *Offensive · CD 2 · single enemy · power 10 (DEX) · Fire* — Lash an enemy with a cruel whip, weakening them. — *applies Weaken*

---

## Learnable Skills (Barracks)

Taught at the **Barracks** → "Teach Ally Skill". Pick an ally and a category (Offensive / Defensive / Support), then choose a skill to start learning. The ally gains learning EXP in combat; when the EXP bar fills, the skill is learned. Allies can hold **3 learned skills** at once (replacing a learned skill to start a new one) and learn only **1 skill at a time**.

**Tier ladder:**

| Tier | Name | EXP to Learn | Required Ally Level | Required Level Cap |
|------|------|--------------|---------------------|--------------------|
| I | Novice | 300 | 1 | — |
| II | Adept | 800 | 8 | — |
| III | Veteran | 2000 | 16 | 20 |
| IV | Master | 5000 | 25 | 30 |
| V | Elite | 10000 | 35 | 40 |
| VI | Legend | 20000 | 45 | 50 |

**Mastery:** each time a skill is used, its mastery grows — shown as ★ / ★★ / ★★★ / ✦ / ✦✦. Thresholds are 10/25/50/90/150 uses. ★★★ unlocks bonus effects, ✦ (mastery 4) adds +1 turn to effect durations, and ✦✦ (mastery 5) raises power, status potency, and total cooldown reduction to −2. Burn skills upgrade their burn tier instead: +1 tier at ★★★, +2 tiers at ✦✦ (capped at Conflagration).

### Offensive Skills (17)

- **Arcane Bolt** — *Tier I Novice · Offensive · CD 2 · single enemy · power 10 (LER) · Magical* — Fire a bolt of pure magic. — *mastery at 10/25/50/90/150 uses*
- **Quick Strike** — *Tier I Novice · Offensive · CD 1 · single enemy · power 6 (DEX) · Wind* — A fast, nimble attack. — *mastery at 10/25/50/90/150 uses*
- **Slash** — *Tier I Novice · Offensive · CD 2 · single enemy · power 8 (STR) · Physical* — A basic melee slash. — *mastery at 10/25/50/90/150 uses*
- **Fireball** — *Tier II Adept · Offensive · CD 3 · single enemy · power 14 (LER) · Fire* — Hurl a ball of flame at a single enemy. — *mastery at 10/25/50/90/150 uses*
- **Poison Strike** — *Tier II Adept · Offensive · CD 3 · single enemy · power 8 (DEX) · Water* — Strike with poison. Target takes damage over time. — *Poison 4 dmg x 4 turns · mastery at 10/25/50/90/150 uses*
- **Power Strike** — *Tier II Adept · Offensive · CD 3 · single enemy · power 12 (STR) · Physical* — A strong downward strike. — *mastery at 10/25/50/90/150 uses*
- **Ice Shards** — *Tier III Veteran · Offensive · CD 4 · all enemies · power 10 (LER) · Water* — Launch sharp ice projectiles at all enemies. — *mastery at 10/25/50/90/150 uses*
- **Multi Hit** — *Tier III Veteran · Offensive · CD 4 · single enemy · power 6 (DEX) · Physical* — Strike 3 times in quick succession. — *3 hits · mastery at 10/25/50/90/150 uses*
- **Whirlwind** — *Tier III Veteran · Offensive · CD 4 · all enemies · power 9 (STR) · Wind* — Spin and hit all enemies. — *mastery at 10/25/50/90/150 uses*
- **Annihilate** — *Tier IV Master · Offensive · CD 5 · single enemy · power 25 (STR) · Dark* — A devastating blow that shatters the target's defenses. — *mastery at 10/25/50/90/150 uses*
- **Inferno** — *Tier IV Master · Offensive · CD 5 · all enemies · power 18 (LER) · Fire* — Unleash a torrent of flame that scorches all enemies. — *Blaze (10/turn) x 3 turns · mastery at 10/25/50/90/150 uses*
- **Shadow Dance** — *Tier IV Master · Offensive · CD 5 · single enemy · power 12 (DEX) · Dark* — Strike from the shadows twice, ignoring armor. — *ignores armor · 2 hits · mastery at 10/25/50/90/150 uses*
- **Glacial Requiem** — *Tier V Elite · Offensive · CD 6 · all enemies · power 18 (LER) · Water* — A requiem of ice that slows all enemies for 3 turns. — *applies Slow · mastery at 10/25/50/90/150 uses*
- **Rend** — *Tier V Elite · Offensive · CD 6 · single enemy · power 10 (DEX) · Physical* — Tear into an enemy three times, leaving a bleeding wound. — *Bleed 12 dmg x 4 turns · 3 hits · mastery at 10/25/50/90/150 uses*
- **Thunderfall** — *Tier V Elite · Offensive · CD 6 · all enemies · power 20 (LER) · Thunder* — Call down a storm of lightning that shocks all enemies. — *Shock 12 dmg x 3 turns · mastery at 10/25/50/90/150 uses*
- **Judgment** — *Tier VI Legend · Offensive · CD 7 · all enemies · power 22 (LER) · Light* — Call down radiant light on all enemies. Deals bonus damage to Undead and Abominations. — *+30% dmg vs Undead, Abomination · mastery at 10/25/50/90/150 uses*
- **Worldbreaker** — *Tier VI Legend · Offensive · CD 7 · single enemy · power 24 (STR) · Earth* — Smash an enemy twice with earth-shattering force, piercing half its armor. — *ignores 50% armor · 2 hits · mastery at 10/25/50/90/150 uses*

### Defensive Skills (12)

- **Dodge** — *Tier I Novice · Defensive · CD 3 · self · Wind* — Gain +2 Dexterity and evade 50% of attacks for 2 turns. — *+50% dodge, +2 DEX for 2 turns · mastery at 10/25/50/90/150 uses*
- **Protect** — *Tier I Novice · Defensive · CD 3 · self · Earth* — Reduce damage taken by 30% for 2 turns. — *damage taken -30% for 2 turns · mastery at 10/25/50/90/150 uses*
- **Hardened Skin** — *Tier II Adept · Defensive · CD 4 · self · Earth* — Strengthen your body, taking 25% less damage for 3 turns. — *damage taken -25% for 3 turns · mastery at 10/25/50/90/150 uses*
- **Shield Wall** — *Tier II Adept · Defensive · CD 4 · self or ally · Earth* — Grant yourself or an ally 40% damage reduction for 2 turns. — *damage taken -40% for 2 turns · mastery at 10/25/50/90/150 uses*
- **Counter** — *Tier III Veteran · Defensive · CD 3 · self · Physical* — Parry and riposte. Reflect 40% of damage taken back to attacker. — *reflect 40% of damage back for 2 turns · mastery at 10/25/50/90/150 uses*
- **Perfect Guard** — *Tier IV Master · Defensive · CD 4 · self · Light* — Fortify your stance. Take 60% less damage and reflect 30% for 2 turns. — *damage taken -60%, reflect 30% for 2 turns · mastery at 10/25/50/90/150 uses*
- **Phantom Dodge** — *Tier IV Master · Defensive · CD 4 · self · Dark* — Become a phantom. Evade 75% of attacks and gain +3 Dexterity for 2 turns. — *evade 75% of attacks, +3 DEX for 2 turns · mastery at 10/25/50/90/150 uses*
- **Aegis Shell** — *Tier V Elite · Defensive · CD 6 · self or ally · Magical* — Wrap yourself or an ally in a barrier that absorbs damage equal to 30% of your max HP. — *absorbs 30% of caster's max HP for 3 turns · mastery at 10/25/50/90/150 uses*
- **Bulwark** — *Tier V Elite · Defensive · CD 6 · whole party · Earth* — Brace the whole party, reducing damage taken by 30% for 2 turns. — *damage taken -30% for 2 turns · mastery at 10/25/50/90/150 uses*
- **Guardian's Vow** — *Tier VI Legend · Defensive · CD 8 · whole party · Earth* — A vow that shields the whole party, reducing damage taken by 40% for 3 turns. — *damage taken -40% for 3 turns · mastery at 10/25/50/90/150 uses*
- **Indomitable** — *Tier VI Legend · Defensive · CD 7 · self · Light* — Refuse to fall. Take 80% less damage for 2 turns. — *damage taken -80% for 2 turns · mastery at 10/25/50/90/150 uses*
- **Undying Vow** — *Tier VI Legend · Defensive · CD 9 · whole party · Light* — Vow that no ally shall fall — the first lethal blow each ally takes leaves them at 1 HP instead. — *survive lethal at 1 HP, once for 3 turns · mastery at 10/25/50/90/150 uses*

### Support Skills (18)

- **Heal** — *Tier I Novice · Support · CD 3 · self or ally · power 16 (WIS) · Light* — Restore health to yourself or an ally. — *mastery at 10/25/50/90/150 uses*
- **Slow** — *Tier I Novice · Support · CD 3 · single enemy · Water* — Reduce an enemy's speed and attack frequency for 3 turns. — *Slow for 3 turns · mastery at 10/25/50/90/150 uses*
- **Strength Buff** — *Tier I Novice · Support · CD 3 · self or ally · Physical* — Increase an ally's Strength for 3 turns. The bonus starts at +2 and grows with the caster's level. — *Strength +2 (scales) for 3 turns · mastery at 10/25/50/90/150 uses*
- **Group Heal** — *Tier II Adept · Support · CD 5 · whole party · power 10 (WIS) · Light* — Restore health to all allies. — *mastery at 10/25/50/90/150 uses*
- **Regenerate** — *Tier II Adept · Support · CD 4 · self or ally · Earth* — Grant an ally 10% HP recovery each turn for 4 turns. — *regenerate 10% max HP for 4 turns · mastery at 10/25/50/90/150 uses*
- **Weakening Curse** — *Tier II Adept · Support · CD 3 · single enemy · Dark* — Reduce an enemy's Strength for 3 turns. The penalty starts at -2 and grows with the caster's level. — *Strength -2 (scales) for 3 turns · mastery at 10/25/50/90/150 uses*
- **Blind** — *Tier III Veteran · Support · CD 3 · single enemy · Dark* — Reduce an enemy's accuracy. 40% chance to miss attacks for 3 turns. — *Blind (40% miss) for 3 turns · mastery at 10/25/50/90/150 uses*
- **Haste** — *Tier III Veteran · Support · CD 4 · self or ally · Thunder* — Grant an ally -2 cooldown on next skill use for 2 turns. — *next skill cooldown -2 for 2 turns · mastery at 10/25/50/90/150 uses*
- **Wisdom Buff** — *Tier III Veteran · Support · CD 3 · self or ally · Magical* — Increase an ally's Wisdom for 3 turns. The bonus starts at +2 and grows with the caster's level. — *Wisdom +2 (scales) for 3 turns · mastery at 10/25/50/90/150 uses*
- **Aura of Despair** — *Tier IV Master · Support · CD 5 · all enemies · Dark* — Drain the enemy's will. All enemies take +15% damage for 3 turns. — *target takes +15% damage for 3 turns · mastery at 10/25/50/90/150 uses*
- **Heroic Onslaught** — *Tier IV Master · Support · CD 5 · whole party · Fire* — Raise the party's Strength for 3 turns. The bonus starts at +3 and grows with the caster's level. — *Strength +3 (scales) for 3 turns · mastery at 10/25/50/90/150 uses*
- **Mass Regenerate** — *Tier IV Master · Support · CD 5 · whole party · Earth* — Grant all allies 8% HP recovery each turn for 3 turns. — *regenerate 8% max HP for 3 turns · mastery at 10/25/50/90/150 uses*
- **Benediction** — *Tier V Elite · Support · CD 5 · self or ally · power 30 (WIS) · Light* — Restore a large amount of health to yourself or an ally. — *mastery at 10/25/50/90/150 uses*
- **Cleansing Chorus** — *Tier V Elite · Support · CD 6 · whole party · power 12 (WIS) · Light* — Heal the whole party and cleanse all debuffs. — *cleanse all debuffs · mastery at 10/25/50/90/150 uses*
- **Phoenix Call** — *Tier V Elite · Support · CD 8 · fallen ally · Light* — Call a fallen ally back to their feet with 20% of their HP — rising to 35% with mastery. — *revive at 30% HP · mastery at 10/25/50/90/150 uses*
- **Astral Haste** — *Tier VI Legend · Support · CD 8 · whole party · Thunder* — The party moves like starlight — +3 initiative and next-skill cooldowns reduced by 1 for 3 turns. — *haste (+3 init, -1 CD) for 3 turns · mastery at 10/25/50/90/150 uses*
- **Fate's Favor** — *Tier VI Legend · Support · CD 7 · whole party · Fire* — The party deals +15% damage for 3 turns. — *+15% damage for 3 turns · mastery at 10/25/50/90/150 uses*
- **Radiant Rebirth** — *Tier VI Legend · Support · CD 9 · fallen ally · Light* — Revive a fallen ally at 45% HP (70% with mastery), shielded by a barrier equal to 15% of your max HP. — *revive at 75% HP · revives with a 15% caster-HP barrier · mastery at 10/25/50/90/150 uses*

