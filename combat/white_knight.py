"""White Knight of the Fallen Empire — Pandemonium Floor 40 superboss.

Design doc: docs/white_knight_design.md

Three phases of accuracy-denial:
  P1 (100-65%): 55% passive dodge, no riposte.
  P2 (65-30%):  telegraphed "Oathguard" states (70% dodge, riposte <=2/round,
                first hit after activation guaranteed), partner flurries,
                Disarming Flourish (allies -20% hit rate, floor -35%),
                edge-triggered +25% DMG when 3+ party units are Exposed.
  P3 (<30%):    "Last Vigil" states add 50% skill dodge (telegraphed).

Ripostes apply Expose stacks to the attacker; each stack makes the Knight's
attacks ignore 10% CON (via ``enemy_attack_armor_mult``). At 6 stacks the
Knight consumes them for a sure-hit Judgment Burst (Defend halves).

Status resistance 0.75 lives in the YAML template (global status_res system).
Reward: Last Oath (unique rapier, Expose-on-hit) — granted on first victory.
"""
import random

from combat.combat_io import c_print, c_input
from combat.helpers import format_damage_msg
from combat.superboss_common import superboss_combat_loop
from combat.ally import get_active_allies
from combat.status_effects import absorb_damage

BOSS_KEY = "white_knight"
BOSS_NAME = "White Knight of the Fallen Empire"

# ── Tuning (see docs/white_knight_design.md §4.2) ──────────────────────────
P1_DODGE = 0.55
STATE_DODGE = 0.70
RECOVERY_DODGE = 0.35          # 1-turn negative-dodge window after states
RIPOSTE_CHANCE = 0.50
RIPOSTE_CAP = 2                # per round
ALLY_PENALTY = 0.20            # Disarming Flourish (floor 0.35 enforced in stats)
SKILL_DODGE_P3 = 0.50
EDGE_THRESHOLD = 3             # party units with >=1 Expose stack
EDGE_DMG = 0.25
EDGE_TURNS = 3
FLURRY_CHANCE = 0.40           # of neutral turns in P2/P3
BURST_STACKS = 6
EXPOSE_CAP = 6
BURST_MIN, BURST_MAX = 70, 100
P2_MIN_ROUNDS = 2              # completed rounds in P2 before it can end (anti-skip)


class _PhaseLockedKnight(dict):
    """HP-floor wrapper that prevents phase skips and one-shots.

    Phase 1 cannot drop below 65% max HP and Phase 2 cannot drop below 30%
    (floors match the phase thresholds). Phase 3 has no floor — the kill
    window. Floors lift only when pre_player_hook advances ``_wk_phase`` at
    round start, so every phase gets at least one full round on the field.
    Mirrors the CaptainDict interception pattern (everlong_ship.py).
    """

    def __setitem__(self, key, value):
        if key == "hp":
            value = self._phase_clamp(value)
        super().__setitem__(key, value)

    def _phase_clamp(self, value):
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return value
        max_hp = self.get("max_hp", 0) or 0
        if max_hp <= 0:
            return value
        phase = self.get("_wk_phase", 1)
        floor_pct = 0.65 if phase == 1 else (0.30 if phase == 2 else None)
        if floor_pct is None:
            return max(0, value)
        floor = max(1, int(max_hp * floor_pct))
        if numeric < floor:
            round_no = self.get("_wk_round", 0)
            if self.get("_wk_floor_msg_round") != round_no:
                self["_wk_floor_msg_round"] = round_no
                try:
                    from combat.combat_io import c_print
                    c_print("  ✋ The white porcelain holds — the phase bar is sealed.")
                except Exception:
                    pass
            return floor
        return value


def _party(player):
    return [player] + get_active_allies(player)


def _get_boss(enemies):
    return next((e for e in enemies if e.get("key") == BOSS_KEY), None)


def _armor_mult_for(unit):
    stacks = min(EXPOSE_CAP, unit.get("expose_stacks", 0))
    return max(0.4, 1.0 - 0.10 * stacks)


def _refresh_armor_mults(player):
    for m in [player] + player.get("allies", []):
        if "enemy_attack_armor_mult" in m or m.get("expose_stacks", 0) > 0:
            m["enemy_attack_armor_mult"] = _armor_mult_for(m)


def _set_dodge(boss, value, skill_dodge=0.0):
    """Update the Knight's dodge cap + visible evasion buff."""
    boss["dodge_cap_override"] = value
    boss["skill_dodge_chance"] = skill_dodge
    for b in boss.get("active_buffs", []):
        if b.get("source") == "wk_dodge":
            b["value"] = value
            break
    else:
        boss.setdefault("active_buffs", []).append({
            "type": "evasion", "value": value, "remaining": 999, "source": "wk_dodge",
        })


def _remove_buff(boss, source):
    boss["active_buffs"] = [b for b in boss.get("active_buffs", [])
                            if b.get("source") != source]


def _add_expose_stack(unit):
    unit["expose_stacks"] = min(EXPOSE_CAP, unit.get("expose_stacks", 0) + 1)
    unit["enemy_attack_armor_mult"] = _armor_mult_for(unit)
    return unit["expose_stacks"]


def combat_white_knight(player, floor=None, enemies=None):
    """Entry point — runs the White Knight encounter.

    ``enemies`` is mutated in place when provided (the GUI passes its shared
    list for live HUD rendering — wrapping the boss and HP changes must land
    on that same list).
    """
    if enemies is None:
        enemies = []
    boss = _get_boss(enemies)
    if boss is None:
        from combat.stats import enemy_stats
        boss = enemy_stats(BOSS_KEY, player)
        boss["max_hp"] = boss["hp"]
        boss = _PhaseLockedKnight(boss)
        enemies.append(boss)
    elif not isinstance(boss, _PhaseLockedKnight):
        wrapped = _PhaseLockedKnight(boss)
        for _i, _e in enumerate(enemies):
            if _e.get("key") == BOSS_KEY:
                enemies[_i] = wrapped
                break
        boss = wrapped

    # ── Combat-start setup ─────────────────────────────────────────────
    boss["_wk_phase"] = 1
    boss["_wk_round"] = 0
    _set_dodge(boss, P1_DODGE)
    boss["ally_accuracy_penalty"] = 0.0  # becomes 0.20 in Phase 2
    for m in [player] + player.get("allies", []):
        m.setdefault("expose_stacks", 0)
        m["enemy_attack_armor_mult"] = _armor_mult_for(m)
        m.pop("_skill_dodge_used", None)
        m.pop("_accuracy_penalty_used", None)

    context = {
        "phase": 1,
        "phase_entered_round": 1,
        "cadence": 0,
        "mode": "neutral",
        "riposte_count": 0,
        "first_hit_pending": False,
        "edge_armed": True,
        "edge_turns": 0,
        "round": 0,
    }

    # ── Hooks ──────────────────────────────────────────────────────────
    def pre_player_hook(ctx, elist):
        b = _get_boss(elist)
        if b is None or b["hp"] <= 0:
            return
        ctx["round"] += 1
        b["_wk_round"] = ctx["round"]

        hp_pct = b["hp"] / max(1, b["max_hp"])
        if ctx["phase"] == 1 and hp_pct <= 0.65:
            ctx["phase"] = 2
            ctx["cadence"] = 0
            ctx["phase_entered_round"] = ctx["round"]
            b["_wk_phase"] = 2
            b["ally_accuracy_penalty"] = ALLY_PENALTY
            _set_dodge(b, P1_DODGE)
            c_print("\n  ⚜ The White Knight plants their feet. \"Oathguard.\"")
            c_print("  ↠ States unlocked — strikes may be riposted (max 2/round).")
            c_print("  ↠ Disarming Flourish: allies suffer -20% hit rate against the Knight.")
        elif (ctx["phase"] == 2 and hp_pct <= 0.30
              and ctx["round"] - ctx.get("phase_entered_round", 1) >= P2_MIN_ROUNDS):
            ctx["phase"] = 3
            ctx["cadence"] = 0
            ctx["phase_entered_round"] = ctx["round"]
            b["_wk_phase"] = 3
            _set_dodge(b, P1_DODGE)
            c_print("\n  ⚜ The porcelain cracks — cold light pours through.")
            c_print("  ⚠ \"The last vigil begins.\" — Last Vigil states can read and slip skills!")

        # Edge-triggered oath banner (3+ party units exposed)
        exposed = sum(1 for m in _party(player) if m.get("expose_stacks", 0) >= 1)
        if exposed >= EDGE_THRESHOLD and ctx["edge_armed"]:
            ctx["edge_armed"] = False
            ctx["edge_turns"] = EDGE_TURNS
            _remove_buff(b, "wk_edge")
            b.setdefault("active_buffs", []).append({
                "type": "damage_boost", "value": EDGE_DMG,
                "remaining": EDGE_TURNS, "source": "wk_edge",
            })
            c_print(f"\n  🔺 Three are exposed — the oath burns brighter! "
                    f"(+{int(EDGE_DMG * 100)}% DMG, {EDGE_TURNS} rounds)")
        elif exposed < EDGE_THRESHOLD and not ctx["edge_armed"]:
            ctx["edge_armed"] = True  # re-arm after the count drops below 3

        if ctx["edge_turns"] > 0:
            ctx["edge_turns"] -= 1
            if ctx["edge_turns"] <= 0:
                _remove_buff(b, "wk_edge")
                c_print("  ↠ The oath-banner fades.")

        _refresh_armor_mults(player)
        ctx["riposte_count"] = 0

        # State cadence (P2/P3 only)
        if ctx["phase"] >= 2:
            ctx["cadence"] += 1
            if ctx["phase"] == 2:
                pattern = ["neutral", "neutral", "warn", "active", "active", "active", "recovery"]
            else:
                pattern = ["neutral", "neutral", "warn", "active", "active", "recovery"]
            mode = pattern[(ctx["cadence"] - 1) % len(pattern)]
            if mode != ctx["mode"]:
                _transition_mode(b, ctx, mode)

    def _transition_mode(b, ctx, mode):
        ctx["mode"] = mode
        if mode == "warn":
            _set_dodge(b, P1_DODGE)
            c_print("\n  ⚠ The White Knight raises their guard... (state incoming)")
        elif mode == "active":
            skill_dodge = SKILL_DODGE_P3 if ctx["phase"] == 3 else 0.0
            _set_dodge(b, STATE_DODGE, skill_dodge=skill_dodge)
            ctx["first_hit_pending"] = True
            name = "Last Vigil" if ctx["phase"] == 3 else "Oathguard"
            extra = " Skills can be read and slipped (50%)!" if skill_dodge else ""
            c_print(f"\n  🛡 [{name}] The blade turns aside attacks — ripostes live!{extra}")
        elif mode == "recovery":
            _set_dodge(b, RECOVERY_DODGE)
            c_print("\n  ⏳ The guard drops — negative-dodge window! STRIKE NOW!")
        else:
            _set_dodge(b, P1_DODGE)

    def on_player_hit_hook(target, elist, ctx, attacker=None):
        if target.get("key") != BOSS_KEY or target.get("hp", 0) <= 0:
            return
        if ctx.get("mode") != "active":
            return
        if ctx.get("riposte_count", 0) >= RIPOSTE_CAP:
            return
        attacker = attacker if attacker is not None else player
        guaranteed = ctx.get("first_hit_pending", False)
        ctx["first_hit_pending"] = False
        if not guaranteed and random.random() >= RIPOSTE_CHANCE:
            return
        ctx["riposte_count"] += 1

        dmg = max(1, 4 + random.randint(0, 4) + target.get("str_mod", 0) // 2)
        attacker["current_hp"] = max(0, attacker.get("current_hp", 0) - dmg)
        stacks = _add_expose_stack(attacker)
        who = attacker.get("name", "you")
        c_print("\n  ⚔ [RIPOSTE] " + format_damage_msg("White Knight", who, dmg, skill_name="Riposte"))
        c_print(f"  ⚖ Exposed! {who} — EXP×{stacks} "
                f"(Knight ignores {min(60, stacks * 10)}% CON vs them)")
        if attacker["current_hp"] <= 0:
            if attacker is player:
                c_print(f"  {who} has been slain by the riposte.")
            else:
                attacker["defeated"] = True

    def enemy_turn_hook(enemy, ctx, pl, p_con, defending, **kwargs):
        b = _get_boss([enemy])
        if b is None:
            return 1, False, None, 1.0, 0

        # Judgment Burst consumes the turn when a unit sits at 6 stacks
        ready = [m for m in _party(pl) if m.get("expose_stacks", 0) >= BURST_STACKS]
        if ready:
            target = max(ready, key=lambda m: m.get("expose_stacks", 0))
            _execute_burst(b, target, pl, defending)
            return 1, True, None, 1.0, 0

        # Unfocused flurry on neutral turns
        if ctx.get("mode") == "neutral" and random.random() < FLURRY_CHANCE:
            _execute_flurry(b, pl)
            return 1, True, None, 1.0, 0

        return 1, False, None, 1.0, 0

    def _execute_burst(b, target, pl, defending):
        stacks = target.get("expose_stacks", 0)
        target["expose_stacks"] = 0
        target["enemy_attack_armor_mult"] = 1.0
        dmg = random.randint(BURST_MIN, BURST_MAX) + 2 * b.get("str_mod", 0)
        is_defending = defending if target is pl else bool(target.get("defending_this_turn"))
        if is_defending:
            dmg = max(1, dmg // 2)
        dmg, absorbed = absorb_damage(target, dmg)
        target["current_hp"] = max(0, target.get("current_hp", 0) - dmg)
        who = target.get("name", "you")
        c_print(f'\n  ☀ "The oath is judged." — [JUDGMENT BURST] consumes {stacks} Expose stacks!')
        c_print("  " + format_damage_msg("White Knight", who, dmg, skill_name="Judgment Burst"))
        if absorbed:
            c_print(f"  {who}'s barrier absorbs {absorbed} damage.")
        if target.get("current_hp", 0) <= 0:
            if target is pl:
                c_print(f"  {who} has been slain by the judgment.")
            else:
                target["defeated"] = True
                c_print(f"  {who} has fallen.")

    def _execute_flurry(b, pl):
        living = [m for m in _party(pl) if m.get("current_hp", 0) > 0]
        if not living:
            return
        c_print('\n  ⚔ "Falling Star Flurry!" — the White Knight rides the light.')
        for _ in range(3):
            if not living:
                break
            t = random.choice(living)
            dmg = random.randint(10, 16) + max(0, b.get("str_mod", 0) // 2)
            res = t.get("elemental_res", {}).get("light", 1.0)
            dmg = max(1, int(dmg * res))
            t["current_hp"] = max(0, t.get("current_hp", 0) - dmg)
            c_print(f"  ✦ Light lance strikes {t.get('name', 'you')} — {dmg} dmg [LIGHT]")
            if t.get("current_hp", 0) <= 0:
                living = [m for m in living if m.get("current_hp", 0) > 0]
                if t is not pl:
                    t["defeated"] = True
                    c_print(f"  {t.get('name', 'they')} has fallen.")

    def custom_hud_hook(ctx, elist):
        b = _get_boss(elist)
        if b is None:
            return
        mode_label = {
            "neutral": "watchful", "warn": "guard rising",
            "active": "RIPOSTES LIVE", "recovery": "EXPOSED WINDOW",
        }.get(ctx["mode"], ctx["mode"])
        lines = [f"⚜ Phase {ctx['phase']} — {mode_label}"]
        if ctx["mode"] == "active":
            left = max(0, RIPOSTE_CAP - ctx["riposte_count"])
            lines.append(f"⚔ Ripostes left this round: {left}")
        if ctx["edge_turns"] > 0:
            lines.append(f"🔺 Oath banner: +{int(EDGE_DMG * 100)}% DMG ({ctx['edge_turns']} rounds)")
        stacks = [f"{m.get('name', 'you')}:{m.get('expose_stacks', 0)}"
                  for m in _party(player) if m.get("expose_stacks", 0) > 0]
        if stacks:
            lines.append("⚖ Expose — " + " · ".join(stacks) +
                         f" (burst at {BURST_STACKS})")
        for line in lines:
            c_print(f"  {line}")

    # ── Intro ──────────────────────────────────────────────────────────
    c_print("\n" + "=" * 60)
    c_print("A cold radiance fills the chamber. Armour of white porcelain")
    c_print("kneels before an empty throne, a rapier driven into the floor.")
    c_print("It rises. The oath it swore outlived the empire it served.")
    c_print(f"\n{BOSS_NAME} — HP: {boss['hp']}")
    c_print("=" * 60)
    c_input("\nPress Enter to face the fallen oath...")

    result = superboss_combat_loop(
        player, enemies, floor, BOSS_NAME, context,
        pre_player_hook=pre_player_hook,
        custom_hud_hook=custom_hud_hook,
        on_player_hit_hook=on_player_hit_hook,
        enemy_turn_hook=enemy_turn_hook,
    )

    # ── Cleanup + reward ───────────────────────────────────────────────
    for m in [player] + player.get("allies", []):
        m.pop("enemy_attack_armor_mult", None)
        m.pop("expose_stacks", None)
        m.pop("_skill_dodge_used", None)
        m.pop("_accuracy_penalty_used", None)
    boss.pop("dodge_cap_override", None)
    boss.pop("skill_dodge_chance", None)
    boss.pop("ally_accuracy_penalty", None)
    boss.pop("_wk_phase", None)
    boss.pop("_wk_round", None)
    boss.pop("_wk_floor_msg_round", None)
    _remove_buff(boss, "wk_dodge")
    _remove_buff(boss, "wk_edge")

    if result == "victory":
        if not player.get("boss_defeated_white_knight"):
            c_print("\n" + "=" * 60)
            c_print("The porcelain falls away. The oath is kept at last —")
            c_print("what remains is a blade that never misses its promise.")
            c_print("=" * 60)
            from resources.items import build_item
            from inventory_ui import prompt_acquire_item
            rapier = build_item("last_oath", "unique")
            c_print("\n  ⚜ You obtained: LAST OATH (Unique) ⚜")
            prompt_acquire_item(player, rapier)
            player["boss_defeated_white_knight"] = True
        c_input("  Press Enter to continue...")

    return result
