# Temp verification (2026-10-07): the action panel must keep the SAME height
# whether the current menu needs 1 or 2 button rows, and whether the cooldown
# line is empty, short, or wraps to two lines. Reserves: second button row +
# second cooldown line (combat UI has spare room since the HUD rework).
# 2026-10-15 (wave 2): extended to the 9-skill + utility worst case.
import sys
sys.path.insert(0, "c:/Code/Pandemonium")

import tkinter as tk
from gui.combat import action_panel as ap

FAILS = []


def check(label, cond, extra=""):
    print(("PASS" if cond else "FAIL"), "-", label, extra)
    if not cond:
        FAILS.append(label)


def fake_menu(count, disabled=0):
    menu = "  ".join(f"[{i + 1}] Skill {i + 1}" for i in range(count))
    valid = [str(i + 1) for i in range(count)]
    disabled_keys = [f"[{100 + i}]" for i in range(disabled)]
    return menu, valid, disabled_keys


root = tk.Tk()
root.geometry("1400x900")
panel = ap.ActionPanel(root, on_action=lambda k: None)
panel.pack(fill=tk.X, padx=10, pady=(0, 10))
root.update()

COOLDOWNS = [
    "(Sunfire Breath recharging: 6 turn(s))",
    "(Heart of Tin recharging: 4 turn(s))",
    "(Fate's Favor recharging: 3 turn(s))",
]

# ── 1 row of 7 buttons, no cooldowns ──
ap.get_action_menu = lambda p, e: fake_menu(7)
panel.set_actions({}, [])
root.update_idletasks()
h_1row = panel.winfo_reqheight()

# ── 2 rows (9 buttons), no cooldowns ──
ap.get_action_menu = lambda p, e: fake_menu(9)
panel.set_actions({}, [])
root.update_idletasks()
h_2row = panel.winfo_reqheight()

# ── 1 row + cooldown list ──
ap.get_action_menu = lambda p, e: fake_menu(7)
panel.set_actions({}, [], cooldowns=COOLDOWNS)
root.update_idletasks()
h_1row_cd = panel.winfo_reqheight()

# ── 2 rows + cooldown list ──
ap.get_action_menu = lambda p, e: fake_menu(9)
panel.set_actions({}, [], cooldowns=COOLDOWNS)
root.update_idletasks()
h_2row_cd = panel.winfo_reqheight()

# ── 1 row + disabled workshop buttons pushing it to 2 rows anyway ──
ap.get_action_menu = lambda p, e: fake_menu(7, disabled=2)
panel.set_actions({}, [])
root.update_idletasks()
h_1row_disabled = panel.winfo_reqheight()

# ── duplicate-capture prompt (3 choice buttons) uses the same reservation ──
panel.set_capture_choice_actions(lambda k: None)
root.update_idletasks()
h_capture = panel.winfo_reqheight()

check("1-row menu == 2-row menu height", h_1row == h_2row, f"({h_1row} vs {h_2row})")
check("1-row+cooldown == 2-row+cooldown height", h_1row_cd == h_2row_cd, f"({h_1row_cd} vs {h_2row_cd})")
check("empty cooldown reserves same as filled cooldown", h_1row == h_1row_cd, f"({h_1row} vs {h_1row_cd})")
check("disabled-key rows keep the same height", h_1row == h_1row_disabled, f"({h_1row} vs {h_1row_disabled})")
check("capture-choice prompt == regular panel height", h_capture == h_1row, f"({h_capture} vs {h_1row})")

# ── Wave 2: full 9-skill menu + utility buttons (worst realistic case) ──
ap.get_action_menu = lambda p, e: fake_menu(15)
panel.set_actions({}, [])
root.update_idletasks()
h_15 = panel.winfo_reqheight()
ap.get_action_menu = lambda p, e: fake_menu(16)
panel.set_actions({}, [])
root.update_idletasks()
h_16 = panel.winfo_reqheight()
check("15-button menu (9 skills + utility) keeps height", h_15 == h_1row, f"({h_15} vs {h_1row})")
check("16-button menu keeps height", h_16 == h_1row, f"({h_16} vs {h_1row})")

root.destroy()
print()
if FAILS:
    print("FAILURES:", FAILS)
    sys.exit(1)
print("OK: action panel height is constant")
