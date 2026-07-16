"""
gui/screens/facility_screen.py — Generic wrapper for all terminal-based facilities.

Runs any facility function (shop, inn, blacksmith, house, etc.) in a background
thread with monkey-patched print()/input() redirected to a tkinter Text widget.

This preserves all existing facility logic while giving it a GUI window.
"""

import builtins
import queue
import threading
import tkinter as tk
from tkinter import scrolledtext

from gui.screens.base_screen import BaseScreen
from gui.theme import Theme
from gui.widgets.confirm_dialog import confirm_dialog
from utils import strip_ansi


# ── Internal exception for clean thread abort ──────────────────────────────────

class _FacilityStopped(Exception):
    """Raised inside the facility thread when the user aborts early."""
    pass


# ── Thread-safe I/O redirection ─────────────────────────────────────────────────
# When a facility runs in a background thread, we temporarily redirect
# builtins.print and builtins.input. The patched versions check if the
# calling thread is the facility thread, and only redirect if so. This
# keeps the tkinter main thread (and any other threads) unaffected.

_facility_thread = None
_facility_screen = None
_orig_print = builtins.print
_orig_input = builtins.input


def _redirected_print(*args, **kwargs):
    """Thread-aware print() replacement."""
    text = " ".join(str(a) for a in args)
    if _facility_thread is not None and threading.current_thread() is _facility_thread:
        if _facility_screen is not None:
            _facility_screen._append_output(text)
    else:
        _orig_print(*args, **kwargs)


def _redirected_input(prompt=""):
    """Thread-aware input() replacement."""
    if _facility_thread is not None and threading.current_thread() is _facility_thread:
        if _facility_screen is not None:
            return _facility_screen._wait_for_input(prompt)
    return _orig_input(prompt)


def _redirected_clear():
    """Thread-aware clear_screen() replacement."""
    if _facility_thread is not None and threading.current_thread() is _facility_thread:
        if _facility_screen is not None:
            _facility_screen._clear_output()


def _install_redirects(screen):
    """Activate I/O redirection for the current facility thread."""
    global _facility_thread, _facility_screen
    _facility_thread = threading.current_thread()
    _facility_screen = screen
    builtins.print = _redirected_print
    builtins.input = _redirected_input


def _uninstall_redirects():
    """Restore original builtins."""
    global _facility_thread, _facility_screen
    _facility_thread = None
    _facility_screen = None
    builtins.print = _orig_print
    builtins.input = _orig_input


# ── Facility Screen ───────────────────────────────────────────────────────────

class FacilityScreen(BaseScreen):
    """
    Generic wrapper that runs a terminal-based facility in a GUI window.

    Constructor kwargs:
        title       — display title (e.g. "Shop")
        func        — callable to run (e.g. city_shop)
        func_args   — tuple of positional args for func
        func_kwargs — dict of keyword args for func
        on_close    — callback(result) when facility exits (optional)
    """

    def __init__(self, parent, screen_manager,
                 title="Facility", func=None, func_args=(), func_kwargs=None,
                 on_close=None, **kwargs):
        self.facility_title = title
        self.facility_func = func
        self.facility_args = func_args
        self.facility_kwargs = func_kwargs or {}
        self.on_close = on_close

        self._input_queue = queue.Queue()
        self._pending_lines = []
        self._pending_lock = threading.Lock()
        self._input_mode = False
        self._input_prompt = ""
        self._stopped = False  # Set when user aborts early — thread should bail out
        self._finished = False  # Set when _finish() is called — prevents double-call
        self._confirm_dialog_open = False  # Guard against stacked dialogs

        super().__init__(parent, screen_manager, **kwargs)

    @property
    def tick_interval_ms(self):
        """Faster tick rate during travel journeys so time visibly counts up."""
        if self.facility_title.startswith("Journey"):
            return 400   # 1 game minute per 0.4 real seconds
        return 2000      # Default: 1 game minute per 2 real seconds

    # ── UI construction ───────────────────────────────────────────────────────

    def build_ui(self):
        self.sm.clear_log()
        # Don't overwrite the top bar — preserve the CityScreen format.
        # The game clock tick will refresh it via _update_top_bar().
        self._update_top_bar()

        # Main container
        container = self.styled_frame(self)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        container.grid_rowconfigure(0, weight=3)
        container.grid_rowconfigure(1, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # Output panel (scrollable text)
        output_frame = tk.LabelFrame(
            container,
            text=f" {self.facility_title} ",
            bg=Theme.BG_DARK,
            fg=Theme.TEXT,
            font=Theme.FONT_BOLD,
            highlightthickness=1,
            highlightbackground=Theme.BORDER,
        )
        output_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        output_frame.grid_rowconfigure(0, weight=1)
        output_frame.grid_columnconfigure(0, weight=1)

        self.output_text = tk.Text(
            output_frame,
            wrap=tk.WORD,
            state=tk.DISABLED,
            bg=Theme.BG_DARK,
            fg=Theme.TEXT,
            font=Theme.FONT,
            highlightthickness=0,
            borderwidth=0,
            padx=8,
            pady=8,
        )
        self.output_text.grid(row=0, column=0, sticky="nsew")

        scrollbar = tk.Scrollbar(
            output_frame,
            command=self.output_text.yview,
            bg=Theme.BG_MID,
            troughcolor=Theme.BG_DARK,
        )
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.output_text.config(yscrollcommand=scrollbar.set)

        # Input area
        input_frame = tk.Frame(container, bg=Theme.BG_DARK)
        input_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 5))
        input_frame.grid_columnconfigure(1, weight=1)

        self.prompt_label = tk.Label(
            input_frame,
            text="",
            bg=Theme.BG_DARK,
            fg=Theme.ACCENT,
            font=Theme.FONT_BOLD,
            width=12,
            anchor=tk.W,
        )
        self.prompt_label.grid(row=0, column=0, padx=(0, 5))

        self.input_entry = tk.Entry(
            input_frame,
            bg=Theme.BG_MID,
            fg=Theme.TEXT,
            font=Theme.FONT,
            insertbackground=Theme.TEXT,
            highlightthickness=1,
            highlightbackground=Theme.BORDER,
            highlightcolor=Theme.ACCENT,
            state=tk.DISABLED,
        )
        self.input_entry.grid(row=0, column=1, sticky="ew", padx=5)
        self.input_entry.bind("<Return>", self._on_input_submit)

        self.continue_btn = self.styled_button(
            input_frame,
            text="Continue",
            command=self._on_continue_click,
            width=10,
        )
        self.continue_btn.grid(row=0, column=2, padx=5)
        self.continue_btn.config(state=tk.DISABLED)

        # Button panel (for menu choices — replaces text input for simple choices)
        self._button_frame = tk.Frame(container, bg=Theme.BG_DARK)
        self._button_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0, 5))
        self._button_frame.grid_rowconfigure(1, weight=1)
        self._button_frame.grid_columnconfigure(0, weight=1)
        self._button_prompt = tk.Label(
            self._button_frame,
            text="",
            bg=Theme.BG_DARK,
            fg=Theme.ACCENT,
            font=Theme.FONT_BOLD,
            anchor=tk.W,
        )
        self._button_prompt.grid(row=0, column=0, sticky="ew", padx=5, pady=(2, 4))

        # Scrollable canvas for choice buttons
        self._button_canvas = tk.Canvas(
            self._button_frame,
            bg=Theme.BG_DARK,
            highlightthickness=0,
            borderwidth=0,
            height=180,  # Minimum height to show ~4 rows of buttons
        )
        self._button_scrollbar = tk.Scrollbar(
            self._button_frame,
            orient=tk.VERTICAL,
            command=self._button_canvas.yview,
            bg=Theme.BG_MID,
            troughcolor=Theme.BG_DARK,
        )
        self._button_canvas.configure(yscrollcommand=self._button_scrollbar.set)
        self._button_canvas.grid(row=1, column=0, sticky="nsew")
        self._button_scrollbar.grid(row=1, column=1, sticky="ns")

        # Inner container inside the canvas
        self._button_container = tk.Frame(self._button_canvas, bg=Theme.BG_DARK)
        self._button_canvas_window = self._button_canvas.create_window(
            (0, 0), window=self._button_container, anchor=tk.NW, tags="btn_container"
        )

        # Cancel button area (outside scroll, always visible)
        self._cancel_frame = tk.Frame(self._button_frame, bg=Theme.BG_DARK)
        self._cancel_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(4, 0))
        self._cancel_frame.grid_remove()

        # Bind canvas resize to update inner container width
        self._button_canvas.bind("<Configure>", self._on_button_canvas_configure)
        self._button_container.bind("<Configure>", self._on_button_container_configure)

        # Mouse wheel scrolling
        self._button_canvas.bind("<Enter>", lambda e: self._bind_mousewheel(e))
        self._button_canvas.bind("<Leave>", lambda e: self._unbind_mousewheel(e))

        self._button_frame.grid_remove()  # Hidden by default

        # Loading indicator (hidden when first output arrives)
        self.loading_label = tk.Label(
            output_frame,
            text="Loading...",
            bg=Theme.BG_DARK,
            fg=Theme.TEXT_DIM,
            font=Theme.FONT,
        )
        self.loading_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        # ── Permanent keyboard handler (same pattern as CityScreen / CombatScreen) ──
        self._setup_facility_keys()

        # ── Start the facility thread ───────────────────────────────────────
        self._start_facility()

    def _update_top_bar(self):
        """Refresh the top bar with the same format as CityScreen.

        Uses player.location as the primary city source so that facilities
        that change the player's location (e.g. Arcane Tower teleport)
        immediately reflect the new city in the header.
        """
        p = self.player
        if not p:
            self.sm.update_top_bar("Pandemonium")
            return
        # Use player's current location, falling back to facility_args city_id
        city_id = p.get("location") or (
            self.facility_args[1] if len(self.facility_args) > 1 else "solmere"
        )
        # Resolve dungeon-location to origin city
        if city_id == "dungeon":
            city_id = p.get("origin_city", "solmere")
        from resources.cities import CITIES
        city = CITIES.get(city_id, CITIES.get("solmere", {"name": city_id}))
        city_name = city.get("name", city_id) if isinstance(city, dict) else str(city)
        _cf = p.get("city_floors", {}).get(city_id, {})
        _cur = _cf.get("floor", 1)
        _max = _cf.get("max_floor", 1)
        from events import format_date
        from utils import format_time
        text = (
            f"{p['name']} | {city_name} | Floor {_cur}/{_max} | "
            f"{format_date(p)} | {format_time(p)}"
        )
        self.sm.update_top_bar(text)

    def _setup_facility_keys(self):
        """Bind a permanent <KeyPress> handler and claim keyboard focus.

        This follows the same proven pattern used by CityScreen and CombatScreen:
        the handler is ALWAYS active and dispatches based on the current UI mode
        (button panel, text input, or idle).  Dynamic bind/unbind is not needed.
        """
        self.bind("<KeyPress>", self._on_facility_key)
        self.focus_set()

    def _on_facility_key(self, event):
        """Permanent keyboard handler — delegates based on current mode."""
        # Button panel mode → delegate to the button-key dispatcher
        if self._input_mode and self._button_frame.winfo_ismapped():
            self._on_button_key(event)
            return "break"
        # Text input mode → let the Entry widget handle keys natively
        # (input_entry has its own <Return> binding; other keys type normally)
        # Idle state → consume all keys to prevent leakage to other screens
        return "break"

    # ── Facility thread ───────────────────────────────────────────────────────

    def _start_facility(self):
        """Launch the facility function in a daemon thread."""
        self._thread = threading.Thread(
            target=self._run_facility,
            daemon=True,
        )
        self._thread.start()

    def _run_facility(self):
        """Target for the daemon thread. Sets up Terminal, runs func, cleans up."""
        try:
            # Set up the GUI Terminal for this facility thread
            # IMPORTANT: Use the module-level 'term' singleton, NOT a new Terminal(),
            # because facility functions import 'term' directly from gui.terminal.
            from gui.terminal import term, _set_terminal, _clear_terminal
            term.set_screen(self)
            _set_terminal(term)

            # Also install legacy I/O redirects for backward compat
            _install_redirects(self)
            # Also patch clear_screen for this thread
            from utils import clear_screen
            import utils
            _orig_clear = clear_screen
            utils.clear_screen = _redirected_clear

            try:
                result = self.facility_func(
                    *self.facility_args, **self.facility_kwargs
                )
            except _FacilityStopped:
                # User aborted — clean exit, don't schedule _finish
                result = None
            finally:
                utils.clear_screen = _orig_clear
                _uninstall_redirects()
                _clear_terminal()
        except Exception as e:
            _uninstall_redirects()
            self._append_output(f"\n[ERROR: {e}]")
            result = None

        # Schedule close on main thread (unless already stopped — screen destroyed)
        if not self._stopped:
            try:
                self.after(100, lambda: self._finish(result))
            except (RuntimeError, tk.TclError):
                pass

    # ── Output management (thread-safe) ───────────────────────────────────────

    def _append_output(self, text):
        """Thread-safe append to output text. Called from facility thread."""
        if self._stopped:
            return
        with self._pending_lock:
            self._pending_lines.append(text)
        # Schedule UI update on main thread
        try:
            self.after(0, self._flush_output)
        except (RuntimeError, tk.TclError):
            pass  # widget destroyed

    def _flush_output(self):
        """Flush pending lines to the Text widget (main thread only)."""
        # Hide loading indicator on first output
        if hasattr(self, 'loading_label') and self.loading_label:
            try:
                self.loading_label.place_forget()
                self.loading_label = None
            except tk.TclError:
                pass

        with self._pending_lock:
            lines = self._pending_lines[:]
            self._pending_lines.clear()

        if not lines:
            return

        self.output_text.config(state=tk.NORMAL)
        for line in lines:
            self.output_text.insert(tk.END, strip_ansi(line) + "\n")
        self.output_text.see(tk.END)
        self.output_text.config(state=tk.DISABLED)

    def _clear_output(self):
        """Thread-safe clear. Called from facility thread."""
        try:
            self.after(0, self._do_clear)
        except (RuntimeError, tk.TclError):
            pass

    def _do_clear(self):
        """Clear output text (main thread only)."""
        try:
            self.output_text.config(state=tk.NORMAL)
            self.output_text.delete("1.0", tk.END)
            self.output_text.config(state=tk.DISABLED)
        except tk.TclError:
            pass  # Widget already destroyed — ignore

    # ── Input handling (thread-safe) ──────────────────────────────────────────

    def _wait_for_input(self, prompt=""):
        """Called from facility thread when input() is invoked."""
        if self._stopped:
            raise _FacilityStopped()
        # Schedule UI update on main thread
        try:
            self.after(0, lambda: self._show_input_prompt(prompt))
        except (RuntimeError, tk.TclError):
            raise _FacilityStopped()
        # Block until user submits
        return self._input_queue.get()

    def _show_input_prompt(self, prompt=""):
        """Enable input controls and show prompt (main thread only)."""
        self._input_mode = True
        self._input_prompt = prompt
        self.prompt_label.config(text=(prompt[:30] + "...") if len(prompt) > 30 else prompt)
        self.input_entry.config(state=tk.NORMAL)
        self.continue_btn.config(state=tk.NORMAL)
        self.input_entry.focus_set()

    def _hide_input_prompt(self):
        """Disable input controls (main thread only)."""
        self._input_mode = False
        self.prompt_label.config(text="")
        self.input_entry.delete(0, tk.END)
        self.input_entry.config(state=tk.DISABLED)
        self.continue_btn.config(state=tk.DISABLED)

    # ── Button canvas helpers ───────────────────────────────────────────────

    def _on_button_canvas_configure(self, event):
        """Keep the inner button container full-width when canvas resizes."""
        self._button_canvas.itemconfig(
            self._button_canvas_window, width=event.width
        )

    def _on_button_container_configure(self, event):
        """Update scrollregion when button container changes size."""
        self._button_canvas.configure(
            scrollregion=self._button_canvas.bbox("all")
        )

    def _bind_mousewheel(self, event):
        """Bind mousewheel scrolling when cursor enters the canvas."""
        self._button_canvas.bind("<MouseWheel>", self._on_mousewheel)

    def _unbind_mousewheel(self, event):
        """Unbind mousewheel when cursor leaves the canvas."""
        self._button_canvas.unbind("<MouseWheel>")

    def _on_mousewheel(self, event):
        """Handle mousewheel scroll over the button canvas."""
        self._button_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # ── Button-based choices (main thread) ────────────────────────────────────

    def _show_buttons(self, options, prompt="Choose an option:",
                      allow_cancel=True, cancel_label="Cancel",
                      styles=None):
        """Show a set of choice buttons. Called from facility thread via Terminal."""
        try:
            self.after(0, lambda: self._do_show_buttons(
                options, prompt, allow_cancel, cancel_label, styles
            ))
        except (RuntimeError, tk.TclError):
            pass

    def _do_show_buttons(self, options, prompt, allow_cancel, cancel_label, styles=None):
        """Create choice buttons on the main thread."""
        try:
            # Hide text input row
            self.prompt_label.grid_remove()
            self.input_entry.grid_remove()
            self.continue_btn.grid_remove()

            # Show button panel
            self._button_prompt.config(text=prompt)

            # Clear old buttons
            for w in self._button_container.winfo_children():
                w.destroy()

            # Reset canvas scroll to top
            self._button_canvas.yview_moveto(0)

            # Create option buttons — 3 columns, left-aligned, with scroll
            max_cols = 3
            for i, opt in enumerate(options):
                label = f"[{i + 1}] {opt}" if len(options) > 1 else opt

                # Per-button style overrides
                style = (styles or {}).__getitem__(i) if styles and i < len(styles) else None
                if style is None:
                    style = {}
                bg = style.get("bg", Theme.BUTTON_BG)
                fg = style.get("fg", Theme.BUTTON_FG)
                active_bg = style.get("active_bg", Theme.BUTTON_ACTIVE_BG)
                active_fg = style.get("active_fg", Theme.BUTTON_ACTIVE_FG)

                btn = tk.Button(
                    self._button_container,
                    text=label,
                    bg=bg,
                    fg=fg,
                    activebackground=active_bg,
                    activeforeground=active_fg,
                    font=Theme.FONT_BOLD,
                    relief=tk.RAISED,
                    borderwidth=2,
                    cursor="hand2",
                    anchor=tk.W,
                    justify=tk.LEFT,
                    padx=8,
                    command=lambda idx=i: self._on_button_choice(idx),
                )
                row = i // max_cols
                col = i % max_cols
                btn.grid(row=row, column=col, padx=3, pady=3, sticky="ew")

            # Make all columns equal weight
            for c in range(max_cols):
                self._button_container.grid_columnconfigure(c, weight=1, uniform="btn_col")

            # Cancel button — placed outside scroll area, always visible
            for w in self._cancel_frame.winfo_children():
                w.destroy()
            if allow_cancel:
                cancel_btn = tk.Button(
                    self._cancel_frame,
                    text=cancel_label,
                    bg="#5a3a5a",
                    fg=Theme.BUTTON_FG,
                    activebackground=Theme.BUTTON_ACTIVE_BG,
                    activeforeground=Theme.BUTTON_ACTIVE_FG,
                    font=Theme.FONT_BOLD,
                    relief=tk.RAISED,
                    borderwidth=2,
                    cursor="hand2",
                    command=lambda: self._on_button_choice(-1),
                )
                cancel_btn.pack(fill=tk.X, padx=4, pady=2)
                self._cancel_frame.grid()
            else:
                self._cancel_frame.grid_remove()

            self._button_frame.grid()
            self._input_mode = True

            # ── Keyboard support for button mode ──────────────────────────
            self._bind_button_keys(options, allow_cancel)
            # Keep focus on the FacilityScreen frame so its <KeyPress>
            # binding fires reliably for keyboard shortcuts.  The Enter
            # key already maps to the first option via _on_button_key.
            self.focus_set()

        except (tk.TclError, RuntimeError):
            # Widget destroyed mid-operation — unblock the waiting thread
            self._input_mode = False
            try:
                self._input_queue.put("-1")
            except Exception:
                pass

    def _bind_button_keys(self, options, allow_cancel):
        """Store button options so the permanent _on_facility_key handler
        can dispatch number keys / Escape correctly."""
        self._button_key_options = options
        self._button_key_allow_cancel = allow_cancel
        # The <KeyPress> binding is permanent — no dynamic bind/unbind needed.

    def _on_button_key(self, event):
        """Dispatch keyboard shortcuts for the currently-shown button panel."""
        if not self._input_mode:
            return

        key = event.keysym
        char = event.char

        # Enter / Return → first option
        if key in ("Return", "KP_Enter"):
            self._on_button_choice(0)
            return

        # Number keys 1-9 → corresponding option.
        # Use both event.char AND event.keysym for robustness across
        # platforms and keyboard layouts (e.g. char may be empty on
        # some systems, numpad keys report "KP_1" as keysym, etc.).
        digit = None
        if char and char in "123456789":
            digit = int(char)
        elif key in ("1", "2", "3", "4", "5", "6", "7", "8", "9"):
            digit = int(key)
        elif key.startswith("KP_") and len(key) == 4 and key[3] in "123456789":
            digit = int(key[3])
        # Also handle numpad with Num Lock off:
        elif key in ("KP_End", "KP_Down", "KP_Next", "KP_Left",
                     "KP_Begin", "KP_Right", "KP_Home", "KP_Up", "KP_Prior"):
            _numpad_map = {"KP_End": 1, "KP_Down": 2, "KP_Next": 3,
                          "KP_Left": 4, "KP_Begin": 5, "KP_Right": 6,
                          "KP_Home": 7, "KP_Up": 8, "KP_Prior": 9}
            digit = _numpad_map.get(key)

        if digit is not None:
            idx = digit - 1
            if idx < len(self._button_key_options):
                self._on_button_choice(idx)
            return

        # Escape → cancel (only if cancel button was shown)
        if key == "Escape" and self._button_key_allow_cancel:
            self._escape_just_handled = True
            self._on_button_choice(-1)
            return

    def _unbind_button_keys(self):
        """Clear stored button options (the <KeyPress> binding stays active)."""
        self._button_key_options = []
        self._button_key_allow_cancel = False

    def _on_button_choice(self, index):
        """Handle a button click — put the index into the input queue."""
        if not self._input_mode:
            return
        self._unbind_button_keys()
        self._button_frame.grid_remove()
        # Restore text input row (hidden)
        self.prompt_label.grid()
        self.input_entry.grid()
        self.continue_btn.grid()
        self._input_mode = False
        self._input_queue.put(str(index))

    def _hide_buttons(self):
        """Hide the button panel (main thread only)."""
        self._unbind_button_keys()
        self._button_frame.grid_remove()
        self.prompt_label.grid()
        self.input_entry.grid()
        self.continue_btn.grid()

    def _on_input_submit(self, event=None):
        """Handle Enter key in input entry."""
        if not self._input_mode:
            return
        text = self.input_entry.get().strip()
        self._hide_input_prompt()
        self._input_queue.put(text)

    def _on_continue_click(self):
        """Handle Continue button click."""
        if not self._input_mode:
            return
        text = self.input_entry.get().strip()
        self._hide_input_prompt()
        self._input_queue.put(text)

    # ── Navigation ─────────────────────────────────────────────────────────────

    def _on_back(self):
        """User clicked Back — confirm if facility is still running."""
        if self._confirm_dialog_open:
            return  # Prevent stacking multiple confirm dialogs
        if self._thread.is_alive():
            self._confirm_dialog_open = True
            confirm_dialog(
                parent=self,
                title="Leave Facility?",
                message="The facility is still running. Leave anyway?",
                on_yes=self._on_back_confirmed,
                on_no=self._on_back_cancelled,
            )
        else:
            self._finish()

    def _on_back_confirmed(self):
        """User confirmed leaving early."""
        self._confirm_dialog_open = False
        self._stop_facility()

    def _on_back_cancelled(self):
        """User cancelled leaving."""
        self._confirm_dialog_open = False

    def _stop_facility(self):
        """Stop the background facility thread and clean up."""
        self._stopped = True
        # Unblock any waiting input so the thread can exit
        self._input_queue.put("")
        # Trigger finish if not already finished
        if not self._finished:
            self._finish()

    def _finish(self, result=None):
        """Called when facility thread exits. Guards against double-invocation.

        Defers on_close / switch_to via after(0, …) so the FacilityScreen is
        not destroyed while we are still inside its own call stack.
        """
        if self._finished:
            return  # Already finished — prevent double-call
        self._finished = True
        # Capture the root window now (self may be destroyed before the after fires)
        _root = self.sm.root if self.sm else self.winfo_toplevel()

        def _do_finish():
            if self.on_close:
                self.on_close(result)
            else:
                from gui.screens.city_screen import CityScreen
                self.sm.switch_to(CityScreen)

        # Brief delay so the player can read any final dialogue
        # (e.g., leave messages) before the screen transitions away.
        _root.after(400, _do_finish)

    def destroy(self):
        """Clean up scheduled callbacks and queues.

        Does NOT uninstall I/O redirects here — the _run_facility finally
        block handles that when the facility thread exits. Uninstalling
        prematurely would cause orphaned facility threads to dump output
        to the terminal instead of the GUI.

        Sets _finished = True BEFORE calling _stop_facility so that any
        _finish() chain triggered by stopping does NOT navigate away —
        the ScreenManager is already handling the transition.

        Joins the background thread with a 2-second timeout to prevent
        zombie threads from holding queues / mutating player state after
        the screen is gone.
        """
        # Stop the facility thread if still running (e.g., user closed window)
        if not self._finished and self._thread is not None and self._thread.is_alive():
            self._finished = True  # Prevent _finish() from triggering navigation
            self._stop_facility()
            # Join with timeout — don't block the UI indefinitely
            self._thread.join(timeout=2.0)
        try:
            super().destroy()
        except (AttributeError, tk.TclError):
            pass  # Widget already torn down — suppress race condition

    def handle_escape(self):
        """Override: Esc behavior depends on current mode.

        - If a button panel is shown, _on_button_key already handled Escape
          (cancelled the choice).  A flag prevents double-processing.
        - If text input is active, Esc is blocked to prevent accidental exit.
        - Otherwise, Esc navigates back.
        """
        # If _on_button_key just handled Escape for a button panel,
        # don't also navigate back.  Also guard against stale flag by
        # verifying the button frame is actually mapped.
        if getattr(self, '_escape_just_handled', False):
            self._escape_just_handled = False
            if self._button_frame.winfo_ismapped():
                return
        if self._input_mode:
            return  # Don't exit while the player is being prompted (text input)
        self._on_back()
