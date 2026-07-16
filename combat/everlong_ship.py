# combat/everlong_ship.py – The Everlong Ship superboss encounter
#
# MECHANIC OVERVIEW:
# ─────────────────
# Phase 1 (Crew Endures)
#   • Captain + 4 random crew members. Captain takes heavily reduced damage
#     via a Ghostly Hull that scales with remaining crew morale.
#   • Each defeated crew member reduces the Captain's damage reduction by 10%.
#   • When a crew member falls, a new one immediately boards.
#   • If the Captain is attacked, he ripostes (max 2/turn).
#   • The Captain's Parrot marks one party member per round. If that target
#     does not Defend on their turn, a cannon fires at round-end for heavy
#     damage and stuns them next turn.
#
# Phase 2 (Captain's Rage) — triggered after 10 crew deaths total
#   • Remaining crew fade into mist. No more replacements.
#   • Riposte removed. Captain acts twice per turn.
#   • Parrot continues its cannon mechanic.
#   • "The captain goes down with the ship... and so his men followed him."

import random
from combat.stats import enemy_stats, compute_player_stats
from combat.player_actions import handle_player_turn
from combat.combat_ui import format_enemy_status_line, print_superboss_header, print_combat_hud
from combat.superboss_common import superboss_combat_loop
from combat.ally import get_alive_allies, get_active_allies
from character import player_max_hp
from combat.combat_io import c_print, c_input, c_clear
from combat.helpers import format_damage_msg


BOSS_KEY = "captain_everlong_ship"
CREW_KEYS = [
    "seaman_everlong",
    "gunner_everlong",
    "brawler_everlong",
    "boatswain_everlong",
    "lookout_everlong",
]

CANNON_BASE_DAMAGE = 28


class CaptainDict(dict):
    """Custom dict that intercepts HP changes to apply damage reduction."""
    def __setitem__(self, key, value):
        if key == "hp" and "hp" in self and value < self["hp"]:
            dmg_reduction = self.get("captain_damage_reduction", 0.0)
            if dmg_reduction > 0 and not self.get("_allow_hp_drop"):
                dmg = self["hp"] - value
                reduced_dmg = int(dmg * (1.0 - dmg_reduction))
                if reduced_dmg < dmg:
                    c_print(f"  [GHOSTLY HULL] The Captain's cursed form deflects the blow! ({int(dmg_reduction*100)}% reduced)")
                value = self["hp"] - reduced_dmg
        super().__setitem__(key, value)


def _spawn_crew(player, pool=None):
    """Spawn a random crew member from the pool."""
    if pool is None:
        pool = CREW_KEYS
    key = random.choice(pool)
    crew = enemy_stats(key, player)
    crew["key"] = key
    crew["max_hp"] = crew["hp"]
    return crew


def _get_crew_count(elist):
    """Count living crew members in the enemy list."""
    return sum(1 for e in elist if e.get("key") in CREW_KEYS and e["hp"] > 0)


def _get_captain(elist):
    """Return the Captain enemy from the list, or None."""
    return next((e for e in elist if e.get("key") == BOSS_KEY), None)


def _pick_parrot_target(player):
    """Pick a random alive party member (active row) for the parrot to mark."""
    party = [player] + get_active_allies(player)
    if not party:
        return None
    return random.choice(party)


def combat_everlong_ship(player, floor=None, enemies=None):
    """Superboss: The Everlong Ship (Captain + Ghostly Crew).

    Args:
        enemies: Optional pre-created enemy list for GUI mode state sharing.
                 If provided, the first entry matching BOSS_KEY is wrapped in
                 CaptainDict and used as the boss. Otherwise a new boss and
                 crew are created.
    """
    if floor is None:
        loc = player.get("location", "")
        floor = player.get("city_floors", {}).get(loc, {}).get("floor")

    if enemies is None:
        base_boss = enemy_stats(BOSS_KEY, player)
        boss = CaptainDict(base_boss)
        boss["max_hp"] = boss["hp"]
        boss["captain_damage_reduction"] = 1.0  # 100% reduction
        boss["base_str_mod"] = boss.get("str_mod", 0)
        enemies = [boss]
        # Spawn initial crew
        for _ in range(4):
            enemies.append(_spawn_crew(player))
    else:
        # GUI mode: enemies list is shared with the CombatScreen renderer.
        # Find the boss, wrap in CaptainDict, and spawn crew if needed.
        boss = None
        for i, e in enumerate(enemies):
            if e.get("key") == BOSS_KEY:
                wrapped = CaptainDict(e)
                wrapped["max_hp"] = wrapped["hp"]
                wrapped["captain_damage_reduction"] = 1.0
                wrapped["base_str_mod"] = wrapped.get("str_mod", 0)
                enemies[i] = wrapped
                boss = wrapped
                break
        if boss is None:
            # Fallback: create the boss if not found in the shared list
            base_boss = enemy_stats(BOSS_KEY, player)
            boss = CaptainDict(base_boss)
            boss["max_hp"] = boss["hp"]
            boss["captain_damage_reduction"] = 1.0
            boss["base_str_mod"] = boss.get("str_mod", 0)
            enemies.append(boss)
        # Spawn initial crew alongside the shared boss
        for _ in range(4):
            enemies.append(_spawn_crew(player))

    c_print("\n" + "~" * 60)
    c_print("The air grows thick with salt and rot. Through the fog,")
    c_print("a ghostly vessel materializes — its sails tattered, its")
    c_print("hull gleaming with spectral light. A figure stands at the")
    c_print("prow, cutlass in hand, surrounded by a crew that should")
    c_print("have drowned centuries ago.")
    c_print(f"\nCaptain of the Everlong Ship — HP: {boss['hp']}")
    c_print("~" * 60)
    c_input("\nPress Enter to face the Everlong Ship...")

    context = {
        "phase": 1,
        "crew_defeated": 0,
        "riposte_count": 0,
        "parrot_target_name": None,
        "parrot_target_entity": None,
        "parrot_target_defended": False,
        "rally_cooldown": 3,  # First rally on turn 3
        "rally_active": False,
        "rally_turns_remaining": 0,
        "captain_actions": 1,
    }

    # ── on_player_hit_hook: Riposte when Captain is attacked ──────────
    def on_player_hit_hook(target, elist, ctx):
        if target.get("key") != BOSS_KEY:
            return
        if ctx["phase"] == 1 and ctx.get("riposte_count", 0) < 2:
            ctx["riposte_count"] = ctx.get("riposte_count", 0) + 1
            riposte_dmg = max(1, target.get("str_mod", 0) + random.randint(3, 6))
            player["current_hp"] -= riposte_dmg
            c_print(f"\n  ⚔ [RIPOSTE] " + format_damage_msg("Captain", player['name'], riposte_dmg, skill_name="Riposte"))
            if player["current_hp"] <= 0:
                c_print(f"  {player['name']} has been slain by the Captain's riposte!")

    # ── on_kill_hook: Crew death tracking and replacement ─────────────
    def on_kill_hook(target, elist, ctx):
        if target.get("key") not in CREW_KEYS:
            return

        ctx["crew_defeated"] = ctx.get("crew_defeated", 0) + 1
        captain = _get_captain(elist)
        if captain:
            new_reduction = max(0.0, 1.0 - (ctx["crew_defeated"] * 0.10))
            captain["captain_damage_reduction"] = new_reduction
            if new_reduction == 0.0:
                c_print(f"\n  [HULL BROKEN] The Captain's ghostly protection shatters! He is fully exposed!")
            else:
                c_print(f"\n  [CREW FALLS] A crewman falls! The Captain's hull weakens! ({int(new_reduction*100)}% reduction remaining)")

        # Replace crew in Phase 1
        if ctx["phase"] == 1:
            new_crew = _spawn_crew(player)
            enemies.append(new_crew)
            c_print(f"  [REINFORCEMENT] A {new_crew['name']} clambers aboard from the spectral depths!")

    # ── pre_player_hook: Parrot marks target, reset riposte ───────────
    def pre_player_hook(ctx, elist):
        # Reset riposte count at start of each round
        ctx["riposte_count"] = 0

        # Clear previous parrot target tags
        if ctx.get("parrot_target_entity"):
            ctx["parrot_target_entity"]["parrot_target"] = False
        for ally in get_active_allies(player):
            ally["parrot_target"] = False

        # Parrot picks a new target
        target = _pick_parrot_target(player)
        if target is player:
            ctx["parrot_target_name"] = "player"
        else:
            ctx["parrot_target_name"] = target["name"] if target else None
        ctx["parrot_target_entity"] = target
        ctx["parrot_target_defended"] = False

        # Mark the target with a visible tag
        if target:
            target["parrot_target"] = True

        if ctx["parrot_target_name"]:
            c_print(f"\n  🦜 [PARROT] SQUAWK! 'Fire the cannon! Fire at {target['name']}!'")

    # ── custom_hud_hook ──────────────────────────────────────────────
    def custom_hud_hook(ctx, elist):
        captain = _get_captain(elist)
        lines = []
        if captain:
            dr = captain.get("captain_damage_reduction", 0.0)
            if dr > 0:
                lines.append(f"⚓ Hull: {int(dr*100)}% DR")
            else:
                lines.append("⚓ Hull: BROKEN")
        lines.append(f"☠ Crew Defeated: {ctx['crew_defeated']}/10")
        if ctx["phase"] == 2:
            lines.append("⚡ RAGE: Double Actions!")
        if ctx.get("rally_active"):
            lines.append(f"📯 Rally: {ctx['rally_turns_remaining']}t")
        if ctx.get("parrot_target_name"):
            target_name = "You" if ctx["parrot_target_name"] == "player" else ctx["parrot_target_name"]
            lines.append(f"🦜 CANNON → {target_name}")
        if lines:
            c_print("  " + " | ".join(lines))
        print_combat_hud(player, elist, header="Superboss: The Everlong Ship")

    # ── player_action_override: Track defending for parrot ────────────
    def player_action_override(ctx):
        action = c_input("Choose: ").strip().lower()
        # Check if the marked target is the player and they chose defend
        if ctx.get("parrot_target_name") == "player" and action == "d":
            ctx["parrot_target_defended"] = True
            c_print("  🦜 [PARROT] You brace for the cannon shot — the cannonball SPLASHES harmlessly!")
        return action

    # ── enemy_turn_hook: Captain rally + crew behavior ───────────────
    def enemy_turn_hook(enemy, ctx, pl, p_con, defending, **kwargs):
        if enemy.get("key") == BOSS_KEY:
            # Rally cooldown
            ctx["rally_cooldown"] = ctx.get("rally_cooldown", 0) - 1

            # Check if rally should activate
            if ctx["rally_cooldown"] <= 0 and not ctx.get("rally_active") and ctx["phase"] == 1:
                ctx["rally_cooldown"] = 5
                ctx["rally_active"] = True
                ctx["rally_turns_remaining"] = 2
                c_print("\n  ⚓ [CREW RALLY] The Captain raises his cutlass!")
                c_print("  'Stand fast, ye dogs! For the Everlong!'")
                # Buff all enemies: +2 STR, +2 DEX for 2 turns
                for e in enemies:
                    if e.get("key") in ([BOSS_KEY] + CREW_KEYS) and e["hp"] > 0:
                        e.setdefault("active_buffs", []).append({
                            "stat": "Strength",
                            "value": 2,
                            "remaining": 2,
                            "source": "captain_rally",
                        })
                        e.setdefault("active_buffs", []).append({
                            "stat": "Dexterity",
                            "value": 2,
                            "remaining": 2,
                            "source": "captain_rally",
                        })
                c_print("  The crew's spectral morale surges — +2 STR, +2 DEX for all undead sailors!")

            actions = ctx.get("captain_actions", 1)
            extra = None
            if random.random() < 0.35:
                def captain_curse(e, p, dmg):
                    if dmg > 0:
                        from combat.status_effects import apply_curse
                        result = apply_curse(p)
                        if result == "applied":
                            return f"⚓ The Captain's curse of the sea settles on {p['name']}! All attributes reduced!"
                        return None
                extra = captain_curse
            return actions, False, extra, 1.0, 0

        # Crew behavior: standard undead attacks
        return 1, False, None, 1.0, 0

    # ── post_round_hook: Cannon fire, rally tick, phase check ────────
    def post_round_hook(ctx, elist):
        # Check cannon fire on non-defended target
        if ctx.get("parrot_target_entity") and not ctx.get("parrot_target_defended"):
            target = ctx["parrot_target_entity"]
            target_hp = target.get("current_hp", target.get("hp", 0))
            if target_hp > 0:
                # Check if ally defended on their turn
                if target is not player and target.get("defending_this_turn"):
                    ctx["parrot_target_defended"] = True
                    c_print(f"\n  🦜 [PARROT] {target['name']} braces for the cannon shot — the cannonball SPLASHES harmlessly!")

        if ctx.get("parrot_target_entity") and not ctx.get("parrot_target_defended"):
            target = ctx["parrot_target_entity"]
            target_hp = target.get("current_hp", target.get("hp", 0))
            if target_hp > 0:
                captain = _get_captain(elist)
                str_bonus = captain.get("str_mod", 0) if captain else 0
                cannon_dmg = CANNON_BASE_DAMAGE + str_bonus * 2 + random.randint(0, 6)
                if target is player:
                    player["current_hp"] -= cannon_dmg
                    c_print(f"\n  💥 [CANNON FIRE] " + format_damage_msg("Parrot's Cannon", "You", cannon_dmg, skill_name="Cannon Fire"))
                    c_print(f"  You are STUNNED by the blast and lose your next turn!")
                    ctx["skip_player_turn"] = True
                    if player["current_hp"] <= 0:
                        c_print(f"  {player['name']} has been slain by the cannon fire!")
                        return "dead"
                else:
                    target["current_hp"] -= cannon_dmg
                    target["stunned"] = True
                    c_print(f"\n  💥 [CANNON FIRE] " + format_damage_msg("Parrot's Cannon", target['name'], cannon_dmg, skill_name="Cannon Fire"))
                    c_print(f"  {target['name']} is STUNNED by the blast and loses their next turn!")

        # Clear parrot target tag at end of round
        if ctx.get("parrot_target_entity"):
            ctx["parrot_target_entity"]["parrot_target"] = False
        for ally in get_active_allies(player):
            ally["parrot_target"] = False

        # Rally tick
        if ctx.get("rally_active") and ctx.get("rally_turns_remaining", 0) > 0:
            ctx["rally_turns_remaining"] -= 1
            if ctx["rally_turns_remaining"] <= 0:
                ctx["rally_active"] = False
                c_print("\n  [RALLY FADES] The Captain's rally cry echoes into silence.")
                # Remove rally buffs from enemies
                for e in elist:
                    if e.get("active_buffs"):
                        e["active_buffs"] = [b for b in e["active_buffs"] if b.get("source") != "captain_rally"]

        # Phase 2 transition
        if ctx["phase"] == 1 and ctx["crew_defeated"] >= 10:
            ctx["phase"] = 2
            ctx["captain_actions"] = 2
            c_print("\n" + "!" * 60)
            c_print("[PHASE 2] The Captain's crew is shattered!")
            c_print("The ghostly sailors fade into mist, their wails swallowed")
            c_print("by the fog. The Captain stands alone, his eyes burning")
            c_print("with a fury that has sailed ten thousand storms.")
            c_print()
            c_print("'The captain goes down with the ship...")
            c_print(" and so his men followed him.'")
            c_print()
            c_print("The Everlong Ship begins its journey again...")
            c_print("!" * 60)
            c_input("Press Enter to continue the final confrontation...")

            # Remove remaining crew
            for e in elist[:]:
                if e.get("key") in CREW_KEYS:
                    e["hp"] = 0

            # Captain fully exposed
            captain = _get_captain(elist)
            if captain:
                captain["captain_damage_reduction"] = 0.0

        # Safety: check player death
        if player["current_hp"] <= 0:
            c_print(f"\n  {player['name']} has been slain.")
            return "dead"

        return None

    result = superboss_combat_loop(
        player, enemies, floor, "Captain of the Everlong Ship", context,
        pre_player_hook=pre_player_hook,
        custom_hud_hook=custom_hud_hook,
        on_kill_hook=on_kill_hook,
        on_player_hit_hook=on_player_hit_hook,
        player_action_override=player_action_override,
        enemy_turn_hook=enemy_turn_hook,
        post_round_hook=post_round_hook,
    )

    if result == "victory":
        # Guard: only award loot once per save
        if not player.get("boss_defeated_everlong_ship"):
            c_print("\n" + "~" * 60)
            c_print("The Captain's spectral form dissolves into sea-spray and mist.")
            c_print("The Everlong Ship groans, its haunted timbers finally at rest.")
            c_print("As the vessel fades beneath the waves, a single cutlass")
            c_print("glows with an eerie light — the Captain's authority,")
            c_print("now yours to wield.")
            c_print("~" * 60)

            # Award Cutlass of the Captain
            from resources.items import build_item
            from inventory_ui import prompt_acquire_item
            cutlass = build_item("cutlass_of_the_captain", "unique")
            c_print("\n  ⚓ You obtained: CUTLASS OF THE CAPTAIN (Unique) ⚓")
            prompt_acquire_item(player, cutlass)
            # Set defeated flag AFTER awarding loot
            player["boss_defeated_everlong_ship"] = True
        c_input("  Press Enter to continue...")

    return result
