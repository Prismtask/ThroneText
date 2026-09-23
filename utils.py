import os
import random

# ── GUI terminal detection (safe import for terminal mode) ──────────
try:
    from gui.terminal import get_terminal as _get_gui_terminal
except ImportError:
    _get_gui_terminal = lambda: None


def _term():
    """Return the GUI Terminal if running in GUI mode, else None."""
    return _get_gui_terminal()


def _tprint(*args, sep=" "):
    """Print to GUI if available, else to terminal."""
    t = _term()
    text = sep.join(str(a) for a in args)
    if t:
        t.print(text)
    else:
        print(text)


def _tpause(prompt="Press Enter to continue..."):
    """Pause for user acknowledgement."""
    t = _term()
    if t:
        t.pause(prompt)
    else:
        input(prompt)


def _tinput(prompt=""):
    """Free-text input. Falls back to terminal input() if no GUI."""
    t = _term()
    if t:
        return t.input(prompt)
    else:
        return input(prompt)


def _tclear():
    """Clear screen (no-op in GUI since output is managed by the panel)."""
    t = _term()
    if t:
        t.clear()
    else:
        clear_screen()


def _tmenu(options, prompt="Choose an option:", allow_cancel=False, cancel_label="Cancel"):
    """Show a menu; returns 0-based index or -1."""
    t = _term()
    if t:
        return t.menu(options, prompt=prompt, allow_cancel=allow_cancel, cancel_label=cancel_label)
    else:
        for i, opt in enumerate(options):
            print(f"{i+1}. {opt}")
        if allow_cancel:
            print(f"0. {cancel_label}")
        try:
            choice = input(prompt + " ").strip()
            idx = int(choice) - 1
            if allow_cancel and idx == -1:
                return -1
            if 0 <= idx < len(options):
                return idx
        except (ValueError, IndexError):
            pass
        return -1


def _get_wonderland_max_floor(player):
    """Return the highest floor reached in Wonderland dungeon."""
    wl_prog = player.get("city_floors", {}).get("wonderland", {})
    return wl_prog.get("max_floor", 1)


def _int_to_roman(num):
    """Convert integer (1-10) to Roman numeral."""
    val = [10, 9, 5, 4, 1]
    syms = ["X", "IX", "V", "IV", "I"]
    roman = ""
    i = 0
    while num > 0:
        d = num // val[i]
        roman += syms[i] * d
        num -= d * val[i]
        i += 1
    return roman


def apply_death_penalty(player):
    """Apply death penalties without any I/O. Safe for both terminal and GUI modes.

    Returns the penalty gold amount for display purposes.
    """
    gold = player.get("gold", 0)
    penalty_pct = 0.20
    penalty_gold = max(10, int(gold * penalty_pct))
    penalty_gold = min(penalty_gold, gold)

    # Apply penalty
    player["gold"] = max(0, gold - penalty_gold)

    # Advance time for recovery (8 hours)
    advance_time(player, 480)

    # Heal player to 1 HP
    player["current_hp"] = 1

    # Heal allies to 1 HP as well
    for ally in player.get("allies", []):
        if ally.get("current_hp", 0) <= 0:
            ally["current_hp"] = 1

    # Return to origin city
    origin = player.get("origin_city", "solmere")
    player["location"] = origin

    # Wipe dungeon progress
    for key in ("saved_dungeon_floor", "saved_dungeon_rooms", "saved_dungeon_room_index"):
        player.pop(key, None)

    # Clear any lingering combat state
    if "abyss_triple_actions" in player:
        player["abyss_triple_actions"] = 0
    player.pop("abyss_tempo_pending", None)

    # Save game
    from save_load import save_game
    save_game(player)

    return penalty_gold


def handle_player_death(player):
    """Handle player death: offer continue or quit, apply penalties if continuing.

    Terminal-mode wrapper that prints UI and calls apply_death_penalty().
    """
    clear_screen()
    _tprint("\n" + "=" * 50)
    _tprint("         ☠  YOU HAVE BEEN DEFEATED  ☠")
    _tprint("=" * 50)

    # Penalty calculation
    gold = player.get("gold", 0)
    penalty_pct = 0.20  # 20% gold loss
    penalty_gold = max(10, int(gold * penalty_pct))
    penalty_gold = min(penalty_gold, gold)  # can't lose more than you have

    _tprint(f"\n  A passing adventurer drags you from the brink.")
    _tprint(f"  You wake hours later in a back-alley clinic, battered but alive.")
    _tprint(f"\n  Penalty: -{penalty_gold} gold ({int(penalty_pct*100)}% of your coin, minimum 10g)")
    _tprint(f"\n  [C]ontinue your journey")
    _tprint(f"  [Q]uit to main menu")

    while True:
        choice = _tinput("\n  Choice: ").strip().lower()
        if choice == "q":
            return False
        if choice == "c":
            break
        _tprint("  Invalid choice. Enter C to continue or Q to quit.")

    apply_death_penalty(player)
    return True


def clear_screen():
    """Clear the terminal screen (works on Windows and Unix-like systems)."""
    os.system('cls' if os.name == 'nt' else 'clear')


# ── Wonderland clock flavours ──────────────────────────────────────────
_WL_CLOCK_FLAVORS = [
    ("!!:!!", "The little lamb is confused"),
    ("?:??", "The clock has forgotten how to count"),
    ("\u20ae:\u20ae\u20ae", "Teatime, obviously"),
    ("\u221e:\u221e\u221e", "Always. Never. Both."),
    ("\u231b:\u23f3", "The hourglass is arguing with itself"),
    ("42:42", "The answer. The question is still pending."),
    ("--:--", "Time is on strike. It wants better working conditions."),
    ("13:13", "The thirteenth hour. The one that doesn't exist. Until it does."),
    ("\u2465:\u24ea\u2465", "The March Hare broke the minute hand again"),
    ("ZZ:ZZ", "The Dormouse is dreaming the clock. Don't wake him."),
    ("\U0001F3A9:\u2615", "Hatter o'Clock"),
    ("?:!?", "The clock is asking you a question. You don't know the answer."),
    ("AB:CD", "The Caterpillar is spelling something. Probably."),
    ("OO:PS", "The White Rabbit dropped the clock. Again."),
    ("--:--", "The hands have gone for a walk. They'll be back. Probably."),
]


def format_time(total_minutes):
    """Convert total minutes to HH:MM (24-hour format).

    When the player is in Wonderland (player dict passed), returns
    a whimsical clock flavour instead.
    """
    if isinstance(total_minutes, dict):
        if total_minutes.get("wonderland_active"):
            clock, flavor = random.choice(_WL_CLOCK_FLAVORS)
            return f"{clock}  \u2014 {flavor}"
        total_minutes = total_minutes.get("time_minutes", 480)
    hours = (total_minutes // 60) % 24
    minutes = total_minutes % 60
    return f"{hours:02d}:{minutes:02d}"


def advance_time(player, minutes):
    """Advance player's time by minutes, handling day rollover cleanly.

    While in Wonderland, real time does not advance — only an internal
    Wonderland clock ticks forward.
    """
    if player.get("wonderland_active"):
        player["wl_internal_time"] = player.get("wl_internal_time", 0) + minutes
        return format_time(player)

    if "time_minutes" not in player:
        player["time_minutes"] = 8 * 60  # Start at 08:00
    if "day" not in player:
        player["day"] = 1

    old_day = player["day"]
    player["time_minutes"] += minutes
    
    # 1440 minutes = 24 hours
    if player["time_minutes"] >= 1440:
        days_passed = player["time_minutes"] // 1440
        player["day"] += days_passed
        player["time_minutes"] %= 1440
        
        # ── Process day-based events ─────────────────────────────────────
        from events import process_day_rollover, display_event_alert, queue_event_alerts
        events = process_day_rollover(player, days_passed, old_day)
        
        if events:
            if player.get("location") == "dungeon":
                # Queue alerts to show when player returns to the city
                queue_event_alerts(player, events)
            else:
                # Show immediately (GUI mode suppresses console via journal)
                for evt in events:
                    display_event_alert(evt)
        
        # CHECK BOUNTY EXPIRY AFTER DAY ROLLOVER
        from facilities.guild import check_bounty_expiry
        expired = check_bounty_expiry(player)
        if expired:
            # Record expired bounties in the journal instead of printing to console
            from events import ensure_journal
            ensure_journal(player)
            day = player.get("day", 1)
            for b in expired:
                player["journal"]["events"].append({
                    "day": day,
                    "name": "Bounty Expired",
                    "desc": f"Bounty for {b['target_name']} expired (deadline passed).",
                    "tag": "[BOUNTY]",
                    "fixed": False,
                })
        
    return format_time(player["time_minutes"])


def get_time_period(total_minutes):
    """Determine time period for difficulty scaling."""
    hour = (total_minutes // 60) % 24
    if 0 <= hour <= 3:
        return "midnight"  # Very punishing
    elif 4 <= hour <= 7:
        return "dawn"
    elif hour == 12 or 13 <= hour <= 14:  # Noon period
        return "noon"
    elif 17 <= hour <= 20:  # Dusk
        return "dusk"
    elif 21 <= hour <= 23:
        return "night"
    return "normal"


def get_difficulty_multiplier_from_time(player):
    """Get time-based difficulty multiplier (time-of-day + daily events)."""
    if "time_minutes" not in player:
        return 1.0
    period = get_time_period(player["time_minutes"])
    if period == "midnight":
        mult = 1.8  # Very punishing for early-mid game
    elif period == "dawn":
        mult = 1.1
    elif period == "noon":
        mult = 1.25
    elif period == "dusk":
        mult = 1.4
    elif period == "night":
        mult = 1.6
    else:
        mult = 1.0

    # Daily events: Peaceful Skies (-10%) / Crimson Dawn (+15%)
    difficulty_mod = player.get("daily_effects", {}).get("difficulty_mod", 0.0)
    if difficulty_mod:
        mult *= (1.0 + difficulty_mod)

    return mult


# ── ANSI escape code stripping (for GUI text widgets that don't support SGR) ─

import re as _re

_ANSI_PATTERN = _re.compile(r'\x1b\[[0-9;]*m')

def strip_ansi(text):
    """Remove ANSI SGR escape sequences (color codes) from a string.

    Used before inserting text into tkinter Text widgets, which don't
    process ANSI escape sequences and would render them as garbage.
    """
    return _ANSI_PATTERN.sub('', text)