"""Quest definitions and the Command Resonance grade ladder.

Pure data module — imports nothing from game systems, so it is safe to import
from anywhere (facilities, combat, GUI, tests).

Design reference: docs/quest_system_design.md

Quest schema
────────────
QUESTS[quest_id] = {
    "id":           str,
    "type":         "main" | "side",
    "name":         str,                  # shown in the Journal title bar
    "giver":        str,                  # npc id (informational)
    "region":       str,                  # informational
    "prereq":       None | quest_id | flag_name,
    "turn_in":      None,                 # None => auto-completes when all objectives done
    "journal_desc": str,                  # keep to 2-3 lines (Journal renders it as one label)
    "stages": [
        {"id": str, "desc": str,
         "objectives": [{"type": str, "target": str, "label": str}, ...]},
    ],
    "rewards": {
        "xp":           int,
        "gold":         int,
        "items":        [{"id": item_id, "rarity": "common"}, ...],
        "flags":        [flag_name, ...],
        "grade_unlock": int | None,       # Command Resonance tier granted (RESONANCE_GRADES)
        "next":         quest_id | None,  # auto-started on completion
    },
}

Runtime helpers live in the root-level ``quests.py``.
"""

# ── Command Resonance grades — SINGLE SOURCE OF TRUTH ─────────────────────────
# front = combat row size (player + active allies); bench = reserve slots.
# Grade 5 (Crescendo, 4/4) matches the game's historical fixed party caps, so
# endgame content needs no rebalancing when the ladder is implemented.
RESONANCE_GRADES = {
    0: {"name": "Unattuned", "front": 2, "bench": 0},
    1: {"name": "Pitch",     "front": 3, "bench": 0},
    2: {"name": "Timbre",    "front": 3, "bench": 1},
    3: {"name": "Cadence",   "front": 3, "bench": 2},
    4: {"name": "Chord",     "front": 4, "bench": 2},
    5: {"name": "Crescendo", "front": 4, "bench": 4},
}

MAX_RESONANCE_TIER = max(RESONANCE_GRADES)


def get_resonance_grade(tier):
    """Return the grade dict for a tier (clamped to the valid range)."""
    tier = max(0, min(int(tier), MAX_RESONANCE_TIER))
    return RESONANCE_GRADES[tier]


def get_grade_name(tier):
    """Return just the display name for a tier, e.g. 'Pitch'."""
    return get_resonance_grade(tier)["name"]


# Human-readable requirement for each earned grade (UI text).
GRADE_REQUIREMENTS = {
    1: "own a house and capture your first monster girl",
    2: "recruit one monster girl (50 affection)",
    3: "recruit 3 distinct monster girls",
    4: "collect 6 distinct girls across 3+ races",
    5: "collect 10+ distinct girls across 5+ races, and marry one",
}


def get_next_grade(tier):
    """Return (next_tier, grade_dict, requirement_text), or None at the cap."""
    nxt = int(tier) + 1
    if nxt not in RESONANCE_GRADES:
        return None
    return nxt, RESONANCE_GRADES[nxt], GRADE_REQUIREMENTS.get(nxt, "")


def format_resonance_status(tier):
    """One-line Command Resonance status for UI screens."""
    grade = get_resonance_grade(tier)
    line = (f"Command Resonance: {grade['name']} — "
            f"{grade['front']} front / {grade['bench']} bench")
    nxt = get_next_grade(tier)
    if nxt:
        _, nxt_grade, req = nxt
        line += f"  ·  Next: {nxt_grade['name']} ({req})"
    return line


# ── The Resonance Orb — Voss's "resonance blank" ────────────────────────────
# One key item whose name, rarity and lore grow whole as the tier rises. The
# runtime refreshes it (quests._refresh_resonance_orb); tier -> state here.
RESONANCE_ORB_STATES = {
    0: {"name": "Shattered Orb", "rarity": "common",
        "lore": ("The shards sit cold in their cloth wrap, inert as a song "
                 "no one has played yet.")},
    1: {"name": "Cracked Orb", "rarity": "uncommon",
        "lore": ("The shards have drawn themselves together. Hairline cracks "
                 "web the surface, and somewhere inside, a single note hums.")},
    2: {"name": "Mending Orb", "rarity": "rare",
        "lore": ("The cracks are drawing shut. Warm light pools along the "
                 "seams, steady as long as companions stand beside you.")},
    3: {"name": "Whole Orb", "rarity": "epic",
        "lore": ("Smooth and clear, holding a resonance that never quite "
                 "fades — a full phrase, quietly repeating.")},
    4: {"name": "Radiant Orb", "rarity": "legendary",
        "lore": ("Light moves beneath the surface like a choir breathing. "
                 "Held close, you can almost hear the harmonies overlap.")},
    5: {"name": "Resonant Orb", "rarity": "mythic",
        "lore": ("The orb sings. Not loudly — completely. Every bond in "
                 "your ledger is in the note, and the note is in tune.")},
}


def get_orb_state(tier):
    """Return the Resonance Orb state dict (name/rarity/lore) for a tier."""
    tier = max(0, min(int(tier), MAX_RESONANCE_TIER))
    return RESONANCE_ORB_STATES[tier]


def format_orb_meter(tier):
    """Six-slot fill meter — the orb becoming whole: '✦ ✦ · · · ·'."""
    tier = max(0, min(int(tier), MAX_RESONANCE_TIER))
    return " ".join("✦" if i <= tier else "·"
                    for i in range(MAX_RESONANCE_TIER + 1))


# ── Quest registry ────────────────────────────────────────────────────────────

QUESTS = {
    "mq_archivist_01": {
        "id": "mq_archivist_01",
        "type": "main",
        "name": "The Stellar Summons",
        "giver": "archivist_voss",
        "region": "skylume",
        "prereq": None,
        "turn_in": None,                    # auto-completes at the audience scene
        "journal_desc": (
            "A recorded message from Archivist Quillan Voss of Skylume's "
            "Star Tower. He asks for help — and asks you to come in person."
        ),
        "stages": [
            {
                "id": "journey",
                "desc": "Travel to Skylume and enter the Star Tower.",
                "objectives": [
                    {"type": "visit_city",    "target": "skylume",    "label": "Reach Skylume"},
                    {"type": "visit_service", "target": "star_tower", "label": "Enter the Star Tower"},
                ],
            },
            {
                "id": "audience",
                "desc": "Speak with Archivist Voss.",
                "objectives": [
                    {"type": "talk_npc", "target": "archivist_voss", "label": "Speak with Archivist Voss"},
                ],
            },
        ],
        "rewards": {
            "xp": 150,
            "gold": 80,
            "items": [],
            "flags": ["met_voss"],
            "grade_unlock": None,
            "next": "mq_archivist_02",
        },
    },

    "mq_archivist_02": {
        "id": "mq_archivist_02",
        "type": "main",
        "name": "A Place to Belong",
        "giver": "archivist_voss",
        "region": "skylume",
        "prereq": "mq_archivist_01",
        "turn_in": None,
        "journal_desc": (
            "Field Study One — Voss needs a baseline reading: a home, and "
            "a monster girl who chooses it. Then the first thread of "
            "resonance can be measured."
        ),
        "stages": [
            {
                "id": "home",
                "desc": "Prepare a home for your first companion.",
                "objectives": [
                    {"type": "own_house", "target": "any",
                     "label": "Own a house (deed from a Trade Hall)"},
                ],
            },
            {
                "id": "capture",
                "desc": "Capture your first monster girl.",
                "objectives": [
                    {"type": "capture_girl", "target": "any",
                     "label": "Capture a monster girl in battle"},
                ],
            },
        ],
        "rewards": {
            "xp": 200,
            "gold": 0,
            "items": [],
            "flags": [],
            "grade_unlock": 1,              # Pitch
            "next": "mq_archivist_03",
        },
    },

    "mq_archivist_03": {
        "id": "mq_archivist_03",
        "type": "main",
        "name": "A Willing Bond",
        "giver": "archivist_voss",
        "region": "skylume",
        "prereq": "mq_archivist_02",
        "turn_in": None,
        "journal_desc": (
            "Field Study Two — Voss wants the reading for a partnership, "
            "not just a household: one monster girl who fights at your side."
        ),
        "stages": [
            {
                "id": "recruit",
                "desc": "Recruit a companion to fight beside you.",
                "objectives": [
                    {"type": "recruit_count", "target": "1",
                     "label": "Recruit a monster girl (50 affection)"},
                ],
            },
        ],
        "rewards": {
            "xp": 250,
            "gold": 0,
            "items": [],
            "flags": [],
            "grade_unlock": 2,              # Timbre
            "next": "mq_archivist_04",
        },
    },

    "mq_archivist_04": {
        "id": "mq_archivist_04",
        "type": "main",
        "name": "Variety of Command",
        "giver": "archivist_voss",
        "region": "skylume",
        "prereq": "mq_archivist_03",
        "turn_in": None,
        "journal_desc": (
            "Field Study Three — can one handler hold three different "
            "voices in concert? The Archive needs the reading."
        ),
        "stages": [
            {
                "id": "variety",
                "desc": "Recruit three distinct companions.",
                "objectives": [
                    {"type": "recruit_count", "target": "3",
                     "label": "Recruit three distinct monster girls"},
                ],
            },
        ],
        "rewards": {
            "xp": 350,
            "gold": 0,
            "items": [],
            "flags": [],
            "grade_unlock": 3,              # Cadence
            "next": "mq_archivist_05",
        },
    },

    "mq_archivist_05": {
        "id": "mq_archivist_05",
        "type": "main",
        "name": "The Broad Ledger",
        "giver": "archivist_voss",
        "region": "skylume",
        "prereq": "mq_archivist_04",
        "turn_in": None,
        "journal_desc": (
            "Field Study Four — the Archive measures breadth now: "
            "many girls, many races, one ledger."
        ),
        "stages": [
            {
                "id": "breadth",
                "desc": "Broaden the household.",
                "objectives": [
                    {"type": "collection_count", "target": "6",
                     "label": "Own six distinct monster girls"},
                    {"type": "race_count", "target": "3",
                     "label": "Command three different races"},
                ],
            },
        ],
        "rewards": {
            "xp": 500,
            "gold": 0,
            "items": [],
            "flags": [],
            "grade_unlock": 4,              # Chord
            "next": "mq_archivist_06",
        },
    },

    "mq_archivist_06": {
        "id": "mq_archivist_06",
        "type": "main",
        "name": "Grand Resonance",
        "giver": "archivist_voss",
        "region": "skylume",
        "prereq": "mq_archivist_05",
        "turn_in": None,
        "journal_desc": (
            "Field Study Five — the capstone reading: a full household, "
            "five races, one marriage. The Archive has waited a long "
            "time for these numbers."
        ),
        "stages": [
            {
                "id": "grand",
                "desc": "Complete the ledger.",
                "objectives": [
                    {"type": "collection_count", "target": "10",
                     "label": "Own ten distinct monster girls"},
                    {"type": "race_count", "target": "5",
                     "label": "Command five different races"},
                    {"type": "married", "target": "1",
                     "label": "Marry one of them"},
                ],
            },
        ],
        "rewards": {
            "xp": 800,
            "gold": 0,
            "items": [],
            "flags": [],
            "grade_unlock": 5,              # Crescendo
            "next": None,
        },
    },

    # ── Wonderland side quests ────────────────────────────────────────────
    # The hidden realm has no quest board: the book, the tea party, and the
    # Storybook Dungeon are the givers. quests._sync_wonderland_quests()
    # starts these automatically as the player progresses.
    "sq_wonderland_00": {
        "id": "sq_wonderland_00",
        "type": "side",
        "name": "The Looking-Glass Road",
        "giver": "white_rabbit",
        "region": "veilholt",
        "prereq": None,
        "turn_in": None,
        "journal_desc": (
            "Wonderland is reached through a book in Veilholt's Arcane Tower. "
            "Clear Floor 20 in two different biomes to unlock the Looking "
            "Glass Shard at Veilholt's Black Market (5,000g) — then open the "
            "book."
        ),
        "stages": [
            {
                "id": "gate",
                "desc": "Prove you are ready for the hidden realm.",
                "objectives": [
                    {"type": "wonderland_gate", "target": "2",
                     "label": "Clear Floor 20 in two different biomes"},
                ],
            },
            {
                "id": "shard",
                "desc": "Find the key that looks through, not at.",
                "objectives": [
                    {"type": "wonderland_shard", "target": "looking_glass_shard",
                     "label": "Hold a Looking Glass Shard (Veilholt Black Market)"},
                ],
            },
            {
                "id": "book",
                "desc": "Open the book.",
                "objectives": [
                    {"type": "wonderland_enter", "target": "any",
                     "label": "Open the book in Veilholt's Arcane Tower"},
                ],
            },
        ],
        "rewards": {
            "xp": 300,
            "gold": 250,
            "items": [],
            "flags": [],
            "grade_unlock": None,
            "next": "sq_wonderland_01",
        },
    },

    "sq_wonderland_01": {
        "id": "sq_wonderland_01",
        "type": "side",
        "name": "Down the Rabbit Hole",
        "giver": "white_rabbit",
        "region": "wonderland",
        "prereq": None,
        "turn_in": None,
        "journal_desc": (
            "The mysterious book in Veilholt's Arcane Tower opens onto a realm "
            "stitched from stories. The White Rabbit is late, the Queen is "
            "furious, and the Storybook Dungeon is waiting. After the Queen "
            "falls, return to the Mad Hatter's tea party — guests are waiting."
        ),
        "stages": [
            {
                "id": "arrival",
                "desc": "Step through the looking-glass.",
                "objectives": [
                    {"type": "wonderland_enter", "target": "any",
                     "label": "Enter Wonderland through the mysterious book"},
                ],
            },
            {
                "id": "queen",
                "desc": "Survive the first chapter.",
                "objectives": [
                    {"type": "wonderland_boss", "target": "queen_of_hearts",
                     "label": "Defeat the Queen of Hearts (Floor 10)"},
                ],
            },
            {
                "id": "tea_party",
                "desc": "The tea party has guests.",
                "objectives": [
                    {"type": "wonderland_guest_scene", "target": "any",
                     "label": "Return to the Mad Hatter's tea party"},
                ],
            },
        ],
        "rewards": {
            "xp": 400,
            "gold": 300,
            "items": [],
            "flags": [],
            "grade_unlock": None,
            "next": "sq_wonderland_02",
        },
    },

    "sq_wonderland_02": {
        "id": "sq_wonderland_02",
        "type": "side",
        "name": "The Storybook Road",
        "giver": "white_rabbit",
        "region": "wonderland",
        "prereq": "sq_wonderland_01",
        "turn_in": None,
        "journal_desc": (
            "The road through Wonderland runs floor by floor. The deeper "
            "chapters hold the Wolf, the Witch, the Jabberwock — and the "
            "Author at the very end."
        ),
        "stages": [
            {
                "id": "deep",
                "desc": "Follow the story deeper.",
                "objectives": [
                    {"type": "wonderland_floor", "target": "20",
                     "label": "Reach Floor 20 of the Storybook Dungeon"},
                    {"type": "wonderland_floor", "target": "30",
                     "label": "Reach Floor 30 of the Storybook Dungeon"},
                    {"type": "wonderland_floor", "target": "40",
                     "label": "Reach Floor 40 of the Storybook Dungeon"},
                ],
            },
        ],
        "rewards": {
            "xp": 700,
            "gold": 600,
            "items": [],
            "flags": [],
            "grade_unlock": None,
            "next": "sq_wonderland_03",
        },
    },

    "sq_wonderland_03": {
        "id": "sq_wonderland_03",
        "type": "side",
        "name": "The Author's Last Page",
        "giver": "white_rabbit",
        "region": "wonderland",
        "prereq": "sq_wonderland_02",
        "turn_in": None,
        "journal_desc": (
            "Every chapter has an ending. At the bottom of the Storybook, the "
            "Author is still writing — and she does not intend to let anyone "
            "leave."
        ),
        "stages": [
            {
                "id": "finale",
                "desc": "Close the book.",
                "objectives": [
                    {"type": "wonderland_boss", "target": "big_bad_wolf",
                     "label": "Defeat the Big Bad Wolf (Floor 20)"},
                    {"type": "wonderland_boss", "target": "wicked_witch",
                     "label": "Defeat the Wicked Witch of the West (Floor 30)"},
                    {"type": "wonderland_boss", "target": "jabberwock",
                     "label": "Defeat the Jabberwock (Floor 40)"},
                    {"type": "wonderland_boss", "target": "mary_sue",
                     "label": "Defeat Mary Sue, the Author (Floor 50)"},
                ],
            },
        ],
        "rewards": {
            "xp": 1200,
            "gold": 1000,
            "items": [],
            "flags": [],
            "grade_unlock": None,
            "next": None,
        },
    },

    # ── Wonderland heroine arcs ───────────────────────────────────────────
    # Each arc starts when the heroine is first met at the Mad Hatter's tea
    # party and resolves when her personal superboss is defeated.
    "sq_wonderland_alice": {
        "id": "sq_wonderland_alice",
        "type": "side",
        "name": "Alice's Jabberwock",
        "giver": "alice",
        "region": "wonderland",
        "prereq": None,
        "turn_in": None,
        "journal_desc": (
            "Alice has been counting sugar cubes at the Mad Hatter's table "
            "while a beast writes its own ending. She would like her story "
            "back."
        ),
        "stages": [
            {
                "id": "meet",
                "desc": "Find Alice at the tea party.",
                "objectives": [
                    {"type": "heroine_met", "target": "alice",
                     "label": "Meet Alice at the Mad Hatter's tea party"},
                ],
            },
            {
                "id": "join",
                "desc": "Invite her to travel with you.",
                "objectives": [
                    {"type": "heroine_recruited", "target": "alice",
                     "label": "Recruit Alice into your party"},
                ],
            },
            {
                "id": "jabberwock",
                "desc": "Face the beast that rewrote her story.",
                "objectives": [
                    {"type": "wonderland_boss", "target": "jabberwock",
                     "label": "Defeat the Jabberwock (Floor 40)"},
                ],
            },
            {
                "id": "free",
                "desc": "See Alice's story to its end.",
                "objectives": [
                    {"type": "heroine_permanent", "target": "alice",
                     "label": "Help Alice become a permanent ally"},
                ],
            },
        ],
        "rewards": {
            "xp": 800,
            "gold": 500,
            "items": [],
            "flags": [],
            "grade_unlock": None,
            "next": None,
        },
    },

    "sq_wonderland_red_hood": {
        "id": "sq_wonderland_red_hood",
        "type": "side",
        "name": "Red Hood's New Ending",
        "giver": "red_hood",
        "region": "wonderland",
        "prereq": None,
        "turn_in": None,
        "journal_desc": (
            "Red Hood came to Wonderland to write a new ending for her story. "
            "The Big Bad Wolf ate the old one — and he is still hungry."
        ),
        "stages": [
            {
                "id": "meet",
                "desc": "Find Red Hood at the tea party.",
                "objectives": [
                    {"type": "heroine_met", "target": "red_hood",
                     "label": "Meet Red Hood at the Mad Hatter's tea party"},
                ],
            },
            {
                "id": "join",
                "desc": "Prove your back is worth watching.",
                "objectives": [
                    {"type": "heroine_recruited", "target": "red_hood",
                     "label": "Recruit Red Hood into your party"},
                ],
            },
            {
                "id": "wolf",
                "desc": "Hunt the Wolf that ate her ending.",
                "objectives": [
                    {"type": "wonderland_boss", "target": "big_bad_wolf",
                     "label": "Defeat the Big Bad Wolf (Floor 20)"},
                ],
            },
            {
                "id": "free",
                "desc": "Let her write her own ending.",
                "objectives": [
                    {"type": "heroine_permanent", "target": "red_hood",
                     "label": "Help Red Hood become a permanent ally"},
                ],
            },
        ],
        "rewards": {
            "xp": 800,
            "gold": 500,
            "items": [],
            "flags": [],
            "grade_unlock": None,
            "next": None,
        },
    },

    "sq_wonderland_dorothy": {
        "id": "sq_wonderland_dorothy",
        "type": "side",
        "name": "Dorothy's Way Home",
        "giver": "dorothy",
        "region": "wonderland",
        "prereq": None,
        "turn_in": None,
        "journal_desc": (
            "Dorothy has walked the yellow brick road six times, and it never "
            "ends where she wants. To go home, she must first finish the "
            "Witch's story."
        ),
        "stages": [
            {
                "id": "meet",
                "desc": "Find Dorothy at the tea party.",
                "objectives": [
                    {"type": "heroine_met", "target": "dorothy",
                     "label": "Meet Dorothy at the Mad Hatter's tea party"},
                ],
            },
            {
                "id": "join",
                "desc": "Walk the road with her.",
                "objectives": [
                    {"type": "heroine_recruited", "target": "dorothy",
                     "label": "Recruit Dorothy into your party"},
                ],
            },
            {
                "id": "witch",
                "desc": "Face the Witch the story demands.",
                "objectives": [
                    {"type": "wonderland_boss", "target": "wicked_witch",
                     "label": "Defeat the Wicked Witch of the West (Floor 30)"},
                ],
            },
            {
                "id": "free",
                "desc": "Show her home can wait for the right ending.",
                "objectives": [
                    {"type": "heroine_permanent", "target": "dorothy",
                     "label": "Help Dorothy become a permanent ally"},
                ],
            },
        ],
        "rewards": {
            "xp": 800,
            "gold": 500,
            "items": [],
            "flags": [],
            "grade_unlock": None,
            "next": None,
        },
    },
}
