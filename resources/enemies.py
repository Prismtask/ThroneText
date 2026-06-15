ENEMY_RACES = {
    "Human": {"mods": {}},
    "Goblin": {"mods": {"Dexterity": 2, "Strength": -1, "Constitution": -1}},
    "Orc": {"mods": {"Strength": 3, "Constitution": 1, "Charisma": -2}},
    "Undead": {"mods": {"Constitution": 3, "Wisdom": -2, "Charisma": -3}},
    "Beast": {"mods": {"Strength": 2, "Dexterity": 1, "Learning": -3}},
    "Demon": {"mods": {"Strength": 2, "Charisma": 2, "Wisdom": -1}},
    "Construct": {"mods": {"Strength": 2, "Constitution": 4, "Charisma": -5}},
    "Dragonkin": {"mods": {"Strength": 3, "Constitution": 2, "Learning": -2}},
    "Fey": {"mods": {"Dexterity": 3, "Charisma": 2, "Strength": -2}},
    "Elemental": {"mods": {"Constitution": 3, "Learning": 2, "Dexterity": -1}},
    "Giant": {"mods": {"Strength": 4, "Constitution": 2, "Dexterity": -3}},
    "Vampire": {"mods": {"Dexterity": 3, "Charisma": 2, "Wisdom": -1, "Constitution": 1}},
    "Lizardfolk": {"mods": {"Constitution": 2, "Strength": 1, "Learning": -1}},
    "Gnome": {"mods": {"Learning": 2, "Dexterity": 1, "Strength": -2}},
    "Shadow": {"mods": {"Dexterity": 3, "Wisdom": -1, "Constitution": -1}},
    "Clockwork": {"mods": {"Constitution": 3, "Learning": 1, "Charisma": -4}},
    "Abomination": {"mods": {"Strength": 4, "Constitution": 3, "Wisdom": -3, "Charisma": -4}},
}

BIOME_RACES = {
    "temperate": ["Human", "Goblin", "Beast", "Undead", "Fey", "Gnome", "Lizardfolk", "Shadow", "Abomination", "Vampire"],
    "coastal":   ["Human", "Lizardfolk", "Beast", "Elemental", "Undead", "Vampire", "Giant"],
    "forest":    ["Beast", "Fey", "Goblin", "Human", "Gnome", "Elemental", "Dragonkin"],
    "swamp":     ["Undead", "Lizardfolk", "Abomination", "Beast", "Shadow", "Vampire"],
    "mountain":  ["Orc", "Giant", "Dragonkin", "Construct", "Human", "Elemental"],
    "desert":    ["Human", "Undead", "Lizardfolk", "Elemental", "Gnome", "Beast"],
    "volcanic":  ["Demon", "Elemental", "Dragonkin", "Construct", "Giant"],
    "magical":   ["Fey", "Construct", "Clockwork", "Elemental", "Gnome", "Shadow", "Abomination"],
}

ENEMIES = {
    # ----- LOW LEVEL (1–3) -----
    "bandit": {
        "name": "Bandit", "race": "Human", "level": 2, "base_hp": 19,
        "mods": {"Dexterity": 1}, "boss": False, "super_boss": False
    },
    "cave_rat": {
        "name": "Cave Rat", "race": "Beast", "level": 1, "base_hp": 10,
        "mods": {}, "boss": False, "super_boss": False
    },
    "coastal_raider": {
        "name": "Coastal Raider", "race": "Human", "level": 3, "base_hp": 22,
        "mods": {"Dexterity": 2}, "boss": False, "super_boss": False
    },
    "novice_mage": {
        "name": "Novice Mage", "race": "Human", "level": 3, "base_hp": 18,
        "mods": {"Learning": 2}, "boss": False, "super_boss": False
    },
    "desert_viper": {
        "name": "Desert Viper", "race": "Beast", "level": 3, "base_hp": 20,
        "mods": {"Dexterity": 3}, "boss": False, "super_boss": False
    },
    "fey_sprite": {
        "name": "Fey Sprite", "race": "Fey", "level": 3, "base_hp": 14,
        "mods": {"Dexterity": 2, "Charisma": 1}, "boss": False, "super_boss": False
    },
    "forest_spider": {
        "name": "Forest Spider", "race": "Beast", "level": 1, "base_hp": 12,
        "mods": {"Dexterity": 2}, "boss": False, "super_boss": False
    },
    "forest_venom_spitter": {
        "name": "Forest Venom Spitter", "race": "Beast", "level": 3, "base_hp": 18,
        "mods": {"Dexterity": 3}, "boss": False, "super_boss": False
    },
    "gnome_tinker": {
        "name": "Gnome Tinker", "race": "Gnome", "level": 1, "base_hp": 11,
        "mods": {"Learning": 1}, "boss": False, "super_boss": False
    },
    "goblin_archer": {
        "name": "Goblin Archer", "race": "Goblin", "level": 2, "base_hp": 15,
        "mods": {"Dexterity": 3}, "boss": False, "super_boss": False
    },
    "goblin_girl": {
        "name": "Goblin Girl", "race": "Goblin", "level": 2, "base_hp": 14,
        "mods": {"Dexterity": 2, "Charisma": 1}, "boss": False, "super_boss": False
    }, # Monster Girl
    "goblin_knifer": {
        "name": "Goblin Knifer", "race": "Goblin", "level": 2, "base_hp": 17,
        "mods": {"Dexterity": 2}, "boss": False, "super_boss": False
    },
    "goblin_scout": {
        "name": "Goblin Scout", "race": "Goblin", "level": 1, "base_hp": 13,
        "mods": {"Dexterity": 1}, "boss": False, "super_boss": False
    },
    "goblin_thief": {
        "name": "Goblin Thief", "race": "Goblin", "level": 1, "base_hp": 11,
        "mods": {"Dexterity": 2}, "boss": False, "super_boss": False
    },
    "goblin_shaman": {
        "name": "Goblin Shaman", "race": "Goblin", "level": 2, "base_hp": 14,
        "mods": {"Wisdom": 1}, "boss": False, "super_boss": False
    },
    "imp": {
        "name": "Imp", "race": "Demon", "level": 1, "base_hp": 12,
        "mods": {"Dexterity": 2}, "boss": False, "super_boss": False
    },
    "lesser_imp": {
        "name": "Lesser Imp", "race": "Demon", "level": 1, "base_hp": 11,
        "mods": {"Charisma": 1}, "boss": False, "super_boss": False
    },
    "lizardfolk_hunter": {
        "name": "Lizardfolk Hunter", "race": "Lizardfolk", "level": 2, "base_hp": 18,
        "mods": {"Dexterity": 1}, "boss": False, "super_boss": False
    },
    "magical_rune_dust": {
        "name": "Rune Dust", "race": "Elemental", "level": 2, "base_hp": 14,
        "mods": {"Learning": 2}, "boss": False, "super_boss": False
    },
    "mountain_rock_thrower": {
        "name": "Rock Thrower", "race": "Giant", "level": 4, "base_hp": 34,
        "mods": {"Strength": 2}, "boss": False, "super_boss": False
    },
    "pixie_trickster": {
        "name": "Pixie Trickster", "race": "Fey", "level": 2, "base_hp": 13,
        "mods": {"Dexterity": 3}, "boss": False, "super_boss": False
    },
    "rotten_carcass": {
        "name": "Rotten Carcass", "race": "Undead", "level": 3, "base_hp": 25,
        "mods": {"Constitution": 2}, "boss": False, "super_boss": False
    },
    "shadow_stalker": {
        "name": "Shadow Stalker", "race": "Shadow", "level": 3, "base_hp": 16,
        "mods": {"Dexterity": 2}, "boss": False, "super_boss": False
    },
    "skeleton": {
        "name": "Skeleton", "race": "Undead", "level": 2, "base_hp": 18,
        "mods": {}, "boss": False, "super_boss": False
    },
    "swamp_mud_crawler": {
        "name": "Mud Crawler", "race": "Beast", "level": 2, "base_hp": 16,
        "mods": {"Constitution": 2}, "boss": False, "super_boss": False
    },
    "temperate_bandit_leader": {
        "name": "Bandit Leader", "race": "Human", "level": 3, "base_hp": 24,
        "mods": {"Strength": 1, "Dexterity": 1}, "boss": False, "super_boss": False
    },
    "thief": {
        "name": "Thief", "race": "Human", "level": 2, "base_hp": 16,
        "mods": {"Dexterity": 2}, "boss": False, "super_boss": False
    },
    "wild_dog": {
        "name": "Wild Dog", "race": "Beast", "level": 1, "base_hp": 14,
        "mods": {}, "boss": False, "super_boss": False
    },
    "zombie_minion": {
        "name": "Zombie Minion", "race": "Undead", "level": 3, "base_hp": 22,
        "mods": {"Constitution": 1}, "boss": False, "super_boss": False
    },

    # ===== NEW LOW-LEVEL ENEMIES (filling gaps) =====
    "goblin_ratcatcher": {
        "name": "Goblin Ratcatcher", "race": "Goblin", "level": 1, "base_hp": 11,
        "mods": {"Dexterity": 1}, "boss": False, "super_boss": False
    },
    "goblin_whisperer": {
        "name": "Goblin Whisperer", "race": "Goblin", "level": 2, "base_hp": 16,
        "mods": {"Charisma": 2}, "boss": False, "super_boss": False
    },
    "gnome_clockwork_helper": {
        "name": "Clockwork Helper", "race": "Gnome", "level": 2, "base_hp": 12,
        "mods": {"Learning": 1}, "boss": False, "super_boss": False
    },
    "gnome_mushroom_farmer": {
        "name": "Mushroom Farmer", "race": "Gnome", "level": 3, "base_hp": 14,
        "mods": {"Constitution": 1}, "boss": False, "super_boss": False
    },
    "lizardfolk_egg_stealer": {
        "name": "Egg Stealer", "race": "Lizardfolk", "level": 1, "base_hp": 14,
        "mods": {"Dexterity": 2}, "boss": False, "super_boss": False
    },
    "lizardfolk_scout": {
        "name": "Lizardfolk Scout", "race": "Lizardfolk", "level": 3, "base_hp": 20,
        "mods": {"Dexterity": 2}, "boss": False, "super_boss": False
    },
    "shadow_rat": {
        "name": "Shadow Rat", "race": "Shadow", "level": 2, "base_hp": 12,
        "mods": {"Dexterity": 2}, "boss": False, "super_boss": False
    },
    "shadow_creeper": {
        "name": "Shadow Creeper", "race": "Shadow", "level": 4, "base_hp": 20,
        "mods": {"Dexterity": 2}, "boss": False, "super_boss": False
    },
    "beast_wolf_pup": {
        "name": "Wolf Pup", "race": "Beast", "level": 1, "base_hp": 9,
        "mods": {}, "boss": False, "super_boss": False
    },
    "beast_feral_cat": {
        "name": "Feral Cat", "race": "Beast", "level": 2, "base_hp": 13,
        "mods": {"Dexterity": 1}, "boss": False, "super_boss": False
    },
    "human_footpad": {
        "name": "Footpad", "race": "Human", "level": 1, "base_hp": 15,
        "mods": {"Dexterity": 1}, "boss": False, "super_boss": False
    },
    "human_peasant_brigand": {
        "name": "Peasant Brigand", "race": "Human", "level": 1, "base_hp": 14,
        "mods": {}, "boss": False, "super_boss": False
    },
    "orc_half_breed_outcast": {
        "name": "Half-Orc Outcast", "race": "Orc", "level": 4, "base_hp": 26,
        "mods": {"Strength": 1}, "boss": False, "super_boss": False
    },
    "undead_rotting_hand": {
        "name": "Rotting Hand", "race": "Undead", "level": 1, "base_hp": 12,
        "mods": {"Strength": -1}, "boss": False, "super_boss": False
    },
    "undead_banshee_wailer": {
        "name": "Banshee Wailer", "race": "Undead", "level": 5, "base_hp": 26,
        "mods": {"Dexterity": 2, "Charisma": -1}, "boss": False, "super_boss": False
    },
    "demon_cinder_spirit": {
        "name": "Cinder Spirit", "race": "Demon", "level": 2, "base_hp": 16,
        "mods": {"Constitution": 1}, "boss": False, "super_boss": False
    },
    "demon_brimstone_imp": {
        "name": "Brimstone Imp", "race": "Demon", "level": 3, "base_hp": 18,
        "mods": {"Dexterity": 2}, "boss": False, "super_boss": False
    },
    "fey_glowmoth": {
        "name": "Glowmoth", "race": "Fey", "level": 1, "base_hp": 10,
        "mods": {"Dexterity": 1}, "boss": False, "super_boss": False
    },
    "fey_leaf_whisper": {
        "name": "Leaf Whisper", "race": "Fey", "level": 4, "base_hp": 18,
        "mods": {"Dexterity": 2}, "boss": False, "super_boss": False
    },
    "elemental_spark": {
        "name": "Spark", "race": "Elemental", "level": 1, "base_hp": 11,
        "mods": {"Dexterity": 1}, "boss": False, "super_boss": False
    },
    "elemental_pebble": {
        "name": "Pebble", "race": "Elemental", "level": 3, "base_hp": 18,
        "mods": {"Constitution": 2}, "boss": False, "super_boss": False
    },
    "giant_tiny_troll": {
        "name": "Tiny Troll", "race": "Giant", "level": 1, "base_hp": 20,
        "mods": {"Strength": 1}, "boss": False, "super_boss": False
    },
    "vampire_bat_swarm": {
        "name": "Bat Swarm", "race": "Vampire", "level": 8, "base_hp": 32,
        "mods": {"Dexterity": 3}, "boss": False, "super_boss": False
    },

    # ----- MID LEVEL (4–6) -----
    "battle_hound": {
        "name": "Battle Hound", "race": "Beast", "level": 5, "base_hp": 31,
        "mods": {"Dexterity": 2, "Strength": 1}, "boss": False, "super_boss": False
    },
    "clockwork_sentinel": {
        "name": "Clockwork Sentinel", "race": "Clockwork", "level": 4, "base_hp": 29,
        "mods": {"Strength": 1}, "boss": False, "super_boss": False
    },
    "clockwork_spy": {
        "name": "Clockwork Spy", "race": "Clockwork", "level": 6, "base_hp": 30,
        "mods": {"Dexterity": 2}, "boss": False, "super_boss": False
    },
    "cultist": {
        "name": "Cultist", "race": "Human", "level": 5, "base_hp": 26,
        "mods": {"Learning": 1}, "boss": False, "super_boss": False
    },
    "dire_wolf": {
        "name": "Dire Wolf", "race": "Beast", "level": 4, "base_hp": 32,
        "mods": {"Dexterity": 1}, "boss": False, "super_boss": False
    },
    "fire_elemental": {
        "name": "Fire Elemental", "race": "Elemental", "level": 5, "base_hp": 37,
        "mods": {"Constitution": 2}, "boss": False, "super_boss": False
    },
    "ghoul": {
        "name": "Ghoul", "race": "Undead", "level": 6, "base_hp": 38,
        "mods": {"Strength": 2}, "boss": False, "super_boss": False
    },
    "gnoll_marauder": {
        "name": "Gnoll Marauder", "race": "Beast", "level": 4, "base_hp": 30,
        "mods": {"Strength": 2}, "boss": False, "super_boss": False
    },
    "gnome_illusionist": {
        "name": "Gnome Illusionist", "race": "Gnome", "level": 5, "base_hp": 24,
        "mods": {"Learning": 2, "Charisma": 1}, "boss": False, "super_boss": False
    },
    "harpy_scout": {
        "name": "Harpy Scout", "race": "Beast", "level": 5, "base_hp": 27,
        "mods": {"Dexterity": 3, "Charisma": 1}, "boss": False, "super_boss": False
    }, # Monster Girl
    "ice_elemental": {
        "name": "Ice Elemental", "race": "Elemental", "level": 5, "base_hp": 35,
        "mods": {"Constitution": 3}, "boss": False, "super_boss": False
    },
    "lesser_abomination": {
        "name": "Lesser Abomination", "race": "Abomination", "level": 6, "base_hp": 48,
        "mods": {"Strength": 2}, "boss": False, "super_boss": False
    },
    "lizardfolk_spearman": {
        "name": "Lizardfolk Spearman", "race": "Lizardfolk", "level": 4, "base_hp": 31,
        "mods": {"Dexterity": 1}, "boss": False, "super_boss": False
    },
    "lizardfolk_warrior": {
        "name": "Lizardfolk Warrior", "race": "Lizardfolk", "level": 5, "base_hp": 35,
        "mods": {"Strength": 2}, "boss": False, "super_boss": False
    },
    "mercenary": {
        "name": "Mercenary", "race": "Human", "level": 5, "base_hp": 32,
        "mods": {"Strength": 1, "Constitution": 1}, "boss": False, "super_boss": False
    },
    "orc_brute": {
        "name": "Orc Brute", "race": "Orc", "level": 5, "base_hp": 34,
        "mods": {"Strength": 2}, "boss": False, "super_boss": False
    },
    "orc_grunt": {
        "name": "Orc Grunt", "race": "Orc", "level": 4, "base_hp": 28,
        "mods": {"Strength": 1}, "boss": False, "super_boss": False
    },
    "orc_shaman": {
        "name": "Orc Shaman", "race": "Orc", "level": 5, "base_hp": 27,
        "mods": {"Learning": 2, "Wisdom": 1}, "boss": False, "super_boss": False
    },
    "shadow_assassin": {
        "name": "Shadow Assassin", "race": "Shadow", "level": 6, "base_hp": 33,
        "mods": {"Dexterity": 3}, "boss": False, "super_boss": False
    },
    "shadow_wraithling": {
        "name": "Shadow Wraithling", "race": "Shadow", "level": 6, "base_hp": 28,
        "mods": {"Dexterity": 2}, "boss": False, "super_boss": False
    },
    "spectral_knight": {
        "name": "Spectral Knight", "race": "Undead", "level": 6, "base_hp": 40,
        "mods": {"Dexterity": 1}, "boss": False, "super_boss": False
    },
    "venom_wolf": {
        "name": "Venom Wolf", "race": "Beast", "level": 4, "base_hp": 29,
        "mods": {"Dexterity": 2}, "boss": False, "super_boss": False
    },
    "zombie": {
        "name": "Zombie", "race": "Undead", "level": 4, "base_hp": 33,
        "mods": {"Strength": 1}, "boss": False, "super_boss": False
    },

    # ===== NEW MID-LEVEL ENEMIES =====
    "human_bounty_hunter": {
        "name": "Bounty Hunter", "race": "Human", "level": 4, "base_hp": 28,
        "mods": {"Dexterity": 2, "Strength": 1}, "boss": False, "super_boss": False
    },
    "human_fencer": {
        "name": "Fencer", "race": "Human", "level": 6, "base_hp": 30,
        "mods": {"Dexterity": 3}, "boss": False, "super_boss": False
    },
    "human_archer_captain": {
        "name": "Archer Captain", "race": "Human", "level": 6, "base_hp": 28,
        "mods": {"Dexterity": 2, "Wisdom": 1}, "boss": False, "super_boss": False
    },
    "orc_raider": {
        "name": "Orc Raider", "race": "Orc", "level": 6, "base_hp": 36,
        "mods": {"Strength": 2, "Constitution": 1}, "boss": False, "super_boss": False
    },
    "orc_war_priest": {
        "name": "Orc War Priest", "race": "Orc", "level": 9, "base_hp": 44,
        "mods": {"Learning": 2, "Wisdom": 2}, "boss": False, "super_boss": False
    },
    "orc_blade_dancer": {
        "name": "Orc Blade Dancer", "race": "Orc", "level": 11, "base_hp": 58,
        "mods": {"Dexterity": 2, "Strength": 2}, "boss": False, "super_boss": False
    },
    "orc_berserker_chief": {
        "name": "Berserker Chief", "race": "Orc", "level": 12, "base_hp": 72,
        "mods": {"Strength": 4, "Constitution": 1}, "boss": False, "super_boss": False
    },
    "undead_corpse_swarm": {
        "name": "Corpse Swarm", "race": "Undead", "level": 5, "base_hp": 28,
        "mods": {"Constitution": 2}, "boss": False, "super_boss": False
    },
    "undead_festering_zombie": {
        "name": "Festering Zombie", "race": "Undead", "level": 8, "base_hp": 42,
        "mods": {"Constitution": 2, "Strength": 1}, "boss": False, "super_boss": False
    },
    "undead_drowned_captain": {
        "name": "Drowned Captain", "race": "Undead", "level": 12, "base_hp": 58,
        "mods": {"Strength": 2, "Constitution": 2}, "boss": False, "super_boss": False
    },
    "undead_phantom_archer": {
        "name": "Phantom Archer", "race": "Undead", "level": 14, "base_hp": 62,
        "mods": {"Dexterity": 3}, "boss": False, "super_boss": False
    },
    "undead_rotting_giant": {
        "name": "Rotting Giant", "race": "Undead", "level": 16, "base_hp": 88,
        "mods": {"Strength": 3, "Constitution": 2}, "boss": False, "super_boss": False
    },
    "undead_lich_servitor": {
        "name": "Lich Servitor", "race": "Undead", "level": 18, "base_hp": 78,
        "mods": {"Learning": 3}, "boss": False, "super_boss": False
    },
    "undead_death_guard": {
        "name": "Death Guard", "race": "Undead", "level": 20, "base_hp": 90,
        "mods": {"Strength": 2, "Constitution": 3}, "boss": False, "super_boss": False
    },
    "beast_maned_hyena": {
        "name": "Maned Hyena", "race": "Beast", "level": 4, "base_hp": 26,
        "mods": {"Strength": 1, "Dexterity": 1}, "boss": False, "super_boss": False
    },
    "beast_snow_leopard": {
        "name": "Snow Leopard", "race": "Beast", "level": 6, "base_hp": 32,
        "mods": {"Dexterity": 3}, "boss": False, "super_boss": False
    },
    "beast_rock_crab": {
        "name": "Rock Crab", "race": "Beast", "level": 7, "base_hp": 44,
        "mods": {"Constitution": 2}, "boss": False, "super_boss": False
    },
    "beast_giant_wasp": {
        "name": "Giant Wasp", "race": "Beast", "level": 8, "base_hp": 38,
        "mods": {"Dexterity": 3}, "boss": False, "super_boss": False
    },
    "beast_thunder_bird": {
        "name": "Thunder Bird", "race": "Beast", "level": 9, "base_hp": 46,
        "mods": {"Dexterity": 2, "Strength": 1}, "boss": False, "super_boss": False
    },
    "beast_alpha_wolf": {
        "name": "Alpha Wolf", "race": "Beast", "level": 10, "base_hp": 52,
        "mods": {"Strength": 2, "Dexterity": 2}, "boss": False, "super_boss": False
    },
    "beast_cave_bear": {
        "name": "Cave Bear", "race": "Beast", "level": 13, "base_hp": 70,
        "mods": {"Strength": 3, "Constitution": 2}, "boss": False, "super_boss": False
    },
    "beast_sabertooth_tiger": {
        "name": "Sabertooth Tiger", "race": "Beast", "level": 14, "base_hp": 74,
        "mods": {"Strength": 3, "Dexterity": 2}, "boss": False, "super_boss": False
    },
    "beast_mammoth": {
        "name": "Mammoth", "race": "Beast", "level": 16, "base_hp": 92,
        "mods": {"Strength": 4, "Constitution": 2}, "boss": False, "super_boss": False
    },
    "beast_great_wyvern": {
        "name": "Great Wyvern", "race": "Beast", "level": 17, "base_hp": 85,
        "mods": {"Strength": 3, "Dexterity": 2}, "boss": False, "super_boss": False
    },
    "beast_thunder_lizard": {
        "name": "Thunder Lizard", "race": "Beast", "level": 21, "base_hp": 110,
        "mods": {"Strength": 4, "Constitution": 3}, "boss": False, "super_boss": False
    },
    "beast_roc_chick": {
        "name": "Roc Chick", "race": "Beast", "level": 22, "base_hp": 105,
        "mods": {"Strength": 3, "Dexterity": 2}, "boss": False, "super_boss": False
    },
    "beast_sea_serpent": {
        "name": "Sea Serpent", "race": "Beast", "level": 25, "base_hp": 125,
        "mods": {"Strength": 4, "Constitution": 3}, "boss": False, "super_boss": False
    },
    "demon_hellcat": {
        "name": "Hellcat", "race": "Demon", "level": 4, "base_hp": 24,
        "mods": {"Dexterity": 2, "Strength": 1}, "boss": False, "super_boss": False
    },
    "demon_malebranche": {
        "name": "Malebranche", "race": "Demon", "level": 7, "base_hp": 42,
        "mods": {"Strength": 2, "Constitution": 1}, "boss": False, "super_boss": False
    },
    "demon_pain_master": {
        "name": "Pain Master", "race": "Demon", "level": 12, "base_hp": 68,
        "mods": {"Strength": 2, "Charisma": 2}, "boss": False, "super_boss": False
    },
    "demon_abyssal_knight": {
        "name": "Abyssal Knight", "race": "Demon", "level": 14, "base_hp": 80,
        "mods": {"Strength": 3, "Constitution": 1}, "boss": False, "super_boss": False
    },
    "demon_void_imp": {
        "name": "Void Imp", "race": "Demon", "level": 16, "base_hp": 68,
        "mods": {"Dexterity": 3}, "boss": False, "super_boss": False
    },
    "demon_shadow_demon": {
        "name": "Shadow Demon", "race": "Demon", "level": 19, "base_hp": 94,
        "mods": {"Dexterity": 4, "Wisdom": 1}, "boss": False, "super_boss": False
    },
    "demon_marilith": {
        "name": "Marilith", "race": "Demon", "level": 22, "base_hp": 110,
        "mods": {"Strength": 4, "Dexterity": 3}, "boss": False, "super_boss": False
    },
    "construct_bronze_sentinel": {
        "name": "Bronze Sentinel", "race": "Construct", "level": 9, "base_hp": 52,
        "mods": {"Strength": 2}, "boss": False, "super_boss": False
    },
    "construct_silver_warden": {
        "name": "Silver Warden", "race": "Construct", "level": 10, "base_hp": 58,
        "mods": {"Constitution": 2}, "boss": False, "super_boss": False
    },
    "construct_obsidian_guard": {
        "name": "Obsidian Guard", "race": "Construct", "level": 14, "base_hp": 78,
        "mods": {"Strength": 3}, "boss": False, "super_boss": False
    },
    "construct_mithril_golem": {
        "name": "Mithril Golem", "race": "Construct", "level": 15, "base_hp": 88,
        "mods": {"Constitution": 3, "Strength": 2}, "boss": False, "super_boss": False
    },
    "construct_rune_guardian": {
        "name": "Rune Guardian", "race": "Construct", "level": 17, "base_hp": 92,
        "mods": {"Learning": 2, "Constitution": 2}, "boss": False, "super_boss": False
    },
    "construct_colossal_statue": {
        "name": "Colossal Statue", "race": "Construct", "level": 19, "base_hp": 110,
        "mods": {"Strength": 4, "Constitution": 2}, "boss": False, "super_boss": False
    },
    "construct_star_metal_golem": {
        "name": "Star Metal Golem", "race": "Construct", "level": 22, "base_hp": 125,
        "mods": {"Strength": 4, "Constitution": 3}, "boss": False, "super_boss": False
    },
    "dragonkin_scorched_zealot": {
        "name": "Scorched Zealot", "race": "Dragonkin", "level": 10, "base_hp": 58,
        "mods": {"Strength": 2, "Constitution": 2}, "boss": False, "super_boss": False
    },
    "dragonkin_flame_weaver": {
        "name": "Flame Weaver", "race": "Dragonkin", "level": 12, "base_hp": 68,
        "mods": {"Learning": 2, "Strength": 1}, "boss": False, "super_boss": False
    },
    "dragonkin_storm_roarer": {
        "name": "Storm Roarer", "race": "Dragonkin", "level": 15, "base_hp": 84,
        "mods": {"Strength": 3, "Dexterity": 1}, "boss": False, "super_boss": False
    },
    "dragonkin_iron_scale": {
        "name": "Iron Scale", "race": "Dragonkin", "level": 17, "base_hp": 98,
        "mods": {"Constitution": 3, "Strength": 2}, "boss": False, "super_boss": False
    },
    "dragonkin_ancient_guardian": {
        "name": "Ancient Guardian", "race": "Dragonkin", "level": 20, "base_hp": 118,
        "mods": {"Strength": 4, "Constitution": 2}, "boss": False, "super_boss": False
    },
    "dragonkin_sky_terror": {
        "name": "Sky Terror", "race": "Dragonkin", "level": 25, "base_hp": 138,
        "mods": {"Strength": 4, "Dexterity": 2}, "boss": False, "super_boss": False
    },
    "fey_moss_guardian": {
        "name": "Moss Guardian", "race": "Fey", "level": 4, "base_hp": 20,
        "mods": {"Constitution": 2}, "boss": False, "super_boss": False
    },
    "fey_wisp_trickster": {
        "name": "Wisp Trickster", "race": "Fey", "level": 6, "base_hp": 28,
        "mods": {"Dexterity": 2, "Charisma": 1}, "boss": False, "super_boss": False
    },
    "fey_bramble_hulk": {
        "name": "Bramble Hulk", "race": "Fey", "level": 9, "base_hp": 44,
        "mods": {"Constitution": 2, "Strength": 1}, "boss": False, "super_boss": False
    },
    "fey_moon_dancer": {
        "name": "Moon Dancer", "race": "Fey", "level": 10, "base_hp": 48,
        "mods": {"Dexterity": 3, "Charisma": 2}, "boss": False, "super_boss": False
    },
    "fey_ancient_dryad": {
        "name": "Ancient Dryad", "race": "Fey", "level": 15, "base_hp": 74,
        "mods": {"Wisdom": 3, "Charisma": 2}, "boss": False, "super_boss": False
    },
    "elemental_sand_whirl": {
        "name": "Sand Whirl", "race": "Elemental", "level": 3, "base_hp": 16,
        "mods": {"Dexterity": 2}, "boss": False, "super_boss": False
    },
    "elemental_mud_geyser": {
        "name": "Mud Geyser", "race": "Elemental", "level": 4, "base_hp": 24,
        "mods": {"Constitution": 2}, "boss": False, "super_boss": False
    },
    "elemental_steam_vent": {
        "name": "Steam Vent", "race": "Elemental", "level": 6, "base_hp": 32,
        "mods": {"Dexterity": 1}, "boss": False, "super_boss": False
    },
    "elemental_crystal_shard": {
        "name": "Crystal Shard", "race": "Elemental", "level": 7, "base_hp": 38,
        "mods": {"Learning": 2, "Constitution": 1}, "boss": False, "super_boss": False
    },
    "elemental_ash_wraith": {
        "name": "Ash Wraith", "race": "Elemental", "level": 11, "base_hp": 58,
        "mods": {"Dexterity": 2}, "boss": False, "super_boss": False
    },
    "elemental_lightning_orb": {
        "name": "Lightning Orb", "race": "Elemental", "level": 16, "base_hp": 86,
        "mods": {"Dexterity": 3, "Learning": 1}, "boss": False, "super_boss": False
    },
    "giant_ogre_thug": {
        "name": "Ogre Thug", "race": "Giant", "level": 6, "base_hp": 48,
        "mods": {"Strength": 2}, "boss": False, "super_boss": False
    },
    "giant_cyclops": {
        "name": "Cyclops", "race": "Giant", "level": 9, "base_hp": 68,
        "mods": {"Strength": 3, "Constitution": 1}, "boss": False, "super_boss": False
    },
    "giant_frost_giant_brute": {
        "name": "Frost Giant Brute", "race": "Giant", "level": 10, "base_hp": 78,
        "mods": {"Strength": 3, "Constitution": 2}, "boss": False, "super_boss": False
    },
    "giant_fire_giant_forgemaster": {
        "name": "Fire Giant Forgemaster", "race": "Giant", "level": 12, "base_hp": 88,
        "mods": {"Strength": 4, "Constitution": 1}, "boss": False, "super_boss": False
    },
    "giant_cloud_giant_thunderer": {
        "name": "Cloud Giant Thunderer", "race": "Giant", "level": 14, "base_hp": 102,
        "mods": {"Strength": 3, "Constitution": 2}, "boss": False, "super_boss": False
    },
    "giant_mountain_behemoth": {
        "name": "Mountain Behemoth", "race": "Giant", "level": 16, "base_hp": 118,
        "mods": {"Strength": 4, "Constitution": 3}, "boss": False, "super_boss": False
    },
    "vampire_noble_brat": {
        "name": "Vampire Noble Brat", "race": "Vampire", "level": 10, "base_hp": 46,
        "mods": {"Dexterity": 2, "Charisma": 1}, "boss": False, "super_boss": False
    },
    "vampire_blood_scribe": {
        "name": "Blood Scribe", "race": "Vampire", "level": 13, "base_hp": 68,
        "mods": {"Learning": 2, "Charisma": 1}, "boss": False, "super_boss": False
    },
    "vampire_mist_walker": {
        "name": "Mist Walker", "race": "Vampire", "level": 14, "base_hp": 72,
        "mods": {"Dexterity": 3}, "boss": False, "super_boss": False
    },
    "vampire_night_claw": {
        "name": "Night Claw", "race": "Vampire", "level": 16, "base_hp": 82,
        "mods": {"Dexterity": 3, "Strength": 1}, "boss": False, "super_boss": False
    },
    "vampire_dread_visor": {
        "name": "Dread Visor", "race": "Vampire", "level": 19, "base_hp": 98,
        "mods": {"Strength": 2, "Charisma": 2}, "boss": False, "super_boss": False
    },
    "lizardfolk_swamp_witch": {
        "name": "Swamp Witch", "race": "Lizardfolk", "level": 6, "base_hp": 34,
        "mods": {"Learning": 2, "Wisdom": 1}, "boss": False, "super_boss": False
    },
    "lizardfolk_venom_priest": {
        "name": "Venom Priest", "race": "Lizardfolk", "level": 9, "base_hp": 48,
        "mods": {"Learning": 2, "Constitution": 1}, "boss": False, "super_boss": False
    },
    "lizardfolk_coastal_reaver": {
        "name": "Coastal Reaver", "race": "Lizardfolk", "level": 11, "base_hp": 62,
        "mods": {"Strength": 2, "Dexterity": 1}, "boss": False, "super_boss": False
    },
    "lizardfolk_ancient_guardian": {
        "name": "Ancient Guardian", "race": "Lizardfolk", "level": 12, "base_hp": 68,
        "mods": {"Constitution": 2, "Strength": 1}, "boss": False, "super_boss": False
    },
    "gnome_potion_thrower": {
        "name": "Potion Thrower", "race": "Gnome", "level": 4, "base_hp": 18,
        "mods": {"Dexterity": 2, "Learning": 1}, "boss": False, "super_boss": False
    },
    "gnome_gear_master": {
        "name": "Gear Master", "race": "Gnome", "level": 7, "base_hp": 32,
        "mods": {"Learning": 2, "Constitution": 1}, "boss": False, "super_boss": False
    },
    "gnome_arcane_trickster": {
        "name": "Arcane Trickster", "race": "Gnome", "level": 9, "base_hp": 38,
        "mods": {"Learning": 2, "Dexterity": 2}, "boss": False, "super_boss": False
    },
    "gnome_elemental_binder": {
        "name": "Elemental Binder", "race": "Gnome", "level": 10, "base_hp": 44,
        "mods": {"Learning": 3, "Charisma": 1}, "boss": False, "super_boss": False
    },
    "shadow_veil_hunter": {
        "name": "Veil Hunter", "race": "Shadow", "level": 5, "base_hp": 24,
        "mods": {"Dexterity": 3}, "boss": False, "super_boss": False
    },
    "shadow_night_terror": {
        "name": "Night Terror", "race": "Shadow", "level": 7, "base_hp": 32,
        "mods": {"Dexterity": 3, "Wisdom": -1}, "boss": False, "super_boss": False
    },
    "shadow_umbral_blade": {
        "name": "Umbral Blade", "race": "Shadow", "level": 14, "base_hp": 66,
        "mods": {"Dexterity": 4}, "boss": False, "super_boss": False
    },
    "shadow_dark_messenger": {
        "name": "Dark Messenger", "race": "Shadow", "level": 17, "base_hp": 80,
        "mods": {"Dexterity": 4, "Charisma": 1}, "boss": False, "super_boss": False
    },
    "shadow_abyssal_watcher": {
        "name": "Abyssal Watcher", "race": "Shadow", "level": 19, "base_hp": 94,
        "mods": {"Dexterity": 4, "Wisdom": 2}, "boss": False, "super_boss": False
    },
    "clockwork_scout_drone": {
        "name": "Scout Drone", "race": "Clockwork", "level": 5, "base_hp": 26,
        "mods": {"Dexterity": 2}, "boss": False, "super_boss": False
    },
    "clockwork_repair_bot": {
        "name": "Repair Bot", "race": "Clockwork", "level": 7, "base_hp": 34,
        "mods": {"Constitution": 1}, "boss": False, "super_boss": False
    },
    "clockwork_steam_juggernaut": {
        "name": "Steam Juggernaut", "race": "Clockwork", "level": 8, "base_hp": 48,
        "mods": {"Constitution": 2, "Strength": 1}, "boss": False, "super_boss": False
    },
    "clockwork_heavy_sentinel": {
        "name": "Heavy Sentinel", "race": "Clockwork", "level": 11, "base_hp": 64,
        "mods": {"Constitution": 2, "Strength": 2}, "boss": False, "super_boss": False
    },
    "clockwork_assassin_bot": {
        "name": "Assassin Bot", "race": "Clockwork", "level": 12, "base_hp": 56,
        "mods": {"Dexterity": 3}, "boss": False, "super_boss": False
    },
    "clockwork_chrono_stabilizer": {
        "name": "Chrono Stabilizer", "race": "Clockwork", "level": 15, "base_hp": 78,
        "mods": {"Learning": 3, "Constitution": 1}, "boss": False, "super_boss": False
    },
    "abomination_twisted_shambler": {
        "name": "Twisted Shambler", "race": "Abomination", "level": 7, "base_hp": 54,
        "mods": {"Strength": 2, "Constitution": 1}, "boss": False, "super_boss": False
    },
    "abomination_flesh_reaver": {
        "name": "Flesh Reaver", "race": "Abomination", "level": 8, "base_hp": 62,
        "mods": {"Strength": 3, "Dexterity": -1}, "boss": False, "super_boss": False
    },
    "abomination_bone_weaver": {
        "name": "Bone Weaver", "race": "Abomination", "level": 10, "base_hp": 72,
        "mods": {"Constitution": 2, "Learning": -1}, "boss": False, "super_boss": False
    },
    "abomination_eyestalk_horror": {
        "name": "Eyestalk Horror", "race": "Abomination", "level": 15, "base_hp": 98,
        "mods": {"Wisdom": 2, "Constitution": 2}, "boss": False, "super_boss": False
    },
    "abomination_maw_of_the_abyss": {
        "name": "Maw of the Abyss", "race": "Abomination", "level": 17, "base_hp": 110,
        "mods": {"Strength": 4, "Constitution": 2}, "boss": False, "super_boss": False
    },
    "abomination_void_crawler": {
        "name": "Void Crawler", "race": "Abomination", "level": 19, "base_hp": 124,
        "mods": {"Dexterity": 2, "Constitution": 3}, "boss": False, "super_boss": False
    },
    "abomination_dream_eater": {
        "name": "Dream Eater", "race": "Abomination", "level": 21, "base_hp": 135,
        "mods": {"Wisdom": 3, "Constitution": 2}, "boss": False, "super_boss": False
    },
    "abomination_abyssal_leviathan": {
        "name": "Abyssal Leviathan", "race": "Abomination", "level": 24, "base_hp": 160,
        "mods": {"Strength": 5, "Constitution": 4}, "boss": False, "super_boss": False
    },
    "abomination_chaos_spawn": {
        "name": "Chaos Spawn", "race": "Abomination", "level": 27, "base_hp": 180,
        "mods": {"Strength": 4, "Constitution": 4}, "boss": False, "super_boss": False
    },
    "abomination_doom_of_worlds": {
        "name": "Doom of Worlds", "race": "Abomination", "level": 30, "base_hp": 220,
        "mods": {"Strength": 6, "Constitution": 5}, "boss": False, "super_boss": False
    },

    # ----- HIGH LEVEL (7–9) -----
    "abomination_brute": {
        "name": "Abomination Brute", "race": "Abomination", "level": 9, "base_hp": 72,
        "mods": {"Strength": 3, "Constitution": 2}, "boss": False, "super_boss": False
    },
    "alraune_fledger": {
        "name": "Alraune Fledger", "race": "Fey", "level": 7, "base_hp": 40,
        "mods": {"Charisma": 3, "Learning": 1}, "boss": False, "super_boss": False
    }, # Monster Girl
    "arcane_clockwork": {
        "name": "Arcane Clockwork", "race": "Clockwork", "level": 9, "base_hp": 52,
        "mods": {"Learning": 3}, "boss": False, "super_boss": False
    },
    "blood_vampire": {
        "name": "Blood Vampire", "race": "Vampire", "level": 9, "base_hp": 52,
        "mods": {"Dexterity": 2, "Charisma": 2}, "boss": False, "super_boss": False
    },
    "bone_colossus": {
        "name": "Bone Colossus", "race": "Undead", "level": 9, "base_hp": 65,
        "mods": {"Constitution": 3}, "boss": False, "super_boss": False
    },
    "clockwork_guardian": {
        "name": "Clockwork Guardian", "race": "Clockwork", "level": 9, "base_hp": 58,
        "mods": {"Constitution": 2}, "boss": False, "super_boss": False
    },
    "dark_knight": {
        "name": "Dark Knight", "race": "Human", "level": 8, "base_hp": 52,
        "mods": {"Strength": 2, "Constitution": 2}, "boss": False, "super_boss": False
    },
    "elder_dragonkin": {
        "name": "Elder Dragonkin", "race": "Dragonkin", "level": 9, "base_hp": 68,
        "mods": {"Strength": 3, "Constitution": 1}, "boss": False, "super_boss": False
    },
    "elite_assassin": {
        "name": "Elite Assassin", "race": "Human", "level": 7, "base_hp": 42,
        "mods": {"Dexterity": 3}, "boss": False, "super_boss": False
    },
    "flame_salamander": {
        "name": "Flame Salamander", "race": "Elemental", "level": 8, "base_hp": 56,
        "mods": {"Dexterity": 2}, "boss": False, "super_boss": False
    },
    "gnome_skycaptain": {
        "name": "Gnome Skycaptain", "race": "Gnome", "level": 8, "base_hp": 39,
        "mods": {"Learning": 3, "Dexterity": 2}, "boss": False, "super_boss": False
    },
    "greater_demon": {
        "name": "Greater Demon", "race": "Demon", "level": 9, "base_hp": 58,
        "mods": {"Strength": 2, "Charisma": 2}, "boss": False, "super_boss": False
    },
    "hellhound": {
        "name": "Hellhound", "race": "Demon", "level": 6, "base_hp": 42,
        "mods": {"Dexterity": 1}, "boss": False, "super_boss": False
    },
    "hill_giant": {
        "name": "Hill Giant", "race": "Giant", "level": 8, "base_hp": 75,
        "mods": {"Strength": 3}, "boss": False, "super_boss": False
    },
    "iron_golem": {
        "name": "Iron Golem", "race": "Construct", "level": 8, "base_hp": 70,
        "mods": {"Strength": 1}, "boss": False, "super_boss": False
    },
    "lizardfolk_champion": {
        "name": "Lizardfolk Champion", "race": "Lizardfolk", "level": 7, "base_hp": 48,
        "mods": {"Strength": 2}, "boss": False, "super_boss": False
    },
    "lizardfolk_high_priest": {
        "name": "Lizardfolk High Priest", "race": "Lizardfolk", "level": 8, "base_hp": 44,
        "mods": {"Learning": 2, "Wisdom": 1}, "boss": False, "super_boss": False
    },
    "night_stalker": {
        "name": "Night Stalker", "race": "Shadow", "level": 8, "base_hp": 44,
        "mods": {"Dexterity": 4}, "boss": False, "super_boss": False
    },
    "orc_chieftain": {
        "name": "Orc Chieftain", "race": "Orc", "level": 8, "base_hp": 55,
        "mods": {"Strength": 2, "Constitution": 1}, "boss": False, "super_boss": False
    },
    "orc_warlord": {
        "name": "Orc Warlord", "race": "Orc", "level": 7, "base_hp": 48,
        "mods": {"Strength": 3, "Charisma": 1}, "boss": False, "super_boss": False
    },
    "shadow_lord": {
        "name": "Shadow Lord", "race": "Shadow", "level": 9, "base_hp": 47,
        "mods": {"Dexterity": 3, "Charisma": 1}, "boss": False, "super_boss": False
    },
    "stone_golem": {
        "name": "Stone Golem", "race": "Construct", "level": 8, "base_hp": 62,
        "mods": {}, "boss": False, "super_boss": False
    },
    "thunder_elemental": {
        "name": "Thunder Elemental", "race": "Elemental", "level": 9, "base_hp": 60,
        "mods": {"Constitution": 2}, "boss": False, "super_boss": False
    },
    "troll_regenerator": {
        "name": "Troll Regenerator", "race": "Giant", "level": 7, "base_hp": 68,
        "mods": {"Constitution": 3}, "boss": False, "super_boss": False
    },
    "vampire_spawn": {
        "name": "Vampire Spawn", "race": "Vampire", "level": 8, "base_hp": 45,
        "mods": {"Dexterity": 3}, "boss": False, "super_boss": False
    },
    "wraith": {
        "name": "Wraith", "race": "Undead", "level": 7, "base_hp": 38,
        "mods": {"Dexterity": 2}, "boss": False, "super_boss": False
    },
    "young_dragonkin": {
        "name": "Young Dragonkin", "race": "Dragonkin", "level": 7, "base_hp": 50,
        "mods": {"Strength": 3}, "boss": False, "super_boss": False
    },

    # ----- VERY HIGH LEVEL (10–16) -----
    "abomination_grunt": {
        "name": "Abomination Grunt", "race": "Abomination", "level": 12, "base_hp": 85,
        "mods": {"Strength": 3, "Constitution": 2}, "boss": False, "super_boss": False
    },
    "abomination_titan": {
        "name": "Abomination Titan", "race": "Abomination", "level": 16, "base_hp": 130,
        "mods": {"Strength": 5, "Constitution": 4}, "boss": False, "super_boss": False
    },
    "adamantine_golem": {
        "name": "Adamantine Golem", "race": "Construct", "level": 13, "base_hp": 95,
        "mods": {"Constitution": 3}, "boss": False, "super_boss": False
    },
    "ancient_construct_sentinel": {
        "name": "Ancient Construct Sentinel", "race": "Construct", "level": 11, "base_hp": 80,
        "mods": {"Strength": 2, "Constitution": 2}, "boss": False, "super_boss": False
    },
    "ancient_vampire": {
        "name": "Ancient Vampire", "race": "Vampire", "level": 12, "base_hp": 75,
        "mods": {"Dexterity": 3, "Charisma": 2}, "boss": False, "super_boss": False
    },
    "arcane_elemental": {
        "name": "Arcane Elemental", "race": "Elemental", "level": 10, "base_hp": 68,
        "mods": {"Learning": 4}, "boss": False, "super_boss": False
    },
    "archfey_sentinel": {
        "name": "Archfey Sentinel", "race": "Fey", "level": 14, "base_hp": 75,
        "mods": {"Dexterity": 3, "Charisma": 4}, "boss": False, "super_boss": False
    },
    "centaur_scout": {
        "name": "Centaur Scout", "race": "Beast", "level": 11, "base_hp": 64,
        "mods": {"Strength": 2, "Dexterity": 2}, "boss": False, "super_boss": False
    }, # Monster Girl
    "clockwork_executor": {
        "name": "Clockwork Executor", "race": "Clockwork", "level": 13, "base_hp": 78,
        "mods": {"Strength": 3, "Constitution": 2}, "boss": False, "super_boss": False
    },
    "clockwork_warrior": {
        "name": "Clockwork Warrior", "race": "Clockwork", "level": 10, "base_hp": 65,
        "mods": {"Constitution": 2, "Strength": 1}, "boss": False, "super_boss": False
    },
    "colossal_abomination": {
        "name": "Colossal Abomination", "race": "Abomination", "level": 13, "base_hp": 110,
        "mods": {"Strength": 5, "Constitution": 3}, "boss": False, "super_boss": False
    },
    "death_knight": {
        "name": "Death Knight", "race": "Undead", "level": 11, "base_hp": 68,
        "mods": {"Strength": 2, "Dexterity": 2}, "boss": False, "super_boss": False
    },
    "dragonkin_captain": {
        "name": "Dragonkin Captain", "race": "Dragonkin", "level": 14, "base_hp": 92,
        "mods": {"Strength": 3, "Constitution": 2, "Dexterity": 1}, "boss": False, "super_boss": False
    },
    "dragonkin_scout": {
        "name": "Dragonkin Scout", "race": "Dragonkin", "level": 11, "base_hp": 68,
        "mods": {"Dexterity": 2, "Strength": 2}, "boss": False, "super_boss": False
    },
    "elven_blade_dancer": {
        "name": "Elven Blade Dancer", "race": "Human", "level": 10, "base_hp": 58,
        "mods": {"Dexterity": 3, "Strength": 1}, "boss": False, "super_boss": False
    },
    "giant_frost_bear": {
        "name": "Giant Frost Bear", "race": "Beast", "level": 12, "base_hp": 78,
        "mods": {"Strength": 3, "Constitution": 2}, "boss": False, "super_boss": False
    },
    "great_forest_guardian": {
        "name": "Great Forest Guardian", "race": "Fey", "level": 12, "base_hp": 70,
        "mods": {"Dexterity": 3, "Charisma": 3}, "boss": False, "super_boss": False
    },
    "greater_abomination_brute": {
        "name": "Greater Abomination Brute", "race": "Abomination", "level": 14, "base_hp": 105,
        "mods": {"Strength": 4, "Constitution": 3}, "boss": False, "super_boss": False
    },
    "greater_lizardfolk_brute": {
        "name": "Greater Lizardfolk Brute", "race": "Lizardfolk", "level": 10, "base_hp": 72,
        "mods": {"Strength": 3, "Constitution": 1}, "boss": False, "super_boss": False
    },
    "greater_shadow_stalker": {
        "name": "Greater Shadow Stalker", "race": "Shadow", "level": 15, "base_hp": 80,
        "mods": {"Dexterity": 5, "Charisma": 2}, "boss": False, "super_boss": False
    },
    "infernal_hound": {
        "name": "Infernal Hound", "race": "Demon", "level": 10, "base_hp": 65,
        "mods": {"Strength": 2, "Dexterity": 2}, "boss": False, "super_boss": False
    },
    "infernal_priest": {
        "name": "Infernal Priest", "race": "Demon", "level": 11, "base_hp": 60,
        "mods": {"Learning": 3, "Charisma": 2}, "boss": False, "super_boss": False
    },
    "lamia_constrictor": {
        "name": "Lamia Constrictor", "race": "Lizardfolk", "level": 13, "base_hp": 76,
        "mods": {"Strength": 2, "Dexterity": 3}, "boss": False, "super_boss": False
    }, # Monster Girl
    "lizardfolk_ancient_one": {
        "name": "Lizardfolk Ancient One", "race": "Lizardfolk", "level": 15, "base_hp": 98,
        "mods": {"Strength": 3, "Constitution": 3, "Learning": 2}, "boss": False, "super_boss": False
    },
    "lizardfolk_warlord": {
        "name": "Lizardfolk Warlord", "race": "Lizardfolk", "level": 10, "base_hp": 70,
        "mods": {"Strength": 3}, "boss": False, "super_boss": False
    },
    "magma_elemental": {
        "name": "Magma Elemental", "race": "Elemental", "level": 13, "base_hp": 82,
        "mods": {"Constitution": 4, "Strength": 1}, "boss": False, "super_boss": False
    },
    "master_artificer": {
        "name": "Master Artificer", "race": "Gnome", "level": 11, "base_hp": 55,
        "mods": {"Learning": 4, "Dexterity": 2}, "boss": False, "super_boss": False
    },
    "mature_dragonkin": {
        "name": "Mature Dragonkin", "race": "Dragonkin", "level": 11, "base_hp": 82,
        "mods": {"Strength": 4, "Constitution": 2}, "boss": False, "super_boss": False
    },
    "orc_berserker": {
        "name": "Orc Berserker", "race": "Orc", "level": 10, "base_hp": 72,
        "mods": {"Strength": 4}, "boss": False, "super_boss": False
    },
    "orc_warbringer": {
        "name": "Orc Warbringer", "race": "Orc", "level": 13, "base_hp": 80,
        "mods": {"Strength": 4, "Constitution": 1}, "boss": False, "super_boss": False
    },
    "primeval_construct": {
        "name": "Primeval Construct", "race": "Construct", "level": 16, "base_hp": 115,
        "mods": {"Strength": 4, "Constitution": 5}, "boss": False, "super_boss": False
    },
    "shadow_hunter": {
        "name": "Shadow Hunter", "race": "Shadow", "level": 13, "base_hp": 66,
        "mods": {"Dexterity": 5}, "boss": False, "super_boss": False
    },
    "shadow_reaver": {
        "name": "Shadow Reaver", "race": "Shadow", "level": 10, "base_hp": 52,
        "mods": {"Dexterity": 4}, "boss": False, "super_boss": False
    },
    "slime_girl": {
        "name": "Slime Girl", "race": "Elemental", "level": 12, "base_hp": 88,
        "mods": {"Constitution": 4, "Dexterity": 2}, "boss": False, "super_boss": False
    }, # Monster Girl
    "storm_giant": {
        "name": "Storm Giant", "race": "Giant", "level": 11, "base_hp": 98,
        "mods": {"Strength": 4, "Constitution": 2}, "boss": False, "super_boss": False
    },
    "titan_clockwork": {
        "name": "Titan Clockwork", "race": "Clockwork", "level": 13, "base_hp": 88,
        "mods": {"Constitution": 4}, "boss": False, "super_boss": False
    },
    "titanic_behemoth": {
        "name": "Titanic Behemoth", "race": "Giant", "level": 15, "base_hp": 120,
        "mods": {"Strength": 5, "Constitution": 3}, "boss": False, "super_boss": False
    },
    "vampire_bloodknight": {
        "name": "Vampire Bloodknight", "race": "Vampire", "level": 11, "base_hp": 62,
        "mods": {"Dexterity": 3, "Strength": 1}, "boss": False, "super_boss": False
    },
    "void_elemental": {
        "name": "Void Elemental", "race": "Elemental", "level": 14, "base_hp": 88,
        "mods": {"Constitution": 3, "Learning": 3}, "boss": False, "super_boss": False
    },
    "void_shadow": {
        "name": "Void Shadow", "race": "Shadow", "level": 11, "base_hp": 58,
        "mods": {"Dexterity": 4}, "boss": False, "super_boss": False
    },
    "warlord_general": {
        "name": "Warlord General", "race": "Human", "level": 10, "base_hp": 62,
        "mods": {"Strength": 3, "Charisma": 2}, "boss": False, "super_boss": False
    },

    # ===== NEW VERY HIGH LEVEL ENEMIES (continuing from 16–20) =====
    "human_imperial_knight": {
        "name": "Imperial Knight", "race": "Human", "level": 9, "base_hp": 54,
        "mods": {"Strength": 2, "Constitution": 1}, "boss": False, "super_boss": False
    },
    "human_high_mage": {
        "name": "High Mage", "race": "Human", "level": 10, "base_hp": 48,
        "mods": {"Learning": 3}, "boss": False, "super_boss": False
    },
    "human_swordmaster": {
        "name": "Swordmaster", "race": "Human", "level": 10, "base_hp": 60,
        "mods": {"Dexterity": 3, "Strength": 1}, "boss": False, "super_boss": False
    },
    "human_blackguard": {
        "name": "Blackguard", "race": "Human", "level": 12, "base_hp": 72,
        "mods": {"Strength": 2, "Constitution": 2}, "boss": False, "super_boss": False
    },
    "orc_war_matriarch": {
        "name": "War Matriarch", "race": "Orc", "level": 12, "base_hp": 68,
        "mods": {"Strength": 3, "Wisdom": 1}, "boss": False, "super_boss": False
    },
    "orc_flesh_ripper": {
        "name": "Flesh Ripper", "race": "Orc", "level": 13, "base_hp": 76,
        "mods": {"Strength": 4, "Dexterity": -1}, "boss": False, "super_boss": False
    },
    "undead_crimson_knight": {
        "name": "Crimson Knight", "race": "Undead", "level": 15, "base_hp": 84,
        "mods": {"Strength": 2, "Constitution": 2}, "boss": False, "super_boss": False
    },
    "undead_void_lich": {
        "name": "Void Lich", "race": "Undead", "level": 25, "base_hp": 130,
        "mods": {"Learning": 5, "Constitution": 1}, "boss": False, "super_boss": False
    },
    "undead_eternal_sentinel": {
        "name": "Eternal Sentinel", "race": "Undead", "level": 28, "base_hp": 150,
        "mods": {"Strength": 3, "Constitution": 3}, "boss": False, "super_boss": False
    },
    "undead_spectral_dragon": {
        "name": "Spectral Dragon", "race": "Undead", "level": 32, "base_hp": 190,
        "mods": {"Strength": 4, "Dexterity": 2}, "boss": False, "super_boss": False
    },
    "beast_crag_wyrm": {
        "name": "Crag Wyrm", "race": "Beast", "level": 18, "base_hp": 98,
        "mods": {"Strength": 3, "Constitution": 2}, "boss": False, "super_boss": False
    },
    "beast_desert_worm": {
        "name": "Desert Worm", "race": "Beast", "level": 20, "base_hp": 112,
        "mods": {"Constitution": 4, "Strength": 1}, "boss": False, "super_boss": False
    },
    "beast_lightning_roc": {
        "name": "Lightning Roc", "race": "Beast", "level": 23, "base_hp": 118,
        "mods": {"Dexterity": 3, "Strength": 2}, "boss": False, "super_boss": False
    },
    "beast_titan_snake": {
        "name": "Titan Snake", "race": "Beast", "level": 26, "base_hp": 135,
        "mods": {"Strength": 4, "Dexterity": 2}, "boss": False, "super_boss": False
    },
    "beast_thunder_bird_elder": {
        "name": "Thunder Bird Elder", "race": "Beast", "level": 28, "base_hp": 145,
        "mods": {"Dexterity": 4, "Strength": 2}, "boss": False, "super_boss": False
    },
    "beast_ancient_wyrm": {
        "name": "Ancient Wyrm", "race": "Beast", "level": 30, "base_hp": 170,
        "mods": {"Strength": 5, "Constitution": 3}, "boss": False, "super_boss": False
    },
    "demon_infernal_guardian": {
        "name": "Infernal Guardian", "race": "Demon", "level": 17, "base_hp": 95,
        "mods": {"Strength": 3, "Constitution": 2}, "boss": False, "super_boss": False
    },
    "demon_gore_brute": {
        "name": "Gore Brute", "race": "Demon", "level": 20, "base_hp": 110,
        "mods": {"Strength": 4, "Dexterity": -1}, "boss": False, "super_boss": False
    },
    "demon_pit_fiend": {
        "name": "Pit Fiend", "race": "Demon", "level": 23, "base_hp": 125,
        "mods": {"Strength": 4, "Charisma": 2}, "boss": False, "super_boss": False
    },
    "construct_obsidian_colossus": {
        "name": "Obsidian Colossus", "race": "Construct", "level": 18, "base_hp": 108,
        "mods": {"Strength": 4, "Constitution": 3}, "boss": False, "super_boss": False
    },
    "construct_titanic_guardian": {
        "name": "Titanic Guardian", "race": "Construct", "level": 20, "base_hp": 125,
        "mods": {"Strength": 4, "Constitution": 3}, "boss": False, "super_boss": False
    },
    "construct_aurum_golem": {
        "name": "Aurum Golem", "race": "Construct", "level": 25, "base_hp": 145,
        "mods": {"Constitution": 4, "Strength": 2}, "boss": False, "super_boss": False
    },
    "construct_primal_guardian": {
        "name": "Primal Guardian", "race": "Construct", "level": 28, "base_hp": 165,
        "mods": {"Strength": 4, "Constitution": 4}, "boss": False, "super_boss": False
    },
    "dragonkin_flare_drake": {
        "name": "Flare Drake", "race": "Dragonkin", "level": 18, "base_hp": 102,
        "mods": {"Strength": 3, "Constitution": 2}, "boss": False, "super_boss": False
    },
    "dragonkin_ice_claw": {
        "name": "Ice Claw", "race": "Dragonkin", "level": 22, "base_hp": 125,
        "mods": {"Strength": 3, "Constitution": 2}, "boss": False, "super_boss": False
    },
    "dragonkin_storm_wing": {
        "name": "Storm Wing", "race": "Dragonkin", "level": 27, "base_hp": 148,
        "mods": {"Dexterity": 3, "Strength": 2}, "boss": False, "super_boss": False
    },
    "dragonkin_abyssal_drake": {
        "name": "Abyssal Drake", "race": "Dragonkin", "level": 32, "base_hp": 180,
        "mods": {"Strength": 4, "Constitution": 3}, "boss": False, "super_boss": False
    },
    "fey_blossom_sentry": {
        "name": "Blossom Sentry", "race": "Fey", "level": 11, "base_hp": 52,
        "mods": {"Dexterity": 2, "Charisma": 2}, "boss": False, "super_boss": False
    },
    "fey_mist_phantom": {
        "name": "Mist Phantom", "race": "Fey", "level": 16, "base_hp": 78,
        "mods": {"Dexterity": 3, "Charisma": 2}, "boss": False, "super_boss": False
    },
    "fey_dream_weaver": {
        "name": "Dream Weaver", "race": "Fey", "level": 19, "base_hp": 92,
        "mods": {"Learning": 3, "Charisma": 2}, "boss": False, "super_boss": False
    },
    "fey_verdant_queen_guard": {
        "name": "Verdant Queen Guard", "race": "Fey", "level": 22, "base_hp": 108,
        "mods": {"Strength": 2, "Constitution": 2, "Charisma": 2}, "boss": False, "super_boss": False
    },
    "elemental_plasma_sphere": {
        "name": "Plasma Sphere", "race": "Elemental", "level": 17, "base_hp": 92,
        "mods": {"Constitution": 2, "Learning": 2}, "boss": False, "super_boss": False
    },
    "elemental_azure_whirl": {
        "name": "Azure Whirl", "race": "Elemental", "level": 18, "base_hp": 98,
        "mods": {"Dexterity": 3}, "boss": False, "super_boss": False
    },
    "elemental_magma_behemoth": {
        "name": "Magma Behemoth", "race": "Elemental", "level": 19, "base_hp": 108,
        "mods": {"Constitution": 4, "Strength": 1}, "boss": False, "super_boss": False
    },
    "giant_elder_cyclops": {
        "name": "Elder Cyclops", "race": "Giant", "level": 17, "base_hp": 112,
        "mods": {"Strength": 4, "Constitution": 2}, "boss": False, "super_boss": False
    },
    "giant_crag_titan": {
        "name": "Crag Titan", "race": "Giant", "level": 19, "base_hp": 128,
        "mods": {"Strength": 5, "Constitution": 2}, "boss": False, "super_boss": False
    },
    "giant_doom_giant": {
        "name": "Doom Giant", "race": "Giant", "level": 22, "base_hp": 145,
        "mods": {"Strength": 5, "Constitution": 3}, "boss": False, "super_boss": False
    },
    "giant_thunder_titan": {
        "name": "Thunder Titan", "race": "Giant", "level": 26, "base_hp": 168,
        "mods": {"Strength": 5, "Constitution": 3}, "boss": False, "super_boss": False
    },
    "vampire_nosferatu_elder": {
        "name": "Nosferatu Elder", "race": "Vampire", "level": 17, "base_hp": 88,
        "mods": {"Dexterity": 3, "Constitution": 2}, "boss": False, "super_boss": False
    },
    "vampire_blood_duchess": {
        "name": "Blood Duchess", "race": "Vampire", "level": 20, "base_hp": 108,
        "mods": {"Charisma": 4, "Dexterity": 2}, "boss": False, "super_boss": False
    },
    "vampire_crimson_lord": {
        "name": "Crimson Lord", "race": "Vampire", "level": 23, "base_hp": 122,
        "mods": {"Strength": 3, "Charisma": 3}, "boss": False, "super_boss": False
    },
    "lizardfolk_death_gazer": {
        "name": "Death Gazer", "race": "Lizardfolk", "level": 14, "base_hp": 82,
        "mods": {"Wisdom": 2, "Constitution": 2}, "boss": False, "super_boss": False
    },
    "gnome_aether_engineer": {
        "name": "Aether Engineer", "race": "Gnome", "level": 12, "base_hp": 58,
        "mods": {"Learning": 4, "Dexterity": 1}, "boss": False, "super_boss": False
    },
    "shadow_umbral_hunter": {
        "name": "Umbral Hunter", "race": "Shadow", "level": 18, "base_hp": 86,
        "mods": {"Dexterity": 4, "Strength": 1}, "boss": False, "super_boss": False
    },
    "shadow_eclipse_bringer": {
        "name": "Eclipse Bringer", "race": "Shadow", "level": 20, "base_hp": 100,
        "mods": {"Dexterity": 4, "Charisma": 2}, "boss": False, "super_boss": False
    },
    "shadow_void_lord": {
        "name": "Void Lord", "race": "Shadow", "level": 21, "base_hp": 108,
        "mods": {"Dexterity": 5, "Wisdom": 1}, "boss": False, "super_boss": False
    },
    "clockwork_heavy_artillery": {
        "name": "Heavy Artillery", "race": "Clockwork", "level": 16, "base_hp": 90,
        "mods": {"Constitution": 2, "Strength": 2}, "boss": False, "super_boss": False
    },
    "clockwork_arcane_annihilator": {
        "name": "Arcane Annihilator", "race": "Clockwork", "level": 18, "base_hp": 105,
        "mods": {"Learning": 3, "Constitution": 2}, "boss": False, "super_boss": False
    },
    "clockwork_doom_machine": {
        "name": "Doom Machine", "race": "Clockwork", "level": 20, "base_hp": 118,
        "mods": {"Strength": 3, "Constitution": 3}, "boss": False, "super_boss": False
    },
    "clockwork_apocalypse_engine": {
        "name": "Apocalypse Engine", "race": "Clockwork", "level": 24, "base_hp": 140,
        "mods": {"Constitution": 4, "Learning": 2}, "boss": False, "super_boss": False
    },
    "abomination_hive_queen": {
        "name": "Hive Queen", "race": "Abomination", "level": 22, "base_hp": 145,
        "mods": {"Constitution": 4, "Wisdom": 2}, "boss": False, "super_boss": False
    },
    "abomination_annihilation_beast": {
        "name": "Annihilation Beast", "race": "Abomination", "level": 25, "base_hp": 168,
        "mods": {"Strength": 5, "Constitution": 4}, "boss": False, "super_boss": False
    },
    "abomination_world_eater": {
        "name": "World Eater", "race": "Abomination", "level": 28, "base_hp": 195,
        "mods": {"Strength": 6, "Constitution": 4}, "boss": False, "super_boss": False
    },
    "abomination_necro_titan": {
        "name": "Necro Titan", "race": "Abomination", "level": 31, "base_hp": 225,
        "mods": {"Strength": 5, "Constitution": 5}, "boss": False, "super_boss": False
    },
    "abomination_god_serpent": {
        "name": "God Serpent", "race": "Abomination", "level": 34, "base_hp": 250,
        "mods": {"Strength": 6, "Constitution": 5}, "boss": False, "super_boss": False
    },
    "abomination_primordial_chaos": {
        "name": "Primordial Chaos", "race": "Abomination", "level": 37, "base_hp": 290,
        "mods": {"Strength": 7, "Constitution": 6}, "boss": False, "super_boss": False
    },

    # ----- EPIC LEVEL (17–30) -----
    "arachne_weaver": {
        "name": "Arachne Weaver", "race": "Beast", "level": 19, "base_hp": 110,
        "mods": {"Dexterity": 4, "Strength": 2}, "boss": False, "super_boss": False
    }, # Monster Girl
    "abyssal_stalker": {
        "name": "Abyssal Stalker", "race": "Shadow", "level": 22, "base_hp": 118,
        "mods": {"Dexterity": 5, "Wisdom": 2}, "boss": False, "super_boss": False
    },
    "clockwork_colossus": {
        "name": "Clockwork Colossus", "race": "Clockwork", "level": 27, "base_hp": 175,
        "mods": {"Constitution": 4, "Strength": 3}, "boss": False, "super_boss": False
    },
    "draconic_vanguard": {
        "name": "Draconic Vanguard", "race": "Dragonkin", "level": 24, "base_hp": 155,
        "mods": {"Strength": 4, "Constitution": 3}, "boss": False, "super_boss": False
    },
    "neko_ninja": {
        "name": "Neko Ninja", "race": "Beast", "level": 18, "base_hp": 92,
        "mods": {"Dexterity": 5, "Strength": 1}, "boss": False, "super_boss": False
    }, # Monster Girl
    "scylla_wrecker": {
        "name": "Scylla Wrecker", "race": "Abomination", "level": 26, "base_hp": 180,
        "mods": {"Strength": 5, "Constitution": 4}, "boss": False, "super_boss": False
    }, # Monster Girl
    "succubus_seductress": {
        "name": "Succubus Seductress", "race": "Demon", "level": 21, "base_hp": 120,
        "mods": {"Charisma": 5, "Dexterity": 3}, "boss": False, "super_boss": False
    }, # Monster Girl
    "vampire_matriarch": {
        "name": "Vampire Matriarch", "race": "Vampire", "level": 25, "base_hp": 140,
        "mods": {"Dexterity": 4, "Charisma": 4, "Constitution": 2}, "boss": False, "super_boss": False
    }, # Monster Girl
    "void_walker": {
        "name": "Void Walker", "race": "Elemental", "level": 20, "base_hp": 130,
        "mods": {"Constitution": 4, "Learning": 3}, "boss": False, "super_boss": False
    },

    # ----- MYTHIC LEVEL (31–40) -----
    "cosmic_abomination": {
        "name": "Cosmic Abomination", "race": "Abomination", "level": 38, "base_hp": 270,
        "mods": {"Strength": 6, "Constitution": 5}, "boss": False, "super_boss": False
    },
    "draconic_valkyrie": {
        "name": "Draconic Valkyrie", "race": "Dragonkin", "level": 33, "base_hp": 225,
        "mods": {"Strength": 5, "Constitution": 4, "Charisma": 3}, "boss": False, "super_boss": False
    }, # Monster Girl
    "elder_titan": {
        "name": "Elder Titan", "race": "Giant", "level": 36, "base_hp": 260,
        "mods": {"Strength": 6, "Constitution": 4}, "boss": False, "super_boss": False
    },
    "lich_queen_avatar": {
        "name": "Lich Queen Avatar", "race": "Undead", "level": 35, "base_hp": 195,
        "mods": {"Learning": 6, "Charisma": 3}, "boss": False, "super_boss": False
    }, # Monster Girl
    "planar_behemoth": {
        "name": "Planar Behemoth", "race": "Abomination", "level": 32, "base_hp": 240,
        "mods": {"Strength": 5, "Constitution": 5}, "boss": False, "super_boss": False
    },
    "sphinx_riddler": {
        "name": "Sphinx Riddler", "race": "Beast", "level": 34, "base_hp": 210,
        "mods": {"Learning": 5, "Wisdom": 4, "Dexterity": 2}, "boss": False, "super_boss": False
    }, # Monster Girl

    # ===== MORE EPIC/MYTHIC ENEMIES =====
    "undead_dread_lich": {
        "name": "Dread Lich", "race": "Undead", "level": 30, "base_hp": 170,
        "mods": {"Learning": 5, "Constitution": 2}, "boss": False, "super_boss": False
    },
    "undead_soul_reaper": {
        "name": "Soul Reaper", "race": "Undead", "level": 33, "base_hp": 185,
        "mods": {"Dexterity": 4, "Strength": 2}, "boss": False, "super_boss": False
    },
    "undead_eternal_emperor": {
        "name": "Eternal Emperor", "race": "Undead", "level": 38, "base_hp": 230,
        "mods": {"Strength": 4, "Constitution": 4, "Learning": 3}, "boss": False, "super_boss": False
    },
    "beast_sky_leviathan": {
        "name": "Sky Leviathan", "race": "Beast", "level": 32, "base_hp": 200,
        "mods": {"Strength": 5, "Constitution": 4}, "boss": False, "super_boss": False
    },
    "beast_earth_breaker": {
        "name": "Earth Breaker", "race": "Beast", "level": 36, "base_hp": 240,
        "mods": {"Strength": 6, "Constitution": 4}, "boss": False, "super_boss": False
    },
    "demon_arch_devil": {
        "name": "Arch Devil", "race": "Demon", "level": 28, "base_hp": 160,
        "mods": {"Strength": 5, "Charisma": 4}, "boss": False, "super_boss": False
    },
    "demon_lord_of_ruin": {
        "name": "Lord of Ruin", "race": "Demon", "level": 30, "base_hp": 185,
        "mods": {"Strength": 5, "Constitution": 3}, "boss": False, "super_boss": False
    },
    "construct_primordial_golem": {
        "name": "Primordial Golem", "race": "Construct", "level": 32, "base_hp": 210,
        "mods": {"Strength": 5, "Constitution": 5}, "boss": False, "super_boss": False
    },
    "construct_celestial_automaton": {
        "name": "Celestial Automaton", "race": "Construct", "level": 36, "base_hp": 250,
        "mods": {"Constitution": 5, "Learning": 3}, "boss": False, "super_boss": False
    },
    "dragonkin_elder_wyrm": {
        "name": "Elder Wyrm", "race": "Dragonkin", "level": 30, "base_hp": 185,
        "mods": {"Strength": 5, "Constitution": 3}, "boss": False, "super_boss": False
    },
    "dragonkin_time_drake": {
        "name": "Time Drake", "race": "Dragonkin", "level": 35, "base_hp": 240,
        "mods": {"Learning": 4, "Constitution": 3}, "boss": False, "super_boss": False
    },
    "giant_supreme_titan": {
        "name": "Supreme Titan", "race": "Giant", "level": 32, "base_hp": 240,
        "mods": {"Strength": 6, "Constitution": 4}, "boss": False, "super_boss": False
    },
    "giant_world_carrier": {
        "name": "World Carrier", "race": "Giant", "level": 38, "base_hp": 310,
        "mods": {"Strength": 7, "Constitution": 5}, "boss": False, "super_boss": False
    },
    "shadow_abyss_lord": {
        "name": "Abyss Lord", "race": "Shadow", "level": 24, "base_hp": 125,
        "mods": {"Dexterity": 5, "Charisma": 2}, "boss": False, "super_boss": False
    },
    "shadow_void_spectre": {
        "name": "Void Spectre", "race": "Shadow", "level": 26, "base_hp": 135,
        "mods": {"Dexterity": 5, "Wisdom": 1}, "boss": False, "super_boss": False
    },
    "clockwork_epoch_engine": {
        "name": "Epoch Engine", "race": "Clockwork", "level": 30, "base_hp": 185,
        "mods": {"Learning": 4, "Constitution": 3}, "boss": False, "super_boss": False
    },
    "clockwork_genesis_device": {
        "name": "Genesis Device", "race": "Clockwork", "level": 34, "base_hp": 220,
        "mods": {"Constitution": 5, "Learning": 4}, "boss": False, "super_boss": False
    },
    "abomination_doom_of_elders": {
        "name": "Doom of Elders", "race": "Abomination", "level": 40, "base_hp": 320,
        "mods": {"Strength": 7, "Constitution": 6}, "boss": False, "super_boss": False
    },

    # ----- BOSSES (non‑superboss) -----
    "abomination_overlord": {
        "name": "Abomination Overlord", "race": "Abomination", "level": 18, "base_hp": 160,
        "mods": {"Strength": 6, "Constitution": 5, "Wisdom": -2}, "boss": True, "super_boss": False
    },
    "abomination_rotting_god": {
        "name": "Abomination Rotting God", "race": "Abomination", "level": 14, "base_hp": 110,
        "mods": {"Strength": 5, "Constitution": 3}, "boss": True, "super_boss": False
    },
    "abyssal_abomination": {
        "name": "Abyssal Abomination", "race": "Abomination", "level": 20, "base_hp": 180,
        "mods": {"Strength": 7, "Constitution": 6}, "boss": True, "super_boss": False
    },
    "ancient_chronos_golem": {
        "name": "Ancient Chronos Golem", "race": "Construct", "level": 35, "base_hp": 410,
        "mods": {"Strength": 5, "Constitution": 6, "Learning": 3}, "boss": True, "super_boss": False
    },
    "ancient_dragonkin": {
        "name": "Ancient Dragonkin", "race": "Dragonkin", "level": 14, "base_hp": 105,
        "mods": {"Strength": 4, "Constitution": 3}, "boss": True, "super_boss": False
    },
    "ancient_golem": {
        "name": "Ancient Golem", "race": "Construct", "level": 12, "base_hp": 88,
        "mods": {"Strength": 2}, "boss": True, "super_boss": False
    },
    "apocalypse_bringer": {
        "name": "Apocalypse Bringer", "race": "Abomination", "level": 40, "base_hp": 520,
        "mods": {"Strength": 8, "Constitution": 7}, "boss": True, "super_boss": False
    },
    "arch_lich": {
        "name": "Arch Lich", "race": "Undead", "level": 17, "base_hp": 125,
        "mods": {"Learning": 6, "Constitution": 2}, "boss": True, "super_boss": False
    },
    "balor_demon": {
        "name": "Balor Demon", "race": "Demon", "level": 18, "base_hp": 140,
        "mods": {"Strength": 5, "Charisma": 4}, "boss": True, "super_boss": False
    },
    "clockwork_overlord": {
        "name": "Clockwork Overlord", "race": "Clockwork", "level": 11, "base_hp": 70,
        "mods": {"Constitution": 3, "Learning": 2}, "boss": True, "super_boss": False
    },
    "clockwork_titan": {
        "name": "Clockwork Titan", "race": "Clockwork", "level": 14, "base_hp": 110,
        "mods": {"Strength": 4, "Constitution": 4}, "boss": True, "super_boss": False
    },
    "demon_imp": {
        "name": "Demon Imp", "race": "Demon", "level": 6, "base_hp": 28,
        "mods": {"Learning": 1}, "boss": True, "super_boss": False
    },
    "demon_knight": {
        "name": "Demon Knight", "race": "Demon", "level": 10, "base_hp": 68,
        "mods": {"Strength": 3}, "boss": True, "super_boss": False
    },
    "demon_lord": {
        "name": "Demon Lord", "race": "Demon", "level": 15, "base_hp": 115,
        "mods": {"Strength": 4, "Charisma": 3}, "boss": True, "super_boss": False
    },
    "dragon_goddess_avatar": {
        "name": "Dragon Goddess Avatar", "race": "Dragonkin", "level": 37, "base_hp": 440,
        "mods": {"Strength": 6, "Constitution": 5, "Charisma": 5}, "boss": True, "super_boss": False
    }, # Monster Girl
    "dragonkin_ancient_wyrm": {
        "name": "Dragonkin Ancient Wyrm", "race": "Dragonkin", "level": 13, "base_hp": 95,
        "mods": {"Strength": 4, "Constitution": 2}, "boss": True, "super_boss": False
    },
    "dragonkin_overlord": {
        "name": "Dragonkin Overlord", "race": "Dragonkin", "level": 19, "base_hp": 165,
        "mods": {"Strength": 6, "Constitution": 4}, "boss": True, "super_boss": False
    },
    "elemental_cataclysm": {
        "name": "Elemental Cataclysm", "race": "Elemental", "level": 15, "base_hp": 100,
        "mods": {"Constitution": 4, "Learning": 3}, "boss": True, "super_boss": False
    },
    "eternal_shadow": {
        "name": "Eternal Shadow", "race": "Shadow", "level": 16, "base_hp": 95,
        "mods": {"Dexterity": 6, "Charisma": 3}, "boss": True, "super_boss": False
    },
    "fey_lord": {
        "name": "Fey Lord", "race": "Fey", "level": 13, "base_hp": 82,
        "mods": {"Dexterity": 4, "Charisma": 3}, "boss": True, "super_boss": False
    },
    "fey_trickster_lord": {
        "name": "Fey Trickster Lord", "race": "Fey", "level": 8, "base_hp": 48,
        "mods": {"Dexterity": 3, "Charisma": 3}, "boss": True, "super_boss": False
    },
    "forest_spirit": {
        "name": "Forest Spirit", "race": "Fey", "level": 5, "base_hp": 22,
        "mods": {"Dexterity": 2, "Charisma": 1}, "boss": True, "super_boss": False
    },
    "gnome_high_artificer": {
        "name": "Gnome High Artificer", "race": "Gnome", "level": 12, "base_hp": 68,
        "mods": {"Learning": 5, "Dexterity": 2}, "boss": True, "super_boss": False
    },
    "greater_abomination": {
        "name": "Greater Abomination", "race": "Abomination", "level": 11, "base_hp": 85,
        "mods": {"Strength": 4, "Constitution": 3}, "boss": True, "super_boss": False
    },
    "infernal_commander": {
        "name": "Infernal Commander", "race": "Demon", "level": 9, "base_hp": 60,
        "mods": {"Strength": 2, "Charisma": 2}, "boss": True, "super_boss": False
    },
    "infernal_empress": {
        "name": "Infernal Empress", "race": "Demon", "level": 26, "base_hp": 290,
        "mods": {"Strength": 5, "Charisma": 6, "Dexterity": 3}, "boss": True, "super_boss": False
    }, # Monster Girl
    "lich": {
        "name": "Lich", "race": "Undead", "level": 11, "base_hp": 58,
        "mods": {"Learning": 4}, "boss": True, "super_boss": False
    },
    "lizardfolk_king": {
        "name": "Lizardfolk King", "race": "Lizardfolk", "level": 13, "base_hp": 95,
        "mods": {"Strength": 3, "Constitution": 3}, "boss": True, "super_boss": False
    },
    "mountain_giant": {
        "name": "Mountain Giant", "race": "Giant", "level": 13, "base_hp": 135,
        "mods": {"Strength": 5}, "boss": True, "super_boss": False
    },
    "mountain_troll": {
        "name": "Mountain Troll", "race": "Giant", "level": 5, "base_hp": 38,
        "mods": {"Strength": 2, "Constitution": 2}, "boss": True, "super_boss": False
    },
    "omega_clockwork_god": {
        "name": "Omega Clockwork God", "race": "Clockwork", "level": 39, "base_hp": 490,
        "mods": {"Strength": 6, "Constitution": 7, "Learning": 5}, "boss": True, "super_boss": False
    },
    "primordial_elemental": {
        "name": "Primordial Elemental", "race": "Elemental", "level": 17, "base_hp": 130,
        "mods": {"Constitution": 5, "Learning": 4}, "boss": True, "super_boss": False
    },
    "shadow_dragon": {
        "name": "Shadow Dragon", "race": "Shadow", "level": 16, "base_hp": 100,
        "mods": {"Dexterity": 5, "Charisma": 2}, "boss": True, "super_boss": False
    },
    "shadow_phantom_king": {
        "name": "Shadow Phantom King", "race": "Shadow", "level": 12, "base_hp": 65,
        "mods": {"Dexterity": 4, "Charisma": 2}, "boss": True, "super_boss": False
    },
    "siren_empress": {
        "name": "Siren Empress", "race": "Fey", "level": 23, "base_hp": 220,
        "mods": {"Charisma": 6, "Dexterity": 4}, "boss": True, "super_boss": False
    }, # Monster Girl
    "storm_elemental": {
        "name": "Storm Elemental", "race": "Elemental", "level": 12, "base_hp": 95,
        "mods": {"Learning": 3, "Constitution": 2}, "boss": True, "super_boss": False
    },
    "tide_caller": {
        "name": "Tide Caller", "race": "Elemental", "level": 5, "base_hp": 26,
        "mods": {"Constitution": 2, "Learning": 1}, "boss": True, "super_boss": False
    },
    "titanic_golem": {
        "name": "Titanic Golem", "race": "Construct", "level": 16, "base_hp": 155,
        "mods": {"Strength": 5, "Constitution": 4}, "boss": True, "super_boss": False
    },
    "undead_dread_emperor": {
        "name": "Undead Dread Emperor", "race": "Undead", "level": 31, "base_hp": 340,
        "mods": {"Strength": 4, "Constitution": 5, "Learning": 4}, "boss": True, "super_boss": False
    },
    "undead_war_behemoth": {
        "name": "Undead War Behemoth", "race": "Undead", "level": 10, "base_hp": 75,
        "mods": {"Strength": 3, "Constitution": 2}, "boss": True, "super_boss": False
    },
    "vampire_lord": {
        "name": "Vampire Lord", "race": "Vampire", "level": 15, "base_hp": 102,
        "mods": {"Dexterity": 4, "Charisma": 3}, "boss": True, "super_boss": False
    },

    # ===== NEW BOSSES =====
    "beast_alpha_thunder_bird": {
        "name": "Alpha Thunder Bird", "race": "Beast", "level": 15, "base_hp": 110,
        "mods": {"Strength": 4, "Dexterity": 3}, "boss": True, "super_boss": False
    },
    "demon_overlord_of_legions": {
        "name": "Overlord of Legions", "race": "Demon", "level": 25, "base_hp": 210,
        "mods": {"Strength": 5, "Charisma": 4}, "boss": True, "super_boss": False
    },
    "giant_king_of_the_peaks": {
        "name": "King of the Peaks", "race": "Giant", "level": 22, "base_hp": 210,
        "mods": {"Strength": 6, "Constitution": 4}, "boss": True, "super_boss": False
    },
    "construct_eternal_warden": {
        "name": "Eternal Warden", "race": "Construct", "level": 20, "base_hp": 170,
        "mods": {"Constitution": 5, "Strength": 3}, "boss": True, "super_boss": False
    },
    "fey_winter_queen": {
        "name": "Winter Queen", "race": "Fey", "level": 18, "base_hp": 130,
        "mods": {"Charisma": 5, "Dexterity": 3}, "boss": True, "super_boss": False
    },
    "vampire_nocturnal_king": {
        "name": "Nocturnal King", "race": "Vampire", "level": 20, "base_hp": 145,
        "mods": {"Dexterity": 4, "Charisma": 4}, "boss": True, "super_boss": False
    },
    "shadow_umbral_emperor": {
        "name": "Umbral Emperor", "race": "Shadow", "level": 18, "base_hp": 120,
        "mods": {"Dexterity": 5, "Charisma": 3}, "boss": True, "super_boss": False
    },
    "lizardfolk_god_king": {
        "name": "Lizardfolk God King", "race": "Lizardfolk", "level": 16, "base_hp": 130,
        "mods": {"Strength": 4, "Constitution": 3, "Learning": 2}, "boss": True, "super_boss": False
    },
    "orc_blood_chieftain": {
        "name": "Blood Chieftain", "race": "Orc", "level": 14, "base_hp": 100,
        "mods": {"Strength": 4, "Constitution": 2}, "boss": True, "super_boss": False
    },

    # ----- EXPANDED ROSTER (50 NEW ENEMIES) -----
    "bandit_bruiser": {
        "name": "Bandit Bruiser", "race": "Human", "level": 4, "base_hp": 30,
        "mods": {"Strength": 2}, "boss": False, "super_boss": False
    },
    "veteran_swordsman": {
        "name": "Veteran Swordsman", "race": "Human", "level": 7, "base_hp": 55,
        "mods": {"Strength": 2, "Dexterity": 1}, "boss": False, "super_boss": False
    },
    "rogue_assassin": {
        "name": "Rogue Assassin", "race": "Human", "level": 9, "base_hp": 60,
        "mods": {"Dexterity": 3}, "boss": False, "super_boss": False
    },

    # -- Orc (Level 4-13) --
    "orc_hunter": {
        "name": "Orc Hunter", "race": "Orc", "level": 6, "base_hp": 40,
        "mods": {"Dexterity": 2}, "boss": False, "super_boss": False
    },
    "orc_blood_shaman": {
        "name": "Orc Blood Shaman", "race": "Orc", "level": 11, "base_hp": 75,
        "mods": {"Wisdom": 3}, "boss": False, "super_boss": False
    },
    "orc_gladiator": {
        "name": "Orc Gladiator", "race": "Orc", "level": 12, "base_hp": 85,
        "mods": {"Strength": 4}, "boss": False, "super_boss": False
    },

    # -- Gnome (Level 1-12) --
    "gnome_saboteur": {
        "name": "Gnome Saboteur", "race": "Gnome", "level": 4, "base_hp": 25,
        "mods": {"Dexterity": 2, "Learning": 1}, "boss": False, "super_boss": False
    },
    "gnome_alchemist": {
        "name": "Gnome Alchemist", "race": "Gnome", "level": 7, "base_hp": 40,
        "mods": {"Learning": 3}, "boss": False, "super_boss": False
    },
    "gnome_mecha_pilot": {
        "name": "Gnome Mecha Pilot", "race": "Gnome", "level": 12, "base_hp": 75,
        "mods": {"Learning": 2, "Constitution": 2}, "boss": False, "super_boss": False
    },

    # -- Lizardfolk (Level 2-15) --
    "lizardfolk_shaman": {
        "name": "Lizardfolk Shaman", "race": "Lizardfolk", "level": 6, "base_hp": 42,
        "mods": {"Wisdom": 2}, "boss": False, "super_boss": False
    },
    "lizardfolk_gladiator": {
        "name": "Lizardfolk Gladiator", "race": "Lizardfolk", "level": 12, "base_hp": 88,
        "mods": {"Strength": 3, "Constitution": 2}, "boss": False, "super_boss": False
    },
    "lizard_queen": {
        "name": "Lizard Queen", "race": "Lizardfolk", "level": 14, "base_hp": 130,
        "mods": {"Charisma": 3, "Constitution": 3}, "boss": True, "super_boss": False
    }, # Monster Girl

    # -- Fey (Level 2-23) --
    "dryad_protector": {
        "name": "Dryad Protector", "race": "Fey", "level": 9, "base_hp": 50,
        "mods": {"Charisma": 2, "Wisdom": 2}, "boss": False, "super_boss": False
    }, # Monster Girl
    "winter_fairy": {
        "name": "Winter Fairy", "race": "Fey", "level": 14, "base_hp": 70,
        "mods": {"Dexterity": 3, "Charisma": 2}, "boss": False, "super_boss": False
    }, # Monster Girl
    "fey_wild_stalker": {
        "name": "Fey Wild Stalker", "race": "Fey", "level": 19, "base_hp": 105,
        "mods": {"Dexterity": 4}, "boss": False, "super_boss": False
    },
    "summer_court_knight": {
        "name": "Summer Court Knight", "race": "Fey", "level": 22, "base_hp": 140,
        "mods": {"Strength": 3, "Charisma": 3}, "boss": False, "super_boss": False
    },

    # -- Elemental (Level 2-20) --
    "wind_elemental": {
        "name": "Wind Elemental", "race": "Elemental", "level": 7, "base_hp": 55,
        "mods": {"Dexterity": 3}, "boss": False, "super_boss": False
    },
    "earth_elemental": {
        "name": "Earth Elemental", "race": "Elemental", "level": 8, "base_hp": 75,
        "mods": {"Constitution": 4}, "boss": False, "super_boss": False
    },
    "crystal_golem_elemental": {
        "name": "Crystal Golem", "race": "Elemental", "level": 14, "base_hp": 110,
        "mods": {"Constitution": 4}, "boss": False, "super_boss": False
    },
    "plasma_elemental": {
        "name": "Plasma Elemental", "race": "Elemental", "level": 18, "base_hp": 120,
        "mods": {"Constitution": 3, "Dexterity": 3}, "boss": False, "super_boss": False
    },

    # -- Shadow (Level 3-22) --
    "shadow_fiend": {
        "name": "Shadow Fiend", "race": "Shadow", "level": 5, "base_hp": 30,
        "mods": {"Dexterity": 3}, "boss": False, "super_boss": False
    },
    "umbral_weaver": {
        "name": "Umbral Weaver", "race": "Shadow", "level": 14, "base_hp": 85,
        "mods": {"Dexterity": 3, "Wisdom": 2}, "boss": False, "super_boss": False
    }, # Monster Girl
    "eclipse_knight": {
        "name": "Eclipse Knight", "race": "Shadow", "level": 19, "base_hp": 130,
        "mods": {"Dexterity": 4, "Strength": 2}, "boss": False, "super_boss": False
    },
    "darkness_incarnate": {
        "name": "Darkness Incarnate", "race": "Shadow", "level": 22, "base_hp": 210,
        "mods": {"Dexterity": 6, "Charisma": 4}, "boss": True, "super_boss": False
    },

    # -- Demon (Level 1-26) --
    "incubus_infiltrator": {
        "name": "Incubus Infiltrator", "race": "Demon", "level": 14, "base_hp": 90,
        "mods": {"Charisma": 4, "Dexterity": 2}, "boss": False, "super_boss": False
    },
    "chaos_fiend": {
        "name": "Chaos Fiend", "race": "Demon", "level": 19, "base_hp": 140,
        "mods": {"Strength": 4, "Dexterity": 3}, "boss": False, "super_boss": False
    },
    "demon_whip_master": {
        "name": "Demon Whip Master", "race": "Demon", "level": 24, "base_hp": 170,
        "mods": {"Dexterity": 5, "Charisma": 3}, "boss": False, "super_boss": False
    }, # Monster Girl
    "abyssal_juggernaut": {
        "name": "Abyssal Juggernaut", "race": "Demon", "level": 25, "base_hp": 210,
        "mods": {"Strength": 6, "Constitution": 5}, "boss": False, "super_boss": False
    },

    # -- Vampire (Level 8-25) --
    "vampire_fledgling": {
        "name": "Vampire Fledgling", "race": "Vampire", "level": 8, "base_hp": 50,
        "mods": {"Dexterity": 2, "Charisma": 1}, "boss": False, "super_boss": False
    },
    "vampire_seductress": {
        "name": "Vampire Seductress", "race": "Vampire", "level": 16, "base_hp": 100,
        "mods": {"Charisma": 5, "Dexterity": 3}, "boss": False, "super_boss": False
    }, # Monster Girl
    "nosferatu_stalker": {
        "name": "Nosferatu Stalker", "race": "Vampire", "level": 20, "base_hp": 135,
        "mods": {"Dexterity": 5, "Strength": 2}, "boss": False, "super_boss": False
    },
    "crimson_countess": {
        "name": "Crimson Countess", "race": "Vampire", "level": 24, "base_hp": 230,
        "mods": {"Charisma": 6, "Dexterity": 4}, "boss": True, "super_boss": False
    }, # Monster Girl

    # -- Beast (Level 1-34) --
    "mutated_bear": {
        "name": "Mutated Bear", "race": "Beast", "level": 15, "base_hp": 115,
        "mods": {"Strength": 4, "Constitution": 3}, "boss": False, "super_boss": False
    },
    "minotaur_warrior": {
        "name": "Minotaur Warrior", "race": "Beast", "level": 18, "base_hp": 145,
        "mods": {"Strength": 5}, "boss": False, "super_boss": False
    },
    "chimera_alpha": {
        "name": "Chimera Alpha", "race": "Beast", "level": 24, "base_hp": 190,
        "mods": {"Strength": 4, "Dexterity": 4}, "boss": False, "super_boss": False
    },
    "ninetales_fox": {
        "name": "Ninetales Fox", "race": "Beast", "level": 30, "base_hp": 220,
        "mods": {"Charisma": 6, "Wisdom": 5}, "boss": False, "super_boss": False
    }, # Monster Girl

    # -- Undead (Level 2-35) --
    "skeletal_mage": {
        "name": "Skeletal Mage", "race": "Undead", "level": 9, "base_hp": 50,
        "mods": {"Learning": 3}, "boss": False, "super_boss": False
    },
    "banshee_wailer": {
        "name": "Banshee Wailer", "race": "Undead", "level": 18, "base_hp": 110,
        "mods": {"Charisma": 4, "Dexterity": 2}, "boss": False, "super_boss": False
    }, # Monster Girl
    "bone_dragon": {
        "name": "Bone Dragon", "race": "Undead", "level": 28, "base_hp": 230,
        "mods": {"Strength": 5, "Constitution": 4}, "boss": False, "super_boss": False
    },
    "death_bringer": {
        "name": "Death Bringer", "race": "Undead", "level": 34, "base_hp": 360,
        "mods": {"Strength": 6, "Constitution": 6}, "boss": True, "super_boss": False
    },

    # -- Giant (Level 4-36) --
    "frost_giant": {
        "name": "Frost Giant", "race": "Giant", "level": 19, "base_hp": 170,
        "mods": {"Strength": 5, "Constitution": 3}, "boss": False, "super_boss": False
    },
    "fire_giant_forge_master": {
        "name": "Fire Giant Forge Master", "race": "Giant", "level": 28, "base_hp": 240,
        "mods": {"Strength": 6, "Constitution": 5}, "boss": False, "super_boss": False
    },
    "ancient_cyclops": {
        "name": "Ancient Cyclops", "race": "Giant", "level": 35, "base_hp": 310,
        "mods": {"Strength": 7, "Constitution": 5}, "boss": False, "super_boss": False
    },

    # -- Dragonkin (Level 7-37) --
    "wyvern_rider": {
        "name": "Wyvern Rider", "race": "Dragonkin", "level": 16, "base_hp": 130,
        "mods": {"Dexterity": 3, "Strength": 3}, "boss": False, "super_boss": False
    },
    "dragon_knight_commander": {
        "name": "Dragon Knight Commander", "race": "Dragonkin", "level": 28, "base_hp": 240,
        "mods": {"Strength": 5, "Charisma": 4}, "boss": False, "super_boss": False
    },

    # -- Clockwork (Level 4-39) --
    "clockwork_dragon": {
        "name": "Clockwork Dragon", "race": "Clockwork", "level": 32, "base_hp": 290,
        "mods": {"Constitution": 6, "Strength": 5}, "boss": False, "super_boss": False
    },

    # -- Abomination (Level 6-40) --
    "flesh_amalgam": {
        "name": "Flesh Amalgam", "race": "Abomination", "level": 25, "base_hp": 220,
        "mods": {"Constitution": 6, "Strength": 4}, "boss": False, "super_boss": False
    },

    # ----- SUPER BOSSES (floor 10, 20, etc.) -----
    "broodmother_vileheart": {
        "name": "Broodmother Vileheart", "race": "Beast", "level": 20, "base_hp": 350,
        "mods": {"Strength": 6, "Constitution": 6, "Dexterity": 4},
        "boss": True, "super_boss": True
    },
    "dream_devouring_slitcurrent": {
        "name": "Dream-Devouring Slitcurrent", "race": "Abomination", "level": 21, "base_hp": 420,
        "mods": {"Strength": 5, "Constitution": 7, "Dexterity": 6},
        "boss": True, "super_boss": True
    },
    "melt_forge_golem_ignis": {
        "name": "Ignis, the Melt-Forge Golem", "race": "Construct", "level": 21, "base_hp": 400,
        "mods": {"Strength": 6, "Constitution": 8, "Dexterity": 1},
        "boss": True, "super_boss": True
    },
    "queen_of_mirrors_sylvana": {
        "name": "Queen of Mirrors Sylvana", "race": "Fey", "level": 21, "base_hp": 380,
        "mods": {"Dexterity": 7, "Charisma": 5, "Constitution": 3, "Strength": 2},
        "boss": True, "super_boss": True
    },

    # ----- SUPERBOSS MINIONS (never spawn alone) -----
    "dream_floatsam": {
        "name": "Dream Floatsam", "race": "Construct", "level": 16, "base_hp": 55,
        "mods": {"Dexterity": 4, "Constitution": 2}, "boss": False, "super_boss": False
    },
    "sylvana_mirror_copy": {
        "name": "Sylvana Mirror Copy", "race": "Fey", "level": 21, "base_hp": 1,
        "mods": {"Dexterity": 7, "Charisma": 5, "Constitution": 3, "Strength": 2},
        "boss": False, "super_boss": False
    },
    "vileheart_spiderling": {
        "name": "Vileheart Spiderling", "race": "Beast", "level": 15, "base_hp": 45,
        "mods": {"Dexterity": 5, "Strength": 2}, "boss": False, "super_boss": False
    },
}