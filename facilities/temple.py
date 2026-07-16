# facilities/temple.py
import random
from utils import clear_screen, advance_time
from character import player_max_hp
from city_dialogue import service_dialogue
from facilities.shop import get_discounted_price
from resources.items import build_item
from inventory import add_item_to_inventory, get_inventory_caps, count_inventory
from gui.terminal import term


# ── Roman numeral helpers ───────────────────────────────────────────────────

def _int_to_roman(num):
    """Convert integer (1-10) to Roman numeral."""
    val = [10, 9, 5, 4, 1]
    syms = ["X", "IX", "V", "IV", "I"]
    roman = ""
    i = 0
    while num > 0:
        d = num // val[i]
        roman += syms[i] * d
        num -= d * val[i]
        i += 1
    return roman


def _get_global_max_floor(player):
    """Return the highest max_floor reached across all city dungeons."""
    max_floor = 0
    for city_prog in player.get("city_floors", {}).values():
        max_floor = max(max_floor, city_prog.get("max_floor", 1))
    return max_floor


def _get_available_ascension_stones(player):
    """Return list of (tier, item_id, name) for stones the player can currently buy."""
    global_max = _get_global_max_floor(player)
    available = []
    # Stones unlock at floor 10, 20, 30, ...
    tier = 1
    while tier * 10 <= global_max:
        roman = _int_to_roman(tier)
        item_id = f"ascension_stone_{roman.lower().replace(' ', '_')}"
        # Map to actual item IDs (e.g., ascension_stone_i, ascension_stone_ii)
        # The item IDs use lowercase roman without spaces: i, ii, iii, iv, v, vi
        item_id_map = {
            1: "ascension_stone_i",
            2: "ascension_stone_ii",
            3: "ascension_stone_iii",
            4: "ascension_stone_iv",
            5: "ascension_stone_v",
            6: "ascension_stone_vi",
        }
        actual_id = item_id_map.get(tier)
        if actual_id:
            available.append((tier, actual_id, f"Ascension Stone {roman}"))
        tier += 1
    return available


def _ascension_stone_base_price(tier):
    """Temple fixed pricing: 500 gold per tier, marked up 1.2x."""
    return int(600 * tier)


def _buy_ascension_stone(player, city_id):
    """Show available ascension stones and handle purchase."""
    stones = _get_available_ascension_stones(player)
    if not stones:
        term.print("No Ascension Stones are available yet. Clear deeper dungeon floors to unlock them.")
        term.pause()
        return

    term.print("\n--- Ascension Stones ---")
    term.print("These sacred stones can break the level limit of your allies.")
    term.print("(Use them in your House -> Lounge on an ally who has reached their cap.)\n")

    options = []
    for i, (tier, item_id, name) in enumerate(stones, 1):
        base_price = _ascension_stone_base_price(tier)
        final_price = get_discounted_price(base_price, player, city_id)
        options.append(f"{name} — {final_price} gold (base: {base_price})")

    choice = term.menu(options, prompt="Buy which stone?", allow_cancel=True)
    if choice < 0:
        term.print("Cancelled.")
        term.pause()
        return

    tier, item_id, name = stones[choice]
    base_price = _ascension_stone_base_price(tier)
    final_price = get_discounted_price(base_price, player, city_id)

    if player.get("gold", 0) < final_price:
        term.print("You cannot afford this stone.")
        term.pause()
        return

    # Check inventory space
    equip_cap, other_cap = get_inventory_caps(player)
    equip_count, other_count = count_inventory(player)
    if other_count >= other_cap:
        term.print("Your item bag is full! Store or use some items first.")
        term.pause()
        return

    item = build_item(item_id, rarity="common")
    if not add_item_to_inventory(player, item):
        term.print("Could not add stone to inventory (full).")
        term.pause()
        return

    player["gold"] -= final_price
    term.print(f"\nThe priestess hands you a {name}.")
    term.print("'May this light shatter the chains that bind your companions.'")
    term.print(f"You paid {final_price} gold. Remaining: {player['gold']}")
    term.pause()


def recover_allies(player, city_id):
    """Revive all defeated (incapacitated) allies in the party."""
    defeated = [ally for ally in player.get("allies", []) if ally.get("defeated")]
    if not defeated:
        term.print("\nAll of your allies are already in good health.")
        term.pause()
        return

    cost = 50 * len(defeated)
    if player.get("gold", 0) < cost:
        term.print(f"\nYou need {cost} gold to perform the recovery ritual.")
        term.pause()
        return

    player["gold"] -= cost
    term.print(f"\nYou pay {cost} gold for the recovery ritual.")
    for ally in defeated:
        ally["defeated"] = False
        ally["current_hp"] = ally["max_hp"]
        # Print is_recovered dialogue
        from resources.enemies import ENEMIES
        template = ENEMIES.get(ally.get("key", ""), {})
        dialogue = template.get("dialogue", {})
        recovered_line = dialogue.get("is_recovered", f"{ally['name']} is back on their feet!")
        if "{name}" in recovered_line:
            recovered_line = recovered_line.format(name=ally['name'])
        term.print(f"  {recovered_line}")
    term.print("\nThe priestess finishes her prayers. Your party is whole once more.")
    term.pause()


# ── Main menu ────────────────────────────────────────────────────────────────

def _get_wonderland_max_floor(player):
    """Return the highest floor reached in Wonderland dungeon."""
    wl_prog = player.get("city_floors", {}).get("wonderland", {})
    return wl_prog.get("max_floor", 1)


def _godmother_interaction(player, city_id):
    """Handle the Fairy Godmother encounter in Wonderland's temple.
    
    Phase 1: Give the ??? Blade to the player (requires floor 20+)
    Phase 2: Upgrade ??? Blade → Vorpal Blade (requires Jabberwock defeat + fragment)
    """
    from resources.dialogues.wonderland import WONDERLAND_GODMOTHER_DIALOGUE as GD
    from combat.ally import get_heroine_in_party

    term.clear()

    # ── Already upgraded ────────────────────────────────────────────────
    if player.get("wl_godmother_blade_upgraded"):
        for line in GD.get("upgrade_already", [GD["leave"][0]]):
            term.print(line)
        term.pause()
        return

    godmother_spoken = player.get("wl_godmother_spoken", False)
    jabberwock_defeated = player.get("wl_boss_defeated_jabberwock", False)

    # ── Phase 2: Upgrade check ──────────────────────────────────────────
    if godmother_spoken and jabberwock_defeated:
        # Check if Alice is in party with the ??? Blade equipped
        alice = get_heroine_in_party(player, "alice")
        alice_has_blade = (
            alice and
            alice.get("equipped", {}).get("weapon", {}).get("id") == "vorpal_blade_rusted"
        )

        # Check for vorpal_blade_fragment in inventory
        has_fragment = any(
            item.get("id") == "vorpal_blade_fragment"
            for item in player.get("inventory", [])
        )

        if not alice_has_blade:
            for line in GD.get("upgrade_no_alice", [GD["leave"][0]]):
                term.print(line)
            term.pause()
            return

        if not has_fragment:
            for line in GD.get("upgrade_no_fragment", [GD["leave"][0]]):
                term.print(line)
            term.pause()
            return

        # ── Perform upgrade ──────────────────────────────────────────
        for line in GD.get("upgrade_intro", []):
            term.print(line)
        term.print("")
        choice = term.menu([
            "Yes — reforge the Vorpal Blade!",
            "Not yet.",
        ], prompt="")
        if choice != 0:
            term.print(GD.get("leave", [""])[0])
            term.pause()
            return

        for line in GD.get("upgrade_perform", []):
            term.print(line)

        # Remove fragment from inventory
        for item in list(player.get("inventory", [])):
            if item.get("id") == "vorpal_blade_fragment":
                player["inventory"].remove(item)
                break

        # Upgrade Alice's equipped weapon
        vorpal = build_item("vorpal_blade", rarity="unique", enhance=5)
        alice["equipped"]["weapon"] = vorpal

        # Recalculate elemental profile
        from combat.elemental import compute_ally_elemental
        e_res, e_dmg = compute_ally_elemental(alice)
        alice["elemental_res"] = e_res
        alice["elemental_dmg"] = e_dmg

        # Grant Frabjous Day skill
        from combat.ally_skills import swap_alice_to_vorpal_skills, grant_vorpal_upgrade_skill
        swap_alice_to_vorpal_skills(alice)
        grant_vorpal_upgrade_skill(alice)

        player["wl_godmother_blade_upgraded"] = True

        term.print("")
        term.print("✨ The Vorpal Blade is complete! Alice gains 'Frabjous Day'!")
        term.pause()
        return

    # ── Phase 1: First meeting ──────────────────────────────────────────
    if not godmother_spoken:
        for line in GD.get("enter", []):
            term.print(line)
        term.print("")

        choice = term.menu([
            '"A happy ending? In Wonderland?"',
            '"Who are you, really?"',
            '"I\'ll hear what you have to say."',
        ], prompt="")
        if choice < 0:
            term.print(GD.get("leave", [""])[0])
            term.pause()
            return

        for line in GD.get("blade_gift", []):
            term.print(line)
        term.print("")

        # Give the ??? Blade
        blade = build_item("vorpal_blade_rusted", rarity="unique", enhance=0)
        if not add_item_to_inventory(player, blade):
            term.print("\nYour inventory is full! Make room and return.")
            term.pause()
            return

        player["wl_godmother_spoken"] = True
        term.print("\n🔮 Received: ??? Blade (Vorpal Blade — rusted and dormant)")
        term.pause()
        return

    # ── Already spoken, not yet upgrade time ────────────────────────────
    for line in GD.get("blade_already", [GD["leave"][0]]):
        term.print(line)
    term.pause()


def temple_menu(player, city_id="solmere"):
    while True:
        term.clear()
        service_dialogue(city_id, "temple", "enter")
        term.print(f"=== TEMPLE OF {city_id.upper()} ===")
        term.print(f"Gold: {player.get('gold', 0)}")
        
        # Check if the player OR any ally has a curse
        party_cursed = player.get("cursed") or any(
            ally.get("cursed") or any(d.get("type") == "curse" for d in ally.get("active_debuffs", []))
            for ally in player.get("allies", [])
        )
        
        if party_cursed:
            term.print("\nYou feel a dark curse weighing upon your party.")
        else:
            term.print("\nYou feel at peace in this sacred place.")
        
        # Check for defeated allies
        defeated_allies = [a for a in player.get("allies", []) if a.get("defeated")]
        
        # Check if ascension stones are available
        stones_available = bool(_get_available_ascension_stones(player))
        
        # Check for Godmother availability (Wonderland floor 20+)
        godmother_available = (
            city_id == "wonderland" and
            _get_wonderland_max_floor(player) >= 20
        )
        
        options = [
            "Remove Curse (100 gold)",
            "Receive Blessing (50 gold – temporary +2 to all stats for next dungeon floor)",
        ]
        if defeated_allies:
            cost = 50 * len(defeated_allies)
            options.append(f"Recover Incapacitated Allies ({cost} gold)")
        else:
            options.append("Recover Allies — all healthy")
        if stones_available:
            options.append("Buy Ascension Stone")
        if godmother_available:
            options.append("Speak with the Godmother")
        options.append("Leave")
        
        choice = term.menu(options, prompt="What seek you from the temple?")
        
        # Track option indices dynamically
        opt_idx = 0
        curse_opt = opt_idx; opt_idx += 1      # 0
        bless_opt = opt_idx; opt_idx += 1       # 1
        ally_opt = opt_idx; opt_idx += 1        # 2
        stone_opt = opt_idx if stones_available else -1
        if stones_available: opt_idx += 1       # 3 (if available)
        godmother_opt = opt_idx if godmother_available else -1
        if godmother_available: opt_idx += 1    # 3 or 4
        leave_opt = opt_idx                      # last
        
        if choice == curse_opt:
            remove_curse(player, city_id)
            advance_time(player, 30)
        elif choice == bless_opt:
            receive_blessing(player, city_id)
            advance_time(player, 30)
        elif choice == ally_opt:
            recover_allies(player, city_id)
            advance_time(player, 30)
        elif choice == stone_opt:
            _buy_ascension_stone(player, city_id)
            advance_time(player, 15)
        elif choice == godmother_opt:
            _godmother_interaction(player, city_id)
            advance_time(player, 30)
        elif choice == leave_opt or choice == -1:
            service_dialogue(city_id, "temple", "leave")
            advance_time(player, 30)
            break
        else:
            term.print("Invalid choice.")
            term.pause()
            advance_time(player, 15)

def remove_curse(player, city_id):
    # Find which allies are cursed (flag or active_debuffs)
    cursed_allies = [
        ally for ally in player.get("allies", [])
        if ally.get("cursed") or any(d.get("type") == "curse" for d in ally.get("active_debuffs", []))
    ]
    is_player_cursed = player.get("cursed")

    # Check if anyone needs cleansing
    if not is_player_cursed and not cursed_allies:
        term.print("Your party is not cursed. No need for cleansing.")
        term.pause()
        return
    
    cost = 100
    if player.get("gold", 0) < cost:
        term.print("You don't have enough gold for the ritual.")
        term.pause()
        return
    
    player["gold"] -= cost
    
    # Cleanse the Player
    if is_player_cursed:
        player["cursed"] = False
        if player.get("active_debuffs"):
            player["active_debuffs"] = [d for d in player["active_debuffs"] if d.get("type") != "curse"]
            
    # Cleanse all affected Allies
    for ally in cursed_allies:
        ally["cursed"] = False
        if ally.get("active_debuffs"):
            ally["active_debuffs"] = [d for d in ally["active_debuffs"] if d.get("type") != "curse"]
    
    term.print("The priestess chants ancient prayers. The dark curse lifts from your party.")
    term.print("The ritual is complete. You all feel cleansed.")
    term.pause()

def receive_blessing(player, city_id):
    cost = 50
    if player.get("gold", 0) < cost:
        term.print("You cannot afford a blessing.")
        term.pause()
        return
    
    player["gold"] -= cost
    
    blessing = {
        "type": "blessing",
        "stat": "all",
        "value": 2,
        "remaining": 1
    }
    player.setdefault("active_buffs", []).append(blessing)
    
    term.print("The temple's light washes over you. You feel divinely empowered (+2 to all stats for the next floor).")
    service_dialogue(city_id, "temple", "bless")
    term.pause()
