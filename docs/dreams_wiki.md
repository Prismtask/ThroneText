# Pandemonium — Dreams Wiki

> Generated from the dream registry (`resources/dreams.py`) and runtime (`dreams.py`). Regenerate the web wiki with `tests/gen_wiki_html.py`.

Sleep is a scene, not a button. Every night at **home**, at an **inn**, or at **camp** can bring a dream — short, atmospheric, sometimes useful, sometimes unsettling.

## Contents

1. [How Dreams Work](#how-dreams-work)
2. [Boon Dreams](#boon-dreams)
3. [Burden Dreams](#burden-dreams)
4. [Choice Dreams](#choice-dreams)
5. [Dreams by Location](#dreams-by-location)
6. [Story Dreams (spoilers)](#story-dreams-spoilers)
7. [Dreams, Sleep & Stress](#dreams-sleep--stress)
8. [The Dream Journal](#the-dream-journal)

---

## How Dreams Work

- **One roll per sleep** — 20% base chance, after the day rolls. A dreamless night is normal.
- **Soft pity** — after 5 dreamless nights in a row, the chance rises by 5% per further night (capped at 60%).
- **Repeat decay** — a dream you have seen before weighs 60% of its original weight per sighting, down to a 20% floor.
- **Context weighting** — burden dreams ×2 while a party girl is at 60+ stress, ×1.5 at 2+ fatigue stacks, ×0.5 right after another burden (no spirals). Bond dreams ×2 with an engaged or married girl in the party; memory/omen dreams ×1.5 on the first dream in a new place.
- **Once vs repeat** — some dreams happen only once per save; the rest can return.
- **Skip** — a choice dream you have already had adds a **Wake up** option that takes nothing from you.
- **Never while time is frozen** — no dreams in Wonderland or Event Horizon, and none on the death path.
- Every dream writes a **[DREAM]** entry to your Journal.

---

## Boon Dreams

| Dream | When | Effect |
|---|---|---|
| **The Forgiven Page** | once, day 3+ | +10 XP — a line of the Accord's ledger stays with you |
| **The Unlearned Kata** | any | +35 XP |
| **Deeper Than the Well** | any | **Dream-Blessed**: +1 all attributes for the party, 2 rooms |
| **The Grey Cat's Favour** | any | +5% crit chance, 2 rooms |
| **The Smaller Hand** | any | A **Healing Potion** (skipped if your bag is full) |
| **A Fire That Needs No Wood** | party required | +2 affection with a companion |
| **The Tide That Stays** | party required | −6 stress for every companion |

**Dream-Blessed** is a sleep buff: it merges with Well-Rested and Shared Night rather than stacking, and wears off as you clear dungeon rooms. The HUD tags it **DRM**.

---

## Burden Dreams

Burdens never take items, stats, levels, or progression — and two burdens never happen in a row.

| Dream | When | Effect |
|---|---|---|
| **Under the Door** | any | **+34 player stress**, +8 companion stress |
| **The Watch Nobody Set** | any | +20 player stress, +4 companion stress, **+5 XP** (the small mercy) |
| **The Polite Visitor** | day 2+ | Loses gold — capped at **5% of your purse or 50g**, whichever is lower |
| **A Corridor of Doors** | any | Flavor only — a warning you cannot quite remember |

---

## Choice Dreams

Each option shows its trade-off in the button text. The safe option pays in buffs, XP or affection; the bold one pays in power and **stress**.

### The Offered Hand

- **Take the hand.** +10% damage for 2 rooms · **+20 stress**
- **Refuse, and walk on.** +15 XP

### The Accord Echo *(once, day 5+)*

- **Listen to the whole clause.** +35 XP · **+20 stress**
- **Cover your ears and sleep.** Dream-Blessed for the party, 1 room

### The Mirror Self

- **Hold its gaze.** +25 XP · **+15 stress**
- **Look away and wake.** +5% crit for 2 rooms

### The Feast *(party required)*

- **Eat your fill.** Dream-Blessed for the party, 2 rooms
- **Save the seat for someone.** +3 affection

---

## Dreams by Location

| Dream | Where | Effect |
|---|---|---|
| **The Hearth's Song** | home only | Dream-Blessed for the party, 2 rooms |
| **The House Remembers** | home only, once, day 4+ | +10 XP |
| **The Road's Patience** | camp only | +25 XP |
| **The Rented Room** | inn only | +5 companion stress |

---

## Story Dreams (spoilers)

Story dreams never roll. They queue themselves the night their condition is met and arrive on your **next sleep**, can set story flags, and never repeat.

| Dream | Arrives when |
|---|---|
| **The First Night Not Alone** | after your first Shared Night (requires intimacy content to be on) |
| **The Lamp in the Unbuilt Room** | after a conception (requires the family system to be enabled and intimacy content on) |
| **The Archive That Rains Upward** | after the Voss & Lumen epilogue *"The First Page"* |
| **The Counting in the Walls** | while a **Vampire** companion is in your living party |

---

## Dreams, Sleep & Stress

- Dreams fire **after** the sleep reset, so a dream can leave you tense even though you slept.
- **Player stress** is 0–100. It reaches you through skipped nights (+50 each), burden dreams, and companions falling in combat (+34 each). Every full 100 becomes **one fatigue stack**.
- At **67+ stress you are Rattled** — the HUD shows an eye marker, hallucinations gain a tier, and they can find you without exhaustion.
- **Companions** carry their own 0–100 stress with banded penalties in combat: Weary (50+) −1, Frayed (75+) −2, Burned Out (90+) −3 to all attributes, and Burned Out girls **refuse** that fight. A real sleep takes 10 stress off each companion.
- **Only real sleep** (home bed, inn Sleep, or camp) clears your stress. Resting at an inn for a block does not.

---

## The Dream Journal

Every dream you have seen is kept in **Inventory → Journal → Dreams** — name, category, the full text, and how often it has found you, with a "seen X of Y" header.

The Journal's **Event** tab also carries a `[DREAM]` entry for each night a dream occurred, including which choice you made.

> This page is generated from the live dream registry; the run-in-game collection is the authoritative list.
