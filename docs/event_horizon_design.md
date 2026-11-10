# Event Horizon — Infinite Dungeon Design & Implementation Plan

Status: **Phases 1–5 DONE (2026-10-06).**
Scope: A room-based, endless mid-endgame dungeon ("Event Horizon") accessed from a
permanent world-map site (unlocks once Floor 20 is **cleared**, `max_floor ≥ 21`).
Runs are endless until
death or quitting; enemy scaling and party **Entropy** rise with room count;
**flasks** grant permanent-per-run single-actor buffs; **trial rooms** at 5-room
milestones force enemy handicap cards (every 20th room milestone: a positive team
card instead). Inside, **XP is frozen and enemies drop nothing** — loot comes
from an end-of-run **gold payout** (scaled by rooms cleared × Entropy weight),
a run-only currency (**Horizon Motes**, wiped on run end), flasks, and
milestone rewards (high-tier flasks, deep boons, unique trophies).

Decision log from planning session 2026-10-06 (user-confirmed):

**Phase 1 (done 2026-10-06):** `event_horizon.py` core (state, constants,
scaling math, flask/card rolls + application, Entropy, battle-start debuffs,
payout math, milestone schedule, wipe/strip); formal `weapon_type` pass on all
51 weapons; three trophy items + `combat/weapon/` modules
(`piece_of_relationship.py`, `chance_and_choice.py`, `dopo_robe.py`); hooks in
`combat/stats` (enemy scaling + Entropy reads), `combat/elemental`
(`eh_ele_dmg`), `combat/enemy_ai` (rift regen + POR mark), `combat/combat_engine`
(battle-start + POR battle cleanup), `leveling` (XP freeze guard), `character`
(defaults), `save_load`/`utils` (scrub + deferred death payout),
`combat/ally.equip_ally_item` (`player_only` guard). Tests:
`tests/test_event_horizon.py` (19 passed) + `tests/_diag_eh_phase1.py`; full
suite 126 passed + 60 subtests, no regressions.

Phase 1 implementation deviations (recorded):
1. Permanent actor buffs use `remaining: 9999` + strip-on-run-end instead of
   tick-skip edits — the status-effect tick routines are **unchanged**.
2. `curse` is excluded from the Entropy battle-start pool (it is indefinite
   and would stack forever); the other 10 pool types ship as specced.
3. `apply_death_penalty` scrubs `_eh_in_run` and pays the deferred payout;
   the run wipe itself is the Phase 2 loop's exit responsibility.
4. POR battle buffs apply in the standard combat engine only — identical
   coverage to the wedding combat-start effects; superboss loops untouched.

**Phase 2 (done 2026-10-06):** `event_horizon_rooms.py` (weighted room
generation with trial interleaving, combat/flask flow, trial + deep-boon card
choice rendered through the shared `_tmenu` bridge, mote shop with free visit
flask + Tune-Up, mote event, still-pool healing, milestone grants with
pending-trophy retry queue, post-room menu) + `dungeon.py`
`_explore_event_horizon()` loop (per-room checkpoints via `save_game`, exits
`dead` / `eh_quit` / `save_exit` / `timeout`, floor snapshot/restore,
well_rested parity, no XP/drops/bounty calls). Combat flee is disabled in-rift
(`player_actions`). `beating_root` item def added (use-effect = Phase 5).
Suspend resumes at the **next room** — save & quit only exists between rooms,
so no mid-room snapshots are needed (`current_room` stays a defensive field).
Tests: `tests/_diag_eh_run.py` (6 scenarios: suspend/abandon/death/trial/
milestones/shop); full suite 126 passed + 60 subtests.

---

## 0. Decision log (locked 2026-10-06)

1. **Name:** Event Horizon.
2. **Entry:** permanent **world-map site** (a space-time distortion). Unlock gate:
   **Floor 20 cleared** (`max_floor ≥ 21` — reaching floor 20 and failing its
   superboss does **not** unlock it; fixed 2026-11-07). An NPC — the **Horizon
   Watcher** (name TBD) — greets the
   party at the site and explains the distortion; entering, resuming, and
   abandoning runs all happen there. No spawn/expiry cycle — the site never
   disappears once unlocked.
3. **Room-based, not floor-based.** One room is generated at a time; each cleared
   room increments the counter. There are no floors, no boss floors, no
   superboss scheduling, no Pandemonium curses, no Wonderland systems.
4. **Scaling:** enemies gain stats per room (§2.2); the party accumulates
   **Entropy** stacks as progress (§2.3). Both visible in the HUD + inventory.
5. **Flask:** after **every room clear** and at **every shop**, one flask with a
   random buff (tier 1–7) is offered. The player selects a flask and then picks
   **exactly one actor** (MC or an ally) to drink it. The buff is **permanent for
   the run** and benefits only that actor — "feed the damage dealer, or balance
   buffs across the team." Tiers scale with depth; magnitudes are small because
   supply is infinite (§3).
6. **Trial rooms:** after clearing any room where `room % 5 == 0 and room >= 10`,
   the **next room is a Trial** and **does not count as progress** (sequence:
   … r10 → trial → r11 … r15 → trial → r16 … r20 → trial → r21 …).
   The trial offers **3 random cards; the player must pick 1**:
   - Normally: **enemy handicap cards** (status res up, dmg up, hp up,
     ele dmg up, regen passive, …) — persist for the rest of the run.
   - When the just-cleared room was a multiple of 20: a **positive team buff
     card** instead — persists for the rest of the run.
7. **Run end:** death (standard death flow) **or** quitting (flee/abandon) ends
   the run — run state, cards, flasks, and motes are wiped. **Save & quit
   suspends** the run (resumable from the site). Suspended state lives in the
   save JSON.
8. **Currency:** **Horizon Motes** (◎ — name locked). Earned inside, only
   spendable inside (Event Horizon shops), wiped when the run ends.
9. **Rewards:** payout, milestones, and trophy item designs locked (§10);
   future trophies beyond r100 TBD. `best_room` persists across runs.
10. **GUI:** DungeonScreen gets a third branding branch (room counter + motes in
    the top bar); the inventory screen gets a conditional **Event Horizon tab**
    (per-actor flask buffs + face-up positive/negative cards); HUD tags show
    Entropy and the stacked run-bonus totals.
11. **XP frozen / no drops.** No character XP, no per-kill gold, and no item
    drops inside the Event Horizon. The only loot channels are the run gold
    payout, motes, flasks, and milestone rewards (§10).
12. **Run gold payout — full, any outcome.** Paid when the run ends (death,
    quit, interrupt), computed from rooms cleared × **Entropy weight**. Picking
    the mild trial card keeps Entropy lower → less pressure now but a smaller
    payout (and vice versa). On death the payout is **exempt from the 20% death
    toll** (granted after it — §6.2/§10.2).
13. **Entropy variety.** Negative trial cards add Entropy by severity cost
    (T1/T2/T3 = +2/+4/+6); every Event Horizon combat begins with a random
    debuff inflicted on **every active party member**, tiered by current Entropy
    (§2.4).
14. **Milestones:** every 25 rooms → guaranteed tier 6–7 flask; every 50 rooms →
    **deep boon** (pick 1 of 3 positive team cards). **Trophy items** (one-time,
    granted mid-run, run continues): r50 → **Chance and Choice**, r75 →
    **Old Dopo Robe**, r100 → **Piece of Relationship** (full effect on
    acquisition; scales with how many owned allies sit at 200 affection —
    §10.5). **Beating Root** drops at every 25-room milestone past r100
    (r125, r150, …): a consumable trophy — each copy permanently opens the
    **consuming actor's own 3rd accessory slot** (§10.6). Every unique equipment
    gets an **Examine** button + lore.
15. **Superbosses:** none can *spawn* in the Event Horizon — closed and
    final. Sole exception (locked 2026-10-12): the player-invoked **Boss
    Rush** (§6.4) — an arrival-scene offer that replays overworld-felled
    superbosses as flat-scaled "echoes" behind minimum-progress gates.
    🚧 **WIP — under review (2026-10-14):** the rush→fight connection needs
    a review pass.
16. **Card selection UI:** terminal = text menu with full card details; GUI =
    the same choices as buttons (standard `term.menu` bridge).
17. **Horizon Watcher appearance:** a man in a robe whose head is a **black
    hole**; he speaks normally, but his voice **echoes** (name still open).
18. **`weapon_type` field:** every weapon gains a formal `weapon_type`
    (sword, blade, greatsword, axe, bow, …). The robe checks for `blade`
    specifically — and this field becomes the foundation for future
    weapon-synergy mechanics.
19. **Capture enabled** inside the Event Horizon (normal capture rules); the
    flask system is **approved as designed** (any owned ally, incl. reserve,
    may be chosen as the drinker).
20. **Bounty progress is disabled** inside the Event Horizon (locked — infinite
    kills would farm bounties).
21. **First contact — Vesper Erebus:** once **Floor 20 has been cleared**
    (`max_floor ≥ 21`, `eh_intro_seen` unset), the Horizon Watcher **Vesper
    Erebus** greets them in an NPC scene using the Archivist-Voss-style UI,
    explains the distortion, and reveals the site on the world map (Phase 3).
22. **Enemy spawns (2026-10-06, second playtest — locked):** flat start —
    room 1 always spawns the **lv20 band**, +1 level per 3 rooms, **cap 56**
    (the game's max regular-enemy level — the old cap of 80 emptied the pool
    band and silently fell back to mixed trash), **independent of
    `max_floor`** (anchoring r1 to deepest-floor spawned 500+ HP packs on
    deep saves). In-run difficulty is **frozen at ×1.4** (dusk baseline,
    Pandemonium parity) so runs don't swing with the real-world clock. All
    races spawn (no region filter); bosses, superbosses, minions, shadow
    copies, heroines and Wonderland-storybook enemies stay excluded. Full
    spec §2.1.
23. **Band widening at capped depth (2026-10-06, locked):** the spawn band's
    lower edge never rises past **lv30** (`EH_ENEMY_BAND_FLOOR`, threaded to
    the picker as its `band_lo` override) — at the lv56 cap the pool spans
    **lv30–59** (94 templates) so weak stragglers still spawn for variety and
    breathing room (weakest roll ~414 HP at r109 vs ~2123 with the narrow
    band; still scales with room multipliers).
24. **Second playtest refinements (2026-10-06, locked):** **Entropy
    Afflictions** — every 10 stacks Entropy gains one random distinct
    affliction type (Persistent, shown in the inventory tab); rift battles
    open with debuffs drawn ONLY from the acquired set, and there is no
    battle-start pressure before the first affliction („like negative cards
    but random and more merciful“). Combat top bar + round headers show
    `⚔ The Event Horizon | Room N` (no floors/levels). Flask menu shows each
    actor's owned-flask tally. Rift enemies show `TRL×N` for trial burdens
    (with the active burden effects — item 27).
    Inventory EH tab gains IN RUN / SUSPENDED banners and a post-run history
    stub (best room).
25. **Effect detach/restore (2026-10-06, third playtest — locked):** rift
    buffs/debuffs apply ONLY while inside the run. Suspend/interrupt paths
    detach them from the roster (data stays in run state); entry
    re-attaches; `load_game` strips baked-in entries. Fixes the ENT tag /
    flask buffs leaking onto city screens after exiting, and closes the
    cross-content power exploit.
26. **Vesper idle dialogue (2026-10-06, locked):** arrival-scene greetings
    depend on story context — first arrival, rotating re-entry idle lines,
    and a one-time line the first time each 25-room mark is reached
    (r25/r50/r75/r100/r125+), acknowledged once per save via
    `eh_vesper_milestone` (see §6.1).
27. **HUD tag stacking + trial detail (2026-10-06, locked):** the party HUD
    sums permanent Event-Horizon run bonuses (flasks, positive cards,
    Tune-Up) per effect type into one tag — `DMG+37%` instead of six `DMG+…`
    tags; temporary ally-skill buffs (Frabjous Day, Fate's Favor) stay
    individual. Rift enemies' `TRL×N` now lists what the trial burdens do
    (`TRL×5: HP+20% DMG+9% …`) via `trial_burden_tags`.
29. **Balance pass 1 (2026-10-07, r83 playtest feedback — locked):** (a) room
    curves cut: HP 0.025→0.018, DMG 0.020→0.013, DEF 0.015→0.010 per room
    (§2.2); (b) deck rule — trial/boon cards never stack, owned kinds return
    only as upgrades that replace them, taken ladders leave the deck which
    exhausts (§4.2), positive trials every 15 rooms; an empty deck passes
    the trial with motes and no burden; (c) Entropy stat bite now −3% per
    full 20 stacks (cap −45% at 300), battle-start rolls unchanged (§2.3);
    (d) Vitality flasks heal % max HP per round (0.5%→2% by tier); (e) one
    shop ware per visit is 40% off; (f) Tarnished Jade untouched (its Wedge
    Backlash halving is an accepted build-vs-rift trade-off) — the crit note
    in §3.2 was corrected (cap is 100% with overflow→crit damage).
30. **T4 ladders + the Joker (2026-10-07, locked):** trial/boon decks gained
    a **T4** step per kind (6 kinds × 4 tiers = 24 per deck; T4 reachable
    only via upgrade, entropy +8) because the no-stacking ladder exhausted
    by ~r130; and every rn+25 offers **the Joker** — +10% damage dealt,
    +5% damage taken, party-wide, run-long, **skippable**, off-deck (no
    Entropy / no payout), both events when it coincides with a milestone
    (§4.3). No special cap on Mending Roil: the one-tier-per-kind rule
    bounds it at T4 (5%/turn).
31. **Deck semantics corrected (2026-10-07, supersedes items 29b/30a):** each
    (kind, tier) is a UNIQUE card; **same-kind cards at different tiers
    stack** (effects add — Mending Roil spans 2+3+4+5 = 14%/turn, uncapped by
    design); exact duplicates never repeat; tiers unlock by depth (T1–T4, T4
    from r45) so an unpicked low tier can surface late; decks exhaust when
    all eligible cards are claimed; migration collapses only exact
    duplicates. The Joker grew to a **3-card pool** (Edge / Warden /
    Gambler — one dealt at random per rn+25; Warden's drawback is a negative
    `damage_boost` entry in `active_buffs`).
28. **Rift quality-of-life (2026-10-07 playtest — locked):** (a) the dungeon
    screen's Party Status panel updates during Event Horizon runs (at run
    start, each room entry, and after every cleared room); the (mapless) Map
    panel is relabeled **Rift** and shows `render_event_horizon_status`
    (room/best, motes, Entropy + next affliction, next trial, next flask
    milestone); (b) choice menus render every button the same size (uniform
    invisible focus ring + `sticky="nsew"` row-stretch — the focused first
    option no longer renders bigger); (c) the rift merchant sells **flasks
    instead of random items** — three kinds, grade scales with room
    progress, price by grade; (d) Tune-Up/Might stat bonuses stack and the
    HUD shows the summed total (`ALL+3`).

---

## 1. Data model

### 1.1 `player["event_horizon"]` (persistent; JSON-safe)

```python
{
    "run_active":   False,        # suspended or in-progress run exists
    "room":         0,            # last cleared room number (progress only)
    "current_room": None,         # pending room snapshot for suspend/resume (§1.2)
    "pending_flask": None,        # unconsumed flask awaiting a drinker (defensive)
    "actor_flasks": {},           # {actor_key: [flask buff records]} — display log
    "positive_cards": [],         # [card dicts] — team cards, persist for run
    "negative_cards": [],         # [card dicts] — enemy handicaps, persist for run
    "motes":        0,            # Horizon Motes (wiped on run end)
    "entropy":      0,            # current Entropy stacks
    "best_room":    0,            # persists ACROSS runs (never wiped)
    "origin_city":  "solmere",    # return city for exits (nearest to the site)
    "started_day":  0,
}
```

- Actor key: `"player"` for the MC; allies use the house-style stable key
  `f"{key}:{name}"` (mirrors `_girl_unique_id`). Never key by display name.
- Buff *effects* live on the actors themselves (`active_buffs` / `active_debuffs`
  entries marked `"source": "event_horizon"`, `"permanent": True`) — the run
  state only keeps the display log + card records. Runtime reads use the actor
  entries (so existing damage/defense/stat read sites keep working — §7).
- Managed by `event_horizon.ensure_eh_state(player)` (pattern:
  `wild_dungeons.ensure_wild_dungeon_state`); called from
  `character.build_character` + `ensure_player_fields`, and defensively at every
  access point.

### 1.2 Room snapshot (`current_room`)

```python
{
    "number": 11,                       # the room number it WILL become
    "type":   "combat" | "shop" | "event" | "trial_neg" | "trial_pos",
    "enemies": [...],                   # combat only (enemy keys)
    "trial_cards": [...],               # trial only (rolled 3-card offer)
    "entropy_applied_at": 10,           # bookkeeping for resume
}
```

Suspend keeps `current_room` as-is; resume re-enters it without re-rolling.
Room state is snapshot-safe: no RNG replay on load.

---

## 2. Progression

### 2.1 Room loop

- After each clear: check trial trigger (§4) → else generate the next room.
- Room type weights (v1, tunable): **combat 70%**, **shop 12%**,
  **mote event 10%** (no item treasures — nothing drops inside, §10),
  **fountain/rest 8%**.
- Combat pack size: `randint(max(2, pack-1), pack)` where
  `pack = 2 + min(3, room // 12)` (r1–11 → 2–3 enemies, r12+ → 3, r24+ → 4,
  r36+ → 5).
- **Enemy spawn level — flat start (locked 2026-10-06, second playtest):**
  `lvl = clamp(20 + (room − 1) // 3, 1, 56)` — r1–3 always spawn the lv20
  band (+1 per 3 rooms: lv50 at r91, **lv56 cap at r109**), **decoupled from
  `max_floor`**. 56 = the game's maximum regular-enemy level: bands above it
  empty out (the generic picker then silently falls back to *any* enemy,
  mixing low-tier trash into deep rooms — the old lv80 cap had this bug).
  Past the cap the per-room multipliers carry the infinite pressure.
  Anchoring r1 to the player's deepest floor spawned 500+ HP enemies for
  deep saves (band 48–63 → `base_hp` 410–820); the flat ramp gives every
  save the same warm-up and climbs past the player's home depth in
  `3 × (max_floor − 20)` rooms. Enemy level picks the pool band **only**
  — HP comes from each template's `base_hp` (§2.2), it does not grow with
  level.
- **Band widening at capped depth (locked 2026-10-06):** the picker band's
  lower edge never rises past **lv30** — `enemy_band_for_room()` returns
  `(level, band_lo)` with `band_lo = min(30, level − (6 + level//10))`, passed
  to `get_random_enemy_key(..., band_lo=...)`. Widening starts ~r58 and at
  the lv56 cap the pool spans **lv30–59 → 94 templates** (`base_hp` 80–820):
  weak stragglers ride along with elites (weakest effective HP ~414 at r109,
  ~669 at r200, ~1229 at r400 — the floor still climbs with the room
  multipliers). Variety + breathing room at cap depth.
- **Difficulty freeze (locked 2026-10-06):** time-of-day/daily difficulty is
  frozen at the dusk baseline **×1.4** (`EH_TIME_DIFFICULTY`, Pandemonium
  parity) for the whole run — enemy HP no longer swings 1.0–1.8 with the
  real-world clock. Full Moon's +20% still applies (Pandemonium parity).
- Enemy pool uses **no region filter** — the distortion pulls from everywhere
  (`get_random_enemy_key(level, boss=False, region=None, player=player)`):
  all races (Beast, Demon, Abomination, Shadow, Undead, Dragonkin, Giant,
  Angel, Vampire, Clockwork, Construct, Fey, Gnome, Elemental, …). Excluded:
  bosses, superbosses, minion-only enemies, shadow copies, heroines, and
  Wonderland-storybook enemies (existing filter).
- No superboss spawns (final — none can spawn in the Event Horizon), no
  curses/quirks/shadows. Sole exception: the player-invoked **Boss Rush**
  (§6.4) replays already-felled overworld superbosses as flat-scaled echoes.
  **Capture is enabled** under normal rules; the flask system is approved as
  designed.

### 2.2 Enemy scaling (constants in `event_horizon.py`)

Applied inside `combat/stats.enemy_stats()` via the rift hook (§7) to every
enemy spawned during an active in-run session:

| Stat | Per-room growth | At r=25 | At r=50 | At r=100 |
|---|---|---|---|---|
| HP | `×(1 + 0.018·(room−1))` | ×1.43 | ×1.88 | ×2.78 |
| STR (dmg) | `×(1 + 0.013·(room−1))` | ×1.31 | ×1.64 | ×2.29 |
| CON / DEX | `×(1 + 0.010·(room−1))` | ×1.24 | ×1.49 | ×1.99 |

Curves cut in the 2026-10-07 balance pass (was 0.025 / 0.020 / 0.015 — the
compounding outran every party growth source). Negative trial cards multiply
on top of this (§4.2 — no stacking since 2026-10-07). All constants tunable.

### 2.3 Entropy (party debuff + reward weight)

Entropy is both the run's pressure gauge and its payout weight.

**Stack sources**
- **+1 per room cleared**, starting at room 5.
- **+ severity cost per negative trial card picked** (T1/T2/T3 = +2/+4/+6, §4)
  — the soft pick keeps Entropy lower now but lowers the final payout, and the
  hard pick raises both.

**Pressure effects**
- **−3% all attributes per full 20 stacks** (player + all allies), cap **−45%**
  (reached at 300 stacks); the reward weight uses raw stacks, uncapped.
  (Changed 2026-10-07 from −1%/stack, which capped at just 45 stacks.)
- **Entropy Afflictions (locked 2026-10-06):** every
  `EH_ENTROPY_AFFLICTION_EVERY` (10) stacks permanently acquires ONE random
  distinct affliction type from the battle-start pool (§2.4) — stored in
  `state["entropy_afflictions"]`, numbered + described in the inventory tab.
  Battle-start debuffs are drawn ONLY from the acquired set; before 10 stacks
  there is no battle-start pressure (merciful early game). All 10 types owned
  at 100 stacks; afflictions are never lost mid-run.
- **Battle start (§2.4):** every active party member is hit with random debuffs
  tiered by current Entropy.
- Stored as a single permanent debuff entry on each actor:
  `{type: "eh_entropy", stacks: N, value: pct, source: "event_horizon"}`;
  recomputed on room clear (one entry, not N entries).
- Read sites: new branch in `get_effective_attribute` (player) and
  `get_ally_effective_attribute` (allies) — §7.
- HUD tag: `ENT×N`; full description in the inventory tab.

### 2.4 Entropy battle-start debuffs

When an Event Horizon combat begins (round 1 of `_combat_inner`, next to
`apply_wedding_combat_start`), every **active/living party member** receives a
debuff drawn from the run's acquired **Entropy Afflictions** (§2.3); with no
affliction acquired yet (< 10 stacks) nothing is applied. At higher tiers a
second, distinct affliction can be applied. Tier = `min(4, 1 + entropy // 15)`
(entropy-based magnitudes, affliction-based identity).

Pool (all player-capable appliers — no hard CC): poison, bleed, burn, weaken,
slow, blind, silence, confusion, dread, damage_taken_up. (`curse` is excluded:
it is indefinite and would stack forever — 10 types ship.) Names shown in the
inventory tab via `ENTROPY_AFFLICTION_INFO` (Burn, Weaken, Exposure, …).
Every applied entry is tagged `_eh_entropy` — including entries a fresh
application merely refreshed/merged into — so exit/load sweeps can strip
leftovers (and their flag mirrors) cleanly.

| Tier | Entropy | Durations | DoT damage | Weaken % | DT+ % | 2nd debuff chance |
|---|---|---|---|---|---|---|
| 1 | 0–14 | 2t | `2 + room//5` | 15% | 8% | 0% |
| 2 | 15–29 | 2t | `4 + room//5` | 20% | 10% | 15% |
| 3 | 30–44 | 3t | `6 + room//5` | 25% | 12% | 30% |
| 4 | 45+ | 3t | `8 + room//5` | 30% | 15% | 50% |

Messages print through `c_print`. Implemented as
`event_horizon.apply_entropy_battle_start(player)` (no-op unless `_eh_in_run`).
All numbers are tunable constants (§12).

---

## 3. Flask system

### 3.1 Flow

1. Trigger: **room clear** (combat/event rooms — not trial rooms, they don't
   count as progress) and **shop entry**.
2. Roll: 1 flask = random archetype + tier.
   - `tier_max = min(7, 1 + room // 6)`; roll uniform 1..tier_max.
     (Tier 7 reachable from r36. Early rooms = small numbers, by design —
     infinite supply.)
3. **Select flask** → the log announces the offer
   (`◆ The Horizon offers a flask: <label>`) → prompt **"Who drinks?"** →
   choose MC or any owned ally (front + reserve; dead actors allowed — buff
   persists and applies when revived). Each actor line carries a compact
   owned-flask tally (`Fervor×2, Edge×1`) as an allocation reminder
   (locked 2026-10-06).
4. Consumed immediately upon selection; the chosen actor gains a **permanent
   for the run** buff entry (`permanent: True`, `source: "event_horizon"`).
5. Logged to `actor_flasks[actor_key]` for the inventory display.

### 3.2 Archetypes & magnitudes (tier 1–7)

| Archetype | Mechanism | T1 | T2 | T3 | T4 | T5 | T6 | T7 |
|---|---|---|---|---|---|---|---|---|
| Fervor (+dmg%) | `damage_boost` buff (existing read sites) | 2% | 3% | 4% | 5% | 6% | 8% | 10% |
| Prism (+ele dmg%) | new `eh_ele_dmg` read in `calculate_elemental_damage` (all elements) | 2% | 3% | 4% | 5% | 6% | 8% | 10% |
| Bastion (+DR%) | `defense_pct` buff (existing read sites; 80% total cap applies) | 1% | 2% | 2.5% | 3% | 4% | 5% | 6% |
| Might (+stat) | stat buff entry to a random attribute (existing reads) | +1 | +2 | +3 | +4 | +5 | +6 | +8 |
| Vitality (regen/turn) | `regen_pct` buff — **% max HP per round** (2026-10-07; was flat 1–8) | 0.5% | 0.75% | 1% | 1.25% | 1.5% | 1.75% | 2% |
| Edge (+crit%) | `crit_chance` buff — crit caps at **100%** since the crit rework (overflow converts to crit damage ×0.5) | 1% | 1.5% | 2% | 2.5% | 3% | 4% | 5% |

- Entries carry `permanent: True` and `remaining: 9999`; they are stripped on
  run end by `strip_event_horizon_effects` (no tick-routine changes — 9999
  rounds never expires in practice).
- HUD (playtest 2026-10-06): run-bonus tags **stack** — all permanent
  flask/card/tune-up entries of one effect type sum into a single tag
  (`DMG+37%`, `ELM+14%`, `DEF3%`, `CRT+6%`, `REG+2%`, `STR+2`, `ALL+3` — the
  stat totals make Tune-Up/Might stacking visible);
  ally-skill buffs (Frabjous Day, Fate's Favor) stay individual because they
  are temporary. Prism shows as `ELM+%`; `ENT×N` unchanged.

---

## 4. Trial rooms & cards

### 4.1 Scheduling

- Trigger check after each numbered room clear:
  `room % 5 == 0 and room >= 10` → the next room is a Trial.
- `room % 15 == 0` → `trial_pos` (positive team card); otherwise `trial_neg`
  (enemy handicap). Cadence changed from every 20 in the 2026-10-07 pass.
- Trials do **not** increment `room`. Example:
  `… → r10 → trial_neg → r11 … r15 → trial_pos → r16 … r20 → trial_neg → r21 …`
- Trial flow: intro text → roll 3 distinct cards (different severities; each
  shows its Entropy cost) → **must pick 1** (no skip) → apply → continue to the
  next numbered room. Card selection renders through the standard `term.menu`
  bridge — terminal shows a text menu with full card details; the GUI shows
  the choices as buttons with the details in their labels.
- **Severity economics:** each negative card tier carries an Entropy cost —
  **T1 +2 / T2 +4 / T3 +6** — added when picked. The soft pick keeps pressure
  (and the eventual gold payout) lower; the hard pick raises both. Positive
  (team) cards cost no Entropy.

### 4.2 Card pools (v1)

Card tier scales with depth: `tier = clamp(1 + room // 15, 1, 3)`.

**Deck rule (2026-10-07, corrected):** every **(kind, tier)** pair is a unique
card in the deck — an exact duplicate never appears twice, but cards of the
same kind at *different* tiers both exist and **stack** (effects add: Mending
Roil T1+T2+T3+T4 = 2+3+4+5 = 14%/turn; deliberately uncapped — taking every
tier is the player's choice). A card's tier must be unlocked by depth
(`card_tier_for_room`, T1–T4; T4 from r45), so an **unpicked low tier can
surface at a late room**. Each deck is 6 kinds × 4 tiers = 24 cards and
**exhausts** when everything eligible has been claimed — an empty trial
passes with its motes ("the deck is spent"), an exhausted boon simply
relents, and legacy saves collapse only exact duplicates (different tiers
are kept).

**Negative (enemy handicaps)** — applied to every enemy spawned for the rest of
the run (read in the `enemy_stats` hook):

| Card | Effect (T1/T2/T3/T4) | Entropy cost |
|---|---|---|
| Status Ward | enemies +8/12/16/20% `status_res` (clamped 1.0) | +2/+4/+6/+8 |
| Bloodlust | enemies +6/9/12/15% damage dealt (STR scaling) | +2/+4/+6/+8 |
| Marrow | enemies +10/15/20/25% max HP | +2/+4/+6/+8 |
| Elemental Surge | enemies +6/9/12/15% all elemental damage | +2/+4/+6/+8 |
| Mending Roil | enemies regen 2/3/4/5% max HP per enemy turn (new flag read at enemy turn start) | +2/+4/+6/+8 |
| Chitin | enemies +8/12/16/20% CON/DEX | +2/+4/+6/+8 |

**Positive (team cards)** — applied as permanent buffs to the player + all
owned allies at pick time (same mechanisms as flasks; recorded in
`positive_cards`):

| Card | Effect (T1/T2/T3/T4) |
|---|---|
| Unity | team +4/6/8/10% damage dealt |
| Bulwark | team +4/6/8/10% DR |
| Harmony | team regen 1/2/3/4 HP per round (flat) |
| Insight | team +2/3/4/5 all attributes |
| Aftershock | team +5/8/10/12% elemental damage |
| Celerity | team +1/2/3/4 DEX & crit +2/3/4/5% |

Both lists are stored in run state and rendered face-up in the inventory tab
("positive cards" / "negative cards" groups).

### 4.3 The Joker — the 22 Major Arcana (2026-10-09, all 22 live)

- **The deal:** every 25th cleared room (r25/50/75/…) the Joker deals **2
  faces** from the unowned pool; keep **at most one** or refuse. When rn+25
  lands on a milestone both events occur (milestone first, then the spread).
- **The hand:** capped at **7** arcana, **distinct**, **replaceable** — at
  cap a keep requires throwing an owned arcana, and a **thrown card returns
  to the deck** (dealable again). Stored in `state["joker_cards"]`.
- **The spread:** all **22 Major Arcana** designed
  (`docs/joker_cards_proposal.md`) and **all dealable** (`ready=True`);
  boosts are run-long & party-wide, burdens are bold (drains, price taxes,
  option-closing). The High Priestess ships its documented fallback
  (−25% skill cooldowns — no clean chokepoint for status-application
  chance).
- **The World** is the capstone: it lifts every other owned arcana's
  drawback, but closes the deal — no further offers, no more throws.
- **Off-deck** (no Entropy, no payout weight — "it does not feed the
  Horizon"); refused deals cost nothing. Stripped/restored with the run
  (`apply_joker` / `_apply_joker_to_roster` / `discard_joker`).
- Hooks in code: Tower flask ×2 (`apply_flask`) + per-round drain
  (`tick_player_debuffs`), Magician weakness gate
  (`calculate_elemental_damage` + `_eh_joker_weakness_gate` flag), Wheel
  enemy crit cap (`_eh_crit_cap` stamp/read in `apply_enemy_scaling` /
  `stats.resolve_critical_chance`), Temperance/Hermit economy multipliers
  (mote award sites + `compute_payout`), Moon battle-start
  (`apply_joker_battle_start` — `combat_engine` round 1), Devil shop ×1.2
  (`_shop_flask_price`).
- Batch-2 hooks (2026-10-09; Rev 8/9 redesigns same day): Death lifesteal
  (`_eh_joker_lifesteal` flag at damage sites; healing received ×0.5), Fool
  miss (`joker_attack_missed`, 10%) + initiative
  (`joker_initiative_bonus`, +2), Priestess flat −2-turn cooldowns
  (`set_skill_cooldown`) with basic attacks ×0.5, Hierophant skill ×1.25 /
  basic ×0.75 (`joker_damage_multiplier`), Justice debuff mirror
  (`debuff_signature` diff per action in the engine's player/ally/enemy
  turn blocks → `joker_mirror_debuffs` — every newly-inflicted debuff type
  lands back on the inflictor, once per type per action; the party side is
  the drawback), Hanged Man round-1 skip (`_eh_joker_skip_r1` in
  `roll_initiative`/turn blocks), Star (`tick_player_debuffs` — first-tick
  extra decrement), Sun (`joker_crit_modifier` +30% crit / −15% non-crit),
  Judgement round-start pulse (`joker_judgement_pulse` in the engine round
  loop — 20% max HP pure to all enemies; from round 3 the party takes the
  same, ≥1 HP clamp). All flags lifecycle-managed via
  `_refresh_joker_actor_flags`; World lifts every drawback.

---

## 5. Horizon Motes (run currency)

- **Earn:** combat room clear `6 + room // 2`; event rooms `randint(3, 8)`;
  trial rooms `10 + room // 5` (a consolation for a no-progress room).
- **Spend (only inside):** Event Horizon shops price their stock in motes —
  **flasks only** (playtest 2026-10-06: the old random consumable wares were
  dead weight once deep fights run minutes long):
  - three distinct flask kinds per stall; the **grade scales with room
    progress** (`flask_tier_max`, minus ≤1 grade of variance) and the price
    scales by grade (`20 + 20 × tier`); buying one prompts the usual
    "who drinks?" pick (`_choose_flask_drinker`),
  - "Tune-Up": +1 all attributes to one actor, permanent for the run, once
    per shop visit (stacks across visits — the HUD shows the summed total),
  - one ware per visit is **40% off** (marked SALE; 2026-10-07 playtest),
  - v1 stock excludes equipment (equipment enters the game via milestone
    trophies — §10.3).
- **Wipe:** run end (death/quit) zeroes motes. While suspended, motes persist in
  the run state but are not usable outside (detached like all rift effects,
  §6.2).
- The shop also always offers the free room-visit flask (§3.1).

---

## 6. Entry, exits, save hygiene

### 6.1 Site & entry

- **Unlock:** **Floor 20 cleared** (`player["max_floor"] >= 21`) → the site
  marker appears on the world map (permanent from then on; no spawn cycle).
  Merely reaching floor 20 leaves `max_floor` at 20 — a failed superboss
  attempt does not unlock the site. Saves already introduced to Vesper or
  holding rift progress stay unlocked (grandfathered).
- **Site position:** fixed remote coordinate — placeholder `(730, 280)` in
  `resources/world_layout.py` space (east of the known world, clear of all city
  nodes). Final coordinate decided during implementation.
- **Travel:** same off-road journey plumbing as wild dungeons
  (`facilities/travel.py` + world map "Travel Here"), but the endpoint is
  permanent. Arrival city routing = nearest city (origin_city).
- **The Horizon Watcher — Vesper Erebus (locked):** a man in a robe whose head
  is a **black hole**; he speaks normally, but his voice **echoes**.
- **First contact:** once **Floor 20 has been cleared** (`max_floor ≥ 21`,
  `eh_intro_seen` unset), Vesper greets them in an NPC scene using the
  Archivist-Voss-style UI (facility I/O), explains the distortion, and reveals
  the site on the world map.
- **Arrival scene:** at the site, Vesper talks about the distortion. Menu:
  - No run: `[Enter the Event Horizon] [Ask about the distortion] [Leave]`
  - Suspended run: `[Resume the descent] [Abandon the run & start fresh] [Leave]`
  - Leaving = free; abandoning wipes the run (confirm dialog).
- **Vesper idle dialogue (locked 2026-10-06):** the arrival greeting is
  context-aware, not random: a first-arrival version; rotating idle lines for
  repeat visits (`eh_visits` counter); and a one-time line the first time the
  party's deepest room crosses each 25-room milestone — bespoke at **r25**
  (the deeper flask), **r50** (the coin), **r75** (the robe), **r100** (the
  bond piece) and **r125+** (beating roots). Acknowledged once per save via
  the `eh_vesper_milestone` high-water mark (`plan_vesper_greeting` in
  `facilities/event_horizon_intro.py`). Suspended arrivals append the
  "left it turning at room N" line.
- Entering sets run fields, `origin_city = nearest city`, launches
  `DungeonScreen` with an `_on_eh_result` handler (wild-dungeon pattern).

### 6.2 Exits & cleanup

| Exit | Result | Run state | Payout | Player goes to |
|---|---|---|---|---|
| Death | `"dead"` | **wiped** (best_room kept) | full — stashed in `_eh_pending_payout`, granted by `apply_death_penalty` after the 20% toll | standard death flow |
| Abandon (post-room menu) | `"eh_quit"` | **wiped** | full — paid immediately | nearest city (site) |
| Save & quit | `"save_exit"` | **suspended** | deferred (not a run end) | main menu (load resumes in city; travel back to site) |
| Combat interrupted/timeout | `"timeout"` | **suspended** (defensive) | deferred | nearest city |

- **Flee is disabled in combat** ("the Horizon folds space — there is nowhere to
  flee"); quitting is the explicit post-room menu option (confirm required).
  The dungeon screen's corner button is relabeled **← Leave Rift**
  during runs: it confirms — *"There is no fleeing the rift…"*, buttons
  **Save & Quit / Keep Going** — and the confirm **defaults to Keep Going**
  (playtest: the player may still be mid-Enter on the "Press Enter to
  descend" prompt, which instantly confirmed the old generic dialog and
  flashed it away). Confirming suspends the run before returning to the city.
- **Run-end aftermath:** every run that ends (in-run abandon, death, and
  "abandon & start fresh" from the arrival scene) stashes a run summary
  (`event_horizon.build_run_summary`, captured before the wipe) shown as a
  scrollable dialog — rooms cleared, deepest room, final Entropy, gold paid,
  motes forfeited, cards taken (positive/negative with tiers) and flask
  effects per actor. Death shows it before the death screen (payout line notes
  it is exempt from the toll). The stash `player["_eh_last_summary"]` is
  transient (never saved; scrubbed in `load_game`).
- **Payout:** every run end computes the gold payout (formula in §10.2) before
  wiping. Death pays after the standard penalty so the payout itself is exempt;
  quit pays on the spot with a summary line.
- **Detach / restore (locked 2026-10-06):** rift effects — flask buffs, team
  cards, the Entropy penalty entry, and any leftover battle-start debuffs
  (marked `_eh_entropy`, incl. their `slowed`/`blinded`/`silenced`/`dreaded`
  flags) — are **detached from the roster on every exit that keeps the run
  alive** (suspend, interrupt) and on load of a suspended save. They live in
  `player["event_horizon"]` and are re-attached by
  `restore_event_horizon_effects()` when entering/resuming. Nothing leaks into
  cities or other dungeons, and rift power cannot be carried into unrelated
  content. `strip_event_horizon_effects()` is the single sweep used by both
  detach and run-end wipe (idempotent).
- Wipe = clear run dict (keep `best_room`), strip all `event_horizon` buff
  entries from every actor, clear transient flags.

### 6.3 Save hygiene (pandemonium-lesson compliant)

- Transient flag `player["_eh_in_run"]` gates the combat hooks. It is **popped
  before any save while inside** (both save&quit branches) and **defensively
  popped in `save_load.load_game`** (mirror of the `pandemonium_mode` fix).
- `apply_death_penalty` scrubs `_eh_in_run` and pays the deferred payout
  (after the toll); `city_screen._launch_dungeon` defensively scrubs stale EH
  flags/ids so the rift can never hijack city runs.
- Floor-cursor parity: snapshot `player["floor"]` at entry, restore on every
  exit (`_wild_restore_floor` pattern). The rift must never touch
  `city_floors` / `max_floor`.
- **Effect hygiene:** a suspended save stores effects **only** in
  `player["event_horizon"]` (flask records gain an `effect` field for exact
  restore; legacy records rebuild from archetype + tier). `load_game`
  defensively strips baked-in actor entries for saves with EH run history
  (covers pre-detach saves and mid-run checkpoints) — **legacy sweep
  included**: untagged leftovers from pre-marking builds are matched by
  signature (`damage_taken_up` values from the Entropy tier ladder with
  remaining ≤ 3, `source:"entropy"` bleeds) and removed too (third playtest:
  a stuck `DT+8%`). The button-flee defensive path
  (`world_map._on_eh_result` timeout/None) also detaches with the sweep.

### 6.4 Boss Rush (locked 2026-10-12)

> 🚧 **Status: WIP — under review (2026-10-14).** The rush reuses the
> superboss profiles/fights, but **the way the fight connects to the rush
> flow needs a review pass** before this counts as shipped. Playable for
> testing (menu option carries `[WIP]`); not listed in the README/changelog.

A **player-invoked** rematch mode offered at the arrival scene (not a spawn —
decision-log item 15 stands). When every gate is met, Vesper's menu gains
**"⚔ Face the gathered echoes — Boss Rush"**.

- **Pool = overworld kills only.** The queue is built from
  `player["defeated_superbosses"]` against the fixed `BOSS_RUSH_ROSTER`
  (9 pool bosses + 5 Wonderland + Chrysalis + White Knight = 16). Undefeated
  bosses are skipped entirely; order is a difficulty ramp by each boss's
  original template level. Old saves: `ensure_player_fields` backfills the
  ledger from Wonderland / White-Knight flags + awakening `pool:` sources —
  kills logged before the ledger existed still count.
- **Entry gates (all):** ≥ `EH_RUSH_MIN_BOSSES` (3) defeated superbosses,
  `best_room ≥ 50`, `max_floor ≥ 40`. An active run blocks the plain offer;
  a **suspended** run is offered the rush too — picking it asks to collapse
  the sitting run first (payout kept, run wiped), then raises the echoes.
- **Setup:** `eh.begin_rush(player, city)` starts a **fresh run** in
  `rush_mode` (queue + locked `rush_level` stored in state; cards / flasks /
  motes / entropy start clean). A normal fresh run can never inherit a rush
  queue (`begin_run` resets the rush keys).
- **Scaling (flat; replaces room + trial scaling):** every enemy spawned
  during a rush (minions included) goes through `apply_rush_scaling`:
  `level = max(original_level, 40 + 5·pool + 10·pandemonium)` and
  `stats ×= 1.25 + 0.03·(level − 40)` on HP/STR/CON/DEX. The frozen ×1.4
  rift difficulty and Full Moon still apply; room progress and trial cards
  do **not** (flat by definition). Rush enemies carry `_eh_rush`.
- **Room flow:** each boss is one room (`BOSS RUSH k/N — the echo of …`),
  numbered 1..N so payout math / `best_room` tiering behaves like a normal
  run. **Pure linear progress (locked 2026-10-12): no motes, no cards, no
  flasks, no system healing** — the only things that persist between echoes
  are **HP and skill buffs**. Interval healing is self-service: the
  between-echoes intermission keeps the usual **Inventory / Stats** option
  (consume your own bag) alongside save & quit / abandon. **No** trials /
  milestones / Joker / Entropy accrue during a rush (`sync_entropy` pins
  room progress to 0 in rush mode).
- **Flee is blocked mid-rush:** a fled fight restarts from the top ("There
  is no running from the echoes."), matching overworld superboss semantics.
- **Completion (WIN):** after the final echo the run ends via
  `dungeon._eh_rush_complete` — full payout **+ full-circuit bonus**
  `100 + 25·pool` gold; `rush_clears += 1` and `rush_best = max(…, pool)`
  persist through `clear_run`; the summary shows `Boss Rush : N/N echoes
  felled`. Death mid-rush is the standard EH death (deferred payout, run
  wiped); suspend/abandon behave as usual.
- **GUI:** rush fights ride the existing superboss overlay
  (`superboss_override` receives a `{"rush": True, …}` spec;
  `_gui_superboss` resolves it) with top bar `⚔ Boss Rush | Echo k/N`; the
  rift status panel + dungeon top bar show `Boss Rush k/N`.
- **Registry:** `BOSS_RUSH_ROSTER` in `event_horizon.py` (`id` = the
  defeat-ledger id; `keys` = HUD enemy keys; `module`/`func` resolved lazily
  by `rush_boss_combat`).

---

## 7. Combat / engine integration points (exact)

| File | Change |
|---|---|
| `event_horizon.py` (NEW) | State, constants, scaling math, flask roll/apply, card roll/apply, mote helpers, wipe/strip helpers, trial schedule, `create_room()`. |
| `event_horizon_rooms.py` (NEW) | Room handlers: shop (mote-priced flask wares + Tune-Up), mote events / fountain reuse, trial card selection flow, flask "who drinks?" flow (`_choose_flask_drinker`). |
| `dungeon.py` | `explore_dungeon()` fork → `_explore_event_horizon()` loop (room-based; no floor logic); exits: `eh_quit`/`save_exit`/`dead`/`timeout`; run payout + milestones; no XP/drop/bounty calls. |
| `combat/combat_engine.py` | `_combat_inner` round-1 block: `event_horizon.apply_entropy_battle_start(player)` (gated by `_eh_in_run`). |
| `leveling.py` | Defensive XP-freeze early-return in `gain_exp` while `_eh_in_run` (ally XP skipped at call sites). |
| `combat/stats.py` | `enemy_stats()` rift hook: HP/STR/CON/DEX multipliers, negative-card effects (status_res, HP, ele dmg), set `rift_regen_pct` flag. |
| `combat/status_effects.py` | Untouched (Phase 1 deviation 1: permanent entries use `remaining: 9999` + strip-on-run-end). Entropy helpers live in `event_horizon.py`. |
| `combat/elemental.py` | `calculate_elemental_damage()`: read `eh_ele_dmg` buffs (works for any actor: party, enemies). |
| `combat/enemy_ai.py` | Enemy turn start: `rift_regen_pct` heal + message. |
| `combat/combat_ui.py` | Tags: `ENT×N`; run bonuses STACK per type (`DMG+%`, `ELM+%`, `DEF%`, `CRT+%`, `REG+n`, `+STAT`); `TRL×N: …effects` (trial burdens + what they do, stamped by `apply_enemy_scaling`; effect list from `event_horizon.trial_burden_tags`). |
| `combat/stats.py` (`get_effective_attribute`) + `combat/ally.py` (`get_ally_effective_attribute`) | `eh_entropy` debuff read (multiplicative on totals). |
| `character.py` | `ensure_player_fields` defaults for `player["event_horizon"]` (+ `eh_intro_seen`). |
| `save_load.py` | Defensive pop of `_eh_in_run` + `_eh_last_summary` (aftermath stash) on load. |
| `utils.py` (`apply_death_penalty`) | Defensive EH wipe (run + actor effects) **+ grant `_eh_pending_payout` after the toll**. |
| `combat/weapon/piece_of_relationship.py` (NEW) | MC-only trophy: ally-count tiers, battle-start buffs, ally-targeted mark hook + `player_only` guard for ally equips. |
| `combat/weapon/chance_and_choice.py` (NEW) | Trophy: per-action 50/50 ×0.25/×1.75 roll wired into the four party damage paths. |
| `combat/weapon/dopo_robe.py` (NEW) | Trophy: blade-only live damage multipliers (wearer 1.40/1.50; blade allies 1.15). |
| `combat/enemy_ai.py` | Rift regen flag + POR tier +7: mark the attacker when an ally is targeted (hit or miss). |
| `combat/ally.py` (`equip_ally_item`) | Refuse `player_only` items for allies (new flag convention). |
| `resources/items.py` | Three trophy item defs (`unique`, `description`, trophy flags). |
| `resources/world_layout.py` | Optional: `EVENT_HORIZON_POSITION` constant (or keep in `event_horizon.py`). |

Runtime gate for all combat hooks: `player.get("_eh_in_run")` **and**
`player["event_horizon"]["run_active"]`.

---

## 8. GUI integration

| Screen | Change |
|---|---|
| `gui/screens/dungeon_screen.py` | Third branding branch: name "EVENT HORIZON", top bar `Room N · ◎ motes`; `_update_top_bar` branch; result routing via `on_result`; leave button relabeled `← Leave Rift` with an EH suspend-confirm (focus defaults No — `confirm_dialog(..., focus_no=True)`); Map panel relabeled "Rift" fed by `render_event_horizon_status`, Party Status refreshed per room (`_eh_refresh_hud`). |
| `gui/screens/combat_screen.py` | During runs the top bar shows `Combat | ⚔ The Event Horizon | Room N` (build_ui + `_update_top_bar` + `_on_round_header`); Wonderland quirk append suppressed for EH combat. |
| `gui/screens/inventory_screen.py` | Conditional **" Event Horizon "** tab while a run is active/suspended (IN RUN / SUSPENDED banner, motes, Entropy + **afflictions**, per-actor flask buffs, positive/negative cards); after a wiped run a history stub remains when any run happened (best room). |
| `gui/screens/inventory_screen.py` (bag + equipped) | **Examine on unique equipment** — new convention: every `unique` item shows Examine + lore (`description`) + an **Equip Effect** line (registry `resources/unique_effects.py`; wedding accessories reuse their combat blurbs incl. the bonded upgrade). The button stays available while the item is equipped (Stats & Equip + ally pages, 2026-10-07). Uniques with no implemented effect say so. |
| `gui/screens/world_map_screen.py` | Permanent site marker (appears once Floor 20 is cleared, `max_floor ≥ 21`), info panel, "Travel to Site" button, arrival handling → Watcher scene → launch/resume. |
| `facilities/travel.py` | Site endpoint support in journeys (mirror wild support). |
| Arrival NPC scene | Implemented as a facility-style flow (reuse `gui/terminal.py` I/O); intro text + menu (§6.1). |
| Modals | Card selection + flask drinker prompts use the `term.menu` bridge: terminal = text menu with full details; GUI = the same choices as buttons. |

---

## 9. Persistence summary

- `player["event_horizon"]` and actor buff entries round-trip through the
  existing JSON save (all JSON-safe primitives).
- Suspended runs survive quit → load → travel back to the site.
- Death/abandon wipes run state + actor effects; `best_room` is forever.
- `ensure_player_fields` migration means old saves gain empty defaults.

---

## 10. Rewards (locked)

### 10.1 Frozen / disabled inside Event Horizon

- **Character XP is frozen** — no `gain_exp`/`gain_exp_ally` from any EH source
  (defensive early-return in `gain_exp` while `_eh_in_run`; ally calls skipped at
  call sites).
- **Enemies drop nothing** — no per-kill gold, no item drops (room-victory code
  skips `add_drop_to_inventory`, `add_gold_drop`, and XP).
- **Bounty progress disabled in EH** (locked — infinite kills would farm
  bounties).
- **Wedding end-of-combat loot suppressed** (run `end_wedding_combat` cleanup
  only; skip `apply_wedding_combat_end`'s gold/gift branches).
- Merchant flasks apply like any rift flask (per-run, logged in the
  inventory tab); motes spent never return.

### 10.2 Gold payout (at run end)

```
room_value(r)  = EH_GOLD_BASE + EH_GOLD_PER_ROOM · r        # 10 + 2·r
entropy_weight = 1 + entropy · EH_GOLD_PER_ENTROPY          # 0.02/stack, uncapped
payout         = int( Σ_{r=1..rooms} room_value(r) · entropy_weight )
```

- Reference points: r50 with ~50 Entropy ≈ 3,050 × 2.0 ≈ **6,100 gold**;
  r100 with ~110 Entropy ≈ 11,100 × 3.2 ≈ **35,500 gold**. All constants
  tunable (§12).
- **Full on any run end** — death, quit, interrupt. Death stashes
  `player["_eh_pending_payout"]` and `apply_death_penalty` grants it **after**
  the 20% toll (payout exempt). Quit pays immediately with a summary line.
- No daily-event / Pandemonium / time-of-day multipliers apply inside.

### 10.3 Milestones (fire on room clear; the run continues)

| Room | Reward |
|---|---|
| every 25 (r25, r50, r75, …) | guaranteed **tier 6–7 flask** (drinker chosen as usual) |
| every 50 (r50, r100, …) | **Deep boon** — pick 1 of 3 positive team cards (extra, on top of any trial that follows) |
| r50 (one-time) | Trophy: **Chance and Choice** (§10.5) |
| r75 (one-time) | Trophy: **Old Dopo Robe** (§10.5) |
| r100 (one-time) | Trophy: **Piece of Relationship** (§10.5) |
| every 25 past r100 (r125, r150, …) | Trophy: **Beating Root** — consumable; each copy opens **one actor's** 3rd accessory slot (§10.6) |

- Milestone order when a room clears: milestone rewards → flask offer → trial
  check. A trophy room that is also a trial-trigger room still spawns its
  trial next (e.g., r50: deep boon + Chance and Choice → then the negative
  trial).
- Trophy flags are one-time per save (`eh_trophy_<item_id>`); duplicates are
  never granted.
- Trophies are safe from the death penalty (it is gold-only).
- `best_room` persists across runs (always the deepest reached).

### 10.4 Motes

- **Intentionally lost on run end** (confirmed) — not a gap.

### 10.5 Trophy items (locked designs)

All three are `unique` equipment with authored `description` lore and an
**Examine** button in the bag (new convention: every unique is examinable —
§8). Trophy lore text carried from the planning brief (POR keeps its
`[REDACTED]` line). Actor-based modules follow the repo's unique-equipment
convention (`combat/weapon/<name>.py`, `_actor_has_<id>` helpers).

#### Piece of Relationship — `piece_of_relationship` (MC-only accessory)

Obtained: **r100**. Full effect on acquisition — it is **not** an upgrade
chain and **not** enhance-level based. Its tiers are driven by how many owned
allies (active + bench) sit at **200 affection** (`affection >= 200`); the
count is re-checked at every battle start, so the item grows as more allies
marry.

| Bonded allies | MC gains | Each bonded ally gains |
|---|---|---|
| 2–3 ("+2") | +10% dmg | +5% dmg |
| 4–6 ("+4") | +10% dmg, +2% dodge, +2% crit | +10% dmg |
| 7+ ("+7") | +20% dmg, +5% dodge, +5% crit | +15% dmg, +5% dodge, +5% crit |

- **Tier +7 extra:** when an ally is targeted by an enemy attack (**hit or
  miss**), that attacker gains **Hunter's Mark** — `hunters_mark = True`,
  explicit `hunters_mark_bonus = 0.20`, `hunters_mark_turns = 2` (tunable),
  source "Piece of Relationship".
- Buffs are applied at battle start (whole battle), refreshed each combat;
  active + bench allies included so swaps keep their buffs.
- Battle-start log line doubles as the "ally indicator":
  `✥ Piece of Relationship resonates with N bonded allies (tier +4).`
- **MC-only:** item carries `player_only: True`; `equip_ally_item` refuses it
  for allies (new flag convention). The player has dual accessory slots, so
  it can coexist with a wedding accessory.
- Effect mechanism: existing `damage_boost`, `evasion`, `crit_chance` buffs
  (no new read sites needed except the mark hook in `enemy_ai`).

#### Chance and Choice — `chance_and_choice` (accessory, any actor)

Obtained: **r50**. A coin: **once per damaging action**, a 50/50 roll scales
that action's damage — either **×0.25** or **×1.75** (all hits of the action).
Expected value is exactly **1.0** (pure volatility; no expected-power change).

- Applies to **every** direct damaging action of the wearer (rev 3.5): basic
  attacks, skills, workshop/Furioso volleys (one flip for all hits), kit
  bursts (Cutlass riposte, Jade discharges, Palette exhibits/Signature/
  Spectrum), and wedding counters/retributions. Not DoTs/burn ticks, heals,
  trap damage, or riders on an attack that already rolled.
- One proc log line per roll: `🪙 Chance and Choice — DISASTER! The coin fails
  you — damage reduced (×0.25).` / `🪙 Chance and Choice — FORTUNE! The coin
  favors you — damage boosted (×1.75).`.
- Implementation: per-action roll cached in the action's damage closure
  (same pattern as `power_buff`'s once-per-action consumption), wired into all
  four party damage paths (player basic, player skills, ally basic, ally
  skills) and — since rev 3.5 — every weapon-kit damage path (multi-hit
  volleys share one state; solo bursts pass `state=None`).

#### Old Dopo Robe — `old_dopo_robe` (armor, any actor)

Obtained: **r75**. Blade-synergy armor. The whole effect requires the
**wearer** to wield a `blade` weapon.

| Condition | Effect |
|---|---|
| Wearer wields a blade | wearer damage **×1.40** |
| Each blade-wielding ally (excluding the wearer; **benched count**) | wearer **+5% per ally, uncapped** (×1.40 + 0.05·N); each such ally **×1.15** |

- **Weapon check:** only `weapon_type == "blade"` activates the effect.
- **Stacking (locked):** the wearer's bonus grows +5% per blade-wielding ally
  with **no cap**; N counts **all recruited allies**, active or benched (user
  decision). Reserve allies still receive their own ×1.15 when swapped in.
- **Live-read at damage time** (handles mid-combat ally swaps; no battle-start
  application needed): helper returns the multiplier per attacking actor.
- Player + allies both usable (actor-based); allies can wear it if their own
  weapon is a sword (then they are the wearer).


---

### 10.6 Beating Root — per-actor accessory slot unlock (deep content)

- **Grant:** one copy at every 25-room milestone past r100 (r125, r150,
  r175, …), once per milestone per save. Eight copies cover a full 8-actor
  roster — i.e., clearing to **r300** opens a 3rd accessory slot for everyone.
- **Use:** Beating Root is a **consumable trophy** — the player picks ONE
  actor (MC or ally) to consume it. That actor permanently opens **their own**
  `accessory3` slot. Copies are consumed; there is no global unlock.
- **Persistence:** the item and the per-actor unlock persist outside the run
  (trophy, not run-scoped).
- **Implementation (Phase 5, done 2026-10-06):** per-actor `acc3_unlocked`
  flag (+ `player.setdefault` in `ensure_player_fields`); `accessory3`
  appears in equipped dicts only once unlocked (`consume_beating_root`
  creates the key); `equip_item` / `equip_ally_item` auto-pick chains prefer
  1 → 2 → 3(unlocked); a locked `accessory3` request falls back to the
  normal auto-pick chain (no locked-slot messaging — the slot stays entirely
  invisible until a root is consumed); the
  accessory-replacement chooser gains a third button only when unlocked;
  Stats & Equip + ally panels show the third row only when unlocked;
  `_slot_display_name` → "Accessory 3".
- **Audit results (every `accessory1`/`accessory2` assumption):**
  gear-preservation loops (house return/stash ×3) + `_ally_to_house_record`
  / `create_ally_from_girl` persist `acc3_unlocked` across house round-trips
  (otherwise the unlock was lost when benching); item-identity scans
  (`vileheart_venom`, `authors_pen`, `prescript_ledger`, `sky_piercer`,
  `wedding_specials`) extended; blacksmith enhancement pools ×2 extended;
  already slot-agnostic and unchanged: `get_total_equipment_mods`,
  `compute_player/ally_elemental`, `unequip_slot` / `unequip_ally_slot`,
  save/load. Not extended by design: temp-heroine 4-slot auto-equip builds
  (guests never unlock), Inn slipper checks (deliberately accessory1),
  `character.py` base-slot normalization (slot 3 is created on unlock only).

---

## 11. Implementation phases

**Phase 1 — core module + hooks + trophy items (no UI). ✅ DONE 2026-10-06**
`event_horizon.py` (state, constants, scaling math, flask/card roll + apply,
entropy battle-start debuffs, payout math, milestone schedule,
wipe/strip), `character.py` defaults, `combat/stats.py` hook,
`combat/status_effects.py` permanent-skip + entropy + strip,
`combat/elemental.py` read, `combat/enemy_ai.py` regen + POR mark hook,
`combat/combat_engine.py` battle-start hook, `leveling.py` XP guard,
`resources/items.py` `weapon_type` pass on all weapons, three
trophy item defs + modules (`piece_of_relationship.py`, `chance_and_choice.py`,
`dopo_robe.py`), `equip_ally_item` player-only guard.
Tests: `tests/test_event_horizon.py` (state migration, tier bounds, scaling
math, trial schedule + severity costs, entropy math, payout math, battle-start
debuff application, trophy effect math, wipe/strip idempotence).

**Phase 2 — dungeon loop. ✅ DONE 2026-10-06**
`dungeon.py` `_explore_event_horizon()` + `event_horizon_rooms.py` (room gen,
flask flow, trial flow, mote shop, milestones/trophy grants, payouts, no-drop
victory path, exits, suspend/resume snapshots).
Tests: `tests/_diag_eh_run.py` scenario runs (loop with mocked combat:
clear/flask/trial/milestones/suspend/quit/death wipes + payout).

**Phase 3 — world map + entry. ✅ DONE 2026-10-06**
`event_horizon.py` site helpers (`site_unlocked`, `event_horizon_site`,
`build_journey_to_site`, `begin_run`); `wild_dungeons.offroad_segment` /
`build_journey_to_dungeon` gain a `to=` target; world map marker + info panel +
selection + travel + Vesper arrival scene routing (`_arrive_at_horizon` /
`_after_eh_scene`, `_stop_travel_visuals` helper);
`facilities/event_horizon_intro.py` (first-contact + arrival scenes, per §6.1
menus); `city_screen` intro hook + `_launch_dungeon` scrub; `dungeon_screen` EH
branding + room/motes top bar. Save hygiene landed with Phases 1–2
(`load_game` pop, `apply_death_penalty` pending-payout grant).
Tests: `tests/_diag_eh_map.py` (unlock gate, site fields, journey + wild
regression, run lifecycle, GUI wiring smoke).

**Phase 4 — inventory + polish. ✅ DONE 2026-10-06**
Inventory "Event Horizon" tab (conditional on an active/suspended run: room
cursor, best room, motes, Entropy, per-actor flask effects, positive/negative
cards); unique-item Examine on bag equipment (trophy lore, rarity fallback via
`drop_rarity`); HUD tags `ENT×N` (entropy debuff) + `ELM+%` (prism flask) in
`combat_ui._get_entity_buff_tags`; changelog v0.1.8.0 "Event Horizon" section +
Equipment UI bullet; README section + What Next bullet + ToC entry.
Tests: `TestHudTags` (event_horizon suite) + `tests/_diag_eh_phase4.py`
(headless InventoryScreen build: tab visible with content while run active,
absent without a run, unique/key Examine buttons present); full sweep green.

**Phase 5 — Beating Root (post-core). ✅ DONE 2026-10-06**
Per-actor 3rd accessory slot unlock: `acc3_unlocked` + `accessory3` created
on consume; equip flows/auto-chains/prompts gated by the flag; inventory UI
(third slot row + chooser button only when unlocked); house round-trip
persistence; full `accessory1`/`accessory2` audit (results in §10.6); GUI
"Use" flow on the Beating Root (Key Items) with an actor picker; milestone
grants at r125+ verified (flag-per-milestone, pending queue on a full bag).
Tests: `TestBeatingRoot` (8) in the event_horizon suite; `_diag_eh_phase4`
Use-button + slot-row visibility checks.

---

## 12. Tunable constants (v1 defaults)

| Constant | Default |
|---|---|
| `EH_UNLOCK_MAX_FLOOR` | 20 (must be **cleared** — gate is `max_floor > 20`) |
| `EH_ENEMY_HP_PER_ROOM` | 0.018 (was 0.025) |
| `EH_ENEMY_DMG_PER_ROOM` | 0.013 (was 0.020) |
| `EH_ENEMY_DEF_PER_ROOM` | 0.010 (was 0.015) |
| `EH_LEVEL_PER_ROOM` | 3 (rooms per +1 enemy level) |
| `EH_ENEMY_START_LEVEL` | 20 (flat room-1 band; decoupled from `max_floor`) |
| `EH_ENEMY_LEVEL_CAP` | 56 (max regular enemy level; multipliers carry beyond) |
| `EH_ENEMY_BAND_FLOOR` | 30 (band lower edge held here at depth) |
| `EH_TIME_DIFFICULTY` | 1.4 (frozen in-run difficulty baseline) |
| `EH_ENTROPY_START_ROOM` | 5 |
| `EH_ENTROPY_STEP_STACKS` / `EH_ENTROPY_STEP_VALUE` | 20 stacks → −3% all attributes |
| `EH_ENTROPY_CAP` | 0.45 (reached at 300 stacks) |
| `EH_TRIAL_ENTROPY_COST` | T1 +2 / T2 +4 / T3 +6 / T4 +8 |
| `EH_BS_TIER_STEP` | 15 (tier = min(4, 1 + entropy // 15)) |
| `EH_BS_SECOND_CHANCE` | 0 / 0.15 / 0.30 / 0.50 by tier |
| `EH_ENTROPY_AFFLICTION_EVERY` | 10 stacks per random Entropy Affliction |
| `EH_GOLD_BASE` | 10 |
| `EH_GOLD_PER_ROOM` | 2 |
| `EH_GOLD_PER_ENTROPY` | 0.02 (weight per stack; uncapped) |
| `EH_MILESTONE_FLASK_EVERY` | 25 |
| `EH_MILESTONE_BOON_EVERY` | 50 |
| Trophy grants | r50 Chance and Choice · r75 Old Dopo Robe · r100 Piece of Relationship · r125+ Beating Root (consumable; per-actor accessory3 unlock) |
| `EH_BEATING_ROOT_EVERY` | 25 rooms past r100, once per milestone per save |
| `EH_JOKER_EVERY` | 25 rooms (the Joker deals 2 arcana; keep 1, skippable, off-deck) |
| `EH_JOKER_HAND_CAP` | 7 (hand cap; a thrown card returns to the deck) |
| `EH_JOKER_DEAL` | 2 faces dealt per encounter |
| `EH_POR_TIERS` | 2 / 4 / 7 bonded allies (owned, `affection >= 200`, incl. bench) |
| `EH_POR_MARK` | +20% / 2 turns (tier +7 attackers) |
| `EH_ROBE_WEARER_PCT` | 40% base + 5% per blade-wielding ally (uncapped) |
| `EH_ROBE_ALLY_PCT` | 15% per blade-wielding ally |
| `EH_COIN` | 50% ×0.25 / 50% ×1.75, once per damaging action |
| `EH_FLASK_TIER_PER_ROOMS` | 6 (tier_max = min(7, 1 + room//6)) |
| `EH_TRIAL_EVERY` | 5 rooms, first at r10 |
| `EH_POSITIVE_TRIAL_EVERY` | 15 rooms (was 20) |
| `EH_ROOM_WEIGHTS` | combat 70 / shop 12 / event 10 / fountain 8 |
| `EH_MOTES_BASE` | `6 + room // 2` per combat room |
| `EH_SITE_POSITION` | (730, 280) placeholder |
| Boss Rush gates (`EH_RUSH_MIN_BOSSES` / `_MIN_BEST_ROOM` / `_MIN_MAX_FLOOR`) | 3 / 50 / 40 (all required; arrival offer) |
| Boss Rush level (`EH_RUSH_MIN_LEVEL` / `_LEVEL_PER_BOSS` / `_LEVEL_PER_PANDEMONIUM`) | 40 + 5·pool + 10·pandemonium (flat, locked at start) |
| Boss Rush stats (`EH_RUSH_STAT_BASE` / `_STAT_PER_LEVEL`) | ×(1.25 + 0.03·(level − 40)) on HP/STR/CON/DEX |
| Boss Rush clear bonus (`EH_RUSH_CLEAR_BONUS_BASE` / `_PER_BOSS`) | 100 + 25·pool gold on full circuit |

---

## 13. Open items / deferred

- Trophy numbers (POR mark magnitude, robe stacking, coin spread) are
  first-pass defaults, tunable via playtest.
- ✅ **Vesper Erebus dialogue (Phase 3, extended 2026-10-06)** — first-contact
  + site arrival scenes shipped in `facilities/event_horizon_intro.py`, with
  context-aware idle dialogue on arrival (first visit / rotating re-entries /
  one-time milestone lines r25–r125+); a prose polish pass is welcome but no
  longer blocking.
- Balance numbers above are first-pass defaults, expected to be tuned via
  playtest (like wild dungeon level bands were).
