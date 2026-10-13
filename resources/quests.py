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

    # Side quests: later phases.
}
