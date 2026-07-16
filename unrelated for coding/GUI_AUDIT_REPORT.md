# TerminalRPG GUI — Comprehensive Bug & UX Improvement Audit

**Date:** 2026-07-07  
**Scope:** Every file in `gui/`, plus related facility/travel files that interface with the GUI  
**Methodology:** Full static code analysis of all GUI-related source files

---

## ⚠️ CRITICAL BUGS (Game-Breaking / Data-Loss Risk)

### BUG-1: Travel Facility — Leaving Early Does Not Return to City Properly
**Files:** `gui/screens/city_screen.py`, `gui/screens/facility_screen.py`, `facilities/travel.py`

**Problem:**
When `_open_travel()` is called from `CityScreen`, it creates a `FacilityScreen` wrapping `travel_to_city()`. If the player presses the "← Back to City" button before choosing a destination (while `_thread.is_alive()` is True), the `_finish()` method is called.

- `_finish()` calls `on_close(result)` → this runs `_after_travel(result)` with `result=None`.
- `_after_travel` checks for `result == "dead"`, which is false, and `player.get("current_hp", 1) <= 0`, which is also false.
- Then it does `_refresh_city_id()` and if `self.city_id != old_city`, switches to a new `CityScreen`.
- **However, `_finish()` ALSO has a fallback:** if `on_close` is falsy or doesn't exist, it does `self.sm.switch_to(CityScreen)` directly. But since `on_close=_after_travel` IS set, this should work.

**The actual bug:** When the user clicks "Back to City" and the facility thread is still running, the confirm dialog appears. If user clicks "Yes", `_finish()` is called. But `_finish()` also has an `else` branch that overwrites to `CityScreen`. The travel thread is NOT properly terminated — it continues in the background. This can cause:
- The travel thread eventually completing and trying to update destroyed widgets (crash)
- The player's location being modified by the still-running travel thread after they've "returned"
- Ghost input blocking (`_input_queue` never unblocked)

**Suggested Fix:**
1. Add a `_stop_facility()` method to `FacilityScreen` that properly terminates the background thread.
2. Before calling `_finish()`, set a flag that tells the thread to abort.
3. Restore original I/O redirects before destroying.

---

### BUG-2: `_equip_on_ally` Has Duplicated Code Block (Double Execution)
**File:** `gui/screens/inventory_screen.py`, lines ~695-725 (`_equip_on_ally` → `do_equip`)

**Problem:**
The inner function `do_equip()` has two identical blocks of code that run sequentially:
```python
# First block (lines ~695-710):
sel = listbox.curselection()
if not sel: return
item = equip_items[sel[0]]
# ... accessory check ...
# equip_ally_item, dlg.destroy(), _refresh_all()

# Second block (lines ~711-725): IDENTICAL CODE RUNS AGAIN
sel = listbox.curselection()        # <-- already destroyed dialog!
if not sel: return
item = equip_items[sel[0]]          # <-- will crash if dialog is gone
# ... accessory check again ...
# ... equip_ally_item again ...
```

Clicking "Equip" executes `equip_ally_item` TWICE on the same item, causing doubly-removed inventory entries (potential `ValueError`) and potentially equipping the wrong item on the second pass.

**Suggested Fix:** Delete the duplicate block entirely. Lines 711-725 are a copy-paste error.

---

### BUG-3: `_prompt_accessory_choice` Also Has Duplicated Code
**File:** `gui/screens/inventory_screen.py`, lines ~750-790 (`_prompt_accessory_choice` → `choose(slot)`)

**Problem:**
Same pattern as BUG-2. The `choose(slot)` inner function removes the item from inventory, equips it, then immediately removes it again and equips it again. This causes:
- `equip_item` called twice
- `equip_ally_item` called twice for ally target
- Dialog destroyed after the first set of calls, so the second `dlg.destroy()` may raise `TclError`

**Suggested Fix:** Delete the duplicate logic block. Keep only the first one.

---

### BUG-4: `_equip_item` Logs and Refreshes Twice
**File:** `gui/screens/inventory_screen.py`, lines ~630-645 (`_equip_item`)

**Problem:**
```python
        self.sm.log(f"Equipped {item['name']}.")
        self._refresh_all()
        self.sm.log(f"Equipped {item['name']}.")   # DUPLICATE
        self._refresh_all()                          # DUPLICATE
```
The log and refresh are called twice at the end of `_equip_item`.

**Suggested Fix:** Remove the duplicate `self.sm.log(...)` and `self._refresh_all()` lines.

---

### BUG-5: Superboss Fights Bypass GUI Combat Override
**File:** `dungeon.py`, lines ~298-348 (inside `explore_dungeon`)

**Problem:**
The GUI passes `combat_override=_gui_combat` to `explore_dungeon`, which correctly handles regular combat rooms (line ~432). However, superboss encounters (every 20th floor, lines 298-348) call specialized functions directly (`combat_broodmother`, `combat_slitcurrent`, etc.) which use terminal I/O (`print`/`input`), NOT the GUI overrides. This means:
- Superboss battles show NO GUI — the game hangs or crashes because the I/O threads are not properly redirected.
- The GUI `DungeonScreen` sits idle while the dungeon thread blocks on `builtins.input()` for the superboss fight.

**Suggested Fix:**
Either:
1. Refactor superboss functions to accept a `combat_override` parameter (like normal combat)
2. Have the `DungeonScreen._run_facility()` redirect I/O for superboss fights to use the facility I/O bridge
3. Create GUI wrapper screens for each superboss (like normal `CombatScreen`)

---

### BUG-6: `confirm_dialog` and `ok_dialog` — Parent Window Reference May Become Stale
**File:** `gui/widgets/confirm_dialog.py`

**Problem:**
Both `confirm_dialog()` and `ok_dialog()` call `parent.winfo_toplevel()` to get the root window for positioning and `transient()`. However, if the parent widget has been destroyed between scheduling and execution (common with `after()` callbacks), this raises `tk.TclError`. This can happen when:
- Combat ends quickly and the combat screen is destroyed
- A dialog is queued via `after()` but the screen was already switched

**Suggested Fix:** Wrap `parent.winfo_toplevel()` in a try/except and fall back to the screen manager's root window.

---

## 🐛 MEDIUM BUGS (Incorrect Behavior / Crashes in Edge Cases)

### BUG-7: `DungeonScreen._finish()` Override Doesn't Stop Facility Thread
**File:** `gui/screens/dungeon_screen.py`

**Problem:**
`DungeonScreen` overrides `build_ui()` and `_run_facility()` but does NOT override `_finish()`, `_on_back()`, or `destroy()`. When the user clicks "← Flee to City":
1. `_on_flee()` shows `confirm_dialog` → calls `self._finish()`.
2. `_finish()` from `FacilityScreen` runs: calls `on_close` → `_handle_result` → `_on_result`.
3. But the dungeon thread is still running! `_finish()` does not stop it.

**Real scenario:** If player clicks "Flee to City" but the dungeon thread is in the middle of generating a room, showing output, or waiting for combat to end, the thread keeps running and tries to update destroyed widgets.

**Suggested Fix:** Override `_finish()` in `DungeonScreen` to set a stop flag, or use the same `_stop_facility()` mechanism suggested in BUG-1.

---

### BUG-8: Combat Screen — Missing Keyboard Binding for "Enter" During Target Selection
**File:** `gui/screens/combat_screen.py`

**Problem:**
When in target selection mode (`_pending_input_mode` is `enemy_target` or `capture_target`), the player must press a number key (1-9) to select an enemy. Pressing Enter does nothing during this phase. A new player might try pressing Enter to "confirm" the highlighted enemy.

Additionally, there's no clickable "Confirm" button — clicking an enemy frame calls `_on_enemy_click()` directly, but there's no visible instruction that clicking or number keys are the only way to interact.

**Suggested Fix:**
1. Add a temporary "Click an enemy or press 1-9 to select" label in the action panel during target mode.
2. Consider allowing Enter to select the first available enemy.
3. Ensure click targets cover the full enemy frame area (currently only binds to frame + direct children).

---

### BUG-9: `_on_enemy_click` Only Binds to Direct Children
**File:** `gui/screens/combat_screen.py`, lines ~118-122

**Problem:**
```python
for i in range(len(self.enemies)):
    frame = self.renderer.get_enemy_frame(i)
    if frame:
        frame.bind("<Button-1>", lambda e, idx=i: self._on_enemy_click(idx))
        for child in frame.winfo_children():
            child.bind("<Button-1>", lambda e, idx=i: self._on_enemy_click(idx))
```

This only binds to `frame` and its immediate `winfo_children()`. But `CombatRenderer._create_entity_frame()` creates nested frames (e.g., `name_frame` inside the main frame, which contains `active_lbl`, `name_lbl`, `mg_lbl`). Grandchildren (e.g., `name_lbl`) are NOT bound because `winfo_children()` only returns direct children. Clicks on the name label or HP bar won't register.

**Suggested Fix:** Use a recursive function to bind all descendants, or use `bind_class` with a unique tag.

---

### BUG-10: Facility Screen — `_on_back` While Thread Alive Shows Dialog on Every Attempt
**File:** `gui/screens/facility_screen.py`, `_on_back()`

**Problem:**
If the facility thread is alive and the user clicks "Back", a confirm dialog appears. If the user clicks "No", the dialog closes. But there's no debounce — the user can rapidly click "Back" and spawn multiple confirm dialogs stacked on top of each other.

**Suggested Fix:** Add a `_confirm_dialog_open` flag.

---

### BUG-11: `DungeonScreen` — `_gui_combat` Blocks Dungeon Thread Indefinitely If GUI Crashes
**File:** `gui/screens/dungeon_screen.py`, `_gui_combat()`

**Problem:**
```python
def _gui_combat(self, player, enemy_keys, floor=None, room_num=None, total_rooms=None):
    result_queue = queue.Queue()
    def start_combat():
        from gui.screens.combat_screen import CombatScreen
        self.sm.switch_to(CombatScreen, ...)
    self.sm.root.after(0, start_combat)
    return result_queue.get()   # <-- blocks forever if CombatScreen never puts result
```

If `CombatScreen` encounters an error before calling `on_result`, or if the `on_result` callback is somehow lost, the dungeon thread blocks forever on `result_queue.get()`. There's no timeout.

**Suggested Fix:** Add a timeout to `result_queue.get(timeout=300)` (5 minutes) and fall back to a safe state.

---

### BUG-12: `CityScreen._return_from_dungeon` Destroys and Rebuilds UI Manually
**File:** `gui/screens/city_screen.py`, lines ~260-270

**Problem:**
```python
elif result == "fled":
    self.sm.log("You fled the dungeon.")
    self._refresh_city_id()
    for w in self.winfo_children():
        w.destroy()
    self.build_ui()
```

This manually destroys and rebuilds the UI instead of using `self.sm.switch_to(CityScreen, push_history=False)`. This is inconsistent with how other results are handled (e.g., the "else" branch at the bottom does the same thing). More critically, manually destroying children and calling `build_ui()` again may cause subtle issues with event bindings, scheduled `after()` callbacks, and widget state not being fully reset.

**Suggested Fix:** Use `self.sm.switch_to(CityScreen, push_history=False)` consistently for all return paths.

---

## 🟡 MINOR BUGS

### BUG-13: `theme.py` — `Theme` Class Defined Twice
**File:** `gui/theme.py`, lines ~55-70 and ~77-93

**Problem:**
The `Theme` class is defined twice in the same file. The second definition overwrites the first, but both contain different sets of attributes. The first definition has `FONT_SIZE`, `FONT_SIZE_LARGE`, `FONT_SIZE_SMALL`, `FONT_BOLD` — these are lost in the second definition. However, `set_font_size()` updates `Theme.FONT_SIZE` etc. dynamically, and the second definition re-declares `FONT`, `FONT_BOLD`, etc., so the values might still work. But the duplicated class is confusing and may cause issues if someone adds attributes to the wrong definition.

**Suggested Fix:** Remove the first `class Theme` definition (lines 55-70), keep only the second.

---

### BUG-14: `screen_manager.py` — `go_back()` Does Not Restore Previous Screen State
**File:** `gui/screen_manager.py`, `go_back()`

**Problem:**
`go_back()` instantiates a brand-new screen of the previous class:
```python
prev_class = self._screen_history.pop()
self.current_screen = prev_class(parent=self.content_frame, screen_manager=self)
```

This means all UI state (scroll positions, selected tabs, temporary selections) is lost. For example, going back from Settings to City forgets which tab was selected. This is by design for simplicity, but for some screens (like Inventory), this can be jarring.

**Suggested Fix:** Consider caching screen instances for frequently-visited screens, or restoring state from a saved context dict.

---

### BUG-15: `DungeonScreen` — Map Panel Width Fixed at 200px
**File:** `gui/screens/dungeon_screen.py`, line ~80

**Problem:**
The map panel has `width=200` and `grid_propagate(False)`. On high-DPI displays or when using larger font sizes, the ASCII map text may be clipped horizontally.

**Suggested Fix:** Make the map panel width proportional to the font size or window width (e.g., `width=max(180, font_size * 18)`).

---

### BUG-16: `CombatScreen._handle_result` — Default Result Path Shows CityScreen After 1.5s Delay
**File:** `gui/screens/combat_screen.py`, lines ~408-412

**Problem:**
```python
if self.on_result:
    self.on_result(result)
else:
    if not self._destroyed:
        self.after(1500, lambda: self._return_to_city() if not self._destroyed else None)
```

When `on_result` is set (which it always is when launched from `DungeonScreen._gui_combat`), the result is passed back immediately. But when launched standalone (e.g., testing), there's a 1.5 second delay before returning to city. This delay is unnecessary and delays user interaction.

**Suggested Fix:** Remove the `after(1500, ...)` delay — switch immediately, or show a "Combat Ended" dialog with an OK button.

---

### BUG-17: `launcher.py` — No GUI Error Handling for Thread Crashes
**File:** `launcher.py` (entry point)

**Problem:**
If a daemon thread (facility, dungeon, combat) crashes with an unhandled exception, the main GUI continues running but the user sees no error. The screen may appear frozen. There's no global crash handler for background threads.

**Suggested Fix:** Add a `threading.excepthook` or wrap facility/combat thread targets in try/except with `ok_dialog` error reporting.

---

## 🎨 UX IMPROVEMENTS (Not Bugs, But Needed)

### UX-1: Target Selection in Combat — No Instruction Text
**Files:** `gui/screens/combat_screen.py`, `gui/combat/action_panel.py`

**Problem (reported by user):** When the enemy borders light up red in target selection mode, there is no visible instruction telling the player to press a number key or click an enemy. Your friend tried to click but didn't realize number keys work too.

**Current behavior:**
- `set_target_mode(True, "Select a target")` sets the section label to "Select a target" in accent color
- Enemies get red `highlightthickness=2` borders
- Number keys 1-9 and clicks work, but there's NO text like "Press 1-9 or click an enemy"

**Suggested Fix:**
1. Add a prominent instruction label: "▶ Press 1-9 or click an enemy to select target (Esc to cancel)"
2. Show numbers on each enemy frame while in target mode (e.g., "[1]", "[2]")
3. Change cursor to `hand2` or `target` on enemy frames during selection

---

### UX-2: Combat Action Buttons — No Visual Feedback on Hover/Click
**Files:** `gui/combat/action_panel.py`, `gui/screens/combat_screen.py`

**Problem:** The action buttons (`[A] Attack`, `[D] Defend`, etc.) use `relief=tk.RAISED` but there's no color change on hover or pressed state beyond tkinter's default behavior (which is subtle on some platforms).

**Suggested Fix:**
- Bind `<Enter>`/`<Leave>` to change button background
- Add a brief "flash" animation when a button is pressed (e.g., change bg to `ACCENT` for 100ms)

---

### UX-3: No Visual Distinction Between Player and Ally Turns
**File:** `gui/screens/combat_screen.py`, `gui/combat/combat_renderer.py`

**Problem:** When an ally's turn comes up, the action panel shows the ally's skills, but there's no clear indicator that it's not the player's turn. The `> ` active indicator appears in the party column, but it's subtle.

**Suggested Fix:**
- Change the action panel background or border color during ally turns
- Display the ally's name prominently: "▶ AllyName's Turn — Choose Action"
- Color-code the active indicator (gold for player, blue for ally)

---

### UX-4: Bottom Log Panel — No Scrollbar, Cannot Scroll Back
**Files:** `gui/screen_manager.py`, `gui/screens/combat_screen.py`

**Problem:** The global bottom bar log (`screen_manager.log_text`) and the combat log (`combat_screen.log_text`) both lack visible scrollbars. The combat log is 5 lines tall, the bottom bar is ~4 lines. Players can't scroll back to read missed messages.

**Suggested Fix:** Add a small scrollbar to both log text widgets, or make the combat log taller and scrollable with mouse wheel.

---

### UX-5: No Confirmation on "Flee" During Combat
**File:** `gui/screens/combat_screen.py`

**Problem:** Pressing `F` or clicking `[F] Flee` immediately sends the flee command — no confirmation dialog. Since fleeing in dungeon means returning to city (with time penalty), an accidental keypress is punishing.

**Suggested Fix:** Show a confirmation dialog: "Flee from combat? You will return to the city."

---

### UX-6: City Services Grid Has No Keyboard Navigation
**File:** `gui/screens/city_screen.py`

**Problem:** The city services are displayed as a grid of buttons. There's no way to navigate them with keyboard (arrow keys, Tab). The player must use the mouse. The same applies to the bottom action bar.

**Suggested Fix:**
- Add Tab navigation between buttons
- Add keyboard shortcuts (1-9) for each service
- Allow Enter to activate the focused button

---

### UX-7: Inventory Screen — No Item Tooltips/Details
**File:** `gui/screens/inventory_screen.py`

**Problem:** Items in the bag show name, rarity color, and mod abbreviations. But there's no way to see detailed item descriptions (flavor text, full stat breakdown, special effects) without equipping/using the item.

**Suggested Fix:**
- Add a hover tooltip or a "Details" pane on the right side of the bag tab
- Show item description in a tooltip on mouse hover

---

### UX-8: Inventory Screen — "Drop" Has No Confirmation
**File:** `gui/screens/inventory_screen.py`

**Problem:** The "Drop" button immediately removes an item without confirmation. A misclick on a legendary item is permanent.

**Suggested Fix:** Show a confirm dialog before dropping items of rare+ rarity.

---

### UX-9: Facility Screen — "Back to City" Button Color Suggests Danger
**File:** `gui/screens/facility_screen.py`

**Problem:** The "← Back to City" button uses the default `styled_button` which has `bg=Theme.BUTTON_BG` (dark blue). This doesn't stand out from other buttons. In some contexts (especially long facility outputs), the user may not immediately find it.

**Suggested Fix:** Give the back button a distinct color (e.g., slightly brighter or with a border), or always position it at a fixed location (like a sticky bottom bar).

---

### UX-10: Death Screen — No Sound/Animation for Impact
**File:** `gui/screens/death_screen.py`

**Problem:** The death screen is a static page. For such a dramatic game event, there's no visual flourish (fade-in, skull animation, screen shake).

**Suggested Fix:**
- Add a brief fade-in animation
- Pulse the skull emoji
- Delay the button appearance by 1-2 seconds for dramatic effect

---

### UX-11: No Loading Indicator During Facility/Dungeon Thread Operations
**Files:** `gui/screens/facility_screen.py`, `gui/screens/dungeon_screen.py`

**Problem:** When a facility or dungeon screen is launched, the background thread starts immediately. There's no "Loading..." indicator. For slow operations (like generating a dungeon floor), the screen may appear blank or frozen for a moment.

**Suggested Fix:** Show a "Loading..." label or spinner that disappears when the first output arrives.

---

### UX-12: City Screen — No Quick-Reference for Current Stats
**File:** `gui/screens/city_screen.py`

**Problem:** The city screen shows the city name, description, and service buttons, but the player's current HP, level, and gold are only in the top bar. A player may not notice the small top bar text.

**Suggested Fix:** Add a compact "Hero Status" card in the city screen showing HP bar, level, gold, and current floor.

---

### UX-13: No Keyboard Shortcut Legend / Help Screen
**Files:** `gui/app.py`, all screens

**Problem:** There's no in-game reference for keyboard shortcuts. Players discover them by accident (`I` for inventory, `Escape` for back, `Ctrl+Q` to quit). The global bindings are documented in code only.

**Suggested Fix:** Add a "Help" button to the main menu and city screen that shows a keyboard shortcut reference.

---

### UX-14: Settings Screen Changes Don't Take Effect Until Restart
**File:** `gui/screens/settings_screen.py`

**Problem:** Font size and window size changes in settings may not take full effect until the application is restarted. The `SettingsScreen` updates `sm.settings` dict and calls `save_settings()`, but doesn't call `set_font_size()` or update window geometry immediately.

**Suggested Fix:** Apply font size changes immediately and offer to restart for window size changes.

---

### UX-15: Combat HUD Doesn't Show Turn Order for All Combatants
**File:** `gui/combat/combat_renderer.py`

**Problem:** The `turn_order_label` at the bottom of the HUD shows turn order, but the `_refresh_hud()` method in `CombatScreen` only calls `self.renderer.refresh()` without passing `turn_order` data. The `turn_order` parameter is always `None`, so the turn order bar always shows empty.

**Suggested Fix:** Compute turn order from enemy/ally speed stats and pass it to `refresh()`.

---

## 📊 SUMMARY

| Category | Count |
|----------|-------|
| Critical Bugs | 6 |
| Medium Bugs | 6 |
| Minor Bugs | 5 |
| UX Improvements | 15 |
| **Total** | **32** |

### Priority Matrix

| Priority | Bug IDs |
|----------|---------|
| 🔴 Fix Immediately | BUG-1, BUG-2, BUG-3, BUG-4, BUG-5 |
| 🟠 Fix Soon | BUG-6, BUG-7, BUG-8, BUG-9, BUG-11, BUG-12 |
| 🟡 Fix Eventually | BUG-10, BUG-13, BUG-14, BUG-15, BUG-16, BUG-17 |
| 🔵 UX Polish | UX-1 through UX-8 (high), UX-9 through UX-15 (medium) |

---

## 🔧 Quick Wins (Highest Impact, Lowest Effort)

1. **BUG-2/3/4 (Duplicate code in inventory):** Delete ~20 lines of duplicated code. Fixes equip-on-ally crashes and double-logging.
2. **UX-1 (No target instruction in combat):** Add one label widget. Massive usability improvement.
3. **UX-5 (Flee confirmation):** Add `confirm_dialog()` call before sending flee command.
4. **BUG-12 (Inconsistent CityScreen return):** Replace manual destroy + build_ui with `self.sm.switch_to(CityScreen)`.
5. **BUG-13 (Duplicate Theme class):** Delete 15 lines.
