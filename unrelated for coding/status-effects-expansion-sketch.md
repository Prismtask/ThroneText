# Status Effects Expansion Sketch — Pandemonium

## 1. Current State Audit

### 1.1 Debuffs (18 tracked types)

| # | Type | Target | Mechanic | Source |
|---|------|--------|----------|--------|
| 1 | **Poison** | Any | Flat DoT/turn, refreshes | Skills, items, enemy attacks |
| 2 | **Bleed** | Any | DoT/turn, heavier overwrites | Skills, Jabberwock |
| 3 | **Burn** (Tier 1–5) | Any | Tiered DoT (3→30/turn); reduces enemy CON; repeated apps intensify | Fire skills, Ignite trait, superbosses |
| 4 | **Freeze** | Enemy | Skip attack, slow on thaw | Ice skills, items |
| 5 | **Slow** | Any | Reduced speed/initiative | Ice skills, items, boss mechanics |
| 6 | **Stun** | Enemy | Skip turn entirely | Skills, ally abilities |
| 7 | **Confusion** | Enemy | Random action (may hit self) | Skills, WL floor bosses |
| 8 | **Fear** | Enemy | % chance to skip turn | Skills, Wicked Witch, WL bosses |
| 9 | **Blind** | Any | 25% miss, −2 Dex for flee | Skills, items, boss mechanics |
| 10 | **Weaken** | Any | −STR penalty to damage rolls | Skills, Chrysalis, boss attacks |
| 11 | **Silence** | Player | Cannot use items | Enemy attacks |
| 12 | **Dread** | Player | 40% miss, +4 flee difficulty | Supernatural enemy attacks |
| 13 | **Curse** | Player | −stat penalty (permanent until cured) | Cursed items, enemy attacks |
| 14 | **Vulnerable** | Player | +% damage taken | Feral Rage (self-inflicted), boss mechanics |
| 15 | **Healing Down** | Player | −% healing received | Chrysalis Wrath mechanic |
| 16 | **Expose** | Enemy | −CON (permanent, stacks to 5) | Skills, items |
| 17 | **Sunder** | Enemy | −armor (flat value) | Skills, wedding specials |
| 18 | **Elemental Weakness** | Enemy | −resist to specific element | Ally skills |

### 1.2 Buffs (15 tracked types)

| # | Type | Target | Mechanic | Source |
|---|------|--------|----------|--------|
| 1 | **HoT** (Heal over Time) | Player/Ally | HP regen/turn | Skills, items, ally abilities |
| 2 | **Defense / Defense Pct** | Player/Ally | Flat DR or % DR | Skills, items, ally buffs |
| 3 | **Evasion** | Player/Ally | % dodge chance | Ally skills, superboss passives |
| 4 | **Power Buff / Damage Boost** | Player/Ally | +damage dealt | Skills, ally buffs |
| 5 | **Stat Buff / Strength Up** | Player/Ally | +specific stat | Ally skills, WL boss mechanics |
| 6 | **Initiative** | Player/Ally | +turn speed | Wind trait, skills, items |
| 7 | **Divine Shield** | Player | Full damage immunity (timed) | Paladin/Cleric skills |
| 8 | **Cooldown Reduction** | Player/Ally | Faster skill cooldowns | Ally buffs, skills |
| 9 | **Reflection** | Player/Ally | % damage reflected back | Ally skills, Wicked Witch |
| 10 | **Momentum** | Player/Ally | +3% damage/stack (permanent, cap 20) | Chrysalis, Chronoweave Mantle |
| 11 | **Fear Immunity** | Player/Ally | Immune to Fear | Wedding specials |
| 12 | **Fire Resist** | Player | −% fire damage | Ember Draught item |
| 13 | **Dodge** | Player | Evade next attack | Items (dodge_next) |
| 14 | **Blessing / Well Rested / Floor Buff** | Player | Permanent stat/effect bonus | Temple, Inn, dungeon floors |
| 15 | **Wedding Stats / Wedding Initiative** | Player/Ally | Wedding-exclusive combat buffs | Wedding mechanics |

### 1.3 Observation

The game already has **strong coverage of the basics**: DoTs (poison/bleed/burn), action denial (freeze/stun/fear/confusion), stat modulation (weaken/curse/sunder/expose), and defensive layers (defense/evasion/shield/reflection).

The **gaps** are in:
- **Tactical role effects** (taunt, guard, marking)
- **Risk/reward tradeoffs** (berserk, last stand, doom counter)
- **Positioning / terrain** (root/bind, hazard zones)
- **Healing inversion** (zombie/undead)
- **Absorption shields** (barrier that eats N damage)
- **Counter-attack** (thorns is reflection, but not a triggered counter-strike)
- **Escalating threat** (rage/fury — damage scales with missing HP)

---

## 2. Recommended Additions (Priority-Ordered)

### 🥇 Tier 1 — High Impact, Low Implementation Cost

#### 2.1 Barrier / Ward
> Absorbs the next N damage before HP is touched.

- **Type:** Buff (player/ally/enemy)
- **Mechanic:** `barrier_value` field absorbs incoming damage. Damage → barrier first, then HP. Expires when `barrier_value` hits 0 or duration runs out.
- **Why:** Fills a missing defensive niche between %DR (Defense) and full immunity (Divine Shield). Gives healers/shielders a proactive play.
- **Implementation:** Add `"type": "barrier"` to `active_buffs`. In damage resolution in `combat_engine.py`, check barrier before HP.
- **Sources:** New Cleric/Warden skills, rare accessories, certain ally abilities.
- **Display:** `Barrier(45)` on HUD.

```python
def apply_barrier(target, value, duration=3):
    """Grant a damage-absorption barrier."""
    existing = next((b for b in target.get("active_buffs", [])
                     if b.get("type") == "barrier"), None)
    if existing:
        existing["value"] = max(existing["value"], value)  # stronger overwrites
        existing["remaining"] = max(existing["remaining"], duration)
        return "reinforced"
    target.setdefault("active_buffs", []).append({
        "type": "barrier", "value": value, "remaining": duration
    })
    return "applied"
```

#### 2.2 Taunt / Provoke
> Forces enemies to target the taunter for N turns.

- **Type:** Buff (self) + Debuff (enemies)
- **Mechanic:** While `taunting`, all enemy single-target attacks must target the taunter. AoE attacks ignore taunt. Bosses may have partial resistance (% chance to ignore).
- **Why:** Creates a true "tank" role. Currently defense buffs exist but no aggro control. Deepens party composition choices.
- **Implementation:** `"type": "taunt"` buff on player/ally. In enemy AI target selection, check for taunt aura.
- **Sources:** Knight/Guardian class skills, shield-type weapons, certain ally abilities.
- **Display:** `Taunting(2)` on HUD.

#### 2.3 Berserk
> +damage but player attacks uncontrollably (random target).

- **Type:** Buff (self) + implicit debuff
- **Mechanic:** +30–50% damage dealt, +25% damage taken. Player action is auto-resolved to a random valid enemy target. Lasts 3 turns.
- **Why:** High-risk/high-reward play pattern. Fits Barbarian/Berserker class fantasy. Creates dramatic moments.
- **Implementation:** `"type": "berserk"` buff. In `player_actions.py`, check berserk flag → override target selection with random.
- **Display:** `Berserk(3)` with visual flair.

#### 2.4 Root / Bind
> Cannot flee; −50% evasion. Lasts 2–3 turns.

- **Type:** Debuff (player/enemy)
- **Mechanic:** Flight/flee disabled. Evasion halved. Does NOT prevent attacking or skill use (unlike freeze/stun).
- **Why:** Middle-ground CC. Currently there is nothing between "fully disabled" (freeze/stun) and "just slowed". Adds tactical texture — roots a runner, sets up combos.
- **Implementation:** `"type": "root"` debuff. Check in flee logic and evasion calc.
- **Display:** `Rooted(2)`.

---

### 🥈 Tier 2 — Medium Impact, Thematic Depth

#### 2.5 Doom / Death Sentence
> Countdown (3 turns) → target dies. Bosses immune or resist.

- **Type:** Debuff (enemy, rarely player)
- **Mechanic:** `doom_counter` ticks down each round. At 0, target takes lethal damage (or massive %HP damage if boss-resistant). Cure via specific items/spells.
- **Why:** Dramatic tension. Time-pressure win condition. Fits dark magic / necromancer themes.
- **Implementation:** `"type": "doom"` debuff with `"counter": 3`. In `tick_enemy_debuffs`, decrement; at 0, apply lethal.
- **Sources:** High-level dark magic skills, certain superboss attacks (player-side Doom).
- **Display:** `Doomed(3)` with skull icon.

#### 2.6 Rage / Fury (Scaling)
> Damage dealt increases as HP decreases.

- **Type:** Passive buff
- **Mechanic:** `damage_boost = (missing_hp_ratio) * rage_multiplier`. E.g., at 20% HP with 0.5 multiplier → +40% damage.
- **Why:** Comeback mechanic. Rewards risky low-HP play. Distinct from flat damage buffs.
- **Implementation:** `"type": "rage"` buff. In damage calc, multiply by `1 + (1 - hp_ratio) * rage_value`.
- **Sources:** Barbarian class passive, certain weapon traits.
- **Display:** `Rage(+32%)` — dynamic percentage.

#### 2.7 Zombie / Blight
> Healing damages instead. Cannot be healed by normal means.

- **Type:** Debuff (player/enemy)
- **Mechanic:** All incoming healing → damage. HoT buffs deal damage. Cure spells deal damage instead. Only removable by specific cleansing items.
- **Why:** Subverts healing meta. Creates terrifying enemy fights. Fits undead/dark themes.
- **Implementation:** `"type": "zombie"` debuff. In all healing paths, check for zombie → invert delta.
- **Display:** `Blighted` with green/black icon. Healing numbers shown in red.

#### 2.8 Haste
> +1 action per turn for N turns.

- **Type:** Buff (player/ally)
- **Mechanic:** Target gets a bonus minor action (can basic-attack only, or use a restricted skill pool). True double-turn is too strong — instead: bonus quick-attack at 60% damage.
- **Why:** Speed fantasy. Currently only initiative/slow exists. A true "extra action" feels powerful and distinct.
- **Implementation:** `"type": "haste"` buff. After normal turn, prompt for quick-attack if hasted.
- **Display:** `Hasted(2)`.

---

### 🥉 Tier 3 — Niche / Boss-Specific

#### 2.9 Last Stand
> Survive a lethal hit at 1 HP. One-time trigger, then buff expires.

- **Type:** Buff
- **Mechanic:** On lethal damage → set HP to 1, remove Last Stand buff, grant brief invulnerability (1 turn).
- **Why:** Epic survival moment. Fits Paladin/Knight class identity.
- **Implementation:** Check in damage resolution before death flag.
- **Display:** `Last Stand` icon.

#### 2.10 Phantasm / Mirror Image
> Creates 2 illusory copies. Next 2 single-target attacks miss (hit a copy instead).

- **Type:** Buff (charges-based)
- **Mechanic:** `phantasm_charges: 2`. Each incoming single-target attack consumes 1 charge and misses. AoE ignores phantasm. Expires after all charges consumed or duration ends.
- **Why:** Distinct from evasion (which is % chance). Guaranteed miss is tactically very different.
- **Display:** `Phantasm(2)` on HUD.

#### 2.11 Static Charge / Thorns Aura
> Deal flat retaliation damage when hit by a physical attack.

- **Type:** Buff
- **Mechanic:** `thorns: 8` → each received physical hit deals 8 damage back to attacker. Distinct from Reflection (which is % based).
- **Why:** Already have % reflection. Flat thorns gives a different scaling profile — better vs many small hits than one big hit.
- **Display:** `Thorns(8)`.

#### 2.12 Magnetize / Polarity
> Next elemental attack on this target is guaranteed to crit.

- **Type:** Debuff (enemy)
- **Mechanic:** Sets up a guaranteed crit window. Consumed on next elemental hit. Great synergy with multi-element parties.
- **Why:** Encourages coordinated party play. Rewards sequencing actions.
- **Display:** `Polarized`.

---

## 3. Design Principles

1. **Don't bloat the HUD.** Each new status must have a short tag (≤4 chars) or icon. The combat HUD is fixed 68 chars wide — status display space is limited.

2. **Every debuff needs a cleanse path.** Ensure cure items, skills, or facilities can remove each new effect. No "permanent with no counter" except Curse (which already has Blessed Water).

3. **Enemies should use these too.** A new buff/debuff is twice as interesting if enemies can inflict it on the player. Design for symmetry where possible.

4. **Tier before type.** Prefer deepening existing systems (e.g., more burn tiers, poison variants) over adding entirely new types unless the mechanic is genuinely distinct.

5. **Boss immunity table.** Maintain a clear list of which debuffs bosses resist. Currently boss immunity logic is scattered across individual boss files — centralize it.

6. **Ally compatibility.** Allies use the same `active_buffs`/`active_debuffs` structure. All new effects must work for ally dicts with zero extra work.

---

## 4. Implementation Roadmap

### Phase A — Quick Wins (1–2 sessions)
- [ ] **Barrier** — ~50 lines in `status_effects.py` + damage resolution check
- [ ] **Root** — ~30 lines, simple flag checks in flee + evasion
- [ ] **Taunt** — ~40 lines, enemy AI target override

### Phase B — Thematic Depth (2–3 sessions)
- [ ] **Berserk** — ~60 lines, needs random-target override in player action flow
- [ ] **Doom** — ~50 lines, tick logic + boss resistance table
- [ ] **Haste** — ~80 lines, bonus action prompt in combat loop

### Phase C — Advanced (3–4 sessions)
- [ ] **Zombie** — ~40 lines but touches ALL healing paths (invasive)
- [ ] **Last Stand** — ~30 lines in damage resolution
- [ ] **Phantasm** — ~50 lines in hit resolution
- [ ] **Rage** — ~30 lines in damage calc (purely formulaic)

### Follow-up
- [ ] Create or expand a central **boss-immunity table** (YAML or Python dict)
- [ ] Add corresponding **cure/cleanse items** to `resources/items.py`
- [ ] Add **skill entries** to `resources/skill_book/` YAML files
- [ ] Update **combat HUD** (`combat_ui.py`) to display new status tags
- [ ] Update **`get_player_status_tags()`** in `status_effects.py`
- [ ] Write **test cases** in `tests/`

---

## 5. What NOT to Add

| Idea | Reason to Skip |
|------|---------------|
| **Sleep** (can't act, wakes on hit) | Too similar to Stun + Freeze. Redundant. |
| **Petrify** (can't act, +DEF) | Overlaps with Freeze (skip turn) + Defense buff. Not distinct enough. |
| **Charm** (attack allies) | Already have Confusion (random action). Charm would need complex AI override for minimal gain. |
| **Gravity** (grounds flying enemies) | Flying enemies aren't a core mechanic yet. Premature. |
| **Time Stop** (skip all enemy turns) | Balance nightmare. Even at high cost, trivializes fights. |
| **Instant Death** (no counter) | Frustrating. Doom with countdown is the better design — gives counterplay window. |
| **Mana Burn** (drain MP) | Game has no MP system — skills use cooldowns. Would require adding a whole resource system. |
| **Polymorph** (transform target) | Too complex. Would need per-enemy alternate stat blocks. |

---

## 6. Quick Reference: Proposed Type Tags

| Effect | Tag | Color/Icon | Duration |
|--------|-----|-----------|----------|
| Barrier | `SHD` | 💠 Blue | 3 turns |
| Taunt | `TNT` | 🛡️ Gold | 2–3 turns |
| Berserk | `BSK` | 💢 Red | 3 turns |
| Root | `ROT` | 🌿 Green | 2–3 turns |
| Doom | `DOM` | 💀 Purple | 3 turns |
| Rage | `RGE` | 🔥 Orange | Permanent (aura) |
| Zombie | `BLT` | ☠️ Green | Until cured |
| Haste | `HST` | ⚡ Yellow | 2 turns |
| Last Stand | `LST` | ✨ White | Until triggered |
| Phantasm | `PHA` | 🌫️ Gray | Charges-based |
| Thorns | `THN` | 🌵 Green | 3 turns |
| Polarized | `POL` | 🧲 Cyan | 2 turns |

---

*Sketch compiled 2026-07-14. Review with the full team before implementation — some effects (Zombie, Haste) touch many code paths and need careful integration planning.*
