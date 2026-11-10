"""Phase 1 import verification script."""
import sys
sys.path.insert(0, ".")

errors = []

# Test character.py refactor
try:
    from character import build_character, create_character, allocate_points, player_max_hp
    # Test build_character pure function
    attrs = {"Strength": 5, "Constitution": 5, "Dexterity": 5, "Wisdom": 5, "Learning": 5, "Charisma": 5}
    p = build_character("1", "1", attrs, "Test", 99)
    assert p["name"] == "Test"
    assert p["race"] == "Human"
    assert p["class"] == "Warrior"
    assert p["save_slot"] == 99
    print("[OK] character.py refactor (build_character)")
except Exception as e:
    errors.append(f"character.py: {e}")
    print(f"[FAIL] character.py: {e}")

# Test GUI screens (need tk root)
try:
    import tkinter as tk
    root = tk.Tk()
    root.withdraw()

    from gui.screens.main_menu_screen import MainMenuScreen
    print("[OK] gui.screens.main_menu_screen")

    from gui.screens.char_create_screen import CharCreateScreen
    print("[OK] gui.screens.char_create_screen")

    from gui.screens.city_screen import CityScreen
    print("[OK] gui.screens.city_screen")

    from gui.app import PandemoniumApp, run_gui
    print("[OK] gui.app")

    root.destroy()
except Exception as e:
    errors.append(f"gui imports: {e}")
    print(f"[FAIL] gui imports: {e}")

print()
if errors:
    print(f"Phase 1 verification FAILED with {len(errors)} error(s):")
    for err in errors:
        print(f"  - {err}")
    sys.exit(1)
else:
    print("Phase 1 verification PASSED - all modules import and build_character works.")
    sys.exit(0)
