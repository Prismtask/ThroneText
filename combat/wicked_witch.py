# combat/wicked_witch.py — Wonderland Superboss: Wicked Witch of the West (Floor 30)
#
# MECHANIC OVERVIEW:
# ─────────────────
# Three-phase fight with Flying Monkey minions in Phase 2.
#
# Phase 1 — Emerald Flame (100%–65%):
#   Cycles fire spells: Ember Volley → Fireball → Wall of Flame → Scrying Smoke.
#   "How about a little fire, Scarecrow?" at 85% HP: massive fire hit on lowest-res target.
#   Emerald Cackle every 4 witch turns: AoE dark + Fear chance, +15% fire damage.
#
# Phase 2 — Flying Fury (65%–30%):
#   Summons 3 Flying Monkeys. Witch gains Broomstick Evasion (+40% dodge).
#   Landing cycle: 3 turns airborne → 2 turns grounded (vulnerable, evasion suppressed).
#   Monkeys steal consumables on Dive Bomb (30% chance).
#
# Phase 3 — I'm Melting! (30%–0%):
#   Witch auto-melts 3% max HP/turn. Attacks twice per turn.
#   Damage ramps: +20% → +40% → +60% as HP drops.
#   Death Throes at ≤5% HP: final AoE fire to ALL combatants (including witch).
#
# Water Weakness: 2× damage from water (via YAML elemental_res override).
#   Water hits also interrupt fire spell casts in Phases 1–2 (witch loses turn).
#
# Dorothy synergy: +25% Fear resist for party in Phase 1, Phase 2 hint, Phase 3 immunity.
#   Permanent unlock trigger set via context flag on water-finisher kill.

import random
from combat.stats import enemy_stats, compute_player_stats
from combat.player_actions import handle_player_turn
from combat.combat_ui import format_enemy_status_line, print_superboss_header
from combat.superboss_common import superboss_combat_loop
from combat.status_effects import apply_bleed
from combat.combat_io import c_print, c_input, c_clear

# ── Keys ────────────────────────────────────────────────────────────────────

WITCH_KEY  = "wl_wicked_witch"
MONKEY_KEY = "wl_flying_monkey"


# ── Helpers ──────────────────────────────────────────────────────────────────

def _is_witch(e):
    return e.get("key") == WITCH_KEY


def _is_monkey(e):
    return e.get("key") == MONKEY_KEY


def _count_live_monkeys(enemies):
    return sum(1 for e in enemies if _is_monkey(e) and e["hp"] > 0 and not e.get("captured"))


def _find_witch(enemies):
    for e in enemies:
        if _is_witch(e) and e["hp"] > 0:
            return e
    return None


def _spawn_monkeys(player, enemies, count=3):
    """Spawn Flying Monkey minions and add them to the enemy list."""
    spawned = []
    for _ in range(count):
        monkey = enemy_stats(MONKEY_KEY, player)
        monkey["key"] = MONKEY_KEY
        monkey["max_hp"] = monkey["hp"]
        enemies.append(monkey)
        spawned.append(monkey)
    return spawned


def _get_living_targets(player):
    """Return list of living player + active allies."""
    targets = []
    if player.get("current_hp", 0) > 0:
        targets.append(player)
    for ally in player.get("allies", []):
        if ally.get("current_hp", 0) > 0:
            targets.append(ally)
    return targets


def _find_lowest_fire_res(player):
    """Find the party member with the lowest fire resistance (highest res value = weakest)."""
    targets = _get_living_targets(player)
    if not targets:
        return None
    best = targets[0]
    best_res = best.get("elemental_res", {}).get("fire", 1.0)
    for t in targets[1:]:
        res = t.get("elemental_res", {}).get("fire", 1.0)
        if res > best_res:
            best_res = res
            best = t
    return best


def _deal_damage(target, dmg, element=None):
    """Apply damage to a target, respecting elemental resistances."""
    if element:
        res = target.get("elemental_res", {}).get(element, 1.0)
        dmg = max(1, int(dmg * res))
    target["current_hp"] = max(0, target.get("current_hp", 0) - dmg)


def _apply_broomstick_evasion(witch):
    """Apply +40% broomstick evasion buff."""
    _remove_broomstick_evasion(witch)
    witch.setdefault("active_buffs", []).append({
        "type": "evasion",
        "value": 0.40,
        "remaining": 999,
        "source": "broomstick_evasion",
    })


def _remove_broomstick_evasion(witch):
    """Remove broomstick evasion buff."""
    witch["active_buffs"] = [
        b for b in witch.get("active_buffs", [])
        if b.get("source") != "broomstick_evasion"
    ]


# ── Phase 1: Emerald Flame ──────────────────────────────────────────────────

def _witch_ember_volley(witch, player):
    """3 small fire hits on random targets. Applies Burning (3 dmg × 2 turns) per hit."""
    targets = _get_living_targets(player)
    for i in range(3):
        if not targets:
            break
        target = random.choice(targets)
        dmg = random.randint(8, 12)
        c_print(f"  Ember strikes {target.get('name', 'You')}! {dmg} dmg [FIRE]")
        _deal_damage(target, dmg, "fire")
        apply_bleed(target, 3, 2)


def _witch_fireball(witch, player):
    """Single-target heavy fire damage. 25% chance to destroy one consumable."""
    targets = _get_living_targets(player)
    if not targets:
        return
    target = random.choice(targets)
    dmg = random.randint(30, 45)
    c_print(f'  Fireball strikes {target.get("name", "You")}! {dmg} dmg [FIRE]')
    _deal_damage(target, dmg, "fire")
    if random.random() < 0.25:
        c_print('  "Your potions! They\'re boiling!"')
        # Destroy one random consumable from target inventory
        inv = target.get("inventory", [])
        consumables = [inv_item for inv_item in inv
                       if isinstance(inv_item, dict) and inv_item.get("type") == "consumable"]
        if consumables:
            destroyed = random.choice(consumables)
            inv.remove(destroyed)
            c_print(f'  ↠ {destroyed.get("name", "an item")} is destroyed!')


def _witch_wall_of_flame(witch):
    """Self-buff: 2 turns of 10 fire reflect damage on attackers."""
    c_print("  The Witch raises a wall of emerald flame! (Reflect: 10 fire dmg, 2 turns)")
    witch.setdefault("active_buffs", []).append({
        "type": "reflect",
        "value": 10,
        "remaining": 2,
        "source": "wall_of_flame",
    })


def _witch_scrying_smoke(witch, player):
    """Read one target's lowest resistance; next attack exploits it."""
    targets = _get_living_targets(player)
    if not targets:
        return
    target = random.choice(targets)
    c_print(f'  Scrying smoke swirls around {target.get("name", "You")}...')
    c_print('  "I see your weaknesses, my pretty."')
    # Store for next turn — witch will use single heavy hit with that element
    # For simplicity: store the target ref and flag
    witch["_scrying_target"] = target
    # Find weakest element (highest res value)
    reses = target.get("elemental_res", {})
    if reses:
        weakest = max(reses, key=reses.get)
        witch["_scrying_element"] = weakest
        c_print(f'  ↠ The Witch learns your weakness to {weakest}!')


def _witch_emerald_cackle(witch, player, ctx):
    """AoE dark damage + 40% Fear on each target. +15% fire damage for 1 turn."""
    c_print('\n  "Eh heheheheHAHAHAHA!"')
    c_print("  The Witch's cackle echoes through the chamber!")
    for target in _get_living_targets(player):
        dmg = random.randint(15, 25)
        c_print(f"  {target.get('name', 'You')} takes {dmg} dmg [DARK] — Emerald Cackle")
        _deal_damage(target, dmg, "dark")
        # 40% Fear chance (skip Dorothy)
        if target.get("_heroine_key") != "dorothy" and random.random() < 0.40:
            target.setdefault("active_debuffs", []).append({
                "type": "fear",
                "remaining": 1,
                "source": "emerald_cackle",
            })
            c_print(f'    {target.get("name", "You")} is FEARED!')
    # +15% fire damage for 1 turn
    witch.setdefault("active_buffs", []).append({
        "type": "damage_boost",
        "value": 0.15,
        "remaining": 1,
        "source": "emerald_cackle",
    })


def _witch_little_fire(witch, player, ctx):
    """85% HP trigger: massive fire hit on lowest fire-res target."""
    ctx["used_little_fire"] = True
    target = _find_lowest_fire_res(player)
    if target is None:
        return
    dmg = random.randint(50, 70)
    c_print(f'\n  "How about a little fire, Scarecrow?"')
    c_print(f'  {target.get("name", "You")} is engulfed! {dmg} dmg [FIRE]')
    _deal_damage(target, dmg, "fire")
    if target.get("current_hp", 0) <= 0:
        c_print('  "One down. They always burn."')
    else:
        c_print('  "Stubborn. Like the Scarecrow. He burned anyway."')


def _witch_phase1_turn(witch, player, ctx):
    """Execute one Phase 1 Witch action. Returns (actions, skip_default, extra_logic, armor_mult, temp_str)."""
    hp_pct = witch["hp"] / witch["max_hp"]

    # ── "How about a little fire" at 85% (once) ─────────────────────────
    if not ctx["used_little_fire"] and hp_pct <= 0.85:
        _witch_little_fire(witch, player, ctx)
        return 1, True, None, 1.0, 0

    # ── Emerald Cackle every 4 witch actions ────────────────────────────
    if ctx["witch_actions"] > 0 and ctx["witch_actions"] % 4 == 0:
        _witch_emerald_cackle(witch, player, ctx)
        return 1, True, None, 1.0, 0

    # ── Spell cycle (0→1→2→3→0…) ───────────────────────────────────────
    spell_idx = ctx["phase1_spell_idx"] % 4
    ctx["phase1_spell_idx"] += 1

    if spell_idx == 0:
        _witch_ember_volley(witch, player)
    elif spell_idx == 1:
        _witch_fireball(witch, player)
    elif spell_idx == 2:
        _witch_wall_of_flame(witch)
        return 1, True, None, 1.0, 0   # Wall of Flame = no attack
    elif spell_idx == 3:
        _witch_scrying_smoke(witch, player)
        return 1, True, None, 1.0, 0   # Scrying Smoke = no attack

    return 1, False, None, 1.0, 0


# ── Phase 2: Flying Fury ────────────────────────────────────────────────────

def _witch_broomstick_dive(witch, player):
    """Physical dive attack on landing turn."""
    targets = _get_living_targets(player)
    if not targets:
        return
    target = random.choice(targets)
    dmg = random.randint(20, 35)
    c_print(f'  "You\'ll have to catch me—" she gasps, diving at {target.get("name", "You")}!')
    c_print(f"  Broomstick Dive! {dmg} dmg [PHYSICAL]")
    _deal_damage(target, dmg, "physical")


def _witch_fire_from_above(witch, player):
    """AoE fire damage on all party members."""
    for target in _get_living_targets(player):
        dmg = random.randint(20, 30)
        c_print(f"  Fire rains on {target.get('name', 'You')}! {dmg} dmg [FIRE]")
        _deal_damage(target, dmg, "fire")


def _witch_here_my_pretty(witch, player):
    """Mark one target: +15% damage taken from all sources for 2 turns."""
    targets = _get_living_targets(player)
    if not targets:
        return
    target = random.choice(targets)
    c_print(f'  "Here, my pretty!" — the Witch marks {target.get("name", "You")}!')
    target.setdefault("active_debuffs", []).append({
        "type": "marked",
        "value": 0.15,
        "remaining": 2,
        "source": "heres_my_pretty",
    })


def _witch_phase2_turn(witch, player, ctx, elist):
    """Execute one Phase 2 Witch action. Returns (actions, skip_default, extra_logic, armor_mult, temp_str)."""

    # ── Flight cycle management ─────────────────────────────────────────
    if ctx["vulnerable_remaining"] > 0:
        # Witch is grounded — vulnerable window
        ctx["vulnerable_remaining"] -= 1
        if ctx["vulnerable_remaining"] <= 0:
            # Re-apply evasion, reset flight timer
            _apply_broomstick_evasion(witch)
            ctx["broomstick_evasion_active"] = True
            ctx["flight_timer"] = 3
            c_print('\n  "The Witch remounts her broomstick! Evasion restored."')
            _witch_fire_from_above(witch, player)
            return 1, False, None, 1.0, 0
        else:
            _witch_fire_from_above(witch, player)
            return 1, False, None, 1.0, 0

    # Witch is airborne — count down to landing
    ctx["flight_timer"] -= 1

    if ctx["flight_timer"] <= 0:
        # LANDING! Remove evasion, set vulnerable window
        _remove_broomstick_evasion(witch)
        ctx["broomstick_evasion_active"] = False
        ctx["vulnerable_remaining"] = 2
        c_print('\n  "The Witch descends to catch her breath..."')
        c_print('  "You\'ll pay for that!" She lands hard — her magic wavers.')
        _witch_broomstick_dive(witch, player)
        return 1, False, None, 1.0, 0

    # ── "Here, my pretty!" every 3 witch actions ───────────────────────
    if ctx["witch_actions"] > 0 and ctx["witch_actions"] % 3 == 0:
        _witch_here_my_pretty(witch, player)
        return 1, True, None, 1.0, 0

    # ── Summon monkeys if fewer than 2 alive ────────────────────────────
    if _count_live_monkeys(elist) < 2:
        c_print('\n  "More! I need MORE of you!"')
        spawned = _spawn_monkeys(player, elist, 2)
        for m in spawned:
            c_print(f"  {m['name']} swoops in! HP: {m['hp']}")
        return 1, True, None, 1.0, 0

    # ── Default: Fire From Above ───────────────────────────────────────
    _witch_fire_from_above(witch, player)
    return 1, False, None, 1.0, 0


# ── Phase 3: I'm Melting! ───────────────────────────────────────────────────

def _witch_emerald_curse(witch, player):
    """Single target: dark damage + cannot be healed for 2 turns."""
    targets = _get_living_targets(player)
    if not targets:
        return
    target = random.choice(targets)
    dmg = random.randint(15, 25)
    c_print(f'  Emerald Curse strikes {target.get("name", "You")}! {dmg} dmg [DARK]')
    _deal_damage(target, dmg, "dark")
    target.setdefault("active_debuffs", []).append({
        "type": "heal_block",
        "remaining": 2,
        "source": "emerald_curse",
    })
    c_print(f'    {target.get("name", "You")} cannot be healed for 2 turns!')


def _witch_black_smoke(witch, player):
    """AoE dark damage. Applies Blinding to non-Dorothy targets."""
    for target in _get_living_targets(player):
        if target.get("_heroine_key") == "dorothy":
            continue  # Dorothy immune
        dmg = random.randint(20, 35)
        c_print(f"  Black Smoke engulfs {target.get('name', 'You')}! {dmg} dmg [DARK]")
        _deal_damage(target, dmg, "dark")
        # Blinding: 50% miss, 1 turn
        target.setdefault("active_debuffs", []).append({
            "type": "blind",
            "remaining": 1,
            "source": "black_smoke",
        })
        c_print(f'    {target.get("name", "You")} is BLINDED!')


def _witch_death_throes(witch, player):
    """Final AoE fire to ALL combatants (including witch)."""
    c_print('\n  "I\'LL TAKE YOU ALL WITH ME!"')
    c_print("  The Witch explodes in a final burst of emerald flame!")
    for target in _get_living_targets(player):
        dmg = random.randint(50, 70)
        c_print(f"  {target.get('name', 'You')} takes {dmg} dmg [FIRE] — Death Throes!")
        _deal_damage(target, dmg, "fire")
    # Witch also takes damage
    self_dmg = random.randint(50, 70)
    witch["hp"] = max(0, witch["hp"] - self_dmg)
    c_print(f"  The Witch takes {self_dmg} from her own Death Throes!")


def _witch_phase3_turn(witch, player, ctx, elist):
    """Execute Phase 3 Witch actions (2 per turn). Returns (actions, skip_default, extra_logic, armor_mult, temp_str)."""

    # ── Auto-melt ───────────────────────────────────────────────────────
    melt_dmg = max(1, int(witch["max_hp"] * 0.03))
    witch["hp"] = max(0, witch["hp"] - melt_dmg)

    if witch["hp"] <= 0:
        c_print('\n  The Witch dissolves into a puddle of green smoke and black fabric...')
        return 1, True, None, 1.0, 0

    hp_pct = witch["hp"] / witch["max_hp"]

    # ── Death Throes at ≤5% HP ──────────────────────────────────────────
    if hp_pct <= 0.05 and not ctx.get("death_throes_used"):
        ctx["death_throes_used"] = True
        _witch_death_throes(witch, player)
        return 1, True, None, 1.0, 0

    # ── 2 actions per turn ─────────────────────────────────────────────
    actions_taken = 0
    for _ in range(2):
        if witch["hp"] <= 0:
            break
        # Alternate: Emerald Curse → Black Smoke
        if actions_taken == 0:
            _witch_emerald_curse(witch, player)
        else:
            _witch_black_smoke(witch, player)
        actions_taken += 1

    return 1, True, None, 1.0, 0


# ── Monkey AI ────────────────────────────────────────────────────────────────

def _monkey_steal_logic(enemy, target, dmg):
    """Extra logic: 30% chance to steal a consumable after Dive Bomb."""
    if random.random() < 0.30:
        inv = target.get("inventory", [])
        consumables = [inv_item for inv_item in inv
                       if isinstance(inv_item, dict) and inv_item.get("type") == "consumable"]
        if consumables:
            stolen = random.choice(consumables)
            inv.remove(stolen)
            return f"  ↠ {enemy['name']} steals {stolen.get('name', 'an item')}!"
    return None


# ── Main Combat Function ────────────────────────────────────────────────────

def combat_wicked_witch(player, floor=None, enemies=None):
    """Wonderland Superboss — Wicked Witch of the West (Floor 30).

    Args:
        enemies: Optional pre-created enemy list for GUI mode state sharing.
    """
    if floor is None:
        loc = player.get("location", "")
        floor = player.get("city_floors", {}).get(loc, {}).get("floor", 30)

    # ── Create or locate boss ────────────────────────────────────────────
    if enemies is None:
        witch = enemy_stats(WITCH_KEY, player)
        witch["max_hp"] = witch["hp"]
        enemies = [witch]
    else:
        witch = _find_witch(enemies)
        if witch is None:
            witch = enemy_stats(WITCH_KEY, player)
            witch["max_hp"] = witch["hp"]
            enemies.append(witch)
        else:
            witch["max_hp"] = witch["hp"]
            witch["hp"] = witch["max_hp"]  # Reset HP in GUI mode

    # ── Check for Dorothy ────────────────────────────────────────────────
    dorothy = next((a for a in player.get("allies", [])
                    if a.get("_heroine_key") == "dorothy"
                    and a.get("current_hp", 0) > 0), None)

    # ── Opening narration ────────────────────────────────────────────────
    c_clear()
    c_print("=" * 60)
    c_print("The corridor opens into a vast chamber. The walls are green —")
    c_print("not painted, but glowing faintly, as though the stone itself")
    c_print("is sick with envy.")
    c_print("")
    c_print("At the far end, silhouetted against an emerald flame, a figure")
    c_print("in black waits. Her hat is impossibly tall. Her skin is the")
    c_print("colour of jealousy. Her eyes are fixed on you — no, past you.")
    c_print("")
    if dorothy:
        c_print('"I smell... Kansas."')
        c_print("")
        c_print('Dorothy stiffens beside you. "She\'s been waiting for me."')
    else:
        c_print('"I smell... an intruder. How... predictable."')
    c_print("")
    c_print('She turns. The emerald flame gutters and flares.')
    c_print('"Let\'s not rush. Let\'s... savour it."')
    c_print("=" * 60)
    c_print(f"\nWicked Witch of the West — HP: {witch['hp']}")
    c_input("\nPress Enter to face the Witch...")

    # ── Combat context ──────────────────────────────────────────────────
    context = {
        "phase": 1,                    # Current phase: 1, 2, or 3
        "witch_actions": 0,            # Total witch turns taken
        "phase1_spell_idx": 0,         # Rotating spell index for Phase 1
        "used_little_fire": False,     # "How about a little fire" fired?

        # Phase 2: minions & flight
        "monkeys_summoned": False,     # Initial 3 monkeys spawned
        "flight_timer": 3,             # Counts down to landing
        "vulnerable_remaining": 0,     # Turns witch is grounded (0 = airborne)
        "broomstick_evasion_active": False,

        # Phase 3: melting
        "death_throes_used": False,

        # Dorothy integration
        "dorothy_in_party": dorothy is not None,
        "dorothy_hint_given": False,
    }

    # ── Hooks ───────────────────────────────────────────────────────────

    def pre_player_hook(ctx, elist):
        """Check HP thresholds and handle phase transitions."""
        witch_obj = _find_witch(elist)
        if witch_obj is None:
            return None

        hp_pct = witch_obj["hp"] / witch_obj["max_hp"]

        # ── Phase 1 → 2 (65% HP) ─────────────────────────────────────
        if hp_pct <= 0.65 and ctx["phase"] == 1:
            ctx["phase"] = 2
            ctx["broomstick_evasion_active"] = True
            _apply_broomstick_evasion(witch_obj)
            ctx["flight_timer"] = 3
            ctx["vulnerable_remaining"] = 0
            spawned = _spawn_monkeys(player, elist, 3)
            ctx["monkeys_summoned"] = True

            c_print("\n" + "-" * 50)
            c_print("The Witch stumbles. Her emerald flame gutters. For a")
            c_print("moment — just a moment — she looks afraid.")
            c_print("")
            c_print("Then she laughs. It's not a cackle this time. It's cold.")
            c_print('"You\'re stronger than I expected. No matter. I didn\'t come alone."')
            c_print("")
            c_print("She raises a gnarled hand. The shadows in the corners of")
            c_print("the chamber begin to writhe. Wings. Dozens of wings.")
            c_print("")
            c_print('"FLY, MY PRETTIES! FLY!"')
            c_print("-" * 50)
            for m in spawned:
                c_print(f"  {m['name']} swoops in! HP: {m['hp']}")
            c_input("Press Enter...")

        # ── Phase 2 → 3 (30% HP) ─────────────────────────────────────
        elif hp_pct <= 0.30 and ctx["phase"] == 2:
            ctx["phase"] = 3
            # Remove all monkeys — they flee
            for e in elist[:]:
                if _is_monkey(e):
                    elist.remove(e)
            # Remove evasion — witch is grounded permanently
            _remove_broomstick_evasion(witch_obj)
            ctx["broomstick_evasion_active"] = False

            c_print("\n" + "!" * 50)
            c_print("A strike catches the Witch mid-cackle. She shrieks — not")
            c_print("in anger. In pain. Real, genuine pain.")
            c_print("")
            c_print("Her broomstick lurches. She crashes to the ground, robes")
            c_print("smoking. The emerald flame behind her SPUTTERS and DIES.")
            c_print("")
            c_print("The Flying Monkeys shriek and scatter. Without their")
            c_print("mistress's power, they're just frightened animals.")
            c_print("")
            c_print("The Witch rises slowly. Her hat is askew. Her green skin")
            c_print("is... running? Where the strike hit, her skin melts like wax.")
            c_print("")
            c_print('"What have you DONE?! Do you know what water DOES to me?!"')
            c_print('"I\'LL TAKE YOU ALL WITH ME!"')
            c_print("!" * 50)
            c_input("Press Enter...")

        # ── Dorothy Phase 2 hint ──────────────────────────────────────
        if (ctx["phase"] == 2 and ctx["dorothy_in_party"]
                and not ctx["dorothy_hint_given"]):
            ctx["dorothy_hint_given"] = True
            c_print('\nDorothy: "She always sends the monkeys first. She\'s')
            c_print('afraid to get her hands dirty — that\'s her weakness!')
            c_print('When she lands to catch her breath, her magic wavers.')
            c_print('That\'s when you strike."')
            c_input("Press Enter...")

        # ── Phase 3: announce melting ─────────────────────────────────
        if ctx["phase"] == 3 and not ctx.get("melting_announced"):
            ctx["melting_announced"] = True
            c_print('\n  "I\'m melting! MELTING! But I won\'t go alone —"')
            c_print(f'  The Witch loses {max(1, int(witch_obj["max_hp"] * 0.03))} HP per turn from melting!')

        return None

    def enemy_turn_hook(enemy, ctx, pl, p_con, defending, turn_order=None, step_idx=None):
        """Handle Witch-specific AI or monkey attacks."""

        # ── Monkey turn ──────────────────────────────────────────────
        if _is_monkey(enemy):
            return 1, False, _monkey_steal_logic, 1.0, 0

        # ── Non-witch enemy ──────────────────────────────────────────
        if not _is_witch(enemy):
            return 1, False, None, 1.0, 0

        # ── Increment witch action counter ───────────────────────────
        ctx["witch_actions"] += 1

        # ── Dispatch to phase handler ────────────────────────────────
        if ctx["phase"] == 3:
            return _witch_phase3_turn(enemy, pl, ctx, enemies)
        elif ctx["phase"] == 2:
            return _witch_phase2_turn(enemy, pl, ctx, enemies)
        else:
            return _witch_phase1_turn(enemy, pl, ctx)

    def post_round_hook(ctx, elist):
        """Tick witch buffs and handle post-round cleanup."""
        witch_obj = _find_witch(elist)
        if witch_obj is None:
            return

        # Tick buffs with "remaining" field
        for buff in witch_obj.get("active_buffs", []):
            if "remaining" in buff and buff.get("source") not in ("broomstick_evasion",):
                buff["remaining"] -= 1
        witch_obj["active_buffs"] = [
            b for b in witch_obj.get("active_buffs", [])
            if b.get("remaining", 999) > 0
        ]

        # Tick debuffs on player and allies
        for target in [player] + player.get("allies", []):
            for debuff in target.get("active_debuffs", []):
                if "remaining" in debuff:
                    debuff["remaining"] -= 1
            target["active_debuffs"] = [
                d for d in target.get("active_debuffs", [])
                if d.get("remaining", 999) > 0
            ]

    # ── Victory handler: Dorothy permanent unlock (Phase 18) ─────────────

    def on_kill_hook(target, elist, ctx):
        """Handle Witch death, Dorothy permanent unlock, and drops."""
        if _is_witch(target) and target.get("hp", 0) <= 0:
            from combat.ally import promote_heroine_to_permanent, set_heroine_state, get_heroine_in_party

            c_print("\n" + "=" * 60)
            c_print("The Witch dissolves into a puddle of ink and emerald")
            c_print("smoke. Her hat floats for a moment, then sinks.")
            c_print("")
            c_print("The green glow fades. The walls return to stone.")
            c_print("The chamber is just a chamber again — no magic,")
            c_print("no menace. Just silence and the faint smell of")
            c_print("ozone, like after a thunderstorm.")
            c_print("=" * 60)

            # ── Dorothy permanent unlock ──────────────────────────────
            if dorothy:
                join_level = dorothy.get("level", player.get("level", 1))
                promote_heroine_to_permanent(player, dorothy, join_level)
                set_heroine_state(player, "dorothy", "permanent")
                player["wl_boss_defeated_wicked_witch"] = True

                c_print(f'\n  Dorothy stands over the puddle, ruby slippers')
                c_print('  gleaming — no longer on the table, but on her feet.')
                c_print('')
                c_print('  "She\'s gone. She\'s really gone."')
                c_print('  (She clicks her heels once. Nothing happens.)')
                c_print('  (She clicks them twice. A warm breeze stirs.)')
                c_print('  (She doesn\'t click them a third time.)')
                c_print('')
                c_print('  "I could go home now. I can feel it — Kansas is')
                c_print('  right there, three clicks away. But..."')
                c_print('')
                c_print('  She looks at you. Toto barks.')
                c_print('')
                c_print('  "You\'re not from Kansas. And you\'re still fighting.')
                c_print('  Maybe... maybe home can wait. Just a little longer."')
                c_print('')
                c_print('  Dorothy becomes a PERMANENT ally.')
                c_input("Press Enter...")

    # ── Run the combat loop ──────────────────────────────────────────────
    return superboss_combat_loop(
        player, enemies, floor, "Wicked Witch of the West", context,
        pre_player_hook=pre_player_hook,
        enemy_turn_hook=enemy_turn_hook,
        post_round_hook=post_round_hook,
        on_kill_hook=on_kill_hook,
    )
