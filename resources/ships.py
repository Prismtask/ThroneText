# resources/ships.py
"""
Ship / vessel definitions (Phase B of the cargo system).

Ships are the sea-travel equivalent of mounts: they reduce sea voyage time,
mitigate sea events, carry cargo, and cost a monthly maintenance fee billed
on the 1st of each month (see facilities/monthly_billing.py).
"""

SHIPS = {
    "sloop": {
        "name": "Merchant Sloop",
        "tier": 1,
        "cost": 500,
        "sea_time_reduction": 0.30,   # 30 % faster voyages
        "event_mitigation": 0.10,     # 10 % less chance of any sea event
        "cargo_capacity": 40,         # cargo weight units
        "monthly_fee": 20,
    },
    "frigate": {
        "name": "War Frigate",
        "tier": 2,
        "cost": 1500,
        "sea_time_reduction": 0.35,
        "event_mitigation": 0.30,     # safest voyages
        "cargo_capacity": 90,
        "monthly_fee": 50,
    },
    "galleon": {
        "name": "Trade Galleon",
        "tier": 3,
        "cost": 4000,
        "sea_time_reduction": 0.40,
        "event_mitigation": 0.15,
        "cargo_capacity": 180,
        "monthly_fee": 100,
    },
}


def get_ship(ship_id):
    """Return ship definition or None."""
    return SHIPS.get(ship_id)


def get_ship_by_tier(tier):
    """Return (id, data) for the ship matching the given tier, or (None, None)."""
    for k, v in SHIPS.items():
        if v["tier"] == tier:
            return k, v
    return None, None
