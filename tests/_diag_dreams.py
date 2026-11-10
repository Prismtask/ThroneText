"""Headless smoke test for Phase 1 dream events (docs/dream_events_design.md).

Covers: state seeding, chance + soft pity, pool conditions, weighting
modifiers (stress / fatigue / anti-spiral / bond / fresh location / repeat
decay), effect application (xp, gold cap, stress, affection, buffs, items),
the dream_blessed merge rule, Journal entries, Wonderland/EH suppression,
and the buff wiring in stats / HUD / dungeon tick loops.

Run:
    .venv\\Scripts\\python.exe tests\\_diag_dreams.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# Headless runs must never open the level-up UI, and must never write saves.
import leveling
AWARDED = []
leveling.gain_exp = lambda player, amount: AWARDED.append(int(amount))
leveling.gain_exp_ally = lambda ally, amount: None
import save_load
save_load.save_game = lambda player: None

from character import build_character, ensure_player_fields
import dreams
from resources.dreams import DREAMS, get_dream, dream_location_allowed
import family
from combat.stats import get_effective_attribute
from combat.combat_ui import _get_entity_buff_tags

ATTRS = {"Strength": 5, "Constitution": 5, "Dexterity": 5,
         "Learning": 5, "Wisdom": 5, "Charisma": 5}

CHECKS = []

ALLOWED_EFFECTS = {"xp", "ally_xp", "gold_loss", "girl_stress", "player_stress",
                   "affection", "buff", "items"}


def check(name, ok, detail=""):
    CHECKS.append((name, bool(ok), detail))
    tag = "OK  " if ok else "FAIL"
    print(f"[{tag}] {name}" + (f" — {detail}" if detail and not ok else ""))


class FakeTerm:
    def __init__(self, menu_answers=None):
        self.lines = []
        self.menu_answers = list(menu_answers or [])
        self.menu_calls = []

    def print(self, text=""):
        self.lines.append(str(text))

    def pause(self, *args, **kwargs):
        pass

    def menu(self, options, prompt="Choose an option:", **kwargs):
        self.menu_calls.append(list(options))
        if self.menu_answers:
            return self.menu_answers.pop(0)
        return 0


def new_player():
    player = build_character("1", "1", ATTRS, "Diag", 1)
    player.pop("save_slot", None)
    ensure_player_fields(player)
    return player


def add_ally(player, stress=0, affection=30, cap=100, hp=None):
    ally = {"key": "harpy_scout", "name": "Harpy Scout", "level": 5,
            "affection": affection, "affection_cap": cap, "stress": stress,
            "current_hp": hp if hp is not None else 50, "max_hp": 50}
    player.setdefault("allies", []).append(ally)
    return ally


def pool_totals(player, location="home"):
    pool = dreams.build_pool(player, location)
    totals = {"boon": 0.0, "burden": 0.0, "choice": 0.0}
    for dream, weight in pool:
        key = dream.get("category", "boon")
        totals[key] = totals.get(key, 0.0) + weight
    return totals, {d["id"]: w for d, w in pool}


# ── 1. State seeding ────────────────────────────────────────────────────────
player = new_player()
check("ensure_player_fields seeds player['dreams']",
      isinstance(player.get("dreams"), dict) and "seen" in player["dreams"])

raw = {}
dreams.ensure_state(raw)
check("ensure_state is idempotent on raw dicts",
      raw["dreams"]["streak"] == 0 and dreams.ensure_state(raw) is raw["dreams"])

# ── 2. Chance + soft pity ───────────────────────────────────────────────────
check("base dream chance is 20% (D1)", abs(dreams.DREAM_CHANCE - 0.20) < 1e-9)
player["dreams"]["streak"] = 0
check("chance with no streak is 20%", abs(dreams.dream_chance(player) - 0.20) < 1e-9)
player["dreams"]["streak"] = 5
check("pity starts after 5 dreamless sleeps (+5%)",
      abs(dreams.dream_chance(player) - 0.25) < 1e-9,
      f"{dreams.dream_chance(player):.2f}")
player["dreams"]["streak"] = 10
check("pity adds +5% per further sleep",
      abs(dreams.dream_chance(player) - 0.50) < 1e-9,
      f"{dreams.dream_chance(player):.2f}")
player["dreams"]["streak"] = 50
check("pity is capped", abs(dreams.dream_chance(player) - dreams.PITY_CAP) < 1e-9)
player["dreams"]["streak"] = 0

# ── 3. Location gating ──────────────────────────────────────────────────────
camp_only = {"id": "x", "conditions": {"location": "camp"}}
check("location condition honours a single string",
      dream_location_allowed(camp_only, "camp")
      and not dream_location_allowed(camp_only, "inn"))
check("no location condition allows every sleep location",
      all(dream_location_allowed({"id": "x", "conditions": {}}, loc)
          for loc in ("home", "inn", "camp")))

# ── 4. Pool conditions ──────────────────────────────────────────────────────
player = new_player()
ids, _ = pool_totals(player)[1], None
pool_ids = set(pool_totals(player)[1])
check("party-gated dream excluded with an empty party",
      "dream_warm_company" not in pool_ids and "dream_clear_water" not in pool_ids)
ally = add_ally(player)
pool_ids = set(pool_totals(player)[1])
check("party-gated dream appears with a party girl",
      {"dream_warm_company", "dream_clear_water"} <= pool_ids)

player["dreams"]["seen"]["dream_accord_page"] = 1
check("once-dreams leave the pool after being seen",
      "dream_accord_page" not in set(pool_totals(player)[1]))

# ── 5. Weight modifiers ─────────────────────────────────────────────────────
player = new_player()
ally = add_ally(player, stress=0)
base_totals, base_w = pool_totals(player)

ally["stress"] = 80
stressed_totals, stressed_w = pool_totals(player)
check("party stress >= 60 doubles burden weight (x2)",
      abs(stressed_totals["burden"] - base_totals["burden"] * 2.0) < 1e-6
      and abs(stressed_totals["boon"] - base_totals["boon"]) < 1e-6,
      f"{base_totals['burden']:.2f} -> {stressed_totals['burden']:.2f}")

ally["stress"] = 0
player["fatigue_stacks"] = 2
fatigue_totals, _ = pool_totals(player)
check("fatigue stacks >= 2 lift burden weight (x1.5)",
      abs(fatigue_totals["burden"] - base_totals["burden"] * 1.5) < 1e-6)
player["fatigue_stacks"] = 0

player["dreams"]["last_category"] = "burden"
spiral_totals, _ = pool_totals(player)
check("a burden dream halves the next burden weight (no spiral)",
      abs(spiral_totals["burden"] - base_totals["burden"] * 0.5) < 1e-6)
player["dreams"]["last_category"] = None

ally["married"] = True
bond_totals, bond_w = pool_totals(player)
check("a married party girl doubles the bond dream weight",
      abs(bond_w["dream_warm_company"] - base_w["dream_warm_company"] * 2.0) < 1e-6)
ally["married"] = False

player["dreams"]["last_location"] = "home"
_, same_w = pool_totals(player, "home")
player["dreams"]["last_location"] = "inn"
_, fresh_w = pool_totals(player, "home")
check("Memory/Omen dreams gain x1.5 on a fresh location",
      abs(fresh_w["dream_ominous_doors"]
          - same_w["dream_ominous_doors"] * dreams.FRESH_LOCATION_MULT) < 1e-6,
      f"{same_w.get('dream_ominous_doors')} -> {fresh_w.get('dream_ominous_doors')}")
player["dreams"]["last_location"] = None

player["dreams"]["seen"]["dream_inspired"] = 1
_, decay_w = pool_totals(player)
base_inspired = get_dream("dream_inspired")["weight"]
check("repeat decay is x0.6 per sighting",
      abs(decay_w["dream_inspired"] - base_inspired * dreams.REPEAT_DECAY) < 1e-6,
      f"{decay_w['dream_inspired']}")
player["dreams"]["seen"]["dream_inspired"] = 12
_, floored_w = pool_totals(player)
check("repeat decay floor holds at 20% of base",
      abs(floored_w["dream_inspired"] - base_inspired * dreams.REPEAT_FLOOR) < 1e-6)

# ── 6. Effect application ───────────────────────────────────────────────────
player = new_player()
ally = add_ally(player, stress=0)
AWARDED.clear()
dreams._apply_effects(player, get_dream("dream_inspired"))
check("inspired dream grants player XP", AWARDED == [35], f"{AWARDED}")

gold_msgs = []
player["gold"] = 1000
dreams._apply_effects(player, get_dream("dream_pale_hand"))
check("gold loss capped at 50g on a fat purse", player["gold"] == 950,
      f"{player['gold']}")
player["gold"] = 100
dreams._apply_effects(player, get_dream("dream_pale_hand"))
check("gold loss capped at 5% on a small purse", player["gold"] == 95,
      f"{player['gold']}")
player["gold"] = 0
dreams._apply_effects(player, get_dream("dream_pale_hand"))
check("no gold loss when the purse is empty", player["gold"] == 0)

ally["stress"] = 95
dreams._apply_effects(player, get_dream("dream_thin_place"))
check("nightmare stress clamps at 100", ally["stress"] == 100, f"{ally['stress']}")
dreams._apply_effects(player, get_dream("dream_clear_water"))
check("calm dream reduces stress (clamped at 0)",
      ally["stress"] == 94, f"{ally['stress']}")
ally["stress"] = 3
dreams._apply_effects(player, get_dream("dream_clear_water"))
check("calm dream clamps at 0", ally["stress"] == 0, f"{ally['stress']}")

ally["affection"] = 99
ally["affection_cap"] = 100
dreams._apply_effects(player, get_dream("dream_warm_company"))
check("bond dream respects the affection cap", ally["affection"] == 100,
      f"{ally['affection']}")

# ── 7. dream_blessed buff (D8) ──────────────────────────────────────────────
player = new_player()
ally = add_ally(player)
dreams._apply_effects(player, get_dream("dream_restful"))
ptypes = [b.get("type") for b in player.get("active_buffs", [])]
atypes = [b.get("type") for b in ally.get("active_buffs", [])]
check("dream_blessed lands on the player and the party",
      "dream_blessed" in ptypes and "dream_blessed" in atypes,
      f"{ptypes} / {atypes}")
check("dream_blessed is a sleep-buff family member",
      "dream_blessed" in family.SLEEP_BUFF_TYPES)

player = new_player()
family.grant_sleep_buff(player, "well_rested", 2, 3)
dreams._apply_buff(player, {"type": "dream_blessed", "value": 1, "rooms": 2})
sleep_buffs = [b for b in player["active_buffs"]
               if b.get("type") in family.SLEEP_BUFF_TYPES]
check("dream_blessed merges with well_rested (never stacks)",
      len(sleep_buffs) == 1
      and sleep_buffs[0]["type"] == "well_rested"
      and sleep_buffs[0]["value"] == 2
      and sleep_buffs[0]["remaining"] == 3,
      str(sleep_buffs))

player = new_player()
before_str = get_effective_attribute(player, "Strength")
dreams._apply_buff(player, {"type": "dream_blessed", "value": 1, "rooms": 2})
after_str = get_effective_attribute(player, "Strength")
check("dream_blessed adds its value to every attribute",
      after_str - before_str == 1, f"{before_str} -> {after_str}")

tags = _get_entity_buff_tags(player)
check("HUD shows the DRM tag for dream_blessed", "DRM" in tags, tags)

# ── 8. Items ────────────────────────────────────────────────────────────────
player = new_player()
messages = dreams._apply_effects(player, get_dream("dream_small_mercy"))
potions = [i for i in player.get("inventory", [])
           if i.get("id") == "healing_potion"]
check("treasure dream grants the item", len(potions) == 1,
      f"{len(potions)} potion(s)")
check("treasure dream reports the pickup",
      any("Healing Potion" in m for m in messages), str(messages))

player = new_player()
player["inventory"] = [{"id": f"junk_{i}", "name": f"Junk {i}",
                        "type": "consumable", "count": 1} for i in range(40)]
messages = dreams._apply_effects(player, get_dream("dream_small_mercy"))
check("full bag skips the gift without crashing",
      not any(i.get("id") == "healing_potion" for i in player["inventory"])
      and any("no room" in m for m in messages), str(messages))

# ── 9. Full roll + Journal ──────────────────────────────────────────────────
player = new_player()
add_ally(player)
term = FakeTerm()
rng = __import__("random").Random(7)
old_chance = dreams.DREAM_CHANCE
dreams.DREAM_CHANCE = 1.0
fired = dreams.maybe_offer_dream(player, "home", term=term, rng=rng)
dreams.DREAM_CHANCE = old_chance
journals = [e for e in player["journal"]["events"] if e.get("tag") == "[DREAM]"]
check("a forced dream fires and returns its definition", isinstance(fired, dict))
check("the dream prints a scene", any("DREAM" in line for line in term.lines))
check("the dream writes a [DREAM] Journal entry", len(journals) == 1, str(journals))
check("state records the sighting",
      player["dreams"]["seen"].get(fired["id"]) == 1
      and player["dreams"]["streak"] == 0
      and player["dreams"]["last_category"] == fired["category"]
      and player["dreams"]["last_location"] == "home")

player = new_player()
dreams.DREAM_CHANCE = 0.0
none_fired = dreams.maybe_offer_dream(player, "inn", term=term, rng=rng)
dreams.DREAM_CHANCE = old_chance
check("a dreamless night counts toward the pity streak",
      none_fired is None and player["dreams"]["streak"] == 1,
      f"streak={player['dreams']['streak']}")

# ── 10. Suppression (D7 + death path) ──────────────────────────────────────
for flag, label in (("wonderland_active", "Wonderland"),
                    ("_eh_in_run", "Event Horizon")):
    player = new_player()
    add_ally(player)
    player[flag] = True
    dreams.DREAM_CHANCE = 1.0
    result = dreams.maybe_offer_dream(player, "home", term=term, rng=rng)
    dreams.DREAM_CHANCE = old_chance
    check(f"no dreams in {label}", result is None
          and player["dreams"]["seen"] == {}
          and player["dreams"]["streak"] == 0)

player = new_player()
player["current_hp"] = 0
dreams.DREAM_CHANCE = 1.0
result = dreams.maybe_offer_dream(player, "home", term=term, rng=rng)
dreams.DREAM_CHANCE = old_chance
check("no dream on the death path", result is None)

# ── 10b. Phase 2 — choice dreams ───────────────────────────────────────────
CHOICES = [d for d in DREAMS if d.get("category") == "choice"]
check("four choice dreams are registered", len(CHOICES) == 4,
      str([d["id"] for d in CHOICES]))
check("every choice dream has a prompt header and 2 prompts",
      all(d.get("prompt") and len(d.get("prompts") or []) == 2 for d in CHOICES))
check("every prompt has a label, a reply and effects",
      all(p.get("text") and p.get("reply") and isinstance(p.get("effects"), dict)
          for d in CHOICES for p in d["prompts"]))
check("choice effects stay inside the allowed keys (D4)",
      all(set(p.get("effects") or {}) <= ALLOWED_EFFECTS
          for d in CHOICES for p in d["prompts"]),
      str({k for d in CHOICES for p in d["prompts"]
           for k in (p.get("effects") or {})} - ALLOWED_EFFECTS))

# A choice dream resolves the picked prompt's effects
player = new_player()
add_ally(player)
term = FakeTerm(menu_answers=[0])
dream = get_dream("dream_offered_hand")
old_chance = dreams.DREAM_CHANCE
dreams.DREAM_CHANCE = 1.0
fired = dreams._deliver(player, dream, "home", term)
dreams.DREAM_CHANCE = old_chance
buffs = [b.get("type") for b in player.get("active_buffs", [])]
check("the menu was shown with both options", len(term.menu_calls[0]) == 2,
      str(term.menu_calls))
check("taking the hand grants the damage buff",
      "damage_boost" in buffs, str(buffs))
check("taking the hand adds player stress", player["stress"] == 20,
      f"{player['stress']}")
check("the chosen option is written to the Journal",
      any("Take the hand" in e.get("desc", "")
          for e in player["journal"]["events"] if e.get("tag") == "[DREAM]"),
      str(player["journal"]["events"]))

# Token substitution reaches the option labels ({girl})
player = new_player()
girl = add_ally(player, "Harpy")
term = FakeTerm(menu_answers=[1])
fired = dreams._deliver(player, get_dream("dream_feast"), "home", term)
affection_labels = term.menu_calls[0][1]
check("option labels substitute {girl}", "Harpy" in affection_labels,
      affection_labels)
check("the share option grants affection", girl["affection"] == 33,
      f"{girl['affection']}")

# Repeats gain a Skip option; skipping applies nothing
player = new_player()
add_ally(player)
player["dreams"]["seen"]["dream_mirror_self"] = 1
term = FakeTerm(menu_answers=[2])          # 3 options: 2 prompts + skip
gold_before = player["gold"]
stress_before = player["stress"]
fired = dreams._deliver(player, get_dream("dream_mirror_self"), "home", term)
check("repeats gain a Skip option", len(term.menu_calls[0]) == 3,
      str(term.menu_calls))
check("skipping applies no effects",
      player["stress"] == stress_before and player["gold"] == gold_before
      and not player.get("active_buffs"))
check("skipping is journalled",
      any("let it go" in e.get("desc", "")
          for e in player["journal"]["events"] if e.get("tag") == "[DREAM]"),
      str(player["journal"]["events"]))
check("a skipped dream still counts as seen",
      player["dreams"]["seen"]["dream_mirror_self"] == 2)

# Once-dreams leave the pool after the choice was played
player = new_player()
add_ally(player)
player["day"] = 10
player["dreams"]["seen"]["dream_accord_echo"] = 1
pool_ids = {d["id"] for d, _ in dreams.build_pool(player, "home")}
check("a played once-choice leaves the pool",
      "dream_accord_echo" not in pool_ids)

# ── 10c. Phase 2 — story queue (§4.5) ─────────────────────────────────────
player = new_player()
add_ally(player)
check("queue_story_dream rejects unknown ids",
      dreams.queue_story_dream(player, "not_a_dream") is False)
check("queue_story_dream accepts a real dream",
      dreams.queue_story_dream(player, "dream_mirror_self") is True)
check("queue_story_dream dedupes",
      dreams.queue_story_dream(player, "dream_mirror_self") is False
      and player["dreams"]["queue"] == ["dream_mirror_self"])

term = FakeTerm(menu_answers=[1])
dreams.DREAM_CHANCE = 0.0                 # queued beats ignore the roll
fired = dreams.maybe_offer_dream(player, "camp", term=term, rng=rng)
dreams.DREAM_CHANCE = old_chance
check("a queued story dream is delivered despite a 0% roll",
      isinstance(fired, dict) and fired["id"] == "dream_mirror_self",
      str(fired and fired.get("id")))
check("the queue empties after delivery", player["dreams"]["queue"] == [])

# Story-category dreams never appear in the random pool
story_probe = {
    "id": "dream_probe_story",
    "name": "Probe",
    "category": "story",
    "weight": 999,
    "once": True,
    "conditions": {},
    "lines": ["probe"],
    "journal": "probe",
    "effects": {},
}
DREAMS.append(story_probe)
try:
    player = new_player()
    add_ally(player)
    pool_ids = {d["id"] for d, _ in dreams.build_pool(player, "home")}
    check("story dreams are never rolled", "dream_probe_story" not in pool_ids)
finally:
    DREAMS.remove(story_probe)

# ── 10d. Phase 3 — story dreams + Dream Journal ───────────────────────────
STORY = [d for d in DREAMS if d.get("category") == "story"]
check("four story dreams are registered", len(STORY) == 4,
      str([d["id"] for d in STORY]))
check("story dreams are once-only", all(d.get("once") for d in STORY))
check("story dreams carry a journal line and effects block",
      all(d.get("journal") and isinstance(d.get("effects"), dict) for d in STORY))

# Nothing queues on a fresh save
player = new_player()
add_ally(player)
check("no story dream queues on a fresh save",
      dreams.check_story_triggers(player) == [], str(player["dreams"]["queue"]))

# Shared night -> family dream (content level gate)
player = new_player()
add_ally(player)
player["had_shared_night"] = True
queued = dreams.check_story_triggers(player)
check("the first shared night queues its story dream",
      "dream_first_shared_night" in queued, str(queued))
check("story trigger is idempotent",
      dreams.check_story_triggers(player) == []
      and player["dreams"]["queue"].count("dream_first_shared_night") == 1)

import family as family_mod
_real_content = family_mod.get_content_level
try:
    family_mod.get_content_level = lambda settings=None: "off"
    player = new_player()
    add_ally(player)
    player["had_shared_night"] = True
    check("content level off blocks the intimate story dream",
          "dream_first_shared_night" not in dreams.check_story_triggers(player))
finally:
    family_mod.get_content_level = _real_content

# Pregnancy -> family-enabled gate
player = new_player()
add_ally(player)
player["family_expecting"] = True
check("the expectant dream needs family_enabled",
      "dream_expectant_light" not in dreams.check_story_triggers(player))
player["family_enabled"] = True
check("the expectant dream queues once family is enabled",
      "dream_expectant_light" in dreams.check_story_triggers(player))

# Voss epilogue flag
player = new_player()
add_ally(player)
player["quests"]["flags"]["voss_epilogue_seen"] = True
check("the Voss epilogue queues its echo",
      "dream_voss_first_page" in dreams.check_story_triggers(player))

# Vampire companion -> thirst foreshadowing
player = new_player()
add_ally(player)
check("no thirst dream without a vampire",
      "dream_thirst_beneath" not in dreams.check_story_triggers(player))
vamp = add_ally(player, "Sanguine")
vamp["race"] = "Vampire"
check("a vampire in the party queues the thirst dream",
      "dream_thirst_beneath" in dreams.check_story_triggers(player))

# Delivery sets story flags and journals the beat
player = new_player()
add_ally(player)
player["had_shared_night"] = True
term = FakeTerm()
dreams.DREAM_CHANCE = 0.0
fired = dreams.maybe_offer_dream(player, "home", term=term, rng=rng)
dreams.DREAM_CHANCE = old_chance
check("a queued story dream is delivered on the next sleep",
      isinstance(fired, dict) and fired["id"] == "dream_first_shared_night",
      str(fired and fired.get("id")))

player = new_player()
add_ally(player)
player["quests"]["flags"]["voss_epilogue_seen"] = True
term = FakeTerm()
dreams.queue_story_dream(player, "dream_voss_first_page")
dreams.DREAM_CHANCE = 0.0
dreams.maybe_offer_dream(player, "home", term=term, rng=rng)
dreams.DREAM_CHANCE = old_chance
check("story dreams can set story flags",
      player.get("dreamed_of_voss") is True
      and player["quests"]["flags"].get("dreamed_of_voss") is True,
      f"{player.get('dreamed_of_voss')}")

# Dream Journal data
entries = dreams.journal_entries(player)
check("the Dream Journal lists seen dreams",
      any(e["id"] == "dream_voss_first_page" for e in entries), str(entries))
check("journal entries carry name, category, lines and count",
      all(e.get("name") and e.get("category") and e.get("lines")
          and e.get("count") >= 1 for e in entries))
player = new_player()
check("a save with no dreams has an empty Dream Journal",
      dreams.journal_entries(player) == [])

# ── 10e. Phase 4 — per-context dreams ───────────────────────────────────
player = new_player()
add_ally(player)
home_ids = {d["id"] for d, _ in dreams.build_pool(player, "home")}
inn_ids = {d["id"] for d, _ in dreams.build_pool(player, "inn")}
camp_ids = {d["id"] for d, _ in dreams.build_pool(player, "camp")}
check("home-only dreams stay home",
      "dream_hearth_song" in home_ids
      and "dream_hearth_song" not in inn_ids
      and "dream_hearth_song" not in camp_ids)
check("the camp-only dream stays at camp",
      "dream_road_patience" in camp_ids and "dream_road_patience" not in home_ids)
check("the inn-only dream stays at the inn",
      "dream_rented_room" in inn_ids and "dream_rented_room" not in home_ids)
check("the house-remembers dream waits for day 4",
      "dream_home_remembers" not in home_ids)
player["day"] = 4
home_ids = {d["id"] for d, _ in dreams.build_pool(player, "home")}
check("...and appears once day 4 arrives",
      "dream_home_remembers" in home_ids)
check("every context dream has lines, journal and effects",
      all(get_dream(did).get("journal") and (get_dream(did).get("lines"))
          for did in ("dream_hearth_song", "dream_home_remembers",
                      "dream_road_patience", "dream_rented_room")))

# ── 11. Wiring guards ──────────────────────────────────────────────────────
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(root, "dungeon.py"), encoding="utf-8") as fh:
    dungeon_src = fh.read()
check("dungeon room ticks know dream_blessed (3 loops x player/ally)",
      dungeon_src.count("dream_blessed") >= 6,
      f"{dungeon_src.count('dream_blessed')} occurrence(s)")

with open(os.path.join(root, "facilities", "travel.py"), encoding="utf-8") as fh:
    travel_src = fh.read()
call_sites = travel_src.count("maybe_offer_dream(player, \"camp\", term)")
check("both terminal camp paths roll a dream", call_sites == 2,
      f"{call_sites} call(s)")

for rel in (("facilities", "house.py"), ("facilities", "inn.py"),
            ("facilities", "camp.py")):
    with open(os.path.join(root, *rel), encoding="utf-8") as fh:
        src = fh.read()
    check(f"{rel[1]} hooks maybe_offer_dream", "maybe_offer_dream" in src)

with open(os.path.join(root, "facilities", "inn.py"), encoding="utf-8") as fh:
    inn_src = fh.read()
wonderland_block = inn_src.split("def _wonderland_inn_menu")[1]
check("the Wonderland inn sleep path rolls no dream (D7)",
      "maybe_offer_dream" not in wonderland_block)

# ── 12. Registry integrity ─────────────────────────────────────────────────
ids = [d["id"] for d in DREAMS]
check("dream ids are unique", len(ids) == len(set(ids)))
check("every dream has lines and a journal line",
      all(d.get("lines") and d.get("journal") for d in DREAMS))
check("all four categories are represented",
      {d["category"] for d in DREAMS} == {"boon", "burden", "choice", "story"})
check("no dream uses an unsupported or destructive effect (D4)",
      all(set(d.get("effects") or {}) <= ALLOWED_EFFECTS for d in DREAMS))

# ── Summary ────────────────────────────────────────────────────────────────
failed = [name for name, ok, _ in CHECKS if not ok]
print()
print(f"{len(CHECKS) - len(failed)}/{len(CHECKS)} checks passed")
if failed:
    print("FAILED:")
    for name in failed:
        print(f"  - {name}")
    sys.exit(1)
print("dreams phases 1-4 OK")
