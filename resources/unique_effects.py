"""resources/unique_effects.py — Equip-effect blurbs for unique equipment.

Every unique item's `special` effect should be explainable somewhere the
player can actually read it. The inventory Examine popup (bag + equipped
rows) is that place: it shows "Equip Effect: ..." using the text here.

Conventions:
- One short, honest, player-facing summary per special — key numbers only.
  Never advertise an effect the code does not implement.
- Wedding accessories are NOT listed here; their blurbs live with their
  implementation in ``combat/weapon/wedding_specials.py``
  (``wedding_special_blurb``), including the bonded (girl in party) upgrade.
- Flavour-only specials are listed explicitly with a no-effect note so the
  Examine popup tells the truth instead of staying silent.

Lookup helper: ``unique_effect_text(special)`` returns "" for unknown
specials (callers then fall back to the wedding registry, or show nothing).
"""

# ── Superboss drops ──────────────────────────────────────────────────────
UNIQUE_EFFECTS = {
    "dream_devour": (
        "Wield the Abyss (action): pay 40% of max HP for +8 STR (4 turns) — "
        "and from the next round, act 3 times per round for 4 rounds. "
        "6-turn cooldown."
    ),
    "tarnished_jade": (
        "Taking hits embeds Jade Pins (max 10; +1 STR/WIS per 2 pins). Pins "
        "deal 5% max-HP damage per pin at turn start. At 20% HP or less they "
        "shatter: 6+ pins — Divine Lament (all enemies take pins × (STR+WIS)/2; "
        "wearer heals 5% max HP per pin); fewer pins — Wedge Backlash (halved "
        "blast, but the wearer's stats are halved for the battle)."
    ),
    "captain_cutlass": (
        "Kills build High Tide (max 5: +5% damage dealt and +10% damage taken "
        "per stack, for the floor). Crew Rally (5-turn cooldown): party +3 DEX "
        "and +20% attack, damage reduction of 5% per party member, and High "
        "Tide's vulnerability is suppressed. When attacked, riposte up to "
        "twice a turn."
    ),
    "vileheart_venom": (
        "Physical attacks have a 25% chance to poison (4 damage × 3 turns), "
        "rising to 50% against an already-poisoned target."
    ),
    "black_silence_gloves": (
        "Replaces all class skills with 9 one-use workshop attacks and the "
        "Furioso finisher. +3 initiative, +8% dodge, +15% damage when acting "
        "first. Workshop damage scales with the gloves' enhance level."
    ),
    "painters_touch": (
        "Replaces class skills with the brush's own kit: commit a colour each "
        "turn for 1.35× elemental attacks; 3 strokes complete a painting "
        "(Pigment Explosion, +50%) and grant a pigment — up to 3 rankable "
        "auras. Exhibits unlock at 6/12/18 lifetime strokes."
    ),
    "blank_canvas": (
        "Once per combat, free action: cleanse all debuffs, heal 15% max HP "
        "and gain Afterimage (blocks the next 2 debuffs) — but it also wipes "
        "the wearer's own buffs. In Palette's hands the cleanse and heal "
        "become party-wide (10% max HP each)."
    ),
    "chronoweave": (
        "Below 50% HP at turn start: gain 1 Momentum stack (max 10; +3% "
        "damage each). Once per floor, survive a fatal blow at 1 HP and gain "
        "+50% dodge for 1 turn."
    ),
    "last_oath": (
        "Basic attacks reduce the target's armour by 1 (2 on a critical hit)."
    ),
    "authors_pen": (
        "While in Wonderland: +4 to all stats. Rewrite (action, 5-turn "
        "cooldown): heal the party for all damage taken during the previous "
        "round — fallen allies are not revived."
    ),

    # ── Guild legacy accessories ─────────────────────────────────────────
    "sky_piercer": (
        "Attacks instantly execute a non-superboss enemy left at 5% max HP "
        "or less (+3% per enhance level, up to 20%)."
    ),
    "prescript_ledger": (
        "Each round issues a Prescript: fulfil it for Grace (up to 9 stacks — "
        "+2% damage, +1.5% crit and 1.5% max-HP regen each, plus a skill clash "
        "bonus at 3/6/9). Ignoring a feasible order adds Karma (+3% damage "
        "taken per stack); at 6 stacks, Karmic Retribution strikes."
    ),

    # ── Event Horizon trophies ───────────────────────────────────────────
    "chance_and_choice": (
        "Once per damaging action, flip a coin: 50% — ×0.25 damage; 50% — "
        "×1.75 damage. Averages out to exactly normal."
    ),
    "dopo_robe": (
        "While the wearer wields a sword-family weapon: the wearer deals "
        "×1.40 damage, +5% per sword-wielding ally (all recruited allies "
        "count, even benched — uncapped); each sword-wielding ally deals ×1.15."
    ),
    "piece_of_relationship": (
        "Tiers by bonded allies (200 affection, active or benched): 2–3 — MC "
        "+10% damage; 4–6 — +10% damage, +2% dodge and crit; 7+ — +20% damage, "
        "+5% dodge and crit, and enemies that attack allies gain Hunter's Mark "
        "(+20% damage taken, 2 turns). Bonded allies gain +5%/10%/15% damage "
        "by tier. MC only."
    ),

    # ── Wonderland heroine gear ──────────────────────────────────────────
    "vorpal_rusted": (
        "Alice's blade. While she wields it, her innate skills become her "
        "true Wonderland kit (Vorpal Edge, Snicker-Snack). Can be reforged "
        "into the Vorpal Blade."
    ),
    "vorpal_blade": (
        "Alice's reforged blade. While she wields it, her innate skills become "
        "Vorpal Edge and Snicker-Snack — and Frabjous Day once its upgrade is "
        "unlocked."
    ),
    "woodcutter_broken": (
        "Basic attacks have a 20% chance to detonate the target's strongest "
        "bleed for 3× its damage; in Red Hood's hands it also awakens her true "
        "skills (What Big Teeth, Fell the Wolf). Can be reforged into "
        "Grandmother's Axe."
    ),
    "grandmothers_axe": (
        "Basic attacks have a 40% chance to detonate the target's strongest "
        "bleed for 3× its damage; in Red Hood's hands it also awakens her true "
        "skills (What Big Teeth, Fell the Wolf — plus Through the Forest once "
        "upgraded)."
    ),
    "silver_slippers": (
        "Dorothy's slippers. While she wears them, her innate skills become "
        "her true Wonderland kit (Cyclone's Call, Heart of Tin). Can be "
        "upgraded to the Ruby Slippers."
    ),
    "ruby_slippers": (
        "Dorothy's ruby slippers. While she wears them, her innate skills "
        "become Cyclone's Call and Heart of Tin — and Emerald City's Light "
        "once its upgrade is unlocked."
    ),

    # ── Flavour-only specials (no combat implementation) ─────────────────
    "silent_visage": "No active combat effect — worn for its stat bonuses.",
    "rose_crown": "No active combat effect — worn for its stat bonuses.",
    "im_melting": "No active combat effect — worn for its stat bonuses.",
    "pocket_watch": "No active combat effect — worn for its stat bonuses.",
    "no_place": "No active combat effect — worn for its stat bonuses.",
}


def unique_effect_text(special):
    """Return the equip-effect blurb for a unique special, or "" if none.

    Wedding accessories are not in this registry — callers should fall back
    to ``combat.weapon.wedding_specials.wedding_special_blurb``.
    """
    if not special:
        return ""
    return UNIQUE_EFFECTS.get(special, "")
