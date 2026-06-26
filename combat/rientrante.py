# combat/rientrante.py – Rientrante, the Frostbound / Truth Unveiled superboss
import random
from combat.stats import enemy_stats, compute_player_stats
from combat.combat_ui import print_combat_hud
from combat.superboss_common import superboss_combat_loop
from combat.status_effects import apply_bleed, apply_blind
from combat.ally import get_alive_allies

BOSS_KEY = "rientrante_frostbound"
SHARD_KEY = "frost_shard"
EYE_KEY = "eye_of_truth"
ARM_KEY = "frozen_arm"


class FrostboundDict(dict):
    """Custom dict that intercepts HP changes to implement:
    - Frozen Shell: absorbs damage into shell_hp first
    - damage_taken_mult: multiplies incoming damage
    Executes (hp = 0) bypass the shell entirely.
    """
    def __setitem__(self, key, value):
        if key == "hp" and "hp" in self and value < self["hp"]:
            is_execute = (value == 0)

            # 1. Shell absorption
            if not is_execute and "shell_hp" in self and self["shell_hp"] > 0:
                dmg = self["hp"] - value
                shell = self["shell_hp"]
                absorbed = min(dmg, shell)
                self["shell_hp"] = shell - absorbed
                remaining = dmg - absorbed
                if self["shell_hp"] <= 0 and shell > 0:
                    print(
                        "\n[CRACK] The frozen shell shatters! "
                        "Rientrante staggers forward, exposed!"
                    )
                if absorbed > 0:
                    print(f"  [Frozen Shell absorbs {absorbed} damage]")
                if remaining > 0:
                    value = self["hp"] - remaining
                else:
                    value = self["hp"]

            # 2. Damage multipliers
            if "damage_taken_mult" in self and value < self["hp"]:
                dmg = self["hp"] - value
                mult = self.get("damage_taken_mult", 1.0)
                if mult != 1.0:
                    dmg = max(0, int(dmg * mult))
                    value = self["hp"] - dmg

        super().__setitem__(key, value)


def _spawn_shards(player, count=3):
    shards = []
    for _ in range(count):
        s = enemy_stats(SHARD_KEY, player)
        s["key"] = SHARD_KEY
        s["max_hp"] = s["hp"]
        shards.append(s)
    return shards


def _spawn_eye(player):
    eye = enemy_stats(EYE_KEY, player)
    eye["key"] = EYE_KEY
    eye["max_hp"] = eye["hp"]
    return eye


def _spawn_arm(player):
    arm = enemy_stats(ARM_KEY, player)
    arm["key"] = ARM_KEY
    arm["max_hp"] = arm["hp"]
    return arm


def _glacial_pulse(boss, player):
    """Phase 1: Every 3rd boss turn, AoE frost damage + blind chance."""
    print("\n❄️  GLACIAL PULSE! The air itself freezes solid!")
    allies = get_alive_allies(player)
    p_str, p_con, p_dex, p_ler, p_wis, p_cha = compute_player_stats(player)
    targets = [player] + allies
    for t in targets:
        if t.get("current_hp", 0) <= 0:
            continue
        dmg = max(1, random.randint(3, 8) + boss["str_mod"] // 2 - p_con // 3)
        t_res = t.get("elemental_res", {})
        water_res = t_res.get("water", 1.0)
        dmg = max(1, int(dmg * water_res))
        t["current_hp"] -= dmg
        print(f"  {t.get('name', 'You')} takes {dmg} frost damage!")
        if random.random() < 0.5:
            apply_blind(t, duration=1)
            print(f"  {t.get('name', 'You')}'s vision ices over!")
        if t["current_hp"] <= 0 and t is player:
            return "dead"
    return None


def _shard_explosion(shards, player):
    """Shards explode, dealing damage and applying bleed to all party."""
    print("\n💥 [GIMMICK] The Frost Shards destabilize and explode!")
    allies = get_alive_allies(player)
    p_str, p_con, p_dex, p_ler, p_wis, p_cha = compute_player_stats(player)
    targets = [player] + allies
    for t in targets:
        if t.get("current_hp", 0) <= 0:
            continue
        dmg = random.randint(5, 10)
        t["current_hp"] -= dmg
        print(f"  {t.get('name', 'You')} takes {dmg} shrapnel damage!")
        apply_bleed(t, damage=3, duration=3)
        print(f"  {t.get('name', 'You')} is bleeding from frost wounds!")
        if t["current_hp"] <= 0 and t is player:
            return "dead"
    return None


def _revelation_beam(eye, player):
    """Eye of Truth attacks and blinds a random target."""
    print(f"\n👁️  {eye['name']} unleashes a REVELATION BEAM!")
    allies = get_alive_allies(player)
    targets = [player] + allies
    alive_targets = [t for t in targets if t.get("current_hp", 0) > 0]
    if not alive_targets:
        return None
    target = random.choice(alive_targets)
    p_str, p_con, p_dex, p_ler, p_wis, p_cha = compute_player_stats(player)
    if target is player:
        t_con = p_con
    else:
        t_con = target["attributes"].get("Constitution", 0)
    dmg = max(1, random.randint(4, 10) + eye["str_mod"] - t_con)
    target["current_hp"] -= dmg
    print(f"  The beam strikes {target.get('name', 'You')} for {dmg} damage!")
    apply_blind(target, duration=2)
    print(f"  {target.get('name', 'You')} is blinded by terrible truth!")
    if target["current_hp"] <= 0 and target is player:
        return "dead"
    return None


def _frozen_burst(arm, player):
    """An arm explodes on death, dealing AoE damage."""
    print(f"\n💨 {arm['name']} shatters in a FROZEN BURST!")
    allies = get_alive_allies(player)
    p_str, p_con, p_dex, p_ler, p_wis, p_cha = compute_player_stats(player)
    targets = [player] + allies
    for t in targets:
        if t.get("current_hp", 0) <= 0:
            continue
        dmg = max(1, random.randint(3, 8) + arm["str_mod"] * 2 - p_con // 2)
        t["current_hp"] -= dmg
        print(f"  {t.get('name', 'You')} takes {dmg} frost burst damage!")
        if t["current_hp"] <= 0 and t is player:
            return "dead"
    return None


def _trigger_phase2(ctx, elist, boss, player):
    """Transition to Phase 2."""
    print("\n" + "!" * 60)
    print("[PHASE 2] The ice cracks. Something terrible emerges.")
    print("Rientrante's shell splits open, revealing a form of absolute truth.")
    print("The Eye of Truth opens. Frozen Arms rise from the ice.")
    print("!" * 60)
    input("Press Enter to confront the truth...")

    ctx["phase"] = 2
    ctx["phase2_triggered"] = True

    # Transform boss
    boss["name"] = "Rientrante, Truth Unveiled"
    boss["str_mod"] = boss.get("str_mod", 0) + 3
    boss["con_mod"] = boss.get("con_mod", 0) + 1
    boss["dex_mod"] = max(0, boss.get("dex_mod", 0) - 2)

    # Spawn Eye and Arms
    eye = _spawn_eye(player)
    elist.append(eye)
    for _ in range(2):
        arm = _spawn_arm(player)
        elist.append(arm)
    ctx["arms_alive"] = 2
    ctx["eye_alive"] = True

    # Truth Shield: 50% damage reduction while Eye is alive
    boss["damage_taken_mult"] = 0.5
    print(
        "\n[TRUTH SHIELD] The Eye of Truth protects Rientrante! "
        "(50% damage reduction)"
    )


def combat_rientrante(player, floor=None):
    """Main Rientrante superboss encounter."""
    boss = enemy_stats(BOSS_KEY, player)
    boss = FrostboundDict(boss)
    boss["max_hp"] = boss["hp"]
    boss["shell_hp"] = int(boss["max_hp"] * 0.30)
    enemies = [boss]

    print("\n" + "=" * 60)
    print("The temperature plummets. Your breath crystallizes in the air.")
    print("A towering figure of jagged ice and frost emerges — its eyes")
    print("glow with a pale, merciless light. The ground freezes beneath it.")
    print(f"\nRientrante, the Frostbound — HP: {boss['hp']} (Shell: {boss['shell_hp']})")
    print("=" * 60)
    input("\nPress Enter to face the Frostbound...")

    context = {
        "phase": 1,
        "shell_broken": False,
        "shards_spawned": False,
        "shard_timer": 0,
        "glacial_counter": 0,
        "phase2_triggered": False,
        "eye_alive": False,
        "arms_alive": 0,
        "revelation_counter": 0,
        "core_exposed_turns": 0,
        "truth_shattered_turns": 0,
        "shell_cracked_turns": 0,
    }

    # ── pre_player_hook ───────────────────────────────────────────────────
    def pre_player_hook(ctx, elist):
        b = next((e for e in elist if e.get("key") == BOSS_KEY), None)
        if not b:
            return None

        # Detect shell break and apply buff
        if not ctx["shell_broken"] and b.get("shell_hp", 0) <= 0:
            ctx["shell_broken"] = True
            b["str_mod"] = b.get("str_mod", 0) + 2
            b["con_mod"] = max(0, b.get("con_mod", 0) - 2)
            ctx["shell_cracked_turns"] = 3
            print(
                "\n[SHELL BROKEN] Rientrante's shell is shattered! "
                "It fights with desperate fury!"
            )

        # Phase 1: Shard spawn at 65% HP
        if (
            ctx["phase"] == 1
            and not ctx["shards_spawned"]
            and not ctx["phase2_triggered"]
        ):
            if b["hp"] <= int(b["max_hp"] * 0.65):
                print("\n[GIMMICK] Rientrante's shell fractures!")
                print("Three Frost Shards emerge from the cracks!")
                ctx["shards_spawned"] = True
                ctx["shard_timer"] = 4
                shards = _spawn_shards(player, 3)
                for s in shards:
                    elist.append(s)

        # Phase 2 trigger at 50% HP
        if ctx["phase"] == 1 and not ctx["phase2_triggered"]:
            if b["hp"] <= int(b["max_hp"] * 0.50):
                _trigger_phase2(ctx, elist, b, player)

        # Shard timer
        if ctx["shards_spawned"] and ctx["shard_timer"] > 0:
            shards = [e for e in elist if e.get("key") == SHARD_KEY and e["hp"] > 0]
            if shards:
                ctx["shard_timer"] -= 1
                if ctx["shard_timer"] <= 0:
                    result = _shard_explosion(shards, player)
                    for s in shards:
                        s["hp"] = 0
                    ctx["shards_spawned"] = False
                    if result == "dead":
                        return "dead"
                    # Boss empowered by explosion
                    b["str_mod"] = b.get("str_mod", 0) + 2
                    ctx["shell_cracked_turns"] = 3
                    print("Rientrante absorbs the explosion — empowered!")
            else:
                ctx["shards_spawned"] = False
                ctx["shard_timer"] = 0

        return None

    # ── custom_hud_hook ────────────────────────────────────────────────────
    def custom_hud_hook(ctx, elist):
        b = next((e for e in elist if e.get("key") == BOSS_KEY), None)
        lines = []
        if b:
            if b.get("shell_hp", 0) > 0:
                lines.append(f"❄️ Shell: {b['shell_hp']}")
            if ctx["eye_alive"]:
                lines.append("👁️ Shield: Active")
            elif ctx["phase"] == 2:
                lines.append("👁️ Shield: Broken")
            if ctx["shell_cracked_turns"] > 0:
                lines.append(f"🧊 Crack: {ctx['shell_cracked_turns']}t")
            if ctx["core_exposed_turns"] > 0:
                lines.append(f"⚠️ Core: {ctx['core_exposed_turns']}t")
            if ctx["truth_shattered_turns"] > 0:
                lines.append(f"💔 Truth: {ctx['truth_shattered_turns']}t")
        if lines:
            print("  " + " | ".join(lines))
        print_combat_hud(player, elist, header="Superboss: Rientrante")

    # ── on_kill_hook ───────────────────────────────────────────────────────
    def on_kill_hook(target, elist, ctx):
        key = target.get("key")

        if key == SHARD_KEY:
            shards_alive = any(
                e.get("key") == SHARD_KEY and e["hp"] > 0 for e in elist
            )
            if not shards_alive and ctx["shards_spawned"]:
                ctx["shards_spawned"] = False
                ctx["shard_timer"] = 0
                print("\n[GIMMICK] All Frost Shards destroyed!")
                b = next(
                    (e for e in elist if e.get("key") == BOSS_KEY), None
                )
                if b and ctx["phase"] == 1:
                    print("Rientrante is exposed! Vulnerable core revealed!")
                    b["damage_taken_mult"] = 1.25
                    ctx["shell_cracked_turns"] = 2

        elif key == ARM_KEY:
            result = _frozen_burst(target, player)
            ctx["arms_alive"] = max(0, ctx["arms_alive"] - 1)
            arms_alive = sum(
                1 for e in elist if e.get("key") == ARM_KEY and e["hp"] > 0
            )
            if arms_alive == 0 and ctx["phase"] == 2:
                print(
                    "\n[GIMMICK] Both Frozen Arms destroyed! "
                    "Rientrante's core is exposed!"
                )
                b = next(
                    (e for e in elist if e.get("key") == BOSS_KEY), None
                )
                if b:
                    b["damage_taken_mult"] = 1.5
                    ctx["core_exposed_turns"] = 3
            if result == "dead":
                # Signal via context; end-of-round check will catch it
                ctx["player_dead_from_burst"] = True

        elif key == EYE_KEY:
            ctx["eye_alive"] = False
            print("\n[GIMMICK] The Eye of Truth shatters! The truth is broken!")
            b = next(
                (e for e in elist if e.get("key") == BOSS_KEY), None
            )
            if b:
                b["damage_taken_mult"] = 1.5
                ctx["truth_shattered_turns"] = 3

    # ── enemy_turn_hook ────────────────────────────────────────────────────
    def enemy_turn_hook(enemy, ctx, pl, p_con, defending):
        key = enemy.get("key")

        # Phase 1 boss
        if key == BOSS_KEY and ctx["phase"] == 1:
            ctx["glacial_counter"] += 1

            # Glacial Pulse every 3 turns
            if ctx["glacial_counter"] >= 3:
                ctx["glacial_counter"] = 0
                result = _glacial_pulse(enemy, pl)
                if result == "dead":
                    return "dead"
                # After pulse, still gets a normal attack
                extra = None
                if random.random() < 0.4:
                    def ice_wound(e, p, dmg):
                        if dmg > 0 and random.random() < 0.5:
                            apply_bleed(p, damage=3, duration=3)
                            return (
                                "❄️ Frost wounds bleed into your veins! "
                                "(Bleed 3/3)"
                            )
                        return None

                    extra = ice_wound
                return 1, False, extra, 1.0, 0

            # Standard attack with ice wound chance
            extra = None
            if random.random() < 0.4:
                def ice_wound(e, p, dmg):
                    if dmg > 0 and random.random() < 0.5:
                        apply_bleed(p, damage=3, duration=3)
                        return (
                            "❄️ Frost wounds bleed into your veins! "
                            "(Bleed 3/3)"
                        )
                    return None

                extra = ice_wound
            return 1, False, extra, 1.0, 0

        # Phase 2 boss
        if key == BOSS_KEY and ctx["phase"] == 2:
            actions = 2 if (ctx["eye_alive"] and ctx["arms_alive"] > 0) else 1
            extra = None
            if random.random() < 0.4:
                def truth_wound(e, p, dmg):
                    if dmg > 0:
                        apply_bleed(p, damage=4, duration=3)
                        return "👁️ The truth cuts deep! (Bleed 4/3)"
                    return None

                extra = truth_wound
            return actions, False, extra, 1.0, 0

        # Eye of Truth
        if key == EYE_KEY:
            ctx["revelation_counter"] += 1
            if ctx["revelation_counter"] % 2 == 0:
                result = _revelation_beam(enemy, pl)
                if result == "dead":
                    return "dead"
                return 0, True, None, 1.0, 0
            return 1, False, None, 1.0, 0

        # Frost Shard / Frozen Arm standard attack
        return 1, False, None, 1.0, 0

    def _recalc_damage_mult(ctx, boss):
        """Set the correct damage_taken_mult based on current active debuffs."""
        if ctx["core_exposed_turns"] > 0 or ctx["truth_shattered_turns"] > 0:
            boss["damage_taken_mult"] = 1.5
        elif ctx["shell_cracked_turns"] > 0:
            boss["damage_taken_mult"] = 1.25
        elif ctx["eye_alive"]:
            boss["damage_taken_mult"] = 0.5
        else:
            boss["damage_taken_mult"] = 1.0

    # ── post_round_hook ────────────────────────────────────────────────────
    def post_round_hook(ctx, elist):
        # Shell cracked countdown
        if ctx.get("shell_cracked_turns", 0) > 0:
            ctx["shell_cracked_turns"] -= 1
            if ctx["shell_cracked_turns"] == 0:
                b = next(
                    (e for e in elist if e.get("key") == BOSS_KEY), None
                )
                if b:
                    _recalc_damage_mult(ctx, b)
                    print("\n[CRACK FADES] Rientrante's vulnerability fades.")

        # Core exposed countdown
        if ctx.get("core_exposed_turns", 0) > 0:
            ctx["core_exposed_turns"] -= 1
            if ctx["core_exposed_turns"] == 0:
                b = next(
                    (e for e in elist if e.get("key") == BOSS_KEY), None
                )
                if b:
                    _recalc_damage_mult(ctx, b)
                    print("\n[CORE] Rientrante's core vulnerability fades.")

        # Truth shattered countdown
        if ctx.get("truth_shattered_turns", 0) > 0:
            ctx["truth_shattered_turns"] -= 1
            if ctx["truth_shattered_turns"] == 0:
                b = next(
                    (e for e in elist if e.get("key") == BOSS_KEY), None
                )
                if b:
                    _recalc_damage_mult(ctx, b)
                    print("\n[TRUTH] The shattered truth mends partially.")

        # Safety: check if player died from burst
        if ctx.get("player_dead_from_burst"):
            if player["current_hp"] <= 0:
                return "dead"

        return None

    result = superboss_combat_loop(
        player,
        enemies,
        floor,
        "Rientrante, the Frostbound",
        context,
        pre_player_hook=pre_player_hook,
        custom_hud_hook=custom_hud_hook,
        on_kill_hook=on_kill_hook,
        enemy_turn_hook=enemy_turn_hook,
        post_round_hook=post_round_hook,
    )

    if result == "victory":
        print("\n" + "~" * 55)
        print("The ice shatters. The truth dissolves. Rientrante falls.")
        print("In the silence that follows, a cold star flickers and dies.")
        print("~" * 55)

    return result
