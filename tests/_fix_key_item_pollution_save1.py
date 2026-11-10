"""Report and (with --apply) clean up key-item pollution in savegame_1.json.

Why: facilities/travel_events._SKIP_IDS did not exclude type "key_item", so
the shared random-loot roll (_random_item_id) could hand out key items:
  - resonance_orb  ("Shattered Orb", granted by Archivist Voss)
  - glass_anchor   (Isle of Glass floor 10 clear reward)
  - beating_root   (Event Horizon milestone reward, rooms >= 125)
The bug is fixed; this script repairs the one polluted save (slot 1).

Legitimate ownership is decided from story state:
  - resonance_orb: only if quests.flags.met_voss is set (grant is idempotent,
    so a legit player can hold at most one).
  - glass_anchor: only if the Isle of Glass has a cleared floor 10
    (city_floors.isle_of_glass.max_floor >= 10 / _grant_glass_anchor call site).
  - beating_root: at most one per claimed Event Horizon milestone flag
    (player["eh_root_<room>"] entries) — but the use-effect is not shipped yet,
    so each claimed milestone legitimately holds one root.

Extra copies are removed; the first occurrence of each id is kept as the
legit copy (and re-refreshed like the game would). Item stacks (count > 1)
are capped to the legit count.

Usage:
  python tests/_fix_key_item_pollution_save1.py           # report only
  python tests/_fix_key_item_pollution_save1.py --apply   # repair + backup
"""
import json
import os
import shutil
import sys
import time

# Make repo root importable when running this script from tests/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PATH = os.path.join("savefile", "savegame_1.json")
APPLY = "--apply" in sys.argv

KEY_IDS = ("resonance_orb", "glass_anchor", "beating_root")


def find_all_key_copies(player):
    """Return list of (location, inventory_list, index, item) for key ids."""
    hits = []
    inv = player.get("inventory", [])
    for idx, item in enumerate(inv):
        if item.get("id") in KEY_IDS:
            hits.append(("inventory", inv, idx, item))
    # Defensive sweep: pending quest reward items can also hold copies
    pending = (player.get("quests") or {}).get("pending_items", [])
    for idx, item in enumerate(pending):
        if isinstance(item, dict) and item.get("id") in KEY_IDS:
            hits.append(("quests.pending_items", pending, idx, item))
    return hits


def legit_counts(player):
    """How many of each key id the player can legitimately own right now."""
    quests_state = player.get("quests") or {}
    flags = quests_state.get("flags") or {}

    orb_legit = 1 if flags.get("met_voss") else 0
    anchor_legit = 1 if anchor_earned(player) else 0
    # One root per claimed milestone flag (use-effect not shipped yet)
    root_flags = [k for k in player if k.startswith("eh_root_")]
    root_legit = len(root_flags)

    return {
        "resonance_orb": orb_legit,
        "glass_anchor": anchor_legit,
        "beating_root": root_legit,
    }, root_flags


def anchor_earned(player):
    """True if the save shows Isle of Glass floor 10 cleared."""
    cf = (player.get("city_floors") or {}).get("isle_of_glass") or {}
    if cf.get("max_floor", 0) >= 10:
        return True
    # Fallback signals: any flag mentioning the isle clear, or best floors
    for k, v in player.items():
        if isinstance(k, str) and "isle" in k.lower() and v:
            return True
    if player.get("max_floor", 0) >= 10 and "isle_of_glass" in (player.get("city_floors") or {}):
        return True
    return False


def main():
    with open(PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    quests_state = data.get("quests") or {}
    flags = quests_state.get("flags") or {}
    counts, root_flags = legit_counts(data)

    print(f"Save: {PATH}")
    print(f"Player: {data.get('name')}  level {data.get('level')}  day {data.get('day')}")
    print(f"quests.flags.met_voss      = {flags.get('met_voss')}")
    print(f"quests.resonance_tier      = {quests_state.get('resonance_tier')}")
    print(f"Isle city_floors entry     = {(data.get('city_floors') or {}).get('isle_of_glass')}")
    print(f"global max_floor           = {data.get('max_floor')}")
    print(f"EH root milestone flags    = {sorted(root_flags)}")
    print()

    hits = find_all_key_copies(data)
    if not hits:
        print("No resonance_orb/glass_anchor/beating_root found — save is clean.")
        return

    for loc, lst, idx, item in hits:
        print(f"[{loc} idx={idx}] id={item.get('id')!r} count={item.get('count', 1)} "
              f"name={item.get('name')!r} rarity={item.get('rarity')!r} "
              f"meter={item.get('resonance_meter')!r} special={item.get('special')!r}")

    print()
    kept = {}
    to_remove = []
    for loc, lst, idx, item in hits:
        want = kept.get(item["id"], 0)
        allowed = counts.get(item["id"], 0)
        have = item.get("count", 1)
        if want < allowed:
            keep_n = min(have, allowed - want)
            kept[item["id"]] = want + keep_n
            if keep_n < have:
                to_remove.append((loc, lst, idx, item, "excess copies in stack", have - keep_n))
        else:
            to_remove.append((loc, lst, idx, item, "no legit source remaining", have))

    print("Legit capacity:", counts)
    print("Plan (dry-run):")
    for loc, lst, idx, item, reason, n in to_remove:
        print(f"  remove {n}x {item.get('name')!r} ({item.get('id')}) from {loc}[{idx}] — {reason}")
    if not to_remove:
        print("  nothing to remove")

    if not APPLY:
        print("\nRun with --apply to repair (a backup is written first).")
        return

    backup = PATH.replace(".json", f".backup_{time.strftime('%Y%m%d_%H%M%S')}.json")
    shutil.copy2(PATH, backup)
    print(f"\nBackup written: {backup}")

    # Remove from the back so earlier indexes stay valid
    for loc, lst, idx, item, reason, n in sorted(to_remove, key=lambda t: -t[2]):
        have = item.get("count", 1)
        if n >= have:
            lst.pop(idx)
        else:
            item["count"] = have - n

    # Re-refresh the kept orb so name/rarity/meter match story tier
    try:
        import quests as quests_mod
        if quests_mod._find_resonance_orb(data) is not None:
            quests_mod._refresh_resonance_orb(data)
            print("Re-refreshed kept resonance orb.")
    except Exception as exc:  # pragma: no cover — advisory only
        print(f"WARN: orb refresh skipped: {exc}")

    with open(PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # Verify
    with open(PATH, "r", encoding="utf-8") as f:
        check = json.load(f)
    print("\nAfter repair:")
    for loc, lst, idx, item in find_all_key_copies(check):
        print(f"  [{loc} idx={idx}] {item.get('name')!r} count={item.get('count', 1)} "
              f"rarity={item.get('rarity')!r} meter={item.get('resonance_meter')!r}")


if __name__ == "__main__":
    main()
