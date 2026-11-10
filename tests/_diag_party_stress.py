"""Headless diagnostic: combat-driven party stress (2026-10-30).

Covers
──────
* Fall settlement — player +34 per fall, fallen ally +34, witnesses +20.
* Fall detection without touching knockout sites (combat-scoped marker),
  including a "superboss left a marker behind" replay.
* Burned Out companions refuse the encounter and are filtered out of every
  combat/party selection helper, with a template-overridable dialogue line.
* Banded combat penalty (Weary −1 / Frayed −2 / Burned Out −3) + HUD tag.
* Sleep recovery (−10 per companion) and EH/Wonderland suppression.

Run:
    .venv\\Scripts\\python.exe tests\\_diag_party_stress.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import leveling
leveling.gain_exp = lambda player, amount: None
leveling.gain_exp_ally = lambda ally, amount: None
import save_load
save_load.save_game = lambda player: None

import time_blocks as tb
from character import build_character, ensure_player_fields
import combat.party_stress as ps
from combat.ally import (get_active_allies, get_reserve_allies,
                         get_alive_allies, get_all_active_allies_including_defeated,
                         get_ally_effective_attribute)
from combat.combat_ui import _get_entity_buff_tags

CHECKS = []


def check(name, ok, detail=""):
    CHECKS.append((name, bool(ok), detail))
    tag = "OK  " if ok else "FAIL"
    print(f"[{tag}] {name}" + (f" — {detail}" if detail and not ok else ""))


ATTRS = {"Strength": 20, "Constitution": 20, "Dexterity": 20,
         "Learning": 20, "Wisdom": 20, "Charisma": 20}


def new_player():
    player = build_character("1", "1", ATTRS, "Diag", 1)
    player.pop("save_slot", None)
    ensure_player_fields(player)
    return player


def add_ally(player, name, stress=0, hp=50):
    ally = {"key": "harpy_scout", "name": name, "is_ally": True, "level": 5,
            "attributes": dict(ATTRS), "equipped": {}, "active_buffs": [],
            "active_debuffs": [], "current_hp": hp, "max_hp": 50,
            "stress": stress, "affection": 30, "affection_cap": 100,
            "defeated": False}
    player.setdefault("allies", []).append(ally)
    return ally


# ── 1. Bands, penalty, tags ────────────────────────────────────────────────
bands = {0: "calm", 49: "calm", 50: "weary", 74: "weary",
         75: "frayed", 89: "frayed", 90: "burnout", 100: "burnout"}
check("stress bands split at 50 / 75 / 90",
      all(ps.stress_band({"stress": v}) == name for v, name in bands.items()),
      str({v: ps.stress_band({"stress": v}) for v in bands}))
check("penalties are 0 / 1 / 2 / 3",
      [ps.stress_penalty({"stress": v}) for v in (0, 50, 75, 90)] == [0, 1, 2, 3])
check("HUD tags are WEA / FRY / EXH",
      [ps.stress_tag({"stress": v}) for v in (0, 50, 75, 90)]
      == [None, "WEA", "FRY", "EXH"])

ally = {"stress": 97}
check("ally stress clamps at 100",
      ps.add_ally_stress(ally, 10) == 100)
check("ally stress clamps at 0", ps.add_ally_stress(ally, -500) == 0)

# ── 2. Marker + fall settlement ───────────────────────────────────────────
player = new_player()
fallen = add_ally(player, "Fallen")
witness = add_ally(player, "Witness")
messages = ps.begin_encounter(player)
check("begin_encounter marks only living allies",
      fallen.get("_combat_started_alive") is True
      and witness.get("_combat_started_alive") is True
      and not messages, str(messages))

# Simulate a knockout exactly the way the engines do it
fallen["current_hp"] = 0
fallen["defeated"] = True
before_player = tb.get_stress(player)
messages = ps.settle_pending_falls(player)
check("a fall charges the player +34 stress",
      tb.get_stress(player) == before_player + ps.PLAYER_STRESS_PER_FALL,
      f"{tb.get_stress(player)}")
check("the fallen companion takes +34", fallen["stress"] == 34,
      f"{fallen['stress']}")
check("surviving companions take +20", witness["stress"] == 20,
      f"{witness['stress']}")
check("the fall is announced", any("fell in the fighting" in m for m in messages),
      str(messages))

snapshot = (tb.get_stress(player), fallen["stress"], witness["stress"])
ps.settle_pending_falls(player)
check("settlement is idempotent (no double charge)",
      (tb.get_stress(player), fallen["stress"], witness["stress"]) == snapshot)

# ── 3. A superboss that never settled: marker survives to the next fight ──
player = new_player()
ally = add_ally(player, "Left Behind")
ally["_combat_started_alive"] = True     # superboss loop exited without settle
ally["current_hp"] = 0
ps.begin_encounter(player)
check("begin_encounter settles a marker left by a superboss loop",
      ally["stress"] == ps.ALLY_STRESS_FALLEN
      and tb.get_stress(player) == ps.PLAYER_STRESS_PER_FALL,
      f"ally={ally['stress']} player={tb.get_stress(player)}")

# ── 4. Two falls in one fight ─────────────────────────────────────────────
player = new_player()
a = add_ally(player, "A")
b = add_ally(player, "B")
c = add_ally(player, "C")
ps.begin_encounter(player)
a["current_hp"] = 0
b["current_hp"] = 0
ps.settle_pending_falls(player)
check("two falls = +68 player stress",
      tb.get_stress(player) == 2 * ps.PLAYER_STRESS_PER_FALL,
      f"{tb.get_stress(player)}")
check("the survivor takes +20 per fall", c["stress"] == 2 * ps.ALLY_STRESS_WITNESS,
      f"{c['stress']}")

# ── 5. Conversion into fatigue still applies ─────────────────────────────
player = new_player()
player["stress"] = 80
ally = add_ally(player, "Victim")
ps.begin_encounter(player)
ally["current_hp"] = 0
messages = ps.settle_pending_falls(player)
check("80 + 34 converts into Fatigue I with 14 left",
      player["fatigue_stacks"] == 1 and tb.get_stress(player) == 14,
      f"fatigue={player['fatigue_stacks']} stress={tb.get_stress(player)}")
check("the conversion is announced",
      any("Fatigue" in m for m in messages), str(messages))

# ── 6. Refusal ────────────────────────────────────────────────────────────
player = new_player()
burned = add_ally(player, "Burned Out", stress=95)
steady = add_ally(player, "Steady", stress=10)
messages = ps.begin_encounter(player)
check("a Burned Out companion refuses the encounter",
      ps.is_sitting_out(burned) is True, str(burned.get("_stress_sit_out")))
check("the refusal is announced",
      len(messages) == 1 and "Burned Out" in messages[0], str(messages))
check("refused allies leave the front row",
      burned not in get_active_allies(player))
check("the steady ally is still fightable",
      steady in get_alive_allies(player))
check("refused allies leave the bench",
      burned not in get_reserve_allies(player))
check("refused allies leave the living-allies list",
      burned not in get_alive_allies(player))
check("refused allies leave the party display",
      burned not in get_all_active_allies_including_defeated(player))

# Template override support
from resources.enemies import ENEMIES
tmpl = ENEMIES.get("harpy_scout")
if isinstance(tmpl, dict):
    tmpl.setdefault("dialogue", {})["stress_refusal"] = "TEMPLATE {name}"
    try:
        line = ps.refusal_line(burned)
    finally:
        tmpl["dialogue"].pop("stress_refusal", None)
    check("template dialogue overrides the generic refusal",
          line == "TEMPLATE Burned Out", line)

ps.settle_pending_falls(player)
check("the refusal clears when the encounter settles",
      burned.get("_stress_sit_out") is None)

# A Burned Out companion on the BENCH has not been asked, so she stays quiet
player = new_player()
steady_first = add_ally(player, "Front", stress=0)
bench_burned = add_ally(player, "Bench Burnout", stress=95)
messages = ps.begin_encounter(player)
check("bench companions do not refuse (nobody asked them)",
      not messages and not ps.is_sitting_out(bench_burned), str(messages))

# ── 7. Combat stat penalty + HUD tag ─────────────────────────────────────
player = new_player()
ally = add_ally(player, "Weary One", stress=0)
base = get_ally_effective_attribute(ally, "Strength")
ally["stress"] = 50
weary = get_ally_effective_attribute(ally, "Strength")
ally["stress"] = 75
frayed = get_ally_effective_attribute(ally, "Strength")
ally["stress"] = 90
burned = get_ally_effective_attribute(ally, "Strength")
check("ally stats drop −1 / −2 / −3 by band",
      (base - weary, base - frayed, base - burned) == (1, 2, 3),
      f"{base} → {weary}/{frayed}/{burned}")

ally["stress"] = 0
check("a calm ally shows no stress tag", "WEA" not in _get_entity_buff_tags(ally))
ally["stress"] = 76
tags = _get_entity_buff_tags(ally)
check("a Frayed ally shows the FRY tag", "FRY" in tags, tags)
player["is_ally"] = False
check("the player never gets an ally stress tag",
      "WEA" not in _get_entity_buff_tags(player))

# ── 8. Sleep recovery + settlement in one call ───────────────────────────
player = new_player()
ally = add_ally(player, "Tired", stress=60)
ally["_combat_started_alive"] = True
ally["current_hp"] = 0
messages = ps.on_party_sleep(player)
check("sleep settles falls before recovering",
      ally["stress"] == 60 + ps.ALLY_STRESS_FALLEN - ps.SLEEP_STRESS_RECOVERY,
      f"{ally['stress']}")
check("sleep recovery is announced",
      any("sleeps it off" in m for m in messages), str(messages))

player = new_player()
rested = add_ally(player, "Resting", stress=5)
ps.on_party_sleep(player)
check("recovery clamps at 0", rested["stress"] == 0, f"{rested['stress']}")

# ── 9. Suppression ────────────────────────────────────────────────────────
for flag, label in (("_eh_in_run", "Event Horizon"),
                    ("wonderland_active", "Wonderland")):
    player = new_player()
    ally = add_ally(player, "Fallen")
    ps.begin_encounter(player)
    ally["current_hp"] = 0
    player[flag] = True
    ps.settle_pending_falls(player)
    check(f"no stress charged inside {label}",
          tb.get_stress(player) == 0 and ally["stress"] == 0
          and ally.get("_combat_started_alive") is None,
          f"player={tb.get_stress(player)} ally={ally['stress']}")

# ── 10. Wiring guards ────────────────────────────────────────────────────
import inspect
import combat.combat_engine as ce
check("the standard engine begins and settles encounters",
      "begin_encounter" in inspect.getsource(ce.combat)
      and "settle_pending_falls" in inspect.getsource(ce._end_combat_with_result))
import combat.superboss_common as sc
check("superboss fights begin encounters",
      "begin_encounter" in inspect.getsource(sc.superboss_combat_loop))

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for rel in (("facilities", "house.py"), ("facilities", "inn.py"),
            ("facilities", "camp.py")):
    with open(os.path.join(root, *rel), encoding="utf-8") as fh:
        src = fh.read()
    check(f"{rel[1]} sleeps settle party stress", "on_party_sleep" in src)

failed = [name for name, ok, _ in CHECKS if not ok]
print()
print(f"{len(CHECKS) - len(failed)}/{len(CHECKS)} checks passed")
if failed:
    print("FAILED:")
    for name in failed:
        print(f"  - {name}")
    sys.exit(1)
print("party stress OK")
