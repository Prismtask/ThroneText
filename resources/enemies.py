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

ENEMIES = {
    # Low level (1–3)
    "goblin_scout": {"name": "Goblin Scout", "race": "Goblin", "level": 1, "base_hp": 13, "mods": {"Dexterity": 1}, "boss": False},
    "goblin_knifer": {"name": "Goblin Knifer", "race": "Goblin", "level": 2, "base_hp": 17, "mods": {"Dexterity": 2}, "boss": False},
    "wild_dog": {"name": "Wild Dog", "race": "Beast", "level": 1, "base_hp": 14, "mods": {}, "boss": False},
    "skeleton": {"name": "Skeleton", "race": "Undead", "level": 2, "base_hp": 18, "mods": {}, "boss": False},
    "bandit": {"name": "Bandit", "race": "Human", "level": 2, "base_hp": 19, "mods": {"Dexterity": 1}, "boss": False},
    "imp": {"name": "Imp", "race": "Demon", "level": 1, "base_hp": 12, "mods": {"Dexterity": 2}, "boss": False},
    "pixie_trickster": {"name": "Pixie Trickster", "race": "Fey", "level": 2, "base_hp": 13, "mods": {"Dexterity": 3}, "boss": False},
    "lizardfolk_hunter": {"name": "Lizardfolk Hunter", "race": "Lizardfolk", "level": 2, "base_hp": 18, "mods": {"Dexterity": 1}, "boss": False},
    "gnome_tinker": {"name": "Gnome Tinker", "race": "Gnome", "level": 1, "base_hp": 11, "mods": {"Learning": 1}, "boss": False},
    "shadow_stalker": {"name": "Shadow Stalker", "race": "Shadow", "level": 3, "base_hp": 16, "mods": {"Dexterity": 2}, "boss": False},
    "cave_rat": {"name": "Cave Rat", "race": "Beast", "level": 1, "base_hp": 10, "mods": {}, "boss": False},
    "rotten_carcass": {"name": "Rotten Carcass", "race": "Undead", "level": 3, "base_hp": 25, "mods": {"Constitution": 2}, "boss": False},

    # Added more low-level variety
    "goblin_archer": {"name": "Goblin Archer", "race": "Goblin", "level": 2, "base_hp": 15, "mods": {"Dexterity": 3}, "boss": False},
    "forest_spider": {"name": "Forest Spider", "race": "Beast", "level": 1, "base_hp": 12, "mods": {"Dexterity": 2}, "boss": False},
    "zombie_minion": {"name": "Zombie Minion", "race": "Undead", "level": 3, "base_hp": 22, "mods": {"Constitution": 1}, "boss": False},
    "thief": {"name": "Thief", "race": "Human", "level": 2, "base_hp": 16, "mods": {"Dexterity": 2}, "boss": False},
    "lesser_imp": {"name": "Lesser Imp", "race": "Demon", "level": 1, "base_hp": 11, "mods": {"Charisma": 1}, "boss": False},
    "fey_sprite": {"name": "Fey Sprite", "race": "Fey", "level": 3, "base_hp": 14, "mods": {"Dexterity": 2, "Charisma": 1}, "boss": False},

    # Mid level (4–6)
    "orc_grunt": {"name": "Orc Grunt", "race": "Orc", "level": 4, "base_hp": 28, "mods": {"Strength": 1}, "boss": False},
    "orc_brute": {"name": "Orc Brute", "race": "Orc", "level": 5, "base_hp": 34, "mods": {"Strength": 2}, "boss": False},
    "dire_wolf": {"name": "Dire Wolf", "race": "Beast", "level": 4, "base_hp": 32, "mods": {"Dexterity": 1}, "boss": False},
    "zombie": {"name": "Zombie", "race": "Undead", "level": 4, "base_hp": 33, "mods": {"Strength": 1}, "boss": False},
    "cultist": {"name": "Cultist", "race": "Human", "level": 5, "base_hp": 26, "mods": {"Learning": 1}, "boss": False},
    "fire_elemental": {"name": "Fire Elemental", "race": "Elemental", "level": 5, "base_hp": 37, "mods": {"Constitution": 2}, "boss": False},
    "gnoll_marauder": {"name": "Gnoll Marauder", "race": "Beast", "level": 4, "base_hp": 30, "mods": {"Strength": 2}, "boss": False},
    "spectral_knight": {"name": "Spectral Knight", "race": "Undead", "level": 6, "base_hp": 40, "mods": {"Dexterity": 1}, "boss": False},
    "lizardfolk_warrior": {"name": "Lizardfolk Warrior", "race": "Lizardfolk", "level": 5, "base_hp": 35, "mods": {"Strength": 2}, "boss": False},
    "clockwork_sentinel": {"name": "Clockwork Sentinel", "race": "Clockwork", "level": 4, "base_hp": 29, "mods": {"Strength": 1}, "boss": False},
    "shadow_assassin": {"name": "Shadow Assassin", "race": "Shadow", "level": 6, "base_hp": 33, "mods": {"Dexterity": 3}, "boss": False},
    "gnome_illusionist": {"name": "Gnome Illusionist", "race": "Gnome", "level": 5, "base_hp": 24, "mods": {"Learning": 2, "Charisma": 1}, "boss": False},
    "lesser_abomination": {"name": "Lesser Abomination", "race": "Abomination", "level": 6, "base_hp": 48, "mods": {"Strength": 2}, "boss": False},
    "battle_hound": {"name": "Battle Hound", "race": "Beast", "level": 5, "base_hp": 31, "mods": {"Dexterity": 2, "Strength": 1}, "boss": False},

    # Added more mid-level variety
    "orc_shaman": {"name": "Orc Shaman", "race": "Orc", "level": 5, "base_hp": 27, "mods": {"Learning": 2, "Wisdom": 1}, "boss": False},
    "venom_wolf": {"name": "Venom Wolf", "race": "Beast", "level": 4, "base_hp": 29, "mods": {"Dexterity": 2}, "boss": False},
    "ghoul": {"name": "Ghoul", "race": "Undead", "level": 6, "base_hp": 38, "mods": {"Strength": 2}, "boss": False},
    "mercenary": {"name": "Mercenary", "race": "Human", "level": 5, "base_hp": 32, "mods": {"Strength": 1, "Constitution": 1}, "boss": False},
    "ice_elemental": {"name": "Ice Elemental", "race": "Elemental", "level": 5, "base_hp": 35, "mods": {"Constitution": 3}, "boss": False},
    "lizardfolk_spearman": {"name": "Lizardfolk Spearman", "race": "Lizardfolk", "level": 4, "base_hp": 31, "mods": {"Dexterity": 1}, "boss": False},
    "clockwork_spy": {"name": "Clockwork Spy", "race": "Clockwork", "level": 6, "base_hp": 30, "mods": {"Dexterity": 2}, "boss": False},
    "shadow_wraithling": {"name": "Shadow Wraithling", "race": "Shadow", "level": 6, "base_hp": 28, "mods": {"Dexterity": 2}, "boss": False},

    # High level (7–9)
    "orc_warlord": {"name": "Orc Warlord", "race": "Orc", "level": 7, "base_hp": 48, "mods": {"Strength": 3, "Charisma": 1}, "boss": False},
    "wraith": {"name": "Wraith", "race": "Undead", "level": 7, "base_hp": 38, "mods": {"Dexterity": 2}, "boss": False},
    "hellhound": {"name": "Hellhound", "race": "Demon", "level": 6, "base_hp": 42, "mods": {"Dexterity": 1}, "boss": False},
    "stone_golem": {"name": "Stone Golem", "race": "Construct", "level": 8, "base_hp": 62, "mods": {}, "boss": False},
    "dark_knight": {"name": "Dark Knight", "race": "Human", "level": 8, "base_hp": 52, "mods": {"Strength": 2, "Constitution": 2}, "boss": False},
    "young_dragonkin": {"name": "Young Dragonkin", "race": "Dragonkin", "level": 7, "base_hp": 50, "mods": {"Strength": 3}, "boss": False},
    "vampire_spawn": {"name": "Vampire Spawn", "race": "Vampire", "level": 8, "base_hp": 45, "mods": {"Dexterity": 3}, "boss": False},
    "troll_regenerator": {"name": "Troll Regenerator", "race": "Giant", "level": 7, "base_hp": 68, "mods": {"Constitution": 3}, "boss": False},
    "lizardfolk_high_priest": {"name": "Lizardfolk High Priest", "race": "Lizardfolk", "level": 8, "base_hp": 44, "mods": {"Learning": 2, "Wisdom": 1}, "boss": False},
    "clockwork_guardian": {"name": "Clockwork Guardian", "race": "Clockwork", "level": 9, "base_hp": 58, "mods": {"Constitution": 2}, "boss": False},
    "shadow_lord": {"name": "Shadow Lord", "race": "Shadow", "level": 9, "base_hp": 47, "mods": {"Dexterity": 3, "Charisma": 1}, "boss": False},
    "gnome_skycaptain": {"name": "Gnome Skycaptain", "race": "Gnome", "level": 8, "base_hp": 39, "mods": {"Learning": 3, "Dexterity": 2}, "boss": False},
    "abomination_brute": {"name": "Abomination Brute", "race": "Abomination", "level": 9, "base_hp": 72, "mods": {"Strength": 3, "Constitution": 2}, "boss": False},
    "flame_salamander": {"name": "Flame Salamander", "race": "Elemental", "level": 8, "base_hp": 56, "mods": {"Dexterity": 2}, "boss": False},

    # Added more high-level variety
    "orc_chieftain": {"name": "Orc Chieftain", "race": "Orc", "level": 8, "base_hp": 55, "mods": {"Strength": 2, "Constitution": 1}, "boss": False},
    "bone_colossus": {"name": "Bone Colossus", "race": "Undead", "level": 9, "base_hp": 65, "mods": {"Constitution": 3}, "boss": False},
    "greater_demon": {"name": "Greater Demon", "race": "Demon", "level": 9, "base_hp": 58, "mods": {"Strength": 2, "Charisma": 2}, "boss": False},
    "iron_golem": {"name": "Iron Golem", "race": "Construct", "level": 8, "base_hp": 70, "mods": {"Strength": 1}, "boss": False},
    "elite_assassin": {"name": "Elite Assassin", "race": "Human", "level": 7, "base_hp": 42, "mods": {"Dexterity": 3}, "boss": False},
    "elder_dragonkin": {"name": "Elder Dragonkin", "race": "Dragonkin", "level": 9, "base_hp": 68, "mods": {"Strength": 3, "Constitution": 1}, "boss": False},
    "blood_vampire": {"name": "Blood Vampire", "race": "Vampire", "level": 9, "base_hp": 52, "mods": {"Dexterity": 2, "Charisma": 2}, "boss": False},
    "hill_giant": {"name": "Hill Giant", "race": "Giant", "level": 8, "base_hp": 75, "mods": {"Strength": 3}, "boss": False},
    "lizardfolk_champion": {"name": "Lizardfolk Champion", "race": "Lizardfolk", "level": 7, "base_hp": 48, "mods": {"Strength": 2}, "boss": False},
    "arcane_clockwork": {"name": "Arcane Clockwork", "race": "Clockwork", "level": 9, "base_hp": 52, "mods": {"Learning": 3}, "boss": False},
    "night_stalker": {"name": "Night Stalker", "race": "Shadow", "level": 8, "base_hp": 44, "mods": {"Dexterity": 4}, "boss": False},
    "thunder_elemental": {"name": "Thunder Elemental", "race": "Elemental", "level": 9, "base_hp": 60, "mods": {"Constitution": 2}, "boss": False},

    # Very High level (10–12) - new category for bigger level range
    "orc_berserker": {"name": "Orc Berserker", "race": "Orc", "level": 10, "base_hp": 72, "mods": {"Strength": 4}, "boss": False},
    "death_knight": {"name": "Death Knight", "race": "Undead", "level": 11, "base_hp": 68, "mods": {"Strength": 2, "Dexterity": 2}, "boss": False},
    "infernal_hound": {"name": "Infernal Hound", "race": "Demon", "level": 10, "base_hp": 65, "mods": {"Strength": 2, "Dexterity": 2}, "boss": False},
    "adamantine_golem": {"name": "Adamantine Golem", "race": "Construct", "level": 12, "base_hp": 95, "mods": {"Constitution": 3}, "boss": False},
    "warlord_general": {"name": "Warlord General", "race": "Human", "level": 10, "base_hp": 62, "mods": {"Strength": 3, "Charisma": 2}, "boss": False},
    "mature_dragonkin": {"name": "Mature Dragonkin", "race": "Dragonkin", "level": 11, "base_hp": 82, "mods": {"Strength": 4, "Constitution": 2}, "boss": False},
    "ancient_vampire": {"name": "Ancient Vampire", "race": "Vampire", "level": 12, "base_hp": 75, "mods": {"Dexterity": 3, "Charisma": 2}, "boss": False},
    "storm_giant": {"name": "Storm Giant", "race": "Giant", "level": 11, "base_hp": 98, "mods": {"Strength": 4, "Constitution": 2}, "boss": False},
    "lizardfolk_warlord": {"name": "Lizardfolk Warlord", "race": "Lizardfolk", "level": 10, "base_hp": 70, "mods": {"Strength": 3}, "boss": False},
    "titan_clockwork": {"name": "Titan Clockwork", "race": "Clockwork", "level": 12, "base_hp": 88, "mods": {"Constitution": 4}, "boss": False},
    "void_shadow": {"name": "Void Shadow", "race": "Shadow", "level": 11, "base_hp": 58, "mods": {"Dexterity": 4}, "boss": False},
    "colossal_abomination": {"name": "Colossal Abomination", "race": "Abomination", "level": 12, "base_hp": 110, "mods": {"Strength": 5, "Constitution": 3}, "boss": False},
    "arcane_elemental": {"name": "Arcane Elemental", "race": "Elemental", "level": 10, "base_hp": 68, "mods": {"Learning": 4}, "boss": False},
    "master_artificer": {"name": "Master Artificer", "race": "Gnome", "level": 11, "base_hp": 55, "mods": {"Learning": 4, "Dexterity": 2}, "boss": False},

    # Bosses
    "demon_imp": {"name": "Demon Imp", "race": "Demon", "level": 6, "base_hp": 28, "mods": {"Learning": 1}, "boss": True},
    "demon_knight": {"name": "Demon Knight", "race": "Demon", "level": 10, "base_hp": 68, "mods": {"Strength": 3}, "boss": True},
    "lich": {"name": "Lich", "race": "Undead", "level": 11, "base_hp": 58, "mods": {"Learning": 4}, "boss": True},
    "ancient_golem": {"name": "Ancient Golem", "race": "Construct", "level": 12, "base_hp": 88, "mods": {"Strength": 2}, "boss": True},
    "demon_lord": {"name": "Demon Lord", "race": "Demon", "level": 15, "base_hp": 115, "mods": {"Strength": 4, "Charisma": 3}, "boss": True},
    "ancient_dragonkin": {"name": "Ancient Dragonkin", "race": "Dragonkin", "level": 14, "base_hp": 105, "mods": {"Strength": 4, "Constitution": 3}, "boss": True},
    "fey_lord": {"name": "Fey Lord", "race": "Fey", "level": 13, "base_hp": 82, "mods": {"Dexterity": 4, "Charisma": 3}, "boss": True},
    "storm_elemental": {"name": "Storm Elemental", "race": "Elemental", "level": 12, "base_hp": 95, "mods": {"Learning": 3, "Constitution": 2}, "boss": True},
    "vampire_lord": {"name": "Vampire Lord", "race": "Vampire", "level": 15, "base_hp": 102, "mods": {"Dexterity": 4, "Charisma": 3}, "boss": True},
    "mountain_giant": {"name": "Mountain Giant", "race": "Giant", "level": 13, "base_hp": 135, "mods": {"Strength": 5}, "boss": True},
    "lizardfolk_king": {"name": "Lizardfolk King", "race": "Lizardfolk", "level": 13, "base_hp": 95, "mods": {"Strength": 3, "Constitution": 3}, "boss": True},
    "clockwork_titan": {"name": "Clockwork Titan", "race": "Clockwork", "level": 14, "base_hp": 110, "mods": {"Strength": 4, "Constitution": 4}, "boss": True},
    "shadow_dragon": {"name": "Shadow Dragon", "race": "Shadow", "level": 16, "base_hp": 100, "mods": {"Dexterity": 5, "Charisma": 2}, "boss": True},
    "abomination_overlord": {"name": "Abomination Overlord", "race": "Abomination", "level": 18, "base_hp": 160, "mods": {"Strength": 6, "Constitution": 5, "Wisdom": -2}, "boss": True},
    "gnome_high_artificer": {"name": "Gnome High Artificer", "race": "Gnome", "level": 12, "base_hp": 68, "mods": {"Learning": 5, "Dexterity": 2}, "boss": True},
    "greater_abomination": {"name": "Greater Abomination", "race": "Abomination", "level": 11, "base_hp": 85, "mods": {"Strength": 4, "Constitution": 3}, "boss": True},

    # Added more powerful bosses for bigger level range
    "arch_lich": {"name": "Arch Lich", "race": "Undead", "level": 17, "base_hp": 125, "mods": {"Learning": 6, "Constitution": 2}, "boss": True},
    "balor_demon": {"name": "Balor Demon", "race": "Demon", "level": 18, "base_hp": 140, "mods": {"Strength": 5, "Charisma": 4}, "boss": True},
    "titanic_golem": {"name": "Titanic Golem", "race": "Construct", "level": 16, "base_hp": 155, "mods": {"Strength": 5, "Constitution": 4}, "boss": True},
    "dragonkin_overlord": {"name": "Dragonkin Overlord", "race": "Dragonkin", "level": 19, "base_hp": 165, "mods": {"Strength": 6, "Constitution": 4}, "boss": True},
    "primordial_elemental": {"name": "Primordial Elemental", "race": "Elemental", "level": 17, "base_hp": 130, "mods": {"Constitution": 5, "Learning": 4}, "boss": True},
    "abyssal_abomination": {"name": "Abyssal Abomination", "race": "Abomination", "level": 20, "base_hp": 180, "mods": {"Strength": 7, "Constitution": 6}, "boss": True},
    "eternal_shadow": {"name": "Eternal Shadow", "race": "Shadow", "level": 16, "base_hp": 95, "mods": {"Dexterity": 6, "Charisma": 3}, "boss": True},

    # Super Bosses (20+)
    #Broodmother Vilehart
    "broodmother_vileheart": {
    "name": "Broodmother Vileheart",
    "race": "Beast",
    "level": 20,
    "base_hp": 350,
    "mods": {"Strength": 6, "Constitution": 6, "Dexterity": 4},
    "boss": True,
    "super_boss": True
    },
    "vileheart_spiderling": {
    "name": "Vileheart Spiderling",
    "race": "Beast",
    "level": 15,
    "base_hp": 45,
    "mods": {"Dexterity": 5, "Strength": 2},
    "boss": False
    },

    # Dream-Devouring Slitcurrent
    "dream_devouring_slitcurrent": {
    "name": "Dream-Devouring Slitcurrent",
    "race": "Abomination",
    "level": 21,
    "base_hp": 420,
    "mods": {"Strength": 5, "Constitution": 7, "Dexterity": 6},
    "boss": True,
    "super_boss": True
    },
    "dream_floatsam": {
    "name": "Dream Floatsam",
    "race": "Construct",
    "level": 16,
    "base_hp": 55,
    "mods": {"Dexterity": 4, "Constitution": 2},
    "boss": False
    }
}