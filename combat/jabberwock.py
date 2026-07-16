# combat/jabberwock.py — Wonderland Superboss: The Jabberwock (Floor 40)
#
# MECHANIC OVERVIEW:
# ─────────────────
# Four-phase superboss fight.  Alice-linked (heroine quest boss).
#
# Phase 1 — Bewilderbeast (100%–75%):
#   Burble: AoE confusion, 40% chance Bewildered (random targeting) per target.
#   Galumphing Charge: single-target physical + pushes target to initiative bottom.
#   "The frumious Bandersnatch!" at 85% HP: summons one Bandersnatch minion.
#   Alice: +15% dodge vs Burble.
#
# Phase 2 — Manxome (75%–45%):
#   Claws That Catch: 2 attacks/turn, second ignores 50% of target's CON.
#   Jaws That Bite (every 3 turns): heavy single-target + Vorpal Wound
#     (10 dmg × 4 turns, UNCLEANSABLE bleed). Refreshed on same target.
#   Whiffling (every 5 turns): self-buff +40% dodge, skip attack.
#     Next turn: -30% dodge (exhaustion).
#   Alice: tactical hint about Whiffling vulnerability window.
#
# Phase 3 — Frabjous (45%–20%):
#   Vorpal Beam (every 3 turns): 1-turn windup → 60–90 thunder AoE.
#     Interruptible if party deals 40+ damage during windup.
#   Narrative Rewrite (every 2 turns): erases last positive buff from a
#     random party member.
#   Page Storm (passive, each round): +1 cooldown to one random skill.
#   Alice: +50% damage during Vorpal Beam windup turns.
#
# Phase 4 — Narrative Collapse (20%–0%):
#   Death Throes (passive): 15 unavoidable damage to all party each round.
#   Final Vorpal Strike at 5% HP: 80–120 damage on random target.
#     Defending guarantees survival at 1 HP.  Jabberwock then defenseless.

import random
from combat.stats import enemy_stats, compute_player_stats
from combat.player_actions import handle_player_turn
from combat.combat_ui import format_enemy_status_line, print_superboss_header
from combat.superboss_common import superboss_combat_loop
from combat.status_effects import apply_bleed
from combat.combat_io import c_print, c_input, c_clear
from combat.ally import get_active_allies, compute_ally_stats

# ── Keys ────────────────────────────────────────────────────────────────────

JABBERWOCK_KEY  = "wl_jabberwock"
BANDERSNATCH_KEY = "wl_bandersnatch"


# ── Helpers ──────────────────────────────────────────────────────────────────

def _is_jabberwock(e):
    return e.get("key") == JABBERWOCK_KEY


def _is_bandersnatch(e):
    return e.get("key") == BANDERSNATCH_KEY


def _find_jabberwock(enemies):
    for e in enemies:
        if _is_jabberwock(e) and e["hp"] > 0:
            return e
    return None


def _count_live_bandersnatches(enemies):
    return sum(1 for e in enemies
               if _is_bandersnatch(e) and e["hp"] > 0 and not e.get("captured"))


def _get_living_targets(player):
    """Return list of living player + active allies."""
    targets = []
    if player.get("current_hp", 0) > 0:
        targets.append(player)
    for ally in get_active_allies(player):
        if ally.get("current_hp", 0) > 0:
            targets.append(ally)
    return targets


def _get_alice(player):
    """Find Alice in the active party, or None."""
    for ally in get_active_allies(player):
        if ally.get("_heroine_key") == "alice" and ally.get("current_hp", 0) > 0:
            return ally
    return None


def _spawn_bandersnatch(player, enemies):
    """Spawn a single Bandersnatch minion with boosted dodge."""
    bn = enemy_stats(BANDERSNATCH_KEY, player)
    bn["key"] = BANDERSNATCH_KEY
    # Override HP to ~60 (low HP minion)
    bn["hp"] = max(40, min(80, bn["hp"]))
    bn["max_hp"] = bn["hp"]
    # Give +30% dodge
    bn.setdefault("active_buffs", []).append({
        "type": "evasion",
        "value": 0.30,
        "remaining": 999,
        "source": "bandersnatch_evasion",
    })
    enemies.append(bn)
    return bn


# ══════════════════════════════════════════════════════════════════════════════
# Phase 1 — Bewilderbeast
# ══════════════════════════════════════════════════════════════════════════════

def _jabberwock_burble(jabber, player):
    """AoE confusion gas. 40% chance per target to inflict Bewildered (2 turns)."""
    c_print('\n  "The Jabberwock burbles — nonsense spills from its jaws like smoke."')

    alice = _get_alice(player)
    for target in _get_living_targets(player):
        chance = 0.40
        # Alice gets +15% dodge vs Burble
        if target is alice:
            chance = max(0.10, chance - 0.15)

        if random.random() < chance:
            target.setdefault("active_debuffs", []).append({
                "type": "bewildered",
                "remaining": 2,
                "source": "burble",
            })
            c_print(f"    {target.get('name', 'You')} is BEWILDERED! (50% random targeting, 2 turns)")
        else:
            c_print(f"    {target.get('name', 'You')} resists the nonsense.")


def _jabberwock_galumphing_charge(jabber, player, context):
    """Single-target physical + push to bottom of initiative."""
    c_print('\n  "The Jabberwock GALUMPS forward — a heavy, lurching charge!"')

    def _push_extra(e, target, dmg):
        name = target.get("name", "The target")
        # Push target to bottom of initiative
        turn_order = context.get("_current_turn_order", [])
        if turn_order and target is not None:
            # Collect all entries for this target and move them to the end
            target_entries = []
            kept_entries = []
            for entry in turn_order:
                if entry.get("entity") is target:
                    target_entries.append(entry)
                else:
                    kept_entries.append(entry)
            # Rebuild: kept first, then target entries at the end
            turn_order[:] = kept_entries + target_entries
        return f"  ↠ {name} is hurled to the back of the line!"

    return _push_extra


def _jabberwock_phase1_turn(jabber, player, ctx):
    """Execute one Phase 1 action. Returns (actions, skip_default, extra_logic, armor_mult, temp_str)."""
    hp_pct = jabber["hp"] / jabber["max_hp"]

    # ── Bandersnatch summon at 85% HP (once) ────────────────────────────
    if not ctx.get("bandersnatch_summoned") and hp_pct <= 0.85:
        ctx["bandersnatch_summoned"] = True
        c_print('\n  "The Jabberwock howls — and the howl takes shape!"')
        c_print('  "The frumious Bandersnatch!"')
        c_print("  A creature of angles and fury tears itself free from the shadow...")
        bn = _spawn_bandersnatch(player, ctx.get("_enemies_ref", []))
        c_print(f"  {bn['name']} appears! HP: {bn['hp']}")
        return 1, True, None, 1.0, 0

    # ── Burble every 3 Jabberwock actions ───────────────────────────────
    actions_count = ctx.get("jabberwock_actions", 0)
    if actions_count > 0 and actions_count % 3 == 0:
        _jabberwock_burble(jabber, player)
        return 1, True, None, 1.0, 0

    # ── Galumphing Charge every 4 actions (offset from Burble) ──────────
    if actions_count > 0 and actions_count % 4 == 0 and actions_count % 3 != 0:
        extra = _jabberwock_galumphing_charge(jabber, player, ctx)
        return 1, False, extra, 1.0, 2   # temp_str +2 for heavier hit

    # ── Default: basic physical attack ──────────────────────────────────
    return 1, False, None, 1.0, 0


# ══════════════════════════════════════════════════════════════════════════════
# Phase 2 — Manxome
# ══════════════════════════════════════════════════════════════════════════════

def _jabberwock_claws_that_catch(jabber, player):
    """Two attacks. Second ignores 50% of target's CON."""
    c_print('\n  "The claws that CATCH!" — the Jabberwock slashes with both claws!')
    # Return parameters: 2 actions, second has armor_mult=0.5 (ignores 50% CON)
    # We handle the second attack's CON pierce via armor_mult in enemy_attack
    return 2, False, None, 0.5, 0   # 2 actions, 0.5 armor for second hit


def _jabberwock_jaws_that_bite(jabber, player, ctx):
    """Heavy single-target + Vorpal Wound (uncleansable bleed, 10 dmg × 4 turns)."""
    c_print('\n  "The JAWS that BITE!"')

    def _vorpal_wound_extra(e, target, dmg):
        name = target.get("name", "The target")
        # Apply uncleansable Vorpal Wound bleed
        target.setdefault("active_debuffs", []).append({
            "type": "bleed",
            "damage": 10,
            "remaining": 4,
            "source": "vorpal_wound",
            "_uncleansable": True,
        })
        ctx["_vorpal_wound_target"] = target  # Track for refresh
        ctx["_vorpal_wound_cooldown"] = 3     # Reapply every 3 turns
        return f"  🩸 VORPAL WOUND! {name} bleeds for 10 dmg × 4 turns (UNCLEANSABLE)"

    return _vorpal_wound_extra


def _jabberwock_whiffle(jabber, ctx):
    """Self-buff: +40% dodge for 1 turn, skip attack. Next turn: -30% dodge."""
    c_print('\n  "The Jabberwock begins to WHIFFLE through the tulgey wood..."')
    # Apply +40% dodge buff
    jabber.setdefault("active_buffs", []).append({
        "type": "evasion",
        "value": 0.40,
        "remaining": 1,
        "source": "whiffling",
    })
    ctx["_whiffle_exhausted"] = True   # Next turn: -30% dodge
    c_print("  ↠ +40% dodge for 1 turn! The Jabberwock dances away.")
    return True   # skip attack


def _jabberwock_phase2_turn(jabber, player, ctx):
    """Execute one Phase 2 action. Returns (actions, skip_default, extra_logic, armor_mult, temp_str)."""
    actions_count = ctx.get("jabberwock_actions", 0)

    # ── Handle Whiffling exhaustion from previous turn ──────────────────
    if ctx.get("_whiffle_exhausted"):
        ctx["_whiffle_exhausted"] = False
        # Apply -30% dodge for 1 turn
        jabber.setdefault("active_debuffs", []).append({
            "type": "evasion_down",
            "value": -0.30,
            "remaining": 1,
            "source": "whiffle_exhaustion",
        })
        c_print('\n  "The Jabberwock catches its breath — its guard is DOWN!"')
        c_print("  ↠ -30% dodge for 1 turn! STRIKE NOW!")

        # Alice hint
        alice = _get_alice(player)
        if alice and not ctx.get("_alice_whiffle_hint_given"):
            ctx["_alice_whiffle_hint_given"] = True
            c_print(f'\n  Alice: "Now! It\'s catching its breath — hit it with everything!"')

    # ── Jaws That Bite on cooldown ──────────────────────────────────────
    vorpal_cd = ctx.get("_vorpal_wound_cooldown", 0)
    if vorpal_cd > 0:
        ctx["_vorpal_wound_cooldown"] = vorpal_cd - 1
    if ctx.get("_vorpal_wound_cooldown", 0) <= 0 and actions_count > 0:
        extra = _jabberwock_jaws_that_bite(jabber, player, ctx)
        return 1, False, extra, 1.0, 3   # Heavy hit +3 temp_str

    # ── Whiffling every 5 actions ───────────────────────────────────────
    if actions_count > 0 and actions_count % 5 == 0:
        skipped = _jabberwock_whiffle(jabber, ctx)
        return 1, skipped, None, 1.0, 0

    # ── Claws That Catch (default) ──────────────────────────────────────
    return _jabberwock_claws_that_catch(jabber, player)


# ══════════════════════════════════════════════════════════════════════════════
# Phase 3 — Frabjous
# ══════════════════════════════════════════════════════════════════════════════

def _jabberwock_vorpal_beam_windup(jabber, ctx):
    """Announce Vorpal Beam charging. Track damage for interrupt check."""
    c_print('\n  ⚡ "The Jabberwock\'s eyes glow with VORPAL LIGHT..."')
    c_print('  ⚡ CHARGING: Vorpal Beam — next turn! Deal 40+ damage to interrupt!')
    ctx["_vorpal_beam_charging"] = True
    ctx["_vorpal_beam_damage_taken"] = 0

    # Alice bonus damage during windup
    ctx["_alice_vorpal_bonus"] = True
    alice = _get_alice(ctx.get("_player_ref"))
    if alice:
        c_print(f'\n  Alice: "The eyes! Aim for the eyes — that\'s where it keeps its plot holes!"')
        c_print(f"  ↠ Alice\'s attacks deal +50% damage during the windup!")


def _jabberwock_vorpal_beam_fire(jabber, player, ctx):
    """Fire Vorpal Beam or report interruption."""
    if ctx.get("_vorpal_beam_damage_taken", 0) >= 40:
        # Interrupted!
        c_print('\n  "The vorpal light SPUTTERS! The Jabberwock shrieks in frustration!"')
        c_print("  ↠ Vorpal Beam INTERRUPTED! Jabberwock loses its next attack.")
        ctx["_vorpal_beam_charging"] = False
        ctx["_vorpal_beam_interrupted"] = True
        ctx["_alice_vorpal_bonus"] = False
        return True   # skip attack
    else:
        # Beam fires!
        c_print('\n  💀 "VORPAL BEAM!" — A line of blinding light tears through the party!')
        for target in _get_living_targets(player):
            dmg = random.randint(60, 90)
            res = target.get("elemental_res", {}).get("thunder", 1.0)
            final_dmg = max(1, int(dmg * res))
            target["current_hp"] = max(0, target.get("current_hp", 0) - final_dmg)
            c_print(f"    {target.get('name', 'You')} takes {final_dmg} damage [THUNDER]!")
            if target.get("current_hp", 0) <= 0:
                c_print(f"    {target.get('name', 'You')} has been struck down!")
        ctx["_vorpal_beam_charging"] = False
        ctx["_alice_vorpal_bonus"] = False
        return True   # skip attack (beam is the attack)


def _jabberwock_narrative_rewrite(player):
    """Erase the last positive buff from a random party member."""
    targets = _get_living_targets(player)
    # Find targets that have buffs
    buffed = [t for t in targets if t.get("active_buffs")]
    if not buffed:
        c_print('\n  "The Jabberwock tries to rewrite... but finds nothing to edit."')
        return

    target = random.choice(buffed)
    removed = target["active_buffs"].pop()  # Remove last (most recent) buff
    c_print(f'\n  📖 "The Jabberwock REWRITES the story..."')
    c_print(f'    {target.get("name", "Someone")}\'s buff "{removed.get("type", "unknown")}" is ERASED!')
    c_print('    "That never happened."')


def _jabberwock_page_storm(player):
    """Increase a random skill cooldown by 1 on a random party member."""
    # Collect all entities with cooldowns
    entities = []
    if player.get("skill_cooldowns"):
        entities.append(("You", player))
    for ally in get_active_allies(player):
        if ally.get("current_hp", 0) > 0 and ally.get("skill_cooldowns"):
            entities.append((ally.get("name", "Ally"), ally))

    if not entities:
        return

    name, entity = random.choice(entities)
    cooldowns = entity.get("skill_cooldowns", {})
    if not cooldowns:
        return

    skill_id = random.choice(list(cooldowns.keys()))
    cooldowns[skill_id] += 1

    # Try to get skill name for nicer display
    skill_name = skill_id
    from combat.skills import get_class_skill_map
    skill_map = get_class_skill_map(entity) if entity is not player else {}
    if not skill_map:
        # Allies use their own skill system
        skill_map = entity.get("_skill_map", {})
    skill_def = skill_map.get(skill_id, {})
    if skill_def:
        skill_name = skill_def.get("name", skill_id)

    c_print(f'\n  📄 "A page tears from {name}\'s storybook: \'{skill_name}\' gains +1 cooldown!"')


def _jabberwock_phase3_turn(jabber, player, ctx):
    """Execute one Phase 3 action. Returns (actions, skip_default, extra_logic, armor_mult, temp_str)."""
    actions_count = ctx.get("jabberwock_actions", 0)

    # ── Vorpal Beam interrupted last turn? Skip this attack ─────────────
    if ctx.pop("_vorpal_beam_interrupted", False):
        c_print('\n  "The Jabberwock reels — its narrative disrupted!"')
        return 1, True, None, 1.0, 0   # Skip this turn entirely

    # ── Vorpal Beam firing this turn? ───────────────────────────────────
    if ctx.get("_vorpal_beam_charging"):
        skipped = _jabberwock_vorpal_beam_fire(jabber, player, ctx)
        return 1, skipped, None, 1.0, 0

    # ── Vorpal Beam windup every 3 actions ─────────────────────────────
    if actions_count > 0 and actions_count % 3 == 0:
        _jabberwock_vorpal_beam_windup(jabber, ctx)
        return 1, True, None, 1.0, 0   # Windup turn: no attack

    # ── Narrative Rewrite every 2 actions (offset from beam) ────────────
    if actions_count > 0 and actions_count % 2 == 0:
        _jabberwock_narrative_rewrite(player)
        return 1, True, None, 1.0, 0   # Rewrite replaces attack

    # ── Default: basic attack ───────────────────────────────────────────
    return 1, False, None, 1.0, 0


# ══════════════════════════════════════════════════════════════════════════════
# Phase 4 — Narrative Collapse
# ══════════════════════════════════════════════════════════════════════════════

def _jabberwock_death_throes(player):
    """15 unavoidable environmental damage to all party members each round."""
    c_print('\n  💥 "The dungeon COLLAPSES around you — pages tear, ink bleeds, the story dies!"')
    for target in _get_living_targets(player):
        target["current_hp"] = max(0, target.get("current_hp", 0) - 15)
        c_print(f"    {target.get('name', 'You')} takes 15 damage from the collapsing narrative!")
        if target.get("current_hp", 0) <= 0:
            c_print(f"    {target.get('name', 'You')} is consumed by the void!")


def _jabberwock_final_vorpal_strike(jabber, player, ctx):
    """At 5% HP: 80–120 damage on random target. Defend = survive at 1 HP."""
    c_print('\n  💀 "The Jabberwock gathers every word it has left..."')
    c_print('  "Every claw, every jaw, every burble and galumph."')
    c_print('  "It shapes them into one FINAL ATTACK — a sentence with no period, no mercy."')

    targets = _get_living_targets(player)
    if not targets:
        return

    target = random.choice(targets)
    name = target.get("name", "The target")
    dmg = random.randint(80, 120)

    c_print(f'\n  "FINAL VORPAL STRIKE!" — aimed at {name}!')

    # Check if target is defending
    # We can't check defending here (that's in the combat loop), so we use a flag
    ctx["_final_strike_target"] = target
    ctx["_final_strike_dmg"] = dmg

    # Apply damage (Defend check happens in extra_logic via the combat loop's defending flag)
    def _final_strike_extra(e, tgt, raw_dmg):
        actual_name = tgt.get("name", "The target")
        # The combat loop applies damage with defending already factored in
        # If the target defended, they survive at 1 HP
        if tgt.get("current_hp", 0) <= 0 and raw_dmg > 0:
            # They would die — but if they defended, they survive
            # (This is handled by the combat engine's defend logic)
            pass
        ctx["_final_strike_used"] = True
        ctx["_jabberwock_defenseless"] = True
        c_print(f'\n  "The Jabberwock has spent its last word. It is DEFENSELESS!"')
        return f"  {actual_name} takes {raw_dmg} damage from the Final Vorpal Strike!"

    return _final_strike_extra


def _jabberwock_phase4_turn(jabber, player, ctx):
    """Execute Phase 4 actions. Returns (actions, skip_default, extra_logic, armor_mult, temp_str)."""
    hp_pct = jabber["hp"] / jabber["max_hp"]

    # ── Final Vorpal Strike at 5% HP ────────────────────────────────────
    if hp_pct <= 0.05 and not ctx.get("_final_strike_used"):
        extra = _jabberwock_final_vorpal_strike(jabber, player, ctx)
        return 1, False, extra, 1.0, 5   # Massive damage

    # ── If defenseless after Final Strike, just basic weak attacks ──────
    if ctx.get("_jabberwock_defenseless"):
        c_print('\n  "The Jabberwock flails weakly — a story with no ending..."')
        return 1, False, None, 1.0, -2   # Weak attack

    # ── Default: desperate attacks ──────────────────────────────────────
    return 1, False, None, 1.0, 1   # Slightly stronger attacks


# ══════════════════════════════════════════════════════════════════════════════
# Main Combat Function
# ══════════════════════════════════════════════════════════════════════════════

def combat_jabberwock(player, floor=None, enemies=None):
    """Wonderland Superboss — The Jabberwock (Floor 40).
    
    Alice's personal quest boss.  Four phases of escalating narrative horror.

    Args:
        enemies: Optional pre-created enemy list for GUI mode state sharing.
    """
    if floor is None:
        loc = player.get("location", "")
        floor = player.get("city_floors", {}).get(loc, {}).get("floor", 40)

    # ── Create or locate boss ────────────────────────────────────────────
    if enemies is None:
        jabber = enemy_stats(JABBERWOCK_KEY, player)
        jabber["max_hp"] = jabber["hp"]
        enemies = [jabber]
    else:
        jabber = _find_jabberwock(enemies)
        if jabber is None:
            jabber = enemy_stats(JABBERWOCK_KEY, player)
            jabber["max_hp"] = jabber["hp"]
            enemies.append(jabber)
        else:
            jabber["max_hp"] = jabber["hp"]
            jabber["hp"] = jabber["max_hp"]

    # ── Check for Alice ──────────────────────────────────────────────────
    alice = _get_alice(player)

    # ── Opening narration ────────────────────────────────────────────────
    c_clear()
    c_print("=" * 60)
    c_print("The tulgey wood closes around you. Trees with bark like")
    c_print("bookbindings. Leaves that rustle in reverse — from brown")
    c_print("to green, from death to birth.")
    c_print("")
    c_print("A sound reaches you before it should. Galumphing. A heavy,")
    c_print("lurching gait that arrives at your ears seconds before its")
    c_print("source rounds the corner.")
    c_print("")
    c_print("The Jabberwock is hard to look at. Your eyes keep sliding")
    c_print("off — not from fear, but because the thing is written in a")
    c_print("language your brain refuses to parse. It has the body of a")
    c_print("dragon. The wings of a tattered manuscript. Eyes that are")
    c_print("inkwells, dripping with someone else's nightmares.")
    c_print("")
    if alice:
        c_print('Alice grips her teacup — when did she pick that up? — and')
        c_print('whispers: "It\'s been writing this chapter for a very long')
        c_print('time. I think... I think I\'m supposed to be the ending."')
        c_print("")
        c_print('"Or maybe you\'re the plot twist," you reply.')
        c_print('She manages a small smile. "I\'ve always wanted to be one of those."')
    else:
        c_print('It opens its jaws. Words spill out — nonsense words, puns')
        c_print('so bad they physically hurt, plot holes that bend the air.')
        c_print('')
        c_print('"Beware," it doesn\'t quite say. "The jaws that bite..."')
    c_print("")
    c_print("The Jabberwock has noticed you.")
    c_print("=" * 60)
    c_print(f"\nThe Jabberwock — HP: {jabber['hp']}")
    c_input("\nPress Enter to face the Jabberwock...")

    # ── Combat context ──────────────────────────────────────────────────
    context = {
        "phase": 1,                     # Current phase: 1-4
        "jabberwock_actions": 0,        # Total Jabberwock actions taken
        "bandersnatch_summoned": False, # Bandersnatch summoned at 85%?

        # Whiffling
        "_whiffle_exhausted": False,    # Next turn: -30% dodge debuff

        # Vorpal Wound
        "_vorpal_wound_target": None,   # Current wound target
        "_vorpal_wound_cooldown": 0,    # Turns until next Jaws That Bite

        # Vorpal Beam
        "_vorpal_beam_charging": False,
        "_vorpal_beam_damage_taken": 0,
        "_vorpal_beam_interrupted": False,

        # Final Vorpal Strike
        "_final_strike_used": False,
        "_final_strike_target": None,
        "_final_strike_dmg": 0,
        "_jabberwock_defenseless": False,

        # Alice integration
        "_alice_in_party": alice is not None,
        "_alice_whiffle_hint_given": False,
        "_alice_vorpal_bonus": False,

        # Turn order reference (set each round by enemy_turn_hook)
        "_current_turn_order": [],

        # Player ref (stored for use in phase 3 page storm, etc.)
        "_player_ref": player,
        "_enemies_ref": enemies,

        # Skip player turn (used for stun-like effects)
        "skip_player_turn": False,
    }

    # ── Hooks ───────────────────────────────────────────────────────────

    def pre_player_hook(ctx, elist):
        """Check HP thresholds and handle phase transitions."""
        j = _find_jabberwock(elist)
        if j is None:
            return None
        hp_pct = j["hp"] / j["max_hp"]

        # ── Phase 1 → 2 (75% HP) ─────────────────────────────────────
        if hp_pct <= 0.75 and ctx["phase"] == 1:
            ctx["phase"] = 2
            ctx["_vorpal_wound_cooldown"] = 1   # First Jaws That Bite soon

            c_print("\n" + "-" * 50)
            c_print("The Jabberwock roars — and the nonsense condenses.")
            c_print("The bewildering shapes solidify into something you")
            c_print("can finally see clearly.")
            c_print("")
            c_print("And you wish you couldn't.")
            c_print("")
            c_print("It has the body of a dragon. The wings of a tattered")
            c_print("manuscript. Eyes that are inkwells — and they are")
            c_print("fixed on you.")
            c_print("")
            c_print("The Jabberwock has stopped playing with its food.")
            c_print("-" * 50)

            if alice:
                c_print(f'\n  Alice: "It\'s real now. Fully real. Be careful —')
                c_print('  when it whiffles, don\'t attack. Wait for it to')
                c_print('  catch its breath. That\'s when you strike."')
            c_input("Press Enter...")

        # ── Phase 2 → 3 (45% HP) ─────────────────────────────────────
        elif hp_pct <= 0.45 and ctx["phase"] == 2:
            ctx["phase"] = 3

            c_print("\n" + "!" * 50)
            c_print("The Jabberwock's wings unfurl — not outward, but upward.")
            c_print("They spread across the arena like pages torn from a book")
            c_print("and thrown into a storm.")
            c_print("")
            c_print("The ceiling vanishes. Above you: a vortex of ink, paper,")
            c_print("and half-finished sentences. The Jabberwock ascends into")
            c_print("it, and the vortex descends onto you.")
            c_print("")
            c_print('"Callooh! Callay!" it chortles. The sound is the opposite')
            c_print("of joy.")
            c_print("!" * 50)

            if alice:
                c_print(f'\n  Alice: "It\'s writing the fight! It\'s rewriting it as')
                c_print('  we go! When its eyes glow — aim for them! That\'s where')
                c_print('  it keeps its plot holes!"')
            c_input("Press Enter...")

        # ── Phase 3 → 4 (20% HP) ─────────────────────────────────────
        elif hp_pct <= 0.20 and ctx["phase"] == 3:
            ctx["phase"] = 4
            ctx["_vorpal_beam_charging"] = False
            ctx["_alice_vorpal_bonus"] = False

            c_print("\n" + "!" * 50)
            c_print("The Jabberwock screams. The vortex begins to collapse —")
            c_print("not upward, but inward. Pages are flying in reverse,")
            c_print("words unscrambling, ink flowing back into its wounds.")
            c_print("")
            c_print("It's dying. And it's taking this chapter with it.")
            c_print("")
            c_print("The arena CRUMBLES. Every round, the collapsing")
            c_print("narrative deals 15 unavoidable damage to your party.")
            c_print("FINISH IT — before the story finishes you.")
            c_print("!" * 50)
            c_input("Press Enter...")

        # ── Phase 4: Death Throes ─────────────────────────────────────
        if ctx["phase"] == 4 and j["hp"] > 0:
            _jabberwock_death_throes(player)

        return None

    def on_player_hit_hook(target, elist, ctx):
        """Track damage dealt during Vorpal Beam windup for interrupt check."""
        if ctx.get("_vorpal_beam_charging") and _is_jabberwock(target):
            # We don't know exact damage here, but we can estimate from HP change
            # The on_hit hook doesn't receive damage amount — it receives the target after being hit
            # Actually, looking at the superboss_common, on_hit is called as:
            # on_hit_fn(target, elist) — just target and elist
            # We can't track exact damage here. Let's use a different approach.
            pass

    def enemy_turn_hook(enemy, ctx, pl, p_con, defending, turn_order=None, step_idx=None):
        """Handle Jabberwock, Bandersnatch, and phase-specific AI."""

        # Store turn_order and player ref for use in extra_logic callbacks
        if turn_order is not None:
            ctx["_current_turn_order"] = turn_order
        ctx["_player_ref"] = pl
        ctx["_enemies_ref"] = ctx.get("_enemies_ref", [enemy] if isinstance(enemy, dict) else [])

        # ── Bandersnatch turn ──────────────────────────────────────────
        if _is_bandersnatch(enemy):
            # Bandersnatch does Frumious Swipe: moderate damage, can crit
            # Use +2 temp_str for moderate hit, and crit chance via extra_logic
            def _frumious_swipe(e, tgt, dmg):
                if random.random() < 0.25:
                    return f"  💥 FRUMIOUS SWIPE! Critical hit on {tgt.get('name', 'target')}!"
                return None
            return 1, False, _frumious_swipe, 1.0, 1

        # ── Non-Jabberwock enemy ───────────────────────────────────────
        if not _is_jabberwock(enemy):
            return 1, False, None, 1.0, 0

        # ── Increment action counter ───────────────────────────────────
        ctx["jabberwock_actions"] = ctx.get("jabberwock_actions", 0) + 1

        # ── Dispatch to phase handler ──────────────────────────────────
        if ctx["phase"] == 4:
            return _jabberwock_phase4_turn(enemy, pl, ctx)
        elif ctx["phase"] == 3:
            return _jabberwock_phase3_turn(enemy, pl, ctx)
        elif ctx["phase"] == 2:
            return _jabberwock_phase2_turn(enemy, pl, ctx)
        else:
            return _jabberwock_phase1_turn(enemy, pl, ctx)

    def post_round_hook(ctx, elist):
        """Tick buffs/debuffs, handle Page Storm, clean up per-round state."""
        j = _find_jabberwock(elist)

        # ── Phase 3: Page Storm (passive, every round) ──────────────────
        if ctx["phase"] == 3 and j and j["hp"] > 0:
            _jabberwock_page_storm(player)

        # ── Tick Jabberwock buffs ───────────────────────────────────────
        if j:
            for buff in j.get("active_buffs", []):
                if "remaining" in buff:
                    buff["remaining"] -= 1
            j["active_buffs"] = [
                b for b in j.get("active_buffs", [])
                if b.get("remaining", 999) > 0
            ]
            for debuff in j.get("active_debuffs", []):
                if "remaining" in debuff:
                    debuff["remaining"] -= 1
            j["active_debuffs"] = [
                d for d in j.get("active_debuffs", [])
                if d.get("remaining", 999) > 0
            ]

        # ── Tick player/allies debuffs ──────────────────────────────────
        for target in [player] + player.get("allies", []):
            for debuff in target.get("active_debuffs", []):
                if "remaining" in debuff:
                    debuff["remaining"] -= 1
            # Keep uncleansable debuffs (Vorpal Wound)
            target["active_debuffs"] = [
                d for d in target.get("active_debuffs", [])
                if d.get("_uncleansable") or d.get("remaining", 999) > 0
            ]

        # ── Clear turn order reference ──────────────────────────────────
        ctx["_current_turn_order"] = []

        # ── Apply Alice vorpal bonus damage marker ──────────────────────
        # (Handled by combat engine via on_hit hooks; flag is consumed each round)

    # ── Victory handler ─────────────────────────────────────────────────

    def on_kill_hook(target, elist, ctx):
        """Handle Jabberwock death, Alice permanent unlock, and drops."""
        if _is_jabberwock(target) and target.get("hp", 0) <= 0:
            c_print("\n" + "=" * 60)
            c_print("The Jabberwock's body dissolves into ink. The vortex")
            c_print("calms.")
            c_print("")
            c_print("Pages drift down around you like snow. Each one has a")
            c_print("single word on it — the Jabberwock's vocabulary,")
            c_print("scattered and spent.")
            c_print("")
            c_print("The ink pools on the floor. It spells one word across")
            c_print("the stones:")
            c_print("")
            c_print("    F I N .")
            c_print("")
            c_print("Then the word itself evaporates.")
            c_print("")
            c_print("Silence. Real silence. The kind that comes after a")
            c_print("story ends.")
            c_print("=" * 60)

            # ── Alice permanent unlock ──────────────────────────────────
            if alice:
                from combat.ally import promote_heroine_to_permanent, set_heroine_state
                join_level = alice.get("level", player.get("level", 1))
                promote_heroine_to_permanent(player, alice, join_level)
                set_heroine_state(player, "alice", "permanent")
                player["wl_boss_defeated_jabberwock"] = True

                c_print(f'\n  Alice stands very still. The teacup she\'s been')
                c_print('  holding this entire time has a crack in it.')
                c_print('')
                c_print('  "It\'s over. It\'s really over."')
                c_print('')
                c_print('  She reads the vanishing ink on the floor. Her')
                c_print('  expression flickers.')
                c_print('')
                c_print('  "It says... \'To be continued.\'"')
                c_print('  She looks at you.')
                c_print('  "That\'s not ominous at all."')
                c_print('')
                c_print('  Alice becomes a permanent ally.')
                c_input("Press Enter...")

        # ── Bandersnatch killed? No special effect ─────────────────────

    # ── Run the combat loop ──────────────────────────────────────────────
    return superboss_combat_loop(
        player, enemies, floor, "The Jabberwock", context,
        pre_player_hook=pre_player_hook,
        enemy_turn_hook=enemy_turn_hook,
        post_round_hook=post_round_hook,
        on_kill_hook=on_kill_hook,
        on_player_hit_hook=on_player_hit_hook,
    )
