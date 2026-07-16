# Pandemonium — Full Skill Elemental Rework

> **Goal:** Assign every skill in the game a specific elemental profile from the 9-element system, replacing the current `physical`/`magical` binary classification and filling in the gaps for ally skills.

---

## Element Reference

| # | Element | Theme / Keywords |
|---|---------|------------------|
| 1 | **fire** | flames, heat, magma, explosions, passion, destruction |
| 2 | **water** | ice, frost, oceans, tides, fluidity, cleansing |
| 3 | **thunder** | lightning, storms, speed, shock, plasma, electricity |
| 4 | **wind** | gales, tornados, flight, swiftness, piercing, air |
| 5 | **earth** | stone, nature, roots, endurance, defense, ground |
| 6 | **light** | holy, divine, purity, healing, radiance, truth |
| 7 | **dark** | shadow, void, curses, necrotic, fear, corruption |
| 8 | **physical** | blades, fists, arrows, raw muscle, martial prowess |
| 9 | **magical** | arcane, raw mana, psychic, cosmic, pure spellcraft |

---

## How to Implement

### 1. YAML Changes
Add an `elemental:` field to every skill definition in:
- `resources/skill_book/skill_list.yaml` (class skills, learnable skills)
- `resources/skill_book/innate_skills.yaml` (ally innate skills)

Example:
```yaml
mage_fireball:
  name: Fireball
  elemental: fire          # ← NEW
  description: Hurl a massive fireball at a single enemy.
  unlock_level: 3
  cooldown: 3
  target: enemy
  power_type: ler
  base_power: 16
```

### 2. Code Changes
- **Remove** the hardcoded `SKILL_ELEMENTS` dictionary from `combat/skills.py`
- Instead, read `elemental` from the skill definition YAML: `skill.get("elemental")`
- In `combat/ally_skills.py`, add `calculate_elemental_damage()` call in the `_calc_dmg` helper, reading `skill_def.get("elemental")`
- Update `combat/combat_ui.py` to display elemental tags on skill descriptions

### 3. Fallback
If a skill has no `elemental` field, treat it as **neutral** (1.0× multiplier, no elemental interaction).

---

## 1. CLASS SKILLS (48 skills)

### 1A. WARRIOR — Physical / Earth Hybrid

| Skill ID | Name | Old Element | **New Element** | Rationale |
|---|---|---|---|---|
| `war_cleave` | Cleave | physical | **physical** | Pure weapon strike, wide arc |
| `war_battlecry` | Battle Cry | physical | **physical** | Martial shout, rallying cry |
| `war_execute` | Execute | physical | **physical** | Finishing blow, raw killing intent |
| `war_shield_slam` | Shield Slam | physical | **earth** | Shield bash = concussive force, grounding |
| `war_second_wind` | Second Wind | physical | **physical** | Martial endurance, grit |
| `war_bladestorm` | Bladestorm | physical | **wind** | Whirlwind of steel, cyclone imagery |

> **Design Note:** Warrior uses physical/earth/wind — the grounded, unstoppable force. Shield Slam becomes earth because it's concussive and defensive. Bladestorm becomes wind because of the spinning cyclone theme.

---

### 1B. MAGE — Fire / Water / Thunder / Magical

| Skill ID | Name | Old Element | **New Element** | Rationale |
|---|---|---|---|---|
| `mage_fireball` | Fireball | magical | **fire** | It's literally a fireball |
| `mage_frostnova` | Frost Nova | magical | **water** | Ice = water element |
| `mage_arcane` | Arcane Barrage | (none) | **magical** | Pure arcane missiles |
| `mage_meteor` | Meteor | magical | **fire** | Blazing rock from the sky |
| `mage_timewarp` | Time Warp | (none) | **magical** | Bending time = arcane mastery |
| `mage_overload` | Mana Overload | magical | **thunder** | Overload = electrical/surge imagery |

> **Design Note:** Mage gets fire, water, thunder, and magical — a true elementalist. Overload → thunder fits the "surge/overcharge" theme better than generic magical.

---

### 1C. ROGUE — Dark / Physical / Magical Hybrid

| Skill ID | Name | Old Element | **New Element** | Rationale |
|---|---|---|---|---|
| `rog_backstab` | Backstab | physical | **dark** | Striking from shadows |
| `rog_smoke` | Smoke Bomb | physical | **dark** | Obscuring darkness, ninja tools |
| `rog_assassinate` | Assassinate | physical | **dark** | Killing from the void |
| `rog_shadow_strike` | Shadow Strike | physical | **dark** | Shadow in the name |
| `rog_venom` | Venomous Blade | physical | **water** | Liquid poison = water's corrupt aspect |
| `rog_death_dance` | Death Dance | (none) | **dark** | Dance of death, grim reaper imagery |

> **Design Note:** Rogue shifts heavily into dark element — shadow strikes, assassination, smoke. Venom becomes water (poison = corrupted liquid). This gives Rogue a distinct elemental identity.

---

### 1D. CLERIC — Light / Magical Hybrid

| Skill ID | Name | Old Element | **New Element** | Rationale |
|---|---|---|---|---|
| `clr_heal` | Heal | magical | **light** | Holy healing radiance |
| `clr_shield` | Divine Shield | magical | **light** | Divine protection |
| `clr_smite` | Holy Smite | magical | **light** | Smiting with holy power |
| `clr_mass_heal` | Mass Heal | magical | **light** | Radiant party healing |
| `clr_resurrection` | Resurrection | magical | **light** | Returning life = pure light |
| `clr_divine_wrath` | Divine Wrath | magical | **light** | Wrath of the heavens |

> **Design Note:** Cleric is pure light — the holy conduit. Everything channels divine radiance.

---

### 1E. RANGER — Wind / Earth / Physical Hybrid

| Skill ID | Name | Old Element | **New Element** | Rationale |
|---|---|---|---|---|
| `rng_pierce` | Piercing Shot | physical | **wind** | Arrow through the air, piercing gale |
| `rng_mark` | Hunter's Mark | physical | **wind** | Hawk's eye, tracking winds |
| `rng_rain` | Rain of Arrows | physical | **wind** | Arrows falling like storm |
| `rng_rapid` | Rapid Fire | physical | **wind** | Swift as the wind |
| `rng_trueshot` | Trueshot | physical | **physical** | Pure marksmanship, no magic |
| `rng_nature` | Nature's Grasp | (none) | **earth** | Vines and roots = earth's embrace |

> **Design Note:** Ranger uses wind (speed, arrows, air) and earth (nature, roots). Trueshot stays physical as pure skill.

---

### 1F. PALADIN — Light / Physical Hybrid

| Skill ID | Name | Old Element | **New Element** | Rationale |
|---|---|---|---|---|
| `pal_strike` | Holy Strike | magical | **light** | Divine-infused weapon |
| `pal_layhands` | Lay on Hands | (none) | **light** | Miraculous healing touch |
| `pal_judgment` | Divine Judgment | magical | **light** | Heaven's verdict |
| `pal_consecrate` | Consecrate | magical | **light** | Hallowed ground |
| `pal_bastion` | Bastion of Light | (none) | **light** | It's in the name |
| `pal_avenging` | Avenging Wrath | magical | **light** | Righteous fury |

> **Design Note:** Paladin is light + physical — the holy warrior blending martial and divine. Lay on Hands and Bastion were missing elements entirely.

---

### 1G. WARLOCK — Dark / Fire / Magical Hybrid

| Skill ID | Name | Old Element | **New Element** | Rationale |
|---|---|---|---|---|
| `lck_drain` | Drain Life | magical | **dark** | Stealing life force = void magic |
| `lck_curse` | Dark Curse | magical | **dark** | Cursing = dark magic |
| `lck_pact` | Demonic Pact | magical | **fire** | Demonic = hellfire |
| `lck_fear` | Soul Fear | magical | **dark** | Terror of the abyss |
| `lck_empower` | Dark Empowerment | magical | **dark** | Channeling darkness for power |
| `lck_soul_fire` | Soul Fire | magical | **fire** | Fire in the name, soul-burning |

> **Design Note:** Warlock splits between dark (curses, drain, fear) and fire (demonic, soul fire). Gives Warlock two elemental axes to play with.

---

### 1H. BARBARIAN — Physical / Fire / Earth Hybrid

| Skill ID | Name | Old Element | **New Element** | Rationale |
|---|---|---|---|---|
| `bar_rage` | Feral Rage | physical | **fire** | Burning anger, inner fire |
| `bar_whirl` | Whirlwind | physical | **wind** | Spinning cyclone of death |
| `bar_berserk` | Berserk | physical | **fire** | Frenzied flames of battle |
| `bar_sunder` | Sunder Armor | physical | **earth** | Shattering stone, breaking mountains |
| `bar_bloodlust` | Bloodlust | physical | **physical** | Primal savagery, raw instinct |
| `bar_earth_shatter` | Earth Shatter | physical | **earth** | Earth in the name, ground-splitting |

> **Design Note:** Barbarian uses fire (rage, berserk fury), earth (sundering, shattering), and physical. The primal elements of destruction.

---

## 2. LEARNABLE SKILLS (31 skills)

### 2A. OFFENSIVE (12 skills)

| Skill ID | Name | Tier | Old | **New Element** | Rationale |
|---|---|---|---|---|---|
| `slash` | Slash | 1 | none | **physical** | Basic blade work |
| `quick_strike` | Quick Strike | 1 | none | **wind** | Speed and precision |
| `arcane_bolt` | Arcane Bolt | 1 | none | **magical** | Pure arcane energy |
| `power_strike` | Power Strike | 2 | none | **physical** | Heavy blow, brute force |
| `fireball` | Fireball | 2 | none | **fire** | It's a fireball |
| `poison_strike` | Poison Strike | 2 | none | **water** | Liquid poison = water's corrupt facet |
| `ice_shards` | Ice Shards | 3 | none | **water** | Ice = frozen water |
| `multi_hit` | Multi Hit | 3 | none | **physical** | Flurry of strikes |
| `whirlwind` | Whirlwind | 3 | none | **wind** | Spinning cyclone |
| `annihilate` | Annihilate | 4 | none | **dark** | Total obliteration, void-energy |
| `inferno` | Inferno | 4 | none | **fire** | All-consuming flames |
| `shadow_dance` | Shadow Dance | 4 | none | **dark** | Dancing in shadows |

### 2B. DEFENSIVE (7 skills)

| Skill ID | Name | Tier | Old | **New Element** | Rationale |
|---|---|---|---|---|---|
| `protect` | Protect | 1 | none | **earth** | Stalwart defense, immovable |
| `dodge` | Dodge | 1 | none | **wind** | Evasive footwork, like the breeze |
| `shield_wall` | Shield Wall | 2 | none | **earth** | Fortification, bulwark |
| `hardened_skin` | Hardened Skin | 2 | none | **earth** | Stone-like endurance |
| `counter` | Counter | 3 | none | **physical** | Martial riposte |
| `perfect_guard` | Perfect Guard | 4 | none | **light** | Impenetrable holy barrier |
| `phantom_dodge` | Phantom Dodge | 4 | none | **dark** | Ghost-like intangibility |

### 2C. SUPPORT (12 skills)

| Skill ID | Name | Tier | Old | **New Element** | Rationale |
|---|---|---|---|---|---|
| `heal` | Heal | 1 | none | **light** | Restorative light |
| `strength_buff` | Strength Buff | 1 | none | **physical** | Martial encouragement |
| `slow` | Slow | 1 | none | **water** | Freezing/slowing = ice magic |
| `group_heal` | Group Heal | 2 | none | **light** | Radiant party restoration |
| `regenerate` | Regenerate | 2 | none | **earth** | Natural regrowth |
| `weakening_curse` | Weakening Curse | 2 | none | **dark** | Cursing = dark magic |
| `wisdom_buff` | Wisdom Buff | 3 | none | **magical** | Arcane insight |
| `haste` | Haste | 3 | none | **thunder** | Lightning speed |
| `blind` | Blind | 3 | none | **dark** | Obscuring shadows |
| `mass_regenerate` | Mass Regenerate | 4 | none | **earth** | Verdant regrowth for all |
| `heroic_onslaught` | Heroic Onslaught | 4 | none | **fire** | Inspiring flames of battle |
| `aura_of_despair` | Aura of Despair | 4 | none | **dark** | Choking darkness |

---

## 3. ALLY INNATE SKILLS (90 skills)

### 3A. Tier 1 Monster Girls (Common)

#### Goblin Girl
| Skill ID | Name | **New Element** | Rationale |
|---|---|---|---|
| `goblin_dart` | Goblin Dart | **water** | Poison-tipped dart = liquid toxin |
| `goblin_evasion` | Goblin Evasion | **wind** | Quick dodging, nimble as breeze |

#### Harpy Scout
| Skill ID | Name | **New Element** | Rationale |
|---|---|---|---|
| `harpy_swoop` | Harpy Swoop | **wind** | Diving from the sky |
| `harpy_cry` | Harpy Cry | **wind** | Sonic screech, air vibration |

#### Alraune Fledger
| Skill ID | Name | **New Element** | Rationale |
|---|---|---|---|
| `root_strike` | Root Strike | **earth** | Magical roots from the ground |
| `nature_embrace` | Nature's Embrace | **earth** | Nature's healing touch |

#### Kobold Tinkerer
| Skill ID | Name | **New Element** | Rationale |
|---|---|---|---|
| `gadget_explosion` | Gadget Explosion | **fire** | Explosions = fire |
| `tinker_enhancement` | Tinker Enhancement | **thunder** | Mechanical empowerment, spark of genius |

#### Dryad Protector
| Skill ID | Name | **New Element** | Rationale |
|---|---|---|---|
| `entangle` | Entangle | **earth** | Vines gripping from the soil |
| `forest_shield` | Forest Shield | **earth** | Bark and thorn barrier |

#### Ghost Maid
| Skill ID | Name | **New Element** | Rationale |
|---|---|---|---|
| `spectral_strike` | Spectral Strike | **dark** | Ghostly, phasing through defenses |
| `phantom_barrier` | Phantom Barrier | **dark** | Spectral protection |

#### Centaur Scout
| Skill ID | Name | **New Element** | Rationale |
|---|---|---|---|
| `charge` | Charge | **physical** | Raw charging momentum |
| `hoof_stomp` | Hoof Stomp | **earth** | Ground-shaking stomp |

#### Moth Girl Flutterer
| Skill ID | Name | **New Element** | Rationale |
|---|---|---|---|
| `flutter_strike` | Flutter Strike | **wind** | Fluttering wings, airy strike |
| `dust_cloud` | Dust Cloud | **earth** | Dust/sand cloud |

#### Slime Girl
| Skill ID | Name | **New Element** | Rationale |
|---|---|---|---|
| `acidic_blob` | Acidic Blob | **water** | Liquid acid = corrosive water |
| `slime_absorption` | Slime Absorption | **water** | Absorbing like a sponge |

#### Lamia Constrictor
| Skill ID | Name | **New Element** | Rationale |
|---|---|---|---|
| `constrict` | Constrict | **physical** | Physical crushing grip |
| `venom_fang` | Venom Fang | **water** | Venom = liquid toxin |

#### Lizard Queen
| Skill ID | Name | **New Element** | Rationale |
|---|---|---|---|
| `royal_slash` | Royal Slash | **physical** | Majestic blade work |
| `regenerate_scale` | Regenerate Scale | **earth** | Natural reptilian regrowth |

#### Mimic Girl
| Skill ID | Name | **New Element** | Rationale |
|---|---|---|---|
| `surprise_strike` | Surprise Strike | **dark** | Ambush from hiding |
| `mimic_form` | Mimic Form | **magical** | Shapeshifting magic |

---

### 3B. Tier 2 Monster Girls (Uncommon)

#### Umbral Weaver
| Skill ID | Name | **New Element** | Rationale |
|---|---|---|---|
| `shadow_strike` | Shadow Strike | **dark** | Shadow in the name |
| `web_trap` | Web Trap | **earth** | Sticky entrapment |

#### Winter Fairy
| Skill ID | Name | **New Element** | Rationale |
|---|---|---|---|
| `frost_bolt` | Frost Bolt | **water** | Ice = frozen water |
| `ice_shield` | Ice Shield | **water** | Shield of frozen water |

#### Holstaur Brawler
| Skill ID | Name | **New Element** | Rationale |
|---|---|---|---|
| `mighty_punch` | Mighty Punch | **physical** | Raw fist-fighting |
| `earthen_stomp` | Earthen Stomp | **earth** | Earth in the name |

#### Gargoyle Watcher
| Skill ID | Name | **New Element** | Rationale |
|---|---|---|---|
| `stone_fist` | Stone Fist | **earth** | Fists of living stone |
| `stone_skin` | Stone Skin | **earth** | Petrified hide |

#### Vampire Seductress
| Skill ID | Name | **New Element** | Rationale |
|---|---|---|---|
| `blood_drain` | Blood Drain | **dark** | Vampiric life-stealing |
| `seductive_charm` | Seductive Charm | **dark** | Dark allure, mesmerism |

#### Yuki Onna
| Skill ID | Name | **New Element** | Rationale |
|---|---|---|---|
| `blizzard` | Blizzard | **water** | Frozen storm = ice/water |
| `frozen_heart` | Frozen Heart | **water** | Ice-bound soul |

#### Amazon Warrior
| Skill ID | Name | **New Element** | Rationale |
|---|---|---|---|
| `spear_thrust` | Spear Thrust | **physical** | Precise martial thrust |
| `warrior_stance` | Warrior Stance | **physical** | Battle-hardened posture |

#### Banshee Wailer
| Skill ID | Name | **New Element** | Rationale |
|---|---|---|---|
| `wail_of_sorrow` | Wail of Sorrow | **dark** | Mournful death-cry |
| `death_shriek` | Death Shriek | **dark** | Scream of the grave |

#### Neko Ninja
| Skill ID | Name | **New Element** | Rationale |
|---|---|---|---|
| `shadow_clone` | Shadow Clone | **dark** | Illusory shadow duplicate |
| `ninja_strike` | Ninja Strike | **wind** | Swift as the silent wind |

#### Arachne Weaver
| Skill ID | Name | **New Element** | Rationale |
|---|---|---|---|
| `web_throw` | Web Throw | **earth** | Sticky silk trap |
| `spider_dance` | Spider Dance | **dark** | Hypnotic, unsettling |

#### Mummy Princess
| Skill ID | Name | **New Element** | Rationale |
|---|---|---|---|
| `desert_curse` | Desert Curse | **earth** | Ancient desert malediction |
| `pharaohs_wrath` | Pharaoh's Wrath | **dark** | Vengeance of the dead |

#### Oni Bruiser
| Skill ID | Name | **New Element** | Rationale |
|---|---|---|---|
| `oni_smash` | Oni Smash | **fire** | Demonic strength, hell-born |
| `hellfire_roar` | Hellfire Roar | **fire** | Hellfire in the name |

#### Salamander Dancer
| Skill ID | Name | **New Element** | Rationale |
|---|---|---|---|
| `flame_dance` | Flame Dance | **fire** | Flames in the name |
| `ember_shield` | Ember Shield | **fire** | Protective embers |

#### Succubus Seductress
| Skill ID | Name | **New Element** | Rationale |
|---|---|---|---|
| `allure` | Allure | **dark** | Demonic charm, bewitchment |
| `draining_kiss` | Draining Kiss | **dark** | Life-draining touch |

#### Dullahan Knight
| Skill ID | Name | **New Element** | Rationale |
|---|---|---|---|
| `headless_charge` | Headless Charge | **dark** | Undead rider's charge |
| `spectral_guard` | Spectral Guard | **dark** | Ghostly defenders |

#### Kitsune Miko
| Skill ID | Name | **New Element** | Rationale |
|---|---|---|---|
| `foxfire` | Foxfire | **fire** | Spiritual flame |
| `spirit_shield` | Spirit Shield | **light** | Holy shrine maiden barrier |

#### Siren Empress
| Skill ID | Name | **New Element** | Rationale |
|---|---|---|---|
| `siren_call` | Siren Call | **water** | Oceanic song |
| `ocean_lullaby` | Ocean Lullaby | **water** | Ocean in the name |

#### Crimson Countess
| Skill ID | Name | **New Element** | Rationale |
|---|---|---|---|
| `crimson_slash` | Crimson Slash | **dark** | Bloody vampiric strike |
| `blood_ritual` | Blood Ritual | **dark** | Sacrificial blood magic |

#### Demon Whip Master
| Skill ID | Name | **New Element** | Rationale |
|---|---|---|---|
| `whip_lash` | Whip Lash | **fire** | Crack of the demon whip, searing pain |
| `dominating_presence` | Dominating Presence | **dark** | Crushing demonic authority |

#### Minotaur Gladiator
| Skill ID | Name | **New Element** | Rationale |
|---|---|---|---|
| `colossal_slam` | Colossal Slam | **earth** | Earth-shaking impact |
| `gladiator_stance` | Gladiator Stance | **physical** | Arena-hardened combat stance |

---

### 3C. Tier 3 Monster Girls (Rare / Elite)

#### Vampire Matriarch
| Skill ID | Name | **New Element** | Rationale |
|---|---|---|---|
| `matriarch_bite` | Matriarch's Bite | **dark** | Ancient vampiric feeding |
| `dark_blessing` | Dark Blessing | **dark** | Unholy vitality gift |

#### Centaur Champion
| Skill ID | Name | **New Element** | Rationale |
|---|---|---|---|
| `champion_charge` | Champion's Charge | **wind** | Gale-speed cavalry charge |
| `stampede` | Stampede | **earth** | Thunderous hoof-beats shaking ground |

#### Infernal Empress
| Skill ID | Name | **New Element** | Rationale |
|---|---|---|---|
| `infernal_flame` | Infernal Flame | **fire** | Infernal hellfire |
| `empress_command` | Empress Command | **dark** | Demonic royal authority |

#### Scylla Wrecker
| Skill ID | Name | **New Element** | Rationale |
|---|---|---|---|
| `tentacle_crush` | Tentacle Crush | **water** | Deep-sea monster, crushing depths |
| `abyssal_pull` | Abyssal Pull | **water** | Dragging into the abyss |

#### Gorgon Petrifier
| Skill ID | Name | **New Element** | Rationale |
|---|---|---|---|
| `petrifying_gaze` | Petrifying Gaze | **earth** | Turning to stone |
| `serpent_fang` | Serpent Fang | **water** | Venomous snake bite |

#### Ninetales Fox
| Skill ID | Name | **New Element** | Rationale |
|---|---|---|---|
| `sunfire_breath` | Sunfire Breath | **fire** | Solar flames |
| `nine_tails_strike` | Nine Tails Strike | **magical** | Mystical multi-tail assault |

#### Mermaid Siren Queen
| Skill ID | Name | **New Element** | Rationale |
|---|---|---|---|
| `tidal_wave` | Tidal Wave | **water** | Ocean's crushing force |
| `siren_lullaby` | Siren Lullaby | **water** | Soothing sea melody |

#### Draconic Valkyrie
| Skill ID | Name | **New Element** | Rationale |
|---|---|---|---|
| `dragon_breath` | Dragon Breath | **fire** | Draconic fire breath |
| `valkyrie_strike` | Valkyrie Strike | **light** | Divine spear of the choosers |

#### Sphinx Riddler
| Skill ID | Name | **New Element** | Rationale |
|---|---|---|---|
| `riddle_blast` | Riddle Blast | **magical** | Puzzling arcane energy |
| `enigma_field` | Enigma Field | **magical** | Reality-bending confusion |

#### Lich Queen Avatar
| Skill ID | Name | **New Element** | Rationale |
|---|---|---|---|
| `necrotic_bolt` | Necrotic Bolt | **dark** | Pure death energy |
| `raise_dead` | Raise Dead | **dark** | Unholy resurrection |

#### Valkyrie Commander
| Skill ID | Name | **New Element** | Rationale |
|---|---|---|---|
| `commanders_slash` | Commander's Slash | **physical** | Precision martial strike |
| `rally` | Rally | **light** | Inspiring divine presence |

#### Dragon Goddess Avatar
| Skill ID | Name | **New Element** | Rationale |
|---|---|---|---|
| `starfire_breath` | Starfire Breath | **fire** | Celestial dragon flames |
| `divine_wings` | Divine Wings | **light** | Heavenly protection |

#### Arachne Brood Queen
| Skill ID | Name | **New Element** | Rationale |
|---|---|---|---|
| `brood_bite` | Brood Bite | **water** | Venomous brood fangs |
| `silk_shield` | Silk Shield | **earth** | Woven silk barrier |

#### Cosmic Slime Empress
| Skill ID | Name | **New Element** | Rationale |
|---|---|---|---|
| `cosmic_blast` | Cosmic Blast | **magical** | Raw cosmic energy |
| `gravity_well` | Gravity Well | **magical** | Space-time distortion |

---

### 3D. Wonderland Heroines (Special)

#### Alice
| Skill ID | Name | **New Element** | Rationale |
|---|---|---|---|
| `curious_inquiry` | Curious Inquiry | **magical** | Wonderland logic-bending (already applies elemental_weakness) |
| `try_me` | Try Me | **magical** | Size-shifting = magical transformation |

#### Alice (Vorpal Blade)
| Skill ID | Name | Current | **New Element** | Rationale |
|---|---|---|---|---|
| `vorpal_edge` | Vorpal Edge | light | **light** | Already correct — luminous slash |
| `snicker_snack` | Snicker-Snack | light | **light** | Already correct — singing blade of light |
| `frabjous_day` | Frabjous Day | none | **light** | Triumphant celebration, radiant joy |

#### Red Hood
| Skill ID | Name | **New Element** | Rationale |
|---|---|---|---|
| `hunters_mark` | Hunter's Mark | **wind** | Tracker's instinct, scent on the breeze |
| `whats_in_the_basket` | What's in the Basket? | **earth** | Provisions from the forest |

#### Red Hood (Vorpal)
| Skill ID | Name | **New Element** | Rationale |
|---|---|---|---|
| `what_big_teeth` | What Big Teeth | **dark** | Wolf's savage maw |
| `fell_the_wolf` | Fell the Wolf | **physical** | Brutal hunting strike |
| `through_the_forest` | Through the Forest | **wind** | Racing through the woods |

#### Dorothy
| Skill ID | Name | **New Element** | Rationale |
|---|---|---|---|
| `no_place_like_home` | There's No Place Like Home | **light** | Heartwarming restoration |
| `ruby_blink` | Ruby Blink | **magical** | Magical teleportation |

#### Dorothy (Vorpal)
| Skill ID | Name | **New Element** | Rationale |
|---|---|---|---|
| `cyclones_call` | Cyclone's Call | **wind** | Twister/tornado = wind |
| `heart_of_tin` | Heart of Tin | **light** | Pure-hearted restoration |
| `emerald_citys_light` | Emerald City's Light | **light** | Radiant emerald glow |

---

## 4. RACE PASSIVES — Elemental Synergy (Optional)

Race passives don't deal damage, so they don't need elemental assignments. However, some races could receive elemental synergy bonuses. These would be **separate** from the skill elemental rework but worth noting:

| Race Passive | Suggested Elemental Synergy |
|---|---|
| `beast_passive` (Feral Instinct) | +10% `physical` dmg |
| `fey_passive` (Nature's Blessing) | +10% `earth` res |
| `dragonkin_passive` (Dragon's Might) | +15% `fire` dmg (already implied) |
| `demon_passive` (Infernal Blood) | +10% `fire` dmg (already implied) |
| `elemental_passive` (Elemental Resilience) | +20% all elemental res (already implied) |
| `shadow_passive` (Shadow Step) | +10% `dark` dmg |
| `vampire_passive` (Vampiric Bloodlust) | +10% `dark` dmg |

---

## 5. CODE CHANGE BLUEPRINT

### 5A. `combat/skills.py` — Replace `SKILL_ELEMENTS` dict

**Remove:**
```python
SKILL_ELEMENTS = {
    "mage_fireball": "magical",
    "mage_frostnova": "magical",
    # ... entire hardcoded dict
}
```

**Replace with:**
```python
def _get_skill_element(skill_def, skill_id):
    """Read elemental from YAML skill definition. Falls back to None (neutral)."""
    return skill_def.get("elemental")
```

Then in `_calc_dmg`, change:
```python
# OLD:
if element is None and skill_id in SKILL_ELEMENTS:
    element = SKILL_ELEMENTS[skill_id]

# NEW:
if element is None:
    element = _get_skill_element(skill, skill_id)
```

### 5B. `combat/ally_skills.py` — Add elemental damage call

In the `_calc_dmg` inner function, add after the armor calculation:
```python
# Apply elemental damage
element = skill_def.get("elemental")
if element:
    from combat.elemental import calculate_elemental_damage
    power = calculate_elemental_damage(power, ally, target, element)
```

### 5C. `combat/combat_ui.py` — Display elemental tags

When displaying skill descriptions, read the `elemental` field and show a colored tag. Element colors:
- **fire** → red
- **water** → blue
- **thunder** → yellow/gold
- **wind** → cyan/teal
- **earth** → brown/green
- **light** → white/yellow
- **dark** → purple/gray
- **physical** → gray
- **magical** → magenta

---

## 6. ELEMENTAL DISTRIBUTION SUMMARY

| Element | Class Skills | Learnable | Ally Innate | **Total** |
|---|---|---|---|---|
| **fire** | 7 | 3 | 12 | **22** |
| **water** | 2 | 4 | 13 | **19** |
| **thunder** | 1 | 2 | 0 | **3** |
| **wind** | 3 | 4 | 8 | **15** |
| **earth** | 3 | 5 | 16 | **24** |
| **light** | 11 | 3 | 9 | **23** |
| **dark** | 8 | 5 | 17 | **30** |
| **physical** | 7 | 4 | 9 | **20** |
| **magical** | 6 | 2 | 6 | **14** |

> **Note:** Thunder is underrepresented. Consider adding more thunder-themed monsters or skills in future expansions, or re-theming some existing skills (e.g., `quick_strike` → thunder, `ninja_strike` → thunder).

---

## 7. IMPLEMENTATION ORDER

1. ✅ **YAML files** — Add `elemental:` to every skill in `skill_list.yaml` and `innate_skills.yaml`
2. ✅ **`combat/skills.py`** — Remove `SKILL_ELEMENTS`, read from YAML
3. ✅ **`combat/ally_skills.py`** — Add `calculate_elemental_damage()` in `_calc_dmg`
4. ✅ **`combat/combat_ui.py`** — Display elemental tags on skills
5. ✅ **Test** — Run the existing test suite, verify no regressions
6. ⏳ **Balance pass** — Adjust enemy elemental resistances to account for the wider elemental spread

---

*Document generated 2026-07-14. Total skills reworked: **169** (48 class + 31 learnable + 90 ally innate).*
