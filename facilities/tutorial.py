# facilities/tutorial.py
"""Tutorial for newly created characters, presented through the facility UI.

Runs inside gui/screens/facility_screen.py (the same generic wrapper used by
the shop, inn, blacksmith, etc.): everything printed here appears in the GUI
output panel and every question becomes clickable buttons.

Entry point: tutorial_menu(player, city_id=None)
"""

from gui.terminal import term
from save_load import save_game


# ── FacilityScreen subclass with the game clock paused ────────────────────────

from gui.screens.facility_screen import FacilityScreen, _FacilityStopped


class TutorialScreen(FacilityScreen):
    """FacilityScreen whose game clock is effectively paused while reading."""

    @property
    def tick_interval_ms(self):
        # One tick only after ~24 real hours — the clock never advances
        # while the player reads the tutorial.
        return 1000 * 60 * 60 * 24


# ── Small formatting helpers ──────────────────────────────────────────────────

def _header(text):
    rule = "═" * min(len(text) + 4, 70)
    term.print(rule)
    term.print(f"  {text}")
    term.print(rule)


def _page(lines):
    """Print a page of plain text, one line at a time."""
    for line in lines:
        term.print(line)


# ── Tutorial sections ─────────────────────────────────────────────────────────

def _section_city():
    term.clear()
    _header("THE CITY & ITS SERVICES")
    _page([
        "You awaken in Solmere, the starting city, at 8:00 AM with",
        "100 gold in your pocket.",
        "",
        "Each city has its own services, reached by clicking the",
        "buildings on the city map or the service buttons:",
        "",
        "  Shop       - buy consumables and gear, sell loot.",
        "  Inn        - rest to fully restore HP (free in Solmere).",
        "  Blacksmith - craft and upgrade equipment.",
        "  Temple     - blessings and curse removal.",
        "  Guild      - raise your level cap, clear biomes.",
        "  Trade Hall - trading opportunities.",
        "",
        "Other cities add more: Barracks (ally training and a",
        "sparring dummy), Gift Shop, Arcane Tower, Herbalist, Port,",
        "Shipyard, and the Black Market (the only source of capture",
        "nets for monster girls).",
        "",
        "Time always moves forward. Some services cost time and gold,",
        "and nighttime is more dangerous - enemies grow stronger",
        "after dark.",
    ])
    term.pause("Continue")


def _section_inventory():
    term.clear()
    _header("INVENTORY & EQUIPMENT")
    _page([
        "Open Inventory from the city action bar to manage your gear:",
        "one weapon, one armor, and two accessory slots.",
        "",
        "Stats are shown as:",
        "  Attribute: base + equipment + buffs = total",
        "",
        "Weapons carry an ELEMENT. There are 8 elements:",
        "Fire, Water, Ice, Lightning, Wind, Earth, Light, Dark.",
        "Hitting an enemy's weakness deals extra damage; hitting a",
        "resistance deals less. Your own elemental resistances matter",
        "just as much.",
        "",
        "Gear comes in rarity tiers - keep an eye out for rare finds,",
        "and for UNIQUE items with special effects.",
        "",
        "Finish the tutorial and you'll receive a class starter",
        "weapon to get you going.",
        "",
        "Your Skill Book (city action bar) shows the class skills you",
        "have unlocked so far.",
    ])
    term.pause("Continue")


def _section_combat():
    term.clear()
    _header("DUNGEONS & COMBAT")
    _page([
        "The Dungeon button starts a crawl. Each floor has about 10",
        "rooms; roughly 1 in 10 is non-combat (fountain, merchant,",
        "trap, treasure, or stat-check). Progress is saved between",
        "rooms, so leaving is safe.",
        "",
        "In combat you command a party of up to 1 player + 3 allies",
        "against up to 5 enemies. Actions: Attack, Skills, Items,",
        "Defend, Flee, and Capture.",
        "",
        "  Skills     - class-based, unlock as you level, cooldowns.",
        "  Defend     - cut incoming damage this turn.",
        "  Flee       - escape (not always possible).",
        "  Capture    - nets can catch weakened monster girls.",
        "",
        "Hits can apply elemental debuffs and status effects (poison,",
        "burn, bleed, curse, dread...). Potion sickness limits how",
        "often you can chug consumables.",
        "",
        "Party order matters: front row and back row positioning is",
        "set in the city.",
        "",
        "The deeper you go, the worse it gets. Pandemonium floors",
        "stack CURSES that grow with corruption tiers; Wonderland",
        "plays by its own whimsical rules (quirks) and drops floor",
        "bosses on you far more often.",
        "",
        "Defeat carries a penalty - rest up before pushing deep.",
    ])
    term.pause("Continue")


def _section_allies():
    term.clear()
    _header("ALLIES & YOUR HOUSE")
    _page([
        "Monster girls can be captured in combat with Capture Nets",
        "(sold only at the Black Market).",
        "",
        "Captured girls move into Your House, where you can raise",
        "their affection with daily gifts and conversation. At 100",
        "affection you can propose with a ring; at 200 you receive a",
        "legendary soulbound accessory.",
        "",
        "Allies fight beside you in dungeons, level up, and can learn",
        "new skills at the Barracks.",
        "",
        "Houses can be purchased in multiple cities once you can",
        "travel the world map.",
    ])
    term.pause("Continue")


# ── Class starter weapon ─────────────────────────────────────────────────────

STARTER_WEAPONS = {
    "Warrior":   "iron_sword",           # +2 Strength
    "Mage":      "arcane_staff",         # +4 Learning
    "Rogue":     "shadow_dagger",        # +3 Dexterity
    "Cleric":    "divine_staff",         # +4 Wisdom
    "Ranger":    "gale_bow",             # +4 Dexterity (wind)
    "Paladin":   "radiant_sword",        # +3 Strength, +2 Wisdom
    "Warlock":   "shadow_tongue_dagger", # +3 Charisma, +2 Dexterity
    "Barbarian": "blaze_axe",            # +4 Strength
}


def _mods_text(item):
    """Format an item's stat mods as '+2 Strength, +1 Wisdom'."""
    return ", ".join(f"+{v} {k}" for k, v in item.get("mods", {}).items())


def _grant_starter_weapon(player, announce=True):
    """Give the player a common weapon matching their class.

    Equips it to the weapon slot (or adds it to the inventory if the slot is
    already taken). Returns the item, or None if the class has no mapping.
    """
    item_id = STARTER_WEAPONS.get(player.get("class"))
    if not item_id:
        return None
    from resources.items import build_item
    item = build_item(item_id, rarity="common")
    pclass = player.get("class", "hero")
    if player.get("equipped", {}).get("weapon"):
        from inventory import add_item_to_inventory
        add_item_to_inventory(player, item)
        if announce:
            term.print("")
            term.print(f"As a {pclass}, you receive your class starter weapon:")
            term.print(f"    {item['name']} ({_mods_text(item)})")
            term.print("Your weapon slot was already filled, so it was placed")
            term.print("in your inventory instead.")
    else:
        player["equipped"]["weapon"] = item
        # Refresh the elemental profile to include the weapon's elements.
        from combat.elemental import compute_player_elemental
        res, dmg = compute_player_elemental(player)
        player["elemental_res"] = res
        player["elemental_dmg"] = dmg
        if announce:
            term.print("")
            term.print(f"As a {pclass}, you receive your class starter weapon:")
            term.print(f"    {item['name']} ({_mods_text(item)})")
            term.print("It has been equipped to your weapon slot.")
    return item


def _finish_tutorial(player):
    term.clear()
    _header("GOOD LUCK, ADVENTURER")
    _page([
        "That's everything you need to get started.",
        "",
        "Use Save & Quit in the city to save your progress. Your",
        "session log (the scroll icon, top-right) records important",
        "events if you ever lose track.",
        "",
        "The world of Pandemonium is waiting. Survive the depths,",
        "and remember: the deeper you go, the stranger it gets.",
    ])
    _grant_starter_weapon(player)
    player["tutorial_seen"] = True
    try:
        save_game(player)
    except Exception:
        pass  # Never block the player's start because of a save hiccup.
    term.pause("Begin Your Adventure")


# ── Entry point ───────────────────────────────────────────────────────────────

def tutorial_menu(player, city_id=None):
    """Main tutorial loop. Runs inside FacilityScreen / TutorialScreen."""
    try:
        _run_tutorial(player)
    except _FacilityStopped:
        # Player backed out early — still grant the starter weapon so it
        # isn't lost, then let the screen close normally.
        _grant_starter_weapon(player, announce=False)
        player["tutorial_seen"] = True
        try:
            save_game(player)
        except Exception:
            pass


def _run_tutorial(player):
    """Interactive tutorial body (separate so early-exit handling is clean)."""
    name = player.get("name", "adventurer")
    race = player.get("race", "?")
    pclass = player.get("class", "?")
    while True:
        # Re-render the welcome screen each loop so returning from a topic
        # section brings the player back to the menu, not a stale topic page.
        term.clear()
        _header(f"WELCOME TO PANDEMONIUM, {name}")
        _page([
            f"You are a {race} {pclass}, newly arrived in Solmere.",
            "",
            "This short tour covers the essentials. You can revisit any",
            "topic or skip straight to the adventure.",
        ])
        choice = term.menu(
            [
                "The City & Services",
                "Inventory & Equipment",
                "Dungeons & Combat",
                "Allies & Your House",
                "Finish Tutorial",
            ],
            prompt="Choose a topic:",
        )
        if choice == 0:
            _section_city()
        elif choice == 1:
            _section_inventory()
        elif choice == 2:
            _section_combat()
        elif choice == 3:
            _section_allies()
        elif choice == 4 or choice == -1:
            _finish_tutorial(player)
            return
