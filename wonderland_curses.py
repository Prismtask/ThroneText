# wonderland_curses.py — Whimsical floor blessings & quirks for Wonderland
"""
Wonderland Curse System
───────────────────────
Each floor in Wonderland rolls a random "quirk" — a whimsical, mostly-beneficial
twist that persists for the entire floor. Unlike Pandemonium's punishing curses,
Wonderland's effects are playful and often helpful, reflecting the realm's
chaotic-but-not-malevolent nature.

Quirk Tiers (based on floor depth):
  Tier 1 — Floors  1–10 — 1.0× base effect (gentle whimsy)
  Tier 2 — Floors 11–20 — 1.3× base effect (growing curious)
  Tier 3 — Floors 21–30 — 1.6× base effect (quite mad)
  Tier 4 — Floors 31–50 — 2.0× base effect (truly wonderland)

Wonderland Shadows (Floor 40+):
  At Floor 40, the player must choose 1 "Shadow" — a persistent negative effect
  that lingers across all subsequent floors. At Floor 46, the list refreshes
  and the player must choose a 2nd Shadow. These accumulated Shadows alter
  Mary Sue's behavior on Floor 50, granting her unique passives based on which
  Shadows the player carries.

Shadow effect types:
  authors_will       — Mary Sue's narrative influence seeps through
  off_with_heads     — The Queen's temper turns on you
  down_rabbit_hole   — Reality distorts unpredictably
  jabberwock_wrath   — The Jabberwock's spirit is angered
  madness_contagion  — The Hatter's madness is infectious
  looking_glass_shatter — The mirror cracks
  caterpillars_smoke — Disorienting smoke
  rose_wilt          — The roses die
  white_rabbit_panic — Time pressure intensifies
  cheshire_absence   — The Cat abandons you
"""

import random

# ═══════════════════════════════════════════════════════════════════════════════
# WONDERLAND QUIRK DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════════

WONDERLAND_QUIRKS = [
    {
        "key": "curiosity_boost",
        "name": "Curiouser and Curiouser",
        "desc": "The very air of Wonderland makes you feel... different. Stronger? Smarter? Who knows!",
        "desc_full": "At the start of each room, a random party member gains +{val} to a random stat for the room.",
        "effect": "curiosity_boost",
        "base_value": 3,
        "icon": "🍄",
    },
    {
        "key": "tea_party_regen",
        "name": "The Mad Hatter's Tea Party",
        "desc": "A phantom tea set appears after each battle, offering warm cups to the weary.",
        "desc_full": "Post-combat healing is increased by {pct}%.",
        "effect": "tea_party_regen",
        "base_value": 0.50,
        "icon": "🫖",
    },
    {
        "key": "cheshire_dodge",
        "name": "The Cheshire Cat's Favor",
        "desc": "A disembodied grin flits around you. Sometimes it confuses your enemies.",
        "desc_full": "Enemies have a {pct}% chance to miss their attacks entirely.",
        "effect": "cheshire_dodge",
        "base_value": 0.10,
        "icon": "😸",
    },
    {
        "key": "queens_decree",
        "name": "The Queen's Decree",
        "desc": "'Off with their... purses!' The Queen's card soldiers leave extra coin behind.",
        "desc_full": "Gold drops are increased by {pct}%.",
        "effect": "queens_decree",
        "base_value": 0.40,
        "icon": "👑",
    },
    {
        "key": "white_rabbit_haste",
        "name": "White Rabbit's Haste",
        "desc": "'I'm late, I'm late!' The White Rabbit scurries past, and time itself quickens.",
        "desc_full": "All skill cooldowns are reduced by {val} turn(s).",
        "effect": "white_rabbit_haste",
        "base_value": 1,
        "icon": "🐇",
    },
    {
        "key": "caterpillars_insight",
        "name": "Caterpillar's Insight",
        "desc": "'Who... are... YOU?' The Caterpillar's smoke clears your mind.",
        "desc_full": "All stat check DCs are reduced by {val}.",
        "effect": "caterpillars_insight",
        "base_value": 2,
        "icon": "🐛",
    },
    {
        "key": "jabberwock_bane",
        "name": "Jabberwock's Bane",
        "desc": "The vorpal blade's echo hums in your hands. Boss-type enemies tremble.",
        "desc_full": "You and allies deal {pct}% more damage to boss enemies.",
        "effect": "jabberwock_bane",
        "base_value": 0.15,
        "icon": "⚔️",
    },
    {
        "key": "mad_hatter_gift",
        "name": "Mad Hatter's Generosity",
        "desc": "A most un-birthday gift! The Hatter leaves trinkets scattered about.",
        "desc_full": "{pct}% chance for an extra item drop after each combat.",
        "effect": "mad_hatter_gift",
        "base_value": 0.20,
        "icon": "🎁",
    },
    {
        "key": "painting_roses",
        "name": "Painting the Roses Red",
        "desc": "Card soldiers frantically repaint the scenery — even your wounds seem less lasting.",
        "desc_full": "Bleed and poison durations are reduced by {val} turn(s).",
        "effect": "painting_roses",
        "base_value": 1,
        "icon": "🌹",
    },
    {
        "key": "looking_glass_luck",
        "name": "Through the Looking Glass",
        "desc": "Reality ripples like a mirror. What was once bad is now... good?",
        "desc_full": "{pct}% chance for any failed d20 roll to be re-rolled once.",
        "effect": "looking_glass_luck",
        "base_value": 0.12,
        "icon": "🪞",
    },
]

# ═══════════════════════════════════════════════════════════════════════════════
# WONDERLAND SHADOWS — Negative persistent effects (Floor 40+)
# ═══════════════════════════════════════════════════════════════════════════════
# At Floor 40 the player must choose 1 Shadow. At Floor 46 the list refreshes
# and the player must choose a 2nd. These persist on all subsequent floors.
# On Floor 50, each Shadow grants Mary Sue a unique passive buff.

WONDERLAND_SHADOWS = [
    {
        "key": "authors_will",
        "name": "Author's Will",
        "desc": "Mary Sue's pen scratches in the distance. Your story is no longer your own.",
        "desc_full": "All stat checks have their DC increased by {val}. The author is watching.",
        "effect": "authors_will",
        "base_value": 3,
        "icon": "📖",
        # ── Mary Sue Floor 50 passive ──
        "mary_sue_passive": {
            "name": "Plot Armor Reinforcement",
            "desc": "Mary Sue's Plot Armor starts with +2 extra stacks (7 total) and regenerates +1 per turn in ALL phases.",
            "effect": "extra_plot_armor",
        },
    },
    {
        "key": "off_with_heads",
        "name": "Off With Their Heads",
        "desc": "The Queen of Hearts' fury follows you. Her card soldiers strike with deadly precision.",
        "desc_full": "All enemies deal {pct}% more damage.",
        "effect": "off_with_heads",
        "base_value": 0.15,
        "icon": "🪓",
        "mary_sue_passive": {
            "name": "Queen's Execution",
            "desc": "When any party member falls below 30% HP, Mary Sue gains an immediate bonus attack against them.",
            "effect": "execution_threshold",
        },
    },
    {
        "key": "down_rabbit_hole",
        "name": "Down the Rabbit Hole",
        "desc": "The ground shifts beneath you. Reality frays at the edges. Which way is up?",
        "desc_full": "{pct}% chance for you or an ally to lose a turn each round.",
        "effect": "down_rabbit_hole",
        "base_value": 0.10,
        "icon": "🕳️",
        "mary_sue_passive": {
            "name": "Reality Warp",
            "desc": "Mary Sue can swap positions with a shadow minion or force a party member to the back row each turn.",
            "effect": "reality_warp",
        },
    },
    {
        "key": "jabberwock_wrath",
        "name": "Jabberwock's Wrath",
        "desc": "The slain Jabberwock's spirit burns with undying rage. Its flames seek you still.",
        "desc_full": "Take {val} fire damage at the start of every room.",
        "effect": "jabberwock_wrath",
        "base_value": 8,
        "icon": "🔥",
        "mary_sue_passive": {
            "name": "Vorpal Resistance",
            "desc": "Mary Sue takes 40% reduced damage from all physical attacks.",
            "effect": "vorpal_resistance",
        },
    },
    {
        "key": "madness_contagion",
        "name": "Madness Contagion",
        "desc": "The Hatter's madness spreads like spilled tea. Your thoughts tangle and twist.",
        "desc_full": "At the start of each room, a random party member loses {val} from a random stat for the room.",
        "effect": "madness_contagion",
        "base_value": 3,
        "icon": "🎭",
        "mary_sue_passive": {
            "name": "Maddening Aura",
            "desc": "At the start of each round, one random party member has a 50% chance to be Confused (targets random enemy).",
            "effect": "maddening_aura",
        },
    },
    {
        "key": "looking_glass_shatter",
        "name": "Looking Glass Shatter",
        "desc": "The mirror cracks. Seven years of bad luck settle over you like a shroud.",
        "desc_full": "All healing effects are reduced by {pct}%.",
        "effect": "looking_glass_shatter",
        "base_value": 0.35,
        "icon": "💔",
        "mary_sue_passive": {
            "name": "Shattered Reflection",
            "desc": "Mary Sue reflects 25% of all damage she takes back at the attacker.",
            "effect": "damage_reflect",
        },
    },
    {
        "key": "caterpillars_smoke",
        "name": "Caterpillar's Smoke",
        "desc": "The Caterpillar's hookah smoke thickens. Your vision blurs and strikes go wide.",
        "desc_full": "All attacks have {pct}% reduced accuracy.",
        "effect": "caterpillars_smoke",
        "base_value": 0.15,
        "icon": "💨",
        "mary_sue_passive": {
            "name": "Obscuring Smoke",
            "desc": "At the start of each round, all party members suffer -15% accuracy for that round.",
            "effect": "smoke_accuracy_debuff",
        },
    },
    {
        "key": "rose_wilt",
        "name": "Rose Wilt",
        "desc": "The roses die on their stems. Their thorns grow sharper and more numerous.",
        "desc_full": "Bleed and poison last {val} extra turn(s).",
        "effect": "rose_wilt",
        "base_value": 2,
        "icon": "🥀",
        "mary_sue_passive": {
            "name": "Wilting Presence",
            "desc": "Mary Sue's attacks apply a stacking 'Wilting' debuff that reduces max HP by 5% per stack (max 5).",
            "effect": "wilting_debuff",
        },
    },
    {
        "key": "white_rabbit_panic",
        "name": "White Rabbit's Panic",
        "desc": "'I'm late! Oh, I'm SO very late!' The Rabbit's panic is contagious. Time is running out.",
        "desc_full": "Gold drops are reduced by {pct}%. The Rabbit keeps the coin for himself.",
        "effect": "white_rabbit_panic",
        "base_value": 0.35,
        "icon": "⏰",
        "mary_sue_passive": {
            "name": "Time Lord",
            "desc": "Every 3 turns, Mary Sue takes an extra action. She writes faster than you can read.",
            "effect": "extra_turn",
        },
    },
    {
        "key": "cheshire_absence",
        "name": "Cheshire Cat's Absence",
        "desc": "The grin fades. The Cat has gone elsewhere — and without his chaos, Wonderland grows sharp-edged.",
        "desc_full": "All enemies gain +{val} initiative. The Cat's protection is gone.",
        "effect": "cheshire_absence",
        "base_value": 3,
        "icon": "👻",
        "mary_sue_passive": {
            "name": "Predator's Grin",
            "desc": "Mary Sue's critical hit chance is doubled and crits deal +50% extra damage.",
            "effect": "predators_grin",
        },
    },
]

# ── Floors where Shadow choices trigger ──────────────────────────────────────
# Floor 41-45: 1 shadow per floor (stacks, no clearing)
# Floor 46-49: 2 shadows per floor (cleared on 46 first, then stack)
# Floor 50:    2 shadows (cleared first, determines Mary Sue passives)
SHADOW_CHOICE_FLOORS = list(range(41, 51))  # Floors 41 through 50

# ═══════════════════════════════════════════════════════════════════════════════
# WONDERLAND TIERS
# ═══════════════════════════════════════════════════════════════════════════════

WONDERLAND_TIERS = [
    (1, 10, 1.0, "Gentle Whimsy"),
    (11, 20, 1.3, "Growing Curious"),
    (21, 30, 1.6, "Quite Mad"),
    (31, 50, 2.0, "Truly Wonderland"),
]


def get_wonderland_tier(floor):
    """Return (multiplier, tier_name) for the given floor."""
    for f_min, f_max, mult, name in WONDERLAND_TIERS:
        if f_min <= floor <= f_max:
            return mult, name
    return 2.0, "Truly Wonderland"


def roll_wonderland_quirk(floor, previous_quirk_key=None):
    """Roll a random Wonderland quirk for the current floor.

    Args:
        floor: Current floor number (used for tier scaling)
        previous_quirk_key: Key of the last floor's quirk to avoid repeats

    Returns:
        dict with keys: key, name, desc_full, effect, value, tier_name, icon
    """
    mult, tier_name = get_wonderland_tier(floor)

    pool = WONDERLAND_QUIRKS[:]
    if previous_quirk_key:
        pool = [q for q in pool if q["key"] != previous_quirk_key]

    quirk_def = random.choice(pool)

    scaled_value = quirk_def["base_value"] * mult

    if quirk_def["effect"] in ("tea_party_regen", "queens_decree", "cheshire_dodge",
                                "jabberwock_bane", "mad_hatter_gift", "looking_glass_luck"):
        desc_full = quirk_def["desc_full"].format(pct=int(scaled_value * 100))
    else:
        desc_full = quirk_def["desc_full"].format(val=int(scaled_value))

    return {
        "key": quirk_def["key"],
        "name": quirk_def["name"],
        "desc_full": desc_full,
        "effect": quirk_def["effect"],
        "value": scaled_value,
        "tier_name": tier_name,
        "tier_mult": mult,
        "icon": quirk_def.get("icon", "✨"),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# HEROINE DIALOGUE REACTIONS
# ═══════════════════════════════════════════════════════════════════════════════

HEROINE_CURSE_DIALOGUE = {
    "alice": {
        "curiosity_boost": [
            '"Curiouser and curiouser!" Alice exclaims, twirling. "I always did say Wonderland makes one feel... larger than life!"',
            '"Oh my! It\'s just like the mushroom — one side makes you taller, the other smaller. Which will it be?" Alice wonders aloud.',
        ],
        "tea_party_regen": [
            '"Clean cup! Move down!" Alice giggles. "The Hatter\'s tea always hits the spot — even when it isn\'t tea time."',
            'Alice pours herself an invisible cup. "There\'s nothing like a spot of tea after a frightful scuffle."',
        ],
        "cheshire_dodge": [
            '"The Cheshire Cat!" Alice claps her hands. "He always did enjoy confusing people. I\'m rather glad he\'s on our side."',
            '"Most everyone\'s mad here," Alice says with a knowing smile. "Luckily, that includes our enemies\' aim."',
        ],
        "queens_decree": [
            '"The Queen may shout \'Off with their heads!\' but her soldiers are terribly generous with their coin," Alice muses.',
            'Alice straightens her dress. "One must maintain proper decorum — even when looting fallen card soldiers."',
        ],
        "white_rabbit_haste": [
            '"Oh dear! Oh dear! The White Rabbit is running late again!" Alice grabs your hand. "Quickly now — no time to dawdle!"',
            '"I spent so long chasing that rabbit," Alice says wistfully. "It\'s rather nice having him help us instead."',
        ],
        "caterpillars_insight": [
            '"Who... are... YOU?" Alice mimics the Caterpillar\'s drawl, then laughs. "He always did ask the important questions."',
            'Alice breathes deeply. "The Caterpillar\'s hookah smoke is rather clarifying, isn\'t it? I feel sharper already."',
        ],
        "jabberwock_bane": [
            '"Beware the Jabberwock, my son! The jaws that bite, the claws that catch!" Alice recites solemnly. "But we have the vorpal blade\'s blessing."',
            '"I slew the Jabberwock once," Alice says quietly. "It seems Wonderland remembers."',
        ],
        "mad_hatter_gift": [
            '"A very merry unbirthday to us!" Alice curtsies. "The Hatter does love giving presents — even when it isn\'t anyone\'s unbirthday."',
            'Alice peers around expectantly. "The Hatter promised me a thimble once. Perhaps he\'ll leave something nicer this time."',
        ],
        "painting_roses": [
            '"Painting the roses red!" Alice hums the tune. "Though I always thought white roses were prettier. Still, the cards do good work."',
            '"The Queen would be furious if she saw white roses," Alice whispers. "Lucky for us, the paint has... medicinal properties."',
        ],
        "looking_glass_luck": [
            '"The looking-glass world is backwards," Alice explains. "Up is down, left is right, and failure is... success?"',
            'Alice steps through an imaginary mirror. "I do love a good second chance. The looking-glass always provides."',
        ],
    },
    "red_hood": {
        "curiosity_boost": [
            '"This place makes no sense," Red Hood mutters, checking her axe. "But I feel stronger, so I\'m not complaining."',
            '"Something\'s different," Red Hood says, flexing her fingers. "Whatever Wonderland is doing, I\'ll take it."',
        ],
        "tea_party_regen": [
            '"Tea? In the middle of a dungeon?" Red Hood shrugs. "After the wolf, nothing surprises me. Pass me a cup."',
            'Red Hood eyes the spectral teapot suspiciously, then drinks. "...Not bad. Better than grandmother\'s brew."',
        ],
        "cheshire_dodge": [
            '"A floating cat?" Red Hood grips her axe tighter. "I\'ve seen wolves in grandmother\'s clothing. A grinning cat is almost normal."',
            '"That cat keeps distracting them," Red Hood notes. "Good. Makes my job easier."',
        ],
        "queens_decree": [
            '"A queen who wants heads?" Red Hood smirks darkly. "I know the type. At least her soldiers have deep pockets."',
            'Red Hood picks through fallen cards. "Playing-card soldiers. And I thought MY story was strange."',
        ],
        "white_rabbit_haste": [
            '"A talking rabbit in a waistcoat." Red Hood shakes her head. "I\'ve officially seen everything. Let\'s move while he\'s helping."',
            '"I\'m used to being hunted," Red Hood says, matching the quickened pace. "It\'s nice to be the one moving faster for once."',
        ],
        "caterpillars_insight": [
            '"A smoking caterpillar giving life advice." Red Hood stares. "You know what? Sure. Why not. His advice is good."',
            'Red Hood ponders the smoke rings. "That caterpillar... he actually makes sense. More than most people I\'ve met."',
        ],
        "jabberwock_bane": [
            '"A dragon with eyes of flame?" Red Hood readies her axe. "I\'ve faced one monster. What\'s one more? Especially with this blessing."',
            '"The vorpal blade\'s power..." Red Hood touches her weapon. "I can feel it. This is for every girl who faced a wolf alone."',
        ],
        "mad_hatter_gift": [
            '"A madman leaving presents?" Red Hood raises an eyebrow. "As long as it\'s not a basket of poisoned goodies, I\'ll take it."',
            'Red Hood examines a stray gift. "The Hatter has better taste than the wolf. That\'s a low bar, but still."',
        ],
        "painting_roses": [
            '"Painting flowers red." Red Hood\'s expression darkens. "Reminds me of blood on snow. At least this paint HEALS instead."',
            'Red Hood touches a painted rose. "I\'ve seen too much red. But this... this is a good kind of red."',
        ],
        "looking_glass_luck": [
            '"Everything reversed?" Red Hood smirks. "Finally. A world where bad luck turns good. I\'ve been waiting for this."',
            '"Second chances," Red Hood murmurs. "Back in the woods, you don\'t get those. I won\'t waste it."',
        ],
    },
    "dorothy": {
        "curiosity_boost": [
            '"Toto, I\'ve a feeling we\'re not in Kansas anymore," Dorothy whispers. "Though... I rather like this feeling!"',
            '"Oz made me feel special. Wonderland makes me feel STRONG!" Dorothy twirls, ruby slippers clicking.',
        ],
        "tea_party_regen": [
            '"A tea party! Oh, how lovely!" Dorothy claps. "The Munchkins would have adored this. Much better than Aunt Em\'s bitter brew."',
            'Dorothy sips daintily. "The Scarecrow always said a warm cup makes the thinking easier. Or was that the Tin Man?"',
        ],
        "cheshire_dodge": [
            '"A disappearing cat?!" Dorothy gasps. "And I thought the Horse of a Different Color was strange! But he IS helpful."',
            '"The Wicked Witch would\'ve loved that cat," Dorothy muses. "Which means I\'m glad he\'s OUR friend instead."',
        ],
        "queens_decree": [
            '"Follow the yellow brick road... to treasure!" Dorothy laughs. "The Wizard never paid this well!"',
            '"Emeralds, gold... the Queen\'s soldiers just leave it lying about?!" Dorothy scoops up coins eagerly.',
        ],
        "white_rabbit_haste": [
            '"A rabbit who\'s late?" Dorothy giggles. "The White Rabbit would get along with the White Rabbit of Oz! Wait... they\'re different, right?"',
            '"There\'s no place like home," Dorothy says, "but there\'s also no place like being FAST! Keep up, everyone!"',
        ],
        "caterpillars_insight": [
            '"A wise caterpillar..." Dorothy\'s eyes go distant. "Professor Marvel would\'ve had quite the conversation with him."',
            'Dorothy breathes the hookah-scented air. "I feel like I could solve the Wizard\'s riddles three times over now."',
        ],
        "jabberwock_bane": [
            '"A Jabberwock..." Dorothy shivers. "I faced a Wicked Witch. I can face a dragon. Especially with this courage!"',
            '"The Cowardly Lion would be so proud," Dorothy says, gripping her weapon. "We\'re ALL brave now."',
        ],
        "mad_hatter_gift": [
            '"Presents from a stranger?" Dorothy tilts her head. "The Wizard gave me gifts too. But the Hatter seems... nicer. Sillier, but nicer."',
            '"An unbirthday present!" Dorothy beams. "I have SO many unbirthdays to celebrate! This is wonderful!"',
        ],
        "painting_roses": [
            '"Painting flowers..." Dorothy touches a rose. "In Kansas, roses bloom red all on their own. But this paint — it feels magical!"',
            '"Emerald City had green everywhere," Dorothy says. "Red roses are a nice change. And they heal, too!"',
        ],
        "looking_glass_luck": [
            '"Click your heels three times," Dorothy says, "and maybe your luck turns around! This mirror world is BETTER than Oz!"',
            '"Second chances are precious," Dorothy says softly. "I know. I got one to go home. Let\'s not waste this one."',
        ],
    },
}

# ── Generic (no heroine) flavour text for each quirk ──────────────────
GENERIC_QUIRK_FLAVOUR = {
    "curiosity_boost": [
        "You feel a strange tingling — as if Wonderland itself is remaking you, piece by curious piece.",
    ],
    "tea_party_regen": [
        "The scent of bergamot and buttered scones wafts through the hall. Your spirits lift.",
    ],
    "cheshire_dodge": [
        "A floating grin winks at you from thin air, then vanishes. Your enemies look very confused.",
    ],
    "queens_decree": [
        "A distant shout of 'OFF WITH THEIR HEADS!' echoes. The card soldiers look nervous... and wealthy.",
    ],
    "white_rabbit_haste": [
        "'Oh my ears and whiskers, we\'re late!' The words echo and time seems to hurry along with you.",
    ],
    "caterpillars_insight": [
        "Smoke rings drift past, smelling of spice and wisdom. Your thoughts clear like never before.",
    ],
    "jabberwock_bane": [
        "Your weapon hums faintly. Somewhere, something large and terrible just flinched.",
    ],
    "mad_hatter_gift": [
        "Party streamers and confetti drift from nowhere. Someone, somewhere, is celebrating YOU.",
    ],
    "painting_roses": [
        "The walls shimmer with fresh red paint. The air smells of roses and second chances.",
    ],
    "looking_glass_luck": [
        "Reality ripples like a pond. For a moment, you see yourself winning — and the vision lingers.",
    ],
}


# ═══════════════════════════════════════════════════════════════════════════════
# HEROINE SHADOW CHOICE DIALOGUE — Reactions when player picks a Shadow
# ═══════════════════════════════════════════════════════════════════════════════

HEROINE_SHADOW_CHOICE_DIALOGUE = {
    "alice": {
        "authors_will": [
            '"She\'s rewriting everything," Alice whispers, her voice unsteady. "Just like the Queen tried to rewrite Wonderland. But this... this is worse. She wrote the Queen."',
            'Alice clutches her skirt. "My story was written by someone else too, once. But I took it back. You can too."',
        ],
        "off_with_heads": [
            '"Off with their heads!" Alice murmurs. "I\'ve heard that scream so many times. The Queen\'s temper is legendary... and now it follows US."',
            'Alice touches her neck unconsciously. "The Queen tried to take MY head. I know exactly how dangerous that decree is."',
        ],
        "down_rabbit_hole": [
            '"Falling... falling..." Alice\'s eyes go distant. "I fell for what felt like hours. You never quite learn to land."',
            '"The rabbit hole is deeper than I remembered," Alice says, steadying herself. "And this time, I don\'t think there\'s a bottom."',
        ],
        "jabberwock_wrath": [
            '"The Jabberwock, with eyes of flame..." Alice recites, then shudders. "I slew it once with the vorpal blade. But its rage... its rage never died."',
            'Alice draws an imaginary sword. "One, two! One, two! And through and through. But the poem never said the beast would haunt you."',
        ],
        "madness_contagion": [
            '"We\'re all mad here," Alice says with a sad smile. "I\'m mad. You\'re mad. The question is... how much madder can we become before we break?"',
            'Alice laughs, but it\'s hollow. "The Hatter\'s tea party never ends. And neither does his madness. It\'s... contagious, you see."',
        ],
        "looking_glass_shatter": [
            '"The looking-glass..." Alice reaches out as if touching shards. "I walked through it once. Everything was backwards. Now it\'s just... broken."',
            '"Seven years of bad luck," Alice says quietly. "That\'s what they say about broken mirrors. I wonder if Wonderland counts in dog years."',
        ],
        "caterpillars_smoke": [
            '"The Caterpillar\'s hookah..." Alice coughs. "He always did ask the important questions. But the smoke — the smoke makes everything so HARD to see."',
            '"Who are YOU?" Alice mimics, then frowns. "I can\'t even see myself anymore. The smoke is everywhere."',
        ],
        "rose_wilt": [
            '"The roses are dying," Alice gasps. "The cards painted them red so the Queen wouldn\'t be angry. But now they\'re wilting and there\'s no paint left."',
            'Alice kneels beside a dead rose. "We\'re painting the roses red... except there\'s no red left. Only thorns."',
        ],
        "white_rabbit_panic": [
            '"Oh dear! Oh dear! I\'m late!" Alice says, but her voice trembles. "The White Rabbit\'s panic... it\'s not funny anymore. I think he was running from something."',
            'Alice checks an invisible pocket watch. "The Rabbit was always rushing. I never understood why until now. Time is running out."',
        ],
        "cheshire_absence": [
            '"The Cheshire Cat..." Alice looks around desperately. "He always appeared when I needed him most. But now... now there\'s only the grin. And even that is fading."',
            '"Most everyone\'s mad here," Alice whispers. "But the Cat — the Cat kept me sane. Without him, I\'m just... lost."',
        ],
    },
    "red_hood": {
        "authors_will": [
            '"Someone\'s writing my story?" Red Hood\'s grip tightens on her axe. "Last time someone wrote my story, I ended up in a wolf\'s belly. Not again."',
            'Red Hood scans the darkness. "A narrator who controls everything? I\'ve killed wolves. I can kill an author."',
        ],
        "off_with_heads": [
            '"An executioner\'s axe," Red Hood says flatly. "I know what it feels like to face one. The huntsman had an axe too. He used it to save me."',
            '"Off with their heads?" Red Hood bares her teeth. "The wolf said something similar. I took HIS head instead."',
        ],
        "down_rabbit_hole": [
            '"The woods shifted too," Red Hood mutters, planting her feet. "Trees that moved. Paths that led in circles. I learned to keep my footing then."',
            'Red Hood steadies herself. "Falling is just... falling. What matters is what you do when you stand back up."',
        ],
        "jabberwock_wrath": [
            '"A beast of fire and fang," Red Hood says quietly. "Reminds me of... someone. The jaws that bite, the claws that catch. I\'ve seen those before."',
            'Red Hood\'s eyes narrow. "The wolf was a monster. The Jabberwock is a legend. And legends... legends can be killed."',
        ],
        "madness_contagion": [
            '"Madness?" Red Hood scoffs. "I walked through the dark woods alone as a child. I talked to a wolf dressed as my grandmother. Madness and I are old friends."',
            'Red Hood touches her red cloak. "Everyone thinks I\'m crazy for wearing this. Let them. Madness is just another weapon."',
        ],
        "looking_glass_shatter": [
            '"Broken mirrors," Red Hood says. "I stopped looking in mirrors a long time ago. The reflection never showed me — just the wolf."',
            '"Seven years of bad luck?" Red Hood laughs bitterly. "I\'ve had a lifetime of bad luck. This is just... more."',
        ],
        "caterpillars_smoke": [
            '"Smoke," Red Hood coughs. "The wolf\'s breath was hot and smoky too. At least this caterpillar isn\'t trying to eat me."',
            'Red Hood squints through the haze. "Can\'t see. Doesn\'t matter. The wolf couldn\'t see in the dark either. I still found him."',
        ],
        "rose_wilt": [
            '"Flowers dying?" Red Hood touches a wilted rose. "My grandmother loved roses. The wolf trampled her garden before he... before everything."',
            'Red Hood crushes a dead rose in her fist. "Death follows beauty. That\'s the way of the woods. That\'s the way of everywhere."',
        ],
        "white_rabbit_panic": [
            '"Running out of time," Red Hood mutters. "I ran out of time once. Grandmother ran out of time. The wolf didn\'t wait."',
            '"A panicked rabbit?" Red Hood shakes her head. "I\'ve been hunted. I\'ve been prey. Panic doesn\'t help. Action does."',
        ],
        "cheshire_absence": [
            '"A grinning cat who disappears," Red Hood says. "I had a protector once. The huntsman. He disappeared too, when I needed him most."',
            'Red Hood looks up at the empty air. "Everyone leaves eventually. The Cat. The huntsman. Grandmother. The only one who stays is me."',
        ],
    },
    "dorothy": {
        "authors_will": [
            '"Someone\'s writing this story?" Dorothy\'s eyes widen. "Like the Wizard pulling levers behind a curtain? I\'ve seen this trick before!"',
            'Dorothy stamps her foot. "The Wizard tried to control Oz from behind a curtain. But I pulled that curtain back. I\'ll pull this one too."',
        ],
        "off_with_heads": [
            '"The Wicked Witch wanted my head too," Dorothy says, crossing her arms. "And my ruby slippers. The Queen will have to wait in line."',
            '"An executioner?" Dorothy shivers. "The Witch sent flying monkeys after me. An axe is almost... straightforward."',
        ],
        "down_rabbit_hole": [
            '"A twister!" Dorothy grabs for something to hold. "No... it\'s different. A twister lifts you UP. This is pulling me DOWN. But it\'s just as scary."',
            'Dorothy closes her eyes. "Click your heels three times... no, that won\'t work here. Toto, I don\'t think we\'re in Oz anymore either."',
        ],
        "jabberwock_wrath": [
            '"Lions and tigers and... Jabberwocks?" Dorothy\'s voice wavers. "Oh my. The Cowardly Lion would faint. Actually, I might faint too."',
            'Dorothy squares her shoulders. "I faced a Wicked Witch. I faced the Wizard himself. A fire-breathing dragon is just... another Tuesday."',
        ],
        "madness_contagion": [
            '"I thought Oz was strange," Dorothy says. "Talking scarecrows. Heartless tin men. Cowardly lions. But Wonderland makes Oz look like Kansas."',
            'Dorothy giggles nervously. "The Scarecrow wanted a brain. The Tin Man wanted a heart. What do you want when you\'re GOING mad?"',
        ],
        "looking_glass_shatter": [
            '"The mirror..." Dorothy touches her ruby slippers. "The Wizard used mirrors and smoke to seem powerful. But broken mirrors just show the truth."',
            '"Bad luck?" Dorothy shakes her head. "I was swept away by a tornado. My house landed on a witch. Luck is just... perspective."',
        ],
        "caterpillars_smoke": [
            '"Smoke everywhere," Dorothy coughs. "The Wizard used smoke too — to hide his machines, his tricks. But this smoke hides something worse."',
            'Dorothy waves her hand through the haze. "Professor Marvel used smoke in his fortune-telling act. He was a fraud. This... this is real."',
        ],
        "rose_wilt": [
            '"The flowers are dying..." Dorothy kneels down. "In Oz, the poppies made us sleep forever. These roses just... give up. I don\'t know which is worse."',
            'Dorothy touches a wilting petal. "Aunt Em\'s garden never looked like this. Kansas has tornadoes, but at least the flowers come back."',
        ],
        "white_rabbit_panic": [
            '"A rabbit who\'s late?" Dorothy frowns. "Back home, being late meant missing supper. Here... here it means something terrible is coming."',
            '"Time running out," Dorothy whispers. "The Witch\'s hourglass was running out for me once. I made it. But I barely made it."',
        ],
        "cheshire_absence": [
            '"A friend who disappears," Dorothy says sadly. "The Scarecrow, the Tin Man, the Lion... they all stayed with me. I don\'t know what I\'d do without them."',
            'Dorothy looks around the empty air. "Everyone needs someone. That Cat was your someone, wasn\'t he? And now he\'s gone."',
        ],
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# HEROINE FLOOR 50 DIALOGUE — Story climax when Mary Sue's shadow passives activate
# ═══════════════════════════════════════════════════════════════════════════════

HEROINE_SHADOW_FLOOR50_DIALOGUE = {
    "alice": {
        "authors_will": [
            '"She\'s rewriting EVERYTHING!" Alice cries. "My story, your story, the Queen\'s story — she wrote them ALL! She\'s making herself the hero of every tale, and we\'re just... characters she can erase!"',
            'Alice stands frozen, staring at Mary Sue\'s pen. "I thought I escaped my story. I thought Wonderland was MINE. But she wrote me into existence. She can write me OUT."',
        ],
        "off_with_heads": [
            '"The Queen\'s decree..." Alice\'s voice is barely a whisper. "She taught the Queen to say it. \'Off with their heads!\' — those are HER words, not the Queen\'s. She created a monster just to see what would happen."',
            'Alice trembles. "The Queen of Hearts was HER first draft. A villain she wrote for FUN. And now that same cruelty is aimed at US."',
        ],
        "down_rabbit_hole": [
            '"The rabbit hole!" Alice points at Mary Sue. "She wrote the rabbit hole! She made me fall! My entire adventure — being small, being tall, the tea party, the trial — it was ALL her first draft!"',
            'Alice\'s eyes fill with tears — of rage, not sadness. "I thought Wonderland was MY dream. But I was HERS. Everything I am, everything I became... was her practice."',
        ],
        "jabberwock_wrath": [
            '"The Jabberwock..." Alice draws an invisible vorpal blade. "She wrote the poem. She put the beast in my path. My greatest victory — slaying the Jabberwock — was just HER plot point!"',
            '"\'Beware the Jabberwock, my son!\'" Alice recites bitterly. "She wrote those words. She made me the hero so she could take the glory when I won. And now the beast\'s rage lives on."',
        ],
        "madness_contagion": [
            '"The Hatter\'s madness," Alice says slowly. "She made him that way. She thought a mad hatter was FUNNY. She didn\'t care that he was suffering — she just wanted a quirky character!"',
            'Alice presses her hands to her temples. "We\'re ALL her characters. Our quirks, our flaws, our madness — she wrote them ALL. And now she\'s writing us into oblivion."',
        ],
        "looking_glass_shatter": [
            '"The looking-glass..." Alice stares at the shards floating around Mary Sue. "I went through it. I met the Red Queen, the White Queen, the talking flowers. All of them — HER creations!"',
            '"Everything\'s backwards through the looking-glass," Alice says. "But she\'s the one holding the mirror. She decides what\'s forward and what\'s backward. She decides what\'s REAL."',
        ],
        "caterpillars_smoke": [
            '"The Caterpillar\'s questions," Alice murmurs. "\'Who are YOU?\' He asked me that. But he never asked HER. She was too busy writing him as a wise old sage to realize she had no answer herself."',
            'Alice coughs in the smoke. "The Caterpillar gave me the mushroom. He helped me control my size. But SHE wrote him. She decided he would help. What if she changes her mind?"',
        ],
        "rose_wilt": [
            '"The roses..." Alice watches them die. "The cards painted them red because the Queen demanded it. But who taught the Queen to demand? Who wrote her temper, her vanity, her CRUELTY?"',
            'Alice kneels beside a dying rose. "White roses were beautiful. They didn\'t NEED to be red. But she wrote a Queen who hated white. And now everything beautiful is dying."',
        ],
        "white_rabbit_panic": [
            '"The White Rabbit..." Alice\'s voice cracks. "He was my first friend in Wonderland. He led me to adventure. But he was always afraid. Always running. Because SHE wrote him that way."',
            '"\'I\'m late, I\'m late!\'" Alice mimics, then wipes her eyes. "He was late for HER story. She put him on a schedule, gave him anxiety, made him a puppet to her plot!"',
        ],
        "cheshire_absence": [
            '"The Cheshire Cat," Alice says, her voice breaking. "He was the only one who told me the truth. \'We\'re all mad here.\' He knew. He KNEW they were all characters in someone else\'s story."',
            'Alice looks up at the empty space where the Cat\'s grin should be. "He disappeared because he figured it out. He LEFT the story. And now she can\'t find him. That\'s why he\'s gone — he ESCAPED."',
        ],
    },
    "red_hood": {
        "authors_will": [
            '"She wrote the wolf," Red Hood says, her voice dangerously calm. "She wrote grandmother\'s sickness. She wrote the woods that trapped me. Every nightmare I lived through — was HER entertainment."',
            'Red Hood\'s knuckles go white on her axe. "My story was a cautionary tale. \'Don\'t talk to strangers.\' But she didn\'t write it to teach — she wrote it because she thought my fear was INTERESTING."',
        ],
        "off_with_heads": [
            '"The huntsman\'s axe," Red Hood says quietly. "He used it to cut me out of the wolf\'s belly. It saved my life. But now an executioner\'s axe is coming for me — and SHE put it there."',
            '"An execution?" Red Hood\'s laugh is hollow. "I survived being eaten alive. I survived the dark woods. I survived everything SHE wrote for me. I\'m not dying to her final draft."',
        ],
        "down_rabbit_hole": [
            '"The woods," Red Hood whispers. "They didn\'t just feel endless — she MADE them endless. Every twisted tree, every false path, every shadow that looked like a wolf... she wrote ALL of it."',
            'Red Hood plants her feet. "I got lost in those woods. For days. And she was just... watching. Taking notes. Thinking about how to make it SCARIER."',
        ],
        "jabberwock_wrath": [
            '"A fire-breathing monster?" Red Hood snarls. "The wolf was bad enough. But at least the wolf was REAL — as real as anything she writes. The Jabberwock is just another monster from her pen."',
            '"The wolf had one weakness," Red Hood says. "His belly. The huntsman cut it open. Every monster has a weakness — even the ones she writes. We just have to FIND it."',
        ],
        "madness_contagion": [
            '"Madness," Red Hood says bitterly. "She thinks it\'s a plot device. She doesn\'t know what real madness feels like — the kind that comes from watching your grandmother get eaten."',
            'Red Hood\'s eyes are wild. "I\'ve been to the edge of sanity. I looked over. The only thing that brought me back was the huntsman\'s hand. But she\'d write that as \'deus ex machina\' and move on."',
        ],
        "looking_glass_shatter": [
            '"Mirrors," Red Hood growls. "After the wolf, I couldn\'t look in mirrors. My reflection looked like someone else — someone who\'d been inside a monster. Now she\'s shattering every mirror in existence."',
            '"Fine," Red Hood snarls. "Break the mirrors. I don\'t need to see myself. I know who I am. I\'m the girl who KILLED the wolf. And that wasn\'t her writing — that was ME."',
        ],
        "caterpillars_smoke": [
            '"More smoke," Red Hood coughs. "The wolf\'s cave was full of smoke — from grandmother\'s fireplace. He was wearing her nightgown, sitting in her chair. The smoke hid his teeth."',
            'Red Hood squints through the haze at Mary Sue. "She thinks smoke makes things mysterious. I think it just makes it harder to see the MONSTER hiding behind the words."',
        ],
        "rose_wilt": [
            '"Grandmother loved roses," Red Hood says quietly. "She had a garden. The wolf trampled it. Now something worse than a wolf is killing every rose that ever bloomed."',
            'Red Hood touches her red cloak. "Red like roses. Red like blood. Red like the hood that marked me as prey. She chose the color. She wrote the symbolism. And now she\'s letting it all DIE."',
        ],
        "white_rabbit_panic": [
            '"I ran out of time once," Red Hood says. "I got to grandmother\'s house too late. The wolf was already there. She wrote it that way. She thought the DRAMA was worth it."',
            '"A ticking clock," Red Hood snarls. "She loves deadlines. Tension. The reader on the edge of their seat. But we\'re not READERS — we\'re the ones running out of time!"',
        ],
        "cheshire_absence": [
            '"The huntsman," Red Hood says, almost to herself. "He was there when I needed him. He heard my screams, broke down the door, killed the wolf. But she could have written him out. She could have let me DIE."',
            'Red Hood looks at the empty space where the Cat should be. "Your Cat escaped the story. My huntsman stayed. I don\'t know which of us is luckier."',
        ],
    },
    "dorothy": {
        "authors_will": [
            '"She wrote everything?" Dorothy\'s ruby slippers click together. "The Wizard pretended to be all-powerful. But SHE actually IS. She wrote Oz. She wrote Kansas. She wrote ME."',
            'Dorothy points at Mary Sue, her hand shaking. "The tornado? That was her. The Witch? Her. The yellow brick road? She paved it. My entire journey home — was just her FIRST NOVEL."',
        ],
        "off_with_heads": [
            '"The Witch sent flying monkeys," Dorothy says. "She wrote \'Surrender Dorothy\' in the sky. But those were the WITCH\'S words. Mary Sue wrote the Witch. She wrote the MONKEYS. She wrote my FEAR."',
            'Dorothy straightens her dress. "The Witch wanted my ruby slippers. The Queen wants my head. And Mary Sue wants my STORY. She can\'t have any of them."',
        ],
        "down_rabbit_hole": [
            '"A twister," Dorothy breathes. "The cyclone that took me to Oz — it wasn\'t an accident. She wrote it. She needed a protagonist, so she ripped a farm girl out of Kansas and dropped her in a fantasy world."',
            'Dorothy looks sick. "Aunt Em was calling my name. I couldn\'t reach the storm cellar. And all along, it wasn\'t fate or weather — it was HER, turning my life into CHAPTER ONE."',
        ],
        "jabberwock_wrath": [
            '"A dragon?" Dorothy gasps. "The Wicked Witch had a crystal ball that showed her everything. But even SHE couldn\'t create monsters — she just controlled the ones that existed. Mary Sue creates them from NOTHING."',
            '"Lions and tigers and bears," Dorothy whispers. "The Cowardly Lion was afraid of everything. But at least the things he feared were REAL. Mary Sue\'s monsters are made of ink and cruelty."',
        ],
        "madness_contagion": [
            '"Oz was strange," Dorothy says. "But it had rules. Yellow brick road. Emerald City. Don\'t touch the poppies. Wonderland has no rules — because she changes them whenever she gets BORED."',
            'Dorothy looks at her companions. "The Scarecrow, the Tin Man, the Lion — they were looking for brains, a heart, and courage. But they already HAD those things. Mary Sue would write them as actually MISSING."',
        ],
        "looking_glass_shatter": [
            '"The Wizard\'s hall," Dorothy remembers. "He used mirrors and smoke to look like a giant floating head. But Mary Sue doesn\'t need tricks. She just writes what she wants and it BECOMES true."',
            '"She\'s the Wizard without the curtain," Dorothy says. "No need to hide. No need to pretend. Just a pen and an ego and an entire universe that bends to her WILL."',
        ],
        "caterpillars_smoke": [
            '"Smoke and mirrors," Dorothy coughs. "The Wizard used them because he was a fraud. Mary Sue uses them because she thinks they\'re atmospheric. She\'s not hiding anything — she\'s SHOWING OFF."',
            'Dorothy waves at the smoke. "Professor Marvel pretended to see the future in smoke. Mary Sue doesn\'t pretend. If she writes it, it happens. The smoke is just for DRAMA."',
        ],
        "rose_wilt": [
            '"The poppies," Dorothy whispers. "In Oz, the poppies put you to sleep forever. The Witch planted them to stop me. But Glinda made it snow and woke us up. These roses... no one\'s coming to save them."',
            'Dorothy touches a dying rose. "In Kansas, things die because of drought or frost. Natural things. But these roses are dying because she\'s TIRED of them. She\'s moving on to the next scene."',
        ],
        "white_rabbit_panic": [
            '"Time running out," Dorothy says. "The Witch gave me an hourglass. When the sand ran out, she said she\'d kill me. But that was FICTION. Mary Sue\'s deadlines are REAL."',
            '"There\'s no place like home," Dorothy whispers. "But home only exists if she lets it. If she erases Kansas, if she unwrites Aunt Em — I have NOWHERE to go back to."',
        ],
        "cheshire_absence": [
            '"A friend who fades away," Dorothy says, her voice breaking. "The Scarecrow, the Tin Man, the Lion — I had to leave them. But they were still THERE. They existed. Your Cat just... doesn\'t."',
            'Dorothy looks up. "Toto stayed with me through everything. Even the Witch couldn\'t take him. But Mary Sue can write anyone out of existence. Your Cat. My friends. Anyone she gets bored with."',
        ],
    },
}


def get_heroine_shadow_choice_dialogue(heroine_key, shadow_key):
    """Get a random dialogue line for a heroine reacting to the player CHOOSING a Shadow.

    Called when the player picks a Shadow at floor 40 or 46.

    Args:
        heroine_key: "alice", "red_hood", or "dorothy"
        shadow_key: the shadow's key string

    Returns:
        A dialogue string, or None if no dialogue is defined.
    """
    heroine_lines = HEROINE_SHADOW_CHOICE_DIALOGUE.get(heroine_key, {})
    lines = heroine_lines.get(shadow_key)
    if lines:
        return random.choice(lines)
    return None


def get_heroine_shadow_floor50_dialogue(heroine_key, shadow_key):
    """Get a special story-climax dialogue line for Floor 50 Mary Sue reveal.

    Called when Mary Sue's shadow passives are revealed at the start of the fight.

    Args:
        heroine_key: "alice", "red_hood", or "dorothy"
        shadow_key: the shadow's key string

    Returns:
        A dialogue string, or None if no dialogue is defined.
    """
    heroine_lines = HEROINE_SHADOW_FLOOR50_DIALOGUE.get(heroine_key, {})
    lines = heroine_lines.get(shadow_key)
    if lines:
        return random.choice(lines)
    return None


def get_heroine_dialogue(heroine_key, quirk_key):
    """Get a random dialogue line for a heroine reacting to a Wonderland quirk.

    Args:
        heroine_key: "alice", "red_hood", or "dorothy"
        quirk_key: the quirk's key string

    Returns:
        A dialogue string, or None if no dialogue is defined.
    """
    heroine_lines = HEROINE_CURSE_DIALOGUE.get(heroine_key, {})
    lines = heroine_lines.get(quirk_key)
    if lines:
        return random.choice(lines)
    return None


def get_generic_flavour(quirk_key):
    """Get a generic (non-heroine) flavour line for a quirk."""
    lines = GENERIC_QUIRK_FLAVOUR.get(quirk_key)
    if lines:
        return random.choice(lines)
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# QUIRK APPLICATION FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def apply_wonderland_quirk_on_floor_start(player, floor):
    """Roll and apply a Wonderland floor quirk. Call at the start of each floor.

    Quirks are persisted per floor in player['wonderland_floor_quirks'].
    If the player already has a quirk for this floor (e.g., after leaving
    and re-entering), the same quirk is reused — preventing the player from
    re-rolling for a more favourable quirk by leaving and coming back.

    Returns:
        str: formatted display message
    """
    # ── Check for existing quirk on this floor (prevents leave/re-enter abuse) ─
    floor_quirks = player.setdefault("wonderland_floor_quirks", {})
    floor_key = str(floor)
    if floor_key in floor_quirks:
        # Re-use the existing quirk for this floor
        quirk = floor_quirks[floor_key]
        player["wonderland_quirk"] = quirk
    else:
        previous_key = None
        prev = player.get("wonderland_quirk")
        if prev:
            previous_key = prev.get("key")

        quirk = roll_wonderland_quirk(floor, previous_quirk_key=previous_key)

        # Persist the quirk for this floor
        floor_quirks[floor_key] = quirk
        player["wonderland_quirk"] = quirk

    # Build display message
    lines = []
    lines.append("")
    lines.append("╔" + "═" * 58 + "╗")
    lines.append(f"║  WONDERLAND WHIMSY — Floor {floor} — {quirk['tier_name']}".ljust(59) + "║")
    lines.append("╠" + "═" * 58 + "╣")
    lines.append(f"║  {quirk['icon']}  {quirk['name']}".ljust(59) + "║")
    lines.append("║" + " " * 58 + "║")
    # Wrap description
    desc = quirk["desc_full"]
    while len(desc) > 54:
        split = desc.rfind(" ", 0, 54)
        if split == -1:
            split = 54
        lines.append(f"║  {desc[:split]}".ljust(59) + "║")
        desc = desc[split:].strip()
    if desc:
        lines.append(f"║  {desc}".ljust(59) + "║")
    lines.append("╚" + "═" * 58 + "╝")

    # ── Heroine dialogue reactions ──────────────────────────────────────
    dialogue_lines = []
    for ally in player.get("allies", []):
        heroine_key = ally.get("_heroine_key")
        if heroine_key:
            dialogue = get_heroine_dialogue(heroine_key, quirk["key"])
            if dialogue:
                dialogue_lines.append(f"\n  💬 [{ally['name']}] {dialogue}")

    if dialogue_lines:
        lines.append("")
        lines.append("  ── Heroine Reactions ──")
        lines.extend(dialogue_lines)
    else:
        # Generic flavour if no heroines present
        flavour = get_generic_flavour(quirk["key"])
        if flavour:
            lines.append("")
            lines.append(f"  {flavour}")

    return "\n".join(lines)


def clear_wonderland_quirk(player):
    """Remove the Wonderland quirk and all persisted floor quirks from the player."""
    player.pop("wonderland_quirk", None)
    player.pop("wonderland_floor_quirks", None)


def get_wl_quirk(player):
    """Get the current Wonderland quirk dict, or None."""
    return player.get("wonderland_quirk")


def get_wl_quirk_value(player, effect_type):
    """Get the scaled value for a specific quirk effect, or 0 if not active."""
    quirk = get_wl_quirk(player)
    if quirk and quirk.get("effect") == effect_type:
        return quirk.get("value", 0)
    return 0


# ═══════════════════════════════════════════════════════════════════════════════
# QUIRK EFFECT APPLICATION FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def apply_tea_party_regen(player, heal_amount):
    """Increase post-combat healing if Tea Party Regen is active."""
    quirk = get_wl_quirk(player)
    if quirk and quirk.get("effect") == "tea_party_regen":
        bonus = quirk.get("value", 0)
        heal_amount = int(heal_amount * (1.0 + bonus))
    return heal_amount


def apply_queens_decree(player, gold_amount):
    """Increase gold drops if Queen's Decree is active."""
    quirk = get_wl_quirk(player)
    if quirk and quirk.get("effect") == "queens_decree":
        bonus = quirk.get("value", 0)
        gold_amount = int(gold_amount * (1.0 + bonus))
    return gold_amount


def get_cheshire_dodge_chance(player):
    """Return the enemy miss chance from Cheshire Cat's Favor, or 0."""
    return get_wl_quirk_value(player, "cheshire_dodge")


def get_jabberwock_bane_multiplier(player):
    """Return the bonus damage multiplier vs bosses from Jabberwock's Bane."""
    return get_wl_quirk_value(player, "jabberwock_bane")


def get_caterpillars_insight_reduction(player):
    """Return the DC reduction from Caterpillar's Insight."""
    return get_wl_quirk_value(player, "caterpillars_insight")


def get_white_rabbit_cooldown_reduction(player):
    """Return the cooldown reduction from White Rabbit's Haste."""
    return get_wl_quirk_value(player, "white_rabbit_haste")


def get_mad_hatter_drop_chance(player):
    """Return the extra item drop chance from Mad Hatter's Generosity."""
    return get_wl_quirk_value(player, "mad_hatter_gift")


def get_looking_glass_reroll_chance(player):
    """Return the re-roll chance from Through the Looking Glass."""
    return get_wl_quirk_value(player, "looking_glass_luck")


def get_curiosity_boost_value(player):
    """Return the random stat boost value from Curiouser and Curiouser."""
    return get_wl_quirk_value(player, "curiosity_boost")


def get_painting_roses_reduction(player):
    """Return the bleed/poison duration reduction from Painting the Roses Red."""
    return get_wl_quirk_value(player, "painting_roses")


def format_active_quirk_line(player):
    """Format a single-line display of the active Wonderland quirk."""
    quirk = get_wl_quirk(player)
    if not quirk:
        return None
    return f"  {quirk.get('icon', '✨')} {quirk['name']} — {quirk['desc_full']}"


def format_quirk_summary(player):
    """Return a short summary string for the top bar: quirk icon+name + shadow count.
    
    Returns empty string if no Wonderland quirk or shadows are active.
    """
    parts = []
    quirk = get_wl_quirk(player)
    if quirk:
        parts.append(f"{quirk.get('icon', '✨')} {quirk['name']}")
    shadows = get_player_shadows(player)
    if shadows:
        shadow_icons = []
        for sk in shadows:
            sd = get_shadow_def(sk)
            if sd:
                shadow_icons.append(sd.get("icon", "🌑"))
        if shadow_icons:
            parts.append(f"🌑×{len(shadows)} {' '.join(shadow_icons)}")
    return " | ".join(parts) if parts else ""


# ═══════════════════════════════════════════════════════════════════════════════
# WONDERLAND SHADOW SYSTEM (Floor 40+)
# ═══════════════════════════════════════════════════════════════════════════════


def get_player_shadows(player):
    """Return the list of active persistent Shadow keys on the player."""
    return player.get("wonderland_shadows", [])


def has_shadow(player, shadow_key):
    """Check if the player carries a specific Shadow."""
    return shadow_key in get_player_shadows(player)


def get_available_shadows(player):
    """Return Shadows the player hasn't picked yet (for choice menus)."""
    current = set(get_player_shadows(player))
    return [s for s in WONDERLAND_SHADOWS if s["key"] not in current]


def get_shadow_def(shadow_key):
    """Get a Shadow definition by key."""
    for s in WONDERLAND_SHADOWS:
        if s["key"] == shadow_key:
            return s
    return None


def build_shadow_choice_display(player, available_shadows):
    """Build a formatted display of available Shadows for the choice screen."""
    lines = []
    lines.append("")
    lines.append("╔" + "═" * 58 + "╗")
    lines.append("║  🌑  WONDERLAND GROWS DARKER...".ljust(59) + "║")
    lines.append("╠" + "═" * 58 + "╣")
    lines.append("║  The realm's whimsy twists. A Shadow must be chosen.".ljust(59) + "║")
    lines.append("║  This Shadow will persist on ALL subsequent floors.".ljust(59) + "║")
    lines.append("║" + " " * 58 + "║")
    lines.append("║  Choose wisely — it cannot be undone.".ljust(59) + "║")
    lines.append("╚" + "═" * 58 + "╝")
    lines.append("")
    for i, shadow in enumerate(available_shadows):
        icon = shadow.get("icon", "🌑")
        lines.append(f"  [{i + 1}] {icon} {shadow['name']}")
        # Wrap description
        desc = shadow["desc"]
        while len(desc) > 52:
            split = desc.rfind(" ", 0, 52)
            if split == -1:
                split = 52
            lines.append(f"      {desc[:split]}")
            desc = desc[split:].strip()
        if desc:
            lines.append(f"      {desc}")
        lines.append(f"      Effect: {shadow['desc_full'].format(val=int(shadow['base_value']), pct=int(shadow['base_value'] * 100))}")
        lines.append("")
    return "\n".join(lines)


def trigger_shadow_choice(player, floor, term_func=None, count=1):
    """Present the player with Shadow choices and apply them.

    Args:
        player: player dict
        floor: current floor number
        term_func: optional function for getting terminal (for GUI mode)
        count: how many Shadows to pick (1 for floor 40, 2 for floor 46)

    Returns:
        str: display message about the choices
    """
    available = get_available_shadows(player)
    if not available:
        return "\n  All Shadows have already been chosen. Wonderland watches in silence."

    chosen_shadows = []
    result = []

    for pick_num in range(count):
        if not available:
            break

        display = build_shadow_choice_display(player, available)

        if count == 1:
            prompt_text = "Choose your Shadow (1-{0}): ".format(len(available))
        else:
            prompt_text = "Choose Shadow {0} of {1} (1-{2}): ".format(pick_num + 1, count, len(available))

        # Try GUI terminal first
        if term_func:
            t = term_func()
            if t:
                t.print(display)
                choice = t.menu(
                    [f"{s['icon']} {s['name']}" for s in available],
                    prompt=prompt_text.strip(),
                    allow_cancel=False,
                )
            else:
                print(display)
                try:
                    choice = int(input(prompt_text).strip()) - 1
                    if choice < 0 or choice >= len(available):
                        choice = 0
                except (ValueError, IndexError):
                    choice = 0
        else:
            print(display)
            try:
                choice = int(input(prompt_text).strip()) - 1
                if choice < 0 or choice >= len(available):
                    choice = 0
            except (ValueError, IndexError):
                choice = 0

        chosen = available[choice]
        player.setdefault("wonderland_shadows", []).append(chosen["key"])
        chosen_shadows.append(chosen)

        # Remove chosen from available for next pick
        available = [s for s in available if s["key"] != chosen["key"]]

    # Build result message
    result.append("")
    if count == 1:
        ch = chosen_shadows[0]
        result.append(f"  🌑 You have accepted the Shadow: {ch['icon']} {ch['name']}")
        result.append(f"  {ch['desc']}")
        result.append("")
        if floor <= 45:
            result.append(f"  ⚠️  This Shadow stacks with your previous choices.")
            result.append(f"  Shadows accumulate until Floor 46, when the slate is wiped clean.")
        else:
            result.append(f"  ⚠️  This Shadow will persist for ALL remaining floors.")
        result.append("")
    else:
        result.append(f"  🌑🌑 You have accepted TWO Shadows:")
        for ch in chosen_shadows:
            result.append(f"      {ch['icon']} {ch['name']} — {ch['desc']}")
        result.append("")
        if floor == 50:
            result.append(f"  ⚠️  These Shadows will directly empower Mary Sue.")
            result.append(f"  Each Shadow grants her a unique passive ability in the final battle.")
        elif floor == 46:
            result.append(f"  ⚠️  The slate is clean — these are your first Shadows in the new cycle.")
            result.append(f"  More Shadows will stack on Floors 47-49.")
        else:
            result.append(f"  ⚠️  These Shadows stack with your previous choices.")
            result.append(f"  On Floor 50, the slate will be wiped clean for the final choice.")
        result.append("")

    # Show Mary Sue foreshadowing
    for ch in chosen_shadows:
        ms_passive = ch.get("mary_sue_passive", {})
        if ms_passive:
            result.append(f"  📖 A page turns somewhere above... ({ch['icon']} {ms_passive.get('name', '')})")

    # ── Heroine reactions to the chosen Shadows ────────────────────────
    dialogue_lines = []
    for ally in player.get("allies", []):
        heroine_key = ally.get("_heroine_key")
        if heroine_key:
            for ch in chosen_shadows:
                dialogue = get_heroine_shadow_choice_dialogue(heroine_key, ch["key"])
                if dialogue:
                    dialogue_lines.append(f"\n  💬 [{ally['name']}] {dialogue}")
                    break  # One reaction per heroine

    if dialogue_lines:
        result.append("")
        result.append("  ── Heroine Reactions ──")
        result.extend(dialogue_lines)

    return "\n".join(result)


def format_active_shadows_line(player):
    """Format a line showing all active persistent Shadows."""
    shadows = get_player_shadows(player)
    if not shadows:
        return None
    lines = []
    for sk in shadows:
        sd = get_shadow_def(sk)
        if sd:
            lines.append(f"  {sd.get('icon', '🌑')} {sd['name']}")
    return "\n".join(lines)


def clear_all_shadows(player):
    """Remove all persistent Shadows from the player."""
    player.pop("wonderland_shadows", None)


# ═══════════════════════════════════════════════════════════════════════════════
# SHADOW EFFECT APPLICATION (for dungeon/combat integration)
# ═══════════════════════════════════════════════════════════════════════════════

def get_shadow_damage_taken_multiplier(player):
    """Off With Their Heads: bonus damage taken multiplier."""
    if has_shadow(player, "off_with_heads"):
        sd = get_shadow_def("off_with_heads")
        return sd["base_value"] if sd else 0
    return 0


def get_shadow_skip_chance(player):
    """Down the Rabbit Hole: lose-turn chance."""
    if has_shadow(player, "down_rabbit_hole"):
        sd = get_shadow_def("down_rabbit_hole")
        return sd["base_value"] if sd else 0
    return 0


def get_shadow_room_damage(player):
    """Jabberwock's Wrath: room-entry fire damage."""
    if has_shadow(player, "jabberwock_wrath"):
        sd = get_shadow_def("jabberwock_wrath")
        return sd["base_value"] if sd else 0
    return 0


def get_shadow_stat_penalty(player):
    """Madness Contagion: random stat penalty value."""
    if has_shadow(player, "madness_contagion"):
        sd = get_shadow_def("madness_contagion")
        return sd["base_value"] if sd else 0
    return 0


def get_shadow_healing_reduction(player):
    """Looking Glass Shatter: healing reduction multiplier."""
    if has_shadow(player, "looking_glass_shatter"):
        sd = get_shadow_def("looking_glass_shatter")
        return sd["base_value"] if sd else 0
    return 0


def get_shadow_accuracy_penalty(player):
    """Caterpillar's Smoke: accuracy penalty."""
    if has_shadow(player, "caterpillars_smoke"):
        sd = get_shadow_def("caterpillars_smoke")
        return sd["base_value"] if sd else 0
    return 0


def get_shadow_bleed_poison_extension(player):
    """Rose Wilt: extra bleed/poison duration."""
    if has_shadow(player, "rose_wilt"):
        sd = get_shadow_def("rose_wilt")
        return sd["base_value"] if sd else 0
    return 0


def get_shadow_gold_reduction(player):
    """White Rabbit's Panic: gold reduction multiplier."""
    if has_shadow(player, "white_rabbit_panic"):
        sd = get_shadow_def("white_rabbit_panic")
        return sd["base_value"] if sd else 0
    return 0


def get_shadow_initiative_bonus(player):
    """Cheshire Cat's Absence: enemy initiative bonus."""
    if has_shadow(player, "cheshire_absence"):
        sd = get_shadow_def("cheshire_absence")
        return sd["base_value"] if sd else 0
    return 0


def get_shadow_stat_check_dc_increase(player):
    """Author's Will: stat check DC increase."""
    if has_shadow(player, "authors_will"):
        sd = get_shadow_def("authors_will")
        return sd["base_value"] if sd else 0
    return 0


# ═══════════════════════════════════════════════════════════════════════════════
# MARY SUE SHADOW MODIFIERS (Floor 50)
# ═══════════════════════════════════════════════════════════════════════════════

def get_mary_sue_shadow_modifiers(player):
    """Return a dict of all Mary Sue passive modifiers based on player's Shadows.

    Returns:
        dict mapping passive effect keys to their definitions, or empty dict.
    """
    modifiers = {}
    shadows = get_player_shadows(player)
    for sk in shadows:
        sd = get_shadow_def(sk)
        if sd and "mary_sue_passive" in sd:
            mp = sd["mary_sue_passive"]
            modifiers[mp["effect"]] = mp
    return modifiers


def format_mary_sue_shadow_intro(player):
    """Build the intro text showing how Shadows empower Mary Sue on Floor 50."""
    modifiers = get_mary_sue_shadow_modifiers(player)
    if not modifiers:
        return None

    lines = []
    lines.append("")
    lines.append("  ╔" + "═" * 54 + "╗")
    lines.append("  ║  📖 THE SHADOWS AWAKEN...".ljust(55) + "║")
    lines.append("  ╠" + "═" * 54 + "╣")
    lines.append("  ║  Mary Sue looks at you — and through you.".ljust(55) + "║")
    lines.append("  ║  She sees the Shadows you carry. And she smiles.".ljust(55) + "║")
    lines.append("  ║" + " " * 54 + "║")
    for effect_key, mp in modifiers.items():
        name = mp.get("name", effect_key)
        desc = mp.get("desc", "")
        lines.append(f"  ║  🌑 {name}".ljust(55) + "║")
        while len(desc) > 50:
            split = desc.rfind(" ", 0, 50)
            if split == -1:
                split = 50
            lines.append(f"  ║     {desc[:split]}".ljust(55) + "║")
            desc = desc[split:].strip()
        if desc:
            lines.append(f"  ║     {desc}".ljust(55) + "║")
    lines.append("  ╚" + "═" * 54 + "╝")
    return "\n".join(lines)


def roll_d20_with_looking_glass(player, verbose=True):
    """Roll a d20 with Looking Glass Luck reroll chance.

    If Through the Looking Glass is active and the first roll is low,
    there's a chance to reroll once. Returns (final_roll, was_rerolled).

    Args:
        player: player dict
        verbose: if True, prints reroll messages

    Returns:
        (int, bool): final d20 result and whether a reroll occurred
    """
    roll = random.randint(1, 20)
    reroll_chance = get_looking_glass_reroll_chance(player)

    if reroll_chance > 0 and roll <= 10 and random.random() < reroll_chance:
        new_roll = random.randint(1, 20)
        if new_roll > roll:
            if verbose:
                from combat.combat_io import c_print
                c_print(f"  🪞 The Looking Glass ripples! {roll} → {new_roll}!")
            return new_roll, True
        elif verbose:
            from combat.combat_io import c_print
            c_print(f"  🪞 The Looking Glass flickers... but fate is stubborn. ({roll})")

    return roll, False

