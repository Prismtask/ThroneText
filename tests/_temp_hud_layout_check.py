"""Temp check (2026-09-27): crit line sits beside the actor name in the combat HUD.

Uses a withdrawn Tk root so nothing pops up; verifies pack side/parent and that
enemy frames keep the crit label hidden.
"""
import os
import sys
import tkinter as tk

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gui.combat.combat_renderer import CombatRenderer

root = tk.Tk()
root.withdraw()

player = {
    "name": "prism", "current_hp": 207, "level": 20,
    "attributes": {"Strength": 30, "Constitution": 30, "Dexterity": 40,
                   "Learning": 30, "Wisdom": 10, "Charisma": 10},
    "active_buffs": [], "active_debuffs": [], "equipped": {}, "allies": [],
    "skill_cooldowns": {}, "party_order": [],
}
enemies = [{"name": "Mook", "hp": 100, "max_hp": 100, "con_mod": 0}]

r = CombatRenderer(root)
r.refresh(player, enemies)

pframe = r._party_frames[0]
crit = pframe.widgets["crit"]
name_master = pframe.widgets["name"].master

assert crit.winfo_manager() == "pack", crit.winfo_manager()
assert crit.pack_info().get("side") == "right", crit.pack_info()
assert crit.master is name_master, "crit label must live in the name row frame"
assert crit.cget("text").startswith("Crit:"), crit.cget("text")
print("OK: crit label beside the name on the party frame ->", crit.cget("text"))

eframe = r._enemy_frames[0]
assert eframe.widgets["crit"].winfo_manager() == "", "enemy crit label should stay hidden"
print("OK: enemy frames keep the crit label hidden")

root.destroy()
print("ALL CHECKS PASSED")
