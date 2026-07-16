# combat/mary_sue_shadows.py — Mary Sue Shadow Boss Factory & AI
#
# Provides creation functions and simplified enemy_turn_hook implementations
# for the three shadow bosses Mary Sue summons during her fight.
#
# Shadow bosses are simplified versions of their Floor 10/20/30/40 counterparts:
#   - Queen of Hearts:  ~40% HP, 1 soldier (no respawn), decrees at 70% power, no temper/mercy
#   - Big Bad Wolf:     ~35% HP, single phase, simplified attacks, limited abilities
#   - Wicked Witch:     ~35% HP, single phase, emerald flames + melting, no monkeys
#   - Jabberwock:       ~30% HP, single phase, reduced power, no page storm / narrative rewrite

import random
from combat.stats import enemy_stats
from combat.status_effects import apply_bleed
from combat.combat_io import c_print
from combat.ally import get_active_allies

# ── Keys ────────────────────────────────────────────────────────────────────

SHADOW_QUEEN_KEY    = "wl_queen_of_hearts_shadow"
SHADOW_SOLDIER_KEY  = "wl_card_soldier_shadow"
SHADOW_WOLF_KEY     = "wl_big_bad_wolf_shadow"
SHADOW_WITCH_KEY    = "wl_wicked_witch_shadow"
SHADOW_JABBER_KEY   = "wl_jabberwock_shadow"

# ── Decree definitions (simplified from queen_of_hearts.py) ──────────────────

_DECREE_NAMES = [
    "Off with their heads!",
    "Painting the roses red!",
    "All ways are my ways!",
]


# ══════════════════════════════════════════════════════════════════════════════
# Factory Functions
# ══════════════════════════════════════════════════════════════════════════════

def create_shadow_queen_of_hearts(player):
    """Create a simplified shadow of the Floor 10 boss, plus 1 Card Soldier."""
    boss = enemy_stats(SHADOW_QUEEN_KEY, player)
    boss["max_hp"] = boss["hp"]
    boss["key"] = SHADOW_QUEEN_KEY
    boss["_shadow_of"] = "queen_of_hearts"
    return boss


def create_shadow_card_soldier(player):
    """Create a shadow card soldier minion."""
    soldier = enemy_stats(SHADOW_SOLDIER_KEY, player)
    soldier["max_hp"] = soldier["hp"]
    soldier["key"] = SHADOW_SOLDIER_KEY
    return soldier


def create_shadow_big_bad_wolf(player):
    """Create a simplified shadow of the Floor 20 boss."""
    boss = enemy_stats(SHADOW_WOLF_KEY, player)
    boss["max_hp"] = boss["hp"]
    boss["key"] = SHADOW_WOLF_KEY
    boss["_shadow_of"] = "big_bad_wolf"
    return boss


def create_shadow_jabberwock(player):
    """Create a simplified shadow of the Floor 40 boss."""
    boss = enemy_stats(SHADOW_JABBER_KEY, player)
    boss["max_hp"] = boss["hp"]
    boss["key"] = SHADOW_JABBER_KEY
    boss["_shadow_of"] = "jabberwock"
    return boss


def create_shadow_wicked_witch(player):
    """Create a simplified shadow of the Floor 30 boss."""
    boss = enemy_stats(SHADOW_WITCH_KEY, player)
    boss["max_hp"] = boss["hp"]
    boss["key"] = SHADOW_WITCH_KEY
    boss["_shadow_of"] = "wicked_witch"
    return boss


# ══════════════════════════════════════════════════════════════════════════════
# Shadow AI — Queen of Hearts
# ══════════════════════════════════════════════════════════════════════════════

def _is_shadow_queen(e):
    return e.get("key") == SHADOW_QUEEN_KEY


def _is_shadow_soldier(e):
    return e.get("key") == SHADOW_SOLDIER_KEY


def shadow_queen_turn_hook(enemy, ctx, pl, p_con, defending, enemies_list):
    """AI for Shadow Queen of Hearts and Shadow Card Soldier.

    Shadow Queen: cycles through 3 decrees (at 70% power of original),
    one card soldier, no respawn, no temper tantrum, no mercy rule.

    Returns: (actions, skip_default, extra_logic, armor_mult, temp_str)
    """
    if _is_shadow_soldier(enemy):
        # Simple melee attack
        return 1, False, None, 1.0, 0

    if not _is_shadow_queen(enemy):
        return 1, False, None, 1.0, 0

    # ── Decree cycle (every 3 actions) ───────────────────────────────────
    actions_count = ctx.get("shadow_queen_actions", 0)
    is_decree = (actions_count % 3 == 0)
    decree_idx = ctx.get("shadow_queen_decree_idx", 0)

    if is_decree:
        decree_name = _DECREE_NAMES[decree_idx]
        c_print(f'\n  👑 Shadow Queen decrees: "{decree_name}"')

        if decree_idx == 0:
            # "Off with their heads!" — 70% power execution strike
            def _exe(e, p, dmg):
                threshold = 0.07 if defending else 0.14
                if dmg > 0 and p.get("current_hp", 0) <= int(p.get("max_hp", p.get("current_hp", 1)) * threshold):
                    c_print(f'\n  💀 "OFF WITH YOUR HEAD!"')
                    c_print(f"  The shadow\'s axe falls. {p.get("name", "Target")} is EXECUTED!")
                    p["current_hp"] = 0
                    return "💀 EXECUTED!"
                return None
            ctx["shadow_queen_decree_idx"] = 1
            ctx["shadow_queen_actions"] = actions_count + 1
            return 1, False, _exe, 1.0, 2

        elif decree_idx == 1:
            # "Painting the roses red!" — 70% power AoE bleed
            def _bleed(e, p, dmg):
                bleed_dmg = 2
                dur = 2
                target_name = p.get("name", "You")
                if defending:
                    msg = f"🩸 Defended! Bleed reduced to 1 x 2 turns."
                    apply_bleed(p, 1, 2)
                else:
                    msg = f"🩸 Painted red! Bleed: {bleed_dmg} x {dur} turns."
                    apply_bleed(p, bleed_dmg, dur)
                # Also bleed active allies
                for ally in get_active_allies(pl):
                    if ally.get("current_hp", 0) > 0:
                        apply_bleed(ally, 1 if defending else bleed_dmg, dur)
                if pl.get("allies"):
                    msg += " (All party members affected!)"
                return msg
            ctx["shadow_queen_decree_idx"] = 2
            ctx["shadow_queen_actions"] = actions_count + 1
            return 1, True, _bleed, 1.0, 0

        else:
            # "All ways are my ways!" — 70% power self-buff
            c_print("  ↠ +20% damage, +10% defense for 1 turn!")
            enemy.setdefault("active_buffs", []).append({
                "type": "royal_decree",
                "source": "royal_decree_shadow",
                "remaining": 1,
                "value": 0,
            })
            enemy["_royal_dmg_buff"] = True
            enemy["_royal_def_buff"] = True
            ctx["shadow_queen_decree_idx"] = 0
            ctx["shadow_queen_actions"] = actions_count + 1
            return 1, True, None, 1.0, 0

    # ── Non-decree turn: basic physical attack ──────────────────────────
    ctx["shadow_queen_actions"] = actions_count + 1
    return 1, False, None, 1.0, 0


# ══════════════════════════════════════════════════════════════════════════════
# Shadow AI — Big Bad Wolf
# ══════════════════════════════════════════════════════════════════════════════

def _is_shadow_wolf(e):
    return e.get("key") == SHADOW_WOLF_KEY


def shadow_wolf_turn_hook(enemy, ctx, pl, p_con, defending, enemies_list):
    """AI for Shadow Big Bad Wolf.

    Simplified version: no multi-phase, no swallow, no huff-and-puff scaling.
    - Gnashing Jaws: single-bleed, no stacking
    - Howl: self-buff (+20% damage for 2 turns)
    - Enrage at 15% HP: +40% damage, 2 attacks

    Returns: (actions, skip_default, extra_logic, armor_mult, temp_str)
    """
    if not _is_shadow_wolf(enemy):
        return 1, False, None, 1.0, 0

    actions_count = ctx.get("shadow_wolf_actions", 0)
    hp_pct = enemy["hp"] / enemy["max_hp"]

    # ── Enrage at 15% HP ───────────────────────────────────────────────
    if hp_pct <= 0.15 and not ctx.get("shadow_wolf_enraged"):
        ctx["shadow_wolf_enraged"] = True
        c_print('\n  🐺 "The shadow Wolf\'s eyes BLAZE crimson — it\'s ENRAGED!"')
        c_print("  ↠ +40% damage, 2 attacks per turn!")
        enemy.setdefault("active_buffs", []).append({
            "type": "damage_boost",
            "value": 0.40,
            "remaining": 999,
            "source": "shadow_wolf_enrage",
        })
        ctx["shadow_wolf_actions"] = actions_count + 1
        return 2, False, None, 1.0, 0  # 2 attacks

    # ── Gnashing Jaws every 3 actions ──────────────────────────────────
    if actions_count > 0 and actions_count % 3 == 0:
        def _gnash(e, p, dmg):
            apply_bleed(p, 4, 3)
            return f"🩸 Gnashing Jaws! {p.get('name', 'You')} bleeds: 4 dmg x 3 turns."
        ctx["shadow_wolf_actions"] = actions_count + 1
        return 1, False, _gnash, 1.0, 2

    # ── Howl every 5 actions ───────────────────────────────────────────
    if actions_count > 0 and actions_count % 5 == 0:
        c_print('\n  🐺 "The shadow Wolf HOWLS — the air itself trembles!"')
        c_print("  ↠ +20% damage for 2 turns!")
        enemy.setdefault("active_buffs", []).append({
            "type": "damage_boost",
            "value": 0.20,
            "remaining": 2,
            "source": "shadow_wolf_howl",
        })
        ctx["shadow_wolf_actions"] = actions_count + 1
        return 1, True, None, 1.0, 0

    # ── Default: physical attack ───────────────────────────────────────
    ctx["shadow_wolf_actions"] = actions_count + 1
    return 1, False, None, 1.0, 0


# ══════════════════════════════════════════════════════════════════════════════
# Shadow AI — Jabberwock
# ══════════════════════════════════════════════════════════════════════════════

def _is_shadow_jabberwock(e):
    return e.get("key") == SHADOW_JABBER_KEY


def _get_living_targets(pl):
    """Return list of living player + active allies."""
    targets = []
    if pl.get("current_hp", 0) > 0:
        targets.append(pl)
    for ally in get_active_allies(pl):
        if ally.get("current_hp", 0) > 0:
            targets.append(ally)
    return targets


def shadow_jabberwock_turn_hook(enemy, ctx, pl, p_con, defending, enemies_list):
    """AI for Shadow Jabberwock.

    Simplified version: no multi-phase transitions, no whiffling, no page storm,
    no narrative rewrite.
    - Claws That Catch: dual attack, no CON pierce
    - Jaws That Bite: cleanseable bleed
    - Vorpal Beam: 30+ damage to interrupt, 40-60 AoE
    - Final Vorpal Strike at 5% HP: same as original

    Returns: (actions, skip_default, extra_logic, armor_mult, temp_str)
    """
    if not _is_shadow_jabberwock(enemy):
        return 1, False, None, 1.0, 0

    actions_count = ctx.get("shadow_jabber_actions", 0)
    hp_pct = enemy["hp"] / enemy["max_hp"]

    # ── Final Vorpal Strike at 5% HP ────────────────────────────────────
    if hp_pct <= 0.05 and not ctx.get("_shadow_final_strike_used"):
        ctx["_shadow_final_strike_used"] = True
        c_print('\n  💀 "The shadow Jabberwock gathers its remaining words..."')
        c_print('  "FINAL VORPAL STRIKE!"')

        def _final_strike(e, tgt, raw_dmg):
            actual_name = tgt.get("name", "The target")
            ctx["_shadow_jabber_defenseless"] = True
            c_print('  "The shadow Jabberwock has exhausted itself. It is DEFENSELESS!"')
            return f"  {actual_name} takes {raw_dmg} damage from the Final Vorpal Strike!"
        ctx["shadow_jabber_actions"] = actions_count + 1
        return 1, False, _final_strike, 1.0, 5

    # ── If defenseless, weak attacks ────────────────────────────────────
    if ctx.get("_shadow_jabber_defenseless"):
        ctx["shadow_jabber_actions"] = actions_count + 1
        return 1, False, None, 1.0, -2

    # ── Vorpal Beam windup/fire ────────────────────────────────────────
    if ctx.get("_shadow_vorpal_charging"):
        # Firing this turn
        ctx["_shadow_vorpal_charging"] = False
        if ctx.get("_shadow_vorpal_dmg_taken", 0) >= 30:
            c_print('\n  ⚡ "The vorpal light SPUTTERS! The shadow shrieks!"')
            c_print("  ↠ Vorpal Beam INTERRUPTED! Shadow loses its next attack.")
            ctx["_shadow_vorpal_interrupted"] = True
            ctx["shadow_jabber_actions"] = actions_count + 1
            return 1, True, None, 1.0, 0
        else:
            c_print('\n  💀 "VORPAL BEAM!" — A line of pale light tears through the party!')
            for target in _get_living_targets(pl):
                dmg = random.randint(40, 60)
                res = target.get("elemental_res", {}).get("thunder", 1.0)
                final_dmg = max(1, int(dmg * res))
                target["current_hp"] = max(0, target.get("current_hp", 0) - final_dmg)
                c_print(f"    {target.get('name', 'You')} takes {final_dmg} damage [THUNDER]!")
                if target.get("current_hp", 0) <= 0:
                    c_print(f"    {target.get('name', 'You')} has been struck down!")
            ctx["shadow_jabber_actions"] = actions_count + 1
            return 1, True, None, 1.0, 0

    # ── Interrupted last turn? Skip attack ─────────────────────────────
    if ctx.pop("_shadow_vorpal_interrupted", False):
        c_print('\n  "The shadow Jabberwock reels — its narrative disrupted!"')
        ctx["shadow_jabber_actions"] = actions_count + 1
        return 1, True, None, 1.0, 0

    # ── Vorpal Beam windup every 3 actions ─────────────────────────────
    if actions_count > 0 and actions_count % 3 == 0:
        c_print('\n  ⚡ "The shadow Jabberwock\'s eyes glow with pale light..."')
        c_print('  ⚡ CHARGING: Vorpal Beam — next turn! Deal 30+ damage to interrupt!')
        ctx["_shadow_vorpal_charging"] = True
        ctx["_shadow_vorpal_dmg_taken"] = 0
        ctx["shadow_jabber_actions"] = actions_count + 1
        return 1, True, None, 1.0, 0

    # ── Jaws That Bite every 3 actions (offset from beam) ───────────────
    if actions_count > 0 and actions_count % 3 == 0:
        def _jaws(e, p, dmg):
            apply_bleed(p, 8, 3)
            return f"🩸 JAWS THAT BITE! {p.get('name', 'You')} bleeds: 8 dmg x 3 turns."
        ctx["shadow_jabber_actions"] = actions_count + 1
        return 1, False, _jaws, 1.0, 2

    # ── Claws That Catch: dual attack, no CON pierce ────────────────────
    ctx["shadow_jabber_actions"] = actions_count + 1
    return 2, False, None, 1.0, 0


# ══════════════════════════════════════════════════════════════════════════════
# Shadow AI — Wicked Witch
# ══════════════════════════════════════════════════════════════════════════════

def _is_shadow_witch(e):
    return e.get("key") == SHADOW_WITCH_KEY


def shadow_witch_turn_hook(enemy, ctx, pl, p_con, defending, enemies_list):
    """AI for Shadow Wicked Witch.

    Simplified version: no phase transitions, no Flying Monkey minions,
    no Broomstick Evasion, no death throes.
    - Emerald Flame: single-target fire damage (every 3 actions)
    - Scrying Smoke: AoE dark + accuracy debuff (every 5 actions)
    - I'm Melting! at 30% HP: takes 3% max HP self-damage per turn,
      attacks twice per turn
    - Water Weakness: 2x damage from water (via YAML)
    - Dorothy synergy: +25% water damage vs shadow (applied by Mary Sue phase)

    Returns: (actions, skip_default, extra_logic, armor_mult, temp_str)
    """
    if not _is_shadow_witch(enemy):
        return 1, False, None, 1.0, 0

    actions_count = ctx.get("shadow_witch_actions", 0)
    hp_pct = enemy["hp"] / enemy["max_hp"]

    # ── I'm Melting! at 30% HP ──────────────────────────────────────────
    if hp_pct <= 0.30 and not ctx.get("shadow_witch_melting"):
        ctx["shadow_witch_melting"] = True
        c_print('\n  🧙‍♀️ "The shadow Witch SHRIEKS — her form begins to dissolve!"')
        c_print('  "I\'m melting! MELTING! What a world... what a world..."')
        c_print("  ↠ Shadow Witch takes 3% max HP damage per turn, but attacks TWICE!")
        # Apply self-damage immediately
        melt_dmg = max(1, int(enemy["max_hp"] * 0.03))
        enemy["hp"] = max(0, enemy["hp"] - melt_dmg)
        c_print(f"  ↠ Shadow Witch loses {melt_dmg} HP from melting!")
        ctx["shadow_witch_actions"] = actions_count + 1
        return 2, False, None, 1.0, 0  # 2 attacks

    # ── Melting self-damage each turn ────────────────────────────────────
    if ctx.get("shadow_witch_melting"):
        melt_dmg = max(1, int(enemy["max_hp"] * 0.03))
        enemy["hp"] = max(0, enemy["hp"] - melt_dmg)
        c_print(f"\n  💧 The shadow Witch continues to melt... (-{melt_dmg} HP)")

    # ── Emerald Flame every 3 actions ────────────────────────────────────
    if actions_count > 0 and actions_count % 3 == 0:
        def _emerald(e, p, dmg):
            # Apply scorch effect
            p.setdefault("active_debuffs", []).append({
                "type": "scorched",
                "remaining": 2,
                "source": "shadow_witch_emerald",
                "value": 0.15,
            })
            return f"💚 EMERALD FLAME engulfs {p.get('name', 'You')}! -15% fire resist for 2 turns!"
        ctx["shadow_witch_actions"] = actions_count + 1
        return 1, False, _emerald, 1.0, 2

    # ── Scrying Smoke every 5 actions ────────────────────────────────────
    if actions_count > 0 and actions_count % 5 == 0:
        def _smoke(e, p, dmg):
            # Accuracy debuff
            p.setdefault("active_debuffs", []).append({
                "type": "blinded",
                "remaining": 2,
                "source": "shadow_witch_smoke",
                "value": 0.20,
            })
            return f"💨 SCRYING SMOKE clouds {p.get('name', 'You')}! -20% accuracy for 2 turns!"
        ctx["shadow_witch_actions"] = actions_count + 1
        return 1, True, _smoke, 1.0, 0

    # ── Default: physical attack (cackling scratch) ──────────────────────
    ctx["shadow_witch_actions"] = actions_count + 1
    return 1, False, None, 1.0, 0


# ══════════════════════════════════════════════════════════════════════════════
# Plot Armor Tracker
# ══════════════════════════════════════════════════════════════════════════════

ALL_ELEMENT_TYPES = ["physical", "fire", "water", "thunder", "wind", "earth", "light", "dark"]


def init_plot_armor(stacks=5):
    """Initialize Plot Armor tracking dictionary."""
    return {
        "stacks": stacks,
        "used_types": set(),
    }


def get_plot_armor_dr(armor):
    """Calculate damage reduction from Plot Armor stacks. Each stack = 12% DR."""
    return min(0.60, armor["stacks"] * 0.12)


def try_strip_plot_armor(armor, damage_type):
    """Attempt to strip a Plot Armor stack with the given damage type.

    Returns True if a stack was stripped, False otherwise.
    """
    if armor["stacks"] <= 0:
        return False
    if damage_type not in ALL_ELEMENT_TYPES:
        damage_type = "physical"
    if damage_type not in armor["used_types"]:
        armor["used_types"].add(damage_type)
        armor["stacks"] -= 1
        c_print(f'\n  📖 "A crack appears in Mary Sue\'s narrative armor!"')
        c_print(f'  ({armor["stacks"]} stacks remaining — {get_plot_armor_dr(armor)*100:.0f}% DR)')
        return True
    return False


def regen_plot_armor(armor):
    """Regenerate 1 stack of Plot Armor (up to 5 max)."""
    if armor["stacks"] < 5:
        armor["stacks"] += 1
        c_print(f'\n  ✨ Mary Sue\'s Plot Armor strengthens... ({armor["stacks"]} stacks)')
