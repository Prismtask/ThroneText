"""
gui/screens/changelog_screen.py — Changelog viewer showing version history.
"""

import tkinter as tk

from gui.screens.base_screen import BaseScreen
from gui.theme import Theme


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
