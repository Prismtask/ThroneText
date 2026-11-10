"""
tests/_tk_test_utils.py — Shared Tk root helper for GUI-dependent tests.

Not collected by pytest (underscore prefix).

Multiple Tk root creations in one process (create → destroy → create) are
flaky on some Windows Python builds — Tcl library files can fail to load on
re-initialization ("Can't find a usable init.tcl"). To avoid that, every
GUI-dependent test module shares ONE withdrawn root, created lazily on the
first request and torn down by the process exit.

When Tk cannot initialize at all (headless CI, broken Tcl install), callers
receive unittest.SkipTest so affected tests skip gracefully instead of
erroring.
"""

import tkinter as tk
import unittest

_root = None


def shared_tk_root():
    """Return the process-wide shared, withdrawn Tk root.

    Raises unittest.SkipTest when Tk cannot initialize in this environment.
    """
    global _root
    if _root is None:
        try:
            _root = tk.Tk()
            _root.withdraw()
        except tk.TclError as exc:
            raise unittest.SkipTest(f"Tk unavailable in this environment: {exc}")
    return _root
