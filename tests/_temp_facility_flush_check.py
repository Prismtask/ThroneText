# Temp verification (2026-10-27): FacilityScreen._flush_output no longer
# raises TclError when the widget tree was destroyed before the after(0, …)
# callback fires (stale callback from a worker thread).
import sys
import threading
import queue
import tkinter as tk

sys.path.insert(0, "c:/Code/Pandemonium")
from gui.screens.facility_screen import FacilityScreen

root = tk.Tk()
root.withdraw()
host = tk.Frame(root)
host.pack()

screen = FacilityScreen.__new__(FacilityScreen)
tk.Frame.__init__(screen, host)
screen._stopped = False
screen._finished = False
screen._thread = None
screen._input_queue = queue.Queue()
screen._pending_lines = []
screen._pending_lock = threading.Lock()
screen.loading_label = None
text = tk.Text(screen)
text.pack()
text.config(state=tk.DISABLED)
screen.output_text = text

checks = []


def check(name, cond, detail=""):
    checks.append(bool(cond))
    print(("PASS" if cond else "FAIL") + f" — {name}" + (f" ({detail})" if detail else ""))


# 1. Live widget: flush still writes and leaves the Text read-only
screen._pending_lines.append("hello")
screen._flush_output()
content = text.get("1.0", tk.END)
check("live flush writes text", "hello" in content, content.strip())
check("text stays read-only", str(text.cget("state")) == "disabled", text.cget("state"))

# 2. Destroyed widget, _stopped set by destroy(): flush is a no-op, no TclError
screen._pending_lines.append("late")
screen.destroy()
screen._flush_output()
check("flush after destroy is safe", True)
check("destroy sets _stopped", screen._stopped is True)

# 3. Destroyed widget with _stopped manually cleared: winfo_exists guard holds
screen._stopped = False
screen._pending_lines.append("late2")
try:
    screen._flush_output()
    check("dead-widget guard holds", True)
except tk.TclError as exc:
    check("dead-widget guard holds", False, str(exc))

# 4. _show_input_prompt unblocks the worker queue instead of touching widgets
screen._stopped = False
try:
    screen._show_input_prompt("prompt")
    unblocked = screen._input_queue.get_nowait() == ""
    check("dead input prompt unblocks worker", unblocked)
except (tk.TclError, queue.Empty) as exc:
    check("dead input prompt unblocks worker", False, repr(exc))

root.destroy()
failed = checks.count(False)
print(f"\n{len(checks) - failed}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
