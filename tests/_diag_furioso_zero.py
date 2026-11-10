"""Diagnostic: why does Furioso deal 0 damage to the Elder Titan?

Loads the live save, reconstructs the in-run state (room/entropy/cards),
then computes:
  1. player effective stats (compute_player_stats) as combat would see them
  2. Elder Titan con_mod as spawned for that room (enemy_stats)
  3. raw Furioso per-workshop damage math from black_silence_gloves.py

Read-only: does not modify the save file.
"""
import json
import io
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

with open("savefile/savegame_1.json", encoding="utf-8") as f:
    player = json.load(f)

# Recreate the in-run gate the engine sets while a run is active.
player["_eh_in_run"] = True
eh = player.setdefault("event_horizon", {})
print("=== EVENT HORIZON STATE ===")
print("run_active:", eh.get("run_active"), "| room:", eh.get("room"),
      "| entropy:", eh.get("entropy"), "| best:", eh.get("best_room"))
print("negative cards:", [(c.get("name"), c.get("effects")) for c in eh.get("negative_cards", [])])
print("positive cards:", [(c.get("name"), c.get("effects")) for c in eh.get("positive_cards", [])])
print("afflictions:", eh.get("entropy_afflictions"))

print()
print("=== PLAYER ===")
from combat.stats import compute_player_stats, get_effective_attribute
from inventory import get_total_equipment_mods
print("base attributes:", player["attributes"])
print("equipment mods:", get_total_equipment_mods(player))
print("weapon:", (player.get("equipped", {}).get("weapon") or {}).get("id"),
      "|", (player.get("equipped", {}).get("weapon") or {}).get("name"))
print("active buffs (player):")
for b in player.get("active_buffs", []):
    print("   ", {k: b.get(k) for k in ("type", "stat", "value", "source", "permanent", "label")})
print("active debuffs (player):")
for d in player.get("active_debuffs", []):
    print("   ", {k: d.get(k) for k in ("type", "value", "remaining", "stacks")})

print("tarnished_jade_weakened flag:", player.get("tarnished_jade_weakened"))
print("tarnished_jade_pins:", player.get("tarnished_jade_pins"))
print("equipped slots:")
for slot, item in (player.get("equipped") or {}).items():
    if isinstance(item, dict):
        print("   ", slot, "=", item.get("id"), item.get("name"))

# Compare the attribute math with the Jade debuff manually disabled
names = ["STR", "CON", "DEX", "LER", "WIS", "CHA"]
saved_flag = player.get("tarnished_jade_weakened")
player["tarnished_jade_weakened"] = False
p_nojade = compute_player_stats(player)
print("effective stats (jade flag off, no entropy):", dict(zip(names, p_nojade)))
player["tarnished_jade_weakened"] = saved_flag

# ── Re-attach the live-run buffs the game reapplies on resume ──
# Insight (+4 all), Celerity (+3 DEX), plus stat flasks recorded in the EH
# state. These exist on actors during the fight (the HUD proves it) but were
# stripped from this save snapshot.
def _attach_run_buffs(actor, key):
    have = {(b.get("type"), b.get("stat")) for b in actor.get("active_buffs", [])}
    if ("stat", "all") not in have:
        actor.setdefault("active_buffs", []).append(
            {"type": "stat", "stat": "all", "value": 4, "source": "event_horizon", "permanent": True})
    if ("stat", "Dexterity") not in have:
        actor["active_buffs"].append(
            {"type": "stat", "stat": "Dexterity", "value": 3, "source": "event_horizon", "permanent": True})
    for rec in (eh.get("actor_flasks", {}) or {}).get(key, []) or []:
        eff = rec.get("effect") or {}
        if eff.get("type") == "stat":
            actor["active_buffs"].append(
                {"type": "stat", "stat": eff.get("stat"), "value": eff.get("value")})

_attach_run_buffs(player, "player")
_party_all = [player] + [a for a in player.get("allies", []) if a.get("current_hp", 0) > 0]
for _a in player.get("allies", []):
    _key = f"{_a.get('key', '?')}:{_a.get('name', '?')}"
    _attach_run_buffs(_a, _key)
print()
print("player buffs after re-attach:")
for b in player.get("active_buffs", []):
    print("   ", {k: b.get(k) for k in ("type", "stat", "value", "source", "permanent")})

p = compute_player_stats(player)
names = ["STR", "CON", "DEX", "LER", "WIS", "CHA"]
print("effective stats (no entropy entry in save context):", dict(zip(names, p)))

# Now apply entropy the way refresh_entropy_entries() would in-run.
from event_horizon import sync_entropy, get_entropy_total
total = sync_entropy(player)
print("entropy total after sync:", total)
p = compute_player_stats(player)
p_str, p_con, p_dex, p_ler, p_wis, p_cha = p
print("effective stats WITH entropy:", dict(zip(names, p)))

print()
print("=== ELDER TITAN (as spawned for this room) ===")
from combat.stats import enemy_stats
enemy = enemy_stats("elder_titan", player)
print("hp:", enemy["hp"], "| con_mod:", enemy["con_mod"], "| str:", enemy["str_mod"],
      "| dex:", enemy["dex_mod"], "| elemental_res:", enemy["elemental_res"])
print("con_mod breakdown: base 15 -> x1.24 (dusk) -> x EH def mod")

print()
print("=== FURIOSO MATH (10k samples per workshop, reworked pipeline) ===")
from combat.weapon.black_silence_gloves import (
    WORKSHOPS, _workshop_net_damage, get_gloves_power_mult, get_gloves_enhance_level,
)
from combat.stat_milestones import get_strength_bonus
stat_map = {"Strength": p_str, "Dexterity": p_dex, "Constitution": p_con,
            "Wisdom": p_wis, "Learning": p_ler, "Charisma": p_cha}
con = enemy["con_mod"]
str_bonus = get_strength_bonus(player)
enh_lv = get_gloves_enhance_level(player)
enh_mult = get_gloves_power_mult(player)
print(f"con_mod = {con} | gloves enhance = +{enh_lv} (power x{enh_mult:.2f})")
print("str milestone bonus:", str_bonus)
for wid, ws in WORKSHOPS.items():
    stat_val = stat_map[ws["stat"]]
    vals = []
    zeroes = 0
    for _ in range(20000):
        base = random.randint(4, 10) + stat_val + (str_bonus if ws["stat"] == "Strength" else 0)
        power = int(base * enh_mult)
        dmg = _workshop_net_damage(power, enemy, ws["mult"],
                                   ignore_con_pct=0.10 if wid == 1 else 0.0,
                                   extra_mult=1.45)
        vals.append(dmg)
        if dmg == 0:
            zeroes += 1
    avg = sum(vals) / len(vals)
    print(f"  [{wid}] {ws['name']:<16} power={int((4 + stat_val) * enh_mult)}..{int((10 + stat_val) * enh_mult)} "
          f"-> min={min(vals)} avg={avg:.1f} max={max(vals)}  zero%={zeroes / len(vals) * 100:.0f}%")

print()
print("=== SIMPLE ATTACK / ALLY COMPARISON ===")
# Basic player attack: randint(4,10) + weapon scaling - con, min 0
w = player.get("equipped", {}).get("weapon") or {}
scaling = 0
for s in (w.get("scaling_stat") or ["Strength"]):
    scaling += stat_map.get(s, 0)
if w.get("scaling_mult"):
    scaling = int(scaling * w["scaling_mult"])
print(f"basic attack scaling_val ({w.get('scaling_stat')}): {scaling} "
      f"-> roll+scaling-con = {4 + scaling - con}..{10 + scaling - con} (min 0)")

print()
print("=== ALLIES ===")
from combat.ally import compute_ally_stats
from combat.stat_milestones import get_strength_bonus as gsb

# (Run buffs for allies were already re-attached above, before stat math.)

for a in player.get("allies", []):
    if a.get("current_hp", 0) <= 0:
        continue
    print(f"  {a.get('name')} lvl={a.get('level')} hp={a.get('current_hp')}/{a.get('max_hp')} "
          f"attrs={a.get('attributes')}")
    print(f"     innate skills: {a.get('innate_skills')} | enhanced: {a.get('enhanced_skills')}")
    print(f"     weapon: {(a.get('equipped', {}).get('weapon') or {}).get('id')}")

print()
print("=== ALLY DAMAGE vs CHITIN-BUFFED ELDER TITAN (con 38) ===")
from resources.enemies import ENEMIES
for a in player.get("allies", []):
    if a.get("current_hp", 0) <= 0:
        continue
    a_stats = compute_ally_stats(a)
    names6 = ["STR", "CON", "DEX", "LER", "WIS", "CHA"]
    d = dict(zip(names6, a_stats))
    print(f"  {a.get('name')} effective: {d}")
    # Nine Tails Strike (base 8, 3 hits, WIS) if native
    if "nine_tails_strike" in (a.get("innate_skills") or []):
        power = 8 + d["WIS"] + d["LER"] // 2
        per_hit = max(1, power + gsb(a) - con)
        print(f"     nine_tails_strike: power={power} -> per hit vs con38 = {per_hit} (x3 hits)")
    # basic attack with their weapon scaling
    w = a.get("equipped", {}).get("weapon") or {}
    scaling = 0
    for s in (w.get("scaling_stat") or ["Strength"]):
        scaling += d.get({"Strength": "STR", "Dexterity": "DEX", "Wisdom": "WIS",
                          "Learning": "LER", "Constitution": "CON", "Charisma": "CHA"}.get(s, "STR"), 0)
    if w.get("scaling_mult"):
        scaling = int(scaling * w["scaling_mult"])
    lo = max(0, 3 + scaling + gsb(a) - con)
    hi = max(0, 8 + scaling + gsb(a) - con)
    print(f"     basic attack ({w.get('id')}, scales {w.get('scaling_stat')}): {lo}-{hi} raw/hit")
