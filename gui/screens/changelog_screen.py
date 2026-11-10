"""
gui/screens/changelog_screen.py — Changelog viewer showing version history.
"""

import tkinter as tk

from gui.screens.base_screen import BaseScreen
from gui.theme import Theme

from version import IS_BETA


class ChangelogScreen(BaseScreen):
    """Scrollable changelog viewer."""

    def build_ui(self):
        self.sm.update_top_bar("Changelog")
        self.sm.clear_log()

        container = self.styled_frame(self)
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Title
        tk.Label(
            container,
            text="Changelog",
            bg=Theme.BG_DARK,
            fg=Theme.ACCENT,
            font=Theme.FONT_LARGE,
        ).pack(anchor=tk.W, pady=(0, 12))

        # Beta clarifier (pre-1.0)
        if IS_BETA:
            tk.Label(
                container,
                text="Pre-1.0 beta — features, balance, and save formats may change between builds.",
                bg=Theme.BG_DARK,
                fg=Theme.TEXT_DIM,
                font=Theme.FONT_SMALL,
            ).pack(anchor=tk.W, pady=(0, 12))

        # ── Scrollable text area ───────────────────────────────────────────────
        text_frame = tk.Frame(container, bg=Theme.BG_DARK)
        text_frame.pack(fill=tk.BOTH, expand=True)

        self.text_widget = tk.Text(
            text_frame,
            bg=Theme.BG_MID,
            fg=Theme.TEXT,
            font=Theme.FONT,
            wrap=tk.WORD,
            relief=tk.FLAT,
            borderwidth=0,
            padx=12,
            pady=10,
            state=tk.DISABLED,
            cursor="arrow",
        )
        self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(
            text_frame,
            command=self.text_widget.yview,
            bg=Theme.BG_DARK,
            troughcolor=Theme.BG_DARK,
            activebackground=Theme.BG_LIGHT,
        )
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_widget.configure(yscrollcommand=scrollbar.set)

        # ── Configure text tags for styling ────────────────────────────────────
        self.text_widget.tag_configure("version", foreground=Theme.ACCENT, font=Theme.FONT_LARGE)
        self.text_widget.tag_configure("section", foreground=Theme.ACCENT_HOVER, font=Theme.FONT_BOLD)
        self.text_widget.tag_configure("bullet", foreground=Theme.TEXT, font=Theme.FONT, lmargin1=20, lmargin2=20)
        self.text_widget.tag_configure("sub_bullet", foreground=Theme.TEXT_DIM, font=Theme.FONT, lmargin1=40, lmargin2=40)
        self.text_widget.tag_configure("italic", foreground=Theme.TEXT_DIM, font=Theme.FONT)
        self.text_widget.tag_configure("spacer", font=Theme.FONT_SMALL)

        # Insert changelog content
        self._insert_changelog()

        # ── Back button ────────────────────────────────────────────────────────
        btn_frame = tk.Frame(container, bg=Theme.BG_DARK)
        btn_frame.pack(fill=tk.X, pady=(12, 0))

        self.styled_button(
            btn_frame,
            text="Back",
            command=lambda: self.sm.go_back(),
        ).pack(side=tk.LEFT)

    def _insert_changelog(self):
        """Populate the text widget with changelog entries."""
        t = self.text_widget
        t.configure(state=tk.NORMAL)

        # Frozen history — released headers are never edited (a version's
        # contents must not change after release). On a bump: prepend a new
        # _add_version() block ABOVE this one and update version.py. The
        # newest header here must always match version.py's VERSION_DISPLAY.
        # Checked by tests/_diag_version_consistency.py.
        self._add_version("v0.1.9.0 — The Family We Choose")

        self._add_section("Combat & Dungeon Presentation")
        self._add_bullet("Superboss **intro narration** now reveals **three lines at a time** on the "
                         "combat screen — each **Continue** press shows the next page — so the boss "
                         "scene is readable without opening the combat log.")
        self._add_bullet("Wonderland **heroine endings** (Red Hood, Dorothy, Alice, and Mary Sue's "
                         "resolutions) now play on the **dungeon screen** after the battle instead of "
                         "being squeezed into the combat ticker.")
        self._add_bullet("Entering a **wild dungeon** now starts with a clean dungeon log — leftover "
                         "lines from the previous run (such as a Wonderland superboss floor) no "
                         "longer carry over.")

        self._add_section("Wonderland — Heroine Weapon Timing")
        self._add_bullet("The **Fairy Godmother** now offers Alice's **??? Blade** at **Floor 35** "
                         "instead of Floor 20, so it appears after Alice joins at Floor 31 and "
                         "before the Floor-40 Jabberwock.")
        self._add_bullet("The **Wizard of Oz** now offers Dorothy's **Silver Slippers** at "
                         "**Floor 25** instead of Floor 30, giving them a full chapter before "
                         "the Wicked Witch.")
        self._add_bullet("The **Woodcutter** now offers Red Hood's **Broken Axe** at "
                         "**Floor 15** instead of Floor 20, giving her a full chapter between "
                         "joining at Floor 11 and the Big Bad Wolf.")

        self._add_section("Deed Titles — The Wonderland Set")
        self._add_bullet("Nine **Wonderland titles** join the deed collection: **Curiouser** "
                         "(enter the realm; +1% XP), **Tea-Party Guest** (the three-guest "
                         "scene; +3% rest healing), **Shadow-Touched** (accept a Shadow; "
                         "+2% damage), and one per floor boss — **Heartsbane** (+3% dungeon "
                         "gold), **Wolf-Hunter** (+1 Strength), **Witch-Breaker** (+6% XP), "
                         "**Vorpal Hand** (+4% damage), and **Author's Bane** (+2 Learning, "
                         "+4% XP).")
        self._add_bullet("The capstone, **Happily Ever After**, unlocks when Red Hood, "
                         "Dorothy, and Alice all become permanent heroines and grants "
                         "**+1 to all attributes**. Late-arc resolutions count.")
        self._add_bullet("Unlocks fire on Wonderland entry, at the tea party, on every "
                         "Shadow choice, on each Floor 10/20/30/40/50 boss kill, and when "
                         "a heroine becomes permanent. Old saves reconcile the bosses and "
                         "heroines they already finished on load, and a save already carrying "
                         "Shadows backfills the lifetime Shadow counter.")

        self._add_section("Sylvana — The Mirror Heroine")
        self._add_bullet("Defeating the **Queen of Mirrors** now leaves a **Cracked Mirror** key "
                         "item. Existing saves that already beat her receive it on load.")
        self._add_bullet("The House menu gains **The Cracked Mirror**. Each repair restores **5%** "
                         "for **6 time blocks**, and Sylvana's response changes at every step. At "
                         "**100%** she steps out, joins at **100 affection**, and equips her unique "
                         "**Decaying Aegis**.")
        self._add_bullet("Sylvana's kit: **Null**, **Illusory Veil** (party evasion), **Hall of "
                         "Mirrors** (party damage reduction + reflection), and **Mirror Guard** "
                         "(aggro + shield + fixed pure damage to attackers). Her permanent passive, "
                         "**Queen's Grace**, gives the party **+5% evasion**. She has no Awakening.")
        self._add_bullet("Marrying Sylvana grants the **Looking-Glass Locket**, which reflects "
                         "**50%** of the first enemy hit each combat.")

        self._add_section("Equipment — Unique Element Profiles")
        self._add_bullet("Every piece of **unique equipment** now carries **one primary element**. "
                         "Hand-tuned secondary and tertiary elements are gone from the base item; "
                         "the primary is fixed and defines the weapon's damage or the armor/"
                         "accessory's resistance identity.")
        self._add_bullet("The Blacksmith's **Infuse Element** service now accepts **unique gear**: "
                         "flowers fill its **two open slots** (secondary and tertiary). Weapons gain "
                         "damage, armor gains resistance, and accessories extend whichever profile "
                         "they already carry (damage, resistance, or both). Unique names never take "
                         "a flower word.")
        self._add_bullet("**Reforge** can re-roll a unique's flower slots, but never its primary. "
                         "Old saves collapse existing multi-element uniques to their primary on load.")

        self._add_section("Unique Equipment — Moonlight Greatsword")
        self._add_bullet("**Moonlight Greatsword** joins the Guild's **Legendary Rewards**. "
                         "Claim it after defeating **3 different Super Bosses**. Its basic "
                         "attacks are **physical**, scaling with Strength and Learning.")
        self._add_bullet("**Moonlight** (action, **5-turn cooldown**): for the **next 3 rounds**, "
                         "basic attacks become **magical waves** that strike **all enemies** for "
                         "**75%** damage. The HUD shows remaining turns (**MOON×N**) and the "
                         "weapon's attack tag switches to **⚔MAG** while empowered.")
        self._add_bullet("Ally wielders can use Moonlight too — turns and cooldown are tracked "
                         "per-actor and cleared when the fight ends.")

        self._add_section("Wonderland — The Looking-Glass Road")
        self._add_bullet("\"The Looking-Glass Road\" now shows how to reach Wonderland in the "
                         "Journal's Side Quest tab: clear Floor 20 in two different biomes, buy "
                         "a Looking Glass Shard from **Veilholt's Black Market (5,000g)**, then "
                         "open the mysterious book in **Veilholt's Arcane Tower**. The quest "
                         "appears once you hold a shard, clear a Floor-20 biome, or have prior "
                         "Wonderland progress.")
        self._add_bullet("Wonderland's unlock no longer requires **Day 60**. The Veilholt book "
                         "and the Black Market shard only check the two-biome Floor-20 milestone.")

        self._add_section("Wonderland — Guest Pacing & Boss Variants")
        self._add_bullet("The Mad Hatter's tea party is empty until the Queen of Hearts falls. "
                         "Clearing Floor 10 and entering the inn reveals the three-guest scene "
                         "and invites Red Hood.")
        self._add_bullet("Heroines now arrive in strict order: Red Hood before the Floor-20 "
                         "Wolf, Dorothy before the Floor-30 Witch, and Alice before the Floor-40 "
                         "Jabberwock. Accepting a heroine arms a variant of her boss — "
                         "**Huntress's Oath**, **Emerald Road**, or **Vorpal Opening** — while "
                         "the base fight stays unchanged if she is skipped.")
        self._add_bullet("Skipping a heroine opens a **late arc** at the inn. She still becomes "
                         "permanent and keeps her full weapon-upgrade path.")
        self._add_bullet("\"Ask the Hatter about the guests\" always names the next trigger, "
                         "and the Journal's **Down the Rabbit Hole** quest now asks you to "
                         "return to the tea party after Floor 10.")
        self._add_bullet("Heroine auto-equipment now follows Wonderland depth: **common +0** "
                         "through Floor 15, **uncommon +1** through Floor 25, **rare +3** "
                         "through Floor 35, and **rare +4** beyond. The old flat common +5 "
                         "on all four pieces pushed Red Hood's effective Dexterity past 40 "
                         "at her join floor.")
        self._add_bullet("Leaving Wonderland through the Looking-Glass now reads the current "
                         "**Morning**, **Noon**, or **Night** phase — matching the top bar — "
                         "instead of the retired HH:MM clock.")

        self._add_section("Capture & Check Tuning")
        self._add_bullet("Incapacitated monster girls are now much easier to capture — the "
                         "capture roll gains **+35%** vs stunned/paralyzed girls, **+30%** vs "
                         "sleeping girls, **+25%** frozen, **+20%** entombed, **+10%** "
                         "slowed/blinded/confused, and **+5%** weakened. The total status bonus "
                         "is capped at **+50%**.")
        self._add_bullet("A stun that makes a monster girl lose her turn now leaves her "
                         "**off-balance** until her next turn, so the **+35%** stun bonus is "
                         "still active when you throw the net on the following turn.")
        self._add_bullet("Capture target menus and the capture roll now show the **exact "
                         "success chance**, including status bonuses, so it is clear why a "
                         "stunned girl is easier to catch.")
        self._add_bullet("**Stun Bomb** no longer lists 8 damage — it is a pure control item "
                         "and can never accidentally KO a low-HP monster girl you are trying "
                         "to net.")
        self._add_bullet("**Natural 20** is now an automatic success on d20 checks: dungeon "
                         "stat events, trap disarming, city-gate talk-downs, and flee attempts. "
                         "Dungeon checks and traps also treat **natural 1** as an automatic "
                         "failure, matching the pass-probability display.")

        self._add_section("Casino Games — Phases 1–3")
        self._add_bullet("Inns now keep **tavern tables**: **Under & Over** (2d6) and **Blackjack** "
                         "(Hit/Stand). Stakes are **25 / 100 / 250 gold**, with a **1,000g pot cap** "
                         "and a **1,000g daily win cap**.")
        self._add_bullet("The **Black Market back room** opens at night for players with **negative "
                         "Karma**. Stakes are **250 / 1,000 / 2,500 gold**, gated at Karma below 0 / "
                         "≤ −15 / ≤ −40 and levels 5 / 15 / 25; odds are better and the pot cap is 10,000g.")
        self._add_bullet("Both venues share a **12-hand daily limit** and cost **20 minutes per hand**. "
                         "Blackjack naturals pay **6:5**; ties return half the stake at the inn and push "
                         "in the back room. Exactly 7 is offered only where the pot cap allows.")
        self._add_bullet("Blackjack cards show their **suit** (`A♠`, `10♥`, `J♦`), and the dealer's hole "
                         "card stays **?** until you stand; each dealer hit is revealed one card at a time.")
        self._add_bullet("The back room's tables now offer **Cheat**: a DEX+CHA check vs DC 16/18/20, "
                         "capped at **70%** success. Under & Over success pays **1.30×**; Blackjack "
                         "success removes the **latest card** dealt to you. Getting caught loses the "
                         "stake, costs **2 Karma**, and bars you from every back room for **7 days**. "
                         "Two attempts per day, shared across games.")
        self._add_bullet("Karma is only charged **when you're caught**; Karma-off saves still get the "
                         "7-day blacklist. A caught cheat writes a `[CASINO]` Journal entry.")
        self._add_bullet("Back-room dealers greet you by Karma tier, and the inn/back room now have "
                         "per-city dialogue (Solmere, Ashkara, Blackwake) with generic fallbacks elsewhere.")
        self._add_bullet("Three **gambling titles** join the deed collection: **The Gambler** (win 100 "
                         "hands or record a 4,000g biggest win; **+1% casino payouts**), **Sleight-Hand** "
                         "(10 unseen cheats; **+3% Black Market discount**), and **Marked** (3 caught "
                         "cheats; **+5% Black Market discount**, **−5% shop discount**).")
        self._add_bullet("All three show the same casino record line — **hands won · biggest win · "
                         "cheats unseen · caught** — on locked and unlocked Journal cards. Old saves "
                         "backfill the counters from their lifetime casino stats; unlocks are checked "
                         "after every hand/cheat and on load.")

        self._add_section("Economy — Market Index (Phase 3)")
        self._add_bullet("Shop and black-market prices now scale with your **market index**: the higher "
                         "of your level or highest cleared floor sets a **1.0–8.5×** multiplier. "
                         "Sell prices scale with it too, so endgame loot stays valuable.")
        self._add_bullet("Kill gold is reduced by the extra loot value, keeping total gold per kill "
                         "roughly flat. **L1–5 is unchanged**; the ramp starts at L5.")
        self._add_bullet("Blacksmith services — enhancement, reforge, scrolls and fusion — are "
                         "**not** indexed; their Phase 1/2 costs stay exactly as tuned.")

        self._add_section("Combat — Text Output & Quest Notices")
        self._add_bullet("Retired the old **✦ emoji borders** from capture text and superboss gimmick "
                         "output; the long decorated lines were overflowing the 3-line combat feed.")
        self._add_bullet("**Quest, capture and unique-loot lines are now pinned combat notices.** They "
                         "ignore turn-header sweeps and the end-of-combat feed wipe.")
        self._add_bullet("At the end of a fight, the result slot lists these notices above **Leave "
                         "Battle** — quest completion, rewards, the follow-up quest, and captured girls "
                         "are no longer lost. No modal popup is used.")
        self._add_bullet("The **Combat Log popup now keeps the full fight history**. The engine's "
                         "per-round `c_clear()` only resets the compact ticker; it no longer erases "
                         "every earlier round from the log.")
        self._add_bullet("**Failed capture feedback** (net slips, no net, level-gated net, "
                         "non-capturable target) is treated as an action result: it stays readable "
                         "through the next turn header and in the full log, but no longer pins itself "
                         "over the result. The end-of-battle ticker is cleared so VICTORY/DEFEAT "
                         "always owns it.")
        self._add_bullet("The combat feed now keeps **all action results** — damage, item use, heals, "
                         "failed effects — readable across the next turn header; the new combatant's "
                         "first action then sweeps them. Item-use lines lead with **“You use <item>.”** "
                         "so the ticker/log shows what was used.")
        self._add_bullet("The two-column **combat item picker** pads an odd item count with a blank "
                         "placeholder row, so both columns have the same row count and scroll in "
                         "lockstep. The placeholder cannot be selected or confirmed.")
        self._add_bullet("**Legacy text menus no longer leak into the combat log.** Choosing an item "
                         "(player or ally), picking a capture net, or opening the ally switch roster used "
                         "to dump the whole numbered list into the ticker and log. The GUI already draws "
                         "those panels from live state, so the engine now skips the duplicate list "
                         "(terminal mode still prints it). Only the result line — e.g. “You use Health "
                         "Potion.” — reaches the log.")
        self._add_bullet("The same cleanup covers the **ally / party / revive target rosters** printed by "
                         "skills and ally skills, and the **blacksmith** enhancement, scroll and fusion "
                         "lists, which showed every item twice (once as text, once as a button). Lists that "
                         "still carry information the buttons lack — shop multi-sell, house storage, guild "
                         "bounties, the house roster — are unchanged.")
        self._add_bullet("Player class skills now tag their damage lines with **`(CRITICAL!)`** — "
                         "`hundur [Execute] → Night Stalker: 243 dmg (CRITICAL!) [PHYSICAL]` — matching "
                         "ally and enemy attacks. The separate **Critical hit!** line stays, but a skill "
                         "crit no longer loses the tag (Execute and every other player skill).")

        self._add_section("Combat — Superboss Presentation")
        self._add_bullet("All **16 superbosses** (Wolf, Black Silence, Broodmother, Chrysalis, Everlong "
                         "Ship, Ignis, Jabberwock, Mary Sue, Palette, Queen of Hearts, Rientrante, "
                         "Slitcurrent, Sylvana, White Knight, Wicked Witch, Yinglong) share one combat "
                         "loop. That loop now prints the **standard round header** — `>> ROUND 2 | Floor "
                         "12 | 🌤 Noon ▮▮▮▮▮▮▮▯` — so the combat top bar shows the floor and the current "
                         "time again instead of a bare `ROUND 2`, and the action phase line matches the "
                         "normal engine (`⚔️ ROUND n: ACTION PHASE`).")
        self._add_bullet("Combat headers now show the **phase track** (`☀ Morning ▮▮▮▮▮▮▮▯`) instead of "
                         "the retired HH:MM clock — the same morning/noon/night reading as the top bar, "
                         "in normal fights *and* superbosses.")
        self._add_bullet("**Gimmick banners are pinned in the message strip.** `⚙ [GIMMICK] …`, "
                         "`[PHASE 2] …` and `[FINAL FORM] …` now own a row of the combat ticker and are "
                         "mirrored to the session log, so \"Mirror Reflection — the copies bear subtly "
                         "wrong names\" no longer scrolls past before you can read it. The banner clears "
                         "when the fight ends.")
        self._add_bullet("**Old `===` / `!!!` / `───` / `~~~` banners are gone** from every superboss "
                         "module, and the combat bridge drops any divider line it still receives — each "
                         "one used to eat a row of the 3-line strip for no information.")

        self._add_section("UI — Party Cards")
        self._add_bullet("Every member box on the city party card now gets a **fixed width/height "
                         "sized for a full 8-actor party**; short names no longer produce smaller "
                         "cards, and a 2-member party keeps the same box size instead of stretching "
                         "across the row.")
        self._add_bullet("Long player names/titles and ally nicknames are **width-aware ellipsized** "
                         "(e.g. `prism the Ab…  Lv.50`) so the single-row party bar can no longer overflow "
                         "the card or window edge. The level suffix is always preserved.")

        self._add_section("UI — Time Display")
        self._add_bullet("Absolute **Day N** stamps are gone from player-facing text: bounty-board "
                         "refreshes, dispatch returns, pregnancy due dates, recovery timers, and "
                         "dispatch-offer refreshes now read **today / tomorrow / in N days**.")
        self._add_bullet("Fixed active bounties showing **EXPIRED** on their final day; the deadline "
                         "day is still valid and matches the Guild Hall's turn-in rules.")

        self._add_section("Allies — Late Bloomer Growth")
        self._add_bullet("Late-bloomer bonus points are now **chosen during level-up** instead of "
                         "being auto-assigned to the girl's highest attribute. Each bonus point opens "
                         "the same attribute picker as the normal level-up, labeled **Late Bloomer "
                         "bonus**.")

        self._add_section("Combat — Human Elemental Traits")
        self._add_bullet("**Human enemies now have a natural damage type** instead of a blank "
                         "elemental profile: martial humans (Bandit, Elite Assassin, City Guard, ...) "
                         "attack **physical**, while caster names (Novice Mage, High Mage, Cultist, ...) "
                         "attack **magical**. The HUD now shows `⚔PHY` / `⚔MAG`.")
        self._add_bullet("The fallback uses a **1.2× baseline** and feeds the elemental-debuff "
                         "channel (physical → bleed, magical → confusion). Existing race/keyword "
                         "traits (Gnome thunder, Undead dark, Dark Knight dark, Blade Dancer physical) "
                         "are unchanged.")

        self._add_section("Event Horizon — Unlock Fix")
        self._add_bullet("The Event Horizon no longer opens on a **failed Floor 20 clear**. The "
                         "world-map site, Vesper's first-contact scene, and the whole rift now "
                         "require **Floor 20 to be cleared** (`max_floor` 21+). Reaching Floor 20 "
                         "and dying to its superboss leaves the rift locked until you win.")
        self._add_bullet("Saves already introduced to Vesper or holding rift progress stay "
                         "unlocked — the fix never takes the site away mid-run.")

        self._add_section("UI — World Map")
        self._add_bullet("Deselecting a highlighted route no longer leaves a **green trail over "
                         "city boxes and ruin markers** — route lines keep their original stacking "
                         "order, so the map returns to its exact pre-selection look.")

        self._add_section("Economy — Reforge (Phase 2)")
        self._add_bullet("The Blacksmith can now **reforge one elemental infusion**: the element is "
                         "re-rolled while its value (weapons) or tier (armor/accessories) is kept. "
                         "The fee is **40× the item's value**, paid before the roll — keeping the old "
                         "element does not refund it.")
        self._add_bullet("This gives gold a **repeatable endgame sink** after enhancement and "
                         "scrolls cap out. Uniques cannot be reforged; the piece must already have "
                         "an infusion.")

        self._add_section("Economy — House & Scroll Pacing (Phase 1)")
        self._add_bullet("**House passive income** now scales as 1 + min(3, floor/15) (capped at 4×) "
                         "instead of floor/3. The house screen shows the exact daily rate you "
                         "collect — no hidden upkeep.")
        self._add_bullet("House income is now banked for at most **5 days** (was 10). Saves with "
                         "more than 5 days banked lose the excess once on collection.")
        self._add_bullet("**Scroll of Fusion** craft costs are now value-derived: **2,000 / 2,800 / "
                         "4,400 / 8,000 / 16,000 gold** (legendary was 80,000). The four-item fodder "
                         "remains the real gate.")

        self._add_section("Deed Titles — Worldbreaker Fix")
        self._add_bullet("**Worldbreaker** now grants **+2 to all attributes** instead of +2 Strength, "
                         "matching its original design. It remains the T4 completion title with a "
                         "visible **−10% shop discount** drawback.")
        self._add_bullet("**Stormbreaker** remains a fixed **+2 Strength** reward for three superbosses; "
                         "the two endgame titles now have distinct effects.")

        self._add_section("Deed Titles — Phase 3")
        self._add_bullet("Five endgame titles arrive: **Stormbreaker** (+2 Strength after three "
                         "superbosses), **Abyss Walker** (+6% XP after reaching Event Horizon room "
                         "50), **Collector** (+2 Learning and +5% XP for 80% Bestiary completion), "
                         "**Worldbreaker** (+2 Strength, but a visible −10% shop discount), and "
                         "**First Page** (+10% rest healing after the Voss epilogue).")
        self._add_bullet("Worldbreaker is the first title with a **visible drawback** — its power "
                         "is shown up front and the trade-off is real, never hidden.")
        self._add_bullet("New condition support: Event Horizon depth, Bestiary completion, and "
                         "quest-runtime flags. Title-aware NPC greetings now appear when entering "
                         "city services.")
        self._add_bullet("The collection now holds **19 titles**; locked cards still show `???` "
                         "with hints and progress, and every unlock writes a `[TITLE]` Journal entry.")

        self._add_section("Deed Titles — Phase 2")
        self._add_bullet("Five more titles join the collection: **Dragon-Slayer** (+1 Strength), "
                         "**Contracted** (+5% bounty gold), **Hearthkeeper** (−5% monthly bills), "
                         "**Honest** (+5% shop discount), and **Unrepentant** (+5% Black Market "
                         "discount).")
        self._add_bullet("Combat integration is now player-only and title-aware: the equipped "
                         "title can add a small attribute or damage bonus, and combat HUD cards "
                         "show the compact honourific without changing name matching or fixed "
                         "widths.")
        self._add_bullet("Economy hooks: bounty payouts, monthly upkeep, and Black Market prices "
                         "all read the equipped title. Karma and family titles stay unavailable "
                         "when their Game Rules toggle is off.")
        self._add_bullet("Old saves backfill the new titles on load; unlock conditions are checked "
                         "against existing bestiary, bounty, house, and Karma state.")

        self._add_section("Deed Titles — Phase 1")
        self._add_bullet("Deeds now leave a **title** behind. Nine titles unlock from play — "
                         "first kills, floor clears, travel, shop spending, and captures — and "
                         "are collected in **Inventory → Journal → Titles**.")
        self._add_bullet("**One title may be equipped at a time.** The equipped title appears "
                         "after your name (e.g. *Aria the Roadwarden*); a Settings toggle can "
                         "hide the honourific.")
        self._add_bullet("Locked titles show as **???** with a hint and, where countable, "
                         "progress (e.g. `Floors Cleared: 3 / 25`). Unlocking reveals the name "
                         "and effect and writes a `[TITLE]` entry to the Journal's Event tab.")
        self._add_bullet("Swap titles freely at any safe point — city, house, camp, or the "
                         "dungeon/Event Horizon post-room menu. Titles are locked during combat.")
        self._add_bullet("Effects are small and never stack: travel time, shop discount, XP, "
                         "capture chance, and dungeon gold, each capped. Old saves backfill "
                         "titles they have already earned on first load.")

        self._add_section("Enemy Roles & Spawn Composition")
        self._add_bullet("Regular enemies now have an explicit combat role — attacker or supporter. "
                         "Supporters prioritise healing and only occasionally use damaging skills; "
                         "attackers never spend turns healing.")
        self._add_bullet("Dungeon and Event Horizon rooms now compose encounters by role: early rooms "
                         "are overwhelmingly attackers, support becomes more common with floor "
                         "depth, groups cap at two supporters, always keep an attacker, and a lone "
                         "enemy is always an attacker. Bounties still weight their role slot.")
        self._add_bullet("Roles are inferred from enemy names, races and abilities, and designers can "
                         "override them with role: attacker / role: supporter in enemy data.")

        self._add_section("Dream Events — Phase 1")
        self._add_bullet("Sleep can now bring a **dream**: a 20% chance per night at your house, "
                         "at any inn, or at camp. Boon dreams grant XP, a small item, a wink of "
                         "luck, or the new **Dream-Blessed** buff (+1 all attributes for 2 rooms); "
                         "burden dreams take a little gold (capped at 5% or 50g), raise party "
                         "stress, or leave only a warning you can't quite remember.")
        self._add_bullet("Dreams never remove items, stats, or levels, and never chain two "
                         "burdens in a row. A run of dreamless nights slowly raises the chance "
                         "(soft pity); Wonderland and Event Horizon nights never dream.")
        self._add_bullet("**Dream-Blessed** merges with Well-Rested and Shared Night instead of "
                         "stacking, and wears off as you clear dungeon rooms. The HUD tags it "
                         "**DRM**.")
        self._add_bullet("Every dream is written to the Journal with a **[DREAM]** tag.")
        self._add_bullet("**Choice dreams** can now find you (**The Offered Hand**, **The Accord Echo**, "
                         "**The Mirror Self**, **The Feast**). Each option shows its trade-off — "
                         "a buff or XP at the cost of stress, rest versus affection — and the "
                         "choice you made is recorded in the Journal.")
        self._add_bullet("Dreams you have had before now offer a **Skip** — let the dream go "
                         "without taking anything from it.")
        self._add_bullet("**Story dreams** now arrive on their own schedule: the first night you "
                         "do not sleep alone, the lamp of an expected child, the Archive's "
                         "rain-soaked library, and something counting your pulse in the walls. "
                         "They never repeat and can set story flags.")
        self._add_bullet("The Journal gains a **Dreams** tab (Inventory → Journal → Dreams): "
                         "every dream you have had, re-readable, with how often it found you.")
        self._add_bullet("Where you sleep now shapes the dream: **The Hearth's Song** and "
                         "**The House Remembers** only come at your house, **The Road's Patience** "
                         "only at camp, and **The Rented Room** only at inns.")
        self._add_bullet("The **wiki** has a new **Dreams** page (every dream, its trigger and its "
                         "numbers), and the Player Guide now covers Dreams plus the day-block, "
                         "sleep, fatigue and stress rules.")

        self._add_section("Time — Player Stress")
        self._add_bullet("Skipping a night now builds **Stress** instead of instantly adding fatigue: "
                         "**+50 per unslept day**, shown in every top bar (e.g. `STRESS 50`). A full "
                         "meter — two skipped nights — converts into **one fatigue stack**, so real "
                         "exhaustion has to be earned.")
        self._add_bullet("Only a real sleep (home bed, inn Sleep, camp) clears stress. Wonderland and "
                         "Event Horizon nights accrue nothing; Pandemonium still accrues.")
        self._add_bullet("At **67+** stress you are **Rattled** (👁 marker): hallucinations gain a tier "
                         "and can find you even without exhaustion — a Nightmare can follow you into "
                         "the dark.")
        self._add_bullet("Burden dreams feed the meter: Nightmare **+34**, Restless **+20**.")
        self._add_bullet("A companion falling in combat is now the second big source: **you +34** "
                         "stress per fall, the fallen girl **+34**, and everyone who saw it **+20**. "
                         "Three falls in a run is a fatigue stack.")
        self._add_bullet("Companions have their own stress teeth: **Weary (50+)** −1, "
                         "**Frayed (75+)** −2 and **Burned Out (90+)** −3 to all attributes in "
                         "combat (`WEA` / `FRY` / `EXH` HUD tags), and Burned Out girls refuse to "
                         "fight that encounter — with something to say about it.")
        self._add_bullet("A real sleep now also settles the party's nerves: **−10 companion "
                         "stress** each.")

        self._add_section("Family Content — Written Variants")
        self._add_bullet("`Content level: written` now adds a more intimate prose layer to "
                         "Shared Night actions and endings. Every girl keeps her signature "
                         "line first; the written pool follows it and replaces the generic "
                         "ending with a closer, more detailed one.")
        self._add_bullet("Written mode remains **non-graphic**: it closes before explicit "
                         "detail. `fade-to-black` stays the default, and `off` still disables "
                         "Shared Night entirely.")
        self._add_bullet("The scene now prints **“The rest is yours.”** in written mode instead "
                         "of the fade-to-black marker.")
        self._add_bullet("Dialogue pools widened: 8 generic lines per tone, 6 ending lines per "
                         "tier, 12 random beats, and 4–5 written lines per tone/ending, on top "
                         "of each girl's signature line.")
        self._add_bullet("Family scene text now lives in `resources/family_scenes.yaml`; "
                         "`resources/family_scenes.py` is a loader. Dialogue can be tuned "
                         "without editing Python.")
        self._add_bullet("`shared_night` and `beloved` now tick per dungeon room instead of "
                         "per combat round: the MC keeps +1 all attributes and the girl keeps "
                         "+2 to her primary attribute for two rooms.")
        self._add_bullet("The HUD labels the merged Shared Night buff **SHR**, beloved **BLV**, "
                         "and ordinary bed rest **RST**, so the night buff is no longer hidden "
                         "behind RST.")

        self._add_section("Family System")
        self._add_bullet("A new optional family layer: an opt-in **Game Rules** toggle "
                         "(`Family content`, final per save) plus the global **Content level** "
                         "setting (`off` / `fade-to-black` / `written`). The system gates "
                         "pregnancy, birth, and growth; Shared Night itself follows the content "
                         "setting.")
        self._add_bullet("**Shared Night** is a three-round Attunement scene with a visible "
                         "mood each round. Hold her close, play along, take the lead, or whisper; "
                         "exact matches score +2, the same energy family +1, and a clash +0. "
                         "Endings are Together, Warm, Quiet, or Rest.")
        self._add_bullet("Every capturable monster girl and the three Wonderland heroines now "
                         "have a signature line for each tone, overlaid on the generic pool, plus "
                         "her own personal closing line from her house dialogue.")
        self._add_bullet("**Pregnancy** runs 30 days in three 10-day periods; the third period is "
                         "lounge rest, followed by 7-day recovery and a 30-day conception cooldown. "
                         "Birth, naming, and conception pity are wired into the day rollover.")
        self._add_bullet("**True-born children** grow by total age — infant → child at 15 days, "
                         "adult at 40, prime at 60 — and inherit their mother's race, innate skills, "
                         "and race passive plus a weakened **Father's Legacy** from your race.")
        self._add_bullet("Daughters use a 100-point **Bond** instead of romance affection. The "
                         "lounge labels them **Daughter**, hides kiss/proposal/night actions, and "
                         "uses daughter-specific talk and gift pools. Adults count toward the house "
                         "cap and join the party through the normal recruitment/resonance flow.")
        self._add_bullet("Pregnant, recovering, and underage girls are blocked from dispatch, "
                         "ascension, and awakening. True-born adults awaken using their mother's "
                         "upgraded innate kit.")

        self._add_section("Voss & Lumen — The First Page")
        self._add_bullet("After **Grand Resonance** and **A Moth at the Window** are complete, "
                         "entering Skylume delivers a one-time Star Tower epilogue. It reveals "
                         "Lumen Quillan's history and the Archive's first true-born entry, and "
                         "grants **The First Page** keepsake (no combat power).")

        self._add_section("Affection Ladder v2")
        self._add_bullet("Base affection cap is now **200**; engaged and married girls cap at "
                         "**300**. Awakening now requires **200** affection, and the wedding gift "
                         "arrives at **300**. Shared Night gates are **140** (you initiate) and "
                         "**160** (she initiates).")

        self._add_version("v0.1.8.8 — The Distant Journey")

        self._add_section("Karma — One Standing Score")
        self._add_bullet("City Favor has been removed. **Karma** is now the only "
                         "standing score, so the same reputation follows you to every "
                         "shop, guild hall, gate, and port. Old saves keep their favor "
                         "data, but it is no longer read or displayed.")
        self._add_bullet("Guild bounties now scale with Karma: high Karma draws harder "
                         "contracts with richer gold rewards, while low Karma keeps the "
                         "board at its minimum and pays less. Karma-off saves use "
                         "level-scaled contracts.")
        self._add_bullet("Shops and blacksmiths use Charisma + Karma only. With Karma off, "
                         "Charisma alone sets prices.")
        self._add_bullet("Dispatch reports grant gold, items, and EXP only. The New Moon "
                         "Festival now grants +25% bounty gold instead of favor.")

        self._add_section("Seasons & Weather")
        self._add_bullet("The calendar now has four 30-day seasons — Spring, Summer, "
                         "Autumn, and Winter — cycling with the months. The season is "
                         "shown beside the day in the top bar and time dialogs.")
        self._add_bullet("Weather rolls from a season-weighted table: rain in Spring, "
                         "snow in Winter, fog in Autumn. A weather day replaces the "
                         "Morning/Noon/Night icon with its own glyph while the phase "
                         "word stays visible.")
        self._add_bullet("Weather now costs travel blocks exactly once: light weather "
                         "+1 block, heavy weather +2, per hop. Heavy Rain no longer "
                         "double-charges as both a 30% time multiplier and extra blocks.")

        self._add_version("v0.1.8.7 — The Distant Journey")

        self._add_section("Karma — Phase 3 Polish")
        self._add_bullet("Low Karma now sharpens fatigue hallucinations and high Karma "
                         "softens them by one instability tier at ±50 (still requiring "
                         "at least two fatigue stacks). Wonderland keeps its existing rules.")
        self._add_bullet("Receptionists, shopkeepers, blacksmiths, guild clerks, portmasters, "
                         "gate guards, and Blackwake innkeepers now react to your Karma tier. "
                         "Blackwake has its own outlaw-versus-saint lines.")
        self._add_bullet("Travel can present a stranded traveler: help for +2 Karma, rob them "
                         "for gold and −3 Karma, or walk away. The event is hidden when Karma "
                         "is off.")
        self._add_bullet("Blackwake offers a 50-gold smuggler's ferry berth to outlaws, and "
                         "Black Markets stock a sealed outlaw crate at −25 Karma or lower.")
        self._add_bullet("The Stats & Equipment tab now shows your Karma tier, its shop and "
                         "bill effects, and your three most recent Karma changes.")

        self._add_version("v0.1.8.6 — The Distant Journey")

        self._add_section("Karma — Phase 2 Consequences")
        self._add_bullet("Low Karma now meets you at the city gate. A one-time warning "
                         "comes first; after that, Suspect entries demand a fee, while "
                         "Wanted and Outlaw entries offer pay, talk-down, submission, or a "
                         "non-lethal guard fight. Turning away leaves the gate unresolved.")
        self._add_bullet("City guards scale to your level and never grant XP, loot, "
                         "bestiary entries, captures, or quest credit. Victory or paying "
                         "opens the city; defeat or submission sends you to jail instead "
                         "of the death screen.")
        self._add_bullet("Jail clamps the fine, advances to the next morning, heals the "
                         "party to 50%, and marks you watched. Serving time grants "
                         "**+3 Karma** once every 3 days, sharing the +8/day cap.")
        self._add_bullet("Atonement paths are open: the temple's **Act of Contrition** "
                         "restores 1 Karma per 50 gold toward 0, and guilds offer a weekly "
                         "**Atonement contract** worth +5 Karma. Both share the daily cap.")
        self._add_bullet("Blackwake, Wonderland, and Event Horizon runs never trigger the "
                         "gate. Gate checks run once per travel/menu arrival, so dungeon "
                         "and facility returns are safe. The Game Rules step now treats the "
                         "Karma choice as final for the save.")

        self._add_version("v0.1.8.5 — The Distant Journey")

        self._add_section("Karma — Phase 1 Core")
        self._add_bullet("New characters now choose **Karma** in a new **Game Rules** step "
                         "during character creation (on by default). The step is ready for the "
                         "family-system toggle and future difficulty rules. Karma is locked per "
                         "save; existing saves keep it off for now.")
        self._add_bullet("Dungeon events now ask how you treat the wounded, the dead, and wild "
                         "beasts: help, bury, and calm for positive Karma — or rob, loot, and "
                         "ambush for gold and negative Karma. A new **Forgotten Shrine** offers a "
                         "blessing for 50 gold or a theft of its offerings.")
        self._add_bullet("High Karma lowers shop and blacksmith prices, monthly upkeep, and waives "
                         "Tax Day; low Karma raises them, but earns a discount at the Black Market. "
                         "With Karma off, the classic Charisma + City Favor pricing returns.")
        self._add_bullet("Duplicate captures now offer a licensed broker (standard gold), a "
                         "slaver (+60% gold, −5 Karma), release (+1 Karma), or bonding. A full "
                         "house now offers broker, slaver, or release instead of losing the capture.")
        self._add_bullet("The Prescript Ledger's combat-local **Karma** display is now "
                         "**Prescript Debt** (`DBT`), so it is not confused with the new moral axis.")

        self._add_version("v0.1.8.4 — The Distant Journey")

        self._add_section("Enemy AI Behaviors")
        self._add_bullet("Regular enemies now choose between basic attacks, single-target skills, "
                         "AoE skills, heals and AoE heals instead of always swinging once. Kits "
                         "come from race and level, so low-level mooks stay simple while veteran "
                         "enemies unleash themed attacks like Goblin Firebomb, Orc Cleave and "
                         "Dragonkin Breath Weapon.")
        self._add_bullet("Enemy cunning now scales with monster level: levels 1–4 only basic "
                         "attack and heal, single-target skills unlock at level 5, AoE skills at "
                         "level 10, and level 20+ / 35+ enemies use their kits more often and "
                         "manage healing earlier.")
        self._add_bullet("Enemies do not hand-pick the weakest party member. The AI only chooses "
                         "the action — the existing weighted target selection still decides who "
                         "gets hit, so enemies cannot focus-fire low-HP actors.")
        self._add_bullet("Support enemies are recognised by role names — Goblin Shamans, "
                         "Infernal Priests, Swamp Witches, Oracles and Alchemists mend themselves "
                         "or their most wounded ally, and the stronger healers can restore the "
                         "whole enemy group.")
        self._add_bullet("Skills use cooldowns and normal resistance/dodge rules; AoE skills "
                         "cannot be dodged but hit each party member for reduced damage. Monster "
                         "girls never use AoE so capture nets stay viable, and superbosses / "
                         "scripted floor bosses keep their existing behaviours.")

        self._add_version("v0.1.8.3 — The Distant Journey")

        self._add_section("Fireside Tales — House Stories")
        self._add_bullet("Your house menu now holds a storybook. Fireside Tales are multi-part "
                         "side stories about the household — romance, lore and quiet nights in — "
                         "unlocked by who lives with you and how close you are.")
        self._add_bullet("Requirements are shown in the book: a number of girls at a minimum "
                         "affection, a featured girl or designated allies, a married companion, a "
                         "house level, a quest flag, or a defeated superboss. Locked entries tell "
                         "you exactly what is still missing.")
        self._add_bullet("Eight arcs ship now: The Lucky Coin (Goblin Girl), Wind at the Window "
                         "(Harpy Scout), Hoof and Wing (Harpy + Centaur pair), A Shape of Her Own "
                         "(Slime Girl), Small Hours (ensemble household), A Moth at the Window "
                         "(Archive lore), The Eighth Color (Palette) and The Last Oath (the White "
                         "Knight). Parts are read in order, grant affection/stress/XP/gold, and "
                         "can be re-read once complete.")
        self._add_bullet("Some stories wait for a kill instead of an item: defeating Palette, the "
                         "Chromatic Artisan unlocks The Eighth Color (with Palette's later parts "
                         "requiring them in your household), and defeating the White Knight "
                         "unlocks The Last Oath. Old saves are credited from each boss's own "
                         "defeat flag.")
        self._add_bullet("Some stories find you while travelling instead of waiting at home — "
                         "A Moth at the Window begins when you enter Skylume after meeting Voss. "
                         "Read parts are recorded as [STORY] entries in the Journal's Event tab.")

        self._add_version("v0.1.8.2 — The Distant Journey")

        self._add_section("Wonderland Quests")
        self._add_bullet("Wonderland now has its own Journal side-quest chain. Step through the "
                         "mysterious book to open \"Down the Rabbit Hole\"; \"The Storybook Road\" "
                         "follows the dungeon's floor milestones, and \"The Author's Last Page\" "
                         "tracks the five Wonderland superbosses from the Queen of Hearts to Mary Sue.")
        self._add_bullet("\"The Looking-Glass Road\" now tracks how to reach Wonderland before you "
                         "step through: clear Floor 20 in two city dungeons, reach Day 60, buy a "
                         "Looking Glass Shard from Veilholt's Black Market (5,000g), then open the "
                         "mysterious book in Veilholt's Arcane Tower.")
        self._add_bullet("Alice, Red Hood and Dorothy each receive a Journal arc once you meet them "
                         "at the Mad Hatter's tea party — from that first conversation, through "
                         "recruitment, to the personal superboss that makes them permanent. Quest "
                         "objectives resolve from your existing Wonderland state, so saves that "
                         "already went down the rabbit hole catch up on their next city visit.")
        self._add_bullet("Quest rewards for the new arcs are XP and gold; the Wonderland boss "
                         "drops and heroine weapon chains are unchanged.")

        self._add_section("Armor & Accessory Resistance Slots")
        self._add_bullet("Armor and accessories now hold up to three infused elements, each "
                         "with its own three-tier resistance track. A new flower fills the "
                         "next slot; a fourth distinct flower replaces the third, keeping the "
                         "first two. The first slot names the piece and owns the form's "
                         "drawback — slotting an element that resists that drawback covers "
                         "the weakness, so endgame gear is no longer locked to one defence.")
        self._add_bullet("Accessories keep their form's stat identity through every infusion. "
                         "Flowers now add or merge elemental resistance instead of re-attuning "
                         "the accessory to the element's stat affinity.")
        self._add_bullet("A weapon's primary element also powers matching skills, not only "
                         "basic attacks and its trait. Examine now says so, and secondary/"
                         "tertiary elements are called out as skill boosts.")

        self._add_section("Mage Skill Rework — Time Warp & Cataclysm")
        self._add_bullet("Time Warp now unlocks at Level 20 (Elemental Focus moves to Level 12). "
                         "Casting Time Warp is now a free action: it still reduces every skill "
                         "cooldown by 2 turns, then the action menu immediately reopens so you act "
                         "again in the same turn. Its own cooldown is clamped to at least 1 turn so "
                         "it can never be chain-cast.")
        self._add_bullet("Cataclysm is no longer one massive Fire hit. It now unleashes seven "
                         "strikes, one for each element — Fire, Water, Thunder, Wind, Earth, Light "
                         "and Dark — spread round-robin across living enemies. Each strike uses its "
                         "own resistance check; the Fire strike still applies Inferno. Mastery "
                         "upgrades that burn to Conflagration, but seven hits is the cap.")
        self._add_bullet("The combat skill menu now shows Cataclysm's [MULTI] tag, and the web wiki "
                         "reflects the updated Mage ladder.")

        self._add_version("v0.1.8.1 — The Distant Journey")

        self._add_section("Rarity, Grade & Flowers — Audit Patch")
        self._add_bullet("The hard grade ceiling is gone. Rarity is now a soft ceiling: an epic "
                         "rolled on grade 1 survives 60% of the time, a legendary 15%; on grade 2 a "
                         "legendary survives 40%; grade 3 is unrestricted. A Legendary Ember or "
                         "Legendary Blaze can finally drop — rarely — instead of being silently "
                         "demoted, and treasure rooms at low floors stop being 100% rare.")
        self._add_bullet("Scrolls no longer refuse to finish a rarity above a grade's old ceiling. "
                         "The blacksmith's \"Temper it to a higher grade first\" refusal is gone, and "
                         "so is the matching silent failure in the inventory fusion path. Tempering, "
                         "scrolling and enhancing now stack in any order.")
        self._add_bullet("City shops never stock a legendary below grade 3; late-game shops get "
                         "fresh stock under the new rule. Road and dungeon merchants were already "
                         "epic-capped.")
        self._add_bullet("Tempering gold now scales with rarity — a legendary grade-up costs ×4 "
                         "the common price — so preserving a legendary's value isn't free.")
        self._add_bullet("Blacksmith: Forge Commission (Order a Base). Pick a form and an element, "
                         "pay one flower of that element plus gold, and receive a common "
                         "base-form piece of exactly that shape. Rarity stays drop/scroll "
                         "territory, so the chase is preserved while a specific base becomes "
                         "obtainable on purpose.")
        self._add_bullet("Flowers now transmute 3:1 at the blacksmith: three blooms of one element "
                         "become one bloom of another, free of charge. A farming streak in the wrong "
                         "biome can always be converted into the flower your build actually needs.")
        self._add_bullet("Dungeon loot follows the run, not the map pin: wild ruins and world-map "
                         "dungeons roll their own biome's elements and flowers instead of the "
                         "origin city's.")
        self._add_bullet("Trap caches, wandering-monster drops, the rose-painting cache and the "
                         "Cheshire Cat's gift now use the same grade-gated loot pipeline as every "
                         "other dungeon drop — no more floor-1 grade-3 surprises or rarity-tagged "
                         "flowers.")

        self._add_section("Flower Infusion Rework — Grade Retired")
        self._add_bullet("Equipment no longer has grades. Every drop is a base form — 29 weapon "
                         "shapes, 16 armor, 17 accessories — and rarity is the only power roll, "
                         "compressed to ×1.0–1.4 so a legendary is stronger without being another "
                         "game. Enhancement adds stats only; elemental power is no longer "
                         "multiplied by rarity or enhancement.")
        self._add_bullet("Flowers set the element. The blacksmith's new Infuse Element service "
                         "works one flower into a piece: the same flower strengthens that "
                         "element's slot, a new flower adds one. Weapons hold three elements — "
                         "primary up to 1.48 with the trait at 1.25/1.35/1.48, secondary up to "
                         "1.20, tertiary up to 1.15. Armor and accessories hold one element with "
                         "a three-tier resistance track; accessories re-attune their stats to "
                         "the element.")
        self._add_bullet("Item names now read the flower tier: Ember → Blaze → Inferno for "
                         "fire, and each element's own three words otherwise. A piece's name "
                         "moves to the next word at 1.25 (tier II) and 1.40 (tier III); an "
                         "uninfused drop is just its form — Common Greatsword.")
        self._add_bullet("Unique weapons keep their hand-written names and state their element "
                         "in Examine instead: “This weapon causes Dark damage "
                         "(×1.35 | Leech II).” The popup already listed the equip effect; "
                         "now it also says what the weapon actually strikes with.")
        self._add_bullet("Flowers finally have their own Bag tab with live counts — “Flowers "
                         "(12)” — listed in element order, so you can see at a glance how many "
                         "of each bloom you hold instead of digging through Key Items. The "
                         "Bag also rebuilds when you open it, so loot from the run you just "
                         "finished is there.")
        self._add_bullet("Dungeon loot carries its region's craft signature: the favoured "
                         "weapon and armor forms drop three times as often, and the dungeon "
                         "header now names them (volcanic → axes, hammers and plate; forest "
                         "→ bows, spears and leathers).")
        self._add_bullet("Flower drops now follow the fight too: 60% of flowers match the "
                         "defeated enemy's own attack element, the other 40% follow the "
                         "region's weights — fire creatures feed fire flowers even in a "
                         "tundra run. Neutral foes and room caches stay purely regional.")
        self._add_bullet("Every element now has a proper trait ladder. Fire's "
                         "Burn->Conflagration line has company: Sunder, Douse, Chain, Swift, "
                         "Bulwark, Purge, Leech and Pierce each gain three infusion tiers "
                         "(previously only fire scaled).")
        self._add_bullet("Tempering is retired. Existing grid gear migrates automatically on "
                         "load to its base form plus the element it carried (save formula v4), "
                         "keeping rarity and enhancement.")
        self._add_bullet("Forge Commission now forges the base form and works in your chosen "
                         "flower; city shops never stock legendaries (epic is the ceiling).")
        self._add_bullet("Enhancement is capped by rarity: +5 common, +6 uncommon, +7 rare, "
                         "+8 epic, +10 legendary (uniques keep +5). A common piece can no "
                         "longer ride a flat +10 past the whole rarity curve.")
        self._add_bullet("Unique weapons are standardized: each carries one primary element "
                         "at infusion tier II (1.35) and gains that element's trait II, and "
                         "unique stat totals are budgeted at +5 — 32 weapon, 33 armor, "
                         "26 accessory — with the old hidden +5 bonus removed. Gimmicks and "
                         "specials carry their identity; raw stats no longer dwarf maxed gear.")
        self._add_bullet("Enemies now deal exactly the element they advertise: each one carries "
                         "a single damage element that drives both its attacks and its "
                         "elemental debuff proc, instead of extra damage entries that never "
                         "contributed. Resistances stay multi-element.")

        self._add_section("Combat UI")
        self._add_bullet("The combat screen finally holds still: the action panel keeps one fixed "
                         "height whether your turn fills one row of skills or two, whether cooldowns "
                         "are recharging or quiet, and whether you or an ally is acting. Cooldown "
                         "lists also wrap at the panel's real width now instead of a fixed 700px "
                         "cap, using the space the HUD rework freed instead of stacking into extra "
                         "rows.")
        self._add_bullet("The action header just says ACTIONS — for you and for every ally — instead "
                         "of swapping to a name banner on their turns. Whose turn it is still reads "
                         "clearly from the turn-order bar and the acting-card glow.")
        self._add_bullet("Target selection sits in the same-sized panel: the \"press 1–9 or click a "
                         "target\" hint line keeps its own reserved row, so the screen no longer "
                         "shifts when you pick a skill and go hunting for a target.")
        self._add_bullet("Every prompt button matches the panel's footprint too: encounter intros "
                         "(\"Press Enter to face…\"), reading a skill description (\"Press Enter to "
                         "use it…\"), round breaks, and the final Leave Battle button all fill the "
                         "exact height the action panel reserves. The bottom of the screen is the "
                         "same shape from the first prompt to the victory banner.")
        self._add_bullet("Use item now reads in two columns — consumables and capture nets run "
                         "left-to-right (1, 2 across the first row, 3, 4 on the next) inside the "
                         "same reserved slot, with both columns scrolling together. The numbers "
                         "still map one-to-one to what the engine expects, and the capture-net "
                         "picker shares the layout.")
        self._add_bullet("The turn-order bar finally keeps its promise in every superboss fight: "
                         "it was quietly falling back to a speed preview that parked you, then "
                         "your allies, then the boss, while the real initiative rolled underneath. "
                         "Each round now feeds the bar its actual rolled order — the acting "
                         "combatant lights up in the slot where they really act — and the "
                         "numbered speed list stops leaking into the combat log.")

        self._add_section("Combat & Equipment")
        self._add_bullet("Chance and Choice now rides every kit, not just basic attacks: a "
                         "workshop volley or Furioso flips the coin once for all its hits, and "
                         "Cutlass ripostes, Tarnished Jade discharges, Palette's exhibits and "
                         "Spectrum, and wedding counters and retributions all call heads or "
                         "tails too — one flip per action, every time.")
        self._add_bullet("Hallucination fights no longer scramble your party: the solo illusion "
                         "parks your allies to face you alone, and your front/bench arrangement "
                         "now comes back exactly as you set it — it used to quietly reset the "
                         "party order the moment the next real fight rebuilt it.")
        self._add_bullet("The illusion hands you back to the log when it ends: \"The room "
                         "still awaits...\" appears and waits for your word — read the "
                         "aftermath and your companions' lines in the dungeon log, then walk "
                         "into the real room instead of crashing straight from one fight into "
                         "the next.")
        self._add_bullet("Divine Intervention had a hole: with its pins spent (or never built "
                         "up), the Tarnished Jade still repelled every incoming blow at the "
                         "20% line — \"REPULSED … takes 0 damage!\" once per round, forever, "
                         "with nothing consumed, and the wearer simply could not be brought "
                         "down. The shatter now fires exactly when a blow (or the pins' own "
                         "toll) brings you down to 20% or less, paid for with the pins it "
                         "consumes — one save per descent. Once you're under the line the "
                         "Jade is spent: blows land, the pins only dig deeper, and the next "
                         "save must be earned by climbing back above the line.")

        self._add_section("Time Rework")
        self._add_bullet("Pandemonium finally feels the day: fatigue stacks accrue, Night rolls "
                         "the same hallucinations, and every stack dulls your stats there too — "
                         "the old suppression was hiding the whole system inside the one dungeon "
                         "built for long pushes. The Event Horizon alone stays frozen.")
        self._add_bullet("Inns and taverns speak in blocks now: Rest says 1 block and tells you "
                         "what it healed (or that you were already at full health), the "
                         "innkeeper's \"eight hours\" sleep line is just a night, and your own "
                         "house quotes rest costs in blocks — free from Villa upward. Journey "
                         "narration at the port and on the road shows block estimates too.")

        self._add_section("Lounge & Marriage")
        self._add_bullet("Proposing now shows you which rings you own and lets you choose: the "
                         "chosen ring's stats become your companion's permanent engagement bonus. "
                         "(The old flow looked for the wrong data key, so rings could be consumed "
                         "without their stats ever reaching her.) The gift shop's ring list also "
                         "shows each ring's real numbers now.")
        self._add_bullet("The ring's power finally shows up: it's folded into her stat sheet the "
                         "moment you propose, survives being sent home and re-recruited, and "
                         "continues to display as her Ring Blessing in the lounge.")
        self._add_bullet("Weddings are honest again: the wedding gift now requires the full 200 "
                         "affection — a stale affection cap can no longer marry a companion at "
                         "100 — and any engaged or married girl still sitting under the old cap "
                         "is quietly restored to 200 when you visit her.")
        self._add_bullet("Dorothy, Alice, and Red Hood finally have wedding accessories of their "
                         "own: Homeward Locket (a hearth-light that lifts you once per fight "
                         "below 35% HP), Rabbit's Pocket Watch (+2 initiative to the whole party "
                         "every round, +3 when bonded), and Huntsman's Oath (+30% damage on the "
                         "first strike of each fight, +45% when bonded).")

        self._add_section("Player Skills — Wave 2")
        self._add_bullet("Every class grows a second wave: three new actives unlock at levels 20, "
                         "26 and 32 — right where the long climb to the cap used to have nothing "
                         "waiting. Warriors charge and plant war banners, Mages focus the elements "
                         "and cast Glacial Prison, Rogues scatter caltrops and poison blades, "
                         "Clerics mend and ward their allies, Rangers camouflage and call down blast "
                         "arrows, Paladins bless the faithful and shatter the dark with Dawnbreaker, "
                         "Warlocks grasp the void and siphon souls, and Barbarians enter battle "
                         "trances. The Skill Book lists them all as Tier 3 (Level 20-32).")
        self._add_bullet("The new support effects are real, not renamed: Blessed Aegis is a true "
                         "damage-absorbing barrier (the absorb bar shows on your party frames), "
                         "Prayer of Mending restores 6% max HP each round, War Banner buffs the "
                         "whole party, Elemental Focus boosts every element you wield, Perfect "
                         "Opening and Reckless Abandon feed a new crit-damage bonus, and Caltrops "
                         "and Grasp of the Void leave their targets bleeding.")

        self._add_section("Player Skills — Capstones & Battle Loadout")
        self._add_bullet("Every class now ends its ladder with a capstone at level 40 (cooldown 9): "
                         "Warrior's Onslaught (five blows, the last one executes), Mage's Cataclysm "
                         "(the field in Inferno), Rogue's Death's Embrace (an execution that refunds "
                         "its own cooldown on a kill), Cleric's Providence (party heal plus a "
                         "shielded revive), Ranger's Skyfall Volley, Paladin's Heaven's Sword "
                         "(party-wide healing from the blow), Warlock's Dark Apotheosis and "
                         "Barbarian's Wrath Incarnate.")
        self._add_bullet("Combat now runs on a Battle Loadout: you bring at most 9 of your "
                         "unlocked skills into a fight. Everything past the ninth unlock queues "
                         "outside the fight — equip what fits your plan at the Skill Book's new "
                         "'Manage Battle Loadout' screen, and remember unequipped skills keep "
                         "their mastery.")
        self._add_bullet("Support skills finally earn mastery: heals, buffs, barriers and revives "
                         "count every cast toward ★ progress — previously only damaging skills "
                         "tracked uses at all. Frost Nova also slows again (the freeze had been "
                         "missing since the shared damage rework).")

        self._add_section("Player Skills — Professions")
        self._add_bullet("Every class now forks at level 40: once your capstone is learned, visit any "
                         "Guild and choose one of two professions — permanently. Warlord or "
                         "Sentinel, Evoker or Chronomancer, Assassin or Shadowdancer, Hierophant or "
                         "Inquisitor, Sharpshooter or Warden, Crusader or Templar, Nethermancer or "
                         "Infernalist, Berserker or Juggernaut. Your class passive is upgraded "
                         "with new powers (crit chance, elemental mastery, combat-start cooldowns, "
                         "regeneration, evasion, low-HP fury), your signature skill arrives "
                         "immediately, and two more unlock at levels 50 and 60. The other path is "
                         "closed forever.")
        self._add_bullet("Forty-eight new skills across the sixteen paths: command the party with "
                         "Iron Command, lock the field with Time Stop, vanish behind a Veil of "
                         "Shadows, raise the fallen with Greater Resurrection, brand a target with "
                         "Mark for Death, blanket the field in Hellfire, or simply refuse to die "
                         "with Undying Rage.")
        self._add_bullet("The Skill Book shows your profession, its upgraded passive and the locked "
                         "branch you gave up — your Inventory's Skills tab carries the banner too. "
                         "Profession skills flow through mastery, the Battle Loadout and the wiki "
                         "like everything else.")

        self._add_section("Event Horizon")
        self._add_bullet("Judgement holds its court only inside the rift now — and its gavel was "
                         "falling everywhere. Arcana stay in your run's records while a run is "
                         "suspended, and Judgement's round-start pulse read those records directly, "
                         "so ordinary dungeon fights were being judged too: every enemy bled 20% "
                         "max HP each round (and from round 3, so did your party). Justice could "
                         "mirror debuffs outside the rift the same way. Both hooks now verify a "
                         "run is actually turning; they snap back to full strength the moment you "
                         "step back into the Event Horizon.")

        self._add_section("Equipment Economy Tuning")
        self._add_bullet("Equipment is now priced by what it is: value = (base stats + elemental "
                         "richness + special bonuses + enhancement) × rarity. A Legendary Iron "
                         "Sword is cheap; a Legendary Inferno Greatsword is not. Selling uses the "
                         "same value, so enhanced and higher-value gear finally sells for more.")
        self._add_bullet("Shops roll stock by city tier (early / mid / late) with a level clamp: "
                         "early cities stock almost entirely common/uncommon, epic gear requires "
                         "level 12, legendary level 20. A starting character no longer sees rares "
                         "as everyday stock, and legendaries only appear regularly in high-bias "
                         "late cities.")
        self._add_bullet("Drop curves flattened: legendary is capped at 5% (normal) / 10% "
                         "(Pandemonium) at level 30+, with epics as the endgame workhorse. "
                         "Treasure rooms are re-tuned (18% legendary at depth, down from 25%). "
                         "Base value also caps the rarity an item can roll (low-value bases stop "
                         "at rare/epic), so 'Legendary Iron Sword' drops are gone.")
        self._add_bullet("Enhancement is multiplicative with rarity: +N is applied before the "
                         "rarity multiplier (a legendary +10 greatsword has 28 STR vs a common "
                         "one's 15), matching the 8× enhancement cost. Existing owned gear is "
                         "rescaled automatically on load.")
        self._add_bullet("Scroll fusion now charges for the value it adds — cheap for junk hops, "
                         "expensive for legendary ones (Inferno Greatsword +10 common → legendary "
                         "≈ 7,350g) — and rescales the elemental profile, so fused items match "
                         "natural drops instead of being permanently weaker.")

        self._add_section("Compositional Weapons — Form × Element × Grade")
        self._add_bullet("The weapon catalog is no longer a fixed list: 29 forms × 9 elements × "
                         "3 grades (~750 weapons) are generated at load. Every form can be found "
                         "in every element and tier, named by the prefix families the design "
                         "always promised — an Ember, Blaze and Inferno Greatsword are now the same "
                         "form at grades 1–3 (STR 4 / 6 / 8, fire 1.10 / 1.30 / 1.50).")
        self._add_bullet("Grade gates depth: grade 1 drops on floors 1–10, grade 2 on 11–25, "
                         "grade 3 on 26+, and city shops mix grades by tier (early cities are "
                         "grade 1 only). Rarity stays luck, capped by grade: a grade-1 weapon can "
                         "never be legendary, grade 2 caps at epic.")
        self._add_bullet("Regions bias elements: volcanic shops favour fire and earth, tundra "
                         "water and wind, Pandemonium dark and void — the same form plays "
                         "differently depending on where you find it.")
        self._add_bullet("Tempering now raises elemental damage as well: +0.02 per enhancement "
                         "step, so a +10 Ember Greatsword reaches Blaze-tier fire without being "
                         "renamed. Existing gear is rescaled automatically on load.")
        self._add_bullet("Curated weapons (Iron Sword, Inferno Greatsword, boss and quest "
                         "rewards) keep their hand-tuned stats as overrides; the grid fills every "
                         "combination that didn't exist before. Uniques, heroine and wedding gear "
                         "are untouched.")

        self._add_section("Compositional Armor & Accessories")
        self._add_bullet("Armor and accessories join the grid: 16 armor forms × 9 elements × 3 "
                         "grades and 17 accessory forms × 9 × 3 (~850 new pieces). An Ember, Blaze "
                         "and Inferno Padded Armor are the same silhouette at grades 1–3, and every "
                         "ring, crown or cloak now exists in every element.")
        self._add_bullet("Armor elements are defensive triangles, not cosmetic resists: a fire "
                         "piece resists fire (15/25/35% by grade) and earth, but takes ~15% more "
                         "water damage; light armor trades total entries for having no weakness. "
                         "Deep sets (Plate, Runic Plate) cover more elements at a lower value.")
        self._add_bullet("Accessories follow the element→stat affinity the old catalog only "
                         "hinted at: fire is STR/CON, water CON/DEX, wind DEX/CHA, light CHA/WIS, "
                         "magical LRN/WIS. Single-stat forms pour the whole budget into the primary "
                         "stat; two-stat forms split it.")
        self._add_bullet("Grades apply everywhere: +1 primary stat per grade, resistance values "
                         "climb with grade (secondary resists only appear from grade 2), and the "
                         "same rarity caps hold — grade 1 can never be legendary. City shops roll "
                         "armor and accessories by their tier's grade mix; floors gate them the same "
                         "way as weapons.")
        self._add_bullet("Armor and accessories are priced with a smaller grade premium than "
                         "weapons, so a grade-3 breastplate is valuable without out-pricing a "
                         "grade-3 greatsword. Curated pieces, uniques and wedding gear keep their "
                         "hand-tuned stats and are untouched.")

        self._add_section("Form Traditions")
        self._add_bullet("Every piece of equipment now carries a form tradition, and every "
                         "equipped slot contributes: weapon, armor, accessory 1 and accessory 2 "
                         "(four traditions), plus accessory 3 once an actor has consumed a "
                         "Beating Root (five). Two pieces with the same tradition stack.")
        self._add_bullet("Weapons: swords, rapiers, bows and daggers sharpen crits (Keen); axes "
                         "and tongue daggers deepen them (Brutal); greatswords, blades, mauls and "
                         "flails add damage (Cleaving); hammers, maces, halberds and crossbows "
                         "punch through armour (Sundering); shields and gauntlets reduce damage "
                         "taken (Guarded); spears, chakrams and bells act earlier (Swift); "
                         "staves, orbs, grimoires, wands and spellblades boost magical damage "
                         "(Focused); focus orbs, scepters, lutes and harps boost healing (Mending).")
        self._add_bullet("Armor and accessories use the same vocabulary: plate and mail guard, "
                         "leathers and silks dodge, robes and regalia focus, vestments and mantles "
                         "mend, dragonhide hardens its own element, rings and crowns sharpen, "
                         "boots and earrings quicken. Examine and shop lines name the tradition.")
        self._add_bullet("Unique gear participates through its form — Vorpal Blade counts as a "
                         "blade, Sky Piercer as a talisman, wedding bands as bands — so nothing "
                         "is left out. Traditions don't scale with grade, rarity or enhancement, "
                         "and don't change an item's price.")

        self._add_section("Equipment Catalog Rebuilt")
        self._add_bullet("The old hand-written catalog has been retired: every non-unique weapon, "
                         "armor and accessory is now generated from its form, element and grade, "
                         "so stats, elements and prices finally follow the same formulas. Shops, "
                         "merchants, dungeons and treasure rooms already drew from this grid, so "
                         "drops are canonical everywhere.")
        self._add_bullet("Existing gear is rescaled automatically on load, names included. A "
                         "handful of story pieces that don't fit the grid (Magma Locket, "
                         "Cyclone Anklet, Captain's Hook…) remain as legacy trophies — still "
                         "equippable, but they no longer drop or appear in shops.")
        self._add_bullet("Drop rules made explicit: grade comes from the floor (1–10 → grade 1, "
                         "11–25 → grade 2, 26+ → grade 3) and rarity is capped by grade. "
                         "Legendary only exists on grade-3 gear, so 'legendary iron sword' is "
                         "structurally impossible — every legendary you find is endgame-tier.")

        self._add_section("Tempering & Flowers")
        self._add_bullet("The blacksmith now offers Temper (Raise Grade): grade 1 → 2 costs 3 "
                         "element flowers and 1,200 gold; grade 2 → 3 costs 6 flowers and 3,000 "
                         "gold (city discounts apply). Enhancement and rarity survive the "
                         "upgrade.")
        self._add_bullet("Nine flowers exist — Ironbriar, Emberbloom, Frostlotus, Stormlily, "
                         "Galeorchid, Stonebloom, Sunpetal, Nightbloom and Manabloom, one per "
                         "element. They are never sold: they drop from enemies (about 12% of "
                         "drop rolls, weighted to the region's elements) and every treasure "
                         "room hides one.")
        self._add_bullet("Element and form are locked. Fire gear can only ever become stronger "
                         "fire gear — there is no service that turns a fire blade into a water "
                         "blade. Tempering is the fallback for players who can't find a grade-3 "
                         "legendary naturally.")
        self._add_bullet("Fusion scrolls now respect grade ceilings: a scroll can finish a "
                         "grade's rarity cap (grade 1 → rare, grade 2 → epic, grade 3 → any) but "
                         "never exceed it. A legendary scroll on a grade-1 Ember is refused with "
                         "'temper it first' instead of creating a 'legendary' item weaker than a "
                         "plain grade-3 Inferno. Items made before this change keep their rarity.")

        self._add_section("Elemental Resistances — Convention Fix")
        self._add_bullet("Resistance values now work as designed: higher = stronger. The damage "
                         "formula used to multiply by the raw value, so fire armor made you take "
                         "MORE fire damage and 'flame' enemies were weak to fire — every "
                         "resistance in the game was inverted. The damage-taken multiplier is now "
                         "2.0 - rating (1.3 = 30% resist, 0.7 = 30% weakness), fixing gear, races, "
                         "enemy profiles, keyword specialisations and boss elemental attacks in "
                         "one pass.")
        self._add_bullet("Pierce (Magical weapons) now correctly bypasses resistance ratings, "
                         "and the White Knight / Wicked Witch target selection follows the fixed "
                         "convention (lowest fire resistance = weakest).")
        self._add_bullet("The training dummy uses the corrected scale too: its resistance % maps "
                         "to 1.0 + value behind the scenes, so '+80%' now truly resists 80% "
                         "instead of 20%.")

        self._add_section("Wild Dungeons — Header Floor Fixes")
        self._add_bullet("The dungeon header subtitle now tracks the run: entering or resuming a "
                         "ruin at floor 3 and descending to floor 5 no longer leaves "
                         "'Volcanic Region · Floor 3' frozen at the top of the screen — the "
                         "subtitle refreshes with the same floor the map and log show.")
        self._add_bullet("Combat round headers show the ruin's floor index (Floor 5/6) instead "
                         "of its enemy level. The level is still used for scaling and the "
                         "final-room empowerment; only the display changed. Event Horizon room "
                         "subtitles refresh with the room counter too.")

        self._add_section("Wild Dungeons — Clear Windows")
        self._add_bullet("Conquering a wild dungeon no longer strands the player on a dead "
                         "screen. The reward window was parented to the WorldMapScreen instance "
                         "that had already been destroyed when the run started, so opening it "
                         "raised a TclError and every button — including Flee to City — became a "
                         "no-op. The conquest window now opens on the live screen, lists the "
                         "spoils recovered from the hoard, and offers a single Return to City "
                         "button.")
        self._add_bullet("Clearing a wild-dungeon floor now opens the same floor-clear window "
                         "as city dungeons: continue to the next floor, return to the city, or "
                         "save and return to the main menu. Terminal mode keeps the plain "
                         "'Press Enter to descend' prompt.")
        self._add_bullet("Safety net: a crash inside a dungeon result callback now falls back "
                         "to the city instead of leaving the finished run stuck on screen.")

        self._add_section("Voss's Stellar Field Kit — Research Loan")
        self._add_bullet("The Stellar Field Kit is now its own item: a one-use capture net that "
                         "never misses on monster girls below level 8. The weave refuses anything "
                         "at level 8 or higher without spending the kit.")
        self._add_bullet("The kit is spent on the throw even when you have no house to bring the "
                         "girl home to, and you can only carry one at a time. Once it is used, ask "
                         "Archivist Voss at the Star Tower for another — the request appears in the "
                         "archive menu whenever the kit is not in your bag.")
        self._add_bullet("Voss stops issuing kits once Field Study One (\"A Place to Belong\") is "
                         "complete — the loan was only ever meant to bring the first girl home.")
        self._add_bullet("Allies can no longer consume capture nets from the shared battle bag — "
                         "previously an ally could waste one for no effect.")
        self._add_bullet("The Fractured Hourglass is now consistently marked unique (red) in every "
                         "save. Old saves that stored it as a common consumable are repaired on "
                         "load, and it can no longer be sold or dropped.")

        self._add_version("v0.1.8.0 — The Distant Journey")

        self._add_section("Combat & Equipment")
        self._add_bullet("Unique gear finally explains itself: every unique item's Examine popup now "
                         "carries an Equip Effect line — Abyss Fang's Wield the Abyss and triple "
                         "actions, the Captain's Cutlass's High Tide and Crew Rally, Tarnished Jade's "
                         "pins and Divine Lament, Sky Piercer's execute threshold, the Prescript "
                         "Ledger's Grace and Karma, Chance and Choice's coin, the Old Dopo Robe's "
                         "sword synergy, and the rest of the relics from the Black Silence gloves to "
                         "the Wonderland heroine weapons. Wedding accessories show both their base "
                         "effect and their bonded upgrade — the same wording the round-one combat "
                         "reminder uses.")
        self._add_bullet("Examine now follows your equipment: unique items stay examinable while "
                         "equipped — the button sits on your Stats & Equip rows and on every ally's "
                         "page, not just in the bag — so wearing a trophy no longer hides what it "
                         "actually does. Uniques whose special is flavour rather than mechanics "
                         "(Perception-Blocking Mask, Rose-Tinted Crown, Wicked Witch's Hat, Pocket "
                         "Watch, the \"There's No Place\" Charm) say so plainly instead of staying "
                         "silent.")
        self._add_bullet("The Black Silence Gloves now grow with the gear: workshop and Furioso "
                         "damage scales with the gloves' enhance level (+12% power per +1, up to "
                         "×1.60 at +5 — the same top-end as ✦✦ skill mastery, applied before the "
                         "target's CON is subtracted), and every workshop hit floors at 1 damage "
                         "like ally skills do. A deep-rift brick like the Elder Titan (CON 38 after "
                         "scaling) can no longer multiply the whole kit into all-zero — the "
                         "multiplier and the floor are this kit's replacement for skill mastery.")
        self._add_bullet("Workshop and Furioso hits now consume the same attack buffs as basic "
                         "attacks and skills: persistent damage boosts (Frabjous Day, rift damage "
                         "flasks) multiply their damage, and an Empower effect (Overclock / Tinker "
                         "Enhancement) is spent to fuel them — once per action, exactly like a "
                         "basic attack.")
        self._add_bullet("The Tarnished Jade's Wedge Backlash is finally visible: a WEDGE −50% "
                         "tag marks whoever suffers the curse (ALL stats halved for the battle), "
                         "so a sudden damage collapse has a name. The rift's Entropy tag also "
                         "states its attribute penalty now (ENT×98 (−45% attrs)), matching the "
                         "inventory tab instead of showing the stack count alone.")
        self._add_bullet("Suspended runs no longer keep stale battle state: an interrupted rift "
                         "fight (defensive save & quit after a timeout) used to persist things "
                         "like the Jade curse, the glove cycle and Crystal Atelier's dodge into "
                         "the suspend save — all battle-scoped effects are now scrubbed on every "
                         "Event Horizon exit.")
        self._add_bullet("Unique gear finally pays unique prices: blacksmith enhancement for "
                         "unique items (Black Silence Gloves, Tarnished Jade, wedding "
                         "accessories…) was falling through to the common price multiplier and "
                         "costing less than enhancing a legendary — it now carries a proper "
                         "premium above legendary rates.")

        self._add_section("Event Horizon")
        self._add_bullet("The Event Horizon opens — an endless rift beyond the known map. Once your "
                         "deepest floor reaches 20, a robed watcher with a starless void for a head, "
                         "Vesper Erebus, finds you in any city and marks a tear in the sky east of "
                         "Veilholt on your world map. Travel out, step in — rooms forever, no floors: "
                         "about seven in ten are battles, with rift merchants (Horizon Motes), mote "
                         "storms, and still pools between. No superboss can ever lurk inside.")
        self._add_bullet("Vesper remembers: the arrival scene greets you differently every visit — "
                         "a first-visit version, rotating idle lines, and a one-time word each time "
                         "you first cross a 25-room milestone (r25, r50, r75, r100, then the root "
                         "marks past 100).")
        self._add_bullet("Deep runs stay readable: permanent rift bonuses (flasks, cards, tune-ups) "
                         "now stack into a single HUD total — DMG+37% instead of six separate DMG "
                         "tags — while temporary ally-skill buffs like Frabjous Day and Fate's Favor "
                         "still show on their own. Rift trial burdens on enemies list what they do "
                         "(TRL×5: HP+20% DMG+9% …) instead of just the count.")
        self._add_bullet("Rift quality-of-life: Party Status now updates while you're inside the "
                         "rift, the empty Map slot shows a Rift status block (room, "
                         "motes, Entropy, next trial and flask milestone), and menus render every "
                         "option the same size — no more stretched first button.")
        self._add_bullet("Rift merchants trade in flasks: each stall stocks three kinds at your "
                         "depth's grade, priced in motes by grade — buy one and pick who drinks — "
                         "plus the once-a-visit Tune-Up (+1 all attributes, and yes: tune-ups stack; "
                         "the HUD now shows the summed total, e.g. ALL+3).")
        self._add_bullet("Rift balance pass (r83 playtest feedback): enemy growth curves eased — "
                         "HP +1.8%/room, DMG +1.3%, CON/DEX +1.0%, roughly a third off the old "
                         "compounding — and trial cards are now a finite, stacking deck: every "
                         "(kind, tier) card is unique and never repeats, same-kind cards at "
                         "different tiers stack their effects, tiers unlock with depth (T4 from "
                         "r45), and the deck exhausts over a long run (positive trials every 15 "
                         "rooms; a spent deck passes with motes and no burden).")
        self._add_bullet("Softer pressure, better rewards: Entropy's attribute bite is now −3% per "
                         "full 20 stacks (was −1% each, capping at just 45 stacks; still capped at "
                         "−45%) while battle-start rolls stay at full strength; Vitality flasks heal "
                         "% max HP per round instead of tiny flats; one rift-merchant ware per visit "
                         "is 40% off.")
        self._add_bullet("The decks grew a capstone: every trial and boon card has a T4 grade "
                         "(unlocked at r45 — 24 cards per deck), and every 25th room the Horizon "
                         "deals you a Joker — a pool of run-long trade-offs: +10% damage dealt for "
                         "+5% taken, −10% taken for −5% dealt, or +10% crit for +5% taken. Jokers "
                         "are skippable, sit outside the decks, and never feed the payout.")
        self._add_bullet("The rift pays in depth, not drops: no XP, no items, no bounty progress. "
                         "Every cleared room offers a flask — a random buff (damage, elemental damage, "
                         "damage reduction, an attribute, regeneration, or crit, across seven grades "
                         "that climb with depth) that lasts for the whole run and is drunk by ONE "
                         "actor you choose — your character or any monster girl, bench included. The "
                         "log announces every flask the moment it surfaces, and the “who drinks?” "
                         "menu reminds you what each actor already carries (a tally "
                         "like “Fervor×2, Edge×1”).")
        self._add_bullet("Entropy is the price of depth: +1 per room from room 5, −1% to every "
                         "party member's attributes per stack (capped −45%), and every 10 stacks "
                         "it permanently gains a random affliction — a lasting debuff identity "
                         "like Burn, Silence or Dread, listed in your inventory's Event Horizon "
                         "tab. Rift battles open with debuffs drawn ONLY from the afflictions "
                         "you've already gained (none before your first — the early rift is "
                         "merciful). Every 5th room is a trial — pick one of three cards; "
                         "negative picks empower all enemies for the run (and add Entropy — a "
                         "richer payout) and stamp TRL×N on every enemy so the burdens are "
                         "visible; positive cards bless the team. Every 20th room deals a deep "
                         "boon instead.")
        self._add_bullet("Know when to walk away: save & quit suspends the run to resume at the "
                         "site; death or abandoning wipes it — only your best room is kept forever — "
                         "and pays a gold payout scaled by rooms AND Entropy (death pays after the "
                         "usual toll, exempt from it). The corner button during a run reads ← Leave "
                         "Rift: it confirms before saving you out mid-room (and no longer "
                         "flashes past unread). Rift combat counts rooms, never floors — "
                         "the top bar and round headers read ⚔ The Event Horizon | Room N. A closing "
                         "summary tallies the run: rooms, gold, cards taken, and every flask effect. "
                         "Rift power stays in the rift — while a run is suspended, none of its "
                         "flasks, cards or Entropy follow you into cities (the ENT tag and buff "
                         "row return the moment you step back in). While a run lives, your "
                         "inventory gains an Event Horizon tab (motes, "
                         "Entropy + afflictions, flask effects, every card — with IN RUN / "
                         "SUSPENDED banners; after a run ends it keeps a best-room stub), and the "
                         "combat HUD shows ENT×N pressure and ELM+% prism tags.")
        self._add_bullet("Trophies for the deep: Chance and Choice (r50 — every strike flips a "
                         "coin: ×0.25 or ×1.75 damage), Old Dopo Robe (r75 — a sword pilgrim's robe, "
                         "stronger with every blade in your company), Piece of Relationship (r100 — "
                         "it grows with the number of girls who truly love you), and from r125 the "
                         "Beating Root, which permanently opens a third accessory slot for one actor.")
        self._add_bullet("The Beating Root is usable: from r125 onward, one copy every 25 rooms past "
                         "100. In your bag (Inventory → Bag → Key Items) it gains a Use button — "
                         "choose any actor, and the root sinks in: that actor permanently grows a "
                         "THIRD accessory slot, marked as Accessory 3 in their equipment panel. The "
                         "unlock follows them everywhere — through saves, death, and time at home "
                         "in the house — and stacks all the way to eight roots for a full party. "
                         "(The replacement prompt and the Bag's auto-equip both use the new slot "
                         "once it's open.)")
        self._add_bullet("Flask totals at a glance: the Event Horizon tab's Flask Effects section now "
                         "shows each actor's running totals beside their name — damage %, elemental "
                         "damage %, damage taken %, crit %, regeneration, and every Might attribute "
                         "summed across all the flasks that actor has drunk this run.")

        self._add_section("Ally Potential & Awakening")
        self._add_bullet("Late-bloomer Growth: monster girls captured at a low base now gain bonus "
                         "attributes as they level with you — a fully-raised Goblin Girl now ends even "
                         "with a Lich Queen in raw stats. The lounge and skill book show each girl's "
                         "Growth band (High / Medium / Low).")
        self._add_bullet("Every race passive now delivers its full text — Goblin dodge and Shadow evade, "
                         "Construct poison & bleed immunity, Undead regeneration (allied heals are "
                         "blocked, her own still work), Giant and Abomination damage reduction, Demon / "
                         "Elemental / Gnome elemental damage, Orc stun-on-hit, Beast's +2 STR/+3 DEX, "
                         "Vampire's charm, and more.")
        self._add_bullet("Awakening: twelve monster girls (Goblin Girl, Harpy Scout, Moth Girl, Slime "
                         "Girl, Automata Doll, Centaur Champion, Gorgon Petrifier, Mimic Girl, Gear "
                         "Maiden, Dusk Weaver, Demon Whip Master, Dullahan Knight) can reach a true "
                         "awakening — both innate skills upgraded, a new name, and a one-time scene — "
                         "in the House Lounge at Lv 40, level cap 40, and affection 150, for one "
                         "Awakening Sigil. Skill mastery and cooldown progress carries over.")
        self._add_bullet("Awakening Sigils are scarce — five per save: one for your first-ever superboss "
                         "kill, one from Mary Sue, and three forgeable at the Arcane Tower's Awakening "
                         "Research (4 Sigil Shards + 25,000 gold). Sigil Shards drop from first-time "
                         "superbosses in Wonderland's depths and the global superboss rotation. Existing "
                         "saves are retro-credited for kills already earned.")
        self._add_bullet("Heroine upgrade skills (Frabjous Day, Through the Forest, Emerald City's "
                         "Light) now live in their own category instead of counting as learned skills: "
                         "they no longer occupy one of the three Barracks skill slots, no longer appear "
                         "in the replace-a-skill menu, and stay with the heroine permanently once her "
                         "signature weapon has been restored. Existing saves migrate automatically.")

        self._add_section("Companion Dispatch & Errands")
        self._add_bullet("Your house can now work while you do: the new Dispatch Board in your house "
                         "menu sends housed companions on dungeon sweeps over floors you've already "
                         "cleared, or on errands — foraging, courier runs, caravan escorts, scouting "
                         "and surveys. Missions resolve on their own as time passes, and the rewards "
                         "(gold, items, EXP, a little city Favor) wait in a report at the board. Offers "
                         "refresh every 3 days.")
        self._add_bullet("Every companion now carries Stress (0–100) and a derived Mood. A rested, "
                         "fond girl is Spirited; a worn one turns Tired, Weary, and finally Burned "
                         "Out — refusing missions outright at 90+. Stress sharpens the risk of injury, "
                         "so rotate your roster: nightly rest at home, talking, gifts, kisses, Herbal "
                         "Bath Salts (Herbalist) and the Temple's Day of Respite all soothe it.")
        self._add_bullet("Dispatch is not without teeth: damaged girls come home hurt, and a bad "
                         "enough outcome leaves a companion Downed at 1 HP. She recovers on her own "
                         "(housed girls regain 25% HP a night), can't be recruited or sent out until "
                         "healed, and never dies or leaves over it.")
        self._add_bullet("Your house sets the scale: its level governs concurrent dispatches "
                         "(1 → 2 → 2 → 3), team size (up to 4), the difficulty of work you can "
                         "administer (up to ★6), and how many offers the board carries (4–7, "
                         "refreshed every 3 days).")

        self._add_section("Wild Dungeons")
        self._add_bullet("Ruins now surface across the world map: every week, three to seven wild "
                         "dungeons appear near the cities and crumble away after a few days. Each "
                         "is a one-time, limited-floor delve at a level scaled to your progress — "
                         "fresh adventurers will never be sent against a ruin far beyond them.")
        self._add_bullet("Every ruin announces itself on the map with a biome glyph — ❄ for the "
                         "tundra, 🌋 for the volcanic reaches, 🐚 for the sea caves, and so on. "
                         "Click one to see its level, floor count, days until it crumbles, "
                         "estimated travel time, and the full reward pool before you commit a "
                         "single step.")
        self._add_bullet("Travel to a ruin follows the same rules as any road: pick \"Travel to "
                         "Dungeon\" in the info panel, and your mounts, ferries, cargo, and "
                         "roadside encounters all apply. Fleeing or falling sends you to the "
                         "nearest city — and a ruin stays retryable until it crumbles. Clear "
                         "every floor and its previewed hoard is yours, plus gold and EXP.")
        self._add_bullet("Weekly spawns and conquests are recorded in the Journal's Event tab — "
                         "each completed ruin with its name, level, and date.")

        self._add_section("Quality of Life & Bug Fixes")
        self._add_bullet("Key Items in your bag now have an Examine button — name, rarity, and "
                         "lore for every keepsake and Wonderland material (Looking Glass Shard, "
                         "Frabjous Page, Witch's Broom, Wolf's Tooth, and more all gained "
                         "description text). Find it under Inventory → Bag → Key Items.")
        self._add_bullet("Keepsake and crafting-material names lost the mechanical rarity prefix — "
                         "the Glass Anchor now reads simply \"Glass Anchor (Legendary)\" instead of "
                         "repeating its rarity twice.")
        self._add_bullet("Popup dialogs now size themselves to their wrapped text — the OK button "
                         "on long Examine popups was being clipped by the window edge (most "
                         "visible on the Glass Anchor's lore).")
        self._add_bullet("The Combat Log pane became a 📜 popup with a compact three-line event feed "
                         "in its place — the pane ate ~114px of HUD space, which made five-enemy "
                         "fights clip the last enemy's card. The feed keeps your latest actions "
                         "visible and pins the skill being cast as a banner line (that description "
                         "used to scroll past in the pane). Click 📜 — or the top-bar log button — "
                         "to open the full history, click again to hide; it can stay pinned open "
                         "while you fight.")
        self._add_bullet("Turn feedback on the HUD: the combatant who is acting now briefly lights "
                         "up gold, and an ally's card pulses red when they take a hit — so the "
                         "enemy phase is visible at a glance instead of only in log text.")
        self._add_bullet("Combat now plays out with a readable beat: a short pause when each actor "
                         "takes their turn (longer for enemies), a beat after you confirm before "
                         "the action resolves, and staggered action lines. Skill selection itself "
                         "stays instant. Click anywhere to skip the current actor's beat. Set the "
                         "pace in Settings → Gameplay → Combat pacing (instant restores the old "
                         "speed).")
        self._add_bullet("Combat polish from the same pass: the round number lives only in the top "
                         "bar now, the turn-order list highlights whoever is acting, and the "
                         "events feed sweeps each actor's lines when the next turn begins — with "
                         "one exception: the latest damage line stays on screen until the next "
                         "combatant's damage replaces it, so hits don't flash away before you "
                         "can read them (same-actor multi-hits stack). The victory line still "
                         "lands on a clean feed.")
        self._add_bullet("The wedding accessory's battle-start line now states the item's real "
                         "effect (\"Sunfire Band — attacks leave a 3-turn Burn\") — the old line "
                         "falsely claimed \"you strike first!\", a mechanic that never existed.")
        self._add_bullet("Wedding accessory effects now trigger on every kind of attack — Black "
                         "Silence workshop attacks and Furioso, plus all class skills. Previously "
                         "only basic attacks could proc them, so glove wearers (who have no basic "
                         "attack) never saw their wedding item's on-hit effect at all. "
                         "Wedding burn text also now speaks the burn system's language — tier "
                         "names like \"Burn\" and \"Blaze\" instead of pre-rework flat numbers "
                         "(\"6/turn\", \"10/turn\") on the Sunfire Band, Emberwaltz Ring, "
                         "Infernal Throne Seal, Eternal Ember, and Infernal Vow Band. The "
                         "Stardust Crown's bonded bonus also now really applies its promised "
                         "3-turn burn.")
        self._add_bullet("Voss now gives you a resonance blank — a shattered glass orb that "
                         "records your Command Resonance grade. It mends as your household grows: "
                         "Shattered → Cracked → Mending → Whole → Radiant → Resonant, its rarity "
                         "colour and a ✦ fill-meter following along. Examine it (Inventory → Bag → "
                         "Key Items) to see your grade and what the Archive wants next. Existing "
                         "saves receive theirs on the next City sync.")
        self._add_bullet("Unequipping an item with a full bag now opens a clear popup warning — "
                         "previously the failure was only printed to the console, and the log falsely "
                         "reported a successful unequip. The same warning appears when unequipping "
                         "allies.")
        self._add_bullet("The shop's sell prompt once again shows its full multi-select hint: type "
                         "'1 3 5' for individual items, '1-4' for a range, or 'all' to sell everything. "
                         "The hint always worked, but the GUI was cutting it off after 30 characters.")
        self._add_bullet("Monster girls can now be given a name in the House Lounge — choose "
                         "'Give a name' / 'Rename' on any companion (at home or in the active party). "
                         "The name follows her through the lounge, the bag's Allies tab, party cards, "
                         "the combat HUD and combat log, and the barracks. Her species is never lost: "
                         "her lounge page shows a 'Species:' line and the lounge list reads "
                         "\"Luna (Goblin Girl)\".")
        self._add_bullet("Fixed a critical save bug that could silently EMPTY your house of monster "
                         "girls: house lookups treated origin_city — a value that travel and dungeon "
                         "runs constantly repoint — as your home city. After entering a dungeon from "
                         "a city where you own no house (e.g. Irondeep), teaching a skill at the "
                         "barracks read an empty list and saved it back over your real house's girls. "
                         "House reads and saves now always resolve to the house you actually own, so "
                         "a read→save cycle can never touch a different house.")
        self._add_bullet("The Fractured Hourglass now works as intended: using it is a free action "
                         "(you keep your turn) that reduces all of the user's cooldowns by 1, and "
                         "the hourglass is never consumed — it recharges for 3 turns before it can "
                         "bend time again. It only works in combat, and allies can use it too. "
                         "Previously the item was consumed on use and did nothing.")
        self._add_bullet("The Fractured Hourglass is now flagged UNIQUE like the rest of the "
                         "Chrysalis's trophies: no merchant or shop can roll it into stock, and it "
                         "can no longer be sold, dropped, or discarded. Existing saves are covered "
                         "too.")
        self._add_bullet("The save browser got a full rework — Load Game now opens one scrollable "
                         "window with a card per save (name, level, race, and class on the left; "
                         "Savefile number on the right). Click a card and its Savefile number turns "
                         "into Load / Delete buttons — each asks for confirmation before acting, "
                         "and clicking the card again backs out (the bottom Close button becomes "
                         "Cancel while a save is selected). Previously the action buttons were "
                         "squeezed once you had more than four saves, and the list could be scrolled "
                         "above the first card into empty space.")
        self._add_bullet("Renamed companions are now recognized on their combat turns. A monster "
                         "girl renamed at the House Lounge (e.g. \"Ran Yakumo\") could fail to match "
                         "on her turn — the action bar showed YOUR menu (Black Gloves workshops, or "
                         "any other weapon menu) while the turn order correctly said it was hers. "
                         "Workshop clicks then fed numbers into HER skill list (a click on "
                         "\"Wheels Industry\" could really cast her Judgment), while other clicks "
                         "were silently rejected. Companions now resolve by their chosen name, "
                         "nickname, or species name.")

        self._add_section("Equipment UI")
        self._add_bullet("Weapons now show which attribute scales their damage — a gold "
                         "\"▸ Scales: STR\" tag in the Bag, Stats & Equipment, shops, merchants, and "
                         "item cards. Multi-stat weapons list both (e.g. STR + DEX).")
        self._add_bullet("Every unique item in your bag now has an Examine button — the Event "
                         "Horizon trophies carry authored lore (Chance and Choice, Old Dopo Robe, "
                         "Piece of Relationship, the Beating Root), and any unique missing written "
                         "text falls back to a keepsake note. Key Items keep their Examine too.")

        self._add_section("Combat UI")
        self._add_bullet("Potion Sickness now shows a status tag (SICK×N) on the combat HUD for the "
                         "player and allies, showing how many turns remain before another healing "
                         "potion can be used.")
        self._add_bullet("Turn-order highlights now pick out the right twin: when two enemies share "
                         "a name (say two Reality Engineers), only the one whose turn it is lights "
                         "up in the turn-order bar. Previously every enemy with that name lit up at "
                         "once, since the bar matched on the bare name.")
        self._add_bullet("The turn-order card no longer flips your hero's name into “You” mid-fight — "
                         "the engine's turn bar now uses the name you chose at character creation, "
                         "matching the opening preview and the damage feed.")
        self._add_bullet("Dodges and misses now linger in the combat feed: evasion results (\"The Wolf "
                         "dodges your attack!\", a blinded enemy flailing wide) stay visible across "
                         "the next turn header like damage lines already did — they used to flash "
                         "for a single beat and get swept before they could be read, which made "
                         "blinded attacks look like they silently skipped your turn.")

        self._add_section("Combat")
        self._add_bullet("Vorpal Edge no longer double-crits: its +30% crit chance is now added to "
                         "the standard crit roll — one \"Critical hit!\" per hit — and its criticals "
                         "deal 2.2× damage instead of the usual 1.5×. The skill description and the "
                         "skills wiki now state this, and crit damage lines show the (CRITICAL!) tag.")
        self._add_bullet("Certain Someone's Black Gloves workshop attacks and Furioso now actually "
                         "apply the gloves' Dark element — each hit uses the wearer's Dark damage "
                         "bonus against the target's Dark resistance and can critically hit like a "
                         "normal attack. Previously the [DARK] tag on workshop hits was display-only.")
        self._add_bullet("Pandemonium runs no longer swing with the clock — Isle of Glass enemies "
                         "always carry the dusk baseline inflation (+40%) instead of scaling up to "
                         "1.8× at midnight. Daily event effects and the dungeon's own curse "
                         "multiplier are unchanged.")
        self._add_bullet("Weapon attacks now resolve their element from the weapon's authored primary "
                         "element. Weapons whose elements tie (Blaze Axe: physical 1.3 / fire 1.3) "
                         "used to silently land as [PHYSICAL] in the log, and the HUD's ⚔ tag could "
                         "name a different element than the attacks actually used — it scanned "
                         "every equipped accessory instead of the weapon. Dorothy's Blaze Lute now "
                         "shows ⚔FIR and hits [FIRE]; the ⚔ tag always matches the damage line.")

        self._add_section("Cargo Trading")
        self._add_bullet("The Trade Permit now unlocks a real cargo trading loop. Buy regional goods at "
                         "any city shop's new Cargo Market (permit-gated), haul them with a mount, and "
                         "sell them in other cities at terrain-themed demand prices — mountain goods "
                         "fetch top gold at ports, sea goods inland, and each city pays its own rates.")
        self._add_bullet("Cargo is a new inventory item type: bag-exempt, stackable, with its own tab "
                         "in the Bag screen, and never sold through normal item selling.")
        self._add_bullet("Each mount has a cargo capacity and hauling load slows travel (up to +25%). "
                         "Purchases are rejected past 1.8× your transport's capacity; dungeon and "
                         "roadside pickups may exceed it, but map travel is blocked until you shed the "
                         "load. Traveling with no mount gives the maximum slowdown.")
        self._add_bullet("Cargo also appears out in the world: road and dungeon merchants stock cargo "
                         "(~30% of their wares) and buy it, Guild Market Day merchants pay local demand "
                         "prices, and roadside abandoned wagons or drifting crates yield 1–3 units.")
        self._add_bullet("New ship system at the Shipyard — buy, upgrade, downgrade, or sell vessels "
                         "(Merchant Sloop, War Frigate, Trade Galleon) for faster, safer sea voyages "
                         "with their own cargo holds.")
        self._add_bullet("Monthly maintenance: ships and high-tier mounts (War Horse, Caravan) now bill "
                         "upkeep on the 1st of each month with an immediate breakdown, and you can go "
                         "into debt.")
        self._add_bullet("Removed the placeholder \"Sell bulk goods\" option from the Trade Hall.")

        self._add_section("Buff & Debuff Fixes")
        self._add_bullet("Damage-boost buffs (Frabjous Day, Try Me's Grow, the Big Bad Wolf's enrage...) "
                         "were only ever read by ally attacks — your own basic attacks and class skills "
                         "ignored them while the combat HUD still showed the tag. Player attacks and skills "
                         "now apply damage_boost, and enemies finally benefit from their own damage boosts.")
        self._add_bullet("Timed buffs used to tick down at the end of the round they were cast in, silently "
                         "eating one round of effect (a \"2 turn\" buff only covered 1 full round). Fresh "
                         "buffs now skip their first end-of-round tick, so they last their full advertised "
                         "number of rounds.")
        self._add_bullet("Regular enemies' timed buffs now decay instead of lasting forever, and the Big "
                         "Bad Wolf's Howl/enrage buffs tick down as intended now that they actually do "
                         "something.")
        self._add_bullet("Aura of Despair reworked: instead of a barely-noticeable -3 Constitution (flat "
                         "armor), it now makes all enemies take +15% damage for 3 turns — applied to every "
                         "enemy and read by basic attacks and skills alike, with a DT+15% HUD tag.")
        self._add_bullet("Fear immunity (Through the Forest, the Headless Oath ring) now actually blocks "
                         "Fear — previously the tag showed but no fear source ever checked it. Wonderland "
                         "floor bosses and the Wicked Witch's Emerald Cackle respect it now.")
        self._add_bullet("Overclock and Tinker Enhancement did nothing for the player — the power_buff "
                         "effect was only ever consumed by ally skills. It now empowers the recipient's "
                         "next damaging action for real: class skills, ally skills, and basic attacks all "
                         "consume it (multi-hit skills empower every hit), heal/support casts no longer "
                         "waste it, and the combat HUD shows a PWR+% tag while it's up.")
        self._add_bullet("The bonded Sunfire Band no longer snowballs a whole pack into Inferno off a "
                         "single action. Its fire spread was applying Blaze twice per enemy during one "
                         "multi-target attack (spread + direct hit) — one AoE instantly triggered the "
                         "burn system's same-tier escalation on everyone. The spread is now a pure seed: "
                         "it only lights enemies that aren't already burning, and your first strike on a "
                         "seeded enemy just fans the flame — the next one intensifies it. Inferno still "
                         "arrives on the second application (two strikes, or two AoE casts), and the "
                         "combat log now reports the tier you actually reach (\"flames intensify into "
                         "Inferno!\") instead of always claiming Blaze.")
        self._add_bullet("Fire weapons' Ignite trait now follows its advertised rarity curve: Common applies "
                         "Burn, Uncommon and Rare apply Blaze, Epic applies Inferno, and Legendary applies "
                         "Conflagration. Rare and Epic fire weapons had been landing one tier higher than "
                         "documented — an epic fire weapon opened with Conflagration on every basic hit. "
                         "Legendary fire weapons still ignite at Conflagration, and repeated hits still "
                         "intensify the flames as usual.")

        self._add_section("Barracks & Ally Skills")
        self._add_bullet("Barracks tier gates rescaled to match the campaign: Tier II now requires "
                         "Lv.8 (was 5), Tier III Lv.16 (was 10), and Tier IV Lv.25 (was 15), with "
                         "learning costs of 300/800/2000/5000 EXP. Master-tier skills are a mid-game "
                         "investment now, not an early unlock.")
        self._add_bullet("Barracks skills are now also gated by level cap: Tier III requires Cap 20 "
                         "and Tier IV requires Cap 30. High-level captures can no longer skip the "
                         "ladder — ascend them at the House Lounge first.")
        self._add_bullet("Learnable Barracks buffs no longer go stale: Strength Buff, Wisdom Buff, and "
                         "Heroic Onslaught now scale with the caster's level — roughly +1 per 7 levels "
                         "on top of their base value — and Weakening Curse scales a little slower "
                         "(+1 per 10 levels).")
        self._add_bullet("Fixed Regenerate and Mass Regenerate healing the player from a hard-coded "
                         "100 HP basis — the heal-over-time now uses the player's real max HP, exactly "
                         "as it always did for allies.")
        self._add_bullet("Dodge now grants the +2 Dexterity it advertises — previously only the 50% "
                         "evasion was applied.")
        self._add_bullet("Slow and Blind now strike the single targeted enemy as their descriptions "
                         "always said — they were silently affecting the whole enemy line.")
        self._add_bullet("Shield Wall's description now matches its effect: 40% damage reduction for "
                         "yourself or one ally.")

        self._add_section("Barracks Tiers V & VI")
        self._add_bullet("Two endgame skill tiers join the Barracks: Tier V Elite (Lv.35 · Cap 40 · "
                         "10,000 EXP) and Tier VI Legend (Lv.45 · Cap 50 · 20,000 EXP). Sixteen "
                         "new skills — eight per tier — covering every category.")
        self._add_bullet("New mechanics: Aegis Shell's barrier absorbs 30% of the caster's max HP; "
                         "Phoenix Call (revive 30%) and Radiant Rebirth (revive 75% + a 15% caster-HP "
                         "shield) bring revives to the learnable pool; Undying Vow prevents death "
                         "outright — the first lethal blow each ally takes leaves them at 1 HP; "
                         "Bulwark/Guardian's Vow shield the whole party; Fate's Favor and Astral Haste "
                         "empower it.")
        self._add_bullet("Thunder, earth, and light attacks finally exist in the learnable pool "
                         "(Thunderfall, Worldbreaker, Judgment), alongside Rend's bleed, Glacial "
                         "Requiem's slow, and Benediction/Cleansing Chorus for support.")
        self._add_bullet("Revive skills now only offer fallen allies as targets.")
        self._add_bullet("Fixed a bug where reviving an ally left them benched: the defeated flag was "
                         "never cleared, so a \"revived\" ally still couldn't act. Both the ally "
                         "revives and the Cleric's Resurrection now restore the ally properly.")

        self._add_section("Skill Mastery — ★ to ✦✦")
        self._add_bullet("Skill mastery now has five levels, shown as ★ / ★★ / ★★★ / ✦ / ✦✦. "
                         "Thresholds are 10/25/50/90/150 uses — ★-★★★ keep their original pacing, "
                         "so existing progress is untouched.")
        self._add_bullet("New mastery bonuses apply to every skill: ✦ (mastery 4) raises power to "
                         "+45% and extends effect durations by +1 turn (buffs, debuffs, barriers, "
                         "regeneration...) — on both class skills and ally skills; ✦✦ (mastery 5) "
                         "raises power to +60%, doubles effect potency on both sides, and brings "
                         "total cooldown reduction to −2.")
        self._add_bullet("Support skills scale with mastery now too — the same ×1.5 / ×1.75 / ×2.0 "
                         "potency applies to curse penalties, Hunter's Mark, Soul Fear, Aura of "
                         "Despair, damage-taken amps, barriers, evasions, damage buffs and more "
                         "(poison/burn/bleed already scaled).")
        self._add_bullet("Burn skills upgrade their burn TIER with mastery instead of raw damage: "
                         "+1 tier at ★★★ and +2 tiers at ✦✦ (capped at Conflagration) — a maxed "
                         "Soul Fire now burns as Inferno.")
        self._add_bullet("Revives are mastery-scaled and rebalanced: Phoenix Call 20% → 35% HP, "
                         "Radiant Rebirth 45% → 70% HP (was a flat 30% / 75%). Lich Queen's "
                         "innate Raise Dead rises 30% → 50% — the strongest revive stays hers.")
        self._add_bullet("The Arcane Tower's mastery research now goes all the way to the ✦✦ cap — "
                         "costs are 5,000 / 15,000 / 40,000 / 80,000 / 170,000 gold.")

        self._add_section("Crit Rework")
        self._add_bullet("Crit chance now caps at 100% instead of 20%, and everything above 100% converts "
                         "to bonus crit damage at 2:1 — stacking crit is never wasted. At the base ×1.5 "
                         "multiplier this keeps expected damage linear across the cap.")
        self._add_bullet("All crit sources now add up before the cap — Through the Forest, Vorpal Edge's "
                         "+30%, Fell the Wolf's +15%, and any future crit gear — and player class skills "
                         "support crit_bonus / crit_mult skill data like ally skills already did. Enemies "
                         "keep their 12% cap with no conversion.")
        self._add_bullet("Crit is now visible: Stats & Equipment shows your crit chance and crit damage "
                         "(including the overflow bonus), and in combat each party member shows "
                         "\"Crit: X% (×Y.YY)\" beside their name, updating live with buffs.")

        self._add_section("Quests & Story")
        self._add_bullet("A Journal-backed quest system has arrived. The first Main Quest — "
                         "\"The Stellar Summons\" — is delivered right after the tutorial: an "
                         "Archivist in Skylume is looking for help, and his story continues "
                         "through the Field Studies. Check your Journal (Inventory → Journal) "
                         "for live objectives with ✓/☐ tracking and a bit of a paper trail.")
        self._add_bullet("Completing the tutorial now grants a 200-gold Field Allowance from "
                         "the Adventurer's Guild — new adventurers begin with 300 gold, enough "
                         "to provision the road to Skylume.")
        self._add_bullet("Skylume's Star Tower is now a clickable landmark. Its Archivist takes "
                         "an interest in your party's bonds... and his companion is very glad "
                         "to meet you.")
        self._add_bullet("Command Resonance now governs party size: you set out with a single ally "
                         "at your side, and the Archivist's grades — Pitch, Timbre, Cadence, Chord, "
                         "Crescendo — grow your front rank and reserve bench as your household does. "
                         "Existing saves are rated from their current roster when they load.")
        self._add_bullet("The full Field Study chain is registered — A Willing Bond, Variety of "
                         "Command, The Broad Ledger, and Grand Resonance. Households that already "
                         "qualify (existing saves included) watch the studies resolve as the Archive "
                         "catches up, so the story never dead-ends at \"A Place to Belong\".")

        self._add_section("The White Knight — Pandemonium Floor 40")
        self._add_bullet("A second Pandemonium-exclusive superboss awaits on Floor 40: the White "
                         "Knight of the Fallen Empire, an Undead paladin of holy light. Phase 1 "
                         "teaches its 55% dodge; Phase 2 adds telegraphed Oathguard states (70% "
                         "dodge, ripostes that Expose you — max 2/round, first hit guaranteed — "
                         "plus a −20% ally hit-rate flourish); Phase 3 adds a 50% skill-dodge "
                         "Last Vigil — the first boss in the game that can slip your skills. "
                         "States warn a turn ahead and end in a negative-dodge window: hold "
                         "your burst for it.")
        self._add_bullet("Phase bars are sealed: no burst can skip a phase or one-shot the duel. "
                         "P1 holds at 65% HP and P2 at 30% — \"the white porcelain holds\" — until "
                         "the next round's transition, and Oathguard can't end until it has had at "
                         "least two full rounds. Time your windows around the floors.")
        self._add_bullet("Every riposte brands you with Expose — each stack makes the Knight's "
                         "attacks ignore 10% CON. Let a unit reach 6 stacks and it eats a "
                         "sure-hit Judgment Burst (Defend halves). Let three heroes carry stacks "
                         "at once and the Knight's oath flares for +25% damage. It also carries "
                         "75% status resistance (blessed plate).")
        self._add_bullet("First victory drops LAST OATH, the first unique rapier: a DEX-scaling "
                         "holy blade whose basic attacks apply Expose (double on crits) — "
                         "the answer to dodge games everywhere.")

        self._add_section("Superboss Status Resistance")
        self._add_bullet("Superbosses now resist debuffs. Every superboss carries a status resistance — "
                         "separate from its elemental profile — rolled against burn, bleed, poison, "
                         "shock, sunder, stun/freeze/sleep/paralyze/entomb, weaken, blind, silence, "
                         "dread, curse, elemental-weakness, item Expose, brush auras, and wedding "
                         "accessory procs. A resisted effect is announced and simply doesn't land; "
                         "regular enemies are unchanged.")
        self._add_bullet("Starting values run from 20–30% for early bosses (Queen of Hearts 20%, "
                         "Broodmother Vileheart 25%, Big Bad Wolf 25%), through 30–40% mid-game "
                         "(Sylvana 30%, Yinglong 40%, Rientrante 40%, Jabberwock 40%), up to 50–60% "
                         "for the hardest fights (Black Silence 50%, Palette 50%, Chrysalis 60%, "
                         "Mary Sue 60%). Expect status-focused builds to want a plan B against "
                         "the late-game roster.")

        self._add_section("New Guild Legacy Reward — The Prescript Ledger")
        self._add_bullet("The Guild Master turns to a second page: the PRESCRIPT LEDGER, a unique "
                         "accessory earned by fulfilling 10 guild bounties against LEVEL 20+ targets "
                         "(Sky Piercer is unchanged at 5 distinct Super Bosses). Both are claimed "
                         "under Guild → Legendary Rewards.")
        self._add_bullet("While worn — by you or an ally — the ledger issues a Prescript every "
                         "round: shed blood on the marked Target, exercise the art (any skill; "
                         "workshops, Furioso and brush exhibits all count), use an item, or endure. "
                         "Fulfilling it stacks Grace of the Prescript: +2% damage, +1.5% crit and "
                         "1.5% max-HP regen per stack (cap 9), plus +10/20/30% skill damage against "
                         "the marked Target at 3/6/9 stacks. Grace resets between fights.")
        self._add_bullet("Ignore a Prescript you could have followed and Karmic Consequence "
                         "accrues: +3% damage taken per stack. At 6 stacks the ledger collects its "
                         "due — a sure-hit Karmic Retribution (8% max HP + 20; Defend halves). "
                         "Fulfilling a Prescript atones 1 Karma at any Grace level — even at the "
                         "cap — though Karma still stacks at max Grace if you ignore one: obey "
                         "the page, not just the buff.")

        self._add_section("Time Rework — The Day in Blocks")
        self._add_bullet("The clock is yours now: the real-time tick is gone and every day is a "
                         "budget of 24 blocks — Morning, Noon and Night, eight each. Quick errands "
                         "are free, ordinary visits and dungeon rooms cost a block, major rites "
                         "cost two, and the top bar shows the phase with the blocks left in it. "
                         "Nothing moves unless you act — and existing saves simply wake up on the "
                         "morning of their current day.")
        self._add_bullet("Nights are for sleeping: the inn and your house only take guests at "
                         "Night, and a day that ends without sleep leaves you Fatigued — the top "
                         "bar and the battle HUD both show the stacks, and every stack dulls your "
                         "stats. At Night, a carrying mind starts seeing things: hazy figures "
                         "that fight you alone, because your companions cannot see them at all. "
                         "Ending one lifts the lightest burdens of exhaustion (stack II fades to "
                         "I; deeper, only real sleep mends it) — and losing such a fight does not "
                         "kill you: you come to at 1 HP with your party mid-panic.")
        self._add_bullet("Waiting is a choice: [W] in a city (or Waiting at home) offers A Brief "
                         "moment — a single block — or A While, straight through to the next "
                         "phase; from Night, A While walks you into morning, awake and tired.")
        self._add_bullet("Cities keep schedules: most trades keep Morning–Noon hours and their "
                         "closed shopfronts dim on the city map, the star tower works Noon–Night, "
                         "and the black market only opens at dusk — while inn, house, guild, "
                         "arcane tower and harbour run around the clock. Night is also when the "
                         "roads and seas bite harder.")
        self._add_bullet("Travel is priced in blocks — one per started half-hour plus supplies, "
                         "shaved by your mount — and spent as each leg completes, so a long haul "
                         "can genuinely take days; the map and every route offer show the cost "
                         "up front. When night falls on the road you can Set Camp with a Portable "
                         "Camp (sold at any shop) or on a Caravan mount and wake without fatigue; "
                         "marching on stacks it. Sailings depart at any hour.")
        self._add_bullet("Wonderland keeps its own time: inside the storybook the clock simply "
                         "does not exist. No blocks pass, no shop closes, the day is whatever the "
                         "book decides it is — and when you leave, not a minute has followed you "
                         "home.")

        self._add_version("v0.1.7.1 — The Chromatic Artisan")

        self._add_section("World Events Now Actually Happen")
        self._add_bullet("The daily event system was announcing effects that never fired — Traveling "
                         "Merchant, New Moon, Full Moon, Month-End Festival, Heavy Rain, Bounty Rush, "
                         "Monster Surge, Lucky Day, and Blessed Wind are all now wired into gameplay.")
        self._add_bullet("Market Day (days 7 & 21): the Traveling Merchant now sets up a stall inside "
                         "the Guild Hall with buy/sell stock at road rates.")
        self._add_bullet("New Moon grants +25% favor on bounty turn-ins; Bounty Rush boosts bounty "
                         "gold and favor by 50%; Full Moon raises enemy strength by 20%; Month-End "
                         "Festival cuts shop prices by 20%; Heavy Rain slows travel by 30%; Monster "
                         "Surge adds an extra enemy per dungeon room; Lucky Day adds 15% gold drops.")
        self._add_bullet("Blessed Wind (+1 all stats) now properly expires when the day changes.")

        self._add_section("New Events")
        self._add_bullet("Tax Day — shop prices +15%. Scholar's Day — +25% XP. Peaceful Skies — "
                         "monsters 10% weaker. Crimson Dawn — monsters 15% stronger.")
        self._add_bullet("Monster Girl Season — +15 capture chance. Wary Prey — -10 capture chance. "
                         "Ill Omen — dungeons swarm with foes and gold is scarcer (-5%).")
        self._add_bullet("Difficulty stacking is capped at 2.2x so stacked night/event modifiers "
                         "can't spiral out of control.")

        self._add_version("v0.1.7.0")

        self._add_section("New Super Boss: Palette, the Chromatic Artisan")
        self._add_bullet("A new tier-8 superboss joins the normal superboss rotation — a painter "
                         "whose canvas is reality, and who teaches you the very mechanics her "
                         "drops later grant.")
        self._add_bullet("7-color stance system: Palette cycles Crimson, Azure, Gold, Verdant, Umber, "
                         "Alabaster, and Obsidian. Each stance changes her attacks, resistances "
                         "(0.6 vs her own element, 1.4 vs the counter element), and a unique boss "
                         "passive (damage boost, regen, initiative, dodge, defense, self-cleanse, "
                         "lifesteal). Physical and magical stay 0.8 in every stance.")
        self._add_bullet("Paint system: her attacks stain the whole party with Paint stacks. At 5 stacks "
                         "the paint bursts into the stance's color-matched debuff (Burn, Slow, Shock, "
                         "Blind, Weaken, Silence, Dread); at 6-7 it explodes at +50% potency. "
                         "Phase 1 cap is 5, phase 2+ is 7.")
        self._add_bullet("3 phases: Underpainting, Layering (a Blank Canvas transition that wipes every "
                         "debuff and heals her), and Masterpiece (Dual Palette — two colors, two "
                         "passives, two weaknesses).")
        self._add_bullet("Signature: below 10% HP she paints your name — a 2-turn instant-KO charge, "
                         "interrupted by dealing 40+ total party damage during the charge. "
                         "Fixative locks your paint in place for 3 turns — no growth, no burst, "
                         "no cleanse.")

        self._add_section("New Unique Equipment")
        self._add_bullet("Palette's Brush (100% drop) — the game's second no-skills weapon. Replaces ALL "
                         "class skills with the brush kit: stance commitment (1.35x elemental attacks), "
                         "stroke painting (3rd stroke = Pigment Explosion, +50%), permanent battle auras "
                         "(Wet Palette: 3 slots, rank up to 3), and one-use Exhibits (Impasto, "
                         "Chiaroscuro, Signature) unlocked at 6/12/18 strokes. Fully usable by allies.")
        self._add_bullet("Blank Canvas Shawl (100% drop) — once per combat, a free action that wipes every "
                         "debuff (including Paint), heals 15% max HP, and grants Afterimage (blocks the "
                         "next 2 debuffs for 2 turns) — at the cost of your own buffs.")

        self._add_section("New Ally: Palette (Heroine)")
        self._add_bullet("Not capturable — recruited through \"The Artist's Choice\" after the fight if you "
                         "let a full Paint burst dry on your skin, or if you survive her finished "
                         "Signature (\"You held the canvas\").")
        self._add_bullet("Joins directly as a permanent party member (Elemental race) with a degraded "
                         "masterpiece kit: Brushstroke (her cycling color), Spectrum (3 random-element "
                         "hits), and Signature (2.5x, 1-turn telegraph, cannot be defended).")
        self._add_bullet("Original-equipment synergies: wielding her own brush locks her into the full "
                         "brush kit and grants half-strength boss passives per stance; wearing her own "
                         "shawl upgrades Blank Canvas to a party-wide cleanse and heal.")

        self._add_section("New Wedding Accessory")
        self._add_bullet("Palette's Palette (soulbound Legendary at 200 affection) — Masterclass: while "
                         "Palette is in the party, brush Exhibits unlock at 5/10/15 strokes and deal "
                         "+15% damage.")

        self._add_section("Engine Additions & Fixes")
        self._add_bullet("New party damage hook in superboss fights (enemy-HP tracking across player and "
                         "ally turns) powering the Signature interrupt.")
        self._add_bullet("The generic elemental debuff proc is suppressed for Palette — paint bursts are "
                         "her only debuff channel.")
        self._add_bullet("Enemies can carry an initiative bonus; Paint shows as a Painted status tag; "
                         "enemy status lines display active brush strokes.")
        self._add_bullet("Afterimage gate added to all debuff application paths, including Paint.")

        self._add_section("Bug Fixes")
        self._add_bullet("Fixed a bug where the Tarnished Jade PIN status tag appeared even when "
                         "the Jade wasn't equipped. Combat start unconditionally set pin stacks to 1 "
                         "and end-of-combat cleanup never reset them, so the phantom pin persisted "
                         "into the save and showed on the city party card. Pins now initialize only "
                         "when the Jade is actually worn (player and allies), are cleared after "
                         "combat, and the tag only renders for a real Jade wielder.")

        self._add_version("v0.1.6.2")

        self._add_section("Bug Fixes")
        self._add_bullet("Fixed a bug where capturing or recruiting a monster girl in a new city "
                         "would silently create a duplicate house instead of sending the girl to "
                         "the player's existing house. The save_house_data() function now routes "
                         "girls to the existing house across all cities, and only auto-creates a "
                         "house as a fallback when the player has none at all.")
        self._add_bullet("Fixed a bug where ally equipment, active buffs, and race passives were "
                         "not counted during dungeon stat-check events (Wounded Adventurer, Ancient "
                         "Corpse, Monster Approaching, trap disarm attempts, and all Wonderland "
                         "encounters). Only raw base attributes were used — now compute_ally_stats() "
                         "is called so allies contribute their full effective stats just like the player.")
        self._add_bullet("Fixed a bug in the Rientrante superboss fight where rapidly pushing the "
                         "boss from 65% to 50% HP caused Frost Shards to survive into Phase 2, "
                         "resulting in 7 simultaneous enemies (boss + 3 shards + Eye + 2 Arms) that "
                         "overflowed the combat menu and made actions unselectable. Lingering shards "
                         "are now dissolved when Phase 2 triggers.")
        self._add_bullet("Added a global enemy cap to all superboss fights: if any boss spawns more "
                         "than 5 enemies, the lowest-HP non-boss enemies are automatically culled "
                         "to prevent combat menu overflow.")
        self._add_bullet("Fixed a rare soft-lock in the Yinglong superboss fight where the Heaven "
                         "Pinning Wedge could fail to spawn during the Immortal Rage phase, leaving "
                         "Yinglong permanently immortal. Wedge creation is now wrapped in error "
                         "handling — if it fails, immortality is stripped so the fight can continue.")
        self._add_bullet("Fixed a bug where corrupted or partial dungeon save state (saved floor, "
                         "rooms, or room index) could cause the player to teleport to a lower floor "
                         "or reset to Room 1 mid-run. Saved dungeon state is now validated before "
                         "being restored — invalid state is auto-wiped and the floor regenerates "
                         "fresh instead of silently corrupting the run.")

        self._add_section("New Monster Girls & Wedding Accessories")
        self._add_bullet("10 new monster girls are now recruitable/capturable across various dungeons: "
                         "Gear Maiden (Gnome, L23), War Sister (Orc, L25), Dusk Weaver (Shadow, L27), "
                         "Automata Doll (Clockwork, L29), Maiden of Stone (Giant, L32), "
                         "Flame Heart (Dragonkin, L39), Seraph Ascendant (Angel, L42), "
                         "Star Court Dancer (Fey, L44), Infernal Bride (Demon, L47), "
                         "and Grave Queen (Undead, L50).")
        self._add_bullet("Each new monster girl has a unique Legendary soulbound wedding accessory "
                         "earned at 200 affection after engagement, with active combat effects and "
                         "enhanced Bonded effects when she is in the active party:")
        self._add_sub_bullet("Gearheart Pendant (Gear Maiden) — Overclock: first attack bonus damage + "
                             "skill cooldown refresh chance. [thunder/magical]")
        self._add_sub_bullet("War-Sister's Bond (War Sister) — Blood Fury: ramps up STR/CON at low HP. "
                             "[physical/fire]")
        self._add_sub_bullet("Twilight Shroud (Dusk Weaver) — Dusk Weave: evasion + on-hit blind/slow. "
                             "[dark/magical res]")
        self._add_sub_bullet("Precision Core (Automata Doll) — Auto Guard: damage reduction + regen + "
                             "combat-start CON boost. [physical/thunder res]")
        self._add_sub_bullet("Mountainheart Band (Maiden of Stone) — Stone Ward: max HP + physical "
                             "resistance + stun immunity. [earth/physical res]")
        self._add_sub_bullet("Eternal Ember (Flame Heart) — Dragon Heart: fire damage bonus + "
                             "spreading burn on hit. [fire/light]")
        self._add_sub_bullet("Seraph's Feather (Seraph Ascendant) — Seraph Light: ally-scaling damage "
                             "+ party heal + debuff cleanse. [light/wind]")
        self._add_sub_bullet("Constellation Waltz Ring (Star Court Dancer) — Star Waltz: dodge + "
                             "counter-attack + DEX boost on dodge. [light/magical]")
        self._add_sub_bullet("Infernal Vow Band (Infernal Bride) — Infernal Vow: fire/dark damage + "
                             "burn/dread on hit + retribution when struck. [fire/dark]")
        self._add_sub_bullet("Deathward Crown (Grave Queen) — Grave Reign: combat-start AoE + "
                             "on-kill heal + stacking all-stat buff (up to 3×). [dark/earth]")

        self._add_version("v0.1.6")

        self._add_section("Elemental Profile Debuff System")
        self._add_bullet("Enemies now have a secondary debuff channel driven by their elemental affinity. "
                         "Each enemy's strongest elemental damage type (fire, water, thunder, etc.) can proc "
                         "a thematically appropriate debuff on-hit: Fire→Burn, Water→Slow, Thunder→Shock, "
                         "Wind→Blind, Earth→Weaken, Light→Silence, Dark→Dread, Physical→Bleed, Magical→Confusion.")
        self._add_bullet("Proc chance scales dynamically with combat round (longer fights = more dangerous) "
                         "and enemy level (higher level = more proficient). Formula: BASE × round_factor × "
                         "level_factor. Early-game low-level enemies barely proc; late-game bosses are "
                         "genuinely threatening.")
        self._add_bullet("Elemental debuffs compose with racial debuffs — a Fire-aspected Beast (e.g. "
                         "Hellhound) can inflict both Bleed (racial) and Burn (elemental) in a single hit, "
                         "making every enemy combination feel distinct.")
        self._add_bullet("Enemy name keywords (Flame, Frost, Lightning, Shadow, etc.) automatically feed "
                         "into the elemental profile via the existing ELEMENTAL_KEYWORDS system, so named "
                         "enemies naturally gain their thematic secondary debuff with no extra configuration.")
        self._add_bullet("Added player-facing apply functions (apply_shock_to_player, apply_slow_to_player, "
                         "apply_confusion_to_player) and tick handling for Shock (DoT + 25% stun proc) and "
                         "Confusion in tick_player_debuffs — these debuff types are now fully supported on "
                         "players for the first time.")
        self._add_bullet("Added backward-compatible aliases (apply_confusion, apply_slow) in status_effects "
                         "to fix a pre-existing crash when Storybook enemies attempted to apply Confusion "
                         "via a missing import.")

        self._add_section("Full Skill Elemental Rework")
        self._add_bullet("Every skill in the game (186 total) now has a specific elemental profile from the "
                         "9-element system: fire, water, thunder, wind, earth, light, dark, physical, magical.")
        self._add_sub_bullet("48 class skills assigned elements — e.g. Fireball→fire, Backstab→dark, "
                             "Shield Slam→earth, Bladestorm→wind, Holy Smite→light, Soul Fire→fire.")
        self._add_sub_bullet("31 learnable skills assigned elements — e.g. Haste→thunder, Inferno→fire, "
                             "Perfect Guard→light, Shadow Dance→dark, Regenerate→earth.")
        self._add_sub_bullet("107 ally innate skills assigned elements — every monster girl skill now has "
                             "thematic elemental affinity (Goblin Dart→water, Oni Smash→fire, "
                             "Valkyrie Strike→light, Necrotic Bolt→dark, etc.).")
        self._add_bullet("Removed the hardcoded SKILL_ELEMENTS dictionary from combat/skills.py. Elemental "
                         "profiles are now read directly from the YAML skill definition files, making them "
                         "data-driven and easily moddable.")
        self._add_bullet("Ally skills now properly apply elemental damage/resistance via calculate_elemental_damage(). "
                         "Previously, ally skills had no elemental interaction at all — now their elemental "
                         "profile matters against enemy resistances just like player skills.")
        self._add_bullet("Skill descriptions in combat now display a colored elemental tag (e.g. [FIRE] in red, "
                         "[DARK] in purple, [LIGHT] in white) when a skill is selected, so you always know "
                         "what element you're about to use.")
        self._add_bullet("Fallback: skills without an elemental field are treated as neutral (1.0× multiplier, "
                         "no elemental interaction).")

        self._add_section("New Super Bosses")
        self._add_bullet("Chrysalis, the Entangled One — Pandemonium dungeon exclusive, appears on floor 20. "
                         "3-phase temporal boss with Past/Present/Future aspects, linked shards, and a "
                         "Paradox Fracture vulnerability mechanic.")
        self._add_bullet("The Black Silence — 3-phase superboss wielding 9 workshop attacks, "
                         "revival mechanic, and Furioso ultimate.")

        self._add_section("New Items")
        self._add_bullet("Chronoweave Mantle (Legendary armor) — guaranteed drop from Chrysalis. "
                         "Builds Momentum stacks on hit.")
        self._add_bullet("Fractured Hourglass (Legendary infinite consumable) — guaranteed drop from Chrysalis. "
                         "Resets 1 skill cooldown per floor, reusable.")
        self._add_bullet("Certain Someone's Black Gloves (Legendary weapon) — drop from The Black Silence. "
                         "Grants the 9 workshop attacks.")

        self._add_section("Wonderland Heroine Quest Items")
        self._add_italic('"Every story needs someone who believes in happy endings."')
        self._add_bullet("Alice: ??? Blade quest chain. Speak to the Fairy Godmother at Wonderland's "
                         "Temple (floor 20+) to receive a rusted blade. Give it to Alice at the Inn "
                         "to unlock her Vorpal skills. After defeating the Jabberwock, return to the "
                         "Godmother with the Vorpal Blade Fragment to forge the true Vorpal Blade.")
        self._add_bullet("Red Hood: Grandmother's Axe quest chain. Find the Woodcutter in Wonderland's "
                         "Black Market (floor 20+) to receive his broken axe. Give it to Red Hood at the "
                         "Inn to unlock her hunting skills. Use the Wolf's Tooth and Crimson Hood Scrap "
                         "from the Big Bad Wolf to reforge it into Grandmother's Axe.")
        self._add_bullet("Dorothy: Silver Slippers quest chain. Meet the Wizard of Oz in Wonderland's "
                         "Arcane Tower (floor 30+) to receive dormant silver slippers. Give them to "
                         "Dorothy at the Inn to unlock her cyclone magic. Use the Witch's Hat and "
                         "Emerald Flame Crystal from the Wicked Witch to awaken the Ruby Slippers.")
        self._add_sub_bullet("Each heroine's quest item grants 2 new skills and 1 ultimate skill on upgrade.")
        self._add_sub_bullet("Unequipping the item reverts skills. Items persist through permanent ally promotion.")

        self._add_section("Combat — Burn Rework")
        self._add_bullet("Burn is now a 5-tier debuff system instead of a flat damage value. "
                         "Each tier has a unique name, damage, and HUD tag.")
        self._add_sub_bullet("Tier 1: Singe (3/turn, SNG) — Tier 2: Burn (6/turn, BRN) — "
                             "Tier 3: Blaze (10/turn, BLZ) — Tier 4: Inferno (18/turn, INF) — "
                             "Tier 5: Conflagration (30/turn, CFL)")
        self._add_bullet("Repeated burn applications now intensify the flames: same-tier reapplication "
                         "bumps the burn up by 1 tier. Higher-tier sources upgrade directly. "
                         "Lower-tier sources refresh duration without downgrading. Capped at Conflagration (T5).")
        self._add_bullet("Ignite weapon trait (fire element) no longer deals % max HP burn — it now "
                         "applies a burn tier based on weapon rarity: Common=Burn, Uncommon=Blaze, "
                         "Rare=Blaze, Epic=Inferno, Legendary=Conflagration.")
        self._add_bullet("Chrysalis superboss burns now apply Conflagration (T5, 30/turn) directly.")
        self._add_bullet("All fire skills, wedding accessories, and enemy fire attacks now use the "
                         "tiered burn system. Legacy damage= keyword is auto-converted for backward compatibility.")
        self._add_bullet("Combat HUD now shows tier-specific burn tags (SNG/BRN/BLZ/INF/CFL) instead "
                         "of the generic BRN. Combat log messages include tier names (e.g. 'suffers 18 Inferno damage').")
        self._add_bullet("Sunder (Physical trait) and Pierce (Magical trait) now always display "
                         "visual feedback in the combat log on every hit, with penetration percentages shown.")

        self._add_section("Bug Fixes")
        self._add_bullet("Fixed a bug where the player could lower an item's rarity with a Scroll of Fusion, "
                         "enchant it cheaply, then upgrade the rarity back. Now the player cannot lower rarity "
                         "via fusion, and upgrading rarity on an already-enchanted item costs exponentially more gold.")
        self._add_bullet("Fixed a bug where failing a dungeon stat check would always deal damage to the player, "
                         "even if an ally performed the check. Damage now goes to whoever made the attempt.")
        self._add_bullet("Fixed a bug where Arcane Tower teleportation showed all visited cities as "
                         "destinations instead of only cities that have an arcane tower. Teleportation "
                         "to Isle of Glass is now disabled (unstable magic prevents inbound teleportation), "
                         "but teleporting from Isle of Glass to other tower cities still works.")
        self._add_bullet("Fixed a bug where Mook Workshop lifesteal (Black Silence gloves) would always "
                         "recover 0 HP. The player's max HP key was missing from the actor dict, causing "
                         "the heal cap to fall back to current HP — making lifesteal silently useless.")
        self._add_bullet("Fixed a bug where the Slitcurrent and Broodmother superboss fights would crash "
                         "when the boss tried to spawn minions (Dream Floatsam / Vileheart Spiderling). "
                         "The minion enemy definitions were never migrated from the old enemy dictionary "
                         "to the YAML data files, causing a KeyError that kicked the player back to the "
                         "dungeon log screen.")
        self._add_bullet("Fixed a bug where using Mass Regenerate or Dark Blessing (any skill with "
                         "a regen effect targeting all allies) would crash the combat thread with an "
                         "AttributeError, causing the combat overlay to close and the dungeon run to "
                         "freeze while the dungeon thread waited indefinitely for a combat result.")
        self._add_bullet("Fixed a bug where Potion Sickness blocked ALL consumable and utility items "
                         "instead of only healing potions. Buff items, bombs, flasks, and escape items "
                         "are now usable during potion sickness.")
        self._add_bullet("Fixed a bug where allies had no Potion Sickness mechanic — they could "
                         "freely chain healing potions with no cooldown. Allies now gain potion "
                         "sickness after using a healing consumable, and it ticks down each round.")
        self._add_bullet("Fixed a bug where Armour Shatter Flask would never ask for a target, "
                         "causing the armour reduction effect to silently fail. Added a fallback "
                         "that auto-selects a valid enemy if target resolution is skipped.")
        self._add_bullet("Fixed a bug where using Armour Shatter Flask, Poison Flask, Stun Bomb, "
                         "Throwing Knife, Holy Water, or Capture Nets from the inventory bag or GUI "
                         "inventory outside of combat would silently consume the item with no effect. "
                         "These items now show a warning and are not consumed.")
        self._add_bullet("Fixed a bug where Fire Bomb, Thunder Bomb, and Acid Flask had no debuff "
                         "effects despite having themed status effect functions available in the engine. "
                         "They were pure damage items with no elemental identity.")
        self._add_bullet("Fixed a bug where Yinglong's Heaven Pinning Wedge (Phase 4) would die instantly "
                         "after firing at turn-end, without triggering on_kill_hook. The OneHitWedgeDict "
                         "wrapping code accidentally snapped the wedge's HP from 30 to 0, leaving "
                         "wedge_active permanently True and Yinglong permanently immortal — soft-locking "
                         "the fight.")
        self._add_bullet("Fixed a bug where Black Silence Gloves workshop attacks (Ranga, Zelkova, "
                         "Allas, Furioso, etc.) and Furioso would never call on_kill when defeating "
                         "an enemy. If the Heaven Pinning Wedge was killed by a workshop attack, "
                         "the backlash and respawn never triggered — soft-locking the Yinglong fight "
                         "the same way. Affected both player and ally workshop users.")
        self._add_bullet("Fixed a bug where ally Abyss Fang cooldowns, Abyssal Tempo, and Captain's "
                         "Cutlass state were never ticked in superboss combat. In normal combat these "
                         "tick every round, but superboss_combat_loop only ticked the player's state. "
                         "Allies with Abyss Fang could use Wield the Abyss once and then never again — "
                         "the cooldown was permanently stuck.")

        self._add_section("Arcane Tower Improvements")
        self._add_bullet("Research now scales by player level (5 tiers: Novice Study → Astral Projection).")
        self._add_bullet("Skill mastery can now be upgraded at the tower.")
        self._add_bullet("Teleport between any cities that have an arcane tower.")
        self._add_bullet("Craft a Scroll of Fusion by sacrificing 3 pieces of equipment of the same rarity.")
        self._add_bullet("Arcane Blessings and Mystic Blessings — temporary buffs for your next dungeon run.")
        self._add_bullet("Pandemonium curse negation buff (Isle of Glass tower only).")

        self._add_section("Arcane Tower Relocation")
        self._add_bullet("The Cinderpeak Arcane Tower has been decommissioned — volcanic instability "
                         "made the Spire of Molten Glass unsafe for research.")
        self._add_bullet("A Northern Spire now stands in Stormhold, channeling aurora-lit ley energy "
                         "through the ancient glacier ice.")
        self._add_bullet("The Amber Spire has risen in Dunemar, where desert winds hum through "
                         "crystallized dune-glass resonance chambers.")

        self._add_section("Barracks — Training Dummy")
        self._add_bullet("Added a sparring dummy to the barracks. Player can adjust its stats "
                         "and elemental resistances freely.")
        self._add_bullet("Use Flee to exit dummy combat.")

        self._add_section("Party Display & UI")
        self._add_bullet("Fixed party status alignment in the city hub — members with status effects (CRS, "
                         "BLS, etc.) no longer misalign HP bars vertically against members without effects.")
        self._add_bullet("Removed sword (⚔) and shield (🛡) emoji from party member labels to reclaim "
                         "horizontal space, preventing the 8th party member from being cut off.")
        self._add_bullet("Dungeon Party Status panel replaced with a modern GUI: color-coded HP bars, "
                         "level display, FRONT/BACK section separators, and scroll-wheel support — no more "
                         "raw terminal ASCII in that panel.")

        self._add_section("Facility Header Update")
        self._add_bullet("Time is now shown in the GUI header instead of being printed in the terminal.")

        self._add_section("Ally Equipment")
        self._add_bullet("Allies can now equip unique items beyond just wedding accessories.")

        self._add_section("Time Tick")
        self._add_bullet("The game now advances 1 in-game minute every 2 real seconds. "
                         "A full in-game day passes in 48 real minutes.")

        self._add_section("Wonderland")
        self._add_italic('"Hehe, look — we broke the 4th wall!"')
        self._add_italic('"Quiet, you and your stupid hat. Do your job properly."')
        self._add_bullet("A hidden city accessible only through the Veilholt Arcane Tower.")
        self._add_bullet("To unlock it, the player needs 3 things:")
        self._add_sub_bullet("1. Clear floor 20 across 2 different dungeon types.")
        self._add_sub_bullet("2. The world must be on day 60+.")
        self._add_sub_bullet("3. Buy a shard from the Veilholt Black Market, then visit the "
                            "arcane tower and choose the mysterious book.")
        self._add_bullet("New biome: wonderland.")
        self._add_bullet("New enemy race: Storybook.")

        self._add_section("Wonderland Curses & Shadows")
        self._add_bullet("Each Wonderland floor now rolls a whimsical 'quirk' — mostly-beneficial effects "
                         "like Tea Party Regen (bonus healing), Cheshire Cat's Favor (enemy miss chance), "
                         "and Queen's Decree (bonus gold). 10 quirks total, scaling with floor depth.")
        self._add_bullet("Heroines (Alice, Red Hood, Dorothy) now have unique dialogue reacting to each "
                         "floor quirk and shadow choice — 120+ new voice lines.")
        self._add_bullet("From Floor 41 onward, Wonderland grows darker. Each floor the player must "
                         "choose a persistent negative Shadow (10 varieties) that stacks across floors. "
                         "Shadows include Jabberwock's Wrath (room damage), Off With Their Heads (increased "
                         "enemy damage), Madness Contagion (stat penalties), and more.")
        self._add_bullet("Floor 46 clears all Shadows and escalates — the player picks 2 Shadows per floor "
                         "from a refreshed pool, stacking up to 8 by Floor 49.")
        self._add_bullet("On Floor 50, the player's final 2 Shadow choices directly empower the Mary Sue "
                         "superboss. Each Shadow grants her a unique passive: Plot Armor Reinforcement, "
                         "Time Lord (extra turns), Execution Threshold, Vorpal Resistance, Maddening Aura, "
                         "and more — making every Mary Sue fight different.")

        self._add_section("Capture Net Rework")
        self._add_bullet("Capture Nets are now exclusive to the Black Market — they no longer appear in "
                         "regular shops, dungeon drops, or travel events.")
        self._add_bullet("Three tiers of Capture Nets are now available at the Black Market:")
        self._add_sub_bullet("Capture Net — 550 gold, +25 catch bonus, max 10 per player")
        self._add_sub_bullet("Reinforced Capture Net — 1,200 gold, +37 catch bonus, max 5 (unlocks at Floor 20+)")
        self._add_sub_bullet("Mythril Capture Net — 3,000 gold, +55 catch bonus, max 3 (unlocks at Floor 40+)")
        self._add_bullet("Each tier enforces its own purchase cap independently — buying regular nets "
                         "doesn't count against your reinforced or mythril net limits.")
        self._add_bullet("The capture formula now uses each net's own rarity_mult_bonus directly instead "
                         "of the old ITEM_RARITY lookup, making tiered nets self-contained and extensible.")
        self._add_bullet("Net selection in combat now shows the catch bonus (+N) instead of a meaningless "
                         "rarity label.")

        self._add_section("Utility Item Debuff Expansion")
        self._add_bullet("Fire Bomb now applies Burn (tier 2, 6 damage/turn for 3 turns) on hit — "
                         "it's no longer just raw damage.")
        self._add_bullet("Thunder Bomb now applies Shocked (5 damage/turn + 25% stun proc per tick, "
                         "3 turns) on hit — Thunder element finally has an identity.")
        self._add_bullet("Acid Flask now applies Expose Armour (2) on hit — corrodes enemy plating "
                         "just like Armour Shatter Flask.")
        self._add_bullet("Burn and Shock effects are now supported across the full item pipeline: "
                         "build_item, combat item handler, ally item handler, and inventory restrictions.")
        self._add_sub_bullet("Combat-only items (bombs, flasks, nets) are now blocked from being used "
                             "outside of combat via the inventory bag and GUI inventory screen — they "
                             "show 'can only be used in combat' instead of being silently consumed.")

        self._add_section("Throwing Damage Rebalance")
        self._add_bullet("Dexterity now grants +3 thrown damage per 5 DEX (up from +1). "
                         "Throwing builds are properly rewarded for DEX investment.")
        self._add_bullet("All thrown utility item base damages reduced ~35% to shift power into "
                         "DEX scaling. At 20 DEX damage is roughly equal to old values; at 30+ DEX "
                         "throwing becomes stronger than before.")
        self._add_bullet("Allies now also scale thrown item damage with their Dexterity (previously "
                         "allies dealt flat base damage with no DEX bonus at all).")

        self._add_section("Dungeon Check — Pass Probability Display")
        self._add_bullet("When a dungeon event requires a stat check (Charisma, Wisdom, Strength, "
                         "Dexterity, or Agility for trap rooms), the party member selection menu now "
                         "shows each character's probability of passing the check alongside their HP.")
        self._add_sub_bullet("Before: '[1] prism (You) — HP: 192/192'")
        self._add_sub_bullet("After:  '[1] prism (You) — HP: 192/192  |  Pass: 65%'")
        self._add_bullet("Probability is calculated as the chance to roll (DC − stat) or higher on a d20, "
                         "clamped between 5% (natural 20 always succeeds) and 95% (natural 1 always fails).")
        self._add_bullet("Applies to all stat-check events (Wounded Adventurer, Ancient Corpse, Monster "
                         "Approaching, and all Wonderland encounters) plus trap room disarming attempts.")

        t.configure(state=tk.DISABLED)

    def _add_version(self, text):
        """Insert a version header."""
        self.text_widget.insert(tk.END, f"\n{text}\n", "version")
        self.text_widget.insert(tk.END, "─" * 50 + "\n", "spacer")

    def _add_section(self, text):
        """Insert a section header."""
        self.text_widget.insert(tk.END, f"\n{text}\n", "section")

    def _add_bullet(self, text):
        """Insert a bullet point."""
        self.text_widget.insert(tk.END, f"  • {text}\n", "bullet")

    def _add_sub_bullet(self, text):
        """Insert an indented sub-bullet."""
        self.text_widget.insert(tk.END, f"    {text}\n", "sub_bullet")

    def _add_italic(self, text):
        """Insert italic flavortext."""
        self.text_widget.insert(tk.END, f"  {text}\n", "italic")

    def handle_escape(self):
        """Navigate back on Escape."""
        if self.sm:
            self.sm.go_back()
