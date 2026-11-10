# tests/test_gloves_rework.py — Black Silence Gloves rework (2026-10-07)
#
# Covers:
#  1. Enhance-level "mastery" scaling (+12% power per +1, capped ×1.60 at +5)
#  2. Min-1 damage floor vs extreme CON (ally-skill parity) — no more all-zero Furioso
#  3. damage_boost buffs + one-shot power_buff now apply to workshop/Furioso hits
#  4. HUD: WEDGE −50% tag for the Tarnished Jade curse
#  5. clear_battle_scoped_state scrub (EH suspend must not leak battle state)
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import combat.stats as stats
import combat.weapon.black_silence_gloves as g

_orig_roll_crit = stats.roll_critical_hit
_orig_roll_base = g._roll_base_damage


def setUpModule():
    # Deterministic: no crits, fixed roll of 10 so only the tested multipliers
    # move the numbers. _roll_base_damage returns roll + scaling_val.
    stats.roll_critical_hit = lambda *a, **k: (False, 0.0, 0.0)
    g._roll_base_damage = lambda scaling_val: 10 + scaling_val


def tearDownModule():
    stats.roll_critical_hit = _orig_roll_crit
    g._roll_base_damage = _orig_roll_base


def make_actor(enhance=0, buffs=None):
    actor = {
        "name": "Wearer", "is_ally": False, "current_hp": 100,
        "attributes": {"Strength": 10, "Constitution": 10, "Dexterity": 10,
                       "Learning": 10, "Wisdom": 10, "Charisma": 10},
        "equipped": {"weapon": {"id": "certain_someone_black_gloves",
                                "enhance": enhance}},
        "elemental_dmg": {}, "elemental_res": {},
        "active_buffs": list(buffs or []), "active_debuffs": [],
        "gloves_workshop_used": set(),
    }
    return actor


def make_enemy(hp=5000, con=0):
    return {"name": "Dummy", "hp": hp, "max_hp": hp, "con_mod": con,
            "elemental_res": {}}


def run_workshop(actor, wid, enemy, stat=40):
    return g._execute_workshop_actor(
        actor, [enemy], wid, stat, 0, stat, stat, stat, 0, is_player=True)


class TestEnhanceScaling(unittest.TestCase):
    def test_power_mult_curve(self):
        a = make_actor()
        cases = [(0, 1.00), (1, 1.12), (2, 1.24), (3, 1.36), (4, 1.48), (5, 1.60)]
        for lv, expected in cases:
            a["equipped"]["weapon"]["enhance"] = lv
            self.assertAlmostEqual(g.get_gloves_power_mult(a), expected, places=6)

    def test_power_mult_caps_at_plus_5(self):
        a = make_actor(enhance=99)
        self.assertAlmostEqual(g.get_gloves_power_mult(a), 1.60, places=6)

    def test_non_gloves_actor_gets_no_bonus(self):
        a = make_actor(enhance=5)
        a["equipped"]["weapon"] = {"id": "iron_sword", "enhance": 5}
        self.assertEqual(g.get_gloves_enhance_level(a), 0)
        self.assertEqual(g.get_gloves_power_mult(a), 1.0)
        # No weapon at all
        a["equipped"] = {}
        self.assertEqual(g.get_gloves_power_mult(a), 1.0)

    def test_workshop_damage_scales_with_enhance(self):
        enemy = make_enemy()
        run_workshop(make_actor(enhance=0), 8, enemy)
        dmg0 = 5000 - enemy["hp"]  # Logic: int(50 * 2.9) = 145
        self.assertEqual(dmg0, 145)

        enemy["hp"] = 5000
        run_workshop(make_actor(enhance=5), 8, enemy)
        dmg5 = 5000 - enemy["hp"]  # int(int(50 * 1.6) * 2.9) = int(80 * 2.9) = 232
        self.assertEqual(dmg5, 232)
        self.assertGreater(dmg5, dmg0)


class TestDamageFloor(unittest.TestCase):
    def test_workshops_cannot_deal_zero_vs_extreme_con(self):
        # CON 999: pre-rework every single hit was exactly 0. Ally-skill parity
        # floors each hit at 1 (element neutral here).
        for wid in range(1, 10):
            enemy = make_enemy(con=999)
            run_workshop(make_actor(), wid, enemy)
            dealt = 5000 - enemy["hp"]
            expected = 2 if wid == 3 else (3 if wid == 9 else 1)
            self.assertEqual(dealt, expected,
                             f"workshop {wid}: {dealt} (expected {expected})")

    def test_furioso_hits_all_floor_at_1(self):
        enemy = make_enemy(con=999, hp=5000)
        msg, victory = g._execute_furioso_actor(
            make_actor(), [enemy], 40, 0, 40, 40, 40, 0, is_player=True)
        # 8 single workshops + Zelkova's extra hit + Durandal's 2 extra = 12 hits
        self.assertEqual(5000 - enemy["hp"], 12, msg)
        self.assertIn("Total Furioso damage: 12", msg)
        self.assertFalse(victory)

    def test_normal_con_damage_unchanged(self):
        # Sanity: with CON 0 the floor doesn't interfere with real damage.
        # Ranga (DEX workshop, 1.20×): (10 + 40) * 1.20 = 60.
        enemy = make_enemy(con=0)
        run_workshop(make_actor(), 6, enemy)
        self.assertEqual(5000 - enemy["hp"], int(50 * 1.20))


class TestAttackBuffs(unittest.TestCase):
    def test_damage_boost_buff_multiplies(self):
        enemy = make_enemy()
        actor = make_actor(buffs=[{"type": "damage_boost", "value": 0.5}])
        run_workshop(actor, 8, enemy)
        # int(int(50 * 1.5) * 2.9) = int(75 * 2.9) = 217
        self.assertEqual(5000 - enemy["hp"], 217)

    def test_damage_boost_buffs_stack_additively(self):
        enemy = make_enemy()
        actor = make_actor(buffs=[{"type": "damage_boost", "value": 0.5},
                                  {"type": "damage_boost", "value": 0.5}])
        run_workshop(actor, 8, enemy)
        # Percentage sources are additive: 1.00 + 0.5 + 0.5 = 2.0
        # int(int(50 * 2.0) * 2.9) = 290
        self.assertEqual(5000 - enemy["hp"], 290)

    def test_power_buff_applied_and_consumed_once(self):
        enemy = make_enemy()
        actor = make_actor(buffs=[{"type": "power_buff", "value": 0.25}])
        msg, _ = run_workshop(actor, 8, enemy)
        # int(int(50 * 1.25) * 2.9) = int(62 * 2.9) = 179
        self.assertEqual(5000 - enemy["hp"], 179)
        self.assertIn("Empowered", msg)
        self.assertEqual(actor["active_buffs"], [])

    def test_furioso_collects_buffs_once(self):
        enemy = make_enemy(con=0)
        actor = make_actor(buffs=[{"type": "power_buff", "value": 0.5}])
        g._execute_furioso_actor(actor, [enemy], 40, 0, 40, 40, 40, 0,
                                 is_player=True)
        # power_buff consumed exactly once for the whole action
        self.assertEqual([b for b in actor["active_buffs"]
                          if b.get("type") == "power_buff"], [])


class TestHudTags(unittest.TestCase):
    def test_wedge_backlash_tag(self):
        from combat.combat_ui import _get_entity_buff_tags
        tags = _get_entity_buff_tags({"active_buffs": [], "active_debuffs": [],
                                      "tarnished_jade_weakened": True})
        self.assertIn("WEDGE \u221250%", tags)

    def test_wedge_tag_absent_without_flag(self):
        from combat.combat_ui import _get_entity_buff_tags
        tags = _get_entity_buff_tags({"active_buffs": [], "active_debuffs": []})
        self.assertNotIn("WEDGE", tags)


class TestBattleStateScrub(unittest.TestCase):
    def test_clear_battle_scoped_state(self):
        from combat.combat_engine import clear_battle_scoped_state
        player = {
            "active_buffs": [
                {"type": "evasion", "source": "crystal_atelier",
                 "value": 0.1, "remaining": 2},
                {"type": "stat", "stat": "all", "value": 4,
                 "source": "event_horizon", "permanent": True},
            ],
            "active_debuffs": [],
            "tarnished_jade_pins": 3,
            "tarnished_jade_weakened": True,
            "gloves_workshop_used": {1, 2, 3},
            "gloves_furioso_available": True,
            "potion_sickness": 2,
            "allies": [{"name": "Ally", "current_hp": 10,
                        "active_buffs": [
                            {"type": "evasion", "source": "crystal_atelier",
                             "value": 0.2, "remaining": 1}],
                        "active_debuffs": [],
                        "tarnished_jade_weakened": True,
                        "tarnished_jade_pins": 4}],
        }
        clear_battle_scoped_state(player)

        self.assertFalse(player["tarnished_jade_weakened"])
        self.assertEqual(player["tarnished_jade_pins"], 0)
        self.assertNotIn("gloves_workshop_used", player)
        self.assertNotIn("gloves_furioso_available", player)
        self.assertEqual(player["potion_sickness"], 0)
        # Battle dodge scrubbed, run buff kept
        self.assertTrue(all(b.get("source") != "crystal_atelier"
                            for b in player["active_buffs"]))
        self.assertTrue(any(b.get("source") == "event_horizon"
                            for b in player["active_buffs"]))
        ally = player["allies"][0]
        self.assertFalse(ally["tarnished_jade_weakened"])
        self.assertEqual(ally["tarnished_jade_pins"], 0)
        self.assertTrue(all(b.get("source") != "crystal_atelier"
                            for b in ally["active_buffs"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
