"""Headless-ish geometry check: OK-dialog sizing keeps the button visible.

Opens the real ok_dialog twice (the Glass Anchor / Resonance Orb examine
bodies from the 2026-09-28 bug report) and measures the dialog + button
geometry. The dialogs flash briefly on screen — run manually.

Bug: height was estimated from source lines only; a long wrapped
description (Glass Anchor: 1 source line -> 4 visual lines) made the
window too short and the packer clipped the OK button (packed last,
after the expand=True label). Fixed by counting wrapped lines and
packing the button bottom-first.

Run:
    .venv\\Scripts\\python.exe tests\\_diag_dialog_sizing.py
"""
import os
import sys
import tkinter as tk

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gui.widgets.confirm_dialog import ok_dialog, _estimate_dialog_size

ANCHOR_MSG = ("Glass Anchor  (Legendary)\n\n"
              "A crystalline shard attuned to the Isle of Glass, torn from the "
              "heart of its deepest dungeon. It resonates with the island's "
              "unstable magic, allowing arcane teleportation to breach the "
              "Isle's wards from outside.")

ORB_MSG = ("Resonant Orb  (Mythic)\n\n"
           "✦ ✦ ✦ ✦ ✦ ✦\n\n"
           "The orb sings. Not loudly — completely. Every bond in your ledger "
           "is in the note, and the note is in tune.\n\n"
           "Grade: Crescendo — 4 front / 4 bench\n"
           "The orb is whole, and it sings.")


def _walk(widget):
    for child in widget.winfo_children():
        yield child
        yield from _walk(child)


def _check(root, title, message):
    # What ok_dialog will set (min_width=300, base_height=90, max_width=480)
    est_w, est_h = _estimate_dialog_size(message, min_width=300,
                                         base_height=90, max_width=480)
    ok_dialog(root, title, message)
    root.update()
    dlg = [w for w in root.winfo_children() if isinstance(w, tk.Toplevel)][-1]
    dlg.update_idletasks()
    # Natural (packed) size of the content — the dialog must cover this or
    # the packer clips the last widget (the OK button).
    req_w, req_h = dlg.winfo_reqwidth(), dlg.winfo_reqheight()
    btns = [w for w in _walk(dlg) if isinstance(w, tk.Button)]
    assert btns, "no button found"
    b = btns[0]
    btn_req_h = b.winfo_reqheight()
    print(f"{title}: set_by_estimator={est_w}x{est_h} "
          f"content_required={req_w}x{req_h} button_req_h={btn_req_h}")
    assert btn_req_h >= 20, f"button implausibly small: {btn_req_h}"
    assert est_h >= req_h, \
        f"content ({req_h}px) exceeds dialog height ({est_h}px) — button would clip"
    dlg.destroy()
    return btn_req_h


root = tk.Tk()
root.withdraw()
h_anchor = _check(root, "Glass Anchor", ANCHOR_MSG)
h_orb = _check(root, "Resonant Orb", ORB_MSG)
root.destroy()

assert h_anchor == h_orb, (h_anchor, h_orb)
print("Dialog sizing OK — button fully visible in both.")
