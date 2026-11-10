# Fireside Tales — House Stories Design

**Status:** Implemented 2026-10-27 (v0.1.8.3 content patch).
**Runtime:** `facilities/house_stories.py` · **Data:** `resources/house_stories.py`.

A house is a building until something happens in it. Fireside Tales is a
storybook in the house menu: multi-part side stories about the household,
gated by who lives there and how close you are. Some threads find the player
while travelling instead of waiting at home.

## 1. Player experience

- The house menu gains **Fireside tales** (with a `(N ready)` badge).
- Each arc lists its next part, a lock reason, a "waits in …" hint, or
  `✓ complete (re-read)`.
- Reading a part marks progress, applies small effects, writes a
  `[STORY]` Journal event, and saves immediately.
- Completed arcs remain re-readable from the house — no effects on replay.
- Story reading uses the existing `term` facility I/O, so it works in the
  house facility thread and in a city `StoryScreen` overlay.

## 2. Requirements (locked)

Per-arc and per-part gates are merged (the stricter numeric value wins):

| Key | Meaning |
|---|---|
| `girls` | distinct owned girls at/above `affection` |
| `affection` | affection threshold for the counted girls / featured / designated girls |
| `girl` | featured girl key (must be owned) |
| `girl_keys` | designated allies (list) that must all be owned; affection applies to each |
| `married` | married companions required |
| `house_level` | highest owned house level |
| `flags` | quest flags (checks quest flags **and** top-level story flags) |
| `superbosses` | superboss ids that must be defeated (`defeated_superbosses` or per-boss flag) |

Roster = active party + every owned house's `monster_girls` + Wonderland
benched allies, deduplicated by `key:name`. All effects mutate the live
records, so affection/stress changes show up immediately in the Lounge.

Parts are read strictly in order: a part is available only when every
earlier part of the same arc is in `player["house_stories"]["seen"]`.

## 3. Triggers

Default: read from the house menu. A part may also carry:

```python
"trigger": {"type": "city", "city": "skylume"}          # city id or "any"
"trigger": {"type": "city", "city": "any", "phase": "night"}
```

On city entry, `gui/screens/city_screen.py::_check_story_beats` first
delivers queued quest beats, then calls
`facilities.house_stories.claim_city_trigger(player, city_id)`. The first
eligible unseen triggered part opens as a `StoryScreen` overlay. Progress is
marked at the start of `play_part` (early-close safe), so a closed window
never re-triggers the same part.

City-triggered parts that were not delivered (wrong city/phase, or a quest
beat took priority) remain visible in the house storybook with a
`waits in …` / `waits for …` hint.

### Superboss-gated stories

Stories can also wait on a kill rather than a place. `"superbosses":
["chromatic_artisan"]` unlocks the arc once that boss is defeated. The
runtime accepts either the shared `player["defeated_superbosses"]` ledger
or the boss's own top-level flag (`boss_defeated_palette`,
`boss_defeated_white_knight`, Wonderland flags, …), so old saves work. The
story then appears in the house book — the same "read at home" flow as any
other arc.

## 4. Effects

Effects are intentionally social, not combat power:

| Effect | Behaviour |
|---|---|
| `affection` | featured girl, the designated `girl_keys`, or all qualifying girls |
| `affection_all` | every girl meeting the part's affection threshold |
| `stress` | negative relaxes; same targets as affection |
| `gold` | added to the player |
| `xp` | `leveling.gain_exp` (shared reward API) |
| `items` | `resources.items.build_item` + `inventory.add_item_to_inventory` |

Affection clamps at `affection_cap` (100, or 200 for engaged/married girls).
Stress clamps to 0–100.

## 5. Shipped arcs

| Arc | Gate | Parts | Notes |
|---|---|---|---|
| **The Lucky Coin** | Goblin Girl, affection 30 → 60 → 90 | 3 | Romance arc; coin as a luck-vs-choice motif. |
| **Wind at the Window** | Harpy Scout, affection 40 → 70 | 2 | A scout with no nest; roof perch and a dawn flight. |
| **Hoof and Wing** | Harpy Scout **and** Centaur Scout, both 50+ → 70+ | 2 | Designated pair arc; shared watches and different horizons. |
| **A Shape of Her Own** | Slime Girl, affection 35 → 65 | 2 | A slime who copies everyone chooses her own shape. |
| **Small Hours** | 3 girls at 40+, house Lv2; escalates to 4/50 and 5/60, Lv3 | 3 | Ensemble household arc; names on the mantel. |
| **A Moth at the Window** | 2 girls at 40+, `met_voss` | 3 | Part 1 triggers on entering **Skylume**; parts 2–3 read at home. |
| **The Eighth Color** | Defeat **Palette, the Chromatic Artisan**; house Lv2; parts 2–3 need Palette recruited (affection 60 → 100) | 3 | Superboss aftermath + Palette household interaction. |
| **The Last Oath** | Defeat the **White Knight**; 2 girls at 40+ → 3 at 50+ | 2 | A shield arrives at the door; the household keeps the watch. |

## 6. Save compatibility

- New field: `player["house_stories"] = {"seen": {part_id: day}}`.
- Seeded in `character.build_character` and
  `character.ensure_player_fields` (`.setdefault`), so old saves load cleanly.
- No migration is needed: an empty `seen` map simply starts every arc at
  part 1. Progress is monotonic (part ids are only ever added).
- Journal events use the existing `events` list with the `[STORY]` tag; no
  Journal schema change.

## 7. Verification

`tests/_diag_house_stories.py` covers state seeding, roster dedupe,
requirement gates (affection, featured girl, designated allies, house
level, superboss evidence), effect targeting/clamps, city-trigger
eligibility, play/replay idempotency, readiness badges and data integrity
(unique part ids, non-empty prose).

Run:

```
.venv\Scripts\python.exe tests\_diag_house_stories.py
```

## 8. Phase 2 backlog

- More per-girl arcs (Kobold Tinkerer, Moth Girl Flutterer, Ghost Maid, …)
  and a marriage-gated epilogue arc.
- Pair/trio arcs for other designated ally combinations (the `girl_keys`
  gate is already generic).
- Trigger types beyond city entry (dungeon floor clear, day phase already
  supported in the trigger schema but unused by shipped content).
- Story rewards that unlock decor / a mantel trophy or a small permanent
  house perk — must respect the economy rules before adding anything
  mechanical.
- Per-arc completion flags for future quest/bestiary/journal cross-links.
