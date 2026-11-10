"""House Stories ("Fireside Tales") — pure data definitions.

Design: docs/house_stories_design.md

Stories are read from the house menu ("Fireside Tales") once their
requirements are met. Each story is a multi-part arc; parts are read in
order and stay re-readable after completion. A part may carry a city
trigger (``"trigger": {"type": "city", "city": "skylume"}``) so some threads
find the player while travelling instead of waiting at home.

Schema
──────
HOUSE_STORIES[story_id] = {
    "title":   str,
    "summary": str,                       # one-line teaser
    "girl":    girl_key | None,           # featured girl (optional)
    "requires": {                         # arc-wide gate (parts add to it)
        "girls":       int,               # distinct owned girls at affection >= ...
        "affection":   int,               # ... this threshold (default 0)
        "girl":        girl_key,          # featured girl must be owned
        "girl_keys":   [girl_key, ...],   # designated allies that must be owned
        "married":     int,               # married companions required
        "house_level": int,               # highest owned house level
        "flags":       [flag, ...],       # quest flags required
        "superbosses": [boss_id, ...],    # superbosses that must be defeated
    },
    "parts": [
        {
            "id":       str,              # stable, never reuse
            "title":    str,
            "requires": {...},            # merged with the arc gate (max values)
            "trigger":  None | {"type": "city", "city": city_id | "any",
                                "phase": "morning"|"noon"|"night"},  # optional
            "lines":    [paragraph, ...], # "\\n" splits lines inside a paragraph
            "effects": {
                "affection":     int,     # featured girl / designated allies / all
                "affection_all": int,     # every qualifying girl
                "stress":        int,     # negative relaxes, same target as affection
                "gold":          int,
                "xp":            int,
                "items":         [{"id": item_id, "count": int}, ...],
            },
        },
    ],
}

Pure module: imports nothing from game systems, so it is safe to import
from facilities, GUI and tests.
"""

# ── Requirement helpers ──────────────────────────────────────────────────────

_NUMERIC_REQ_KEYS = ("girls", "affection", "married", "house_level")


def _as_list(value):
    """Normalize a requirement value that may be a string or a list."""
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    return list(value)


def ensure_state(player):
    """Initialize the house-story state block (old-save safe)."""
    state = player.setdefault("house_stories", {})
    state.setdefault("seen", {})       # part_id -> day first read
    return state


def get_story(story_id):
    return HOUSE_STORIES.get(story_id)


def iter_story_parts(story):
    """Yield (part_number, part) in reading order (1-based)."""
    for index, part in enumerate(story.get("parts", []), start=1):
        yield index, part


def get_part(part_id):
    """Return (story_id, story, part_number, part) or (None, None, 0, None)."""
    for story_id, story in HOUSE_STORIES.items():
        for number, part in iter_story_parts(story):
            if part.get("id") == part_id:
                return story_id, story, number, part
    return None, None, 0, None


def merge_requirements(story, part):
    """Combine an arc gate with a part gate (the stricter value wins)."""
    arc = story.get("requires") or {}
    own = part.get("requires") or {}
    merged = {}
    for key in _NUMERIC_REQ_KEYS:
        values = [int(v) for v in (arc.get(key), own.get(key)) if v is not None]
        if values:
            merged[key] = max(values)
    flags = []
    for source in (arc, own):
        for flag in source.get("flags") or []:
            if flag not in flags:
                flags.append(flag)
    if flags:
        merged["flags"] = flags

    girl_keys = []
    for source in (story, arc, own):
        for key in _as_list(source.get("girl_keys")):
            if key not in girl_keys:
                girl_keys.append(key)
    if girl_keys:
        merged["girl_keys"] = girl_keys

    superbosses = []
    for source in (arc, own):
        for boss in _as_list(source.get("superbosses")):
            if boss not in superbosses:
                superbosses.append(boss)
    if superbosses:
        merged["superbosses"] = superbosses

    featured = own.get("girl") or arc.get("girl") or story.get("girl")
    if featured:
        merged["girl"] = featured
        if featured not in girl_keys:
            girl_keys.insert(0, featured)
            merged["girl_keys"] = girl_keys
    return merged


def requirement_labels(req):
    """Human-readable requirement lines (no progress numbers)."""
    lines = []
    girls = int(req.get("girls", 0) or 0)
    affection = int(req.get("affection", 0) or 0)
    if girls and affection:
        lines.append(f"{girls} companions at {affection}+ affection")
    elif girls:
        lines.append(f"{girls} companions in your household")
    elif affection:
        lines.append(f"{affection}+ affection")
    if req.get("girl"):
        lines.append(f"{req['girl'].replace('_', ' ').title()} in your household")
    for key in _as_list(req.get("girl_keys")):
        if key == req.get("girl"):
            continue
        lines.append(f"{key.replace('_', ' ').title()} in your household")
    if req.get("married"):
        count = int(req["married"])
        lines.append("a married companion" if count == 1 else f"{count} married companions")
    if req.get("house_level"):
        lines.append(f"house level {int(req['house_level'])}+")
    for flag in req.get("flags") or []:
        lines.append(FLAG_LABELS.get(flag, flag.replace("_", " ")))
    for boss in _as_list(req.get("superbosses")):
        lines.append(f"having defeated {SUPERBOSS_LABELS.get(boss, boss.replace('_', ' '))}")
    return lines


# Quest flags -> player-facing requirement text.
FLAG_LABELS = {
    "met_voss": "having met Archivist Voss (Star Tower)",
    "intro_seen": "having received the Archivist's summons",
}


# Superboss ids -> player-facing names (story gates).
SUPERBOSS_LABELS = {
    "chromatic_artisan": "Palette, the Chromatic Artisan",
    "white_knight": "the White Knight of the Fallen Empire",
    "entangled_chrysalis": "the Entangled Chrysalis",
    "broodmother_vileheart": "the Broodmother",
    "dream_devouring_slitcurrent": "Slitcurrent",
    "queen_of_mirrors_sylvana": "Sylvana, Queen of Mirrors",
    "melt_forge_golem_ignis": "Ignis, the Melt-Forge Golem",
    "heaven_banished_dragon_yinglong": "Yinglong",
    "rientrante_frostbound": "Rientrante",
    "captain_everlong_ship": "the Everlong",
    "black_silence": "the Black Silence",
    "wl_queen_of_hearts": "the Queen of Hearts",
    "wl_big_bad_wolf": "the Big Bad Wolf",
    "wl_wicked_witch": "the Wicked Witch of the West",
    "wl_jabberwock": "the Jabberwock",
    "wl_mary_sue": "Mary Sue",
}


# ── Story content ────────────────────────────────────────────────────────────
# Tokens: {girl} = featured/first qualifying girl, {girls} = the household,
#         {player} = player name, {home} = house name.

HOUSE_STORIES = {

    # ── Goblin Girl romance arc ──────────────────────────────────────────────
    "lucky_coin": {
        "title": "The Lucky Coin",
        "summary": "A goblin, a coin, and the difference between luck and choice.",
        "girl": "goblin_girl",
        "requires": {"girl": "goblin_girl"},
        "parts": [
            {
                "id": "lucky_coin_1",
                "title": "Two Sides",
                "requires": {"affection": 30},
                "lines": [
                    "The Goblin Girl is on the lounge floor with her lucky coin,\n"
                    "polishing it against her sleeve in slow, even strokes. She\n"
                    "doesn't hear you come in.",
                    '"Oh — hi." She cups the coin. "I was just... thinking. Do you\n'
                    'believe in luck?"',
                    "You answer. She listens with her whole body, ears tipping\n"
                    "toward you like a pair of small flags.",
                    '"I used to think luck was all I had," she says. "Every dart I\n'
                    'threw, every coin I flipped, I was begging the world to be\n'
                    'kind. Then you caught me — and I thought, great, more luck."',
                    "She turns the coin over. Heads. Tails.\n"
                    '"But you keep coming back. That\'s not luck. That\'s a choice."',
                    "She holds the coin out to you, then pulls it back at the last\n"
                    'second, grinning. "Heads, I ask you a favor. Tails, you ask me\n'
                    'one. Deal?"',
                    "It comes up tails. She leans in, suddenly serious.\n"
                    '"Ask me to stay. Not as a favor — just... ask."',
                    "You ask. She tucks the coin away, and for once the lucky one\n"
                    "looks like she got exactly what she wanted.",
                ],
                "effects": {"affection": 3, "xp": 10, "stress": -3},
            },
            {
                "id": "lucky_coin_2",
                "title": "Heads, You Win",
                "requires": {"affection": 60},
                "lines": [
                    "The lounge fire has burned down to embers when the Goblin\n"
                    "Girl drops onto the cushion beside you, coin already balanced\n"
                    "on her thumb.",
                    '"Game tonight. Heads, you answer. Tails, I answer. No\n'
                    'skipping."',
                    'She flips. Heads.\n"Why do you keep going into the deep floors?\n'
                    'You already have enough gold to stop."',
                    "You tell her the truth — or something close to it.",
                    "Tails, she answers one of yours.\n"
                    '"What\'s your wish? The real one. Not the one you say out\n'
                    'loud."',
                    "She looks at the coin for a long time.\n"
                    '"I used to wish to be lucky. Now I wish for this. The fire.\n'
                    'The quiet. You, looking at me like I\'m not a monster you\n'
                    'found in a dungeon."',
                    "The coin stills. She doesn't flip again.\n"
                    '"That\'s not a wish you need luck for," she says, very softly.\n'
                    '"It\'s one you need to keep."',
                ],
                "effects": {"affection": 4, "xp": 20, "stress": -5},
            },
            {
                "id": "lucky_coin_3",
                "title": "The Wish That Landed",
                "requires": {"affection": 90},
                "lines": [
                    "She finds you at the window after midnight, coin held flat in\n"
                    "her palm. The moon makes the copper look like gold.",
                    '"I figured it out," she says. "The coin was never lucky. I\n'
                    'just kept throwing it until I got brave enough to want\n'
                    'something."',
                    "She presses it into your hand and closes your fingers over\n"
                    'it. "So I\'m not asking the coin anymore. I\'m asking you."',
                    '"Keep me. Not because I\'m useful or because I hit things\n'
                    'good. Because when you\'re home, the whole house feels like\n'
                    'the wish landed."',
                    "Her ears go red. She lifts her chin anyway, meeting your\n"
                    'eyes. "...That was a lot. I know. You can say something now."',
                    "You take her hand — the empty one, the one without the coin\n"
                    "in it. She laughs, wobbly and bright, and leans her forehead\n"
                    "against your shoulder like she's been waiting her whole life\n"
                    "for somewhere to rest.",
                    "The coin stays warm in your pocket. On the hearth, unnoticed,\n"
                    "a single ember pops and settles. Luck, it turns out, was just\n"
                    "choice in disguise.",
                ],
                "effects": {"affection": 6, "xp": 30, "stress": -8},
            },
        ],
    },

    # ── Ensemble household arc ───────────────────────────────────────────────
    "small_hours": {
        "title": "Small Hours",
        "summary": "A storm, an empty chair, and the names a house remembers.",
        "requires": {"girls": 3, "affection": 40, "house_level": 2},
        "parts": [
            {
                "id": "small_hours_1",
                "title": "The Storm",
                "lines": [
                    "The storm hits after dark. Wind shoulders the shutters; rain\n"
                    "finds three ways through the roof.",
                    "By the fire, the household has gathered without being asked:\n"
                    "{girls}.",
                    "Somebody drags a mattress into the lounge. Somebody else\n"
                    "declares it a fort. The declaration is accepted by\n"
                    "acclamation.",
                    '"Story first," says one. "Then cards. Then somebody has to\n'
                    'check the roof."\n"Not it." "Not it." "...Not it."',
                    "You listen to them argue about whose turn it is to tell the\n"
                    "first story and realize you've stopped thinking of this place\n"
                    "as a building.",
                    "When the fire burns low, nobody moves to leave. The storm can\n"
                    "take its time. The house is warm, and the house is loud, and\n"
                    "the house is yours.",
                ],
                "effects": {"affection_all": 1, "xp": 15, "stress": -3},
            },
            {
                "id": "small_hours_2",
                "title": "The Empty Chair",
                "requires": {"girls": 4, "affection": 50},
                "lines": [
                    "There's a chair by the window that nobody uses. You've never\n"
                    "asked why.",
                    "Tonight one of the girls catches you looking at it.\n"
                    '"We keep it for the next one," she says. "New girls get a\n'
                    'chair before they get a name. Makes the house feel less like\n'
                    'a cage."',
                    'The others drift over. {girls}.\n"When I got here I thought it\n'
                    'was a trap," one admits. "A nice trap. The kind with soup."',
                    '"Soup is how they get you," says another, deadpan.\nThe room\n'
                    "dissolves into laughter.",
                    "The empty chair doesn't feel like an absence anymore. It feels\n"
                    "like patience — a place set at the table for someone not home\n"
                    "yet.",
                    "You pull an extra stool from the corner and set it beside the\n"
                    "chair. Nobody says anything. Everybody notices.",
                ],
                "effects": {"affection_all": 1, "xp": 20, "stress": -3},
            },
            {
                "id": "small_hours_3",
                "title": "Names on the Mantel",
                "requires": {"girls": 5, "affection": 60, "house_level": 3},
                "lines": [
                    "You find them at the mantel with a knife and a piece of\n"
                    "charcoal, arguing about handwriting.",
                    '"The house should remember," one of them says. "Every house I\n'
                    'lived in before forgot me the day I left. This one\'s going to\n'
                    'be different."',
                    "One by one, they carve their names into the wood — crooked,\n"
                    "bold, bordered with little hearts nobody will admit to\n"
                    "drawing.",
                    "There's a gap left in the middle. They look at you.\n"
                    '"It\'s your house too," says {girl}. "Sign it."',
                    "You carve your name among theirs. The mantel looks like the\n"
                    "cover of a book nobody planned to write, and everybody did.",
                    "The fire catches. The names glow faintly, the way names do in\n"
                    "a house that has decided to keep them.",
                ],
                "effects": {"affection_all": 2, "xp": 30, "gold": 25, "stress": -5},
            },
        ],
    },

    # ── Star Tower / Lumen lore arc (city-triggered start) ───────────────────
    "moth_at_the_window": {
        "title": "A Moth at the Window",
        "summary": "The Archive has studied bonds. It has never studied a home.",
        "requires": {"girls": 2, "affection": 40, "flags": ["met_voss"]},
        "parts": [
            {
                "id": "moth_window_1",
                "title": "The Letter",
                "trigger": {"type": "city", "city": "skylume"},
                "lines": [
                    "You're crossing a Skylume bridge when something small and\n"
                    "bright bumps against your shoulder, circles twice, and lands\n"
                    "on your hand.",
                    "A star-moth. It carries a scrap of Archive paper, folded to\n"
                    "the size of a thumbnail in tiny, careful folds.",
                    '"To the household," the letter reads. "The Archive has never\n'
                    'studied a home from the inside. Would you permit a visit? We\n'
                    'will bring tea. — L."',
                    'Below that, in much smaller writing: "He means Voss. I want\n'
                    'to see the lounge. Please say yes. — Lumen."',
                    "The moth lifts off, waits for you to follow, and then dives\n"
                    "into your sleeve to nap, apparently confident in your answer.",
                    "You have a letter to take home. That's a strange sentence to\n"
                    "think, and a good one.",
                ],
                "effects": {"affection_all": 1, "xp": 15},
            },
            {
                "id": "moth_window_2",
                "title": "Tea with the Archive",
                "requires": {"affection": 45},
                "lines": [
                    "Lumen arrives first, a lantern of moths fanning out ahead of\n"
                    "her like an honor guard. She is small, luminous, and utterly\n"
                    "unafraid of the lounge.",
                    "Voss follows with a crate of ledgers, a tea set, and the\n"
                    "expression of a man who has been told to enjoy himself.",
                    '"We brought three kinds of tea," he says. "I was advised —\n'
                    'strongly — that one tea was insufficient."',
                    "The house girls have arranged themselves in a line, trying to\n"
                    "look casual. Lumen lands on the arm of the sofa and begins\n"
                    "asking questions like a professional.",
                    '"When did this stop being a place you were kept and start\n'
                    'being a place you chose?"',
                    "The answers surprise everyone, most of all the girls\n"
                    "answering. Voss writes very fast. Lumen listens with her wings\n"
                    "folded still.",
                    '"I find," Voss says, quietly, "that the Archive has recorded a\n'
                    'great many bonds. It has recorded very few homes." He closes\n'
                    'the ledger. "This, I think, is a home."',
                ],
                "effects": {"affection_all": 1, "xp": 25, "stress": -4},
            },
            {
                "id": "moth_window_3",
                "title": "A Thread in the Ledger",
                "requires": {"girls": 3, "affection": 50},
                "lines": [
                    "The letter comes a week later, delivered by three moths in\n"
                    "formation.",
                    '"The reading came back inconclusive," Voss writes. "Not\n'
                    'because the resonance is weak. Because it has no single\n'
                    'source. It rises from the house itself."',
                    '"I have never recorded anything like it. The Archive\'s theory\n'
                    'holds that bonds live in people. I am beginning to suspect\n'
                    'that they also live in walls that hold the people."',
                    "At the bottom, in a different hand:\n"
                    '"He\'s been pacing. I told him to say it simpler. What he\n'
                    'means is: your house is a new page. Take care of it. — Lumen."',
                    "You read it aloud in the lounge. The girls get quiet in the\n"
                    "way people do when they're being told something they already\n"
                    "knew.",
                    '"Then we should keep writing," someone says. "The page, I\n'
                    'mean."\nAnd the whole room agrees, loudly, all at once.',
                ],
                "effects": {"affection_all": 2, "xp": 40, "gold": 30, "stress": -5},
            },
        ],
    },

    # ── Harpy Scout romance arc ──────────────────────────────────────────────
    "harpy_sky": {
        "title": "Wind at the Window",
        "summary": "A scout with no nest learns what it means to land.",
        "girl": "harpy_scout",
        "requires": {"girl": "harpy_scout"},
        "parts": [
            {
                "id": "harpy_sky_1",
                "title": "Groundbound",
                "requires": {"affection": 40},
                "lines": [
                    "The Harpy Scout has been sleeping on the roof. You know\n"
                    "because you can hear her wings shift against the tiles every\n"
                    "time the wind changes.",
                    "Tonight it rains. She comes in soaked, pretending she wasn't\n"
                    "out there at all.",
                    '"A nest is just a place you leave," she says. "Scouts don\'t—"\n'
                    "She stops. The sentence goes somewhere she doesn't follow.",
                    "You build a perch by the window: a shelf, a blanket, a rope.\n"
                    "She watches the whole time with the flat suspicion of a bird\n"
                    "deciding whether a branch will hold.",
                    "When you finish, she tests it with one foot, then the other,\n"
                    "then folds herself into it all at once. \"...It's the right\n"
                    'height," she says, as if that explains everything.',
                    'From the doorway, you hear her add, very quietly:\n"For thermals. Obviously."',
                ],
                "effects": {"affection": 3, "xp": 12, "stress": -4},
            },
            {
                "id": "harpy_sky_2",
                "title": "The High Road",
                "requires": {"affection": 70},
                "lines": [
                    'She wakes you before dawn with a wing in your face. "Up.\n'
                    'You\'re coming."',
                    "On the roof, the city is still grey and the sky is doing\n"
                    "something complicated with pink. She hooks her arms under\n"
                    "yours and jumps.",
                    "For one terrible second the ground is a wall. Then the wind\n"
                    "takes you both and the wall becomes a map — streets, roofs,\n"
                    "chimneys, the river like a dropped ribbon.",
                    '"This is what I see," she says against your ear. "All the\n'
                    "time. I used to think it made me lucky. Then I thought it\n"
                    'made me lonely."',
                    'She lands on a chimney pot and doesn\'t let go. "Now it\'s\n'
                    'just... ours. The view. The sky. This."',
                    "The sun clears the rooftops. She looks at you instead of it.",
                ],
                "effects": {"affection": 5, "xp": 25, "stress": -6},
            },
        ],
    },

    # ── Harpy + Centaur pair arc (designated allies) ─────────────────────────
    "two_of_a_kind": {
        "title": "Hoof and Wing",
        "summary": "Two scouts, two horizons, one finish line.",
        "requires": {"girl_keys": ["harpy_scout", "centaur_scout"], "affection": 50},
        "parts": [
            {
                "id": "two_of_a_kind_1",
                "title": "The Race",
                "requires": {"affection": 50},
                "lines": [
                    "It starts as an argument about speed and becomes a race\n"
                    "before anyone agrees to it.",
                    "The Harpy Scout takes the rooftops; the Centaur Scout takes\n"
                    "the streets. You are the finish line, standing in the\n"
                    "courtyard with a borrowed scarf.",
                    "They arrive at the same moment from opposite directions,\n"
                    "both claiming victory, both out of breath, both grinning.",
                    '"Best two out of three," says the harpy. "Different route,"\n'
                    'says the centaur.',
                    "You point out that nobody actually raced. They were both\n"
                    "showing off.",
                    "The room laughs. Something tight in the pair eases, and\n"
                    "neither of them notices the other looking relieved.",
                ],
                "effects": {"affection": 2, "xp": 15, "stress": -3},
            },
            {
                "id": "two_of_a_kind_2",
                "title": "Two Kinds of Horizon",
                "requires": {"affection": 70},
                "lines": [
                    "They ask you to walk with them — both of them, at once,\n"
                    "which is its own kind of declaration.",
                    "The harpy talks about thermals; the centaur talks about\n"
                    "roads. They interrupt each other, apologize, then do it\n"
                    "again.",
                    '"I thought you\'d hate the sky," the harpy says. "I thought\n'
                    'you\'d hate being watched from it," the centaur answers.',
                    "They walk in silence for a while. The city goes on around\n"
                    "them.",
                    '"We could share a watch," says the Centaur Scout. "Ground\n'
                    'and air. Like a real patrol." The Harpy Scout pretends to\n'
                    "consider it for exactly one second.",
                    "Later, you find them asleep in the lounge — wings folded\n"
                    "over a blanket, hooves propped on a cushion, absolutely\n"
                    "refusing to be the first to accept the other's route.",
                ],
                "effects": {"affection": 4, "xp": 25, "stress": -4},
            },
        ],
    },

    # ── Slime Girl romance arc ──────────────────────────────────────────────
    "mirror_slime": {
        "title": "A Shape of Her Own",
        "summary": "A slime who learned to be everyone, until she chose herself.",
        "girl": "slime_girl",
        "requires": {"girl": "slime_girl"},
        "parts": [
            {
                "id": "mirror_slime_1",
                "title": "Reflections",
                "requires": {"affection": 35},
                "lines": [
                    "You catch the Slime Girl in the hallway, practicing your\n"
                    "posture. She goes ripple-still when she sees you.",
                    '"I was just..." Her shape wavers. "You walk like you know\n'
                    'where you\'re going."',
                    "She admits she copies people — the way they laugh, the way\n"
                    "they cross their arms — because a slime with no shape is\n"
                    "only a puddle with opinions.",
                    "You tell her she doesn't have to be a reflection. She\n"
                    "listens the way a mirror can't: with her whole body,\n"
                    "leaning toward the words.",
                    '"But what would I be instead?" she asks. "If I stopped\n'
                    'being everyone else."',
                    "You don't answer for her. You tell her you'll wait while\n"
                    "she figures it out.",
                ],
                "effects": {"affection": 3, "xp": 12, "stress": -4},
            },
            {
                "id": "mirror_slime_2",
                "title": "Her Own Shape",
                "requires": {"affection": 65},
                "lines": [
                    "She asks you to close your eyes. There's a wet, thoughtful\n"
                    "sound, then nothing.",
                    '"Okay." Her voice is nervous. "Look."',
                    "She has chosen a shape: small, bright, entirely her own —\n"
                    "a little taller than before, shoulders squared, hair like a\n"
                    "held wave. She is blushing in three colors.",
                    '"I picked it from parts I liked," she says. "Nothing copied.\n'
                    'Just... me. Do you like it?"',
                    "You tell her the truth. She blinks hard, then grins with a\n"
                    "mouth that is finally hers, and the whole room seems to\n"
                    "settle around her.",
                    "Later, she makes a point of walking beside you instead of\n"
                    "behind — same pace, different paths, her shape holding\n"
                    "steady.",
                ],
                "effects": {"affection": 5, "xp": 25, "stress": -6},
            },
        ],
    },

    # ── Palette arc — unlocked by the Chromatic Artisan superboss ───────────
    "palette_afterimage": {
        "title": "The Eighth Color",
        "summary": "After the Artisan falls, the house keeps painting.",
        "requires": {"superbosses": ["chromatic_artisan"], "house_level": 2},
        "parts": [
            {
                "id": "palette_afterimage_1",
                "title": "The Unfinished Wall",
                "lines": [
                    "The blank canvas came home with you. So did the brush — or\n"
                    "maybe they followed, the way paint follows a hand.",
                    "There's a wall in the lounge that has never held a picture.\n"
                    "Tonight it looks unfinished in a way you can't explain.",
                    "You set the canvas against it. The house settles. Somewhere\n"
                    "in the walls, a sound like a brush being cleaned.",
                    "The brush rests against the canvas. By morning it has not\n"
                    "moved, but the wall looks less empty.",
                    "You leave it as it is. Some paintings need a second sitting.",
                ],
                "effects": {"affection_all": 1, "xp": 20, "stress": -2},
            },
            {
                "id": "palette_afterimage_2",
                "title": "Seven Colours",
                "requires": {"girl_keys": ["wonderland_palette"], "affection": 60},
                "lines": [
                    "Palette paints the wall. It takes three days and no time at\n"
                    "all.",
                    "The house girls drift in to watch: a stroke of impossible\n"
                    "green, a sky that remembered being a river, a window that\n"
                    "opens onto somewhere nobody has been.",
                    "Palette talks while they work — about canvases, about being\n"
                    "seen, about the difference between a masterpiece and a home.",
                    '"A masterpiece is finished," they say. "A home is allowed\n'
                    'to have wet paint."',
                    "One of the girls puts a mug of tea on the drop cloth.\n"
                    "Palette stares at it like it's the first gift they've ever\n"
                    "been given.",
                    "That night, the wall is still wet. Nobody minds.",
                ],
                "effects": {"affection": 3, "xp": 35, "stress": -5},
            },
            {
                "id": "palette_afterimage_3",
                "title": "The Eighth Colour",
                "requires": {"girl_keys": ["wonderland_palette"], "affection": 100},
                "lines": [
                    "Palette finds you at the wall after midnight. The painting\n"
                    "has dried into something that looks different every time\n"
                    "you don't look at it.",
                    '"I keep trying to name the last color," they say. "It\'s not\n'
                    "on any wheel. It only shows up when you're standing there.\"",
                    "They hold up a small canvas: the house at dusk, the window\n"
                    "lit, a figure in the doorway that is unmistakably you.",
                    '"I don\'t know what to call it," they admit. "The color.\n'
                    'The feeling. This."',
                    "You tell them they don't have to name it. They can just\n"
                    "keep painting it.",
                    "Palette laughs — sudden and bright — and for the first time,\n"
                    "the Artisan's hands are perfectly steady. \"Then I'll paint\n"
                    'it every day," they say. "If that\'s allowed."',
                ],
                "effects": {"affection": 5, "xp": 40, "stress": -8},
            },
        ],
    },

    # ── White Knight arc — unlocked by the F40 superboss ────────────────────
    "oath_after": {
        "title": "The Last Oath",
        "summary": "A shield nobody claimed, and a promise the house keeps.",
        "requires": {"superbosses": ["white_knight"], "girls": 2, "affection": 40},
        "parts": [
            {
                "id": "oath_after_1",
                "title": "A Shield at the Door",
                "lines": [
                    "The shield is waiting on the doorstep when you come home:\n"
                    "white porcelain, a hairline crack down the center, too heavy\n"
                    "for any courier to have carried alone.",
                    'There\'s a note tied to the grip. "An oath kept is a door\n'
                    'left open. Keep it." No signature. The handwriting is very\n'
                    "old.",
                    "The house girls gather around it. Nobody wants to be the\n"
                    "first to touch it.",
                    '"It\'s not a trophy," one of them says. "It\'s a promise\n'
                    'someone didn\'t break."',
                    "You hang it over the door. It fits as if the wall was built\n"
                    "for it.",
                    "That night, the house feels a little more defended than it\n"
                    "was.",
                ],
                "effects": {"affection_all": 1, "xp": 20},
            },
            {
                "id": "oath_after_2",
                "title": "The Watch",
                "requires": {"girls": 3, "affection": 50},
                "lines": [
                    "The shield has become part of the furniture. The girls take\n"
                    "turns polishing it, which mostly means arguing about the\n"
                    "right cloth.",
                    '"A watch is just a promise with a schedule," says one.',
                    '"Then we should schedule it," says another. "Rota. On the\n'
                    'mantel. No skipping."',
                    "They make a rota. It is wildly impractical and everyone\n"
                    "signs it.",
                    "When your turn comes, you find the rota has been amended:\n"
                    "your name appears three times more than anyone else's.",
                    "You look up to find several girls pretending very hard to\n"
                    "be busy.",
                ],
                "effects": {"affection_all": 1, "xp": 25, "stress": -4},
            },
        ],
    },
}
