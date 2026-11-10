# tests/_temp_vampire_bleed_check.py
# Verify vampire drain doubles vs bleeding targets (agreed bleed-consumption hook).
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from combat.enemy_ai import get_race_extra_logic
from combat.status_effects import apply_bleed, is_bleeding

enemy = {"name": "Vampire Fledgling", "key": "vampire_fledgling", "hp": 40, "max_hp": 40}
fn = get_race_extra_logic(enemy)
assert fn is not None

# Baseline: half damage drained
player = {"name": "You", "current_hp": 100, "active_debuffs": []}
assert not is_bleeding(player)
msg = fn(enemy, player, 20)
assert player["current_hp"] == 90, (msg, player["current_hp"])
assert "life force" in msg

# Bleeding: full damage drained
apply_bleed(player, 3, 3)
assert is_bleeding(player)
player["current_hp"] = 100
enemy["hp"] = 40
msg = fn(enemy, player, 20)
assert player["current_hp"] == 80, (msg, player["current_hp"])
assert "open wound" in msg

# Ally side: same feast multiplier feeds the Vampire race passive
from combat.status_effects import get_bleed_feast_multiplier
assert get_bleed_feast_multiplier(player) == 2.0      # player still bleeding
fresh = {"name": "Foe", "hp": 20, "active_debuffs": []}
assert get_bleed_feast_multiplier(fresh) == 1.0
# Ally heal math sanity: 25% of 20 -> 5 normally, 10 while feasting
assert int(20 * 0.25 * get_bleed_feast_multiplier(fresh)) == 5
assert int(20 * 0.25 * get_bleed_feast_multiplier(player)) == 10

print("VAMPIRE BLEED DRAIN CHECKS PASSED")
