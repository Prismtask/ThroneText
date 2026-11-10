"""facilities/house/dispatch_board.py — the house Dispatch Board.

Sends housed girls on time-based sweeps and errands. Mission rules and
resolution live in facilities/dispatch.py; this module is the board UI that
launches them from the house.
"""

from events import format_day_delta
from utils import advance_time, display_name
from gui.terminal import term

from .core import _resolve_house


def _dispatch_board(player, city_id, house):
    """Dispatch board (Phase 1) — send housed girls on sweeps and errands.

    Operates on the effective home house (explicit city → origin → first
    owned, via _resolve_house) even if the player opened a secondary house.
    """
    from resources.cities import CITIES
    from facilities.dispatch import (
        ensure_offers, slot_cap, star_cap, refresh_day, get_dispatch_state,
        sanitize_flags, collect_reports, return_time_text,
    )

    home_city, home_house = _resolve_house(player)
    if home_house is None:
        term.print("You don't have a home yet.")
        term.pause()
        return

    sanitize_flags(player, home_house)

    while True:
        term.clear()
        d = get_dispatch_state(player)
        level = int(home_house.get("level", 1))
        active = list(d.get("active", []))
        offers = ensure_offers(player, home_city, home_house)
        city_name = CITIES.get(home_city, {}).get("name", home_city)

        term.print(f"=== DISPATCH BOARD ===  ({city_name})")
        term.print(f"  Slots: {len(active)}/{slot_cap(level)} used · "
                   f"House limit: {'★' * star_cap(level)}")
        for inst in active:
            term.print(f"  Away: {'★' * int(inst.get('stars', 1))} {inst['name']}")
            term.print(f"        Team: {', '.join(inst.get('girl_names', []))} — "
                       f"back {return_time_text(player, inst)}")
        rep_count = len(d.get("reports", []))
        if rep_count:
            term.print(f"  Reports: {rep_count} ready to collect")
        board_day = player.get("day", 1)
        term.print(f"  Offers refresh {format_day_delta(refresh_day(board_day), board_day)} "
                   f"(3-day cycle)")
        if not offers:
            term.print("  No missions left on the board this cycle.")
        term.print()

        options, actions = [], []
        for offer in offers:
            options.append(f"{'★' * offer['stars']} {offer['name']} — {offer['label']}, "
                           f"power {offer['power']}, ~{offer['hours']}h, risk {offer['risk']}")
            actions.append(("offer", offer))
        options.append("View active dispatches")
        actions.append(("view", None))
        if rep_count:
            options.append(f"Collect reports ({rep_count})")
            actions.append(("collect", None))

        idx = term.menu(options, prompt="Choose a mission:", allow_cancel=True,
                        cancel_label="Back", columns=2)
        if idx < 0:
            return
        kind, payload = actions[idx]

        if kind == "offer":
            if len(active) >= slot_cap(level):
                term.print("All dispatch slots are in use — wait for a team to return.")
                term.pause()
                continue
            _dispatch_team_select(player, home_city, home_house, payload)
        elif kind == "view":
            term.clear()
            if not active:
                term.print("No active dispatches.")
            for inst in active:
                term.print(f"{'★' * int(inst.get('stars', 1))} {inst['name']}")
                term.print(f"  Team: {', '.join(inst.get('girl_names', []))}")
                term.print(f"  Returns {return_time_text(player, inst)}")
            term.pause()
        elif kind == "collect":
            collect_reports(player, home_city, home_house)


def _dispatch_team_select(player, home_city, house, offer):
    """Toggle-select a team, preview success, and launch the mission."""
    from facilities.dispatch import (
        eligible_girls, team_cap, success_chance_for, create_instance,
        girl_status_line,
    )
    cap = team_cap(house.get("level", 1))
    team = []

    while True:
        term.clear()
        day = player.get("day", 1)
        term.print(f"=== {offer['name']} ===")
        term.print(f"  {'★' * offer['stars']} {offer['label']} · power {offer['power']} · "
                   f"~{offer['hours']}h · risk {offer['risk']}")
        if offer.get("floors"):
            term.print(f"  Floors {offer['floors'][0]}–{offer['floors'][1]}")
        term.print(f"  Team: {len(team)}/{cap} — press a name to add/remove it")
        term.print()

        LAUNCH_STYLE = {"bg": "#2f6b2f", "fg": "#e0ffe0",
                        "active_bg": "#3f8b3f", "active_fg": "#f0fff0"}

        pool = eligible_girls(player, house)
        options, actions, styles = [], [], []
        for g in pool:
            mark = "★" if any(g is m for m in team) else " "
            options.append(f"[{mark}] {display_name(g)} Lv{g.get('level', 1)} — {girl_status_line(g, day)}")
            actions.append(("toggle", g))
            styles.append(None)
        if not pool:
            term.print("No girls are available (away, injured, or burned out).")
        if team:
            chance = success_chance_for(offer, team, day)
            names = ", ".join(display_name(g) for g in team)
            options.append(f"▶ Launch — {names} (projected success ~{chance}%)")
            actions.append(("launch", None))
            styles.append(LAUNCH_STYLE)

        idx = term.menu(options, prompt="Assemble your team:", allow_cancel=True,
                        cancel_label="Back", styles=styles, columns=2)
        if idx < 0:
            return
        kind, payload = actions[idx]

        if kind == "toggle":
            if payload in team:
                team.remove(payload)
            elif len(team) >= cap:
                term.print(f"At most {cap} girls can go on one mission.")
                term.pause()
            else:
                team.append(payload)
        elif kind == "launch":
            if not team:
                term.print("Pick at least one girl.")
                term.pause()
                continue
            names = ", ".join(display_name(g) for g in team)
            if not term.confirm(f"Send {names} on \"{offer['name']}\"?"):
                continue
            inst, msg = create_instance(player, home_city, house, offer, team)
            term.print(msg)
            if inst:
                advance_time(player, 30)  # organizing the send-off
            term.pause()
            return
