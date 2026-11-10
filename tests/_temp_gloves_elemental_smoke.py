# Temp smoke test: Black Silence Gloves workshop hits apply crit + Dark elemental mods
import sys
sys.path.insert(0, "c:/Code/Pandemonium")

import combat.stats as stats
import combat.weapon.black_silence_gloves as g


# ── 1. Unit: _deal_workshop_hit pipeline (crit + elemental) ──
def force_crit(flag):
    stats.roll_critical_hit = (
        lambda entity, entity_type="player", dex=None, lrn=None: (flag, 1.0 if flag else 0.0, 0.0)
    )


actor = {
    "name": "Tester", "is_ally": False,
    "elemental_dmg": {"dark": 1.5}, "elemental_res": {},
    "active_buffs": [], "active_debuffs": [],
}
target = {"name": "Dummy", "hp": 10000, "con_mod": 0, "elemental_res": {"dark": 0.5}}

force_crit(False)
dmg, msg = g._deal_workshop_hit(actor, target, 100, "Test", 10, 10)
assert dmg == int(100 * 1.5 * 0.5), (dmg, msg)  # 75 — elemental only
assert "[DARK]" in msg and "CRITICAL" not in msg, msg
assert target["hp"] == 10000 - dmg, (target["hp"], dmg)
print("non-crit hit:      ", dmg, "|", msg)

target["hp"] = 10000
force_crit(True)
dmg, msg = g._deal_workshop_hit(actor, target, 100, "Test", 10, 10)
assert dmg == int(int(100 * 1.5) * 1.5 * 0.5), (dmg, msg)  # 112 — crit then elemental
assert "CRITICAL" in msg and "[DARK]" in msg, msg
print("crit hit:          ", dmg, "|", msg)

# Dark resistance direction check (weak target takes more)
target["elemental_res"] = {"dark": 1.5}
target["hp"] = 10000
force_crit(False)
dmg, _ = g._deal_workshop_hit(actor, target, 100, "Test", 10, 10)
assert dmg == int(100 * 1.5 * 1.5), dmg  # 225
print("dark-weak target:  ", dmg, "| ok")

# ── 2. Integration: a full workshop branch uses the pipeline ──
stats.roll_critical_hit = lambda *a, **k: (False, 0.0, 0.0)  # no crits for determinism
g._roll_base_damage = lambda scaling_val: 100           # fixed damage roll

player = {
    "name": "Wearer", "is_ally": False,
    "attributes": {"Strength": 0, "Dexterity": 10, "Learning": 10},
    "elemental_dmg": {"dark": 1.5}, "elemental_res": {},
    "active_buffs": [], "active_debuffs": [], "current_hp": 100,
}
enemy = {"name": "Foe", "hp": 5000, "con_mod": 0, "elemental_res": {"dark": 1.0}}

msg, victory = g._execute_workshop_actor(
    player, [enemy], 4, 0, 0, 10, 10, 0, 0, is_player=True,
)
# workshop 4: (100 - 0) * 1.20 = 120 → dark 1.5× → 180
assert enemy["hp"] == 5000 - 180, (enemy["hp"], msg)
assert "[DARK]" in msg, msg
print("workshop 4:        ", 5000 - enemy["hp"], "dmg | ok")

# First strike bonus stacks multiplicatively before crit/elemental
player["gloves_first_strike_active"] = True
player["gloves_workshop_used"] = set()
enemy["hp"] = 5000
msg, _ = g._execute_workshop_actor(
    player, [enemy], 4, 0, 0, 10, 10, 0, 0, is_player=True,
)
# int(120 * 1.15) = 138 → ×1.5 dark = 207
assert enemy["hp"] == 5000 - 207, (enemy["hp"], msg)
print("workshop 4 + 1st:  ", 5000 - enemy["hp"], "dmg | ok")

# ── 3. Crits re-enabled: a forced crit doubles nothing else but multiplies by 1.5 ──
stats.roll_critical_hit = lambda *a, **k: (True, 1.0, 0.0)
player["gloves_first_strike_active"] = False
player["gloves_workshop_used"] = set()
enemy["hp"] = 5000
msg, _ = g._execute_workshop_actor(
    player, [enemy], 4, 0, 0, 10, 10, 0, 0, is_player=True,
)
# int(120 * 1.5) = 180 → ×1.5 dark = 270
assert enemy["hp"] == 5000 - 270, (enemy["hp"], msg)
assert "CRITICAL" in msg, msg
print("workshop 4 crit:   ", 5000 - enemy["hp"], "dmg | ok")

# ── 4. Ally path (is_ally=True) uses the same pipeline ──
stats.roll_critical_hit = lambda *a, **k: (False, 0.0, 0.0)
ally = {
    "name": "Ally", "is_ally": True,
    "attributes": {"Strength": 0, "Dexterity": 10, "Learning": 10},
    "elemental_dmg": {"dark": 1.5}, "elemental_res": {},
    "active_buffs": [], "active_debuffs": [], "current_hp": 100,
}
enemy["hp"] = 5000
msg, _ = g._execute_workshop_actor(
    ally, [enemy], 4, 0, 0, 10, 10, 0, 0, is_player=False,
)
assert enemy["hp"] == 5000 - 180, (enemy["hp"], msg)
print("ally workshop 4:   ", 5000 - enemy["hp"], "dmg | ok")

print("\nAll Black Silence Gloves crit/elemental smoke checks passed.")
