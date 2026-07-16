# combat/big_bad_wolf.py — Wonderland Superboss: Big Bad Wolf (Floor 20)
#
# MECHANIC OVERVIEW:
# ─────────────────
# Single-phase fight against the Big Bad Wolf of fairy-tale fame.
#
# Swallow (core gimmick — post‑round hook):
#   After every combatant has acted, the Wolf scans the party for allies
#   who did NOT Defend this turn.  One non‑defending ally is SWALLOWED
#   WHOLE, removed from the field entirely for 2 turns.
#
#   While an ally is swallowed the party must deal 100+ total damage to
#   the Wolf within those 2 turns.  If the threshold is met the ally is
#   coughed up unharmed.  If the party fails to meet the threshold the
#   ally is spat out and takes 55% of their max HP minus their CON mod
#   as damage (minimum 1).
#
#   The Wolf cannot swallow the player — only allies.  If every active
#   ally Defended, the Wolf instead performs a devastating Maul on the
#   player (heavy physical hit).
#
# Wolf action pattern (enemy_turn_hook):
#   • Gnashing Jaws (every 3 actions) — heavy single‑target physical +
#     bleed (5 dmg × 3 turns).
#   • Huff and Puff  (every 4 actions) — AoE wind damage to all party.
#   • Howl           (every 5 actions) — self‑buff +20% dmg 2 turns;
#     if an ally is currently swallowed, the swallow timer is EXTENDED
#     by 1 turn.
#   • Enrage at 15% HP — +40% damage, 2 attacks per turn permanently.
#   • Default — basic physical attack.
#
# Victory rewards the Crimson Hood Scrap (unique) plus Wolf's Tooth
# and Woodcutter's Broken Axe (secondary).

import random
from combat.stats import enemy_stats, compute_player_stats
from combat.player_actions import handle_player_turn
from combat.combat_ui import format_enemy_status_line, print_superboss_header
from combat.superboss_common import superboss_combat_loop
from combat.status_effects import apply_bleed
from combat.ally import get_active_allies, compute_ally_stats
from combat.combat_io import c_print, c_input, c_clear

# ── Boss key ─────────────────────────────────────────────────────────────────

WOLF_KEY = "wl_big_bad_wolf"

# ── Swallow constants ────────────────────────────────────────────────────────

SWALLOW_DURATION = 2          # turns ally remains swallowed
SWALLOW_DAMAGE_THRESHOLD = 100  # total damage needed to free ally
SWALLOW_HP_PCT = 0.55         # % of max HP dealt if threshold not met


# ── Helpers ──────────────────────────────────────────────────────────────────

def _is_wolf(e):
    return e.get("key") == WOLF_KEY


def _find_wolf(enemies):
    for e in enemies:
        if _is_wolf(e) and e["hp"] > 0:
            return e
    return None


def _get_non_defending_allies(player):
    """Return list of active allies that did NOT Defend this turn."""
    allies = get_active_allies(player)
    return [a for a in allies if not a.get("defending_this_turn", False)
            and a.get("current_hp", 0) > 0]


def _get_alive_party(player):
    """Return list of living player + active allies."""
    targets = []
    if player.get("current_hp", 0) > 0:
        targets.append(player)
    for ally in get_active_allies(player):
        if ally.get("current_hp", 0) > 0:
            targets.append(ally)
    return targets


# ══════════════════════════════════════════════════════════════════════════════
# Enemy turn hook (Wolf AI)
# ══════════════════════════════════════════════════════════════════════════════

def _wolf_turn_hook(enemy, ctx, player, p_con, defending, **kwargs):
    """AI for the Big Bad Wolf.

    Returns: (actions, skip_default, extra_logic, armor_mult, temp_str)
    """
    if not _is_wolf(enemy):
        return 1, False, None, 1.0, 0

    actions_count = ctx.get("wolf_actions", 0)
    hp_pct = enemy["hp"] / enemy["max_hp"]

    # ── Enrage at 15% HP ───────────────────────────────────────────────
    if hp_pct <= 0.15 and not ctx.get("wolf_enraged"):
        ctx["wolf_enraged"] = True
        c_print('\n  🐺 "The Wolf\'s eyes BLAZE crimson — it\'s ENRAGED!"')
        c_print("  ↠ +40% damage, 2 attacks per turn!")
        enemy.setdefault("active_buffs", []).append({
            "type": "damage_boost",
            "value": 0.40,
            "remaining": 999,
            "source": "wolf_enrage",
        })
        ctx["wolf_actions"] = actions_count + 1
        return 2, False, None, 1.0, 0  # 2 attacks this turn

    # ── Gnashing Jaws every 3 actions ─────────────────────────────────
    if actions_count > 0 and actions_count % 3 == 0:
        def _gnash(e, p, dmg):
            apply_bleed(p, 5, 3)
            return f"🩸 Gnashing Jaws! {p.get('name', 'You')} bleeds: 5 dmg × 3 turns."
        ctx["wolf_actions"] = actions_count + 1
        return 1, False, _gnash, 1.0, 3  # +3 temp str for heavy hit

    # ── Huff and Puff every 4 actions (AoE wind) ──────────────────────
    if actions_count > 0 and actions_count % 4 == 0:
        def _huff(e, p, dmg):
            # AoE: damage ALL party members
            party = _get_alive_party(player)
            total = 0
            for member in party:
                if member is player:
                    mem_con = p_con
                    is_def = defending
                else:
                    _, mem_con, _, _, _, _ = compute_ally_stats(member)
                    is_def = member.get("defending_this_turn", False)

                # Simplified AoE: 60% of normal damage to each
                raw = max(1, e.get("str_mod", 5) + 4)
                if is_def:
                    raw = max(1, raw // 2)
                member["current_hp"] = member.get("current_hp", 0) - raw
                total += raw

            names = ", ".join(m.get("name", "You") for m in party if m.get("current_hp", 0) > 0)
            return f"💨 Huff and Puff! {names} take wind damage!"
        ctx["wolf_actions"] = actions_count + 1
        return 1, True, _huff, 1.0, 0  # skip default, use extra_logic

    # ── Howl every 5 actions ───────────────────────────────────────────
    if actions_count > 0 and actions_count % 5 == 0:
        c_print('\n  🐺 "The Wolf throws back its head and HOWLS —')
        c_print('     the very trees shudder!"')
        c_print("  ↠ +20% damage for 2 turns!")

        enemy.setdefault("active_buffs", []).append({
            "type": "damage_boost",
            "value": 0.20,
            "remaining": 2,
            "source": "wolf_howl",
        })

        # If an ally is currently swallowed, extend the timer
        if ctx.get("swallowed_ally") is not None and ctx.get("swallow_turns_remaining", 0) > 0:
            ctx["swallow_turns_remaining"] += 1
            c_print("  🐺 The Howl tightens its throat — the swallow timer EXTENDS by 1 turn!")

        ctx["wolf_actions"] = actions_count + 1
        return 1, True, None, 1.0, 0  # skip default attack

    # ── Default: basic physical attack ─────────────────────────────────
    ctx["wolf_actions"] = actions_count + 1
    return 1, False, None, 1.0, 0


# ══════════════════════════════════════════════════════════════════════════════
# Post‑round hook (Swallow mechanic)
# ══════════════════════════════════════════════════════════════════════════════

def _post_round_hook(ctx, enemies):
    """Handle swallow mechanics at the end of each round."""
    wolf = _find_wolf(enemies)
    if wolf is None:
        return None

    player = ctx.get("_player")
    if player is None:
        return None

    # ── Case 1: An ally is already swallowed ───────────────────────────
    if ctx.get("swallowed_ally") is not None:
        ctx["swallow_turns_remaining"] = ctx.get("swallow_turns_remaining", 0) - 1

        ally = ctx["swallowed_ally"]
        ally_name = ally.get("name", "Unknown")

        c_print(f"\n  🐺 Inside the Wolf's belly... ({ally_name})")
        c_print(f"     Turns remaining: {ctx['swallow_turns_remaining']}")
        c_print(f"     Damage dealt to Wolf: {ctx.get('swallow_damage_dealt', 0)}/{SWALLOW_DAMAGE_THRESHOLD}")

        if ctx["swallow_turns_remaining"] <= 0:
            # Timer expired — check damage threshold
            if ctx.get("swallow_damage_dealt", 0) >= SWALLOW_DAMAGE_THRESHOLD:
                c_print(f"\n  💪 The Wolf GAGS — {ally_name} is coughed up unharmed!")
                _free_ally(ctx)
            else:
                # Failed to meet threshold — spit damage
                _, a_con, _, _, _, _ = compute_ally_stats(ally)
                damage_pct = SWALLOW_HP_PCT - (a_con * 0.01)  # CON reduces damage %
                damage_pct = max(0.10, min(0.55, damage_pct))  # clamp 10%–55%
                damage = max(1, int(ally.get("max_hp", 50) * damage_pct))

                c_print(f"\n  🤮 The Wolf SPITS out {ally_name}!")
                c_print(f"     {ally_name} crashes to the ground, taking {damage} damage!")
                c_print(f"     (Digestive damage: {int(damage_pct*100)}% of max HP)")

                ally["current_hp"] = max(0, ally.get("current_hp", 0) - damage)
                _free_ally(ctx)

                if ally.get("current_hp", 0) <= 0:
                    ally["defeated"] = True
                    c_print(f"     {ally_name} has been defeated by the digestive acids...")

        # Track damage dealt TO the wolf (reset per round below in next case)
        # We track this by checking wolf HP change — handled externally

        return None

    # ── Case 2: No ally swallowed — try to swallow one ────────────────
    non_def = _get_non_defending_allies(player)
    if non_def:
        target = random.choice(non_def)
        target_name = target.get("name", "Unknown")

        c_print(f"\n  🐺 The Wolf's jaws SNAP SHUT around {target_name}!")
        c_print(f"     {target_name} is SWALLOWED WHOLE — removed from the field!")
        c_print(f"     Deal {SWALLOW_DAMAGE_THRESHOLD}+ damage in {SWALLOW_DURATION} turns to free them!")

        # Remove ally from field
        target["defeated"] = True  # temporary — restored on free
        ctx["swallowed_ally"] = target
        ctx["swallow_turns_remaining"] = SWALLOW_DURATION
        ctx["swallow_damage_dealt"] = 0
        # Snapshot wolf's current HP to track damage later
        ctx["_wolf_hp_at_swallow"] = wolf["hp"]
        return None

    # ── Case 3: All allies defended — Maul the player ──────────────────
    c_print('\n  🐺 "No prey hides behind their guard from ME!"')
    c_print("     The Wolf MAULS you with unrestrained fury!")
    raw_dmg = wolf.get("str_mod", 7) + 10
    p_con_val = player.get("con_mod", 5)
    final_dmg = max(1, raw_dmg - p_con_val)
    player["current_hp"] = player.get("current_hp", 0) - final_dmg
    c_print(f"     You take {final_dmg} damage!")

    if player.get("current_hp", 0) <= 0:
        c_print(f"     {player.get('name', 'You')} have been slain.")
        return "dead"

    return None


def _free_ally(ctx):
    """Release a swallowed ally back to the field."""
    ally = ctx.get("swallowed_ally")
    if ally is not None:
        ally["defeated"] = False
        ally["defending_this_turn"] = False
    ctx["swallowed_ally"] = None
    ctx["swallow_turns_remaining"] = 0
    ctx["swallow_damage_dealt"] = 0


# ══════════════════════════════════════════════════════════════════════════════
# Pre‑player hook (track swallow damage & HP thresholds)
# ══════════════════════════════════════════════════════════════════════════════

def _pre_player_hook(ctx, elist):
    """Track damage dealt to the Wolf for swallow escape, check HP thresholds."""
    wolf = _find_wolf(elist)
    if wolf is None:
        return None

    # Track damage dealt since last swallow for escape condition
    if ctx.get("swallowed_ally") is not None:
        prev_hp = ctx.get("_wolf_hp_at_swallow", wolf["hp"])
        damage_dealt = max(0, prev_hp - wolf["hp"])
        ctx["swallow_damage_dealt"] = ctx.get("swallow_damage_dealt", 0) + damage_dealt
        ctx["_wolf_hp_at_swallow"] = wolf["hp"]  # reset tracker for next interval

    return None


# ══════════════════════════════════════════════════════════════════════════════
# Main combat function
# ══════════════════════════════════════════════════════════════════════════════

def combat_big_bad_wolf(player, floor=None, enemies=None):
    """Wonderland Superboss — Big Bad Wolf (Floor 20).

    Args:
        enemies: Optional pre-created enemy list for GUI mode state sharing.
    """
    if floor is None:
        loc = player.get("location", "")
        floor = player.get("city_floors", {}).get(loc, {}).get("floor", 20)

    # ── Create or locate boss ──────────────────────────────────────────
    if enemies is None:
        boss = enemy_stats(WOLF_KEY, player)
        boss["max_hp"] = boss["hp"]
        enemies = [boss]
    else:
        boss = None
        for e in enemies:
            if _is_wolf(e):
                e["max_hp"] = e["hp"]
                boss = e
                break
        if boss is None:
            boss = enemy_stats(WOLF_KEY, player)
            boss["max_hp"] = boss["hp"]
            enemies.append(boss)

    # ── Check for Red Hood ────────────────────────────────────────────
    red_hood = next((a for a in player.get("allies", [])
                     if a.get("_heroine_key") == "red_hood"
                     and a.get("current_hp", 0) > 0), None)

    # ── Opening narration ──────────────────────────────────────────────
    c_clear()
    c_print("=" * 60)
    c_print("The forest path opens onto a clearing bathed in silver")
    c_print("moonlight.  A quaint cottage stands at the far end, its")
    c_print("door hanging askew.  The wind carries a low, rumbling growl.")
    c_print("")
    c_print("From the shadow of the cottage steps a wolf — but this is no")
    c_print("ordinary beast.  It walks on two legs, its yellow eyes gleaming")
    c_print("with terrible intelligence.  A tattered crimson hood hangs")
    c_print("from one jagged fang.")
    c_print("")
    if red_hood:
        c_print('"Grandmother..." Red Hood\'s voice cracks. "That\'s Grandmother\'s —"')
        c_print("")
        c_print("The Wolf grins. Its teeth are very, very sharp.")
    c_print('"Grandmother?  Oh, I ALREADY ate Grandmother."')
    c_print("")
    c_print("It grins.  All the better to EAT you with.")
    c_print("=" * 60)
    c_print(f"\nBig Bad Wolf — HP: {boss['hp']}")
    c_input("\nPress Enter to face the Big Bad Wolf...")

    # ── Combat context ─────────────────────────────────────────────────
    context = {
        "wolf_actions": 0,            # how many times the Wolf has acted
        "swallowed_ally": None,       # reference to swallowed ally (or None)
        "swallow_turns_remaining": 0, # turns until ally is freed/spat
        "swallow_damage_dealt": 0,    # damage dealt since last swallow
        "_wolf_hp_at_swallow": boss["hp"],  # snapshot for damage tracking
        "wolf_enraged": False,        # whether enrage has triggered
        "_player": player,            # player reference for post_round_hook
    }

    # ── Victory handler: Red Hood permanent unlock ──────────────────────

    def on_kill_hook(target, elist, ctx):
        """Handle Wolf death, Red Hood permanent unlock, and drops."""
        if _is_wolf(target) and target.get("hp", 0) <= 0:
            from combat.ally import promote_heroine_to_permanent, set_heroine_state

            c_print("\n" + "=" * 60)
            c_print("The Wolf collapses. Its great body shrinks, the bristling")
            c_print("fur receding until all that remains is a gaunt, grey shape")
            c_print("lying still on the cottage floor.")
            c_print("")
            c_print("The crimson hood slips from its jaws and drifts to the")
            c_print("ground, lighter than it should be.")
            c_print("=" * 60)

            # ── Red Hood permanent unlock ──────────────────────────────
            if red_hood:
                join_level = red_hood.get("level", player.get("level", 1))
                promote_heroine_to_permanent(player, red_hood, join_level)
                set_heroine_state(player, "red_hood", "permanent")
                player["wl_boss_defeated_big_bad_wolf"] = True

                c_print(f'\n  Red Hood kneels beside the body. Her hands are')
                c_print('  shaking — not from fear. From something else.')
                c_print('')
                c_print('  "He\'s gone. He\'s really gone."')
                c_print('')
                c_print('  She picks up the crimson hood. It\'s clean now,')
                c_print('  as though the Wolf\'s mouth never touched it.')
                c_print('')
                c_print('  "Grandmother... I finished it. The story you started."')
                c_print('')
                c_print('  She ties the hood around her shoulders. It fits')
                c_print('  differently now — not a child\'s cloak, but a hunter\'s.')
                c_print('')
                c_print('  "You helped me finish this. I\'m not going anywhere."')
                c_print('')
                c_print('  Red Hood becomes a PERMANENT ally.')
                c_input("Press Enter...")

    # ── Run combat loop ────────────────────────────────────────────────
    result = superboss_combat_loop(
        player, enemies, floor,
        boss_name="Big Bad Wolf",
        context=context,
        pre_player_hook=_pre_player_hook,
        enemy_turn_hook=_wolf_turn_hook,
        post_round_hook=_post_round_hook,
        on_kill_hook=on_kill_hook,
    )

    # ── Cleanup: ensure swallowed ally is freed on any exit ────────────
    _free_ally(context)

    return result
