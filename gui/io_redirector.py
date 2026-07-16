"""
gui/io_redirector.py — Optional: captures stray print() calls for a debug window.

During migration, some files may still call print(). This redirector captures
those calls and forwards them to the GUI log panel instead of stdout.

Usage:
    from gui.io_redirector import GUIRedirector
    redirector = GUIRedirector(screen_manager)
    redirector.install()   # Replaces sys.stdout
    redirector.uninstall() # Restores original sys.stdout
"""

import sys
from typing import Optional

from gui.screen_manager import ScreenManager


class GUIRedirector:
    """
    Redirects stdout print() calls into the GUI log panel.
    Useful during gradual migration when not all prints have been refactored.
    """

    def __init__(self, screen_manager: Optional[ScreenManager] = None):
        self.sm = screen_manager
        self._original_stdout = sys.stdout
        self._buffer = ""
        self._installed = False

    def install(self):
        """Replace sys.stdout with this redirector."""
        if not self._installed:
            sys.stdout = self
            self._installed = True

    def uninstall(self):
        """Restore the original sys.stdout."""
        if self._installed:
            sys.stdout = self._original_stdout
            self._installed = False

    def write(self, text: str):
        """Called by print() statements. Buffers and forwards to GUI log."""
        self._original_stdout.write(text)  # Still echo to terminal for debugging
        self._buffer += text
        if "\n" in self._buffer:
            lines = self._buffer.split("\n")
            for line in lines[:-1]:
                line = line.rstrip("\r")
                if line.strip():
                    if self.sm:
                        self.sm.log(line)
            self._buffer = lines[-1]

    def flush(self):
        """Required for file-like interface."""
        self._original_stdout.flush()
        if self._buffer.strip() and self.sm:
            self.sm.log(self._buffer.strip())
            self._buffer = ""

    def isatty(self) -> bool:
        """Claim to be a TTY so color libraries don't complain."""
        return False
