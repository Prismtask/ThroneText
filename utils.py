import os

def handle_player_death(player):
    """Handle player death: offer continue or quit, apply penalties if continuing."""
    clear_screen()
    print("\n" + "=" * 50)
    print("     ☠  YOU HAVE BEEN DEFEATED  ☠")
    print("=" * 50)

    # Penalty calculation
    gold = player.get("gold", 0)
    penalty_pct = 0.20  # 20% gold loss
    penalty_gold = max(10, int(gold * penalty_pct))
    penalty_gold = min(penalty_gold, gold)  # can't lose more than you have

    print(f"\n  A passing adventurer drags you from the brink.")
    print(f"  You wake hours later in a back-alley clinic, battered but alive.")
    print(f"\n  Penalty: -{penalty_gold} gold ({int(penalty_pct*100)}% of your coin, minimum 10g)")
    print(f"\n  [C]ontinue your journey")
    print(f"  [Q]uit to main menu")

    while True:
        choice = input("\n  Choice: ").strip().lower()
        if choice == "q":
            return False
        if choice == "c":
            break
        print("  Invalid choice. Enter C to continue or Q to quit.")

    # Apply penalty
    player["gold"] = max(0, gold - penalty_gold)

    # Advance time for recovery (8 hours)
    advance_time(player, 480)

    # Heal player to 1 HP
    player["current_hp"] = 1

    # Heal allies to 1 HP as well (they were also rescued)
    for ally in player.get("allies", []):
        if ally.get("current_hp", 0) <= 0:
            ally["current_hp"] = 1

    # Return to origin city
    origin = player.get("origin_city", "solmere")
    player["location"] = origin

    # Wipe dungeon progress so they don't respawn mid-floor
    for key in ("saved_dungeon_floor", "saved_dungeon_rooms", "saved_dungeon_room_index"):
        player.pop(key, None)

    # Clear any lingering combat state
    player["abyss_triple_actions"] = 0
    player.pop("abyss_tempo_pending", None)

    # Save game
    from save_load import save_game
    save_game(player)

    print(f"\n  You recover in {origin.title()}.")
    print(f"  Current time: {format_time(player.get('time_minutes', 480))}")
    print(f"  Gold: {player.get('gold', 0)}")
    input("\n  Press Enter to continue...")
    return True


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
                # Show immediately
                for evt in events:
                    display_event_alert(evt)
        
        # CHECK BOUNTY EXPIRY AFTER DAY ROLLOVER
        from facilities.guild import check_bounty_expiry
        expired = check_bounty_expiry(player)
        if expired:
            print(f"\n {len(expired)} bounty(s) expired due to time!")
            for b in expired:
                print(f"  - {b['target_name']} (deadline passed)")
        
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