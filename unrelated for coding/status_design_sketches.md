# Status Effects — Design Sketches for New Additions

> Matches existing patterns in `combat/status_effects.py`, `combat/combat_engine.py`,
> `combat/enemy_ai.py`, `combat/ally_skills.py`, and `resources/skill_book/skill_list.yaml`.

---

## 1. Shocked (Thunder DoT + Stun Proc)

**Type:** Enemy debuff  
**Element:** Thunder  
**Design:** DoT tick each round + 25% chance to stun on each tick.  
**Why:** Thunder currently has no unique debuff. This gives it identity — dangerous but unreliable CC.

### apply function
```python
def apply_shock(enemy, damage, duration=3):
    """Apply Shocked to an enemy — thunder DoT with stun chance per tick."""
    existing = next(
        (d for d in enemy.get("active_debuffs", []) if d["type"] == "shock"), None
    )
    if existing:
        existing["remaining"] = duration
        existing["damage"] = max(existing["damage"], damage)
        return "refreshed"
    enemy.setdefault("active_debuffs", []).append({
        "type": "shock",
        "damage": damage,
        "remaining": duration,
    })
    return "applied"
```

### tick logic (in `tick_enemy_debuffs`)
```python
elif debuff["type"] == "shock":
    dmg = debuff["damage"]
    enemy["hp"] -= dmg
    messages.append(f"The {enemy['name']} is jolted for {dmg} thunder damage!")
    # 25% chance to stun on each tick
    if random.random() < 0.25:
        enemy["stunned"] = True
        messages.append(f"The {enemy['name']} is paralyzed by the shock!")
    debuff["remaining"] -= 1
    if debuff["remaining"] <= 0:
        enemy["active_debuffs"].remove(debuff)
        messages.append(f"The sparks fade from {enemy['name']}.")
```

### Display label
Add to `get_player_status_tags` type_labels (if player can be shocked):
```python
"shock": "Shocked",
```

### Skill YAML integration
```yaml
# Example Mage skill
mage_thunderbolt:
  name: Thunderbolt
  description: Strike an enemy with lightning, applying Shocked for 3 turns.
  unlock_level: 6
  cooldown: 3
  target: enemy
  power_type: ler
  base_power: 10
  shock_damage: 4
  shock_duration: 3
```

---

## 2. Barrier / Ward (Damage-Absorb Shield)

**Type:** Player/Ally buff  
**Design:** Absorbs X damage before HP is touched. Fills the gap between "no protection" 
and the Divine Shield full-immunity. Good for squishy classes.

### apply function
```python
def apply_barrier(target, amount, duration=3):
    """Grant a damage-absorbing barrier to target (player or ally).

    Barrier absorbs incoming damage before HP is reduced.
    Stacks by adding to remaining absorb, not overwriting.
    """
    existing = next(
        (b for b in target.get("active_buffs", []) if b.get("type") == "barrier"), None
    )
    if existing:
        existing["value"] += amount
        existing["remaining"] = max(existing["remaining"], duration)
        return "reinforced"
    target.setdefault("active_buffs", []).append({
        "type": "barrier",
        "value": amount,
        "remaining": duration,
    })
    return "applied"


def absorb_damage(target, incoming_damage):
    """Apply barrier absorption to incoming damage. Call BEFORE dealing damage.

    Returns (actual_damage, absorbed_amount).
    Mutates barrier buff in place (reduces value or removes).
    """
    for buff in target.get("active_buffs", [])[:]:
        if buff.get("type") == "barrier" and buff.get("value", 0) > 0:
            absorbed = min(buff["value"], incoming_damage)
            buff["value"] -= absorbed
            if buff["value"] <= 0:
                target["active_buffs"].remove(buff)
            return incoming_damage - absorbed, absorbed
    return incoming_damage, 0
```

### tick logic (in `tick_player_buffs`)
```python
elif btype == "barrier":
    buff["remaining"] -= 1
    if buff["remaining"] <= 0:
        player["active_buffs"].remove(buff)
        messages.append("Your barrier shimmers and fades.")
    elif buff.get("value", 0) > 0:
        messages.append(f"Barrier: {buff['value']} absorb remaining.")
```

### Integration in combat (enemy_ai.py, before damage application)
```python
# Before dealing damage to player:
actual_dmg, absorbed = absorb_damage(player, raw_dmg)
if absorbed > 0:
    c_print(f"Your barrier absorbs {absorbed} damage!")
player["current_hp"] -= actual_dmg
```

---

## 3. Sleep (Action Lock, Breaks on Damage)

**Type:** Enemy debuff  
**Design:** Skips turns. Breaks when the enemy takes damage. Stronger than stun 
because it can last multiple turns, but fragile.

### apply function
```python
def apply_sleep(enemy, duration=3):
    """Put an enemy to sleep. Slept enemies skip turns until damaged."""
    if enemy.get("asleep"):
        return "already_asleep"
    enemy["asleep"] = True
    enemy.setdefault("active_debuffs", []).append({
        "type": "sleep",
        "remaining": duration,
    })
    return "applied"


def wake_on_damage(enemy):
    """Call after dealing damage to a sleeping enemy. Returns message or None."""
    if enemy.get("asleep"):
        enemy["asleep"] = False
        enemy["active_debuffs"] = [
            d for d in enemy.get("active_debuffs", []) if d.get("type") != "sleep"
        ]
        return f"The {enemy['name']} jolts awake!"
    return None
```

### tick logic (in `tick_enemy_debuffs`)
```python
elif debuff["type"] == "sleep":
    debuff["remaining"] -= 1
    if debuff["remaining"] <= 0:
        enemy["asleep"] = False
        enemy["active_debuffs"].remove(debuff)
        messages.append(f"The {enemy['name']} stirs awake naturally.")
```

### Integration in enemy_ai.py (early turn check)
```python
# Check BEFORE stunned/frozen, so sleep takes highest priority:
if enemy.get("asleep"):
    c_print(f"The {enemy['name']} is fast asleep...")
    return "asleep"
```

### Integration in player_actions.py (after dealing damage)
```python
# After enemy takes damage from player attack:
wake_msg = wake_on_damage(target)
if wake_msg:
    c_print(wake_msg)
```

---

## 4. Haste (Speed & Action Buff)

**Type:** Player/Ally buff  
**Design:** +3 initiative (turn order) and grants the existing `cooldown_reduction` 
effect bundled in. Makes the buff feel impactful beyond just cooldown.

### apply function
```python
def apply_haste(target, duration=3, init_bonus=3, cd_reduction=1):
    """Haste the target — they act faster and skills recover quicker."""
    existing = next(
        (b for b in target.get("active_buffs", []) if b.get("type") == "haste"), None
    )
    if existing:
        existing["remaining"] = max(existing["remaining"], duration)
        existing["value"] = max(existing.get("value", 0), init_bonus)
        existing["cd_reduction"] = max(existing.get("cd_reduction", 0), cd_reduction)
        return "refreshed"
    target.setdefault("active_buffs", []).append({
        "type": "haste",
        "value": init_bonus,        # initiative bonus
        "cd_reduction": cd_reduction,
        "remaining": duration,
    })
    return "applied"


def get_haste_initiative_bonus(target):
    """Return the initiative bonus from Haste (0 if none)."""
    for b in target.get("active_buffs", []):
        if b.get("type") == "haste":
            return b.get("value", 0)
    return 0
```

### tick logic (in `tick_player_buffs`)
```python
elif btype == "haste":
    buff["remaining"] -= 1
    if buff["remaining"] <= 0:
        player["active_buffs"].remove(buff)
        messages.append("Your movements return to normal — haste fades.")
```

### Integration in initiative roll (combat_engine.py)
```python
# In roll_initiative(), when computing player/ally speed:
haste_bonus = get_haste_initiative_bonus(entity_dict)
player_speed = random.randint(1, 20) + p_dex + get_wisdom_bonus(player) + haste_bonus
```

### Integration in cooldown application (skills.py `set_skill_cooldown`)
Consume the `cd_reduction` from the haste buff (or keep the existing `cooldown_reduction` 
consumption logic — haste would just be an alternate source).

---

## 5. Paralyze (Stronger Stun — Multi-Turn, No Auto-Break)

**Type:** Enemy debuff  
**Design:** Like stun but lasts multiple turns and does NOT auto-clear after one skip. 
Rare, powerful. More threatening than freeze (which thaws into slow).

### apply function
```python
def apply_paralyze(enemy, duration=2):
    """Paralyze an enemy — skip all actions for N turns. Stronger than stun."""
    if enemy.get("paralyzed"):
        return "already_paralyzed"
    enemy["paralyzed"] = True
    enemy.setdefault("active_debuffs", []).append({
        "type": "paralyze",
        "remaining": duration,
    })
    return "applied"
```

### tick logic (in `tick_enemy_debuffs`)
```python
elif debuff["type"] == "paralyze":
    debuff["remaining"] -= 1
    if debuff["remaining"] <= 0:
        enemy["paralyzed"] = False
        enemy["active_debuffs"].remove(debuff)
        messages.append(f"The {enemy['name']} breaks free from paralysis!")
```

### Integration in enemy_ai.py early turn check
```python
if enemy.get("paralyzed"):
    c_print(f"The {enemy['name']} is paralyzed and cannot move!")
    return "paralyzed"
```
> Place AFTER sleep check (sleep breaks on damage, paralyze does not).

---

## 6. Regeneration (Long-Duration HoT)

**Type:** Player/Ally buff  
**Design:** A longer-lasting, smaller-tick HoT. Distinct from the current `hot` 
(healing salve) which is short. Good for Cleric/Druid-style sustain.

### apply function
```python
def apply_regen(target, heal_per_tick, duration=5):
    """Grant long-duration regeneration. Heals a small amount each round."""
    existing = next(
        (b for b in target.get("active_buffs", []) if b.get("type") == "regen"), None
    )
    if existing:
        existing["value"] = max(existing["value"], heal_per_tick)
        existing["remaining"] = max(existing["remaining"], duration)
        return "refreshed"
    target.setdefault("active_buffs", []).append({
        "type": "regen",
        "value": heal_per_tick,
        "remaining": duration,
    })
    return "applied"
```

### tick logic (in `tick_player_buffs`)
```python
elif btype == "regen":
    old_hp = target["current_hp"]
    from combat.stat_milestones import get_wisdom_bonus
    heal = buff["value"] + get_wisdom_bonus(target)
    new_hp = min(old_hp + heal, player_max_hp(target))
    healed = new_hp - old_hp
    target["current_hp"] = new_hp
    if healed > 0:
        messages.append(f"Regeneration restores {healed} HP.")
    buff["remaining"] -= 1
    if buff["remaining"] <= 0:
        target["active_buffs"].remove(buff)
        messages.append("Your regeneration fades.")
```

---

## 7. Entombed (Earth — Flee Lock + Healing Reduction)

**Type:** Enemy debuff  
**Element:** Earth  
**Design:** Earth's debuff. Prevents fleeing and reduces healing received by 50%. 
Makes Earth-element attacks good against healing enemies.

### apply function
```python
def apply_entomb(enemy, duration=3):
    """Entomb an enemy in stone. Cannot flee. Healing received is halved."""
    existing = next(
        (d for d in enemy.get("active_debuffs", []) if d["type"] == "entomb"), None
    )
    if existing:
        existing["remaining"] = max(existing["remaining"], duration)
        return "refreshed"
    enemy.setdefault("active_debuffs", []).append({
        "type": "entomb",
        "remaining": duration,
    })
    enemy["entombed"] = True
    return "applied"


def is_entombed(enemy):
    """Check if an enemy is entombed (for healing reduction)."""
    return bool(enemy.get("entombed"))

def get_healing_multiplier(target):
    """Return healing multiplier (0.5 if entombed, 1.0 otherwise)."""
    return 0.5 if target.get("entombed") else 1.0
```

### tick logic (in `tick_enemy_debuffs`)
```python
elif debuff["type"] == "entomb":
    debuff["remaining"] -= 1
    if debuff["remaining"] <= 0:
        enemy["entombed"] = False
        enemy["active_debuffs"].remove(debuff)
        messages.append(f"The stone crumbles from {enemy['name']}.")
```

---

## 8. Void-Touched (Dark — Healing Becomes Damage)

**Type:** Player/Enemy debuff  
**Element:** Dark  
**Design:** While void-touched, any healing received deals damage instead. High-risk, 
high-impact debuff. Fits the dark/abyss theme perfectly.

### apply function
```python
def apply_void_touched(target, duration=2):
    """Curse target with void — healing received becomes damage."""
    if target.get("void_touched"):
        return "already_void_touched"
    target["void_touched"] = True
    target.setdefault("active_debuffs", []).append({
        "type": "void_touched",
        "remaining": duration,
    })
    return "applied"
```

### tick logic (in `tick_player_debuffs` or `tick_enemy_debuffs`)
```python
elif dtype == "void_touched":
    debuff["remaining"] -= 1
    if debuff["remaining"] <= 0:
        target["void_touched"] = False
        target["active_debuffs"].remove(debuff)
        messages.append(f"The void's grip on {target.get('name', 'you')} releases.")
```

### Integration — wrap all healing with this check
Create a central healing helper:
```python
def apply_healing(target, amount):
    """Apply healing to a target, respecting void_touched."""
    if target.get("void_touched"):
        target["current_hp"] -= amount  # healing hurts!
        return -amount  # negative = damage dealt
    old_hp = target.get("current_hp", target.get("hp", 0))
    max_hp = target.get("max_hp", old_hp)
    target["current_hp"] = min(old_hp + amount, max_hp)
    return target["current_hp"] - old_hp
```

---

## Summary: Files That Need Changes

| File | What to add |
|------|-------------|
| `combat/status_effects.py` | All `apply_*` functions, tick logic additions, query helpers, display labels |
| `combat/combat_engine.py` | Haste in initiative, barrier absorption hook, sleep wake hook |
| `combat/enemy_ai.py` | Sleep/paralyze turn-skip checks, barrier absorb before damage |
| `combat/player_actions.py` | Wake-on-damage for sleep, barrier absorb before damage |
| `combat/ally_skills.py` | Apply calls for new debuffs in ally skill execution |
| `resources/skill_book/skill_list.yaml` | New skills that use these statuses |
| `combat/helpers.py` (optional) | Central `apply_healing()` — refactor all healing to go through it |

## Implementation Order (Recommended)

| Priority | Status | Reason |
|----------|--------|--------|
| 1 | **Barrier** | Closes biggest design gap (no partial protection). Low risk. |
| 2 | **Shocked** | Gives Thunder element identity. Reuses existing stun logic. |
| 3 | **Haste** | High player satisfaction. Simple, just initiative + existing CD reduction. |
| 4 | **Sleep** | Creates tactical depth. Needs 3 integration points but logic is simple. |
| 5 | **Entombed** | Gives Earth element identity. Healing reduction is easy to add. |
| 6 | **Paralyze** | Minor variant of freeze/stun. Low effort, adds variety. |
| 7 | **Regeneration** | Minor variant of HoT. Low effort. |
| 8 | **Void-Touched** | Coolest but highest effort — needs healing system refactor. Save for last. |
