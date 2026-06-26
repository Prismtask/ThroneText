# resources/mounts.py
"""
Mount / Stable / Caravan definitions.

Mounts reduce overland travel time and lower the chance of hostile travel events.
Sea voyages are not affected by mounts.
"""

MOUNTS = {
    "mule": {
        "name": "Mule",
        "tier": 1,
        "cost": 100,
        "time_reduction": 0.15,      # 15 % faster overland travel
        "event_mitigation": 0.10,    # 10 % less chance of any travel event
    },
    "horse": {
        "name": "Horse",
        "tier": 2,
        "cost": 300,
        "time_reduction": 0.25,
        "event_mitigation": 0.20,
    },
    "war_horse": {
        "name": "War Horse",
        "tier": 3,
        "cost": 800,
        "time_reduction": 0.35,
        "event_mitigation": 0.30,
    },
    "caravan": {
        "name": "Caravan",
        "tier": 4,
        "cost": 2000,
        "time_reduction": 0.45,
        "event_mitigation": 0.40,
    },
}


def get_mount(mount_id):
    """Return mount definition or None."""
    return MOUNTS.get(mount_id)


def get_mount_by_tier(tier):
    """Return (id, data) for the mount matching the given tier, or (None, None)."""
    for k, v in MOUNTS.items():
        if v["tier"] == tier:
            return k, v
    return None, None


def sell_value(mount_id):
    """A mount sells back for half its purchase cost."""
    mount = MOUNTS.get(mount_id)
    return mount["cost"] // 2 if mount else 0


def upgrade_cost(current_id, next_id):
    """Cost to trade current mount in for the next tier (full difference)."""
    current = MOUNTS.get(current_id, {})
    nxt = MOUNTS.get(next_id, {})
    return max(0, nxt.get("cost", 0) - current.get("cost", 0))


def downgrade_refund(current_id, prev_id):
    """
    Refund when trading current mount down to previous tier.
    Player receives half the cost difference between the two tiers.
    """
    current = MOUNTS.get(current_id, {})
    prev = MOUNTS.get(prev_id, {})
    return max(0, (current.get("cost", 0) - prev.get("cost", 0)) // 2)
