"""
launcher.py — Entry point for Pandemonium (GUI only).

Launch:
    python launcher.py
    python launcher.py --gui

This file is the PyInstaller entry point.
"""

import sys
import threading
import traceback


def _setup_thread_excepthook():
    """Register a global handler for unhandled exceptions in background threads."""
    def _thread_excepthook(args):
        exc_type, exc_value, exc_tb = args.exc_type, args.exc_value, args.exc_traceback
        tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        try:
            import tkinter.messagebox as mb
            mb.showerror(
                "Background Thread Error",
                f"A background task crashed:\n\n{exc_value}\n\n"
                f"The application will continue, but some features may not work.\n"
                f"Details (last lines):\n{tb_str[-500:]}"
            )
        except Exception:
            # If tkinter isn't available, print to stderr
            print(f"[Thread Crash] {tb_str}", file=sys.stderr)

    threading.excepthook = _thread_excepthook


def main():
    _setup_thread_excepthook()
    from gui.app import run_gui
    run_gui()


if __name__ == "__main__":
    main()
