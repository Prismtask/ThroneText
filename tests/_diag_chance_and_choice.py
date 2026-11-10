"""Diagnostic: Chance and Choice coin (EH trophy) — roll, message, plumbing.

Locks the 2026-10-14 report: "no indicator whether it deals more or less damage".

  1. Equipping the built unique is detected (special survives build/equip).
  2. Low roll  → damage ×0.25 with a visible DISASTER line.
  3. High roll → damage ×1.75 with a visible FORTUNE line.
  4. Per-action state: one roll, one message; multi-hit follow-ups reuse the
     multiplier silently.
  5. No coin equipped → damage untouched.
  6. Kit strikes ride the coin too (rev 3.5): Cutlass riposte, Jade Divine
     Lament, a Black Silence workshop volley (ONE flip across all hits),
     and Palette Spectrum's 3 hits (ONE shared flip).

Run from repo root with:
    .venv\\Scripts\\python.exe -m tests._diag_chance_and_choice
"""
import contextlib
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:  # piped consoles on Windows may default to a legacy codepage
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass

import combat.weapon.chance_and_choice as cac
from resources.items import build_item


class _FakeRandom:
    def __init__(self, v):
        self.v = v

    def random(self):
        return self.v


def _coin_player():
    item = build_item("chance_and_choice")
    return {"name": "Tester", "equipped": {"accessory1": item}}


def main():
    p = _coin_player()
    assert cac.actor_has_chance_and_choice(p), "equip detection failed"
    print("PASS 0: built unique is detected as equipped")

    orig = cac.random
    try:
        # ── 1. Low roll → ×0.25 + disaster line ──────────────────────────
        cac.random = _FakeRandom(0.2)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            dmg = cac.apply_chance_and_choice(p, 100)
        out = buf.getvalue()
        assert dmg == 25, dmg
        assert "×0.25" in out and "disaster" in out.lower(), out
        print("PASS 1: low roll → ×0.25 with a visible disaster line")

        # ── 2. High roll → ×1.75 + fortune line ──────────────────────────
        cac.random = _FakeRandom(0.9)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            dmg = cac.apply_chance_and_choice(p, 100)
        out = buf.getvalue()
        assert dmg == 175, dmg
        assert "×1.75" in out and "fortune" in out.lower(), out
        print("PASS 2: high roll → ×1.75 with a visible fortune line")

        # ── 3. One roll per action; follow-ups reuse silently ────────────
        state = {"rolled": False, "mult": 1.0}
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            first = cac.apply_chance_and_choice(p, 100, state)
            second = cac.apply_chance_and_choice(p, 100, state)
        out = buf.getvalue()
        assert first == second == 175, (first, second)
        assert out.count("coin") == 1, out
        print("PASS 3: one roll per action (multi-hit shares it, one message)")
    finally:
        cac.random = orig

    # ── 4. No coin equipped → untouched ──────────────────────────────────
    assert cac.apply_chance_and_choice({"equipped": {}}, 100) == 100
    print("PASS 4: no coin equipped → damage untouched")

    # ── 5. Kit strikes outside the standard paths flip too (rev 3.5) ─────
    import combat.stats as stats_mod

    orig_gea = stats_mod.get_effective_attribute
    stats_mod.get_effective_attribute = lambda a, s: 20
    orig_cac = cac.random
    cac.random = _FakeRandom(0.9)
    try:
        # Cutlass riposte (the wearer's own strike — one flip)
        import combat.weapon.captain_cutlass as cc
        actor = _coin_player()
        actor["equipped"]["weapon"] = build_item("cutlass_of_the_captain")
        enemy = {"name": "Mob", "hp": 500}
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            cc.trigger_captain_riposte(actor, enemy)
        out = buf.getvalue()
        dealt = 500 - enemy["hp"]
        assert "fortune" in out.lower(), out
        assert 24 <= dealt <= 29, dealt   # (20//2+3+1..4) × 1.75
        print("PASS 5: cutlass riposte rides the coin (one flip per riposte)")

        # Tarnished Jade discharge (own burst — one flip)
        import combat.weapon.tarnished_jade as tj
        orig_pmh = tj.player_max_hp
        tj.player_max_hp = lambda a: 100
        try:
            actor = _coin_player()
            actor["name"] = "Tester"
            actor["current_hp"] = 50
            actor["tarnished_jade_pins"] = 4
            enemy = {"name": "Mob", "hp": 500}
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                tj.trigger_divine_lament(actor, [enemy], source="test")
            out = buf.getvalue()
            base = 4 * (20 + 20) // 2       # pins × (STR+WIS)//2 = 80
            assert 500 - enemy["hp"] == int(base * 1.75), (500 - enemy["hp"], out)
            assert "fortune" in out.lower(), out
            print("PASS 6: Jade Divine Lament rides the coin (one flip for the burst)")
        finally:
            tj.player_max_hp = orig_pmh

        # Black Silence workshop volley (ONE flip across all hits)
        import combat.weapon.black_silence_gloves as bsg
        import combat.elemental as elem
        orig_calc = elem.calculate_elemental_damage
        orig_roll = stats_mod.roll_critical_hit
        elem.calculate_elemental_damage = lambda d, a, t, el="magical": d
        stats_mod.roll_critical_hit = lambda a, role, dex=0, lrn=0: (False, 0, 0)
        try:
            actor = _coin_player()
            actor["is_ally"] = True         # skip wedding/player-only hooks
            actor["name"] = "Wearer"
            actor["_gloves_cac_state"] = {"rolled": False, "mult": 1.0}
            target = {"name": "Mob", "hp": 1000}
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                d1, _ = bsg._deal_workshop_hit(actor, target, 100, "Allas", 10, 10)
                d2, _ = bsg._deal_workshop_hit(actor, target, 100, "Zelkova", 10, 10)
            out = buf.getvalue()
            assert (d1, d2) == (175, 175), (d1, d2)
            assert out.count("coin") == 1, out
            print("PASS 7: workshop volley rides one coin flip across all hits")
        finally:
            elem.calculate_elemental_damage = orig_calc
            stats_mod.roll_critical_hit = orig_roll

        # Palette Spectrum (3 hits — ONE shared flip)
        import combat.palette_ally as pa
        import combat.ally as ally_mod
        orig_pick = pa._pick_enemy
        orig_acs = ally_mod.compute_ally_stats
        orig_pa_calc = pa.calculate_elemental_damage
        pa._pick_enemy = lambda live, prompt: live[0]
        ally_mod.compute_ally_stats = lambda a: (5, 5, 5, 10, 10, 5)
        pa.calculate_elemental_damage = lambda d, a, t, el="magical": d
        try:
            actor = _coin_player()
            actor["name"] = "Palette"
            enemy = {"name": "Mob", "hp": 1000}
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                pa.palette_spectrum_attack(actor, None, [enemy])
            out = buf.getvalue()
            dealt = 1000 - enemy["hp"]
            assert "fortune" in out.lower(), out
            assert out.count("coin") == 1, out
            assert 24 <= dealt <= 36, dealt   # 3 hits of int(5..7 × 1.75)
            print("PASS 8: Spectrum's 3 hits share one flip")
        finally:
            pa._pick_enemy = orig_pick
            ally_mod.compute_ally_stats = orig_acs
            pa.calculate_elemental_damage = orig_pa_calc
    finally:
        cac.random = orig_cac
        stats_mod.get_effective_attribute = orig_gea

    print("\nAll Chance and Choice diagnostics passed.")


if __name__ == "__main__":
    main()
