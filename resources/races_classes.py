RACES = {
    "1": {"name": "Human", "desc": "Versatile and balanced.", "mods": {}},
    "2": {"name": "Elf", "desc": "Agile and wise, but fragile.",
          "mods": {"Dexterity": 2, "Wisdom": 1, "Constitution": -1}},
    "3": {"name": "Dwarf", "desc": "Tough and strong, but clumsy.",
          "mods": {"Strength": 1, "Constitution": 2, "Dexterity": -1}},
    "4": {"name": "Halfling", "desc": "Quick and charming, but weak.",
          "mods": {"Dexterity": 2, "Charisma": 1, "Strength": -2}},
    "5": {"name": "Orc", "desc": "Brutal and powerful, but impulsive.",
          "mods": {"Strength": 3, "Constitution": 1, "Wisdom": -2, "Charisma": -1}},
    "6": {"name": "Gnome", "desc": "Ingenious tinkerers with sharp minds.",
          "mods": {"Learning": 3, "Dexterity": 1, "Strength": -2}},
    "7": {"name": "Tiefling", "desc": "Infernal blood grants dark charisma.",
          "mods": {"Charisma": 2, "Learning": 1, "Wisdom": -1, "Constitution": -1}},
    "8": {"name": "Dragonborn", "desc": "Proud and resilient with draconic power.",
          "mods": {"Strength": 2, "Constitution": 2, "Charisma": 1, "Dexterity": -1}},
}

CLASSES = {
    "1": {"name": "Warrior", "desc": "Master of weapons and endurance.",
          "mods": {"Strength": 2, "Constitution": 2, "Wisdom": -1}},
    "2": {"name": "Mage", "desc": "Wielder of arcane forces.",
          "mods": {"Learning": 3, "Wisdom": 1, "Strength": -2}},
    "3": {"name": "Rogue", "desc": "Stealthy and persuasive.",
          "mods": {"Dexterity": 2, "Charisma": 2, "Constitution": -1}},
    "4": {"name": "Cleric", "desc": "Divine healer and protector.",
          "mods": {"Wisdom": 2, "Charisma": 1, "Learning": 1, "Strength": -1}},
    "5": {"name": "Ranger", "desc": "Wilderness warrior and marksman.",
          "mods": {"Dexterity": 2, "Wisdom": 2, "Strength": 1, "Charisma": -1}},
    "6": {"name": "Paladin", "desc": "Holy knight sworn to justice.",
          "mods": {"Strength": 2, "Charisma": 2, "Constitution": 1, "Learning": -1}},
    "7": {"name": "Warlock", "desc": "Bargainer with otherworldly powers.",
          "mods": {"Learning": 2, "Charisma": 3, "Constitution": -1, "Wisdom": -1}},
    "8": {"name": "Barbarian", "desc": "Fierce rage-fueled warrior.",
          "mods": {"Strength": 3, "Constitution": 2, "Dexterity": -1, "Learning": -2}},
}

ATTRIBUTES = ["Strength", "Constitution", "Dexterity", "Wisdom", "Learning", "Charisma"]
TOTAL_POINTS = 20