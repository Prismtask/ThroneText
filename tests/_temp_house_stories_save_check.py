"""Read-only check: Fireside Tales against the real savefile (no writes)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import save_load
from character import ensure_player_fields
from resources.house_stories import HOUSE_STORIES
import facilities.house_stories as hs

player = save_load.load_game(1)
assert player, "savegame_1 not found"
ensure_player_fields(player)

print("houses:", {k: v.get("level") for k, v in (player.get("houses") or {}).items()})
print("met_voss:", (player.get("quests") or {}).get("flags", {}).get("met_voss"))
print("owned girls:", len(hs.all_owned_girls(player)))
print("ready in skylume:", hs.available_ready_count(player, "skylume"))
print("ready in solmere:", hs.available_ready_count(player, "solmere"))
for sid, story in HOUSE_STORIES.items():
    info = hs.story_status(player, story, "skylume")
    print(f"  {story['title']}: {info['state']} "
          f"({info['seen']}/{info['total']}) "
          f"next={info['next_part']['id'] if info['next_part'] else '-'} "
          f"missing={info['missing']}")
print("city claim in skylume:", (hs.claim_city_trigger(player, "skylume") or {}).get("id"))
print("house_stories state:", player.get("house_stories"))
