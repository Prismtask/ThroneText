# Pandemonium — Improvement Planning Guide

**Purpose:** a general, reusable process to run through **before implementing any improvement** — QoL polish, balance changes, content, system extensions, or new systems. It answers three questions: *Does this already exist? What does it touch? What must be true before, during, and after the work?*

> Historical idea lists (e.g. [`TerminalRPG_Improvement_Opportunities.md`](./TerminalRPG_Improvement_Opportunities.md)) are **raw input, not plans**. That doc is kept as a historical record — many of its items have since shipped, so always verify status in code, never in old docs.
>
> The **living backlog** is [`Pandemonium_Open_Improvements.md`](./Pandemonium_Open_Improvements.md) — pick ideas from there, and update that list as items ship.

---

## 1. Check it doesn't already exist

The #1 source of wasted work is re-implementing something that shipped months ago.

| Where to look | What it tells you |
|---|---|
| `gui/screens/changelog_screen.py` | Every shipped feature, newest first — the most complete history |
| `docs/*_design.md` | Locked design decisions for active/planned systems |
| `README.md` / `wiki/index.html` | Player-facing feature coverage |
| Code search | Ground truth — grep for identifiers, not prose |
| `/memories/repo/` notes | Decisions and pitfalls already encountered |

If it exists partially, prefer **extending the existing system** over building a parallel one (e.g. masteries extend skills; dispatch extends house girls — don't add a competing subsystem).

## 2. Classify & evaluate the idea

**Types:** QoL/polish · balance · content (enemies, items, quests, dialogue) · system extension · brand-new system.

**Answer these before scoping:**

- **Touch points** — which systems does it involve? Combat, time blocks, quests/journal, dispatch, economy/trade, GUI screens, save data, wiki.
- **Save compatibility** — does it add player fields? → `ensure_player_fields()` (`.setdefault()`) + an old-save migration path. Make state progress **monotonic** where possible so old saves never dead-end.
- **Threading / GUI** — does it run in a facility or combat background thread? → `_tprint` / `_tpause` / `_tinput` (or `c_print` / `c_input` in combat). Never raw `print()` / `input()`, never create tkinter widgets off the main thread.
- **Notifications** — quest/dispatch-style flows use the **Journal + session log**, never toasts (standing user decision). Toasts are main-thread only.
- **Balance risk** — if it touches combat math or stats, plan a scripted check (`tests/_temp_*_check.py`) or a sim before declaring it done.
- **Time-system cost** — does it consume time blocks or hook `advance_time`? Does it need a Wonderland frozen-time guard?
- **Content debt** — dialogues, YAML entries, ASCII art, README, wiki rebuild. Budget this; it is usually the hidden cost.
- **Phasing** — can it ship in stages? House style: Phase 1 = core loop, Phase 2 = polish (see `dispatch_system_design.md`).

**Priority read:** Impact vs Effort vs Risk. Be honest about effort — Medium/Low ideas can wait; do not let a "quick idea" skip sections 1–3.

## 3. Write (or update) the design doc

For anything non-trivial, the project convention is a design doc **before implementation**:

- Location: `docs/<system>_design.md` (e.g. `quest_system_design.md`, `time_system_design.md`, `dispatch_system_design.md`).
- Lock the open decisions explicitly ("locked" sections); unresolved decisions are where scope creep starts.
- List phases up front and **update the doc as phases ship** — the doc is the source of truth; README/changelog only get player-facing summaries.
- Never contradict a locked decision silently — if a change is needed, update the doc and note why.

## 4. Pre-flight checklist (conventions that bite)

Before writing code, confirm each applies and how it will be handled:

- [ ] **Persistence:** new fields registered in `character.py` `ensure_player_fields()`; old saves load cleanly.
- [ ] **Notifications:** Journal + log only for quest/dispatch flows; toasts main-thread only, never from facility threads.
- [ ] **Threading:** I/O via `_tprint`/`_tpause`/`_tinput`; tkinter calls marshalled with `after()`; results returned via queues.
- [ ] **Local imports:** never import a name inside a branch if it is used elsewhere in the same function (UnboundLocalError trap — see `tests/_diag_local_imports.py`).
- [ ] **Combat parity:** anything combat-related must work for the player **and** allies (actor-based pattern for unique equipment; ally cooldowns tick in `combat/superboss_common.py` too; reinforcement loops call `reinforce_fallen_allies`; end state cleared via `end_of_combat_cleanup()`).
- [ ] **Rewards:** use shared APIs — `leveling.gain_exp` / `gain_exp_ally`; `resources/items.build_item` + `inventory.add_item_to_inventory`.
- [ ] **Display:** reuse shared formatters (`format_mastery_label`, stat-line conventions, HUD fixed widths) — never fork display logic.
- [ ] **Version/changelog:** plan the changelog bullet and whether this needs a version bump (read the bump procedure inside `version.py`).

## 5. Verify before calling it done

- Run the relevant diagnostics: `tests/_diag_*.py` (e.g. `_diag_quests.py`, `_diag_dispatch.py`, `_diag_local_imports.py`).
- Run targeted checks/sims for risky math: `tests/_temp_*_check.py`, `tests/_sim_*.py`.
- **Old-save smoke test:** load a real savefile (read-only first — do not mutate the user's saves until proven).
- Manual playtest for GUI flows (threading bugs only show up live); check the Problems panel for touched files.
- If the version was bumped: run `tests/_diag_version_consistency.py` — expect `version consistency OK`.

## 6. Record after shipping

- **Changelog:** add bullets under the current version block in `gui/screens/changelog_screen.py` (newest first; never edit old headers). Bump only per the `version.py` scheme.
- **README/wiki:** update the README section for player-facing features; regenerate `wiki/index.html` if wiki content changed.
- **Design doc:** mark shipped phases (do not delete the plan — future phases build on it).
- **Memory notes:** record new pitfalls/decisions in `/memories/repo/` so the next session doesn't relearn them.

---

## Quick reference

| Resource | Use for |
|---|---|
| `version.py` | Version scheme + bump procedure |
| `gui/screens/changelog_screen.py` | Shipped-feature history, changelog format |
| `docs/*_design.md` | Locked designs — read before proposing changes to that system |
| `.github/skills/pandemoniumhelper/` | Architecture map + full conventions/pitfalls |
| `tests/_diag_*.py` | System smoke tests |
| `tests/_temp_*_check.py`, `tests/_sim_*.py` | Targeted math/behavior verification |
