# TerminalRPG — Phase 4 Polish Blueprint

> **Based on:** `GUI_MIGRATION_PLAN.md` (Week 7+ — Polish & Release)  
> **Current Status:** Phases 0–3 are functional. Phase 4 features are partially implemented or entirely missing.  
> **Goal:** A detailed, actionable roadmap to bring the GUI from "functional" to "polished and release-ready."

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Current State Audit](#2-current-state-audit)
3. [Gap Analysis](#3-gap-analysis)
4. [Implementation Roadmap](#4-implementation-roadmap)
5. [Detailed Feature Blueprints](#5-detailed-feature-blueprints)
6. [Testing & Release Checklist](#6-testing--release-checklist)
7. [Appendix: File Inventory](#appendix-file-inventory)

---

## 1. Executive Summary

The TerminalRPG GUI migration has successfully completed Phases 0–3:

| Phase | Status | Notes |
|-------|--------|-------|
| **Phase 0** (Architecture) | ✅ Complete | `gui/` package, `launcher.py`, `theme.py`, `screen_manager.py`, `base_screen.py` |
| **Phase 1** (Menu & City) | ✅ Complete | Main menu, char creation, city hub, load/delete dialogs |
| **Phase 2** (Combat) | ✅ Complete | Combat screen, renderer, action panel, thread-based I/O bridge, target selection |
| **Phase 3** (Inventory & Facilities) | ✅ Complete | Tabbed inventory, generic `FacilityScreen` wrapper, dungeon screen with ASCII map |
| **Phase 4** (Polish) | 🚧 Partial / Missing | Settings, keyboard shortcuts, animations, log window, splash screen, build polish |

Phase 4 is the final polish layer that transforms the game from a functional prototype into a professional, release-ready product. This blueprint breaks down every Phase 4 feature from the original plan, compares it against the current codebase, and provides exact implementation guidance.

---

## 2. Current State Audit

### 2.1 What EXISTS (Phase 4-adjacent)

| Feature | File(s) | Status | Notes |
|---------|---------|--------|-------|
| Dark theme | `gui/theme.py` | ✅ Complete | `#1a1a2e` bg, `#e94560` accent, rarity colors, monospace fonts |
| Top status bar | `gui/screen_manager.py` | ✅ Basic | Single `top_label` — no structured layout |
| Bottom log panel | `gui/screen_manager.py` | ✅ Basic | `log_text` Text widget, append-only, no scrollback history |
| Combat log | `gui/screens/combat_screen.py` | ✅ Basic | Dedicated `log_text` inside combat screen, 5 lines |
| Notification queue | `gui/notification_queue.py` | ✅ Data-only | Queue class exists, but **no visual toast UI** renders it |
| I/O redirector | `gui/io_redirector.py` | ✅ Complete | Captures stray `print()` → GUI log panel |
| `launcher.py` | root | ✅ Complete | `--terminal` / `--gui` dual entry |
| `make_exe.py` | root | ✅ Complete | PyInstaller, tkinter hidden imports, `--add-data` for `gui/` |
| Reusable widgets | `gui/widgets/` | ✅ Complete | `HPBar`, `confirm_dialog`, `item_card`, `stat_display` |
| Screen transitions | `gui/screen_manager.py` | ✅ Basic | Instant swap, no animation |
| Back-stack | `gui/screen_manager.py` | ✅ Complete | `_screen_history`, `go_back()` |
| IO bridge | `gui/screens/combat_screen.py` | ✅ Complete | `GUICombatIO` with queues for threaded combat |
| Facility wrapper | `gui/screens/facility_screen.py` | ✅ Complete | Generic `print()`/`input()` monkey-patch for all facilities |

### 2.2 What is MISSING or INCOMPLETE

| Feature | Original Plan | Current State | Impact |
|---------|-------------|---------------|--------|
| **Settings screen** | Sound, font size, theme | ❌ Not implemented | High — expected in any release app |
| **Keyboard shortcuts** | 1–9 skills, A/D/F/C/U, Esc, I | ❌ Not implemented | High — power users expect keyboard |
| **Splash screen** | Title art / logo on launch | ❌ Not implemented | Medium — first impression |
| **Log window** | Scrollable combat/dungeon history | ⚠️ Partial | Medium — bottom log is 4 lines, no history persistence |
| **Animations** | Fade/slide transitions, damage popups | ❌ Not implemented | Medium — visual feedback |
| **Sound toggle** | Enable/disable audio | ❌ Not implemented | Low — no audio system exists at all |
| **Color theme switch** | Dark / light / high-contrast | ❌ Not implemented | Low — dark theme is fine for release |
| **Font size adjustment** | Slider or preset sizes | ❌ Not implemented | Low — fixed 11pt is readable |
| **GUI settings persistence** | `gui_settings.json` | ❌ Not implemented | Medium — window size, theme prefs lost on restart |
| **Death screen** | Dedicated screen on player death | ❌ Not implemented | Medium — death handled via terminal prints inside facility wrapper |
| **Post-floor screen** | Dedicated screen after boss clear | ❌ Not implemented | Medium — terminal-based menu inside dungeon wrapper |
| **Phase label** | Update "Phase 1" → release | ❌ Still says Phase 1 | Trivial — cosmetic |
| **Top bar enrichment** | Structured status (HP, gold, day, time) | ⚠️ Basic string only | Medium — could be richer |
| **Notification toasts** | Visual popup for events | ❌ Queue exists, no UI | Medium — events are invisible in GUI |
| **Damage popups** | Floating numbers on hit | ❌ Not implemented | Low — nice-to-have |
| **Initiative bar** | Visual turn-order strip | ⚠️ Label only | Low — `turn_order_label` exists but is basic text |
| **Dedicated facility screens** | Per-facility GUI (not generic wrapper) | ❌ All generic | Medium — long-term wishlist; not required for Phase 4 |

---

## 3. Gap Analysis

### 3.1 Critical Path (Must-Have for Release)

These are the blockers that prevent calling Phase 4 "done":

1. **Keyboard Shortcuts** — The original plan explicitly mapped `1`–`9` for skills, `A`/`D`/`F`/`C`/`U` for combat actions, `I` for inventory, `Esc` for back. Without these, the GUI feels clunky to keyboard-oriented players (the original audience was terminal users).

2. **Settings Screen** — Even a minimal settings screen is table stakes for a desktop game. The original plan called for sound toggle, font size, and color theme. At minimum, we need **window size persistence**, **font size**, and **keyboard mode toggle**.

3. **GUI Settings Persistence** — Without `gui_settings.json`, every launch resets to 900×700 and default fonts. This is a poor user experience.

4. **Escape Key Handling** — Every screen should respond to `Esc` for "back / cancel". Currently there is no global key binding.

5. **Phase Label Cleanup** — `main_menu_screen.py` line 78 still reads `"GUI Mode (Phase 1)"`. This must be removed or updated before release.

### 3.2 High-Impact Polish (Should-Have)

6. **Combat Keyboard Navigation** — The `ActionPanel` renders buttons but only mouse-click works. Binding keys to the same actions is a medium effort, high payoff change.

7. **Inventory Keyboard Shortcut** — `I` key should open inventory from city and dungeon screens.

8. **Log Window Enhancement** — The bottom log is limited to 4 lines. A dedicated scrollable log window (popup or expandable panel) would let players review combat history, especially for long dungeon runs.

9. **Notification Toast UI** — `gui/notification_queue.py` has the data model but no visual rendering. Events (day-rollover, bounties, etc.) are silently swallowed in GUI mode.

10. **Top Bar Structured Layout** — The current `top_label` is a single string. Breaking it into structured widgets (name, HP bar, gold, day/time) would make status information glanceable.

### 3.3 Nice-to-Have (Can Defer Post-Release)

11. **Splash Screen** — Purely cosmetic. Can be added in a future update.

12. **Animations** — Fade/slide transitions and damage popups. tkinter is not well-suited for smooth animations; these are better deferred to a Pygame upgrade (Phase 3+ upgrade path).

13. **Sound System** — No audio exists in the game at all. Adding sound is a feature, not a polish task. Defer.

14. **Color Theme Switching** — Dark theme is cohesive and functional. Light theme is not required for release.

15. **Dedicated Per-Facility Screens** — The generic `FacilityScreen` wrapper is functional and preserves all facility logic. Custom screens for Shop, House, etc. are Phase 5+ scope.

---

## 4. Implementation Roadmap

### 4.1 Recommended Priority Order

| Priority | Task | Effort | Files to Create / Modify |
|----------|------|--------|--------------------------|
| P0 | **GUI Settings persistence** | Small | `gui/settings.py` (new), `gui/app.py` |
| P0 | **Settings screen** | Medium | `gui/screens/settings_screen.py` (new) |
| P0 | **Global keyboard shortcuts** | Medium | `gui/app.py`, `gui/screens/base_screen.py`, per-screen binds |
| P0 | **Combat keyboard bindings** | Medium | `gui/combat/action_panel.py`, `gui/screens/combat_screen.py` |
| P0 | **Remove "Phase 1" label** | Trivial | `gui/screens/main_menu_screen.py` |
| P1 | **Escape key = back / cancel** | Small | `gui/screens/base_screen.py`, `gui/screen_manager.py` |
| P1 | **Inventory hotkey (`I`)** | Small | `gui/screens/city_screen.py`, `gui/screens/dungeon_screen.py` |
| P1 | **Notification toast UI** | Medium | `gui/widgets/notification_toast.py` (new), `gui/screen_manager.py` |
| P1 | **Top bar structured layout** | Medium | `gui/screen_manager.py`, `gui/widgets/hp_bar.py` |
| P1 | **Log window (expandable / popup)** | Medium | `gui/widgets/log_window.py` (new), `gui/screen_manager.py` |
| P2 | **Death screen** | Medium | `gui/screens/death_screen.py` (new), `gui/screens/combat_screen.py` |
| P2 | **Post-floor screen** | Medium | `gui/screens/post_floor_screen.py` (new), `gui/screens/dungeon_screen.py` |
| P2 | **Splash screen** | Small | `gui/screens/splash_screen.py` (new), `gui/app.py` |
| P3 | **Animations** | Large | Defer to Pygame upgrade |
| P3 | **Sound system** | Large | Defer — requires audio assets + engine |
| P3 | **Color themes** | Medium | Defer — dark theme is sufficient |

### 4.2 Estimated Timeline

| Week | Focus | Deliverables |
|------|-------|--------------|
| **Week 1** | Settings + persistence + keyboard | `settings.py`, `settings_screen.py`, global key binds, combat keys |
| **Week 2** | UX polish | Escape handling, `I` hotkey, notification toasts, top bar rewrite, log window |
| **Week 3** | Missing screens + testing | Death screen, post-floor screen, splash screen, full playthrough testing |
| **Week 4** | Build & release | `make_exe.py` final verification, README update, release build |

---

## 5. Detailed Feature Blueprints

### 5.1 GUI Settings Persistence (`gui/settings.py`)

**New file:** `gui/settings.py`

**Purpose:** Load and save GUI preferences independently of the game save file. This keeps save compatibility at 100% while letting the GUI remember user preferences.

**Specification:**

```python
# gui/settings.py
import json
import os

SETTINGS_FILE = os.path.join("savefile", "gui_settings.json")

DEFAULT_SETTINGS = {
    "window_size": "900x700",
    "window_position": None,          # "+x+y" or None for center
    "font_size": 11,
    "theme": "dark",                   # "dark" | "light" | "high_contrast"
    "sound_enabled": False,            # Reserved for future sound system
    "keyboard_mode": True,            # Enable keyboard shortcuts globally
    "show_splash": True,
    "log_max_lines": 1000,             # Combat/dungeon log scrollback
}

def load_settings() -> dict:
    """Load GUI settings from disk, merging with defaults."""
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            # Merge with defaults so new fields are backward-compatible
            merged = DEFAULT_SETTINGS.copy()
            merged.update(loaded)
            return merged
        except (json.JSONDecodeError, OSError):
            pass
    return DEFAULT_SETTINGS.copy()

def save_settings(settings: dict):
    """Save GUI settings to disk."""
    os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)
```

**Integration points:**
- `gui/app.py`: Call `load_settings()` in `TerminalRPGApp.__init__()`. Apply `window_size` and `window_position` before `root.geometry()`. Apply `font_size` to `Theme` (see 5.1b below).
- `gui/screens/settings_screen.py`: Mutate the loaded settings dict and call `save_settings()` on apply.
- On window close: intercept `WM_DELETE_WINDOW` in `app.py` to capture current window size/position and save.

**5.1b Dynamic Font Size**

Modify `gui/theme.py` to accept a runtime font size:

```python
# gui/theme.py (modification)
class Theme:
    # ... existing constants ...
    
    @classmethod
    def set_font_size(cls, size: int):
        """Rebuild font tuples at runtime. Call once at app startup."""
        cls.FONT_SIZE = size
        cls.FONT_SIZE_LARGE = size + 3
        cls.FONT_SIZE_SMALL = max(8, size - 2)
        cls.FONT = (cls.FONT_FAMILY, cls.FONT_SIZE)
        cls.FONT_BOLD = (cls.FONT_FAMILY, cls.FONT_SIZE, "bold")
        cls.FONT_LARGE = (cls.FONT_FAMILY, cls.FONT_SIZE_LARGE, "bold")
        cls.FONT_SMALL = (cls.FONT_FAMILY, cls.FONT_SIZE_SMALL)
```

> **Note:** tkinter widgets created *before* `set_font_size()` will retain the old font. Best practice: call `Theme.set_font_size()` immediately after `root = tk.Tk()` but before any widget creation.

---

### 5.2 Settings Screen (`gui/screens/settings_screen.py`)

**New file:** `gui/screens/settings_screen.py`

**Layout:**

```
+--------------------------------------------------+
| Settings                              [Save] [X] |
+--------------------------------------------------+
|  Display                                         |
|  Font Size: [ 11 ▼ ]  (Small / Medium / Large)  |
|  Window Size: [900x700 ▼]                        |
|                                                  |
|  Gameplay                                        |
|  [✓] Enable keyboard shortcuts                   |
|  [  ] Show splash screen on launch                 |
|                                                  |
|  Audio (reserved)                                |
|  [  ] Enable sound effects                       |
|  Volume: [========●====]                         |
+--------------------------------------------------+
|  [Reset to Defaults]           [Apply & Close]    |
+--------------------------------------------------+
```

**Implementation notes:**
- Inherit from `BaseScreen`.
- Access settings via `gui.settings.load_settings()`.
- On "Apply & Close": mutate settings dict, call `gui.settings.save_settings()`, then `self.sm.go_back()`.
- The settings dict should be a **singleton** stored on `ScreenManager` so all screens can read it without re-loading from disk.

---

### 5.3 Global Keyboard Shortcuts

**Strategy:** Bind keys on the root window in `gui/app.py` so they are active across all screens. Screens can override or disable specific keys as needed.

**Implementation in `gui/app.py`:**

```python
def _setup_global_bindings(self):
    """Bind global keyboard shortcuts."""
    # Only if keyboard_mode is enabled in settings
    settings = self.screen_manager.settings
    if not settings.get("keyboard_mode", True):
        return
    
    self.root.bind("<Escape>", self._on_escape)
    self.root.bind("<KeyPress-i>", self._on_inventory_key)
    self.root.bind("<KeyPress-I>", self._on_inventory_key)

    # Ctrl+Q = quit
    self.root.bind("<Control-q>", lambda e: self.root.destroy())
    self.root.bind("<Control-Q>", lambda e: self.root.destroy())

def _on_escape(self, event):
    """Global escape handler."""
    # Delegate to current screen if it has a handle_escape method
    screen = self.screen_manager.current_screen
    if hasattr(screen, "handle_escape"):
        screen.handle_escape()
    else:
        self.screen_manager.go_back()

def _on_inventory_key(self, event):
    """Open inventory from city or dungeon screens."""
    from gui.screens.city_screen import CityScreen
    from gui.screens.dungeon_screen import DungeonScreen
    from gui.screens.inventory_screen import InventoryScreen
    
    screen = self.screen_manager.current_screen
    if isinstance(screen, (CityScreen, DungeonScreen)):
        # Pass a return callback so inventory "Back" returns to the right screen
        self.screen_manager.switch_to(InventoryScreen, push_history=True)
```

**Per-screen opt-in/opt-out:**

Screens that consume keys (e.g., `CharCreateScreen` with text entry, `FacilityScreen` with input box) should **not** propagate the key event. The input widget naturally consumes the key. But for screens that have their own key handlers (e.g., `CombatScreen` with action keys), bind on the screen's frame instead of the root, and use `event.widget == self` guards to avoid triggering from nested dialogs.

---

### 5.4 Combat Keyboard Bindings

**Strategy:** Bind action keys on the `CombatScreen` frame. When a key matches a valid action, simulate the same flow as a button click.

**Mapping (from original plan):**

| Key | Action |
|-----|--------|
| `A` | Attack |
| `D` | Defend |
| `F` | Flee |
| `C` | Capture |
| `U` | Use Item |
| `1`–`9` | Skill slot (if skill exists in that slot) |
| `0` | Cancel / Back |
| `Enter` | Confirm (Continue button) |
| `Esc` | Cancel target selection |

**Implementation in `gui/screens/combat_screen.py`:**

```python
def _setup_key_binds(self):
    """Bind combat action keys to this screen."""
    self.bind("<KeyPress>", self._on_key)
    self.focus_set()  # Ensure this widget receives key events

def _on_key(self, event):
    """Handle keyboard action shortcuts."""
    key = event.char.lower()
    
    # If action panel is disabled (enemy turn), ignore
    if not self.action_panel.winfo_exists():
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
    if key in "123456789":
        mapped = key
    elif key in key_map:
        mapped = key_map[key]
    else:
        return
    
    # Check if this action is currently available
    if mapped in self.action_panel._buttons:
        self._on_action_click(mapped)
```

> **Important:** The combat screen must call `self.focus_set()` after every screen transition into combat. Also, when the `Continue` button is visible, `Enter` should trigger it.

---

### 5.5 Escape Key = Back / Cancel

**Implementation:**

Add a `handle_escape()` method to `BaseScreen` with a default implementation:

```python
# gui/screens/base_screen.py (addition)
def handle_escape(self):
    """Default: navigate back. Subclasses may override."""
    if self.sm:
        self.sm.go_back()
```

Override in screens that need special behavior:
- `CombatScreen`: If in target-selection mode, cancel target selection. Otherwise, do nothing (Esc should not exit combat).
- `FacilityScreen`: If input box is active, do nothing (Esc should not close the facility mid-flow).
- `CharCreateScreen`: Go to previous step instead of going back entirely.

---

### 5.6 Notification Toast UI (`gui/widgets/notification_toast.py`)

**New file:** `gui/widgets/notification_toast.py`

**Purpose:** Render `NotificationQueue` entries as slide-in banners at the top-right of the window.

**Specification:**

```python
class NotificationToast(tk.Frame):
    """A sliding toast notification that auto-dismisses after duration_ms."""
    
    def __init__(self, parent, message, category="info", duration_ms=3000):
        super().__init__(parent, bg=...)
        # Draw a colored banner with text
        # After duration_ms, animate opacity down (or just destroy)
        # tkinter limitation: no opacity on Frames. Alternative: fade background color.
```

**Integration:**

In `gui/screen_manager.py`, add a `show_toast()` method:

```python
def show_toast(self, message: str, category: str = "info"):
    from gui.widgets.notification_toast import NotificationToast
    toast = NotificationToast(self.root, message, category)
    toast.place(relx=1.0, y=50, anchor=tk.NE, x=-10)
```

Hook into the city's event flush: after `flush_event_queue()` returns event strings, call `show_toast()` for each.

---

### 5.7 Top Bar Structured Layout

**Current:** Single `tk.Label` with plain text.

**Target:** Grid of structured widgets:

```
+--------------------------------------------------+
| Arin | Lv.12 | HP [███████░░░] 106/120 | 1,240g |
|      | Floor 7 | Day 14 | 14:30 | ⛰ Solmere     |
+--------------------------------------------------+
```

**Implementation:**

Replace `gui/screen_manager.py` `top_bar` construction:

```python
# Instead of a single top_label, create a grid of widgets:
self.top_name = tk.Label(self.top_bar, ...)
self.top_hp = HPBar(self.top_bar, width=120, height=14, show_text=True)
self.top_gold = tk.Label(self.top_bar, ...)
self.top_day = tk.Label(self.top_bar, ...)
self.top_time = tk.Label(self.top_bar, ...)
self.top_city = tk.Label(self.top_bar, ...)

# Pack or grid them horizontally
```

Add a `refresh_top_bar(player)` method to `ScreenManager` that updates all widgets from the player dict. Call it from `CityScreen.build_ui()` and after any action that changes HP, gold, or time.

---

### 5.8 Log Window (`gui/widgets/log_window.py`)

**New file:** `gui/widgets/log_window.py`

**Purpose:** A scrollable, filterable log history popup. The existing bottom bar log is only 4 lines and gets cleared on screen switches. The log window should persist history across the session.

**Specification:**

- Toplevel popup with a `ScrolledText` widget.
- Categories: `combat`, `dungeon`, `facility`, `event`, `system`.
- Filter buttons to show/hide categories.
- Search box to find text.
- "Clear" button.
- Opened via a button in the bottom bar or a hotkey (`Ctrl+L`).

**Integration:**

- `ScreenManager.log()` should append to both the bottom bar *and* a persistent in-memory list.
- The log window reads from this persistent list.

---

### 5.9 Death Screen (`gui/screens/death_screen.py`)

**New file:** `gui/screens/death_screen.py`

**Purpose:** Replace the terminal-based death message with a GUI screen that gives the player clear choices.

**Layout:**

```
+--------------------------------------------------+
|                                                  |
|              ☠ YOU DIED ☠                        |
|                                                  |
|    You were slain on Floor 7 of Solmere.        |
|    You lost 500 gold. Time has passed...          |
|                                                  |
|         [Continue]        [Quit to Menu]         |
|                                                  |
+--------------------------------------------------+
```

**Integration:**

- `CombatScreen` or `DungeonScreen` calls `self.sm.switch_to(DeathScreen, ...)` when the player dies.
- `DeathScreen` receives `player`, `floor`, `city_id`, and callbacks `on_continue` / `on_quit`.
- `on_continue` applies the death penalty (gold loss, time advance, HP → 1) and returns to `CityScreen`.
- `on_quit` returns to `MainMenuScreen`.

---

### 5.10 Post-Floor Screen (`gui/screens/post_floor_screen.py`)

**New file:** `gui/screens/post_floor_screen.py`

**Purpose:** After clearing a dungeon floor (especially boss floors), show a celebratory screen with choices instead of a terminal prompt.

**Layout:**

```
+--------------------------------------------------+
|         ✦ Floor 7 Cleared! ✦                     |
|                                                  |
|    Loot: Iron Sword, 340g, 1200 XP               |
|    Milestone: Superboss defeated!                |
|                                                  |
|    [Continue to Floor 8]                         |
|    [Return to City]                              |
|    [Save & Quit]                                 |
+--------------------------------------------------+
```

**Integration:**

- `DungeonScreen` or `CombatScreen` calls this when the floor boss dies.
- Requires loot data to be passed from the combat engine or dungeon loop.

---

### 5.11 Splash Screen (`gui/screens/splash_screen.py`)

**New file:** `gui/screens/splash_screen.py`

**Purpose:** A brief 2–3 second title card shown before the main menu.

**Implementation:**

```python
class SplashScreen(tk.Frame):
    def __init__(self, parent, on_complete):
        super().__init__(parent, bg=Theme.BG_DARK)
        tk.Label(self, text="THRONE OF PLAINTEXT", font=(Theme.FONT_FAMILY, 28, "bold"), fg=Theme.ACCENT).pack(expand=True)
        tk.Label(self, text="A TerminalRPG Adventure", font=Theme.FONT, fg=Theme.TEXT_DIM).pack()
        self.after(2500, on_complete)  # 2.5 second delay
```

**Integration:** In `app.py`, show `SplashScreen` first, then switch to `MainMenuScreen` after delay. If `settings["show_splash"]` is False, skip it.

---

### 5.12 Remove "Phase 1" Label

**File:** `gui/screens/main_menu_screen.py`

**Change:** Delete or replace lines 76–82:

```python
# REMOVE:
# tk.Label(
#     container,
#     text="GUI Mode (Phase 1)",
#     ...
# ).pack(pady=(20, 0))
```

**Replacement (optional):** Add a version number instead:

```python
tk.Label(
    container,
    text="v1.0.0",
    bg=Theme.BG_DARK,
    fg=Theme.TEXT_DIM,
    font=Theme.FONT_SMALL,
).pack(pady=(20, 0))
```

---

### 5.13 `make_exe.py` Final Verification

**Current state:** Already working. Items to verify before release:

1. **Entry point:** `launcher.py` is correct.
2. **Console flag:** `--console` is present (required for terminal mode).
3. **Hidden imports:** `tkinter`, `tkinter.ttk`, `tkinter.font`, `tkinter.messagebox` are present.
4. **Data bundles:** `gui/`, `resources/enemies/enemies_data/`, `resources/skill_book/` are bundled.
5. **Add `savefile/`:** Ensure the EXE can create `savefile/` and `savefile/gui_settings.json` at runtime.
6. **One-file option:** Document the `--onefile` trade-off in a README.

**No code changes needed** unless new directories are added during Phase 4 implementation.

---

## 6. Testing & Release Checklist

### 6.1 Integration Tests (Critical Paths)

| # | Test | Command / Steps | Expected |
|---|------|-----------------|----------|
| 1 | Launch GUI | `python launcher.py` | Main menu appears, splash screen (if enabled) |
| 2 | Create character → city → dungeon | Full flow | No crashes, HP/gold/time update correctly |
| 3 | Fight combat with keyboard | Press `A`, `1`, `D`, `F` | Actions fire correctly, no mouse needed |
| 4 | Open inventory with `I` | Press `I` in city | Inventory opens; `Esc` returns to city |
| 5 | Death → continue | Die in combat, click Continue | Gold penalty applied, return to city, HP = 1 |
| 6 | Death → quit | Die in combat, click Quit to Menu | Return to main menu |
| 7 | Settings → change font → restart | Set font 14, close, reopen | Font is 14pt on relaunch |
| 8 | Old save loads in GUI | Copy pre-GUI save, load | Character loads, `ensure_player_fields()` applies defaults |
| 9 | Terminal mode still works | `python launcher.py --terminal` | Full terminal game functional |
| 10 | EXE build | `.venv\Scripts\python.exe make_exe.py` | Clean build, launches without errors |

### 6.2 Regression Tests

After each Phase 4 change, verify:
- Save/load produces byte-identical files to pre-Phase 4.
- Terminal mode `main_menu()` is untouched.
- `combat_engine.py` logic is unchanged.
- `dungeon.py` floor generation is unchanged.
- Facility logic (all `facilities/*.py`) is unchanged.

### 6.3 Release Criteria

Phase 4 is "done" when:
- [ ] All P0 tasks are complete.
- [ ] All P1 tasks are complete or consciously deferred.
- [ ] The 10 integration tests pass.
- [ ] `make_exe.py` produces a working build.
- [ ] The game has been played from character creation through at least one dungeon boss floor without crashes.
- [ ] Terminal mode is verified functional.
- [ ] No file contains "Phase 1", "TODO", "FIXME", or "HACK".

---

## Appendix: File Inventory

### New Files to Create (Phase 4)

| File | Size | Purpose |
|------|------|---------|
| `gui/settings.py` | ~60 lines | Load/save `gui_settings.json` |
| `gui/screens/settings_screen.py` | ~200 lines | Settings UI |
| `gui/screens/death_screen.py` | ~120 lines | Player death GUI |
| `gui/screens/post_floor_screen.py` | ~150 lines | Floor clear rewards GUI |
| `gui/screens/splash_screen.py` | ~40 lines | Title splash on launch |
| `gui/widgets/notification_toast.py` | ~80 lines | Slide-in toast notifications |
| `gui/widgets/log_window.py` | ~150 lines | Scrollable persistent log history |

### Files to Modify (Phase 4)

| File | Lines to Change | Nature of Change |
|------|-----------------|------------------|
| `gui/app.py` | ~20 lines | Settings loading, global key binds, splash integration, window-close handler |
| `gui/theme.py` | ~15 lines | `set_font_size()` classmethod |
| `gui/screen_manager.py` | ~60 lines | Structured top bar, `refresh_top_bar()`, toast helper, persistent log list, settings reference |
| `gui/screens/base_screen.py` | ~10 lines | `handle_escape()` default method |
| `gui/screens/main_menu_screen.py` | ~5 lines | Remove "Phase 1" label |
| `gui/screens/combat_screen.py` | ~30 lines | Key binds, `focus_set()`, continue-on-Enter |
| `gui/screens/city_screen.py` | ~10 lines | `I` hotkey support, call `refresh_top_bar()` |
| `gui/screens/dungeon_screen.py` | ~10 lines | `I` hotkey support, death/post-floor routing |
| `gui/combat/action_panel.py` | ~5 lines | Ensure `_buttons` dict is accessible for keyboard lookup |
| `gui/screens/inventory_screen.py` | ~5 lines | `handle_escape()` override → return to previous screen |
| `gui/screens/facility_screen.py` | ~5 lines | Prevent `Esc` from closing while input is active |
| `gui/screens/char_create_screen.py` | ~10 lines | `Esc` → previous step; `Enter` → next step |
| `make_exe.py` | ~0 lines | Verify only — no changes expected unless new resource dirs added |

---

*End of Blueprint*
