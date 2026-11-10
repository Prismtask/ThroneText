# tests/_temp_bleed_unify_check.py
# Temporary smoke checks for the unified bleed core + percentage slow/weaken.
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from combat.status_effects import (
    apply_bleed, apply_weaken, get_weaken_pct, apply_slow_to_enemy, apply_slow_to_player,
    apply_slow_penalty, tick_enemy_debuffs, tick_player_debuffs, is_cleansable,
    cure_bleed, detonate_bleed, SLOW_DEX_PCT, WEAKEN_STR_PCT,
)
from combat.weapon.blank_canvas_shawl import _cleanse_actor

# ── 1. Bleed core: apply / refresh / weaker-refresh ──────────────────────────
t = {"name": "Dummy", "hp": 100, "active_debuffs": []}
assert apply_bleed(t, 3, 3) == "applied"
assert t["active_debuffs"][0]["damage"] == 3

# Equal damage refreshes duration (was a no-op before)
assert apply_bleed(t, 3, 3) == "refreshed"
assert t["active_debuffs"][0]["remaining"] == 3 and len(t["active_debuffs"]) == 1

# Weaker application refreshes duration, keeps stronger damage
t["active_debuffs"][0]["remaining"] = 1
assert apply_bleed(t, 2, 4) == "refreshed"
assert t["active_debuffs"][0]["damage"] == 3      # kept strongest
assert t["active_debuffs"][0]["remaining"] == 4   # extended

# Stronger replaces damage + refreshes
assert apply_bleed(t, 6, 3) == "refreshed"
assert t["active_debuffs"][0]["damage"] == 6

# ── 2. Uncleansable wound: own slot, coexist, cleanse-proof ─────────────────
assert apply_bleed(t, 10, 4, source="vorpal_wound", uncleansable=True) == "applied"
assert len(t["active_debuffs"]) == 2
wound = next(d for d in t["active_debuffs"] if d.get("_uncleansable"))
assert not is_cleansable(wound) and is_cleansable(t["active_debuffs"][0])

# Normal applicaton must not touch the wound slot, wound must not touch normal
apply_bleed(t, 1, 9)
assert wound["damage"] == 10 and wound["remaining"] == 4
apply_bleed(t, 20, 1, uncleansable=True)  # stronger wound replaces, keeps longer duration
assert wound["damage"] == 20 and wound["remaining"] == 4

# cure_bleed removes only the cleansable one
assert cure_bleed({"active_debuffs": [dict(wound)]}) == "not_bleeding"
mixed = {"active_debuffs": [dict(wound), {"type": "bleed", "damage": 3, "remaining": 2}]}
assert cure_bleed(mixed) == "cured"
assert len(mixed["active_debuffs"]) == 1 and mixed["active_debuffs"][0]["_uncleansable"]

# ── 3. detonate_bleed consumes the strongest wound ──────────────────────────
t2 = {"name": "Dummy", "hp": 100, "active_debuffs": [
    {"type": "bleed", "damage": 3, "remaining": 2},
    {"type": "bleed", "damage": 6, "remaining": 2},
]}
dmg, msgs = detonate_bleed(t2)
assert dmg == 18 and t2["hp"] == 82, (dmg, t2["hp"], msgs)
assert len(t2["active_debuffs"]) == 1 and t2["active_debuffs"][0]["damage"] == 3

# ── 4. Weaken percentage ────────────────────────────────────────────────────
p = {"name": "Player", "active_debuffs": []}
apply_weaken(p, duration=3)
assert get_weaken_pct(p) == WEAKEN_STR_PCT
apply_weaken(p, penalty_pct=0.10, duration=2)      # weaker does not downgrade
assert get_weaken_pct(p) == WEAKEN_STR_PCT
assert apply_weaken(p, penalty_pct=0.40, duration=2) == "refreshed"
assert get_weaken_pct(p) == 0.40

# ── 5. Slow percentage + flag lifecycle ─────────────────────────────────────
e = {"name": "Dummy", "hp": 100, "active_debuffs": [], "active_buffs": []}
apply_slow_to_enemy(e, duration=1)
assert e.get("slowed") is True
assert apply_slow_penalty(e, 20) == int(20 * (1.0 - SLOW_DEX_PCT)) == 15
msgs, died = tick_enemy_debuffs(e)   # remaining 1 -> expires this tick
assert e.get("slowed") is False and not e["active_debuffs"]
assert apply_slow_penalty(e, 20) == 20

p2 = {"name": "Player", "current_hp": 100, "active_debuffs": [], "attributes": {}, "level": 1}
apply_slow_to_player(p2, duration=1)
assert p2.get("slowed") is True
tick_player_debuffs(p2)
assert p2.get("slowed") is False

# ── 6. Cleanse filter: Blank Canvas keeps the uncleansable wound ────────────
actor = {"name": "Actor", "active_debuffs": [
    {"type": "poison", "damage": 3, "remaining": 2},
    {"type": "bleed", "damage": 10, "remaining": 4, "_uncleansable": True},
]}
_cleanse_actor(actor)
assert len(actor["active_debuffs"]) == 1 and actor["active_debuffs"][0]["type"] == "bleed"

print("ALL BLEED/SLOW/WEAKEN UNIFY CHECKS PASSED")
