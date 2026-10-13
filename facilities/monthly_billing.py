# facilities/monthly_billing.py
"""
Monthly maintenance billing — deducted on the 1st of each in-game month.

Seed of the future tax system: `compute_monthly_bills` returns a list of
(source, amount) owed per month. Debt is allowed — gold may go negative.

Wired into utils.advance_time() after day rollover (month boundary check via
events.get_month_day(day)[1] == 1).
"""

from events import get_month_day


def is_month_start(day):
    """True when `day` is the 1st of a month (months are 30 days)."""
    return get_month_day(day)[1] == 1


def compute_monthly_bills(player):
    """
    Return a list of (source_name, amount) owed this month.
    Sources: owned ship upkeep; high-tier land mount upkeep.
    Extend here for future taxes (house tax, trade fees, ...).
    """
    bills = []

    ship_id = player.get("ship_id")
    if ship_id:
        from resources.ships import get_ship
        ship = get_ship(ship_id)
        if ship:
            fee = ship.get("monthly_fee", 0)
            if fee:
                bills.append((f"{ship['name']} upkeep", fee))

    mount_id = player.get("mount_id")
    if mount_id:
        from resources.mounts import get_mount
        mount = get_mount(mount_id)
        if mount:
            fee = mount.get("monthly_fee", 0)
            if fee:
                bills.append((f"{mount['name']} upkeep", fee))

    return bills


def process_monthly_billing(player, day):
    """
    Deduct the monthly bills and return an event dict for display/journal,
    or None if nothing was owed. Gold may go negative (debt allowed).
    """
    bills = compute_monthly_bills(player)
    if not bills:
        return None

    total = sum(amount for _, amount in bills)
    player["gold"] = player.get("gold", 0) - total

    item_lines = "\n".join(f"    • {name}: {amount}g" for name, amount in bills)
    desc = (
        f"Maintenance due on the 1st of the month:\n"
        f"{item_lines}\n\n"
        f"  Total: {total}g\n"
        f"  Gold after payment: {player['gold']}g"
    )

    return {
        "day": day,
        "name": "Monthly Bills",
        "desc": desc,
        "tag": "[BILL]",
        "fixed": True,
        "duration": "Paid immediately",
    }
