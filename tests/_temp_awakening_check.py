# tests/_temp_awakening_check.py
# Verify the Awakening system (docs/awakening_design.md Part C):
#   YAML shape, skill swap + carry-over, display names, gating,
#   forge math, reward grants + migration, and awakened skill execution.
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from combat.ally_skills import (
    AWAKENINGS,
    INNATE_SKILL_DEFS,
    INNATE_SKILLS_MAP,
    apply_awakening_skills,
    get_awakened_skill_ids,
    get_innate_skill_def,
    has_awakening,
    initialize_ally_skills,
    execute_ally_skill,
)
from combat.ally import create_ally_from_girl, _ally_to_house_record
from character import _migrate_awakening_rewards
from facilities.arcane_tower import can_forge_sigil, forge_sigil
from facilities.house import can_awaken_girl, _fmt_dialogue
from utils import display_name, display_name_with_species

ATTRS = ("Strength", "Constitution", "Dexterity", "Wisdom", "Learning", "Charisma")

print("=== Awakening check (docs/awakening_design.md Part C) ===")

# ── 1. YAML shape ─────────────────────────────────────────────────────────
assert len(AWAKENINGS) == 12, len(AWAKENINGS)
for key, mapping in AWAKENINGS.items():
    assert len(mapping) == 2, key
    assert key in INNATE_SKILLS_MAP, key
    for base_id, upgraded_id in mapping.items():
        assert base_id in INNATE_SKILLS_MAP[key], (key, base_id)
        assert upgraded_id in INNATE_SKILL_DEFS, (key, upgraded_id)
        assert INNATE_SKILL_DEFS[upgraded_id].get("awakened_from") == base_id, upgraded_id
assert get_innate_skill_def("lucky_volley")["name"] == "Lucky Volley"
print("1. 12 girls / 24 awakened defs wired to their base skills  [ok]")

# ── 2. Swap + mastery / cooldown carry-over ───────────────────────────────
rec = {
    "key": "goblin_girl",
    "innate_skills": list(INNATE_SKILLS_MAP["goblin_girl"]),
    "skill_mastery": {"goblin_dart": 90, "goblin_evasion": 10},
    "skill_cooldowns": {"goblin_dart": 2},
}
assert has_awakening("goblin_girl") and not has_awakening("lich_queen_avatar")
assert apply_awakening_skills(rec, "goblin_girl") is True
assert rec["awakened_skills"] == ["lucky_volley", "fortunes_veil"]
assert rec["innate_skills"] == ["lucky_volley", "fortunes_veil"], rec["innate_skills"]
assert rec["skill_mastery"] == {"lucky_volley": 90, "fortunes_veil": 10}
assert rec["skill_cooldowns"] == {"lucky_volley": 2}
# Idempotency: a second call changes nothing
apply_awakening_skills(rec, "goblin_girl")
assert rec["skill_mastery"] == {"lucky_volley": 90, "fortunes_veil": 10}
assert rec["skill_cooldowns"] == {"lucky_volley": 2}
assert rec["innate_skills"] == ["lucky_volley", "fortunes_veil"]
# House-record flavour: no innate list → rebuilt from the map
house_rec = {"key": "slime_girl"}
apply_awakening_skills(house_rec, "slime_girl")
assert house_rec["awakened_skills"] == ["adaptive_membrane", "corrosive_deluge"]
assert house_rec["innate_skills"] == ["adaptive_membrane", "corrosive_deluge"]
assert get_awakened_skill_ids("slime_girl") == ["adaptive_membrane", "corrosive_deluge"]
assert get_awakened_skill_ids("grave_queen") == []
print("2. swap + mastery/cooldown carry-over + idempotent rebuild  [ok]")

# ── 3. Swap-aware initialize ──────────────────────────────────────────────
ally_a = {"awakened": True, "awakened_skills": []}
initialize_ally_skills(ally_a, "goblin_girl", "Goblin")
assert ally_a["innate_skills"] == ["lucky_volley", "fortunes_veil"], ally_a["innate_skills"]
assert ally_a["awakened_skills"] == ["lucky_volley", "fortunes_veil"]
ally_b = {}
initialize_ally_skills(ally_b, "goblin_girl", "Goblin")
assert ally_b["innate_skills"] == ["goblin_dart", "goblin_evasion"], ally_b["innate_skills"]
print("3. initialize_ally_skills honours the awakened flag  [ok]")

# ── 4. Display names: nickname → awakened_name → name ─────────────────────
plain = {"name": "Goblin Girl"}
awakened = {"name": "Goblin Girl", "awakened_name": "Goblin Deadeye"}
both = {"name": "Goblin Girl", "awakened_name": "Goblin Deadeye", "nickname": "Lucky"}
assert display_name(plain) == "Goblin Girl"
assert display_name(awakened) == "Goblin Deadeye"
assert display_name(both) == "Lucky"
assert display_name_with_species(awakened) == "Goblin Deadeye"
assert display_name_with_species(both) == "Lucky (Goblin Deadeye)"
assert display_name_with_species(plain) == "Goblin Girl"
print("4. display_name resolution (nickname > awakened > species)  [ok]")

# ── 5. Prereq gating ──────────────────────────────────────────────────────
def gl(key, level=40, cap=40, aff=150, **kw):
    g = {"key": key, "level": level, "level_cap": cap, "affection": aff}
    g.update(kw)
    return g

assert can_awaken_girl(gl("goblin_girl"))[0]
assert not can_awaken_girl(gl("goblin_girl", level=39))[0]
assert not can_awaken_girl(gl("goblin_girl", cap=30))[0]
assert not can_awaken_girl(gl("goblin_girl", aff=149))[0]
assert not can_awaken_girl(gl("goblin_girl", awakened=True))[0]
assert not can_awaken_girl(gl("grave_queen"))[0]
assert can_awaken_girl(gl("goblin_girl", awakened=True))[1] == "already awakened"
print("5. level / cap / affection / candidate gating  [ok]")

# ── 6. Forge math ─────────────────────────────────────────────────────────
p = {"awakening_shards": 4, "gold": 25000, "awakening_sigils": 0}
assert can_forge_sigil(p)
assert forge_sigil(p)
assert p == {"awakening_shards": 0, "gold": 0, "awakening_sigils": 1}
assert not can_forge_sigil(p) and not forge_sigil(p)
p2 = {"awakening_shards": 7, "gold": 26000, "awakening_sigils": 3}
assert forge_sigil(p2) and p2["awakening_shards"] == 3 and p2["gold"] == 1000 and p2["awakening_sigils"] == 4
p3 = {"awakening_shards": 4, "gold": 24999, "awakening_sigils": 0}
assert not forge_sigil(p3) and p3["awakening_shards"] == 4 and p3["gold"] == 24999
print("6. forge: 4 shards + 25,000g → 1 Sigil, exact-boundary cases  [ok]")

# ── 7. Reward grants are idempotent (dungeon helpers) ─────────────────────
from dungeon import _check_first_superboss_sigil, _grant_awakening_shard, _grant_awakening_sigil

p = {}
_check_first_superboss_sigil(p)
assert p["awakening_sigils"] == 1 and p["awakening_intro_granted"] is True
_check_first_superboss_sigil(p)  # second call must not re-grant
assert p["awakening_sigils"] == 1
_grant_awakening_shard(p, "wl:10")
_grant_awakening_shard(p, "wl:10")
assert p["awakening_shards"] == 1 and p["awakening_shard_sources"] == ["wl:10"]
_grant_awakening_sigil(p, "wl:50")
_grant_awakening_sigil(p, "wl:50")
assert p["awakening_sigils"] == 2 and p["awakening_shard_sources"] == ["wl:10", "wl:50"]
print("7. first-superboss / shard / sigil grants are idempotent  [ok]")

# ── 8. Migration for pre-patch superboss clears ───────────────────────────
old_save = {
    "defeated_superbosses": ["broodmother_vileheart", "queen_of_mirrors_sylvana", "wl_mary_sue", "entangled_chrysalis"],
    "wl_boss_defeated_queen_of_hearts": True,
    "wl_boss_defeated_big_bad_wolf": True,
    "wl_boss_defeated_mary_sue": True,
}
_migrate_awakening_rewards(old_save)
# 2 pool shards + 2 wonderland shards = 4 shards; intro sigil + mary sue = 2 sigils
assert old_save["awakening_shards"] == 4, old_save["awakening_shards"]
assert old_save["awakening_sigils"] == 2, old_save["awakening_sigils"]
assert old_save["awakening_intro_granted"] is True
# Second migration pass must change nothing
_migrate_awakening_rewards(old_save)
assert old_save["awakening_shards"] == 4 and old_save["awakening_sigils"] == 2
# New save with no kills: nothing granted
empty = {}
_migrate_awakening_rewards(empty)
assert empty.get("awakening_sigils", 0) == 0
print("8. retro-grant migration (idempotent, no-kill saves untouched)  [ok]")

# ── 9. Ally + house round-trip carries awakened fields ────────────────────
girl = {
    "key": "goblin_girl", "name": "Goblin Girl", "level": 40, "level_cap": 40,
    "affection": 150, "awakened": True, "awakened_name": "Goblin Deadeye",
    "awakened_skills": ["lucky_volley", "fortunes_veil"],
}
ally = create_ally_from_girl(girl)
assert ally["awakened"] is True
assert ally["awakened_name"] == "Goblin Deadeye"
assert ally["innate_skills"] == ["lucky_volley", "fortunes_veil"], ally["innate_skills"]
record = _ally_to_house_record(ally, {})
assert record["awakened"] is True
assert record["awakened_name"] == "Goblin Deadeye"
assert record["awakened_skills"] == ["lucky_volley", "fortunes_veil"]
print("9. create_ally_from_girl + _ally_to_house_record persist awakening  [ok]")

# ── 10. Awakened skill execution smoke ────────────────────────────────────
def make_ally(key, race):
    return {
        "name": "Tester", "key": key, "race": race, "is_ally": True, "level": 40,
        "attributes": {a: 12 for a in ATTRS},
        "equipped": {"weapon": None, "armor": None, "accessory1": None, "accessory2": None},
        "active_buffs": [], "active_debuffs": [],
        "current_hp": 100, "max_hp": 100,
        "skill_cooldowns": {}, "skill_mastery": {},
    }

def make_enemy(name="Dummy"):
    return {"name": name, "hp": 100, "max_hp": 100, "con_mod": 0,
            "active_debuffs": [], "race": "Human"}

hero = {"name": "Hero", "current_hp": 100, "attributes": {a: 10 for a in ATTRS},
        "active_buffs": [], "active_debuffs": [], "skill_cooldowns": {"heroic_slash": 2}}

# Moonveil Dust: AoE blind + marked
caster = make_ally("moth_girl_flutterer", "Fey")
foes = [make_enemy("A"), make_enemy("B")]
msg, _ = execute_ally_skill(caster, hero, "moonveil_dust", get_innate_skill_def("moonveil_dust"), foes, [])
assert all(e.get("blinded") for e in foes), msg
assert all(e.get("hunters_mark_bonus") == 0.1 for e in foes), msg

# Absolute Dominion: AoE STR curse + fear
caster = make_ally("demon_whip_master", "Demon")
foes = [make_enemy("A")]
msg, _ = execute_ally_skill(caster, hero, "absolute_dominion", get_innate_skill_def("absolute_dominion"), foes, [])
assert any(d.get("type") == "curse" and "Strength" in d.get("stats", []) for d in foes[0]["active_debuffs"]), msg
assert any(d.get("type") == "fear" and d.get("value") == 0.3 for d in foes[0]["active_debuffs"]), msg

# Adaptive Membrane: absorb + reflect on self
caster = make_ally("slime_girl", "Elemental")
msg, _ = execute_ally_skill(caster, hero, "adaptive_membrane", get_innate_skill_def("adaptive_membrane"), [make_enemy()], [])
assert any(b.get("type") == "damage_absorption" and b.get("value") == 0.4 for b in caster["active_buffs"]), msg
assert any(b.get("type") == "reflection" and b.get("value") == 0.3 for b in caster["active_buffs"]), msg

# Reboot Protocol: death ward with 30% restore
caster = make_ally("clockwork_automata_doll", "Clockwork")
msg, _ = execute_ally_skill(caster, hero, "reboot_protocol", get_innate_skill_def("reboot_protocol"), [make_enemy()], [])
ward = next(b for b in caster["active_buffs"] if b["type"] == "death_ward")
assert ward.get("hp_pct") == 0.3 and ward.get("remaining") == 3, msg

# System Overdrive: power buff + cooldown refund on the sole party member
caster = make_ally("gnome_gear_maiden", "Gnome")
msg, _ = execute_ally_skill(caster, hero, "system_overdrive", get_innate_skill_def("system_overdrive"), [make_enemy()], [])
assert any(b.get("type") == "power_buff" for b in hero["active_buffs"]), msg
assert hero["skill_cooldowns"]["heroic_slash"] == 1, hero["skill_cooldowns"]

# Death's Vigil: DR + death ward on the sole party member
caster = make_ally("dullahan_knight", "Undead")
msg, _ = execute_ally_skill(caster, hero, "deaths_vigil", get_innate_skill_def("deaths_vigil"), [make_enemy()], [])
assert any(b.get("type") == "defense_pct" and b.get("value") == 0.35 for b in hero["active_buffs"]), msg
assert any(b.get("type") == "death_ward" for b in hero["active_buffs"]), msg
print("10. awakened skill execution (dust/dominion/membrane/reboot/overdrive/vigil)  [ok]")

# ── 11. Ceremony dialogue formatter ───────────────────────────────────────
assert _fmt_dialogue("Hello {name}, welcome {new_name}!", name="A", new_name="B") == "Hello A, welcome B!"
assert _fmt_dialogue("No tokens here.") == "No tokens here."
print("11. _fmt_dialogue token replacement  [ok]")

# ── 12. Perfect Mimicry elemental adaptation feeds the damage calc ────────
from combat.elemental import calculate_elemental_damage

atk = {
    "active_buffs": [{"type": "elemental_adapt_dmg", "element": "fire", "value": 0.25, "remaining": 3}],
    "elemental_dmg": {"fire": 1.5},
}
tgt = {
    "active_buffs": [{"type": "elemental_adapt_res", "element": "fire", "value": 0.5, "remaining": 3}],
    "elemental_res": {"fire": 1.0},
    "active_debuffs": [],
}
# 100 × (1.5 + 0.25) × (1.0 + 0.5) = 262.5 → 262
assert calculate_elemental_damage(100, atk, tgt, "fire") == 262
# Wrong element: adapt buffs do not apply → 100 × 1.0 × 1.0 = 100
assert calculate_elemental_damage(100, atk, tgt, "water") == 100
# Expired buffs are ignored
for b in atk["active_buffs"] + tgt["active_buffs"]:
    b["remaining"] = 0
assert calculate_elemental_damage(100, atk, tgt, "fire") == 150
print("12. elemental_adapt dmg/res buffs apply to the right element only  [ok]")

print("")
print("All awakening checks passed.")
