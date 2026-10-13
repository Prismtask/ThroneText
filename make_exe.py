#!/usr/bin/env python3
"""
Build script for Pandemonium executable.

Usage:
    cd C:\\Code\\TerminalRPG
    .venv\\Scripts\\python.exe make_exe.py

This creates a clean distribution in dist/Pandemonium/ that you can zip
and share with your friend. Your friend just unzips and runs Pandemonium.exe.

The build also bundles the local web wiki (wiki/index.html) and writes an
"Open Wiki.bat" next to the exe — double-clicking it opens the wiki in a
web browser tab, fully offline.

No source files, no venv, no git repo — just the game and its data.
"""

import sys
import os
import shutil
import subprocess

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(PROJECT_ROOT, "dist")
BUILD_DIR = os.path.join(PROJECT_ROOT, "build")

APP_NAME = "Pandemonium"                       # exe / output folder name
WIKI_DIR = os.path.join(PROJECT_ROOT, "wiki")  # local web wiki source


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

    # GUI package data (JSON configs, assets, etc. if added later)
    gui_dir = os.path.join(PROJECT_ROOT, "gui")
    if os.path.exists(gui_dir):
        datas.append(f'--add-data={gui_dir};gui')

    return datas


def create_wiki_launcher():
    """
    Bundle the local web wiki into the distribution and write a double-click
    launcher ("Open Wiki.bat") that opens it in a browser tab.

    wiki/index.html is a single self-contained HTML file, so the browser can
    open it straight from disk (file://) — no web server or internet needed.
    """
    wiki_src = os.path.join(WIKI_DIR, "index.html")
    if not os.path.exists(wiki_src):
        print("  [skip] wiki/index.html not found - wiki will not be bundled.")
        return

    app_dir = os.path.join(DIST_DIR, APP_NAME)

    # 1) Copy the wiki next to the exe so the zipped folder is self-contained.
    wiki_dst_dir = os.path.join(app_dir, "wiki")
    os.makedirs(wiki_dst_dir, exist_ok=True)
    shutil.copy2(wiki_src, os.path.join(wiki_dst_dir, "index.html"))

    # 2) Write the double-click launcher. "%~dp0" is this .bat's own folder,
    #    so it keeps working no matter where the folder is unzipped.
    #    Uses CRLF line endings (Windows batch files).
    launcher_path = os.path.join(app_dir, "Open Wiki.bat")
    launcher_text = (
        "@echo off\r\n"
        "REM Pandemonium Wiki - opens the local game wiki in your default browser.\r\n"
        "REM Double-click this file to open wiki\\index.html in a new web tab.\r\n"
        'start "" "%~dp0wiki\\index.html"\r\n'
    )
    with open(launcher_path, "w", encoding="ascii", newline="") as f:
        f.write(launcher_text)

    print(f"  [OK] Wiki copied   -> {wiki_dst_dir}{os.sep}index.html")
    print(f"  [OK] Wiki launcher -> {launcher_path}")


def build():
    """Run PyInstaller with the correct settings for a terminal RPG."""
    print("=" * 60)
    print("  Pandemonium Executable Builder")
    print("=" * 60)

    clean_old_builds()
    datas = collect_data_files()

    # PyInstaller command (one-directory build recommended for speed & debugging)
    # Use --onefile instead if you want a single .exe (slower startup).
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "launcher.py",                      # Entry point (GUI)
        "--name", APP_NAME,                 # Output exe name
        "--distpath", DIST_DIR,             # Where the final folder goes
        "--workpath", BUILD_DIR,            # Where temp build files go
        "--clean",                          # Always clean
        "--noconfirm",                      # Overwrite without asking
        "--windowed",                        # windowed mode (no console) consider --console for debugging
        # "--onefile",                      # Uncomment for single .exe (slower startup)
        "--hidden-import", "tkinter",
        "--hidden-import", "tkinter.ttk",
        "--hidden-import", "tkinter.font",
        "--hidden-import", "tkinter.messagebox",
        "--hidden-import", "yaml",
    ] + datas

    print(f"\n  Building with: {sys.executable}")
    print(f"  Data files: {len(datas)} bundle(s) + wiki/")
    print(f"  Output: {DIST_DIR}/{APP_NAME}/{APP_NAME}.exe")
    print("  This may take 30-60 seconds ...\n")

    result = subprocess.run(cmd, cwd=PROJECT_ROOT)

    if result.returncode != 0:
        print("\n  [FAIL] Build failed. Check the output above for errors.")
        sys.exit(1)

    # Add the local web wiki + its double-click browser launcher to dist.
    create_wiki_launcher()

    print("\n" + "=" * 60)
    print("  [OK] Build successful!")
    print("=" * 60)
    print(f"""
  Output folder: {DIST_DIR}/{APP_NAME}/

  Files your friend needs:
    Pandemonium.exe          <- Double-click or run from terminal
    Open Wiki.bat            <- Double-click to open the game wiki in a browser tab
    wiki/                    <- Local web wiki (loaded by Open Wiki.bat)
    _internal/               <- Python runtime & libraries (don't touch)

  To share:
    1. Zip the entire folder: {DIST_DIR}/{APP_NAME}/
    2. Send the zip to your friend
    3. Friend unzips and runs Pandemonium.exe (game) or Open Wiki.bat (wiki)

  Note: Save files will be created in a "savefile/" folder
        next to Pandemonium.exe when the game runs.

  Launch modes:
    Pandemonium.exe           -> Launches the GUI
    Open Wiki.bat             -> Opens the local game wiki in your default browser

  If you want a SINGLE .exe file instead of a folder:
    Edit make_exe.py and uncomment the --onefile line.
    Trade-off: slower startup time (~2-5 sec extract on first run).
""")


if __name__ == "__main__":
    build()
