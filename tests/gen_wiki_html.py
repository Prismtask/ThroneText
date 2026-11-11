# -*- coding: utf-8 -*-
"""Build the standalone Pandemonium web wiki (wiki/index.html).

One self-contained HTML file, no external dependencies (works offline, opens
from disk, can be dropped on any static host). It combines three sources:

  * README.md                              -> the Player Guide page
  * docs/dreams_wiki.md                    -> the Dreams page
  * docs/monster_girls_skills_wiki.md      -> the Skills Wiki page
  * resources/enemies/enemies_data/*.yaml  -> the interactive Enemy Database
    (+ resource race/biome profiles from resources/enemies/enemy_races.py
       and biome_races.py, skill names from resources/skill_book/)

Enemy Database features:
  * filter by category / race / level range, sort by name/level/HP/race
  * click an enemy -> detail view with clickable tags (race, level, category,
    boss flags, element profile, skills, awakening kit)
  * clicking a tag returns to the list with that filter applied

Usage:
    .venv\\Scripts\\python.exe tests/gen_wiki_html.py [--out wiki/index.html]

``tests/_temp_gen_skills_wiki.py`` calls :func:`build_site` so one command
regenerates the markdown wiki and the website together.
"""
import argparse
import html
import importlib.util
import json
import os
import re
import string
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)  # allow `combat.ally` imports when run as a script

README_MD = os.path.join(ROOT, "README.md")
DREAMS_MD = os.path.join(ROOT, "docs", "dreams_wiki.md")
SKILLS_MD = os.path.join(ROOT, "docs", "monster_girls_skills_wiki.md")
OUT_HTML = os.path.join(ROOT, "wiki", "index.html")
ENEMY_DIR = os.path.join(ROOT, "resources", "enemies", "enemies_data")

HEADING_RE = re.compile(r"^(#{1,4})\s+(.*?)\s*$")
LIST_RE = re.compile(r"^(\s*)(-|\d+\.)\s+(.*)$")
TABLE_SEP_RE = re.compile(r"^\|[\s:\-|]+\|$")
HR_RE = re.compile(r"^-{3,}\s*$")

# ── markdown → HTML (covers the constructs used by README + skills wiki) ────


def inline(text, link_prefix=""):
    """Convert inline markdown (bold, italics, code, links) to HTML."""
    t = html.escape(text, quote=False)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", t)

    def _link(m):
        label, href = m.group(1), m.group(2)
        if href.startswith("#") and link_prefix:
            href = link_prefix + href[1:]
        return f'<a href="{href}">{label}</a>'

    return re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", _link, t)


def make_slug(title, seen):
    """GitHub-style heading slug so links in the markdown keep working."""
    slug = title.strip().lower()
    slug = re.sub(r"[^\w\s-]", "", slug, flags=re.UNICODE)
    slug = re.sub(r"\s", "-", slug) or "section"
    count = seen.get(slug, 0)
    seen[slug] = count + 1
    return slug if count == 0 else f"{slug}-{count}"


def _plain(title):
    return title.replace("*", "").replace("`", "")


def _render_list_tree(items, link_prefix=""):
    """Render [(indent, ordered, text)] as a nested <ul>/<ol> tree."""
    if not items:
        return ""
    pos = [0]

    def rec(depth):
        tag = "ol" if items[pos[0]][1] else "ul"
        parts = [f"<{tag}>"]
        while pos[0] < len(items):
            indent, _ordered, text = items[pos[0]]
            if indent < depth:
                break
            if indent > depth:
                parts.append(rec(indent))
                continue
            parts.append(f"<li>{inline(text, link_prefix)}")
            pos[0] += 1
            if pos[0] < len(items) and items[pos[0]][0] > depth:
                parts.append(rec(items[pos[0]][0]))
            parts.append("</li>")
        parts.append(f"</{tag}>")
        return "".join(parts)

    return rec(items[0][0])


def parse_markdown(md, id_prefix="", link_prefix=""):
    """Return (body_html, toc) for a markdown document.

    toc entries are (level, title, slug, html_id) for h2/h3 headings.
    """
    lines = md.splitlines()
    out, toc = [], []
    seen = {}
    i, n = 0, len(lines)

    while i < n:
        s = lines[i].strip()
        if not s:
            i += 1
            continue

        # ── fenced code blocks ──
        if s.startswith("```"):
            i += 1
            code = []
            while i < n and not lines[i].strip().startswith("```"):
                code.append(lines[i])
                i += 1
            i += 1  # closing fence
            out.append('<pre class="code-block"><code>' + html.escape("\n".join(code)) + "</code></pre>")
            continue

        # ── tables ──
        if s.startswith("|") and i + 1 < n and TABLE_SEP_RE.match(lines[i + 1].strip()):
            headers = [c.strip() for c in s.strip("|").split("|")]
            i += 2
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            parts = ['<div class="table-wrap"><table><thead><tr>']
            parts += [f"<th>{inline(h, link_prefix)}</th>" for h in headers]
            parts.append("</tr></thead><tbody>")
            for row in rows:
                parts.append("<tr>" + "".join(f"<td>{inline(c, link_prefix)}</td>" for c in row) + "</tr>")
            parts.append("</tbody></table></div>")
            out.append("".join(parts))
            continue

        # ── headings ──
        m = HEADING_RE.match(s)
        if m:
            level, title = len(m.group(1)), m.group(2)
            plain = _plain(title)
            slug = make_slug(plain, seen)
            h_id = id_prefix + slug
            if level in (2, 3) and plain.lower() not in ("contents", "table of contents"):
                toc.append((level, plain, slug, h_id))
            anchor = (link_prefix + slug) if link_prefix else f"#{h_id}"
            out.append(f'<h{level} id="{h_id}"><a class="anchor" href="{anchor}" aria-hidden="true">#</a>{inline(title, link_prefix)}</h{level}>')
            i += 1
            continue

        # ── horizontal rules ──
        if HR_RE.match(s):
            out.append("<hr>")
            i += 1
            continue

        # ── blockquotes ──
        if s.startswith(">"):
            blocks, buf = [], []
            while i < n and lines[i].strip().startswith(">"):
                text = lines[i].strip()[1:].strip()
                if text:
                    buf.append(text)
                elif buf:
                    blocks.append(" ".join(buf))
                    buf = []
                i += 1
            if buf:
                blocks.append(" ".join(buf))
            out.append("<blockquote>" + "".join(f"<p>{inline(b, link_prefix)}</p>" for b in blocks) + "</blockquote>")
            continue

        # ── lists (nested) ──
        if LIST_RE.match(lines[i].rstrip()) and (s.startswith("- ") or re.match(r"^\d+\.\s", s)):
            items = []
            while i < n:
                raw = lines[i].rstrip()
                mm = LIST_RE.match(raw)
                if mm:
                    indent = len(mm.group(1).replace("\t", "    "))
                    items.append((indent, mm.group(2)[0].isdigit(), mm.group(3)))
                    i += 1
                elif items and re.match(r"^\s+\S", raw) and not raw.strip().startswith(("#", "|", ">")):
                    indent, ordered, text = items[-1]
                    items[-1] = (indent, ordered, text + " " + raw.strip())
                    i += 1
                else:
                    break
            out.append(_render_list_tree(items, link_prefix))
            continue

        # ── paragraphs ──
        buf = [s]
        i += 1
        while i < n:
            t = lines[i].strip()
            if not t or t.startswith(("#", "|", ">")) or HR_RE.match(t) \
                    or LIST_RE.match(lines[i].rstrip()):
                break
            buf.append(t)
            i += 1
        out.append("<p>" + inline(" ".join(buf), link_prefix) + "</p>")

    return "\n".join(out), toc


def render_toc(toc, link_prefix):
    """Render the nested sidebar contents list."""
    if not toc:
        return ""
    out = ['<ul class="toc-list">']
    open_l3 = False
    pending_l2 = False
    for level, title, slug, h_id in toc:
        label = html.escape(title)
        link = f'<a class="toc-link" href="{link_prefix}{slug}" data-target="{h_id}">{label}</a>'
        if level == 2:
            if open_l3:
                out.append("</ul>")
                open_l3 = False
            if pending_l2:
                out.append("</li>")
            out.append(f'<li class="toc-l2">{link}')
            pending_l2 = True
        else:
            if not open_l3:
                out.append('<ul class="toc-sub">')
                open_l3 = True
            out.append(f'<li class="toc-l3">{link}</li>')
    if open_l3:
        out.append("</ul>")
    if pending_l2:
        out.append("</li>")
    out.append("</ul>")
    return "\n".join(out)


# ── enemy / race / biome data ───────────────────────────────────────────────

def _load_yaml(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _load_py_dict(path, attr):
    """Load a plain dict constant from a .py file without importing the package."""
    spec = importlib.util.spec_from_file_location("_wiki_" + attr, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, attr)


def _make_enemy(key, v, cat, source):
    e = {
        "key": key,
        "name": v.get("name", key),
        "race": v.get("race", "?"),
        "level": v.get("level", 0),
        "hp": v.get("base_hp"),
        "mods": dict(v.get("mods") or {}),
        "cat": cat,
        "boss": bool(v.get("boss")),
        "super": bool(v.get("super_boss")),
        "mg": bool(v.get("monster_girl")),
        "source": source,
    }
    if v.get("secondary_race"):
        e["race2"] = v["secondary_race"]
    if v.get("awakened_name"):
        e["awakened"] = v["awakened_name"]
    if v.get("minion_only"):
        e["minion"] = True
    if v.get("_shadow"):
        e["shadow"] = True
    if v.get("_shadow_of"):
        e["shadowOf"] = v["_shadow_of"]
    if v.get("_heroine"):
        e["heroine"] = v["_heroine"]
        e["cat"] = "heroine"
    if isinstance(v.get("elemental_res"), dict) and v["elemental_res"]:
        e["res"] = v["elemental_res"]
    if v.get("status_res") is not None:
        e["statusRes"] = v["status_res"]
    return e


def load_enemy_data():
    """Flatten the enemy YAML files (mirrors resources/enemies/enemy_loader.py)."""
    files = [
        ("all_enemies.yaml", "regular"),
        ("wonderland.yaml", "wonderland"),
        ("superbosses.yaml", "superboss"),
        ("monster_girls.yaml", "mg"),
    ]
    by_key = {}
    for fname, cat in files:
        data = _load_yaml(os.path.join(ENEMY_DIR, fname))
        for key, value in data.items():
            if key == "affection_gifts" or not isinstance(value, dict):
                continue
            if "name" in value and "level" in value:
                entries = [(key, value)]
            else:
                entries = [(k, v) for k, v in value.items()
                           if isinstance(v, dict) and "name" in v and "level" in v]
            for k, v in entries:
                if v.get("city_only"):
                    continue
                by_key[k] = _make_enemy(k, v, cat, fname)
    return by_key


def _enrich_enemies(enemies):
    """Attach innate skills / awakening kit / growth label + trim empty fields."""
    innate = _load_yaml(os.path.join(ROOT, "resources", "skill_book", "innate_skills.yaml"))
    skill_map = innate.get("innate_skills", {})
    defs = innate.get("innate_skill_defs", {})
    awakenings = innate.get("awakenings", {})

    try:
        from combat.ally import get_growth_label  # single source of truth
    except Exception:
        get_growth_label = None

    for e in enemies:
        ids = skill_map.get(e["key"])
        if ids:
            e["skills"] = [{"id": sid, "name": defs.get(sid, {}).get("name", sid)} for sid in ids]
        if e["key"] in awakenings:
            e["awakening"] = [
                {"from": defs.get(b, {}).get("name", b), "to": defs.get(u, {}).get("name", u)}
                for b, u in awakenings[e["key"]].items()
            ]
        if e["mg"] and get_growth_label is not None:
            try:
                label = get_growth_label({"key": e["key"]})
                if label and label != "—":
                    e["growth"] = label
            except Exception:
                pass


def _linkify_skill_roster(body, enemies):
    """Turn monster-girl names in the skills roster tables into links."""
    names = {}
    for e in enemies:
        if e["mg"]:
            names[e["name"] + " ♀"] = e["key"]
        if e.get("awakened"):
            names[e["awakened"] + " ♀"] = e["key"]
    for label, key in names.items():
        needle = ">" + html.escape(label) + "<"
        if needle in body:
            body = body.replace(
                needle,
                f'><a class="xlink" href="#/enemy/{key}">{html.escape(label)}</a><',
            )
    return body


# ── reference pages: equipment & status effects ─────────────────────────────

STAT_ABBR = {
    "Strength": "STR", "Constitution": "CON", "Dexterity": "DEX",
    "Wisdom": "WIS", "Learning": "LRN", "Charisma": "CHA",
}


def build_equipment_markdown():
    """Markdown reference page: weapon base forms, flowers and their sources."""
    from resources.item_generation import (
        WEAPON_FORMS, FORM_WEIGHTS_BY_BIOME, ELEMENT_WEIGHTS_BY_BIOME, FLOWER_ITEMS,
    )
    from resources.items import ITEMS

    weapon_keys = {f["key"] for f in WEAPON_FORMS}
    form_biomes = {}
    for biome, forms in FORM_WEIGHTS_BY_BIOME.items():
        for key in forms:
            if key in weapon_keys:
                form_biomes.setdefault(key, []).append(biome)

    lines = [
        "# Equipment & Flowers",
        "",
        "> Generated from `resources/item_generation.py` and `resources/items.py`. Drops are "
        "**uninfused base forms**; flowers supply elements at the blacksmith; rarity supplies "
        "stats and traits.",
        "",
        "## Weapon Base Forms (29)",
        "",
        "Drops pick a base form — not a form × element × grade coordinate. **Family** is "
        "`weapon_type`, the key used by weapon-synergy effects (e.g. the Old Dopo Robe's sword "
        "family: `sword` / `blade` / `greatsword` / `rapier` / `cutlass`). **Biome bias** marks "
        "forms drawn 3× as often in that biome; `—` means uniform. Uninfused weapons keep their "
        "innate axis: martial forms are Physical (Sunder I), caster forms Magical (Pierce I).",
        "",
        "| Form | Family | Scaling | Base stats | Damage | Biome bias (3×) | Notes |",
        "|---|---|---|---|---|---|---|",
    ]
    for form in WEAPON_FORMS:
        stats = " · ".join(
            f"{STAT_ABBR.get(k, k)} {v:+d}" for k, v in form["template"].items()
        )
        note = "CON weapon: half damage; DR = CON÷2" if form.get("flags", {}).get("con_defense") else "—"
        bias = ", ".join(form_biomes.get(form["key"], [])) or "—"
        lines.append(
            f"| {form['noun']} (`{form['key']}`) | {form['weapon_type']} | {form['scaling']} | "
            f"{stats} | {form['base'].title()} | {bias} | {note} |"
        )

    lines += [
        "",
        "## Flowers (9)",
        "",
        "One flower per element. All are `crafting_material` with `no_random_stock` — **never "
        "sold in shops**. *Favoured biomes* are the `ELEMENT_WEIGHTS_BY_BIOME` rows above the "
        "default weight 1 (temperate is all-1; an unknown biome is a uniform 1/9).",
        "",
        "| Flower | Element | Item id | Favoured biomes (weight) |",
        "|---|---|---|---|",
    ]
    for element, flower_id in FLOWER_ITEMS.items():
        name = ITEMS.get(flower_id, {}).get("name", flower_id)
        favs = [
            f"{biome} ×{weights.get(element, 1)}"
            for biome, weights in ELEMENT_WEIGHTS_BY_BIOME.items()
            if weights.get(element, 1) > 1
        ]
        lines.append(
            f"| {name} | {element.title()} | `{flower_id}` | "
            f"{', '.join(favs) or '— (equal everywhere)'} |"
        )

    lines += [
        "",
        "Flowers are consumed by blacksmith services: **1 per infusion**, **1 per Forge "
        "Commission**, and **3 → 1** element transmutation. Stripping an element returns "
        "**1 flower per 3** that were infused into that slot.",
        "",
        "## Sources",
        "",
        "| Source | Base forms | Flowers | Notes |",
        "|---|---|---|---|",
        "| Dungeon enemy kill (`roll_drop`) | Yes — 60% of successful drop rolls | Yes — 12% of "
        "successful drop rolls | Roll succeeds 50% normal / 70% Pandemonium → **flowers 6.0% / "
        "8.4% per kill**. Element is biome-weighted via `dungeon_biome(player)` (Pandemonium → "
        "`pandemonium`; wild dungeons → own region; else city biome). |",
        "| Treasure room (`handle_treasure_room`) | Yes — 1 random item | **Yes — 1 guaranteed** "
        "| Biome-weighted; the reliable flower-farming spot. |",
        "| City shop | Yes — base-form stock | **No** — `no_random_stock` | Shop rarity caps at "
        "epic. |",
        "| Travel combat / discovery / merchant | Yes | No | Uses `pick_equipment_id` + rarity "
        "helpers; merchant stock caps at epic. |",
        "| Trap bonus / monster_approaching / Wonderland paint-roses & cat riddle | Yes | "
        "Incidental — consumables/flowers make up ≈2% of `_random_item_id` rolls | Bypasses "
        "form weighting (audit §2.9). |",
        "| **Forge Commission** (blacksmith) | **Yes — any form, chosen** | Consumes 1 matching "
        "flower | 600g before discounts → common item + first infusion. The deterministic form "
        "+ element source. |",
        "| Infuse Element (blacksmith) | — | Consumes 1 per infusion | Same element upgrades the "
        "slot; a new element fills the next (caps 1.48 / 1.20 / 1.15). |",
        "| Strip Element (blacksmith) | — | Refunds floor(flowers / 3) of the stripped element "
        "| Removes one flower slot; no gold fee. |",
        "| Transmute Flowers (blacksmith) | — | 3 → 1 of another element | No gold fee; fixes "
        "element-locked farming streaks. |",
        "",
        "**Rate summary:** a specific flower's share is `weight / Σweights` — 1/9 ≈ 11% in "
        "temperate or an unknown biome, up to 3/12 = 25% in a themed biome. At 6.0% flower drops "
        "that is ≈ 67 kills per themed flower and ≈ 150 for an unweighted one. Forge Commission "
        "removes the form × element hunt; flowers then gate infusion count (up to 8 per weapon "
        "primary) while rarity remains the chase.",
    ]
    return "\n".join(lines)


# Curated from combat/combat_ui.py `_get_entity_buff_tags` and
# combat/status_effects.py. Keep in sync when tags or effects change.
BUFF_ROWS = [
    ("Damage boost (attack, +ATK%)", "`DMG+X%`", "Damage dealt +X% from all attacks and skills (Frabjous Day, Fate's Favor, Fervor flasks, Unity cards)."),
    ("Next-action power", "`PWR+X%`", "The next damaging action deals +X% power (Overclock, Tinker Enhancement)."),
    ("Critical chance", "`CRT+X%`", "Critical hit chance +X%."),
    ("Critical damage", "`CDMG+X%`", "Critical hit damage +X%."),
    ("Elemental damage", "`ELM+X%`", "All elemental damage +X% (Prism flasks, Aftershock cards)."),
    ("Damage reduction (flat)", "`DEF`", "Incoming damage reduced by a flat amount (Bastion of Light, Arcane Ward)."),
    ("Damage reduction (%)", "`DEFX%`", "Incoming damage reduced by X% (stacking, capped at 80%)."),
    ("Evasion", "`DGEX%`", "Dodge chance +X% (Dodge, Phantom Dodge, Veil of Dusk)."),
    ("Regeneration (flat)", "`REG` / `REG+X`", "Heal X HP each round (Regenerate, Harmony cards)."),
    ("Regeneration (% max HP)", "`REG+X%`", "Heal X% max HP each round (Vitality flasks, Mass Regenerate)."),
    ("Barrier", "`BARn`", "Absorbs n incoming damage before HP (Aegis Shell, Radiant Rebirth)."),
    ("Death ward", "`WARD`", "Survive one lethal blow at 1 HP (Undying Vow, Death's Vigil, Reboot Protocol)."),
    ("Haste", "`HST`", "+initiative and next-skill cooldown reduction (Haste, Astral Haste)."),
    ("Blessing", "`BLS`", "Attribute buffs from Temple blessings or bed rest."),
    ("Well rested", "`RST`", "Inn rest bonus."),
    ("Arcane blessing", "`ARC`", "Arcane Tower blessing."),
    ("Fear immunity", "`FER-IMN`", "Immune to Fear effects (Through the Forest, Headless Oath)."),
    ("Mark damage bonus", "`MRK+X%`", "Deals +X% damage to the marked enemy."),
    ("Attribute buff", "`+STR` `+CON` `+DEX` `+WIS` `+LRN` `+CHA` `+ALL`", "Flat attribute increase (Battle Cry, Insight, Might flasks)."),
    ("Momentum", "— (info panel: `Momentum(N)`)", "+3% damage per stack, cap 20 (Chronoweave Mantle, Chrysalis)."),
    ("Bloodlust", "—", "Heal for 50% of damage dealt (Barbarian skill)."),
    ("Event Horizon run bonus", "`DMG+` `ELM+` `DEF%` `CRT+` `REG+` `+STAT`", "Flasks/cards/tune-ups stack and are summed per effect type for the whole run."),
]

DEBUFF_ROWS = [
    ("Burn", "`SNG` / `BRN` / `BLZ` / `INF` / `CFL`", "Tiered fire damage over time: 3 / 6 / 10 / 18 / 30 per turn. Higher tiers overwrite lower; same/lower refresh duration."),
    ("Poison", "`PSN`", "Damage over time."),
    ("Bleed", "`BLE`", "Damage over time; a stronger application replaces a normal bleed, some sources stack."),
    ("Shock", "— (no HUD tag)", "Thunder damage over time; each tick can stun (25% on players)."),
    ("Stun", "`STN`", "Skips the next action."),
    ("Freeze", "`FRZ`", "Skips the next attack; Slowed for 1 round after thawing."),
    ("Slow", "`SLW`", "−25% DEX (initiative and DEX checks)."),
    ("Weaken", "`WKN`", "−25% Strength for damage (some skills use a different percentage)."),
    ("Blind", "`BLD`", "25% miss chance; −2 DEX on flee attempts."),
    ("Silence", "`SIL`", "Cannot use skills."),
    ("Dread", "`DRD`", "40% chance to miss each attack; +4 flee difficulty."),
    ("Curse", "`CRS`", "−X to all attributes (scales with level); cured at a Temple."),
    ("Confusion", "`CNF`", "30% chance to strike an ally or miss."),
    ("Fear", "`FER`", "Deals −X% damage (typically −30%)."),
    ("Vulnerable", "`VUL`", "Takes +X% damage."),
    ("Elemental weakness", "`ELW`", "All resistances reduced by X — takes extra elemental damage."),
    ("Damage-taken up", "`DT+X%`", "Takes +X% damage from all sources."),
    ("Expose", "`EXP×N`", "Permanent armor (CON) reduction this fight; stacks up to 5."),
    ("Sunder", "— (no HUD tag)", "Armor reduced by X for N turns."),
    ("Sleep", "— (no HUD tag)", "Skips turns until damaged."),
    ("Paralyze", "— (no HUD tag)", "Skips all actions for N turns (no auto-break)."),
    ("Entomb", "— (no HUD tag)", "Cannot flee; healing received is halved."),
    ("Void-Touched", "— (no HUD tag)", "Healing received becomes damage."),
    ("Painted", "— (info panel: `Painted`)", "Paint stacks; at 5+ the canvas bursts, applying the current color's elemental debuff (6+ empowers it)."),
    ("Hunter's Mark", "`MRK`", "Target takes +X% damage (skill default 15%; Piece of Relationship 20%)."),
    ("Potion sickness", "`SICK×N`", "Cannot use healing consumables for N turns."),
]

BURN_ROWS = [
    ("1", "Singe", "`SNG`", "3"),
    ("2", "Burn", "`BRN`", "6"),
    ("3", "Blaze", "`BLZ`", "10"),
    ("4", "Inferno", "`INF`", "18"),
    ("5", "Conflagration", "`CFL`", "30"),
]

SPECIAL_ROWS = [
    ("Prescript Grace", "`GRC×N`", "Buff — +2% damage, +1.5% crit and +1.5% max-HP regen per stack (cap 9)."),
    ("Prescript Debt", "`DBT×N`", "Debuff — +3% damage taken per stack."),
    ("Prescript mark", "`📜TGT`", "Marked target of the Prescript Ledger."),
    ("Parrot target", "`🦜TGT`", "Wonderland parrot mark."),
    ("Tarnished Jade pins", "`PIN×N`", "Pin stacks; at 10, unleash Divine Lament."),
    ("Wedge Backlash", "`WEDGE −50%`", "All stats halved for the battle."),
    ("Fatigue", "`FATIGUE I/II/III` (👁 from II)", "Stress/fatigue stacks; hallucinations can appear from II."),
    ("Event Horizon Entropy", "`ENT×N (−X% attrs)`", "Run pressure — −1% all attributes per stack (cap −45%)."),
    ("Trial burdens", "`TRL×N: …`", "Negative trial cards empowering every Rift enemy; the burden text follows the count."),
]


def build_effects_markdown():
    """Markdown reference page: buffs, debuffs, burn tiers and special tags."""
    lines = [
        "# Buffs & Debuffs",
        "",
        "> HUD tags from `combat/combat_ui.py` (`_get_entity_buff_tags`); effects from "
        "`combat/status_effects.py` and the combat engine. The full name is shown in info panels "
        "via `get_player_status_tags`.",
        "",
        "## Buffs",
        "",
        "| Effect | HUD tag | What it does |",
        "|---|---|---|",
    ]
    lines += [f"| {name} | {tag} | {effect} |" for name, tag, effect in BUFF_ROWS]
    lines += [
        "",
        "## Debuffs",
        "",
        "| Effect | HUD tag | What it does |",
        "|---|---|---|",
    ]
    lines += [f"| {name} | {tag} | {effect} |" for name, tag, effect in DEBUFF_ROWS]
    lines += [
        "",
        "## Burn Tiers",
        "",
        "Fire skills and Ignite apply a burn **tier**; a higher tier overwrites a lower one, the "
        "same or a lower tier refreshes its duration.",
        "",
        "| Tier | Name | HUD tag | Damage per turn |",
        "|---|---|---|---|",
    ]
    lines += [f"| {tier} | {name} | {tag} | {dmg} |" for tier, name, tag, dmg in BURN_ROWS]
    lines += [
        "",
        "## Special Stacks & Marks",
        "",
        "| Effect | HUD tag | What it does |",
        "|---|---|---|",
    ]
    lines += [f"| {name} | {tag} | {effect} |" for name, tag, effect in SPECIAL_ROWS]
    lines += [
        "",
        "## Reading the HUD",
        "",
        "- **+ATK%** attack/damage buffs are shown as **`DMG+X%`** in the combat HUD — there is "
        "no separate ATK tag.",
        "- Permanent Event Horizon bonuses are summed per effect type into one tag (e.g. "
        "`DMG+37%`, `ELM+14%`, `DEF3%`, `CRT+6%`, `REG+2%`); temporary ally-skill buffs keep "
        "individual tags so their remaining turns stay visible.",
        "- Some statuses have no short HUD tag yet (Shock, Sunder, Sleep, Paralyze, Entomb, "
        "Void-Touched, Painted) — they are still announced in the combat log and info panels.",
        "- Debuff tags appear on the entity they affect: enemy-side tags on the enemy row, "
        "player/ally tags on the party row.",
    ]
    return "\n".join(lines)


# ── page assets ─────────────────────────────────────────────────────────────

PAGE_CSS = r"""
* { box-sizing: border-box; }
:root {
  --bg: #1a1a2e; --bg-mid: #16213e; --bg-light: #0f3460; --card: #1e1e3f;
  --accent: #e94560; --accent-hover: #ff6b81; --gold: #f1c40f;
  --text: #eaeaea; --dim: #a0a0a0; --head: #ffffff; --border: #2c2c50;
  --topbar-h: 56px; --sidebar-w: 310px;
  --mono: Consolas, Menlo, "DejaVu Sans Mono", monospace;
}
html { scroll-behavior: smooth; }
body { margin: 0; background: var(--bg); color: var(--text); font: 15px/1.6 "Segoe UI", system-ui, -apple-system, "Helvetica Neue", Arial, sans-serif; }
[hidden] { display: none !important; }
.skip-link { position: absolute; left: -999px; top: 0; z-index: 200; background: var(--accent); color: #fff; padding: 6px 12px; }
.skip-link:focus { left: 8px; top: 8px; }
a { color: #8ab4f8; }
a:hover { color: #b3ccff; }

/* ── top bar ── */
.topbar { position: fixed; top: 0; left: 0; right: 0; height: var(--topbar-h); z-index: 60; display: flex; align-items: center; gap: 14px; padding: 0 16px; background: rgba(22, 33, 62, .96); border-bottom: 1px solid var(--border); -webkit-backdrop-filter: blur(8px); backdrop-filter: blur(8px); }
.brand { font-size: 15px; font-weight: 700; color: var(--head); text-decoration: none; white-space: nowrap; cursor: pointer; }
.brand span { color: var(--accent); }
.brand:hover { color: var(--accent-hover); }
.topnav { display: flex; gap: 4px; }
.topnav a { padding: 5px 10px; border-radius: 7px; color: var(--text); text-decoration: none; font-size: 13.5px; }
.topnav a:hover { background: rgba(255, 255, 255, .07); }
.topnav a.active { background: rgba(233, 69, 96, .16); color: var(--accent-hover); }
.topbar-spacer { flex: 1 1 auto; }
.search-box { display: flex; align-items: center; gap: 6px; flex: 0 1 430px; min-width: 0; background: var(--card); border: 1px solid var(--border); border-radius: 8px; padding: 4px 8px; }
.search-box:focus-within { border-color: var(--accent); box-shadow: 0 0 0 2px rgba(233, 69, 96, .25); }
#search { flex: 1 1 auto; min-width: 70px; background: transparent; border: 0; outline: 0; color: var(--text); font-size: 14px; }
#search::placeholder { color: var(--dim); }
#search-count { font-size: 12px; color: var(--dim); white-space: nowrap; }
.search-btn { background: transparent; border: 0; color: var(--dim); font-size: 14px; padding: 2px 6px; border-radius: 5px; cursor: pointer; }
.search-btn:hover { color: var(--head); background: rgba(255, 255, 255, .08); }
#menu-toggle { display: none; background: var(--card); color: var(--text); border: 1px solid var(--border); border-radius: 6px; padding: 5px 9px; font-size: 14px; cursor: pointer; }

/* ── sidebar ── */
.sidebar { position: fixed; top: var(--topbar-h); bottom: 0; left: 0; width: var(--sidebar-w); z-index: 40; overflow-y: auto; padding: 12px 10px 40px; background: var(--bg-mid); border-right: 1px solid var(--border); }
.side-nav { display: flex; flex-direction: column; gap: 2px; padding-bottom: 10px; margin-bottom: 6px; border-bottom: 1px solid var(--border); }
.side-nav a { display: block; padding: 7px 10px; border-radius: 7px; color: var(--text); text-decoration: none; font-size: 14px; }
.side-nav a:hover { background: rgba(255, 255, 255, .06); }
.side-nav a.active { background: rgba(233, 69, 96, .14); color: var(--accent-hover); font-weight: 600; }
.toc-title { padding: 10px 10px 6px; font-size: 11px; letter-spacing: .12em; text-transform: uppercase; color: var(--dim); }
.toc-list, .toc-sub { list-style: none; margin: 0; padding: 0; }
.toc-list .toc-link { display: block; padding: 4px 10px; border-left: 2px solid transparent; border-radius: 6px; color: var(--text); font-size: 13.5px; text-decoration: none; }
.toc-l3 .toc-link { padding-left: 24px; font-size: 12.5px; color: var(--dim); }
.toc-link:hover { background: rgba(255, 255, 255, .05); color: var(--head); }
.toc-link.active { color: var(--accent-hover); border-left-color: var(--accent); background: rgba(233, 69, 96, .08); }
.dim { color: var(--dim); font-weight: 400; }

/* ── content ── */
main { margin-left: var(--sidebar-w); max-width: 1120px; padding: calc(var(--topbar-h) + 26px) 34px 90px; }
h1 { margin: .2em 0 .6em; font-size: 29px; line-height: 1.25; color: var(--head); }
h1::after { content: ""; display: block; width: 72px; height: 4px; margin-top: 12px; border-radius: 2px; background: linear-gradient(90deg, var(--accent), transparent); }
h2 { margin: 2.2em 0 .7em; padding-bottom: .3em; font-size: 22px; color: var(--head); border-bottom: 1px solid var(--border); scroll-margin-top: calc(var(--topbar-h) + 14px); }
h3 { margin: 1.6em 0 .5em; font-size: 17.5px; color: #dfe4ff; scroll-margin-top: calc(var(--topbar-h) + 14px); }
h4 { margin: 1.4em 0 .4em; font-size: 15.5px; color: #cfd5f5; scroll-margin-top: calc(var(--topbar-h) + 14px); }
h1 .anchor, h2 .anchor, h3 .anchor, h4 .anchor { margin-right: 6px; color: var(--accent); font-weight: 400; text-decoration: none; opacity: 0; transition: opacity .15s; }
h1:hover .anchor, h2:hover .anchor, h3:hover .anchor, h4:hover .anchor, .anchor:focus { opacity: .9; }
p { margin: .7em 0; }
strong { color: #fff; }
code { padding: 1px 5px; border: 1px solid rgba(255, 255, 255, .07); border-radius: 4px; background: rgba(255, 255, 255, .07); color: #ffd9a0; font-family: var(--mono); font-size: .9em; }
pre.code-block { margin: 1em 0; padding: 12px 14px; border: 1px solid var(--border); border-radius: 10px; background: #10162c; overflow-x: auto; }
pre.code-block code { padding: 0; border: 0; background: none; color: #cfe3ff; font-size: 13px; line-height: 1.55; }
blockquote { margin: 1em 0; padding: .7em 1em; border-left: 3px solid var(--accent); border-radius: 0 8px 8px 0; background: rgba(233, 69, 96, .06); color: #cfd3e6; }
blockquote p { margin: .35em 0; font-size: 14px; }
hr { border: 0; border-top: 1px solid var(--border); margin: 2.2em 0; }
ul, ol { margin: .5em 0 .9em; padding-left: 1.5em; }
li { margin: .32em 0; }
main li::marker { color: var(--accent); }
ul.plain { list-style: none; padding-left: .2em; }
ul.plain li { margin: .2em 0; }

/* skill bullet meta / tag chips (skills page only) */
em.meta { font-family: var(--mono); font-size: 12.5px; font-style: normal; color: var(--dim); }
em.tags { font-size: 12.5px; font-style: normal; color: #6fd3b4; }
.el { font-weight: 600; }
.el-fire { color: #ff7043; } .el-water { color: #4fc3f7; } .el-thunder { color: #ffd54f; }
.el-wind { color: #81c784; } .el-earth { color: #cfa64b; } .el-light { color: #fff176; }
.el-dark { color: #b39ddb; } .el-magical { color: #f06292; } .el-physical { color: #b0bec5; }
.el-spacing { margin-right: 8px; }

/* ── tables (guide / skills) ── */
.table-wrap { margin: 1em 0 1.4em; border: 1px solid var(--border); border-radius: 10px; overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 14px; }
thead th { padding: 9px 12px; background: var(--bg-light); color: var(--head); font-weight: 600; text-align: left; white-space: nowrap; }
thead th.sortable { cursor: pointer; user-select: none; }
thead th.sortable:hover { background: #17457f; }
th.sort-asc::after { content: " ▲"; color: var(--accent-hover); font-size: 10px; }
th.sort-desc::after { content: " ▼"; color: var(--accent-hover); font-size: 10px; }
tbody td { padding: 7px 12px; border-top: 1px solid rgba(255, 255, 255, .05); vertical-align: top; }
tbody tr:nth-child(even) { background: rgba(255, 255, 255, .02); }
tbody tr:hover { background: rgba(233, 69, 96, .08); }
.xlink { color: inherit; text-decoration: none; border-bottom: 1px dotted var(--accent); }
.xlink:hover { color: var(--accent-hover); }

/* ── tags & badges ── */
.tag { display: inline-block; margin: 1px 3px 1px 0; padding: 1px 9px; border: 1px solid var(--border); border-radius: 999px; background: rgba(255, 255, 255, .07); color: var(--text); font-size: 12.5px; text-decoration: none; cursor: pointer; }
a.tag:hover { border-color: var(--accent); background: rgba(233, 69, 96, .18); color: #fff; }
.tag-static { cursor: default; }
.badge { display: inline-block; margin-left: 6px; padding: 0 7px; border-radius: 999px; font-size: 10.5px; font-weight: 700; letter-spacing: .04em; vertical-align: 1px; text-decoration: none; cursor: default; }
a.badge { cursor: pointer; }
.badge-mg { background: rgba(233, 69, 96, .22); color: #ff9db0; border: 1px solid rgba(233, 69, 96, .5); }
.badge-boss { background: rgba(243, 156, 18, .18); color: #ffd166; border: 1px solid rgba(243, 156, 18, .5); }
.badge-super { background: rgba(155, 89, 182, .22); color: #d2a8ff; border: 1px solid rgba(155, 89, 182, .55); }
.badge-minion { background: rgba(255, 255, 255, .08); color: #b9b9c9; border: 1px solid rgba(255, 255, 255, .2); }
.badge-shadow { background: rgba(52, 73, 94, .5); color: #a9c1e8; border: 1px solid rgba(100, 140, 200, .45); }
.badge-heroine { background: rgba(26, 188, 156, .2); color: #7fe8d0; border: 1px solid rgba(26, 188, 156, .5); }
a.badge:hover { filter: brightness(1.25); }

/* ── enemy database ── */
.page-sub { color: var(--dim); margin-top: -.2em; }
.filterbar { margin: 1em 0 .4em; }
.chips { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 10px; }
.chip-btn { padding: 5px 12px; border: 1px solid var(--border); border-radius: 999px; background: var(--card); color: var(--text); font-size: 13px; cursor: pointer; }
.chip-btn:hover { border-color: var(--accent); }
.chip-btn.active { background: rgba(233, 69, 96, .2); border-color: var(--accent); color: #fff; }
.filter-row { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; }
.filter-row select, .filter-row input { background: var(--card); color: var(--text); border: 1px solid var(--border); border-radius: 7px; padding: 5px 8px; font-size: 13px; }
.filter-row input[type="number"] { width: 76px; }
.filter-row .fld { color: var(--dim); font-size: 13px; }
.sort-dir { padding: 5px 10px; border: 1px solid var(--border); border-radius: 7px; background: var(--card); color: var(--text); font-size: 13px; cursor: pointer; }
.sort-dir:hover { border-color: var(--accent); }
.count-note { margin-left: auto; color: var(--dim); font-size: 13px; }
.multiselect { position: relative; }
.ms-btn { display: flex; gap: 6px; align-items: center; background: var(--card); color: var(--text); border: 1px solid var(--border); border-radius: 7px; padding: 5px 10px; font-size: 13px; cursor: pointer; }
.ms-btn:hover { border-color: var(--accent); }
.ms-panel { position: absolute; top: calc(100% + 6px); left: 0; z-index: 80; width: min(280px, 84vw); max-height: 340px; overflow-y: auto; background: var(--bg-mid); border: 1px solid var(--border); border-radius: 10px; padding: 8px; box-shadow: 0 10px 30px rgba(0, 0, 0, .5); }
.ms-actions { display: flex; justify-content: space-between; align-items: center; gap: 8px; padding: 2px 4px 8px; font-size: 12px; }
.ms-mini { background: var(--card); color: var(--text); border: 1px solid var(--border); border-radius: 6px; padding: 2px 8px; font-size: 12px; cursor: pointer; }
.ms-mini:hover { border-color: var(--accent); }
.ms-opt { display: flex; align-items: center; gap: 8px; padding: 5px 6px; border-radius: 6px; font-size: 13px; cursor: pointer; }
.ms-opt:hover { background: rgba(255, 255, 255, .06); }
.ms-opt input { accent-color: var(--accent); }
.ms-opt .dim { margin-left: auto; }
.active-filters { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; margin: 8px 0 2px; font-size: 13px; }
.active-filters .lbl { color: var(--dim); }
.chip { display: inline-block; padding: 2px 10px; border: 1px solid rgba(233, 69, 96, .5); border-radius: 999px; background: rgba(233, 69, 96, .12); color: #ffc2cd; text-decoration: none; cursor: pointer; }
.chip .x { color: var(--dim); }
.chip:hover { background: rgba(233, 69, 96, .25); color: #fff; }
.chip-clear { border-style: dashed; border-color: var(--border); background: none; color: var(--dim); }
.race-banner { margin: 10px 0 4px; padding: 10px 14px; border: 1px solid var(--border); border-left: 3px solid var(--accent); border-radius: 0 10px 10px 0; background: var(--bg-mid); font-size: 13.5px; }
.race-banner .lbl { color: var(--dim); margin-right: 4px; }
.enemy-table td:first-child { font-weight: 600; }
.enemy-row { cursor: pointer; }
.enemy-row:hover td { background: rgba(233, 69, 96, .1); }
.empty { color: var(--dim); text-align: center; padding: 18px 0; }

/* ── enemy detail ── */
.back-link { display: inline-block; margin-bottom: 6px; color: var(--dim); text-decoration: none; cursor: pointer; }
.back-link:hover { color: var(--accent-hover); }
.detail-tags { margin: 4px 0 14px; }
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(330px, 1fr)); gap: 12px; margin: 12px 0; }
.card { background: var(--bg-mid); border: 1px solid var(--border); border-radius: 10px; padding: 14px 16px; }
.card-title { margin: 0 0 8px; font-size: 15px; color: var(--head); }
.race-line { margin: .35em 0; font-size: 13.5px; }
.race-line .lbl { color: var(--dim); }
.attr-table { width: auto; min-width: 220px; font-size: 13.5px; }
.attr-table td { padding: 3px 12px 3px 0; border: 0; }
.attr-table td:last-child { font-weight: 700; }
.pos { color: #7ee2a8; } .neg { color: #ff8f8f; }

mark { padding: 0 2px; border-radius: 3px; background: var(--gold); color: #1a1a2e; }
mark.current { background: var(--accent); color: #fff; }
.page-footer { margin-top: 46px; padding-top: 14px; border-top: 1px solid var(--border); color: var(--dim); font-size: 12.5px; }
#to-top { position: fixed; right: 22px; bottom: 22px; z-index: 70; padding: 10px 14px; border: 0; border-radius: 999px; background: var(--accent); color: #fff; font-size: 14px; cursor: pointer; opacity: 0; pointer-events: none; transition: opacity .2s; box-shadow: 0 4px 14px rgba(0, 0, 0, .45); }
#to-top.visible { opacity: 1; pointer-events: auto; }
#to-top:hover { background: var(--accent-hover); }

@media (max-width: 980px) {
  #menu-toggle { display: inline-block; }
  .sidebar { width: 290px; transform: translateX(-100%); transition: transform .2s ease; }
  body.nav-open .sidebar { transform: none; box-shadow: 0 0 40px rgba(0, 0, 0, .6); }
  main { margin-left: 0; padding: calc(var(--topbar-h) + 18px) 16px 80px; }
  .brand { display: none; }
  .search-box { flex: 1 1 auto; }
}
@media (max-width: 640px) { .topnav { display: none; } #search-count { display: none; } .count-note { margin-left: 0; width: 100%; } }
@media print {
  .topbar, .sidebar, #to-top { display: none !important; }
  main { margin: 0; padding: 0; max-width: none; }
  body { background: #fff; color: #111; }
  h1, h2, h3, h4, strong { color: #000; }
  main a { color: #000; }
  code { color: #333; background: #f2f2f2; }
}
"""

PAGE_JS = r"""
(function () {
  "use strict";
  var DATA = window.WIKI_DATA || { enemies: [], races: {}, biomes: {} };
  var byKey = {};
  DATA.enemies.forEach(function (e) { byKey[e.key] = e; });

  var marks = [], cur = -1, searchMode = "text", searchRoot = null;
  var lastListHash = "#/enemies";
  var spyHeadings = [], spyLinks = {};

  var CATS = [["all", "All"], ["mg", "Monster Girls"], ["regular", "Regular"], ["boss", "Bosses"], ["super", "Superbosses"], ["wonderland", "Wonderland"], ["heroine", "Heroines"]];
  var CAT_LABELS = { mg: "Monster Girl", regular: "Regular enemy", superboss: "Superboss", wonderland: "Wonderland", heroine: "Heroine" };
  var CAT_BADGE = { mg: "mg", super: "super", boss: "boss", heroine: "heroine" };
  var ATTRS = [["Strength", "STR"], ["Constitution", "CON"], ["Dexterity", "DEX"], ["Wisdom", "WIS"], ["Learning", "LRN"], ["Charisma", "CHA"]];

  function el(id) { return document.getElementById(id); }
  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) { return c === "&" ? "&amp;" : c === "<" ? "&lt;" : c === ">" ? "&gt;" : "&quot;"; }); }
  function enc(s) { return encodeURIComponent(String(s == null ? "" : s)); }
  function cap(s) { s = String(s || ""); return s.charAt(0).toUpperCase() + s.slice(1); }
  function nav(hash) { if (location.hash === hash) { render(); } else { location.hash = hash; } }
  function hashFor(params) { var qs = params.toString(); return "#/enemies" + (qs ? "?" + qs : ""); }
  function replaceHash(params) {
    var url = hashFor(params);
    try { history.replaceState(null, "", url); } catch (err) { location.hash = url; }
  }

  function parseHash() {
    var h = location.hash || "";
    if (h.indexOf("#/") !== 0) { h = "#/" + h.replace(/^#\/?/, ""); }
    var qIdx = h.indexOf("?");
    var path = qIdx === -1 ? h.slice(2) : h.slice(2, qIdx);
    var params = new URLSearchParams(qIdx === -1 ? "" : h.slice(qIdx + 1));
    var parts = path.split("/").filter(function (x) { return x; });
    return { route: parts[0] || "home", arg: parts[1] || "", params: params };
  }

  // ── text search (guide / skills pages) ──
  function clearMarks() {
    marks.forEach(function (m) { m.parentNode.replaceChild(document.createTextNode(m.textContent), m); });
    marks = [];
    cur = -1;
  }

  function runTextSearch(q) {
    clearMarks();
    var countEl = el("search-count");
    if (!q || !searchRoot) { countEl.textContent = ""; return; }
    var ql = q.toLowerCase();
    [].slice.call(searchRoot.querySelectorAll("li, p, td, th, h1, h2, h3, h4, pre")).forEach(function (root) {
      var walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null);
      var nodes = [], node;
      while ((node = walker.nextNode())) {
        var parent = node.parentElement;
        if (parent && parent.closest(".anchor")) continue;
        nodes.push(node);
      }
      nodes.forEach(function (n) {
        var text = n.nodeValue;
        var lower = text.toLowerCase();
        var idx = lower.indexOf(ql);
        if (idx === -1) return;
        var frag = document.createDocumentFragment();
        var from = 0;
        while (idx !== -1) {
          if (idx > from) frag.appendChild(document.createTextNode(text.slice(from, idx)));
          var m = document.createElement("mark");
          m.textContent = text.slice(idx, idx + q.length);
          frag.appendChild(m);
          marks.push(m);
          from = idx + q.length;
          idx = lower.indexOf(ql, from);
        }
        if (from < text.length) frag.appendChild(document.createTextNode(text.slice(from)));
        n.parentNode.replaceChild(frag, n);
      });
    });
    countEl.textContent = marks.length ? marks.length + (marks.length === 1 ? " match" : " matches") : "no matches";
  }

  function go(delta) {
    if (!marks.length) return;
    cur = (cur + delta + marks.length) % marks.length;
    marks.forEach(function (m, i) { m.classList.toggle("current", i === cur); });
    marks[cur].scrollIntoView({ behavior: "smooth", block: "center" });
  }

  function jumpToFirst() {
    if (!marks.length) return;
    cur = 0;
    marks.forEach(function (m, i) { m.classList.toggle("current", i === 0); });
    marks[0].scrollIntoView({ behavior: "smooth", block: "center" });
  }

  function setupTextSearch(viewId, placeholder) {
    searchMode = "text";
    searchRoot = el(viewId);
    el("search").placeholder = placeholder;
    el("search-count").style.display = "";
    el("search-prev").style.display = "";
    el("search-next").style.display = "";
  }

  function setupFilterSearch() {
    searchMode = "filter";
    searchRoot = null;
    clearMarks();
    el("search").placeholder = "Filter enemies by name…";
    el("search-count").textContent = "";
    el("search-prev").style.display = "none";
    el("search-next").style.display = "none";
  }

  function initSearchBox() {
    var input = el("search");
    var timer = null;
    input.addEventListener("input", function () {
      if (timer) clearTimeout(timer);
      timer = setTimeout(function () {
        if (searchMode === "filter") {
          var r = parseHash();
          var p = new URLSearchParams(r.params.toString());
          var v = input.value.trim();
          if (v) { p.set("q", v); } else { p.delete("q"); }
          replaceHash(p);
          renderEnemies(p);
        } else {
          runTextSearch(input.value.trim());
        }
      }, 140);
    });
    input.addEventListener("keydown", function (e) {
      if (e.key === "Enter") {
        if (searchMode === "text") {
          e.preventDefault();
          if (timer) clearTimeout(timer);
          runTextSearch(input.value.trim());
          go(e.shiftKey ? -1 : 1);
        }
      } else if (e.key === "Escape") {
        input.value = "";
        if (searchMode === "filter") {
          var r = parseHash();
          var p = new URLSearchParams(r.params.toString());
          p.delete("q");
          replaceHash(p);
          renderEnemies(p);
        } else {
          runTextSearch("");
        }
      }
    });
    el("search-prev").addEventListener("click", function () { go(-1); });
    el("search-next").addEventListener("click", function () { go(1); });
    document.addEventListener("keydown", function (e) {
      var ae = document.activeElement;
      if (e.key === "/" && ae !== input && (!ae || !/^(INPUT|TEXTAREA|SELECT)$/.test(ae.tagName))) {
        e.preventDefault();
        input.focus();
      }
    });
  }

  // ── enemy database ──
  function computeCounts() {
    var c = { all: DATA.enemies.length, mg: 0, regular: 0, boss: 0, super: 0, wonderland: 0, heroine: 0 };
    DATA.enemies.forEach(function (e) {
      if (e.mg) c.mg++;
      if (e.cat === "regular" && !e.boss) c.regular++;
      if (e.boss) c.boss++;
      if (e.super || e.cat === "superboss") c.super++;
      if (e.cat === "wonderland") c.wonderland++;
      if (e.heroine) c.heroine++;
    });
    return c;
  }
  var COUNTS = computeCounts();

  function setRaces(p, values) {
    p.delete("race");
    values.forEach(function (v) { p.append("race", v); });
  }

  function updateEnemyParams(mutator) {
    var r = parseHash();
    var p = new URLSearchParams(r.params.toString());
    mutator(p);
    replaceHash(p);
    renderEnemies(p);
  }

  function initEnemiesView() {
    var chips = el("cat-chips");
    chips.innerHTML = CATS.map(function (c) {
      return '<button type="button" class="chip-btn" data-cat="' + c[0] + '">' + c[1] + ' <span class="dim">' + (COUNTS[c[0]] || 0) + "</span></button>";
    }).join("");
    chips.addEventListener("click", function (ev) {
      var b = ev.target.closest("button[data-cat]");
      if (!b) return;
      updateEnemyParams(function (p) {
        var v = b.getAttribute("data-cat");
        if (v === "all") { p.delete("cat"); } else { p.set("cat", v); }
      });
    });

    var raceBtn = el("race-btn");
    var racePanel = el("race-panel");
    var raceOptions = el("race-options");
    raceOptions.innerHTML = Object.keys(DATA.races).sort().map(function (n) {
      var count = DATA.enemies.filter(function (e) { return e.race === n || e.race2 === n; }).length;
      return '<label class="ms-opt"><input type="checkbox" value="' + esc(n) + '"> ' + esc(n) + ' <span class="dim">' + count + "</span></label>";
    }).join("");
    raceBtn.addEventListener("click", function (ev) {
      ev.stopPropagation();
      racePanel.hidden = !racePanel.hidden;
      raceBtn.setAttribute("aria-expanded", racePanel.hidden ? "false" : "true");
    });
    racePanel.addEventListener("click", function (ev) { ev.stopPropagation(); });
    document.addEventListener("click", function () {
      if (!racePanel.hidden) { racePanel.hidden = true; raceBtn.setAttribute("aria-expanded", "false"); }
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && !racePanel.hidden) { racePanel.hidden = true; raceBtn.setAttribute("aria-expanded", "false"); }
    });
    raceOptions.addEventListener("change", function (ev) {
      var box = ev.target;
      if (!box || box.type !== "checkbox") return;
      var chosen = parseHash().params.getAll("race").filter(Boolean);
      var idx = chosen.indexOf(box.value);
      if (box.checked && idx === -1) chosen.push(box.value);
      if (!box.checked && idx !== -1) chosen.splice(idx, 1);
      updateEnemyParams(function (p) { setRaces(p, chosen); });
    });
    el("race-clear").addEventListener("click", function () {
      updateEnemyParams(function (p) { p.delete("race"); });
    });

    function levelChanged() {
      updateEnemyParams(function (p) {
        p.delete("lvl");
        var lo = el("lvl-min").value.trim(), hi = el("lvl-max").value.trim();
        if (lo) { p.set("min", lo); } else { p.delete("min"); }
        if (hi) { p.set("max", hi); } else { p.delete("max"); }
      });
    }
    el("lvl-min").addEventListener("change", levelChanged);
    el("lvl-max").addEventListener("change", levelChanged);
    el("sort").addEventListener("change", function () {
      updateEnemyParams(function (p) { p.set("sort", el("sort").value); });
    });
    el("sort-dir").addEventListener("click", function () {
      updateEnemyParams(function (p) { p.set("dir", p.get("dir") === "desc" ? "asc" : "desc"); });
    });
  }

  function filterEnemies(params) {
    var q = (params.get("q") || "").toLowerCase();
    var cat = params.get("cat") || "";
    var races = params.getAll("race").filter(Boolean);
    var lvl = params.get("lvl");
    var min = params.get("min"), max = params.get("max");
    var list = DATA.enemies.filter(function (e) {
      if (q && e.name.toLowerCase().indexOf(q) === -1) return false;
      if (races.length && races.indexOf(e.race) === -1 && (!e.race2 || races.indexOf(e.race2) === -1)) return false;
      if (lvl && String(e.level) !== lvl) return false;
      if (min && e.level < +min) return false;
      if (max && e.level > +max) return false;
      if (cat && cat !== "all") {
        if (cat === "mg" && !e.mg) return false;
        if (cat === "regular" && !(e.cat === "regular" && !e.boss)) return false;
        if (cat === "boss" && !e.boss) return false;
        if (cat === "super" && !(e.super || e.cat === "superboss")) return false;
        if (cat === "wonderland" && e.cat !== "wonderland") return false;
        if (cat === "heroine" && !e.heroine) return false;
      }
      return true;
    });
    var key = params.get("sort") || "name";
    var dir = params.get("dir") === "desc" ? -1 : 1;
    list.sort(function (a, b) {
      var va, vb;
      if (key === "level") { va = a.level; vb = b.level; }
      else if (key === "hp") { va = a.hp || 0; vb = b.hp || 0; }
      else if (key === "race") { va = a.race.toLowerCase(); vb = b.race.toLowerCase(); }
      else { va = a.name.toLowerCase(); vb = b.name.toLowerCase(); }
      if (va < vb) return -1 * dir;
      if (va > vb) return 1 * dir;
      return a.name.localeCompare(b.name);
    });
    return list;
  }

  function enemyBadges(e, clickable) {
    var out = [];
    function badge(kind, label) {
      if (clickable && CAT_BADGE[kind]) {
        return '<a class="badge badge-' + kind + '" data-nav="#/enemies?cat=' + CAT_BADGE[kind] + '">' + label + "</a>";
      }
      return '<span class="badge badge-' + kind + '">' + label + "</span>";
    }
    if (e.mg) out.push(badge("mg", "♀ MG"));
    if (e.super) out.push(badge("super", "SUPERBOSS"));
    else if (e.boss) out.push(badge("boss", "BOSS"));
    if (e.minion) out.push('<span class="badge badge-minion">MINION</span>');
    if (e.shadow) out.push('<span class="badge badge-shadow">SHADOW</span>');
    if (e.heroine) out.push(badge("heroine", "HEROINE"));
    return out.join("");
  }

  function enemyRow(e) {
    return '<tr class="enemy-row" data-nav="#/enemy/' + enc(e.key) + '">' +
      '<td class="ename">' + esc(e.name) + enemyBadges(e, false) + "</td>" +
      '<td><a class="tag" data-nav="#/enemies?race=' + enc(e.race) + '">' + esc(e.race) + "</a></td>" +
      '<td><a class="tag" data-nav="#/enemies?lvl=' + e.level + '">' + e.level + "</a></td>" +
      "<td>" + (e.hp == null ? "—" : e.hp) + "</td>" +
      "</tr>";
  }

  function catLabel(cat) {
    for (var i = 0; i < CATS.length; i++) { if (CATS[i][0] === cat) return CATS[i][1]; }
    return cat;
  }

  function hashWithout(params, dropKey, dropValue) {
    var p = new URLSearchParams();
    params.forEach(function (v, k) {
      if (k === dropKey && (dropValue === undefined || v === dropValue)) return;
      p.append(k, v);
    });
    return hashFor(p);
  }

  function filterChip(params, key, value, label) {
    return '<a class="chip" data-nav="' + esc(hashWithout(params, key, value)) + '">' + esc(label) + ' <span class="x">×</span></a>';
  }

  function activeChips(params) {
    var chips = [];
    var cat = params.get("cat");
    if (cat && cat !== "all") chips.push(filterChip(params, "cat", undefined, catLabel(cat)));
    params.getAll("race").filter(Boolean).forEach(function (r) {
      chips.push(filterChip(params, "race", r, "Race: " + r));
    });
    if (params.get("lvl")) chips.push(filterChip(params, "lvl", undefined, "Level " + params.get("lvl")));
    if (params.get("min")) chips.push(filterChip(params, "min", undefined, "Level ≥ " + params.get("min")));
    if (params.get("max")) chips.push(filterChip(params, "max", undefined, "Level ≤ " + params.get("max")));
    if (!chips.length) return "";
    return '<span class="lbl">Filters:</span> ' + chips.join(" ") + '<a class="chip chip-clear" data-nav="#/enemies">Clear all</a>';
  }

  function chipsIf(map, test) {
    return Object.keys(map || {}).filter(function (k) { return test(map[k]); }).map(function (k) {
      return '<span class="el el-' + k + '">' + cap(k) + " ×" + map[k] + "</span>";
    }).join('<span class="el-spacing"></span>');
  }

  function raceBanner(race) {
    var r = DATA.races[race];
    var count = DATA.enemies.filter(function (e) { return e.race === race || e.race2 === race; }).length;
    var h = "<div class=\"race-banner\"><strong>" + esc(race) + "</strong> — " + count + " entries";
    if (r && r.mods && Object.keys(r.mods).length) {
      var mods = Object.keys(r.mods).map(function (k) {
        var v = r.mods[k];
        return '<span class="' + (v > 0 ? "pos" : "neg") + '">' + esc(k) + " " + (v > 0 ? "+" + v : v) + "</span>";
      }).join(" · ");
      h += ' <span class="lbl">· racial mods:</span> ' + mods;
    }
    var biomes = DATA.biomes[race] || [];
    if (biomes.length) h += ' <span class="lbl">· biomes:</span> ' + biomes.map(esc).join(", ");
    return h + "</div>";
  }

  function renderEnemies(params) {
    var q = params.get("q") || "";
    var input = el("search");
    if (input.value !== q) input.value = q;
    var cat = params.get("cat") || "all";
    [].slice.call(el("cat-chips").querySelectorAll("button")).forEach(function (b) {
      b.classList.toggle("active", b.getAttribute("data-cat") === cat);
    });
    var races = params.getAll("race").filter(Boolean);
    [].slice.call(el("race-options").querySelectorAll("input")).forEach(function (box) {
      box.checked = races.indexOf(box.value) !== -1;
    });
    el("race-btn-label").textContent = races.length === 0 ? "All" : (races.length === 1 ? races[0] : races[0] + " +" + (races.length - 1));
    var lvl = params.get("lvl") || "";
    var lo = lvl || params.get("min") || "";
    var hi = lvl || params.get("max") || "";
    if (el("lvl-min").value !== lo) el("lvl-min").value = lo;
    if (el("lvl-max").value !== hi) el("lvl-max").value = hi;
    el("sort").value = params.get("sort") || "name";
    var dir = params.get("dir") === "desc" ? "desc" : "asc";
    el("sort-dir").textContent = dir === "desc" ? "▼" : "▲";
    el("sort-dir").setAttribute("data-dir", dir);

    var list = filterEnemies(params);
    el("enemy-count").textContent = list.length + " of " + DATA.enemies.length + " enemies";
    el("race-banner").innerHTML = races.map(raceBanner).join("");
    el("active-filters").innerHTML = activeChips(params);

    var rows = list.map(enemyRow).join("");
    el("enemy-rows").innerHTML = rows || '<tr><td colspan="4" class="empty">No enemies match — <a href="#" data-nav="#/enemies">clear all filters</a>.</td></tr>';
    lastListHash = hashFor(params);
  }

  function attrTable(mods) {
    var rows = ATTRS.map(function (a) {
      var v = (mods && mods[a[0]]) || 0;
      var cls = v > 0 ? "pos" : v < 0 ? "neg" : "dim";
      return "<tr><td>" + a[1] + ' <span class="dim">' + a[0] + '</span></td><td class="' + cls + '">' + (v > 0 ? "+" + v : v) + "</td></tr>";
    }).join("");
    return '<table class="attr-table"><tbody>' + rows + "</tbody></table>";
  }

  function catChip(e) {
    var link = null;
    if (e.cat === "mg") link = "mg";
    else if (e.cat === "regular") link = "regular";
    else if (e.cat === "superboss") link = "super";
    else if (e.cat === "wonderland") link = "wonderland";
    else if (e.cat === "heroine") link = "heroine";
    var label = CAT_LABELS[e.cat] || e.cat;
    if (link) return '<a class="tag" data-nav="#/enemies?cat=' + link + '">' + label + "</a>";
    return '<span class="tag tag-static">' + label + "</span>";
  }

  function detailTags(e) {
    var t = [catChip(e)];
    t.push('<a class="tag" data-nav="#/enemies?race=' + enc(e.race) + '">' + esc(e.race) + "</a>");
    if (e.race2) t.push('<a class="tag" data-nav="#/enemies?race=' + enc(e.race2) + '">' + esc(e.race2) + "</a>");
    t.push('<a class="tag" data-nav="#/enemies?lvl=' + e.level + '">Level ' + e.level + "</a>");
    t.push('<span class="tag tag-static">HP ' + (e.hp == null ? "—" : e.hp) + "</span>");
    var badges = enemyBadges(e, true);
    if (badges) t.push(badges);
    return t.join(" ");
  }

  function raceCard(race) {
    var r = DATA.races[race];
    var h = '<div class="card"><h3 class="card-title">Race profile: <a class="tag" data-nav="#/enemies?race=' + enc(race) + '">' + esc(race) + "</a></h3>";
    if (!r) return h + '<p class="dim">No racial profile on record for this race.</p></div>';
    var mods = r.mods || {};
    var modTxt = Object.keys(mods).map(function (k) {
      var v = mods[k];
      return '<span class="' + (v > 0 ? "pos" : "neg") + '">' + esc(k) + " " + (v > 0 ? "+" + v : v) + "</span>";
    }).join(" · ");
    h += '<p class="race-line"><span class="lbl">Racial modifiers (applied on top):</span> ' + (modTxt || "none") + "</p>";
    var res = r.res || {}, dmg = r.dmg || {};
    var weak = chipsIf(res, function (v) { return v > 1; });
    var resist = chipsIf(res, function (v) { return v < 1; });
    var strong = chipsIf(dmg, function (v) { return v > 1; });
    if (weak) h += '<p class="race-line"><span class="lbl">Takes extra damage:</span> ' + weak + "</p>";
    if (resist) h += '<p class="race-line"><span class="lbl">Resists:</span> ' + resist + "</p>";
    if (strong) h += '<p class="race-line"><span class="lbl">Deals extra damage:</span> ' + strong + "</p>";
    var biomes = DATA.biomes[race] || [];
    if (biomes.length) h += '<p class="race-line"><span class="lbl">Biomes:</span> ' + biomes.map(esc).join(", ") + "</p>";
    return h + "</div>";
  }

  function mgCard(e) {
    var h = '<div class="card"><h3 class="card-title">' + (e.mg ? "Monster Girl" : "Skills & kit") + "</h3>";
    if (e.growth) h += '<p><span class="lbl">Growth:</span> <strong>' + esc(e.growth) + '</strong> <span class="dim">(late-bloomer attribute pace)</span></p>';
    if (e.skills && e.skills.length) {
      h += '<p class="lbl">Innate skills</p><ul class="plain">' + e.skills.map(function (s) {
        return '<li><a data-nav="#/skills?q=' + enc(s.name) + '">' + esc(s.name) + "</a></li>";
      }).join("") + "</ul>";
    }
    if (e.awakening && e.awakening.length) {
      h += '<p class="lbl">Awakening' + (e.awakened ? " → " + esc(e.awakened) : "") + "</p><ul class=\"plain\">" + e.awakening.map(function (p) {
        return "<li>" + esc(p.from) + ' → <a data-nav="#/skills?q=' + enc(p.to) + '">' + esc(p.to) + "</a></li>";
      }).join("") + "</ul>";
    }
    if (e.mg) h += '<p class="dim">Capturable with a net when weakened (♀). Captured girls join your house.</p>';
    return h + "</div>";
  }

  function heroineCard(e) {
    var name = cap(e.heroine);
    return '<div class="card"><h3 class="card-title">Heroine ally</h3><p>' + esc(name) +
      ' — see the <a data-nav="#/skills?q=' + enc(name) + '">skills wiki</a> for her full kit and enhanced skills.</p></div>';
  }

  function nameOf(key) {
    if (byKey[key]) return byKey[key].name;
    return String(key || "").replace(/_/g, " ").replace(/\b\w/g, function (c) { return c.toUpperCase(); });
  }

  function wlCard(e) {
    var title = e.cat === "wonderland" ? "Wonderland data" : "Resistances & traits";
    var h = '<div class="card"><h3 class="card-title">' + title + "</h3>";
    if (e.res) {
      var weak = chipsIf(e.res, function (v) { return v > 1; });
      var resist = chipsIf(e.res, function (v) { return v < 1; });
      if (weak) h += '<p class="race-line"><span class="lbl">Elemental weakness:</span> ' + weak + "</p>";
      if (resist) h += '<p class="race-line"><span class="lbl">Elemental resistance:</span> ' + resist + "</p>";
    }
    if (e.statusRes != null) h += '<p class="race-line"><span class="lbl">Status resistance:</span> ' + Math.round(e.statusRes * 100) + "%</p>";
    if (e.shadowOf) {
      var target = byKey[e.shadowOf];
      h += '<p class="race-line"><span class="lbl">Shadow of:</span> ' +
        (target ? '<a data-nav="#/enemy/' + enc(e.shadowOf) + '">' + esc(target.name) + "</a>" : esc(nameOf(e.shadowOf))) + "</p>";
    }
    return h + "</div>";
  }

  function renderEnemyDetail(key) {
    var box = el("enemy-detail");
    var e = byKey[key];
    if (!e) {
      box.innerHTML = '<p>Unknown enemy “' + esc(key) + '”. <a data-nav="#/enemies">Back to the enemy database</a>.</p>';
      return;
    }
    var h = [];
    h.push('<a class="back-link" data-nav="' + esc(lastListHash) + '">← Back to the enemy list (with filters)</a>');
    var title = esc(e.name);
    if (e.awakened) title += ' <span class="dim">· awakened as ' + esc(e.awakened) + "</span>";
    h.push("<h1>" + title + "</h1>");
    h.push('<div class="detail-tags">' + detailTags(e) + "</div>");
    h.push('<div class="cards">');
    h.push('<div class="card"><h3 class="card-title">Stats</h3>' + attrTable(e.mods) +
      '<p class="dim">Base HP: ' + (e.hp == null ? "—" : e.hp) + " · Level " + e.level + "</p></div>");
    h.push(raceCard(e.race));
    h.push("</div>");
    var extras = [];
    if (e.mg || e.skills || e.awakening) extras.push(mgCard(e));
    if (e.heroine) extras.push(heroineCard(e));
    if (e.res || e.statusRes != null || e.shadowOf) extras.push(wlCard(e));
    if (extras.length) h.push('<div class="cards">' + extras.join("") + "</div>");
    if (e.super) h.push('<p class="dim">Superboss — you cannot flee from this encounter.</p>');
    box.innerHTML = h.join("");
  }

  // ── sidebar / scrollspy ──
  function buildEnemySidebar() {
    var h = '<div class="toc-title">Browser</div><ul class="toc-list">';
    CATS.forEach(function (c) {
      var href = c[0] === "all" ? "#/enemies" : "#/enemies?cat=" + c[0];
      h += '<li class="toc-l2"><a class="toc-link" data-nav="' + href + '">' + c[1] + ' <span class="dim">' + (COUNTS[c[0]] || 0) + "</span></a></li>";
    });
    h += '</ul><div class="toc-title">Races</div><ul class="toc-list">';
    Object.keys(DATA.races).sort().forEach(function (r) {
      var count = DATA.enemies.filter(function (e) { return e.race === r || e.race2 === r; }).length;
      h += '<li class="toc-l3"><a class="toc-link" data-nav="#/enemies?race=' + enc(r) + '">' + esc(r) + ' <span class="dim">' + count + "</span></a></li>";
    });
    h += "</ul>";
    el("side-enemies").innerHTML = h;
  }

  function refreshSpy() {
    var route = parseHash().route;
    var TEXT_PAGE = {
      home: ["view-home", "side-home"],
      skills: ["view-skills", "side-skills"],
      equipment: ["view-equipment", "side-equipment"],
      effects: ["view-effects", "side-effects"]
    };
    var pair = TEXT_PAGE[route];
    var container = pair ? el(pair[0]) : null;
    spyHeadings = container ? [].slice.call(container.querySelectorAll("h2[id], h3[id]")) : [];
    spyLinks = {};
    var side = pair ? el(pair[1]) : null;
    if (side) {
      [].slice.call(side.querySelectorAll(".toc-link")).forEach(function (a) {
        spyLinks[a.getAttribute("data-target")] = a;
      });
    }
    spy();
  }

  function spy() {
    if (!spyHeadings.length) return;
    var y = window.scrollY + 130;
    var current = spyHeadings[0];
    for (var i = 0; i < spyHeadings.length; i++) {
      if (spyHeadings[i].getBoundingClientRect().top + window.scrollY <= y) { current = spyHeadings[i]; } else { break; }
    }
    Object.keys(spyLinks).forEach(function (k) {
      spyLinks[k].classList.toggle("active", k === current.id);
    });
  }

  var spyQueued = false;
  function queueSpy() {
    if (spyQueued) return;
    spyQueued = true;
    window.requestAnimationFrame(function () { spyQueued = false; spy(); });
  }

  // ── misc page chrome ──
  function setActiveNav(route) {
    var target = route === "enemy" ? "#/enemies" : "#/" + route;
    [].slice.call(document.querySelectorAll(".side-nav a, .topnav a")).forEach(function (a) {
      a.classList.toggle("active", a.getAttribute("data-nav") === target);
    });
  }

  function scrollToId(id) {
    var node = document.getElementById(id);
    if (node) node.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function classifySkills() {
    var root = el("view-skills");
    [].slice.call(root.querySelectorAll("li")).forEach(function (li) {
      var ems = li.querySelectorAll("em");
      if (!ems.length) return;
      ems[0].classList.add("meta");
      if (ems.length > 1) ems[ems.length - 1].classList.add("tags");
    });
    var ELEMENTS = ["Fire", "Water", "Thunder", "Wind", "Earth", "Light", "Dark", "Magical", "Physical"];
    [].slice.call(root.querySelectorAll("li em.meta")).forEach(function (em) {
      var m = em.innerHTML.match(/ · ([A-Za-z]+)\s*$/);
      if (!m || ELEMENTS.indexOf(m[1]) === -1) return;
      em.innerHTML = em.innerHTML.slice(0, m.index) + ' · <span class="el el-' + m[1].toLowerCase() + '">' + m[1] + "</span>";
    });
  }

  function cellKey(cell) {
    if (!cell) return "";
    var t = cell.textContent.trim();
    var num = parseFloat(t.replace(/[^0-9.\-]/g, ""));
    if (/\d/.test(t) && isFinite(num)) return num;
    return t.toLowerCase();
  }

  function makeSortable() {
    [].slice.call(document.querySelectorAll("main table")).forEach(function (table) {
      if (table.classList.contains("enemy-table") || !table.tHead || !table.tBodies.length) return;
      var ths = [].slice.call(table.tHead.rows[0].cells);
      ths.forEach(function (th, idx) {
        th.classList.add("sortable");
        th.title = "Click to sort";
        th.addEventListener("click", function () {
          var dir = th.getAttribute("data-dir") === "asc" ? "desc" : "asc";
          ths.forEach(function (o) {
            if (o !== th) { o.removeAttribute("data-dir"); o.classList.remove("sort-asc", "sort-desc"); }
          });
          th.setAttribute("data-dir", dir);
          th.classList.toggle("sort-asc", dir === "asc");
          th.classList.toggle("sort-desc", dir === "desc");
          var rows = [].slice.call(table.tBodies[0].rows);
          rows.sort(function (a, b) {
            var ka = cellKey(a.cells[idx]), kb = cellKey(b.cells[idx]);
            var cmp = (typeof ka === "number" && typeof kb === "number") ? ka - kb : String(ka).localeCompare(String(kb));
            return dir === "asc" ? cmp : -cmp;
          });
          rows.forEach(function (r) { table.tBodies[0].appendChild(r); });
        });
      });
    });
  }

  function initChrome() {
    if ("scrollRestoration" in history) { history.scrollRestoration = "manual"; }
    el("menu-toggle").addEventListener("click", function () { document.body.classList.toggle("nav-open"); });
    document.addEventListener("click", function (ev) {
      var t = ev.target.closest("[data-nav]");
      if (!t) return;
      ev.preventDefault();
      document.body.classList.remove("nav-open");
      nav(t.getAttribute("data-nav"));
    });
    var toTop = el("to-top");
    window.addEventListener("scroll", function () {
      toTop.classList.toggle("visible", window.scrollY > 600);
      queueSpy();
    }, { passive: true });
    toTop.addEventListener("click", function () { window.scrollTo({ top: 0, behavior: "smooth" }); });
    window.addEventListener("resize", queueSpy);
  }

  // ── routing ──
  function render() {
    var r = parseHash();
    var viewId = r.route === "enemy" ? "view-enemy" : "view-" + r.route;
    var views = ["view-home", "view-skills", "view-equipment", "view-effects", "view-dreams", "view-enemies", "view-enemy"];
    if (views.indexOf(viewId) === -1) { nav("#/home"); return; }
    views.forEach(function (v) { el(v).hidden = v !== viewId; });
    el("side-home").hidden = r.route !== "home";
    el("side-skills").hidden = r.route !== "skills";
    el("side-equipment").hidden = r.route !== "equipment";
    el("side-effects").hidden = r.route !== "effects";
    el("side-dreams").hidden = r.route !== "dreams";
    el("side-enemies").hidden = r.route !== "enemies" && r.route !== "enemy";
    setActiveNav(r.route);

    var anchor = r.params.get("h");
    var q = r.params.get("q");
    window.scrollTo({ top: 0, behavior: "instant" });

    if (r.route === "home") {
      setupTextSearch("view-home", "Search the player guide…");
      if (anchor) { requestAnimationFrame(function () { scrollToId("h-" + anchor); }); }
    } else if (r.route === "skills") {
      setupTextSearch("view-skills", "Search skills…");
      if (q) {
        el("search").value = q;
        runTextSearch(q);
        requestAnimationFrame(jumpToFirst);
      } else {
        el("search").value = "";
        if (anchor) { requestAnimationFrame(function () { scrollToId("s-" + anchor); }); }
      }
    } else if (r.route === "enemies") {
      setupFilterSearch();
      renderEnemies(r.params);
    } else if (r.route === "enemy") {
      setupFilterSearch();
      renderEnemyDetail(r.arg);
    } else if (r.route === "equipment") {
      setupTextSearch("view-equipment", "Search equipment…");
      el("search").value = "";
      if (anchor) { requestAnimationFrame(function () { scrollToId("e-" + anchor); }); }
    } else if (r.route === "effects") {
      setupTextSearch("view-effects", "Search buffs & debuffs…");
      el("search").value = "";
      if (anchor) { requestAnimationFrame(function () { scrollToId("x-" + anchor); }); }
    } else if (r.route === "dreams") {
      setupTextSearch("view-dreams", "Search dreams…");
      el("search").value = "";
      if (anchor) { requestAnimationFrame(function () { scrollToId("d-" + anchor); }); }
    }
    refreshSpy();
  }

  // ── init ──
  initSearchBox();
  initEnemiesView();
  buildEnemySidebar();
  classifySkills();
  makeSortable();
  initChrome();
  window.addEventListener("hashchange", render);
  render();
})();
"""

PAGE_TEMPLATE = string.Template("""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="dark">
<title>$title</title>
<style>$css</style>
</head>
<body>
<a class="skip-link" href="#/home">Skip to content</a>
<header class="topbar">
  <button id="menu-toggle" type="button" aria-label="Toggle contents">☰</button>
  <a class="brand" data-nav="#/home">Pandemonium <span>Wiki</span></a>
  <nav class="topnav">
    <a data-nav="#/home">Player Guide</a>
    <a data-nav="#/skills">Skills</a>
    <a data-nav="#/enemies">Enemies</a>
    <a data-nav="#/equipment">Equipment</a>
    <a data-nav="#/effects">Effects</a>
    <a data-nav="#/dreams">Dreams</a>
  </nav>
  <span class="topbar-spacer"></span>
  <div class="search-box">
    <input id="search" type="search" placeholder="Search…  ( / )" autocomplete="off" spellcheck="false">
    <span id="search-count"></span>
    <button id="search-prev" class="search-btn" type="button" title="Previous match (Shift+Enter)">↑</button>
    <button id="search-next" class="search-btn" type="button" title="Next match (Enter)">↓</button>
  </div>
</header>
<div class="layout">
<nav class="sidebar" id="sidebar" aria-label="Wiki navigation">
  <div class="side-nav">
    <a data-nav="#/home">🏰 Player Guide</a>
    <a data-nav="#/skills">⚔️ Skills Wiki</a>
    <a data-nav="#/enemies">👹 Enemy Database</a>
    <a data-nav="#/equipment">🧪 Equipment</a>
    <a data-nav="#/effects">✨ Buffs & Debuffs</a>
    <a data-nav="#/dreams">🌙 Dreams</a>
  </div>
  <div id="side-home" class="side-context" hidden>
    <div class="toc-title">On this page</div>
    $toc_home
  </div>
  <div id="side-skills" class="side-context" hidden>
    <div class="toc-title">On this page</div>
    $toc_skills
  </div>
  <div id="side-equipment" class="side-context" hidden>
    <div class="toc-title">On this page</div>
    $toc_equipment
  </div>
  <div id="side-effects" class="side-context" hidden>
    <div class="toc-title">On this page</div>
    $toc_effects
  </div>
  <div id="side-dreams" class="side-context" hidden>
    <div class="toc-title">On this page</div>
    $toc_dreams
  </div>
  <div id="side-enemies" class="side-context" hidden></div>
</nav>
<main id="content">
  <section class="view" id="view-home" hidden>$body_home</section>
  <section class="view" id="view-skills" hidden>$body_skills</section>
  <section class="view" id="view-equipment" hidden>$body_equipment</section>
  <section class="view" id="view-effects" hidden>$body_effects</section>
  <section class="view" id="view-dreams" hidden>$body_dreams</section>
  <section class="view" id="view-enemies" hidden>
    <h1>Enemy Database</h1>
    <p class="page-sub">Every enemy in Pandemonium — click a row for details, its skills, awakening kit, and racial profile. Clicking a race, level, or category tag on a detail page brings you back here with that filter applied.</p>
    <div class="filterbar">
      <div class="chips" id="cat-chips"></div>
      <div class="filter-row">
        <div class="multiselect" id="race-multi">
          <button id="race-btn" class="ms-btn" type="button" aria-haspopup="true" aria-expanded="false">Race <span class="dim" id="race-btn-label">All</span></button>
          <div class="ms-panel" id="race-panel" hidden>
            <div class="ms-actions">
              <span class="dim">Pick any number — matches any chosen race (OR)</span>
              <button id="race-clear" class="ms-mini" type="button">Clear</button>
            </div>
            <div id="race-options"></div>
          </div>
        </div>
        <span class="fld">Level</span>
        <input id="lvl-min" type="number" min="1" placeholder="min" aria-label="Minimum level">
        <span class="fld">–</span>
        <input id="lvl-max" type="number" min="1" placeholder="max" aria-label="Maximum level">
        <span class="fld">Sort</span>
        <select id="sort" aria-label="Sort by">
          <option value="name">Name</option>
          <option value="level">Level</option>
          <option value="hp">HP</option>
          <option value="race">Race</option>
        </select>
        <button id="sort-dir" class="sort-dir" type="button" title="Toggle sort direction">▲</button>
        <span class="count-note" id="enemy-count"></span>
      </div>
      <div class="active-filters" id="active-filters"></div>
    </div>
    <div id="race-banner"></div>
    <div class="table-wrap">
      <table class="enemy-table">
        <thead><tr><th>Enemy</th><th>Race</th><th>Lv</th><th>HP</th></tr></thead>
        <tbody id="enemy-rows"></tbody>
      </table>
    </div>
  </section>
  <section class="view" id="view-enemy" hidden><div id="enemy-detail"></div></section>
  <footer class="page-footer">Sources: <code>README.md</code> · <code>docs/dreams_wiki.md</code> · <code>docs/monster_girls_skills_wiki.md</code> · <code>resources/enemies/enemies_data/*.yaml</code> · <code>resources/item_generation.py</code> · <code>resources/items.py</code> · <code>combat/status_effects.py</code> · $footer_note</footer>
</main>
</div>
<button id="to-top" type="button">↑ Top</button>
<script>window.WIKI_DATA = $data;</script>
<script>$js</script>
</body>
</html>
""")


# ── site assembly ───────────────────────────────────────────────────────────

def build_site(out_path=None, footer_note=None):
    """Build the standalone wiki site. Returns the output path."""
    out_path = os.path.abspath(out_path or OUT_HTML)

    with open(README_MD, encoding="utf-8") as f:
        readme = f.read()
    with open(DREAMS_MD, encoding="utf-8") as f:
        dreams_wiki = f.read()
    with open(SKILLS_MD, encoding="utf-8") as f:
        skills = f.read()

    home_body, home_toc = parse_markdown(readme, "h-", "#/home?h=")
    dreams_body, dreams_toc = parse_markdown(dreams_wiki, "d-", "#/dreams?h=")
    skills_body, skills_toc = parse_markdown(skills, "s-", "#/skills?h=")
    equipment_body, equipment_toc = parse_markdown(build_equipment_markdown(), "e-", "#/equipment?h=")
    effects_body, effects_toc = parse_markdown(build_effects_markdown(), "x-", "#/effects?h=")

    enemies = list(load_enemy_data().values())
    _enrich_enemies(enemies)
    skills_body = _linkify_skill_roster(skills_body, enemies)

    enemy_races = _load_py_dict(os.path.join(ROOT, "resources", "enemies", "enemy_races.py"), "ENEMY_RACES")
    biome_races = _load_py_dict(os.path.join(ROOT, "resources", "enemies", "biome_races.py"), "BIOME_RACES")
    races = {
        name: {
            "mods": r.get("mods", {}),
            "res": r.get("elemental_res", {}),
            "dmg": r.get("elemental_dmg", {}),
        }
        for name, r in enemy_races.items()
    }
    biomes = {}
    for biome, race_list in biome_races.items():
        for race in race_list:
            biomes.setdefault(race, []).append(biome)

    data_json = json.dumps(
        {"enemies": enemies, "races": races, "biomes": biomes},
        ensure_ascii=False,
        separators=(",", ":"),
    ).replace("</", "<\\/")

    page = PAGE_TEMPLATE.substitute(
        title="Pandemonium Wiki",
        css=PAGE_CSS,
        js=PAGE_JS,
        toc_home=render_toc(home_toc, "#/home?h="),
        toc_skills=render_toc(skills_toc, "#/skills?h="),
        toc_equipment=render_toc(equipment_toc, "#/equipment?h="),
        toc_effects=render_toc(effects_toc, "#/effects?h="),
        toc_dreams=render_toc(dreams_toc, "#/dreams?h="),
        body_home=home_body,
        body_skills=skills_body,
        body_equipment=equipment_body,
        body_effects=effects_body,
        body_dreams=dreams_body,
        data=data_json,
        footer_note=footer_note or "Built with <code>tests/gen_wiki_html.py</code>",
    )

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(page)

    cats = {}
    for e in enemies:
        cats[e["cat"]] = cats.get(e["cat"], 0) + 1
    print(f"Wrote {out_path}")
    print(f"  enemies embedded: {len(enemies)}  ({', '.join(f'{k}: {v}' for k, v in sorted(cats.items()))})")
    print(f"  guide headings:   {len(home_toc)}   skill headings: {len(skills_toc)}")
    print(f"  equipment headings: {len(equipment_toc)}   effect headings: {len(effects_toc)}")
    print(f"  dream headings:     {len(dreams_toc)}")
    return out_path


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build the standalone Pandemonium wiki site.")
    parser.add_argument("--out", default=OUT_HTML, help="output HTML path (default: wiki/index.html)")
    args = parser.parse_args(argv)
    build_site(args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
