"""Phase 0 import verification script."""
import sys
sys.path.insert(0, ".")

errors = []

# Test imports that don't need a display
try:
    from gui.theme import Theme, FONT_FAMILY, WINDOW_DEFAULT_SIZE
    print("[OK] gui.theme")
except Exception as e:
    errors.append(f"gui.theme: {e}")
    print(f"[FAIL] gui.theme: {e}")

try:
    from gui.notification_queue import NotificationQueue
    nq = NotificationQueue()
    nq.push("test", "info")
    assert len(nq) == 1
    print("[OK] gui.notification_queue")
except Exception as e:
    errors.append(f"gui.notification_queue: {e}")
    print(f"[FAIL] gui.notification_queue: {e}")

try:
    from gui.io_redirector import GUIRedirector
    print("[OK] gui.io_redirector")
except Exception as e:
    errors.append(f"gui.io_redirector: {e}")
    print(f"[FAIL] gui.io_redirector: {e}")

# Test launcher import
try:
    import launcher
    print("[OK] launcher.py")
except Exception as e:
    errors.append(f"launcher: {e}")
    print(f"[FAIL] launcher: {e}")

# Test widgets (no tk root needed for class definition)
try:
    import tkinter as tk
    root = tk.Tk()
    root.withdraw()

    from gui.widgets.hp_bar import HPBar
    bar = HPBar(root, current=50, maximum=100)
    assert bar.get_percentage() == 50.0
    print("[OK] gui.widgets.hp_bar")

    from gui.widgets.stat_display import StatDisplay
    sd = StatDisplay(root, name="STR", base=8, equipment=2, buff=1)
    print("[OK] gui.widgets.stat_display")

    from gui.widgets.item_card import ItemCard
    ic = ItemCard(root, item={"name": "Test Sword", "rarity": "rare", "slot": "weapon", "stats": {"atk": 5}})
    print("[OK] gui.widgets.item_card")

    from gui.widgets.confirm_dialog import confirm_dialog, ok_dialog
    print("[OK] gui.widgets.confirm_dialog")

    root.destroy()
except Exception as e:
    errors.append(f"gui.widgets: {e}")
    print(f"[FAIL] gui.widgets: {e}")

# Test screens / app (need display)
try:
    import tkinter as tk
    root = tk.Tk()
    root.withdraw()

    from gui.screens.base_screen import BaseScreen
    print("[OK] gui.screens.base_screen")

    from gui.screen_manager import ScreenManager
    sm = ScreenManager(root)
    print("[OK] gui.screen_manager")

    from gui.app import PandemoniumApp, run_gui
    print("[OK] gui.app")

    root.destroy()
except Exception as e:
    errors.append(f"gui.app/screens: {e}")
    print(f"[FAIL] gui.app/screens: {e}")

print()
if errors:
    print(f"Phase 0 verification FAILED with {len(errors)} error(s):")
    for err in errors:
        print(f"  - {err}")
    sys.exit(1)
else:
    print("Phase 0 verification PASSED - all modules import and instantiate correctly.")
    sys.exit(0)
