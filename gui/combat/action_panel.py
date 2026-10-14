"""
gui/combat/action_panel.py — Dynamic action buttons for combat.

Builds Attack, Defend, Skills, Items, Flee, Capture buttons from
combat/action_menu.py. Handles cooldown grey-out and target-selection mode.
"""

import tkinter as tk

from gui.theme import Theme
from combat.action_menu import get_action_menu
from combat.ally import _ally_action_menu
from utils import display_name


class ActionPanel(tk.Frame):
    """
    Bottom action bar for the combat screen.
    Dynamically generates buttons based on the current combatant's available actions.
    """

    # Button rows the panel ALWAYS reserves (see _reserve_rows) so 1-row and
    # 2-row menus render at identical height — spare room from the HUD rework.
    MIN_ROWS = 2

    def __init__(self, parent, on_action=None, **kwargs):
        """
        Args:
            on_action: callback(action_key: str) called when a button is clicked.
        """
        super().__init__(parent, bg=Theme.BG_DARK, **kwargs)
        self.on_action = on_action
        self._buttons = {}
        self._build_layout()

    def _build_layout(self):
        # Section label
        self.section_label = tk.Label(
            self,
            text="ACTIONS",
            bg=Theme.BG_DARK,
            fg=Theme.TEXT_DIM,
            font=Theme.FONT_BOLD,
        )
        self.section_label.pack(anchor=tk.W, pady=(0, 4))

        # Button container (flows left-to-right, wrapping)
        self.btn_container = tk.Frame(self, bg=Theme.BG_DARK)
        self.btn_container.pack(fill=tk.X)

        # Target-mode instruction label — PACKED ALWAYS (its one-line slot is
        # reserved even when idle) so entering/leaving target selection never
        # changes the panel height. Its text is cleared when not targeting.
        self.target_instruction = tk.Label(
            self,
            text="",
            bg=Theme.BG_DARK,
            fg=Theme.ACCENT,
            font=Theme.FONT_BOLD,
            anchor=tk.W,
            height=1,
        )
        self.target_instruction.pack(fill=tk.X, pady=(4, 4), before=self.btn_container)

        # Cooldown messages — ALWAYS two lines tall, even when empty, so the
        # panel height never jumps between 1-line and 2-line cooldown lists
        # (mirrors the reserved second button row below).
        self.cooldown_label = tk.Label(
            self,
            text="",
            bg=Theme.BG_DARK,
            fg=Theme.TEXT_DIM,
            font=(Theme.FONT_FAMILY, 9),
            anchor=tk.W,
            justify=tk.LEFT,
            height=2,
            wraplength=700,
        )
        self.cooldown_label.pack(fill=tk.X, pady=(4, 0))

        # Wrap cooldown text at the panel's real width instead of a fixed
        # 700px cap — uses the space freed by the HUD rework.
        self._cooldown_wrap = 700
        self.bind("<Configure>", self._on_panel_configure)

        # ── Reserve the panel's final height from the very first frame ────
        # The combat screen sizes the Continue/Leave Battle slot from
        # `reserved_height`, and the first prompt of a fight ('Press Enter to
        # begin...') arrives before set_actions() ever runs — so the two
        # button rows must be reserved here too, using a probe button to
        # measure the real row height.
        probe = tk.Button(
            self.btn_container, text="X",
            font=Theme.FONT_BOLD, relief=tk.RAISED, borderwidth=2,
        )
        self.update_idletasks()
        row_h = probe.winfo_reqheight() + 4  # + button pady (2 top/bottom)
        probe.destroy()
        for _ in range(self.MIN_ROWS):
            spacer = tk.Frame(self.btn_container, bg=self.btn_container["bg"], height=row_h)
            spacer.pack(fill=tk.X, pady=1)

        # Canonical height — constant for the panel's whole lifetime;
        # set_actions() rebuilds its rows at exactly this size.
        self.update_idletasks()
        self.reserved_height = self.winfo_reqheight()

    # ── Public API ────────────────────────────────────────────────────────────

    def set_actions(self, player, enemies, active_ally=None, cooldowns=None):
        """Rebuild buttons from the current action menu."""
        # Clear existing
        for widget in self.btn_container.winfo_children():
            widget.destroy()
        self._buttons.clear()

        # Fetch menu
        ally_name = None
        disabled_keys = []
        if active_ally is not None:
            menu_str, valid_actions, disabled_keys = _ally_action_menu(active_ally, player, enemies)
            ally_name = display_name(active_ally) or "Ally"
        else:
            menu_str, valid_actions, disabled_keys = get_action_menu(player, enemies)

        # Header is always "ACTIONS" — player and ally turns must match.
        # The lighter panel tint is the only remaining ally-turn cue.
        self.section_label.config(text="ACTIONS", fg=Theme.TEXT_DIM)
        if ally_name:
            self.config(bg="#16213e")
            self.btn_container.config(bg="#16213e")
        else:
            self.config(bg=Theme.BG_DARK)
            self.btn_container.config(bg=Theme.BG_DARK)

        # Create buttons in rows of 7. A second row is ALWAYS reserved (even
        # when this menu only needs one) so the panel — and therefore the
        # whole bottom section — keeps the same size on every turn. The HUD
        # rework left enough spare room for this (2026-10-07 feedback).
        MAX_PER_ROW = 7
        rows = []

        def _row_for(index):
            while len(rows) * MAX_PER_ROW <= index:
                rf = tk.Frame(self.btn_container, bg=self.btn_container["bg"])
                rf.pack(fill=tk.X, pady=1)
                rows.append(rf)
            return rows[index // MAX_PER_ROW]

        for i, key in enumerate(valid_actions):
            row_frame = _row_for(i)
            label = self._label_for_key(key, menu_str)
            btn = tk.Button(
                row_frame,
                text=f"[{key.upper()}] {label}",
                bg=Theme.BUTTON_BG,
                fg=Theme.BUTTON_FG,
                activebackground=Theme.BUTTON_ACTIVE_BG,
                activeforeground=Theme.BUTTON_ACTIVE_FG,
                font=Theme.FONT_BOLD,
                relief=tk.RAISED,
                borderwidth=2,
                cursor="hand2",
                command=lambda k=key, e=None: self._click(k),
            )
            btn.bind("<Enter>", lambda e=None, b=btn: b.config(bg=Theme.BUTTON_ACTIVE_BG))
            btn.bind("<Leave>", lambda e=None, b=btn: b.config(bg=Theme.BUTTON_BG))
            btn.pack(side=tk.LEFT, padx=4, pady=2)
            self._buttons[key] = btn

        # Disabled buttons (used workshops) — greyed out, not clickable
        for i, key in enumerate(disabled_keys):
            row_frame = _row_for(len(valid_actions) + i)
            label = self._label_for_key(key, menu_str)
            btn = tk.Button(
                row_frame,
                text=f"[{key.upper()}] {label}",
                bg=Theme.BG_MID,
                fg=Theme.TEXT_DIM,
                font=Theme.FONT_BOLD,
                relief=tk.SUNKEN,
                borderwidth=2,
                state=tk.DISABLED,
            )
            btn.pack(side=tk.LEFT, padx=4, pady=2)
            self._buttons[key] = btn

        # Pad a short menu with an invisible spacer row so a 1-row menu gets
        # exactly the same height as a 2-row menu (constant panel size).
        self._reserve_rows(rows)

        # Cooldown messages
        if cooldowns:
            self.cooldown_label.config(text="  |  ".join(cooldowns))
        else:
            self.cooldown_label.config(text="")

    def set_capture_choice_actions(self, on_action):
        """Show 3 buttons for capture duplicate: Sell / Release / Bond."""
        # Clear existing
        for widget in self.btn_container.winfo_children():
            widget.destroy()
        self._buttons.clear()

        self.section_label.config(
            text="⌖ Duplicate Monster Girl Captured — Choose Action",
            fg="#e67e22",
        )
        self.config(bg=Theme.BG_DARK)
        self.btn_container.config(bg=Theme.BG_DARK)
        self.target_instruction.config(text="")
        self.cooldown_label.config(text="")

        choices = [
            ("1", "Sell for Gold"),
            ("2", "Release to Wild"),
            ("3", "Bond (+20 Affection)"),
        ]
        row_frame = tk.Frame(self.btn_container, bg=Theme.BG_DARK)
        row_frame.pack(fill=tk.X, pady=1)
        for key, label in choices:
            btn = tk.Button(
                row_frame,
                text=f"[{key}] {label}",
                bg=Theme.BUTTON_BG,
                fg=Theme.BUTTON_FG,
                activebackground=Theme.BUTTON_ACTIVE_BG,
                activeforeground=Theme.BUTTON_ACTIVE_FG,
                font=Theme.FONT_BOLD,
                relief=tk.RAISED,
                borderwidth=2,
                cursor="hand2",
                command=lambda k=key, e=None: self._click(k),
            )
            btn.bind("<Enter>", lambda e=None, b=btn: b.config(bg=Theme.BUTTON_ACTIVE_BG))
            btn.bind("<Leave>", lambda e=None, b=btn: b.config(bg=Theme.BUTTON_BG))
            btn.pack(side=tk.LEFT, padx=4, pady=2)
            self._buttons[key] = btn

        # Same row reservation as the regular panel so this prompt keeps the
        # exact panel height (see _reserve_rows).
        self._reserve_rows([row_frame])

    def set_target_mode(self, enabled: bool, prompt: str = "Select a target", is_ally_target: bool = False):
        """Enable/disable target selection mode."""
        if enabled:
            self.section_label.config(text=prompt, fg=Theme.ACCENT)
            # Instruction label is always packed (slot reserved) — set text only
            target_type = "ally" if is_ally_target else "enemy"
            self.target_instruction.config(
                text=f"▶ Press 1–9 or click a {target_type} to select target  (Esc to cancel)",
            )
            # Disable non-target actions, keep Cancel implicit
            for key, btn in self._buttons.items():
                if key not in ("0", "cancel"):
                    btn.config(state=tk.DISABLED)
        else:
            self.section_label.config(text="ACTIONS", fg=Theme.TEXT_DIM)
            self.target_instruction.config(text="")
            self.config(bg=Theme.BG_DARK)
            self.btn_container.config(bg=Theme.BG_DARK)
            for btn in self._buttons.values():
                btn.config(state=tk.NORMAL)

    def enable_all(self):
        """Enable all buttons."""
        for btn in self._buttons.values():
            btn.config(state=tk.NORMAL)

    def disable_all(self):
        """Disable all buttons (e.g. during enemy turns)."""
        for btn in self._buttons.values():
            btn.config(state=tk.DISABLED)

    # ── Internals ─────────────────────────────────────────────────────────────

    def _reserve_rows(self, rows):
        """Pad `rows` with invisible spacer frames up to MIN_ROWS so short
        menus keep the same panel height as full two-row menus."""
        self.update_idletasks()
        row_h = rows[0].winfo_reqheight() if rows else 0
        while len(rows) < self.MIN_ROWS:
            spacer = tk.Frame(self.btn_container, bg=self.btn_container["bg"], height=row_h)
            spacer.pack(fill=tk.X, pady=1)
            rows.append(spacer)

    def _on_panel_configure(self, event):
        """Re-wrap cooldown text at the panel's actual (spare) width."""
        wrap = max(300, event.width - 4)
        if wrap != self._cooldown_wrap:
            self._cooldown_wrap = wrap
            self.cooldown_label.config(wraplength=wrap)

    def _click(self, key):
        """Handle button click with brief visual flash."""
        btn = self._buttons.get(key)
        if btn:
            btn.config(bg=Theme.ACCENT)
            btn.after(100, lambda b=btn: b.config(bg=Theme.BUTTON_ACTIVE_BG if b.cget("state") != "disabled" else Theme.BUTTON_BG))
        if self.on_action:
            self.on_action(key)

    @staticmethod
    def _label_for_key(key, menu_str):
        """Extract the label for a given action key from the menu string."""
        for part in menu_str.split("  "):
            part = part.strip()
            if part.startswith(f"[{key.upper()}]"):
                return part[len(f"[{key.upper()}]"):]
            if part.startswith(f"[{key.lower()}]"):
                return part[len(f"[{key.lower()}]"):]
        return key
