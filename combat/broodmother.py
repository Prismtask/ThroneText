# combat/broodmother.py
"""Superboss: Broodmother Vileheart — Pandemonium's first superboss.

Three-phase fight with venom, swarm, and desperation mechanics.

Phase 1 — "The Nest Awakens" (100%–70% HP):
  - 1 action/turn with AI-weighted attack selection
  - Venomous Strike (40%): single target + Poison (5 dmg x 3 turns)
  - Web Shot (25%): single target + Slow (-3 DEX, 2 turns) + 15% Stun
  - Acid Spray (25%): AoE all party + Corrosion (-15% DEF, 2 turns)
  - Feed the Brood (10%): self-heal 5% max HP, +2 STR for 2 turns
  - Passive spawn: if no spiderlings alive at round start, spawn 2 (max 3)

Phase 2 — "The Hatchling Swarm" (70%–35% HP):
  - Broodmother retreats to ceiling (untargetable)
  - Summons 4 Spiderlings + 1 Vileheart Venomweaver (elite)
  - Ceiling attacks: Toxic Rain (AoE poison), Web Cage (skip turn),
    Lay Eggs (spawn another spiderling)
  - Return condition: kill all minions OR survive 4 turns
  - On return: ENRAGED — 2 actions/turn, 10 impact damage to party

Phase 3 — "Vileheart's Desperation" (35%–0% HP):
  - 2 actions/turn, +50% damage, poison upgraded to 8 dmg x 4 turns
  - Venom Overload: spiderling death → +1 stack (+3% dmg, max 10)
    Clears on 50+ damage single hit
  - Toxic Explosion (every 4 turns): detonate all poison stacks on party
  - Consume Brood (every 3 turns): sacrifice spiderling → heal 15% +5 STR
  - Death Throes (below 15% HP): 10 unavoidable damage/round to all party
  - Heart Pulse (10% HP, once): 1-turn windup, 60+ dmg to interrupt
"""

import random
from combat.stats import enemy_stats, compute_player_stats
from combat.combat_ui import format_enemy_status_line, print_combat_hud
from combat.superboss_common import superboss_combat_loop
from combat.status_effects import apply_poison
from combat.ally import get_active_allies, compute_ally_stats
from combat.combat_io import c_print, c_input, c_clear

# ═══════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════

BOSS_KEY = "broodmother_vileheart"
SPIDERLING_KEY = "vileheart_spiderling"
VENOMWEAVER_KEY = "vileheart_venomweaver"

PHASE1_HP = 0.70   # Phase 1 → 2 threshold
PHASE2_HP = 0.35   # Phase 2 → 3 threshold
MAX_SPIDERLINGS = 3
VENOM_OVERLOAD_CAP = 10
HEART_PULSE_THRESHOLD = 0.10
HEART_PULSE_DMG_NEEDED = 60


# ═══════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════

def _get_boss(elist):
    return next((e for e in elist if e.get("key") == BOSS_KEY), None)


def _spawn_spiderling(player, count=1):
    """Create spiderling enemy dicts. Returns list."""
    spiderlings = []
    for _ in range(count):
        m = enemy_stats(SPIDERLING_KEY, player)
        m["key"] = SPIDERLING_KEY
        m["max_hp"] = m["hp"]
        spiderlings.append(m)
    return spiderlings


def _spawn_venomweaver(player):
    """Create a Venomweaver elite minion. Returns dict."""
    v = enemy_stats(VENOMWEAVER_KEY, player)
    v["key"] = VENOMWEAVER_KEY
    v["max_hp"] = v["hp"]
    return v


def _count_spiderlings(elist):
    """Count living spider-type minions (spiderlings + venomweavers)."""
    return sum(1 for e in elist
               if e.get("key") in (SPIDERLING_KEY, VENOMWEAVER_KEY)
               and e["hp"] > 0 and not e.get("captured"))


def _get_alive_party(player):
    """Return [player] + active alive allies."""
    party = [player] if player.get("current_hp", 0) > 0 else []
    for ally in get_active_allies(player):
        if ally.get("current_hp", 0) > 0:
            party.append(ally)
    return party


def _get_actor_con(actor, player, p_con):
    """Get CON for a target (player or ally)."""
    if actor is player:
        return p_con
    _, a_con, _, _, _, _ = compute_ally_stats(actor)
    return a_con


# ═══════════════════════════════════════════════════════════════════
# PHASE 1 ATTACKS
# ═══════════════════════════════════════════════════════════════════

def _phase1_attack_selection(boss, player, ctx):
    """AI-weighted attack selection for Phase 1.

    Returns (attack_name, extra_logic_fn, armor_mult, temp_str).
    """
    r = random.random()

    if r < 0.40:
        # Venomous Strike: poison on hit
        def venom_strike(e, p, dmg):
            if dmg > 0:
                apply_poison(p, 5, 3)
                return "🧪 Vileheart toxins seep into your veins! (Poison 5 x 3)"
            return None
        return "Venomous Strike", venom_strike, 1.0, 0

    elif r < 0.65:
        # Web Shot: slow + stun chance
        def web_shot(e, p, dmg):
            msgs = []
            # Apply Slow (-3 DEX, 2 turns)
            p.setdefault("active_debuffs", []).append({
                "type": "slow",
                "stat": "Dexterity",
                "value": -3,
                "remaining": 2,
                "source": "web_shot",
            })
            msgs.append("🕸️ Webbed! -3 DEX for 2 turns!")
            # 15% stun chance
            if random.random() < 0.15:
                p["stunned"] = True
                msgs.append("💥 You are STUNNED by the sticky webbing!")
            return " | ".join(msgs) if msgs else None
        return "Web Shot", web_shot, 1.0, 0

    elif r < 0.90:
        # Acid Spray: AoE, Corrosion debuff
        return "Acid Spray", _acid_spray_extra, 1.0, 0

    else:
        # Feed the Brood: self-heal + buff
        def feed_brood(e, p, dmg):
            heal = int(e.get("max_hp", 350) * 0.05)
            e["hp"] = min(e.get("max_hp", 350), e["hp"] + heal)
            e.setdefault("active_buffs", []).append({
                "type": "stat_buff",
                "stat": "Strength",
                "value": 2,
                "remaining": 2,
                "source": "feed_brood",
            })
            return f"🕷️ Broodmother feeds! +{heal} HP, +2 STR for 2 turns!"
        return "Feed the Brood", feed_brood, 1.0, 0


def _acid_spray_extra(enemy, player, dmg):
    """Acid Spray: AoE Corrosion debuff to all party members."""
    party = _get_alive_party(player)
    for target in party:
        target.setdefault("active_debuffs", []).append({
            "type": "corrosion",
            "value": -0.15,  # -15% DEF
            "remaining": 2,
            "source": "acid_spray",
        })
    return "🧪 Acid Spray! All party members: -15% DEF for 2 turns!"


# ═══════════════════════════════════════════════════════════════════
# PHASE 2 CEILING ATTACKS
# ═══════════════════════════════════════════════════════════════════

def _ceiling_attack_selection(boss, player, ctx, elist):
    """AI selection for Broodmother's ceiling attacks in Phase 2.

    Returns (attack_name, extra_logic_fn, armor_mult, temp_str).
    """
    r = random.random()
    if r < 0.45:
        # Toxic Rain: AoE poison
        return "Toxic Rain (from above)", _toxic_rain_extra, 1.0, 0
    elif r < 0.75:
        # Web Cage: trap a party member
        return "Web Cage (from above)", _web_cage_extra, 1.0, 0
    else:
        # Lay Eggs: spawn another spiderling
        return "Lay Eggs (from above)", lambda e, p, d: _lay_eggs_extra(ctx, elist, player), 1.0, 0


def _toxic_rain_extra(enemy, player, dmg):
    """Toxic Rain: apply poison to all party members."""
    party = _get_alive_party(player)
    for target in party:
        apply_poison(target, 3, 4)
    return "🌧️ Toxic Rain! All party poisoned (3 dmg x 4 turns)!"


def _web_cage_extra(enemy, player, dmg):
    """Web Cage: trap a random party member — they skip their next turn."""
    party = _get_alive_party(player)
    if not party:
        return None
    target = random.choice(party)
    name = target.get("name", "Someone")
    target["stunned"] = True
    return f"🕸️ Web Cage traps {name}! They'll miss their next turn!"


def _lay_eggs_extra(ctx, elist, player):
    """Lay Eggs: spawn 1 additional spiderling (max 5 total minions)."""
    current = _count_spiderlings(elist)
    if current >= 5:
        return "🥚 No room for more eggs..."
    spiderling = _spawn_spiderling(player, count=1)[0]
    elist.append(spiderling)
    ctx["_eggs_laid"] = ctx.get("_eggs_laid", 0) + 1
    return f"🥚 A Vileheart Spiderling hatches! ({current + 1} minions alive)"


# ═══════════════════════════════════════════════════════════════════
# PHASE 3 ATTACKS
# ═══════════════════════════════════════════════════════════════════

def _phase3_attack_selection(boss, player, ctx, elist):
    """AI-weighted attack selection for Phase 3 (enhanced versions).

    Returns (attack_name, extra_logic_fn, armor_mult, temp_str).
    """
    # Track Toxic Explosion cooldown
    toxic_cd = ctx.get("_toxic_explosion_cd", 0)
    if toxic_cd <= 0:
        # Time for Toxic Explosion!
        ctx["_toxic_explosion_cd"] = 4
        return "TOXIC EXPLOSION", _toxic_explosion_extra, 1.0, 0

    # Track Consume Brood cooldown
    consume_cd = ctx.get("_consume_brood_cd", 0)
    spiderlings_alive = _count_spiderlings(elist) > 0
    if consume_cd <= 0 and spiderlings_alive:
        ctx["_consume_brood_cd"] = 3
        return "Consume Brood", lambda e, p, d: _consume_brood_extra(ctx, elist), 1.0, 0

    # Standard attacks (enhanced)
    r = random.random()
    if r < 0.45:
        # Enhanced Venomous Strike
        def enhanced_venom(e, p, dmg):
            if dmg > 0:
                apply_poison(p, 8, 4)
                return "🧪 CONCENTRATED Vileheart toxins! (Poison 8 x 4)"
            return None
        return "Venomous Strike+", enhanced_venom, 1.0, 0
    elif r < 0.70:
        return "Web Shot+", _phase3_web_shot, 1.0, 0
    else:
        return "Acid Spray+", _phase3_acid_spray, 1.0, 0


def _phase3_web_shot(enemy, player, dmg):
    """Enhanced Web Shot: always slows, 25% stun."""
    msgs = []
    player.setdefault("active_debuffs", []).append({
        "type": "slow",
        "stat": "Dexterity",
        "value": -4,
        "remaining": 2,
        "source": "web_shot_p3",
    })
    msgs.append("🕸️ Heavy Webbing! -4 DEX for 2 turns!")
    if random.random() < 0.25:
        player["stunned"] = True
        msgs.append("💥 You are STUNNED!")
    return " | ".join(msgs) if msgs else None


def _phase3_acid_spray(enemy, player, dmg):
    """Enhanced Acid Spray: stronger corrosion."""
    party = _get_alive_party(player)
    for target in party:
        target.setdefault("active_debuffs", []).append({
            "type": "corrosion",
            "value": -0.25,
            "remaining": 2,
            "source": "acid_spray_p3",
        })
    return "🧪 Concentrated Acid! All party: -25% DEF for 2 turns!"


def _toxic_explosion_extra(enemy, player, dmg):
    """Toxic Explosion: detonate all poison stacks on all party members.

    Each poison stack deals its remaining total damage instantly.
    """
    party = _get_alive_party(player)
    total_detonated = 0
    for target in party:
        for debuff in list(target.get("active_debuffs", [])):
            if debuff.get("type") == "poison":
                remaining = debuff.get("remaining", 0)
                damage = debuff.get("damage", 0)
                detonate_dmg = remaining * damage
                target["current_hp"] = max(0, target.get("current_hp", 0) - detonate_dmg)
                total_detonated += detonate_dmg
                target["active_debuffs"].remove(debuff)
                c_print(f"  💥 {target.get('name', 'Someone')}'s poison DETONATES for {detonate_dmg} damage!")
    return f"☠️ TOXIC EXPLOSION! {total_detonated} total poison damage unleashed!"


def _consume_brood_extra(ctx, elist):
    """Consume Brood: sacrifice a spiderling to heal 15% max HP + gain +5 STR."""
    # Find a spiderling to sacrifice
    for e in elist:
        if e.get("key") in (SPIDERLING_KEY, VENOMWEAVER_KEY) and e["hp"] > 0:
            victim_name = e["name"]
            e["hp"] = 0
            boss = _get_boss(elist)
            if boss:
                heal = int(boss.get("max_hp", 350) * 0.15)
                boss["hp"] = min(boss.get("max_hp", 350), boss["hp"] + heal)
                boss.setdefault("active_buffs", []).append({
                    "type": "stat_buff",
                    "stat": "Strength",
                    "value": 5,
                    "remaining": 1,
                    "source": "consume_brood",
                })
                # Gain 1 Venom Overload stack for the sacrificed spiderling
                ctx["venom_overload"] = min(VENOM_OVERLOAD_CAP,
                                             ctx.get("venom_overload", 0) + 1)
                c_print(f"  🕷️ Broodmother consumes {victim_name}! +{heal} HP, +5 STR!")
                return f"🕷️ Consumed {victim_name}! +{heal} HP, +5 STR, +1 Venom Overload"
            return f"🕷️ Consumed {victim_name}!"
    return None


# ═══════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════

def combat_broodmother(player, floor=None, enemies=None):
    """Superboss: Broodmother Vileheart.

    Args:
        enemies: Optional pre-created enemy list for GUI mode state sharing.
    """
    if floor is None:
        loc = player.get("location", "")
        floor = player.get("city_floors", {}).get(loc, {}).get("floor")
    boss_key = BOSS_KEY

    # ── Create or locate boss ────────────────────────────────────────
    if enemies is None:
        boss = enemy_stats(boss_key, player)
        boss["max_hp"] = boss["hp"]
        enemies = [boss]
    else:
        boss = None
        for e in enemies:
            if e.get("key") == boss_key:
                e["max_hp"] = e["hp"]
                boss = e
                break
        if boss is None:
            boss = enemy_stats(boss_key, player)
            boss["max_hp"] = boss["hp"]
            enemies.append(boss)

    # ── Opening narration ────────────────────────────────────────────
    c_print("\n" + "=" * 60)
    c_print("The air grows thick with the stench of rot and venom.")
    c_print("Hundreds of tiny legs skitter in the darkness above and below.")
    c_print("A monstrous, bloated silhouette rises — crowned with thrashing")
    c_print("limbs and dripping fangs. Countless spider eyes gleam with")
    c_print("pure, instinctual hunger.")
    c_print("")
    c_print("The Broodmother's nest pulses with vile, living warmth.")
    c_print("Egg sacs line the walls. The floor is sticky with old webbing.")
    c_print("This creature has ruled this pit for centuries. It will not")
    c_print("give it up without a fight.")
    c_print(f"\n  Broodmother Vileheart — HP: {boss['hp']}")
    c_print("=" * 60)
    c_input("\nPress Enter to face the Broodmother...")

    # ── Context state ─────────────────────────────────────────────────
    context = {
        # Phase tracking
        "phase": 1,
        "phase2_triggered": False,
        "phase3_triggered": False,

        # Phase 2 retreat state
        "boss_escaped_data": None,
        "retreat_active": False,
        "retreat_timer": 0,
        "retreat_spawned": False,

        # Phase 3 mechanics
        "venom_overload": 0,
        "_toxic_explosion_cd": 4,
        "_consume_brood_cd": 3,
        "_death_throes_active": False,
        "_heart_pulse_used": False,
        "_heart_pulse_charging": False,
        "_heart_pulse_dmg_taken": 0,
        "_eggs_laid": 0,

        # General
        "boss_enraged_turns": 0,
    }

    # ═══════════════════════════════════════════════════════════════
    # HOOKS
    # ═══════════════════════════════════════════════════════════════

    def pre_player_hook(ctx, elist):
        """Phase transitions and spawn logic at round start."""
        boss = _get_boss(elist)
        if not boss:
            return

        hp_pct = boss["hp"] / boss.get("max_hp", 1)
        phase = ctx["phase"]

        # ── Phase 1 → 2 transition ──────────────────────────────────
        if phase == 1 and hp_pct <= PHASE1_HP and not ctx["phase2_triggered"]:
            ctx["phase"] = 2
            ctx["phase2_triggered"] = True
            ctx["retreat_active"] = True
            ctx["retreat_timer"] = 4
            ctx["retreat_spawned"] = False
            ctx["boss_escaped_data"] = boss
            elist.remove(boss)

            c_print("\n" + "-" * 40)
            c_print("The Broodmother SCREECHES — a sound that rattles your teeth!")
            c_print("She skitters UP the walls, vanishing into the darkness above.")
            c_print("")
            c_print("From every corner, egg sacs BURST open!")
            c_print("Four Spiderlings and a massive VENOMWEAVER descend!")
            c_print('"Protect the Brood!" their chittering seems to say.')
            c_print("-" * 40)
            c_input("\nPress Enter...")

            # Spawn minions
            spiderlings = _spawn_spiderling(player, count=4)
            venomweaver = _spawn_venomweaver(player)
            for s in spiderlings:
                elist.append(s)
            elist.append(venomweaver)
            ctx["retreat_spawned"] = True

            return

        # ── Phase 2 → 3 transition ──────────────────────────────────
        if phase == 2 and not ctx["retreat_active"] and hp_pct <= PHASE2_HP and not ctx["phase3_triggered"]:
            ctx["phase"] = 3
            ctx["phase3_triggered"] = True
            ctx["venom_overload"] = 0
            ctx["_toxic_explosion_cd"] = 2  # Will trigger sooner
            ctx["_consume_brood_cd"] = 3
            ctx["boss_enraged_turns"] = 999  # Permanent 2 actions

            c_print("\n" + "-" * 40)
            c_print("The Broodmother's vile heart PULSES with green light!")
            c_print("The walls of the nest THROB — alive, aware, and FURIOUS.")
            c_print("")
            c_print("Her venom grows darker. Her movements become frantic,")
            c_print("desperate. This is the last stand of a dying queen.")
            c_print('"The nest will NOT fall!" her shriek seems to promise.')
            c_print("-" * 40)
            c_input("\nPress Enter...")
            return

        # ── Phase 1: passive spiderling spawn ─────────────────────────
        if phase == 1 and not ctx["retreat_active"]:
            spider_count = _count_spiderlings(elist)
            if spider_count == 0:
                c_print("\n🕷️ Egg sacs along the walls begin to twitch...")
                for s in _spawn_spiderling(player, count=2):
                    elist.append(s)
                c_print("   Two Vileheart Spiderlings emerge!")
            elif spider_count < MAX_SPIDERLINGS and random.random() < 0.4:
                for s in _spawn_spiderling(player, count=1):
                    elist.append(s)
                c_print("\n🕷️ Another egg sac bursts! A Spiderling joins the fray!")

        # ── Phase 3: Death Throes below 15% ──────────────────────────
        if phase == 3 and hp_pct <= 0.15 and not ctx["_death_throes_active"]:
            ctx["_death_throes_active"] = True
            c_print("\n💀 The Broodmother's body begins to convulse uncontrollably!")
            c_print("   Vile energy radiates from her — DEATH THROES active!")

        # ── Phase 3: Heart Pulse at 10% ──────────────────────────────
        if (phase == 3 and hp_pct <= HEART_PULSE_THRESHOLD
                and not ctx["_heart_pulse_used"] and not ctx["_heart_pulse_charging"]):
            ctx["_heart_pulse_charging"] = True
            ctx["_heart_pulse_dmg_taken"] = 0
            ctx["_heart_pulse_hp_at_start"] = boss["hp"]  # Track HP for damage calc
            c_print("\n" + "!" * 50)
            c_print("The Broodmother's vile heart glows BRIGHT GREEN!")
            c_print("Pulses of venomous light fill the chamber.")
            c_print('She is channeling HEART PULSE — her final, desperate act!')
            c_print(f"  ⚡ Deal {HEART_PULSE_DMG_NEEDED}+ damage this turn to INTERRUPT!")
            c_print("!" * 50)

    def enemy_turn_hook(enemy, ctx, pl, p_con, defending, **kwargs):
        """AI-driven turn logic for all phases."""
        is_boss = (enemy.get("key") == BOSS_KEY)
        is_spiderling = (enemy.get("key") == SPIDERLING_KEY)
        is_venomweaver = (enemy.get("key") == VENOMWEAVER_KEY)

        # ── Broodmother's turn ──────────────────────────────────────
        if is_boss:
            phase = ctx["phase"]
            actions = 2 if (phase == 3 or ctx["boss_enraged_turns"] > 0) else 1

            # Phase 2: Boss is retreated — should not be in enemy list
            if ctx["retreat_active"]:
                return 0, True, None, 1.0, 0

            # Phase 3: Heart Pulse charging — resolve interrupt
            if ctx.get("_heart_pulse_charging"):
                return _resolve_heart_pulse(ctx, enemy, pl)

            # Select attack based on phase
            if phase == 1:
                name, extra, armor_mult, temp_str = _phase1_attack_selection(enemy, pl, ctx)
            elif phase == 3:
                name, extra, armor_mult, temp_str = _phase3_attack_selection(enemy, pl, ctx, kwargs.get("turn_order", []))
                # Apply Venom Overload damage bonus
                vo_stacks = ctx.get("venom_overload", 0)
                if vo_stacks > 0:
                    temp_str += vo_stacks  # +1 STR per stack
            else:
                name, extra, armor_mult, temp_str = "Basic Attack", None, 1.0, 0

            if name:
                c_print(f"\n  🕷️ {enemy['name']} uses {name}!")

            return actions, False, extra, armor_mult, temp_str

        # ── Spiderling turn ─────────────────────────────────────────
        elif is_spiderling:
            def spider_poison(e, p, dmg):
                if dmg > 0 and random.random() < 0.45:
                    apply_poison(p, 4, 3)
                    return f"🧪 {e['name']}'s bite is venomous! (Poison 4 x 3)"
                return None
            return 1, False, spider_poison, 1.0, 0

        # ── Venomweaver turn ────────────────────────────────────────
        elif is_venomweaver:
            r = random.random()
            if r < 0.55:
                # Venomous Bite: stronger poison
                def venom_bite(e, p, dmg):
                    if dmg > 0:
                        apply_poison(p, 6, 4)
                        return f"🧪 {e['name']}'s bite injects potent venom! (Poison 6 x 4)"
                    return None
                c_print(f"\n  🕸️ {enemy['name']} uses Venomous Bite!")
                return 1, False, venom_bite, 1.0, 0
            else:
                # Web Wrap: stun a target
                def web_wrap(e, p, dmg):
                    if random.random() < 0.60:
                        p["stunned"] = True
                        return f"🕸️ {e['name']} wraps {p.get('name', 'You')} in webbing! STUNNED!"
                    return None
                c_print(f"\n  🕸️ {enemy['name']} uses Web Wrap!")
                return 1, False, web_wrap, 1.0, 0

        # Fallback
        return 1, False, None, 1.0, 0

    def _resolve_heart_pulse(ctx, boss, player):
        """Resolve Heart Pulse: check if interrupted or cast."""
        hp_start = ctx.get("_heart_pulse_hp_at_start", boss["hp"])
        dmg_taken = max(0, hp_start - boss["hp"])
        ctx["_heart_pulse_charging"] = False

        if dmg_taken >= HEART_PULSE_DMG_NEEDED:
            c_print("\n  ⚡ The Broodmother's heart SPASMS! The pulse scatters into nothing!")
            c_print("  INTERRUPTED! She is STUNNED and loses all Venom Overload!")
            boss["stunned"] = True
            ctx["venom_overload"] = 0
            ctx["_heart_pulse_used"] = True
        else:
            c_print("\n  💚 The heart pulse DETONATES!")
            c_print("  A wave of pure venom washes over your party!")
            party = _get_alive_party(player)
            total_dmg = 0
            for target in party:
                dmg = random.randint(50, 70)
                name = target.get("name", "Someone")
                target["current_hp"] = max(0, target.get("current_hp", 0) - dmg)
                total_dmg += dmg
                c_print(f"    {name} takes {dmg} poison damage!")
                apply_poison(target, 8, 5)  # Max poison stacks
                c_print(f"    {name} is MAXIMALLY POISONED! (8 x 5)")
            c_print(f"  Total devastation: {total_dmg} damage dealt!")
            ctx["_heart_pulse_used"] = True

        return 0, True, None, 1.0, 0

    def post_round_hook(ctx, elist):
        """End-of-round mechanics for all phases."""
        phase = ctx["phase"]
        boss = _get_boss(elist)

        # ── Phase 2: retreat timer ──────────────────────────────────
        if ctx["retreat_active"]:
            ctx["retreat_timer"] -= 1
            timer = ctx["retreat_timer"]

            # Check if all minions dead
            minions_alive = _count_spiderlings(elist) > 0

            if not minions_alive or timer <= 0:
                # Broodmother returns
                if not minions_alive and timer > 0:
                    c_print("\n[GIMMICK] You slaughtered the swarm!")
                else:
                    c_print("\n[GIMMICK] Time's up! The Broodmother is done waiting!")

                c_print("Broodmother Vileheart CRASHES down from the ceiling, ENRAGED!")
                c_print("The impact sends shockwaves through the nest!")
                boss_data = ctx["boss_escaped_data"]
                if boss_data:
                    # Impact damage to party
                    party = _get_alive_party(player)
                    for target in party:
                        dmg = 10
                        name = target.get("name", "Someone")
                        target["current_hp"] = max(0, target.get("current_hp", 0) - dmg)
                        c_print(f"  💥 {name} takes {dmg} impact damage!")

                    elist.append(boss_data)
                    ctx["boss_escaped_data"] = None

                ctx["retreat_active"] = False
                ctx["boss_enraged_turns"] = 999  # Permanent enrage for rest of phase 2

            else:
                # Broodmother attacks from ceiling
                c_print(f"\n🕷️ Broodmother watches from above... ({timer} turns remain)")
                c_print("   She prepares to strike from the darkness!")
                # Execute a ceiling attack against the party
                _execute_ceiling_attack(ctx, elist)

        # ── Phase 3: tick cooldowns ─────────────────────────────────
        if phase == 3 and not ctx["retreat_active"]:
            ctx["_toxic_explosion_cd"] = max(0, ctx.get("_toxic_explosion_cd", 0) - 1)
            ctx["_consume_brood_cd"] = max(0, ctx.get("_consume_brood_cd", 0) - 1)

            # Death Throes
            if ctx.get("_death_throes_active"):
                c_print("\n💀 DEATH THROES: Vile energy pulses from the Broodmother!")
                party = _get_alive_party(player)
                for target in party:
                    name = target.get("name", "Someone")
                    target["current_hp"] = max(0, target.get("current_hp", 0) - 10)
                    c_print(f"   {name} takes 10 unavoidable poison damage!")

        # ── Phase 1: boss enraged timer ─────────────────────────────
        if ctx["boss_enraged_turns"] > 0 and ctx["boss_enraged_turns"] < 900:
            ctx["boss_enraged_turns"] -= 1

    def _execute_ceiling_attack(ctx, elist):
        """Execute a ceiling attack from the retreated Broodmother."""
        boss_data = ctx.get("boss_escaped_data")
        if not boss_data:
            return

        party = _get_alive_party(player)
        if not party:
            return

        target = random.choice(party)
        p_con = _get_actor_con(target, player, compute_player_stats(player)[1])

        name, extra_fn, armor_mult, temp_str = _ceiling_attack_selection(
            boss_data, target, ctx, elist
        )
        c_print(f"\n  🕷️ From above: {name}!")

        # Deal base damage from ceiling
        str_mod = boss_data.get("str_mod", 8)
        is_defending = False  # Can't defend vs ceiling attacks
        block = p_con // 2
        dmg = max(0, random.randint(3, 8) + str_mod - block)
        target["current_hp"] = max(0, target.get("current_hp", 0) - dmg)
        c_print(f"    {target.get('name', 'Someone')} takes {dmg} damage!")

        # Apply extra effect
        if extra_fn:
            msg = extra_fn(boss_data, player, dmg)
            if msg:
                c_print(f"    {msg}")

    def custom_hud_hook(ctx, elist):
        """Display phase info and mechanical state above the combat HUD."""
        phase = ctx["phase"]
        boss = _get_boss(elist)

        # Phase label
        phase_labels = {
            1: "Phase 1: The Nest Awakens",
            2: "Phase 2: The Hatchling Swarm",
            3: "Phase 3: Vileheart's Desperation",
        }
        label = phase_labels.get(phase, f"Phase {phase}")

        extras = []
        if ctx["retreat_active"]:
            extras.append(f"Broodmother RETREATED ({ctx['retreat_timer']}t)")
        if phase == 2 and ctx["boss_enraged_turns"] > 0:
            extras.append("ENRAGED")
        if phase == 3:
            vo = ctx.get("venom_overload", 0)
            if vo > 0:
                extras.append(f"Venom Overload: {vo} stacks (+{vo * 3}% dmg)")
            tc = ctx.get("_toxic_explosion_cd", 0)
            extras.append(f"Toxic Explosion in {tc}t")
        if ctx.get("_heart_pulse_charging"):
            extras.append("⚠️ HEART PULSE CHARGING!")

        extra_str = " | ".join(extras) if extras else ""
        c_print(f"\n  {label}")
        if extra_str:
            c_print(f"  {extra_str}")

        print_combat_hud(player, elist, header="Superboss: Broodmother Vileheart")

    # ═══════════════════════════════════════════════════════════════
    # RUN COMBAT
    # ═══════════════════════════════════════════════════════════════

    result = superboss_combat_loop(
        player, enemies, floor, "Broodmother Vileheart", context,
        pre_player_hook=pre_player_hook,
        custom_hud_hook=custom_hud_hook,
        enemy_turn_hook=enemy_turn_hook,
        post_round_hook=post_round_hook,
    )

    # ═══════════════════════════════════════════════════════════════
    # POST-COMBAT (victory)
    # ═══════════════════════════════════════════════════════════════

    if result == "victory":
        # Guard: only award loot once per save
        if not player.get("boss_defeated_broodmother"):
            c_print("\n" + "=" * 60)
            c_print("The Broodmother lets out one final, shuddering screech.")
            c_print("Her massive body crumples. The nest falls silent.")
            c_print("")
            c_print("The egg sacs stop pulsing. The skittering in the walls")
            c_print("fades away. For the first time in centuries, this pit")
            c_print("is still.")
            c_print("")
            c_print("At the center of her thorax, something glints in the dark —")
            c_print("her crystallized heart, still warm, still pulsing faintly.")
            c_print("You reach out and claim it.")
            c_print("=" * 60)

            # Grant loot
            from resources.items import build_item
            from inventory_ui import prompt_acquire_item
            pendant = build_item("vileheart_pendant", rarity="unique")
            c_print(f"\n  🎁 Received: {pendant['name']}!")
            c_print(f"    A dark pendant that still thrums with venomous life.")
            c_print(f"    Physical attacks have a chance to poison foes.")
            prompt_acquire_item(player, pendant)

            # Set defeated flag AFTER awarding loot
            player["boss_defeated_broodmother"] = True

    return result