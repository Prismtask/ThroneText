"""Diagnostic: casino / tavern games Phases 1–3 (docs/casino_games_design.md).

Covers:
  * save-state defaults and daily resets
  * stake / level / Karma / blacklist gates
  * Karma-off fallback
  * hand lifecycle, hand limits, pot caps, daily net caps
  * Under & Over RTP (including the exact-7 pot-limit rule)
  * Blackjack rules, suited card display, hand values, and RTP
  * Under & Over and Blackjack cheating, caught-only Karma, 7-day blacklist
  * casino title backfill/unlocks, record lines, payouts, and RTP caps

Run:
    .venv\\Scripts\\python.exe tests/_diag_casino.py
"""
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# Suit symbols (♠ ♥ ♦ ♣) need UTF-8 even on Windows consoles.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import casino
from city_dialogue import get_city_dialogues
from facilities import casino_ui

failures = []


def check(label, got, expected):
    ok = got == expected
    print(f"  {'OK  ' if ok else 'FAIL'} {label}: got {got}, expected {expected}")
    if not ok:
        failures.append(label)


def check_close(label, got, expected, tolerance=0.01):
    ok = abs(got - expected) <= tolerance
    print(
        f"  {'OK  ' if ok else 'FAIL'} {label}: got {got:.4f}, "
        f"expected {expected:.4f} +/- {tolerance:.4f}"
    )
    if not ok:
        failures.append(label)


def make_player(level=10, karma=0, karma_enabled=True, gold=100_000, day=1):
    return {
        "name": "Tester",
        "level": level,
        "karma": karma,
        "karma_enabled": karma_enabled,
        "gold": gold,
        "day": day,
        "current_hp": 100,
        "attributes": {
            "Strength": 5, "Constitution": 5, "Dexterity": 10,
            "Learning": 5, "Wisdom": 5, "Charisma": 10,
        },
        "passive_unlocked": False,
        "equipped": {},
    }


class FixedRng:
    def __init__(self, roll):
        self.roll = roll

    def randint(self, _a, _b):
        return self.roll


def sim_under_over(venue, stake, bet, trials=100_000, seed=11, player=None):
    rng = random.Random(seed)
    total = 0
    for _ in range(trials):
        total += casino.simulate_under_over(venue, stake, bet, rng, player)
    return total / (trials * stake)


def sim_blackjack(venue, stake, trials=30_000, seed=22, player=None):
    rng = random.Random(seed)
    total = 0
    for _ in range(trials):
        total += casino.simulate_blackjack(
            venue, stake, casino.basic_policy, rng, player
        )
    return total / (trials * stake)


print("=== CASINO STATE & DAILY RESET ===")
player = make_player(day=2)
state = casino.ensure_state(player)
check("default hands_today", state["hands_today"], 0)
check("default hands_played", state["hands_played"], 0)
check("default net inn", state["net"]["inn"], 0)
check("default net black_market", state["net"]["black_market"], 0)
check("default closed inn", state["closed"]["inn"], False)
check("default cheats_unseen", state["cheats_unseen"], 0)
check("default cheats_caught", state["cheats_caught"], 0)

state["day"] = 1
state["hands_today"] = 12
state["cheats_today"] = 2
state["net"]["inn"] = 500
state["closed"]["inn"] = True
casino.reset_daily(player)
check("reset day", state["day"], 2)
check("reset hands_today", state["hands_today"], 0)
check("reset cheats_today", state["cheats_today"], 0)
check("reset net inn", state["net"]["inn"], 0)
check("reset closed inn", state["closed"]["inn"], False)

bad = {"casino": []}
casino.ensure_state(bad)
check("heal malformed state", isinstance(bad["casino"], dict), True)

print("\n=== STAKE / LEVEL / KARMA GATES ===")
player = make_player(level=1, karma=0, karma_enabled=True)
allowed, _ = casino.stake_allowed(player, "inn", 25)
check("inn 25 at L1", allowed, True)
allowed, _ = casino.stake_allowed(player, "inn", 100)
check("inn 100 at L1", allowed, False)
player["level"] = 5
allowed, _ = casino.stake_allowed(player, "inn", 100)
check("inn 100 at L5", allowed, True)
player["level"] = 10
allowed, _ = casino.stake_allowed(player, "inn", 250)
check("inn 250 at L10", allowed, True)

player = make_player(level=5, karma=-1, karma_enabled=True)
allowed, _ = casino.stake_allowed(player, "black_market", 250)
check("back room 250 at Karma -1", allowed, True)
allowed, _ = casino.stake_allowed(player, "black_market", 1_000)
check("back room 1000 at L5", allowed, False)
player["level"] = 15
player["karma"] = -15
allowed, _ = casino.stake_allowed(player, "black_market", 1_000)
check("back room 1000 at Karma -15", allowed, True)
player["karma"] = -14
allowed, _ = casino.stake_allowed(player, "black_market", 1_000)
check("back room 1000 at Karma -14", allowed, False)
player["level"] = 25
player["karma"] = -40
allowed, _ = casino.stake_allowed(player, "black_market", 2_500)
check("back room 2500 at Karma -40", allowed, True)
player["karma"] = -39
allowed, _ = casino.stake_allowed(player, "black_market", 2_500)
check("back room 2500 at Karma -39", allowed, False)

player = make_player(level=15, karma=50, karma_enabled=False)
allowed, _ = casino.stake_allowed(player, "black_market", 1_000)
check("Karma off, 1000 at L15", allowed, True)
allowed, _ = casino.stake_allowed(player, "black_market", 2_500)
check("Karma off, 2500 at L15", allowed, False)

print("\n=== BACK-ROOM STATUS ===")
player = make_player(level=5, karma=0, karma_enabled=True)
check("Karma 0 refused", casino.back_room_status(player)["reason"], "karma")
player["karma"] = -1
check("Karma -1 opens", casino.back_room_status(player)["ok"], True)
player["level"] = 4
check("L4 refused", casino.back_room_status(player)["reason"], "level")
player["level"] = 5
state = casino.ensure_state(player)
state["ban_until_day"] = player["day"] + 3
check("blacklisted", casino.back_room_status(player)["reason"], "blacklisted")
check("blacklist days", casino.back_room_status(player)["days_left"], 3)
player["karma_enabled"] = False
player["karma"] = 50
state["ban_until_day"] = 0
check("Karma off opens", casino.back_room_status(player)["ok"], True)

print("\n=== HAND LIFECYCLE & CAPS ===")
player = make_player(level=10, karma=0, karma_enabled=True, gold=1_000, day=1)
ok, message = casino.begin_hand(player, "inn", 250)
check("begin ok", ok, True)
check("begin message", message, "")
check("gold after stake", player["gold"], 750)
check("hands_today after begin", player["casino"]["hands_today"], 1)

settled = casino.finish_hand(player, "inn", 250, 550.0)
check("win gold", player["gold"], 1_300)
check("win net", settled["net"], 300)
check("win net counter", player["casino"]["net"]["inn"], 300)
check("win hands_won", player["casino"]["hands_won"], 1)
check("win biggest_win", player["casino"]["biggest_win"], 300)
check("title hands_won", player["title_stats"]["casino_hands_won"], 1)
check("title biggest_win", player["title_stats"]["casino_biggest_win"], 300)

ok, _ = casino.begin_hand(player, "inn", 25)
check("loss stake", player["gold"], 1_275)
settled = casino.finish_hand(player, "inn", 25, 0)
check("loss gold", player["gold"], 1_275)
check("loss net", settled["net"], -25)
check("loss not a win", settled["won"], False)

ok, _ = casino.begin_hand(player, "inn", 25)
check("push stake", player["gold"], 1_250)
settled = casino.finish_hand(player, "inn", 25, 25)
check("push gold", player["gold"], 1_275)
check("push net", settled["net"], 0)
check("push not a win", settled["won"], False)

payout, capped = casino.finalize_payout(None, "inn", 99_999)
check("inn pot cap", payout, 1_000)
check("inn pot capped", capped, True)
payout, capped = casino.finalize_payout(None, "black_market", 99_999)
check("back room pot cap", payout, 10_000)
check("back room pot capped", capped, True)

check("exact-7 inn 250", casino.exact_seven_allowed("inn", 250), False)
check("exact-7 inn 100", casino.exact_seven_allowed("inn", 100), True)
check("exact-7 back room 2500", casino.exact_seven_allowed("black_market", 2_500), False)
check("exact-7 back room 1000", casino.exact_seven_allowed("black_market", 1_000), True)

player = make_player(level=10, gold=10_000, day=5)
state = casino.ensure_state(player)
state["day"] = 5
state["hands_today"] = 12
ok, _ = casino.begin_hand(player, "inn", 25)
check("daily hand limit", ok, False)

player = make_player(level=10, gold=10_000, day=6)
state = casino.ensure_state(player)
state["day"] = 6
state["net"]["inn"] = 999
state["closed"]["inn"] = False
state["hands_today"] = 0
ok, _ = casino.begin_hand(player, "inn", 25)
check("net-cap begin", ok, True)
settled = casino.finish_hand(player, "inn", 25, 55)
check("net-cap closed", settled["closed"], True)
check("net-cap state", state["closed"]["inn"], True)

player = make_player(level=10, gold=10, day=7)
state = casino.ensure_state(player)
state["day"] = 7
state["hands_today"] = 0
ok, _ = casino.begin_hand(player, "inn", 25)
check("cannot bet more than gold", ok, False)
check("gold unchanged", player["gold"], 10)

print("\n=== BLACKJACK RULES ===")
check("A+7 value", casino.hand_value([14, 7]), 18)
check("A+7 soft", casino.is_soft([14, 7]), True)
check("A+A value", casino.hand_value([14, 14]), 12)
check("A+A soft", casino.is_soft([14, 14]), True)
check("A+5+6 value", casino.hand_value([14, 5, 6]), 12)
check("A+5+6 hard", casino.is_soft([14, 5, 6]), False)
check("K+Q value", casino.hand_value([13, 12]), 20)
check("A+K value", casino.hand_value([14, 13]), 21)
check("A+K soft", casino.is_soft([14, 13]), True)
check("format cards", casino.format_cards([14, 10, 11]), "A 10 J")
check("format suited cards",
      casino.format_cards([(14, "♠"), (10, "♥"), (11, "♦")]), "A♠ 10♥ J♦")
check("suited A+7 value", casino.hand_value([(14, "♠"), (7, "♥")]), 18)

deck = casino.make_deck(random.Random(1))
check("deck size", len(deck), 52)
check("deck aces", sum(1 for card in deck if card[0] == 14), 4)
check("deck suits", len({card[1] for card in deck}), 4)

check("basic hard 12 vs 3", casino.basic_policy([10, 2], 3), "hit")
check("basic hard 12 vs 6", casino.basic_policy([10, 2], 6), "stand")
check("basic hard 12 vs 7", casino.basic_policy([10, 2], 7), "hit")
check("basic hard 17", casino.basic_policy([10, 7], 10), "stand")
check("basic soft 18 vs 8", casino.basic_policy([14, 7], 8), "stand")
check("basic soft 18 vs 9", casino.basic_policy([14, 7], 9), "hit")

result = casino.resolve_blackjack(100, [14, 13], [10, 7], "inn")
check("natural outcome", result["outcome"], "natural")
check("natural payout", round(result["payout"], 2), 220.0)
result = casino.resolve_blackjack(100, [14, 13], [14, 13], "inn")
check("two naturals outcome", result["outcome"], "tie")
check("two naturals payout", result["payout"], 50.0)
result = casino.resolve_blackjack(100, [10, 7], [14, 13], "inn")
check("dealer natural outcome", result["outcome"], "dealer_natural")
result = casino.resolve_blackjack(100, [10, 9], [10, 6, 10], "inn")
check("dealer bust outcome", result["outcome"], "dealer_bust")
result = casino.resolve_blackjack(100, [10, 8], [10, 8], "inn")
check("inn tie outcome", result["outcome"], "tie")
check("inn tie payout", result["payout"], 50.0)
result = casino.resolve_blackjack(100, [10, 8], [10, 8], "black_market")
check("back room tie payout", result["payout"], 100.0)

print("\n=== CHEAT CHECK & PENALTIES ===")
player = make_player(level=5, karma=-1, gold=10_000, day=10)
casino.ensure_state(player)
chance, stat, dc = casino.cheat_chance(player, 250)
check("cheat stat", stat, 10)
check("cheat 250 chance", round(chance, 2), 0.70)
check("cheat 250 dc (capped)", dc, 17)
chance, stat, dc = casino.cheat_chance(player, 1_000)
check("cheat 1000 chance", round(chance, 2), 0.65)
check("cheat 1000 dc", dc, 18)
chance, stat, dc = casino.cheat_chance(player, 2_500)
check("cheat 2500 chance", round(chance, 2), 0.55)
check("cheat 2500 dc", dc, 20)

ok, _ = casino.begin_cheat(player, "inn", 25)
check("cheat rejected at inn", ok, False)
ok, _ = casino.begin_cheat(player, "black_market", 250)
check("cheat begin 1", ok, True)
check("cheat attempts 1", player["casino"]["cheats_today"], 1)
check("cheat gold after stake", player["gold"], 9_750)
result = casino.resolve_cheat(player, "black_market", 250, FixedRng(20))
check("cheat roll success", result["success"], True)
settled = casino.finish_cheat(player, "black_market", 250, result)
check("cheat payout", settled["payout"], 325)
check("cheat net", settled["net"], 75)
check("cheat unseen", player["casino"]["cheats_unseen"], 1)
check("cheat caught", player["casino"]["cheats_caught"], 0)
check("cheat title unseen", player["title_stats"]["casino_cheats_unseen"], 1)
check("cheat no karma loss", settled["karma_lost"], 0)
check("cheat no blacklist", player["casino"]["ban_until_day"], 0)

ok, _ = casino.begin_cheat(player, "black_market", 250)
check("cheat begin 2", ok, True)
check("cheat attempts 2", player["casino"]["cheats_today"], 2)
result = casino.resolve_cheat(player, "black_market", 250, FixedRng(1))
check("cheat roll caught", result["success"], False)
karma_before = player["karma"]
settled = casino.finish_cheat(player, "black_market", 250, result)
check("cheat caught counter", player["casino"]["cheats_caught"], 1)
check("cheat caught title", player["title_stats"]["casino_cheats_caught"], 1)
check("cheat caught payout", settled["payout"], 0)
check("cheat caught net", settled["net"], -250)
check("cheat caught karma", player["karma"], karma_before - 2)
check("cheat caught days", settled["days_left"], 7)
check("cheat ban_until", player["casino"]["ban_until_day"], 17)
check("cheat caught journal",
      any(e.get("tag") == "[CASINO]" for e in player["journal"]["events"]), True)
ok, _ = casino.begin_cheat(player, "black_market", 250)
check("cheat after caught refused", ok, False)

player = make_player(level=5, karma=-1, gold=10_000, day=10)
casino.ensure_state(player)
for _ in range(2):
    ok, _ = casino.begin_cheat(player, "black_market", 250)
    check("cheat two attempts begin", ok, True)
    result = casino.resolve_cheat(player, "black_market", 250, FixedRng(20))
    casino.finish_cheat(player, "black_market", 250, result)
ok, _ = casino.begin_cheat(player, "black_market", 250)
check("cheat daily limit", ok, False)

player = make_player(level=5, karma=50, karma_enabled=False, gold=10_000, day=10)
casino.ensure_state(player)
ok, _ = casino.begin_cheat(player, "black_market", 250)
check("cheat karma-off begin", ok, True)
result = casino.resolve_cheat(player, "black_market", 250, FixedRng(1))
settled = casino.finish_cheat(player, "black_market", 250, result)
check("cheat karma-off no karma", settled["karma_lost"], 0)
check("cheat karma-off blacklist", player["casino"]["ban_until_day"], 17)

player = make_player(level=5, karma=-1, gold=1_000, day=10)
casino.ensure_state(player)
ok, _ = casino.begin_hand(player, "black_market", 250)
check("blackjack cheat hand begin", ok, True)
check("blackjack cheat gold after stake", player["gold"], 750)
ok, _ = casino.begin_blackjack_cheat(player, "inn")
check("blackjack cheat rejected at inn", ok, False)
ok, _ = casino.begin_blackjack_cheat(player, "black_market")
check("blackjack cheat begin", ok, True)
check("blackjack cheat attempts", player["casino"]["cheats_today"], 1)
check("blackjack cheat no extra stake", player["gold"], 750)
check("blackjack cheat no extra hand", player["casino"]["hands_played"], 1)
casino.record_cheat_success(player)
check("blackjack cheat unseen", player["casino"]["cheats_unseen"], 1)
check("blackjack cheat title unseen",
      player["title_stats"]["casino_cheats_unseen"], 1)
ok, _ = casino.begin_blackjack_cheat(player, "black_market")
check("blackjack cheat second begin", ok, True)
check("blackjack cheat attempts 2", player["casino"]["cheats_today"], 2)
karma_before = player["karma"]
settled = casino.finish_blackjack_cheat(player, "black_market", 250)
check("blackjack cheat caught", settled["caught"], True)
check("blackjack cheat caught payout", settled["payout"], 0)
check("blackjack cheat caught net", settled["net"], -250)
check("blackjack cheat caught karma", player["karma"], karma_before - 2)
check("blackjack cheat caught days", settled["days_left"], 7)
check("blackjack cheat caught ban", player["casino"]["ban_until_day"], 17)
check("blackjack cheat caught counter", player["casino"]["cheats_caught"], 1)

print("\n=== UNDER & OVER RTP ===")
check_close("inn under 250 RTP", sim_under_over("inn", 250, "under"), 0.9167)
check_close("inn over 250 RTP", sim_under_over("inn", 250, "over"), 0.9167)
check_close("inn exact-7 100 RTP", sim_under_over("inn", 100, "seven"), 0.9167)
check_close("back room under 2500 RTP", sim_under_over("black_market", 2_500, "under"), 0.9583)
check_close("back room over 2500 RTP", sim_under_over("black_market", 2_500, "over"), 0.9583)
check_close("back room exact-7 1000 RTP", sim_under_over("black_market", 1_000, "seven"), 0.9583)

print("\n=== BLACKJACK RTP ===")
inn_rtp = sim_blackjack("inn", 250)
print(f"  INFO blackjack inn RTP: {inn_rtp:.4f} (target 0.90-0.93)")
check("blackjack inn band", 0.90 <= inn_rtp <= 0.93, True)
back_rtp = sim_blackjack("black_market", 2_500)
print(f"  INFO blackjack back-room RTP: {back_rtp:.4f} (target 0.94-0.97)")
check("blackjack back-room band", 0.94 <= back_rtp <= 0.97, True)

print("\n=== CASINO TITLES (PHASE 3) ===")
import titles
from resources.titles import TITLES_BY_ID

# Old-save backfill: lifetime casino stats -> title_stats -> unlocks.
old = make_player(level=10, gold=10_000, day=1)
old["casino"] = {
    "hands_won": 100,
    "biggest_win": 4_750,
    "cheats_unseen": 10,
    "cheats_caught": 3,
}
old["title_stats"] = {}
casino.ensure_state(old)
check("title backfill hands", old["title_stats"]["casino_hands_won"], 100)
check("title backfill biggest", old["title_stats"]["casino_biggest_win"], 4_750)
check("title backfill unseen", old["title_stats"]["casino_cheats_unseen"], 10)
check("title backfill caught", old["title_stats"]["casino_cheats_caught"], 3)
titles.check_unlock(old)
for _tid in ("the_gambler", "sleight_hand", "marked"):
    check(f"{_tid} backfill unlock", _tid in old["titles_unlocked"], True)

# The Gambler: 100 hands OR a 4,000g biggest net win.
big_win = make_player(level=10, gold=10_000, day=1)
big_win["title_stats"] = {"casino_hands_won": 0, "casino_biggest_win": 4_000}
titles.check_unlock(big_win)
check("gambler biggest-win branch", "the_gambler" in big_win["titles_unlocked"], True)

# Payout effect: +1% of the stake on wins, never on pushes.
gambler = make_player(level=10, gold=10_000, day=1)
gambler["titles_unlocked"] = {"the_gambler": {"day": 1, "seen": True}}
gambler["title_active"] = "the_gambler"
check("gambler win bonus", casino.finalize_payout(gambler, "inn", 220, 100),
      (221, False))
check("gambler low-stake minimum",
      casino.finalize_payout(gambler, "inn", 55, 25), (56, False))
check("gambler push unchanged",
      casino.finalize_payout(gambler, "inn", 100, 100), (100, False))
check("gambler pot cap",
      casino.finalize_payout(gambler, "inn", 1_000, 100), (1_000, True))
check("gambler effect line",
      "casino payouts" in titles.format_effect_line(TITLES_BY_ID["the_gambler"]),
      True)

# Black Market titles, including Marked's visible shop drawback.
check("unrepentant effect line has no phantom shop bonus",
      "shop discount" not in titles.format_effect_line(
          TITLES_BY_ID["unrepentant"]), True)
marked = make_player(level=10, gold=10_000, day=1)
marked["titles_unlocked"] = {"marked": {"day": 1, "seen": True}}
marked["title_active"] = "marked"
check("marked black market mod",
      round(titles.mod(marked, "black_market_pct"), 4), 0.05)
check("marked shop drawback",
      round(titles.mod(marked, "shop_discount_pct"), 4), -0.05)
check("marked effect line",
      "drawback" in titles.format_effect_line(TITLES_BY_ID["marked"]), True)

from facilities.black_market import _karma_price
sleight = make_player(level=10, gold=10_000, day=1, karma_enabled=False)
sleight["titles_unlocked"] = {"sleight_hand": {"day": 1, "seen": True}}
sleight["title_active"] = "sleight_hand"
check("sleight black market mod",
      round(titles.mod(sleight, "black_market_pct"), 4), 0.03)
check("black market title works with Karma off",
      _karma_price(sleight, 1_000), 970)

# Casino actions trigger the unlock check immediately.
finish = make_player(level=10, gold=10_000, day=1)
finish["casino"] = {"hands_won": 99, "biggest_win": 0}
finish["title_stats"] = {"casino_hands_won": 99}
finish["titles_unlocked"] = {}
finish["title_active"] = None
ok, _ = casino.begin_hand(finish, "inn", 25)
check("title finish hand begin", ok, True)
casino.finish_hand(finish, "inn", 25, 50)
check("finish hand unlocks gambler",
      "the_gambler" in finish["titles_unlocked"], True)

cheat = make_player(level=10, gold=10_000, day=1)
cheat["casino"] = {"cheats_unseen": 9}
cheat["title_stats"] = {"casino_cheats_unseen": 9}
cheat["titles_unlocked"] = {}
casino.record_cheat_success(cheat)
check("unseen cheat unlocks sleight hand",
      "sleight_hand" in cheat["titles_unlocked"], True)
caught = make_player(level=10, gold=10_000, day=1)
caught["casino"] = {"cheats_caught": 2}
caught["title_stats"] = {"casino_cheats_caught": 2}
caught["titles_unlocked"] = {}
casino._record_cheat(caught, False)
check("caught cheat unlocks marked", "marked" in caught["titles_unlocked"], True)

# The shared record line is shown for locked and unlocked cards.
rows = titles.list_titles(old)
gambler_row = next(r for r in rows if r["id"] == "the_gambler")
check("gambler record line", "Hands won: 100" in gambler_row["record_line"], True)
check("gambler biggest record", "4,750g" in gambler_row["record_line"], True)
locked = make_player(level=10, gold=10_000, day=1)
titles.ensure_state(locked)
locked_row = next(r for r in titles.list_titles(locked) if r["id"] == "the_gambler")
check("locked record line", "Hands won: 0" in locked_row["record_line"], True)

# The Gambler's +1% must keep the back room inside the 97% RTP guardrail.
gambler_uo = sim_under_over("black_market", 2_500, "under", player=gambler)
gambler_bj = sim_blackjack("black_market", 2_500, player=gambler)
print(f"  INFO gambler back-room UO RTP: {gambler_uo:.4f}")
print(f"  INFO gambler back-room blackjack RTP: {gambler_bj:.4f}")
check("gambler UO above base", gambler_uo > 0.9583, True)
check("gambler UO RTP cap", gambler_uo <= 0.97, True)
check("gambler blackjack above base", gambler_bj > back_rtp, True)
check("gambler blackjack RTP cap", gambler_bj <= 0.97, True)

print("\n=== CASINO DIALOGUE FALLBACKS ===")
check("Solmere games dialogue",
      bool(get_city_dialogues("solmere", "games").get("enter")), True)
check("Generic games dialogue",
      bool(get_city_dialogues("stormhold", "games").get("enter")), True)
check("Ashkara back-room dialogue",
      bool(get_city_dialogues("ashkara", "back_room").get("enter")), True)
check("Blackwake games dialogue",
      bool(get_city_dialogues("blackwake", "games").get("enter")), True)
check("Blackwake back-room dialogue",
      bool(get_city_dialogues("blackwake", "back_room").get("enter")), True)

print("\n=== UI SMOKE TEST (FAKE TERMINAL) ===")


class FakeTerm:
    def __init__(self, choices):
        self.choices = list(choices)
        self.outputs = []
        self.menus = []

    def clear(self):
        self.outputs.append("<clear>")

    def print(self, *args, **kwargs):
        self.outputs.append(" ".join(str(a) for a in args))

    def pause(self, prompt="Press Continue..."):
        self.outputs.append(f"<pause:{prompt}>")

    def sleep(self, seconds=0.5):
        pass

    def menu(self, options, prompt="Choose an option:", **kwargs):
        self.menus.append((prompt, list(options)))
        if not self.choices:
            return -1
        return self.choices.pop(0)


original_term = casino_ui.term
original_advance = casino_ui.advance_time
original_service_dialogue = casino_ui.service_dialogue
casino_ui.service_dialogue = lambda *args, **kwargs: None
try:
    fake = FakeTerm([0, 0, 0, 3])  # game, 25g stake, Under 7, Leave
    casino_ui.term = fake
    advances = []
    casino_ui.advance_time = lambda p, m: advances.append(m)
    player = make_player(level=10, gold=1_000, day=1)
    casino.ensure_state(player)
    casino_ui.tavern_games_menu(player)
    check("inn UI hand played", player["casino"]["hands_played"], 1)
    check("inn UI hands today", player["casino"]["hands_today"], 1)
    check("inn UI time advanced", advances, [casino.MINUTES_PER_HAND])
    check("inn UI first menu has Under & Over",
          any("Under & Over" in label for _prompt, opts in fake.menus for label in opts),
          True)

    original_deal = casino.deal_blackjack
    try:
        # Fixed hand: player 17, dealer 16 -> dealer must hit 5 and stand on 21.
        casino.deal_blackjack = lambda: (
            [(5, "♣")],
            [(10, "♠"), (7, "♥")],
            [(10, "♦"), (6, "♣")],
        )
        fake = FakeTerm([1, 0, 1, 3])  # Blackjack, 25g, Stand, Leave
        casino_ui.term = fake
        advances = []
        casino_ui.advance_time = lambda p, m: advances.append(m)
        player = make_player(level=10, gold=1_000, day=1)
        casino.ensure_state(player)
        casino_ui.tavern_games_menu(player)
        check("inn blackjack UI hand played", player["casino"]["hands_played"], 1)
        check("inn blackjack UI time advanced", advances, [casino.MINUTES_PER_HAND])
        check("inn blackjack hides hole card",
              any("Dealer shows" in line and "?" in line for line in fake.outputs), True)
        check("inn blackjack reveals dealer",
              any("Dealer reveals" in line for line in fake.outputs), True)
        check("inn blackjack shows dealer hit",
              any("Dealer hits" in line for line in fake.outputs), True)
    finally:
        casino.deal_blackjack = original_deal

    fake = FakeTerm([0, 0, 0, 3])  # game, 250g stake, Under 7, Leave
    casino_ui.term = fake
    advances = []
    casino_ui.advance_time = lambda p, m: advances.append(m)
    player = make_player(level=5, karma=-1, gold=1_000, day=1)
    player["day_blocks"] = 18  # night
    casino.ensure_state(player)
    casino_ui.back_room_menu(player, "ashkara")
    check("back-room UI hand played", player["casino"]["hands_played"], 1)
    check("back-room UI hands today", player["casino"]["hands_today"], 1)
    check("back-room UI time advanced", advances, [casino.MINUTES_PER_HAND])

    original_deal = casino.deal_blackjack
    original_resolve_cheat = casino.resolve_cheat
    try:
        # Player 16 vs dealer 19. Cheat removes 6♥, then the player stands at 10.
        casino.deal_blackjack = lambda: (
            [(5, "♣")],
            [(10, "♠"), (6, "♥")],
            [(10, "♦"), (9, "♣")],
        )
        casino.resolve_cheat = lambda p, v, s: {
            "success": True, "roll": 20, "stat": 10, "dc": 17,
            "chance": 0.70, "payout": 0.0,
        }
        fake = FakeTerm([1, 0, 2, 1, 3])  # Blackjack, 250g, Cheat, Stand, Leave
        casino_ui.term = fake
        advances = []
        casino_ui.advance_time = lambda p, m: advances.append(m)
        player = make_player(level=5, karma=-1, gold=1_000, day=1)
        player["day_blocks"] = 18
        casino.ensure_state(player)
        casino_ui.back_room_menu(player, "ashkara")
        check("blackjack cheat UI attempts", player["casino"]["cheats_today"], 1)
        check("blackjack cheat UI unseen", player["casino"]["cheats_unseen"], 1)
        check("blackjack cheat UI hand played", player["casino"]["hands_played"], 1)
        check("blackjack cheat UI time", advances, [casino.MINUTES_PER_HAND])
        check("blackjack cheat UI removed card",
              any("palm the 6♥" in line for line in fake.outputs), True)
    finally:
        casino.deal_blackjack = original_deal
        casino.resolve_cheat = original_resolve_cheat

    original_deal = casino.deal_blackjack
    original_resolve_cheat = casino.resolve_cheat
    try:
        # Player hits into a bust, then cheats away the busting card.
        casino.deal_blackjack = lambda: (
            [(10, "♣")],
            [(10, "♠"), (6, "♥")],
            [(10, "♦"), (9, "♣")],
        )
        casino.resolve_cheat = lambda p, v, s: {
            "success": True, "roll": 20, "stat": 10, "dc": 17,
            "chance": 0.70, "payout": 0.0,
        }
        fake = FakeTerm([1, 0, 0, 0, 1, 3])  # Blackjack, 250g, Hit, Cheat, Stand, Leave
        casino_ui.term = fake
        advances = []
        casino_ui.advance_time = lambda p, m: advances.append(m)
        player = make_player(level=5, karma=-1, gold=1_000, day=1)
        player["day_blocks"] = 18
        casino.ensure_state(player)
        casino_ui.back_room_menu(player, "ashkara")
        check("blackjack bust cheat attempts", player["casino"]["cheats_today"], 1)
        check("blackjack bust cheat unseen", player["casino"]["cheats_unseen"], 1)
        check("blackjack bust cheat hand played", player["casino"]["hands_played"], 1)
        check("blackjack bust cheat time", advances, [casino.MINUTES_PER_HAND])
        check("blackjack bust cheat removed draw",
              any("palm the 10♣" in line for line in fake.outputs), True)
    finally:
        casino.deal_blackjack = original_deal
        casino.resolve_cheat = original_resolve_cheat

    original_deal = casino.deal_blackjack
    original_resolve_cheat = casino.resolve_cheat
    try:
        casino.deal_blackjack = lambda: (
            [(5, "♣")],
            [(10, "♠"), (6, "♥")],
            [(10, "♦"), (9, "♣")],
        )
        casino.resolve_cheat = lambda p, v, s: {
            "success": False, "roll": 1, "stat": 10, "dc": 17,
            "chance": 0.70, "payout": 0.0,
        }
        fake = FakeTerm([1, 0, 2])  # Blackjack, 250g, Cheat; blacklist ends it
        casino_ui.term = fake
        advances = []
        casino_ui.advance_time = lambda p, m: advances.append(m)
        player = make_player(level=5, karma=-1, gold=1_000, day=1)
        player["day_blocks"] = 18
        casino.ensure_state(player)
        casino_ui.back_room_menu(player, "ashkara")
        check("blackjack caught UI caught", player["casino"]["cheats_caught"], 1)
        check("blackjack caught UI ban", player["casino"]["ban_until_day"], 8)
        check("blackjack caught UI hand played", player["casino"]["hands_played"], 1)
        check("blackjack caught UI message",
              any("closed to you for 7 days" in line for line in fake.outputs), True)
    finally:
        casino.deal_blackjack = original_deal
        casino.resolve_cheat = original_resolve_cheat

    original_resolve_cheat = casino.resolve_cheat
    try:
        casino.resolve_cheat = lambda p, v, s: {
            "success": True, "roll": 20, "stat": 10, "dc": 17,
            "chance": 0.70, "payout": s * casino.CHEAT_PAYOUT,
        }
        fake = FakeTerm([0, 0, 3, 3])  # game, 250g, Cheat, Leave
        casino_ui.term = fake
        advances = []
        casino_ui.advance_time = lambda p, m: advances.append(m)
        player = make_player(level=5, karma=-1, gold=1_000, day=1)
        player["day_blocks"] = 18
        casino.ensure_state(player)
        casino_ui.back_room_menu(player, "ashkara")
        check("back-room cheat UI attempts", player["casino"]["cheats_today"], 1)
        check("back-room cheat UI unseen", player["casino"]["cheats_unseen"], 1)
        check("back-room cheat UI hand played", player["casino"]["hands_played"], 1)
        check("back-room cheat UI time", advances, [casino.MINUTES_PER_HAND])
    finally:
        casino.resolve_cheat = original_resolve_cheat

    original_resolve_cheat = casino.resolve_cheat
    try:
        casino.resolve_cheat = lambda p, v, s: {
            "success": False, "roll": 1, "stat": 10, "dc": 17,
            "chance": 0.70, "payout": 0.0,
        }
        fake = FakeTerm([0, 0, 3])  # game, 250g, Cheat; blacklist ends the menu
        casino_ui.term = fake
        advances = []
        casino_ui.advance_time = lambda p, m: advances.append(m)
        player = make_player(level=5, karma=-1, gold=1_000, day=1)
        player["day_blocks"] = 18
        casino.ensure_state(player)
        casino_ui.back_room_menu(player, "ashkara")
        check("back-room caught UI caught", player["casino"]["cheats_caught"], 1)
        check("back-room caught UI ban", player["casino"]["ban_until_day"], 8)
        check("back-room caught UI hand played", player["casino"]["hands_played"], 1)
        check("back-room caught UI message",
              any("closed to you for 7 days" in line for line in fake.outputs), True)
    finally:
        casino.resolve_cheat = original_resolve_cheat

    fake = FakeTerm([])
    casino_ui.term = fake
    player = make_player(level=10, karma=0, gold=1_000, day=1)
    casino.ensure_state(player)
    casino_ui.back_room_menu(player, "ashkara")
    check("back-room refusal has text",
          any("back room" in line for line in fake.outputs), True)
    check("back-room refusal plays no hand", player["casino"]["hands_played"], 0)
finally:
    casino_ui.term = original_term
    casino_ui.advance_time = original_advance
    casino_ui.service_dialogue = original_service_dialogue

print("\n=== SUMMARY ===")
if failures:
    print(f"{len(failures)} failure(s): {', '.join(failures)}")
    sys.exit(1)
print("All casino diagnostics passed.")
