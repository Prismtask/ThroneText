"""Dream Events — pure data definitions.

Design: docs/dream_events_design.md (decisions locked 2026-10-30)

Phase 1 scope: boon and burden dreams only (no choices, no story dreams).
Dreams roll once per sleep at home / the inn / camp. See ``dreams.py`` for
the runtime (pool building, rolling, effects, journal).

Schema
──────
DREAMS = [
    {
        "id":       str,                  # stable, never reuse
        "name":     str,
        "category": "boon" | "burden" | "choice" | "story",
                                          # story = queued beat, never rolled
        "weight":   int,                  # base weight (>= 1)
        "once":     bool,                 # removed from the pool once seen
        "skippable": bool,                # choice dreams: offer Skip on repeats
        "content_level": None | "fade-to-black" | "written" | "any",
                                          # "any" = intimacy content is on
        "family":   bool,                 # requires player["family_enabled"]
        "flags_set": [flag, ...],        # story dreams: story flags to set
        "new_city_bonus": bool,           # weight x1.5 on the first dream in
                                          # a location (Memory/Omen dreams)
        "conditions": {
            "location": ("home", "inn", "camp"),   # tuple or single string
            "min_day":  int,
            "flags":    [flag, ...],      # quest flags OR top-level keys
            "not_flags": [flag, ...],
            "party_min": int,             # living party members required
            "party_race": str,            # a living party member of this race
        },
        "lines": [paragraph, ...],        # 2–5 short lines, dream tone
        "journal": str,                   # one-line Journal description
        "prompt": str,                    # choice dreams: menu header
        "prompts": [                      # choice dreams only
            {
                "text": str,              # option label (trade-off visible)
                "reply": str,             # flavor line after choosing
                "effects": {...},         # same effect keys as below
            },
        ],
        "effects": {
            "xp":          int,           # player XP (leveling.gain_exp)
            "ally_xp":     int,           # one living ally
            "gold_loss":   bool,          # capped at 5% / 50g (D4)
            "girl_stress": int,           # every living party girl (0–100)
            "player_stress": int,         # player stress meter (time_blocks)
            "affection":   int,           # one random living party girl
            "buff": {"type": str, "value": int|float, "rooms": int,
                     "target": "party" | "player"},
            "items": [{"id": item_id, "count": int}, ...],
        },
    },
]

Guardrails enforced by the runtime (not this module): no item loss, no
stat/level loss, gold loss capped, never two burden dreams in a row.
"""

# ── Content ──────────────────────────────────────────────────────────────────

DREAMS = [
    # ── Boons ────────────────────────────────────────────────────────────
    {
        "id": "dream_accord_page",
        "name": "The Forgiven Page",
        "category": "boon",
        "weight": 2,
        "once": True,
        "new_city_bonus": True,
        "conditions": {"min_day": 3},
        "lines": [
            "A page turns somewhere under the floor of the world.",
            "The words rearrange themselves as you read: a ledger of every",
            "debt the Accord ever forgave, written in a hand much like yours.",
            "When you wake, one line stays with you, sharp as a paper cut.",
        ],
        "journal": "You dreamed of the Accord's ledger — and one debt that was forgiven.",
        "effects": {"xp": 10},
    },
    {
        "id": "dream_inspired",
        "name": "The Unlearned Kata",
        "category": "boon",
        "weight": 4,
        "once": False,
        "conditions": {},
        "lines": [
            "You dream of a kata you have never learned, performed perfectly.",
            "Your hands know the ending long before your mind does.",
            "You wake with the shape of it still moving through your fingers.",
        ],
        "journal": "You dreamed a form you have never trained — and remembered it.",
        "effects": {"xp": 35},
    },
    {
        "id": "dream_restful",
        "name": "Deeper Than the Well",
        "category": "boon",
        "weight": 4,
        "once": False,
        "conditions": {},
        "lines": [
            "Warm water, deeper than any well, holds you without drowning.",
            "Something older than the town rocks you the way a mother would,",
            "patient and unhurried, and asks nothing in return.",
            "You wake rested past the reach of your own bones.",
        ],
        "journal": "You slept deeper than sleep — the party wakes clear-headed.",
        "effects": {"buff": {"type": "dream_blessed", "value": 1,
                             "rooms": 2, "target": "party"}},
    },
    {
        "id": "dream_steady_hands",
        "name": "The Grey Cat's Favour",
        "category": "boon",
        "weight": 3,
        "once": False,
        "conditions": {},
        "lines": [
            "A grey cat watches you from a fence you have never seen.",
            "It blinks once, slowly, and the whole world tilts a half-degree",
            "in your favour. Nothing else happens. That is the point.",
            "You wake with a heartbeat exaggeratedly calm.",
        ],
        "journal": "A grey cat's slow blink followed you out of the dream.",
        "effects": {"buff": {"type": "crit_chance", "value": 0.05,
                             "rooms": 2, "target": "player"}},
    },
    {
        "id": "dream_small_mercy",
        "name": "The Smaller Hand",
        "category": "boon",
        "weight": 2,
        "once": False,
        "conditions": {},
        "lines": [
            "A hand — yours, but smaller — presses something warm into your palm.",
            "\"You'll need this,\" the child says. \"You always forget.\"",
            "You wake with the weight still there, close against your fingers.",
        ],
        "journal": "A smaller version of you gave you something to carry.",
        "effects": {"items": [{"id": "healing_potion", "count": 1}]},
    },
    {
        "id": "dream_warm_company",
        "name": "A Fire That Needs No Wood",
        "category": "boon",
        "weight": 4,
        "once": False,
        "conditions": {"party_min": 1},
        "lines": [
            "The dream has no walls and no weather, only a fire that needs no wood.",
            "{girl} is there, saying nothing, which is somehow the kindest thing.",
            "You wake before you can answer, and the answer no longer matters.",
        ],
        "journal": "You dreamed of good company and woke warmer for it.",
        "effects": {"affection": 2},
    },
    {
        "id": "dream_clear_water",
        "name": "The Tide That Stays",
        "category": "boon",
        "weight": 4,
        "once": False,
        "conditions": {"party_min": 1},
        "lines": [
            "You walk a shoreline that keeps going, and the tide does not follow.",
            "Every worry you set down on the sand stays there, small and far behind.",
            "The party wakes lighter, as if they walked it with you.",
        ],
        "journal": "You dreamed a quiet shore — the party's worries eased.",
        "effects": {"girl_stress": -6},
    },

    # ── Burdens ──────────────────────────────────────────────────────────
    {
        "id": "dream_thin_place",
        "name": "Under the Door",
        "category": "burden",
        "weight": 4,
        "once": False,
        "conditions": {},
        "lines": [
            "The Dark comes in under the door, patient as water finding a seam.",
            "It knows your name and uses it the way an old friend would.",
            "You wake with your hand on a weapon that isn't there.",
            "The small mercy is this: the dark stayed in the dream.",
        ],
        "journal": "The Dark visited your sleep and left its patience behind.",
        "effects": {"girl_stress": 8, "player_stress": 34},
    },
    {
        "id": "dream_restless_watch",
        "name": "The Watch Nobody Set",
        "category": "burden",
        "weight": 3,
        "once": False,
        "conditions": {},
        "lines": [
            "You dream of a watch you never agreed to: a wall, a road, a door.",
            "Nothing comes. Nothing comes. Nothing comes.",
            "You wake more tired than you lay down — but your eyes have",
            "learned every corner of the room, and corners remember things.",
        ],
        "journal": "You stood a watch in your sleep and woke with sharp eyes.",
        "effects": {"girl_stress": 4, "xp": 5, "player_stress": 20},
    },
    {
        "id": "dream_pale_hand",
        "name": "The Polite Visitor",
        "category": "burden",
        "weight": 3,
        "once": False,
        "conditions": {"min_day": 2},
        "lines": [
            "A visitor in a coat the colour of old blood counts your coins",
            "while you watch. You cannot move. The counting is polite,",
            "almost apologetic, the way a tax collector is polite.",
            "You wake lighter by a little.",
        ],
        "journal": "A visitor counted your coins while you slept.",
        "effects": {"gold_loss": True},
    },
    {
        "id": "dream_ominous_doors",
        "name": "A Corridor of Doors",
        "category": "burden",
        "weight": 3,
        "once": False,
        "new_city_bonus": True,
        "conditions": {},
        "lines": [
            "A corridor of doors, each one a floor you have not opened yet.",
            "Behind one of them, something is already listening for your step.",
            "You wake with the shape of a warning and none of its details.",
        ],
        "journal": "You dreamed of doors you have not opened — something waited behind one.",
        "effects": {},
    },

    # ── Per-context dreams (Phase 4) — each tied to where you sleep ──────
    {
        "id": "dream_hearth_song",
        "name": "The Hearth's Song",
        "category": "boon",
        "weight": 3,
        "once": False,
        "conditions": {"location": ("home",)},
        "lines": [
            "The house is humming — the kettle, the beams, the small settling",
            "sounds that mean nothing is wrong anywhere tonight.",
            "You dream of a door you can lock, and a fire that is yours to keep.",
        ],
        "journal": "You dreamed of a quiet house and a fire that was yours to keep.",
        "effects": {"buff": {"type": "dream_blessed", "value": 1,
                             "rooms": 2, "target": "party"}},
    },
    {
        "id": "dream_home_remembers",
        "name": "The House Remembers",
        "category": "boon",
        "weight": 2,
        "once": True,
        "conditions": {"location": ("home",), "min_day": 4},
        "lines": [
            "The house dreams back at you: every room wearing the shape of",
            "someone who lives there, every scuff on the floor accounted for.",
            "It remembers boots by the door, and a name it does not speak.",
            "You wake as though the walls had been keeping a record.",
        ],
        "journal": "The house dreamed back at you and kept its own record of who lives there.",
        "effects": {"xp": 10},
    },
    {
        "id": "dream_road_patience",
        "name": "The Road's Patience",
        "category": "boon",
        "weight": 3,
        "once": False,
        "conditions": {"location": ("camp",)},
        "lines": [
            "A road unrolls under the stars and keeps unrolling, but you are",
            "not on it. You are sitting beside it, and the walking can wait.",
            "Somewhere a fire keeps itself going just for you.",
        ],
        "journal": "The road let you rest on the way to somewhere.",
        "effects": {"xp": 25},
    },
    {
        "id": "dream_rented_room",
        "name": "The Rented Room",
        "category": "burden",
        "weight": 3,
        "once": False,
        "conditions": {"location": ("inn",)},
        "lines": [
            "Footsteps pass your door in the night, stop, and do not move on.",
            "In a rented room you are a guest, and the hall is not yours to know.",
            "You wake with the sense of someone listening through the wall.",
        ],
        "journal": "Someone stood in the inn's hall and listened to you sleep.",
        "effects": {"girl_stress": 5},
    },

    # ── Choices (Phase 2) ────────────────────────────────────────────────
    {
        "id": "dream_offered_hand",
        "name": "The Offered Hand",
        "category": "choice",
        "weight": 3,
        "once": False,
        "conditions": {"min_day": 2},
        "lines": [
            "A hand comes out of the dark, palm up, patient as a held breath.",
            "It is not your hand. It is not anyone's.",
            "\"You only have to take it,\" says a voice that is almost yours.",
        ],
        "journal": "A hand out of the dark offered you its patience.",
        "prompt": "The hand waits. What do you do?",
        "prompts": [
            {
                "text": "Take the hand. (+10% damage, 2 rooms · +20 stress)",
                "reply": "You wake with your fingers closed around something "
                         "that isn't there — and your grip is stronger for it.",
                "effects": {
                    "buff": {"type": "damage_boost", "value": 0.10,
                             "rooms": 2, "target": "player"},
                    "player_stress": 20,
                },
            },
            {
                "text": "Refuse, and walk on. (+15 XP)",
                "reply": "The hand folds away without offence. You wake with "
                         "your own name clear in your mouth.",
                "effects": {"xp": 15},
            },
        ],
    },
    {
        "id": "dream_accord_echo",
        "name": "The Accord Echo",
        "category": "choice",
        "weight": 2,
        "once": True,
        "conditions": {"min_day": 5},
        "lines": [
            "A voice reads a clause you have never heard, and will not repeat.",
            "The words are patient, exact, and older than the town above you.",
            "Somewhere in the dark, a pen waits to see whether you agree.",
        ],
        "journal": "Something read the Accord aloud, and waited for your answer.",
        "prompt": "The clause hangs unfinished. What do you do?",
        "prompts": [
            {
                "text": "Listen to the whole clause. (+35 XP · +20 stress)",
                "reply": "You wake with a sentence you cannot place, and a "
                         "headache you can.",
                "effects": {"xp": 35, "player_stress": 20},
            },
            {
                "text": "Cover your ears and sleep. (Dream-Blessed, 1 room)",
                "reply": "The voice stops mid-clause. Sleep takes you back, "
                         "gentle as a hand on the forehead.",
                "effects": {
                    "buff": {"type": "dream_blessed", "value": 1,
                             "rooms": 1, "target": "party"},
                },
            },
        ],
    },
    {
        "id": "dream_mirror_self",
        "name": "The Mirror Self",
        "category": "choice",
        "weight": 3,
        "once": False,
        "conditions": {"min_day": 3},
        "lines": [
            "There is a door in the wall of sleep, and behind it, a mirror.",
            "Your reflection is doing something you have not done yet.",
            "It notices you noticing, and stops.",
        ],
        "journal": "Your reflection stopped doing what it was doing.",
        "prompt": "The reflection waits for you to move first.",
        "prompts": [
            {
                "text": "Hold its gaze. (+25 XP · +15 stress)",
                "reply": "It looks back until you understand which of you is "
                         "the copy. You wake first.",
                "effects": {"xp": 25, "player_stress": 15},
            },
            {
                "text": "Look away and wake. (+5% crit, 2 rooms)",
                "reply": "You wake before the mirror can answer. Your hands "
                         "are steady.",
                "effects": {
                    "buff": {"type": "crit_chance", "value": 0.05,
                             "rooms": 2, "target": "player"},
                },
            },
        ],
    },
    {
        "id": "dream_feast",
        "name": "The Feast",
        "category": "choice",
        "weight": 3,
        "once": False,
        "conditions": {"party_min": 1},
        "lines": [
            "A table you did not set is laid in the dark, and every dish is",
            "something you missed. Across from you, a chair is pulled out",
            "and left waiting.",
        ],
        "journal": "A table was laid in the dark, with a seat left open.",
        "prompt": "The food is warm. The chair is empty. What do you do?",
        "prompts": [
            {
                "text": "Eat your fill. (Dream-Blessed, 2 rooms)",
                "reply": "You wake full, for having eaten nothing.",
                "effects": {
                    "buff": {"type": "dream_blessed", "value": 1,
                             "rooms": 2, "target": "party"},
                },
            },
            {
                "text": "Save the seat for {girl}. (+3 affection)",
                "reply": "{girl} wakes in a better mood and cannot say why.",
                "effects": {"affection": 3},
            },
        ],
    },

    # ── Story beats (Phase 3) — queued, never rolled (§4.5) ─────────────
    {
        "id": "dream_first_shared_night",
        "name": "The First Night Not Alone",
        "category": "story",
        "weight": 1,
        "once": True,
        "content_level": "any",
        "conditions": {"flags": ["had_shared_night"]},
        "lines": [
            "The dream has no room in it — only warmth, and the sound of",
            "someone breathing who is not afraid of you.",
            "She is there, close enough that the dark cannot get between you.",
            "You do not speak. There is nothing that needs saying.",
            "The dream closes gently, the way a hand closes when it trusts",
            "what it is holding.",
            "You wake before the story goes any further.",
        ],
        "journal": "You dreamed of the first night you did not sleep alone.",
        "effects": {},
    },
    {
        "id": "dream_expectant_light",
        "name": "The Lamp in the Unbuilt Room",
        "category": "story",
        "weight": 1,
        "once": True,
        "family": True,
        "content_level": "any",
        "conditions": {"flags": ["family_expecting"]},
        "lines": [
            "A lamp burns in a room you have not built yet.",
            "Someone small is asleep in the light of it, and the dream will",
            "not show you their face — only the shape of their hand.",
            "You are not afraid. That is the strange part.",
            "The lamp keeps burning after you wake.",
        ],
        "journal": "You dreamed of a lamp burning for someone you have not met.",
        "effects": {},
    },
    {
        "id": "dream_voss_first_page",
        "name": "The Archive That Rains Upward",
        "category": "story",
        "weight": 1,
        "once": True,
        "conditions": {"flags": ["voss_epilogue_seen"]},
        "lines": [
            "A library with no ceiling, and rain falling upward past the shelves.",
            "Archivist Voss is writing at a desk made of the same rain.",
            "He does not look up. \"The first page is the hardest,\" he says.",
            "\"It was always yours. You only had to stop asking permission.\"",
            "Somewhere above the shelves, Lumen laughs — the way you laugh at",
            "a joke that has been waiting a very long time to be told.",
            "You wake with the smell of ink and nothing to show for it.",
        ],
        "journal": "Voss and Lumen found you in a dream, still keeping the Archive.",
        "flags_set": ["dreamed_of_voss"],
        "effects": {},
    },
    {
        "id": "dream_thirst_beneath",
        "name": "The Counting in the Walls",
        "category": "story",
        "weight": 1,
        "once": True,
        "conditions": {"party_race": "Vampire"},
        "lines": [
            "The dream is a hallway, and every door in it is warm to the touch.",
            "Something in the walls is counting your pulse — patiently, the way",
            "you would count coins you intend to spend.",
            "You know the count is not for your heart.",
            "You wake with your tongue against your teeth, and the taste of it",
            "is not your own.",
        ],
        "journal": "Something in the walls counted your heartbeat and knew your name.",
        "flags_set": ["dreamed_of_the_thirst"],
        "effects": {},
    },
]


# ── Lookup helpers (pure) ───────────────────────────────────────────────────

DREAMS_BY_ID = {dream["id"]: dream for dream in DREAMS}


def get_dream(dream_id):
    """Return a dream definition by id (None when unknown)."""
    return DREAMS_BY_ID.get(dream_id)


def _as_tuple(value):
    """Normalize a condition value that may be a string or an iterable."""
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    return tuple(value)


def dream_location_allowed(dream, location):
    """True when the dream may fire at ``location`` (home/inn/camp)."""
    allowed = _as_tuple((dream.get("conditions") or {}).get("location"))
    if not allowed:
        return True
    return location in allowed


def category_of(dream):
    """Return the dream's category (boon/burden/choice/story)."""
    return dream.get("category", "boon")
