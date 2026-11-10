"""Event Horizon Phase 1 tests — core state, scaling, flasks, trial cards,
Entropy, payout math, milestone schedule, trophy items, wipe/strip.

Run: c:/Code/Pandemonium/.venv/Scripts/python.exe -m pytest tests/test_event_horizon.py
"""

import random
import unittest

import event_horizon as eh
from resources.races_classes import ATTRIBUTES


def make_player(**over):
    p = {
        "name": "Hero",
        "current_hp": 100,
        "max_hp": 100,
        "level": 50,
        "gold": 0,
        "max_floor": 30,
        "attributes": {a: 10 for a in ATTRIBUTES},
        "active_buffs": [],
        "active_debuffs": [],
        "allies": [],
    }
    p.update(over)
    return p


def make_ally(name="Mira", weapon_type=None, affection=0):
    ally = {
        "name": name,
        "key": "harpy_scout",
        "is_ally": True,
        "current_hp": 50,
        "max_hp": 50,
        "level": 40,
        "affection": affection,
        "attributes": {a: 8 for a in ATTRIBUTES},
        "active_buffs": [],
        "active_debuffs": [],
        "equipped": {"weapon": None, "armor": None, "accessory1": None, "accessory2": None},
    }
    if weapon_type:
        ally["equipped"]["weapon"] = {"id": "w_test", "name": "Test Blade", "weapon_type": weapon_type}
    return ally


def sword_item():
    return {"id": "iron_sword", "name": "Iron Sword", "slot": "weapon", "weapon_type": "sword"}


def robe_item():
    return {"id": "old_dopo_robe", "name": "Old Dopo Robe", "slot": "armor", "special": "dopo_robe"}


def por_item():
    return {"id": "piece_of_relationship", "name": "Piece of Relationship",
            "slot": "accessory", "special": "piece_of_relationship"}


def cac_item():
    return {"id": "chance_and_choice", "name": "Chance and Choice",
            "slot": "accessory", "special": "chance_and_choice"}


class TestState(unittest.TestCase):
    def test_migration_creates_defaults(self):
        p = make_player()
        state = eh.ensure_eh_state(p)
        self.assertFalse(state["run_active"])
        self.assertEqual(state["room"], 0)
        self.assertEqual(state["best_room"], 0)
        self.assertIsInstance(state["actor_flasks"], dict)
        # Idempotent + preserves existing values
        state["room"] = 12
        state2 = eh.ensure_eh_state(p)
        self.assertEqual(state2["room"], 12)
        self.assertIs(state, state2)

    def test_gating(self):
        p = make_player()
        eh.ensure_eh_state(p)
        self.assertFalse(eh.in_run(p))
        p["_eh_in_run"] = True
        self.assertFalse(eh.in_run(p))
        p["event_horizon"]["run_active"] = True
        self.assertTrue(eh.in_run(p))
        p.pop("_eh_in_run")
        self.assertFalse(eh.in_run(p))


class TestSiteUnlock(unittest.TestCase):
    """Floor 20 must be CLEARED — reaching it (failed boss) must not open EH."""

    def test_requires_floor_20_cleared(self):
        p = make_player(max_floor=20)
        self.assertFalse(eh.site_unlocked(p))
        self.assertIsNone(eh.event_horizon_site(p))
        p["max_floor"] = 21
        self.assertTrue(eh.site_unlocked(p))
        self.assertIsNotNone(eh.event_horizon_site(p))

    def test_failed_floor_20_attempt_stays_locked(self):
        # max_floor hits 20 by descending past Floor 19; dying to the
        # Floor-20 superboss leaves it at 20 and must not unlock the rift.
        p = make_player(max_floor=20, current_hp=1)
        self.assertFalse(eh.site_unlocked(p))
        self.assertIsNone(eh.build_journey_to_site(p))

    def test_existing_progress_grandfathered(self):
        p = make_player(max_floor=20)
        p["eh_intro_seen"] = True
        self.assertTrue(eh.site_unlocked(p))

        q = make_player(max_floor=20)
        q["event_horizon"] = {"run_active": True}
        self.assertTrue(eh.site_unlocked(q))

        r = make_player(max_floor=20)
        r["event_horizon"] = {"best_room": 3}
        self.assertTrue(eh.site_unlocked(r))


class TestFlask(unittest.TestCase):
    def test_tier_bounds(self):
        random.seed(7)
        for room in (1, 7, 13, 36, 100):
            cap = eh.flask_tier_max(room)
            for _ in range(60):
                flask = eh.roll_flask(room)
                self.assertGreaterEqual(flask["tier"], 1)
                self.assertLessEqual(flask["tier"], cap)
                self.assertLessEqual(cap, 7)
                spec = eh.FLASK_ARCHETYPES[flask["kind"]]
                self.assertEqual(flask["value"], spec["values"][flask["tier"] - 1])

    def test_forced_kind_and_tier(self):
        flask = eh.roll_flask(40, tier=5, kind="fervor")
        self.assertEqual(flask["kind"], "fervor")
        self.assertEqual(flask["type"], "damage_boost")
        self.assertEqual(flask["value"],
                         eh.FLASK_ARCHETYPES["fervor"]["values"][4])
        # Unknown archetype falls back to a random valid one (defensive)
        fallback = eh.roll_flask(10, kind="not_a_flask")
        self.assertIn(fallback["kind"], eh.FLASK_ARCHETYPES)

    def test_vitality_is_percent_max_hp(self):
        flask = eh.roll_flask(40, tier=7, kind="vitality")
        self.assertEqual(flask["type"], "regen_pct")
        self.assertAlmostEqual(flask["value"], 0.02)
        self.assertIn("% max HP", flask["label"])
        small = eh.roll_flask(40, tier=1, kind="vitality")
        self.assertAlmostEqual(small["value"], 0.005)

    def test_apply_and_strip(self):
        p = make_player()
        eh.ensure_eh_state(p)
        flask = {"kind": "fervor", "type": "damage_boost", "name": "Fervor",
                 "tier": 3, "value": 0.04, "stat": None}
        flask["label"] = eh.format_flask_label(flask)
        eh.apply_flask(p, p, flask)
        entries = [b for b in p["active_buffs"] if b.get("source") == eh.EH_SOURCE]
        self.assertEqual(len(entries), 1)
        self.assertTrue(entries[0]["permanent"])
        self.assertIn("player", p["event_horizon"]["actor_flasks"])
        eh.strip_event_horizon_effects(p)
        self.assertEqual([b for b in p["active_buffs"] if b.get("source") == eh.EH_SOURCE], [])
        eh.strip_event_horizon_effects(p)  # idempotent


class TestEntropy(unittest.TestCase):
    def test_stack_math_and_cap(self):
        p = make_player(allies=[make_ally()])
        state = eh.ensure_eh_state(p)
        state["room"] = 4
        self.assertEqual(eh.sync_entropy(p), 0)
        self.assertEqual([d for d in p["active_debuffs"] if d["type"] == "eh_entropy"], [])
        state["room"] = 60
        total = eh.sync_entropy(p)
        self.assertEqual(total, 56)
        for actor in [p] + p["allies"]:
            entry = next(d for d in actor["active_debuffs"] if d["type"] == "eh_entropy")
            self.assertEqual(entry["value"], eh.entropy_stat_penalty(56))
            self.assertAlmostEqual(entry["value"], 0.06)
        weight = 1 + total * eh.EH_GOLD_PER_ENTROPY
        self.assertAlmostEqual(weight, 2.12)

    def test_stat_penalty_steps(self):
        self.assertEqual(eh.entropy_stat_penalty(0), 0.0)
        self.assertEqual(eh.entropy_stat_penalty(19), 0.0)
        self.assertEqual(eh.entropy_stat_penalty(20), 0.03)
        self.assertAlmostEqual(eh.entropy_stat_penalty(137), 0.18)
        self.assertAlmostEqual(eh.entropy_stat_penalty(300), eh.EH_ENTROPY_CAP)
        self.assertAlmostEqual(eh.entropy_stat_penalty(9999), eh.EH_ENTROPY_CAP)

    def test_negative_card_adds_entropy(self):
        p = make_player()
        state = eh.ensure_eh_state(p)
        state["room"] = 13
        eh.sync_entropy(p)
        cards = eh.roll_trial_cards(p, positive=False)
        card = cards[0]
        msg = eh.apply_negative_card(p, card)
        self.assertIn("Trial accepted", msg)
        self.assertEqual(state["entropy"], eh.base_entropy_for_room(13) + card["entropy_cost"])
        mods = eh.get_enemy_mods(p)
        self.assertGreaterEqual(mods["hp"], 1.0)

    def test_positive_card_applies_to_roster(self):
        p = make_player(allies=[make_ally()])
        eh.ensure_eh_state(p)
        cards = eh.roll_trial_cards(p, positive=True)
        eh.apply_positive_card(p, cards[0])
        for actor in [p] + p["allies"]:
            self.assertTrue(any(b.get("source") == eh.EH_SOURCE for b in actor["active_buffs"]))
        self.assertEqual(len(p["event_horizon"]["positive_cards"]), 1)


class TestEnemyScaling(unittest.TestCase):
    def test_scaling_math(self):
        p = make_player()
        state = eh.ensure_eh_state(p)
        state["room"] = 41
        enemy = {"hp": 100, "max_hp": 100, "str_mod": 20, "con_mod": 10, "dex_mod": 10,
                 "status_res": 0.1, "elemental_dmg": {"fire": 1.2}}
        p["_eh_in_run"] = True
        state["run_active"] = True
        eh.apply_enemy_scaling(enemy, p)
        self.assertEqual(enemy["hp"], int(100 * (1 + eh.EH_ENEMY_HP_PER_ROOM * 40)))
        self.assertEqual(enemy["str_mod"], int(20 * (1 + eh.EH_ENEMY_DMG_PER_ROOM * 40)))

    def test_no_scaling_outside_run(self):
        p = make_player()
        enemy = {"hp": 100, "max_hp": 100, "str_mod": 20, "con_mod": 10, "dex_mod": 10}
        eh.apply_enemy_scaling(enemy, p)
        self.assertEqual(enemy["hp"], 100)

    def test_enemy_level_flat_start(self):
        p = make_player()
        p["max_floor"] = 60
        self.assertEqual(eh.enemy_level_for_room(p, 1), 20)
        self.assertEqual(eh.enemy_level_for_room(p, 3), 20)
        self.assertEqual(eh.enemy_level_for_room(p, 4), 21)
        self.assertEqual(eh.enemy_level_for_room(p, 31), 30)
        self.assertEqual(eh.enemy_level_for_room(p, 91), 50)
        self.assertEqual(eh.enemy_level_for_room(p, 106), 55)
        self.assertEqual(eh.enemy_level_for_room(p, 109), 56)
        self.assertEqual(eh.enemy_level_for_room(p, 500), 56)
        # Deep saves no longer start harder than a fresh unlock
        q = make_player()
        q["max_floor"] = 20
        self.assertEqual(eh.enemy_level_for_room(q, 1),
                         eh.enemy_level_for_room(p, 1))

    def test_enemy_band_widens_at_depth(self):
        p = make_player()
        # Early rooms: standard picker band (no widening yet)
        level, band_lo = eh.enemy_band_for_room(p, 1)
        self.assertEqual((level, band_lo), (20, 12))
        # Mid rooms: standard edge still below the floor cap
        level, band_lo = eh.enemy_band_for_room(p, 31)
        self.assertEqual(level, 30)
        self.assertEqual(band_lo, 30 - (6 + 30 // 10))
        # Capped depth: lower edge held at EH_ENEMY_BAND_FLOOR
        level, band_lo = eh.enemy_band_for_room(p, 109)
        self.assertEqual((level, band_lo), (56, eh.EH_ENEMY_BAND_FLOOR))
        level, band_lo = eh.enemy_band_for_room(p, 500)
        self.assertEqual((level, band_lo), (56, 30))

    def test_picker_honors_band_override(self):
        import dungeon
        from resources.enemies import ENEMIES
        p = make_player()
        picked = {dungeon.get_random_enemy_key(56, boss=False, region=None,
                                               player=p, band_lo=30)
                  for _ in range(40)}
        for key in picked:
            self.assertGreaterEqual(ENEMIES[key]["level"], 30)
            self.assertLessEqual(ENEMIES[key]["level"], 59)

    def test_enemy_difficulty_frozen_in_run(self):
        from combat.stats import enemy_stats
        p = make_player()
        p["day_blocks"] = 0            # Morning → ×1.0 outside runs (§7)
        p["time_minutes"] = 6 * 60
        p["daily_effects"] = {}
        outside = enemy_stats("goblin_scout", p)
        self.assertEqual(outside["multiplier"], 1.0)
        state = eh.ensure_eh_state(p)
        state["run_active"] = True
        p["_eh_in_run"] = True
        inside = enemy_stats("goblin_scout", p)
        self.assertEqual(inside["multiplier"], 1.25)   # frozen night baseline (§7)


class TestPayoutAndMilestones(unittest.TestCase):
    def test_payout_math(self):
        p = make_player()
        state = eh.ensure_eh_state(p)
        state["room"] = 50
        eh.sync_entropy(p)
        total = eh.get_entropy_total(p)
        expected_rooms = sum(eh.EH_GOLD_BASE + eh.EH_GOLD_PER_ROOM * r for r in range(1, 51))
        expected = int(expected_rooms * (1 + total * eh.EH_GOLD_PER_ENTROPY))
        self.assertEqual(eh.compute_payout(p), expected)

    def test_death_payout_deferred(self):
        p = make_player()
        state = eh.ensure_eh_state(p)
        state["room"] = 10
        amount, deferred = eh.grant_payout(p, death=True)
        self.assertTrue(deferred)
        self.assertEqual(p["gold"], 0)
        self.assertEqual(p["_eh_pending_payout"], amount)
        amount2, deferred2 = eh.grant_payout(p, death=False)
        self.assertFalse(deferred2)
        self.assertEqual(p["gold"], amount2)

    def test_milestone_schedule(self):
        p = make_player()
        eh.ensure_eh_state(p)
        self.assertEqual(eh.get_milestone_rewards(p, 24), [])
        kinds25 = [e["kind"] for e in eh.get_milestone_rewards(p, 25)]
        self.assertIn("high_flask", kinds25)
        kinds50 = [e["kind"] for e in eh.get_milestone_rewards(p, 50)]
        self.assertIn("boon", kinds50)
        self.assertIn("trophy", kinds50)
        t50 = next(e for e in eh.get_milestone_rewards(p, 50) if e["kind"] == "trophy")
        self.assertEqual(t50["item_id"], "chance_and_choice")
        self.assertTrue(eh.claim_milestone(p, t50))
        self.assertFalse(eh.claim_milestone(p, t50))
        self.assertNotIn("trophy", [e["kind"] for e in eh.get_milestone_rewards(p, 50)])
        t75 = next(e for e in eh.get_milestone_rewards(p, 75) if e["kind"] == "trophy")
        self.assertEqual(t75["item_id"], "old_dopo_robe")
        t100 = next(e for e in eh.get_milestone_rewards(p, 100) if e["kind"] == "trophy")
        self.assertEqual(t100["item_id"], "piece_of_relationship")
        self.assertIn("beating_root", [e["kind"] for e in eh.get_milestone_rewards(p, 125)])

    def test_clear_run_keeps_best_room_and_flags(self):
        p = make_player()
        state = eh.ensure_eh_state(p)
        state["room"] = 77
        state["run_active"] = True
        p["_eh_in_run"] = True
        p["eh_trophy_chance_and_choice"] = True
        eh.sync_entropy(p)
        best = eh.clear_run(p)
        self.assertEqual(best, 77)
        self.assertEqual(p["event_horizon"]["best_room"], 77)
        self.assertFalse(p["event_horizon"]["run_active"])
        self.assertNotIn("_eh_in_run", p)
        self.assertTrue(p["eh_trophy_chance_and_choice"])
        self.assertEqual([d for d in p["active_debuffs"] if d["type"] == "eh_entropy"], [])


class TestBattleStart(unittest.TestCase):
    def test_entropy_debuffs_applied(self):
        random.seed(3)
        p = make_player(allies=[make_ally()])
        state = eh.ensure_eh_state(p)
        state["run_active"] = True
        p["_eh_in_run"] = True
        state["room"] = 30
        eh.sync_entropy(p)
        applied = eh.apply_entropy_battle_start(p)
        self.assertGreaterEqual(applied, 2)
        for actor in [p] + p["allies"]:
            types = {d["type"] for d in actor["active_debuffs"]}
            self.assertTrue(types & set(eh.ENTROPY_DEBUFF_POOL), types)

    def test_no_debuffs_outside_run(self):
        p = make_player()
        self.assertEqual(eh.apply_entropy_battle_start(p), 0)

    def test_afflictions_acquired_every_ten_stacks(self):
        random.seed(7)
        p = make_player()
        state = eh.ensure_eh_state(p)
        state["room"] = 9  # 5 stacks → none yet
        eh.sync_entropy(p)
        self.assertEqual(state["entropy_afflictions"], [])
        state["room"] = 14  # 10 stacks → 1
        eh.sync_entropy(p)
        self.assertEqual(len(state["entropy_afflictions"]), 1)
        state["room"] = 24  # 20 stacks → 2 (distinct)
        eh.sync_entropy(p)
        self.assertEqual(len(state["entropy_afflictions"]), 2)
        self.assertEqual(len(set(state["entropy_afflictions"])), 2)
        state["room"] = 104  # 100 stacks → all 10
        eh.sync_entropy(p)
        self.assertEqual(len(state["entropy_afflictions"]),
                         len(eh.ENTROPY_DEBUFF_POOL))

    def test_battle_start_draws_from_afflictions_only(self):
        random.seed(11)
        p = make_player(allies=[make_ally()])
        state = eh.ensure_eh_state(p)
        state["run_active"] = True
        p["_eh_in_run"] = True
        state["room"] = 14  # 10 stacks → exactly one affliction
        eh.sync_entropy(p)
        owned = set(state["entropy_afflictions"])
        self.assertEqual(len(owned), 1)
        applied = eh.apply_entropy_battle_start(p)
        self.assertGreaterEqual(applied, 1)
        for actor in [p] + p["allies"]:
            types = {d["type"] for d in actor["active_debuffs"]}
            self.assertTrue(types & owned, types)
            self.assertFalse(
                (types & set(eh.ENTROPY_DEBUFF_POOL)) - owned,
                f"rolled a non-owned affliction: {types}")

    def test_no_afflictions_early_run(self):
        random.seed(13)
        p = make_player()
        state = eh.ensure_eh_state(p)
        state["run_active"] = True
        p["_eh_in_run"] = True
        state["room"] = 9  # only 5 stacks → no afflictions yet
        eh.sync_entropy(p)
        self.assertEqual(eh.apply_entropy_battle_start(p), 0)


class TestTrophies(unittest.TestCase):
    def test_dopo_robe_multipliers(self):
        from combat.weapon import dopo_robe
        p = make_player()
        p["equipped"] = {
            "weapon": {"id": "x", "name": "X", "weapon_type": "blade"},
            "armor": robe_item(),
        }
        p["allies"] = [make_ally("A", "sword"), make_ally("B", "axe"), make_ally("C", "blade")]
        expected = dopo_robe.WEARER_BASE + dopo_robe.WEARER_PER_ALLY
        self.assertAlmostEqual(dopo_robe.get_robe_multiplier(p, p), expected)
        self.assertEqual(dopo_robe.get_robe_multiplier(p["allies"][0], p), 1.0)
        self.assertEqual(dopo_robe.get_robe_multiplier(p["allies"][1], p), 1.0)
        self.assertAlmostEqual(dopo_robe.get_robe_multiplier(p["allies"][2], p), dopo_robe.ALLY_BONUS)
        # A non-blade weapon on the wearer disables the entire aura.
        p["equipped"]["weapon"] = sword_item()
        self.assertEqual(dopo_robe.get_robe_multiplier(p, p), 1.0)

    def test_chance_and_choice(self):
        from combat.weapon import chance_and_choice as cac
        random.seed(11)
        p = make_player()
        p["equipped"] = {"accessory1": cac_item()}
        state = {"rolled": False, "mult": 1.0}
        first = cac.apply_chance_and_choice(p, 100, state)
        second = cac.apply_chance_and_choice(p, 100, state)
        self.assertEqual(first, second)  # one roll per action
        self.assertIn(state["mult"], (cac.LOW_MULT, cac.HIGH_MULT))
        # No item → untouched
        q = make_player()
        self.assertEqual(cac.apply_chance_and_choice(q, 100), 100)

    def test_piece_of_relationship_tiers(self):
        from combat.weapon import piece_of_relationship as por
        p = make_player()
        p["equipped"] = {"accessory1": por_item()}
        bonded = [make_ally(f"B{i}", affection=200) for i in range(7)]
        others = [make_ally("C0", affection=50)]
        p["allies"] = bonded + others
        self.assertEqual(por.count_bonded_allies(p), 7)
        tier = por.apply_battle_start(p)
        self.assertEqual(tier, 7)
        mc_dmg = [b for b in p["active_buffs"]
                  if b["type"] == "damage_boost" and b.get("source") == por.SOURCE]
        self.assertTrue(mc_dmg and mc_dmg[0]["value"] == 0.20)
        for ally in bonded:
            self.assertTrue(any(b.get("source") == por.SOURCE for b in ally["active_buffs"]))
        self.assertFalse(any(b.get("source") == por.SOURCE for b in others[0]["active_buffs"]))
        # Mark hook (tier +7)
        enemy = {"name": "Foe", "hp": 30}
        por.maybe_mark_attacker(enemy, bonded[0], p)
        self.assertTrue(enemy["hunters_mark"])
        self.assertEqual(enemy["hunters_mark_bonus"], por.MARK_BONUS)
        self.assertEqual(enemy["hunters_mark_turns"], por.MARK_TURNS)
        # Cleanup strips battle buffs
        por.clear_battle_buffs(p)
        for actor in [p] + p["allies"]:
            self.assertFalse(any(b.get("source") == por.SOURCE for b in actor["active_buffs"]))

    def test_por_low_count_no_effect(self):
        from combat.weapon import piece_of_relationship as por
        p = make_player(allies=[make_ally("Solo", affection=200)])
        p["equipped"] = {"accessory1": por_item()}
        self.assertEqual(por.apply_battle_start(p), 0)


class TestRunSummary(unittest.TestCase):
    def test_summary_captures_run_details(self):
        random.seed(41)
        p = make_player(gold=0, allies=[make_ally("Mira")])
        state = eh.ensure_eh_state(p)
        state["run_active"] = True
        p["_eh_in_run"] = True
        state["room"] = 12
        state["best_room"] = 20
        state["motes"] = 44
        eh.sync_entropy(p)
        pos = eh.roll_trial_cards(p, positive=True, count=1)[0]
        eh.apply_positive_card(p, pos)
        neg = eh.roll_trial_cards(p, positive=False, count=1)[0]
        eh.apply_negative_card(p, neg)
        flask = eh.roll_flask(12, tier=4)
        eh.apply_flask(p, p, flask)
        flask2 = eh.roll_flask(12, tier=2)
        eh.apply_flask(p, p["allies"][0], flask2)
        eh.apply_joker(p)          # default = Strength

        summary = eh.build_run_summary(p, payout=99)
        d = summary["data"]
        self.assertEqual(d["room"], 12)
        self.assertEqual(d["best"], 20)
        self.assertEqual(d["motes"], 44)
        self.assertEqual(d["payout"], 99)
        self.assertFalse(d["fatal"])
        self.assertEqual([n for n, _t in d["positive"]], [pos["name"]])
        self.assertEqual([n for n, _t in d["negative"]], [neg["name"]])
        self.assertEqual(d["tarot"], ["Strength"])
        self.assertEqual(d["total_flasks"], 2)
        self.assertEqual(len(d["flasks"]["player"]), 1)
        ally_key = f"{p['allies'][0]['key']}:{p['allies'][0]['name']}"
        self.assertEqual(len(d["flasks"][ally_key]), 1)

        text = "\n".join(summary["lines"])
        self.assertIn("Rooms cleared this run", text)
        self.assertIn("CARDS TAKEN", text)
        self.assertIn(pos["name"], text)
        self.assertIn(neg["name"], text)
        self.assertIn("TAROT", text)
        self.assertIn("Strength", text)
        self.assertIn("FLASK EFFECTS", text)
        self.assertIn(flask["label"], text)
        self.assertIn(flask2["label"], text)
        self.assertIn("Gold paid out           : +99", text)
        self.assertIn("Motes forfeited : 44", text)

        # The wipe destroys the source data; the summary is the survivor
        eh.clear_run(p)
        fresh = eh.ensure_eh_state(p)
        self.assertEqual(fresh["actor_flasks"], {})
        self.assertEqual(fresh["positive_cards"], [])
        self.assertEqual(fresh["negative_cards"], [])
        self.assertEqual(fresh["joker_cards"], [])

    def test_fatal_summary_marks_deferred_payout(self):
        p = make_player()
        state = eh.ensure_eh_state(p)
        state["run_active"] = True
        p["_eh_in_run"] = True
        state["room"] = 7
        summary = eh.build_run_summary(p, payout=123, fatal=True)
        self.assertTrue(summary["data"]["fatal"])
        text = "\n".join(summary["lines"])
        self.assertIn("after the death toll", text)
        self.assertIn("death", summary["subtitle"])

    def test_empty_summary_is_safe(self):
        p = make_player()
        summary = eh.build_run_summary(p)
        text = "\n".join(summary["lines"])
        self.assertIn("+ (none)", text)
        self.assertIn("  − (none)", text)
        self.assertIn("TAROT", text)
        self.assertIn("♠ (none)", text)
        self.assertIn("(no flasks consumed)", text)
        self.assertIn("Gold paid out           : none", text)


class TestEffectDetachRestore(unittest.TestCase):
    def test_strip_clears_entropy_flags(self):
        p = make_player()
        eh._apply_one_entropy_debuff(p, "slow", 1)
        self.assertTrue(p.get("slowed"))
        self.assertTrue(any(d.get("_eh_entropy")
                            for d in p["active_debuffs"]))
        eh.strip_event_horizon_effects(p)
        self.assertFalse(p.get("slowed"), "flag outlived the stripped debuff")
        self.assertFalse(any(d.get("type") == "slow"
                             for d in p["active_debuffs"]))

    def test_strip_and_restore_round_trip(self):
        random.seed(5)
        p = make_player(allies=[make_ally("Mira")])
        state = eh.ensure_eh_state(p)
        state["run_active"] = True
        p["_eh_in_run"] = True
        state["room"] = 30
        eh.sync_entropy(p)
        eh.apply_entropy_battle_start(p)
        flask = eh.roll_flask(12, tier=3)
        eh.apply_flask(p, p, flask)
        card = eh.roll_trial_cards(p, positive=True, count=1)[0]
        eh.apply_positive_card(p, card)

        eh.strip_event_horizon_effects(p)
        for actor in [p] + p["allies"]:
            self.assertFalse(any(b.get("source") == eh.EH_SOURCE
                                 for b in actor["active_buffs"]))
            self.assertFalse(any(d.get("type") == "eh_entropy"
                                 or d.get("_eh_entropy")
                                 for d in actor["active_debuffs"]))
        # Run data survives for the restore
        self.assertEqual(len(state["actor_flasks"]["player"]), 1)
        self.assertEqual(len(state["positive_cards"]), 1)
        self.assertEqual(len(state["entropy_afflictions"]), 2)

        eh.restore_event_horizon_effects(p)
        self.assertTrue(any(d.get("type") == "eh_entropy"
                            for d in p["active_debuffs"]))
        self.assertTrue(any(b.get("source") == eh.EH_SOURCE
                            for b in p["active_buffs"]))
        self.assertTrue(any(b.get("type") == flask["type"]
                            for b in p["active_buffs"]))
        # Idempotent — no duplicate entries on a second restore
        count_before = sum(1 for b in p["active_buffs"]
                           if b.get("source") == eh.EH_SOURCE)
        eh.restore_event_horizon_effects(p)
        count_after = sum(1 for b in p["active_buffs"]
                          if b.get("source") == eh.EH_SOURCE)
        self.assertEqual(count_before, count_after)

    def test_flask_record_stores_effect(self):
        random.seed(9)
        p = make_player()
        flask = eh.roll_flask(12, tier=5)
        rec = eh.apply_flask(p, p, flask)
        self.assertEqual(rec["effect"]["type"], flask["type"])
        self.assertEqual(rec["effect"]["value"], flask["value"])

    def test_refresh_merge_gets_marked(self):
        """A fresh application refreshing an unmarked entry still tags it."""
        p = make_player()
        p["active_debuffs"].append({"type": "damage_taken_up", "value": 0.08,
                                    "remaining": 1})
        eh._apply_one_entropy_debuff(p, "damage_taken_up", 1)
        self.assertTrue(all(d.get("_eh_entropy")
                            for d in p["active_debuffs"]
                            if d.get("type") == "damage_taken_up"))
        eh.strip_event_horizon_effects(p)
        self.assertFalse(any(d.get("type") == "damage_taken_up"
                             for d in p["active_debuffs"]))

    def test_legacy_dt_sweep_scope(self):
        p = make_player()
        p["active_debuffs"].append({"type": "damage_taken_up", "value": 0.08,
                                    "remaining": 2})
        # Default strip leaves untagged entries alone…
        eh.strip_event_horizon_effects(p)
        self.assertTrue(any(d.get("type") == "damage_taken_up"
                            for d in p["active_debuffs"]))
        # …the legacy sweep (exit/load paths) removes the tier-ladder value.
        eh.strip_event_horizon_effects(p, legacy=True)
        self.assertFalse(any(d.get("type") == "damage_taken_up"
                             for d in p["active_debuffs"]))
        # Non-entropy values are never touched, even in legacy mode
        p["active_debuffs"].append({"type": "damage_taken_up", "value": 0.25,
                                    "remaining": 5})
        eh.strip_event_horizon_effects(p, legacy=True)
        self.assertTrue(any(d.get("type") == "damage_taken_up"
                            for d in p["active_debuffs"]))


class TestBeatingRoot(unittest.TestCase):
    def _root_item(self):
        from resources.items import build_item
        return build_item("beating_root")

    def test_consume_unlocks_and_consumes(self):
        p = make_player(allies=[make_ally("Mira")])
        p["inventory"] = [self._root_item()]
        msg = eh.consume_beating_root(p, p)
        self.assertIn("third accessory slot", msg)
        self.assertTrue(p["acc3_unlocked"])
        self.assertIn("accessory3", p["equipped"])
        self.assertIsNone(p["equipped"]["accessory3"])
        self.assertEqual([i for i in p["inventory"]
                          if i.get("special") == "beating_root"], [])

    def test_consume_on_ally(self):
        p = make_player(allies=[make_ally("Mira")])
        p["inventory"] = [self._root_item()]
        ally = p["allies"][0]
        eh.consume_beating_root(p, ally)
        self.assertTrue(ally["acc3_unlocked"])
        self.assertIn("accessory3", ally["equipped"])
        self.assertFalse(p.get("acc3_unlocked", False))

    def test_consume_refuses_duplicate_and_missing(self):
        p = make_player()
        p["inventory"] = []
        self.assertIn("No Beating Root", eh.consume_beating_root(p, p))
        p["inventory"] = [self._root_item()]
        eh.consume_beating_root(p, p)
        p["inventory"] = [self._root_item()]
        msg = eh.consume_beating_root(p, p)
        self.assertIn("already", msg)
        # Refused use must not eat the item
        self.assertEqual(len(p["inventory"]), 1)

    def test_equip_auto_picks_slot3_when_unlocked(self):
        from inventory import equip_item
        p = make_player()
        p["equipped"] = {"weapon": None, "armor": None,
                         "accessory1": None, "accessory2": None}
        p["acc3_unlocked"] = True
        p["equipped"]["accessory3"] = None
        for _ in range(3):
            equip_item(p, dict(cac_item()))
        self.assertIsNotNone(p["equipped"]["accessory3"])

    def test_equip_slot3_locked_falls_back_to_default(self):
        # The third slot stays invisible until unlocked — a locked request
        # falls back to the normal accessory auto-pick chain, no message.
        from inventory import equip_item
        p = make_player()
        p["equipped"] = {"weapon": None, "armor": None,
                         "accessory1": None, "accessory2": None}
        result = equip_item(p, dict(cac_item()), target_slot="accessory3")
        self.assertTrue(result)
        self.assertIsNotNone(p["equipped"]["accessory1"])
        self.assertNotIn("accessory3", p["equipped"])

    def test_equipment_mods_include_slot3(self):
        from inventory import get_total_equipment_mods
        p = make_player()
        p["equipped"] = {"accessory3": {
            "id": "x", "name": "X", "slot": "accessory",
            "mods": {"Strength": 7}}}
        self.assertEqual(get_total_equipment_mods(p).get("Strength"), 7)

    def test_house_round_trip_keeps_unlock(self):
        from combat.ally import _ally_to_house_record, create_ally_from_girl
        ally = make_ally("Mira")
        ally["acc3_unlocked"] = True
        ally["equipped"]["accessory3"] = None
        rec = _ally_to_house_record(ally, {})
        self.assertTrue(rec.get("acc3_unlocked"))
        rebuilt = create_ally_from_girl(rec)
        self.assertTrue(rebuilt.get("acc3_unlocked"))
        self.assertIn("accessory3", rebuilt["equipped"])

    def test_house_record_without_unlock(self):
        from combat.ally import _ally_to_house_record
        ally = make_ally("Mira")
        rec = _ally_to_house_record(ally, {})
        self.assertFalse(rec.get("acc3_unlocked"))


class TestHudTags(unittest.TestCase):
    def test_entropy_tag(self):
        from combat.combat_ui import _get_entity_buff_tags
        ent = {"type": "eh_entropy", "stacks": 12, "value": 0.12,
               "source": "event_horizon"}
        tags = _get_entity_buff_tags({"active_debuffs": [ent],
                                      "active_buffs": []})
        self.assertIn("ENT×12", tags)
        # The attribute penalty is stated, not just the stack count
        self.assertIn("\u221212% attrs", tags)

    def test_elemental_flask_tag(self):
        from combat.combat_ui import _get_entity_buff_tags
        buff = {"type": "eh_ele_dmg", "value": 0.06,
                "source": "event_horizon", "permanent": True}
        tags = _get_entity_buff_tags({"active_buffs": [buff],
                                      "active_debuffs": []})
        self.assertIn("ELM+6%", tags)

    def test_trial_burden_tag(self):
        from combat.combat_ui import _get_entity_buff_tags
        tags = _get_entity_buff_tags({"active_buffs": [], "active_debuffs": [],
                                      "_eh_trial_count": 3})
        self.assertIn("TRL×3", tags)

    def test_trial_burden_effect_tags(self):
        from combat.combat_ui import _get_entity_buff_tags
        tags = _get_entity_buff_tags({
            "active_buffs": [], "active_debuffs": [],
            "_eh_trial_count": 3, "_eh_trial_tags": ["HP+20%", "DMG+9%"],
        })
        self.assertIn("TRL×3: HP+20% DMG+9%", tags)

    def test_flask_tags_stack(self):
        from combat.combat_ui import _get_entity_buff_tags
        buffs = [
            {"type": "damage_boost", "value": 0.04,
             "source": "event_horizon", "permanent": True},
            {"type": "damage_boost", "value": 0.05,
             "source": "event_horizon", "permanent": True},
            {"type": "damage_boost", "value": 0.03,
             "source": "event_horizon", "permanent": True},
            {"type": "eh_ele_dmg", "value": 0.08,
             "source": "event_horizon", "permanent": True},
            {"type": "eh_ele_dmg", "value": 0.04,
             "source": "event_horizon", "permanent": True},
        ]
        tags = _get_entity_buff_tags({"active_buffs": buffs,
                                      "active_debuffs": []})
        self.assertIn("DMG+12%", tags)
        self.assertNotIn("DMG+4%", tags)
        self.assertNotIn("DMG+5%", tags)
        self.assertIn("ELM+12%", tags)
        self.assertNotIn("ELM+8%", tags)

    def test_regen_flask_stacks(self):
        from combat.combat_ui import _get_entity_buff_tags
        buffs = [
            {"type": "regen", "value": 4,
             "source": "event_horizon", "permanent": True},
            {"type": "regen", "value": 6,
             "source": "event_horizon", "permanent": True},
        ]
        tags = _get_entity_buff_tags({"active_buffs": buffs,
                                      "active_debuffs": []})
        self.assertIn("REG+10", tags)

    def test_ally_skill_tags_stay_individual(self):
        from combat.combat_ui import _get_entity_buff_tags
        buffs = [
            {"type": "damage_boost", "value": 0.04,
             "source": "event_horizon", "permanent": True},
            {"type": "damage_boost", "value": 0.25,
             "remaining": 2},   # Frabjous Day
            {"type": "damage_boost", "value": 0.15,
             "remaining": 3},   # Fate's Favor
        ]
        tags = _get_entity_buff_tags({"active_buffs": buffs,
                                      "active_debuffs": []})
        self.assertIn("DMG+4%", tags)     # flask total (single entry)
        self.assertIn("DMG+25%", tags)    # ally skill — kept individual
        self.assertIn("DMG+15%", tags)    # ally skill — kept individual

    def test_stat_bonus_totals(self):
        from combat.combat_ui import _get_entity_buff_tags
        buffs = [{"type": "stat", "stat": "all", "value": 1,
                  "source": "event_horizon", "permanent": True}] * 3
        buffs.append({"type": "stat", "stat": "Strength", "value": 2,
                      "source": "event_horizon", "permanent": True})
        tags = _get_entity_buff_tags({"active_buffs": buffs,
                                      "active_debuffs": []})
        self.assertIn("ALL+3", tags)
        self.assertIn("STR+2", tags)

    def test_no_eh_tags_without_effects(self):
        from combat.combat_ui import _get_entity_buff_tags
        tags = _get_entity_buff_tags({"active_buffs": [],
                                      "active_debuffs": []})
        self.assertNotIn("ENT", tags)
        self.assertNotIn("ELM", tags)
        self.assertNotIn("TRL", tags)

    def test_flask_hint_tally(self):
        import event_horizon_rooms as ehr
        p = make_player(allies=[make_ally("Mira")])
        f1 = eh.roll_flask(12, tier=2)
        eh.apply_flask(p, p, f1)
        f2 = eh.roll_flask(12, tier=3)
        eh.apply_flask(p, p, f2)
        hint = ehr._flask_hint(p, p)
        self.assertIn(f1["name"], hint)
        if f1["name"] == f2["name"]:
            self.assertIn("×2", hint)
        else:
            self.assertIn(f2["name"], hint)
        # Actors who drank nothing get no hint
        self.assertEqual(ehr._flask_hint(p, p["allies"][0]), "")


class TestTrialBurdenTags(unittest.TestCase):
    """trial_burden_tags / enemy HUD trial detail (playtest 2026-10-06)."""

    def test_tags_from_cards(self):
        p = make_player()
        state = eh.ensure_eh_state(p)
        state["negative_cards"] = [
            {"effects": {"hp": 0.10}},
            {"effects": {"dmg": 0.06, "status_res": 0.08}},
            {"effects": {"regen": 0.02, "ele_dmg": 0.09}},
        ]
        tags = eh.trial_burden_tags(p)
        self.assertIn("HP+10%", tags)
        self.assertIn("DMG+6%", tags)
        self.assertIn("RES+8%", tags)
        self.assertIn("REG+2%", tags)
        self.assertIn("ELE+9%", tags)

    def test_no_cards_no_tags(self):
        p = make_player()
        eh.ensure_eh_state(p)
        self.assertEqual(eh.trial_burden_tags(p), [])

    def test_scaling_stamps_effect_tags(self):
        p = make_player()
        state = eh.ensure_eh_state(p)
        state["run_active"] = True
        state["negative_cards"] = [{"effects": {"hp": 0.10}}]
        p["_eh_in_run"] = True
        enemy = {"name": "Foe", "hp": 100, "max_hp": 100,
                 "str_mod": 10, "con_mod": 5, "dex_mod": 5,
                 "elemental_dmg": {}}
        eh.apply_enemy_scaling(enemy, p)
        self.assertEqual(enemy.get("_eh_trial_count"), 1)
        self.assertEqual(enemy.get("_eh_trial_tags"), ["HP+10%"])


class TestTuneUpStacking(unittest.TestCase):
    """Motes-merchant Tune-Up: +1 all attributes each — and it stacks."""

    def test_tuneups_stack_in_effective_attribute(self):
        from combat.stats import get_effective_attribute
        p = make_player()
        base = get_effective_attribute(p, "Strength")
        for _ in range(3):
            p["active_buffs"].append({
                "type": "stat", "stat": "all", "value": 1,
                "remaining": 9999, "permanent": True,
                "source": eh.EH_SOURCE, "label": "Tune-Up",
            })
        self.assertEqual(get_effective_attribute(p, "Strength"), base + 3)


class TestCardDeck(unittest.TestCase):
    """Deck rules (2026-10-07): unique (kind, tier) cards that stack."""

    def test_offers_are_distinct_kinds(self):
        p = make_player()
        eh.ensure_eh_state(p)["room"] = 40
        cards = eh.roll_trial_cards(p, positive=False)
        ids = [c["id"] for c in cards]
        self.assertEqual(len(ids), len(set(ids)))

    def test_offer_tiers_gated_by_depth(self):
        p = make_player()
        state = eh.ensure_eh_state(p)
        state["room"] = 12
        offers = eh.roll_trial_cards(p, positive=False, count=6)
        self.assertTrue(offers)
        self.assertTrue(all(c["tier"] == 1 for c in offers))
        state["room"] = 60
        offers = eh.roll_trial_cards(p, positive=False, count=6)
        self.assertTrue(all(1 <= c["tier"] <= 4 for c in offers))

    def test_same_kind_different_tiers_stack(self):
        p = make_player()
        state = eh.ensure_eh_state(p)
        tpl = next(t for t in eh.NEGATIVE_CARDS if t["id"] == "mending_roil")
        eh.apply_negative_card(p, eh._build_card(tpl, 1, False, 12))
        eh.apply_negative_card(p, eh._build_card(tpl, 2, False, 30))
        self.assertEqual(len(state["negative_cards"]), 2)
        mods = eh.get_enemy_mods(p)
        self.assertAlmostEqual(mods["regen"],
                               tpl["values"][0] + tpl["values"][1])

    def test_exact_duplicate_card_is_a_no_op(self):
        p = make_player()
        state = eh.ensure_eh_state(p)
        tpl = next(t for t in eh.NEGATIVE_CARDS if t["id"] == "marrow")
        eh.apply_negative_card(p, eh._build_card(tpl, 1, False, 12))
        eh.apply_negative_card(p, eh._build_card(tpl, 1, False, 12))
        self.assertEqual(len(state["negative_cards"]), 1)

    def test_unpicked_low_tier_surfaces_late(self):
        p = make_player()
        state = eh.ensure_eh_state(p)
        state["room"] = 60
        # Claim every card except Mending Roil T1
        for tpl in eh.NEGATIVE_CARDS:
            for tier in (1, 2, 3, 4):
                if tpl["id"] == "mending_roil" and tier == 1:
                    continue
                eh.apply_negative_card(p, eh._build_card(tpl, tier, False, 60))
        offers = eh.roll_trial_cards(p, positive=False, count=6)
        self.assertEqual(len(offers), 1)
        self.assertEqual((offers[0]["id"], offers[0]["tier"]),
                         ("mending_roil", 1))

    def test_positive_cards_stack_on_roster(self):
        p = make_player(allies=[make_ally()])
        eh.ensure_eh_state(p)
        tpl = next(t for t in eh.POSITIVE_CARDS if t["id"] == "unity")
        eh.apply_positive_card(p, eh._build_card(tpl, 1, True, 10))
        eh.apply_positive_card(p, eh._build_card(tpl, 2, True, 40))
        state = eh.ensure_eh_state(p)
        self.assertEqual(len(state["positive_cards"]), 2)
        hits = sorted(b["value"] for b in p["active_buffs"]
                      if b.get("source") == eh.EH_SOURCE
                      and b.get("label") == "Unity")
        self.assertEqual(hits, [tpl["effects"][0]["values"][0],
                                tpl["effects"][0]["values"][1]])

    def test_deck_exhausts_at_full_ladder(self):
        p = make_player()
        state = eh.ensure_eh_state(p)
        state["room"] = 60
        for tpl in eh.NEGATIVE_CARDS:
            for tier in (1, 2, 3, 4):
                eh.apply_negative_card(p, eh._build_card(tpl, tier, False, 60))
        self.assertEqual(eh.roll_trial_cards(p, positive=False), [])

    def test_legacy_exact_duplicates_collapse(self):
        p = make_player()
        state = eh.ensure_eh_state(p)
        state["negative_cards"] = [
            {"id": "marrow", "tier": 2},
            {"id": "marrow", "tier": 2},
            {"id": "marrow", "tier": 3},
        ]
        eh.ensure_eh_state(p)
        tiers = sorted(c["tier"] for c in state["negative_cards"])
        self.assertEqual(tiers, [2, 3])

    def test_positive_trial_every_fifteen(self):
        import event_horizon_rooms as ehr
        p = make_player()
        state = eh.ensure_eh_state(p)
        for room, expected in ((10, "trial_neg"), (15, "trial_pos"),
                               (20, "trial_neg"), (30, "trial_pos")):
            with self.subTest(room=room):
                state["room"] = room
                state["trial_done_for"] = 0
                self.assertEqual(ehr.generate_room(p)["type"], expected)


class TestJoker(unittest.TestCase):
    """The 22 Major Arcana hand model (2026-10-08): deal 2, keep 1, cap 7."""

    _ENTRY_DRAWBACKS = ("damage_taken_up", "slow", "damage_boost",
                        "defense_pct", "crit_chance", "eh_ele_dmg",
                        "regen_pct", "stat")
    _BEHAVIOURAL_EFFECTS = ("flask_double", "world_suppress", "cheat_death",
                            "lifesteal", "cooldown_down",
                            "debuff_duration_down", "initiative",
                            "crit_damage", "round_pulse", "debuff_mirror",
                            "reflect", "kill_heal")
    @staticmethod
    def _card(joker_id):
        return next(c for c in eh.JOKER_CARDS if c["id"] == joker_id)

    def test_deal_is_two_distinct_unowned_ready_faces(self):
        p = make_player()
        eh.ensure_eh_state(p)
        faces = eh.deal_joker_faces(p)
        self.assertEqual(len(faces), 2)
        self.assertEqual(len({f["id"] for f in faces}), 2)
        for f in faces:
            self.assertTrue(f.get("ready"))
        # All 22 faces are ready — the whole spread is dealable.
        self.assertEqual(len(eh.available_joker_faces(p)),
                         len(eh.JOKER_CARDS))

    def test_hand_cap_and_throw(self):
        p = make_player()
        eh.ensure_eh_state(p)
        ready = [c for c in eh.JOKER_CARDS if c.get("ready")]
        for card in ready[:eh.EH_JOKER_HAND_CAP]:
            eh.apply_joker(p, card)
        self.assertTrue(eh.joker_hand_full(p))
        extra = ready[eh.EH_JOKER_HAND_CAP]
        msg = eh.apply_joker(p, extra)
        self.assertIn("hand is full", msg)
        first = eh.owned_jokers(p)[0]
        eh.apply_joker(p, extra, replace=first)
        ids = eh.owned_joker_ids(p)
        self.assertIn(extra["id"], ids)
        self.assertNotIn(first["id"], ids)
        self.assertEqual(len(eh.owned_jokers(p)), eh.EH_JOKER_HAND_CAP)
        # The thrown arcana's entries left with it.
        self.assertFalse(any(e.get("label") == first["name"]
                             for e in p["active_buffs"] + p["active_debuffs"]))

    def test_thrown_face_returns_to_deck(self):
        p = make_player()
        eh.ensure_eh_state(p)
        card = self._card("joker_chariot")
        eh.apply_joker(p, card)
        self.assertNotIn(card["id"],
                         {f["id"] for f in eh.available_joker_faces(p)})
        eh.discard_joker(p, eh.owned_jokers(p)[0])
        self.assertIn(card["id"],
                      {f["id"] for f in eh.available_joker_faces(p)})

    def test_ready_faces_apply_and_strip(self):
        for card in [c for c in eh.JOKER_CARDS if c.get("ready")]:
            with self.subTest(card=card["id"]):
                p = make_player(allies=[make_ally()])
                eh.ensure_eh_state(p)
                eh.apply_joker(p, card)
                name = card["name"]
                effects = [e for e in card.get("effects", [])
                           if e.get("type") not in self._BEHAVIOURAL_EFFECTS]
                for eff in effects:
                    who = eff.get("actors", "all")
                    actors = ([p] + p["allies"] if who == "all"
                              else p["allies"] if who == "allies" else [p])
                    for actor in actors:
                        self.assertTrue(
                            any(b.get("label") == name
                                and b.get("type") == eff["type"]
                                for b in actor["active_buffs"]),
                            f"{card['id']} effect missing on roster")
                        if who == "allies":
                            self.assertFalse(
                                any(b.get("label") == name
                                    and b.get("value") == eff["value"]
                                    for b in p["active_buffs"]))
                for draw in eh._joker_drawbacks(card):
                    if draw.get("type") not in self._ENTRY_DRAWBACKS:
                        continue
                    who = draw.get("actors", "all")
                    actors = ([p] + p["allies"] if who == "all"
                              else p["allies"] if who == "allies" else [p])
                    for actor in actors:
                        pool = (actor["active_debuffs"]
                                if draw["type"] in ("damage_taken_up", "slow")
                                else actor["active_buffs"])
                        self.assertTrue(any(e.get("label") == name
                                            for e in pool),
                                        f"{card['id']} drawback missing")
                # strip removes everything; restore re-attaches
                eh.strip_event_horizon_effects(p)
                for actor in [p] + p["allies"]:
                    self.assertFalse(
                        any(e.get("label") == name
                            for e in actor["active_buffs"]
                            + actor["active_debuffs"]))
                eh.restore_event_horizon_effects(p)
                expected_entries = bool(effects) or any(
                    d.get("type") in self._ENTRY_DRAWBACKS
                    for d in eh._joker_drawbacks(card))
                if expected_entries:
                    restored = [e for e in
                                (p["active_buffs"] + p["active_debuffs"])
                                if e.get("label") == name]
                    self.assertTrue(restored,
                                    f"{card['id']} restore missing")

    def test_off_deck_no_entropy_no_payout(self):
        p = make_player(allies=[make_ally()])
        state = eh.ensure_eh_state(p)
        state["room"] = 25
        eh.sync_entropy(p)
        before_entropy = state["entropy"]
        before_payout = eh.compute_payout(p)
        msg = eh.apply_joker(p)          # default = Strength
        self.assertIn("The Joker is played", msg)
        for actor in [p] + p["allies"]:
            self.assertTrue(any(b.get("label") == "Strength"
                                for b in actor["active_buffs"]))
            self.assertTrue(any(d.get("type") == "slow"
                                and d.get("label") == "Strength"
                                for d in actor["active_debuffs"]))
        # Off-deck: no Entropy, no payout weight
        self.assertEqual(state["entropy"], before_entropy)
        self.assertEqual(eh.compute_payout(p), before_payout)
        self.assertEqual(len(state["joker_cards"]), 1)

    def test_world_suppresses_drawbacks_and_closes_deal(self):
        p = make_player()
        eh.ensure_eh_state(p)
        eh.apply_joker(p, self._card("joker_chariot"))
        self.assertTrue(any(d.get("type") == "damage_taken_up"
                            for d in p["active_debuffs"]))
        eh.apply_joker(p, self._card("joker_world"))
        self.assertFalse(any(d.get("type") == "damage_taken_up"
                             for d in p["active_debuffs"]))
        self.assertTrue(any(b.get("label") == "The Chariot"
                            for b in p["active_buffs"]))  # boost stays
        self.assertIn("deal is closed",
                      eh.apply_joker(p, self._card("joker_devil")))
        self.assertFalse(eh.joker_drawbacks_active(p, "joker_chariot"))
        # The restore path keeps the suppression.
        eh.strip_event_horizon_effects(p)
        eh.restore_event_horizon_effects(p)
        self.assertFalse(any(d.get("type") == "damage_taken_up"
                             for d in p["active_debuffs"]))

    def test_tower_doubles_flasks_and_sets_drain(self):
        p = make_player()
        state = eh.ensure_eh_state(p)
        state["room"] = 30
        base = eh.roll_flask(30, tier=4, kind="fervor")
        rec1 = eh.apply_flask(p, p, dict(base))
        self.assertAlmostEqual(rec1["effect"]["value"], base["value"])
        eh.apply_joker(p, self._card("joker_tower"))
        second = eh.roll_flask(30, tier=4, kind="fervor")
        rec2 = eh.apply_flask(p, p, dict(second))
        self.assertAlmostEqual(rec2["effect"]["value"], second["value"] * 2)
        self.assertIn("\u00d72", rec2["label"])
        for _ in range(3):
            eh.apply_flask(p, p, dict(eh.roll_flask(30, tier=4, kind="fervor")))
        drains = [d for d in p["active_debuffs"]
                  if d.get("type") == "eh_tower_drain"]
        self.assertEqual(len(drains), 1)
        self.assertAlmostEqual(drains[0]["value"], 0.02)

    def test_moon_battle_start_gamble(self):
        p = make_player()
        state = eh.ensure_eh_state(p)
        p["_eh_in_run"] = True
        state["run_active"] = True
        eh.apply_joker(p, self._card("joker_moon"))
        applied = eh.apply_joker_battle_start(p)
        self.assertEqual(applied, 1)
        labelled = [e for e in p["active_buffs"] + p["active_debuffs"]
                    if e.get("label") == "The Moon"]
        self.assertGreaterEqual(len(labelled), 2)

    def test_devil_shop_and_economy_multipliers(self):
        from event_horizon_rooms import _shop_flask_price
        p = make_player()
        eh.ensure_eh_state(p)
        self.assertEqual(eh.joker_shop_multiplier(p), 1.0)
        eh.apply_joker(p, self._card("joker_devil"))
        self.assertAlmostEqual(eh.joker_shop_multiplier(p), 1.2)
        self.assertEqual(_shop_flask_price(5, p), int((20 + 100) * 1.2))
        eh.apply_joker(p, self._card("joker_temperance"))
        eh.apply_joker(p, self._card("joker_hermit"))
        gold, mote = eh.joker_economy_multipliers(p)
        self.assertAlmostEqual(gold, 0.5)
        self.assertAlmostEqual(mote, 0.75 * 0.5)
        self.assertEqual(eh.apply_mote_multiplier(p, 40), 15)

    def test_emperor_save_once_per_battle(self):
        from combat.status_effects import try_consume_death_ward
        p = make_player()
        state = eh.ensure_eh_state(p)
        p["_eh_in_run"] = True
        state["run_active"] = True
        eh.apply_joker(p, self._card("joker_emperor"))
        self.assertTrue(p.get("_eh_joker_emperor"))
        eh.apply_joker_battle_start(p)      # battle 1 reset
        p["current_hp"] = 0
        self.assertTrue(try_consume_death_ward(p))
        self.assertEqual(p["current_hp"], 1)
        self.assertTrue(any(d.get("type") == "silence"
                            for d in p["active_debuffs"]))
        # Once per battle only.
        p["current_hp"] = 0
        self.assertFalse(try_consume_death_ward(p))
        # The next battle resets it.
        eh.apply_joker_battle_start(p)
        p["current_hp"] = 0
        self.assertTrue(try_consume_death_ward(p))
        # Strip clears the flag for good.
        eh.strip_event_horizon_effects(p)
        self.assertFalse(p.get("_eh_joker_emperor"))

    def test_batch2_flags_lifecycle(self):
        p = make_player()
        eh.ensure_eh_state(p)
        for jid in ("joker_death", "joker_fool", "joker_priestess",
                    "joker_hierophant", "joker_justice", "joker_hanged_man",
                    "joker_star", "joker_sun", "joker_judgement"):
            eh.apply_joker(p, self._card(jid))
        self.assertTrue(p.get("_eh_joker_star"))
        self.assertGreater(p.get("_eh_joker_lifesteal", 0), 0)
        self.assertTrue(p.get("_eh_joker_skip_r1"))
        self.assertTrue(p.get("_eh_joker_priestess"))
        self.assertAlmostEqual(p.get("_eh_joker_priestess_pen"), 0.5)
        eh.strip_event_horizon_effects(p)
        for key in ("_eh_joker_star", "_eh_joker_lifesteal",
                    "_eh_joker_skip_r1", "_eh_joker_miss",
                    "_eh_joker_priestess",
                    "_eh_joker_priestess_pen"):
            self.assertFalse(p.get(key), key)

    def test_fool_miss_and_initiative(self):
        from unittest import mock
        p = make_player()
        eh.ensure_eh_state(p)
        eh.apply_joker(p, self._card("joker_fool"))
        self.assertEqual(eh.joker_initiative_bonus(p), 2)
        with mock.patch.object(eh.random, "random", return_value=0.0):
            self.assertTrue(eh.joker_attack_missed(p))
        with mock.patch.object(eh.random, "random", return_value=0.99):
            self.assertFalse(eh.joker_attack_missed(p))

    def test_hierophant_and_sun_modifiers(self):
        p = make_player()
        eh.ensure_eh_state(p)
        self.assertEqual(eh.joker_damage_multiplier(p, "basic"), 1.0)
        eh.apply_joker(p, self._card("joker_hierophant"))
        self.assertAlmostEqual(eh.joker_damage_multiplier(p, "skill"), 1.25)
        self.assertAlmostEqual(eh.joker_damage_multiplier(p, "basic"), 0.75)
        self.assertEqual(eh.joker_crit_modifier(p, True, 100), 100)
        eh.apply_joker(p, self._card("joker_sun"))
        self.assertEqual(eh.joker_crit_modifier(p, True, 100), 130)
        self.assertEqual(eh.joker_crit_modifier(p, False, 100), 85)

    def test_priestess_flat_cooldown_and_basic_pen(self):
        from unittest import mock
        p = make_player()
        eh.ensure_eh_state(p)
        eh.apply_joker(p, self._card("joker_priestess"))
        self.assertAlmostEqual(eh.joker_damage_multiplier(p, "basic"), 0.5)
        self.assertAlmostEqual(eh.joker_damage_multiplier(p, "skill"), 1.0)
        with mock.patch("combat.skills.get_class_skill_map",
                        return_value={"slash": {"cooldown": 5}}):
            from combat.skills import set_skill_cooldown
            msg = set_skill_cooldown(p, "slash")
        self.assertEqual(p["skill_cooldowns"]["slash"], 3)
        self.assertIn("−2", msg or "")

    def test_justice_debuff_mirror(self):
        from combat import status_effects as se
        p = make_player(allies=[make_ally()])
        state = eh.ensure_eh_state(p)
        p["_eh_in_run"] = True
        state["run_active"] = True
        eh.apply_joker(p, self._card("joker_justice"))
        ally = p["allies"][0]
        # Drawback: a party member's own debuff bounces back at them.
        foe = {"name": "Foe", "hp": 100, "max_hp": 100}
        before = eh.debuff_signature([foe])
        se.apply_poison(foe, 5, 3)
        msgs = eh.joker_mirror_debuffs(p, ally, [foe], before)
        self.assertTrue(msgs)
        self.assertTrue(any(d.get("type") == "poison"
                            for d in ally["active_debuffs"]))
        # Once per type per action — an AoE burn mires the caster once.
        foe_b = {"name": "Foe B", "hp": 80, "max_hp": 80}
        foe_c = {"name": "Foe C", "hp": 80, "max_hp": 80}
        before = eh.debuff_signature([foe_b, foe_c])
        se.apply_burn(foe_b, tier=2, duration=2)
        se.apply_burn(foe_c, tier=2, duration=2)
        eh.joker_mirror_debuffs(p, ally, [foe_b, foe_c], before)
        self.assertEqual(sum(1 for d in ally["active_debuffs"]
                             if d.get("type") == "burn"), 1)
        # Boost: an enemy's debuff is inflicted back on the enemy.
        before = eh.debuff_signature([p])
        se.apply_weaken(p, penalty_pct=0.15, duration=2)
        msgs = eh.joker_mirror_debuffs(p, foe, [p], before)
        self.assertTrue(msgs)
        self.assertTrue(any(d.get("type") == "weaken"
                            for d in foe["active_debuffs"]))
        # The World lifts the party's backfire — the enemy still pays.
        eh.apply_joker(p, self._card("joker_world"))
        p["active_debuffs"] = []
        before = eh.debuff_signature([foe_b])
        se.apply_poison(foe_b, 5, 3)
        self.assertFalse(eh.joker_mirror_debuffs(p, ally, [foe_b], before))
        before = eh.debuff_signature([p])
        se.apply_weaken(p, penalty_pct=0.15, duration=2)
        eh.joker_mirror_debuffs(p, foe_b, [p], before)
        self.assertTrue(any(d.get("type") == "weaken"
                            for d in foe_b["active_debuffs"]))

    def test_judgement_round_pulse(self):
        p = make_player()
        state = eh.ensure_eh_state(p)
        p["_eh_in_run"] = True
        state["run_active"] = True
        eh.apply_joker(p, self._card("joker_judgement"))
        enemies = [{"name": "A", "hp": 100, "max_hp": 100},
                   {"name": "B", "hp": 40, "max_hp": 50}]
        p["current_hp"] = 100
        msgs = eh.joker_judgement_pulse(p, enemies, 1)
        self.assertEqual(enemies[0]["hp"], 80)
        self.assertEqual(enemies[1]["hp"], 30)
        self.assertEqual(p["current_hp"], 100)   # party safe before round 3
        self.assertEqual(len(msgs), 1)
        # Round 3 — the party bleeds 20% max HP too, never below 1.
        msgs = eh.joker_judgement_pulse(p, enemies, 3)
        self.assertLess(p["current_hp"], 100)
        self.assertEqual(len(msgs), 2)
        p["current_hp"] = 1
        eh.joker_judgement_pulse(p, enemies, 3)
        self.assertGreaterEqual(p["current_hp"], 1)
        # The World lifts the party side; the enemy pulse keeps falling.
        eh.apply_joker(p, self._card("joker_world"))
        p["current_hp"] = 100
        before_a = enemies[0]["hp"]
        eh.joker_judgement_pulse(p, enemies, 3)
        self.assertEqual(p["current_hp"], 100)
        self.assertLess(enemies[0]["hp"], before_a)

    def test_judgement_and_justice_gated_to_active_run(self):
        """Raw state reads must not leak outside the rift (2026-10-15).

        Joker records persist in state while a run is suspended and have no
        roster entry to strip — Judgement used to pulse (and Justice mirror)
        in overworld fights until the run was wiped.
        """
        from combat import status_effects as se
        p = make_player(allies=[make_ally()])
        state = eh.ensure_eh_state(p)
        eh.apply_joker(p, self._card("joker_judgement"))
        eh.apply_joker(p, self._card("joker_justice"))
        # Suspended run: records stay in state, `_eh_in_run` is gone.
        state["run_active"] = True
        p.pop("_eh_in_run", None)
        enemies = [{"name": "A", "hp": 100, "max_hp": 100}]
        p["current_hp"] = 100
        self.assertEqual(eh.joker_judgement_pulse(p, enemies, 3), [])
        self.assertEqual(enemies[0]["hp"], 100)
        self.assertEqual(p["current_hp"], 100)
        ally = p["allies"][0]
        foe = {"name": "Foe", "hp": 100, "max_hp": 100}
        before = eh.debuff_signature([foe])
        se.apply_poison(foe, 5, 3)
        self.assertEqual(eh.joker_mirror_debuffs(p, ally, [foe], before), [])
        self.assertFalse(any(d.get("type") == "poison"
                             for d in ally["active_debuffs"]))
        # Back inside the rift both hooks come alive again.
        p["_eh_in_run"] = True
        self.assertTrue(eh.joker_judgement_pulse(p, enemies, 3))
        foe2 = {"name": "Foe2", "hp": 80, "max_hp": 80}
        before = eh.debuff_signature([foe2])
        se.apply_poison(foe2, 5, 3)
        self.assertTrue(eh.joker_mirror_debuffs(p, ally, [foe2], before))

    def test_star_shortens_debuffs(self):
        from combat.status_effects import tick_player_debuffs
        p = make_player()
        eh.ensure_eh_state(p)
        eh.apply_joker(p, self._card("joker_star"))
        # A 2-turn debuff dies in a single tick (star step + normal tick).
        p["active_debuffs"] = [{"type": "poison", "damage": 3,
                                "remaining": 2}]
        tick_player_debuffs(p)
        self.assertFalse(any(d.get("type") == "poison"
                             for d in p["active_debuffs"]))
        # A 1-turn debuff is ended by the Star step itself (message fires).
        p["active_debuffs"] = [{"type": "poison", "damage": 3,
                                "remaining": 1}]
        msgs, _died = tick_player_debuffs(p)
        self.assertFalse(any(d.get("type") == "poison"
                             for d in p["active_debuffs"]))
        self.assertTrue(any("Star" in m for m in msgs))

    def test_weakness_gate_flag_lifecycle(self):
        p = make_player()
        eh.ensure_eh_state(p)
        eh.apply_joker(p, self._card("joker_magician"))
        self.assertTrue(p.get("_eh_joker_weakness_gate"))
        eh.discard_joker(p, eh.owned_jokers(p)[0])
        self.assertFalse(p.get("_eh_joker_weakness_gate"))
        eh.apply_joker(p, self._card("joker_magician"))
        eh.strip_event_horizon_effects(p)
        self.assertFalse(p.get("_eh_joker_weakness_gate"))


class TestVesperGreetings(unittest.TestCase):
    """Arrival-scene idle dialogue (facilities/event_horizon_intro)."""

    @staticmethod
    def _greet(player, state, room, suspended=False):
        from facilities.event_horizon_intro import plan_vesper_greeting
        return "\n".join(plan_vesper_greeting(player, state, room, suspended))

    def test_first_arrival(self):
        p = make_player()
        state = eh.ensure_eh_state(p)
        text = self._greet(p, state, 0)
        self.assertIn("You came. Good.", text)
        self.assertEqual(p["eh_visits"], 1)
        self.assertEqual(p.get("eh_vesper_milestone", 0), 0)

    def test_idle_rotation_varies(self):
        p = make_player()
        state = eh.ensure_eh_state(p)
        self._greet(p, state, 0)              # visit 1: first arrival
        second = self._greet(p, state, 0)     # visit 2
        third = self._greet(p, state, 0)      # visit 3
        self.assertNotIn("You came. Good.", second)
        self.assertNotEqual(second, third)
        self.assertEqual(p["eh_visits"], 3)

    def test_suspended_idle_reminder(self):
        p = make_player()
        state = eh.ensure_eh_state(p)
        self._greet(p, state, 0)              # burn the first visit
        text = self._greet(p, state, 12, suspended=True)
        self.assertIn("room 12", text)

    def test_milestone_r25_once(self):
        p = make_player()
        state = eh.ensure_eh_state(p)
        state["run_active"] = True
        state["room"] = 25
        first = self._greet(p, state, 25, suspended=True)
        self.assertIn("Twenty-five", first)
        self.assertIn("room 25", first)      # suspended continuation
        self.assertEqual(p["eh_vesper_milestone"], 25)
        again = self._greet(p, state, 25, suspended=True)
        self.assertNotIn("Twenty-five", again)   # acknowledged once
        self.assertEqual(p["eh_vesper_milestone"], 25)

    def test_trophy_milestone_lines(self):
        for room, needle in ((50, "coin"), (75, "Seventy-five"),
                             (100, "hundred")):
            with self.subTest(room=room):
                p = make_player()
                state = eh.ensure_eh_state(p)
                text = self._greet(p, state, room)
                self.assertIn(needle, text)
                self.assertEqual(p["eh_vesper_milestone"], room)

    def test_beating_root_milestone(self):
        p = make_player()
        state = eh.ensure_eh_state(p)
        state["best_room"] = 130
        text = self._greet(p, state, 0)
        self.assertIn("roots", text)
        self.assertEqual(p["eh_vesper_milestone"], 125)

    def test_old_save_milestone_fires_once(self):
        # Migration: best_room already past a mark, no visit counter yet.
        p = make_player()
        state = eh.ensure_eh_state(p)
        state["best_room"] = 80
        text = self._greet(p, state, 0)
        self.assertIn("Seventy-five", text)
        self.assertEqual(p["eh_vesper_milestone"], 75)
        self.assertEqual(p["eh_visits"], 1)
        again = self._greet(p, state, 0)
        self.assertNotIn("Seventy-five", again)

    def test_only_latest_milestone_per_visit(self):
        p = make_player()
        state = eh.ensure_eh_state(p)
        state["best_room"] = 150
        first = self._greet(p, state, 150)
        self.assertIn("roots", first)        # r150 lands in the >100 lines
        self.assertEqual(p["eh_vesper_milestone"], 150)
        second = self._greet(p, state, 150)
        self.assertNotIn("roots", second)


class TestBossRush(unittest.TestCase):
    """Boss Rush — pool gating, flat scaling, room flow, records (§6.4)."""

    KILLS = ["broodmother_vileheart", "black_silence", "white_knight"]

    def _ready_player(self, **over):
        """Eligible: 3+ overworld kills, best_room 50+, max_floor 40+."""
        p = make_player(defeated_superbosses=list(self.KILLS),
                        max_floor=40, **over)
        eh.ensure_eh_state(p)["best_room"] = 50
        return p

    def test_pool_skips_undefeated_and_keeps_ramp_order(self):
        p = make_player(defeated_superbosses=["wl_mary_sue",
                                              "broodmother_vileheart"])
        pool = eh.build_boss_rush_pool(p)
        # Undefeated bosses are skipped; survivors follow roster (level) order.
        self.assertEqual([b["id"] for b in pool],
                         ["broodmother_vileheart", "wl_mary_sue"])
        empty = eh.build_boss_rush_pool(make_player())
        self.assertEqual(empty, [])

    def test_requirements_gating(self):
        p = make_player(defeated_superbosses=["broodmother_vileheart"])
        state = eh.ensure_eh_state(p)
        ok, reasons = eh.boss_rush_requirements(p)
        self.assertFalse(ok)
        self.assertEqual(len(reasons), 3)          # pool + depth + world
        p["defeated_superbosses"] = list(self.KILLS)
        p["max_floor"] = 40
        state["best_room"] = 50
        ok, reasons = eh.boss_rush_requirements(p)
        self.assertTrue(ok, reasons)
        # A suspended/active run hides the arrival offer entirely.
        state["run_active"] = True
        self.assertFalse(eh.boss_rush_available(p))
        state["run_active"] = False
        self.assertTrue(eh.boss_rush_available(p))

    def test_begin_rush_queue_and_level(self):
        p = self._ready_player()
        ok, reasons = eh.begin_rush(p, "solmere")
        self.assertTrue(ok, reasons)
        state = eh.ensure_eh_state(p)
        self.assertTrue(state["rush_mode"])
        self.assertEqual(state["rush_queue"],
                         ["broodmother_vileheart", "black_silence",
                          "white_knight"])
        self.assertEqual(state["rush_total"], 3)
        # 40 + 5×3 + 10×1 (White Knight is Pandemonium) = 65
        self.assertEqual(state["rush_level"], 65)
        self.assertEqual(eh.rush_level(p), 65)
        # Rejected while a run is turning; rejected below the gates.
        p2 = self._ready_player()
        eh.ensure_eh_state(p2)["run_active"] = True
        ok, reasons = eh.begin_rush(p2, "solmere")
        self.assertFalse(ok)
        self.assertIn("already turning", reasons[0])
        p3 = make_player(defeated_superbosses=["broodmother_vileheart"])
        ok, reasons = eh.begin_rush(p3, "solmere")
        self.assertFalse(ok)

    def test_flat_stat_scaling_overrides_room_scaling(self):
        p = self._ready_player()
        eh.begin_rush(p, "solmere")
        p["_eh_in_run"] = True
        state = eh.ensure_eh_state(p)
        state["room"] = 50               # deep run: room scaling would apply
        enemy = {"key": "broodmother_vileheart", "level": 24, "hp": 100,
                 "max_hp": 100, "str_mod": 10, "con_mod": 10, "dex_mod": 10}
        eh.apply_enemy_scaling(enemy, p)
        mult = eh.rush_stat_mult(p)      # 1.25 + 0.03×(65−40) = 2.0
        self.assertAlmostEqual(mult, 2.0)
        self.assertEqual(enemy["level"], 65)          # formula beats original 24
        self.assertEqual(enemy["hp"], 200)            # flat — no room scaling
        self.assertEqual(enemy["max_hp"], 200)
        self.assertEqual(enemy["str_mod"], 20)
        self.assertTrue(enemy["_eh_rush"])
        # A boss already above the formula level keeps its own (never lower).
        high = {"key": "wl_mary_sue", "level": 70, "hp": 10, "max_hp": 10,
                "str_mod": 1, "con_mod": 1, "dex_mod": 1}
        eh.apply_enemy_scaling(high, p)
        self.assertEqual(high["level"], 70)

    def test_entropy_stays_flat_in_rush(self):
        p = self._ready_player()
        eh.begin_rush(p, "solmere")
        p["_eh_in_run"] = True
        state = eh.ensure_eh_state(p)
        state["room"] = 30
        eh.sync_entropy(p)
        self.assertEqual(eh.get_entropy_total(p), 0)
        state["rush_mode"] = False
        eh.sync_entropy(p)
        self.assertGreater(eh.get_entropy_total(p), 0)

    def test_rush_room_play_and_fled_restart(self):
        p = self._ready_player()
        eh.begin_rush(p, "solmere")
        p["_eh_in_run"] = True
        from event_horizon_rooms import generate_rush_room, play_room, room_title

        room = generate_rush_room(p)
        self.assertEqual(room["type"], "boss_rush")
        self.assertEqual(room["number"], 1)
        self.assertEqual(room["total"], 3)
        self.assertEqual(room["boss"]["id"], "broodmother_vileheart")
        self.assertIn("BOSS RUSH 1/3", room_title(room))

        calls = []

        def override(spec, floor):
            calls.append(spec)
            return "victory"

        p["current_hp"] = 11                     # low HP — must not heal
        result = play_room(p, room, None, superboss_override=override)
        self.assertEqual(result, "cleared")
        self.assertEqual(calls[0]["boss_id"], "broodmother_vileheart")
        self.assertEqual(calls[0]["index"], 1)
        self.assertEqual(calls[0]["total"], 3)
        # Pure linear progress: no motes, no healing between echoes.
        self.assertEqual(eh.ensure_eh_state(p)["motes"], 0)
        self.assertEqual(p["current_hp"], 11)   # untouched (no catch-breath)

        # Flee is blocked — the fight restarts until a real result lands.
        calls.clear()

        def flee_once(spec, floor):
            calls.append(spec)
            return "fled" if len(calls) == 1 else "victory"

        result = play_room(p, room, None, superboss_override=flee_once)
        self.assertEqual(result, "cleared")
        self.assertEqual(len(calls), 2)
        self.assertEqual(eh.ensure_eh_state(p)["motes"], 0)
        self.assertEqual(p["current_hp"], 11)   # no heal here either

        # Death passes straight through (dungeon loop routes the EH death).
        result = play_room(p, room, None,
                           superboss_override=lambda spec, floor: "dead")
        self.assertEqual(result, "dead")

    def test_rush_done_on_empty_queue(self):
        p = self._ready_player()
        eh.begin_rush(p, "solmere")
        eh.ensure_eh_state(p)["rush_queue"] = []
        from event_horizon_rooms import generate_rush_room
        room = generate_rush_room(p)
        self.assertEqual(room["type"], "rush_done")

    def test_clear_run_preserves_rush_records(self):
        p = self._ready_player()
        state = eh.ensure_eh_state(p)
        state["best_room"] = 0
        state["rush_clears"] = 2
        state["rush_best"] = 7
        state["rush_mode"] = True
        state["rush_queue"] = ["black_silence"]
        state["room"] = 4
        eh.clear_run(p)
        state = eh.ensure_eh_state(p)
        self.assertEqual(state["rush_clears"], 2)
        self.assertEqual(state["rush_best"], 7)
        self.assertFalse(state["rush_mode"])
        self.assertEqual(state["rush_queue"], [])
        self.assertEqual(state["best_room"], 4)

    def test_legacy_ledger_backfill(self):
        # Old saves: kills recorded before the ledger existed (Wonderland
        # flags, White Knight flag, pool:<id> awakening sources) are rebuilt
        # into defeated_superbosses so the rush pool isn't starved.
        from character import _backfill_superboss_ledger
        p = make_player()
        p["defeated_superbosses"] = ["queen_of_mirrors_sylvana"]
        p.update({
            "wl_boss_defeated_queen_of_hearts": True,
            "wl_boss_defeated_big_bad_wolf": True,
            "wl_boss_defeated_wicked_witch": True,
            "wl_boss_defeated_jabberwock": True,
            "wl_boss_defeated_mary_sue": True,
            "boss_defeated_white_knight": True,
            "awakening_shard_sources": ["wl:10", "pool:black_silence"],
        })
        _backfill_superboss_ledger(p)
        for boss_id in ("wl_queen_of_hearts", "wl_big_bad_wolf",
                        "wl_wicked_witch", "wl_jabberwock", "wl_mary_sue",
                        "white_knight", "black_silence"):
            self.assertIn(boss_id, p["defeated_superbosses"])
        # Idempotent — a second pass adds nothing, never duplicates.
        before = list(p["defeated_superbosses"])
        _backfill_superboss_ledger(p)
        self.assertEqual(p["defeated_superbosses"], before)
        # The rebuilt ledger feeds a usable rush pool.
        pool_ids = [b["id"] for b in eh.build_boss_rush_pool(p)]
        self.assertIn("wl_mary_sue", pool_ids)
        self.assertIn("black_silence", pool_ids)

    def test_suspended_menu_offers_rush_with_collapse_confirm(self):
        from facilities import event_horizon_intro as ei

        p = self._ready_player()
        st = eh.ensure_eh_state(p)
        st["run_active"] = True
        st["room"] = 7

        answers = [2, 0]   # pick the Boss Rush option, then confirm collapse

        class _Stub:
            def __init__(self):
                self.calls = []

            def clear(self):
                pass

            def print(self, *a, **k):
                pass

            def pause(self, *a, **k):
                pass

            def menu(self, options, prompt="", **k):
                self.calls.append(list(options))
                return answers.pop(0)

        stub = _Stub()
        orig = ei.term
        ei.term = stub
        try:
            result = ei.event_horizon_arrival_service(p, "solmere")
        finally:
            ei.term = orig
        self.assertEqual(result, "boss_rush_fresh")
        self.assertTrue(any("Boss Rush" in opt for opt in stub.calls[0]),
                        stub.calls[0])

    def test_suspended_menu_hides_rush_below_gates(self):
        from facilities import event_horizon_intro as ei

        p = make_player()                       # no kills / depth: gates fail
        st = eh.ensure_eh_state(p)
        st["run_active"] = True
        st["room"] = 7

        answers = [3]   # no rush option: [resume, fresh, lore, leave] → leave

        class _Stub:
            def __init__(self):
                self.calls = []

            def clear(self):
                pass

            def print(self, *a, **k):
                pass

            def pause(self, *a, **k):
                pass

            def menu(self, options, prompt="", **k):
                self.calls.append(list(options))
                return answers.pop(0)

        stub = _Stub()
        orig = ei.term
        ei.term = stub
        try:
            result = ei.event_horizon_arrival_service(p, "solmere")
        finally:
            ei.term = orig
        self.assertEqual(result, "leave")
        self.assertFalse(any("Boss Rush" in opt for opt in stub.calls[0]),
                         stub.calls[0])

    def test_roster_entries_resolve(self):
        from resources.enemies import ENEMIES
        for boss in eh.BOSS_RUSH_ROSTER:
            with self.subTest(boss=boss["id"]):
                fn = eh.rush_boss_combat(boss)
                self.assertTrue(callable(fn))
                self.assertTrue(boss["keys"])
                for key in boss["keys"]:
                    self.assertIn(key, ENEMIES)
        # Ramp order: the roster must be sorted by the boss's original level.
        levels = [ENEMIES[b["keys"][0]]["level"] for b in eh.BOSS_RUSH_ROSTER]
        self.assertEqual(levels, sorted(levels))

    def test_summary_includes_rush_line(self):
        p = self._ready_player()
        eh.begin_rush(p, "solmere")
        state = eh.ensure_eh_state(p)
        state["room"] = 2
        state["rush_defeated"] = ["broodmother_vileheart", "black_silence"]
        summary = eh.build_run_summary(p, payout=0)
        self.assertTrue(any("Boss Rush" in ln and "2/3" in ln
                            for ln in summary["lines"]))
        self.assertEqual(summary["data"]["rush"]["felled"], 2)
        self.assertEqual(summary["data"]["rush"]["total"], 3)

    def test_rush_completion_payout_and_records(self):
        from unittest import mock
        import dungeon as dungeon_mod

        p = self._ready_player()
        eh.begin_rush(p, "solmere")
        p["_eh_in_run"] = True
        state = eh.ensure_eh_state(p)
        state["room"] = 3
        state["rush_queue"] = []
        state["rush_defeated"] = list(self.KILLS)
        state["motes"] = 120
        with mock.patch.object(dungeon_mod, "save_game", lambda pl: None):
            result = dungeon_mod._eh_rush_complete(p)
        self.assertEqual(result, "eh_rush_complete")
        state = eh.ensure_eh_state(p)
        self.assertEqual(state["rush_clears"], 1)
        self.assertEqual(state["rush_best"], 3)
        self.assertFalse(state["rush_mode"])
        # Payout (rooms 1-3 = 12+14+16) + full-circuit bonus (100 + 25×3).
        self.assertEqual(p["gold"], 42 + 175)
        self.assertIn("Boss Rush", "\n".join(
            p["_eh_last_summary"]["lines"]))


if __name__ == "__main__":
    unittest.main()
