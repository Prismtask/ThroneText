# combat/combat_io.py – I/O abstraction for combat module.
"""
Thread-safe I/O redirection for combat code.

Terminal mode (default):
    Uses standard print() and input().

GUI mode:
    The GUI sets a custom IO object via set_io() before starting combat.
    Combat functions call get_io().print() / get_io().input() instead of
    builtins, so output is captured and input is bridged to the GUI.
"""

import builtins
import threading


# ── Thread-local I/O storage ──────────────────────────────────────────────────
# Each thread gets its own IO object. This lets the GUI run combat in a
# background thread without affecting the main (tkinter) thread.
_thread_local = threading.local()


def get_io():
    """Return the I/O object for the current thread."""
    if not hasattr(_thread_local, "io"):
        _thread_local.io = TerminalIO()
    return _thread_local.io


def set_io(io):
    """Set the I/O object for the current thread."""
    _thread_local.io = io


def reset_io():
    """Reset to terminal I/O for the current thread."""
    _thread_local.io = TerminalIO()


# ── Base class ────────────────────────────────────────────────────────────────

class BaseCombatIO:
    """Abstract I/O interface for combat code."""

    def print(self, *args, **kwargs):
        raise NotImplementedError

    def input(self, prompt=""):
        raise NotImplementedError

    def clear(self):
        raise NotImplementedError

    def show_hud(self, data: dict):
        """Optional: called by the GUI renderer when HUD data is available."""
        pass


# ── Terminal implementation ───────────────────────────────────────────────────

class TerminalIO(BaseCombatIO):
    """Standard terminal I/O."""

    def print(self, *args, **kwargs):
        return builtins.print(*args, **kwargs)

    def input(self, prompt=""):
        return builtins.input(prompt)

    def clear(self):
        from utils import clear_screen
        clear_screen()


# ── Convenience aliases (used by refactored combat modules) ───────────────────

def c_print(*args, **kwargs):
    """Print via the current thread's I/O object."""
    return get_io().print(*args, **kwargs)


def c_input(prompt=""):
    """Input via the current thread's I/O object."""
    return get_io().input(prompt)


def c_clear():
    """Clear via the current thread's I/O object."""
    return get_io().clear()
