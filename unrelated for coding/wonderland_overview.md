# Wonderland — Full Design Blueprint

## Table of Contents

1. [Unlock Condition](#1-unlock-condition)
2. [New Race: Storybook](#2-new-race-storybook)
3. [New Biome: Wonderland](#3-new-biome-wonderland)
4. [City Definition](#4-city-definition)
5. [Facility NPCs — Known Figures](#5-facility-npcs--known-figures)
6. [City ASCII Map](#6-city-ascii-map)
7. [Dialogue Flavours](#7-dialogue-flavours)
8. [Entry Restriction: Allies Left Behind & Time Lock](#8-entry-restriction-allies-left-behind--time-lock)
9. [Heroine Quest System](#9-heroine-quest-system)
10. [Dungeon Structure](#10-dungeon-structure)
11. [Enemy Roster (by floor tier)](#11-enemy-roster-by-floor-tier)
12. [Superboss Cadence](#12-superboss-cadence)
13. [New Items](#13-new-items)
14. [Files to Create/Modify](#14-files-to-create--modify)
15. [Implementation Order](#15-implementation-order)

---

## 1. Unlock Condition

Wonderland is a **hidden city** that appears after all three conditions are met:

| Condition | Requirement |
|---|---|
| **Floor Milestone** | Floor 20+ cleared in at least 2 different city dungeons |
| **Time Milestone** | Day 60+ (2 in-game months) |
| **Key Item** | Possess a **Looking Glass Shard** |

**Looking Glass Shard** is purchasable from the
Veilholt Black Market for 5000 gold once the floor milestone is met.

### Unlock Event

Once conditions are met, the player sees this event on their next city visit, replacing receptonist enter dialogue (once):

> *"A shimmering portal has appeared in the Veilholt forest. The locals
> whisper of a realm that exists between pages — Wonderland."*

The event sets `player["wonderland_unlocked"] = True`.

### Access Method

Visit **Veilholt Arcane Tower** → new option appears: **"Investigate mysterious book."**
Selecting it teleports the player to Wonderland (see [Entry Restriction](#8-entry-restriction-allies-left-behind),
also see [arcane tower teleport feature](#)). This is the **only** way in or out —
Wonderland does **not** appear on the world map, in the travel system, or in
any city list. It is a hidden destination accessible exclusively through the book.

```python
# No travel connections needed — entry is via arcane_tower.py handler only.
# Wonderland's CITIES entry has an empty "travel" block:
"travel": {"connections": []},
```

---

## 2. New Race: Storybook

Add to `resources/enemies/enemy_races.py`:

```python
"Storybook": {
    "mods": {"Strength": 2, "Dexterity": 2, "Charisma": 3, "Wisdom": -1, "Constitution": -1},
    "elemental_res": {"light": 1.2, "dark": 0.7, "thunder": 1.1},
    "elemental_dmg": {"light": 1.3, "wind": 1.2},
},
```

**Key trait**: Wonderland enemies are **dual-race** — they have `"race": "Storybook"`
as primary and a `"secondary_race"` field (Fey, Beast, Demon, etc.) for the
fantasy half. This allows them to qualify for the Wonderland biome filter while
still reflecting their storybook origins.

**Exception**: Mary Sue (the final superboss) is pure Storybook — no secondary race.

---

## 3. New Biome: Wonderland

Add to `resources/enemies/biome_races.py`:

```python
"wonderland": ["Storybook", "Fey", "Beast", "Construct", "Abomination", "Demon", "Shadow"],
```

The dungeon spawn logic (`dungeon.py`'s `get_random_enemy_key()`) needs a minor
tweak to check both `race` and `secondary_race` against `allowed_races`:

```python
if allowed_races:
    enemy_race = data.get("race")
    secondary = data.get("secondary_race")
    if enemy_race not in allowed_races and secondary not in allowed_races:
        continue
```

---

## 4. City Definition

```python
# resources/cities.py

"wonderland": {
    "name": "Wonderland",
    "biome": "wonderland",
    "description": (
        "A realm stitched from forgotten storybooks and half-remembered dreams. "
        "The sky is the colour of aged parchment, and the clocks tick backwards. "
        "The residents are... familiar, in a way that unsettles the soul."
    ),
    "services": ["shop", "inn", "herbalist", "arcane_tower", "black_market", "temple", "gift_shop"],
    "dialogues": {
        "receptionist":  WONDERLAND_RECEPTIONIST_DIALOGUE,
        "shop":          WONDERLAND_SHOPKEEPER_DIALOGUE,
        "inn":           WONDERLAND_INNKEEPER_DIALOGUE,
        "herbalist":     WONDERLAND_HERBALIST_DIALOGUE,
        "arcane_tower":  WONDERLAND_ARCANE_TOWER_DIALOGUE,
        "black_market":  WONDERLAND_BLACK_MARKET_DIALOGUE,
        "temple":        WONDERLAND_TEMPLE_DIALOGUE,
        "gift_shop":     WONDERLAND_GIFT_SHOP_DIALOGUE,
    },
    "travel": {
        "connections": [],   # No travel connections — entry/exit is via Arcane Tower book only
    },
    "shop": {
        "stock_size": 9,
        "base_price_consumable": 22,
        "base_price_other": 70,
        "rarity_bias": "higher",
    },
    "inn": {
        "rest_cost": 15,
        "sleep_after_hour": 22,
    },
},
```

### Region Comment (added to world map section header)

```
#  WONDERLAND (hidden — accessible only via Veilholt Arcane Tower book)
```

---

## 5. Facility NPCs — Known Figures

Each facility is run by a recognizable character from classic literature.

| Facility | NPC | Flavour |
|---|---|---|
| **Receptionist** | White Rabbit | Always late. Checks a pocket watch compulsively. Speaks in rushed, anxious fragments. |
| **Shop** | The Caterpillar | Sits atop a mushroom. Blows smoke rings shaped like question marks. Answers questions with questions. |
| **Inn** | Mad Hatter | Perpetual tea party. Rest cost is random (±5 gold). Rooms are upside-down. Heroines sit at the far end of the table. |
| **Herbalist** | Rose Gardener | Painting white roses red. Sells bizarre potions with poetic names. Terrified of the Queen. |
| **Arcane Tower** | Cheshire Cat | Appears and disappears mid-sentence. The tower itself is invisible save for a grinning door. |
| **Black Market** | Captain Hook | Polished, menacing, obsessed with a certain crocodile. Trades in stolen storybook artifacts. |
| **Temple** | Fairy Godmother | Grants "storybook blessings" — buffs that last until you leave the dungeon. |
| **Gift Shop** | Tweedledee & Tweedledum | Sell whimsical trinkets. They finish each other's sentences and argue about everything. |

---

## 6. City ASCII Map

```
         .  *  .  ★  .  *  .          ╔═════════════════════════════════════╗          .  *  .  ★  .  *  .
      *   Parchment Sky   ★           ║       THE LOOKING-GLASS GATE       ║       ★   Backwards Clock   *
   .  The sun is a pocket watch  .    ║  ┌──────────┐     ┌──────────────┐  ║    .  Ticking counter-clockwise  .
      ★  Pages flutter like birds  *  ║  │   INN    │     │  BLACK       │  ║   ★    .  *  .  ★  .  *  .
   .  ┌─────────────────────────┐ .   ║  │ (Mad Tea │     │  MARKET      │  ║  . ┌──────────────────────┐ .
   │  │   THE TULGEY WOOD       │ │   ║  │  Party)  │     │ (Hook's Ship)│  ║  │ │  QUEEN'S ROSE GARDEN  │ │
   │  │  (twisted trees with    │ │   ║  └────┬─────┘     └──────┬───────┘  ║  │ │  (half red, half white)│ │
   │  │   door-shaped shadows)  │ │   ║       └────────┬─────────┘          ║  │ └───────────┬──────────┘ │
   │  └───────────┬─────────────┘ │   ║  ┌─────────────┴───────────────┐     ║  │  ┌──────────┴──────────┐ │
   │              │               │   ║  │      CROQUET LAWN           │     ║  │  │  HERBALIST          │ │
   │  ┌───────────┴───────────┐   │   ║  │  (flamingo mallets, card   │     ║  │  │ (Rose Gardener)      │ │
   │  │   MUSHROOM GROVE      │   │   ║  │   soldiers as hoops)       │     ║  │  └─────────────────────┘ │
   │  │  ┌──────────────────┐ │   │   ║  └┬──────────┬──────────┬────┘     ║  │  ┌──────────────────────┐ │
   │  │  │ SHOP (Caterpillar│ │   │   ║   │ TEMPLE   │ ARCANE   │ GIFT      ║  │  │   LOOKING-GLASS      │ │
   │  │  │ atop mushroom)   │ │   │   ║   │(Fairy G.)│ TOWER    │ SHOP      ║  │  │   PORTAL             │ │
   │  │  └──────────────────┘ │   │   ║   │          │(Cheshire)│(Tweedles) ║  │  └──────────────────────┘ │
   │  └───────────────────────┘   │   ╚═══╧══════════╧══════════╧══════════╝  └────────────────────────────┘
    \_____________________________/        ╔══ DUNGEON: THE STORYBOOK ══╗
```

---

## 7. Dialogue Flavours

### White Rabbit (Receptionist)

```python
WONDERLAND_RECEPTIONIST_DIALOGUE = {
    "enter": [
        '"Oh dear! Oh dear! You\'re early. Or late. I can never tell anymore." '
        'The White Rabbit consults a watch with no hands.',
        '"I\'m late, I\'m late, for a very important date!" He squints at you. '
        '"Are you the date? No, no — you\'re much too solid."',
        'The Rabbit flips through a calendar whose pages are all blank. '
        '"Yes, yes, you\'re expected. I think. Probably."',
    ],
    "tip": [
        '"Tip? Tip! The time — it\'s always teatime somewhere. '
        'Especially here. Especially now."',
        '"Don\'t follow the cat. That\'s my advice. '
        'Not that anyone ever takes it."',
        '"The dungeon down the rabbit hole... it gets curiouser and curiouser. '
        'Take a pocket watch. You\'ll want to know when you\'ve been gone too long."',
    ],
    "leave": [
        '"Going? Already? But you just arrived! ...Or did you? '
        'I lose track." The Rabbit hops away in the wrong direction.',
    ],
}
```

### Mad Hatter (Innkeeper)

```python
WONDERLAND_INNKEEPER_DIALOGUE = {
    "enter": [
        '"No room! No room!" — just kidding, we always have room. '
        'The question is whether the room has you.',
        'Tea? It\'s always tea time. The rooms are upstairs, '
        'though "up" is a matter of perspective here.',
        '"A very merry unbirthday to you!" The Hatter pours tea into a cup '
        'that wasn\'t there a moment ago.',
        'The table is set for twenty-four. Only three chairs are occupied — '
        'the Hatter, the March Hare, and a Dormouse who mutters about treacle.',
    ],
    "rest": [
        '"Clean cup! Move down!" The Hatter slides one seat over. '
        'Somehow, you feel better. The tea probably helped. Probably.',
    ],
    "sleep": [
        'You dream of riddles without answers. '
        'Of ravens and writing-desks. Of things that aren\'t and things that are.',
    ],
    "early_sleep": [
        '"Sleep? Now? It\'s only half past the Jabberwock!" '
        'The Hatter gestures at a clock that has thirteen numbers.',
    ],
    "leave": [
        '"Clean cup! Move down!" The Hatter slides to the next seat. '
        'You realize you\'ve been sleeping in a teacup.',
        'The door that you entered is now a window. The Hatter waves from the windowsill.',
        '"Come back when you\'ve learned to believe six impossible things before breakfast."',
    ],
}
```

### Cheshire Cat (Arcane Tower)

```python
WONDERLAND_ARCANE_TOWER_DIALOGUE = {
    "enter": [
        '"Oh, you\'re here again. Or perhaps you never left. '
        'It\'s so hard to tell with linear beings."',
        'Two eyes float in the darkness. Then a grin. Then the rest of the cat, '
        'in no particular order.',
        '"Most everyone\'s mad here. You may have noticed." The grin widens. '
        '"You fit right in."',
    ],
    "research": [
        '"I\'m not all here myself," the Cat admits, vanishing from the tail up. '
        'The grin remains. "But what remains is... informative."',
        'The Cat draws a diagram in the air with its tail. '
        'The diagram is nonsense. It is also the clearest thing you have ever seen.',
    ],
    "leave": [
        '"We\'re all mad here. I\'m mad. You\'re mad." '
        'The Cat\'s body fades. "You wouldn\'t have come here otherwise."',
        'The grin lingers for a full minute after the Cat has gone. '
        'You are not sure it ever leaves.',
    ],
}
```

### Caterpillar (Shopkeeper)

```python
WONDERLAND_SHOPKEEPER_DIALOGUE = {
    "enter": [
        '"Who... are... you?" The Caterpillar exhales a smoke ring. '
        'It hangs in the air, shaped like a coin.',
        'The Caterpillar regards you through half-lidded eyes. '
        '"One side makes you larger. The other makes you smaller. '
        'Which are you buying?"',
    ],
    "success": [
        '"Keep... the change." The smoke ring drifts toward you. '
        'When it passes through your head, you briefly understand everything. '
        'Then you forget.',
    ],
    "fail": [
        '"Not... enough." The Caterpillar turns away. '
        '"Come back when you know who you are. And have more gold."',
    ],
    "leave": [
        '"You\'ll come back. They always come back. '
        'Curiosity... is expensive."',
    ],
}
```

### Fairy Godmother (Temple)

```python
WONDERLAND_TEMPLE_DIALOGUE = {
    "enter": [
        '"Bibbidi-bobbidi — oh, you\'re not a pumpkin. Pity. '
        'Those are my favourite."',
        '"A blessing? Of course, dear. But remember: '
        'all magic comes with a closing time."',
    ],
    "leave": [
        '"The clock will strike. It always does. '
        'Use my gift before midnight."',
    ],
}
```

### Captain Hook (Black Market)

```python
WONDERLAND_BLACK_MARKET_DIALOGUE = {
    "enter": [
        'Captain Hook polishes his namesake with a silk cloth. '
        '"Browsing or buying? I\'ve no patience for the former."',
        '"Everything here was... acquired. From stories that won\'t miss them. '
        'Mostly." Hook\'s eyes flick nervously toward a ticking sound.',
    ],
    "leave": [
        '"If you hear ticking... you didn\'t hear it from me."',
    ],
}
```

### Tweedledee & Tweedledum (Gift Shop)

```python
WONDERLAND_GIFT_SHOP_DIALOGUE = {
    "enter": [
        '"Welcome!" "No, I say welcome first!" "You always say welcome first!" '
        '"That\'s because I\'m Tweedledee!" "No, I\'M Tweedledee!"',
        '"We have gifts." "The finest gifts!" "Contrariwise, the second-finest." '
        '"Contrariwise, YOU\'RE the second-finest!"',
    ],
    "leave": [
        '"Come again!" "Don\'t come again!" "I was being polite!" '
        '"Contrariwise, I was being honest!"',
    ],
}
```

---

## 8. Entry Restriction: Allies Left Behind & Time Lock

### Concept

Wonderland is a realm between pages — physical companions cannot follow,
and time itself is just another story being told. Only the player enters.
Thematic justifications:
- *"The book only has room for one reader."*
- *"Clocks don't tick here. They narrate."*

While inside Wonderland, time in the outside world is **frozen**. Days do not
pass, events do not trigger, passive income does not accumulate. When the
player leaves, the world resumes from the exact moment they opened the book.

### Time Lock Mechanic

```python
# On entry:
player["wonderland_time_frozen"] = player["time_minutes"]   # snapshot
player["wonderland_day_frozen"]  = player.get("day", 1)     # snapshot
player["wonderland_active"]      = True

# While in Wonderland:
# - advance_time() is a no-op
# - format_time() returns flavored text (see below)
# - Inn "Sleep" advances a Wonderland-internal counter (wl_time), not real time
# - Events, income, day-based buffs are all suspended
# - The "day" counter does NOT increment

# On exit:
player["time_minutes"] = player.pop("wonderland_time_frozen")
player["day"]          = player.pop("wonderland_day_frozen")
```

**Design note**: `advance_time()` in `utils.py` needs a guard:

```python
def advance_time(player, minutes):
    if player.get("wonderland_active"):
        # Wonderland time flows differently — track internally but don't advance real clock
        player["wl_internal_time"] = player.get("wl_internal_time", 0) + minutes
        return
    # ... existing logic
```

### Wonderland Clock Display

Instead of normal time (`08:30`, `14:15`), Wonderland shows whimsical,
nonsensical clock readings. A random flavored text is chosen each time
the clock is displayed. Some texts reference the Mad Hatter's eternal
tea party, others are pure nonsense.

| Display | Flavour |
|---|---|
| `!!:!!` | *The little lamb is confused* |
| `?:??` | *The clock has forgotten how to count* |
| `₮:₮₮` | *Teatime, obviously* |
| `∞:∞∞` | *Always. Never. Both.* |
| `⌛:⏳` | *The hourglass is arguing with itself* |
| `42:42` | *The answer. The question is still pending.* |
| `--:--` | *Time is on strike. It wants better working conditions.* |
| `13:13` | *The thirteenth hour. The one that doesn't exist. Until it does.* |
| `⑥:⓪⑥` | *The March Hare broke the minute hand again* |
| `ZZ:ZZ` | *The Dormouse is dreaming the clock. Don't wake him.* |
| `🎩:☕` | *Hatter o'Clock* |
| `?:!?` | *The clock is asking you a question. You don't know the answer.* |
| `AB:CD` | *The Caterpillar is spelling something. Probably.* |
| `OO:PS` | *The White Rabbit dropped the clock. Again.* |
| `--:--` | *The hands have gone for a walk. They'll be back. Probably.* |

The display format in the city header changes from:
```
Time: 14:30
```
to:
```
Time: !!:!!  — The little lamb is confused
```

**Implementation**: `format_time()` in `utils.py` checks `player.get("wonderland_active")`:

```python
_WL_CLOCK_FLAVORS = [
    ("!!:!!", "The little lamb is confused"),
    ("?:??", "The clock has forgotten how to count"),
    ("₮:₮₮", "Teatime, obviously"),
    # ... etc
]

def format_time(player_or_minutes):
    if isinstance(player_or_minutes, dict) and player_or_minutes.get("wonderland_active"):
        clock, flavor = random.choice(_WL_CLOCK_FLAVORS)
        return f"{clock} — {flavor}"
    # ... existing logic
```

### New Player Data Fields

```python
player["wonderland_benched_allies"] = [...]     # allies stored on entry
player["wonderland_active"] = True               # flag: currently in Wonderland
player["wonderland_return_city"] = "veilholt"    # where to return on exit
player["wonderland_time_frozen"] = 480           # time_minutes at entry (snapshot)
player["wonderland_day_frozen"]  = 15            # day counter at entry (snapshot)
player["wl_internal_time"] = 0                   # Wonderland's own time tracker (internal only)
```

### Entry Flow (Veilholt Arcane Tower)

In `facilities/arcane_tower.py`, `_build_menu_options()` appends a new option
when Wonderland conditions are met:

```python
if city_id == "veilholt" and player.get("wonderland_unlocked"):
    options.append("Investigate mysterious book")
```

The handler:

```python
def _investigate_mysterious_book(player, city_id):
    """Entry point to Wonderland — benches all allies and teleports player."""
    term.print(
        "\nA leather-bound book sits on a pedestal, its pages rustling "
        "though there is no wind. The title reads: 'Wonderland.'"
    )
    term.print(
        "\nThe archmage warns: 'That book... it does not merely tell a story. "
        "It pulls the reader inside. Your companions cannot follow.'"
    )

    if not term.confirm("Open the book and enter Wonderland?"):
        return

    # ── Bench all current allies ─────────────────────────────────
    current_allies = player.get("allies", [])
    player["wonderland_benched_allies"] = current_allies
    player["allies"] = []
    player["party_order"] = []

    # ── Freeze time ─────────────────────────────────────────────
    player["wonderland_time_frozen"] = player["time_minutes"]
    player["wonderland_day_frozen"]  = player.get("day", 1)

    # ── Store return location ────────────────────────────────────
    player["wonderland_return_city"] = city_id

    # ── Teleport ─────────────────────────────────────────────────
    player["location"] = "wonderland"
    player["wonderland_active"] = True

    term.print(
        "\nThe pages envelop you. The archmage's tower dissolves into "
        "a sky the colour of aged parchment."
    )
    term.print("You are in Wonderland.")
    term.print("The clock on the wall reads: !!:!!")
    term.pause()
```

### Exit Flow

When the player travels from Wonderland back to Veilholt (portal), the reverse
happens:

```python
def _leave_wonderland(player):
    """Restore benched allies and unfreeze time when leaving Wonderland."""

    # ── Separate permanent vs temporary heroines ─────────────────
    permanent_heroines = []
    for ally in player.get("allies", []):
        hk = ally.get("_heroine_key")
        if hk == "alice" and player.get("wonderland_heroine_alice_permanent"):
            ally["_wonderland_temp"] = False
            permanent_heroines.append(ally)
        elif hk == "red_hood" and player.get("wonderland_heroine_redhood_permanent"):
            ally["_wonderland_temp"] = False
            permanent_heroines.append(ally)
        elif hk == "dorothy" and player.get("wonderland_heroine_dorothy_permanent"):
            ally["_wonderland_temp"] = False
            permanent_heroines.append(ally)

    # ── Restore benched allies ───────────────────────────────────
    benched = player.pop("wonderland_benched_allies", [])
    player["allies"] = benched
    player["party_order"] = list(range(len(benched)))

    # ── Append permanent heroines ───────────────────────────────
    for heroine in permanent_heroines:
        player["allies"].append(heroine)
        player["party_order"].append(len(player["allies"]) - 1)

    # ── Unfreeze time ───────────────────────────────────────────
    player["time_minutes"] = player.pop("wonderland_time_frozen", player["time_minutes"])
    player["day"] = player.pop("wonderland_day_frozen", player.get("day", 1))

    # ── Reset temp states ───────────────────────────────────────
    if not player.get("wonderland_heroine_alice_permanent"):
        player["wl_alice_state"] = "intro"
    if not player.get("wonderland_heroine_redhood_permanent"):
        player["wl_redhood_state"] = "intro"
    if not player.get("wonderland_heroine_dorothy_permanent"):
        player["wl_dorothy_state"] = "intro"

    player["wonderland_active"] = False

    term.print(
        "\nThe book closes. The archmage's tower reforms around you."
    )
    term.print(
        f"The clock on the wall reads: {format_time(player['time_minutes'])}. "
        "No time has passed."
    )
```

### Leaving Wonderland

The player leaves Wonderland by returning to the **Veilholt Arcane Tower**.
When in Wonderland, the Arcane Tower's teleportation menu includes a special option:

```
"Return through the Looking-Glass (Veilholt)"
```

Selecting it triggers `_leave_wonderland()`, which restores allies, unfreezes time,
and places the player back in Veilholt. There is no cost — the book is a two-way
passage.

### World Map & Travel in Wonderland

Wonderland is **completely hidden** from the world map and travel system.
It does not appear in `CITY_MAPS`, the travel UI, or any destination list.

If the player attempts to open the **world map** or **travel menu** while inside
Wonderland, instead of a map they see this:

```
                                  .'\   /`.
                                .'.-.`-'.-.`.
                            ..._:   .-. .-.   :_...
                        .'    '-.(o ) (o ).-'    `.
                        :  _    _ _`~(_)~`_ _    _  :
                        :  /:   ' .-=_   _=-. `   ;\  :
                        :   :|-.._  '     `  _..-|:   :
                        :   `:| |`:-:-.-:-:'| |:'   :
                        `.   `.| | | | | | |.'   .'
                            `.   `-:_| | |_:-'   .'
                             `-._   ````    _.-'
                                ``-------''

         "Oh, you're looking for a map? How delightfully linear of you.
          There is no map. There is no 'north.' There is only where you are,
          and where you aren't, and the difference is mostly academic.

          But if you must go somewhere... try the book. It's how you came in.
          It's how you'll leave. Everything else is just scenery."

                        — The Cheshire Cat
```

The Cheshire Cat's grin appears superimposed on the text. The ASCII art should
be centered in the GUI terminal and use the current theme's accent colour.

**Implementation**: In `gui/screens/travel_screen.py` (or wherever the world map
is rendered), check `player.get("wonderland_active")` and render the Cheshire
Cat art + text instead of the normal map. In terminal mode, `print()` the art
directly.

---

## 9. Heroine Quest System

### Overview

Three heroines wait in the Wonderland Inn. They are **not** monster girls to
capture — they are story characters with full dialogue trees and quest arcs.

| Heroine | Race | Associated Superboss / Quest Boss | Location |
|---|---|---|---|
| **Alice** | Fey | Jabberwock (F40) | Wonderland Inn (far end of Mad Hatter's table) |
| **Red Hood** | Beast | Big Bad Wolf (F20) | Wonderland Inn (near the fireplace, sharpening axe) |
| **Dorothy** | Human | Wicked Witch of the West (F30) | Wonderland Inn (by the window, staring at a pair of ruby slippers) |

### Heroine States

Each heroine has a state tracked in the player dict:

| State | Flag Value | Meaning |
|---|---|---|
| Unmet | `"unmet"` | Never spoken to |
| Intro | `"intro"` | First conversation done; "Join me" option available |
| Temp Ally | `"temp"` | Currently in party (temporary — lost on leaving Wonderland) |
| Permanent | `"permanent"` | Superboss defeated; survives leaving Wonderland |
| Declined | `"declined"` | Player chose not to recruit; can ask again next visit |

```python
player["wl_alice_state"]      # "unmet" | "intro" | "temp" | "permanent" | "declined"
player["wl_redhood_state"]    # same
player["wl_dorothy_state"]    # same

# Permanent flags:
player["wonderland_heroine_alice_permanent"]     # bool
player["wonderland_heroine_redhood_permanent"]   # bool
player["wonderland_heroine_dorothy_permanent"]   # bool
```

### State Machine

```
 UNMET ──(talk)──→ INTRO ──("Join me")──→ TEMP_ALLY
                      │                        │
                      └──("Not now")──→ DECLINED ──(talk again)──→ TEMP_ALLY
                                                                    │
                                          ┌─────────────────────────┘
                                          ▼
                                     TEMP_ALLY ──(leave Wonderland)──→ removed from party
                                          │
                                          └──(defeat superboss in dungeon)──→ PERMANENT
                                                                                │
                                          PERMANENT ──(leave Wonderland)──→ follows you out
```

### Inn Modification

In `facilities/inn.py`, when `city_id == "wonderland"`, the standard Rest/Sleep/Back
menu is extended with heroine options:

```
=== THE MAD HATTER'S TEA PARTY — WONDERLAND ===

[Standard inn options: Rest, Sleep]

At the far end of the table:
  1. Talk to the girl in the blue dress (Alice)
  2. Talk to the huntress in the red hood (Red Hood)
  3. Talk to the girl with the ruby slippers (Dorothy)
  4. Back
```

### Alice — First Meeting Dialogue

```
Alice sits at the far end of the table, teacup in hand. She doesn't seem
to notice you until you're right beside her.

Alice: "Oh! I'm sorry — I was counting the sugar cubes. There are exactly
       forty-two, which is the answer to a question I haven't asked yet."

Player options:
  1. "Who are you?"
  2. "Why are you here?"
  3. "Would you like to travel with me?" [only if state == "intro"]

Option 1:
  Alice: "Alice. I followed a rabbit once, and then a cat, and then...
         I'm not quite sure how I got *here*, specifically. The book
         shuffled its pages again. It does that."

Option 2:
  Alice: "There's a beast here — a Jabberwock. It's been writing its own
         story, and it's *terrible*. Run-on sentences everywhere. I tried
         to edit it, but it... didn't appreciate the feedback."

Option 3:
  Alice: "You're going into the Storybook Dungeon? Oh, please take me with
         you! I know the way — mostly. Sometimes the path is upside-down,
         but I've learned to walk on ceilings."

  → Alice joins as temporary ally
```

### Red Hood — First Meeting Dialogue

```
Red Hood sits with her back to the wall, a basket on the table. Her crimson
hood is pulled low, but wolf ears twitch beneath it. She's sharpening a
woodcutter's axe.

Red Hood: "You're not from here. Good. The locals have a... particular sense
          of humour. The last person who asked me for directions turned left
          at the wrong mushroom and hasn't been seen since."

Player options:
  1. "You're a long way from the forest."
  2. "What's in the basket?"
  3. "I could use someone who can handle an axe." [only if state == "intro"]

Option 1:
  Red Hood: "The forest is wherever the wolf is. And the wolf? He's here.
            Calls himself 'The Big Bad.' Thinks he's clever because he ate
            the original ending to my story. I'm here to write a new one."

Option 2:
  Red Hood: "Provisions. Healing herbs. A whetstone. And a very angry
            letter to my grandmother's estate lawyer. The usual."

Option 3:
  Red Hood: (She tests the axe's edge with her thumb, nods.)
            "Fine. You watch my back, I'll watch yours. But when we find
            the Wolf — he's mine."

  → Red Hood joins as temporary ally
```

### Dorothy — First Meeting Dialogue

```
Dorothy sits by the window, a pair of ruby slippers on the table before
her. She's not wearing them — just looking at them, her expression distant.
A small black dog sleeps at her feet.

Dorothy: "They say these can take me home. Three clicks and I'd be back in
         Kansas. But every time I try... I end up somewhere worse."

         She looks up at you. Her eyes are tired but not defeated.

         "Are you real? You don't look like the others. The ones she writes.
         You look like... someone who actually chooses where they're going."

Player options:
  1. "Who is 'she'?"
  2. "Do you want to go home?"
  3. "Come with me. We'll find a way out together." [only if state == "intro"]

Option 1:
  Dorothy: "The one with the pen. She wrote a witch for me to fight, and a
           wizard to disappoint me, and a road that never really ends. I've
           walked it six times now. It changes, but it never... stops."

Option 2:
  Dorothy: "More than anything. But I think... I think I can't go home until
           I finish the story. And the story wants me to kill a witch."
           (She glances at the slippers.) "These won't work until I do."

Option 3:
  Dorothy: (She studies you for a long moment. The dog lifts its head.)
           "Toto says you're okay. And Toto's never wrong about people."
           She picks up the slippers — but puts them in her bag, not on her
           feet. "Lead the way. But if we see a witch... I'm not running."

  → Dorothy joins as temporary ally
```

### Heroine Ally Templates

#### Level & Stat Scaling

Heroines follow special scaling rules that differ from regular captured allies:

| State | Level | XP | Stat Formula |
|---|---|---|---|
| **Temporary** (in Wonderland) | Matches player level on join, **does not change** | Does not gain XP | `base_mod + (join_level - 1) × 0.22` |
| **Permanent** (superboss defeated) | **Frozen** at the level they joined at | Gains XP normally from this point | Stats frozen at temp values; level-up bonuses apply going forward |

**HP formula** (both states):
```
max_hp = base_hp + (level - 1) × 4
```

**Stat formula** (temporary state, computed once on join):
```python
def compute_heroine_temp_stats(base_mods, player_level):
    """Heroines keep their full base stats with a per-level bonus."""
    scaled = {}
    for attr, base in base_mods.items():
        # Heroines use 0.22 per level (vs 0.18 for regular allies)
        # No 0.85 multiplier — heroines are special characters
        scaled[attr] = max(1, int(base + (player_level - 1) * 0.22))
    return scaled
```

**Design rationale**: Heroines don't use the `ALLY_STAT_MULTIPLIER (0.85)`
that regular captured allies do. Their base stats are their *actual* stats
at level 1, making them stronger than equivalent-level regular allies. This
compensates for:
- No equipment (heroines can't equip weapons/armor)
- No affection bonuses (they're story characters, not captured)
- Temporary nature (they leave when you exit Wonderland, unless permanent)

**On permanent unlock**:
1. Heroine's level is frozen at the value they joined with
2. Stats are frozen at their current computed values
3. `level_hp_bonus` is set to `(level - 1) * 4`
4. They begin gaining XP from combat
5. On level-up, they gain stat points like regular allies (player chooses allocation)
6. They can now equip items (weapon, armor, accessories)
7. They survive leaving Wonderland

```python
def promote_heroine_to_permanent(player, ally, join_level):
    """Called when a heroine's superboss is defeated."""
    ally["_wonderland_temp"] = False
    ally["level"] = join_level
    ally["level_hp_bonus"] = (join_level - 1) * 4
    ally["exp"] = 0
    ally["affection"] = 60  # High base affection — they chose to stay
    ally["equipped"] = {"weapon": None, "armor": None, "accessory1": None, "accessory2": None}
    # Stats are already computed; keep them as-is
    # From here, normal ally leveling takes over
```

#### Example: Alice at Player Level 25

```python
# Alice base mods:
base_mods = {"Wisdom": 4, "Dexterity": 2, "Charisma": 2, "Strength": -1,
             "Constitution": 0, "Learning": 0}
base_hp = 20
player_level = 25

# Temporary stats:
# Wisdom:  max(1, 4 + 24 * 0.22) = max(1, 9.28) = 9
# Dexterity: max(1, 2 + 24 * 0.22) = max(1, 7.28) = 7
# Charisma: max(1, 2 + 24 * 0.22) = max(1, 7.28) = 7
# Strength: max(1, -1 + 24 * 0.22) = max(1, 4.28) = 4
# Constitution: max(1, 0 + 24 * 0.22) = max(1, 5.28) = 5
# Learning: max(1, 0 + 24 * 0.22) = max(1, 5.28) = 5
# HP: 20 + 24 * 4 = 116

# After permanent unlock at level 25:
# Stats frozen, XP starts at 0, can equip items
# Next level-up at 100 XP → player allocates +1 to any stat
```

#### Alice (Fey)

```yaml
wonderland_alice:
  name: Alice
  race: Fey
  secondary_race: Storybook
  level: 1                       # Scales to player level on join (see formula above)
  base_hp: 20                    # HP = base_hp + (level - 1) × 4
  mods:                          # Stats = mod + (level - 1) × 0.22 (no 0.85 multiplier)
    Wisdom: 4
    Dexterity: 2
    Charisma: 2
    Strength: -1
  boss: false
  super_boss: false
```

**Innate Skills:**
- `curious_inquiry` — Debuff: increases enemy's elemental weakness by 0.6, -3 Wisdom for 3 turns
- `try_me` — Self-buff: +30% dodge for 2 turns or +30% damage for 2 turns (shrink/grow)

**Permanent Unlock** (after Jabberwock defeat at F40):
- `vorpal_instinct` — Passive: +20% damage vs Dragonkin & Storybook races

**Passive:** `wonderland_logic` — +1 Wisdom per Storybook enemy on field

#### Red Hood (Beast)

```yaml
wonderland_red_hood:
  name: Red Hood
  race: Beast
  secondary_race: Storybook
  level: 1                       # Scales to player level on join
  base_hp: 24                    # HP = base_hp + (level - 1) × 4
  mods:
    Strength: 3
    Dexterity: 3
    Constitution: 2
    Wisdom: -1
    Charisma: 1
  boss: false
  super_boss: false
```

**Innate Skills:**
- `hunters_mark` — Debuff: target takes +15% damage from all sources, 3 turns
- `whats_in_the_basket` — Heal: restores 25% HP to one ally

**Permanent Unlock** (after Big Bad Wolf defeat):
- `grandmothers_lesson` — Passive: immune to Fear, +10% crit vs Beasts & Abominations

**Passive:** `woodcutter_training` — +1 Strength per consecutive attack on same target (max +3)

#### Dorothy (Human)

```yaml
wonderland_dorothy:
  name: Dorothy
  race: Human
  secondary_race: Storybook
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
```

**Innate Skills:**
- `no_place_like_home` — Party-wide heal (25% max HP) + cleanse one debuff per ally. 6-turn cooldown.
- `ruby_blink` — Self: teleport to safety. +50% dodge for 1 turn.

**Permanent Unlock** (after Wicked Witch defeat at F30):
- `somewhere_over_rainbow` — Passive: party gains +10% XP from all sources. Dorothy's mere presence makes the journey feel worthwhile.

**Passive:** `totos_nose` — Dorothy detects traps and hidden rooms. +15% chance to find non-combat rooms (fountain, treasure, merchant) in the dungeon.

### Superboss / Quest Boss Defeat → Permanent Unlock

When Alice is in the party and Jabberwock (F40) is defeated:

```
[The Jabberwock collapses, its narrative unspooling into ink-black mist.
 Alice stands over the fading beast, teacup still in hand.]

Alice: "The sentence is complete. Full stop. ... I think I can leave now.
       Not just the dungeon — Wonderland itself. If you'll have me."

→ Alice becomes a permanent ally
```

When Red Hood is in the party and Big Bad Wolf (F20) is defeated:

```
[The Wolf dissolves into smoke and scattered pages. Red Hood stands over
 the spot where it fell, breathing hard.]

Red Hood: "The original ending. He ate it, you know. But he never digested it."
          (She tucks a tattered page away.)
          "The story's done. I'm free. And... I owe you for that."
          "Where to next?"

→ Red Hood becomes a permanent ally
```

When Dorothy is in the party and the Wicked Witch of the West (F30) is defeated:

```
[The Witch dissolves into a puddle of ink and emerald smoke. Her hat
 floats for a moment, then sinks. Dorothy stands over the puddle,
 ruby slippers gleaming — no longer on the table, but on her feet.]

Dorothy: "She's gone. She's really gone."
         (She clicks her heels once. Nothing happens.)
         (She clicks them twice. A warm breeze stirs.)
         (She doesn't click them a third time.)

         "I could go home now. I can feel it — Kansas is right there,
          three clicks away. But..."

         She looks at you. Toto barks.

         "You're not from Kansas. And you're still fighting. Maybe...
          maybe home can wait. Just a little longer."

→ Dorothy becomes a permanent ally
```

### Fallback: Mary Sue Victory

Even if the player skipped F20/F30/F40, defeating Mary Sue (F50) with a heroine
in the party also grants permanent status — she has defeated the *author*,
which supersedes defeating any individual character. See the Mary Sue superboss doc.

---

## 10. Dungeon Structure

The Storybook Dungeon has **7 thematic blocks** across **50 floors**.
**Regular floor bosses appear every 2 floors** (even floors that aren't
multiples of 10). Superbosses appear every 10 floors.

| Floors | Theme | Source Material |
|---|---|---|
| 1–8 | Alice's Descent | Alice in Wonderland |
| 9–16 | Neverland's Lost | Peter Pan |
| 17–24 | The Yellow Brick Road + Gothic | Wizard of Oz / Dracula / Jekyll & Hyde |
| 25–32 | Wonderland Revisited | Alice in Wonderland (deeper) |
| 33–40 | The Final Chapter | Mixed / Original |
| 41–48 | The Author's Draft | Mary Sue's unpublished, experimental stories |
| 49–50 | The Last Page | Preamble to Mary Sue |

### Floor Boss Cadence

```
 Floor  2 ─ Boss: White Rabbit (Beast / Storybook)
 Floor  4 ─ Boss: Cheshire Cat (Shadow / Storybook)
 Floor  6 ─ Boss: Card Knight (Construct / Storybook)
 Floor  8 ─ Boss: Dormouse Captain (Beast / Storybook)
 Floor 10 ─ SUPERBOSS: Queen of Hearts ★
 Floor 12 ─ Boss: Peter Pan (Fey / Storybook)
 Floor 14 ─ Boss: Tick-Tock Crocodile (Beast / Storybook)
 Floor 16 ─ Boss: Pirate Captain James (Undead / Storybook)
 Floor 18 ─ Boss: Tin Woodsman Captain (Construct / Storybook)
 Floor 20 ─ SUPERBOSS: Big Bad Wolf ★
 Floor 22 ─ Boss: Mr. Hyde (Abomination / Storybook)
 Floor 24 ─ Boss: Professor Moriarty (Human / Storybook)
 Floor 26 ─ Boss: Dracula's Bride (Vampire / Storybook)
 Floor 28 ─ Boss: Phantom of the Opera (Shadow / Storybook)
 Floor 30 ─ SUPERBOSS: Wicked Witch of the West ★ (Dorothy's quest)
 Floor 32 ─ Boss: Captain Hook (Human / Storybook)
 Floor 34 ─ Boss: The Red Queen (Demon / Storybook)
 Floor 36 ─ Boss: The Scarecrow King (Construct / Storybook)
 Floor 38 ─ Boss: Bandersnatch Alpha (Beast / Storybook)
 Floor 40 ─ SUPERBOSS: Jabberwock ★ (Alice's quest)
 Floor 42 ─ Boss: The Wizard of Oz (Human / Storybook)
 Floor 44 ─ Boss: The Headless Horseman (Undead / Storybook)
 Floor 46 ─ Boss: The Snow Queen (Fey / Storybook)
 Floor 48 ─ Boss: The Nothing (Abomination / Storybook)
 Floor 50 ─ SUPERBOSS: Mary Sue — The Author ★
```

**Total**: 20 regular bosses + 5 superbosses = 25 boss encounters across 50 floors.

**Design note**: The Wicked Witch at F30 is a full superboss (see
`wonderland_superboss_wicked_witch.md`). When Dorothy is in the party,
the encounter gains additional narrative weight and she triggers her
permanent unlock on victory.

---

## 11. Enemy Roster (by floor tier)

### Floors 1–8: Alice's Descent

| ID | Name | Lvl | 2nd Race | Notes |
|---|---|---|---|---|
| `wl_card_soldier_2` | Card Soldier (Clubs) | 1–3 | Construct | Weak melee, groups |
| `wl_card_soldier_3` | Card Soldier (Spades) | 2–4 | Construct | Stronger, bleed |
| `wl_white_rabbit` | Panicked Rabbit | 3–5 | Beast | High speed, flees at low HP — also F2 boss |
| `wl_dormouse` | Dormouse | 4–6 | Beast | Sleep-inducing attacks |
| `wl_cheshire` | Grinning Shadow | 5–7 | Shadow | Phases, confusion debuff — also F4 boss |
| `wl_card_knight` | Card Knight | 6–7 | Construct | F6 boss, summons card soldiers |
| `wl_dormouse_capt` | Dormouse Captain | 7–8 | Beast | F8 boss, tea-themed AoE |

### Floors 9–16: Neverland's Lost

| ID | Name | Lvl | 2nd Race | Notes |
|---|---|---|---|---|
| `wl_lost_boy` | Lost Boy | 9–11 | Human | Skirmisher, packs |
| `wl_tinker_spite` | Spiteful Sprite | 10–12 | Fey | Pixie dust blinds |
| `wl_peter_pan` | Peter Pan | 11–13 | Fey | F12 boss — never ages, heals per turn |
| `wl_croc_ticktock` | Tick-Tock Hatchling | 11–13 | Beast | Swallow, ticking telegraph — also F14 boss |
| `wl_pirate_shade` | Pirate Shade | 12–14 | Undead | Ghost pirate, curse chance |
| `wl_pirate_captain` | Pirate Captain James | 14–16 | Undead | F16 boss, crew-summoning |

### Floors 17–24: Yellow Brick Road & Gothic

| ID | Name | Lvl | 2nd Race | Notes |
|---|---|---|---|---|
| `wl_munchkin` | Munchkin Trickster | 16–18 | Gnome | Debuffs, low HP |
| `wl_flying_monkey` | Flying Monkey | 17–19 | Beast | Dive attack, high evasion |
| `wl_tin_woodsman` | Rusted Woodsman | 17–19 | Construct | Axe cleave, self-buff |
| `wl_tin_woodsman_capt` | Tin Woodsman Captain | 18 | Construct | F18 boss — seeks a heart, gains power from allies' buffs |
| `wl_cowardly_lion` | Cowardly Beast | 17–19 | Beast | Fear AoE, flees/returns |
| `wl_hyde` | Mr. Hyde | 20–22 | Abomination | Transforms mid-fight — also F22 boss |
| `wl_frankenstein` | Stitched Abomination | 21–23 | Abomination | Thunder absorb, slow attacks |
| `wl_moriarty` | Professor Moriarty | 23–25 | Human | F24 boss — counters last-used skill |

### Floors 25–32: Wonderland Revisited

| ID | Name | Lvl | 2nd Race | Notes |
|---|---|---|---|---|
| `wl_bandersnatch` | Bandersnatch | 25–27 | Beast | Rage mechanic |
| `wl_jubjub_bird` | Jubjub Bird | 26–28 | Beast | Shriek (AoE thunder) |
| `wl_dracula_bride` | Dracula's Bride | 26–28 | Vampire | F26 boss — life drain, bat swarm |
| `wl_tweedle_dum` | Tweedledum | 27–29 | Human | Paired — buffs twin |
| `wl_tweedle_dee` | Tweedledee | 27–29 | Human | Paired — buffs twin |
| `wl_phantom` | Phantom of the Opera | 28–30 | Shadow | F28 boss — invisible until attacking, musical cues |

### Floors 33–40: The Final Chapter

| ID | Name | Lvl | 2nd Race | Notes |
|---|---|---|---|---|
| `wl_captain_hook` | Captain Hook | 31–34 | Human | F32 boss — rapier & hook, croc phobia |
| `wl_red_queen` | The Red Queen | 33–36 | Demon | F34 boss — speed chess, action economy |
| `wl_scarecrow_king` | The Scarecrow King | 34–37 | Construct | F36 boss — "If I only had a brain" — learns and adapts to your patterns |
| `wl_bandersnatch_alpha` | Bandersnatch Alpha | 36–38 | Beast | F38 boss — frumious rage, higher stats than regular Bandersnatch |

### Floors 41–48: The Author's Draft

Mary Sue's unpublished experiments — stories she wrote and abandoned. These
enemies are weirder, more abstract, and less anchored to any single source.

| ID | Name | Lvl | 2nd Race | Notes |
|---|---|---|---|---|
| `wl_wizard_oz` | The Wizard of Oz | 41–43 | Human | F42 boss — "Pay no attention to the man behind the curtain." Illusion-based: summons fake copies, hides real self. |
| `wl_headless_horseman` | Headless Horseman | 43–45 | Undead | F44 boss — throws explosive pumpkins (fire AoE), cannot be crit ("no head to strike") |
| `wl_snow_queen` | The Snow Queen | 45–47 | Fey | F46 boss — ice magic, freezes one party member per 3 turns, shatter combo |
| `wl_the_nothing` | The Nothing | 47–49 | Abomination | F48 boss — consumes buffs, grows larger, final pre-Mary Sue challenge. "It's the emptiness left behind when a story is abandoned." |

### Floor 50: The Last Page

The approach to Mary Sue. No regular enemies — only the final superboss.

---

## 12. Superboss Cadence

Wonderland uses **per-10-floor superbosses** (unlike the global pool's per-20).
Regular floor bosses appear on **every even floor that isn't a multiple of 10**
(floors 2, 4, 6, 8, 12, 14, 16, 18, 22, 24, 26, 28, 32, 34, 36, 38, 42, 44, 46, 48).

| Floor | Boss | Type | Phases | Heroine Link | Doc |
|---|---|---|---|---|---|
| 2,4,6,8,12,14,16,18,22,24,26,28,32,34,36,38,42,44,46,48 | Various | Regular floor boss | 1 | — | Inline in §11 |
| **10** | **Queen of Hearts** | **Superboss** | 1 (+ minions) | None | `wonderland_superboss_queen_of_hearts.md` |
| **20** | **Big Bad Wolf** | **Superboss** | 3 | Red Hood | `wonderland_superboss_big_bad_wolf.md` |
| **30** | **Wicked Witch of the West** | **Superboss** | 3 | **Dorothy** | `wonderland_superboss_wicked_witch.md` |
| **40** | **Jabberwock** | **Superboss** | 4 | Alice | `wonderland_superboss_jabberwock.md` |
| **50** | **Mary Sue** | **Superboss** | 5 (shadow gauntlet) | All three | `wonderland_superboss_mary_sue.md` |

### Trigger Logic

```python
# In dungeon.py explore_dungeon(), added before the global superboss check:
if region == "wonderland" and floor % 10 == 0 and city_prog["max_floor"] <= floor:
    _wonderland_superboss_encounter(player, floor, superboss_override)
elif floor % 20 == 0 and city_prog["max_floor"] <= floor:
    # ... existing global superboss pool
```

Defeat flags:

```python
player["wl_boss_defeated_queen_of_hearts"] = True   # F10
player["wl_boss_defeated_big_bad_wolf"]   = True    # F20
player["wl_boss_defeated_wicked_witch"]   = True    # F30 (Dorothy's quest)
player["wl_boss_defeated_jabberwock"]     = True    # F40 (Alice's quest)
player["wl_boss_defeated_mary_sue"]       = True    # F50
```

### Dispatcher

```python
_WL_SUPERBOSS_MAP = {
    10: ("Queen of Hearts",        "combat/queen_of_hearts.py", combat_queen_of_hearts),
    20: ("Big Bad Wolf",           "combat/big_bad_wolf.py",    combat_big_bad_wolf),
    30: ("Wicked Witch of the West","combat/wicked_witch.py",   combat_wicked_witch),
    40: ("Jabberwock",             "combat/jabberwock.py",      combat_jabberwock),
    50: ("Mary Sue",               "combat/mary_sue.py",        combat_mary_sue),
}
```

Rewards scale with floor: `exp = 300 + (floor * 60)`, `gold = 200 + (floor * 40)`.

---

## 13. New Items (exclusive to wonderland shop)

| ID | Name | Type | Rarity | Source |
|---|---|---|---|---|
| `looking_glass_shard` | Looking Glass Shard | Key Item | Rare | Veilholt Black Market |
| `vorpal_blade_rusted` | ??? Blade | Weapon | Legendary | given by fairy godmother upon reaching floor 25 in wonderland |
| `vorpal_blade` | Vorpal Blade | Weapon | Legendary | dropped by jabberwock replace ??? blade upon acquisition |
| `drink_me_potion` | Drink Me Potion | Consumable | Uncommon | Wonderland shop — shrink (dodge ↑, HP ↓) 3 turns |
| `eat_me_cake` | Eat Me Cake | Consumable | Uncommon | Wonderland inn — grow (HP ↑, speed ↓) 3 turns |
| `pixie_dust_vial` | Pixie Dust Vial | Consumable | Rare | Wonderland gift shop — Flight buff (immune ground attacks) 2 turns |
| `pocket_watch` | White Rabbit's Pocket Watch | Accessory | Epic | Temple blessing reward — skip 1 turn cooldown once per battle |
| `hook_hand` | Captain's Hook | Weapon | Epic | Black Market — bleed on crit, +threat vs Beast |
| `ruby_slippers` | Ruby Slippers | Boots | Legendary | Dorothy starts with these (story item). On her permanent unlock, she gifts a replica: "There's No Place" charm (accessory, +10% dodge) |
| `rose_tinted_crown` | Rose-Tinted Crown | Accessory | Epic | Queen of Hearts (F10) drop |
| `witch_hat` | Wicked Witch's Hat | Accessory | Epic | Wicked Witch (F30) drop — +2 Learning, "I'm Melting!" active: water-imbue one attack per combat |
| `broomstick` | Broomstick | Weapon | Epic | Wicked Witch (F30) drop — +3 Dex, +10% dodge vs ground enemies |
| `emerald_flame_crystal` | Emerald Flame Crystal | Crafting Mat | Legendary | Wicked Witch (F30) drop — forge "Wicked Flame" or "Emerald Curse" |
| `wolfs_tooth` | Wolf's Tooth | Crafting Mat | Legendary | Big Bad Wolf (F20) drop |
| `crimson_hood_scrap` | Crimson Hood Scrap | Accessory Mat | Epic | Big Bad Wolf (F20) drop |
| `vorpal_blade_fragment` | Vorpal Blade Fragment | Crafting Mat | Legendary | Jabberwock (F40) drop |
| `frabjous_page` | Frabjous Page | Key Item | — | Jabberwock (F40) drop — needed with Witch's Broom to access F50 |
| `witchs_broom` | Witch's Broom (Key) | Key Item | — | Wicked Witch (F30) drop — needed with Frabjous Page to access F50 |
| `authors_pen` | The Author's Pen | Accessory | Legendary | Mary Sue (F50) drop |
| `mary_sue_teardrop` | Mary Sue's Teardrop | Crafting Mat | Legendary | Mary Sue (F50) drop |
| `plot_hole_scrap` | Plot Hole Scrap | Consumable | Epic | Mary Sue (F50) drop — skip 1 dungeon room |
| `wonderland_key` | Wonderland Key | Key Item | — | Mary Sue victory — permanent Wonderland access (no book needed) |
| `no_place_charm` | "There's No Place" Charm | Accessory | Legendary | Dorothy permanent-unlock gift — +10% dodge, +1 Wisdom |

---

## 14. Files to Create / Modify

### New Files

| File | Contents |
|---|---|
| `resources/dialogues/wonderland.py` | All 8 NPC dialogue dicts |
| `resources/enemies/enemies_data/wonderland.yaml` | 45+ enemies, 5 superbosses, 3 heroines, 20 floor bosses |
| `combat/queen_of_hearts.py` | `combat_queen_of_hearts()` |
| `combat/big_bad_wolf.py` | `combat_big_bad_wolf()` |
| `combat/jabberwock.py` | `combat_jabberwock()` |
| `combat/wicked_witch.py` | `combat_wicked_witch()` |
| `combat/mary_sue.py` | `combat_mary_sue()` |
| `combat/mary_sue_shadows.py` | Shadow boss factory helpers |

### Modified Files

| File | Change |
|---|---|
| `resources/cities.py` | Add `CITIES["wonderland"]` entry, dialogue imports, empty travel connections |
| `resources/city_maps.py` | Add `CITY_MAPS["wonderland"]` ASCII art |
| `resources/enemies/enemy_races.py` | Add `"Storybook"` race |
| `resources/enemies/biome_races.py` | Add `"wonderland"` biome |
| `resources/enemies/__init__.py` | Ensure wonderland.yaml is picked up by loader |
| `resources/items.py` | Add all new item definitions |
| `city_dialogue.py` | Import wonderland dialogue refs |
| `dungeon.py` | Add wonderland region superboss dispatch, dual-race filter |
| `facilities/arcane_tower.py` | Add "Investigate mysterious book" option for Veilholt |
| `facilities/inn.py` | Add heroine interaction menu for wonderland city_id |
| `gui/screens/travel_screen.py` | Add Cheshire Cat map replacement when `wonderland_active` |
| `combat/ally.py` | Handle `_wonderland_temp` flag, `_heroine_key` field |
| `combat/ally_skills.py` | Alice, Red Hood & Dorothy innate/permanent skills |
| `resources/skill_book/` | Alice, Red Hood & Dorothy skill YAML entries |
| `events.py` | Wonderland unlock event |

---

## 15. Implementation Order

| Phase | Tasks | Dependencies |
|---|---|---|
| **1** | Storybook race + wonderland biome in race files | None |
| **2** | Wonderland YAML: all 30+ regular enemies | Phase 1 |
| **3** | City entry in `cities.py` (empty travel connections) | Phase 1 |
| **4** | NPC dialogues in `dialogues/wonderland.py` + import in `city_dialogue.py` | Phase 3 |
| **5** | ASCII map in `city_maps.py` | Phase 3 |
| **6** | New items in `items.py` | None |
| **7** | Wonderland unlock condition + unlock event in `events.py` | Phase 3 |
| **8** | Veilholt Arcane Tower "mysterious book" entry point | Phase 7 |
| **9** | Ally benching + time freeze system (enter/exit logic) | Phase 8 |
| **10** | Cheshire Cat world map replacement (travel_screen.py) | Phase 9 |
| **11** | Wonderland superboss dispatch logic in `dungeon.py` (+ every-2-floor boss trigger, 50-floor cap) | Phase 2 |
| **12** | `combat/queen_of_hearts.py` (F10 superboss) | Phase 11 |
| **13** | `combat/big_bad_wolf.py` (F20 superboss) | Phase 11 |
| **14** | `combat/wicked_witch.py` (F30 superboss) | Phase 11 |
| **15** | `combat/jabberwock.py` (F40 superboss) | Phase 11 |
| **16** | `combat/mary_sue.py` + `mary_sue_shadows.py` (F50 superboss) | Phases 12, 13, 14, 15 |
| **17** | Heroine ally templates, skills, inn interaction (all 3) | Phase 3 |
| **18** | Heroine permanent-unlock logic (superboss defeat hooks) | Phases 13, 14, 15, 16 |
| **19** | 20 regular floor bosses + F41-48 enemies (YAML entries + AI patterns) | Phase 2 |
| **20** | Integration test: enter → recruit → F10 → F20 → F30(Witch+Dorothy) → F40(Jabberwock+Alice) → F50 → leave → verify | All |
