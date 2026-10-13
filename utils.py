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


def display_name(entity):
    """Return an ally/girl's chosen name (nickname), awakened name, or species name.

    Resolution: nickname → awakened_name → name. The underlying ``name`` field
    is never overwritten — it is the species name and part of the girl's unique
    identity (save matching, daily talk tracking).
    """
    if not entity:
        return ""
    return ((entity.get("nickname") or "").strip()
            or (entity.get("awakened_name") or "").strip()
            or entity.get("name", ""))


def display_name_with_species(entity):
    """Return 'Nickname (Awakened Name / Species)' when renamed, otherwise the base name."""
    if not entity:
        return ""
    nick = (entity.get("nickname") or "").strip()
    base = (entity.get("awakened_name") or "").strip() or entity.get("name", "")
    return f"{nick} ({base})" if nick else base


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

    # Advance time for recovery (8 hours ≈ 4 blocks in the block model)
    import time_blocks
    time_blocks.spend_blocks(player, 4)

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
    # Wipe wild-dungeon run state (defensive — normal exits clean up first)
    player.pop("wild_dungeon_id", None)
    player.pop("_wild_prev_floor", None)
    for key in ("saved_wild_floor", "saved_wild_rooms", "saved_wild_room_index"):
        player.pop(key, None)

    # Clear any lingering combat state
    if "abyss_triple_actions" in player:
        player["abyss_triple_actions"] = 0
    player.pop("abyss_tempo_pending", None)

    # Event Horizon: scrub the transient in-run flag + pay the deferred death
    # payout AFTER the toll (the payout itself is exempt — docs §10.2)
    player.pop("_eh_in_run", None)
    pending = player.pop("_eh_pending_payout", 0)
    if pending:
        player["gold"] = player.get("gold", 0) + pending
        _tprint(f"  ◎ The Event Horizon's withheld fortune arrives: +{pending} gold.")

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
    """Advance game time by `minutes` using the block model.

    Delegates to time_blocks (docs/time_system_design.md): ≤15 min free,
    16–90 = 1 block, 91+ = 2 blocks; overflow eats into the next day.
    Whole days (1440+) roll the day once per 1440 (tests / scripted skips).
    Sleep is a caller-side special path: `time_blocks.end_day(player, slept=True)`.
    """
    import time_blocks
    return time_blocks.advance_time(player, minutes)


# ── Time-of-day → difficulty (block phases, docs §7) ────────────────────────

PHASE_DIFFICULTY = {"morning": 1.0, "noon": 1.1, "night": 1.25}


def get_time_period(total_minutes):
    """Phase id from legacy clock minutes (block model: day starts 06:00)."""
    hour = (total_minutes // 60) % 24
    if 6 <= hour < 14:
        return "morning"
    if 14 <= hour < 22:
        return "noon"
    return "night"


def get_difficulty_multiplier_from_time(player):
    """Phase-based difficulty multiplier (docs §7).

    Morning 1.0 / Noon 1.1 / Night 1.25, with daily-event modifiers
    (Peaceful Skies −10% / Crimson Dawn +15% / Full Moon handled in stats)
    multiplying on top.
    """
    if not player:
        return 1.0
    try:
        import time_blocks
        phase = time_blocks.get_day_phase(player)
    except Exception:
        phase = get_time_period(player.get("time_minutes", 8 * 60))
    mult = PHASE_DIFFICULTY.get(phase, 1.0)

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