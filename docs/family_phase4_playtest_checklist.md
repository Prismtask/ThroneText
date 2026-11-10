# Family System — Phase 4 Playtest Checklist

**Version:** v0.1.9.1 — The Family We Choose
**Scope:** Shared Night, pregnancy/birth, true-born children, written variants, and the Voss & Lumen epilogue.
**Use:** Back up your save before starting. Tick each item; note the save/day if something fails.

---

## 0. Pre-flight

- [ ] Back up the save you intend to test.
- [ ] Settings → **Content level** set to `fade-to-black` for the base pass.
- [ ] Create a new save with **Family content ON** in Game Rules.
- [ ] Confirm the Family submenu appears in the house.
- [ ] Confirm the Family content choice is final for the save (no mid-game toggle).

## 1. Shared Night — base pass (`fade-to-black`)

- [ ] At **139 affection**, "Share the night" is unavailable.
- [ ] At **140 affection**, it appears during the **Night** phase.
- [ ] The scene shows three rounds, a visible mood line, and the Attunement bar.
- [ ] Tender / Playful / Bold / Shy produce match, same-family, and miss feedback.
- [ ] The action menu uses natural language (no "Tender · soft" labels).
- [ ] The ending resolves as **Together**, **Warm**, or **Quiet**; **End the night** gives **Rest**.
- [ ] Affection, stress, `shared_night`, and `beloved` behave as expected.
- [ ] The personal closing line matches the girl's own dialogue.
- [ ] The event is limited to once per night.
- [ ] A second girl cannot also initiate the same night.

## 2. Shared Night — girl-initiated

- [ ] At **159 affection**, the girl does not initiate.
- [ ] At **160+ affection**, she can initiate on Sleep at home.
- [ ] Season/moon/daily effects visibly change the chance in the diag or through repeated nights.
- [ ] At most one girl initiates per night.

## 3. Written variants

- [ ] Set Settings → **Content level** to `written`.
- [ ] Start a Shared Night.
- [ ] Each action prints the girl's signature line **followed by** a written-mode continuation.
- [ ] The ending uses a written-mode ending line.
- [ ] The scene prints **“The rest is yours.”** instead of **“(Fade to black.)”**
- [ ] Written mode remains non-graphic and closes before explicit detail.
- [ ] Switch back to `fade-to-black` and confirm the original text returns.
- [ ] Set `off` and confirm Shared Night is unavailable.

## 4. Pregnancy

- [ ] Enable family content and trigger conception (or use a test save).
- [ ] Pregnancy status shows **period 1/3** with a due day.
- [ ] Periods advance at the expected days.
- [ ] Period 3 returns the girl to the lounge and blocks combat recruitment.
- [ ] Dispatch, ascension, and awakening are blocked during pregnancy.
- [ ] Birth fires on day rollover; the mother enters **7-day recovery**.
- [ ] The **30-day conception cooldown** is set.
- [ ] The birth scene prompts for a name and the child appears in the Family menu.
- [ ] The house nesting stress bonus applies while someone is expecting.

## 5. True-born children — growth & bond

- [ ] At **15 days**, the child becomes a child-stage record.
- [ ] At **40 days**, the child becomes an adult house record.
- [ ] At **60 days**, the child reaches **prime** and aging stops.
- [ ] The Family menu shows the countdown to the next stage and to prime.
- [ ] The lounge shows **👧 Daughter** and **Bond x/100**, not hearts/Affection.
- [ ] Kiss, proposal, marriage, and Shared Night are unavailable.
- [ ] Child talk uses the mother/race pool; the starter girls use their YAML child keys.
- [ ] Child gifts give positive bond reactions.
- [ ] Father's Legacy is shown in the submenu and matches the player's race.
- [ ] Human legacy adds the chosen two attributes at adulthood.

## 6. True-born children — party & combat

- [ ] An adult child can be recruited from the lounge.
- [ ] `stage` and `prime` survive party → house round-trips.
- [ ] A minor cannot be recruited even if forced into a house record.
- [ ] The adult child uses normal Command Resonance/party limits.
- [ ] The adult child counts toward the house monster-girl cap.
- [ ] A full house leaves the adult child waiting in the Family menu.
- [ ] Dispatch rejects pregnant, recovering, and minor girls.
- [ ] Ascension/awakening reject pregnant, recovering, and minor girls.
- [ ] A true-born adult can awaken using the mother's upgraded innate kit.
- [ ] Father's Legacy combat effects apply (Dwarf HP, Elf dodge, Halfling crit, Orc low-HP damage, Gnome items, Tiefling fire/dark, Dragonborn all-element).

## 7. Toggles & time pockets

- [ ] `family_enabled` OFF allows Shared Night but never conception, birth, or growth.
- [ ] `content_level: off` disables Shared Night entirely.
- [ ] Pregnancy and growth do not advance in **Event Horizon**.
- [ ] Pregnancy and growth do not advance in **Wonderland** time pockets.
- [ ] Save/load mid-pregnancy preserves conceived day, due day, recovery, and cooldown.
- [ ] Save/load with a child preserves stage, prime, mother key, bond, and Father's Legacy.
- [ ] An old save with no family fields loads cleanly (family OFF by default).

## 8. Voss & Lumen — “The First Page”

- [ ] Complete **Grand Resonance (MQ6)** and **A Moth at the Window**.
- [ ] Enter **Skylume** and confirm the epilogue triggers once.
- [ ] The scene reveals **Lumen Quillan** and the first true-born entry.
- [ ] The `voss_epilogue_seen` flag is set.
- [ ] The Journal records **The First Page**.
- [ ] **The First Page** keepsake appears in the bag (or house storage if full).
- [ ] The keepsake has no combat power.
- [ ] Re-entering Skylume does not repeat the scene.
- [ ] Entering Skylume before both requirements does not trigger it.

## 9. Regression sweep

- [ ] Talk/gift daily limits still work.
- [ ] Marriage, wedding gifts, and wedding accessories still work for non-children.
- [ ] House income, storage, and resting still work.
- [ ] Dispatch launch/collect still works for eligible girls.
- [ ] Fireside Tales still triggers and completes.
- [ ] The combat HUD shows no missing or broken ally data.
- [ ] No new traceback appears in the console during any step.

---

## Sign-off

- **Build tested:** v0.1.9.1
- **Save/day:**
- **Result:** PASS / FAIL
- **Notes:**
