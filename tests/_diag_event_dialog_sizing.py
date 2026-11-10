"""Geometry check: the Event Notice dialog never clips its event text.

Regression for the 2026-10-24 overflow report: the popup height was
estimated as 210 + 95 per event, which cannot know how many wrapped lines
a description takes (wild-dungeon spawn notices list every ruin). The body
is now measured after layout and turns scrollable when it cannot fit on
screen.

Opens the real dialog twice (short pair + overflowing pile). The dialogs
flash briefly — run manually from the repo root:

    .venv\\Scripts\\python.exe tests\\_diag_event_dialog_sizing.py
"""
import os
import sys
import tkinter as tk

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gui.widgets.event_dialog import _EventNoticeDialog


SPAWN_DESC = (
    "4 wild dungeons appeared on the world map:\n"
    "  • Glacial Maw — Lv 15 (3 floors) near Stormhold\n"
    "  • Brine-Soaked Spray-Ruins — Lv 6 (3 floors) near Ashkara\n"
    "  • Wind-Scoured Gallery — Lv 10 (6 floors) near Elderfen\n"
    "  • Verdant Vault — Lv 11 (3 floors) near Solmere"
)

SHORT_EVENTS = [
    {"name": "Heavy Rain",
     "desc": "Rain lashes the city. Travel takes 30% longer.",
     "fixed": False},
    {"name": "Strange Ruins Surfaced", "desc": SPAWN_DESC, "fixed": False},
]

MANY_EVENTS = [
    {"name": f"Event {i}", "desc": SPAWN_DESC, "fixed": bool(i % 2)}
    for i in range(12)
]


def _walk(widget):
    for child in widget.winfo_children():
        yield child
        yield from _walk(child)


def _check(root, label, events):
    dlg = _EventNoticeDialog(events, day_text="Day 28 (M1-D28)", parent=root)
    dlg.dialog.update_idletasks()

    canvas = dlg._body_canvas
    body = canvas.winfo_children()[0]   # frame hosted by the canvas window
    body_h = body.winfo_reqheight()
    canvas_h = int(canvas.cget("height"))
    window_h = dlg.dialog.winfo_height()
    scrollbars = [w for w in _walk(dlg.dialog) if isinstance(w, tk.Scrollbar)]
    packed_bars = [w for w in scrollbars if w.winfo_manager()]

    print(f"{label}: window={window_h}px body_req={body_h}px "
          f"canvas={canvas_h}px scrollable={dlg._scrollable} "
          f"scrollbars={len(packed_bars)}")

    # The Continue button must sit fully inside the window.
    btns = [w for w in _walk(dlg.dialog) if isinstance(w, tk.Button)]
    assert btns, "Continue button missing"
    btn = btns[0]
    btn_bottom = btn.winfo_rooty() - dlg.dialog.winfo_rooty() + btn.winfo_height()
    assert btn_bottom <= window_h, \
        f"Continue button clipped ({btn_bottom} > {window_h})"

    if body_h <= canvas_h:
        assert not dlg._scrollable, "scrollbar on but content fits"
        assert not packed_bars, "scrollbar packed but content fits"
    else:
        assert dlg._scrollable, "content overflows but body is not scrollable"
        assert packed_bars, "content overflows but no scrollbar is packed"
        assert canvas_h < body_h, "canvas did not clamp overflowing content"

    dlg.dialog.destroy()
    return dlg._scrollable


root = tk.Tk()
root.title("_diag_event_dialog_sizing")
fits = _check(root, "2 events (reported case)", SHORT_EVENTS)
scrolls = _check(root, "12 events (overflow)", MANY_EVENTS)
root.destroy()

assert not fits, "the reported 2-event case should fit without scrolling"
assert scrolls, "12 long events must scroll"
print("Event Notice sizing OK — no clipped text.")
