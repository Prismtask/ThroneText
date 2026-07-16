"""
gui/combat/action_panel.py — Dynamic action buttons for combat.

Builds Attack, Defend, Skills, Items, Flee, Capture buttons from
combat/action_menu.py. Handles cooldown grey-out and target-selection mode.
"""

import tkinter as tk

from gui.theme import Theme
from combat.action_menu import get_action_menu
from combat.ally import _ally_action_menu


class ActionPanel(tk.Frame):
    """
    Bottom action bar for the combat screen.
    Dynamically generates buttons based on the current combatant's available actions.
    """

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

        # Target-mode instruction label (hidden by default)
        self.target_instruction = tk.Label(
            self,
            text="",
            bg=Theme.BG_DARK,
            fg=Theme.ACCENT,
            font=Theme.FONT_BOLD,
            anchor=tk.W,
        )

        # Cooldown messages
        self.cooldown_label = tk.Label(
            self,
            text="",
            bg=Theme.BG_DARK,
            fg=Theme.TEXT_DIM,
            font=(Theme.FONT_FAMILY, 9),
            anchor=tk.W,
            wraplength=700,
        )
        self.cooldown_label.pack(fill=tk.X, pady=(4, 0))

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
            ally_name = active_ally.get("name", "Ally")
        else:
            menu_str, valid_actions, disabled_keys = get_action_menu(player, enemies)

        # Visual distinction for ally turns
        if ally_name:
            self.section_label.config(
                text=f"▶ {ally_name}'s Turn — Choose Action",
                fg="#3498db",
            )
            self.config(bg="#16213e")
            self.btn_container.config(bg="#16213e")
        else:
            self.section_label.config(text="ACTIONS", fg=Theme.TEXT_DIM)
            self.config(bg=Theme.BG_DARK)
            self.btn_container.config(bg=Theme.BG_DARK)

        # Create buttons in rows of 7
        MAX_PER_ROW = 7
        row_frame = None
        for i, key in enumerate(valid_actions):
            if i % MAX_PER_ROW == 0:
                row_frame = tk.Frame(self.btn_container, bg=self.btn_container["bg"])
                row_frame.pack(fill=tk.X, pady=1)
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
            idx = len(valid_actions) + i
            if idx % MAX_PER_ROW == 0:
                row_frame = tk.Frame(self.btn_container, bg=self.btn_container["bg"])
                row_frame.pack(fill=tk.X, pady=1)
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
        self.target_instruction.pack_forget()
        self.cooldown_label.config(text="")

        choices = [
            ("1", "Sell for Gold"),
            ("2", "Release to Wild"),
            ("3", "Bond (+20 Affection)"),
        ]
        for key, label in choices:
            btn = tk.Button(
                self.btn_container,
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

    def set_target_mode(self, enabled: bool, prompt: str = "Select a target", is_ally_target: bool = False):
        """Enable/disable target selection mode."""
        if enabled:
            self.section_label.config(text=prompt, fg=Theme.ACCENT)
            # Show instruction label with keyboard + click hints
            target_type = "ally" if is_ally_target else "enemy"
            self.target_instruction.config(
                text=f"▶ Press 1–9 or click a {target_type} to select target  (Esc to cancel)",
            )
            self.target_instruction.pack(fill=tk.X, pady=(4, 4), before=self.btn_container)
            # Disable non-target actions, keep Cancel implicit
            for key, btn in self._buttons.items():
                if key not in ("0", "cancel"):
                    btn.config(state=tk.DISABLED)
        else:
            self.section_label.config(text="ACTIONS", fg=Theme.TEXT_DIM)
            self.target_instruction.pack_forget()
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
