"""Diagnostic: Moonlight Greatsword unique weapon.

Verifies:
  1. Item registration: unique greatsword, PHYSICAL base element, documented
     examine effect, greatsword form tag.
  2. State machine: Moonlight activation (3 turns, 5-turn cooldown), availability,
     tick order, clear.
  3. Player action menu exposes [M] Moonlight only while the skill is ready.
  4. Empowered basic attack: hits EVERY living enemy, deals [MAGICAL] damage,
     and leaves non-empowered actors untouched.

Run: C:/Code/Pandemonium/.venv/Scripts/python.exe tests/_diag_moonlight_greatsword.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import combat.weapon.moonlight_greatsword as moon
from resources.items import ITEMS, build_item
from resources.unique_effects import unique_effect_text

_failures = []
_logs = []


def check(label, cond, detail=""):
    status = "PASS" if cond else "FAIL"
    print(f"[{status}] {label}" + (f" — {detail}" if detail and not cond else ""))
    if not cond:
        _failures.append(label)


def _capture(*args, **kwargs):
    _logs.append(" ".join(str(a) for a in args))


moon.c_print = _capture

ATTRS = {a: 10 for a in ("Strength", "Constitution", "Dexterity",
                         "Wisdom", "Learning", "Charisma")}


def make_player(weapon=None):
    return {
        "name": "Hero", "class": None, "level": 20,
        "attributes": dict(ATTRS),
        "current_hp": 100, "max_hp": 100,
        "passive_unlocked": False,
        "equipped": {"weapon": weapon, "armor": None,
                     "accessory1": None, "accessory2": None},
        "active_buffs": [], "active_debuffs": [],
        "elemental_dmg": {}, "elemental_res": {},
        "skills": [], "skill_cooldowns": {}, "skill_mastery": {},
        "inventory": [], "allies": [],
    }


def make_enemy(name="Dummy", hp=500):
    return {
        "name": name, "hp": hp, "max_hp": hp,
        "con_mod": 0, "dex_mod": 0,
        "active_buffs": [], "active_debuffs": [],
        "elemental_res": {}, "elemental_dmg": {},
        "captured": False, "boss": False, "super_boss": False,
    }


# ── 1. Item registration ─────────────────────────────────────────────────
base = ITEMS.get("moonlight_greatsword")
check("item registered", base is not None)
check("unique weapon slot", base.get("unique") and base.get("slot") == "weapon")
check("greatsword form tag", base.get("form") == "greatsword", base.get("form"))
check("physical base element", base.get("elemental_dmg", {}).get("physical"), base)

item = build_item("moonlight_greatsword", "unique")
check("built as unique", item.get("rarity") == "unique")
check("instance primary element physical", item.get("primary_element") == "physical")
check("instance physical profile", item.get("elemental_dmg") == {"physical": 1.35},
      item.get("elemental_dmg"))
check("special wired", item.get("special") == "moonlight_greatsword")
check("examine blurb exists", bool(unique_effect_text("moonlight_greatsword")))

# ── 2. State machine ─────────────────────────────────────────────────────
player = make_player(item)
enemies = [make_enemy()]

check("detected when equipped", moon._actor_has_moonlight_greatsword(player) is not None)
check("available at combat start", moon.is_moonlight_available(player))
check("not active before use", not moon.is_moonlight_active(player))

result, _def = moon.use_moonlight(player)
check("activation consumes turn", result == "continue")
check("light is pending, not active yet",
      player.get("moonlight_pending") == moon.MOONLIGHT_DURATION
      and player.get("moonlight_turns", 0) == 0)
check("cooldown set", player["moonlight_cooldown"] == moon.MOONLIGHT_COOLDOWN,
      player.get("moonlight_cooldown"))
check("not active on activation round", not moon.is_moonlight_active(player))
check("not available while active", not moon.is_moonlight_available(player))

result2, _ = moon._use_moonlight_actor(player, is_player=True)
check("second activation refused", result2 == "retry")

check("round start activates the light",
      moon.apply_moonlight_round_start(player) is True)
check("active after round start", moon.is_moonlight_active(player))
check("duration set", player["moonlight_turns"] == moon.MOONLIGHT_DURATION,
      player.get("moonlight_turns"))

moon.tick_moonlight(player)
moon.tick_moonlight(player)
check("still active after 2 rounds", moon.is_moonlight_active(player))
moon.tick_moonlight(player)
check("fades after 3 rounds", not moon.is_moonlight_active(player))
check("cooldown still running", player["moonlight_cooldown"] == 2,
      player.get("moonlight_cooldown"))
moon.tick_moonlight(player)
moon.tick_moonlight(player)
check("ready after cooldown ticks", moon.is_moonlight_available(player))
check("status line shows ready (empty)", moon.get_moonlight_status_display(player) == "")

player["moonlight_turns"] = 2
player["moonlight_cooldown"] = 5
check("status line shows active",
      "active: 2" in moon.get_moonlight_status_display(player))
player["moonlight_turns"] = 0
player["moonlight_pending"] = 3
check("status line shows gathering",
      "gathering" in moon.get_moonlight_status_display(player))
actor_to_clear = player
moon.clear_moonlight_state(actor_to_clear)
check("clear resets all fields",
      actor_to_clear["moonlight_turns"] == 0
      and actor_to_clear["moonlight_cooldown"] == 0
      and "moonlight_pending" not in actor_to_clear,
      actor_to_clear)

# ── 3. Action menu ───────────────────────────────────────────────────────
from combat.action_menu import get_action_menu

player = make_player(item)
menu, valid, _disabled = get_action_menu(player, enemies)
check("menu offers Moonlight", "m" in valid and "Moonlight" in menu, menu)
player["moonlight_cooldown"] = 2
menu2, valid2, _ = get_action_menu(player, enemies)
check("menu hides Moonlight on cooldown", "m" not in valid2, menu2)

# ── 4. Empowered AoE attack ──────────────────────────────────────────────
player = make_player(item)
player["moonlight_turns"] = 3
enemies = [make_enemy("Slime A"), make_enemy("Slime B"), make_enemy("Slime C")]
_logs.clear()
moon.execute_moonlight_aoe_attack(
    player, player, enemies, (10, 10, 10, 10, 10, 10), is_player=True,
)
check("all enemies damaged", all(e["hp"] < e["max_hp"] for e in enemies),
      [e["hp"] for e in enemies])
check("damage logged as magical", sum("[MAGICAL]" in line for line in _logs) == 3,
      _logs)
check("wave announcement logged", any("Moonlight spills" in line for line in _logs))

# Non-empowered / non-wielding actors cannot run the AoE.
plain = make_player(None)
before = [e["hp"] for e in enemies]
moon.execute_moonlight_aoe_attack(
    plain, plain, enemies, (10, 10, 10, 10, 10, 10), is_player=True,
)
check("no weapon → no AoE", [e["hp"] for e in enemies] == before)

# Ally actor works through the same module.
ally = make_player(item)
ally.update({"is_ally": True, "race": "Human", "max_hp": 100})
ally["moonlight_turns"] = 3
enemies = [make_enemy("Slime D"), make_enemy("Slime E")]
_logs.clear()
moon.execute_moonlight_aoe_attack(
    ally, make_player(None), enemies, (10, 10, 10, 10, 10, 10), is_player=False,
)
check("ally AoE damages all", all(e["hp"] < e["max_hp"] for e in enemies),
      [e["hp"] for e in enemies])

# ── 5. Turn-handler integration (player 'a' action) ──────────────────────
import combat.player_actions as pa

pa.c_print = _capture
pa.c_input = lambda *a, **k: "1"
player = make_player(item)
player["moonlight_turns"] = 3
enemies = [make_enemy("Slime F"), make_enemy("Slime G")]
_logs.clear()
result, defending = pa.handle_player_turn(
    player, enemies, 10, 10, 10, 10, 10, 10, _action_override="a",
)
check("turn handler continues after AoE", result == "continue" and not defending,
      result)
check("turn handler damages every enemy",
      all(e["hp"] < e["max_hp"] for e in enemies), [e["hp"] for e in enemies])

# ── 6. Guild Legendary Rewards claim ─────────────────────────────────────
import facilities.guild as guild_mod


class _QuietTerm:
    def print(self, *a, **k):
        pass

    def pause(self, *a, **k):
        pass

    def clear(self):
        pass


guild_mod.term = _QuietTerm()
claim_player = make_player(None)
claim_player["inventory"] = []
guild_mod._legendary_moon_claim(claim_player, 3, 0)
check("claim rejected below requirement",
      not claim_player.get("moonlight_greatsword_claimed"))
guild_mod._legendary_moon_claim(claim_player, 3, 3)
check("claim succeeds at requirement",
      claim_player.get("moonlight_greatsword_claimed")
      and any(it.get("id") == "moonlight_greatsword"
              for it in claim_player["inventory"]),
      claim_player.get("inventory"))

if _failures:
    print(f"\nFAILED: {len(_failures)} check(s): {', '.join(_failures)}")
    sys.exit(1)
print("\nmoonlight greatsword diagnostics OK")
