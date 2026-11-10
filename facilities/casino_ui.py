"""facilities/casino_ui.py — terminal UI for tavern tables and the back room.

Phases 1–3 of docs/casino_games_design.md.  All I/O goes through gui.terminal.term
so the facility runs safely inside FacilityScreen's background thread.
"""

import time_blocks

import casino
import karma
from city_dialogue import service_dialogue
from gui.terminal import term
from utils import advance_time


# ── Shared helpers ──────────────────────────────────────────────────────────

def _gold(player):
    try:
        return int(player.get("gold", 0) or 0)
    except (TypeError, ValueError):
        return 0


def _header(player, title, subtitle):
    term.clear()
    term.print(f"=== {title} ===")
    term.print(subtitle)
    term.print(
        f"Gold: {_gold(player):,}g   |   "
        f"Hands left today: {casino.hands_remaining(player)}"
    )


def _dealer_line(player):
    """Karma-tier flavour for the back-room dealer."""
    if not karma.is_enabled(player):
        return "The dealer doesn't ask your name. That's the service."
    tier = karma.get_karma_tier(player)["label"]
    lines = {
        "Shady": "The dealer counts your coin twice. 'New face. Keep your hands where I can see them.'",
        "Suspect": "The dealer nods at the chalk marks by the door. 'You've been busy. Sit.'",
        "Wanted": "The dealer grins. 'The watch is looking for you. In here, that's a reference.'",
        "Outlaw": "The dealer slides a chair out with one boot. 'The house knows you. The house likes you.'",
    }
    return lines.get(tier, "The dealer looks you over. 'Sit. The house is patient.'")


def _print_settlement(player, venue, stake, settled):
    if settled.get("payout", 0) > 0:
        term.print(f"The table returns {settled['payout']:,}g.")
    net = int(settled.get("net", 0) or 0)
    if net > 0:
        term.print(f"Net: +{net:,}g.")
    elif net < 0:
        term.print(f"Net: {net:,}g.")
    else:
        term.print("Net: 0g.")
    if settled.get("capped"):
        term.print(
            f"The house caps the pot at "
            f"{casino.VENUES[venue]['pot_cap']:,}g."
        )
    term.print(f"Gold: {_gold(player):,}g")
    if settled.get("closed"):
        term.print(
            "The house has seen enough of your luck. "
            "This table is closed for the day."
        )


def _show_house_rules(venue):
    term.clear()
    if venue == "inn":
        term.print("=== TAVERN HOUSE RULES ===")
        term.print("UNDER & OVER — roll 2d6.")
        term.print("  Under 7 or Over 7 pays 2.20x. Exactly 7 pays 5.50x.")
        term.print("  Exactly 7 is offered only where the payout fits the pot cap.")
        term.print("BLACKJACK — Hit or Stand only. No double, split, or insurance.")
        term.print("  Dealer stands on all 17s. Natural 21 pays 6:5 (2.20x).")
        term.print("  A tied hand returns half your stake to you.")
        term.print("LIMITS — 12 hands/day shared with the back room.")
        term.print("  1,000g maximum pot; 1,000g maximum net win per day.")
    else:
        term.print("=== THE BACK ROOM RULES ===")
        term.print("UNDER & OVER — roll 2d6.")
        term.print("  Under 7 or Over 7 pays 2.30x. Exactly 7 pays 5.75x.")
        term.print("  Exactly 7 is offered only where the payout fits the pot cap.")
        term.print("BLACKJACK — Hit or Stand only. No double, split, or insurance.")
        term.print("  Dealer stands on all 17s. Natural 21 pays 6:5 (2.20x).")
        term.print("  A tied hand pushes: your stake comes back.")
        term.print("CHEAT — Under & Over: 1.30x payout. Blackjack: remove the latest card.")
        term.print("  Caught: lose the stake, -2 Karma, 7-day blacklist. 2 attempts/day.")
        term.print("STAKES — 250g (Karma below 0), 1,000g (Karma -15 or lower),")
        term.print("  2,500g (Karma -40 or lower). Levels 5 / 15 / 25.")
        term.print("LIMITS — 12 hands/day shared with the inn.")
        term.print("  10,000g maximum pot; 5,000g maximum net win per day.")
    term.pause()


def _choose_stake(player, venue):
    rows = casino.stake_options(player, venue)
    if not rows:
        term.print("No table is open to you yet.")
        term.pause()
        return None

    labels = [row["label"] for row in rows] + ["Back"]
    choice = term.menu(labels, prompt="Choose a stake:", columns=1)
    if choice < 0 or choice >= len(rows):
        return None

    row = rows[choice]
    if not row["allowed"]:
        term.print(row["reason"] or "That table is not open to you.")
        term.pause()
        return None
    if _gold(player) < row["stake"]:
        term.print(
            f"You need {row['stake']:,}g to sit at that table. "
            f"You have {_gold(player):,}g."
        )
        term.pause()
        return None
    return row["stake"]


def _play_game(player, venue, game):
    stake = _choose_stake(player, venue)
    if stake is None:
        return
    if game == "under_over":
        _play_under_over(player, venue, stake)
    else:
        _play_blackjack(player, venue, stake)


# ── Under & Over ────────────────────────────────────────────────────────────

def _play_under_over(player, venue, stake):
    config = casino.VENUES[venue]
    under_over = config["under_over_pay"]
    seven_pay = config["exact_seven_pay"]
    seven_allowed = casino.exact_seven_allowed(venue, stake)

    term.clear()
    term.print("=== UNDER & OVER ===")
    term.print(f"Stake: {stake:,}g")
    if not seven_allowed:
        term.print("Exactly 7 is not offered at this stake (house pot limit).")

    options = [
        f"Under 7 — pays {under_over:.2f}x (sum 2–6)",
        f"Over 7 — pays {under_over:.2f}x (sum 8–12)",
    ]
    bets = ["under", "over"]
    if seven_allowed:
        options.insert(1, f"Exactly 7 — pays {seven_pay:.2f}x")
        bets.insert(1, "seven")

    cheat_index = None
    if venue == "black_market":
        cheat_index = len(options)
        if casino.cheats_remaining(player) > 0:
            chance, _stat, _dc = casino.cheat_chance(player, stake)
            options.append(
                f"Cheat the dealer — {chance:.0%} success (Karma only if caught)"
            )
        else:
            options.append("Cheat the dealer — no attempts left today")
    options.append("Back")

    choice = term.menu(options, prompt="Place your bet:", columns=2)
    if cheat_index is not None and choice == cheat_index:
        _attempt_cheat(player, venue, stake)
        return
    if choice < 0 or choice >= len(bets):
        return

    ok, message = casino.begin_hand(player, venue, stake)
    if not ok:
        term.print(message)
        term.pause()
        return

    bet = bets[choice]
    result = casino.resolve_under_over(stake, bet, venue)
    settled = casino.finish_hand(player, venue, stake, result["payout"])

    d1, d2 = result["dice"]
    term.print("")
    term.print(f"You roll {d1} + {d2} = {result['total']}.")
    if result["won"]:
        bet_label = {"under": "Under 7", "over": "Over 7", "seven": "Exactly 7"}[result["bet"]]
        term.print(f"{bet_label} wins — pays {result['multiplier']:.2f}x.")
    else:
        term.print("The house takes the stake.")
    _print_settlement(player, venue, stake, settled)
    term.pause()
    advance_time(player, casino.MINUTES_PER_HAND)


def _attempt_cheat(player, venue, stake):
    ok, message = casino.begin_cheat(player, venue, stake)
    if not ok:
        term.print(message)
        term.pause()
        return

    result = casino.resolve_cheat(player, venue, stake)
    settled = casino.finish_cheat(player, venue, stake, result)

    term.print("")
    term.print(
        f"DEX+CHA check: d20({result['roll']}) + {result['stat']} "
        f"vs DC {result['dc']} — {result['chance']:.0%} chance."
    )
    if result["success"]:
        term.print(
            "You palm the bones and slide them across. The dealer's eyes "
            "narrow... but the throw lands your way."
        )
    else:
        term.print("The dealer catches your wrist. The room goes quiet.")

    _print_settlement(player, venue, stake, settled)
    if settled.get("caught"):
        if settled.get("karma_lost"):
            term.print(f"Karma {settled['karma_lost']:+d}.")
        term.print(
            f"The back room is closed to you for "
            f"{settled.get('days_left', 0)} days."
        )
    term.pause()
    advance_time(player, casino.MINUTES_PER_HAND)


# ── Blackjack ───────────────────────────────────────────────────────────────

def _blackjack_result_text(outcome, player_total, dealer_total, venue):
    if outcome == "bust":
        return "Bust. The house takes your stake."
    if outcome == "dealer_natural":
        return "The dealer turns a natural 21. You lose."
    if outcome == "natural":
        return "Blackjack! The table pays 2.20x."
    if outcome == "dealer_bust":
        return f"The dealer busts with {dealer_total}. You win."
    if outcome == "win":
        return f"Your {player_total} beats the dealer's {dealer_total}. You win."
    if outcome == "lose":
        return f"The dealer's {dealer_total} beats your {player_total}. You lose."
    if outcome == "tie":
        if venue == "inn":
            return "A tie — the house keeps half your stake."
        return "Push — your stake comes back."
    return "The hand is settled."


def _attempt_blackjack_cheat(player, venue, stake, player_cards):
    """Return True when the hand is over (caught); False when it continues."""
    ok, message = casino.begin_blackjack_cheat(player, venue)
    if not ok:
        term.print(message)
        term.pause()
        return False

    result = casino.resolve_cheat(player, venue, stake)
    term.print("")
    term.print(
        f"DEX+CHA check: d20({result['roll']}) + {result['stat']} "
        f"vs DC {result['dc']} — {result['chance']:.0%} chance."
    )
    if result["success"]:
        removed = player_cards.pop()
        casino.record_cheat_success(player)
        term.print(
            f"You palm the {casino.format_cards([removed])} off your hand."
        )
        term.print(f"Your hand: {casino.hand_description(player_cards)}")
        term.sleep(0.25)
        return False

    term.print("The dealer catches your wrist. The room goes quiet.")
    settled = casino.finish_blackjack_cheat(player, venue, stake)
    _print_settlement(player, venue, stake, settled)
    if settled.get("karma_lost"):
        term.print(f"Karma {settled['karma_lost']:+d}.")
    term.print(
        f"The back room is closed to you for "
        f"{settled.get('days_left', 0)} days."
    )
    term.pause()
    advance_time(player, casino.MINUTES_PER_HAND)
    return True


def _play_blackjack(player, venue, stake):
    ok, message = casino.begin_hand(player, venue, stake)
    if not ok:
        term.print(message)
        term.pause()
        return

    deck, player_cards, dealer_cards = casino.deal_blackjack()

    term.clear()
    term.print("=== BLACKJACK ===")
    term.print(f"Stake: {stake:,}g")
    term.print(f"Your hand: {casino.hand_description(player_cards)}")
    term.print(f"Dealer shows: {casino.format_cards([dealer_cards[0]])}  ?")

    while True:
        total = casino.hand_value(player_cards)
        if total == 21:
            break

        cheat_available = (
            venue == "black_market"
            and casino.cheats_remaining(player) > 0
            and len(player_cards) > 1
        )
        cheat_label = ""
        if cheat_available:
            chance = casino.cheat_chance(player, stake)[0]
            last_card = casino.format_cards([player_cards[-1]])
            cheat_label = f"Cheat — remove {last_card} ({chance:.0%})"

        if total > 21:
            if not cheat_available:
                break
            choice = term.menu(
                [cheat_label, "Accept the bust"],
                prompt="Bust. Cheat to remove the latest card?",
                columns=2,
            )
            if choice == 0:
                if _attempt_blackjack_cheat(player, venue, stake, player_cards):
                    return
                continue
            break

        options = ["Hit", "Stand"]
        if cheat_available:
            options.append(cheat_label)
        prompt = f"Your total: {total}."
        prompt += " Hit, stand, or cheat?" if cheat_available else " Hit or stand?"
        choice = term.menu(options, prompt=prompt, columns=2)
        if choice == 0:
            player_cards.append(deck.pop())
            term.print(f"You draw: {casino.format_cards([player_cards[-1]])}")
            term.print(f"Your hand: {casino.hand_description(player_cards)}")
            continue
        if choice == 1:
            break
        if cheat_available and choice == 2:
            if _attempt_blackjack_cheat(player, venue, stake, player_cards):
                return
            continue
        break

    player_total = casino.hand_value(player_cards)
    if player_total <= 21:
        term.print(f"Dealer reveals: {casino.hand_description(dealer_cards)}")
        while casino.dealer_should_hit(dealer_cards):
            dealer_cards.append(deck.pop())
            term.print(f"Dealer hits: {casino.format_cards([dealer_cards[-1]])}")
            term.print(f"Dealer hand: {casino.hand_description(dealer_cards)}")
            term.sleep(0.25)
        if casino.hand_value(dealer_cards) > 21:
            term.print("Dealer busts.")
        else:
            term.print("Dealer stands.")

    result = casino.resolve_blackjack(stake, player_cards, dealer_cards, venue)
    settled = casino.finish_hand(player, venue, stake, result["payout"])

    term.print("")
    term.print(
        _blackjack_result_text(
            result["outcome"], result["player_total"],
            result["dealer_total"], venue,
        )
    )
    _print_settlement(player, venue, stake, settled)
    term.pause()
    advance_time(player, casino.MINUTES_PER_HAND)


# ── Menus ───────────────────────────────────────────────────────────────────

def tavern_games_menu(player, city_id="solmere"):
    """Inn tables — always open, no Karma gate."""
    casino.ensure_state(player)
    first = True
    while True:
        casino.reset_daily(player)
        _header(
            player,
            "THE TAVERN TABLES",
            "A scarred board, a worn deck, and a house smile that never reaches the eyes.",
        )
        if first:
            service_dialogue(city_id, "games", "enter")
            first = False

        if casino.hands_remaining(player) <= 0:
            term.print("You've had enough hands for one day.")
            term.pause()
            return
        if casino.is_closed(player, "inn"):
            term.print("The house has closed this table for today. Come back tomorrow.")
            term.pause()
            return

        choice = term.menu(
            [
                "Under & Over (2d6)",
                "Blackjack (Hit or Stand)",
                "House rules",
                "Leave",
            ],
            prompt="What will it be?",
            columns=2,
        )
        if choice == 0:
            _play_game(player, "inn", "under_over")
        elif choice == 1:
            _play_game(player, "inn", "blackjack")
        elif choice == 2:
            _show_house_rules("inn")
        else:
            service_dialogue(city_id, "games", "leave")
            return


def print_back_room_refusal(player, status=None):
    """Explain why the back room is closed to this player."""
    status = status or casino.back_room_status(player)
    if status.get("ok"):
        term.print("The dealer nods you toward the back.")
        return
    reason = status.get("reason")
    if reason == "blacklisted":
        days = int(status.get("days_left", 0) or 0)
        suffix = "day" if days == 1 else "days"
        term.print(
            f"The dealer taps a chalk mark beside the door. "
            f"'Not for you. Not for {days} more {suffix}.'"
        )
    elif reason == "karma":
        term.print(
            "The dealer looks you over. 'The back room is for people the "
            "watch doesn't like. Come back when you've done something "
            "worth regretting.'"
        )
    elif reason == "level":
        term.print(
            "The dealer looks you over. 'Not yet. Come back when you've "
            "learned which end of a knife to hold.'"
        )
    else:
        term.print("The dealer shakes their head and turns away.")


def back_room_menu(player, city_id):
    """Black Market back room — night only, negative Karma, level 5+."""
    first = True
    while True:
        status = casino.back_room_status(player)
        if not status.get("ok"):
            if first:
                print_back_room_refusal(player, status)
                term.pause()
            return

        casino.reset_daily(player)
        _header(
            player,
            "THE BACK ROOM",
            "The dealer's smile doesn't reach the eyes. The dice are bone.",
        )
        if first:
            service_dialogue(city_id, "back_room", "enter")
            term.print(f'  "{_dealer_line(player)}"')
            first = False

        if not time_blocks.is_service_open(player, "black_market", city_id):
            term.print(
                "Dawn light seeps under the door. The dealer starts "
                "stacking the chips."
            )
            term.pause()
            return
        if casino.hands_remaining(player) <= 0:
            term.print("You've had enough hands for one day. The dealer waves you off.")
            term.pause()
            return
        if casino.is_closed(player, "black_market"):
            term.print("The house has closed this table for the day.")
            term.pause()
            return

        choice = term.menu(
            [
                "Under & Over (2d6)",
                "Blackjack (Hit or Stand)",
                "House rules",
                "Leave",
            ],
            prompt="What will it be?",
            columns=2,
        )
        if choice == 0:
            _play_game(player, "black_market", "under_over")
        elif choice == 1:
            _play_game(player, "black_market", "blackjack")
        elif choice == 2:
            _show_house_rules("black_market")
        else:
            service_dialogue(city_id, "back_room", "leave")
            return
