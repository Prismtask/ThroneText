"""
gui/screens/combat_screen.py — Main combat screen.

Runs the combat engine in a background thread, bridges I/O via queues,
and renders the combat HUD + action buttons in tkinter.
"""

import tkinter as tk
import threading
import queue
import re

from gui.screens.base_screen import BaseScreen
from gui.theme import Theme
from gui.combat.combat_renderer import CombatRenderer
from gui.combat.action_panel import ActionPanel
from gui.widgets.confirm_dialog import ok_dialog
from combat.combat_io import BaseCombatIO, get_io, set_io, reset_io
from combat.combat_engine import combat
from combat.stats import enemy_stats
from utils import strip_ansi


# ── GUI-specific I/O bridge ──────────────────────────────────────────────────

class GUICombatIO(BaseCombatIO):
    """
    Bridges combat thread I/O to the tkinter GUI via queues.
    The GUI polls the output_queue; the combat thread blocks on input_queue.
    """

    def __init__(self):
        self.input_queue = queue.Queue()
        self.output_queue = queue.Queue()
        self._active = True

    def print(self, *args, **kwargs):
        text = " ".join(str(a) for a in args)
        self.output_queue.put(("OUTPUT", text))

    def input(self, prompt=""):
        self.output_queue.put(("INPUT_NEEDED", prompt))
        return self.input_queue.get()

    def clear(self):
        self.output_queue.put(("CLEAR", None))

    def send_input(self, text: str):
        """Called by GUI thread to provide input."""
        self.input_queue.put(text)

    def stop(self):
        self._active = False
        # Unblock any waiting input
        self.input_queue.put("")


# ── Main screen ───────────────────────────────────────────────────────────────

class CombatScreen(BaseScreen):
    """
    Full-screen combat interface.

    Constructor kwargs (pop before BaseScreen sees them):
        enemy_keys   — list of enemy key strings
        floor        — current dungeon floor (optional)
        room_num     — current room number (optional)
        total_rooms  — total rooms on floor (optional)
        on_result    — callback(result_str) when combat ends
    """

    def __init__(self, parent, screen_manager,
                 enemy_keys=None, floor=None, room_num=None,
                 total_rooms=None, on_result=None, is_overlay=False,
                 combat_context=None, combat_func=None, **kwargs):
        # Ensure screen_manager/player are available before use
        self.sm = screen_manager
        self.player = screen_manager.player if screen_manager else None

        self.enemy_keys = enemy_keys or []
        self.floor = floor
        self.room_num = room_num
        self.total_rooms = total_rooms
        self.combat_context = combat_context
        self.on_result = on_result
        self.is_overlay = is_overlay  # True when shown via push_overlay
        self._combat_func = combat_func  # Custom combat function (superboss, etc.)

        self.io = GUICombatIO()
        self._combat_thread = None
        self._poll_id = None
        self._hud_poll_id = None
        self._pending_input_mode = None
        self._target_callback = None
        self._destroyed = False  # Guard against after() callbacks after destroy
        self._target_context = False  # Set when recent output suggests target selection
        self._ally_target_context = False  # Set when recent output suggests ALLY target selection
        self._revive_target_context = False  # Set when recent output suggests revive (dead ally) target selection
        self._capture_context = False  # Set when recent output suggests capture target selection
        self._target_index_map = {}  # Maps frame index → badge number for target selection

        # Create enemy instances up-front so GUI can reference them
        self.enemies = []
        if self.player and self.enemy_keys:
            self.enemies = [enemy_stats(k, self.player) for k in self.enemy_keys]

        super().__init__(parent, screen_manager, **kwargs)

    def build_ui(self):
        self.sm.clear_log()
        if self.combat_context == "superboss":
            self.sm.update_top_bar(f"⚔ Superboss | Floor {self.floor or '?'}")
        elif self.combat_context == "travel":
            self.sm.update_top_bar("Combat | On the Road")
        elif self.combat_context == "training":
            self.sm.update_top_bar("⚔ Sparring | Training Dummy")
        else:
            top = f"Combat | Floor {self.floor or '?'} | Room {self.room_num or '?'}/{self.total_rooms or '?'}"
            # ── Pandemonium: append active curse to the top bar ─────────
            if self.player and self.player.get("pandemonium_mode"):
                curse = self.player.get("pandemonium_curse")
                if curse:
                    top += f" | {curse.get('icon', '☠️')} {curse.get('name', '')}"
            # ── Wonderland: append active quirk + shadows ───────────────
            elif self.player and self.player.get("dungeon_region") == "wonderland":
                from wonderland_curses import format_quirk_summary
                qs = format_quirk_summary(self.player)
                if qs:
                    top += f" | {qs}"
            self.sm.update_top_bar(top)

        self._active_ally = None  # Track which ally's turn it is
        self._actual_turn_order = None  # Parsed from engine output (labels list)
        self._turn_step_prefix = ""     # e.g. "[2/7]" for the current combatant

        # ── Top: Combat HUD ──────────────────────────────────────────────────
        self.renderer = CombatRenderer(self)
        self.renderer.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Bind enemy clicks for target selection (recursive — covers all descendants)
        self.renderer.bind_enemy_clicks(self._on_enemy_click)

        # Bind party clicks for ally target selection
        self.renderer.bind_party_clicks(self._on_party_click)

        # ── Middle: Log ──────────────────────────────────────────────────────
        log_frame = tk.LabelFrame(
            self,
            text=" Combat Log ",
            bg=Theme.BG_DARK,
            fg=Theme.TEXT_DIM,
            font=Theme.FONT_BOLD,
            highlightthickness=1,
            highlightbackground=Theme.BORDER,
        )
        log_frame.pack(fill=tk.X, padx=10, pady=(0, 8))
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(0, weight=1)

        self.log_text = tk.Text(
            log_frame,
            height=5,
            wrap=tk.WORD,
            state=tk.DISABLED,
            bg=Theme.BG_DARK,
            fg=Theme.TEXT,
            font=(Theme.FONT_FAMILY, 9),
            highlightthickness=0,
            borderwidth=0,
        )
        self.log_text.grid(row=0, column=0, sticky="nsew", padx=(5, 0), pady=5)

        log_scroll = tk.Scrollbar(
            log_frame,
            command=self.log_text.yview,
            bg=Theme.BG_MID,
            troughcolor=Theme.BG_DARK,
        )
        log_scroll.grid(row=0, column=1, sticky="ns", padx=(0, 5), pady=5)
        self.log_text.config(yscrollcommand=log_scroll.set)
        # Bind mouse wheel to scroll
        self.log_text.bind("<MouseWheel>", lambda e: self.log_text.yview_scroll(-1 * (e.delta // 120), "units"))

        # ── Bottom: Action Panel ─────────────────────────────────────────────
        self.action_panel = ActionPanel(
            self,
            on_action=self._on_action_click,
        )
        self.action_panel.pack(fill=tk.X, padx=10, pady=(0, 10))

        # ── Continue button (hidden by default) ──────────────────────────────
        self.continue_btn = tk.Button(
            self,
            text="▶ Continue",
            bg=Theme.ACCENT,
            fg=Theme.TEXT_HEADER,
            font=Theme.FONT_LARGE,
            relief=tk.RAISED,
            borderwidth=3,
            cursor="hand2",
            command=self._on_continue_click,
        )
        # Don't pack yet — shown only when needed

        # ── Item selection list (hidden by default) ──────────────────────────
        self.item_frame = tk.Frame(self, bg=Theme.BG_DARK)
        self.item_listbox = tk.Listbox(
            self.item_frame,
            bg=Theme.BG_MID,
            fg=Theme.TEXT,
            font=Theme.FONT,
            selectmode=tk.SINGLE,
            height=6,
        )
        self.item_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        item_scroll = tk.Scrollbar(self.item_frame, command=self.item_listbox.yview)
        item_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.item_listbox.config(yscrollcommand=item_scroll.set)

        self.item_confirm_btn = tk.Button(
            self.item_frame,
            text="Use Item",
            bg=Theme.ACCENT,
            fg=Theme.TEXT_HEADER,
            font=Theme.FONT_BOLD,
            command=self._on_item_confirmed,
        )
        self.item_cancel_btn = tk.Button(
            self.item_frame,
            text="Cancel",
            bg=Theme.BUTTON_BG,
            fg=Theme.BUTTON_FG,
            font=Theme.FONT_BOLD,
            command=self._on_item_cancelled,
        )
        self.item_confirm_btn.pack(side=tk.LEFT, padx=4)
        self.item_cancel_btn.pack(side=tk.LEFT, padx=4)

        # ── Keyboard bindings ────────────────────────────────────────────────
        self._setup_key_binds()

        # ── Destroy guard ───────────────────────────────────────────────────
        # Belt-and-suspenders: bind <Destroy> so _destroyed is set even if the
        # widget is torn down at the Tcl level without going through destroy().
        self.bind("<Destroy>", self._on_destroy_event)

        # Start combat thread
        self._start_combat()
        self._schedule_poll()
        self._schedule_hud_refresh()

    def _update_top_bar(self):
        """Called by the game clock tick — preserves curse/quirk info in combat."""
        if self.combat_context == "superboss":
            top = f"⚔ Superboss | Floor {self.floor or '?'}"
        elif self.combat_context == "travel":
            top = "Combat | On the Road"
        elif self.combat_context == "training":
            top = "⚔ Sparring | Training Dummy"
        else:
            top = f"Combat | Floor {self.floor or '?'} | Room {self.room_num or '?'}/{self.total_rooms or '?'}"
            if self.player and self.player.get("pandemonium_mode"):
                curse = self.player.get("pandemonium_curse")
                if curse:
                    top += f" | {curse.get('icon', '☠️')} {curse.get('name', '')}"
            elif self.player and self.player.get("dungeon_region") == "wonderland":
                from wonderland_curses import format_quirk_summary
                qs = format_quirk_summary(self.player)
                if qs:
                    top += f" | {qs}"
        self.sm.update_top_bar(top)

    # ── Keyboard bindings ────────────────────────────────────────────────────

    def _setup_key_binds(self):
        """Bind combat action keys to this screen."""
        self.bind("<KeyPress>", self._on_key)
        self.focus_set()

    def _on_key(self, event):
        """Handle keyboard action shortcuts."""
        key = event.char.lower()

        # If we're in continue mode, Enter triggers continue
        if self.continue_btn.winfo_ismapped():
            if event.keysym == "Return" or event.keysym == "KP_Enter":
                if hasattr(self, '_handle_result_pending'):
                    self._finish_combat()
                else:
                    self.io.send_input("")
                    self.continue_btn.pack_forget()
                    self.action_panel.pack(fill=tk.X, padx=10, pady=(0, 10))
            return

        # If item selection is visible, handle Enter/Esc there
        if self.item_frame.winfo_ismapped():
            if event.keysym == "Return" or event.keysym == "KP_Enter":
                self._on_item_confirmed()
            elif event.keysym == "Escape":
                self._on_item_cancelled()
            return

        # If in target mode, number keys select targets, Esc cancels, Enter confirms first
        if self._pending_input_mode in ("enemy_target", "capture_target", "ally_target", "ally_switch"):
            if event.keysym == "Escape":
                self.io.send_input("0")
                self.renderer.clear_target_highlight()
                self.renderer.hide_target_indicators()
                self.action_panel.set_target_mode(False)
                self.action_panel.enable_all()
                self._pending_input_mode = None
                if self.player:
                    self.player["_ally_switch_mode"] = False
                return
            if event.keysym in ("Return", "KP_Enter"):
                # Enter/Return → select the first available target (badge #1)
                frame_idx = None
                for fi, bn in self._target_index_map.items():
                    if bn == 1:
                        frame_idx = fi
                        break
                if frame_idx is not None:
                    if self._pending_input_mode == "ally_target":
                        self._on_party_click(frame_idx)
                    else:
                        self._on_enemy_click(frame_idx)
                return
            if key and key in "123456789":
                badge_num = int(key)
                # Find the frame index that corresponds to this badge number
                frame_idx = None
                for fi, bn in self._target_index_map.items():
                    if bn == badge_num:
                        frame_idx = fi
                        break
                if frame_idx is not None:
                    if self._pending_input_mode == "ally_target":
                        self._on_party_click(frame_idx)
                    else:
                        self._on_enemy_click(frame_idx)
            return

        # Map keys to action keys
        key_map = {
            "a": "a",      # Attack
            "d": "d",      # Defend
            "f": "f",      # Flee
            "c": "c",      # Capture
            "u": "u",      # Use Item
            "0": "0",      # Cancel
        }

        # Number keys 1-9 map directly to skill keys "1"-"9"
        if key and key in "123456789":
            mapped = key
        elif key in key_map:
            mapped = key_map[key]
        elif event.keysym == "Escape":
            # Esc during action mode = Cancel (key "0")
            mapped = "0"
        else:
            return

        # Check if this action is currently available
        if mapped in self.action_panel._buttons:
            self._on_action_click(mapped)

    def handle_escape(self):
        """Override: Esc does nothing in combat unless in target mode."""
        if self._pending_input_mode in ("enemy_target", "capture_target", "ally_target"):
            self.io.send_input("0")
            self.renderer.clear_target_highlight()
            self.renderer.hide_target_indicators()
            self.action_panel.set_target_mode(False)
            self.action_panel.enable_all()
            self._pending_input_mode = None

    # ── Combat thread lifecycle ───────────────────────────────────────────────

    def _start_combat(self):
        """Launch combat in a daemon thread."""
        # ── Reconcile vorpal skills before combat ─────────────────────────
        # Safety net: ensures all heroines' innate/learned skills match their
        # vorpal flags before combat actions are built.
        from character import _reconcile_heroine_vorpal_skills
        for ally in self.player.get("allies", []):
            _reconcile_heroine_vorpal_skills(ally, self.player)

        def run_combat():
            set_io(self.io)
            try:
                if self._combat_func:
                    # Custom combat function (superboss, etc.)
                    # Pass enemies for shared state so the HUD renderer sees live enemy data.
                    result = self._combat_func(
                        self.player,
                        floor=self.floor,
                        enemies=self.enemies,
                    )
                else:
                    result = combat(
                        self.player,
                        self.enemy_keys,
                        floor=self.floor,
                        room_num=self.room_num,
                        total_rooms=self.total_rooms,
                        enemies=self.enemies,
                    )
                self.io.output_queue.put(("RESULT", result))
            except Exception as e:
                import traceback
                self.io.output_queue.put(("ERROR", str(e) + "\n" + traceback.format_exc()))
            finally:
                reset_io()

        self._combat_thread = threading.Thread(target=run_combat, daemon=True)
        self._combat_thread.start()

    # ── Polling loop ──────────────────────────────────────────────────────────

    def _schedule_poll(self):
        self._poll_id = self.after(100, self._poll)

    def _poll(self):
        """Process events from the combat thread."""
        if self._destroyed:
            return
        while True:
            try:
                event = self.io.output_queue.get(block=False)
            except queue.Empty:
                break

            kind, data = event
            if kind == "INPUT_NEEDED":
                self._handle_input_needed(data)
            elif kind == "OUTPUT":
                self._handle_output(data)
            elif kind == "CLEAR":
                self._clear_log()
            elif kind == "RESULT":
                self._handle_result(data)
                return
            elif kind == "ERROR":
                self._handle_error(data)
                return

        if not self._destroyed:
            self._schedule_poll()

    def _schedule_hud_refresh(self):
        """Poll player/enemy state and update the HUD renderer."""
        if self._destroyed:
            return
        self._refresh_hud()
        self._hud_poll_id = self.after(200, self._schedule_hud_refresh)

    # ── Event handlers ────────────────────────────────────────────────────────

    def _handle_input_needed(self, prompt: str):
        """Combat thread is waiting for input — show appropriate UI."""
        mode, context = self._parse_prompt(prompt)

        # Use output context to detect target selection when prompt is ambiguous
        # (e.g. "Choice:" after "Select target:" output)
        # Note: "Choice:" is parsed as "capture_target" by _parse_prompt,
        # but if the preceding output was an ally target list, override to ally_target.
        if self._ally_target_context or self._revive_target_context:
            mode = "ally_target"
        elif self._target_context and mode in ("action", "capture_target") and not self._capture_context:
            mode = "enemy_target"
        self._target_context = False  # Reset after consuming
        self._ally_target_context = False  # Reset after consuming
        revive_mode = self._revive_target_context
        self._revive_target_context = False  # Reset after consuming
        self._capture_context = False  # Reset after consuming

        self._pending_input_mode = mode

        # Detect ally switch mode from player state
        if self.player and self.player.get("_ally_switch_mode"):
            self._pending_input_mode = "ally_switch"
            # Force immediate HUD refresh to show backup party
            self._refresh_hud()

        # Detect and store active ally from prompt context
        self._active_ally = self._resolve_active_ally(context)

        if self._pending_input_mode == "continue":
            # Show Continue button, hide actions
            self._active_ally = None  # Continue prompts are never per-ally
            self.action_panel.pack_forget()
            self.continue_btn.pack(fill=tk.X, padx=10, pady=(0, 10))

        elif self._pending_input_mode == "action":
            # Show action buttons for the current combatant (player or ally)
            self.continue_btn.pack_forget()
            self.item_frame.pack_forget()
            self.action_panel.pack(fill=tk.X, padx=10, pady=(0, 10))
            self.renderer.clear_target_highlight()
            enemies = self._enemies_snapshot()
            self.action_panel.set_actions(
                self.player, enemies,
                active_ally=self._active_ally,
                cooldowns=self._get_current_cooldowns(),
            )

        elif self._pending_input_mode == "enemy_target":
            # Refresh HUD first to ensure frames match the current (pruned) enemy list
            self.continue_btn.pack_forget()
            self.item_frame.pack_forget()
            self._refresh_hud()
            # Build list of alive enemy indices for target badges and a mapping
            # from frame index → badge number so clicks send the correct input.
            # Use snapshot to avoid racing the combat thread's in-place prune.
            enemies = self._enemies_snapshot()
            alive_indices = [i for i, e in enumerate(enemies)
                             if e.get("hp", 0) > 0 and not e.get("captured")]
            self._target_index_map = {idx: badge_num + 1 for badge_num, idx in enumerate(alive_indices)}
            self.action_panel.set_target_mode(True, "Select a target")
            self.renderer.show_target_indicators(alive_indices)
            for i in alive_indices:
                self.renderer.highlight_enemy(i)

        elif self._pending_input_mode == "capture_target":
            # Refresh HUD first to ensure frames match the current enemy list
            self.continue_btn.pack_forget()
            self.item_frame.pack_forget()
            self._refresh_hud()
            # Build list of alive monster-girl enemy indices for target badges.
            # Use snapshot to avoid racing the combat thread's in-place prune.
            enemies = self._enemies_snapshot()
            mg_indices = [i for i, e in enumerate(enemies)
                          if e.get("hp", 0) > 0 and not e.get("captured") and e.get("monster_girl")]
            self._target_index_map = {idx: badge_num + 1 for badge_num, idx in enumerate(mg_indices)}
            self.action_panel.set_target_mode(True, "Select a monster girl to capture")
            self.renderer.show_target_indicators(mg_indices)
            for i in mg_indices:
                self.renderer.highlight_enemy(i)

        elif self._pending_input_mode == "ally_target":
            # Refresh HUD to ensure party frames are up-to-date
            self.continue_btn.pack_forget()
            self.item_frame.pack_forget()
            self._refresh_hud()
            # Build list of targetable party members
            # revive_mode: only show dead allies; otherwise show alive
            party = self._get_party_snapshot()
            if revive_mode:
                targetable = [i for i, m in enumerate(party)
                              if m.get("current_hp", m.get("hp", 1)) <= 0]
                prompt = "Select a fallen ally to revive"
            else:
                targetable = [i for i, m in enumerate(party)
                              if m.get("current_hp", m.get("hp", 1)) > 0]
                prompt = "Select an ally"
            self._target_index_map = {idx: badge_num + 1 for badge_num, idx in enumerate(targetable)}
            self.action_panel.set_target_mode(True, prompt, is_ally_target=True)
            self.renderer.show_ally_target_indicators(targetable)
            for i in targetable:
                self.renderer.highlight_ally(i)

        elif self._pending_input_mode == "ally_switch":
            # Ally is switching with a reserve party member.
            # The renderer shows reserve allies in the enemy column (switch_mode=True).
            self.continue_btn.pack_forget()
            self.item_frame.pack_forget()
            self._refresh_hud()
            # Build target mapping for reserve allies shown in enemy column
            from combat.ally import get_reserve_allies
            reserve = get_reserve_allies(self.player)
            self._target_index_map = {idx: badge_num + 1 for badge_num, idx in enumerate(range(len(reserve)))}
            self.action_panel.set_target_mode(True, "Select a reserve ally to swap with")
            for i in range(len(reserve)):
                self.renderer.highlight_enemy(i)

        elif self._pending_input_mode == "item":
            # Show item selection UI (uses player inventory; ally turns use same items)
            self.continue_btn.pack_forget()
            self.action_panel.pack_forget()
            self._show_item_selection()

        elif self._pending_input_mode == "capture_net_select":
            # Show capture-net-only selection UI
            self.continue_btn.pack_forget()
            self.action_panel.pack_forget()
            self._show_capture_net_selection()

        elif self._pending_input_mode == "capture_choice":
            # Capture duplicate menu: show Sell / Release / Bond as action buttons
            self.continue_btn.pack_forget()
            self.item_frame.pack_forget()
            self.action_panel.pack(fill=tk.X, padx=10, pady=(0, 10))
            self.action_panel.set_capture_choice_actions(self._on_action_click)

        else:
            # Fallback: show action buttons
            self.action_panel.pack(fill=tk.X, padx=10, pady=(0, 10))
            enemies = self._enemies_snapshot()
            self.action_panel.set_actions(self.player, enemies, active_ally=self._active_ally)

    def _handle_output(self, text: str):
        """Append combat output to the log widget and detect target-selection context.

        Filters out HUD/UI/prompt messages so the combat log only shows
        combat events: damage, heals, skills, DoT ticks, status effects.
        Also captures the engine's real turn order and turn-step indicators.
        """
        # Detect round header and update the top bar
        if ">> ROUND" in text:
            self._on_round_header(text)

        # Detect combat engine's actual Turn Order and update renderer
        if "Turn Order:" in text:
            self._on_turn_order(text)

        # Detect turn-step indicator: "[n/m] Name's Turn:"
        turn_match = re.match(r'^\s*\[(\d+/\d+)\]\s+(.+)\'s\s+Turn:', text.strip())
        if turn_match:
            self._turn_step_prefix = f"[{turn_match.group(1)}]"
            return  # Don't log this line

        # Always detect target-selection context (needed for input routing)
        lowered = text.lower()
        if "select target" in lowered or "select fallen" in lowered:
            self._target_context = True
            # Determine if this is ally or enemy targeting
            # "Select target number:" → enemy targeting
            # "Select target:" alone → ally targeting (followed by party list)
            # "Select fallen ally to revive:" → dead ally (revive) targeting
            # "Select target for X:" → enemy targeting (item usage)
            self._capture_context = "to capture" in lowered
            if "select target number" in lowered or "select target for" in lowered:
                self._ally_target_context = False   # Enemy targeting
                self._revive_target_context = False
            elif "select fallen" in lowered:
                self._ally_target_context = False   # Not regular ally
                self._revive_target_context = True  # Dead ally targeting
            elif "select target:" in lowered and not any(x in lowered for x in ["number", "for", "to capture"]):
                self._ally_target_context = True    # Ally targeting
                self._revive_target_context = False

        # Only log combat event messages
        if self._is_combat_event(text):
            if self._turn_step_prefix and self._should_apply_turn_prefix(text):
                self._append_log(f"{self._turn_step_prefix} {text.strip()}")
            else:
                self._append_log(text)

    def _should_apply_turn_prefix(self, text: str) -> bool:
        """Return True if the turn-step prefix [n/m] should be prepended.

        Only action-results get the prefix: damage, kills, defends, status
        effects, DoT ticks, heals, misses, dodges, blocks.
        Excluded: skill descriptions, mastery labels, target lists, and
        dead/captured enemy skip messages.
        """
        t = text.strip()

        # ── NEVER prefix these: they are UI/interaction, not action results ──
        # Skill descriptions (player: >>>, ally: >>)
        if t.startswith(">") and not t.startswith(">> ROUND"):
            return False
        # Mastery labels
        if t.startswith("Mastery"):
            return False
        # Enemy target lists: "  1. EnemyName (HP: X/Y)"
        if re.match(r'^\s*\d+\.\s+.+\s+\(HP:\s*\d+/\d+\)', t):
            return False
        # Ally target lists: "  1. Name (X/Y)" or "  1. Name (X/Y) [FALLEN]"
        if re.match(r'^\s*\d+\.\s+.+\s+\(\d+/\d+\)', t):
            return False
        # Dead / captured enemy skip messages
        if "is already defeated" in t or "is captured and cannot act" in t:
            return False

        # ── Everything else is an action result ─────────────────────────────
        return True

    def _on_turn_order(self, text: str):
        """Parse the engine's Turn Order line and store for the renderer."""
        # Format: "  Turn Order:  You ->  Harpy Scout ->  Goblin Girl ->  [1] Abyssal Watcher"
        # Strip the prefix and split on arrows
        after = text.split("Turn Order:", 1)[-1]
        labels = [part.strip() for part in after.split("->")]
        labels = [l for l in labels if l]  # remove empties
        # Store as list of dicts matching _compute_turn_order format
        self._actual_turn_order = [{"label": l} for l in labels]

    def _is_combat_event(self, text: str) -> bool:
        """Return True if the message is a combat event worth showing in the log.

        Combat events: damage, heals, skill usage, DoT ticks, status effects,
        buff/debuff applications, misses, dodges, blocks, round headers.
        Filtered out: HUD boxes, enemy lists, initiative, turn order,
        action prompts, separators, enemy intros.
        """
        t = text.strip()
        if not t:
            return False

        # ── Round headers: show in log AND update top bar ─────────────────
        if ">> ROUND" in t:
            return True

        # ── Skill descriptions (">>> SkillName: Description") ─────────────
        if t.startswith(">>>"):
            return True

        # ── Damage messages (use the new arrow format) ───────────────────
        if "→" in t and "dmg" in t.lower():
            return True

        # ── Explicit skip patterns: HUD boxes, prompts, UI elements ──────
        # HUD box borders
        if (t.startswith("+") and t.endswith("+") and len(t) > 40) or \
           (t.startswith("|") and ("YOUR PARTY" in t or "ENEMIES" in t or
            len(t) > 50)):
            return False

        # Enemy display list: "[1] EnemyName (HP/MaxHP)" or "  [1] Enemy Name (HP/MaxHP)"
        if re.match(r'^\s*\[\d+\]\s+.+\s+\(\d+/\d+\)', t):
            return False

        # Initiative / turn order / phase headers / ally action prompts
        skip_starts = [
            "ENEMIES:", "Rolling initiative", "Turn Order:",
            "Press Enter", "Choose", "Choice:", "Select target",
            "Available:", "Invalid", "Please enter",
            "Select fallen",
        ]
        t_lower = t.lower()
        for s in skip_starts:
            if t_lower.startswith(s.lower()):
                return False

        # Ally action prompt: "  (AllyName) Choose action: "
        if re.match(r'^\s*\(.+\)\s*[Cc]hoose', t):
            return False

        # Separator lines
        if all(c in "-─═~" for c in t) and len(t) > 10:
            return False

        # Action phase headers
        if "ACTION PHASE" in t:
            return False

        # Turn indicators: "[1/6] Name's Turn:"
        if re.match(r'^\s*\[\d+/\d+\]', t):
            return False

        # Enemy intro messages
        if "Enemies approach!" in t:
            return False
        if re.match(r'^- A .+ appears!', t):
            return False

        # Action menu lines (contain action key patterns)
        if re.search(r'\[[ADFUCadfuc]\].*[Aa]ttack|[Dd]efend|[Ff]lee|Use [Ii]tem', t):
            return False

        # Skill menu lines (numbered skills in action menu)
        if re.search(r'\[\d+\]\s*\w', t) and ("recharging" not in t.lower()):
            # Check if it looks like an action menu line with multiple [X]Label pairs
            bracket_count = len(re.findall(r'\[\w+\]', t))
            if bracket_count >= 3:
                return False

        # Separator in HUD
        if t.startswith("--") and len(t) > 20:
            return False

        # Capture duplicate menu lines (shown as GUI buttons instead)
        if "already have" in t_lower and "household" in t_lower:
            return False
        if re.match(r'^\d+\.\s*(Sell|Release|Let her bond)', t):
            return False

        # ── Everything else is a combat event ────────────────────────────
        return True

    def _on_round_header(self, text: str):
        """Extract round/floor/room/time from header and update top bar."""
        # Pattern: "  >> ROUND 2 | Floor 22 | Room 1/10 | Time: 09:14"
        clean = text.replace(">>", "").strip()
        # ── Append active curse/quirk info only during actual dungeon combat ─
        #     (not travel, training, or superboss fights)
        if self.combat_context in (None, ""):
            if self.player and self.player.get("pandemonium_mode"):
                curse = self.player.get("pandemonium_curse")
                if curse:
                    clean += f" | {curse.get('icon', '☠️')} {curse.get('name', '')}"
            elif self.player and self.player.get("dungeon_region") == "wonderland":
                from wonderland_curses import format_quirk_summary
                qs = format_quirk_summary(self.player)
                if qs:
                    clean += f" | {qs}"
        self.sm.top_name.config(text=clean)
        self.sm.top_info.config(text="")
        # Reset turn step for the new round
        self._turn_step_prefix = ""
        self._actual_turn_order = None

    def _handle_result(self, result: str):
        """Combat ended — notify caller immediately, then show Leave Battle.

        The result is delivered to the dungeon thread right away so the
        5-minute safety timeout never fires while the player reads the log.
        The Leave Battle button is purely cosmetic — it just dismisses the overlay.
        """
        self._cancel_polls()
        self._append_log(f"\n=== Combat ended: {result.upper()} ===")
        # Clear turn step prefix so the result line isn't prefixed
        self._turn_step_prefix = ""

        # ── Refresh HUD one last time to show empty enemy frame ──────────
        # The combat engine may have pruned dead enemies after the last
        # HUD poll, so force a final refresh to display the correct state.
        self._active_ally = None
        self._actual_turn_order = None
        self._refresh_hud()

        # ── Deliver result immediately ───────────────────────────────────
        # This unblocks the dungeon thread so it doesn't time out while the
        # player reviews the combat log at their own pace.
        if self.on_result:
            self._on_result_delivered = True
            self.on_result(result)

        self._handle_result_pending = result
        self.action_panel.pack_forget()
        self.item_frame.pack_forget()
        self.continue_btn.config(
            text="▶ Leave Battle",
            command=lambda: self._finish_combat(),
        )
        self.continue_btn.pack(fill=tk.X, padx=10, pady=(0, 10))

    def _finish_combat(self):
        """Proceed after combat ends — dismiss overlay (result already delivered)."""
        self.continue_btn.pack_forget()
        # Result was already delivered to the dungeon thread in _handle_result.
        # Just clean up the UI.
        if self.is_overlay:
            self.sm.dismiss_overlay()
        elif not self.on_result:
            if not self._destroyed:
                self._return_to_city()

    def _handle_error(self, error_text: str):
        """Combat thread crashed — show error and return."""
        self._cancel_polls()
        self._append_log(f"\n!!! COMBAT ERROR !!!\n{error_text}")
        ok_dialog(self, "Combat Error", f"An error occurred during combat:\n{error_text[:500]}")
        # Notify caller (e.g. dungeon thread) so it doesn't hang waiting for a result
        if self.on_result:
            self.on_result("error")
        if self.is_overlay:
            self.sm.dismiss_overlay()
        else:
            self._return_to_city()

    def _return_to_city(self):
        from gui.screens.city_screen import CityScreen
        self.sm.switch_to(CityScreen)

    # ── User input handlers ───────────────────────────────────────────────────

    def _on_action_click(self, key: str):
        """Player clicked an action button."""
        if key == "f":
            # Flee — confirm first since this abandons the dungeon run
            from gui.widgets.confirm_dialog import confirm_dialog
            confirm_dialog(
                parent=self,
                title="Flee Combat?",
                message="Flee from combat? You will return to the city.",
                on_yes=lambda: self._do_send_action(key),
            )
        else:
            self._do_send_action(key)

    def _do_send_action(self, key: str):
        """Actually send the action to the combat thread."""
        self.io.send_input(key)
        self.action_panel.disable_all()

    def _on_continue_click(self):
        """Handle Continue button click — same as pressing Enter."""
        self.io.send_input("")
        self.continue_btn.pack_forget()
        self.action_panel.pack(fill=tk.X, padx=10, pady=(0, 10))

    def _on_enemy_click(self, index: int):
        """Player clicked an enemy (target selection) or backup party ally (switch mode).
        Uses _target_index_map to translate frame index → badge number
        so the correct 1-based target number is sent to the combat engine."""
        if self._pending_input_mode in ("enemy_target", "capture_target", "ally_switch"):
            # Map frame index to badge number (1-based alive position)
            target_num = self._target_index_map.get(index)
            if target_num is None:
                return  # Clicked a dead/non-targetable enemy — ignore
            self.io.send_input(str(target_num))
            self.renderer.clear_target_highlight()
            self.renderer.hide_target_indicators()
            self.action_panel.set_target_mode(False)
            self.action_panel.disable_all()
            # Clear switch mode flag on next refresh
            if self._pending_input_mode == "ally_switch" and self.player:
                self.player["_ally_switch_mode"] = False

    def _on_party_click(self, index: int):
        """Player clicked a party member (ally target selection).
        Uses _target_index_map to translate frame index → badge number
        so the correct 1-based position is sent to the combat engine."""
        if self._pending_input_mode == "ally_target":
            target_num = self._target_index_map.get(index)
            if target_num is None:
                return  # Clicked a dead/non-targetable party member — ignore
            self.io.send_input(str(target_num))
            self.renderer.clear_target_highlight()
            self.renderer.hide_target_indicators()
            self.action_panel.set_target_mode(False)
            self.action_panel.disable_all()

    def _get_party_snapshot(self):
        """Return list of party member dicts: [player, ...allies]."""
        party = [self.player]
        for ally in self.player.get("allies", []):
            party.append(ally)
        return party

    def _show_item_selection(self):
        """Populate and show the item selection listbox."""
        self.item_listbox.delete(0, tk.END)
        self._item_refs = []

        combat_items = [
            (idx, item) for idx, item in enumerate(self.player.get("inventory", []))
            if item.get("type") in ["consumable", "utility"]
        ]

        if not combat_items:
            self._append_log("No usable items in combat.")
            self.io.send_input("0")
            return

        for display_idx, (true_idx, item) in enumerate(combat_items):
            qty = item.get("count", 1)
            qty_str = f" x{qty}" if qty > 1 else ""
            self.item_listbox.insert(tk.END, f"{display_idx + 1}. {item['name']}{qty_str}")
            self._item_refs.append((true_idx, item))

        self.item_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

    def _show_capture_net_selection(self):
        """Populate and show the item selection listbox with only capture nets."""
        self.item_listbox.delete(0, tk.END)
        self._item_refs = []

        nets = [
            (idx, item) for idx, item in enumerate(self.player.get("inventory", []))
            if item.get("capture_net")
        ]

        if not nets:
            self._append_log("No capture nets in inventory.")
            self.io.send_input("0")
            return

        for display_idx, (true_idx, net) in enumerate(nets):
            bonus = net.get("rarity_mult_bonus", 25)
            qty = net.get("count", 1)
            qty_str = f" x{qty}" if qty > 1 else ""
            self.item_listbox.insert(tk.END, f"{display_idx + 1}. {net['name']} (+{bonus} catch){qty_str}")
            self._item_refs.append((true_idx, net))

        self.item_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

    def _on_item_confirmed(self):
        """Player confirmed item selection."""
        selection = self.item_listbox.curselection()
        if not selection:
            return
        idx = selection[0]
        self.io.send_input(str(idx + 1))
        self.item_frame.pack_forget()

    def _on_item_cancelled(self):
        """Player cancelled item selection."""
        self.io.send_input("0")
        self.item_frame.pack_forget()

    # ── HUD refresh ───────────────────────────────────────────────────────────

    def _enemies_snapshot(self):
        """Return a thread-safe shallow copy of the enemy list.

        The combat engine mutates self.enemies in-place (enemies[:] = prune_dead(...))
        from its background thread. Taking a snapshot prevents "list changed size
        during iteration" RuntimeErrors when the GUI thread reads the list.
        """
        return list(self.enemies)

    def _refresh_hud(self):
        """Update renderer from shared player/enemy state."""
        # Use the engine-reported turn order if available, else compute locally
        turn_order = self._actual_turn_order or self._compute_turn_order()
        enemies = self._enemies_snapshot()
        self.renderer.refresh(self.player, enemies,
                              active_ally=self._active_ally,
                              turn_order=turn_order)

    def _compute_turn_order(self):
        """Build a turn-order preview list sorted by speed (fastest first).
        Only includes active (front-row) allies, matching the engine's roll_initiative."""
        from combat.ally import get_active_allies
        entries = []
        # Player
        p_spd = self.player.get("attributes", {}).get("Speed", 10)
        entries.append({"label": self.player.get("name", "You")[:8], "speed": p_spd})
        # Active (front-row) allies only
        for ally in get_active_allies(self.player):
            if ally.get("current_hp", 0) > 0:
                a_spd = ally.get("attributes", {}).get("Speed", 10)
                entries.append({"label": ally.get("name", "Ally")[:8], "speed": a_spd})
        # Enemies — use snapshot to avoid racing the combat thread's prune
        for enemy in self._enemies_snapshot():
            if enemy.get("hp", 0) > 0:
                e_spd = enemy.get("spd", 10)
                entries.append({"label": enemy.get("name", "?")[:8], "speed": e_spd})
        # Sort fastest first
        entries.sort(key=lambda x: x["speed"], reverse=True)
        return entries

    def _get_current_cooldowns(self):
        """Return list of cooldown strings for the action panel."""
        from combat.combat_ui import format_combat_hud_data
        enemies = self._enemies_snapshot()
        data = format_combat_hud_data(self.player, enemies, active_ally=self._active_ally)
        return data.get("cooldowns", [])

    # ── Prompt parser ─────────────────────────────────────────────────────────

    @staticmethod
    def _parse_prompt(prompt: str) -> tuple:
        """Map an input prompt to a UI mode. Returns (mode, context_dict).

        context_dict may contain:
            'ally_name': str — set when prompt matches an ally turn pattern
        """
        import re
        p = prompt.strip()
        p_lower = p.lower()

        # ── Ally turn detection: "  (AllyName) Choose action: " or "  Choose: " ──
        ally_match = re.match(r'^\s*\(([^)]+)\)\s*Choose\s+action', p, re.IGNORECASE)
        if ally_match:
            return "action", {"ally_name": ally_match.group(1).strip()}

        # ── Ally turn fallback: "Choose:" after ally menu (no name in prompt) ──
        # Check if the prompt is just "Choose:" and we recently had an ally action
        if p_lower in ("choose:", "choose"):
            return "action", None  # Could be either; context from previous prompt wins

        if p_lower in ("choose action",) or "choose action" in p_lower:
            return "action", None

        if "press enter" in p_lower:
            return "continue", None

        if "select target number" in p_lower:
            return "enemy_target", None

        if "select target for" in p_lower:
            return "enemy_target", None

        if "use which item" in p_lower:
            return "item", None

        # Capture prompts
        if "select target to capture" in p_lower:
            return "capture_target", None

        if "net choice" in p_lower:
            return "capture_net_select", None

        if "capture_duplicate_choice" in p_lower:
            return "capture_choice", None

        if p_lower == "choice:":
            return "capture_target", None

        # Generic fallback
        if "choose" in p_lower:
            return "action", None

        return "action", None

    def _resolve_active_ally(self, context: dict):
        """Find the active ally from a parsed prompt context dict.

        Returns the ally dict if found, or None if this is the player's turn.
        """
        if not context or "ally_name" not in context:
            return None
        ally_name = context["ally_name"]
        for ally in self.player.get("allies", []):
            if ally.get("name", "").lower() == ally_name.lower():
                return ally
        return None

    # ── Log helpers ───────────────────────────────────────────────────────────

    def _append_log(self, text: str):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, strip_ansi(text) + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def _clear_log(self):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state=tk.DISABLED)

    # ── Cleanup ───────────────────────────────────────────────────────────────

    def _on_destroy_event(self, event):
        """<Destroy> event handler — belt-and-suspenders guard.

        Ensures _destroyed is set and polls are cancelled even if the widget
        is torn down at the Tcl level without going through our destroy().
        Only acts on our own widget (ignores child-widget destroy events).
        """
        if event.widget is self:
            self._cancel_polls()

    def _cancel_polls(self):
        self._destroyed = True
        if self._poll_id:
            try:
                self.after_cancel(self._poll_id)
            except (ValueError, AttributeError):
                pass
            self._poll_id = None
        if self._hud_poll_id:
            try:
                self.after_cancel(self._hud_poll_id)
            except (ValueError, AttributeError):
                pass
            self._hud_poll_id = None

    def destroy(self):
        self._cancel_polls()
        self.io.stop()
        try:
            super().destroy()
        except (AttributeError, tk.TclError):
            pass  # Widget already torn down by Tcl — suppress race condition
