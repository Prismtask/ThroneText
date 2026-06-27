# Wedding Item Design Document — TerminalRPG

## Overview
When a monster girl reaches **100 affection** and the player proposes marriage, she gifts a **unique, soulbound Legendary accessory** that reflects her personality, race, and lore. These items are equippable by the **player** (and optionally by the girl herself) and provide a thematic mechanical benefit.

---

## Item Framework
- **Slot:** `accessory` (all wedding items)
- **Rarity:** `legendary`
- **Unique:** `True` (cannot be duplicated; only one per girl)
- **Soulbound:** Cannot be sold, dropped, or stored in the house chest
- **Equip Rule:** Player can equip any wedding item. If the **married girl is in the active party**, the item's `special` effect is amplified (denoted as **Bonded**).

---

## Tier 1 — Early Companions (Levels 2–14)

### 1. Goblin Girl — *Lucky Copper Ring*
**Theme:** Her lucky coin, her shy hope, her hidden courage.
- **Mods:** `Charisma +3`, `Learning +2`
- **Elemental:** —
- **Special — `goblin_luck`:** After each combat victory, 25% chance to find 5–15 bonus gold. **Bonded:** Chance becomes 50%.

### 2. Harpy Scout — *Windweaver Pinion*
**Theme:** The wind that carries her cries, the sky she shares with you.
- **Mods:** `Dexterity +4`, `Wisdom +1`
- **Elemental Res:** `Wind +1.3`
- **Special — `tailwind`:** +8% dodge chance. **Bonded:** Party gains +1 initiative at combat start.

### 3. Alraune Fledger — *Pollenheart Locket*
**Theme:** The blossom she grew for you, root and stem intertwined.
- **Mods:** `Charisma +3`, `Constitution +2`
- **Elemental Res:** `Earth +1.2`
- **Special — `bloom_regen`:** Regenerate 3 HP at the end of every turn in combat. **Bonded:** Regenerate 5 HP and cure 1 poison stack per turn.

### 4. Kobold Tinkerer — *Clockwork Bond Ring*
**Theme:** The clockwork heart she made — ticking in time with yours.
- **Mods:** `Learning +4`, `Dexterity +1`
- **Elemental Res:** `Thunder +1.2`
- **Special — `tinkerers_inspiration`:** 20% chance on skill use to not trigger the cooldown. **Bonded:** Chance becomes 40%.

### 5. Dryad Protector — *Barkskin Band*
**Theme:** The rune she traced on your palm, the tree you have become to her.
- **Mods:** `Constitution +4`, `Wisdom +1`
- **Elemental Res:** `Earth +1.3`, `Fire +1.1`
- **Special — `bark_shield`:** Once per dungeon floor, survive a fatal blow with 1 HP and gain a 4-turn defense buff (+3 damage reduction). **Bonded:** Trigger refreshes every 5 rooms.

### 6. Ghost Maid — *Ectoplasm Veil*
**Theme:** The warmth in her chill, the servant who chose to stay.
- **Mods:** `Dexterity +3`, `Charisma +2`
- **Elemental Res:** `Dark +1.3`
- **Special — `spectral_dodge`:** +10% dodge chance. **Bonded:** When you dodge, heal 5 HP.

### 7. Centaur Scout — *Thunderhoof Brooch*
**Theme:** The herd that is you, the thunder of her hooves at your side.
- **Mods:** `Strength +2`, `Dexterity +3`
- **Elemental Dmg:** `Wind +1.2`
- **Special — `stampede`:** First attack each combat deals +5 flat damage. **Bonded:** First attack also inflicts 1-turn stun (25% chance).

### 8. Moth Girl Flutterer — *Moondust Pendant*
**Theme:** The light she follows, the dust that marks you as her flame.
- **Mods:** `Dexterity +3`, `Charisma +2`
- **Elemental Dmg:** `Light +1.2`
- **Special — `moth_dust`:** Attacks have 20% chance to blind the enemy for 2 turns. **Bonded:** Blind duration becomes 3 turns and also reduces enemy DEX by 1.

### 9. Slime Girl — *Gelatinous Heart*
**Theme:** The home she finds in you, the squish that never lets go.
- **Mods:** `Constitution +5`, `Learning +1`
- **Elemental Res:** `Water +1.2`, `Thunder +1.2`
- **Special — `slime_absorb`:** Absorb 15% of incoming elemental damage as healing. **Bonded:** Absorb 25% and share 10% of absorbed healing with the married girl.

### 10. Lamia Constrictor — *Coiled Serpent Ring*
**Theme:** The warmth of her coils, the prey she will never release.
- **Mods:** `Strength +2`, `Dexterity +3`
- **Elemental Dmg:** `Earth +1.2`
- **Special — `coil_bind`:** Attacks have 25% chance to slow the enemy for 2 turns. **Bonded:** Slowed enemies also take +2 damage from all sources.

### 11. Lizard Queen — *Crownscale Circlet*
**Theme:** The queen who kneels for no one — except you.
- **Mods:** `Charisma +3`, `Constitution +2`
- **Elemental Res:** `Fire +1.2`, `Earth +1.2`
- **Special — `regal_presence`:** +15% capture chance (additive with CHA milestone). **Bonded:** When a monster girl is captured, she starts with +10 affection.

### 12. Mimic Girl — *Mimic's Tooth*
**Theme:** The best treasure she ever found — you.
- **Mods:** `Strength +3`, `Dexterity +2`
- **Elemental Dmg:** `Dark +1.2`
- **Special — `mimic_jackpot`:** After combat, 20% chance to duplicate one random consumable from your inventory. **Bonded:** Also 10% chance to find a random gift item.

### 13. Umbral Weaver — *Shadowthread Ring*
**Theme:** The thread she cannot cut, the darkness that keeps you safe.
- **Mods:** `Dexterity +3`, `Wisdom +2`
- **Elemental Res:** `Dark +1.3`
- **Special — `shadow_cloak`:** Enemies have -12% accuracy against you (simulated as extra dodge). **Bonded:** At combat start, you gain a 2-turn invisible buff (enemies cannot target you; they attack allies first).

### 14. Winter Fairy — *Frostbloom Charm*
**Theme:** The winter sun you are to her, the frost that never bites you.
- **Mods:** `Dexterity +3`, `Charisma +2`
- **Elemental Dmg:** `Water +1.3`
- **Special — `frost_aura`:** Attacks have 20% chance to freeze the enemy for 1 turn. **Bonded:** Freeze chance becomes 35% and frozen enemies take +20% damage from the next hit.

---

## Tier 2 — Mid-Game Companions (Levels 15–24)

### 15. Holstaur Brawler — *Bullheart Signet*
**Theme:** The herd she would take a thousand hits for.
- **Mods:** `Strength +4`, `Constitution +2`
- **Elemental Dmg:** `Earth +1.3`
- **Special — `bull_rush`:** While above 70% HP, deal +4 flat damage on all attacks. **Bonded:** Threshold becomes 50% HP and bonus becomes +6.

### 16. Gargoyle Watcher — *Stonegaze Locket*
**Theme:** The perch she left for you, the eternity she chose to spend.
- **Mods:** `Constitution +4`, `Strength +2`
- **Elemental Res:** `Earth +1.3`, `Wind +1.2`
- **Special — `stone_endurance`:** -2 flat damage taken from all sources. **Bonded:** -4 flat damage and immune to stun.

### 17. Vampire Seductress — *Sanguine Kiss Ring*
**Theme:** The kiss that binds you, body and soul, to the night.
- **Mods:** `Charisma +4`, `Dexterity +2`
- **Elemental Dmg:** `Dark +1.3`
- **Special — `blood_drain`:** Heal 15% of damage dealt (rounded down). **Bonded:** Heal 25% and excess healing becomes a 3-turn HoT.

### 18. Yuki-onna — *Blizzard Veil*
**Theme:** The warmth that did not melt her, the love that fell like snow.
- **Mods:** `Charisma +3`, `Learning +3`
- **Elemental Dmg:** `Water +1.3`, `Wind +1.2`
- **Special — `blizzard_song`:** Attacks deal +3 ice damage and have 20% chance to slow for 2 turns. **Bonded:** Slowed enemies have a 15% chance to freeze instead.

### 19. Amazon Warrior — *Warband of the Sister*
**Theme:** The shield-wall she swore to stand in, the battle-sister you became.
- **Mods:** `Strength +3`, `Dexterity +2`, `Charisma +1`
- **Elemental Dmg:** `Fire +1.2`, `Wind +1.1`
- **Special — `war_sister`:** +3 flat damage when you have 2 or more allies in the party. **Bonded:** +5 flat damage and +1 to all allies' STR.

### 20. Banshee Wailer — *Wailing Spirit Locket*
**Theme:** The song of life she sings for you, the wail she will never sound again.
- **Mods:** `Charisma +4`, `Wisdom +2`
- **Elemental Dmg:** `Dark +1.2`, `Wind +1.2`
- **Special — `keening_wail`:** When your HP drops below 25%, all enemies take 10–20 damage and have a 30% chance to be feared for 1 turn. **Bonded:** Damage becomes 15–30 and triggers at 35% HP.

### 21. Neko Ninja — *Nekomata Bell*
**Theme:** The shadow that is always yours, the bell that marks her territory.
- **Mods:** `Dexterity +5`, `Strength +1`
- **Elemental Dmg:** `Dark +1.2`, `Wind +1.1`
- **Special — `neko_shadow`:** +12% dodge chance. **Bonded:** When you dodge, counter-attack for 50% of a normal attack's damage.

### 22. Arachne Weaver — *Silkspinner Band*
**Theme:** The web that holds you, the center she will never let fall.
- **Mods:** `Dexterity +4`, `Strength +2`
- **Elemental Res:** `Earth +1.2`, `Dark +1.2`
- **Special — `silk_bind`:** Attacks have 25% chance to reduce enemy DEX by 2 for 3 turns (webbed). **Bonded:** Webbed enemies also have -20% dodge chance.

### 23. Mummy Princess — *Pharaoh's Band*
**Theme:** The dynasty she ruled, the king she chose to rule beside.
- **Mods:** `Charisma +4`, `Constitution +2`, `Learning +1`
- **Elemental Res:** `Dark +1.2`, `Earth +1.2`
- **Special — `pharaohs_curse`:** Enemies that attack you take 4 damage (retribution). **Bonded:** Retribution damage becomes 8 and enemies have -10% accuracy.

### 24. Oni Bruiser — *Oni Horn Ring*
**Theme:** The guts she loves, the hell you raise together.
- **Mods:** `Strength +5`, `Constitution +2`
- **Elemental Dmg:** `Fire +1.3`, `Earth +1.2`
- **Special — `oni_rage`:** When below 50% HP, deal +5 flat damage. **Bonded:** When below 50% HP, also gain +2 CON and +2 STR until combat ends.

### 25. Salamander Dancer — *Emberwaltz Ring*
**Theme:** The fire that burns only for you, the dance that never ends.
- **Mods:** `Dexterity +3`, `Charisma +3`
- **Elemental Dmg:** `Fire +1.3`
- **Special — `flame_dance`:** Attacks have 30% chance to burn the enemy for 3 turns (5 damage/turn). **Bonded:** Burn damage becomes 8/turn and spread to 1 adjacent enemy on proc.

### 26. Succubus Seductress — *Dreamcatcher Ring*
**Theme:** The dream she lets you into, the heart she never gives.
- **Mods:** `Charisma +5`, `Dexterity +2`
- **Elemental Dmg:** `Dark +1.3`
- **Special — `dream_drain`:** Attacks have 20% chance to inflict dread for 2 turns. **Bonded:** Dreaded enemies have 40% chance to miss attacks instead of 25%.

### 27. Dullahan Knight — *Headless Rider's Seal*
**Theme:** The oath she swore, the heart she never had — now beating for you.
- **Mods:** `Strength +4`, `Constitution +2`, `Charisma +1`
- **Elemental Res:** `Dark +1.2`, `Light +1.1`
- **Special — `headless_oath`:** Immune to fear and dread. **Bonded:** When you defeat an enemy, all allies heal 10 HP.

### 28. Kitsune Miko — *Foxfire Band*
**Theme:** The nine tails that cocoon you, the shrine that walks with you.
- **Mods:** `Wisdom +4`, `Charisma +3`
- **Elemental Dmg:** `Fire +1.2`, `Light +1.2`
- **Special — `foxfire_trick`:** 20% chance when attacked to create a foxfire clone — the attack misses and the attacker takes 5 fire damage. **Bonded:** Chance becomes 35% and also blinds the attacker for 1 turn.

### 29. Siren Empress — *Coral Crown Ring*
**Theme:** The tide that always returns to you, the song that drowns out all others.
- **Mods:** `Charisma +5`, `Dexterity +2`
- **Elemental Dmg:** `Water +1.3`, `Wind +1.1`
- **Special — `siren_song`:** Attacks have 20% chance to charm the enemy (stun for 1 turn). **Bonded:** Charm duration becomes 2 turns and also reduces enemy WIS by 2.

### 30. Crimson Countess — *Crimson Sigil*
**Theme:** The dawn she never expected, the life she feels in your veins.
- **Mods:** `Charisma +5`, `Dexterity +2`
- **Elemental Dmg:** `Dark +1.3`, `Water +1.2`
- **Special — `crimson_feast`:** Heal 15% of max HP when you defeat an enemy. **Bonded:** Heal 25% and gain +2 CHA for 3 turns (stackable once).

### 31. Demon Whip Master — *Whipmaster's Coil*
**Theme:** The leash and the freedom, the command she obeys with pleasure.
- **Mods:** `Dexterity +4`, `Charisma +2`
- **Elemental Dmg:** `Fire +1.2`, `Dark +1.2`
- **Special — `whip_crack`:** Attacks have 25% chance to reduce enemy armor by 3 for 3 turns (vulnerable). **Bonded:** Vulnerable enemies also have -2 DEX.

### 32. Minotaur Gladiator — *Arenaborn Signet*
**Theme:** The arena she conquered, the victory you are.
- **Mods:** `Strength +5`, `Constitution +2`, `Dexterity +1`
- **Elemental Dmg:** `Earth +1.3`, `Fire +1.1`
- **Special — `arena_glory`:** +5 flat damage against boss enemies. **Bonded:** +8 flat damage vs bosses and -2 damage taken from boss attacks.

---

## Tier 3 — Late-Game & Legendary Companions (Levels 25–40)

### 33. Vampire Matriarch — *Matriarch's Favor*
**Theme:** The mother of the night, the child she chose above all others.
- **Mods:** `Charisma +4`, `Constitution +3`, `Wisdom +2`
- **Elemental Res:** `Dark +1.3`, `Water +1.2`
- **Special — `matriarchs_embrace`:** +10% max HP. **Bonded:** All allies gain +5% max HP and regenerate 2 HP per turn.

### 34. Centaur Champion — *Champion's Mane Ring*
**Theme:** The champion who yields only to a greater champion.
- **Mods:** `Strength +3`, `Dexterity +3`, `Charisma +2`
- **Elemental Dmg:** `Wind +1.3`, `Light +1.2`
- **Special — `champion_charge`:** First attack each combat deals +8 flat damage and has +15% accuracy. **Bonded:** First attack deals +12 flat damage and ignores 50% armor.

### 35. Infernal Empress — *Infernal Throne Seal*
**Theme:** The spark that did not die in her furnace, the consort of hell.
- **Mods:** `Strength +4`, `Charisma +4`, `Constitution +2`
- **Elemental Dmg:** `Fire +1.4`, `Dark +1.3`
- **Special — `infernal_crown`:** +15% fire and dark damage. Enemies that attack you in melee take 5 burn damage. **Bonded:** Burn damage becomes 10 and also inflicts 1-turn dread on the attacker.

### 36. Scylla Wrecker — *Abyssal Coil*
**Theme:** The deep that dragged others down, but pulls you close.
- **Mods:** `Strength +4`, `Constitution +3`, `Dexterity +1`
- **Elemental Dmg:** `Water +1.4`, `Dark +1.2`
- **Special — `abyssal_grasp`:** Attacks have 30% chance to reduce enemy DEX by 3 for 3 turns (tentacle bind). **Bonded:** Bound enemies also lose 1 action per turn (slowed) and take 3 water damage per turn.

### 37. Gorgon Petrifier — *Gorgon's Veil Ring*
**Theme:** The gaze that petrifies — except when it looks at you.
- **Mods:** `Dexterity +3`, `Charisma +3`, `Wisdom +2`
- **Elemental Dmg:** `Earth +1.3`, `Dark +1.2`
- **Special — `stone_gaze`:** Attacks have 20% chance to petrify (reduce enemy STR and DEX by 3 for 3 turns). **Bonded:** Petrified enemies have a 15% chance to be fully stunned for 1 turn instead.

### 38. Ninetales Fox — *Sunfire Band*
**Theme:** The legend you became, the story she will guard until the last page.
- **Mods:** `Charisma +5`, `Wisdom +3`, `Learning +2`
- **Elemental Dmg:** `Fire +1.4`, `Light +1.3`
- **Special — `legendary_flame`:** Attacks leave a 3-turn burn (6 damage/turn). **Bonded:** Burn becomes 10/turn and spreads to all enemies on the turn it is applied.

### 39. Mermaid Siren Queen — *Tidecaller Ring*
**Theme:** The shore she always returns to, the ocean she commands for you.
- **Mods:** `Charisma +5`, `Wisdom +3`, `Learning +2`
- **Elemental Dmg:** `Water +1.4`, `Wind +1.2`
- **Special — `tidal_blessing`:** Heal 15% of damage dealt. **Bonded:** Heal 25% and at combat start, all enemies take 5 water damage (tidal wave).

### 40. Draconic Valkyrie — *Dragonwing Signet*
**Theme:** The glory she carries you to on dragon-wings.
- **Mods:** `Strength +4`, `Constitution +3`, `Charisma +2`
- **Elemental Dmg:** `Fire +1.3`, `Wind +1.3`
- **Special — `dragon_judgment`:** +10% damage vs enemies with wings or flight (simulated: all beast/fey/dragonkin enemies). **Bonded:** +15% and your attacks ignore 30% of their elemental resistance.

### 41. Sphinx Riddler — *Riddlelock Band*
**Theme:** The answer to her oldest riddle — you.
- **Mods:** `Learning +5`, `Wisdom +3`, `Charisma +2`
- **Elemental Dmg:** `Thunder +1.3`, `Light +1.2`
- **Special — `riddle_solved`:** If you attack an enemy before it has acted this combat, deal +8 damage. **Bonded:** Bonus becomes +12 and the enemy is silenced for 1 turn.

### 42. Lich Queen Avatar — *Phylactery Bond*
**Theme:** The variable she cannot solve, the thesis she will defend forever.
- **Mods:** `Learning +6`, `Charisma +3`, `Wisdom +2`
- **Elemental Dmg:** `Dark +1.4`, `Thunder +1.2`
- **Special — `lich_grasp`:** Attacks have 25% chance to apply curse (enemy -2 to all stats for 3 turns). **Bonded:** Cursed enemies also take 5 dark damage per turn and cannot heal.

### 43. Valkyrie Commander — *Commander's Ring*
**Theme:** The Valhalla you are, the army she leads for you alone.
- **Mods:** `Strength +4`, `Dexterity +3`, `Charisma +3`
- **Elemental Dmg:** `Light +1.3`, `Wind +1.2`
- **Special — `valkyrie_ride`:** +10% damage when you have full HP. **Bonded:** Also grants all allies +5% damage when you are at full HP.

### 44. Dragon Goddess Avatar — *Stardust Crown*
**Theme:** The ember that refused to die, the constellation she named after you.
- **Mods:** `Strength +5`, `Constitution +4`, `Charisma +3`
- **Elemental Dmg:** `Fire +1.4`, `Light +1.4`, `Thunder +1.2`
- **Special — `starfire_breath`:** Attacks deal bonus damage equal to 20% of your CHA (rounded up). **Bonded:** Bonus becomes 35% of CHA and also burns enemies for 3 turns.

### 45. Arachne Brood Queen — *Broodmother's Web*
**Theme:** The family she weaves around you, the thread she never cuts.
- **Mods:** `Dexterity +5`, `Strength +3`, `Constitution +2`
- **Elemental Res:** `Earth +1.3`, `Dark +1.3`
- **Special — `brood_swarm`:** 25% chance on attack to summon spiderlings (deal +6 bonus damage and poison enemy for 3 turns, 4 dmg/turn). **Bonded:** Poison becomes 8/turn and spiderlings also reduce enemy DEX by 2.

### 46. Cosmic Slime Empress — *Galaxy Heart*
**Theme:** The gravity she did not expect, the center of her universe.
- **Mods:** `Constitution +6`, `Learning +5`, `Charisma +4`
- **Elemental Res:** All elements +1.2
- **Special — `cosmic_gravity`:** +8% to all stats when the married girl is in the party. **Bonded:** +12% to all stats, and once per combat you can absorb an enemy's buff (steal 1 random active buff from the target on your first hit).

---

## Implementation Notes (for later)

1. **New field `married_to`** on player dict: list of girl keys who are married.
2. **New field `wedding_item`** on the married girl's dict (or player inventory): the soulbound item.
3. **Special effects** can be implemented as:
   - `special` string on the item (like `abyss_fang`)
   - Hook checks in `combat/enemy_ai.py` for retribution, on-dodge, on-defeat, etc.
   - Hook checks in `combat/player_actions.py` for on-attack procs (burn, poison, slow, blind, etc.)
   - Hook checks in `combat/ally.py` or `combat/combat_engine.py` for start-of-combat and end-of-combat effects.
4. **Bonded check:** At combat start, verify if the married girl is in `player["allies"]` and set a flag `wedding_bonded = True`. All `special` handlers check this flag.
5. **UI:** In the lounge, add a `Wedding` option when affection reaches 100 (only if not already married). After the ceremony, the girl's dialogue changes to wedding-themed lines and the item is added to the player's inventory.

---

*Document version: 1.0 — Design phase. No code written yet.*
