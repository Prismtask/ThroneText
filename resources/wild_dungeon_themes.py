"""
resources/wild_dungeon_themes.py — Wild dungeon name themes.

Pure data module — imports nothing from game systems, safe to import from
anywhere (runtime, GUI, tests). Same pattern as resources/quests.py.

Design: docs/wild_dungeon_design.md §1.4

Wild dungeon names are f"{adjective} {ruin}", themed by the biome of the
random seed city the dungeon spawned near.
"""

WILD_DUNGEON_THEMES = {
    "tundra": {
        "adjectives": ["Frozen", "Howling", "Glacial", "Bitter", "Snowbound", "Hollowed"],
        "ruins": ["Maw", "Pit", "Sepulcher", "Citadel", "Catacombs", "Wound"],
    },
    "temperate": {
        "adjectives": ["Forgotten", "Sunken", "Verdant", "Moss-Crowned", "Silent", "Weathered"],
        "ruins": ["Crypt", "Hollow", "Barrens", "Vault", "Keep", "Reliquary"],
    },
    "swamp": {
        "adjectives": ["Drowned", "Miasmic", "Sodden", "Murky", "Rotting", "Choked"],
        "ruins": ["Mire", "Fen", "Bog-Temple", "Mausoleum", "Grotto", "Lair"],
    },
    "mountain": {
        "adjectives": ["Crumbling", "Wind-Scoured", "Cragbound", "Iron", "Echoing", "Thunderous"],
        "ruins": ["Delve", "Peak-Fort", "Gallery", "Aerie", "Mines", "Redoubt"],
    },
    "magical": {
        "adjectives": ["Ley-Woven", "Shimmering", "Arcane", "Starless", "Runebound", "Unmade"],
        "ruins": ["Sanctum", "Nexus", "Observatory", "Reliquary", "Vault", "Manse"],
    },
    "volcanic": {
        "adjectives": ["Smoldering", "Ashen", "Searing", "Cindered", "Magma-Touched", "Smoking"],
        "ruins": ["Caldera", "Forge-Ruins", "Furnace", "Foundry", "Cinder-Vault", "Pyre"],
    },
    "forest": {
        "adjectives": ["Tangled", "Rootbound", "Shadowed", "Sylvan", "Overgrown", "Whispering"],
        "ruins": ["Grove", "Thicket", "Hollow", "Shrine", "Warren", "Barrow"],
    },
    "savanna": {
        "adjectives": ["Sun-Bleached", "Wind-Worn", "Drought-Cursed", "Dusty", "Cracked", "Golden"],
        "ruins": ["Rise", "Termite-Fort", "Basin", "Outcrop", "Ziggurat", "Warren"],
    },
    "coastal": {
        "adjectives": ["Tide-Washed", "Barnacled", "Salt-Bitten", "Brine-Soaked", "Storm-Torn", "Sinking"],
        "ruins": ["Cove", "Spray-Ruins", "Reef-Crypt", "Lighthouse", "Breakers", "Depth"],
    },
    "desert": {
        "adjectives": ["Scorched", "Dune-Buried", "Mirage", "Wind-Carved", "Glass-Blasted", "Sunken"],
        "ruins": ["Tomb", "Sands", "Caravan-Fort", "Oasis-Ruin", "Necropolis", "Dune-Vault"],
    },
    "tropical": {
        "adjectives": ["Vine-Choked", "Monsoon", "Jungle-Hidden", "Coral", "Blooming", "Perfumed"],
        "ruins": ["Temple", "Atoll", "Canopy-Fort", "Grotto", "Ruins", "Shrine"],
    },
    "sea_caves": {
        "adjectives": ["Abyssal", "Brine-Black", "Echoing", "Barnacled", "Tide-Locked", "Drowned"],
        "ruins": ["Cavern", "Trench", "Grotto", "Cistern", "Sinkhole", "Maw"],
    },
    "pandemonium": {
        "adjectives": ["Crystalline", "Discordant", "Shard-Glass", "Hollow", "Resonant", "Fractured"],
        "ruins": ["Refraction", "Cacophony", "Prism-Vault", "Echo", "Lattice", "Chorus"],
    },
}

_DEFAULT_THEME = {
    "adjectives": ["Forgotten", "Sunken", "Hidden", "Crumbling", "Weathered", "Silent"],
    "ruins": ["Crypt", "Hollow", "Barrens", "Vault", "Ruins", "Keep"],
}


def get_theme(biome):
    """Return the {adjectives, ruins} theme for a biome (with a safe default)."""
    return WILD_DUNGEON_THEMES.get(biome, _DEFAULT_THEME)
