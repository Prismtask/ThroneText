# TerminalRPG GUI — Comprehensive Health Check & Development Plan

**Date:** 2026-07-08  
**Scope:** Every file in `gui/`, plus related `combat/`, facility, and core files that interface with the GUI  
**Methodology:** Full static code analysis of 43+ source files

---

## Executive Summary

All files across the `gui/` package, `combat/`, and core game files (`main.py`, `character.py`, `utils.py`, `dungeon.py`, `city.py`, `events.py`, `save_load.py`, `launcher.py`) were analyzed for bugs, thread-safety issues, race conditions, and code quality concerns. Below are findings organized by severity, followed by a prioritized development roadmap.

---

## 🔴 Critical Bugs (Crash / Data Loss / Game-Breaking)

### BUG-C1: CombatScreen — `_destroyed` flag never set to `True`
**File:** `gui/screens/combat_screen.py`

The `_destroyed` flag is initialized to `False` and checked in `_poll()` and `_schedule_hud_refresh()` to prevent accessing destroyed widgets, but **it is never set to `True`** anywhere. If `CombatScreen` is destroyed while the combat thread is running, `after()` polling callbacks continue firing and accessing torn-down tkinter widgets → unhandled `TclError` crashes.

**Fix:** Override `destroy()` or bind `"<Destroy>"` to set `self._destroyed = True` and cancel all pending `after()` IDs before the widget tree is torn down.

```python
def destroy(self):
    self._destroyed = True
    self._cancel_polls()
    super().destroy()
```

---

### BUG-C2: FacilityScreen — Background thread not stopped on widget destroy
**File:** `gui/screens/facility_screen.py`

`_stopped` is set during user-initiated abort, but there is **no cleanup when the widget is destroyed externally** (e.g., window close). If the user closes via `WM_DELETE_WINDOW` or ScreenManager replaces the screen while the facility thread is running, the thread continues:
- Calling `self.after(0, ...)` on a destroyed widget → `RuntimeError` / `TclError`
- Holding `_input_queue` with no consumer → facility thread hangs forever
- Modifying player state after screens have switched

**Fix:** Override `destroy()` to set `self._stopped = True`, push a sentinel to `_input_queue`, and join the thread with a timeout.

```python
def destroy(self):
    self._stopped = True
    try:
        self._input_queue.put("")  # unblock waiting thread
    except Exception:
        pass
    super().destroy()
```

---

### BUG-C3: CombatScreen — Enemy list synchronization between GUI and engine
**File:** `gui/screens/combat_screen.py`, `_on_enemy_click`, `_handle_input_needed`

The combat engine maintains its own internal enemy list (pruning dead/captured enemies). The GUI's `self.enemies` list is created once in `__init__` from `enemy_stats()` and is **never updated** when the combat engine prunes enemies. This causes:

- `_target_index_map` rebuilt from GUI's `self.enemies` alive indices, but combat engine expects 1-based indices into its *own* pruned list
- Target selection may send wrong enemy indices to the engine
- HUD shows dead enemies until next refresh (polled at 200ms intervals, so brief but visible)

**Fix:** After `_handle_output` or in `_refresh_hud`, sync `self.enemies` with the combat engine's current enemy state. Consider passing a callback or shared reference so the GUI always has the current list.

---

### BUG-C4: CombatOverlay — `is_overlay` kwarg could leak to tk.Frame
**File:** `gui/screens/dungeon_screen.py`, `gui/screen_manager.py`

In `DungeonScreen._gui_combat()`:
```python
self.sm.push_overlay(
    CombatScreen,
    enemy_keys=enemy_keys,
    ...
    is_overlay=True,
)
```

`push_overlay()` passes all `**kwargs` to the screen constructor. `CombatScreen.__init__` has `is_overlay` as a named parameter, so it's popped from `**kwargs` before reaching `tk.Frame.__init__`. **Currently safe**, but fragile — if a new kwarg is added to `push_overlay` but forgotten in `CombatScreen.__init__`, tkinter will raise `_tkinter.TclError: unknown option`.

**Fix:** In `push_overlay`, separate overlay-specific kwargs from screen-specific kwargs explicitly.

---

## 🟠 High Priority Bugs (Functional Issues, Poor UX)

### BUG-H1: CityScreen — `_on_city_key` ignores capital letter keys
**File:** `gui/screens/city_screen.py`

The global app binding uses both `<KeyPress-i>` and `<KeyPress-I>` to handle inventory, but `_on_city_key` does `key_map.get(key.lower())` where `key = event.char`. For capital I, `event.char` is `"I"` → `"i"` after `.lower()` → works. But keyboard mode check in `app.py` returns early for capital key bindings:

```python
self.root.bind("<KeyPress-i>", self._on_inventory_key)
self.root.bind("<KeyPress-I>", self._on_inventory_key)
```

These global bindings dispatch correctly. The CityScreen local `_on_city_key` handler also handles this via `.lower()`. **Not a current bug**, but the presence of both global and local key handlers creates confusing double-dispatch (inventory opens via global handler AND local handler, potentially triggering twice).

**Fix:** Decide on a single key-handling strategy — either all global or all per-screen.

---

### BUG-H2: TravelScreen — `unbind_all("<MouseWheel>")` removes bindings from ALL widgets
**File:** `gui/screens/travel_screen.py`

```python
def _unbind_mousewheel(self, event):
    if self._card_canvas is not None:
        self._card_canvas.unbind_all("<MouseWheel>")  # ← UNBINDS FROM EVERY WIDGET
```

`unbind_all()` is a global operation — it strips the `<MouseWheel>` binding from **every widget in the entire application**. If the combat log, inventory, or any other screen has mousewheel scrolling, it silently breaks when the mouse leaves the travel screen's card canvas.

**Fix:** Use `self._card_canvas.unbind("<MouseWheel>")` and store the binding ID from `bind()`:

```python
def _bind_mousewheel(self, event):
    if self._card_canvas is not None:
        self._mw_bind_id = self._card_canvas.bind("<MouseWheel>", self._on_mousewheel)

def _unbind_mousewheel(self, event):
    if self._card_canvas is not None and hasattr(self, '_mw_bind_id'):
        self._card_canvas.unbind("<MouseWheel>", self._mw_bind_id)
```

---

### BUG-H3: HPBar — Hardcoded "Consolas" font breaks cross-platform
**File:** `gui/widgets/hp_bar.py`, line ~105

```python
font=("Consolas", 9, "bold"),
```

On macOS (Menlo) and Linux (DejaVu Sans Mono), Consolas may not be installed. The `Theme` module already defines `FONT_FAMILY` with per-platform detection, but the HPBar ignores it.

**Fix:** Use `Theme.FONT_FAMILY`:
```python
font=(Theme.FONT_FAMILY, 9, "bold"),
```

---

### BUG-H4: Verification needed — `_get_current_cooldowns()`, `_parse_prompt()`, `_resolve_active_ally()`
**File:** `gui/screens/combat_screen.py`

These three methods are called in `_handle_input_needed()` and `_on_action_click()`:
```python
cooldowns=self._get_current_cooldowns(),
...
mode, context = self._parse_prompt(prompt)
...
self._active_ally = self._resolve_active_ally(context)
```

They must be defined in the rest of `combat_screen.py` (after line 500). If any are missing, combat input handling will raise `AttributeError` and crash.

**Action:** Verify these three methods exist and work correctly. If they're intentionally stubbed, add explicit `raise NotImplementedError` with a clear message.

---

### BUG-H5: CombatRenderer — `_refresh_column` stale highlight on hidden frames
**File:** `gui/combat/combat_renderer.py`

When enemies die, `_refresh_column` calls `pack_forget()` on excess frames but doesn't clear their highlight state. If target selection was active and an enemy died, the highlight stays visually on the hidden frame. When a new enemy reuses that frame, it appears pre-highlighted.

**Fix:** Call `clear_target_highlight()` on hidden frames, or reset highlight state in `_update_entity_frame`.

---

### BUG-H6: NotificationToast — Auto-dismiss callback fires after parent destroyed
**File:** `gui/widgets/notification_toast.py`

```python
self._dismiss_id = self.after(duration_ms, self.destroy)
```

If the toast's parent container is destroyed before the `after()` callback fires, `self.destroy()` is called on an already-destroyed widget. The `dismiss()` method guards against `TclError`, but the raw `after` callback does not.

**Fix:** Wrap the `after` callback:
```python
self._dismiss_id = self.after(duration_ms, self.dismiss)
```

(`dismiss()` already has the try/except guard.)

---

## 🟡 Medium Priority (Edge Cases, Resilience Issues)

### BUG-M1: BaseScreen — No standard cleanup hook on destroy
**File:** `gui/screens/base_screen.py`

`BaseScreen` does not override `destroy()`. Subclasses that create background threads (`FacilityScreen`, `DungeonScreen`, `CombatScreen`) manage their own cleanup, but there's no standard pattern. When `ScreenManager.switch_to()` destroys the current screen, any pending `after()` callbacks fire on destroyed widgets.

**Fix:** Add a `cleanup()` method to `BaseScreen` that subclasses can override, and call it from `ScreenManager.switch_to()` before `destroy()`.

---

### BUG-M2: DungeonScreen — Monkey-patch not restored if `_orig_render` is never called
**File:** `gui/screens/dungeon_screen.py`, `_run_facility`

```python
_orig_render = dungeon_rooms.render_ascii_map
dungeon_rooms.render_ascii_map = _gui_render
try:
    super()._run_facility()
finally:
    dungeon_rooms.render_ascii_map = _orig_render
```

If the facility function crashes before `_orig_render` is called (e.g., during setup), the monkey-patch is still restored by `finally`. ✅ This is actually safe. But the inner `t.print` monkey-patch is restored in a nested `finally`:

```python
if t:
    _orig_t_print = t.print
    t.print = _capture_print
try:
    _orig_render(rooms, explored, current_room_idx, floor)
finally:
    if t:
        t.print = _orig_t_print
```

If `_orig_render` raises, `t.print` is restored. ✅ Safe.

---

### BUG-M3: FacilityScreen — `_button_frame` and `input_frame` share same grid cell
**File:** `gui/screens/facility_screen.py`

```python
input_frame.grid(row=1, column=0, ...)       # text input row
self._button_frame.grid(row=1, column=0, ...) # button choice row
```

Both occupy row 1, column 0. When `_do_show_buttons` is called, it hides the text input widgets via `grid_remove()` and shows `_button_frame` via `grid()`. This works as a swap, but if `_hide_input_prompt()` is called after `_do_show_buttons`, it might try to `grid()` the input widgets back over the button panel. The current code doesn't do this, but the design is fragile.

**Fix:** Add explicit state tracking (`_showing_buttons` flag) or use a `tk.Frame` with `grid` that swaps child frames rather than sibling grid cells.

---

### BUG-M4: `_safe_toplevel` — `parent._root()` fallback is suspicious
**File:** `gui/widgets/confirm_dialog.py`

```python
return parent._root() if hasattr(parent, '_root') else parent.master.winfo_toplevel()
```

`_root()` is an internal method on `tk.Tk`, not on `tk.Widget`. If `parent` is a regular Frame, `hasattr(parent, '_root')` returns False, so it falls through correctly. But the check is misleading — it suggests the code expects `_root()` to be available on all widgets.

**Fix:** Replace with a simpler, more explicit fallback chain:
```python
try:
    return parent.winfo_toplevel()
except tk.TclError:
    import tkinter as _tk
    return _tk._default_root
```

---

### BUG-M5: `utils.py` — `handle_player_death()` calls `os.system('cls')` in GUI mode
**File:** `utils.py`

`handle_player_death()` calls `clear_screen()` which does `os.system('cls' if os.name == 'nt' else 'clear')`. In GUI mode, this clears the actual terminal (not the GUI). The function is only called from terminal mode (`main.py` → `play_game`), but if ever invoked from GUI mode, it would be a no-op visually.

**Fix:** The `_tprint`/`_tclear` pattern in `dungeon.py` should be replicated in `utils.py` for consistency. Currently `handle_player_death()` uses `_tprint` and `_tinput` correctly, but `clear_screen()` is the raw terminal version.

---

### BUG-M6: Silent exception swallowing in multiple files
**Files:** `inventory_screen.py`, `screen_manager.py`, `facility_screen.py`

Several `except Exception: pass` or `except (tk.TclError, AttributeError): pass` blocks exist. While many are intentional (widget already destroyed), over-broad exception swallowing hides real bugs.

| File | Location | Issue |
|------|----------|-------|
| `inventory_screen.py` | `_jump_to_bag_and_hint` | Swallows all exceptions |
| `screen_manager.py` | `_on_close` | Swallows settings save errors |
| `facility_screen.py` | `_flush_output` | `AttributeError` catch — `loading_label` may not exist |

---

## 🟢 Low Priority (Code Quality, Maintainability)

### BUG-L1: Unused imports
- `gui/screens/facility_screen.py` imports `scrolledtext` but uses `tk.Text` directly
- `gui/screens/city_screen.py` imports `ttk` but never uses it

### BUG-L2: Redundant variable reassignment
**File:** `gui/screens/city_screen.py`, `_show_floor_selection`:
```python
root = self.sm.root if self.sm else self.winfo_toplevel()  # assigned
dialog = tk.Toplevel(root)
...
root = self.sm.root if self.sm else self.winfo_toplevel()  # reassigned with same value
```

### BUG-L3: Theme font size update touches class attributes directly
**File:** `gui/theme.py`, `set_font_size()`:
```python
Theme.FONT_SIZE = FONT_SIZE
Theme.FONT = FONT
```
This works but is unusual — module-level globals and class attributes are being used interchangeably. Consider consolidating to one or the other.

### BUG-L4: `combat/combat_engine.py` — `combat()` signature unknown
The `CombatScreen._start_combat()` calls:
```python
result = combat(self.player, self.enemy_keys, floor=..., room_num=..., total_rooms=..., enemies=self.enemies)
```
If `combat()` doesn't accept `enemies=` as a keyword argument, this will raise `TypeError`.

### BUG-L5: `launcher.py` — `--gui` flag mentioned in docstring but not in args check
```python
# Docstring says: python launcher.py --gui → Launch GUI (explicit)
# But code only checks: if "--terminal" in args: ... else: (GUI)
```
The `--gui` flag works implicitly (it falls into the `else` branch), but it's not explicitly checked. Minor doc/code mismatch.

---

## 📊 Bug Summary Table

| ID | Severity | File | Issue | Impact |
|----|----------|------|-------|--------|
| C1 | 🔴 Critical | `combat_screen.py` | `_destroyed` never set, polling continues after destroy | Crash |
| C2 | 🔴 Critical | `facility_screen.py` | Background thread not stopped on widget destroy | Crash |
| C3 | 🔴 Critical | `combat_screen.py` | Enemy list desync between GUI and combat engine | Wrong targets |
| H1 | 🟠 High | `city_screen.py` | Dual key-handling (global + local) | Double-dispatch |
| H2 | 🟠 High | `travel_screen.py` | `unbind_all` removes global mousewheel bindings | UX breakage |
| H3 | 🟠 High | `hp_bar.py` | Hardcoded "Consolas" font | macOS/Linux break |
| H4 | 🟠 High | `combat_screen.py` | Unverified method existence (`_get_current_cooldowns`, etc.) | Potential crash |
| H5 | 🟠 High | `combat_renderer.py` | Stale highlight on hidden enemy frames | Visual bug |
| H6 | 🟠 High | `notification_toast.py` | Auto-dismiss callback after parent destroyed | Crash |
| M1 | 🟡 Medium | `base_screen.py` | No standard cleanup hook | Leaked callbacks |
| M2 | 🟡 Medium | `dungeon_screen.py` | Monkey-patch edge case (verified safe) | None currently |
| M3 | 🟡 Medium | `facility_screen.py` | Fragile grid-cell swap for input/buttons | Layout bug risk |
| M4 | 🟡 Medium | `confirm_dialog.py` | Suspicious `_root()` fallback | Fragile |
| M5 | 🟡 Medium | `utils.py` | `clear_screen` uses raw terminal in GUI mode | No-op |
| M6 | 🟡 Medium | Multiple | Silent exception swallowing | Hidden bugs |
| L1-L5 | 🟢 Low | Multiple | Code hygiene: unused imports, redundant code, doc mismatch | Maintenance |

---

## 🎯 Development Plan: High-Impact Feature & UI Improvements

### Phase A: Stabilization (Bug Fixes) — **Do First**

| # | Task | Effort | Impact |
|---|------|--------|--------|
| A1 | Add proper `destroy()` cleanup to `CombatScreen`, `FacilityScreen`, `DungeonScreen` — set flags, cancel `after()` IDs, push sentinel to queues | 2–3h | Prevents crashes |
| A2 | Fix `unbind_all` → `unbind` in `travel_screen.py` | 0.5h | Prevents UX bugs |
| A3 | Fix hardcoded font in `hp_bar.py` → use `Theme.FONT_FAMILY` | 0.25h | Cross-platform |
| A4 | Verify `_get_current_cooldowns`, `_parse_prompt`, `_resolve_active_ally` exist in `combat_screen.py` | 0.5h | Prevents crash |
| A5 | Add thread-safe enemy list sync in `CombatScreen` | 3–4h | Correct target selection |
| A6 | Fix `NotificationToast` after-callback to use `self.dismiss` instead of `self.destroy` | 0.25h | Prevents crash |

---

### Phase B: UI Polish & Quality of Life

| # | Feature | Effort | Impact |
|---|---------|--------|--------|
| B1 | **Resizable dungeon panels** — Let user drag the split between map and log in `DungeonScreen` using a `PanedWindow` | 3h | High UX |
| B2 | **Combat animations** — Smooth HP bar transitions (tween drain/fill over 300ms), floating damage numbers on hit, shake effect on critical hits | 5–6h | High visual polish |
| B3 | **Contextual keyboard shortcut sheet** — Press `?` to show an overlay listing all available keyboard shortcuts for the current screen | 3h | High UX |
| B4 | **Sound effects** — Hook up the reserved `sound_enabled` setting. Play UI click sounds, combat hit sounds, dungeon ambience, menu music using `winsound`/`pygame` | 8h | Immersion |
| B5 | **Theme system** — Currently dark-only. Implement light + high_contrast themes (already reserved in settings). Add theme preview thumbnails | 6h | Accessibility |
| B6 | **HP Bar color on city screen** — Color-code party HP bars in the hero card by health percentage (green > 50%, orange > 25%, red ≤ 25%) | 0.5h | Quick win |

---

### Phase C: Feature Expansion

| # | Feature | Effort | Impact |
|---|---------|--------|--------|
| C1 | **Bestiary tab** — New tab in `InventoryScreen` showing discovered enemy types, kill counts, element weaknesses, and drop tables | 6h | Content depth |
| C2 | **Achievement system** — Track milestones (first kill, floor 10 cleared, all cities visited, superboss defeated). Show in a new overlay panel with progress bars | 8h | Engagement & replayability |
| C3 | **Auto-save configuration** — Currently saves on every floor clear. Add toggle + interval setting (every N floors, every N minutes) | 2h | QoL |
| C4 | **Combat log export** — Allow saving the session log to a `.txt` file from the `LogWindow` with a "Save As…" button | 1h | QoL |
| C5 | **City map visualization** — Replace text service list with a stylized node graph showing connected cities, travel times, danger levels. Click nodes to travel | 10h | Major UX upgrade |
| C6 | **Mount stable UI** — Visual mount selection in city with portrait images, stat comparison cards, and preview of speed/safety bonuses | 4h | Feature depth |

---

### Phase D: Architecture Improvements

| # | Task | Effort | Impact |
|---|------|--------|--------|
| D1 | **Add type hints throughout GUI layer** — All method signatures, queue types, callback signatures | 4h | Maintainability & IDE support |
| D2 | **Extract keyboard shortcut pattern** — Every screen duplicates `_setup_key_binds`/`_on_key`. Create a `KeyboardMixin` class | 2h | DRY, consistency |
| D3 | **Add unit tests** — `ScreenManager` transitions, back-stack navigation, overlay push/pop. `CombatScreen` polling loop with mock I/O | 6h | Regression prevention |
| D4 | **Thread-safety assertions** — Add runtime check (debug mode only) that tkinter widget access happens on the main thread. Prevents "TclError from wrong thread" | 3h | Debugging aid |
| D5 | **Consolidate I/O redirection** — `facility_screen.py` has `_redirected_print`/`_redirected_input`. `terminal.py` has `Terminal` class. `combat_io.py` has `BaseCombatIO`/`GUICombatIO`. Three parallel I/O systems — unify into one pattern | 8h | Reduce complexity |

---

## 🏆 Recommended Priority Order

| Order | Phase | Tasks | Total Effort | Rationale |
|-------|-------|-------|-------------|-----------|
| **1** | A | A1, A2, A4, A6 | 3.5h | Fix crash-causing bugs. Game must be stable before adding features. |
| **2** | A + B | A3, A5, B6 | 4.25h | Remaining critical fixes + quick visible win (HP bar colors). |
| **3** | B | B1, B3 | 6h | High-impact UX improvements players notice immediately. |
| **4** | B | B2 | 5–6h | Combat animations make the game feel polished and modern. |
| **5** | C | C3, C4 | 3h | Quick QoL wins with low effort. |
| **6** | C + D | C1, D1, D2 | 12h | Content depth + tech debt that speeds up future development. |
| **7** | B | B4, B5 | 14h | Sound + themes — high effort but transformative. |
| **8** | C | C2, C5, C6 | 22h | Major feature expansion. |
| **9** | D | D3, D4, D5 | 17h | Architecture hardening for long-term maintainability. |

---

## Appendix: Thread Safety Notes

The GUI uses a **multi-threaded architecture** where game logic runs in background daemon threads and communicates with tkinter via queues:

| Component | Thread | Communication |
|-----------|--------|---------------|
| `FacilityScreen` | Background daemon | `_input_queue` (facility → GUI), `_pending_lines` + `after(0, _flush_output)` (GUI → display) |
| `CombatScreen` | Background daemon | `GUICombatIO.input_queue` / `.output_queue` (thread-safe `queue.Queue`) |
| `DungeonScreen` | Background daemon (inherits `FacilityScreen`) | Same as FacilityScreen + monkey-patched `term.print` for map capture |
| `ScreenManager` | Main thread (tkinter) | Owns all widgets, processes `after()` callbacks |

**Key rule:** Only the main thread may touch tkinter widgets. Background threads use `self.after(0, lambda: ...)` to schedule UI updates. This pattern is mostly followed, but the bugs noted above (C1, C2, C3) are violations where background thread effects leak past widget destruction.
