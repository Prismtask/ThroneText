"""Diagnostic: Fractured Hourglass fix (reusable, free action, 3-turn cooldown).

Covers:
  1. Module-level use / refusal / tick logic.
  2. Player combat 'u' path — item NOT consumed, turn NOT consumed ("retry"),
     cooldowns reduced, hourglass cooldown set.
  3. Ally combat 'u' path — same, actor-based (player cooldowns untouched).
  4. Out-of-combat inventory block (item is combat-only, never consumed).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from resources.items import build_item
from combat.fractured_hourglass import (
    is_fractured_hourglass, use_fractured_hourglass, get_hourglass_cooldown,
    tick_hourglass_cooldown, HOURGLASS_COOLDOWN_TURNS,
)
from inventory import is_combat_only_item, use_consumable

failures = []


def check(label, cond, extra=""):
    status = "PASS" if cond else "FAIL"
    print(f"[{status}] {label}" + (f" — {extra}" if extra else ""))
    if not cond:
        failures.append(label)


def fresh_player():
    return {
        "name": "prism",
        "current_hp": 100,
        "skill_cooldowns": {"pierce": 2, "whirl": 3, "guard": 1},
        "inventory": [build_item("fractured_hourglass", "legendary")],
        "equipped": {},
        "allies": [],
        "active_buffs": [],
        "active_debuffs": [],
    }


def fresh_ally():
    return {
        "name": "Luna",
        "current_hp": 50,
        "max_hp": 50,
        "skill_cooldowns": {"bite": 2},
        "equipped": {},
        "active_buffs": [],
        "active_debuffs": [],
    }


# ── 1. Module level ──────────────────────────────────────────────────────
print("── Module logic ──")
item = build_item("fractured_hourglass", "legendary")
check("item instance identified", is_fractured_hourglass(item))
check("item is combat-only", is_combat_only_item(item))
check("out-of-combat use blocked (inert message)", "inert" in use_consumable(fresh_player(), item))

p = fresh_player()
check("first use succeeds", use_fractured_hourglass(p, is_player=True) is True)
check("all cooldowns reduced by 1", p["skill_cooldowns"] == {"pierce": 1, "whirl": 2},
      f"got {p['skill_cooldowns']}")
check("hourglass cooldown set", get_hourglass_cooldown(p) == HOURGLASS_COOLDOWN_TURNS)
check("second use refused while recharging", use_fractured_hourglass(p, is_player=True) is False)

tick_hourglass_cooldown(p)
tick_hourglass_cooldown(p)
check("still recharging after 2 ticks", get_hourglass_cooldown(p) == 1)
tick_hourglass_cooldown(p)
check("ready again after 3 ticks", get_hourglass_cooldown(p) == 0)
check("reuse succeeds once ready", use_fractured_hourglass(p, is_player=True) is True)
check("reuse reduced remaining cooldown", p["skill_cooldowns"] == {"whirl": 1},
      f"got {p['skill_cooldowns']}")

p2 = fresh_player()
p2["skill_cooldowns"] = {}
check("refused when nothing on cooldown", use_fractured_hourglass(p2, is_player=True) is False)
check("no hourglass cooldown started on refusal", get_hourglass_cooldown(p2) == 0)

# ── 2. Player combat path ────────────────────────────────────────────────
print("\n── Player combat path ──")
import combat.player_actions as pa


def _mock_input(inputs):
    def fake_input(_prompt=""):
        if not inputs:
            raise RuntimeError("unexpected c_input call — no scripted input left")
        return inputs.pop(0)
    return fake_input


def run_player_item_use(player):
    """Drive handle_player_turn('u') with mocked IO, picking battle item #1."""
    pa.c_print = lambda *a, **k: None
    pa.c_input = _mock_input(["1"])
    pa.print_combat_hud = lambda *a, **k: None
    pa.get_action_menu = lambda *a, **k: ("", ["u"], set())
    return pa.handle_player_turn(
        player, [{"name": "Dummy", "hp": 999, "con_mod": 5}],
        10, 10, 10, 10, 10, 10, _action_override="u",
    )


p3 = fresh_player()
res = run_player_item_use(p3)
check("player: free action returns retry (turn kept)", res == ("retry", False), f"got {res}")
check("player: item NOT consumed",
      any(i.get("id") == "fractured_hourglass" for i in p3["inventory"]))
check("player: cooldowns reduced", p3["skill_cooldowns"] == {"pierce": 1, "whirl": 2},
      f"got {p3['skill_cooldowns']}")
check("player: hourglass cooldown set", get_hourglass_cooldown(p3) == HOURGLASS_COOLDOWN_TURNS)

# ── 3. Ally combat path ──────────────────────────────────────────────────
print("\n── Ally combat path ──")
import combat.ally as ca
import combat.combat_ui as cui

cui.print_combat_hud = lambda *a, **k: None


def run_ally_item_use(ally, player):
    """Drive handle_ally_turn('u') with mocked IO, picking battle item #1."""
    ca.c_print = lambda *a, **k: None
    ca.c_input = _mock_input(["u", "1"])
    ca._ally_action_menu = lambda *a, **k: ("", ["u"], set())
    ca.compute_ally_stats = lambda a: (10, 10, 10, 10, 10, 10)
    return ca.handle_ally_turn(
        ally, player, [{"name": "Dummy", "hp": 999, "con_mod": 5}],
        10, 10, 10, 10, 10, 10,
    )


ally = fresh_ally()
p4 = fresh_player()
p4["skill_cooldowns"] = {"pierce": 2}
res = run_ally_item_use(ally, p4)
check("ally: free action returns retry (turn kept)", res == "retry", f"got {res}")
check("ally: item NOT consumed",
      any(i.get("id") == "fractured_hourglass" for i in p4["inventory"]))
check("ally: ally cooldowns reduced", ally["skill_cooldowns"] == {"bite": 1},
      f"got {ally['skill_cooldowns']}")
check("ally: ally hourglass cooldown set", get_hourglass_cooldown(ally) == HOURGLASS_COOLDOWN_TURNS)
check("ally: player cooldowns untouched", p4["skill_cooldowns"] == {"pierce": 2},
      f"got {p4['skill_cooldowns']}")

# ── Result ───────────────────────────────────────────────────────────────
print()
if failures:
    print(f"RESULT: {len(failures)} FAILURE(S): {failures}")
    sys.exit(1)
print("RESULT: all checks passed.")
