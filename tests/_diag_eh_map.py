"""
tests/_diag_eh_map.py — Manual check of Event Horizon world-map entry (Phase 3).

Not collected by pytest (underscore prefix). Run directly:
    c:/Code/Pandemonium/.venv/Scripts/python.exe tests/_diag_eh_map.py

Verifies the non-GUI logic behind the world-map site:
  1. Unlock gate — hidden at max_floor 19/20 (Floor 20 not cleared),
     visible at 21; existing rift progress is grandfathered
  2. Site fields — id/name/position/nearest_city
  3. Journey builder — city route + off-road leg ends at "horizon"
  4. Wild regression — build_journey_to_dungeon default still targets wild:<id>
  5. Run lifecycle — begin_run fresh vs resume, clear_run keeps best_room
  6. GUI wiring smoke — source strings present in the three screens
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import event_horizon as eh
import wild_dungeons as wd

_results = []


def check(label, cond, detail=""):
    status = "ok" if cond else "FAIL"
    _results.append(status)
    line = f"  [{status}] {label}"
    if detail and not cond:
        line += f"  ({detail})"
    print(line)


def _fresh_player(max_floor=19):
    return {
        "name": "Diag",
        "gold": 10000,
        "location": "solmere",
        "day": 3,
        "max_floor": max_floor,
        "allies": [],
        "floor": 1,
        "inventory": [],
    }


print("── 1. Unlock gate ─────────────────────────────────────────")
p = _fresh_player(19)
check("locked at max_floor 19", eh.site_unlocked(p) is False)
check("site None while locked", eh.event_horizon_site(p) is None)
check("journey None while locked", eh.build_journey_to_site(p) is None)
p["max_floor"] = 20
check("locked at max_floor 20 (reached, not cleared)",
      eh.site_unlocked(p) is False)
check("site None at max_floor 20", eh.event_horizon_site(p) is None)
p["max_floor"] = 21
check("unlocked at max_floor 21 (Floor 20 cleared)",
      eh.site_unlocked(p) is True)
p["max_floor"] = 20
p["eh_intro_seen"] = True
check("grandfathered by intro seen", eh.site_unlocked(p) is True)
p["eh_intro_seen"] = False
p["event_horizon"] = {"best_room": 4}
check("grandfathered by rift progress", eh.site_unlocked(p) is True)
p = _fresh_player(21)

print("── 2. Site fields ─────────────────────────────────────────")
site = eh.event_horizon_site(p)
check("site returned", site is not None)
check("site id", site.get("id") == "event_horizon")
check("site name", site.get("name") == eh.EVENT_HORIZON_NAME)
check("site position", site.get("position") == eh.EVENT_HORIZON_POSITION,
      f"got {site.get('position')}")
check("nearest city", bool(site.get("nearest_city")),
      f"got {site.get('nearest_city')!r}")
check("near city reachable from map", site.get("nearest_city") in wd.CITIES
      if hasattr(wd, "CITIES") else True)

print("── 3. Journey to the distortion ───────────────────────────")
journey = eh.build_journey_to_site(p)
check("journey built", journey is not None)
if journey:
    check("has path/segments/time/cost keys",
          all(k in journey for k in
              ("path", "segments", "total_time", "total_cost")))
    check("path ends at 'horizon'", journey["path"][-1] == "horizon",
          f"got {journey['path'][-1]!r}")
    last_seg = journey["segments"][-1]
    check("final segment to == 'horizon'", last_seg.get("to") == "horizon",
          f"got {last_seg.get('to')!r}")
    check("final segment is synthetic off-road leg",
          last_seg.get("type") == "land" and "raw_time" in last_seg,
          f"got type={last_seg.get('type')!r}")
    check("path starts at a city", journey["path"][0] in wd.CITIES,
          f"got {journey['path'][0]!r}")
    print(f"    route: {' → '.join(map(str, journey['path']))}"
          f"  ({journey['total_time']} min, {journey['total_cost']}g)")

print("── 4. Wild journey regression ─────────────────────────────")
dungeon = {
    "id": "diag_ruin",
    "name": "Diag Ruin",
    "position": (600, 420),
    "biome": "forest",
    "level": 10,
}
wp = _fresh_player(20)
wjourney = wd.build_journey_to_dungeon(wp, dungeon)
check("wild journey built", wjourney is not None)
if wjourney:
    check("wild path ends at wild:diag_ruin",
          wjourney["path"][-1] == "wild:diag_ruin",
          f"got {wjourney['path'][-1]!r}")
    check("wild final segment to", wjourney["segments"][-1].get("to")
          == "wild:diag_ruin")

print("── 5. Run lifecycle ───────────────────────────────────────")
p = _fresh_player(25)
state = eh.begin_run(p, "solmere")
check("fresh run active", state.get("run_active") is True)
check("fresh run room 0", int(state.get("room", -1)) == 0)
check("origin city recorded", state.get("origin_city") == "solmere")
state["room"] = 12
state["motes"] = 40
state["best_room"] = 9
state2 = eh.begin_run(p, "solmere")
check("resume keeps room", int(state2.get("room", -1)) == 12)
check("resume keeps motes", int(state2.get("motes", -1)) == 40)
# payout + clear
p["gold"] = 0
amount, deferred = eh.grant_payout(p, death=False)
check("payout paid", amount > 0 and p["gold"] == amount and not deferred,
      f"amount={amount} gold={p['gold']} deferred={deferred}")
best = eh.clear_run(p)
check("clear keeps best_room", best == 12, f"got {best}")
check("clear wipes run_active",
      not p["event_horizon"].get("run_active"))
check("clear removes _eh_in_run flag", "_eh_in_run" not in p)
# death defers
p2 = _fresh_player(25)
eh.begin_run(p2, "solmere")
p2["event_horizon"]["room"] = 30
p2["gold"] = 0
amount2, deferred2 = eh.grant_payout(p2, death=True)
check("death payout deferred", deferred2 and p2["gold"] == 0
      and p2.get("_eh_pending_payout") == amount2,
      f"amount={amount2} deferred={deferred2} gold={p2['gold']}")

print("── 6. GUI wiring smoke (source strings) ───────────────────")
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read(rel):
    with open(os.path.join(root, rel), encoding="utf-8") as f:
        return f.read()


wm = _read("gui/screens/world_map_screen.py")
check("world map draws EH marker", "self._draw_event_horizon()" in wm)
check("world map has travel handler", "_on_travel_to_horizon" in wm)
check("world map has arrival handler", "_arrive_at_horizon" in wm)
check("world map routes EH result", "_on_eh_result" in wm)
check("world map arrival scene router", "_after_eh_scene" in wm)
check("world map travel-stop helper", "_stop_travel_visuals" in wm)
check("world map summary router", "_show_eh_summary_then" in wm)
check("world map clears stale dungeon log",
      'player.pop("_dungeon_log", None)' in wm)
check("summary dialog widget exists",
      "def run_summary_dialog" in _read("gui/widgets/run_summary_dialog.py"))
loaded = _fresh_player(20)
eh.ensure_eh_state(loaded)
s = eh.build_run_summary(loaded, payout=0)
check("summary builder runs on fresh state",
      any("Rooms cleared" in ln for ln in s["lines"]))
check("summary data keys", {"room", "best", "payout", "fatal"}
      <= set(s["data"].keys()))
band_p = _fresh_player(20)
check("band low rooms standard",
      eh.enemy_band_for_room(band_p, 1) == (20, 12))
check("band capped at depth",
      eh.enemy_band_for_room(band_p, 200) == (56, 30))

ei = _read("facilities/event_horizon_intro.py")
check("arrival scene service", "event_horizon_arrival_service" in ei)
check("resume menu option", "Resume the descent" in ei)
check("abandon menu option", "Abandon the run & start fresh" in ei)
check("ask menu option", "Ask about the distortion" in ei)
check("Vesper greeting planner", "plan_vesper_greeting" in ei)
check("Vesper idle pool", "_EH_IDLE_GREETINGS" in ei)
check("Vesper milestone acknowledgment", "eh_vesper_milestone" in ei)

ds = _read("gui/screens/dungeon_screen.py")
check("dungeon screen sets _eh_run", "self._eh_run = False" in ds)
check("dungeon screen EH branding", "Event Horizon" in ds)
check("dungeon screen room top bar", "Room {floor}" in ds)
check("dungeon leave button EH label", "Leave Rift" in ds)
check("dungeon EH leave confirm text", "no fleeing the rift" in ds)
check("flee confirm defaults to No", "focus_no=True" in ds)
check("EH suspend message on leave", "step out of the rift" in wm)

cs = _read("gui/screens/city_screen.py")
check("city screen intro hook", "_maybe_event_horizon_intro" in cs)
check("city screen intro launcher", "event_horizon_intro_service" in cs)
check("city screen scrubs flag", '_eh_in_run' in cs)

er = _read("event_horizon_rooms.py")
check("EH shop trades flasks", "_shop_flask_price" in er
      and "EH_SHOP_GOODS" not in er)
check("EH flask drinker helper", "_choose_flask_drinker" in er)
dm = _read("dungeon_rooms.py")
check("EH rift status renderer", "def render_event_horizon_status" in dm)
dg = _read("dungeon.py")
check("EH loop refreshes side panels", "_eh_refresh_hud" in dg)
check("dungeon screen EH status hook", "render_event_horizon_status" in ds)
fs = _read("gui/screens/facility_screen.py")
check("choice buttons uniform focus", "highlightcolor=bg" in fs)
check("choice buttons row-stretch", 'sticky="nsew"' in fs)
check("EH shop discount", "SALE" in er)
check("EH entropy step helper", "entropy_stat_penalty" in _read("event_horizon.py"))
check("EH card deck rule", "_picked_entries" in _read("event_horizon.py"))
check("EH joker wiring", "JOKER_CARD" in _read("event_horizon.py")
      and "offer_joker" in er)
check("EH joker hand model", "EH_JOKER_HAND_CAP" in _read("event_horizon.py")
      and "deal_joker_faces" in _read("event_horizon.py")
      and "discard_joker" in _read("event_horizon.py"))

print("── 7. Vesper greeting smoke ───────────────────────────────")
from facilities.event_horizon_intro import plan_vesper_greeting

vp = _fresh_player(25)
vstate = eh.ensure_eh_state(vp)
first = "\n".join(plan_vesper_greeting(vp, vstate, 0, False))
check("first-visit greeting", "You came. Good." in first)
vstate["run_active"] = True
vstate["room"] = 25
ms = "\n".join(plan_vesper_greeting(vp, vstate, 25, True))
check("r25 milestone first time", "Twenty-five" in ms)
check("milestone acknowledged once", vp.get("eh_vesper_milestone") == 25)
again = "\n".join(plan_vesper_greeting(vp, vstate, 25, True))
check("milestone not repeated", "Twenty-five" not in again)
later = "\n".join(plan_vesper_greeting(vp, vstate, 25, True))
check("idle lines vary", later != again)

import dungeon_rooms as dr
status = dr.render_event_horizon_status(vp)
check("rift status renders", "E V E N T   H O R I Z O N" in status
      and "Room" in status and "Entropy" in status)
check("entropy step penalty", abs(eh.entropy_stat_penalty(137) - 0.18) < 1e-9
      and abs(eh.entropy_stat_penalty(300) - eh.EH_ENTROPY_CAP) < 1e-9)
eh.apply_joker(vp)
_jname = vp["event_horizon"]["joker_cards"][-1]["name"]
check("joker trade-off applied",
      any(b.get("label") == _jname for b in vp["active_buffs"])
      and any(d.get("label") == _jname and d.get("type") == "slow"
              for d in vp["active_debuffs"]))

print()
fails = _results.count("FAIL")
print(f"── {len(_results) - fails}/{len(_results)} checks passed "
      f"({fails} failed) ──")
sys.exit(1 if fails else 0)
