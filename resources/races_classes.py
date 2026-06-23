RACES = {
    "1": {
        "name": "Human", "desc": "Versatile and balanced.", "mods": {},
        "elemental_res": {}, "elemental_dmg": {}
    },
    "2": {
        "name": "Elf", "desc": "Agile and wise, but fragile.",
        "mods": {"Dexterity": 2, "Wisdom": 1, "Constitution": -1},
        "elemental_res": {"light": 1.2, "earth": 0.8},
        "elemental_dmg": {"wind": 1.3, "light": 1.1}
    },
    "3": {
        "name": "Dwarf", "desc": "Tough and strong, but clumsy.",
        "mods": {"Strength": 1, "Constitution": 2, "Dexterity": -1},
        "elemental_res": {"fire": 1.2, "wind": 0.8},
        "elemental_dmg": {"earth": 1.3, "fire": 1.1}
    },
    "4": {
        "name": "Halfling", "desc": "Quick and charming, but weak.",
        "mods": {"Dexterity": 2, "Charisma": 1, "Strength": -2},
        "elemental_res": {"earth": 1.2, "dark": 0.8},
        "elemental_dmg": {"wind": 1.3}
    },
    "5": {
        "name": "Orc", "desc": "Brutal and powerful, but impulsive.",
        "mods": {"Strength": 3, "Constitution": 1, "Wisdom": -2, "Charisma": -1},
        "elemental_res": {"dark": 1.2, "light": 0.8},
        "elemental_dmg": {"fire": 1.3, "dark": 1.1}
    },
    "6": {
        "name": "Gnome", "desc": "Ingenious tinkerers with sharp minds.",
        "mods": {"Learning": 3, "Dexterity": 1, "Strength": -2},
        "elemental_res": {"earth": 1.2, "thunder": 1.1},
        "elemental_dmg": {"thunder": 1.3, "earth": 1.1}
    },
    "7": {
        "name": "Tiefling", "desc": "Infernal blood grants dark charisma.",
        "mods": {"Charisma": 2, "Learning": 1, "Wisdom": -1, "Constitution": -1},
        "elemental_res": {"dark": 1.2, "light": 0.7, "water": 0.8},
        "elemental_dmg": {"fire": 1.3, "dark": 1.2}
    },
    "8": {
        "name": "Dragonborn", "desc": "Proud and resilient with draconic power.",
        "mods": {"Strength": 2, "Constitution": 2, "Charisma": 1, "Dexterity": -1},
        "elemental_res": {"fire": 1.2, "thunder": 1.2, "water": 1.1},
        "elemental_dmg": {"fire": 1.3, "thunder": 1.1}
    },
}

CLASSES = {
    "1": {
        "name": "Warrior", "desc": "Master of weapons and endurance.",
        "mods": {"Strength": 2, "Constitution": 2, "Wisdom": -1},
        "elemental_res": {}, "elemental_dmg": {}
    },
    "2": {
        "name": "Mage", "desc": "Wielder of arcane forces.",
        "mods": {"Learning": 3, "Wisdom": 1, "Strength": -2},
        "elemental_res": {"earth": 0.8},
        "elemental_dmg": {"fire": 1.3, "water": 1.3, "thunder": 1.2}
    },
    "3": {
        "name": "Rogue", "desc": "Stealthy and persuasive.",
        "mods": {"Dexterity": 2, "Charisma": 2, "Constitution": -1},
        "elemental_res": {"dark": 1.1},
        "elemental_dmg": {"dark": 1.3, "wind": 1.2}
    },
    "4": {
        "name": "Cleric", "desc": "Divine healer and protector.",
        "mods": {"Wisdom": 2, "Charisma": 1, "Learning": 1, "Strength": -1},
        "elemental_res": {"dark": 1.2, "light": 1.1},
        "elemental_dmg": {"light": 1.3}
    },
    "5": {
        "name": "Ranger", "desc": "Wilderness warrior and marksman.",
        "mods": {"Dexterity": 2, "Wisdom": 2, "Strength": 1, "Charisma": -1},
        "elemental_res": {"earth": 1.2, "wind": 1.1},
        "elemental_dmg": {"wind": 1.3, "earth": 1.1}
    },
    "6": {
        "name": "Paladin", "desc": "Holy knight sworn to justice.",
        "mods": {"Strength": 2, "Charisma": 2, "Constitution": 1, "Learning": -1},
        "elemental_res": {"dark": 1.2, "fire": 1.1, "light": 1.1},
        "elemental_dmg": {"light": 1.3, "fire": 1.1}
    },
    "7": {
        "name": "Warlock", "desc": "Bargainer with otherworldly powers.",
        "mods": {"Learning": 2, "Charisma": 3, "Constitution": -1, "Wisdom": -1},
        "elemental_res": {"dark": 1.2, "light": 0.8},
        "elemental_dmg": {"dark": 1.3, "fire": 1.1}
    },
    "8": {
        "name": "Barbarian", "desc": "Fierce rage-fueled warrior.",
        "mods": {"Strength": 3, "Constitution": 2, "Dexterity": -1, "Learning": -2},
        "elemental_res": {"wind": 0.8, "fire": 1.1},
        "elemental_dmg": {"fire": 1.3, "earth": 1.2}
    },
}

ATTRIBUTES = ["Strength", "Constitution", "Dexterity", "Wisdom", "Learning", "Charisma"]
TOTAL_POINTS = 15