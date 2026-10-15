# combat/hallucination.py — Fatigue hallucinations (docs/time_system_design.md §5)
"""Stack II+ / Night illusions: a solo fight with yourself.

Trigger: fatigue stacks >= 2, Night phase, normal dungeon content (city
floors + wild ruins). Suppressed in Event Horizon runs, the Wonderland
pocket, boss rooms, and while critically wounded (<25% HP). Pandemonium
accrues and hallucinates as of rev 3.5 (player call). At most one roll
per room.

The enemy is a generated illusion (NOT a race): party-average stats with a
stack-scaled boost, 100% status immunity (`status_res = 1.0` rides the
existing superboss resistance path), a start-of-fight Dread pulse on the
player, evasion, and — at instability III — a mid-fight "flicker" re-form
(one heal + name change at 50% HP, dispatched by the engine's round hook).

Stakes (locked, rev 3.2 playtest): no gold / XP / loot, never counts as a
room clear; a victory clears one fatigue stack **at stack II only** — at
stack III the weariness clings (sleep-only), so high-stack fights are a
pure hazard; fleeing leaves stacks unchanged. "Dying" is not possible in
an illusion: you collapse and come to at 1 HP (the party's reactions are
part of the aftermath). Karma (future design) plugs into
`hallucination_tier()` as an extra input.
"""

import random

from character import player_max_hp
from combat.combat_io import c_print
from combat.elemental import ELEMENTS

HALLUCINATION_NAMES = ("Hollow You", "The Watcher", "Mirror Shade")

TIER_CHANCE = {2: 0.18, 3: 0.45}       # lockpick chance per room (§5)
TIER_STAT_BONUS = {2: 1.15, 3: 1.25}   # ≈ +15% / +25% over the party's curve
TIER_EVASION = {2: 0.15, 3: 0.28}      # "your blade passes where it isn't"


def hallucination_tier(player):
    """Instability tier from fatigue (2 or 3); 0 below stack II.

    Karma hook: when karma lands, add it here as an extra input to the tier.
    """
    try:
        import time_blocks
        stacks = time_blocks.get_fatigue_stacks(player)
    except Exception:
        try:
            stacks = int((player or {}).get("fatigue_stacks", 0) or 0)
        except (TypeError, ValueError):
            stacks = 0
    return min(3, max(0, stacks))


def should_trigger(player, room=None):
    """Gate + roll. True → run the encounter (call once per room)."""
    if not player:
        return False
    # Suppression: Event Horizon runs, Wonderland pocket. Pandemonium
    # accrues + hallucinates as of rev 3.5 (player call).
    if player.get("wonderland_active"):
        return False
    if player.get("_eh_in_run"):
        return False
    try:
        from event_horizon import in_run
        if in_run(player):
            return False
    except Exception:
        pass
    if player.get("current_hp", 1) <= 0:
        return False
    # Never triggers while critically wounded (~25% HP — knob)
    if player.get("current_hp", 1) < player_max_hp(player) * 0.25:
        return False
    # Boss rooms keep their own drama
    if room and room.get("is_boss"):
        return False
    # Night phase only (§5)
    try:
        import time_blocks
        if time_blocks.get_day_phase(player) != "night":
            return False
    except Exception:
        return False
    tier = hallucination_tier(player)
    if tier < 2:
        return False
    return random.random() < TIER_CHANCE.get(tier, TIER_CHANCE[2])


def _glitch(name):
    """Mild combining-mark glitch on every other letter (cheap + eerie)."""
    out = []
    for idx, ch in enumerate(name):
        out.append(ch)
        if ch != " " and idx % 2 == 0:
            out.append("\u0338")   # combining long solidus overlay
    return "".join(out)


def create_hallucination(player):
    """Build the illusion enemy dict (party-average stats + tier boost)."""
    from combat.stats import get_effective_attribute

    tier = max(2, hallucination_tier(player))
    bonus = TIER_STAT_BONUS.get(tier, TIER_STAT_BONUS[2])

    party = [player] + [a for a in player.get("allies", [])
                        if a.get("current_hp", 0) > 0]

    def _avg(getter):
        vals = [getter(m) for m in party if m is not None]
        return sum(vals) / max(1, len(vals))

    def _level(m):
        try:
            return int(m.get("level", 1) or 1)
        except (TypeError, ValueError):
            return 1

    avg_level = max(1, round(_avg(_level)))
    avg_str = max(1, round(_avg(lambda m: get_effective_attribute(m, "Strength"))))
    avg_con = max(1, round(_avg(lambda m: get_effective_attribute(m, "Constitution"))))
    avg_dex = max(1, round(_avg(lambda m: get_effective_attribute(m, "Dexterity"))))

    hp = int((70 + avg_level * 26) * bonus)

    enemy = {
        "key": "_hallucination",
        "name": _glitch(random.choice(HALLUCINATION_NAMES)),
        "hp": hp,
        "max_hp": hp,
        "str_mod": int(avg_str * 0.95 * bonus),
        "con_mod": int(avg_con * 0.85 * bonus),
        "dex_mod": int(avg_dex * 0.85),
        "level": avg_level,
        "multiplier": 1.0,
        "monster_girl": False,
        "dialogue": {},
        "elemental_res": {el: 1.0 for el in ELEMENTS},
        "elemental_dmg": {el: 1.0 for el in ELEMENTS},
        "active_debuffs": [],
        "active_buffs": [{"type": "evasion", "value": TIER_EVASION.get(tier, 0.15)}],
        "is_hallucination": True,
        "hallucination_tier": tier,
        # 100% status/debuff immunity — rides the superboss status_res path
        # (status_effects.get_status_res / check_status_resisted).
        "status_res": 1.0,
        "round_hook": hallucination_round_hook,
    }
    return enemy


def hallucination_round_hook(enemy, player, enemies):
    """Engine round-start hook: stack III flicker at 50% HP (once)."""
    if enemy.get("hallucination_tier", 2) < 3 or enemy.get("_flickered"):
        return
    if enemy.get("hp", 0) > enemy.get("max_hp", 1) * 0.5:
        return
    enemy["_flickered"] = True
    heal = max(1, int(enemy.get("max_hp", 1) * 0.15))
    enemy["hp"] = min(enemy.get("max_hp", 1), enemy.get("hp", 0) + heal)
    enemy["name"] = _glitch(random.choice(HALLUCINATION_NAMES))
    c_print("\n  The figure blinks out of focus — the air folds — and it snaps")
    c_print(f"  back wearing a different face.  ({enemy['name']} re-forms, wounds half-gone.)")


def print_intro(player):
    """The locked telegraph: hazy figure + companions gone (blocking prompt)."""
    from utils import _tprint, _tpause
    _tprint("\n" + "\u2500" * 52)
    _tprint("  A hazy figure stands where the path narrows.")
    _tprint("  You turn to call out — your companions are nowhere to be found.")
    _tprint("  The air hums like a struck bell.  This is not real.")
    _tprint("  It is standing there anyway.")
    _tpause("Press Enter...")


def run_encounter(player, floor=None, room_num=None, total_rooms=None,
                  combat_override=None):
    """Intro → Dread pulse → solo combat → outcome. Returns the result string.

    "victory" / "fled" are resolved internally (stack change + aftermath);
    "dead" / "timeout" / "error" are returned for the caller to propagate.
    """
    enemy = create_hallucination(player)
    print_intro(player)

    # One bounded dread pulse — it is fear given shape (§5)
    try:
        from combat.status_effects import apply_dread
        if apply_dread(player, duration=2) == "applied":
            from utils import _tprint
            _tprint("  A weight settles on your chest — it is looking straight "
                    "at you.  [Dreaded]")
    except Exception:
        pass

    player["_combat_solo"] = True
    try:
        if combat_override:
            result = combat_override(player, [], floor=floor, room_num=room_num,
                                     total_rooms=total_rooms, enemies=[enemy])
        else:
            from combat.combat_engine import combat
            result = combat(player, [], floor=floor, room_num=room_num,
                            total_rooms=total_rooms, enemies=[enemy])
    finally:
        player["_combat_solo"] = False

    if result == "dead":
        # It was never real — you snap out of it at the edge of collapse
        # instead of dying. The dungeon loop treats "collapsed" as a
        # non-fatal outcome and carries on with the room.
        player["current_hp"] = 1
        _collapsed_flavor(player)
        return "collapsed"

    resolve_outcome(player, result)
    return result


def _collapsed_flavor(player):
    """The pseudo-death: you wake at 1 HP with the party mid-panic."""
    from utils import _tprint, display_name
    _tprint("")
    _tprint("  The figure reaches for you — and the world lurches sideways.")
    _tprint("  You come to on the road, on your knees, gasping.  1 HP left.")
    living = [a for a in player.get("allies", []) if a.get("current_hp", 0) > 0]
    if living:
        who = display_name(random.choice(living))
        _tprint("  " + random.choice([
            f"{who} is shaking your shoulder: \"Hey — hey! You walked straight into that wall!\"",
            f"{who} stares at the empty road: \"You were fighting NOTHING. Look at me.\"",
            f"{who}: \"We couldn't wake you. What did you see out there?\"",
        ]))


def resolve_outcome(player, result):
    """Victory at stack II clears one stack; stack III is sleep-only (§5).

    Fleeing leaves stacks unchanged. At stack III the win no longer relieves
    exhaustion (playtest 2026-10-13): only real sleep does — up there the
    fight is a pure hazard, which is exactly the urgency it should carry.
    """
    from utils import _tprint
    if result == "victory":
        try:
            import time_blocks
            stacks = time_blocks.get_fatigue_stacks(player)
        except Exception:
            stacks = int(player.get("fatigue_stacks", 0) or 0)
        _tprint("")
        _tprint("  The figure unravels like smoke and the hum dies away.")
        if stacks == 2:
            player["fatigue_stacks"] = 1
            _tprint("  Your head clears a little.  (Fatigue 2 \u2192 1)")
        elif stacks >= 3:
            _tprint("  But the weariness sits bone-deep — it does not lift.")
            _tprint("  Only real sleep will mend this.  (Fatigue III — unchanged)")
        _aftermath(player)
    elif result == "fled":
        _tprint("")
        _tprint("  You break away — when you look back, the path is empty.")
        _tprint("  Your companions are standing exactly where they were, "
                "mid-sentence.")
        _aftermath(player, escaped=True)


def _aftermath(player, escaped=False):
    """The party never saw it — their confusion is the real cost (§5)."""
    from utils import _tprint, display_name
    living = [a for a in player.get("allies", []) if a.get("current_hp", 0) > 0]
    if not living:
        return
    who = display_name(random.choice(living))
    if escaped:
        _tprint(f"  {who}: \"...why are you out of breath?\"")
    else:
        _tprint(f"  {who} stares at your weapon, then at the empty air: "
                f"\"Who were you fighting?\"")
