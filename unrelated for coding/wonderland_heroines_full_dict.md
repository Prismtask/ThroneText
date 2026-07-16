# Wonderland Heroines — Full Data Dictionary

> Complete ally templates, dialogue trees, skill definitions, and wedding item designs
> for Alice, Red Hood, and Dorothy.

---

## Table of Contents

1. [Scaling & Mechanics](#1-scaling--mechanics)
2. [Alice — The Curious Dreamer](#2-alice--the-curious-dreamer)
3. [Red Hood — The Huntress of Endings](#3-red-hood--the-huntress-of-endings)
4. [Dorothy — The Girl from Kansas](#4-dorothy--the-girl-from-kansas)
5. [Wedding Flow for Heroines](#5-wedding-flow-for-heroines)
6. [Wedding Items](#6-wedding-items)
7. [Skill Definitions](#7-skill-definitions)
8. [Implementation Notes](#8-implementation-notes)

---

## 1. Scaling & Mechanics

### Temporary State (in Wonderland)

| Property | Formula |
|---|---|
| **Level** | Matches player level on join, frozen thereafter |
| **XP** | Does not gain XP |
| **Stats** | `max(1, int(base_mod + (join_level - 1) × 0.22))` — no 0.85 multiplier |
| **HP** | `base_hp + (join_level - 1) × 4` |
| **Equipment** | Cannot equip weapons/armor (accessories only) |
| **On Exit** | Leaves party — stored in `wonderland_benched_allies`, not in house |

### Permanent State (superboss defeated)

| Property | Formula |
|---|---|
| **Level** | Frozen at join level, now gains XP normally |
| **Stats** | Frozen at temp values; level-up bonuses apply going forward |
| **XP to Next** | Standard ally curve starting from 0 |
| **HP** | Same formula, `level_hp_bonus = (level - 1) × 4` |
| **Equipment** | Full: weapon, armor, accessory1, accessory2 |
| **Affection** | Starts at 60 (they chose to stay) |
| **House** | Lives in player's house like any monster girl |
| **On Exit** | Stays in party — survives leaving Wonderland |

### Permanent Unlock Trigger

```python
def promote_heroine_to_permanent(player, ally, join_level):
    ally["_wonderland_temp"] = False
    ally["_heroine_key"] = ally.get("_heroine_key")  # preserve
    ally["level"] = join_level
    ally["level_hp_bonus"] = (join_level - 1) * 4
    ally["exp"] = 0
    ally["affection"] = 60
    ally["affection_cap"] = 100
    ally["engaged"] = False
    ally["married"] = False
    ally["equipped"] = {"weapon": None, "armor": None, "accessory1": None, "accessory2": None}
    ally["captured_on"] = player.get("day", 1)
    # Stats already computed; keep them
```

### Mary Sue Fallback

Defeating Mary Sue (F50) with ANY heroine in party grants permanent status to ALL heroines in party — even if their individual superboss was skipped. She defeated the *author*, which supersedes individual storylines.

---

## 2. Alice — The Curious Dreamer

### 2.1 Ally Template

```yaml
wonderland_alice:
  name: Alice
  race: Fey
  secondary_race: Storybook
  _heroine_key: alice
  _wonderland_temp: true
  level: 1                       # Scales to player level on join
  base_hp: 20                    # HP = base_hp + (level - 1) × 4
  mods:
    Wisdom: 4
    Dexterity: 2
    Charisma: 2
    Strength: -1
    Constitution: 0
    Learning: 0
  boss: false
  super_boss: false
  monster_girl: true
  elemental_res:
    light: 1.3
    dark: 0.7
    magical: 1.1
  elemental_dmg:
    light: 1.2
    magical: 1.1
  skills:
    innate:
      - curious_inquiry
      - try_me
    permanent_unlock:
      - vorpal_instinct
    passive:
      - wonderland_logic
```

### 2.2 Full Python Dict (runtime ally object)

```python
ALICE_ALLY_TEMPLATE = {
    "name": "Alice",
    "key": "wonderland_alice",
    "_heroine_key": "alice",
    "_wonderland_temp": True,
    "race": "Fey",
    "secondary_race": "Storybook",
    "level": 1,                    # overwritten on join
    "base_hp": 20,
    "max_hp": 20,                  # computed on join
    "current_hp": 20,
    "mods": {
        "Wisdom": 4,
        "Dexterity": 2,
        "Charisma": 2,
        "Strength": -1,
        "Constitution": 0,
        "Learning": 0,
    },
    "elemental_res": {
        "light": 1.3,
        "dark": 0.7,
        "magical": 1.1,
    },
    "elemental_dmg": {
        "light": 1.2,
        "magical": 1.1,
    },
    "exp": 0,
    "affection": 50,               # starts warm — she chose to join
    "affection_cap": 100,
    "engaged": False,
    "married": False,
    "equipped": {
        "weapon": None,
        "armor": None,
        "accessory1": None,
        "accessory2": None,
    },
    "skills": ["curious_inquiry", "try_me"],
    "active_buffs": [],
    "active_debuffs": [],
    "skill_cooldowns": {},
    "defeated": False,
    "monster_girl": True,
    "captured": True,
    "boss": False,
    "super_boss": False,
}
```

### 2.3 Dialogue Tree

```python
ALICE_DIALOGUE = {
    # ── Recruitment (Mad Hatter's Inn) ──────────────────────────────────
    "recruit_intro": [
        "A girl with golden hair sits at the far end of the Mad Hatter's "
        "table, teacup in hand. She's not drinking — just staring into "
        "the tea as if it might reveal something. She looks up as you "
        "approach.",

        '"Oh! You\'re not from here, are you? I can tell. You walk like '
        'someone who expects the ground to stay where it is." '
        'She sets down the teacup. It keeps spinning.',

        '"I\'m Alice. I fell down a rabbit hole. That was... a long time '
        'ago? Or maybe tomorrow. It\'s hard to tell here." '
        'She gestures around the tea party. "I\'ve been trying to leave '
        'for ages. But the story won\'t let me go until I face IT."',

        'She looks at you — really looks. "You\'re going deeper, aren\'t '
        'you? Into the dungeon. Towards the Jabberwock." '
        'She takes a shaky breath. "Take me with you. Please. I\'ve been '
        'running from it for so long. I think... I think I\'m ready to stop."',
    ],

    "recruit_yes": [
        'Alice smiles — the first real smile you\'ve seen from her. '
        '"Thank you. I\'ll try to be useful. I\'m quite good at asking '
        'questions, and I\'ve had a LOT of practice with nonsense."',

        'She picks up her teacup. It stops spinning. '
        '"Let\'s go write a new chapter."',
    ],

    "recruit_no": [
        'Alice nods slowly. "I understand. It\'s a lot to ask. I\'ll... '
        'I\'ll be here. At this table. The tea is always hot and the '
        'company is always mad." She returns to staring into her cup.',
    ],

    "recruit_rejoin": [
        'Alice looks up from her teacup. "You came back. I was starting '
        'to think I\'d imagined you. That happens a lot here." '
        'She stands. "Are we finishing this?"',
    ],

    # ── Idle / Lounge Talk ─────────────────────────────────────────────
    "talk_1": [
        '"Do you ever wonder if we\'re characters in someone else\'s story? '
        'I used to think that was terrifying. Now I think it\'s... '
        'comforting? Someone is reading us. Someone cares how it ends."',
    ],
    "talk_2": [
        '"I tried to count the impossible things I believed today. '
        'I got to seven. The seventh was that you\'d actually win." '
        'She smiles. "I\'m glad I was right about that one."',
    ],
    "talk_3": [
        '"The Jabberwock writes in its sleep. Did you know that? Every '
        'nightmare it has becomes a new room in the dungeon. That\'s why '
        'the deeper floors don\'t make sense — they\'re someone else\'s bad dreams."',
    ],
    "talk_4": [
        '"I had a cat once. Dinah. She was very sensible. The Cheshire '
        'Cat is... not Dinah. He\'s the opposite of sensible. He\'s '
        'senseless. Which is almost the same word, isn\'t that odd?"',
    ],
    "talk_5": [
        '"The flowers here can talk. They\'re very rude. They told me '
        'my hair was the wrong shade of gold. I told them at least I '
        'HAVE hair. They didn\'t like that."',
    ],
    "talk_6": [
        '"I\'ve been keeping a journal. The pages keep rearranging '
        'themselves. Yesterday\'s entry is now about something that '
        'hasn\'t happened yet. Tomorrow\'s entry is blank — but it '
        'already has a conclusion." She shivers.',
    ],

    # ── Affection Milestones ───────────────────────────────────────────
    "affection_60": [
        '"You know, you\'re the first person here who\'s treated me like '
        'a person and not a character. It\'s... refreshing. And slightly '
        'terrifying. I\'m not sure I remember how to be a person."',
    ],
    "affection_80": [
        '"I had a dream last night. Not a Wonderland dream — a real one. '
        'We were sitting by a river, and the sky was the right colour, '
        'and nothing was trying to eat us. You were there. It was nice." '
        'She looks away. "I hope it was a prophecy."',
    ],
    "affection_100": [
        '"I\'ve finally figured it out. The reason I couldn\'t leave '
        'Wonderland wasn\'t the Jabberwock. It was me. I was waiting for '
        'someone worth leaving WITH." '
        'She takes your hand. "I think I found them."',
    ],

    # ── Gifts ──────────────────────────────────────────────────────────
    "gift_like": [
        '"Oh! This is lovely. It reminds me of something — I\'m not sure '
        'what. A memory that hasn\'t happened yet, perhaps."',
        '"How curious! I was just thinking about something like this. '
        'Were you reading my mind? That\'s very forward of you."',
    ],
    "gift_love": [
        '"This is... this is perfect. How did you know? No, don\'t tell '
        'me. I want it to remain a mystery. Mysteries are the best '
        'part of any story."',
        '"I\'ll treasure this. Really. In Wonderland, things have a way '
        'of disappearing when you stop paying attention. But I won\'t '
        'stop paying attention to this. Ever."',
    ],
    "gift_dislike": [
        '"Oh. Um. Thank you? I\'m sure it\'s very... practical. '
        'I\'ll put it somewhere safe. Somewhere I won\'t find it by accident."',
    ],

    # ── Kiss ───────────────────────────────────────────────────────────
    "kiss": [
        'Alice\'s eyes go wide. For a moment, all of Wonderland seems to '
        'hold its breath. Even the clocks stop ticking.',

        '"Oh," she whispers. "That was... that was the most sensible '
        'thing that\'s ever happened to me." '
        'She touches her lips, dazed. "Do it again?"',
    ],

    # ── Proposal ───────────────────────────────────────────────────────
    "proposal": [
        'You kneel in the middle of the Mad Hatter\'s tea party. The '
        'Hatter applauds. The March Hare throws a scone. The Dormouse '
        'wakes up just long enough to say "Finally!" and falls back asleep.',

        'Alice stares at the ring. Her teacup clatters to the saucer. '
        '"You\'re asking me? ME? The girl who followed a rabbit, who '
        'argued with flowers, who grew and shrank and grew again?"',

        'Tears well up in her eyes — real tears, not Wonderland tears '
        'that turn into butterflies. "Yes. Yes, of course yes. '
        'A thousand times yes. Or maybe once. Once is enough, if it\'s '
        'the right once."',

        'She slips the ring onto her finger. It fits perfectly — as if '
        'the story always knew this moment was coming.',
    ],

    "proposal_accepted": [
        'Alice looks at her hand as if seeing it for the first time. '
        '"I spent so long trying to get HOME. And now... now I AM home. '
        'You\'re my home. How wonderfully, impossibly curious."',
    ],

    # ── Wedding ────────────────────────────────────────────────────────
    "wedding_vows": [
        '"I, Alice, take you to be my wondering, my wandering, my always. '
        'I promise to believe six impossible things with you before '
        'breakfast every day. I promise to follow you down whatever '
        'rabbit hole you choose — and to always, always bring a spare '
        'teacup."',
    ],

    "wedding_gift": [
        'Alice hands you a small, wrapped package. Inside: a single '
        'teacup, impossibly warm. "This is from the tea party. The '
        'one that never ends. As long as this cup is warm, you\'ll '
        'always be welcome at the table. And so will I. Wherever we are."',

        'She fastens the Teacup Brooch to your collar. "There. Now '
        'you\'re part of the story. OUR story."',
    ],

    # ── Blessing ───────────────────────────────────────────────────────
    "blessing": [
        '"A blessing? I\'m not a fairy godmother. But I can give you '
        'something better — a question. The right question, at the '
        'right time. What would you like to ask the universe?"',
    ],

    "blessing_granted": [
        'Alice whispers something in your ear. It\'s not words exactly — '
        'more like the shape of an idea. You feel... clearer. Sharper. '
        'As if the nonsense of the world has parted, just a little, '
        'to let you see through.',
    ],

    # ── Combat ─────────────────────────────────────────────────────────
    "combat_start": [
        '"Curiouser and curiouser. Let\'s see what happens when we poke it."',
        '"Remember: nothing here plays by the rules. Including us."',
        '"I\'ve read about things like this. The book said \'run.\' '
        'I say \'let\'s rewrite that chapter.\'"',
    ],

    "combat_victory": [
        '"And they all lived — well, WE lived. The rest is optional."',
        '"Another page turned. I wonder what the next one says?"',
        '"That was almost fun. The almost is doing a lot of work there."',
    ],

    "combat_low_hp": [
        '"I\'m feeling a bit... small. Metaphorically. And possibly literally."',
        '"This isn\'t how the story is supposed to go!"',
    ],

    "combat_ally_defeated": [
        '"No! That\'s not — that can\'t be the ending!"',
    ],

    "combat_using_skill": [
        '"Let me ask you a question..."',
        '"One side makes you larger..."',
        '"I\'ve always wanted to try this!"',
    ],

    "is_recovered": [
        'Alice blinks. "Oh! I\'m back. Was I gone long? It felt like '
        'I was falling. But... sideways."',
    ],

    # ── Superboss-specific ─────────────────────────────────────────────
    "jabberwock_encounter": [
        'Alice goes very still. "It\'s him. The Jabberwock. I\'ve been '
        'running from him since I fell down the rabbit hole." '
        'She takes a shaky breath. "I\'m not running anymore."',
    ],

    "jabberwock_vorpal_hint": [
        '"The eyes! Aim for the eyes — that\'s where it keeps its plot holes!"',
    ],

    "jabberwock_whiffle_hint": [
        '"When it whiffles, don\'t attack — it\'ll just dance away. '
        'Wait. Then strike when it\'s catching its breath."',
    ],

    "jabberwock_burble_hint": [
        '"It\'s speaking in puns. Terrible, terrible puns. That\'s how '
        'it hunts — it confuses you until you don\'t know which way is forward."',
    ],

    "jabberwock_victory": [
        'Alice stands very still. The teacup she\'s been holding — you\'re '
        'not sure when she picked it up — has a crack in it.',

        '"It\'s over. It\'s really over." '
        'She reads the vanishing ink on the floor. Her expression flickers. '
        '"It says... \'To be continued.\'" '
        'She looks at you. "That\'s not ominous at all."',

        '→ Alice becomes a permanent ally.',
    ],

    # ── Permanent unlock dialogue ──────────────────────────────────────
    "permanent_unlock": [
        '"The sentence is complete. Full stop. ... I think I can leave now. '
        'Not just the dungeon — Wonderland itself. If you\'ll have me."',
    ],

    # ── Idle in House ──────────────────────────────────────────────────
    "house_idle_1": [
        'Alice is reading a book upside-down. "The story makes more '
        'sense this way," she explains earnestly.',
    ],
    "house_idle_2": [
        'Alice has set up a small tea party in the corner. Three cups '
        'are laid out. "One for you, one for me, and one for whoever '
        'shows up. Someone always shows up."',
    ],
    "house_idle_3": [
        'Alice is practicing curtsies. "The Red Queen said my form '
        'was atrocious. I\'m inclined to agree, which makes me very angry."',
    ],
}
```

### 2.4 Affection Item Preferences

| Category | Items |
|---|---|
| **Loves (+5–7)** | Teacups, books, pocket watches, mushrooms, chess pieces, ribbons, poetry scrolls, anything "curious" or "impossible" |
| **Likes (+3–4)** | Flowers (especially roses), cakes, potions ("drink me" style), quills, ink |
| **Neutral (+1–2)** | Standard gifts, most food, accessories |
| **Dislikes (–1–3)** | Weapons (violent things), armour (too heavy), anything "boring" or "practical" |

---

## 3. Red Hood — The Huntress of Endings

### 3.1 Ally Template

```yaml
wonderland_red_hood:
  name: Red Hood
  race: Beast
  secondary_race: Storybook
  _heroine_key: red_hood
  _wonderland_temp: true
  level: 1                       # Scales to player level on join
  base_hp: 24                    # HP = base_hp + (level - 1) × 4
  mods:
    Strength: 3
    Dexterity: 3
    Constitution: 2
    Wisdom: -1
    Charisma: 1
    Learning: 0
  boss: false
  super_boss: false
  monster_girl: true
  elemental_res:
    physical: 1.1
    dark: 0.8
    earth: 1.1
  elemental_dmg:
    physical: 1.15
    fire: 1.1
  skills:
    innate:
      - hunters_mark
      - whats_in_the_basket
    permanent_unlock:
      - grandmothers_lesson
    passive:
      - woodcutter_training
```

### 3.2 Full Python Dict (runtime ally object)

```python
RED_HOOD_ALLY_TEMPLATE = {
    "name": "Red Hood",
    "key": "wonderland_red_hood",
    "_heroine_key": "red_hood",
    "_wonderland_temp": True,
    "race": "Beast",
    "secondary_race": "Storybook",
    "level": 1,                    # overwritten on join
    "base_hp": 24,
    "max_hp": 24,                  # computed on join
    "current_hp": 24,
    "mods": {
        "Strength": 3,
        "Dexterity": 3,
        "Constitution": 2,
        "Wisdom": -1,
        "Charisma": 1,
        "Learning": 0,
    },
    "elemental_res": {
        "physical": 1.1,
        "dark": 0.8,
        "earth": 1.1,
    },
    "elemental_dmg": {
        "physical": 1.15,
        "fire": 1.1,
    },
    "exp": 0,
    "affection": 45,               # cautious — she's been betrayed by stories before
    "affection_cap": 100,
    "engaged": False,
    "married": False,
    "equipped": {
        "weapon": None,
        "armor": None,
        "accessory1": None,
        "accessory2": None,
    },
    "skills": ["hunters_mark", "whats_in_the_basket"],
    "active_buffs": [],
    "active_debuffs": [],
    "skill_cooldowns": {},
    "defeated": False,
    "monster_girl": True,
    "captured": True,
    "boss": False,
    "super_boss": False,
}
```

### 3.3 Dialogue Tree

```python
RED_HOOD_DIALOGUE = {
    # ── Recruitment (Mad Hatter's Inn) ──────────────────────────────────
    "recruit_intro": [
        "A young woman in a crimson cloak sits apart from the tea party, "
        "her back to the wall. A woodsman's axe leans against her chair. "
        "She's sharpening it with slow, deliberate strokes. She doesn't "
        "look up as you approach — but she knows you're there.",

        '"I\'m not lost, if that\'s what you\'re going to ask. I know '
        'exactly where I am. I\'m exactly where the wolf is." '
        'She tests the axe\'s edge with her thumb. "Calls himself '
        '\'The Big Bad.\' Thinks he\'s clever because he ate the original '
        'ending to my story."',

        '"I\'ve tracked him through three forests, two dreams, and '
        'a chapter that hasn\'t been written yet. He\'s down there — in '
        'the dungeon. Waiting." '
        'She finally looks at you. Her eyes are the colour of old blood. '
        '"You\'re going down there. I can smell the dungeon on you. '
        'Take me with you. I\'ll watch your back. But when we find '
        'the Wolf — he\'s mine."',
    ],

    "recruit_yes": [
        'Red Hood stands. The axe comes up to rest on her shoulder. '
        '"Good. Don\'t get in my way, and I won\'t get in yours. '
        'Fair warning: I don\'t trust easily. Stories have a way of '
        'betraying you. But you... you smell like an original. '
        'Not a rewrite. Let\'s hunt."',
    ],

    "recruit_no": [
        'Red Hood\'s expression doesn\'t change. "Your choice. The Wolf '
        'will still be down there when you change your mind. He\'s '
        'patient. So am I." She resumes sharpening her axe.',
    ],

    "recruit_rejoin": [
        'She looks up from her axe. "Changed your mind? Good. The trail '
        'doesn\'t get any warmer." She shoulders the axe. "Let\'s go."',
    ],

    # ── Idle / Lounge Talk ─────────────────────────────────────────────
    "talk_1": [
        '"My grandmother taught me to hunt. She said: \'The forest '
        'doesn\'t care if you\'re a little girl. It will eat you just '
        'the same.\' She was right. About everything."',
    ],
    "talk_2": [
        '"The Wolf ate my story\'s ending. Did you know that? Not '
        'grandmother — the ENDING. The part where the woodsman saves '
        'me. It\'s gone. That\'s why I carry the axe now. I\'m my own '
        'woodsman."',
    ],
    "talk_3": [
        '"I don\'t sleep much. When I do, I dream of teeth. Not the '
        'Wolf\'s teeth — my own. I think that means I\'m becoming '
        'something. I\'m not sure what."',
    ],
    "talk_4": [
        '"The basket. Everyone asks about the basket. It\'s just bread '
        'and wine. Grandmother\'s recipe. The wine is for celebrating. '
        'We haven\'t had cause to open it yet."',
    ],
    "talk_5": [
        '"I met a girl once who talked to wolves. Called them her '
        'brothers. I didn\'t understand it then. I think I do now. '
        'We\'re all a little bit wolf, under the skin."',
    ],

    # ── Affection Milestones ───────────────────────────────────────────
    "affection_60": [
        '"You\'re still here. Most people leave when they realize I\'m '
        'not... soft. That I don\'t know how to be gentle. But you '
        'stayed. Why?" '
        'She doesn\'t wait for an answer. "Whatever the reason... '
        'thank you."',
    ],
    "affection_80": [
        '"I was wrong about you. You\'re not just another character in '
        'someone else\'s story. You\'re... real. The realest thing '
        'I\'ve found since I fell into this place." '
        'She hesitates, then: "If anything happens to you... I\'ll '
        'burn this whole book to the ground."',
    ],
    "affection_100": [
        '"The Wolf ate my ending. But you... you gave me a new one. '
        'A better one. One where I choose who I walk through the '
        'woods with." '
        'She takes off her hood — a gesture of vulnerability you\'ve '
        'never seen from her. "I choose you."',
    ],

    # ── Gifts ──────────────────────────────────────────────────────────
    "gift_like": [
        '"Practical. I like practical. Thank you."',
        '"This will serve well. In the forest or the dungeon. Good eye."',
    ],
    "gift_love": [
        '"This is... grandmother would have loved this. Where did you '
        'find it?" She holds it carefully, as if it might break. '
        'She doesn\'t treat many things that way.',
        '"You actually listen. When I talk about my grandmother, about '
        'the forest, about what I miss. You LISTEN." She looks away. '
        '"That\'s rarer than you think."',
    ],
    "gift_dislike": [
        '"Pretty. Useless, but pretty. I\'ll put it somewhere safe." '
        'You suspect "somewhere safe" means "somewhere I won\'t have to look at it."',
    ],

    # ── Kiss ───────────────────────────────────────────────────────────
    "kiss": [
        'Red Hood goes rigid. For a terrifying moment, you think '
        'she\'s going for her axe.',

        'Then she exhales — a long, shaky breath, like someone who\'s '
        'been holding it for years. "No one\'s ever..." '
        'She doesn\'t finish. Instead, she kisses you back. Hard. '
        '"Don\'t you dare get eaten by anything. That\'s an order."',
    ],

    # ── Proposal ───────────────────────────────────────────────────────
    "proposal": [
        'You find her at the edge of the Tulgey Wood, axe in hand, '
        'watching the treeline. "The Wolf is dead," you remind her. '
        '"I know," she says. "Old habits."',

        'You kneel. In the dirt. In the dark. In the one place she '
        'feels most at home.',

        'She stares at the ring. Then at you. Then at the ring again. '
        '"Is this a trick? Some kind of storybook magic?" '
        'You shake your head. "It\'s real. I\'m real. This is real."',

        'She doesn\'t cry. Red Hood doesn\'t cry. But her voice cracks '
        'when she says: "Then yes. A thousand times yes. But I\'m '
        'keeping the axe. And the hood. And you\'re not allowed to '
        'get eaten. Ever. Those are my conditions."',
    ],

    "proposal_accepted": [
        'She slides the ring onto her finger. It catches the light '
        'filtering through the twisted trees. "Grandmother always '
        'said I\'d find someone who wasn\'t afraid of the woods. '
        'She was right. She was always right."',
    ],

    # ── Wedding ────────────────────────────────────────────────────────
    "wedding_vows": [
        '"I, Red Hood, take you as my pack, my hearth, my home. '
        'I will walk through every dark forest at your side. I will '
        'face every wolf that dares cross our path. And if anyone — '
        'ANYONE — tries to hurt you, they\'ll learn what the Big Bad '
        'Wolf learned: I don\'t miss."',
    ],

    "wedding_gift": [
        'Red Hood hands you a small bundle wrapped in oilcloth. Inside: '
        'a strip of crimson fabric, still warm. "A piece of my hood. '
        'As long as you wear it, I\'ll always find my way back to you. '
        'No matter how dark the woods get."',

        'She ties the Crimson Clasp around your wrist. "There. Now '
        'you\'re pack. And pack doesn\'t leave pack behind."',
    ],

    # ── Blessing ───────────────────────────────────────────────────────
    "blessing": [
        '"A blessing? Grandmother used to say a blessing before I went '
        'into the woods. \'May your eyes be sharp and your axe sharper.\' '
        'Close your eyes. Let me do the same for you."',
    ],

    "blessing_granted": [
        'Red Hood rests the flat of her axe blade on your shoulder — '
        'a woodsman\'s benediction. "There. Now the forest knows you\'re '
        'under my protection. The trees will whisper warnings. The '
        'path will clear before you. And the wolves... the wolves '
        'will think twice."',
    ],

    # ── Combat ─────────────────────────────────────────────────────────
    "combat_start": [
        '"Finally. I was getting bored."',
        '"Remember: go for the throat. Everything has a throat."',
        '"Stay behind me. Or don\'t. I\'m not your mother."',
    ],

    "combat_victory": [
        '"And stay down."',
        '"That\'s one less monster in the woods."',
        '"Good fight. Now let\'s find something to eat."',
    ],

    "combat_low_hp": [
        '"I\'ve had worse. That time with the bear, for instance."',
        '"Is that all you\'ve got? My GRANDMOTHER hits harder."',
    ],

    "combat_ally_defeated": [
        '"NO! Get up! That\'s an ORDER!"',
    ],

    "combat_using_skill": [
        '"I see you."',
        '"This is from grandmother."',
        '"Marked. Now finish it."',
    ],

    "is_recovered": [
        'Red Hood sits up sharply, hand already reaching for her axe. '
        '"How long was I out? What did I miss? Is it dead?"',
    ],

    # ── Superboss-specific ─────────────────────────────────────────────
    "big_bad_wolf_encounter": [
        'Red Hood goes very still. "There you are. I\'ve been looking '
        'for you for a VERY long time." '
        'Her knuckles go white on the axe handle. "This ends now."',
    ],

    "big_bad_wolf_deception_hint": [
        '"Don\'t believe a word he says. Especially the polite ones. '
        'He\'s testing who you\'ll try to protect."',
    ],

    "big_bad_wolf_victory": [
        'Red Hood steps forward. She\'s shaking — not from fear. '
        'From release.',

        '"That\'s for grandmother." '
        'She swings her axe. '
        '"And for every little girl who walked through the woods alone."',

        'The axe bites. The Wolf exhales. Stillness.',

        '→ Red Hood gains +1 permanent Strength. '
        '→ Red Hood becomes a permanent ally.',
    ],

    # ── Permanent unlock dialogue ──────────────────────────────────────
    "permanent_unlock": [
        '"The original ending. He ate it, you know. But he never '
        'digested it." '
        'She tucks a tattered page away. '
        '"The story\'s done. I\'m free. And... I owe you for that." '
        '"Where to next?"',
    ],

    # ── Idle in House ──────────────────────────────────────────────────
    "house_idle_1": [
        'Red Hood is doing maintenance on her axe. The whetstone '
        'makes a rhythmic shhhk, shhhk sound. "A dull blade is '
        'a dead woodsman," she says without looking up.',
    ],
    "house_idle_2": [
        'Red Hood is baking bread. The kitchen smells amazing. '
        '"Grandmother\'s recipe," she says gruffly. "Don\'t tell anyone."',
    ],
    "house_idle_3": [
        'Red Hood sits by the window, watching the treeline. Old '
        'habits. But her axe is propped against the wall, not in her '
        'lap. Progress.',
    ],
}
```

### 3.4 Affection Item Preferences

| Category | Items |
|---|---|
| **Loves (+5–7)** | Whetstones, sharpening kits, dried meat, sturdy boots, oil for weapons, grandmother's recipes, wolf pelts |
| **Likes (+3–4)** | Practical tools, camping gear, warm cloaks, bread, wine, hunting trophies |
| **Neutral (+1–2)** | Standard gifts, most food, simple accessories |
| **Dislikes (–1–3)** | Frilly things, "useless decorations," anything pink and delicate, tea sets |

---

## 4. Dorothy — The Girl from Kansas

### 4.1 Ally Template

```yaml
wonderland_dorothy:
  name: Dorothy
  race: Human
  secondary_race: Storybook
  _heroine_key: dorothy
  _wonderland_temp: true
  level: 1                       # Scales to player level on join
  base_hp: 22                    # HP = base_hp + (level - 1) × 4
  mods:
    Charisma: 3
    Wisdom: 3
    Constitution: 2
    Dexterity: 2
    Strength: 0
    Learning: 2
  boss: false
  super_boss: false
  monster_girl: true
  elemental_res:
    wind: 1.3
    dark: 0.7
    earth: 1.1
  elemental_dmg:
    water: 1.2
    light: 1.15
    wind: 1.1
  skills:
    innate:
      - no_place_like_home
      - ruby_blink
    permanent_unlock:
      - somewhere_over_rainbow
    passive:
      - totos_nose
```

### 4.2 Full Python Dict (runtime ally object)

```python
DOROTHY_ALLY_TEMPLATE = {
    "name": "Dorothy",
    "key": "wonderland_dorothy",
    "_heroine_key": "dorothy",
    "_wonderland_temp": True,
    "race": "Human",
    "secondary_race": "Storybook",
    "level": 1,                    # overwritten on join
    "base_hp": 22,
    "max_hp": 22,                  # computed on join
    "current_hp": 22,
    "mods": {
        "Charisma": 3,
        "Wisdom": 3,
        "Constitution": 2,
        "Dexterity": 2,
        "Strength": 0,
        "Learning": 2,
    },
    "elemental_res": {
        "wind": 1.3,
        "dark": 0.7,
        "earth": 1.1,
    },
    "elemental_dmg": {
        "water": 1.2,
        "light": 1.15,
        "wind": 1.1,
    },
    "exp": 0,
    "affection": 55,               # warmest start — she's the most trusting
    "affection_cap": 100,
    "engaged": False,
    "married": False,
    "equipped": {
        "weapon": None,
        "armor": None,
        "accessory1": None,
        "accessory2": None,
    },
    "skills": ["no_place_like_home", "ruby_blink"],
    "active_buffs": [],
    "active_debuffs": [],
    "skill_cooldowns": {},
    "defeated": False,
    "monster_girl": True,
    "captured": True,
    "boss": False,
    "super_boss": False,
    "_toto_present": True,         # flavour — Toto is always with her
}
```

### 4.3 Dialogue Tree

```python
DOROTHY_DIALOGUE = {
    # ── Recruitment (Mad Hatter's Inn) ──────────────────────────────────
    "recruit_intro": [
        "A young woman sits by the window, a pair of ruby slippers on "
        "the table before her. She's not wearing them — just looking "
        "at them, her expression distant. A small black dog sleeps at "
        "her feet. He lifts his head as you approach, wags his tail "
        "once, and goes back to sleep.",

        '"They say these can take me home. Three clicks and I\'d be '
        'back in Kansas. But every time I try... I end up somewhere '
        'worse." '
        'She looks up at you. Her eyes are tired but not defeated.',

        '"Are you real? You don\'t look like the others. The ones SHE '
        'writes. You look like... someone who actually CHOOSES where '
        'they\'re going."',

        '"The one with the pen. She wrote a witch for me to fight, '
        'and a wizard to disappoint me, and a road that never really '
        'ends. I\'ve walked it six times now. It changes, but it '
        'never... stops."',

        '"More than anything, I want to go home. But I think... I think '
        'I CAN\'T go home until I finish the story. And the story wants '
        'me to kill a witch." She glances at the slippers. "These won\'t '
        'work until I do."',

        'She studies you for a long moment. Toto lifts his head again, '
        'barks once, and settles. "Toto says you\'re okay. And Toto\'s '
        'never wrong about people." '
        'She picks up the slippers — but puts them in her bag, not on '
        'her feet. "Lead the way. But if we see a witch... I\'m not running."',
    ],

    "recruit_yes": [
        'Dorothy stands, slinging her bag over her shoulder. Toto '
        'jumps up, suddenly very awake. "I\'ve been walking this road '
        'alone for so long. It\'ll be nice to have company. Real '
        'company. Not scarecrows or tin men or lions who run away." '
        'She scratches behind Toto\'s ears. "We\'re ready. Let\'s go '
        'find this witch."',
    ],

    "recruit_no": [
        'Dorothy\'s face falls, but she nods. "I understand. It\'s '
        'dangerous. The Witch is... she\'s worse than the stories say. '
        'I\'ll wait here. The road isn\'t going anywhere. It never does." '
        'Toto whines softly.',
    ],

    "recruit_rejoin": [
        'Dorothy brightens when she sees you. "You came back! Toto, '
        'look — they came back!" Toto runs in a happy circle. "Are we '
        'doing this? Together?"',
    ],

    # ── Idle / Lounge Talk ─────────────────────────────────────────────
    "talk_1": [
        '"Back in Kansas, we had tornadoes. Big ones. Everyone was '
        'terrified of them. But after walking the Yellow Brick Road '
        'six times, a tornado seems almost... quaint. At least '
        'tornadoes END."',
    ],
    "talk_2": [
        '"I had friends, once. A scarecrow who wanted a brain, a tin '
        'man who wanted a heart, a lion who wanted courage. They were '
        'wonderful. They were also... written. I don\'t know if they '
        'were ever real. That\'s the worst part. Not knowing."',
    ],
    "talk_3": [
        '"Toto knows things. I don\'t know how. He just looks at '
        'someone and he KNOWS. He\'s never wrong. He says you\'re '
        'good people. The best people. I agree."',
    ],
    "talk_4": [
        '"The Wizard was just a man behind a curtain. That was the '
        'big secret. He couldn\'t give anyone anything they didn\'t '
        'already have. I think... maybe that\'s the point. Maybe '
        'we all have what we need. We just need someone to pull '
        'back the curtain."',
    ],
    "talk_5": [
        '"I miss wheat fields. I miss the smell of rain on dry earth. '
        'I miss Aunt Em\'s cooking. I miss boring, ordinary, wonderful '
        'things. Do you ever miss things that aren\'t magical at all?"',
    ],
    "talk_6": [
        '"The Witch of the West... she\'s not like the others. The '
        'other witches were just doing their jobs — being wicked '
        'because the story said so. But HER? She ENJOYS it. She\'s '
        'been waiting for me. Preparing. She\'s made this personal."',
    ],

    # ── Affection Milestones ───────────────────────────────────────────
    "affection_60": [
        '"I used to click my heels every night before bed. Just in '
        'case. Three clicks — there\'s no place like home. It never '
        'worked. But since I met you... I don\'t click them as often. '
        'I think that means something."',
    ],
    "affection_80": [
        '"You know what I realized? Home isn\'t a place. It\'s... '
        'people. Aunt Em was home. Toto is home. And... and you. '
        'You\'re starting to feel like home too. Is that strange?"',
    ],
    "affection_100": [
        'Dorothy takes out the ruby slippers. She looks at them for '
        'a long moment. Then she puts them back in her bag. '
        '"I could go home now. I can feel it — Kansas is right there, '
        'three clicks away. But my home doesn\'t have you in it. ',
        'And that\'s not a home I want anymore."',
    ],

    # ── Gifts ──────────────────────────────────────────────────────────
    "gift_like": [
        '"Oh, this is lovely! It reminds me of something Aunt Em '
        'would have — oh! Thank you!"',
        '"How thoughtful! Toto, look what they gave me!" Toto barks '
        'approvingly.',
    ],
    "gift_love": [
        '"This is... this is perfect. It feels like home. I know that '
        'sounds silly — how can a THING feel like home? But this does. '
        'Thank you. Truly."',
        '"You remembered. You remembered what I said about Kansas, '
        'about the wheat fields, about... me. No one\'s ever remembered '
        'before." Her eyes are wet. "Thank you."',
    ],
    "gift_dislike": [
        '"Oh. Um. That\'s... very green. The Witch wore a lot of green. '
        'I\'m not fond of green." She forces a smile. "But thank you '
        'for thinking of me!"',
    ],

    # ── Kiss ───────────────────────────────────────────────────────────
    "kiss": [
        'Dorothy\'s cheeks flush bright red. Toto barks — once, sharply, '
        'as if to say "finally!"',

        '"Oh my," she breathes. "That was... that was better than '
        'a Kansas sunrise. And I REALLY like Kansas sunrises." '
        'She giggles nervously. "Can we... can we do that again? '
        'I want to make sure it\'s real."',
    ],

    # ── Proposal ───────────────────────────────────────────────────────
    "proposal": [
        'You find her in a quiet corner of the inn, Toto asleep in '
        'her lap. She\'s humming something — an old song, something '
        'about rainbows and bluebirds.',

        'You kneel. Toto wakes up. He watches with keen interest.',

        '"What are you — oh. OH." '
        'Her hands fly to her mouth. The ruby slippers on the table '
        'begin to glow — faintly, softly, like embers.',

        '"You\'re asking me to stay? HERE? With YOU?" '
        'Tears — happy tears, Kansas tears, real tears — spill down '
        'her cheeks. "But what about home? What about Kansas?"',

        '"Dorothy," you say, "you ARE home."',

        'She looks at the ruby slippers. Then at you. Then at the '
        'ring. Then at Toto, who barks once — his vote is clear.',

        '"Yes. Yes, a thousand times yes. I don\'t need three clicks. '
        'I don\'t need a wizard. I just need you."',
    ],

    "proposal_accepted": [
        'The ruby slippers stop glowing. They\'re just shoes now. '
        'Beautiful, priceless shoes — but just shoes. '
        '"I guess they finally got me where I needed to go," Dorothy '
        'whispers. "Not to Kansas. To you."',
    ],

    # ── Wedding ────────────────────────────────────────────────────────
    "wedding_vows": [
        '"I, Dorothy Gale, take you to be my home. Not the place '
        'I\'m from, but the place I belong. I promise to walk every '
        'road with you — yellow brick or otherwise. I promise to '
        'face every witch, every wizard, every tornado. And I promise '
        'that wherever you are, that\'s where my heart will click its '
        'heels and say: there\'s no place like here. There\'s no place '
        'like you."',
    ],

    "wedding_gift": [
        'Dorothy hands you a small velvet pouch. Inside: a charm — '
        'a tiny pair of ruby slippers on a silver chain. '

        '"These are a replica. The originals only work for me. But '
        'these... these will remind you that you always have a way '
        'home. Because home is wherever we are. Together."',

        'She fastens the "There\'s No Place" Charm around your neck. '
        '"There. Now you\'re never lost. No matter how far the '
        'tornado takes you."',
    ],

    # ── Blessing ───────────────────────────────────────────────────────
    "blessing": [
        '"A blessing? Well, Aunt Em always said: \'The Lord bless '
        'you and keep you.\' But I think... I think a blessing should '
        'be personal. Let me try." '
        'She closes her eyes.',
    ],

    "blessing_granted": [
        '"There\'s no place like home," Dorothy whispers. "And there\'s '
        'no one like you. May the road rise to meet you. May the wind '
        'be always at your back. May the witches tremble at your name. '
        'And may you always, ALWAYS find your way back."',
    ],

    # ── Combat ─────────────────────────────────────────────────────────
    "combat_start": [
        '"Here we go again. Toto, stay close."',
        '"I\'ve faced witches. This is nothing."',
        '"Remember what the Scarecrow said: use your brain!"',
    ],

    "combat_victory": [
        '"And that\'s how we do it in Kansas!"',
        '"Another one down. Are you okay? Everyone okay?"',
        '"Toto, we\'re not in Kansas anymore — and thank goodness for that!"',
    ],

    "combat_low_hp": [
        '"I\'m not giving up. I walked the Yellow Brick Road SIX TIMES. '
        'This is nothing!"',
        '"Aunt Em always said I was too stubborn to quit. She was right."',
    ],

    "combat_ally_defeated": [
        '"NO! Get away from them! TOTO, BITE!"',
    ],

    "combat_using_skill": [
        '"There\'s no place like home!"',
        '"Click your heels — oh wait, that\'s me!"',
        '"Close your eyes and tap your heels together..."',
    ],

    "is_recovered": [
        'Dorothy stirs. "Aunt Em? Is that — oh. Oh, it\'s you. '
        'I was dreaming about Kansas. About home. But you know what? '
        'I\'m glad I woke up here instead."',
    ],

    # ── Superboss-specific ─────────────────────────────────────────────
    "wicked_witch_encounter": [
        'Dorothy freezes. "It\'s her. The Wicked Witch of the West. '
        'She\'s been waiting for me. All this time — she KNEW I\'d '
        'come back." '
        'Toto growls low in his throat. "But I\'m not the scared '
        'little girl she remembers. I\'m not alone anymore."',
    ],

    "wicked_witch_fear_hint": [
        '"Don\'t listen to her. She wants you to run. That\'s when '
        'she\'s most dangerous."',
    ],

    "wicked_witch_water_hint": [
        '"Water! She can\'t stand water! Back in Kansas, we called '
        'this a twister — but a rainstorm works just as well!"',
    ],

    "wicked_witch_landing_hint": [
        '"She always sends the monkeys first. She\'s afraid to get '
        'her hands dirty — that\'s her weakness! When she lands to '
        'catch her breath, her magic wavers. That\'s when you strike."',
    ],

    "wicked_witch_victory": [
        'Dorothy steps forward, ruby slippers gleaming — no longer '
        'on the table, but on her feet.',

        '"She\'s gone. She\'s really gone." '
        'She clicks her heels once. Nothing happens. '
        'She clicks them twice. A warm breeze stirs. '
        'She doesn\'t click them a third time.',

        '"I could go home now. I can feel it — Kansas is right there, '
        'three clicks away. But..." '
        'She looks at you. Toto barks. '
        '"You\'re not from Kansas. And you\'re still fighting. Maybe... '
        'maybe home can wait. Just a little longer."',

        '→ Dorothy becomes a permanent ally.',
    ],

    # ── Permanent unlock dialogue ──────────────────────────────────────
    "permanent_unlock": [
        '"I could go home now. But you ARE home. And I\'m not leaving '
        'you. Not ever."',
    ],

    # ── Idle in House ──────────────────────────────────────────────────
    "house_idle_1": [
        'Dorothy is teaching Toto a new trick. "Roll over! Roll over, '
        'Toto!" Toto yawns and goes back to sleep. "We\'re... still '
        'working on it."',
    ],
    "house_idle_2": [
        'Dorothy is baking. The kitchen smells of fresh bread and '
        'cinnamon. "Aunt Em\'s recipe. Well, my best guess at it. '
        'Kansas ingredients are hard to find here. Want to try?"',
    ],
    "house_idle_3": [
        'Dorothy sits by the window, humming "Somewhere Over the '
        'Rainbow." The ruby slippers are on the mantle, gathering '
        'dust. She hasn\'t worn them in weeks.',
    ],
}
```

### 4.4 Affection Item Preferences

| Category | Items |
|---|---|
| **Loves (+5–7)** | Anything from "home" — apple pie, gingham fabric, wheat, sunflowers, lullabies, warm blankets, anything that smells like rain |
| **Likes (+3–4)** | Practical clothing, bread, cheese, books about faraway places, dog treats (for Toto), baskets |
| **Neutral (+1–2)** | Standard gifts, most accessories, flowers |
| **Dislikes (–1–3)** | Anything green (the Witch's colour), anything sinister or dark, masks |

---

## 5. Wedding Flow for Heroines

### 5.1 Differences from Monster Girl Wedding

Heroines follow the same affection/engagement/wedding flow as monster girls but with key differences:

| Aspect | Monster Girls | Heroines |
|---|---|---|
| **Recruitment** | Captured in combat → recruited at affection 50+ | Join via story dialogue at Mad Hatter's Inn |
| **Affection Start** | Varies (usually 30) | Alice: 50, Red Hood: 45, Dorothy: 55 |
| **Engagement Ring** | Any of 6 rings from Gift Shop | Requires a STORY-SPECIFIC ring (see below) |
| **Wedding Item** | `wedding_<girl_key>` with `special` field | Custom named item with `special` field |
| **Soulbound** | Yes | Yes |
| **House Residence** | Lives in player's house | Lives in player's house after permanent unlock |
| **Prerequisite** | Affection 100 + engagement ring | Affection 100 + story ring + superboss defeated (permanent) |

### 5.2 Story-Specific Engagement Rings

Each heroine requires a unique ring — not the generic Gift Shop rings. These are **crafted or found**:

| Heroine | Ring | How to Obtain |
|---|---|---|
| **Alice** | **Curiouser Ring** (`alice_engagement_ring`) | Found in a hidden room in the Storybook Dungeon (F25–F32 tier), or crafted at Blacksmith using `wonderland_teacup_fragment` + gold |
| **Red Hood** | **Crimson Promise Ring** (`red_hood_engagement_ring`) | Dropped by Big Bad Wolf (guaranteed on first kill if Red Hood is in party) |
| **Dorothy** | **Kansas Heart Ring** (`dorothy_engagement_ring`) | Dropped by Wicked Witch (guaranteed on first kill if Dorothy is in party) |

```python
# resources/items.py additions

"alice_engagement_ring": {
    "name": "Curiouser Ring",
    "type": "equipment",
    "slot": "accessory",
    "unique": True,
    "base_mods": {"Wisdom": 4, "Charisma": 2},
    "elemental_dmg": {"light": 1.15, "magical": 1.1},
    "description": "A ring that seems to grow and shrink as you look at it. 'Wear me,' it whispers.",
    "heroine_ring_for": "alice",
},

"red_hood_engagement_ring": {
    "name": "Crimson Promise Ring",
    "type": "equipment",
    "slot": "accessory",
    "unique": True,
    "base_mods": {"Strength": 4, "Constitution": 2},
    "elemental_dmg": {"physical": 1.15, "fire": 1.1},
    "description": "Forged from the tooth of the Big Bad Wolf. Still faintly warm with swallowed stories.",
    "heroine_ring_for": "red_hood",
},

"dorothy_engagement_ring": {
    "name": "Kansas Heart Ring",
    "type": "equipment",
    "slot": "accessory",
    "unique": True,
    "base_mods": {"Charisma": 4, "Wisdom": 2},
    "elemental_dmg": {"water": 1.15, "light": 1.1},
    "description": "A simple silver band set with a chip of ruby. It smells faintly of wheat fields and rain.",
    "heroine_ring_for": "dorothy",
},
```

### 5.3 Proposal Flow

```
1. Heroine reaches affection 100
2. Player possesses the correct story ring
3. "Propose marriage" option appears in lounge menu
4. Unique proposal dialogue plays (see dialogue trees above)
5. On acceptance:
   - Ring is consumed (removed from inventory)
   - Heroine gains `engaged = True`
   - `ring_stat_bonus` is applied to the heroine
   - Affection cap increases to 150
6. Wedding can occur after a waiting period (3–7 days, same as monster girls)

7. On wedding:
   - Heroine gains `married = True`
   - Wedding item is added to player inventory (soulbound)
   - Heroine gains `matriarchs_embrace` equivalent: +10 max HP to player
   - Unique wedding dialogue plays
```

---

## 6. Wedding Items

### 6.1 Alice — Teacup Brooch

```python
"wedding_alice": {
    "name": "Teacup Brooch",
    "type": "equipment",
    "slot": "accessory",
    "unique": True,
    "soulbound": True,
    "base_mods": {"Wisdom": 5, "Charisma": 3, "Learning": 2},
    "elemental_dmg": {"light": 1.3, "magical": 1.2},
    "elemental_res": {"dark": 1.2},
    "special": "wonderland_tea_party",
    "description": (
        "A tiny porcelain teacup, impossibly warm to the touch. "
        "It never empties, and the tea always tastes exactly like "
        "whatever you need most. Alice's wedding gift — a promise "
        "that you'll always have a seat at her table."
    ),
    "drop_source": "alice",
    "drop_rarity": "legendary",
},
```

**Special Effect: `wonderland_tea_party`**

| Condition | Effect |
|---|---|
| **Base (always)** | +1 Wisdom per Storybook enemy on the field (stacks with Alice's passive if she's in party) |
| **Bonded (Alice in active party)** | At the start of every 3rd round, all allies regain 8 HP and cleanse 1 debuff ("It's always teatime somewhere") |
| **Bonded — combat start** | Party gains +10% dodge for 2 turns ("The tea sharpens your senses") |

### 6.2 Red Hood — Crimson Clasp

```python
"wedding_red_hood": {
    "name": "Crimson Clasp",
    "type": "equipment",
    "slot": "accessory",
    "unique": True,
    "soulbound": True,
    "base_mods": {"Strength": 5, "Dexterity": 3, "Constitution": 2},
    "elemental_dmg": {"physical": 1.25, "fire": 1.15},
    "elemental_res": {"dark": 1.2},
    "special": "hunters_vow",
    "description": (
        "A strip of crimson fabric from Red Hood's cloak, bound around "
        "your wrist. It pulses with a slow, steady warmth — like a "
        "heartbeat. As long as you wear it, she will always find her "
        "way back to you."
    ),
    "drop_source": "red_hood",
    "drop_rarity": "legendary",
},
```

**Special Effect: `hunters_vow`**

| Condition | Effect |
|---|---|
| **Base (always)** | Immune to Fear. +10% crit chance vs Beasts & Abominations |
| **Bonded (Red Hood in active party)** | When you kill an enemy, gain +2 Strength for 2 turns (stacks up to +6). "The hunt fuels you." |
| **Bonded — combat start** | If any enemy is Beast or Abomination, you gain +15% damage vs that enemy type for the entire combat |

### 6.3 Dorothy — "There's No Place" Charm

```python
"wedding_dorothy": {
    "name": "\"There's No Place\" Charm",
    "type": "equipment",
    "slot": "accessory",
    "unique": True,
    "soulbound": True,
    "base_mods": {"Charisma": 5, "Wisdom": 3, "Constitution": 2},
    "elemental_dmg": {"water": 1.25, "light": 1.2},
    "elemental_res": {"wind": 1.3, "dark": 1.1},
    "special": "no_place_like_you",
    "description": (
        "A tiny pair of ruby slippers on a silver chain. They don't "
        "take you to Kansas — they remind you that you're already "
        "where you belong. Dorothy's wedding gift, given with a kiss "
        "on the cheek and Toto's bark of approval."
    ),
    "drop_source": "dorothy",
    "drop_rarity": "legendary",
},
```

**Special Effect: `no_place_like_you`**

| Condition | Effect |
|---|---|
| **Base (always)** | +10% dodge. +10% XP from all sources (stacks with Dorothy's `somewhere_over_rainbow`) |
| **Bonded (Dorothy in active party)** | Once per combat, when you would take lethal damage, survive with 1 HP instead. "There's no place like home — and you're not leaving yours." |
| **Bonded — combat start** | Toto's Blessing: +15% chance to find non-combat rooms (fountain, treasure, merchant) in the dungeon. "Toto always finds the best paths." |

---

## 7. Skill Definitions

### 7.1 Alice's Skills

```yaml
# resources/skill_book/wonderland_heroines.yaml

curious_inquiry:
  name: Curious Inquiry
  description: "Asks a question so perplexing it weakens the enemy's defences."
  type: debuff
  target: single_enemy
  cooldown: 4
  effect:
    - type: elemental_weakness
      value: 0.6
      duration: 3
    - type: stat_debuff
      stat: Wisdom
      value: -3
      duration: 3
  flavour: "Alice tilts her head and asks something impossible."

try_me:
  name: Try Me
  description: "Drinks from a mysterious bottle. Results may vary."
  type: self_buff
  target: self
  cooldown: 5
  effect:
    - type: random_one_of
      options:
        - type: buff
          stat: dodge
          value: 0.30
          duration: 2
          flavour: "One side makes you smaller — Alice shrinks, becoming harder to hit! (+30% dodge)"
        - type: buff
          stat: damage
          value: 0.30
          duration: 2
          flavour: "The other side makes you larger — Alice grows, towering over the battlefield! (+30% damage)"
  flavour: "Alice eyes the bottle. 'What's the worst that could happen?'"

vorpal_instinct:
  name: Vorpal Instinct
  description: "Alice has faced the Jabberwock. She knows how monsters work now."
  type: passive
  effect:
    - type: damage_boost_vs_race
      races: ["Dragonkin", "Storybook"]
      value: 0.20
  flavour: "Alice's eyes narrow. She's seen worse."

wonderland_logic:
  name: Wonderland Logic
  description: "The nonsense of Wonderland is Alice's native tongue."
  type: passive
  effect:
    - type: stat_per_enemy_race
      stat: Wisdom
      race: Storybook
      value: 1
  flavour: "The more impossible the situation, the clearer Alice's thinking becomes."
```

### 7.2 Red Hood's Skills

```yaml
hunters_mark:
  name: Hunter's Mark
  description: "Marks a target. The pack closes in."
  type: debuff
  target: single_enemy
  cooldown: 3
  effect:
    - type: damage_taken_increase
      value: 0.15
      duration: 3
  flavour: "Red Hood's eyes lock onto her prey. 'There. That one.'"

whats_in_the_basket:
  name: What's in the Basket?
  description: "Grandmother's recipe — bread and wine. Restorative and warm."
  type: heal
  target: single_ally
  cooldown: 5
  effect:
    - type: heal_percent
      value: 0.25
  flavour: "Red Hood pulls fresh bread from her basket. 'Eat. You'll need your strength.'"

grandmothers_lesson:
  name: Grandmother's Lesson
  description: "What big teeth YOU have. The huntress has become the hunter."
  type: passive
  effect:
    - type: fear_immunity
    - type: crit_chance_vs_race
      races: ["Beast", "Abomination"]
      value: 0.10
  flavour: "Red Hood smiles. It's not a nice smile."

woodcutter_training:
  name: Woodcutter Training
  description: "Every swing finds its mark a little better than the last."
  type: passive
  effect:
    - type: stacking_stat_per_consecutive_attack
      stat: Strength
      max_stacks: 3
      value_per_stack: 1
  flavour: "Red Hood's axe bites deeper with every swing."
```

### 7.3 Dorothy's Skills

```yaml
no_place_like_home:
  name: There's No Place Like Home
  description: "A healing wind that carries the scent of Kansas wheat."
  type: heal
  target: all_allies
  cooldown: 6
  effect:
    - type: heal_percent
      value: 0.25
    - type: cleanse_one_debuff
  flavour: "Dorothy closes her eyes. A warm breeze fills the battlefield, smelling of rain and wheat."

ruby_blink:
  name: Ruby Blink
  description: "The ruby slippers flash — and Dorothy is somewhere else."
  type: self_buff
  target: self
  cooldown: 4
  effect:
    - type: dodge
      value: 0.50
      duration: 1
  flavour: "Dorothy clicks her heels — once, twice — and vanishes in a flash of ruby light."

somewhere_over_rainbow:
  name: Somewhere Over the Rainbow
  description: "The journey is its own reward. Dorothy makes everything feel worthwhile."
  type: passive
  effect:
    - type: xp_boost
      value: 0.10
      target: party
  flavour: "Dorothy hums a familiar tune. The road ahead seems a little brighter."

totos_nose:
  name: Toto's Nose
  description: "Toto always knows the best paths — and the worst ones to avoid."
  type: passive
  effect:
    - type: non_combat_room_chance
      value: 0.15
  flavour: "Toto sniffs the air and barks once — that way. Definitely that way."
```

---

## 8. Implementation Notes

### 8.1 Files to Modify

| File | Change |
|---|---|
| `resources/enemies/enemies_data/wonderland.yaml` | Add heroine template entries |
| `resources/dialogues/wonderland.py` | Add all dialogue trees |
| `resources/items.py` | Add engagement rings + wedding items |
| `resources/skill_book/wonderland_heroines.yaml` | Add all skill definitions |
| `combat/ally.py` | Handle `_wonderland_temp` flag, `_heroine_key`, heroine-specific scaling |
| `combat/ally_skills.py` | Wire heroine skills into ally skill system |
| `facilities/inn.py` | Add heroine recruitment dialogue flow for Wonderland |
| `facilities/house.py` | Handle heroine-specific engagement rings (not generic rings) |
| `combat/big_bad_wolf.py` | Hook: Red Hood dialogue + permanent unlock on victory |
| `combat/wicked_witch.py` | Hook: Dorothy dialogue + permanent unlock on victory |
| `combat/jabberwock.py` | Hook: Alice dialogue + permanent unlock on victory |
| `combat/mary_sue.py` | Hook: all-heroines fallback permanent unlock on victory |

### 8.2 Heroine State Tracking

```python
# Player dict keys for heroine state
player["wl_alice_state"] = "intro"           # intro | recruited | permanent
player["wl_redhood_state"] = "intro"         # intro | recruited | permanent
player["wl_dorothy_state"] = "intro"         # intro | recruited | permanent

player["wonderland_heroine_alice_permanent"] = False
player["wonderland_heroine_redhood_permanent"] = False
player["wonderland_heroine_dorothy_permanent"] = False
```

### 8.3 Affection Tracking for Wonderland Heroines

Heroines in temporary state (inside Wonderland) track affection on the ally dict itself. When they become permanent, the affection transfers to the house system. Since heroines don't live in a house until permanent, their affection lives entirely on the ally object:

```python
# Affection is stored directly on the ally dict
ally["affection"] = 50         # starts at heroine-specific value
ally["affection_cap"] = 100    # increases to 150 on engagement
ally["engaged"] = False
ally["married"] = False
```

### 8.4 Gift System Integration

When in Wonderland, the inn's heroine interaction menu provides Talk / Gift / Blessing / Kiss options (matching the house lounge pattern). Gifts come from the player's inventory. The gift preference system uses the same mechanism as monster girls — check item type/category against the heroine's preference table.

### 8.5 Blessing System

Each heroine's blessing is a 1/day buff that lasts for the current dungeon run:

| Heroine | Blessing | Effect |
|---|---|---|
| **Alice** | Question the Universe | +2 Wisdom, +10% dodge vs Storybook enemies |
| **Red Hood** | Woodsman's Benediction | +2 Strength, Fear immunity |
| **Dorothy** | Kansas Wind | +2 Charisma, +10% non-combat room chance |
