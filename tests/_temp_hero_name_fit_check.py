# Temp check (2026-11-05): city hero-card names ellipsize to FIXED slots.
#
# Repro: the player name can include a title ("hundur the Hundred") and ally
# nicknames are free text; the single-row party card grew past the window, and
# short names produced visibly smaller boxes than long ones. Boxes must keep
# the size they have in a full 8-actor card even with only 2 members.
#
# Run: .venv\Scripts\python.exe tests\_temp_hero_name_fit_check.py
import sys
import tkinter as tk
import tkinter.font as tkfont
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gui.screens.city_screen import (
    CityScreen, HERO_CARD_MAX_SLOTS, HERO_ROW_EXTRAS_MAX, _fit_text_to_width,
)
from gui.theme import Theme


class DummyScreen:
    """Minimal `self` for the unbound _fit_hero_names helper."""

    def __init__(self, labels):
        self._hero_name_labels = labels
        self._hero_party_row = None
        self._hero_fit_state = None
        self._hero_row_extras = HERO_ROW_EXTRAS_MAX
        self._hero_blocks = []

    def winfo_exists(self):
        return True


def main():
    root = tk.Tk()
    root.geometry("1x1+0+0")

    # 1. Pixel-accurate truncation.
    bold = tkfont.Font(font=Theme.FONT_BOLD)
    full = "hundur the Hundred"
    assert _fit_text_to_width(full, Theme.FONT_BOLD, 10_000) == full
    for width in (40, 60, 90, 120):
        out = _fit_text_to_width(full, Theme.FONT_BOLD, width)
        assert bold.measure(out) <= width, (width, out, bold.measure(out))
        assert out.endswith("…"), (width, out)
    assert _fit_text_to_width(full, Theme.FONT_BOLD, 2) == ""
    print("OK — _fit_text_to_width respects the pixel budget")

    # 2. Fixed 8-actor slots, even with only 2 members, at the min window.
    from gui.widgets.hp_bar import HPBar

    frame = tk.Frame(root)
    frame.pack()
    labels = []
    blocks = []
    for full_name, level, tags in (
            ("hundur the Hundred", 10, "[DMG+50% RST BLV STN SLW BLD FRZ]"),
            ("Ninetales Fox the Everlasting", 42, "[+LEA +DEX]")):
        block = tk.Frame(frame)
        block.pack(side=tk.LEFT, padx=(0, 8))
        name_row = tk.Frame(block)
        name_row.pack(anchor=tk.W)
        name_lbl = tk.Label(name_row, text=full_name, font=Theme.FONT_BOLD)
        name_lbl.pack(side=tk.LEFT)
        level_lbl = tk.Label(name_row, text=f"Lv.{level}", font=Theme.FONT_BOLD)
        level_lbl.pack(side=tk.LEFT, padx=(5, 0))
        hp = HPBar(block, current=99, maximum=100, width=90, height=14,
                   show_text=True)
        hp.pack(anchor=tk.W)
        tag_lbl = tk.Label(block, text=tags, font=(Theme.FONT_FAMILY, 7),
                           anchor=tk.W)
        tag_lbl.pack(anchor=tk.W)
        labels.append((name_lbl, level_lbl, full_name))
        blocks.append((block, hp, tag_lbl, tags))
    root.update_idletasks()

    dummy = DummyScreen(labels)
    dummy._hero_blocks = blocks
    CityScreen._fit_hero_names(dummy, row_width=840)
    root.update_idletasks()

    slot = max(56, (840 - HERO_ROW_EXTRAS_MAX) // HERO_CARD_MAX_SLOTS)
    block_w = max(52, slot - 4)
    assert HERO_CARD_MAX_SLOTS * slot + HERO_ROW_EXTRAS_MAX <= 840
    for name_lbl, level_lbl, full_name in labels:
        text = name_lbl.cget("text")
        assert text != full_name, (full_name, text)
        used = bold.measure(text) + level_lbl.winfo_reqwidth() + 5
        assert used <= block_w, (full_name, used, block_w)
        print(f"   {full_name!r} → {text!r} ({used}px ≤ {block_w}px)")

    # Equal-width boxes: short and long names get the same card size.
    widths = {int(b.cget("width")) for b, *_ in blocks}
    heights = {int(b.cget("height")) for b, *_ in blocks}
    assert widths == {block_w}, widths
    assert len(heights) == 1, heights
    assert {hp._width for _, hp, _, _ in blocks} == {max(50, block_w - 10)}, \
        [hp._width for _, hp, _, _ in blocks]
    assert blocks[0][2].cget("text") != blocks[0][3].strip(), \
        "overlong tag should be ellipsized"
    # 2 members use only 2 fixed slots — the rest of the row stays empty.
    assert 2 * (block_w + 4) + 8 < 840
    print("OK — all member boxes share one fixed width/height")

    # 3. A wide row leaves the full names alone.
    dummy._hero_fit_state = None
    CityScreen._fit_hero_names(dummy, row_width=3000)
    for name_lbl, _, full_name in labels:
        assert name_lbl.cget("text") == full_name
    print("OK — wide rows keep full names")
    print("OK — party slots ellipsize long names")

    root.destroy()
    print("\nAll hero-name fit checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
