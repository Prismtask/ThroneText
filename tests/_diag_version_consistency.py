"""Diagnostic: version consistency between version.py and the changelog.

version.py is the single source of truth for the current version; the
changelog (gui/screens/changelog_screen.py) keeps frozen per-release headers,
newest first. When a version is bumped, both must change together — this
script catches drift.

Usage:
    .venv/Scripts/python.exe tests/_diag_version_consistency.py

Checks:
  * version.py defines GAME_VERSION / VERSION_NAME / IS_BETA / VERSION_DISPLAY / VERSION_LABEL.
  * IS_BETA stays True while the version is still 0.x (pre-1.0).
  * The newest _add_version() literal in changelog_screen.py == VERSION_DISPLAY.
Exit 0 = OK; 1 = problem.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_version_namespace():
    ns = {}
    path = ROOT / "version.py"
    exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), ns)
    return ns


def main():
    problems = []

    ns = load_version_namespace()
    game_version = ns.get("GAME_VERSION")
    version_name = ns.get("VERSION_NAME")
    display = ns.get("VERSION_DISPLAY")

    if not (game_version and version_name and display):
        problems.append("version.py must define GAME_VERSION, VERSION_NAME and VERSION_DISPLAY.")
    elif display != f"v{game_version} — {version_name}":
        problems.append(f"VERSION_DISPLAY drifted from its formula: {display!r}")

    is_beta = ns.get("IS_BETA")
    if is_beta is None:
        problems.append("version.py must define IS_BETA (pre-1.0 beta flag).")
    elif str(game_version).startswith("0.") and not is_beta:
        problems.append("GAME_VERSION is still 0.x but IS_BETA is False — pre-1.0 builds must stay beta.")

    label = ns.get("VERSION_LABEL")
    if not label:
        problems.append("version.py must define VERSION_LABEL (player-facing label).")
    elif display and not label.startswith(display):
        problems.append(f"VERSION_LABEL {label!r} should start with VERSION_DISPLAY {display!r}.")

    changelog = (ROOT / "gui" / "screens" / "changelog_screen.py").read_text(encoding="utf-8")
    match = re.search(r'self\._add_version\(\s*"([^"]+)"', changelog)
    if match is None:
        problems.append('No self._add_version("...") literal found in changelog_screen.py.')
    elif display and match.group(1) != display:
        problems.append(
            f"Changelog newest header {match.group(1)!r} != version.py VERSION_DISPLAY {display!r}.\n"
            "     If you bumped: prepend the new changelog block and keep older headers frozen.\n"
            "     If you rolled back: fix the header in changelog_screen.py."
        )

    if problems:
        print(f"version consistency: {len(problems)} problem(s)")
        for p in problems:
            print(f"  - {p}")
        return 1

    print(f"version consistency OK: {display}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
