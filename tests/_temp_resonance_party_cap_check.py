# Temp check (2026-11-09): "party is full" fallbacks use Command Resonance
# capacity (front + bench allies, capped at MAX_ALLIES) — not the flat
# MAX_ALLIES roster cap.
#
# Repro: savegame_4 is Chord (3 front / 2 bench = 5 allies). It owned 7
# allies, yet Sylvana's mirror scene and the Wonderland exit overflow only
# checked MAX_ALLIES (7), so new allies joined with no "who makes room?"
# prompt and ended up inactive.
#
# Run: .venv\Scripts\python.exe tests\_temp_resonance_party_cap_check.py
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from combat.ally import (MAX_ALLIES, get_ally_capacity, get_resonance_tier,
                         recruit_ally_from_house)
from resources.quests import get_grade_name
from wonderland_guests import resolve_late_arc

SAVE_DIR = Path(__file__).resolve().parent.parent / "savefile"


def _load(name):
    data = json.load(open(SAVE_DIR / name, encoding="utf-8"))
    return data.get("player") or data


def main():
    # 1. Capacity follows the Resonance grade, capped by MAX_ALLIES.
    chord = _load("savegame_4.json")          # tier 4 — 3 front / 2 bench
    crescendo = _load("savegame_1.json")      # tier 5 — 4 front / 4 bench

    print(f"chord:     tier {get_resonance_tier(chord)} "
          f"({get_grade_name(get_resonance_tier(chord))}) "
          f"capacity {get_ally_capacity(chord)}")
    print(f"crescendo: tier {get_resonance_tier(crescendo)} "
          f"({get_grade_name(get_resonance_tier(crescendo))}) "
          f"capacity {get_ally_capacity(crescendo)}")

    assert get_ally_capacity(chord) == 5, get_ally_capacity(chord)
    assert get_ally_capacity(crescendo) == MAX_ALLIES, get_ally_capacity(crescendo)
    assert len(chord["allies"]) > get_ally_capacity(chord)
    print("OK - capacity is front + bench (MAX_ALLIES-bound at Crescendo)")

    # 2. House recruitment at capacity must ask who makes room (cancel path),
    #    even though the roster is below MAX_ALLIES.
    from gui.terminal import term
    prompts = []

    def fake_menu(options, prompt=None, allow_cancel=False):
        prompts.append(prompt)
        return len(options) - 1          # "Cancel"

    orig_menu = term.menu
    term.menu = fake_menu
    try:
        girl = {"key": "slime_girl", "name": "Slime Girl", "affection": 90}
        house = {"monster_girls": [dict(girl)]}
        ally, msg = recruit_ally_from_house(chord, girl, house)
    finally:
        term.menu = orig_menu

    assert ally is None and msg == "Recruitment cancelled.", (ally, msg)
    assert prompts and "/5" in prompts[0], prompts
    print(f"OK - house recruit prompts at Resonance capacity ({prompts[0]})")

    # 3. A late Wonderland arc refuses to add the heroine when the roster is
    #    full for the grade.
    chord.setdefault("wonderland_guests", {})["alice"] = "late"
    ok, msg = resolve_late_arc(chord, "alice")
    print(f"late arc: ok={ok} msg={msg!r}")
    assert ok is False and "/5" in msg, (ok, msg)
    print("OK - late heroine arc respects Resonance capacity")

    print("\nAll Resonance party-cap checks passed.")


if __name__ == "__main__":
    main()
