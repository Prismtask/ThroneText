"""
tests/test_wild_dungeons.py — Wild Dungeons Phase 1 (foundation) tests.

Design: docs/wild_dungeon_design.md

Covers:
  - State init / legacy-save migration
  - Level band (max_floor ± 8, clamped 1-80)
  - Weekly spawn cycle (3-7 dungeons, throttle, idempotence)
  - Reward pool generation (size, rarity floor, valid item ids)
  - Marker placement (map bounds, city clearance, mutual spacing)
  - Nearest-city resolution
  - Expiry and completion bookkeeping
  - events.process_day_rollover integration
"""

import random
import unittest

from wild_dungeons import (
    ensure_wild_dungeon_state,
    get_active_dungeons,
    get_wild_dungeon,
    roll_dungeon_level,
    find_nearest_city,
    generate_reward_pool,
    expire_dungeons,
    maybe_spawn_cycle,
    complete_wild_dungeon,
    record_completion_event,
    build_journey_to_dungeon,
    offroad_segment,
    SPAWN_PER_CYCLE_MIN,
    SPAWN_PER_CYCLE_MAX,
    LEVEL_MIN,
    LEVEL_MAX,
    MIN_CITY_DIST,
    MIN_DUNGEON_DIST,
    WILD_OFFROAD_MIN_MINUTES,
    WILD_OFFROAD_MAX_MINUTES,
)
from resources.items import ITEMS
from resources.cities import CITIES
from resources.world_layout import map_bounds, city_node_centers


def make_player(day=1, max_floor=5):
    """Minimal player dict with the fields wild dungeons touch."""
    return {
        "day": day,
        "max_floor": max_floor,
        "daily_effects": {},
        "active_buffs": [],
    }


class WildDungeonTestCase(unittest.TestCase):
    """Base class: isolate the global RNG between tests."""

    def setUp(self):
        self._rng_state = random.getstate()

    def tearDown(self):
        random.setstate(self._rng_state)


# ═══════════════════════════════════════════════════════════════
# State init & migration
# ═══════════════════════════════════════════════════════════════

class TestStateInit(WildDungeonTestCase):

    def test_fresh_player_gets_state_block(self):
        player = make_player()
        state = ensure_wild_dungeon_state(player)
        self.assertEqual(state["active"], [])
        self.assertEqual(state["completed"], [])
        self.assertEqual(state["next_id"], 1)
        self.assertEqual(state["last_spawn_day"], 0)

    def test_legacy_save_migrates_missing_keys(self):
        """Old saves without the block (or with partial blocks) are repaired."""
        player = make_player(day=30, max_floor=12)
        state = ensure_wild_dungeon_state(player)
        self.assertEqual(state["active"], [])
        self.assertEqual(state["next_id"], 1)

        # Partial block: only 'active' present — missing keys backfilled.
        player["wild_dungeons"] = {"active": [{"id": "wild_1"}]}
        state = ensure_wild_dungeon_state(player)
        self.assertEqual(state["active"], [{"id": "wild_1"}])
        self.assertEqual(state["completed"], [])
        self.assertEqual(state["next_id"], 1)
        self.assertEqual(state["last_spawn_day"], 0)


# ═══════════════════════════════════════════════════════════════
# Level band
# ═══════════════════════════════════════════════════════════════

class TestLevelBand(WildDungeonTestCase):

    def test_band_low_floor(self):
        random.seed(11)
        for _ in range(300):
            level = roll_dungeon_level(make_player(max_floor=1))
            self.assertTrue(1 <= level <= 3, level)

    def test_band_mid_floor(self):
        random.seed(12)
        for _ in range(300):
            level = roll_dungeon_level(make_player(max_floor=20))
            self.assertTrue(12 <= level <= 28, level)

    def test_band_up_scales_at_low_floors(self):
        """The upward offset grows with progress: 2 + floor//3, cap +8."""
        random.seed(15)
        cases = {
            1: 3,    # +2
            4: 7,    # +3
            7: 11,   # +4
            10: 15,  # +5
            16: 23,  # +7
            18: 26,  # +8 (cap reached)
            30: 38,  # +8 still
        }
        for base, hi in cases.items():
            for _ in range(200):
                level = roll_dungeon_level(make_player(max_floor=base))
                self.assertTrue(1 <= level <= hi, (base, hi, level))
                # The −8 side always stays available
                self.assertGreaterEqual(level, max(1, base - 8))

    def test_band_clamps_at_cap(self):
        random.seed(13)
        for _ in range(300):
            level = roll_dungeon_level(make_player(max_floor=80))
            self.assertTrue(72 <= level <= 80, level)

    def test_band_clamps_above_cap(self):
        """max_floor beyond 80 clamps to the 72-80 range."""
        random.seed(14)
        for _ in range(300):
            level = roll_dungeon_level(make_player(max_floor=100))
            self.assertTrue(LEVEL_MIN <= level <= LEVEL_MAX, level)
            self.assertGreaterEqual(level, 72)


# ═══════════════════════════════════════════════════════════════
# Nearest city
# ═══════════════════════════════════════════════════════════════

class TestNearestCity(WildDungeonTestCase):

    def test_point_near_solmere(self):
        # Solmere node: (200,160)+center(60,19) = (260,179)
        self.assertEqual(find_nearest_city([265, 180]), "solmere")

    def test_point_near_isle_of_glass(self):
        # Isle of Glass node: (650,500)+center = (710,519)
        self.assertEqual(find_nearest_city([705, 515]), "isle_of_glass")


# ═══════════════════════════════════════════════════════════════
# Reward pool
# ═══════════════════════════════════════════════════════════════

class TestRewardPool(WildDungeonTestCase):

    def test_pool_size_and_valid_items(self):
        random.seed(21)
        for floors in (2, 4, 6):
            pool = generate_reward_pool(30, floors)
            self.assertEqual(len(pool), floors + 2)
            for entry in pool:
                self.assertIn(entry["item_id"], ITEMS)
                self.assertIn("rarity", entry)

    def test_top_item_rarity_floor(self):
        random.seed(22)
        # Level >= 25: top item is epic or legendary
        for level in (25, 40, 80):
            for _ in range(20):
                top = generate_reward_pool(level, 3)[0]
                self.assertIn(top["rarity"], ("epic", "legendary"))
        # Level < 25: top item is rare or better
        for level in (1, 10, 24):
            for _ in range(20):
                top = generate_reward_pool(level, 3)[0]
                self.assertIn(top["rarity"], ("rare", "epic", "legendary"))

    def test_top_item_is_equipment(self):
        random.seed(23)
        for _ in range(30):
            top = generate_reward_pool(30, 3)[0]
            self.assertEqual(ITEMS[top["item_id"]].get("type"), "equipment")


# ═══════════════════════════════════════════════════════════════
# Spawn cycle
# ═══════════════════════════════════════════════════════════════

class TestSpawnCycle(WildDungeonTestCase):

    def test_cycle_spawns_3_to_7_valid_dungeons(self):
        random.seed(31)
        player = make_player(day=14, max_floor=20)
        spawned, event = maybe_spawn_cycle(player)

        self.assertTrue(SPAWN_PER_CYCLE_MIN <= len(spawned) <= SPAWN_PER_CYCLE_MAX)
        self.assertIsNotNone(event)
        self.assertEqual(event["name"], "Strange Ruins Surfaced")

        state = player["wild_dungeons"]
        self.assertEqual(state["last_spawn_day"], 14)
        self.assertEqual(len(state["active"]), len(spawned))

        ids = [d["id"] for d in spawned]
        self.assertEqual(len(set(ids)), len(ids))  # unique ids

        x_min, y_min, x_max, y_max = map_bounds()
        centers = city_node_centers()
        positions = []
        for d in spawned:
            # Level band ± 8 around max_floor 20
            self.assertTrue(12 <= d["level"] <= 28, d["level"])
            self.assertTrue(2 <= d["total_floors"] <= 6)
            self.assertEqual(len(d["reward_pool"]), d["total_floors"] + 2)
            self.assertGreaterEqual(d["expire_day"], d["spawn_day"] + 3)

            # Position: inside bounds, clear of city nodes
            x, y = d["position"]
            self.assertTrue(x_min <= x <= x_max, (x, x_min, x_max))
            self.assertTrue(y_min <= y <= y_max, (y, y_min, y_max))
            for cx, cy in centers.values():
                self.assertGreaterEqual(
                    (x - cx) ** 2 + (y - cy) ** 2, MIN_CITY_DIST ** 2)
            positions.append((x, y))

            # Nearest city consistent with recompute
            self.assertEqual(d["nearest_city"], find_nearest_city(d["position"]))
            # Biome comes from the seed city
            self.assertEqual(
                d["biome"], CITIES[d["seed_city"]].get("biome", "temperate"))
            # Marker sits in the ring around its seed city
            cx, cy = city_node_centers()[d["seed_city"]]
            ring_dist = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            self.assertGreaterEqual(ring_dist, MIN_CITY_DIST - 1)
            self.assertLessEqual(ring_dist, 260 + 2)

        # Dungeons spawned this cycle keep their distance from each other
        for i, (x1, y1) in enumerate(positions):
            for x2, y2 in positions[i + 1:]:
                self.assertGreaterEqual(
                    (x1 - x2) ** 2 + (y1 - y2) ** 2, MIN_DUNGEON_DIST ** 2)

        # Journal got the spawn entry
        names = [e["name"] for e in player["journal"]["events"]]
        self.assertIn("Strange Ruins Surfaced", names)

    def test_cycle_throttle(self):
        random.seed(32)
        player = make_player(day=7, max_floor=5)
        spawned1, _ = maybe_spawn_cycle(player)
        self.assertTrue(len(spawned1) >= SPAWN_PER_CYCLE_MIN)

        # Same week: no second cycle
        spawned2, event2 = maybe_spawn_cycle(player)
        self.assertEqual(spawned2, [])
        self.assertIsNone(event2)

        # Next week: a new cycle rolls
        player["day"] = 14
        spawned3, _ = maybe_spawn_cycle(player)
        self.assertTrue(SPAWN_PER_CYCLE_MIN <= len(spawned3) <= SPAWN_PER_CYCLE_MAX)

    def test_cycle_skipped_multi_day_jump_still_rolls(self):
        """A long advance that skips the exact 7-day boundary still spawns."""
        random.seed(33)
        player = make_player(day=9, max_floor=5)  # jumped 1 → 9 in one advance
        spawned, _ = maybe_spawn_cycle(player)
        self.assertTrue(len(spawned) >= SPAWN_PER_CYCLE_MIN)
        self.assertEqual(player["wild_dungeons"]["last_spawn_day"], 9)


# ═══════════════════════════════════════════════════════════════
# Expiry & completion
# ═══════════════════════════════════════════════════════════════

class TestLifecycle(WildDungeonTestCase):

    def test_expiry_removes_overdue_only(self):
        random.seed(41)
        player = make_player(day=7, max_floor=5)
        spawned, _ = maybe_spawn_cycle(player)

        # All expire_day values are 7 + 3..5 → 10..12.
        player["day"] = 12
        expired = expire_dungeons(player)
        self.assertEqual(len(expired) + len(player["wild_dungeons"]["active"]),
                         len(spawned))
        # Nothing with expire_day >= 12 was removed
        for d in player["wild_dungeons"]["active"]:
            self.assertGreaterEqual(d["expire_day"], 12)

        # Way past everything: all gone
        player["day"] = 100
        expire_dungeons(player)
        self.assertEqual(player["wild_dungeons"]["active"], [])

    def test_complete_moves_to_record(self):
        random.seed(42)
        player = make_player(day=7, max_floor=5)
        spawned, _ = maybe_spawn_cycle(player)
        target = spawned[0]

        completed = complete_wild_dungeon(player, target["id"])
        self.assertIsNotNone(completed)
        self.assertEqual(completed["id"], target["id"])

        active_ids = [d["id"] for d in get_active_dungeons(player)]
        self.assertNotIn(target["id"], active_ids)
        self.assertIn(target["id"], player["wild_dungeons"]["completed"])
        self.assertIsNone(get_wild_dungeon(player, target["id"]))
        # Double-complete is a no-op
        self.assertIsNone(complete_wild_dungeon(player, target["id"]))

    def test_complete_after_expiry_still_records(self):
        """A dungeon that crumbled mid-run can still be recorded as cleared."""
        random.seed(43)
        player = make_player(day=7, max_floor=5)
        spawned, _ = maybe_spawn_cycle(player)
        target = spawned[0]

        # Expire it off the active list
        player["day"] = 100
        expire_dungeons(player)
        self.assertIsNone(get_wild_dungeon(player, target["id"]))

        completed = complete_wild_dungeon(player, target["id"])
        self.assertIsNone(completed)  # was no longer active
        self.assertIn(target["id"], player["wild_dungeons"]["completed"])

        # Idempotent — no duplicate entries
        complete_wild_dungeon(player, target["id"])
        self.assertEqual(
            player["wild_dungeons"]["completed"].count(target["id"]), 1)


# ═══════════════════════════════════════════════════════════════
# Completion journal entries
# ═══════════════════════════════════════════════════════════════

class TestCompletionJournal(WildDungeonTestCase):

    def test_completion_entry_has_name_level_day(self):
        player = make_player(day=25, max_floor=10)
        dungeon = {"name": "Forgotten Crypt", "level": 12, "total_floors": 4}
        record_completion_event(player, dungeon, 1200, 1920)

        events = player["journal"]["events"]
        self.assertEqual(len(events), 1)
        entry = events[0]
        self.assertIn("Forgotten Crypt", entry["name"])
        self.assertIn("Lv 12", entry["desc"])
        self.assertIn("+1200 gold", entry["desc"])
        self.assertEqual(entry["day"], 25)
        self.assertEqual(entry["tag"], "[WILD]")

    def test_two_completions_same_day_both_recorded(self):
        """Direct append — the (day, name) dedupe of record_event must not
        swallow a second conquest on the same day."""
        player = make_player(day=25, max_floor=10)
        record_completion_event(
            player, {"name": "A", "level": 5, "total_floors": 2}, 1, 2)
        record_completion_event(
            player, {"name": "B", "level": 6, "total_floors": 3}, 3, 4)
        self.assertEqual(len(player["journal"]["events"]), 2)


# ═══════════════════════════════════════════════════════════════
# Journey construction (Phase 3 travel)
# ═══════════════════════════════════════════════════════════════

class TestJourneyConstruction(WildDungeonTestCase):

    def _dungeon(self, dungeon_id="wild_9", nearest="elderfen",
                 biome="swamp"):
        return {
            "id": dungeon_id,
            "name": "Forgotten Crypt",
            "biome": biome,
            "level": 12,
            "nearest_city": nearest,
            "position": [320, 240],
        }

    def test_journey_from_other_city(self):
        random.seed(61)
        player = make_player(day=10, max_floor=10)
        player["location"] = "solmere"
        dungeon = self._dungeon()

        journey = build_journey_to_dungeon(player, dungeon)
        self.assertIsNotNone(journey)
        self.assertEqual(journey["path"][-1], "wild:wild_9")
        self.assertEqual(journey["path"][0], "solmere")

        seg = journey["segments"][-1]
        self.assertEqual(seg["to"], "wild:wild_9")
        self.assertEqual(seg["from"], "elderfen")
        self.assertEqual(seg["type"], "land")
        self.assertEqual(seg["cost"], 0)
        self.assertTrue(WILD_OFFROAD_MIN_MINUTES <= seg["raw_time"]
                        <= WILD_OFFROAD_MAX_MINUTES)

        # Total time = city legs + off-road leg
        city_time = sum(s["effective_time"] for s in journey["segments"][:-1])
        self.assertEqual(journey["total_time"],
                         city_time + seg["effective_time"])
        # Biomes on the off-road leg come from the nearest city
        self.assertEqual(seg["biome"], CITIES["elderfen"].get("biome"))
        self.assertFalse(journey["blocked_segments"])

    def test_journey_already_at_nearest_city(self):
        random.seed(62)
        player = make_player(day=10, max_floor=10)
        player["location"] = "solmere"
        dungeon = self._dungeon(nearest="solmere", biome="temperate")

        journey = build_journey_to_dungeon(player, dungeon)
        self.assertEqual(len(journey["segments"]), 1)
        self.assertEqual(journey["path"], ["solmere", "wild:wild_9"])
        self.assertEqual(journey["total_cost"], 0)

    def test_journey_from_dungeon_location_uses_origin(self):
        """When location == 'dungeon', routing starts from origin_city."""
        random.seed(63)
        player = make_player(day=10, max_floor=10)
        player["location"] = "dungeon"
        player["origin_city"] = "solmere"
        dungeon = self._dungeon()

        journey = build_journey_to_dungeon(player, dungeon)
        self.assertIsNotNone(journey)
        self.assertEqual(journey["path"][0], "solmere")

    def test_offroad_segment_bounds_no_mount(self):
        random.seed(64)
        player = make_player(day=10, max_floor=10)
        for _ in range(50):
            seg = offroad_segment(player, self._dungeon(nearest="solmere"))
            self.assertTrue(WILD_OFFROAD_MIN_MINUTES <= seg["effective_time"]
                            <= WILD_OFFROAD_MAX_MINUTES)
            self.assertEqual(seg["cost"], 0)
            self.assertEqual(seg["to"], "wild:wild_9")

    def test_terminal_journey_entry_fields(self):
        """_set_wild_entry sets the three routing fields used by exits."""
        from facilities.travel import _set_wild_entry
        player = make_player(day=10, max_floor=10)
        player["location"] = "solmere"
        _set_wild_entry(player, self._dungeon())
        self.assertEqual(player["wild_dungeon_id"], "wild_9")
        self.assertEqual(player["origin_city"], "elderfen")
        self.assertEqual(player["dungeon_region"], "swamp")
        self.assertEqual(player["location"], "dungeon")


# ═══════════════════════════════════════════════════════════════
# events.process_day_rollover integration
# ═══════════════════════════════════════════════════════════════

class TestDayRolloverHook(WildDungeonTestCase):

    def test_week_rollover_triggers_spawn_event(self):
        random.seed(51)
        from events import process_day_rollover
        player = make_player(day=1, max_floor=10)
        player["day"] = 8  # advance_time sets day before calling rollover
        events = process_day_rollover(player, days_passed=7, old_day=1)

        spawn_events = [e for e in events if e.get("id") == "wild_dungeon_spawn"]
        self.assertEqual(len(spawn_events), 1)
        self.assertTrue(3 <= len(player["wild_dungeons"]["active"]) <= 7)

    def test_short_advance_no_spawn(self):
        random.seed(52)
        from events import process_day_rollover
        player = make_player(day=1, max_floor=10)
        player["day"] = 2
        events = process_day_rollover(player, days_passed=1, old_day=1)
        self.assertFalse(any(e.get("id") == "wild_dungeon_spawn" for e in events))
        self.assertEqual(player["wild_dungeons"]["active"], [])


if __name__ == "__main__":
    unittest.main()
