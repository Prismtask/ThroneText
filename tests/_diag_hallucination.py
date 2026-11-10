"""Diagnostic: fatigue hallucinations (docs/time_system_design.md §5, locked 2026-10-13).

Covers:
  1. Gates — stack II+, Night, EH/Wonderland suppression, boss rooms,
     critically-wounded block, one roll per room (caller-side).
  2. The per-room roll honors the tier chance (deterministic via fake RNG).
  3. Generated illusion: party-average stats + tier boost, glitched name,
     evasion buff, round hook, status_res = 1.0 (100% immunity).
  4. Immunity rides the central check_status_resisted path.
  5. Flicker: tier III re-forms once at 50% HP; tier II never does.
  6. Outcomes: victory clears one stack; fleeing leaves stacks unchanged.
  7. run_encounter: solo flag set/cleared, pre-built enemy passed through,
     result resolved internally.
  8. Fatigue stat penalty (−N all stats), suppressed in Event Horizon only.
  9. Solo parking preserves party_order (front/bench kept, rev 3.5).

Run from repo root with:
    .venv\\Scripts\\python.exe -m tests._diag_hallucination
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:  # piped consoles on Windows may default to a legacy codepage
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass

import combat.hallucination as hall


class _FakeRandom:
    def __init__(self, v=0.0):
        self.v = v

    def random(self):
        return self.v

    def choice(self, seq):
        return seq[0]


def _player(**kw):
    p = {"name": "Tester", "level": 20,
         "attributes": {"Strength": 20, "Constitution": 18, "Dexterity": 14,
                        "Wisdom": 10, "Learning": 10, "Charisma": 10},
         "day": 3, "day_blocks": 16,         # Night phase (24-block day)
         "fatigue_stacks": 2, "time_minutes": 6 * 60,
         "inventory": [], "allies": [],
         "active_buffs": [], "active_debuffs": []}
    p.update(kw)
    from character import player_max_hp
    p.setdefault("current_hp", player_max_hp(p))
    return p


def main():
    # ── 1. Gates ─────────────────────────────────────────────────────────
    assert not hall.should_trigger(_player(fatigue_stacks=1))
    assert not hall.should_trigger(_player(day_blocks=0))       # morning
    assert not hall.should_trigger(_player(_eh_in_run=True))
    assert not hall.should_trigger(_player(wonderland_active=True))
    assert not hall.should_trigger(_player(), room={"is_boss": True})
    low = _player()
    low["current_hp"] = 1
    assert not hall.should_trigger(low)                         # <25% HP
    print("PASS 1: gates (stack II+/Night/EH/Wonderland/boss/low HP)")

    # ── 2. Per-room roll ─────────────────────────────────────────────────
    orig = hall.random
    try:
        hall.random = _FakeRandom(0.0)
        assert hall.should_trigger(_player())                   # stack II
        assert hall.should_trigger(_player(fatigue_stacks=3))   # stack III
        # rev 3.5: Pandemonium no longer suppresses hallucinations
        assert hall.should_trigger(_player(fatigue_stacks=3,
                                           pandemonium_mode=True))
        hall.random = _FakeRandom(0.99)
        assert not hall.should_trigger(_player(fatigue_stacks=3))
    finally:
        hall.random = orig
    print("PASS 2: per-room roll honors the tier chance")

    # ── 3. Generator ─────────────────────────────────────────────────────
    p3 = _player(fatigue_stacks=3)
    e3 = hall.create_hallucination(p3)
    assert e3["is_hallucination"] and e3["status_res"] == 1.0
    assert e3["hallucination_tier"] == 3
    assert e3["hp"] > 0 and e3["max_hp"] == e3["hp"]
    assert callable(e3.get("round_hook"))
    assert any(b.get("type") == "evasion" and b.get("value") >= 0.28
               for b in e3["active_buffs"])
    assert "\u0338" in e3["name"]                               # glitched
    e2 = hall.create_hallucination(_player())
    assert e2["hallucination_tier"] == 2
    assert e2["hp"] < e3["hp"] and e2["str_mod"] < e3["str_mod"]
    print("PASS 3: illusion generator — immunity, evasion, glitch, tier boost")

    # ── 4. Immunity path ─────────────────────────────────────────────────
    from combat.status_effects import check_status_resisted
    assert check_status_resisted(e3) is True
    print("PASS 4: 100% status immunity rides check_status_resisted")

    # ── 5. Flicker ───────────────────────────────────────────────────────
    e3["hp"] = int(e3["max_hp"] * 0.4)
    e3["name"] = hall._glitch("Mirror Shade")   # deterministic vs the fake RNG
    name_before = e3["name"]
    _rng = hall.random
    hall.random = _FakeRandom(0.0)               # choice → "Hollow You"
    try:
        hall.hallucination_round_hook(e3, p3, [e3])
        assert e3["_flickered"] and e3["hp"] > int(e3["max_hp"] * 0.4)
        assert e3["name"] != name_before
        hp_after = e3["hp"]
        hall.hallucination_round_hook(e3, p3, [e3])     # once only
        assert e3["hp"] == hp_after
        e2["hp"] = int(e2["max_hp"] * 0.4)
        hall.hallucination_round_hook(e2, p3, [e2])     # tier II: no-op
        assert not e2.get("_flickered")
    finally:
        hall.random = _rng
    print("PASS 5: flicker re-forms once at 50% HP (tier III only)")

    # ── 6. Outcomes ──────────────────────────────────────────────────────
    p6 = _player(fatigue_stacks=2)
    hall.resolve_outcome(p6, "victory")
    assert p6["fatigue_stacks"] == 1          # II → I (relief valve)
    p6c = _player(fatigue_stacks=3)
    hall.resolve_outcome(p6c, "victory")
    assert p6c["fatigue_stacks"] == 3         # III is sleep-only (rev 3.2)
    p6b = _player(fatigue_stacks=2)
    hall.resolve_outcome(p6b, "fled")
    assert p6b["fatigue_stacks"] == 2
    print("PASS 6: win clears at II only (III unchanged); flee unchanged")

    # ── 7. run_encounter plumbing ────────────────────────────────────────
    p7 = _player(fatigue_stacks=2)
    seen = {}

    def fake_override(player, keys, floor=None, room_num=None,
                      total_rooms=None, enemies=None):
        seen["enemies"] = enemies
        seen["solo"] = player.get("_combat_solo")
        seen["floor"], seen["room"] = floor, room_num
        return "victory"

    orig_intro = hall.print_intro
    hall.print_intro = lambda player: None
    try:
        res = hall.run_encounter(p7, floor=3, room_num=4, total_rooms=10,
                                 combat_override=fake_override)
    finally:
        hall.print_intro = orig_intro
    assert res == "victory"
    assert seen["solo"] is True and p7.get("_combat_solo") is False
    assert seen["enemies"] and seen["enemies"][0]["is_hallucination"]
    assert (seen["floor"], seen["room"]) == (3, 4)
    assert p7["fatigue_stacks"] == 1
    print("PASS 7: encounter runs solo with the pre-built illusion and resolves")

    # ── 7b. Collapse: "death" is a snap-out, not a death ─────────────────
    p7b = _player(fatigue_stacks=2)
    p7b["current_hp"] = 5
    hall.print_intro = lambda player: None
    try:
        res2 = hall.run_encounter(p7b, combat_override=lambda *a, **k: "dead")
    finally:
        hall.print_intro = orig_intro
    assert res2 == "collapsed" and p7b["current_hp"] == 1
    assert p7b["fatigue_stacks"] == 2
    assert p7b.get("_combat_solo") is False
    print("PASS 7b: collapse wakes at 1 HP (no death, stacks unchanged)")

    # ── 7c. Solo park restores party_order (rev 3.5 fix) ─────────────────
    # Regression (Pande playtest): ensure_party_order() pruned party_order
    # against the parked (empty) allies list mid-illusion, so the front/bench
    # arrangement silently reset to default for the next real fight.
    import combat.combat_engine as engine

    p7c = _player(fatigue_stacks=0)
    p7c["allies"] = [
        {"name": "One", "current_hp": 10, "max_hp": 10},
        {"name": "Two", "current_hp": 10, "max_hp": 10},
        {"name": "Three", "current_hp": 10, "max_hp": 10},
    ]
    p7c["party_order"] = [1, 0, 2]          # custom arrangement (Two leads)

    park_seen = {}
    orig_begin = engine.begin_wedding_combat
    orig_end = engine.end_wedding_combat
    orig_inner = engine._combat_inner

    def fake_inner(player, enemy_keys, floor=None, room_num=None,
                   total_rooms=None, enemies=None):
        park_seen["parked"] = list(player.get("allies") or [])
        from combat.ally import ensure_party_order
        ensure_party_order(player)          # this used to wipe party_order
        park_seen["wiped"] = list(player.get("party_order") or [])
        return "victory"

    engine.begin_wedding_combat = lambda *a, **k: None
    engine.end_wedding_combat = lambda *a, **k: None
    engine._combat_inner = fake_inner
    try:
        p7c["_combat_solo"] = True
        res3 = engine.combat(p7c, [])
    finally:
        engine.begin_wedding_combat = orig_begin
        engine.end_wedding_combat = orig_end
        engine._combat_inner = orig_inner
    assert res3 == "victory"
    assert park_seen["parked"] == []            # allies really were parked
    assert park_seen["wiped"] == []             # ...which is how it got wiped
    assert [a["name"] for a in p7c["allies"]] == ["One", "Two", "Three"]
    assert p7c["party_order"] == [1, 0, 2]      # arrangement survived
    print("PASS 7c: solo parking preserves party order (front/bench kept)")

    # ── 8. Fatigue stat penalty ──────────────────────────────────────────
    from combat.stats import get_effective_attribute
    p8 = _player(fatigue_stacks=0)
    base = get_effective_attribute(p8, "Strength")
    p8["fatigue_stacks"] = 2
    assert get_effective_attribute(p8, "Strength") == base - 2
    p8["pandemonium_mode"] = True
    assert get_effective_attribute(p8, "Strength") == base - 2   # rev 3.5
    p8.pop("pandemonium_mode")
    p8["_eh_in_run"] = True
    assert get_effective_attribute(p8, "Strength") == base
    print("PASS 8: fatigue −N all stats (Pandemonium penalized; EH suppressed)")

    # ── 9. Personalized ally dialogue (victory + collapse) ───────────────
    from resources.enemies import ENEMIES
    from combat import hallucination_dialogue as hd
    import utils as _utils

    girls = [k for k, v in ENEMIES.items() if v.get("monster_girl")]
    heroines = ["alice", "red_hood", "dorothy", "palette"]
    for key in girls + heroines:
        assert len(hd.VICTORY_LINES.get(key) or []) >= 2, key
        assert len(hd.COLLAPSE_LINES.get(key) or []) >= 2, key
    assert set(hd.RACE_VICTORY_LINES) == set(hd.RACE_COLLAPSE_LINES)

    # Lookup precedence: heroine → enemy key → race → generic
    assert hd.ally_identity_key({"key": "goblin_girl"}) == "goblin_girl"
    assert hd.ally_identity_key(
        {"_heroine_key": "alice", "key": "goblin_girl"}) == "alice"
    assert hd.has_personalized_lines({"key": "slime_girl"})
    assert not hd.has_personalized_lines(
        {"key": "synthetic_child", "race": "Goblin"})
    assert hd.get_ally_line(
        {"_heroine_key": "alice", "key": "goblin_girl"}, "victory"
    ) in hd.VICTORY_LINES["alice"]
    assert hd.get_ally_line(
        {"key": "slime_girl"}, "collapse"
    ) in hd.COLLAPSE_LINES["slime_girl"]
    assert hd.get_ally_line(
        {"key": "synthetic_child", "race": "Goblin"}, "victory"
    ) in hd.RACE_VICTORY_LINES["Goblin"]
    assert hd.get_ally_line(
        {"key": "unknown", "race": "Unknown"}, "collapse"
    ) in hd.GENERIC_COLLAPSE

    # The aftermath + collapse flavor actually speak the personal line.
    printed = []
    orig_tprint = _utils._tprint
    _utils._tprint = lambda *a, **k: printed.append(
        " ".join(str(x) for x in a))
    try:
        p9 = _player()
        p9["allies"] = [{"name": "Blob", "key": "slime_girl",
                         "current_hp": 4, "max_hp": 4}]
        hall._aftermath(p9, escaped=False)
        assert printed and printed[-1].startswith("  Blob: \"")
        assert any(line in printed[-1]
                   for line in hd.VICTORY_LINES["slime_girl"])

        printed.clear()
        hall._collapsed_flavor(p9)
        assert any(line in printed[-1]
                   for line in hd.COLLAPSE_LINES["slime_girl"])

        printed.clear()
        p9["allies"] = [{"name": "Wisp", "key": "nobody",
                         "race": "Unknown", "current_hp": 4, "max_hp": 4}]
        hall._collapsed_flavor(p9)
        assert any(line in printed[-1] for line in hd.GENERIC_COLLAPSE)

        printed.clear()
        p9["allies"] = []
        hall._collapsed_flavor(p9)
        assert "get up alone" in printed[-1]
    finally:
        _utils._tprint = orig_tprint
    print("PASS 9: personalized ally reactions (60 identities + fallbacks)")

    print("\nAll hallucination diagnostics passed.")


if __name__ == "__main__":
    main()
