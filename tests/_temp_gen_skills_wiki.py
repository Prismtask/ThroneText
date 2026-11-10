# -*- coding: utf-8 -*-
"""One-off generator: builds docs/monster_girls_skills_wiki.md from game data.

Also refreshes the standalone web wiki (wiki/index.html — player guide +
skills + enemy database) via tests/gen_wiki_html.py — no extra command needed.

Sources:
  - resources/skill_book/innate_skills.yaml  (innate skill map + definitions)
  - resources/enemies/enemies_data/monster_girls.yaml (names, races, levels)
Run:  .venv python tests/_temp_gen_skills_wiki.py
"""
import os
import sys
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from combat.ally import get_growth_label  # noqa: E402  (single source of truth)


def load(rel_path):
    with open(os.path.join(ROOT, rel_path), encoding="utf-8") as f:
        return yaml.safe_load(f)


innate = load(os.path.join("resources", "skill_book", "innate_skills.yaml"))
mg_data = load(os.path.join("resources", "enemies", "enemies_data", "monster_girls.yaml"))
learnable_data = load(os.path.join("resources", "skill_book", "skill_list.yaml"))

SKILL_MAP = innate["innate_skills"]
DEFS = innate["innate_skill_defs"]
AWAKENINGS = innate.get("awakenings", {})
LEARNABLE = learnable_data.get("learnable_skills", {})
PASSIVES = learnable_data.get("passive_skills", {})
CLASS_SKILLS = learnable_data.get("class_skills", {})
PROFESSIONS = learnable_data.get("professions", {})

HEROINE_KEYS = {
    "wonderland_alice", "wonderland_alice_vorpal",
    "wonderland_red_hood", "wonderland_red_hood_vorpal",
    "wonderland_dorothy", "wonderland_dorothy_vorpal",
    "wonderland_palette",
}

TARGET_LABELS = {
    "enemy": "single enemy",
    "enemies": "all enemies",
    "self": "self",
    "ally_or_self": "self or ally",
    "all_allies": "whole party",
    "dead_ally": "fallen ally",
}

# Tier metadata — keep in sync with facilities/barracks.py
TIER_LABELS = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI"}
TIER_NAMES = {1: "Novice", 2: "Adept", 3: "Veteran", 4: "Master", 5: "Elite", 6: "Legend"}

# Mastery thresholds — keep in sync with combat/skills.py MASTERY_THRESHOLDS
MASTERY_THRESHOLDS = [10, 25, 50, 90, 150]

# Burn tiers — keep in sync with combat/status_effects.py BURN_TIERS
# (legacy flat "burn N dmg" values map up to the nearest tier)
BURN_TIERS = {
    1: ("Singe", 3),
    2: ("Burn", 6),
    3: ("Blaze", 10),
    4: ("Inferno", 18),
    5: ("Conflagration", 30),
}


def _burn_tier(damage):
    """Map a legacy burn_damage value to its tier (mirrors damage_to_burn_tier)."""
    dmg = float(damage)
    if dmg <= 3:
        return 1
    if dmg <= 6:
        return 2
    if dmg <= 10:
        return 3
    if dmg <= 18:
        return 4
    return 5


# ---------------------------------------------------------------------------
# Effect / extra formatting
# ---------------------------------------------------------------------------

def _pct(value):
    try:
        return f"{round(float(value) * 100)}%"
    except (TypeError, ValueError):
        return str(value)


def _turns(dur):
    try:
        return f"for {dur} turn" if int(dur) == 1 else f"for {dur} turns"
    except (TypeError, ValueError):
        return str(dur)


def fmt_effect(eff):
    """Render one effect dict into a short parenthetical phrase."""
    if not isinstance(eff, dict):
        return str(eff)
    t = eff.get("type", "")
    v = eff.get("value")
    dur = eff.get("duration")

    if t == "damage_reduction":
        return f"damage taken -{_pct(v)} {_turns(dur)}"
    if t == "evasion":
        dex = eff.get("dex_bonus", 0)
        extra = f", +{dex} DEX" if dex else ""
        return f"+{_pct(v)} dodge{extra} {_turns(dur)}"
    if t == "damage_absorption":
        return f"absorbs {_pct(v)} of damage {_turns(dur)}"
    if t == "barrier":
        pct = eff.get("value_from_caster_hp")
        if pct:
            return f"absorbs {_pct(pct)} of caster's max HP {_turns(dur)}"
        return f"absorbs {v} damage {_turns(dur)}"
    if t == "death_ward":
        return f"survive lethal at 1 HP, once {_turns(dur)}"
    if t == "haste":
        return f"haste (+{eff.get('init_bonus', 3)} init, -{eff.get('cd_reduction', 1)} CD) {_turns(dur)}"
    if t == "regen":
        return f"regenerate {_pct(v)} max HP {_turns(dur)}"
    if t == "slow":
        return f"Slow {_turns(dur)}"
    if t == "blind":
        return f"Blind ({_pct(v)} miss) {_turns(dur)}"
    if t == "stun":
        return f"Stun {_turns(dur)}"
    if t == "confusion":
        return f"Confusion ({_pct(v)}) {_turns(dur)}"
    if t == "stat_debuff":
        scale = " (scales)" if eff.get("scale_per_level") else ""
        return f"{eff.get('stat', 'stat')} -{v}{scale} {_turns(dur)}"
    if t == "stat_buff":
        scale = " (scales)" if eff.get("scale_per_level") else ""
        return f"{eff.get('stat', 'stat')} +{v}{scale} {_turns(dur)}"
    if t == "power_buff":
        return f"next action +{_pct(v)} power"
    if t == "damage_boost":
        return f"+{_pct(v)} damage {_turns(dur)}"
    if t == "crit_boost":
        return f"+{_pct(v)} crit chance {_turns(dur)}"
    if t == "fear_immunity":
        return f"Fear immunity {_turns(dur)}"
    if t == "marked":
        return f"target takes +{_pct(v)} damage {_turns(dur)}"
    if t == "damage_taken_up":
        return f"target takes +{_pct(v)} damage {_turns(dur)}"
    if t == "elemental_weakness":
        extra = ""
        if eff.get("stat_debuff"):
            extra = f", {eff['stat_debuff']} {eff.get('stat_value', 0)}"
        return f"elemental weakness +{v}{extra} {_turns(dur)}"
    if t == "life_steal":
        return f"heal {_pct(v)} of damage dealt"
    if t == "reflection":
        return f"reflect {_pct(v)} of damage back {_turns(dur)}"
    if t == "perfect_guard":
        return f"damage taken -{_pct(v)}, reflect {_pct(eff.get('reflect_value', 0))} {_turns(dur)}"
    if t == "phantom_dodge":
        return f"evade {_pct(v)} of attacks, +{eff.get('dex_bonus', 0)} DEX {_turns(dur)}"
    if t == "cooldown_reduction":
        return f"next skill cooldown -{v} {_turns(dur)}"
    if t == "random_buff":
        labels = [o.get("label", o.get("type", "?")) for o in eff.get("options", [])]
        return " / ".join(labels)
    if t == "entomb":
        return f"Entomb {_turns(dur)}"
    if t == "fear":
        return f"Fear (deals -{_pct(v)} damage) {_turns(dur)}"
    if t == "dodge_counter":
        return f"counter-attacks after dodging ({_pct(v)}) {_turns(dur)}"
    if t == "cd_refund":
        return f"all active cooldowns -{v}"
    if t == "elemental_adapt":
        return "adapts to the last element that struck her (+dmg/+res)"
    if t == "multi":
        return " · ".join(fmt_effect(e) for e in eff.get("effects", []))
    return t


def skill_extras(d):
    """Collect extra mechanics tags for a skill def."""
    tags = []
    if d.get("guaranteed_crit"):
        tags.append("guaranteed crit")
    if d.get("crit_bonus"):
        tag = f"+{_pct(d['crit_bonus'])} crit chance"
        if d.get("crit_mult"):
            tag += f" ({d['crit_mult']}x damage)"
        tags.append(tag)
    if d.get("ignore_armor"):
        tags.append("ignores armor")
    if d.get("ignore_armor_pct"):
        tags.append(f"ignores {_pct(d['ignore_armor_pct'])} armor")
    if d.get("poison_damage") is not None:
        tags.append(f"Poison {d['poison_damage']} dmg x {d.get('poison_duration', '?')} turns")
    if d.get("burn_damage") is not None:
        name, tdmg = BURN_TIERS[_burn_tier(d["burn_damage"])]
        tags.append(f"{name} ({tdmg}/turn) x {d.get('burn_duration', '?')} turns")
    if d.get("bleed_damage") is not None:
        tags.append(f"Bleed {d['bleed_damage']} dmg x {d.get('bleed_duration', '?')} turns")
    if d.get("shock_damage") is not None:
        tags.append(f"Shock {d['shock_damage']} dmg x {d.get('shock_duration', '?')} turns")
    if d.get("bonus_vs_races"):
        races = ", ".join(d["bonus_vs_races"])
        tags.append(f"+{_pct(d.get('bonus_value', 0))} dmg vs {races}")
    if d.get("stun_chance"):
        tags.append(f"{_pct(d['stun_chance'])} stun chance")
    if d.get("apply_weaken"):
        tags.append("applies Weaken")
    if d.get("apply_slow"):
        tags.append("applies Slow")
    if d.get("heal_percent"):
        tags.append(f"heal {_pct(d['heal_percent'])} max HP")
    if d.get("revive_percent"):
        tags.append(f"revive at {_pct(d['revive_percent'])} HP")
    if d.get("revive_barrier_pct"):
        tags.append(f"revives with a {_pct(d['revive_barrier_pct'])} caster-HP barrier")
    if d.get("hits"):
        tags.append(f"{d['hits']} hits")
    if d.get("cleanse_one_debuff"):
        tags.append("cleanse 1 debuff")
    if d.get("cleanse_all_debuffs"):
        tags.append("cleanse all debuffs")
    if d.get("push_initiative"):
        tags.append("enemies drop to initiative bottom")
    if d.get("palette_dynamic_element"):
        tags.append("element matches Palette's current color")
    if d.get("palette_spectrum"):
        tags.append("3 hits, each a random element")
    if d.get("palette_signature"):
        tags.append("strikes next turn for 2.5x, ignores defense")
    if d.get("blind_value") is not None:
        tags.append(f"Blind ({_pct(d['blind_value'])} miss) x {d.get('blind_duration', '?')} turns")
    if d.get("apply_blind"):
        tags.append(f"Blind (40% miss) x {d.get('blind_duration', '?')} turns")
    if d.get("self_vulnerable"):
        tags.append(f"you take +{_pct(d['self_vulnerable'])} damage for {d.get('self_vulnerable_duration', '?')} turns")
    if d.get("hp_cost_percent"):
        tags.append(f"costs {_pct(d['hp_cost_percent'])} max HP")
    if d.get("apply_fear"):
        tags.append(f"Fear (-{_pct(d.get('fear_value', 0))} damage) x {d.get('fear_duration', '?')} turns")
    if d.get("expose_armor"):
        tags.append(f"Expose -{d['expose_armor']} armor")
    if d.get("bonus_vs_high_hp"):
        tags.append(f"+{_pct(d['bonus_vs_high_hp'])} dmg vs foes above 80% HP")
    if d.get("bonus_vs_bleeding"):
        tags.append(f"+{_pct(d['bonus_vs_bleeding'])} dmg vs bleeding foes")
    if d.get("effect"):
        tags.append(fmt_effect(d["effect"]))
    return tags


def skill_bullet(sid):
    """One-line wiki bullet for a skill."""
    d = DEFS.get(sid)
    if d is None:
        return f"- **{sid}** — *(definition missing)*"
    parts = [str(d.get("category", "?")).capitalize()]
    if d.get("cooldown") is not None:
        parts.append(f"CD {d['cooldown']}")
    parts.append(TARGET_LABELS.get(d.get("target"), str(d.get("target", "?"))))
    if d.get("power_type") and d.get("base_power") is not None:
        parts.append(f"power {d['base_power']} ({d['power_type'].upper()})")
    if d.get("elemental"):
        parts.append(d["elemental"].capitalize())
    line = f"- **{d.get('name', sid)}** — *{' · '.join(parts)}* — {d.get('description', '')}"
    tags = skill_extras(d)
    if tags:
        line += " — *" + " · ".join(tags) + "*"
    return line


def learnable_bullet(sid, d):
    """One-line wiki bullet for a Barracks learnable skill."""
    tier = d.get("tier", 1)
    parts = [f"Tier {TIER_LABELS.get(tier, '?')} {TIER_NAMES.get(tier, '?')}"]
    parts.append(str(d.get("category", "?")).capitalize())
    if d.get("cooldown") is not None:
        parts.append(f"CD {d['cooldown']}")
    parts.append(TARGET_LABELS.get(d.get("target"), str(d.get("target", "?"))))
    if d.get("power_type") and d.get("base_power") is not None:
        parts.append(f"power {d['base_power']} ({d['power_type'].upper()})")
    if d.get("elemental"):
        parts.append(d["elemental"].capitalize())
    line = f"- **{d.get('name', sid)}** — *{' · '.join(parts)}* — {d.get('description', '')}"
    tags = skill_extras(d)
    # Thresholds are global (combat/skills.py) — the per-skill YAML lists are
    # legacy documentation and no longer drive the game.
    tags.append("mastery at " + "/".join(str(t) for t in MASTERY_THRESHOLDS) + " uses")
    if tags:
        line += " — *" + " · ".join(tags) + "*"
    return line


def class_extras(d):
    """Extra mechanic tags for player class skills."""
    tags = []
    if d.get("capstone"):
        tags.append("class capstone")
    if d.get("free_action"):
        tags.append("free action")
    if d.get("elements"):
        tags.append(f"{len(d['elements'])} hits (one per element)")
    if d.get("cooldown_reduction"):
        tags.append(f"all active cooldowns -{d['cooldown_reduction']}")
    if d.get("recoil_percent"):
        tags.append(f"recoil {_pct(d['recoil_percent'])} max HP")
    if d.get("party_heal"):
        tags.append("heals the party for damage dealt")
    if d.get("self_heal_damage"):
        tags.append("heals you for damage dealt")
    if d.get("defense_buff"):
        tags.append(f"party damage reduction +{d['defense_buff']} (flat) for {d.get('buff_duration', '?')} turns")
    if d.get("apply_sunder"):
        tags.append(f"Sunder -{d.get('sunder_value', '?')} armor for {d.get('sunder_duration', '?')} turns")
    if d.get("bloodlust_duration"):
        tags.append(f"heal 50% of damage dealt for {d['bloodlust_duration']} turns")
    return tags


def class_skill_bullet(sid, d):
    """One-line wiki bullet for a player class skill."""
    parts = [f"Level {d.get('unlock_level', '?')}"]
    if d.get("cooldown") is not None:
        parts.append(f"CD {d['cooldown']}")
    parts.append(TARGET_LABELS.get(d.get("target"), str(d.get("target", "?"))))
    if d.get("power_type") and d.get("base_power") is not None:
        parts.append(f"power {d['base_power']} ({d['power_type'].upper()})")
    if d.get("elements"):
        parts.append("Multi-element")
    elif d.get("elemental"):
        parts.append(d["elemental"].capitalize())
    line = f"- **{d.get('name', sid)}** — *{' · '.join(parts)}* — {d.get('description', '')}"
    tags = skill_extras(d) + class_extras(d)
    if tags:
        line += " — *" + " · ".join(tags) + "*"
    return line


# ---------------------------------------------------------------------------
# Heroine definitions
# ---------------------------------------------------------------------------

HEROINES = [
    {
        "name": "Alice",
        "role": "Wonderland Heroine",
        "normal": ["curious_inquiry", "try_me"],
        "vorpal_weapon": "Vorpal Blade (Rusted → Restored)",
        "vorpal": ["vorpal_edge", "snicker_snack"],
        "upgrade": "frabjous_day",
        "upgrade_note": "granted by the Godmother's Blade facility upgrade",
        "note": None,
    },
    {
        "name": "Red Hood",
        "role": "Wonderland Heroine",
        "normal": ["hunters_mark", "whats_in_the_basket"],
        "vorpal_weapon": "Grandmother's Axe (Woodcutter's Broken Axe → Restored)",
        "vorpal": ["what_big_teeth", "fell_the_wolf"],
        "upgrade": "through_the_forest",
        "upgrade_note": "granted by the Woodcutter's Axe facility upgrade",
        "note": None,
    },
    {
        "name": "Dorothy",
        "role": "Wonderland Heroine",
        "normal": ["no_place_like_home", "ruby_blink"],
        "vorpal_weapon": "Silver Slippers → Ruby Slippers",
        "vorpal": ["cyclones_call", "heart_of_tin"],
        "upgrade": "emerald_citys_light",
        "upgrade_note": "granted by the Wizard's Slippers facility upgrade",
        "note": None,
    },
    {
        "name": "Palette",
        "role": "Chromatic Artisan",
        "normal": ["palette_brushstroke", "palette_spectrum", "palette_signature"],
        "vorpal_weapon": None,
        "vorpal": [],
        "upgrade": None,
        "upgrade_note": None,
        "note": "No skill swap — instead her Palette Brush grants elemental color stances.",
    },
]

# ---------------------------------------------------------------------------
# Monster girl roster
# ---------------------------------------------------------------------------

girls = []
for key, entry in mg_data.items():
    if not isinstance(entry, dict) or not entry.get("name"):
        continue
    if key == "affection_gifts":
        continue
    girls.append((key, entry))

with_skills = [(k, e) for k, e in girls if k in SKILL_MAP]
without_skills = [(k, e) for k, e in girls if k not in SKILL_MAP]
with_skills.sort(key=lambda t: t[1]["name"].lower())
without_skills.sort(key=lambda t: t[1]["name"].lower())

# All skill ids used by monster girls, for the details dictionary.
all_mg_skill_ids = sorted(
    {sid for k, _e in with_skills for sid in SKILL_MAP[k]},
    key=lambda sid: DEFS.get(sid, {}).get("name", sid).lower(),
)

# ---------------------------------------------------------------------------
# Wiki output
# ---------------------------------------------------------------------------

out = []
w = out.append

w("# Pandemonium — Skills Wiki")
w("")
w("> Generated from `resources/skill_book/innate_skills.yaml`, "
  "`resources/skill_book/skill_list.yaml` and "
  "`resources/enemies/enemies_data/monster_girls.yaml`. Regenerate with "
  "`tests/_temp_gen_skills_wiki.py` — the same command refreshes the web wiki "
  "(`wiki/index.html`).")
w("")
w("Covers player class skills, heroine skills, monster-girl innate & awakened skills, "
  "and ally learnable skills.")
w("")
w("## Contents")
w("")
w("1. [How Skills Work](#how-skills-work)")
w("2. [Player Class Skills](#player-class-skills)")
w("3. [Heroines — Innate & Enhanced Skills](#heroines--innate--enhanced-skills)")
w("4. [Monster Girls — Innate Skill Roster](#monster-girls--innate-skill-roster)")
w("5. [Awakened Skills (wave 1)](#awakened-skills-wave-1)")
w("6. [Innate Skill Details (Dictionary)](#innate-skill-details-dictionary)")
w("7. [Learnable Skills (Barracks)](#learnable-skills-barracks)")
w("")
w("---")
w("")
w("## How Skills Work")
w("")
w("- Every **class** has **1 passive skill** (always active) and **10 active skills** "
  "unlocked at levels 3, 5, 8, 10, 12, 15, 20, 26, 32 and 40 — see [Player Class Skills](#player-class-skills).")
w("- Every **monster girl** has **2 innate skills** unique to her. "
  "Capture her with a net (♀ icon) and she joins your party with both skills unlocked.")
w("- Every **heroine** has 2 innate skills. Equipping her signature weapon "
  "**swaps them for 2 enhanced (vorpal) skills**; restoring/upgrading the weapon at "
  "the Arcane Tower grants a **third skill**.")
w("- Skills scale with a primary attribute (`STR`, `DEX`, `WIS`, `LER`, `CHA`, `CON`) "
  "and have per-skill cooldowns tracked in `skill_cooldowns`.")
w("- Elements: Fire, Water, Thunder, Wind, Earth, Light, Dark, Magical, Physical.")
w("- Fire skills apply the **burn tier** system — **Singe** (3/turn) → **Burn** (6/turn) → "
  "**Blaze** (10/turn) → **Inferno** (18/turn) → **Conflagration** (30/turn). Tags name the "
  "tier each skill applies; higher tiers overwrite lower ones.")
w("- Every monster girl and heroine also has a **race passive** (separate from innate skills).")
w("- Some girls are **late bloomers** — low-base girls (Goblin Girl, Harpy Scout, …) "
  "gain bonus attribute points while leveling in your party (see the Growth column below).")
w("- **Awakening** — twelve girls can be Awakened at the House Lounge "
  "(Lv 40 + level cap 40 + affection 150 + 1 Awakening Sigil). An awakening replaces both "
  "innate skills with upgraded versions, carries over mastery, and changes her displayed "
  "name — see [Awakened Skills (wave 1)](#awakened-skills-wave-1).")
w("- **Learnable skills** are taught at the **Barracks** ('Teach Ally Skill'). Each ally can "
  "hold up to **3 learned skills** and learn **1 skill at a time** (earn EXP in combat to finish learning). "
  "They come in 4 tiers with level requirements and EXP costs — see [Learnable Skills (Barracks)](#learnable-skills-barracks).")
w("")
w("---")
w("")

# ── Player class skills ─────────────────────────────────────────────────────
w("## Player Class Skills")
w("")
w("Every class has **1 passive skill** and **10 active skills**: the launch six unlock at "
  "levels 3, 5, 8, 10, 12 and 15, the **wave-2 skills** at 20, 26 and 32, and the class "
  "**capstone** at 40 — after which you choose a **profession** (see below). In combat your "
  "skills appear as numbered options (`1`–`9`) and you bring a **Battle Loadout** of up to 9 — "
  "the **Skill Book** in any city menu lists them with cooldowns and mastery.")
w("")
for class_name, class_skills in CLASS_SKILLS.items():
    w(f"### {class_name}")
    w("")
    passive = PASSIVES.get(class_name)
    if passive:
        w(f"- **Passive — {passive.get('name', '?')}:** {passive.get('description', '')}")
        w("")
    for sid, d in sorted(class_skills.items(), key=lambda kv: kv[1].get("unlock_level", 0)):
        w(class_skill_bullet(sid, d))
    w("")
w("---")
w("")

# ── Player professions (Phase 3) ──────────────────────────────────────────
if PROFESSIONS:
    w("## Player Professions")
    w("")
    w("After learning your class **capstone** (Level 40), choose **one of two professions** at "
      "any Guild — the choice is **permanent**. Your class passive is **upgraded**, your "
      "**signature skill** is granted immediately, and two more skills unlock at levels 50 and "
      "60. The other branch is locked out for that save.")
    w("")
    for class_name, branches in PROFESSIONS.items():
        w(f"### {class_name}")
        w("")
        for pid, pdata in branches.items():
            w(f"#### {pdata.get('name', pid)} — *{pdata.get('tagline', '')}*")
            w("")
            passive = pdata.get("passive")
            if passive:
                w(f"- **Upgraded passive — {passive.get('name', '?')}:** {passive.get('description', '')}")
                w("")
            for sid, d in sorted(pdata.get("skills", {}).items(), key=lambda kv: kv[1].get("unlock_level", 0)):
                w(class_skill_bullet(sid, d))
            w("")
    w("---")
    w("")

# ── Heroines ──────────────────────────────────────────────────────────────
w("## Heroines — Innate & Enhanced Skills")
w("")

for h in HEROINES:
    w(f"### {h['name']} ({h['role']})")
    w("")
    w("**Innate skills:**")
    for sid in h["normal"]:
        w(skill_bullet(sid))
    w("")
    if h["vorpal"]:
        w(f"**Enhanced skills** — unlocked by equipping the *{h['vorpal_weapon']}* "
          "(replaces the innate skills while equipped):")
        for sid in h["vorpal"]:
            w(skill_bullet(sid))
        w("")
        if h["upgrade"]:
            w(f"**Upgrade skill** — {h['upgrade_note']}:")
            w(skill_bullet(h["upgrade"]))
            w("")
    if h["note"]:
        w(f"> {h['note']}")
        w("")
    w("---")
    w("")

# ── Monster girl roster ───────────────────────────────────────────────────
w("## Monster Girls — Innate Skill Roster")
w("")
w("| # | Monster Girl | Race | Level | Growth | Innate Skill 1 | Innate Skill 2 |")
w("|---|--------------|------|-------|--------|----------------|----------------|")
for idx, (key, entry) in enumerate(with_skills, 1):
    name = entry["name"]
    race = entry.get("race", "?")
    level = entry.get("level", "?")
    growth = get_growth_label({"key": key})
    s1, s2 = SKILL_MAP[key][0], SKILL_MAP[key][1]
    n1 = DEFS.get(s1, {}).get("name", s1)
    n2 = DEFS.get(s2, {}).get("name", s2)
    w(f"| {idx} | {name} ♀ | {race} | {level} | {growth} | {n1} | {n2} |")
w("")

if without_skills:
    w("### No Innate Skills Yet")
    w("")
    w("These monster girls are capturable but have not been assigned innate skills:")
    w("")
    for idx, (key, entry) in enumerate(without_skills, 1):
        w(f"{idx}. **{entry['name']}** ♀ — {entry.get('race', '?')}, level {entry.get('level', '?')}")
    w("")
w("---")
w("")

# ── Awakened skills (wave 1) ──────────────────────────────────────────────
w("## Awakened Skills (wave 1)")
w("")
w("Twelve girls can be **Awakened** at the House Lounge — **Lv 40**, **level cap 40**, "
  "**affection 150**, plus **1 Awakening Sigil** (max 5 Sigils per save). An awakening "
  "replaces both innate skills, carries over mastery/cooldown progress, and changes her "
  "displayed name (a chosen nickname still wins).")
w("")
w("| Monster Girl | Awakened Name | Base kit → Awakened kit |")
w("|---|---|---|")
for key, mapping in AWAKENINGS.items():
    entry = mg_data.get(key, {})
    girl_name = entry.get("name", key)
    awakened_name = entry.get("awakened_name", "?")
    pairs = []
    for base_id, upgraded_id in mapping.items():
        bn = DEFS.get(base_id, {}).get("name", base_id)
        un = DEFS.get(upgraded_id, {}).get("name", upgraded_id)
        pairs.append(f"{bn} → **{un}**")
    w(f"| {girl_name} ♀ | {awakened_name} | {' · '.join(pairs)} |")
w("")
w("**Awakened skill details:**")
w("")
for key, mapping in AWAKENINGS.items():
    for upgraded_id in mapping.values():
        w(skill_bullet(upgraded_id))
w("")
w("---")
w("")

# ── Skill dictionary ──────────────────────────────────────────────────────
w("## Innate Skill Details (Dictionary)")
w("")
w("Alphabetical reference for every monster-girl innate skill in the roster above. "
  "Heroine skills are detailed in their own sections.")
w("")
for sid in all_mg_skill_ids:
    w(skill_bullet(sid))
w("")

# ── Learnable skills (Barracks) ────────────────────────────────────────────
w("---")
w("")
w("## Learnable Skills (Barracks)")
w("")
w("Taught at the **Barracks** → \"Teach Ally Skill\". Pick an ally and a category "
  "(Offensive / Defensive / Support), then choose a skill to start learning. "
  "The ally gains learning EXP in combat; when the EXP bar fills, the skill is learned. "
  "Allies can hold **3 learned skills** at once (replacing a learned skill to start a new one) "
  "and learn only **1 skill at a time**.")
w("")
w("**Tier ladder:**")
w("")
w("| Tier | Name | EXP to Learn | Required Ally Level | Required Level Cap |")
w("|------|------|--------------|---------------------|--------------------|")
tier_rows = {}
for _cat, skills in LEARNABLE.items():
    for _sid, d in skills.items():
        t = d.get("tier", 1)
        row = tier_rows.setdefault(t, {"exp": set(), "lvl": set(), "cap": set()})
        row["exp"].add(d.get("exp_cost", 300))
        row["lvl"].add(d.get("required_level", 1))
        row["cap"].add(d.get("required_cap", 0))
for t in sorted(tier_rows):
    exp = "/".join(str(x) for x in sorted(tier_rows[t]["exp"]))
    lvl = "/".join(str(x) for x in sorted(tier_rows[t]["lvl"]))
    cap = "/".join(str(x) if x else "—" for x in sorted(tier_rows[t]["cap"]))
    w(f"| {TIER_LABELS.get(t, '?')} | {TIER_NAMES.get(t, '?')} | {exp} | {lvl} | {cap} |")
w("")
w("**Mastery:** each time a skill is used, its mastery grows — shown as "
  "★ / ★★ / ★★★ / ✦ / ✦✦. Thresholds are 10/25/50/90/150 uses. ★★★ unlocks "
  "bonus effects, ✦ (mastery 4) adds +1 turn to effect durations, and ✦✦ "
  "(mastery 5) raises power, status potency, and total cooldown reduction to −2. "
  "Burn skills upgrade their burn tier instead: +1 tier at ★★★, +2 tiers at ✦✦ "
  "(capped at Conflagration).")
w("")
for category in ["offensive", "defensive", "support"]:
    skills = LEARNABLE.get(category, {})
    if not skills:
        continue
    w(f"### {category.capitalize()} Skills ({len(skills)})")
    w("")
    ordered = sorted(skills.items(), key=lambda kv: (kv[1].get("tier", 9), kv[1].get("name", "")))
    for _sid, d in ordered:
        w(learnable_bullet(_sid, d))
    w("")

out_path = os.path.join(ROOT, "docs", "monster_girls_skills_wiki.md")
os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, "w", encoding="utf-8") as f:
    f.write("\n".join(out) + "\n")

print(f"Wrote {out_path}")

# Refresh the standalone web wiki (wiki/index.html) in the same run.
try:
    from gen_wiki_html import build_site  # lives in this folder — no install needed

    build_site(
        footer_note="Regenerate: <code>python tests/_temp_gen_skills_wiki.py</code>",
    )
except Exception as exc:  # never let the optional web build invalidate the markdown
    print(f"Web wiki build skipped: {exc}")
print(f"  monster girls with skills: {len(with_skills)}")
print(f"  monster girls without:     {len(without_skills)}")
print(f"  skill definitions listed:  {len(all_mg_skill_ids)}")
print(f"  awakenings:                {len(AWAKENINGS)}")
print(f"  learnable skills:          {sum(len(v) for v in LEARNABLE.values())}")
