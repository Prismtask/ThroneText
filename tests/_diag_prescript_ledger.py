"""Diagnostic: Prescript Ledger (Index-style mission accessory).

Run: python tests/_diag_prescript_ledger.py
Exit code 0 = all checks passed.
"""
import sys

sys.path.insert(0, ".")

import combat.weapon.prescript_ledger as pl
import inventory
import facilities.guild as guild
from resources.items import build_item
from combat.combat_ui import _get_entity_buff_tags

failures = []


def check(cond, label):
    if cond:
        print(f"  PASS  {label}")
    else:
        print(f"  FAIL  {label}")
        failures.append(label)


def make_actor(name="Tester", ally=False, max_hp=100):
    actor = {
        "name": name,
        "current_hp": max_hp,
        "max_hp": max_hp,
        "active_buffs": [],
        "active_debuffs": [],
        "equipped": {"accessory1": {"id": "prescript_ledger"}},
    }
    if ally:
        actor["is_ally"] = True
    return actor


# Bare-dict player HP override for the harness
pl.player_max_hp = lambda p: p.get("max_hp", 100)

print("== 1. Item definition ==")
item = build_item("prescript_ledger")
check(item.get("name") == "Prescript Ledger", "name Prescript Ledger")
check(item.get("slot") == "accessory", "accessory slot")
check(bool(item.get("unique")), "unique flag")

print("== 2. Equipment detection ==")
a1 = {"equipped": {"accessory1": {"id": "prescript_ledger"}}}
a2 = {"equipped": {"accessory2": {"id": "prescript_ledger"}}}
a3 = {"equipped": {"accessory": {"id": "prescript_ledger"}}}
bogus = {"equipped": {"accessory1": {"id": "sky_piercer"}}}
check(pl._actor_has_prescript_ledger(a1) and pl._actor_has_prescript_ledger(a2)
      and pl._actor_has_prescript_ledger(a3), "all three accessory slots detected")
check(not pl._actor_has_prescript_ledger(bogus), "wrong item not detected")

player = make_actor()
ally = make_actor("Ally", ally=True)
player["allies"] = [ally]
check(len(pl.get_wearers(player)) == 2, "wearers include player + ally")

print("== 3. Issue: mark + feasibile pool + no-repeat ==")
_orig_skill, _orig_item = pl._has_skill_action, pl._can_use_item
pl._has_skill_action = lambda *a, **k: False
pl._can_use_item = lambda *a, **k: False
try:
    enemies = [{"name": "A", "hp": 10}, {"name": "B", "hp": 10}]
    pl.issue_prescripts(player, enemies)
    marks = [e for e in enemies if e.get("prescript_mark")]
    check(len(marks) == 1, "exactly one Prescript's Target marked")
    kind1 = player["prescript_current"]["kind"]
    check(kind1 in ("target", "defend"), "feasible pool only (target/defend)")
    pl.issue_prescripts(player, enemies)
    kind2 = player["prescript_current"]["kind"]
    check(kind2 != kind1, "no immediate repeat")
    check(len([e for e in enemies if e.get("prescript_mark")]) == 1, "mark refreshed, single")
finally:
    pl._has_skill_action, pl._can_use_item = _orig_skill, _orig_item

print("== 4. Grace: stacks, single refresh, cap, atonement ==")
actor = make_actor()
actor["prescript_current"] = {"kind": "defend", "done": False}
pl.report_defend(actor)
check(actor.get("prescript_grace_stacks") == 1, "defend fulfil -> Grace 1")
dmg_buffs = [b for b in actor["active_buffs"] if b.get("source") == "prescript_grace_dmg"]
crit_buffs = [b for b in actor["active_buffs"] if b.get("source") == "prescript_grace_crit"]
check(len(dmg_buffs) == 1 and abs(dmg_buffs[0]["value"] - 0.02) < 1e-9, "single dmg aura +2%")
check(len(crit_buffs) == 1 and abs(crit_buffs[0]["value"] - 0.015) < 1e-9, "single crit aura +1.5%")

actor["prescript_current"] = {"kind": "defend", "done": False}
pl.report_defend(actor)
dmg_buffs = [b for b in actor["active_buffs"] if b.get("source") == "prescript_grace_dmg"]
check(actor["prescript_grace_stacks"] == 2 and len(dmg_buffs) == 1
      and abs(dmg_buffs[0]["value"] - 0.04) < 1e-9, "refresh in place (no duplicates)")

actor["prescript_karma_stacks"] = 2
actor["prescript_current"] = {"kind": "item", "done": False}
pl.report_item(actor)
check(actor["prescript_grace_stacks"] == 3 and actor["prescript_karma_stacks"] == 1,
      "atonement: fulfil -> Karma -1")

actor["prescript_grace_stacks"] = 9
actor["prescript_karma_stacks"] = 1
actor["prescript_current"] = {"kind": "defend", "done": False}
pl.report_defend(actor)
check(actor["prescript_grace_stacks"] == 9, "cap: no gain at 9")
check(actor["prescript_karma_stacks"] == 0, "cap: atonement still cleanses at 9")
actor["prescript_current"] = {"kind": "defend", "done": False}
pl.report_defend(actor)
check(actor["prescript_karma_stacks"] == 0, "cap: atonement with no Karma is a no-op")

print("== 5. Waiver + punish ==")
actor = make_actor()
actor["prescript_current"] = {"kind": "skill", "done": False}
actor["prescript_acted"] = False
pl.evaluate_round(actor, [])
check(actor.get("prescript_karma_stacks", 0) == 0, "no turn -> waived, no Karma")

actor["prescript_current"] = {"kind": "skill", "done": False}
actor["prescript_acted"] = True
pl.evaluate_round(actor, [])
check(actor["prescript_karma_stacks"] == 1, "ignored (acted) -> Karma 1")
vuln = [d for d in actor["active_debuffs"] if d.get("source") == "prescript_karma"]
check(len(vuln) == 1 and abs(vuln[0]["value"] - 0.03) < 1e-9, "Karma = vulnerable +3% (single refresh)")

print("== 6. Karmic Retribution at 6 ==")
actor = make_actor(max_hp=100)
actor["prescript_karma_stacks"] = 5
actor["prescript_current"] = {"kind": "skill", "done": False}
actor["prescript_acted"] = True
pl.evaluate_round(actor, [])
check(actor["prescript_karma_stacks"] == 0, "retribution consumes all 6")
check(actor["current_hp"] == 100 - (int(100 * 0.08) + 20), "sure-hit blow 8% max + 20")
check(not any(d.get("source") == "prescript_karma" for d in actor["active_debuffs"]),
      "Karma debuff cleared")

half = make_actor(max_hp=100)
half["prescript_karma_stacks"] = 5
half["prescript_current"] = {"kind": "skill", "done": False}
half["prescript_acted"] = True
half["prescript_defended"] = True
pl.evaluate_round(half, [])
check(half["current_hp"] == 100 - (int(100 * 0.08) + 20) // 2, "Defend halves retribution")

ward = make_actor(max_hp=100)
ward["current_hp"] = 1
ward["prescript_karma_stacks"] = 5
ward["prescript_current"] = {"kind": "skill", "done": False}
ward["prescript_acted"] = True
ward["active_buffs"] = [{"type": "death_ward", "remaining": 3}]
pl.evaluate_round(ward, [])
check(ward["current_hp"] == 1 and not any(b.get("type") == "death_ward" for b in ward["active_buffs"]),
      "Undying Vow honours the blow (survive at 1)")

print("== 7. Shed blood: damage report + auto-credit ==")
actor = make_actor()
actor["prescript_current"] = {"kind": "target", "target_name": "M", "done": False}
live_target = {"name": "M", "hp": 50, "prescript_mark": True}
pl.report_damage(actor, live_target)
check(actor.get("prescript_grace_stacks") == 1, "damage dealt to Target -> fulfilled (any attack)")
pl.report_damage(actor, live_target)
check(actor["prescript_grace_stacks"] == 1, "no double credit for extra hits")
bystander = {"name": "B", "hp": 50}
actor_b = make_actor()
actor_b["prescript_current"] = {"kind": "target", "done": False}
pl.report_damage(actor_b, bystander)
check(actor_b.get("prescript_grace_stacks", 0) == 0, "damage to a non-Target doesn't fulfill")

actor = make_actor()
actor["prescript_current"] = {"kind": "target", "target_name": "M", "done": False}
actor["prescript_acted"] = False
dead_targets = [{"name": "M", "hp": 0, "prescript_mark": True}]
pl.evaluate_round(actor, dead_targets)
check(actor["prescript_grace_stacks"] == 1, "marked Target fell -> auto-credit")
check(not any(e.get("prescript_mark") for e in dead_targets), "marks cleared at round end")

print("== 8. Clash empowerment ==")
target = {"name": "E", "hp": 50, "prescript_mark": True}
carrier = make_actor()
carrier["prescript_grace_stacks"] = 2
check(pl.get_clash_bonus(carrier, target) == 0.0, "below Grace 3 -> no clash bonus")
carrier["prescript_grace_stacks"] = 3
check(abs(pl.get_clash_bonus(carrier, target) - 0.10) < 1e-9, "Grace 3 -> +10%")
carrier["prescript_grace_stacks"] = 6
check(abs(pl.get_clash_bonus(carrier, target) - 0.20) < 1e-9, "Grace 6 -> +20%")
carrier["prescript_grace_stacks"] = 9
check(abs(pl.get_clash_bonus(carrier, target) - 0.30) < 1e-9, "Grace 9 -> +30%")
unmarked = {"name": "E2", "hp": 50}
check(pl.get_clash_bonus(carrier, unmarked) == 0.0, "unmarked target -> no bonus")
check(pl.get_clash_bonus(make_actor(), target) == 0.0, "non-wearer -> no bonus")

print("== 9. HUD tags ==")
tags = _get_entity_buff_tags({"prescript_grace_stacks": 4, "prescript_karma_stacks": 2})
check("GRC×4" in tags and "DBT×2" in tags, "GRC/DBT tags render")
check("📜TGT" in _get_entity_buff_tags({"prescript_mark": True}), "Target mark tag renders")

print("== 10. Grace regen ==")
actor = make_actor(max_hp=100)
actor["current_hp"] = 50
actor["prescript_grace_stacks"] = 3
pl.evaluate_round(actor, [])
check(actor["current_hp"] == 50 + int(100 * 0.015 * 3), "regen = 1.5% max HP per stack")

print("== 11. Reset cleans everything ==")
actor = make_actor()
actor["prescript_grace_stacks"] = 5
actor["prescript_karma_stacks"] = 3
actor["prescript_current"] = {"kind": "skill", "done": False}
pl._refresh_grace_buffs(actor)
pl._refresh_karma_debuff(actor)
player2 = make_actor()
player2["allies"] = [actor]
pl.reset_all_state(player2)
check("prescript_grace_stacks" not in player2 and "prescript_grace_stacks" not in actor,
      "counters cleared")
check("prescript_current" not in actor, "prescript state cleared")
check(actor["active_buffs"] == [] and actor["active_debuffs"] == [], "source buffs stripped")

print("== 12. Guild acquisition ==")


class _TermStub:
    def __init__(self, choice=-1):
        self.lines = []
        self.choice = choice

    def clear(self):
        pass

    def print(self, *a):
        self.lines.append(" ".join(str(x) for x in a))

    def pause(self):
        pass

    def menu(self, options, **kw):
        return self.choice


_orig_term = guild.term
_orig_add = inventory.add_item_to_inventory
granted = []
try:
    inventory.add_item_to_inventory = lambda p, i: granted.append(i) or True
    guild.term = _TermStub(choice=0)

    # A: not enough bounties -> rejected
    p = {"inventory": [], "sky_piercer_claimed": True}
    guild._legendary_rewards(p, "solmere")
    check(any("CLAIM REJECTED" in l for l in guild.term.lines), "0 bounties -> claim rejected")
    check(not p.get("prescript_ledger_claimed") and not granted, "no grant on rejection")

    # B: 10 Level 20+ bounties -> claim
    guild.term = _TermStub(choice=0)
    p = {"inventory": [], "sky_piercer_claimed": True, "high_bounties_completed": 10}
    guild._legendary_rewards(p, "solmere")
    check(p.get("prescript_ledger_claimed") is True, "10 Level 20+ bounties -> claimed")
    check(granted and granted[0].get("name") == "Prescript Ledger", "ledger granted via build_item")

    # C: both claimed -> closed
    guild.term = _TermStub(choice=0)
    p = {"inventory": [], "sky_piercer_claimed": True, "prescript_ledger_claimed": True}
    guild._legendary_rewards(p, "solmere")
    check(any("Both relics" in l for l in guild.term.lines), "both claimed -> ledger closed")
finally:
    guild.term = _orig_term
    inventory.add_item_to_inventory = _orig_add

print("== 12b. Level 20+ bounty gate ==")
gen_player = {"level": 30, "karma": 100, "karma_enabled": True}
gen = guild.generate_bounties(gen_player, "solmere")
check(bool(gen) and all("target_level" in b for b in gen), "bounties store target_level at generation")

pc = {}
guild._record_bounty_completion(pc, {"target_level": 25})
check(pc["bounties_completed"] == 1 and pc["high_bounties_completed"] == 1,
      "Level 25 bounty counts toward gate")
guild._record_bounty_completion(pc, {"target_level": 10})
check(pc["bounties_completed"] == 2 and pc["high_bounties_completed"] == 1,
      "Level 10 bounty only counts total")
check(guild._bounty_target_level({"target_level": 20}) == guild.HIGH_BOUNTY_LEVEL,
      "exactly Level 20 counts (>= gate)")

big_key = next(k for k, v in guild.ENEMIES.items()
               if v.get("level", 0) >= 20 and not v.get("boss") and not v.get("super_boss"))
small_key = next(k for k, v in guild.ENEMIES.items()
                 if 1 <= v.get("level", 0) <= 5 and not v.get("boss") and not v.get("super_boss"))
guild._record_bounty_completion(pc, {"target_enemy": big_key})
check(pc["high_bounties_completed"] == 2, "template fallback counts Level 20+ target")
guild._record_bounty_completion(pc, {"target_enemy": small_key})
check(pc["high_bounties_completed"] == 2 and pc["bounties_completed"] == 4,
      "template fallback rejects low-level target")

print()
if failures:
    print(f"FAILED: {len(failures)} check(s)")
    for f in failures:
        print("  -", f)
    sys.exit(1)
print("All checks passed.")
