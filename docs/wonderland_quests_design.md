# Wonderland Side Quests — Design & Wiring

**Status:** Implemented 2026-10-27 (v0.1.8.2 content patch); way-in guide added 2026-11-08.
**Runtime:** root `quests.py` · **Definitions:** `resources/quests.py`.

> **Next:** the staged inn/guest pacing and per-heroine boss-variant rework is
> proposed in [`wonderland_heroine_rework.md`](./wonderland_heroine_rework.md).

Wonderland is a hidden realm with no quest board — the book, the tea party and
the Storybook Dungeon are the givers. These seven side quests make existing
Wonderland content visible in the Journal without duplicating its progression
state.

## Quest chain

| Quest ID | Name | Objectives |
|---|---|---|
| `sq_wonderland_00` | The Looking-Glass Road | Clear Floor 20 in two biomes; hold a Looking Glass Shard; open the book in Veilholt's Arcane Tower |
| `sq_wonderland_01` | Down the Rabbit Hole | Enter Wonderland; defeat the Queen of Hearts (F10); return to the Mad Hatter's tea party |
| `sq_wonderland_02` | The Storybook Road | Reach F20, F30 and F40 |
| `sq_wonderland_03` | The Author's Last Page | Defeat the Big Bad Wolf (F20), Wicked Witch (F30), Jabberwock (F40) and Mary Sue (F50) |
| `sq_wonderland_alice` | Alice's Jabberwock | Meet Alice; recruit her; defeat the Jabberwock; see her become permanent |
| `sq_wonderland_red_hood` | Red Hood's New Ending | Meet Red Hood; recruit her; defeat the Big Bad Wolf; see her become permanent |
| `sq_wonderland_dorothy` | Dorothy's Way Home | Meet Dorothy; recruit her; defeat the Wicked Witch; see her become permanent |

`sq_wonderland_00 → 01 → 02 → 03` chain through `rewards.next`; the three
heroine arcs stand alone. All rewards are XP + gold (no new items, so existing
unique drops and weapon upgrades keep their own pacing).

## Auto-start rules

`quests._sync_wonderland_quests()` runs at the top of every
`quests.update_quests()` call (city entry, travel, capture, recruitment…):

1. **Way-in guide:** start `sq_wonderland_00` once the player holds a Looking
   Glass Shard, has at least one Floor-20 biome clear, or has prior Wonderland
   progress. The quest's description names the shard's source (Veilholt's Black
   Market, 5,000g) and the book's location.
2. If `wonderland_unlocked` / `wonderland_active` is false, stop after the
   guide.
3. Start `sq_wonderland_01` once the book sets `wonderland_unlocked`; its
   "enter the book" objective checks off via `wonderland_visited`. The two
   flags are separate so a future unlock event cannot pre-check the objective.
   Old saves that already cleared the Queen resolve immediately.
4. Start each heroine arc once `heroine_met` is true — under the staged guest
   flow that means the heroine has arrived and been met at the inn, not that
   the player has merely entered Wonderland. See `wonderland_heroine_rework.md`.
5. Start `sq_wonderland_02` once the intro completes (or `max_floor >= 20` for
   legacy saves). `sq_wonderland_03` follows from the chain.

The mysterious book sets `wonderland_visited` and calls
`update_quests(player, "visit_city", "wonderland")` on entry, so the first
objective checks off immediately; the tea-party interactions call
`update_quests` with `heroine_met` / `heroine_recruited` so the arcs update
while still in the inn.

## Objective state checks

All new objectives are state-based and monotonic (old-save safe):

| Type | Passes when |
|---|---|
| `wonderland_gate` | the count of non-Wonderland biomes with `max_floor >= 20` meets the target |
| `wonderland_shard` | a `looking_glass_shard` is in the inventory |
| `wonderland_enter` | `wonderland_visited` / `wonderland_active`, or old-save evidence of a visit |

The two way-in prerequisites (`gate`, `shard`) also pass once
`wonderland_entered` is true, so saves that predate the guide never keep an
uncompletable reminder active.
| `wonderland_floor` | `city_floors["wonderland"]["max_floor"] >= target` |
| `wonderland_boss` | `wl_boss_defeated_<target>` is set (fallback: `max_floor` past that boss's floor) |
| `heroine_met` | state key is not `"unmet"`, permanent flag, party, or saved temp heroine |
| `heroine_recruited` | state is `"temp"`/`"permanent"`, permanent flag, party, or saved temp heroine |
| `heroine_permanent` | permanent flag, state `"permanent"`, or a non-temp heroine in the party |

The floor fallback (`_WL_BOSS_FLOOR_FALLBACK`) exists because a Wonderland run
cannot pass a living floor-10/20/30/40/50 boss: reaching the next floor proves
the kill even if an ancient save lacks the explicit flag.

## Save compatibility

One new persistent field: `wonderland_visited` (seeded in
`character.ensure_player_fields()`; old saves backfill it from
`wonderland_unlocked`, which was only set on entry in earlier builds). Progress
otherwise lives in the existing `player["quests"]` block.
`_sync_wonderland_quests` backfills on the next city entry, and completed
quests are recorded in `journal["side_quests"]` by `sync_journal`.

## Verification

`tests/_diag_quests.py` covers:

- the way-in guide appearing after one Floor-20 biome clear and resolving gate /
  shard / book objectives in order;
- no quest before a relevant Wonderland milestone;
- entry → intro completion → Storybook Road;
- tea-party states (`intro` / `temp` / `declined`) filling the right objectives;
- floor + boss milestones completing the road, heroine arcs and finale;
- idempotency of repeated sync passes;
- old-save floor fallback when all `wl_boss_defeated_*` flags are missing.

Run: `.venv\Scripts\python.exe tests\_diag_quests.py`
