# Pandemonium — Items Overhaul Blueprint

> **Status:** Design Phase  
> **Target:** Replace the current rarity-dominated item system with one where elemental identity, weapon choice, and skill-vs-consumable balance all matter.

---

## Table of Contents

1. [Rarity Rework](#1-rarity-rework)
2. [Elemental Trait System](#2-elemental-trait-system)
3. [Equipment Redesign](#3-equipment-redesign)
    - [3a. Elemental Naming Convention — Evaluation](#3a-elemental-naming-convention--evaluation)
4. [Unique Items — The Red Tier](#4-unique-items--the-red-tier)
5. [Consumable Overhaul](#5-consumable-overhaul)
6. [Dungeon Drop Chance Rework](#6-dungeon-drop-chance-rework)
7. [Facilities That Need Updating](#7-facilities-that-need-updating)
8. [Migration Checklist](#8-migration-checklist)

---

## 1. Rarity Rework

### Current State (Problem)

```
common    1.0×  →  uncommon 1.3×  →  rare 1.7×  →  epic 2.4×  →  legendary 3.5×
```

- Legendary is **3.5× stronger** than common. This gap is so large that base item identity is irrelevant.
- A Common Greatsword (5 STR → 5 mods) is strictly worse than a Legendary Short Sword (2 STR → 7 mods).
- Pandemonium mode's generous drop rates make legendary the de facto baseline.

### Proposed State

```
common    1.00×  →  uncommon 1.15×  →  rare 1.35×  →  epic 1.60×  →  legendary 1.90×
```

| Tier | Stat Mult | Price Mult | Old Stat Mult | Old Price Mult |
|---|---|---|---|---|
| Common | 1.00× | 1.0× | 1.0× | 1.0× |
| Uncommon | 1.15× | 1.4× | 1.3× | 1.5× |
| Rare | 1.35× | 2.2× | 1.7× | 3.0× |
| Epic | 1.60× | 4.0× | 2.4× | 6.0× |
| Legendary | 1.90× | 8.0× | 3.5× | 12.0× |
| **Unique** | **Varies** | **N/A** | *(was legendary)* | *(was 12.0×)* |

**Key changes:**
- Legendary is now **1.9×** instead of 3.5× — still the best, but doesn't delete item identity.
- A Common Greatsword (5 STR) now beats a Legendary Short Sword (2 × 1.9 ≈ 4 STR). Weapon choice matters again.
- Price multipliers also reduced, since the power gap is narrower.
- **Unique items** leave the rarity ladder entirely (see §4).

### Code Change: `resources/items.py`

```python
ITEM_RARITY = {
    "common":    {"stat_mult": 1.00, "price_mult": 1.0},
    "uncommon":  {"stat_mult": 1.15, "price_mult": 1.4},
    "rare":      {"stat_mult": 1.35, "price_mult": 2.2},
    "epic":      {"stat_mult": 1.60, "price_mult": 4.0},
    "legendary": {"stat_mult": 1.90, "price_mult": 8.0},
    "unique":    {"stat_mult": 1.00, "price_mult": 1.0},  # unused — uniques don't use this
}
```

The `unique` entry exists only so `build_item` doesn't crash if passed `rarity="unique"` — but unique items should **never** go through the stat_mult scaling path.

---

## 2. Elemental Trait System

### Current State (Problem)

Elements are purely multiplicative damage-type modifiers. A Fire weapon and a Dark weapon play exactly the same — you press "Attack" and a different multiplier is checked against enemy resistances. No behavioral difference.

### Proposed State

Every element gains a **combat trait** — a passive effect that triggers on-hit, on-kill, or conditionally. The trait is an intrinsic property of the weapon, not a separate buff.

| Element | Trait Name | Effect | Scaling |
|---|---|---|---|
| **Physical** | Sunder | +15% armor penetration on this attack | *(static)* |
| **Fire** | Ignite | Applies Burn: 3% max HP / turn, 3 turns | +1% per rarity tier above common |
| **Water** | Douse | On kill: reduce 1 random skill cooldown by 1 | +1 extra skill at epic+ |
| **Thunder** | Chain | 15% chance: 40% splash damage to 1 adjacent enemy | +5% chance per rarity tier |
| **Wind** | Swift | +2 initiative for 1 turn after attacking (stacks 2×) | +1 init per rarity tier |
| **Earth** | Bulwark | +8% damage reduction for 1 turn after attacking | +2% per rarity tier |
| **Light** | Purge | On kill: remove 1 random debuff from self | +1 debuff at rare+ |
| **Dark** | Leech | Heal for 8% of damage dealt | +2% per rarity tier |
| **Magical** | Pierce | Ignores 25% of target elemental resistance | +5% per rarity tier |

**Design notes:**
- Traits are **per-weapon**, determined by the weapon's **primary element** (the highest-value entry in `elemental_dmg`).
- If a weapon has multiple elements (e.g., `{"fire": 1.3, "earth": 1.1}`), the primary is Fire → Gets Ignite.
- Rarity amplifies the trait, not just raw stats. A Legendary Fire Sword burns *harder*, not just hits harder.
- Trait effects are applied in `player_actions.py` during the attack resolution, after damage is dealt.

### Code Change: New Module `combat/elemental_traits.py`

```python
# combat/elemental_traits.py

ELEMENTAL_TRAITS = {
    "physical": {
        "name": "Sunder",
        "desc": "+{pct}% armor penetration",
        "on_hit_armor_pen": 0.15,  # base 15%
        "rarity_bonus": 0.0,       # no scaling — static
    },
    "fire": {
        "name": "Ignite",
        "desc": "Applies Burn: {pct}% max HP/turn for 3 turns",
        "on_hit_burn_pct": 0.03,
        "rarity_bonus": 0.01,      # +1% per tier above common
    },
    "water": {
        "name": "Douse",
        "desc": "On kill: reduce {n} skill cooldown(s) by 1",
        "on_kill_cd_reduce": 1,
        "rarity_bonus": 0,         # becomes 2 at epic+
    },
    "thunder": {
        "name": "Chain",
        "desc": "{pct}% chance: 40% splash to adjacent enemy",
        "on_hit_chain_chance": 0.15,
        "on_hit_chain_pct": 0.40,
        "rarity_bonus": 0.05,      # +5% chance per tier
    },
    "wind": {
        "name": "Swift",
        "desc": "+{n} initiative for 1 turn after attacking",
        "on_hit_init_bonus": 2,
        "rarity_bonus": 1,
    },
    "earth": {
        "name": "Bulwark",
        "desc": "+{pct}% damage reduction for 1 turn after attacking",
        "on_hit_def_bonus": 0.08,
        "rarity_bonus": 0.02,
    },
    "light": {
        "name": "Purge",
        "desc": "On kill: remove {n} debuff(s) from self",
        "on_kill_cleanse": 1,
        "rarity_bonus": 0,         # becomes 2 at rare+
    },
    "dark": {
        "name": "Leech",
        "desc": "Heal for {pct}% of damage dealt",
        "on_hit_leech_pct": 0.08,
        "rarity_bonus": 0.02,
    },
    "magical": {
        "name": "Pierce",
        "desc": "Ignores {pct}% of target resistance",
        "on_hit_res_ignore": 0.25,
        "rarity_bonus": 0.05,
    },
}

RARITY_TIER = {"common": 0, "uncommon": 1, "rare": 2, "epic": 3, "legendary": 4}


def get_primary_element(weapon: dict) -> str | None:
    """Return the element with the highest dmg multiplier on a weapon, or None."""
    ele_dmg = weapon.get("elemental_dmg", {})
    if not ele_dmg:
        return None
    return max(ele_dmg, key=ele_dmg.get)


def get_trait_for_weapon(weapon: dict, rarity: str) -> dict | None:
    """Return the resolved trait dict for a weapon, with rarity bonuses applied."""
    element = get_primary_element(weapon)
    if element is None:
        return None
    trait = ELEMENTAL_TRAITS.get(element)
    if trait is None:
        return None
    tier = RARITY_TIER.get(rarity, 0)
    bonus = trait.get("rarity_bonus", 0)
    # Clone and apply bonus
    resolved = dict(trait)
    for key in ("on_hit_burn_pct", "on_hit_chain_chance", "on_hit_leech_pct",
                "on_hit_res_ignore", "on_hit_def_bonus", "on_hit_init_bonus"):
        if key in resolved:
            resolved[key] = resolved[key] + bonus * tier
    # Special cases for non-linear scaling
    if element == "water" and tier >= 3:
        resolved["on_kill_cd_reduce"] = 2
    if element == "light" and tier >= 2:
        resolved["on_kill_cleanse"] = 2
    return resolved
```

### Integration Point: `combat/player_actions.py`

After damage is dealt and the target takes HP loss, call the trait hook:

```python
# In the attack resolution section, after:
#   target["hp"] -= final_dmg
#   add_tarnished_jade_pin(player)

# NEW: Apply elemental weapon trait
from combat.elemental_traits import get_trait_for_weapon
trait = get_trait_for_weapon(equipped_weapon, equipped_weapon.get("rarity", "common"))
if trait:
    _apply_elemental_trait(trait, player, target, enemies, final_dmg)
```

Where `_apply_elemental_trait` dispatches to the relevant effect. This function lives in `elemental_traits.py`:

```python
def apply_trait(trait: dict, player: dict, target: dict, enemies: list, damage: int):
    """Apply an elemental trait's effects after a successful hit."""
    # Burn (Fire)
    if "on_hit_burn_pct" in trait:
        burn_dmg = max(1, int(target.get("max_hp", 100) * trait["on_hit_burn_pct"]))
        from combat.status_effects import apply_burn  # new
        apply_burn(target, burn_dmg, 3)
        c_print(f"  🔥 Ignite! {target['name']} burns for {burn_dmg}/turn (3 turns).")

    # Chain (Thunder)
    if "on_hit_chain_chance" in trait:
        if random.random() < trait["on_hit_chain_chance"]:
            # Find an adjacent enemy (not the target)
            others = [e for e in enemies if e is not target and e.get("hp", 0) > 0]
            if others:
                splash_target = random.choice(others)
                splash_dmg = int(damage * trait.get("on_hit_chain_pct", 0.40))
                splash_target["hp"] = max(0, splash_target["hp"] - splash_dmg)
                c_print(f"  ⚡ Chain! {splash_dmg} splash damage to {splash_target['name']}.")

    # Leech (Dark)
    if "on_hit_leech_pct" in trait:
        heal = int(damage * trait["on_hit_leech_pct"])
        if heal > 0:
            max_hp = player_max_hp(player)
            old = player.get("current_hp", 0)
            player["current_hp"] = min(old + heal, max_hp)
            actual = player["current_hp"] - old
            if actual > 0:
                c_print(f"  🩸 Leech! You recover {actual} HP.")

    # Swift (Wind)
    if "on_hit_init_bonus" in trait:
        bonus = trait["on_hit_init_bonus"]
        player.setdefault("active_buffs", []).append({
            "type": "initiative",
            "value": bonus,
            "remaining": 1,
            "source": "wind_trait",
        })

    # Bulwark (Earth)
    if "on_hit_def_bonus" in trait:
        pct = trait["on_hit_def_bonus"]
        player.setdefault("active_buffs", []).append({
            "type": "defense",
            "value": pct,  # stored as decimal; applied as (1 - pct) multiplier
            "remaining": 1,
            "source": "earth_trait",
        })

    # Sunder (Physical) — applied BEFORE damage, so handled in damage calc
    # Pierce (Magical) — applied BEFORE damage, so handled in damage calc
    # Douse (Water) & Purge (Light) — applied ON KILL, handled in kill resolution
```

Sunder and Pierce are pre-damage modifiers and would be applied in the damage calculation step:

```python
# In the attack damage calculation (player_actions.py):
if trait and "on_hit_armor_pen" in trait:
    armor = int(armor * (1 - trait["on_hit_armor_pen"]))
if trait and "on_hit_res_ignore" in trait:
    effective_res = {k: 1.0 + (v - 1.0) * (1 - trait["on_hit_res_ignore"])
                     for k, v in target.get("elemental_res", {}).items()}
```

---

## 3. Equipment Redesign

### Current State

Every weapon/armor/accessory is a stat stick. The `base_mods` dict + `rarity × stat_mult` + `enhance` determines everything. Elemental profiles exist but are passive multipliers.

### Proposed Changes

**A. Every weapon gets a declared primary element.**

Currently weapons have `elemental_dmg` dicts like `{"physical": 1.2, "earth": 1.1}`. The highest-value entry becomes the **primary element** and determines the trait. This requires no new fields — just a resolution function.

**B. Weapons gain differentiation through trait + base identity.**

A Short Sword and a Greatsword now differ in:
- Base stat mods (Greatsword has more STR)
- Scaling stat (STR vs DEX vs LRN vs ...)
- Primary element → trait (Fire Greatsword burns, Dark Dagger leeches)
- Elemental damage profile (which resistances it hits)

Since rarity only goes to 1.9×, the base stats matter more. A player chooses between:
- **Epic Short Sword** (DEX scaling, Wind trait → initiative stacking) — fast, evasive playstyle
- **Rare Greatsword** (STR scaling, Fire trait → burn pressure) — heavy, DoT playstyle

This is an *interesting choice* instead of a math problem.

**C. Armor and accessories also get traits (but softer).**

| Slot | Trait Source | Effect |
|---|---|---|
| Weapon | Primary element (full trait) | On-hit combat effects |
| Armor | Primary element (half trait) | Defensive element trait (e.g., Earth armor gives 4% DR per hit instead of 8%) |
| Accessory | Primary element (utility trait) | Non-combat or passive (e.g., Wind accessory gives +movement on world map) |

Armor/accessory traits are secondary — weapons are the star.

**D. Elemental Naming Convention**

Every generic equipment piece gets a `[Element Prefix] + [Weapon Type]` name (e.g., "Ember Greatsword", "Storm Dagger", "Frost Staff"). Unique items keep their distinctive names. Full evaluation and naming framework in [§3a](#3a-elemental-naming-convention--evaluation).

**Example — Before and After:**

```python
# Before (current):
"greatsword": {"name": "Greatsword", "slot": "weapon",
    "base_mods": {"Strength": 5}, "scaling_stat": "Strength",
    "elemental_dmg": {"physical": 1.3, "earth": 1.2}},
# Name says: "big sword" — element unknown without inspection

# After (proposed):
"inferno_greatsword": {"name": "Inferno Greatsword", "slot": "weapon",
    "base_mods": {"Strength": 5}, "scaling_stat": "Strength",
    "primary_element": "fire",
    "elemental_dmg": {"physical": 1.3, "fire": 1.3}},
# Name says: "big sword, FIRE element" → Ignite trait, burn build
```

The `"primary_element"` field is explicit on every equipment item — no auto-detection needed. This ensures designers (you) intentionally assign elements rather than relying on alphabetical tiebreaks.

**E. Element-to-Stat-Affinity Matrix**

See the full matrix in [§3a](#3a-elemental-naming-convention--evaluation). Key takeaway: STR builds get 8 elemental options, DEX/LRN get 5, CHA gets 4, WIS/CON get 3. Every build type has meaningful elemental choices.

---

### 3a. Elemental Naming Convention — Evaluation

> **Question:** Should every generic equipment get a unique name that signals its primary element?  
> **Answer:** **Yes, with a structured prefix+type convention, not fully unique names.**  
> **Verdict:** Adds to the blueprint.

---

#### What the Current Naming Does (and Doesn't Do)

Currently, 74 generic equipment pieces have names like:

| Current Name | Signals | Does NOT Signal |
|---|---|---|
| Short Sword | Weapon type, low tier | Element *(what element is this?)* |
| Arcane Staff | Learning scaling, magic | Element *(magical? thunder?)* |
| Silver Sword | Light/holy theme | That it's light-element |
| Elven Bow | Dexterity, racial flavor | Wind? Light? Both? |
| Flail | Weapon type | Fire element |
| Runic Dagger | Hybrid DEX/LRN | Dark? Thunder? Magical? |

Some names *accidentally* hint at elements (`silver_sword` → light, `flail` → fire, `grimoire` → dark), but most don't. The player has no way to know a Flail is fire-element without inspecting its stat card. And since elements currently have no behavioral difference (they're just multipliers), there was never a reason to care. That changes with the elemental trait system.

#### Why Elemental Naming Matters Now

With the trait system (Fire = burn, Dark = leech, Wind = initiative, etc.), the player's weapon element dictates their **playstyle**. A Fire build and a Dark build play differently. The name should communicate this instantly:

| If the player sees... | They immediately know... |
|---|---|
| "Ember Greatsword" | STR scaling, Fire trait → burn pressure build |
| "Storm Dagger" | DEX scaling, Thunder trait → chain splash build |
| "Leech Blade" | STR/DEX scaling, Dark trait → life-steal sustain build |
| "Gale Bow" | DEX scaling, Wind trait → initiative/speed build |
| "Frost Scepter" | WIS scaling, Water trait → cooldown-reset build |

This creates **build identity**. A player says "I'm running a Fire build" and knows to look for "Ember-", "Blaze-", "Inferno-" prefixed gear. Rather than memorizing that `flail` happens to be fire and `war_hammer` happens to be earth.

#### The Risk: Loss of Archetype Readability

"Short Sword" is universally understood as a low-tier STR/DEX weapon. "Ember Blade" requires the player to learn a new vocabulary. This is a real UX cost.

**Mitigation:** Use a **two-axis naming convention** that preserves weapon type while adding elemental identity:

```
[Element Prefix] + [Weapon Type]
```

Examples:
- `Ember Greatsword` — Fire + STR, the player knows it's a greatsword-class weapon
- `Storm Dagger` — Thunder + DEX, the player knows it's a dagger-class weapon
- `Frost Staff` — Water + LRN, the player knows it's a staff-class weapon
- `Grave Maul` — Earth + STR, the player knows it's a maul-class weapon
- `Radiant Sword` — Light + STR, the player knows it's a sword-class weapon

The weapon type (Greatsword, Dagger, Staff, Bow, etc.) anchors the player's existing knowledge. The prefix adds the new elemental layer. This is **learnable in 5 minutes** rather than requiring memorization of 74 unique fantasy names.

#### Avoid: Fully Unique Names

❌ **Don't do this:**
- "Emberfang" (is this a sword? a dagger? what stat?)
- "Stormcaller" (am I supposed to know what this is?)
- "Graveleater" (creative, but communicates nothing)

Fully unique names are great for... unique items. For generic equipment, the player needs to parse *what it is* at a glance. Save the poetic names for the red-tier uniques (Abyss Fang, Vorpal Blade — these already work).

#### The Naming Framework

Each element gets a family of **thematic prefixes** that scale in intensity, and each prefix maps to specific weapon types across stat affinities:

| Element | Low-Tier Prefix | Mid-Tier Prefix | High-Tier Prefix | Weapon Types |
|---|---|---|---|---|
| **Physical** | Iron | Steel | Titan | Sword, Axe, Spear, Bow, Shield |
| **Fire** | Ember | Blaze | Inferno | Greatsword, Axe, Dagger, Staff, Gauntlets, Lute |
| **Water** | Frost | Glacier | Abyssal | Blade, Bow, Orb, Scepter |
| **Thunder** | Spark | Storm | Tempest | Hammer, Dagger, Wand, Chakram |
| **Wind** | Gale | Zephyr | Cyclone | Spear, Bow, Chakram, Crossbow, Harp |
| **Earth** | Stone | Grave | Bedrock | Maul, Axe, Shield, Plate |
| **Light** | Radiant | Divine | Solar | Sword, Staff, Scepter, Mace, Lute |
| **Dark** | Shadow | Void | Nether | Dagger, Blade, Grimoire, Orb, Tongue Dagger |
| **Magical** | Arcane | Mystic | Astral | Staff, Wand, Orb, Tome, Bell |

**Design rule:** Not every element needs weapons for every stat affinity. The matrix should look like this:

| Element | STR | DEX | LRN | WIS | CHA | CON |
|---|---|---|---|---|---|---|
| Physical | Iron Sword, Steel Axe | — | — | — | — | Titan Shield |
| Fire | Ember Greatsword, Blaze Axe | Spark Dagger | Cinder Staff | — | Blaze Lute | Magma Gauntlets |
| Water | Frost Blade | Rime Bow | Torrent Orb | Glacier Scepter | — | — |
| Thunder | Storm Hammer | Volt Chakram | Thunder Wand | — | — | — |
| Wind | Gale Spear | Zephyr Bow, Cyclone Crossbow | — | — | Zephyr Harp | — |
| Earth | Stone Maul, Grave Axe | — | — | — | — | Bedrock Plate |
| Light | Radiant Sword | — | — | Divine Staff | Radiant Lute | — |
| Dark | Void Blade | Shadow Dagger | Nether Grimoire | — | Shadow Tongue Dagger | — |
| Magical | — | — | Arcane Staff, Mystic Wand | Astral Orb | Mystic Bell | — |

This gives:
- **STR builds:** 8 elemental options (Physical, Fire, Water, Thunder, Wind, Earth, Light, Dark)
- **DEX builds:** 5 elemental options (Fire, Water, Thunder, Wind, Dark)
- **LRN builds:** 5 elemental options (Fire, Water, Thunder, Dark, Magical)
- **WIS builds:** 3 elemental options (Water, Light, Magical)
- **CHA builds:** 4 elemental options (Fire, Wind, Light, Dark)
- **CON builds:** 3 elemental options (Physical, Fire, Earth)

Every stat affinity has multiple elemental choices → build diversity.

#### CHA Weapon Design Notes

Charisma weapons are instruments, orator's tools, and subtle implements — not brute-force armaments. Their elemental traits complement support/utility playstyles:

| CHA Weapon | Element | Trait | Playstyle |
|---|---|---|---|
| Blaze Lute | Fire | Ignite (burn DoT) | Aggressive bard — deals supplemental fire damage while buffing |
| Zephyr Harp | Wind | Swift (initiative) | Speed enabler — outspeeds enemies to land debuffs first |
| Radiant Lute | Light | Purge (cleanse on kill) | Support anchor — keeps party debuff-free |
| Shadow Tongue Dagger | Dark | Leech (life steal) | Self-sustaining orator — stays alive through manipulation |
| Mystic Bell | Magical | Pierce (resist ignore) | Pure caster hybrid — CHA/LRN build with unresistable charm |

These replace the current `bards_lute` and `silver_tongue_dagger`, expanding CHA from 2 weapons (with arbitrary elements) to 5 weapons with intentional elemental identities.

#### Armor and Accessories Follow the Same Convention

| Current | Proposed |
|---|---|
| Padded Armor | Iron Padded Armor (Physical) |
| Leather Armor | Gale Leathers (Wind) |
| Chainmail | Steel Chainmail (Physical) |
| Dragonhide | Ember Dragonhide (Fire) |
| Robes | Arcane Robes (Magical) |
| Elven Mail | Zephyr Elven Mail (Wind) |
| Silk Garb | Shadow Silk Garb (Dark) |
| Ring of Power | Ember Ring (Fire) |
| Amulet of Vigor | Stone Amulet (Earth) |
| Cloak of Shadows | Void Cloak (Dark) |

Same prefix system, same learnability.

#### What Stays Unchanged

- **Unique items** (Abyss Fang, Vorpal Blade, wedding rings, etc.) keep their existing names. They're already distinctive.
- **Item IDs** can remain the same internally if we want to minimize code churn — only the `"name"` field changes for display. Or we rename IDs too for consistency. This is an implementation choice.
- **The `ITEMS` dict structure** doesn't change — we just update `"name"` and `"elemental_dmg"` values, and add an explicit `"primary_element"` field.

#### Concrete Example: Before and After

**Before (current `resources/items.py`):**
```python
"battle_axe":   {"name": "Battle Axe",  "slot": "weapon",
    "base_mods": {"Strength": 4}, "scaling_stat": "Strength",
    "elemental_dmg": {"physical": 1.3, "earth": 1.1}},

"flail":        {"name": "Flail",       "slot": "weapon",
    "base_mods": {"Strength": 3, "Constitution": 1}, "scaling_stat": "Strength",
    "elemental_dmg": {"physical": 1.2, "fire": 1.3}},

"war_hammer":   {"name": "War Hammer",  "slot": "weapon",
    "base_mods": {"Strength": 5}, "scaling_stat": "Strength",
    "elemental_dmg": {"physical": 1.3, "earth": 1.3}},
```

**After (proposed):**
```python
"blaze_axe":   {"name": "Blaze Axe",  "slot": "weapon",
    "base_mods": {"Strength": 4}, "scaling_stat": "Strength",
    "primary_element": "fire",
    "elemental_dmg": {"physical": 1.3, "fire": 1.3}},

"inferno_flail": {"name": "Inferno Flail", "slot": "weapon",
    "base_mods": {"Strength": 3, "Constitution": 1}, "scaling_stat": "Strength",
    "primary_element": "fire",
    "elemental_dmg": {"physical": 1.2, "fire": 1.3}},

"grave_maul":  {"name": "Grave Maul",  "slot": "weapon",
    "base_mods": {"Strength": 5}, "scaling_stat": "Strength",
    "primary_element": "earth",
    "elemental_dmg": {"physical": 1.3, "earth": 1.3}},
```

Notice: `battle_axe` (earth) → `blaze_axe` (fire). The old elemental assignment was arbitrary. The new one is intentional. Each element gets a clear lane.

#### Scope of Changes

| What | Count | Effort |
|---|---|---|
| Generic weapons to rename | ~23 | Medium — rename + reassign elements intentionally |
| Generic armor to rename | ~15 | Low — same pattern |
| Generic accessories to rename | ~25 | Low — same pattern |
| Unique items | ~60 | **None** — keep existing names |
| `build_item()` calls in boss files | ~10 | Low — update item_id strings |
| `_HEROINE_EQUIPMENT_BUILDS` | 3 heroines × 4 slots | Low — update item_id strings |
| `_random_item_id()` pools | 2 files | Low — pools auto-update from ITEMS dict |
| Save files | Affected | Items stored with `"id"` field — migration needed |

The migration is ~63 renamed items + ~15 call-site updates. Manageable in a day or two.

#### Verdict: **YES, add to the blueprint.**

The two-axis `[Element Prefix] + [Weapon Type]` convention:
- Makes elemental build identity immediately readable
- Preserves weapon type familiarity
- Is learnable in minutes (9 prefixes × 3 tiers = 27 words to learn)
- Creates natural build diversity (Fire build vs Dark build vs Wind build)
- Costs ~63 renames + ~15 call-site updates
- Unique items keep their existing distinctive names

The alternative — keeping generic names — means the elemental trait system is hidden behind stat-card inspection. The player would need to hover over every "Battle Axe" to discover it happens to be earth-element. That defeats the purpose of making elements matter.

---

## 4. Unique Items — The Red Tier

### Current State

Unique items like Abyss Fang, Tarnished Jade, and Vorpal Blade have `"drop_rarity": "legendary"`. They:
- Use the legendary stat multiplier (3.5×)
- Display in gold (`#f1c40f`) — same color as any legendary
- Cannot drop from normal enemies (excluded via `_EXCLUDED_ITEM_IDS`)
- Have `"unique": True` but this only controls drop exclusion, not behavior

There's already a `RARITY_MYTHIC` color (`#ff6b6b` — red) defined in `gui/theme.py` but it's unused in the rarity color map and not referenced anywhere meaningful.

### Proposed State

Unique items become their own tier — **Unique (Red)** — completely outside the rarity ladder.

**Rules for Unique items:**
1. They have `"rarity": "unique"` — NOT "legendary"
2. They do **not** go through `build_item`'s stat_mult scaling. Their stats are hand-tuned.
3. They display in **red** (`#ff6b6b`) — visually distinct from legendary gold
4. They have the `"unique": True` flag + a `"special"` effect (already the case)
5. They cannot be enhanced at the blacksmith (or: enhanced only to +5 instead of +10)
6. They cannot have their rarity changed via Scroll of Fusion
7. They drop ONLY from their specific boss source — never random
8. The `build_item` function must handle `rarity="unique"` as a special case

### Code Change: `resources/items.py` — `build_item`

```python
def build_item(item_id, rarity="common", enhance=0):
    base = ITEMS[item_id]

    # Unique items bypass the rarity scaling system entirely
    if base.get("unique") or rarity == "unique":
        return _build_unique_item(item_id, base, enhance)

    # ... rest of existing build_item logic ...
```

```python
def _build_unique_item(item_id, base, enhance=0):
    """Build a unique item with hand-tuned stats, bypassing rarity scaling."""
    item = {
        "id": item_id,
        "name": base["name"],  # no rarity prefix like "Legendary ..."
        "type": base["type"],
        "rarity": "unique",    # fixed
        "enhance": enhance,
    }

    if base["type"] == "equipment":
        item["slot"] = base["slot"]
        # Unique items use their base_mods AS-IS (no stat_mult multiplication)
        item["mods"] = {
            stat: val + enhance
            for stat, val in base["base_mods"].items()
        }
        # Carry over special properties
        for key in ["special", "unique", "drop_source", "scaling_stat",
                     "scaling_mult", "con_defense", "elemental_dmg", "elemental_res"]:
            if key in base:
                item[key] = base[key]
    elif base["type"] in ("consumable", "utility", "crafting_material", "key_item"):
        item["count"] = 1
        for key in ["power", "base_power", "special", "drop_source",
                     "temp_stat", "duration", "heal_over_time"]:
            if key in base:
                item[key] = base[key]

    return item
```

### Unique Item Stat Tuning

Since uniques no longer get the 3.5× legendary multiplier, their `base_mods` need to be tuned to feel powerful. Example recalculations:

| Item | Old (Legendary 3.5×) | New (Unique, hand-tuned) |
|---|---|---|
| Abyss Fang | STR 6×3.5=21, DEX 3×3.5=10.5 | STR 18, DEX 9 → still ~legendary power |
| Tarnished Jade | CON 5×3.5=17.5, WIS 4×3.5=14 | CON 15, WIS 12 |
| Vorpal Blade | STR 8×3.5=28, DEX 5×3.5=17.5 | STR 22, DEX 14 |
| Black Silence Gloves | STR 4×3.5=14, DEX 4×3.5=14, LRN 3×3.5=10.5 | STR 12, DEX 12, LRN 9 |

The special effects (dream_devour, tarnished_jade, vorpal_blade, etc.) already carry significant power — the raw stats just need to be in the legendary ballpark without the multiplier. The special effect is what makes the item *unique*, not the stat number.

### GUI Color

Add `"unique"` to the existing `RARITY_COLORS` dict and use the existing `RARITY_MYTHIC` color:

```python
# gui/theme.py — already defined:
RARITY_MYTHIC = "#ff6b6b"  # bright red

# Add to RARITY_COLORS:
"unique": RARITY_MYTHIC,  # red for unique items
```

The `ItemCard` widget in `gui/widgets/item_card.py` already reads from `Theme.RARITY_COLORS`, so unique items will automatically display in red. The only change needed: when `rarity == "unique"`, the label should show `[UNIQUE]` instead of `[LEGENDARY]`.

---

## 5. Consumable Overhaul

### Current State (Problem)

```
Healing Potion (common):  55 HP
Healing Potion (legendary): 55 × 3.5 = 192 HP
Superior Healing Potion (legendary): 180 × 3.5 = 630 HP
```

Meanwhile Cleric's Heal skill heals ~40-50 HP on a 3-turn cooldown. Potions:
- Have no cooldown (just inventory limit)
- Scale with rarity (nonsensical for a brewed item)
- Heal far more than dedicated healing skills
- Can be used by any class

### Proposed State

**A. Consumables have NO rarity.**

All consumables are built with `rarity="common"` (effectively: no multiplier). Their power is fixed.

| Consumable | Old (Common) | Old (Legendary) | New (Fixed) |
|---|---|---|---|
| Minor Healing Potion | 25 HP | 87 HP | 25 HP |
| Healing Potion | 55 HP | 192 HP | 55 HP |
| Greater Healing Potion | 110 HP | 385 HP | 110 HP |
| Superior Healing Potion | 180 HP | 630 HP | 180 HP |

**B. Potion Sickness — shared cooldown.**

After using ANY consumable in combat, the player gains **Potion Sickness** for 2 turns. While sick, no consumables can be used. This:
- Prevents potion-spam
- Makes healing skills the primary sustain
- Makes potions "oh crap" emergency buttons
- Creates tension: "Do I potion now or save it?"

```python
# In player_actions.py, after using a consumable:
player["potion_sickness"] = 2  # turns remaining

# At the start of the "use item" action:
if player.get("potion_sickness", 0) > 0:
    c_print("You're still queasy from the last potion! ({} turns)".format(
        player["potion_sickness"]))
    return "retry", False
```

**C. Consumable variety — elemental flavors.**

Instead of "Healing Potion" (common/rare/epic/legendary), introduce **themed consumables** with side effects:

| New Consumable | Heals | Side Effect | Element Theme |
|---|---|---|---|
| Healing Potion | 55 HP | *(none — baseline)* | Neutral |
| Ember Draught | 40 HP | +20% Fire resist, 2 turns | Fire |
| Frostward Tonic | 40 HP | Cleanses Burn & Poison | Water |
| Thunderbrew | 30 HP | Reduces all skill cooldowns by 1 | Thunder |
| Gale Cordial | 35 HP | +3 Initiative for 3 turns | Wind |
| Stoneblood Vial | 30 HP | +15% damage reduction, 2 turns | Earth |
| Blessed Water | 50 HP | Removes 1 curse or debuff | Light |
| Shadow Essence | 25 HP | Gain 1-turn dodge (avoid next attack) | Dark |
| Mana Philter | 0 HP | Restores 1 use of a random skill on cooldown | Magical |

**Each has a situational purpose.** Players choose which potion to carry based on their build and the dungeon region. This creates inventory strategy.

**D. Remove `power` scaling from consumable build path.**

In `build_item`, consumables currently do:
```python
item["power"] = int(base.get("base_power", 0) * r["stat_mult"])
```

Change to:
```python
# Consumables always use base_power directly, no rarity scaling
if base["type"] == "consumable":
    item["power"] = base.get("base_power", 0)
```

### Migration: Potion Item IDs

Existing potion IDs stay, but add the new elemental potions:

```python
# Keep (but they no longer scale with rarity):
"minor_healing_potion": {"name": "Minor Healing Potion", "type": "consumable", "base_power": 25},
"healing_potion":       {"name": "Healing Potion",       "type": "consumable", "base_power": 55},
"greater_healing_potion":{"name": "Greater Healing Potion","type": "consumable","base_power": 110},
"superior_healing_potion":{"name": "Superior Healing Potion","type": "consumable","base_power": 180},

# New elemental potions:
"ember_draught":    {"name": "Ember Draught",    "type": "consumable", "base_power": 40, "buff_fire_resist": 0.20, "buff_duration": 2},
"frostward_tonic":  {"name": "Frostward Tonic",  "type": "consumable", "base_power": 40, "cleanse_burn_poison": True},
"thunderbrew":      {"name": "Thunderbrew",      "type": "consumable", "base_power": 30, "cooldown_reduce": 1},
"gale_cordial":     {"name": "Gale Cordial",     "type": "consumable", "base_power": 35, "init_bonus": 3, "buff_duration": 3},
"stoneblood_vial":  {"name": "Stoneblood Vial",  "type": "consumable", "base_power": 30, "defense_buff": 0.15, "buff_duration": 2},
"blessed_water":    {"name": "Blessed Water",    "type": "consumable", "base_power": 50, "cleanse_curse_debuff": True},
"shadow_essence":   {"name": "Shadow Essence",   "type": "consumable", "base_power": 25, "dodge_next": True},
"mana_philter":     {"name": "Mana Philter",     "type": "consumable", "base_power": 0,  "restore_random_skill": True},
```

### Healing Skill Rebalance

With potions nerfed to fixed values and gated by Potion Sickness, healing skills need a slight buff to become the primary sustain:

| Skill | Old Base Power | New Base Power | Rationale |
|---|---|---|---|
| `clr_heal` | 20 | 28 | Should heal ~60-70 HP at mid WIS — competitive with a Healing Potion (55) but on cooldown |
| `clr_mass_heal` | 15 | 22 | Party-wide healing should feel impactful |
| `war_second_wind` | 25% max HP | 30% max HP | Self-sustain on a cooldown should beat a potion |

These numbers can be tuned after playtesting.

---

## 6. Dungeon Drop Chance Rework

### Current State

`roll_drop` in `dungeon.py:319` picks a random item ID and a random rarity from a weighted table. Consumables and equipment are in the same pool, both affected by rarity.

### Proposed State

Split the drop logic into two paths:

**Path 1: Equipment drops (uses rarity)**
- Same weighted rarity table (but with the new, narrower multipliers)
- Only equipment items are in this pool

**Path 2: Consumable drops (no rarity)**
- Separate pool of consumable item IDs
- No rarity roll — consumables are always built with `rarity="common"`
- Weighted by consumable tier (minor/common/greater/superior) based on floor

### New `roll_drop` Logic

```python
# dungeon.py

# ── Equipment drop pool (exclude uniques + consumables + scrolls) ──
_EQUIP_POOL = frozenset(
    k for k, v in ITEMS.items()
    if v.get("type") == "equipment"
    and not v.get("unique")
    and not v.get("wonderland_only")
)

# ── Consumable drop pool (weighted by tier) ──
_CONSUMABLE_TIERS = {
    1: ["minor_healing_potion", "antidote", "healing_salve"],
    2: ["healing_potion", "elixir_of_strength", "elixir_of_speed",
        "elixir_of_vitality", "elixir_of_mind", "battle_drink",
        "iron_skin_potion", "curse_cleansing_scroll", "fire_bomb",
        "ice_bomb", "smoke_bomb", "throwing_knife", "flash_powder",
        "poison_flask", "stun_bomb"],
    3: ["greater_healing_potion", "holy_water", "thunder_bomb",
        "acid_flask", "armor_shatter_flask"],
    4: ["superior_healing_potion", "recalled_scroll",
        "ember_draught", "frostward_tonic", "thunderbrew",
        "gale_cordial", "stoneblood_vial", "blessed_water",
        "shadow_essence", "mana_philter"],
}


def roll_drop(enemy_level, pandemonium=False):
    """Roll for an item drop. Returns (item_id, rarity) or None."""
    if pandemonium:
        if random.random() > 0.70:
            return None
    else:
        if random.random() > 0.50:
            return None

    # 60% equipment, 40% consumable (was 100% equipment-or-consumable mixed)
    if random.random() < 0.60:
        return _roll_equipment_drop(enemy_level, pandemonium)
    else:
        return _roll_consumable_drop(enemy_level, pandemonium)


def _roll_equipment_drop(enemy_level, pandemonium):
    """Roll for equipment with rarity."""
    rarities = ["common", "uncommon", "rare", "epic", "legendary"]

    # New, narrower weights (tuned for 1.0×–1.9× scale)
    if pandemonium:
        if enemy_level <= 5:
            weights = [0.18, 0.28, 0.28, 0.16, 0.10]
        elif enemy_level <= 10:
            weights = [0.10, 0.18, 0.30, 0.26, 0.16]
        elif enemy_level <= 20:
            weights = [0.05, 0.14, 0.26, 0.32, 0.23]
        elif enemy_level <= 30:
            weights = [0.03, 0.10, 0.20, 0.35, 0.32]
        else:
            weights = [0.02, 0.06, 0.16, 0.36, 0.40]
    else:
        if enemy_level <= 5:
            weights = [0.48, 0.32, 0.15, 0.05, 0.00]
        elif enemy_level <= 10:
            weights = [0.34, 0.34, 0.20, 0.10, 0.02]
        elif enemy_level <= 20:
            weights = [0.22, 0.30, 0.28, 0.15, 0.05]
        elif enemy_level <= 30:
            weights = [0.12, 0.24, 0.30, 0.22, 0.12]
        else:
            weights = [0.06, 0.18, 0.28, 0.28, 0.20]

    rarity = random.choices(rarities, weights=weights)[0]
    valid_ids = [k for k in _EQUIP_POOL]
    item_id = random.choice(valid_ids) if valid_ids else "short_sword"
    return (item_id, rarity)


def _roll_consumable_drop(enemy_level, pandemonium):
    """Roll for a consumable. No rarity — consumables are always 'common'."""
    # Determine which tier of consumables can drop
    if enemy_level <= 5:
        tier_pool = [1, 1, 1, 2]  # mostly tier 1, occasional tier 2
    elif enemy_level <= 10:
        tier_pool = [1, 2, 2, 2]
    elif enemy_level <= 20:
        tier_pool = [2, 2, 3, 3]
    elif enemy_level <= 30:
        tier_pool = [2, 3, 3, 4]
    else:
        tier_pool = [3, 3, 4, 4]

    tier = random.choice(tier_pool)
    pool = _CONSUMABLE_TIERS.get(tier, _CONSUMABLE_TIERS[1])
    item_id = random.choice(pool)
    return (item_id, "common")  # consumables always common
```

### Merchant & Travel Event Rarity

Same split applies to `_merchant_stock_rarity` and `_discovery_rarity` in `travel_events.py` and `dungeon_rooms.py`:
- Equipment: roll rarity from the new table
- Consumables: always common, just pick which tier

---

## 7. Facilities That Need Updating

| Facility | What Changes |
|---|---|
| **Blacksmith** (`facilities/blacksmith.py`) | Enhancement cost uses new `ITEM_RARITY` price_mult. Unique items cannot be enhanced past +5. `_rarity_style` needs "unique" → red. |
| **Arcane Tower** (`facilities/arcane_tower.py`) | `RARITY_ORDER` adds "unique" at the top. Scroll sacrifice: uniques cannot be sacrificed. Fusion scrolls cannot target unique items. |
| **Shop** (`facilities/shop.py`) | Price calculation uses new price_mult. Stock generation uses new rarity weights. Consumables sold without rarity. |
| **Herbalist** (`facilities/herbalist.py`) | Potions are always common. Add new elemental potions to stock rotation. |
| **Temple** (`facilities/temple.py`) | Consumable rewards use new potion tables. No rarity on potions. |
| **Black Market** (`facilities/black_market.py`) | Unique items priced as fixed high-cost items, not via rarity formula. |
| **Gift Shop** (`facilities/gift_shop.py`) | Wedding accessories become Unique tier (red). Hand-tune their stats. |
| **Travel Events** (`facilities/travel_events.py`) | `_discovery_rarity` uses new weights. Consumable discoveries skip rarity roll. Merchant stock splits equip/consumable. |
| **Dungeon Rooms** (`dungeon_rooms.py`) | `_merchant_stock_rarity` uses new weights. Treasure room drops use new `roll_drop`. |
| **GUI ItemCard** (`gui/widgets/item_card.py`) | Display `[UNIQUE]` in red for unique items. Elemental trait shown on card. |
| **GUI CombatScreen** (`gui/screens/combat_screen.py`) | Potion Sickness indicator in status area. Elemental trait proc messages. |
| **Inventory** (`inventory.py`) | `RARITY_ORDER` adds "unique": 5. Sorting still works. `apply_scroll_to_item` rejects unique targets. |

---

## 8. Migration Checklist

### Phase 1 — Core Data Changes (no gameplay impact yet)
- [ ] Update `ITEM_RARITY` in `resources/items.py` with new multipliers
- [ ] Add `RARITY_ORDER["unique"] = 5` in `inventory.py`
- [ ] Add `"unique": RARITY_MYTHIC` to `RARITY_COLORS` in `gui/theme.py`
- [ ] Create `combat/elemental_traits.py` module (no integration yet)

### Phase 1.5 — Equipment Naming Overhaul
- [ ] Define the 9×3 prefix table (element × tier) and weapon type mapping
- [ ] Rename all ~63 generic equipment IDs and `"name"` fields in `ITEMS` dict
- [ ] Add explicit `"primary_element"` field to every equipment definition
- [ ] Reassign elemental profiles intentionally (not arbitrary as currently)
- [ ] Update `_HEROINE_EQUIPMENT_BUILDS` in `combat/ally.py` (3 heroines × 4 slots)
- [ ] Update all `build_item("old_id", ...)` call sites (~15 calls in combat/ + facilities/)
- [ ] Update verb-selection logic in `player_actions.py` (check for new ID patterns)
- [ ] Verify `_random_item_id()` pools auto-populate from renamed ITEMS dict
- [ ] Plan save-file migration path for items stored with old IDs

### Phase 2 — Unique Items Migration
- [ ] Change all `"drop_rarity": "legendary"` to `"drop_rarity": "unique"` on unique items
- [ ] Add `_build_unique_item()` to `resources/items.py`
- [ ] Update `build_item()` to detect unique items and branch
- [ ] Re-tune `base_mods` on all unique items (compensate for losing 3.5× multiplier)
- [ ] Update `ItemCard` to show `[UNIQUE]` in red
- [ ] Block unique items from enhancement past +5
- [ ] Block unique items from scroll fusion

### Phase 3 — Consumable Overhaul
- [ ] Remove `rarity` scaling from consumable path in `build_item()`
- [ ] Add `potion_sickness` field to `ensure_player_fields()` in `character.py`
- [ ] Implement Potion Sickness check in `player_actions.py` "use item" path
- [ ] Tick potion sickness in `end_of_combat_cleanup()` and each turn
- [ ] Add new elemental consumable definitions to `ITEMS` dict
- [ ] Buff healing skill base_power values in `skill_list.yaml`
- [ ] Update herbalist stock to include new potions

### Phase 4 — Elemental Trait Integration
- [ ] Wire `get_trait_for_weapon()` into `player_actions.py` attack resolution
- [ ] Implement `apply_trait()` for all 9 elements
- [ ] Add trait info to ItemCard display
- [ ] Test each trait proc in combat

### Phase 5 — Drop Table Rework
- [ ] Rewrite `roll_drop()` in `dungeon.py` (split equip/consumable)
- [ ] Rewrite `_merchant_stock_rarity()` in `dungeon_rooms.py`
- [ ] Rewrite `_discovery_rarity()` and `_merchant_stock_rarity()` in `travel_events.py`
- [ ] Update `_combat_drop_rarity()` in `travel_events.py`
- [ ] Define `_CONSUMABLE_TIERS` table

### Phase 6 — Facility Updates
- [ ] Blacksmith: new price_mult, unique cap at +5, red style
- [ ] Arcane Tower: unique exclusion, new scroll crafting costs
- [ ] Shop: new rarity weights, consumable handling
- [ ] Herbalist: new potion stock
- [ ] Temple: new consumable rewards
- [ ] Black Market: unique item pricing

### Phase 7 — Balance Pass & Playtest
- [ ] Verify Common Greatsword (5 STR) > Legendary Short Sword (2 × 1.9 ≈ 3.8 STR)
- [ ] Verify Cleric Heal (~60 HP) > Healing Potion (55 HP) but on cooldown
- [ ] Verify Potion Sickness feels fair (2 turns)
- [ ] Verify elemental traits feel distinct
- [ ] Verify Pandemonium mode drop rates aren't too generous
- [ ] Verify unique items feel worth farming bosses for
- [ ] Run existing test suite; update expected values

---

## Summary Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    ITEM SYSTEM (NEW)                      │
├─────────────────┬───────────────────┬───────────────────┤
│   EQUIPMENT      │   CONSUMABLES     │   UNIQUE ITEMS     │
│   (has rarity)   │   (no rarity)     │   (red tier)       │
├─────────────────┼───────────────────┼───────────────────┤
│ Rarity scales:   │ Fixed power       │ Hand-tuned stats   │
│  • stat_mult     │ Potion Sickness   │ Boss-drop only     │
│  • price_mult    │   cooldown (2t)   │ Cannot enhance     │
│  • trait bonus   │ Elemental flavors │   past +5          │
│                  │   w/ side effects │ Cannot fuse        │
│ Primary element  │                   │   scrolls onto     │
│  → combat trait  │ Situational value │                    │
│    9 elements    │   (choose which   │ Red display color  │
│    9 traits      │    potion to      │ Special effects    │
│                  │    carry)         │   are the draw     │
├─────────────────┼───────────────────┼───────────────────┤
│ Drop: rarity     │ Drop: tier-based  │ Drop: boss-only    │
│ table by floor   │ by floor          │ guaranteed         │
└─────────────────┴───────────────────┴───────────────────┘

RARITY SCALE (narrowed):
  Common 1.00× ── Uncommon 1.15× ── Rare 1.35× ── Epic 1.60× ── Legendary 1.90×
                                                                    │
                                                        UNIQUE (red) — separate track
```
