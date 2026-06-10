import os

def clear_screen():
    """Clear the terminal screen (works on Windows and Unix-like systems)."""
    os.system('cls' if os.name == 'nt' else 'clear')


def format_time(total_minutes):
    """Convert total minutes to HH:MM (24-hour format)."""
    hours = (total_minutes // 60) % 24
    minutes = total_minutes % 60
    return f"{hours:02d}:{minutes:02d}"


def advance_time(player, minutes):
    """Advance player's time by minutes, handling day rollover cleanly."""
    if "time_minutes" not in player:
        player["time_minutes"] = 8 * 60  # Start at 08:00
    if "day" not in player:
        player["day"] = 1

    player["time_minutes"] += minutes
    
    # 1440 minutes = 24 hours
    if player["time_minutes"] >= 1440:
        days_passed = player["time_minutes"] // 1440
        player["day"] += days_passed
        player["time_minutes"] %= 1440  # Caps the clock strictly between 0 and 1439
        
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
    """Get time-based difficulty multiplier."""
    if "time_minutes" not in player:
        return 1.0
    period = get_time_period(player["time_minutes"])
    if period == "midnight":
        return 1.8  # Very punishing for early-mid game
    elif period == "dawn":
        return 1.1
    elif period == "noon":
        return 1.25
    elif period == "dusk":
        return 1.4
    elif period == "night":
        return 1.6
    return 1.0