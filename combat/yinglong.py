# yinglong_3.py – Heaven-Banished Dragon Yinglong super boss encounter
#
# MECHANIC OVERVIEW:
# ─────────────────
# Phase 1  (100% → 75% HP)
#   • Takes -60% damage from the player (divine scales).
#   • Every 3 turns, a Heaven Pillar is summoned (max 1 active).
#     Destroying the pillar grants "Shattered Heaven" buff:
#     player deals FULL damage to Yinglong for 3 turns.
#   • Normal enemy attacks (modified by damage resistance).
#
# Phase 2  "Devoured" (75% HP trigger, once)
#   • Yinglong swallows the player whole.
#   • Inner-Dragon combat: 5 Dragonkin enemies, all stats ×1.40.
#     – Every 3 turns INSIDE (announced after initiative), "Heaven
#       Pinning Wedge" activates on TURN-END: deals 20% max HP as
#       pure unblockable damage — BUT if the player Defended that
#       turn, the wedge deals 0 damage and the player gains a
#       20%-max-HP bonus hit for their next turn instead.
#       Only fires twice total across the inner fight.
#   • After all 5 dragonkin die → Yinglong resumes at 35% HP.
#
# Phase 3  (35% HP onwards — normal attacks, no pillar)
#   • Same 60% damage resistance unless Shattered Heaven buff is
#     active (carried over / refreshed from Phase 1 if still ticking).
#
# Phase 4  "Immortal Rage" (≤20% HP)
#   • Yinglong becomes Immortal: completely immune to normal attacks
#     while Wedge is alive.
#   • +30% damage bonus on all attacks.
#   • Summons 1 Heaven Pinning Wedge entity (always acts last).
#     – Player must destroy the Wedge; on death it bounces 7% of
#       Yinglong's MAX HP as true damage.
#     – Until the Wedge is destroyed Yinglong remains Immortal.

import random
from utils import clear_screen
from combat.stats import enemy_stats, compute_player_stats
from combat.player_actions import handle_player_turn
from combat.combat_ui import format_enemy_status_line, print_superboss_header, print_combat_hud
from combat.superboss_common import superboss_combat_loop
from combat.status_effects import apply_weaken, format_player_status_line
from character import player_max_hp


# ═══════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════

BOSS_KEY = "heaven_banished_dragon_yinglong"
PILLAR_KEY = "yinglong_heaven_pillar"
WEDGE_KEY = "yinglong_heaven_pinning_wedge"

DRAGON_MINION_POOL = [
    "dragonkin_sky_terror",
    "dragonkin_storm_wing",
    "dragonkin_abyssal_drake",
    "dragonkin_time_drake",
    "dragonkin_elder_wyrm",
]

DAMAGE_RESIST     = 0.60
INNER_STAT_MULT   = 1.40
WEDGE_HP_DMG_PCT  = 0.20
WEDGE_BOUNCE_PCT  = 0.07
IMMORTAL_DMG_MULT = 1.30


# ═══════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════

def _is_boss(e):
    return e.get("key") == BOSS_KEY

def _is_pillar(e):
    return e.get("key") == PILLAR_KEY

def _is_wedge(e):
    return e.get("key") == WEDGE_KEY

def _apply_shattered_heaven(player, turns=3):
    for b in player.get("active_buffs", []):
        if b.get("source") == "shattered_heaven":
            b["remaining"] = max(b["remaining"], turns)
            return "refreshed"
    player.setdefault("active_buffs", []).append({
        "type":   "shattered_heaven",
        "source": "shattered_heaven",
        "remaining": turns,
        "value":  0,
    })
    return "applied"

def _has_shattered_heaven(player):
    return any(b.get("source") == "shattered_heaven" for b in player.get("active_buffs", []))

def _tick_shattered_heaven(player):
    for b in player.get("active_buffs", [])[:]:
        if b.get("source") == "shattered_heaven":
            b["remaining"] -= 1
            if b["remaining"] <= 0:
                player["active_buffs"].remove(b)
                return True
    return False

def _make_pillar():
    return {
        "key":     PILLAR_KEY,
        "name":    "Heaven Pillar",
        "hp":      40,
        "max_hp":  40,
        "str_mod": 0,
        "con_mod": 0,
        "dex_mod": -10,
        "level":   45,
        "multiplier": 1.0,
        "active_debuffs": [],
    }

def _make_wedge():
    return {
        "key":     WEDGE_KEY,
        "name":    "Heaven Pinning Wedge",
        "hp":      30,
        "max_hp":  30,
        "str_mod": 0,
        "con_mod": 0,
        "dex_mod": -20,
        "level":   45,
        "multiplier": 1.0,
        "active_debuffs": [],
    }

def _make_dragonkin_minion(player, stat_mult):
    key = random.choice(DRAGON_MINION_POOL)
    base = enemy_stats(key, player)
    base["str_mod"]  = int(base["str_mod"]  * stat_mult)
    base["con_mod"]  = int(base["con_mod"]  * stat_mult)
    base["dex_mod"]  = int(base["dex_mod"]  * stat_mult)
    scaled_hp        = int(base["hp"]       * stat_mult)
    base["hp"]       = scaled_hp
    base["max_hp"]   = scaled_hp
    base["name"]    += f" [Belly {random.randint(10,99)}]"
    return base


# ═══════════════════════════════════════════════════════════════════
# INNER-DRAGON BELLY COMBAT
# ═══════════════════════════════════════════════════════════════════

def _inner_dragon_combat(player):
    print("\n" + "☁" * 60)
    print("The world goes dark.  You have been SWALLOWED.")
    print("Inside the Dragon's belly — a warped skyscape of crushing")
    print("heaven-light and writhing draconic sinew.")
    print("Defeat all 5 dragon guardians to escape!")
    print("☁" * 60)
    input("Press Enter to fight your way out...")

    minions = [_make_dragonkin_minion(player, INNER_STAT_MULT) for _ in range(5)]

    inner_ctx = {
        "turn_counter":       0,
        "wedge_activations":  0,
        "defending_this_turn": False,
        "bonus_dmg_next_turn": False,
    }

    def inner_hud(ctx, elist):
        wedge_warn = ""
        next_wedge_turn = 3 * (ctx["wedge_activations"] + 1)
        turns_left = next_wedge_turn - ctx["turn_counter"]
        if ctx["wedge_activations"] < 2:
            wedge_warn = f"⚠ Heaven Pinning Wedge in {turns_left} turn(s)!"
        print(f"☁ INSIDE YINGLONG ☁ {wedge_warn}")
        if ctx["bonus_dmg_next_turn"]:
            print("⚡ BONUS: You deflected the Wedge — deal +20% max HP next attack!")
        print_combat_hud(player, elist, header="Dragon Guardians")

    def inner_action_override(ctx):
        action = input("Choose: ").strip().lower()
        ctx["defending_this_turn"] = (action == "d")
        return action

    def inner_post_round(ctx, elist):
        if all(e["hp"] <= 0 for e in elist):
            return
        ctx["turn_counter"] += 1
        next_trigger = 3 * (ctx["wedge_activations"] + 1)
        if ctx["wedge_activations"] < 2 and ctx["turn_counter"] >= next_trigger:
            ctx["wedge_activations"] += 1
            max_hp_player = player_max_hp(player)
            print("\n" + "✦" * 55)
            print(f"☁ HEAVEN PINNING WEDGE activates!")

            for e in elist:
                if e["hp"] > 0:
                    enemy_dmg = int(e["max_hp"] * WEDGE_HP_DMG_PCT)
                    e["hp"] = max(0, e["hp"] - enemy_dmg)
                    print(f"  {e['name']} takes {enemy_dmg} damage!")

            if ctx["defending_this_turn"]:
                print("You DEFENDED — the Wedge's energy is deflected from you!")
                print(f"The energy redirects — you gain +20% max HP on your next attack!")
                ctx["bonus_dmg_next_turn"] = True
            else:
                wedge_dmg = int(max_hp_player * WEDGE_HP_DMG_PCT)
                player["current_hp"] -= wedge_dmg
                print(f"Pure divine force — {wedge_dmg} unblockable damage to {player['name']}!")
                for ally in player.get("allies", []):
                    if ally.get("current_hp", 0) > 0:
                        if ally.pop("defending_this_turn", False):
                            print(f"{ally['name']} DEFENDED — the Wedge's energy is deflected from them!")
                        else:
                            ally_dmg = int(ally["max_hp"] * WEDGE_HP_DMG_PCT)
                            ally["current_hp"] -= ally_dmg
                            print(f"Pure divine force — {ally_dmg} unblockable damage to {ally['name']}!")
                if player["current_hp"] <= 0:
                    print(f"{player['name']} is crushed by Heaven's weight inside the Dragon!")
                    return "dead"

            print("✦" * 55)
            ctx["defending_this_turn"] = False

    def inner_on_kill(target, elist, ctx):
        pass

    def inner_enemy_hook(enemy, ctx, pl, p_con, defending):
        return 1, False, None, 1.0, 0

    result = superboss_combat_loop(
        player, minions, floor=None, boss_name="Inside Yinglong",
        context=inner_ctx,
        pre_player_hook=None,
        custom_hud_hook=inner_hud,
        on_kill_hook=inner_on_kill,
        player_action_override=inner_action_override,
        enemy_turn_hook=inner_enemy_hook,
        post_round_hook=inner_post_round,
    )

    if result == "fled":
        print("There is no escape from within! You are still trapped!")
        return "victory"

    return result


# ═══════════════════════════════════════════════════════════════════
# MAIN COMBAT FUNCTION
# ═══════════════════════════════════════════════════════════════════

def combat_yinglong(player, floor=None):
    # ── CUSTOM HOOKS & IMMORTALITY IMPLEMENTATION ───────────────
    class ImmortalDragonDict(dict):
        def __setitem__(self, key, value):
            if key == "hp":
                max_hp = self.get("max_hp_total")
                if max_hp is None:
                    max_hp = self.get("hp", 1000)
                    self["max_hp_total"] = max_hp
                
                lock_threshold = int(max_hp * 0.20)
                
                # If Phase 4 is locked, clamp health to the floor threshold
                if self.get("phase_4_locked"):
                    if not self.get("_allow_hp_drop"):
                        current_threshold = self.get("hp_lock_threshold", lock_threshold)
                        if value < current_threshold:
                            value = current_threshold
                else:
                    # Automatically trigger Phase 4 locking when hitting <= 20% HP
                    if value <= lock_threshold:
                        value = lock_threshold
                        self["phase_4_locked"] = True
                        self["hp_lock_threshold"] = lock_threshold
            super().__setitem__(key, value)

    class OneHitWedgeDict(dict):
        def __setitem__(self, key, value):
            if key == "hp":
                # If its HP drops at all, instantly snap it to 0 (1-hit kill rule)
                if value < self.get("hp", 1):
                    value = 0
            super().__setitem__(key, value)

    # Initialize stats and wrap Yinglong in the Immortal Dictionary subclass
    base_boss_stats = enemy_stats(BOSS_KEY, player)
    boss = ImmortalDragonDict(base_boss_stats)
    boss["max_hp"] = boss["hp"]
    boss["max_hp_total"] = boss["hp"]
    boss["base_str_mod"] = boss.get("str_mod", 0)
    
    enemies = [boss]

    print("\n" + "═" * 60)
    print("The sky CRACKS.  A shape descends from the wound in heaven —")
    print("colossal, serpentine, wreathed in clouds that weep lightning.")
    print("This is no mere monster.  This is a GOD cast down from the")
    print("celestial realm, still furious, still DIVINE.")
    print(f"\nYinglong, Heaven-Banished Dragon — HP: {boss['hp']}")
    print("═" * 60)
    input("Press Enter to face the Heaven-Banished Dragon...")

    context = {
        "phase":                1,
        "devour_triggered":     False,
        "immortal_triggered":   False,
        "pillar_turn_counter":  0,
        "pillar_active":        False,
        "belly_complete":       False,
        "wedge_active":         False,
        "immortal":             False,
        "defending_this_turn":  False,
        "bonus_dmg_next_turn":  False,
    }

    # ── Player Hit Hook (Immortality & Bonus Damage) ────────────────
    def on_player_hit_hook(target, elist, ctx):
        if not _is_boss(target):
            return
            
        if ctx.get("immortal") and ctx.get("wedge_active"):
            print("\n✦ Yinglong's divine immortality holds firm — it takes no damage!")
            return
            
        # Dynamically apply bonus deflected Wedge true damage directly to health pool
        if ctx.get("bonus_dmg_next_turn"):
            bonus_damage = int(player_max_hp(player) * 0.20)
            
            # Briefly disable immortality limits if present to allow bonus pure damage
            target["_allow_hp_drop"] = True
            target["hp"] -= bonus_damage
            target["_allow_hp_drop"] = False
            
            print(f"\n⚡ Deflected Wedge energy surges! +{bonus_damage} bonus pure damage delivered!")
            ctx["bonus_dmg_next_turn"] = False

    # ── Pre-player hook ─────────────────────────────────────────────
    def pre_player_hook(ctx, elist):
        b = next((e for e in elist if _is_boss(e)), None)
        if not b: return

        # Phase 2
        if b and not ctx["devour_triggered"] and b["hp"] <= int(b["max_hp"] * 0.75):
            ctx["devour_triggered"] = True
            ctx["phase"] = 2
            print("\n" + "☁" * 60)
            print("Yinglong OPENS ITS MAWS WIDE —")
            print("A gravity-less vortex tears you off your feet!")
            print("YOU HAVE BEEN SWALLOWED WHOLE.")
            print("☁" * 60)
            input("Press Enter...")

            inner_result = _inner_dragon_combat(player)
            if inner_result == "dead":
                return "dead"

            ctx["belly_complete"] = True
            ctx["phase"] = 3
            print("\n" + "☁" * 60)
            print("You claw your way OUT through the Dragon's side.")
            print("Yinglong ROARS in agony — but it is still alive.")
            resume_hp = int(b["max_hp"] * 0.35)
            b["hp"] = resume_hp
            print(f"Yinglong's remaining HP: {resume_hp}")
            print("☁" * 60)
            input("Press Enter to continue the battle...")

            elist[:] = [e for e in elist if not _is_pillar(e)]
            ctx["pillar_active"] = False
            return

        # Phase 4 (can re-trigger after wedge bounce)
        if b and ctx["phase"] >= 3 and b["hp"] <= int(b["max_hp"] * 0.20) and not ctx.get("wedge_active"):
            if not ctx["immortal_triggered"]:
                ctx["immortal_triggered"] = True
            ctx["phase"] = 4
            ctx["immortal"] = True
            b["str_mod"] = int(b["base_str_mod"] * IMMORTAL_DMG_MULT)

            print("\n" + "!" * 60)
            print("[IMMORTAL RAGE]  Yinglong REFUSES to die.")
            print("Crackling divine light seals its wounds shut — IMMORTAL!")
            print("A Heaven Pinning Wedge descends — destroy it to")
            print("force 7% MAX HP true damage!")
            print("!" * 60)
            input("Press Enter...")

            wedge = _make_wedge()
            elist.append(wedge)
            ctx["wedge_active"] = True

        # Phase 1 Pillar
        if ctx["phase"] == 1 and not ctx["pillar_active"]:
            ctx["pillar_turn_counter"] += 1
            if ctx["pillar_turn_counter"] >= 3:
                ctx["pillar_turn_counter"] = 0
                ctx["pillar_active"] = True
                pillar = _make_pillar()
                elist.append(pillar)
                print("\n" + "═" * 55)
                print("⚡ [HEAVEN PILLAR]  A crystalline spire erupts from the floor!")
                print("Destroy it to shatter Yinglong's divine scales and deal")
                print("FULL damage for 3 turns! (Shattered Heaven buff)")
                print("═" * 55)

    # ── Custom HUD ──────────────────────────────────────────────────
    def custom_hud(ctx, elist):
        phase_label = {1: "I — Dragon Descends", 2: "II — Devoured",
                       3: "III — Resurgent", 4: "IV — Immortal Rage"}.get(ctx["phase"], "")
        gimmick = f"Phase {phase_label}"
        if ctx["immortal"]:
            gimmick += " | ☠ IMMORTAL"
        if _has_shattered_heaven(player):
            rem = next((b2["remaining"] for b2 in player.get("active_buffs", [])
                        if b2.get("source") == "shattered_heaven"), 0)
            gimmick += f" | ✦ Shattered Heaven ({rem} turns)"
        if ctx["bonus_dmg_next_turn"]:
            gimmick += " | ⚡ Wedge Deflected — bonus dmg ready!"

        if not _has_shattered_heaven(player):
            print("  ⚠ Yinglong's divine scales resist 60% of your damage.")
        if ctx["immortal"] and ctx.get("wedge_active"):
            print("  ☠ Yinglong is IMMORTAL while the Heaven Pinning Wedge exists!")
        for e in elist:
            if _is_pillar(e):
                print("  ⚡ Heaven Pillar: Destroy it to break Yinglong's scales!")
            elif _is_wedge(e):
                print("  ⚡ Heaven Pinning Wedge: Destroy it to strip Immortality!")

        print_combat_hud(player, elist, header=f"Superboss: Heaven-Banished Dragon Yinglong | {gimmick}")

    def player_action_override(ctx):
        action = input("Choose: ").strip().lower()
        ctx["defending_this_turn"] = (action == "d")
        return action

    def on_kill_hook(target, elist, ctx):
        # Handle the custom Phase 4 Wedge destruction backlash
        if target.get("key") == WEDGE_KEY or target.get("name") == "Heaven Pinning Wedge":
            b = next((e for e in elist if _is_boss(e)), None)
            if b:
                b["_allow_hp_drop"] = True
                backlash_dmg = int(b["max_hp_total"] * WEDGE_BOUNCE_PCT)
                b["hp"] -= backlash_dmg
                b["hp_lock_threshold"] = b["hp"] # Update the locked floor threshold
                b["_allow_hp_drop"] = False
                
                ctx["immortal"] = False
                ctx["wedge_active"] = False
                b["str_mod"] = b["base_str_mod"]
                
                print("\n" + "✦" * 55)
                print(f"💥 The Heaven Pinning Wedge shatters! Backlash deals {backlash_dmg} true damage to Yinglong!")
                print(f"🐉 Yinglong's immortality SHATTERS! HP forced down to {b['hp']}/{b['max_hp_total']}!")
                print("✦" * 55)
            return

        if _is_pillar(target):
            ctx["pillar_active"] = False
            result = _apply_shattered_heaven(player, turns=3)
            print("\n✦ Heaven Pillar shattered!")
            if result == "applied":
                print("SHATTERED HEAVEN — you deal full damage to Yinglong for 3 turns!")
            else:
                print("SHATTERED HEAVEN refreshed — full damage for 3 more turns!")

    def enemy_turn_hook(enemy, ctx, pl, p_con, defending):
        if _is_pillar(enemy):
            print(f"  (The Heaven Pillar pulses — it does not attack.)")
            return 0, True, None, 1.0, 0

        if _is_wedge(enemy):
            print(f"  (The Heaven Pinning Wedge hums ominously at turn-end...)")
            return 0, True, None, 1.0, 0

        immortal_bonus = int(enemy["str_mod"] * (IMMORTAL_DMG_MULT - 1.0)) if ctx["immortal"] else 0

        def dragon_extra(e, p, dmg):
            msgs = []
            if dmg > 0 and random.random() < 0.30:
                if apply_weaken(p, str_penalty=3, duration=2) == "applied":
                    msgs.append("🐉 Heaven's Judgment — your strength crumbles! (STR -3, 2 turns)")
            return "\n".join(msgs) if msgs else None

        return 1, False, dragon_extra, 1.0, immortal_bonus

    def post_round_hook(ctx, elist):
        if _has_shattered_heaven(player):
            expired = _tick_shattered_heaven(player)
            if expired:
                print("\n✦ Shattered Heaven fades — Yinglong's divine scales reassert!")

        wedge = next((e for e in elist if _is_wedge(e) and e["hp"] > 0), None)
        if wedge:
            max_hp = player_max_hp(player)
            print("\n" + "✦" * 55)
            print("⚡ Heaven Pinning Wedge fires at turn-end!")
            if ctx["defending_this_turn"]:
                print("You DEFENDED — the Wedge's energy scatters harmlessly!")
                bonus = int(max_hp * WEDGE_HP_DMG_PCT)
                ctx["bonus_dmg_next_turn"] = True
                print(f"Deflected power stored — +{bonus} bonus true damage on your next strike!")
            else:
                wedge_dmg = int(max_hp * WEDGE_HP_DMG_PCT)
                player["current_hp"] -= wedge_dmg
                print(f"Pure divine force — {wedge_dmg} unblockable damage to {player['name']}!")
                for ally in player.get("allies", []):
                    if ally.get("current_hp", 0) > 0:
                        if ally.pop("defending_this_turn", False):
                            print(f"{ally['name']} DEFENDED — the Wedge's energy is deflected from them!")
                        else:
                            ally_dmg = int(ally["max_hp"] * WEDGE_HP_DMG_PCT)
                            ally["current_hp"] -= ally_dmg
                            print(f"Pure divine force — {ally_dmg} unblockable damage to {ally['name']}!")
                if player["current_hp"] <= 0:
                    print(f"{player['name']} is pinned to heaven and cannot continue!")
                    return "dead"
                    
            # Wrap standard wedge dictionaries into OneHitWedgeDict instances to enforce 1-hit KO limits
            for i, e in enumerate(elist):
                if (e.get("key") == WEDGE_KEY or e.get("name") == "Heaven Pinning Wedge") and not isinstance(e, OneHitWedgeDict):
                    wrapped_wedge = OneHitWedgeDict(e)
                    wrapped_wedge["hp"] = 1
                    wrapped_wedge["max_hp"] = 1
                    elist[i] = wrapped_wedge
            print("✦" * 55)
            ctx["defending_this_turn"] = False

    # Resistance handling
    original_con = boss.get("con_mod", 0)

    def _set_boss_resistance(ctx, elist):
        b = next((e for e in elist if _is_boss(e)), None)
        if not b: return
        
        # Absolute immunity blocking
        if ctx.get("immortal") and ctx.get("wedge_active"):
            b["con_mod"] = 9999
            return

        # Regular Divine Scales logic
        if _has_shattered_heaven(player):
            b["con_mod"] = original_con
        else:
            b["con_mod"] = original_con + 12

    _original_pre = pre_player_hook
    def pre_player_hook_wrapped(ctx, elist):
        _set_boss_resistance(ctx, elist)
        # Safely wrap to avoid NoneType invocation
        if _original_pre:
            return _original_pre(ctx, elist)

    # ─────────────────────────────────────────────────────────────────
    result = superboss_combat_loop(
        player, enemies, floor, "Heaven-Banished Dragon Yinglong", context,
        pre_player_hook=pre_player_hook_wrapped,
        custom_hud_hook=custom_hud,
        on_kill_hook=on_kill_hook,
        on_player_hit_hook=on_player_hit_hook,
        player_action_override=player_action_override,
        enemy_turn_hook=enemy_turn_hook,
        post_round_hook=post_round_hook,
    )

    boss["con_mod"] = original_con

    if result == "victory":
        print("\n" + "═" * 60)
        print("Yinglong collapses. The wound in heaven slowly seals shut.")
        print("As the colossal form dissolves into cloud and lightning,")
        print("a soft rain falls — the first rain in this place in")
        print("a thousand years. You stand in it, breathing.")
        print("═" * 60)

    return result