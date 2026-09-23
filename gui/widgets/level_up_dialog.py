"""
gui/widgets/level_up_dialog.py — Modal level-up dialogs for attribute selection
and results display.

Provides GUI popups for level-up events that work regardless of context
(dungeon, travel, world map, facilities).  Replaces the terminal-based
_tmenu/_tprint fallback in leveling.py with proper tkinter dialogs.

Works correctly both on the main thread (synchronous wait_window) and
from background threads (queue-based scheduling via root.after).

Usage:

    from gui.widgets.level_up_dialog import (
        choose_level_up_attribute,
        show_level_up_results,
    )

    # Phase 1: pick an attribute  (blocks until user chooses)
    chosen = choose_level_up_attribute("Hero", 47, {"Strength": 11, ...})
    if chosen is None:
        chosen = random.choice(attrs)

    # Apply the change (caller's responsibility)
    player["attributes"][chosen] += 1
    # ... calculate HP, skills, milestones ...

    # Phase 2: show results  (blocks until user clicks Continue)
    show_level_up_results(
        entity_name="Hero", level=47,
        chosen_attr=chosen, new_value=player["attributes"][chosen],
        hp_increase=4, new_max_hp=220,
        new_skills=["Fireball"],
        milestones=["Learning reached milestone 10! Passive bonus increased!"],
    )
"""

import queue
import threading
import traceback
import tkinter as tk
from typing import Optional, List, Dict

from gui.theme import Theme


class LevelUpDialogError(Exception):
    """Raised when the level-up dialog could not be built/shown on the GUI
    thread.  Carries the original traceback so callers can log the real
    failure reason instead of silently degrading."""
    pass

# Map attribute keys to display names and icons
_ATTR_DISPLAY = {
    "Strength":     ("\U0001f4aa Strength",     Theme.BUFF_NEGATIVE),
    "Constitution": ("\U0001f9ec Constitution", Theme.BUFF_POSITIVE),
    "Dexterity":    ("\U0001f3af Dexterity",    Theme.BUFF_NEUTRAL),
    "Wisdom":       ("\U0001f4d6 Wisdom",       Theme.MP_BAR_FILL),
    "Learning":     ("\U0001f4d8 Learning",     Theme.XP_BAR_FILL),
    "Charisma":     ("\U0001f31f Charisma",     Theme.ACCENT_HOVER),
}

_ATTR_ORDER = ["Strength", "Constitution", "Dexterity",
               "Wisdom", "Learning", "Charisma"]


def _safe_toplevel(parent=None):
    """Return a usable tkinter toplevel/root, trying several fallbacks."""
    try:
        return parent.winfo_toplevel()
    except (tk.TclError, AttributeError):
        pass
    try:
        if tk._default_root:
            return tk._default_root
    except Exception:
        pass
    root = tk.Tk()
    root.withdraw()
    return root


def _has_gui():
    """Return True if tkinter has a root window (GUI is available)."""
    try:
        return tk._default_root is not None
    except Exception:
        return False


def _is_main_thread():
    """Return True if the calling thread is the main thread."""
    return threading.current_thread() is threading.main_thread()


# ═══════════════════════════════════════════════════════════════════════════
#  Public API
# ═══════════════════════════════════════════════════════════════════════════

def choose_level_up_attribute(entity_name: str,
                              level: int,
                              attributes: Dict[str, int],
                              parent=None) -> Optional[str]:
    """
    Show a modal dialog for choosing which attribute to increase on level-up.

    Blocks until the user clicks an attribute button or closes the dialog.
    Safe to call from any thread.

    Returns the chosen attribute key (e.g. "Strength"), or None if the
    dialog was closed without a choice (caller should pick randomly).
    """
    if not _has_gui():
        return None

    if _is_main_thread():
        # Main thread: build and run dialog synchronously
        dlg = _AttrChoiceDialog(entity_name, level, attributes, parent)
        dlg.dialog.wait_window()  # Processes tkinter events
        return dlg._result
    else:
        # Background thread: schedule on main thread, block on queue
        result_queue = queue.Queue()

        def _build():
            try:
                dlg = _AttrChoiceDialog(entity_name, level, attributes, parent)
                dlg._result_queue = result_queue
            except Exception:
                result_queue.put(("__ERROR__", traceback.format_exc()))

        root = tk._default_root
        if root is None:
            return None
        root.after(0, _build)

        try:
            out = result_queue.get(timeout=120)
        except queue.Empty:
            return None
        if isinstance(out, tuple) and out and out[0] == "__ERROR__":
            raise LevelUpDialogError(out[1])
        return out


def show_level_up_results(entity_name: str,
                          level: int,
                          chosen_attr: str,
                          new_value: int,
                          hp_increase: int = 0,
                          new_max_hp: int = 0,
                          new_skills: Optional[List[str]] = None,
                          milestones: Optional[List[str]] = None,
                          parent=None):
    """
    Show a modal dialog displaying the results of a level-up.

    Blocks until the user clicks Continue. Safe to call from any thread.
    If the GUI is not available, this is a no-op.
    """
    if not _has_gui():
        return

    if _is_main_thread():
        dlg = _ResultsDialog(
            entity_name=entity_name,
            level=level,
            chosen_attr=chosen_attr,
            new_value=new_value,
            hp_increase=hp_increase,
            new_max_hp=new_max_hp,
            new_skills=new_skills or [],
            milestones=milestones or [],
            parent=parent,
        )
        dlg.dialog.wait_window()
    else:
        result_queue = queue.Queue()

        def _build():
            try:
                dlg = _ResultsDialog(
                    entity_name=entity_name,
                    level=level,
                    chosen_attr=chosen_attr,
                    new_value=new_value,
                    hp_increase=hp_increase,
                    new_max_hp=new_max_hp,
                    new_skills=new_skills or [],
                    milestones=milestones or [],
                    parent=parent,
                )
                dlg._result_queue = result_queue
            except Exception:
                result_queue.put(("__ERROR__", traceback.format_exc()))

        root = tk._default_root
        if root is None:
            return
        root.after(0, _build)

        try:
            out = result_queue.get(timeout=120)
        except queue.Empty:
            return
        if isinstance(out, tuple) and out and out[0] == "__ERROR__":
            raise LevelUpDialogError(out[1])


# ═══════════════════════════════════════════════════════════════════════════
#  Internal dialogs
# ═══════════════════════════════════════════════════════════════════════════

class _AttrChoiceDialog:
    """Modal Toplevel for picking an attribute to increase."""

    def __init__(self, entity_name, level, attributes, parent=None):
        self._result = None
        self._result_queue = None  # Set externally for cross-thread use

        top = _safe_toplevel(parent) if parent else _safe_toplevel()
        self.dialog = tk.Toplevel(top)
        self.dialog.title("Level Up!")
        self.dialog.transient(top)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)
        self.dialog.configure(bg=Theme.BG_DARK)

        # ── Header ────────────────────────────────────────────────────
        header = tk.Frame(self.dialog, bg=Theme.BG_DARK)
        header.pack(fill=tk.X, padx=24, pady=(18, 6))

        tk.Label(
            header,
            text="\u2b50  LEVEL UP!  \u2b50",
            bg=Theme.BG_DARK,
            fg=Theme.XP_BAR_FILL,
            font=Theme.FONT_LARGE,
        ).pack()

        name_color = Theme.ACCENT if entity_name else Theme.TEXT
        tk.Label(
            header,
            text=f"{entity_name} is now level {level}",
            bg=Theme.BG_DARK,
            fg=name_color,
            font=Theme.FONT_BOLD,
        ).pack(pady=(2, 0))

        # ── Instruction ───────────────────────────────────────────────
        tk.Label(
            self.dialog,
            text="Choose an attribute to increase by 1:",
            bg=Theme.BG_DARK,
            fg=Theme.TEXT,
            font=Theme.FONT,
        ).pack(pady=(8, 8))

        # ── Attribute buttons ─────────────────────────────────────────
        btn_container = tk.Frame(self.dialog, bg=Theme.BG_DARK)
        btn_container.pack(fill=tk.BOTH, expand=True, padx=24, pady=(0, 16))

        for i, attr_key in enumerate(_ATTR_ORDER, 1):
            current = attributes.get(attr_key, 0)
            display_name, color = _ATTR_DISPLAY.get(
                attr_key, (attr_key, Theme.TEXT)
            )

            row_frame = tk.Frame(btn_container, bg=Theme.BG_DARK)
            row_frame.pack(fill=tk.X, pady=2)

            btn = tk.Button(
                row_frame,
                text=f"  {display_name}  —  current: {current}  ",
                command=lambda a=attr_key: self._choose(a),
                bg=Theme.BG_MID,
                fg=Theme.TEXT,
                activebackground=color,
                activeforeground=Theme.TEXT_HEADER,
                font=Theme.FONT,
                cursor="hand2",
                anchor=tk.W,
                padx=12,
                pady=6,
                relief=tk.FLAT,
                bd=1,
            )
            btn.pack(fill=tk.X)

            # Hover effects
            btn.bind("<Enter>",
                     lambda e, b=btn, c=color: b.configure(
                         bg=c, fg=Theme.TEXT_HEADER))
            btn.bind("<Leave>",
                     lambda e, b=btn: b.configure(
                         bg=Theme.BG_MID, fg=Theme.TEXT))

            # Number key shortcut
            self.dialog.bind(str(i),
                             lambda e, a=attr_key: self._choose(a))

        # ── Keyboard & close ──────────────────────────────────────────
        self.dialog.bind("<Escape>", self._on_close)
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_close)

        # Center & show
        self._center(400, 150 + len(_ATTR_ORDER) * 42)
        self.dialog.wait_visibility()
        self.dialog.lift()
        self.dialog.focus_force()

    def _choose(self, attr_key):
        self._result = attr_key
        self._notify()
        self.dialog.destroy()

    def _on_close(self, _event=None):
        self._result = None
        self._notify()
        self.dialog.destroy()

    def _notify(self):
        """If a result_queue was set (cross-thread mode), push the result."""
        if self._result_queue is not None:
            self._result_queue.put(self._result)

    def _center(self, width, height):
        try:
            sw = self.dialog.winfo_screenwidth()
            sh = self.dialog.winfo_screenheight()
            x = (sw - width) // 2
            y = (sh - height) // 2
        except Exception:
            x, y = 200, 150
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")


class _ResultsDialog:
    """Modal Toplevel for showing level-up results."""

    def __init__(self, entity_name, level, chosen_attr, new_value,
                 hp_increase, new_max_hp, new_skills, milestones,
                 parent=None):
        self._result_queue = None  # Set externally for cross-thread use

        top = _safe_toplevel(parent) if parent else _safe_toplevel()
        self.dialog = tk.Toplevel(top)
        self.dialog.title("Level Up!")
        self.dialog.transient(top)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)
        self.dialog.configure(bg=Theme.BG_DARK)

        display_name, color = _ATTR_DISPLAY.get(
            chosen_attr, (chosen_attr, Theme.TEXT)
        )

        # ── Header ────────────────────────────────────────────────────
        header = tk.Frame(self.dialog, bg=Theme.BG_DARK)
        header.pack(fill=tk.X, padx=24, pady=(18, 8))

        tk.Label(
            header,
            text="\u2b50  LEVEL UP!  \u2b50",
            bg=Theme.BG_DARK,
            fg=Theme.XP_BAR_FILL,
            font=Theme.FONT_LARGE,
        ).pack()

        tk.Label(
            header,
            text=f"{entity_name} is now level {level}",
            bg=Theme.BG_DARK,
            fg=Theme.ACCENT,
            font=Theme.FONT_BOLD,
        ).pack(pady=(2, 0))

        # ── Results ───────────────────────────────────────────────────
        body = tk.Frame(self.dialog, bg=Theme.BG_DARK)
        body.pack(fill=tk.BOTH, expand=True, padx=24, pady=4)

        # Attribute change
        tk.Label(
            body,
            text=f"{display_name}  \u2192  {new_value}",
            bg=Theme.BG_DARK,
            fg=color,
            font=Theme.FONT_BOLD,
        ).pack(anchor=tk.W, pady=(0, 8))

        # HP increase
        if hp_increase > 0:
            tk.Label(
                body,
                text=f"\u2764  Max HP +{hp_increase}   \u2192   New max: {new_max_hp}",
                bg=Theme.BG_DARK,
                fg=Theme.BUFF_POSITIVE,
                font=Theme.FONT,
            ).pack(anchor=tk.W, pady=2)

        # New skills
        if new_skills:
            skills_text = ", ".join(new_skills)
            tk.Label(
                body,
                text=f"\u2728  NEW SKILL(S): {skills_text}",
                bg=Theme.BG_DARK,
                fg=Theme.XP_BAR_FILL,
                font=Theme.FONT_BOLD,
                wraplength=340,
                justify=tk.LEFT,
            ).pack(anchor=tk.W, pady=(8, 2))

        # Milestones
        if milestones:
            for msg in milestones:
                tk.Label(
                    body,
                    text=msg,
                    bg=Theme.BG_DARK,
                    fg=Theme.ACCENT_HOVER,
                    font=Theme.FONT,
                    wraplength=340,
                    justify=tk.LEFT,
                ).pack(anchor=tk.W, pady=1)

        # ── Continue button ───────────────────────────────────────────
        btn_area = tk.Frame(self.dialog, bg=Theme.BG_DARK)
        btn_area.pack(fill=tk.X, pady=(8, 16))

        cont_btn = tk.Button(
            btn_area,
            text="Continue",
            command=self._dismiss,
            bg=Theme.ACCENT,
            fg=Theme.TEXT_HEADER,
            activebackground=Theme.ACCENT_HOVER,
            font=Theme.FONT_BOLD,
            cursor="hand2",
            width=14,
            padx=8,
            pady=4,
        )
        cont_btn.pack()
        cont_btn.focus_set()

        self.dialog.bind("<Return>", lambda e: self._dismiss())
        self.dialog.bind("<KP_Enter>", lambda e: self._dismiss())
        self.dialog.bind("<Escape>", lambda e: self._dismiss())
        self.dialog.protocol("WM_DELETE_WINDOW", self._dismiss)

        # Size & center
        needed_h = 230
        if new_skills:
            needed_h += 30
        if milestones:
            needed_h += len(milestones) * 24
        self._center(400, min(needed_h, 550))

        self.dialog.wait_visibility()
        self.dialog.lift()
        self.dialog.focus_force()

    def _dismiss(self):
        if self._result_queue is not None:
            self._result_queue.put(True)
        self.dialog.destroy()

    def _center(self, width, height):
        try:
            sw = self.dialog.winfo_screenwidth()
            sh = self.dialog.winfo_screenheight()
            x = (sw - width) // 2
            y = (sh - height) // 2
        except Exception:
            x, y = 200, 150
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")
