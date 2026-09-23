# Palette, the Chromatic Artisan — Superboss Blueprint

> *"Let me paint you a masterpiece... in your own blood."*
>
> — Palette, the Chromatic Artisan

---

## Table of Contents

1. [Overview](#overview)
2. [Lore & Encounter](#lore--encounter)
3. [Enemy Definition](#enemy-definition)
4. [Core Mechanic: Color Stances](#core-mechanic-color-stances)
5. [Paint Stack System](#paint-stack-system)
6. [Phase Breakdown](#phase-breakdown)
7. [Attack Reference](#attack-reference)
8. [Color Shift & Telegraphing](#color-shift--telegraphing)
9. [AI Behavior](#ai-behavior)
10. [Player Counterplay](#player-counterplay)
11. [Unique Drops](#unique-drops)
12. [Recruitment & Ally Form](#recruitment--ally-form)
13. [Engine Additions Required](#engine-additions-required)
14. [Edge Cases](#edge-cases)
15. [Tuning Levers](#tuning-levers)
16. [Implementation Checklist](#implementation-checklist)

---

## Overview

| Property | Value |
|---|---|
| **Name** | Palette, the Chromatic Artisan |
| **Module** | `combat/palette_chromatic_artisan.py` |
| **Function** | `combat_palette(player, floor=None, enemies=None)` |
| **Enemy Key** | `chromatic_artisan` |
| **Level** | 35 |
| **Base HP** | 600 |
| **Phases** | 3 (100%→65% / 65%→30% / 30%→0%) with HP gates |
| **Availability** | Normal superboss pool (global rotation in `dungeon.py`, alongside the other superbosses) |
| **Core Gimmick** | Cycles through 7 elemental color stances. Current color determines attacks, debuffs, resistances, and passives. Attacks stack **Paint** on the player that bursts into color-matched debuffs. |
| **Drops** | `palette_brush` (unique weapon, 100%), `blank_canvas_shawl` (unique armor, 100%) |
| **Theme** | A painter whose canvas is reality; the fight teaches the mechanics that the brush drop later grants the player |

---

## Lore & Encounter

### Setting

A forgotten atelier suspended between worlds, where the walls are unfinished sketches and the floor is raw gesso. Palette was the artisan who painted the boundaries between elements — and went mad watching their colors run together.

The fight takes place **on** a living canvas. Every effect, debuff, and phase transition is framed as a painting term.

### Encounter Text

```
The walls here are not walls. They are canvas — stretched over nothing,
stapled to the air itself. Half-finished landscapes bleed into each other:
a burning forest drowning in a frozen sea, a lightning-struck desert.

At the easel stands a figure in a coat of seven stains. Their brush drips
with a color you cannot name, because it is every color at once.

They turn. Their eyes are blank, wet canvases.

"Be still," they say, "or do not. A smear is still a mark."
```

---

## Enemy Definition

### `superbosses.yaml` entry

```yaml
  chromatic_artisan:
    name: Palette, the Chromatic Artisan
    race: Human
    level: 35
    base_hp: 600
    mods:
      Strength: 7
      Constitution: 8
      Dexterity: 9
      Wisdom: 10
      Learning: 12
      Charisma: 10
    boss: true
    super_boss: true
    elemental_res:
      physical: 0.8
      magical: 0.8
    elemental_dmg:
      magical: 1.3
```

> The stance system rebuilds elemental resistances/damage at runtime, but the **physical/magical resistances persist across all stances**. Pure physical or magical builds eat a constant 0.8× — playable, but a well-built elemental team that chases the 1.4× stance weakness is clearly rewarded.

---

## Core Mechanic: Color Stances

Palette is always in one of **7 color stances**, cycling through them. The current color determines everything: attacks, on-hit debuffs, resistances, and a passive.

### Stance Data

| Color | Element | On-Hit Debuff | Boss Passive | Resist (0.6) | Weak (1.4) |
|:---:|------|---------------|--------------|--------------|------------|
| 🔴 Crimson | fire | Burn (tier 2+) | +15% damage dealt | fire | water |
| 🔵 Azure | water | Slow (2 turns) | Heal 3% max HP/turn | water | thunder |
| 🟡 Gold | thunder | Shock (3 dmg) | +10 initiative | thunder | earth |
| 🟢 Verdant | wind | Blind (2 turns) | +15% dodge | wind | earth |
| 🟤 Umber | earth | Weaken (−1 STR) | +20% defense | earth | wind |
| ⚪ Alabaster | light | Silence (2 turns) | Clears 1 self-debuff/turn | light | dark |
| ⚫ Obsidian | dark | Dread (2 turns) | 8% lifesteal | dark | light |

On-hit debuffs use the existing `elemental_debuffs.py` mappings so durations/strengths stay consistent with the rest of the game.

### Stance Application (runtime)

```python
def _apply_stance(boss, color):
    data = COLOR_DATA[color]
    boss["elemental_res"] = {
        "physical":      0.8,  # base res — persists across all stances
        "magical":       0.8,
        data["resist"]:  0.6,  # 40% resistance to own element
        data["weak"]:    1.4,  # 40% weakness to counter element
    }
    boss["elemental_dmg"] = {
        data["element"]: 1.5,  # 50% bonus damage with own element
    }
```

The stance **always exposes exactly one weakness and one strength** — the fight's core read. Physical and magical stay at 0.8× in every stance: a pure phys/magic team is playable, but a well-built elemental team is rewarded.

---

## Paint Stack System

Palette's attacks accumulate **Paint** stacks on the player. Stacks are colorless — they inherit the *current boss color* when they burst.

| Paint Stacks | Effect |
|-------------|--------|
| 1–2 | Cosmetic only ("Paint drips in your eyes") |
| 3–4 | Minor nuisance: −5% hit chance |
| 5 | **Pigment Burst**: all stacks → color-matched debuff at full strength, stacks reset |
| 6–7 | **Pigment Explosion**: all stacks → color-matched debuff at **+50% duration/strength**, stacks reset |

- Phase 1 cap: **5 stacks**. Phase 2+: **7 stacks**.
- Paint is cleansed by: the Light trait (Purge), consumable solvents, or the boss's own *Blank Canvas*.
- Paint is **visible in the HUD** with the current color's emoji.

---

## Phase Breakdown

### Phase 1 — "Underpainting" (100% → 65% HP)

- One action per turn
- Color cycle order: Crimson → Azure → Gold → Verdant → Umber → Alabaster → Obsidian
- Shifts color every **3 turns**
- Simple single-target **Brushstroke**; +1 Paint per hit

### Phase 2 — "Layering" (65% → 30% HP)

**Transition — "Blank Canvas":**
- Wipes ALL Paint stacks and ALL player debuffs (and the boss's own debuffs — a true blank canvas)
- Boss heals 5% max HP
- Announcement: *"Palette sweeps the canvas clean. Begin again."*

Then:
- Color cycle speeds up: shift every **2 turns**
- **Two actions per turn** (two brushstrokes at different targets)
- New attacks: **Impasto**, **Glaze**, **Drybrush**
- Paint cap raised to 7

### Phase 3 — "Masterpiece" (30% → 0% HP)

**Transition — "Final Canvas":**
- Boss enters **Dual Palette** mode: holds a primary **and** secondary color
- Both colors' passives and debuffs are active; both resistances and both weaknesses apply
- **Two actions per turn**
- New attacks: **Chiaroscuro**, **Spectrum**, **Fixative**

**At 10% HP — "Signature":**
- 2-turn charge attack; paints the player's name into the canvas of death
- Interrupted when the **party deals 40+ total damage** during the charge (player + allies, every hit counts)
- If uninterrupted: instant KO (cannot be defended)

---

## Attack Reference

### Phase 1

| Attack | Target | Damage | Effect |
|--------|--------|--------|--------|
| Brushstroke | Single | 1.0× | +1 Paint, current color's element |
| Wash | All | 0.5× | No Paint; boss shifts color early next turn |
| Study the Subject | — | — | Skip attack; next attack grants +2 Paint |

### Phase 2 (adds)

| Attack | Target | Damage | Effect |
|--------|--------|--------|--------|
| Impasto | All | 0.8× | +2 Paint to all targets |
| Glaze | Single | 0.6× | Pre-applies **next** color's debuff at half duration |
| Drybrush | Single | 1.3× | Ignores 30% defense; +1 Paint |

### Phase 3 (adds)

| Attack | Target | Damage | Effect |
|--------|--------|--------|--------|
| Chiaroscuro | Single | 1.2× | Light + Dark; unblockable; +3 Paint |
| Spectrum | All | 4 × 0.4× | Four hits, one random element each; +1 Paint per hit that lands |
| Fixative | Self | — | Locks current Paint stacks (uncleansable) for 3 turns |
| Signature | Single | Instant KO | 2-turn charge; interrupted by 40+ total party damage during the charge |

---

## Color Shift & Telegraphing

- Shifts happen on the boss's turn when the per-color turn counter expires (or early via *Wash*)
- **One turn before** every shift, the boss telegraphs:
  > *"Palette eyes the Azure pigment..."*
- This is the player's window to swap weapons, Defend, or prepare cleanses

```python
def _shift_color(context, new_color=None):
    """Advance Palette's stance, rebuild resistances, announce the shift."""
    if new_color is None:
        context["color_idx"] = (context["color_idx"] + 1) % len(COLOR_CYCLE)
        new_color = COLOR_CYCLE[context["color_idx"]]
    old_color = context["current_color"]
    context["current_color"] = new_color
    context["turns_in_color"] = 0
    _apply_stance(context["_boss"], new_color)
    c_print(f"\n🎨  Palette dips their brush into {COLOR_NAMES[new_color]}!")
    c_print(f"    New stance: {COLOR_DATA[new_color]['element'].upper()}")
```

---

## AI Behavior

| Input | Decision |
|-------|----------|
| Player HP < 25% | Prefer Brushstroke (single) or Chiaroscuro (P3) for the kill |
| Player has 4+ Paint | Prefer the burst attack for the current color |
| Player has elemental weakness vs current color | Prefer AoE (Wash / Impasto) |
| Boss HP < 15% (P3) | Begin Signature charge |
| Color turn counter expiring | Shift color (free, replaces one action) |
| Multiple allies alive | Prefer AoE attacks |

All decisions are weighted random choices — never hard scripted, so the fight stays unpredictable.

---

## Player Counterplay

| If Palette is... | Exploit with... | Beware of... |
|------------------|-----------------|--------------|
| 🔴 Crimson (fire) | Water weapons | Burn stacking |
| 🔵 Azure (water) | Thunder weapons | Slow + healing |
| 🟡 Gold (thunder) | Earth weapons | Shock + high initiative |
| 🟢 Verdant (wind) | Earth weapons | Blind misses |
| 🟤 Umber (earth) | Wind weapons | Weaken + high defense |
| ⚪ Alabaster (light) | Dark weapons | Silence locking skills |
| ⚫ Obsidian (dark) | Light weapons | Dread + lifesteal |

- **Weapon swapping** between color shifts is the intended skill expression
- **Ally elemental coverage** matters — bring varied damage types
- **Paint management**: burst at 5 stacks, or gamble to cleanse before the cap
- **Glaze telegraphs the next color's debuff** — prepare defensively
- **Dual Palette (P3)** means two weaknesses are open but two strengths are active; commit to one element

---

## Unique Drops

### 1. Palette's Brush (Weapon) — 100% drop

> *A masterwork sable brush, still wet with elemental pigment. The bristles shimmer through seven colors, never settling on one. It does not accept other tools — only itself, and the canvas before it.*

The brush is the game's **second "no-skills" weapon** — the first being the Black Silence Gloves. Equipping it replaces ALL class skills with the brush's own kit. In exchange it grants stance flexibility, a snowballing passive system, and stroke-unlocked finishers.

**Item entry** (`resources/items.py`):

```yaml
    "palette_brush": {
        "name": "Palette's Brush",
        "type": "equipment",
        "slot": "weapon",
        "unique": True,
        "base_mods": {"Wisdom": 10, "Learning": 10, "Charisma": 8},
        "scaling_stat": ["Wisdom", "Learning", "Charisma"],
        "elemental_dmg": {"magical": 1.3},
        "special": "painters_touch",
        "drop_source": "chromatic_artisan",
        "drop_rarity": "unique",
    },
```

#### Mechanic 1 — Skill Lock (Black Gloves pattern)

- All class skills are replaced by the brush's **Exhibit** menu (see below)
- Scales on Wisdom/Learning/Charisma — turns casters into magical auto-attackers
- Power curve is deliberately **back-loaded**: weak start, monster by fight's end

#### Mechanic 2 — Brush Stance (once per turn)

- **Free action, once per turn, chosen BEFORE attacking** — commit to a color, then act
- Attacks deal that color's element at **1.35×** (above generic magical, below dedicated elemental weapons' 1.3–1.5×, since you pay flexibility tax)
- No mid-turn flipping — the color commitment is the decision
- No stance chosen: attacks default to magical 1.3×

#### Mechanic 3 — Strokes (pigment acquisition — no kills involved)

- Each brush basic attack adds **+1 stroke** to the target (stored on the enemy dict; shown in HUD as `🎨 2/3`)
- On the **3rd stroke** on the same enemy: painting complete → **Pigment Explosion** + gain a pigment of the **finishing stroke's color**
- Strokes reset to 0; the same enemy can be painted again (a boss is a paint factory)
- Ally hits and DoT ticks **never** interact with strokes — no kill-stealing, no credit theft
- Enemy dies before 3 strokes: nothing gained, nothing lost
- Switching targets abandons the unfinished canvas (1–2 strokes of progress)

**Pigment Explosion:** the 3rd stroke deals **+50% damage** — painting always pays out immediately, even if the fight ends right after.

#### Mechanic 4 — Wet Palette (permanent battle auras)

Pigments are **never consumed**. Each stored pigment grants a permanent passive for the rest of the battle:

| Color | Aura | Rank 1 | Rank 2 | Rank 3 |
|:---:|------|-----|-----|-----|
| 🔴 Crimson | On-attack Burn | 25% tier 2 | 40% tier 3 | 55% tier 4 |
| 🔵 Azure | On-attack Slow | 25% 2 turns | 40% 3 turns | 55% 3 turns |
| 🟡 Gold | On-attack Shock | 20% 3 dmg | 35% 4 dmg | 50% 6 dmg |
| 🟢 Verdant | Initiative | +3 | +5 | +8 |
| 🟤 Umber | Damage reduction | +8% | +12% | +16% |
| ⚪ Alabaster | On-attack Silence | 20% 2 turns | 35% 3 turns | 50% 3 turns |
| ⚫ Obsidian | Lifesteal | 8% | 12% | 16% |

- **3 palette slots.** All auras stack simultaneously
- Same color again → **upgrade rank** (max 3). New color when full → replaces the oldest (FIFO)
- The finishing stroke's color = the pigment's color → the wielder chooses what they collect
- Auras reset at combat end (battle-scoped, not run-scoped)

#### Mechanic 5 — Exhibits (skill replacements)

Every **6 total strokes** unlock a one-use Exhibit (mirrors Black Gloves' workshops → Furioso structure):

| Exhibit | Unlock | Effect |
|---------|--------|--------|
| **Impasto** | 6 strokes | AoE in stance color; applies stance's aura debuff to ALL enemies (no roll) |
| **Chiaroscuro** | 12 strokes | Single target 2.2×; ignores defense; +1 stroke |
| **Signature** | 18 strokes | 3.0× single target + instant full rank-up of one chosen aura |

#### Brush state keys (on player dict)

```python
"brush_stance":         str    # current color element or None (default magical)
"brush_stance_changed": bool   # consumed once per turn
"brush_strokes":        {enemy_id: int}   # per-enemy stroke counters
"brush_palette":        [{"color": str, "rank": int}, ...]  # max 3
"brush_total_strokes":  int    # lifetime counter for Exhibit unlocks
"brush_exhibits_used":  set    # {"impasto", "chiaroscuro", "signature"}
```

#### Brush flow example

```
Turn 1:  Stance 🔴 → attack Goblin (1/3)
Turn 2:  Stance locked (changed last turn) → attack Goblin (2/3)
Turn 3:  Switch → ⚫ → attack Goblin (3/3) 💥 Pigment Explosion +50%
         ✨ Painting complete! 🖤 Obsidian → Lifesteal 8% aura (battle-long)
Stroke 6:  🎨 Exhibit: Impasto unlocked in the action menu
```

#### Companion pairing note

No ally can equip the brush — player-unique weapons are blocked at equip time, with one exception: a recruited Palette can wear her own originals for boosted effects (see Recruitment & Ally Form). The real question is who to **bring**:

- **Wisdom-scaling healer allies are the strongest pick.** Equipping the brush replaces ALL your class skills (no self-heal, no cleanse, no buffs), so a light-heal support ally covers the brush's only true gap. Undead girls get +2 Wisdom from *Unholy Resilience* and can still be healed by others.
- **Fight length is the brush's real scaling stat** — rank-3 auras and Exhibits only come online late. Fey allies (10% max HP regen/turn from *Nature's Blessing*) and Elemental allies (+20% all-element resist from *Elemental Resilience*) stall fights exactly the way the brush wants.
- **Cover the color you're not in.** The brush commits to one color per turn, so an ally with learnable elemental attacks (Fireball/Inferno for fire, Ice Shards for water, Whirlwind for wind, Shadow Dance for dark) can always poke the stance weakness while you hold your color.

---

### 2. Blank Canvas Shawl (Armor) — 100% drop

> *A length of pristine white linen that seems to reject any stain. Once per battle it can wipe away everything — wounds, curses, even the memory of pain.*

Mirrors the boss's own phase-2 "Blank Canvas" transition. A panic button that rewards timing.

**Item entry**:

```yaml
    "blank_canvas_shawl": {
        "name": "Blank Canvas Shawl",
        "type": "equipment",
        "slot": "armor",
        "unique": True,
        "base_mods": {"Constitution": 8, "Wisdom": 6},
        "elemental_res": {"magical": 1.15, "light": 1.1, "dark": 1.1},
        "special": "blank_canvas",
        "drop_source": "chromatic_artisan",
        "drop_rarity": "unique",
    },
```

**Special `blank_canvas`:**

| Property | Value |
|----------|-------|
| Activation | Free action, once per combat |
| Cleanse | Removes ALL debuffs from self (including Paint stacks, burn, bleed, slow, curse) |
| Heal | Restores 15% of max HP |
| Afterimage | For 2 turns: immune to the next 2 debuff applications |
| Cost | Also clears ALL of your buffs — a true blank canvas |

---

## Recruitment & Ally Form

Palette joins as a **permanent house girl + ally** via a unique method — no Capture Net. This mirrors the Wonderland heroine system (`_heroine` flag, quest-style recruitment) rather than `store_captured_girl`.

### Recruitment — "The Artist's Choice"

- **Not capturable**: `monster_girl: true` on her template, but excluded from `is_capturable()` via the heroine flag. Nets bounce off.
- **Condition** (tracked during the fight; post-victory scene in `combat_palette()` offers her a place in the party if EITHER was met):
  1. **"You let it dry."** — the player survived a full Paint burst: a 5-stack Pigment Burst or 6–7-stack Pigment Explosion that actually triggered on them (no shawl, solvent, or cleanse on that stack). She respects someone who lets the paint dry on their skin.
  2. **"You held the canvas."** — the player survived a completed Signature charge via a death-prevention/revive effect. Engine-dependent stretch goal; requires such an effect to exist.
- **No temp phase** — joins directly as a permanent ally (superboss investment), stored in the house like other girls.

### Personality

**Curious and timid** at first — she stammers, fidgets with her brush bristles, and flusters when you compliment the coat of seven stains. The menacing boss persona is just "working mode." Her **stylish streak** emerges at higher affection: immaculate color coordination, and she starts leaving tiny painted gifts on your windowsill.

### Ally Kit — "Degraded Masterpiece"

Default skills are weakened boss moves; she does **not** use the Paint stack system in ally form:

| Skill | Type | Boss version | Ally version |
|-------|------|--------------|--------------|
| Brushstroke | Basic, single | 1.0×, +1 Paint | 0.7×, current color's element |
| Spectrum | AoE, cooldown | 4 × 0.4×, +1 Paint per hit | 3 × 0.3×, one random element per hit |
| Signature (degraded) | Finisher, single | Instant KO, 2-turn charge | 2.5×, 1-turn telegraph, 4-turn cooldown; cannot be defended |

- Her colors cycle in boss order (Crimson → Azure → Gold → Verdant → Umber → Alabaster → Obsidian), one shift per turn; Brushstroke always uses the current color.
- Race: **Elemental** (`elemental_passive`: +2 Con, +20% all-element res) — the living-pigment read, not Construct.

### Original Equipment Buffs (Alice/Vorpal pattern)

Equip exceptions in `equip_ally_item()` for `_heroine_key == "palette"`, plus skill-swap functions (`swap_palette_to_original_skills` / `revert_palette_to_normal_skills`):

- **`palette_brush` on Palette**: her skills lock to the brush's own kit exactly like the player's (original kit replaced by stance, strokes, auras, and Exhibits). On top of that, her current color grants the boss passive at half strength — "she remembers being the boss":

  | Color | Ally passive (½ boss values) |
  |:---:|---|
  | 🔴 Crimson | +7% damage dealt |
  | 🔵 Azure | Heal 1.5% max HP/turn |
  | 🟡 Gold | +5 initiative |
  | 🟢 Verdant | +7% dodge |
  | 🟤 Umber | +10% defense |
  | ⚪ Alabaster | Clears 1 self-debuff/turn |
  | ⚫ Obsidian | 4% lifesteal |

- **`blank_canvas_shawl` on Palette**: her Blank Canvas becomes a once-per-combat **party-wide** cleanse + heal 10% max HP per member; she keeps her Afterimage window.

### Wedding Accessory — "Palette's Palette"

Soulbound Legendary at 200 affection (mirrors the `wedding_*` accessories). Effect TBD — candidates:

| Candidate | Effect |
|-----------|--------|
| **Masterclass** (recommended) | While Palette is in the party, brush Exhibits unlock at 5/10/15 strokes and Exhibit damage +15% |
| Living Pigment | Each turn, the player's attacks deal +10% damage of Palette's current color's element (auto color-matching) |
| Wet-on-Wet | Debuffs (including Paint) on the player expire 1 turn sooner (min 1 turn) |

*Masterclass* is the smallest engine surface and makes the brush+Palette duo the only build that fast-tracks Exhibits.

---

## Engine Additions Required

| Hook | Location |
|------|----------|
| Boss module + `superboss_combat_loop` hooks | `combat/palette_chromatic_artisan.py` (new) |
| Brush stroke counting + Pigment Explosion | Player attack path in `combat/player_actions.py` (`on_hit` exists) |
| Brush stance element resolution | `get_attack_element` in `combat/elemental.py` + brush module |
| Aura on-hit procs (burn/slow/shock/silence) | On-hit path, gated by aura ranks |
| Stat auras (initiative, DR) | `compute_player_stats` in `combat/stats.py` |
| Lifesteal aura | On-hit path (mirror existing Dark trait leech) |
| Skill lock + Exhibit menu | Skill resolution path; mirror `black_silence_gloves.py` |
| Shawl `blank_canvas` special | Once-per-combat free action; debuff application gate for Afterimage |
| Paint HUD counter | `combat_ui.py` |
| Strokes HUD on enemies | `combat_ui.py` enemy status line |
| Boss YAML | `resources/enemies/enemies_data/superbosses.yaml` |
| Item entries | `resources/items.py` |
| Dungeon registration | `dungeon.py` — import `combat_palette`; add tier 8 to the normal superboss pool (`superboss_pool` + tier dispatch) |
| Ally equip gate (player-unique weapons) | `combat/ally.py` — block player-unique weapons for allies at equip time; exception for Palette (`_heroine_key == "palette"`) |
| Palette ally kit + original-equip swaps | `combat/palette_brush.py` or `combat/ally_skills.py` — degraded skills; `swap_palette_to_original_skills` / `revert_palette_to_normal_skills` |
| Recruitment scene + condition tracking | `combat/palette_chromatic_artisan.py` — track full-burst survival; post-victory offer |
| Wedding accessory `palettes_palette` | `resources/items.py` |

---

## Edge Cases

| Case | Ruling |
|------|--------|
| Ally/DoT kills the painted enemy mid-strokes | Strokes lost, no penalty — progress is incidental, never stolen |
| Enemy dies to the 3rd stroke (Pigment Explosion overkill) | Pigment still granted + explosion damage still applies |
| Wielder switches weapons mid-combat | Palette state clears (like `clear_gloves_state`) |
| Player-unique weapons on allies | Blocked at equip time in `equip_ally_item()`; EXCEPTION: Palette may wear her own brush/shaul (Alice/Vorpal pattern) |
| Capture Net on Palette mid-fight | Not capturable — heroine flag; the recruitment condition is the only path |
| Drops vs recruited Palette | Drops still drop after victory; she joins without gear — hand her the originals to trigger the buffs |
| Palette (ally) wields `palette_brush` | The skill-lock **does** apply to her — her original kit (Brushstroke/Spectrum/Signature) is replaced by the brush's own kit (stance, strokes, auras, Exhibits), same as the player; the shawl's active skill is not affected by the lock |
| Palette (ally) wears `blank_canvas_shawl` | The once-per-combat cleanse is her own active and survives the brush's skill-lock (item actives are not class skills) — it triggers her party-wide Blank Canvas (cleanse + heal 10% max HP per member). If the player also wears a shawl, each is a separate once-per-combat charge — no duplicate stacking |
| Boss's *Fixative* vs shawl's cleanse | Fixative wins — locked Paint cannot be cleansed for its 3 turns |
| Signature charge vs player death prevention | Charge breaks when the party's total damage during the charge reaches 40+ — every hit from player and allies counts |
| Dual Palette with same color twice? | Not possible — secondary is always a different color |
| Stroke counter on captured/fled enemies | Cleared with the enemy dict (no cleanup needed) |
| Auras + elemental weakness debuff interactions | Aura debuffs apply through existing `status_effects` functions; no new stacks invented |

---

## Tuning Levers

| Lever | Default | Effect of raising |
|-------|---------|-------------------|
| `STROKES_PER_PIGMENT` | 3 | Slower ramp, weaker brush |
| `PIGMENT_EXPLOSION_PCT` | 0.50 | Stronger immediate painting payoff |
| `STANCE_MULT` | 1.35 | Brush attack power |
| `PALETTE_SLOTS` | 3 | Max simultaneous auras |
| `MAX_AURA_RANK` | 3 | Aura ceiling |
| `EXHIBIT_STROKES` | 6 / 12 / 18 | Finisher pacing |
| Boss `turns_per_color` | 3 (P1) / 2 (P2+) | Fight read difficulty |
| `PAINT_BURST_THRESHOLD` | 5 | Player pressure |
| `SIGNATURE_INTERRUPT_DMG` | 40 | Party-wide damage threshold; raise it if 3 allies trivialize the interrupt |
| Ally `ALLY_SIGNATURE_MULT` | 2.5 | Ally finisher burst |
| Ally `ALLY_SPECTRUM_HITS` | 3 | Ally AoE reach |
| `PALETTE_COLOR_CYCLE` | 7 | Ally elemental coverage |

---

## Implementation Checklist

- [ ] `combat/palette_chromatic_artisan.py` — boss combat function, stance cycle, phases, attacks, AI
- [ ] `superbosses.yaml` — `chromatic_artisan` entry
- [ ] `combat/palette_brush.py` — brush module: skill lock, stance, strokes, auras, exhibits
- [ ] `resources/items.py` — `palette_brush` + `blank_canvas_shawl` entries
- [ ] `dungeon.py` — import `combat_palette`, register as tier 8 in the normal superboss pool (not Wonderland)
- [ ] Ally equip gate — block player-unique weapons for allies in `equip_ally_item()`; Palette exception
- [ ] Recruitment scene + condition tracking (survived full Paint burst) in `combat_palette`
- [ ] Palette ally conversion — `_heroine_key="palette"`, Elemental race, degraded kit (Brushstroke/Spectrum/Signature), house dialogue + personality lines
- [ ] Equip buffs — `swap_palette_to_original_skills` / `revert_palette_to_normal_skills` (brush passives, party Blank Canvas)
- [ ] `palettes_palette` wedding accessory (soulbound Legendary, 200 affection; effect per chosen candidate)
- [ ] Combat engine hooks — on-hit strokes/explosion, aura procs, stat auras, lifesteal
- [ ] Skill lock + Exhibit menu integration (mirror Black Gloves)
- [ ] `blank_canvas` special + Afterimage debuff-application gate
- [ ] HUD — Paint counter (player), strokes + stance (enemy/boss)
- [ ] Loot drops on boss victory (100% both items)
- [ ] Balance pass vs Black Gloves build (front-loaded burst vs back-loaded snowball)
- [ ] Playtest: 5-enemy trash fight, elite fight, superboss fight with the brush equipped
