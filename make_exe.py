#!/usr/bin/env python3
"""
Build script for TerminalRPG executable.

Usage:
    cd C:\\Code\\TerminalRPG
    .venv\Scripts\python.exe make_exe.py

This creates a clean distribution in dist/TerminalRPG/ that you can zip
and share with your friend. Your friend just unzips and runs TerminalRPG.exe.

No source files, no venv, no git repo — just the game and its data.
"""

import sys
import os
import shutil
import subprocess

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(PROJECT_ROOT, "dist")
BUILD_DIR = os.path.join(PROJECT_ROOT, "build")


def clean_old_builds():
    """Remove old PyInstaller artifacts so we start fresh."""
    for folder in (BUILD_DIR, DIST_DIR):
        if os.path.exists(folder):
            print(f"  Removing old {folder} ...")
            shutil.rmtree(folder)


def collect_data_files():
    """
    Build --add-data entries for non-Python files that the game loads at runtime.
    PyInstaller auto-bundles .py files, but YAML data files must be declared explicitly.

    Windows syntax: --add-data "src;dest"
    """
    datas = []

    # Enemy YAML data (loaded via os.listdir() in enemy_loader.py)
    enemy_data_dir = os.path.join(PROJECT_ROOT, "resources", "enemies", "enemies_data")
    if os.path.exists(enemy_data_dir):
        datas.append(f'--add-data={enemy_data_dir};resources/enemies/enemies_data')

    # Skill book YAMLs (loaded via os.path.join(__file__, ...) in skill_loader.py / ally_skills.py)
    skill_book_dir = os.path.join(PROJECT_ROOT, "resources", "skill_book")
    if os.path.exists(skill_book_dir):
        datas.append(f'--add-data={skill_book_dir};resources/skill_book')

    return datas


def build():
    """Run PyInstaller with the correct settings for a terminal RPG."""
    print("=" * 60)
    print("  TerminalRPG Executable Builder")
    print("=" * 60)

    clean_old_builds()
    datas = collect_data_files()

    # PyInstaller command (one-directory build recommended for speed & debugging)
    # Use --onefile instead if you want a single .exe (slower startup).
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "main.py",                          # Entry point
        "--name", "TerminalRPG",            # Output exe name
        "--distpath", DIST_DIR,             # Where the final folder goes
        "--workpath", BUILD_DIR,            # Where temp build files go
        "--clean",                          # Always clean
        "--noconfirm",                      # Overwrite without asking
        "--console",                        # IMPORTANT: terminal game needs a console
        # "--onefile",                      # Uncomment for single .exe (slower startup)
    ] + datas

    print(f"\n  Building with: {sys.executable}")
    print(f"  Data files: {len(datas)} bundle(s)")
    print(f"  Output: {DIST_DIR}/TerminalRPG/TerminalRPG.exe")
    print("  This may take 30-60 seconds ...\n")

    result = subprocess.run(cmd, cwd=PROJECT_ROOT)

    if result.returncode != 0:
        print("\n  [FAIL] Build failed. Check the output above for errors.")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("  [OK] Build successful!")
    print("=" * 60)
    print(f"""
  Output folder: {DIST_DIR}/TerminalRPG/

  Files your friend needs:
    TerminalRPG.exe          <- Double-click or run from terminal
    _internal/               <- Python runtime & libraries (don't touch)

  To share:
    1. Zip the entire folder: {DIST_DIR}/TerminalRPG/
    2. Send the zip to your friend
    3. Friend unzips and runs TerminalRPG.exe

  Note: Save files will be created in a "savefile/" folder
        next to TerminalRPG.exe when the game runs.

  If you want a SINGLE .exe file instead of a folder:
    Edit make_exe.py and uncomment the --onefile line.
    Trade-off: slower startup time (~2-5 sec extract on first run).
""")


if __name__ == "__main__":
    build()
