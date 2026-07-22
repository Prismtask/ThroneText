"""Enemy audit report generator for Pandemonium."""
import yaml
import os
import json
from collections import Counter

ENEMY_RACES = {
    "Human": {"mods": {}, "elemental_res": {}, "elemental_dmg": {}},
    "Goblin": {"mods": {"Dexterity": 2, "Strength": -1, "Constitution": -1},
               "elemental_res": {"earth": 0.8, "light": 0.9}, "elemental_dmg": {"dark": 1.2}},
    "Orc": {"mods": {"Strength": 3, "Constitution": 1, "Charisma": -2},
            "elemental_res": {"dark": 1.2, "fire": 1.1, "physical": 1.2, "magical": 0.85},
            "elemental_dmg": {"fire": 1.3, "dark": 1.1, "physical": 1.3}},
    "Undead": {"mods": {"Constitution": 3, "Wisdom": -2, "Charisma": -3},
               "elemental_res": {"light": 0.7, "fire": 0.8, "dark": 1.3, "physical": 1.1},
               "elemental_dmg": {"dark": 1.3, "fire": 0.9}},
    "Beast": {"mods": {"Strength": 2, "Dexterity": 1, "Learning": -3},
              "elemental_res": {"earth": 1.2, "wind": 1.1, "physical": 1.1},
              "elemental_dmg": {"physical": 1.3}},
    "Demon": {"mods": {"Strength": 2, "Charisma": 2, "Wisdom": -1},
              "elemental_res": {"dark": 1.3, "fire": 1.2, "light": 0.6, "water": 0.7, "magical": 1.2, "physical": 0.85},
              "elemental_dmg": {"fire": 1.3, "dark": 1.3, "magical": 1.2}},
    "Construct": {"mods": {"Strength": 2, "Constitution": 4, "Charisma": -5},
                  "elemental_res": {"earth": 1.2, "fire": 1.2, "thunder": 0.7, "physical": 1.3, "magical": 0.8},
                  "elemental_dmg": {"earth": 1.1, "physical": 1.2}},
    "Dragonkin": {"mods": {"Strength": 3, "Constitution": 2, "Learning": -2},
                  "elemental_res": {"fire": 1.2, "thunder": 1.2, "water": 1.1, "physical": 1.2},
                  "elemental_dmg": {"fire": 1.3, "thunder": 1.1, "physical": 1.2}},
    "Fey": {"mods": {"Dexterity": 3, "Charisma": 2, "Strength": -2},
            "elemental_res": {"light": 1.2, "wind": 1.1, "dark": 0.7, "magical": 1.3, "physical": 0.8},
            "elemental_dmg": {"light": 1.3, "wind": 1.2, "magical": 1.3}},
    "Elemental": {"mods": {"Constitution": 3, "Learning": 2, "Dexterity": -1},
                  "elemental_res": {"fire": 1.1, "water": 1.1, "thunder": 1.1, "wind": 1.1, "earth": 1.1,
                                    "physical": 0.85, "magical": 1.2},
                  "elemental_dmg": {"fire": 1.2, "water": 1.2, "thunder": 1.2, "wind": 1.2, "earth": 1.2, "magical": 1.2}},
    "Giant": {"mods": {"Strength": 4, "Constitution": 2, "Dexterity": -3},
              "elemental_res": {"earth": 1.3, "thunder": 0.8, "wind": 0.7, "physical": 1.2},
              "elemental_dmg": {"earth": 1.3, "fire": 1.1, "physical": 1.3}},
    "Vampire": {"mods": {"Dexterity": 3, "Charisma": 2, "Wisdom": -1, "Constitution": 1},
                "elemental_res": {"dark": 1.2, "light": 0.6, "fire": 0.7, "magical": 1.1},
                "elemental_dmg": {"dark": 1.3, "fire": 0.9}},
    "Lizardfolk": {"mods": {"Constitution": 2, "Strength": 1, "Learning": -1},
                   "elemental_res": {"water": 1.2, "earth": 1.2, "fire": 0.8, "physical": 1.1},
                   "elemental_dmg": {"water": 1.1, "earth": 1.1, "physical": 1.1}},
    "Gnome": {"mods": {"Learning": 2, "Dexterity": 1, "Strength": -2},
              "elemental_res": {"earth": 1.2, "thunder": 1.1, "magical": 1.1},
              "elemental_dmg": {"thunder": 1.3, "earth": 1.1, "magical": 1.2}},
    "Shadow": {"mods": {"Dexterity": 3, "Wisdom": -1, "Constitution": -1},
               "elemental_res": {"dark": 1.3, "light": 0.6, "physical": 1.1},
               "elemental_dmg": {"dark": 1.3}},
    "Clockwork": {"mods": {"Constitution": 3, "Learning": 1, "Charisma": -4},
                  "elemental_res": {"thunder": 0.7, "fire": 1.2, "physical": 1.2, "magical": 0.8},
                  "elemental_dmg": {"thunder": 1.2, "fire": 1.1, "physical": 1.2}},
    "Abomination": {"mods": {"Strength": 4, "Constitution": 3, "Wisdom": -3, "Charisma": -4},
                    "elemental_res": {"dark": 1.2, "light": 0.8, "fire": 1.1, "water": 0.9, "physical": 1.2},
                    "elemental_dmg": {"dark": 1.3, "fire": 1.1, "physical": 1.3}},
    "Storybook": {"mods": {"Strength": 2, "Dexterity": 2, "Charisma": 3, "Wisdom": -1, "Constitution": -1},
                  "elemental_res": {"light": 1.2, "dark": 0.7, "thunder": 1.1},
                  "elemental_dmg": {"light": 1.3, "wind": 1.2}},
}

ALL_ELEMENTS = ["fire", "water", "ice", "thunder", "wind", "earth", "light", "dark", "physical", "magical"]
ATTRIBUTES = ["Strength", "Constitution", "Dexterity", "Wisdom", "Learning", "Charisma"]


def compute_resistances(enemy):
    """Combine race resistance with enemy-specific overrides."""
    race = enemy.get("race", "Human")
    race_data = ENEMY_RACES.get(race, ENEMY_RACES["Human"])
    res = dict(race_data.get("elemental_res", {}))
    enemy_res = enemy.get("elemental_res", {})
    for elem, val in enemy_res.items():
        res[elem] = val
    return res


def compute_effective_stats(enemy):
    """Compute effective stats = base mods + race mods."""
    race = enemy.get("race", "Human")
    race_data = ENEMY_RACES.get(race, ENEMY_RACES["Human"])
    race_mods = race_data.get("mods", {})
    enemy_mods = enemy.get("mods", {})
    stats = {}
    for attr in ATTRIBUTES:
        stats[attr] = enemy_mods.get(attr, 0) + race_mods.get(attr, 0)
    return stats


def load_all_enemies():
    base = "resources/enemies/enemies_data"
    all_enemies = {}

    def add_enemy(eid, data):
        if isinstance(data, dict) and "name" in data and "level" in data:
            all_enemies[eid] = data

    for fname in sorted(os.listdir(base)):
        if not fname.endswith((".yaml", ".yml")):
            continue
        with open(os.path.join(base, fname), "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            continue
        for key, value in data.items():
            if isinstance(value, dict):
                if "name" in value and "level" in value:
                    add_enemy(key, value)
                else:
                    for sub_key, sub_value in value.items():
                        if isinstance(sub_value, dict):
                            add_enemy(sub_key, sub_value)
    return all_enemies


def main():
    all_enemies = load_all_enemies()
    print("=" * 70)
    print("PANDEMONIUM ENEMY AUDIT REPORT")
    print("=" * 70)
    print()
    print(f"Total enemies: {len(all_enemies)}")
    print(f"Monster Girls: {sum(1 for e in all_enemies.values() if e.get('monster_girl'))}")
    print(f"Wonderland (Storybook secondary): {sum(1 for e in all_enemies.values() if e.get('secondary_race') == 'Storybook')}")
    print(f"Superbosses: {sum(1 for e in all_enemies.values() if e.get('super_boss'))}")
    print(f"Bosses (non-super): {sum(1 for e in all_enemies.values() if e.get('boss') and not e.get('super_boss'))}")
    print(f"Minion-only: {sum(1 for e in all_enemies.values() if e.get('minion_only'))}")
    print()

    # ── Section 1: Race Distribution ──
    print("─" * 70)
    print("SECTION 1: RACE DISTRIBUTION & LEVEL COVERAGE")
    print("─" * 70)

    race_info = {}
    for eid, e in all_enemies.items():
        race = e.get("race", "Unknown")
        lvl = e.get("level", 0)
        if race not in race_info:
            race_info[race] = {"min": 999, "max": 0, "count": 0, "levels": []}
        ri = race_info[race]
        ri["min"] = min(ri["min"], lvl)
        ri["max"] = max(ri["max"], lvl)
        ri["count"] += 1
        ri["levels"].append(lvl)

    for race in sorted(race_info.keys()):
        ri = race_info[race]
        ri["levels"].sort()
        gaps = []
        prev = ri["min"] - 1
        for l in ri["levels"]:
            if l - prev > 2:
                gaps.append(f"{prev+1}-{l-1}")
            prev = l
        gap_str = " | GAPS: " + ", ".join(gaps[:6]) if gaps else ""
        print(f"  {race:14s}  Lv {ri['min']:2d}–{ri['max']:2d}  ({ri['count']:2d} enemies){gap_str}")

    print()

    # ── Section 2: Level Distribution ──
    print("─" * 70)
    print("SECTION 2: LEVEL DISTRIBUTION & HP SCALING")
    print("─" * 70)

    brackets = [(1, 5), (6, 10), (11, 15), (16, 20), (21, 25), (26, 30),
                (31, 35), (36, 40), (41, 45), (46, 50), (51, 60)]
    for lo, hi in brackets:
        in_range = [e for e in all_enemies.values() if lo <= e.get("level", 0) <= hi]
        if not in_range:
            print(f"  Lv {lo:2d}–{hi:2d}: 0 enemies — **CRITICAL GAP**")
            continue
        hps = [e.get("base_hp", 0) for e in in_range]
        bosses = [e for e in in_range if e.get("boss")]
        mg = [e for e in in_range if e.get("monster_girl")]
        wl = [e for e in in_range if e.get("secondary_race") == "Storybook"]
        print(f"  Lv {lo:2d}–{hi:2d}: {len(in_range):3d} enemies | "
              f"HP {min(hps):.0f}–{max(hps):.0f} (avg {sum(hps)/len(hps):.0f}) | "
              f"Boss:{len(bosses)} MG:{len(mg)} WL:{len(wl)}")

    print()

    # ── Section 3: Race Resistance Profiles ──
    print("─" * 70)
    print("SECTION 3: RACE RESISTANCE PROFILES")
    print("─" * 70)
    print("  (Values >1.0 = resist, <1.0 = weakness. Enemy-specific can override.)")
    print()
    for race in sorted(ENEMY_RACES.keys()):
        rd = ENEMY_RACES[race]
        res = rd.get("elemental_res", {})
        if not res:
            print(f"  {race:14s}: No special resistances (all 1.0x)")
            continue
        parts = []
        for elem in ALL_ELEMENTS:
            val = res.get(elem, 1.0)
            if val != 1.0:
                parts.append(f"{elem}:{val:.1f}x")
        if parts:
            print(f"  {race:14s}: {', '.join(parts)}")
        else:
            print(f"  {race:14s}: All 1.0x")

    print()

    # ── Section 4: High-Level Enemy Gap Analysis ──
    print("─" * 70)
    print("SECTION 4: HIGH-LEVEL (30+) ENEMY INVENTORY")
    print("─" * 70)
    high = [(eid, e) for eid, e in all_enemies.items() if e.get("level", 0) >= 30]
    high.sort(key=lambda x: x[1]["level"])
    for eid, e in high:
        race = e.get("race", "?")
        lvl = e.get("level", 0)
        hp = e.get("base_hp", 0)
        sec = e.get("secondary_race", "")
        tags = []
        if e.get("boss"):
            tags.append("BOSS")
        if e.get("super_boss"):
            tags.append("SUPERBOSS")
        if e.get("minion_only"):
            tags.append("MINION")
        if e.get("monster_girl"):
            tags.append("MG")
        if sec:
            tags.append(f"WL[{sec}]")
        res = compute_resistances(e)
        res_str = ", ".join(f"{k}:{v:.1f}" for k, v in res.items() if v != 1.0)
        print(f"  Lv{lvl:2d} {e['name']:<32s} [{race:<12s}] HP={hp:4d}  {' '.join(tags)}")
        if res_str:
            print(f"       Resists: {res_str}")

    print()

    # ── Section 5: Monster Girl List ──
    print("─" * 70)
    print("SECTION 5: MONSTER GIRL ROSTER")
    print("─" * 70)
    mg_list = [(eid, e) for eid, e in all_enemies.items() if e.get("monster_girl")]
    mg_list.sort(key=lambda x: x[1]["level"])
    for eid, e in mg_list:
        race = e.get("race", "?")
        lvl = e.get("level", 0)
        hp = e.get("base_hp", 0)
        res = compute_resistances(e)
        res_str = ", ".join(f"{k}:{v:.1f}" for k, v in sorted(res.items()) if v != 1.0)
        print(f"  Lv{lvl:2d} {e['name']:<25s} [{race:<12s}] HP={hp:3d}  Res: {res_str if res_str else 'none'}")

    print()

    # ── Section 6: Wonderland Enemy Roster ──
    print("─" * 70)
    print("SECTION 6: WONDERLAND ENEMY ROSTER")
    print("─" * 70)
    wl_list = [(eid, e) for eid, e in all_enemies.items() if e.get("secondary_race") == "Storybook"]
    wl_list.sort(key=lambda x: x[1]["level"])
    for eid, e in wl_list:
        race = e.get("race", "?")
        lvl = e.get("level", 0)
        hp = e.get("base_hp", 0)
        tags = []
        if e.get("boss"):
            tags.append("BOSS")
        res = compute_resistances(e)
        res_str = ", ".join(f"{k}:{v:.1f}" for k, v in sorted(res.items()) if v != 1.0)
        print(f"  Lv{lvl:2d} {e['name']:<28s} [{race:<12s}] HP={hp:3d}  {' '.join(tags)}  Res: {res_str if res_str else 'none'}")

    print()

    # ── Section 7: Race-Level Heatmap (levels without any enemy per race) ──
    print("─" * 70)
    print("SECTION 7: PLAYER-RELEVANT LEVEL GAPS (for dungeon spawning)")
    print("─" * 70)
    print("  Showing levels 1-50 where fewer than 5 non-boss enemies of any race exist")
    for lo, hi in [(1,10),(11,20),(21,30),(31,40),(41,50)]:
        in_range = [e for e in all_enemies.values()
                    if lo <= e.get("level", 0) <= hi
                    and not e.get("minion_only")
                    and not e.get("super_boss")]
        bosses_in = [e for e in in_range if e.get("boss")]
        trash_in = [e for e in in_range if not e.get("boss")]
        print(f"  Lv {lo:2d}–{hi:2d}: {len(trash_in):3d} trash + {len(bosses_in):2d} bosses = {len(in_range)} total (non-minion)")

    print()
    print("=" * 70)
    print("END OF AUDIT REPORT")
    print("=" * 70)


if __name__ == "__main__":
    main()
