"""Check (2026-10-07): ENEMIES column is pre-sized for 5 entity slots.

The enemy box used to grow with each enemy added and shrink as enemies
died. It now always reserves a full 5-slot layout, blank slots included,
so the HUD boxes keep a constant "5 entity size" for the whole fight.

Run: .venv\\Scripts\\python.exe tests\\_temp_enemy_slots_check.py
"""
import sys
import tkinter as tk
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gui.combat.combat_renderer import CombatRenderer, ENEMY_SLOTS
from gui.theme import Theme

root = tk.Tk()
root.title("enemy-slots-check")
root.geometry("1536x793")

screen = tk.Frame(root, bg=Theme.BG_DARK)
screen.pack(fill=tk.BOTH, expand=True)

player = {
    "name": "prism", "current_hp": 207, "level": 20,
    "attributes": {"Strength": 30, "Constitution": 30, "Dexterity": 40,
                   "Learning": 30, "Wisdom": 10, "Charisma": 10},
    "active_buffs": [], "active_debuffs": [], "equipped": {}, "allies": [],
    "skill_cooldowns": {}, "party_order": [],
}

r = CombatRenderer(screen)
r.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)


def enemies(n):
    return [{"name": f"Mook {i}", "hp": 100, "max_hp": 100} for i in range(n)]


def heights():
    return r.enemy_col.winfo_reqheight(), r.party_col.winfo_height()


failures = []
measured = {}
for n in range(0, 6):
    r.refresh(player, enemies(n))
    root.update_idletasks()
    root.update()
    ec_h = r.enemy_col.winfo_reqheight()
    pc_h = r.party_col.winfo_height()
    measured[n] = ec_h
    print(f"n={n}: enemy_col req-height={ec_h}px "
          f"party_col height={pc_h}px "
          f"visible enemy slots="
          f"{sum(1 for f in r._enemy_frames if f.winfo_manager())}")

# 1. Height constant for 0..5 enemies (5 = full wave size).
if len(set(measured.values())) != 1:
    failures.append(f"enemy_col height varies with enemy count: {measured}")
else:
    print("OK — enemy box keeps one constant height (5-slot size)")

# 2. Simulates enemies dying mid-fight: 5 -> 2 -> 5 keeps the same height.
r.refresh(player, enemies(5))
root.update_idletasks(); root.update()
full = r.enemy_col.winfo_reqheight()
r.refresh(player, enemies(2))
root.update_idletasks(); root.update()
mid = r.enemy_col.winfo_reqheight()
r.refresh(player, enemies(5))
root.update_idletasks(); root.update()
back = r.enemy_col.winfo_reqheight()
if not (full == mid == back):
    failures.append(f"height changed mid-fight: 5->{full} 2->{mid} 5->{back}")
else:
    print(f"OK — mid-fight prunes keep the height ({full}px)")

# 3. Empty slots are blank and packed; real slots render normally afterwards.
r.refresh(player, enemies(1))
root.update_idletasks(); root.update()
slot2 = r._enemy_frames[2]
if slot2.winfo_manager() != "pack":
    failures.append("reserved slot is not packed")
w = slot2.widgets
if w["name"].cget("text") or w["hp_bar"].find_all():
    failures.append("reserved slot is not blank")
else:
    print("OK — reserved slots are blank, full-height placeholders")

r.refresh(player, enemies(4))
root.update_idletasks(); root.update()
if not r._enemy_frames[2].widgets["name"].cget("text"):
    failures.append("slot did not re-render when an enemy filled it")
elif not r._enemy_frames[2].widgets["hp_bar"].find_all():
    failures.append("HP bar did not re-render when an enemy filled it")
else:
    print("OK — slots re-render when an enemy takes them")

# 4. Interaction guards: flash("") is a no-op; badges only land on real slots.
if r.flash_entity(""):
    failures.append("flash_entity('') matched a reserved slot")
badges_before = len(getattr(r, "_target_labels", []))
r.show_target_indicators([0])
badge_frames = [b.winfo_x() for b in r._target_labels]
if len(r._target_labels) != 1:
    failures.append(f"badges should appear only on real enemies: {len(r._target_labels)}")
else:
    print("OK — badges landed only on the real enemy slot")
r.hide_target_indicators()

# 5. Enemy column and party column stay identical widths.
if r.enemy_col.winfo_width() != r.party_col.winfo_width():
    failures.append("enemy/party columns have different widths")
else:
    print("OK — columns remain equal width")

# 6. Empty slots stay invisible even after target-selection outline cycles.
r.refresh(player, enemies(2))
root.update_idletasks(); root.update()
r.clear_target_highlight()
real, empty = r._enemy_frames[0], r._enemy_frames[4]
if str(empty.cget("highlightbackground")).lower() != str(Theme.BG_DARK).lower():
    failures.append("empty slot picked up a target-selection outline")
if str(real.cget("highlightbackground")).lower() != str(Theme.BORDER).lower():
    failures.append("real enemy card did not get the cleared highlight")
if not failures:
    print("OK — empty slots skip the target-selection outline")

# A highlighted card that empties out (enemy defeated) resets to invisible.
r.refresh(player, enemies(1))
root.update_idletasks(); root.update()
if str(r._enemy_frames[1].cget("highlightbackground")).lower() != str(Theme.BG_DARK).lower():
    failures.append("stale selection outline leaked onto a freed slot")
else:
    print("OK — freed slots drop stale outlines")

root.destroy()
if failures:
    print("\nFAILURES:")
    for f in failures:
        print(" -", f)
    sys.exit(1)
print("\nALL CHECKS PASSED")
