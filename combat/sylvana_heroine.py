# combat/sylvana_heroine.py
"""Sylvana heroine support helpers.

Her permanent passive, Queen's Grace, grants the whole party +5% evasion
while she is alive in the party. The flag is refreshed at round start (so
reinforcements and revived allies also benefit) and read by
``combat.stats.get_dodge_chance``.
"""


def is_sylvana_in_party(player):
    """True if the recruited Sylvana is in the player's party and alive."""
    for ally in player.get("allies", []):
        if ally.get("_heroine_key") == "sylvana" and ally.get("current_hp", 0) > 0:
            return True
    return False


def apply_sylvana_party_grace(player):
    """Tag the player + living allies with Queen's Grace for this round."""
    active = is_sylvana_in_party(player)
    for actor in [player] + list(player.get("allies", [])):
        if active and actor.get("current_hp", 0) > 0:
            actor["_mirror_grace"] = True
        else:
            actor.pop("_mirror_grace", None)


def clear_sylvana_party_grace(player):
    """Remove the Queen's Grace tag from every actor."""
    player.pop("_mirror_grace", None)
    for ally in player.get("allies", []):
        ally.pop("_mirror_grace", None)


def clear_sylvana_combat_state(player):
    """Scrub Sylvana's battle-scoped tags and Mirror Guard buffs."""
    clear_sylvana_party_grace(player)
    for actor in [player] + list(player.get("allies", [])):
        buffs = actor.get("active_buffs")
        if buffs:
            actor["active_buffs"] = [
                b for b in buffs if b.get("source") != "mirror_guard"
            ]
